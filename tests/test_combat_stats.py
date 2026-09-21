from pathlib import Path

import pytest

from dd4tester.campaign import _source_ranked_caster_output_for_state
from dd4tester.hunt_candidates import (
    ITEM_WEAPON, ObjectSource, WorldSource, _observed_combat_stat,
    _source_dex_swiftness,
    source_combat_output_estimate,
)
from dd4tester.observations import ObservationParser
from dd4tester.state import replay_events


@pytest.mark.parametrize("value", [50000, "50000", 50000.0, None, True, "bad", float("inf"), float("nan")])
def test_unobserved_combat_stat_is_not_a_numeric_bonus(value):
    assert _observed_combat_stat(value) is None


@pytest.mark.parametrize("value", [-30, -1, 0, 5, 150])
def test_revealed_combat_stat_retains_its_sign(value):
    assert _observed_combat_stat(value) == value
    assert _observed_combat_stat(str(value)) == value


@pytest.mark.parametrize(
    ("current_dex", "expected"),
    [(3, -3), (15, 0), (18, 1), (27, 4), (31, 6)],
)
def test_source_dexterity_swiftness_matches_const_table(current_dex, expected):
    assert _source_dex_swiftness(current_dex) == expected


@pytest.mark.parametrize("current_dex", [None, 50000, "bad", True, -1, 32])
def test_unknown_source_dexterity_grants_no_swiftness(current_dex):
    assert _source_dex_swiftness(current_dex) is None


@pytest.mark.parametrize("character_class,skills", [
    ("warrior", {"kick": 35}), ("thief", {"circle": 35, "backstab": 35}),
])
def test_legacy_campaign_stats_use_the_same_sanitized_output(character_class, skills):
    parser = ObservationParser()
    fixture = Path(__file__).parent / "fixtures" / "dd4_gmcp.txt"
    state = replay_events([
        event for line in fixture.read_text(encoding="utf-8").splitlines()
        for event in parser.feed_gmcp(line)
    ]).to_dict()
    state.update(
        level=8, character_class=character_class,
        campaign_known_skills=list(skills), campaign_known_skill_levels=skills,
        equipment=[{"slot": "wield", "wear_loc": 16, "vnum": 3020, "item_type": ITEM_WEAPON}],
    )
    world = WorldSource(objects={
        3020: ObjectSource(3020, "dagger", "a dagger", ITEM_WEAPON, (0, 5, 7, 2), 10),
    })
    output = _source_ranked_caster_output_for_state(
        state, character_level=8, source_world=world, target_body_form_flags=0,
    )
    baseline = source_combat_output_estimate(
        character_level=8, character_class=character_class,
        known_skills=tuple(skills), known_skill_levels=skills,
        weapon_damage_range=(5, 7), weapon_vnum=3020, weapon_damage_type=2,
        player_damroll=0, player_swiftness=None, target_body_form_flags=0,
    )
    assert baseline is not None
    assert output == baseline
    assert state["stats"]["damroll"] == 50000


def test_revealed_damage_bonus_and_penalty_still_affect_the_plan():
    params = dict(
        character_level=20, character_class="warrior", known_skills=("kick",),
        known_skill_levels={"kick": 50}, weapon_damage_range=(5, 7),
    )
    penalty = source_combat_output_estimate(**params, player_damroll=-2)
    base = source_combat_output_estimate(**params, player_damroll=0)
    bonus = source_combat_output_estimate(**params, player_damroll=8)
    swift = source_combat_output_estimate(**params, player_damroll=8, player_swiftness=40)
    assert penalty.expected_damage < base.expected_damage < bonus.expected_damage < swift.expected_damage
