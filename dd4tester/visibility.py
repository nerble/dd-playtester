"""Source-authorized learned invisibility for noncombat city travel."""

from __future__ import annotations

from typing import Mapping

from .archetypes import archetype_registry
from .hunt_candidates import WorldSource, _mobile_level_range
from .specials import SAFE_NONCOMBAT_SPECIALS


_AFF_DETECT_INVIS = 1 << 3
_APPLY_DETECT_INVIS = 29


def invisibility_blocks_source_aggression(
    world: WorldSource | None,
    mobile_vnum: int | None,
) -> bool:
    """Audit update.c aggression visibility for one source mobile."""
    if world is None or mobile_vnum is None:
        return False
    mobile = world.mobiles.get(mobile_vnum)
    if (
        mobile is None
        or not mobile.aggressive
        or mobile.affected_flags & _AFF_DETECT_INVIS
        or _mobile_level_range(mobile.level)[1] > 100
        or mobile.programs
    ):
        return False
    resets = [reset for reset in world.mob_resets if reset.mobile_vnum == mobile_vnum]
    if not resets:
        return False
    for reset in resets:
        for _wear_location, object_vnum in reset.equipment:
            object_source = world.objects.get(object_vnum)
            if object_source is None or any(
                location == _APPLY_DETECT_INVIS
                for location, _modifier in object_source.affects
            ):
                return False
    specials = set(world.mobile_specials.get(mobile_vnum, ()))
    return not specials or specials <= SAFE_NONCOMBAT_SPECIALS


def learned_invisibility_mana_cost(
    character_class: str, subclass: str | None, skills: Mapping[str, object],
) -> int | None:
    """Return a cost only for an audited class and positive observed practice."""
    if not isinstance(skills, Mapping):
        return None
    registry = archetype_registry()
    subclass = str(subclass or "").strip().casefold()
    if subclass == "none":
        subclass = ""
    try:
        base = registry.class_profile(character_class).name
        if subclass:
            profile = registry.subclass_profile(subclass)
            if profile.base_class != base or not profile.available:
                return None
    except ValueError:
        return None
    # pre_req-mage:57, cleric:166, thief:49-50, psionic:86-87, monk:66-67.
    if base not in {"mage", "cleric", "thief", "psionic"} and subclass != "monk":
        return None
    proficiency = skills.get("invis")
    if type(proficiency) is not int or not 0 < proficiency <= 100:
        return None
    # const.c:invis is defensive, min_mana=5; handler.c:mana_cost.
    return max(5, 45 - proficiency)
