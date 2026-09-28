from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .campaign import (
    DEFAULT_LIVE_SEGMENT_RUNTIME_SECONDS,
    CampaignResult,
    run_campaign_file,
)
from .scenario import load_yaml_mapping


@dataclass(frozen=True)
class CampaignRotationEntry:
    entry_id: str
    campaign_path: Path


@dataclass(frozen=True)
class CampaignRotationSpec:
    name: str
    target_level: int
    inter_character_delay: float
    entries: tuple[CampaignRotationEntry, ...]


@dataclass(frozen=True)
class CampaignRotationAttempt:
    entry_id: str
    cycle: int
    campaign_path: Path
    result: CampaignResult | None
    error: str | None = None


@dataclass(frozen=True)
class CampaignRotationResult:
    spec: CampaignRotationSpec
    attempts: tuple[CampaignRotationAttempt, ...]
    completed_entry_ids: tuple[str, ...]
    deferred_entry_reasons: dict[str, str]


def load_campaign_rotation(path: str | Path) -> CampaignRotationSpec:
    config_path = Path(path).resolve()
    mapping = load_yaml_mapping(config_path)
    raw_entries = mapping.get("entries")
    if not isinstance(raw_entries, list) or not raw_entries:
        raise ValueError("campaign rotation entries must be a non-empty list")

    target_level = _integer(mapping.get("target_level", 100), "target_level")
    if not 1 <= target_level <= 100:
        raise ValueError("campaign rotation target_level must be between 1 and 100")
    delay = _number(mapping.get("inter_character_delay", 0), "inter_character_delay")
    if delay < 0:
        raise ValueError("inter_character_delay cannot be negative")

    entries: list[CampaignRotationEntry] = []
    seen_ids: set[str] = set()
    for index, raw_entry in enumerate(raw_entries, start=1):
        if not isinstance(raw_entry, dict):
            raise ValueError(f"campaign rotation entry {index} must be a mapping")
        entry_id = str(raw_entry.get("id") or "").strip()
        raw_campaign = raw_entry.get("campaign")
        if not entry_id or not isinstance(raw_campaign, str) or not raw_campaign.strip():
            raise ValueError(
                f"campaign rotation entry {index} needs id and campaign"
            )
        normalized_id = entry_id.casefold()
        if normalized_id in seen_ids:
            raise ValueError(f"duplicate campaign rotation id: {entry_id}")
        seen_ids.add(normalized_id)
        campaign_path = (config_path.parent / raw_campaign).resolve()
        if not campaign_path.is_file():
            raise ValueError(
                f"campaign rotation entry {entry_id!r} does not exist: "
                f"{campaign_path}"
            )
        entries.append(CampaignRotationEntry(entry_id, campaign_path))

    return CampaignRotationSpec(
        name=str(mapping.get("name") or config_path.stem),
        target_level=target_level,
        inter_character_delay=delay,
        entries=tuple(entries),
    )


async def run_campaign_rotation(
    path: str | Path,
    *,
    rounds: int = 1,
    max_segment_runtime: float = DEFAULT_LIVE_SEGMENT_RUNTIME_SECONDS,
    progress_callback: Callable[[str], None] | None = None,
) -> CampaignRotationResult:
    """Give each configured campaign one bounded turn per round.

    A blocked or failed character is deferred for the rest of this invocation;
    the next configured character still gets its turn.
    """
    if rounds < 1:
        raise ValueError("rounds must be positive")
    if rounds > 1000:
        raise ValueError("rounds cannot exceed 1000")
    if not math.isfinite(max_segment_runtime) or max_segment_runtime <= 0:
        raise ValueError("max_segment_runtime must be positive")

    spec = load_campaign_rotation(path)
    attempts: list[CampaignRotationAttempt] = []
    completed: set[str] = set()
    deferred: dict[str, str] = {}

    for cycle in range(1, rounds + 1):
        cycle_had_work = False
        for entry_index, entry in enumerate(spec.entries):
            if entry.entry_id in completed or entry.entry_id in deferred:
                continue
            if progress_callback is not None:
                progress_callback(
                    f"Rotation {cycle}/{rounds}: running {entry.entry_id} "
                    "for one bounded campaign segment."
                )
            cycle_had_work = True
            try:
                result = await run_campaign_file(
                    entry.campaign_path,
                    segments=1,
                    reset_retries=0,
                    max_segment_runtime=max_segment_runtime,
                    progress_callback=progress_callback,
                )
            except Exception as exc:
                message = f"{type(exc).__name__}: {exc}"
                attempts.append(
                    CampaignRotationAttempt(
                        entry.entry_id,
                        cycle,
                        entry.campaign_path,
                        None,
                        message,
                    )
                )
                deferred[entry.entry_id] = message
                if progress_callback is not None:
                    progress_callback(
                        f"Rotation deferred {entry.entry_id}: {message}"
                    )
            else:
                attempts.append(
                    CampaignRotationAttempt(
                        entry.entry_id,
                        cycle,
                        entry.campaign_path,
                        result,
                    )
                )
                level = _result_level(result)
                if result.status == "success" or level >= spec.target_level:
                    completed.add(entry.entry_id)
                elif (
                    result.status != "ready"
                    or not result.ready_for_next_segment
                ):
                    deferred[entry.entry_id] = result.message or result.status
                if progress_callback is not None:
                    progress_callback(
                        f"Rotation result {entry.entry_id}: "
                        f"status={result.status}; level={level}."
                    )

            has_later_work = any(
                later.entry_id not in completed
                and later.entry_id not in deferred
                for later in spec.entries[entry_index + 1 :]
            )
            if spec.inter_character_delay > 0 and has_later_work:
                await asyncio.sleep(spec.inter_character_delay)

        if not cycle_had_work or len(completed) + len(deferred) == len(spec.entries):
            break

    return CampaignRotationResult(
        spec=spec,
        attempts=tuple(attempts),
        completed_entry_ids=tuple(
            entry.entry_id for entry in spec.entries if entry.entry_id in completed
        ),
        deferred_entry_reasons=deferred,
    )


def _result_level(result: CampaignResult) -> int:
    try:
        return int(result.state.get("level", 0) or 0)
    except (TypeError, ValueError):
        return 0


def _integer(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"campaign rotation {field} must be an integer")
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"campaign rotation {field} must be an integer") from exc
    if isinstance(value, float) and not value.is_integer():
        raise ValueError(f"campaign rotation {field} must be an integer")
    return result


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"campaign rotation {field} must be a number")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"campaign rotation {field} must be a number") from exc
    if not math.isfinite(result):
        raise ValueError(f"campaign rotation {field} must be finite")
    return result
