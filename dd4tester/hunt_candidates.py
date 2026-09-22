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
from .combat_capabilities import (
    combat_capabilities_for,
)
from .specials import (
    COMBAT_JOINING_SPECIALS,
    SAFE_NONCOMBAT_SPECIALS,
    TRANSIT_SAFE_COMBAT_ONLY_SPECIALS,
    source_special_is_transit_safe,
    source_special_profile,
)


ACT_SENTINEL = 1 << 1
ACT_AGGRESSIVE = 1 << 5
ACT_STAY_AREA = 1 << 6
ACT_WIZINVIS_MOB = 1 << 16
ACT_IS_FAMOUS = 1 << 14
ACT_LOSE_FAME = 1 << 15
ACT_DIE_IF_MASTER_GONE = 1 << 21
ACT_NO_EXPERIENCE = 1 << 24
ACT_NO_FIGHT = 1 << 26
ACT_UNDEAD = 1 << 30

# ``rank_table`` in ``server/src/mob.c`` is applied by ``create_mobile``
# after the ordinary area-file hit-point roll.  Keep the source multiplier
# here so static target estimates match live elite/boss/world mobiles.
MOBILE_RANK_HP_MULTIPLIERS = {
    "none": 1,
    "common": 1,
    "uncommon": 1,
    "rare": 2,
    "elite": 5,
    "boss": 7,
    "world": 30,
}

# ``MobHPMod`` and ``MobDamMod`` are signed percentages applied after the
# level/rank calculation or attack calculation in DD4.  These limits mirror
# the source constants in ``merc.h``.
MOBILE_HP_MOD_MIN = -99
MOBILE_DAMAGE_MOD_MIN = -99
MOBILE_SPAWN_HP_LIMIT = ((1 << 31) - 1) // 100
MOBILE_ATTACK_DAMAGE_LIMIT = ((1 << 31) - 1) // 1000
MOBILE_TEMPLATE_UNSET = -(1 << 31)
MOBILE_SPECIAL_SLOTS = 3
MOBILE_SPECIAL_AUTO = -1

# These values mirror DD4's ``body_form`` bits in ``merc.h``.  Keep the raw
# value on source records so anatomy-sensitive actions can make an explicit
# decision instead of inferring from a mobile's display name.
BODY_NO_HEAD = 1 << 0
BODY_NO_EYES = 1 << 1
BODY_NO_ARMS = 1 << 2
BODY_NO_LEGS = 1 << 3
BODY_NO_HEART = 1 << 4
BODY_HUGE = 1 << 7
BODY_INORGANIC = 1 << 8
PART_HEAD = 1 << 10
PART_MANY_HEAD = 1 << 11
PART_ARMS = 1 << 12
PART_MANY_ARMS = 1 << 13
PART_2_LEGS = 1 << 15
PART_4_LEGS = 1 << 16
PART_MANY_LEGS = 1 << 17
PART_EYE = 1 << 25


def body_form_is_huge(flags: int | None) -> bool | None:
    """Return source ``IS_HUGE`` evidence, preserving an unknown value."""
    return None if flags is None else bool(flags & BODY_HUGE)


def body_form_is_inorganic(flags: int | None) -> bool | None:
    """Return source ``IS_INORGANIC`` evidence, preserving an unknown value."""
    return None if flags is None else bool(flags & BODY_INORGANIC)


def body_form_has_arms(flags: int | None) -> bool | None:
    """Mirror DD4's ``HAS_ARMS`` macro for an optional source body form."""
    if flags is None:
        return None
    return not bool(flags & BODY_NO_ARMS) or bool(
        flags & (PART_ARMS | PART_MANY_ARMS)
    )


def body_form_has_legs(flags: int | None) -> bool | None:
    """Mirror DD4's ``HAS_LEGS`` macro for an optional source body form."""
    if flags is None:
        return None
    return not bool(flags & BODY_NO_LEGS) or bool(
        flags & (PART_2_LEGS | PART_4_LEGS | PART_MANY_LEGS)
    )


def body_form_has_eyes(flags: int | None) -> bool | None:
    """Mirror DD4's ``HAS_EYES`` macro for an optional source body form."""
    if flags is None:
        return None
    return not bool(flags & BODY_NO_EYES) or bool(flags & PART_EYE)


def body_form_has_head(flags: int | None) -> bool | None:
    """Mirror DD4's ``HAS_HEAD`` macro for an optional source body form."""
    if flags is None:
        return None
    return not bool(flags & BODY_NO_HEAD) or bool(
        flags & (PART_HEAD | PART_MANY_HEAD)
    )


AFF_BLIND = 1 << 0
AFF_DETECT_INVIS = 1 << 3
AFF_DETECT_MAGIC = 1 << 4
AFF_NON_CORPOREAL = 1 << 28
AFF_MINDLESS = 1 << 49

ROOM_NO_MOB = 1 << 2
ROOM_NO_RECALL = 1 << 13
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
ITEM_PILL = 26
ITEM_CONTAINER = 15
ITEM_FOOD = 19
ITEM_MONEY = 20
ITEM_LOCK_PICK = 35

# Container flags from ``merc.h``.  A nested resource is not loose ground
# loot: a closed or locked container needs an explicit extraction plan.
CONT_CLOSEABLE = 1
CONT_PICKPROOF = 2
CONT_CLOSED = 4
CONT_LOCKED = 8

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
# DD4's area format stores a door *type* in the second field of a ``D``
# record. ``db.c`` expands that type into exit flags; it is not a bitmask.
_SOURCE_EXIT_FLAGS_BY_LOCK_TYPE = {
    1: 1,    # EX_ISDOOR
    2: 33,   # EX_ISDOOR | EX_PICKPROOF
    3: 17,   # EX_ISDOOR | EX_BASHPROOF
    4: 49,   # EX_ISDOOR | EX_PICKPROOF | EX_BASHPROOF
    5: 65,   # EX_ISDOOR | EX_PASSPROOF
    6: 97,   # EX_ISDOOR | EX_PICKPROOF | EX_PASSPROOF
    7: 81,   # EX_ISDOOR | EX_BASHPROOF | EX_PASSPROOF
    8: 113,  # EX_ISDOOR | EX_PICKPROOF | EX_BASHPROOF | EX_PASSPROOF
    9: EX_WALL,
    10: 257,  # EX_ISDOOR | EX_SECRET
    11: 369,  # EX_ISDOOR | EX_PICKPROOF | EX_BASHPROOF | EX_PASSPROOF | EX_SECRET
    12: 256,  # EX_SECRET
}


def _source_exit_flags_for_lock_type(lock_type: int) -> int:
    """Mirror ``db.c``'s ``locks`` switch for an area ``D`` record."""
    return _SOURCE_EXIT_FLAGS_BY_LOCK_TYPE.get(int(lock_type), 0)


_TILDE_VALUE = re.compile(r"(-?\d+)")
_MOBILE_TEACHING = re.compile(
    r"^\s*&\s*(?P<percent>\d+)\s+'(?P<skill>[^']+)'\s*$",
    re.IGNORECASE,
)
_MOBILE_TEMPLATE = re.compile(
    r"^\s*<\s*(?P<template>[^~]*)~\s*(?P<rank>[^~]*)~\s*$",
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

# The ordinary XP cutoff is five levels, but a source-aggressive mobile that
# can still be close enough to interrupt travel needs a wider route-only gate.
# It remains eligible as an incidental kill when it is farther below this band;
# this does not change target selection or the live consider rule.
_SOURCE_TRANSIT_AGGRESSOR_RISK_GAP = 10
# A source-identified, unarmed aggressor below the useful XP band may still
# interrupt travel.  Admit it only when one live exchange and one critical
# hit remain well inside the character's current HP reserve; the live runner
# still requires exact identity, isolation, and a bounded return.
_SOURCE_BOUNDED_TRANSIT_PEAK_RATIO = 0.40
_SOURCE_BOUNDED_TRANSIT_CRITICAL_RATIO = 0.20
# A probabilistic greet-program attacker may be treated as bounded route noise
# only when both its trigger and source combat envelope are tightly capped.
_SOURCE_BOUNDED_PROGRAM_MAX_TRIGGER_PERCENT = 25
_SOURCE_BOUNDED_PROGRAM_LEVEL_GAP = 4
_SOURCE_BOUNDED_PROGRAM_MAX_CAPACITY = 3
# A low-level probabilistic greet program can be checked from recall before
# the route is crossed. Keep this separate from the ordinary transit-risk
# band: the starter has a bounded ``where`` preflight for exactly this case.
_SOURCE_PROGRAM_PREFLIGHT_LEVEL_GAP = 2

# A modest detour is worthwhile when it removes a source-proven crowd from a
# route. Keep route planning from replacing a short, unusable path with an
# effectively cross-world journey.
_MAX_SOURCE_ROUTE_DETOUR_STEPS = 20

# Passive and control capabilities remain separate because they affect the
# ordinary weapon cycle or target safety rather than being direct actions.
_SOURCE_PASSIVE_COMBAT_SKILLS = (
    "second attack",
    "third attack",
    "enhanced damage",
    "enhanced hit",
    "second punch",
    "counterbalance",
)
_SOURCE_CONTROL_COMBAT_SKILLS = (
    "disarm",
    "grip",
    "stun",
    "smash",
    "kansetsu",
    "dirt kick",
    "trip",
)
_SOURCE_DEFENSIVE_COMBAT_SKILLS = (
    "armor",
    "sanctuary",
    "mental barrier",
    "displacement",
    "shield block",
    "dodge",
    "parry",
    "fast healing",
    "weaponchain",
    "summon familiar",
)


@dataclass(frozen=True)
class SourceCombatOutput:
    """One source-backed, repeatable damage action for a player class.

    ``expected_damage`` is the source formula's integer planning average.
    ``conservative_damage`` applies a fixed 80% planning haircut; it is not a
    proof of a kill and must be followed by the live damage-window probe.
    """

    action: str
    minimum_damage: int
    expected_damage: int
    maximum_damage: int
    resource: str
    resource_cost: int
    conservative_damage: int
    maximum_actions: int = 12
    source_reference: str = ""
    opening_action: str | None = None
    opening_min_damage: int | None = None
    opening_expected_damage: int | None = None
    opening_max_damage: int | None = None
    opening_conservative_damage: int | None = None
    opening_source_reference: str | None = None


_SOURCE_PIERCING_WEAPON_DAMAGE_TYPES = frozenset({2, 11})


def _source_known_skill_set(
    known_skills: Collection[str],
    known_skill_levels: Mapping[str, int] | None,
) -> frozenset[str]:
    raw_skills = (
        (known_skills,)
        if isinstance(known_skills, str)
        else (known_skills or ())
    )
    skills = {
        _normalize_skill_name(skill)
        for skill in raw_skills
        if str(skill).strip()
    }
    if not isinstance(known_skill_levels, Mapping):
        return frozenset(skills)
    # A level map is supplemental evidence. It may contain mixed-case keys,
    # but it must not turn an unobserved skill into a usable capability.
    for skill in tuple(skills):
        raw_percent = known_skill_levels.get(skill)
        if raw_percent is None:
            raw_percent = next(
                (
                    value
                    for raw_skill, value in known_skill_levels.items()
                    if _normalize_skill_name(raw_skill) == skill
                ),
                None,
            )
        try:
            if raw_percent is not None and int(raw_percent) <= 0:
                skills.discard(skill)
        except (TypeError, ValueError):
            continue
    return frozenset(skills)


def _source_skill_percent(
    skill: str,
    known_skills: frozenset[str],
    known_skill_levels: Mapping[str, int] | None,
) -> int:
    """Return a positive observed percentage without inventing a capability."""
    if skill not in known_skills or not isinstance(known_skill_levels, Mapping):
        return 0
    raw_percent = known_skill_levels.get(skill)
    if raw_percent is None:
        raw_percent = next(
            (
                value
                for raw_skill, value in known_skill_levels.items()
                if _normalize_skill_name(raw_skill) == skill
            ),
            None,
        )
    try:
        return max(0, min(100, int(raw_percent)))
    except (TypeError, ValueError):
        return 0


def _source_knife_toss_face_hit_percent(
    skill_percent: int,
    target_body_form_flags: int | None,
) -> int:
    """Return DD4's proven knife-toss face-hit probability in percent."""
    if body_form_has_eyes(target_body_form_flags) is not True:
        return 0
    # ``do_knife_toss`` succeeds when ``chance < learned`` and doubles the
    # damage when that same roll is ``<= 10``. ``number_percent`` rolls 1..100.
    return min(10, max(0, int(skill_percent) - 1))


def _source_c_trunc_divide(numerator: int, denominator: int) -> int:
    """Mirror C integer division for the small signed damage values here."""
    if numerator < 0:
        return -((-numerator) // denominator)
    return numerator // denominator


def _source_weapon_damage_value(
    base_damage: int,
    *,
    damroll: int,
    enhanced_damage: int,
    enhanced_hit: int,
) -> int:
    """Apply the player portion of DD4's ``one_hit`` weapon formula."""
    damage = base_damage + damroll
    if enhanced_damage > 0:
        damage += _source_c_trunc_divide(
            damage * enhanced_damage,
            200,
        )
    if enhanced_hit > 0:
        damage += _source_c_trunc_divide(
            damage * enhanced_hit,
            400,
        )
    return max(1, damage)


def _source_weapon_expected_attacks(
    *,
    skills: frozenset[str],
    known_skill_levels: Mapping[str, int] | None,
    swiftness: int | None,
    dex_swiftness: int,
    counterbalance_percent: int | None = None,
) -> tuple[float, int]:
    """Return expected and maximum ``multi_hit`` attacks for one round.

    DD4 returns from ``multi_hit`` when a player misses the second or third
    attack, so the later attack probabilities are conditional rather than
    additive.  Swiftness is an independent extra hit before that chain.
    """
    probability_second = 0.0
    probability_third = 0.0
    probability_fourth = 0.0
    for skill, base_chance in (
        ("second attack", 45),
        ("third attack", 35),
        ("fourth attack", 25),
    ):
        percent = _source_skill_percent(
            skill,
            skills,
            known_skill_levels,
        )
        if percent <= 0:
            continue
        chance = max(0.0, min(100.0, base_chance + percent / 2.0))
        if skill == "second attack":
            probability_second = chance / 100.0
        elif skill == "third attack":
            probability_third = chance / 100.0
        else:
            probability_fourth = chance / 100.0

    expected_attacks = (
        1.0
        + probability_second
        + probability_second * probability_third
        + probability_second * probability_third * probability_fourth
    )
    maximum_attacks = 1
    if probability_second:
        maximum_attacks += 1
    if probability_second and probability_third:
        maximum_attacks += 1
    if probability_second and probability_third and probability_fourth:
        maximum_attacks += 1

    if swiftness is not None:
        enhanced_swiftness = _source_skill_percent(
            "enhanced swiftness",
            skills,
            known_skill_levels,
        )
        swift_chance = max(
            0.0,
            min(
                100.0,
                float(swiftness)
                + float(dex_swiftness)
                + enhanced_swiftness / 4.0,
            ),
        )
        expected_attacks += swift_chance / 100.0
        if swift_chance:
            maximum_attacks += 1

    # ``do_counterbalance`` stores the learned percentage on the weapon as
    # APPLY_BALANCE. ``fight.c`` rolls a separate attack after the ordinary
    # cycle, so this passive is usable only when the caller has independently
    # verified the currently wielded object.
    if counterbalance_percent is not None:
        try:
            counterbalance_chance = max(
                0,
                min(99, int(counterbalance_percent) - 1),
            )
        except (TypeError, ValueError):
            counterbalance_chance = 0
        expected_attacks += counterbalance_chance / 100.0
        if counterbalance_chance:
            maximum_attacks += 1
    return expected_attacks, maximum_attacks


def _source_weapon_hit_values(
    weapon_damage_range: tuple[int, int] | None,
    *,
    skills: frozenset[str],
    known_skill_levels: Mapping[str, int] | None,
    damroll: int,
) -> tuple[int, ...]:
    """Return the observed weapon's post-bonus one-hit damage values."""
    if weapon_damage_range is None:
        return ()
    try:
        weapon_minimum, weapon_maximum = weapon_damage_range
        weapon_minimum = int(weapon_minimum)
        weapon_maximum = int(weapon_maximum)
        damroll = int(damroll)
    except (TypeError, ValueError):
        return ()
    if weapon_minimum <= 0 or weapon_maximum < weapon_minimum:
        return ()
    enhanced_damage = _source_skill_percent(
        "enhanced damage",
        skills,
        known_skill_levels,
    )
    enhanced_hit = _source_skill_percent(
        "enhanced hit",
        skills,
        known_skill_levels,
    )
    return tuple(
        _source_weapon_damage_value(
            base_damage,
            damroll=damroll,
            enhanced_damage=enhanced_damage,
            enhanced_hit=enhanced_hit,
        )
        for base_damage in range(weapon_minimum, weapon_maximum + 1)
    )


def _source_vampire_attack_values(
    hit_values: tuple[int, ...],
    *,
    player_rage: int | None,
    player_max_rage: int | None,
) -> tuple[int, ...]:
    """Apply DD4's source ``suck``/``lunge`` damage and rage branches."""
    attack_values = tuple(
        damage + damage // 2
        for damage in hit_values
    )
    if player_rage is None or player_max_rage is None or player_max_rage <= 0:
        return attack_values
    if player_rage > (player_max_rage * 3 // 4):
        return tuple(
            damage + damage // 10
            for damage in attack_values
        )
    if player_rage < (player_max_rage // 4):
        return tuple(
            max(1, damage - damage // 10)
            for damage in attack_values
        )
    return attack_values


def _observed_combat_stat(value: object) -> int | None:
    """Decode update.c's concealed-stat sentinel without altering raw evidence."""
    if isinstance(value, bool):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return None if number == 50000 else number


# This mirrors ``dex_app[].toswift`` in ``server/src/const.c``.  The live
# ``Char.Stats`` packet calls the permanent stat ``dex`` and the current,
# equipment-adjusted value ``dex_mod``; combat uses the latter via
# ``get_curr_dex``.
_SOURCE_DEX_SWIFTNESS = (
    -5, -4, -4, -3, -3, -2, -2, -1,
    -1, -1, -1, 0, 0, 0, 0, 0,
    0, 0, 1, 1, 2, 2, 2, 3,
    3, 3, 4, 4, 4, 5, 5, 6,
)


def _source_dex_swiftness(current_dex: object) -> int | None:
    """Return DD4's dexterity contribution to an extra attack roll."""
    dexterity = _observed_combat_stat(current_dex)
    if dexterity is None or not 0 <= dexterity < len(_SOURCE_DEX_SWIFTNESS):
        return None
    return _SOURCE_DEX_SWIFTNESS[dexterity]


def source_combat_output_estimate(
    *,
    character_level: int,
    character_class: str | None,
    character_subclass: str | None = None,
    known_skills: Collection[str] = (),
    known_skill_levels: Mapping[str, int] | None = None,
    weapon_damage_range: tuple[int, int] | None = None,
    weapon_vnum: int | None = None,
    weapon_damage_type: int | None = None,
    ranged_weapon_damage_range: tuple[int, int] | None = None,
    ranged_weapon_vnum: int | None = None,
    player_damroll: int = 0,
    player_swiftness: int | None = None,
    player_dex_swiftness: int = 0,
    player_rage: int | None = None,
    player_max_rage: int | None = None,
    weapon_counterbalanced: bool = False,
    weapon_chained: bool = False,
    target_body_form_flags: int | None = None,
) -> SourceCombatOutput | None:
    """Return the first executable source-backed damage action.

    This covers formulas audited in ``magic.c``, ``skill.c``, and the bounded
    werewolf natural attacks in ``sft.c``. It also models the source-backed
    between-round ``headbutt``, ``kick``, ``knife toss``, and ``circle`` actions
    when their observed skill percentage and weapon requirements are present.
    Headbutt is estimated only with parsed source body-form evidence proving a
    non-huge target has a head. When a
    current structured equipment snapshot supplies a source object damage
    range, it models the player half of ``fight.c``'s weapon and
    ``multi_hit`` formula. Hit chance, temporary affects, target armor, and
    target resistances remain live-probed rather than guessed. An unknown
    weapon keeps ordinary physical output unassessed.
    Counterbalance is included only when the caller has verified that the
    current wielded object carries DD4's ``APPLY_BALANCE`` affect, not from
    the learned skill alone; its source percentage adds a separate expected
    hit to the ordinary cycle.
    For a trained thief with a source-identified piercing weapon, the result
    also carries one optional backstab opening budget. DD4's ``multi_hit``
    automatically rolls ``double backstab`` after that opener; include that
    branch only from positive observed proficiency. For a trained ranger
    with a source-identified bow, it carries the one-shot ``do_shoot`` volley
    budget, including only observed second- and third-shot proficiencies. Both
    openings are weighted by live proficiency and are never recurring actions.
    For a source-verified vampire, ``suck`` uses the current weapon (or DD4's
    unarmed 1d4 fallback), applies the source drain multiplier, and weights
    the one-hit result by the observed skill percentage. Its rage adjustment
    is applied only when live rage and max-rage values are available.
    A source-verified vampire with a trained ``lunge`` also receives one
    bounded full-health-target opening budget. ``double lunge`` contributes
    only its observed second-opening probability; it is never treated as a
    recurring combat action.
    Subclass actions are enabled only for their source-legal subclass; a
    subclass skill must never make an unrelated base-class route look ready.
    Smithy ``hurl`` is included only when the current wielded weapon is
    independently observed to carry ``EGO_ITEM_CHAINED``. The learned skill
    alone is never treated as proof of that object property.
    DD4 conceals low-level damroll/swiftness with the sentinel 50000. Missing,
    concealed, or malformed values grant no damage bonus or swiftness credit;
    the raw observation remains available to the caller for audit.
    """
    player_damroll = _observed_combat_stat(player_damroll) or 0
    player_swiftness = _observed_combat_stat(player_swiftness)
    try:
        level = max(1, int(character_level))
    except (TypeError, ValueError):
        return None
    normalized_class = _normalize_skill_name(character_class or "")
    normalized_subclass = _normalize_skill_name(character_subclass or "")
    actions = tuple(
        capability.name
        for capability in combat_capabilities_for(
            normalized_class,
            normalized_subclass,
            estimated_only=True,
        )
    )
    if weapon_damage_range is not None:
        actions = (*actions, "weapon strike")
    skills = _source_known_skill_set(known_skills, known_skill_levels)
    if (
        normalized_class == "smithy"
        and weapon_chained
        and weapon_damage_range is not None
        and "hurl" in skills
    ):
        actions = ("hurl", *actions)
    counterbalance_percent = (
        _source_skill_percent(
            "counterbalance",
            skills,
            known_skill_levels,
        )
        if weapon_counterbalanced
        else None
    )
    opening_action: str | None = None
    opening_data: tuple[int, int, int, int, str] | None = None
    if normalized_class == "shifter" and normalized_subclass == "vampire":
        lunge_percent = _source_skill_percent(
            "lunge",
            skills,
            known_skill_levels,
        )
        lunge_hit_values = _source_weapon_hit_values(
            weapon_damage_range or (1, 4),
            skills=skills,
            known_skill_levels=known_skill_levels,
            damroll=player_damroll,
        )
        if lunge_percent > 0 and lunge_hit_values:
            lunge_values = _source_vampire_attack_values(
                lunge_hit_values,
                player_rage=player_rage,
                player_max_rage=player_max_rage,
            )
            double_lunge_percent = _source_skill_percent(
                "double lunge",
                skills,
                known_skill_levels,
            )
            successful_expected = (
                sum(lunge_values) / len(lunge_values)
            )
            expected = max(
                1,
                int(
                    successful_expected
                    * lunge_percent
                    / 100.0
                    * (1.0 + double_lunge_percent / 100.0)
                ),
            )
            opening_data = (
                min(lunge_values),
                expected,
                max(lunge_values) * (
                    2 if double_lunge_percent > 0 else 1
                ),
                max(1, expected * 4 // 5),
                "fight.c:do_lunge/multi_hit/one_hit",
            )
            if weapon_vnum is not None:
                opening_data = (
                    *opening_data[:-1],
                    f"fight.c:do_lunge/multi_hit/one_hit; object vnum "
                    f"{int(weapon_vnum)}",
                )
            opening_action = "lunge"
    if (
        normalized_class == "thief"
        and weapon_damage_type in _SOURCE_PIERCING_WEAPON_DAMAGE_TYPES
    ):
        backstab_percent = _source_skill_percent(
            "backstab",
            skills,
            known_skill_levels,
        )
        hit_values = _source_weapon_hit_values(
            weapon_damage_range,
            skills=skills,
            known_skill_levels=known_skill_levels,
            damroll=player_damroll,
        )
        if backstab_percent > 0 and hit_values:
            multiplier = 3 + level // 15
            successful_minimum = min(hit_values) * multiplier
            successful_maximum = max(hit_values) * multiplier
            successful_expected = (
                sum(hit_values) / len(hit_values) * multiplier
            )
            double_backstab_percent = _source_skill_percent(
                "double backstab",
                skills,
                known_skill_levels,
            )
            expected = max(
                1,
                int(
                    successful_expected
                    * backstab_percent
                    / 100.0
                    * (1.0 + double_backstab_percent / 100.0)
                ),
            )
            maximum = successful_maximum * (
                2 if double_backstab_percent > 0 else 1
            )
            reference = "fight.c:do_backstab/one_hit"
            if double_backstab_percent > 0:
                reference += "; plus fight.c:multi_hit/double_backstab"
            opening_data = (
                successful_minimum,
                expected,
                maximum,
                max(1, expected * 4 // 5),
                reference,
            )
            if weapon_vnum is not None:
                opening_data = (
                    *opening_data[:-1],
                    f"{reference}; object vnum {int(weapon_vnum)}",
                )
            opening_action = "backstab"
    if normalized_class == "ranger":
        shoot_percent = _source_skill_percent(
            "shoot",
            skills,
            known_skill_levels,
        )
        ranged_hit_values = _source_weapon_hit_values(
            ranged_weapon_damage_range,
            skills=skills,
            known_skill_levels=known_skill_levels,
            damroll=player_damroll,
        )
        if shoot_percent > 0 and ranged_hit_values:
            second_shot_percent = _source_skill_percent(
                "second shot",
                skills,
                known_skill_levels,
            )
            third_shot_percent = _source_skill_percent(
                "third shot",
                skills,
                known_skill_levels,
            )
            expected_shots = (
                1.0
                + second_shot_percent / 100.0
                + third_shot_percent / 100.0
            )
            maximum_shots = (
                1
                + int(second_shot_percent > 0)
                + int(third_shot_percent > 0)
            )
            successful_expected = (
                sum(ranged_hit_values) / len(ranged_hit_values)
                * expected_shots
            )
            expected = max(
                1,
                int(successful_expected * shoot_percent / 100.0),
            )
            opening_data = (
                min(ranged_hit_values),
                expected,
                max(ranged_hit_values) * maximum_shots,
                max(1, expected * 4 // 5),
                "fight.c:do_shoot/one_hit",
            )
            if ranged_weapon_vnum is not None:
                opening_data = (
                    *opening_data[:-1],
                    f"fight.c:do_shoot/one_hit; object vnum "
                    f"{int(ranged_weapon_vnum)}",
                )
            opening_action = "shoot"
    if not actions:
        return None
    for action in actions:
        if action != "weapon strike" and action not in skills:
            continue
        if action == "punch":
            # do_punch's primary damage is level/2 plus number_range(1,
            # level*2). The source then makes one independent second-punch
            # roll when the arm-trauma gate is clear. Include that automatic
            # side effect only when its positive live proficiency is known;
            # the command remains the same ``punch`` action.
            minimum = level // 2 + 1
            maximum = level // 2 + level * 2
            expected = level // 2 + (1 + level * 2) // 2
            reference = "skill.c:do_punch"
            resource_cost = 0
            second_punch_percent = _source_skill_percent(
                "second punch",
                skills,
                known_skill_levels,
            )
            if second_punch_percent > 0:
                second_minimum = level + level
                second_maximum = level + level * 2
                second_expected = (second_minimum + second_maximum) // 2
                expected += max(
                    1,
                    int(second_expected * second_punch_percent / 100.0),
                )
                maximum += second_maximum
                reference = (
                    "skill.c:do_punch; plus skill.c:do_punch/second_punch"
                )
        elif action == "headbutt":
            # do_headbutt requires a fighting target with a head and rejects
            # huge targets before its learned-percent damage roll. Unknown
            # anatomy is therefore not an executable output estimate.
            if (
                body_form_has_head(target_body_form_flags) is not True
                or body_form_is_huge(target_body_form_flags) is not False
            ):
                continue
            skill_percent = _source_skill_percent(
                "headbutt",
                skills,
                known_skill_levels,
            )
            if skill_percent <= 0:
                continue
            base = level // 2
            minimum = base + 1
            maximum = base + level * 3
            successful_expected = base + (1 + level * 3) // 2
            success_probability = skill_percent / 100.0
            second_headbutt_percent = _source_skill_percent(
                "second headbutt",
                skills,
                known_skill_levels,
            )
            second_maximum = base + level * 3
            second_expected = base + (10 + level * 3) // 2
            expected = max(
                1,
                int(
                    successful_expected * success_probability
                    + second_expected
                    * success_probability
                    * (second_headbutt_percent / 100.0)
                ),
            )
            if second_headbutt_percent > 0:
                maximum += second_maximum
                reference = (
                    "fight.c:do_headbutt/one_hit; plus "
                    "fight.c:do_headbutt/second_headbutt"
                )
            else:
                reference = "fight.c:do_headbutt/one_hit"
            resource_cost = 0
        elif action in {"kick", "knife toss"}:
            # Both commands use a level-scaled roll and a learned-percent
            # success gate.  Keep the successful source range visible while
            # weighting the planning average by the observed chance; a live
            # damage-window probe still decides whether the target is viable.
            skill_percent = _source_skill_percent(
                action,
                skills,
                known_skill_levels,
            )
            if skill_percent <= 0:
                continue
            base = level // 2
            minimum = base + 1
            maximum = base + level
            successful_expected = base + (level + 1) // 2
            face_hit_percent = (
                _source_knife_toss_face_hit_percent(
                    skill_percent,
                    target_body_form_flags,
                )
                if action == "knife toss"
                else 0
            )
            expected = max(
                1,
                int(
                    successful_expected
                    * (skill_percent + face_hit_percent)
                    / 100.0
                ),
            )
            reference = (
                "fight.c:do_kick"
                if action == "kick"
                else "fight.c:do_knife_toss"
            )
            if face_hit_percent > 0:
                maximum *= 2
                reference += "; plus fight.c:do_knife_toss/face_hit"
            resource_cost = 0
        elif action == "circle":
            if (
                weapon_damage_range is None
                or weapon_damage_type
                not in _SOURCE_PIERCING_WEAPON_DAMAGE_TYPES
            ):
                continue
            skill_percent = _source_skill_percent(
                "circle",
                skills,
                known_skill_levels,
            )
            if skill_percent <= 0:
                continue
            hit_values = _source_weapon_hit_values(
                weapon_damage_range,
                skills=skills,
                known_skill_levels=known_skill_levels,
                damroll=player_damroll,
            )
            if not hit_values:
                continue
            circle_values = tuple(
                damage + damage // 2 for damage in hit_values
            )
            second_circle_percent = _source_skill_percent(
                "second circle",
                skills,
                known_skill_levels,
            )
            success_probability = skill_percent / 100.0
            second_probability = second_circle_percent / 100.0
            successful_expected = sum(circle_values) / len(circle_values)
            expected = max(
                1,
                int(
                    successful_expected
                    * success_probability
                    * (1.0 + second_probability)
                ),
            )
            minimum = min(circle_values)
            maximum = max(circle_values) * (
                2 if second_circle_percent > 0 else 1
            )
            reference = "fight.c:do_circle/one_hit"
            if weapon_vnum is not None:
                reference += f"; object vnum {int(weapon_vnum)}"
            resource_cost = 0
        elif action == "suck":
            # ``do_suck`` performs one source ``one_hit`` and then adds half
            # of that damage. A vampire can use the same action unarmed; the
            # ordinary unarmed one_hit range is 1..4 for non-brawlers.
            suck_weapon_range = weapon_damage_range or (1, 4)
            hit_values = _source_weapon_hit_values(
                suck_weapon_range,
                skills=skills,
                known_skill_levels=known_skill_levels,
                damroll=player_damroll,
            )
            skill_percent = _source_skill_percent(
                "suck",
                skills,
                known_skill_levels,
            )
            if skill_percent <= 0 or not hit_values:
                continue
            suck_values = _source_vampire_attack_values(
                hit_values,
                player_rage=player_rage,
                player_max_rage=player_max_rage,
            )
            successful_expected = sum(suck_values) / len(suck_values)
            minimum = min(suck_values)
            maximum = max(suck_values)
            expected = max(
                1,
                int(successful_expected * skill_percent / 100.0),
            )
            reference = "skill.c:do_suck; fight.c:one_hit"
            resource_cost = 0
        elif action == "hurl":
            # A weapon hurl is a repeatable between-round action.  DD4 uses
            # level/2 + number_range(level, level*2) for a successful weapon
            # hurl, with the learned percentage as the success gate. The
            # caller has already proved the weapon is chained and wielded.
            skill_percent = _source_skill_percent(
                "hurl",
                skills,
                known_skill_levels,
            )
            if (
                not weapon_chained
                or weapon_damage_range is None
                or skill_percent <= 0
            ):
                continue
            minimum = level // 2 + level
            maximum = level // 2 + level * 2
            successful_expected = (minimum + maximum) // 2
            expected = max(
                1,
                int(successful_expected * skill_percent / 100.0),
            )
            reference = "fight.c:do_hurl/weapon"
            if weapon_vnum is not None:
                reference += f"; object vnum {int(weapon_vnum)}"
            resource_cost = 0
        elif action == "atemi":
            # The standalone do_atemi path resets combo state before calling
            # atemi(), whose source damage is a fixed level*1.5.
            minimum = maximum = expected = level * 3 // 2
            reference = "skill.c:do_atemi and atemi"
            resource_cost = 0
        elif action == "burning hands":
            dice_count = min(level, 30)
            minimum = (10 + dice_count) // 2
            maximum = 20 + dice_count * 3
            expected = 15 + (dice_count * 2)
            reference = "magic.c:spell_burning_hands"
            resource_cost = 15
        elif action == "shocking grasp":
            minimum = 10 + (2 * level)
            maximum = 20 + (2 * level)
            expected = 15 + (2 * level)
            reference = "magic.c:spell_shocking_grasp"
            resource_cost = 15
        elif action in {"lightning bolt", "colour spray"}:
            # Both spells use dice(level, 4) + level.  DD4's save or
            # resistance path halves the damage, so retain the halved raw
            # floor while keeping the source maximum visible.
            minimum = level
            maximum = 5 * level
            expected = (7 * level) // 2
            reference = (
                "magic.c:spell_lightning_bolt"
                if action == "lightning bolt"
                else "magic.c:spell_colour_spray"
            )
            resource_cost = 15
        elif action in {"fireball", "acid blast"}:
            # Fireball and acid blast are dice(level, 6/8).  Their source
            # save/resistance checks can halve the result; the conservative
            # floor models that branch without lowering the raw ceiling.
            sides = 6 if action == "fireball" else 8
            minimum = level // 2
            maximum = sides * level
            expected = ((sides + 1) * level) // 2
            reference = (
                "magic.c:spell_fireball"
                if action == "fireball"
                else "magic.c:spell_acid_blast"
            )
            resource_cost = 15 if action == "fireball" else 20
        elif action == "chill touch":
            minimum = 10 + level
            maximum = 20 + level
            expected = 15 + level
            reference = "magic.c:spell_chill_touch"
            resource_cost = 10
        elif action == "magic missile":
            missiles = min((level + 1) // 2, 10)
            minimum = 2 * missiles
            maximum = 5 * missiles
            expected = (7 * missiles) // 2
            reference = "magic.c:spell_magic_missile"
            resource_cost = 5
        elif action == "cause critical":
            minimum = 3 + level - 6
            maximum = 24 + level - 6
            expected = (3 * 9) // 2 + level - 6
            reference = "magic.c:spell_cause_critical"
            resource_cost = 20
        elif action == "cause serious":
            minimum = 2 + level // 2
            maximum = 16 + level // 2
            expected = 9 + level // 2
            reference = "magic.c:spell_cause_serious"
            resource_cost = 17
        elif action == "cause light":
            minimum = 1 + level // 3
            maximum = 8 + level // 3
            expected = 4 + level // 3
            reference = "magic.c:spell_cause_light"
            resource_cost = 15
        elif action == "psychic crush":
            minimum = 3 + level
            maximum = 15 + level
            expected = 9 + level
            reference = "magic.c:spell_psychic_crush"
            resource_cost = 15
        elif action == "mind thrust":
            minimum = 1 + level // 2
            maximum = 10 + level // 2
            expected = 5 + level // 2
            reference = "magic.c:spell_mind_thrust"
            resource_cost = 8
        elif action == "harm":
            minimum = 50
            maximum = 100
            expected = 75
            reference = "magic.c:spell_harm"
            resource_cost = 35
        elif action == "wither":
            minimum = 2 * level
            maximum = 9 * level
            expected = 11 * level // 2
            reference = "magic.c:spell_wither"
            resource_cost = 20
        elif action == "flamestrike":
            minimum = 3 * level
            maximum = 6 * level
            expected = 9 * level // 2
            reference = "magic.c:spell_flamestrike"
            resource_cost = 20
        elif action == "hellfire":
            # spell_hells_fire uses dice(level, 8) plus two damage per level.
            # Its source command is named ``hellfire`` in the skill table.
            minimum = 3 * level
            maximum = 10 * level
            expected = 13 * level // 2
            reference = "magic.c:spell_hells_fire"
            resource_cost = 20
        elif action == "agitation":
            damage_by_level = (
                0,
                0,
                0,
                3,
                6,
                9,
                12,
                15,
                18,
                21,
                24,
                24,
                24,
                25,
                25,
                26,
                26,
                26,
                27,
                27,
                27,
                28,
                28,
                28,
                29,
                29,
                29,
                30,
                30,
                30,
                31,
                31,
                31,
                32,
                32,
                32,
                33,
                33,
                33,
                34,
                34,
                34,
                35,
                35,
                35,
                36,
                36,
                36,
                37,
                37,
                37,
            )
            base = damage_by_level[min(level, len(damage_by_level) - 1)]
            minimum = base // 2
            maximum = base * 2
            expected = (minimum + maximum) // 2
            reference = "magic.c:spell_agitation"
            resource_cost = 10
        elif action == "wolfbite":
            # do_wolfbite uses number_range(level * 3, level * 5) after a
            # learned-percent hit roll. Keep the successful damage range as
            # the source bound; the live damage-window probe remains the
            # authority on whether this character can finish the target.
            minimum = 3 * level
            maximum = 5 * level
            expected = 4 * level
            reference = "sft.c:do_wolfbite"
            resource_cost = 0
        elif action == "ravage":
            # Ravage always attempts one hit, then repeats with the source
            # decrementing proficiency by seven points per extra hit, up to
            # eight hits. Model that bounded expectation without treating it
            # as live kill proof.
            minimum = 2 * level
            maximum = 24 * level
            try:
                proficiency = int(
                    next(
                        (
                            value
                            for raw_skill, value in (
                                known_skill_levels or {}
                            ).items()
                            if _normalize_skill_name(raw_skill) == action
                        ),
                        100,
                    )
                )
            except (TypeError, ValueError):
                proficiency = 100
            proficiency = max(0, min(100, proficiency))
            hit_probability = 1.0
            expected_hits = 1.0
            for extra_hit in range(1, 8):
                hit_probability *= max(
                    0.0,
                    min(100, proficiency - extra_hit * 7) / 100,
                )
                expected_hits += hit_probability
            expected = max(1, int(2.5 * level * expected_hits))
            reference = "sft.c:do_ravage"
            resource_cost = 0
        elif action == "weapon strike":
            try:
                dex_swiftness = int(player_dex_swiftness)
            except (TypeError, ValueError):
                continue
            hit_values = _source_weapon_hit_values(
                weapon_damage_range,
                skills=skills,
                known_skill_levels=known_skill_levels,
                damroll=player_damroll,
            )
            if not hit_values:
                continue
            expected_hit = sum(hit_values) / len(hit_values)
            expected_attacks, maximum_attacks = _source_weapon_expected_attacks(
                skills=skills,
                known_skill_levels=known_skill_levels,
                swiftness=player_swiftness,
                dex_swiftness=dex_swiftness,
                counterbalance_percent=counterbalance_percent,
            )
            minimum = min(hit_values)
            maximum = max(hit_values) * maximum_attacks
            expected = max(1, int(expected_hit * expected_attacks))
            reference = "fight.c:one_hit/multi_hit"
            if weapon_vnum is not None:
                reference += f"; object vnum {int(weapon_vnum)}"
            if counterbalance_percent is not None and counterbalance_percent > 1:
                reference += "; plus fight.c:counterbalance"
            resource_cost = 0
        else:
            continue
        if minimum <= 0 or maximum < minimum or expected <= 0:
            return None
        if action in {
            "headbutt",
            "kick",
            "knife toss",
            "circle",
            "suck",
            "hurl",
        }:
            # These commands are issued between automatic combat rounds. If a
            # source weapon is currently wielded, include one audited
            # ``multi_hit`` cycle in the same planning window instead of
            # pretending that the controller stops making normal attacks.
            automatic_hit_values = _source_weapon_hit_values(
                weapon_damage_range,
                skills=skills,
                known_skill_levels=known_skill_levels,
                damroll=player_damroll,
            )
            if automatic_hit_values:
                automatic_expected_attacks, automatic_maximum_attacks = (
                    _source_weapon_expected_attacks(
                        skills=skills,
                        known_skill_levels=known_skill_levels,
                        swiftness=player_swiftness,
                        dex_swiftness=player_dex_swiftness,
                        counterbalance_percent=counterbalance_percent,
                    )
                )
                automatic_expected = max(
                    1,
                    int(
                        sum(automatic_hit_values)
                        / len(automatic_hit_values)
                        * automatic_expected_attacks
                    ),
                )
                minimum = min(minimum, min(automatic_hit_values))
                maximum += (
                    max(automatic_hit_values) * automatic_maximum_attacks
                )
                expected += automatic_expected
                reference += "; plus fight.c:one_hit/multi_hit"
        return SourceCombatOutput(
            action=action,
            minimum_damage=minimum,
            expected_damage=expected,
            maximum_damage=maximum,
            resource=(
                "actions"
                if action in {
                    "circle",
                    "headbutt",
                    "kick",
                    "knife toss",
                    "suck",
                    "hurl",
                    "punch",
                    "atemi",
                    "wolfbite",
                    "ravage",
                    "weapon strike",
                }
                else "mana"
            ),
            resource_cost=resource_cost,
            conservative_damage=max(1, expected * 4 // 5),
            source_reference=reference,
            opening_action=opening_action if opening_data else None,
            opening_min_damage=opening_data[0] if opening_data else None,
            opening_expected_damage=opening_data[1] if opening_data else None,
            opening_max_damage=opening_data[2] if opening_data else None,
            opening_conservative_damage=(
                opening_data[3] if opening_data else None
            ),
            opening_source_reference=opening_data[4] if opening_data else None,
        )
    return None


@dataclass(frozen=True)
class MobileProgram:
    """One source mobile-program trigger and its executable commands."""

    trigger: str
    condition: str = ""
    commands: tuple[str, ...] = ()


@dataclass(frozen=True)
class MobileTemplateSource:
    """One resolved body-species/archetype layer from DD4's mob.c."""

    name: str
    species: str
    act_flags: int = 0
    affected_flags: int = 0
    body_form_flags: int = 0
    xp_modifier: int = 0
    hp_modifier: int = 0
    damage_modifier: int = 0
    # Resolved DD4 template special slots and their source probability policy.
    # A slot name is empty when the template explicitly clears it.
    special_names: tuple[str | None, ...] = (None, None, None)
    special_chances: tuple[int, ...] = (
        MOBILE_SPECIAL_AUTO,
        MOBILE_SPECIAL_AUTO,
        MOBILE_SPECIAL_AUTO,
    )

    @property
    def specials(self) -> tuple[str, ...]:
        return _effective_mobile_special_names(
            self.special_names,
            self.special_chances,
        )


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
    # ``None`` is reserved for malformed or legacy records with no body line;
    # a parsed ``0`` is real source evidence for an ordinary organic body.
    body_form_flags: int | None = None
    # DD4 stores this on the mobile prototype and multiplies max_hit when the
    # live instance is created.  Missing legacy records are ordinary/common.
    rank: str = "common"
    # Preserve DD4's source layering.  The public flag fields remain the
    # effective values used by candidate safety decisions.
    template_name: str | None = None
    template_species: str | None = None
    template_act_flags: int = 0
    template_affected_flags: int = 0
    template_body_form_flags: int = 0
    xp_modifier: int = 0
    area_act_flags: int | None = None
    area_affected_flags: int | None = None
    area_body_form_flags: int | None = None
    # Source scalar layers used by ``create_mobile``.  ``None`` means the
    # area record omitted ``MobHPMod`` or explicitly requested inheritance.
    template_hp_modifier: int = 0
    area_hp_modifier: int | None = None
    hp_modifier: int | None = 0
    hp_modifier_known: bool = True
    # DD4 applies this percentage to each positive attack routed through
    # ``one_hit``.  ``None`` means a referenced source template was not
    # resolved and therefore cannot authorize a safety estimate.
    template_damage_modifier: int = 0
    area_damage_modifier: int | None = None
    damage_modifier: int | None = 0
    damage_modifier_known: bool = True

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
    def undead(self) -> bool:
        """Return DD4's source-level undead marker for this mobile."""
        return bool(self.act_flags & ACT_UNDEAD)

    @property
    def rank_hp_multiplier(self) -> int:
        """Return DD4's source ``rank_table`` hit-point multiplier."""
        return MOBILE_RANK_HP_MULTIPLIERS.get(self.rank.casefold(), 1)

    @property
    def confused(self) -> bool:
        return bool(self.affected_flags & AFF_CONFUSION)

    @property
    def mindless(self) -> bool:
        """Mirror DD4's explicit ``AFF_MINDLESS`` trait."""
        return bool(self.affected_flags & AFF_MINDLESS)

    @property
    def non_corporeal(self) -> bool:
        """Return whether DD4's source prototype cannot be attacked."""
        return bool(self.affected_flags & AFF_NON_CORPOREAL)

    @property
    def huge(self) -> bool | None:
        """Return DD4's source-level ``IS_HUGE`` result."""
        return body_form_is_huge(self.body_form_flags)

    @property
    def inorganic(self) -> bool | None:
        """Return DD4's source-level ``IS_INORGANIC`` result."""
        return body_form_is_inorganic(self.body_form_flags)

    @property
    def has_arms(self) -> bool | None:
        """Mirror DD4's ``HAS_ARMS`` macro for source mobile prototypes."""
        return body_form_has_arms(self.body_form_flags)

    @property
    def has_head(self) -> bool | None:
        """Mirror DD4's ``HAS_HEAD`` macro for source mobile prototypes."""
        return body_form_has_head(self.body_form_flags)

    @property
    def has_eyes(self) -> bool | None:
        """Mirror DD4's ``HAS_EYES`` macro for source mobile prototypes."""
        return body_form_has_eyes(self.body_form_flags)

    @property
    def has_legs(self) -> bool | None:
        """Mirror DD4's ``HAS_LEGS`` macro for source mobile prototypes."""
        return body_form_has_legs(self.body_form_flags)

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


def _source_mobile_has_deterministic_attack_program(
    mobile: MobileSource,
) -> bool:
    """Return whether a source attack program fires on every trigger."""
    for program in mobile.attack_programs:
        condition = str(program.condition).strip()
        if not condition:
            return True
        try:
            if int(condition) >= 100:
                return True
        except (TypeError, ValueError):
            # An unparseable condition is not safe to treat as probabilistic.
            return True
    return False


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
    # DD4 applies these area-wide access values in ``act_move.c`` before a
    # player enters the destination room. Synthetic fixtures leave them unset
    # so they retain the older unrestricted route semantics.
    area_low_level: int | None = None
    area_high_level: int | None = None
    area_low_enforced: int | None = None
    area_high_enforced: int | None = None

    @property
    def no_mob(self) -> bool:
        return bool(self.room_flags & ROOM_NO_MOB)

    @property
    def no_recall(self) -> bool:
        return bool(self.room_flags & ROOM_NO_RECALL)


@dataclass(frozen=True)
class MobReset:
    mobile_vnum: int
    room_vnum: int
    maximum_count: int
    object_vnums: tuple[int, ...]
    equipment: tuple[tuple[int, int], ...] = ()


def _reset_object_vnums(reset: MobReset) -> tuple[int, ...]:
    """Return every object loaded by a mobile reset, including equipment."""
    return tuple(
        dict.fromkeys(
            (
                *reset.object_vnums,
                *(object_vnum for _wear_location, object_vnum in reset.equipment),
            )
        )
    )


def _source_key_carrier_resets(
    world: WorldSource,
    key_object_vnums: Collection[int],
    *,
    mobile_vnums: Collection[int] = (),
    room_vnums: Collection[int] = (),
) -> tuple[MobReset, ...]:
    """Return raw reset entries that actually load one of the given keys.

    Keep this query on the unaggregated reset stream.  DD4 applies each ``M``
    reset separately, so merging two same-mobile/same-room entries can make a
    key appear on every instance even when only the first reset's ``G``
    command loads it.
    """
    keys = {int(vnum) for vnum in key_object_vnums}
    mobiles = {int(vnum) for vnum in mobile_vnums}
    rooms = {int(vnum) for vnum in room_vnums}
    if not keys:
        return ()
    return tuple(
        reset
        for reset in world.mob_resets
        if (not mobiles or reset.mobile_vnum in mobiles)
        and (not rooms or reset.room_vnum in rooms)
        and keys.intersection(_reset_object_vnums(reset))
    )


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
    mobile_templates: dict[str, MobileTemplateSource] = field(default_factory=dict)
    skill_groups: dict[str, tuple[tuple[str, int], ...]] = field(default_factory=dict)


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
    rank: str = "common"
    equipped_weapons: tuple[str, ...] = ()
    # ``None`` means a legacy or synthetic candidate has no body-form proof;
    # parsed source candidates preserve a real zero-valued body form.
    target_body_form_flags: int | None = None
    estimated_level_range: tuple[int, int] = (0, 0)
    estimated_base_hp_range: tuple[int, int] = (0, 0)
    estimated_peak_round_damage: int = 0
    estimated_min_peak_round_damage: int = 0
    estimated_critical_hit_damage: int = 0
    autonomy_rejections: tuple[str, ...] = ()
    combat_readiness: str = "unassessed"
    combat_readiness_bonus: int = 0
    specials: tuple[str, ...] = ()
    route_preflight_room_vnum: str | None = None
    route_preflight_command: str | None = None
    route_preflight_target: str | None = None
    route_preflight_level_range: tuple[int, int] = (0, 0)
    route_preflight_hard_hazard: bool = False
    route_preflight_route_room_names: tuple[str, ...] = ()
    route_hard_hazard_targets: tuple[str, ...] = ()
    # Exact source identities for mobiles that can interrupt the route.  Keep
    # these separate from display-only hazard text so policy gates can reason
    # about aggressive NPCs even when their source has no special procedure.
    route_hazard_mobile_vnums: tuple[int, ...] = ()
    route_aggressive_mobile_vnums: tuple[int, ...] = ()
    route_attack_program_mobile_vnums: tuple[int, ...] = ()
    route_special_mobile_vnums: tuple[int, ...] = ()
    sentinel: bool = False
    stay_area: bool = False
    estimated_move_cost: int = 0
    estimated_flying_move_cost: int = 0
    requires_flight: bool = False
    ground_loot_keywords: tuple[str, ...] = ()
    ground_loot_object_vnums: tuple[int, ...] = ()
    is_coin_stash: bool = False
    is_food_stash: bool = False
    route_origin_recall_index: int = 0
    route_origin_room_vnum: int = RECALL_VNUM
    undead: bool = False
    source_damage_modifier: int | None = 0

    @property
    def autonomous_safe(self) -> bool:
        """Whether source evidence permits a live probe-to-hunt policy."""
        return not self.autonomy_rejections


@dataclass(frozen=True)
class ResourcePlacement:
    """One source-backed location where a recovery resource can appear."""

    effect: str
    object_vnum: int
    object_keywords: str
    object_description: str
    item_type: int
    source_kind: str
    source_mobile_vnum: int | None
    source_mobile: str
    room_vnum: int
    room_name: str
    area_file: str
    maximum_count: int
    source_level_range: tuple[int, int]
    status: str
    route: tuple[str, ...] = ()
    route_origin_recall_index: int = 0
    hazards: tuple[str, ...] = ()
    autonomy_rejections: tuple[str, ...] = ()
    activation: "ResourceActivation | None" = None
    # A resource may be reset inside one or more source containers rather than
    # directly on a mobile or room. Keep the chain explicit so a runner can
    # prove the acquisition commands instead of treating nested contents as
    # loose ground loot.
    container_object_vnums: tuple[int, ...] = ()
    required_key_object_vnums: tuple[int, ...] = ()
    required_key_source_mobile_vnums: tuple[int, ...] = ()
    # A source placement can be visible but unreachable from recall because a
    # route door is locked. Keep that route separate from ``route``: it is
    # diagnostic evidence only and must never be dispatched as a live plan.
    source_analysis_route: tuple[str, ...] = ()
    route_key_object_vnums: tuple[int, ...] = ()
    route_key_source_mobile_vnums: tuple[int, ...] = ()


@dataclass(frozen=True)
class ResourceActivation:
    """Source-audited command semantics for one beneficial object effect.

    Acquisition and combat safety remain separate from activation.  In
    particular, a spell-bearing mobile is still a source hazard; this record
    only prevents the runner from having to rediscover how a safely acquired
    object is consumed.
    """

    spell: str
    command: str
    mode: str
    requires_hold: bool
    consumes_object: bool
    consumes_charge: bool
    target: str | None = None


def source_room_level_rejection(
    room: RoomSource | None,
    character_level: int,
) -> str | None:
    """Return DD4's source access rejection for one destination room.

    ``act_move.c`` enforces the fourth-value area band on every move and also
    treats ``-4 -4`` areas as player-inaccessible safety zones. Keep this
    separate from mobile combat hazards so a legal target is not confused with
    an area the character cannot enter at all.
    """
    if room is None or character_level > 100:
        return None
    if room.area_low_level == -4 and room.area_high_level == -4:
        return "area is source-marked player-inaccessible"
    if room.area_low_enforced is None or room.area_high_enforced is None:
        return None
    if (
        character_level < room.area_low_enforced
        or character_level > room.area_high_enforced
    ):
        return (
            "area access requires level "
            f"{room.area_low_enforced}-{room.area_high_enforced}"
        )
    return None


def _source_container_access_notes(
    world: WorldSource,
    container_object_vnums: Collection[int],
    required_key_object_vnums: Collection[int],
    required_key_source_mobile_vnums: Collection[int],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Describe source container barriers without authorizing extraction.

    Resource reports are also used as audit evidence.  A nested potion must
    therefore retain the source container's closed/locked state and its key
    provenance; otherwise a locked display case can look like a safe ground
    stash to a later selector.
    """
    hazards: list[str] = []
    rejections: list[str] = []
    for container_vnum in container_object_vnums:
        container = world.objects.get(container_vnum)
        if container is None or container.item_type != ITEM_CONTAINER:
            rejections.append(
                f"source container {container_vnum} is not a parsed container"
            )
            continue
        flags = (
            int(container.values[1])
            if len(container.values) > 1
            else None
        )
        if flags is None:
            rejections.append(
                f"source container {container_vnum} has unknown flags"
            )
            continue
        if flags & CONT_CLOSED:
            hazards.append(
                f"source container is closed: {container.short_description} "
                f"({container_vnum})"
            )
        if flags & CONT_LOCKED:
            hazards.append(
                f"source container is locked: {container.short_description} "
                f"({container_vnum})"
            )
            rejections.append(
                f"source container {container_vnum} requires an explicit key "
                "acquisition plan"
            )
    if required_key_object_vnums:
        key_text = ",".join(str(vnum) for vnum in required_key_object_vnums)
        carrier_text = ",".join(
            str(vnum) for vnum in required_key_source_mobile_vnums
        ) or "none"
        hazards.append(
            f"source container keys {key_text}; source carriers {carrier_text}"
        )
        if not required_key_source_mobile_vnums:
            rejections.append(
                f"source container key {key_text} has no same-area source carrier"
            )
    return (
        tuple(dict.fromkeys(hazards)),
        tuple(dict.fromkeys(rejections)),
    )


_RESOURCE_EFFECT_SPELLS = {
    "sanctuary": frozenset({"sanctuary"}),
    "protection": frozenset({"protection"}),
    "healing": frozenset(
        {
            "cure blindness",
            "cure critical",
            "cure light",
            "cure poison",
            "cure serious",
            "heal",
            "power heal",
            "refresh",
        }
    ),
    "flight": frozenset({"fly", "levitation"}),
}
_RESOURCE_EFFECT_ALIASES = {
    "cure": "healing",
    "recovery": "healing",
    "fly": "flight",
    "levitation": "flight",
    "travel": "flight",
}
_RESOURCE_EFFECT_ORDER = (
    "sanctuary",
    "protection",
    "healing",
    "flight",
    "food",
)
_RESOURCE_EFFECT_SPELL_ORDER = {
    "sanctuary": ("sanctuary",),
    "protection": ("protection",),
    "healing": (
        "power heal",
        "heal",
        "cure critical",
        "cure serious",
        "cure light",
        "refresh",
    ),
    "flight": ("fly", "levitation"),
}


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


def pill_spell_names(item: ObjectSource) -> tuple[str, ...]:
    """Return normalized source spell names encoded on a pill prototype."""
    if item.item_type != ITEM_PILL:
        return ()
    return _encoded_spell_names(item)


def resource_effects_for_object(
    item: ObjectSource,
    *,
    effect: str = "all",
) -> tuple[str, ...]:
    """Return recovery effects supported by one source object.

    ``food`` is deliberately limited to the same positive, non-poisonous
    direct-food rule used by :func:`rank_food_stashes`.  Spell effects are
    read from the source-encoded potion, pill, scroll, wand, or staff values.
    """
    normalized = " ".join(str(effect).casefold().split())
    normalized = _RESOURCE_EFFECT_ALIASES.get(normalized, normalized)
    valid_effects = set(_RESOURCE_EFFECT_SPELLS) | {"food"}
    if normalized != "all" and normalized not in valid_effects:
        choices = ", ".join(("all", *_RESOURCE_EFFECT_ORDER))
        raise ValueError(f"unknown resource effect {effect!r}; choose {choices}")

    effects: list[str] = []
    if (
        item.item_type == ITEM_FOOD
        and item.values
        and item.values[0] > 0
        and (len(item.values) < 4 or item.values[3] == 0)
        and normalized in {"all", "food"}
    ):
        effects.append("food")
    spell_names = (
        set(potion_spell_names(item))
        | set(pill_spell_names(item))
        | set(castable_spell_names(item))
    )
    for name in _RESOURCE_EFFECT_ORDER:
        if name == "food" or (normalized not in {"all", name}):
            continue
        if spell_names.intersection(_RESOURCE_EFFECT_SPELLS[name]):
            effects.append(name)
    return tuple(effects)


def resource_activation_for_object(
    item: ObjectSource,
    *,
    effect: str,
    spell_name: str | None = None,
) -> ResourceActivation | None:
    """Return DD4's source command contract for one positive object effect.

    ``do_quaff`` consumes a potion, ``do_eat`` consumes a pill,
    ``do_recite`` consumes a held scroll, ``do_brandish`` spends a held staff
    charge, and ``do_zap`` spends a held wand charge. The command is
    deliberately descriptive rather than a ready-to-send selector: duplicate
    live objects still require the normal source/VNUM-aware keyword resolution
    at execution time.
    """
    normalized = " ".join(str(effect).casefold().split())
    normalized = _RESOURCE_EFFECT_ALIASES.get(normalized, normalized)
    requested_spell = (
        " ".join(str(spell_name).casefold().split())
        if spell_name is not None
        else None
    )
    if requested_spell is None:
        # Accepting a spell-shaped effect keeps the campaign selector able to
        # ask for an exact source spell without duplicating the effect table.
        spell_effect = next(
            (
                effect_name
                for effect_name, spell_names in _RESOURCE_EFFECT_SPELLS.items()
                if normalized in spell_names
            ),
            None,
        )
        if spell_effect is not None:
            requested_spell = normalized
            normalized = spell_effect
    if normalized not in _RESOURCE_EFFECT_SPELL_ORDER:
        return None
    spell_names = (
        set(potion_spell_names(item))
        | set(pill_spell_names(item))
        | set(castable_spell_names(item))
    )
    spell = requested_spell or next(
        (
            candidate
            for candidate in _RESOURCE_EFFECT_SPELL_ORDER[normalized]
            if candidate in spell_names
        ),
        None,
    )
    if spell not in spell_names:
        return None
    if spell is None:
        return None
    if item.item_type == ITEM_POTION:
        return ResourceActivation(
            spell=spell,
            command="quaff",
            mode="potion",
            requires_hold=False,
            consumes_object=True,
            consumes_charge=False,
        )
    if item.item_type == ITEM_PILL:
        return ResourceActivation(
            spell=spell,
            command="eat",
            mode="pill",
            requires_hold=False,
            consumes_object=True,
            consumes_charge=False,
        )
    if item.item_type == ITEM_SCROLL:
        return ResourceActivation(
            spell=spell,
            command="recite",
            mode="scroll",
            requires_hold=True,
            consumes_object=True,
            consumes_charge=False,
        )
    if item.item_type == ITEM_STAFF:
        return ResourceActivation(
            spell=spell,
            command="brandish",
            mode="staff",
            requires_hold=True,
            consumes_object=False,
            consumes_charge=True,
        )
    if item.item_type == ITEM_WAND:
        return ResourceActivation(
            spell=spell,
            command="zap",
            mode="wand",
            requires_hold=True,
            consumes_object=False,
            consumes_charge=True,
            target="self",
        )
    return None


def rank_resource_sources(
    world: WorldSource,
    *,
    character_level: int,
    effect: str = "all",
    character_max_hp: int | None = None,
    include_all_areas: bool = False,
    recall_origins: Mapping[int, int] | None = None,
) -> list[ResourcePlacement]:
    """List source resource placements with routes and hazard evidence.

    The report keeps shop stock, mob-carried objects, direct ground resets,
    and nested ground-container contents distinct. A matching hunt or
    ground-stash candidate contributes the same route, status, and hazard
    annotations used by campaign selection; a source placement without a
    current-level candidate remains visible as ``source-only`` rather than
    being silently discarded.
    """
    if character_level < 1:
        raise ValueError("character_level must be at least 1")
    # Validate the effect once even when the source contains no objects.
    normalized_effect = " ".join(str(effect).casefold().split())
    normalized_effect = _RESOURCE_EFFECT_ALIASES.get(
        normalized_effect,
        normalized_effect,
    )
    if normalized_effect != "all":
        resource_effects_for_object(
            ObjectSource(0, "", "", 0, (), 0),
            effect=normalized_effect,
        )
    allowed_areas = None if include_all_areas else set(LOW_LEVEL_AREA_FILES)
    selected_objects = tuple(
        sorted(
            (
                item
                for item in world.objects.values()
                if resource_effects_for_object(
                    item,
                    effect=normalized_effect,
                )
            ),
            key=lambda item: (item.vnum, item.short_description),
        )
    )
    if not selected_objects:
        return []
    selected_vnums = {item.vnum for item in selected_objects}

    candidates = rank_hunt_candidates(
        world,
        character_level=character_level,
        include_xp_only=True,
        include_below_band=True,
        character_max_hp=character_max_hp,
        include_all_areas=include_all_areas,
        required_loot_object_vnums=selected_vnums,
        recall_origins=recall_origins,
    )
    candidates_by_source = {
        (candidate.mobile_vnum, candidate.room_vnum): candidate
        for candidate in candidates
    }
    direct_candidates = _rank_direct_ground_stashes(
        world,
        character_level=character_level,
        include_all_areas=include_all_areas,
        object_filter=lambda item: item.vnum in selected_vnums,
        object_value=lambda _item: 1,
        object_keyword=_food_object_keyword,
        target="resource stash",
    )
    direct_by_room = {
        candidate.room_vnum: candidate for candidate in direct_candidates
    }
    direct_paths = _shortest_paths_from(world.rooms, RECALL_VNUM)
    object_by_vnum = {item.vnum: item for item in selected_objects}

    def fallback_mobile_hazards(mobile: MobileSource) -> tuple[str, ...]:
        hazards: list[str] = []
        if mobile.non_corporeal:
            hazards.append("source mobile is non-corporeal")
        if mobile.aggressive:
            hazards.append("source mobile is aggressive")
        if mobile.vnum in world.shopkeepers:
            hazards.append("source mobile is a shopkeeper")
        for special in world.mobile_specials.get(mobile.vnum, ()):
            hazards.append(f"source special: {special}")
        if mobile.attack_programs:
            hazards.append("source mobile has a combat-triggering program")
        return tuple(dict.fromkeys(hazards))

    def item_level_range(item: ObjectSource) -> tuple[int, int]:
        minimum = item.load_level_min or item.level
        maximum = item.load_level_max or item.level
        return minimum, maximum

    placements: list[ResourcePlacement] = []
    placement_keys: set[tuple[int, str, int | None, int, int]] = set()

    def append_placement(
        item: ObjectSource,
        *,
        source_kind: str,
        source_mobile_vnum: int | None,
        source_mobile: str,
        room: RoomSource,
        maximum_count: int,
        source_level_range: tuple[int, int],
        candidate: HuntCandidate | None,
        container_object_vnums: tuple[int, ...] = (),
        required_key_object_vnums: tuple[int, ...] = (),
        required_key_source_mobile_vnums: tuple[int, ...] = (),
    ) -> None:
        placement_key = (
            item.vnum,
            source_kind,
            source_mobile_vnum,
            room.vnum,
            maximum_count,
            container_object_vnums,
        )
        if placement_key in placement_keys:
            return
        placement_keys.add(placement_key)
        if candidate is None:
            path = direct_paths.get(room.vnum)
            route = path[0] if path is not None else ()
            source_route_rooms: tuple[int, ...] = ()
            source_analysis_route: tuple[str, ...] = ()
            route_key_object_vnums: tuple[int, ...] = ()
            route_key_source_mobile_vnums: tuple[int, ...] = ()
            hazards: tuple[str, ...] = ()
            autonomy_rejections: tuple[str, ...] = ()
            if path is not None:
                source_route_rooms = path[1]
            if path is None:
                analysis_path = _shortest_source_analysis_path(
                    world.rooms,
                    RECALL_VNUM,
                    room.vnum,
                )
                if analysis_path is not None:
                    (
                        source_analysis_route,
                        analysis_rooms,
                        _analysis_closed_doors,
                        route_key_object_vnums,
                    ) = analysis_path
                    source_route_rooms = analysis_rooms
                    route_key_source_mobile_vnums = _source_key_carriers(
                        world,
                        route_key_object_vnums,
                    )
                    autonomy_rejections = (
                        *autonomy_rejections,
                        *_source_route_key_acquisition_rejections(
                            world,
                            route_key_object_vnums,
                            directly_reachable_rooms=direct_paths.keys(),
                        ),
                    )
            status = "source-only"
            route_origin = 0
            area_rejections = tuple(
                rejection
                for path_room_vnum in source_route_rooms[1:]
                if (
                    rejection := source_room_level_rejection(
                        world.rooms.get(path_room_vnum),
                        character_level,
                    )
                ) is not None
            )
            if area_rejections:
                hazards = tuple(
                    f"source route area gate: {rejection}"
                    for rejection in area_rejections
                )
                autonomy_rejections = area_rejections
            if source_mobile_vnum is not None:
                mobile = world.mobiles.get(source_mobile_vnum)
                if mobile is not None:
                    hazards = tuple(
                        dict.fromkeys(
                            (*hazards, *fallback_mobile_hazards(mobile))
                        )
                    )
        else:
            route = candidate.route
            source_analysis_route = ()
            route_key_object_vnums = ()
            route_key_source_mobile_vnums = ()
            status = candidate.status
            route_origin = candidate.route_origin_recall_index
            hazards = candidate.hazards
            autonomy_rejections = candidate.autonomy_rejections
        container_hazards, container_rejections = _source_container_access_notes(
            world,
            container_object_vnums,
            required_key_object_vnums,
            required_key_source_mobile_vnums,
        )
        hazards = tuple(dict.fromkeys((*hazards, *container_hazards)))
        autonomy_rejections = tuple(
            dict.fromkeys((*autonomy_rejections, *container_rejections))
        )
        for effect_name in resource_effects_for_object(
            item,
            effect=normalized_effect,
        ):
            activation = resource_activation_for_object(
                item,
                effect=effect_name,
            )
            placements.append(
                ResourcePlacement(
                    effect=effect_name,
                    object_vnum=item.vnum,
                    object_keywords=item.keywords,
                    object_description=item.short_description,
                    item_type=item.item_type,
                    source_kind=source_kind,
                    source_mobile_vnum=source_mobile_vnum,
                    source_mobile=source_mobile,
                    room_vnum=room.vnum,
                    room_name=room.name,
                    area_file=room.area_file,
                    maximum_count=maximum_count,
                    source_level_range=source_level_range,
                    status=status,
                    route=route,
                    route_origin_recall_index=route_origin,
                    hazards=tuple(dict.fromkeys(hazards)),
                    autonomy_rejections=tuple(dict.fromkeys(autonomy_rejections)),
                    activation=activation,
                    container_object_vnums=container_object_vnums,
                    required_key_object_vnums=required_key_object_vnums,
                    required_key_source_mobile_vnums=(
                        required_key_source_mobile_vnums
                    ),
                    source_analysis_route=source_analysis_route,
                    route_key_object_vnums=route_key_object_vnums,
                    route_key_source_mobile_vnums=route_key_source_mobile_vnums,
                )
            )

    for reset in world.mob_resets:
        room = world.rooms.get(reset.room_vnum)
        mobile = world.mobiles.get(reset.mobile_vnum)
        if (
            room is None
            or mobile is None
            or (allowed_areas is not None and room.area_file not in allowed_areas)
        ):
            continue
        matching_vnums = selected_vnums.intersection(_reset_object_vnums(reset))
        for object_vnum in sorted(matching_vnums):
            item = object_by_vnum[object_vnum]
            equipped = any(
                equipped_vnum == object_vnum
                for _wear_location, equipped_vnum in reset.equipment
            )
            source_kind = (
                "shop-stock"
                if mobile.vnum in world.shopkeepers
                else "mob-equipped"
                if equipped
                else "mob-carried"
            )
            append_placement(
                item,
                source_kind=source_kind,
                source_mobile_vnum=mobile.vnum,
                source_mobile=mobile.short_description,
                room=room,
                maximum_count=reset.maximum_count,
                source_level_range=_mobile_level_range(mobile.level),
                candidate=candidates_by_source.get((mobile.vnum, room.vnum)),
            )

    for reset in world.room_object_resets:
        room = world.rooms.get(reset.room_vnum)
        item = object_by_vnum.get(reset.object_vnum)
        if (
            room is None
            or item is None
            or (allowed_areas is not None and room.area_file not in allowed_areas)
        ):
            continue
        append_placement(
            item,
            source_kind="ground-reset",
            source_mobile_vnum=None,
            source_mobile="",
            room=room,
            maximum_count=reset.maximum_count,
            source_level_range=item_level_range(item),
            candidate=direct_by_room.get(room.vnum),
        )

    # ``P`` resets place an object inside a container loaded by an ``O``
    # reset. Preserve the source chain and any container key requirement. A
    # nested object is never promoted to an executable loose-ground route by
    # this report alone; callers still need to validate the route and perform
    # the source-proven extraction actions. Build every target path once per
    # root: the old root/target traversal repeated the same graph walk for
    # every matching resource and made all-area reports needlessly unbounded.
    container_roots = {
        reset.object_vnum
        for reset in world.room_object_resets
        if reset.object_vnum in world.container_contents
    }
    container_paths_by_root: dict[
        int, dict[int, tuple[tuple[int, ...], ...]]
    ] = {}

    for root_vnum in container_roots:
        paths_by_target: dict[int, list[tuple[int, ...]]] = {}

        def walk(
            current: int,
            ancestors: tuple[int, ...],
        ) -> None:
            if current in ancestors:
                return
            next_ancestors = (*ancestors, current)
            for child_vnum in world.container_contents.get(current, ()):
                if child_vnum in selected_vnums:
                    paths_by_target.setdefault(child_vnum, []).append(
                        next_ancestors
                    )
                if child_vnum in world.container_contents:
                    walk(child_vnum, next_ancestors)

        walk(root_vnum, ())
        container_paths_by_root[root_vnum] = {
            target_vnum: tuple(paths)
            for target_vnum, paths in paths_by_target.items()
        }

    direct_container_candidates = _rank_direct_ground_stashes(
        world,
        character_level=character_level,
        include_all_areas=include_all_areas,
        object_filter=lambda candidate: candidate.vnum in container_roots,
        object_value=lambda _candidate: 1,
        object_keyword=lambda candidate: _food_object_keyword(candidate),
        target="resource container",
    )
    direct_container_by_room = {
        candidate.room_vnum: candidate
        for candidate in direct_container_candidates
    }
    for reset in world.room_object_resets:
        room = world.rooms.get(reset.room_vnum)
        root = world.objects.get(reset.object_vnum)
        if (
            room is None
            or root is None
            or reset.object_vnum not in container_roots
            or (allowed_areas is not None and room.area_file not in allowed_areas)
        ):
            continue
        paths_by_target = container_paths_by_root.get(root.vnum, {})
        for item in selected_objects:
            for container_chain in paths_by_target.get(item.vnum, ()):
                key_vnums = tuple(
                    dict.fromkeys(
                        int(container.values[2])
                        for container_vnum in container_chain
                        if (container := world.objects.get(container_vnum))
                        is not None
                        and container.item_type == ITEM_CONTAINER
                        and len(container.values) > 2
                        and int(container.values[2]) > 0
                    )
                )
                key_mobile_vnums = tuple(
                    sorted(
                        {
                            mob_reset.mobile_vnum
                            for mob_reset in world.mob_resets
                            if (
                                (key_room := world.rooms.get(mob_reset.room_vnum))
                                is not None
                                and key_room.area_file == room.area_file
                            )
                            and set(key_vnums).intersection(
                                _reset_object_vnums(mob_reset)
                            )
                        }
                    )
                )
                append_placement(
                    item,
                    source_kind="ground-container",
                    source_mobile_vnum=None,
                    source_mobile="",
                    room=room,
                    maximum_count=reset.maximum_count,
                    source_level_range=item_level_range(item),
                    candidate=direct_container_by_room.get(room.vnum),
                    container_object_vnums=container_chain,
                    required_key_object_vnums=key_vnums,
                    required_key_source_mobile_vnums=key_mobile_vnums,
                )

    status_order = {
        "promising": 0,
        "caution": 1,
        "source-only": 2,
        "reject": 3,
    }
    return sorted(
        placements,
        key=lambda placement: (
            _RESOURCE_EFFECT_ORDER.index(placement.effect),
            status_order.get(placement.status, 4),
            len(placement.route),
            placement.room_vnum,
            placement.object_vnum,
            placement.source_kind,
        ),
    )


_C_DEFINE = re.compile(
    r"^\s*#define\s+(?P<name>[A-Za-z_]\w*)\s+(?P<value>.+?)\s*$"
)
_C_IDENTIFIER = re.compile(r"\b[A-Za-z_]\w*\b")


def _strip_c_comments(value: str) -> str:
    value = re.sub(r"/\*.*?\*/", "", value, flags=re.DOTALL)
    return re.sub(r"//[^\r\n]*", "", value)


def _parse_c_integer_expression(
    expression: str,
    macros: Mapping[str, int],
) -> int | None:
    """Evaluate the small integer-expression subset used by mob.c tables."""
    expression = " ".join(expression.split())
    if not expression or expression.endswith("\\"):
        return None

    def replace_identifier(match: re.Match[str]) -> str:
        name = match.group(0)
        if name not in macros:
            raise ValueError(name)
        return str(macros[name])

    try:
        resolved = _C_IDENTIFIER.sub(replace_identifier, expression)
    except ValueError:
        return None
    if not re.fullmatch(r"[0-9A-Fa-fxX\s()+\-*/%<>&|^~]+", resolved):
        return None
    try:
        return int(eval(resolved, {"__builtins__": {}}, {}))
    except (ArithmeticError, SyntaxError, TypeError, ValueError):
        return None


def _load_c_integer_macros(header_text: str) -> dict[str, int]:
    """Resolve the flag aliases used by DD4's source template tables."""
    definitions: dict[str, str] = {}
    for line in _strip_c_comments(header_text).splitlines():
        match = _C_DEFINE.match(line)
        if match is not None:
            definitions[match.group("name")] = match.group("value").strip()

    values: dict[str, int] = {
        "INT_MIN": -(1 << 31),
        "INT_MAX": (1 << 31) - 1,
    }
    for _ in range(len(definitions) + 1):
        progress = False
        for name, expression in definitions.items():
            parsed = _parse_c_integer_expression(expression, values)
            if parsed is None or values.get(name) == parsed:
                continue
            values[name] = parsed
            progress = True
        if not progress:
            break
    return values


def _c_initializer_rows(source_text: str, table_name: str) -> tuple[str, ...]:
    """Extract top-level brace records from one C initializer table."""
    source_text = _strip_c_comments(source_text)
    match = re.search(
        rf"\b{re.escape(table_name)}\s*\[[^\]]+\]\s*=\s*\{{",
        source_text,
    )
    if match is None:
        return ()
    opening = source_text.find("{", match.start())
    rows: list[str] = []
    depth = 0
    row_start: int | None = None
    quoted = False
    escaped = False
    for position in range(opening, len(source_text)):
        char = source_text[position]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
            continue
        if char == "{":
            depth += 1
            if depth == 2:
                row_start = position + 1
        elif char == "}":
            if depth == 2 and row_start is not None:
                rows.append(source_text[row_start:position])
                row_start = None
            depth -= 1
            if depth == 0:
                break
    return tuple(rows)


def _split_c_initializer_fields(row: str) -> tuple[str, ...]:
    fields: list[str] = []
    start = 0
    parentheses = 0
    braces = 0
    quoted = False
    escaped = False
    for position, char in enumerate(row):
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char == "(":
            parentheses += 1
        elif char == ")":
            parentheses = max(0, parentheses - 1)
        elif char == "{":
            braces += 1
        elif char == "}":
            braces = max(0, braces - 1)
        elif char == "," and parentheses == 0 and braces == 0:
            fields.append(row[start:position].strip())
            start = position + 1
    fields.append(row[start:].strip())
    return tuple(fields)


def _c_string_literal(value: str) -> str | None:
    match = re.fullmatch(r'\s*"((?:\\.|[^"\\])*)"\s*', value, re.DOTALL)
    return None if match is None else match.group(1)


_UNPARSED_SOURCE_SPECIAL = "__unparsed_source_special__"


def _parse_c_special_name(expression: str) -> str | None:
    literal = _c_string_literal(expression)
    if literal is not None:
        return literal
    if expression.strip().casefold() == "null":
        return None
    # A source parser failure must remain a hazard, not silently become an
    # empty special slot that could authorize an unsafe route.
    return _UNPARSED_SOURCE_SPECIAL


def _parse_c_special_names(
    fields: tuple[str, ...],
    start: int,
) -> tuple[str | None, ...]:
    return tuple(
        _parse_c_special_name(fields[start + offset])
        if start + offset < len(fields)
        else None
        for offset in range(MOBILE_SPECIAL_SLOTS)
    )


def _parse_c_special_chances(
    expression: str | None,
    macros: Mapping[str, int],
    *,
    default: tuple[int, ...],
) -> tuple[int, ...]:
    if expression is None:
        return default
    normalized = " ".join(expression.split()).casefold()
    if normalized == "mob_special_chances_inherit":
        return (MOBILE_TEMPLATE_UNSET,) * MOBILE_SPECIAL_SLOTS
    if normalized == "mob_special_chances_auto":
        return (MOBILE_SPECIAL_AUTO,) * MOBILE_SPECIAL_SLOTS
    if not (expression.strip().startswith("{") and expression.strip().endswith("}")):
        return default
    values = _split_c_initializer_fields(expression.strip()[1:-1])
    if len(values) != MOBILE_SPECIAL_SLOTS:
        return default
    parsed = tuple(
        _parse_c_integer_expression(value, macros)
        for value in values
    )
    if any(value is None for value in parsed):
        return default
    return tuple(int(value) for value in parsed)


def _resolve_template_special_names(
    species_names: tuple[str | None, ...],
    archetype_names: tuple[str | None, ...],
) -> tuple[str | None, ...]:
    resolved: list[str | None] = []
    for species_name, archetype_name in zip(
        species_names,
        archetype_names,
        strict=True,
    ):
        # ``None`` means inherit; an empty string explicitly clears the slot.
        resolved.append(
            species_name
            if archetype_name is None
            else (archetype_name or None)
        )
    return tuple(resolved)


def _resolve_template_special_chances(
    species_chances: tuple[int, ...],
    archetype_chances: tuple[int, ...],
) -> tuple[int, ...]:
    inherit = (MOBILE_TEMPLATE_UNSET,) * MOBILE_SPECIAL_SLOTS
    if archetype_chances != inherit:
        return archetype_chances
    if species_chances != inherit:
        return species_chances
    return (MOBILE_SPECIAL_AUTO,) * MOBILE_SPECIAL_SLOTS


def _effective_mobile_special_names(
    names: Iterable[str | None],
    chances: Iterable[int],
) -> tuple[str, ...]:
    normalized_names = tuple(names)
    normalized_chances = tuple(chances)
    nonempty = tuple(
        name
        for name in normalized_names
        if name is not None and name != ""
    )
    if not nonempty:
        return ()
    if len(normalized_names) != MOBILE_SPECIAL_SLOTS or len(normalized_chances) != MOBILE_SPECIAL_SLOTS:
        return tuple(dict.fromkeys(nonempty))
    if normalized_chances in {
        (MOBILE_TEMPLATE_UNSET,) * MOBILE_SPECIAL_SLOTS,
        (MOBILE_SPECIAL_AUTO,) * MOBILE_SPECIAL_SLOTS,
    }:
        return tuple(dict.fromkeys(nonempty))
    if any(chance < 0 or chance > 100 for chance in normalized_chances):
        return tuple(dict.fromkeys(nonempty))
    if sum(normalized_chances) not in {0, 100}:
        return tuple(dict.fromkeys(nonempty))
    return tuple(
        dict.fromkeys(
            name
            for name, chance in zip(
                normalized_names,
                normalized_chances,
                strict=True,
            )
            if name is not None and name != "" and chance > 0
        )
    )


@lru_cache(maxsize=4)
def load_mobile_template_catalog(
    source_directory: Path,
) -> dict[str, MobileTemplateSource]:
    """Load DD4's resolved mobile-template defaults from the source mirror.

    Area files carry only the individual XOR overrides.  Keeping this parser
    beside the area parser means a source refresh changes candidate safety
    decisions without requiring a hand-maintained Python copy of mob.c.
    """
    mob_path = source_directory / "mob.c"
    header_path = source_directory / "merc.h"
    if not mob_path.is_file() or not header_path.is_file():
        return {}
    mob_text = mob_path.read_text(encoding="latin-1")
    macros = _load_c_integer_macros(header_path.read_text(encoding="latin-1"))
    species_by_name: dict[
        str,
        tuple[
            str,
            int,
            int,
            int,
            int,
            int,
            tuple[str | None, ...],
            tuple[int, ...],
        ],
    ] = {}
    for row in _c_initializer_rows(mob_text, "species_table"):
        fields = _split_c_initializer_fields(row)
        if len(fields) < 4:
            continue
        name = _c_string_literal(fields[0])
        if not name:
            continue
        species_special_names = _parse_c_special_names(fields, 16)
        species_special_chances = _parse_c_special_chances(
            fields[19] if len(fields) > 19 else None,
            macros,
            default=(MOBILE_TEMPLATE_UNSET,) * MOBILE_SPECIAL_SLOTS,
        )
        species_by_name[name.casefold()] = (
            name,
            _parse_c_integer_expression(fields[1], macros) or 0,
            _parse_c_integer_expression(fields[2], macros) or 0,
            _parse_c_integer_expression(fields[3], macros) or 0,
            (
                _parse_c_integer_expression(fields[8], macros)
                if len(fields) > 8
                else MOBILE_TEMPLATE_UNSET
            ),
            (
                _parse_c_integer_expression(fields[9], macros)
                if len(fields) > 9
                else MOBILE_TEMPLATE_UNSET
            ),
            species_special_names,
            species_special_chances,
        )

    templates: dict[str, MobileTemplateSource] = {}
    for row in _c_initializer_rows(mob_text, "mob_table"):
        fields = _split_c_initializer_fields(row)
        if len(fields) < 12:
            continue
        name = _c_string_literal(fields[0])
        species_name = _c_string_literal(fields[1])
        if not name or not species_name:
            continue
        species = species_by_name.get(species_name.casefold())
        if species is None:
            continue
        archetype_hp_modifier = (
            _parse_c_integer_expression(fields[11], macros)
            if len(fields) > 11
            else MOBILE_TEMPLATE_UNSET
        )
        archetype_damage_modifier = (
            _parse_c_integer_expression(fields[12], macros)
            if len(fields) > 12
            else MOBILE_TEMPLATE_UNSET
        )
        archetype_special_names = _parse_c_special_names(fields, 19)
        archetype_special_chances = _parse_c_special_chances(
            fields[23] if len(fields) > 23 else None,
            macros,
            default=(MOBILE_TEMPLATE_UNSET,) * MOBILE_SPECIAL_SLOTS,
        )
        special_names = _resolve_template_special_names(
            species[6],
            archetype_special_names,
        )
        special_chances = _resolve_template_special_chances(
            species[7],
            archetype_special_chances,
        )
        templates[name.casefold()] = MobileTemplateSource(
            name=name,
            species=species[0],
            act_flags=species[1]
            ^ (_parse_c_integer_expression(fields[4], macros) or 0),
            affected_flags=species[2]
            ^ (_parse_c_integer_expression(fields[5], macros) or 0),
            body_form_flags=species[3]
            ^ (_parse_c_integer_expression(fields[6], macros) or 0),
            xp_modifier=(
                _parse_c_integer_expression(
                    fields[22] if len(fields) > 22 else fields[-1],
                    macros,
                )
                or 0
            ),
            hp_modifier=_resolve_template_scalar(
                species[4],
                archetype_hp_modifier,
            ),
            damage_modifier=_resolve_template_scalar(
                species[5],
                archetype_damage_modifier,
            ),
            special_names=special_names,
            special_chances=special_chances,
        )
    return templates


@lru_cache(maxsize=4)
def load_world_source(
    area_directory: Path,
    *,
    include_all_areas: bool = False,
) -> WorldSource:
    """Parse global hazards and selected candidate-area loot evidence."""
    if not area_directory.is_dir():
        raise FileNotFoundError(f"DD4 area directory not found: {area_directory}")

    mobile_templates = load_mobile_template_catalog(area_directory.parent / "src")
    world = WorldSource(mobile_templates=mobile_templates)
    const_path = area_directory.parent / "src" / "const.c"
    if const_path.is_file():
        from .teaching import parse_skill_groups

        try:
            world.skill_groups = parse_skill_groups(const_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            # Missing teaching evidence cannot authorize the optional fallback.
            world.skill_groups = {}
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
            mobile_templates=mobile_templates,
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
    mobile_templates: Mapping[str, MobileTemplateSource] | None = None,
) -> AreaSource:
    lines = path.read_text(encoding="latin-1").splitlines()
    area_levels = _parse_area_level_bounds(lines)
    sections = _section_ranges(lines)
    mobiles = (
        _parse_mobiles(
            lines,
            sections.get("#MOBILES"),
            path.name,
            mobile_templates=mobile_templates,
        )
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
    if area_levels is not None:
        low_level, high_level, low_enforced, high_enforced = area_levels
        for room in rooms.values():
            room.area_low_level = low_level
            room.area_high_level = high_level
            room.area_low_enforced = low_enforced
            room.area_high_enforced = high_enforced
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
            mobiles=mobiles,
            mobile_templates=mobile_templates,
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


def _parse_area_level_bounds(
    lines: Collection[str],
) -> tuple[int, int, int, int] | None:
    """Parse DD4's four numeric area-header level values."""
    for raw_line in tuple(lines)[:6]:
        fields = raw_line.split()
        if len(fields) != 4:
            continue
        try:
            values = tuple(int(field) for field in fields)
        except ValueError:
            continue
        return (values[0], values[1], values[2], values[3])
    return None


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
        or not mobile.damage_modifier_known
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
        damage_modifier=mobile.damage_modifier,
    )
    critical_hit_damage = _mobile_critical_hit_damage(
        maximum_level,
        wielding=wielding or dual_wielding,
        damage_modifier=mobile.damage_modifier,
    )
    return (
        peak_round_damage < character_max_hp
        and critical_hit_damage < character_max_hp
    )


def source_mobile_route_aggressor_is_bounded(
    world: WorldSource,
    mobile: MobileSource,
    *,
    character_level: int,
    character_max_hp: int | None = None,
) -> bool:
    """Return whether one below-band route aggressor may be finished once.

    This is deliberately narrower than the ordinary ten-level movement
    cutoff.  It is for source-identified mobiles that can only make a small
    incidental interruption: scripted attacks, unsafe specials, dual-wielded
    or otherwise ambiguous equipment, and useful-band loads remain rejected.
    A single source-listed wielded weapon is admitted only when its stricter
    peak and critical-damage bounds fit the character's transit reserve.
    Additional source-listed armor is inert for this damage bound and is
    accepted when its object type is known; a second weapon or unknown
    equipment remains ambiguous and is rejected.
    Without a live HP ceiling the older ten-level rule remains the fail-closed
    fallback.
    """
    if (
        not mobile.aggressive
        or mobile.attack_programs
        or not mobile.damage_modifier_known
    ):
        return False
    specials = {
        str(special).strip().casefold()
        for special in world.mobile_specials.get(mobile.vnum, ())
    }
    if specials and not specials <= SAFE_NONCOMBAT_SPECIALS:
        # ``update.c`` skips ordinary aggression when the player is more
        # than ten levels above the mobile. Combat-only specials such as
        # ``spec_cast_undead`` also require ``victim->fighting == ch`` in
        # ``special.c``, so they cannot affect this transit at that gap.
        maximum_level = _mobile_level_range(mobile.level)[1]
        if not (
            specials <= TRANSIT_SAFE_COMBAT_ONLY_SPECIALS
            and character_level > maximum_level + 10
        ):
            return False
    maximum_level = _mobile_level_range(mobile.level)[1]
    if maximum_level > character_level - 5:
        return False
    resets = [
        reset
        for reset in world.mob_resets
        if reset.mobile_vnum == mobile.vnum
    ]
    if not resets:
        # Synthetic and legacy callers may provide only the mobile identity.
        # Preserve their older level-only fallback; parsed ranked candidates
        # always originate from a concrete reset and take the strict branch.
        if character_max_hp is None or character_max_hp <= 0:
            return maximum_level <= character_level - _SOURCE_TRANSIT_AGGRESSOR_RISK_GAP
        peak_round_damage = _mobile_peak_round_damage(
            maximum_level,
            wielding=False,
            dual_wielding=False,
            damage_modifier=mobile.damage_modifier,
        )
        critical_hit_damage = _mobile_critical_hit_damage(
            maximum_level,
            wielding=False,
            damage_modifier=mobile.damage_modifier,
        )
        return (
            peak_round_damage * 100
            <= int(character_max_hp * _SOURCE_BOUNDED_TRANSIT_PEAK_RATIO * 100)
            and critical_hit_damage * 100
            <= int(
                character_max_hp * _SOURCE_BOUNDED_TRANSIT_CRITICAL_RATIO * 100
            )
        )
    # A mobile prototype can reset in more than one room. Equipment belongs
    # to each reset instance; aggregating the rows would turn one sword on
    # each of two separate spawns into a false dual-wielding profile.
    reset_profiles: list[tuple[bool, bool]] = []
    for reset in resets:
        reset_wielding = False
        reset_dual_wielding = False
        for wear_location, object_vnum in tuple(reset.equipment):
            if wear_location == WEAR_DUAL:
                reset_dual_wielding = True
                continue
            item = world.objects.get(object_vnum)
            if wear_location == WEAR_WIELD:
                if (
                    reset_wielding
                    or item is None
                    or item.item_type != ITEM_WEAPON
                ):
                    return False
                reset_wielding = True
                continue
            if item is None or item.item_type != ITEM_ARMOR:
                # Held objects, unknown prototypes, and non-armor equipment
                # can change the interruption in ways this envelope does not
                # model. Keep those source proofs closed.
                return False
        if reset_dual_wielding:
            return False
        reset_profiles.append((reset_wielding, reset_dual_wielding))
    if any(dual_wielding for _wielding, dual_wielding in reset_profiles):
        return False
    if character_max_hp is None or character_max_hp <= 0:
        return maximum_level <= character_level - _SOURCE_TRANSIT_AGGRESSOR_RISK_GAP
    peak_limit = int(
        character_max_hp * _SOURCE_BOUNDED_TRANSIT_PEAK_RATIO * 100
    )
    critical_limit = int(
        character_max_hp * _SOURCE_BOUNDED_TRANSIT_CRITICAL_RATIO * 100
    )
    return all(
        _mobile_peak_round_damage(
            maximum_level,
            wielding=wielding,
            dual_wielding=dual_wielding,
            damage_modifier=mobile.damage_modifier,
        )
        * 100
        <= peak_limit
        and _mobile_critical_hit_damage(
            maximum_level,
            wielding=wielding,
            damage_modifier=mobile.damage_modifier,
        )
        * 100
        <= critical_limit
        for wielding, dual_wielding in reset_profiles
    )


def source_mobile_route_program_attacker_is_bounded(
    world: WorldSource,
    mobile: MobileSource,
    *,
    character_level: int,
    character_max_hp: int | None,
) -> bool:
    """Return whether one probabilistic greeter is a bounded transit fight.

    This exception is intentionally source-generic but narrow. It covers an
    exact, low-chance ``greet_prog`` attacker such as Midgaard's drunk only
    when the mobile is unarmed, ordinary rank-adjusted HP fits inside the
    character's maximum HP, and both ordinary and critical damage remain well
    inside the existing transit reserve. Live identity, isolation, health,
    and return gates still decide whether an interruption is actually fought.
    """
    if (
        character_max_hp is None
        or character_max_hp <= 0
        or mobile.aggressive
        or mobile.non_corporeal
        or mobile.costs_fame
        or mobile.vnum in world.shopkeepers
        or mobile.act_flags & (ACT_NO_EXPERIENCE | ACT_NO_FIGHT)
        or not mobile.hp_modifier_known
        or not mobile.damage_modifier_known
    ):
        return False
    attack_programs = mobile.attack_programs
    if len(attack_programs) != 1:
        return False
    program = attack_programs[0]
    if program.trigger != "greet_prog":
        return False
    try:
        trigger_percent = int(str(program.condition).strip())
    except (TypeError, ValueError):
        return False
    if not 0 < trigger_percent <= _SOURCE_BOUNDED_PROGRAM_MAX_TRIGGER_PERCENT:
        return False
    if world.mobile_specials.get(mobile.vnum):
        return False

    maximum_level = _mobile_level_range(mobile.level)[1]
    if maximum_level > character_level - _SOURCE_BOUNDED_PROGRAM_LEVEL_GAP:
        return False
    resets = tuple(
        reset
        for reset in world.mob_resets
        if reset.mobile_vnum == mobile.vnum
    )
    if (
        len(resets) != 1
        or not 0 < resets[0].maximum_count <= _SOURCE_BOUNDED_PROGRAM_MAX_CAPACITY
        or resets[0].equipment
    ):
        return False

    _, maximum_hp = _mobile_base_hp_range(
        _mobile_level_range(mobile.level),
        rank=mobile.rank,
        hp_modifier=mobile.hp_modifier,
    )
    peak_round_damage = _mobile_peak_round_damage(
        maximum_level,
        wielding=False,
        dual_wielding=False,
        damage_modifier=mobile.damage_modifier,
    )
    critical_hit_damage = _mobile_critical_hit_damage(
        maximum_level,
        wielding=False,
        damage_modifier=mobile.damage_modifier,
    )
    return (
        maximum_hp <= character_max_hp
        and peak_round_damage * 100
        <= int(character_max_hp * _SOURCE_BOUNDED_TRANSIT_PEAK_RATIO * 100)
        and critical_hit_damage * 100
        <= int(character_max_hp * _SOURCE_BOUNDED_TRANSIT_CRITICAL_RATIO * 100)
    )


def rank_hunt_candidates(
    world: WorldSource,
    *,
    character_level: int,
    character_class: str | None = None,
    character_subclass: str | None = None,
    known_skills: Collection[str] = (),
    known_skill_levels: Mapping[str, int] | None = None,
    boot_kill_counts: Mapping[str, int] | None = None,
    boot_kill_counts_by_mobile_vnum: Mapping[int, int] | None = None,
    include_xp_only: bool = False,
    include_below_band: bool = False,
    character_max_hp: int | None = None,
    include_level_ceiling_candidates: bool = False,
    level_ceiling_offset: int | None = None,
    include_all_areas: bool = False,
    required_loot_object_vnums: Collection[int] = (),
    route_key_object_vnums: Collection[int] = (),
    recall_origins: Mapping[int, int] | None = None,
    character_alignment: int | None = None,
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
    prototype_population_limits: dict[int, int] = {}
    for reset in world.mob_resets:
        prototype_population_limits[reset.mobile_vnum] = max(
            prototype_population_limits.get(reset.mobile_vnum, 0),
            reset.maximum_count,
        )
    candidate_area_files = None if include_all_areas else set(LOW_LEVEL_AREA_FILES)
    wandering_aggressors = _wandering_aggressors(world)
    recall_origin_rooms: dict[int, int] = {0: RECALL_VNUM}
    for raw_index, raw_room_vnum in (recall_origins or {}).items():
        try:
            index = int(raw_index)
            room_vnum = int(raw_room_vnum)
        except (TypeError, ValueError):
            continue
        if index < 0 or room_vnum not in world.rooms:
            continue
        recall_origin_rooms[index] = room_vnum
    route_key_vnums = {
        int(object_vnum) for object_vnum in route_key_object_vnums
    }
    recall_paths_by_origin = {
        index: _shortest_paths_from(
            world.rooms,
            room_vnum,
            unlockable_key_vnums=route_key_vnums,
        )
        for index, room_vnum in recall_origin_rooms.items()
    }
    wanderer_reachability = {
        (mobile.vnum, reset.room_vnum): _wanderer_reachable_rooms(
            world,
            mobile,
            reset.room_vnum,
        )
        for mobile, reset in wandering_aggressors
    }
    # Index source reachability once, retaining reset order for stable evidence.
    # Joining-only specials matter at the endpoint, not every transit room.
    transit_wanderers: dict[int, set[int]] = {}
    endpoint_wanderers: dict[int, set[int]] = {}
    for index, (hazard, hazard_reset) in enumerate(wandering_aggressors):
        if _source_mobile_has_safe_noncombat_special(world, hazard.vnum):
            continue
        room_index = (
            transit_wanderers
            if hazard.aggressive
            or hazard.attack_programs
            or _source_mobile_has_unsafe_special(
                world,
                hazard.vnum,
                hazard,
                character_level=character_level,
            )
            else endpoint_wanderers
        )
        for reachable_room in wanderer_reachability[
            (hazard.vnum, hazard_reset.room_vnum)
        ]:
            room_index.setdefault(reachable_room, set()).add(index)
    source_keyword_counts = _source_keyword_counts(world)
    required_loot_vnums = {
        int(object_vnum) for object_vnum in required_loot_object_vnums
    }
    route_hazard_rooms = _route_hazard_rooms(
        world,
        resets_by_room,
        character_level=character_level,
    )
    safe_recall_paths_by_origin = {
        index: _shortest_paths_from(
            world.rooms,
            room_vnum,
            blocked_rooms=route_hazard_rooms - {room_vnum},
            unlockable_key_vnums=route_key_vnums,
        )
        for index, room_vnum in recall_origin_rooms.items()
    }

    def path_from_recall_origin(
        room_vnum: int,
    ) -> tuple[tuple[str, ...], tuple[int, ...], int, int, int] | None:
        """Choose a source route from an observed recall point.

        Prefer a route that avoids source-identified hazards, then the
        shortest route.  The default recall point remains the only option
        unless the caller has supplied a live-observed recall list.
        """
        choices: list[
            tuple[
                tuple[int, int, int, int],
                tuple[tuple[str, ...], tuple[int, ...], int],
                int,
            ]
        ] = []
        for index, paths in recall_paths_by_origin.items():
            direct = paths.get(room_vnum)
            if direct is None:
                continue
            if any(
                source_room_level_rejection(world.rooms.get(path_room), character_level)
                for path_room in direct[1][1:]
            ):
                # ``act_move.c`` checks the destination room before moving;
                # do not rank a target behind an enforced area gate.
                continue
            selected = direct
            if route_hazard_rooms.intersection(direct[1][:-1]):
                safe = safe_recall_paths_by_origin[index].get(room_vnum)
                if (
                    safe is not None
                    and len(safe[0]) <= len(direct[0]) + _MAX_SOURCE_ROUTE_DETOUR_STEPS
                ):
                    selected = safe
            has_route_hazard = bool(
                route_hazard_rooms.intersection(selected[1][:-1])
            )
            choices.append(
                (
                    (
                        int(has_route_hazard),
                        len(selected[0]),
                        selected[2],
                        index,
                    ),
                    selected,
                    index,
                )
            )
        if not choices:
            return None
        _, selected, index = min(choices, key=lambda item: item[0])
        return (*selected, index, recall_origin_rooms[index])
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
        if source_room_level_rejection(room, character_level) is not None:
            continue
        reset_object_vnums = _reset_object_vnums(reset)
        required_loot_objects = tuple(
            world.objects[object_vnum]
            for object_vnum in reset_object_vnums
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

        # Equipment resets are separate from carried-object resets in the
        # source model.  Treat both as loot after a kill so weapon and armour
        # provenance is not lost from ordinary candidates.
        loot_objects = _loot_objects(world, reset_object_vnums)
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
        hp_range = _mobile_base_hp_range(
            level_range,
            rank=mobile.rank,
            hp_modifier=mobile.hp_modifier,
        )
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
            damage_modifier=mobile.damage_modifier,
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
            damage_modifier=mobile.damage_modifier,
        )
        critical_hit_damage = _mobile_critical_hit_damage(
            level_range[1],
            wielding=bool(equipped_weapon_slots),
            damage_modifier=mobile.damage_modifier,
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

        path_choice = path_from_recall_origin(reset.room_vnum)
        if path_choice is None:
            continue
        route, path_rooms, closed_doors, route_origin_recall_index, route_origin_room_vnum = path_choice
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
            route_preflight_route_room_names,
            route_hard_hazard_targets,
        ) = _route_preflight_metadata(
            world,
            route,
            character_level=character_level,
        )
        hazards: list[str] = []
        autonomy_rejections: list[str] = []
        route_hazard_mobile_vnums: set[int] = set()
        route_aggressive_mobile_vnums: set[int] = set()
        route_attack_program_mobile_vnums: set[int] = set()
        route_special_mobile_vnums: set[int] = set()
        dangerous = False
        if not mobile.hp_modifier_known:
            hazards.append("source mobile HP modifier is unavailable")
            autonomy_rejections.append(
                "source mobile HP modifier is unavailable"
            )
            dangerous = True
        if not mobile.damage_modifier_known:
            hazards.append("source mobile damage modifier is unavailable")
            autonomy_rejections.append(
                "source mobile damage modifier is unavailable"
            )
            dangerous = True
        normalized_target = _normalize_name(mobile.short_description)
        boot_kills = (
            mobile_kill_counts.get(mobile.vnum, 0)
            if boot_kill_counts_by_mobile_vnum is not None
            else kill_counts.get(normalized_target, 0)
        )

        if mobile.non_corporeal:
            hazards.append("source mobile is non-corporeal")
            dangerous = True
            autonomy_rejections.append("source mobile is non-corporeal")

        # db.c checks the prototype-global count for every M reset. A local
        # reset with a smaller limit cannot bound spawns from other rooms.
        matching_target_capacity = prototype_population_limits[mobile.vnum]
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
                and not companion.attack_programs
            )
            companion_can_join = source_mobile_can_join_player_fight(
                world,
                companion,
                character_level=character_level,
                character_alignment=character_alignment,
            )
            companion_is_source_capable = source_mobile_can_join_player_fight(
                world,
                companion,
                character_level=character_level,
            )
            if (
                not companion_can_join
                and companion_is_source_capable
                and _source_mobile_has_combat_joining_special(
                    world,
                    companion.vnum,
                )
            ):
                hazards.append(
                    "source-backed good-alignment guard cannot join "
                    "positive-alignment player: "
                    f"{companion.short_description}"
                )
                continue
            companion_is_good_alignment_safe = (
                not companion_can_join
                and not companion.aggressive
                and not companion.attack_programs
                and set(companion_specials).issubset(
                    SAFE_NONCOMBAT_SPECIALS | TRANSIT_SAFE_COMBAT_ONLY_SPECIALS
                )
                and companion.alignment >= 350
                and _source_character_is_good_alignment(character_alignment)
            )
            if companion_is_good_alignment_safe:
                hazards.append(
                    "source-backed good-alignment companion cannot join "
                    "positive-alignment player: "
                    f"{companion.short_description}"
                )
                continue
            # A source-proven below-band mobile cannot make this useful-band
            # target an unsafe crowd.  This remains true when its special is
            # capable of a bounded nuisance effect; the field runner must
            # finish an unavoidable trivial interruption rather than flee.
            companion_is_trivial = companion_is_below_band or (
                not companion_can_join
                and not companion_specials
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
            # ``violence_update`` rejects a passive ordinary bystander more
            # than six levels above the player before it can join the fight.
            # Keep that source level window authoritative: only aggression,
            # specials, programs, or an actual source-capable join path make
            # this endpoint dangerous.
            if (
                companion.aggressive
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
            elif companion_can_join:
                dangerous = True
                hazards.append(
                    "source-backed companion may join player combat: "
                    f"{companion.short_description}"
                )
                autonomy_rejections.append(
                    "target room has a source-capable assisting companion"
                )
                autonomy_rejections.append(
                    "target room has a dangerous reset companion"
                )

        for path_room in path_rooms[:-1]:
            for path_reset in resets_by_room.get(path_room, ()):
                hazard = world.mobiles.get(path_reset.mobile_vnum)
                if hazard is None:
                    continue
                unsafe_special = _source_mobile_has_unsafe_special(
                    world,
                    hazard.vnum,
                    hazard,
                    character_level=character_level,
                )
                if not (
                    _source_mobile_is_combat_hazard(world, hazard)
                    or unsafe_special
                ):
                    continue
                route_hazard_mobile_vnums.add(hazard.vnum)
                if hazard.aggressive:
                    route_aggressive_mobile_vnums.add(hazard.vnum)
                if hazard.attack_programs:
                    route_attack_program_mobile_vnums.add(hazard.vnum)
                if unsafe_special:
                    route_special_mobile_vnums.add(hazard.vnum)
                # A combat-joining guard only reacts after a fight starts;
                # a mobile program can initiate combat on entry even when its
                # prototype is not flagged ACT_AGGRESSIVE.
                if (
                    not hazard.aggressive
                    and not hazard.attack_programs
                    and not unsafe_special
                ):
                    continue
                if _source_mobile_has_safe_noncombat_special(world, hazard.vnum):
                    hazards.append(
                        f"source-backed noncombat route special: "
                        f"{hazard.short_description}"
                    )
                    continue
                hazard_kind = (
                    "route program attacker"
                    if hazard.attack_programs
                    else "route"
                    if hazard.aggressive
                    else "route combat-joining special"
                )
                hazards.append(
                    f"{hazard_kind}: {hazard.short_description} "
                    f"L{hazard.level} in {path_room}"
                )
                if unsafe_special:
                    dangerous = True
                    autonomy_rejections.append(
                        "route crosses a non-safe special mobile"
                    )
                if (
                    hazard.attack_programs
                    and _source_mobile_has_deterministic_attack_program(hazard)
                ):
                    hazards.append(
                        "source-backed route attack program: "
                        f"{hazard.short_description}"
                    )
                    dangerous = True
                    autonomy_rejections.append(
                        "route crosses a program-triggered attacker"
                    )
                hazard_level_max = _mobile_level_range(hazard.level)[1]
                hazard_noun = (
                    "program-triggered attacker"
                    if hazard.attack_programs
                    else "aggressive reset"
                    if hazard.aggressive
                    else "combat-joining special"
                )
                hazard_article = (
                    "an" if hazard_noun.startswith("aggressive") else "a"
                )
                if hazard_level_max > character_level:
                    dangerous = True
                    autonomy_rejections.append(
                        f"route crosses a higher-level {hazard_noun}"
                    )
                elif (
                    hazard.attack_programs
                    and not hazard.aggressive
                    and hazard_level_max
                    <= character_level - _SOURCE_PROGRAM_PREFLIGHT_LEVEL_GAP
                ):
                    # A probabilistic, non-aggressive program such as the
                    # level-2 drunk is exactly what the source-backed `where`
                    # preflight handles. Its fuzzed upper bound may overlap
                    # the ordinary five-level XP floor, but the live locator
                    # lets the route avoid it before departure.
                    continue
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
                            f"route crosses {hazard_article} {hazard_noun} "
                            "inside the useful XP band"
                        )
                elif hazard.aggressive and hazard_level_max > (
                    character_level - _SOURCE_TRANSIT_AGGRESSOR_RISK_GAP
                ):
                    if source_mobile_route_aggressor_is_bounded(
                        world,
                        hazard,
                        character_level=character_level,
                        character_max_hp=character_max_hp,
                    ):
                        hazards.append(
                            "bounded low-risk aggressive transit mobile may be "
                            "finished once"
                        )
                    else:
                        autonomy_rejections.append(
                            "route crosses an aggressive transit attacker inside "
                            "the transit-risk band"
                        )
                elif (
                    path_reset.maximum_count
                    > _MAX_BELOW_BAND_ROUTE_AGGRESSOR_CAPACITY
                    and _source_aggressive_reset_can_reach_character(
                        world,
                        hazard,
                        character_level=character_level,
                    )
                ):
                    hazards.append(
                        "route crosses a large below-band "
                        f"{'aggressive' if hazard.aggressive else 'combat-joining'} reset "
                        f"(up to {path_reset.maximum_count} mobiles)"
                    )
                    dangerous = True
                    autonomy_rejections.append(
                        "route crosses a large below-band "
                        f"{'aggressive' if hazard.aggressive else 'combat-joining'} crowd"
                    )

        path_room_set = set(path_rooms)
        reachable_wanderers = set(endpoint_wanderers.get(path_rooms[-1], ()))
        for path_room in path_room_set:
            reachable_wanderers.update(transit_wanderers.get(path_room, ()))
        for index in sorted(reachable_wanderers):
            hazard, hazard_reset = wandering_aggressors[index]
            if _source_mobile_has_safe_noncombat_special(world, hazard.vnum):
                continue
            if (
                _source_mobile_has_combat_joining_special(world, hazard.vnum)
                and source_mobile_can_join_player_fight(
                    world,
                    hazard,
                    character_level=character_level,
                )
                and not source_mobile_can_join_player_fight(
                    world,
                    hazard,
                    character_level=character_level,
                    character_alignment=character_alignment,
                )
            ):
                hazards.append(
                    "source-backed good-alignment guard cannot join "
                    "positive-alignment player: "
                    f"{hazard.short_description}"
                )
                continue
            unsafe_special = _source_mobile_has_unsafe_special(
                world,
                hazard.vnum,
                hazard,
                character_level=character_level,
            )
            hazard_rooms = (
                path_room_set
                if hazard.aggressive or hazard.attack_programs or unsafe_special
                else {path_rooms[-1]}
            )
            if (
                hazard.vnum == mobile.vnum
                or hazard_reset.room_vnum in hazard_rooms
                or hazard_rooms.isdisjoint(
                    wanderer_reachability[
                        (hazard.vnum, hazard_reset.room_vnum)
                    ]
                )
            ):
                continue
            route_hazard_mobile_vnums.add(hazard.vnum)
            if hazard.aggressive:
                route_aggressive_mobile_vnums.add(hazard.vnum)
            if hazard.attack_programs:
                route_attack_program_mobile_vnums.add(hazard.vnum)
            if unsafe_special:
                route_special_mobile_vnums.add(hazard.vnum)
            hazard_kind = (
                "reachable program attacker"
                if hazard.attack_programs
                else "reachable wanderer"
                if hazard.aggressive
                else "reachable special mobile"
                if unsafe_special
                and not _source_mobile_has_combat_joining_special(
                    world,
                    hazard.vnum,
                )
                else "reachable combat-joining special"
            )
            hazards.append(
                f"{hazard_kind}: {hazard.short_description} L{hazard.level}"
            )
            hazard_level_max = _mobile_level_range(hazard.level)[1]
            hazard_noun = (
                "program-triggered attacker"
                if hazard.attack_programs
                else "aggressive wanderer"
                if hazard.aggressive
                else "combat-joining special"
            )
            hazard_article = (
                "an" if hazard_noun.startswith("aggressive") else "a"
            )
            if unsafe_special:
                dangerous = True
                autonomy_rejections.append(
                    "a non-safe special mobile can reach the route"
                )
            if (
                hazard.attack_programs
                and _source_mobile_has_deterministic_attack_program(hazard)
            ):
                dangerous = True
                autonomy_rejections.append(
                    "route crosses a program-triggered attacker"
                )
            if hazard_level_max > character_level:
                dangerous = True
                autonomy_rejections.append(
                    f"a higher-level {hazard_noun} can reach the route"
                )
            elif (
                hazard.aggressive
                and hazard_level_max
                > character_level - _SOURCE_TRANSIT_AGGRESSOR_RISK_GAP
            ):
                if source_mobile_route_aggressor_is_bounded(
                    world,
                    hazard,
                    character_level=character_level,
                    character_max_hp=character_max_hp,
                ):
                    hazards.append(
                        "bounded low-risk aggressive wanderer may be finished once"
                    )
                else:
                    autonomy_rejections.append(
                        "an aggressive wanderer inside the transit-risk band "
                        "can reach the route"
                    )
            elif (
                hazard.attack_programs
                and not hazard.aggressive
                and hazard_level_max
                <= character_level - _SOURCE_PROGRAM_PREFLIGHT_LEVEL_GAP
            ):
                # Keep the same two-level source-fuzz admission rule for a
                # wandering program attacker. The exact `where` result is
                # still required before the live route can start.
                pass
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
                        f"{hazard_article} {hazard_noun} inside the useful XP band "
                        "can reach the route"
                    )

        # A single far-below-band probabilistic greet program can be checked
        # once from the recall origin. Preserve the exact source identity and
        # room map so the live starter can issue ``where`` before crossing the
        # route; deterministic or multi-program routes remain ordinary hazards.
        if (
            route_preflight_room_vnum is None
            and len(route_attack_program_mobile_vnums) == 1
        ):
            program_mobile = world.mobiles.get(
                next(iter(route_attack_program_mobile_vnums))
            )
            if (
                program_mobile is not None
                and program_mobile.attack_programs
                and not _source_mobile_has_deterministic_attack_program(
                    program_mobile
                )
                and _mobile_level_range(program_mobile.level)[1]
                <= character_level - _SOURCE_PROGRAM_PREFLIGHT_LEVEL_GAP
            ):
                route_preflight_room_vnum = str(route_origin_room_vnum)
                route_preflight_command = (
                    f"where {_source_mobile_where_keyword(program_mobile)}"
                )
                route_preflight_target = program_mobile.short_description
                route_preflight_level_range = _mobile_level_range(
                    program_mobile.level
                )
                route_preflight_hard_hazard = True
                route_preflight_route_room_names = _source_route_room_names(
                    world,
                    path_rooms,
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
            # Aggressive mobiles can enter combat as soon as their reset room
            # loads, before live consider can reject a below-band fuzzy load.
            # Mark that case as a hard pre-entry rejection.  This must happen
            # here, before bounded capacity or other research pools can treat
            # the same target as probeable.
            if level_range[0] < character_level - 5:
                dangerous = True
                autonomy_rejections.append("target is aggressive")
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
        combat_readiness, combat_readiness_bonus = source_combat_readiness(
            character_level=character_level,
            character_class=character_class,
            character_subclass=character_subclass,
            known_skills=known_skills,
            known_skill_levels=known_skill_levels,
            target_level_range=level_range,
            equipped_weapon_count=len(equipped_weapons),
            character_max_hp=character_max_hp,
            peak_round_damage=peak_round_damage,
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
            + combat_readiness_bonus
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
                source_spawn_limit=matching_target_capacity,
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
                rank=mobile.rank,
                equipped_weapons=tuple(
                    item.short_description for item in equipped_weapons
                ),
                target_body_form_flags=mobile.body_form_flags,
                estimated_level_range=level_range,
                estimated_base_hp_range=hp_range,
                estimated_peak_round_damage=peak_round_damage,
                estimated_min_peak_round_damage=minimum_peak_round_damage,
                estimated_critical_hit_damage=critical_hit_damage,
                autonomy_rejections=tuple(dict.fromkeys(autonomy_rejections)),
                combat_readiness=combat_readiness,
                combat_readiness_bonus=combat_readiness_bonus,
                specials=world.mobile_specials.get(mobile.vnum, ()),
                route_preflight_room_vnum=route_preflight_room_vnum,
                route_preflight_command=route_preflight_command,
                route_preflight_target=route_preflight_target,
                route_preflight_level_range=route_preflight_level_range,
                route_preflight_hard_hazard=route_preflight_hard_hazard,
                route_preflight_route_room_names=route_preflight_route_room_names,
                route_hard_hazard_targets=route_hard_hazard_targets,
                route_hazard_mobile_vnums=tuple(sorted(route_hazard_mobile_vnums)),
                route_aggressive_mobile_vnums=tuple(
                    sorted(route_aggressive_mobile_vnums)
                ),
                route_attack_program_mobile_vnums=tuple(
                    sorted(route_attack_program_mobile_vnums)
                ),
                route_special_mobile_vnums=tuple(sorted(route_special_mobile_vnums)),
                undead=mobile.undead,
                sentinel=mobile.sentinel,
                stay_area=mobile.stay_area,
                estimated_move_cost=estimated_move_cost,
                estimated_flying_move_cost=estimated_flying_move_cost,
                requires_flight=requires_flight,
                route_origin_recall_index=route_origin_recall_index,
                route_origin_room_vnum=route_origin_room_vnum,
                source_damage_modifier=mobile.damage_modifier,
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


def _parse_mobile_rank(
    lines: list[str],
    start: int,
    end: int,
) -> str:
    """Parse the rank from the optional ``< mobspec~ rank~`` record."""
    for line in lines[start:end]:
        match = _MOBILE_TEMPLATE.match(line)
        if match is None:
            continue
        rank = " ".join(match.group("rank").casefold().split())
        return rank or "common"
    return "common"


def _parse_mobile_template_name(
    lines: list[str],
    start: int,
    end: int,
) -> str | None:
    """Parse the body-species/archetype name from a template record."""
    for line in lines[start:end]:
        match = _MOBILE_TEMPLATE.match(line)
        if match is None:
            continue
        template = " ".join(match.group("template").casefold().split())
        return template or None
    return None


def _parse_mobile_hp_modifier(
    lines: list[str],
    start: int,
    end: int,
) -> int | None:
    """Parse DD4's optional per-mobile ``MobHPMod`` scalar."""
    modifier: int | None = None
    found = False
    for line in lines[start:end]:
        parts = line.split()
        if not parts or parts[0].casefold() != "mobhpmod":
            continue
        found = True
        if len(parts) != 2:
            raise ValueError("MobHPMod requires one signed percentage value")
        value = parts[1]
        if value.casefold() == "inherit":
            modifier = None
            continue
        if not re.fullmatch(r"[+-]?\d+", value):
            raise ValueError(f"invalid MobHPMod value: {value}")
        modifier = int(value)
        if not MOBILE_HP_MOD_MIN <= modifier <= (1 << 31) - 1:
            raise ValueError(f"MobHPMod is outside the source range: {value}")
    return modifier if found else None


def _parse_mobile_damage_modifier(
    lines: list[str],
    start: int,
    end: int,
) -> int | None:
    """Parse DD4's optional per-mobile ``MobDamMod`` scalar."""
    modifier: int | None = None
    found = False
    for line in lines[start:end]:
        parts = line.split()
        if not parts or parts[0].casefold() != "mobdammod":
            continue
        found = True
        if len(parts) != 2:
            raise ValueError("MobDamMod requires one signed percentage value")
        value = parts[1]
        if value.casefold() == "inherit":
            modifier = None
            continue
        if not re.fullmatch(r"[+-]?\d+", value):
            raise ValueError(f"invalid MobDamMod value: {value}")
        modifier = int(value)
        if not MOBILE_DAMAGE_MOD_MIN <= modifier <= (1 << 31) - 1:
            raise ValueError(f"MobDamMod is outside the source range: {value}")
    return modifier if found else None


def _resolve_template_scalar(
    species_value: int | None,
    archetype_value: int | None,
) -> int:
    """Mirror DD4's explicit archetype, species, then neutral resolution."""
    if archetype_value is not None and archetype_value != MOBILE_TEMPLATE_UNSET:
        return archetype_value
    if species_value is not None and species_value != MOBILE_TEMPLATE_UNSET:
        return species_value
    return 0


def _parse_mobiles(
    lines: list[str],
    bounds: tuple[int, int] | None,
    area_file: str,
    *,
    mobile_templates: Mapping[str, MobileTemplateSource] | None = None,
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
        body_form_flags: int | None = None
        if index < record_end:
            body_parts = lines[index].split()
            if body_parts:
                try:
                    body_form_flags = _parse_bits(body_parts[0])
                except ValueError:
                    # Keep malformed or legacy records usable, but do not
                    # invent anatomy evidence for them.
                    body_form_flags = None
        area_act_flags = _parse_bits(flag_parts[0])
        area_affected_flags = _parse_bits(flag_parts[1])
        area_body_form_flags = body_form_flags
        template_name = _parse_mobile_template_name(lines, index, record_end)
        template = (
            mobile_templates.get(template_name)
            if mobile_templates is not None and template_name is not None
            else None
        )
        template_act_flags = template.act_flags if template is not None else 0
        template_affected_flags = (
            template.affected_flags if template is not None else 0
        )
        template_body_form_flags = (
            template.body_form_flags if template is not None else 0
        )
        template_hp_modifier = (
            template.hp_modifier if template is not None else 0
        )
        area_hp_modifier = _parse_mobile_hp_modifier(
            lines,
            index,
            record_end,
        )
        hp_modifier_known = (
            template_name is None
            or template is not None
            or area_hp_modifier is not None
        )
        template_damage_modifier = (
            template.damage_modifier if template is not None else 0
        )
        area_damage_modifier = _parse_mobile_damage_modifier(
            lines,
            index,
            record_end,
        )
        damage_modifier_known = (
            template_name is None
            or template is not None
            or area_damage_modifier is not None
        )
        effective_body_form_flags = (
            None
            if body_form_flags is None
            else body_form_flags ^ template_body_form_flags
        )
        mobiles[vnum] = MobileSource(
            vnum=vnum,
            keywords=_clean_text(keywords),
            short_description=_clean_text(short_description),
            level=int(combat_parts[0]),
            act_flags=area_act_flags ^ template_act_flags,
            alignment=int(flag_parts[2]),
            area_file=area_file,
            room_description=_clean_text(room_description),
            affected_flags=area_affected_flags ^ template_affected_flags,
            programs=_parse_mobile_programs(lines, index, record_end),
            teachings=_parse_mobile_teachings(lines, index, record_end),
            body_form_flags=effective_body_form_flags,
            rank=_parse_mobile_rank(lines, index, record_end),
            template_name=template_name,
            template_species=template.species if template is not None else None,
            template_act_flags=template_act_flags,
            template_affected_flags=template_affected_flags,
            template_body_form_flags=template_body_form_flags,
            xp_modifier=template.xp_modifier if template is not None else 0,
            area_act_flags=area_act_flags,
            area_affected_flags=area_affected_flags,
            area_body_form_flags=area_body_form_flags,
            template_hp_modifier=template_hp_modifier,
            area_hp_modifier=area_hp_modifier,
            hp_modifier=(
                (
                    area_hp_modifier
                    if area_hp_modifier is not None
                    else template_hp_modifier
                )
                if hp_modifier_known
                else None
            ),
            hp_modifier_known=hp_modifier_known,
            template_damage_modifier=template_damage_modifier,
            area_damage_modifier=area_damage_modifier,
            damage_modifier=(
                (
                    area_damage_modifier
                    if area_damage_modifier is not None
                    else template_damage_modifier
                )
                if damage_modifier_known
                else None
            ),
            damage_modifier_known=damage_modifier_known,
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
                    _source_exit_flags_for_lock_type(int(exit_parts[0])),
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
    *,
    mobiles: Mapping[int, MobileSource] | None = None,
    mobile_templates: Mapping[str, MobileTemplateSource] | None = None,
) -> dict[int, tuple[str, ...]]:
    if bounds is None:
        index, end = 0, 0
    else:
        index, end = bounds
    missing = object()
    name_overrides: dict[int, list[object]] = {}
    chance_overrides: dict[int, tuple[int, ...]] = {}

    def names_for(vnum: int) -> list[object]:
        return name_overrides.setdefault(
            vnum,
            [missing] * MOBILE_SPECIAL_SLOTS,
        )

    def parse_name(value: str) -> str | None | object:
        normalized = value.casefold()
        if normalized == "inherit":
            return missing
        if normalized == "none":
            return ""
        return value

    while index < end:
        parts = lines[index].split()
        index += 1
        if len(parts) < 2 or parts[0] not in {"M", "N", "P"}:
            continue
        if not _all_ints(parts[1:2]):
            continue
        vnum = int(parts[1])
        if parts[0] == "M":
            if len(parts) < 3:
                continue
            name = parse_name(parts[2])
            overrides = names_for(vnum)
            if name is missing:
                overrides[:] = [missing] * MOBILE_SPECIAL_SLOTS
                chance_overrides.pop(vnum, None)
            elif name == "":
                overrides[:] = [""] * MOBILE_SPECIAL_SLOTS
                chance_overrides[vnum] = (0,) * MOBILE_SPECIAL_SLOTS
            else:
                overrides[:] = [name, "", ""]
                chance_overrides[vnum] = (100, 0, 0)
            continue
        if parts[0] == "N":
            if len(parts) < 4 or not _all_ints(parts[2:3]):
                continue
            slot = int(parts[2])
            if not 1 <= slot <= MOBILE_SPECIAL_SLOTS:
                continue
            names_for(vnum)[slot - 1] = parse_name(parts[3])
            continue
        if len(parts) < 3:
            continue
        policy = _parse_c_special_chances(
            "{ " + ", ".join(parts[2:]) + " }",
            {},
            default=(MOBILE_SPECIAL_AUTO,) * MOBILE_SPECIAL_SLOTS,
        )
        # The source treats an all-word ``inherit`` policy as template
        # inheritance; ``auto`` is an explicit automatic distribution.
        if parts[2].casefold() == "inherit":
            chance_overrides.pop(vnum, None)
        else:
            chance_overrides[vnum] = policy

    resolved: dict[int, tuple[str, ...]] = {}
    source_mobiles = mobiles or {}
    for vnum, mobile in source_mobiles.items():
        template = (
            mobile_templates.get(mobile.template_name)
            if mobile_templates is not None and mobile.template_name is not None
            else None
        )
        names = list(
            template.special_names
            if template is not None
            else (None,) * MOBILE_SPECIAL_SLOTS
        )
        chances = (
            template.special_chances
            if template is not None
            else (MOBILE_SPECIAL_AUTO,) * MOBILE_SPECIAL_SLOTS
        )
        overrides = name_overrides.get(vnum)
        if overrides is not None:
            for slot, value in enumerate(overrides):
                if value is not missing:
                    names[slot] = value  # type: ignore[assignment]
        if vnum in chance_overrides:
            chances = chance_overrides[vnum]
        effective = _effective_mobile_special_names(names, chances)
        if effective:
            resolved[vnum] = effective
    return resolved


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
    require_no_combat_hazards: bool = False,
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
            if mobile is None or not (
                _source_mobile_is_combat_hazard(world, mobile)
                or _source_mobile_has_unsafe_special(
                    world,
                    mobile.vnum,
                    mobile,
                    character_level=character_level,
                )
            ):
                continue
            if _source_mobile_has_safe_noncombat_special(world, mobile.vnum):
                continue
            unsafe_special = _source_mobile_has_unsafe_special(
                world,
                mobile.vnum,
                mobile,
                character_level=character_level,
            )
            if require_no_combat_hazards and (
                mobile.attack_programs
                or unsafe_special
                or _source_mobile_has_combat_joining_special(
                    world,
                    mobile.vnum,
                )
                or (
                    mobile.aggressive
                    and _source_aggressive_reset_can_reach_character(
                        world,
                        mobile,
                        character_level=character_level,
                    )
                )
            ):
                blocked.add(room_vnum)
                break
            if unsafe_special:
                # A non-safe special can start combat or apply an unmodeled
                # effect before a live target check. Plain aggressive mobiles
                # still follow DD4's cutoff and the existing
                # useful-band/crowd gates below.
                blocked.add(room_vnum)
                break
            level_max = _mobile_level_range(mobile.level)[1]
            if (
                (
                    mobile.aggressive
                    and level_max > character_level - _SOURCE_TRANSIT_AGGRESSOR_RISK_GAP
                )
                or (
                    not mobile.aggressive
                    and level_max > character_level - 5
                )
                or mobile.attack_programs
                or (
                    reset.maximum_count
                    > _MAX_BELOW_BAND_ROUTE_AGGRESSOR_CAPACITY
                    and _source_aggressive_reset_can_reach_character(
                        world,
                        mobile,
                        character_level=character_level,
                    )
                )
            ):
                blocked.add(room_vnum)
                break
    if require_no_combat_hazards:
        # A wandering aggressor is a route hazard throughout the rooms that
        # DD4's update.c movement rules allow it to reach, not only at its
        # reset room. Keep strict resource-recovery routes out of that entire
        # source-reachable set.
        for mobile, reset in _wandering_aggressors(world):
            if _source_mobile_has_safe_noncombat_special(world, mobile.vnum):
                continue
            if not (
                mobile.attack_programs
                or _source_mobile_has_unsafe_special(
                    world,
                    mobile.vnum,
                    mobile,
                    character_level=character_level,
                )
                or _source_mobile_has_combat_joining_special(
                    world,
                    mobile.vnum,
                )
                or (
                    mobile.aggressive
                    and _source_aggressive_reset_can_reach_character(
                        world,
                        mobile,
                        character_level=character_level,
                    )
                )
            ):
                continue
            blocked.update(
                _wanderer_reachable_rooms(world, mobile, reset.room_vnum)
            )
    return blocked


def _source_route_hazard_rejections(
    world: WorldSource,
    path_rooms: Collection[int],
    *,
    character_level: int,
    require_no_combat_hazards: bool = False,
    combat_at_destination: bool = True,
    invisible: bool = False,
) -> tuple[str, ...]:
    """Return source-backed combat hazards on a route, including its endpoint.

    Ordinary hunt candidates already perform this analysis while ranking a
    mobile. Retrieve and hoard quests have no mobile target to rank, so they
    need the same fixed-room and reachable-wanderer checks before walking to
    an object.
    """
    if character_level < 1:
        raise ValueError("character_level must be at least 1")
    path_room_sequence = tuple(path_rooms)
    path_room_set = set(path_room_sequence)
    target_room_vnum = (
        path_room_sequence[-1] if path_room_sequence and combat_at_destination else None
    )
    resets_by_room = _resets_by_room(world)
    rejections: list[str] = []
    for room_vnum in path_room_sequence[1:]:
        access_rejection = source_room_level_rejection(
            world.rooms.get(room_vnum),
            character_level,
        )
        if access_rejection is not None:
            rejections.append(
                f"route crosses an inaccessible source area in room {room_vnum}: "
                f"{access_rejection}"
            )
    for room_vnum in path_room_set:
        for reset in resets_by_room.get(room_vnum, ()):
            mobile = world.mobiles.get(reset.mobile_vnum)
            if mobile is None or _source_mobile_has_safe_noncombat_special(
                world,
                mobile.vnum,
            ):
                continue
            if (
                invisible
                and not combat_at_destination
                and source_invisibility_blocks_mobile_aggression(
                    world,
                    mobile.vnum,
                )
            ):
                continue
            unsafe_special = _source_mobile_has_unsafe_special(
                world,
                mobile.vnum,
                mobile,
                character_level=character_level,
            )
            if require_no_combat_hazards and (
                mobile.attack_programs
                or unsafe_special
                or _source_mobile_has_combat_joining_special(
                    world,
                    mobile.vnum,
                )
                or (
                    mobile.aggressive
                    and _source_aggressive_reset_can_reach_character(
                        world,
                        mobile,
                        character_level=character_level,
                    )
                )
            ):
                rejections.append(
                    "strict route crosses source combat hazard: "
                    f"{mobile.short_description} in room {room_vnum}"
                )
                continue
            if unsafe_special:
                rejections.append(
                    "route crosses a non-safe special mobile: "
                    f"{mobile.short_description} in room {room_vnum}"
                )
                continue
            if mobile.attack_programs:
                rejections.append(
                    "route includes program-triggered attacker: "
                    f"{mobile.short_description} in room {room_vnum}"
                )
            if not _source_mobile_is_combat_hazard(world, mobile):
                continue
            if not mobile.aggressive and room_vnum != target_room_vnum:
                continue
            maximum_level = _mobile_level_range(mobile.level)[1]
            hazard_noun = (
                "aggressive reset"
                if mobile.aggressive
                else "combat-joining special"
            )
            hazard_article = "an" if mobile.aggressive else "a"
            if maximum_level > character_level:
                rejections.append(
                    f"route crosses a higher-level {hazard_noun}: "
                    f"{mobile.short_description} in room {room_vnum}"
                )
            elif mobile.aggressive and maximum_level > (
                character_level - _SOURCE_TRANSIT_AGGRESSOR_RISK_GAP
            ):
                rejections.append(
                    "route crosses an aggressive transit attacker inside the "
                    "transit-risk band: "
                    f"{mobile.short_description} in room {room_vnum}"
                )
            elif maximum_level > character_level - 5:
                rejections.append(
                    f"route crosses {hazard_article} {hazard_noun} inside the useful "
                    f"XP band: {mobile.short_description} in room {room_vnum}"
                )
            elif reset.maximum_count > _MAX_BELOW_BAND_ROUTE_AGGRESSOR_CAPACITY:
                rejections.append(
                    "route crosses a large below-band "
                    f"{'aggressive' if mobile.aggressive else 'combat-joining'} crowd: "
                    f"{mobile.short_description} in room {room_vnum}"
                )

    for mobile, reset in _wandering_aggressors(world):
        if _source_mobile_has_safe_noncombat_special(world, mobile.vnum):
            continue
        if (
            invisible
            and not combat_at_destination
            and source_invisibility_blocks_mobile_aggression(
                world,
                mobile.vnum,
            )
        ):
            continue
        unsafe_special = _source_mobile_has_unsafe_special(
            world,
            mobile.vnum,
            mobile,
            character_level=character_level,
        )
        hazard_rooms = (
            path_room_set
            if mobile.aggressive or mobile.attack_programs or unsafe_special
            else ({target_room_vnum} if target_room_vnum is not None else set())
        )
        if reset.room_vnum in hazard_rooms:
            continue
        reachable = set(
            _wanderer_reachable_rooms(world, mobile, reset.room_vnum)
        )
        if hazard_rooms.isdisjoint(reachable):
            continue
        maximum_level = _mobile_level_range(mobile.level)[1]
        if require_no_combat_hazards and (
            mobile.attack_programs
            or unsafe_special
            or _source_mobile_has_combat_joining_special(
                world,
                mobile.vnum,
            )
            or (
                mobile.aggressive
                and _source_aggressive_reset_can_reach_character(
                    world,
                    mobile,
                    character_level=character_level,
                )
            )
        ):
            rejections.append(
                "strict route crosses source-reachable combat hazard: "
                f"{mobile.short_description} from room {reset.room_vnum}"
            )
            continue
        if unsafe_special:
            rejections.append(
                "a non-safe special mobile can reach the route: "
                f"{mobile.short_description}"
            )
            continue
        if (
            mobile.attack_programs
            and _source_mobile_has_deterministic_attack_program(mobile)
        ):
            rejections.append(
                "a program-triggered attacker can reach the route: "
                f"{mobile.short_description}"
            )
        hazard_noun = (
            "program-triggered attacker"
            if mobile.attack_programs
            else "aggressive wanderer"
            if mobile.aggressive
            else "combat-joining special"
        )
        hazard_article = (
            "an" if hazard_noun.startswith("aggressive") else "a"
        )
        maximum_level = _mobile_level_range(mobile.level)[1]
        if maximum_level > character_level:
            rejections.append(
                f"a higher-level {hazard_noun} can reach the route: "
                f"{mobile.short_description}"
            )
        elif maximum_level > character_level - 5:
            rejections.append(
                f"{hazard_article} {hazard_noun} inside the useful XP band can reach "
                f"the route: {mobile.short_description}"
            )
    return tuple(dict.fromkeys(rejections))


def source_safe_route_to_room_with_origin(
    world: WorldSource,
    room_vnum: int,
    *,
    character_level: int,
    recall_origins: Mapping[int, int] | None = None,
    require_no_combat_hazards: bool = False,
) -> tuple[tuple[str, ...], tuple[int, ...], int, int, int] | None:
    """Return a source-safe route and its observed recall origin.

    Quest destinations are normally planned from Midgaard recall.  Once a
    live ``recall list`` has established another destination, that point is a
    valid route origin too.  The caller still controls which origins are
    trusted; an omitted mapping deliberately means default recall only.
    """
    return _source_safe_route_to_room_from_origins(
        world,
        room_vnum,
        character_level=character_level,
        recall_origins=recall_origins,
        require_no_combat_hazards=require_no_combat_hazards,
    )


def _source_safe_route_to_room_from_origins(
    world: WorldSource,
    room_vnum: int,
    *,
    character_level: int,
    recall_origins: Mapping[int, int] | None,
    require_no_combat_hazards: bool,
) -> tuple[tuple[str, ...], tuple[int, ...], int, int, int] | None:
    """Return the best source-safe route from the supplied recall points."""
    recall_origin_rooms: dict[int, int] = {0: RECALL_VNUM}
    for raw_index, raw_room_vnum in (recall_origins or {}).items():
        try:
            index = int(raw_index)
            origin_room_vnum = int(raw_room_vnum)
        except (TypeError, ValueError):
            continue
        if index < 0 or origin_room_vnum not in world.rooms:
            continue
        recall_origin_rooms[index] = origin_room_vnum

    resets_by_room = _resets_by_room(world)
    blocked_rooms = _route_hazard_rooms(
        world,
        resets_by_room,
        character_level=character_level,
        require_no_combat_hazards=require_no_combat_hazards,
    ) - {room_vnum}
    choices: list[
        tuple[
            tuple[int, int, int, int],
            tuple[tuple[str, ...], tuple[int, ...], int],
            int,
            int,
        ]
    ] = []
    for index, origin_room_vnum in recall_origin_rooms.items():
        direct = _shortest_paths_from(world.rooms, origin_room_vnum).get(
            room_vnum
        )
        if direct is None:
            continue
        safe = _shortest_paths_from(
            world.rooms,
            origin_room_vnum,
            blocked_rooms=blocked_rooms,
        ).get(room_vnum)
        selected = direct
        if (
            safe is not None
            and len(safe[0])
            <= len(direct[0]) + _MAX_SOURCE_ROUTE_DETOUR_STEPS
        ):
            selected = safe
        if _source_route_hazard_rejections(
            world,
            selected[1],
            character_level=character_level,
            require_no_combat_hazards=require_no_combat_hazards,
        ):
            continue
        choices.append(
            (
                (len(selected[0]), selected[2], index, origin_room_vnum),
                selected,
                index,
                origin_room_vnum,
            )
        )
    if not choices:
        return None
    _, selected, index, origin_room_vnum = min(
        choices,
        key=lambda item: item[0],
    )
    return (*selected, index, origin_room_vnum)


def source_safe_route_to_room(
    world: WorldSource,
    room_vnum: int,
    *,
    character_level: int,
    require_no_combat_hazards: bool = False,
) -> tuple[tuple[str, ...], tuple[int, ...], int] | None:
    """Return a source-safe route to a quest object room, if one exists."""
    selected = source_safe_route_to_room_with_origin(
        world,
        room_vnum,
        character_level=character_level,
        require_no_combat_hazards=require_no_combat_hazards,
    )
    if selected is None:
        return None
    commands, path_rooms, closed_doors, _, _ = selected
    return commands, path_rooms, closed_doors


def source_route_hazard_rejections(
    world: WorldSource,
    path_rooms: Collection[int],
    *,
    character_level: int,
    require_no_combat_hazards: bool = False,
    combat_at_destination: bool = True,
    invisible: bool = False,
) -> tuple[str, ...]:
    """Check a room path; noncombat endpoints omit only combat-only joiners."""
    return _source_route_hazard_rejections(
        world,
        path_rooms,
        character_level=character_level,
        require_no_combat_hazards=require_no_combat_hazards,
        combat_at_destination=combat_at_destination,
        invisible=invisible,
    )


def source_invisibility_blocks_mobile_aggression(
    world: WorldSource,
    mobile_vnum: int,
) -> bool:
    """Return whether source-proven invisibility prevents route combat.

    DD4's ordinary aggression calls ``can_see`` before attacking. Keep this
    admission narrow: the mobile must have no detect-invisibility affect,
    executable program, equipped reset object, or special that can act before
    combat. Combat-only specials such as ``spec_poison`` remain inert while
    the invisible character is not fighting.
    """
    mobile = world.mobiles.get(mobile_vnum)
    if (
        mobile is None
        or not mobile.aggressive
        or mobile.affected_flags & AFF_DETECT_INVIS
        or _mobile_level_range(mobile.level)[1] > 100
        or mobile.programs
    ):
        return False
    resets = [
        reset for reset in world.mob_resets
        if reset.mobile_vnum == mobile_vnum
    ]
    if not resets or any(reset.equipment for reset in resets):
        return False
    permitted_specials = (
        SAFE_NONCOMBAT_SPECIALS | TRANSIT_SAFE_COMBAT_ONLY_SPECIALS
    )
    return all(
        str(special).strip().casefold() in permitted_specials
        for special in world.mobile_specials.get(mobile_vnum, ())
    )


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


def _source_mobile_has_unsafe_special(
    world: WorldSource,
    mobile_vnum: int,
    mobile: MobileSource | None = None,
    *,
    character_level: int | None = None,
) -> bool:
    """Return whether a source special can affect an ordinary traveler.

    Combat-only and combat-joining procedures are handled by the normal
    aggression, target-room, and wandering-mobile gates. An aggressive mobile
    carrying a combat-only procedure remains hazardous only while DD4's normal
    ten-level aggression check can start the fight. A source procedure that can
    act before combat, an economic theft risk, or an unknown procedure remains
    a direct transit hazard at every level.
    """
    specials = tuple(world.mobile_specials.get(mobile_vnum, ()))
    if not specials:
        return False
    if any(not source_special_is_transit_safe(special) for special in specials):
        return True
    aggressive_combat_only = bool(
        mobile is not None
        and mobile.aggressive
        and any(
            str(special).strip().casefold()
            in TRANSIT_SAFE_COMBAT_ONLY_SPECIALS
            for special in specials
        )
    )
    if not aggressive_combat_only:
        return False
    if character_level is None:
        return True
    return character_level <= _mobile_level_range(mobile.level)[1] + 10


def _source_mobile_has_combat_joining_special(
    world: WorldSource,
    mobile_vnum: int,
) -> bool:
    """Return whether source special code can join another mobile's fight."""
    return any(
        str(special).strip().casefold() in COMBAT_JOINING_SPECIALS
        for special in world.mobile_specials.get(mobile_vnum, ())
    )


def source_mobile_can_join_target_fight(
    world: WorldSource,
    mobile: MobileSource,
    target: MobileSource,
    *,
    character_level: int | None = None,
    character_alignment: int | None = None,
) -> bool:
    """Compatibility wrapper for the player-fight source gate.

    The field runner's target is an NPC, but DD4's ``violence_update`` branch
    tests the alignment of the *player* being attacked. The NPC target's
    alignment is relevant only to a separate NPC-versus-NPC guard-special
    path, so it must not make a field companion look harmless.
    """
    return source_mobile_can_join_player_fight(
        world,
        mobile,
        character_level=character_level,
        character_alignment=character_alignment,
    )


def _source_mobile_is_combat_hazard(
    world: WorldSource,
    mobile: MobileSource,
) -> bool:
    """Return whether a source mobile can add combat before being attacked.

    A mobile program can initiate combat even when the prototype is not
    flagged ``ACT_AGGRESSIVE``. DD4's greet programs use ``mpkill`` for this
    exact purpose, so keep those mobiles in the same route-hazard set.
    """
    return bool(mobile.attack_programs) or mobile.aggressive or (
        _source_mobile_has_combat_joining_special(world, mobile.vnum)
    )


def _source_aggressive_reset_can_reach_character(
    world: WorldSource,
    mobile: MobileSource,
    *,
    character_level: int,
) -> bool:
    """Mirror DD4's level cutoff for an aggressive mobile's attack pass.

    ``update.c`` skips an aggressive mobile when the player is more than ten
    levels above it. Use the highest possible fuzzy mobile level so a route
    is reopened only when every source-backed load is harmless by that rule.
    Mobile programs and source procedures that can initiate travel combat are
    separate source behavior and remain route hazards regardless of the level
    cutoff. Combat-only specials still follow the normal aggression cutoff.
    """
    if not mobile.aggressive:
        return False
    if mobile.attack_programs:
        return True
    if world.mobile_specials.get(mobile.vnum) and _source_mobile_has_unsafe_special(
        world,
        mobile.vnum,
        mobile,
        character_level=character_level,
    ):
        return True
    return character_level <= _mobile_level_range(mobile.level)[1] + 10


def _shortest_paths_from(
    rooms: Mapping[int, RoomSource],
    origin: int,
    *,
    blocked_rooms: set[int] | frozenset[int] = frozenset(),
    unlockable_key_vnums: Collection[int] = (),
) -> dict[int, tuple[tuple[str, ...], tuple[int, ...], int]]:
    if origin not in rooms:
        return {}
    key_vnums = {int(vnum) for vnum in unlockable_key_vnums}
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
                or (
                    exit_source.closed
                    and exit_source.locked
                    and exit_source.key_vnum not in key_vnums
                )
            ):
                continue
            door_cost = 1 if exit_source.closed else 0
            random_cost = 20 if room.random_exits else 0
            next_cost = cost + 1 + door_cost + random_cost
            if next_cost >= best_cost.get(exit_source.destination, 1_000_000):
                continue
            best_cost[exit_source.destination] = next_cost
            next_commands = commands
            if exit_source.closed and exit_source.locked:
                next_commands += (f"unlock {direction}",)
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


def _shortest_source_analysis_path(
    rooms: Mapping[int, RoomSource],
    origin: int,
    target: int,
) -> tuple[tuple[str, ...], tuple[int, ...], int, tuple[int, ...]] | None:
    """Find a source-analysis route while recording locked-door keys.

    This helper deliberately differs from the executable route planner:
    locked doors are traversable only on paper, and the returned route is
    never passed to campaign dispatch. It exists so reports can explain why a
    source placement is ``source-only`` instead of silently showing no path.
    """
    if origin not in rooms or target not in rooms:
        return None
    queue: list[
        tuple[
            int,
            int,
            tuple[str, ...],
            tuple[int, ...],
            int,
            tuple[int, ...],
        ]
    ] = [(0, origin, (), (origin,), 0, ())]
    best_cost = {origin: 0}
    while queue:
        cost, room_vnum, commands, visited_rooms, closed_doors, required_keys = (
            heapq.heappop(queue)
        )
        if cost != best_cost.get(room_vnum):
            continue
        if room_vnum == target:
            return commands, visited_rooms, closed_doors, required_keys
        room = rooms[room_vnum]
        for direction, exit_source in sorted(room.exits.items()):
            if exit_source.destination not in rooms:
                continue
            door_cost = 1 if exit_source.closed else 0
            random_cost = 20 if room.random_exits else 0
            next_cost = cost + 1 + door_cost + random_cost
            if next_cost >= best_cost.get(exit_source.destination, 1_000_000):
                continue
            next_commands = commands
            next_keys = required_keys
            if exit_source.closed and exit_source.locked:
                if exit_source.key_vnum > 0:
                    next_commands += (f"unlock {direction}",)
                    next_keys = tuple(
                        dict.fromkeys((*required_keys, exit_source.key_vnum))
                    )
            if exit_source.closed:
                next_commands += (f"open {direction}",)
            next_commands += (direction,)
            best_cost[exit_source.destination] = next_cost
            heapq.heappush(
                queue,
                (
                    next_cost,
                    exit_source.destination,
                    next_commands,
                    visited_rooms + (exit_source.destination,),
                    closed_doors + door_cost,
                    next_keys,
                ),
            )
    return None


def _source_key_carriers(
    world: WorldSource,
    key_object_vnums: Collection[int],
) -> tuple[int, ...]:
    """Return source mobile VNUMs that reset with any required route key."""
    return tuple(
        sorted(
            {
                reset.mobile_vnum
                for reset in _source_key_carrier_resets(
                    world,
                    key_object_vnums,
                )
            }
        )
    )


def _source_route_key_acquisition_rejections(
    world: WorldSource,
    key_object_vnums: Collection[int],
    *,
    directly_reachable_rooms: Collection[int],
) -> tuple[str, ...]:
    """Explain route keys whose source placements are themselves unreachable.

    A source-analysis path can cross a locked door even when the only reset
    entries for that door's key are on the far side of the same door. Such a
    route is useful evidence, but it is not an acquisition plan. Record the
    circular dependency explicitly so resource selectors cannot mistake it
    for an ordinary missing live observation.
    """
    reachable = {int(room_vnum) for room_vnum in directly_reachable_rooms}
    rejections: list[str] = []
    for raw_key_vnum in key_object_vnums:
        try:
            key_vnum = int(raw_key_vnum)
        except (TypeError, ValueError):
            continue
        if key_vnum <= 0:
            continue
        carrier_rooms = {
            reset.room_vnum
            for reset in world.mob_resets
            if key_vnum in _reset_object_vnums(reset)
        }
        ground_rooms = {
            reset.room_vnum
            for reset in world.room_object_resets
            if reset.object_vnum == key_vnum
        }
        if reachable.intersection(carrier_rooms | ground_rooms):
            continue
        if carrier_rooms:
            rejections.append(
                f"source route key {key_vnum} has no independently "
                "reachable carrier reset"
            )
        elif ground_rooms:
            rejections.append(
                f"source route key {key_vnum} has no independently "
                "reachable ground reset"
            )
        else:
            rejections.append(
                f"source route key {key_vnum} has no source carrier or "
                "ground reset"
            )
    return tuple(dict.fromkeys(rejections))


_SUBCLASS_SOURCE_SKILL_ALIASES = {
    "bounty hunter": "bounty base",
    "necromancer": "necro base",
    "martial artist": "artist base",
}

_CLASS_SOURCE_TEACHER_SKILLS = {
    "mage": "evocation magiks",
    "cleric": "healing magiks",
    "thief": "detect hidden",
    "warrior": "inner force",
    "psionic": "invis",
    "shifter": "morphing knowledge",
    "brawler": "pugilism knowledge",
    "ranger": "archery knowledge",
    "smithy": "weaponsmithing",
}

_CLASS_SOURCE_TEACHER_KEYWORDS = {
    "mage": "guildmaster",
    "cleric": "guildmaster",
    "thief": "guildmaster",
    "warrior": "guildmaster",
    "psionic": "guildmaster",
    "shifter": "guildmaster",
    "brawler": "guildmaster",
    "ranger": "ranger",
    "smithy": "craftsman",
}


def source_subclass_teacher_skill(subclass: str) -> str:
    """Return the source ``do_change`` teaching entry for a subclass."""
    normalized = " ".join(str(subclass).casefold().split())
    return _SUBCLASS_SOURCE_SKILL_ALIASES.get(
        normalized,
        f"{normalized} base",
    )


def source_class_teacher_skill(character_class: str) -> str | None:
    """Return the source skill that identifies a level-10 class teacher."""
    normalized = " ".join(str(character_class).casefold().split())
    return _CLASS_SOURCE_TEACHER_SKILLS.get(normalized)


def _source_teacher_route(
    world: WorldSource,
    source_skill: str,
    *,
    character_class: str | None = None,
    origin: int = RECALL_VNUM,
    preferred_mobile_vnums: Collection[int] = (),
    preferred_room_vnum: int | None = None,
    preferred_keywords: Collection[str] = (),
    allowed_area_files: Collection[str] = (),
) -> SourceTeacherRoute | None:
    """Find a source-reset teacher that can teach one source skill.

    Both level-10 practice and level-30 subclass changes use the same source
    representation: a teacher skill, a mobile reset, and a route from recall.
    Optional area and keyword filters keep a broad source snapshot from
    selecting a distant higher-tier teacher for an early class handoff.
    """
    preferred = {int(vnum) for vnum in preferred_mobile_vnums}
    preferred_rooms = (
        {int(preferred_room_vnum)}
        if preferred_room_vnum is not None
        else set()
    )
    preferred_keyword_set = {
        " ".join(str(keyword).casefold().split())
        for keyword in preferred_keywords
    }
    allowed_areas = {
        Path(str(area_file)).name.casefold()
        for area_file in allowed_area_files
    }
    class_skill = (
        f"{' '.join(str(character_class).casefold().split())} base"
        if character_class
        else None
    )
    route_rooms = (
        {
            room_vnum: room
            for room_vnum, room in world.rooms.items()
            if Path(str(room.area_file)).name.casefold() in allowed_areas
        }
        if allowed_areas
        else world.rooms
    )
    paths = _shortest_paths_from(route_rooms, origin)
    candidates: list[tuple[tuple[int, int, int, int], SourceTeacherRoute]] = []
    resets_by_mobile: dict[int, list[MobReset]] = {}
    for reset in world.mob_resets:
        resets_by_mobile.setdefault(reset.mobile_vnum, []).append(reset)
    for mobile in world.mobiles.values():
        if (
            allowed_areas
            and Path(str(mobile.area_file)).name.casefold() not in allowed_areas
        ):
            continue
        if not mobile.teaches("teacher base") or not mobile.teaches(source_skill):
            continue
        class_fit = 0 if class_skill and mobile.teaches(class_skill) else 1
        for reset in resets_by_mobile.get(mobile.vnum, ()):
            if (
                allowed_areas
                and (
                    reset.room_vnum not in route_rooms
                    or reset.room_vnum not in world.rooms
                )
            ):
                continue
            if preferred_rooms and reset.room_vnum not in preferred_rooms:
                continue
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
            keywords = tuple(
                " ".join(keyword.casefold().split())
                for keyword in (
                    *mobile.keywords.split(),
                    *mobile.short_description.split(),
                )
            )
            preferred_keyword = next(
                (
                    keyword
                    for keyword in preferred_keyword_set
                    if keyword in keywords
                ),
                None,
            )
            keyword = preferred_keyword or (
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
    return _source_teacher_route(
        world,
        source_subclass_teacher_skill(subclass),
        character_class=character_class,
        origin=origin,
        preferred_mobile_vnums=preferred_mobile_vnums,
    )


def source_class_teacher_route(
    world: WorldSource,
    character_class: str,
    *,
    origin: int = RECALL_VNUM,
    preferred_room_vnum: int | None = None,
) -> SourceTeacherRoute | None:
    """Find the source-backed Midgaard teacher for a base class."""
    normalized = " ".join(str(character_class).casefold().split())
    source_skill = source_class_teacher_skill(normalized)
    if source_skill is None:
        return None
    return _source_teacher_route(
        world,
        source_skill,
        origin=origin,
        preferred_room_vnum=preferred_room_vnum,
        preferred_keywords=(_CLASS_SOURCE_TEACHER_KEYWORDS[normalized],),
        allowed_area_files=("midgaard.are",),
    )


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


def _source_character_is_good_alignment(value: int | None) -> bool:
    """Mirror ``IS_GOOD`` for a revealed player alignment only."""
    return type(value) is int and 350 <= value <= 1000


def source_mobile_can_join_player_fight(
    world: WorldSource,
    mobile: MobileSource,
    *,
    character_level: int | None = None,
    character_alignment: int | None = None,
) -> bool:
    """Mirror the source conditions for an NPC joining a player fight.

    ``violence_update`` considers every visible, ordinary NPC in the room,
    not only mobiles with ``ACT_AGGRESSIVE``.  The source level window in that
    function is player level minus three through plus six; a source range is
    eligible when any fuzzy load can fall inside it.  ``ACT_NO_FIGHT`` is not
    excluded because DD4 still puts that mobile into combat and permits
    effects such as fireshield. Once the player's alignment is revealed,
    DD4's exact ``IS_GOOD(ch) && IS_GOOD(victim)`` branch prevents a good
    bystander from joining a good player's fight. Unknown or masked alignment
    remains possible and therefore fails closed.
    """
    if mobile.vnum in world.shopkeepers:
        return False
    if not mobile.keywords.strip():
        return False
    if mobile.act_flags & ACT_WIZINVIS_MOB:
        return False
    if mobile.affected_flags & (AFF_BLIND | AFF_NON_CORPOREAL):
        return False
    if character_level is not None:
        minimum_level, maximum_level = _mobile_level_range(mobile.level)
        if (
            maximum_level < character_level - 3
            or minimum_level > character_level + 6
        ):
            return False
    if mobile.alignment >= 350 and _source_character_is_good_alignment(
        character_alignment
    ):
        return False
    return True


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
            route_definition.route_preflight_route_room_names,
            route_definition.route_hard_hazard_targets,
        )
    return (None, None, None, (0, 0), False, (), ())


def _mobile_base_hp_range(
    level_range: tuple[int, int],
    *,
    rank: str | None = None,
    hp_modifier: int | None = 0,
) -> tuple[int, int]:
    """Mirror ``create_mobile``'s level, rank, and source HP adjustment."""
    low, high = level_range
    multiplier = MOBILE_RANK_HP_MULTIPLIERS.get(
        str(rank or "common").casefold(),
        1,
    )
    base_range = (
        (low * 8 + low * low // 4) * multiplier,
        (high * 8 + high * high) * multiplier,
    )
    if hp_modifier is None:
        # An unresolved source template is never allowed to look like a
        # neutral mobile. Callers separately reject this state; the range is
        # conservative for reports that still need to display it.
        return (1, MOBILE_SPAWN_HP_LIMIT)
    modifier = max(MOBILE_HP_MOD_MIN, hp_modifier)
    return tuple(
        min(
            MOBILE_SPAWN_HP_LIMIT,
            max(1, base_hp * (100 + modifier) // 100),
        )
        for base_hp in base_range
    )


def _mobile_peak_round_damage(
    level: int,
    *,
    wielding: bool,
    dual_wielding: bool,
    damage_modifier: int | None = 0,
) -> int:
    """Return the raw upper bound when every possible NPC strike lands."""
    unarmed_hit = _apply_mobile_damage_modifier(
        _mobile_normal_hit_damage(level, wielding=False),
        damage_modifier,
    )
    weapon_hit = _apply_mobile_damage_modifier(
        _mobile_normal_hit_damage(level, wielding=True),
        damage_modifier,
    )
    cycle_damage = weapon_hit if wielding else unarmed_hit
    if dual_wielding:
        cycle_damage += weapon_hit
    possible_attacks = 5 + int(level >= 20)
    return cycle_damage * possible_attacks


def _mobile_normal_hit_damage(level: int, *, wielding: bool) -> int:
    """Mirror the maximum ordinary NPC damage for one ``one_hit`` call."""
    unarmed_hit = level * 3 // 2 + level // 4
    return unarmed_hit + (unarmed_hit // 2 if wielding else 0)


def _apply_mobile_damage_modifier(
    damage: int,
    damage_modifier: int | None,
) -> int:
    """Mirror DD4's per-attack ``dam_mod`` scaling and arithmetic cap."""
    if damage <= 0:
        return damage
    if damage_modifier is None:
        # Unknown template inheritance is not a neutral estimate.  Returning
        # the source's per-attack cap keeps downstream gates fail-closed while
        # still allowing diagnostic rows to be rendered.
        return MOBILE_ATTACK_DAMAGE_LIMIT
    modifier = max(MOBILE_DAMAGE_MOD_MIN, int(damage_modifier))
    scaled = damage * (100 + modifier) // 100
    return min(
        MOBILE_ATTACK_DAMAGE_LIMIT,
        max(1, scaled),
    )


def mobile_expected_round_damage(
    level: int,
    *,
    wielding: bool,
    dual_wielding: bool,
    damage_modifier: int | None = 0,
) -> int:
    """Return a conservative source-derived NPC damage-per-round estimate.

    DD4 assumes the first NPC attack lands for this planning estimate, then
    applies the source chances for second, third, fourth, and (at level 20+)
    fifth attacks.  It intentionally ignores the player's armor and the
    mobile's special procedures, so it is an admission estimate rather than
    a live combat result.
    """
    level = max(1, int(level))
    base_damages = range(level // 2, level * 3 // 2 + 1)
    damage_values = tuple(
        _apply_mobile_damage_modifier(
            (
                damage
                + level // 4
                + (damage + level // 4) // 2
                if wielding
                else damage + level // 4
            ),
            damage_modifier,
        )
        for damage in base_damages
    )
    if not damage_values:
        return 1
    damage_sum = sum(damage_values)
    damage_count = len(damage_values)
    if dual_wielding:
        weapon_values = tuple(
            _apply_mobile_damage_modifier(
                damage
                + level // 4
                + (damage + level // 4) // 2,
                damage_modifier,
            )
            for damage in base_damages
        )
        # NPC dual wielding uses a 90-percent source chance.
        cycle_numerator = damage_sum * 10 + sum(weapon_values) * 9
        cycle_denominator = damage_count * 10
    else:
        cycle_numerator = damage_sum
        cycle_denominator = damage_count
    attack_chance = 100 + (level + level // 2) + level + level
    if level >= 20:
        attack_chance += level
    numerator = cycle_numerator * attack_chance
    denominator = cycle_denominator * 100
    return max(1, (numerator + denominator - 1) // denominator)


def _mobile_critical_hit_damage(
    level: int,
    *,
    wielding: bool,
    damage_modifier: int | None = 0,
) -> int:
    """Mirror DD4's NPC critical, which doubles one ordinary hit."""
    return 2 * _apply_mobile_damage_modifier(
        _mobile_normal_hit_damage(level, wielding=wielding),
        damage_modifier,
    )


def mobile_sanctuary_peak_round_damage(
    level: int,
    *,
    wielding: bool,
    dual_wielding: bool,
    damage_modifier: int | None = 0,
) -> int:
    """Return a source upper bound after DD4 sanctuary mitigation.

    ``fight.c`` halves each ordinary strike before the critical multiplier is
    applied, so integer division belongs inside the attack loop rather than
    on the completed raw round total.
    """
    unarmed_hit = _apply_mobile_damage_modifier(
        _mobile_normal_hit_damage(level, wielding=False),
        damage_modifier,
    ) // 2
    weapon_hit = _apply_mobile_damage_modifier(
        _mobile_normal_hit_damage(level, wielding=True),
        damage_modifier,
    ) // 2
    cycle_damage = weapon_hit if wielding else unarmed_hit
    if dual_wielding:
        cycle_damage += weapon_hit
    possible_attacks = 5 + int(level >= 20)
    return cycle_damage * possible_attacks


def mobile_sanctuary_critical_hit_damage(
    level: int,
    *,
    wielding: bool,
    damage_modifier: int | None = 0,
) -> int:
    """Return one critical-hit upper bound after sanctuary mitigation."""
    return (
        _apply_mobile_damage_modifier(
            _mobile_normal_hit_damage(level, wielding=wielding),
            damage_modifier,
        )
        // 2
    ) * 2


def _wandering_aggressors(
    world: WorldSource,
) -> tuple[tuple[MobileSource, MobReset], ...]:
    """Return wandering mobiles that can add combat to a route or endpoint."""
    return tuple(
        (mobile, reset)
        for reset in world.mob_resets
        if (mobile := world.mobiles.get(reset.mobile_vnum)) is not None
        and (
            _source_mobile_is_combat_hazard(world, mobile)
            or _source_mobile_has_unsafe_special(
                world,
                mobile.vnum,
                mobile,
            )
        )
        and mobile.wanders
    )


def _money_object_keyword(item: ObjectSource) -> str:
    """Choose a source-listed keyword that addresses a money object."""
    words = item.keywords.casefold().split()
    for preferred in ("coins", "gold", "silver", "copper", "platinum"):
        if preferred in words:
            return preferred
    return words[0] if words else "coins"


def _source_route_room_names(
    world: WorldSource,
    path_rooms: Collection[int],
) -> tuple[str, ...]:
    """Return normalized source room names crossed by a route."""
    return tuple(
        dict.fromkeys(
            label
            for room_vnum in path_rooms
            if (room := world.rooms.get(room_vnum)) is not None
            and (label := _normalize_name(room.name))
        )
    )


def _source_mobile_where_keyword(mobile: MobileSource) -> str:
    """Choose the shortest source keyword for a live ``where`` query."""
    words = _normalize_name(mobile.keywords).split()
    if words:
        return words[0]
    return _normalize_name(mobile.short_description).split()[-1]


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
    # A wandering mobile's source-reachable rooms do not depend on the
    # destination stash. Cache them across stash routes; otherwise a full
    # world gear scan repeats the same graph search once per stash.
    mobile_search_rooms_cache: dict[int, tuple[int, ...]] = {}
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
        for path_room_vnum in path_rooms[1:]:
            access_rejection = source_room_level_rejection(
                world.rooms.get(path_room_vnum),
                character_level,
            )
            if access_rejection is not None:
                rejections.append(
                    f"route crosses an inaccessible source area in room "
                    f"{path_room_vnum}: {access_rejection}"
                )
        probabilistic_route_program_vnums: list[int] = []
        for path_room_vnum in path_rooms:
            for reset in resets_by_room.get(path_room_vnum, ()):
                mobile = world.mobiles.get(reset.mobile_vnum)
                if mobile is None or not _source_mobile_is_combat_hazard(
                    world,
                    mobile,
                ):
                    continue
                if _source_mobile_has_safe_noncombat_special(
                    world,
                    mobile.vnum,
                ):
                    hazards.append(
                        "source-backed noncombat route special: "
                        f"{mobile.short_description}"
                    )
                    continue
                if (
                    not mobile.aggressive
                    and not mobile.attack_programs
                    and path_room_vnum != room_vnum
                ):
                    continue
                hazard_kind = (
                    "route program attacker"
                    if mobile.attack_programs
                    else "route"
                    if mobile.aggressive
                    else "route combat-joining special"
                )
                hazards.append(
                    f"{hazard_kind}: {mobile.short_description} L{mobile.level} "
                    f"in {path_room_vnum}"
                )
                hazard_level_max = _mobile_level_range(mobile.level)[1]
                hazard_noun = (
                    "program-triggered attacker"
                    if mobile.attack_programs
                    else "aggressive reset"
                    if mobile.aggressive
                    else "combat-joining special"
                )
                hazard_article = (
                    "an" if hazard_noun.startswith("aggressive") else "a"
                )
                if mobile.attack_programs:
                    if _source_mobile_has_deterministic_attack_program(mobile):
                        rejections.append(
                            "route crosses a program-triggered attacker"
                        )
                    elif hazard_level_max > character_level:
                        rejections.append(
                            f"route crosses a higher-level {hazard_noun}"
                        )
                    elif mobile.aggressive and hazard_level_max > (
                        character_level - _SOURCE_TRANSIT_AGGRESSOR_RISK_GAP
                    ):
                        rejections.append(
                            "route crosses an aggressive transit attacker inside "
                            "the transit-risk band"
                        )
                    elif hazard_level_max > character_level - 5:
                        rejections.append(
                            f"route crosses {hazard_article} {hazard_noun} "
                            "inside the useful XP band"
                        )
                    else:
                        probabilistic_route_program_vnums.append(mobile.vnum)
                elif hazard_level_max > character_level:
                    rejections.append(
                        f"route crosses a higher-level {hazard_noun}"
                    )
                elif mobile.aggressive and hazard_level_max > (
                    character_level - _SOURCE_TRANSIT_AGGRESSOR_RISK_GAP
                ):
                    rejections.append(
                        "route crosses an aggressive transit attacker inside "
                        "the transit-risk band"
                    )
                elif hazard_level_max > character_level - 5:
                    rejections.append(
                        f"route crosses {hazard_article} {hazard_noun} "
                        "inside the useful XP band"
                    )
                elif (
                    mobile.aggressive
                    and reset.maximum_count
                    > _MAX_BELOW_BAND_ROUTE_AGGRESSOR_CAPACITY
                ):
                    # A below-band pack can still consume the whole funding
                    # segment before the character reaches the stash.
                    hazards.append(
                        "route crosses a large below-band aggressive reset: "
                        f"{mobile.short_description} L{mobile.level} in "
                        f"{path_room_vnum} (up to {reset.maximum_count} mobiles)"
                    )
                    rejections.append(
                        "route crosses a large below-band aggressive crowd"
                    )
        # A wandering aggressor can enter a path room even when its reset
        # room is elsewhere. Keep below-band transit hazards as cautionary
        # evidence: the runner can finish an unavoidable source-proven trivial
        # interruption without treating it as an XP target.
        for mobile_vnum, mobile in world.mobiles.items():
            if not _source_mobile_is_combat_hazard(world, mobile) or not mobile.wanders:
                continue
            hazard_rooms = (
                path_room_set
                if mobile.aggressive or mobile.attack_programs
                else {room_vnum}
            )
            reachable = mobile_search_rooms_cache.get(mobile_vnum)
            if reachable is None:
                reachable = source_mobile_search_rooms(world, mobile_vnum)
                mobile_search_rooms_cache[mobile_vnum] = reachable
            if hazard_rooms.isdisjoint(reachable):
                continue
            if _source_mobile_has_safe_noncombat_special(world, mobile_vnum):
                hazards.append(
                    "source-backed noncombat route special: "
                    f"{mobile.short_description}"
                )
                continue
            hazard_kind = (
                "reachable program attacker"
                if mobile.attack_programs
                else "reachable wanderer"
                if mobile.aggressive
                else "reachable combat-joining special"
            )
            hazards.append(
                f"{hazard_kind}: {mobile.short_description} L{mobile.level}"
            )
            hazard_level_max = _mobile_level_range(mobile.level)[1]
            hazard_noun = (
                "program-triggered attacker"
                if mobile.attack_programs
                else "aggressive wanderer"
                if mobile.aggressive
                else "combat-joining special"
            )
            hazard_article = (
                "an" if hazard_noun.startswith("aggressive") else "a"
            )
            if mobile.attack_programs:
                if _source_mobile_has_deterministic_attack_program(mobile):
                    rejections.append(
                        "a program-triggered attacker can reach the route"
                    )
                elif hazard_level_max > character_level:
                    rejections.append(
                        f"a higher-level {hazard_noun} can reach the route"
                    )
                elif hazard_level_max > character_level - 5:
                    rejections.append(
                        f"{hazard_article} {hazard_noun} inside the useful XP band "
                        "can reach the route"
                    )
                else:
                    probabilistic_route_program_vnums.append(mobile_vnum)
            elif hazard_level_max > character_level:
                rejections.append(
                    f"a higher-level {hazard_noun} can reach the route"
                )
            elif hazard_level_max > character_level - 5:
                rejections.append(
                    f"{hazard_article} {hazard_noun} inside the useful XP band "
                    "can reach the route"
                )
        for reset in resets_by_room.get(room_vnum, ()):
            mobile = world.mobiles.get(reset.mobile_vnum)
            if mobile is None or not _source_mobile_is_combat_hazard(
                world,
                mobile,
            ):
                continue
            if _source_mobile_has_safe_noncombat_special(
                world,
                mobile.vnum,
            ):
                hazards.append(
                    "source-backed noncombat stash special: "
                    f"{mobile.short_description}"
                )
                continue
            if mobile.aggressive:
                hazards.append(
                    f"stash room has aggressive reset: "
                    f"{mobile.short_description}"
                )
                rejections.append("stash room has an aggressive reset")
            else:
                hazards.append(
                    "stash room has combat-joining special: "
                    f"{mobile.short_description}"
                )
                rejections.append(
                    "stash room has a combat-joining special"
                )

        route_preflight_room_vnum: str | None = None
        route_preflight_command: str | None = None
        route_preflight_target: str | None = None
        route_preflight_level_range = (0, 0)
        route_preflight_hard_hazard = False
        route_preflight_route_room_names: tuple[str, ...] = ()
        probabilistic_programs = tuple(dict.fromkeys(probabilistic_route_program_vnums))
        if len(probabilistic_programs) > 1:
            rejections.append(
                "route has multiple probabilistic program attackers requiring separate preflights"
            )
        elif probabilistic_programs:
            preflight_mobile = world.mobiles.get(probabilistic_programs[0])
            if preflight_mobile is not None:
                route_preflight_room_vnum = str(RECALL_VNUM)
                route_preflight_command = (
                    f"where {_source_mobile_where_keyword(preflight_mobile)}"
                )
                route_preflight_target = preflight_mobile.short_description
                route_preflight_level_range = _mobile_level_range(
                    preflight_mobile.level
                )
                route_preflight_hard_hazard = True
                route_preflight_route_room_names = _source_route_room_names(
                    world,
                    path_rooms,
                )

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
                route_preflight_room_vnum=route_preflight_room_vnum,
                route_preflight_command=route_preflight_command,
                route_preflight_target=route_preflight_target,
                route_preflight_level_range=route_preflight_level_range,
                route_preflight_hard_hazard=route_preflight_hard_hazard,
                route_preflight_route_room_names=route_preflight_route_room_names,
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
    include_closed: bool = False,
) -> tuple[int, ...]:
    """Return rooms a source mobile can occupy from its reset locations.

    DD4's ``update.c`` chooses a random open exit for ordinary non-sentinel
    mobiles.  ``ACT_STAY_AREA`` limits that movement to the mobile's area; it
    does not make the reset room a fixed location.  ``ACT_DIE_IF_MASTER_GONE``
    makes a reset mobile effectively fixed until a master is present, while
    ``AFF_CONFUSION`` uses a separate movement path that overrides sentinel,
    stay-area, and no-mob restrictions.  This graph is therefore the
    source-backed search boundary for live target discovery.  Callers that
    resolve a mobile already observed after a player opened a reset-closed
    door may set ``include_closed`` so the room identity remains source-bound
    for that current session; ordinary route safety keeps the default.
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
                or (not include_closed and exit_source.closed)
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


def _normalize_skill_name(value: object) -> str:
    return " ".join(str(value).casefold().split())


def source_combat_readiness(
    *,
    character_level: int,
    character_class: str | None,
    character_subclass: str | None = None,
    known_skills: Collection[str] = (),
    known_skill_levels: Mapping[str, int] | None = None,
    target_level_range: tuple[int, int],
    equipped_weapon_count: int = 0,
    character_max_hp: int | None = None,
    peak_round_damage: int = 0,
) -> tuple[str, int]:
    """Return a deterministic combat hint and target-specific score bonus.

    The hint only describes commands already selected by the starter's
    source-backed controller.  The bonus is deliberately small and only
    changes ordering within the existing status tier: it rewards a known
    direct action more for a near-band target, lets known disarm reduce the
    armed-target penalty, and gives known protection a small credit near the
    source damage bound.  It never changes a candidate's safety status.
    """
    normalized_class = (
        _normalize_skill_name(character_class) if character_class else ""
    )
    if not normalized_class:
        return "unassessed", 0
    if isinstance(known_skills, str):
        raw_skills: Collection[str] = (known_skills,)
    else:
        raw_skills = known_skills or ()
    skills = set(_source_known_skill_set(raw_skills, known_skill_levels))
    if not skills:
        return "unassessed", 0

    subclass = (
        _normalize_skill_name(character_subclass)
        if character_subclass
        else ""
    )
    capabilities = combat_capabilities_for(normalized_class, subclass)
    direct = tuple(
        capability.name
        for capability in capabilities
        if capability.role == "damage"
        and capability.name in skills
        and capability.name not in _SOURCE_CONTROL_COMBAT_SKILLS
    )
    setup = tuple(
        capability.name
        for capability in capabilities
        if capability.role == "setup" and capability.name in skills
    )
    passive = tuple(
        skill for skill in _SOURCE_PASSIVE_COMBAT_SKILLS if skill in skills
    )
    control = tuple(
        skill for skill in _SOURCE_CONTROL_COMBAT_SKILLS if skill in skills
    )
    defensive = tuple(
        skill for skill in _SOURCE_DEFENSIVE_COMBAT_SKILLS if skill in skills
    )
    labels = []
    if direct:
        labels.append("direct=" + ",".join(direct))
    if setup:
        labels.append("setup=" + ",".join(setup))
    if passive:
        labels.append("passive=" + ",".join(passive))
    if control:
        labels.append("control=" + ",".join(control))
    if defensive:
        labels.append("defense=" + ",".join(defensive))
    if not labels:
        return "no mapped action", 0

    # A source target's upper fuzzed level is the available deterministic
    # proxy for combat pressure. Keep this a tie-breaker, never a viability
    # decision: live consider and the runner's damage window remain final.
    target_pressure = max(
        1,
        min(4, target_level_range[1] - character_level + 4),
    )
    bonus = 0
    if direct:
        bonus += min(12, len(direct) * (2 + target_pressure))
    if passive:
        bonus += min(6, len(passive) * max(1, target_pressure // 2))
    if equipped_weapon_count and "disarm" in control:
        bonus += min(12, equipped_weapon_count * 6)
    if (
        defensive
        and character_max_hp is not None
        and character_max_hp > 0
        and peak_round_damage >= character_max_hp * 0.5
    ):
        bonus += min(5, len(defensive) * 2)
    return "; ".join(labels), bonus


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
    """Choose a source keyword that minimizes live ``where`` collisions.

    Prefer a keyword that distinguishes this prototype from every other
    prototype with the same visible short description.  DD4 can expose the
    same room text for distinct mobiles (for example, male and female
    citizens), so a globally uncommon keyword is not enough when a more
    specific source keyword is available.
    """
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

    normalized_short = _normalize_name(mobile.short_description)
    same_display_keyword_counts: dict[str, int] = {}
    for other in world.mobiles.values():
        if _normalize_name(other.short_description) != normalized_short:
            continue
        other_tokens = {
            token.casefold()
            for token in re.findall(r"[A-Za-z0-9]+", other.keywords)
        }
        for token in other_tokens:
            same_display_keyword_counts[token] = (
                same_display_keyword_counts.get(token, 0) + 1
            )
    distinguishing_tokens = tuple(
        token for token in tokens
        if same_display_keyword_counts.get(token, 0) == 1
    )
    if distinguishing_tokens:
        return min(
            distinguishing_tokens,
            key=lambda token: (
                keyword_counts.get(token, 0),
                -len(token),
                tokens.index(token),
            ),
        )

    return min(
        tokens,
        key=lambda token: (
            keyword_counts.get(token, 0),
            -len(token),
            tokens.index(token),
        ),
    )
