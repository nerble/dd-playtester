"""Source-backed reward planning for the timing of level-up equipment."""

from __future__ import annotations

import math

from .hunt_candidates import WorldSource, _mobile_base_hp_range, _mobile_level_range


def single_kill_gear_window(
    world: WorldSource,
    mobile_vnum: int,
    *,
    character_level: int,
    maximum_action_damage: int,
    maximum_runtime: float,
) -> int | None:
    """Plan generously for one plain kill, not combat or XP authorization.

    fight.c awards both xp_compute and damage credit. Use the most favorable
    popularity/random roll, full source HP, possible regeneration throughout
    the worker's cleanup allowance, and an amplified final-hit allowance.
    Complicated or incompletely parsed sources keep the original gear rule.
    """
    mobile = world.mobiles.get(mobile_vnum)
    if (
        mobile is None or character_level < 1 or maximum_action_damage <= 0
        or not math.isfinite(maximum_runtime) or maximum_runtime <= 0
        or mobile.programs or world.mobile_specials.get(mobile_vnum)
        or mobile.rank not in {"none", "common"}
        or not mobile.hp_modifier_known or mobile.hp_modifier is None
    ):
        return None
    area_modifier = world.area_xp_modifiers.get(mobile.area_file)
    resets = [reset for reset in world.mob_resets if reset.mobile_vnum == mobile_vnum]
    if type(area_modifier) is not int or not resets or any(r.equipment for r in resets):
        return None
    if mobile.template_name and mobile.template_name not in world.mobile_templates:
        return None
    modifier = max(0, area_modifier + mobile.xp_modifier)
    levels = _mobile_level_range(mobile.level)
    kill_reward = 0
    for level in range(levels[0], levels[1] + 1):
        if level < character_level - 5:
            reward = level * 10
        else:
            difference = max(-4, min(character_level - level, 11))
            base = ((level + 10) ** 2 - difference * 3 * (level + 10)) * modifier // 100
            # xp *= 5 / 4 in DD4 uses integer division, so alignment adds no XP.
            popular_bonus = base + base // 8
            reward = max(level * 10, math.ceil(popular_bonus * 1.1))
        kill_reward = max(kill_reward, reward)
    hp = _mobile_base_hp_range(levels, rank=mobile.rank, hp_modifier=mobile.hp_modifier)[1]
    regeneration = levels[1] * 3 // 2
    if mobile.act_flags & (1 << 11):  # ACT_REGENERATOR
        regeneration *= levels[1] // 10 + 2
    if mobile.act_flags & (1 << 25):  # ACT_NO_HEAL
        regeneration = 0
    # update_handler's shortest ordinary tick is 15s. Include a tick at entry.
    ticks = math.ceil((maximum_runtime + 105) / 15) + 1
    return kill_reward + hp + regeneration * ticks + maximum_action_damage * 3 + 11
