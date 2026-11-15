from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import json
import math
from typing import Any

from .hunt_outcomes import completed_single_target_hunt
from .storage import RUN_REPORT_SUMMARY_VERSION


def load_bounded_hunt_visits(
    storage: Any, campaign_id: int, phase: str,
    recent_segments: Iterable[Mapping[str, Any]],
    latest: Mapping[str, Any] | None = None,
) -> list[tuple[Mapping[str, Any], Mapping[str, Any]]]:
    """Link at most eight visits from 256 thin headers, not full history."""
    known = {row["id"]: dict(row) for row in recent_segments if row["phase"] == phase}
    if latest is not None:
        known[latest["id"]] = dict(latest)
    headers = getattr(storage, "list_recent_campaign_segment_headers", None)
    load = getattr(storage, "get_campaign_segment_by_id", None)
    if callable(headers) and callable(load):
        selected = [dict(row) for row in headers(campaign_id, limit=256)
                    if row["phase"] == phase]
    else:
        selected = list(known.values())
    selected.sort(key=lambda row: row["id"], reverse=True)
    visits = []
    for header in selected[:8]:
        row = known.get(header["id"])
        if row is None:
            loaded = load(campaign_id, header["id"])
            row = dict(loaded) if loaded is not None else None
        if (row is None or row.get("id") != header["id"]
                or row.get("phase") != phase or row.get("run_id") != header.get("run_id")):
            return []
        run_id = row.get("run_id")
        if type(run_id) is not int or run_id <= 0:
            continue
        summary = storage.get_run_summary(run_id)
        if not isinstance(summary, Mapping):
            return []
        visits.append((row, summary))
    return visits


@dataclass(frozen=True)
class HuntVisitEfficiency:
    net_xp: int
    duration_seconds: float
    run_ids: tuple[int, ...]
    productive_visits: int

    @property
    def xp_per_minute(self) -> float:
        return self.net_xp * 60 / self.duration_seconds


def observed_hunt_efficiency(
    state: Mapping[str, Any],
    visits: Iterable[tuple[Mapping[str, Any], Mapping[str, Any]]],
    *, policy_id: str, source_policy_id: str, mobile_vnum: int,
    prior_level_source_policy_id: str | None = None,
    audited_source_revision: str | None = None,
) -> HuntVisitEfficiency | None:
    """Measure bounded completed visits; a rate never authorizes an encounter."""
    xp = 0
    seconds = 0.0
    run_ids: list[int] = []
    productive = 0
    for index, (segment, summary) in enumerate(visits):
        if index >= 8:
            break
        run = summary.get("run")
        outcomes = summary.get("outcomes")
        progress = summary.get("progress")
        if not all(isinstance(value, Mapping) for value in (run, outcomes, progress)):
            continue
        run_id = run.get("id")
        duration = run.get("duration_seconds")
        if (
            summary.get("summary_version") != RUN_REPORT_SUMMARY_VERSION
            or segment.get("phase") != policy_id or not segment.get("finished_at")
            or segment.get("status") not in {"success", "ready"}
            or type(segment.get("command_count")) is not int or segment["command_count"] <= 0
            or type(run_id) is not int or run_id != segment.get("run_id") or run_id in run_ids
            or type(duration) not in (int, float) or not math.isfinite(duration) or duration <= 0
            or outcomes.get("execution") not in {"success", "ready"}
            or outcomes.get("safety") != "safe"
        ):
            continue
        completed = completed_single_target_hunt(
            state, segment, summary, policy_id=policy_id,
            source_policy_id=source_policy_id, mobile_vnum=mobile_vnum,
            prior_level_source_policy_id=prior_level_source_policy_id,
            audited_source_revision=audited_source_revision,
        )
        experience = progress.get("experience")
        if not isinstance(experience, Mapping) or type(experience.get("change")) is not int:
            continue
        delta = experience["change"]
        if not completed:
            # Include safe, zero-progress visits to this same current-band
            # route in its cost, not as productive or retry evidence.
            if delta != 0 or progress.get("confirmed_kills") or outcomes.get("objective") not in {"not_achieved", "unknown"}:
                continue
            try:
                start = json.loads(segment.get("start_state_json") or "{}")
                end = json.loads(segment.get("end_state_json") or "{}")
            except (TypeError, ValueError):
                continue
            if not isinstance(start, Mapping) or not isinstance(end, Mapping):
                continue
            if any(state.get(key) is None or not state[key] == start.get(key) == end.get(key)
                   for key in ("level", "world_boot_id")):
                continue
            revision = start.get("campaign_source_revision")
            if (
                not revision or revision != end.get("campaign_source_revision")
                or (revision != state.get("campaign_source_revision")
                    and audited_source_revision != state.get("campaign_source_revision"))
                or any(str(snapshot.get("room_vnum")) != "3054" or snapshot.get("dead") is not False
                       or snapshot.get("in_combat") is not False
                       or type(snapshot.get("hp")) is not int or snapshot["hp"] <= 0
                       for snapshot in (start, end))
                or type(start.get("xp")) is not int or start["xp"] != end.get("xp")
                or type(start.get("campaign_xp_loss_total")) is not int
                or start["campaign_xp_loss_total"] != end.get("campaign_xp_loss_total")
            ):
                continue
        elif delta <= 0:
            continue
        xp += delta
        seconds += duration
        run_ids.append(run_id)
        productive += int(completed)
    if not productive or not run_ids or xp <= 0:
        return None
    return HuntVisitEfficiency(xp, seconds, tuple(run_ids), productive)
