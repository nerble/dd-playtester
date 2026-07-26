from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable

from .character import CharacterSpec, load_character_spec
from .equipment import (
    GearCatalog,
    is_capacity_infrastructure,
    item_category,
    item_keyword,
    load_gear_catalog,
    normalize_item_name,
    protects_from_sale,
)
from .fastwalks import route_named
from .progression import ProgressionPolicy, policy_for
from .runner import RunResult
from .scenario import load_yaml_mapping
from .starter import (
    FieldHuntStop,
    StarterBotRunner,
    _equipment_audit_descriptions,
    _equipment_audit_present,
    _equipment_empty_categories,
    _inventory_descriptions,
    _sellable_inventory_keyword,
    ambush_caster_level_eight_hunt_stops,
    ambush_level_eight_hunt_stops,
    ambush_martial_level_eight_hunt_stops,
    ambush_raider_hunt_stops,
    ambush_vile_goblin_hunt_stops,
    circus_freak_show_hunt_stops,
    cult_fanatic_research_stops,
    daycare_armed_guard_hunt_stops,
    daycare_armed_guard_hunt_route,
    daycare_nanny_hunt_route,
    daycare_nanny_hunt_stops,
    daycare_ring_hunt_route,
    daycare_ring_hunt_stops,
    foundry_body_gear_hunt_stops,
    foundry_level_six_hunt_stops,
    foundry_level_seven_hunt_stops,
    fleshmonger_guard_research_stops,
    gnome_hermit_hunt_route,
    gnome_hermit_hunt_stops,
    gnome_guard_hunt_stops,
    gnome_small_troll_hunt_stops,
    gremlin_waist_hunt_route,
    gremlin_waist_hunt_stops,
    midennir_mountain_goblin_hunt_stops,
    moria_level_eight_large_orc_hunt_stops,
    moria_level_seven_orc_hunt_stops,
    moria_sanctuary_potion_hunt_stops,
    shire_bull_hunt_route,
    shire_bull_hunt_stops,
    school_accessory_hunt_route,
    school_wrist_float_hunt_stops,
)
from .storage import RunStorage


SegmentRunner = Callable[[CharacterSpec, Path], Awaitable[RunResult]]
_MAINTENANCE_EXECUTIONS = {
    "restock",
    "sell-loot",
    "vault-spare-gear",
    "rearm-weapon",
    "outfit-basic-gear",
    "recover-basic-body",
    "recover-school-wrist-float",
    "recover-gremlin-waist",
    "recover-daycare-ring",
    "buy-flight",
}
_LIQUIDATION_BASELINE_KEY = "campaign_liquidation_baseline"
_CAMPAIGN_POLICY_REVISION = 27
_ANSI_ESCAPE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
_RECOVER_BASIC_BODY_REQUIRED_FREE_WEIGHT = 7
_RECOVER_SCHOOL_WRIST_FLOAT_REQUIRED_FREE_WEIGHT = 30
_RECOVER_GREMLIN_WAIST_REQUIRED_FREE_WEIGHT = 5
_RECOVER_DAYCARE_RING_REQUIRED_FREE_WEIGHT = 21
_BASIC_SHOP_CATEGORIES = frozenset(
    {"body", "head", "arms", "hands", "legs", "feet", "pouch"}
)
_MUD_SCHOOL_ACCESSORY_ROOMS = frozenset(
    {"3711", "3712", "3715", "3716", "3720", "3721", "3722", "3723", "3724", "3725"}
)


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


def _refresh_policy_revision(state: dict[str, Any]) -> dict[str, Any]:
    """Reset stale stall history once when the autonomous policy graph changes."""
    if state.get("campaign_policy_revision") == _CAMPAIGN_POLICY_REVISION:
        return state
    refreshed = {
        **state,
        "campaign_policy_revision": _CAMPAIGN_POLICY_REVISION,
        "campaign_stalled_segments": 0,
    }
    if int(state.get("campaign_policy_revision", 0)) < 20:
        refreshed.pop("campaign_body_gear_attempted_level", None)
    return refreshed


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
        self._policy_xp_deltas: dict[str, int] = {}
        self._gear_catalog: GearCatalog | None = None

    async def run(self) -> CampaignResult:
        with RunStorage(self.spec.database) as storage:
            source_directory = Path("runs/dd4-source/server/area")
            if self._gear_catalog is None and source_directory.is_dir():
                self._gear_catalog = load_gear_catalog(
                    str(source_directory.resolve())
                )
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
            state = _refresh_policy_revision(state)
            self._policy_xp_deltas = _campaign_policy_xp_deltas(
                storage.list_campaign_segments(campaign_id)
            )
            checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)
            checkpoint_id = int(checkpoint["id"]) if checkpoint is not None else None

            if _level(state) >= self.spec.target_level:
                if _level(_checkpoint_state(checkpoint)) < self.spec.target_level:
                    checkpoint_id = storage.record_campaign_checkpoint(
                        campaign_id,
                        segment_id=None,
                        run_id=None,
                        phase="target-complete",
                        reason="target_reconciled",
                        state=state,
                    )
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
        empty_categories = set(
            state.get("campaign_empty_equipment_categories") or ()
        )
        school_exit_required = (
            str(state.get("room_vnum", "")) in _MUD_SCHOOL_ACCESSORY_ROOMS
        )
        recovered_own_corpse = _has_own_corpse_recovery(
            state,
            self.spec.character.name,
        )
        outfit_attempted_this_level = (
            int(state.get("campaign_outfit_attempted_level", -1))
            == _level(state)
        )
        school_wrist_float_attempted_this_level = (
            int(state.get("campaign_school_wrist_float_attempted_level", -1))
            == _level(state)
        )
        gremlin_waist_attempted_this_level = (
            int(state.get("campaign_gremlin_waist_attempted_level", -1))
            == _level(state)
        )
        daycare_ring_attempted_this_level = (
            int(state.get("campaign_daycare_ring_attempted_level", -1))
            == _level(state)
        )
        vault_stow_items = _campaign_vault_stow_items(
            state,
            gear_catalog=self._gear_catalog,
        )
        can_retry_rejected_vault = (
            not state.get("vault_storage_rejected")
            or _has_oversized_capacity_stow_item(
                state,
                gear_catalog=self._gear_catalog,
                stow_items=vault_stow_items,
            )
        )
        return policy_for(
            _level(state),
            self.spec.character.character_class,
            subclass=self.spec.character.subclass,
            has_large_sack=(
                self._historical_large_sack
                or _state_has_item(state.get("inventory"), "large sack")
            ),
            has_sellable_loot=(
                not school_exit_required
                and
                not recovered_own_corpse
                and
                _has_campaign_sellable_loot(
                    state,
                    gear_catalog=self._gear_catalog,
                )
            ),
            needs_capacity_relief=bool(
                not school_exit_required
                and
                not recovered_own_corpse
                and
                can_retry_rejected_vault
                and
                vault_stow_items
            ),
            has_food=(
                school_exit_required
                or _has_campaign_food(
                    state,
                    gear_catalog=self._gear_catalog,
                )
            ),
            has_weapon=bool(
                school_exit_required
                or state.get("campaign_has_weapon", True)
            ),
            needs_basic_gear=bool(
                not school_exit_required
                and
                empty_categories & _BASIC_SHOP_CATEGORIES
            )
            and not outfit_attempted_this_level,
            needs_body_gear_recovery=(
                not school_exit_required
                and
                "body" in empty_categories
                and outfit_attempted_this_level
                and _has_campaign_free_weight(
                    state,
                    _RECOVER_BASIC_BODY_REQUIRED_FREE_WEIGHT,
                )
                and int(
                    state.get("campaign_body_gear_attempted_level", -1)
                )
                != _level(state)
            ),
            needs_school_wrist_float=bool(
                school_exit_required
                or (
                    empty_categories & {"wrist", "float"}
                    and _has_campaign_free_weight(
                        state,
                        _RECOVER_SCHOOL_WRIST_FLOAT_REQUIRED_FREE_WEIGHT,
                    )
                )
            )
            and (
                school_exit_required
                or not school_wrist_float_attempted_this_level
            ),
            needs_gremlin_waist=(
                "waist" in empty_categories
                and not gremlin_waist_attempted_this_level
                and _has_campaign_free_weight(
                    state,
                    _RECOVER_GREMLIN_WAIST_REQUIRED_FREE_WEIGHT,
                )
            ),
            needs_daycare_ring=(
                "finger" in empty_categories
                and not daycare_ring_attempted_this_level
                and _has_campaign_free_weight(
                    state,
                    _RECOVER_DAYCARE_RING_REQUIRED_FREE_WEIGHT,
                )
            ),
            has_sanctuary_potion=(
                int(
                    dict(state.get("combat_pouch_potions") or {}).get(
                        "purple", 0
                    )
                )
                > 0
                or _state_has_item(state.get("inventory"), "purple potion")
            ),
            has_flight=any(
                _state_has_active_affect(state.get("affects"), effect)
                for effect in ("fly", "levitation")
            ),
            can_attempt_flight_purchase=_state_copper_value(state) >= 90,
            flight_purchase_failed=bool(state.get("magic_shop_purchase_failed")),
            boot_kill_counts=self._boot_kill_counts,
            policy_xp_deltas=self._policy_xp_deltas,
            stalled_segments=int(state.get("campaign_stalled_segments", 0)),
            last_policy_id=(
                str(state["campaign_last_policy"])
                if state.get("campaign_last_policy")
                else None
            ),
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
        flight_purchase_failed = _campaign_flight_purchase_failed(
            storage,
            campaign_id,
        )
        if flight_purchase_failed is not None:
            state["magic_shop_purchase_failed"] = flight_purchase_failed
        if checkpoint is not None and "campaign_last_policy" not in state:
            state["campaign_last_policy"] = str(checkpoint["phase"])
        if (
            checkpoint is not None
            and checkpoint["run_id"] is not None
            and _run_has_unrecovered_weapon_loss(
                storage,
                int(checkpoint["run_id"]),
            )
        ):
            state["campaign_has_weapon"] = False
        if checkpoint is not None and checkpoint["run_id"] is not None:
            empty_categories = _run_equipment_empty_categories(
                storage,
                int(checkpoint["run_id"]),
            )
            if empty_categories is not None:
                state["campaign_empty_equipment_categories"] = sorted(
                    empty_categories
                )
            worn_equipment = _run_worn_equipment_descriptions(
                storage,
                int(checkpoint["run_id"]),
            )
            if worn_equipment is not None:
                state["campaign_worn_equipment"] = worn_equipment
        if (
            checkpoint is not None
            and checkpoint["phase"] == "liquidate-loot"
            and checkpoint["reason"] == "segment_complete"
            and _LIQUIDATION_BASELINE_KEY not in state
        ):
            state[_LIQUIDATION_BASELINE_KEY] = list(
                _campaign_liquidation_signature(
                    state,
                    gear_catalog=self._gear_catalog,
                )
            )
        if (
            campaign["status"] == "success"
            and _level(state) >= self.spec.target_level
        ):
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
                    adjusted_character,
                    self.spec.character_profile,
                    policy,
                    # The current practice listing is authoritative.  A character may
                    # earn another practice before the next bounded campaign segment.
                    practice_types_spent=frozenset(),
                    rejected_practice_skills=_campaign_rejected_practice_skills(
                        storage,
                        campaign_id,
                        level=_level(state),
                    ),
                    vault_stow_items=(
                        _campaign_vault_stow_items(
                            state,
                            gear_catalog=self._gear_catalog,
                        )
                        if policy.execution == "vault-spare-gear"
                        else ()
                    ),
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
        end_state = _campaign_segment_end_state(
            state,
            result.final_state,
            execution=policy.execution,
        )
        empty_categories = _run_equipment_empty_categories(storage, result.run_id)
        if empty_categories is not None:
            end_state["campaign_empty_equipment_categories"] = sorted(
                empty_categories
            )
        if policy.execution == "outfit-basic-gear":
            end_state["campaign_outfit_attempted_level"] = _level(end_state)
        if policy.execution == "recover-basic-body":
            end_state["campaign_body_gear_attempted_level"] = _level(end_state)
        if (
            policy.execution == "recover-school-wrist-float"
            and not (
                set(end_state.get("campaign_empty_equipment_categories") or ())
                & {"wrist", "float"}
            )
        ):
            end_state["campaign_school_wrist_float_attempted_level"] = _level(
                end_state
            )
        if policy.execution == "recover-gremlin-waist":
            end_state["campaign_gremlin_waist_attempted_level"] = _level(end_state)
        if policy.execution == "recover-daycare-ring":
            end_state["campaign_daycare_ring_attempted_level"] = _level(end_state)
        self._policy_xp_deltas[policy.policy_id] = _xp_delta(state, end_state)
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
            "campaign_policy_revision": _CAMPAIGN_POLICY_REVISION,
            "campaign_last_policy": (
                state.get("campaign_last_policy")
                if policy.execution in _MAINTENANCE_EXECUTIONS
                else policy.policy_id
            ),
            "campaign_has_weapon": (
                bool(
                    end_state.get(
                        "campaign_has_weapon",
                        state.get("campaign_has_weapon", True),
                    )
                )
            ),
        }
        previous_liquidation_baseline = state.get(_LIQUIDATION_BASELINE_KEY)
        if policy.execution in {"sell-loot", "rearm-weapon"}:
            checkpoint_state[_LIQUIDATION_BASELINE_KEY] = list(
                _campaign_liquidation_signature(
                    end_state,
                    gear_catalog=self._gear_catalog,
                )
            )
        elif previous_liquidation_baseline is not None:
            checkpoint_state[_LIQUIDATION_BASELINE_KEY] = (
                previous_liquidation_baseline
            )
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


def _campaign_practice_types_spent(
    storage: RunStorage,
    campaign_id: int,
    *,
    level: int,
) -> frozenset[str]:
    spent: set[str] = set()
    for segment in storage.list_campaign_segments(campaign_id):
        if segment["status"] != "success" or segment["run_id"] is None:
            continue
        start_state = json.loads(segment["start_state_json"] or "{}")
        if _level(start_state) != level:
            continue
        for event in storage.list_events(int(segment["run_id"])):
            if event["kind"] != "game_event":
                continue
            payload = json.loads(event["payload_json"])
            if payload.get("type") != "training_completed":
                continue
            practice_type = str(payload.get("data", {}).get("practice_type", ""))
            if practice_type in {"physical", "intellectual"}:
                spent.add(practice_type)
    return frozenset(spent)


def _campaign_rejected_practice_skills(
    storage: RunStorage,
    campaign_id: int,
    *,
    level: int,
) -> frozenset[str]:
    rejected: set[str] = set()
    permanent_trainer_reasons = {
        "trainer level requirement",
        "trainer proficiency cap",
    }
    for segment in storage.list_campaign_segments(campaign_id):
        if segment["status"] != "success" or segment["run_id"] is None:
            continue
        start_state = json.loads(segment["start_state_json"] or "{}")
        if _level(start_state) != level:
            continue
        for event in storage.list_events(int(segment["run_id"])):
            if event["kind"] != "game_event":
                continue
            payload = json.loads(event["payload_json"])
            if payload.get("type") != "training_rejected":
                continue
            data = payload.get("data", {})
            if data.get("reason") not in permanent_trainer_reasons:
                continue
            skill = str(data.get("skill", "")).strip().casefold()
            if skill:
                rejected.add(skill)
    return frozenset(rejected)


def _campaign_flight_purchase_failed(
    storage: RunStorage,
    campaign_id: int,
) -> bool | None:
    """Return the newest result from the policy that owns flight purchasing."""
    for segment in reversed(storage.list_campaign_segments(campaign_id)):
        if segment["phase"] != "buy-flight-potion":
            continue
        if segment["status"] != "success" or not segment["end_state_json"]:
            continue
        state = json.loads(segment["end_state_json"])
        return bool(state.get("magic_shop_purchase_failed"))
    return None


async def _run_policy_segment(
    spec: CharacterSpec,
    profile_path: Path,
    policy: ProgressionPolicy,
    *,
    practice_types_spent: frozenset[str] = frozenset(),
    rejected_practice_skills: frozenset[str] = frozenset(),
    vault_stow_items: tuple[str, ...] = (),
) -> RunResult:
    if policy.execution == "starter":
        return await StarterBotRunner(spec, profile_path).run()
    if policy.execution == "arena":
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 10,
            arena_kill_limit=policy.segment_kill_limit,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "foundry-hunt":
        hunt_stops = (
            foundry_level_seven_hunt_stops()
            if policy.minimum_level >= 7
            else foundry_level_six_hunt_stops()
        )
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 7,
            fastwalk_route=route_named("foundry"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=hunt_stops,
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "moria-orc-hunt":
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 8,
            fastwalk_route=route_named("moria"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=moria_level_seven_orc_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "moria-large-orc-hunt":
        hunt_stops = (
            moria_level_seven_orc_hunt_stops()
            if policy.minimum_level >= 9
            else moria_level_eight_large_orc_hunt_stops()
        )
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 9,
            fastwalk_route=route_named("moria"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=hunt_stops,
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "daycare-nanny-hunt":
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 8,
            fastwalk_route=daycare_nanny_hunt_route(),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=daycare_nanny_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "daycare-armed-guard-hunt":
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 9,
            fastwalk_route=daycare_armed_guard_hunt_route(),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=daycare_armed_guard_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "cult-fanatic-research":
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 9,
            fastwalk_route=route_named("dragon cult"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=cult_fanatic_research_stops(),
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "circus-freak-show-hunt":
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 8,
            fastwalk_route=route_named("circus bearded lady"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=circus_freak_show_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_world_cache_items=("ticket",),
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "shire-bull-hunt":
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 8,
            fastwalk_route=shire_bull_hunt_route(),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=shire_bull_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "gnome-hermit-hunt":
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 8,
            fastwalk_route=gnome_hermit_hunt_route(),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=gnome_hermit_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "gnome-guard-hunt":
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 9,
            fastwalk_route=route_named("gnome guard hut"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=gnome_guard_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "gnome-small-troll-hunt":
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 8,
            fastwalk_route=route_named("gnome small troll"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=gnome_small_troll_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=True,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "sell-loot":
        return await StarterBotRunner(
            spec,
            profile_path,
            liquidate_loot=True,
        ).run()
    if policy.execution == "vault-spare-gear":
        return await StarterBotRunner(
            spec,
            profile_path,
            vault_stow_items=vault_stow_items,
            vault_required_free_weight=10,
            vault_only=True,
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
    if policy.execution == "outfit-basic-gear":
        return await StarterBotRunner(
            spec,
            profile_path,
            city_outfit=True,
        ).run()
    if policy.execution == "recover-basic-body":
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 10,
            fastwalk_route=route_named("foundry"),
            fastwalk_required_free_weight=_RECOVER_BASIC_BODY_REQUIRED_FREE_WEIGHT,
            fastwalk_hunt_stops=foundry_body_gear_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=False,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
        ).run()
    if policy.execution == "recover-school-wrist-float":
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 10,
            fastwalk_route=school_accessory_hunt_route(),
            fastwalk_required_free_weight=(
                _RECOVER_SCHOOL_WRIST_FLOAT_REQUIRED_FREE_WEIGHT
            ),
            fastwalk_hunt_stops=school_wrist_float_hunt_stops(),
            fastwalk_train_before_departure=False,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
        ).run()
    if policy.execution == "recover-gremlin-waist":
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 10,
            fastwalk_route=gremlin_waist_hunt_route(),
            fastwalk_required_free_weight=_RECOVER_GREMLIN_WAIST_REQUIRED_FREE_WEIGHT,
            fastwalk_hunt_stops=gremlin_waist_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=False,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
        ).run()
    if policy.execution == "recover-daycare-ring":
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 10,
            fastwalk_route=daycare_ring_hunt_route(),
            fastwalk_required_free_weight=_RECOVER_DAYCARE_RING_REQUIRED_FREE_WEIGHT,
            fastwalk_hunt_stops=daycare_ring_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=False,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
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
        "ambush-raider-hunt",
        "ambush-vile-hunt",
    }:
        if policy.execution == "ambush-war-dog-hunt":
            hunt_stops = (
                ambush_caster_level_eight_hunt_stops()
                if policy.policy_id == "ambush-war-dog-looter-8-9"
                else ambush_level_eight_hunt_stops()
            )
        elif policy.execution == "ambush-raider-hunt":
            hunt_stops = ambush_raider_hunt_stops()
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
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=True,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
        ).run()
    if policy.execution == "fleshmonger-guard-research":
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 9,
            fastwalk_route=replace(
                route_named("fleshmonger"),
                recall_after_loot=True,
            ),
            fastwalk_hunt_stops=fleshmonger_guard_research_stops(),
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
        ).run()
    if policy.execution == "ambush-martial-hunt":
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 9,
            fastwalk_route=route_named("ambush"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=ambush_martial_level_eight_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "midennir-hunt":
        use_level_eight_loadout = (policy.minimum_level or 0) >= 8
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=policy.maximum_level or 10,
            fastwalk_route=route_named("ambush"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=midennir_mountain_goblin_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=not use_level_eight_loadout,
            fastwalk_require_invisibility=use_level_eight_loadout,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
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


def _has_campaign_food(
    state: dict[str, Any],
    *,
    gear_catalog: GearCatalog | None,
) -> bool:
    if "inventory" not in state:
        return True
    for description in _inventory_descriptions(state.get("inventory")):
        normalized = normalize_item_name(description)
        if "pie" in normalized or "steak" in normalized:
            return True
        item = gear_catalog.match(description) if gear_catalog is not None else None
        if item is not None and item.item_type == 19:
            return True
    return False


def _has_own_corpse_recovery(
    state: dict[str, Any],
    character_name: str,
) -> bool:
    needle = f"corpse of {character_name}".casefold()
    acquisitions = state.get("acquired_items")
    if not isinstance(acquisitions, list):
        return False
    return any(
        needle in str(acquisition.get("item", "")).casefold()
        for acquisition in acquisitions
        if isinstance(acquisition, dict)
    )


def _campaign_policy_xp_deltas(segments: list[Any]) -> dict[str, int]:
    """Return the most recent same-campaign XP result for each policy."""
    results: dict[str, int] = {}
    for segment in segments:
        if segment["status"] != "success":
            continue
        start = json.loads(segment["start_state_json"] or "{}")
        end = json.loads(segment["end_state_json"] or "{}")
        results[str(segment["phase"])] = _xp_delta(start, end)
    return results


def _xp_delta(before: dict[str, Any], after: dict[str, Any]) -> int:
    """Treat a level gain as progress even when DD4 resets cumulative XP."""
    level_delta = _level(after) - _level(before)
    if level_delta > 0:
        return max(1, level_delta)
    return _numeric_progress(after, "xp") - _numeric_progress(before, "xp")


def _campaign_segment_end_state(
    previous: dict[str, Any],
    current: dict[str, Any],
    *,
    execution: str,
) -> dict[str, Any]:
    """Keep maintenance facts sticky until their owning policy re-evaluates them."""
    merged = dict(current)
    if (
        execution != "buy-flight-potion"
        and previous.get("magic_shop_purchase_failed")
    ):
        merged["magic_shop_purchase_failed"] = True
    if previous.get("vault_storage_rejected"):
        merged["vault_storage_rejected"] = True
    for owner, key in (
        ("outfit-basic-gear", "campaign_outfit_attempted_level"),
        ("recover-basic-body", "campaign_body_gear_attempted_level"),
        (
            "recover-school-wrist-float",
            "campaign_school_wrist_float_attempted_level",
        ),
        ("recover-gremlin-waist", "campaign_gremlin_waist_attempted_level"),
        ("recover-daycare-ring", "campaign_daycare_ring_attempted_level"),
    ):
        if execution != owner and key in previous:
            merged[key] = previous[key]
    return merged


def _newer_progress_state(
    checkpoint: dict[str, Any],
    live: dict[str, Any] | None,
) -> dict[str, Any]:
    if not live:
        return checkpoint
    if (
        isinstance(live.get("level"), (int, float))
        and isinstance(live.get("xp"), (int, float))
    ):
        merged = {**checkpoint, **live}
        if (
            merged.get("dead")
            and str(merged.get("area", "")).casefold() != "purgatory"
            and _numeric_progress(merged, "hp") > 0
        ):
            merged["dead"] = False
        return merged
    checkpoint_progress = (_level(checkpoint), _numeric_progress(checkpoint, "xp"))
    live_progress = (_level(live), _numeric_progress(live, "xp"))
    return {**checkpoint, **live} if live_progress >= checkpoint_progress else checkpoint


def _numeric_progress(state: dict[str, Any], key: str) -> int:
    value = state.get(key)
    return int(value) if isinstance(value, (int, float)) else 0


def _run_has_unrecovered_weapon_loss(
    storage: RunStorage,
    run_id: int,
) -> bool:
    """Reconstruct the final weapon state for legacy or interrupted runs."""
    weapon_present: bool | None = None
    awaiting_equipment_response = False
    for event in storage.list_events(run_id):
        payload = json.loads(event["payload_json"])
        if event["kind"] == "command":
            awaiting_equipment_response = (
                str(payload.get("command", "")).casefold() == "equipment"
            )
            continue
        if event["kind"] != "response":
            continue
        response = str(payload.get("text", "")).casefold()
        if awaiting_equipment_response:
            cleaned = _ANSI_ESCAPE.sub("", response)
            if _is_equipment_audit_response(cleaned):
                weapon_present = bool(
                    re.search(r"(?:\[weapon\]|<[^>]*wield[^>]*>)", cleaned)
                )
                awaiting_equipment_response = False
        if (
            "disarms you" in response
            or "your weapon slips from your hand" in response
        ):
            weapon_present = False
        if "you wield " in response:
            weapon_present = True
    return weapon_present is False


def _run_equipment_empty_categories(
    storage: RunStorage,
    run_id: int,
) -> set[str] | None:
    """Return the empty legal categories from the run's newest ``eq all``."""
    result: set[str] | None = None
    awaiting_audit = False
    for event in storage.list_events(run_id):
        payload = json.loads(event["payload_json"])
        if event["kind"] == "command":
            awaiting_audit = (
                str(payload.get("command", "")).strip().casefold() == "eq all"
            )
            continue
        if event["kind"] != "response" or not awaiting_audit:
            continue
        response = str(payload.get("text", ""))
        if not _equipment_audit_present(response):
            continue
        result = _equipment_empty_categories(response)
        awaiting_audit = False
    return result


def _run_worn_equipment_descriptions(
    storage: RunStorage,
    run_id: int,
) -> list[str] | None:
    """Return source-matchable worn descriptions from the newest ``eq all``."""
    result: list[str] | None = None
    awaiting_audit = False
    for event in storage.list_events(run_id):
        payload = json.loads(event["payload_json"])
        if event["kind"] == "command":
            awaiting_audit = (
                str(payload.get("command", "")).strip().casefold() == "eq all"
            )
            continue
        if event["kind"] != "response" or not awaiting_audit:
            continue
        response = str(payload.get("text", ""))
        if not _equipment_audit_present(response):
            continue
        result = _equipment_audit_descriptions(response)
        awaiting_audit = False
    return result


def _is_equipment_audit_response(response: str) -> bool:
    """Reject stale command pulses while reconstructing an equipment audit."""
    return "you are not using any equipment" in response or bool(
        re.search(r"(?:\[weapon\]|\[held\]|<[^>]*worn[^>]*>)", response)
    )


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


def _has_campaign_sellable_loot(
    state: dict[str, Any],
    *,
    gear_catalog: GearCatalog | None = None,
) -> bool:
    keyword = _sellable_inventory_keyword(
        state.get("inventory"),
        gear_catalog,
    )
    if keyword is None:
        return False
    if keyword == "collar":
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
        if carry_weight / maximum_weight < 0.85:
            return False
    stats = state.get("stats")
    if isinstance(stats, dict):
        carry_weight = stats.get("carry_wt")
        maximum_weight = stats.get("maxcarry_wt")
        if (
            isinstance(carry_weight, (int, float))
            and isinstance(maximum_weight, (int, float))
            and maximum_weight > 0
            and maximum_weight - carry_weight <= 10
        ):
            empty_categories = set(
                state.get("campaign_empty_equipment_categories") or ()
            )
            for description in _inventory_descriptions(state.get("inventory")):
                if _sellable_inventory_keyword(
                    [[{"short_desc": description}]],
                    gear_catalog,
                ) is None:
                    continue
                item = gear_catalog.match(description) if gear_catalog else None
                if (
                    item is not None
                    and item_category(item) in empty_categories
                ):
                    continue
                return True
            return False
    return not _matches_liquidation_baseline(state, gear_catalog=gear_catalog)


def _campaign_vault_stow_items(
    state: dict[str, Any],
    *,
    gear_catalog: GearCatalog | None,
    required_free_weight: int = 10,
) -> tuple[str, ...]:
    if gear_catalog is None:
        return ()
    stats = state.get("stats")
    if not isinstance(stats, dict):
        return ()
    carry_weight = stats.get("carry_wt")
    maximum_weight = stats.get("maxcarry_wt")
    if not isinstance(carry_weight, (int, float)):
        return ()
    if not isinstance(maximum_weight, (int, float)):
        return ()
    if maximum_weight - carry_weight >= required_free_weight:
        return ()

    keywords: list[str] = []
    selected_weight = 0
    capacity_candidates: list[tuple[int, str]] = []
    worn_counts = Counter(
        normalize_item_name(description)
        for description in state.get("campaign_worn_equipment") or ()
    )
    for description in _inventory_descriptions(state.get("inventory")):
        item = gear_catalog.match(description)
        if item is None:
            continue
        normalized_description = normalize_item_name(description)
        if worn_counts[normalized_description] > 0:
            worn_counts[normalized_description] -= 1
            continue
        candidates = gear_catalog.candidates(description)
        ambiguous_weapon = (
            item.item_type == 5
            and len(candidates) > 1
            and all(candidate.item_type == 5 for candidate in candidates)
        )
        plain_armour = item.item_type == 9 and not protects_from_sale(item)
        protected_spare = (
            protects_from_sale(item)
            and not is_capacity_infrastructure(item)
            and item_category(item) not in {"light", "wield"}
        )
        keyword = item_keyword(item)
        normalized_name = normalize_item_name(item.short_description)
        if is_capacity_infrastructure(item):
            if "large sack" in normalized_name:
                keyword = "sack"
            elif "backpack" in normalized_name:
                keyword = "backpack"
            elif "girdle of many pouches" in normalized_name:
                keyword = "girdle"
        if not keyword:
            continue
        if is_capacity_infrastructure(item):
            capacity_candidates.append((item.weight, keyword))
            continue
        if ambiguous_weapon or plain_armour or protected_spare:
            selected_weight += item.weight
        else:
            continue
        if keyword not in keywords:
            keywords.append(keyword)

    free_weight = maximum_weight - carry_weight
    for weight, keyword in sorted(capacity_candidates, reverse=True):
        if free_weight + selected_weight >= required_free_weight:
            break
        if keyword not in keywords:
            keywords.append(keyword)
            selected_weight += weight
    return tuple(keywords)


def _has_oversized_capacity_stow_item(
    state: dict[str, Any],
    *,
    gear_catalog: GearCatalog | None,
    stow_items: tuple[str, ...],
) -> bool:
    if gear_catalog is None or not stow_items:
        return False
    stats = state.get("stats")
    maximum_weight = stats.get("maxcarry_wt") if isinstance(stats, dict) else None
    if not isinstance(maximum_weight, (int, float)) or maximum_weight <= 0:
        return False
    stow_keywords = {keyword.casefold() for keyword in stow_items}
    for description in _inventory_descriptions(state.get("inventory")):
        item = gear_catalog.match(description)
        if item is None or not is_capacity_infrastructure(item):
            continue
        if not stow_keywords.intersection(item.keywords.casefold().split()):
            continue
        if item.weight >= max(20, maximum_weight * 0.2):
            return True
    return False


def _has_campaign_free_weight(
    state: dict[str, Any],
    required_free_weight: int,
) -> bool:
    stats = state.get("stats")
    if not isinstance(stats, dict):
        return True
    carry_weight = stats.get("carry_wt")
    maximum_weight = stats.get("maxcarry_wt")
    if not isinstance(carry_weight, (int, float)):
        return True
    if not isinstance(maximum_weight, (int, float)):
        return True
    return maximum_weight - carry_weight >= required_free_weight


def _campaign_liquidation_signature(
    state: dict[str, Any],
    *,
    gear_catalog: GearCatalog | None = None,
) -> tuple[str, ...]:
    candidates = (
        normalize_item_name(description)
        for description in _inventory_descriptions(state.get("inventory"))
        if _sellable_inventory_keyword(
            [[{"short_desc": description}]],
            gear_catalog,
        )
        is not None
    )
    return tuple(sorted(candidates))


def _matches_liquidation_baseline(
    state: dict[str, Any],
    *,
    gear_catalog: GearCatalog | None = None,
) -> bool:
    baseline = state.get(_LIQUIDATION_BASELINE_KEY)
    if not isinstance(baseline, (list, tuple)) or not all(
        isinstance(item, str) for item in baseline
    ):
        return False
    return _campaign_liquidation_signature(
        state,
        gear_catalog=gear_catalog,
    ) == tuple(sorted(normalize_item_name(item) for item in baseline))


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
    if previous.get("campaign_policy_revision") != before.get(
        "campaign_policy_revision"
    ):
        previous_stalled = 0
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
