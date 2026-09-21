from dataclasses import replace
from pathlib import Path
import re

import pytest

from dd4tester.character import CharacterSpec
from dd4tester.combat_capabilities import BASE_COMBAT_CAPABILITIES, SUBCLASS_COMBAT_CAPABILITIES
from dd4tester.combat_timing import (
    CombatCommandWindow, SPELL_NOUNS, SPELL_MIN_MANA, anticipatory_companion_withdrawal,
)
from dd4tester.companions import FamiliarPreparation
from dd4tester.dd4_catalog import _initializer_rows, _strings
from dd4tester.fastwalks import route_named
from dd4tester.hunt_candidates import MobileSource, WorldSource
from dd4tester.starter import BotDecision, FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


def test_timing_registry_matches_all_registered_direct_spells_and_current_source():
    registered = {cap.name for entries in (
        *BASE_COMBAT_CAPABILITIES.values(), *SUBCLASS_COMBAT_CAPABILITIES.values(),
    ) for cap in entries if cap.kind == "spell"}
    assert registered == SPELL_NOUNS.keys() == SPELL_MIN_MANA.keys()
    text = Path("runs/dd4-source/server/src/const.c").read_text(encoding="utf-8", errors="replace")
    checked = set()
    for row in _initializer_rows(text, "skill_table"):
        strings = _strings(row)
        if not strings or strings[0] not in registered:
            continue
        name = strings[0]
        assert re.sub(r"<\d+>", "", strings[1]) == SPELL_NOUNS[name]
        limits = re.search(r"\bspell_\w+\s*,\s*(\d+)\s*,\s*(\d+)\s*,", row)
        assert limits is not None
        assert tuple(map(int, limits.groups())) == (SPELL_MIN_MANA[name], 12)
        checked.add(name)
    assert checked == registered


@pytest.mark.parametrize("spell,noun", SPELL_NOUNS.items())
def test_damage_acknowledgement_does_not_clear_ensuing_wait(spell, noun):
    window = CombatCommandWindow()
    window.issue(f"cast '{spell}' #42", target="the guardian", now=0)
    reply = f"Your {noun} misses The guardian.\n"
    window.observe(reply[:12], now=.1)
    assert window.pending
    window.observe(reply[12:], now=.2)
    assert not window.pending and window.acknowledged == 1
    assert window.blocked(3.4)
    assert not window.blocked(3.5)


@pytest.mark.parametrize("spell,noun", SPELL_NOUNS.items())
def test_critical_hit_suffix_acknowledges_each_registered_spell(spell, noun):
    window = CombatCommandWindow()
    window.issue(f"cast '{spell}' #23715", target="The guardian", now=0)
    window.observe(f"Your {noun} mauls The guardian! *CRITICAL HIT*\n", now=.5)
    assert window.acknowledged == 1 and not window.pending
    assert window.blocked(3.5) and not window.blocked(4)
    assert not window.expired(10)


def test_run_12761_critical_reply_and_departure_allow_next_cast(monkeypatch):
    policy, state, clock = policy_fixture(monkeypatch)
    policy.familiar_disengagement_attempted = True
    policy.after_command(BotDecision("cast 'chill touch' #22916", "damage"))
    clock[0] = .5
    policy.observe_text("Your chilling touch mauls Katrina the Shepherd! *CRITICAL HIT*\n")
    clock[0] = 4
    policy.observe_text("The pony leaves east.\nThe pony has fled!\nOk.\n<113/113 hits 224/324 mana 199/220 move [Ultima]> ")
    assert policy._between_round_combat_decision(state).command == "cast 'chill touch' #22916"
    assert policy.combat_command_window.timeouts == 0


@pytest.mark.parametrize("reply", [
    "<113/113 hits 224/324 mana 199/220 move [Ultima]> ",
    "The pony grazes Katrina the Shepherd.\n",
    "Your pierce scratches Katrina the Shepherd.\n",
    "Someone says 'Your chilling touch grazes Katrina the Shepherd.'\n",
    "Your chilling touch grazes another opponent.\n", "Ok.\n",
])
def test_unsolicited_round_or_other_reply_cannot_acknowledge_a_spell(reply):
    window = CombatCommandWindow()
    window.issue("cast 'chill touch' #42", target="Katrina the Shepherd", now=0)
    window.observe(reply, now=4)
    assert window.pending and window.blocked(4)
    assert not window.expired(9.9) and window.expired(10)


def test_source_refusal_acknowledges_without_replaying_the_command():
    window = CombatCommandWindow()
    window.issue("cast 'chill touch' #42", target="target", now=0)
    window.observe("You don't have enough mana.\n", now=.2)
    assert not window.pending and window.blocked(1)
    assert not window.expired(100)
    window.reset()
    assert not window.blocked(1) and window.evidence()["acknowledged"] == 1
    assert "command" not in window.evidence()


def finish_args():
    return dict(
        enemy_hp=34, enemy_max_hp=50, companion_level=16,
        player_hp=113, player_max_hp=113, mana=224, max_mana=324,
        source_peak=100, source_critical=40, action_damage=18,
        action_cost=25, maximum_actions=8,
        expected_incoming_per_round=11,
    )


def test_fragile_live_target_withdraws_before_another_lagged_action():
    assert anticipatory_companion_withdrawal(**finish_args())


def test_early_withdrawal_rejects_unknown_companion_damage_modifier():
    assert not anticipatory_companion_withdrawal(
        **(finish_args() | {"companion_damage_modifier": None})
    )


@pytest.mark.parametrize("changes", [
    {"enemy_hp": 40}, {"player_hp": 75}, {"enemy_max_hp": 30},
    {"source_peak": 113}, {"source_critical": 60}, {"action_damage": 1},
    {"mana": 80}, {"maximum_actions": 1}, {"action_cost": 0},
    {"expected_incoming_per_round": 24},
])
def test_early_withdrawal_requires_a_short_funded_finish(changes):
    assert not anticipatory_companion_withdrawal(**(finish_args() | changes))


def policy_fixture(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: clock[0])
    spec = CharacterSpec.from_mapping({
        "name": "Testmage", "race": "human", "gender": "female", "class": "mage",
    })
    policy = StarterPolicy(
        spec, "fixture-password", fastwalk_route=route_named("moria"),
        known_skill_levels={"chill touch": 35, "summon familiar": 36},
        source_world=WorldSource(mobiles={19900: MobileSource(
            19900, "pony", "the pony", 15, 0, 0, "mounts.are",
            "A small pony stands here grazing.",
        )}),
        fastwalk_hunt_stops=(FieldHuntStop(
            (), "Katrina the Shepherd", source_mobile_vnum=2405,
            source_peak_round_damage=100, source_critical_hit_damage=40,
            source_target_armed=True,
            source_combat_action="chill touch", source_combat_conservative_damage=18,
            source_combat_max_actions=8, require_familiar=True,
        ),),
    )
    policy.in_world = policy.combat_active = policy.fastwalk_attack_started = True
    policy.active_target = "Katrina the Shepherd"
    policy.active_target_selector = "#22916"
    policy.current_room = "2415"
    state = CharacterState(
        level=8, hp=113, max_hp=113, mana=224, max_mana=324,
        room_vnum="2415", position=6, in_combat=True,
        enemies=[[{"name": "Katrina the Shepherd", "isnpc": "2405", "level": "5", "hp": "34", "maxhp": "50"}]],
    )
    return policy, state, clock


def test_run_12745_background_round_cannot_queue_second_chill_touch(monkeypatch):
    policy, state, clock = policy_fixture(monkeypatch)
    policy.fastwalk_hunt_stops = (replace(policy.fastwalk_hunt_stops[0], require_familiar=False),)
    policy.after_command(BotDecision("kill #22916", "open"))
    clock[0] = .2
    policy.observe_text("Your pierce misses Katrina the Shepherd.\n")
    assert policy._between_round_combat_decision(state) is None
    clock[0] = 3.5
    first = policy._between_round_combat_decision(state)
    assert first.command == "cast 'chill touch' #22916"
    policy.after_command(first)
    clock[0] = 6.7
    policy.observe_text("The pony scratches Katrina the Shepherd.\n<113/113 hits 224/324 mana 199/220 move [Ultima]> ")
    assert not policy.between_round_action_issued  # Legacy prompt parsing is not authoritative.
    assert policy._between_round_combat_decision(state) is None
    clock[0] = 6.8
    policy.observe_text("\nYour chilling touch grazes Katrina the Shepherd.\n")
    assert policy._between_round_combat_decision(state) is None
    clock[0] = 10.1
    assert policy._between_round_combat_decision(state).command == "cast 'chill touch' #22916"


def test_run_12745_fragile_target_queues_withdrawal_ahead_of_first_spell(monkeypatch):
    policy, state, clock = policy_fixture(monkeypatch)
    policy.familiar_active = True
    policy.familiar_preparation = FamiliarPreparation(stage="ready", selector="#23679", summoned=True, grouped=True)
    policy.after_command(BotDecision("kill #22916", "open"))
    clock[0] = .2
    policy.observe_text("Your pierce misses Katrina the Shepherd.\n")
    decision = policy._between_round_combat_decision(state)
    assert decision.command == "order #23679 flee"
    assert "short finishing reserve" in decision.reason
    assert policy.combat_command_window.evidence()["early_withdrawals"] == 1
    assert policy._between_round_combat_decision(state) is None


def test_standard_withdrawal_preempts_pending_spell_and_cooldown(monkeypatch):
    policy, state, clock = policy_fixture(monkeypatch)
    policy.familiar_active = True
    policy.familiar_preparation.selector = "#23679"
    state.enemies[0][0]["hp"] = "15"
    policy.between_round_action_issued = True
    policy.between_round_action_ready_at = 100
    policy.combat_command_window.issue("cast 'chill touch' #22916", target=policy.active_target, now=0)
    assert policy._between_round_combat_decision(state).command == "order #23679 flee"


def test_missing_acknowledgement_suspends_injection_without_fleeing_a_healthy_fight(monkeypatch):
    policy, state, clock = policy_fixture(monkeypatch)
    policy.fastwalk_hunt_stops = (replace(policy.fastwalk_hunt_stops[0], require_familiar=False),)
    policy.after_command(BotDecision("cast 'chill touch' #22916", "damage"))
    clock[0] = 10
    assert policy._between_round_combat_decision(state) is None
    assert not policy.fastwalk_returning
    assert policy.combat_command_window.evidence()["timeouts"] == 1
    clock[0] = 20
    assert policy._between_round_combat_decision(state) is None
    assert policy.combat_command_window.evidence()["timeouts"] == 1
    policy.after_command(BotDecision("recall", "normal survival boundary"))
    assert not policy.combat_command_window.blocked(clock[0])


def test_late_matching_reply_resumes_only_after_source_wait():
    window = CombatCommandWindow()
    window.issue("cast 'chill touch' #42", target="the guardian", now=0)
    window.suspend()
    window.observe("Your chilling touch hits the guardian.\n", now=11)
    assert not window.suspended and window.blocked(14)
    assert not window.blocked(14.5) and window.timeouts == 1


def test_pending_command_does_not_delay_required_companion_loss(monkeypatch):
    policy, state, clock = policy_fixture(monkeypatch)
    policy.combat_command_window.issue("cast 'chill touch' #22916", target=policy.active_target, now=0)
    assert policy._between_round_combat_decision(state).command == "flee"


def test_run_12747_binds_source_combat_name_instead_of_room_alias(monkeypatch):
    policy, state, clock = policy_fixture(monkeypatch)
    policy.source_world.mobiles[4002] = MobileSource(
        4002, "centipede", "the centipede", 4, 0, 0, "moria.are",
        "A small centipede here is looking for vegetation.",
    )
    policy.fastwalk_hunt_stops = (FieldHuntStop((), "small centipede", source_mobile_vnum=4002),)
    policy.active_target = "small centipede"
    policy.after_command(BotDecision("kill #2753", "open"))
    assert policy.combat_command_window.target == "centipede"
    clock[0] = .5
    policy.observe_text("Your pierce misses the centipede.\n")
    assert policy.combat_command_window.acknowledged == 1
    assert not policy.combat_command_window.pending
    assert not policy.combat_command_window.expired(100)


def test_real_source_katrina_stop_preserves_entry_gate_and_enables_short_finish(monkeypatch):
    import dd4tester.campaign as campaign
    world = campaign.load_world_source(Path("runs/dd4-source/server/area"), include_all_areas=True)
    state = {
        "level": 8, "max_hp": 113, "max_mana": 324, "character_class": "mage",
        "world_boot_id": "fixture-boot", "campaign_known_skills": ["chill touch", "summon familiar"],
        "campaign_known_skill_levels": {"chill touch": 35, "summon familiar": 36},
    }
    candidates = campaign.rank_hunt_candidates(
        world, character_level=8, character_class="mage",
        known_skills=state["campaign_known_skills"], known_skill_levels=state["campaign_known_skill_levels"],
        include_xp_only=True, include_level_ceiling_candidates=True,
        level_ceiling_offset=1, include_all_areas=True, character_max_hp=113,
        recall_origins={0: 3001},
    )
    target = next(t for t in candidates if t.mobile_vnum == 2405 and t.room_vnum == 2415)
    stops = [s for s in campaign._source_ranked_hunt_stops(target, world, character_level=8, state=state)
             if s.source_mobile_vnum == 2405]
    assert stops and all(s.require_familiar for s in stops)
    for stop in stops:
        assert stop.source_peak_round_damage is None
        assert stop.source_familiar_finish_peak_round_damage == target.estimated_peak_round_damage
    policy, live, clock = policy_fixture(monkeypatch)
    policy.source_world = world
    policy.fastwalk_hunt_stops = (stops[0],)
    policy.familiar_active = True
    policy.familiar_preparation.selector = "#23679"
    decision = policy._between_round_combat_decision(live)
    assert decision.command == "order #23679 flee Fear"
    assert "short finishing reserve" in decision.reason
