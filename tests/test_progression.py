import pytest

from dd4tester.progression import CLASS_PRACTICE_SKILLS, policy_for


def test_starter_policy_is_executable_before_level_two() -> None:
    policy = policy_for(1, "mage")

    assert policy.policy_id == "starter-0-2"
    assert policy.executable is True
    assert policy.execution == "starter"


@pytest.mark.parametrize("character_class", sorted(CLASS_PRACTICE_SKILLS))
def test_level_two_to_six_policy_is_verified_and_executable(
    character_class: str,
) -> None:
    policy = policy_for(2, character_class)

    assert policy.policy_id == "mud-school-2-6"
    assert policy.status == "verified"
    assert policy.executable is True
    assert policy.execution == "arena"
    assert policy.practice_skill == CLASS_PRACTICE_SKILLS[character_class]
    assert any("Live run 76" in item for item in policy.evidence)
    assert any("Live run 82" in item for item in policy.evidence)


def test_level_six_to_ten_policy_uses_verified_bounded_arena_segments() -> None:
    policy = policy_for(6, "mage")

    assert policy.policy_id == "mud-school-6-10"
    assert policy.status == "verified"
    assert policy.execution == "arena"
    assert policy.segment_kill_limit == 10
    assert policy.executable is True
    assert any("Guildmaster" in item for item in policy.evidence)


def test_level_seven_mage_uses_verified_bounded_arena_after_moria_regression() -> None:
    policy = policy_for(7, "mage")

    assert policy.policy_id == "mud-school-6-10"
    assert policy.status == "verified"
    assert policy.execution == "arena"
    assert policy.segment_kill_limit == 10
    assert policy.executable is True


def test_level_seven_non_mage_keeps_the_arena_policy() -> None:
    policy = policy_for(7, "warrior")

    assert policy.policy_id == "mud-school-6-10"
    assert policy.execution == "arena"


def test_level_ten_and_above_is_explicitly_unavailable() -> None:
    policy = policy_for(10, "psionicist")

    assert policy.policy_id == "unregistered-10-100"
    assert policy.status == "unavailable"
    assert policy.practice_skill == "mind thrust"


def test_unknown_class_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown class"):
        policy_for(2, "illusionist")
