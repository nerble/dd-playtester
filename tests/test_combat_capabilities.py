from dd4tester.archetypes import archetype_registry
from dd4tester.combat_capabilities import (
    combat_capabilities_for,
    combat_capability_names,
    combat_skill_names,
    combat_spell_names,
    SUBCLASS_COMBAT_CAPABILITIES,
)


def test_brawler_action_contract_is_shared_and_deduplicated() -> None:
    capabilities = combat_capabilities_for("BRAWLER", "monk")

    assert [capability.name for capability in capabilities] == [
        "agitation",
        "mind thrust",
        "headbutt",
        "punch",
    ]
    assert combat_spell_names("psionic") == (
        "psychic crush",
        "agitation",
        "mind thrust",
    )
    assert combat_capability_names("brawler", "monk") == (
        "agitation",
        "mind thrust",
        "headbutt",
        "punch",
    )
    assert combat_skill_names("ranger") == ("shoot", "kick", "disarm")
    assert combat_skill_names(
        "mage",
        observed_skills=("knife toss",),
    ) == ("knife toss",)


def test_mage_exposes_the_source_evocation_progression_in_damage_order() -> None:
    assert combat_spell_names("mage") == (
        "acid blast",
        "fireball",
        "lightning bolt",
        "shocking grasp",
        "colour spray",
        "burning hands",
        "chill touch",
        "magic missile",
    )


def test_infernalist_and_witch_expose_source_direct_damage_spells() -> None:
    assert combat_spell_names("psionic", "infernalist") == (
        "hellfire",
        "psychic crush",
        "agitation",
        "mind thrust",
    )
    assert combat_spell_names("psionic", "witch") == (
        "wither",
        "psychic crush",
        "agitation",
        "mind thrust",
    )
    assert combat_spell_names("mage", "witch") == combat_spell_names("mage")


def test_every_available_subclass_has_an_explicit_combat_contract() -> None:
    registry = archetype_registry()

    for subclass, profile in registry.subclasses.items():
        if not profile.available:
            continue
        assert subclass in SUBCLASS_COMBAT_CAPABILITIES
        capabilities = SUBCLASS_COMBAT_CAPABILITIES[subclass]
        assert capabilities
        assert all(item.source_reference for item in capabilities)


def test_subclass_actions_are_ignored_for_a_wrong_base_class() -> None:
    assert combat_capabilities_for("psionic", "monk") == combat_capabilities_for(
        "psionic"
    )
    assert combat_capabilities_for("psionic", "vampire") == combat_capabilities_for(
        "psionic"
    )


def test_thug_smash_is_shared_but_remains_unestimated_until_live_gated() -> None:
    capabilities = combat_capabilities_for("warrior", "thug")

    assert [capability.name for capability in capabilities] == [
        "smash",
        "stun",
        "headbutt",
        "kick",
        "disarm",
    ]
    assert combat_capabilities_for(
        "warrior",
        "thug",
        estimated_only=True,
    )[-1].name == "kick"


def test_unestimated_subclass_actions_are_visible_but_not_source_output() -> None:
    all_actions = combat_capabilities_for("shifter", "vampire")
    estimated = combat_capabilities_for(
        "shifter",
        "vampire",
        estimated_only=True,
    )

    assert [capability.name for capability in all_actions] == [
        "disarm",
        "suck",
        "lunge",
        "morph",
        "snake form",
    ]
    assert estimated == (all_actions[1],)


def test_straight_shifter_forms_are_setup_capabilities() -> None:
    capabilities = combat_capabilities_for("shifter")

    assert [(item.name, item.role) for item in capabilities] == [
        ("morph", "setup"),
        ("snake form", "setup"),
    ]
    assert combat_capabilities_for("shifter", estimated_only=True) == ()


def test_disarm_is_registered_as_control_only_for_armed_classes() -> None:
    for character_class, subclass in (
        ("thief", None),
        ("warrior", None),
        ("ranger", None),
        ("shifter", "vampire"),
    ):
        capability = next(
            item
            for item in combat_capabilities_for(character_class, subclass)
            if item.name == "disarm"
        )
        assert capability.kind == "skill"
        assert capability.estimated is False


def test_smithy_hurl_is_registered_but_not_estimated_without_object_evidence() -> None:
    capabilities = combat_capabilities_for("smithy")

    assert [(item.name, item.role, item.estimated) for item in capabilities] == [
        ("weaponchain", "setup", False),
        ("hurl", "damage", False),
    ]
    assert combat_skill_names("smithy") == ("weaponchain", "hurl")
    assert combat_capabilities_for("smithy", estimated_only=True) == ()


def test_thief_control_actions_are_visible_but_not_source_estimated() -> None:
    capabilities = combat_capabilities_for("thief")

    assert [capability.name for capability in capabilities] == [
        "circle",
        "knife toss",
        "dirt kick",
        "trip",
        "backstab",
        "disarm",
    ]
    assert combat_capabilities_for("thief", estimated_only=True) == capabilities[:2]


def test_observed_extra_skill_does_not_change_static_dispatch_contract() -> None:
    assert combat_skill_names("mage") == ()
    assert combat_skill_names("mage", observed_skills=("knife toss",)) == (
        "knife toss",
    )
