"""Walking-return evidence for hoards; not permission to excavate or flee."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from typing import Any, Collection, Mapping

from .equipment import ITEM_DIGGER
from .excavation import (
    DigBudget, HoardGuardianDamage, hoard_guardian_damage,
    maximum_hoard_direct_damage, shop_digger_level_bounds, tool_dig_budget,
)
from .hunt_candidates import (
    EX_WALL,
    ObjectSource, WorldSource,
    _resets_by_room,
    _route_hazard_rooms,
    _shortest_paths_from,
    source_room_level_rejection,
    source_route_hazard_rejections,
    source_route_movement_cost,
)
from .quests import snapshot_quest_status


_ROOM_HEALING = 1 << 16
_RESTRICTED_ROOMS = (1 << 9) | (1 << 11)  # private / solitary
_LAND_SECTORS = frozenset({0, 1, 2, 3, 4, 5, 10, 11})
_DIRECTIONS = frozenset({"north", "east", "south", "west", "up", "down"})
_HOARD_LOCATOR_MOBILES = (3060, 3064)
_HOARD_GUARDIAN_VNUM = 83


def _exact_hoard_locator_resets(world: WorldSource) -> tuple[int, ...]:
    """Return the two source-audited Midgaard hazards allowed only with live where checks."""
    cityguard = world.mobiles.get(3060)
    drunk = world.mobiles.get(3064)
    if (
        cityguard is None or cityguard.area_file != "midgaard.are"
        or cityguard.keywords != "cityguard guard"
        or cityguard.level != 15 or cityguard.act_flags != 16810049
        or cityguard.alignment != 1000 or cityguard.programs
        or world.mobile_specials.get(3060) != ("spec_guard",)
        or drunk is None or drunk.area_file != "midgaard.are"
        or drunk.keywords != "drunk"
        or drunk.level != 2 or drunk.act_flags != 0 or drunk.alignment != 400
        or world.mobile_specials.get(3064)
    ):
        raise ValueError("hoard live-locator source profiles are absent or changed")

    expected_cityguard_resets = Counter({
        (3004, 12, (3365, 3364, 3350, 3353, 3355),
         ((0, 3365), (1, 3364), (16, 3350), (5, 3353), (4, 3355))): 1,
        (3014, 12, (3365, 3364, 3350, 3353, 3356),
         ((0, 3365), (1, 3364), (16, 3350), (5, 3353), (6, 3356))): 1,
        (3017, 10, (3365, 3364, 3350, 3353, 3357),
         ((0, 3365), (1, 3364), (16, 3350), (5, 3353), (7, 3357))): 1,
        (3021, 10, (3365, 3364, 3350, 3353, 3358),
         ((0, 3365), (1, 3364), (16, 3350), (5, 3353), (8, 3358))): 1,
        (3027, 12, (3365, 3364, 3350, 3353, 3359),
         ((0, 3365), (1, 3364), (16, 3350), (5, 3353), (9, 3359))): 1,
        (3111, 20, (3365, 3364, 3350, 3353, 3120),
         ((0, 3365), (1, 3364), (16, 3350), (5, 3353))): 1,
        (3111, 20, (3365, 3364, 3350, 3353, 3363),
         ((0, 3365), (1, 3364), (16, 3350), (5, 3353), (15, 3363))): 1,
        (3111, 20, (3365, 3364, 3350, 3353),
         ((0, 3365), (1, 3364), (16, 3350), (5, 3353))): 2,
    })
    cityguard_resets = [r for r in world.mob_resets if r.mobile_vnum == 3060]
    if (
        Counter((r.room_vnum, r.maximum_count, r.object_vnums, r.equipment)
                for r in cityguard_resets)
        != expected_cityguard_resets
    ):
        raise ValueError("hoard cityguard reset profile is absent or changed")

    expected_drunk_programs = (
        ("rand_prog", "10", ("if rand(50)", "dance", "else", "sing", "endif")),
        ("greet_prog", "10", ("yell Monster!  I found a monster!  Kill!  Banzai!", "mpkill $n")),
        ("bribe_prog", "10", ("say Ahh!  More spirits!  Good spirits!", "sing")),
    )
    if tuple((p.trigger, p.condition, p.commands) for p in drunk.programs) != expected_drunk_programs:
        raise ValueError("hoard drunk program profile is absent or changed")
    drunk_resets = [r for r in world.mob_resets if r.mobile_vnum == 3064]
    if (
        len(drunk_resets) != 1 or drunk_resets[0].room_vnum != 3007
        or drunk_resets[0].maximum_count != 3 or drunk_resets[0].object_vnums
        or drunk_resets[0].equipment
    ):
        raise ValueError("hoard drunk reset profile is absent or changed")
    return _HOARD_LOCATOR_MOBILES


@dataclass(frozen=True)
class HoardReturnRoute:
    commands: tuple[str, ...]
    rooms: tuple[int, ...]
    movement: int
    required_absent_mobile_vnums: tuple[int, ...] = ()


@dataclass(frozen=True)
class HoardEscapeBranch:
    direction: str
    destination: int
    flee_movement: int
    return_route: HoardReturnRoute


@dataclass(frozen=True)
class HoardReturnPlan:
    endpoint: int
    healer: int
    outbound: HoardReturnRoute
    preparation_commands: tuple[str, ...]
    physical_return: HoardReturnRoute
    escape_branches: tuple[HoardEscapeBranch, ...]
    live_locator_mobile_vnums: tuple[int, ...] = ()
    live_locator_selectors: tuple[tuple[int, str], ...] = ()
    flying: bool = False

    @property
    def movement_reserve(self) -> int:
        return max(
            self.physical_return.movement,
            *(branch.flee_movement + branch.return_route.movement
              for branch in self.escape_branches),
        )

    @property
    def expected_open_exits(self) -> dict[str, int]:
        return {branch.direction: branch.destination for branch in self.escape_branches}

    def live_exit_issue(self, exits: dict[str, int] | None) -> str | None:
        """Require complete fresh endpoint exits after preparation, before dig."""
        if (
            not isinstance(exits, dict)
            or any(type(vnum) is not int for vnum in exits.values())
            or exits != self.expected_open_exits
        ):
            return "live hoard exits differ from the complete audited escape set"
        return None

    def live_route_issue(
        self,
        route: HoardReturnRoute,
        locations_by_mobile_vnum: Mapping[int, Collection[int]],
        *,
        first_room_index: int = 0,
        flying_active: bool | None = None,
    ) -> str | None:
        """Require fresh complete where results immediately before each route leg."""
        if self.flying and flying_active is not True:
            return "fresh active flight is required for this movement plan"
        planned_routes = (
            self.outbound, self.physical_return,
            *(b.return_route for b in self.escape_branches),
        )
        if route not in planned_routes:
            return "return route is not part of this source-audited hoard plan"
        if type(first_room_index) is not int or not 0 <= first_room_index < len(route.rooms):
            return "live route check needs a valid next-room index"
        required = tuple(dict.fromkeys((
            *self.live_locator_mobile_vnums,
            *route.required_absent_mobile_vnums,
        )))
        return _live_mobile_route_issue(
            required, route.rooms[first_room_index:], locations_by_mobile_vnum,
        )

    def live_escape_issue(
        self,
        locations_by_mobile_vnum: Mapping[int, Collection[int]],
        *,
        flying_active: bool | None = None,
    ) -> str | None:
        """Check every random flee and return room before excavation begins."""
        if self.flying and flying_active is not True:
            return "fresh active flight is required for this movement plan"
        if not self.live_locator_mobile_vnums:
            return None
        route_rooms = {
            *self.outbound.rooms,
            self.endpoint,
            *(branch.destination for branch in self.escape_branches),
            *(room for branch in self.escape_branches for room in branch.return_route.rooms),
        }
        return _live_mobile_route_issue(
            self.live_locator_mobile_vnums, tuple(sorted(route_rooms)),
            locations_by_mobile_vnum,
        )


@dataclass(frozen=True)
class HoardMovementCircuit:
    """One healer-to-hoard visit that keeps enough movement to get back."""

    outbound_commands: tuple[str, ...]
    preparation_commands: tuple[str, ...]
    dig_commands: int
    return_commands: tuple[str, ...]
    outbound_movement: int
    digging_movement: int
    return_reserve: int

    @property
    def total_movement(self) -> int:
        return self.outbound_movement + self.digging_movement + self.return_reserve

    @property
    def total_route_commands(self) -> int:
        return (
            len(self.outbound_commands)
            + len(self.preparation_commands)
            + self.dig_commands
            + len(self.return_commands)
        )


@dataclass(frozen=True)
class HoardMovementPlan:
    """Finite dig batches separated by recovery at the registered healer."""

    circuits: tuple[HoardMovementCircuit, ...]
    required_digs: int
    total_route_commands: int


def plan_hoard_movement_circuits(
    route: HoardReturnPlan,
    budget: DigBudget,
    *,
    maximum_movement: int,
    starting_movement: int,
    maximum_route_commands: int = 240,
) -> HoardMovementPlan:
    """Split an untrapped excavation into bounded round trips to the healer.

    A trap ends the attempt and uses the same reserved physical return; this
    plan therefore budgets the depth digs, not extra charges for deliberately
    continuing after a trap. It does not authorize the route or any live dig.
    """
    values = (maximum_movement, starting_movement, maximum_route_commands)
    if (
        any(type(value) is not int for value in values)
        or maximum_movement <= 0
        or not 0 <= starting_movement <= maximum_movement
        or maximum_route_commands < 1
        or budget.maximum_digs < 1
        or budget.maximum_move_per_dig < 1
        or route.outbound.movement < 0
        or route.movement_reserve < 0
    ):
        raise ValueError("hoard movement planning needs complete positive bounds")

    return_commands = route.physical_return.commands
    if (
        route.preparation_commands
        and return_commands[:len(route.preparation_commands)]
        != route.preparation_commands
    ):
        raise ValueError("return preparation is not the first physical-return step")
    return_commands = return_commands[len(route.preparation_commands):]
    route_commands = (
        len(route.outbound.commands)
        + len(route.preparation_commands)
        + len(return_commands)
    )
    first_capacity = (
        starting_movement - route.outbound.movement - route.movement_reserve
    ) // budget.maximum_move_per_dig
    later_capacity = (
        maximum_movement - route.outbound.movement - route.movement_reserve
    ) // budget.maximum_move_per_dig
    if first_capacity < 1 or later_capacity < 1:
        raise ValueError(
            "movement cannot cover the audited outbound, one dig, and return reserve"
        )

    remaining = budget.maximum_digs
    circuits: list[HoardMovementCircuit] = []
    while remaining:
        capacity = first_capacity if not circuits else later_capacity
        dig_commands = min(remaining, capacity)
        circuits.append(HoardMovementCircuit(
            outbound_commands=route.outbound.commands,
            preparation_commands=route.preparation_commands,
            dig_commands=dig_commands,
            return_commands=return_commands,
            outbound_movement=route.outbound.movement,
            digging_movement=dig_commands * budget.maximum_move_per_dig,
            return_reserve=route.movement_reserve,
        ))
        remaining -= dig_commands

    total_route_commands = len(circuits) * route_commands + budget.maximum_digs
    if total_route_commands > maximum_route_commands:
        raise ValueError("healer-return dig circuits exceed their command bound")
    return HoardMovementPlan(tuple(circuits), budget.maximum_digs, total_route_commands)


@dataclass(frozen=True)
class HoardExecutionPlan:
    """Composed source plan; live observations are still required to execute it."""

    quest_identity: tuple[int, int, int]
    tool: ObjectSource
    dig_budget: DigBudget
    return_plan: HoardReturnPlan
    movement_plan: HoardMovementPlan
    maximum_direct_trap_damage: int
    guardian: HoardGuardianDamage
    maximum_guardian_damage_before_next_command: int

    @property
    def live_dispatch_authorized(self) -> bool:
        return False


def _positive_quest_id(value: Any, field: str) -> int:
    if type(value) is int and value > 0:
        return value
    if isinstance(value, str) and value.isdecimal() and int(value) > 0:
        return int(value)
    raise ValueError(f"hoard assignment is missing its exact {field}")


def build_source_hoard_execution_plan(
    world: WorldSource,
    quest_status: Mapping[str, Any],
    *,
    tool_vnum: int,
    carried_tool_vnums: Collection[int],
    character_level: int,
    race: str,
    healer_vnum: int,
    maximum_movement: int,
    starting_movement: int,
    strength: int,
    constitution: int,
    dexterity: int,
    swiftness: int,
    enhanced_swiftness_percent: int,
    armor_class: int,
    sanctuary: bool,
    observed_tool_level: int | None = None,
    source_tool_level_bounds: tuple[int, int] | None = None,
    haste: bool = False,
    quicken: bool = False,
    bonus_attack: bool = False,
    cannot_see_self: bool = False,
    flying: bool = False,
    slow: bool = False,
    allow_exact_live_where_hazards: bool = True,
    maximum_route_commands: int = 240,
) -> HoardExecutionPlan:
    """Compose exact quest, source tool, excavation, return, and survival bounds.

    This is planning evidence only. ``carried_tool_vnums`` and an observed
    tool level must come from the current live inventory/identify evidence;
    the source-bounded range is accepted only for exact shop stock. Callers
    still need fresh route, exit, flight, target, and recovery checks before
    issuing any game command.
    """
    if not isinstance(quest_status, Mapping):
        raise ValueError("hoard planning requires the observed quest record")
    if any(type(value) is not bool for value in (
        haste, quicken, bonus_attack, cannot_see_self, flying, slow, sanctuary,
        allow_exact_live_where_hazards,
    )):
        raise ValueError("hoard planning requires explicit status flags")
    quest = snapshot_quest_status(quest_status)
    evidence = quest_status.get("retrieval_evidence")
    if (
        not quest.active or quest.complete or quest.kind != "hoard"
        or not isinstance(evidence, Mapping)
        or evidence.get("method") != "hoard"
        or evidence.get("source") != "requested-questmaster-narrative"
    ):
        raise ValueError("hoard planning requires the exact active narrative-verified assignment")
    identity = (
        _positive_quest_id(quest_status.get("giver_vnum"), "giver VNUM"),
        _positive_quest_id(quest_status.get("room_vnum"), "room VNUM"),
        _positive_quest_id(quest_status.get("object_vnum"), "object VNUM"),
    )
    if (
        identity[1] != quest.room_vnum
        or identity[2] != quest.object_vnum
        or any(
            _positive_quest_id(evidence.get(field), f"narrative {field}") != value
            for field, value in zip(
                ("giver_vnum", "room_vnum", "object_vnum"), identity,
            )
        )
    ):
        raise ValueError("hoard narrative identity differs from the active assignment")
    if (
        type(tool_vnum) is not int or tool_vnum <= 0
        or isinstance(carried_tool_vnums, (str, bytes))
        or not isinstance(carried_tool_vnums, Collection)
        or any(type(value) is not int or value <= 0 for value in carried_tool_vnums)
        or tool_vnum not in carried_tool_vnums
    ):
        raise ValueError("the exact source digging tool must be present in observed inventory")
    tool = world.objects.get(tool_vnum)
    if tool is None or tool.item_type != ITEM_DIGGER:
        raise ValueError("the carried tool is not a source-identified digging implement")
    if quest.object_vnum not in world.objects:
        raise ValueError("the hoard quest object is absent from the source catalog")
    source_level_bounds = source_tool_level_bounds
    if source_level_bounds is not None:
        if source_level_bounds != shop_digger_level_bounds(tool):
            raise ValueError("shop-stock tool level range differs from source fuzz bounds")
    endpoint = world.rooms.get(identity[1])
    if endpoint is None:
        raise ValueError("the hoard endpoint is absent from the source room catalog")
    budget = tool_dig_budget(
        tool,
        sector_type=endpoint.sector_type,
        race=race,
        level=character_level,
        observed_tool_level=observed_tool_level,
        strength=strength,
        constitution=constitution,
        dexterity=dexterity,
        swiftness=swiftness,
        enhanced_swiftness_percent=enhanced_swiftness_percent,
        source_tool_level_bounds=source_level_bounds,
        haste=haste,
        quicken=quicken,
        bonus_attack=bonus_attack,
        cannot_see_self=cannot_see_self,
        slow=slow,
    )
    route = hoard_return_plan(
        world,
        identity[1],
        registered_healer_vnum=healer_vnum,
        character_level=character_level,
        maximum_commands=maximum_route_commands,
        slow=slow,
        allow_exact_live_where_hazards=allow_exact_live_where_hazards,
        flying=flying,
    )
    movement = plan_hoard_movement_circuits(
        route,
        budget,
        maximum_movement=maximum_movement,
        starting_movement=starting_movement,
        maximum_route_commands=maximum_route_commands,
    )
    direct_trap_damage = maximum_hoard_direct_damage(character_level, armor_class)
    guardian = hoard_guardian_damage(
        world, character_level=character_level, sanctuary=sanctuary,
    )
    guardian_window = guardian.maximum_damage_before_command(
        budget.maximum_wait_pulses,
        every_hit_critical=True,
    )
    return HoardExecutionPlan(
        identity,
        tool,
        budget,
        route,
        movement,
        direct_trap_damage,
        guardian,
        guardian_window,
    )


def _live_mobile_route_issue(
    required_mobile_vnums: Collection[int],
    route_rooms: Collection[int],
    locations_by_mobile_vnum: Mapping[int, Collection[int]],
) -> str | None:
    if not isinstance(locations_by_mobile_vnum, Mapping):
        return "live where evidence is not a complete mobile-location map"
    remaining_rooms = set(route_rooms)
    for mobile_vnum in required_mobile_vnums:
        raw_locations = locations_by_mobile_vnum.get(mobile_vnum)
        if (
            raw_locations is None
            or isinstance(raw_locations, (str, bytes))
            or not isinstance(raw_locations, Collection)
        ):
            return f"fresh complete where evidence is missing for mobile {mobile_vnum}"
        locations = tuple(raw_locations)
        if any(type(room_vnum) is not int for room_vnum in locations):
            return f"where evidence for mobile {mobile_vnum} has an unresolved room"
        if remaining_rooms.intersection(locations):
            return f"mobile {mobile_vnum} is reported on the planned route"
    return None


def hoard_return_plan(
    world: WorldSource, endpoint: int, *, registered_healer_vnum: int,
    character_level: int, maximum_commands: int = 60, slow: bool = False,
    allow_exact_live_where_hazards: bool = False,
    flying: bool = False,
) -> HoardReturnPlan:
    """Audit an on-foot outbound leg, return, and every source-open flee branch.

    A curse can prevent recall and a trap strips invisibility. Do not rely on
    either, nor on flight lasting through excavation. DD4 chooses the flee
    direction randomly; callers cannot select just the convenient branch.
    Live exits, hazards, guardian damage, post-hex carrying capacity, and
    actual flee confirmation remain separate preconditions. The optional
    exact-locator mode only creates a conditional source plan; the caller must
    enforce its complete, fresh location checks before dispatch and every leg.
    """
    if (
        any(type(n) is not int for n in (endpoint, registered_healer_vnum,
                                       character_level, maximum_commands))
        or not 1 <= character_level <= 100 or not 1 <= maximum_commands <= 240
        or type(slow) is not bool or type(allow_exact_live_where_hazards) is not bool
        or type(flying) is not bool
        or endpoint == registered_healer_vnum
    ):
        raise ValueError("invalid hoard return identity or finite route bound")
    healer = world.rooms.get(registered_healer_vnum)
    origin = world.rooms.get(endpoint)
    if healer is None or not healer.room_flags & _ROOM_HEALING or origin is None:
        raise ValueError("hoard return requires a source-registered healing endpoint")

    # Ordinary unlocked doors use explicit open commands. Keys, secret doors,
    # flight, private rooms, and randomized exits need separate capabilities.
    # Never mutate the shared source catalog.
    rooms = {
        vnum: replace(room, exits={
            direction: edge for direction, edge in room.exits.items()
            if direction in _DIRECTIONS and not (edge.closed and edge.locked)
            and not edge.flags & (EX_WALL | 256)
        })
        for vnum, room in world.rooms.items()
        if not room.random_exits and not room.room_flags & _RESTRICTED_ROOMS
        and room.sector_type in _LAND_SECTORS
        and source_room_level_rejection(room, character_level) is None
    }
    if endpoint not in rooms or registered_healer_vnum not in rooms:
        raise ValueError("hoard endpoint or healer needs unsupported access")
    locator_vnums: tuple[int, ...] = ()
    route_world = world
    if allow_exact_live_where_hazards:
        locator_vnums = _exact_hoard_locator_resets(world)
        route_world = replace(
            world,
            mob_resets=[r for r in world.mob_resets if r.mobile_vnum not in locator_vnums],
        )

    multiplier = 3 if slow else 1
    blocked = _route_hazard_rooms(
        route_world, _resets_by_room(route_world), character_level=character_level,
        require_no_combat_hazards=True,
    )

    def audit(path: tuple[int, ...]) -> None:
        if any(reset.room_vnum in path and reset.mobile_vnum not in route_world.mobiles
               for reset in route_world.mob_resets):
            raise ValueError("hoard return route contains an unresolved mobile reset")
        issues = source_route_hazard_rejections(
            route_world, path, character_level=character_level,
            require_no_combat_hazards=True, combat_at_destination=True,
        )
        if issues:
            raise ValueError("hoard physical return is unsafe: " + "; ".join(issues))

    def route_from(
        start: int, *, exclude_endpoint: bool, allow_guardian_room_reentry: bool = False,
    ) -> HoardReturnRoute:
        path = _shortest_paths_from(
            rooms, start, blocked_rooms=blocked | ({endpoint} if exclude_endpoint else set()),
        ).get(registered_healer_vnum)
        required_absent = (_HOARD_GUARDIAN_VNUM,)
        if (
            path is None and exclude_endpoint and allow_guardian_room_reentry
        ):
            path = _shortest_paths_from(rooms, start, blocked_rooms=blocked).get(
                registered_healer_vnum
            )
        if path is None or len(path[0]) > maximum_commands:
            raise ValueError("hoard has no bounded physical return to its registered healer")
        audit(path[1])
        return HoardReturnRoute(
            path[0], path[1], multiplier * source_route_movement_cost(
                world, path[1], flying=flying,
            ),
            required_absent,
        )

    outbound_path = _shortest_paths_from(rooms, registered_healer_vnum, blocked_rooms=blocked).get(
        endpoint
    )
    if outbound_path is None or len(outbound_path[0]) > maximum_commands:
        raise ValueError("hoard has no bounded source route from the registered healer")
    audit(outbound_path[1])
    outbound = HoardReturnRoute(
        outbound_path[0], outbound_path[1],
        multiplier * source_route_movement_cost(
            world, outbound_path[1], flying=flying,
        ),
    )
    physical = route_from(endpoint, exclude_endpoint=False)
    preparation = (
        (physical.commands[0],)
        if physical.commands and physical.commands[0].startswith("open ") else ()
    )
    prepared_direction = preparation[0].split()[1] if preparation else None
    exits = tuple(sorted(
        (direction, edge) for direction, edge in origin.exits.items()
        if not edge.closed or direction == prepared_direction
    ))
    if not exits:
        raise ValueError("hoard endpoint has no source-backed escape")
    if len(preparation) + len(physical.commands) > maximum_commands:
        raise ValueError("hoard preparation and return exceed their combined command bound")
    branches = []
    for direction, edge in exits:
        if (
            direction not in _DIRECTIONS or edge.flags & (EX_WALL | 256)
            or edge.destination not in rooms or edge.destination == endpoint
        ):
            raise ValueError("an open hoard exit has no supported escape destination")
        audit((endpoint, edge.destination))
        retreat = route_from(
            edge.destination, exclude_endpoint=True, allow_guardian_room_reentry=True,
        )
        if len(preparation) + len(retreat.commands) + 1 > maximum_commands:
            raise ValueError("hoard flee and return exceed their combined command bound")
        branches.append(HoardEscapeBranch(
            direction, edge.destination,
            multiplier * source_route_movement_cost(
                world, (endpoint, edge.destination), flying=flying,
            ),
            retreat,
        ))
    locator_selectors = tuple(
        (vnum, world.mobiles[vnum].keywords.split()[0]) for vnum in locator_vnums
    )
    return HoardReturnPlan(
        endpoint, registered_healer_vnum, outbound, preparation,
        physical, tuple(branches), locator_vnums, locator_selectors, flying,
    )
