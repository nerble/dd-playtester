"""Walking-return evidence for hoards; not permission to excavate or flee."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .hunt_candidates import (
    EX_WALL,
    WorldSource,
    _resets_by_room,
    _route_hazard_rooms,
    _shortest_paths_from,
    source_room_level_rejection,
    source_route_hazard_rejections,
    source_route_movement_cost,
)


_ROOM_HEALING = 1 << 16
_RESTRICTED_ROOMS = (1 << 9) | (1 << 11)  # private / solitary
_LAND_SECTORS = frozenset({0, 1, 2, 3, 4, 5, 10, 11})
_DIRECTIONS = frozenset({"north", "east", "south", "west", "up", "down"})


@dataclass(frozen=True)
class HoardReturnRoute:
    commands: tuple[str, ...]
    rooms: tuple[int, ...]
    movement: int


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
    preparation_commands: tuple[str, ...]
    physical_return: HoardReturnRoute
    escape_branches: tuple[HoardEscapeBranch, ...]

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


def hoard_return_plan(
    world: WorldSource, endpoint: int, *, registered_healer_vnum: int,
    character_level: int, maximum_commands: int = 60, slow: bool = False,
) -> HoardReturnPlan:
    """Audit a visible, on-foot return and every source-open flee branch.

    A curse can prevent recall and a trap strips invisibility. Do not rely on
    either, nor on flight lasting through excavation. DD4 chooses the flee
    direction randomly; callers cannot select just the convenient branch.
    Live exits, hazards, guardian damage, post-hex carrying capacity, and
    actual flee confirmation remain separate preconditions.
    """
    if (
        any(type(n) is not int for n in (endpoint, registered_healer_vnum,
                                       character_level, maximum_commands))
        or not 1 <= character_level <= 100 or not 1 <= maximum_commands <= 60
        or type(slow) is not bool or endpoint == registered_healer_vnum
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
    multiplier = 3 if slow else 1
    blocked = _route_hazard_rooms(
        world, _resets_by_room(world), character_level=character_level,
        require_no_combat_hazards=True,
    )

    def audit(path: tuple[int, ...]) -> None:
        if any(reset.room_vnum in path and reset.mobile_vnum not in world.mobiles
               for reset in world.mob_resets):
            raise ValueError("hoard return route contains an unresolved mobile reset")
        issues = source_route_hazard_rejections(
            world, path, character_level=character_level,
            require_no_combat_hazards=True, combat_at_destination=True,
        )
        if issues:
            raise ValueError("hoard physical return is unsafe: " + "; ".join(issues))

    def route_from(start: int, *, exclude_endpoint: bool) -> HoardReturnRoute:
        path = _shortest_paths_from(
            rooms, start, blocked_rooms=blocked | ({endpoint} if exclude_endpoint else set()),
        ).get(registered_healer_vnum)
        if path is None or len(path[0]) > maximum_commands:
            raise ValueError("hoard has no bounded physical return to its registered healer")
        audit(path[1])
        return HoardReturnRoute(
            path[0], path[1], multiplier * source_route_movement_cost(world, path[1]),
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
        retreat = route_from(edge.destination, exclude_endpoint=True)
        if len(preparation) + len(retreat.commands) + 1 > maximum_commands:
            raise ValueError("hoard flee and return exceed their combined command bound")
        branches.append(HoardEscapeBranch(
            direction, edge.destination,
            multiplier * source_route_movement_cost(world, (endpoint, edge.destination)),
            retreat,
        ))
    return HoardReturnPlan(endpoint, registered_healer_vnum, preparation,
                           physical, tuple(branches))
