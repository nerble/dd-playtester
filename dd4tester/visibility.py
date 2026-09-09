"""Source-authorized learned invisibility for noncombat city travel."""

from __future__ import annotations

import re
from typing import Mapping

from .archetypes import archetype_registry
from .hunt_candidates import WorldSource, _mobile_level_range
from .specials import SAFE_NONCOMBAT_SPECIALS


_AFF_DETECT_INVIS = 1 << 3
_APPLY_DETECT_INVIS = 29


def invisibility_blocks_source_greet(
    world: WorldSource | None, mobile_vnum: int | None, *, target: str,
) -> bool:
    """Audit mob_prog.c:greet visibility, never ALL_GREET or general combat."""
    if world is None or mobile_vnum is None:
        return False
    mobile = world.mobiles.get(mobile_vnum)
    if (
        mobile is None or mobile.aggressive or not mobile.attack_programs
        or mobile.affected_flags & _AFF_DETECT_INVIS
        or _mobile_level_range(mobile.level)[1] > 100  # handler.c: can_see
        or world.mobile_specials.get(mobile_vnum)
        or " ".join(mobile.short_description.casefold().split())
        != " ".join(target.casefold().split())
        or any(program.trigger != "greet_prog" for program in mobile.attack_programs)
    ):
        return False
    resets = [reset for reset in world.mob_resets if reset.mobile_vnum == mobile_vnum]
    if not resets or any(reset.equipment or reset.object_vnums for reset in resets):
        return False
    # Do not infer visibility from an unaudited script that can cast, load,
    # equip, or otherwise change the observer's detection capabilities.
    for program in mobile.programs:
        for raw in program.commands:
            command = " ".join(raw.casefold().split())
            if command == "mpkill $n" and program.trigger == "greet_prog":
                continue
            if re.fullmatch(r"if rand\(\d+\)", command):
                continue
            if command in {"else", "endif", "dance", "sing"}:
                continue
            if command.startswith(("say ", "yell ", "emote ")):
                continue
            return False
    return True


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
