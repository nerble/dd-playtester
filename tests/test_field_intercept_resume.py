from dataclasses import replace

import pytest

from dd4tester.character import CharacterSpec
from dd4tester.fastwalks import Fastwalk
from dd4tester.starter import FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


def intercepted_route(*, later_stop=True):
    stop = FieldHuntStop(
        (), "the orc", exact_target=True, source_mobile_vnum=4004,
        route_vnums=("4001", "4002", "4010", "4011", "4014"),
        source_policy_id="source-ranked-hunt-moria-4004-4028-11",
    )
    stops = (stop,)
    if later_stop:
        stops += (replace(stop, route_vnums=("4015",)),)
    spec = CharacterSpec.from_mapping({
        "name": "Testchar", "race": "human", "gender": "female", "class": "thief",
    })
    policy = StarterPolicy(
        spec, "unused", fastwalk_route=Fastwalk("field route", 1, 100, "n"),
        fastwalk_hunt_stops=stops,
        source_mobile_level_ranges_by_vnum={4004: (3, 7)},
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_outbound_index = 1
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_targetmode_configured = True
    policy.fastwalk_hunt_move_index = 3
    policy.current_room = "4010"
    policy.room_targets["4010"] = ["the orc"]
    policy.room_target_selectors["4010"] = {"the orc": ["#2763"]}
    state = CharacterState(
        level=11, hp=186, max_hp=186, mana=172, max_mana=172,
        move=243, max_move=250, room_vnum="4010",
        exits={"n": "4011", "s": "4002"}, position=7,
        hunger=16, thirst=47,
    )
    decision = policy._fastwalk_live_target_intercept_decision(
        state, during_field_circuit=True,
    )
    assert decision is not None and decision.command == "consider #2763"
    policy.after_command(decision)
    policy.observe_text(
        "The orc is no match for you.\n\r"
        "Also, you are currently much healthier than he.\n\r\n\r"
        "<186/186 hits 172/172 mana 243/250 move [Moria]> "
    )
    decision = policy._fastwalk_intercept_followup_decision(state)
    assert decision is not None and decision.command == "look"
    return policy, state


@pytest.mark.parametrize("later_stop", [False, True])
def test_run_12822_rejected_waypoint_resumes_original_route(later_stop):
    policy, state = intercepted_route(later_stop=later_stop)
    stops = policy.fastwalk_hunt_stops
    assert policy._fastwalk_intercept_followup_decision(state) is None
    assert policy.fastwalk_hunt_stop_index == 0
    assert policy.fastwalk_hunt_move_index == 3
    assert not policy.fastwalk_hunt_stop_skipped
    assert policy.fastwalk_intercept_resume_context is None
    assert policy.consider_viable is None
    assert ("4010", "the orc") in policy.fastwalk_below_band_sightings
    decision = policy._fastwalk_hunt_plan_decision(state)
    assert decision is not None and decision.command == "north"
    assert policy.fastwalk_hunt_move_index == 4
    assert policy.fastwalk_hunt_stop_index == 0
    assert policy.fastwalk_hunt_stops == stops
    assert not policy.fastwalk_returning and not policy.fastwalk_abort_reason


def test_old_intercept_handoff_reproduces_nonadjacent_next_leg(monkeypatch):
    policy, state = intercepted_route()
    monkeypatch.setattr(policy, "_intercepted_field_route_can_resume", lambda: False)
    assert policy._fastwalk_intercept_followup_decision(state) is None
    decision = policy._fastwalk_hunt_plan_decision(state)
    assert decision is not None and decision.command == "recall"
    assert policy.fastwalk_abort_reason == "field route could not find GMCP exit to room 4015"


def test_resumed_route_requires_fresh_consider_at_unvisited_endpoint():
    policy, state = intercepted_route(later_stop=False)
    policy._fastwalk_intercept_followup_decision(state)
    policy.current_room = state.room_vnum = "4014"
    policy.fastwalk_hunt_move_index = 5
    policy.room_targets["4014"] = ["the orc"]
    policy.room_target_selectors["4014"] = {"the orc": ["#7000"]}
    decision = policy._fastwalk_hunt_plan_decision(state)
    assert decision is not None and decision.command == "consider #7000"
    assert policy.consider_viable is None
    assert not policy.fastwalk_attack_started
    assert ("4010", "the orc") in policy.fastwalk_below_band_sightings


@pytest.mark.parametrize("boundary", [
    "room", "endpoint", "explicit_abort", "crowded", "route_hazard",
    "missing_context", "missing_below_band", "raw_route", "different_stop",
])
def test_field_route_resume_requires_the_exact_unfinished_waypoint(boundary):
    policy, state = intercepted_route(later_stop=False)
    if boundary == "room":
        policy.current_room = "4012"
    elif boundary == "endpoint":
        context = policy.fastwalk_intercept_resume_context
        policy.fastwalk_intercept_resume_context = (context[0], 5, *context[2:])
    elif boundary == "explicit_abort":
        policy.fastwalk_hunt_stops = (replace(
            policy.fastwalk_hunt_stops[0], abort_after_consider_rejection=True,
        ),)
    elif boundary == "crowded":
        policy.fastwalk_crowded = True
    elif boundary == "route_hazard":
        policy.fastwalk_abort_reason = "observed route hazard"
    elif boundary == "missing_context":
        policy.fastwalk_intercept_resume_context = None
    elif boundary == "missing_below_band":
        policy.fastwalk_below_band_sightings.clear()
    elif boundary == "raw_route":
        policy.fastwalk_hunt_stops = (replace(
            policy.fastwalk_hunt_stops[0], route=("north",),
        ),)
    else:
        context = policy.fastwalk_intercept_resume_context
        policy.fastwalk_intercept_resume_context = (1, *context[1:])
    assert not policy._intercepted_field_route_can_resume()
    decision = policy._fastwalk_intercept_followup_decision(state)
    assert decision is not None and decision.command == "recall"
    assert policy.fastwalk_returning
