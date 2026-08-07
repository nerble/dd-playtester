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

ECONOMIC_SPECIALS = frozenset({"spec_thief"})
"""Specials that can remove a bounded amount of carried currency."""

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
    return SourceSpecialProfile(normalized, xp_bonus, risk)


def source_special_xp_bonus(name: str) -> int:
    """Return the additive XP modifier used by ``db.c`` for a special."""

    return source_special_profile(name).xp_bonus

