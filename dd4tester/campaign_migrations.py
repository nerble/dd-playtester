"""Historical campaign checkpoint migrations, isolated from policy selection."""
from __future__ import annotations

import json
from threading import RLock
from typing import Any, Collection

_namespace_lock = RLock()


def refresh_policy_revision(
    state: dict[str, Any],
    *,
    completed_policy_ids: Collection[str] = (),
    recent_segments: Collection[Any] = (),
    recent_checkpoints: Collection[Any] = (),
    helper_namespace: dict[str, Any],
) -> dict[str, Any]:
    """Apply the legacy checkpoint migration using audited campaign helpers."""
    protected = {
        "_namespace_lock",
        "refresh_policy_revision",
        "_refresh_campaign_policy_revision_impl",
    }
    with _namespace_lock:
        globals().update({
            name: value
            for name, value in helper_namespace.items()
            if not name.startswith('__') and name not in protected
        })
        refreshed = _refresh_campaign_policy_revision_impl(
            state,
            completed_policy_ids=completed_policy_ids,
        )
        refreshed = _repair_pounding_weapon_rearm_attempt(
            refreshed,
            recent_segments,
        )
        return _restore_pounding_weapon_rearm_attempt(
            refreshed,
            recent_checkpoints,
        )


def _restore_pounding_weapon_rearm_attempt(
    state: dict[str, Any],
    recent_checkpoints: Collection[Any],
) -> dict[str, Any]:
    """Recover a valid frontier marker lost by an older state merge."""
    marker_key = "campaign_pounding_weapon_rearm_attempt"
    if _rearm_marker_matches_state(state.get(marker_key), state):
        return state

    for raw_checkpoint in reversed(tuple(recent_checkpoints)):
        try:
            checkpoint = dict(raw_checkpoint)
        except (TypeError, ValueError):
            continue
        snapshot = _rearm_segment_state(checkpoint.get("state_json"))
        if snapshot is None:
            continue
        marker = snapshot.get(marker_key)
        if not (
            _rearm_marker_matches_state(marker, snapshot)
            and _rearm_marker_matches_state(marker, state)
        ):
            continue
        updated = dict(state)
        updated[marker_key] = dict(marker)
        return updated

    if marker_key in state:
        updated = dict(state)
        updated.pop(marker_key, None)
        return updated
    return state


def _rearm_marker_matches_state(
    marker: object,
    state: dict[str, Any],
) -> bool:
    if not isinstance(marker, dict) or state.get("campaign_has_weapon") is not True:
        return False
    level = _rearm_integer(state.get("level"))
    try:
        marker_level = _rearm_integer(marker.get("level"))
    except AttributeError:
        return False
    boot_id = str(state.get("world_boot_id") or "")
    source_revision = str(state.get("campaign_source_revision") or "")
    primary = _rearm_weapon_name(state.get("campaign_primary_weapon"))
    return bool(
        level is not None
        and level == marker_level
        and boot_id
        and marker.get("boot_id") == boot_id
        and source_revision
        and marker.get("source_revision") == source_revision
        and primary
        and marker.get("primary_weapon") == primary
    )


def restore_checkpointed_sanctuary_attempts(
    state: dict[str, Any],
    recent_checkpoints: Collection[Any],
) -> dict[str, Any]:
    """Restore reserve-route limits dropped by an older unrelated merge."""
    attempts_key = "campaign_sanctuary_resource_attempts"
    boot_id = str(state.get("world_boot_id") or "")
    level = _rearm_integer(state.get("level"))
    if not boot_id or level is None:
        return state

    reset_marker = state.get("campaign_sanctuary_area_reset_recheck")
    reset_policy_ids: set[str] = set()
    if (
        isinstance(reset_marker, dict)
        and reset_marker.get("boot_id") == boot_id
        and _rearm_integer(reset_marker.get("level")) == level
        and reset_marker.get("status") in {"pending", "attempted"}
    ):
        raw_policy_ids = reset_marker.get("policy_ids")
        if isinstance(raw_policy_ids, (list, tuple, set, frozenset)):
            reset_policy_ids = {str(value) for value in raw_policy_ids}

    results = state.get("campaign_research_results")
    results = results if isinstance(results, dict) else {}
    current_attempts = state.get(attempts_key)
    attempts = dict(current_attempts) if isinstance(current_attempts, dict) else {}
    checkpoint_attempts: dict[str, dict[str, Any]] = {}

    for raw_checkpoint in reversed(tuple(recent_checkpoints)):
        try:
            checkpoint = dict(raw_checkpoint)
        except (TypeError, ValueError):
            continue
        snapshot = _rearm_segment_state(checkpoint.get("state_json"))
        if not (
            isinstance(snapshot, dict)
            and str(snapshot.get("world_boot_id") or "") == boot_id
            and _rearm_integer(snapshot.get("level")) == level
        ):
            continue
        snapshot_results = snapshot.get("campaign_research_results")
        snapshot_results = (
            snapshot_results if isinstance(snapshot_results, dict) else {}
        )
        snapshot_attempts = snapshot.get(attempts_key)
        if not isinstance(snapshot_attempts, dict):
            continue
        for raw_policy_id, raw_record in snapshot_attempts.items():
            policy_id = str(raw_policy_id)
            if not isinstance(raw_record, dict):
                continue
            if (
                raw_record.get("boot_id") != boot_id
                or _rearm_integer(raw_record.get("level")) != level
            ):
                continue
            if policy_id in reset_policy_ids and raw_record.get(
                "area_reset_cycle"
            ) != 1:
                continue
            result = snapshot_results.get(policy_id)
            if (
                isinstance(result, dict)
                and result.get("boot_id") == boot_id
                and result.get("required_object_acquired") is True
            ):
                continue
            try:
                count = max(0, int(raw_record.get("count") or 0))
            except (TypeError, ValueError):
                continue
            existing = checkpoint_attempts.get(policy_id)
            try:
                existing_count = int(existing.get("count") or 0) if existing else -1
            except (TypeError, ValueError):
                existing_count = -1
            if count > existing_count:
                checkpoint_attempts[policy_id] = dict(raw_record)

    restored = False
    for policy_id, checkpoint_record in checkpoint_attempts.items():
        current_result = results.get(policy_id)
        if (
            isinstance(current_result, dict)
            and current_result.get("boot_id") == boot_id
            and current_result.get("required_object_acquired") is True
        ):
            continue
        current_record = attempts.get(policy_id)
        if policy_id in reset_policy_ids:
            if (
                isinstance(current_record, dict)
                and current_record.get("area_reset_cycle") == 1
                and current_record.get("boot_id") == boot_id
                and _rearm_integer(current_record.get("level")) == level
                and current_record.get("area_reset_after_segment_id")
                == checkpoint_record.get("area_reset_after_segment_id")
            ):
                try:
                    current_count = max(
                        0,
                        int(current_record.get("count") or 0),
                    )
                    checkpoint_count = max(
                        0,
                        int(checkpoint_record.get("count") or 0),
                    )
                except (TypeError, ValueError):
                    continue
                if current_count >= checkpoint_count:
                    continue
                attempts[policy_id] = {
                    **checkpoint_record,
                    **current_record,
                    "count": checkpoint_count,
                }
            else:
                attempts[policy_id] = checkpoint_record
            restored = True
            continue
        if isinstance(current_record, dict):
            if (
                current_record.get("boot_id") != boot_id
                or _rearm_integer(current_record.get("level")) != level
            ):
                continue
            if current_record.get("area_reset_cycle") == 1:
                continue
            try:
                current_count = max(0, int(current_record.get("count") or 0))
                checkpoint_count = max(
                    0,
                    int(checkpoint_record.get("count") or 0),
                )
            except (TypeError, ValueError):
                continue
            if current_count >= checkpoint_count:
                continue
            attempts[policy_id] = {
                **checkpoint_record,
                **current_record,
                "count": checkpoint_count,
            }
        else:
            attempts[policy_id] = checkpoint_record
        restored = True

    if not restored:
        return state
    updated = dict(state)
    updated[attempts_key] = attempts
    return updated


def _repair_pounding_weapon_rearm_attempt(
    state: dict[str, Any],
    recent_segments: Collection[Any],
) -> dict[str, Any]:
    """Persist one exact safe rearm-route failure for the current frontier."""
    marker_key = "campaign_pounding_weapon_rearm_attempt"
    for raw_segment in reversed(tuple(recent_segments)):
        try:
            segment = dict(raw_segment)
        except (TypeError, ValueError):
            continue
        error = str(segment.get("error") or "")
        located_route_blocked = (
            "Dave's located room" in error
            and "no source-safe sweep within 22 commands" in error
        )
        located_room_unmapped = (
            "Dave's located room" in error
            and "had no bounded source-reachable room set" in error
        )
        completed_sweep_empty = (
            "Dave was absent from every source room in the single bounded locator sweep"
            in error
        )
        locator_empty = "Dave was absent from the one live locator check" in error
        if (
            segment.get("phase") != "rearm-primary-weapon"
            or segment.get("status") != "failed"
            or segment.get("execution_status") != "failed"
            or segment.get("safety_outcome") != "safe"
            or not (
                located_route_blocked
                or located_room_unmapped
                or completed_sweep_empty
                or locator_empty
            )
            or "returned to the healer without retrying" not in error
        ):
            continue
        try:
            command_count = int(segment.get("command_count") or 0)
            run_id = int(segment.get("run_id"))
            segment_id = int(segment.get("id"))
        except (TypeError, ValueError):
            continue
        if command_count <= 0:
            continue
        start = _rearm_segment_state(segment.get("start_state_json"))
        end = _rearm_segment_state(segment.get("end_state_json"))
        if start is None or end is None:
            continue
        current_level = _rearm_integer(state.get("level"))
        start_level = _rearm_integer(start.get("level"))
        end_level = _rearm_integer(end.get("level"))
        current_xp = _rearm_integer(state.get("xp"))
        start_xp = _rearm_integer(start.get("xp"))
        end_xp = _rearm_integer(end.get("xp"))
        source_revision = str(state.get("campaign_source_revision") or "")
        boot_id = str(state.get("world_boot_id") or "")
        primary = _rearm_weapon_name(state.get("campaign_primary_weapon"))
        if not (
            current_level is not None
            and current_level == start_level == end_level
            and current_xp is not None
            and current_xp == start_xp == end_xp
            and boot_id
            and boot_id
            == start.get("world_boot_id")
            == end.get("world_boot_id")
            and source_revision
            and source_revision
            == start.get("campaign_source_revision")
            == end.get("campaign_source_revision")
            and state.get("campaign_has_weapon") is True
            and start.get("campaign_has_weapon") is True
            and end.get("campaign_has_weapon") is True
            and primary
            and primary
            == _rearm_weapon_name(start.get("campaign_primary_weapon"))
            == _rearm_weapon_name(end.get("campaign_primary_weapon"))
            and state.get("room_vnum") == "3054"
            and end.get("room_vnum") == "3054"
            and state.get("dead") is False
            and start.get("dead") is False
            and end.get("dead") is False
            and state.get("in_combat") is False
            and start.get("in_combat") is False
            and end.get("in_combat") is False
            and start.get("xp_loss_observed") is not True
            and end.get("xp_loss_observed") is not True
            and state.get("xp_loss_observed") is not True
        ):
            continue
        loss_keys = ("xp_loss_total", "campaign_xp_loss_total")
        if any(
            start.get(key) is None
            or start.get(key) != end.get(key)
            or (state.get(key) is not None and state.get(key) != end.get(key))
            for key in loss_keys
        ):
            continue
        if state.get("campaign_xp_loss_observed") is True or any(
            snapshot.get("campaign_xp_loss_observed") is True
            for snapshot in (start, end)
        ):
            continue
        updated = dict(state)
        updated[marker_key] = {
            "level": current_level,
            "observed_xp": current_xp,
            "xp_loss_total": end.get("xp_loss_total"),
            "campaign_xp_loss_total": end.get("campaign_xp_loss_total"),
            "boot_id": boot_id,
            "source_revision": source_revision,
            "primary_weapon": primary,
            "run_id": run_id,
            "segment_id": segment_id,
            "reason": "safe_rearm_route_blocked",
        }
        return updated
    return state


def _rearm_segment_state(value: object) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return None
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _rearm_integer(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _rearm_weapon_name(value: object) -> str:
    return " ".join(str(value or "").casefold().split())


def _refresh_campaign_policy_revision_impl(
    state: dict[str, Any],
    *,
    completed_policy_ids: Collection[str] = (),
) -> dict[str, Any]:
    """Reset stale stall history once when the autonomous policy graph changes."""
    state = _repair_retryable_dynamic_route_hazards(state)
    previous_revision = int(state.get("campaign_policy_revision", 0))
    if previous_revision < _CAMPAIGN_POLICY_REVISION:
        state = _repair_source_ranked_locator_rebase_revalidation(state)
    if previous_revision < _SOURCE_RANKED_UNPROTECTED_HP_OPENER_REVALIDATION_REVISION:
        state = _repair_unprotected_hp_opener_revalidation(state)
    if previous_revision < _FIXED_ROUTE_PROGRAM_REVALIDATION_REVISION:
        policy_id = str(state.get("campaign_last_policy") or "")
        result = _campaign_research_results(state).get(policy_id)
        abort_reason = str(state.get("campaign_fastwalk_abort_reason") or "")
        raw_room_flags = state.get("room_flags")
        room_flags = (
            {str(flag).casefold() for flag in raw_room_flags}
            if isinstance(raw_room_flags, Collection)
            and not isinstance(raw_room_flags, (str, bytes))
            else set()
        )
        raw_locations = state.get("campaign_fastwalk_route_preflight_locations")
        locations = (
            {" ".join(str(value).casefold().split()) for value in raw_locations}
            if isinstance(raw_locations, Collection)
            and not isinstance(raw_locations, (str, bytes))
            else set()
        )
        try:
            hp = int(state.get("hp") or 0)
            retry_attempts = int(
                state.get("campaign_fastwalk_route_preflight_retry_attempts")
                or 0
            )
        except (TypeError, ValueError):
            hp = retry_attempts = 0
        if (
            policy_id
            in {
                _SOURCE_RANKED_SANCTUARY_RESERVE_POLICY.policy_id,
                _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id,
            }
            and isinstance(result, Mapping)
            and result.get("boot_id") == state.get("world_boot_id")
            and result.get("observed") is False
            and result.get("viable") is False
            and result.get("completed_kill") is not True
            and result.get("route_hazard") == abort_reason
            and abort_reason.startswith(_FIXED_ROUTE_DRUNK_PREFLIGHT_PREFIX)
            and abort_reason.endswith(_FIXED_ROUTE_DRUNK_PREFLIGHT_SUFFIX)
            and retry_attempts == 3
            and "the main street" in locations
            and state.get("campaign_fastwalk_route_preflight_hazard_observed")
            is True
            and state.get("campaign_fastwalk_route_hazards") == []
            and not state.get("campaign_objective_kills")
            and not state.get("campaign_fastwalk_required_object_vnums")
            and state.get("campaign_died_during_segment") is False
            and state.get("dead") is not True
            and state.get("xp_loss_observed") is not True
            and state.get("campaign_xp_loss_observed") is not True
            and str(state.get("room_vnum") or "") == "3054"
            and {"healing", "safe"}.issubset(room_flags)
            and state.get("enemies") in (None, [])
            and not state.get("combat_target")
            and state.get("in_combat") is not True
            and state.get("position") in {5, 6, 7}
            and hp > 0
        ):
            # Revision 255 reuses the existing source-bounded transit combat
            # gate for fixed routes. Preserve run 12868 as evidence, but do
            # not let its now-obsolete locator veto suppress the corrected
            # route forever.
            state = dict(state)
            results = dict(_campaign_research_results(state))
            superseded_result = dict(results.pop(policy_id))
            if results:
                state["campaign_research_results"] = results
            else:
                state.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(state.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    state[cooldown_key] = cooldowns
                else:
                    state.pop(cooldown_key, None)
            cleared = [
                str(candidate_id)
                for candidate_id in state.get(
                    _CLEARED_RESEARCH_POLICIES_KEY, ()
                )
                if str(candidate_id) != policy_id
            ]
            if cleared:
                state[_CLEARED_RESEARCH_POLICIES_KEY] = cleared
            else:
                state.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
            state[_FIXED_ROUTE_PROGRAM_REVALIDATION_KEY] = {
                "policy_revision": _FIXED_ROUTE_PROGRAM_REVALIDATION_REVISION,
                "policy_id": policy_id,
                "boot_id": state.get("world_boot_id"),
                "level": _level(state),
                "status": "reopened",
                "source_mobile_vnum": 3064,
                "preflight_locations": sorted(locations),
                "superseded_result": superseded_result,
            }
            state.pop("campaign_last_policy", None)
            for key in (
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
                "campaign_fastwalk_route_preflight_complete",
                "campaign_fastwalk_route_preflight_hazard_observed",
                "campaign_fastwalk_route_preflight_inconclusive",
                "campaign_fastwalk_route_preflight_locations",
                "campaign_fastwalk_route_preflight_retry_attempts",
            ):
                state.pop(key, None)
    if previous_revision < _SANCTUARY_SAFE_LOCATOR_REVALIDATION_REVISION:
        policy_id = str(state.get("campaign_last_policy") or "")
        result = _campaign_research_results(state).get(policy_id)
        predecessor = state.get(_FIXED_ROUTE_PROGRAM_REVALIDATION_KEY)
        protection = state.get(_PROTECTION_RECOVERY_KEY)
        raw_room_flags = state.get("room_flags")
        room_flags = (
            {str(flag).casefold() for flag in raw_room_flags}
            if isinstance(raw_room_flags, Collection)
            and not isinstance(raw_room_flags, (str, bytes))
            else set()
        )
        try:
            hp = int(state.get("hp") or 0)
            relocation_attempts = int(
                state.get("campaign_fastwalk_where_relocation_attempts") or 0
            )
        except (TypeError, ValueError):
            hp = relocation_attempts = 0
        if (
            policy_id
            in {
                _SOURCE_RANKED_SANCTUARY_RESERVE_POLICY.policy_id,
                _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id,
            }
            and _level(state) >= 24
            and isinstance(result, Mapping)
            and result.get("boot_id") == state.get("world_boot_id")
            and result.get("observed") is False
            and result.get("viable") is False
            and result.get("absent") is True
            and result.get("completed_kill") is not True
            and isinstance(predecessor, Mapping)
            and predecessor.get("policy_revision")
            == _FIXED_ROUTE_PROGRAM_REVALIDATION_REVISION
            and predecessor.get("policy_id") == policy_id
            and predecessor.get("boot_id") == state.get("world_boot_id")
            and predecessor.get("level") == _level(state)
            and predecessor.get("status") == "reopened"
            and predecessor.get("source_mobile_vnum") == 3064
            and isinstance(protection, Mapping)
            and protection.get("boot_id") == state.get("world_boot_id")
            and protection.get("level") in {None, _level(state)}
            and not state.get("campaign_fastwalk_abort_reason")
            and state.get("campaign_fastwalk_target_absent") is True
            and state.get("campaign_fastwalk_target_present_observed") is False
            and state.get("campaign_fastwalk_where_area_checks") == []
            and relocation_attempts == 0
            and state.get("campaign_fastwalk_route_hazards") == []
            and state.get("campaign_fastwalk_required_object_vnums") == []
            and state.get("campaign_objective_kills") == []
            and state.get("campaign_died_during_segment") is False
            and state.get("dead") is not True
            and state.get("xp_loss_observed") is not True
            and state.get("campaign_xp_loss_observed") is not True
            and str(state.get("room_vnum") or "") == "3054"
            and {"healing", "safe"}.issubset(room_flags)
            and state.get("enemies") in (None, [])
            and not state.get("combat_target")
            and state.get("in_combat") is not True
            and state.get("position") in {5, 6, 7}
            and hp > 0
        ):
            # Run 12872 proved the corrected fixed route but inspected only
            # room 4064. Reopen that exact no-loss absence once so revision
            # 256 can issue the source-bounded locator and inspect 4063 too.
            state = dict(state)
            results = dict(_campaign_research_results(state))
            superseded_result = dict(results.pop(policy_id))
            if results:
                state["campaign_research_results"] = results
            else:
                state.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(state.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    state[cooldown_key] = cooldowns
                else:
                    state.pop(cooldown_key, None)
            cleared = [
                str(candidate_id)
                for candidate_id in state.get(
                    _CLEARED_RESEARCH_POLICIES_KEY, ()
                )
                if str(candidate_id) != policy_id
            ]
            if cleared:
                state[_CLEARED_RESEARCH_POLICIES_KEY] = cleared
            else:
                state.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
            state[_SANCTUARY_SAFE_LOCATOR_REVALIDATION_KEY] = {
                "policy_revision": (
                    _SANCTUARY_SAFE_LOCATOR_REVALIDATION_REVISION
                ),
                "policy_id": policy_id,
                "boot_id": state.get("world_boot_id"),
                "level": _level(state),
                "status": "reopened",
                "source_mobile_vnum": _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
                "safe_endpoint_room_vnums": [4064, 4063],
                "superseded_result": superseded_result,
            }
            state.pop("campaign_last_policy", None)
            for key in (
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
                "campaign_fastwalk_where_area_checks",
                "campaign_fastwalk_where_relocation_attempts",
            ):
                state.pop(key, None)
    if (
        previous_revision
        < _SANCTUARY_COMBAT_ONLY_TRANSIT_REVALIDATION_REVISION
    ):
        policy_id = str(state.get("campaign_last_policy") or "")
        result = _campaign_research_results(state).get(policy_id)
        predecessor = state.get(_SANCTUARY_SAFE_LOCATOR_REVALIDATION_KEY)
        protection = state.get(_PROTECTION_RECOVERY_KEY)
        attempts = state.get(_SANCTUARY_RESOURCE_ATTEMPTS_KEY)
        attempt = attempts.get(policy_id) if isinstance(attempts, Mapping) else None
        where_checks = state.get("campaign_fastwalk_where_area_checks")
        raw_room_flags = state.get("room_flags")
        room_flags = (
            {str(flag).casefold() for flag in raw_room_flags}
            if isinstance(raw_room_flags, Collection)
            and not isinstance(raw_room_flags, (str, bytes))
            else set()
        )
        try:
            hp = int(state.get("hp") or 0)
            attempt_count = int(attempt.get("count") or 0)
        except (AttributeError, TypeError, ValueError):
            hp = attempt_count = 0
        expected_where_check = {
            "area_file": "moria.are",
            "result": "present",
            "room_vnum": "4014",
            "scope": "current_area",
            "source_mobile_vnum": _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
            "target": "large hobgoblin",
        }
        if (
            policy_id
            in {
                _SOURCE_RANKED_SANCTUARY_RESERVE_POLICY.policy_id,
                _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id,
            }
            and _level(state) >= 23
            and isinstance(result, Mapping)
            and result.get("boot_id") == state.get("world_boot_id")
            and result.get("level") == _level(state)
            and result.get("observed") is True
            and result.get("viable") is False
            and result.get("completed_kill") is False
            and result.get("fatal_failure") is True
            and result.get("route_hazard")
            == "sanctuary resource route exhausted after 2 failed attempts"
            and result.get("required_object_acquired") is not True
            and isinstance(predecessor, Mapping)
            and predecessor.get("policy_revision")
            == _SANCTUARY_SAFE_LOCATOR_REVALIDATION_REVISION
            and predecessor.get("policy_id") == policy_id
            and predecessor.get("boot_id") == state.get("world_boot_id")
            and predecessor.get("level") == _level(state)
            and predecessor.get("status") == "reopened"
            and predecessor.get("source_mobile_vnum")
            == _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM
            and predecessor.get("safe_endpoint_room_vnums") == [4064, 4063]
            and isinstance(protection, Mapping)
            and protection.get("boot_id") == state.get("world_boot_id")
            and protection.get("level") in {None, _level(state)}
            and isinstance(attempt, Mapping)
            and attempt.get("boot_id") == state.get("world_boot_id")
            and attempt.get("level") == _level(state)
            and attempt_count >= _SANCTUARY_RESOURCE_MAX_ATTEMPTS
            and state.get("campaign_fastwalk_abort_reason")
            == _SANCTUARY_COMBAT_ONLY_TRANSIT_ABORT_REASON
            and state.get("campaign_fastwalk_target_absent") is False
            and state.get("campaign_fastwalk_target_present_observed") is True
            and where_checks == [expected_where_check]
            and state.get("campaign_fastwalk_where_relocation_attempts") == 1
            and state.get("campaign_fastwalk_route_hazards") == []
            and state.get("campaign_fastwalk_required_object_vnums") == []
            and state.get("campaign_fastwalk_consider_outcomes") == {}
            and state.get("campaign_objective_kills") == []
            and state.get("campaign_completed_kills") == []
            and state.get("campaign_fastwalk_crowded") is False
            and state.get("campaign_died_during_segment") is False
            and state.get("dead") is not True
            and state.get("xp_loss_observed") is not True
            and state.get("campaign_xp_loss_observed") is not True
            and _verified_combat_potion_count(state, "purple") == 0
            and str(state.get("room_vnum") or "") == "3054"
            and {"healing", "safe"}.issubset(room_flags)
            and state.get("enemies") in (None, [])
            and not state.get("combat_target")
            and state.get("in_combat") is not True
            and state.get("position") in {5, 6, 7}
            and hp > 0
        ):
            # Run 12874 found the moving carrier beyond the two-room graph.
            # Source update.c proves that level 23+ characters cannot be
            # attacked by the fuzzed level-8..12 poison snake on that route,
            # while spec_poison acts only after combat has already started.
            state = dict(state)
            results = dict(_campaign_research_results(state))
            superseded_result = dict(results.pop(policy_id))
            if results:
                state["campaign_research_results"] = results
            else:
                state.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(state.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    state[cooldown_key] = cooldowns
                else:
                    state.pop(cooldown_key, None)
            cleared = [
                str(candidate_id)
                for candidate_id in state.get(
                    _CLEARED_RESEARCH_POLICIES_KEY, ()
                )
                if str(candidate_id) != policy_id
            ]
            if cleared:
                state[_CLEARED_RESEARCH_POLICIES_KEY] = cleared
            else:
                state.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
            state[_SANCTUARY_COMBAT_ONLY_TRANSIT_REVALIDATION_KEY] = {
                "policy_revision": (
                    _SANCTUARY_COMBAT_ONLY_TRANSIT_REVALIDATION_REVISION
                ),
                "policy_id": policy_id,
                "boot_id": state.get("world_boot_id"),
                "level": _level(state),
                "status": "pending",
                "carrier_mobile_vnum": _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
                "transit_mobile_vnum": 4053,
                "transit_special": "spec_poison",
                "transit_mobile_level_range": [8, 12],
                "preserved_attempt_count": attempt_count,
                "superseded_result": superseded_result,
            }
            state.pop("campaign_last_policy", None)
            for key in (
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
                "campaign_fastwalk_where_area_checks",
                "campaign_fastwalk_where_relocation_attempts",
            ):
                state.pop(key, None)
    if previous_revision < 251:
        policy_id = str(state.get("campaign_last_policy") or "")
        result = _campaign_research_results(state).get(policy_id)
        raw_room_flags = state.get("room_flags")
        room_flags = (
            {str(flag).casefold() for flag in raw_room_flags}
            if isinstance(raw_room_flags, Collection)
            and not isinstance(raw_room_flags, (str, bytes))
            else set()
        )
        if (
            policy_id.startswith(_SOURCE_RANKED_POLICY_PREFIX)
            and isinstance(result, Mapping)
            and result.get("boot_id") == state.get("world_boot_id")
            and result.get("observed") is False
            and result.get("viable") is False
            and result.get("completed_kill") is not True
            and result.get("route_hazard")
            == _FIELD_ROOM_LISTING_UNAVAILABLE_ABORT_REASON
            and state.get("campaign_fastwalk_abort_reason")
            == _FIELD_ROOM_LISTING_UNAVAILABLE_ABORT_REASON
            and str(state.get("room_vnum") or "") == "3054"
            and {"healing", "safe"}.issubset(room_flags)
            and state.get("enemies") in (None, [])
            and not state.get("combat_target")
            and state.get("dead") is not True
            and state.get("in_combat") is not True
            and state.get("campaign_died_during_segment") is not True
            and state.get("xp_loss_observed") is not True
            and state.get("campaign_xp_loss_observed") is not True
        ):
            # Closed doors appear inside DD4's exit line as nested brackets.
            # Revision 250 rejected that complete response before target
            # parsing. The original run/checkpoint remains durable evidence;
            # remove only its derived terminal gate for one corrected replay.
            state = dict(state)
            results = dict(_campaign_research_results(state))
            results.pop(policy_id, None)
            if results:
                state["campaign_research_results"] = results
            else:
                state.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(state.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    state[cooldown_key] = cooldowns
                else:
                    state.pop(cooldown_key, None)
            cleared = [
                str(candidate_id)
                for candidate_id in state.get(
                    _CLEARED_RESEARCH_POLICIES_KEY, ()
                )
                if str(candidate_id) != policy_id
            ]
            if cleared:
                state[_CLEARED_RESEARCH_POLICIES_KEY] = cleared
            else:
                state.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
            if not state.get(_SOURCE_RANKED_REVALIDATION_POLICY_KEY):
                state[_SOURCE_RANKED_REVALIDATION_POLICY_KEY] = policy_id
            state.pop("campaign_last_policy", None)
            for key in (
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
            ):
                state.pop(key, None)
    if (
        previous_revision < _FAMILIAR_POST_KILL_RECALL_REVISION
        and _stale_post_kill_familiar_abort(state)
    ):
        state = dict(state)
        state.pop("campaign_fastwalk_abort_reason", None)
    if previous_revision < _SANCTUARY_VISIBILITY_REVALIDATION_REVISION:
        policy_id = _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
        result = _campaign_research_results(state).get(policy_id)
        protection = state.get(_PROTECTION_RECOVERY_KEY)
        known_skills = state.get("campaign_known_skill_levels")
        invisibility_cost = learned_invisibility_mana_cost(
            str(state.get("character_class") or ""),
            str(state.get("subclass") or ""),
            known_skills if isinstance(known_skills, Mapping) else {},
        )
        if (
            isinstance(result, Mapping)
            and result.get("boot_id") == state.get("world_boot_id")
            and result.get("level") == _level(state)
            and result.get("completed_kill") is not True
            and result.get("fatal_failure") is True
            and result.get("route_hazard") == _OBSOLETE_SANCTUARY_GREET_HAZARD
            and isinstance(protection, Mapping)
            and protection.get("boot_id") == state.get("world_boot_id")
            and protection.get("level") in {None, _level(state)}
            and invisibility_cost is not None
            and not state.get(_SANCTUARY_VISIBILITY_REVALIDATION_KEY)
        ):
            # The old route treated a visible, ordinary GREET mobile as a
            # hard veto even while the character had source-authorized invis.
            # Archive that exact terminal result and permit one fresh segment;
            # no combat loss, protection requirement, or attempt total moves.
            state = dict(state)
            results = dict(_campaign_research_results(state))
            results.pop(policy_id, None)
            if results:
                state["campaign_research_results"] = results
            else:
                state.pop("campaign_research_results", None)
            state[_SANCTUARY_VISIBILITY_REVALIDATION_KEY] = {
                "policy_revision": _SANCTUARY_VISIBILITY_REVALIDATION_REVISION,
                "policy_id": policy_id,
                "boot_id": state.get("world_boot_id"),
                "level": _level(state),
                "status": "pending",
                "reason": (
                    "ordinary source GREET now honors fresh live invisibility"
                ),
                "superseded_result": dict(result),
            }
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(state.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    state[cooldown_key] = cooldowns
                else:
                    state.pop(cooldown_key, None)
            cleared = {
                str(candidate_id)
                for candidate_id in state.get(_CLEARED_RESEARCH_POLICIES_KEY, ())
                if str(candidate_id) != policy_id
            }
            if cleared:
                state[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(cleared)
            else:
                state.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
            explicit = state.get(_EXPLICIT_RESEARCH_RETRY_KEY)
            if isinstance(explicit, Mapping):
                policy_ids = {
                    str(candidate_id)
                    for candidate_id in explicit.get("policy_ids", ())
                    if str(candidate_id) != policy_id
                }
                if policy_ids:
                    state[_EXPLICIT_RESEARCH_RETRY_KEY] = {
                        **dict(explicit), "policy_ids": sorted(policy_ids),
                    }
                else:
                    state.pop(_EXPLICIT_RESEARCH_RETRY_KEY, None)
            if state.get("campaign_last_policy") == policy_id:
                state.pop("campaign_last_policy", None)
                for key in (
                    "campaign_fastwalk_abort_reason",
                    "campaign_fastwalk_target_absent",
                    "campaign_fastwalk_target_present_observed",
                    "campaign_fastwalk_crowded",
                    "campaign_fastwalk_consider_outcomes",
                ):
                    state.pop(key, None)
    carrier_evidence = _sanctuary_invisible_carrier_revalidation_evidence(
        state
    )
    if carrier_evidence is not None:
        policy_id = _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
        result = _campaign_research_results(state)[policy_id]
        state = dict(state)
        results = dict(_campaign_research_results(state))
        results.pop(policy_id, None)
        if results:
            state["campaign_research_results"] = results
        else:
            state.pop("campaign_research_results", None)
        state[_SANCTUARY_INVISIBLE_CARRIER_REVALIDATION_KEY] = {
            "policy_revision": (
                _SANCTUARY_INVISIBLE_CARRIER_REVALIDATION_REVISION
            ),
            "policy_id": policy_id,
            "boot_id": state.get("world_boot_id"),
            "level": _level(state),
            "status": "pending",
            "reason": (
                "a fresh safe route preflight reopens one bounded Moria "
                "carrier recovery"
            ),
            "source_location_evidence": carrier_evidence,
            "superseded_result": dict(result),
        }
        for cooldown_key in (
            _RESEARCH_ABSENCE_COOLDOWN_KEY,
            _RESEARCH_CROWD_COOLDOWN_KEY,
        ):
            cooldowns = dict(state.get(cooldown_key) or {})
            cooldowns.pop(policy_id, None)
            if cooldowns:
                state[cooldown_key] = cooldowns
            else:
                state.pop(cooldown_key, None)
        cleared = {
            str(candidate_id)
            for candidate_id in state.get(_CLEARED_RESEARCH_POLICIES_KEY, ())
            if str(candidate_id) != policy_id
        }
        if cleared:
            state[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(cleared)
        else:
            state.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
        explicit = state.get(_EXPLICIT_RESEARCH_RETRY_KEY)
        if isinstance(explicit, Mapping):
            policy_ids = {
                str(candidate_id)
                for candidate_id in explicit.get("policy_ids", ())
                if str(candidate_id) != policy_id
            }
            if policy_ids:
                state[_EXPLICIT_RESEARCH_RETRY_KEY] = {
                    **dict(explicit), "policy_ids": sorted(policy_ids),
                }
            else:
                state.pop(_EXPLICIT_RESEARCH_RETRY_KEY, None)
        state.pop("campaign_last_policy", None)
        for key in (
            "campaign_fastwalk_abort_reason",
            "campaign_fastwalk_target_absent",
            "campaign_fastwalk_target_present_observed",
            "campaign_fastwalk_crowded",
            "campaign_fastwalk_consider_outcomes",
            "campaign_objective_kills",
            "campaign_fastwalk_required_object_vnums",
            "campaign_fastwalk_route_hazards",
            "campaign_fastwalk_route_invisibility_checks",
            "campaign_fastwalk_where_area_checks",
            "campaign_fastwalk_where_relocation_attempts",
        ):
            state.pop(key, None)
    locator_evidence = _sanctuary_locator_label_revalidation_evidence(state)
    if locator_evidence is not None:
        policy_id = _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
        result = _campaign_research_results(state)[policy_id]
        state = dict(state)
        results = dict(_campaign_research_results(state))
        results.pop(policy_id, None)
        if results:
            state["campaign_research_results"] = results
        else:
            state.pop("campaign_research_results", None)
        state[_SANCTUARY_LOCATOR_LABEL_REVALIDATION_KEY] = {
            "policy_revision": _SANCTUARY_LOCATOR_LABEL_REVALIDATION_REVISION,
            "policy_id": policy_id,
            "boot_id": state.get("world_boot_id"),
            "level": _level(state),
            "status": "pending",
            "reason": (
                "bounded carrier search preserves distinct where labels and "
                "rejects empty relocations"
            ),
            "source_location_evidence": locator_evidence,
            "superseded_result": dict(result),
        }
        for cooldown_key in (
            _RESEARCH_ABSENCE_COOLDOWN_KEY,
            _RESEARCH_CROWD_COOLDOWN_KEY,
        ):
            cooldowns = dict(state.get(cooldown_key) or {})
            cooldowns.pop(policy_id, None)
            if cooldowns:
                state[cooldown_key] = cooldowns
            else:
                state.pop(cooldown_key, None)
        cleared = {
            str(candidate_id)
            for candidate_id in state.get(_CLEARED_RESEARCH_POLICIES_KEY, ())
            if str(candidate_id) != policy_id
        }
        if cleared:
            state[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(cleared)
        else:
            state.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
        explicit = state.get(_EXPLICIT_RESEARCH_RETRY_KEY)
        if isinstance(explicit, Mapping):
            policy_ids = {
                str(candidate_id)
                for candidate_id in explicit.get("policy_ids", ())
                if str(candidate_id) != policy_id
            }
            if policy_ids:
                state[_EXPLICIT_RESEARCH_RETRY_KEY] = {
                    **dict(explicit), "policy_ids": sorted(policy_ids),
                }
            else:
                state.pop(_EXPLICIT_RESEARCH_RETRY_KEY, None)
        state.pop("campaign_last_policy", None)
        for key in (
            "campaign_fastwalk_abort_reason",
            "campaign_fastwalk_target_absent",
            "campaign_fastwalk_target_present_observed",
            "campaign_fastwalk_crowded",
            "campaign_fastwalk_consider_outcomes",
            "campaign_objective_kills",
            "campaign_fastwalk_required_object_vnums",
            "campaign_fastwalk_route_hazards",
            "campaign_fastwalk_where_area_checks",
            "campaign_fastwalk_where_relocation_attempts",
        ):
            state.pop(key, None)
    if previous_revision < 170:
        # Mud School now keeps a circuit open when one arena mobile is
        # below-band but another passes live consideration. Reopen only a
        # same-level, same-reboot exclusion created under the old all-or-
        # nothing merge behavior; a fresh segment will re-record a genuine
        # all-below-band result.
        raw_exclusions = state.get(_BELOW_BAND_POLICY_EXCLUSIONS_KEY)
        if isinstance(raw_exclusions, Mapping):
            current_level = _level(state)
            current_boot = state.get("world_boot_id")
            repaired_exclusions = {
                str(policy_id): dict(record)
                for policy_id, record in raw_exclusions.items()
                if not (
                    str(policy_id) in _MUD_SCHOOL_PARTIAL_BAND_POLICY_IDS
                    and isinstance(record, Mapping)
                    and record.get("level") == current_level
                    and record.get("boot_id") == current_boot
                )
            }
            if len(repaired_exclusions) != len(raw_exclusions):
                state = dict(state)
                if repaired_exclusions:
                    state[_BELOW_BAND_POLICY_EXCLUSIONS_KEY] = (
                        repaired_exclusions
                    )
                else:
                    state.pop(_BELOW_BAND_POLICY_EXCLUSIONS_KEY, None)
    if previous_revision < 172:
        # The level-six source-ranked Gnome route was once abandoned because
        # mobile 3064 greeted the character in Temple Square. The starter now
        # source-identifies that harmless interruption and finishes it rather
        # than paying DD4's flee penalty. Reopen only that exact old result;
        # every other route hazard remains authoritative.
        policy_id = "source-ranked-hunt-gnome-1524-1589-6"
        route_hazard = (
            "unexpected combat interrupted fastwalk "
            "'source-ranked hunt crab 1589' before its objective"
        )
        result = _campaign_research_results(state).get(policy_id)
        if (
            isinstance(result, Mapping)
            and result.get("route_hazard") == route_hazard
        ):
            state = dict(state)
            research_results = dict(_campaign_research_results(state))
            research_results.pop(policy_id, None)
            if research_results:
                state["campaign_research_results"] = research_results
            else:
                state.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(state.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    state[cooldown_key] = cooldowns
                else:
                    state.pop(cooldown_key, None)
            if (
                state.get("campaign_last_policy") == policy_id
                and state.get("campaign_fastwalk_abort_reason") == route_hazard
            ):
                state.pop("campaign_last_policy", None)
                state.pop("campaign_fastwalk_abort_reason", None)
            for key in (
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
            ):
                state.pop(key, None)
            state[_SOURCE_RANKED_REVALIDATION_POLICY_KEY] = policy_id
        elif (
            _level(state) == 6
            and not isinstance(result, Mapping)
            and not state.get(_SOURCE_RANKED_REVALIDATION_POLICY_KEY)
        ):
            # Revision 171 was already applied before the one-shot selector
            # marker existed. Schedule the same bounded revalidation for
            # level-six campaigns whose Gnome route has no live result yet.
            state = dict(state)
            state[_SOURCE_RANKED_REVALIDATION_POLICY_KEY] = policy_id
    if previous_revision < _CAMPAIGN_POLICY_REVISION:
        # Revision 312 changed the exact Dwarven room-6505 gate from a
        # generic one-mobile isolation check to source-proven, selector-based
        # same-prototype handling.  Reopen only the old fatal result produced
        # by that crowd rejection; preserve all other fatal sanctuary and
        # combat evidence.
        dwarven_gate_policy_id = _SOURCE_RANKED_DWARVEN_SANCTUARY_POLICY.policy_id
        dwarven_gate_result = _campaign_research_results(state).get(
            dwarven_gate_policy_id
        )
        if (
            previous_revision < 312
            and isinstance(dwarven_gate_result, Mapping)
            and dwarven_gate_result.get("boot_id") == state.get("world_boot_id")
            and dwarven_gate_result.get("level") == _level(state)
            and dwarven_gate_result.get("fatal_failure") is True
            and dwarven_gate_result.get("completed_kill") is not True
            and dwarven_gate_result.get("route_hazard")
            == _SANCTUARY_RESOURCE_EXHAUSTED_HAZARD
            and _level(state) >= _DWARVEN_SANCTUARY_MINIMUM_LEVEL
        ):
            state = dict(state)
            research_results = dict(_campaign_research_results(state))
            superseded_result = dict(
                research_results.pop(dwarven_gate_policy_id)
            )
            if research_results:
                state["campaign_research_results"] = research_results
            else:
                state.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(state.get(cooldown_key) or {})
                cooldowns.pop(dwarven_gate_policy_id, None)
                if cooldowns:
                    state[cooldown_key] = cooldowns
                else:
                    state.pop(cooldown_key, None)
            sanctuary_attempts = dict(
                state.get("campaign_sanctuary_resource_attempts") or {}
            )
            sanctuary_attempts.pop(dwarven_gate_policy_id, None)
            if sanctuary_attempts:
                state["campaign_sanctuary_resource_attempts"] = sanctuary_attempts
            else:
                state.pop("campaign_sanctuary_resource_attempts", None)
            if state.get("campaign_last_policy") == dwarven_gate_policy_id:
                state.pop("campaign_last_policy", None)
                state.pop("campaign_fastwalk_abort_reason", None)
                state.pop("campaign_fastwalk_route_hazards", None)
            for key in (
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
            ):
                state.pop(key, None)
            state[_SOURCE_RANKED_REVALIDATION_POLICY_KEY] = (
                dwarven_gate_policy_id
            )
            state[_DWARVEN_KEY_GATE_REVALIDATION_KEY] = {
                "policy_revision": 312,
                "policy_id": dwarven_gate_policy_id,
                "boot_id": state.get("world_boot_id"),
                "level": _level(state),
                "status": "pending",
                "reason": (
                    "reopen the exact Dwarven key gate after adding bounded "
                    "same-source TARGETMODE selector handling"
                ),
                "superseded_result": superseded_result,
            }
        # Revision 313 repairs the first live attempt after revision 312: the
        # source identity audit was evaluated at the healer before transit and
        # exhausted the Dwarven resource counter without opening the route.
        # Reopen only that exact same-boot hazard; all other Dwarven failures
        # remain authoritative.
        dwarven_identity_gate_hazard = (
            "route gate aborted: same-source route gate failed its source identity audit"
        )
        current_dwarven_result = _campaign_research_results(state).get(
            dwarven_gate_policy_id
        )
        current_dwarven_hazards = {
            str(hazard)
            for hazard in (state.get("campaign_fastwalk_route_hazards") or ())
        }
        if (
            312 <= previous_revision < 313
            and isinstance(current_dwarven_result, Mapping)
            and current_dwarven_result.get("boot_id") == state.get("world_boot_id")
            and current_dwarven_result.get("level") == _level(state)
            and current_dwarven_result.get("fatal_failure") is True
            and current_dwarven_result.get("completed_kill") is not True
            and current_dwarven_result.get("route_hazard")
            == _SANCTUARY_RESOURCE_EXHAUSTED_HAZARD
            and dwarven_identity_gate_hazard in current_dwarven_hazards
            and _level(state) >= _DWARVEN_SANCTUARY_MINIMUM_LEVEL
        ):
            state = dict(state)
            research_results = dict(_campaign_research_results(state))
            superseded_result = dict(
                research_results.pop(dwarven_gate_policy_id)
            )
            if research_results:
                state["campaign_research_results"] = research_results
            else:
                state.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(state.get(cooldown_key) or {})
                cooldowns.pop(dwarven_gate_policy_id, None)
                if cooldowns:
                    state[cooldown_key] = cooldowns
                else:
                    state.pop(cooldown_key, None)
            sanctuary_attempts = dict(
                state.get("campaign_sanctuary_resource_attempts") or {}
            )
            sanctuary_attempts.pop(dwarven_gate_policy_id, None)
            if sanctuary_attempts:
                state["campaign_sanctuary_resource_attempts"] = sanctuary_attempts
            else:
                state.pop("campaign_sanctuary_resource_attempts", None)
            if state.get("campaign_last_policy") == dwarven_gate_policy_id:
                state.pop("campaign_last_policy", None)
                state.pop("campaign_fastwalk_abort_reason", None)
            state.pop("campaign_fastwalk_route_hazards", None)
            for key in (
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
            ):
                state.pop(key, None)
            state[_SOURCE_RANKED_REVALIDATION_POLICY_KEY] = (
                dwarven_gate_policy_id
            )
            state[_DWARVEN_KEY_GATE_REVALIDATION_KEY] = {
                "policy_revision": 313,
                "policy_id": dwarven_gate_policy_id,
                "boot_id": state.get("world_boot_id"),
                "level": _level(state),
                "status": "pending",
                "reason": (
                    "reopen the Dwarven key gate after moving its source identity "
                    "audit from healer-origin transit to room-local execution"
                ),
                "superseded_result": superseded_result,
            }
        # Revision 314 repairs the next live attempt after revision 313: the
        # first exact guard was killed as route maintenance, then the worker
        # returned to the healer on its ordinary health floor. That segment
        # is not a failed sanctuary-carrier attempt, but the old checkpoint
        # reconstructed it as one and exhausted the bounded reserve counter.
        # Require both exact route-gate hazards so unrelated health-floor
        # returns remain authoritative.
        dwarven_gate_consider_hazard = (
            "required-loot route gate considered before carrier: "
            "dwarven guard (source mobile 6500)"
        )
        dwarven_gate_health_floor_hazard = (
            "route gate aborted: required-loot route gate appeared below its "
            "health-entry floor"
        )
        current_dwarven_result = _campaign_research_results(state).get(
            dwarven_gate_policy_id
        )
        current_dwarven_hazards = {
            str(hazard)
            for hazard in (state.get("campaign_fastwalk_route_hazards") or ())
        }
        if (
            313 <= previous_revision < 314
            and isinstance(current_dwarven_result, Mapping)
            and current_dwarven_result.get("boot_id") == state.get("world_boot_id")
            and current_dwarven_result.get("level") == _level(state)
            and current_dwarven_result.get("fatal_failure") is True
            and current_dwarven_result.get("completed_kill") is not True
            and current_dwarven_result.get("route_hazard")
            == _SANCTUARY_RESOURCE_EXHAUSTED_HAZARD
            and dwarven_gate_consider_hazard in current_dwarven_hazards
            and dwarven_gate_health_floor_hazard in current_dwarven_hazards
            and state.get("campaign_last_policy") == dwarven_gate_policy_id
            and _level(state) >= _DWARVEN_SANCTUARY_MINIMUM_LEVEL
        ):
            state = dict(state)
            research_results = dict(_campaign_research_results(state))
            superseded_result = dict(
                research_results.pop(dwarven_gate_policy_id)
            )
            if research_results:
                state["campaign_research_results"] = research_results
            else:
                state.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(state.get(cooldown_key) or {})
                cooldowns.pop(dwarven_gate_policy_id, None)
                if cooldowns:
                    state[cooldown_key] = cooldowns
                else:
                    state.pop(cooldown_key, None)
            sanctuary_attempts = dict(
                state.get("campaign_sanctuary_resource_attempts") or {}
            )
            sanctuary_attempts.pop(dwarven_gate_policy_id, None)
            if sanctuary_attempts:
                state["campaign_sanctuary_resource_attempts"] = sanctuary_attempts
            else:
                state.pop("campaign_sanctuary_resource_attempts", None)
            state.pop("campaign_last_policy", None)
            state.pop("campaign_fastwalk_abort_reason", None)
            state.pop("campaign_fastwalk_route_hazards", None)
            for key in (
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
            ):
                state.pop(key, None)
            state[_SOURCE_RANKED_REVALIDATION_POLICY_KEY] = (
                dwarven_gate_policy_id
            )
            state[_DWARVEN_KEY_GATE_REVALIDATION_KEY] = {
                "policy_revision": 314,
                "policy_id": dwarven_gate_policy_id,
                "boot_id": state.get("world_boot_id"),
                "level": _level(state),
                "status": "pending",
                "reason": (
                    "reopen the Dwarven key gate after excluding route-gate "
                    "maintenance from sanctuary carrier attempts"
                ),
                "superseded_result": superseded_result,
            }
        # Revision 315 recovers the exact live key acquisition that happened
        # before the old selector persistence crash. The failed run's latest
        # GMCP/text checkpoint carries the source-named key in inventory even
        # though its derived object ledger is empty; do not make Dorrik kill
        # that guard again or replay the stale sanctuary counter.
        current_dwarven_result = _campaign_research_results(state).get(
            dwarven_gate_policy_id
        )
        current_dwarven_attempt = dict(
            (state.get("campaign_sanctuary_resource_attempts") or {}).get(
                dwarven_gate_policy_id,
                {},
            )
            if isinstance(
                (state.get("campaign_sanctuary_resource_attempts") or {}).get(
                    dwarven_gate_policy_id,
                    {},
                ),
                Mapping,
            )
            else {}
        )
        if (
            314 <= previous_revision < 315
            and isinstance(current_dwarven_result, Mapping)
            and current_dwarven_result.get("boot_id") == state.get("world_boot_id")
            and current_dwarven_result.get("level") == _level(state)
            and current_dwarven_result.get("fatal_failure") is True
            and current_dwarven_result.get("observed") is False
            and current_dwarven_result.get("completed_kill") is not True
            and current_dwarven_result.get("route_hazard")
            == _SANCTUARY_RESOURCE_EXHAUSTED_HAZARD
            and state.get("campaign_last_policy") == dwarven_gate_policy_id
            and _dwarven_key_gate_key_acquired(state)
            and int(current_dwarven_attempt.get("count") or 0)
            >= _SANCTUARY_RESOURCE_MAX_ATTEMPTS
            and _level(state) >= _DWARVEN_SANCTUARY_MINIMUM_LEVEL
        ):
            state = dict(state)
            research_results = dict(_campaign_research_results(state))
            superseded_result = dict(
                research_results.pop(dwarven_gate_policy_id)
            )
            if research_results:
                state["campaign_research_results"] = research_results
            else:
                state.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(state.get(cooldown_key) or {})
                cooldowns.pop(dwarven_gate_policy_id, None)
                if cooldowns:
                    state[cooldown_key] = cooldowns
                else:
                    state.pop(cooldown_key, None)
            sanctuary_attempts = dict(
                state.get("campaign_sanctuary_resource_attempts") or {}
            )
            sanctuary_attempts.pop(dwarven_gate_policy_id, None)
            if sanctuary_attempts:
                state["campaign_sanctuary_resource_attempts"] = sanctuary_attempts
            else:
                state.pop("campaign_sanctuary_resource_attempts", None)
            required_object_vnums = {
                int(vnum)
                for vnum in (
                    state.get("campaign_fastwalk_required_object_vnums") or ()
                )
                if str(vnum).lstrip("-").isdigit()
            }
            required_object_vnums.add(_DWARVEN_SANCTUARY_DOOR_KEY_VNUM)
            state["campaign_fastwalk_required_object_vnums"] = sorted(
                required_object_vnums
            )
            recovered_selectors = {
                selector
                for description, selector in _inventory_entries(
                    state.get("inventory")
                )
                if selector is not None
                and "deep green key" in str(description).casefold()
                and re.fullmatch(r"#[0-9]+", selector)
            }
            if recovered_selectors:
                prior_selectors = {
                    str(selector)
                    for selector in (
                        state.get(_DWARVEN_KEY_GATE_ATTEMPTED_SELECTORS_KEY)
                        or ()
                    )
                    if re.fullmatch(r"#[0-9]+", str(selector))
                }
                prior_selectors.update(
                    selector if selector.startswith("#") else f"#{selector}"
                    for selector in recovered_selectors
                )
                state[_DWARVEN_KEY_GATE_ATTEMPTED_SELECTORS_KEY] = sorted(
                    prior_selectors
                )
            state.pop("campaign_last_policy", None)
            state.pop("campaign_fastwalk_abort_reason", None)
            state.pop("campaign_fastwalk_route_hazards", None)
            state[_SOURCE_RANKED_REVALIDATION_POLICY_KEY] = (
                dwarven_gate_policy_id
            )
            state[_DWARVEN_KEY_GATE_REVALIDATION_KEY] = {
                "policy_revision": 315,
                "policy_id": dwarven_gate_policy_id,
                "boot_id": state.get("world_boot_id"),
                "level": _level(state),
                "status": "succeeded",
                "outcome": "door key acquired from the exact room-6505 guard",
                "selector": (
                    sorted(recovered_selectors)[0]
                    if recovered_selectors
                    else None
                ),
                "superseded_result": superseded_result,
            }
        # Revision 311 taught the starter to distinguish an exact live
        # TARGETMODE instance from a source-prototype ambiguity when every
        # reachable ordinary target profile is identical. Reopen only the
        # same-level, same-boot research results whose sole route hazard was
        # that old ambiguity; losses, specials, protected probes, and other
        # route hazards remain authoritative.
        current_level = _level(state)
        source_identity_alias_policy_ids = sorted(
            str(policy_id)
            for policy_id, raw_result in _campaign_research_results(
                state
            ).items()
            if (
                str(policy_id).startswith(_SOURCE_RANKED_POLICY_PREFIX)
                and str(policy_id).endswith(f"-{current_level}")
                and isinstance(raw_result, Mapping)
                and raw_result.get("boot_id") == state.get("world_boot_id")
                and raw_result.get("observed") is False
                and raw_result.get("viable") is False
                and raw_result.get("completed_kill") is not True
                and "source-ambiguous" in str(
                    raw_result.get("route_hazard") or ""
                )
            )
        )
        if source_identity_alias_policy_ids:
            state = dict(state)
            research_results = dict(_campaign_research_results(state))
            superseded_results = {
                policy_id: dict(research_results.pop(policy_id))
                for policy_id in source_identity_alias_policy_ids
            }
            if research_results:
                state["campaign_research_results"] = research_results
            else:
                state.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(state.get(cooldown_key) or {})
                for policy_id in source_identity_alias_policy_ids:
                    cooldowns.pop(policy_id, None)
                if cooldowns:
                    state[cooldown_key] = cooldowns
                else:
                    state.pop(cooldown_key, None)
            if state.get(_SOURCE_RANKED_RETRY_EXHAUSTED_KEY) in set(
                source_identity_alias_policy_ids
            ):
                state.pop(_SOURCE_RANKED_RETRY_EXHAUSTED_KEY, None)
                state.pop(_SOURCE_RANKED_RETRY_EXHAUSTED_BOOT_KEY, None)
            if state.get("campaign_last_policy") in set(
                source_identity_alias_policy_ids
            ):
                state.pop("campaign_last_policy", None)
                state.pop("campaign_fastwalk_abort_reason", None)
            for key in (
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
            ):
                state.pop(key, None)
            revalidation_policy_id = next(
                (
                    policy_id
                    for policy_id in source_identity_alias_policy_ids
                    if policy_id.endswith(f"-{current_level}")
                ),
                source_identity_alias_policy_ids[0],
            )
            state[_SOURCE_RANKED_REVALIDATION_POLICY_KEY] = (
                revalidation_policy_id
            )
            state[_SOURCE_IDENTITY_ALIAS_REVALIDATION_KEY] = {
                "policy_revision": _CAMPAIGN_POLICY_REVISION,
                "policy_ids": source_identity_alias_policy_ids,
                "boot_id": state.get("world_boot_id"),
                "level": current_level,
                "status": "pending",
                "reason": (
                    "reopen source-ranked target identity after proving "
                    "equivalent source prototypes can share a room"
                ),
                "superseded_results": superseded_results,
            }
        # Revision 309 fixed the authoritative-room parser: DD4's
        # colour-coded GMCP title for Undersea room 27073 was being
        # replaced by the plain-text ``look`` title, clearing its VNUM
        # before the target stop could be evaluated. Reopen only the
        # exact same-boot route hazard produced by that stale identity.
        undersea_policy_prefix = (
            f"{_SOURCE_RANKED_POLICY_PREFIX}undersea-27005-27073-"
        )
        undersea_route_hazard = (
            "field route could not find GMCP exit to room 27073"
        )
        stale_policy_ids = sorted(
            str(policy_id)
            for policy_id, raw_result in _campaign_research_results(
                state
            ).items()
            if (
                str(policy_id).startswith(undersea_policy_prefix)
                and isinstance(raw_result, Mapping)
                and raw_result.get("boot_id") == state.get("world_boot_id")
                and raw_result.get("observed") is False
                and raw_result.get("viable") is False
                and raw_result.get("completed_kill") is not True
                and raw_result.get("route_hazard") == undersea_route_hazard
            )
        )
        if stale_policy_ids:
            state = dict(state)
            research_results = dict(_campaign_research_results(state))
            superseded_results = {
                policy_id: dict(research_results.pop(policy_id))
                for policy_id in stale_policy_ids
            }
            if research_results:
                state["campaign_research_results"] = research_results
            else:
                state.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(state.get(cooldown_key) or {})
                for policy_id in stale_policy_ids:
                    cooldowns.pop(policy_id, None)
                if cooldowns:
                    state[cooldown_key] = cooldowns
                else:
                    state.pop(cooldown_key, None)
            if state.get("campaign_last_policy") in stale_policy_ids:
                state.pop("campaign_last_policy", None)
                if (
                    state.get("campaign_fastwalk_abort_reason")
                    == undersea_route_hazard
                ):
                    state.pop("campaign_fastwalk_abort_reason", None)
            for key in (
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
            ):
                state.pop(key, None)
            current_level_policy = next(
                (
                    policy_id
                    for policy_id in stale_policy_ids
                    if policy_id.endswith(f"-{_level(state)}")
                ),
                stale_policy_ids[0],
            )
            state[_SOURCE_RANKED_REVALIDATION_POLICY_KEY] = (
                current_level_policy
            )
            state[_UNDERSEA_ROOM_IDENTITY_REVALIDATION_KEY] = {
                "policy_revision": _CAMPAIGN_POLICY_REVISION,
                "policy_ids": stale_policy_ids,
                "boot_id": state.get("world_boot_id"),
                "level": _level(state),
                "status": "reopened",
                "old_route_hazard": undersea_route_hazard,
                "superseded_results": superseded_results,
            }
        if previous_revision < 186:
            # The recallable Mirror Guardian route was quarantined after the
            # old starter killed one low-level drunk and then fled from a
            # same-prototype respawn on the way home. The starter now has a
            # bounded same-prototype defensive return allowance, so reopen
            # only that exact stale result for one fresh live revalidation.
            mirror_guardian_prefix = (
                f"{_SOURCE_RANKED_POLICY_PREFIX}mirror-realm-19001-19041-"
            )
            stale_policy_ids = []
            for policy_id, raw_result in _campaign_research_results(
                state
            ).items():
                route_hazard = str(
                    raw_result.get("route_hazard") or ""
                ) if isinstance(raw_result, Mapping) else ""
                if (
                    str(policy_id).startswith(mirror_guardian_prefix)
                    and isinstance(raw_result, Mapping)
                    and raw_result.get("boot_id") == state.get("world_boot_id")
                    and "the drunk" in route_hazard.casefold()
                    and route_hazard.startswith(
                        "field hunt aborted after one unavoidable below-band "
                        "transit attacker"
                    )
                ):
                    stale_policy_ids.append(str(policy_id))
            if stale_policy_ids:
                state = dict(state)
                research_results = dict(_campaign_research_results(state))
                for policy_id in stale_policy_ids:
                    research_results.pop(policy_id, None)
                if research_results:
                    state["campaign_research_results"] = research_results
                else:
                    state.pop("campaign_research_results", None)
                for cooldown_key in (
                    _RESEARCH_ABSENCE_COOLDOWN_KEY,
                    _RESEARCH_CROWD_COOLDOWN_KEY,
                ):
                    cooldowns = dict(state.get(cooldown_key) or {})
                    for policy_id in stale_policy_ids:
                        cooldowns.pop(policy_id, None)
                    if cooldowns:
                        state[cooldown_key] = cooldowns
                    else:
                        state.pop(cooldown_key, None)
                if state.get("campaign_last_policy") in stale_policy_ids:
                    state.pop("campaign_last_policy", None)
                    state.pop("campaign_fastwalk_abort_reason", None)
                    for key in (
                        "campaign_fastwalk_target_absent",
                        "campaign_fastwalk_target_present_observed",
                        "campaign_fastwalk_crowded",
                    ):
                        state.pop(key, None)
                current_level_policy = next(
                    (
                        policy_id
                        for policy_id in stale_policy_ids
                        if policy_id.endswith(f"-{_level(state)}")
                    ),
                    stale_policy_ids[0],
                )
                state[_SOURCE_RANKED_REVALIDATION_POLICY_KEY] = (
                    current_level_policy
                )
        if previous_revision < 187:
            # The repaired starter can now finish one exact, source-known,
            # no-special below-band transit attacker and continue to the
            # Mirror Guardian endpoint. Reopen only the current-reboot result
            # created by the earlier route-abort behavior.
            mirror_guardian_prefix = (
                f"{_SOURCE_RANKED_POLICY_PREFIX}mirror-realm-19001-19041-"
            )
            stale_policy_ids = []
            for policy_id, raw_result in _campaign_research_results(
                state
            ).items():
                route_hazard = str(
                    raw_result.get("route_hazard") or ""
                ) if isinstance(raw_result, Mapping) else ""
                if (
                    str(policy_id).startswith(mirror_guardian_prefix)
                    and isinstance(raw_result, Mapping)
                    and raw_result.get("boot_id") == state.get("world_boot_id")
                    and "carnivorous grass" in route_hazard.casefold()
                    and route_hazard.startswith(
                        "field hunt aborted after one unavoidable below-band "
                        "transit attacker"
                    )
                ):
                    stale_policy_ids.append(str(policy_id))
            if stale_policy_ids:
                state = dict(state)
                research_results = dict(_campaign_research_results(state))
                for policy_id in stale_policy_ids:
                    research_results.pop(policy_id, None)
                if research_results:
                    state["campaign_research_results"] = research_results
                else:
                    state.pop("campaign_research_results", None)
                for cooldown_key in (
                    _RESEARCH_ABSENCE_COOLDOWN_KEY,
                    _RESEARCH_CROWD_COOLDOWN_KEY,
                ):
                    cooldowns = dict(state.get(cooldown_key) or {})
                    for policy_id in stale_policy_ids:
                        cooldowns.pop(policy_id, None)
                    if cooldowns:
                        state[cooldown_key] = cooldowns
                    else:
                        state.pop(cooldown_key, None)
                if state.get("campaign_last_policy") in stale_policy_ids:
                    state.pop("campaign_last_policy", None)
                    state.pop("campaign_fastwalk_abort_reason", None)
                    for key in (
                        "campaign_fastwalk_target_absent",
                        "campaign_fastwalk_target_present_observed",
                        "campaign_fastwalk_crowded",
                    ):
                        state.pop(key, None)
                current_level_policy = next(
                    (
                        policy_id
                        for policy_id in stale_policy_ids
                        if policy_id.endswith(f"-{_level(state)}")
                    ),
                    stale_policy_ids[0],
                )
                state[_SOURCE_RANKED_REVALIDATION_POLICY_KEY] = (
                    current_level_policy
                )
        if previous_revision < 185:
            # Fame recovery now has an executable sanctuary-protected source
            # damage bound. Reopen only the old retryable Circus and Mirror
            # attempts; preserve their records so the historical probes are
            # never mistaken for fresh evidence. Fatal Lotus evidence remains
            # quarantined until a reboot or a separately justified repair.
            fame_policy_ids = (
                _FAME_RECOVERY_CIRCUS_POLICY.policy_id,
                _FAME_RECOVERY_POLICY.policy_id,
            )
            research_results = _campaign_research_results(state)
            migrated_results = dict(research_results)
            absence_cooldowns = dict(
                state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
            )
            crowd_cooldowns = dict(
                state.get(_RESEARCH_CROWD_COOLDOWN_KEY) or {}
            )
            changed = False
            for policy_id in fame_policy_ids:
                result = research_results.get(policy_id)
                if (
                    not isinstance(result, Mapping)
                    or result.get("completed_kill") is True
                    or result.get("fatal_failure") is True
                    or result.get("retryable_failure") is not True
                ):
                    continue
                migrated_result = dict(result)
                migrated_result["superseded_by_policy_revision"] = 185
                migrated_result["superseded_reason"] = (
                    "reopened for the executable sanctuary-protected "
                    "source damage bound"
                )
                if migrated_result != result:
                    migrated_results[policy_id] = migrated_result
                    changed = True
                if policy_id in absence_cooldowns:
                    absence_cooldowns.pop(policy_id, None)
                    changed = True
                if policy_id in crowd_cooldowns:
                    crowd_cooldowns.pop(policy_id, None)
                    changed = True
            if changed:
                state = dict(state)
                state["campaign_research_results"] = migrated_results
                if absence_cooldowns:
                    state[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
                else:
                    state.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
                if crowd_cooldowns:
                    state[_RESEARCH_CROWD_COOLDOWN_KEY] = crowd_cooldowns
                else:
                    state.pop(_RESEARCH_CROWD_COOLDOWN_KEY, None)
        if (
            _legacy_fastwalk_training_route_hazard(state)
            and not state.get(_FASTWALK_TRAINING_ROUTE_HAZARD_KEY)
        ):
            # Revision 174 could leave a distant class-trainer trip marked
            # incomplete after one unavoidable transit attacker. Preserve
            # that exact safe-return checkpoint so the next segment does not
            # retrace the same route before the next reboot or level.
            state = dict(state)
            state[_FASTWALK_TRAINING_ROUTE_HAZARD_KEY] = (
                _fastwalk_training_route_hazard_marker(state)
            )
    revalidation_policy_id = str(
        state.get(_SOURCE_RANKED_REVALIDATION_POLICY_KEY) or ""
    )
    revalidation_result = _campaign_research_results(state).get(
        revalidation_policy_id
    )
    if (
        revalidation_policy_id
        and isinstance(revalidation_result, Mapping)
        and revalidation_result.get("boot_id") == state.get("world_boot_id")
        and revalidation_result.get("completed_kill") is True
        and revalidation_result.get("viable") is True
    ):
        # A checkpoint written before the marker-consumption repair may still
        # contain the marker and its old single-loss record. A confirmed kill
        # is newer evidence: clear both before the next selector invocation.
        state = dict(state)
        state.pop(_SOURCE_RANKED_REVALIDATION_POLICY_KEY, None)
        state = _clear_source_ranked_xp_loss(
            state,
            policy_ids=(revalidation_policy_id,),
        )
        if state.get("campaign_last_policy") == revalidation_policy_id:
            state.pop("campaign_last_policy", None)
            state.pop("campaign_fastwalk_abort_reason", None)
            for key in (
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
            ):
                state.pop(key, None)
    if previous_revision < 161:
        exclusions = dict(state.get(_BELOW_BAND_POLICY_EXCLUSIONS_KEY) or {})
        if exclusions.pop("recover-daycare-ring", None) is not None:
            state = dict(state)
            if exclusions:
                state[_BELOW_BAND_POLICY_EXCLUSIONS_KEY] = exclusions
            else:
                state.pop(_BELOW_BAND_POLICY_EXCLUSIONS_KEY, None)
    if previous_revision == 168:
        # The sanctuary locator now follows the live `where` result through
        # source-approved Moria rooms. Reopen only the old retryable result so
        # this route repair receives one fresh autonomous evaluation; absence,
        # crowd, hazard, and completed-kill evidence remain untouched.
        sanctuary_policy_id = _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
        sanctuary_result = _campaign_research_results(state).get(
            sanctuary_policy_id
        )
        if (
            isinstance(sanctuary_result, Mapping)
            and sanctuary_result.get("boot_id") == state.get("world_boot_id")
            and sanctuary_result.get("retryable_failure") is True
            and sanctuary_result.get("completed_kill") is not True
        ):
            state = dict(state)
            research_results = dict(_campaign_research_results(state))
            research_results.pop(sanctuary_policy_id, None)
            if research_results:
                state["campaign_research_results"] = research_results
            else:
                state.pop("campaign_research_results", None)
            absence_cooldowns = dict(
                state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
            )
            absence_cooldowns.pop(sanctuary_policy_id, None)
            if absence_cooldowns:
                state[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
            else:
                state.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
            retry_marker = state.get(_EXPLICIT_RESEARCH_RETRY_KEY)
            if isinstance(retry_marker, Mapping):
                retry_policy_ids = {
                    str(policy_id)
                    for policy_id in retry_marker.get("policy_ids", ())
                    if str(policy_id) != sanctuary_policy_id
                }
                if retry_policy_ids:
                    state[_EXPLICIT_RESEARCH_RETRY_KEY] = {
                        "boot_id": retry_marker.get("boot_id"),
                        "policy_ids": sorted(retry_policy_ids),
                    }
                else:
                    state.pop(_EXPLICIT_RESEARCH_RETRY_KEY, None)
            if state.get("campaign_last_policy") == sanctuary_policy_id:
                state.pop("campaign_fastwalk_target_absent", None)
                state.pop("campaign_fastwalk_abort_reason", None)
    daycare_result = _campaign_research_results(state).get(
        "recover-daycare-ring"
    )
    if (
        143 <= previous_revision < 145
        and _level(state) >= 10
        and (
            int(state.get(_DAYCARE_RING_COOLDOWN_KEY) or 0) > 0
            or (
                isinstance(daycare_result, Mapping)
                and daycare_result.get("crowded") is True
            )
        )
    ):
        state = _clear_daycare_ring_field_metadata(state)
        for key in (
            "campaign_daycare_ring_attempted_level",
            _DAYCARE_RING_ATTEMPT_BOOT_KEY,
            _DAYCARE_RING_COOLDOWN_KEY,
        ):
            state.pop(key, None)
    if previous_revision < 142 and _SOURCE_RANKED_CANDIDATE_KEY in state:
        state = dict(state)
        state.pop(_SOURCE_RANKED_CANDIDATE_KEY, None)
    if previous_revision < 134:
        raw_exclusions = state.get(_BELOW_BAND_POLICY_EXCLUSIONS_KEY)
        if isinstance(raw_exclusions, Mapping):
            repaired_exclusions: dict[str, dict[str, Any]] = {}
            changed = False
            for policy_id, value in raw_exclusions.items():
                if not isinstance(value, Mapping):
                    continue
                record = dict(value)
                source_keys = record.get("source_mobile_keys")
                if source_keys:
                    if str(policy_id).startswith(_SOURCE_RANKED_POLICY_PREFIX):
                        match = re.search(r"-(\d+)-\d+-\d+$", str(policy_id))
                        expected = (
                            f"mobile:{match.group(1)}" if match else None
                        )
                        repaired_keys = [expected] if expected else []
                        if list(source_keys) != repaired_keys:
                            changed = True
                        if repaired_keys:
                            record["source_mobile_keys"] = repaired_keys
                        else:
                            record.pop("source_mobile_keys", None)
                    else:
                        record.pop("source_mobile_keys", None)
                        changed = True
                repaired_exclusions[str(policy_id)] = record
            if changed:
                state = dict(state)
                state[_BELOW_BAND_POLICY_EXCLUSIONS_KEY] = repaired_exclusions
    if previous_revision < 130:
        results = _campaign_research_results(state)
        mirror_result = results.get(_FAME_RECOVERY_POLICY.policy_id)
        if (
            isinstance(mirror_result, Mapping)
            and mirror_result.get("boot_id") == state.get("world_boot_id")
            and mirror_result.get("crowded") is True
            and mirror_result.get("completed_kill") is not True
        ):
            state = dict(state)
            results = dict(results)
            results.pop(_FAME_RECOVERY_POLICY.policy_id, None)
            if results:
                state["campaign_research_results"] = results
            else:
                state.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(state.get(cooldown_key) or {})
                cooldowns.pop(_FAME_RECOVERY_POLICY.policy_id, None)
                if cooldowns:
                    state[cooldown_key] = cooldowns
                else:
                    state.pop(cooldown_key, None)
            if (
                state.get("campaign_last_policy")
                == _FAME_RECOVERY_POLICY.policy_id
            ):
                state.pop("campaign_fastwalk_crowded", None)
                state.pop("campaign_fastwalk_abort_reason", None)
    if previous_revision < 133:
        gardener_policy_id = state.get("campaign_last_policy")
        if (
            isinstance(gardener_policy_id, str)
            and gardener_policy_id.startswith(
                f"{_SOURCE_RANKED_POLICY_PREFIX}mirror-realm-19022-"
            )
        ):
            results = _campaign_research_results(state)
            gardener_result = results.get(gardener_policy_id)
            gardener_cleared = gardener_policy_id in {
                str(policy_id)
                for policy_id in state.get(
                    _CLEARED_RESEARCH_POLICIES_KEY,
                    (),
                )
            }
            if (
                (
                    isinstance(gardener_result, Mapping)
                    and gardener_result.get("boot_id")
                    == state.get("world_boot_id")
                    and gardener_result.get("crowded") is True
                )
                or (previous_revision in {131, 132} and gardener_cleared)
            ):
                state = dict(state)
                results = dict(results)
                if isinstance(gardener_result, Mapping):
                    gardener_result = dict(gardener_result)
                    gardener_result.pop("crowded", None)
                    gardener_result.pop("crowd_exhausted", None)
                    if (
                        gardener_result.get("viable") is True
                        and gardener_result.get("completed_kill") is not False
                    ):
                        results[gardener_policy_id] = gardener_result
                    else:
                        results.pop(gardener_policy_id, None)
                if results:
                    state["campaign_research_results"] = results
                else:
                    state.pop("campaign_research_results", None)
                for cooldown_key in (
                    _RESEARCH_ABSENCE_COOLDOWN_KEY,
                    _RESEARCH_CROWD_COOLDOWN_KEY,
                    _SOURCE_RANKED_CROWD_ATTEMPTS_KEY,
                ):
                    cooldowns = dict(state.get(cooldown_key) or {})
                    cooldowns.pop(gardener_policy_id, None)
                    if cooldowns:
                        state[cooldown_key] = cooldowns
                    else:
                        state.pop(cooldown_key, None)
                cleared_policies = [
                    str(policy_id)
                    for policy_id in state.get(
                        _CLEARED_RESEARCH_POLICIES_KEY,
                        (),
                    )
                    if str(policy_id) != gardener_policy_id
                ]
                if cleared_policies:
                    state[_CLEARED_RESEARCH_POLICIES_KEY] = cleared_policies
                else:
                    state.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
                state.pop("campaign_fastwalk_crowded", None)
                state.pop("campaign_fastwalk_abort_reason", None)
    if previous_revision < 127:
        results = _campaign_research_results(state)
        fame_result = results.get(_FAME_RECOVERY_POLICY.policy_id)
        if (
            isinstance(fame_result, dict)
            and fame_result.get("boot_id") == state.get("world_boot_id")
            and fame_result.get("viable") is False
            and fame_result.get("completed_kill") is not True
        ):
            state = dict(state)
            results = dict(results)
            fame_result = dict(fame_result)
            fame_result["retryable_failure"] = True
            results[_FAME_RECOVERY_POLICY.policy_id] = fame_result
            state["campaign_research_results"] = results
            cooldowns = dict(
                state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
            )
            cooldowns[_FAME_RECOVERY_POLICY.policy_id] = max(
                int(cooldowns.get(_FAME_RECOVERY_POLICY.policy_id) or 0),
                _RESEARCH_ABSENCE_RETRY_COOLDOWNS[
                    _FAME_RECOVERY_POLICY.policy_id
                ],
            )
            state[_RESEARCH_ABSENCE_COOLDOWN_KEY] = cooldowns
    if (
        previous_revision < 129
        and state.get("campaign_last_policy")
        == _FAME_RECOVERY_LOTUS_POLICY.policy_id
    ):
        results = _campaign_research_results(state)
        lotus_result = results.get(_FAME_RECOVERY_LOTUS_POLICY.policy_id)
        if (
            isinstance(lotus_result, Mapping)
            and lotus_result.get("boot_id") == state.get("world_boot_id")
            and lotus_result.get("viable") is False
            and lotus_result.get("completed_kill") is not True
        ):
            state = dict(state)
            results = dict(results)
            lotus_result = dict(lotus_result)
            lotus_result["fatal_failure"] = True
            lotus_result["level"] = _level(state)
            lotus_result.pop("retryable_failure", None)
            results[_FAME_RECOVERY_LOTUS_POLICY.policy_id] = lotus_result
            state["campaign_research_results"] = results
            cooldowns = dict(
                state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
            )
            cooldowns.pop(_FAME_RECOVERY_LOTUS_POLICY.policy_id, None)
            if cooldowns:
                state[_RESEARCH_ABSENCE_COOLDOWN_KEY] = cooldowns
            else:
                state.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
    if previous_revision <= _CAMPAIGN_POLICY_REVISION:
        state = _repair_source_special_level_ceiling_evidence(state)
    original_research_results = dict(
        state.get("campaign_research_results") or {}
    )
    research_results = dict(original_research_results)
    crowd_abort_reason = str(
        state.get("campaign_fastwalk_abort_reason") or ""
    )
    crowd_policy_id = state.get("campaign_last_policy")
    if (
        isinstance(crowd_policy_id, str)
        and crowd_abort_reason.startswith(_FIELD_ASSIST_CROWD_ABORT_PREFIX)
        and crowd_policy_id in research_results
    ):
        # A combat-assist abort can leave a viable consideration in the
        # checkpoint even though the hunt never completed. Repair that stale
        # promotion before selecting the next bounded segment.
        state = dict(state)
        research_results.pop(crowd_policy_id, None)
        if research_results:
            state["campaign_research_results"] = research_results
        else:
            state.pop("campaign_research_results", None)
        absence_cooldowns = dict(
            state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
        )
        absence_cooldowns.pop(crowd_policy_id, None)
        if absence_cooldowns:
            state[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
        else:
            state.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
    crowd_cooldowns = dict(
        state.get(_RESEARCH_CROWD_COOLDOWN_KEY) or {}
    )
    if (
        isinstance(crowd_policy_id, str)
        and state.get("campaign_fastwalk_crowded") is True
        and crowd_abort_reason.startswith(_FIELD_ROOM_CROWD_ABORT_PREFIX)
        and crowd_policy_id not in research_results
        and crowd_policy_id in crowd_cooldowns
        and int(crowd_cooldowns.get(crowd_policy_id) or 0) > 0
    ):
        # A pre-fix checkpoint may have lost only the result while retaining
        # its crowd marker and cooldown. Reconstruct the durable evidence so
        # the next selection can rotate instead of replaying that target.
        state = dict(state)
        research_results[crowd_policy_id] = {
            "observed": False,
            "viable": False,
            "crowded": True,
            "boot_id": state.get("world_boot_id"),
        }
        state["campaign_research_results"] = research_results
        original_research_results = dict(research_results)
    deep_probe_result = research_results.get(
        _MORIA_DEEP_SANCTUARY_THIEF_PROBE_POLICY_ID
    )
    if (
        isinstance(deep_probe_result, dict)
        and deep_probe_result.get("boot_id") == state.get("world_boot_id")
        and deep_probe_result.get("observed") is False
        and deep_probe_result.get("viable") is False
        and not any(
            deep_probe_result.get(key)
            for key in (
                "absent",
                "route_hazard",
                "crowded",
                "unattackable",
                "target_vnum_mismatch",
            )
        )
    ):
        # Older deep probes used a research execution and therefore lacked
        # the generic unobserved-hunt migration. Convert that legacy result
        # into the same temporary absence evidence produced by new probes.
        state = dict(state)
        migrated_deep_probe = dict(deep_probe_result)
        migrated_deep_probe["absent"] = True
        migrated_deep_probe["unobserved"] = True
        research_results[_MORIA_DEEP_SANCTUARY_THIEF_PROBE_POLICY_ID] = (
            migrated_deep_probe
        )
        state["campaign_research_results"] = research_results
        original_research_results = dict(research_results)
    previous_revision = int(state.get("campaign_policy_revision", 0))
    unobserved_policy_ids = {
        policy_id
        for policy_id, result in research_results.items()
        if (
            isinstance(result, dict)
            and result.get("observed") is False
            and not result.get("absent")
            and not result.get("route_hazard")
            and not result.get("crowded")
            and not result.get("arena_empty")
            and not (
                previous_revision < 112
                and _is_research_absence_retry_policy(policy_id)
                and result.get("completed_kill") is False
                and result.get("boot_id") == state.get("world_boot_id")
            )
        )
    }
    if unobserved_policy_ids:
        state = dict(state)
        state["campaign_research_results"] = {
            policy_id: result
            for policy_id, result in research_results.items()
            if policy_id not in unobserved_policy_ids
        }
        if not state["campaign_research_results"]:
            state.pop("campaign_research_results")
    if previous_revision < 112:
        # A research hunt that ended without a consider outcome was previously
        # recorded as a generic failed hunt, which allowed an empty circuit to
        # repeat immediately. Migrate only same-reboot, unobserved hunt results
        # into the temporary absence rotation introduced by the merge logic.
        migrated_results = dict(
            state.get("campaign_research_results") or {}
        )
        absence_cooldowns = dict(
            state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
        )
        changed = False
        for policy_id, raw_result in list(migrated_results.items()):
            if not (
                _is_research_absence_retry_policy(policy_id)
                and isinstance(raw_result, dict)
                and raw_result.get("completed_kill") is False
                and raw_result.get("observed") is False
                and raw_result.get("boot_id") == state.get("world_boot_id")
                and not raw_result.get("absent")
                and not raw_result.get("route_hazard")
                and not raw_result.get("crowded")
                and not raw_result.get("unattackable")
            ):
                continue
            migrated_result = dict(raw_result)
            migrated_result["absent"] = True
            migrated_result["unobserved"] = True
            migrated_results[policy_id] = migrated_result
            retry_cooldown = _research_absence_retry_cooldown(policy_id)
            if retry_cooldown is None:
                continue
            absence_cooldowns[policy_id] = retry_cooldown
            changed = True
        if changed:
            state = dict(state)
            state["campaign_research_results"] = migrated_results
            state[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
    absence_cooldowns = dict(
        state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
    )
    for policy_id, result in dict(
        state.get("campaign_research_results") or {}
    ).items():
        retry_cooldown = _research_absence_retry_cooldown(policy_id)
        if (
            retry_cooldown is not None
            and isinstance(result, dict)
            and (
                result.get("absent")
                or result.get("route_hazard")
                == _DYNAMIC_FIELD_ROUTE_HAZARD_ABORT_REASON
                or (
                    result.get("route_hazard")
                    != _SOURCE_RANKED_RUNTIME_BOUNDARY_ROUTE_HAZARD
                    and _is_retryable_source_ranked_route_hazard(
                        str(policy_id),
                        result.get("route_hazard"),
                    )
                )
            )
        ):
            absence_cooldowns.setdefault(policy_id, retry_cooldown)
    if absence_cooldowns != dict(
        state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
    ):
        state = dict(state)
        state[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
    state = _mark_retryable_research_failures(state)

    # A no-combat research probe that has already fled an unexpected attacker
    # is route-risk evidence. Preserve the current checkpoint's result instead
    # of allowing a reconnect or maintenance pass to replay the same hazard.
    if (
        state.get("campaign_policy_revision") == _CAMPAIGN_POLICY_REVISION
        and str(state.get("campaign_fastwalk_abort_reason") or "").startswith(
            _DYNAMIC_FIELD_ROUTE_HAZARD_ABORT_REASON
        )
    ):
        policy_id = state.get("campaign_last_policy")
        if isinstance(policy_id, str) and policy_id:
            current_results = _campaign_research_results(state)
            if policy_id not in current_results:
                state = dict(state)
                current_results[policy_id] = {
                    "observed": False,
                    "viable": False,
                    "route_hazard": state["campaign_fastwalk_abort_reason"],
                    "boot_id": state.get("world_boot_id"),
                }
                state["campaign_research_results"] = current_results

    if (
        state.get("campaign_policy_revision") == _CAMPAIGN_POLICY_REVISION
        and not _sanctuary_deep_route_migration_candidate(state)
    ):
        current_route_policy = state.get("campaign_last_policy")
        if (
            current_route_policy in _GALAXY_ROUTE_HAZARD_POLICY_IDS
            and not state.get(_HARD_ROUTE_HAZARD_REPAIR_KEY)
            and not (
                isinstance(
                    state.get(_SHADOW_GROVE_ROUTE_HAZARD_KEY),
                    Mapping,
                )
                and state[_SHADOW_GROVE_ROUTE_HAZARD_KEY].get("boot_id")
                == state.get("world_boot_id")
            )
        ):
            # The hard-hazard policy supersedes the old below-band waiver.
            # Clear only the pre-fix generic dynamic result once; explicit
            # source-preflight evidence remains a durable route block.
            repaired = dict(state)
            current_results = _campaign_research_results(state)
            current_result = current_results.get(current_route_policy)
            stale_dynamic_hazard = (
                isinstance(current_result, dict)
                and current_result.get("route_hazard")
                == _DYNAMIC_FIELD_ROUTE_HAZARD_ABORT_REASON
            )
            if stale_dynamic_hazard:
                repaired_results = dict(current_results)
                repaired_results.pop(str(current_route_policy), None)
                if repaired_results:
                    repaired["campaign_research_results"] = repaired_results
                else:
                    repaired.pop("campaign_research_results", None)
                absence_cooldowns = dict(
                    repaired.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
                )
                absence_cooldowns.pop(str(current_route_policy), None)
                if absence_cooldowns:
                    repaired[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
                else:
                    repaired.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
                if (
                    repaired.get("campaign_fastwalk_abort_reason")
                    == _DYNAMIC_FIELD_ROUTE_HAZARD_ABORT_REASON
                ):
                    repaired.pop("campaign_fastwalk_abort_reason", None)
                repaired.pop("campaign_fastwalk_target_absent", None)
            repaired[_HARD_ROUTE_HAZARD_REPAIR_KEY] = True
            return repaired
        current_route_abort = str(
            state.get("campaign_fastwalk_abort_reason") or ""
        )
        current_route_result = _campaign_research_results(state).get(
            current_route_policy
        )
        current_route_hazard = (
            str(current_route_result.get("route_hazard") or "")
            if isinstance(current_route_result, dict)
            else ""
        )
        if (
            current_route_policy
            in {
                _HIGHLAND_KEEPER_POLICY_ID,
                _HIGHLAND_KEEPER_HUNT_POLICY_ID,
            }
            and (
                current_route_abort
                == _DYNAMIC_FIELD_ROUTE_HAZARD_ABORT_REASON
                or current_route_hazard
                == _DYNAMIC_FIELD_ROUTE_HAZARD_ABORT_REASON
            )
            and not state.get(_HIGHLAND_KEEPER_ROUTE_REPAIR_KEY)
        ):
            repaired = dict(state)
            repaired_results = _campaign_research_results(repaired)
            repaired_results.pop(_HIGHLAND_KEEPER_POLICY_ID, None)
            repaired_results.pop(_HIGHLAND_KEEPER_HUNT_POLICY_ID, None)
            if repaired_results:
                repaired["campaign_research_results"] = repaired_results
            else:
                repaired.pop("campaign_research_results", None)
            absence_cooldowns = dict(
                repaired.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
            )
            absence_cooldowns.pop(_HIGHLAND_KEEPER_POLICY_ID, None)
            absence_cooldowns.pop(_HIGHLAND_KEEPER_HUNT_POLICY_ID, None)
            if absence_cooldowns:
                repaired[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
            else:
                repaired.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
            repaired.pop("campaign_fastwalk_target_absent", None)
            repaired.pop("campaign_fastwalk_abort_reason", None)
            repaired[_HIGHLAND_KEEPER_ROUTE_REPAIR_KEY] = True
            return repaired
        if (
            current_route_policy == _HIGHLAND_KEEPER_HUNT_POLICY_ID
            and current_route_abort.startswith(
                "field combat aborted after unapproved attacker "
                "'The Keeper of the Tower'"
            )
            and not state.get(_HIGHLAND_KEEPER_IDENTITY_REPAIR_KEY)
        ):
            repaired = dict(state)
            repaired["campaign_last_policy"] = _HIGHLAND_KEEPER_POLICY_ID
            repaired.pop("campaign_fastwalk_target_absent", None)
            repaired.pop("campaign_fastwalk_abort_reason", None)
            repaired[_HIGHLAND_KEEPER_IDENTITY_REPAIR_KEY] = True
            return repaired
        cleared_research_policies = {
            str(policy_id)
            for policy_id in state.get(_CLEARED_RESEARCH_POLICIES_KEY, ())
        }
        research_results = _campaign_research_results(state)
        failed_jailor_hunt = (
            state.get("campaign_last_policy") == _HIGHTOWER_JAILOR_HUNT_POLICY_ID
            and isinstance(
                research_results.get(_HIGHTOWER_JAILOR_HUNT_POLICY_ID),
                dict,
            )
            and research_results[_HIGHTOWER_JAILOR_HUNT_POLICY_ID].get(
                "viable"
            )
            is True
            and not state.get("campaign_objective_kills")
            and str(state.get("campaign_fastwalk_abort_reason") or "").startswith(
                "field combat aborted"
            )
        )
        if not cleared_research_policies and failed_jailor_hunt:
            repaired = dict(state)
            repaired_results = dict(research_results)
            repaired_results[_HIGHTOWER_JAILOR_HUNT_POLICY_ID] = {
                **repaired_results[_HIGHTOWER_JAILOR_HUNT_POLICY_ID],
                "viable": False,
                "completed_kill": False,
            }
            repaired["campaign_research_results"] = repaired_results
            return repaired
        stale_jailor_evidence = any(
            isinstance(research_results.get(policy_id), dict)
            and research_results[policy_id].get("absent")
            for policy_id in (
                _HIGHTOWER_JAILOR_POLICY_ID,
                _HIGHTOWER_JAILOR_HUNT_POLICY_ID,
            )
        ) or bool(state.get("campaign_fastwalk_target_absent"))
        if not cleared_research_policies and stale_jailor_evidence:
            repaired = dict(state)
            for policy_id in (
                _HIGHTOWER_JAILOR_POLICY_ID,
                _HIGHTOWER_JAILOR_HUNT_POLICY_ID,
            ):
                research_results.pop(policy_id, None)
            if research_results:
                repaired["campaign_research_results"] = research_results
            else:
                repaired.pop("campaign_research_results", None)
            absence_cooldowns = dict(
                repaired.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
            )
            absence_cooldowns.pop(_HIGHTOWER_JAILOR_POLICY_ID, None)
            absence_cooldowns.pop(_HIGHTOWER_JAILOR_HUNT_POLICY_ID, None)
            if absence_cooldowns:
                repaired[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
            else:
                repaired.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
            repaired[_CLEARED_RESEARCH_POLICIES_KEY] = [
                _HIGHTOWER_JAILOR_HUNT_POLICY_ID,
                _HIGHTOWER_JAILOR_POLICY_ID,
            ]
            repaired.pop("campaign_fastwalk_target_absent", None)
            return repaired
        return state
    refreshed = {
        **state,
        "campaign_policy_revision": _CAMPAIGN_POLICY_REVISION,
        "campaign_stalled_segments": 0,
    }
    if previous_revision < _CAMPAIGN_POLICY_REVISION:
        # The starter now identifies DD4's "takes a swing at you" combat
        # messages before applying the ordinary source and damage gates. The
        # old parser quarantined this exact no-kill route result as if the
        # attacker were unknown. Reopen only same-boot, same-level source-
        # ranked results with that exact hazard; losses and other hazards stay
        # authoritative.
        current_level = _level(refreshed)
        swing_policy_ids = sorted(
            str(policy_id)
            for policy_id, raw_result in _campaign_research_results(
                refreshed
            ).items()
            if (
                str(policy_id).startswith(_SOURCE_RANKED_POLICY_PREFIX)
                and str(policy_id).endswith(f"-{current_level}")
                and isinstance(raw_result, Mapping)
                and raw_result.get("boot_id") == refreshed.get("world_boot_id")
                and raw_result.get("observed") is False
                and raw_result.get("viable") is False
                and raw_result.get("completed_kill") is not True
                and raw_result.get("fatal_failure") is not True
                and raw_result.get("xp_loss_observed") is not True
                and raw_result.get("campaign_xp_loss_observed") is not True
                and raw_result.get("route_hazard")
                == _SOURCE_RANKED_SWING_ATTACK_ROUTE_HAZARD
            )
        )
        if swing_policy_ids:
            research_results = dict(_campaign_research_results(refreshed))
            superseded_results = {
                policy_id: dict(research_results.pop(policy_id))
                for policy_id in swing_policy_ids
            }
            refreshed = dict(refreshed)
            if research_results:
                refreshed["campaign_research_results"] = research_results
            else:
                refreshed.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                for policy_id in swing_policy_ids:
                    cooldowns.pop(policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            cleared = {
                str(policy_id)
                for policy_id in refreshed.get(
                    _CLEARED_RESEARCH_POLICIES_KEY,
                    (),
                )
                if str(policy_id) not in swing_policy_ids
            }
            if cleared:
                refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(cleared)
            else:
                refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
            explicit_retry = refreshed.get(_EXPLICIT_RESEARCH_RETRY_KEY)
            if isinstance(explicit_retry, Mapping):
                retry_policy_ids = {
                    str(policy_id)
                    for policy_id in explicit_retry.get("policy_ids", ())
                    if str(policy_id) not in swing_policy_ids
                }
                if retry_policy_ids:
                    refreshed[_EXPLICIT_RESEARCH_RETRY_KEY] = {
                        **dict(explicit_retry),
                        "policy_ids": sorted(retry_policy_ids),
                    }
                else:
                    refreshed.pop(_EXPLICIT_RESEARCH_RETRY_KEY, None)
            if refreshed.get(_SOURCE_RANKED_RETRY_EXHAUSTED_KEY) in set(
                swing_policy_ids
            ):
                refreshed.pop(_SOURCE_RANKED_RETRY_EXHAUSTED_KEY, None)
                refreshed.pop(_SOURCE_RANKED_RETRY_EXHAUSTED_BOOT_KEY, None)
            if refreshed.get("campaign_last_policy") in set(swing_policy_ids):
                refreshed.pop("campaign_last_policy", None)
                refreshed.pop(_SOURCE_RANKED_CANDIDATE_KEY, None)
                for key in (
                    "campaign_fastwalk_abort_reason",
                    "campaign_fastwalk_target_absent",
                    "campaign_fastwalk_target_present_observed",
                    "campaign_fastwalk_crowded",
                    "campaign_fastwalk_consider_outcomes",
                    "campaign_fastwalk_route_hazards",
                ):
                    refreshed.pop(key, None)
            if not refreshed.get(_SOURCE_RANKED_REVALIDATION_POLICY_KEY):
                refreshed[_SOURCE_RANKED_REVALIDATION_POLICY_KEY] = (
                    swing_policy_ids[0]
                )
            refreshed[_SOURCE_RANKED_SWING_ATTACK_REVALIDATION_KEY] = {
                "policy_revision": _CAMPAIGN_POLICY_REVISION,
                "policy_ids": swing_policy_ids,
                "boot_id": refreshed.get("world_boot_id"),
                "level": current_level,
                "status": "reopened",
                "reason": (
                    "reopen the exact no-kill route evidence after teaching "
                    "the starter to identify DD4 swing attacks"
                ),
                "superseded_results": superseded_results,
            }
    if previous_revision < 217:
        # Revision 216 consumed the one bounded no-sanctuary fallback before
        # combat, then the generic hunt-stop builder incorrectly required the
        # missing reserve. Re-arm only that exact pre-combat abort. A real
        # exchange, XP loss, death, or objective kill remains authoritative.
        fallback = refreshed.get(
            _PROTECTION_RECOVERY_ORDINARY_FALLBACK_KEY
        )
        fallback_policy_id = (
            str(fallback.get("policy_id") or "")
            if isinstance(fallback, Mapping)
            else ""
        )
        fallback_boot_id = (
            fallback.get("boot_id")
            if isinstance(fallback, Mapping)
            else None
        )
        precombat_reserve_abort = bool(
            isinstance(fallback, Mapping)
            and fallback.get("attempted") is True
            and fallback_policy_id
            and fallback_policy_id
            == str(refreshed.get("campaign_last_policy") or "")
            and fallback_boot_id == refreshed.get("world_boot_id")
            and fallback.get("level") in {None, _level(refreshed)}
            and _FIELD_REQUIRED_SANCTUARY_ABORT_FRAGMENT
            in str(refreshed.get("campaign_fastwalk_abort_reason") or "")
            and not refreshed.get("campaign_objective_kills")
            and refreshed.get("dead") is not True
            and refreshed.get("campaign_died_during_segment") is not True
            and refreshed.get("xp_loss_observed") is not True
            and refreshed.get("campaign_xp_loss_observed") is not True
        )
        if precombat_reserve_abort:
            attempted_policy_ids = sorted(
                policy_id
                for policy_id in (
                    _source_ranked_protection_recovery_fallback_attempted_policy_ids(
                        fallback
                    )
                )
                if policy_id != fallback_policy_id
            )
            refreshed[_PROTECTION_RECOVERY_ORDINARY_FALLBACK_KEY] = {
                **dict(fallback),
                "attempted": False,
                "attempted_policy_ids": attempted_policy_ids,
                "rearmed_after_policy_revision": 217,
            }
            if (
                refreshed.get(_SOURCE_RANKED_RETRY_EXHAUSTED_KEY)
                == fallback_policy_id
                and refreshed.get(_SOURCE_RANKED_RETRY_EXHAUSTED_BOOT_KEY)
                in {None, fallback_boot_id}
            ):
                refreshed.pop(_SOURCE_RANKED_RETRY_EXHAUSTED_KEY, None)
                refreshed.pop(_SOURCE_RANKED_RETRY_EXHAUSTED_BOOT_KEY, None)
            results = _campaign_research_results(refreshed)
            result = results.get(fallback_policy_id)
            if (
                isinstance(result, Mapping)
                and result.get("boot_id") == fallback_boot_id
                and result.get("completed_kill") is not True
                and result.get("protection_required") == "sanctuary"
            ):
                corrected_result = dict(result)
                corrected_result.pop("protection_required", None)
                results[fallback_policy_id] = corrected_result
                refreshed["campaign_research_results"] = results
            refreshed.pop("campaign_fastwalk_abort_reason", None)
    if previous_revision < 218:
        # A successful independent hunt can clear the protection requirement
        # even when it differs from the fallback policy selected earlier. The
        # fallback has no authority once its parent requirement is gone.
        fallback = refreshed.get(
            _PROTECTION_RECOVERY_ORDINARY_FALLBACK_KEY
        )
        protection = refreshed.get(_PROTECTION_RECOVERY_KEY)
        if isinstance(fallback, Mapping) and not isinstance(
            protection,
            Mapping,
        ):
            stale_policy_id = str(fallback.get("policy_id") or "")
            stale_boot_id = fallback.get("boot_id")
            refreshed.pop(
                _PROTECTION_RECOVERY_ORDINARY_FALLBACK_KEY,
                None,
            )
            if (
                stale_policy_id
                and refreshed.get(_SOURCE_RANKED_RETRY_EXHAUSTED_KEY)
                == stale_policy_id
                and refreshed.get(_SOURCE_RANKED_RETRY_EXHAUSTED_BOOT_KEY)
                in {None, stale_boot_id}
            ):
                refreshed.pop(_SOURCE_RANKED_RETRY_EXHAUSTED_KEY, None)
                refreshed.pop(_SOURCE_RANKED_RETRY_EXHAUSTED_BOOT_KEY, None)
    if previous_revision < 258:
        # The first Forest live probe found DD4's source display line but the
        # locator parser rejected its leading "Giant" adjective. Reopen only
        # that paired maintenance hazard; unrelated absence, loss, and
        # cooldown evidence must remain authoritative.
        maintenance_hazards = refreshed.get(_MAINTENANCE_ROUTE_HAZARDS_KEY)
        forest_hazard = (
            maintenance_hazards.get(_FOREST_LOCATOR_POLICY_ID)
            if isinstance(maintenance_hazards, Mapping)
            else None
        )
        if (
            isinstance(forest_hazard, Mapping)
            and forest_hazard.get("route_hazard")
            == _FOREST_OLD_LOCATOR_ABSENCE
        ):
            refreshed = dict(refreshed)
            stale_boot_id = forest_hazard.get("boot_id")
            remaining_hazards = dict(maintenance_hazards)
            remaining_hazards.pop(_FOREST_LOCATOR_POLICY_ID, None)
            if remaining_hazards:
                refreshed[_MAINTENANCE_ROUTE_HAZARDS_KEY] = remaining_hazards
            else:
                refreshed.pop(_MAINTENANCE_ROUTE_HAZARDS_KEY, None)

            results = _campaign_research_results(refreshed)
            forest_result = results.get(_FOREST_LOCATOR_POLICY_ID)
            removed_research_result = bool(
                isinstance(forest_result, Mapping)
                and forest_result.get("absent") is True
                and forest_result.get("observed") is False
                and forest_result.get("viable") is False
                and forest_result.get("completed_kill") is not True
                and forest_result.get("fatal_failure") is not True
                and (
                    stale_boot_id is None
                    or forest_result.get("boot_id") == stale_boot_id
                )
            )
            if removed_research_result:
                results.pop(_FOREST_LOCATOR_POLICY_ID, None)
                if results:
                    refreshed["campaign_research_results"] = results
                else:
                    refreshed.pop("campaign_research_results", None)

            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(_FOREST_LOCATOR_POLICY_ID, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)

            cleared = [
                str(policy_id)
                for policy_id in refreshed.get(
                    _CLEARED_RESEARCH_POLICIES_KEY,
                    (),
                )
                if str(policy_id) != _FOREST_LOCATOR_POLICY_ID
            ]
            if cleared:
                refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = cleared
            else:
                refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)

            upgrade_boot_id = refreshed.get(_PIERCING_WEAPON_UPGRADE_BOOT_KEY)
            if upgrade_boot_id in {None, stale_boot_id}:
                refreshed.pop(_PIERCING_WEAPON_UPGRADE_BOOT_KEY, None)
                refreshed.pop(_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY, None)

            transient_abort_reason = str(
                refreshed.get("campaign_fastwalk_abort_reason") or ""
            )
            if (
                transient_abort_reason == _FOREST_OLD_LOCATOR_ABSENCE
                or refreshed.get("campaign_last_policy")
                == _FOREST_LOCATOR_POLICY_ID
            ):
                if (
                    refreshed.get("campaign_last_policy")
                    == _FOREST_LOCATOR_POLICY_ID
                ):
                    refreshed.pop("campaign_last_policy", None)
                for key in (
                    "campaign_fastwalk_abort_reason",
                    "campaign_fastwalk_target_absent",
                    "campaign_fastwalk_target_present_observed",
                    "campaign_fastwalk_crowded",
                    "campaign_fastwalk_consider_outcomes",
                ):
                    refreshed.pop(key, None)

            refreshed[_FOREST_LOCATOR_REPAIR_KEY] = {
                "from_policy_revision": previous_revision,
                "policy_revision": 258,
                "policy_id": _FOREST_LOCATOR_POLICY_ID,
                "boot_id": stale_boot_id or refreshed.get("world_boot_id"),
                "old_route_hazard": _FOREST_OLD_LOCATOR_ABSENCE,
                "removed_research_result": removed_research_result,
                "status": "reopened",
            }
    if previous_revision < 259:
        # Revision 258 repaired the parser's leading-adjective false negative.
        # The first corrected probe then exposed River bed as a real, source-
        # mapped wanderer room, where the old exclusion still created a stale
        # route veto. Reopen only that exact derived hazard and retain the
        # original parser-repair marker as separate evidence.
        maintenance_hazards = refreshed.get(_MAINTENANCE_ROUTE_HAZARDS_KEY)
        forest_hazard = (
            maintenance_hazards.get(_FOREST_LOCATOR_POLICY_ID)
            if isinstance(maintenance_hazards, Mapping)
            else None
        )
        stale_boot_id = (
            forest_hazard.get("boot_id")
            if isinstance(forest_hazard, Mapping)
            else None
        )
        if (
            isinstance(forest_hazard, Mapping)
            and forest_hazard.get("route_hazard")
            == _FOREST_EXCLUDED_ROOM_LOCATOR_HAZARD
            and stale_boot_id == refreshed.get("world_boot_id")
        ):
            refreshed = dict(refreshed)
            remaining_hazards = dict(maintenance_hazards)
            remaining_hazards.pop(_FOREST_LOCATOR_POLICY_ID, None)
            if remaining_hazards:
                refreshed[_MAINTENANCE_ROUTE_HAZARDS_KEY] = remaining_hazards
            else:
                refreshed.pop(_MAINTENANCE_ROUTE_HAZARDS_KEY, None)

            results = _campaign_research_results(refreshed)
            forest_result = results.get(_FOREST_LOCATOR_POLICY_ID)
            removed_research_result = bool(
                isinstance(forest_result, Mapping)
                and forest_result.get("route_hazard")
                == _FOREST_EXCLUDED_ROOM_LOCATOR_HAZARD
                and forest_result.get("observed") is False
                and forest_result.get("viable") is False
                and forest_result.get("completed_kill") is not True
                and forest_result.get("fatal_failure") is not True
                and forest_result.get("boot_id") == stale_boot_id
            )
            if removed_research_result:
                results.pop(_FOREST_LOCATOR_POLICY_ID, None)
                if results:
                    refreshed["campaign_research_results"] = results
                else:
                    refreshed.pop("campaign_research_results", None)

            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(_FOREST_LOCATOR_POLICY_ID, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)

            cleared = [
                str(policy_id)
                for policy_id in refreshed.get(
                    _CLEARED_RESEARCH_POLICIES_KEY,
                    (),
                )
                if str(policy_id) != _FOREST_LOCATOR_POLICY_ID
            ]
            if cleared:
                refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = cleared
            else:
                refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)

            upgrade_boot_id = refreshed.get(_PIERCING_WEAPON_UPGRADE_BOOT_KEY)
            if upgrade_boot_id in {None, stale_boot_id}:
                refreshed.pop(_PIERCING_WEAPON_UPGRADE_BOOT_KEY, None)
                refreshed.pop(_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY, None)

            transient_abort_reason = str(
                refreshed.get("campaign_fastwalk_abort_reason") or ""
            )
            if (
                transient_abort_reason == _FOREST_EXCLUDED_ROOM_LOCATOR_HAZARD
                or refreshed.get("campaign_last_policy")
                == _FOREST_LOCATOR_POLICY_ID
            ):
                if (
                    refreshed.get("campaign_last_policy")
                    == _FOREST_LOCATOR_POLICY_ID
                ):
                    refreshed.pop("campaign_last_policy", None)
                for key in (
                    "campaign_fastwalk_abort_reason",
                    "campaign_fastwalk_target_absent",
                    "campaign_fastwalk_target_present_observed",
                    "campaign_fastwalk_crowded",
                    "campaign_fastwalk_consider_outcomes",
                ):
                    refreshed.pop(key, None)

            refreshed[_FOREST_RIVER_BRANCH_REPAIR_KEY] = {
                "from_policy_revision": previous_revision,
                "policy_revision": 259,
                "policy_id": _FOREST_LOCATOR_POLICY_ID,
                "boot_id": stale_boot_id,
                "old_route_hazard": _FOREST_EXCLUDED_ROOM_LOCATOR_HAZARD,
                "removed_research_result": removed_research_result,
                "source_route_room_vnums": ["18028", "18029", "18030"],
                "status": "reopened",
            }
    if previous_revision < 260:
        # The first River-branch implementation skipped a crowded 18027 and
        # then tried to jump directly to 18029. Reopen only that exact route
        # cursor failure; the corrected source gate will now assess the crowd
        # before entering the poison-swarm rooms.
        maintenance_hazards = refreshed.get(_MAINTENANCE_ROUTE_HAZARDS_KEY)
        forest_hazard = (
            maintenance_hazards.get(_FOREST_LOCATOR_POLICY_ID)
            if isinstance(maintenance_hazards, Mapping)
            else None
        )
        stale_boot_id = (
            forest_hazard.get("boot_id")
            if isinstance(forest_hazard, Mapping)
            else None
        )
        if (
            isinstance(forest_hazard, Mapping)
            and forest_hazard.get("route_hazard")
            == "field route could not find GMCP exit to room 18029"
            and stale_boot_id == refreshed.get("world_boot_id")
        ):
            refreshed = dict(refreshed)
            remaining_hazards = dict(maintenance_hazards)
            remaining_hazards.pop(_FOREST_LOCATOR_POLICY_ID, None)
            if remaining_hazards:
                refreshed[_MAINTENANCE_ROUTE_HAZARDS_KEY] = remaining_hazards
            else:
                refreshed.pop(_MAINTENANCE_ROUTE_HAZARDS_KEY, None)

            results = _campaign_research_results(refreshed)
            forest_result = results.get(_FOREST_LOCATOR_POLICY_ID)
            removed_research_result = bool(
                isinstance(forest_result, Mapping)
                and forest_result.get("crowded") is True
                and forest_result.get("observed") is False
                and forest_result.get("viable") is False
                and forest_result.get("completed_kill") is not True
                and forest_result.get("boot_id") == stale_boot_id
            )
            if removed_research_result:
                results.pop(_FOREST_LOCATOR_POLICY_ID, None)
                if results:
                    refreshed["campaign_research_results"] = results
                else:
                    refreshed.pop("campaign_research_results", None)

            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(_FOREST_LOCATOR_POLICY_ID, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)

            crowd_attempts = dict(
                refreshed.get(_SOURCE_RANKED_CROWD_ATTEMPTS_KEY) or {}
            )
            crowd_attempts.pop(_FOREST_LOCATOR_POLICY_ID, None)
            if crowd_attempts:
                refreshed[_SOURCE_RANKED_CROWD_ATTEMPTS_KEY] = crowd_attempts
            else:
                refreshed.pop(_SOURCE_RANKED_CROWD_ATTEMPTS_KEY, None)

            cleared = [
                str(policy_id)
                for policy_id in refreshed.get(
                    _CLEARED_RESEARCH_POLICIES_KEY,
                    (),
                )
                if str(policy_id) != _FOREST_LOCATOR_POLICY_ID
            ]
            if cleared:
                refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = cleared
            else:
                refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)

            upgrade_boot_id = refreshed.get(_PIERCING_WEAPON_UPGRADE_BOOT_KEY)
            if upgrade_boot_id in {None, stale_boot_id}:
                refreshed.pop(_PIERCING_WEAPON_UPGRADE_BOOT_KEY, None)
                refreshed.pop(_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY, None)

            transient_abort_reason = str(
                refreshed.get("campaign_fastwalk_abort_reason") or ""
            )
            if (
                transient_abort_reason
                == "field route could not find GMCP exit to room 18029"
                or refreshed.get("campaign_last_policy")
                == _FOREST_LOCATOR_POLICY_ID
            ):
                if (
                    refreshed.get("campaign_last_policy")
                    == _FOREST_LOCATOR_POLICY_ID
                ):
                    refreshed.pop("campaign_last_policy", None)
                for key in (
                    "campaign_fastwalk_abort_reason",
                    "campaign_fastwalk_target_absent",
                    "campaign_fastwalk_target_present_observed",
                    "campaign_fastwalk_crowded",
                    "campaign_fastwalk_consider_outcomes",
                ):
                    refreshed.pop(key, None)

            refreshed[_FOREST_ROUTE_CURSOR_REPAIR_KEY] = {
                "from_policy_revision": previous_revision,
                "policy_revision": 260,
                "policy_id": _FOREST_LOCATOR_POLICY_ID,
                "boot_id": stale_boot_id,
                "old_route_hazard": (
                    "field route could not find GMCP exit to room 18029"
                ),
                "removed_research_result": removed_research_result,
                "source_route_room_vnums": [
                    "18027",
                    "18028",
                    "18029",
                    "18030",
                ],
                "status": "reopened",
            }
    if previous_revision < _SOURCE_RANKED_DAMAGE_WINDOW_REVALIDATION_REVISION:
        # The first New Ofcol probe was source-safe and sanctuary-protected,
        # but the old fixed 12-action ceiling rejected a healthy, unarmed
        # target after only a short zero-damage exchange. Reopen only that
        # exact current-reboot loss for the measured 36-action retry; retain
        # the original loss and research result as superseded evidence.
        policy_id = _SOURCE_RANKED_DAMAGE_WINDOW_REVALIDATION_POLICY_ID
        result = _campaign_research_results(refreshed).get(policy_id)
        loss_record = _source_ranked_xp_loss_record(refreshed, policy_id)
        protection = refreshed.get(_PROTECTION_RECOVERY_KEY)
        abort_reason = str(
            refreshed.get("campaign_fastwalk_abort_reason") or ""
        )
        raw_room_flags = refreshed.get("room_flags")
        room_flags = (
            {str(flag).casefold() for flag in raw_room_flags}
            if isinstance(raw_room_flags, Collection)
            and not isinstance(raw_room_flags, (str, bytes))
            else set()
        )
        try:
            hp = int(refreshed.get("hp") or 0)
        except (TypeError, ValueError):
            hp = 0
        if (
            _level(refreshed) == 24
            and refreshed.get("campaign_last_policy") == policy_id
            and refreshed.get(_SOURCE_RANKED_RETRY_EXHAUSTED_KEY) == policy_id
            and isinstance(result, Mapping)
            and result.get("boot_id") == refreshed.get("world_boot_id")
            and result.get("observed") is True
            and result.get("consider_viable") is True
            and result.get("completed_kill") is False
            and result.get("viable") is False
            and result.get("retryable_failure") is True
            and isinstance(loss_record, Mapping)
            and loss_record.get("boot_id") == refreshed.get("world_boot_id")
            and loss_record.get("level") == _level(refreshed)
            and _source_ranked_xp_loss_count(loss_record) == 1
            and _source_ranked_xp_loss_was_protected(loss_record)
            and isinstance(protection, Mapping)
            and protection.get("boot_id") == refreshed.get("world_boot_id")
            and protection.get("level") in {None, _level(refreshed)}
            and protection.get("policy_id") == policy_id
            and abort_reason.startswith("field damage-window probe for '")
            and "protected source-backed" in abort_reason
            and "live target HP ceiling" in abort_reason
            and "outside the executable kill window" in abort_reason
            and refreshed.get("campaign_fastwalk_sanctuary_consumed_in_combat")
            is True
            and str(refreshed.get("room_vnum") or "") == "3054"
            and {"healing", "safe"}.issubset(room_flags)
            and refreshed.get("enemies") in (None, [])
            and not refreshed.get("combat_target")
            and refreshed.get("in_combat") is not True
            and refreshed.get("dead") is not True
            and refreshed.get("campaign_died_during_segment") is not True
            and not refreshed.get("campaign_objective_kills")
            and hp > 0
        ):
            refreshed = dict(refreshed)
            results = dict(_campaign_research_results(refreshed))
            superseded_result = dict(results.pop(policy_id))
            if results:
                refreshed["campaign_research_results"] = results
            else:
                refreshed.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            refreshed[_SOURCE_RANKED_DAMAGE_WINDOW_REVALIDATION_KEY] = {
                "policy_revision": (
                    _SOURCE_RANKED_DAMAGE_WINDOW_REVALIDATION_REVISION
                ),
                "policy_id": policy_id,
                "boot_id": refreshed.get("world_boot_id"),
                "level": _level(refreshed),
                "status": "pending",
                "reason": (
                    "reopen one exact unarmed sanctuary probe after the old "
                    "fixed action ceiling rejected a zero-damage exchange"
                ),
                "superseded_result": superseded_result,
                "superseded_loss_event_id": loss_record.get("loss_event_id"),
            }
            refreshed[_SOURCE_RANKED_REVALIDATION_POLICY_KEY] = policy_id
            if refreshed.get(_SOURCE_RANKED_RETRY_EXHAUSTED_KEY) == policy_id:
                refreshed.pop(_SOURCE_RANKED_RETRY_EXHAUSTED_KEY, None)
                refreshed.pop(_SOURCE_RANKED_RETRY_EXHAUSTED_BOOT_KEY, None)
            if refreshed.get("campaign_last_policy") == policy_id:
                refreshed.pop("campaign_last_policy", None)
            if refreshed.get("campaign_fastwalk_abort_reason") == abort_reason:
                refreshed.pop("campaign_fastwalk_abort_reason", None)
            for key in (
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
                "campaign_fastwalk_sanctuary_consumed_in_combat",
            ):
                refreshed.pop(key, None)
    if previous_revision < _SOURCE_RANKED_ALIGNMENT_CROWD_REVALIDATION_REVISION:
        # The measured retry reached the registered New Ofcol teller, but a
        # good-alignment dragonknight happened to share the room. DD4's
        # violence_update rejects that NPC-to-NPC assist before its special
        # procedure can act. Reopen only this exact no-kill crowd observation
        # after the target-specific source gate was corrected; retain both the
        # damage retry and crowd result as nested superseded evidence.
        policy_id = _SOURCE_RANKED_DAMAGE_WINDOW_REVALIDATION_POLICY_ID
        damage_marker = refreshed.get(
            _SOURCE_RANKED_DAMAGE_WINDOW_REVALIDATION_KEY
        )
        crowd_result = _campaign_research_results(refreshed).get(policy_id)
        abort_reason = str(
            refreshed.get("campaign_fastwalk_abort_reason") or ""
        )
        crowd_attempts = refreshed.get(_SOURCE_RANKED_CROWD_ATTEMPTS_KEY)
        crowd_attempt = (
            crowd_attempts.get(policy_id)
            if isinstance(crowd_attempts, Mapping)
            else None
        )
        try:
            crowd_attempt_count = int(
                crowd_attempt.get("count") or 0
            ) if isinstance(crowd_attempt, Mapping) else 0
            alignment = int(
                (refreshed.get("progress") or {}).get("alignment")
            )
            hp = int(refreshed.get("hp") or 0)
        except (AttributeError, TypeError, ValueError):
            crowd_attempt_count = alignment = hp = 0
        if (
            _level(refreshed) == 24
            and refreshed.get("campaign_last_policy") == policy_id
            and isinstance(damage_marker, Mapping)
            and damage_marker.get("policy_revision")
            == _SOURCE_RANKED_DAMAGE_WINDOW_REVALIDATION_REVISION
            and damage_marker.get("policy_id") == policy_id
            and damage_marker.get("boot_id") == refreshed.get("world_boot_id")
            and damage_marker.get("level") == _level(refreshed)
            and damage_marker.get("status") == "closed"
            and damage_marker.get("outcome") == "no_kill"
            and isinstance(damage_marker.get("superseded_result"), Mapping)
            and isinstance(crowd_result, Mapping)
            and crowd_result.get("boot_id") == refreshed.get("world_boot_id")
            and crowd_result.get("observed") is False
            and crowd_result.get("viable") is False
            and crowd_result.get("crowded") is True
            and crowd_attempt_count < _SOURCE_RANKED_CROWD_ROTATION_THRESHOLD
            and abort_reason.casefold()
            == (
                "field room contained 2 observed mobiles while evaluating "
                "'sluggish dragonhoard teller'"
            )
            and refreshed.get("campaign_fastwalk_target_present_observed")
            is True
            and refreshed.get("campaign_fastwalk_crowded") is True
            and alignment >= 300
            and str(refreshed.get("room_vnum") or "") == "3054"
            and {"healing", "safe"}.issubset(
                {
                    str(flag).casefold()
                    for flag in (refreshed.get("room_flags") or ())
                }
            )
            and refreshed.get("enemies") in (None, [])
            and not refreshed.get("combat_target")
            and refreshed.get("in_combat") is not True
            and refreshed.get("dead") is not True
            and refreshed.get("campaign_died_during_segment") is not True
            and not refreshed.get("campaign_objective_kills")
            and hp > 0
        ):
            refreshed = dict(refreshed)
            results = dict(_campaign_research_results(refreshed))
            superseded_crowd_result = dict(results.pop(policy_id))
            if results:
                refreshed["campaign_research_results"] = results
            else:
                refreshed.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            refreshed[_SOURCE_RANKED_DAMAGE_WINDOW_REVALIDATION_KEY] = {
                "policy_revision": (
                    _SOURCE_RANKED_ALIGNMENT_CROWD_REVALIDATION_REVISION
                ),
                "policy_id": policy_id,
                "boot_id": refreshed.get("world_boot_id"),
                "level": _level(refreshed),
                "status": "pending",
                "reason": (
                    "reopen one exact New Ofcol target after source-backed "
                    "positive-alignment crowd correction"
                ),
                "superseded_attempt": dict(damage_marker),
                "superseded_crowd_result": superseded_crowd_result,
            }
            refreshed[_SOURCE_RANKED_REVALIDATION_POLICY_KEY] = policy_id
            if refreshed.get("campaign_last_policy") == policy_id:
                refreshed.pop("campaign_last_policy", None)
            if refreshed.get("campaign_fastwalk_abort_reason") == abort_reason:
                refreshed.pop("campaign_fastwalk_abort_reason", None)
            for key in (
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
            ):
                refreshed.pop(key, None)
    if previous_revision < _SANCTUARY_SECOND_RESERVE_REFILL_REVALIDATION_REVISION:
        # The first second-reserve handoff carried one purple because the
        # normal count is reduced for characters without invisibility. That
        # exact no-loss attempt could not satisfy its two-item objective, so
        # reopen one corrected segment with the failed evidence nested.
        policy_id = _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
        marker = refreshed.get(_SANCTUARY_SECOND_RESERVE_REFILL_KEY)
        result = _campaign_research_results(refreshed).get(policy_id)
        reserve_result = _campaign_research_results(refreshed).get(
            _SOURCE_RANKED_SANCTUARY_RESERVE_POLICY.policy_id
        )
        where_checks = refreshed.get("campaign_fastwalk_where_area_checks")
        where_proved = any(
            isinstance(check, Mapping)
            and str(check.get("area_file") or "").casefold() == "moria.are"
            and str(check.get("scope") or "").casefold() == "current_area"
            and check.get("result") == "present"
            and check.get("room_vnum") == "4014"
            and check.get("source_mobile_vnum")
            == _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM
            and str(check.get("target") or "").casefold()
            == "large hobgoblin"
            for check in where_checks
        ) if isinstance(where_checks, Collection) and not isinstance(
            where_checks, (str, bytes)
        ) else False
        attempts = refreshed.get(_SANCTUARY_RESOURCE_ATTEMPTS_KEY)
        recovery_attempt = (
            attempts.get(policy_id)
            if isinstance(attempts, Mapping)
            else None
        )
        reserve_attempt = (
            attempts.get(_SOURCE_RANKED_SANCTUARY_RESERVE_POLICY.policy_id)
            if isinstance(attempts, Mapping)
            else None
        )
        try:
            recovery_attempt_count = int(
                recovery_attempt.get("count") or 0
            ) if isinstance(recovery_attempt, Mapping) else 0
            reserve_attempt_count = int(
                reserve_attempt.get("count") or 0
            ) if isinstance(reserve_attempt, Mapping) else 0
            hp = int(refreshed.get("hp") or 0)
            purple_count = _verified_combat_potion_count(refreshed, "purple")
        except (TypeError, ValueError):
            recovery_attempt_count = reserve_attempt_count = hp = purple_count = 0
        raw_room_flags = refreshed.get("room_flags")
        room_flags = {
            str(flag).casefold()
            for flag in raw_room_flags
        } if isinstance(raw_room_flags, Collection) and not isinstance(
            raw_room_flags, (str, bytes)
        ) else set()
        legacy_marker = (
            marker is None
            or (
                isinstance(marker, Mapping)
                and marker.get("boot_id") == refreshed.get("world_boot_id")
                and marker.get("level") == _level(refreshed)
                and marker.get("policy_id") == policy_id
                and marker.get("status") == "attempted"
                and not marker.get("policy_revision")
                and str(marker.get("reason") or "")
                == (
                    "reuse the proven generic recovery route for a second "
                    "purple after the dedicated reserve route was quarantined"
                )
            )
        )
        exact_failed_refill = bool(
            _level(refreshed) == 24
            and legacy_marker
            and isinstance(result, Mapping)
            and result.get("boot_id") == refreshed.get("world_boot_id")
            and result.get("observed") is True
            and result.get("viable") is False
            and result.get("completed_kill") is False
            and result.get("retryable_failure") is True
            and result.get("required_object_acquired") is not True
            and isinstance(reserve_result, Mapping)
            and reserve_result.get("boot_id")
            == refreshed.get("world_boot_id")
            and reserve_result.get("viable") is False
            and reserve_result.get("fatal_failure") is True
            and reserve_result.get("route_hazard")
            == "sanctuary resource route exhausted after 2 failed attempts"
            and recovery_attempt_count == 1
            and reserve_attempt_count >= _SANCTUARY_RESOURCE_MAX_ATTEMPTS
            and where_proved
            and "large hobgoblin"
            in {
                str(target).casefold()
                for target in refreshed.get(
                    "campaign_fastwalk_below_band_targets", ()
                )
            }
            and refreshed.get("campaign_fastwalk_target_present_observed")
            is True
            and refreshed.get("campaign_fastwalk_required_object_vnums") == []
            and not refreshed.get("campaign_objective_kills")
            and refreshed.get("campaign_fastwalk_abort_reason") in (None, "")
            and refreshed.get("campaign_fastwalk_crowded") is not True
            and refreshed.get("campaign_died_during_segment") is not True
            and refreshed.get("dead") is not True
            and refreshed.get("xp_loss_observed") is not True
            and refreshed.get("campaign_xp_loss_observed") is not True
            and _current_protection_recovery_marker_present(refreshed)
            and _state_has_sanctuary_reserve(refreshed)
            and not _state_has_blindness_recovery_reserve(refreshed)
            and purple_count == 1
            and str(refreshed.get("room_vnum") or "") == "3054"
            and {"healing", "safe"}.issubset(room_flags)
            and refreshed.get("enemies") in (None, [])
            and not refreshed.get("combat_target")
            and refreshed.get("in_combat") is not True
            and hp > 0
        )
        if exact_failed_refill:
            refreshed = dict(refreshed)
            results = dict(_campaign_research_results(refreshed))
            superseded_result = dict(results.pop(policy_id))
            if results:
                refreshed["campaign_research_results"] = results
            else:
                refreshed.pop("campaign_research_results", None)
            absence_cooldowns = dict(
                refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
            )
            absence_cooldowns.pop(policy_id, None)
            if absence_cooldowns:
                refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
            else:
                refreshed.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
            refreshed[_SANCTUARY_SECOND_RESERVE_REFILL_KEY] = {
                "policy_revision": (
                    _SANCTUARY_SECOND_RESERVE_REFILL_REVALIDATION_REVISION
                ),
                "policy_id": policy_id,
                "boot_id": refreshed.get("world_boot_id"),
                "level": _level(refreshed),
                "status": "pending",
                "requested_potion_count": 2,
                "reason": (
                    "reopen one second-reserve refill after the first handoff "
                    "requested only one potion"
                ),
                "superseded_marker": (
                    dict(marker) if isinstance(marker, Mapping) else None
                ),
                "superseded_result": superseded_result,
                "source_where_evidence": [
                    check for check in where_checks
                    if isinstance(check, Mapping)
                    and str(check.get("area_file") or "").casefold()
                    == "moria.are"
                    and str(check.get("scope") or "").casefold()
                    == "current_area"
                    and check.get("result") == "present"
                    and check.get("room_vnum") == "4014"
                    and check.get("source_mobile_vnum")
                    == _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM
                    and str(check.get("target") or "").casefold()
                    == "large hobgoblin"
                ],
            }
            if refreshed.get("campaign_last_policy") == policy_id:
                refreshed.pop("campaign_last_policy", None)
            for key in (
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
                "campaign_fastwalk_required_object_vnums",
                "campaign_fastwalk_where_area_checks",
                "campaign_fastwalk_where_relocation_attempts",
            ):
                refreshed.pop(key, None)
    if previous_revision < _SANCTUARY_DEEP_LOCATOR_REVALIDATION_REVISION:
        # The corrected deep Moria locator now includes the safe 4063 entrance
        # while keeping the poisoner and sentinel maze rooms out of the route.
        # Reopen only the exact no-loss terminal chain that reached 4014 and
        # was blocked because that safe endpoint was missing from the graph.
        policy_id = _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
        reserve_policy_id = _SOURCE_RANKED_SANCTUARY_RESERVE_POLICY.policy_id
        result = _campaign_research_results(refreshed).get(policy_id)
        reserve_result = _campaign_research_results(refreshed).get(
            reserve_policy_id
        )
        safe_locator = refreshed.get(_SANCTUARY_SAFE_LOCATOR_REVALIDATION_KEY)
        transit_revalidation = refreshed.get(
            _SANCTUARY_COMBAT_ONLY_TRANSIT_REVALIDATION_KEY
        )
        attempts = refreshed.get(_SANCTUARY_RESOURCE_ATTEMPTS_KEY)
        recovery_attempt = (
            attempts.get(policy_id) if isinstance(attempts, Mapping) else None
        )
        protection = refreshed.get(_PROTECTION_RECOVERY_KEY)
        raw_room_flags = refreshed.get("room_flags")
        room_flags = (
            {str(flag).casefold() for flag in raw_room_flags}
            if isinstance(raw_room_flags, Collection)
            and not isinstance(raw_room_flags, (str, bytes))
            else set()
        )
        try:
            recovery_attempt_count = (
                int(recovery_attempt.get("count") or 0)
                if isinstance(recovery_attempt, Mapping)
                else 0
            )
            hp = int(refreshed.get("hp") or 0)
        except (TypeError, ValueError):
            recovery_attempt_count = hp = 0
        superseded_transit_result = (
            transit_revalidation.get("superseded_result")
            if isinstance(transit_revalidation, Mapping)
            else None
        )
        if (
            not refreshed.get(_SANCTUARY_DEEP_LOCATOR_REVALIDATION_KEY)
            and _level(refreshed) == 24
            and isinstance(result, Mapping)
            and result.get("boot_id") == refreshed.get("world_boot_id")
            and result.get("level") == _level(refreshed)
            and result.get("observed") is True
            and result.get("viable") is False
            and result.get("completed_kill") is False
            and result.get("fatal_failure") is True
            and result.get("route_hazard") == _SANCTUARY_RESOURCE_EXHAUSTED_HAZARD
            and result.get("required_object_acquired") is not True
            and isinstance(reserve_result, Mapping)
            and reserve_result.get("boot_id") == refreshed.get("world_boot_id")
            and reserve_result.get("level") == _level(refreshed)
            and reserve_result.get("observed") is True
            and reserve_result.get("viable") is False
            and reserve_result.get("completed_kill") is False
            and reserve_result.get("fatal_failure") is True
            and reserve_result.get("route_hazard")
            == _SANCTUARY_RESOURCE_EXHAUSTED_HAZARD
            and isinstance(recovery_attempt, Mapping)
            and recovery_attempt.get("boot_id") == refreshed.get("world_boot_id")
            and recovery_attempt.get("level") == _level(refreshed)
            and recovery_attempt_count >= _SANCTUARY_RESOURCE_MAX_ATTEMPTS
            and isinstance(safe_locator, Mapping)
            and safe_locator.get("policy_revision")
            == _SANCTUARY_SAFE_LOCATOR_REVALIDATION_REVISION
            and safe_locator.get("policy_id") == reserve_policy_id
            and safe_locator.get("boot_id") == refreshed.get("world_boot_id")
            and safe_locator.get("level") == _level(refreshed)
            and safe_locator.get("status") == "reopened"
            and safe_locator.get("safe_endpoint_room_vnums") == [4064, 4063]
            and isinstance(transit_revalidation, Mapping)
            and transit_revalidation.get("policy_revision")
            == _SANCTUARY_COMBAT_ONLY_TRANSIT_REVALIDATION_REVISION
            and transit_revalidation.get("policy_id") == reserve_policy_id
            and transit_revalidation.get("boot_id")
            == refreshed.get("world_boot_id")
            and transit_revalidation.get("level") == _level(refreshed)
            and transit_revalidation.get("status") == "attempted"
            and isinstance(superseded_transit_result, Mapping)
            and superseded_transit_result.get("fatal_failure") is True
            and superseded_transit_result.get("route_hazard")
            == _SANCTUARY_RESOURCE_EXHAUSTED_HAZARD
            and isinstance(protection, Mapping)
            and protection.get("boot_id") == refreshed.get("world_boot_id")
            and protection.get("level") in {None, _level(refreshed)}
            and not _state_has_sanctuary_reserve(refreshed)
            and not refreshed.get("campaign_objective_kills")
            and refreshed.get("campaign_died_during_segment") is not True
            and refreshed.get("dead") is not True
            and refreshed.get("in_combat") is not True
            and refreshed.get("enemies") in (None, [])
            and not refreshed.get("combat_target")
            and str(refreshed.get("room_vnum") or "") == "3054"
            and {"healing", "safe"}.issubset(room_flags)
            and hp > 0
        ):
            refreshed = dict(refreshed)
            results = dict(_campaign_research_results(refreshed))
            superseded_result = dict(results.pop(policy_id))
            if results:
                refreshed["campaign_research_results"] = results
            else:
                refreshed.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            cleared = [
                str(candidate_id)
                for candidate_id in refreshed.get(
                    _CLEARED_RESEARCH_POLICIES_KEY, ()
                )
                if str(candidate_id) != policy_id
            ]
            if cleared:
                refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = cleared
            else:
                refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
            refreshed[_SANCTUARY_DEEP_LOCATOR_REVALIDATION_KEY] = {
                "policy_revision": (
                    _SANCTUARY_DEEP_LOCATOR_REVALIDATION_REVISION
                ),
                "policy_id": policy_id,
                "boot_id": refreshed.get("world_boot_id"),
                "level": _level(refreshed),
                "status": "pending",
                "source_mobile_vnum": _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
                "safe_endpoint_room_vnums": [4064, 4063],
                "observed_block_room_vnum": "4014",
                "superseded_result": superseded_result,
                "superseded_transit_result": dict(superseded_transit_result),
            }
            if refreshed.get("campaign_last_policy") == policy_id:
                refreshed.pop("campaign_last_policy", None)
            for key in (
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
                "campaign_fastwalk_where_area_checks",
                "campaign_fastwalk_where_relocation_attempts",
            ):
                refreshed.pop(key, None)
    if previous_revision < _SANCTUARY_SOURCE_SAFE_BYSTANDER_REVALIDATION_REVISION:
        # The first revision-276 live retry reached the repaired Moria
        # endpoint, then stopped on warrior 4051. Source update.c proves that
        # this known level-5..9 aggressive bystander cannot attack or join a
        # level-24 player fight. Reopen only that exact false-positive once;
        # retain the failed run and attempt count inside the marker.
        policy_id = _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
        result = _campaign_research_results(refreshed).get(policy_id)
        deep_locator = refreshed.get(_SANCTUARY_DEEP_LOCATOR_REVALIDATION_KEY)
        attempts = refreshed.get(_SANCTUARY_RESOURCE_ATTEMPTS_KEY)
        recovery_attempt = (
            attempts.get(policy_id) if isinstance(attempts, Mapping) else None
        )
        raw_room_flags = refreshed.get("room_flags")
        room_flags = (
            {str(flag).casefold() for flag in raw_room_flags}
            if isinstance(raw_room_flags, Collection)
            and not isinstance(raw_room_flags, (str, bytes))
            else set()
        )
        try:
            recovery_attempt_count = (
                int(recovery_attempt.get("count") or 0)
                if isinstance(recovery_attempt, Mapping)
                else 0
            )
            hp = int(refreshed.get("hp") or 0)
        except (TypeError, ValueError):
            recovery_attempt_count = hp = 0
        abort_reason = str(refreshed.get("campaign_fastwalk_abort_reason") or "")
        route_hazards = refreshed.get("campaign_fastwalk_route_hazards")
        if (
            not refreshed.get(_SANCTUARY_SOURCE_SAFE_BYSTANDER_REVALIDATION_KEY)
            and refreshed.get("campaign_last_policy") == policy_id
            and _level(refreshed) == 24
            and isinstance(result, Mapping)
            and result.get("boot_id") == refreshed.get("world_boot_id")
            and result.get("level") == _level(refreshed)
            and result.get("observed") is False
            and result.get("viable") is False
            and result.get("completed_kill") is not True
            and result.get("fatal_failure") is True
            and result.get("crowded") is True
            and result.get("route_hazard") == _SANCTUARY_RESOURCE_EXHAUSTED_HAZARD
            and isinstance(deep_locator, Mapping)
            and deep_locator.get("policy_revision")
            == _SANCTUARY_DEEP_LOCATOR_REVALIDATION_REVISION
            and deep_locator.get("policy_id") == policy_id
            and deep_locator.get("boot_id") == refreshed.get("world_boot_id")
            and deep_locator.get("level") == _level(refreshed)
            and deep_locator.get("status") == "attempted"
            and deep_locator.get("observed_block_room_vnum") == "4014"
            and deep_locator.get("safe_endpoint_room_vnums") == [4064, 4063]
            and isinstance(recovery_attempt, Mapping)
            and recovery_attempt.get("boot_id") == refreshed.get("world_boot_id")
            and recovery_attempt.get("level") == _level(refreshed)
            and recovery_attempt_count > _SANCTUARY_RESOURCE_MAX_ATTEMPTS
            and abort_reason == _SANCTUARY_SOURCE_SAFE_BYSTANDER_ABORT_REASON
            and route_hazards == [_SANCTUARY_SOURCE_SAFE_BYSTANDER_ROUTE_HAZARD]
            and refreshed.get("campaign_fastwalk_target_absent") is False
            and refreshed.get("campaign_fastwalk_target_present_observed") is True
            and refreshed.get("campaign_fastwalk_crowded") is True
            and not refreshed.get("campaign_objective_kills")
            and refreshed.get("campaign_died_during_segment") is not True
            and refreshed.get("dead") is not True
            and refreshed.get("in_combat") is not True
            and refreshed.get("enemies") in (None, [])
            and not refreshed.get("combat_target")
            and str(refreshed.get("room_vnum") or "") == "3054"
            and {"healing", "safe"}.issubset(room_flags)
            and refreshed.get("position") in {5, 6, 7}
            and hp > 0
        ):
            refreshed = dict(refreshed)
            results = dict(_campaign_research_results(refreshed))
            superseded_result = dict(results.pop(policy_id))
            if results:
                refreshed["campaign_research_results"] = results
            else:
                refreshed.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            cleared = [
                str(candidate_id)
                for candidate_id in refreshed.get(
                    _CLEARED_RESEARCH_POLICIES_KEY, ()
                )
                if str(candidate_id) != policy_id
            ]
            if cleared:
                refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = cleared
            else:
                refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
            refreshed[_SANCTUARY_SOURCE_SAFE_BYSTANDER_REVALIDATION_KEY] = {
                "policy_revision": (
                    _SANCTUARY_SOURCE_SAFE_BYSTANDER_REVALIDATION_REVISION
                ),
                "policy_id": policy_id,
                "boot_id": refreshed.get("world_boot_id"),
                "level": _level(refreshed),
                "status": "pending",
                "source_mobile_vnum": 4051,
                "source_mobile_level_range": [5, 9],
                "source_mobile_aggressive": True,
                "source_mobile_can_join_player_fight": False,
                "blocked_room_vnum": "4064",
                "reason": (
                    "source-known aggressive bystander is outside DD4's "
                    "attack and join level windows"
                ),
                "source_revision": refreshed.get(_SOURCE_REVISION_KEY),
                "superseded_result": superseded_result,
                "superseded_abort_reason": abort_reason,
                "superseded_route_hazards": list(route_hazards),
                "superseded_deep_locator": dict(deep_locator),
            }
            if refreshed.get("campaign_last_policy") == policy_id:
                refreshed.pop("campaign_last_policy", None)
            for key in (
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
                "campaign_fastwalk_route_hazards",
                "campaign_fastwalk_where_area_checks",
                "campaign_fastwalk_where_relocation_attempts",
            ):
                refreshed.pop(key, None)
    if previous_revision < _SANCTUARY_RESET_CAPACITY_REVALIDATION_REVISION:
        # DD4's reset_area() counts the same mobile prototype globally, while
        # the two Moria reset entries place one carrier in each room. Preserve
        # both exhausted probes, then reopen exactly one required-loot attempt
        # against that audited two-room/global-capacity-2 source.
        policy_id = _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
        reserve_policy_id = _SOURCE_RANKED_SANCTUARY_RESERVE_POLICY.policy_id
        marker = refreshed.get(_SANCTUARY_RESET_CAPACITY_REVALIDATION_KEY)
        results = _campaign_research_results(refreshed)
        recovery_result = results.get(policy_id)
        reserve_result = results.get(reserve_policy_id)
        attempts = refreshed.get(_SANCTUARY_RESOURCE_ATTEMPTS_KEY)
        recovery_attempt = (
            attempts.get(policy_id) if isinstance(attempts, Mapping) else None
        )
        reserve_attempt = (
            attempts.get(reserve_policy_id) if isinstance(attempts, Mapping) else None
        )
        try:
            recovery_attempt_count = (
                int(recovery_attempt.get("count") or 0)
                if isinstance(recovery_attempt, Mapping)
                else 0
            )
            reserve_attempt_count = (
                int(reserve_attempt.get("count") or 0)
                if isinstance(reserve_attempt, Mapping)
                else 0
            )
            hp = int(refreshed.get("hp") or 0)
        except (TypeError, ValueError):
            recovery_attempt_count = reserve_attempt_count = hp = 0
        raw_room_flags = refreshed.get("room_flags")
        room_flags = (
            {str(flag).casefold() for flag in raw_room_flags}
            if isinstance(raw_room_flags, Collection)
            and not isinstance(raw_room_flags, (str, bytes))
            else set()
        )
        exact_failed_capacity_pair = bool(
            not marker
            and _level(refreshed) == 24
            and refreshed.get(_SOURCE_REVISION_KEY)
            and isinstance(recovery_result, Mapping)
            and recovery_result.get("boot_id") == refreshed.get("world_boot_id")
            and recovery_result.get("level") == _level(refreshed)
            and recovery_result.get("observed") is True
            and recovery_result.get("viable") is False
            and recovery_result.get("completed_kill") is False
            and recovery_result.get("fatal_failure") is True
            and recovery_result.get("route_hazard")
            == _SANCTUARY_RESOURCE_EXHAUSTED_HAZARD
            and recovery_result.get("required_object_acquired") is not True
            and isinstance(reserve_result, Mapping)
            and reserve_result.get("boot_id") == refreshed.get("world_boot_id")
            and reserve_result.get("level") == _level(refreshed)
            and reserve_result.get("observed") is True
            and reserve_result.get("viable") is False
            and reserve_result.get("completed_kill") is False
            and reserve_result.get("fatal_failure") is True
            and reserve_result.get("route_hazard")
            == _SANCTUARY_RESOURCE_EXHAUSTED_HAZARD
            and recovery_attempt_count >= _SANCTUARY_RESOURCE_MAX_ATTEMPTS
            and reserve_attempt_count >= _SANCTUARY_RESOURCE_MAX_ATTEMPTS
            and _current_protection_recovery_marker_present(refreshed)
            and not _state_has_sanctuary_reserve(refreshed)
            and not refreshed.get("campaign_objective_kills")
            and refreshed.get("campaign_died_during_segment") is not True
            and refreshed.get("dead") is not True
            and refreshed.get("in_combat") is not True
            and refreshed.get("enemies") in (None, [])
            and not refreshed.get("combat_target")
            and str(refreshed.get("room_vnum") or "") == "3054"
            and {"healing", "safe"}.issubset(room_flags)
            and refreshed.get("position") in {5, 6, 7}
            and hp > 0
        )
        if exact_failed_capacity_pair:
            refreshed = dict(refreshed)
            superseded_results = {
                policy_id: dict(recovery_result),
                reserve_policy_id: dict(reserve_result),
            }
            remaining_results = dict(_campaign_research_results(refreshed))
            remaining_results.pop(policy_id, None)
            remaining_results.pop(reserve_policy_id, None)
            if remaining_results:
                refreshed["campaign_research_results"] = remaining_results
            else:
                refreshed.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                cooldowns.pop(reserve_policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            cleared = [
                str(candidate_id)
                for candidate_id in refreshed.get(
                    _CLEARED_RESEARCH_POLICIES_KEY, ()
                )
                if str(candidate_id) not in {policy_id, reserve_policy_id}
            ]
            if cleared:
                refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = cleared
            else:
                refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
            refreshed[_SANCTUARY_RESET_CAPACITY_REVALIDATION_KEY] = {
                "policy_revision": (
                    _SANCTUARY_RESET_CAPACITY_REVALIDATION_REVISION
                ),
                "policy_id": policy_id,
                "boot_id": refreshed.get("world_boot_id"),
                "level": _level(refreshed),
                "status": "pending",
                "source_mobile_vnum": _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
                "source_object_vnum": _MORIA_SANCTUARY_POTION_OBJECT_VNUM,
                "source_room_vnums": [4064, 4071],
                "source_global_reset_capacity": 2,
                "source_reset_entries_per_room": 1,
                "reason": _SANCTUARY_RESET_CAPACITY_REVALIDATION_REASON,
                "source_revision": refreshed.get(_SOURCE_REVISION_KEY),
                "superseded_results": superseded_results,
            }
            if refreshed.get("campaign_last_policy") in {
                policy_id,
                reserve_policy_id,
            }:
                refreshed.pop("campaign_last_policy", None)
            if refreshed.get(_SOURCE_RANKED_REVALIDATION_POLICY_KEY) in {
                policy_id,
                reserve_policy_id,
            }:
                refreshed.pop(_SOURCE_RANKED_REVALIDATION_POLICY_KEY, None)
            for key in (
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
                "campaign_fastwalk_route_hazards",
                "campaign_fastwalk_required_object_vnums",
                "campaign_fastwalk_where_area_checks",
                "campaign_fastwalk_where_relocation_attempts",
                _SOURCE_RANKED_CANDIDATE_KEY,
            ):
                refreshed.pop(key, None)
    if previous_revision < _SANCTUARY_LOCATOR_GRAPH_REVALIDATION_REVISION:
        # The southern Moria locator graph now follows all source-reachable
        # rooms sharing ``The maze``. Reopen only the exact level-24, no-loss
        # recovery result that exhausted its prior graph; preserve the old
        # attempt and locator marker inside this one-shot migration.
        policy_id = _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
        result = _campaign_research_results(refreshed).get(policy_id)
        deep_locator = refreshed.get(_SANCTUARY_DEEP_LOCATOR_REVALIDATION_KEY)
        raw_room_flags = refreshed.get("room_flags")
        room_flags = (
            {str(flag).casefold() for flag in raw_room_flags}
            if isinstance(raw_room_flags, Collection)
            and not isinstance(raw_room_flags, (str, bytes))
            else set()
        )
        exact_locator_graph_retry = bool(
            not refreshed.get(_SANCTUARY_LOCATOR_GRAPH_REVALIDATION_KEY)
            and _level(refreshed) == 24
            and isinstance(result, Mapping)
            and result.get("boot_id") == refreshed.get("world_boot_id")
            and result.get("level") == _level(refreshed)
            and result.get("observed") is True
            and result.get("viable") is False
            and result.get("completed_kill") is False
            and result.get("fatal_failure") is True
            and result.get("route_hazard")
            == _SANCTUARY_RESOURCE_EXHAUSTED_HAZARD
            and result.get("required_object_acquired") is not True
            and isinstance(deep_locator, Mapping)
            and deep_locator.get("policy_revision")
            == _SANCTUARY_DEEP_LOCATOR_REVALIDATION_REVISION
            and deep_locator.get("policy_id") == policy_id
            and deep_locator.get("boot_id") == refreshed.get("world_boot_id")
            and deep_locator.get("level") == _level(refreshed)
            and deep_locator.get("status") == "attempted"
            and deep_locator.get("source_mobile_vnum")
            == _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM
            and deep_locator.get("observed_block_room_vnum") == "4014"
            and deep_locator.get("safe_endpoint_room_vnums") == [4064, 4063]
            and _current_protection_recovery_marker_present(refreshed)
            and not _state_has_sanctuary_reserve(refreshed)
            and not refreshed.get("campaign_objective_kills")
            and refreshed.get("campaign_died_during_segment") is not True
            and refreshed.get("dead") is not True
            and refreshed.get("in_combat") is not True
            and refreshed.get("enemies") in (None, [])
            and not refreshed.get("combat_target")
            and str(refreshed.get("room_vnum") or "") == "3054"
            and {"healing", "safe"}.issubset(room_flags)
            and refreshed.get("position") in {5, 6, 7}
            and int(refreshed.get("hp") or 0) > 0
        )
        if exact_locator_graph_retry:
            refreshed = dict(refreshed)
            results = dict(_campaign_research_results(refreshed))
            superseded_result = dict(results.pop(policy_id))
            if results:
                refreshed["campaign_research_results"] = results
            else:
                refreshed.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            cleared = [
                str(candidate_id)
                for candidate_id in refreshed.get(
                    _CLEARED_RESEARCH_POLICIES_KEY,
                    (),
                )
                if str(candidate_id) != policy_id
            ]
            if cleared:
                refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = cleared
            else:
                refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
            refreshed[_SANCTUARY_LOCATOR_GRAPH_REVALIDATION_KEY] = {
                "policy_revision": (
                    _SANCTUARY_LOCATOR_GRAPH_REVALIDATION_REVISION
                ),
                "policy_id": policy_id,
                "boot_id": refreshed.get("world_boot_id"),
                "level": _level(refreshed),
                "status": "pending",
                "source_mobile_vnum": _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
                "source_object_vnum": _MORIA_SANCTUARY_POTION_OBJECT_VNUM,
                "source_locator_room_vnums": ["4063", "4066", "4065"],
                "reason": _SANCTUARY_LOCATOR_GRAPH_REVALIDATION_REASON,
                "source_revision": refreshed.get(_SOURCE_REVISION_KEY),
                "superseded_result": superseded_result,
                "superseded_deep_locator": dict(deep_locator),
            }
            if refreshed.get("campaign_last_policy") == policy_id:
                refreshed.pop("campaign_last_policy", None)
            if refreshed.get(_SOURCE_RANKED_REVALIDATION_POLICY_KEY) == policy_id:
                refreshed.pop(_SOURCE_RANKED_REVALIDATION_POLICY_KEY, None)
            for key in (
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
                "campaign_fastwalk_route_hazards",
                "campaign_fastwalk_required_object_vnums",
                "campaign_fastwalk_where_area_checks",
                "campaign_fastwalk_where_relocation_attempts",
                _SOURCE_RANKED_CANDIDATE_KEY,
            ):
                refreshed.pop(key, None)
    if (
        _SANCTUARY_LOCATOR_GRAPH_REVALIDATION_REVISION
        <= previous_revision
        <= _SANCTUARY_DEEP_ROUTE_REVALIDATION_REVISION
    ):
        # Revision 283 was consumed before the deep-route implementation was
        # corrected: its source-safe graph check started at recall and thus
        # rejected a route that is safe once the known 4064 endpoint has been
        # reached. Preserve that attempt, then reopen exactly one level-24
        # recovery route from the audited endpoint. This migration never
        # fabricates a carrier or a kill; the normal live gates still decide
        # whether the route can run.
        policy_id = _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
        result = _campaign_research_results(refreshed).get(policy_id)
        graph_marker = refreshed.get(
            _SANCTUARY_LOCATOR_GRAPH_REVALIDATION_KEY
        )
        marker = refreshed.get(_SANCTUARY_DEEP_ROUTE_REVALIDATION_KEY)
        attempts = refreshed.get(_SANCTUARY_RESOURCE_ATTEMPTS_KEY)
        attempt = attempts.get(policy_id) if isinstance(attempts, Mapping) else None
        try:
            attempt_count = (
                int(attempt.get("count") or 0)
                if isinstance(attempt, Mapping)
                else 0
            )
            hp = int(refreshed.get("hp") or 0)
        except (TypeError, ValueError):
            attempt_count = hp = 0
        raw_room_flags = refreshed.get("room_flags")
        room_flags = (
            {str(flag).casefold() for flag in raw_room_flags}
            if isinstance(raw_room_flags, Collection)
            and not isinstance(raw_room_flags, (str, bytes))
            else set()
        )
        exact_deep_route_retry = bool(
            not marker
            and _level(refreshed) == 24
            and isinstance(result, Mapping)
            and result.get("boot_id") == refreshed.get("world_boot_id")
            and result.get("level") == _level(refreshed)
            and result.get("observed") is True
            and result.get("viable") is False
            and result.get("completed_kill") is not True
            and result.get("fatal_failure") is True
            and result.get("route_hazard")
            == _SANCTUARY_RESOURCE_EXHAUSTED_HAZARD
            and result.get("required_object_acquired") is not True
            and isinstance(graph_marker, Mapping)
            and graph_marker.get("policy_revision")
            == _SANCTUARY_LOCATOR_GRAPH_REVALIDATION_REVISION
            and graph_marker.get("policy_id") == policy_id
            and graph_marker.get("boot_id") == refreshed.get("world_boot_id")
            and graph_marker.get("level") == _level(refreshed)
            and graph_marker.get("status") == "attempted"
            and graph_marker.get("source_mobile_vnum")
            == _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM
            and graph_marker.get("source_object_vnum")
            == _MORIA_SANCTUARY_POTION_OBJECT_VNUM
            and graph_marker.get("source_locator_room_vnums")
            == ["4063", "4066", "4065"]
            and attempt_count >= _SANCTUARY_RESOURCE_MAX_ATTEMPTS
            and _current_protection_recovery_marker_present(refreshed)
            and not _state_has_sanctuary_reserve(refreshed)
            and not refreshed.get("campaign_objective_kills")
            and refreshed.get("campaign_died_during_segment") is not True
            and refreshed.get("dead") is not True
            and refreshed.get("in_combat") is not True
            and refreshed.get("enemies") in (None, [])
            and not refreshed.get("combat_target")
            and str(refreshed.get("room_vnum") or "") == "3054"
            and {"healing", "safe"}.issubset(room_flags)
            and refreshed.get("position") in {5, 6, 7}
            and hp > 0
        )
        if exact_deep_route_retry:
            refreshed = dict(refreshed)
            results = dict(_campaign_research_results(refreshed))
            superseded_result = dict(results.pop(policy_id))
            if results:
                refreshed["campaign_research_results"] = results
            else:
                refreshed.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            cleared = [
                str(candidate_id)
                for candidate_id in refreshed.get(
                    _CLEARED_RESEARCH_POLICIES_KEY,
                    (),
                )
                if str(candidate_id) != policy_id
            ]
            if cleared:
                refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = cleared
            else:
                refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
            refreshed[_SANCTUARY_DEEP_ROUTE_REVALIDATION_KEY] = {
                "policy_revision": _SANCTUARY_DEEP_ROUTE_REVALIDATION_REVISION,
                "policy_id": policy_id,
                "boot_id": refreshed.get("world_boot_id"),
                "level": _level(refreshed),
                "status": "pending",
                "source_mobile_vnum": _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
                "source_object_vnum": _MORIA_SANCTUARY_POTION_OBJECT_VNUM,
                "route_origin_room_vnum": 4064,
                "route_target_room_vnum": 4152,
                "reason": _SANCTUARY_DEEP_ROUTE_REVALIDATION_REASON,
                "source_revision": refreshed.get(_SOURCE_REVISION_KEY),
                "superseded_result": superseded_result,
                "superseded_locator_graph": dict(graph_marker),
            }
            if refreshed.get("campaign_last_policy") == policy_id:
                refreshed.pop("campaign_last_policy", None)
            if refreshed.get(_SOURCE_RANKED_REVALIDATION_POLICY_KEY) == policy_id:
                refreshed.pop(_SOURCE_RANKED_REVALIDATION_POLICY_KEY, None)
            for key in (
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
                "campaign_fastwalk_route_hazards",
                "campaign_fastwalk_required_object_vnums",
                "campaign_fastwalk_where_area_checks",
                "campaign_fastwalk_where_relocation_attempts",
                _SOURCE_RANKED_CANDIDATE_KEY,
                _SOURCE_CONSUMABLE_SPELL_KEY,
                _SOURCE_RESOURCE_RESERVES_KEY,
            ):
                refreshed.pop(key, None)
    if previous_revision < _SANCTUARY_DEEP_ROUTE_CONTINUATION_REVISION:
        # The first execution of revision 284 stopped at room 4064 when the
        # wandering carrier was absent. Revision 285 changes only the
        # source-vetted deep sweep to continue through its approved rooms;
        # reopen that exact evidence pass once and preserve the old negative
        # result for auditability.
        policy_id = _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
        result = _campaign_research_results(refreshed).get(policy_id)
        marker = refreshed.get(_SANCTUARY_DEEP_ROUTE_REVALIDATION_KEY)
        raw_room_flags = refreshed.get("room_flags")
        room_flags = (
            {str(flag).casefold() for flag in raw_room_flags}
            if isinstance(raw_room_flags, Collection)
            and not isinstance(raw_room_flags, (str, bytes))
            else set()
        )
        absent_sightings = refreshed.get(_SOURCE_ABSENT_SIGHTINGS_KEY)
        has_reset_room_absence = bool(
            isinstance(absent_sightings, (list, tuple, set, frozenset))
            and any(
                isinstance(sighting, Mapping)
                and str(sighting.get("policy_id") or "") == policy_id
                and str(sighting.get("room_vnum") or "") == "4064"
                and str(sighting.get("target") or "").casefold()
                == "large hobgoblin"
                for sighting in absent_sightings
            )
        )
        exact_continuation_retry = bool(
            isinstance(marker, Mapping)
            and marker.get("policy_revision")
            == _SANCTUARY_DEEP_ROUTE_REVALIDATION_REVISION
            and marker.get("policy_id") == policy_id
            and marker.get("boot_id") == refreshed.get("world_boot_id")
            and marker.get("level") == _level(refreshed)
            and marker.get("status") == "attempted"
            and marker.get("reason") == _SANCTUARY_DEEP_ROUTE_REVALIDATION_REASON
            and marker.get("source_mobile_vnum")
            == _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM
            and marker.get("source_object_vnum")
            == _MORIA_SANCTUARY_POTION_OBJECT_VNUM
            and marker.get("route_origin_room_vnum") == 4064
            and marker.get("route_target_room_vnum") == 4152
            and isinstance(result, Mapping)
            and result.get("boot_id") == refreshed.get("world_boot_id")
            and result.get("level") == _level(refreshed)
            and result.get("observed") is False
            and result.get("viable") is False
            and result.get("fatal_failure") is True
            and result.get("absent") is True
            and result.get("route_hazard")
            == _SANCTUARY_RESOURCE_EXHAUSTED_HAZARD
            and result.get("required_object_acquired") is not True
            and has_reset_room_absence
            and _current_protection_recovery_marker_present(refreshed)
            and not _state_has_sanctuary_reserve(refreshed)
            and not refreshed.get("campaign_objective_kills")
            and refreshed.get("campaign_died_during_segment") is not True
            and refreshed.get("dead") is not True
            and refreshed.get("in_combat") is not True
            and refreshed.get("enemies") in (None, [])
            and not refreshed.get("combat_target")
            and str(refreshed.get("room_vnum") or "") == "3054"
            and {"healing", "safe"}.issubset(room_flags)
            and refreshed.get("position") in {5, 6, 7}
            and int(refreshed.get("hp") or 0) > 0
        )
        if exact_continuation_retry:
            refreshed = dict(refreshed)
            results = dict(_campaign_research_results(refreshed))
            superseded_result = dict(results.pop(policy_id))
            if results:
                refreshed["campaign_research_results"] = results
            else:
                refreshed.pop("campaign_research_results", None)
            old_absent_sightings = [
                dict(sighting)
                for sighting in absent_sightings
                if isinstance(sighting, Mapping)
                and str(sighting.get("policy_id") or "") == policy_id
            ] if isinstance(absent_sightings, (list, tuple, set, frozenset)) else []
            retained_absent_sightings = [
                sighting
                for sighting in absent_sightings
                if not (
                    isinstance(sighting, Mapping)
                    and str(sighting.get("policy_id") or "") == policy_id
                )
            ] if isinstance(absent_sightings, (list, tuple, set, frozenset)) else []
            if retained_absent_sightings:
                refreshed[_SOURCE_ABSENT_SIGHTINGS_KEY] = retained_absent_sightings
            else:
                refreshed.pop(_SOURCE_ABSENT_SIGHTINGS_KEY, None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            cleared = [
                str(candidate_id)
                for candidate_id in refreshed.get(
                    _CLEARED_RESEARCH_POLICIES_KEY,
                    (),
                )
                if str(candidate_id) != policy_id
            ]
            if cleared:
                refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = cleared
            else:
                refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
            refreshed[_SANCTUARY_DEEP_ROUTE_REVALIDATION_KEY] = {
                "policy_revision": _SANCTUARY_DEEP_ROUTE_CONTINUATION_REVISION,
                "policy_id": policy_id,
                "boot_id": refreshed.get("world_boot_id"),
                "level": _level(refreshed),
                "status": "pending",
                "source_mobile_vnum": _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
                "source_object_vnum": _MORIA_SANCTUARY_POTION_OBJECT_VNUM,
                "route_origin_room_vnum": 4064,
                "route_target_room_vnum": 4152,
                "reason": _SANCTUARY_DEEP_ROUTE_CONTINUATION_REASON,
                "source_revision": refreshed.get(_SOURCE_REVISION_KEY),
                "superseded_result": superseded_result,
                "superseded_deep_route": dict(marker),
                "superseded_source_absent_sightings": old_absent_sightings,
            }
            if refreshed.get("campaign_last_policy") == policy_id:
                refreshed.pop("campaign_last_policy", None)
            if refreshed.get(_SOURCE_RANKED_REVALIDATION_POLICY_KEY) == policy_id:
                refreshed.pop(_SOURCE_RANKED_REVALIDATION_POLICY_KEY, None)
            for key in (
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
                "campaign_fastwalk_route_hazards",
                "campaign_fastwalk_required_object_vnums",
                "campaign_fastwalk_where_area_checks",
                "campaign_fastwalk_where_relocation_attempts",
                _SOURCE_RANKED_CANDIDATE_KEY,
                _SOURCE_CONSUMABLE_SPELL_KEY,
                _SOURCE_RESOURCE_RESERVES_KEY,
            ):
                refreshed.pop(key, None)
    if previous_revision < _SANCTUARY_DEEP_ROUTE_SOURCE_ROOM_REVISION:
        # Revision 286 makes the first deep locator's source reset room
        # explicit and records route/stop boundaries in each live transcript.
        # Reopen only the exact revision-285 absence so this evidence pass is
        # bounded and its predecessor remains available for audit.
        policy_id = _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
        result = _campaign_research_results(refreshed).get(policy_id)
        marker = refreshed.get(_SANCTUARY_DEEP_ROUTE_REVALIDATION_KEY)
        absent_sightings = refreshed.get(_SOURCE_ABSENT_SIGHTINGS_KEY)
        has_reset_room_absence = bool(
            isinstance(absent_sightings, (list, tuple, set, frozenset))
            and any(
                isinstance(sighting, Mapping)
                and str(sighting.get("policy_id") or "") == policy_id
                and str(sighting.get("room_vnum") or "") == "4064"
                and str(sighting.get("target") or "").casefold()
                == "large hobgoblin"
                for sighting in absent_sightings
            )
        )
        exact_source_room_retry = bool(
            isinstance(marker, Mapping)
            and marker.get("policy_revision")
            == _SANCTUARY_DEEP_ROUTE_CONTINUATION_REVISION
            and marker.get("policy_id") == policy_id
            and marker.get("boot_id") == refreshed.get("world_boot_id")
            and marker.get("level") == _level(refreshed)
            and marker.get("status") == "attempted"
            and marker.get("reason") == _SANCTUARY_DEEP_ROUTE_CONTINUATION_REASON
            and marker.get("source_mobile_vnum")
            == _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM
            and marker.get("source_object_vnum")
            == _MORIA_SANCTUARY_POTION_OBJECT_VNUM
            and marker.get("route_origin_room_vnum") == 4064
            and marker.get("route_target_room_vnum") == 4152
            and isinstance(result, Mapping)
            and result.get("boot_id") == refreshed.get("world_boot_id")
            and (
                result.get("level") == _level(refreshed)
                or result.get("level") is None
            )
            and result.get("observed") is False
            and result.get("viable") is False
            and result.get("absent") is True
            and (
                (
                    result.get("fatal_failure") is True
                    and result.get("route_hazard")
                    == _SANCTUARY_RESOURCE_EXHAUSTED_HAZARD
                )
                or (
                    "fatal_failure" not in result
                    and "route_hazard" not in result
                )
            )
            and result.get("required_object_acquired") is not True
            and has_reset_room_absence
            and _current_protection_recovery_marker_present(refreshed)
            and not _state_has_sanctuary_reserve(refreshed)
            and not refreshed.get("campaign_objective_kills")
            and refreshed.get("campaign_died_during_segment") is not True
            and refreshed.get("dead") is not True
            and refreshed.get("in_combat") is not True
            and refreshed.get("enemies") in (None, [])
            and not refreshed.get("combat_target")
            and str(refreshed.get("room_vnum") or "") == "3054"
            and int(refreshed.get("hp") or 0) > 0
        )
        if exact_source_room_retry:
            refreshed = dict(refreshed)
            results = dict(_campaign_research_results(refreshed))
            superseded_result = dict(results.pop(policy_id))
            if results:
                refreshed["campaign_research_results"] = results
            else:
                refreshed.pop("campaign_research_results", None)
            old_absent_sightings = [
                dict(sighting)
                for sighting in absent_sightings
                if isinstance(sighting, Mapping)
                and str(sighting.get("policy_id") or "") == policy_id
            ] if isinstance(absent_sightings, (list, tuple, set, frozenset)) else []
            retained_absent_sightings = [
                sighting
                for sighting in absent_sightings
                if not (
                    isinstance(sighting, Mapping)
                    and str(sighting.get("policy_id") or "") == policy_id
                )
            ] if isinstance(absent_sightings, (list, tuple, set, frozenset)) else []
            if retained_absent_sightings:
                refreshed[_SOURCE_ABSENT_SIGHTINGS_KEY] = retained_absent_sightings
            else:
                refreshed.pop(_SOURCE_ABSENT_SIGHTINGS_KEY, None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            cleared = [
                str(candidate_id)
                for candidate_id in refreshed.get(
                    _CLEARED_RESEARCH_POLICIES_KEY,
                    (),
                )
                if str(candidate_id) != policy_id
            ]
            if cleared:
                refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = cleared
            else:
                refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
            refreshed[_SANCTUARY_DEEP_ROUTE_REVALIDATION_KEY] = {
                "policy_revision": _SANCTUARY_DEEP_ROUTE_SOURCE_ROOM_REVISION,
                "policy_id": policy_id,
                "boot_id": refreshed.get("world_boot_id"),
                "level": _level(refreshed),
                "status": "pending",
                "source_mobile_vnum": _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
                "source_object_vnum": _MORIA_SANCTUARY_POTION_OBJECT_VNUM,
                "route_origin_room_vnum": 4064,
                "route_target_room_vnum": 4152,
                "reason": _SANCTUARY_DEEP_ROUTE_SOURCE_ROOM_REASON,
                "source_revision": refreshed.get(_SOURCE_REVISION_KEY),
                "superseded_result": superseded_result,
                "superseded_deep_route": dict(marker),
                "superseded_source_absent_sightings": old_absent_sightings,
            }
            if refreshed.get("campaign_last_policy") == policy_id:
                refreshed.pop("campaign_last_policy", None)
            if refreshed.get(_SOURCE_RANKED_REVALIDATION_POLICY_KEY) == policy_id:
                refreshed.pop(_SOURCE_RANKED_REVALIDATION_POLICY_KEY, None)
            for key in (
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
                "campaign_fastwalk_route_hazards",
                "campaign_fastwalk_required_object_vnums",
                "campaign_fastwalk_where_area_checks",
                "campaign_fastwalk_where_relocation_attempts",
                _SOURCE_RANKED_CANDIDATE_KEY,
                _SOURCE_CONSUMABLE_SPELL_KEY,
                _SOURCE_RESOURCE_RESERVES_KEY,
            ):
                refreshed.pop(key, None)
    if previous_revision < _SANCTUARY_DEEP_ROUTE_PRECEDENCE_REVISION:
        # The revision-286 attempt reached the old generic sanctuary-reserve
        # dispatcher before the dedicated Moria branch. Reopen only that
        # exact compact absence so the precedence fix gets one live pass.
        policy_id = _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
        result = _campaign_research_results(refreshed).get(policy_id)
        marker = refreshed.get(_SANCTUARY_DEEP_ROUTE_REVALIDATION_KEY)
        absent_sightings = refreshed.get(_SOURCE_ABSENT_SIGHTINGS_KEY)
        raw_room_flags = refreshed.get("room_flags")
        room_flags = (
            {str(flag).casefold() for flag in raw_room_flags}
            if isinstance(raw_room_flags, Collection)
            and not isinstance(raw_room_flags, (str, bytes))
            else set()
        )
        has_reset_room_absence = bool(
            isinstance(absent_sightings, (list, tuple, set, frozenset))
            and any(
                isinstance(sighting, Mapping)
                and str(sighting.get("policy_id") or "") == policy_id
                and str(sighting.get("room_vnum") or "") == "4064"
                and str(sighting.get("target") or "").casefold()
                == "large hobgoblin"
                for sighting in absent_sightings
            )
        )
        exact_precedence_retry = bool(
            isinstance(marker, Mapping)
            and marker.get("policy_revision")
            == _SANCTUARY_DEEP_ROUTE_SOURCE_ROOM_REVISION
            and marker.get("policy_id") == policy_id
            and marker.get("boot_id") == refreshed.get("world_boot_id")
            and marker.get("level") == _level(refreshed)
            and marker.get("status") == "attempted"
            and marker.get("reason") == _SANCTUARY_DEEP_ROUTE_SOURCE_ROOM_REASON
            and marker.get("source_mobile_vnum")
            == _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM
            and marker.get("source_object_vnum")
            == _MORIA_SANCTUARY_POTION_OBJECT_VNUM
            and marker.get("route_origin_room_vnum") == 4064
            and marker.get("route_target_room_vnum") == 4152
            and isinstance(result, Mapping)
            and result.get("boot_id") == refreshed.get("world_boot_id")
            and (
                result.get("level") == _level(refreshed)
                or result.get("level") is None
            )
            and result.get("observed") is False
            and result.get("viable") is False
            and result.get("absent") is True
            and (
                (
                    result.get("fatal_failure") is True
                    and result.get("route_hazard")
                    == _SANCTUARY_RESOURCE_EXHAUSTED_HAZARD
                )
                or (
                    "fatal_failure" not in result
                    and "route_hazard" not in result
                )
            )
            and result.get("required_object_acquired") is not True
            and has_reset_room_absence
            and _current_protection_recovery_marker_present(refreshed)
            and not _state_has_sanctuary_reserve(refreshed)
            and refreshed.get("campaign_last_policy") == policy_id
            and refreshed.get("campaign_fastwalk_target_absent") is True
            and refreshed.get("campaign_fastwalk_target_present_observed") is False
            and refreshed.get("campaign_fastwalk_required_object_vnums") == []
            and refreshed.get("campaign_fastwalk_route_hazards") == []
            and refreshed.get("campaign_fastwalk_where_area_checks") == []
            and not refreshed.get("campaign_objective_kills")
            and refreshed.get("campaign_died_during_segment") is not True
            and refreshed.get("dead") is not True
            and refreshed.get("in_combat") is not True
            and refreshed.get("enemies") in (None, [])
            and not refreshed.get("combat_target")
            and str(refreshed.get("room_vnum") or "") == "3054"
            and {"healing", "safe"}.issubset(room_flags)
            and refreshed.get("position") in {5, 6, 7}
            and int(refreshed.get("hp") or 0) > 0
        )
        if exact_precedence_retry:
            refreshed = dict(refreshed)
            results = dict(_campaign_research_results(refreshed))
            superseded_result = dict(results.pop(policy_id))
            if results:
                refreshed["campaign_research_results"] = results
            else:
                refreshed.pop("campaign_research_results", None)
            old_absent_sightings = [
                dict(sighting)
                for sighting in absent_sightings
                if isinstance(sighting, Mapping)
                and str(sighting.get("policy_id") or "") == policy_id
            ] if isinstance(absent_sightings, (list, tuple, set, frozenset)) else []
            retained_absent_sightings = [
                sighting
                for sighting in absent_sightings
                if not (
                    isinstance(sighting, Mapping)
                    and str(sighting.get("policy_id") or "") == policy_id
                )
            ] if isinstance(absent_sightings, (list, tuple, set, frozenset)) else []
            if retained_absent_sightings:
                refreshed[_SOURCE_ABSENT_SIGHTINGS_KEY] = retained_absent_sightings
            else:
                refreshed.pop(_SOURCE_ABSENT_SIGHTINGS_KEY, None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            cleared = [
                str(candidate_id)
                for candidate_id in refreshed.get(
                    _CLEARED_RESEARCH_POLICIES_KEY,
                    (),
                )
                if str(candidate_id) != policy_id
            ]
            if cleared:
                refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = cleared
            else:
                refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
            refreshed[_SANCTUARY_DEEP_ROUTE_REVALIDATION_KEY] = {
                "policy_revision": _SANCTUARY_DEEP_ROUTE_PRECEDENCE_REVISION,
                "policy_id": policy_id,
                "boot_id": refreshed.get("world_boot_id"),
                "level": _level(refreshed),
                "status": "pending",
                "source_mobile_vnum": _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
                "source_object_vnum": _MORIA_SANCTUARY_POTION_OBJECT_VNUM,
                "route_origin_room_vnum": 4064,
                "route_target_room_vnum": 4152,
                "reason": _SANCTUARY_DEEP_ROUTE_PRECEDENCE_REASON,
                "source_revision": refreshed.get(_SOURCE_REVISION_KEY),
                "superseded_result": superseded_result,
                "superseded_deep_route": dict(marker),
                "superseded_source_absent_sightings": old_absent_sightings,
            }
            if refreshed.get("campaign_last_policy") == policy_id:
                refreshed.pop("campaign_last_policy", None)
            if refreshed.get(_SOURCE_RANKED_REVALIDATION_POLICY_KEY) == policy_id:
                refreshed.pop(_SOURCE_RANKED_REVALIDATION_POLICY_KEY, None)
            for key in (
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
                "campaign_fastwalk_route_hazards",
                "campaign_fastwalk_required_object_vnums",
                "campaign_fastwalk_where_area_checks",
                "campaign_fastwalk_where_relocation_attempts",
                _SOURCE_RANKED_CANDIDATE_KEY,
                _SOURCE_CONSUMABLE_SPELL_KEY,
                _SOURCE_RESOURCE_RESERVES_KEY,
            ):
                refreshed.pop(key, None)
    if previous_revision < _SANCTUARY_DEEP_ROUTE_CONSUMED_FLAG_REVISION:
        # Revision 287 consumed the pending marker before the generic reserve
        # branch was bypassed. Reopen only that exact compact absence so the
        # explicit segment-start flag can reach the Moria dispatcher.
        policy_id = _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
        result = _campaign_research_results(refreshed).get(policy_id)
        marker = refreshed.get(_SANCTUARY_DEEP_ROUTE_REVALIDATION_KEY)
        absent_sightings = refreshed.get(_SOURCE_ABSENT_SIGHTINGS_KEY)
        raw_room_flags = refreshed.get("room_flags")
        room_flags = (
            {str(flag).casefold() for flag in raw_room_flags}
            if isinstance(raw_room_flags, Collection)
            and not isinstance(raw_room_flags, (str, bytes))
            else set()
        )
        has_reset_room_absence = bool(
            isinstance(absent_sightings, (list, tuple, set, frozenset))
            and any(
                isinstance(sighting, Mapping)
                and str(sighting.get("policy_id") or "") == policy_id
                and str(sighting.get("room_vnum") or "") == "4064"
                and str(sighting.get("target") or "").casefold()
                == "large hobgoblin"
                for sighting in absent_sightings
            )
        )
        exact_consumed_flag_retry = bool(
            isinstance(marker, Mapping)
            and marker.get("policy_revision")
            == _SANCTUARY_DEEP_ROUTE_PRECEDENCE_REVISION
            and marker.get("policy_id") == policy_id
            and marker.get("boot_id") == refreshed.get("world_boot_id")
            and marker.get("level") == _level(refreshed)
            and marker.get("status") == "attempted"
            and marker.get("reason") == _SANCTUARY_DEEP_ROUTE_PRECEDENCE_REASON
            and marker.get("source_mobile_vnum")
            == _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM
            and marker.get("source_object_vnum")
            == _MORIA_SANCTUARY_POTION_OBJECT_VNUM
            and marker.get("route_origin_room_vnum") == 4064
            and marker.get("route_target_room_vnum") == 4152
            and isinstance(result, Mapping)
            and result.get("boot_id") == refreshed.get("world_boot_id")
            and (
                result.get("level") == _level(refreshed)
                or result.get("level") is None
            )
            and result.get("observed") is False
            and result.get("viable") is False
            and result.get("absent") is True
            and (
                (
                    result.get("fatal_failure") is True
                    and result.get("route_hazard")
                    == _SANCTUARY_RESOURCE_EXHAUSTED_HAZARD
                )
                or (
                    "fatal_failure" not in result
                    and "route_hazard" not in result
                )
            )
            and result.get("required_object_acquired") is not True
            and has_reset_room_absence
            and _current_protection_recovery_marker_present(refreshed)
            and not _state_has_sanctuary_reserve(refreshed)
            and refreshed.get("campaign_last_policy") == policy_id
            and refreshed.get("campaign_fastwalk_target_absent") is True
            and refreshed.get("campaign_fastwalk_target_present_observed") is False
            and refreshed.get("campaign_fastwalk_required_object_vnums") == []
            and refreshed.get("campaign_fastwalk_route_hazards") == []
            and refreshed.get("campaign_fastwalk_where_area_checks") == []
            and not refreshed.get("campaign_objective_kills")
            and refreshed.get("campaign_died_during_segment") is not True
            and refreshed.get("dead") is not True
            and refreshed.get("in_combat") is not True
            and refreshed.get("enemies") in (None, [])
            and not refreshed.get("combat_target")
            and str(refreshed.get("room_vnum") or "") == "3054"
            and {"healing", "safe"}.issubset(room_flags)
            and refreshed.get("position") in {5, 6, 7}
            and int(refreshed.get("hp") or 0) > 0
        )
        if exact_consumed_flag_retry:
            refreshed = dict(refreshed)
            results = dict(_campaign_research_results(refreshed))
            superseded_result = dict(results.pop(policy_id))
            if results:
                refreshed["campaign_research_results"] = results
            else:
                refreshed.pop("campaign_research_results", None)
            old_absent_sightings = [
                dict(sighting)
                for sighting in absent_sightings
                if isinstance(sighting, Mapping)
                and str(sighting.get("policy_id") or "") == policy_id
            ] if isinstance(absent_sightings, (list, tuple, set, frozenset)) else []
            retained_absent_sightings = [
                sighting
                for sighting in absent_sightings
                if not (
                    isinstance(sighting, Mapping)
                    and str(sighting.get("policy_id") or "") == policy_id
                )
            ] if isinstance(absent_sightings, (list, tuple, set, frozenset)) else []
            if retained_absent_sightings:
                refreshed[_SOURCE_ABSENT_SIGHTINGS_KEY] = retained_absent_sightings
            else:
                refreshed.pop(_SOURCE_ABSENT_SIGHTINGS_KEY, None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            cleared = [
                str(candidate_id)
                for candidate_id in refreshed.get(
                    _CLEARED_RESEARCH_POLICIES_KEY,
                    (),
                )
                if str(candidate_id) != policy_id
            ]
            if cleared:
                refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = cleared
            else:
                refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
            refreshed[_SANCTUARY_DEEP_ROUTE_REVALIDATION_KEY] = {
                "policy_revision": _SANCTUARY_DEEP_ROUTE_CONSUMED_FLAG_REVISION,
                "policy_id": policy_id,
                "boot_id": refreshed.get("world_boot_id"),
                "level": _level(refreshed),
                "status": "pending",
                "source_mobile_vnum": _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
                "source_object_vnum": _MORIA_SANCTUARY_POTION_OBJECT_VNUM,
                "route_origin_room_vnum": 4064,
                "route_target_room_vnum": 4152,
                "reason": _SANCTUARY_DEEP_ROUTE_CONSUMED_FLAG_REASON,
                "source_revision": refreshed.get(_SOURCE_REVISION_KEY),
                "superseded_result": superseded_result,
                "superseded_deep_route": dict(marker),
                "superseded_source_absent_sightings": old_absent_sightings,
            }
            if refreshed.get("campaign_last_policy") == policy_id:
                refreshed.pop("campaign_last_policy", None)
            if refreshed.get(_SOURCE_RANKED_REVALIDATION_POLICY_KEY) == policy_id:
                refreshed.pop(_SOURCE_RANKED_REVALIDATION_POLICY_KEY, None)
            for key in (
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
                "campaign_fastwalk_route_hazards",
                "campaign_fastwalk_required_object_vnums",
                "campaign_fastwalk_where_area_checks",
                "campaign_fastwalk_where_relocation_attempts",
                _SOURCE_RANKED_CANDIDATE_KEY,
                _SOURCE_CONSUMABLE_SPELL_KEY,
                _SOURCE_RESOURCE_RESERVES_KEY,
            ):
                refreshed.pop(key, None)
    if previous_revision < _SANCTUARY_DEEP_ROUTE_TRANSIT_ADVANCE_REVISION:
        # Revision 288 reached the source-vetted deep route and the locator
        # found the wandering carrier in Moria, but the shared required-loot
        # contract made the no-mob transit waypoint recall before the later
        # locator stops. Reopen only that exact live result once.
        policy_id = _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
        result = _campaign_research_results(refreshed).get(policy_id)
        marker = refreshed.get(_SANCTUARY_DEEP_ROUTE_REVALIDATION_KEY)
        raw_room_flags = refreshed.get("room_flags")
        room_flags = (
            {str(flag).casefold() for flag in raw_room_flags}
            if isinstance(raw_room_flags, Collection)
            and not isinstance(raw_room_flags, (str, bytes))
            else set()
        )
        exact_transit_advance_retry = bool(
            isinstance(marker, Mapping)
            and marker.get("policy_revision")
            == _SANCTUARY_DEEP_ROUTE_CONSUMED_FLAG_REVISION
            and marker.get("policy_id") == policy_id
            and marker.get("boot_id") == refreshed.get("world_boot_id")
            and marker.get("level") == _level(refreshed)
            and marker.get("status") == "attempted"
            and marker.get("reason") == _SANCTUARY_DEEP_ROUTE_CONSUMED_FLAG_REASON
            and marker.get("source_mobile_vnum")
            == _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM
            and marker.get("source_object_vnum")
            == _MORIA_SANCTUARY_POTION_OBJECT_VNUM
            and marker.get("route_origin_room_vnum") == 4064
            and marker.get("route_target_room_vnum") == 4152
            and isinstance(result, Mapping)
            and result.get("boot_id") == refreshed.get("world_boot_id")
            and result.get("level") == _level(refreshed)
            and result.get("observed") is True
            and result.get("viable") is False
            and result.get("completed_kill") is False
            and result.get("fatal_failure") is True
            and result.get("route_hazard")
            == _SANCTUARY_RESOURCE_EXHAUSTED_HAZARD
            and result.get("required_object_acquired") is not True
            and _current_protection_recovery_marker_present(refreshed)
            and not _state_has_sanctuary_reserve(refreshed)
            and refreshed.get("campaign_last_policy") == policy_id
            and refreshed.get("campaign_fastwalk_target_absent") is False
            and refreshed.get("campaign_fastwalk_target_present_observed") is True
            and refreshed.get("campaign_fastwalk_abort_reason")
            == "field expedition withdrew before acquiring required item(s): purple potion"
            and refreshed.get("campaign_fastwalk_required_object_vnums") == []
            and refreshed.get("campaign_fastwalk_route_hazards") == []
            and refreshed.get("campaign_fastwalk_where_area_checks") == []
            and not refreshed.get("campaign_objective_kills")
            and refreshed.get("campaign_died_during_segment") is not True
            and refreshed.get("dead") is not True
            and refreshed.get("in_combat") is not True
            and refreshed.get("enemies") in (None, [])
            and not refreshed.get("combat_target")
            and str(refreshed.get("room_vnum") or "") == "3054"
            and {"healing", "safe"}.issubset(room_flags)
            and refreshed.get("position") in {5, 6, 7}
            and int(refreshed.get("hp") or 0) > 0
        )
        if exact_transit_advance_retry:
            refreshed = dict(refreshed)
            results = dict(_campaign_research_results(refreshed))
            superseded_result = dict(results.pop(policy_id))
            if results:
                refreshed["campaign_research_results"] = results
            else:
                refreshed.pop("campaign_research_results", None)
            absent_sightings = refreshed.get(_SOURCE_ABSENT_SIGHTINGS_KEY)
            old_absent_sightings = [
                dict(sighting)
                for sighting in absent_sightings
                if isinstance(sighting, Mapping)
                and str(sighting.get("policy_id") or "") == policy_id
            ] if isinstance(absent_sightings, (list, tuple, set, frozenset)) else []
            retained_absent_sightings = [
                sighting
                for sighting in absent_sightings
                if not (
                    isinstance(sighting, Mapping)
                    and str(sighting.get("policy_id") or "") == policy_id
                )
            ] if isinstance(absent_sightings, (list, tuple, set, frozenset)) else []
            if retained_absent_sightings:
                refreshed[_SOURCE_ABSENT_SIGHTINGS_KEY] = retained_absent_sightings
            else:
                refreshed.pop(_SOURCE_ABSENT_SIGHTINGS_KEY, None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            cleared = [
                str(candidate_id)
                for candidate_id in refreshed.get(
                    _CLEARED_RESEARCH_POLICIES_KEY,
                    (),
                )
                if str(candidate_id) != policy_id
            ]
            if cleared:
                refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = cleared
            else:
                refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
            refreshed[_SANCTUARY_DEEP_ROUTE_REVALIDATION_KEY] = {
                "policy_revision": _SANCTUARY_DEEP_ROUTE_TRANSIT_ADVANCE_REVISION,
                "policy_id": policy_id,
                "boot_id": refreshed.get("world_boot_id"),
                "level": _level(refreshed),
                "status": "pending",
                "source_mobile_vnum": _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
                "source_object_vnum": _MORIA_SANCTUARY_POTION_OBJECT_VNUM,
                "route_origin_room_vnum": 4064,
                "route_target_room_vnum": 4152,
                "reason": _SANCTUARY_DEEP_ROUTE_TRANSIT_ADVANCE_REASON,
                "source_revision": refreshed.get(_SOURCE_REVISION_KEY),
                "superseded_result": superseded_result,
                "superseded_deep_route": dict(marker),
                "superseded_source_absent_sightings": old_absent_sightings,
            }
            if refreshed.get("campaign_last_policy") == policy_id:
                refreshed.pop("campaign_last_policy", None)
            if refreshed.get(_SOURCE_RANKED_REVALIDATION_POLICY_KEY) == policy_id:
                refreshed.pop(_SOURCE_RANKED_REVALIDATION_POLICY_KEY, None)
            for key in (
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
                "campaign_fastwalk_route_hazards",
                "campaign_fastwalk_required_object_vnums",
                "campaign_fastwalk_where_area_checks",
                "campaign_fastwalk_where_relocation_attempts",
                _SOURCE_RANKED_CANDIDATE_KEY,
                _SOURCE_CONSUMABLE_SPELL_KEY,
                _SOURCE_RESOURCE_RESERVES_KEY,
            ):
                refreshed.pop(key, None)
    if previous_revision < _SANCTUARY_DEEP_ROUTE_ROUTE_COMPLETION_REVISION:
        # Revision 289 fixed the waypoint's shared loot check, but its route
        # completion predicate still treated the targetless transit stop as
        # complete before the final affordable step. Reopen only that exact
        # live result once.
        policy_id = _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
        result = _campaign_research_results(refreshed).get(policy_id)
        marker = refreshed.get(_SANCTUARY_DEEP_ROUTE_REVALIDATION_KEY)
        raw_room_flags = refreshed.get("room_flags")
        room_flags = (
            {str(flag).casefold() for flag in raw_room_flags}
            if isinstance(raw_room_flags, Collection)
            and not isinstance(raw_room_flags, (str, bytes))
            else set()
        )
        exact_route_completion_retry = bool(
            isinstance(marker, Mapping)
            and marker.get("policy_revision")
            == _SANCTUARY_DEEP_ROUTE_TRANSIT_ADVANCE_REVISION
            and marker.get("policy_id") == policy_id
            and marker.get("boot_id") == refreshed.get("world_boot_id")
            and marker.get("level") == _level(refreshed)
            and marker.get("status") == "attempted"
            and marker.get("reason")
            == _SANCTUARY_DEEP_ROUTE_TRANSIT_ADVANCE_REASON
            and marker.get("source_mobile_vnum")
            == _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM
            and marker.get("source_object_vnum")
            == _MORIA_SANCTUARY_POTION_OBJECT_VNUM
            and marker.get("route_origin_room_vnum") == 4064
            and marker.get("route_target_room_vnum") == 4152
            and isinstance(result, Mapping)
            and result.get("boot_id") == refreshed.get("world_boot_id")
            and result.get("level") == _level(refreshed)
            and result.get("observed") is True
            and result.get("viable") is False
            and result.get("completed_kill") is False
            and result.get("fatal_failure") is True
            and result.get("route_hazard")
            == _SANCTUARY_RESOURCE_EXHAUSTED_HAZARD
            and result.get("required_object_acquired") is not True
            and _current_protection_recovery_marker_present(refreshed)
            and not _state_has_sanctuary_reserve(refreshed)
            and refreshed.get("campaign_last_policy") == policy_id
            and refreshed.get("campaign_fastwalk_target_absent") is False
            and refreshed.get("campaign_fastwalk_target_present_observed") is True
            and refreshed.get("campaign_fastwalk_abort_reason")
            == "field expedition withdrew before acquiring required item(s): purple potion"
            and refreshed.get("campaign_fastwalk_required_object_vnums") == []
            and refreshed.get("campaign_fastwalk_route_hazards") == []
            and refreshed.get("campaign_fastwalk_where_area_checks") == []
            and not refreshed.get("campaign_objective_kills")
            and refreshed.get("campaign_died_during_segment") is not True
            and refreshed.get("dead") is not True
            and refreshed.get("in_combat") is not True
            and refreshed.get("enemies") in (None, [])
            and not refreshed.get("combat_target")
            and str(refreshed.get("room_vnum") or "") == "3054"
            and {"healing", "safe"}.issubset(room_flags)
            and refreshed.get("position") in {5, 6, 7}
            and int(refreshed.get("hp") or 0) > 0
        )
        if exact_route_completion_retry:
            refreshed = dict(refreshed)
            results = dict(_campaign_research_results(refreshed))
            superseded_result = dict(results.pop(policy_id))
            if results:
                refreshed["campaign_research_results"] = results
            else:
                refreshed.pop("campaign_research_results", None)
            absent_sightings = refreshed.get(_SOURCE_ABSENT_SIGHTINGS_KEY)
            old_absent_sightings = [
                dict(sighting)
                for sighting in absent_sightings
                if isinstance(sighting, Mapping)
                and str(sighting.get("policy_id") or "") == policy_id
            ] if isinstance(absent_sightings, (list, tuple, set, frozenset)) else []
            retained_absent_sightings = [
                sighting
                for sighting in absent_sightings
                if not (
                    isinstance(sighting, Mapping)
                    and str(sighting.get("policy_id") or "") == policy_id
                )
            ] if isinstance(absent_sightings, (list, tuple, set, frozenset)) else []
            if retained_absent_sightings:
                refreshed[_SOURCE_ABSENT_SIGHTINGS_KEY] = retained_absent_sightings
            else:
                refreshed.pop(_SOURCE_ABSENT_SIGHTINGS_KEY, None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            cleared = [
                str(candidate_id)
                for candidate_id in refreshed.get(
                    _CLEARED_RESEARCH_POLICIES_KEY,
                    (),
                )
                if str(candidate_id) != policy_id
            ]
            if cleared:
                refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = cleared
            else:
                refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
            refreshed[_SANCTUARY_DEEP_ROUTE_REVALIDATION_KEY] = {
                "policy_revision": _SANCTUARY_DEEP_ROUTE_ROUTE_COMPLETION_REVISION,
                "policy_id": policy_id,
                "boot_id": refreshed.get("world_boot_id"),
                "level": _level(refreshed),
                "status": "pending",
                "source_mobile_vnum": _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
                "source_object_vnum": _MORIA_SANCTUARY_POTION_OBJECT_VNUM,
                "route_origin_room_vnum": 4064,
                "route_target_room_vnum": 4152,
                "reason": _SANCTUARY_DEEP_ROUTE_ROUTE_COMPLETION_REASON,
                "source_revision": refreshed.get(_SOURCE_REVISION_KEY),
                "superseded_result": superseded_result,
                "superseded_deep_route": dict(marker),
                "superseded_source_absent_sightings": old_absent_sightings,
            }
            if refreshed.get("campaign_last_policy") == policy_id:
                refreshed.pop("campaign_last_policy", None)
            if refreshed.get(_SOURCE_RANKED_REVALIDATION_POLICY_KEY) == policy_id:
                refreshed.pop(_SOURCE_RANKED_REVALIDATION_POLICY_KEY, None)
            for key in (
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
                "campaign_fastwalk_route_hazards",
                "campaign_fastwalk_required_object_vnums",
                "campaign_fastwalk_where_area_checks",
                "campaign_fastwalk_where_relocation_attempts",
                _SOURCE_RANKED_CANDIDATE_KEY,
                _SOURCE_CONSUMABLE_SPELL_KEY,
                _SOURCE_RESOURCE_RESERVES_KEY,
            ):
                refreshed.pop(key, None)
    if previous_revision < _SANCTUARY_DEEP_ROUTE_TRANSIT_WAIT_REVISION:
        # Revision 290 still issued the final Moria edge when the preceding
        # prompt had already fallen below its audited movement cost. Reopen
        # only that exact clean healer return; the new policy waits standing
        # in the field and retains the same bounded route.
        policy_id = _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
        result = _campaign_research_results(refreshed).get(policy_id)
        marker = refreshed.get(_SANCTUARY_DEEP_ROUTE_REVALIDATION_KEY)
        raw_room_flags = refreshed.get("room_flags")
        room_flags = (
            {str(flag).casefold() for flag in raw_room_flags}
            if isinstance(raw_room_flags, Collection)
            and not isinstance(raw_room_flags, (str, bytes))
            else set()
        )
        exact_transit_wait_retry = bool(
            isinstance(marker, Mapping)
            and marker.get("policy_revision")
            == _SANCTUARY_DEEP_ROUTE_ROUTE_COMPLETION_REVISION
            and marker.get("policy_id") == policy_id
            and marker.get("boot_id") == refreshed.get("world_boot_id")
            and marker.get("level") == _level(refreshed)
            and marker.get("status") == "attempted"
            and marker.get("reason")
            == _SANCTUARY_DEEP_ROUTE_ROUTE_COMPLETION_REASON
            and marker.get("source_mobile_vnum")
            == _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM
            and marker.get("source_object_vnum")
            == _MORIA_SANCTUARY_POTION_OBJECT_VNUM
            and marker.get("route_origin_room_vnum") == 4064
            and marker.get("route_target_room_vnum") == 4152
            and isinstance(result, Mapping)
            and result.get("boot_id") == refreshed.get("world_boot_id")
            and result.get("level") == _level(refreshed)
            and result.get("observed") is True
            and result.get("viable") is False
            and result.get("completed_kill") is False
            and result.get("fatal_failure") is True
            and result.get("route_hazard")
            == _SANCTUARY_RESOURCE_EXHAUSTED_HAZARD
            and result.get("required_object_acquired") is not True
            and _current_protection_recovery_marker_present(refreshed)
            and not _state_has_sanctuary_reserve(refreshed)
            and refreshed.get("campaign_last_policy") == policy_id
            and refreshed.get("campaign_fastwalk_target_absent") is False
            and refreshed.get("campaign_fastwalk_target_present_observed") is True
            and refreshed.get("campaign_fastwalk_abort_reason")
            == "field expedition withdrew before acquiring required item(s): purple potion"
            and refreshed.get("campaign_fastwalk_required_object_vnums") == []
            and refreshed.get("campaign_fastwalk_route_hazards") == []
            and refreshed.get("campaign_fastwalk_where_area_checks") == []
            and not refreshed.get("campaign_objective_kills")
            and refreshed.get("campaign_died_during_segment") is not True
            and refreshed.get("dead") is not True
            and refreshed.get("in_combat") is not True
            and refreshed.get("enemies") in (None, [])
            and not refreshed.get("combat_target")
            and str(refreshed.get("room_vnum") or "") == "3054"
            and {"healing", "safe"}.issubset(room_flags)
            and refreshed.get("position") in {5, 6, 7}
            and int(refreshed.get("hp") or 0) > 0
        )
        if exact_transit_wait_retry:
            refreshed = dict(refreshed)
            results = dict(_campaign_research_results(refreshed))
            superseded_result = dict(results.pop(policy_id))
            if results:
                refreshed["campaign_research_results"] = results
            else:
                refreshed.pop("campaign_research_results", None)
            absent_sightings = refreshed.get(_SOURCE_ABSENT_SIGHTINGS_KEY)
            old_absent_sightings = [
                dict(sighting)
                for sighting in absent_sightings
                if isinstance(sighting, Mapping)
                and str(sighting.get("policy_id") or "") == policy_id
            ] if isinstance(absent_sightings, (list, tuple, set, frozenset)) else []
            retained_absent_sightings = [
                sighting
                for sighting in absent_sightings
                if not (
                    isinstance(sighting, Mapping)
                    and str(sighting.get("policy_id") or "") == policy_id
                )
            ] if isinstance(absent_sightings, (list, tuple, set, frozenset)) else []
            if retained_absent_sightings:
                refreshed[_SOURCE_ABSENT_SIGHTINGS_KEY] = retained_absent_sightings
            else:
                refreshed.pop(_SOURCE_ABSENT_SIGHTINGS_KEY, None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            cleared = [
                str(candidate_id)
                for candidate_id in refreshed.get(
                    _CLEARED_RESEARCH_POLICIES_KEY,
                    (),
                )
                if str(candidate_id) != policy_id
            ]
            if cleared:
                refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = cleared
            else:
                refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
            refreshed[_SANCTUARY_DEEP_ROUTE_REVALIDATION_KEY] = {
                "policy_revision": _SANCTUARY_DEEP_ROUTE_TRANSIT_WAIT_REVISION,
                "policy_id": policy_id,
                "boot_id": refreshed.get("world_boot_id"),
                "level": _level(refreshed),
                "status": "pending",
                "source_mobile_vnum": _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
                "source_object_vnum": _MORIA_SANCTUARY_POTION_OBJECT_VNUM,
                "route_origin_room_vnum": 4064,
                "route_target_room_vnum": 4152,
                "reason": _SANCTUARY_DEEP_ROUTE_TRANSIT_WAIT_REASON,
                "source_revision": refreshed.get(_SOURCE_REVISION_KEY),
                "superseded_result": superseded_result,
                "superseded_deep_route": dict(marker),
                "superseded_source_absent_sightings": old_absent_sightings,
            }
            if refreshed.get("campaign_last_policy") == policy_id:
                refreshed.pop("campaign_last_policy", None)
            if refreshed.get(_SOURCE_RANKED_REVALIDATION_POLICY_KEY) == policy_id:
                refreshed.pop(_SOURCE_RANKED_REVALIDATION_POLICY_KEY, None)
            for key in (
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
                "campaign_fastwalk_route_hazards",
                "campaign_fastwalk_required_object_vnums",
                "campaign_fastwalk_where_area_checks",
                "campaign_fastwalk_where_relocation_attempts",
                _SOURCE_RANKED_CANDIDATE_KEY,
                _SOURCE_CONSUMABLE_SPELL_KEY,
                _SOURCE_RESOURCE_RESERVES_KEY,
            ):
                refreshed.pop(key, None)
    if previous_revision < _SANCTUARY_DEEP_ROUTE_LOCATOR_BOUNDARY_REVISION:
        # Revision 291 still let a positive ``where`` result compact the
        # explicit no-mob waypoint into its following target leg. Reopen only
        # that exact clean healer return once after preserving the boundary.
        policy_id = _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
        result = _campaign_research_results(refreshed).get(policy_id)
        marker = refreshed.get(_SANCTUARY_DEEP_ROUTE_REVALIDATION_KEY)
        raw_room_flags = refreshed.get("room_flags")
        room_flags = (
            {str(flag).casefold() for flag in raw_room_flags}
            if isinstance(raw_room_flags, Collection)
            and not isinstance(raw_room_flags, (str, bytes))
            else set()
        )
        exact_locator_boundary_retry = bool(
            isinstance(marker, Mapping)
            and marker.get("policy_revision")
            == _SANCTUARY_DEEP_ROUTE_TRANSIT_WAIT_REVISION
            and marker.get("policy_id") == policy_id
            and marker.get("boot_id") == refreshed.get("world_boot_id")
            and marker.get("level") == _level(refreshed)
            and marker.get("status") == "attempted"
            and marker.get("reason")
            == _SANCTUARY_DEEP_ROUTE_TRANSIT_WAIT_REASON
            and marker.get("source_mobile_vnum")
            == _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM
            and marker.get("source_object_vnum")
            == _MORIA_SANCTUARY_POTION_OBJECT_VNUM
            and marker.get("route_origin_room_vnum") == 4064
            and marker.get("route_target_room_vnum") == 4152
            and isinstance(result, Mapping)
            and result.get("boot_id") == refreshed.get("world_boot_id")
            and result.get("level") == _level(refreshed)
            and result.get("observed") is True
            and result.get("viable") is False
            and result.get("completed_kill") is False
            and result.get("fatal_failure") is True
            and result.get("route_hazard")
            == _SANCTUARY_RESOURCE_EXHAUSTED_HAZARD
            and result.get("required_object_acquired") is not True
            and _current_protection_recovery_marker_present(refreshed)
            and not _state_has_sanctuary_reserve(refreshed)
            and refreshed.get("campaign_last_policy") == policy_id
            and refreshed.get("campaign_fastwalk_target_absent") is False
            and refreshed.get("campaign_fastwalk_target_present_observed") is True
            and refreshed.get("campaign_fastwalk_abort_reason")
            == "field expedition withdrew before acquiring required item(s): purple potion"
            and refreshed.get("campaign_fastwalk_required_object_vnums") == []
            and refreshed.get("campaign_fastwalk_route_hazards") == []
            and refreshed.get("campaign_fastwalk_where_area_checks") == []
            and not refreshed.get("campaign_objective_kills")
            and refreshed.get("campaign_died_during_segment") is not True
            and refreshed.get("dead") is not True
            and refreshed.get("in_combat") is not True
            and refreshed.get("enemies") in (None, [])
            and not refreshed.get("combat_target")
            and str(refreshed.get("room_vnum") or "") == "3054"
            and {"healing", "safe"}.issubset(room_flags)
            and refreshed.get("position") in {5, 6, 7}
            and int(refreshed.get("hp") or 0) > 0
        )
        if exact_locator_boundary_retry:
            refreshed = dict(refreshed)
            results = dict(_campaign_research_results(refreshed))
            superseded_result = dict(results.pop(policy_id))
            if results:
                refreshed["campaign_research_results"] = results
            else:
                refreshed.pop("campaign_research_results", None)
            absent_sightings = refreshed.get(_SOURCE_ABSENT_SIGHTINGS_KEY)
            old_absent_sightings = [
                dict(sighting)
                for sighting in absent_sightings
                if isinstance(sighting, Mapping)
                and str(sighting.get("policy_id") or "") == policy_id
            ] if isinstance(absent_sightings, (list, tuple, set, frozenset)) else []
            retained_absent_sightings = [
                sighting
                for sighting in absent_sightings
                if not (
                    isinstance(sighting, Mapping)
                    and str(sighting.get("policy_id") or "") == policy_id
                )
            ] if isinstance(absent_sightings, (list, tuple, set, frozenset)) else []
            if retained_absent_sightings:
                refreshed[_SOURCE_ABSENT_SIGHTINGS_KEY] = retained_absent_sightings
            else:
                refreshed.pop(_SOURCE_ABSENT_SIGHTINGS_KEY, None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            cleared = [
                str(candidate_id)
                for candidate_id in refreshed.get(
                    _CLEARED_RESEARCH_POLICIES_KEY,
                    (),
                )
                if str(candidate_id) != policy_id
            ]
            if cleared:
                refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = cleared
            else:
                refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
            refreshed[_SANCTUARY_DEEP_ROUTE_REVALIDATION_KEY] = {
                "policy_revision": _SANCTUARY_DEEP_ROUTE_LOCATOR_BOUNDARY_REVISION,
                "policy_id": policy_id,
                "boot_id": refreshed.get("world_boot_id"),
                "level": _level(refreshed),
                "status": "pending",
                "source_mobile_vnum": _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
                "source_object_vnum": _MORIA_SANCTUARY_POTION_OBJECT_VNUM,
                "route_origin_room_vnum": 4064,
                "route_target_room_vnum": 4152,
                "reason": _SANCTUARY_DEEP_ROUTE_LOCATOR_BOUNDARY_REASON,
                "source_revision": refreshed.get(_SOURCE_REVISION_KEY),
                "superseded_result": superseded_result,
                "superseded_deep_route": dict(marker),
                "superseded_source_absent_sightings": old_absent_sightings,
            }
            if refreshed.get("campaign_last_policy") == policy_id:
                refreshed.pop("campaign_last_policy", None)
            if refreshed.get(_SOURCE_RANKED_REVALIDATION_POLICY_KEY) == policy_id:
                refreshed.pop(_SOURCE_RANKED_REVALIDATION_POLICY_KEY, None)
            for key in (
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
                "campaign_fastwalk_route_hazards",
                "campaign_fastwalk_required_object_vnums",
                "campaign_fastwalk_where_area_checks",
                "campaign_fastwalk_where_relocation_attempts",
                _SOURCE_RANKED_CANDIDATE_KEY,
                _SOURCE_CONSUMABLE_SPELL_KEY,
                _SOURCE_RESOURCE_RESERVES_KEY,
            ):
                refreshed.pop(key, None)
    if previous_revision < _SANCTUARY_DEEP_ROUTE_DISPATCH_REVISION:
        # Revision 301 could still send an already-reconciled Moria recovery
        # through the generic one-room reserve executor. Reopen only the
        # exact level-24 terminal result that has the audited deep-route
        # marker, preserving both records before the corrected dispatcher
        # gets one fresh live attempt.
        policy_id = _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
        result = _campaign_research_results(refreshed).get(policy_id)
        marker = refreshed.get(_SANCTUARY_DEEP_ROUTE_REVALIDATION_KEY)
        attempts = refreshed.get(_SANCTUARY_RESOURCE_ATTEMPTS_KEY)
        attempt = attempts.get(policy_id) if isinstance(attempts, Mapping) else None
        raw_room_flags = refreshed.get("room_flags")
        room_flags = (
            {str(flag).casefold() for flag in raw_room_flags}
            if isinstance(raw_room_flags, Collection)
            and not isinstance(raw_room_flags, (str, bytes))
            else set()
        )
        try:
            attempt_count = (
                int(attempt.get("count") or 0)
                if isinstance(attempt, Mapping)
                else 0
            )
            hp = int(refreshed.get("hp") or 0)
        except (TypeError, ValueError):
            attempt_count = hp = 0
        exact_dispatch_retry = bool(
            _level(refreshed) == 24
            and isinstance(result, Mapping)
            and result.get("boot_id") == refreshed.get("world_boot_id")
            and result.get("level") == _level(refreshed)
            and result.get("observed") is True
            and result.get("viable") is False
            and result.get("completed_kill") is False
            and result.get("fatal_failure") is True
            and result.get("route_hazard")
            == _SANCTUARY_RESOURCE_EXHAUSTED_HAZARD
            and attempt_count >= _SANCTUARY_RESOURCE_MAX_ATTEMPTS
            and isinstance(marker, Mapping)
            and marker.get("policy_revision")
            in {
                _SANCTUARY_DEEP_ROUTE_REVALIDATION_REVISION,
                _SANCTUARY_DEEP_ROUTE_CONTINUATION_REVISION,
                _SANCTUARY_DEEP_ROUTE_SOURCE_ROOM_REVISION,
                _SANCTUARY_DEEP_ROUTE_PRECEDENCE_REVISION,
                _SANCTUARY_DEEP_ROUTE_CONSUMED_FLAG_REVISION,
                _SANCTUARY_DEEP_ROUTE_TRANSIT_ADVANCE_REVISION,
                _SANCTUARY_DEEP_ROUTE_ROUTE_COMPLETION_REVISION,
                _SANCTUARY_DEEP_ROUTE_TRANSIT_WAIT_REVISION,
                _SANCTUARY_DEEP_ROUTE_LOCATOR_BOUNDARY_REVISION,
            }
            and marker.get("policy_id") == policy_id
            and marker.get("boot_id") == refreshed.get("world_boot_id")
            and marker.get("level") == _level(refreshed)
            and marker.get("status") == "attempted"
            and marker.get("source_mobile_vnum")
            == _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM
            and marker.get("source_object_vnum")
            == _MORIA_SANCTUARY_POTION_OBJECT_VNUM
            and marker.get("route_origin_room_vnum") == 4064
            and marker.get("route_target_room_vnum") == 4152
            and _current_protection_recovery_marker_present(refreshed)
            and not _state_has_sanctuary_reserve(refreshed)
            and not refreshed.get("campaign_objective_kills")
            and refreshed.get("campaign_died_during_segment") is not True
            and refreshed.get("dead") is not True
            and refreshed.get("in_combat") is not True
            and refreshed.get("enemies") in (None, [])
            and not refreshed.get("combat_target")
            and str(refreshed.get("room_vnum") or "") == "3054"
            and {"healing", "safe"}.issubset(room_flags)
            and refreshed.get("position") in {5, 6, 7}
            and hp > 0
        )
        if exact_dispatch_retry:
            refreshed = dict(refreshed)
            results = dict(_campaign_research_results(refreshed))
            superseded_result = dict(results.pop(policy_id))
            if results:
                refreshed["campaign_research_results"] = results
            else:
                refreshed.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            cleared = [
                str(candidate_id)
                for candidate_id in refreshed.get(
                    _CLEARED_RESEARCH_POLICIES_KEY,
                    (),
                )
                if str(candidate_id) != policy_id
            ]
            if cleared:
                refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = cleared
            else:
                refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
            refreshed[_SANCTUARY_DEEP_ROUTE_REVALIDATION_KEY] = {
                "policy_revision": _SANCTUARY_DEEP_ROUTE_DISPATCH_REVISION,
                "policy_id": policy_id,
                "boot_id": refreshed.get("world_boot_id"),
                "level": _level(refreshed),
                "status": "pending",
                "source_mobile_vnum": _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
                "source_object_vnum": _MORIA_SANCTUARY_POTION_OBJECT_VNUM,
                "route_origin_room_vnum": 4064,
                "route_target_room_vnum": 4152,
                "reason": _SANCTUARY_DEEP_ROUTE_DISPATCH_REASON,
                "source_revision": refreshed.get(_SOURCE_REVISION_KEY),
                "superseded_result": superseded_result,
                "superseded_deep_route": dict(marker),
            }
            if refreshed.get("campaign_last_policy") == policy_id:
                refreshed.pop("campaign_last_policy", None)
            if refreshed.get(_SOURCE_RANKED_REVALIDATION_POLICY_KEY) == policy_id:
                refreshed.pop(_SOURCE_RANKED_REVALIDATION_POLICY_KEY, None)
            for key in (
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
                "campaign_fastwalk_route_hazards",
                "campaign_fastwalk_required_object_vnums",
                "campaign_fastwalk_where_area_checks",
                "campaign_fastwalk_where_relocation_attempts",
                _SOURCE_RANKED_CANDIDATE_KEY,
                _SOURCE_CONSUMABLE_SPELL_KEY,
                _SOURCE_RESOURCE_RESERVES_KEY,
            ):
                refreshed.pop(key, None)
    if previous_revision < _FOREST_ROUTE_GATE_POISON_REVALIDATION_REVISION:
        # The first Forest gate recheck correctly rejected a live crowd, but
        # the next bounded run proved that one isolated source poisoner can be
        # killed and crossed while the ACT_STAY_AREA Kodiak is still ahead.
        # Preserve both old records, then reopen only this exact maintenance
        # route with the corrected poison-continuation contract.
        forest_policy_id = _FOREST_LOCATOR_POLICY_ID
        crowd_marker = refreshed.get(_FOREST_ROUTE_GATE_CROWD_RECHECK_KEY)
        frontier_marker = refreshed.get(
            _PIERCING_WEAPON_UPGRADE_FRONTIER_RETRY_KEY
        )
        forest_result = _campaign_research_results(refreshed).get(
            forest_policy_id
        )
        evidence = (
            crowd_marker.get("evidence")
            if isinstance(crowd_marker, Mapping)
            else None
        )
        exact_forest_reopen = bool(
            isinstance(crowd_marker, Mapping)
            and crowd_marker.get("status") == "closed"
            and crowd_marker.get("policy_revision") == 302
            and crowd_marker.get("policy_id") == forest_policy_id
            and crowd_marker.get("boot_id") == refreshed.get("world_boot_id")
            and crowd_marker.get("level") == _level(refreshed)
            and crowd_marker.get("source_revision")
            == refreshed.get(_SOURCE_REVISION_KEY)
            and crowd_marker.get("outcome") == "required_object_not_acquired"
            and crowd_marker.get("reason")
            == "exact source poison-swarm crowd was observed at the Forest route gate"
            and isinstance(evidence, Mapping)
            and evidence.get("gate_room_vnum")
            == _FOREST_ROUTE_GATE_OBSERVED_ROOM_VNUM
            and evidence.get("source_mobile_vnums")
            == list(_FOREST_ROUTE_GATE_SOURCE_MOBILE_VNUMS)
            and evidence.get("abort_reason") == _FOREST_ROUTE_GATE_CROWD_ABORT_REASON
            and isinstance(frontier_marker, Mapping)
            and frontier_marker.get("status") == "closed"
            and frontier_marker.get("outcome") == "required_object_not_acquired"
            and frontier_marker.get("policy_id") == forest_policy_id
            and frontier_marker.get("boot_id") == refreshed.get("world_boot_id")
            and frontier_marker.get("level") == _level(refreshed)
            and frontier_marker.get("source_revision")
            == refreshed.get(_SOURCE_REVISION_KEY)
            and _level(refreshed) == 24
            and isinstance(forest_result, Mapping)
            and forest_result.get("boot_id") == refreshed.get("world_boot_id")
            and forest_result.get("completed_kill") is False
            and forest_result.get("viable") is False
            and not refreshed.get("campaign_objective_kills")
            and refreshed.get("dead") is not True
            and refreshed.get("in_combat") is not True
            and refreshed.get("enemies") in (None, [])
            and not refreshed.get("combat_target")
            and str(refreshed.get("room_vnum") or "") in {
                *(_MIDGAARD_HEALER_CHECKPOINT_ROOMS),
                *(_MIDGAARD_CITY_HEALER_ROOMS),
            }
        )
        if exact_forest_reopen:
            refreshed = dict(refreshed)
            results = dict(_campaign_research_results(refreshed))
            superseded_result = results.pop(forest_policy_id, None)
            if results:
                refreshed["campaign_research_results"] = results
            else:
                refreshed.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(forest_policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            refreshed.pop(_FOREST_ROUTE_GATE_CROWD_RECHECK_KEY, None)
            refreshed.pop(_PIERCING_WEAPON_UPGRADE_FRONTIER_RETRY_KEY, None)
            refreshed.pop(_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY, None)
            refreshed.pop(_PIERCING_WEAPON_UPGRADE_BOOT_KEY, None)
            refreshed[_FOREST_ROUTE_GATE_POISON_REVALIDATION_KEY] = {
                "policy_revision": _FOREST_ROUTE_GATE_POISON_REVALIDATION_REVISION,
                "policy_id": forest_policy_id,
                "boot_id": refreshed.get("world_boot_id"),
                "level": _level(refreshed),
                "source_revision": refreshed.get(_SOURCE_REVISION_KEY),
                "status": "reopened",
                "reason": _FOREST_ROUTE_GATE_POISON_REVALIDATION_REASON,
                "superseded_route_gate_crowd": dict(crowd_marker),
                "superseded_frontier_retry": dict(frontier_marker),
                "superseded_result": (
                    dict(superseded_result)
                    if isinstance(superseded_result, Mapping)
                    else None
                ),
            }
            if refreshed.get("campaign_last_policy") == forest_policy_id:
                refreshed.pop("campaign_last_policy", None)
            for key in (
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
                "campaign_fastwalk_required_object_vnums",
                "campaign_fastwalk_where_area_checks",
                "campaign_fastwalk_where_relocation_attempts",
                "campaign_fastwalk_route_hazards",
            ):
                refreshed.pop(key, None)
    if previous_revision < _SANCTUARY_DEEP_ROUTE_ROOM_INSPECTION_REVISION:
        # The live locator can report duplicate room labels. The old deep
        # route crossed room 4020 as transit, so it could miss a carrier there
        # before reaching the 4152 recovery boundary. Reopen only the exact
        # level-24 terminal Moria attempt and reset its bounded counter; all
        # prior evidence remains nested in the new marker.
        policy_id = _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
        result = _campaign_research_results(refreshed).get(policy_id)
        marker = refreshed.get(_SANCTUARY_DEEP_ROUTE_REVALIDATION_KEY)
        attempts = refreshed.get(_SANCTUARY_RESOURCE_ATTEMPTS_KEY)
        attempt = attempts.get(policy_id) if isinstance(attempts, Mapping) else None
        raw_room_flags = refreshed.get("room_flags")
        room_flags = (
            {str(flag).casefold() for flag in raw_room_flags}
            if isinstance(raw_room_flags, Collection)
            and not isinstance(raw_room_flags, (str, bytes))
            else set()
        )
        try:
            attempt_count = (
                int(attempt.get("count") or 0)
                if isinstance(attempt, Mapping)
                else 0
            )
            hp = int(refreshed.get("hp") or 0)
        except (TypeError, ValueError):
            attempt_count = hp = 0
        exact_room_inspection_retry = bool(
            _level(refreshed) == 24
            and isinstance(result, Mapping)
            and result.get("boot_id") == refreshed.get("world_boot_id")
            and result.get("level") in {None, _level(refreshed)}
            and result.get("observed") is True
            and result.get("viable") is False
            and result.get("completed_kill") is False
            and result.get("fatal_failure") is True
            and result.get("route_hazard")
            == _SANCTUARY_RESOURCE_EXHAUSTED_HAZARD
            and result.get("required_object_acquired") is not True
            and result.get("xp_loss_observed") is not True
            and attempt_count >= _SANCTUARY_RESOURCE_MAX_ATTEMPTS
            and isinstance(marker, Mapping)
            and marker.get("policy_revision")
            == _SANCTUARY_DEEP_ROUTE_DISPATCH_REVISION
            and marker.get("policy_id") == policy_id
            and marker.get("boot_id") == refreshed.get("world_boot_id")
            and marker.get("level") == _level(refreshed)
            and marker.get("status") == "attempted"
            and marker.get("source_revision")
            in {None, refreshed.get(_SOURCE_REVISION_KEY)}
            and marker.get("source_mobile_vnum")
            == _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM
            and marker.get("source_object_vnum")
            == _MORIA_SANCTUARY_POTION_OBJECT_VNUM
            and marker.get("route_origin_room_vnum") == 4064
            and marker.get("route_target_room_vnum") == 4152
            and _current_protection_recovery_marker_present(refreshed)
            and not _state_has_sanctuary_reserve(refreshed)
            and not refreshed.get("campaign_objective_kills")
            and refreshed.get("campaign_died_during_segment") is not True
            and refreshed.get("dead") is not True
            and refreshed.get("in_combat") is not True
            and refreshed.get("enemies") in (None, [])
            and not refreshed.get("combat_target")
            and str(refreshed.get("room_vnum") or "") == "3054"
            and {"healing", "safe"}.issubset(room_flags)
            and refreshed.get("position") in {5, 6, 7}
            and hp > 0
        )
        if exact_room_inspection_retry:
            refreshed = dict(refreshed)
            results = dict(_campaign_research_results(refreshed))
            superseded_result = dict(results.pop(policy_id))
            if results:
                refreshed["campaign_research_results"] = results
            else:
                refreshed.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            attempts = dict(refreshed.get(_SANCTUARY_RESOURCE_ATTEMPTS_KEY) or {})
            prior_attempt = attempts.get(policy_id)
            if isinstance(prior_attempt, Mapping):
                updated_attempt = dict(prior_attempt)
                updated_attempt["prior_count"] = attempt_count
                updated_attempt["count"] = 0
                updated_attempt["reopened_policy_revision"] = (
                    _SANCTUARY_DEEP_ROUTE_ROOM_INSPECTION_REVISION
                )
                attempts[policy_id] = updated_attempt
                refreshed[_SANCTUARY_RESOURCE_ATTEMPTS_KEY] = attempts
            cleared = [
                str(candidate_id)
                for candidate_id in refreshed.get(
                    _CLEARED_RESEARCH_POLICIES_KEY,
                    (),
                )
                if str(candidate_id) != policy_id
            ]
            if cleared:
                refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = cleared
            else:
                refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
            refreshed[_SANCTUARY_DEEP_ROUTE_REVALIDATION_KEY] = {
                "policy_revision": (
                    _SANCTUARY_DEEP_ROUTE_ROOM_INSPECTION_REVISION
                ),
                "policy_id": policy_id,
                "boot_id": refreshed.get("world_boot_id"),
                "level": _level(refreshed),
                "status": "pending",
                "source_mobile_vnum": _MORIA_SANCTUARY_CARRIER_MOBILE_VNUM,
                "source_object_vnum": _MORIA_SANCTUARY_POTION_OBJECT_VNUM,
                "inspection_room_vnum": 4020,
                "route_origin_room_vnum": 4064,
                "route_target_room_vnum": 4152,
                "reason": _SANCTUARY_DEEP_ROUTE_ROOM_INSPECTION_REASON,
                "source_revision": refreshed.get(_SOURCE_REVISION_KEY),
                "superseded_result": superseded_result,
                "superseded_deep_route": dict(marker),
            }
            if refreshed.get("campaign_last_policy") == policy_id:
                refreshed.pop("campaign_last_policy", None)
            if refreshed.get(_SOURCE_RANKED_REVALIDATION_POLICY_KEY) == policy_id:
                refreshed.pop(_SOURCE_RANKED_REVALIDATION_POLICY_KEY, None)
            for key in (
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
                "campaign_fastwalk_route_hazards",
                "campaign_fastwalk_required_object_vnums",
                "campaign_fastwalk_where_area_checks",
                "campaign_fastwalk_where_relocation_attempts",
                "campaign_fastwalk_resume_checkpoint",
                _SOURCE_RANKED_CANDIDATE_KEY,
                _SOURCE_CONSUMABLE_SPELL_KEY,
                _SOURCE_RESOURCE_RESERVES_KEY,
            ):
                refreshed.pop(key, None)
    if previous_revision < _SOURCE_RANKED_SPECIAL_HP_REVALIDATION_REVISION:
        # The first Canyon Cyclops run consumed sanctuary only after combat
        # had begun and withdrew with an XP loss. Reopen that exact source
        # policy once now that the endpoint gate consumes sanctuary before the
        # opener and the live GMCP HP ceiling can reject oversized loads.
        policy_id = _SOURCE_RANKED_SPECIAL_HP_REVALIDATION_POLICY_ID
        loss_record = _source_ranked_xp_loss_record(refreshed, policy_id)
        marker = refreshed.get(_SOURCE_RANKED_SPECIAL_HP_REVALIDATION_KEY)
        raw_room_flags = refreshed.get("room_flags")
        room_flags = (
            {str(flag).casefold() for flag in raw_room_flags}
            if isinstance(raw_room_flags, Collection)
            and not isinstance(raw_room_flags, (str, bytes))
            else set()
        )
        try:
            hp = int(refreshed.get("hp") or 0)
        except (TypeError, ValueError):
            hp = 0
        if (
            not isinstance(marker, Mapping)
            and not refreshed.get(_SOURCE_RANKED_REVALIDATION_POLICY_KEY)
            and _level(refreshed) == 24
            and isinstance(loss_record, Mapping)
            and loss_record.get("boot_id") == refreshed.get("world_boot_id")
            and loss_record.get("level") == _level(refreshed)
            and _source_ranked_xp_loss_count(loss_record) == 1
            and _source_ranked_xp_loss_was_protected(loss_record)
            and loss_record.get("xp_delta") == -81
            and refreshed.get(_SOURCE_REVISION_KEY)
            and not refreshed.get("campaign_objective_kills")
            and refreshed.get("dead") is not True
            and refreshed.get("campaign_died_during_segment") is not True
            and refreshed.get("in_combat") is not True
            and not refreshed.get("combat_target")
            and refreshed.get("enemies") in (None, [])
            and str(refreshed.get("room_vnum") or "") == "3054"
            and {"healing", "safe"}.issubset(room_flags)
            and refreshed.get("position") in {5, 6, 7}
            and hp > 0
        ):
            refreshed = dict(refreshed)
            refreshed[_SOURCE_RANKED_SPECIAL_HP_REVALIDATION_KEY] = {
                "policy_revision": (
                    _SOURCE_RANKED_SPECIAL_HP_REVALIDATION_REVISION
                ),
                "policy_id": policy_id,
                "boot_id": refreshed.get("world_boot_id"),
                "level": _level(refreshed),
                "status": "pending",
                "reason": (
                    "reopen one exact Cyclops special probe after adding "
                    "pre-opener sanctuary and live HP budget gates"
                ),
                "source_mobile_vnum": 9202,
                "source_endpoint_room_vnum": "9204",
                "source_special": "spec_cast_cleric",
                "source_revision": refreshed.get(_SOURCE_REVISION_KEY),
                "superseded_loss": dict(loss_record),
                "superseded_loss_event_id": loss_record.get("loss_event_id"),
            }
            refreshed[_SOURCE_RANKED_REVALIDATION_POLICY_KEY] = policy_id
    if previous_revision < _ABYSS_SAFE_FIDO_REVALIDATION_REVISION:
        # The pre-fix Abyss probes stopped at the aerial reserve before any
        # target engagement because randomized-route preflight incorrectly
        # blocked source-safe ``spec_fido`` rooms. Reopen only the preferred
        # 7548 reset after the planner fix; preserve the old movement result
        # and leave the alternate 7544 route quarantined.
        policy_id = _ABYSS_SAFE_FIDO_REVALIDATION_POLICY_ID
        result = _campaign_research_results(refreshed).get(policy_id)
        marker = refreshed.get(_ABYSS_SAFE_FIDO_REVALIDATION_KEY)
        raw_room_flags = refreshed.get("room_flags")
        room_flags = (
            {str(flag).casefold() for flag in raw_room_flags}
            if isinstance(raw_room_flags, Collection)
            and not isinstance(raw_room_flags, (str, bytes))
            else set()
        )
        try:
            hp = int(refreshed.get("hp") or 0)
            max_hp = int(refreshed.get("max_hp") or 0)
        except (TypeError, ValueError):
            hp = max_hp = 0
        exact_abyss_reopen = bool(
            not isinstance(marker, Mapping)
            and not refreshed.get(_SOURCE_RANKED_REVALIDATION_POLICY_KEY)
            and _level(refreshed) == 25
            and refreshed.get("world_boot_id")
            and refreshed.get(_SOURCE_REVISION_KEY)
            and isinstance(result, Mapping)
            and result.get("boot_id") == refreshed.get("world_boot_id")
            and result.get("observed") is False
            and result.get("viable") is False
            and result.get("route_hazard") == _ABYSS_SAFE_FIDO_REVALIDATION_HAZARD
            and result.get("completed_kill") is not True
            and result.get("xp_loss_observed") is not True
            and not refreshed.get("campaign_source_ranked_xp_loss_policies")
            and not refreshed.get("dead")
            and refreshed.get("campaign_died_during_segment") is not True
            and not refreshed.get("in_combat")
            and refreshed.get("enemies") in (None, [])
            and not refreshed.get("combat_target")
            and str(refreshed.get("room_vnum") or "")
            in set(_MIDGAARD_HEALER_CHECKPOINT_ROOMS)
            and {"healing", "safe"}.issubset(room_flags)
            and refreshed.get("position") in {5, 6, 7}
            and hp > 0
            and max_hp > 0
        )
        if exact_abyss_reopen:
            refreshed = dict(refreshed)
            results = dict(_campaign_research_results(refreshed))
            superseded_result = dict(results.pop(policy_id))
            if results:
                refreshed["campaign_research_results"] = results
            else:
                refreshed.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            if refreshed.get("campaign_last_policy") == policy_id:
                refreshed.pop("campaign_last_policy", None)
            for key in (
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_consider_outcomes",
                "campaign_fastwalk_route_hazards",
                "campaign_fastwalk_resume_checkpoint",
                _SOURCE_RANKED_CANDIDATE_KEY,
            ):
                refreshed.pop(key, None)
            refreshed[_ABYSS_SAFE_FIDO_REVALIDATION_KEY] = {
                "policy_revision": _ABYSS_SAFE_FIDO_REVALIDATION_REVISION,
                "policy_id": policy_id,
                "boot_id": refreshed.get("world_boot_id"),
                "level": _level(refreshed),
                "status": "pending",
                "source_mobile_vnum": 7508,
                "source_endpoint_room_vnum": "7548",
                "source_revision": refreshed.get(_SOURCE_REVISION_KEY),
                "reason": (
                    "reopen one exact Abyss navigation result after allowing "
                    "source-safe spec_fido rooms through randomized preflight"
                ),
                "superseded_result": superseded_result,
            }
            refreshed[_SOURCE_RANKED_REVALIDATION_POLICY_KEY] = policy_id
    if previous_revision < _CAMPAIGN_POLICY_REVISION:
        if _level(refreshed) >= QUESTMASTER_MAX_LEVEL and (
            "recall_points_observed" not in refreshed
        ):
            # Older checkpoints cannot distinguish an empty list from an
            # unperformed audit. Force one explicit live list observation at
            # the remote-quest boundary instead of guessing ownership.
            refreshed["recall_points_observed"] = bool(
                refreshed.get("recall_points")
            )
    daycare_ring_abort = str(refreshed.get("fastwalk_abort_reason") or "")
    if (
        previous_revision < _CAMPAIGN_POLICY_REVISION
        and refreshed.get("fastwalk_route") == "dwarven-daycare-ring"
        and daycare_ring_abort.startswith(
            "required-loot endpoint contained source-registered preflight hazard "
        )
        and "before 'abused and old doll' confirmation" in daycare_ring_abort
        and refreshed.get("campaign_fastwalk_route_preflight_complete") is True
        and refreshed.get("campaign_fastwalk_target_present_observed") is True
        and refreshed.get("world_boot_id") is not None
        and _campaign_item_count(refreshed, "pink ice ring") < 2
    ):
        # Preserve one bounded retry after the exact live crowd failure; the
        # runtime history repair below restores only cooldown already earned.
        refreshed["campaign_daycare_ring_attempted_level"] = _level(refreshed)
        refreshed[_DAYCARE_RING_ATTEMPT_BOOT_KEY] = refreshed["world_boot_id"]
        refreshed[_DAYCARE_RING_COOLDOWN_KEY] = max(
            int(refreshed.get(_DAYCARE_RING_COOLDOWN_KEY) or 0),
            _DAYCARE_RING_COOLDOWN_SEGMENTS,
        )
    if previous_revision < 151:
        # Source-ranked negative considers are level-and-reboot terminal. Old
        # checkpoints attached generic retry metadata even though selection
        # already treated the consideration as authoritative.
        results = _campaign_research_results(refreshed)
        cooldowns = dict(
            refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
        )
        changed = False
        for policy_id, raw_result in list(results.items()):
            if not (
                policy_id.startswith(_SOURCE_RANKED_POLICY_PREFIX)
                and isinstance(raw_result, Mapping)
                and raw_result.get("consider_viable") is False
            ):
                continue
            result = dict(raw_result)
            for key in ("retryable_failure", "previously_productive"):
                if key in result:
                    result.pop(key, None)
                    changed = True
            results[policy_id] = result
            if policy_id in cooldowns:
                cooldowns.pop(policy_id, None)
                changed = True
        if changed:
            refreshed["campaign_research_results"] = results
            if cooldowns:
                refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = cooldowns
            else:
                refreshed.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
    if previous_revision < 152:
        throughput_limit = refreshed.get(
            _SOURCE_RANKED_THROUGHPUT_LIMIT_KEY
        )
        if (
            isinstance(throughput_limit, Mapping)
            and throughput_limit.get("limits") == ["health"]
        ):
            # The old generated circuit applied each target's 85% fresh-start
            # gate after a kill, so ordinary recoverable damage was mislabeled
            # as a character throughput deficiency.
            refreshed.pop(_SOURCE_RANKED_THROUGHPUT_LIMIT_KEY, None)
    if previous_revision < 153:
        throughput_limit = refreshed.get(
            _SOURCE_RANKED_THROUGHPUT_LIMIT_KEY
        )
        if isinstance(throughput_limit, Mapping):
            old_limits = list(throughput_limit.get("limits") or ())
            limits = [limit for limit in old_limits if limit != "mana"]
            if limits != old_limits:
                if limits:
                    refreshed[_SOURCE_RANKED_THROUGHPUT_LIMIT_KEY] = {
                        **throughput_limit,
                        "limits": limits,
                    }
                else:
                    # The old post-loot gate withdrew at 30% mana even though
                    # ordinary field continuation is legal down to 7.5%.
                    refreshed.pop(_SOURCE_RANKED_THROUGHPUT_LIMIT_KEY, None)
    if previous_revision < 150:
        # Revision 149 treated globally wandering Midgaard fidos and the
        # vagabond as ambiguous crowds after they crossed into the Circus.
        # Reopen only the affected generated Bearded Lady/Illusionist circuit;
        # all unrelated live crowd evidence remains authoritative.
        candidate_record = refreshed.get(_SOURCE_RANKED_CANDIDATE_KEY)
        if isinstance(candidate_record, Mapping):
            circuit_records = candidate_record.get("circuit")
            candidate_records = (
                candidate_record,
                *(
                    tuple(circuit_records)
                    if isinstance(circuit_records, (list, tuple))
                    else ()
                ),
            )
            affected_candidate_vnums = {
                int(record.get("mobile_vnum") or 0)
                for record in candidate_records
                if isinstance(record, Mapping)
                and str(record.get("area_file") or "").casefold()
                == "circus.are"
            }
            affected_policy_ids = set(
                _source_ranked_circuit_policy_ids(
                    candidate_record,
                    primary_policy_id=str(
                        refreshed.get("campaign_last_policy") or ""
                    ),
                )
            )
            results = _campaign_research_results(refreshed)
            stale_crowd_policy_ids = {
                policy_id
                for policy_id in affected_policy_ids
                if isinstance(results.get(policy_id), Mapping)
                and results[policy_id].get("observed") is False
                and results[policy_id].get("crowded") is True
            }
            if (
                affected_candidate_vnums.intersection({4406, 4407})
                and stale_crowd_policy_ids
            ):
                for policy_id in stale_crowd_policy_ids:
                    results.pop(policy_id, None)
                if results:
                    refreshed["campaign_research_results"] = results
                else:
                    refreshed.pop("campaign_research_results", None)
                for cooldown_key in (
                    _RESEARCH_ABSENCE_COOLDOWN_KEY,
                    _RESEARCH_CROWD_COOLDOWN_KEY,
                    _SOURCE_RANKED_CROWD_ATTEMPTS_KEY,
                ):
                    cooldowns = dict(refreshed.get(cooldown_key) or {})
                    for policy_id in stale_crowd_policy_ids:
                        cooldowns.pop(policy_id, None)
                    if cooldowns:
                        refreshed[cooldown_key] = cooldowns
                    else:
                        refreshed.pop(cooldown_key, None)
                cleared = {
                    str(policy_id)
                    for policy_id in refreshed.get(
                        _CLEARED_RESEARCH_POLICIES_KEY,
                        (),
                    )
                }
                cleared.difference_update(stale_crowd_policy_ids)
                if cleared:
                    refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(cleared)
                else:
                    refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
                if (
                    refreshed.get("campaign_last_policy")
                    in stale_crowd_policy_ids
                ):
                    refreshed.pop("campaign_last_policy", None)
                refreshed.pop(_SOURCE_RANKED_CANDIDATE_KEY, None)
                refreshed.pop("campaign_fastwalk_crowded", None)
                refreshed.pop("campaign_fastwalk_abort_reason", None)
    if previous_revision < 136:
        # Revision 135 counted the source-trivial Circus mother and fido as a
        # crowd around the ticket clerk. Reopen only that exact pre-fix result.
        circus_policy_id = _FAME_RECOVERY_CIRCUS_POLICY.policy_id
        circus_result = _campaign_research_results(refreshed).get(
            circus_policy_id
        )
        circus_abort = str(
            refreshed.get("campaign_fastwalk_abort_reason") or ""
        )
        if (
            refreshed.get("campaign_last_policy") == circus_policy_id
            and isinstance(circus_result, dict)
            and circus_result.get("crowded") is True
            and circus_abort.startswith(_FIELD_ROOM_CROWD_ABORT_PREFIX)
            and "ticket clerk" in circus_abort.casefold()
        ):
            research_results = _campaign_research_results(refreshed)
            research_results.pop(circus_policy_id, None)
            if research_results:
                refreshed["campaign_research_results"] = research_results
            else:
                refreshed.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(circus_policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            refreshed.pop("campaign_fastwalk_crowded", None)
            refreshed.pop("campaign_fastwalk_abort_reason", None)
    if previous_revision < 137:
        # Fame routes previously copied their 95% start requirement into the
        # in-combat floor, forcing a flee after the first ordinary hit.
        fame_policy_ids = {
            _FAME_RECOVERY_CIRCUS_POLICY.policy_id,
            _FAME_RECOVERY_POLICY.policy_id,
            _FAME_RECOVERY_LOTUS_POLICY.policy_id,
        }
        current_policy_id = str(refreshed.get("campaign_last_policy") or "")
        stale_fame_floor_abort = (
            str(refreshed.get("campaign_fastwalk_abort_reason") or "")
            == "field combat aborted for safety: health at or below 95%"
        )
        if current_policy_id in fame_policy_ids and stale_fame_floor_abort:
            research_results = _campaign_research_results(refreshed)
            research_results.pop(current_policy_id, None)
            if research_results:
                refreshed["campaign_research_results"] = research_results
            else:
                refreshed.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(current_policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            refreshed.pop("campaign_fastwalk_abort_reason", None)
    if previous_revision < 138:
        # Losing sanctuary before the opener is an acquisition dependency, not
        # an area-state failure. Preserve the viable target and reopen the
        # reserve route immediately.
        fame_policy_ids = {
            _FAME_RECOVERY_CIRCUS_POLICY.policy_id,
            _FAME_RECOVERY_POLICY.policy_id,
            _FAME_RECOVERY_LOTUS_POLICY.policy_id,
        }
        current_policy_id = str(refreshed.get("campaign_last_policy") or "")
        if (
            current_policy_id in fame_policy_ids
            and _FIELD_REQUIRED_SANCTUARY_ABORT_FRAGMENT
            in str(refreshed.get("campaign_fastwalk_abort_reason") or "")
        ):
            results = _campaign_research_results(refreshed)
            results[current_policy_id] = {
                "observed": True,
                "viable": True,
                "completed_kill": False,
                "protection_required": "sanctuary",
                "boot_id": refreshed.get("world_boot_id"),
            }
            refreshed["campaign_research_results"] = results
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(current_policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
    if previous_revision < 139:
        # Before arrival-line interception, a source target could visibly walk
        # into the active route without exposing its TARGETMODE selector. Reopen
        # only the current reserve result that was neither absent nor hazardous.
        reserve_policy_id = _SOURCE_RANKED_SANCTUARY_RESERVE_POLICY.policy_id
        reserve_result = _campaign_research_results(refreshed).get(
            reserve_policy_id
        )
        if (
            refreshed.get("campaign_last_policy") == reserve_policy_id
            and refreshed.get("campaign_fastwalk_target_absent") is False
            and not refreshed.get("campaign_fastwalk_abort_reason")
            and isinstance(reserve_result, dict)
            and reserve_result.get("boot_id") == refreshed.get("world_boot_id")
            and reserve_result.get("completed_kill") is not True
            and reserve_result.get("observed") is True
            and reserve_result.get("viable") is False
            and reserve_result.get("retryable_failure") is True
        ):
            results = _campaign_research_results(refreshed)
            results.pop(reserve_policy_id, None)
            if results:
                refreshed["campaign_research_results"] = results
            else:
                refreshed.pop("campaign_research_results", None)
            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                cooldowns.pop(reserve_policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)
            refreshed.pop("campaign_fastwalk_target_absent", None)
    if previous_revision < 125:
        # The source mobile recognizer stopped counting a mobile's short
        # description when it duplicated the room title. Reopen only the
        # current-reboot crowd results produced by that false count; observed
        # crowds and evidence from another reboot remain authoritative.
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        stale_crowd_policies = {
            str(policy_id)
            for policy_id, raw_result in research_results.items()
            if (
                str(policy_id).startswith(_SOURCE_RANKED_POLICY_PREFIX)
                and isinstance(raw_result, dict)
                and raw_result.get("boot_id") == refreshed.get("world_boot_id")
                and raw_result.get("observed") is False
                and raw_result.get("crowded") is True
                and raw_result.get("crowd_exhausted") is True
            )
        }
        if stale_crowd_policies:
            for policy_id in stale_crowd_policies:
                research_results.pop(policy_id, None)
            if research_results:
                refreshed["campaign_research_results"] = research_results
            else:
                refreshed.pop("campaign_research_results", None)

            for cooldown_key in (
                _RESEARCH_ABSENCE_COOLDOWN_KEY,
                _RESEARCH_CROWD_COOLDOWN_KEY,
            ):
                cooldowns = dict(refreshed.get(cooldown_key) or {})
                for policy_id in stale_crowd_policies:
                    cooldowns.pop(policy_id, None)
                if cooldowns:
                    refreshed[cooldown_key] = cooldowns
                else:
                    refreshed.pop(cooldown_key, None)

            crowd_attempts = dict(
                refreshed.get(_SOURCE_RANKED_CROWD_ATTEMPTS_KEY) or {}
            )
            for policy_id in stale_crowd_policies:
                crowd_attempts.pop(policy_id, None)
            if crowd_attempts:
                refreshed[_SOURCE_RANKED_CROWD_ATTEMPTS_KEY] = crowd_attempts
            else:
                refreshed.pop(_SOURCE_RANKED_CROWD_ATTEMPTS_KEY, None)

            cleared_research_policies = {
                str(policy_id)
                for policy_id in refreshed.get(
                    _CLEARED_RESEARCH_POLICIES_KEY, ()
                )
            }
            cleared_research_policies.difference_update(stale_crowd_policies)
            if cleared_research_policies:
                refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(
                    cleared_research_policies
                )
            else:
                refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)

            if refreshed.get("campaign_last_policy") in stale_crowd_policies:
                refreshed.pop("campaign_last_policy", None)
                refreshed.pop(_SOURCE_RANKED_CANDIDATE_KEY, None)
                for key in (
                    "campaign_fastwalk_target_absent",
                    "campaign_fastwalk_target_present_observed",
                    "campaign_fastwalk_crowded",
                    "campaign_fastwalk_abort_reason",
                    "campaign_fastwalk_consider_outcomes",
                ):
                    refreshed.pop(key, None)
            if (
                refreshed.get(_SOURCE_RANKED_RETRY_EXHAUSTED_KEY)
                in stale_crowd_policies
            ):
                refreshed.pop(_SOURCE_RANKED_RETRY_EXHAUSTED_KEY, None)
                refreshed.pop(_SOURCE_RANKED_RETRY_EXHAUSTED_BOOT_KEY, None)
    if previous_revision <= 117:
        # A bounded return could overwrite the concrete Galaxy preflight
        # hazard in older checkpoints after the runner had already observed
        # it. Reconstruct that source-backed result once so the scheduler
        # rotates away instead of repeating the same route.
        current_policy = str(refreshed.get("campaign_last_policy") or "")
        current_abort = str(
            refreshed.get("campaign_fastwalk_abort_reason") or ""
        )
        if (
            current_policy in _GALAXY_ROUTE_HAZARD_POLICY_IDS
            and refreshed.get("campaign_fastwalk_route_preflight_hazard_observed")
            is True
            and current_abort.startswith(
                "segment runtime boundary requested a safe healer return"
            )
        ):
            route_hazard = (
                "field route preflight found source-registered hazard "
                "'shadow guardian' in room 1300"
            )
            migrated_results = dict(
                refreshed.get("campaign_research_results") or {}
            )
            migrated_results[current_policy] = {
                "observed": False,
                "viable": False,
                "route_hazard": route_hazard,
                "boot_id": refreshed.get("world_boot_id"),
            }
            refreshed["campaign_research_results"] = migrated_results
            absence_cooldowns = dict(
                refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
            )
            retry_cooldown = _research_absence_retry_cooldown(
                current_policy,
                default=_DEFAULT_RESEARCH_CROWD_COOLDOWN,
            )
            if retry_cooldown is not None:
                absence_cooldowns[current_policy] = retry_cooldown
            refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
            refreshed["campaign_fastwalk_abort_reason"] = route_hazard
    if previous_revision <= 117:
        # Older checkpoints recorded crowd evidence without distinguishing a
        # first observation from a repeated source-ranked search. Seed one
        # attempt so the next same-reboot crowd result can rotate normally.
        current_policy = str(refreshed.get("campaign_last_policy") or "")
        current_result = _campaign_research_results(refreshed).get(
            current_policy
        )
        current_attempts = dict(
            refreshed.get(_SOURCE_RANKED_CROWD_ATTEMPTS_KEY) or {}
        )
        if (
            current_policy.startswith(_SOURCE_RANKED_POLICY_PREFIX)
            and isinstance(current_result, dict)
            and current_result.get("crowded") is True
            and current_result.get("boot_id") == refreshed.get("world_boot_id")
            and current_policy not in current_attempts
        ):
            current_attempts[current_policy] = {
                "boot_id": refreshed.get("world_boot_id"),
                "count": _SOURCE_RANKED_CROWD_ROTATION_THRESHOLD - 1,
            }
            refreshed[_SOURCE_RANKED_CROWD_ATTEMPTS_KEY] = current_attempts
    if previous_revision <= 117:
        # Older checkpoints treated a present but unfinished research hunt as
        # immediately retryable, which could replay the same target forever.
        # Preserve the evidence, but rotate it behind productive field work.
        migrated_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        absence_cooldowns = dict(
            refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
        )
        changed = False
        for policy_id, raw_result in list(migrated_results.items()):
            if not (
                policy_id.startswith(_SOURCE_RANKED_POLICY_PREFIX)
                and isinstance(raw_result, dict)
                and raw_result.get("boot_id") == refreshed.get("world_boot_id")
                and raw_result.get("observed") is True
                and raw_result.get("viable") is False
                and raw_result.get("completed_kill") is False
                and not raw_result.get("absent")
                and not raw_result.get("route_hazard")
                and not raw_result.get("crowded")
                and not raw_result.get("unattackable")
            ):
                continue
            migrated_result = dict(raw_result)
            migrated_result["retryable_failure"] = True
            retry_cooldown = _research_absence_retry_cooldown(
                policy_id,
                default=_DEFAULT_RESEARCH_CROWD_COOLDOWN,
            )
            if (
                migrated_results.get(policy_id) != migrated_result
                or absence_cooldowns.get(policy_id) != retry_cooldown
            ):
                changed = True
            migrated_results[policy_id] = migrated_result
            absence_cooldowns[policy_id] = retry_cooldown
        if changed:
            refreshed["campaign_research_results"] = migrated_results
            refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
    bardoosh_was_unobserved = bool(
        state.get("campaign_last_policy") == _BARDOOSH_POLICY_ID
        and not bool(
            original_research_results.get(_BARDOOSH_POLICY_ID, {}).get(
                "observed"
            )
        )
    )
    bardoosh_has_result = _BARDOOSH_POLICY_ID in completed_policy_ids
    if (
        previous_revision < 78
        and bardoosh_was_unobserved
        and not bardoosh_has_result
    ):
        refreshed["campaign_fastwalk_abort_reason"] = (
            _BARDOOSH_ROUTE_FIX_RETRY_REASON
        )
    elif (
        previous_revision < 79
        and bardoosh_was_unobserved
        and not bardoosh_has_result
    ):
        refreshed["campaign_fastwalk_abort_reason"] = (
            _BARDOOSH_IDENTITY_FIX_RETRY_REASON
        )
    elif (
        previous_revision < 80
        and state.get("campaign_last_policy") == _BARDOOSH_POLICY_ID
        and (
            bardoosh_has_result
            or state.get("campaign_fastwalk_abort_reason")
            in {
                _BARDOOSH_ROUTE_FIX_RETRY_REASON,
                _BARDOOSH_IDENTITY_FIX_RETRY_REASON,
            }
        )
    ):
        refreshed.pop("campaign_fastwalk_abort_reason", None)
    nobleman_result = original_research_results.get(_NOBLEMAN_POLICY_ID)
    if (
        previous_revision < 81
        and isinstance(nobleman_result, dict)
        and nobleman_result.get("observed") is False
    ):
        refreshed["campaign_fastwalk_abort_reason"] = (
            _NOBLEMAN_ROUTE_FIX_RETRY_REASON
        )
    elif (
        previous_revision < 82
        and isinstance(nobleman_result, dict)
        and nobleman_result.get("observed") is False
    ):
        refreshed["campaign_fastwalk_abort_reason"] = (
            _NOBLEMAN_IDENTITY_FIX_RETRY_REASON
        )
    worker_result = original_research_results.get(_DWARVEN_WORKERS_POLICY_ID)
    if (
        previous_revision < 91
        and isinstance(worker_result, dict)
        and worker_result.get("observed") is False
    ):
        refreshed["campaign_fastwalk_abort_reason"] = (
            _DWARVEN_WORKERS_SEARCH_FIX_RETRY_REASON
        )
    # The Forest target can repopulate during the same reboot. Retire the old
    # reboot-scoped attempt marker and allow one immediate retry.
    if previous_revision < 83:
        refreshed.pop(_PIERCING_WEAPON_UPGRADE_BOOT_KEY, None)
        refreshed.pop(_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY, None)
    if previous_revision < 85 and int(
        state.get(_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY) or 0
    ) > 0:
        refreshed.pop(_PIERCING_WEAPON_UPGRADE_BOOT_KEY, None)
        refreshed.pop(_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY, None)
    if previous_revision < 87:
        refreshed.pop("campaign_training_cap_gear_attempted_level", None)
        refreshed.pop("campaign_training_cap_gear_recovered_level", None)
    if previous_revision < 93:
        refreshed.pop(
            _INTERMEDIATE_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY,
            None,
        )
    if (
        previous_revision < 94
        and int(refreshed.get(_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY) or 0) > 0
    ):
        refreshed[_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY] = max(
            int(refreshed[_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY]),
            _PIERCING_WEAPON_UPGRADE_COOLDOWN_SEGMENTS,
        )
    if previous_revision < 96:
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        watchman_result = research_results.get(_MIRROR_WATCHMAN_POLICY_ID)
        if (
            isinstance(watchman_result, dict)
            and watchman_result.get("observed") is False
        ):
            research_results.pop(_MIRROR_WATCHMAN_POLICY_ID)
            refreshed["campaign_research_results"] = research_results
    if previous_revision < 98:
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        soldier_result = research_results.get(_SHADOW_KEEP_SOLDIER_POLICY_ID)
        if (
            isinstance(soldier_result, dict)
            and soldier_result.get("observed") is False
        ):
            research_results.pop(_SHADOW_KEEP_SOLDIER_POLICY_ID)
            refreshed["campaign_research_results"] = research_results
    if previous_revision < 99:
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        if _MIRROR_WATCHMAN_POLICY_ID in research_results:
            research_results.pop(_MIRROR_WATCHMAN_POLICY_ID)
            refreshed["campaign_research_results"] = research_results
    if previous_revision < 100:
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        stag_result = research_results.get(_CRYSTALMIR_WHITE_STAG_POLICY_ID)
        if isinstance(stag_result, dict) and stag_result.get("absent"):
            absence_cooldowns = dict(
                refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
            )
            absence_cooldowns.setdefault(
                _CRYSTALMIR_WHITE_STAG_POLICY_ID,
                _RESEARCH_ABSENCE_RETRY_COOLDOWNS[
                    _CRYSTALMIR_WHITE_STAG_POLICY_ID
                ],
            )
            refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
    if previous_revision < 101:
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        research_results.pop(_HIGHTOWER_JAILOR_POLICY_ID, None)
        research_results.pop(_HIGHTOWER_JAILOR_HUNT_POLICY_ID, None)
        if research_results:
            refreshed["campaign_research_results"] = research_results
        else:
            refreshed.pop("campaign_research_results", None)
        absence_cooldowns = dict(
            refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
        )
        absence_cooldowns.pop(_HIGHTOWER_JAILOR_POLICY_ID, None)
        absence_cooldowns.pop(_HIGHTOWER_JAILOR_HUNT_POLICY_ID, None)
        if absence_cooldowns:
            refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
        else:
            refreshed.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
        cleared_research_policies = {
            str(policy_id)
            for policy_id in refreshed.get(_CLEARED_RESEARCH_POLICIES_KEY, ())
        }
        cleared_research_policies.update(
            {
                _HIGHTOWER_JAILOR_POLICY_ID,
                _HIGHTOWER_JAILOR_HUNT_POLICY_ID,
            }
        )
        refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(
            cleared_research_policies
        )
        refreshed.pop("campaign_fastwalk_target_absent", None)
    if previous_revision < 102:
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        research_results.pop(_GALAXY_RED_SUPERGIANT_POLICY_ID, None)
        research_results.pop("galaxy-red-supergiant-hunt-17-20", None)
        if research_results:
            refreshed["campaign_research_results"] = research_results
        else:
            refreshed.pop("campaign_research_results", None)
        absence_cooldowns = dict(
            refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
        )
        absence_cooldowns.pop(_GALAXY_RED_SUPERGIANT_POLICY_ID, None)
        absence_cooldowns.pop("galaxy-red-supergiant-hunt-17-20", None)
        if absence_cooldowns:
            refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
        else:
            refreshed.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
        if refreshed.get("campaign_last_policy") in {
            _GALAXY_RED_SUPERGIANT_POLICY_ID,
            "galaxy-red-supergiant-hunt-17-20",
        }:
            refreshed.pop("campaign_fastwalk_target_absent", None)
            refreshed.pop("campaign_fastwalk_abort_reason", None)
    if (
        previous_revision < 103
        and refreshed.get("campaign_last_policy")
        in {
            _MAHNTOR_ROCK_TOAD_CIRCUIT_POLICY_ID,
            _MAHNTOR_ROCK_TOAD_HUNT_POLICY_ID,
        }
        and str(refreshed.get("campaign_fastwalk_abort_reason") or "")
        .startswith(_MAHNTOR_ROUTE_ABORT_PREFIX)
    ):
        # The old circuit registered a non-contiguous destination sequence and
        # could abort before it reached its next source reset room.
        refreshed.pop("campaign_fastwalk_abort_reason", None)
    if previous_revision < 104:
        # Below-band evidence recorded before room-specific sightings existed
        # could not identify which Mahn-Tor reset produced it. Re-evaluate the
        # route once rather than carrying an anonymous whole-policy exclusion.
        exclusions = dict(
            refreshed.get(_BELOW_BAND_POLICY_EXCLUSIONS_KEY) or {}
        )
        for policy_id in (
            _MAHNTOR_ROCK_TOAD_CIRCUIT_POLICY_ID,
            _MAHNTOR_ROCK_TOAD_HUNT_POLICY_ID,
        ):
            exclusions.pop(policy_id, None)
        if exclusions:
            refreshed[_BELOW_BAND_POLICY_EXCLUSIONS_KEY] = exclusions
        else:
            refreshed.pop(_BELOW_BAND_POLICY_EXCLUSIONS_KEY, None)
        sightings = dict(refreshed.get(_BELOW_BAND_SIGHTINGS_KEY) or {})
        for policy_id in (
            _MAHNTOR_ROCK_TOAD_CIRCUIT_POLICY_ID,
            _MAHNTOR_ROCK_TOAD_HUNT_POLICY_ID,
        ):
            sightings.pop(policy_id, None)
        if sightings:
            refreshed[_BELOW_BAND_SIGHTINGS_KEY] = sightings
        else:
            refreshed.pop(_BELOW_BAND_SIGHTINGS_KEY, None)
    if previous_revision < 105:
        # Revision 104 recorded the Shire prince with an article that the
        # source-backed target parser removes. Clear only that false absence
        # so the corrected exact identity gets one live retry.
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        for policy_id in (
            _SHIRE_DWARVEN_PRINCE_POLICY_ID,
            _SHIRE_DWARVEN_PRINCE_HUNT_POLICY_ID,
        ):
            research_results.pop(policy_id, None)
        if research_results:
            refreshed["campaign_research_results"] = research_results
        else:
            refreshed.pop("campaign_research_results", None)
        absence_cooldowns = dict(
            refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
        )
        for policy_id in (
            _SHIRE_DWARVEN_PRINCE_POLICY_ID,
            _SHIRE_DWARVEN_PRINCE_HUNT_POLICY_ID,
        ):
            absence_cooldowns.pop(policy_id, None)
        if absence_cooldowns:
            refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
        else:
            refreshed.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
        if refreshed.get("campaign_last_policy") in {
            _SHIRE_DWARVEN_PRINCE_POLICY_ID,
            _SHIRE_DWARVEN_PRINCE_HUNT_POLICY_ID,
        }:
            refreshed.pop("campaign_fastwalk_target_absent", None)
            refreshed.pop("campaign_fastwalk_abort_reason", None)
    if previous_revision < 106:
        # The first corrected-identity retry could consider a crowded room
        # before the shared crowd gate was applied to research probes. Remove
        # only that result and cached target outcome for a clean re-probe.
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        for policy_id in (
            _SHIRE_DWARVEN_PRINCE_POLICY_ID,
            _SHIRE_DWARVEN_PRINCE_HUNT_POLICY_ID,
        ):
            research_results.pop(policy_id, None)
        if research_results:
            refreshed["campaign_research_results"] = research_results
        else:
            refreshed.pop("campaign_research_results", None)
        absence_cooldowns = dict(
            refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
        )
        for policy_id in (
            _SHIRE_DWARVEN_PRINCE_POLICY_ID,
            _SHIRE_DWARVEN_PRINCE_HUNT_POLICY_ID,
        ):
            absence_cooldowns.pop(policy_id, None)
        if absence_cooldowns:
            refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
        else:
            refreshed.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
        consider_outcomes = dict(
            refreshed.get("campaign_fastwalk_consider_outcomes") or {}
        )
        consider_outcomes.pop("dwarven prince", None)
        if consider_outcomes:
            refreshed["campaign_fastwalk_consider_outcomes"] = consider_outcomes
        else:
            refreshed.pop("campaign_fastwalk_consider_outcomes", None)
    if previous_revision < 108:
        # The Pyramid probe used to inspect only reset room 2643. A live
        # locator proved that Ali Baba can be elsewhere in the source-vetted
        # tunnel branch, so clear only the stale Pyramid absence for one
        # bounded re-probe.
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        for policy_id in (
            _PYRAMID_ALI_BABA_POLICY_ID,
            _PYRAMID_ALI_BABA_HUNT_POLICY_ID,
        ):
            research_results.pop(policy_id, None)
        if research_results:
            refreshed["campaign_research_results"] = research_results
        else:
            refreshed.pop("campaign_research_results", None)
        absence_cooldowns = dict(
            refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
        )
        for policy_id in (
            _PYRAMID_ALI_BABA_POLICY_ID,
            _PYRAMID_ALI_BABA_HUNT_POLICY_ID,
        ):
            absence_cooldowns.pop(policy_id, None)
        if absence_cooldowns:
            refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
        else:
            refreshed.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
        if refreshed.get("campaign_last_policy") in {
            _PYRAMID_ALI_BABA_POLICY_ID,
            _PYRAMID_ALI_BABA_HUNT_POLICY_ID,
        }:
            refreshed.pop("campaign_fastwalk_target_absent", None)
            refreshed.pop("campaign_fastwalk_abort_reason", None)
    if previous_revision < 109:
        # The first extended Pyramid sweep still stopped on a redundant route
        # destination before reaching the source-connected tunnel rooms. Clear
        # only that stale absence so the corrected route gets one fresh probe.
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        pyramid_result = research_results.get(_PYRAMID_ALI_BABA_POLICY_ID)
        if isinstance(pyramid_result, dict) and pyramid_result.get("absent"):
            research_results.pop(_PYRAMID_ALI_BABA_POLICY_ID, None)
            research_results.pop(_PYRAMID_ALI_BABA_HUNT_POLICY_ID, None)
            if research_results:
                refreshed["campaign_research_results"] = research_results
            else:
                refreshed.pop("campaign_research_results", None)
            absence_cooldowns = dict(
                refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
            )
            absence_cooldowns.pop(_PYRAMID_ALI_BABA_POLICY_ID, None)
            absence_cooldowns.pop(_PYRAMID_ALI_BABA_HUNT_POLICY_ID, None)
            if absence_cooldowns:
                refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
            else:
                refreshed.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
            if refreshed.get("campaign_last_policy") in {
                _PYRAMID_ALI_BABA_POLICY_ID,
                _PYRAMID_ALI_BABA_HUNT_POLICY_ID,
            }:
                refreshed.pop("campaign_fastwalk_target_absent", None)
                refreshed.pop("campaign_fastwalk_abort_reason", None)
    if previous_revision < 110:
        # Run 2604 found Ali Baba in source room 2639, which the previous
        # tunnel sweep did not inspect. Clear that stale absence for one probe
        # using the expanded, source-connected room list.
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        pyramid_result = research_results.get(_PYRAMID_ALI_BABA_POLICY_ID)
        if isinstance(pyramid_result, dict) and pyramid_result.get("absent"):
            research_results.pop(_PYRAMID_ALI_BABA_POLICY_ID, None)
            research_results.pop(_PYRAMID_ALI_BABA_HUNT_POLICY_ID, None)
            if research_results:
                refreshed["campaign_research_results"] = research_results
            else:
                refreshed.pop("campaign_research_results", None)
            absence_cooldowns = dict(
                refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
            )
            absence_cooldowns.pop(_PYRAMID_ALI_BABA_POLICY_ID, None)
            absence_cooldowns.pop(_PYRAMID_ALI_BABA_HUNT_POLICY_ID, None)
            if absence_cooldowns:
                refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
            else:
                refreshed.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
            if refreshed.get("campaign_last_policy") in {
                _PYRAMID_ALI_BABA_POLICY_ID,
                _PYRAMID_ALI_BABA_HUNT_POLICY_ID,
            }:
                refreshed.pop("campaign_fastwalk_target_absent", None)
            refreshed.pop("campaign_fastwalk_abort_reason", None)
    # Historical revisions treated a low nominal level as permission to
    # re-probe Galaxy routes. That is unsafe for hard preflight hazards such
    # as Shadow Guardians, so preserve their evidence for every resumed
    # campaign instead of deleting it during migration.
    if previous_revision < 120:
        # Generated source-ranked routes now navigate the randomized Shadow
        # Grove by live destination VNUM and resume on the command leaving the
        # stable destination room. Reopen old endpoint-block results so the
        # corrected route can gather real target evidence once.
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        cleared_route_hazards = {
            policy_id
            for policy_id, result in research_results.items()
            if (
                policy_id.startswith(_SOURCE_RANKED_POLICY_PREFIX)
                and isinstance(result, dict)
                and str(result.get("route_hazard") or "").startswith(
                    "official fastwalk 'source-ranked hunt "
                )
                and str(result.get("route_hazard") or "").endswith(
                    " was blocked before its endpoint"
                )
            )
        }
        for policy_id in cleared_route_hazards:
            research_results.pop(policy_id, None)
        if research_results:
            refreshed["campaign_research_results"] = research_results
        else:
            refreshed.pop("campaign_research_results", None)
        absence_cooldowns = dict(
            refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
        )
        for policy_id in cleared_route_hazards:
            absence_cooldowns.pop(policy_id, None)
        if absence_cooldowns:
            refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
        else:
            refreshed.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
        cleared_research_policies = {
            str(policy_id)
            for policy_id in refreshed.get(_CLEARED_RESEARCH_POLICIES_KEY, ())
        }
        cleared_research_policies.difference_update(cleared_route_hazards)
        if cleared_research_policies:
            refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(
                cleared_research_policies
            )
        else:
            refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
        if refreshed.get("campaign_last_policy") in cleared_route_hazards:
            refreshed.pop("campaign_fastwalk_target_absent", None)
            refreshed.pop("campaign_fastwalk_crowded", None)
            refreshed.pop("campaign_fastwalk_abort_reason", None)
    if previous_revision < 121:
        # Source-ranked candidates now share the exact room-line identity
        # parser used by TARGETMODE. Old absence results can therefore be
        # false negatives (for example, ``Secretary`` versus its source line
        # ``The Sergeant at Arm's Secretary is here.``); reopen them once.
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        stale_identity_results = {
            str(policy_id)
            for policy_id, result in research_results.items()
            if (
                str(policy_id).startswith(_SOURCE_RANKED_POLICY_PREFIX)
                and isinstance(result, dict)
                and result.get("absent") is True
            )
        }
        for policy_id in stale_identity_results:
            research_results.pop(policy_id, None)
        if research_results:
            refreshed["campaign_research_results"] = research_results
        else:
            refreshed.pop("campaign_research_results", None)
        absence_cooldowns = dict(
            refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
        )
        for policy_id in stale_identity_results:
            absence_cooldowns.pop(policy_id, None)
        if absence_cooldowns:
            refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
        else:
            refreshed.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
        cleared_research_policies = {
            str(policy_id)
            for policy_id in refreshed.get(_CLEARED_RESEARCH_POLICIES_KEY, ())
        }
        cleared_research_policies.difference_update(stale_identity_results)
        if cleared_research_policies:
            refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(
                cleared_research_policies
            )
        else:
            refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
        if refreshed.get("campaign_last_policy") in stale_identity_results:
            refreshed.pop("campaign_last_policy", None)
            refreshed.pop(_SOURCE_RANKED_CANDIDATE_KEY, None)
            for key in (
                "campaign_fastwalk_target_absent",
                "campaign_fastwalk_target_present_observed",
                "campaign_fastwalk_crowded",
                "campaign_fastwalk_abort_reason",
                "campaign_fastwalk_consider_outcomes",
            ):
                refreshed.pop(key, None)
    if previous_revision < 122:
        # Candidate records now persist whether their source route enters an
        # air room or crosses an EX_WALL exit. Re-rank the next segment rather
        # than trusting an older record that cannot carry that requirement.
        refreshed.pop(_SOURCE_RANKED_CANDIDATE_KEY, None)
    if previous_revision < 123:
        # Eastern Desert source hunts now cross the reboot-randomized maze by
        # live destination VNUM. Reopen only the old route result that was
        # caused by following a stale source direction into the worm room.
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        cleared_route_hazards = {
            policy_id
            for policy_id, result in research_results.items()
            if (
                policy_id.startswith("source-ranked-hunt-eastern-desert-")
                and isinstance(result, dict)
                and result.get("route_hazard")
                and result.get("completed_kill") is not True
            )
        }
        for policy_id in cleared_route_hazards:
            research_results.pop(policy_id, None)
        if research_results:
            refreshed["campaign_research_results"] = research_results
        else:
            refreshed.pop("campaign_research_results", None)
        for cooldown_key in (
            _RESEARCH_ABSENCE_COOLDOWN_KEY,
            _RESEARCH_CROWD_COOLDOWN_KEY,
        ):
            cooldowns = dict(refreshed.get(cooldown_key) or {})
            for policy_id in cleared_route_hazards:
                cooldowns.pop(policy_id, None)
            if cooldowns:
                refreshed[cooldown_key] = cooldowns
            else:
                refreshed.pop(cooldown_key, None)
        cleared_research_policies = {
            str(policy_id)
            for policy_id in refreshed.get(_CLEARED_RESEARCH_POLICIES_KEY, ())
        }
        cleared_research_policies.difference_update(cleared_route_hazards)
        if cleared_research_policies:
            refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(
                cleared_research_policies
            )
        else:
            refreshed.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
        if refreshed.get("campaign_last_policy") in cleared_route_hazards:
            refreshed.pop("campaign_fastwalk_target_absent", None)
            refreshed.pop("campaign_fastwalk_crowded", None)
            refreshed.pop("campaign_fastwalk_abort_reason", None)
            refreshed.pop(_SOURCE_RANKED_CANDIDATE_KEY, None)
    if not refreshed.get(_HIGHLAND_KEEPER_ROUTE_REPAIR_KEY):
        # Run 2794 exposed a source-confirmed below-band bogleech interruption
        # before the no-combat probe could apply its incidental-combat rule.
        # Clear that one stale result so the corrected runner gets one retry;
        # preserve any new route hazard after the retry.
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        keeper_result = research_results.get(_HIGHLAND_KEEPER_POLICY_ID)
        if (
            isinstance(keeper_result, dict)
            and keeper_result.get("route_hazard")
            == _DYNAMIC_FIELD_ROUTE_HAZARD_ABORT_REASON
        ):
            research_results.pop(_HIGHLAND_KEEPER_POLICY_ID, None)
            research_results.pop(_HIGHLAND_KEEPER_HUNT_POLICY_ID, None)
            if research_results:
                refreshed["campaign_research_results"] = research_results
            else:
                refreshed.pop("campaign_research_results", None)
            absence_cooldowns = dict(
                refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
            )
            absence_cooldowns.pop(_HIGHLAND_KEEPER_POLICY_ID, None)
            absence_cooldowns.pop(_HIGHLAND_KEEPER_HUNT_POLICY_ID, None)
            if absence_cooldowns:
                refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
            else:
                refreshed.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
            if refreshed.get("campaign_last_policy") in {
                _HIGHLAND_KEEPER_POLICY_ID,
                _HIGHLAND_KEEPER_HUNT_POLICY_ID,
            }:
                refreshed.pop("campaign_fastwalk_target_absent", None)
                refreshed.pop("campaign_fastwalk_abort_reason", None)
            refreshed[_HIGHLAND_KEEPER_ROUTE_REPAIR_KEY] = True
    if previous_revision < 20:
        refreshed.pop("campaign_body_gear_attempted_level", None)
    # Revision 67 replaced reboot-only ring attempts with a bounded retry.
    # Preserve a newer countdown instead of restarting it on every revision.
    if (
        previous_revision < 67
        and "campaign_daycare_ring_attempted_level" in refreshed
    ):
        refreshed[_DAYCARE_RING_COOLDOWN_KEY] = max(
            int(refreshed.get(_DAYCARE_RING_COOLDOWN_KEY) or 0),
            _DAYCARE_RING_COOLDOWN_SEGMENTS,
        )
    elif "campaign_daycare_ring_attempted_level" not in refreshed:
        refreshed.pop(_DAYCARE_RING_COOLDOWN_KEY, None)
    if previous_revision < 37:
        refreshed.pop("campaign_war_dog_collar_attempted_level", None)
        refreshed.pop(_WAR_DOG_COLLAR_ATTEMPT_BOOT_KEY, None)
        refreshed.pop(_WAR_DOG_COLLAR_COOLDOWN_KEY, None)
    return refreshed
