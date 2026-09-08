"""Bounded, authenticated handoffs between live quest phases."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .fastwalks import Fastwalk
from .quests import snapshot_quest_status

if TYPE_CHECKING:
    from .starter import FieldHuntStop, StarterPolicy
    from .state import CharacterState


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
    for name in (
        "title_configured", "description_configured", "course_complete",
        "world_boot_id", "world_time_queried", "selected_training_stat",
        "counterbalanced_weapon_vnum", "chained_weapon_vnum",
    ):
        setattr(following, name, getattr(previous, name))
    for name in (
        "known_skills", "rejected_practice_skills", "practice_types_spent",
        "deferred_practice_types", "maxed_stats",
    ):
        setattr(following, name, set(getattr(previous, name)))
    for name in ("known_skill_levels", "permanent_stats"):
        setattr(following, name, dict(getattr(previous, name)))
    following.in_world = True
    following.login_authenticated = True
    following.prompt_ready = True
    following.stage = "tutorial"
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
        return CooldownStep(
            "waiting", "remain at the healer while the live quest cooldown advances",
            "quest time", 30.0,
        )
