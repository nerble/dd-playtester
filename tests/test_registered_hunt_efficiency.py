from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from dd4tester import campaign
from dd4tester.character import CharacterSpec
from dd4tester.hunt_candidates import HuntCandidate, WorldSource
from dd4tester.storage import RUN_REPORT_SUMMARY_VERSION


def _receipt(policy_id: str, source_id: str, vnum: int, run_id: int, duration: float, xp: int):
    start = {
        "level": 31, "world_boot_id": "boot", "campaign_source_revision": "old",
        "campaign_xp_loss_total": 100, "room_vnum": "3054", "dead": False,
        "in_combat": False, "enemies": [], "hp": 743, "xp": 710000,
    }
    kill = {"source_mobile_vnum": vnum, "source_policy_id": source_id, "xp_gained": xp}
    end = {**start, "xp": 710000 + xp, "campaign_objective_kills": [kill],
           "campaign_fastwalk_source_consider_outcomes": {source_id: True}}
    segment = {
        "id": run_id + 10, "phase": policy_id, "run_id": run_id, "status": "success",
        "command_count": 100, "finished_at": "finished", "start_state_json": json.dumps(start),
        "end_state_json": json.dumps(end),
    }
    summary = {
        "summary_version": RUN_REPORT_SUMMARY_VERSION, "run": {"id": run_id, "duration_seconds": duration},
        "outcomes": {"execution": "success", "objective": "achieved", "safety": "safe"},
        "progress": {"experience": {"change": xp}, "confirmed_kills": [kill]},
    }
    return segment, summary


def _setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, generic_duration: float | None = 240):
    policy = campaign._VAMPIRE_CATACOMBS_DYING_MAN_LEVEL_25_32_POLICY
    candidate = HuntCandidate(
        status="productive", score=100, area_file="example.are", mobile_vnum=100,
        target="target", target_keyword="target", level=30, room_vnum=200, room_name="room",
        route=(), source_spawn_limit=1, room_spawn_count=1, boot_kills=1,
        loot=(), source_value=0, contained_coins=0, hazards=(),
    )
    source_id = campaign._source_ranked_policy_id(candidate, character_level=31)
    registered, registered_summary = _receipt(
        policy.policy_id, "source-ranked-hunt-vamp-catacombs-9500-9501-31", 9500, 1, 180, 1800,
    )
    records = [registered]
    summaries = {1: registered_summary}
    if generic_duration is not None:
        generic, generic_summary = _receipt(source_id, source_id, 100, 2, generic_duration, 1200)
        records.append(generic)
        summaries[2] = generic_summary
    character = CharacterSpec("Testpilot", "TEST_PASSWORD", "dwarf", "male", "warrior")
    runner = campaign.CampaignRunner(campaign.CampaignSpec("test", tmp_path / "character.yaml", character), tmp_path / "campaign.yaml")
    runner._source_world = WorldSource()
    runner._campaign_policy_campaign_id = 1
    runner._campaign_policy_segments = records
    runner._campaign_policy_storage = SimpleNamespace(
        get_latest_campaign_segment_for_phase=lambda _cid, phase, **_kw: next(
            (row for row in reversed(records) if row["phase"] == phase), None,
        ),
        get_run_summary=lambda rid: summaries.get(rid),
    )
    monkeypatch.setattr(campaign, "_vampire_catacombs_hunt_source_available", lambda *_a, **_kw: True)
    state = json.loads(registered["end_state_json"])
    state.update(xp=714000, campaign_source_revision="new")
    return runner, state, candidate, registered, summaries


def _waiter_receipt(policy_id: str, run_id: int, *, productive: bool = True):
    source_id = "source-ranked-hunt-mirror-realm-19027-19072-39"
    start = {
        "level": 39, "world_boot_id": "boot", "campaign_source_revision": "revision",
        "campaign_xp_loss_total": 0, "room_vnum": "3054", "dead": False,
        "in_combat": False, "enemies": [], "hp": 936, "xp": 1299757,
    }
    xp = 2995 if productive else 0
    kill = {"source_mobile_vnum": 19027, "source_policy_id": source_id, "xp_gained": xp}
    end = {
        **start, "xp": start["xp"] + xp,
        "campaign_objective_kills": [kill] if productive else [],
        "campaign_fastwalk_source_consider_outcomes": {source_id: True} if productive else {},
    }
    segment = {
        "id": run_id + 100, "phase": policy_id, "run_id": run_id,
        "status": "success", "command_count": 100, "finished_at": "finished",
        "start_state_json": json.dumps(start), "end_state_json": json.dumps(end),
    }
    summary = {
        "summary_version": RUN_REPORT_SUMMARY_VERSION,
        "run": {"id": run_id, "duration_seconds": 132.811 if productive else 120.0},
        "outcomes": {
            "execution": "success", "objective": "achieved" if productive else "not_achieved",
            "safety": "safe",
        },
        "progress": {
            "experience": {"change": xp},
            "confirmed_kills": [kill] if productive else [],
        },
    }
    return segment, summary


def _waiter_setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, source_available: bool = True):
    policy = campaign._MIRROR_REALM_WAITER_HUNT_POLICY
    policy_id = f"{policy.policy_id}-level-39"
    segment, summary = _waiter_receipt(policy_id, 10)
    records = [segment]
    summaries = {10: summary}
    character = CharacterSpec("Testpilot", "TEST_PASSWORD", "dwarf", "male", "warrior")
    runner = campaign.CampaignRunner(
        campaign.CampaignSpec("test", tmp_path / "character.yaml", character),
        tmp_path / "campaign.yaml",
    )
    runner._source_world = WorldSource()
    runner._campaign_policy_campaign_id = 7
    runner._campaign_policy_segments = records
    runner._campaign_policy_storage = SimpleNamespace(
        get_latest_campaign_segment_for_phase=lambda _cid, phase, **_kw: next(
            (row for row in reversed(records) if row["phase"] == phase), None,
        ),
        get_run_summary=lambda rid: summaries.get(rid),
    )
    monkeypatch.setattr(
        campaign, "_mirror_realm_plain_hunt_source_available",
        lambda *_a, **_kw: source_available,
    )
    end = json.loads(segment["end_state_json"])
    state = {
        **end, "level": 39, "world_boot_id": "boot", "campaign_source_revision": "revision",
        "campaign_xp_loss_total": 0, "max_hp": 936,
        "campaign_registered_research_xp_loss_policies": [],
        "campaign_source_ranked_xp_loss_policies": [],
    }
    return runner, state, policy_id, records, summaries


@pytest.mark.parametrize(("generic_duration", "registered_selected"), [(60, False), (120, False), (240, True), (None, True)])
def test_current_source_audited_registered_hunt_competes_by_observed_visit_rate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    generic_duration: float | None, registered_selected: bool,
) -> None:
    runner, state, candidate, _, _ = _setup(tmp_path, monkeypatch, generic_duration=generic_duration)
    original = deepcopy(state)
    selected = runner._productive_registered_hunt_policy(state, candidate)
    if registered_selected:
        assert selected == campaign._VAMPIRE_CATACOMBS_DYING_MAN_LEVEL_25_32_POLICY
        audit = state["campaign_hunt_efficiency_selection"]
        assert audit["historical_run_ids"] == [1]
        assert audit["source_revision"] == "new"
        assert audit["xp_per_minute"] == 600
        assert audit["generic_xp_per_minute"] == (300 if generic_duration else None)
    else:
        assert selected is None
        assert state == original


@pytest.mark.parametrize("change", ["source_unavailable", "latest_failed", "lost", "source_loss", "no_summary", "old_summary", "bad_timing", "boot", "level"])
def test_selection_keeps_failed_targets_and_unproved_history_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str,
) -> None:
    runner, state, candidate, registered, summaries = _setup(tmp_path, monkeypatch)
    if change == "source_unavailable":
        monkeypatch.setattr(campaign, "_vampire_catacombs_hunt_source_available", lambda *_a, **_kw: False)
    elif change == "latest_failed":
        failed = deepcopy(registered)
        failed.update(id=99, run_id=99, status="failed")
        runner._campaign_policy_segments.append(failed)
        summaries[99] = deepcopy(summaries[1])
        summaries[99]["run"]["id"] = 99
    elif change in {"lost", "source_loss"}:
        key = "campaign_registered_research_xp_loss_policies" if change == "lost" else "campaign_source_ranked_xp_loss_policies"
        state[key] = [{"boot_id": "boot", "policy_id": registered["phase"] if change == "lost" else "source-ranked-hunt-vamp-catacombs-9500-9501-31"}]
    elif change == "no_summary":
        summaries.pop(1)
    elif change == "old_summary":
        summaries[1]["summary_version"] -= 1
    elif change == "bad_timing":
        summaries[1]["run"]["duration_seconds"] = float("nan")
    elif change in {"boot", "level"}:
        state["world_boot_id" if change == "boot" else "level"] = "changed" if change == "boot" else 33
    assert runner._productive_registered_hunt_policy(state, candidate) is None


def test_single_target_rate_does_not_replace_a_selected_multi_kill_circuit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner, state, candidate, _, _ = _setup(tmp_path, monkeypatch, generic_duration=None)
    runner._selected_source_ranked_circuit = (candidate,)
    original = deepcopy(state)

    assert runner._productive_registered_hunt_policy(state, candidate) is None
    assert runner._selected_source_ranked_circuit == (candidate,)
    assert state == original


@pytest.mark.parametrize("generic_duration,measured_wins", [(240, True), (60, False)])
def test_source_rate_comparison_commits_only_the_winning_candidate_state(tmp_path, monkeypatch, generic_duration, measured_wins):
    from dataclasses import replace

    runner, state, candidate, _, summaries = _setup(tmp_path, monkeypatch, generic_duration=generic_duration)
    measured = replace(candidate, mobile_vnum=101, room_vnum=201)
    measured_id = campaign._source_ranked_policy_id(measured, character_level=31)
    segment, summary = _receipt(measured_id, measured_id, 101, 3, 180, 2700)
    runner._campaign_policy_segments.append(segment)
    summaries[3] = summary
    state[campaign._PRODUCTIVE_POLICY_HISTORY_KEY] = {"boot_id": "boot", "policy_ids": [measured_id]}
    state["campaign_research_results"] = {measured_id: {
        "boot_id": "boot", "observed": True, "viable": True, "completed_kill": True,
    }}
    original = deepcopy(state)
    previous_candidate = runner._selected_source_ranked_candidate

    def select(projection, **kwargs):
        assert projection is not state
        assert kwargs["required_policy_id"] == measured_id
        projection["winner_only"] = True
        runner._selected_source_ranked_candidate = measured
        runner._source_ranked_protection_retry_selected_policy_id = measured_id
        return measured

    monkeypatch.setattr(runner, "_select_source_ranked_candidate", select)
    result = runner._productive_registered_hunt_policy(state, candidate)
    if measured_wins:
        assert result.policy_id == measured_id
        assert state["winner_only"] is True
        assert state[campaign._SOURCE_RANKED_CANDIDATE_KEY]["mobile_vnum"] == 101
        assert runner._selected_source_ranked_candidate is measured
    else:
        assert result is None
        assert state == original
        assert runner._selected_source_ranked_candidate is previous_candidate
        assert runner._source_ranked_protection_retry_selected_policy_id is None


def test_productive_mirror_waiter_competes_at_its_current_level(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner, state, policy_id, _, _ = _waiter_setup(tmp_path, monkeypatch)

    selected = runner._productive_registered_hunt_policy(state, None)

    assert selected is not None
    assert selected.policy_id == policy_id
    assert selected.minimum_level == selected.maximum_level == 39
    audit = state["campaign_hunt_efficiency_selection"]
    assert audit["historical_run_ids"] == [10]
    assert audit["xp_per_minute"] == pytest.approx(2995 * 60 / 132.811)


def test_waiter_rate_charges_safe_zero_xp_visits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner, state, policy_id, records, summaries = _waiter_setup(tmp_path, monkeypatch)
    zero_segment, zero_summary = _waiter_receipt(policy_id, 11, productive=False)
    start = json.loads(zero_segment["start_state_json"])
    start["xp"] = 1302752
    end = json.loads(zero_segment["end_state_json"])
    end["xp"] = 1302752
    zero_segment["start_state_json"] = json.dumps(start)
    zero_segment["end_state_json"] = json.dumps(end)
    records.insert(0, zero_segment)
    summaries[11] = zero_summary
    runner._campaign_policy_storage.get_latest_campaign_segment_for_phase = (
        lambda _cid, phase, **_kw: next(
            (row for row in reversed(records) if row["phase"] == phase), None,
        )
    )

    selected = runner._productive_registered_hunt_policy(state, None)

    assert selected is not None
    audit = state["campaign_hunt_efficiency_selection"]
    assert audit["historical_run_ids"] == [10, 11]
    assert audit["xp_per_minute"] == pytest.approx(2995 * 60 / (132.811 + 120.0))


@pytest.mark.parametrize("change", ["source_unavailable", "exact_loss"])
def test_waiter_repeat_stays_closed_without_fresh_source_and_loss_clearance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str,
) -> None:
    runner, state, _, _, _ = _waiter_setup(
        tmp_path, monkeypatch, source_available=change != "source_unavailable",
    )
    if change == "exact_loss":
        state["campaign_source_ranked_xp_loss_policies"] = [{
            "boot_id": "boot",
            "policy_id": "source-ranked-hunt-mirror-realm-19027-19072-39",
        }]

    assert runner._productive_registered_hunt_policy(state, None) is None
