"""Time-bounded field observations, separate from durable combat failures."""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Collection, Mapping


_LOCATOR_NONCOMBAT_VERBS = frozenset({
    "north", "south", "east", "west", "up", "down", "n", "s", "e", "w", "u", "d",
    "look", "where", "eq", "equipment", "inventory", "time", "score", "practice",
    "config", "sneak", "fill", "drink", "eat", "get", "put", "wear", "remove", "recall", "sleep",
    "rest", "stand", "wake", "save", "quit", "vis", "affect", "affects",
})
_LOCATOR_NONCOMBAT_EVENTS = frozenset({
    "prompt_seen", "vitals_changed", "room_entered", "room_updated", "affects_changed",
    "progress_changed", "posture_changed", "character_identity_observed", "health_changed",
    "stats_changed", "inventory_changed", "equipment_changed", "quest_status_changed",
    "recall_points_changed",
})
_LOCATOR_NONCOMBAT_COMMANDS = frozenset({"cast invis"})


def single_area_locator_miss(
    segment: Mapping[str, Any],
    events: Collection[Mapping[str, Any]],
    *,
    boot_id: str,
    level: int,
    keyword: str,
    reset_room: int,
) -> dict[str, Any] | None:
    """Prove a completed, noncombat, one-area miss from bounded run evidence."""
    try:
        command_count = segment["command_count"]
    except (KeyError, IndexError, TypeError):
        return None
    if (
        not events
        or isinstance(command_count, bool)
        or not isinstance(command_count, int)
        or not 1 <= command_count <= 128
        or len(events) > min(2048, max(512, command_count * 16))
        or segment["status"] != "success"
    ):
        return None
    try:
        start = json.loads(segment["start_state_json"] or "{}")
        end = json.loads(segment["end_state_json"] or "{}")
        if not isinstance(start, dict) or not isinstance(end, dict):
            return None
        if not (
            start.get("world_boot_id") == end.get("world_boot_id") == boot_id
            and start.get("level") == end.get("level") == level
            and isinstance(start.get("xp"), (int, float))
            and not isinstance(start["xp"], bool) and math.isfinite(start["xp"])
            and start["xp"] == end.get("xp")
            and isinstance(start.get("hp"), (int, float)) and start["hp"] > 0
            and not isinstance(start["hp"], bool) and math.isfinite(start["hp"])
            and str(end.get("room_vnum")) == "3054"
            and not end.get("enemy") and not end.get("in_combat")
            and not end.get("dead") and not end.get("campaign_died_during_segment")
            and not end.get("campaign_fastwalk_consider_outcomes")
            and not end.get("campaign_fastwalk_source_consider_outcomes")
            and str(end.get("campaign_fastwalk_abort_reason") or "").startswith("`where` ")
            and str(end.get("campaign_fastwalk_abort_reason") or "").endswith("in the current area")
        ):
            return None
        commands: list[str] = []
        decisions: list[str] = []
        query_rooms: list[str] = []
        negative_observed = False
        room: str | None = None
        for row in events:
            payload = json.loads(row["payload_json"])
            if not isinstance(payload, dict):
                return None
            if row["kind"] == "command":
                commands.append(str(payload.get("command", "")))
            elif row["kind"] == "response" and query_rooms:
                negative_observed = negative_observed or (
                    "you fail to find anyone by that name" in str(payload.get("text") or "").casefold()
                )
            elif row["kind"] == "decision":
                command = str(payload.get("command", ""))
                decisions.append(command)
                if payload.get("category") != "authentication":
                    normalized_command = command.strip().casefold()
                    verb = normalized_command.split(" ", 1)[0]
                    if (
                        verb not in _LOCATOR_NONCOMBAT_VERBS
                        and normalized_command not in _LOCATOR_NONCOMBAT_COMMANDS
                    ):
                        return None
                    if normalized_command == f"where {keyword.casefold()}":
                        query_rooms.append(str(room or ""))
            elif row["kind"] == "game_event":
                data = payload.get("data") or {}
                if not isinstance(data, dict):
                    return None
                deferred_training = (
                    payload.get("type") == "training_deferred"
                    and data.get("preflight") is True
                    and data.get("outcome") == "deferred"
                    and "trainer route hazard"
                    in str(data.get("reason") or "").casefold()
                )
                if (
                    payload.get("type") not in _LOCATOR_NONCOMBAT_EVENTS
                    and not deferred_training
                ):
                    return None
                if data.get("package") == "Room.Info" and data.get("vnum") is not None:
                    room = str(data["vnum"])
                if payload.get("type") == "health_changed" and (
                    float(data["current"]) < start["hp"]
                ):
                    return None
                if data.get("package") == "Char.Vitals" and "hp" in data and float(data["hp"]) < start["hp"]:
                    return None
                if payload.get("type") == "progress_changed" and "xp" in data:
                    if int(data["xp"]) != start["xp"]:
                        return None
        if not (
            0 < len(commands) == segment["command_count"] <= 128
            and commands == decisions and query_rooms == [str(reset_room)] and negative_observed
        ):
            return None
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    return {
        "boot_id": boot_id, "level": level, "segment_id": segment["id"],
        "run_id": segment["run_id"], "query_room_vnum": str(reset_room),
        "observed_at": segment["finished_at"], "command_count": len(commands),
    }


def expired_room_crowds(
    segments: Collection[Mapping[str, Any]],
    *,
    boot_id: str,
    level: int,
    now: datetime | None = None,
) -> dict[str, dict[str, Any]]:
    """Offer reinspection after 5/10/20/30 minutes, never combat permission.

    Derive both the clock and backoff from completed segments so reconnects,
    checkpoint repair, and unexecuted plans cannot renew or spend the wait.
    """
    now = now or datetime.now(timezone.utc)
    latest: dict[str, tuple[Mapping[str, Any], bool]] = {}
    counts: dict[str, int] = {}
    for segment in sorted(segments, key=lambda row: int(row["sequence"] or 0)):
        policy_id = str(segment["phase"] or "")
        if not policy_id.startswith("source-ranked-hunt-"):
            continue
        latest[policy_id] = (segment, False)
        try:
            start = json.loads(segment["start_state_json"] or "{}")
            end = json.loads(segment["end_state_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            continue
        if not isinstance(start, dict) or not isinstance(end, dict):
            continue
        if end.get("world_boot_id") != boot_id:
            continue
        sightings = end.get("campaign_fastwalk_source_present_sightings")
        if not isinstance(sightings, (list, tuple)):
            sightings = ()
        # Require a concrete pre-combat observation, not a generic crowd or
        # assistance marker that could hide an actual losing exchange.
        plain_crowd = bool(
            segment["status"] in {"success", "ready"}
            and start.get("world_boot_id") == boot_id
            and start.get("level") == end.get("level") == level
            and isinstance(start.get("xp"), (int, float))
            and start["xp"] == end.get("xp")
            and str(end.get("room_vnum")) == "3054"
            and not end.get("enemy")
            and str(end.get("campaign_fastwalk_abort_reason") or "").startswith(
                "field room contained "
            )
            and not end.get("campaign_fastwalk_consider_outcomes")
            and not end.get("campaign_fastwalk_source_consider_outcomes")
            and any(
                isinstance(sighting, dict)
                and sighting.get("policy_id") == policy_id
                for sighting in sightings
            )
        )
        latest[policy_id] = (segment, plain_crowd)
        if plain_crowd:
            counts[policy_id] = counts.get(policy_id, 0) + 1

    expired: dict[str, dict[str, Any]] = {}
    for policy_id, (segment, plain_crowd) in latest.items():
        if not plain_crowd:
            continue
        try:
            observed_at = datetime.fromisoformat(str(segment["finished_at"]))
        except (TypeError, ValueError):
            continue
        if observed_at.tzinfo is None or now.tzinfo is None:
            continue
        delay = min(1800, 300 * 2 ** min(3, counts[policy_id] - 1))
        recheck_after = observed_at + timedelta(seconds=delay)
        if now < recheck_after:
            continue
        expired[policy_id] = {
            "boot_id": boot_id,
            "segment_id": segment["id"],
            "run_id": segment["run_id"],
            "observed_at": observed_at.isoformat(),
            "recheck_after": recheck_after.isoformat(),
            "delay_seconds": delay,
            "observation_count": counts[policy_id],
        }
    return expired
