"""Attribute an explicit combat loss to its exact source stop, not its route."""

from __future__ import annotations

import json
import re
from pathlib import Path
from collections.abc import Mapping, Sequence
from typing import Any


SOURCE_COMBAT_LOSSES_KEY = "campaign_source_combat_losses"
_POLICY_ID = re.compile(
    r"^source-ranked-hunt-.+-(\d+)-(\d+)-(\d+)"
    r"(?:-recall-\d+)?(?:-sanctuary-maintenance)?$"
)


def source_stop_policy_id(
    area_file: str, mobile_vnum: int, room_vnum: int, character_level: int,
    recall_index: int = 0,
) -> str:
    area = re.sub(r"[^a-z0-9]+", "-", Path(area_file).stem.casefold()).strip("-") or "area"
    suffix = f"-recall-{recall_index}" if recall_index else ""
    return f"source-ranked-hunt-{area}-{mobile_vnum}-{room_vnum}-{character_level}{suffix}"


def source_stop_identity(policy_id: str) -> tuple[int, int, int] | None:
    match = _POLICY_ID.fullmatch(policy_id)
    return tuple(map(int, match.groups())) if match else None


def source_combat_loss_records(state: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    raw_records: list[Any] = []
    for key in (SOURCE_COMBAT_LOSSES_KEY, "source_combat_losses"):
        raw = state.get(key)
        if isinstance(raw, Mapping):
            raw_records.append(raw)
        elif isinstance(raw, (list, tuple)):
            raw_records.extend(raw[: max(0, 16 - len(raw_records))])
    records = {}
    for record in raw_records[:16]:
        if not isinstance(record, Mapping):
            continue
        policy_id = str(record.get("policy_id") or "")
        identity = source_stop_identity(policy_id)
        if identity is None or any(type(record.get(key)) is not int for key in (
            "mobile_vnum", "room_vnum", "level", "xp_lost",
        )):
            continue
        if (
            identity != (
                record["mobile_vnum"], record["room_vnum"], record["level"],
            )
            or record["level"] != state.get("level") or record["xp_lost"] <= 0
            or not str(record.get("target") or "").strip()
        ):
            continue
        records[policy_id] = dict(record)
    return records


def recover_source_combat_losses(
    start: Mapping[str, Any], end: Mapping[str, Any],
    contexts: Sequence[tuple[Mapping[str, Any], Sequence[Mapping[str, Any]]]],
) -> list[dict[str, Any]]:
    """Recover negative evidence from bounded ordered events of a linked run."""
    if (
        not start.get("world_boot_id")
        or start.get("world_boot_id") != end.get("world_boot_id")
        or type(start.get("level")) is not int or start.get("level") != end.get("level")
        or not start.get("campaign_source_revision")
        or start.get("campaign_source_revision") != end.get("campaign_source_revision")
        or end.get("xp_loss_observed") is not True
    ):
        return []
    candidate = start.get("campaign_source_ranked_hunt_candidate")
    circuit = (candidate.get("circuit") or ()) if isinstance(candidate, Mapping) else ()
    if not isinstance(circuit, (list, tuple)) or len(circuit) > 16:
        return []
    candidates = [candidate, *circuit] if isinstance(candidate, Mapping) else []
    sightings = end.get("campaign_fastwalk_source_present_sightings")
    if isinstance(sightings, (list, tuple)) and len(sightings) <= 16:
        for sighting in sightings:
            if not isinstance(sighting, Mapping):
                continue
            policy_id = str(sighting.get("policy_id") or "")
            identity = source_stop_identity(policy_id)
            if (
                identity is not None and identity[2] == start["level"]
                and str(identity[1]) == str(sighting.get("room_vnum"))
                and not any(isinstance(item, Mapping) and item.get("policy_id") == policy_id
                            for item in candidates)
            ):
                candidates.append({
                    "policy_id": policy_id, "mobile_vnum": identity[0],
                    "room_vnum": identity[1],
                })
    recovered = []
    for loss_row, context in contexts[:4]:
        try:
            loss = json.loads(loss_row["payload_json"])
        except (KeyError, TypeError, ValueError):
            continue
        data = loss.get("data")
        if (
            loss_row.get("kind") != "game_event" or loss.get("type") != "experience_lost"
            or not isinstance(data, Mapping) or type(data.get("xp")) is not int or data["xp"] <= 0
        ):
            continue
        enemies = []
        room = None
        withdrawal = None
        for row in context[-128:]:
            try:
                payload = json.loads(row["payload_json"])
            except (KeyError, TypeError, ValueError):
                continue
            if row.get("kind") == "decision":
                if payload.get("command") in {"flee", "recall"}:
                    withdrawal = (list(enemies), room, str(payload.get("reason") or ""))
                elif payload.get("command") not in {"look", "score"}:
                    withdrawal = None
            if row.get("kind") != "game_event":
                continue
            event_data = payload.get("data")
            if not isinstance(event_data, Mapping):
                continue
            if payload.get("type") == "enemies_changed":
                value = event_data.get("value")
                if isinstance(value, list):
                    enemies = [enemy for group in value
                               for enemy in (group if isinstance(group, list) else [group])
                               if isinstance(enemy, Mapping)]
            elif payload.get("type") in {"room_entered", "room_updated"}:
                room = event_data.get("vnum")
                arrival = event_data.get("arrival")
                if withdrawal and withdrawal[1] is None and isinstance(arrival, Mapping):
                    withdrawal = (withdrawal[0], arrival.get("from"), withdrawal[2])
        if withdrawal is None or len(withdrawal[0]) != 1:
            continue
        enemy = withdrawal[0][0]
        try:
            mobile_vnum = int(enemy.get("isnpc"))
            room_vnum = int(withdrawal[1])
        except (TypeError, ValueError):
            continue
        matches = [item for item in candidates if isinstance(item, Mapping)
                   and item.get("mobile_vnum") == mobile_vnum
                   and item.get("room_vnum") == room_vnum]
        if len(matches) != 1:
            continue
        record = {
            "policy_id": matches[0].get("policy_id"), "mobile_vnum": mobile_vnum,
            "room_vnum": room_vnum, "live_room_vnum": room_vnum, "level": start["level"],
            "target": enemy.get("name"), "xp_lost": data["xp"],
            "partial_xp": data.get("partial_xp", 0), "reason": withdrawal[2],
            "run_id": loss_row.get("run_id"), "event_id": loss_row.get("id"),
            "evidence_source": "ordered_run_events",
        }
        if source_combat_loss_records({"level": start["level"], "source_combat_losses": [record]}):
            recovered.append(record)
    return recovered
