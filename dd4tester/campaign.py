from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable

from .character import CharacterSpec, load_character_spec
from .fastwalks import route_named
from .progression import ProgressionPolicy, policy_for
from .runner import RunResult
from .scenario import load_yaml_mapping
from .starter import (
    FieldHuntStop,
    StarterBotRunner,
    _sellable_inventory_keyword,
    ambush_level_eight_hunt_stops,
    ambush_vile_goblin_hunt_stops,
    moria_sanctuary_potion_hunt_stops,
)
from .storage import RunStorage


SegmentRunner = Callable[[CharacterSpec, Path], Awaitable[RunResult]]
_MAINTENANCE_EXECUTIONS = {
    "restock",
    "sell-loot",
    "rearm-weapon",
    "buy-flight",
}
_ANSI_ESCAPE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


@dataclass(frozen=True)
class CampaignSpec:
    name: str
    character_profile: Path
    character: CharacterSpec
    target_level: int = 100
    max_segments: int = 100
    max_total_runtime: float = 86_400.0
    max_total_commands: int = 25_000
    max_stalled_segments: int = 3

    @property
    def database(self) -> Path:
        return self.character.database

    @classmethod
    def from_mapping(cls, data: dict[str, Any], *, path: Path) -> "CampaignSpec":
        profile_value = data.get("character_profile")
        if not profile_value:
            raise ValueError("character_profile is required")
        character_profile = Path(str(profile_value))
        if not character_profile.is_absolute():
            character_profile = path.parent / character_profile
        character_profile = character_profile.resolve()
        if not character_profile.exists():
            raise ValueError(f"character_profile does not exist: {character_profile}")

        character = load_character_spec(character_profile)
        name = str(data.get("name", character.name)).strip()
        if not name:
            raise ValueError("name must not be empty")
        target_level = int(data.get("target_level", 100))
        max_segments = int(data.get("max_segments", 100))
        max_total_runtime = float(data.get("max_total_runtime", 86_400))
        max_total_commands = int(data.get("max_total_commands", 25_000))
        max_stalled_segments = int(data.get("max_stalled_segments", 3))

        if not 2 <= target_level <= 100:
            raise ValueError("target_level must be between 2 and 100")
        if max_segments < 1:
            raise ValueError("max_segments must be positive")
        if max_total_runtime <= 0:
            raise ValueError("max_total_runtime must be positive")
        if max_total_commands < 1:
            raise ValueError("max_total_commands must be positive")
        if max_stalled_segments < 1:
            raise ValueError("max_stalled_segments must be positive")

        return cls(
            name=name,
            character_profile=character_profile,
            character=character,
            target_level=target_level,
            max_segments=max_segments,
            max_total_runtime=max_total_runtime,
            max_total_commands=max_total_commands,
            max_stalled_segments=max_stalled_segments,
        )


@dataclass(frozen=True)
class CampaignResult:
    campaign_id: int
    status: str
    checkpoint_id: int | None
    message: str | None
    state: dict[str, Any]

    @property
    def ready_for_next_segment(self) -> bool:
        return bool(
            self.status == "blocked"
            and self.message
            and "checkpointed for the next verified segment." in self.message
        )


class CampaignRunner:
    """Run verified policy segments with durable checkpoints and aggregate limits."""

    def __init__(
        self,
        spec: CampaignSpec,
        config_path: Path,
        *,
        segment_runner: SegmentRunner | None = None,
        force_new: bool = False,
    ) -> None:
        self.spec = spec
        self.config_path = config_path.resolve()
        self.segment_runner = segment_runner
        self.force_new = force_new
        self._historical_large_sack = False
        self._boot_kill_counts: Counter[str] = Counter()

    async def run(self) -> CampaignResult:
        with RunStorage(self.spec.database) as storage:
            self._historical_large_sack = storage.character_has_acquired_item(
                self.spec.character.name,
                "large sack",
            )
            boot_id = storage.latest_boot_id()
            if boot_id is not None:
                self._boot_kill_counts.update(
                    str(row["mob_name"])
                    for row in storage.list_mob_kills(
                        self.spec.character.name,
                        boot_id=boot_id,
                    )
                )
            campaign_id, state = self._open_campaign(storage)
            checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)
            checkpoint_id = int(checkpoint["id"]) if checkpoint is not None else None

            if _level(state) >= self.spec.target_level:
                storage.finish_campaign(campaign_id, status="success")
                return CampaignResult(
                    campaign_id,
                    "success",
                    checkpoint_id,
                    f"Target level {self.spec.target_level} already reached.",
                    state,
                )

            policy = self._policy_for_state(state)
            stalled = int(state.get("campaign_stalled_segments", 0))
            if (
                stalled >= self.spec.max_stalled_segments
                and policy.execution not in _MAINTENANCE_EXECUTIONS
            ):
                message = f"Campaign stalled for {stalled} completed segment(s)."
                checkpoint_id = self._checkpoint(
                    storage,
                    campaign_id,
                    checkpoint_id,
                    phase=policy.policy_id,
                    reason="stalled",
                    state=state,
                )
                storage.finish_campaign(campaign_id, status="blocked", error=message)
                return CampaignResult(campaign_id, "blocked", checkpoint_id, message, state)

            totals = storage.campaign_totals(campaign_id)
            budget_failure = _budget_failure(self.spec, totals)
            if budget_failure:
                checkpoint_id = self._checkpoint(
                    storage,
                    campaign_id,
                    checkpoint_id,
                    phase=policy.policy_id,
                    reason="budget_exhausted",
                    state=state,
                )
                storage.finish_campaign(campaign_id, status="blocked", error=budget_failure)
                return CampaignResult(campaign_id, "blocked", checkpoint_id, budget_failure, state)

            if not policy.executable:
                message = policy.blocks_message(self.spec.character.character_class)
                checkpoint_id = self._checkpoint(
                    storage,
                    campaign_id,
                    checkpoint_id,
                    phase=policy.policy_id,
                    reason="awaiting_policy",
                    state=state,
                )
                storage.finish_campaign(campaign_id, status="blocked", error=message)
                return CampaignResult(campaign_id, "blocked", checkpoint_id, message, state)

            return await self._run_starter(
                storage,
                campaign_id,
                state,
                totals,
                policy,
            )

    def _policy_for_state(self, state: dict[str, Any]) -> ProgressionPolicy:
        return policy_for(
            _level(state),
            self.spec.character.character_class,
            has_large_sack=(
                self._historical_large_sack
                or _state_has_item(state.get("inventory"), "large sack")
            ),
            has_sellable_loot=(
                _has_campaign_sellable_loot(state)
            ),
            has_food=(
                "inventory" not in state
                or _state_has_item(state.get("inventory"), "pie")
            ),
            has_weapon=bool(state.get("campaign_has_weapon", True)),
            has_sanctuary_potion=(
                int(
                    dict(state.get("combat_pouch_potions") or {}).get(
                        "purple", 0
                    )
                )
                > 0
                or _state_has_item(state.get("inventory"), "purple potion")
            ),
            has_flight=_state_has_active_affect(state.get("affects"), "fly"),
            can_attempt_flight_purchase=_state_copper_value(state) >= 90,
            flight_purchase_failed=bool(state.get("magic_shop_purchase_failed")),
            boot_kill_counts=self._boot_kill_counts,
            stalled_segments=int(state.get("campaign_stalled_segments", 0)),
        )

    def _open_campaign(self, storage: RunStorage) -> tuple[int, dict[str, Any]]:
        campaign = None if self.force_new else storage.get_latest_campaign_for_config(
            self.config_path
        )
        if campaign is None:
            campaign_id = storage.create_campaign(
                name=self.spec.name,
                config_path=self.config_path,
                character_profile_path=self.spec.character_profile,
                target_level=self.spec.target_level,
            )
            return campaign_id, storage.get_latest_character_state(
                self.spec.character.name
            ) or {}

        campaign_id = int(campaign["id"])
        checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)
        checkpoint_state = _checkpoint_state(checkpoint)
        live_state = storage.get_latest_character_state(self.spec.character.name)
        state = _newer_progress_state(checkpoint_state, live_state)
        if campaign["status"] == "success":
            return campaign_id, state
        storage.resume_campaign(campaign_id)
        return campaign_id, state

    async def _run_starter(
        self,
        storage: RunStorage,
        campaign_id: int,
        state: dict[str, Any],
        totals: Any,
        policy: ProgressionPolicy,
    ) -> CampaignResult:
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase=policy.policy_id,
            start_state=state,
        )
        adjusted_character = replace(
            self.spec.character,
            max_commands=min(
                self.spec.character.max_commands,
                self.spec.max_total_commands - int(totals["command_count"]),
            ),
            max_runtime=min(
                self.spec.character.max_runtime,
                self.spec.max_total_runtime - float(totals["duration_seconds"]),
            ),
        )
        try:
            if self.segment_runner is not None:
                result = await self.segment_runner(adjusted_character, self.spec.character_profile)
            else:
                result = await _run_policy_segment(
                    adjusted_character, self.spec.character_profile, policy
                )
        except Exception as exc:
            message = f"{policy.policy_id} segment failed: {exc}"
            storage.finish_campaign_segment(
                segment_id,
                status="failed",
                run_id=None,
                end_state=state,
                command_count=None,
                duration_seconds=None,
                error=message,
            )
            checkpoint_id = self._checkpoint(
                storage,
                campaign_id,
                segment_id,
                phase=policy.policy_id,
                reason="segment_failed",
                state=state,
            )
            storage.finish_campaign(campaign_id, status="failed", error=message)
            return CampaignResult(campaign_id, "failed", checkpoint_id, message, state)

        command_count = storage.count_events(result.run_id, kind="command")
        duration_seconds = _run_duration(storage.get_run(result.run_id))
        end_state = result.final_state
        if result.status != "success":
            message = f"starter segment returned status {result.status}"
            storage.finish_campaign_segment(
                segment_id,
                status="failed",
                run_id=result.run_id,
                end_state=end_state,
                command_count=command_count,
                duration_seconds=duration_seconds,
                error=message,
            )
            checkpoint_id = self._checkpoint(
                storage,
                campaign_id,
                segment_id,
                phase=policy.policy_id,
                reason="segment_failed",
                state=end_state,
                run_id=result.run_id,
            )
            storage.finish_campaign(campaign_id, status="failed", error=message)
            return CampaignResult(campaign_id, "failed", checkpoint_id, message, end_state)

        storage.finish_campaign_segment(
            segment_id,
            status=result.status,
            run_id=result.run_id,
            end_state=end_state,
            command_count=command_count,
            duration_seconds=duration_seconds,
        )
        stalled = (
            0
            if policy.execution in _MAINTENANCE_EXECUTIONS
            else _stalled_count(
                state,
                end_state,
                storage.get_latest_campaign_checkpoint(campaign_id),
            )
        )
        checkpoint_state = {
            **end_state,
            "campaign_stalled_segments": stalled,
            "campaign_has_weapon": (
                bool(state.get("campaign_has_weapon", True))
                or policy.execution == "rearm-weapon"
            ),
        }
        checkpoint_id = self._checkpoint(
            storage,
            campaign_id,
            segment_id,
            phase=policy.policy_id,
            reason="segment_complete",
            state=checkpoint_state,
            run_id=result.run_id,
        )

        if _level(end_state) >= self.spec.target_level:
            storage.finish_campaign(campaign_id, status="success")
            return CampaignResult(
                campaign_id,
                "success",
                checkpoint_id,
                f"Target level {self.spec.target_level} reached.",
                end_state,
            )

        if stalled >= self.spec.max_stalled_segments:
            message = f"Campaign stalled for {stalled} completed segment(s)."
            storage.finish_campaign(campaign_id, status="blocked", error=message)
            return CampaignResult(campaign_id, "blocked", checkpoint_id, message, end_state)

        next_policy = self._policy_for_state(end_state)
        if next_policy.executable:
            message = (
                f"{policy.policy_id} segment completed at level {_level(end_state)}. "
                "Campaign checkpointed for the next verified segment."
            )
        else:
            message = next_policy.blocks_message(self.spec.character.character_class)
        storage.finish_campaign(campaign_id, status="blocked", error=message)
        return CampaignResult(campaign_id, "blocked", checkpoint_id, message, end_state)

    def _checkpoint(
        self,
        storage: RunStorage,
        campaign_id: int,
        segment_id: int | None,
        *,
        phase: str,
        reason: str,
        state: dict[str, Any],
        run_id: int | None = None,
    ) -> int:
        return storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=segment_id,
            run_id=run_id,
            phase=phase,
            reason=reason,
            state=state,
        )


async def run_campaign_file(
    path: str | Path,
    *,
    force_new: bool = False,
    segments: int = 1,
) -> CampaignResult:
    if segments < 1:
        raise ValueError("segments must be positive")
    config_path = Path(path)
    spec = load_campaign_spec(config_path)
    result = await CampaignRunner(spec, config_path, force_new=force_new).run()
    for _ in range(1, segments):
        if not result.ready_for_next_segment:
            break
        result = await CampaignRunner(spec, config_path).run()
    return result


def load_campaign_spec(path: str | Path) -> CampaignSpec:
    config_path = Path(path)
    return CampaignSpec.from_mapping(load_yaml_mapping(config_path), path=config_path)


async def _run_policy_segment(
    spec: CharacterSpec,
    profile_path: Path,
    policy: ProgressionPolicy,
) -> RunResult:
    if policy.execution == "starter":
        return await StarterBotRunner(spec, profile_path).run()
    if policy.execution == "arena":
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 10,
            arena_kill_limit=policy.segment_kill_limit,
        ).run()
    if policy.execution == "sell-loot":
        return await StarterBotRunner(
            spec,
            profile_path,
            liquidate_loot=True,
        ).run()
    if policy.execution == "restock":
        return await StarterBotRunner(
            spec,
            profile_path,
            city_restock=True,
        ).run()
    if policy.execution == "rearm-weapon":
        return await StarterBotRunner(
            spec,
            profile_path,
            city_rearm=True,
        ).run()
    if policy.execution == "buy-flight":
        return await StarterBotRunner(
            spec,
            profile_path,
            magic_shop_research=True,
            magic_shop_buy_fly=True,
        ).run()
    if policy.execution in {
        "ambush-war-dog-hunt",
        "ambush-hunt",
        "ambush-vile-hunt",
    }:
        if policy.execution == "ambush-war-dog-hunt":
            hunt_stops = ambush_level_eight_hunt_stops()
        elif policy.execution == "ambush-vile-hunt":
            hunt_stops = ambush_vile_goblin_hunt_stops()
        else:
            hunt_stops = ambush_level_eight_hunt_stops()
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 10,
            fastwalk_route=route_named("ambush"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=hunt_stops,
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=(
                policy.execution in {"ambush-hunt", "ambush-vile-hunt"}
            ),
            fastwalk_require_invisibility=True,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
        ).run()
    if policy.execution == "midennir-hunt":
        use_level_eight_loadout = (policy.minimum_level or 0) >= 8
        circuit_routes = (
            (),
            ("east",),
            ("south",),
            ("east",),
            ("south",),
            ("west",),
            ("west",),
            ("south",),
            ("west",),
            ("south",),
            ("south",),
            ("north", "north", "north"),
            ("north",),
            ("east",),
            ("north",),
        )
        hunt_stops = tuple(
            FieldHuntStop(route, "goblin")
            for route in circuit_routes
        )
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 10,
            fastwalk_route=route_named("ambush"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=hunt_stops,
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=not use_level_eight_loadout,
            fastwalk_require_invisibility=use_level_eight_loadout,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
        ).run()
    if policy.execution == "midennir-sack":
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 10,
            fastwalk_route=route_named("ambush"),
            fastwalk_origin_actions=("drop all.piping", "drop cap"),
            vault_stow_items=(
                "sleeves",
                "vest",
                "cape",
                "belt",
                "bracer",
                "guards",
            ),
            vault_required_free_weight=60,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=True,
            fastwalk_hunt_stops=(
                FieldHuntStop(
                    (
                        "west",
                        "south",
                        "south",
                        "west",
                        "south",
                        "west",
                        "south",
                        "south",
                        "east",
                        "south",
                        "south",
                        "open east",
                        "east",
                        "east",
                    ),
                    actions=("get sack", "inventory"),
                    required_items=("large sack",),
                ),
            ),
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
        ).run()
    if policy.execution == "moria-circuit":
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 10,
            fastwalk_route=route_named("moria"),
            fastwalk_hunt_stops=(
                FieldHuntStop(
                    (
                        "west",
                        "west",
                        "north",
                        "west",
                        "south",
                        "east",
                        "south",
                    ),
                    "hobgoblin",
                ),
                FieldHuntStop(("east",), "centipede"),
                FieldHuntStop((), "hobgoblin"),
                FieldHuntStop(("west", "north", "west"), "large orc"),
                FieldHuntStop((), "orc"),
            ),
        ).run()
    if policy.execution == "moria-sanctuary-hunt":
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 10,
            fastwalk_route=route_named("moria"),
            fastwalk_hunt_stops=moria_sanctuary_potion_hunt_stops(),
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=True,
            fastwalk_kill_limit=policy.segment_kill_limit,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
        ).run()
    raise ValueError(f"unsupported executable policy {policy.policy_id}")


def _checkpoint_state(checkpoint: Any) -> dict[str, Any]:
    if checkpoint is None:
        return {}
    return dict(json.loads(checkpoint["state_json"]))


def _level(state: dict[str, Any]) -> int:
    level = state.get("level")
    return int(level) if isinstance(level, (int, float)) else 0


def _newer_progress_state(
    checkpoint: dict[str, Any],
    live: dict[str, Any] | None,
) -> dict[str, Any]:
    if not live:
        return checkpoint
    checkpoint_progress = (_level(checkpoint), _numeric_progress(checkpoint, "xp"))
    live_progress = (_level(live), _numeric_progress(live, "xp"))
    return {**checkpoint, **live} if live_progress >= checkpoint_progress else checkpoint


def _numeric_progress(state: dict[str, Any], key: str) -> int:
    value = state.get(key)
    return int(value) if isinstance(value, (int, float)) else 0


def _state_has_item(value: Any, item_name: str) -> bool:
    target = item_name.casefold()
    if isinstance(value, str):
        try:
            decoded = json.loads(_ANSI_ESCAPE.sub("", value))
        except json.JSONDecodeError:
            return target in value.casefold()
        return _state_has_item(decoded, item_name)
    if isinstance(value, dict):
        for key in ("short_desc", "name", "item"):
            description = value.get(key)
            if isinstance(description, str) and target in description.casefold():
                return True
        return any(_state_has_item(item, item_name) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_state_has_item(item, item_name) for item in value)
    return False


def _state_item_count(value: Any, item_name: str) -> int:
    target = item_name.casefold()
    if isinstance(value, str):
        try:
            decoded = json.loads(_ANSI_ESCAPE.sub("", value))
        except json.JSONDecodeError:
            return int(target in value.casefold())
        return _state_item_count(decoded, item_name)
    if isinstance(value, dict):
        description = next(
            (
                value[key]
                for key in ("short_desc", "name", "item")
                if isinstance(value.get(key), str)
            ),
            None,
        )
        if description is not None and target in description.casefold():
            quantity = value.get("quan", 1)
            try:
                return max(1, int(quantity))
            except (TypeError, ValueError):
                return 1
        return sum(_state_item_count(item, item_name) for item in value.values())
    if isinstance(value, (list, tuple)):
        return sum(_state_item_count(item, item_name) for item in value)
    return 0


def _state_has_active_affect(value: Any, affect_name: str) -> bool:
    target = affect_name.casefold()
    if isinstance(value, str):
        try:
            decoded = json.loads(_ANSI_ESCAPE.sub("", value))
        except json.JSONDecodeError:
            return target in value.casefold()
        return _state_has_active_affect(decoded, affect_name)
    if isinstance(value, dict):
        name = value.get("name")
        if isinstance(name, str) and target == name.casefold():
            duration = value.get("duration")
            try:
                return duration is None or int(duration) > 0
            except (TypeError, ValueError):
                return True
        return any(
            _state_has_active_affect(item, affect_name)
            for item in value.values()
        )
    if isinstance(value, (list, tuple)):
        return any(_state_has_active_affect(item, affect_name) for item in value)
    return False


def _state_copper_value(state: dict[str, Any]) -> int:
    currencies = state.get("currencies")
    source = currencies if isinstance(currencies, dict) else state

    def amount(name: str) -> int:
        value = source.get(name, 0)
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return 0

    return (
        amount("platinum") * 1_000
        + amount("gold") * 100
        + amount("silver") * 10
        + amount("copper")
    )


def _has_campaign_sellable_loot(state: dict[str, Any]) -> bool:
    keyword = _sellable_inventory_keyword(state.get("inventory"))
    if keyword is None:
        return False
    if keyword != "collar":
        return True
    if _state_item_count(state.get("inventory"), "war dog collar") <= 2:
        return False
    stats = state.get("stats")
    if not isinstance(stats, dict):
        return False
    carry_weight = stats.get("carry_wt")
    maximum_weight = stats.get("maxcarry_wt")
    if not isinstance(carry_weight, (int, float)):
        return False
    if not isinstance(maximum_weight, (int, float)) or maximum_weight <= 0:
        return False
    return carry_weight / maximum_weight >= 0.85


def _budget_failure(spec: CampaignSpec, totals: Any) -> str | None:
    if int(totals["segment_count"]) >= spec.max_segments:
        return f"Campaign exceeded its {spec.max_segments} segment budget."
    if int(totals["command_count"]) >= spec.max_total_commands:
        return f"Campaign exceeded its {spec.max_total_commands} command budget."
    if float(totals["duration_seconds"]) >= spec.max_total_runtime:
        return f"Campaign exceeded its {spec.max_total_runtime:g} second runtime budget."
    return None


def _stalled_count(
    before: dict[str, Any],
    after: dict[str, Any],
    checkpoint: Any,
) -> int:
    previous = _checkpoint_state(checkpoint)
    previous_stalled = int(previous.get("campaign_stalled_segments", 0))
    if _level(after) > _level(before):
        return 0
    before_xp = before.get("xp")
    after_xp = after.get("xp")
    if isinstance(before_xp, (int, float)) and isinstance(after_xp, (int, float)):
        if after_xp > before_xp:
            return 0
    if not before and _level(after) > 0:
        return 0
    return previous_stalled + 1


def _run_duration(run: Any) -> float:
    if run is None or not run["finished_at"]:
        return 0.0
    try:
        elapsed = datetime.fromisoformat(run["finished_at"]) - datetime.fromisoformat(
            run["started_at"]
        )
    except ValueError:
        return 0.0
    return max(0.0, elapsed.total_seconds())
