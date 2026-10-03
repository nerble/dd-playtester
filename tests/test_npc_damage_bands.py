import pytest

from dd4tester.hunt_candidates import (
    _mobile_critical_hit_damage,
    _mobile_normal_hit_damage,
    _mobile_peak_round_damage,
    mobile_expected_round_damage,
    mobile_sanctuary_critical_hit_damage,
    mobile_sanctuary_peak_round_damage,
)


@pytest.mark.parametrize("level,unarmed,armed", [
    (1, 1, 1), (29, 50, 75), (30, 60, 90), (31, 61, 91),
    (64, 128, 192), (65, 145, 217), (100, 225, 337),
])
def test_source_npc_level_bands_apply_before_weapon_multiplier(level, unarmed, armed):
    assert _mobile_normal_hit_damage(level, wielding=False) == unarmed
    assert _mobile_normal_hit_damage(level, wielding=True) == armed


@pytest.mark.parametrize("level,expected", [(29, 50), (30, 60), (65, 145)])
def test_round_critical_and_sanctuary_share_the_same_source_base(level, expected):
    args = dict(wielding=False, dual_wielding=False)
    assert _mobile_peak_round_damage(level, **args) == 6 * expected
    assert _mobile_critical_hit_damage(level, wielding=False) == 2 * expected
    assert mobile_sanctuary_peak_round_damage(level, **args) == 6 * (expected // 2)
    assert mobile_sanctuary_critical_hit_damage(level, wielding=False) == 2 * (expected // 2)


def test_damage_modifier_precedes_sanctuary_and_critical_at_band_transition():
    args = dict(wielding=False, damage_modifier=25)
    assert _mobile_critical_hit_damage(30, **args) == 150
    assert mobile_sanctuary_critical_hit_damage(30, **args) == 74
    assert mobile_sanctuary_peak_round_damage(30, dual_wielding=False, **args) == 222


@pytest.mark.parametrize("wielding,dual,expected", [
    (False, False, 106), (True, False, 159), (True, True, 301),
])
def test_expected_round_uses_level_thirty_bonus_for_each_weapon_roll(wielding, dual, expected):
    assert mobile_expected_round_damage(30, wielding=wielding, dual_wielding=dual) == expected


def test_unknown_modifier_is_still_not_assumed_neutral():
    assert _mobile_critical_hit_damage(30, wielding=False, damage_modifier=None) > 120
