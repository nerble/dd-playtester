"""Bounded coin exposure on ordinary XP routes, separate from quest travel."""

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from .hunt_candidates import (
    ITEM_DONOT_RANDOMISE, ITEM_PILL, ITEM_POTION, ITEM_SCROLL, ITEM_STAFF,
    ITEM_WAND, ITEM_WEAPON, HuntCandidate, WorldSource,
)
from .populations import plain_bounded_population


ECONOMIC_HUNT_MAX_COPPER = 1250
_ECONOMIC_ROUTE_REJECTION = "an economic special mobile can reach the route"
_CAPACITY_REJECTION = "target reset capacity exceeds one"
_SPELL_ITEMS = {ITEM_PILL, ITEM_POTION, ITEM_SCROLL, ITEM_STAFF, ITEM_WAND}


def known_purse(currencies: object) -> int | None:
    if not isinstance(currencies, Mapping):
        return None
    total = 0
    for name, scale in (("platinum", 1000), ("gold", 100), ("silver", 10), ("copper", 1)):
        value = currencies.get(name)
        if isinstance(value, bool) or not isinstance(value, (str, int)):
            return None
        try:
            amount = int(value)
        except ValueError:
            return None
        if amount < 0:
            return None
        total += amount * scale
    return total


def passive_economic_hunt_mobile(world: WorldSource, vnum: int, *, level: int) -> bool:
    """Audit a non-initiating spec_thief; never authorize fighting it."""
    mobile = world.mobiles.get(vnum)
    resets = [reset for reset in world.mob_resets if reset.mobile_vnum == vnum]
    if (
        mobile is None or mobile.aggressive or mobile.fear_aura or mobile.confused
        or mobile.non_corporeal or mobile.programs or mobile.rank not in {"common", "none"}
        or not mobile.damage_modifier_known or mobile.damage_modifier is None
        or mobile.damage_modifier > 0
        or mobile.level + 2 > level
        or tuple(world.mobile_specials.get(vnum, ())) != ("spec_thief",)
        or len(resets) != 1 or resets[0].maximum_count != 1
    ):
        return False
    reset = resets[0]
    slots = [slot for slot, _vnum in reset.equipment]
    if len(slots) != len(set(slots)) or 18 in slots:
        return False
    for object_vnum in set(reset.object_vnums) | {v for _slot, v in reset.equipment}:
        item = world.objects.get(object_vnum)
        if item is None or item.item_type in _SPELL_ITEMS or item.extra_flags & (1 << 14):
            return False
        if not item.extra_flags & ITEM_DONOT_RANDOMISE and (
            item.extra_flags & (1 << 39)
            or mobile.level - 2 >= 40 and not item.extra_flags & (1 << 38)
        ):
            return False
        if any(location not in {0, 1, 2, 3, 4, 5, 12, 13, 14, 17, 18, 19, 20, 21, 22, 23, 24}
               for location, _amount in item.affects):
            return False
        if any(location == 19 and amount > 0 for location, amount in item.affects):
            return False
    return True


def economic_hunt_candidate(
    candidate: HuntCandidate, state: Mapping[str, Any], world: WorldSource,
) -> HuntCandidate:
    """Remove economic travel risk, retaining independent population limits."""
    level = state.get("level")
    purse = known_purse(state.get("currencies"))
    mobile = world.mobiles.get(candidate.mobile_vnum)
    remaining_rejections = set(candidate.autonomy_rejections) - {_ECONOMIC_ROUTE_REJECTION}
    population = bool(
        remaining_rejections == {_CAPACITY_REJECTION}
        and plain_bounded_population(replace(
            candidate, status="reject", autonomy_rejections=(_CAPACITY_REJECTION,),
        ), world)
    )
    if (
        type(level) is not int or purse is None or purse > ECONOMIC_HUNT_MAX_COPPER
        or _ECONOMIC_ROUTE_REJECTION not in candidate.autonomy_rejections
        or remaining_rejections and not population
        or candidate.is_coin_stash or candidate.is_food_stash or candidate.specials
        or candidate.equipped_weapons or not (candidate.sentinel or population)
        or not population and candidate.source_spawn_limit != 1
        or candidate.room_spawn_count != 1
        or candidate.route_hard_hazard_targets
        or mobile is None or mobile.aggressive or mobile.fear_aura or mobile.confused
        or mobile.non_corporeal or mobile.programs or mobile.affected_flags
        or not (mobile.sentinel or population)
        or not mobile.damage_modifier_known or not mobile.hp_modifier_known
        or candidate.source_damage_modifier != mobile.damage_modifier
        or not candidate.route_special_mobile_vnums
        or any(not passive_economic_hunt_mobile(world, vnum, level=level)
               for vnum in candidate.route_special_mobile_vnums)
    ):
        return candidate
    resets = [r for r in world.mob_resets if r.mobile_vnum == mobile.vnum]
    if (
        not population and len(resets) != 1
        or not any(reset.room_vnum == candidate.room_vnum for reset in resets)
        or any(slot in {16, 18} for reset in resets for slot, _vnum in reset.equipment)
    ):
        return candidate
    objects = {v for reset in resets for v in reset.object_vnums}
    objects.update(v for reset in resets for _slot, v in reset.equipment)
    for vnum in objects:
        item = world.objects.get(vnum)
        if (
            item is None or item.item_type in _SPELL_ITEMS | {ITEM_WEAPON}
            or any(location not in {0, 1, 2, 3, 4, 5, 12, 14, 17, 18, 20, 21, 22, 23, 24}
                   for location, _amount in item.affects)
            or not item.extra_flags & ITEM_DONOT_RANDOMISE and (
                item.extra_flags & (1 << 39)
                or mobile.level - 2 >= 40 and not item.extra_flags & (1 << 38)
            )
        ):
            return candidate
    return replace(
        candidate, status="reject" if population else "caution",
        autonomy_rejections=(_CAPACITY_REJECTION,) if population else (),
        route_economic_hunt_mobile_vnums=candidate.route_special_mobile_vnums,
        route_economic_source_rejections=candidate.autonomy_rejections,
    )


def economic_hunt_runtime_issue(route: Any, world: WorldSource | None, *, level: int,
                                currencies: object) -> str | None:
    if not route.route_economic_hunt_mobile_vnums:
        return None
    purse = known_purse(currencies)
    if purse is None or purse > ECONOMIC_HUNT_MAX_COPPER:
        return "ordinary XP route exceeded its known economic coin reserve"
    if world is None or any(not passive_economic_hunt_mobile(world, vnum, level=level)
                            for vnum in route.route_economic_hunt_mobile_vnums):
        return "ordinary XP route economic source identity changed"
    return None
