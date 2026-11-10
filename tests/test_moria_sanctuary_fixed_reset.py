from __future__ import annotations

import json
import sqlite3
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest

from dd4tester import campaign


class _RecoveryEvidenceStorage:
    def __init__(
        self,
        segment: dict[str, Any],
        summary: dict[str, Any],
        *,
        moria_segment: dict[str, Any] | None = None,
        moria_summary: dict[str, Any] | None = None,
    ) -> None:
        self.segment = segment
        self.summary = summary
        self.moria_segment = moria_segment
        self.moria_summary = moria_summary

    def get_latest_campaign_segment_for_phase(
        self,
        campaign_id: int,
        phase: str,
        *,
        search_limit: int,
    ) -> dict[str, Any] | None:
        assert campaign_id == 7
        assert search_limit == 256
        if phase == campaign._MORIA_SANCTUARY_FIXED_RESET_POLICY_ID:
            return self.moria_segment
        if phase == campaign._SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id:
            return self.segment
        return None

    def get_run_summary(self, run_id: int) -> dict[str, Any]:
        if self.moria_summary is not None:
            if run_id == self.moria_summary["run"]["id"]:
                return self.moria_summary
        assert run_id == self.summary["run"]["id"]
        return self.summary


def _fallback_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[dict[str, Any], campaign.ProgressionPolicy, _RecoveryEvidenceStorage]:
    revision = "current-source-revision"
    monkeypatch.setattr(
        campaign, "_current_dd4_source_revision", lambda: revision
    )
    policy_id = campaign._SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
    state: dict[str, Any] = {
        "level": 39,
        "world_boot_id": "boot-1",
        campaign._SOURCE_REVISION_KEY: revision,
        "room_vnum": "3054",
        "room_flags": ["safe", "healing"],
        "hp": 936,
        "max_hp": 936,
        "dead": False,
        "in_combat": False,
        "enemies": [],
        "xp": 12345,
        "campaign_xp_loss_total": 0,
        "campaign_protection_recovery_required": {
            "boot_id": "boot-1",
            "level": 39,
            "xp_delta": -100,
        },
        "campaign_research_results": {
            policy_id: {
                "boot_id": "boot-1",
                "level": 39,
                "absent": True,
                "fatal_failure": True,
                "required_object_acquired": False,
                "completed_kill": False,
                "route_hazard": campaign._SANCTUARY_RESOURCE_EXHAUSTED_HAZARD,
            },
        },
        campaign._SANCTUARY_RESOURCE_ATTEMPTS_KEY: {
            policy_id: {"boot_id": "boot-1", "level": 39, "count": 2},
        },
    }
    state = campaign._arm_sanctuary_resource_area_reset_recheck(state)
    state = campaign._reopen_sanctuary_resource_after_reset_wait(
        state, after_segment_id=17
    )
    assert campaign._consume_sanctuary_area_reset_recheck(state)
    state[campaign._SANCTUARY_RESOURCE_ATTEMPTS_KEY][policy_id]["count"] = 1
    state["campaign_research_results"] = {
        policy_id: {
            "boot_id": "boot-1",
            "level": 39,
            "absent": True,
            "fatal_failure": True,
            "required_object_acquired": False,
            "completed_kill": False,
            "route_hazard": campaign._SANCTUARY_RESOURCE_EXHAUSTED_HAZARD,
        },
    }
    assert campaign._sanctuary_area_reset_recheck_failure_terminal(state)

    start = {
        "level": 39,
        "world_boot_id": "boot-1",
        campaign._SOURCE_REVISION_KEY: revision,
        "room_vnum": "3054",
        "dead": False,
        "in_combat": False,
        "xp": 12345,
        "campaign_xp_loss_total": 0,
    }
    end = {
        **start,
        "campaign_fastwalk_target_absent": True,
        campaign._SOURCE_ABSENT_SIGHTINGS_KEY: [{
            "policy_id": policy_id,
            "room_vnum": "927",
            "target": "alchemist",
        }],
    }
    segment = {
        "id": 18,
        "run_id": 100,
        "phase": policy_id,
        "status": "success",
        "finished_at": "finished",
        "start_state_json": json.dumps(start),
        "end_state_json": json.dumps(end),
    }
    summary = {
        "run": {"id": 100},
        "outcomes": {
            "execution": "success",
            "objective": "not_achieved",
            "safety": "safe",
        },
        "progress": {
            "experience": {"change": 0},
            "confirmed_kills": [],
        },
    }
    unavailable = replace(
        campaign._SOURCE_RANKED_HUNT_POLICY,
        policy_id=f"{campaign._SOURCE_RANKED_POLICY_PREFIX}unavailable-39",
        minimum_level=39,
        maximum_level=39,
        status="unavailable",
        execution=None,
    )
    return state, unavailable, _RecoveryEvidenceStorage(segment, summary)


def _locator_revalidation_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[dict[str, Any], campaign.ProgressionPolicy, _RecoveryEvidenceStorage]:
    state, policy, base_storage = _fallback_evidence(monkeypatch)
    attempt = {
        "attempted_at": "attempt-1",
        "boot_id": "boot-1",
        "level": 39,
        "source_revision": "current-source-revision",
        "status": "attempted",
        "prior_segment_id": 17,
        "source_mobile_vnum": campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
        "source_object_vnum": campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,
        "source_reset_room_vnum": 4064,
    }
    state[campaign._MORIA_SANCTUARY_FIXED_RESET_ATTEMPT_KEY] = attempt
    state["affects"] = [[{"name": "fly", "duration": "17"}]]
    snapshot = {
        "level": 39,
        "world_boot_id": "boot-1",
        campaign._SOURCE_REVISION_KEY: "current-source-revision",
        "room_vnum": "3054",
        "dead": False,
        "in_combat": False,
        "xp": 12345,
        "campaign_xp_loss_total": 0,
        campaign._MORIA_SANCTUARY_FIXED_RESET_ATTEMPT_KEY: attempt,
    }
    end = {
        **snapshot,
        "campaign_fastwalk_target_absent": True,
        "campaign_fastwalk_target_present_observed": False,
        "campaign_fastwalk_where_relocation_attempts": 0,
        "fastwalk_route": "moria",
        "fastwalk_abort_reason": None,
    }
    segment = {
        "id": 44,
        "run_id": 101,
        "phase": campaign._MORIA_SANCTUARY_FIXED_RESET_POLICY_ID,
        "status": "success",
        "finished_at": "finished",
        "start_state_json": json.dumps(snapshot),
        "end_state_json": json.dumps(end),
    }
    summary = {
        "run": {"id": 101},
        "outcomes": {
            "execution": "success",
            "objective": "not_achieved",
            "safety": "safe",
        },
        "progress": {
            "experience": {"change": 0},
            "confirmed_kills": [],
            "combat_starts": 0,
            "items_acquired": 0,
        },
        "objective": {
            "fastwalk_route": "moria",
            "fastwalk_hunt_stop_boundaries": [
                {
                    "actions": [],
                    "required_items": ["purple potion"],
                    "source_reset_room_vnum": "4064",
                    "target": "large hobgoblin",
                }
            ],
        },
    }
    storage = _RecoveryEvidenceStorage(
        base_storage.segment,
        base_storage.summary,
        moria_segment=segment,
        moria_summary=summary,
    )
    return state, policy, storage


def test_moria_safe_fixed_reset_miss_allows_one_bounded_locator_revalidation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, policy, storage = _locator_revalidation_evidence(monkeypatch)

    evidence = campaign._moria_sanctuary_fixed_reset_locator_revalidation_evidence(
        state,
        policy,
        storage=storage,
        campaign_id=7,
    )

    assert evidence == {
        "boot_id": "boot-1",
        "level": 39,
        "source_revision": "current-source-revision",
        "prior_source_revision": "current-source-revision",
        "prior_run_id": 101,
        "prior_segment_id": 44,
        "source_mobile_vnum": campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
        "source_object_vnum": campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,
        "source_reset_room_vnum": 4064,
        "reason": "prior exact room-4064 check safely missed the wandering carrier",
    }

    state[campaign._MORIA_SANCTUARY_FIXED_RESET_LOCATOR_REVALIDATION_KEY] = {
        **evidence,
        "status": "attempted",
    }
    assert campaign._moria_sanctuary_fixed_reset_locator_revalidation_evidence(
        state,
        policy,
        storage=storage,
        campaign_id=7,
    ) is None


def test_moria_safe_miss_can_cross_source_refresh_only_after_exact_audit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, policy, storage = _locator_revalidation_evidence(monkeypatch)
    prior_revision = "e7e3a269c006c5386590cfbc07419b42ebd5b424"
    current_revision = campaign._current_dd4_source_revision()
    assert current_revision is not None and current_revision != prior_revision
    monkeypatch.setattr(
        campaign,
        "_current_dd4_source_revision",
        lambda: current_revision,
    )
    state[campaign._SOURCE_REVISION_KEY] = current_revision
    state[campaign._MORIA_SANCTUARY_FIXED_RESET_ATTEMPT_KEY][
        "source_revision"
    ] = prior_revision
    start = json.loads(storage.moria_segment["start_state_json"])
    end = json.loads(storage.moria_segment["end_state_json"])
    for snapshot in (start, end):
        snapshot[campaign._SOURCE_REVISION_KEY] = prior_revision
        snapshot[campaign._MORIA_SANCTUARY_FIXED_RESET_ATTEMPT_KEY][
            "source_revision"
        ] = prior_revision
    storage.moria_segment["start_state_json"] = json.dumps(start)
    storage.moria_segment["end_state_json"] = json.dumps(end)

    assert campaign._moria_sanctuary_fixed_reset_locator_revalidation_evidence(
        state,
        policy,
        storage=storage,
        campaign_id=7,
    ) is None

    current_world = campaign.load_world_source(
        campaign.current_source_directory(),
        include_all_areas=True,
    )
    evidence = (
        campaign._moria_sanctuary_fixed_reset_locator_revalidation_evidence(
            state,
            policy,
            storage=storage,
            campaign_id=7,
            source_world=current_world,
        )
    )
    assert evidence is not None
    assert evidence["source_revision"] == current_revision
    assert evidence["prior_source_revision"] == prior_revision
    assert evidence["prior_run_id"] == 101
    assert evidence["prior_segment_id"] == 44


@pytest.mark.parametrize(
    "mutation",
    [
        "stale-source",
        "changed-current-xp",
        "changed-current-loss",
        "unsafe-run",
        "carrier-not-absent",
        "wrong-reset",
        "multiple-stops",
        "prior-revalidation",
    ],
)
def test_moria_locator_revalidation_rejects_changed_or_unsafe_evidence(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    state, policy, storage = _locator_revalidation_evidence(monkeypatch)
    end = json.loads(storage.moria_segment["end_state_json"])
    objective = storage.moria_summary["objective"]

    if mutation == "stale-source":
        state[campaign._SOURCE_REVISION_KEY] = "old-source"
    elif mutation == "changed-current-xp":
        state["xp"] += 1
    elif mutation == "changed-current-loss":
        state["campaign_xp_loss_total"] += 1
    elif mutation == "unsafe-run":
        storage.moria_summary["outcomes"]["safety"] = "loss"
    elif mutation == "carrier-not-absent":
        end["campaign_fastwalk_target_absent"] = False
    elif mutation == "wrong-reset":
        objective["fastwalk_hunt_stop_boundaries"][0][
            "source_reset_room_vnum"
        ] = "4071"
    elif mutation == "multiple-stops":
        objective["fastwalk_hunt_stop_boundaries"].append(
            objective["fastwalk_hunt_stop_boundaries"][0]
        )
    elif mutation == "prior-revalidation":
        state[campaign._MORIA_SANCTUARY_FIXED_RESET_REVALIDATION_KEY] = {
            "boot_id": "boot-1",
            "level": 39,
            "status": "attempted",
        }
    storage.moria_segment["end_state_json"] = json.dumps(end)

    assert campaign._moria_sanctuary_fixed_reset_locator_revalidation_evidence(
        state,
        policy,
        storage=storage,
        campaign_id=7,
    ) is None


def test_moria_sanctuary_fallback_requires_complete_exact_absence_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, policy, storage = _fallback_evidence(monkeypatch)

    assert campaign._moria_sanctuary_fixed_reset_fallback_ready(
        state, policy, storage=storage, campaign_id=7
    )


def test_moria_level_transition_opens_one_fresh_fixed_reset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, policy, storage = _fallback_evidence(monkeypatch)
    state[campaign._MORIA_SANCTUARY_FIXED_RESET_ATTEMPT_KEY] = {
        "boot_id": "boot-1",
        "level": 38,
        "source_revision": "older-source-revision",
        "status": "attempted",
        "prior_run_id": 99,
        "prior_segment_id": 88,
        "source_mobile_vnum": campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
        "source_reset_room_vnum": 4064,
        "source_object_vnum": campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,
    }

    assert campaign._moria_sanctuary_fixed_reset_level_transition_ready(
        state, policy, storage=storage, campaign_id=7
    )
    assert campaign._moria_sanctuary_fixed_reset_level_transition_ready(
        state, None, storage=storage, campaign_id=7
    )

    state[campaign._MORIA_SANCTUARY_FIXED_RESET_ATTEMPT_KEY][
        "level_transition_reacquisition"
    ] = True
    assert not campaign._moria_sanctuary_fixed_reset_level_transition_ready(
        state, policy, storage=storage, campaign_id=7
    )


def test_moria_level_transition_does_not_reopen_same_level_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, policy, storage = _fallback_evidence(monkeypatch)
    state[campaign._MORIA_SANCTUARY_FIXED_RESET_ATTEMPT_KEY] = {
        "boot_id": "boot-1",
        "level": 39,
        "source_revision": "older-source-revision",
        "status": "attempted",
        "prior_run_id": 99,
        "prior_segment_id": 88,
        "source_mobile_vnum": campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
        "source_reset_room_vnum": 4064,
        "source_object_vnum": campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,
    }

    assert not campaign._moria_sanctuary_fixed_reset_level_transition_ready(
        state, policy, storage=storage, campaign_id=7
    )


def test_moria_source_refresh_revalidation_is_one_shot_and_keeps_old_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, policy, _storage = _fallback_evidence(monkeypatch)
    prior_attempt = {
        "boot_id": "boot-1",
        "level": 39,
        "source_revision": "previous-source-revision",
        "status": "attempted",
        "prior_run_id": 100,
        "prior_segment_id": 18,
        "source_mobile_vnum": campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
        "source_object_vnum": campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,
        "source_reset_room_vnum": 4064,
    }
    state[campaign._MORIA_SANCTUARY_FIXED_RESET_ATTEMPT_KEY] = prior_attempt
    monkeypatch.setattr(
        campaign,
        "_moria_sanctuary_fixed_reset_current_source_audit",
        lambda _state, *, source_world: True,
    )

    recovery_receipt = campaign._moria_sanctuary_source_refresh_revalidation_evidence(
        state,
        campaign._SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY,
        source_world=object(),
    )
    assert recovery_receipt is not None

    receipt = campaign._moria_sanctuary_source_refresh_revalidation_evidence(
        state,
        policy,
        source_world=object(),
    )

    assert receipt is not None
    assert receipt["source_refresh"] is True
    assert receipt["prior_source_revision"] == "previous-source-revision"
    assert receipt["source_revision"] == "current-source-revision"
    assert receipt["status"] == "pending"
    assert state[campaign._MORIA_SANCTUARY_FIXED_RESET_ATTEMPT_KEY] == prior_attempt

    attempted = {
        **receipt,
        "status": "attempted",
        "consumed_before_dispatch": True,
    }
    state[campaign._MORIA_SANCTUARY_SOURCE_REFRESH_REVALIDATION_KEY] = attempted
    assert (
        campaign._moria_sanctuary_source_refresh_revalidation_evidence(
            state,
            policy,
            source_world=object(),
        )
        is None
    )


def test_moria_second_reset_can_follow_source_refresh_miss_without_reset_marker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, policy, storage = _fallback_evidence(monkeypatch)
    state.pop(campaign._SANCTUARY_AREA_RESET_RECHECK_KEY, None)
    state[campaign._SANCTUARY_RESOURCE_ATTEMPTS_KEY][
        campaign._MORIA_SANCTUARY_FIXED_RESET_POLICY_ID
    ] = {
        "boot_id": "boot-1",
        "level": 39,
        "count": 1,
    }
    state[campaign._MORIA_SANCTUARY_SOURCE_REFRESH_REVALIDATION_KEY] = {
        "attempted": False,
        "boot_id": "boot-1",
        "consumed_before_dispatch": True,
        "level": 39,
        "outcome": "no_object",
        "source_mobile_vnum": campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
        "source_object_vnum": campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,
        "source_refresh": True,
        "source_reset_room_vnum": 4064,
        "source_revision": "current-source-revision",
        "status": "closed",
    }

    assert campaign._moria_sanctuary_second_fixed_reset_fallback_ready(
        state,
        policy,
        storage=storage,
        campaign_id=7,
    )


def test_moria_second_source_refresh_revalidation_is_one_shot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, policy, _storage = _fallback_evidence(monkeypatch)
    state[campaign._MORIA_SANCTUARY_SOURCE_REFRESH_REVALIDATION_KEY] = {
        "attempted": False,
        "boot_id": "boot-1",
        "consumed_before_dispatch": True,
        "level": 39,
        "outcome": "no_object",
        "source_mobile_vnum": campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
        "source_object_vnum": campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,
        "source_refresh": True,
        "source_reset_room_vnum": 4064,
        "source_revision": "current-source-revision",
        "status": "closed",
    }
    state[campaign._MORIA_SANCTUARY_SECOND_FIXED_RESET_ATTEMPT_KEY] = {
        "boot_id": "boot-1",
        "level": 39,
        "prior_run_id": 201,
        "prior_segment_id": 21,
        "source_mobile_vnum": campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
        "source_object_vnum": campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,
        "source_reset_room_vnum": 4071,
        "source_revision": "previous-source-revision",
        "status": "attempted",
    }
    monkeypatch.setattr(
        campaign,
        "_moria_sanctuary_second_fixed_reset_current_source_audit",
        lambda _state, *, source_world: True,
    )

    receipt = campaign._moria_sanctuary_second_source_refresh_revalidation_evidence(
        state,
        policy,
        source_world=object(),
    )

    assert receipt is not None
    assert receipt["source_reset_room_vnum"] == 4071
    assert receipt["prior_source_revision"] == "previous-source-revision"
    assert receipt["status"] == "pending"

    state[campaign._MORIA_SANCTUARY_SECOND_SOURCE_REFRESH_REVALIDATION_KEY] = {
        **receipt,
        "consumed_before_dispatch": True,
        "status": "attempted",
    }
    assert (
        campaign._moria_sanctuary_second_source_refresh_revalidation_evidence(
            state,
            policy,
            source_world=object(),
        )
        is None
    )


def test_moria_second_source_refresh_accepts_historical_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, policy, _storage = _fallback_evidence(monkeypatch)
    state[campaign._MORIA_SANCTUARY_SOURCE_REFRESH_REVALIDATION_KEY] = {
        "attempted": False,
        "boot_id": "boot-1",
        "consumed_before_dispatch": True,
        "level": 39,
        "outcome": "no_object",
        "source_mobile_vnum": campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
        "source_object_vnum": campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,
        "source_refresh": True,
        "source_reset_room_vnum": 4064,
        "source_revision": "current-source-revision",
        "status": "closed",
    }
    state[campaign._MORIA_SANCTUARY_SECOND_FIXED_RESET_ATTEMPT_KEY] = {
        "boot_id": "older-boot",
        "level": 38,
        "prior_run_id": 201,
        "prior_segment_id": 21,
        "source_mobile_vnum": campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
        "source_object_vnum": campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,
        "source_reset_room_vnum": 4071,
        "source_revision": "previous-source-revision",
        "status": "succeeded",
    }
    monkeypatch.setattr(
        campaign,
        "_moria_sanctuary_second_fixed_reset_current_source_audit",
        lambda _state, *, source_world: True,
    )

    receipt = campaign._moria_sanctuary_second_source_refresh_revalidation_evidence(
        state,
        policy,
        source_world=object(),
    )

    assert receipt is not None
    assert receipt["boot_id"] == "boot-1"
    assert receipt["level"] == 39
    assert receipt["prior_source_revision"] == "previous-source-revision"
    assert receipt["prior_run_id"] == 201
    assert receipt["prior_segment_id"] == 21


def test_moria_no_flight_abort_can_be_revalidated_once_after_flight_is_repaired(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, policy, base_storage = _fallback_evidence(monkeypatch)
    prior_attempt = {
        "boot_id": "boot-1",
        "level": 39,
        "source_revision": "previous-source-revision",
        "status": "attempted",
        "source_mobile_vnum": campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
        "source_object_vnum": campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,
        "source_reset_room_vnum": 4064,
    }
    state[campaign._MORIA_SANCTUARY_FIXED_RESET_ATTEMPT_KEY] = prior_attempt
    state["affects"] = [[{"name": "fly", "duration": "17"}]]
    snapshot = {
        "level": 39,
        "world_boot_id": "boot-1",
        campaign._SOURCE_REVISION_KEY: "previous-source-revision",
        "room_vnum": "3054",
        "dead": False,
        "in_combat": False,
        "xp": 12345,
        "campaign_xp_loss_total": 0,
        "affects": [],
        campaign._MORIA_SANCTUARY_FIXED_RESET_ATTEMPT_KEY: prior_attempt,
    }
    end = {
        **snapshot,
        "fastwalk_route": "moria",
        "fastwalk_abort_reason": "field route requires active fly or levitation",
    }
    segment = {
        "id": 44,
        "run_id": 101,
        "phase": campaign._MORIA_SANCTUARY_FIXED_RESET_POLICY_ID,
        "status": "success",
        "finished_at": "finished",
        "start_state_json": json.dumps(snapshot),
        "end_state_json": json.dumps(end),
    }
    summary = {
        "run": {"id": 101},
        "outcomes": {
            "execution": "success",
            "objective": "not_achieved",
            "safety": "safe",
        },
        "progress": {
            "experience": {"change": 0},
            "confirmed_kills": [],
        },
    }
    sqlite_connection = sqlite3.connect(":memory:")
    sqlite_connection.row_factory = sqlite3.Row
    moria_segment_row = sqlite_connection.execute(
        "SELECT ? AS id, ? AS run_id, ? AS phase, ? AS status, "
        "? AS finished_at, ? AS start_state_json, ? AS end_state_json",
        (
            segment["id"],
            segment["run_id"],
            segment["phase"],
            segment["status"],
            segment["finished_at"],
            segment["start_state_json"],
            segment["end_state_json"],
        ),
    ).fetchone()
    assert isinstance(moria_segment_row, sqlite3.Row)
    storage = _RecoveryEvidenceStorage(
        base_storage.segment,
        base_storage.summary,
        moria_segment=moria_segment_row,
        moria_summary=summary,
    )

    evidence = campaign._moria_sanctuary_fixed_reset_preflight_revalidation_evidence(
        state,
        policy,
        storage=storage,
        campaign_id=7,
    )

    assert evidence == {
        "boot_id": "boot-1",
        "level": 39,
        "source_revision": "current-source-revision",
        "prior_source_revision": "previous-source-revision",
        "prior_run_id": 101,
        "prior_segment_id": 44,
        "source_mobile_vnum": campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
        "source_object_vnum": campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,
        "source_reset_room_vnum": 4064,
        "reason": "prior exact Moria route stopped at the healer only because flight was absent",
    }

    state[campaign._MORIA_SANCTUARY_FIXED_RESET_REVALIDATION_KEY] = {
        **evidence,
        "status": "attempted",
    }
    assert campaign._moria_sanctuary_fixed_reset_preflight_revalidation_evidence(
        state,
        policy,
        storage=storage,
        campaign_id=7,
    ) is None


@pytest.mark.parametrize(
    ("current_flight", "end_changes"),
    [
        (False, {}),
        (True, {"fastwalk_abort_reason": "different route failure"}),
        (True, {"xp": 12346}),
    ],
)
def test_moria_preflight_revalidation_rejects_changed_flight_abort_evidence(
    monkeypatch: pytest.MonkeyPatch,
    current_flight: bool,
    end_changes: dict[str, Any],
) -> None:
    state, policy, base_storage = _fallback_evidence(monkeypatch)
    attempt = {
        "boot_id": "boot-1",
        "level": 39,
        "source_revision": "previous-source-revision",
        "status": "attempted",
        "source_mobile_vnum": campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
        "source_object_vnum": campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,
        "source_reset_room_vnum": 4064,
    }
    state[campaign._MORIA_SANCTUARY_FIXED_RESET_ATTEMPT_KEY] = attempt
    if current_flight:
        state["affects"] = [[{"name": "fly", "duration": "17"}]]
    snapshot = {
        "level": 39,
        "world_boot_id": "boot-1",
        campaign._SOURCE_REVISION_KEY: "previous-source-revision",
        "room_vnum": "3054",
        "dead": False,
        "in_combat": False,
        "xp": 12345,
        "campaign_xp_loss_total": 0,
        "affects": [],
        campaign._MORIA_SANCTUARY_FIXED_RESET_ATTEMPT_KEY: attempt,
    }
    end = {
        **snapshot,
        "fastwalk_route": "moria",
        "fastwalk_abort_reason": "field route requires active fly or levitation",
        **end_changes,
    }
    segment = {
        "id": 44,
        "run_id": 101,
        "phase": campaign._MORIA_SANCTUARY_FIXED_RESET_POLICY_ID,
        "status": "success",
        "finished_at": "finished",
        "start_state_json": json.dumps(snapshot),
        "end_state_json": json.dumps(end),
    }
    summary = {
        "run": {"id": 101},
        "outcomes": {
            "execution": "success",
            "objective": "not_achieved",
            "safety": "safe",
        },
        "progress": {
            "experience": {"change": 0},
            "confirmed_kills": [],
        },
    }
    storage = _RecoveryEvidenceStorage(
        base_storage.segment,
        base_storage.summary,
        moria_segment=segment,
        moria_summary=summary,
    )

    assert campaign._moria_sanctuary_fixed_reset_preflight_revalidation_evidence(
        state,
        policy,
        storage=storage,
        campaign_id=7,
    ) is None


def test_frontier_reserve_evidence_requires_sanctuary_to_change_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = SimpleNamespace(
        target="The Astral Guardian",
        mobile_vnum=1900,
        room_vnum=1906,
    )
    state = {
        "level": 39,
        "world_boot_id": "boot-1",
        campaign._SOURCE_REVISION_KEY: "source-1",
    }
    calls: list[dict[str, Any]] = []

    def select(_candidates: Any, **kwargs: Any) -> Any:
        calls.append(kwargs)
        return candidate if campaign._state_has_sanctuary_reserve(kwargs["state"]) else None

    monkeypatch.setattr(
        campaign, "_select_source_ranked_hunt_candidate", select
    )
    monkeypatch.setattr(
        campaign,
        "_source_ranked_candidate_requires_sanctuary_for_state",
        lambda *_args, **_kwargs: True,
    )
    monkeypatch.setattr(
        campaign,
        "_source_ranked_policy_id",
        lambda *_args, **_kwargs: "source-ranked-hunt-astral-1900-1906-39",
    )

    marker = campaign._source_ranked_sanctuary_frontier_reserve_evidence(
        state,
        (candidate,),
        selection_kwargs={"state": state, "character_level": 39},
    )

    assert marker is not None
    assert marker["target_policy_id"] == "source-ranked-hunt-astral-1900-1906-39"
    assert len(calls) == 2
    assert not campaign._state_has_sanctuary_reserve(calls[0]["state"])
    assert campaign._state_has_sanctuary_reserve(calls[1]["state"])


def test_frontier_reserve_ignores_stale_plain_target_in_widened_pool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plain = SimpleNamespace(target="Athena", mobile_vnum=907, room_vnum=925)
    protected = SimpleNamespace(
        target="The Astral Guardian", mobile_vnum=1900, room_vnum=1906
    )
    state = {
        "level": 39,
        "world_boot_id": "boot-1",
        campaign._SOURCE_REVISION_KEY: "source-1",
    }

    monkeypatch.setattr(
        campaign,
        "_source_ranked_candidate_requires_sanctuary_for_state",
        lambda candidate, *_args, **_kwargs: candidate is protected,
    )
    candidates = campaign._source_ranked_sanctuary_frontier_candidates(
        (plain,),
        (plain, protected),
        preserve_sanctuary_reserve=True,
        state=state,
        character_level=39,
        source_world=None,
        allow_unarmed_post_loss_aggressive_probe=False,
    )

    def select(pool: Any, **kwargs: Any) -> Any:
        if protected in pool and campaign._state_has_sanctuary_reserve(
            kwargs["state"]
        ):
            return protected
        if plain in pool:
            return plain
        return None

    monkeypatch.setattr(
        campaign, "_select_source_ranked_hunt_candidate", select
    )
    monkeypatch.setattr(
        campaign,
        "_source_ranked_policy_id",
        lambda candidate, **_kwargs: (
            "source-ranked-hunt-astral-1900-1906-39"
            if candidate is protected
            else "source-ranked-hunt-olympus-907-925-39"
        ),
    )
    marker = campaign._source_ranked_sanctuary_frontier_reserve_evidence(
        state,
        candidates,
        selection_kwargs={"state": state, "character_level": 39},
    )

    assert marker is not None
    assert marker["status"] == "needed"
    assert marker["target"] == "The Astral Guardian"


def test_frontier_reserve_treats_deferred_sanctuary_pick_as_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = SimpleNamespace(
        target="Athena",
        mobile_vnum=1907,
        room_vnum=925,
    )
    state = {
        "level": 39,
        "world_boot_id": "boot-1",
        campaign._SOURCE_REVISION_KEY: "source-1",
    }
    calls: list[dict[str, Any]] = []

    def select(_candidates: Any, **kwargs: Any) -> Any:
        calls.append(kwargs)
        return candidate

    monkeypatch.setattr(
        campaign, "_select_source_ranked_hunt_candidate", select
    )
    monkeypatch.setattr(
        campaign,
        "_source_ranked_candidate_requires_sanctuary_for_state",
        lambda *_args, **_kwargs: True,
    )
    monkeypatch.setattr(
        campaign,
        "_source_ranked_policy_id",
        lambda *_args, **_kwargs: "source-ranked-hunt-olympus-907-925-39",
    )

    marker = campaign._source_ranked_sanctuary_frontier_reserve_evidence(
        state,
        (candidate,),
        selection_kwargs={"state": state, "character_level": 39},
        defer_sanctuary_required_candidate=True,
        deferred_candidate=candidate,
    )

    assert marker is not None
    assert marker["status"] == "needed"
    assert marker["target"] == "Athena"
    assert len(calls) == 1
    assert campaign._state_has_sanctuary_reserve(calls[0]["state"])


def test_moria_fallback_accepts_fresh_reserve_frontier_without_xp_loss(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, policy, storage = _fallback_evidence(monkeypatch)
    state.pop("campaign_protection_recovery_required")
    state[campaign._SANCTUARY_FRONTIER_RESERVE_KEY] = {
        "schema_version": 1,
        "status": "needed",
        "boot_id": "boot-1",
        "level": 39,
        "source_revision": "current-source-revision",
        "target_policy_id": "source-ranked-hunt-astral-1900-1906-39",
        "target": "The Astral Guardian",
        "mobile_vnum": 1900,
        "room_vnum": 1906,
    }

    assert not campaign._protection_recovery_required(state)
    assert campaign._source_ranked_sanctuary_frontier_reserve_needed(state)
    assert campaign._moria_sanctuary_fixed_reset_fallback_ready(
        state, policy, storage=storage, campaign_id=7
    )


def test_sanctuary_reserve_marker_must_match_fresh_frontier_diagnosis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, _policy, _storage = _fallback_evidence(monkeypatch)
    state.pop("campaign_protection_recovery_required")
    state[campaign._SANCTUARY_FRONTIER_RESERVE_KEY] = {
        "schema_version": 1,
        "status": "needed",
        "boot_id": "boot-1",
        "level": 39,
        "source_revision": "current-source-revision",
        "target_policy_id": "source-ranked-hunt-astral-1900-1906-39",
        "target": "The Astral Guardian",
        "mobile_vnum": 1900,
        "room_vnum": 1906,
    }
    state[campaign._SOURCE_RANKED_FRONTIER_DIAGNOSIS_KEY] = {
        "boot_id": "boot-1",
        "level": 39,
        "diagnosis_revision": campaign._SOURCE_RANKED_FRONTIER_DIAGNOSIS_REVISION,
        "source_revision": "current-source-revision",
        "sanctuary_required_candidates": [],
    }

    assert not campaign._source_ranked_sanctuary_frontier_reserve_needed(state)


def test_sanctuary_reserve_marker_accepts_only_its_fresh_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, _policy, _storage = _fallback_evidence(monkeypatch)
    state[campaign._SANCTUARY_FRONTIER_RESERVE_KEY] = {
        "schema_version": 1,
        "status": "needed",
        "boot_id": "boot-1",
        "level": 39,
        "source_revision": "current-source-revision",
        "target_policy_id": "source-ranked-hunt-astral-1900-1906-39",
        "target": "The Astral Guardian",
        "mobile_vnum": 1900,
        "room_vnum": 1906,
    }
    state[campaign._SOURCE_RANKED_FRONTIER_DIAGNOSIS_KEY] = {
        "boot_id": "boot-1",
        "level": 39,
        "diagnosis_revision": campaign._SOURCE_RANKED_FRONTIER_DIAGNOSIS_REVISION,
        "source_revision": "current-source-revision",
        "sanctuary_required_candidates": [
            {
                "policy_id": "source-ranked-hunt-astral-1900-1906-39",
                "mobile_vnum": 1900,
                "room_vnum": 1906,
                "same_boot_status": "fresh",
                "same_boot_loss_count": 0,
                "same_boot_blockers": [
                    "does not pass unprotected fallback source gates"
                ],
            }
        ],
    }

    assert campaign._source_ranked_sanctuary_frontier_reserve_needed(state)


def test_moria_frontier_refill_can_use_distinct_reset_after_prior_potion_was_used(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, policy, storage = _fallback_evidence(monkeypatch)
    state.pop("campaign_protection_recovery_required")
    state["campaign_research_results"][
        campaign._SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
    ] = {
        "boot_id": "boot-1",
        "required_object_acquired": True,
    }
    state[campaign._SANCTUARY_FRONTIER_RESERVE_KEY] = {
        "schema_version": 1,
        "status": "needed",
        "boot_id": "boot-1",
        "level": 39,
        "source_revision": "current-source-revision",
        "target_policy_id": "source-ranked-hunt-astral-1900-1906-39",
        "target": "The Astral Guardian",
        "mobile_vnum": 1900,
        "room_vnum": 1906,
    }

    assert campaign._moria_sanctuary_frontier_refill_ready(
        state, policy, storage=storage, campaign_id=7
    )

    state[campaign._SANCTUARY_RESOURCE_ATTEMPTS_KEY][
        campaign._MORIA_SANCTUARY_FIXED_RESET_POLICY_ID
    ] = {"boot_id": "boot-1", "level": 39, "count": 1}
    assert not campaign._moria_sanctuary_frontier_refill_ready(
        state, policy, storage=storage, campaign_id=7
    )


def test_moria_fallback_rejects_stale_reserve_frontier_without_xp_loss(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, policy, storage = _fallback_evidence(monkeypatch)
    state.pop("campaign_protection_recovery_required")
    state[campaign._SANCTUARY_FRONTIER_RESERVE_KEY] = {
        "schema_version": 1,
        "status": "needed",
        "boot_id": "old-boot",
        "level": 39,
        "source_revision": "current-source-revision",
        "target_policy_id": "source-ranked-hunt-astral-1900-1906-39",
        "target": "The Astral Guardian",
        "mobile_vnum": 1900,
        "room_vnum": 1906,
    }

    assert not campaign._source_ranked_sanctuary_frontier_reserve_needed(state)
    assert not campaign._moria_sanctuary_fixed_reset_fallback_ready(
        state, policy, storage=storage, campaign_id=7
    )


def test_moria_fixed_reset_stop_cannot_expand_into_a_where_sweep() -> None:
    (stop,) = campaign._moria_sanctuary_fixed_reset_stops()

    assert stop.source_mobile_vnum == 4055
    assert stop.source_reset_room_vnum == "4064"
    assert stop.source_loot_object_vnums == (4050,)
    assert stop.required_items == ("purple potion",)
    assert stop.route == ("east", "north", "north", "east", "south", "down")
    assert stop.where_target is None
    assert stop.where_source_mobile_vnum is None
    assert stop.where_location_routes == ()
    assert stop.where_relocation_routes == ()
    assert stop.actions == ()
    assert stop.maximum_where_relocations == 0


def test_moria_locator_revalidation_uses_only_the_audited_bounded_search() -> None:
    (stop,) = campaign._moria_sanctuary_fixed_reset_locator_stops()

    assert stop.source_mobile_vnum == campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM
    assert stop.source_reset_room_vnum == "4064"
    assert stop.source_loot_object_vnums == (
        campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,
    )
    assert stop.required_items == ("purple potion",)
    assert stop.where_target == "large hobgoblin"
    assert stop.where_source_mobile_vnum == campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM
    assert stop.actions == ("where hobgoblin",)
    assert stop.maximum_where_relocations == 8
    assert stop.abort_if_where_target_absent is True
    assert stop.abort_if_where_location_unknown is True
    assert stop.route_gate_source_mobile_vnums == (4053, 4056, 4050)
    assert stop.route_gate_room_vnums == ("4058", "4057", "4062")
    assert stop.route_gate_requires_locator_target is True


def test_moria_locator_dispatch_requires_its_exact_consumed_receipt() -> None:
    state = {
        "world_boot_id": "boot-1",
        campaign._SOURCE_REVISION_KEY: "source-1",
        campaign._MORIA_SANCTUARY_FIXED_RESET_LOCATOR_REVALIDATION_KEY: {
            "status": "attempted",
            "consumed_before_dispatch": True,
            "boot_id": "boot-1",
            "level": 39,
            "source_revision": "source-1",
            "source_mobile_vnum": campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
            "source_object_vnum": campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,
            "source_reset_room_vnum": 4064,
            "prior_run_id": 101,
            "prior_segment_id": 44,
        },
    }

    assert campaign._moria_sanctuary_fixed_reset_locator_revalidation_requested(
        state,
        policy_id=campaign._MORIA_SANCTUARY_FIXED_RESET_POLICY_ID,
        character_level=39,
    )
    assert not campaign._moria_sanctuary_fixed_reset_locator_revalidation_requested(
        state,
        policy_id=campaign._MORIA_SANCTUARY_SECOND_FIXED_RESET_POLICY_ID,
        character_level=39,
    )
    state[campaign._MORIA_SANCTUARY_FIXED_RESET_LOCATOR_REVALIDATION_KEY][
        "consumed_before_dispatch"
    ] = False
    assert not campaign._moria_sanctuary_fixed_reset_locator_revalidation_requested(
        state,
        policy_id=campaign._MORIA_SANCTUARY_FIXED_RESET_POLICY_ID,
        character_level=39,
    )


def test_moria_locator_receipt_survives_campaign_state_merge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, policy, storage = _locator_revalidation_evidence(monkeypatch)
    marker = {
        "status": "attempted",
        "consumed_before_dispatch": True,
        "boot_id": "boot-1",
        "level": 39,
        "source_revision": "current-source-revision",
        "source_mobile_vnum": campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
        "source_object_vnum": campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,
        "source_reset_room_vnum": 4064,
        "prior_run_id": 101,
        "prior_segment_id": 44,
    }
    previous = {
        **state,
        campaign._MORIA_SANCTUARY_FIXED_RESET_LOCATOR_REVALIDATION_KEY: marker,
    }

    merged = campaign._campaign_segment_end_state(
        previous,
        state,
        execution="source-ranked-hunt",
        policy_id=campaign._MORIA_SANCTUARY_FIXED_RESET_POLICY_ID,
    )

    assert (
        merged[campaign._MORIA_SANCTUARY_FIXED_RESET_LOCATOR_REVALIDATION_KEY]
        == marker
    )
    assert campaign._moria_sanctuary_fixed_reset_locator_revalidation_evidence(
        merged,
        policy,
        storage=storage,
        campaign_id=7,
    ) is None


def test_moria_second_reset_requires_exhausted_first_reset_and_fresh_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, policy, storage = _fallback_evidence(monkeypatch)
    state[campaign._SANCTUARY_RESOURCE_ATTEMPTS_KEY][
        campaign._MORIA_SANCTUARY_FIXED_RESET_POLICY_ID
    ] = {
        "boot_id": "boot-1",
        "level": 39,
        "count": 2,
    }
    state["campaign_research_results"][
        campaign._MORIA_SANCTUARY_FIXED_RESET_POLICY_ID
    ] = {
        "boot_id": "boot-1",
        "level": 39,
        "fatal_failure": True,
        "route_hazard": campaign._SANCTUARY_RESOURCE_EXHAUSTED_HAZARD,
    }

    assert campaign._moria_sanctuary_second_fixed_reset_fallback_ready(
        state, policy, storage=storage, campaign_id=7
    )

    state[campaign._SANCTUARY_RESOURCE_ATTEMPTS_KEY][
        campaign._MORIA_SANCTUARY_SECOND_FIXED_RESET_POLICY_ID
    ] = {"boot_id": "boot-1", "level": 39, "count": 1}
    assert not campaign._moria_sanctuary_second_fixed_reset_fallback_ready(
        state, policy, storage=storage, campaign_id=7
    )


def test_moria_room_4071_refill_can_use_one_later_reset_entitlement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, _policy, _storage = _fallback_evidence(monkeypatch)
    state[campaign._MORIA_SANCTUARY_SECOND_FIXED_RESET_ATTEMPT_KEY] = {
        "boot_id": "boot-1",
        "level": 39,
        "source_revision": "current-source-revision",
        "source_mobile_vnum": campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
        "source_reset_room_vnum": 4071,
        "source_object_vnum": campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,
        "status": "attempted",
        campaign._MORIA_SANCTUARY_SECOND_FIXED_RESET_REACQUISITION_KEY: True,
    }
    state["campaign_research_results"][
        campaign._MORIA_SANCTUARY_SECOND_FIXED_RESET_POLICY_ID
    ] = {
        "boot_id": "boot-1",
        "level": 39,
        "observed": True,
        "required_object_acquired": True,
        "completed_kill": False,
        "viable": True,
        "required_object_vnums": [campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM],
    }
    state[campaign._SOURCE_CAPACITY_RESET_WAIT_KEY] = {
        "boot_id": "boot-1",
        "consumed": False,
        "reason": "automatic area reset wait completed",
    }

    assert not campaign._moria_sanctuary_second_fixed_reset_reacquisition_allowed(
        state
    )
    assert campaign._moria_sanctuary_second_fixed_reset_reacquisition_allowed(
        state,
        allow_post_reset=True,
    )

    state[campaign._SOURCE_CAPACITY_RESET_WAIT_KEY]["consumed"] = True
    assert not campaign._moria_sanctuary_second_fixed_reset_reacquisition_allowed(
        state,
        allow_post_reset=True,
    )


def test_moria_room_4071_source_refresh_opens_one_reacquisition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, _policy, _storage = _fallback_evidence(monkeypatch)
    state[campaign._MORIA_SANCTUARY_SECOND_SOURCE_REFRESH_REVALIDATION_KEY] = {
        "attempted": False,
        "boot_id": "boot-1",
        "consumed_before_dispatch": True,
        "level": 39,
        "outcome": "required_object_acquired",
        "prior_run_id": 18222,
        "prior_segment_id": 17662,
        "source_mobile_vnum": campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
        "source_object_vnum": campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,
        "source_refresh": True,
        "source_reset_room_vnum": 4071,
        "source_revision": "current-source-revision",
        "status": "succeeded",
    }
    assert campaign._moria_sanctuary_second_fixed_reset_reacquisition_allowed(
        state
    )

    state[campaign._MORIA_SANCTUARY_SECOND_FIXED_RESET_ATTEMPT_KEY] = {
        "boot_id": "boot-1",
        "level": 39,
        "source_mobile_vnum": campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
        "source_object_vnum": campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,
        "source_reset_room_vnum": 4071,
        "source_revision": "current-source-revision",
        "status": "attempted",
        "dispatch_started": True,
        campaign._MORIA_SANCTUARY_SECOND_FIXED_RESET_REACQUISITION_KEY: True,
    }
    assert not campaign._moria_sanctuary_second_fixed_reset_reacquisition_allowed(
        state
    )


def test_moria_4071_absence_can_retry_with_sanctuary_staff_and_no_purple(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, _policy, _storage = _fallback_evidence(monkeypatch)
    state["inventory"] = [[{"short_desc": "a red dragonorb"}]]
    state["campaign_source_resource_reserves"] = {
        "sanctuary": {
            "charges_remaining": 10,
            "mode": "staff",
            "object_description": "red dragonorb",
        }
    }
    state["verified_combat_pouch_potions"] = {}
    state["combat_pouch_potions"] = {}
    state[campaign._MORIA_SANCTUARY_SECOND_SOURCE_REFRESH_REVALIDATION_KEY] = {
        "attempted": False,
        "boot_id": "boot-1",
        "consumed_before_dispatch": True,
        "level": 39,
        "outcome": "required_object_acquired",
        "prior_run_id": 18222,
        "prior_segment_id": 17662,
        "source_mobile_vnum": campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
        "source_object_vnum": campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,
        "source_refresh": True,
        "source_reset_room_vnum": 4071,
        "source_revision": "current-source-revision",
        "status": "succeeded",
    }
    state[campaign._MORIA_SANCTUARY_SECOND_FIXED_RESET_ATTEMPT_KEY] = {
        "boot_id": "boot-1",
        "dispatch_started": True,
        "level": 39,
        "source_mobile_vnum": campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
        "source_object_vnum": campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,
        "source_reset_room_vnum": 4071,
        "source_revision": "current-source-revision",
        "status": "attempted",
        campaign._MORIA_SANCTUARY_SECOND_FIXED_RESET_REACQUISITION_KEY: True,
    }
    state["campaign_research_results"][
        campaign._MORIA_SANCTUARY_SECOND_FIXED_RESET_POLICY_ID
    ] = {
        "boot_id": "boot-1",
        "level": 39,
        "observed": False,
        "required_object_acquired": True,
        "viable": False,
    }

    assert campaign._state_has_sanctuary_reserve(state)
    assert not campaign._state_has_blindness_recovery_reserve(state)
    assert campaign._moria_sanctuary_second_fixed_reset_reacquisition_allowed(
        state
    )

    state[campaign._MORIA_SANCTUARY_SECOND_FIXED_RESET_ATTEMPT_KEY][
        campaign._MORIA_SANCTUARY_SECOND_FIXED_RESET_RETRY_KEY
    ] = True
    assert not campaign._moria_sanctuary_second_fixed_reset_reacquisition_allowed(
        state
    )


def test_moria_post_reset_dispatch_consumes_capacity_entitlement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, _policy, _storage = _fallback_evidence(monkeypatch)
    state[campaign._SOURCE_CAPACITY_RESET_WAIT_KEY] = {
        "boot_id": "boot-1",
        "consumed": False,
        "reason": "automatic area reset wait completed",
    }
    candidate = SimpleNamespace(
        area_file="moria.are",
        mobile_vnum=campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
        room_vnum=4071,
        route_origin_recall_index=0,
        source_spawn_limit=2,
        room_spawn_count=1,
        autonomy_rejections=("target reset capacity exceeds one",),
        specials=(),
    )

    campaign._consume_source_capacity_reset_wait(
        state,
        candidate,
        character_level=39,
        source_object_vnums=(campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,),
        allow_exact_moria_capacity=True,
    )

    marker = state[campaign._SOURCE_CAPACITY_RESET_WAIT_KEY]
    assert marker["consumed"] is True
    assert marker["policy_id"] == campaign._source_ranked_policy_id(
        candidate,
        character_level=39,
    )


def test_moria_post_reset_capacity_repair_closes_legacy_unspent_marker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, _policy, _storage = _fallback_evidence(monkeypatch)
    state[campaign._SOURCE_CAPACITY_RESET_WAIT_KEY] = {
        "boot_id": "boot-1",
        "consumed": False,
        "reason": "automatic area reset wait completed",
    }
    end_state = {
        "world_boot_id": "boot-1",
        campaign._MORIA_SANCTUARY_SECOND_FIXED_RESET_ATTEMPT_KEY: {
            "reacquisition_after_area_reset": True,
        },
    }
    repaired = campaign._repair_moria_post_reset_capacity_entitlement(
        state,
        [
            {
                "id": 99,
                "run_id": 123,
                "phase": campaign._MORIA_SANCTUARY_SECOND_FIXED_RESET_POLICY_ID,
                "status": "success",
                "end_state_json": json.dumps(end_state),
            }
        ],
    )

    marker = repaired[campaign._SOURCE_CAPACITY_RESET_WAIT_KEY]
    assert marker["consumed"] is True
    assert marker["segment_id"] == 99
    assert marker["run_id"] == 123


def test_moria_second_reset_can_refill_a_verified_potion_spent_in_a_lost_hunt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, policy, _ = _fallback_evidence(monkeypatch)
    state[campaign._MORIA_SANCTUARY_FIXED_RESET_ATTEMPT_KEY] = {
        "boot_id": "boot-1",
        "level": 39,
        "source_revision": "current-source-revision",
        "source_mobile_vnum": campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
        "source_reset_room_vnum": 4064,
        "source_object_vnum": campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,
        "status": "attempted",
    }
    state[campaign._SANCTUARY_RESOURCE_ATTEMPTS_KEY].pop(
        campaign._MORIA_SANCTUARY_FIXED_RESET_POLICY_ID, None
    )
    state[campaign._SANCTUARY_RESOURCE_ATTEMPTS_KEY][
        campaign._SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
    ]["count"] = campaign._SANCTUARY_RESOURCE_MAX_ATTEMPTS
    state["campaign_research_results"][
        campaign._MORIA_SANCTUARY_FIXED_RESET_POLICY_ID
    ] = {
        "boot_id": "boot-1",
        "level": 39,
        "required_object_acquired": True,
    }
    state["campaign_fastwalk_sanctuary_consumed_in_combat"] = True
    state["campaign_last_policy"] = "source-ranked-hunt-cyclops-14004-14007-39"
    recovery_result = state["campaign_research_results"][
        campaign._SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
    ]
    recovery_result.pop("absent", None)
    recovery_result["observed"] = True
    recovery_result["viable"] = False

    acquired_state = {
        "world_boot_id": "boot-1",
        "level": 39,
        campaign._SOURCE_REVISION_KEY: "current-source-revision",
        "fastwalk_route": "moria",
        "campaign_fastwalk_target_present_observed": True,
        "campaign_fastwalk_required_object_vnums": [4050],
        "combat_pouch_potions": {"purple": 1},
        "campaign_completed_kills": [{"source_mobile_vnum": 4055}],
    }
    loss_state = {
        "world_boot_id": "boot-1",
        "level": 39,
        campaign._SOURCE_REVISION_KEY: "current-source-revision",
        "campaign_fastwalk_sanctuary_consumed_in_combat": True,
        "combat_pouch_potions": {},
    }
    segments = {
        campaign._MORIA_SANCTUARY_FIXED_RESET_POLICY_ID: {
            "id": 30,
            "phase": campaign._MORIA_SANCTUARY_FIXED_RESET_POLICY_ID,
            "status": "success",
            "finished_at": "finished",
            "run_id": 300,
            "end_state_json": json.dumps(acquired_state),
        },
        state["campaign_last_policy"]: {
            "id": 31,
            "phase": state["campaign_last_policy"],
            "status": "success",
            "finished_at": "finished",
            "run_id": 301,
            "end_state_json": json.dumps(loss_state),
        },
    }
    summaries = {
        300: {
            "outcomes": {
                "execution": "success",
                "objective": "achieved",
                "safety": "safe",
            },
            "progress": {"experience": {"change": 100}},
        },
        301: {
            "outcomes": {
                "execution": "success",
                "objective": "not_achieved",
                "safety": "loss",
            },
            "progress": {"experience": {"change": -475}},
        },
    }
    storage = SimpleNamespace(
        get_latest_campaign_segment_for_phase=lambda _campaign, phase, **_kw: (
            segments.get(phase)
        ),
        get_run_summary=lambda run_id: summaries[run_id],
    )

    assert campaign._moria_sanctuary_first_reserve_spent_after_loss(
        state, storage=storage, campaign_id=7
    )
    assert campaign._moria_sanctuary_second_fixed_reset_fallback_ready(
        state, policy, storage=storage, campaign_id=7
    )

    state["campaign_fastwalk_sanctuary_consumed_in_combat"] = False
    assert not campaign._moria_sanctuary_second_fixed_reset_fallback_ready(
        state, policy, storage=storage, campaign_id=7
    )


def test_moria_deep_hunt_keeps_room_4071_as_an_exact_source_endpoint() -> None:
    stops = campaign.moria_deep_sanctuary_potion_hunt_stops(
        required_potion_count=1
    )

    assert any(
        stop.source_mobile_vnum == campaign._MORIA_SANCTUARY_CARRIER_MOBILE_VNUM
        and stop.route_vnums
        and stop.route_vnums[-1] == "4071"
        and stop.required_items == ("purple potion",)
        and stop.source_loot_object_vnums
        == (campaign._MORIA_SANCTUARY_POTION_OBJECT_VNUM,)
        for stop in stops
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "wrong-room",
        "wrong-target",
        "low-health",
        "changed-xp",
        "changed-xp-loss",
        "unsafe-run",
        "segment-before-recheck",
        "stale-source",
        "repeated-attempt",
    ],
)
def test_moria_sanctuary_fallback_rejects_stale_or_unsafe_evidence(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    state, policy, storage = _fallback_evidence(monkeypatch)
    state = deepcopy(state)
    storage.segment = dict(storage.segment)
    storage.summary = deepcopy(storage.summary)
    end = json.loads(storage.segment["end_state_json"])

    if mutation == "wrong-room":
        end[campaign._SOURCE_ABSENT_SIGHTINGS_KEY][0]["room_vnum"] = "4064"
    elif mutation == "wrong-target":
        end[campaign._SOURCE_ABSENT_SIGHTINGS_KEY][0]["target"] = "waiter"
    elif mutation == "low-health":
        state["hp"] = 839
    elif mutation == "changed-xp":
        end["xp"] += 1
    elif mutation == "changed-xp-loss":
        end["campaign_xp_loss_total"] = 1
    elif mutation == "unsafe-run":
        storage.summary["outcomes"]["safety"] = "loss"
    elif mutation == "segment-before-recheck":
        storage.segment["id"] = 17
    elif mutation == "stale-source":
        state[campaign._SOURCE_REVISION_KEY] = "stale-source"
    elif mutation == "repeated-attempt":
        state[campaign._MORIA_SANCTUARY_FIXED_RESET_ATTEMPT_KEY] = {
            "boot_id": "boot-1",
        }
    storage.segment["end_state_json"] = json.dumps(end)

    assert not campaign._moria_sanctuary_fixed_reset_fallback_ready(
        state, policy, storage=storage, campaign_id=7
    )
