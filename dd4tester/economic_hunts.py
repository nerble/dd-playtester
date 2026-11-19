"""Bounded coin exposure on ordinary XP routes, separate from quest travel."""

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from .hunt_candidates import (
    ITEM_DONOT_RANDOMISE, ITEM_PILL, ITEM_POTION, ITEM_SCROLL, ITEM_STAFF,
    ITEM_WAND, ITEM_WEAPON, HuntCandidate, WorldSource,
    source_mobile_search_rooms,
)
from .populations import plain_bounded_population


ECONOMIC_HUNT_MAX_COPPER = 1250
_ECONOMIC_ROUTE_REJECTION = "an economic special mobile can reach the route"
_CAPACITY_REJECTION = "target reset capacity exceeds one"
_SPELL_ITEMS = {ITEM_PILL, ITEM_POTION, ITEM_SCROLL, ITEM_STAFF, ITEM_WAND}
_ECONOMIC_TARGET_NONTHREATENING_SPECIALS = frozenset({"spec_cast_adept"})
# DD4 merc.h: detect invis, detect hidden, sanctuary, protection, and pass door.
# These affect the target's defenses, not the danger it poses to the player.
_ECONOMIC_TARGET_PASSIVE_AFFECTS = (
    (1 << 3) | (1 << 5) | (1 << 7) | (1 << 13) | (1 << 20)
)
# The live source-ranked locator has its own eight-relocation action budget.
# This larger source audit only proves that a stay-area wanderer has a finite,
# source-defined search boundary before that runtime budget is used.
_ECONOMIC_TARGET_LOCATOR_ROOM_LIMIT = 512

# Hitroll and damroll are wear-location affects 18 and 19 in DD4. They can
# materially improve a route actor's damage, so they are not passive economic
# loadout evidence. Keep this allow-list explicit as the affect table grows.
_ECONOMIC_TARGET_ALLOWED_ITEM_AFFECTS = frozenset({
    0, 1, 2, 3, 4, 5, 12, 13, 14, 17, 20, 21, 22, 23, 24,
})
# The source steel dagger carried by the Quake thief has hitroll (18). It is
# harmless for route-only ``spec_thief`` transit, while damroll remains closed
# because it is unmodelled outgoing combat output if source behavior changes.
_ECONOMIC_ROUTE_ALLOWED_ITEM_AFFECTS = (
    _ECONOMIC_TARGET_ALLOWED_ITEM_AFFECTS | {18}
)


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


def passive_economic_hunt_mobile(
    world: WorldSource,
    vnum: int,
    *,
    level: int,
    allow_bounded_population: bool = False,
) -> bool:
    # WorldSource is intentionally mutable while source audits are refreshed
    # and runtime gates are rechecked. Do not cache by object identity: a
    # changed special or loadout must be observed immediately.
    return _passive_economic_hunt_mobile_uncached(
        world,
        vnum,
        level=level,
        allow_bounded_population=allow_bounded_population,
    )


def passive_economic_transit_mobile(
    world: WorldSource,
    vnum: int,
    *,
    level: int,
    allow_bounded_population: bool = False,
) -> bool:
    """Audit a spec_thief for route-only coin exposure.

    A thief's equipment can affect combat output, but ``spec_thief`` never
    initiates combat or uses that equipment to steal coins. Keep the stricter
    loadout audit for a possible target and use this narrower route contract
    when the mobile is only being crossed in transit.
    """
    return _passive_economic_hunt_mobile_uncached(
        world,
        vnum,
        level=level,
        allow_bounded_population=allow_bounded_population,
        route_only=True,
    )


def _passive_economic_hunt_mobile_uncached(
    world: WorldSource,
    vnum: int,
    *,
    level: int,
    allow_bounded_population: bool = False,
    route_only: bool = False,
) -> bool:
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
    ):
        return False

    if allow_bounded_population:
        # A target population may be capacity-research only while its
        # economic transit actor remains source-bounded. A thief with two to
        # four distinct, same-area singleton resets is safe for this
        # noncombat transit audit as well: it has a finite source population,
        # no loadout, and no combat permission. The multi-reset allowance is
        # never used for selecting or fighting the thief.
        if not (
            (len(resets) == 1 and resets[0].maximum_count == 1)
            or plain_bounded_economic_resets(world, mobile.vnum)
        ):
            return False
    elif len(resets) != 1 or resets[0].maximum_count != 1:
        return False

    for reset in resets:
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
            allowed_item_affects = (
                _ECONOMIC_ROUTE_ALLOWED_ITEM_AFFECTS
                if route_only else _ECONOMIC_TARGET_ALLOWED_ITEM_AFFECTS
            )
            if any(
                location not in allowed_item_affects
                for location, _amount in item.affects
            ):
                return False
            # Positive hitpoint affects on the target are observation/report
            # evidence, not a reason to close an otherwise plain economic
            # route.  Live consider and the player's own health floor decide
            # whether the encounter is worth continuing.
    return True


def plain_bounded_economic_resets(world: WorldSource, vnum: int) -> bool:
    """Audit a finite multi-reset thief for noncombat transit only.

    This deliberately does not call ``plain_bounded_mobile_population``:
    ``spec_thief`` is the one allowed economic special, while the target
    population still has to pass that independent plain-population proof.
    Counts of one are accepted here because this helper bounds the number of
    possible transit thieves, not the number of combat targets in a room.
    """
    mobile = world.mobiles.get(vnum)
    resets = tuple(reset for reset in world.mob_resets if reset.mobile_vnum == vnum)
    if (
        mobile is None
        or not 2 <= len(resets) <= 4
        or len({reset.room_vnum for reset in resets}) != len(resets)
        or any(
            type(reset.maximum_count) is not int
            or not 1 <= reset.maximum_count <= 4
            for reset in resets
        )
        or len({reset.maximum_count for reset in resets}) != 1
    ):
        return False
    for reset in resets:
        room = world.rooms.get(reset.room_vnum)
        if room is None or room.area_file != mobile.area_file or room.random_exits:
            return False
        if reset.object_vnums or reset.equipment:
            return False
    return True


def _bounded_economic_target_locator(
    candidate: HuntCandidate,
    mobile: object,
    world: WorldSource,
) -> bool:
    """Allow one plain stay-area target when its ``where`` search is bounded."""
    if (
        not getattr(mobile, "stay_area", False)
        or not getattr(mobile, "wanders", False)
        or not candidate.stay_area
        or candidate.sentinel
    ):
        return False
    reachable = source_mobile_search_rooms(
        world,
        candidate.mobile_vnum,
        maximum_rooms=_ECONOMIC_TARGET_LOCATOR_ROOM_LIMIT + 1,
    )
    return (
        0 < len(reachable) <= _ECONOMIC_TARGET_LOCATOR_ROOM_LIMIT
        and candidate.room_vnum in reachable
    )


def economic_hunt_candidate(
    candidate: HuntCandidate, state: Mapping[str, Any], world: WorldSource,
) -> HuntCandidate:
    """Remove economic travel risk, retaining independent population limits."""
    level = state.get("level")
    purse = known_purse(state.get("currencies"))
    # Most source candidates are ordinary targets. Do not run the expensive
    # wanderer locator or reset-population audits until the candidate has the
    # specific economic-route rejection this adapter is meant to repair.
    if (
        type(level) is not int
        or purse is None
        or purse > ECONOMIC_HUNT_MAX_COPPER
        or _ECONOMIC_ROUTE_REJECTION not in candidate.autonomy_rejections
    ):
        return candidate
    mobile = world.mobiles.get(candidate.mobile_vnum)
    remaining_rejections = set(candidate.autonomy_rejections) - {_ECONOMIC_ROUTE_REJECTION}
    candidate_specials = set(candidate.specials)
    source_specials = set(world.mobile_specials.get(candidate.mobile_vnum, ()))
    target_special_rejections = {
        f"target has special procedure {str(special).strip().casefold()}"
        for special in candidate_specials
        if special not in _ECONOMIC_TARGET_NONTHREATENING_SPECIALS
    }
    unhandled_rejections = remaining_rejections - target_special_rejections
    population = bool(
        unhandled_rejections == {_CAPACITY_REJECTION}
        and plain_bounded_population(replace(
            candidate, status="reject", autonomy_rejections=(_CAPACITY_REJECTION,),
        ), world)
    )
    economic_route_population = bool(
        type(level) is int
        and candidate.route_special_mobile_vnums
        and all(
            plain_bounded_economic_resets(world, vnum)
            for vnum in candidate.route_special_mobile_vnums
        )
    )
    bounded_target_locator = (
        mobile is not None
        and _bounded_economic_target_locator(candidate, mobile, world)
    )
    if (
        type(level) is not int or purse is None or purse > ECONOMIC_HUNT_MAX_COPPER
        or _ECONOMIC_ROUTE_REJECTION not in candidate.autonomy_rejections
        or unhandled_rejections and not population
        or not target_special_rejections.issubset(candidate.autonomy_rejections)
        or candidate_specials != source_specials
        or candidate.is_coin_stash or candidate.is_food_stash
        or candidate.equipped_weapons
        or not (candidate.sentinel or population or bounded_target_locator)
        or not population and candidate.source_spawn_limit != 1
        or candidate.room_spawn_count != 1
        or candidate.route_hard_hazard_targets
        or mobile is None or mobile.aggressive or mobile.fear_aura or mobile.confused
        or mobile.non_corporeal or mobile.programs
        or mobile.affected_flags & ~_ECONOMIC_TARGET_PASSIVE_AFFECTS
        or not (mobile.sentinel or population or bounded_target_locator)
        or not mobile.damage_modifier_known or not mobile.hp_modifier_known
        or candidate.source_damage_modifier != mobile.damage_modifier
        or not candidate.route_special_mobile_vnums
        or any(
            not passive_economic_transit_mobile(
                world,
                vnum,
                level=level,
                allow_bounded_population=(population or economic_route_population),
            )
            for vnum in candidate.route_special_mobile_vnums
        )
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
            or any(location not in _ECONOMIC_TARGET_ALLOWED_ITEM_AFFECTS
                   for location, _amount in item.affects)
            # DD4's strong randomiser can add damage, hit, crit, or
            # swiftness affects to an equipped item. Keep that uncertainty
            # out of an economic route until its incoming-output bound is
            # modelled; weak randomisation below the source threshold is
            # limited to the prototype's existing affects.
            or not item.extra_flags & ITEM_DONOT_RANDOMISE and (
                item.extra_flags & (1 << 39)
                or mobile.level - 2 >= 40 and not item.extra_flags & (1 << 38)
            )
        ):
            return candidate
    return replace(
        candidate, status="reject" if population else "caution",
        autonomy_rejections=tuple(sorted(remaining_rejections)),
        route_economic_hunt_mobile_vnums=candidate.route_special_mobile_vnums,
        route_economic_population=(population or economic_route_population),
        route_economic_source_rejections=tuple(
            rejection
            for rejection in candidate.autonomy_rejections
            if rejection in {_ECONOMIC_ROUTE_REJECTION, _CAPACITY_REJECTION}
        ),
    )


def economic_hunt_runtime_issue(
    route: Any,
    world: WorldSource | None,
    *,
    level: int,
    currencies: object,
    allow_bounded_population: bool = False,
) -> str | None:
    if not route.route_economic_hunt_mobile_vnums:
        return None
    purse = known_purse(currencies)
    if purse is None or purse > ECONOMIC_HUNT_MAX_COPPER:
        return "ordinary XP route exceeded its known economic coin reserve"
    if world is None or any(
        not passive_economic_transit_mobile(
            world,
            vnum,
            level=level,
            allow_bounded_population=allow_bounded_population,
        )
        for vnum in route.route_economic_hunt_mobile_vnums
    ):
        return "ordinary XP route economic source identity changed"
    return None
