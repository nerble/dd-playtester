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
def test_level_six_policy_uses_verified_arena_after_foundry_retirement(
    character_class: str,
) -> None:
    policy = policy_for(6, character_class)

    assert policy.policy_id == "mud-school-6-10"
    assert policy.status == "verified"
    assert policy.execution == "arena"
    assert policy.segment_kill_limit == 10
    assert policy.executable is True
    assert policy.practice_skill == CLASS_PRACTICE_SKILLS[character_class]
    assert any("Live run 82" in item for item in policy.evidence)


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
            "the Uburz": 5,
            "the drunk": 4,
        },
    )

    assert policy.policy_id == "mud-school-6-10"
    assert policy.execution == "arena"


def test_level_six_policy_ignores_foundry_kill_history_after_retirement() -> None:
    policy = policy_for(
        6,
        "warrior",
        boot_kill_counts={"Olog": 2, "Uburz": 3},
    )

    assert policy.policy_id == "mud-school-6-10"
    assert policy.execution == "arena"


def test_level_seven_mage_starts_with_daycare_after_foundry_retirement() -> None:
    policy = policy_for(7, "mage")

    assert policy.policy_id == "daycare-nanny-circuit-7-8"
    assert policy.status == "verified"
    assert policy.execution == "daycare-nanny-hunt"
    assert policy.segment_kill_limit == 2
    assert policy.practice_skill == "magic missile"
    assert policy.executable is True


def test_level_seven_non_mage_starts_with_daycare_policy() -> None:
    policy = policy_for(7, "warrior")

    assert policy.policy_id == "daycare-nanny-circuit-7-8"
    assert policy.execution == "daycare-nanny-hunt"


@pytest.mark.parametrize("character_class", ["mage", "thief", "warrior"])
def test_level_seven_ignores_retired_foundry_kill_history(
    character_class: str,
) -> None:
    policy = policy_for(
        7,
        character_class,
        boot_kill_counts={
            "Lobuk": 4,
            "Shargook": 3,
            "Golgog": 2,
            "Uburz": 3,
            "mountain goblin": 1,
        },
    )

    assert policy.policy_id == "daycare-nanny-circuit-7-8"
    assert policy.execution == "daycare-nanny-hunt"
    assert policy.segment_kill_limit == 2
    assert policy.practice_skill == CLASS_PRACTICE_SKILLS[character_class]


def test_level_seven_does_not_select_fresh_retired_foundry_targets() -> None:
    policy = policy_for(
        7,
        "thief",
        boot_kill_counts={"Lobuk": 2, "Golgog": 2, "Uburz": 2},
    )

    assert policy.policy_id == "daycare-nanny-circuit-7-8"
    assert policy.execution == "daycare-nanny-hunt"


def test_level_seven_uses_daycare_after_a_stalled_segment() -> None:
    policy = policy_for(
        7,
        "thief",
        boot_kill_counts={"Lobuk": 4, "Golgog": 4, "Uburz": 4},
        stalled_segments=1,
    )

    assert policy.policy_id == "daycare-nanny-circuit-7-8"
    assert policy.execution == "daycare-nanny-hunt"


def test_level_seven_rotates_to_moria_after_two_nannies() -> None:
    policy = policy_for(
        7,
        "warrior",
        boot_kill_counts={
            "Lobuk": 4,
            "Golgog": 4,
            "Uburz": 4,
            "the nanny": 2,
        },
    )

    assert policy.policy_id == "moria-orc-circuit-7-8"
    assert policy.execution == "moria-orc-hunt"


def test_level_seven_rotates_from_daycare_to_moria() -> None:
    policy = policy_for(
        7,
        "warrior",
        boot_kill_counts={"Lobuk": 4, "Golgog": 4, "Uburz": 4},
        stalled_segments=2,
        last_policy_id="daycare-nanny-circuit-7-8",
    )

    assert policy.policy_id == "moria-orc-circuit-7-8"
    assert policy.execution == "moria-orc-hunt"


def test_level_seven_uses_circus_sweep_after_nanny_policy_loses_xp() -> None:
    policy = policy_for(
        7,
        "thief",
        last_policy_id="moria-orc-circuit-7-8",
        policy_xp_deltas={"daycare-nanny-circuit-7-8": -46},
    )

    assert policy.policy_id == "circus-illusionist-7-8"
    assert policy.execution == "circus-freak-show-hunt"
    assert policy.segment_kill_limit == 3


@pytest.mark.parametrize(
    "last_policy_id",
    ("circus-illusionist-7-8", "moria-orc-circuit-7-8"),
)
def test_level_seven_rotates_from_empty_circus_to_gnome_hermit(
    last_policy_id: str,
) -> None:
    policy = policy_for(
        7,
        "warrior",
        last_policy_id=last_policy_id,
        policy_xp_deltas={
            "daycare-nanny-circuit-7-8": -46,
            "circus-illusionist-7-8": 0,
        },
    )

    assert policy.policy_id == "gnome-hermit-7-8"
    assert policy.execution == "gnome-hermit-hunt"
    assert policy.practice_skill == "kick"


def test_level_seven_skips_recently_empty_moria_after_productive_circus() -> None:
    policy = policy_for(
        7,
        "warrior",
        last_policy_id="circus-illusionist-7-8",
        policy_xp_deltas={
            "circus-illusionist-7-8": 132,
            "moria-orc-circuit-7-8": 0,
        },
    )

    assert policy.policy_id == "gnome-hermit-7-8"
    assert policy.execution == "gnome-hermit-hunt"


def test_level_seven_caster_uses_gnome_guard_when_established_circuits_are_empty() -> None:
    policy = policy_for(
        7,
        "mage",
        last_policy_id="circus-illusionist-7-8",
        policy_xp_deltas={
            "circus-illusionist-7-8": 0,
            "gnome-hermit-7-8": 0,
            "moria-orc-circuit-7-8": 0,
        },
    )

    assert policy.policy_id == "gnome-guard-caster-7-8"
    assert policy.execution == "gnome-guard-hunt"
    assert policy.segment_kill_limit == 1


def test_level_seven_caster_uses_daycare_after_productive_circus() -> None:
    policy = policy_for(
        7,
        "mage",
        last_policy_id="circus-illusionist-7-8",
        policy_xp_deltas={
            "circus-illusionist-7-8": 209,
            "gnome-hermit-7-8": 0,
            "moria-orc-circuit-7-8": 0,
        },
    )

    assert policy.policy_id == "daycare-armed-guard-7-8"
    assert policy.execution == "daycare-armed-guard-hunt"


def test_level_seven_caster_rotates_from_daycare_to_gnome() -> None:
    policy = policy_for(
        7,
        "mage",
        last_policy_id="daycare-armed-guard-7-8",
    )

    assert policy.policy_id == "gnome-hermit-7-8"
    assert policy.execution == "gnome-hermit-hunt"


def test_level_seven_caster_rechecks_circus_after_depleted_fallback_cycle() -> None:
    policy = policy_for(
        7,
        "mage",
        last_policy_id="daycare-armed-guard-7-8",
        policy_xp_deltas={
            "circus-illusionist-7-8": 0,
            "gnome-hermit-7-8": 0,
            "moria-orc-circuit-7-8": 0,
        },
    )

    assert policy.policy_id == "circus-illusionist-7-8"
    assert policy.execution == "circus-freak-show-hunt"


def test_level_seven_caster_uses_troll_after_depleted_gnome_guard() -> None:
    policy = policy_for(
        7,
        "mage",
        last_policy_id="gnome-guard-caster-7-8",
        policy_xp_deltas={
            "circus-illusionist-7-8": 0,
            "gnome-hermit-7-8": 0,
            "moria-orc-circuit-7-8": 0,
        },
    )

    assert policy.policy_id == "gnome-small-troll-caster-7-8"
    assert policy.execution == "gnome-small-troll-hunt"
    assert policy.segment_kill_limit == 1


def test_level_seven_caster_rotates_from_troll_to_ambush_war_dog() -> None:
    policy = policy_for(
        7,
        "mage",
        last_policy_id="gnome-small-troll-caster-7-8",
        policy_xp_deltas={
            "circus-illusionist-7-8": 0,
            "gnome-hermit-7-8": 0,
            "moria-orc-circuit-7-8": 0,
        },
    )

    assert policy.policy_id == "ambush-war-dog-caster-7-8"
    assert policy.execution == "ambush-war-dog-hunt"
    assert policy.segment_kill_limit == 1


def test_level_seven_caster_rotates_from_ambush_to_daycare_hunt() -> None:
    policy = policy_for(
        7,
        "mage",
        last_policy_id="ambush-war-dog-caster-7-8",
        policy_xp_deltas={
            "circus-illusionist-7-8": 0,
            "gnome-hermit-7-8": 0,
            "moria-orc-circuit-7-8": 0,
        },
    )

    assert policy.policy_id == "daycare-armed-guard-7-8"
    assert policy.execution == "daycare-armed-guard-hunt"


def test_level_seven_rotates_from_shire_to_moria() -> None:
    policy = policy_for(
        7,
        "mage",
        boot_kill_counts={"Lobuk": 4, "Golgog": 4, "Uburz": 4},
        last_policy_id="shire-bull-7-8",
    )

    assert policy.policy_id == "moria-orc-circuit-7-8"
    assert policy.execution == "moria-orc-hunt"


def test_level_seven_rotates_retired_shire_checkpoint_to_moria() -> None:
    policy = policy_for(
        7,
        "warrior",
        boot_kill_counts={"Lobuk": 4, "Golgog": 4, "Uburz": 4},
        last_policy_id="shire-bull-warrior-7-8",
    )

    assert policy.policy_id == "moria-orc-circuit-7-8"
    assert policy.execution == "moria-orc-hunt"


def test_level_seven_keeps_shire_fallback_research_gated_after_midennir() -> None:
    for character_class in ("thief", "warrior"):
        policy = policy_for(
            7,
            character_class,
            boot_kill_counts={"Lobuk": 4, "Golgog": 4, "Uburz": 4},
            last_policy_id="midennir-goblin-7-8",
        )

        assert policy.policy_id == "daycare-nanny-circuit-7-8"
        assert policy.execution == "daycare-nanny-hunt"


def test_level_seven_rotates_from_moria_to_gnome_hermit() -> None:
    policy = policy_for(
        7,
        "thief",
        boot_kill_counts={"Lobuk": 4, "Golgog": 4, "Uburz": 4},
        last_policy_id="moria-orc-circuit-7-8",
    )

    assert policy.policy_id == "gnome-hermit-7-8"
    assert policy.execution == "gnome-hermit-hunt"
    assert policy.segment_kill_limit == 3


def test_level_seven_thief_repeats_evidenced_hermit_before_general_rotation() -> None:
    policy = policy_for(
        7,
        "thief",
        boot_kill_counts={
            "Lobuk": 4,
            "Golgog": 4,
            "Uburz": 4,
            "hermit": 1,
        },
        last_policy_id="moria-orc-circuit-7-8",
    )

    assert policy.policy_id == "gnome-hermit-7-8"
    assert policy.execution == "gnome-hermit-hunt"


def test_level_seven_thief_returns_to_general_rotation_after_nine_hermit_kills() -> None:
    policy = policy_for(
        7,
        "thief",
        boot_kill_counts={
            "Lobuk": 4,
            "Golgog": 4,
            "Uburz": 4,
            "hermit": 9,
        },
        last_policy_id="gnome-hermit-7-8",
    )

    assert policy.policy_id == "daycare-nanny-circuit-7-8"
    assert policy.execution == "daycare-nanny-hunt"


def test_level_seven_thief_does_not_return_to_depleted_hermit_after_moria() -> None:
    policy = policy_for(
        7,
        "thief",
        boot_kill_counts={
            "Lobuk": 4,
            "Golgog": 4,
            "Uburz": 4,
            "hermit": 9,
        },
        last_policy_id="moria-orc-circuit-7-8",
    )

    assert policy.policy_id == "daycare-nanny-circuit-7-8"
    assert policy.execution == "daycare-nanny-hunt"


def test_level_seven_rotates_to_daycare_after_a_zero_xp_field_route() -> None:
    policy = policy_for(
        7,
        "thief",
        boot_kill_counts={"Lobuk": 4, "Golgog": 4, "Uburz": 4},
        policy_xp_deltas={"gnome-hermit-7-8": 0},
        last_policy_id="gnome-hermit-7-8",
    )

    assert policy.policy_id == "daycare-nanny-circuit-7-8"
    assert policy.execution == "daycare-nanny-hunt"


def test_level_seven_does_not_resume_a_retired_foundry_checkpoint() -> None:
    policy = policy_for(
        7,
        "thief",
        boot_kill_counts={"Lobuk": 4, "Golgog": 4, "Uburz": 4},
        policy_xp_deltas={"foundry-circuit-7-8": 170},
        last_policy_id="foundry-circuit-7-8",
    )

    assert policy.policy_id == "daycare-nanny-circuit-7-8"
    assert policy.execution == "daycare-nanny-hunt"


def test_level_seven_rotates_from_gnome_hermit_to_daycare() -> None:
    policy = policy_for(
        7,
        "mage",
        boot_kill_counts={"Lobuk": 4, "Golgog": 4, "Uburz": 4},
        last_policy_id="gnome-hermit-7-8",
    )

    assert policy.policy_id == "daycare-nanny-circuit-7-8"
    assert policy.execution == "daycare-nanny-hunt"


def test_level_seven_buys_flight_before_depleted_moria_rotation() -> None:
    policy = policy_for(
        7,
        "thief",
        boot_kill_counts={"Lobuk": 4, "Golgog": 4, "Uburz": 4},
        has_flight=False,
        can_attempt_flight_purchase=True,
    )

    assert policy.policy_id == "buy-flight-potion"
    assert policy.execution == "buy-flight"


def test_stalled_level_seven_non_mage_uses_daycare_fallback() -> None:
    policy = policy_for(7, "thief", stalled_segments=1)

    assert policy.policy_id == "daycare-nanny-circuit-7-8"
    assert policy.execution == "daycare-nanny-hunt"
    assert policy.maximum_level == 8
    assert policy.practice_skill == "backstab"


def test_stalled_level_seven_mage_uses_daycare_fallback() -> None:
    policy = policy_for(7, "mage", stalled_segments=1)

    assert policy.policy_id == "daycare-nanny-circuit-7-8"
    assert policy.execution == "daycare-nanny-hunt"
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


@pytest.mark.parametrize(
    ("character_class", "practice_skill"),
    (("thief", "backstab"), ("warrior", "kick")),
)
def test_level_eight_martial_classes_leave_exhausted_mud_school(
    character_class: str,
    practice_skill: str,
) -> None:
    policy = policy_for(8, character_class)

    assert policy.policy_id == "circus-freak-show-8-9"
    assert policy.execution == "circus-freak-show-hunt"
    assert policy.practice_skill == practice_skill
    assert policy.segment_kill_limit == 3
    assert policy.maximum_level == 9


def test_level_eight_martial_rotates_from_circus_to_isolated_moria_orc() -> None:
    policy = policy_for(
        8,
        "thief",
        last_policy_id="circus-freak-show-8-9",
    )

    assert policy.policy_id == "moria-large-orc-8-9"
    assert policy.execution == "moria-large-orc-hunt"
    assert policy.practice_skill == "backstab"
    assert policy.segment_kill_limit == 1


def test_level_eight_martial_rotates_from_moria_to_gnome_guards() -> None:
    policy = policy_for(
        8,
        "warrior",
        last_policy_id="moria-large-orc-8-9",
    )

    assert policy.policy_id == "gnome-guard-circuit-8-9"
    assert policy.execution == "gnome-guard-hunt"
    assert policy.practice_skill == "kick"
    assert policy.segment_kill_limit == 3


def test_level_eight_martial_hunts_daycare_after_gnome_guards() -> None:
    policy = policy_for(
        8,
        "thief",
        last_policy_id="gnome-guard-circuit-8-9",
    )

    assert policy.policy_id == "daycare-armed-guard-8-9"
    assert policy.execution == "daycare-armed-guard-hunt"
    assert policy.segment_kill_limit == 1


def test_level_eight_martial_hunts_ambush_exterior_after_daycare() -> None:
    policy = policy_for(
        8,
        "thief",
        last_policy_id="daycare-armed-guard-8-9",
    )

    assert policy.policy_id == "ambush-martial-exterior-8-9"
    assert policy.execution == "ambush-martial-hunt"
    assert policy.segment_kill_limit == 3


def test_level_eight_martial_returns_to_circus_after_ambush_exterior() -> None:
    policy = policy_for(
        8,
        "thief",
        last_policy_id="ambush-martial-exterior-8-9",
    )

    assert policy.policy_id == "circus-freak-show-8-9"
    assert policy.execution == "circus-freak-show-hunt"


def test_level_eight_martial_returns_to_circus_after_fleshmonger_research() -> None:
    policy = policy_for(
        8,
        "thief",
        last_policy_id="fleshmonger-guard-research-8-9",
    )

    assert policy.policy_id == "circus-freak-show-8-9"
    assert policy.execution == "circus-freak-show-hunt"


def test_level_eight_martial_returns_to_circus_after_cult_research() -> None:
    policy = policy_for(
        8,
        "thief",
        last_policy_id="cult-fanatic-research-8-9",
    )

    assert policy.policy_id == "circus-freak-show-8-9"
    assert policy.execution == "circus-freak-show-hunt"


def test_level_nine_martial_continues_with_objective_level_ten_policy() -> None:
    policy = policy_for(
        9,
        "thief",
        last_policy_id="daycare-armed-guard-8-9",
    )

    assert policy.policy_id == "ambush-martial-exterior-9-10"
    assert policy.execution == "ambush-martial-hunt"
    assert policy.minimum_level == 9
    assert policy.maximum_level == 10


def test_level_eight_martial_buys_flight_before_field_rotation() -> None:
    policy = policy_for(
        8,
        "warrior",
        has_flight=False,
        can_attempt_flight_purchase=True,
    )

    assert policy.policy_id == "buy-flight-potion"
    assert policy.execution == "buy-flight"


def test_level_nine_martial_buys_flight_before_field_rotation() -> None:
    policy = policy_for(
        9,
        "thief",
        has_flight=False,
        can_attempt_flight_purchase=True,
    )

    assert policy.policy_id == "buy-flight-potion"
    assert policy.execution == "buy-flight"


def test_failed_martial_flight_purchase_returns_to_field_rotation() -> None:
    policy = policy_for(
        8,
        "warrior",
        has_flight=False,
        can_attempt_flight_purchase=True,
        flight_purchase_failed=True,
        last_policy_id="ambush-martial-exterior-8-9",
    )

    assert policy.policy_id == "circus-freak-show-8-9"
    assert policy.execution == "circus-freak-show-hunt"


def test_level_nine_martial_rotates_across_verified_field_circuits() -> None:
    expected = (
        ("ambush-martial-exterior-9-10", "circus-freak-show-9-10"),
        ("circus-freak-show-9-10", "moria-large-orc-9-10"),
        ("moria-large-orc-9-10", "gnome-guard-circuit-9-10"),
        ("gnome-guard-circuit-9-10", "daycare-armed-guard-9-10"),
        ("daycare-armed-guard-9-10", "ambush-martial-exterior-9-10"),
    )

    for previous_policy, expected_policy in expected:
        policy = policy_for(
            9,
            "warrior",
            last_policy_id=previous_policy,
        )
        assert policy.policy_id == expected_policy
        assert policy.maximum_level == 10


def test_level_seven_caster_hunts_daycare_after_gnome_guard_fallback() -> None:
    policy = policy_for(
        7,
        "mage",
        last_policy_id="gnome-guard-caster-7-8",
    )

    assert policy.policy_id == "daycare-armed-guard-7-8"
    assert policy.execution == "daycare-armed-guard-hunt"
    assert policy.segment_kill_limit == 1


def test_level_seven_caster_returns_to_gnome_after_daycare_hunt() -> None:
    policy = policy_for(
        7,
        "mage",
        last_policy_id="daycare-armed-guard-7-8",
    )

    assert policy.policy_id == "gnome-hermit-7-8"
    assert policy.execution == "gnome-hermit-hunt"


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
