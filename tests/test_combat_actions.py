import pytest

from dd4tester.combat_actions import preferred_timed_damage_skill
from dd4tester.hunt_candidates import BODY_NO_HEAD, source_combat_output_estimate


def test_run_16671_proficiencies_favor_kick_over_blind_rotation():
    assert preferred_timed_damage_skill(
        ("headbutt", "kick"), level=30,
        proficiency={"headbutt": 49, "kick": 61},
    ) == "kick"


def test_practiced_second_headbutt_can_change_the_preference():
    assert preferred_timed_damage_skill(
        ("headbutt", "kick"), level=30,
        proficiency={"headbutt": 49, "kick": 61, "second headbutt": 99},
    ) == "headbutt"


@pytest.mark.parametrize("level", [None, True, 0, 101, "30"])
def test_unknown_level_grants_no_timed_preference(level):
    assert preferred_timed_damage_skill(
        ("headbutt", "kick"), level=level,
        proficiency={"headbutt": 49, "kick": 61},
    ) is None


@pytest.mark.parametrize("percent", [None, True, 0, 1, -1, 101, 50000, "49", 49.5])
def test_unknown_or_unusable_proficiency_keeps_existing_selection(percent):
    assert preferred_timed_damage_skill(
        ("headbutt", "kick"), level=30,
        proficiency={"headbutt": percent, "kick": 61},
    ) is None


@pytest.mark.parametrize("available", [("kick",), ("headbutt",), (), ("unknown",)])
def test_timing_does_not_admit_an_unavailable_attack(available):
    assert preferred_timed_damage_skill(
        available, level=30, proficiency={"headbutt": 49, "kick": 61},
    ) is None


@pytest.mark.parametrize("second,expected", [(0, "kick"), (99, "headbutt")])
def test_source_output_uses_the_same_practiced_damage_action(second, expected):
    output = source_combat_output_estimate(
        character_level=30, character_class="warrior",
        known_skills=("headbutt", "kick", "second headbutt"),
        known_skill_levels={"headbutt": 49, "kick": 61, "second headbutt": second},
        weapon_damage_range=(5, 7), target_body_form_flags=0,
    )
    assert output is not None
    assert output.action == expected


def test_headless_target_does_not_gain_a_headbutt_from_its_timing_score():
    output = source_combat_output_estimate(
        character_level=30, character_class="warrior",
        known_skills=("headbutt", "kick", "second headbutt"),
        known_skill_levels={"headbutt": 99, "kick": 20, "second headbutt": 99},
        target_body_form_flags=BODY_NO_HEAD,
    )
    assert output is not None and output.action == "kick"
