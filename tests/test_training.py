from __future__ import annotations

from dd4tester.archetypes import archetype_registry
from dd4tester.prerequisites import known_skills, load_snapshot
from dd4tester.training import (
    class_training_analysis,
    parse_practice_listing,
    plan_training,
    prerequisite_class_for,
    prerequisite_classes_for,
    subclass_training_analysis,
    subclass_training_priorities,
    training_priorities,
    training_priorities_for,
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


def test_thief_stops_armed_gateway_at_exact_second_attack_threshold() -> None:
    armed = training_priorities()["thief"][0]

    assert armed.skill == "armed combat knowledge"
    assert armed.target_percent == 20
    assert "pre_req-thief.c" in " ".join(armed.source_refs)


def test_thief_keeps_improving_second_attack_after_the_initial_unlock() -> None:
    choices = plan_training(
        "thief",
        _listing(
            "second attack: 51%    dodge: 50%    hide: 23%",
            "stealth techniques: 56%",
            physical=2,
            intellectual=0,
        ),
        character_level=11,
    )

    assert [choice.skill for choice in choices] == ["second attack"]
    assert choices[0].target_percent == 100


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


def test_planner_preserves_a_practice_type_spent_by_an_earlier_segment() -> None:
    choices = plan_training(
        "warrior",
        _listing(
            "second attack: 42%    armed combat knowledge: 36%",
            "kick: 0%",
            physical=1,
            intellectual=0,
        ),
        excluded_practice_types=frozenset({"physical"}),
    )

    assert choices == ()


def test_thief_begins_source_prerequisite_chain_for_backstab() -> None:
    choices = plan_training(
        "thief",
        _listing(
            "hide: 23%",
            "stealth techniques: 0%",
            physical=0,
            intellectual=2,
        ),
    )

    assert [choice.skill for choice in choices] == ["stealth techniques"]
    assert choices[0].target_percent == 60


def test_thief_skips_persistently_capped_gateway_for_next_priority() -> None:
    choices = plan_training(
        "thief",
        _listing(
            "stealth techniques: 46%",
            "defense knowledge: 0%",
            physical=0,
            intellectual=2,
        ),
        excluded_skills=frozenset({"stealth techniques"}),
    )

    assert [choice.skill for choice in choices] == ["defense knowledge"]


def test_generic_thief_trains_hide_then_sneak_before_backstab() -> None:
    hide = plan_training(
        "thief",
        _listing(
            "armed combat knowledge: 40%",
            "hide: 0%    stealth techniques: 30%",
            physical=1,
            intellectual=0,
        ),
    )
    sneak = plan_training(
        "thief",
        _listing(
            "armed combat knowledge: 40%    hide: 30%    stealth techniques: 60%",
            "sneak: 0%",
            physical=1,
            intellectual=0,
        ),
    )

    assert [choice.skill for choice in hide] == ["hide"]
    assert [choice.skill for choice in sneak] == ["sneak"]


def test_thief_keeps_practising_backstab_when_its_teacher_offers_it() -> None:
    choices = plan_training(
        "thief",
        _listing(
            "armed combat knowledge: 41%    second attack: 37%    stealth techniques: 60%    sneak: 99%    backstab: 31%",
            "",
            physical=1,
            intellectual=0,
        ),
    )

    assert [choice.skill for choice in choices] == ["backstab"]
    assert choices[0].target_percent == 100


def test_thief_builds_disarm_chain_after_backstab() -> None:
    choices = plan_training(
        "thief",
        _listing(
            "armed combat knowledge: 70%    second attack: 40%    "
            "stealth techniques: 60%    hide: 30%    sneak: 99%    "
            "backstab: 100%    defense knowledge: 60%    dodge: 50%    "
            "parry: 40%",
            "disarm: 0%",
            physical=1,
            intellectual=0,
        ),
    )

    assert [choice.skill for choice in choices] == ["disarm"]
    assert choices[0].target_percent == 60


def test_thief_builds_circle_after_disarm_and_its_gateways() -> None:
    choices = plan_training(
        "thief",
        _listing(
            "armed combat knowledge: 70%    second attack: 40%    "
            "stealth techniques: 60%    hide: 30%    sneak: 99%    "
            "backstab: 100%    defense knowledge: 60%    dodge: 50%    "
            "parry: 40%    disarm: 60%    unarmed combat knowledge: 20%    "
            "trip: 70%",
            "circle: 0%",
            physical=1,
            intellectual=0,
        ),
    )

    assert [choice.skill for choice in choices] == ["circle"]
    assert choices[0].target_percent == 60


def test_warrior_builds_grip_chain_and_then_disarm() -> None:
    choices = plan_training(
        "warrior",
        _listing(
            "second attack: 50%    armed combat knowledge: 40%    "
            "enhanced damage: 100%    unarmed combat knowledge: 20%    "
            "kick: 30%    third attack: 50%    shield block: 40%    "
            "defense knowledge: 85%    dodge: 60%    parry: 60%    "
            "grip: 85%",
            "disarm: 0%",
            physical=1,
            intellectual=0,
        ),
    )

    assert [choice.skill for choice in choices] == ["disarm"]
    assert choices[0].target_percent == 60


def test_ranger_builds_grip_chain_and_then_disarm() -> None:
    choices = plan_training(
        "ranger",
        _listing(
            "armed combat knowledge: 20%    second attack: 35%    "
            "archery knowledge: 20%    shoot: 45%    "
            "defense knowledge: 75%    dodge: 70%    parry: 70%    "
            "grip: 75%",
            "disarm: 0%",
            physical=1,
            intellectual=0,
        ),
    )

    assert [choice.skill for choice in choices] == ["disarm"]
    assert choices[0].target_percent == 60


def test_vampire_builds_short_subclass_disarm_chain() -> None:
    choices = plan_training(
        "shifter",
        _listing(
            "armed combat knowledge: 75%    second attack: 45%",
            "disarm: 0%",
            physical=1,
            intellectual=0,
        ),
        subclass="vampire",
    )

    assert [choice.skill for choice in choices] == ["disarm"]
    assert choices[0].target_percent == 60


def test_warrior_prioritizes_enhanced_damage_after_its_gateway() -> None:
    choices = plan_training(
        "warrior",
        _listing(
            "armed combat knowledge: 40%    second attack: 37%    enhanced damage: 30%",
            "",
            physical=1,
            intellectual=0,
        ),
    )

    assert [choice.skill for choice in choices] == ["enhanced damage"]
    assert choices[0].target_percent == 100


def test_enhanced_hit_is_only_selected_when_the_trainer_lists_it() -> None:
    choices = plan_training(
        "warrior",
        _listing(
            "armed combat knowledge: 100%    second attack: 100%",
            "",
            physical=1,
            intellectual=0,
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


def test_every_class_has_an_operational_leveling_analysis() -> None:
    profiles = archetype_registry().classes
    analyses = class_training_analysis()

    assert analyses.keys() == profiles.keys()
    for class_name, analysis in analyses.items():
        assert analysis.strategy
        assert analysis.practice_policy
        assert analysis.highest_value_skills
        assert analysis.source_refs
        priorities = {item.skill for item in training_priorities()[class_name]}
        assert set(analysis.highest_value_skills) <= priorities


def test_every_subclass_has_source_backed_leveling_analysis() -> None:
    profiles = archetype_registry().subclasses
    priorities = subclass_training_priorities()
    analyses = subclass_training_analysis()

    assert priorities.keys() == profiles.keys()
    assert analyses.keys() == profiles.keys()
    for subclass, class_priorities in priorities.items():
        analysis = analyses[subclass]
        assert analysis.strategy
        assert analysis.practice_policy
        assert analysis.highest_value_skills
        assert analysis.source_refs
        assert set(analysis.highest_value_skills) <= {
            item.skill for item in class_priorities
        }
        assert all(item.source_refs for item in class_priorities)


def test_subclass_priorities_precede_inherited_base_priorities() -> None:
    priorities = training_priorities_for("thief", subclass="ninja")

    assert priorities[0].skill == "armed combat knowledge"
    assert priorities[0].target_percent == 90
    assert any(item.skill == "backstab" for item in priorities)


def test_subclass_plan_is_used_only_when_explicitly_active() -> None:
    listing = _listing(
        "backstab: 100%    second attack: 90%    third attack: 90%    "
        "advanced combat knowledge: 65%",
        "fourth attack: 0%    dodge: 0%",
        physical=1,
        intellectual=0,
    )

    base = plan_training("thief", listing)
    ninja = plan_training("thief", listing, subclass="ninja")

    assert [choice.skill for choice in base] == ["dodge"]
    assert [choice.skill for choice in ninja] == ["fourth attack"]


def test_subclass_prerequisite_aliases_match_source_snapshot_names() -> None:
    assert prerequisite_class_for("necromancer") == "necro"
    assert prerequisite_class_for("bounty hunter") == "bounty"
    assert prerequisite_class_for("martial artist") == "artist"
    assert prerequisite_classes_for("ninja") == ("ninja", "thief")
    assert prerequisite_classes_for("bounty hunter") == ("bounty", "thief")


def test_cross_class_plans_select_the_documented_early_level_value() -> None:
    cases = {
        "cleric": (
            _listing("", "healing magiks: 0%", physical=0, intellectual=1),
            "healing magiks",
        ),
        "psionic": (
            _listing("mind thrust: 12%", "", physical=0, intellectual=1),
            "mind thrust",
        ),
        "shifter": (
            _listing("second attack: 20%", "", physical=1, intellectual=0),
            "second attack",
        ),
        "brawler": (
            _listing("", "combat knowledge: 0%", physical=0, intellectual=1),
            "combat knowledge",
        ),
        "ranger": (
            _listing("", "armed combat knowledge: 0%", physical=0, intellectual=1),
            "armed combat knowledge",
        ),
        "smithy": (
            _listing("shield block: 20%", "", physical=1, intellectual=0),
            "shield block",
        ),
    }

    for class_name, (listing, expected) in cases.items():
        choices = plan_training(class_name, listing)
        assert [choice.skill for choice in choices] == [expected]


def test_cleric_adds_source_efficient_healing_after_damage_chain() -> None:
    choices = plan_training(
        "cleric",
        _listing(
            "healing magiks: 30%    harmful magiks: 30%    "
            "cause light: 30%    cause serious: 30%    cure light: 30%",
            "cure serious: 0%",
            physical=0,
            intellectual=1,
        ),
    )

    assert [choice.skill for choice in choices] == ["cure serious"]
    assert "4 plus 3d8" in choices[0].reason
    assert choices[0].target_percent == 30


def test_brawler_unlocks_punch_before_maxing_passive_damage() -> None:
    gateway = plan_training(
        "brawler",
        _listing(
            "combat knowledge: 40%",
            "pugilism knowledge: 0%",
            physical=0,
            intellectual=1,
        ),
    )
    punch = plan_training(
        "brawler",
        _listing(
            "combat knowledge: 40%    second attack: 35%    "
            "pugilism knowledge: 40%    enhanced damage: 25%",
            "punch: 0%",
            physical=1,
            intellectual=0,
        ),
    )

    assert [choice.skill for choice in gateway] == ["pugilism knowledge"]
    assert gateway[0].target_percent == 40
    assert [choice.skill for choice in punch] == ["punch"]
    assert punch[0].target_percent == 1


def test_item_or_form_dependent_damage_is_not_practised_prematurely() -> None:
    smithy = plan_training(
        "smithy",
        _listing(
            "shield block: 45%",
            "weaponsmithing: 0%    counterbalance: 0%    hurl: 0%",
            physical=1,
            intellectual=1,
        ),
        excluded_skills=frozenset({"weaponsmithing", "counterbalance"}),
    )
    shifter = plan_training(
        "shifter",
        _listing(
            "",
            "morphing knowledge: 0%    morph: 0%    cat form: 0%",
            physical=1,
            intellectual=1,
        ),
    )

    assert smithy == ()
    assert shifter == ()
    assert "form controller" in class_training_analysis()["shifter"].automation_gaps[0]


def test_prioritized_skills_exist_in_bundled_prerequisite_graph() -> None:
    _, prerequisites = load_snapshot()

    for class_name, class_priorities in training_priorities().items():
        source_skills = set(
            known_skills(prerequisites, class_name=class_name)
        )
        assert {item.source_skill for item in class_priorities} <= source_skills


def test_subclass_priorities_exist_in_subclass_or_inherited_graph() -> None:
    _, prerequisites = load_snapshot()

    for subclass, class_priorities in subclass_training_priorities().items():
        source_skills: set[str] = set()
        for source_class in prerequisite_classes_for(subclass):
            source_skills.update(
                known_skills(prerequisites, class_name=source_class)
            )
        assert {
            item.source_skill for item in class_priorities
        } <= source_skills, subclass


def test_kick_priority_records_source_verified_between_round_timing() -> None:
    kick = next(
        item
        for item in training_priorities()["warrior"]
        if item.skill == "kick"
    )

    assert "8-pulse wait" in kick.reason
    assert "without replacing 12-pulse automatic weapon rounds" in kick.reason


def test_matrix_training_analysis_carries_source_evidence() -> None:
    priorities = training_priorities()

    for class_name, class_priorities in priorities.items():
        assert any(item.automated for item in class_priorities)
        for item in class_priorities:
            assert item.source_refs, f"{class_name}:{item.skill} lacks evidence"
            assert any("server/" in ref for ref in item.source_refs)


def test_psionic_damage_plan_includes_both_psychic_crush_gateways() -> None:
    priorities = training_priorities()["psionic"]
    mind_thrust_index = next(
        index for index, item in enumerate(priorities)
        if item.skill == "mind thrust"
    )
    telepathy_index = next(
        index for index, item in enumerate(priorities)
        if item.skill == "telepathy disciplines"
    )
    crush_index = next(
        index for index, item in enumerate(priorities)
        if item.skill == "psychic crush"
    )

    assert mind_thrust_index < telepathy_index < crush_index
    assert priorities[telepathy_index].target_percent == 45
