from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from .campaign import run_campaign_file
from .evidence import collect_run_evidence, render_evidence_json
from .progression import policy_for
from .report import build_run_report, render_json, render_markdown
from .runner import run_scenario_file
from .starter import run_starter_profile
from .storage import RunStorage


DEFAULT_DATABASE = Path("runs/dd4tester.sqlite3")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m dd4tester")
    subcommands = parser.add_subparsers(dest="command", required=True)

    run_parser = subcommands.add_parser("run", help="run a YAML play-test scenario")
    run_parser.add_argument("scenario", type=Path, help="path to the scenario YAML file")

    starter_parser = subcommands.add_parser(
        "starter",
        help="create or resume a rule-based starter character",
    )
    starter_parser.add_argument(
        "profile",
        type=Path,
        help="path to the starter character YAML profile",
    )

    campaign_parser = subcommands.add_parser(
        "campaign",
        help="run or resume a checkpointed character campaign",
    )
    campaign_parser.add_argument(
        "config",
        type=Path,
        help="path to the campaign YAML configuration",
    )
    campaign_parser.add_argument(
        "--new",
        action="store_true",
        help="start a new campaign instead of resuming this configuration",
    )

    show_runs_parser = subcommands.add_parser("show-runs", help="list stored scenario runs")
    show_runs_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path, default: {DEFAULT_DATABASE}",
    )
    show_runs_parser.add_argument("--limit", type=int, default=20, help="maximum runs to show")

    show_transcript_parser = subcommands.add_parser(
        "show-transcript",
        help="show a transcript by run id or JSONL transcript path",
    )
    show_transcript_parser.add_argument("target", help="run id or transcript JSONL path")
    show_transcript_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path for run id lookup, default: {DEFAULT_DATABASE}",
    )
    show_transcript_parser.add_argument(
        "--raw",
        action="store_true",
        help="print raw JSONL instead of formatted events",
    )

    show_state_parser = subcommands.add_parser(
        "show-state",
        help="show the latest character state or snapshot history for a run",
    )
    show_state_parser.add_argument("run_id", type=int, help="stored run id")
    show_state_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path, default: {DEFAULT_DATABASE}",
    )
    show_state_parser.add_argument(
        "--history",
        action="store_true",
        help="list all state snapshot revisions instead of the latest state",
    )

    report_parser = subcommands.add_parser(
        "report",
        help="render a Markdown or JSON summary of a stored run",
    )
    report_parser.add_argument("run_id", type=int, help="stored run id")
    report_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path, default: {DEFAULT_DATABASE}",
    )
    report_parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="report format, default: markdown",
    )
    report_parser.add_argument(
        "--output",
        type=Path,
        help="write the report to this file instead of standard output",
    )
    report_parser.add_argument(
        "--commentary-limit",
        type=int,
        default=20,
        help="maximum representative commentary entries, default: 20",
    )

    show_campaign_parser = subcommands.add_parser(
        "show-campaign",
        help="show checkpoint and segment history for a campaign",
    )
    show_campaign_parser.add_argument("campaign_id", type=int, help="stored campaign id")
    show_campaign_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path, default: {DEFAULT_DATABASE}",
    )

    show_policies_parser = subcommands.add_parser(
        "show-policies",
        help="show the evidence and status for a class and level band",
    )
    show_policies_parser.add_argument("--level", type=int, required=True)
    show_policies_parser.add_argument(
        "--class",
        dest="character_class",
        required=True,
    )

    collect_evidence_parser = subcommands.add_parser(
        "collect-evidence",
        help="export a redaction-safe evidence record for a stored run",
    )
    collect_evidence_parser.add_argument("run_id", type=int, help="stored run id")
    collect_evidence_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path, default: {DEFAULT_DATABASE}",
    )
    collect_evidence_parser.add_argument(
        "--output",
        type=Path,
        help="write JSON evidence to this file instead of standard output",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        try:
            result = asyncio.run(run_scenario_file(args.scenario))
        except Exception as exc:
            print(f"Run failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "starter":
        try:
            result = asyncio.run(run_starter_profile(args.profile))
        except Exception as exc:
            print(f"Starter run failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "campaign":
        try:
            result = asyncio.run(run_campaign_file(args.config, force_new=args.new))
        except Exception as exc:
            print(f"Campaign failed: {exc}", file=sys.stderr)
            return 1
        print(f"Campaign {result.campaign_id} {result.status}")
        if result.message:
            print(f"Status: {result.message}")
        if result.checkpoint_id is not None:
            print(f"Checkpoint: {result.checkpoint_id}")
        print(f"Level: {result.state.get('level', '-')}")
        return 0 if result.status == "success" else 1

    if args.command == "show-runs":
        return show_runs(args.database, limit=args.limit)

    if args.command == "show-transcript":
        return show_transcript(args.target, database=args.database, raw=args.raw)

    if args.command == "show-state":
        return show_state(args.run_id, database=args.database, history=args.history)

    if args.command == "report":
        return show_report(
            args.run_id,
            database=args.database,
            report_format=args.format,
            output=args.output,
            commentary_limit=args.commentary_limit,
        )

    if args.command == "show-campaign":
        return show_campaign(args.campaign_id, database=args.database)

    if args.command == "show-policies":
        return show_policies(args.level, args.character_class)

    if args.command == "collect-evidence":
        return collect_evidence(args.run_id, database=args.database, output=args.output)

    parser.error(f"Unknown command: {args.command}")
    return 2


def show_runs(database: Path, *, limit: int) -> int:
    if limit < 1:
        print("--limit must be at least 1", file=sys.stderr)
        return 2
    if not database.exists():
        print(f"No run database found at {database.resolve()}", file=sys.stderr)
        return 1

    with RunStorage(database) as storage:
        runs = storage.list_runs(limit=limit)

    print(f"Database: {database.resolve()}")
    if not runs:
        print("No runs recorded.")
        return 0

    print("id\tstatus\tscenario\tstarted_at\tfinished_at\ttranscript")
    for run in runs:
        print(
            "\t".join(
                [
                    str(run["id"]),
                    run["status"],
                    run["scenario_name"],
                    run["started_at"],
                    run["finished_at"] or "-",
                    run["transcript_path"] or "-",
                ]
            )
        )
    return 0


def show_transcript(target: str, *, database: Path, raw: bool) -> int:
    transcript_path = _resolve_transcript_target(target, database)
    if transcript_path is None:
        return 1
    if not transcript_path.exists():
        print(f"No transcript found at {transcript_path.resolve()}", file=sys.stderr)
        return 1

    if not raw:
        print(f"Transcript: {transcript_path.resolve()}")
    with transcript_path.open(encoding="utf-8") as transcript:
        for line in transcript:
            if raw:
                print(line.rstrip())
                continue
            event = json.loads(line)
            payload = json.dumps(event.get("payload", {}), sort_keys=True)
            print(f"{event.get('timestamp', '-')}\t{event.get('kind', '-')}\t{payload}")
    return 0


def show_state(run_id: int, *, database: Path, history: bool) -> int:
    if run_id < 1:
        print("run_id must be at least 1", file=sys.stderr)
        return 2
    if not database.exists():
        print(f"No run database found at {database.resolve()}", file=sys.stderr)
        return 1

    with RunStorage(database) as storage:
        run = storage.get_run(run_id)
        snapshots = (
            storage.list_state_snapshots(run_id)
            if history
            else [storage.get_latest_state_snapshot(run_id)]
        )

    if run is None:
        print(f"No run with id {run_id} in {database.resolve()}", file=sys.stderr)
        return 1

    available = [snapshot for snapshot in snapshots if snapshot is not None]
    if not available:
        print(f"Run {run_id} has no character state snapshots.", file=sys.stderr)
        return 1

    print(f"Database: {database.resolve()}")
    if not history:
        snapshot = available[0]
        print(
            f"Run {run_id} state revision "
            f"{json.loads(snapshot['state_json'])['revision']} "
            f"at {snapshot['timestamp']} ({snapshot['reason']})"
        )
        print(json.dumps(json.loads(snapshot["state_json"]), indent=2, sort_keys=True))
        return 0

    print("snapshot\ttimestamp\trevision\treason\tlevel\thp\troom")
    for snapshot in available:
        state = json.loads(snapshot["state_json"])
        print(
            "\t".join(
                [
                    str(snapshot["id"]),
                    snapshot["timestamp"],
                    str(state["revision"]),
                    snapshot["reason"],
                    str(state.get("level") or "-"),
                    _resource(state.get("hp"), state.get("max_hp")),
                    state.get("room_name") or "-",
                ]
            )
        )
    return 0


def show_report(
    run_id: int,
    *,
    database: Path,
    report_format: str,
    output: Path | None,
    commentary_limit: int,
) -> int:
    if run_id < 1:
        print("run_id must be at least 1", file=sys.stderr)
        return 2
    if commentary_limit < 1:
        print("--commentary-limit must be at least 1", file=sys.stderr)
        return 2
    if not database.exists():
        print(f"No run database found at {database.resolve()}", file=sys.stderr)
        return 1

    try:
        with RunStorage(database) as storage:
            report = build_run_report(
                storage,
                run_id,
                commentary_limit=commentary_limit,
            )
    except LookupError:
        print(f"No run with id {run_id} in {database.resolve()}", file=sys.stderr)
        return 1

    rendered = render_json(report) if report_format == "json" else render_markdown(report)
    if output is None:
        print(rendered, end="")
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(f"Report: {output.resolve()}")
    return 0


def show_campaign(campaign_id: int, *, database: Path) -> int:
    if campaign_id < 1:
        print("campaign_id must be at least 1", file=sys.stderr)
        return 2
    if not database.exists():
        print(f"No run database found at {database.resolve()}", file=sys.stderr)
        return 1

    with RunStorage(database) as storage:
        campaign = storage.get_campaign(campaign_id)
        segments = storage.list_campaign_segments(campaign_id)
        checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)

    if campaign is None:
        print(f"No campaign with id {campaign_id} in {database.resolve()}", file=sys.stderr)
        return 1

    print(f"Database: {database.resolve()}")
    print(f"Campaign {campaign['id']}: {campaign['name']}")
    print(f"Status: {campaign['status']}")
    print(f"Target level: {campaign['target_level']}")
    print(f"Profile: {campaign['character_profile_path']}")
    if campaign["error"]:
        print(f"Reason: {campaign['error']}")
    if checkpoint is not None:
        state = json.loads(checkpoint["state_json"])
        print(
            f"Checkpoint {checkpoint['id']}: {checkpoint['phase']} "
            f"({checkpoint['reason']}), level {state.get('level', '-')}"
        )
    print("sequence\tphase\tstatus\trun\tcommands\tduration\terror")
    for segment in segments:
        print(
            "\t".join(
                [
                    str(segment["sequence"]),
                    segment["phase"],
                    segment["status"],
                    str(segment["run_id"] or "-"),
                    str(segment["command_count"] or 0),
                    _duration(segment["duration_seconds"]),
                    segment["error"] or "-",
                ]
            )
        )
    return 0


def show_policies(level: int, character_class: str) -> int:
    if level < 0 or level > 100:
        print("--level must be between 0 and 100", file=sys.stderr)
        return 2
    try:
        policy = policy_for(level, character_class)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2

    print(f"Policy: {policy.policy_id}")
    print(f"Level band: {policy.minimum_level}-{policy.maximum_level or 100}")
    print(f"Status: {policy.status}")
    print(f"Summary: {policy.summary}")
    print(f"Practice candidate: {policy.practice_skill or '-'}")
    print("Evidence:")
    if policy.evidence:
        for item in policy.evidence:
            print(f"- {item}")
    else:
        print("- None recorded.")
    return 0


def collect_evidence(run_id: int, *, database: Path, output: Path | None) -> int:
    if run_id < 1:
        print("run_id must be at least 1", file=sys.stderr)
        return 2
    if not database.exists():
        print(f"No run database found at {database.resolve()}", file=sys.stderr)
        return 1
    try:
        with RunStorage(database) as storage:
            rendered = render_evidence_json(collect_run_evidence(storage, run_id))
    except LookupError:
        print(f"No run with id {run_id} in {database.resolve()}", file=sys.stderr)
        return 1

    if output is None:
        print(rendered, end="")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(f"Evidence: {output.resolve()}")
    return 0


def _resolve_transcript_target(target: str, database: Path) -> Path | None:
    if not target.isdigit():
        return Path(target)

    if not database.exists():
        print(f"No run database found at {database.resolve()}", file=sys.stderr)
        return None

    run_id = int(target)
    with RunStorage(database) as storage:
        run = storage.get_run(run_id)

    if run is None:
        print(f"No run with id {run_id} in {database.resolve()}", file=sys.stderr)
        return None
    if not run["transcript_path"]:
        print(f"Run {run_id} has no transcript path recorded", file=sys.stderr)
        return None
    return Path(run["transcript_path"])


def _resource(current: Any, maximum: Any) -> str:
    if current is None:
        return "-"
    if maximum is None:
        return str(current)
    return f"{current}/{maximum}"


def _duration(value: float | None) -> str:
    return "-" if value is None else f"{value:g}s"
