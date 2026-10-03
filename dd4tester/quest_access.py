from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Mapping

from .equipment import ITEM_KEY
from .hunt_candidates import (
    WorldSource, _reset_object_vnums, _shortest_paths_from,
    source_route_hazard_rejections, source_safe_route_to_room,
    source_mobile_has_only_economic_transit_risk, source_mobile_search_rooms,
)
from .quests import snapshot_quest_status

if TYPE_CHECKING:
    from .fastwalks import Fastwalk


ECONOMIC_QUEST_MAX_COPPER = 250


def observed_stealable_copper(currencies: Any) -> int | None:
    """Mirror act_obj.c:total_coins_char, requiring all four observed values."""
    if not isinstance(currencies, Mapping):
        return None
    total = 0
    for name, value in (("platinum", 1000), ("gold", 100), ("silver", 10), ("copper", 1)):
        amount = currencies.get(name)
        if type(amount) is not int or amount < 0:
            return None
        total += amount * value
    return total


@dataclass(frozen=True)
class EconomicQuestTransit:
    commands: tuple[str, ...]
    room_vnums: tuple[int, ...]
    mobile_vnums: tuple[int, ...]


def economic_quest_transit(
    world: WorldSource, room_vnum: int, *, character_level: int, currencies: Any,
) -> EconomicQuestTransit | None:
    """Accept at most one whole small purse of theft risk on a noncombat route."""
    wallet = observed_stealable_copper(currencies)
    if wallet is None or wallet > ECONOMIC_QUEST_MAX_COPPER:
        return None
    path = _shortest_paths_from(world.rooms, 3001).get(room_vnum)
    if (
        path is None or not path[0] or len(path[0]) > 60
        or any(world.rooms[vnum].random_exits for vnum in path[1])
    ):
        return None
    rooms = set(path[1])
    permitted = tuple(sorted(
        vnum for vnum, specials in world.mobile_specials.items()
        if set(specials) == {"spec_thief"}
        and source_mobile_has_only_economic_transit_risk(world, vnum)
        and rooms.intersection(source_mobile_search_rooms(world, vnum))
    ))
    if not permitted or source_route_hazard_rejections(
        world, path[1], character_level=character_level,
        combat_at_destination=False, economic_special_mobile_vnums=permitted,
    ):
        return None
    return EconomicQuestTransit(path[0], path[1], permitted)


def economic_quest_runtime_issue(
    route: Fastwalk, world: WorldSource | None, *, status: Mapping[str, Any],
    currencies: Any,
) -> str | None:
    """Revalidate quest and economic admission without authorizing a fight."""
    if not isinstance(status, Mapping):
        return "economic quest transit lacks its live quest identity"
    quest = snapshot_quest_status(status)
    identity = (status.get("giver_vnum"), quest.room_vnum, quest.object_vnum)
    try:
        identity = tuple(int(value) for value in identity)
    except (TypeError, ValueError):
        return "economic quest transit lacks its live quest identity"
    if (
        not quest.active or quest.kind != "retrieve" or min(identity) <= 0
        or quest.mob_vnum != 0 or quest.countdown <= 0
        or identity != route.route_economic_quest_identity
    ):
        return "economic quest transit no longer matches the live retrieval assignment"
    wallet = observed_stealable_copper(currencies)
    if (
        route.route_economic_max_copper != ECONOMIC_QUEST_MAX_COPPER
        or wallet is None or wallet > ECONOMIC_QUEST_MAX_COPPER
    ):
        return "economic quest transit exceeds its observed whole-purse limit"
    if world is None or not route.route_economic_special_mobile_vnums or not all(
        source_mobile_has_only_economic_transit_risk(world, vnum)
        for vnum in route.route_economic_special_mobile_vnums
    ):
        return "economic quest transit lost its exact source special audit"
    return None


def economic_quest_route_evidence(route: Fastwalk | None, currencies: Any) -> dict[str, Any] | None:
    """Record the selected admission, not a claim of successful live travel."""
    if route is None or not route.route_economic_special_mobile_vnums:
        return None
    return {
        "quest_identity": route.route_economic_quest_identity,
        "mobile_vnums": route.route_economic_special_mobile_vnums,
        "whole_purse_limit": route.route_economic_max_copper,
        "observed_purse": observed_stealable_copper(currencies),
        "commands": route.commands,
        "combat_authorized": False,
    }


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
