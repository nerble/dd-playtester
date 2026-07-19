"""Source-backed low-level hunt candidate discovery and risk scoring."""

from __future__ import annotations

import heapq
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping


ACT_SENTINEL = 1 << 1
ACT_AGGRESSIVE = 1 << 5
ACT_NO_EXPERIENCE = 1 << 24

ITEM_TREASURE = 8
ITEM_WEAPON = 5
ITEM_ARMOR = 9
ITEM_CONTAINER = 15
ITEM_MONEY = 20

RECALL_VNUM = 3001
LOW_LEVEL_AREA_FILES = (
    "foundry.are",
    "gremlinlair.are",
    "circus.are",
    "midennir.are",
    "dwarven_home.are",
)

_DIRECTIONS = {
    0: "north",
    1: "east",
    2: "south",
    3: "west",
    4: "up",
    5: "down",
}
_TILDE_VALUE = re.compile(r"(-?\d+)")


@dataclass(frozen=True)
class MobileSource:
    vnum: int
    keywords: str
    short_description: str
    level: int
    act_flags: int
    alignment: int
    area_file: str

    @property
    def aggressive(self) -> bool:
        return bool(self.act_flags & ACT_AGGRESSIVE)

    @property
    def sentinel(self) -> bool:
        return bool(self.act_flags & ACT_SENTINEL)


@dataclass(frozen=True)
class ObjectSource:
    vnum: int
    keywords: str
    short_description: str
    item_type: int
    values: tuple[int, ...]
    source_cost: int


@dataclass(frozen=True)
class ExitSource:
    direction: str
    destination: int
    flags: int
    key_vnum: int
    reset_state: int = 0

    @property
    def locked(self) -> bool:
        return self.reset_state >= 2 or bool(self.flags & 4)

    @property
    def closed(self) -> bool:
        return self.reset_state >= 1 or bool(self.flags & 2)


@dataclass
class RoomSource:
    vnum: int
    name: str
    area_file: str
    exits: dict[str, ExitSource] = field(default_factory=dict)
    random_exits: bool = False


@dataclass(frozen=True)
class MobReset:
    mobile_vnum: int
    room_vnum: int
    maximum_count: int
    object_vnums: tuple[int, ...]


@dataclass
class AreaSource:
    path: Path
    mobiles: dict[int, MobileSource]
    objects: dict[int, ObjectSource]
    rooms: dict[int, RoomSource]
    mob_resets: list[MobReset]
    container_contents: dict[int, list[int]]
    mobile_specials: dict[int, tuple[str, ...]]


@dataclass
class WorldSource:
    mobiles: dict[int, MobileSource] = field(default_factory=dict)
    objects: dict[int, ObjectSource] = field(default_factory=dict)
    rooms: dict[int, RoomSource] = field(default_factory=dict)
    mob_resets: list[MobReset] = field(default_factory=list)
    container_contents: dict[int, list[int]] = field(default_factory=dict)
    mobile_specials: dict[int, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class HuntCandidate:
    status: str
    score: float
    area_file: str
    mobile_vnum: int
    target: str
    target_keyword: str
    level: int
    room_vnum: int
    room_name: str
    route: tuple[str, ...]
    source_instance_limit: int
    room_spawn_count: int
    boot_kills: int
    loot: tuple[str, ...]
    source_value: int
    contained_coins: int
    hazards: tuple[str, ...]


def load_world_source(area_directory: Path) -> WorldSource:
    """Parse global route hazards and target-area loot evidence from DD4 source."""
    if not area_directory.is_dir():
        raise FileNotFoundError(f"DD4 area directory not found: {area_directory}")

    world = WorldSource()
    target_files = set(LOW_LEVEL_AREA_FILES)
    for path in sorted(area_directory.glob("*.are")):
        is_target = path.name in target_files
        parsed = parse_area_file(
            path,
            include_resets=True,
            include_entities=True,
            include_objects=is_target,
        )
        world.mobiles.update(parsed.mobiles)
        world.objects.update(parsed.objects)
        world.rooms.update(parsed.rooms)
        world.mob_resets.extend(parsed.mob_resets)
        world.mobile_specials.update(parsed.mobile_specials)
        for container, contents in parsed.container_contents.items():
            world.container_contents.setdefault(container, []).extend(contents)
    return world


def parse_area_file(
    path: Path,
    *,
    include_resets: bool = True,
    include_entities: bool = True,
    include_objects: bool | None = None,
) -> AreaSource:
    lines = path.read_text(encoding="latin-1").splitlines()
    sections = _section_ranges(lines)
    mobiles = (
        _parse_mobiles(lines, sections.get("#MOBILES"), path.name)
        if include_entities
        else {}
    )
    if include_objects is None:
        include_objects = include_entities
    objects = (
        _parse_objects(lines, sections.get("#OBJECTS"))
        if include_objects
        else {}
    )
    rooms = _parse_rooms(lines, sections.get("#ROOMS"), path.name)
    mob_resets: list[MobReset] = []
    container_contents: dict[int, list[int]] = {}
    mobile_specials: dict[int, tuple[str, ...]] = {}
    if include_resets:
        mob_resets, container_contents = _parse_resets(
            lines,
            sections.get("#RESETS"),
            rooms,
        )
        mobile_specials = _parse_mobile_specials(
            lines,
            sections.get("#SPECIALS"),
        )
    return AreaSource(
        path,
        mobiles,
        objects,
        rooms,
        mob_resets,
        container_contents,
        mobile_specials,
    )


def rank_hunt_candidates(
    world: WorldSource,
    *,
    character_level: int,
    boot_kill_counts: Mapping[str, int] | None = None,
) -> list[HuntCandidate]:
    if character_level < 1:
        raise ValueError("character_level must be at least 1")
    kill_counts = {
        _normalize_name(name): count for name, count in (boot_kill_counts or {}).items()
    }
    resets_by_room = _resets_by_room(world)
    candidate_area_files = set(LOW_LEVEL_AREA_FILES)
    area_aggressors = _area_wandering_aggressors(
        world,
        {room.area_file for room in world.rooms.values()},
    )
    ranked: list[HuntCandidate] = []

    for reset, room_spawn_count in _aggregate_mob_resets(world.mob_resets):
        mobile = world.mobiles.get(reset.mobile_vnum)
        room = world.rooms.get(reset.room_vnum)
        if mobile is None or room is None or mobile.area_file not in candidate_area_files:
            continue
        if mobile.level > character_level or mobile.act_flags & ACT_NO_EXPERIENCE:
            continue

        loot_objects = _loot_objects(world, reset.object_vnums)
        sellable = [
            item
            for item in loot_objects
            if item.item_type in {ITEM_WEAPON, ITEM_ARMOR, ITEM_TREASURE}
        ]
        contained_coins = sum(
            item.values[0] if item.values else 0
            for item in loot_objects
            if item.item_type == ITEM_MONEY
        )
        if not sellable and contained_coins <= 0:
            continue

        path = _shortest_path(world.rooms, RECALL_VNUM, reset.room_vnum)
        if path is None:
            continue
        route, path_rooms, closed_doors = path
        hazards: list[str] = []
        dangerous = False
        normalized_target = _normalize_name(mobile.short_description)
        boot_kills = kill_counts.get(normalized_target, 0)

        for path_room in path_rooms[:-1]:
            for path_reset in resets_by_room.get(path_room, ()):
                hazard = world.mobiles.get(path_reset.mobile_vnum)
                if hazard is None or not hazard.aggressive:
                    continue
                hazards.append(
                    f"route: {hazard.short_description} L{hazard.level} in {path_room}"
                )
                if hazard.level > character_level:
                    dangerous = True

        for area_file in {
            world.rooms[path_room].area_file
            for path_room in path_rooms
            if path_room in world.rooms
        }:
            for hazard in area_aggressors.get(area_file, ()):
                if hazard.vnum == mobile.vnum:
                    continue
                hazards.append(
                    f"route-area wanderer: {hazard.short_description} L{hazard.level}"
                )
                if hazard.level > character_level:
                    dangerous = True

        if closed_doors:
            hazards.append(f"{closed_doors} closed door(s) on route")
        if mobile.alignment > 0:
            hazards.append(f"positive alignment target ({mobile.alignment})")
        if mobile.aggressive:
            hazards.append("target is aggressive")
        for special in world.mobile_specials.get(mobile.vnum, ()):
            hazards.append(f"target special: {special}")
        if boot_kills >= reset.maximum_count:
            hazards.append(
                "current-boot kills meet the mobile instance limit; "
                "leave the area and await its faster unoccupied reset"
            )

        source_value = sum(item.source_cost for item in sellable)
        score = (
            100
            + mobile.level * 7
            + len({item.vnum for item in sellable}) * 16
            + min(source_value, 500) / 10
            + min(contained_coins, 100) / 2
            + min(room_spawn_count, 5) * 4
            - len(route) * 1.5
            - boot_kills * 15
            - max(mobile.alignment, 0) / 25
            - len(hazards) * 4
        )
        status = "reject" if dangerous else "caution" if hazards else "promising"
        if mobile.alignment > 0:
            status = "reject" if mobile.alignment >= 500 else "caution"

        ranked.append(
            HuntCandidate(
                status=status,
                score=round(score, 1),
                area_file=mobile.area_file,
                mobile_vnum=mobile.vnum,
                target=mobile.short_description,
                target_keyword=mobile.keywords.split()[0],
                level=mobile.level,
                room_vnum=room.vnum,
                room_name=room.name,
                route=route,
                source_instance_limit=reset.maximum_count,
                room_spawn_count=room_spawn_count,
                boot_kills=boot_kills,
                loot=tuple(item.short_description for item in sellable),
                source_value=source_value,
                contained_coins=contained_coins,
                hazards=tuple(dict.fromkeys(hazards)),
            )
        )

    status_order = {"promising": 0, "caution": 1, "reject": 2}
    return sorted(
        ranked,
        key=lambda candidate: (
            status_order[candidate.status],
            -candidate.score,
            candidate.area_file,
            candidate.room_vnum,
            candidate.mobile_vnum,
        ),
    )


def _section_ranges(lines: list[str]) -> dict[str, tuple[int, int]]:
    starts = [
        (index, line.strip())
        for index, line in enumerate(lines)
        if line.strip().startswith("#") and not line.strip()[1:].isdigit()
    ]
    ranges: dict[str, tuple[int, int]] = {}
    for position, (index, name) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        ranges.setdefault(name, (index + 1, end))
    return ranges


def _parse_mobiles(
    lines: list[str],
    bounds: tuple[int, int] | None,
    area_file: str,
) -> dict[int, MobileSource]:
    mobiles: dict[int, MobileSource] = {}
    if bounds is None:
        return mobiles
    index, end = bounds
    while index < end:
        marker = lines[index].strip()
        if marker == "#0":
            break
        if not _is_vnum_marker(marker):
            index += 1
            continue
        vnum = int(marker[1:])
        index += 1
        keywords, index = _read_tilde(lines, index, end)
        short_description, index = _read_tilde(lines, index, end)
        _, index = _read_tilde(lines, index, end)
        _, index = _read_tilde(lines, index, end)
        if index + 1 >= end:
            break
        flag_parts = lines[index].split()
        index += 1
        combat_parts = lines[index].split()
        index += 1
        if (
            len(flag_parts) < 3
            or not combat_parts
            or not _all_ints((flag_parts[2], combat_parts[0]))
        ):
            # Mob programs can contain ``#<vnum>`` references that are not
            # mobile records. Skip them unless their expected numeric header is present.
            index = _next_vnum_marker(lines, index, end)
            continue
        mobiles[vnum] = MobileSource(
            vnum=vnum,
            keywords=_clean_text(keywords),
            short_description=_clean_text(short_description),
            level=int(combat_parts[0]),
            act_flags=_parse_bits(flag_parts[0]),
            alignment=int(flag_parts[2]),
            area_file=area_file,
        )
        index = _next_vnum_marker(lines, index, end)
    return mobiles


def _parse_objects(
    lines: list[str],
    bounds: tuple[int, int] | None,
) -> dict[int, ObjectSource]:
    objects: dict[int, ObjectSource] = {}
    if bounds is None:
        return objects
    index, end = bounds
    while index < end:
        marker = lines[index].strip()
        if marker == "#0":
            break
        if not _is_vnum_marker(marker):
            index += 1
            continue
        vnum = int(marker[1:])
        index += 1
        keywords, index = _read_tilde(lines, index, end)
        short_description, index = _read_tilde(lines, index, end)
        _, index = _read_tilde(lines, index, end)
        _, index = _read_tilde(lines, index, end)
        if index + 2 >= end:
            break
        type_parts = lines[index].split()
        index += 1
        values = tuple(
            int(match.group(1)) for match in _TILDE_VALUE.finditer(lines[index])
        )
        index += 1
        cost_parts = lines[index].split()
        index += 1
        if not type_parts:
            continue
        objects[vnum] = ObjectSource(
            vnum=vnum,
            keywords=_clean_text(keywords),
            short_description=_clean_text(short_description),
            item_type=int(type_parts[0]),
            values=values,
            source_cost=int(cost_parts[1]) if len(cost_parts) > 1 else 0,
        )
        index = _next_vnum_marker(lines, index, end)
    return objects


def _parse_rooms(
    lines: list[str],
    bounds: tuple[int, int] | None,
    area_file: str,
) -> dict[int, RoomSource]:
    rooms: dict[int, RoomSource] = {}
    if bounds is None:
        return rooms
    index, end = bounds
    while index < end:
        marker = lines[index].strip()
        if marker == "#0":
            break
        if not _is_vnum_marker(marker):
            index += 1
            continue
        vnum = int(marker[1:])
        index += 1
        name, index = _read_tilde(lines, index, end)
        _, index = _read_tilde(lines, index, end)
        if index >= end:
            break
        index += 1
        room = RoomSource(vnum, _clean_text(name), area_file)
        while index < end:
            token = lines[index].strip()
            index += 1
            if token == "S":
                break
            if token.startswith("D") and token[1:].isdigit():
                direction_number = int(token[1:])
                _, index = _read_tilde(lines, index, end)
                _, index = _read_tilde(lines, index, end)
                if index >= end:
                    break
                exit_parts = lines[index].split()
                index += 1
                if len(exit_parts) < 3 or direction_number not in _DIRECTIONS:
                    continue
                direction = _DIRECTIONS[direction_number]
                room.exits[direction] = ExitSource(
                    direction,
                    int(exit_parts[2]),
                    int(exit_parts[0]),
                    int(exit_parts[1]),
                )
            elif token == "E":
                _, index = _read_tilde(lines, index, end)
                _, index = _read_tilde(lines, index, end)
        rooms[vnum] = room
    return rooms


def _parse_resets(
    lines: list[str],
    bounds: tuple[int, int] | None,
    rooms: dict[int, RoomSource],
) -> tuple[list[MobReset], dict[int, list[int]]]:
    if bounds is None:
        return [], {}
    index, end = bounds
    pending: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    container_contents: dict[int, list[int]] = {}

    while index < end:
        parts = lines[index].split()
        index += 1
        if not parts:
            continue
        command = parts[0]
        if command == "M" and len(parts) >= 5 and _all_ints(parts[1:5]):
            current = {
                "mobile_vnum": int(parts[2]),
                "maximum_count": int(parts[3]),
                "room_vnum": int(parts[4]),
                "object_vnums": [],
            }
            pending.append(current)
        elif command in {"E", "G"} and current is not None and len(parts) >= 3:
            if _all_ints(parts[1:3]):
                current["object_vnums"].append(int(parts[2]))  # type: ignore[union-attr]
        elif command == "P" and len(parts) >= 5 and _all_ints(parts[1:5]):
            container_contents.setdefault(int(parts[4]), []).append(int(parts[2]))
        elif command == "D" and len(parts) >= 5 and _all_ints(parts[1:5]):
            room_vnum = int(parts[2])
            direction = _DIRECTIONS.get(int(parts[3]))
            room = rooms.get(room_vnum)
            if room is None or direction not in room.exits:
                continue
            previous = room.exits[direction]
            room.exits[direction] = ExitSource(
                previous.direction,
                previous.destination,
                previous.flags,
                previous.key_vnum,
                int(parts[4]),
            )
        elif command == "R" and len(parts) >= 3 and _all_ints(parts[1:3]):
            room = rooms.get(int(parts[2]))
            if room is not None:
                room.random_exits = True

    resets = [
        MobReset(
            mobile_vnum=int(item["mobile_vnum"]),
            room_vnum=int(item["room_vnum"]),
            maximum_count=int(item["maximum_count"]),
            object_vnums=tuple(item["object_vnums"]),  # type: ignore[arg-type]
        )
        for item in pending
    ]
    return resets, container_contents


def _parse_mobile_specials(
    lines: list[str],
    bounds: tuple[int, int] | None,
) -> dict[int, tuple[str, ...]]:
    if bounds is None:
        return {}
    index, end = bounds
    specials: dict[int, list[str]] = {}
    while index < end:
        parts = lines[index].split()
        index += 1
        if (
            len(parts) >= 3
            and parts[0] == "M"
            and _all_ints(parts[1:2])
            and parts[2].startswith("spec_")
        ):
            specials.setdefault(int(parts[1]), []).append(parts[2])
    return {
        mobile_vnum: tuple(dict.fromkeys(values))
        for mobile_vnum, values in specials.items()
    }


def _shortest_path(
    rooms: Mapping[int, RoomSource],
    origin: int,
    destination: int,
) -> tuple[tuple[str, ...], tuple[int, ...], int] | None:
    if origin not in rooms or destination not in rooms:
        return None
    queue: list[tuple[int, int, tuple[str, ...], tuple[int, ...], int]] = [
        (0, origin, (), (origin,), 0)
    ]
    best_cost = {origin: 0}
    while queue:
        cost, room_vnum, commands, visited_rooms, closed_doors = heapq.heappop(queue)
        if room_vnum == destination:
            return commands, visited_rooms, closed_doors
        if cost != best_cost.get(room_vnum):
            continue
        room = rooms[room_vnum]
        for direction, exit_source in sorted(room.exits.items()):
            if exit_source.destination not in rooms or exit_source.locked:
                continue
            door_cost = 1 if exit_source.closed else 0
            random_cost = 20 if room.random_exits else 0
            next_cost = cost + 1 + door_cost + random_cost
            if next_cost >= best_cost.get(exit_source.destination, 1_000_000):
                continue
            best_cost[exit_source.destination] = next_cost
            next_commands = commands
            if exit_source.closed:
                next_commands += (f"open {direction}",)
            next_commands += (direction,)
            heapq.heappush(
                queue,
                (
                    next_cost,
                    exit_source.destination,
                    next_commands,
                    visited_rooms + (exit_source.destination,),
                    closed_doors + door_cost,
                ),
            )
    return None


def _loot_objects(
    world: WorldSource,
    direct_object_vnums: Iterable[int],
) -> list[ObjectSource]:
    found: list[ObjectSource] = []
    visited: set[int] = set()

    def add(vnum: int) -> None:
        if vnum in visited:
            return
        visited.add(vnum)
        item = world.objects.get(vnum)
        if item is not None:
            found.append(item)
        for child in world.container_contents.get(vnum, ()):
            add(child)

    for object_vnum in direct_object_vnums:
        add(object_vnum)
    return found


def _resets_by_room(world: WorldSource) -> dict[int, list[MobReset]]:
    result: dict[int, list[MobReset]] = {}
    for reset in world.mob_resets:
        result.setdefault(reset.room_vnum, []).append(reset)
    return result


def _aggregate_mob_resets(
    resets: Iterable[MobReset],
) -> list[tuple[MobReset, int]]:
    grouped: dict[tuple[int, int], list[MobReset]] = {}
    for reset in resets:
        grouped.setdefault((reset.mobile_vnum, reset.room_vnum), []).append(reset)
    result: list[tuple[MobReset, int]] = []
    for group in grouped.values():
        object_vnums = tuple(
            dict.fromkeys(
                object_vnum
                for reset in group
                for object_vnum in reset.object_vnums
            )
        )
        result.append(
            (
                MobReset(
                    mobile_vnum=group[0].mobile_vnum,
                    room_vnum=group[0].room_vnum,
                    maximum_count=max(reset.maximum_count for reset in group),
                    object_vnums=object_vnums,
                ),
                len(group),
            )
        )
    return result


def _area_wandering_aggressors(
    world: WorldSource,
    area_files: set[str],
) -> dict[str, list[MobileSource]]:
    result: dict[str, list[MobileSource]] = {}
    reset_vnums = {reset.mobile_vnum for reset in world.mob_resets}
    for mobile in world.mobiles.values():
        if (
            mobile.area_file in area_files
            and mobile.vnum in reset_vnums
            and mobile.aggressive
            and not mobile.sentinel
        ):
            result.setdefault(mobile.area_file, []).append(mobile)
    return result


def _read_tilde(
    lines: list[str],
    index: int,
    end: int,
) -> tuple[str, int]:
    parts: list[str] = []
    while index < end:
        line = lines[index]
        index += 1
        if "~" in line:
            before, _, _ = line.partition("~")
            parts.append(before)
            break
        parts.append(line)
    return "\n".join(parts), index


def _next_vnum_marker(lines: list[str], index: int, end: int) -> int:
    while index < end and not _is_vnum_marker(lines[index].strip()):
        index += 1
    return index


def _is_vnum_marker(value: str) -> bool:
    return value.startswith("#") and value[1:].isdigit()


def _parse_bits(value: str) -> int:
    result = 0
    for part in value.split("|"):
        result |= int(part)
    return result


def _all_ints(values: Iterable[str]) -> bool:
    try:
        for value in values:
            int(value)
    except ValueError:
        return False
    return True


def _clean_text(value: str) -> str:
    return " ".join(value.replace("\n", " ").split())


def _normalize_name(value: str) -> str:
    words = value.casefold().split()
    while words and words[0] in {"a", "an", "the"}:
        words.pop(0)
    return " ".join(words)
