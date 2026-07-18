from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any

from .storage import RunStorage


_CREATURE_LINE = re.compile(
    r"^A(?:n)? (?P<target>[A-Za-z][A-Za-z' -]{1,50}?) "
    r"(?:makes|grunts|growls|hisses|snarls|barks|paces|stands|waits|circles)\b",
    re.IGNORECASE | re.MULTILINE,
)
_ANSI_ESCAPE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def collect_run_evidence(storage: RunStorage, run_id: int) -> dict[str, Any]:
    """Create a compact, credential-free observation record for one stored run."""
    run = storage.get_run(run_id)
    if run is None:
        raise LookupError(f"No run with id {run_id}")

    rooms: dict[tuple[str | None, str | None], dict[str, Any]] = {}
    game_event_counts: Counter[str] = Counter()
    observed_targets: list[str] = []
    latest_progress: dict[str, Any] = {}
    lowest_health: dict[str, int | float] | None = None

    for event in storage.list_events(run_id):
        payload = json.loads(event["payload_json"])
        if event["kind"] == "response":
            observed_targets.extend(_targets_from_text(str(payload.get("text", ""))))
            continue
        if event["kind"] != "game_event":
            continue

        event_type = str(payload.get("type", "unknown"))
        game_event_counts[event_type] += 1
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        if event_type in {"room_entered", "room_updated"}:
            room = _room_summary(data)
            if room["name"] or room["vnum"]:
                _record_room(rooms, room)
        elif event_type == "progress_changed":
            latest_progress = {
                key: data[key]
                for key in ("level", "xp", "xptnl", "maxxp", "practice")
                if key in data
            }
        elif event_type == "health_changed":
            current = _number(data.get("current"))
            maximum = _number(data.get("maximum"))
            if current is not None and (
                lowest_health is None or current < lowest_health["current"]
            ):
                lowest_health = {"current": current}
                if maximum is not None:
                    lowest_health["maximum"] = maximum
        elif event_type == "combat_started":
            target = data.get("target", data.get("name"))
            if target:
                observed_targets.append(str(target))

    return {
        "schema_version": 1,
        "run": {
            "id": run["id"],
            "scenario_name": run["scenario_name"],
            "status": run["status"],
            "started_at": run["started_at"],
            "finished_at": run["finished_at"],
        },
        "observations": {
            "rooms": list(rooms.values()),
            "latest_progress": latest_progress,
            "lowest_health": lowest_health,
            "observed_targets": _unique(observed_targets),
            "game_event_counts": dict(sorted(game_event_counts.items())),
        },
        "limitations": [
            "Commands, credentials, and raw response text are intentionally omitted.",
            "Observed rooms and targets are leads until a bounded policy run validates them.",
        ],
    }


def render_evidence_json(evidence: dict[str, Any]) -> str:
    return json.dumps(evidence, indent=2, sort_keys=True) + "\n"


def _room_summary(data: dict[str, Any]) -> dict[str, Any]:
    exits = data.get("exits")
    if isinstance(exits, dict):
        exits = sorted(str(direction) for direction in exits)
    elif isinstance(exits, list):
        exits = [str(direction) for direction in exits]
    else:
        exits = []
    return {
        "name": _text(data.get("name")),
        "vnum": _text(data.get("vnum")),
        "area": _text(data.get("area")),
        "exits": exits,
        "flags": _text(data.get("flags")),
    }


def _record_room(
    rooms: dict[tuple[str | None, str | None], dict[str, Any]],
    room: dict[str, Any],
) -> None:
    name = room["name"]
    vnum = room["vnum"]
    if vnum is None and name is not None:
        has_enriched_room = any(
            existing_name == name and existing_vnum is not None
            for existing_vnum, existing_name in rooms
        )
        if has_enriched_room:
            return
    if vnum is not None and name is not None:
        rooms.pop((None, name), None)
    rooms[(vnum, name)] = room


def _targets_from_text(text: str) -> list[str]:
    text = _ANSI_ESCAPE.sub("", text).replace("\r", "")
    return [
        " ".join(match.group("target").casefold().split())
        for match in _CREATURE_LINE.finditer(text)
    ]


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _number(value: Any) -> int | float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    if isinstance(value, str):
        try:
            number = float(value)
        except ValueError:
            return None
        return int(number) if number.is_integer() else number
    return None


def _text(value: Any) -> str | None:
    return str(value) if value is not None else None
