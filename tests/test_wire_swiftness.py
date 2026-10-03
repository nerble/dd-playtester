import pytest

from dd4tester.hunt_candidates import (
    _source_weapon_expected_attacks, source_combat_output_estimate,
)


@pytest.mark.parametrize("wire,expected,maximum", [
    (None, 1.0, 1), (-5, 1.0, 1), (0, 1.0, 1), (1, 1.0, 1),
    (2, 1.01, 2), (25, 1.24, 2), (100, 1.99, 2), (101, 2.0, 2),
])
def test_wire_swiftness_is_a_total_with_strict_source_roll(wire, expected, maximum):
    attacks, ceiling = _source_weapon_expected_attacks(
        skills=frozenset({"enhanced swiftness"}),
        known_skill_levels={"enhanced swiftness": 80}, swiftness=wire,
    )
    assert attacks == pytest.approx(expected)
    assert ceiling == maximum


@pytest.mark.parametrize("extra", [{}, {"kick": 80}, {"headbutt": 80}])
def test_round_and_between_round_estimates_do_not_double_count_learned_bonus(extra):
    common = dict(
        character_level=29, character_class="warrior",
        weapon_damage_range=(5, 12), weapon_vnum=10014,
        player_damroll=20, player_swiftness=25,
    )
    without = source_combat_output_estimate(
        **common, known_skills=tuple(extra), known_skill_levels=extra,
    )
    with_skill = source_combat_output_estimate(
        **common, known_skills=(*extra, "enhanced swiftness"),
        known_skill_levels={**extra, "enhanced swiftness": 80},
    )
    assert with_skill == without


def test_hidden_wire_total_does_not_get_reconstructed_from_skill_names():
    common = dict(
        character_level=29, character_class="warrior", known_skills=("enhanced swiftness",),
        known_skill_levels={"enhanced swiftness": 100}, weapon_damage_range=(5, 12),
    )
    assert source_combat_output_estimate(**common, player_swiftness=50000) == source_combat_output_estimate(
        **common, player_swiftness=None,
    )
