"""Source-backed hunt candidate discovery and risk scoring."""

from __future__ import annotations

import heapq
import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Iterable, Mapping


ACT_SENTINEL = 1 << 1
ACT_AGGRESSIVE = 1 << 5
ACT_STAY_AREA = 1 << 6
ACT_NO_EXPERIENCE = 1 << 24

ROOM_NO_MOB = 1 << 2

ITEM_TREASURE = 8
ITEM_WEAPON = 5
ITEM_ARMOR = 9
ITEM_CONTAINER = 15
ITEM_MONEY = 20

RECALL_VNUM = 3001
WEAR_WIELD = 16
WEAR_HOLD = 17
WEAR_DUAL = 18
LOW_LEVEL_AREA_FILES = (
    "air.are",
    "ambush.are",
    "arachnos.are",
    "canyon.are",
    "crystal.are",
    "cult.are",
    "daycare.are",
    "forest.are",
    "foundry.are",
    "fleshmonger.are",
    "gnome.are",
    "grave.are",
    "gremlinlair.are",
    "circus.are",
    "grove.are",
    "haon.are",
    "hood.are",
    "lemmings.are",
    "midennir.are",
    "dwarven_home.are",
    "moria.are",
    "plains_north.are",
    "rats.are",
    "sea_deception.are",
    "sewer.are",
    "shire.are",
    "thalos.are",
    "valley_elves.are",
    "wyvern.are",
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
    room_description: str = ""

    @property
    def aggressive(self) -> bool:
        return bool(self.act_flags & ACT_AGGRESSIVE)

    @property
    def sentinel(self) -> bool:
        return bool(self.act_flags & ACT_SENTINEL)

    @property
    def stay_area(self) -> bool:
        return bool(self.act_flags & ACT_STAY_AREA)


@dataclass(frozen=True)
class ObjectSource:
    vnum: int
    keywords: str
    short_description: str
    item_type: int
    values: tuple[int, ...]
    source_cost: int
    wear_flags: int = 0
    level: int = 0
    affects: tuple[tuple[int, int], ...] = ()
    extra_flags: int = 0
    room_description: str = ""
    weight: int = 0
    load_level_min: int = 0
    load_level_max: int = 0

    @property
    def effective_level(self) -> int:
        """Return the lowest source-backed level at which this object can load."""
        return self.load_level_min or self.level


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
    room_flags: int = 0
    sector_type: int = 0

    @property
    def no_mob(self) -> bool:
        return bool(self.room_flags & ROOM_NO_MOB)


@dataclass(frozen=True)
class MobReset:
    mobile_vnum: int
    room_vnum: int
    maximum_count: int
    object_vnums: tuple[int, ...]
    equipment: tuple[tuple[int, int], ...] = ()


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
    source_spawn_limit: int
    room_spawn_count: int
    boot_kills: int
    loot: tuple[str, ...]
    source_value: int
    contained_coins: int
    hazards: tuple[str, ...]
    equipped_weapons: tuple[str, ...] = ()
    estimated_level_range: tuple[int, int] = (0, 0)
    estimated_base_hp_range: tuple[int, int] = (0, 0)
    estimated_peak_round_damage: int = 0
    autonomy_rejections: tuple[str, ...] = ()

    @property
    def autonomous_safe(self) -> bool:
        """Whether source evidence permits a live probe-to-hunt policy."""
        return not self.autonomy_rejections


def load_world_source(
    area_directory: Path,
    *,
    include_all_areas: bool = False,
) -> WorldSource:
    """Parse global hazards and selected candidate-area loot evidence."""
    if not area_directory.is_dir():
        raise FileNotFoundError(f"DD4 area directory not found: {area_directory}")

    world = WorldSource()
    target_files = (
        {path.name for path in area_directory.glob("*.are")}
        if include_all_areas
        else set(LOW_LEVEL_AREA_FILES)
    )
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


def load_object_sources(area_directory: Path) -> dict[int, ObjectSource]:
    """Load prototypes annotated with reset-derived object level ranges."""
    if not area_directory.is_dir():
        raise FileNotFoundError(f"DD4 area directory not found: {area_directory}")

    objects: dict[int, ObjectSource] = {}
    for path in sorted(area_directory.glob("*.are")):
        parsed = parse_area_file(
            path,
            include_resets=True,
            include_entities=True,
            include_objects=True,
        )
        objects.update(parsed.objects)
    return objects


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
        mob_resets, container_contents, object_load_levels = _parse_resets(
            lines,
            sections.get("#RESETS"),
            rooms,
            mobiles,
            objects,
            school_area=_area_has_special(
                lines,
                sections.get("#AREA_SPECIAL"),
                "school",
            ),
            shopkeepers=_parse_shopkeepers(
                lines,
                sections.get("#SHOPS"),
            ),
        )
        objects = _annotate_object_load_levels(objects, object_load_levels)
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
    include_xp_only: bool = False,
    character_max_hp: int | None = None,
    include_all_areas: bool = False,
) -> list[HuntCandidate]:
    if character_level < 1:
        raise ValueError("character_level must be at least 1")
    kill_counts = {
        _normalize_name(name): count for name, count in (boot_kill_counts or {}).items()
    }
    resets_by_room = _resets_by_room(world)
    candidate_area_files = None if include_all_areas else set(LOW_LEVEL_AREA_FILES)
    wandering_aggressors = _wandering_aggressors(world)
    recall_paths = _shortest_paths_from(world.rooms, RECALL_VNUM)
    wanderer_reachability = {
        (mobile.vnum, reset.room_vnum): _wanderer_reachable_rooms(
            world,
            mobile,
            reset.room_vnum,
        )
        for mobile, reset in wandering_aggressors
    }
    ranked: list[HuntCandidate] = []

    for reset, room_spawn_count in _aggregate_mob_resets(world.mob_resets):
        mobile = world.mobiles.get(reset.mobile_vnum)
        room = world.rooms.get(reset.room_vnum)
        if (
            mobile is None
            or room is None
            or (
                candidate_area_files is not None
                and mobile.area_file not in candidate_area_files
            )
        ):
            continue
        if mobile.level > character_level or mobile.act_flags & ACT_NO_EXPERIENCE:
            continue
        level_range = _mobile_level_range(mobile.level)
        # DD4's do_consider treats a target five or more levels below the
        # character as a forbidden low-XP branch. Keep a target only when its
        # normal reset fuzz can still produce a useful live consideration.
        if level_range[1] <= character_level - 5:
            continue

        loot_objects = _loot_objects(world, reset.object_vnums)
        equipped_weapon_slots = tuple(
            (wear_location, item)
            for wear_location, object_vnum in reset.equipment
            if wear_location in {WEAR_WIELD, WEAR_DUAL}
            and (item := world.objects.get(object_vnum)) is not None
            and item.item_type == ITEM_WEAPON
        )
        equipped_weapons = tuple(item for _, item in equipped_weapon_slots)
        hp_range = _mobile_base_hp_range(level_range)
        peak_round_damage = _mobile_peak_round_damage(
            level_range[1],
            wielding=any(
                wear_location == WEAR_WIELD
                for wear_location, _ in equipped_weapon_slots
            ),
            dual_wielding=any(
                wear_location == WEAR_DUAL
                for wear_location, _ in equipped_weapon_slots
            ),
        )
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
        if not include_xp_only and not sellable and contained_coins <= 0:
            continue

        path = recall_paths.get(reset.room_vnum)
        if path is None:
            continue
        route, path_rooms, closed_doors = path
        hazards: list[str] = []
        autonomy_rejections: list[str] = []
        dangerous = False
        normalized_target = _normalize_name(mobile.short_description)
        boot_kills = kill_counts.get(normalized_target, 0)

        matching_target_capacity = sum(
            room_reset.maximum_count
            for room_reset in resets_by_room.get(room.vnum, ())
            if room_reset.mobile_vnum == mobile.vnum
        )
        if matching_target_capacity > 1:
            hazards.append(
                "target reset permits up to "
                f"{matching_target_capacity} matching mobiles in the room"
            )
            # Same-vnum mobiles can automatically assist each other in
            # violence_update, including before an aggressive room can be
            # inspected. Solo hunt policies must reject this source capacity.
            dangerous = True
            autonomy_rejections.append("target reset capacity exceeds one")
        for room_reset in resets_by_room.get(room.vnum, ()):
            if room_reset.mobile_vnum == mobile.vnum:
                continue
            companion = world.mobiles.get(room_reset.mobile_vnum)
            if companion is None:
                continue
            hazards.append(
                "room companion: "
                f"{companion.short_description} L{companion.level} "
                f"(up to {room_reset.maximum_count})"
            )
            if companion.aggressive or companion.level > character_level:
                dangerous = True
            autonomy_rejections.append("target room has a reset companion")

        for path_room in path_rooms[:-1]:
            for path_reset in resets_by_room.get(path_room, ()):
                hazard = world.mobiles.get(path_reset.mobile_vnum)
                if hazard is None or not hazard.aggressive:
                    continue
                hazards.append(
                    f"route: {hazard.short_description} L{hazard.level} in {path_room}"
                )
                hazard_level_max = _mobile_level_range(hazard.level)[1]
                if hazard_level_max > character_level:
                    dangerous = True
                    autonomy_rejections.append(
                        "route crosses a higher-level aggressive reset"
                    )
                elif hazard_level_max > character_level - 5:
                    autonomy_rejections.append(
                        "route crosses an aggressive reset inside the useful XP band"
                    )

        path_room_set = set(path_rooms)
        for hazard, hazard_reset in wandering_aggressors:
            if (
                hazard.vnum == mobile.vnum
                or hazard_reset.room_vnum in path_room_set
                or path_room_set.isdisjoint(
                    wanderer_reachability[
                        (hazard.vnum, hazard_reset.room_vnum)
                    ]
                )
            ):
                continue
            hazards.append(
                f"reachable wanderer: {hazard.short_description} L{hazard.level}"
            )
            hazard_level_max = _mobile_level_range(hazard.level)[1]
            if hazard_level_max > character_level:
                dangerous = True
                autonomy_rejections.append(
                    "a higher-level aggressive wanderer can reach the route"
                )
            elif hazard_level_max > character_level - 5:
                autonomy_rejections.append(
                    "an aggressive wanderer inside the useful XP band can reach the route"
                )

        if closed_doors:
            hazards.append(f"{closed_doors} closed door(s) on route")
        if mobile.alignment > 0:
            hazards.append(f"positive alignment target ({mobile.alignment})")
            autonomy_rejections.append("target has positive alignment")
        if mobile.aggressive:
            hazards.append("target is aggressive")
            dangerous = True
            autonomy_rejections.append("target is aggressive")
        if equipped_weapons:
            weapon_names = ", ".join(
                item.short_description for item in equipped_weapons
            )
            hazards.append(
                f"target equips {weapon_names} (NPC base damage x1.5 per wielded hit)"
            )
        if (
            character_max_hp is not None
            and character_max_hp > 0
            and peak_round_damage >= character_max_hp
        ):
            hazards.append(
                f"source peak round {peak_round_damage} >= "
                f"character max HP {character_max_hp}"
            )
            dangerous = True
            autonomy_rejections.append("source peak round can exceed character HP")
        for special in world.mobile_specials.get(mobile.vnum, ()):
            hazards.append(f"target special: {special}")
            autonomy_rejections.append(f"target has special procedure {special}")
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
            - len(equipped_weapons) * 24
        )
        status = "reject" if dangerous else "caution" if hazards else "promising"
        if mobile.alignment >= 500:
            status = "reject"
        elif mobile.alignment > 0 and status == "promising":
            status = "caution"

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
                source_spawn_limit=reset.maximum_count,
                room_spawn_count=room_spawn_count,
                boot_kills=boot_kills,
                loot=tuple(item.short_description for item in sellable),
                source_value=source_value,
                contained_coins=contained_coins,
                hazards=tuple(dict.fromkeys(hazards)),
                equipped_weapons=tuple(
                    item.short_description for item in equipped_weapons
                ),
                estimated_level_range=level_range,
                estimated_base_hp_range=hp_range,
                estimated_peak_round_damage=peak_round_damage,
                autonomy_rejections=tuple(dict.fromkeys(autonomy_rejections)),
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
        room_description, index = _read_tilde(lines, index, end)
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
            room_description=_clean_text(room_description),
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
        room_description, index = _read_tilde(lines, index, end)
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
        record_end = _next_vnum_marker(lines, index, end)
        try:
            item_type = int(type_parts[0])
            extra_flags = _parse_bits(type_parts[1]) if len(type_parts) > 1 else 0
            wear_flags = _parse_bits(type_parts[2]) if len(type_parts) > 2 else 0
            source_cost = int(cost_parts[1]) if len(cost_parts) > 1 else 0
            level = int(cost_parts[2]) if len(cost_parts) > 2 else 0
            weight = int(cost_parts[0]) if cost_parts else 0
        except ValueError:
            # Object programs and extended descriptions can contain ``#<vnum>``
            # references. Ignore them unless the expected numeric header follows.
            index = record_end
            continue
        affects: list[tuple[int, int]] = []
        detail_index = index
        while detail_index < record_end:
            if lines[detail_index].strip() != "A":
                detail_index += 1
                continue
            detail_index += 1
            if detail_index >= record_end:
                break
            affect_parts = lines[detail_index].split()
            if len(affect_parts) >= 2 and _all_ints(affect_parts[:2]):
                affects.append((int(affect_parts[0]), int(affect_parts[1])))
            detail_index += 1
        objects[vnum] = ObjectSource(
            vnum=vnum,
            keywords=_clean_text(keywords),
            short_description=_clean_text(short_description),
            item_type=item_type,
            values=values,
            source_cost=source_cost,
            wear_flags=wear_flags,
            level=level,
            affects=tuple(affects),
            extra_flags=extra_flags,
            room_description=_clean_text(room_description),
            weight=weight,
        )
        index = record_end
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
        room_header = lines[index].split()
        index += 1
        room_flags = _parse_bits(room_header[1]) if len(room_header) >= 2 else 0
        sector_type = int(room_header[2]) if len(room_header) >= 3 else 0
        room = RoomSource(
            vnum,
            _clean_text(name),
            area_file,
            room_flags=room_flags,
            sector_type=sector_type,
        )
        while index < end:
            token = lines[index].strip()
            index += 1
            if token == "S":
                break
            direction_match = re.fullmatch(r"D\s*([0-5])", token)
            if direction_match is not None:
                direction_number = int(direction_match.group(1))
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
    mobiles: Mapping[int, MobileSource],
    objects: Mapping[int, ObjectSource],
    *,
    school_area: bool,
    shopkeepers: set[int],
) -> tuple[
    list[MobReset],
    dict[int, list[int]],
    dict[int, list[tuple[int, int]]],
]:
    if bounds is None:
        return [], {}, {}
    index, end = bounds
    pending: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    current_mobile_vnum: int | None = None
    current_level_range: tuple[int, int] | None = None
    container_contents: dict[int, list[int]] = {}
    object_load_levels: dict[int, list[tuple[int, int]]] = {}

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
                "equipment": [],
            }
            pending.append(current)
            current_mobile_vnum = int(parts[2])
            mobile = mobiles.get(current_mobile_vnum)
            current_level_range = (
                _mobile_reset_level_range(mobile.level)
                if mobile is not None
                else None
            )
        elif command in {"E", "G"} and current is not None and len(parts) >= 3:
            if _all_ints(parts[1:3]):
                object_vnum = int(parts[2])
                current["object_vnums"].append(object_vnum)  # type: ignore[union-attr]
                if command == "E" and len(parts) >= 5 and _all_ints(parts[4:5]):
                    current["equipment"].append(  # type: ignore[union-attr]
                        (int(parts[4]), object_vnum)
                    )
                if (
                    current_mobile_vnum not in shopkeepers
                    and current_level_range is not None
                ):
                    loaded_range = _mob_loot_level_range(
                        current_level_range,
                        school_area=school_area,
                    )
                    object_load_levels.setdefault(object_vnum, []).append(
                        loaded_range
                    )
        elif command == "O" and len(parts) >= 5 and _all_ints(parts[1:5]):
            if current_level_range is not None:
                object_load_levels.setdefault(int(parts[2]), []).append(
                    _fuzzy_level_range(current_level_range)
                )
        elif command == "I" and len(parts) >= 5 and _all_ints(parts[1:5]):
            object_load_levels.setdefault(int(parts[1]), []).append(
                _fuzzy_level_range((int(parts[2]), int(parts[2])))
            )
        elif command == "P" and len(parts) >= 5 and _all_ints(parts[1:5]):
            object_vnum = int(parts[2])
            container_vnum = int(parts[4])
            container_contents.setdefault(container_vnum, []).append(object_vnum)
            parent_ranges = object_load_levels.get(container_vnum, ())
            if not parent_ranges:
                parent = objects.get(container_vnum)
                if parent is not None and parent.level > 0:
                    parent_ranges = ((parent.level, parent.level),)
            for parent_range in parent_ranges:
                object_load_levels.setdefault(object_vnum, []).append(
                    _fuzzy_level_range(parent_range)
                )
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
            equipment=tuple(item["equipment"]),  # type: ignore[arg-type]
        )
        for item in pending
    ]
    return resets, container_contents, object_load_levels


def _mobile_reset_level_range(source_level: int) -> tuple[int, int]:
    mobile_min = max(1, source_level - 1)
    mobile_max = max(1, source_level + 1)
    return max(0, mobile_min - 2), max(0, mobile_max - 2)


def _fuzzy_level_range(level_range: tuple[int, int]) -> tuple[int, int]:
    return max(1, level_range[0] - 1), max(1, level_range[1] + 1)


def _mob_loot_level_range(
    reset_level_range: tuple[int, int],
    *,
    school_area: bool,
) -> tuple[int, int]:
    if school_area and reset_level_range[1] <= 5:
        return 1, 1
    return _fuzzy_level_range(reset_level_range)


def _annotate_object_load_levels(
    objects: Mapping[int, ObjectSource],
    ranges: Mapping[int, Iterable[tuple[int, int]]],
) -> dict[int, ObjectSource]:
    annotated = dict(objects)
    for vnum, observed_ranges in ranges.items():
        item = annotated.get(vnum)
        materialized = tuple(observed_ranges)
        if item is None or not materialized:
            continue
        annotated[vnum] = replace(
            item,
            load_level_min=min(level_range[0] for level_range in materialized),
            load_level_max=max(level_range[1] for level_range in materialized),
        )
    return annotated


def _area_has_special(
    lines: list[str],
    bounds: tuple[int, int] | None,
    special: str,
) -> bool:
    if bounds is None:
        return False
    start, end = bounds
    return any(lines[index].strip() == special for index in range(start, end))


def _parse_shopkeepers(
    lines: list[str],
    bounds: tuple[int, int] | None,
) -> set[int]:
    if bounds is None:
        return set()
    start, end = bounds
    shopkeepers: set[int] = set()
    for index in range(start, end):
        parts = lines[index].split()
        if not parts or parts[0] == "0":
            continue
        if parts[0].lstrip("-").isdigit():
            shopkeepers.add(int(parts[0]))
    return shopkeepers


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
    return _shortest_paths_from(rooms, origin).get(destination)


def _shortest_paths_from(
    rooms: Mapping[int, RoomSource],
    origin: int,
) -> dict[int, tuple[tuple[str, ...], tuple[int, ...], int]]:
    if origin not in rooms:
        return {}
    paths: dict[int, tuple[tuple[str, ...], tuple[int, ...], int]] = {}
    queue: list[tuple[int, int, tuple[str, ...], tuple[int, ...], int]] = [
        (0, origin, (), (origin,), 0)
    ]
    best_cost = {origin: 0}
    while queue:
        cost, room_vnum, commands, visited_rooms, closed_doors = heapq.heappop(queue)
        if cost != best_cost.get(room_vnum) or room_vnum in paths:
            continue
        paths[room_vnum] = (commands, visited_rooms, closed_doors)
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
    return paths


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
        equipment = tuple(
            dict.fromkeys(
                equipped
                for reset in group
                for equipped in reset.equipment
            )
        )
        result.append(
            (
                MobReset(
                    mobile_vnum=group[0].mobile_vnum,
                    room_vnum=group[0].room_vnum,
                    maximum_count=max(reset.maximum_count for reset in group),
                    object_vnums=object_vnums,
                    equipment=equipment,
                ),
                len(group),
            )
        )
    return result


def _mobile_level_range(source_level: int) -> tuple[int, int]:
    """Account for source-load and runtime ``number_fuzzy`` calls."""
    return max(1, source_level - 2), source_level + 2


def _mobile_base_hp_range(level_range: tuple[int, int]) -> tuple[int, int]:
    """Mirror the unranked base HP bounds in ``create_mobile``."""
    low, high = level_range
    return (
        low * 8 + low * low // 4,
        high * 8 + high * high,
    )


def _mobile_peak_round_damage(
    level: int,
    *,
    wielding: bool,
    dual_wielding: bool,
) -> int:
    """Return the raw upper bound when every possible NPC strike lands."""
    unarmed_hit = level * 3 // 2 + level // 4
    weapon_hit = unarmed_hit + unarmed_hit // 2
    cycle_damage = weapon_hit if wielding else unarmed_hit
    if dual_wielding:
        cycle_damage += weapon_hit
    possible_attacks = 5 + int(level >= 20)
    return cycle_damage * possible_attacks


def _wandering_aggressors(
    world: WorldSource,
) -> tuple[tuple[MobileSource, MobReset], ...]:
    return tuple(
        (mobile, reset)
        for reset in world.mob_resets
        if (mobile := world.mobiles.get(reset.mobile_vnum)) is not None
        and mobile.aggressive
        and not mobile.sentinel
    )


def _wanderer_can_reach_any(
    world: WorldSource,
    mobile: MobileSource,
    origin: int,
    destinations: set[int],
) -> bool:
    return not destinations.isdisjoint(
        _wanderer_reachable_rooms(world, mobile, origin)
    )


def _wanderer_reachable_rooms(
    world: WorldSource,
    mobile: MobileSource,
    origin: int,
) -> frozenset[int]:
    origin_room = world.rooms.get(origin)
    if origin_room is None:
        return frozenset()
    pending = [origin]
    visited = {origin}
    while pending:
        room_vnum = pending.pop()
        room = world.rooms.get(room_vnum)
        if room is None:
            continue
        for exit_source in room.exits.values():
            destination = world.rooms.get(exit_source.destination)
            if (
                destination is None
                or destination.vnum in visited
                or exit_source.closed
                or exit_source.locked
                or destination.no_mob
                or (
                    mobile.stay_area
                    and destination.area_file != origin_room.area_file
                )
            ):
                continue
            visited.add(destination.vnum)
            pending.append(destination.vnum)
    return frozenset(visited)


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
