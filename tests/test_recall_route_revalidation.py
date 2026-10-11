import copy
import json

import pytest

from dd4tester.campaign import (
    _source_ranked_policy_id, _source_ranked_productive_repeatability_allowed,
    _source_ranked_result_status,
)
from dd4tester.hunt_candidates import (
    ROOM_NO_RECALL, ExitSource, HuntCandidate, RoomSource, WorldSource,
)
from dd4tester.recall_recovery import (
    RECALL_ROUTE_REVALIDATION_KEY, recall_route_revalidation_pending,
    repaired_recall_route_evidence,
)


@pytest.fixture
def receipt_case(tmp_path):
    (tmp_path / "test.are").write_text("#RECALL 3001\n", encoding="utf-8")
    world = WorldSource(rooms={
        100: RoomSource(100, "hall", "test.are", room_flags=ROOM_NO_RECALL,
                        exits={"north": ExitSource("north", 101, 0, -1)}),
        101: RoomSource(101, "hall", "test.are"),
    })
    candidate = HuntCandidate(
        status="research", score=1, area_file="test.are", mobile_vnum=200,
        target="a clan member", target_keyword="clan", level=30,
        room_vnum=102, room_name="camp", route=("north",),
        source_spawn_limit=2, room_spawn_count=1, boot_kills=1,
        loot=(), source_value=0, contained_coins=0, hazards=(),
    )
    policy = _source_ranked_policy_id(candidate, character_level=30)
    base = {
        "level": 30, "world_boot_id": "boot", "campaign_source_revision": "source",
        "dead": False, "in_combat": False, "room_vnum": "3054",
        "xp": 10000, "campaign_xp_loss_total": 10, "hp": 700, "max_hp": 700,
    }
    start = {**base, "campaign_source_ranked_hunt_candidate": {
        "policy_id": policy, "mobile_vnum": 200, "room_vnum": 102,
        "source_revision": "source", "route": ["north"],
    }}
    end = {**base, "room_vnum": "100", "xp": 11500}
    recovered = {**base, "xp": 11500, "campaign_adjacent_recall_escape": {
        "origin": "100", "direction": "north", "destination": "101",
        "stage": "complete", "commands_sent": 3, "failure": None,
        "scan_response": "A clan member who is three rooms to the north.\n"
                         "<700/700 hits 100/100 mana 100/100 move [Test]> ",
    }}
    error = "recall-only fastwalk did not reach the Midgaard healer route from room 'hall' (100)"
    failed = {
        "id": 1, "campaign_id": 7, "sequence": 10, "run_id": 20, "phase": policy,
        "execution_status": "failed", "safety_outcome": "safe", "command_count": 20,
        "error": error, "start_state_json": json.dumps(start), "end_state_json": json.dumps(end),
    }
    recovery = {
        "id": 2, "campaign_id": 7, "sequence": 11, "run_id": 21, "phase": "return-home",
        "status": "success", "execution_status": "success", "safety_outcome": "safe",
        "start_state_json": json.dumps(end), "end_state_json": json.dumps(recovered),
    }
    kills = [{
        "run_id": 20, "boot_id": "boot", "source_policy_id": policy,
        "source_mobile_vnum": 200, "objective_eligible": 1,
        "below_useful_band": 0, "route_gate": 0, "xp_gained": 1500,
    }]
    terminal = {
        "state": "failed", "error": error, "fastwalk_abort_reason": None,
        "fastwalk_source_consider_outcomes": {policy: True},
    }
    return failed, recovery, kills, recovered, candidate, world, tmp_path, terminal


def receipt(case):
    failed, recovery, kills, current, candidate, world, directory, terminal = case
    return repaired_recall_route_evidence(
        failed, recovery, kills, current, candidate, world, directory,
        terminal_evidence=terminal,
    )


def test_recall_route_receipt_preserves_failed_outcome_and_later_losses(receipt_case):
    case = receipt_case
    original = copy.deepcopy(case[0])
    case[3].update(xp=13000, campaign_xp_loss_total=50)
    marker = receipt(case)
    assert marker["status"] == "pending"
    assert marker["objective_xp"] == 1500
    assert marker["failed_run_id"] == 20 and marker["recovery_run_id"] == 21
    assert case[0] == original
    state = {**case[3], RECALL_ROUTE_REVALIDATION_KEY: marker}
    assert recall_route_revalidation_pending(state, case[4], case[0]["phase"])
    assert _source_ranked_result_status(case[4], state, character_level=30) == "productive"
    assert _source_ranked_productive_repeatability_allowed(case[4], state, character_level=30)
    assert "campaign_research_results" not in state
    marker["status"] = "attempted"
    assert not recall_route_revalidation_pending(state, case[4], case[0]["phase"])
    assert _source_ranked_result_status(case[4], state, character_level=30) == "fresh"
    assert not _source_ranked_productive_repeatability_allowed(case[4], state, character_level=30)


@pytest.mark.parametrize("change", [
    "loss", "death", "boot", "source", "level", "sequence", "campaign", "run",
    "error", "consider", "crowd", "abort", "route", "mobile", "reset", "recovery",
    "escape", "adjacent", "scan_prompt", "kill_run", "below_band", "incidental",
    "low_xp", "current_loss", "low_health",
])
def test_recall_route_receipt_rejects_incomplete_or_conflicting_evidence(receipt_case, change):
    failed, recovery, kills, current, candidate, world, directory, terminal = receipt_case
    start = json.loads(failed["start_state_json"])
    end = json.loads(failed["end_state_json"])
    recovered = json.loads(recovery["end_state_json"])
    if change == "loss":
        end["campaign_xp_loss_total"] += 1
    elif change == "death":
        end["dead"] = True
    elif change in {"boot", "source", "level"}:
        key = {"boot": "world_boot_id", "source": "campaign_source_revision", "level": "level"}[change]
        current[key] = 31 if change == "level" else "changed"
    elif change == "sequence":
        recovery["sequence"] += 1
    elif change == "campaign":
        recovery["campaign_id"] += 1
    elif change == "run":
        failed["run_id"] = None
    elif change == "error":
        failed["error"] = "combat output timeout"
    elif change == "consider":
        terminal["fastwalk_source_consider_outcomes"] = {}
    elif change == "crowd":
        terminal["fastwalk_crowded"] = True
    elif change == "abort":
        terminal["fastwalk_abort_reason"] = "health floor"
    elif change in {"route", "mobile", "reset"}:
        key = {"route": "route", "mobile": "mobile_vnum", "reset": "room_vnum"}[change]
        start["campaign_source_ranked_hunt_candidate"][key] = ["south"] if change == "route" else 999
    elif change == "recovery":
        recovery["execution_status"] = "failed"
    elif change == "escape":
        recovered["campaign_adjacent_recall_escape"]["stage"] = "stepping"
    elif change == "adjacent":
        recovered["campaign_adjacent_recall_escape"]["scan_response"] = (
            "A demon who is one room to the north.\n<700/700 hits 100/100 mana 100/100 move [Test]> "
        )
    elif change == "scan_prompt":
        recovered["campaign_adjacent_recall_escape"]["scan_response"] = "You can't see anything to the north."
    elif change == "kill_run":
        kills[0]["run_id"] += 1
    elif change == "below_band":
        kills[0]["below_useful_band"] = 1
    elif change == "incidental":
        kills[0]["objective_eligible"] = 0
    elif change == "low_xp":
        kills[0]["xp_gained"] = 300
    elif change == "current_loss":
        current["campaign_xp_loss_total"] = 0
    elif change == "low_health":
        current["hp"] = 100
    failed["start_state_json"], failed["end_state_json"] = json.dumps(start), json.dumps(end)
    recovery["end_state_json"] = json.dumps(recovered)
    assert receipt(receipt_case) is None


def test_recall_route_receipt_never_overrides_saved_crowd_cooldown(receipt_case):
    marker = receipt(receipt_case)
    state = {**receipt_case[3], RECALL_ROUTE_REVALIDATION_KEY: marker,
             "campaign_research_crowd_cooldowns": {marker["policy_id"]: 2}}
    assert _source_ranked_result_status(receipt_case[4], state, character_level=30) == "cooldown"
