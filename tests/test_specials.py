from dd4tester.specials import (
    CONDITIONAL_COMBAT_SPECIALS,
    ECONOMIC_SPECIALS,
    SAFE_NONCOMBAT_SPECIALS,
    WEAK_DEBILITATING_SPECIALS,
    WEAK_DIRECT_DAMAGE_SPECIALS,
    WEAK_EXTRA_ATTACK_SPECIALS,
    source_special_profile,
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


def test_special_profiles_distinguish_behavioral_risk() -> None:
    assert source_special_profile("spec_janitor").risk == "noncombat"
    assert source_special_profile("spec_thief").risk == "economic"
    assert source_special_profile("spec_poison").risk == "debilitating"
    assert source_special_profile("spec_guard").risk == "extra-attack"
    assert source_special_profile("spec_cast_judge").risk == "direct-damage"
    assert source_special_profile("spec_executioner").risk == "conditional-combat"


def test_special_classification_sets_are_explicit() -> None:
    assert "spec_cast_orb" in SAFE_NONCOMBAT_SPECIALS
    assert "spec_clan_guard" in CONDITIONAL_COMBAT_SPECIALS
    assert "spec_thief" in ECONOMIC_SPECIALS
    assert "spec_kungfu_poison" in WEAK_DEBILITATING_SPECIALS
    assert "spec_cast_judge" in WEAK_DIRECT_DAMAGE_SPECIALS
    assert "spec_bloodsucker" in WEAK_EXTRA_ATTACK_SPECIALS

