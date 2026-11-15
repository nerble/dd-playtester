from dataclasses import replace

import pytest

from dd4tester.character import CharacterSpec
from dd4tester.fastwalks import Fastwalk
from dd4tester.hunt_candidates import (
    ITEM_ARMOR, ITEM_WAND, ITEM_WEAPON, MobileSource, MobReset, ObjectSource,
    RoomSource, SourceCombatOutput, WorldSource,
)
from dd4tester.ordinary_joiners import OrdinaryJoinerAssessment, ordinary_joiner_source
from dd4tester.starter import BotDecision, FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


PROMPT = "<800/1000 hits 500/500 mana 100/100 move [Test]> "


def world():
    return WorldSource(
        mobiles={
            1: MobileSource(1, "soldier", "the soldier", 44, 2, 0, "test.are",
                            room_description="A soldier waits here.", description="He guards the doorway."),
            2: MobileSource(2, "watchman", "the watchman", 42, 2, 0, "test.are",
                            room_description="A watchman stands here.", description="He watches the gate carefully."),
        },
        rooms={100: RoomSource(100, "A gate", "test.are")},
        objects={10: ObjectSource(10, "sword", "a sword", ITEM_WEAPON, (0, 1, 6, 0), 1),
                 11: ObjectSource(11, "mail", "some mail", ITEM_ARMOR, (1, 0, 0, 0), 1)},
        mob_resets=[MobReset(1, 100, 1, (10,), ((16, 10),)),
                    MobReset(2, 100, 1, (11,), ((5, 11),))],
    )


def test_source_audit_admits_ordinary_arms_but_checks_all_reset_items():
    source = world()
    assert ordinary_joiner_source(source, 1, 100)
    assert ordinary_joiner_source(source, 2, 100)
    source.objects[12] = ObjectSource(12, "icicle", "an icicle", ITEM_WAND,
                                     (40, 5, 5, 0), 1, value_strings=("40", "5", "5", "frost breath"))
    source.mob_resets[1] = replace(source.mob_resets[1], object_vnums=(11, 12))
    assert not ordinary_joiner_source(source, 2, 100)


def test_rank_and_target_hp_metadata_are_not_admission_gates():
    source = world()
    source.mobiles[1] = replace(source.mobiles[1], rank="boss", hp_modifier=400, hp_modifier_known=False)
    assert ordinary_joiner_source(source, 1, 100)


@pytest.mark.parametrize("hazard", ["special", "program", "unknown_item", "poison", "ego", "population"])
def test_source_audit_preserves_nonordinary_hazards(hazard):
    source = world()
    if hazard == "special":
        source.mobile_specials[1] = ("spec_cast_psionicist",)
    elif hazard == "program":
        source.mobiles[1] = replace(source.mobiles[1], programs=(object(),))
    elif hazard == "unknown_item":
        source.mob_resets[0] = replace(source.mob_resets[0], object_vnums=(999,))
    elif hazard == "population":
        source.mob_resets[0] = replace(source.mob_resets[0], maximum_count=5)
    else:
        source.objects[10] = replace(source.objects[10], extra_flags=1 << (14 if hazard == "poison" else 2))
    assert not ordinary_joiner_source(source, 1, 100)


def prepared_assessment(source_level=42):
    assessment = OrdinaryJoinerAssessment()
    assert assessment.begin(scope=("100", 0, 45, "boot", "#1", 1), attacker="the watchman",
                            mobile_vnum=2, source_level=source_level, room_sequence=1, now=100)
    assert assessment.inspect(selector="#2", descriptions={1: "He guards the doorway.",
                                                           2: "He watches the gate carefully."},
                              room="100", level=45, boot="boot", visit=0, now=101)
    assessment.observe("He watches the gate carefully.\nThe watchman is in perfect health.\n" + PROMPT, now=101.1)
    assert assessment.next_command(now=101.2) == "consider #2"
    return assessment


def test_complete_source_identity_and_relative_consider_ignore_tank_comparison():
    assessment = prepared_assessment()
    assessment.observe("The watchman looks like an easy", now=101.3)
    assert assessment.plan["stage"] == "consider"
    assessment.observe(" kill.\nHowever, it is built like a tank!\n" + PROMPT, now=101.4)
    assert assessment.plan["stage"] == "admitted"
    assert assessment.plan["level_ceiling"] == 43


def test_consider_deadline_and_source_contradictions_fail_closed():
    assessment = prepared_assessment()
    assessment.observe("The perfect match!\n", now=107)
    assert assessment.plan["stage"] == "failed"
    assert "five seconds" in assessment.plan["reason"]
    assessment = prepared_assessment(source_level=5)
    assessment.observe("The perfect match!\n", now=101.3)
    assert assessment.plan["stage"] == "failed"
    assert "source level" in assessment.plan["reason"]


def policy_setup(monkeypatch):
    policy = StarterPolicy(CharacterSpec.from_mapping({
        "name": "Tester", "race": "dwarf", "gender": "male", "class": "warrior",
        "subclass": "knight", "title": "",
    }), "test-password")
    source = world()
    policy.source_world = source
    policy.fastwalk_route = Fastwalk("test", 1, 100, "n")
    policy.fastwalk_hunt_stops = (FieldHuntStop(
        (), "soldier", exact_target=True, source_mobile_vnum=1, source_target_armed=True,
        source_reset_room_vnum="100", source_policy_id="test", maximum_level_offset=1,
    ),)
    policy.fastwalk_attack_started = policy.combat_active = True
    policy.active_target = "soldier"
    policy.active_target_selector = "#1"
    policy.active_target_mobile_vnum = 1
    policy.current_room = policy.enemy_snapshot_room = "100"
    policy.world_boot_id = "boot"
    policy.unapproved_field_attacker = "the watchman"
    policy.fastwalk_source_consider_outcomes = {"test": True}
    policy.source_mobile_targets = {
        "a soldier waits here.": ("soldier",), "the soldier": ("soldier",),
        "a watchman stands here.": ("watchman",), "the watchman": ("watchman",),
    }
    policy.room_target_selectors = {"100": {"soldier": ["#1"], "watchman": ["#2"]}}
    primary = {"isnpc": 1, "name": "the soldier", "level": 44,
               "long_desc": source.mobiles[1].room_description,
               "look_desc": source.mobiles[1].description}
    monkeypatch.setattr(policy, "_current_room_enemy_records", lambda state, deduplicate=True:
                        [primary] if deduplicate else [primary, dict(primary)])
    monkeypatch.setattr(policy, "_encounter_output", lambda *args: SourceCombatOutput("weapon", 20, 30, 40, "actions", 0, 6))
    monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: 100.0)
    state = CharacterState(level=45, room_vnum="100", hp=800, max_hp=1000,
                           mana=500, max_mana=500, in_combat=True, position=6,
                           room_listing={"sequence": 1})
    return policy, state


def complete_policy_probe(policy, state):
    handled, decision = policy._ordinary_joiner_decision(state)
    assert handled and decision.command == "look"
    state.room_listing = {
        "sequence": 2, "room_vnum": "100", "render_complete": True, "unkeyed_lines": [],
        "targeted_lines": [{"target_id": str(i), "description": f"The {name} is here, fighting YOU!"}
                           for i, name in ((1, "soldier"), (2, "watchman"))],
    }
    handled, decision = policy._ordinary_joiner_decision(state)
    assert handled and decision.command == "look #2"
    assessment = policy._combat_session.ordinary_joiner
    assessment.observe("He watches the gate carefully.\nThe watchman is in perfect health.\n" + PROMPT, now=100.1)
    handled, decision = policy._ordinary_joiner_decision(state)
    assert handled and decision.command == "consider #2"
    assessment.observe("The watchman looks like an easy kill.\n" + PROMPT, now=100.2)
    assert policy._ordinary_joiner_decision(state) == (False, None)
    return assessment


def test_policy_binds_second_opponent_without_reclassifying_duplicate_packets_as_solo(monkeypatch):
    policy, state = policy_setup(monkeypatch)
    complete_policy_probe(policy, state)
    encounter = policy.source_material_encounter
    assert encounter.ordinary_joiner
    assert encounter.budget.mobile_vnums == (1, 2)
    assert policy.unapproved_field_attacker is None
    monkeypatch.setattr(policy, "_damage_window_probe_decision", lambda _: None)
    monkeypatch.setattr(policy, "_combat_pouch_potion_decision", lambda _: None)
    monkeypatch.setattr(policy, "_combat_self_heal_decision", lambda _: BotDecision("cast 'cure serious'", "heal"))
    monkeypatch.setattr(policy, "_between_round_combat_decision", lambda _: pytest.fail("healing must retain priority"))
    handled, decision = policy._source_material_encounter_decision(state)
    assert handled and decision.command == "cast 'cure serious'"
    assert set(policy.fastwalk_encounter_budgets[-1]["active_vnums"]) == {1, 2}


def test_policy_rejects_third_attacker_and_preserves_health_floor(monkeypatch):
    policy, state = policy_setup(monkeypatch)
    state.hp = 100
    assert policy._ordinary_joiner_decision(state) == (False, None)
    state.hp = 800
    complete_policy_probe(policy, state)
    primary = {"isnpc": 1, "name": "the soldier", "level": 44}
    monkeypatch.setattr(policy, "_current_room_enemy_records", lambda state, deduplicate=True:
                        [primary] if deduplicate else [primary, dict(primary), dict(primary)])
    handled, decision = policy._source_material_encounter_decision(state)
    assert handled and decision.command == "flee"
    assert "two-opponent" in decision.reason


def test_consider_reply_does_not_overwrite_the_primary_result(monkeypatch):
    policy, state = policy_setup(monkeypatch)
    assessment = prepared_assessment()
    policy._combat_session.ordinary_joiner = assessment
    policy.consider_target = "soldier"
    policy.consider_viable = True
    monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: 101.3)
    policy.observe_text("The watchman is no match for you.\n")
    assert policy.consider_viable is True


def test_room_change_ends_the_probe_instead_of_reusing_a_stale_selector(monkeypatch):
    policy, state = policy_setup(monkeypatch)
    assert policy._ordinary_joiner_decision(state)[1].command == "look"
    state.room_vnum = "101"
    handled, decision = policy._ordinary_joiner_decision(state)
    assert handled and decision.command == "flee"
    assert "context" in decision.reason


def test_loss_after_primary_kill_names_the_surviving_joiner(monkeypatch):
    from dd4tester.combat_losses import source_combat_loss_records

    policy, state = policy_setup(monkeypatch)
    complete_policy_probe(policy, state)
    policy.fastwalk_hunt_stop_killed = True
    mobile = policy.source_world.mobiles[2]
    secondary = {"isnpc": 2, "name": mobile.short_description, "level": 42,
                 "long_desc": mobile.room_description, "look_desc": mobile.description}
    monkeypatch.setattr(policy, "_current_room_enemy_records", lambda state, **kwargs: [secondary])
    policy.after_command(BotDecision("flee", "health floor"), state)
    policy._combat_session.observe_xp_loss({"xp": 1405, "partial_xp": 100})
    losses = source_combat_loss_records({"level": 45, "source_combat_losses": policy._combat_session.source_losses})
    record = losses["source-ranked-hunt-test-2-100-45"]
    assert record["mobile_vnum"] == 2
    assert record["parent_policy_id"] == "test"
    assert record["xp_lost"] == 1405
    assert record["encounter_mobile_vnums"] == [1, 2]


def test_loss_attribution_does_not_alias_an_unidentified_third_actor(monkeypatch):
    from dd4tester.ordinary_joiners import ordinary_joiner_withdrawal

    policy, state = policy_setup(monkeypatch)
    complete_policy_probe(policy, state)
    encounter = policy.source_material_encounter
    assert ordinary_joiner_withdrawal(
        policy.source_world, encounter, enemies=[{"isnpc": 999}], primary_killed=True,
        parent_policy_id="test", level=45, room="100", reason="unknown attacker",
    ) is None


def test_one_observed_level_up_retains_only_the_already_engaged_pair(monkeypatch):
    policy, state = policy_setup(monkeypatch)
    complete_policy_probe(policy, state)
    state.level = 46
    assert policy._ordinary_joiner_decision(state) == (False, None)
    assert policy.source_material_encounter.level == 46
    assert policy.fastwalk_encounter_budgets[-1]["outcome"] == "observed level transition"
    assert policy.fastwalk_encounter_budgets[-1]["from_level"] == 45
    state.level = 48
    handled, decision = policy._ordinary_joiner_decision(state)
    assert handled and decision.command == "flee"


def test_partial_look_and_consider_wait_for_their_own_prompt():
    assessment = OrdinaryJoinerAssessment()
    assert assessment.begin(scope=("100", 0, 45, "boot", "#1", 1), attacker="the watchman",
                            mobile_vnum=2, source_level=42, room_sequence=1, now=100)
    assert assessment.inspect(selector="#2", descriptions={1: "He guards the doorway.",
                                                           2: "He watches the gate carefully."},
                              room="100", level=45, boot="boot", visit=0, now=101)
    assessment.observe("He watches the gate carefully.\nThe watchman is in perfect health.\n", now=101.1)
    assert assessment.next_command(now=101.2) is None
    assessment.observe(PROMPT, now=101.3)
    assert assessment.next_command(now=101.4) == "consider #2"
    assessment.observe("The watchman looks like an easy kill.\n", now=101.5)
    assert assessment.plan["stage"] == "consider"
    assessment.observe("However, it is built like a tank!\n" + PROMPT, now=101.6)
    assert assessment.plan["stage"] == "admitted"
