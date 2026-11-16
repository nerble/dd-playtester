"""Source bounds for one ordinary armed mobile's complete reset loadout."""

from collections.abc import Collection
from dataclasses import dataclass, replace

from .equipment import normalize_item_name
from .hunt_candidates import (
    AFF_SANCTUARY, ITEM_INSTRUMENT, ITEM_ARMOR,
    ITEM_DONOT_RANDOMISE, ITEM_PILL, ITEM_POTION, ITEM_SCROLL, ITEM_STAFF, ITEM_WAND, ITEM_WEAPON,
    HuntCandidate, MobileSource, SourceCombatOutput, WorldSource,
    WEAR_DUAL, WEAR_WIELD,
    _apply_mobile_damage_modifier, _mobile_normal_hit_damage,
)
from .specials import SAFE_NONCOMBAT_SPECIALS, source_special_profile

_AFF_BATTLE_AURA = 1 << 22
_AFF_GLOBE = 1 << 24
_ITEM_HUM = 1 << 1
_ITEM_TAKE = 1
_ITEM_HOLD = 1 << 14
_WEAR_HOLD = 17
_ITEM_TRASH = 13


def bounded_low_guard_companion(
    world: WorldSource, mobile_vnum: int, room_vnum: int, character_level: int,
) -> bool:
    """Audit one low guard wearing armor or inert, detrimental restraints."""
    mobile = world.mobiles.get(mobile_vnum)
    if (
        mobile is None or mobile.level + 2 > character_level - 10
        or mobile.aggressive or mobile.programs or mobile.non_corporeal
        or mobile.fear_aura or mobile.costs_fame
        or mobile_vnum in world.shopkeepers
        or set(world.mobile_specials.get(mobile_vnum, ())) != {"spec_guard"}
        or not mobile.damage_modifier_known or mobile.damage_modifier != 0
    ):
        return False
    resets = [r for r in world.mob_resets if r.mobile_vnum == mobile_vnum]
    if len(resets) != 1 or resets[0].room_vnum != room_vnum or resets[0].maximum_count != 1:
        return False
    return all(
        (item := world.objects.get(vnum)) is not None and (
            item.item_type == ITEM_ARMOR and all(
                loc in {12, 13, 14, 17}
                or (loc in {1, 2, 3, 4, 5, 18, 19} and mod <= 0)
                for loc, mod in item.affects
            )
            or (
                item.item_type == _ITEM_TRASH and item.wear_flags & ~1
                and not any(item.values) and bool(item.affects)
                and all(loc in {1, 2, 3, 4, 5, 18, 19} and mod <= 0
                        for loc, mod in item.affects)
            )
        )
        for vnum in (*resets[0].object_vnums, *(v for _, v in resets[0].equipment))
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


def source_mobile_has_sanctuary(mobile: MobileSource | None) -> bool:
    """Return whether source flags show DD4's victim-side sanctuary effect."""
    return bool(
        mobile is not None
        and int(getattr(mobile, "affected_flags", 0) or 0) & AFF_SANCTUARY
    )


def unarmed_inert_instrument_reset(
    world: WorldSource | None,
    *,
    mobile_vnum: int,
    room_vnum: int,
) -> bool:
    """Audit a singleton reset holding only an inert, source-defined instrument.

    DD4's ``db.c`` leaves ITEM_INSTRUMENT values unchanged during object
    randomisation. This permits only a takeable/holdable, zero-value,
    zero-affect instrument with no flag beyond HUM; it never admits weapons,
    consumables, hidden affects, or carried extras.
    """
    if world is None:
        return False
    resets = [
        reset for reset in world.mob_resets
        if reset.mobile_vnum == mobile_vnum
    ]
    if (
        len(resets) != 1
        or resets[0].room_vnum != room_vnum
        or resets[0].maximum_count != 1
        or len(resets[0].equipment) != 1
        or resets[0].equipment[0][0] != _WEAR_HOLD
        or tuple(dict.fromkeys(resets[0].object_vnums))
        != (resets[0].equipment[0][1],)
    ):
        return False
    item = world.objects.get(resets[0].equipment[0][1])
    return bool(
        item is not None
        and item.item_type == ITEM_INSTRUMENT
        and item.values
        and all(type(value) is int and value == 0 for value in item.values)
        and not item.affects
        and item.extra_flags == _ITEM_HUM
        and item.wear_flags == (_ITEM_TAKE | _ITEM_HOLD)
    )


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
    candidate: HuntCandidate,
    world: WorldSource | None,
    *,
    allow_aggressive: bool = False,
    allow_specials: Collection[str] = (),
    allow_dual_wield: bool = False,
    allow_warrior_special_variance: bool = False,
) -> SingleWeaponLoadout | None:
    """Audit a singleton prototype; movement never grants combat permission.

    ``allow_dual_wield`` is reserved for a source-audited combat special whose
    reset explicitly equips one wielded and one dual-wield weapon. Ordinary
    armed-target checks remain single-weapon checks. The variance option is
    narrower still: it permits only the exact ``spec_warrior`` reset to retain
    source-randomised weapon prototypes and a source ``boss`` rank. It does
    not relax armor, object-type, identity, or special-procedure checks.
    """
    if world is None:
        return None
    candidate_specials = frozenset(candidate.specials)
    source_specials = frozenset(
        world.mobile_specials.get(candidate.mobile_vnum, ())
    )
    requested_specials = frozenset(
        str(special).casefold().strip() for special in allow_specials
    )
    warrior_profile = source_special_profile("spec_warrior")
    audited_grok_special = bool(
        requested_specials == {"spec_warrior"}
        and candidate.mobile_vnum == 9510
        and candidate.room_vnum == 9523
        and candidate.area_file == "vamp_catacombs.are"
        and candidate_specials == source_specials == {"spec_warrior"}
        and candidate.autonomy_rejections == (
            "target has special procedure spec_warrior",
        )
        and warrior_profile.xp_bonus == 10
        and warrior_profile.risk == "moderate-combat"
        and not warrior_profile.status_effects
    )
    warrior_special_rejections = {
        "target has special procedure spec_warrior",
        "below-band transit aggressor is not an XP target",
        "below-band wandering aggressor is not an XP target",
    }
    audited_warrior_special = bool(
        requested_specials == {"spec_warrior"}
        and candidate_specials == source_specials == {"spec_warrior"}
        and "target has special procedure spec_warrior"
        in set(candidate.autonomy_rejections)
        and set(candidate.autonomy_rejections) <= warrior_special_rejections
        and warrior_profile.xp_bonus == 10
        and warrior_profile.risk == "moderate-combat"
        and not warrior_profile.status_effects
    )
    audited_dual_wield = bool(allow_dual_wield and audited_warrior_special)
    audited_warrior_variance = bool(
        allow_warrior_special_variance and audited_dual_wield
    )
    if (
        not (
            candidate.autonomous_safe
            or audited_grok_special
            or audited_warrior_special
        )
        or not candidate.equipped_weapons
        or (
            len(candidate.equipped_weapons) != 1
            and not audited_dual_wield
        )
        or candidate.source_spawn_limit != 1 or candidate.room_spawn_count != 1
        or candidate_specials != source_specials
        or not (
            source_specials <= SAFE_NONCOMBAT_SPECIALS
            or audited_grok_special
            or audited_warrior_special
        )
    ):
        return None
    mobile = world.mobiles.get(candidate.mobile_vnum)
    resets = [r for r in world.mob_resets if r.mobile_vnum == candidate.mobile_vnum]
    if (
        mobile is None or (mobile.aggressive and not allow_aggressive)
        or mobile.fear_aura or mobile.confused
        or mobile.programs
        or not mobile.damage_modifier_known or mobile.damage_modifier is None
        or candidate.level != mobile.level
        or candidate.source_damage_modifier != mobile.damage_modifier
        or mobile.rank.casefold()
        not in (
            {"common", "none", "boss"}
            if audited_warrior_variance
            else {"common", "none"}
        )
        or mobile.affected_flags & (_AFF_BATTLE_AURA | _AFF_GLOBE)
        or len(resets) != 1 or resets[0].room_vnum != candidate.room_vnum
        or resets[0].maximum_count != 1
    ):
        return None
    reset = resets[0]
    slots = [slot for slot, _vnum in reset.equipment]
    if (
        len(slots) != len(set(slots)) or slots.count(16) != 1
        or (18 in slots and not audited_dual_wield)
        or any(type(slot) is not int or not 0 <= slot <= 20 for slot in slots)
    ):
        return None
    weapon_slots = tuple(
        (slot, vnum)
        for slot, vnum in reset.equipment
        if slot in {16, 18}
    )
    if audited_dual_wield and any(
        (item := world.objects.get(vnum)) is None or item.item_type != ITEM_WEAPON
        for _slot, vnum in weapon_slots
    ):
        return None
    weapon_vnum = next(vnum for slot, vnum in reset.equipment if slot == 16)
    weapon = world.objects.get(weapon_vnum)
    if (
        # NPC one_hit() uses any ITEM_WEAPON in WEAR_WIELD as its ordinary
        # melee weapon. ITEM_BOW only changes player use through do_shoot().
        weapon is None or weapon.item_type != ITEM_WEAPON
        or weapon.extra_flags & (1 << 14)
        or normalize_item_name(weapon.short_description)
        != normalize_item_name(candidate.equipped_weapons[0])
    ):
        return None
    if audited_dual_wield:
        source_weapon_names = tuple(
            normalize_item_name(world.objects[vnum].short_description)
            for _slot, vnum in weapon_slots
        )
        candidate_weapon_names = tuple(
            normalize_item_name(name)
            for name in candidate.equipped_weapons
        )
        if source_weapon_names != candidate_weapon_names:
            return None
    allowed_weapon_vnums = {vnum for _slot, vnum in weapon_slots}
    equipped_vnums = {vnum for _slot, vnum in reset.equipment}
    for vnum in set(reset.object_vnums) | equipped_vnums:
        item = world.objects.get(vnum)
        if item is None:
            return None
        # Carried objects do not change the NPC's fight.c one_hit() output.
        # Scavenging only transfers loose room objects to inventory; it does
        # not equip them. Reject combat items only when they are worn/held.
        if vnum in equipped_vnums and (
            item.item_type in {ITEM_PILL, ITEM_POTION, ITEM_SCROLL, ITEM_STAFF, ITEM_WAND}
            or item.item_type == ITEM_WEAPON and vnum not in allowed_weapon_vnums
        ):
            return None
    damage_bonus = hitpoint_bonus = 0
    # NPC base stats stay 13; ordinary saves, AC and hitroll add no damage.
    passive_affects = {0, 1, 2, 3, 4, 5, 12, 14, 17, 18, 20, 21, 22, 23, 24}
    for _slot, vnum in reset.equipment:
        item = world.objects[vnum]
        fixed = bool(item.extra_flags & ITEM_DONOT_RANDOMISE)
        randomized_warrior_equipment = bool(
            audited_warrior_variance
            and not fixed
        )
        # db.c uses prototype level - 2 for reset gear. Fickle items can use
        # the strong randomiser even at low levels, introducing new affects.
        weak = bool(item.extra_flags & (1 << 38)) or mobile.level - 2 < 40
        if (
            not fixed
            and not randomized_warrior_equipment
            and (item.extra_flags & (1 << 39) or not weak)
        ):
            return None
        if randomized_warrior_equipment:
            # db.c randomizes this reset's non-fixed equipment. Keep source
            # identity, slot, type, and castable-item checks above, but do not
            # treat incidental prototype affects as stable combat estimates.
            continue
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
        target_sanctuary=source_mobile_has_sanctuary(mobile),
    )
