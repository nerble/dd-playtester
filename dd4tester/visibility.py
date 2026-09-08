"""Source-authorized learned invisibility for noncombat city travel."""

from __future__ import annotations

from typing import Mapping

from .archetypes import archetype_registry


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
