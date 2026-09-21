from dd4tester.specials import (
    COMBAT_JOINING_SPECIALS,
    CONDITIONAL_COMBAT_SPECIALS,
    ECONOMIC_SPECIALS,
    SAFE_NONCOMBAT_SPECIALS,
    TRANSIT_HAZARD_SPECIALS,
    TRANSIT_SAFE_COMBAT_JOINING_SPECIALS,
    TRANSIT_SAFE_COMBAT_ONLY_SPECIALS,
    TRANSIT_SAFE_RELOCATION_SPECIALS,
    WEAK_DEBILITATING_SPECIALS,
    WEAK_DIRECT_DAMAGE_SPECIALS,
    WEAK_EXTRA_ATTACK_SPECIALS,
    source_special_is_transit_safe,
    source_special_profile,
    source_special_status_effects,
    source_special_xp_bonus,
)


def test_special_profiles_mirror_source_xp_bonus_tiers() -> None:
    assert source_special_xp_bonus("spec_fido") == 0
    assert source_special_xp_bonus("spec_thief") == 0
    assert source_special_xp_bonus("spec_poison") == 5
    assert source_special_xp_bonus("spec_warrior") == 10
    assert source_special_xp_bonus("spec_demon") == 15
    assert source_special_xp_bonus("spec_grail") == 20
    assert source_special_xp_bonus("spec_cast_mage") == 10
    assert source_special_xp_bonus("spec_wraith") == 10


def test_special_profiles_distinguish_behavioral_risk() -> None:
    assert source_special_profile("spec_janitor").risk == "noncombat"
    assert source_special_profile("spec_thief").risk == "economic"
    assert source_special_profile("spec_poison").risk == "debilitating"
    assert source_special_profile("spec_guard").risk == "extra-attack"
    assert source_special_profile("spec_cast_judge").risk == "direct-damage"
    assert source_special_profile("spec_executioner").risk == "conditional-combat"
    assert source_special_profile("spec_wraith").risk == "moderate-combat"


def test_special_classification_sets_are_explicit() -> None:
    assert "spec_cast_orb" in SAFE_NONCOMBAT_SPECIALS
    assert "spec_clan_guard" in CONDITIONAL_COMBAT_SPECIALS
    assert "spec_guard" in COMBAT_JOINING_SPECIALS
    assert "spec_sahuagin_guard" in COMBAT_JOINING_SPECIALS
    assert "spec_thief" in ECONOMIC_SPECIALS
    assert "spec_cast_undead" in TRANSIT_SAFE_COMBAT_ONLY_SPECIALS
    assert "spec_wraith" in TRANSIT_SAFE_COMBAT_ONLY_SPECIALS
    assert "spec_guard" in TRANSIT_SAFE_COMBAT_JOINING_SPECIALS
    assert "spec_spectral_minion" in TRANSIT_SAFE_RELOCATION_SPECIALS
    assert "spec_assassin" in TRANSIT_HAZARD_SPECIALS
    assert "spec_kungfu_poison" in WEAK_DEBILITATING_SPECIALS
    assert "spec_cast_judge" in WEAK_DIRECT_DAMAGE_SPECIALS
    assert "spec_bloodsucker" in WEAK_EXTRA_ATTACK_SPECIALS


def test_source_caster_profiles_expose_status_effects_from_special_c() -> None:
    assert source_special_status_effects("spec_breath_gas") == ("nausea",)
    assert source_special_status_effects("spec_cast_cleric") == (
        "blindness",
        "curse",
        "dispel magic",
    )
    assert "blindness" in source_special_profile("spec_cast_mage").status_effects
    assert source_special_status_effects("spec_assassin") == (
        "blindness",
        "trip",
    )
    assert source_special_status_effects("spec_wraith") == ("energy drain",)
    assert source_special_status_effects("spec_cast_druid", level=14) == ()
    assert source_special_status_effects("spec_cast_druid", level=15) == (
        "fear",
    )
    assert source_special_status_effects("spec_cast_psionicist", level=13) == ()
    assert source_special_status_effects("spec_cast_psionicist", level=35) == (
        "energy drain",
        "disintegrate",
    )
    assert source_special_status_effects("spec_demon", level=14) == (
        "curse",
        "chill touch",
        "burning hands",
        "strength drain",
    )
    assert source_special_status_effects("spec_demon", level=19)[-2:] == (
        "energy drain",
        "hold",
    )
    assert source_special_status_effects("spec_demon", level=50)[-3:] == (
        "gate",
        "hex",
        "fire breath",
    )


def test_mage_and_cleric_special_effects_follow_source_level_gates() -> None:
    assert source_special_status_effects("spec_cast_mage", level=6) == (
        "blindness",
    )
    assert source_special_status_effects("spec_cast_mage", level=19) == (
        "blindness",
        "weaken",
    )
    assert source_special_status_effects("spec_cast_mage", level=20) == (
        "blindness",
        "weaken",
        "dispel magic",
    )
    assert source_special_status_effects("spec_cast_mage", level=25)[-2:] == (
        "dispel magic",
        "energy drain",
    )
    assert source_special_status_effects("spec_cast_cleric", level=11) == (
        "blindness",
    )
    assert source_special_status_effects("spec_cast_cleric", level=12) == (
        "blindness",
        "curse",
    )
    assert source_special_status_effects("spec_cast_cleric", level=16) == (
        "blindness",
        "curse",
        "dispel magic",
    )


def test_undead_special_effects_follow_source_level_gates() -> None:
    assert source_special_status_effects("spec_cast_undead", level=8) == (
        "curse",
        "strength drain",
    )
    assert source_special_status_effects("spec_cast_undead", level=14) == (
        "curse",
        "strength drain",
        "blindness",
        "poison",
    )
    assert source_special_status_effects("spec_cast_undead", level=19)[-2:] == (
        "energy drain",
        "harm",
    )


def test_transit_special_audit_distinguishes_route_and_combat_risk() -> None:
    assert source_special_is_transit_safe("spec_cast_mage")
    assert source_special_is_transit_safe("spec_executioner")
    assert source_special_is_transit_safe("spec_guard")
    assert not source_special_is_transit_safe("spec_thief")
    assert not source_special_is_transit_safe("spec_assassin")
    assert source_special_is_transit_safe("spec_wraith")
    assert not source_special_is_transit_safe("spec_unknown")
