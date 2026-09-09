from dataclasses import replace
from pathlib import Path

import pytest

from dd4tester.hunt_candidates import ACT_AGGRESSIVE, MobileProgram, load_world_source
from dd4tester.observations import GameEvent
from test_starter_bystanders import _encounter


def _loot_encounter():
    policy, state = _encounter()
    stop = replace(
        policy.fastwalk_hunt_stops[0],
        allow_below_band_for_required_loot=True,
        required_items=("a yellow and green ring",),
        source_reset_room_vnum=200,
        source_mobile_room_description="The illusionist is doing tricks here.",
        crowd_retry_limit=2,
        crowd_retry_delay_seconds=12.0,
    )
    policy.fastwalk_hunt_stops = (stop,)
    policy.source_mobile_vnums_by_target_room["midget"] = {"200": (101,)}
    policy.source_world.mobiles[101] = replace(policy.source_world.mobiles[101], level=5)
    policy.source_mobile_level_ranges_by_vnum[101] = (3, 7)
    state.move = 61
    return policy, state, stop


def test_required_loot_bystander_uses_existing_consider_then_target_assessment():
    policy, state, stop = _loot_encounter()
    assert policy._source_mobile_room_required_loot_hazards(state, "illusionist", stop)
    assert policy._fastwalk_endpoint_attacker_gate(state, "illusionist", stop) == (True, None)
    decision = policy._consider_fastwalk_target(state)
    assert decision.command == "consider #11"
    policy.after_command(decision)
    policy.observe_text("A midget is no match for you.\n")
    policy.observe_events([GameEvent("prompt_seen", "gmcp", {})], state)
    assert not policy._source_mobile_room_required_loot_hazards(state, "illusionist", stop)
    assert policy._consider_fastwalk_target(state).command == "consider #10"
    assert not policy.fastwalk_attack_started
    assert not policy.fastwalk_crowded


def test_required_loot_easy_bystander_uses_existing_crowd_budget(monkeypatch):
    policy, state, stop = _loot_encounter()
    monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: 100.0)
    assert policy._fastwalk_endpoint_attacker_gate(state, "illusionist", stop) == (True, None)
    decision = policy._consider_fastwalk_target(state)
    policy.after_command(decision)
    policy.observe_text("A midget looks like an easy kill.\n")
    policy.observe_events([GameEvent("prompt_seen", "gmcp", {})], state)
    for attempt in (1, 2):
        assert policy._fastwalk_endpoint_attacker_gate(state, "illusionist", stop) == (True, None)
        assert policy._consider_fastwalk_target(state) is None
        assert policy.fastwalk_crowd_retry_attempts[0] == attempt
        assert policy.fastwalk_crowd_retry_due == 112.0
        assert not policy.fastwalk_attack_started
    policy._consider_fastwalk_target(state)
    assert policy.fastwalk_crowded
    assert policy.fastwalk_crowd_retry_attempts[0] == 2
    assert policy.bystander_consider_attempts == 1


def test_run_12801_exact_carrier_and_bystander_reach_shared_assessment():
    policy, state, stop = _loot_encounter()
    world = load_world_source(Path("runs/dd4-source/server/area"), include_all_areas=True)
    policy.source_world = world
    target, bystander = world.mobiles[4005], world.mobiles[4004]
    assert bystander.wanders and not bystander.aggressive and not bystander.programs
    assert not world.mobile_specials.get(4004)
    stop = replace(
        stop, target="large orc", source_mobile_vnum=4005,
        source_mobile_room_description=target.room_description,
        source_reset_room_vnum=4034,
    )
    policy.fastwalk_hunt_stops = (stop,)
    policy.fastwalk_attack_target = "large orc"
    policy.current_room = state.room_vnum = "4034"
    policy.source_mobile_targets = {
        target.room_description.strip().casefold(): ("large orc",),
        bystander.room_description.strip().casefold(): ("orc",),
    }
    policy.source_mobile_vnums_by_target_room = {
        "large orc": {"4034": (4005,)}, "orc": {"4034": (4004,)},
    }
    policy.source_mobile_level_ranges_by_vnum = {4005: (3, 7), 4004: (3, 7)}
    policy.room_target_counts["4034"] = {"large orc": 1, "orc": 1}
    policy.room_targets["4034"] = ["large orc", "orc"]
    policy.room_target_selectors["4034"] = {
        "large orc": ("#23698",), "orc": ("#23632",),
    }
    policy.room_target_selector_descriptions["4034"] = {
        "#23698": target.room_description.strip().casefold(),
        "#23632": bystander.room_description.strip().casefold(),
    }
    policy.fastwalk_hunt_looked = True
    decision = policy._fastwalk_hunt_plan_decision(state)
    assert decision is not None, (policy.fastwalk_abort_reason, policy.fastwalk_crowd_retry_attempts,
                                  policy.bystander_consider_pending, policy._bystander_source_instance("orc", state))
    assert decision.command == "consider #23632", decision
    assert not policy.fastwalk_emergency_recall_pending
    assert not policy.fastwalk_attack_started


@pytest.mark.parametrize("change", [
    "aggression", "special", "script", "unknown", "multiple", "absent_target",
    "missing_target_id", "combat", "target_combat", "expired", "new_instance",
])
def test_required_loot_assessment_keeps_safety_and_fresh_identity(change, monkeypatch):
    policy, state, stop = _loot_encounter()
    if change in {"expired", "new_instance"}:
        monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: 100.0)
        policy.after_command(policy._consider_fastwalk_target(state))
        policy.observe_text("A midget is no match for you.\n")
        if change == "expired":
            monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: 131.0)
        else:
            policy.room_target_selectors["200"]["midget"] = ("#12",)
        assert policy._source_mobile_room_required_loot_hazards(state, "illusionist", stop)
        return
    mobile = policy.source_world.mobiles[101]
    if change == "aggression":
        policy.source_world.mobiles[101] = replace(mobile, act_flags=ACT_AGGRESSIVE)
    elif change == "special":
        policy.source_world.mobile_specials[101] = ("spec_poison",)
    elif change == "script":
        policy.source_world.mobiles[101] = replace(
            mobile, programs=(MobileProgram("greet_prog", "100", ("kill $n",)),),
        )
    elif change == "unknown":
        policy.room_target_selector_descriptions["200"].pop("#11")
    elif change == "multiple":
        policy.room_target_counts["200"]["midget"] = 2
        policy.room_target_selectors["200"]["midget"] = ("#11", "#12")
    elif change == "absent_target":
        policy.room_target_counts["200"].pop("illusionist")
    elif change == "missing_target_id":
        policy.room_target_selectors["200"].pop("illusionist")
    elif change == "combat":
        state.in_combat = True
    else:
        state.combat_target = "midget"
    allowed, decision = policy._fastwalk_endpoint_attacker_gate(state, "illusionist", stop)
    assert not allowed
    assert decision.command in {"flee", "recall"}
    assert policy.fastwalk_emergency_recall_pending
    assert policy.bystander_consider_attempts == 0
