from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from .decisions import classify_decision
from .report_migrations import migrate_legacy_run_context
from .storage import RUN_REPORT_SUMMARY_VERSION, RunStorage


def build_run_report(
    storage: RunStorage,
    run_id: int,
    *,
    commentary_limit: int = 20,
) -> dict[str, Any]:
    if commentary_limit < 1:
        raise ValueError("commentary_limit must be at least 1")
    cached = storage.get_run_summary(run_id)
    if (
        cached is not None
        and cached.get("summary_version") == RUN_REPORT_SUMMARY_VERSION
    ):
        cached_limit = len(cached.get("commentary") or ())
        if commentary_limit <= cached_limit or cached_limit < 100:
            cached = dict(cached)
            cached["commentary"] = list(cached.get("commentary") or ())[:commentary_limit]
            cached_run = cached.get("run")
            outcomes = cached.get("outcomes")
            if (
                cached["commentary"]
                and isinstance(cached_run, dict)
                and isinstance(outcomes, dict)
            ):
                run_record = storage.get_run(run_id)
                cached["commentary"][-1] = _run_outcome_ending(
                    str(
                        outcomes.get("execution")
                        or cached_run.get("status")
                        or "unknown"
                    ),
                    str(run_record["error"]) if run_record is not None and run_record["error"] else None,
                    str(outcomes.get("objective") or "unknown"),
                    str(outcomes.get("safety") or "unknown"),
                )
            return cached
    report = _build_run_report_uncached(
        storage, run_id, commentary_limit=commentary_limit,
    )
    run = storage.get_run(run_id)
    if run is not None and run["finished_at"] is not None and not storage.read_only:
        storage.save_run_summary(run_id, report)
    return report


def _build_run_report_uncached(
    storage: RunStorage,
    run_id: int,
    *,
    commentary_limit: int = 20,
) -> dict[str, Any]:
    """Build a deterministic summary from a stored run and its evidence."""
    if commentary_limit < 1:
        raise ValueError("commentary_limit must be at least 1")

    run = storage.get_run(run_id)
    if run is None:
        raise LookupError(f"No run with id {run_id}")

    events = [_event_from_row(event) for event in storage.list_events(run_id)]
    snapshots = [
        _snapshot_from_row(snapshot)
        for snapshot in storage.list_state_snapshots(run_id)
    ]
    initial_state = _initial_observed_state(snapshots)
    final_state = snapshots[-1]["state"] if snapshots else {}
    game_events = [event for event in events if event["kind"] == "game_event"]
    decisions = [event for event in events if event["kind"] == "decision"]
    run_context = next(
        (
            event["payload"]
            for event in reversed(events)
            if event["kind"] == "run_context"
        ),
        {},
    )
    run_context = migrate_legacy_run_context(run_context)
    game_event_counts = Counter(
        str(event["payload"].get("type", "unknown")) for event in game_events
    )
    event_counts = Counter(event["kind"] for event in events)
    duration_seconds = _duration_seconds(run["started_at"], run["finished_at"])
    confirmed_kills = _completed_kills(events)
    sales = [dict(sale) for sale in storage.list_loot_sales_for_run(run_id)]
    sale_rejections = _sale_rejections_from_events(events)

    progress = _progress_summary(
        initial_state,
        final_state,
        snapshots,
        game_event_counts,
        game_events,
        decisions,
        confirmed_kills,
        sales,
        sale_rejections,
    )
    failures = _failures(run, game_event_counts)
    balance_signals = _balance_signals(progress, game_event_counts)
    activity = _activity_metrics(
        events,
        run["started_at"],
        run["finished_at"],
    )
    objective_evidence = _terminal_objective_failure_evidence(events)
    calculated_objective = _objective_outcome(
        run_context, final_state, confirmed_kills, events,
        initial_state=initial_state,
        scenario_name=str(run["scenario_name"] or ""),
    )
    outcomes = {
        "execution": run["execution_status"] or run["status"],
        "objective": (
            calculated_objective
            if calculated_objective != "unknown"
            else "unknown"
        ),
        "safety": run["safety_outcome"] or _safety_outcome(
            run, final_state, game_event_counts,
        ),
    }
    commentary = _commentary(
        events,
        outcomes["execution"],
        run["error"],
        progress,
        commentary_limit,
        objective_outcome=outcomes["objective"],
        safety_outcome=outcomes["safety"],
    )

    return {
        "summary_version": RUN_REPORT_SUMMARY_VERSION,
        "run": {
            "id": run["id"],
            "scenario_name": run["scenario_name"],
            "scenario_path": run["scenario_path"],
            "status": run["status"],
            "started_at": run["started_at"],
            "finished_at": run["finished_at"],
            "duration_seconds": duration_seconds,
            "transcript_path": run["transcript_path"],
        },
        "character": dict(run_context.get("character") or {}),
        "objective": dict(run_context.get("objective") or {}),
        "objective_evidence": objective_evidence,
        "outcomes": outcomes,
        "progress": progress,
        "activity": activity,
        "decision_analysis": _decision_analysis(decisions),
        "failures": failures,
        "balance_signals": balance_signals,
        "commentary": commentary,
        "evidence": {
            "event_counts": dict(sorted(event_counts.items())),
            "game_event_counts": dict(sorted(game_event_counts.items())),
            "state_snapshot_count": len(snapshots),
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    """Render a compact, human-readable form of a run report."""
    run = report["run"]
    progress = report["progress"]
    character = report.get("character") or {}
    identity = _format_identity(character)
    lines = [
        f"# Run {run['id']}: {run['scenario_name']}",
        "",
        f"Run record: **{'finished' if run['finished_at'] else 'running'}**",
        "Execution: **{execution}**; objective: **{objective}**; safety: **{safety}**".format(
            **report["outcomes"]
        ),
        *(
            [f"Objective evidence: {'; '.join(report['objective_evidence'])}"]
            if report.get("objective_evidence")
            else []
        ),
        f"Started: {run['started_at']}",
        f"Finished: {run['finished_at'] or '-'}",
        f"Duration: {_format_duration(run['duration_seconds'])}",
        f"Transcript: {run['transcript_path'] or '-'}",
        f"Character: {identity}",
        "",
        "## Progress",
        "",
        "| Measure | Initial | Final | Change |",
        "| --- | ---: | ---: | ---: |",
        _change_row("Level", progress["level"]),
        _change_row("XP", progress["experience"]),
        _change_row("Health", progress["health"], resource=True),
        "",
        f"Initial room: {progress['room']['initial'] or '-'}  ",
        f"Final room: {progress['room']['final'] or '-'}  ",
        f"Combat starts: {progress['combat_starts']}  ",
        f"Combat decisions: {progress['combat_decisions']}  ",
        f"Confirmed kills: {_format_confirmed_kills(progress['confirmed_kills'])}  ",
        f"Observed level gains: {progress['level_gains_observed']}  ",
        f"Items acquired: {progress['items_acquired']}  ",
        f"Quests received: {progress['quests_received']}  ",
        f"Training: {_format_training(progress['training'])}  ",
        f"Loot sales: {_format_sales(progress['loot_sales'])}",
        f"Loot sale refusals: {_format_sale_rejections(progress['loot_sale_rejections'])}",
        "",
        "## Time Use",
        "",
        f"Productive combat: {_format_duration(report['activity']['productive_combat_seconds'])}",
        f"Travel: {_format_duration(report['activity']['travel_seconds'])}",
        f"Maintenance: {_format_duration(report['activity']['maintenance_seconds'])}",
        f"Waiting: {_format_duration(report['activity']['waiting_seconds'])}",
        "",
        "## Decision Analysis",
        "",
        _count_line(
            "Decision categories",
            report["decision_analysis"]["category_counts"],
        ),
        (
            "Safety-critical decisions: "
            f"{report['decision_analysis']['safety_critical_count']}"
        ),
        "",
        "Notable choices:",
    ]
    persona_lines = _persona_lines(character)
    if persona_lines:
        character_index = lines.index(f"Character: {identity}") + 1
        lines[character_index:character_index] = persona_lines
    notable_decisions = report["decision_analysis"]["notable_decisions"]
    lines.extend(
        f"- **{decision['category']}:** {decision['reason']}"
        for decision in notable_decisions
    )
    if not notable_decisions:
        lines.append("- No decision explanations were recorded.")
    lines.extend([
        "",
        "## Failures",
        "",
    ])
    lines.extend(f"- {failure}" for failure in report["failures"])
    if not report["failures"]:
        lines.append("- None detected.")

    lines.extend(["", "## Balance Signals", ""])
    if report["balance_signals"]:
        lines.extend(
            f"- **{signal['severity']} - {signal['name']}:** {signal['detail']}"
            for signal in report["balance_signals"]
        )
    else:
        lines.append("- No balance signals were available from this run.")

    lines.extend(["", "## Representative Commentary", ""])
    if report["commentary"]:
        lines.extend(f"- {comment}" for comment in report["commentary"])
    else:
        lines.append("- No representative events were recorded.")

    lines.extend(["", "## Evidence", ""])
    evidence = report["evidence"]
    lines.append(f"State snapshots: {evidence['state_snapshot_count']}")
    lines.append(_count_line("Recorded events", evidence["event_counts"]))
    lines.append(_count_line("Game events", evidence["game_event_counts"]))
    return "\n".join(lines) + "\n"


def render_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def build_campaign_report(
    storage: RunStorage,
    campaign_id: int,
    *,
    commentary_limit: int = 40,
    full_history: bool = False,
) -> dict[str, Any]:
    """Build a durable summary across every run in one campaign."""
    if commentary_limit < 1:
        raise ValueError("commentary_limit must be at least 1")

    campaign = storage.get_campaign(campaign_id)
    if campaign is None:
        raise LookupError(f"No campaign with id {campaign_id}")

    segments = (
        [
            dict(row)
            for row in storage.list_campaign_segment_summaries(
                campaign_id,
                include_state_progress=True,
            )
        ]
        if full_history
        else []
    )
    checkpoints = [
        dict(row)
        for row in storage.get_campaign_checkpoint_boundaries(campaign_id)
    ]
    first_state_json, last_state_json = (
        storage.get_campaign_segment_boundary_states(campaign_id)
    )
    initial_state = _campaign_state_from_json(first_state_json)
    if not initial_state and checkpoints:
        initial_state = _campaign_state_from_json(checkpoints[0].get("state_json"))
    final_state = (
        _campaign_state_from_json(last_state_json)
        or _campaign_state_from_json(
            checkpoints[-1].get("state_json") if checkpoints else None
        )
    )

    run_summaries: list[dict[str, Any]] = []
    kills: list[dict[str, Any]] = []
    sale_rejections: list[dict[str, Any]] = []
    commentary: list[str] = []
    character: dict[str, Any] = {}
    death_count = 0
    summary_run_count = 0
    progress_by_run: dict[int, dict[str, Any]] = {}
    segment_count_by_run: Counter[int] = Counter(
        int(segment["run_id"])
        for segment in segments
        if segment.get("run_id") is not None
    )
    campaign_runs = storage.list_campaign_run_records(campaign_id)
    run_ids = list(campaign_runs)
    kills_by_run: dict[int, list[Any]] = {}
    for kill_row in storage.list_campaign_mob_kills(campaign_id):
        kills_by_run.setdefault(int(kill_row["run_id"]), []).append(kill_row)
    segment_by_run = {
        int(segment["run_id"]): segment
        for segment in segments
        if segment.get("run_id") is not None
        and segment_count_by_run[int(segment["run_id"])] == 1
    }
    for run_id in run_ids:
        run, run_report = campaign_runs[run_id]
        if run_report is not None:
            summary_run_count += 1
            if not character:
                character = dict(run_report.get("character") or {})
            game_counts = run_report.get("evidence", {}).get("game_event_counts", {})
            death_count += int(game_counts.get("character_died", 0) or 0)
            commentary.extend(
                str(item)
                for item in run_report.get("commentary", ())
                if str(item).strip()
            )
            run_activity = run_report.get("activity", {})
            run_progress = run_report.get("progress", {})
            run_failures = run_report.get("failures", [])
            run_outcomes = run_report.get("outcomes", {})
        else:
            if not character and initial_state.get("name"):
                character = {"name": initial_state["name"]}
            segment = segment_by_run.get(run_id)
            run_activity = (
                _json_dict(segment.get("metrics_json")).get("activity", {})
                if segment is not None
                else {}
            )
            run_progress = {}
            run_failures = []
            run_outcomes = {
                "execution": run["execution_status"] or run["status"],
                "objective": run["objective_outcome"] or "unknown",
                "safety": run["safety_outcome"] or "unknown",
            }
        run_summaries.append(
            {
                "id": run["id"],
                "scenario_name": run["scenario_name"],
                "status": run["status"],
                "started_at": run["started_at"],
                "finished_at": run["finished_at"],
                "transcript_path": run["transcript_path"],
                "outcomes": run_outcomes,
                "activity": run_activity,
                "progress": run_progress,
                "failures": run_failures,
                "summary_available": run_report is not None,
            }
        )
        progress_by_run[run_id] = run_progress
        for kill in kills_by_run.get(run_id, ()):
            kills.append(
                {
                    "run_id": int(kill["run_id"]),
                    "mob_name": kill["mob_name"],
                    "xp_gained": kill["xp_gained"],
                    "source_mobile_vnum": kill["source_mobile_vnum"],
                    "source_policy_id": kill["source_policy_id"],
                    "below_useful_band": bool(kill["below_useful_band"]),
                    "objective_eligible": bool(kill["objective_eligible"]),
                    "route_gate": bool(kill["route_gate"]),
                    "timestamp": kill["timestamp"],
                }
            )
        if run_report is not None:
            for rejection in run_report["progress"].get(
                "loot_sale_rejections", ()
            ):
                sale_rejection = dict(rejection)
                sale_rejection["run_id"] = run_id
                sale_rejections.append(sale_rejection)

    unique_commentary = list(dict.fromkeys(commentary))[:commentary_limit]
    target_level = int(campaign["target_level"])
    final_level = _campaign_int(final_state.get("level"))
    initial_level = _campaign_int(initial_state.get("level"))
    final_xp = _campaign_int(final_state.get("xp"))
    initial_xp = _campaign_int(initial_state.get("xp"))
    totals = storage.campaign_totals(campaign_id)
    run_link_backfill = storage.get_campaign_run_link_backfill_state(campaign_id)
    outcome_counts = {
        dimension: dict(Counter(
            str((run.get("outcomes") or {}).get(dimension) or "unknown")
            for run in run_summaries
        ))
        for dimension in ("execution", "objective", "safety")
    }

    return {
        "schema": 1,
        "campaign": dict(campaign),
        "character": character,
        "target": {
            "level": target_level,
            "reached": final_level is not None and final_level >= target_level,
        },
        "progress": {
            "initial_level": initial_level,
            "final_level": final_level,
            "level_change": _campaign_delta(initial_level, final_level),
            "initial_xp": initial_xp,
            "final_xp": final_xp,
            "xp_change": _campaign_delta(initial_xp, final_xp),
            "quest": {
                "points": _campaign_int(final_state.get("quest_points")),
                "total_points": _campaign_int(
                    final_state.get("total_quest_points")
                ),
                "level_required": _campaign_int(
                    final_state.get("quest_level_qp_required")
                ),
                "shortfall": _campaign_int(
                    final_state.get("quest_level_qp_shortfall")
                ),
            },
            "final_room": final_state.get("room_name"),
            "final_room_vnum": final_state.get("room_vnum"),
            "alive": not bool(final_state.get("dead")),
        },
        "totals": {
            "segments": int(totals["segment_count"]),
            "commands": int(totals["command_count"]),
            "duration_seconds": float(totals["duration_seconds"]),
            "runs": len(run_ids),
            "deaths": death_count,
            "kills": len(kills),
            "activity": _sum_activity_metrics(run_summaries),
            "activity_complete": summary_run_count == len(run_summaries),
            "outcomes": outcome_counts,
        },
        "segments": [
            _campaign_segment_summary(
                segment,
                progress_by_run.get(int(segment["run_id"]))
                if segment.get("run_id") is not None
                and segment_count_by_run[int(segment["run_id"])] == 1
                else None,
            )
            for segment in segments
        ],
        "runs": run_summaries,
        "kills": kills,
        "sale_rejections": sale_rejections,
        "commentary": unique_commentary,
        "evidence": {
            "run_ids": run_ids,
            "completed_run_summary_count": summary_run_count,
            "legacy_runs_without_summary": len(run_summaries) - summary_run_count,
            "segment_details_included": full_history,
            "run_link_backfill_complete": run_link_backfill["complete"],
            "checkpoint_id": checkpoints[-1]["id"] if checkpoints else None,
            "checkpoint_count": len(checkpoints),
        },
    }


def render_campaign_markdown(report: dict[str, Any]) -> str:
    """Render the campaign report for people inspecting a HERO run."""
    campaign = report["campaign"]
    character = report.get("character") or {}
    progress = report["progress"]
    target = report["target"]
    lines = [
        f"# Campaign {campaign['id']}: {campaign['name']}",
        "",
        f"Status: **{campaign['status']}**",
        f"Character: {_format_identity(character) if character else '-'}",
        f"Target: level {target['level']} ({'reached' if target['reached'] else 'not reached'})",
        f"Final location: {progress['final_room'] or '-'} ({progress['final_room_vnum'] or '-'})",
        f"Alive at checkpoint: {'yes' if progress['alive'] else 'no'}",
        "",
        "## Progress",
        "",
        "| Measure | Initial | Final | Change |",
        "| --- | ---: | ---: | ---: |",
        f"| Level | {progress['initial_level'] or '-'} | {progress['final_level'] or '-'} | {progress['level_change'] if progress['level_change'] is not None else '-'} |",
        f"| XP | {progress['initial_xp'] or '-'} | {progress['final_xp'] or '-'} | {progress['xp_change'] if progress['xp_change'] is not None else '-'} |",
        "",
        "Quest points: "
        f"{progress['quest']['points'] if progress['quest']['points'] is not None else '-'} "
        f"total; next gate "
        f"{progress['quest']['level_required'] if progress['quest']['level_required'] is not None else '-'}; "
        f"shortfall {progress['quest']['shortfall'] or 0}.",
        "",
        "## Totals",
        "",
        f"Segments: {report['totals']['segments']}",
        f"Runs: {report['totals']['runs']}",
        f"Commands: {report['totals']['commands']}",
        f"Confirmed kills: {report['totals']['kills']}",
        f"Deaths: {report['totals']['deaths']}",
        "",
        "## Run Outcomes",
        "",
        "Execution: "
        + _format_outcome_counts(report["totals"]["outcomes"]["execution"]),
        "Objective: "
        + _format_outcome_counts(report["totals"]["outcomes"]["objective"]),
        "Safety: "
        + _format_outcome_counts(report["totals"]["outcomes"]["safety"]),
        "",
        "## Time Use",
        "",
        f"Productive combat: {_format_duration(report['totals']['activity']['productive_combat_seconds'])}",
        f"Travel: {_format_duration(report['totals']['activity']['travel_seconds'])}",
        f"Maintenance: {_format_duration(report['totals']['activity']['maintenance_seconds'])}",
        f"Waiting: {_format_duration(report['totals']['activity']['waiting_seconds'])}",
        *(
            [
                "Time-use coverage is partial; run `summarize-runs` to backfill "
                "older completed sessions."
            ]
            if not report["totals"].get("activity_complete", True)
            else []
        ),
        "",
        "## Kills",
        "",
    ]
    if not report["evidence"].get("run_link_backfill_complete", True):
        lines.extend(
            [
                "",
                "Run-summary coverage is incomplete. Continue the bounded link "
                f"backfill with `python -m dd4tester backfill-campaign-runs {campaign['id']}`.",
            ]
        )
    persona_lines = _persona_lines(character)
    if persona_lines and character:
        character_line = f"Character: {_format_identity(character)}"
        character_index = lines.index(character_line) + 1
        lines[character_index:character_index] = persona_lines
    if report["kills"]:
        lines.extend(
            "- {mob_name} (+{xp_gained} XP, run {run_id})".format(**kill)
            for kill in report["kills"]
        )
    else:
        lines.append("- None recorded.")
    if report.get("sale_rejections"):
        lines.extend(["", "## Sale Rejections", ""])
        for rejection in report["sale_rejections"]:
            item = rejection.get("item_description", "item")
            shop = (
                rejection.get("shop_name")
                or rejection.get("shopkeeper")
                or "shopkeeper"
            )
            lines.append(
                f"- {item} was refused by {shop} (run {rejection['run_id']})."
            )
    lines.extend(["", "## Commentary", ""])
    lines.extend(f"- {item}" for item in report["commentary"])
    if not report["commentary"]:
        lines.append("- No representative commentary was recorded.")
    return "\n".join(lines) + "\n"


def write_campaign_report(
    storage: RunStorage,
    campaign_id: int,
    *,
    directory: Path | None = None,
    commentary_limit: int = 40,
) -> tuple[Path, Path]:
    """Write JSON and Markdown campaign reports beside its campaign YAML."""
    report = build_campaign_report(
        storage,
        campaign_id,
        commentary_limit=commentary_limit,
    )
    campaign = report["campaign"]
    output_directory = (
        directory
        if directory is not None
        else Path(str(campaign["config_path"])).resolve().parent
    )
    output_directory.mkdir(parents=True, exist_ok=True)
    json_path = output_directory / "hero-report.json"
    markdown_path = output_directory / "hero-report.md"
    json_path.write_text(render_json(report), encoding="utf-8")
    markdown_path.write_text(
        render_campaign_markdown(report),
        encoding="utf-8",
    )
    return json_path, markdown_path


def _campaign_state_from_json(value: Any) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value) if isinstance(value, str) else value
    except (TypeError, json.JSONDecodeError):
        return {}
    return dict(parsed) if isinstance(parsed, dict) else {}


def _campaign_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _campaign_delta(initial: int | None, final: int | None) -> int | None:
    if initial is None or final is None:
        return None
    return final - initial


def _campaign_segment_summary(
    segment: dict[str, Any],
    run_progress: dict[str, Any] | None = None,
) -> dict[str, Any]:
    start = _campaign_state_from_json(segment.get("start_state_json"))
    end = _campaign_state_from_json(segment.get("end_state_json"))
    run_level = (run_progress or {}).get("level")
    run_xp = (run_progress or {}).get("experience")
    if not isinstance(run_level, dict):
        run_level = {}
    if not isinstance(run_xp, dict):
        run_xp = {}
    return {
        "id": segment["id"],
        "sequence": segment["sequence"],
        "phase": segment["phase"],
        "run_id": segment["run_id"],
        "status": segment["status"],
        "execution_status": segment.get("execution_status") or segment["status"],
        "objective_outcome": segment.get("objective_outcome") or "unknown",
        "safety_outcome": segment.get("safety_outcome") or "unknown",
        "metrics": _json_dict(segment.get("metrics_json")),
        "error": segment["error"],
        "started_at": segment["started_at"],
        "finished_at": segment["finished_at"],
        "command_count": segment["command_count"],
        "duration_seconds": segment["duration_seconds"],
        "start_level": start.get("level", run_level.get("initial")),
        "end_level": end.get("level", run_level.get("final")),
        "start_xp": start.get("xp", run_xp.get("initial")),
        "end_xp": end.get("xp", run_xp.get("final")),
    }


def _event_from_row(row: Any) -> dict[str, Any]:
    return {
        "timestamp": row["timestamp"],
        "kind": row["kind"],
        "payload": json.loads(row["payload_json"]),
    }


def _snapshot_from_row(row: Any) -> dict[str, Any]:
    return {
        "timestamp": row["timestamp"],
        "reason": row["reason"],
        "state": json.loads(row["state_json"]),
    }


def _initial_observed_state(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    """Use the first state with core GMCP values, not a partial room update."""
    for snapshot in snapshots:
        state = snapshot["state"]
        if all(state.get(field) is not None for field in ("level", "xp", "hp", "max_hp")):
            return state
    return snapshots[0]["state"] if snapshots else {}


def _progress_summary(
    initial: dict[str, Any],
    final: dict[str, Any],
    snapshots: list[dict[str, Any]],
    game_event_counts: Counter[str],
    game_events: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    confirmed_kills: list[dict[str, Any]],
    sales: list[dict[str, Any]],
    sale_rejections: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    health_samples = [
        _fraction(snapshot["state"].get("hp"), snapshot["state"].get("max_hp"))
        for snapshot in snapshots
    ]
    health_samples = [sample for sample in health_samples if sample is not None]
    return {
        "level": _change(initial.get("level"), final.get("level")),
        "experience": _change(initial.get("xp"), final.get("xp")),
        "health": {
            **_change(initial.get("hp"), final.get("hp")),
            "initial_maximum": initial.get("max_hp"),
            "final_maximum": final.get("max_hp"),
            "lowest_fraction": min(health_samples) if health_samples else None,
        },
        "room": {"initial": initial.get("room_name"), "final": final.get("room_name")},
        "combat_starts": max(
            game_event_counts["combat_started"],
            _inferred_combat_start_count(game_events),
            len(confirmed_kills),
        ),
        "combat_decisions": sum(_is_combat_decision(decision) for decision in decisions),
        "confirmed_kills": confirmed_kills,
        "level_gains_observed": game_event_counts["level_gained"],
        "items_acquired": sum(
            _item_acquisition_count(event) for event in game_events
        ),
        "quests_received": game_event_counts["quest_received"],
        "training": _training_summary(game_events),
        "loot_sales": _sales_summary(sales),
        "loot_sale_rejections": list(sale_rejections or ()),
    }


def _inferred_combat_start_count(game_events: list[dict[str, Any]]) -> int:
    """Infer fight starts from the current-enemy stream when start text is absent."""
    engaged = False
    starts = 0
    for event in game_events:
        payload = event.get("payload", {})
        event_type = payload.get("type")
        if event_type == "combat_started":
            if not engaged:
                starts += 1
            engaged = True
            continue
        if event_type != "enemies_changed":
            continue
        data = payload.get("data")
        enemy_value = data.get("value") if isinstance(data, dict) else None
        has_enemies = _contains_enemy_record(enemy_value)
        if has_enemies and not engaged:
            starts += 1
        engaged = has_enemies
    return starts


def _contains_enemy_record(value: Any) -> bool:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return False
    if isinstance(value, dict):
        return "name" in value or "isnpc" in value
    if isinstance(value, (list, tuple)):
        return any(_contains_enemy_record(item) for item in value)
    return False


def _decision_analysis(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    categories: Counter[str] = Counter()
    safety_critical_count = 0
    notable: list[dict[str, Any]] = []
    seen_reasons: set[str] = set()
    for event in decisions:
        payload = event["payload"]
        reason = str(payload.get("reason", "")).strip()
        stage = str(payload.get("stage", ""))
        command = str(payload.get("command", ""))
        metadata = classify_decision(command, reason, stage)
        category = str(payload.get("category") or metadata.category)
        safety_critical = bool(
            payload.get("safety_critical", metadata.safety_critical)
        )
        categories[category] += 1
        safety_critical_count += int(safety_critical)
        if reason and reason not in seen_reasons and len(notable) < 12:
            notable.append(
                {
                    "category": category,
                    "reason": reason,
                    "stage": stage,
                    "safety_critical": safety_critical,
                }
            )
            seen_reasons.add(reason)
    return {
        "category_counts": dict(sorted(categories.items())),
        "safety_critical_count": safety_critical_count,
        "notable_decisions": notable,
    }


def _failures(run: Any, game_event_counts: Counter[str]) -> list[str]:
    failures: list[str] = []
    if run["status"] != "success":
        detail = run["error"] or f"Run ended with status {run['status']}."
        failures.append(detail)
    deaths = game_event_counts["character_died"]
    if deaths:
        failures.append(f"Character died {deaths} time(s).")
    return failures


def _balance_signals(
    progress: dict[str, Any], game_event_counts: Counter[str]
) -> list[dict[str, str]]:
    signals: list[dict[str, str]] = []
    level_change = progress["level"]["change"]
    level_gains = progress["level_gains_observed"]
    if level_change is not None or level_gains:
        if level_change is not None:
            detail = f"Level changed by {level_change:+g}."
        else:
            detail = (
                f"Detected {level_gains} level gain event(s); final recorded level "
                f"was {progress['level']['final']}."
            )
        signals.append(
            {
                "name": "progression",
                "severity": "info",
                "detail": detail,
            }
        )

    xp_change = progress["experience"]["change"]
    if xp_change is not None:
        signals.append(
            {
                "name": "experience",
                "severity": "info",
                "detail": f"XP changed by {xp_change:+g}.",
            }
        )

    sales = progress["loot_sales"]
    if sales["count"]:
        shops = ", ".join(sales["shops"])
        signals.append(
            {
                "name": "loot sales",
                "severity": "info",
                "detail": (
                    f"Sold {sales['count']} item(s) for {sales['coins']} coins "
                    f"through {shops}."
                ),
            }
        )

    sale_rejections = progress["loot_sale_rejections"]
    if sale_rejections:
        signals.append(
            {
                "name": "loot sale refusals",
                "severity": "warning",
                "detail": (
                    f"{len(sale_rejections)} item offer(s) were refused by "
                    "a safe shopkeeper."
                ),
            }
        )

    lowest_fraction = progress["health"]["lowest_fraction"]
    if lowest_fraction is not None and lowest_fraction <= 0.25:
        severity = "critical" if lowest_fraction <= 0.1 else "warning"
        signals.append(
            {
                "name": "health pressure",
                "severity": severity,
                "detail": f"Health reached {lowest_fraction:.0%} of maximum.",
            }
        )

    combats = progress["combat_starts"]
    combat_decisions = progress["combat_decisions"]
    deaths = game_event_counts["character_died"]
    if combats or combat_decisions:
        detail = (
            f"Recorded {combat_decisions} combat decision(s) and detected "
            f"{combats} combat start(s)"
        )
        if deaths:
            detail += f" and {deaths} death(s)."
        else:
            detail += " without a detected death."
        confirmed_kills = progress["confirmed_kills"]
        if confirmed_kills:
            detail += f" Confirmed kills: {_format_confirmed_kills(confirmed_kills)}."
        signals.append({"name": "combat", "severity": "info", "detail": detail})
    return signals


def _commentary(
    events: list[dict[str, Any]],
    status: str,
    error: str | None,
    progress: dict[str, Any],
    limit: int,
    *,
    objective_outcome: str = "unknown",
    safety_outcome: str = "unknown",
) -> list[str]:
    comments: list[tuple[int, str]] = []
    seen: set[str] = set()
    for event in events:
        comment = _comment_for_event(event)
        if comment and comment[1] not in seen:
            comments.append(comment)
            seen.add(comment[1])

    experience_change = progress["experience"]["change"]
    if experience_change is not None:
        amount = int(experience_change)
        if amount > 0:
            comments.append((0, f"I gained {amount} experience points."))
        elif amount < 0:
            comments.append((0, f"I lost {abs(amount)} experience points."))
        elif not progress["confirmed_kills"]:
            comments.append((0, "I made no experience progress this run."))

    ending = _run_outcome_ending(
        status, error, objective_outcome, safety_outcome,
    )
    return _select_commentary(comments, ending, limit)


def _run_outcome_ending(
    status: str,
    error: str | None,
    objective_outcome: str,
    safety_outcome: str,
) -> str:
    if status != "success":
        return f"The run stopped: {error or status}."
    if objective_outcome == "achieved":
        if safety_outcome == "loss":
            return "I achieved the objective, but the run recorded an XP loss."
        return "I completed the objective successfully."
    if objective_outcome == "not_achieved":
        if safety_outcome == "loss":
            return "I finished without achieving the objective and recorded an XP loss."
        if safety_outcome == "safe":
            return "I finished safely, but did not achieve the objective."
        return "I finished without achieving the objective; safety is unverified."
    if safety_outcome == "loss":
        return "I finished with an XP loss; objective completion is unverified."
    return "I finished the run; objective completion is unverified."


def _comment_for_event(event: dict[str, Any]) -> tuple[int, str] | None:
    payload = event["payload"]
    if event["kind"] == "decision":
        reason = str(payload.get("reason", "")).strip()
        if reason and _noteworthy_reason(reason):
            return 1, f"I chose to {reason[0].lower() + reason[1:]}."
        return None
    if event["kind"] == "state":
        kills = event["payload"].get("completed_kills")
        if isinstance(kills, list) and kills:
            return 1, f"I confirmed kills: {_format_confirmed_kills(kills)}."
    if event["kind"] != "game_event":
        return None

    event_type = payload.get("type")
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    if event_type == "room_entered" and data.get("name"):
        return 2, f"I entered {data['name']}."
    if event_type == "combat_started" and data.get("target"):
        return 1, f"I began a fight with {data['target']}."
    if event_type == "item_acquired":
        item = data.get("item", data.get("name"))
        if item and not _is_experience_item(item):
            return 1, f"I acquired {item}."
    if event_type == "quest_received" and data.get("name"):
        return 1, f"I received the quest {data['name']}."
    if event_type == "level_gained" and data.get("level") is not None:
        return 0, f"I reached level {data['level']}."
    if event_type == "training_completed" and data.get("skill"):
        return 1, f"I trained {data['skill']} after the trainer confirmed the lesson."
    if event_type == "training_rejected" and data.get("skill"):
        reason = data.get("reason", "the trainer rejected the lesson")
        return 1, f"I preserved a practice when {data['skill']} was rejected: {reason}."
    if event_type == "character_died":
        return 0, "I died and need to review this part of the run."
    return None


def _select_commentary(
    comments: list[tuple[int, str]],
    ending: str,
    limit: int,
) -> list[str]:
    if limit == 1:
        return [ending]
    slots = limit - 1
    selected: set[int] = set()
    for priority in (0, 1, 2):
        for index, (item_priority, _comment) in enumerate(comments):
            if item_priority == priority and len(selected) < slots:
                selected.add(index)
    chosen = [
        comment
        for index, (_priority, comment) in enumerate(comments)
        if index in selected
    ]
    return chosen + [ending]


def _noteworthy_reason(reason: str) -> bool:
    words = (
        "create",
        "tutorial",
        "fight",
        "combat",
        "recover",
        "provision",
        "practice",
        "portal",
        "save",
        "quit",
    )
    normalized = reason.casefold()
    return any(word in normalized for word in words)


def _is_combat_decision(event: dict[str, Any]) -> bool:
    payload = event["payload"]
    category = payload.get("category")
    if isinstance(category, str) and category.casefold() == "combat":
        return True
    metadata = classify_decision(
        str(payload.get("command", "")),
        str(payload.get("reason", "")),
        str(payload.get("stage", "")),
    )
    return metadata.category == "combat"


def _is_item_acquisition(event: dict[str, Any]) -> bool:
    if event["payload"].get("type") != "item_acquired":
        return False
    data = event["payload"].get("data")
    if not isinstance(data, dict):
        return True
    item = data.get("item", data.get("name"))
    return not _is_experience_item(item)


def _item_acquisition_count(event: dict[str, Any]) -> int:
    if not _is_item_acquisition(event):
        return 0
    data = event["payload"].get("data")
    if not isinstance(data, dict):
        return 1
    quantity = data.get("quantity")
    return quantity if isinstance(quantity, int) and quantity > 0 else 1


def _is_experience_item(value: Any) -> bool:
    return isinstance(value, str) and "experience point" in value.casefold()


def _completed_kills(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for event in reversed(events):
        if event["kind"] != "state":
            continue
        kills = event["payload"].get("completed_kills")
        if not isinstance(kills, list):
            continue
        return [dict(kill) for kill in kills if isinstance(kill, dict)]
    return []


def _training_summary(game_events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for event in game_events:
        event_type = event["payload"].get("type")
        if event_type not in {"training_completed", "training_rejected"}:
            continue
        data = event["payload"].get("data")
        if not isinstance(data, dict):
            continue
        target = accepted if event_type == "training_completed" else rejected
        target.append(dict(data))
    return {"accepted": accepted, "rejected": rejected}


def _format_confirmed_kills(kills: list[dict[str, Any]]) -> str:
    entries: list[str] = []
    for kill in kills:
        name = str(kill.get("mob_name", "unknown target"))
        xp = kill.get("xp_gained")
        entries.append(f"{name} (+{xp} XP)" if _is_number(xp) else name)
    return ", ".join(entries) or "none"


_SALE_REJECTION_LINE = re.compile(
    r"^\s*(?P<shop>[^\r\n]+?)\s+looks uninterested in\s+"
    r"(?P<item>[^\.\r\n]+?)\.\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _sale_rejections_from_events(
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Summarize refused shop offers from structured or legacy events."""
    rejections: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    def add(record: dict[str, Any]) -> None:
        item = str(record.get("item_description") or "").strip()
        shop_room = str(record.get("shop_room_vnum") or "").strip()
        shop = str(record.get("shop_name") or record.get("shopkeeper") or "").strip()
        key = (item.casefold(), shop_room, shop.casefold())
        if not item or key in seen:
            return
        seen.add(key)
        rejections.append(
            {
                key_name: value
                for key_name, value in {
                    "item_keyword": record.get("item_keyword"),
                    "item_description": item,
                    "shopkeeper": record.get("shopkeeper"),
                    "shop_name": record.get("shop_name"),
                    "shop_room_vnum": record.get("shop_room_vnum"),
                    "reason": record.get("reason") or "shopkeeper refused item",
                }.items()
                if value is not None
            }
        )

    for event in events:
        payload = event["payload"]
        if event["kind"] == "state":
            for record in payload.get("sale_rejections") or ():
                if isinstance(record, dict):
                    add(record)
            continue
        if event["kind"] != "response":
            continue
        text = payload.get("text") if isinstance(payload, dict) else None
        if not isinstance(text, str):
            continue
        for match in _SALE_REJECTION_LINE.finditer(text.replace("\r", "")):
            add(
                {
                    "item_description": match.group("item").strip(),
                    "shopkeeper": match.group("shop").strip(),
                    "reason": "shopkeeper refused item",
                }
            )
    return rejections


def _sales_summary(sales: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "count": len(sales),
        "coins": sum(int(sale["sold_coins"]) for sale in sales),
        "shops": sorted({str(sale["shop_name"]) for sale in sales}),
        "items": [
            {
                "item": sale["item_description"],
                "shop": sale["shop_name"],
                "coins": sale["sold_coins"],
            }
            for sale in sales
        ],
    }


def _format_sales(sales: dict[str, Any]) -> str:
    if not sales["count"]:
        return "none"
    return f"{sales['count']} item(s) for {sales['coins']} coins"


def _format_sale_rejections(rejections: list[dict[str, Any]]) -> str:
    if not rejections:
        return "none"
    return f"{len(rejections)} item offer(s) refused"


def _format_training(training: dict[str, list[dict[str, Any]]]) -> str:
    accepted = ", ".join(str(item.get("skill")) for item in training["accepted"])
    rejected = ", ".join(str(item.get("skill")) for item in training["rejected"])
    parts = []
    if accepted:
        parts.append(f"accepted {accepted}")
    if rejected:
        parts.append(f"rejected {rejected}")
    return "; ".join(parts) or "none"


def _change(initial: Any, final: Any) -> dict[str, int | float | None]:
    change = None
    if _is_number(initial) and _is_number(final):
        change = final - initial
    return {"initial": initial, "final": final, "change": change}


def _fraction(current: Any, maximum: Any) -> float | None:
    if not _is_number(current) or not _is_number(maximum) or maximum <= 0:
        return None
    return current / maximum


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _duration_seconds(started_at: str, finished_at: str | None) -> float | None:
    if not finished_at:
        return None
    try:
        elapsed = datetime.fromisoformat(finished_at) - datetime.fromisoformat(
            started_at
        )
        return round(elapsed.total_seconds(), 3)
    except ValueError:
        return None


def _activity_metrics(
    events: list[dict[str, Any]], started_at: str, finished_at: str | None,
) -> dict[str, Any]:
    """Estimate whole-run time by the last issued command."""
    duration = _duration_seconds(started_at, finished_at)
    buckets = {
        "productive_combat_seconds": 0.0,
        "travel_seconds": 0.0,
        "maintenance_seconds": 0.0,
        "waiting_seconds": 0.0,
    }
    if duration is None:
        return {**buckets, "total_seconds": None, "basis": "estimated"}
    try:
        start = datetime.fromisoformat(started_at)
        end = datetime.fromisoformat(finished_at) if finished_at else start
    except (TypeError, ValueError):
        return {**buckets, "total_seconds": duration, "basis": "estimated"}
    active = "waiting_seconds"
    previous = start
    for event in events:
        try:
            occurred = datetime.fromisoformat(str(event["timestamp"]))
        except (KeyError, TypeError, ValueError):
            continue
        occurred = min(max(occurred, previous), end)
        buckets[active] += max(0.0, (occurred - previous).total_seconds())
        previous = occurred
        if event.get("kind") == "command":
            payload = event.get("payload")
            command = payload.get("command") if isinstance(payload, dict) else None
            if isinstance(command, str):
                active = _activity_bucket(command)
    buckets[active] += max(0.0, (end - previous).total_seconds())
    return {
        **{key: round(min(duration, value), 2) for key, value in buckets.items()},
        "total_seconds": round(duration, 2),
        "basis": "estimated",
    }


def _activity_bucket(command: str) -> str:
    value = command.strip().casefold()
    words = value.split()
    head = words[0] if words else ""
    if head in {
        "n", "north", "s", "south", "e", "east", "w", "west",
        "u", "up", "d", "down", "recall", "enter", "portal", "fly",
        "climb", "crawl", "open", "unlock",
    }:
        return "travel_seconds"
    if head == "wait" or value.startswith(("quest time", "time reset", "wait for")):
        return "waiting_seconds"
    if head in {
        "kill", "murder", "kick", "bash", "backstab", "disarm", "trip",
        "stun", "punch", "strike", "charge", "ambush", "flee",
    }:
        return "productive_combat_seconds"
    if head == "order" and any(word in value for word in ("attack", "kill", "flee")):
        return "productive_combat_seconds"
    if head == "cast" and any(
        spell in value for spell in (
            "magic missile", "fireball", "lightning bolt", "acid blast",
            "ice storm", "chain lightning",
        )
    ):
        return "productive_combat_seconds"
    return "maintenance_seconds"


def _objective_outcome(
    run_context: dict[str, Any],
    final_state: dict[str, Any],
    confirmed_kills: list[dict[str, Any]],
    events: list[dict[str, Any]],
    *,
    initial_state: dict[str, Any] | None = None,
    scenario_name: str | None = None,
) -> str:
    objective = run_context.get("objective")
    if not isinstance(objective, dict):
        return "unknown"
    checks: list[bool | None] = []
    if _terminal_objective_failure_evidence(events):
        checks.append(False)
    try:
        kill_limit = int(objective["arena_kill_limit"])
    except (KeyError, TypeError, ValueError):
        kill_limit = 0
    try:
        fastwalk_kill_limit = int(objective.get("fastwalk_kill_limit") or 0)
    except (TypeError, ValueError):
        fastwalk_kill_limit = 0
    kill_limit = max(kill_limit, fastwalk_kill_limit)
    world_time_probe = bool(objective.get("world_time_probe"))
    quest_objective = (
        str(objective.get("kind") or "").casefold() == "quest_reward"
        or any(event.get("kind") == "quest_request_attempt" for event in events)
    )
    objective_kind = str(objective.get("kind") or "").casefold()
    legacy_starter_level_objective = (
        scenario_name is None
        or scenario_name.casefold().startswith("starter:")
    )
    if (
        not quest_objective
        and not world_time_probe
        and kill_limit <= 0
        and not objective.get("fastwalk_route")
        and "level" in objective
        and (
            objective_kind in {"level", "progression"}
            or (not objective_kind and legacy_starter_level_objective)
        )
    ):
        try:
            target_level = int(objective["level"])
            final_level = int(final_state["level"])
        except (KeyError, TypeError, ValueError):
            checks.append(None)
        else:
            checks.append(final_level >= target_level)
    if "required_level" in objective:
        try:
            required_level = int(objective["required_level"])
            final_level = int(final_state["level"])
        except (KeyError, TypeError, ValueError):
            checks.append(None)
        else:
            checks.append(final_level >= required_level)
    if kill_limit > 0:
        checks.append(len(confirmed_kills) >= kill_limit)
    if quest_objective:
        initial_points, final_points = _quest_point_bounds(
            objective, initial_state or {}, final_state, events,
        )
        checks.append(
            None
            if initial_points is None or final_points is None
            else final_points > initial_points
        )
    boundaries = objective.get("fastwalk_hunt_stop_boundaries")
    required_items: list[str] = []
    explicit_required_items = objective.get("required_items")
    if isinstance(explicit_required_items, list):
        required_items.extend(
            item.strip().casefold()
            for item in explicit_required_items
            if isinstance(item, str) and item.strip()
        )
    if not required_items and isinstance(boundaries, list):
        for boundary in boundaries:
            if not isinstance(boundary, dict):
                continue
            boundary_items = boundary.get("required_items")
            if isinstance(boundary_items, list) and boundary_items:
                required_items.extend(
                    item.strip().casefold()
                    for item in boundary_items
                    if isinstance(item, str) and item.strip()
                )
                continue
            actions = boundary.get("actions")
            if not isinstance(actions, list):
                continue
            for action in actions:
                if not isinstance(action, str):
                    continue
                words = action.strip().split(maxsplit=1)
                if len(words) == 2 and words[0].casefold() in {"get", "take"}:
                    required_items.append(words[1].strip().casefold())
    if required_items:
        acquired_events: list[str] = []
        for event in events:
            if event.get("kind") != "game_event":
                continue
            payload = event.get("payload")
            data = payload.get("data") if isinstance(payload, dict) else None
            if (
                not isinstance(payload, dict)
                or payload.get("type") != "item_acquired"
                or not isinstance(data, dict)
            ):
                continue
            item = str(data.get("item") or "").casefold()
            if not item:
                continue
            try:
                quantity = int(data.get("quantity") or data.get("count") or 1)
            except (TypeError, ValueError):
                quantity = 1
            acquired_events.extend([item] * max(0, quantity))
        inventory_items = _nested_strings(final_state.get("inventory"))
        recorded_acquired_items = _nested_strings(
            final_state.get("acquired_items")
        )
        acquired = any(
            _required_items_match(required_items, evidence)
            for evidence in (
                acquired_events,
                inventory_items,
                recorded_acquired_items,
            )
        )
        checks.append(acquired)
    response_requirements = objective.get("required_command_responses")
    if "required_command_responses" in objective:
        checks.append(_required_command_responses_met(
            response_requirements, events,
        ))
    if "required_final_room_vnum" in objective:
        expected_room = str(objective.get("required_final_room_vnum") or "")
        final_room = str(final_state.get("room_vnum") or "")
        checks.append(bool(expected_room) and final_room == expected_room)
    if world_time_probe:
        awaiting_time_response = False
        time_observed = False
        time_output: list[str] = []
        for event in events:
            if event.get("kind") == "command":
                command = str(event.get("payload", {}).get("command", "")).strip().casefold()
                awaiting_time_response = command == "time"
                if awaiting_time_response:
                    time_output.clear()
            elif awaiting_time_response and event.get("kind") == "response":
                payload = event.get("payload")
                response = payload.get("text") if isinstance(payload, dict) else None
                if isinstance(response, str) and response.strip():
                    time_output.append(response)
                    combined = " ".join(time_output)
                    time_observed = (
                        re.search(
                            r"\bIt is \d+ o'clock (?:am|pm), Day of .+, "
                            r"\d+(?:st|nd|rd|th) of the Month of .+\.",
                            combined,
                            re.IGNORECASE,
                        ) is not None
                        and "dd was started at" in combined.casefold()
                        and "dd has been running for" in combined.casefold()
                    )
                    if time_observed:
                        break
        checks.append(time_observed)
    if any(check is False for check in checks):
        return "not_achieved"
    if checks and all(check is True for check in checks):
        return "achieved"
    return "unknown"


def _terminal_objective_failure_evidence(
    events: list[dict[str, Any]],
) -> list[str]:
    """Return explicit missing-objective evidence from a terminal policy state."""
    for event in reversed(events):
        if event.get("kind") != "state":
            continue
        payload = event.get("payload")
        if not isinstance(payload, dict):
            continue
        terminal_state = str(payload.get("state") or "").casefold()
        if terminal_state not in {"completed", "failed"}:
            continue
        reason = payload.get("fastwalk_abort_reason")
        if not isinstance(reason, str):
            continue
        normalized = " ".join(reason.casefold().split())
        if "field expedition did not acquire required item(s):" in normalized:
            return [reason.strip()]
        return []
    return []


def _quest_point_bounds(
    objective: dict[str, Any],
    initial_state: dict[str, Any],
    final_state: dict[str, Any],
    events: list[dict[str, Any]],
) -> tuple[int | None, int | None]:
    def parse(value: Any) -> int | None:
        if isinstance(value, bool):
            return None
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed >= 0 else None

    def state_total(state: dict[str, Any]) -> int | None:
        for key in ("total_quest_points", "total_points", "quest_points", "points"):
            parsed = parse(state.get(key))
            if parsed is not None:
                return parsed
        status = state.get("quest_status")
        if isinstance(status, dict):
            for key in ("total_points", "points"):
                parsed = parse(status.get(key))
                if parsed is not None:
                    return parsed
        return None

    observations: list[int] = []
    for event in events:
        if event.get("kind") != "game_event":
            continue
        payload = event.get("payload")
        if (
            not isinstance(payload, dict)
            or payload.get("type") != "quest_status_changed"
        ):
            continue
        data = payload.get("data")
        if not isinstance(data, dict):
            continue
        for key in ("total_points", "points"):
            observed = parse(data.get(key))
            if observed is not None:
                observations.append(observed)
                break

    initial = parse(objective.get("initial_total_quest_points"))
    if initial is None:
        initial = state_total(initial_state)
    if initial is None and observations:
        initial = observations[0]
    final = state_total(final_state)
    if final is None and observations:
        final = observations[-1]
    return initial, final


def _nested_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        stripped = value.lstrip()
        if stripped.startswith(("[", "{")):
            try:
                decoded = json.loads(value)
            except (TypeError, json.JSONDecodeError):
                pass
            else:
                if not isinstance(decoded, str):
                    return _nested_strings(decoded)
        return [value.casefold()]
    if isinstance(value, dict):
        description = next(
            (
                value[key]
                for key in ("short_desc", "description", "name", "item")
                if isinstance(value.get(key), str) and value[key].strip()
            ),
            None,
        )
        if description is not None:
            try:
                quantity = int(
                    value.get("quan")
                    or value.get("quantity")
                    or value.get("count")
                    or 1
                )
            except (TypeError, ValueError):
                quantity = 1
            return [description.casefold()] * max(0, quantity)
        return [text for nested in value.values() for text in _nested_strings(nested)]
    if isinstance(value, (list, tuple)):
        return [text for nested in value for text in _nested_strings(nested)]
    return []


def _required_items_match(required_items: list[str], evidence: list[str]) -> bool:
    """Match each required object to a distinct acquired/inventory entry."""
    candidates = [item.strip().casefold() for item in evidence if item.strip()]
    item_to_requirement: dict[int, int] = {}

    def assign(requirement_index: int, seen: set[int]) -> bool:
        required = required_items[requirement_index]
        for candidate_index, candidate in enumerate(candidates):
            if candidate_index in seen or not (
                required in candidate or candidate in required
            ):
                continue
            seen.add(candidate_index)
            previous = item_to_requirement.get(candidate_index)
            if previous is None or assign(previous, seen):
                item_to_requirement[candidate_index] = requirement_index
                return True
        return False

    return all(
        assign(index, set())
        for index, _required in sorted(
            enumerate(required_items), key=lambda pair: -len(pair[1])
        )
    )


def _required_command_responses_met(
    requirements: Any,
    events: list[dict[str, Any]],
) -> bool:
    if not isinstance(requirements, list) or not requirements:
        return False
    normalized: list[tuple[str, str]] = []
    for requirement in requirements:
        if not isinstance(requirement, dict):
            return False
        command = requirement.get("command")
        response = requirement.get("response_contains")
        if not isinstance(command, str) or not command.strip():
            return False
        if not isinstance(response, str) or not response.strip():
            return False
        normalized.append((command.strip().casefold(), response.strip().casefold()))

    observed = [False] * len(normalized)

    def record_response(command: str | None, parts: list[str]) -> None:
        if command is None or not parts:
            return
        combined = "".join(parts).casefold()
        for index, (expected_command, expected_response) in enumerate(normalized):
            if (
                not observed[index]
                and command == expected_command
                and expected_response in combined
            ):
                observed[index] = True

    pending_command: str | None = None
    response_parts: list[str] = []
    for event in events:
        if event.get("kind") == "command":
            record_response(pending_command, response_parts)
            payload = event.get("payload")
            command = payload.get("command") if isinstance(payload, dict) else None
            pending_command = (
                command.strip().casefold() if isinstance(command, str) else None
            )
            response_parts = []
        elif event.get("kind") == "response" and pending_command is not None:
            payload = event.get("payload")
            response = payload.get("text") if isinstance(payload, dict) else None
            if isinstance(response, str):
                response_parts.append(response)
    record_response(pending_command, response_parts)
    return all(observed)


def _safety_outcome(
    run: Any, final_state: dict[str, Any], game_event_counts: Counter[str],
) -> str:
    if game_event_counts["character_died"] or final_state.get("dead") is True:
        return "unsafe"
    if game_event_counts["experience_lost"] or final_state.get("xp_loss_observed"):
        return "loss"
    return "safe" if final_state and final_state.get("dead") is False else "unknown"


def _sum_activity_metrics(run_summaries: list[dict[str, Any]]) -> dict[str, float]:
    fields = (
        "productive_combat_seconds", "travel_seconds",
        "maintenance_seconds", "waiting_seconds",
    )
    totals = {field: 0.0 for field in fields}
    for run in run_summaries:
        activity = run.get("activity")
        if not isinstance(activity, dict):
            continue
        for field in fields:
            try:
                totals[field] += float(activity.get(field) or 0)
            except (TypeError, ValueError):
                continue
    return {key: round(value, 2) for key, value in totals.items()}


def _format_outcome_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "none"
    return ", ".join(
        f"{outcome} {count}" for outcome, count in sorted(counts.items())
    )


def _json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if not isinstance(value, str):
        return {}
    try:
        decoded = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    return dict(decoded) if isinstance(decoded, dict) else {}


def _change_row(name: str, change: dict[str, Any], *, resource: bool = False) -> str:
    initial = (
        _display_resource(change["initial"], change.get("initial_maximum"))
        if resource
        else _display(change["initial"])
    )
    final = (
        _display_resource(change["final"], change.get("final_maximum"))
        if resource
        else _display(change["final"])
    )
    return f"| {name} | {initial} | {final} | {_display(change['change'])} |"


def _display_resource(current: Any, maximum: Any) -> str:
    if current is None:
        return "-"
    return str(current) if maximum is None else f"{current}/{maximum}"


def _display(value: Any) -> str:
    return "-" if value is None else str(value)


def _format_duration(seconds: float | None) -> str:
    return "-" if seconds is None else f"{seconds:g} seconds"


def _format_identity(character: dict[str, Any]) -> str:
    if not character:
        return "-"
    parts = [
        str(character.get("name") or "unknown"),
        str(character.get("gender") or "unknown"),
        str(character.get("race") or "unknown"),
        str(character.get("class") or "unknown"),
    ]
    subclass = character.get("subclass")
    if subclass:
        parts[-1] = f"{parts[-1]} ({subclass})"
    return ", ".join(parts)


def _persona_lines(character: dict[str, Any]) -> list[str]:
    """Render optional persona metadata without changing legacy reports."""
    lines: list[str] = []
    for label, key in (
        ("Title", "title"),
        ("Description", "description"),
        ("Personality", "personality"),
    ):
        value = character.get(key)
        if value:
            lines.append(f"{label}: {value}")
    return lines


def _count_line(label: str, counts: dict[str, int]) -> str:
    values = ", ".join(f"{name}={count}" for name, count in counts.items())
    return f"{label}: {values or '-'}"
