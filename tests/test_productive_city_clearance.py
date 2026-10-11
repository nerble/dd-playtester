import json
from dataclasses import replace

import pytest

from dd4tester.campaign_migrations import productive_city_clearance_proof
from dd4tester.campaign import (
    _FIELD_CITY_CLEAR_ROUTE_REVALIDATION_KEY,
    _field_city_alternate_route_revalidation_record,
    _mark_field_city_alternate_route_revalidation,
)
from dd4tester.city_travel import PRODUCTIVE_CITY_CLEARANCE_KEY
from dd4tester.hunt_candidates import HuntCandidate


def clearance_fixture():
    candidate = HuntCandidate(
        "reject", 1, "city.are", 101, "a citizen", "citizen", 30, 301, "street",
        ("north",), 4, 1, 0, (), 0, 0, (),
    )
    policy = "source-ranked-hunt-city-101-301-30"
    result = {"boot_id": "boot", "previously_productive": True,
              "consider_viable": True, "retryable_failure": True}
    state = {
        "level": 30, "world_boot_id": "boot", "campaign_source_revision": "revision",
        "xp": 1200, "campaign_xp_loss_total": 5, "room_vnum": "3054",
        "dead": False, "in_combat": False, "enemies": [],
        "campaign_research_results": {policy: result},
    }
    kill = {"source_policy_id": policy, "source_mobile_vnum": 101, "xp_gained": 400}
    start = state | {"xp": 800, "campaign_source_ranked_hunt_candidate": {
        "policy_id": policy, "mobile_vnum": 101, "room_vnum": 301, "route": ["north"],
    }}
    end = state | {"campaign_objective_kills": [kill]}
    segment = {"id": 2, "run_id": 3, "phase": policy, "status": "success",
               "finished_at": "finished", "error": None,
               "start_state_json": json.dumps(start), "end_state_json": json.dumps(end)}
    summary = {"summary_version": 6, "run": {"id": 3}, "outcomes": {
        "execution": "success", "objective": "not_achieved", "safety": "safe",
    }, "progress": {"confirmed_kills": [kill], "experience": {"initial": 800, "final": 1200}}}
    return state, candidate, policy, [segment], summary


def test_productive_clearance_uses_exact_kill_without_claiming_objective_completion():
    state, candidate, policy, segments, summary = clearance_fixture()
    proof = productive_city_clearance_proof(
        state, candidate, policy_id=policy, segments=segments, summary_loader=lambda _: summary,
    )
    assert proof["productive_run_id"] == 3
    assert proof["prior_result"] == state["campaign_research_results"][policy]
    assert summary["outcomes"]["objective"] == "not_achieved"


@pytest.mark.parametrize("change", [
    "spent", "loss", "xp", "revision", "route", "below_band", "incidental",
    "missing_summary", "unsafe", "wrong_run", "crowd", "identity", "unverified_kill", "old_summary",
])
def test_productive_clearance_rejects_changed_missing_or_unsafe_evidence(change):
    state, candidate, policy, segments, summary = clearance_fixture()
    if change == "spent":
        state[PRODUCTIVE_CITY_CLEARANCE_KEY] = {
            "level": 30, "boot_id": "boot", "policies": {policy: {"status": "attempted"}},
        }
    elif change == "loss":
        state["campaign_xp_loss_total"] += 1
    elif change == "xp":
        state["xp"] += 1
    elif change == "revision":
        state["campaign_source_revision"] = "new"
    elif change == "route":
        candidate = replace(candidate, route=("south",))
    elif change == "below_band":
        summary["progress"]["confirmed_kills"][0]["xp_gained"] = 300
    elif change == "incidental":
        summary["progress"]["confirmed_kills"][0]["source_policy_id"] = "resource-carrier"
    elif change == "missing_summary":
        summary = None
    elif change == "unsafe":
        summary["outcomes"]["safety"] = "unsafe"
    elif change == "wrong_run":
        summary["run"]["id"] = 4
    elif change == "crowd":
        state["campaign_research_results"][policy]["crowded"] = True
    elif change == "identity":
        state["campaign_research_results"][policy]["target_vnum_mismatch"] = True
    elif change == "unverified_kill":
        summary["progress"]["confirmed_kills"] = []
    elif change == "old_summary":
        summary["summary_version"] = 5
    assert productive_city_clearance_proof(
        state, candidate, policy_id=policy, segments=segments, summary_loader=lambda _: summary,
    ) is None


def test_productive_clearance_never_expands_the_eight_segment_tail():
    state, candidate, policy, segments, summary = clearance_fixture()
    segments += [segments[0] | {"phase": "maintenance"}] * 8
    assert productive_city_clearance_proof(
        state, candidate, policy_id=policy, segments=segments, summary_loader=lambda _: summary,
    ) is None


def pending_clearance_fixture():
    state, candidate, policy, segments, summary = clearance_fixture()
    proof = productive_city_clearance_proof(
        state, candidate, policy_id=policy, segments=segments, summary_loader=lambda _: summary,
    )
    state[PRODUCTIVE_CITY_CLEARANCE_KEY] = {
        "boot_id": "boot", "level": 30, "policies": {
            policy: {**proof, "blocked_run_id": 4, "observation_run_id": 5, "status": "pending"},
        },
    }
    state[_FIELD_CITY_CLEAR_ROUTE_REVALIDATION_KEY] = {
        "boot_id": "boot", "level": 30, "source_revision": "revision",
        "policy_id": policy, "source_mobile_vnum": 101, "source_room_vnum": 301,
        "prior_segment_id": 4, "prior_run_id": 4, "observation_run_id": 5,
        "observation_source_revision": "revision", "source_route": ["north"],
        "max_extra_steps": 22, "blocked_room_vnums": [302],
        "route_clear_recheck": True, "status": "pending", "attempted": False,
        "productive_clearance": proof, "superseded_clearance": {"policy_id": "old", "status": "attempted"},
    }
    return state, candidate, policy


@pytest.mark.parametrize("change", ["xp", "loss", "result", "ledger", "spent", "observation"])
def test_pending_clearance_is_bound_to_current_evidence_and_ledger(change):
    state, _, policy = pending_clearance_fixture()
    assert _field_city_alternate_route_revalidation_record(state, policy_id=policy) is not None
    if change == "xp":
        state["xp"] += 1
    elif change == "loss":
        state["campaign_xp_loss_total"] += 1
    elif change == "result":
        state["campaign_research_results"][policy]["crowded"] = True
    elif change == "ledger":
        state.pop(PRODUCTIVE_CITY_CLEARANCE_KEY)
    elif change == "spent":
        state[PRODUCTIVE_CITY_CLEARANCE_KEY]["policies"][policy]["status"] = "attempted"
    elif change == "observation":
        state[PRODUCTIVE_CITY_CLEARANCE_KEY]["policies"][policy]["observation_run_id"] = 6
    assert _field_city_alternate_route_revalidation_record(state, policy_id=policy) is None


def test_clearance_dispatch_consumes_both_receipts_and_keeps_old_failure():
    state, candidate, policy = pending_clearance_fixture()
    old = dict(state[_FIELD_CITY_CLEAR_ROUTE_REVALIDATION_KEY]["superseded_clearance"])
    assert _mark_field_city_alternate_route_revalidation(state, candidate, character_level=30)
    assert state[PRODUCTIVE_CITY_CLEARANCE_KEY]["policies"][policy]["status"] == "attempted"
    assert state[_FIELD_CITY_CLEAR_ROUTE_REVALIDATION_KEY]["status"] == "attempted"
    assert state[_FIELD_CITY_CLEAR_ROUTE_REVALIDATION_KEY]["superseded_clearance"] == old
    assert not _mark_field_city_alternate_route_revalidation(state, candidate, character_level=30)
