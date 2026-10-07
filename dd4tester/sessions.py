"""Own live session state and bounded authenticated quest-phase handoffs."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Collection, Mapping

from .excavation import DigBudget, DigObservation, DigStep, HoardDigSession
from .area_recall import AreaRecallEscape
from .fastwalks import Fastwalk
from .quests import snapshot_quest_status

if TYPE_CHECKING:
    from .starter import FieldHuntStop, StarterPolicy
    from .state import CharacterState


@dataclass
class CombatSessionController:
    """Own the live combat loop's mutable control state."""

    active: bool = False
    action_target: str | None = None
    actions_since_disarm: int = 0
    disarm_attempts: int = 0
    disarm_resolved: bool = False
    repeat_action_cursor: int = 0


@dataclass
class TravelSessionController:
    """Own the active policy's bounded route and stop cursors."""

    outbound_index: int = 0
    return_index: int = 0
    hunt_stop_index: int = 0
    hunt_move_index: int = 0
    hunt_action_index: int = 0
    blocked_reason: str | None = None


@dataclass
class RecoverySessionController:
    """Own pending recovery actions and their bounded route state."""

    emergency_recall_pending: bool = False
    emergency_recall_failed: bool = False
    ready: bool = False
    commands: tuple[str, ...] | None = None
    wake_command_pending: bool = False
    sleep_confirmation_pending: bool = False
    area_recall_escape: AreaRecallEscape | None = None


@dataclass
class LiveSessionState:
    """Root owner for character, lifecycle, and controller state per session."""

    character: CharacterState
    quest_session: QuestSessionController | None = None
    combat: CombatSessionController = field(
        default_factory=CombatSessionController,
    )
    travel: TravelSessionController = field(
        default_factory=TravelSessionController,
    )
    recovery: RecoverySessionController = field(
        default_factory=RecoverySessionController,
    )
    phase: str = "initializing"
    authenticated: bool = False
    in_world: bool = False
    world_boot_id: str | None = None

    def apply(self, event: Any) -> bool:
        return self.character.apply(event)


@dataclass(frozen=True)
class QuestHandoffState:
    """Portable quest-phase continuity, separate from route-local policy state."""

    progression: dict[str, Any]
    skills: dict[str, Any]
    gear: dict[str, Any]
    weapons: dict[str, Any]

    @classmethod
    def capture(cls, policy: StarterPolicy) -> "QuestHandoffState":
        scalar_names = (
            "title_configured", "description_configured", "course_complete",
            "world_boot_id", "world_time_queried", "selected_training_stat",
            "counterbalanced_weapon_vnum", "chained_weapon_vnum",
        )
        set_names = (
            "known_skills", "rejected_practice_skills", "practice_types_spent",
            "deferred_practice_types", "maxed_stats",
        )
        mapping_names = ("known_skill_levels", "permanent_stats")
        progression = {name: deepcopy(getattr(policy, name)) for name in scalar_names}
        skills = {
            name: deepcopy(getattr(policy, name))
            for name in (*set_names, *mapping_names)
        }
        gear: dict[str, Any] = {
            "structured_current": bool(policy.gear_worn_structured_current),
        }
        if policy.gear_worn_structured_current:
            for name in (
                "gear_worn", "gear_instance_sources", "gear_inventory_source_hints",
                "gear_worn_instance_ids", "gear_ranged_vnums",
                "gear_chained_weapon_vnums", "gear_wielded_vnum",
            ):
                gear[name] = deepcopy(getattr(policy, name))
        weapons = {
            name: deepcopy(getattr(policy, name))
            for name in (
                "primary_weapon_lost", "primary_weapon_observed",
                "disarm_recovery_failed",
            )
        }
        return cls(progression, skills, gear, weapons)

    def restore(self, policy: StarterPolicy) -> None:
        for values in (self.progression, self.skills, self.weapons):
            for name, value in values.items():
                setattr(policy, name, deepcopy(value))
        if self.gear.get("structured_current"):
            policy.gear_worn_structured_current = True
            for name, value in self.gear.items():
                if name != "structured_current":
                    setattr(policy, name, deepcopy(value))
        policy.in_world = True
        policy.login_authenticated = True
        policy.prompt_ready = True
        policy.stage = "tutorial"


QUEST_WAIT_READER_REVISION = 3


@dataclass(frozen=True)
class QuestPhase:
    name: str
    reason: str
    route: Fastwalk | None = None
    hunt_stops: tuple[FieldHuntStop, ...] = ()
    origin_actions: tuple[str, ...] = ("drink skin",)
    use_sanctuary_potions: bool = False

    def policy_options(self) -> dict[str, Any]:
        if self.route is None:
            raise ValueError("a travelling quest phase requires an audited route")
        return {
            "fastwalk_route": self.route,
            "fastwalk_hunt_stops": self.hunt_stops,
            "fastwalk_origin_actions": self.origin_actions,
            "fastwalk_kill_limit": 1,
            "fastwalk_train_before_departure": False,
            "use_sanctuary_potions": self.use_sanctuary_potions,
        }


def resume_policy_at_healer(
    previous: StarterPolicy, following: StarterPolicy, state: CharacterState,
) -> None:
    """Carry capabilities, not old route cursors, into an authenticated phase."""
    if (
        state.room_vnum != "3054" or state.dead or state.in_combat
        or not state.hp or state.hp <= 0
        or previous._current_room_enemy_records(state)
        or not previous.in_world or not previous.login_authenticated
        or not previous.saved or previous.runtime_boundary_requested
    ):
        raise ValueError("quest handoff requires an acknowledged live healer checkpoint")
    continuity = QuestHandoffState.capture(previous)
    continuity.restore(following)
    # DD4 may omit unchanged Char.Worn data on this same socket. A new phase's
    # text audit must not discard the exact identities already observed here.
    following.current_room = state.room_vnum
    following.enemy_snapshot_room = state.room_vnum
    following.enemy_snapshot_stale = False


def quest_identity(status: dict[str, Any]) -> tuple[Any, ...]:
    quest = snapshot_quest_status(status)
    return (
        quest.kind, quest.mob_vnum, quest.object_vnum, quest.room_vnum,
        str(status.get("giver_vnum") or ""),
    )


@dataclass(frozen=True)
class CooldownStep:
    status: str
    reason: str
    command: str | None = None
    wait_seconds: float = 0.0


@dataclass
class QuestCooldownWait:
    """Wait for server ticks, never age an offline quest counter locally."""
    lowest_remaining: int | None = None
    last_progress_at: float | None = None
    resource_attempts: dict[str, tuple[float, int]] = field(default_factory=dict)
    vitals_requested: bool = False
    next_query_at: float = 0.0

    def poll(
        self, state: CharacterState, *, now: float,
        food_keyword: str | None, has_water_skin: bool,
    ) -> CooldownStep:
        quest = snapshot_quest_status(state.quest_status)
        if not quest.active:
            try:
                remaining = int(state.quest_status["nextquest"])
            except (KeyError, TypeError, ValueError):
                return CooldownStep("stopped", "live quest cooldown is missing or malformed")
            if remaining < 0:
                return CooldownStep("stopped", "live quest cooldown is negative")
        if quest.active or quest.nextquest <= 0:
            return CooldownStep("ready", "live quest cooldown has cleared")
        if self.lowest_remaining is None or quest.nextquest < self.lowest_remaining:
            self.lowest_remaining = quest.nextquest
            self.last_progress_at = now
        elif quest.nextquest > self.lowest_remaining:
            return CooldownStep("stopped", "live quest cooldown unexpectedly increased")
        if self.last_progress_at is not None and now - self.last_progress_at >= 180:
            return CooldownStep("stopped", "live quest cooldown did not advance for 180 seconds")
        if state.hunger is None or state.thirst is None:
            if self.vitals_requested:
                return CooldownStep("stopped", "live nutrition is unavailable for a connected wait")
            self.vitals_requested = True
            return CooldownStep("waiting", "audit nutrition before a connected quest wait", "score")
        for kind, value, command in (
            ("food", state.hunger, f"eat {food_keyword}" if food_keyword else None),
            ("water", state.thirst, "drink skin" if has_water_skin else None),
        ):
            if value > 8:
                self.resource_attempts.pop(kind, None)
                continue
            if command is None:
                return CooldownStep("stopped", f"no carried {kind} reserve for the connected wait")
            previous, attempts = self.resource_attempts.get(kind, (value, 0))
            attempts = 0 if value > previous else attempts
            if attempts >= 2:
                return CooldownStep("stopped", f"{kind} did not improve after two consumption attempts")
            self.resource_attempts[kind] = (value, attempts + 1)
            return CooldownStep("waiting", f"maintain {kind} during the connected quest wait", command, 1.0)
        if now < self.next_query_at:
            return CooldownStep(
                "waiting", "listen for live quest progress between timer queries",
            )
        query_interval = 5.0 if quest.nextquest <= 1 else 30.0
        self.next_query_at = now + query_interval
        return CooldownStep(
            "waiting", "remain at the healer while the live quest cooldown advances",
            "quest time",
        )


@dataclass
class QuestSessionController:
    """Own bounded quest-phase continuity and its live-session evidence."""

    phase: str | None
    planner: Callable[[str, Mapping[str, Any]], QuestPhase | None] | None = None
    expected_status: dict[str, Any] = field(default_factory=dict)
    wait_for_cooldown: bool = False
    phases: list[dict[str, Any]] = field(default_factory=list)
    completed_kills: list[dict[str, Any]] = field(default_factory=list)
    objective_kills: list[dict[str, Any]] = field(default_factory=list)
    observed_on_connection: bool = False
    continuation_closed: bool = False
    abort_sent: bool = False
    phase_active_checked: bool = False
    cooldown: QuestCooldownWait = field(default_factory=QuestCooldownWait)
    cooldown_marker: tuple[object, ...] | None = None
    request_attempt: dict[str, Any] | None = None
    hoard_excavation_checkpoint: object | None = field(
        default=None, repr=False,
    )
    hoard_excavation: HoardDigSession | None = field(
        default=None, init=False,
    )
    hoard_excavation_restore_issue: str | None = field(
        default=None, init=False,
    )

    def __post_init__(self) -> None:
        if self.hoard_excavation_checkpoint is not None:
            try:
                self.restore_hoard_excavation(
                    self.hoard_excavation_checkpoint,
                )
            except ValueError as exc:
                self.hoard_excavation_restore_issue = str(exc)
            self.hoard_excavation_checkpoint = None

    def _active_hoard_identity(
        self, status: Mapping[str, Any] | None = None,
    ) -> tuple[int, int, int] | None:
        active_status = self.expected_status if status is None else status
        if (
            not isinstance(active_status, Mapping)
            or (
                "active" in active_status
                and not bool(active_status.get("active"))
            )
        ):
            return None
        quest = snapshot_quest_status(active_status)
        if not quest.active or quest.kind != "hoard":
            return None
        try:
            giver_vnum = int(active_status.get("giver_vnum") or 0)
        except (TypeError, ValueError):
            return None
        identity = (giver_vnum, quest.room_vnum, quest.object_vnum)
        return identity if all(value > 0 for value in identity) else None

    def restore_hoard_excavation(self, checkpoint: object) -> None:
        """Restore only against the same narrative-verified active assignment."""
        excavation = HoardDigSession.from_checkpoint(checkpoint)
        if self._active_hoard_identity() != excavation.quest_identity:
            raise ValueError(
                "hoard excavation checkpoint does not match the active verified quest"
            )
        self.hoard_excavation = excavation

    def begin_hoard_excavation(
        self,
        budget: DigBudget,
        *,
        minimum_hp: int,
        return_movement: int,
        current_status: Mapping[str, Any],
    ) -> HoardDigSession:
        """Create one controller only for the observed matching hoard quest."""
        expected_identity = self._active_hoard_identity()
        current_identity = self._active_hoard_identity(current_status)
        if (
            self.phase != "quest-target-run"
            or not self.observed_on_connection
            or expected_identity is None
            or current_identity != expected_identity
        ):
            raise ValueError(
                "hoard excavation requires the exact active quest observed "
                "on this connection"
            )
        if self.hoard_excavation is not None:
            existing = self.hoard_excavation
            if (
                existing.quest_identity != current_identity
                or existing.budget != budget
                or existing.minimum_hp != minimum_hp
                or existing.return_movement != return_movement
            ):
                raise ValueError("a different hoard excavation is already active")
            return existing
        self.hoard_excavation = HoardDigSession(
            budget,
            quest_identity=current_identity,
            minimum_hp=minimum_hp,
            return_movement=return_movement,
        )
        return self.hoard_excavation

    def checkpoint_hoard_excavation(
        self, current_status: Mapping[str, Any] | None = None,
    ) -> dict[str, object] | None:
        """Persist excavation state only while its exact hoard remains active."""
        if self.hoard_excavation is None:
            return None
        if self._active_hoard_identity(
            current_status,
        ) != self.hoard_excavation.quest_identity:
            return None
        return self.hoard_excavation.checkpoint()

    def poll_hoard_excavation(
        self,
        observed: DigObservation,
        *,
        now: float,
        current_status: Mapping[str, Any],
    ) -> DigStep | None:
        """Advance digging only while the exact narrative-verified quest is live."""
        excavation = self.hoard_excavation
        if excavation is None:
            return None
        if self._active_hoard_identity(current_status) != excavation.quest_identity:
            self.hoard_excavation = None
            return DigStep("stopped", "active verified hoard assignment changed")
        return excavation.poll(observed, now=now)

    def confirm_hoard_trap_recovery(
        self,
        observed: DigObservation,
        *,
        current_status: Mapping[str, Any],
    ) -> DigStep | None:
        """Keep trap recovery under the same exact-assignment ownership check."""
        excavation = self.hoard_excavation
        if excavation is None:
            return None
        if self._active_hoard_identity(current_status) != excavation.quest_identity:
            self.hoard_excavation = None
            return DigStep("stopped", "active verified hoard assignment changed")
        return excavation.confirm_trap_recovery(observed)

    def prepare_hoard_object_pickup(
        self,
        *,
        sequence: int,
        quest_object_vnum: int,
        source_object_description: str,
        source_description_vnums: Collection[int],
        current_room_vnum: int | str,
        room_listing: Mapping[str, object],
        inventory_items: object,
        current_status: Mapping[str, Any],
    ) -> DigStep | None:
        """Persist the exact pickup intent under the active quest owner."""
        excavation = self.hoard_excavation
        if excavation is None:
            return None
        if self._active_hoard_identity(current_status) != excavation.quest_identity:
            self.hoard_excavation = None
            return DigStep("stopped", "active verified hoard assignment changed")
        if self.phase != "quest-target-run" or not self.observed_on_connection:
            return DigStep(
                "stopped",
                "quest-object pickup requires the active hoard phase on this connection",
            )
        return excavation.prepare_quest_object_pickup(
            sequence=sequence,
            quest_object_vnum=quest_object_vnum,
            source_object_description=source_object_description,
            source_description_vnums=source_description_vnums,
            current_room_vnum=current_room_vnum,
            room_listing=room_listing,
            inventory_items=inventory_items,
        )

    def confirm_hoard_object_acquired(
        self,
        *,
        sequence: int,
        quest_object_vnum: int,
        source_object_description: str,
        source_description_vnums: Collection[int],
        inventory_items: object,
        current_status: Mapping[str, Any],
    ) -> DigStep | None:
        """Confirm the pending pickup from a newer complete inventory snapshot."""
        excavation = self.hoard_excavation
        if excavation is None:
            return None
        if self._active_hoard_identity(current_status) != excavation.quest_identity:
            self.hoard_excavation = None
            return DigStep("stopped", "active verified hoard assignment changed")
        if self.phase != "quest-target-run" or not self.observed_on_connection:
            return DigStep(
                "stopped",
                "quest-object pickup requires the active hoard phase on this connection",
            )
        return excavation.confirm_quest_object_acquired(
            sequence=sequence,
            quest_object_vnum=quest_object_vnum,
            source_object_description=source_object_description,
            source_description_vnums=source_description_vnums,
            inventory_items=inventory_items,
        )

    def observe_hoard_text(
        self, text: str, current_status: Mapping[str, Any],
    ) -> bool:
        """Forward server text only to the matching active excavation session."""
        excavation = self.hoard_excavation
        if excavation is None:
            return False
        if self._active_hoard_identity(current_status) != excavation.quest_identity:
            self.hoard_excavation = None
            return False
        excavation.observe(text)
        return True

    def observe_quest_status(self) -> None:
        self.observed_on_connection = True

    def connection_closed(self) -> None:
        self.observed_on_connection = False
        self.continuation_closed = True

    def plan_next_phase(
        self, state: Mapping[str, Any], *, permitted: bool,
    ) -> QuestPhase | None:
        active_phase_count = sum(
            item.get("phase") != "quest-cooldown" for item in self.phases
        )
        if (
            not permitted or self.planner is None or self.phase is None
            or active_phase_count >= 4
        ):
            return None
        return self.planner(self.phase, state)

    def activate(self, phase: QuestPhase) -> None:
        if any(item.get("phase") == phase.name for item in self.phases):
            raise RuntimeError("quest phase repetition is not permitted")
        self.phase = phase.name
        self.phase_active_checked = True

    def checkpoint(
        self,
        state: dict[str, Any],
        *,
        objective_kills: list[dict[str, Any]],
        commands: int,
    ) -> dict[str, Any] | None:
        if self.phase is None or (self.phases and self.phases[-1].get("phase") == self.phase):
            return None
        snapshot = {
            "phase": self.phase,
            "state": state,
            "objective_kills": objective_kills,
            "commands": commands,
        }
        self.phases.append(snapshot)
        return snapshot
