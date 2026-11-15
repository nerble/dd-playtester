import pytest

from dd4tester.equipment import has_recovery_resource_gain


@pytest.mark.parametrize("rank,expected", [
    ((0, 0, 0, 0, 5, 0, 0, 0), False),
    ((0, 0, 0, 2, 0, 0, 0, 0), False),
    ((20, 0, 20, 0, 0, 0, 0, 0), True),
    ((0, 20, 20, 0, 0, 0, 0, 0), True),
    ((-10, 50, 40, 0, 0, 0, 0, 0), False),
    ((), False),
])
def test_sleeping_gear_trip_needs_marginal_hp_or_mana(rank, expected):
    assert has_recovery_resource_gain(rank, level_gain_priorities=("hitpoints", "mana")) is expected


def test_mana_priority_retains_its_source_rank_order():
    assert has_recovery_resource_gain((50, -10, 40, 0), level_gain_priorities=("mana", "hitpoints"))
