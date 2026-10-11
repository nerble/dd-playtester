from dataclasses import replace

import pytest

from dd4tester.hunt_candidates import (
    HuntCandidate, MobReset, MobileSource, ObjectSource, SourceCombatOutput, WorldSource,
)
from dd4tester.mobile_loadouts import sanctuary_limited_output, single_weapon_loadout


def loadout_fixture() -> tuple[HuntCandidate, WorldSource]:
    mobile = MobileSource(101, "soldier", "a soldier", 25, 1, 0, "test.are")
    sword = ObjectSource(201, "sword", "a sword", 5, (0, 0, 0, 3), 0,
                         affects=((19, 2), (18, 5)))
    armor = ObjectSource(202, "armor", "some armor", 9, (0, 0, 0, 0), 0,
                         affects=((13, 10), (17, -10)))
    instrument = ObjectSource(203, "pipes", "some pipes", 36, (0, 0, 0, 0), 0,
                              affects=((24, -5),))
    world = WorldSource(
        mobiles={101: mobile},
        objects={item.vnum: item for item in (sword, armor, instrument)},
        mob_resets=[MobReset(101, 301, 1, (201, 202, 203),
                            equipment=((16, 201), (5, 202), (17, 203)))],
    )
    candidate = HuntCandidate(
        status="caution", score=100, area_file="test.are", mobile_vnum=101,
        target="a soldier", target_keyword="soldier", level=25, room_vnum=301,
        room_name="a road", route=("north",), source_spawn_limit=1,
        room_spawn_count=1, boot_kills=0, loot=(), source_value=0,
        contained_coins=0, hazards=(), equipped_weapons=("a sword",),
        estimated_level_range=(23, 27), estimated_base_hp_range=(316, 945),
        estimated_peak_round_damage=414, estimated_critical_hit_damage=138,
        source_damage_modifier=0,
    )
    return candidate, world


def test_passive_wanderer_loadout_bounds_weapon_and_health_fuzz() -> None:
    candidate, world = loadout_fixture()
    loadout = single_weapon_loadout(candidate, world)
    assert loadout is not None
    assert loadout.weapon_vnum == 201
    assert loadout.damage_bonus == 3
    assert loadout.hitpoint_bonus == 13
    assert loadout.peak_damage(candidate) == 432
    assert loadout.critical_damage(candidate) == 144


def test_nonrandomised_loadout_keeps_exact_affects() -> None:
    candidate, world = loadout_fixture()
    world.objects = {vnum: replace(item, extra_flags=1 << 37)
                     for vnum, item in world.objects.items()}
    loadout = single_weapon_loadout(candidate, world)
    assert loadout is not None
    assert (loadout.damage_bonus, loadout.hitpoint_bonus) == (2, 10)


def test_target_sanctuary_reduces_normal_and_opening_output() -> None:
    candidate, world = loadout_fixture()
    world.mobiles[101] = replace(world.mobiles[101], affected_flags=1 << 7)
    loadout = single_weapon_loadout(candidate, world)
    assert loadout is not None and loadout.target_sanctuary
    output = SourceCombatOutput(
        "kick", 11, 21, 31, "actions", 0, 17, opening_action="backstab",
        opening_min_damage=19, opening_expected_damage=29,
        opening_max_damage=39, opening_conservative_damage=23,
    )
    limited = sanctuary_limited_output(output)
    assert (limited.minimum_damage, limited.expected_damage, limited.maximum_damage) == (5, 10, 15)
    assert limited.conservative_damage == 8
    assert (limited.opening_min_damage, limited.opening_expected_damage,
            limited.opening_max_damage, limited.opening_conservative_damage) == (9, 14, 19, 11)
    assert (limited.maximum_actions, limited.resource_cost) == (12, 0)


@pytest.mark.parametrize("change", [
    "capacity", "multiple_resets", "dual", "duplicate_slot", "aggressive",
    "scavenger", "special", "poisoned", "spell_item", "unknown_object",
    "critical", "swiftness", "fickle", "strong_randomiser", "wrong_weapon",
    "damage_mismatch", "rank", "protect", "battle_aura", "globe",
])
def test_uncertain_or_dangerous_loadout_is_not_admitted(change: str) -> None:
    candidate, world = loadout_fixture()
    reset = world.mob_resets[0]
    if change == "capacity":
        world.mob_resets[0] = replace(reset, maximum_count=2)
    elif change == "multiple_resets":
        world.mob_resets.append(replace(reset, room_vnum=302))
    elif change in {"dual", "duplicate_slot"}:
        world.mob_resets[0] = replace(reset, equipment=reset.equipment + (
            (18 if change == "dual" else 16, 201),))
    elif change in {"aggressive", "scavenger"}:
        world.mobiles[101] = replace(world.mobiles[101], act_flags=1 | (
            1 << 5 if change == "aggressive" else 1 << 2))
    elif change == "special":
        world.mobile_specials[101] = ("spec_poison",)
    elif change == "poisoned":
        world.objects[201] = replace(world.objects[201], extra_flags=1 << 14)
    elif change == "spell_item":
        world.objects[203] = replace(world.objects[203], item_type=4)
    elif change == "unknown_object":
        del world.objects[203]
    elif change in {"critical", "swiftness"}:
        world.objects[202] = replace(world.objects[202], affects=(
            (50 if change == "critical" else 51, 5),))
    elif change == "fickle":
        world.objects[201] = replace(world.objects[201], extra_flags=1 << 39)
    elif change == "strong_randomiser":
        world.mobiles[101] = replace(world.mobiles[101], level=42)
        candidate = replace(candidate, level=42)
    elif change == "wrong_weapon":
        candidate = replace(candidate, equipped_weapons=("a different sword",))
    elif change == "damage_mismatch":
        candidate = replace(candidate, source_damage_modifier=25)
    elif change == "rank":
        world.mobiles[101] = replace(world.mobiles[101], rank="boss")
    elif change in {"protect", "battle_aura", "globe"}:
        bit = {"protect": 13, "battle_aura": 22, "globe": 24}[change]
        world.mobiles[101] = replace(world.mobiles[101], affected_flags=1 << bit)
    assert single_weapon_loadout(candidate, world) is None
