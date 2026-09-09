import json
from copy import deepcopy

import pytest

from dd4tester.campaign import (
    CampaignRunner, _MAINTENANCE_ROUTE_HAZARDS_KEY as HAZARDS,
    _PROVISION_FUNDING_LAST_ATTEMPT_KEY as ATTEMPT,
    _reconcile_maintenance_fastwalk_state,
    _repair_provision_funding_route_hazard_metadata,
    _repair_replayed_funding_route_hazard, load_campaign_spec,
)
from dd4tester.state import CharacterState
from dd4tester.storage import RunStorage
from test_campaign import _record_segment_run, _write_campaign_files


REASON = "field city departure remained blocked by the source greeter/guard interaction after bounded rechecks"
CANDIDATE = "moria.are:4005:4022"


def _evidence():
    start = CharacterState(
        level=8, xp=28365, hp=113, max_hp=113, mana=324, max_mana=324,
        move=220, max_move=220, room_vnum="3054", position=7, enemies=[],
    ).to_dict()
    start.update({
        "world_boot_id": "test-boot", "campaign_fastwalk_abort_reason": REASON,
        "campaign_last_policy": "old-field-hunt",
        "campaign_research_results": {"old-field-hunt": {"route_hazard": REASON}},
        "campaign_xp_loss_total": 68,
    })
    end = deepcopy(start)
    end.update({
        "xp": 28498, ATTEMPT: {
            "candidate_key": CANDIDATE, "boot_id": "test-boot", "completed_kill": True,
        },
    })
    hazard = {
        "boot_id": "test-boot", "route_hazard": REASON,
        "candidate_keys": [CANDIDATE], "retryable_failure": True,
    }
    current = deepcopy(end)
    current[HAZARDS] = {"provision-funding": hazard}
    return start, end, current


def _segment(start, end, **changes):
    return {
        "id": 10, "sequence": 1, "phase": "provision-funding", "status": "success",
        "run_id": 20, "start_state_json": json.dumps(start), "end_state_json": json.dumps(end),
        **changes,
    }


def test_checkpoint_cleanup_cannot_create_a_fresh_route_observation():
    _, clean, _ = _evidence()
    result = _reconcile_maintenance_fastwalk_state(
        clean, clean, execution="provision-funding", policy_id="provision-funding",
        boot_id="test-boot", fresh_observation=False,
    )
    assert result == clean


def test_fresh_same_wording_failure_on_another_candidate_still_records_hazard():
    start, end, _ = _evidence()
    end[ATTEMPT]["completed_kill"] = False
    result = _reconcile_maintenance_fastwalk_state(
        start, end, execution="provision-funding", policy_id="provision-funding",
        boot_id="test-boot",
    )
    assert result[HAZARDS]["provision-funding"]["candidate_keys"] == [CANDIDATE]


def test_repair_removes_only_replayed_candidate_and_keeps_loss_history(monkeypatch):
    start, end, current = _evidence()
    current[HAZARDS]["shop"] = {"route_hazard": "real shop obstruction"}
    current[HAZARDS]["provision-funding"]["candidate_keys"].append("other:1:2")
    original = deepcopy(current)
    monkeypatch.setattr("dd4tester.campaign._runtime_campaign_segments", lambda *a: [_segment(start, end)])
    repaired = _repair_replayed_funding_route_hazard(None, 1, current)
    assert repaired[HAZARDS]["provision-funding"]["candidate_keys"] == ["other:1:2"]
    assert repaired[HAZARDS]["shop"] == current[HAZARDS]["shop"]
    assert repaired["campaign_xp_loss_total"] == 68
    assert repaired["campaign_research_results"] == current["campaign_research_results"]
    assert current == original
    assert _repair_replayed_funding_route_hazard(None, 1, repaired) == repaired


def test_metadata_wrapper_does_not_reinfer_the_cleared_hazard(monkeypatch):
    start, end, current = _evidence()
    monkeypatch.setattr("dd4tester.campaign._runtime_campaign_segments", lambda *a: [_segment(start, end)])
    repaired = _repair_provision_funding_route_hazard_metadata(None, 1, current)
    assert HAZARDS not in repaired
    assert _repair_provision_funding_route_hazard_metadata(None, 1, repaired) == repaired


def test_metadata_inference_cannot_restore_cleared_candidate_beside_other_hazard(monkeypatch):
    start, end, current = _evidence()
    current[HAZARDS]["provision-funding"]["candidate_keys"].append("other:1:2")
    historical = deepcopy(start)
    historical[HAZARDS] = deepcopy(current[HAZARDS])
    historical[ATTEMPT] = {"candidate_key": CANDIDATE, "boot_id": "test-boot", "completed_kill": False}
    segments = [_segment(start, historical, id=9, sequence=0), _segment(start, end)]
    monkeypatch.setattr("dd4tester.campaign._runtime_campaign_segments", lambda *a: segments)
    repaired = _repair_provision_funding_route_hazard_metadata(None, 1, current)
    assert repaired[HAZARDS]["provision-funding"]["candidate_keys"] == ["other:1:2"]
    assert _repair_provision_funding_route_hazard_metadata(None, 1, repaired) == repaired


@pytest.mark.parametrize("boundary", [
    "no_history", "newer_failure", "failed", "no_run", "bad_json", "null_json",
    "new_reason", "new_start_reason", "different_boot", "unknown_boot", "new_level",
    "end_hazard", "start_hazard", "unknown_hazards", "missing_attempt", "incomplete",
    "changed_candidate", "old_attempt", "same_attempt", "different_hazard_candidate",
    "invalid_candidate_keys", "nonretryable", "dead", "zero_hp", "wrong_room",
    "combat", "enemy", "missing_enemies", "wrong_position", "xp_loss", "xp_regressed",
    "unknown_start_xp", "unknown_end_xp",
])
def test_repair_requires_exact_successful_inherited_abort_evidence(monkeypatch, boundary):
    start, end, current = _evidence()
    changes = {}
    if boundary == "failed": changes["status"] = "failed"
    elif boundary == "no_run": changes["run_id"] = None
    elif boundary == "bad_json": changes["end_state_json"] = "{"
    elif boundary == "null_json": changes["end_state_json"] = "null"
    elif boundary == "new_reason": end["campaign_fastwalk_abort_reason"] = "new failure"
    elif boundary == "new_start_reason": start["campaign_fastwalk_abort_reason"] = "different failure"
    elif boundary == "different_boot": end["world_boot_id"] = "new-boot"
    elif boundary == "unknown_boot": current.pop("world_boot_id")
    elif boundary == "new_level": end["level"] = 9
    elif boundary == "end_hazard": end[HAZARDS] = deepcopy(current[HAZARDS])
    elif boundary == "start_hazard": start[HAZARDS] = deepcopy(current[HAZARDS])
    elif boundary == "unknown_hazards": end[HAZARDS] = "unknown"
    elif boundary == "missing_attempt": end.pop(ATTEMPT)
    elif boundary == "incomplete": end[ATTEMPT]["completed_kill"] = False
    elif boundary == "changed_candidate": current[ATTEMPT]["candidate_key"] = "new:1:2"
    elif boundary == "old_attempt": end[ATTEMPT]["boot_id"] = "old-boot"
    elif boundary == "same_attempt": start[ATTEMPT] = deepcopy(end[ATTEMPT])
    elif boundary == "different_hazard_candidate": current[HAZARDS]["provision-funding"]["candidate_keys"] = ["other:1:2"]
    elif boundary == "invalid_candidate_keys": current[HAZARDS]["provision-funding"]["candidate_keys"] = CANDIDATE
    elif boundary == "nonretryable": current[HAZARDS]["provision-funding"]["retryable_failure"] = False
    elif boundary == "dead": end["dead"] = True
    elif boundary == "zero_hp": end["hp"] = 0
    elif boundary == "wrong_room": end["room_vnum"] = "4027"
    elif boundary == "combat": end["in_combat"] = True
    elif boundary == "enemy": end["enemies"] = [{"name": "the orc"}]
    elif boundary == "missing_enemies": end.pop("enemies")
    elif boundary == "wrong_position": end["position"] = 0
    elif boundary == "xp_loss": end["xp_loss_observed"] = True
    elif boundary == "xp_regressed": end["xp"] = start["xp"] - 1
    elif boundary == "unknown_start_xp": start["xp"] = None
    elif boundary == "unknown_end_xp": end["xp"] = None
    segments = [_segment(start, end, **changes)]
    if boundary == "no_history": segments.clear()
    elif boundary == "newer_failure": segments.append(_segment(start, end, id=11, sequence=2, status="failed"))
    monkeypatch.setattr("dd4tester.campaign._runtime_campaign_segments", lambda *a: segments)
    assert _repair_replayed_funding_route_hazard(None, 1, current) == current


@pytest.mark.parametrize("already_replayed", [False, True])
def test_full_startup_preserves_successful_funding_clearance(tmp_path, monkeypatch, already_replayed):
    config, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config)
    start, end, current = _evidence()
    # Isolate unrelated inventory/flight metadata migrations, not this reconciliation.
    monkeypatch.setattr("dd4tester.campaign._repair_noop_liquidation_baseline", lambda storage, cid, state, **kw: state)
    runner = CampaignRunner(spec, config)
    with RunStorage(database) as storage:
        cid = storage.create_campaign(
            name=spec.name, config_path=config.resolve(), character_profile_path=spec.character_profile,
            target_level=spec.target_level,
        )
        segment = storage.start_campaign_segment(cid, phase="provision-funding", start_state=start)
        run = _record_segment_run(database, spec.character_profile, end)
        storage.finish_campaign_segment(
            segment, status="success", run_id=run.run_id, end_state=end,
            command_count=30, duration_seconds=121, error=None,
        )
        storage.record_campaign_checkpoint(
            cid, segment_id=segment, run_id=run.run_id, phase="provision-funding",
            reason="campaign_metadata_repaired" if already_replayed else "segment_complete",
            state=current if already_replayed else end,
        )
        _, repaired = runner._open_campaign(storage)
        assert not repaired.get(HAZARDS, {}).get("provision-funding")
        assert repaired["campaign_xp_loss_total"] == 68
        _, reopened = runner._open_campaign(storage)
        assert not reopened.get(HAZARDS, {}).get("provision-funding")
