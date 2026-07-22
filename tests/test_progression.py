import pytest

from dd4tester.progression import (
    CLASS_PRACTICE_SKILLS,
    ProgressionContext,
    policy_for,
    select_policy,
)


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
    assert policy.segment_kill_limit == 10
    assert policy.practice_skill == CLASS_PRACTICE_SKILLS[character_class]
    assert any("Live run 76" in item for item in policy.evidence)
    assert any("Live run 82" in item for item in policy.evidence)


@pytest.mark.parametrize("character_class", ["mage", "thief", "warrior"])
def test_level_six_policy_uses_verified_bounded_foundry_circuit(
    character_class: str,
) -> None:
    policy = policy_for(6, character_class)

    assert policy.policy_id == "foundry-circuit-6-7"
    assert policy.status == "verified"
    assert policy.execution == "foundry-hunt"
    assert policy.segment_kill_limit == 2
    assert policy.executable is True
    assert policy.practice_skill == CLASS_PRACTICE_SKILLS[character_class]
    assert any("Live run 572" in item for item in policy.evidence)


@pytest.mark.parametrize("character_class", ["mage", "thief", "warrior"])
def test_level_six_policy_falls_back_to_arena_after_empty_field_segment(
    character_class: str,
) -> None:
    policy = policy_for(6, character_class, stalled_segments=1)

    assert policy.policy_id == "mud-school-6-10"
    assert policy.execution == "arena"
    assert policy.segment_kill_limit == 10
    assert policy.practice_skill == CLASS_PRACTICE_SKILLS[character_class]


def test_level_six_policy_rotates_after_reboot_local_foundry_kills_degrade_xp() -> None:
    policy = policy_for(
        6,
        "mage",
        boot_kill_counts={
            "Olog": 3,
            "the Uburz": 3,
            "Ushog": 2,
            "the drunk": 4,
        },
    )

    assert policy.policy_id == "mud-school-6-10"
    assert policy.execution == "arena"


def test_level_six_policy_keeps_fresh_foundry_targets_below_rotation_limit() -> None:
    policy = policy_for(
        6,
        "warrior",
        boot_kill_counts={"Olog": 2, "Uburz": 2, "Ushog": 3},
    )

    assert policy.policy_id == "foundry-circuit-6-7"
    assert policy.execution == "foundry-hunt"


def test_level_seven_mage_uses_cross_class_foundry_policy() -> None:
    policy = policy_for(7, "mage")

    assert policy.policy_id == "foundry-circuit-7-8"
    assert policy.status == "verified"
    assert policy.execution == "foundry-hunt"
    assert policy.segment_kill_limit == 5
    assert policy.practice_skill == "magic missile"
    assert policy.executable is True


def test_level_seven_non_mage_uses_foundry_policy() -> None:
    policy = policy_for(7, "warrior")

    assert policy.policy_id == "foundry-circuit-7-8"
    assert policy.execution == "foundry-hunt"


@pytest.mark.parametrize("character_class", ["mage", "thief", "warrior"])
def test_level_seven_rotates_from_repeated_foundry_kills(
    character_class: str,
) -> None:
    policy = policy_for(
        7,
        character_class,
        boot_kill_counts={
            "Olog": 4,
            "the Oshu": 3,
            "Golgog": 2,
            "Uburz": 3,
            "mountain goblin": 1,
        },
    )

    assert policy.policy_id == "moria-garter-snake-7-8"
    assert policy.execution == "moria-snake-hunt"
    assert policy.segment_kill_limit == 1
    assert policy.practice_skill == CLASS_PRACTICE_SKILLS[character_class]


def test_level_seven_keeps_fresh_foundry_targets() -> None:
    policy = policy_for(
        7,
        "thief",
        boot_kill_counts={"Olog": 2, "Oshu": 2, "Uburz": 2},
    )

    assert policy.policy_id == "foundry-circuit-7-8"
    assert policy.execution == "foundry-hunt"


def test_level_seven_keeps_depleted_foundry_rotation_after_a_stalled_segment() -> None:
    policy = policy_for(
        7,
        "thief",
        boot_kill_counts={"Olog": 4, "Oshu": 4, "Uburz": 4},
        stalled_segments=1,
    )

    assert policy.policy_id == "moria-garter-snake-7-8"
    assert policy.execution == "moria-snake-hunt"


def test_stalled_level_seven_non_mage_uses_foundry_fallback() -> None:
    policy = policy_for(7, "thief", stalled_segments=1)

    assert policy.policy_id == "foundry-circuit-7-8"
    assert policy.execution == "foundry-hunt"
    assert policy.maximum_level == 8
    assert policy.practice_skill == "backstab"


def test_stalled_level_seven_mage_uses_foundry_fallback() -> None:
    policy = policy_for(7, "mage", stalled_segments=1)

    assert policy.policy_id == "foundry-circuit-7-8"
    assert policy.execution == "foundry-hunt"
    assert policy.practice_skill == "magic missile"


@pytest.mark.parametrize(
    ("character_class", "subclass", "practice_skill"),
    [
        ("mage", "warlock", "magic missile"),
        ("thief", "ninja", "backstab"),
        ("warrior", "knight", "kick"),
    ],
)
def test_representative_matrix_uses_data_driven_progression_context(
    character_class: str,
    subclass: str,
    practice_skill: str,
) -> None:
    context = ProgressionContext.from_values(
        5,
        character_class,
        subclass=subclass,
    )

    policy = select_policy(context)

    assert context.practice_skill == practice_skill
    assert policy.policy_id == "mud-school-2-6"
    assert policy.practice_skill == practice_skill


def test_level_eight_mage_collects_sack_before_resuming_hunts() -> None:
    sack = policy_for(8, "mage")
    hunt = policy_for(8, "mage", has_large_sack=True)

    assert sack.policy_id == "midennir-sack-8-10"
    assert sack.execution == "midennir-sack"
    assert sack.practice_skill == "invis"
    assert hunt.policy_id == "ambush-war-dog-8-9"
    assert hunt.execution == "ambush-war-dog-hunt"
    assert hunt.segment_kill_limit == 1


def test_level_eight_mage_rotates_from_repeated_dogs_to_midennir() -> None:
    policy = policy_for(
        8,
        "mage",
        has_large_sack=True,
        boot_kill_counts={"The war dog": 10, "the goblin": 3},
    )

    assert policy.policy_id == "midennir-goblin-8-10"
    assert policy.execution == "midennir-hunt"
    assert policy.segment_kill_limit == 1


def test_level_eight_mage_balances_reboot_scoped_hunt_repetition() -> None:
    policy = policy_for(
        8,
        "mage",
        has_large_sack=True,
        boot_kill_counts={"war dog": 10, "goblin": 10},
    )

    assert policy.policy_id == "ambush-war-dog-8-9"


def test_level_eight_mage_falls_back_after_empty_rotated_hunt() -> None:
    policy = policy_for(
        8,
        "mage",
        has_large_sack=True,
        boot_kill_counts={"war dog": 10, "goblin": 0},
        stalled_segments=1,
    )

    assert policy.policy_id == "ambush-war-dog-8-9"


def test_level_nine_mage_uses_proven_war_dog_without_protection() -> None:
    policy = policy_for(9, "mage", has_large_sack=True)

    assert policy.policy_id == "ambush-exterior-9-10"
    assert policy.execution == "ambush-hunt"
    assert policy.practice_skill == "chill touch"
    assert policy.segment_kill_limit == 1


def test_level_nine_mage_buys_flight_before_more_field_work() -> None:
    policy = policy_for(
        9,
        "mage",
        has_large_sack=True,
        has_flight=False,
        can_attempt_flight_purchase=True,
    )

    assert policy.policy_id == "buy-flight-potion"
    assert policy.execution == "buy-flight"


def test_level_nine_mage_buys_flight_before_spending_sanctuary_potion() -> None:
    policy = policy_for(
        9,
        "mage",
        has_large_sack=True,
        has_sanctuary_potion=True,
        has_flight=False,
        can_attempt_flight_purchase=True,
    )

    assert policy.policy_id == "buy-flight-potion"


def test_level_nine_mage_buys_flight_before_depleted_moria_circuit() -> None:
    policy = policy_for(
        9,
        "mage",
        has_large_sack=True,
        has_flight=False,
        can_attempt_flight_purchase=True,
        boot_kill_counts={"war dog": 16, "wounded goblin": 4},
    )

    assert policy.policy_id == "buy-flight-potion"


def test_failed_flight_purchase_does_not_loop() -> None:
    policy = policy_for(
        9,
        "mage",
        has_large_sack=True,
        has_flight=False,
        can_attempt_flight_purchase=True,
        flight_purchase_failed=True,
        stalled_segments=2,
    )

    assert policy.policy_id == "ambush-exterior-9-10"


def test_level_nine_mage_rotates_to_sanctuary_acquisition_after_depletion() -> None:
    policy = policy_for(
        9,
        "mage",
        has_large_sack=True,
        boot_kill_counts={"war dog": 16, "wounded goblin": 4},
    )

    assert policy.policy_id == "moria-sanctuary-9-10"
    assert policy.execution == "moria-sanctuary-hunt"
    assert policy.segment_kill_limit == 1


def test_level_nine_mage_spends_a_confirmed_sanctuary_potion_on_vile_goblin() -> None:
    policy = policy_for(
        9,
        "mage",
        has_large_sack=True,
        has_sanctuary_potion=True,
    )

    assert policy.policy_id == "ambush-vile-goblin-9-10"
    assert policy.execution == "ambush-vile-hunt"
    assert policy.segment_kill_limit == 1


def test_missing_sanctuary_carrier_falls_back_to_exterior_hunt() -> None:
    policy = policy_for(
        9,
        "mage",
        has_large_sack=True,
        boot_kill_counts={"war dog": 16, "wounded goblin": 4},
        stalled_segments=1,
    )

    assert policy.policy_id == "ambush-exterior-9-10"
    assert policy.execution == "ambush-hunt"


def test_missing_primary_weapon_selects_safe_rearm_maintenance() -> None:
    policy = policy_for(
        9,
        "mage",
        has_large_sack=True,
        has_weapon=False,
    )

    assert policy.policy_id == "rearm-primary-weapon"
    assert policy.execution == "rearm-weapon"


def test_sellable_loot_selects_safe_liquidation_before_the_next_hunt() -> None:
    policy = policy_for(
        8,
        "mage",
        has_large_sack=True,
        has_sellable_loot=True,
    )

    assert policy.policy_id == "liquidate-loot"
    assert policy.execution == "sell-loot"


def test_level_ten_mage_acquires_sanctuary_before_hunting() -> None:
    policy = policy_for(10, "mage", has_large_sack=True)

    assert policy.policy_id == "moria-sanctuary-10-11"
    assert policy.execution == "moria-sanctuary-hunt"
    assert policy.maximum_level == 11
    assert policy.segment_kill_limit == 1


def test_level_ten_mage_spends_confirmed_sanctuary_on_fresh_raider() -> None:
    policy = policy_for(
        10,
        "mage",
        has_large_sack=True,
        has_sanctuary_potion=True,
    )

    assert policy.policy_id == "ambush-goblin-raider-10-11"
    assert policy.execution == "ambush-raider-hunt"
    assert policy.maximum_level == 11


def test_level_ten_mage_rotates_from_repeated_raider_to_vile_goblin() -> None:
    policy = policy_for(
        10,
        "mage",
        has_large_sack=True,
        has_sanctuary_potion=True,
        boot_kill_counts={"goblin raider": 2, "vile goblin": 1},
    )

    assert policy.policy_id == "ambush-vile-goblin-10-11"
    assert policy.execution == "ambush-vile-hunt"
    assert policy.maximum_level == 11


def test_level_ten_mage_preserves_flight_maintenance() -> None:
    policy = policy_for(
        10,
        "mage",
        has_large_sack=True,
        has_flight=False,
        can_attempt_flight_purchase=True,
    )

    assert policy.policy_id == "buy-flight-potion"


def test_unregistered_class_at_level_ten_is_explicitly_unavailable() -> None:
    policy = policy_for(10, "psionicist")

    assert policy.policy_id == "unregistered-10-100"
    assert policy.status == "unavailable"
    assert policy.practice_skill == "mind thrust"


def test_unknown_class_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown class"):
        policy_for(2, "illusionist")
