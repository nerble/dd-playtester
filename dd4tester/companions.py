"""Source-bounded preparation and positive ownership proof for field companions."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Collection, Mapping, Sequence

from .hunt_candidates import EX_WALL, WorldSource, source_route_requires_flight
from .archetypes import archetype_registry


ROOM_INDOORS = 1 << 3


def companion_finishing_blow(text: str, *, target: str, companion: str = "the pony") -> bool:
    """Recognize the source damage/death pair, not an unawarded generic death."""
    lines = [" ".join(line.casefold().split()) for line in text.splitlines() if line.strip()]
    name = " ".join(target.casefold().split())
    for index in range(len(lines) - 1, 0, -1):
        if re.fullmatch(rf"{re.escape(name)} is dead!+", lines[index]):
            attack = lines[index - 1]
            return bool(
                attack.startswith(companion.casefold() + " ")
                and re.search(rf"\b{re.escape(name)}[.!]+$", attack)
                and not any(word in attack for word in (" says ", " tells ", " misses "))
            )
    return False


@dataclass
class FamiliarWithdrawal:
    """An order acknowledgement is not proof that the NPC actually fled."""

    selector: str | None = None
    name: str = "the pony"
    settle_in_place: bool = False
    sleeping_attempts: int = 0
    last_order: str | None = None
    attempts: int = 0
    deadline: float | None = None
    acknowledged_at: float | None = None
    confirmed: bool = False
    failure: str | None = None
    buffer: str = ""

    @property
    def pending(self) -> bool:
        return self.attempts > 0 and not self.confirmed and self.failure is None

    def observe(self, text: str, *, now: float) -> None:
        if not self.attempts or self.confirmed:
            return
        self.buffer = (self.buffer + text)[-2_000:]
        lines = {" ".join(line.casefold().split()) for line in self.buffer.splitlines()}
        if f"{self.name.casefold()} has fled!" in lines or (
            self.settle_in_place and self.last_order == "sleep"
            and f"{self.name.casefold()} sleeps." in lines
        ):
            self.confirmed = True
            self.failure = None
        if "ok." in lines and self.acknowledged_at is None:
            self.acknowledged_at = now
        if lines & {"they aren't here.", "do it yourself!", "you have no followers here."}:
            self.failure = "withdrawal order refused"

    def next_command(self, *, now: float) -> str | None:
        if self.confirmed or self.failure:
            return None
        if not self.selector or not re.fullmatch(r"#\d+", self.selector):
            self.failure = "missing exact companion identity"
            return None
        if self.deadline is None:
            self.deadline = now + 10
        if now >= self.deadline:
            self.failure = "withdrawal confirmation deadline expired"
            return None
        if self.attempts:
            # do_order calls interpret before emitting Ok. The departure, if
            # any, therefore precedes this acknowledgement on the same stream.
            # No player WAIT_STATE follows order; do not wait for another tick.
            if self.acknowledged_at is None:
                return None
            if self.settle_in_place and self.last_order == "flee":
                # Charm prevents leaving the master. Flee may still stop
                # fighting before movement fails; positive sleep proves this.
                self.sleeping_attempts += 1
                self.last_order = "sleep"
                self.acknowledged_at = None
                self.buffer = ""
                return f"order {self.selector} sleep"
            if self.attempts >= 3:
                self.failure = "three withdrawal attempts lacked confirmation"
                return None
        self.attempts += 1
        self.last_order = "flee"
        self.acknowledged_at = None
        self.buffer = ""
        return f"order {self.selector} flee"

    def evidence(self) -> dict[str, object]:
        return {
            "attempts": self.attempts, "confirmed": self.confirmed, "failure": self.failure,
            "control": "sleep" if self.settle_in_place else "departure",
            "sleeping_attempts": self.sleeping_attempts,
        }


def learned_familiar_available(
    character_class: str, subclass: str | None, skills: Mapping[str, object],
) -> bool:
    """Authorize the source mage/witch paths, not arbitrary observed names."""
    if not isinstance(skills, Mapping):
        return False
    subclass = str(subclass or "").strip().casefold()
    if subclass == "none":
        subclass = ""
    registry = archetype_registry()
    try:
        base = registry.class_profile(character_class).name
        if subclass:
            profile = registry.subclass_profile(subclass)
            if profile.base_class != base or not profile.available:
                return False
    except ValueError:
        return False
    percent = skills.get("summon familiar")
    return bool(
        (base == "mage" or subclass == "witch")
        and type(percent) is int and 0 < percent <= 100
    )


def familiar_staging_room(
    world: WorldSource,
    route_rooms: Sequence[int],
    search_rooms: Collection[int],
) -> int | None:
    """Find an outdoor no-mob waypoint with a proven ordinary follower path."""
    if not route_rooms or not search_rooms:
        return None
    for index in range(len(route_rooms) - 1, -1, -1):
        room = world.rooms.get(route_rooms[index])
        if (
            room is None or not room.no_mob or room.room_flags & ROOM_INDOORS
            or room.sector_type not in {1, 2, 3, 4, 5, 10}
        ):
            continue
        following = tuple(route_rooms[index:])
        visited = set(following) | set(search_rooms)
        if any(
            (destination := world.rooms.get(vnum)) is None
            or destination.random_exits
            or destination.sector_type not in {0, 1, 2, 3, 4, 5, 10}
            for vnum in visited
        ):
            continue
        if source_route_requires_flight(world, following):
            continue
        if any(
            not any(edge.destination == destination for edge in world.rooms[origin].exits.values())
            for origin, destination in zip(following, following[1:])
        ):
            continue
        # Wandering targets can move to any audited search room. Do not
        # promise follower continuity across a wall, portal, or unknown edge.
        if any(
            exit_source.flags & EX_WALL
            for vnum in visited
            for exit_source in world.rooms[vnum].exits.values()
            if exit_source.destination in visited
        ):
            continue
        if any(reset.room_vnum == room.vnum for reset in world.mob_resets):
            continue
        return room.vnum
    return None


@dataclass
class FamiliarPreparation:
    """Bounded summon/identify/group sequence with positive ownership proof."""

    stage: str = "idle"
    selector: str | None = None
    summoned: bool = False
    grouped: bool = False
    failure: str | None = None
    buffer: str = ""
    order_pending: bool = False
    order_confirmed: bool = False
    attempts: int = 0
    recitation_failed: bool = False
    deadline: float | None = None

    def observe(self, text: str) -> None:
        if self.stage not in {"summoning", "grouping"} and not self.order_pending:
            return
        self.buffer = (self.buffer + text)[-2_000:]
        lines = {" ".join(line.casefold().split()) for line in self.buffer.splitlines()}
        if self.stage == "summoning":
            self.summoned = self.summoned or (
                "you raise your hands and the form of the pony appears before you."
                in lines
            )
            self.recitation_failed = bool(lines & {
                "you fail to correctly recite the spell!",
                "you lost your concentration.", "you lose your concentration.",
            })
        elif self.stage == "grouping":
            self.grouped = self.grouped or "the pony joins your group." in lines
        elif self.order_pending:
            self.order_confirmed = self.order_confirmed or "ok." in lines

    def expect_order(self) -> None:
        self.buffer = ""
        self.order_pending = True
        self.order_confirmed = False

    def evidence(self) -> dict[str, object]:
        return {
            "stage": self.stage, "selector": self.selector,
            "summoned": self.summoned, "grouped": self.grouped,
            "order_confirmed": self.order_confirmed, "failure": self.failure,
            "attempts": self.attempts,
        }

    def next_command(
        self, selectors: Mapping[str, str], description: str, *,
        mana: int | None = None, now: float | None = None,
    ) -> str | None:
        if self.failure or self.stage == "ready":
            return None
        now = time.monotonic() if now is None else now
        if self.deadline is None:
            self.deadline = now + 30
        if now >= self.deadline:
            self.failure = "familiar preparation exceeded its confirmation deadline"
            return None
        if self.stage == "idle" or (
            self.stage == "summoning" and self.recitation_failed and not self.summoned
        ):
            if self.attempts >= 3:
                self.failure = "summon familiar exhausted three recitation attempts"
                return None
            # const.c minimum mana is 100; do_cast failures consume half.
            if mana is None or mana < 100:
                self.failure = "insufficient observed mana for summon familiar"
                return None
            self.attempts += 1
            self.buffer = ""
            self.recitation_failed = False
            self.stage = "summoning"
            return "cast 'summon familiar'"
        if self.stage == "summoning":
            if not self.summoned:
                self.failure = "summon familiar was not positively confirmed"
                return None
            self.stage = "identifying"
            return "look"
        if self.stage == "identifying":
            matches = [
                selector for selector, observed in selectors.items()
                if observed == description and re.fullmatch(r"#\d+", selector)
            ]
            if len(matches) != 1:
                self.failure = "summoned familiar identity is missing or ambiguous"
                return None
            self.selector = matches[0]
            self.stage = "grouping"
            self.buffer = ""
            return f"group {self.selector}"
        if self.stage == "grouping":
            if not self.grouped:
                self.failure = "familiar group ownership was not positively confirmed"
                return None
            self.stage = "ready"
        return None

    def present(self, selectors: Mapping[str, str], description: str) -> bool:
        return bool(
            self.stage == "ready" and self.grouped and self.selector
            and selectors.get(self.selector) == description
        )
