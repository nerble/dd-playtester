"""Read-only trace of one real checkpoint's source-hunt selection."""

from __future__ import annotations

import argparse
import ast
import asyncio
import cProfile
import json
import pstats
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import dd4tester.campaign as campaign
from dd4tester.source_paths import source_directory_context
from dd4tester.storage import RunStorage


async def explain(config: Path, checkpoint: int, seconds: float, *, trace_rejections: bool = False,
                  full_policy: bool = False) -> dict:
    runner = campaign.CampaignRunner(campaign.load_campaign_spec(config), config)
    with source_directory_context(runner.source_directory, live_deployment=True):
        runner._ensure_gear_catalog()
        with RunStorage(runner.spec.database, read_only=True) as storage:
            row = storage.connection.execute(
                "SELECT campaign_id, state_json FROM campaign_checkpoints WHERE id = ?",
                (checkpoint,),
            ).fetchone()
            if row is None:
                raise ValueError(f"checkpoint {checkpoint} does not exist")
            state = json.loads(row["state_json"])
            if str(state.get("name", "")).casefold() != runner.spec.character.name.casefold():
                raise ValueError("checkpoint character does not match the campaign profile")
            runner._boot_id = state.get("world_boot_id")
            runner._campaign_policy_storage = storage
            runner._campaign_policy_campaign_id = row["campaign_id"]
            runner._campaign_policy_segments = campaign._runtime_campaign_segments(storage, row["campaign_id"])
            runner._live_reconnect_requires_flight_revalidation = full_policy
            runner._policy_xp_deltas = campaign._campaign_policy_xp_deltas(
                runner._campaign_policy_segments, storage=storage,
            )
            for kill in storage.list_mob_kills(state["name"], boot_id=runner._boot_id):
                runner._boot_kill_counts.update([str(kill["mob_name"])])
                if kill["source_mobile_vnum"] is None:
                    continue
                vnum, xp = int(kill["source_mobile_vnum"]), int(kill["xp_gained"] or 0)
                runner._boot_source_kill_counts.update([vnum])
                runner._boot_source_latest_xp[vnum] = xp
                runner._boot_source_best_xp[vnum] = max(runner._boot_source_best_xp.get(vnum, 0), xp)
            function = campaign._SOURCE_RANKED_HUNT_CANDIDATE_UNCACHED
            source = Path(function.__code__.co_filename).read_text(encoding="utf-8")
            tree = ast.parse(source)
            node = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                        and n.lineno == function.__code__.co_firstlineno)
            continues = {n.lineno for n in ast.walk(node) if isinstance(n, ast.Continue)}
            lines = source.splitlines()
            rejected: dict[int, list[dict]] = {}
            core_results: list[dict] = []

            def trace(frame, event, value):
                if frame.f_code is not function.__code__:
                    return None
                if event == "line" and frame.f_lineno in continues:
                    candidate = frame.f_locals.get("candidate")
                    if candidate is not None:
                        rejected.setdefault(frame.f_lineno, []).append({
                            "mobile_vnum": candidate.mobile_vnum,
                            "target": candidate.target, "room_vnum": candidate.room_vnum,
                        })
                elif event == "return":
                    core_results.append({
                        "candidate_count": len(frame.f_locals.get("candidates", ())),
                        "selected": getattr(value, "target", None),
                    })
                return trace

            deadline = campaign._CAMPAIGN_PREPARATION_DEADLINE.set(asyncio.get_running_loop().time() + seconds)
            selector = campaign._CAMPAIGN_SOURCE_SELECTOR_CACHE.set({})
            gates = campaign._CAMPAIGN_SOURCE_GATE_CACHE.set({})
            previous_trace = sys.gettrace()
            profile = cProfile.Profile()
            if trace_rejections:
                sys.settrace(trace)
            profile.enable()
            try:
                selected = (runner._policy_for_state(state) if full_policy
                            else runner._select_source_ranked_candidate(state))
            finally:
                profile.disable()
                sys.settrace(previous_trace)
                campaign._CAMPAIGN_SOURCE_GATE_CACHE.reset(gates)
                campaign._CAMPAIGN_SOURCE_SELECTOR_CACHE.reset(selector)
                campaign._CAMPAIGN_PREPARATION_DEADLINE.reset(deadline)
            return {
                "checkpoint": checkpoint, "level": state.get("level"),
                "selected": getattr(selected, "target", None), "core_calls": core_results,
                "policy_id": getattr(selected, "policy_id", None),
                "execution": getattr(selected, "execution", None),
                "diagnosis": state.get("campaign_source_ranked_frontier_diagnosis"),
                "budget_exhausted": runner._source_selector_budget_exhausted,
                "costs": [{
                    "file": Path(key[0]).name, "line": key[1], "function": key[2],
                    "calls": value[1], "own_seconds": round(value[2], 3),
                    "cumulative_seconds": round(value[3], 3),
                } for key, value in sorted(pstats.Stats(profile).stats.items(),
                                          key=lambda pair: -pair[1][3])[:20]],
                "rejections": [{
                    "line": line, "count": len(items), "examples": items[:16],
                    "context": lines[max(0, line - 7):line],
                } for line, items in sorted(rejected.items(), key=lambda pair: -len(pair[1]))],
            }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--checkpoint", required=True, type=int)
    parser.add_argument("--seconds", type=float, default=50)
    parser.add_argument("--trace-rejections", action="store_true",
                        help="enable slower line tracing of exact rejection branches")
    parser.add_argument("--full-policy", action="store_true",
                        help="include campaign handoffs and fresh-connection flight checks")
    args = parser.parse_args()
    if not 0 < args.seconds <= 60:
        parser.error("--seconds must be greater than zero and at most 60")
    print(json.dumps(asyncio.run(explain(args.config, args.checkpoint, args.seconds,
                                      trace_rejections=args.trace_rejections,
                                      full_policy=args.full_policy)), indent=2))
