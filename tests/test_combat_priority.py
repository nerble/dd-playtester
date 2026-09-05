from dataclasses import replace
import time

import pytest

from dd4tester.character import CharacterSpec
from dd4tester.fastwalks import route_named
from dd4tester.observations import GameEvent
from dd4tester.starter import FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


def field_policy(character_class: str = "mage") -> StarterPolicy:
    spec = CharacterSpec.from_mapping({
        "name": "Replaytester",
        "race": "human",
        "gender": "female",
        "class": character_class,
        "title": "",
    })
    policy = StarterPolicy(
        spec,
        "unused-test-password",
        fastwalk_route=route_named("foundry captain"),
        fastwalk_attack_target="the giant, purple sand worm",
        fastwalk_hunt_stops=(FieldHuntStop((), "the giant, purple sand worm"),),
        source_mobile_level_ranges={"the drider": (7, 13)},
        known_skills=("chill touch", "magic missile", "kick"),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = 4
    return policy


def interrupted_combat(hp: int = 37) -> CharacterState:
    enemy = {
        "name": "the drider", "level": "8", "hp": "45",
        "maxhp": "87", "isnpc": "5011",
    }
    return CharacterState(
        level=18, hp=hp, max_hp=218, mana=581, max_mana=628,
        move=274, max_move=320, position=6, in_combat=True,
        room_vnum="5028", room_name="The Great Eastern Desert",
        room_flags=["no_recall"], enemies=[[enemy, dict(enemy)]],
    )


@pytest.mark.parametrize("character_class", ["mage", "thief", "warrior"])
@pytest.mark.parametrize("already_adopted", [False, True])
def test_transit_combat_cannot_bypass_survival_limits(
    character_class: str, already_adopted: bool,
) -> None:
    policy = field_policy(character_class)
    state = interrupted_combat()
    policy.observe_events([
        GameEvent("enemies_changed", "gmcp", {"value": state.enemies}),
    ], state)
    policy._record_field_combat_damage(replace(state, hp=101))
    policy.fastwalk_transit_below_band_return_pending = already_adopted
    policy.fastwalk_transit_below_band_target = "the drider"

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "flee"
    assert "health" in decision.reason
    assert policy.fastwalk_emergency_recall_pending


def test_transit_combat_uses_observed_damage_reserve() -> None:
    policy = field_policy()
    state = interrupted_combat(101)
    policy.observe_events([
        GameEvent("enemies_changed", "gmcp", {"value": state.enemies}),
    ], state)
    policy._record_field_combat_damage(replace(state, hp=154))
    policy.fastwalk_transit_below_band_return_pending = True

    decision = policy.next_decision(state)

    assert policy.field_combat_max_observed_damage == 53
    assert decision is not None
    assert decision.command == "flee"


def test_healthy_transit_combat_keeps_attacking() -> None:
    policy = field_policy()
    state = interrupted_combat(218)
    policy.observe_events([
        GameEvent("enemies_changed", "gmcp", {"value": state.enemies}),
    ], state)
    policy.fastwalk_transit_below_band_return_pending = True

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command.startswith("cast ") or decision.command == "kick"


def test_zero_percent_known_skill_is_not_used_as_a_combat_action() -> None:
    policy = field_policy("warrior")
    policy.known_skills = {"kick"}
    policy.known_skill_levels = {"kick": 0}
    policy.active_target = "the drider"

    decision = policy._between_round_combat_decision(interrupted_combat(218))

    assert decision is None
    assert policy.between_round_action_issued is False


def test_caster_skips_zero_percent_damage_spell_for_known_fallback() -> None:
    policy = field_policy("mage")
    policy.known_skills = {"burning hands", "magic missile"}
    policy.known_skill_levels = {"burning hands": 0, "magic missile": 25}
    policy.active_target = "the drider"

    decision = policy._between_round_combat_decision(interrupted_combat(218))

    assert decision is not None
    assert decision.command == "cast 'magic missile' drider"


@pytest.mark.parametrize("known_burning_hands, expected", [
    (True, "burning hands"), (False, "chill touch"),
])
def test_mage_damage_upgrade_requires_an_observed_skill(
    known_burning_hands: bool, expected: str,
) -> None:
    policy = field_policy()
    policy.known_skills = {"chill touch", "magic missile"}
    if known_burning_hands:
        policy.known_skills.add("burning hands")
    state = interrupted_combat(218)
    policy.observe_events([
        GameEvent("enemies_changed", "gmcp", {"value": state.enemies}),
    ], state)
    policy.fastwalk_transit_below_band_return_pending = True

    first = policy.next_decision(state)
    policy.between_round_action_issued = False
    policy.between_round_action_ready_at = 0
    policy.prompt_ready = True
    second = policy.next_decision(state)

    assert first is not None and second is not None
    assert first.command.startswith(f"cast '{expected}' ")
    assert second.command.startswith(f"cast '{expected}' ")


def test_duplicated_gmcp_cannot_hide_a_text_observed_attacker() -> None:
    policy = field_policy()
    state = interrupted_combat(154)
    policy.observe_text(
        "The drider's slash hits you.\n"
        "The giant, purple sand worm misses you.\n"
        "The giant, purple sand worm injures you!\n"
    )
    policy.observe_events([
        GameEvent("enemies_changed", "gmcp", {"value": state.enemies}),
    ], state)
    policy.prompt_ready = True

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "flee"
    assert "duplicated GMCP" in decision.reason
    assert "worm" in decision.reason


@pytest.mark.parametrize("extra_line", [
    "The drider misses you.",
    "The drider's slash misses you.",
    "The harmless bystander hits you.",
])
def test_duplicate_enemy_report_does_not_alone_force_withdrawal(extra_line: str) -> None:
    policy = field_policy()
    policy.fastwalk_hunt_stops = (replace(
        policy.fastwalk_hunt_stops[0],
        trivial_bystanders=("the harmless bystander",),
    ),)
    state = interrupted_combat(218)
    policy.observe_text("The drider's slash misses you.\n" + extra_line)
    policy.observe_events([
        GameEvent("enemies_changed", "gmcp", {"value": state.enemies}),
    ], state)
    policy.prompt_ready = True
    policy.fastwalk_transit_below_band_return_pending = True

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command != "flee"


@pytest.mark.parametrize("dead_flag", [False, True])
def test_purgatory_preempts_stale_field_and_logout_work(dead_flag: bool) -> None:
    policy = field_policy()
    policy.fastwalk_emergency_recall_pending = True
    policy.utility_emergency_recall_pending = True
    policy.pending_recall_origin = "401"
    policy.pending_travel_origin = "5028"
    policy.gear_response_expectation = "wear"
    policy.fastwalk_crowd_retry_due = time.monotonic() + 60
    policy.request_runtime_boundary()
    state = CharacterState(
        dead=dead_flag, area="Purgatory", room_vnum="401",
        room_name="The Purgatory", hp=1, max_hp=212, position=7,
        exits={"east": "410"},
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "east"
    assert not policy.midgaard_logout_pending
    assert not policy.fastwalk_emergency_recall_pending
    assert policy.pending_recall_origin is None
    assert policy.gear_response_expectation is None


def test_purgatory_movement_still_waits_for_a_response() -> None:
    policy = field_policy()
    policy.prompt_ready = False
    state = CharacterState(dead=True, area="Purgatory", room_vnum="401")

    assert policy.next_decision(state) is None


def test_corpse_recovery_restores_gear_before_resuming_fastwalk_state() -> None:
    policy = field_policy()
    state = CharacterState(
        area="Purgatory", room_vnum="427", hp=1, max_hp=212, position=7,
    )
    assert policy.next_decision(state).command == "get all corpse"
    assert policy.next_decision(state).command == "inventory"
    assert policy.next_decision(state).command == "enter portal"
    healer = replace(state, area="Midgaard", room_vnum="3054")

    decision = policy.next_decision(healer)

    assert decision is not None
    assert decision.command == "wear all"
