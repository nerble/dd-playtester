"""Shared source-backed combat capability ordering.

The source planner and live starter must agree about which learned actions are
available for a base class or subclass.  This module contains only that
contract; damage formulas and live safety gates remain in their owning layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Mapping

from .archetypes import archetype_registry


def _normalize(value: object) -> str:
    return " ".join(str(value).casefold().replace("_", " ").split())


@dataclass(frozen=True)
class CombatCapability:
    """One source-registered action that can contribute to combat output."""

    name: str
    kind: str
    source_reference: str
    estimated: bool = True
    role: str = "damage"


# These are ordered from the preferred action to the cheaper fallback. The
# order is a planning hint only: a capability is executable only after the
# live practice listing, current resources, and target gates confirm it.
BASE_COMBAT_CAPABILITIES: Mapping[str, tuple[CombatCapability, ...]] = {
    "mage": (
        CombatCapability("acid blast", "spell", "magic.c:spell_acid_blast"),
        CombatCapability("fireball", "spell", "magic.c:spell_fireball"),
        CombatCapability("lightning bolt", "spell", "magic.c:spell_lightning_bolt"),
        CombatCapability("shocking grasp", "spell", "magic.c:spell_shocking_grasp"),
        CombatCapability("colour spray", "spell", "magic.c:spell_colour_spray"),
        CombatCapability("burning hands", "spell", "magic.c:spell_burning_hands"),
        CombatCapability("chill touch", "spell", "magic.c:spell_chill_touch"),
        CombatCapability("magic missile", "spell", "magic.c:spell_magic_missile"),
    ),
    "cleric": (
        CombatCapability("cause critical", "spell", "magic.c:spell_cause_critical"),
        CombatCapability("cause serious", "spell", "magic.c:spell_cause_serious"),
        CombatCapability("cause light", "spell", "magic.c:spell_cause_light"),
    ),
    "thief": (
        CombatCapability("circle", "skill", "fight.c:do_circle"),
        CombatCapability("knife toss", "skill", "fight.c:do_knife_toss"),
        CombatCapability(
            "dirt kick",
            "skill",
            "fight.c:do_dirt_kick",
            estimated=False,
        ),
        CombatCapability(
            "trip",
            "skill",
            "fight.c:do_trip",
            estimated=False,
        ),
        # Backstab is budgeted separately as a one-shot opener.
        CombatCapability(
            "backstab",
            "skill",
            "fight.c:do_backstab",
            estimated=False,
        ),
        CombatCapability(
            "disarm",
            "skill",
            "fight.c:do_disarm",
            estimated=False,
        ),
    ),
    "warrior": (
        CombatCapability("stun", "skill", "fight.c:do_stun", estimated=False),
        CombatCapability("headbutt", "skill", "fight.c:do_headbutt"),
        CombatCapability("kick", "skill", "fight.c:do_kick"),
        CombatCapability(
            "disarm",
            "skill",
            "fight.c:do_disarm",
            estimated=False,
        ),
    ),
    "psionic": (
        CombatCapability("psychic crush", "spell", "magic.c:spell_psychic_crush"),
        CombatCapability("agitation", "spell", "magic.c:spell_agitation"),
        CombatCapability("mind thrust", "spell", "magic.c:spell_mind_thrust"),
    ),
    "shifter": (
        # Form changes are setup actions.  They are visible to readiness
        # reporting and live dispatch, but never treated as direct damage.
        CombatCapability(
            "morph",
            "skill",
            "sft.c:do_morph",
            estimated=False,
            role="setup",
        ),
        CombatCapability(
            "snake form",
            "skill",
            "sft.c:do_morph_snake",
            estimated=False,
            role="setup",
        ),
    ),
    "brawler": (
        CombatCapability("headbutt", "skill", "fight.c:do_headbutt"),
        CombatCapability("punch", "skill", "skill.c:do_punch"),
    ),
    "ranger": (
        CombatCapability("shoot", "skill", "fight.c:do_shoot", estimated=False),
        CombatCapability("kick", "skill", "fight.c:do_kick"),
        CombatCapability(
            "disarm",
            "skill",
            "fight.c:do_disarm",
            estimated=False,
        ),
    ),
    "smithy": (
        CombatCapability(
            "weaponchain",
            "skill",
            "skill.c:do_weaponchain",
            estimated=False,
            role="setup",
        ),
        CombatCapability(
            "hurl",
            "skill",
            "fight.c:do_hurl",
            estimated=False,
        ),
    ),
}


SUBCLASS_COMBAT_CAPABILITIES: Mapping[str, tuple[CombatCapability, ...]] = {
    "barbarian": (
        CombatCapability("headbutt", "skill", "fight.c:do_headbutt"),
        CombatCapability(
            "berserk",
            "skill",
            "fight.c:do_berserk",
            estimated=False,
        ),
    ),
    "warlock": (
        CombatCapability(
            "warcry",
            "skill",
            "act_move.c:do_warcry",
            estimated=False,
            role="setup",
        ),
    ),
    "templar": (
        CombatCapability(
            "warcry",
            "skill",
            "act_move.c:do_warcry",
            estimated=False,
            role="setup",
        ),
    ),
    "vampire": (
        CombatCapability(
            "disarm",
            "skill",
            "fight.c:do_disarm",
            estimated=False,
        ),
        CombatCapability(
            "suck",
            "skill",
            "skill.c:do_suck",
        ),
        CombatCapability(
            "lunge",
            "skill",
            "fight.c:do_lunge",
            estimated=False,
        ),
    ),
    "martial artist": (
        CombatCapability("atemi", "skill", "skill.c:do_atemi"),
        CombatCapability(
            "kansetsu",
            "skill",
            "skill.c:do_kansetsu",
            estimated=False,
        ),
    ),
    "thug": (
        CombatCapability(
            "smash",
            "skill",
            "act_move.c:do_smash",
            estimated=False,
        ),
    ),
    "ninja": (
        CombatCapability(
            "decapitate",
            "skill",
            "fight.c:do_decapitate",
            estimated=False,
        ),
    ),
    "bounty hunter": (
        CombatCapability(
            "stun",
            "skill",
            "fight.c:do_stun",
            estimated=False,
            role="control",
        ),
        CombatCapability(
            "berserk",
            "skill",
            "fight.c:do_berserk",
            estimated=False,
            role="setup",
        ),
    ),
    "necromancer": (
        CombatCapability("harm", "spell", "magic.c:spell_harm"),
    ),
    "druid": (
        CombatCapability("wither", "spell", "magic.c:spell_wither"),
    ),
    "knight": (
        CombatCapability("flamestrike", "spell", "magic.c:spell_flamestrike"),
    ),
    "infernalist": (
        CombatCapability(
            "hellfire",
            "spell",
            "magic.c:spell_hells_fire",
        ),
    ),
    "witch": (
        CombatCapability("wither", "spell", "magic.c:spell_wither"),
    ),
    "monk": (
        CombatCapability("agitation", "spell", "magic.c:spell_agitation"),
        CombatCapability("mind thrust", "spell", "magic.c:spell_mind_thrust"),
    ),
    "werewolf": (
        CombatCapability("wolfbite", "skill", "sft.c:do_wolfbite"),
        CombatCapability("ravage", "skill", "sft.c:do_ravage"),
    ),
    "bard": (
        CombatCapability(
            "chant of battle",
            "skill",
            "skill.c:do_chant",
            estimated=False,
            role="setup",
        ),
    ),
    "engineer": (
        CombatCapability(
            "trigger",
            "skill",
            "skill.c:do_trigger",
            estimated=False,
            role="setup",
        ),
    ),
    "runesmith": (
        CombatCapability(
            "pyro rune",
            "skill",
            "skill.c:do_inscribe; magic.c:spell_runic_flames",
            estimated=False,
            role="setup",
        ),
    ),
}


def combat_capabilities_for(
    character_class: str | None,
    character_subclass: str | None = None,
    *,
    estimated_only: bool = False,
) -> tuple[CombatCapability, ...]:
    """Return subclass-first capabilities with duplicate names removed."""
    normalized_class = _normalize(character_class)
    subclass_capabilities: tuple[CombatCapability, ...] = ()
    normalized_subclass = _normalize(character_subclass)
    if normalized_subclass:
        try:
            required_class = archetype_registry().subclass_profile(
                normalized_subclass
            ).base_class
            actual_class = archetype_registry().class_profile(
                normalized_class
            ).name
        except ValueError:
            required_class = None
            actual_class = None
        if required_class is not None and actual_class == required_class:
            subclass_capabilities = SUBCLASS_COMBAT_CAPABILITIES.get(
                normalized_subclass,
                (),
            )
    selected = (
        *subclass_capabilities,
        *BASE_COMBAT_CAPABILITIES.get(normalized_class, ()),
    )
    result: list[CombatCapability] = []
    seen: set[str] = set()
    for capability in selected:
        if estimated_only and not capability.estimated:
            continue
        if capability.name in seen:
            continue
        seen.add(capability.name)
        result.append(capability)
    return tuple(result)


def combat_capability_names(
    character_class: str | None,
    character_subclass: str | None = None,
) -> tuple[str, ...]:
    """Return every registered capability for readiness reporting."""
    return tuple(
        capability.name
        for capability in combat_capabilities_for(
            character_class,
            character_subclass,
        )
    )


def combat_skill_names(
    character_class: str | None,
    character_subclass: str | None = None,
    *,
    observed_skills: Collection[str] = (),
) -> tuple[str, ...]:
    """Return registered skills, optionally followed by observed audit data.

    A checkpoint can contain a legal skill that has not been added to the
    static registry yet. Keep that evidence usable for reports and readiness
    analysis without letting unknown names silently become executable. Live
    dispatchers must call this function without ``observed_skills`` until the
    action has been added to the source-audited registry.
    """
    ordered = [
        capability.name
        for capability in combat_capabilities_for(
            character_class,
            character_subclass,
        )
        if capability.kind == "skill"
    ]
    seen = set(ordered)
    for skill in observed_skills:
        normalized = _normalize(skill)
        if normalized and normalized not in seen:
            ordered.append(normalized)
            seen.add(normalized)
    return tuple(ordered)


def combat_spell_names(
    character_class: str | None,
    character_subclass: str | None = None,
) -> tuple[str, ...]:
    """Return source-registered direct spells in execution order."""
    return tuple(
        capability.name
        for capability in combat_capabilities_for(
            character_class,
            character_subclass,
            estimated_only=True,
        )
        if capability.kind == "spell"
    )
