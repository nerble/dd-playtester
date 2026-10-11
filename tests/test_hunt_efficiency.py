from __future__ import annotations

from copy import deepcopy
import json

import pytest

from dd4tester.hunt_efficiency import observed_hunt_efficiency
from dd4tester.hunt_outcomes import completed_single_target_hunt
from dd4tester.storage import RUN_REPORT_SUMMARY_VERSION


POLICY = "single-target-hunt"
SOURCE = "source-ranked-hunt-example-100-200-31"


def _visit(run_id: int = 1, *, xp: int = 1200, seconds: float = 180.0):
    start = {
        "level": 31, "world_boot_id": "boot", "campaign_source_revision": "old",
        "campaign_xp_loss_total": 100, "room_vnum": "3054", "dead": False,
        "in_combat": False, "hp": 743, "xp": 710000,
    }
    kills = [{"source_mobile_vnum": 100, "source_policy_id": SOURCE, "xp_gained": xp}] if xp else []
    end = {**start, "xp": start["xp"] + xp, "campaign_objective_kills": kills,
           "campaign_fastwalk_source_consider_outcomes": {SOURCE: True} if xp else {}}
    state = {**end, "xp": 714000}
    segment = {
        "id": run_id + 10, "phase": POLICY, "run_id": run_id, "status": "success",
        "command_count": 100, "finished_at": "finished", "start_state_json": json.dumps(start),
        "end_state_json": json.dumps(end),
    }
    summary = {
        "summary_version": RUN_REPORT_SUMMARY_VERSION,
        "run": {"id": run_id, "duration_seconds": seconds},
        "outcomes": {"execution": "success", "objective": "achieved" if xp else "not_achieved", "safety": "safe"},
        "progress": {"experience": {"change": xp}, "confirmed_kills": kills},
    }
    return state, segment, summary


def _rate(state, visits, **kwargs):
    return observed_hunt_efficiency(
        state, visits, policy_id=POLICY, source_policy_id=SOURCE, mobile_vnum=100, **kwargs,
    )


def test_efficiency_includes_zero_progress_visit_cost_and_deduplicates_runs() -> None:
    state, segment, summary = _visit()
    _, empty, empty_summary = _visit(2, xp=0, seconds=60)
    original = deepcopy((state, segment, summary, empty, empty_summary))
    rate = _rate(state, [(segment, summary), (empty, empty_summary), (segment, summary)])
    assert rate is not None
    assert rate.net_xp == 1200
    assert rate.duration_seconds == 240
    assert rate.xp_per_minute == 300
    assert rate.run_ids == (1, 2)
    assert rate.productive_visits == 1
    assert (state, segment, summary, empty, empty_summary) == original


def test_historical_success_needs_an_explicit_current_source_audit() -> None:
    state, segment, summary = _visit()
    state["campaign_source_revision"] = "new"
    assert _rate(state, [(segment, summary)]) is None
    assert _rate(state, [(segment, summary)], audited_source_revision="other") is None
    rate = _rate(state, [(segment, summary)], audited_source_revision="new")
    assert rate is not None and rate.run_ids == (1,)
    state["campaign_source_ranked_xp_loss_policies"] = [{"policy_id": SOURCE, "boot_id": "boot"}]
    assert _rate(state, [(segment, summary)], audited_source_revision="new") is None


def test_efficiency_stops_after_eight_input_visits() -> None:
    state, _, _ = _visit()
    visits = [tuple(_visit(index)[1:]) for index in range(1, 11)]
    rate = _rate(state, visits)
    assert rate is not None and rate.run_ids == tuple(range(1, 9))
    assert rate.net_xp == 9600


@pytest.mark.parametrize("change", [
    "duration_zero", "duration_nan", "duration_boolean", "old_summary", "wrong_run",
    "no_commands", "failed", "loss", "unknown_objective", "below_band", "wrong_mobile",
    "boot", "level", "field", "source_pair", "negative_xp", "empty",
])
def test_efficiency_never_turns_invalid_or_unproductive_evidence_into_a_hunt(change: str) -> None:
    state, segment, summary = _visit()
    end = json.loads(segment["end_state_json"])
    if change.startswith("duration_"):
        summary["run"]["duration_seconds"] = {"duration_zero": 0, "duration_nan": float("nan"), "duration_boolean": True}[change]
    elif change == "old_summary":
        summary["summary_version"] -= 1
    elif change == "wrong_run":
        summary["run"]["id"] += 1
    elif change == "no_commands":
        segment["command_count"] = 0
    elif change in {"failed", "loss", "unknown_objective"}:
        field, value = {"failed": ("execution", "failed"), "loss": ("safety", "loss"), "unknown_objective": ("objective", "unknown")}[change]
        summary["outcomes"][field] = value
    elif change == "below_band":
        summary["progress"]["confirmed_kills"][0]["xp_gained"] = 310
    elif change == "wrong_mobile":
        summary["progress"]["confirmed_kills"][0]["source_mobile_vnum"] += 1
    elif change in {"boot", "level"}:
        state["world_boot_id" if change == "boot" else "level"] = "changed"
    elif change == "field":
        end["room_vnum"] = "200"
    elif change == "source_pair":
        end["campaign_source_revision"] = "other"
    elif change == "negative_xp":
        summary["progress"]["experience"]["change"] = -1
    elif change == "empty":
        state, segment, summary = _visit(xp=0)
        end = json.loads(segment["end_state_json"])
    segment["end_state_json"] = json.dumps(end)
    assert _rate(state, [(segment, summary)]) is None


def test_source_audit_cannot_repair_a_changed_recorded_revision_pair() -> None:
    state, segment, summary = _visit()
    state["campaign_source_revision"] = "new"
    end = json.loads(segment["end_state_json"])
    end["campaign_source_revision"] = "new"
    segment["end_state_json"] = json.dumps(end)
    assert not completed_single_target_hunt(
        state, segment, summary, policy_id=POLICY, source_policy_id=SOURCE,
        mobile_vnum=100, audited_source_revision="new",
    )
