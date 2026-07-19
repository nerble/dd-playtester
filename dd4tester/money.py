"""Bounded, source-backed low-level money loops."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .character import load_character_spec
from .fastwalks import Fastwalk
from .hunt_candidates import HuntCandidate, load_world_source, rank_hunt_candidates
from .runner import RunResult
from .shops import safe_shop_for_item
from .starter import (
    StarterBotRunner,
    run_restock_profile,
    run_sell_loot_profile,
)
from .storage import RunStorage


DEFAULT_SOURCE_DIRECTORY = Path("runs/dd4-source/server/area")
_COMPACT_DIRECTIONS = {
    "north": "n",
    "east": "e",
    "south": "s",
    "west": "w",
    "up": "u",
    "down": "d",
}


@dataclass(frozen=True)
class MoneyLoopResult:
    hunt_runs: tuple[RunResult, ...]
    sale_run: RunResult
    restock_run: RunResult
    targets: tuple[str, ...]

    @property
    def run_ids(self) -> tuple[int, ...]:
        return (
            *(run.run_id for run in self.hunt_runs),
            self.sale_run.run_id,
            self.restock_run.run_id,
        )


def select_money_targets(
    candidates: list[HuntCandidate],
    *,
    trip_limit: int,
    area_file: str = "foundry.are",
) -> tuple[HuntCandidate, ...]:
    """Choose available low-risk targets while favoring varied sale keywords."""
    if trip_limit < 1:
        raise ValueError("trip_limit must be positive")

    available = [
        candidate
        for candidate in candidates
        if candidate.area_file == area_file
        and candidate.status != "reject"
        and any(safe_shop_for_item(item) is not None for item in candidate.loot)
    ]
    selected: list[HuntCandidate] = []
    seen_loot: set[str] = set()
    while available and len(selected) < trip_limit:
        candidate = max(
            available,
            key=lambda item: (
                len(set(item.loot) - seen_loot),
                item.score,
                -len(item.route),
            ),
        )
        selected.append(candidate)
        seen_loot.update(candidate.loot)
        available.remove(candidate)
    return tuple(selected)


def route_notation(commands: tuple[str, ...]) -> str:
    """Convert source graph commands into notation accepted by ``Fastwalk``."""
    return ";".join(_COMPACT_DIRECTIONS.get(command, command) for command in commands)


async def run_money_loop_profile(
    path: str | Path,
    *,
    character_level: int,
    trip_limit: int = 3,
    source_directory: Path = DEFAULT_SOURCE_DIRECTORY,
) -> MoneyLoopResult:
    """Hunt renewable drops, liquidate them safely, and replenish provisions."""
    if character_level < 1:
        raise ValueError("character_level must be at least 1")

    profile_path = Path(path)
    spec = load_character_spec(profile_path)
    with RunStorage(spec.database) as storage:
        boot_id = storage.latest_boot_id()
        kill_counts = Counter(
            row["mob_name"]
            for row in storage.list_mob_kills(spec.name, boot_id=boot_id)
        )

    world = load_world_source(source_directory)
    candidates = rank_hunt_candidates(
        world,
        character_level=character_level,
        boot_kill_counts=kill_counts,
    )
    targets = select_money_targets(candidates, trip_limit=trip_limit)
    if not targets:
        raise RuntimeError(
            "no available safe Foundry money targets remain for the current reboot"
        )

    hunt_runs: list[RunResult] = []
    confirmed_kills = 0
    for candidate in targets:
        route = Fastwalk(
            name=f"money {candidate.target_keyword}",
            minimum_level=1,
            maximum_level=character_level,
            notation=route_notation(candidate.route),
            recall_after_loot=True,
        )
        result = await StarterBotRunner(
            spec,
            profile_path,
            fastwalk_route=route,
            fastwalk_attack_target=candidate.target_keyword,
        ).run()
        hunt_runs.append(result)
        with RunStorage(spec.database) as storage:
            confirmed_kills += sum(
                int(row["run_id"]) == result.run_id
                for row in storage.list_mob_kills(spec.name)
            )

    if confirmed_kills == 0:
        raise RuntimeError(
            "money loop found no available targets; no sale or restock was attempted"
        )

    sale_run = await run_sell_loot_profile(profile_path)
    restock_run = await run_restock_profile(profile_path)
    return MoneyLoopResult(
        hunt_runs=tuple(hunt_runs),
        sale_run=sale_run,
        restock_run=restock_run,
        targets=tuple(candidate.target for candidate in targets),
    )
