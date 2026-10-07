"""Source estimates for the passive defenses against ordinary weapon hits."""

from __future__ import annotations

from fractions import Fraction
from typing import Collection, Mapping


def normal_attack_landing_probability(
    *,
    character_level: int,
    attacker_level: int,
    character_class: str,
    known_skills: Collection[str],
    known_skill_levels: Mapping[str, int],
    wielding: bool,
    shield: bool,
    blind: bool = False,
    arm_trauma: bool = False,
    leg_trauma: bool = False,
    dodge_disabled: bool = False,
    defenses_disabled: bool = False,
) -> Fraction:
    """Mirror fight.c's shield-block, parry and dodge rolls.

    This is conditional on an ordinary, defendable hit reaching damage().
    Armor misses, dual parry, critical mitigation and other defenses receive
    no credit. A defense needs an explicitly observed positive proficiency.
    """
    if defenses_disabled:
        return Fraction(1)
    skills = {str(skill).casefold().strip() for skill in known_skills}
    levels = {
        str(skill).casefold().strip(): value
        for skill, value in known_skill_levels.items()
    }

    def percent(skill: str) -> int:
        value = levels.get(skill)
        return value if (
            skill in skills and type(value) is int and 0 < value <= 100
        ) else 0

    level_bonus = (character_level - attacker_level) * 2
    landing = Fraction(1)
    for skill, enabled in (
        ("shield block", shield),
        (
            "pre-empt" if character_class.casefold() == "brawler" else "parry",
            wielding or character_class.casefold() == "brawler",
        ),
        ("dodge", not dodge_disabled),
    ):
        proficiency = percent(skill)
        if not enabled or proficiency == 0:
            continue
        chance = proficiency // 2 + level_bonus
        # Shield block caps after arm trauma; parry and dodge cap first.
        if skill == "shield block":
            if arm_trauma:
                chance //= 2
            chance = min(66, chance)
        else:
            chance = min(66, chance)
            if blind:
                chance //= 2
            if (skill in {"parry", "pre-empt"} and arm_trauma) or (
                skill == "dodge" and leg_trauma
            ):
                chance //= 2
        # number_percent() is 1..100, and success requires roll < chance.
        success = max(0, min(100, chance - 1))
        landing *= Fraction(100 - success, 100)
    return landing
