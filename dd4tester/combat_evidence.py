from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping


_MAX_TRANSCRIPT_BYTES = 4 * 1024 * 1024
_MAX_TRANSCRIPT_LINES = 100_000
_ITEM_ACTIVATION = re.compile(r"^(?:quaff|brandish|recite|use)\b", re.IGNORECASE)


def verified_unprotected_single_kill_run(
    run: Mapping[str, Any],
    summary: Mapping[str, Any],
    transcript_path: Path,
    *,
    character_name: str,
    character_level: int,
    character_class: str,
    character_race: str,
    character_subclass: str | None,
    world_boot_id: str,
    source_mobile_vnum: int,
    source_policy_id: str,
    minimum_health_fraction: float = 0.20,
) -> dict[str, Any] | None:
    """Return a compact receipt only for an exact, safe, unprotected solo kill."""
    run_id = _positive_int(run.get("id"))
    if (
        run_id is None
        or run.get("boot_id") != world_boot_id
        or not _same(run.get("status"), "success")
        or not _same(run.get("execution_status"), "success")
        or not _same(run.get("objective_outcome"), "achieved")
        or not _same(run.get("safety_outcome"), "safe")
    ):
        return None

    outcomes = summary.get("outcomes")
    character = summary.get("character")
    progress = summary.get("progress")
    objective = summary.get("objective")
    if not all(
        isinstance(value, Mapping)
        for value in (outcomes, character, progress, objective)
    ):
        return None
    if (
        outcomes.get("execution") != "success"
        or outcomes.get("objective") != "achieved"
        or outcomes.get("safety") != "safe"
        or not _same(character.get("name"), character_name)
        or not _same(character.get("class"), character_class)
        or not _same(character.get("race"), character_race)
        or not _same(character.get("subclass"), character_subclass or "")
        or objective.get("fastwalk_kill_limit") != 1
    ):
        return None
    stops = objective.get("fastwalk_hunt_stop_boundaries")
    if not isinstance(stops, list) or len(stops) != 1:
        return None

    level = progress.get("level")
    health = progress.get("health")
    kills = progress.get("confirmed_kills")
    if not all(isinstance(value, Mapping) for value in (level, health)):
        return None
    if (
        level.get("initial") != character_level
        or level.get("final") != character_level
        or not isinstance(kills, list)
        or len(kills) != 1
    ):
        return None
    kill = kills[0]
    if not isinstance(kill, Mapping):
        return None
    xp_gained = _positive_int(kill.get("xp_gained"))
    health_floor = _number(health.get("lowest_fraction"))
    if (
        kill.get("source_mobile_vnum") != source_mobile_vnum
        or kill.get("source_policy_id") != source_policy_id
        or xp_gained is None
        or health_floor is None
        or health_floor < minimum_health_fraction
    ):
        return None

    observed_target_max_hp = _transcript_observations(
        transcript_path,
        run_id=run_id,
        source_mobile_vnum=source_mobile_vnum,
    )
    if observed_target_max_hp is None:
        return None
    return {
        "run_id": run_id,
        "xp_gained": xp_gained,
        "lowest_health_fraction": health_floor,
        "observed_target_max_hp": observed_target_max_hp,
        "source_policy_id": source_policy_id,
        "source_mobile_vnum": source_mobile_vnum,
        "world_boot_id": world_boot_id,
    }


def _transcript_observations(
    transcript_path: Path,
    *,
    run_id: int,
    source_mobile_vnum: int,
) -> int | None:
    try:
        if transcript_path.stat().st_size > _MAX_TRANSCRIPT_BYTES:
            return None
        stream = transcript_path.open(encoding="utf-8")
    except (OSError, UnicodeError):
        return None

    saw_affect_observation = False
    target_max_hp: int | None = None
    try:
        with stream:
            for line_number, line in enumerate(stream, start=1):
                if line_number > _MAX_TRANSCRIPT_LINES:
                    return None
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    return None
                if (
                    not isinstance(event, dict)
                    or event.get("run_id") != run_id
                    or not isinstance(event.get("payload"), dict)
                ):
                    return None
                payload = event["payload"]
                serialized = json.dumps(payload, ensure_ascii=False).casefold()
                if "sanctuary" in serialized:
                    return None
                if event.get("kind") == "gmcp" and "char.affect" in serialized:
                    saw_affect_observation = True
                if event.get("kind") == "gmcp":
                    message = payload.get("message")
                    if isinstance(message, str) and message.startswith("Char.Enemies "):
                        try:
                            enemies = json.loads(message[len("Char.Enemies "):])
                        except json.JSONDecodeError:
                            return None
                        for enemy in _flatten_records(enemies):
                            if _positive_int(enemy.get("isnpc")) != source_mobile_vnum:
                                continue
                            max_hp = _positive_int(enemy.get("maxhp"))
                            if max_hp is not None:
                                target_max_hp = max(target_max_hp or 0, max_hp)
                if event.get("kind") == "command":
                    command = str(payload.get("command") or "").strip()
                    if _ITEM_ACTIVATION.match(command):
                        return None
    except (OSError, UnicodeError):
        return None
    if not saw_affect_observation or target_max_hp is None:
        return None
    return target_max_hp


def _flatten_records(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, list):
        return [record for item in value for record in _flatten_records(item)]
    return []


def _same(left: Any, right: Any) -> bool:
    return str(left or "").strip().casefold() == str(right or "").strip().casefold()


def _positive_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
