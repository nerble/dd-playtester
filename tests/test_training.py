from __future__ import annotations

from dd4tester.archetypes import archetype_registry
from dd4tester.prerequisites import known_skills, load_snapshot
from dd4tester.training import (
    parse_practice_listing,
    plan_training,
    training_priorities,
)


def _listing(
    known: str,
    learnable: str,
    *,
    physical: int,
    intellectual: int,
) -> str:
    return f"""
 Skills known:
{known}
 Skills which may be learned:
{learnable}
You have {physical} physical and {intellectual} intellectual practices remaining.
"""


def test_parse_practice_listing_separates_known_and_learnable() -> None:
    listing = parse_practice_listing(
        _listing(
            "magic missile: 23%    evocation magiks: 24%",
            "detect invis: 0%    protective magiks: 0%",
            physical=2,
            intellectual=1,
        )
    )

    assert listing.known == {"magic missile": 23, "evocation magiks": 24}
    assert listing.learnable == {"detect invis": 0, "protective magiks": 0}
    assert listing.physical_practices == 2
    assert listing.intellectual_practices == 1


def test_mage_prefers_stronger_damage_gateway_over_spell_reinforcement() -> None:
    choices = plan_training(
        "mage",
        _listing(
            "magic missile: 23%    evocation magiks: 24%",
            "detect invis: 0%    protective magiks: 0%",
            physical=2,
            intellectual=1,
        ),
    )

    assert [choice.skill for choice in choices] == ["evocation magiks"]
    assert choices[0].utility == "damage-gateway"


def test_warrior_spends_each_practice_type_on_combat_value() -> None:
    choices = plan_training(
        "warrior",
        _listing(
            "second attack: 22%    shield block: 22%    armed combat knowledge: 21%",
            "unarmed combat knowledge: 0%    defense knowledge: 0%",
            physical=1,
            intellectual=1,
        ),
    )

    assert [choice.skill for choice in choices] == [
        "second attack",
        "armed combat knowledge",
    ]


def test_thief_uses_intellectual_point_to_unlock_second_attack() -> None:
    choices = plan_training(
        "thief",
        _listing(
            "hide: 23%    sneak: 99%",
            "peek: 0%    stealth techniques: 0%    armed combat knowledge: 0%",
            physical=0,
            intellectual=1,
        ),
    )

    assert [choice.skill for choice in choices] == ["armed combat knowledge"]
    assert "unlocks second attack" in choices[0].reason


def test_planner_never_invents_a_skill_missing_from_trainer_listing() -> None:
    choices = plan_training(
        "warrior",
        _listing("shield block: 22%", "defense knowledge: 0%", physical=1, intellectual=0),
    )

    assert [choice.skill for choice in choices] == ["shield block"]


def test_planner_spends_at_most_one_practice_of_each_type_per_level() -> None:
    choices = plan_training(
        "mage",
        _listing(
            "magic missile: 23%    evocation magiks: 24%",
            "protective magiks: 0%    illusion magiks: 0%",
            physical=2,
            intellectual=4,
        ),
    )

    assert [choice.skill for choice in choices] == ["evocation magiks"]


def test_planner_preserves_points_for_unsupported_active_skill() -> None:
    choices = plan_training(
        "thief",
        _listing(
            "hide: 23%",
            "stealth techniques: 0%",
            physical=0,
            intellectual=2,
        ),
    )

    assert choices == ()


def test_every_supported_base_class_has_combat_training_priorities() -> None:
    profiles = archetype_registry().classes
    priorities = training_priorities()

    assert priorities.keys() == profiles.keys()
    for class_priorities in priorities.values():
        assert any(item.utility == "damage" for item in class_priorities)
        assert any(
            item.utility in {"mitigation", "sustain", "safety"}
            for item in class_priorities
        )


def test_prioritized_skills_exist_in_bundled_prerequisite_graph() -> None:
    _, prerequisites = load_snapshot()

    for class_name, class_priorities in training_priorities().items():
        source_skills = set(
            known_skills(prerequisites, class_name=class_name)
        )
        assert {item.source_skill for item in class_priorities} <= source_skills
