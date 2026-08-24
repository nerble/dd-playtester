"""Source-backed hunt candidate discovery and risk scoring."""

from __future__ import annotations

import heapq
import re
from collections import Counter
from dataclasses import dataclass, field, replace
from functools import lru_cache
from pathlib import Path
from typing import Callable, Collection, Iterable, Mapping

from .fastwalks import FASTWALKS, MAP_ROUTES
from .specials import SAFE_NONCOMBAT_SPECIALS, source_special_profile


ACT_SENTINEL = 1 << 1
ACT_AGGRESSIVE = 1 << 5
ACT_STAY_AREA = 1 << 6
ACT_IS_FAMOUS = 1 << 14
ACT_LOSE_FAME = 1 << 15
ACT_DIE_IF_MASTER_GONE = 1 << 21
ACT_NO_EXPERIENCE = 1 << 24

ROOM_NO_MOB = 1 << 2
EX_WALL = 128
SECT_WATER_SWIM = 6
SECT_WATER_NOSWIM = 7
SECT_UNDERWATER = 8
SECT_AIR = 9
SECT_UNDERWATER_GROUND = 12

# These are the sectors for which DD4's movement code makes ordinary land
# travel conditional on flight, swimming, a boat, or a race-specific ability.
# The campaign currently uses flight as its generic, source-backed fallback.
_FLIGHT_OR_WATER_SECTORS = frozenset(
    {
        SECT_WATER_SWIM,
        SECT_WATER_NOSWIM,
        SECT_UNDERWATER,
        SECT_UNDERWATER_GROUND,
    }
)

# ``affected_by`` uses the same bit numbering as the core's ``BIT_*``
# constants.  Confusion is a special case in ``update.c``: it moves a mobile
# even when the prototype is sentinel or stay-area.
AFF_CONFUSION = 1 << 36

ITEM_SCROLL = 2
ITEM_WAND = 3
ITEM_STAFF = 4
ITEM_TREASURE = 8
ITEM_WEAPON = 5
ITEM_ARMOR = 9
ITEM_POTION = 10
ITEM_CONTAINER = 15
ITEM_FOOD = 19
ITEM_MONEY = 20

_CASTABLE_ITEM_TYPES = frozenset({ITEM_SCROLL, ITEM_WAND, ITEM_STAFF})

# ITEM_MONEY stores copper, silver, gold, and platinum in value[0:4].  Keep
# this conversion close to source parsing so candidate ranking cannot mistake
# a multi-denomination stash for a small copper-only drop.
MONEY_DENOMINATION_VALUES = (1, 10, 100, 1000)

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
_MOBILE_TEACHING = re.compile(
    r"^\s*&\s*(?P<percent>\d+)\s+'(?P<skill>[^']+)'\s*$",
    re.IGNORECASE,
)

# This mirrors ``movement_loss`` in DD4's ``server/src/act_move.c``.  Keep
# source route cost separate from command count: terrain, not the direction
# name, determines whether a live route can be completed.
_MOVEMENT_LOSS = (1, 2, 2, 3, 4, 5, 4, 1, 3, 10, 6, 4)

# A single source-proven below-band attacker can be finished as an incidental
# interruption. A large reset crowd is different: it can consume a field
# segment with low-value kills before the useful target is reached.
_MAX_BELOW_BAND_ROUTE_AGGRESSOR_CAPACITY = 4

# A modest detour is worthwhile when it removes a source-proven crowd from a
# route. Keep route planning from replacing a short, unusable path with an
# effectively cross-world journey.
_MAX_SOURCE_ROUTE_DETOUR_STEPS = 20


@dataclass(frozen=True)
class MobileProgram:
    """One source mobile-program trigger and its executable commands."""

    trigger: str
    condition: str = ""
    commands: tuple[str, ...] = ()


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
    affected_flags: int = 0
    programs: tuple[MobileProgram, ...] = ()
    teachings: tuple[tuple[str, int], ...] = ()

    @property
    def aggressive(self) -> bool:
        return bool(self.act_flags & ACT_AGGRESSIVE)

    @property
    def sentinel(self) -> bool:
        return bool(self.act_flags & ACT_SENTINEL)

    @property
    def stay_area(self) -> bool:
        return bool(self.act_flags & ACT_STAY_AREA)

    @property
    def confused(self) -> bool:
        return bool(self.affected_flags & AFF_CONFUSION)

    @property
    def awards_fame(self) -> bool:
        return bool(self.act_flags & ACT_IS_FAMOUS)

    @property
    def costs_fame(self) -> bool:
        return bool(self.act_flags & ACT_LOSE_FAME)

    @property
    def dies_if_master_gone(self) -> bool:
        return bool(self.act_flags & ACT_DIE_IF_MASTER_GONE)

    @property
    def wanders(self) -> bool:
        """Mirror the two mobile movement paths in ``update.c``."""
        return self.confused or (
            not self.sentinel and not self.dies_if_master_gone
        )

    @property
    def attack_programs(self) -> tuple[MobileProgram, ...]:
        """Return programs that can initiate or reinforce autonomous combat."""
        triggers = {
            "all_greet_prog",
            "bribe_prog",
            "fight_prog",
            "greet_prog",
            "rand_prog",
        }
        return tuple(
            program
            for program in self.programs
            if program.trigger in triggers
            and any(
                re.search(r"\bmpkill\b", command, re.IGNORECASE)
                for command in program.commands
            )
        )

    def teaching_percent(self, skill: str) -> int:
        """Return the highest source teaching percentage for ``skill``."""
        target = " ".join(str(skill).casefold().split())
        return max(
            (percent for name, percent in self.teachings if name == target),
            default=0,
        )

    def teaches(self, skill: str, *, minimum_percent: int = 1) -> bool:
        """Return whether the mobile can teach a source-named skill."""
        return self.teaching_percent(skill) >= minimum_percent


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
    value_strings: tuple[str, ...] = ()
    load_level_min: int = 0
    load_level_max: int = 0

    @property
    def effective_level(self) -> int:
        """Return the lowest source-backed level at which this object can load."""
        return self.load_level_min or self.level


@dataclass(frozen=True)
class ObjectSetBonus:
    required_count: int
    location: int
    modifier: int


@dataclass(frozen=True)
class ObjectSetSource:
    vnum: int
    name: str
    description: str
    object_vnums: tuple[int, ...]
    bonuses: tuple[ObjectSetBonus, ...]


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


@dataclass(frozen=True)
class RoomObjectReset:
    """A source ``O`` or ``I`` reset that places an object on the ground."""

    object_vnum: int
    room_vnum: int
    maximum_count: int = 1


@dataclass
class AreaSource:
    path: Path
    mobiles: dict[int, MobileSource]
    objects: dict[int, ObjectSource]
    rooms: dict[int, RoomSource]
    mob_resets: list[MobReset]
    room_object_resets: list[RoomObjectReset]
    container_contents: dict[int, list[int]]
    mobile_specials: dict[int, tuple[str, ...]]
    shopkeepers: frozenset[int] = frozenset()


@dataclass
class WorldSource:
    mobiles: dict[int, MobileSource] = field(default_factory=dict)
    objects: dict[int, ObjectSource] = field(default_factory=dict)
    rooms: dict[int, RoomSource] = field(default_factory=dict)
    mob_resets: list[MobReset] = field(default_factory=list)
    room_object_resets: list[RoomObjectReset] = field(default_factory=list)
    container_contents: dict[int, list[int]] = field(default_factory=dict)
    mobile_specials: dict[int, tuple[str, ...]] = field(default_factory=dict)
    shopkeepers: set[int] = field(default_factory=set)


@dataclass(frozen=True)
class SourceTeacherRoute:
    """A source-reset teacher and the route to its reset room."""

    mobile_vnum: int
    room_vnum: int
    room_name: str
    keyword: str
    source_skill: str
    steps: tuple[tuple[str, str, str], ...]
    open_before: tuple[tuple[str, str], ...] = ()
    wanders: bool = False


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
    target_identity: str = ""
    equipped_weapons: tuple[str, ...] = ()
    estimated_level_range: tuple[int, int] = (0, 0)
    estimated_base_hp_range: tuple[int, int] = (0, 0)
    estimated_peak_round_damage: int = 0
    estimated_min_peak_round_damage: int = 0
    estimated_critical_hit_damage: int = 0
    autonomy_rejections: tuple[str, ...] = ()
    specials: tuple[str, ...] = ()
    route_preflight_room_vnum: str | None = None
    route_preflight_command: str | None = None
    route_preflight_target: str | None = None
    route_preflight_level_range: tuple[int, int] = (0, 0)
    route_preflight_hard_hazard: bool = False
    route_hard_hazard_targets: tuple[str, ...] = ()
    sentinel: bool = False
    stay_area: bool = False
    estimated_move_cost: int = 0
    estimated_flying_move_cost: int = 0
    requires_flight: bool = False
    ground_loot_keywords: tuple[str, ...] = ()
    ground_loot_object_vnums: tuple[int, ...] = ()
    is_coin_stash: bool = False
    is_food_stash: bool = False

    @property
    def autonomous_safe(self) -> bool:
        """Whether source evidence permits a live probe-to-hunt policy."""
        return not self.autonomy_rejections


def money_value(values: Iterable[int]) -> int:
    """Return the copper-equivalent value of a DD4 money object."""
    return sum(
        max(0, int(amount)) * multiplier
        for amount, multiplier in zip(values, MONEY_DENOMINATION_VALUES)
    )


def _encoded_spell_names(item: ObjectSource) -> tuple[str, ...]:
    return tuple(
        value.casefold()
        for value in item.value_strings[1:]
        if value and not value.lstrip("-").isdigit()
    )


def castable_spell_names(item: ObjectSource) -> tuple[str, ...]:
    """Return normalized spells encoded on a scroll, wand, or staff."""
    if item.item_type not in _CASTABLE_ITEM_TYPES:
        return ()
    return _encoded_spell_names(item)


def potion_spell_names(item: ObjectSource) -> tuple[str, ...]:
    """Return normalized source spell names encoded on a potion prototype."""
    if item.item_type != ITEM_POTION:
        return ()
    return _encoded_spell_names(item)


@lru_cache(maxsize=4)
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
        world.room_object_resets.extend(parsed.room_object_resets)
        world.mobile_specials.update(parsed.mobile_specials)
        world.shopkeepers.update(parsed.shopkeepers)
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


def load_object_set_sources(area_directory: Path) -> dict[int, ObjectSetSource]:
    """Load DD4 object sets with their runtime bonus thresholds."""
    if not area_directory.is_dir():
        raise FileNotFoundError(f"DD4 area directory not found: {area_directory}")

    object_sets: dict[int, ObjectSetSource] = {}
    for path in sorted(area_directory.glob("*.are")):
        lines = path.read_text(encoding="latin-1").splitlines()
        bounds = _section_ranges(lines).get("#OBJECT_SETS")
        object_sets.update(_parse_object_sets(lines, bounds))
    return object_sets


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
    room_object_resets: list[RoomObjectReset] = []
    container_contents: dict[int, list[int]] = {}
    mobile_specials: dict[int, tuple[str, ...]] = {}
    shopkeepers = _parse_shopkeepers(
        lines,
        sections.get("#SHOPS"),
    )
    if include_resets:
        (
            mob_resets,
            room_object_resets,
            container_contents,
            object_load_levels,
        ) = _parse_resets(
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
            shopkeepers=shopkeepers,
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
        room_object_resets,
        container_contents,
        mobile_specials,
        frozenset(shopkeepers),
    )


def _bounded_borderline_route_aggressor(
    world: WorldSource,
    reset: MobReset,
    *,
    character_level: int,
    character_max_hp: int | None,
) -> bool:
    """Allow a one-mobile route hazard whose only useful roll is the fringe.

    The live runner still defeats the mobile only when GMCP proves it is in the
    forbidden below-band range. A maximum fuzzy roll at ``level - 4`` follows
    the existing flee-and-return path instead of becoming an implicit target.
    """
    if character_max_hp is None or character_max_hp <= 0:
        return False
    mobile = world.mobiles.get(reset.mobile_vnum)
    if (
        mobile is None
        or not mobile.aggressive
        or mobile.costs_fame
        or mobile.vnum in world.shopkeepers
        or mobile.act_flags & ACT_NO_EXPERIENCE
        or world.mobile_specials.get(mobile.vnum)
    ):
        return False
    source_capacity = max(
        (
            candidate.maximum_count
            for candidate in world.mob_resets
            if candidate.mobile_vnum == mobile.vnum
        ),
        default=0,
    )
    if reset.maximum_count != 1 or source_capacity != 1:
        return False
    maximum_level = _mobile_level_range(mobile.level)[1]
    if maximum_level != character_level - 4:
        return False
    wielding = any(
        wear_location == WEAR_WIELD
        for wear_location, _ in reset.equipment
    )
    dual_wielding = any(
        wear_location == WEAR_DUAL
        for wear_location, _ in reset.equipment
    )
    peak_round_damage = _mobile_peak_round_damage(
        maximum_level,
        wielding=wielding,
        dual_wielding=dual_wielding,
    )
    critical_hit_damage = _mobile_critical_hit_damage(
        maximum_level,
        wielding=wielding or dual_wielding,
    )
    return (
        peak_round_damage < character_max_hp
        and critical_hit_damage < character_max_hp
    )


def rank_hunt_candidates(
    world: WorldSource,
    *,
    character_level: int,
    boot_kill_counts: Mapping[str, int] | None = None,
    boot_kill_counts_by_mobile_vnum: Mapping[int, int] | None = None,
    include_xp_only: bool = False,
    include_below_band: bool = False,
    character_max_hp: int | None = None,
    include_level_ceiling_candidates: bool = False,
    level_ceiling_offset: int | None = None,
    include_all_areas: bool = False,
    required_loot_object_vnums: Collection[int] = (),
) -> list[HuntCandidate]:
    if character_level < 1:
        raise ValueError("character_level must be at least 1")
    if level_ceiling_offset is not None and level_ceiling_offset < 0:
        raise ValueError("level_ceiling_offset must not be negative")
    effective_level_ceiling_offset = (
        1 if level_ceiling_offset is None else int(level_ceiling_offset)
    )
    kill_counts = {
        _normalize_name(name): count for name, count in (boot_kill_counts or {}).items()
    }
    mobile_kill_counts = {
        int(vnum): int(count)
        for vnum, count in (boot_kill_counts_by_mobile_vnum or {}).items()
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
    source_keyword_counts = _source_keyword_counts(world)
    required_loot_vnums = {
        int(object_vnum) for object_vnum in required_loot_object_vnums
    }
    route_hazard_rooms = _route_hazard_rooms(
        world,
        resets_by_room,
        character_level=character_level,
    )
    safe_recall_paths = _shortest_paths_from(
        world.rooms,
        RECALL_VNUM,
        blocked_rooms=route_hazard_rooms - {RECALL_VNUM},
    )
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
        level_ceiling_candidate = (
            include_level_ceiling_candidates
            and character_max_hp is not None
            and character_max_hp > 0
            and character_level < mobile.level
            and mobile.level <= character_level + effective_level_ceiling_offset
        )
        if (
            (mobile.level > character_level and not level_ceiling_candidate)
            or mobile.act_flags & ACT_NO_EXPERIENCE
        ):
            continue
        required_loot_objects = tuple(
            world.objects[object_vnum]
            for object_vnum in reset.object_vnums
            if object_vnum in required_loot_vnums
            and object_vnum in world.objects
        )
        if required_loot_vnums and not required_loot_objects:
            continue
        level_range = _mobile_level_range(mobile.level)
        # DD4's do_consider treats a target five or more levels below the
        # character as a forbidden low-XP branch. Keep a target only when its
        # normal reset fuzz can still produce a useful live consideration.
        if not include_below_band and level_range[1] <= character_level - 5:
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
        equipped_spell_items = tuple(
            item
            for wear_location, object_vnum in reset.equipment
            if wear_location in {WEAR_HOLD, WEAR_WIELD, WEAR_DUAL}
            and (item := world.objects.get(object_vnum)) is not None
            and castable_spell_names(item)
        )
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
        minimum_peak_round_damage = _mobile_peak_round_damage(
            level_range[0],
            wielding=any(
                wear_location == WEAR_WIELD
                for wear_location, _ in equipped_weapon_slots
            ),
            dual_wielding=any(
                wear_location == WEAR_DUAL
                for wear_location, _ in equipped_weapon_slots
            ),
        )
        critical_hit_damage = _mobile_critical_hit_damage(
            level_range[1],
            wielding=bool(equipped_weapon_slots),
        )
        sellable = [
            item
            for item in loot_objects
            if item.item_type in {ITEM_WEAPON, ITEM_ARMOR, ITEM_TREASURE}
        ]
        contained_coins = sum(
            money_value(item.values)
            for item in loot_objects
            if item.item_type == ITEM_MONEY
        )
        if (
            not include_xp_only
            and not sellable
            and contained_coins <= 0
            and not required_loot_objects
        ):
            continue

        path = recall_paths.get(reset.room_vnum)
        if path is None:
            continue
        route, path_rooms, closed_doors = path
        if route_hazard_rooms.intersection(path_rooms[:-1]):
            safe_path = safe_recall_paths.get(reset.room_vnum)
            if (
                safe_path is not None
                and len(safe_path[0])
                <= len(route) + _MAX_SOURCE_ROUTE_DETOUR_STEPS
            ):
                route, path_rooms, closed_doors = safe_path
        estimated_move_cost = source_route_movement_cost(
            world,
            path_rooms,
        )
        estimated_flying_move_cost = source_route_movement_cost(
            world,
            path_rooms,
            flying=True,
        )
        requires_flight = source_route_requires_flight(world, path_rooms)
        (
            route_preflight_room_vnum,
            route_preflight_command,
            route_preflight_target,
            route_preflight_level_range,
            route_preflight_hard_hazard,
            route_hard_hazard_targets,
        ) = _route_preflight_metadata(
            world,
            route,
            character_level=character_level,
        )
        hazards: list[str] = []
        autonomy_rejections: list[str] = []
        dangerous = False
        normalized_target = _normalize_name(mobile.short_description)
        boot_kills = (
            mobile_kill_counts.get(mobile.vnum, 0)
            if boot_kill_counts_by_mobile_vnum is not None
            else kill_counts.get(normalized_target, 0)
        )

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
            companion_level_range = _mobile_level_range(companion.level)
            companion_specials = world.mobile_specials.get(
                companion.vnum,
                (),
            )
            hazards.append(
                "room companion: "
                f"{companion.short_description} L{companion.level} "
                f"(up to {room_reset.maximum_count})"
            )
            companion_is_below_band = (
                companion_level_range[1] <= character_level - 5
            )
            # A source-proven below-band mobile cannot make this useful-band
            # target an unsafe crowd.  This remains true when its special is
            # capable of a bounded nuisance effect; the field runner must
            # finish an unavoidable trivial interruption rather than flee.
            companion_is_trivial = companion_is_below_band or (
                not companion_specials
                and not companion.attack_programs
                and (
                    not companion.aggressive
                    and companion_level_range[1] <= character_level
                )
            )
            if companion_is_trivial:
                hazards.append(
                    "source-backed trivial companion: "
                    f"{companion.short_description}"
                )
                continue
            if (
                companion.aggressive
                or companion_level_range[1] > character_level
                or companion_specials
                or companion.attack_programs
            ):
                dangerous = True
                if companion.attack_programs:
                    hazards.append(
                        "source-backed companion attack program: "
                        f"{companion.short_description}"
                    )
                    autonomy_rejections.append(
                        "target room has a program-triggered attacker"
                    )
                else:
                    autonomy_rejections.append(
                        "target room has a dangerous reset companion"
                    )

        for path_room in path_rooms[:-1]:
            for path_reset in resets_by_room.get(path_room, ()):
                hazard = world.mobiles.get(path_reset.mobile_vnum)
                if hazard is None or not hazard.aggressive:
                    continue
                if _source_mobile_has_safe_noncombat_special(world, hazard.vnum):
                    hazards.append(
                        f"source-backed noncombat route special: "
                        f"{hazard.short_description}"
                    )
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
                    if _bounded_borderline_route_aggressor(
                        world,
                        path_reset,
                        character_level=character_level,
                        character_max_hp=character_max_hp,
                    ):
                        hazards.append(
                            "bounded borderline route aggressor may be defeated "
                            "only on a below-band live roll"
                        )
                    else:
                        autonomy_rejections.append(
                            "route crosses an aggressive reset inside the useful XP band"
                        )
                elif (
                    path_reset.maximum_count
                    > _MAX_BELOW_BAND_ROUTE_AGGRESSOR_CAPACITY
                ):
                    hazards.append(
                        "route crosses a large below-band aggressive reset "
                        f"(up to {path_reset.maximum_count} mobiles)"
                    )
                    dangerous = True
                    autonomy_rejections.append(
                        "route crosses a large below-band aggressive crowd"
                    )

        path_room_set = set(path_rooms)
        for hazard, hazard_reset in wandering_aggressors:
            if _source_mobile_has_safe_noncombat_special(world, hazard.vnum):
                continue
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
                if _bounded_borderline_route_aggressor(
                    world,
                    hazard_reset,
                    character_level=character_level,
                    character_max_hp=character_max_hp,
                ):
                    hazards.append(
                        "bounded borderline aggressive wanderer may be defeated "
                        "only on a below-band live roll"
                    )
                else:
                    autonomy_rejections.append(
                        "an aggressive wanderer inside the useful XP band can reach the route"
                    )

        if closed_doors:
            hazards.append(f"{closed_doors} closed door(s) on route")
        if mobile.alignment > 0:
            hazards.append(f"positive alignment target ({mobile.alignment})")
            # DD4's `is_safe` permits NPC combat regardless of alignment.
            # Preserve the alignment cost as a ranking hazard, but do not
            # make lawful NPCs impossible autonomous XP targets.
        if mobile.vnum in world.shopkeepers:
            hazards.append("source mobile is a shopkeeper")
            dangerous = True
            autonomy_rejections.append("source mobile is a shopkeeper")
        if mobile.costs_fame:
            hazards.append("source mobile costs fame when killed")
            dangerous = True
            autonomy_rejections.append("source mobile costs fame when killed")
        if mobile.attack_programs:
            triggers = ", ".join(
                program.trigger for program in mobile.attack_programs
            )
            hazards.append(
                "source mobile program can initiate combat "
                f"({triggers})"
            )
            dangerous = True
            autonomy_rejections.append(
                "source mobile program can initiate an unmodeled attack"
            )
        if mobile.aggressive:
            hazards.append("target is aggressive")
            # The requested mobile's own reset room is a valid destination.
            # Keep the aggression as a risk signal for scoring and live
            # consider/isolation gates, but do not reject an otherwise
            # isolated target before the runner can weigh reward against the
            # source-derived peak-damage bound.
        if equipped_weapons:
            weapon_names = ", ".join(
                item.short_description for item in equipped_weapons
            )
            hazards.append(
                f"target equips {weapon_names} (NPC base damage x1.5 per wielded hit)"
            )
        if equipped_spell_items:
            spell_items = ", ".join(
                f"{item.short_description} ({', '.join(castable_spell_names(item))})"
                for item in equipped_spell_items
            )
            hazards.append(f"target equips a castable spell item: {spell_items}")
            dangerous = True
            autonomy_rejections.append(
                "target carries a source-castable spell item"
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
            if special not in SAFE_NONCOMBAT_SPECIALS:
                autonomy_rejections.append(
                    f"target has special procedure {special}"
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
            - len(equipped_weapons) * 24
        )
        status = "reject" if dangerous else "caution" if hazards else "promising"
        if mobile.alignment > 0 and status == "promising":
            status = "caution"

        ranked.append(
            HuntCandidate(
                status=status,
                score=round(score, 1),
                area_file=mobile.area_file,
                mobile_vnum=mobile.vnum,
                target=mobile.short_description,
                target_keyword=_least_ambiguous_source_keyword(
                    world,
                    mobile,
                    keyword_counts=source_keyword_counts,
                ),
                level=mobile.level,
                room_vnum=room.vnum,
                room_name=room.name,
                route=route,
                source_spawn_limit=reset.maximum_count,
                room_spawn_count=room_spawn_count,
                boot_kills=boot_kills,
                loot=tuple(
                    dict.fromkeys(
                        item.short_description
                        for item in (*sellable, *required_loot_objects)
                    )
                ),
                source_value=source_value,
                contained_coins=contained_coins,
                hazards=tuple(dict.fromkeys(hazards)),
                target_identity=source_mobile_identities(
                    mobile.room_description,
                    mobile.short_description,
                    mobile.keywords,
                )[0],
                equipped_weapons=tuple(
                    item.short_description for item in equipped_weapons
                ),
                estimated_level_range=level_range,
                estimated_base_hp_range=hp_range,
                estimated_peak_round_damage=peak_round_damage,
                estimated_min_peak_round_damage=minimum_peak_round_damage,
                estimated_critical_hit_damage=critical_hit_damage,
                autonomy_rejections=tuple(dict.fromkeys(autonomy_rejections)),
                specials=world.mobile_specials.get(mobile.vnum, ()),
                route_preflight_room_vnum=route_preflight_room_vnum,
                route_preflight_command=route_preflight_command,
                route_preflight_target=route_preflight_target,
                route_preflight_level_range=route_preflight_level_range,
                route_preflight_hard_hazard=route_preflight_hard_hazard,
                route_hard_hazard_targets=route_hard_hazard_targets,
                sentinel=mobile.sentinel,
                stay_area=mobile.stay_area,
                estimated_move_cost=estimated_move_cost,
                estimated_flying_move_cost=estimated_flying_move_cost,
                requires_flight=requires_flight,
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


def _parse_mobile_programs(
    lines: list[str],
    start: int,
    end: int,
) -> tuple[MobileProgram, ...]:
    """Parse the command bodies attached to one mobile prototype."""
    programs: list[MobileProgram] = []
    trigger: str | None = None
    condition = ""
    commands: list[str] = []

    def finish() -> None:
        if trigger is not None:
            programs.append(
                MobileProgram(
                    trigger=trigger,
                    condition=condition,
                    commands=tuple(commands),
                )
            )

    for line in lines[start:end]:
        stripped = line.strip()
        if stripped.startswith(">"):
            finish()
            commands.clear()
            header = stripped[1:].strip()
            parts = header.split(None, 1)
            trigger = parts[0].casefold() if parts else None
            condition = parts[1].rstrip("~").strip() if len(parts) > 1 else ""
            continue
        if stripped == "~":
            continue
        if stripped == "|":
            finish()
            trigger = None
            condition = ""
            commands.clear()
            continue
        if trigger is not None and stripped:
            commands.append(stripped)
    finish()
    return tuple(programs)


def _parse_mobile_teachings(
    lines: list[str],
    start: int,
    end: int,
) -> tuple[tuple[str, int], ...]:
    """Parse the source ``& percent 'skill'`` entries on one mobile."""
    teachings: list[tuple[str, int]] = []
    for line in lines[start:end]:
        match = _MOBILE_TEACHING.match(line)
        if match is None:
            continue
        skill = " ".join(match.group("skill").casefold().split())
        teachings.append((skill, int(match.group("percent"))))
    return tuple(teachings)


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
        record_end = _next_vnum_marker(lines, index, end)
        mobiles[vnum] = MobileSource(
            vnum=vnum,
            keywords=_clean_text(keywords),
            short_description=_clean_text(short_description),
            level=int(combat_parts[0]),
            act_flags=_parse_bits(flag_parts[0]),
            alignment=int(flag_parts[2]),
            area_file=area_file,
            room_description=_clean_text(room_description),
            affected_flags=_parse_bits(flag_parts[1]),
            programs=_parse_mobile_programs(lines, index, record_end),
            teachings=_parse_mobile_teachings(lines, index, record_end),
        )
        index = record_end
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
        value_line = lines[index]
        values = tuple(
            int(match.group(1)) for match in _TILDE_VALUE.finditer(value_line)
        )
        value_strings = tuple(
            _clean_text(value)
            for value in value_line.split("~")[:-1]
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
            value_strings=value_strings,
        )
        index = record_end
    return objects


def _parse_object_sets(
    lines: list[str],
    bounds: tuple[int, int] | None,
) -> dict[int, ObjectSetSource]:
    object_sets: dict[int, ObjectSetSource] = {}
    if bounds is None:
        return object_sets

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
        description, index = _read_tilde(lines, index, end)
        object_numbers, index = _read_integer_fields(lines, index, end, 5)
        bonus_numbers, index = _read_integer_fields(lines, index, end, 5)
        if len(object_numbers) != 5 or len(bonus_numbers) != 5:
            index = _next_vnum_marker(lines, index, end)
            continue

        file_affects: list[tuple[int, int]] = []
        record_end = _next_vnum_marker(lines, index, end)
        while index < record_end:
            parts = lines[index].split()
            index += 1
            if not parts or parts[0] != "A":
                continue
            affect_parts = parts[1:]
            if len(affect_parts) < 2 and index < record_end:
                affect_parts = lines[index].split()
                index += 1
            if len(affect_parts) >= 2 and _all_ints(affect_parts[:2]):
                file_affects.append((int(affect_parts[0]), int(affect_parts[1])))

        thresholds: list[int] = []
        cumulative = 0
        for required_count in range(2, 6):
            matching = bonus_numbers.count(required_count)
            if matching:
                cumulative += matching
                thresholds.append(cumulative)

        # load_object_sets prepends each affect. Runtime position one is
        # therefore the final A record in the area file.
        runtime_affects = reversed(file_affects)
        bonuses = tuple(
            ObjectSetBonus(required_count, location, modifier)
            for required_count, (location, modifier) in zip(
                thresholds,
                runtime_affects,
            )
        )
        object_sets[vnum] = ObjectSetSource(
            vnum=vnum,
            name=_clean_text(name),
            description=_clean_text(description),
            object_vnums=tuple(value for value in object_numbers if value > 0),
            bonuses=bonuses,
        )
        index = record_end
    return object_sets


def _read_integer_fields(
    lines: list[str],
    index: int,
    end: int,
    count: int,
) -> tuple[list[int], int]:
    values: list[int] = []
    while index < end and len(values) < count:
        line = lines[index].strip()
        if _is_vnum_marker(line):
            break
        index += 1
        if not line:
            continue
        for part in line.split():
            try:
                values.append(int(part))
            except ValueError:
                return values, index
            if len(values) == count:
                break
    return values, index


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
    list[RoomObjectReset],
    dict[int, list[int]],
    dict[int, list[tuple[int, int]]],
]:
    if bounds is None:
        return [], [], {}, {}
    index, end = bounds
    pending: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    current_mobile_vnum: int | None = None
    current_level_range: tuple[int, int] | None = None
    room_object_resets: list[RoomObjectReset] = []
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
            room_object_resets.append(
                RoomObjectReset(
                    object_vnum=int(parts[2]),
                    room_vnum=int(parts[4]),
                    maximum_count=max(1, int(parts[1])),
                )
            )
            if current_level_range is not None:
                object_load_levels.setdefault(int(parts[2]), []).append(
                    _fuzzy_level_range(current_level_range)
                )
        elif command == "I" and len(parts) >= 5 and _all_ints(parts[1:5]):
            room_object_resets.append(
                RoomObjectReset(
                    object_vnum=int(parts[1]),
                    room_vnum=int(parts[3]),
                    maximum_count=max(1, int(parts[4])),
                )
            )
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
    return resets, room_object_resets, container_contents, object_load_levels


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


def _route_hazard_rooms(
    world: WorldSource,
    resets_by_room: Mapping[int, tuple[MobReset, ...]],
    *,
    character_level: int,
) -> set[int]:
    """Return rooms worth routing around for the current level band.

    The target room itself remains an endpoint decision. Only intermediate
    rooms are blocked by callers, so a target with its own source hazard still
    receives the normal target-room rejection and is never silently exempted.
    """
    blocked: set[int] = set()
    for room_vnum, resets in resets_by_room.items():
        for reset in resets:
            mobile = world.mobiles.get(reset.mobile_vnum)
            if mobile is None or not mobile.aggressive:
                continue
            if _source_mobile_has_safe_noncombat_special(world, mobile.vnum):
                continue
            level_max = _mobile_level_range(mobile.level)[1]
            if (
                level_max > character_level - 5
                or reset.maximum_count > _MAX_BELOW_BAND_ROUTE_AGGRESSOR_CAPACITY
            ):
                blocked.add(room_vnum)
                break
    return blocked


def _source_route_hazard_rejections(
    world: WorldSource,
    path_rooms: Collection[int],
    *,
    character_level: int,
) -> tuple[str, ...]:
    """Return source-backed combat hazards on a route, including its endpoint.

    Ordinary hunt candidates already perform this analysis while ranking a
    mobile. Retrieve and hoard quests have no mobile target to rank, so they
    need the same fixed-room and reachable-wanderer checks before walking to
    an object.
    """
    if character_level < 1:
        raise ValueError("character_level must be at least 1")
    path_room_set = set(path_rooms)
    resets_by_room = _resets_by_room(world)
    rejections: list[str] = []
    for room_vnum in path_room_set:
        for reset in resets_by_room.get(room_vnum, ()):
            mobile = world.mobiles.get(reset.mobile_vnum)
            if mobile is None or _source_mobile_has_safe_noncombat_special(
                world,
                mobile.vnum,
            ):
                continue
            if mobile.attack_programs:
                rejections.append(
                    "route includes program-triggered attacker: "
                    f"{mobile.short_description} in room {room_vnum}"
                )
            if not mobile.aggressive:
                continue
            maximum_level = _mobile_level_range(mobile.level)[1]
            if maximum_level > character_level:
                rejections.append(
                    "route crosses a higher-level aggressive reset: "
                    f"{mobile.short_description} in room {room_vnum}"
                )
            elif maximum_level > character_level - 5:
                rejections.append(
                    "route crosses an aggressive reset inside the useful "
                    f"XP band: {mobile.short_description} in room {room_vnum}"
                )
            elif reset.maximum_count > _MAX_BELOW_BAND_ROUTE_AGGRESSOR_CAPACITY:
                rejections.append(
                    "route crosses a large below-band aggressive crowd: "
                    f"{mobile.short_description} in room {room_vnum}"
                )

    for mobile, reset in _wandering_aggressors(world):
        if _source_mobile_has_safe_noncombat_special(world, mobile.vnum):
            continue
        if reset.room_vnum in path_room_set:
            continue
        reachable = set(
            _wanderer_reachable_rooms(world, mobile, reset.room_vnum)
        )
        if path_room_set.isdisjoint(reachable):
            continue
        maximum_level = _mobile_level_range(mobile.level)[1]
        if maximum_level > character_level:
            rejections.append(
                "a higher-level aggressive wanderer can reach the route: "
                f"{mobile.short_description}"
            )
        elif maximum_level > character_level - 5:
            rejections.append(
                "an aggressive wanderer inside the useful XP band can reach "
                f"the route: {mobile.short_description}"
            )
    return tuple(dict.fromkeys(rejections))


def source_safe_route_to_room(
    world: WorldSource,
    room_vnum: int,
    *,
    character_level: int,
) -> tuple[tuple[str, ...], tuple[int, ...], int] | None:
    """Return a source-safe route to a quest object room, if one exists."""
    direct = _shortest_paths_from(world.rooms, RECALL_VNUM).get(room_vnum)
    if direct is None:
        return None
    resets_by_room = _resets_by_room(world)
    blocked_rooms = _route_hazard_rooms(
        world,
        resets_by_room,
        character_level=character_level,
    ) - {room_vnum}
    safe = _shortest_paths_from(
        world.rooms,
        RECALL_VNUM,
        blocked_rooms=blocked_rooms,
    ).get(room_vnum)
    selected = direct
    if safe is not None and len(safe[0]) <= len(direct[0]) + _MAX_SOURCE_ROUTE_DETOUR_STEPS:
        selected = safe
    if _source_route_hazard_rejections(
        world,
        selected[1],
        character_level=character_level,
    ):
        return None
    return selected


def _source_mobile_has_safe_noncombat_special(
    world: WorldSource,
    mobile_vnum: int,
) -> bool:
    """Return whether a mobile special is proven non-attacking in transit."""
    specials = tuple(world.mobile_specials.get(mobile_vnum, ()))
    return bool(specials) and all(
        special in SAFE_NONCOMBAT_SPECIALS
        and source_special_profile(special).risk == "noncombat"
        and source_special_profile(special).xp_bonus == 0
        for special in specials
    )


def _shortest_paths_from(
    rooms: Mapping[int, RoomSource],
    origin: int,
    *,
    blocked_rooms: set[int] | frozenset[int] = frozenset(),
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
            if (
                exit_source.destination not in rooms
                or exit_source.destination in blocked_rooms
                # An open exit may retain EX_LOCKED in DD4's source. Players
                # and mobiles can traverse it; only a closed-and-locked door
                # is inaccessible to the route planner.
                or (exit_source.closed and exit_source.locked)
            ):
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


_SUBCLASS_SOURCE_SKILL_ALIASES = {
    "bounty hunter": "bounty base",
    "necromancer": "necro base",
    "martial artist": "artist base",
}


def source_subclass_teacher_skill(subclass: str) -> str:
    """Return the source ``do_change`` teaching entry for a subclass."""
    normalized = " ".join(str(subclass).casefold().split())
    return _SUBCLASS_SOURCE_SKILL_ALIASES.get(
        normalized,
        f"{normalized} base",
    )


def source_subclass_teacher_route(
    world: WorldSource,
    subclass: str,
    *,
    character_class: str | None = None,
    origin: int = RECALL_VNUM,
    preferred_mobile_vnums: Collection[int] = (),
) -> SourceTeacherRoute | None:
    """Find a source-reset teacher that can perform a level-30 change.

    The server's ``do_change`` checks the teacher's learned subclass skill in
    the current room.  Area-file names and nearby NPC descriptions are not
    enough evidence, so this resolver requires both the exact teaching entry
    and a source-reset route from the normal Midgaard recall room.
    """
    source_skill = source_subclass_teacher_skill(subclass)
    preferred = {int(vnum) for vnum in preferred_mobile_vnums}
    class_skill = (
        f"{' '.join(str(character_class).casefold().split())} base"
        if character_class
        else None
    )
    paths = _shortest_paths_from(world.rooms, origin)
    candidates: list[tuple[tuple[int, int, int, int], SourceTeacherRoute]] = []
    resets_by_mobile: dict[int, list[MobReset]] = {}
    for reset in world.mob_resets:
        resets_by_mobile.setdefault(reset.mobile_vnum, []).append(reset)
    for mobile in world.mobiles.values():
        if not mobile.teaches("teacher base") or not mobile.teaches(source_skill):
            continue
        class_fit = 0 if class_skill and mobile.teaches(class_skill) else 1
        for reset in resets_by_mobile.get(mobile.vnum, ()):
            path = paths.get(reset.room_vnum)
            if path is None:
                continue
            commands, rooms, _closed_doors = path
            directions = tuple(
                command
                for command in commands
                if not command.casefold().startswith("open ")
            )
            if len(directions) != len(rooms) - 1:
                continue
            steps: list[tuple[str, str, str]] = []
            open_before: list[tuple[str, str]] = []
            for origin_vnum, destination_vnum, direction in zip(
                rooms,
                rooms[1:],
                directions,
            ):
                exit_source = world.rooms[origin_vnum].exits.get(direction)
                if exit_source is None or exit_source.destination != destination_vnum:
                    steps = []
                    break
                origin_text = str(origin_vnum)
                destination_text = str(destination_vnum)
                steps.append((origin_text, direction, destination_text))
                if exit_source.closed:
                    open_before.append((origin_text, direction))
            if not steps and rooms[0] != rooms[-1]:
                continue
            keyword = (
                mobile.keywords.split()[0]
                if mobile.keywords
                else mobile.short_description
            )
            route = SourceTeacherRoute(
                mobile_vnum=mobile.vnum,
                room_vnum=reset.room_vnum,
                room_name=world.rooms[reset.room_vnum].name,
                keyword=keyword,
                source_skill=source_skill,
                steps=tuple(steps),
                open_before=tuple(open_before),
                wanders=mobile.wanders,
            )
            candidates.append(
                (
                    (
                        0 if mobile.vnum in preferred else 1,
                        class_fit,
                        len(commands),
                        mobile.vnum,
                    ),
                    route,
                )
            )
    if not candidates:
        return None
    return min(candidates, key=lambda item: item[0])[1]


def source_route_movement_cost(
    world: WorldSource,
    path_rooms: Iterable[int],
    *,
    flying: bool = False,
) -> int:
    """Estimate DD4 movement consumed by a source-backed room path.

    ``path_rooms`` includes the origin room.  The calculation follows the
    core's per-edge terrain loss and its one-third flying reduction; door-open
    commands do not consume movement.  A missing room is ignored so old or
    partial test worlds remain usable, while parsed source paths are complete.
    """
    rooms = tuple(path_rooms)
    total = 0
    for origin_vnum, destination_vnum in zip(rooms, rooms[1:]):
        origin = world.rooms.get(int(origin_vnum))
        destination = world.rooms.get(int(destination_vnum))
        if origin is None or destination is None:
            continue
        origin_sector = min(
            max(int(origin.sector_type), 0),
            len(_MOVEMENT_LOSS) - 1,
        )
        destination_sector = min(
            max(int(destination.sector_type), 0),
            len(_MOVEMENT_LOSS) - 1,
        )
        move = _MOVEMENT_LOSS[origin_sector] + _MOVEMENT_LOSS[destination_sector]
        if flying:
            move = max(1, move // 3)
        total += move
    return total


def source_route_requires_flight(
    world: WorldSource,
    path_rooms: Iterable[int],
) -> bool:
    """Return whether a source route needs a generic movement capability.

    DD4's movement gate is based on the destination sector and EX_WALL flag,
    not on the command spelling.  A route can therefore require flight even
    when it reaches an air or water room via north, east, or another ordinary
    exit.  Water routes also accept swimming, a boat, or race-specific native
    movement in the core; the campaign represents flight as the generic
    capability it can acquire and verify for arbitrary characters.
    """
    rooms = tuple(path_rooms)
    for origin_vnum, destination_vnum in zip(rooms, rooms[1:]):
        origin = world.rooms.get(int(origin_vnum))
        destination = world.rooms.get(int(destination_vnum))
        if destination is None:
            continue
        if (
            destination.sector_type == SECT_AIR
            or destination.sector_type in _FLIGHT_OR_WATER_SECTORS
        ):
            return True
        if origin is None:
            continue
        if any(
            exit_source.destination == destination_vnum
            and bool(exit_source.flags & EX_WALL)
            for exit_source in origin.exits.values()
        ):
            return True
    return False


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


def _route_preflight_metadata(
    world: WorldSource,
    route: tuple[str, ...],
    *,
    character_level: int,
) -> tuple[
    str | None,
    str | None,
    str | None,
    tuple[int, int],
    bool,
    tuple[str, ...],
]:
    """Carry known route checks into generic source-ranked hunt records.

    A route preflight remains hard when its source target can be inside the
    useful band or its source identity is unknown. A source-confirmed target
    at least five levels below the character is a soft transit check, matching
    DD4's XP and below-band crowd rules.
    """
    for route_definition in (*FASTWALKS, *MAP_ROUTES):
        if route_definition.commands != route:
            continue
        target = route_definition.route_preflight_target
        level_range = (0, 0)
        if target is not None:
            normalized_target = _normalize_name(target)
            matching_ranges = [
                _mobile_level_range(mobile.level)
                for mobile in world.mobiles.values()
                if _normalize_name(mobile.short_description) == normalized_target
            ]
            if matching_ranges:
                level_range = (
                    min(low for low, _ in matching_ranges),
                    max(high for _, high in matching_ranges),
                )
        hard_hazard = route_definition.route_preflight_hard_hazard
        if (
            hard_hazard
            and level_range != (0, 0)
            and level_range[1] <= character_level - 5
        ):
            hard_hazard = False
        return (
            route_definition.route_preflight_room_vnum,
            route_definition.route_preflight_command,
            target,
            level_range,
            hard_hazard,
            route_definition.route_hard_hazard_targets,
        )
    return (None, None, None, (0, 0), False, ())


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
    unarmed_hit = _mobile_normal_hit_damage(level, wielding=False)
    weapon_hit = _mobile_normal_hit_damage(level, wielding=True)
    cycle_damage = weapon_hit if wielding else unarmed_hit
    if dual_wielding:
        cycle_damage += weapon_hit
    possible_attacks = 5 + int(level >= 20)
    return cycle_damage * possible_attacks


def _mobile_normal_hit_damage(level: int, *, wielding: bool) -> int:
    """Mirror the maximum ordinary NPC damage for one ``one_hit`` call."""
    unarmed_hit = level * 3 // 2 + level // 4
    return unarmed_hit + (unarmed_hit // 2 if wielding else 0)


def _mobile_critical_hit_damage(level: int, *, wielding: bool) -> int:
    """Mirror DD4's NPC critical, which doubles one ordinary hit."""
    return _mobile_normal_hit_damage(level, wielding=wielding) * 2


def _wandering_aggressors(
    world: WorldSource,
) -> tuple[tuple[MobileSource, MobReset], ...]:
    return tuple(
        (mobile, reset)
        for reset in world.mob_resets
        if (mobile := world.mobiles.get(reset.mobile_vnum)) is not None
        and mobile.aggressive
        and mobile.wanders
    )


def _money_object_keyword(item: ObjectSource) -> str:
    """Choose a source-listed keyword that addresses a money object."""
    words = item.keywords.casefold().split()
    for preferred in ("coins", "gold", "silver", "copper", "platinum"):
        if preferred in words:
            return preferred
    return words[0] if words else "coins"


def _rank_direct_ground_stashes(
    world: WorldSource,
    *,
    character_level: int,
    include_all_areas: bool,
    object_filter: Callable[[ObjectSource], bool],
    object_value: Callable[[ObjectSource], int],
    object_keyword: Callable[[ObjectSource], str],
    target: str,
    is_coin_stash: bool = False,
    is_food_stash: bool = False,
) -> list[HuntCandidate]:
    """Rank direct ground resets with the shared source route-safety gates."""
    if character_level < 1:
        raise ValueError("character_level must be at least 1")
    allowed_areas = (
        None
        if include_all_areas
        else set(LOW_LEVEL_AREA_FILES)
    )
    paths = _shortest_paths_from(world.rooms, RECALL_VNUM)
    resets_by_room = _resets_by_room(world)
    grouped: dict[int, list[RoomObjectReset]] = {}
    for reset in world.room_object_resets:
        room = world.rooms.get(reset.room_vnum)
        if room is None or (
            allowed_areas is not None and room.area_file not in allowed_areas
        ):
            continue
        item = world.objects.get(reset.object_vnum)
        if item is None or not object_filter(item):
            continue
        grouped.setdefault(reset.room_vnum, []).append(reset)

    ranked: list[HuntCandidate] = []
    for room_vnum, resets in grouped.items():
        path = paths.get(room_vnum)
        room = world.rooms.get(room_vnum)
        if path is None or room is None:
            continue
        route, path_rooms, closed_doors = path
        path_room_set = set(path_rooms)
        object_vnums = tuple(dict.fromkeys(reset.object_vnum for reset in resets))
        ground_objects = [
            world.objects[object_vnum]
            for object_vnum in object_vnums
            if object_vnum in world.objects
        ]
        total_value = sum(object_value(item) for item in ground_objects)
        if total_value <= 0:
            continue

        hazards: list[str] = []
        rejections: list[str] = []
        for path_room_vnum in path_rooms:
            for reset in resets_by_room.get(path_room_vnum, ()):
                mobile = world.mobiles.get(reset.mobile_vnum)
                if mobile is None or not mobile.aggressive:
                    continue
                hazards.append(
                    f"route: {mobile.short_description} L{mobile.level} "
                    f"in {path_room_vnum}"
                )
                hazard_level_max = _mobile_level_range(mobile.level)[1]
                if hazard_level_max > character_level:
                    rejections.append("route crosses a higher-level aggressive reset")
                elif hazard_level_max > character_level - 5:
                    rejections.append(
                        "route crosses an aggressive reset inside the useful XP band"
                    )
        # A wandering aggressor can enter a path room even when its reset
        # room is elsewhere. Keep below-band transit hazards as cautionary
        # evidence: the runner can finish an unavoidable source-proven trivial
        # interruption without treating it as an XP target.
        for mobile_vnum, mobile in world.mobiles.items():
            if not mobile.aggressive or not mobile.wanders:
                continue
            reachable = set(source_mobile_search_rooms(world, mobile_vnum))
            if path_room_set.isdisjoint(reachable):
                continue
            hazards.append(
                f"reachable wanderer: {mobile.short_description} L{mobile.level}"
            )
            hazard_level_max = _mobile_level_range(mobile.level)[1]
            if hazard_level_max > character_level:
                rejections.append(
                    "a higher-level aggressive wanderer can reach the route"
                )
            elif hazard_level_max > character_level - 5:
                rejections.append(
                    "an aggressive wanderer inside the useful XP band can reach the route"
                )
        for reset in resets_by_room.get(room_vnum, ()):
            mobile = world.mobiles.get(reset.mobile_vnum)
            if mobile is None or not mobile.aggressive:
                continue
            hazards.append(
                f"stash room has aggressive reset: {mobile.short_description}"
            )
            rejections.append("stash room has an aggressive reset")

        keywords = tuple(dict.fromkeys(object_keyword(item) for item in ground_objects))
        if closed_doors:
            hazards.append(f"{closed_doors} closed door(s) on route")
        route_cost = source_route_movement_cost(world, path_rooms)
        flying_route_cost = source_route_movement_cost(
            world,
            path_rooms,
            flying=True,
        )
        requires_flight = source_route_requires_flight(world, path_rooms)
        if requires_flight:
            hazards.append("route requires flight or another movement capability")
        status = "reject" if rejections else "caution" if hazards else "promising"
        score = total_value / max(route_cost, len(route), 1)
        ranked.append(
            HuntCandidate(
                status=status,
                score=round(score, 1),
                area_file=room.area_file,
                mobile_vnum=0,
                target=target,
                target_keyword=keywords[0],
                level=0,
                room_vnum=room_vnum,
                room_name=room.name,
                route=route,
                source_spawn_limit=max(reset.maximum_count for reset in resets),
                room_spawn_count=len(resets),
                boot_kills=0,
                loot=(
                    ()
                    if is_coin_stash
                    else tuple(item.short_description for item in ground_objects)
                ),
                source_value=0 if is_coin_stash else total_value,
                contained_coins=total_value if is_coin_stash else 0,
                hazards=tuple(dict.fromkeys(hazards)),
                estimated_move_cost=route_cost,
                estimated_flying_move_cost=flying_route_cost,
                requires_flight=requires_flight,
                ground_loot_keywords=keywords,
                ground_loot_object_vnums=object_vnums,
                is_coin_stash=is_coin_stash,
                is_food_stash=is_food_stash,
                autonomy_rejections=tuple(dict.fromkeys(rejections)),
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
        ),
    )


def rank_coin_stashes(
    world: WorldSource,
    *,
    character_level: int,
    include_all_areas: bool = False,
) -> list[HuntCandidate]:
    """Rank directly reset ground coin piles reachable from recall."""
    return _rank_direct_ground_stashes(
        world,
        character_level=character_level,
        include_all_areas=include_all_areas,
        object_filter=lambda item: item.item_type == ITEM_MONEY,
        object_value=lambda item: money_value(item.values),
        object_keyword=_money_object_keyword,
        target="coin stash",
        is_coin_stash=True,
    )


def _food_object_keyword(item: ObjectSource) -> str:
    """Choose the most specific source-listed keyword for ground food."""
    words = item.keywords.casefold().split()
    return words[-1] if words else "food"


def rank_food_stashes(
    world: WorldSource,
    *,
    character_level: int,
    include_all_areas: bool = False,
) -> list[HuntCandidate]:
    """Rank non-poisonous direct ground food by fullness per route effort."""

    def safe_food(item: ObjectSource) -> bool:
        return bool(
            item.item_type == ITEM_FOOD
            and item.values
            and item.values[0] > 0
            and (len(item.values) < 4 or item.values[3] == 0)
        )

    return _rank_direct_ground_stashes(
        world,
        character_level=character_level,
        include_all_areas=include_all_areas,
        object_filter=safe_food,
        object_value=lambda item: max(0, item.values[0]),
        object_keyword=_food_object_keyword,
        target="food stash",
        is_food_stash=True,
    )


def source_mobile_search_rooms(
    world: WorldSource,
    mobile_vnum: int,
    *,
    maximum_rooms: int | None = None,
    blocked_rooms: set[int] | frozenset[int] = frozenset(),
) -> tuple[int, ...]:
    """Return rooms a source mobile can occupy from its reset locations.

    DD4's ``update.c`` chooses a random open exit for ordinary non-sentinel
    mobiles.  ``ACT_STAY_AREA`` limits that movement to the mobile's area; it
    does not make the reset room a fixed location.  ``ACT_DIE_IF_MASTER_GONE``
    makes a reset mobile effectively fixed until a master is present, while
    ``AFF_CONFUSION`` uses a separate movement path that overrides sentinel,
    stay-area, and no-mob restrictions.  This graph is therefore the
    source-backed search boundary for live target discovery.
    """
    mobile = world.mobiles.get(mobile_vnum)
    if mobile is None:
        return ()
    reset_rooms = tuple(
        sorted(
            {
                reset.room_vnum
                for reset in world.mob_resets
                if reset.mobile_vnum == mobile_vnum
                and reset.room_vnum in world.rooms
            }
        )
    )
    if not mobile.wanders:
        return reset_rooms
    if not reset_rooms:
        return ()

    origin_areas = {
        world.rooms[room_vnum].area_file
        for room_vnum in reset_rooms
    }
    pending: list[tuple[int, int]] = [(0, room_vnum) for room_vnum in reset_rooms]
    heapq.heapify(pending)
    distances: dict[int, int] = {}
    while pending:
        distance, room_vnum = heapq.heappop(pending)
        if room_vnum in distances:
            continue
        room = world.rooms.get(room_vnum)
        if room is None:
            continue
        distances[room_vnum] = distance
        if maximum_rooms is not None and len(distances) >= maximum_rooms:
            break
        for direction, exit_source in sorted(room.exits.items()):
            del direction
            destination = world.rooms.get(exit_source.destination)
            if (
                destination is None
                or destination.vnum in distances
                or destination.vnum in blocked_rooms
                # update.c checks EX_CLOSED, not EX_LOCKED, for wandering
                # mobiles. An open-but-locked exit is therefore reachable.
                or exit_source.closed
                or (
                    not mobile.confused
                    and destination.no_mob
                )
                or (
                    not mobile.confused
                    and mobile.stay_area
                    and destination.area_file not in origin_areas
                )
            ):
                continue
            heapq.heappush(
                pending,
                (distance + 1, destination.vnum),
            )
    return tuple(
        room_vnum
        for room_vnum, _distance in sorted(
            distances.items(),
            key=lambda item: (item[1], item[0]),
        )
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
                # Keep this condition identical to update.c's wander check.
                or exit_source.closed
                or (
                    not mobile.confused
                    and destination.no_mob
                )
                or (
                    not mobile.confused
                    and mobile.stay_area
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


def _source_mobile_identity(
    room_description: str,
    short_description: str,
    keywords: str = "",
) -> str:
    """Return a source identity when a generic short name has collisions.

    DD4 can give several prototypes the same short description (for example,
    male and female centaurs are both ``a centaur``).  Their room lines and
    source keywords still identify the prototype that a TARGETMODE selector
    represents.  Use that phrase only when it appears in the source room
    line, preserving the existing short-name identity for ordinary mobiles.
    """
    short_identity = _normalize_name(short_description)
    keyword_identity = _normalize_name(keywords)
    room_text = _normalize_name(room_description)
    if (
        keyword_identity
        and keyword_identity != short_identity
        and len(keyword_identity.split()) > len(short_identity.split())
        and keyword_identity in room_text
    ):
        return keyword_identity
    return short_identity or keyword_identity


_SOURCE_MOBILE_VERBS = (
    r"(?:is|are|sits?|circles?|stands?|waits?|prepares?|paces?|runs?|"
    r"greets?|growls?|prowls?|hisses?|snarls?|slithers?|cowers?|lies?|looks?|"
    r"watches?|spits?|barks?|glares?|grunts?|screams?|cries?|crawls?|"
    r"lunges?|shuffles?|crouches?|yells?|cringes?|tries?|makes?|"
    r"mumbles?|mutters?|poses?|monitors?)"
)
_SOURCE_MOBILE_DISPLAY_PATTERNS = (
    re.compile(
        r"(?:^|\n)\s*(?:\([^)]*\)\s*)*"
        r"(?P<target>[A-Z][A-Za-z'-]*"
        r"(?:\s+[A-Z][A-Za-z'-]*){0,2}),\s+"
        r"(?:the\s+)?[A-Z][A-Za-z' -]{1,60},\s+"
        rf"(?:[A-Za-z]+ly\s+)?{_SOURCE_MOBILE_VERBS}\b",
    ),
    re.compile(
        r"(?:^|\n)\s*(?:\([^)]*\)\s*)*(?:A|An|The|This)\s+"
        r"(?P<target>[A-Za-z][A-Za-z'-]*"
        r"(?:\s+[A-Za-z][A-Za-z'-]*){0,3}?)\s+"
        rf"(?:[A-Za-z]+ly\s+)?{_SOURCE_MOBILE_VERBS}\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:^|\n)\s*(?:\([^)]*\)\s*)*"
        r"(?!(?:A|An|The|This)\s)"
        r"(?P<target>[A-Z][A-Za-z'-]*"
        r"(?:\s+[A-Za-z][A-Za-z'-]*){0,3}?)\s+"
        rf"(?:[A-Za-z]+ly\s+)?{_SOURCE_MOBILE_VERBS}\b",
    ),
)
_SOURCE_MOBILE_IGNORED_WORDS = {
    "autoloot",
    "board",
    "chairs",
    "ceiling",
    "cleric",
    "corpse",
    "door",
    "floor",
    "gate",
    "heart",
    "imp",
    "it",
    "officer",
    "place",
    "portal",
    "recruit",
    "recruits",
    "room",
    "soldier",
    "soldiers",
    "staircase",
    "there",
    "tunnel",
    "wall",
    "yard",
    "you",
    "your",
}


def _source_display_targets(text: str) -> tuple[str, ...]:
    """Extract canonical mobile identities from source room descriptions."""
    targets: Counter[str] = Counter()
    for pattern in _SOURCE_MOBILE_DISPLAY_PATTERNS:
        for match in pattern.finditer(text):
            target = " ".join(match.group("target").casefold().split())
            line_end = text.find("\n", match.end())
            if line_end < 0:
                line_end = len(text)
            activity = text[match.start():line_end].casefold()
            if target == "goblin" and "looting the dead" in activity:
                target = "goblin looter"
            words = set(target.replace("'s", "").split())
            if (
                words.isdisjoint(_SOURCE_MOBILE_IGNORED_WORDS)
                and not target.startswith("imp ")
            ):
                targets[target] += 1
    return tuple(targets)


def _source_targets_match(observed: str, requested: str) -> bool:
    """Match source display parsing's short-name equivalence rules."""
    observed_words = observed.split()
    requested_words = requested.split()
    proper_name_prefix = (
        len(observed_words) == 1
        and len(requested_words) > 1
        and observed_words[0][:1].isupper()
        and observed_words[0].casefold() == requested_words[0].casefold()
    ) or (
        len(requested_words) == 1
        and len(observed_words) > 1
        and requested_words[0][:1].isupper()
        and requested_words[0].casefold() == observed_words[0].casefold()
    )
    return (
        observed.casefold() == requested.casefold()
        or observed.rsplit(maxsplit=1)[-1].casefold()
        == requested.rsplit(maxsplit=1)[-1].casefold()
        or proper_name_prefix
    )


def source_mobile_identities(
    room_description: str,
    short_description: str,
    keywords: str = "",
) -> tuple[str, ...]:
    """Return the identities used by live room parsing and TARGETMODE.

    Source room descriptions are more precise than a prototype short name in
    cases such as ``Secretary`` versus ``The Sergeant at Arm's Secretary``.
    Keep candidate ranking, registered routes, and live room recognition on
    the same source-derived identity.
    """
    parsed = _source_display_targets(room_description)
    normalized_short = _normalize_name(short_description)
    normalized_keywords = _normalize_name(keywords)
    source_identity = _source_mobile_identity(
        room_description,
        short_description,
        keywords,
    )
    if source_identity and source_identity != normalized_short:
        return (source_identity,)
    short_tokens = normalized_short.split()
    keyword_tokens = normalized_keywords.split()
    keyword_in_short = bool(
        keyword_tokens
        and any(
            short_tokens[index : index + len(keyword_tokens)] == keyword_tokens
            for index in range(len(short_tokens) - len(keyword_tokens) + 1)
        )
    )
    display_words = short_description.split()
    if display_words and display_words[0].casefold() in {"a", "an", "the"}:
        display_words = display_words[1:]
    has_explicit_name = bool(
        display_words
        and display_words[0][:1].isupper()
    )
    has_title_case_tail = any(
        word[:1].isupper() for word in display_words[1:]
    )
    has_proper_name_shape = len(display_words) == 1 or has_title_case_tail
    if has_explicit_name and has_proper_name_shape and not any(
        _source_targets_match(normalized_short, target) for target in parsed
    ):
        return (normalized_short,)
    if keyword_in_short and (len(keyword_tokens) > 1 or has_explicit_name):
        return (normalized_keywords,)
    return parsed or (normalized_short or normalized_keywords,)


def _source_keyword_counts(world: WorldSource) -> dict[str, int]:
    """Count each distinct source keyword once per mobile prototype."""
    keyword_counts: dict[str, int] = {}
    for other in world.mobiles.values():
        other_tokens = {
            token.casefold()
            for token in re.findall(r"[A-Za-z0-9]+", other.keywords)
        }
        for token in other_tokens:
            keyword_counts[token] = keyword_counts.get(token, 0) + 1
    return keyword_counts


def _least_ambiguous_source_keyword(
    world: WorldSource,
    mobile: MobileSource,
    *,
    keyword_counts: Mapping[str, int] | None = None,
) -> str:
    """Choose a source keyword that minimizes live ``where`` collisions."""
    tokens = tuple(
        dict.fromkeys(
            token.casefold()
            for token in re.findall(r"[A-Za-z0-9]+", mobile.keywords)
            if token.casefold() not in {"a", "an", "the"}
        )
    )
    if not tokens:
        fallback = mobile.keywords.split()
        return fallback[0].casefold() if fallback else mobile.short_description.casefold()

    if keyword_counts is None:
        keyword_counts = _source_keyword_counts(world)

    return min(
        tokens,
        key=lambda token: (
            keyword_counts.get(token, 0),
            -len(token),
            tokens.index(token),
        ),
    )
