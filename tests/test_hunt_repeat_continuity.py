from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from dd4tester import campaign
from dd4tester.character import CharacterSpec
from dd4tester.hunt_candidates import WorldSource
from dd4tester.hunt_outcomes import completed_single_target_hunt
from dd4tester.storage import RUN_REPORT_SUMMARY_VERSION


POLICY = "independent-hunt"
SOURCE = "source-ranked-hunt-example-9500-9501-31"
PRIOR_SOURCE = "source-ranked-hunt-example-9500-9501-30"


def _evidence(*, transition: bool = True, area: str = "example", policy_id: str = POLICY):
    start = {
        "level": 30 if transition else 31, "world_boot_id": "boot",
        "campaign_source_revision": "revision", "campaign_xp_loss_total": 500,
        "room_vnum": "3054", "dead": False, "in_combat": False,
        "enemies": [], "hp": 727, "xp": 668886,
    }
    source_id = f"source-ranked-hunt-{area}-9500-9501-{start['level']}"
    kill = {"source_mobile_vnum": 9500, "source_policy_id": source_id, "xp_gained": 1858}
    end = {
        **start, "level": 31, "hp": 743, "xp": 670744,
        "campaign_objective_kills": [kill],
        "campaign_fastwalk_source_consider_outcomes": {source_id: True},
    }
    segment = {
        "phase": policy_id, "status": "success", "finished_at": "finished",
        "run_id": 79, "command_count": 168, "start_state_json": json.dumps(start),
        "end_state_json": json.dumps(end),
    }
    summary = {
        "summary_version": RUN_REPORT_SUMMARY_VERSION, "run": {"id": 79},
        "outcomes": {"execution": "success", "objective": "achieved", "safety": "safe"},
        "progress": {
            "confirmed_kills": [kill], "level_gains_observed": int(transition),
            "level": {"initial": start["level"], "final": 31, "change": int(transition)},
        },
    }
    state = deepcopy(end)
    state.update(xp=710210, campaign_xp_loss_total=3460)
    state["campaign_registered_research_xp_loss_policies"] = [{
        "policy_id": "other-hunt", "boot_id": "boot", "loss_count": 1,
    }]
    return state, segment, summary


@pytest.mark.parametrize("transition", [False, True])
def test_completed_hunt_retains_own_success_after_unrelated_losses(transition: bool) -> None:
    evidence = _evidence(transition=transition)
    original = deepcopy(evidence)
    assert completed_single_target_hunt(
        *evidence, policy_id=POLICY, source_policy_id=SOURCE, mobile_vnum=9500,
        prior_level_source_policy_id=PRIOR_SOURCE,
    )
    assert evidence == original


@pytest.mark.parametrize("transition", [False, True])
def test_prior_level_target_loss_stays_closed_after_a_successful_visit(transition: bool) -> None:
    state, segment, summary = _evidence(transition=transition)
    state["campaign_source_ranked_xp_loss_policies"] = [{
        "policy_id": PRIOR_SOURCE, "boot_id": "boot", "loss_count": 1,
    }]
    assert not completed_single_target_hunt(
        state, segment, summary, policy_id=POLICY, source_policy_id=SOURCE,
        mobile_vnum=9500, prior_level_source_policy_id=PRIOR_SOURCE,
    )


@pytest.mark.parametrize("change", [
    "no_transition_opt_in", "wrong_prior_id", "missing_level_receipt", "wrong_level_receipt",
    "missing_observed_gain", "boolean_gain", "boolean_level_receipt", "two_levels", "later_level", "lost_level",
    "source_change", "boot_change", "own_visit_loss", "loss_total_rewind", "registered_loss",
    "current_source_loss", "prior_source_loss", "wrong_run", "unknown_objective", "field_end",
    "crowd", "below_band", "failed_segment", "failed_summary", "malformed_loss_ledger",
])
def test_hunt_continuity_rejects_unproved_transitions_and_target_failures(change: str) -> None:
    state, segment, summary = _evidence()
    start = json.loads(segment["start_state_json"])
    end = json.loads(segment["end_state_json"])
    prior_id = PRIOR_SOURCE
    if change == "no_transition_opt_in":
        prior_id = None
    elif change == "wrong_prior_id":
        prior_id = "other-source"
    elif change == "missing_level_receipt":
        summary["progress"].pop("level")
    elif change == "wrong_level_receipt":
        summary["progress"]["level"]["change"] = 0
    elif change == "boolean_level_receipt":
        summary["progress"]["level"]["change"] = True
    elif change in {"missing_observed_gain", "boolean_gain"}:
        summary["progress"]["level_gains_observed"] = None if change == "missing_observed_gain" else True
    elif change == "two_levels":
        start["level"] = 29
    elif change in {"later_level", "lost_level"}:
        state["level"] = 32 if change == "later_level" else 30
    elif change in {"source_change", "boot_change"}:
        state["campaign_source_revision" if change == "source_change" else "world_boot_id"] = "changed"
    elif change == "own_visit_loss":
        end["campaign_xp_loss_total"] += 1
    elif change == "loss_total_rewind":
        state["campaign_xp_loss_total"] = 499
    elif change in {"registered_loss", "current_source_loss", "prior_source_loss"}:
        registered = change == "registered_loss"
        key = "campaign_registered_research_xp_loss_policies" if registered else "campaign_source_ranked_xp_loss_policies"
        state[key] = [{
            "boot_id": "boot", "policy_id": POLICY if registered else (
                SOURCE if change == "current_source_loss" else PRIOR_SOURCE
            ), "loss_count": 1,
        }]
    elif change == "wrong_run":
        summary["run"]["id"] += 1
    elif change == "unknown_objective":
        summary["outcomes"]["objective"] = "unknown"
    elif change == "field_end":
        end["room_vnum"] = "9501"
    elif change == "crowd":
        end["campaign_fastwalk_crowded"] = True
    elif change == "below_band":
        summary["progress"]["confirmed_kills"][0]["xp_gained"] = 310
    elif change == "failed_segment":
        segment["status"] = "failed"
    elif change == "failed_summary":
        summary["outcomes"]["execution"] = "failed"
    elif change == "malformed_loss_ledger":
        state["campaign_source_ranked_xp_loss_policies"] = {"unparsed": True}
    segment.update(start_state_json=json.dumps(start), end_state_json=json.dumps(end))
    assert not completed_single_target_hunt(
        state, segment, summary, policy_id=POLICY, source_policy_id=SOURCE,
        mobile_vnum=9500, prior_level_source_policy_id=prior_id,
    )


@pytest.mark.parametrize("kill_count", [2, 3, 20])
@pytest.mark.parametrize("transition", [False, True])
def test_campaign_repeats_exact_productive_independent_hunt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kill_count: int, transition: bool,
) -> None:
    policy = campaign._VAMPIRE_CATACOMBS_DYING_MAN_LEVEL_25_32_POLICY
    state, segment, summary = _evidence(
        transition=transition, area="vamp-catacombs", policy_id=policy.policy_id,
    )
    state["campaign_registered_research_xp_loss_policies"].append({
        "policy_id": "vampire-catacombs-hunt-25-32", "boot_id": "boot", "loss_count": 1,
    })
    character = CharacterSpec("Testpilot", "TEST_PASSWORD", "dwarf", "male", "warrior")
    spec = campaign.CampaignSpec("test", tmp_path / "character.yaml", character)
    runner = campaign.CampaignRunner(spec, tmp_path / "campaign.yaml")
    runner._source_world = WorldSource()
    runner._boot_source_kill_counts[9500] = kill_count
    runner._campaign_policy_campaign_id = 1
    runner._campaign_policy_storage = SimpleNamespace(
        get_latest_campaign_segment_for_phase=lambda _cid, phase, **_kw: (
            segment if phase == policy.policy_id else None
        ),
        get_run_summary=lambda _rid: summary,
    )
    monkeypatch.setattr(campaign, "_source_mobile_candidate", lambda *_a, **_kw: object())
    monkeypatch.setattr(campaign, "_source_ranked_candidate_excluded_by_below_band_evidence", lambda *_a, **_kw: False)
    monkeypatch.setattr(campaign, "_vampire_catacombs_hunt_source_available", lambda *_a, **_kw: True)
    original = deepcopy(state)
    assert runner._catacombs_fallback_policy(state) == policy
    assert state == original
    summary["outcomes"]["objective"] = "not_achieved"
    assert runner._catacombs_fallback_policy(state) is None
