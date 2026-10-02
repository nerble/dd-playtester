"""Source-bounded preparation and positive ownership proof for field companions."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Collection, Mapping, Sequence

from .hunt_candidates import (
    EX_WALL, SAFE_NONCOMBAT_SPECIALS, WorldSource,
    source_mobile_can_join_player_fight, source_mobile_search_rooms,
    source_route_requires_flight,
)
from .archetypes import archetype_registry
from .observations import _DD4_PROMPT, _EXITS


_ANSI_ESCAPE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
_MUD_COLOUR_CODE = re.compile(r"(?:\{.|<\d+>)")
_TARGETMODE_SELECTOR = re.compile(
    r"^\s*\[#(?P<target_id>\d+)\]\s*(?P<description>.*)$"
)
_MOBILE_STATUS_PREFIX = re.compile(r"^(?:(?:\([^)]*\)|<[^>\r\n]*>)\s*)+")
ROOM_INDOORS = 1 << 3
FAMILIAR_XP_CREDIT_SUBCLASSES = frozenset({
    "witch", "infernalist", "necromancer", "knight", "werewolf",
})


def familiar_withdrawal_rooms_safe(
    world: WorldSource,
    room_vnums: Collection[int],
    *,
    character_level: int | None = None,
    character_alignment: int | None = None,
    additional_mobile_vnums: Collection[int] = (),
) -> bool:
    """Audit every random flee destination before planning or ordering a pet."""
    familiar = world.mobiles.get(19900)
    if familiar is None or not room_vnums:
        return False
    destinations: set[int] = set()
    for room_vnum in room_vnums:
        room = world.rooms.get(room_vnum)
        if room is None:
            return False
        exits = {
            destination.vnum
            for exit_source in room.exits.values()
            if not exit_source.closed
            and (destination := world.rooms.get(exit_source.destination)) is not None
            and not destination.no_mob
            and (not familiar.stay_area or destination.area_file == room.area_file)
        }
        if not exits:
            return False
        destinations.update(exits)

    direct = {
        reset.mobile_vnum for reset in world.mob_resets
        if reset.room_vnum in destinations
    } | set(additional_mobile_vnums)
    possible = direct | {reset.mobile_vnum for reset in world.mob_resets}
    for mobile_vnum in sorted(possible):
        mobile = world.mobiles.get(mobile_vnum)
        if mobile is None:
            if mobile_vnum in direct:
                return False
            continue
        unsafe = (
            mobile.aggressive
            or mobile.attack_programs
            or any(
                str(special).strip().casefold() not in SAFE_NONCOMBAT_SPECIALS
                for special in world.mobile_specials.get(mobile_vnum, ())
            )
            or source_mobile_can_join_player_fight(
                world, mobile, character_level=character_level,
                character_alignment=character_alignment,
            )
        )
        if not unsafe:
            continue
        if mobile_vnum in direct:
            return False
        # Match the runtime identity map, including doors a player may open.
        # The eight-room target search limit must not truncate this hazard map.
        if mobile.wanders and not destinations.isdisjoint(
            source_mobile_search_rooms(world, mobile_vnum, include_closed=True)
        ):
            return False
    return True


def _live_selector_matches(text: str, description: str) -> tuple[str, ...]:
    """Extract exact numbered mobiles from the fresh room listing."""
    clean = _MUD_COLOUR_CODE.sub("", _ANSI_ESCAPE.sub("", text))
    expected = " ".join(description.casefold().split())
    matches: list[str] = []
    for line in clean.splitlines():
        selector = _TARGETMODE_SELECTOR.match(line)
        if selector is None:
            continue
        observed = _MOBILE_STATUS_PREFIX.sub("", selector.group("description")).strip()
        if " ".join(observed.casefold().split()) == expected:
            matches.append(f"#{selector.group('target_id')}")
    return tuple(matches)


def familiar_kill_credits_owner_xp(character_class: str, subclass: str | None) -> bool:
    """Mirror DD4's source whitelist for XP when a familiar lands the kill."""
    base = " ".join(str(character_class or "").casefold().replace("_", " ").split())
    subclass_name = " ".join(str(subclass or "").casefold().replace("_", " ").split())
    if subclass_name == "none":
        subclass_name = ""
    return subclass_name in FAMILIAR_XP_CREDIT_SUBCLASSES or (
        base in {"shape shifter", "shifter"} and not subclass_name
    )


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
class FamiliarStandby:
    """One acknowledged sleep/stand exchange, scoped to an owned companion."""

    selector: str
    room_vnum: str
    stage: str = "idle"
    deadline: float | None = None
    buffer: str = ""
    failure: str | None = None

    def command(self, *, wake: bool, now: float) -> str | None:
        if self.failure:
            return None
        if re.fullmatch(r"#\d+", self.selector) is None:
            self.failure = "missing exact companion selector"
            return None
        if self.stage in {"sleeping", "waking"}:
            if self.deadline is not None and now >= self.deadline:
                self.failure = "companion standby acknowledgement timed out"
            return None
        if (wake and self.stage != "asleep") or (not wake and self.stage != "idle"):
            return None
        self.stage = "waking" if wake else "sleeping"
        self.deadline = now + 5
        self.buffer = ""
        return f"order {self.selector} {'stand' if wake else 'sleep'}"

    def expire(self, now: float) -> None:
        if self.stage in {"sleeping", "waking"} and self.deadline is not None and now >= self.deadline:
            self.failure = "companion standby acknowledgement timed out"

    def observe(self, text: str, *, now: float) -> None:
        self.expire(now)
        if self.failure:
            return
        self.buffer = (self.buffer + text)[-2000:]
        lines = [line.strip().casefold() for line in self.buffer.splitlines()]
        if set(lines) & {"they aren't here.", "do it yourself!", "you have no followers here."}:
            self.failure = "companion standby order refused"
            return
        if self.stage == "sleeping" and "the pony sleeps." in lines:
            self.stage = "asleep"
        elif self.stage == "waking" and any(
            re.fullmatch(r"the pony wakes and readies (?:him|her|it)self for action\.", line)
            for line in lines
        ):
            self.stage = "awake"


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
        if (
            not self.settle_in_place
            and f"{self.name.casefold()} has fled!" in lines
        ) or (
            self.settle_in_place
            and self.last_order == "sleep"
            and f"{self.name.casefold()} sleeps." in lines
        ):
            self.confirmed = True
            self.failure = None
        if (
            any(re.match(r"^ok\.(?:\s|$)", line) for line in lines)
            and self.acknowledged_at is None
        ):
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
            self.deadline = now + 5
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
        # DD4's Fear argument bypasses the NPC random no-op. Uncharmed
        # companions can confirm by leaving; callers mark source-charmed
        # familiars to require positive in-place sleep evidence instead.
        return f"order {self.selector} flee Fear"

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
    listing_started: bool = False
    listing_complete: bool = False
    group_room: str | None = None
    last_present_room: str | None = None

    @property
    def pending(self) -> bool:
        return self.stage in {"summoning", "identifying", "grouping"} and not self.failure

    def expire(self, now: float) -> None:
        if self.pending and self.deadline is not None and now >= self.deadline:
            self.failure = "familiar preparation exceeded its confirmation deadline"

    def observe(self, text: str, *, now: float | None = None) -> None:
        self.expire(time.monotonic() if now is None else now)
        if self.failure or (not self.pending and not self.order_pending):
            return
        received = self.buffer + text
        self.buffer = received[-2_000:]
        # A server prompt need not end with a newline before the next reply.
        lines = {
            " ".join(line.casefold().split())
            for line in _DD4_PROMPT.sub("\n", self.buffer).splitlines()
        }
        if self.stage == "summoning":
            self.summoned = self.summoned or (
                "you raise your hands and the form of the pony appears before you."
                in lines
            )
            self.recitation_failed = bool(lines & {
                "you fail to correctly recite the spell!",
                "you lost your concentration.", "you lose your concentration.",
            })
            if lines & {
                "you don't have enough mana.",
                "you can't summon a familiar indoors.",
                "you can't summon a familiar underwater.",
            }:
                self.failure = "summon familiar was explicitly refused"
        elif self.stage == "identifying":
            if not self.listing_started:
                header = next((line for line in received.splitlines() if _EXITS.fullmatch(line.strip())), None)
                if header is not None:
                    # Discard any world-tick prompt preceding the requested look.
                    self.buffer = received[received.index(header):][-2_000:]
                    self.listing_started = True
            self.listing_complete = self.listing_started and bool(_DD4_PROMPT.search(self.buffer))
        elif self.stage == "grouping":
            self.grouped = self.grouped or "the pony joins your group." in lines
            if lines & {
                "they aren't here.", "the pony isn't following you.",
                "the pony cannot join your group.",
                "but you are following someone else!",
                "you can't have any more npcs in your group.",
                "you remove the pony from your group.",
            }:
                self.failure = "familiar group ownership was explicitly refused"
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
            "group_room": self.group_room,
            "order_confirmed": self.order_confirmed, "failure": self.failure,
            "attempts": self.attempts,
        }

    def next_command(
        self, selectors: Mapping[str, str], description: str, *,
        mana: int | None = None, now: float | None = None,
        room_vnum: str | None = None,
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
                return None
            self.stage = "identifying"
            self.buffer = ""
            self.listing_started = self.listing_complete = False
            return "look"
        if self.stage == "identifying":
            if not self.listing_complete:
                return None
            matches = [
                selector for selector, observed in selectors.items()
                if observed == description and re.fullmatch(r"#\d+", selector)
            ]
            if not matches:
                matches = list(_live_selector_matches(self.buffer, description))
            if len(matches) != 1:
                self.failure = "summoned familiar identity is missing or ambiguous"
                return None
            self.selector = matches[0]
            self.group_room = str(room_vnum) if room_vnum is not None else None
            self.stage = "grouping"
            self.buffer = ""
            return f"group {self.selector}"
        if self.stage == "grouping":
            if not self.grouped:
                return None
            self.stage = "ready"
        return None

    def present(
        self,
        selectors: Mapping[str, str],
        description: str,
        *,
        room_text: str = "",
        room_vnum: str | None = None,
    ) -> bool:
        if self.stage != "ready" or not self.grouped or not self.selector:
            return False
        room_key = str(room_vnum) if room_vnum is not None else None
        if room_key is not None and room_key == self.last_present_room:
            return True
        indexed = [
            selector for selector, observed in selectors.items()
            if observed == description and re.fullmatch(r"#\d+", selector)
        ]
        visible = _live_selector_matches(room_text, description)
        if indexed:
            matches = tuple(indexed)
        else:
            matches = visible
        if room_key is not None and room_key == self.group_room:
            self.last_present_room = room_key
            return True
        if matches == (self.selector,):
            if room_key is not None:
                self.last_present_room = room_key
            return True
        return False
