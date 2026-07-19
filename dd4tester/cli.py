from __future__ import annotations

import argparse
import asyncio
from collections import Counter
import json
import sys
from pathlib import Path
from typing import Any

from .campaign import run_campaign_file
from .character import load_character_spec
from .credentials import (
    DEFAULT_LOGIN_CREDENTIAL,
    configure_character_password,
    configure_login,
)
from .evidence import collect_run_evidence, render_evidence_json
from .fastwalks import FASTWALKS, routes_for_level
from .hunt_candidates import load_world_source, rank_hunt_candidates
from .prerequisites import known_skills, load_snapshot, requirements_for_skill
from .progression import policy_for
from .report import build_run_report, render_json, render_markdown
from .runner import run_scenario_file
from .starter import (
    run_arena_research_profile,
    run_guildmaster_research_profile,
    run_fastwalk_research_profile,
    run_magic_shop_research_profile,
    run_moria_research_profile,
    run_restock_profile,
    run_return_home_profile,
    run_resupply_profile,
    run_sell_loot_profile,
    run_starter_profile,
)
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

    arena_research_parser = subcommands.add_parser(
        "arena-research",
        help="run a bounded Mud School arena progression segment",
    )
    arena_research_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing level-2 character profile",
    )

    resupply_parser = subcommands.add_parser(
        "resupply",
        help="safely return a character from Limbo or the arena, eat, drink, save, and quit",
    )
    resupply_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing character YAML profile",
    )

    return_home_parser = subcommands.add_parser(
        "return-home",
        help="recall an interrupted character and return safely to its guild",
    )
    return_home_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing character YAML profile",
    )

    restock_parser = subcommands.add_parser(
        "restock",
        help="visit the Midgaard fountain and Bakery, then save and quit",
    )
    restock_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing character YAML profile",
    )
    sell_loot_parser = subcommands.add_parser(
        "sell-loot",
        help="sell carried weapons and armour through verified safe Midgaard shops",
    )
    sell_loot_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing character YAML profile",
    )
    guildmaster_parser = subcommands.add_parser(
        "guildmaster-research",
        help="visit the Midgaard Guildmaster and record available training",
    )
    guildmaster_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing mage character YAML profile",
    )
    magic_shop_parser = subcommands.add_parser(
        "magic-shop-research",
        help="visit the Midgaard Magic Shop and record stock without buying",
    )
    magic_shop_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing mage character YAML profile",
    )
    magic_shop_parser.add_argument(
        "--buy-fly",
        action="store_true",
        help="buy, use, and verify one light blue travel potion after listing stock",
    )
    fastwalk_parser = subcommands.add_parser(
        "fastwalk-research",
        help="verify an official recall-origin route without initiating combat",
    )
    fastwalk_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing character YAML profile",
    )
    fastwalk_parser.add_argument(
        "route",
        help="official route name, for example: moria",
    )
    fastwalk_parser.add_argument(
        "--exit",
        dest="explore_direction",
        choices=("north", "south", "east", "west", "up", "down"),
        help="inspect rooms through this endpoint exit, then return",
    )
    fastwalk_parser.add_argument(
        "--depth",
        type=int,
        default=1,
        help="maximum rooms to inspect through --exit, from 1 to 6, default: 1",
    )
    fastwalk_parser.add_argument(
        "--attack",
        dest="attack_target",
        help="attack one explicit target after the one-room inspection",
    )
    moria_parser = subcommands.add_parser(
        "moria-research",
        help="verify the safe Midgaard-to-Moria approach and return to the Mage Guild",
    )
    moria_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing character YAML profile",
    )
    moria_parser.add_argument(
        "--depth",
        type=int,
        default=0,
        help="number of additional northbound Moria trail rooms to inspect, default: 0",
    )

    fastwalks_parser = subcommands.add_parser(
        "show-fastwalks",
        help="list official recall-origin travel routes and their expanded commands",
    )
    fastwalks_parser.add_argument(
        "--level",
        type=int,
        help="only list routes whose suggested level band includes this level",
    )
    hunt_candidates_parser = subcommands.add_parser(
        "show-hunt-candidates",
        help="rank source-backed low-level hunt and loot candidates",
    )
    hunt_candidates_parser.add_argument("--level", type=int, required=True)
    hunt_candidates_parser.add_argument(
        "--character",
        default="Ararisa",
        help="character name used for current-reboot kill history, default: Ararisa",
    )
    hunt_candidates_parser.add_argument(
        "--source",
        type=Path,
        default=Path("runs/dd4-source/server/area"),
        help="path to the DD4 server area directory",
    )
    hunt_candidates_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path, default: {DEFAULT_DATABASE}",
    )
    hunt_candidates_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="maximum candidates to show, default: 20",
    )
    arena_research_parser.add_argument(
        "--target-level",
        type=int,
        default=3,
        help="bounded completion level from 3 to 10, default: 3",
    )
    arena_research_parser.add_argument(
        "--kill-limit",
        type=int,
        help="save and exit after this many confirmed arena kills",
    )

    configure_login_parser = subcommands.add_parser(
        "configure-login",
        help="store DD4 login credentials in the operating system credential manager",
    )
    configure_login_parser.add_argument(
        "--credential-name",
        default=DEFAULT_LOGIN_CREDENTIAL,
        help=f"stored login name, default: {DEFAULT_LOGIN_CREDENTIAL}",
    )

    configure_character_parser = subcommands.add_parser(
        "configure-character-password",
        help="store a character password in the operating system credential manager",
    )
    configure_character_parser.add_argument("profile", type=Path)
    configure_character_parser.add_argument(
        "--credential-name",
        help="override the credential name from the character profile",
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
    campaign_parser.add_argument(
        "--segments",
        type=int,
        default=1,
        help="run up to this many ready checkpoint segments, default: 1",
    )

    show_runs_parser = subcommands.add_parser("show-runs", help="list stored scenario runs")
    show_runs_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path, default: {DEFAULT_DATABASE}",
    )
    show_runs_parser.add_argument("--limit", type=int, default=20, help="maximum runs to show")

    recover_runs_parser = subcommands.add_parser(
        "recover-runs",
        help="mark orphaned running records as interrupted after their process has ended",
    )
    recover_runs_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path, default: {DEFAULT_DATABASE}",
    )
    recover_runs_parser.add_argument(
        "--reason",
        default="runner process ended before the run could finish",
        help="failure reason to record",
    )

    show_sales_parser = subcommands.add_parser(
        "show-sales",
        help="list recorded loot-sale proceeds for a character",
    )
    show_sales_parser.add_argument(
        "--character",
        default="Ararisa",
        help="character whose sales to show, default: Ararisa",
    )
    show_sales_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path, default: {DEFAULT_DATABASE}",
    )
    show_sales_parser.add_argument(
        "--limit", type=int, default=20, help="maximum sales to show"
    )

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

    show_prerequisites_parser = subcommands.add_parser(
        "show-prereqs",
        help="inspect DD4 skill prerequisites from the bundled server-source snapshot",
    )
    show_prerequisites_parser.add_argument("--class", dest="character_class", required=True)
    show_prerequisites_parser.add_argument("--skill")
    show_prerequisites_parser.add_argument(
        "--snapshot",
        type=Path,
        help="use a prerequisite snapshot JSON file instead of the bundled snapshot",
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

    if args.command == "arena-research":
        try:
            result = asyncio.run(
                run_arena_research_profile(
                    args.profile,
                    target_level=args.target_level,
                    kill_limit=args.kill_limit,
                )
            )
        except Exception as exc:
            print(f"Arena research failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "resupply":
        try:
            result = asyncio.run(run_resupply_profile(args.profile))
        except Exception as exc:
            print(f"Resupply run failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "return-home":
        try:
            result = asyncio.run(run_return_home_profile(args.profile))
        except Exception as exc:
            print(f"Return-home run failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "restock":
        try:
            result = asyncio.run(run_restock_profile(args.profile))
        except Exception as exc:
            print(f"Restock run failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "sell-loot":
        try:
            result = asyncio.run(run_sell_loot_profile(args.profile))
        except Exception as exc:
            print(f"Sell-loot run failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "guildmaster-research":
        try:
            result = asyncio.run(run_guildmaster_research_profile(args.profile))
        except Exception as exc:
            print(f"Guildmaster research failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "magic-shop-research":
        try:
            result = asyncio.run(
                run_magic_shop_research_profile(args.profile, buy_fly=args.buy_fly)
            )
        except Exception as exc:
            print(f"Magic Shop research failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "fastwalk-research":
        try:
            result = asyncio.run(
                run_fastwalk_research_profile(
                    args.profile,
                    args.route,
                    explore_direction=args.explore_direction,
                    explore_depth=args.depth,
                    attack_target=args.attack_target,
                )
            )
        except Exception as exc:
            print(f"Fastwalk research failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "moria-research":
        try:
            result = asyncio.run(
                run_moria_research_profile(args.profile, depth=args.depth)
            )
        except Exception as exc:
            print(f"Moria research failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "show-fastwalks":
        routes = routes_for_level(args.level) if args.level is not None else FASTWALKS
        print("name\tlevels\tnotation\tcommands")
        for route in routes:
            print(
                f"{route.name}\t{route.minimum_level}-{route.maximum_level}\t"
                f"{route.notation}\t{' ; '.join(route.commands)}"
            )
        return 0

    if args.command == "show-hunt-candidates":
        return show_hunt_candidates(
            args.source,
            level=args.level,
            character=args.character,
            database=args.database,
            limit=args.limit,
        )

    if args.command == "configure-login":
        try:
            configure_login(args.credential_name)
        except Exception as exc:
            print(f"Credential setup failed: {exc}", file=sys.stderr)
            return 1
        print(f"Stored login credential: {args.credential_name}")
        return 0

    if args.command == "configure-character-password":
        try:
            spec = load_character_spec(args.profile)
            credential_name = args.credential_name or spec.credential_name
            configure_character_password(credential_name)
        except Exception as exc:
            print(f"Credential setup failed: {exc}", file=sys.stderr)
            return 1
        print(f"Stored character password credential: {credential_name}")
        return 0

    if args.command == "campaign":
        try:
            result = asyncio.run(
                run_campaign_file(
                    args.config,
                    force_new=args.new,
                    segments=args.segments,
                )
            )
        except Exception as exc:
            print(f"Campaign failed: {exc}", file=sys.stderr)
            return 1
        print(f"Campaign {result.campaign_id} {result.status}")
        if result.message:
            print(f"Status: {result.message}")
        if result.checkpoint_id is not None:
            print(f"Checkpoint: {result.checkpoint_id}")
        print(f"Level: {result.state.get('level', '-')}")
        return 0 if result.status == "success" or result.ready_for_next_segment else 1

    if args.command == "show-runs":
        return show_runs(args.database, limit=args.limit)

    if args.command == "recover-runs":
        return recover_runs(args.database, reason=args.reason)

    if args.command == "show-sales":
        return show_sales(args.database, character=args.character, limit=args.limit)

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

    if args.command == "show-prereqs":
        return show_prereqs(
            args.character_class,
            skill=args.skill,
            snapshot=args.snapshot,
        )

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

    print("id\tstatus\tscenario\tboot_id\tstarted_at\tfinished_at\ttranscript")
    for run in runs:
        print(
            "\t".join(
                [
                    str(run["id"]),
                    run["status"],
                    run["scenario_name"],
                    run["boot_id"] or "-",
                    run["started_at"],
                    run["finished_at"] or "-",
                    run["transcript_path"] or "-",
                ]
            )
        )
    return 0


def recover_runs(database: Path, *, reason: str) -> int:
    if not database.exists():
        print(f"No run database found at {database.resolve()}", file=sys.stderr)
        return 1
    with RunStorage(database) as storage:
        recovered = storage.fail_interrupted_runs(reason=reason)
    print(f"Database: {database.resolve()}")
    print(f"Marked {recovered} interrupted run(s) as failed.")
    return 0


def show_sales(database: Path, *, character: str, limit: int) -> int:
    if limit < 1:
        print("--limit must be at least 1", file=sys.stderr)
        return 2
    if not database.exists():
        print(f"No run database found at {database.resolve()}", file=sys.stderr)
        return 1

    with RunStorage(database) as storage:
        sales = storage.list_loot_sales(character)

    print(f"Database: {database.resolve()}")
    print(f"Character: {character}")
    if not sales:
        print("No loot sales recorded.")
        return 0

    visible = sales[-limit:]
    print("id\trun\tboot\titem\tshop\tcoins\ttimestamp")
    for sale in visible:
        print(
            "\t".join(
                [
                    str(sale["id"]),
                    str(sale["run_id"]),
                    sale["boot_id"] or "-",
                    sale["item_description"],
                    sale["shop_name"],
                    str(sale["sold_coins"]),
                    sale["timestamp"],
                ]
            )
        )
    print(f"Total shown: {sum(sale['sold_coins'] for sale in visible)} coins")
    return 0


def show_hunt_candidates(
    source: Path,
    *,
    level: int,
    character: str,
    database: Path,
    limit: int,
) -> int:
    if level < 1:
        print("--level must be at least 1", file=sys.stderr)
        return 2
    if limit < 1:
        print("--limit must be at least 1", file=sys.stderr)
        return 2
    try:
        world = load_world_source(source)
    except (OSError, ValueError) as exc:
        print(f"Unable to load DD4 source: {exc}", file=sys.stderr)
        return 1

    boot_id: str | None = None
    kill_counts: Counter[str] = Counter()
    if database.exists():
        with RunStorage(database) as storage:
            boot_id = storage.latest_boot_id()
            if boot_id is not None:
                kill_counts.update(
                    row["mob_name"]
                    for row in storage.list_mob_kills(
                        character,
                        boot_id=boot_id,
                    )
                )
    candidates = rank_hunt_candidates(
        world,
        character_level=level,
        boot_kill_counts=kill_counts,
    )

    print(f"Source: {source.resolve()}")
    print(f"Character: {character}, level {level}")
    print(f"Current reboot: {boot_id or 'unknown'}")
    print(
        "status\tscore\tarea\ttarget\tlevel\troom\troute\troom_spawns\t"
        "instance_limit\tboot_kills\tloot\thazards"
    )
    for candidate in candidates[:limit]:
        loot = "; ".join(candidate.loot)
        if candidate.contained_coins:
            loot = "; ".join(
                value
                for value in (loot, f"{candidate.contained_coins} contained coins")
                if value
            )
        print(
            "\t".join(
                [
                    candidate.status,
                    f"{candidate.score:g}",
                    candidate.area_file,
                    candidate.target,
                    str(candidate.level),
                    f"{candidate.room_vnum} {candidate.room_name}",
                    ";".join(candidate.route),
                    str(candidate.room_spawn_count),
                    str(candidate.source_instance_limit),
                    str(candidate.boot_kills),
                    loot or "-",
                    "; ".join(candidate.hazards) or "-",
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


def show_prereqs(
    character_class: str,
    *,
    skill: str | None,
    snapshot: Path | None,
) -> int:
    try:
        source, entries = load_snapshot(snapshot)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"Could not load prerequisite snapshot: {exc}", file=sys.stderr)
        return 1

    class_skills = known_skills(entries, class_name=character_class)
    if not class_skills:
        print(f"No prerequisite definitions found for {character_class!r}.", file=sys.stderr)
        return 1

    print(f"Source: {source['repository']} @ {source['revision']}")
    if skill is None:
        print(f"Class: {character_class}")
        print(f"Skills with definitions: {len(class_skills)}")
        print("Skills: " + ", ".join(class_skills))
        return 0

    requirements = requirements_for_skill(
        entries,
        class_name=character_class,
        skill=skill,
    )
    if not requirements:
        print(
            f"No prerequisite definition found for {skill!r} in {character_class!r}.",
            file=sys.stderr,
        )
        return 1

    print(f"Class: {character_class}")
    print(f"Skill: {requirements[0].skill}")
    print("Requirements:")
    for requirement in requirements:
        print(f"- {requirement.prerequisite}: {requirement.minimum_percent}%")
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
