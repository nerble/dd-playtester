"""Bounded source paths for the existing live locator controller."""

from dataclasses import dataclass, replace
from typing import Collection

from .hunt_candidates import (
    EX_WALL, WorldSource, _shortest_paths_from, source_mobile_search_rooms,
    source_route_hazard_rejections, source_route_requires_flight,
)


def source_locator_path_is_safe(
    world: WorldSource,
    rooms: Collection[int],
    *,
    character_level: int | None,
    require_invisibility: bool = False,
) -> bool:
    # Private, solitary, and no-recall rooms introduce a recovery boundary.
    return bool(
        character_level is not None and character_level > 0
        and not any(
            vnum not in world.rooms or world.rooms[vnum].random_exits
            or world.rooms[vnum].room_flags & ((1 << 9) | (1 << 11) | (1 << 13))
            for vnum in rooms
        )
        and not source_route_requires_flight(world, rooms)
        and not source_route_hazard_rejections(
            world,
            rooms,
            character_level=character_level,
            combat_at_destination=False,
            invisible=require_invisibility,
        )
    )


@dataclass(frozen=True)
class SourceLocatorPaths:
    locations: tuple[tuple[str, tuple[str, ...]], ...]
    relocations: tuple[tuple[str, str, tuple[str, ...]], ...]
    search_routes: tuple[tuple[str, ...], ...]


def bounded_carrier_locator_paths(
    world: WorldSource, mobile_vnum: int, *, origin: int, character_level: int,
    maximum_rooms: int = 8, maximum_steps: int = 24,
    require_invisibility: bool = False,
) -> SourceLocatorPaths | None:
    """Map a same-area wanderer without granting combat or crossing hazards."""
    mobile, room = world.mobiles.get(mobile_vnum), world.rooms.get(origin)
    if (
        mobile is None or room is None or not mobile.wanders
        or not mobile.stay_area or mobile.confused or mobile.programs
        or mobile.area_file != room.area_file
        or maximum_rooms < 1 or maximum_steps < 1
    ):
        return None
    reachable = source_mobile_search_rooms(world, mobile_vnum, maximum_rooms=512)
    allowed = {
        vnum: replace(candidate, exits={
            direction: exit_ for direction, exit_ in candidate.exits.items()
            if not exit_.closed and not exit_.flags & EX_WALL
        })
        for vnum, candidate in world.rooms.items()
        if candidate.area_file == room.area_file
        and candidate.sector_type in range(6)
        and source_locator_path_is_safe(
            world,
            (vnum,),
            character_level=character_level,
            require_invisibility=require_invisibility,
        )
    }
    if origin not in allowed:
        return None
    paths = _shortest_paths_from(allowed, origin)
    candidates = {
        vnum for vnum in reachable if vnum in paths
        and len(paths[vnum][0]) <= maximum_steps
    }
    if not candidates:
        return None
    current, remaining_steps = origin, maximum_steps
    destinations, search_routes = [], []
    represented_labels: set[str] = set()
    # Price the whole fallback sweep, not eight independently short trips.
    while candidates and len(destinations) < maximum_rooms:
        paths = _shortest_paths_from(allowed, current)
        choices = []
        for vnum in candidates:
            path = paths.get(vnum)
            if path is None or len(path[0]) > remaining_steps:
                continue
            label = " ".join(world.rooms[vnum].name.casefold().split())
            # ``where`` reports room labels rather than VNUMs. Reserve space
            # for a new label before adding another same-label waypoint so a
            # bounded plan can act on the live locator instead of discarding
            # a uniquely named carrier room beyond the nearest-room prefix.
            choices.append(
                (label in represented_labels, len(path[0]), vnum, path, label)
            )
        if not choices:
            break
        _, cost, destination, path, label = min(choices)
        destinations.append(destination)
        search_routes.append(tuple(str(vnum) for vnum in path[1][1:]))
        candidates.remove(destination)
        represented_labels.add(label)
        current, remaining_steps = destination, remaining_steps - cost
    labels: dict[str, list[str]] = {}
    for vnum in reachable:
        if vnum in world.rooms:
            label = " ".join(world.rooms[vnum].name.casefold().split())
            if label:
                labels.setdefault(label, [])
    for vnum in destinations:
        label = " ".join(world.rooms[vnum].name.casefold().split())
        labels.setdefault(label, []).append(str(vnum))
    relocations = []
    for start in dict.fromkeys((origin, *destinations)):
        paths = _shortest_paths_from(allowed, start)
        for destination in destinations:
            path = paths.get(destination)
            if path is None or len(path[0]) > maximum_steps:
                continue
            label = " ".join(world.rooms[destination].name.casefold().split())
            relocations.append((str(start), label, tuple(str(vnum) for vnum in path[1][1:])))
    return SourceLocatorPaths(
        tuple((label, tuple(vnums)) for label, vnums in sorted(labels.items())),
        tuple(relocations), tuple(search_routes),
    )
