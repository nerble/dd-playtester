"""Source bounds for one ordinary armed mobile's complete reset loadout."""

from dataclasses import dataclass, replace

from .equipment import is_bow, normalize_item_name
from .hunt_candidates import (
    ITEM_DONOT_RANDOMISE, ITEM_PILL, ITEM_POTION, ITEM_SCROLL, ITEM_STAFF, ITEM_WAND, ITEM_WEAPON,
    HuntCandidate, SourceCombatOutput, WorldSource,
    _apply_mobile_damage_modifier, _mobile_normal_hit_damage,
)


def sanctuary_limited_output(output: SourceCombatOutput) -> SourceCombatOutput:
    """Apply fight.c's target sanctuary before ordinary damage planning."""
    fields = (
        "minimum_damage", "expected_damage", "maximum_damage", "conservative_damage",
        "opening_min_damage", "opening_expected_damage", "opening_max_damage",
        "opening_conservative_damage",
    )
    return replace(output, **{
        field: value // 2 if (value := getattr(output, field)) is not None else None
        for field in fields
    }, source_reference=f"{output.source_reference}; fight.c:target sanctuary")


@dataclass(frozen=True)
class SingleWeaponLoadout:
    weapon_vnum: int
    damage_bonus: int
    hitpoint_bonus: int
    wear_locations: tuple[int, ...]
    target_sanctuary: bool = False

    def extra_hit_damage(self, candidate: HuntCandidate, level: int) -> int:
        base = _mobile_normal_hit_damage(level, wielding=True)
        return max(0, _apply_mobile_damage_modifier(
            base + self.damage_bonus, candidate.source_damage_modifier,
        ) - _apply_mobile_damage_modifier(base, candidate.source_damage_modifier))

    def peak_damage(self, candidate: HuntCandidate) -> int:
        level = candidate.estimated_level_range[1]
        return candidate.estimated_peak_round_damage + self.extra_hit_damage(candidate, level) * (
            5 + int(level >= 20)
        )

    def critical_damage(self, candidate: HuntCandidate) -> int:
        level = candidate.estimated_level_range[1]
        return candidate.estimated_critical_hit_damage + 2 * self.extra_hit_damage(candidate, level)


def single_weapon_loadout(
    candidate: HuntCandidate, world: WorldSource | None,
) -> SingleWeaponLoadout | None:
    """Audit a singleton prototype; movement never grants combat permission."""
    if (
        world is None or not candidate.autonomous_safe or candidate.specials
        or len(candidate.equipped_weapons) != 1
        or candidate.source_spawn_limit != 1 or candidate.room_spawn_count != 1
    ):
        return None
    mobile = world.mobiles.get(candidate.mobile_vnum)
    resets = [r for r in world.mob_resets if r.mobile_vnum == candidate.mobile_vnum]
    if (
        mobile is None or mobile.aggressive or mobile.fear_aura or mobile.confused
        or mobile.act_flags & (1 << 2) or mobile.programs
        or world.mobile_specials.get(mobile.vnum)
        or not mobile.damage_modifier_known or mobile.damage_modifier is None
        or candidate.level != mobile.level
        or candidate.source_damage_modifier != mobile.damage_modifier
        or mobile.rank.casefold() not in {"common", "none"}
        or mobile.affected_flags & ((1 << 13) | (1 << 22) | (1 << 24))
        or len(resets) != 1 or resets[0].room_vnum != candidate.room_vnum
        or resets[0].maximum_count != 1
    ):
        return None
    reset = resets[0]
    slots = [slot for slot, _vnum in reset.equipment]
    if (
        len(slots) != len(set(slots)) or slots.count(16) != 1 or 18 in slots
        or any(type(slot) is not int or not 0 <= slot <= 20 for slot in slots)
    ):
        return None
    weapon_vnum = next(vnum for slot, vnum in reset.equipment if slot == 16)
    weapon = world.objects.get(weapon_vnum)
    if (
        weapon is None or weapon.item_type != ITEM_WEAPON or is_bow(weapon)
        or weapon.extra_flags & (1 << 14)
        or normalize_item_name(weapon.short_description)
        != normalize_item_name(candidate.equipped_weapons[0])
    ):
        return None
    for vnum in set(reset.object_vnums) | {vnum for _slot, vnum in reset.equipment}:
        item = world.objects.get(vnum)
        if (
            item is None or item.item_type in {ITEM_PILL, ITEM_POTION, ITEM_SCROLL, ITEM_STAFF, ITEM_WAND}
            or item.item_type == ITEM_WEAPON and vnum != weapon_vnum
        ):
            return None
    damage_bonus = hitpoint_bonus = 0
    # NPC base stats stay 13; ordinary saves, AC and hitroll add no damage.
    passive_affects = {0, 1, 2, 3, 4, 5, 12, 14, 17, 18, 20, 21, 22, 23, 24}
    for _slot, vnum in reset.equipment:
        item = world.objects[vnum]
        fixed = bool(item.extra_flags & ITEM_DONOT_RANDOMISE)
        # db.c uses prototype level - 2 for reset gear. Fickle items can use
        # the strong randomiser even at low levels, introducing new affects.
        weak = bool(item.extra_flags & (1 << 38)) or mobile.level - 2 < 40
        if not fixed and (item.extra_flags & (1 << 39) or not weak):
            return None
        for location, amount in item.affects:
            if type(location) is not int or type(amount) is not int:
                return None
            if location == 19:
                damage_bonus += max(0, amount) if fixed else max(0, (5 * amount + 3) // 4)
            elif location == 13:
                hitpoint_bonus += max(0, amount) if fixed else max(0, (5 * amount + 3) // 4)
            elif location not in passive_affects:
                return None
    return SingleWeaponLoadout(
        weapon_vnum, damage_bonus, hitpoint_bonus, tuple(slots),
        target_sanctuary=bool(mobile.affected_flags & (1 << 7)),
    )
