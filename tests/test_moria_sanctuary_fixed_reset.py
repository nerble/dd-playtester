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


def test_moria_sanctuary_fallback_requires_complete_exact_absence_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, policy, storage = _fallback_evidence(monkeypatch)

    assert campaign._moria_sanctuary_fixed_reset_fallback_ready(
        state, policy, storage=storage, campaign_id=7
    )


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
