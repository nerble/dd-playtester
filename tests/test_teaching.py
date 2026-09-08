from copy import deepcopy
from dataclasses import replace
import json
from types import SimpleNamespace

import pytest

from dd4tester.campaign import (
    CampaignRunner, CampaignSpec,
    _ensure_training_deficit_repair_marker, _reopen_local_teacher_fallback,
    _training_deficit_repair_pending,
    _reopen_noop_training_deficit_repair,
)
from dd4tester.character import CharacterSpec
from dd4tester.equipment import GearCatalog
from dd4tester.hunt_candidates import ACT_AGGRESSIVE, ACT_SENTINEL, ExitSource, MobileSource, MobReset, RoomSource, WorldSource
from dd4tester.starter import _CLASS_TRAINERS, StarterPolicy, plan_local_training_fallback
from dd4tester.state import CharacterState
from dd4tester.teaching import parse_skill_groups, practice_gain, teacher_capacity
from dd4tester.training import parse_practice_listing, training_priorities_for


STATS = {"str_mod": 30, "dex_mod": 17, "int_mod": 12, "wis_mod": 15}
SOURCE = '''
int *spell_groups[MAX_GROUPS] = { &gsn_group_armed, &gsn_group_defense, &gsn_group_last };
struct spell_group_struct spell_group_table[MAX_SPELL_GROUP] = {
    {&gsn_group_armed, 0}, {&gsn_enhanced_damage, 0}, {&gsn_mixed, 30},
    {&gsn_group_defense, 0}, {&gsn_dodge, 0}, {&gsn_mixed, 40}, {&gsn_group_last, 0}
};
const struct skill_type skill_table[MAX_SKILL] = {
    {"armed combat knowledge", &gsn_group_armed},
    {"defense knowledge", &gsn_group_defense},
    {"enhanced damage", &gsn_enhanced_damage}, {"dodge", &gsn_dodge},
    {"mixed action", &gsn_mixed}
};
'''


def test_source_groups_resolve_real_names_and_multiple_memberships():
    groups = parse_skill_groups(SOURCE)
    assert groups["dodge"] == (("defense knowledge", 0),)
    assert groups["mixed action"] == (("armed combat knowledge", 30), ("defense knowledge", 40))
    assert teacher_capacity({"armed combat knowledge": 80, "defense knowledge": 70}, "mixed action", groups) == 70
    assert teacher_capacity({"armed combat knowledge": 80, "defense knowledge": 39}, "mixed action", groups) is None
    assert teacher_capacity({"mixed action": 85}, "mixed action", groups) == 85
    assert teacher_capacity({}, "unknown", groups) is None


@pytest.mark.parametrize("source", [
    SOURCE.replace("{&gsn_dodge, 0}", "{&gsn_dodge, UNKNOWN}"),
    SOURCE.replace("{&gsn_group_armed, 0},", ""),
    SOURCE.replace(", {&gsn_group_last, 0}", ""),
    SOURCE.replace("{&gsn_group_defense, 0},", ""),
])
def test_unknown_or_incomplete_source_does_not_authorize_a_fallback(source):
    with pytest.raises(ValueError):
        parse_skill_groups(source)


def test_dorrik_practice_formula_from_handler_and_do_practice():
    assert practice_gain(28, 70, "physical", STATS) == 42
    assert practice_gain(42, 70, "physical", STATS) == 49
    assert practice_gain(49, 70, "physical", STATS) == 53
    assert practice_gain(66, 80, "physical", STATS) is None
    assert practice_gain(66, 70, "physical", STATS) is None
    assert practice_gain(66, 85, "physical", STATS) == 69
    assert practice_gain(20, 70, "intellectual", STATS) == 36


@pytest.mark.parametrize("updates", [{"str_mod": None}, {"int_mod": 50000}, {"dex_mod": True}, {"int_mod": "bad"}])
def test_missing_or_concealed_stats_are_not_training_permission(updates):
    assert practice_gain(28, 70, "physical", {**STATS, **updates}) is None


@pytest.mark.parametrize("current,capacity", [(100, 70), (True, 70), (28, None), (28, True), (28, 50000)])
def test_practice_acceptance_is_bounded(current, capacity):
    assert practice_gain(current, capacity, "physical", STATS) is None


def _world(character_class="warrior"):
    destination = int(_CLASS_TRAINERS[character_class].room_vnum)
    skill, group, source_skill = {
        "warrior": ("dodge", "defense knowledge", "inner force"),
        "thief": ("backstab", "stealth techniques", "detect hidden"),
        "mage": ("magic missile", "evocation magiks", "evocation magiks"),
    }[character_class]
    world = WorldSource(
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are", exits={"south": ExitSource("south", destination, 0, -1)}),
            destination: RoomSource(destination, "Guild", "midgaard.are", exits={"north": ExitSource("north", 3001, 0, -1)}),
        },
        mobiles={900: MobileSource(
            900, "guildmaster", "the guildmaster", 24, ACT_SENTINEL, 0, "midgaard.are",
            teachings=(("teacher base", 10), (source_skill, 70), (group, 70)),
        )},
        mob_resets=[MobReset(900, destination, 1, ())],
        skill_groups={skill: ((group, 0),)},
    )
    return world, skill


def _plan(world, character_class="warrior", skill="dodge", **updates):
    values = dict(character_class=character_class, subclass=None, character_level=25,
                  known_skill_levels={skill: 28}, stats=STATS, practice_balances=(3, 3))
    values.update(updates)
    return plan_local_training_fallback(world, **values)


@pytest.mark.parametrize("character_class", ["warrior", "thief", "mage"])
def test_registered_local_guild_can_offer_class_appropriate_gain(character_class):
    world, skill = _world(character_class)
    fallback = _plan(world, character_class, skill)
    assert fallback is not None
    assert fallback.teacher_mobile_vnum == 900
    assert fallback.route.room_vnum == _CLASS_TRAINERS[character_class].room_vnum
    assert fallback.gains[0][0] == skill
    assert fallback.gains[0][2] > 28


@pytest.mark.parametrize("updates", [
    {"practice_balances": (0, 0)}, {"practice_balances": (None, None)},
    {"stats": {}}, {"stats": []}, {"known_skill_levels": {}},
    {"known_skill_levels": {"dodge": 0}}, {"known_skill_levels": {"dodge": 60}},
    {"character_level": 19},
])
def test_local_visit_requires_an_available_useful_lesson(updates):
    world, _ = _world()
    assert _plan(world, **updates) is None


def test_local_fallback_preserves_route_hazards_and_teacher_level():
    world, _ = _world()
    teacher = world.mobiles[900]
    world.mobiles[900] = replace(teacher, teachings=(("teacher base", 30), ("inner force", 70), ("defense knowledge", 70)))
    assert _plan(world) is None
    world.mobiles[900] = teacher
    world.mobiles[901] = MobileSource(901, "attacker", "an attacker", 28, ACT_AGGRESSIVE | ACT_SENTINEL, 0, "midgaard.are")
    world.mob_resets.append(MobReset(901, int(_CLASS_TRAINERS["warrior"].room_vnum), 1, ()))
    assert _plan(world) is None


def _state():
    return {
        "level": 25, "world_boot_id": "boot-1", "room_vnum": "3054", "practice": 3,
        "stats": dict(STATS), "campaign_known_skill_levels": {"dodge": 28},
        "campaign_training_audit": {"observed": True, "level": 25, "boot_id": "boot-1", "physical_practices": 3, "intellectual_practices": 0},
        "campaign_training_deficit_repair": {"attempted": True, "level": 25, "boot_id": "boot-1", "deficits": [{"skill": "dodge"}]},
        "campaign_fastwalk_training_deferred_route_hazard": {"level": 25, "boot_id": "boot-1"},
        "campaign_protection_recovery_required": {"policy_id": "failed-fight", "xp_delta": -324, "level": 25, "boot_id": "boot-1"},
    }


def test_distant_deferral_reopens_once_without_touching_combat_loss():
    world, _ = _world()
    state = _state()
    original_protection = deepcopy(state["campaign_protection_recovery_required"])
    _reopen_local_teacher_fallback(state, world=world, character_class="warrior", subclass=None)
    marker = state["campaign_training_deficit_repair"]
    assert marker["local_teacher_fallback"]["status"] == "pending"
    assert _training_deficit_repair_pending(state, character_level=25)
    marker["attempted"] = True
    marker["local_teacher_fallback"]["status"] = "consumed"
    _ensure_training_deficit_repair_marker(state, character_class="warrior", subclass=None)
    _reopen_local_teacher_fallback(state, world=world, character_class="warrior", subclass=None)
    assert not _training_deficit_repair_pending(state, character_level=25)
    assert state["campaign_training_deficit_repair"]["local_teacher_fallback"]["status"] == "consumed"
    assert state["campaign_protection_recovery_required"] == original_protection


@pytest.mark.parametrize("field,value", [
    ("room_vnum", "5000"), ("world_boot_id", "new-boot"),
    ("campaign_fastwalk_training_deferred_route_hazard", None),
    ("campaign_training_audit", {}), ("stats", {}),
])
def test_reopening_requires_same_scope_and_a_proven_alternative(field, value):
    world, _ = _world()
    state = _state()
    state[field] = value
    _reopen_local_teacher_fallback(state, world=world, character_class="warrior", subclass=None)
    assert state["campaign_training_deficit_repair"]["attempted"] is True


def test_live_training_uses_and_retains_the_local_route(monkeypatch):
    world, _ = _world()
    policy = StarterPolicy(
        CharacterSpec.from_mapping({"name": "Replaywar", "race": "dwarf", "gender": "male", "class": "warrior"}),
        "unused", source_world=world, known_skill_levels={"dodge": 28},
        fastwalk_train_before_departure=True,
    )
    policy.latest_practice_balances = (3, 0)
    policy.fastwalk_stat_training_configured = True
    monkeypatch.setattr(policy, "_source_class_trainer_route_hazards", lambda *_: ("unsafe distant room",))
    state = CharacterState(level=25, room_vnum="3054", area="Midgaard", position=7, stats=STATS)
    decision = policy._fastwalk_training_decision(state)
    assert decision.command == "south"
    assert policy._level_ten_class_trainer(state).room_vnum == "3023"
    assert not policy.fastwalk_training_deferred_after_route_hazard
    assert policy.pending_training_events[0].type == "training_route_fallback"
    assert policy.pending_training_events[0].data["teacher_mobile_vnum"] == 900


def test_live_fallback_reads_balances_before_deferring_the_route(monkeypatch):
    world, _ = _world()
    policy = StarterPolicy(
        CharacterSpec.from_mapping({"name": "Replaywar", "race": "dwarf", "gender": "male", "class": "warrior"}),
        "unused", source_world=world, known_skill_levels={"dodge": 28},
        fastwalk_train_before_departure=True,
    )
    policy.fastwalk_stat_training_configured = True

    def preflight(*_):
        if policy.fastwalk_training_route_preflighted:
            return ()
        policy.fastwalk_training_route_preflighted = True
        return ("unsafe distant room",)

    monkeypatch.setattr(policy, "_source_class_trainer_route_hazards", preflight)
    state = CharacterState(level=25, room_vnum="3054", area="Midgaard", position=7, stats=STATS)
    assert policy._fastwalk_training_decision(state).command == "score"
    assert not policy.fastwalk_training_route_preflighted
    assert not policy.fastwalk_training_deferred_after_route_hazard
    assert not policy.pending_training_events
    policy.latest_practice_balances = (3, 0)
    assert policy._fastwalk_training_decision(state).command == "south"
    assert policy.local_training_fallback.route.room_vnum == "3023"


def test_balance_audit_has_three_attempt_ceiling():
    policy = StarterPolicy(
        CharacterSpec.from_mapping({"name": "Replaywar", "race": "dwarf", "gender": "male", "class": "warrior"}),
        "unused",
    )
    for _ in range(3):
        assert policy._fastwalk_practice_balance_audit().command == "score"
    assert policy._fastwalk_practice_balance_audit() is None
    assert policy.failure == "score did not report the practice balance before field departure"


def test_unautomated_priority_cannot_authorize_a_lesson(monkeypatch):
    from dd4tester.training import training_priorities_for

    priorities = tuple(replace(p, automated=False) for p in training_priorities_for("warrior"))
    monkeypatch.setattr("dd4tester.starter.training_priorities_for", lambda *_a, **_k: priorities)
    world, _ = _world()
    assert _plan(world) is None


def _event(kind, **payload):
    return {"kind": kind, "payload_json": json.dumps(payload)}


def _unaudited_local_attempt():
    state = _state()
    state["campaign_training_deficit_repair"].update({
        "policy_revision": 230, "attempt_policy_id": "training-deficit-repair-10-100",
        "local_teacher_fallback": {"status": "consumed", "teacher_mobile_vnum": 900},
    })
    events = [
        _event("game_event", type="room_updated", data={"vnum": "3054"}),
        _event("decision", command="eq all"),
        _event("decision", command="remove robe"),
        _event("decision", command="wear linen"),
        _event("game_event", type="training_deferred", data={"preflight": True}),
        _event("decision", command="save"), _event("decision", command="quit"),
    ]
    segments = [{"phase": "training-deficit-repair-10-100", "status": "success", "run_id": 42}]
    return state, events, segments


def test_policy_230_healer_noop_reopens_once_for_fresh_balance_audit():
    state, events, segments = _unaudited_local_attempt()
    storage = SimpleNamespace(list_events=lambda _: events)
    repaired, reopened = _reopen_noop_training_deficit_repair(
        storage, state, segments, character_class="warrior", subclass=None,
    )
    assert reopened
    marker = repaired["campaign_training_deficit_repair"]
    assert marker["local_teacher_fallback"]["balance_audit_retry_from_run_id"] == 42
    assert marker["local_teacher_fallback"]["status"] == "pending"
    assert repaired["campaign_protection_recovery_required"] == state["campaign_protection_recovery_required"]
    marker["attempted"] = True
    marker["local_teacher_fallback"]["status"] = "consumed"
    _, reopened = _reopen_noop_training_deficit_repair(
        storage, repaired, segments, character_class="warrior", subclass=None,
    )
    assert not reopened


@pytest.mark.parametrize("extra", [
    _event("decision", command="score"),
    _event("decision", command="south"),
    _event("decision", command="practice dodge"),
    _event("game_event", type="training_completed", data={}),
    _event("game_event", type="training_route_fallback", data={}),
    _event("game_event", type="training_deferred", data={"preflight": False}),
    _event("game_event", type="room_updated", data={"vnum": "3023"}),
])
def test_actual_audit_visit_or_lesson_cannot_receive_legacy_retry(extra):
    state, events, segments = _unaudited_local_attempt()
    storage = SimpleNamespace(list_events=lambda _: [*events, extra])
    repaired, reopened = _reopen_noop_training_deficit_repair(
        storage, state, segments, character_class="warrior", subclass=None,
    )
    assert not reopened
    assert repaired == state


def test_campaign_selects_pending_local_lesson_before_unavailable_protection(tmp_path, monkeypatch):
    monkeypatch.setattr("dd4tester.campaign._current_dd4_source_revision", lambda: "source-1")
    world, _ = _world()
    character = CharacterSpec.from_mapping({"name": "Replaywar", "race": "dwarf", "gender": "male", "class": "warrior"})
    spec = CampaignSpec("training", tmp_path / "character.yaml", character)
    runner = CampaignRunner(spec, tmp_path / "campaign.yaml")
    runner._source_world = world
    runner._gear_catalog = GearCatalog({})
    state = _state()
    state.update({
        "campaign_source_revision": "source-1",
        "hp": 569, "max_hp": 569, "mana": 250, "max_mana": 250,
        "move": 442, "max_move": 442, "hunger": 40, "thirst": 40,
        "inventory": [[{"quan": "3", "short_desc": "a big pot pie"}]],
        "campaign_last_policy": "source-ranked-sanctuary-recovery-2-100",
        "campaign_research_results": {"source-ranked-sanctuary-recovery-2-100": {
            "boot_id": "boot-1", "absent": True, "observed": False, "viable": False,
        }},
        "campaign_research_absence_cooldowns": {"source-ranked-sanctuary-recovery-2-100": 3},
    })
    protection = deepcopy(state["campaign_protection_recovery_required"])
    policy = runner._policy_for_state(state)
    assert policy.execution == "training-deficit-repair"
    assert state["campaign_training_deficit_repair"]["local_teacher_fallback"]["status"] == "pending"
    assert state["campaign_protection_recovery_required"] == protection


POST_LESSON = """
Skills known:
armed combat knowledge: 40%     second attack: 55%
enhanced damage: 66%            unarmed combat knowledge: 60%
kick: 41%                      headbutt: 28%
stun: 62%                      shield block: 47%
defense knowledge: 62%          dodge: 28%          grip: 99%
Skills which may be learned:
rescue: 0%                     inner force: 0%     swim: 0%
You have 2 physical and 0 intellectual practices remaining.
"""


def test_rejected_ceiling_cannot_hide_the_next_actual_lesson():
    world, _ = _world()
    listing = parse_practice_listing(POST_LESSON)
    policy = StarterPolicy(
        CharacterSpec.from_mapping({"name": "Replaywar", "race": "dwarf", "gender": "male", "class": "warrior"}),
        "unused", source_world=world, known_skill_levels=listing.known,
        practice_types_spent=frozenset({"physical"}),
        rejected_practice_skills=frozenset({"enhanced damage"}),
    )
    state = CharacterState(level=25, room_vnum="3023", stats=STATS)
    assert policy._critical_damage_unlock(state, listing) == "headbutt"
    policy.local_training_fallback = _plan(world)
    policy.loremaster_step = 2
    policy.text = POST_LESSON
    assert policy._loremaster_decision(state).command == "practice headbutt"
    policy._resolve_pending_practice("accepted", "trainer confirmed the lesson")
    assert policy._loremaster_decision(state).command == "practice"
    policy.text = POST_LESSON.replace("headbutt: 28%", "headbutt: 42%").replace("2 physical", "1 physical")
    assert policy._loremaster_decision(state).command == "practice headbutt"
    policy._resolve_pending_practice("accepted", "trainer confirmed the lesson")
    assert policy._loremaster_decision(state).command == "practice"
    policy.text = POST_LESSON.replace("headbutt: 28%", "headbutt: 49%").replace("2 physical", "0 physical")
    assert not policy._loremaster_decision(state).command.startswith("practice ")


@pytest.mark.parametrize("character_class", ["warrior", "mage", "thief"])
def test_damage_fallback_respects_rejections_and_minimum_level(character_class, monkeypatch):
    template = training_priorities_for(character_class)[0]
    priorities = tuple(replace(template, skill=name, utility="damage", automated=True,
                               target_percent=70, practice_type="physical", minimum_level=level)
                       for name, level in (("capped", None), ("future", 30), ("available", 10)))
    monkeypatch.setattr("dd4tester.starter.training_priorities_for", lambda *_a, **_k: priorities)
    policy = StarterPolicy(
        CharacterSpec.from_mapping({"name": "Replaywar", "race": "human", "gender": "male", "class": character_class}),
        "unused", known_skill_levels={"capped": 60, "future": 20, "available": 20},
        rejected_practice_skills=frozenset({"capped"}),
    )
    listing = parse_practice_listing("Skills known:\ncapped: 60% future: 20% available: 20%\nYou have 1 physical and 0 intellectual practices remaining.")
    assert policy._critical_damage_unlock(CharacterState(level=25), listing) == "available"
    policy.rejected_practice_skills.add("available")
    assert policy._critical_damage_unlock(CharacterState(level=25), listing) is None


def _rejected_ceiling_attempt():
    state, _, segments = _unaudited_local_attempt()
    marker = state["campaign_training_deficit_repair"]
    marker["policy_revision"] = 231
    state["practice"] = 2
    state["campaign_training_audit"]["physical_practices"] = 2
    events = [
        _event("game_event", type="training_rejected", data={"skill": "enhanced damage"}),
        _event("game_event", type="training_completed", data={"skill": "headbutt"}),
        _event("response", text=POST_LESSON),
        _event("game_event", type="training_deferred", data={"reason": "no immediately useful listed skill for this practice type"}),
    ]
    return state, events, segments


def test_source_capable_rejected_ceiling_retry_is_once_and_keeps_losses():
    state, events, segments = _rejected_ceiling_attempt()
    world, _ = _world()
    storage = SimpleNamespace(list_events=lambda _: events)
    repaired, reopened = _reopen_noop_training_deficit_repair(
        storage, state, segments, character_class="warrior", subclass=None, world=world,
    )
    assert reopened
    assert repaired["campaign_protection_recovery_required"] == state["campaign_protection_recovery_required"]
    marker = repaired["campaign_training_deficit_repair"]
    assert marker["local_teacher_fallback"]["rejected_ceiling_retry_from_run_id"] == 42
    assert marker["local_teacher_fallback"]["status"] == "pending"
    marker["attempted"] = True
    marker["local_teacher_fallback"]["status"] = "consumed"
    _, reopened = _reopen_noop_training_deficit_repair(
        storage, repaired, segments, character_class="warrior", subclass=None, world=world,
    )
    assert not reopened


@pytest.mark.parametrize("missing", ["source", "rejection", "listing", "deferral", "balance", "capacity", "scope"])
def test_rejected_ceiling_retry_requires_complete_evidence(missing):
    state, events, segments = _rejected_ceiling_attempt()
    world, _ = _world()
    if missing == "source":
        world = None
    elif missing == "rejection":
        events.pop(0)
    elif missing == "listing":
        events.pop(2)
    elif missing == "deferral":
        events.pop(3)
    elif missing == "balance":
        state["practice"] = 0
    elif missing == "capacity":
        world.mobiles[900] = replace(world.mobiles[900], teachings=(("teacher base", 10), ("inner force", 70), ("defense knowledge", 20)))
    elif missing == "scope":
        state["world_boot_id"] = "new-boot"
    repaired, reopened = _reopen_noop_training_deficit_repair(
        SimpleNamespace(list_events=lambda _: events), state, segments,
        character_class="warrior", subclass=None, world=world,
    )
    assert not reopened
    assert repaired == state
