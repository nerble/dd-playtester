from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from typing import Any

from .decisions import classify_decision
from .storage import RunStorage


def build_run_report(
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
    game_event_counts = Counter(
        str(event["payload"].get("type", "unknown")) for event in game_events
    )
    event_counts = Counter(event["kind"] for event in events)
    duration_seconds = _duration_seconds(run["started_at"], run["finished_at"])
    confirmed_kills = _completed_kills(events)
    sales = [dict(sale) for sale in storage.list_loot_sales_for_run(run_id)]

    progress = _progress_summary(
        initial_state,
        final_state,
        snapshots,
        game_event_counts,
        game_events,
        decisions,
        confirmed_kills,
        sales,
    )
    failures = _failures(run, game_event_counts)
    balance_signals = _balance_signals(progress, game_event_counts)
    commentary = _commentary(events, run["status"], run["error"], commentary_limit)

    return {
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
        "progress": progress,
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
        f"Status: **{run['status']}**",
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
        f"Loot sales: {_format_sales(progress['loot_sales'])}",
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
        "combat_starts": game_event_counts["combat_started"],
        "combat_decisions": sum(_is_combat_decision(decision) for decision in decisions),
        "confirmed_kills": confirmed_kills,
        "level_gains_observed": game_event_counts["level_gained"],
        "items_acquired": sum(_is_item_acquisition(event) for event in game_events),
        "quests_received": game_event_counts["quest_received"],
        "loot_sales": _sales_summary(sales),
    }


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

    combats = game_event_counts["combat_started"]
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
    limit: int,
) -> list[str]:
    comments: list[tuple[int, str]] = []
    seen: set[str] = set()
    for event in events:
        comment = _comment_for_event(event)
        if comment and comment[1] not in seen:
            comments.append(comment)
            seen.add(comment[1])

    ending = (
        "I completed the run successfully."
        if status == "success"
        else f"The run stopped: {error or status}."
    )
    return _select_commentary(comments, ending, limit)


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
    reason = event["payload"].get("reason")
    return isinstance(reason, str) and "fight" in reason.casefold()


def _is_item_acquisition(event: dict[str, Any]) -> bool:
    if event["payload"].get("type") != "item_acquired":
        return False
    data = event["payload"].get("data")
    if not isinstance(data, dict):
        return True
    item = data.get("item", data.get("name"))
    return not _is_experience_item(item)


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


def _format_confirmed_kills(kills: list[dict[str, Any]]) -> str:
    entries: list[str] = []
    for kill in kills:
        name = str(kill.get("mob_name", "unknown target"))
        xp = kill.get("xp_gained")
        entries.append(f"{name} (+{xp} XP)" if _is_number(xp) else name)
    return ", ".join(entries) or "none"


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


def _count_line(label: str, counts: dict[str, int]) -> str:
    values = ", ".join(f"{name}={count}" for name, count in counts.items())
    return f"{label}: {values or '-'}"
