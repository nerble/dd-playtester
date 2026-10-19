from __future__ import annotations

import json
import re
from collections.abc import Collection, Mapping
from typing import Any

from .storage import RUN_REPORT_SUMMARY_VERSION


IDLE_PURSUIT_REVALIDATIONS_KEY = "campaign_idle_pursuit_revalidations"
REGISTERED_LOCATOR_REVALIDATIONS_KEY = "campaign_registered_locator_revalidations"
LOCATOR_ORIGIN_ABORT = "refreshed `where` located the wandering target outside the source-safe relocation graph"


def completed_single_target_hunt(
    state: Mapping[str, Any], segment: Mapping[str, Any], summary: Mapping[str, Any],
    *, policy_id: str, source_policy_id: str, mobile_vnum: int,
    prior_level_source_policy_id: str | None = None,
    audited_source_revision: str | None = None,
) -> bool:
    """Recognize a completed independent objective, never clear a failed visit."""
    run, outcomes, progress = (summary.get(key) for key in ("run", "outcomes", "progress"))
    if not all(isinstance(value, Mapping) for value in (run, outcomes, progress)):
        return False
    if (
        summary.get("summary_version") != RUN_REPORT_SUMMARY_VERSION
        or segment.get("phase") != policy_id
        or segment.get("status") not in {"success", "ready"}
        or not segment.get("finished_at") or not segment.get("run_id")
        or run.get("id") != segment.get("run_id")
        or type(segment.get("command_count")) is not int or segment["command_count"] <= 0
        or outcomes.get("execution") not in {"success", "ready"}
        or outcomes.get("objective") != "achieved" or outcomes.get("safety") != "safe"
    ):
        return False
    try:
        start = json.loads(segment.get("start_state_json") or "{}")
        end = json.loads(segment.get("end_state_json") or "{}")
    except (TypeError, ValueError):
        return False
    if not isinstance(start, Mapping) or not isinstance(end, Mapping):
        return False
    if state.get("world_boot_id") is None or not state["world_boot_id"] == start.get("world_boot_id") == end.get("world_boot_id"):
        return False
    recorded_revision = start.get("campaign_source_revision")
    current_revision = state.get("campaign_source_revision")
    if (
        not recorded_revision or not current_revision
        or recorded_revision != end.get("campaign_source_revision")
        or (current_revision != recorded_revision and audited_source_revision != current_revision)
    ):
        return False
    if type(state.get("level")) is not int or state["level"] < 1:
        return False
    if (
        type(start.get("level")) is not int or start["level"] < 1
        or type(end.get("level")) is not int or end["level"] != state["level"]
    ):
        return False
    observed_source_policy_id = source_policy_id
    if start["level"] != state["level"]:
        level_progress = progress.get("level")
        if (
            start["level"] != state["level"] - 1 or not prior_level_source_policy_id
            or not isinstance(level_progress, Mapping)
            or any(type(level_progress.get(key)) is not int for key in ("initial", "final", "change"))
            or level_progress != {"initial": start["level"], "final": state["level"], "change": 1}
            or type(progress.get("level_gains_observed")) is not int
            or progress["level_gains_observed"] != 1
        ):
            return False
        observed_source_policy_id = prior_level_source_policy_id
    # A later loss elsewhere cannot invalidate this completed encounter. Its
    # own loss total must be unchanged, and exact target quarantines still win.
    losses = [snapshot.get("campaign_xp_loss_total") for snapshot in (state, start, end)]
    if (
        any(type(value) is not int or value < 0 for value in losses)
        or losses[1] != losses[2] or losses[0] < losses[2]
    ):
        return False
    target_ids = {policy_id, source_policy_id, observed_source_policy_id}
    if prior_level_source_policy_id:
        target_ids.add(prior_level_source_policy_id)
    for key in ("campaign_registered_research_xp_loss_policies", "campaign_source_ranked_xp_loss_policies"):
        records = state.get(key) or ()
        if not isinstance(records, (list, tuple)) or any(
            not isinstance(record, Mapping) or (
                record.get("boot_id") == state["world_boot_id"]
                and record.get("policy_id") in target_ids
            ) for record in records
        ):
            return False
    for snapshot in (state, start, end):
        if (
            str(snapshot.get("room_vnum")) != "3054" or snapshot.get("dead") is not False
            or snapshot.get("in_combat") is not False or snapshot.get("enemies") not in (None, [])
            or type(snapshot.get("hp")) is not int or snapshot["hp"] <= 0
            or type(snapshot.get("xp")) is not int
        ):
            return False
    if not state["xp"] >= end["xp"] > start["xp"]:
        return False
    if any(end.get(key) for key in (
        "campaign_fastwalk_abort_reason", "campaign_fastwalk_route_hazards",
        "campaign_fastwalk_crowded", "campaign_fastwalk_target_vnum_mismatch",
        "campaign_fastwalk_unattackable_target", "campaign_fastwalk_target_absent",
    )):
        return False
    kills = progress.get("confirmed_kills")
    if not isinstance(kills, list) or len(kills) != 1 or not isinstance(kills[0], Mapping):
        return False
    kill = kills[0]
    return bool(
        kill.get("source_mobile_vnum") == mobile_vnum
        and kill.get("source_policy_id") == observed_source_policy_id
        and type(kill.get("xp_gained")) is int and kill["xp_gained"] > state["level"] * 10
        and end.get("campaign_objective_kills") == kills
        and end.get("campaign_fastwalk_source_consider_outcomes") == {observed_source_policy_id: True}
    )


def completed_prior_level_single_target_hunt(
    state: Mapping[str, Any], segment: Mapping[str, Any], summary: Mapping[str, Any],
    *, policy_id: str, prior_source_policy_id: str, current_source_policy_id: str,
    mobile_vnum: int, audited_source_revision: str | None,
) -> bool:
    """Validate a safe productive receipt exactly one level behind current state.

    This is prioritization evidence for a fresh, current-level policy only. It
    never grants combat permission; callers must still re-audit source and run
    all live identity, isolation, consider, output, and withdrawal checks.
    """
    run, outcomes, progress = (summary.get(key) for key in ("run", "outcomes", "progress"))
    if not all(isinstance(value, Mapping) for value in (run, outcomes, progress)):
        return False
    if (
        summary.get("summary_version") != RUN_REPORT_SUMMARY_VERSION
        or segment.get("phase") != policy_id or segment.get("status") != "success"
        or not segment.get("finished_at") or not segment.get("run_id")
        or run.get("id") != segment.get("run_id")
        or type(segment.get("command_count")) is not int or segment["command_count"] <= 0
        or outcomes != {"execution": "success", "objective": "achieved", "safety": "safe"}
    ):
        return False
    try:
        start = json.loads(segment.get("start_state_json") or "{}")
        end = json.loads(segment.get("end_state_json") or "{}")
    except (TypeError, ValueError):
        return False
    if not isinstance(start, Mapping) or not isinstance(end, Mapping):
        return False
    current_level = state.get("level")
    prior_level = current_level - 1 if type(current_level) is int else None
    prior_revision = start.get("campaign_source_revision")
    current_revision = state.get("campaign_source_revision")
    if (
        prior_level is None or prior_level < 1
        or state.get("world_boot_id") is None
        or not state["world_boot_id"] == start.get("world_boot_id") == end.get("world_boot_id")
        or start.get("level") != prior_level or end.get("level") != prior_level
        or not prior_revision or prior_revision != end.get("campaign_source_revision")
        or not current_revision
        or (current_revision != prior_revision and audited_source_revision != current_revision)
    ):
        return False
    for snapshot in (state, start, end):
        if (
            str(snapshot.get("room_vnum")) != "3054" or snapshot.get("dead") is not False
            or snapshot.get("in_combat") is not False or snapshot.get("enemies") not in (None, [])
            or type(snapshot.get("hp")) is not int or snapshot["hp"] <= 0
            or type(snapshot.get("xp")) is not int
        ):
            return False
    if end["xp"] <= start["xp"] or state["xp"] < end["xp"]:
        return False
    loss_totals = [snapshot.get("campaign_xp_loss_total") for snapshot in (state, start, end)]
    if (
        any(type(value) is not int or value < 0 for value in loss_totals)
        or loss_totals[1] != loss_totals[2] or loss_totals[0] < loss_totals[2]
    ):
        return False
    level_progress = progress.get("level")
    experience = progress.get("experience")
    kills = progress.get("confirmed_kills")
    if (
        not isinstance(level_progress, Mapping)
        or level_progress != {"change": 0, "final": prior_level, "initial": prior_level}
        or progress.get("level_gains_observed") != 0
        or not isinstance(experience, Mapping)
        or experience.get("change") != end["xp"] - start["xp"]
        or not isinstance(kills, list) or len(kills) != 1 or not isinstance(kills[0], Mapping)
    ):
        return False
    kill = kills[0]
    if (
        kill.get("source_mobile_vnum") != mobile_vnum
        or kill.get("source_policy_id") != prior_source_policy_id
        or type(kill.get("xp_gained")) is not int
        or kill["xp_gained"] <= prior_level * 10
        or end.get("campaign_objective_kills") != kills
        or end.get("campaign_fastwalk_source_consider_outcomes") != {prior_source_policy_id: True}
        or any(end.get(key) for key in (
            "campaign_fastwalk_abort_reason", "campaign_fastwalk_route_hazards",
            "campaign_fastwalk_crowded", "campaign_fastwalk_target_vnum_mismatch",
            "campaign_fastwalk_unattackable_target", "campaign_fastwalk_target_absent",
        ))
    ):
        return False
    target_ids = {policy_id, prior_source_policy_id, current_source_policy_id}
    for key in ("campaign_registered_research_xp_loss_policies", "campaign_source_ranked_xp_loss_policies"):
        records = state.get(key) or ()
        if not isinstance(records, (list, tuple)) or any(
            not isinstance(record, Mapping) or (
                record.get("boot_id") == state["world_boot_id"]
                and record.get("policy_id") in target_ids
            ) for record in records
        ):
            return False
    return True


def productive_crowd_reset_result(
    result: Mapping[str, Any] | None, *, level: int, boot_id: Any,
) -> dict[str, Any] | None:
    """Keep useful kills when a completed reset wait clears only a crowd."""
    if (
        not isinstance(result, Mapping) or type(level) is not int or level < 1
        or boot_id is None or result.get("boot_id") != boot_id
        or result.get("observed") is not True or result.get("viable") is not True
        or result.get("completed_kill") is not True or result.get("consider_viable") is not True
        or type(result.get("max_objective_kill_xp")) is not int
        or result["max_objective_kill_xp"] <= level * 10
        or any(result.get(key) for key in (
            "crowd_exhausted", "fatal_failure", "retryable_failure", "route_hazard",
            "absent", "unattackable", "target_vnum_mismatch", "low_reward",
        ))
    ):
        return None
    retained = dict(result)
    retained["crowded"] = False
    retained["crowd_reset_preserved_productive"] = True
    return retained


def crowded_combat_loss_target(
    state: Mapping[str, Any], segment: Mapping[str, Any], summary: Mapping[str, Any],
    *, policy_id: str, source_policy_ids: Collection[str],
) -> str | None:
    """Scope an observed extra-attacker loss without reopening that encounter."""
    run, outcomes, evidence, progress = (
        summary.get(key) for key in ("run", "outcomes", "evidence", "progress")
    )
    if not all(isinstance(value, Mapping) for value in (run, outcomes, evidence, progress)):
        return None
    counts = evidence.get("game_event_counts")
    if (
        segment.get("phase") != policy_id or segment.get("status") != "success"
        or not segment.get("finished_at") or not segment.get("run_id")
        or run.get("id") != segment.get("run_id")
        or not isinstance(segment.get("command_count"), int) or segment["command_count"] <= 0
        or outcomes != {"execution": "success", "objective": "not_achieved", "safety": "loss"}
        or not isinstance(counts, Mapping) or counts.get("character_died", 0)
        or not counts.get("experience_lost") or not progress.get("combat_starts")
        or progress.get("confirmed_kills")
    ):
        return None
    try:
        start = json.loads(segment.get("start_state_json") or "{}")
        end = json.loads(segment.get("end_state_json") or "{}")
    except (TypeError, ValueError):
        return None
    if not isinstance(start, Mapping) or not isinstance(end, Mapping):
        return None
    for key in ("level", "world_boot_id"):
        if state.get(key) is None or not state.get(key) == start.get(key) == end.get(key):
            return None
    # A source refresh cannot erase a live loss. Only negative encounter scope
    # crosses revisions; the caller must re-audit each independent alternative.
    if (
        not state.get("campaign_source_revision") or not start.get("campaign_source_revision")
        or start.get("campaign_source_revision") != end.get("campaign_source_revision")
        or not isinstance(start.get("campaign_xp_loss_total"), int)
        or not isinstance(end.get("campaign_xp_loss_total"), int)
        or end["campaign_xp_loss_total"] <= start["campaign_xp_loss_total"]
        or state.get("campaign_xp_loss_total") != end["campaign_xp_loss_total"]
    ):
        return None
    for snapshot in (state, start, end):
        if (
            str(snapshot.get("room_vnum")) != "3054" or snapshot.get("dead") is not False
            or snapshot.get("in_combat") is not False or snapshot.get("enemies") not in (None, [])
            or not isinstance(snapshot.get("hp"), int) or snapshot["hp"] <= 0
            or not isinstance(snapshot.get("max_hp"), int)
            or snapshot["hp"] < snapshot["max_hp"]
        ):
            return None
    if (
        end.get("campaign_fastwalk_crowded") is not True
        or not re.fullmatch(
            r"combat text identified '[^'\r\n]+' outside the duplicated GMCP enemy snapshot",
            str(end.get("campaign_fastwalk_abort_reason") or ""),
        )
        or any(end.get(key) for key in (
            "campaign_objective_kills", "campaign_completed_kills", "campaign_fastwalk_route_hazards",
            "campaign_fastwalk_target_vnum_mismatch", "campaign_fastwalk_unattackable_target",
        ))
    ):
        return None
    losses = [record for record in state.get("campaign_registered_research_xp_loss_policies") or ()
              if isinstance(record, Mapping) and record.get("policy_id") == policy_id
              and record.get("boot_id") == state.get("world_boot_id")]
    if (
        len(losses) != 1 or losses[0].get("level") != state["level"]
        or type(losses[0].get("loss_count")) is not int
        or losses[0].get("loss_count") < 1
        or losses[0].get("loss_event_id") != segment.get("id")
    ):
        return None
    # A campaign can reach this exact target after earlier losses on the
    # same parent hunt. Accept the newest linked event only when the start
    # checkpoint proves the immediately preceding cumulative count; a loose
    # higher count in an old snapshot is not enough to reopen siblings.
    current_loss_count = losses[0]["loss_count"]
    if current_loss_count > 1:
        prior_losses = [
            record
            for record in start.get("campaign_registered_research_xp_loss_policies")
            or ()
            if isinstance(record, Mapping)
            and record.get("policy_id") == policy_id
            and record.get("boot_id") == state.get("world_boot_id")
        ]
        if (
            len(prior_losses) != 1
            or prior_losses[0].get("level") != state["level"]
            or prior_losses[0].get("loss_count") != current_loss_count - 1
            or prior_losses[0].get("loss_event_id") in {None, segment.get("id")}
        ):
            return None
    considerations = end.get("campaign_fastwalk_source_consider_outcomes")
    if not isinstance(considerations, Mapping) or len(considerations) != 1:
        return None
    target_id, viable = next(iter(considerations.items()))
    sightings = end.get("campaign_fastwalk_source_present_sightings")
    if (
        target_id not in source_policy_ids or viable is not True
        or not isinstance(sightings, (list, tuple)) or not sightings
        or any(not isinstance(sighting, Mapping) or sighting.get("policy_id") != target_id
               for sighting in sightings)
    ):
        return None
    return str(target_id)


def registered_locator_revalidation_evidence(
    state: Mapping[str, Any], segment: Mapping[str, Any], summary: Mapping[str, Any],
    *, policy_id: str, source_policy_id: str, mobile_vnum: int, target: str,
    productive_policy_ids: Collection[str],
    location_routes: Mapping[str, Collection[str]],
    relocation_routes: Collection[tuple[str, str, tuple[str, ...]]],
) -> dict[str, Any] | None:
    """Recheck a productive, noncombat search after its missing origin is fixed."""
    markers = state.get(REGISTERED_LOCATOR_REVALIDATIONS_KEY)
    existing = markers.get(policy_id) if isinstance(markers, Mapping) else None
    if existing is not None and (
        not isinstance(existing, Mapping) or existing.get("status") != "pending"
    ):
        return None
    if source_policy_id not in productive_policy_ids:
        return None
    for key in ("campaign_registered_research_xp_loss_policies", "campaign_source_ranked_xp_loss_policies"):
        if any(isinstance(record, Mapping)
               and record.get("boot_id") == state.get("world_boot_id")
               and record.get("policy_id") in {policy_id, source_policy_id}
               for record in state.get(key) or ()):
            return None
    run, outcomes, progress = (summary.get(key) for key in ("run", "outcomes", "progress"))
    if not all(isinstance(value, Mapping) for value in (run, outcomes, progress)):
        return None
    experience, health = (progress.get(key) for key in ("experience", "health"))
    if not isinstance(experience, Mapping) or not isinstance(health, Mapping):
        return None
    if (
        segment.get("phase") != policy_id or segment.get("status") != "success"
        or not segment.get("finished_at") or not segment.get("run_id")
        or run.get("id") != segment.get("run_id")
        or not isinstance(segment.get("command_count"), int) or segment["command_count"] <= 0
        or outcomes != {"execution": "success", "objective": "not_achieved", "safety": "safe"}
        or progress.get("combat_starts") != 0 or progress.get("confirmed_kills")
        or experience.get("change") != 0 or health.get("lowest_fraction") != 1.0
    ):
        return None
    try:
        start = json.loads(segment.get("start_state_json") or "{}")
        end = json.loads(segment.get("end_state_json") or "{}")
    except (TypeError, ValueError):
        return None
    if not isinstance(start, Mapping) or not isinstance(end, Mapping):
        return None
    for key in ("level", "world_boot_id", "campaign_source_revision"):
        if state.get(key) is None or not state.get(key) == start.get(key) == end.get(key):
            return None
    # Later, unrelated fights must not replace this search's evidence or losses.
    for key in ("xp", "campaign_xp_loss_total"):
        if (not isinstance(start.get(key), int) or start.get(key) != end.get(key)
                or not isinstance(state.get(key), int)):
            return None
    if state["campaign_xp_loss_total"] < end["campaign_xp_loss_total"]:
        return None
    for snapshot in (state, start, end):
        if (
            str(snapshot.get("room_vnum")) != "3054" or snapshot.get("dead") is not False
            or snapshot.get("in_combat") is not False or snapshot.get("enemies") not in (None, [])
            or not isinstance(snapshot.get("hp"), int) or snapshot["hp"] <= 0
            or snapshot["hp"] != snapshot.get("max_hp")
        ):
            return None
    if (
        end.get("campaign_fastwalk_abort_reason") != LOCATOR_ORIGIN_ABORT
        or end.get("campaign_fastwalk_target_present_observed") is not True
        or end.get("campaign_fastwalk_target_absent") is True
        or any(end.get(key) for key in (
            "campaign_objective_kills", "campaign_completed_kills", "campaign_fastwalk_route_hazards",
            "campaign_fastwalk_source_consider_outcomes", "campaign_fastwalk_target_vnum_mismatch",
            "campaign_fastwalk_unattackable_target", "campaign_fastwalk_crowded",
        ))
    ):
        return None
    results = state.get("campaign_research_results")
    result = results.get(policy_id) if isinstance(results, Mapping) else None
    if (
        not isinstance(result, Mapping) or result.get("boot_id") != state.get("world_boot_id")
        or result.get("route_hazard") != LOCATOR_ORIGIN_ABORT
        or any(result.get(key) for key in ("fatal_failure", "completed_kill", "crowded", "target_vnum_mismatch"))
    ):
        return None
    locators = end.get("campaign_fastwalk_where_decisions")
    decision = locators[-1] if isinstance(locators, list) and locators else None
    if (
        not isinstance(decision, Mapping) or decision.get("source_mobile_vnum") != mobile_vnum
        or decision.get("target") != target.casefold() or decision.get("relocation") is not True
        or decision.get("planned_endpoints") != [] or decision.get("selected_relocation")
        or decision.get("registered_route_origin") is not None
    ):
        return None
    origin = str(decision.get("room_vnum") or "")
    locations, mapped = decision.get("locations"), decision.get("mapped_rooms")
    if not isinstance(locations, list) or not locations or not isinstance(mapped, Mapping):
        return None
    if any(not isinstance(label, str) or not mapped.get(label)
           or set(mapped[label]) != set(location_routes.get(label, ())) for label in locations):
        return None
    if not any(origin in mapped[label] for label in locations):
        return None
    corrected = [[label, list(route)] for route_origin, label, route in relocation_routes
                 if route_origin == origin and label in locations]
    if not any(route for _label, route in corrected):
        return None
    if any(not any((route[-1] if route else origin) == endpoint
                   for route_label, route in corrected if route_label == label)
           for label in locations for endpoint in mapped[label]):
        return None
    receipt = {
        "status": "pending", "revision": 1, "policy_id": policy_id,
        "source_policy_id": source_policy_id, "mobile_vnum": mobile_vnum, "target": target.casefold(),
        "level": state["level"], "boot_id": state["world_boot_id"],
        "source_revision": state["campaign_source_revision"],
        "prior_run_id": segment["run_id"], "prior_segment_id": segment["id"],
        "prior_locator_decision": dict(decision), "corrected_origin_routes": corrected,
        "superseded_result": dict(result), "prior_abort": LOCATOR_ORIGIN_ABORT,
    }
    return receipt if existing is None or dict(existing) == receipt else None


def restore_idle_pursuit_receipts(
    state: dict[str, Any], segments: Collection[Mapping[str, Any]],
) -> dict[str, Any]:
    """Retain consumed receipts from the already-loaded segment tail."""
    existing = state.get(IDLE_PURSUIT_REVALIDATIONS_KEY)
    receipts = dict(existing) if isinstance(existing, Mapping) else {}
    for segment in segments:
        try:
            start = json.loads(segment["start_state_json"] or "{}")
        except (KeyError, TypeError, ValueError):
            continue
        if not isinstance(start, Mapping) or not segment.get("run_id"):
            continue
        saved = start.get(IDLE_PURSUIT_REVALIDATIONS_KEY)
        if not isinstance(saved, Mapping):
            continue
        policy_id = segment.get("phase")
        receipt = saved.get(policy_id)
        if (
            policy_id in receipts or not isinstance(receipt, Mapping)
            or receipt.get("policy_id") != policy_id or receipt.get("status") != "attempted"
            or receipt.get("revision") != 1 or receipt.get("maximum_pursuit_steps") != 3
            or receipt.get("prior_run_id") == segment.get("run_id")
            or not isinstance(receipt.get("prior_run_id"), int)
            or not isinstance(receipt.get("prior_segment_id"), int)
            or receipt["prior_run_id"] <= 0 or receipt["prior_segment_id"] <= 0
            or any(state.get(key) is None or state.get(key) != start.get(key)
                   or state.get(key) != receipt.get(marker_key)
                   for key, marker_key in (("level", "level"), ("world_boot_id", "boot_id"),
                                           ("campaign_source_revision", "source_revision")))
        ):
            continue
        receipts[policy_id] = dict(receipt)
    return {**state, IDLE_PURSUIT_REVALIDATIONS_KEY: receipts} if receipts else state


def idle_pursuit_revalidation_evidence(
    state: Mapping[str, Any], segment: Mapping[str, Any],
    summary: Mapping[str, Any], *, policy_id: str, mobile_vnum: int,
    target: str,
) -> dict[str, Any] | None:
    """Bind one no-combat pursuit repair to its exact completed evidence."""
    markers = state.get(IDLE_PURSUIT_REVALIDATIONS_KEY)
    if isinstance(markers, Mapping) and policy_id in markers:
        return None
    run, outcomes, progress = (summary.get(key) for key in ("run", "outcomes", "progress"))
    if not all(isinstance(value, Mapping) for value in (run, outcomes, progress)):
        return None
    experience, health = (progress.get(key) for key in ("experience", "health"))
    if not isinstance(experience, Mapping) or not isinstance(health, Mapping):
        return None
    abort = f"bounded pursuit of {target.casefold()!r} reached 1 step(s)"
    if (
        segment.get("phase") != policy_id or segment.get("status") != "success"
        or segment.get("finished_at") is None or not segment.get("run_id")
        or run.get("id") != segment.get("run_id")
        or not isinstance(segment.get("command_count"), int)
        or segment["command_count"] <= 0
        or outcomes != {"execution": "success", "objective": "not_achieved", "safety": "safe"}
        or progress.get("combat_starts") != 0 or progress.get("confirmed_kills")
        or experience.get("change") != 0
        or health.get("lowest_fraction") != 1.0
    ):
        return None
    try:
        start = json.loads(segment.get("start_state_json") or "{}")
        end = json.loads(segment.get("end_state_json") or "{}")
    except (TypeError, ValueError):
        return None
    if not isinstance(start, Mapping) or not isinstance(end, Mapping):
        return None
    for key in ("level", "world_boot_id", "campaign_source_revision", "xp", "campaign_xp_loss_total"):
        if state.get(key) is None or not state.get(key) == start.get(key) == end.get(key):
            return None
    for snapshot in (state, start, end):
        if (
            snapshot.get("room_vnum") != "3054" or snapshot.get("dead") is not False
            or snapshot.get("in_combat") is not False or snapshot.get("enemies") not in (None, [])
            or not isinstance(snapshot.get("hp"), int) or snapshot["hp"] <= 0
            or snapshot["hp"] != snapshot.get("max_hp")
        ):
            return None
    if (
        end.get("campaign_fastwalk_abort_reason") != abort
        or end.get("campaign_objective_kills") or end.get("campaign_fastwalk_route_hazards")
        or end.get("campaign_fastwalk_source_consider_outcomes")
        or end.get("campaign_fastwalk_target_vnum_mismatch")
        or end.get("campaign_fastwalk_unattackable_target")
        or end.get("campaign_fastwalk_target_present_observed") is not True
    ):
        return None
    locators = end.get("campaign_fastwalk_where_decisions")
    if not isinstance(locators, list) or not any(
        isinstance(locator, Mapping) and locator.get("source_mobile_vnum") == mobile_vnum
        and locator.get("target") == target.casefold() and locator.get("mapped_rooms")
        for locator in locators
    ):
        return None
    results = state.get("campaign_research_results")
    result = results.get(policy_id) if isinstance(results, Mapping) else None
    if (
        not isinstance(result, Mapping) or result.get("route_hazard") != abort
        or result.get("boot_id") != state.get("world_boot_id")
        or result.get("fatal_failure") or result.get("completed_kill")
    ):
        return None
    return {
        "status": "attempted", "revision": 1, "policy_id": policy_id,
        "mobile_vnum": mobile_vnum, "target": target.casefold(),
        "level": state["level"], "boot_id": state["world_boot_id"],
        "source_revision": state["campaign_source_revision"],
        "prior_run_id": segment["run_id"], "prior_segment_id": segment["id"],
        "prior_abort": abort, "maximum_pursuit_steps": 3,
    }


def isolated_health_floor_target(
    state: Mapping[str, Any],
    segment: Mapping[str, Any],
    summary: Mapping[str, Any],
    *,
    policy_id: str,
    source_policy_ids: Collection[str],
    allow_exact_registered_loss: bool = False,
    audited_source_revision: str | None = None,
) -> str | None:
    """Scope one registered route's health withdrawal to its observed target.

    The caller still validates each alternative's source route and live gates.
    This identifies the failed target without clearing its route's old result.
    """
    run = summary.get("run")
    outcomes = summary.get("outcomes")
    evidence = summary.get("evidence")
    if not all(isinstance(value, Mapping) for value in (run, outcomes, evidence)):
        return None
    if (
        segment.get("phase") != policy_id
        or segment.get("status") != "success"
        or segment.get("finished_at") is None
        or segment.get("run_id") is None
        or run.get("id") != segment.get("run_id")
        or outcomes.get("execution") != "success"
        or outcomes.get("objective") != "not_achieved"
        or outcomes.get("safety") not in {"safe", "loss"}
    ):
        return None
    counts = evidence.get("game_event_counts")
    if not isinstance(counts, Mapping) or counts.get("character_died", 0):
        return None
    try:
        start = json.loads(segment.get("start_state_json") or "{}")
        end = json.loads(segment.get("end_state_json") or "{}")
    except (TypeError, ValueError):
        return None
    if not isinstance(start, Mapping) or not isinstance(end, Mapping):
        return None
    for key in ("level", "world_boot_id"):
        if state.get(key) is None or not state.get(key) == start.get(key) == end.get(key):
            return None
    recorded_revision = start.get("campaign_source_revision")
    current_revision = state.get("campaign_source_revision")
    if (
        not recorded_revision
        or not current_revision
        or recorded_revision != end.get("campaign_source_revision")
        or (
            current_revision != recorded_revision
            and audited_source_revision != current_revision
        )
    ):
        return None
    if (
        str(start.get("room_vnum")) != "3054"
        or str(end.get("room_vnum")) != "3054"
        or start.get("dead") is not False
        or end.get("dead") is not False
        or end.get("in_combat") is not False
        or end.get("campaign_objective_kills")
        or end.get("campaign_fastwalk_route_hazards")
        or end.get("campaign_fastwalk_crowded")
        or end.get("campaign_fastwalk_target_vnum_mismatch")
        or end.get("campaign_fastwalk_unattackable_target")
        or state.get("campaign_xp_loss_total") != end.get("campaign_xp_loss_total")
        or not re.match(
            r"^field combat aborted for safety: health at or below \d+%",
            str(end.get("campaign_fastwalk_abort_reason") or ""),
        )
    ):
        return None
    losses = [
        record
        for record in state.get("campaign_registered_research_xp_loss_policies") or ()
        if isinstance(record, Mapping)
        and record.get("boot_id") == state.get("world_boot_id")
        and record.get("policy_id") == policy_id
    ]
    if bool(losses) != (outcomes.get("safety") == "loss"):
        return None
    exact_registered_loss = False
    if losses:
        try:
            loss_count = int(losses[0].get("loss_count") or 0)
        except (AttributeError, TypeError, ValueError):
            loss_count = 0
        exact_registered_loss = bool(
            len(losses) == 1
            and loss_count >= 1
            and losses[0].get("loss_event_id") == segment.get("id")
            and (
                not allow_exact_registered_loss
                or losses[0].get("level") == state.get("level")
            )
        )
        if not exact_registered_loss or (loss_count != 1 and not allow_exact_registered_loss):
            return None
    if allow_exact_registered_loss and not exact_registered_loss:
        return None

    if allow_exact_registered_loss and exact_registered_loss:
        # Multi-target registered routes record the completed run-level result
        # separately from the exact target loss. Scope only the linked terminal
        # health-floor loss, even if a later sibling result updated the parent.
        terminal_results = end.get("campaign_research_results")
        result = (
            terminal_results.get(policy_id)
            if isinstance(terminal_results, Mapping)
            else None
        )
        counts = evidence.get("game_event_counts")
        try:
            loss_delta = int(end.get("campaign_xp_loss_total")) - int(
                start.get("campaign_xp_loss_total")
            )
        except (TypeError, ValueError):
            loss_delta = 0
        if (
            not isinstance(result, Mapping)
            or result.get("boot_id") != state.get("world_boot_id")
            or result.get("completed_kill") is not False
            or result.get("fatal_failure") is True
            or result.get("viable") is not False
            or not isinstance(counts, Mapping)
            or not counts.get("experience_lost")
            or loss_delta <= 0
        ):
            return None
    else:
        results = state.get("campaign_research_results")
        result = results.get(policy_id) if isinstance(results, Mapping) else None
        if result is None:
            # Legacy cooldown expiry could remove this result while retaining
            # its exact loss ledger. Reuse only the linked terminal record.
            terminal_results = end.get("campaign_research_results")
            if outcomes.get("safety") != "loss" or not isinstance(terminal_results, Mapping):
                return None
            result = terminal_results.get(policy_id)
        if (
            not isinstance(result, Mapping)
            or result.get("boot_id") != state.get("world_boot_id")
            or result.get("completed_kill") is True
            or result.get("fatal_failure") is True
            or result.get("retryable_failure") is not True
        ):
            return None
    outcomes = end.get("campaign_fastwalk_source_consider_outcomes")
    if not isinstance(outcomes, Mapping) or len(outcomes) != 1:
        return None
    target_id, viable = next(iter(outcomes.items()))
    if target_id not in source_policy_ids or viable is not True:
        return None
    sightings = end.get("campaign_fastwalk_source_present_sightings")
    if not isinstance(sightings, (list, tuple)) or not sightings:
        return None
    if any(
        not isinstance(sighting, Mapping) or sighting.get("policy_id") != target_id
        for sighting in sightings
    ):
        return None
    return str(target_id)
