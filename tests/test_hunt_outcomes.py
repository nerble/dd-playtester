from __future__ import annotations

from copy import deepcopy
import json

import pytest

from dd4tester.hunt_outcomes import (
    IDLE_PURSUIT_REVALIDATIONS_KEY,
    LOCATOR_ORIGIN_ABORT,
    REGISTERED_LOCATOR_REVALIDATIONS_KEY,
    crowded_combat_loss_target,
    completed_prior_level_single_target_hunt,
    completed_single_target_hunt,
    idle_pursuit_revalidation_evidence,
    isolated_health_floor_target,
    registered_locator_revalidation_evidence,
    restore_idle_pursuit_receipts,
)
from dd4tester.storage import RUN_REPORT_SUMMARY_VERSION


POLICY = "registered-three-target-hunt"
SOURCE = "source-ranked-hunt-test-100-200-30"
WAITER_POLICY = "mirror-realm-plain-waiter-hunt-38-40"
WAITER_SOURCE_38 = "source-ranked-hunt-mirror-realm-19027-19072-38"
WAITER_SOURCE_39 = "source-ranked-hunt-mirror-realm-19027-19072-39"


def _prior_level_waiter_evidence():
    state = {
        "level": 39, "world_boot_id": "boot", "campaign_source_revision": "new-source",
        "xp": 9000, "campaign_xp_loss_total": 1200, "room_vnum": "3054",
        "hp": 936, "dead": False, "in_combat": False, "enemies": [],
        "campaign_registered_research_xp_loss_policies": [],
        "campaign_source_ranked_xp_loss_policies": [],
    }
    start = {
        "level": 38, "world_boot_id": "boot", "campaign_source_revision": "old-source",
        "xp": 1000, "campaign_xp_loss_total": 551, "room_vnum": "3054",
        "hp": 911, "dead": False, "in_combat": False, "enemies": [],
    }
    kills = [{
        "mob_name": "the waiter", "source_mobile_vnum": 19027,
        "source_policy_id": WAITER_SOURCE_38, "xp_gained": 4206,
    }]
    end = {
        **start, "xp": 5206, "campaign_objective_kills": kills,
        "campaign_fastwalk_source_consider_outcomes": {WAITER_SOURCE_38: True},
    }
    segment = {
        "id": 42, "run_id": 7, "phase": WAITER_POLICY, "status": "success",
        "finished_at": "finished", "command_count": 122,
        "start_state_json": json.dumps(start), "end_state_json": json.dumps(end),
    }
    summary = {
        "summary_version": RUN_REPORT_SUMMARY_VERSION,
        "run": {"id": 7},
        "outcomes": {"execution": "success", "objective": "achieved", "safety": "safe"},
        "progress": {
            "level": {"change": 0, "final": 38, "initial": 38},
            "level_gains_observed": 0,
            "experience": {"change": 4206, "final": 5206, "initial": 1000},
            "confirmed_kills": kills,
        },
    }
    return state, segment, summary


def test_prior_level_waiter_receipt_only_prioritizes_fresh_current_level_policy() -> None:
    state, segment, summary = _prior_level_waiter_evidence()
    assert completed_prior_level_single_target_hunt(
        state, segment, summary, policy_id=WAITER_POLICY,
        prior_source_policy_id=WAITER_SOURCE_38,
        current_source_policy_id=WAITER_SOURCE_39, mobile_vnum=19027,
        audited_source_revision="new-source",
    )


@pytest.mark.parametrize("change", [
    "summary_version", "phase", "outcome", "boot", "terminal_level", "source_revision",
    "not_productive", "lost_xp", "wrong_source", "wrong_mobile", "consider", "abort",
    "target_loss",
])
def test_prior_level_waiter_receipt_rejects_stale_or_unsafe_evidence(change: str) -> None:
    state, segment, summary = _prior_level_waiter_evidence()
    start = json.loads(segment["start_state_json"])
    end = json.loads(segment["end_state_json"])
    if change == "summary_version":
        summary["summary_version"] -= 1
    elif change == "phase":
        segment["phase"] = "other-policy"
    elif change == "outcome":
        summary["outcomes"]["safety"] = "loss"
    elif change == "boot":
        state["world_boot_id"] = "new-boot"
    elif change == "terminal_level":
        state["level"] = 40
    elif change == "source_revision":
        segment["end_state_json"] = json.dumps({**end, "campaign_source_revision": "split-source"})
    elif change == "not_productive":
        summary["progress"]["experience"]["change"] = 0
    elif change == "lost_xp":
        segment["end_state_json"] = json.dumps({**end, "campaign_xp_loss_total": 552})
    elif change == "wrong_source":
        summary["progress"]["confirmed_kills"][0]["source_policy_id"] = "other-source"
    elif change == "wrong_mobile":
        summary["progress"]["confirmed_kills"][0]["source_mobile_vnum"] = 19069
    elif change == "consider":
        end["campaign_fastwalk_source_consider_outcomes"][WAITER_SOURCE_38] = False
        segment["end_state_json"] = json.dumps(end)
    elif change == "abort":
        end["campaign_fastwalk_abort_reason"] = "crowded room"
        segment["end_state_json"] = json.dumps(end)
    elif change == "target_loss":
        state["campaign_source_ranked_xp_loss_policies"] = [{
            "boot_id": "boot", "policy_id": WAITER_SOURCE_39,
        }]
    assert not completed_prior_level_single_target_hunt(
        state, segment, summary, policy_id=WAITER_POLICY,
        prior_source_policy_id=WAITER_SOURCE_38,
        current_source_policy_id=WAITER_SOURCE_39, mobile_vnum=19027,
        audited_source_revision="new-source",
    )


def _crowded_loss_evidence():
    state, segment, summary = _evidence()
    start = json.loads(segment["start_state_json"])
    end = json.loads(segment["end_state_json"])
    for snapshot in (state, start, end):
        snapshot.update(hp=702, max_hp=702, in_combat=False)
    start["campaign_xp_loss_total"] = 0
    end["campaign_fastwalk_crowded"] = True
    end["campaign_fastwalk_abort_reason"] = (
        "combat text identified 'Caroline' outside the duplicated GMCP enemy snapshot"
    )
    state.update(end)
    state["campaign_registered_research_xp_loss_policies"][0]["level"] = 30
    segment.update(command_count=100, start_state_json=json.dumps(start), end_state_json=json.dumps(end))
    summary["progress"] = {"combat_starts": 1, "confirmed_kills": []}
    return state, segment, summary


def test_extra_attacker_loss_scopes_only_the_observed_target() -> None:
    state, segment, summary = _crowded_loss_evidence()
    state["campaign_research_results"][POLICY] = {"boot_id": "boot", "completed_kill": True}
    state["campaign_source_revision"] = "new-source"
    original = deepcopy(state)
    assert crowded_combat_loss_target(
        state, segment, summary, policy_id=POLICY, source_policy_ids=(SOURCE,),
    ) == SOURCE
    assert state == original


@pytest.mark.parametrize("change", [
    "loss_total", "loss_record", "loss_id", "repeated_loss", "level", "boot", "run",
    "source_pair", "missing_source", "health", "location", "death", "objective", "no_combat",
    "kill", "route", "consider", "multiple_targets", "identity", "abort", "crowd", "sighting",
])
def test_extra_attacker_scope_rejects_ambiguous_or_changed_evidence(change: str) -> None:
    state, segment, summary = _crowded_loss_evidence()
    end = json.loads(segment["end_state_json"])
    if change == "loss_total":
        state["campaign_xp_loss_total"] += 1
    elif change == "loss_record":
        state["campaign_registered_research_xp_loss_policies"] = []
    elif change == "loss_id":
        state["campaign_registered_research_xp_loss_policies"][0]["loss_event_id"] += 1
    elif change == "repeated_loss":
        state["campaign_registered_research_xp_loss_policies"][0]["loss_count"] += 1
    elif change in {"level", "boot"}:
        state["world_boot_id" if change == "boot" else "level"] = "changed"
    elif change == "run":
        summary["run"]["id"] += 1
    elif change == "source_pair":
        end["campaign_source_revision"] = "changed"
    elif change == "missing_source":
        state.pop("campaign_source_revision")
    elif change == "health":
        state["hp"] -= 1
    elif change == "location":
        end["room_vnum"] = "9502"
    elif change == "death":
        summary["evidence"]["game_event_counts"]["character_died"] = 1
    elif change == "objective":
        summary["outcomes"]["objective"] = "achieved"
    elif change == "no_combat":
        summary["progress"]["combat_starts"] = 0
    elif change == "kill":
        summary["progress"]["confirmed_kills"] = ["Martin"]
    elif change == "route":
        end["campaign_fastwalk_route_hazards"] = ["locked door"]
    elif change == "consider":
        end["campaign_fastwalk_source_consider_outcomes"][SOURCE] = False
    elif change == "multiple_targets":
        end["campaign_fastwalk_source_consider_outcomes"]["other-target"] = True
    elif change == "identity":
        end["campaign_fastwalk_target_vnum_mismatch"] = True
    elif change == "abort":
        end["campaign_fastwalk_abort_reason"] = "health at or below 20%"
    elif change == "crowd":
        end["campaign_fastwalk_crowded"] = False
    elif change == "sighting":
        end["campaign_fastwalk_source_present_sightings"].append({"policy_id": "other-target"})
    segment["end_state_json"] = json.dumps(end)
    assert crowded_combat_loss_target(
        state, segment, summary, policy_id=POLICY, source_policy_ids=(SOURCE,),
    ) is None


def _locator_evidence():
    state, segment, summary = _pursuit_evidence()
    state["campaign_fastwalk_abort_reason"] = LOCATOR_ORIGIN_ABORT
    state["campaign_research_results"][POLICY]["route_hazard"] = LOCATOR_ORIGIN_ABORT
    state["campaign_fastwalk_where_decisions"] = [{
        "source_mobile_vnum": 9513, "target": "martin", "relocation": True,
        "room_vnum": "9514", "locations": ["a dark corridor"],
        "mapped_rooms": {"a dark corridor": ["9504", "9514"]}, "planned_endpoints": [],
    }]
    segment["start_state_json"] = segment["end_state_json"] = json.dumps(state)
    source = {
        "policy_id": POLICY, "source_policy_id": SOURCE, "mobile_vnum": 9513, "target": "Martin",
        "productive_policy_ids": (SOURCE,), "location_routes": {"a dark corridor": ("9504", "9514")},
        "relocation_routes": (("9514", "a dark corridor", ("9503", "9504")),
                              ("9514", "a dark corridor", ())),
    }
    return state, segment, summary, source


def test_locator_origin_repair_preserves_unrelated_progress_and_loss() -> None:
    state, segment, summary, source = _locator_evidence()
    state["xp"] += 300
    state["campaign_xp_loss_total"] += 551
    state["campaign_registered_research_xp_loss_policies"] = [{
        "policy_id": "independent-hunt", "boot_id": "boot", "loss_count": 1,
    }]
    original = deepcopy(state)
    receipt = registered_locator_revalidation_evidence(state, segment, summary, **source)
    assert receipt is not None
    assert receipt["prior_locator_decision"]["room_vnum"] == "9514"
    assert receipt["superseded_result"]["route_hazard"] == LOCATOR_ORIGIN_ABORT
    assert state == original
    state[REGISTERED_LOCATOR_REVALIDATIONS_KEY] = {POLICY: json.loads(json.dumps(receipt))}
    assert registered_locator_revalidation_evidence(state, segment, summary, **source) == receipt
    state[REGISTERED_LOCATOR_REVALIDATIONS_KEY][POLICY]["status"] = "attempted"
    assert registered_locator_revalidation_evidence(state, segment, summary, **source) is None


def test_consumed_registered_locator_receipt_survives_the_terminal_handoff() -> None:
    from dd4tester.campaign import _campaign_segment_end_state

    state, segment, summary, source = _locator_evidence()
    receipt = registered_locator_revalidation_evidence(state, segment, summary, **source)
    assert receipt is not None
    receipt["status"] = "attempted"
    state[REGISTERED_LOCATOR_REVALIDATIONS_KEY] = {POLICY: receipt}
    terminal = {key: value for key, value in state.items() if key != REGISTERED_LOCATOR_REVALIDATIONS_KEY}
    merged = _campaign_segment_end_state(state, terminal, execution="vampire-catacombs-hunt", policy_id=POLICY)
    assert merged[REGISTERED_LOCATOR_REVALIDATIONS_KEY][POLICY] == receipt


@pytest.mark.parametrize("change", [
    "no_productive_kill", "registered_loss", "source_loss", "source", "boot", "level",
    "combat", "xp_change", "loss_change", "health", "objective", "run", "route",
    "consider", "crowd", "mapped_room", "missing_origin", "partial_routes", "identity",
    "wrong_abort", "already_registered", "pending_changed", "cleared_loss",
])
def test_locator_origin_repair_rejects_other_failures_and_incomplete_routes(change: str) -> None:
    state, segment, summary, source = _locator_evidence()
    end = json.loads(segment["end_state_json"])
    if change == "no_productive_kill":
        source["productive_policy_ids"] = ()
    elif change in {"registered_loss", "source_loss"}:
        key = "campaign_registered_research_xp_loss_policies" if change == "registered_loss" else "campaign_source_ranked_xp_loss_policies"
        state[key] = [{"boot_id": "boot", "policy_id": POLICY if change == "registered_loss" else SOURCE}]
    elif change in {"source", "boot", "level"}:
        key = {"source": "campaign_source_revision", "boot": "world_boot_id"}.get(change, change)
        state[key] = "changed"
    elif change == "combat":
        summary["progress"]["combat_starts"] = 1
    elif change in {"xp_change", "loss_change"}:
        end["xp" if change == "xp_change" else "campaign_xp_loss_total"] += 1
    elif change == "health":
        state["hp"] -= 1
    elif change == "objective":
        summary["outcomes"]["objective"] = "achieved"
    elif change == "run":
        summary["run"]["id"] += 1
    elif change == "route":
        end["campaign_fastwalk_route_hazards"] = ["locked door"]
    elif change == "consider":
        end["campaign_fastwalk_source_consider_outcomes"] = {SOURCE: True}
    elif change == "crowd":
        end["campaign_fastwalk_crowded"] = True
    elif change == "mapped_room":
        source["location_routes"] = {"a dark corridor": ("9504", "9514", "9515")}
    elif change == "missing_origin":
        source["relocation_routes"] = (("9500", "a dark corridor", ("9504",)),)
    elif change == "partial_routes":
        source["relocation_routes"] = (("9514", "a dark corridor", ()),)
    elif change == "identity":
        end["campaign_fastwalk_where_decisions"][-1]["source_mobile_vnum"] = 9517
    elif change == "wrong_abort":
        end["campaign_fastwalk_abort_reason"] = "target absent"
    elif change == "already_registered":
        end["campaign_fastwalk_where_decisions"][-1]["registered_route_origin"] = "9514"
    elif change == "pending_changed":
        state[REGISTERED_LOCATOR_REVALIDATIONS_KEY] = {POLICY: {"status": "pending", "revision": 99}}
    elif change == "cleared_loss":
        state["campaign_xp_loss_total"] = 0
    segment["end_state_json"] = json.dumps(end)
    assert registered_locator_revalidation_evidence(state, segment, summary, **source) is None


def _pursuit_evidence():
    abort = "bounded pursuit of 'paul' reached 1 step(s)"
    state = {
        "level": 30, "world_boot_id": "boot", "campaign_source_revision": "rev",
        "xp": 1000, "campaign_xp_loss_total": 551, "room_vnum": "3054",
        "hp": 702, "max_hp": 702, "dead": False, "in_combat": False,
        "campaign_fastwalk_abort_reason": abort,
        "campaign_fastwalk_target_present_observed": True,
        "campaign_fastwalk_where_decisions": [{
            "source_mobile_vnum": 9517, "target": "paul",
            "mapped_rooms": {"the kitchen": ["9509"]},
        }],
        "campaign_research_results": {
            POLICY: {"boot_id": "boot", "route_hazard": abort},
        },
    }
    segment = {
        "id": 42, "run_id": 7, "phase": POLICY, "status": "success",
        "finished_at": "finished", "command_count": 100,
        "start_state_json": json.dumps(state), "end_state_json": json.dumps(state),
    }
    summary = {
        "run": {"id": 7},
        "outcomes": {"execution": "success", "objective": "not_achieved", "safety": "safe"},
        "progress": {
            "combat_starts": 0, "confirmed_kills": [],
            "experience": {"change": 0}, "health": {"lowest_fraction": 1.0},
        },
    }
    return state, segment, summary


def test_idle_pursuit_revalidation_preserves_the_exact_failed_route() -> None:
    state, segment, summary = _pursuit_evidence()
    original = deepcopy(state)
    receipt = idle_pursuit_revalidation_evidence(
        state, segment, summary, policy_id=POLICY, mobile_vnum=9517, target="Paul",
    )
    assert receipt is not None
    assert receipt["prior_run_id"] == 7
    assert receipt["status"] == "attempted"
    assert receipt["maximum_pursuit_steps"] == 3
    assert state == original


@pytest.mark.parametrize("changed_source", [False, True])
def test_idle_pursuit_receipt_survives_a_missing_terminal_field(changed_source: bool) -> None:
    state, segment, summary = _pursuit_evidence()
    receipt = idle_pursuit_revalidation_evidence(
        state, segment, summary, policy_id=POLICY, mobile_vnum=9517, target="Paul",
    )
    start = {**state, IDLE_PURSUIT_REVALIDATIONS_KEY: {POLICY: receipt}}
    attempted = {**segment, "id": 43, "run_id": 8, "start_state_json": json.dumps(start)}
    if changed_source:
        state["campaign_source_revision"] = "other-source"
    restored = restore_idle_pursuit_receipts(state, (attempted,))
    if changed_source:
        assert restored == state
    else:
        assert restored[IDLE_PURSUIT_REVALIDATIONS_KEY][POLICY] == receipt
        assert idle_pursuit_revalidation_evidence(
            restored, segment, summary, policy_id=POLICY, mobile_vnum=9517, target="Paul",
        ) is None


@pytest.mark.parametrize("change", [
    "spent", "xp", "loss", "source", "boot", "level", "health", "combat",
    "run", "objective", "damage", "route", "identity", "locator", "consider",
])
def test_idle_pursuit_revalidation_rejects_changed_or_unsafe_evidence(change: str) -> None:
    state, segment, summary = _pursuit_evidence()
    end = json.loads(segment["end_state_json"])
    if change == "spent":
        state[IDLE_PURSUIT_REVALIDATIONS_KEY] = {POLICY: {"status": "attempted"}}
    elif change in {"xp", "loss", "source", "boot", "level"}:
        key = {"loss": "campaign_xp_loss_total", "source": "campaign_source_revision", "boot": "world_boot_id"}.get(change, change)
        state[key] = "changed"
    elif change == "health":
        state["hp"] = 701
    elif change == "combat":
        summary["progress"]["combat_starts"] = 1
    elif change == "run":
        summary["run"]["id"] = 8
    elif change == "objective":
        summary["outcomes"]["objective"] = "achieved"
    elif change == "damage":
        summary["progress"]["health"]["lowest_fraction"] = .9
    elif change == "route":
        end["campaign_fastwalk_route_hazards"] = ["locked door"]
    elif change == "identity":
        end["campaign_fastwalk_target_vnum_mismatch"] = True
    elif change == "locator":
        end["campaign_fastwalk_where_decisions"] = []
    elif change == "consider":
        end["campaign_fastwalk_source_consider_outcomes"] = {SOURCE: True}
    segment["end_state_json"] = json.dumps(end)
    assert idle_pursuit_revalidation_evidence(
        state, segment, summary, policy_id=POLICY, mobile_vnum=9517, target="Paul",
    ) is None


def _evidence():
    start = {
        "level": 30, "world_boot_id": "boot", "campaign_source_revision": "rev",
        "room_vnum": "3054", "dead": False,
    }
    end = {
        **start, "in_combat": False, "campaign_xp_loss_total": 551,
        "campaign_objective_kills": [], "campaign_fastwalk_route_hazards": [],
        "campaign_fastwalk_abort_reason": (
            "field combat aborted for safety: health at or below 31%"
        ),
        "campaign_fastwalk_source_consider_outcomes": {SOURCE: True},
        "campaign_fastwalk_source_present_sightings": [{"policy_id": SOURCE}],
        "campaign_research_results": {
            POLICY: {"boot_id": "boot", "retryable_failure": True},
        },
    }
    state = {
        **end,
        "campaign_research_results": {
            POLICY: {"boot_id": "boot", "retryable_failure": True},
        },
        "campaign_registered_research_xp_loss_policies": [{
            "policy_id": POLICY, "boot_id": "boot", "loss_count": 1,
            "loss_event_id": 42,
        }],
    }
    segment = {
        "id": 42, "phase": POLICY, "status": "success", "run_id": 7,
        "finished_at": "finished", "start_state_json": json.dumps(start),
        "end_state_json": json.dumps(end),
    }
    summary = {
        "run": {"id": 7},
        "outcomes": {
            "execution": "success", "objective": "not_achieved", "safety": "loss",
        },
        "evidence": {"game_event_counts": {"experience_lost": 1}},
    }
    return state, segment, summary


def test_health_withdrawal_scopes_failure_without_clearing_xp_loss() -> None:
    state, segment, summary = _evidence()
    original = deepcopy(state)

    assert isolated_health_floor_target(
        state, segment, summary, policy_id=POLICY, source_policy_ids=(SOURCE,),
    ) == SOURCE
    assert state == original


@pytest.mark.parametrize("conflicting_current_result", [False, True])
def test_expired_result_uses_exact_linked_loss_evidence_only_when_missing(
    conflicting_current_result: bool,
) -> None:
    state, segment, summary = _evidence()
    state["campaign_research_results"] = (
        {POLICY: {"boot_id": "boot", "fatal_failure": True}}
        if conflicting_current_result else {}
    )
    original = deepcopy(state)

    assert isolated_health_floor_target(
        state, segment, summary, policy_id=POLICY, source_policy_ids=(SOURCE,),
    ) == (None if conflicting_current_result else SOURCE)
    assert state == original


@pytest.mark.parametrize("change", [
    "death", "route", "output", "multiple_targets", "source", "run", "loss_count",
])
def test_ambiguous_or_route_failures_do_not_open_other_targets(change: str) -> None:
    state, segment, summary = _evidence()
    end = json.loads(segment["end_state_json"])
    if change == "death":
        summary["evidence"]["game_event_counts"]["character_died"] = 1
    elif change == "route":
        end["campaign_fastwalk_route_hazards"] = ["locked exit"]
    elif change == "output":
        end["campaign_fastwalk_abort_reason"] = "live output budget was exhausted"
    elif change == "multiple_targets":
        end["campaign_fastwalk_source_consider_outcomes"]["other-source"] = True
    elif change == "source":
        state["campaign_source_revision"] = "new-revision"
    elif change == "run":
        summary["run"]["id"] = 99
    elif change == "loss_count":
        state["campaign_registered_research_xp_loss_policies"][0]["loss_count"] = 2
    segment["end_state_json"] = json.dumps(end)

    assert isolated_health_floor_target(
        state, segment, summary, policy_id=POLICY, source_policy_ids=(SOURCE,),
    ) is None


def _completed_hunt_evidence():
    start = {
        "level": 30, "world_boot_id": "boot", "campaign_source_revision": "revision",
        "campaign_xp_loss_total": 500, "room_vnum": "3054", "dead": False,
        "in_combat": False, "enemies": [], "hp": 717, "xp": 662990,
    }
    kill = {"source_mobile_vnum": 9500, "source_policy_id": SOURCE, "xp_gained": 2074}
    end = {
        **start, "hp": 698, "xp": 665064, "campaign_objective_kills": [kill],
        "campaign_fastwalk_source_consider_outcomes": {SOURCE: True},
    }
    segment = {
        "phase": POLICY, "status": "success", "finished_at": "finished", "run_id": 74,
        "command_count": 161, "start_state_json": json.dumps(start),
        "end_state_json": json.dumps(end),
    }
    summary = {
        "summary_version": RUN_REPORT_SUMMARY_VERSION, "run": {"id": 74},
        "outcomes": {"execution": "success", "objective": "achieved", "safety": "safe"},
        "progress": {"confirmed_kills": [kill]},
    }
    return deepcopy(end), segment, summary


def test_completed_independent_target_keeps_other_losses_without_repairing_them() -> None:
    state, segment, summary = _completed_hunt_evidence()
    state["campaign_registered_research_xp_loss_policies"] = [{"policy_id": "other-hunt"}]
    original = deepcopy(state)
    assert completed_single_target_hunt(
        state, segment, summary, policy_id=POLICY, source_policy_id=SOURCE, mobile_vnum=9500,
    )
    assert state == original


@pytest.mark.parametrize("change", [
    "old_summary", "wrong_run", "no_commands", "failed_execution", "unachieved", "loss",
    "source", "boot", "level", "loss_total", "xp", "field", "dead", "combat", "abort",
    "crowd", "missing_kill", "multiple_kills", "wrong_mobile", "wrong_policy", "below_band",
    "boolean_reward", "consider", "changed_kill", "invalid_json",
])
def test_completed_target_proof_rejects_failed_changed_and_ambiguous_visits(change: str) -> None:
    state, segment, summary = _completed_hunt_evidence()
    end = json.loads(segment["end_state_json"])
    if change == "old_summary":
        summary["summary_version"] -= 1
    elif change == "wrong_run":
        summary["run"]["id"] += 1
    elif change == "no_commands":
        segment["command_count"] = 0
    elif change in {"failed_execution", "unachieved", "loss"}:
        key, value = {
            "failed_execution": ("execution", "failed"),
            "unachieved": ("objective", "not_achieved"), "loss": ("safety", "loss"),
        }[change]
        summary["outcomes"][key] = value
    elif change in {"source", "boot", "level", "loss_total"}:
        key = {
            "source": "campaign_source_revision", "boot": "world_boot_id",
            "level": "level", "loss_total": "campaign_xp_loss_total",
        }[change]
        state[key] = "changed"
    elif change == "xp":
        state["xp"] = 662990
    elif change == "field":
        end["room_vnum"] = "9501"
    elif change in {"dead", "combat"}:
        end["dead" if change == "dead" else "in_combat"] = True
    elif change in {"abort", "crowd"}:
        end["campaign_fastwalk_abort_reason" if change == "abort" else "campaign_fastwalk_crowded"] = True
    elif change == "missing_kill":
        summary["progress"]["confirmed_kills"] = []
    elif change == "multiple_kills":
        summary["progress"]["confirmed_kills"] *= 2
    elif change in {"wrong_mobile", "wrong_policy", "below_band", "boolean_reward"}:
        key, value = {
            "wrong_mobile": ("source_mobile_vnum", 9501),
            "wrong_policy": ("source_policy_id", "other"),
            "below_band": ("xp_gained", 300), "boolean_reward": ("xp_gained", True),
        }[change]
        summary["progress"]["confirmed_kills"][0][key] = value
    elif change == "consider":
        end["campaign_fastwalk_source_consider_outcomes"][SOURCE] = False
    elif change == "changed_kill":
        end["campaign_objective_kills"] = []
    if change == "invalid_json":
        segment["end_state_json"] = "{"
    else:
        segment["end_state_json"] = json.dumps(end)
    assert not completed_single_target_hunt(
        state, segment, summary, policy_id=POLICY, source_policy_id=SOURCE, mobile_vnum=9500,
    )
