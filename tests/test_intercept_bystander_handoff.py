from dataclasses import replace

import pytest

from dd4tester import starter
from dd4tester.character import CharacterSpec
from dd4tester.fastwalks import Fastwalk
from dd4tester.hunt_candidates import ACT_SENTINEL, MobileSource, WorldSource
from dd4tester.observations import GameEvent
from dd4tester.starter import FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


def library_intercept():
    """Run 12821: two exact instances at an already-planned tower stop."""
    target = "hobgoblin servant"
    description = "a hobgoblin servant looks at you fearfully."
    mobile = MobileSource(
        9411, "hobgoblin servant", "a hobgoblin servant", 8, ACT_SENTINEL, 0,
        "fleshmonger.are", room_description=description,
    )
    stop = FieldHuntStop(
        (), target, exact_target=True, require_isolated=True,
        source_mobile_vnum=9411, source_mobile_room_description=description,
        route_vnums=("9418",),
    )
    policy = StarterPolicy(
        CharacterSpec.from_mapping({
            "name": "Testchar", "race": "human", "gender": "female", "class": "thief",
        }),
        "unused", source_world=WorldSource(mobiles={9411: mobile}),
        fastwalk_route=Fastwalk("tower route", 1, 100, "uu"),
        fastwalk_hunt_stops=(stop, replace(stop, route_vnums=("9417",))),
        source_mobile_targets={description: (target,)},
        source_mobile_vnums_by_target_room={target: {"9417": (9411,), "9418": (9411,)}},
        source_mobile_level_ranges_by_vnum={9411: (6, 10)},
    )
    policy.in_world = policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_targetmode_configured = True
    policy.fastwalk_outbound_index = 1
    policy.current_room = "9417"
    policy.world_boot_id = "test-boot"
    policy.room_targets["9417"] = [target]
    policy.room_target_counts["9417"] = {target: 2}
    policy.room_target_selectors["9417"] = {target: ("#23815", "#4903")}
    policy.room_target_selector_descriptions["9417"] = {
        selector: description for selector in ("#23815", "#4903")
    }
    state = CharacterState(
        level=11, hp=186, max_hp=186, mana=172, max_mana=172,
        move=243, max_move=250, room_vnum="9417", position=7, enemies=[],
        hunger=16, thirst=47, exits={"u": "9418", "d": "9416"},
    )
    decision = policy._fastwalk_live_target_intercept_decision(state)
    assert decision is not None and decision.command == "consider #23815"
    policy.after_command(decision)
    assert policy.fastwalk_hunt_stop_index == 1
    assert policy.fastwalk_intercept_returning
    return policy, state


def reply(policy, state, text):
    policy.observe_text(text + "\n\r")
    policy.observe_events([GameEvent("prompt_seen", "gmcp", {})], state)


def test_run_12821_bystander_completion_reconsiders_second_instance_before_travel():
    policy, state = library_intercept()
    stops = policy.fastwalk_hunt_stops
    reply(policy, state, "A hobgoblin servant is no match for you.")
    assert policy.consider_target is None
    decision = policy._fastwalk_research_decision(state)
    assert decision is not None and decision.command == "consider #4903"
    assert policy.fastwalk_outbound_index == 1
    assert policy.fastwalk_hunt_stop_index == 1
    assert policy.fastwalk_hunt_stops == stops
    assert policy.consider_viable is None
    assert not policy.fastwalk_attack_started
    assert policy.bystander_consider_attempts == 1


def test_second_instance_needs_its_own_result_before_attack_or_movement():
    policy, state = library_intercept()
    reply(policy, state, "A hobgoblin servant is no match for you.")
    decision = policy._fastwalk_intercept_followup_decision(state)
    assert decision is not None and decision.command == "consider #4903"
    policy.after_command(decision)
    assert policy._fastwalk_research_decision(state) is None
    assert policy.fastwalk_outbound_index == 1
    assert not policy.fastwalk_attack_started


def test_both_below_band_instances_end_evaluation_without_attack_or_retry():
    policy, state = library_intercept()
    reply(policy, state, "A hobgoblin servant is no match for you.")
    decision = policy._fastwalk_intercept_followup_decision(state)
    assert decision is not None and decision.command == "consider #4903"
    policy.after_command(decision)
    reply(policy, state, "A hobgoblin servant is no match for you.")
    assert policy._fastwalk_research_decision(state).command == "look"
    assert policy._fastwalk_research_decision(state).command == "recall"
    assert policy.consider_viable is False
    assert not policy.fastwalk_attack_started
    assert policy.bystander_consider_attempts == 1


@pytest.mark.parametrize("seconds", [0, 4.99])
def test_silent_bystander_check_holds_travel_without_duplicate_probe(seconds, monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(starter.time, "monotonic", lambda: clock[0])
    policy, state = library_intercept()
    clock[0] += seconds
    assert policy.next_decision(state) is None
    assert policy.fastwalk_outbound_index == 1
    assert policy.bystander_consider_attempts == 1
    assert not policy.fastwalk_crowded


def test_intercept_still_owns_travel_when_evaluation_temporarily_has_no_command(monkeypatch):
    policy, state = library_intercept()
    reply(policy, state, "A hobgoblin servant is no match for you.")
    monkeypatch.setattr(policy, "_consider_fastwalk_target", lambda state: None)
    assert policy._fastwalk_research_decision(state) is None
    assert policy.fastwalk_outbound_index == 1


def test_positive_second_consider_opens_only_the_exact_remaining_target():
    policy, state = library_intercept()
    reply(policy, state, "A hobgoblin servant is no match for you.")
    decision = policy._fastwalk_research_decision(state)
    assert decision.command == "consider #4903"
    policy.after_command(decision)
    reply(policy, state, "A hobgoblin servant looks like an easy kill.")
    decision = policy._fastwalk_research_decision(state)
    assert decision is not None and decision.command == "kill #4903"
    assert policy.fastwalk_outbound_index == 1
    assert policy.active_target_selector == "#4903"


def test_positive_consider_does_not_bypass_the_source_level_gate():
    policy, state = library_intercept()
    reply(policy, state, "A hobgoblin servant is no match for you.")
    policy.fastwalk_hunt_stops = tuple(
        replace(stop, maximum_level_offset=-4) for stop in policy.fastwalk_hunt_stops
    )
    decision = policy._fastwalk_research_decision(state)
    policy.after_command(decision)
    reply(policy, state, "A hobgoblin servant looks like an easy kill.")
    decision = policy._fastwalk_research_decision(state)
    assert decision is not None and decision.command == "look"
    assert policy.fastwalk_hunt_stop_skipped
    assert not policy.fastwalk_attack_started


@pytest.mark.parametrize("boundary", ["timeout", "combat"])
def test_pending_intercept_bystander_remains_bounded_and_combat_preemptible(boundary, monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(starter.time, "monotonic", lambda: clock[0])
    policy, state = library_intercept()
    if boundary == "timeout":
        clock[0] = 105.0
    else:
        state.in_combat = policy.combat_active = True
        state.position = 6
    policy.next_decision(state)
    assert "#23815" in policy.bystander_consider_results
    assert not policy.bystander_consider_results["#23815"]["below_assistance_band"]
    assert policy.fastwalk_outbound_index == 1
    if boundary == "combat":
        assert policy._fastwalk_intercept_followup_decision(state) is None


@pytest.mark.parametrize("boundary", ["runtime", "emergency"])
def test_return_boundary_preempts_intercept_followup(boundary):
    policy, state = library_intercept()
    reply(policy, state, "A hobgoblin servant is no match for you.")
    if boundary == "runtime":
        policy.request_runtime_boundary(state)
    else:
        policy.fastwalk_emergency_recall_pending = True
    decision = policy._fastwalk_research_decision(state)
    assert decision is not None and decision.command == "recall"
    assert policy.consider_target is None


def test_direct_followup_during_bystander_silence_does_not_label_the_room_crowded():
    policy, state = library_intercept()
    assert policy._fastwalk_intercept_followup_decision(state) is None
    assert not policy.fastwalk_crowded
    assert policy.bystander_consider_attempts == 1
