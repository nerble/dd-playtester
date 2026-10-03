from dataclasses import replace

import pytest

from dd4tester.excavation import hoard_guardian_damage, hoard_hex_inventory
from dd4tester.hunt_candidates import MobileSource, WorldSource


def guardian_world():
    return WorldSource(mobiles={83: MobileSource(
        83, "spirit guardian", "a spirit guardian", 64, 98, -1000, "limbo.are",
        affected_flags=1572904, body_form_flags=336,
    )})


def test_guardian_uses_dynamic_level_and_explicit_extra_damroll():
    result = hoard_guardian_damage(guardian_world(), character_level=29)
    assert (result.level, result.maximum_hp) == (29, 390)
    assert (result.maximum_ordinary_hit, result.maximum_critical_hit) == (64, 128)
    assert (result.expected_round_damage, result.maximum_peak_round_damage) == (114, 384)
    assert result.ordinary_peak_round == 384
    assert result.all_critical_peak_round == 768


def test_guardian_retains_source_level_thirty_damage_increase():
    result = hoard_guardian_damage(guardian_world(), character_level=30)
    assert result.maximum_ordinary_hit == 75
    assert result.expected_round_damage == 141
    assert result.maximum_hp == 400


@pytest.mark.parametrize("wait_pulses,rounds", [(0, 1), (1, 2), (11, 2), (12, 2),
                                                (13, 3), (24, 3)])
def test_guardian_window_includes_immediate_burst_and_unobserved_violence_phase(
    wait_pulses, rounds,
):
    result = hoard_guardian_damage(guardian_world(), character_level=29)
    assert result.maximum_attack_rounds_before_command(wait_pulses) == rounds
    assert result.maximum_damage_before_command(wait_pulses) == rounds * 384
    assert result.maximum_damage_before_command(wait_pulses, every_hit_critical=True) == rounds * 768


@pytest.mark.parametrize("wait_pulses", [-1, 1.5, True, None])
def test_guardian_window_rejects_incomplete_or_invalid_wait(wait_pulses):
    result = hoard_guardian_damage(guardian_world(), character_level=29)
    with pytest.raises(ValueError):
        result.maximum_attack_rounds_before_command(wait_pulses)


def test_guardian_scales_damroll_before_modifier_then_sanctuary_then_critical():
    world = guardian_world()
    world.mobiles[83] = replace(world.mobiles[83], damage_modifier=25)
    result = hoard_guardian_damage(world, character_level=30, sanctuary=True)
    assert (result.maximum_ordinary_hit, result.maximum_critical_hit) == (37, 74)


def test_guardian_level_clamps_but_does_not_inherit_prototype_hp():
    result = hoard_guardian_damage(guardian_world(), character_level=100)
    assert (result.level, result.maximum_hp) == (99, 1090)


@pytest.mark.parametrize("changes", [
    {"damage_modifier": None}, {"damage_modifier_known": False},
    {"template_name": "changed"}, {"act_flags": 0},
    {"affected_flags": 0}, {"body_form_flags": None},
])
def test_changed_or_unknown_guardian_profile_stays_closed(changes):
    world = guardian_world()
    world.mobiles[83] = replace(world.mobiles[83], **changes)
    with pytest.raises(ValueError):
        hoard_guardian_damage(world, character_level=29)


def test_missing_or_new_special_guardian_is_not_an_ordinary_enemy():
    with pytest.raises(ValueError):
        hoard_guardian_damage(WorldSource(), character_level=29)
    world = guardian_world()
    world.mobile_specials[83] = ("spec_poison",)
    with pytest.raises(ValueError):
        hoard_guardian_damage(world, character_level=29)


def test_hex_lowers_pickup_limits_but_has_no_carry_to_walk_rule():
    result = hoard_hex_inventory(character_level=29, strength=30, dexterity=16)
    assert (result.minimum_strength, result.minimum_dexterity) == (23, 9)
    assert (result.carry_weight_limit, result.carry_number_limit) == (800, 31)
    assert result.wield_weight_limit == 50
    assert not result.weapon_drop_risk(primary_weight=50, dual_weight=None)
    assert result.weapon_drop_risk(primary_weight=51, dual_weight=None)


def test_hex_weapon_check_uses_dual_only_when_no_primary_is_present():
    result = hoard_hex_inventory(character_level=29, strength=30, dexterity=16)
    assert not result.weapon_drop_risk(primary_weight=50, dual_weight=51)
    assert result.weapon_drop_risk(primary_weight=None, dual_weight=51)
    assert not result.weapon_drop_risk(primary_weight=None, dual_weight=None)


def test_hex_stats_bottom_out_at_source_minimum_three():
    result = hoard_hex_inventory(character_level=100, strength=3, dexterity=3)
    assert (result.minimum_strength, result.minimum_dexterity) == (3, 3)
    assert (result.carry_weight_limit, result.carry_number_limit, result.wield_weight_limit) == (10, 25, 3)


@pytest.mark.parametrize("bad", [None, True, 50000, 0, 32])
def test_hex_requires_revealed_integer_stats(bad):
    with pytest.raises(ValueError):
        hoard_hex_inventory(character_level=29, strength=bad, dexterity=16)


@pytest.mark.parametrize("weight", [True, -1, 50000, "50"])
def test_unknown_instance_weapon_weight_is_not_a_retention_proof(weight):
    result = hoard_hex_inventory(character_level=29, strength=30, dexterity=16)
    with pytest.raises(ValueError):
        result.weapon_drop_risk(primary_weight=weight, dual_weight=None)
