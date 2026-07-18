import pytest

from dd4tester.progression import CLASS_PRACTICE_SKILLS, policy_for


def test_starter_policy_is_executable_before_level_two() -> None:
    policy = policy_for(1, "mage")

    assert policy.policy_id == "starter-0-2"
    assert policy.executable is True
    assert policy.execution == "starter"


@pytest.mark.parametrize("character_class", sorted(CLASS_PRACTICE_SKILLS))
def test_level_two_to_ten_policy_is_registered_but_research_gated(
    character_class: str,
) -> None:
    policy = policy_for(2, character_class)

    assert policy.policy_id == "mud-school-2-10"
    assert policy.status == "research"
    assert policy.executable is False
    assert policy.practice_skill == CLASS_PRACTICE_SKILLS[character_class]
    assert any("Live run 56" in item for item in policy.evidence)


def test_level_ten_and_above_is_explicitly_unavailable() -> None:
    policy = policy_for(10, "psionicist")

    assert policy.policy_id == "unregistered-10-100"
    assert policy.status == "unavailable"
    assert policy.practice_skill == "mind thrust"


def test_unknown_class_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown class"):
        policy_for(2, "illusionist")
