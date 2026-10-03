from copy import deepcopy
import json

import pytest

from dd4tester.campaign import (
    _campaign_segment_end_state,
    _quest_cooldown_wait_has_no_progress,
    _required_quest_cooldown_wait_allowed,
    _repair_completed_quest_wait_from_segments,
    _legacy_quest_reader_recheck_allowed,
)


def checkpoint():
    return {
        "level": 29, "world_boot_id": "boot", "room_vnum": "3054",
        "area": "Midgaard", "room_flags": ["safe", "healing"],
        "hp": 666, "max_hp": 666, "move": 482, "max_move": 482,
        "mana": 261, "max_mana": 261, "stats": {"fame": 0},
        "quest_status": {"active": 0, "nextquest": 1, "total_points": 0},
        "campaign_quest_cooldown_wait": {"boot_id": "boot", "level": 29, "remaining": 15},
        "campaign_quest_frontier_request": {
            "boot_id": "boot", "level": 29, "session_revision": 235,
            "reason": "live quest request dispatched",
        },
    }


def test_required_level_gate_wait_survives_consumed_optional_frontier_request():
    state = checkpoint()
    original = deepcopy(state)
    assert _required_quest_cooldown_wait_allowed(state, has_food=True)
    assert state == original


@pytest.mark.parametrize("changes", [
    {"level": 28}, {"room_vnum": "3001"}, {"hp": 200}, {"move": 1},
    {"in_combat": True}, {"dead": True}, {"world_boot_id": None},
    {"stats": {"fame": -1}}, {"stats": {}},
    {"quest_status": {"active": 1, "nextquest": 1, "total_points": 0}},
    {"quest_status": {"active": 0, "nextquest": 0, "total_points": 0}},
    {"quest_status": {"active": 0, "nextquest": 1, "total_points": 1}},
    {"quest_status": {"active": 0, "nextquest": 1}},
    {"quest_status": {"active": 0, "nextquest": 1, "total_points": "unknown"}},
    {"quest_status": {"active": 0, "nextquest": 1, "total_points": -1}},
])
def test_required_wait_keeps_level_readiness_reputation_and_observation_gates(changes):
    state = checkpoint()
    state.update(changes)
    assert not _required_quest_cooldown_wait_allowed(state, has_food=True)


def test_required_wait_needs_food_and_does_not_repeat_an_unchanged_counter():
    state = checkpoint()
    assert not _required_quest_cooldown_wait_allowed(state, has_food=False)
    state["campaign_quest_cooldown_wait"]["remaining"] = 1
    assert not _required_quest_cooldown_wait_allowed(state, has_food=True)


def completed_cycle():
    state = checkpoint()
    state["quest_status"]["nextquest"] = 15
    state["campaign_quest_cooldown_wait"]["remaining"] = 1
    state["campaign_quest_phases"] = [
        {"phase": "quest-cooldown", "state": {"quest_status": {
            "active": 0, "nextquest": 0,
        }}},
        {"phase": "quest-request", "state": {"quest_status": {
            "active": 1, "nextquest": 0, "countdown": 16,
            "room_vnum": 10420, "object_vnum": 588,
        }}},
    ]
    return state


def test_accepted_assignment_distinguishes_new_cooldown_from_stalled_wait():
    state = completed_cycle()
    assert not _quest_cooldown_wait_has_no_progress(state)
    assert _required_quest_cooldown_wait_allowed(state, has_food=True)
    # Starting another wait consumes the prior session's phase evidence.
    state.pop("campaign_quest_phases")
    state["campaign_quest_cooldown_wait"]["remaining"] = 15
    assert _quest_cooldown_wait_has_no_progress(state)


@pytest.mark.parametrize("kind", ["no_dispatch", "other_boot", "wrong_order", "uncleared", "unassigned"])
def test_new_cycle_requires_completed_wait_then_observed_assignment(kind):
    state = completed_cycle()
    if kind == "no_dispatch":
        state["campaign_quest_frontier_request"]["reason"] = "policy selected"
    elif kind == "other_boot":
        state["campaign_quest_frontier_request"]["boot_id"] = "old"
    elif kind == "wrong_order":
        state["campaign_quest_phases"].reverse()
    elif kind == "uncleared":
        state["campaign_quest_phases"][0]["state"]["quest_status"]["nextquest"] = 1
    else:
        state["campaign_quest_phases"][1]["state"]["quest_status"]["active"] = 0
    assert _quest_cooldown_wait_has_no_progress(state)


def test_completed_wait_remains_closed_through_unrelated_maintenance():
    previous = completed_cycle()
    maintenance = checkpoint()
    maintenance.pop("campaign_quest_cooldown_wait")
    maintenance.pop("campaign_quest_frontier_request")
    maintenance["quest_status"]["nextquest"] = 6
    merged = _campaign_segment_end_state(previous, maintenance, execution="restock")
    assert merged["campaign_quest_cooldown_wait"] is None
    assert _required_quest_cooldown_wait_allowed(merged, has_food=True)


def test_new_wait_without_timer_progress_still_closes_after_maintenance():
    previous = checkpoint()
    previous["campaign_quest_cooldown_wait"]["remaining"] = 1
    current = deepcopy(previous)
    current.pop("campaign_quest_cooldown_wait")
    merged = _campaign_segment_end_state(previous, current, execution="restock")
    assert _quest_cooldown_wait_has_no_progress(merged)


def test_legacy_wait_completion_is_restored_from_recent_successful_segment():
    end = completed_cycle()
    state = deepcopy(end)
    state.pop("campaign_quest_phases")
    state["quest_status"]["nextquest"] = 6
    segment = {"phase": "quest-cooldown", "status": "success", "run_id": 12,
               "end_state_json": json.dumps(end)}
    repaired = _repair_completed_quest_wait_from_segments(state, [segment])
    assert repaired["campaign_quest_cooldown_wait"] is None
    assert state["campaign_quest_cooldown_wait"]["remaining"] == 1
    later_wait = {**segment, "run_id": 13, "end_state_json": json.dumps(state)}
    assert _repair_completed_quest_wait_from_segments(state, [segment, later_wait]) == state


@pytest.mark.parametrize("change", [
    {"status": "failed"}, {"run_id": None}, {"phase": "quest-request"},
    {"end_state_json": "invalid"},
])
def test_wait_completion_repair_rejects_failed_or_different_sessions(change):
    end = completed_cycle()
    state = deepcopy(end)
    state.pop("campaign_quest_phases")
    segment = {"phase": "quest-cooldown", "status": "success", "run_id": 12,
               "start_state_json": "{}",
               "end_state_json": json.dumps(end), **change}
    assert _repair_completed_quest_wait_from_segments(state, [segment]) == state


@pytest.mark.parametrize("start_change,accepted", [
    ({}, True), ({"world_boot_id": "other"}, False), ({"level": 28}, False),
    ({"quest_status": {"active": 0, "nextquest": 1}}, False),
    ({"quest_status": {"active": 1, "nextquest": 0}}, False),
    ({"quest_status": {"nextquest": 0}}, False),
    ({"quest_status": {}}, False),
])
def test_direct_request_starts_new_cycle_only_from_observed_availability(start_change, accepted):
    start = checkpoint()
    start["quest_status"]["nextquest"] = 0
    start.update(start_change)
    end = completed_cycle()
    end["campaign_quest_cooldown_wait"] = start["campaign_quest_cooldown_wait"]
    end["campaign_quest_phases"] = end["campaign_quest_phases"][1:]
    merged = _campaign_segment_end_state(start, end, execution="quest-request")
    assert (merged["campaign_quest_cooldown_wait"] is None) is accepted
    segment = {
        "phase": "quest-request", "status": "success", "run_id": 17,
        "start_state_json": json.dumps(start), "end_state_json": json.dumps(end),
    }
    repaired = _repair_completed_quest_wait_from_segments(end, [segment])
    assert (repaired["campaign_quest_cooldown_wait"] is None) is accepted


@pytest.mark.parametrize("active", [0, "0", None, "unknown"])
def test_direct_request_without_positive_assignment_cannot_clear_old_wait(active):
    start = checkpoint()
    start["quest_status"]["nextquest"] = 0
    end = completed_cycle()
    end["campaign_quest_phases"] = end["campaign_quest_phases"][1:]
    end["campaign_quest_phases"][0]["state"]["quest_status"]["active"] = active
    merged = _campaign_segment_end_state(start, end, execution="quest-request")
    assert merged["campaign_quest_cooldown_wait"] is not None


def legacy_reader_stall():
    state = checkpoint()
    state["xp"] = 577856
    state["campaign_quest_cooldown_wait"]["remaining"] = 1
    state["campaign_fastwalk_abort_reason"] = "live quest cooldown did not advance for 180 seconds"
    state["campaign_quest_phases"] = [{
        "phase": "quest-cooldown", "objective_kills": [], "state": deepcopy(state),
    }]
    return state


def test_legacy_sleep_before_read_stall_gets_one_mandatory_quest_recheck():
    state = legacy_reader_stall()
    assert _legacy_quest_reader_recheck_allowed(state)
    assert not _quest_cooldown_wait_has_no_progress(state)
    state["campaign_quest_cooldown_wait"]["reader_revision"] = 2
    assert not _legacy_quest_reader_recheck_allowed(state)
    assert _quest_cooldown_wait_has_no_progress(state)


@pytest.mark.parametrize("change", ["reason", "boot", "xp", "injury", "phase", "kills", "quest", "optional", "missing_hp", "unknown_points"])
def test_legacy_reader_recheck_rejects_changed_or_incomplete_evidence(change):
    state = legacy_reader_stall()
    if change == "reason":
        state["campaign_fastwalk_abort_reason"] = "other failure"
    elif change == "boot":
        state["world_boot_id"] = "other"
    elif change == "xp":
        state["xp"] -= 10
    elif change == "injury":
        state["hp"] = 1
    elif change == "phase":
        state["campaign_quest_phases"][0]["phase"] = "quest-request"
    elif change == "kills":
        state["campaign_quest_phases"][0]["objective_kills"] = [{"xp": 10}]
    elif change == "quest":
        state["quest_status"]["active"] = 1
    elif change == "missing_hp":
        state["campaign_quest_phases"][0]["state"].update(hp=None, max_hp=None)
    elif change == "unknown_points":
        state["quest_status"]["total_points"] = "unknown"
        state["campaign_quest_phases"][0]["state"]["quest_status"]["total_points"] = "unknown"
    else:
        state["quest_status"]["total_points"] = 1
        state["campaign_quest_phases"][0]["state"]["quest_status"]["total_points"] = 1
    assert not _legacy_quest_reader_recheck_allowed(state)
