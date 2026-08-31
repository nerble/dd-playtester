"""Source-backed DD4 mobile special-procedure risk profiles.

The XP modifier tiers mirror ``load_specials`` in the DD4 server's
``server/src/db.c``.  The risk labels add the narrower behavioral judgment
from ``server/src/special.c`` that an XP bonus alone cannot provide.
"""

from __future__ import annotations

from dataclasses import dataclass


SOURCE_SPECIAL_AUDIT_REVISION = "1b759f5"


@dataclass(frozen=True)
class SourceSpecialProfile:
    """One source special's reward tier and autonomous risk class."""

    name: str
    xp_bonus: int
    risk: str
    status_effects: tuple[str, ...] = ()


SAFE_NONCOMBAT_SPECIALS = frozenset(
    {
        "spec_cast_adept",
        "spec_cast_hooker",
        "spec_cast_orb",
        "spec_fido",
        "spec_janitor",
        "spec_repairman",
    }
)
"""Specials that do not attack a normal autonomous player."""

CONDITIONAL_COMBAT_SPECIALS = frozenset(
    {"spec_bounty", "spec_clan_guard", "spec_executioner"}
)
"""Zero-bonus specials that can attack players with criminal/clan flags."""

COMBAT_JOINING_SPECIALS = frozenset(
    {"spec_guard", "spec_sahuagin_guard"}
)
"""Specials that can join a fight before they are fighting themselves.

``special.c`` makes these guards attack an NPC that is already fighting a
player, so their source presence can turn an otherwise isolated hunt into a
multi-enemy fight even without ``ACT_AGGRESSIVE``.
"""

ECONOMIC_SPECIALS = frozenset({"spec_thief"})
"""Specials that can remove a bounded amount of carried currency."""

TRANSIT_SAFE_COMBAT_ONLY_SPECIALS = frozenset({"spec_cast_undead"})
"""Specials that act only after another character is fighting the mobile."""

WEAK_DEBILITATING_SPECIALS = frozenset(
    {"spec_poison", "spec_kungfu_poison"}
)
"""Weak specials that apply poison but add no direct damage."""

WEAK_EXTRA_ATTACK_SPECIALS = frozenset(
    {"spec_bloodsucker", "spec_guard", "spec_sahuagin_guard"}
)
"""Weak specials whose extra action is bounded as one additional hit."""

WEAK_DIRECT_DAMAGE_SPECIALS = frozenset({"spec_cast_judge"})
"""Weak specials with a source-bounded direct damage spell."""

POST_OBJECTIVE_HAZARD_SPECIALS = frozenset(
    {
        *WEAK_DEBILITATING_SPECIALS,
        *WEAK_DIRECT_DAMAGE_SPECIALS,
        "spec_cast_cleric",
        "spec_cast_mage",
        "spec_cast_undead",
    }
)
"""Audited specials that make a below-band post-kill pursuer unsafe."""

_STATUS_EFFECTS_BY_SPECIAL: dict[str, tuple[str, ...]] = {
    # special.c chooses blindness without a level gate, then adds curse and
    # dispel magic to the higher-level cleric spell pool.
    "spec_cast_cleric": ("blindness", "curse", "dispel magic"),
    # The mage special has the same level-zero blindness opener and can also
    # remove protection or apply weakening effects at higher levels.
    "spec_cast_mage": (
        "blindness",
        "weaken",
        "dispel magic",
        "energy drain",
    ),
    # spec_cast_undead selects from a level-gated spell table only after the
    # player is already fighting the mobile. The unparameterized profile is
    # intentionally the union of every possible late-level effect; callers
    # with a source level bound should use source_special_status_effects(...,
    # level=...) for the narrower set.
    "spec_cast_undead": (
        "curse",
        "strength drain",
        "blindness",
        "poison",
        "energy drain",
        "harm",
        "gate",
    ),
    # The druid table adds fear at source level 15; its lower-level direct
    # spell set is bounded separately by the campaign selector.
    "spec_cast_druid": ("fear",),
    # The psionicist table adds energy drain at 14 and disintegrate at 35;
    # both are intentionally outside the autonomous special audit for now.
    "spec_cast_psionicist": ("energy drain", "disintegrate"),
    # spec_demon selects from a source-level-gated spell table only after the
    # player is already fighting.  Keep the full late-level union here; the
    # bounded helper below narrows it for a known mobile level.
    "spec_demon": (
        "curse",
        "chill touch",
        "burning hands",
        "strength drain",
        "energy drain",
        "hold",
        "wither",
        "hellfire",
        "gate",
        "hex",
        "fire breath",
    ),
    # The assassin special only reaches this combat branch after the player
    # has engaged the mobile, but its dirt kick can blind and its trip/circle
    # choices can disrupt the fight or add one extra ordinary hit.
    "spec_assassin": ("blindness", "trip"),
}

_ZERO_BONUS_SPECIALS = frozenset(
    {
        *SAFE_NONCOMBAT_SPECIALS,
        *CONDITIONAL_COMBAT_SPECIALS,
        *ECONOMIC_SPECIALS,
        "spec_celestial_repairman",
    }
)
_WEAK_BONUS_SPECIALS = frozenset(
    {
        *WEAK_DEBILITATING_SPECIALS,
        *WEAK_EXTRA_ATTACK_SPECIALS,
        *WEAK_DIRECT_DAMAGE_SPECIALS,
        "spec_bloodsucker",
        "spec_spectral_minion",
        "spec_superwimpy",
    }
)
_MODERATE_BONUS_SPECIALS = frozenset(
    {
        "spec_blue_grung",
        "spec_green_grung",
        "spec_kappa",
        "spec_large_whale",
        "spec_laghathti",
        "spec_sahuagin_cavalry",
        "spec_sahuagin_cleric",
        "spec_sahuagin_infantry",
        "spec_small_whale",
        "spec_uzollru",
        "spec_warrior",
    }
)
_STRONG_BONUS_SPECIALS = frozenset(
    {
        "spec_aboleth",
        "spec_assassin",
        "spec_cast_druid",
        "spec_cast_electric",
        "spec_cast_water_sprite",
        "spec_demon",
        "spec_orange_grung",
        "spec_purple_grung",
        "spec_red_grung",
        "spec_sahuagin_baron",
        "spec_sahuagin_lieutenant",
    }
)
_BOSS_BONUS_SPECIALS = frozenset(
    {
        "spec_cast_archmage",
        "spec_cast_priestess",
        "spec_evil_evil_gezhp",
        "spec_gold_grung",
        "spec_grail",
        "spec_mast_vampire",
        "spec_priestess",
        "spec_sahuagin_high_cleric",
        "spec_sahuagin_prince",
    }
)


def source_special_profile(name: str) -> SourceSpecialProfile:
    """Return the source reward/risk profile for one special name.

    Specials not listed in the explicit ``db.c`` bonus branches use DD4's
    default average-combat bonus of ten.  Unknown names are deliberately
    treated the same way and remain autonomous-rejected by the caller.
    """

    normalized = str(name).strip().casefold()
    if normalized in _ZERO_BONUS_SPECIALS:
        xp_bonus = 0
    elif normalized in _WEAK_BONUS_SPECIALS:
        xp_bonus = 5
    elif normalized in _MODERATE_BONUS_SPECIALS:
        xp_bonus = 10
    elif normalized in _STRONG_BONUS_SPECIALS:
        xp_bonus = 15
    elif normalized in _BOSS_BONUS_SPECIALS:
        xp_bonus = 20
    else:
        xp_bonus = 10

    if normalized in SAFE_NONCOMBAT_SPECIALS:
        risk = "noncombat"
    elif normalized in CONDITIONAL_COMBAT_SPECIALS:
        risk = "conditional-combat"
    elif normalized in ECONOMIC_SPECIALS:
        risk = "economic"
    elif normalized in TRANSIT_SAFE_COMBAT_ONLY_SPECIALS:
        risk = "combat-only"
    elif normalized in WEAK_DEBILITATING_SPECIALS:
        risk = "debilitating"
    elif normalized in WEAK_EXTRA_ATTACK_SPECIALS:
        risk = "extra-attack"
    elif normalized in WEAK_DIRECT_DAMAGE_SPECIALS:
        risk = "direct-damage"
    elif normalized == "spec_celestial_repairman":
        risk = "relocation"
    elif normalized in {"spec_spectral_minion", "spec_superwimpy"}:
        risk = "unstable"
    elif normalized in _BOSS_BONUS_SPECIALS:
        risk = "boss-combat"
    elif normalized in _STRONG_BONUS_SPECIALS:
        risk = "strong-combat"
    elif normalized in _MODERATE_BONUS_SPECIALS:
        risk = "moderate-combat"
    else:
        risk = "combat"
    return SourceSpecialProfile(
        normalized,
        xp_bonus,
        risk,
        _STATUS_EFFECTS_BY_SPECIAL.get(normalized, ()),
    )


def source_special_status_effects(
    name: str,
    *,
    level: int | None = None,
) -> tuple[str, ...]:
    """Return source-audited effects, narrowed by a caster level when known.

    ``spec_cast_undead`` loops until it selects a spell whose minimum level is
    met. Keeping that table here prevents a level-12 undead mobile from being
    treated as if it could already energy-drain, harm, or gate.
    """

    normalized = str(name).strip().casefold()
    if normalized not in {
        "spec_cast_undead",
        "spec_cast_druid",
        "spec_cast_psionicist",
        "spec_demon",
    } or level is None:
        return source_special_profile(normalized).status_effects
    try:
        caster_level = max(0, int(level))
    except (TypeError, ValueError):
        return source_special_profile(normalized).status_effects
    if normalized == "spec_cast_druid":
        return ("fear",) if caster_level >= 15 else ()
    if normalized == "spec_cast_psionicist":
        effects: list[str] = []
        if caster_level >= 14:
            effects.append("energy drain")
        if caster_level >= 35:
            effects.append("disintegrate")
        return tuple(effects)
    if normalized == "spec_demon":
        effects = ["curse"]
        if caster_level >= 3:
            effects.append("chill touch")
        if caster_level >= 5:
            effects.append("burning hands")
        if caster_level >= 12:
            effects.append("strength drain")
        if caster_level >= 15:
            effects.append("energy drain")
        if caster_level >= 18:
            effects.append("hold")
        if caster_level >= 20:
            effects.append("wither")
        if caster_level >= 25:
            effects.append("hellfire")
        if caster_level >= 30:
            effects.append("gate")
        if caster_level >= 40:
            effects.append("hex")
        if caster_level >= 50:
            effects.append("fire breath")
        return tuple(effects)
    effects = ["curse"]
    if caster_level >= 6:
        effects.append("strength drain")
    if caster_level >= 9:
        effects.append("blindness")
    if caster_level >= 12:
        effects.append("poison")
    if caster_level >= 15:
        effects.append("energy drain")
    if caster_level >= 18:
        effects.append("harm")
    if caster_level >= 20:
        effects.append("gate")
    return tuple(effects)


def source_special_xp_bonus(name: str) -> int:
    """Return the additive XP modifier used by ``db.c`` for a special."""

    return source_special_profile(name).xp_bonus
