from __future__ import annotations

from dataclasses import dataclass

from .equipment import ITEM_KEY
from .hunt_candidates import (
    WorldSource, _reset_object_vnums, _shortest_paths_from,
    source_route_hazard_rejections, source_safe_route_to_room,
)


@dataclass(frozen=True)
class CircusAdmission:
    approach: tuple[str, ...]
    continuation: tuple[str, ...]
    room_vnums: tuple[int, ...]


def circus_quest_admission(
    world: WorldSource, room_vnum: int, *, character_level: int,
) -> CircusAdmission | None:
    """Audit the existing ticket purchase before a noncombat Big Top quest."""
    room = world.rooms.get(room_vnum)
    entrance = world.rooms.get(4415)
    door = entrance.exits.get("south") if entrance is not None else None
    ticket = world.objects.get(4400)
    clerk = world.mobiles.get(4400)
    if (
        room is None or room.area_file != "circus.are"
        or door is None or door.destination != 4416 or door.key_vnum != 4400
        or not door.closed or not door.locked
        or ticket is None or ticket.item_type != ITEM_KEY
        or ticket.keywords.casefold() != "ticket"
        or ticket.short_description.casefold() != "a ticket"
        or sum(o.short_description.casefold() == "a ticket" for o in world.objects.values()) != 1
        or clerk is None or not clerk.sentinel or clerk.aggressive
        or clerk.programs or world.mobile_specials.get(clerk.vnum)
        or clerk.vnum not in world.shopkeepers
    ):
        return None
    resets = [r for r in world.mob_resets if r.mobile_vnum == clerk.vnum]
    if (
        len(resets) != 1 or resets[0].room_vnum != 4402
        or 4400 not in _reset_object_vnums(resets[0])
    ):
        return None
    approach = source_safe_route_to_room(world, 4402, character_level=character_level)
    continuation = _shortest_paths_from(
        world.rooms, 4402, unlockable_key_vnums=(4400,),
    ).get(room_vnum)
    if approach is None or continuation is None:
        return None
    rooms = (*approach[1], *continuation[1][1:])
    if (
        4415 not in continuation[1] or 4416 not in continuation[1]
        or "unlock south" not in continuation[0]
        or any(world.rooms[vnum].area_file != "circus.are" for vnum in continuation[1])
        or len(approach[0]) + len(continuation[0]) > 40
        or source_route_hazard_rejections(
            world, rooms, character_level=character_level, combat_at_destination=False,
        )
    ):
        return None
    return CircusAdmission(approach[0], continuation[0], rooms)
