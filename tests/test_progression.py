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


def test_policy_for_honors_a_productive_hunt_handoff() -> None:
    policy = policy_for(
        18,
        "thief",
        last_policy_id="crystalmir-white-stag-probe-16-20",
        research_results={
            "crystalmir-white-stag-probe-16-20": {
                "absent": True,
                "boot_id": "boot-1",
                "observed": False,
                "viable": False,
            },
            "highland-keeper-hunt-17-20": {
                "boot_id": "boot-1",
                "completed_kill": True,
                "observed": True,
                "viable": True,
            },
        },
        handoff_policy_id="highland-keeper-hunt-17-20",
    )

    assert policy.policy_id == "highland-keeper-hunt-17-20"
    assert policy.execution == "highland-keeper-hunt"


def test_empty_basic_slots_select_midgaard_outfit_maintenance() -> None:
    policy = policy_for(8, "mage", needs_basic_gear=True)

    assert policy.policy_id == "outfit-basic-gear"
    assert policy.execution == "outfit-basic-gear"
    assert policy.executable is True


def test_unaffordable_provisions_select_source_funding_policy() -> None:
    policy = policy_for(
        18,
        "thief",
        has_food=False,
        needs_provision_funding=True,
    )

    assert policy.policy_id == "provision-funding"
    assert policy.execution == "provision-funding"
    assert policy.segment_kill_limit == 1
    assert policy.executable is True


def test_excluded_source_funding_remains_available_for_required_loot() -> None:
    policy = policy_for(
        18,
        "thief",
        has_food=True,
        needs_provision_funding=True,
        excluded_policy_ids=frozenset({"provision-funding"}),
    )

    assert policy.policy_id == "provision-funding"
    assert policy.execution == "provision-funding"


def test_excluded_provision_funding_falls_back_to_city_restock_without_food() -> None:
    policy = policy_for(
        18,
        "thief",
        has_food=False,
        needs_provision_funding=True,
        excluded_policy_ids=frozenset({"provision-funding"}),
    )

    assert policy.policy_id == "restock-provisions"
    assert policy.execution == "restock"
    assert policy.executable is True


def test_level_eighteen_thief_rotates_to_argent_after_registered_probes_fail() -> None:
    recorded_results = {
        policy_id: {
            "observed": True,
            "viable": False,
            "boot_id": "boot-1",
        }
        for policy_id in (
            "mirror-realm-watchman-probe-16-20",
            "mirror-realm-watchman-hunt-16-20",
            "crystalmir-white-stag-probe-16-20",
            "shadow-keep-undead-soldier-probe-16-20",
            "galaxy-white-dwarf-probe-17-20",
            "galaxy-white-dwarf-hunt-17-20",
            "galaxy-red-supergiant-probe-17-20",
            "galaxy-red-supergiant-hunt-17-20",
            "hightower-jailor-probe-17-20",
            "hightower-jailor-hunt-17-20",
            "dwarven-nobleman-thief-probe-17-18",
            "dwarven-nobleman-thief-hunt-17-18",
            "dwarven-servant-thief-probe-17-18",
            "dwarven-servant-thief-hunt-17-18",
            "shire-dwarven-prince-thief-probe-17-20",
            "shire-dwarven-prince-thief-hunt-17-20",
            "shire-elven-wizard-probe-17-20",
            "shire-elven-wizard-hunt-17-20",
            "pyramid-ali-baba-probe-18-20",
            "pyramid-ali-baba-hunt-18-20",
            "solace-lord-doom-probe-18-20",
            "solace-lord-doom-hunt-18-20",
        )
    }
    recorded_results["shire-thain-probe-17-20"] = {
        "absent": True,
        "observed": False,
        "viable": False,
        "boot_id": "boot-1",
    }

    policy = policy_for(
        18,
        "thief",
        last_policy_id="shire-thain-probe-17-20",
        world_boot_id="boot-1",
        has_sanctuary_potion=True,
        research_results=recorded_results,
    )

    assert policy.policy_id == "argent-bandit-leader-probe-17-20"
    assert policy.execution == "argent-bandit-leader-research"
    assert policy.status == "research"


def test_level_eighteen_reenters_historical_productive_route_after_cooldown() -> None:
    policy_ids = (
        "mirror-realm-watchman-probe-16-20",
        "mirror-realm-watchman-hunt-16-20",
        "crystalmir-white-stag-probe-16-20",
        "crystalmir-white-stag-hunt-16-20",
        "shadow-keep-undead-soldier-probe-16-20",
        "shadow-keep-undead-soldier-hunt-16-20",
        "galaxy-white-dwarf-probe-17-20",
        "galaxy-white-dwarf-hunt-17-20",
        "galaxy-white-dwarf-secondary-probe-17-20",
        "galaxy-white-dwarf-secondary-hunt-17-20",
        "galaxy-red-supergiant-probe-17-20",
        "galaxy-red-supergiant-hunt-17-20",
        "galaxy-horsehead-nebula-probe-18-20",
        "galaxy-horsehead-nebula-hunt-18-20",
        "hightower-jailor-probe-17-20",
        "hightower-jailor-hunt-17-20",
        "dwarven-nobleman-thief-probe-17-18",
        "dwarven-nobleman-thief-hunt-17-18",
        "dwarven-servant-thief-probe-17-18",
        "dwarven-servant-thief-hunt-17-18",
        "shire-dwarven-prince-thief-probe-17-20",
        "shire-dwarven-prince-thief-hunt-17-20",
        "shire-elven-wizard-probe-17-20",
        "shire-elven-wizard-hunt-17-20",
        "pyramid-ali-baba-probe-18-20",
        "pyramid-ali-baba-hunt-18-20",
        "solace-lord-doom-probe-18-20",
        "solace-lord-doom-hunt-18-20",
        "argent-bandit-leader-probe-17-20",
        "argent-bandit-leader-hunt-17-20",
        "highland-keeper-probe-17-20",
        "highland-keeper-hunt-17-20",
    )
    recorded_results = {
        policy_id: {
            "observed": True,
            "viable": False,
            "boot_id": "boot-1",
        }
        for policy_id in policy_ids
    }
    recorded_results["shire-thain-probe-17-20"] = {
        "absent": True,
        "observed": False,
        "viable": False,
        "boot_id": "boot-1",
    }
    recorded_results["moria-sanctuary-thief-17-20"] = {
        "absent": True,
        "observed": False,
        "viable": False,
        "boot_id": "boot-1",
    }
    recorded_results["highland-keeper-probe-17-20"] = {
        "absent": True,
        "observed": False,
        "viable": False,
        "boot_id": "boot-1",
    }
    recorded_results["highland-keeper-hunt-17-20"] = {
        "absent": True,
        "observed": False,
        "viable": False,
        "boot_id": "boot-1",
    }

    policy = policy_for(
        18,
        "thief",
        last_policy_id="moria-sanctuary-thief-17-20",
        world_boot_id="boot-1",
        has_sanctuary_potion=True,
        research_results=recorded_results,
        research_absence_cooldowns={
            "moria-sanctuary-thief-17-20": 3,
        },
        productive_policy_ids=frozenset({"highland-keeper-hunt-17-20"}),
    )

    assert policy.policy_id == "highland-keeper-probe-17-20"
    assert policy.execution == "highland-keeper-research"
    assert policy.status == "research"


def test_level_nineteen_thief_opens_aruncus_fallback_after_frontier_exhaustion() -> None:
    policy_ids = (
        "mirror-realm-watchman-probe-16-20",
        "mirror-realm-watchman-hunt-16-20",
        "mirror-realm-watchman-probe-19-20",
        "mirror-realm-watchman-hunt-19-20",
        "crystalmir-white-stag-probe-16-20",
        "crystalmir-white-stag-hunt-16-20",
        "shadow-keep-undead-soldier-probe-16-20",
        "shadow-keep-undead-soldier-hunt-16-20",
        "galaxy-white-dwarf-probe-17-20",
        "galaxy-white-dwarf-hunt-17-20",
        "galaxy-white-dwarf-secondary-probe-17-20",
        "galaxy-white-dwarf-secondary-hunt-17-20",
        "galaxy-red-supergiant-probe-17-20",
        "galaxy-red-supergiant-hunt-17-20",
        "galaxy-horsehead-nebula-probe-18-20",
        "galaxy-horsehead-nebula-hunt-18-20",
        "hightower-jailor-probe-17-20",
        "hightower-jailor-hunt-17-20",
        "shire-dwarven-prince-thief-probe-17-20",
        "shire-dwarven-prince-thief-hunt-17-20",
        "shire-thain-probe-17-20",
        "shire-thain-hunt-17-20",
        "shire-elven-wizard-probe-17-20",
        "shire-elven-wizard-hunt-17-20",
        "pyramid-ali-baba-probe-18-20",
        "pyramid-ali-baba-hunt-18-20",
        "solace-lord-doom-probe-18-20",
        "solace-lord-doom-hunt-18-20",
        "argent-bandit-leader-probe-17-20",
        "argent-bandit-leader-hunt-17-20",
        "highland-keeper-probe-17-20",
        "highland-keeper-hunt-17-20",
    )
    results = {
        policy_id: {
            "observed": True,
            "viable": False,
            "boot_id": "boot-1",
        }
        for policy_id in policy_ids
    }

    policy = policy_for(
        19,
        "thief",
        last_policy_id="shadow-keep-undead-soldier-hunt-16-20",
        world_boot_id="boot-1",
        has_sanctuary_potion=True,
        research_results=results,
    )

    assert policy.policy_id == "plains-aruncus-thief-probe-19-20"
    assert policy.execution == "plains-aruncus-research"
    assert policy.status == "research"


def test_level_nineteen_thief_opens_shire_retry_after_aruncus_is_below_band() -> None:
    policy_ids = (
        "mirror-realm-watchman-probe-16-20",
        "mirror-realm-watchman-hunt-16-20",
        "mirror-realm-watchman-probe-19-20",
        "mirror-realm-watchman-hunt-19-20",
        "crystalmir-white-stag-probe-16-20",
        "crystalmir-white-stag-hunt-16-20",
        "shadow-keep-undead-soldier-probe-16-20",
        "shadow-keep-undead-soldier-hunt-16-20",
        "galaxy-white-dwarf-probe-17-20",
        "galaxy-white-dwarf-hunt-17-20",
        "galaxy-white-dwarf-secondary-probe-17-20",
        "galaxy-white-dwarf-secondary-hunt-17-20",
        "galaxy-red-supergiant-probe-17-20",
        "galaxy-red-supergiant-hunt-17-20",
        "galaxy-horsehead-nebula-probe-18-20",
        "galaxy-horsehead-nebula-hunt-18-20",
        "hightower-jailor-probe-17-20",
        "hightower-jailor-hunt-17-20",
        "shire-dwarven-prince-thief-probe-17-20",
        "shire-dwarven-prince-thief-hunt-17-20",
        "shire-thain-probe-17-20",
        "shire-thain-hunt-17-20",
        "shire-elven-wizard-probe-17-20",
        "shire-elven-wizard-hunt-17-20",
        "pyramid-ali-baba-probe-18-20",
        "pyramid-ali-baba-hunt-18-20",
        "solace-lord-doom-probe-18-20",
        "solace-lord-doom-hunt-18-20",
        "argent-bandit-leader-probe-17-20",
        "argent-bandit-leader-hunt-17-20",
        "highland-keeper-probe-17-20",
        "highland-keeper-hunt-17-20",
    )
    results = {
        policy_id: {
            "observed": True,
            "viable": False,
            "boot_id": "boot-1",
        }
        for policy_id in policy_ids
    }
    results["plains-aruncus-thief-probe-19-20"] = {
        "observed": True,
        "viable": False,
        "boot_id": "boot-1",
    }

    policy = policy_for(
        19,
        "thief",
        last_policy_id="plains-aruncus-thief-probe-19-20",
        world_boot_id="boot-1",
        has_sanctuary_potion=True,
        research_results=results,
    )

    assert policy.policy_id == "shire-dwarven-prince-thief-probe-19-20"
    assert policy.execution == "shire-dwarven-prince-research"
    assert policy.status == "research"


def test_level_nineteen_thief_opens_magnus_and_requires_sanctuary_for_hunt() -> None:
    policy_ids = (
        "mirror-realm-watchman-probe-16-20",
        "mirror-realm-watchman-hunt-16-20",
        "mirror-realm-watchman-probe-19-20",
        "mirror-realm-watchman-hunt-19-20",
        "crystalmir-white-stag-probe-16-20",
        "crystalmir-white-stag-hunt-16-20",
        "shadow-keep-undead-soldier-probe-16-20",
        "shadow-keep-undead-soldier-hunt-16-20",
        "galaxy-white-dwarf-probe-17-20",
        "galaxy-white-dwarf-hunt-17-20",
        "galaxy-white-dwarf-secondary-probe-17-20",
        "galaxy-white-dwarf-secondary-hunt-17-20",
        "galaxy-red-supergiant-probe-17-20",
        "galaxy-red-supergiant-hunt-17-20",
        "galaxy-horsehead-nebula-probe-18-20",
        "galaxy-horsehead-nebula-hunt-18-20",
        "hightower-jailor-probe-17-20",
        "hightower-jailor-hunt-17-20",
        "shire-dwarven-prince-thief-probe-17-20",
        "shire-dwarven-prince-thief-hunt-17-20",
        "shire-thain-probe-17-20",
        "shire-thain-hunt-17-20",
        "shire-elven-wizard-probe-17-20",
        "shire-elven-wizard-hunt-17-20",
        "pyramid-ali-baba-probe-18-20",
        "pyramid-ali-baba-hunt-18-20",
        "solace-lord-doom-probe-18-20",
        "solace-lord-doom-hunt-18-20",
        "argent-bandit-leader-probe-17-20",
        "argent-bandit-leader-hunt-17-20",
        "highland-keeper-probe-17-20",
        "highland-keeper-hunt-17-20",
        "plains-aruncus-thief-probe-19-20",
        "plains-aruncus-thief-hunt-19-20",
        "shire-dwarven-prince-thief-probe-19-20",
        "shire-dwarven-prince-thief-hunt-19-20",
    )
    results = {
        policy_id: {
            "observed": True,
            "viable": False,
            "boot_id": "boot-1",
        }
        for policy_id in policy_ids
    }

    probe = policy_for(
        19,
        "thief",
        last_policy_id="shire-dwarven-prince-thief-hunt-19-20",
        world_boot_id="boot-1",
        has_sanctuary_potion=True,
        research_results=results,
    )

    assert probe.policy_id == "solace-magnus-probe-19-20"
    assert probe.execution == "solace-magnus-research"

    results["solace-magnus-probe-19-20"] = {
        "observed": True,
        "viable": True,
        "boot_id": "boot-1",
    }
    hunt = policy_for(
        19,
        "thief",
        last_policy_id="solace-magnus-probe-19-20",
        world_boot_id="boot-1",
        has_sanctuary_potion=True,
        research_results=results,
    )

    assert hunt.policy_id == "solace-magnus-hunt-19-20"
    assert hunt.execution == "solace-magnus-hunt"

    unprotected = policy_for(
        19,
        "thief",
        last_policy_id="solace-magnus-probe-19-20",
        world_boot_id="boot-1",
        has_sanctuary_potion=False,
        research_results=results,
    )

    assert unprotected.policy_id == "moria-sanctuary-thief-17-20"
    assert unprotected.execution == "moria-sanctuary-hunt"


def test_emergency_provision_sale_precedes_field_funding() -> None:
    policy = policy_for(
        18,
        "thief",
        has_food=False,
        needs_provision_funding=True,
        has_emergency_provision_sale=True,
    )

    assert policy.policy_id == "liquidate-loot"
    assert policy.execution == "sell-loot"
    assert policy.executable is True


def test_interrupted_mud_school_funding_run_returns_home_first() -> None:
    policy = policy_for(
        18,
        "thief",
        needs_return_home=True,
        needs_provision_funding=True,
    )

    assert policy.policy_id == "return-home"
    assert policy.execution == "return-home"
    assert policy.executable is True


def test_body_slot_recovery_selects_registered_required_loot_policy() -> None:
    policy = policy_for(8, "mage", needs_body_gear_recovery=True)

    assert policy.policy_id == "recover-basic-body-gear"
    assert policy.execution == "recover-basic-body"
    assert policy.segment_kill_limit == 1
    assert "forbidden for XP progression" in policy.evidence[-1]


def test_wrist_or_float_gap_selects_mud_school_accessory_recovery() -> None:
    policy = policy_for(8, "mage", needs_school_wrist_float=True)

    assert policy.policy_id == "recover-school-wrist-float"
    assert policy.execution == "recover-school-wrist-float"
    assert policy.segment_kill_limit == 2


def test_waist_gap_selects_gremlin_basic_recovery() -> None:
    policy = policy_for(8, "mage", needs_gremlin_waist=True)

    assert policy.policy_id == "recover-gremlin-waist"
    assert policy.execution == "recover-gremlin-waist"
    assert policy.segment_kill_limit == 1


def test_finger_gap_selects_daycare_old_doll_ring_recovery() -> None:
    policy = policy_for(8, "mage", needs_daycare_ring=True)

    assert policy.policy_id == "recover-daycare-ring"
    assert policy.execution == "recover-daycare-ring"
    assert policy.segment_kill_limit == 3
    assert "+1 strength and +6 hit points" in policy.evidence[0]


def test_neck_gap_selects_war_dog_collar_damage_recovery() -> None:
    policy = policy_for(8, "thief", needs_war_dog_collar=True)

    assert policy.policy_id == "recover-war-dog-collar"
    assert policy.execution == "recover-war-dog-collar"
    assert policy.segment_kill_limit == 1
    assert "+1 damroll" in policy.summary


def test_martial_with_ring_selects_foundry_set_circlet_recovery() -> None:
    policy = policy_for(
        14,
        "thief",
        needs_foundry_set_circlet=True,
    )

    assert policy.policy_id == "recover-foundry-set-circlet"
    assert policy.execution == "recover-foundry-set-circlet"
    assert policy.segment_kill_limit == 1
    assert "+2 strength" in policy.summary


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


def test_level_seven_caster_skips_completed_empty_guard_expansion() -> None:
    policy = policy_for(
        7,
        "mage",
        last_policy_id="circus-illusionist-7-8",
        policy_xp_deltas={
            "circus-illusionist-7-8": 0,
            "gnome-hermit-7-8": 63,
            "moria-orc-circuit-7-8": 0,
            "gnome-guard-caster-7-8": 0,
            "gnome-small-troll-caster-7-8": 482,
            "ambush-war-dog-caster-7-8": 234,
        },
    )

    assert policy.policy_id == "gnome-small-troll-caster-7-8"
    assert policy.execution == "gnome-small-troll-hunt"


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


def test_level_seven_caster_skips_known_weak_hunts() -> None:
    policy = policy_for(
        7,
        "mage",
        last_policy_id="daycare-armed-guard-7-8",
        policy_xp_deltas={
            "circus-illusionist-7-8": 131,
            "daycare-armed-guard-7-8": 622,
            "gnome-hermit-7-8": 63,
            "moria-orc-circuit-7-8": 309,
        },
    )

    assert policy.policy_id == "moria-orc-circuit-7-8"
    assert policy.execution == "moria-orc-hunt"


def test_level_seven_caster_expands_when_established_hunts_are_weak() -> None:
    policy = policy_for(
        7,
        "mage",
        last_policy_id="circus-illusionist-7-8",
        policy_xp_deltas={
            "circus-illusionist-7-8": 131,
            "gnome-hermit-7-8": 63,
            "moria-orc-circuit-7-8": 199,
        },
    )

    assert policy.policy_id == "gnome-guard-caster-7-8"
    assert policy.execution == "gnome-guard-hunt"


def test_level_seven_caster_expands_directly_after_depleted_fallback_cycle() -> None:
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

    assert policy.policy_id == "gnome-guard-caster-7-8"
    assert policy.execution == "gnome-guard-hunt"


def test_level_seven_caster_reuses_productive_expanded_hunt_directly() -> None:
    policy = policy_for(
        7,
        "mage",
        last_policy_id="daycare-armed-guard-7-8",
        policy_xp_deltas={
            "circus-illusionist-7-8": 0,
            "gnome-hermit-7-8": 63,
            "moria-orc-circuit-7-8": 0,
            "gnome-guard-caster-7-8": 0,
            "gnome-small-troll-caster-7-8": 482,
            "ambush-war-dog-caster-7-8": 234,
        },
    )

    assert policy.policy_id == "gnome-small-troll-caster-7-8"
    assert policy.execution == "gnome-small-troll-hunt"


def test_level_seven_caster_cycles_expanded_hunts_when_all_are_weak() -> None:
    policy = policy_for(
        7,
        "mage",
        last_policy_id="daycare-armed-guard-7-8",
        policy_xp_deltas={
            "circus-illusionist-7-8": 0,
            "gnome-hermit-7-8": 0,
            "moria-orc-circuit-7-8": 0,
            "gnome-guard-caster-7-8": 0,
            "gnome-small-troll-caster-7-8": 0,
            "ambush-war-dog-caster-7-8": 174,
        },
    )

    assert policy.policy_id == "gnome-small-troll-caster-7-8"
    assert policy.execution == "gnome-small-troll-hunt"


def test_level_seven_caster_leaves_depleted_established_cycle_for_troll() -> None:
    policy = policy_for(
        7,
        "mage",
        last_policy_id="circus-illusionist-7-8",
        policy_xp_deltas={
            "circus-illusionist-7-8": 0,
            "gnome-hermit-7-8": 0,
            "moria-orc-circuit-7-8": 0,
            "gnome-guard-caster-7-8": 0,
            "gnome-small-troll-caster-7-8": 0,
            "ambush-war-dog-caster-7-8": 174,
        },
    )

    assert policy.policy_id == "gnome-small-troll-caster-7-8"
    assert policy.execution == "gnome-small-troll-hunt"


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


def test_critical_coin_encumbrance_preempts_field_progression() -> None:
    policy = policy_for(
        13,
        "thief",
        needs_coin_deposit=True,
        needs_piercing_weapon_upgrade=True,
        has_flight=True,
    )

    assert policy.policy_id == "bank-excess-coins"
    assert policy.execution == "bank-excess-coins"


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


def test_level_eight_mage_requires_sanctuary_for_looter_extension() -> None:
    policy = policy_for(
        8,
        "mage",
        has_large_sack=True,
        has_sanctuary_potion=True,
    )

    assert policy.policy_id == "ambush-war-dog-looter-8-9"
    assert policy.execution == "ambush-war-dog-hunt"
    assert policy.segment_kill_limit == 2


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


def test_level_nine_martial_skips_recent_nonproductive_circuits() -> None:
    policy = policy_for(
        9,
        "warrior",
        last_policy_id="daycare-armed-guard-9-10",
        policy_xp_deltas={
            "ambush-martial-exterior-9-10": -44,
            "circus-freak-show-9-10": 192,
            "moria-large-orc-9-10": 0,
            "gnome-guard-circuit-9-10": 0,
            "daycare-armed-guard-9-10": 241,
        },
    )

    assert policy.policy_id == "circus-freak-show-9-10"


def test_level_nine_martial_skips_trivial_xp_segments() -> None:
    policy = policy_for(
        9,
        "warrior",
        last_policy_id="circus-freak-show-9-10",
        policy_xp_deltas={
            "ambush-martial-exterior-9-10": -44,
            "circus-freak-show-9-10": 20,
            "moria-large-orc-9-10": 0,
            "gnome-guard-circuit-9-10": 0,
            "daycare-armed-guard-9-10": 241,
        },
    )

    assert policy.policy_id == "daycare-armed-guard-9-10"


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


def test_level_eight_mage_rotates_immediately_after_empty_war_dog_hunt() -> None:
    policy = policy_for(
        8,
        "mage",
        has_large_sack=True,
        last_policy_id="ambush-war-dog-8-9",
        stalled_segments=1,
    )

    assert policy.policy_id == "midennir-goblin-8-10"


def test_level_eight_mage_rotates_beyond_depleted_dog_and_goblin_hunts() -> None:
    policy = policy_for(
        8,
        "mage",
        has_large_sack=True,
        last_policy_id="midennir-goblin-8-10",
        policy_xp_deltas={
            "ambush-war-dog-8-9": 0,
            "midennir-goblin-8-10": 0,
        },
    )

    assert policy.policy_id == "moria-large-orc-8-9"
    assert policy.execution == "moria-large-orc-hunt"


def test_level_eight_mage_repeats_productive_extended_hunt() -> None:
    policy = policy_for(
        8,
        "mage",
        has_large_sack=True,
        last_policy_id="moria-large-orc-8-9",
        policy_xp_deltas={
            "ambush-war-dog-8-9": 0,
            "midennir-goblin-8-10": 0,
            "moria-large-orc-8-9": 200,
        },
    )

    assert policy.policy_id == "moria-large-orc-8-9"


def test_level_eight_mage_rotates_after_empty_extended_hunt() -> None:
    policy = policy_for(
        8,
        "mage",
        has_large_sack=True,
        last_policy_id="moria-large-orc-8-9",
        policy_xp_deltas={
            "ambush-war-dog-8-9": 0,
            "midennir-goblin-8-10": 0,
            "moria-large-orc-8-9": 0,
        },
    )

    assert policy.policy_id == "circus-freak-show-8-9"


def test_level_nine_mage_uses_proven_war_dog_without_protection() -> None:
    policy = policy_for(9, "mage", has_large_sack=True)

    assert policy.policy_id == "ambush-exterior-9-10"
    assert policy.execution == "ambush-hunt"
    assert policy.practice_skill == "chill touch"
    assert policy.segment_kill_limit == 1


def test_level_nine_mage_rotates_after_empty_ambush_hunt() -> None:
    policy = policy_for(
        9,
        "mage",
        has_large_sack=True,
        last_policy_id="ambush-exterior-9-10",
        policy_xp_deltas={"ambush-exterior-9-10": 0},
    )

    assert policy.policy_id == "circus-freak-show-9-10"
    assert policy.execution == "circus-freak-show-hunt"


def test_level_nine_mage_rotates_beyond_known_empty_hunts() -> None:
    policy = policy_for(
        9,
        "mage",
        has_large_sack=True,
        last_policy_id="circus-freak-show-9-10",
        policy_xp_deltas={
            "ambush-exterior-9-10": 0,
            "circus-freak-show-9-10": 0,
        },
    )

    assert policy.policy_id == "moria-large-orc-9-10"
    assert policy.execution == "moria-large-orc-hunt"


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


def test_level_nine_mage_preserves_potion_and_rotates_after_empty_vile_hunt() -> None:
    policy = policy_for(
        9,
        "mage",
        has_large_sack=True,
        has_sanctuary_potion=True,
        last_policy_id="ambush-vile-goblin-9-10",
        policy_xp_deltas={"ambush-vile-goblin-9-10": 0},
    )

    assert policy.policy_id == "circus-freak-show-9-10"
    assert policy.execution == "circus-freak-show-hunt"


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


def test_missing_primary_weapon_selects_rearm_without_actionable_loot() -> None:
    policy = policy_for(
        18,
        "thief",
        has_sellable_loot=False,
        has_weapon=False,
    )

    assert policy.policy_id == "rearm-primary-weapon"
    assert policy.execution == "rearm-weapon"


def test_thief_missing_piercing_primary_selects_safe_rearm_maintenance() -> None:
    policy = policy_for(
        17,
        "thief",
        has_weapon=True,
        needs_piercing_weapon=True,
    )

    assert policy.policy_id == "rearm-primary-weapon"
    assert policy.execution == "rearm-weapon"


def test_bounty_hunter_missing_pounding_weapon_selects_rearm_maintenance() -> None:
    policy = policy_for(
        30,
        "thief",
        subclass="bounty hunter",
        has_weapon=True,
        needs_pounding_weapon=True,
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


def test_level_ten_mage_collects_shared_fleshmonger_probe_before_hunting() -> None:
    policy = policy_for(10, "mage", has_large_sack=True)

    assert policy.policy_id == "fleshmonger-guard-probe-10-12"
    assert policy.execution == "fleshmonger-guard-research"
    assert policy.status == "research"
    assert policy.executable


def test_level_ten_mage_acquires_sanctuary_after_shared_probe() -> None:
    policy = policy_for(
        10,
        "mage",
        has_large_sack=True,
        policy_xp_deltas={"fleshmonger-guard-probe-10-12": 0},
    )

    assert policy.policy_id == "moria-sanctuary-10-11"
    assert policy.execution == "moria-sanctuary-hunt"
    assert policy.maximum_level == 11
    assert policy.segment_kill_limit == 1


def test_level_ten_mage_rotates_from_empty_moria_to_guard_research() -> None:
    policy = policy_for(
        10,
        "mage",
        has_large_sack=True,
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "moria-sanctuary-10-11": 0,
        },
        last_policy_id="moria-sanctuary-10-11",
    )

    assert policy.policy_id == "fleshmonger-mage-guard-kill-research-10-11"
    assert policy.status == "research"
    assert policy.execution == "fleshmonger-guard-hunt"
    assert policy.segment_kill_limit == 1
    assert policy.executable


def test_level_ten_mage_moves_from_empty_moria_and_guard_to_orc_research() -> None:
    policy = policy_for(
        10,
        "mage",
        has_large_sack=True,
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "moria-sanctuary-10-11": 0,
            "fleshmonger-mage-guard-kill-research-10-11": 0,
        },
        last_policy_id="moria-sanctuary-10-11",
    )

    assert policy.policy_id == "moria-large-orc-mage-research-10-11"
    assert policy.status == "research"
    assert policy.executable


def test_level_ten_mage_does_not_return_to_moria_after_nonviable_guard() -> None:
    policy = policy_for(
        10,
        "mage",
        has_large_sack=True,
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "moria-sanctuary-10-11": 0,
            "fleshmonger-mage-guard-kill-research-10-11": 0,
        },
        last_policy_id="fleshmonger-mage-guard-kill-research-10-11",
    )

    assert policy.policy_id == "moria-large-orc-mage-research-10-11"
    assert policy.status == "research"
    assert policy.executable


def test_level_ten_mage_uses_two_stop_moria_orc_research_after_guard() -> None:
    policy = policy_for(
        10,
        "mage",
        has_large_sack=True,
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "moria-sanctuary-10-11": 0,
            "fleshmonger-mage-guard-kill-research-10-11": 0,
        },
        last_policy_id="fleshmonger-mage-guard-kill-research-10-11",
    )

    assert policy.policy_id == "moria-large-orc-mage-research-10-11"
    assert policy.status == "research"
    assert policy.execution == "moria-large-orc-hunt"
    assert policy.segment_kill_limit == 1


def test_level_ten_mage_promotes_productive_moria_orc_research() -> None:
    policy = policy_for(
        10,
        "mage",
        has_large_sack=True,
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "moria-sanctuary-10-11": 0,
            "fleshmonger-mage-guard-kill-research-10-11": 0,
            "moria-large-orc-mage-research-10-11": 539,
        },
        last_policy_id="moria-large-orc-mage-research-10-11",
    )

    assert policy.policy_id == "moria-large-orc-mage-10-11"
    assert policy.status == "verified"
    assert policy.execution == "moria-large-orc-hunt"


def test_level_ten_mage_retries_absent_moria_orc_after_reset_wait() -> None:
    policy = policy_for(
        10,
        "mage",
        has_large_sack=True,
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "moria-sanctuary-10-11": 0,
            "fleshmonger-mage-guard-kill-research-10-11": 0,
            "moria-large-orc-mage-research-10-11": 0,
        },
        research_results={
            "moria-large-orc-mage-research-10-11": {
                "absent": True,
                "observed": False,
                "viable": False,
                "boot_id": "boot-1",
            }
        },
        world_boot_id="boot-1",
        last_policy_id="moria-large-orc-mage-research-10-11",
    )

    assert policy.policy_id == "moria-large-orc-mage-research-10-11"
    assert policy.executable


def test_level_ten_mage_spends_confirmed_sanctuary_on_fresh_raider() -> None:
    policy = policy_for(
        10,
        "mage",
        has_large_sack=True,
        has_sanctuary_potion=True,
        policy_xp_deltas={"fleshmonger-guard-probe-10-12": 0},
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
        policy_xp_deltas={"fleshmonger-guard-probe-10-12": 0},
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


def test_thief_piercing_upgrade_buys_flight_before_long_source_route() -> None:
    policy = policy_for(
        11,
        "thief",
        needs_piercing_weapon_upgrade=True,
        has_flight=False,
        can_attempt_flight_purchase=True,
    )

    assert policy.policy_id == "buy-flight-potion"


def test_thief_piercing_upgrade_selects_bounded_forest_research() -> None:
    policy = policy_for(
        11,
        "thief",
        needs_piercing_weapon_upgrade=True,
        has_flight=True,
    )

    assert policy.policy_id == "forest-bear-claws-upgrade-10-29"
    assert policy.status == "research"
    assert policy.execution == "upgrade-piercing-weapon"
    assert policy.segment_kill_limit == 1
    assert policy.practice_skill == "backstab"


def test_thief_selects_thalos_intermediate_upgrade_after_blocked_forest() -> None:
    policy = policy_for(
        15,
        "thief",
        needs_intermediate_piercing_weapon_upgrade=True,
        needs_piercing_weapon_upgrade=True,
        piercing_weapon_upgrade_attempted=True,
    )

    assert policy.policy_id == "thalos-long-dagger-upgrade-10-29"
    assert policy.status == "research"
    assert policy.execution == "upgrade-piercing-weapon"
    assert policy.segment_kill_limit == 1


def test_thalos_intermediate_failure_respects_shared_upgrade_cooldown() -> None:
    policy = policy_for(
        15,
        "thief",
        needs_intermediate_piercing_weapon_upgrade=True,
        intermediate_piercing_weapon_upgrade_attempted=True,
        needs_piercing_weapon_upgrade=True,
        piercing_weapon_upgrade_attempted=True,
    )

    assert policy.execution != "upgrade-piercing-weapon"


def test_level_fifteen_thief_retains_material_piercing_upgrade() -> None:
    policy = policy_for(
        15,
        "thief",
        needs_piercing_weapon_upgrade=True,
        has_flight=True,
    )

    assert policy.policy_id == "forest-bear-claws-upgrade-10-29"
    assert policy.maximum_level == 29


def test_level_thirty_thief_leaves_pre_subclass_piercing_upgrade() -> None:
    policy = policy_for(
        30,
        "thief",
        subclass="ninja",
        needs_piercing_weapon_upgrade=True,
        has_flight=True,
    )

    assert policy.execution != "upgrade-piercing-weapon"


def test_thief_does_not_take_forest_route_without_enough_nonflight_capacity() -> None:
    policy = policy_for(
        11,
        "thief",
        needs_piercing_weapon_upgrade=True,
        has_flight=False,
        can_attempt_flight_purchase=False,
        movement_available=250,
    )

    assert policy.policy_id == "fleshmonger-thief-rotation-11-12"


def test_thief_does_not_wait_for_an_impossible_nonflight_route_reserve() -> None:
    policy = policy_for(
        11,
        "thief",
        needs_piercing_weapon_upgrade=True,
        has_flight=False,
        can_attempt_flight_purchase=False,
        movement_available=225,
        movement_capacity=250,
    )

    assert policy.policy_id == "fleshmonger-thief-rotation-11-12"


def test_thief_piercing_upgrade_is_not_repeated_during_same_reboot() -> None:
    policy = policy_for(
        11,
        "thief",
        needs_piercing_weapon_upgrade=True,
        piercing_weapon_upgrade_attempted=True,
        has_flight=True,
    )

    assert policy.policy_id == "fleshmonger-thief-rotation-11-12"


def test_piercing_upgrade_does_not_override_other_class_policy() -> None:
    policy = policy_for(
        10,
        "warrior",
        needs_piercing_weapon_upgrade=True,
        has_flight=True,
    )

    assert policy.policy_id == "fleshmonger-guard-probe-10-12"


@pytest.mark.parametrize("character_class", ["thief", "warrior"])
def test_level_ten_martial_collects_one_safe_fleshmonger_probe(
    character_class: str,
) -> None:
    policy = policy_for(10, character_class)

    assert policy.policy_id == "fleshmonger-guard-probe-10-12"
    assert policy.status == "research"
    assert policy.execution == "fleshmonger-guard-research"
    assert policy.executable
    assert "without initiating combat" in policy.summary


def test_level_ten_warrior_advances_from_probe_to_one_guard_research() -> None:
    policy = policy_for(
        10,
        "warrior",
        policy_xp_deltas={"fleshmonger-guard-probe-10-12": 0},
    )

    assert policy.policy_id == "fleshmonger-guard-kill-research-10-11"
    assert policy.execution == "fleshmonger-guard-hunt"
    assert policy.segment_kill_limit == 1
    assert policy.executable


def test_level_ten_thief_advances_from_probe_to_two_stop_research() -> None:
    policy = policy_for(
        10,
        "thief",
        policy_xp_deltas={"fleshmonger-guard-probe-10-12": 0},
    )

    assert policy.policy_id == "fleshmonger-thief-guard-research-10-11"
    assert policy.status == "research"
    assert policy.execution == "fleshmonger-guard-circuit-research"
    assert policy.segment_kill_limit == 1
    assert policy.executable
    assert "backstab" in " ".join(policy.evidence)


def test_level_ten_thief_promotes_productive_guard_research() -> None:
    policy = policy_for(
        10,
        "thief",
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "fleshmonger-thief-guard-research-10-11": 500,
        },
    )

    assert policy.policy_id == "fleshmonger-thief-guard-10-11"
    assert policy.status == "verified"
    assert policy.execution == "fleshmonger-guard-circuit"
    assert policy.segment_kill_limit == 1
    assert "Live run 1419" in " ".join(policy.evidence)


def test_level_ten_thief_stops_repeating_empty_verified_guard_loop() -> None:
    policy = policy_for(
        10,
        "thief",
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "fleshmonger-thief-guard-research-10-11": 423,
            "fleshmonger-thief-guard-10-11": 0,
        },
    )

    assert policy.policy_id == "fleshmonger-mufti-probe-10-11"
    assert policy.status == "research"
    assert policy.execution == "fleshmonger-mufti-research"
    assert policy.executable


def test_level_ten_thief_does_not_repeat_completed_mufti_probe() -> None:
    policy = policy_for(
        10,
        "thief",
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "fleshmonger-thief-guard-research-10-11": 423,
            "fleshmonger-thief-guard-10-11": 0,
            "fleshmonger-mufti-probe-10-11": 0,
        },
    )

    assert policy.policy_id == "fleshmonger-cook-probe-v2-10-11"
    assert policy.status == "research"
    assert policy.execution == "fleshmonger-cook-research"
    assert policy.executable


def test_level_ten_thief_does_not_repeat_completed_cook_probe() -> None:
    policy = policy_for(
        10,
        "thief",
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "fleshmonger-thief-guard-research-10-11": 423,
            "fleshmonger-thief-guard-10-11": 0,
            "fleshmonger-mufti-probe-10-11": 0,
            "fleshmonger-cook-probe-v2-10-11": 0,
        },
    )

    assert policy.policy_id == "fleshmonger-cook-10-11"
    assert policy.status == "verified"
    assert policy.execution == "fleshmonger-cook-hunt"
    assert policy.segment_kill_limit == 1
    assert policy.executable


def test_level_ten_thief_repeats_productive_verified_cook_hunt() -> None:
    policy = policy_for(
        10,
        "thief",
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "fleshmonger-thief-guard-research-10-11": 423,
            "fleshmonger-thief-guard-10-11": 0,
            "fleshmonger-mufti-probe-10-11": 0,
            "fleshmonger-cook-probe-v2-10-11": 0,
            "fleshmonger-cook-10-11": 696,
        },
    )

    assert policy.policy_id == "fleshmonger-cook-10-11"
    assert policy.status == "verified"
    assert "Live run 1425" in " ".join(policy.evidence)


def test_level_ten_thief_stops_after_empty_verified_cook_hunt() -> None:
    policy = policy_for(
        10,
        "thief",
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "fleshmonger-thief-guard-research-10-11": 423,
            "fleshmonger-thief-guard-10-11": 0,
            "fleshmonger-mufti-probe-10-11": 0,
            "fleshmonger-cook-probe-v2-10-11": 0,
            "fleshmonger-cook-10-11": 0,
        },
    )

    assert policy.policy_id == "ambush-archer-probe-10-11"
    assert policy.status == "research"
    assert policy.execution == "ambush-archer-research"
    assert policy.executable


def test_level_ten_thief_does_not_repeat_completed_archer_probe() -> None:
    policy = policy_for(
        10,
        "thief",
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "fleshmonger-thief-guard-research-10-11": 423,
            "fleshmonger-thief-guard-10-11": 0,
            "fleshmonger-mufti-probe-10-11": 0,
            "fleshmonger-cook-probe-v2-10-11": 0,
            "fleshmonger-cook-10-11": 0,
            "ambush-archer-probe-10-11": 0,
        },
    )

    assert policy.policy_id == "ambush-archer-kill-research-10-11"
    assert policy.status == "research"
    assert policy.execution == "ambush-archer-hunt"
    assert policy.segment_kill_limit == 1
    assert policy.executable


def test_level_ten_thief_moves_from_rejected_archer_to_gnome_probe() -> None:
    policy = policy_for(
        10,
        "thief",
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "fleshmonger-thief-guard-research-10-11": 423,
            "fleshmonger-thief-guard-10-11": 0,
            "fleshmonger-mufti-probe-10-11": 0,
            "fleshmonger-cook-probe-v2-10-11": 0,
            "fleshmonger-cook-10-11": 0,
            "ambush-archer-probe-10-11": 0,
            "ambush-archer-kill-research-10-11": 3,
        },
    )

    assert policy.policy_id == "gnome-guard-hut-probe-10-11"
    assert policy.status == "research"
    assert policy.execution == "gnome-guard-research"
    assert policy.executable


def test_level_ten_thief_combines_evidenced_targets_after_empty_gnome_probe() -> None:
    policy = policy_for(
        10,
        "thief",
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "fleshmonger-thief-guard-research-10-11": 423,
            "fleshmonger-thief-guard-10-11": 0,
            "fleshmonger-mufti-probe-10-11": 0,
            "fleshmonger-cook-probe-v2-10-11": 0,
            "fleshmonger-cook-10-11": 0,
            "ambush-archer-probe-10-11": 0,
            "ambush-archer-kill-research-10-11": 3,
            "gnome-guard-hut-probe-10-11": 0,
        },
    )

    assert policy.policy_id == "fleshmonger-thief-rotation-research-v8-10-11"
    assert policy.status == "research"
    assert policy.execution == "fleshmonger-thief-rotation-research"
    assert policy.segment_kill_limit == 2
    assert policy.executable


def test_level_ten_thief_stops_after_unproductive_combined_research() -> None:
    policy = policy_for(
        10,
        "thief",
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "fleshmonger-thief-guard-research-10-11": 423,
            "fleshmonger-thief-guard-10-11": 0,
            "fleshmonger-mufti-probe-10-11": 0,
            "fleshmonger-cook-probe-v2-10-11": 0,
            "fleshmonger-cook-10-11": 0,
            "ambush-archer-probe-10-11": 0,
            "ambush-archer-kill-research-10-11": 3,
            "gnome-guard-hut-probe-10-11": 0,
            "fleshmonger-thief-rotation-research-v8-10-11": 0,
        },
    )

    assert policy.status == "unavailable"
    assert not policy.executable


def test_level_ten_thief_promotes_productive_combined_rotation() -> None:
    policy = policy_for(
        10,
        "thief",
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "fleshmonger-thief-guard-research-10-11": 423,
            "fleshmonger-thief-guard-10-11": 0,
            "fleshmonger-mufti-probe-10-11": 0,
            "fleshmonger-cook-probe-v2-10-11": 0,
            "fleshmonger-cook-10-11": 0,
            "ambush-archer-probe-10-11": 0,
            "ambush-archer-kill-research-10-11": 3,
            "gnome-guard-hut-probe-10-11": 0,
            "fleshmonger-thief-rotation-research-v8-10-11": 472,
        },
    )

    assert policy.policy_id == "fleshmonger-thief-rotation-10-11"
    assert policy.status == "verified"
    assert policy.execution == "fleshmonger-thief-rotation-research"
    assert policy.segment_kill_limit == 2
    assert "Live runs 1433, 1436, and 1438" in " ".join(policy.evidence)
    assert "Live run 1446" in " ".join(policy.evidence)
    assert "Live run 1448" in " ".join(policy.evidence)
    assert "Live run 1452" in " ".join(policy.evidence)
    assert "Live run 1457" in " ".join(policy.evidence)


def test_level_ten_thief_revalidates_cook_identity_after_guard_rotation() -> None:
    policy = policy_for(
        10,
        "thief",
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "fleshmonger-thief-guard-research-10-11": 423,
            "fleshmonger-thief-guard-10-11": 0,
            "fleshmonger-mufti-probe-10-11": 0,
            "fleshmonger-cook-probe-v2-10-11": 0,
            "fleshmonger-cook-10-11": 0,
            "ambush-archer-probe-10-11": 0,
            "ambush-archer-kill-research-10-11": 3,
            "gnome-guard-hut-probe-10-11": 0,
            "fleshmonger-thief-rotation-research-v8-10-11": 472,
            "fleshmonger-thief-rotation-10-11": 277,
        },
    )

    assert policy.policy_id == "fleshmonger-cook-identity-probe-v3-10-11"
    assert policy.status == "research"
    assert policy.execution == "fleshmonger-cook-research"
    assert policy.segment_kill_limit is None


def test_level_ten_thief_uses_revalidated_unambiguous_cook() -> None:
    policy = policy_for(
        10,
        "thief",
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "fleshmonger-thief-guard-research-10-11": 423,
            "fleshmonger-thief-guard-10-11": 0,
            "fleshmonger-mufti-probe-10-11": 0,
            "fleshmonger-cook-probe-v2-10-11": 0,
            "fleshmonger-cook-10-11": 0,
            "ambush-archer-probe-10-11": 0,
            "ambush-archer-kill-research-10-11": 3,
            "gnome-guard-hut-probe-10-11": 0,
            "fleshmonger-thief-rotation-research-v8-10-11": 472,
            "fleshmonger-thief-rotation-10-11": 277,
            "fleshmonger-cook-identity-probe-v3-10-11": 0,
        },
    )

    assert policy.policy_id == "fleshmonger-cook-identity-10-11"
    assert policy.status == "verified"
    assert policy.execution == "fleshmonger-cook-hunt"
    assert policy.segment_kill_limit == 1
    assert "Live run 1443" in " ".join(policy.evidence)


def test_level_ten_thief_probes_isolated_study_servant_after_verified_rotation() -> None:
    policy = policy_for(
        10,
        "thief",
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "fleshmonger-thief-guard-research-10-11": 423,
            "fleshmonger-thief-guard-10-11": 0,
            "fleshmonger-mufti-probe-10-11": 0,
            "fleshmonger-cook-probe-v2-10-11": 0,
            "fleshmonger-cook-10-11": 0,
            "ambush-archer-probe-10-11": 0,
            "ambush-archer-kill-research-10-11": 3,
            "gnome-guard-hut-probe-10-11": 0,
            "fleshmonger-thief-rotation-research-v8-10-11": 472,
            "fleshmonger-thief-rotation-10-11": 240,
            "fleshmonger-cook-identity-probe-v3-10-11": 0,
            "fleshmonger-cook-identity-10-11": 504,
        },
    )

    assert policy.policy_id == "fleshmonger-servant-probe-v1-10-11"
    assert policy.status == "research"
    assert policy.execution == "fleshmonger-servant-research"
    assert policy.segment_kill_limit is None
    assert "source-level-8" in " ".join(policy.evidence)
    assert "room 9418" in " ".join(policy.evidence)


def test_level_ten_thief_attacks_study_servant_only_after_live_probe() -> None:
    policy = policy_for(
        10,
        "thief",
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "fleshmonger-thief-guard-research-10-11": 423,
            "fleshmonger-thief-guard-10-11": 0,
            "fleshmonger-mufti-probe-10-11": 0,
            "fleshmonger-cook-probe-v2-10-11": 0,
            "fleshmonger-cook-10-11": 0,
            "ambush-archer-probe-10-11": 0,
            "ambush-archer-kill-research-10-11": 3,
            "gnome-guard-hut-probe-10-11": 0,
            "fleshmonger-thief-rotation-research-v8-10-11": 472,
            "fleshmonger-thief-rotation-10-11": 240,
            "fleshmonger-cook-identity-probe-v3-10-11": 0,
            "fleshmonger-cook-identity-10-11": 504,
            "fleshmonger-servant-probe-v1-10-11": 0,
        },
    )

    assert policy.policy_id == "fleshmonger-servant-kill-research-v1-10-11"
    assert policy.status == "research"
    assert policy.execution == "fleshmonger-servant-hunt"
    assert policy.segment_kill_limit == 1
    assert "Live run 1461" in " ".join(policy.evidence)


def test_level_ten_thief_extends_rotation_after_productive_servant_kill() -> None:
    policy = policy_for(
        10,
        "thief",
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "fleshmonger-thief-guard-research-10-11": 423,
            "fleshmonger-thief-guard-10-11": 0,
            "fleshmonger-mufti-probe-10-11": 0,
            "fleshmonger-cook-probe-v2-10-11": 0,
            "fleshmonger-cook-10-11": 0,
            "ambush-archer-probe-10-11": 0,
            "ambush-archer-kill-research-10-11": 3,
            "gnome-guard-hut-probe-10-11": 0,
            "fleshmonger-thief-rotation-research-v8-10-11": 472,
            "fleshmonger-thief-rotation-10-11": 240,
            "fleshmonger-cook-identity-probe-v3-10-11": 0,
            "fleshmonger-cook-identity-10-11": 504,
            "fleshmonger-servant-probe-v1-10-11": 0,
            "fleshmonger-servant-kill-research-v1-10-11": 372,
        },
    )

    assert (
        policy.policy_id
        == "fleshmonger-thief-extended-rotation-research-v1-10-11"
    )
    assert policy.status == "research"
    assert policy.execution == "fleshmonger-thief-extended-rotation-research"
    assert policy.segment_kill_limit == 2
    assert "Live run 1462" in " ".join(policy.evidence)


def test_level_ten_thief_promotes_productive_extended_rotation() -> None:
    policy = policy_for(
        10,
        "thief",
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "fleshmonger-thief-guard-research-10-11": 423,
            "fleshmonger-thief-guard-10-11": 0,
            "fleshmonger-mufti-probe-10-11": 0,
            "fleshmonger-cook-probe-v2-10-11": 0,
            "fleshmonger-cook-10-11": 0,
            "ambush-archer-probe-10-11": 0,
            "ambush-archer-kill-research-10-11": 3,
            "gnome-guard-hut-probe-10-11": 0,
            "fleshmonger-thief-rotation-research-v8-10-11": 472,
            "fleshmonger-thief-rotation-10-11": 240,
            "fleshmonger-cook-identity-probe-v3-10-11": 0,
            "fleshmonger-cook-identity-10-11": 504,
            "fleshmonger-servant-probe-v1-10-11": 0,
            "fleshmonger-servant-kill-research-v1-10-11": 372,
            "fleshmonger-thief-extended-rotation-research-v1-10-11": 394,
        },
    )

    assert policy.policy_id == "fleshmonger-thief-extended-rotation-10-11"
    assert policy.status == "verified"
    assert policy.execution == "fleshmonger-thief-extended-rotation-research"
    assert policy.segment_kill_limit == 2
    assert "Live run 1464" in " ".join(policy.evidence)
    assert "same-segment cook-plus-servant" in " ".join(policy.evidence)
    assert "Live run 1468" in " ".join(policy.evidence)
    assert "room 9406" in " ".join(policy.evidence)


def test_level_ten_thief_fetches_sanctuary_after_empty_extended_rotation() -> None:
    deltas = {
        "fleshmonger-guard-probe-10-12": 0,
        "fleshmonger-thief-guard-research-10-11": 423,
        "fleshmonger-thief-guard-10-11": 0,
        "fleshmonger-mufti-probe-10-11": 0,
        "fleshmonger-cook-probe-v2-10-11": 0,
        "fleshmonger-cook-10-11": 0,
        "ambush-archer-probe-10-11": 0,
        "ambush-archer-kill-research-10-11": 3,
        "gnome-guard-hut-probe-10-11": 0,
        "fleshmonger-thief-rotation-research-v8-10-11": 472,
        "fleshmonger-thief-rotation-10-11": 240,
        "fleshmonger-cook-identity-probe-v3-10-11": 0,
        "fleshmonger-cook-identity-10-11": 504,
        "fleshmonger-servant-probe-v1-10-11": 0,
        "fleshmonger-servant-kill-research-v1-10-11": 372,
        "fleshmonger-thief-extended-rotation-research-v1-10-11": 394,
        "fleshmonger-thief-extended-rotation-10-11": 0,
    }
    policy = policy_for(
        10,
        "thief",
        policy_xp_deltas=deltas,
    )

    assert policy.policy_id == "moria-sanctuary-10-11"
    assert policy.status == "verified"
    assert policy.execution == "moria-sanctuary-hunt"
    assert policy.practice_skill == "backstab"
    assert policy.segment_kill_limit == 1

    after_moria = policy_for(
        10,
        "thief",
        policy_xp_deltas={
            **deltas,
            "moria-sanctuary-10-11": 278,
        },
        last_policy_id="moria-sanctuary-10-11",
    )

    assert after_moria.policy_id == "fleshmonger-thief-rotation-10-11"
    assert after_moria.execution == "fleshmonger-thief-rotation-research"


def test_level_eleven_thief_starts_verified_level_twelve_rotation() -> None:
    policy = policy_for(11, "thief")

    assert policy.policy_id == "fleshmonger-thief-rotation-11-12"
    assert policy.status == "verified"
    assert policy.execution == "fleshmonger-thief-extended-rotation-research"
    assert policy.minimum_level == 11
    assert policy.maximum_level == 12
    assert policy.segment_kill_limit == 2
    assert "Live run 1504" in " ".join(policy.evidence)
    assert "Live run 1507" in " ".join(policy.evidence)
    assert "Live run 1462" in " ".join(policy.evidence)


def test_level_eleven_thief_rotates_from_fleshmonger_to_moria() -> None:
    policy = policy_for(
        11,
        "thief",
        last_policy_id="fleshmonger-thief-rotation-10-11",
        policy_xp_deltas={"fleshmonger-thief-rotation-10-11": 274},
    )

    assert policy.policy_id == "moria-sanctuary-11-12"
    assert policy.status == "verified"
    assert policy.execution == "moria-sanctuary-hunt"
    assert policy.maximum_level == 12
    assert policy.segment_kill_limit == 1
    assert "Live run 1503" in " ".join(policy.evidence)
    assert "Live run 1506" in " ".join(policy.evidence)


def test_level_eleven_thief_rotates_after_an_unconfirmed_positive_xp_hunt() -> None:
    policy = policy_for(
        11,
        "thief",
        last_policy_id="fleshmonger-thief-rotation-11-12",
        policy_xp_deltas={"fleshmonger-thief-rotation-11-12": 0},
    )

    assert policy.policy_id == "moria-sanctuary-11-12"


def test_level_eleven_thief_rotates_back_to_fleshmonger() -> None:
    policy = policy_for(
        11,
        "thief",
        last_policy_id="moria-sanctuary-11-12",
        policy_xp_deltas={
            "moria-sanctuary-11-12": 313,
            "fleshmonger-thief-rotation-11-12": 274,
        },
    )

    assert policy.policy_id == "fleshmonger-thief-rotation-11-12"
    assert policy.maximum_level == 12


def test_level_twelve_thief_runs_bounded_fleshmonger_research_first() -> None:
    policy = policy_for(12, "thief")

    assert policy.policy_id == "fleshmonger-thief-rotation-research-12-13"
    assert policy.status == "research"
    assert policy.execution == "fleshmonger-thief-extended-rotation-research"
    assert policy.segment_kill_limit == 2
    assert "must record a level-12 result" in " ".join(policy.evidence)


def test_level_twelve_thief_promotes_productive_research_to_verified_rotation() -> None:
    policy = policy_for(
        12,
        "thief",
        policy_xp_deltas={"fleshmonger-thief-rotation-research-12-13": 400},
    )

    assert policy.policy_id == "fleshmonger-thief-rotation-12-13"
    assert policy.status == "verified"
    assert policy.executable
    assert policy.segment_kill_limit == 2
    assert "Live run 1578" in " ".join(policy.evidence)


def test_level_twelve_thief_probes_nonaggressive_aruncus_after_empty_rotation() -> None:
    policy = policy_for(
        12,
        "thief",
        last_policy_id="fleshmonger-thief-rotation-12-13",
        policy_xp_deltas={
            "fleshmonger-thief-rotation-research-12-13": 400,
            "fleshmonger-thief-rotation-12-13": 0,
        },
    )

    assert policy.policy_id == "plains-aruncus-probe-12-13"
    assert policy.status == "research"
    assert policy.execution == "plains-aruncus-research"
    assert policy.segment_kill_limit is None


def test_level_twelve_thief_migrates_retired_moria_probe_to_aruncus() -> None:
    policy = policy_for(
        12,
        "thief",
        last_policy_id="moria-sanctuary-probe-12-13",
        policy_xp_deltas={"fleshmonger-thief-rotation-research-12-13": 400},
    )

    assert policy.policy_id == "plains-aruncus-probe-12-13"


def test_level_twelve_thief_returns_to_verified_rotation_after_aruncus_absence() -> None:
    policy = policy_for(
        12,
        "thief",
        last_policy_id="plains-aruncus-probe-12-13",
        policy_xp_deltas={"fleshmonger-thief-rotation-research-12-13": 400},
    )

    assert policy.policy_id == "fleshmonger-thief-rotation-12-13"
    assert policy.execution == "fleshmonger-thief-extended-rotation-research"
    assert policy.status == "verified"


def test_level_twelve_thief_waits_for_review_after_unproductive_research() -> None:
    policy = policy_for(
        12,
        "thief",
        policy_xp_deltas={"fleshmonger-thief-rotation-research-12-13": 0},
    )

    assert policy.status == "unavailable"
    assert not policy.executable


@pytest.mark.parametrize(
    "character_class",
    ["cleric", "psionic", "shifter", "brawler", "ranger", "smithy"],
)
def test_level_ten_tutorial_tracks_share_the_safe_fleshmonger_scout(
    character_class: str,
) -> None:
    policy = policy_for(10, character_class)

    assert policy.policy_id == "fleshmonger-guard-probe-10-12"
    assert policy.status == "research"
    assert policy.execution == "fleshmonger-guard-research"


def test_level_ten_tutorial_track_does_not_repeat_completed_scout() -> None:
    policy = policy_for(
        10,
        "cleric",
        policy_xp_deltas={"fleshmonger-guard-probe-10-12": 0},
    )

    assert policy.status == "unavailable"
    assert not policy.executable


@pytest.mark.parametrize("character_class", ["mage", "thief", "warrior", "psionicist"])
@pytest.mark.parametrize("level", [13, 14, 15])
def test_levels_thirteen_to_fifteen_use_bounded_aruncus_research(
    character_class: str,
    level: int,
) -> None:
    policy = policy_for(level, character_class)

    assert policy.policy_id == "plains-aruncus-probe-13-15"
    assert policy.status == "research"
    assert policy.execution == "plains-aruncus-research"
    assert policy.executable
    assert "cannot promote a combat policy" in " ".join(policy.evidence)


def test_level_thirteen_thief_adds_bounded_pursuit_after_aruncus_survey() -> None:
    policy = policy_for(
        13,
        "thief",
        last_policy_id="plains-aruncus-probe-13-15",
        policy_xp_deltas={"plains-aruncus-probe-13-15": 0},
    )

    assert policy.policy_id == "plains-aruncus-thief-pursuit-research-13-15"
    assert policy.execution == "plains-aruncus-hunt"
    assert policy.status == "research"
    assert "room 344" in " ".join(policy.evidence)


@pytest.mark.parametrize("level", [13, 14, 15])
def test_successful_aruncus_pursuit_promotes_verified_thief_hunt(level: int) -> None:
    policy = policy_for(
        level,
        "thief",
        policy_xp_deltas={
            "plains-aruncus-probe-13-15": 0,
            "plains-aruncus-thief-pursuit-research-13-15": 866,
        },
    )

    assert policy.policy_id == "plains-aruncus-thief-hunt-13-15"
    assert policy.status == "verified"
    assert policy.execution == "plains-aruncus-hunt"
    assert "Live run 1879" in " ".join(policy.evidence)


def test_level_thirteen_thief_defers_empty_fleshmonger_to_reset_controller() -> None:
    policy = policy_for(
        13,
        "thief",
        policy_xp_deltas={
            "plains-aruncus-probe-13-15": 0,
            "plains-aruncus-thief-pursuit-research-13-15": 0,
            "fleshmonger-thief-rotation-12-13": 0,
        },
    )

    assert policy.policy_id == "fleshmonger-thief-rotation-12-13"
    assert policy.status == "verified"
    assert policy.executable
    assert "outside-area reset controller" in policy.summary


def test_level_thirteen_thief_rotates_from_empty_fleshmonger_to_aruncus() -> None:
    policy = policy_for(
        13,
        "thief",
        last_policy_id="fleshmonger-thief-rotation-12-13",
        policy_xp_deltas={
            "plains-aruncus-probe-13-15": 0,
            "plains-aruncus-thief-pursuit-research-13-15": 0,
            "fleshmonger-thief-rotation-12-13": 0,
        },
    )

    assert policy.policy_id == "plains-aruncus-thief-pursuit-research-13-15"
    assert policy.execution == "plains-aruncus-hunt"


def test_level_thirteen_thief_rotates_empty_verified_aruncus_to_fleshmonger() -> None:
    policy = policy_for(
        13,
        "thief",
        last_policy_id="plains-aruncus-thief-hunt-13-15",
        policy_xp_deltas={
            "plains-aruncus-probe-13-15": 0,
            "plains-aruncus-thief-pursuit-research-13-15": 866,
            "plains-aruncus-thief-hunt-13-15": 0,
            "fleshmonger-thief-rotation-12-13": 0,
        },
    )

    assert policy.policy_id == "fleshmonger-thief-rotation-12-13"


def test_level_thirteen_thief_probes_bardoosh_after_three_aruncus_kills() -> None:
    policy = policy_for(
        13,
        "thief",
        boot_kill_counts={"Aruncus the Druid": 3},
        policy_xp_deltas={
            "plains-aruncus-probe-13-15": 0,
            "plains-aruncus-thief-pursuit-research-13-15": 866,
            "plains-aruncus-thief-hunt-13-15": 598,
            "fleshmonger-thief-rotation-12-13": 0,
        },
    )

    assert policy.policy_id == "ambush-bardoosh-thief-kill-research-13"
    assert policy.status == "research"
    assert policy.execution == "ambush-bardoosh-hunt"
    assert policy.segment_kill_limit == 1


def test_level_fourteen_thief_probes_worker_circuit_after_aruncus() -> None:
    policy = policy_for(
        14,
        "thief",
        last_policy_id="plains-aruncus-thief-hunt-13-15",
        world_boot_id="boot-2",
        boot_kill_counts={"Aruncus the Druid": 10},
        policy_xp_deltas={
            "plains-aruncus-thief-pursuit-research-13-15": 866,
            "plains-aruncus-thief-hunt-13-15": 515,
        },
    )

    assert policy.policy_id == "dwarven-workers-thief-probe-13-15"
    assert policy.execution == "dwarven-workers-research"


def test_level_fourteen_thief_leaves_retired_worker_combat_for_toad_probe() -> None:
    policy = policy_for(
        14,
        "thief",
        last_policy_id="dwarven-workers-thief-probe-13-15",
        world_boot_id="boot-2",
        policy_xp_deltas={
            "plains-aruncus-thief-pursuit-research-13-15": 866,
            "plains-aruncus-thief-hunt-13-15": 515,
        },
        research_results={
            "dwarven-workers-thief-probe-13-15": {
                "boot_id": "boot-2",
                "observed": True,
                "viable": True,
            }
        },
    )

    assert policy.policy_id == "mahntor-rock-toad-thief-probe-14-15"
    assert policy.execution == "mahntor-rock-toad-research"


def test_level_fourteen_thief_rotates_retired_worker_hunt_to_rock_toad_probe() -> None:
    policy = policy_for(
        14,
        "thief",
        last_policy_id="dwarven-workers-thief-kill-research-13-15",
        policy_xp_deltas={
            "plains-aruncus-thief-pursuit-research-13-15": 866,
            "plains-aruncus-thief-hunt-13-15": 515,
            "dwarven-workers-thief-kill-research-13-15": 900,
        },
    )

    assert policy.policy_id == "mahntor-rock-toad-thief-probe-14-15"
    assert policy.execution == "mahntor-rock-toad-research"


def test_level_fourteen_thief_rotates_viable_worker_probe_to_rock_toad_probe() -> None:
    policy = policy_for(
        14,
        "thief",
        last_policy_id="dwarven-workers-thief-probe-13-15",
        world_boot_id="boot-2",
        research_results={
            "dwarven-workers-thief-probe-13-15": {
                "boot_id": "boot-2",
                "observed": True,
                "viable": True,
            }
        },
    )

    assert policy.policy_id == "mahntor-rock-toad-thief-probe-14-15"
    assert policy.execution == "mahntor-rock-toad-research"


def test_level_fourteen_thief_promotes_viable_rock_toad_probe_to_one_kill() -> None:
    policy = policy_for(
        14,
        "thief",
        last_policy_id="mahntor-rock-toad-thief-probe-14-15",
        world_boot_id="boot-2",
        research_results={
            "mahntor-rock-toad-thief-probe-14-15": {
                "boot_id": "boot-2",
                "observed": True,
                "viable": True,
            }
        },
    )

    assert policy.policy_id == "mahntor-rock-toad-thief-kill-research-14-15"
    assert policy.execution == "mahntor-rock-toad-hunt"
    assert policy.segment_kill_limit == 1


def test_level_fourteen_thief_promotes_successful_toad_kill_to_circuit() -> None:
    policy = policy_for(
        14,
        "thief",
        last_policy_id="mahntor-rock-toad-thief-kill-research-14-15",
        policy_xp_deltas={
            "mahntor-rock-toad-thief-kill-research-14-15": 1001,
        },
    )

    assert policy.policy_id == "mahntor-rock-toad-thief-circuit-14-15"
    assert policy.execution == "mahntor-rock-toad-circuit"
    assert policy.status == "verified"
    assert policy.segment_kill_limit == 2


def test_level_fourteen_thief_repeats_productive_toad_without_sanctuary() -> None:
    policy = policy_for(
        14,
        "thief",
        last_policy_id="mahntor-rock-toad-thief-circuit-14-15",
        policy_xp_deltas={
            "mahntor-rock-toad-thief-kill-research-14-15": 1001,
            "mahntor-rock-toad-thief-circuit-14-15": 1800,
        },
    )

    assert policy.policy_id == "mahntor-rock-toad-thief-circuit-14-15"
    assert policy.execution == "mahntor-rock-toad-circuit"
    assert policy.segment_kill_limit == 2


def test_level_fifteen_thief_rotates_productive_toad_to_known_aruncus_hunt() -> None:
    policy = policy_for(
        15,
        "thief",
        last_policy_id="mahntor-rock-toad-thief-circuit-14-15",
        policy_xp_deltas={
            "plains-aruncus-thief-pursuit-research-13-15": 541,
            "mahntor-rock-toad-thief-kill-research-14-15": 473,
            "mahntor-rock-toad-thief-circuit-14-15": 407,
        },
    )

    assert policy.policy_id == "plains-aruncus-thief-hunt-13-15"
    assert policy.execution == "plains-aruncus-hunt"
    assert "resets can repopulate" in policy.summary


def test_level_fifteen_thief_rotates_repeated_one_kill_toad_to_aruncus() -> None:
    policy = policy_for(
        15,
        "thief",
        last_policy_id="mahntor-rock-toad-thief-kill-research-14-15",
        policy_xp_deltas={
            "plains-aruncus-thief-pursuit-research-13-15": 541,
            "mahntor-rock-toad-thief-kill-research-14-15": 719,
            "mahntor-rock-toad-thief-circuit-14-15": 588,
        },
    )

    assert policy.policy_id == "plains-aruncus-thief-hunt-13-15"
    assert policy.execution == "plains-aruncus-hunt"
    assert "one-kill Rock Toad" in policy.summary


def test_level_fifteen_thief_rotates_productive_toad_to_viable_treasurer() -> None:
    policy = policy_for(
        15,
        "thief",
        last_policy_id="mahntor-rock-toad-thief-circuit-14-15",
        policy_xp_deltas={
            "mahntor-rock-toad-thief-kill-research-14-15": 473,
            "mahntor-rock-toad-thief-circuit-14-15": 407,
        },
        boot_kill_counts={"the treasurer": 1},
        world_boot_id="boot-2",
        research_results={
            "gnome-treasurer-thief-probe-13-15": {
                "boot_id": "boot-2",
                "observed": True,
                "viable": True,
            }
        },
    )

    assert policy.policy_id == "gnome-treasurer-thief-kill-research-13-15"
    assert policy.execution == "gnome-treasurer-hunt"
    assert "resets can repopulate" in policy.summary


def test_level_fifteen_thief_leaves_below_band_moria_for_aruncus() -> None:
    policy = policy_for(
        15,
        "thief",
        last_policy_id="moria-sanctuary-thief-14-15",
        excluded_policy_ids={"moria-sanctuary-thief-14-15"},
        policy_xp_deltas={
            "plains-aruncus-thief-pursuit-research-13-15": 541,
            "mahntor-rock-toad-thief-kill-research-14-15": 719,
            "mahntor-rock-toad-thief-circuit-14-15": 0,
            "moria-sanctuary-thief-14-15": 0,
        },
    )

    assert policy.policy_id == "plains-aruncus-thief-hunt-13-15"
    assert policy.execution == "plains-aruncus-hunt"
    assert "below-band Moria carrier" in policy.summary


def test_live_below_band_exclusion_is_terminal_for_selected_policy() -> None:
    policy = policy_for(
        15,
        "thief",
        last_policy_id="mahntor-rock-toad-thief-circuit-14-15",
        excluded_policy_ids={"moria-sanctuary-thief-14-15"},
        policy_xp_deltas={
            "mahntor-rock-toad-thief-kill-research-14-15": 719,
            "mahntor-rock-toad-thief-circuit-14-15": 0,
        },
        has_sanctuary_potion=False,
    )

    assert policy.policy_id == "unregistered-10-100"
    assert policy.executable is False
    assert "excluded by live consider evidence" in policy.summary


def test_level_fourteen_thief_repeats_productive_toad_with_spare_sanctuary() -> None:
    policy = policy_for(
        14,
        "thief",
        last_policy_id="mahntor-rock-toad-thief-circuit-14-15",
        policy_xp_deltas={
            "mahntor-rock-toad-thief-kill-research-14-15": 1001,
            "mahntor-rock-toad-thief-circuit-14-15": 1800,
        },
        has_sanctuary_potion=True,
    )

    assert policy.policy_id == "mahntor-rock-toad-thief-circuit-14-15"
    assert policy.execution == "mahntor-rock-toad-circuit"
    assert policy.segment_kill_limit == 1


def test_level_fourteen_thief_acquires_sanctuary_after_weak_toad_segment() -> None:
    policy = policy_for(
        14,
        "thief",
        last_policy_id="mahntor-rock-toad-thief-circuit-14-15",
        policy_xp_deltas={
            "mahntor-rock-toad-thief-kill-research-14-15": 1001,
            "mahntor-rock-toad-thief-circuit-14-15": 115,
        },
        has_sanctuary_potion=False,
    )

    assert policy.policy_id == "moria-sanctuary-thief-14-15"
    assert policy.execution == "moria-sanctuary-hunt"
    assert policy.segment_kill_limit == 1


def test_level_fourteen_thief_spends_acquired_sanctuary_on_toad_circuit() -> None:
    policy = policy_for(
        14,
        "thief",
        last_policy_id="moria-sanctuary-thief-14-15",
        policy_xp_deltas={
            "mahntor-rock-toad-thief-kill-research-14-15": 1001,
            "mahntor-rock-toad-thief-circuit-14-15": 115,
        },
        has_sanctuary_potion=True,
    )

    assert policy.policy_id == "mahntor-rock-toad-thief-circuit-14-15"
    assert policy.execution == "mahntor-rock-toad-circuit"
    assert policy.segment_kill_limit == 1


def test_level_fourteen_thief_retries_toad_when_moria_carrier_is_absent() -> None:
    policy = policy_for(
        14,
        "thief",
        last_policy_id="moria-sanctuary-thief-14-15",
        policy_xp_deltas={
            "mahntor-rock-toad-thief-kill-research-14-15": 1001,
            "mahntor-rock-toad-thief-circuit-14-15": 115,
            "moria-sanctuary-thief-14-15": 0,
        },
        has_sanctuary_potion=False,
    )

    assert policy.policy_id == "mahntor-rock-toad-thief-circuit-14-15"
    assert policy.execution == "mahntor-rock-toad-circuit"
    assert policy.segment_kill_limit == 2


def test_level_fourteen_thief_retries_expanded_worker_search() -> None:
    policy = policy_for(
        14,
        "thief",
        last_policy_id="dwarven-workers-thief-probe-13-15",
        last_fastwalk_abort_reason=(
            "policy revision bound the worker survey to its exact source room "
            "line"
        ),
        research_results={
            "dwarven-workers-thief-probe-13-15": {
                "observed": False,
                "viable": False,
            }
        },
    )

    assert policy.policy_id == "dwarven-workers-thief-probe-13-15"


def test_level_thirteen_thief_does_not_repeat_unproductive_bardoosh() -> None:
    policy = policy_for(
        13,
        "thief",
        last_policy_id="fleshmonger-thief-rotation-12-13",
        boot_kill_counts={"Aruncus the Druid": 5},
        policy_xp_deltas={
            "plains-aruncus-probe-13-15": 0,
            "plains-aruncus-thief-pursuit-research-13-15": 866,
            "plains-aruncus-thief-hunt-13-15": 0,
            "fleshmonger-thief-rotation-12-13": 0,
            "ambush-bardoosh-thief-kill-research-13": 0,
        },
    )

    assert policy.policy_id == "plains-aruncus-thief-hunt-13-15"
    assert policy.execution == "plains-aruncus-hunt"


def test_level_thirteen_thief_probes_nobleman_after_bardoosh_and_repeated_aruncus() -> None:
    policy = policy_for(
        13,
        "thief",
        last_policy_id="plains-aruncus-thief-hunt-13-15",
        boot_kill_counts={"Aruncus the Druid": 8},
        policy_xp_deltas={
            "plains-aruncus-thief-pursuit-research-13-15": 866,
            "plains-aruncus-thief-hunt-13-15": 482,
            "ambush-bardoosh-thief-kill-research-13": 125,
        },
    )

    assert policy.policy_id == "dwarven-nobleman-thief-probe-13-15"
    assert policy.status == "research"
    assert policy.execution == "dwarven-nobleman-research"
    assert policy.segment_kill_limit is None


def test_level_thirteen_thief_returns_to_aruncus_after_nobleman_probe() -> None:
    policy = policy_for(
        13,
        "thief",
        last_policy_id="dwarven-nobleman-thief-probe-13-15",
        boot_kill_counts={"Aruncus the Druid": 8},
        policy_xp_deltas={
            "plains-aruncus-thief-pursuit-research-13-15": 866,
            "plains-aruncus-thief-hunt-13-15": 482,
            "ambush-bardoosh-thief-kill-research-13": 125,
            "dwarven-nobleman-thief-probe-13-15": 0,
        },
    )

    assert policy.policy_id == "plains-aruncus-thief-hunt-13-15"
    assert policy.execution == "plains-aruncus-hunt"


def test_level_thirteen_thief_retries_nobleman_after_destination_hop_fix() -> None:
    policy = policy_for(
        13,
        "thief",
        last_policy_id="plains-aruncus-thief-hunt-13-15",
        last_fastwalk_abort_reason=(
            "policy revision removed the redundant nobleman destination hop"
        ),
        boot_kill_counts={"Aruncus the Druid": 8},
        policy_xp_deltas={
            "ambush-bardoosh-thief-kill-research-13": 125,
            "dwarven-nobleman-thief-probe-13-15": 0,
        },
    )

    assert policy.policy_id == "dwarven-nobleman-thief-probe-13-15"
    assert policy.execution == "dwarven-nobleman-research"


def test_level_thirteen_thief_retries_nobleman_after_exact_identity_fix() -> None:
    policy = policy_for(
        13,
        "thief",
        last_policy_id="dwarven-nobleman-thief-probe-13-15",
        last_fastwalk_abort_reason=(
            "policy revision aligned the nobleman stop with its source identity"
        ),
        boot_kill_counts={"Aruncus the Druid": 8},
        policy_xp_deltas={
            "ambush-bardoosh-thief-kill-research-13": 125,
            "dwarven-nobleman-thief-probe-13-15": 0,
        },
    )

    assert policy.policy_id == "dwarven-nobleman-thief-probe-13-15"
    assert policy.execution == "dwarven-nobleman-research"


def test_level_thirteen_thief_promotes_viable_nobleman_probe_to_one_hunt() -> None:
    policy = policy_for(
        13,
        "thief",
        last_policy_id="dwarven-nobleman-thief-probe-13-15",
        world_boot_id="boot-1",
        boot_kill_counts={"Aruncus the Druid": 8},
        policy_xp_deltas={
            "ambush-bardoosh-thief-kill-research-13": 125,
            "dwarven-nobleman-thief-probe-13-15": 0,
        },
        research_results={
            "dwarven-nobleman-thief-probe-13-15": {
                "boot_id": "boot-1",
                "observed": True,
                "viable": True,
            }
        },
    )

    assert policy.policy_id == "dwarven-nobleman-thief-kill-research-13-15"
    assert policy.execution == "dwarven-nobleman-hunt"
    assert policy.segment_kill_limit == 1


def test_level_thirteen_thief_rechecks_absent_nobleman_after_two_other_areas() -> None:
    policy = policy_for(
        13,
        "thief",
        last_policy_id="fleshmonger-thief-rotation-12-13",
        world_boot_id="boot-1",
        boot_kill_counts={"Aruncus the Druid": 8},
        policy_xp_deltas={
            "plains-aruncus-thief-hunt-13-15": 0,
            "fleshmonger-thief-rotation-12-13": 0,
            "ambush-bardoosh-thief-kill-research-13": 125,
            "dwarven-nobleman-thief-probe-13-15": 0,
        },
        research_results={
            "dwarven-nobleman-thief-probe-13-15": {
                "boot_id": "boot-1",
                "observed": False,
                "viable": False,
            }
        },
    )

    assert policy.policy_id == "dwarven-nobleman-thief-probe-13-15"
    assert policy.execution == "dwarven-nobleman-research"
    assert "outside-area" in policy.summary


def test_level_thirteen_thief_probes_treasurer_after_rejected_live_nobleman() -> None:
    policy = policy_for(
        13,
        "thief",
        last_policy_id="fleshmonger-thief-rotation-12-13",
        world_boot_id="boot-1",
        boot_kill_counts={"Aruncus the Druid": 8},
        policy_xp_deltas={
            "plains-aruncus-thief-hunt-13-15": 0,
            "fleshmonger-thief-rotation-12-13": 0,
            "ambush-bardoosh-thief-kill-research-13": 125,
            "dwarven-nobleman-thief-probe-13-15": 0,
        },
        research_results={
            "dwarven-nobleman-thief-probe-13-15": {
                "boot_id": "boot-1",
                "observed": True,
                "viable": False,
            }
        },
    )

    assert policy.policy_id == "gnome-treasurer-thief-probe-13-15"
    assert policy.execution == "gnome-treasurer-research"


def test_level_thirteen_thief_promotes_viable_treasurer_probe_to_one_hunt() -> None:
    policy = policy_for(
        13,
        "thief",
        last_policy_id="gnome-treasurer-thief-probe-13-15",
        world_boot_id="boot-1",
        policy_xp_deltas={
            "gnome-treasurer-thief-probe-13-15": 0,
        },
        research_results={
            "dwarven-workers-thief-probe-13-15": {
                "boot_id": "boot-1",
                "observed": False,
                "viable": False,
            },
            "gnome-treasurer-thief-probe-13-15": {
                "boot_id": "boot-1",
                "observed": True,
                "viable": True,
            }
        },
    )

    assert policy.policy_id == "gnome-treasurer-thief-kill-research-13-15"
    assert policy.execution == "gnome-treasurer-hunt"
    assert policy.segment_kill_limit == 1


def test_level_thirteen_thief_rotates_empty_fleshmonger_to_productive_treasurer() -> None:
    policy = policy_for(
        13,
        "thief",
        last_policy_id="fleshmonger-thief-rotation-12-13",
        world_boot_id="boot-1",
        policy_xp_deltas={
            "plains-aruncus-probe-13-15": 0,
            "plains-aruncus-thief-pursuit-research-13-15": 0,
            "plains-aruncus-thief-hunt-13-15": 0,
            "fleshmonger-thief-rotation-12-13": 0,
            "gnome-treasurer-thief-kill-research-13-15": 410,
        },
        research_results={
            "gnome-treasurer-thief-probe-13-15": {
                "boot_id": "boot-1",
                "observed": True,
                "viable": True,
            }
        },
    )

    assert policy.policy_id == "gnome-treasurer-thief-kill-research-13-15"
    assert policy.execution == "gnome-treasurer-hunt"
    assert policy.segment_kill_limit == 1


def test_level_thirteen_thief_continues_productive_treasurer_after_maintenance() -> None:
    policy = policy_for(
        13,
        "thief",
        last_policy_id="gnome-treasurer-thief-kill-research-13-15",
        world_boot_id="boot-1",
        policy_xp_deltas={
            "fleshmonger-thief-rotation-12-13": 0,
            "gnome-treasurer-thief-kill-research-13-15": 230,
        },
        research_results={
            "gnome-treasurer-thief-probe-13-15": {
                "boot_id": "boot-1",
                "observed": True,
                "viable": True,
            }
        },
    )

    assert policy.policy_id == "gnome-treasurer-thief-kill-research-13-15"
    assert policy.execution == "gnome-treasurer-hunt"


def test_level_thirteen_thief_leaves_empty_treasury_for_reset_interval() -> None:
    policy = policy_for(
        13,
        "thief",
        last_policy_id="gnome-treasurer-thief-kill-research-13-15",
        world_boot_id="boot-1",
        boot_kill_counts={"the treasurer": 4},
        policy_xp_deltas={
            "plains-aruncus-probe-13-15": 0,
            "fleshmonger-thief-rotation-12-13": 0,
            "gnome-treasurer-thief-kill-research-13-15": 0,
        },
        research_results={
            "gnome-treasurer-thief-probe-13-15": {
                "boot_id": "boot-1",
                "observed": True,
                "viable": True,
            }
        },
    )

    assert policy.policy_id == "fleshmonger-thief-rotation-12-13"


def test_level_thirteen_thief_retries_treasurer_after_reset_interval() -> None:
    policy = policy_for(
        13,
        "thief",
        last_policy_id="fleshmonger-thief-rotation-12-13",
        world_boot_id="boot-1",
        boot_kill_counts={"the treasurer": 4},
        policy_xp_deltas={
            "plains-aruncus-probe-13-15": 0,
            "fleshmonger-thief-rotation-12-13": 0,
            "gnome-treasurer-thief-kill-research-13-15": 0,
        },
        research_results={
            "gnome-treasurer-thief-probe-13-15": {
                "boot_id": "boot-1",
                "observed": True,
                "viable": True,
            }
        },
    )

    assert policy.policy_id == "gnome-treasurer-thief-kill-research-13-15"
    assert policy.execution == "gnome-treasurer-hunt"


def test_level_thirteen_thief_rechecks_rejected_nobleman_after_reboot() -> None:
    policy = policy_for(
        13,
        "thief",
        last_policy_id="fleshmonger-thief-rotation-12-13",
        world_boot_id="boot-2",
        boot_kill_counts={"Aruncus the Druid": 8},
        policy_xp_deltas={
            "plains-aruncus-thief-hunt-13-15": 0,
            "fleshmonger-thief-rotation-12-13": 0,
            "ambush-bardoosh-thief-kill-research-13": 125,
            "dwarven-nobleman-thief-probe-13-15": 0,
        },
        research_results={
            "dwarven-nobleman-thief-probe-13-15": {
                "boot_id": "boot-1",
                "observed": True,
                "viable": False,
            }
        },
    )

    assert policy.policy_id == "dwarven-nobleman-thief-probe-13-15"
    assert "reboot" in policy.summary


def test_level_thirteen_thief_returns_to_aruncus_after_bardoosh_attempt() -> None:
    policy = policy_for(
        13,
        "thief",
        last_policy_id="ambush-bardoosh-thief-kill-research-13",
        boot_kill_counts={"Aruncus the Druid": 5},
        policy_xp_deltas={
            "plains-aruncus-probe-13-15": 0,
            "plains-aruncus-thief-pursuit-research-13-15": 866,
            "plains-aruncus-thief-hunt-13-15": 0,
            "fleshmonger-thief-rotation-12-13": 0,
            "ambush-bardoosh-thief-kill-research-13": 0,
        },
    )

    assert policy.policy_id == "plains-aruncus-thief-hunt-13-15"
    assert policy.execution == "plains-aruncus-hunt"


def test_level_thirteen_thief_retries_bardoosh_after_route_interruption() -> None:
    policy = policy_for(
        13,
        "thief",
        last_policy_id="ambush-bardoosh-thief-kill-research-13",
        last_fastwalk_abort_reason=(
            "unexpected combat interrupted fastwalk 'ambush' before its objective"
        ),
        boot_kill_counts={"Aruncus the Druid": 5},
        policy_xp_deltas={
            "plains-aruncus-thief-pursuit-research-13-15": 866,
            "ambush-bardoosh-thief-kill-research-13": 0,
        },
    )

    assert policy.policy_id == "ambush-bardoosh-thief-kill-research-13"
    assert policy.execution == "ambush-bardoosh-hunt"
    assert "interrupted" in policy.summary


def test_level_fourteen_thief_keeps_empty_aruncus_under_reset_controller() -> None:
    policy = policy_for(
        14,
        "thief",
        policy_xp_deltas={
            "plains-aruncus-probe-13-15": 0,
            "plains-aruncus-thief-pursuit-research-13-15": 866,
            "plains-aruncus-thief-hunt-13-15": 0,
        },
    )

    assert policy.policy_id == "plains-aruncus-thief-hunt-13-15"
    assert policy.status == "verified"


def test_level_fourteen_thief_rotates_empty_aruncus_to_viable_treasurer() -> None:
    policy = policy_for(
        14,
        "thief",
        last_policy_id="plains-aruncus-thief-hunt-13-15",
        world_boot_id="boot-1",
        boot_kill_counts={"the treasurer": 5},
        policy_xp_deltas={
            "plains-aruncus-probe-13-15": 0,
            "plains-aruncus-thief-pursuit-research-13-15": 866,
            "plains-aruncus-thief-hunt-13-15": 0,
            "gnome-treasurer-thief-kill-research-13-15": 0,
        },
        research_results={
            "gnome-treasurer-thief-probe-13-15": {
                "boot_id": "boot-1",
                "observed": True,
                "viable": True,
            }
        },
    )

    assert policy.policy_id == "gnome-treasurer-thief-kill-research-13-15"
    assert policy.execution == "gnome-treasurer-hunt"
    assert "empty or escaped Aruncus" in policy.summary


def test_level_fifteen_thief_rotates_empty_aruncus_to_productive_toad() -> None:
    policy = policy_for(
        15,
        "thief",
        last_policy_id="plains-aruncus-thief-hunt-13-15",
        excluded_policy_ids={"gnome-treasurer-thief-kill-research-13-15"},
        policy_xp_deltas={
            "plains-aruncus-thief-pursuit-research-13-15": 866,
            "plains-aruncus-thief-hunt-13-15": 0,
            "mahntor-rock-toad-thief-kill-research-14-15": 1001,
        },
    )

    assert policy.policy_id == "mahntor-rock-toad-thief-kill-research-14-15"
    assert policy.execution == "mahntor-rock-toad-hunt"
    assert "empty or escaped Aruncus" in policy.summary


def test_level_fifteen_thief_uses_reboot_kills_after_latest_toad_was_empty() -> None:
    policy = policy_for(
        15,
        "thief",
        last_policy_id="plains-aruncus-thief-hunt-13-15",
        boot_kill_counts={"the Rock Toad": 5},
        excluded_policy_ids={"gnome-treasurer-thief-kill-research-13-15"},
        policy_xp_deltas={
            "plains-aruncus-thief-pursuit-research-13-15": 866,
            "plains-aruncus-thief-hunt-13-15": 0,
            "mahntor-rock-toad-thief-kill-research-14-15": 0,
        },
    )

    assert policy.policy_id == "mahntor-rock-toad-thief-kill-research-14-15"
    assert policy.execution == "mahntor-rock-toad-hunt"
    assert "same-reboot kills" in policy.summary


def test_level_fourteen_thief_rotates_killed_aruncus_to_viable_treasurer() -> None:
    policy = policy_for(
        14,
        "thief",
        last_policy_id="plains-aruncus-thief-hunt-13-15",
        world_boot_id="boot-1",
        boot_kill_counts={
            "Aruncus the Druid": 1,
            "the treasurer": 1,
        },
        policy_xp_deltas={
            "plains-aruncus-probe-13-15": 0,
            "plains-aruncus-thief-pursuit-research-13-15": 866,
            "plains-aruncus-thief-hunt-13-15": 538,
            "gnome-treasurer-thief-kill-research-13-15": 282,
        },
        research_results={
            "dwarven-workers-thief-probe-13-15": {
                "boot_id": "boot-1",
                "observed": False,
                "viable": False,
            },
            "gnome-treasurer-thief-probe-13-15": {
                "boot_id": "boot-1",
                "observed": True,
                "viable": True,
            }
        },
    )

    assert policy.policy_id == "gnome-treasurer-thief-kill-research-13-15"
    assert "single reset" in policy.summary


def test_level_fourteen_thief_skips_same_reboot_below_band_treasurer() -> None:
    policy = policy_for(
        14,
        "thief",
        last_policy_id="plains-aruncus-thief-hunt-13-15",
        world_boot_id="boot-1",
        boot_kill_counts={
            "Aruncus the Druid": 2,
            "the treasurer": 1,
        },
        policy_xp_deltas={
            "plains-aruncus-probe-13-15": 0,
            "plains-aruncus-thief-pursuit-research-13-15": 866,
            "plains-aruncus-thief-hunt-13-15": 438,
            "gnome-treasurer-thief-kill-research-13-15": 0,
        },
        research_results={
            "dwarven-workers-thief-probe-13-15": {
                "boot_id": "boot-1",
                "observed": False,
                "viable": False,
            },
            "gnome-treasurer-thief-probe-13-15": {
                "boot_id": "boot-1",
                "observed": True,
                "viable": True,
            },
        },
        excluded_policy_ids=frozenset(
            {"gnome-treasurer-thief-kill-research-13-15"}
        ),
    )

    assert policy.policy_id == "plains-aruncus-thief-hunt-13-15"


def test_level_thirteen_thief_repeats_productive_fleshmonger_rotation() -> None:
    policy = policy_for(
        13,
        "thief",
        last_policy_id="fleshmonger-thief-rotation-12-13",
        policy_xp_deltas={"fleshmonger-thief-rotation-12-13": 462},
    )

    assert policy.policy_id == "fleshmonger-thief-rotation-12-13"
    assert policy.execution == "fleshmonger-thief-extended-rotation-research"


def test_level_thirteen_thief_retries_with_safe_pursuit_after_retired_probe() -> None:
    policy = policy_for(
        13,
        "thief",
        last_policy_id="plains-aruncus-thief-kill-research-v3-13-15",
        policy_xp_deltas={
            "plains-aruncus-probe-13-15": 0,
            "plains-aruncus-thief-kill-research-v3-13-15": 0,
        },
    )

    assert policy.policy_id == "plains-aruncus-thief-pursuit-research-13-15"
    assert policy.execution == "plains-aruncus-hunt"


@pytest.mark.parametrize("character_class", ["mage", "thief", "warrior", "psionic"])
def test_levels_sixteen_to_twenty_start_with_no_combat_watchman_probe(
    character_class: str,
) -> None:
    policy = policy_for(16, character_class)

    assert policy.policy_id == "mirror-realm-watchman-probe-16-20"
    assert policy.status == "research"
    assert policy.execution == "mirror-realm-watchman-research"
    assert policy.executable


def test_level_sixteen_reprobes_until_live_watchman_evidence_is_recorded() -> None:
    policy = policy_for(
        16,
        "mage",
        policy_xp_deltas={"mirror-realm-watchman-probe-16-20": 0},
    )

    assert policy.policy_id == "mirror-realm-watchman-probe-16-20"
    assert policy.executable


def test_viable_watchman_probe_promotes_to_a_bounded_hunt() -> None:
    policy = policy_for(
        16,
        "mage",
        last_policy_id="mirror-realm-watchman-probe-16-20",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.policy_id == "mirror-realm-watchman-hunt-16-20"
    assert policy.execution == "mirror-realm-watchman-hunt"
    assert policy.segment_kill_limit == 1


def test_watchman_hunt_never_uses_stale_reboot_evidence() -> None:
    policy = policy_for(
        16,
        "mage",
        last_policy_id="mirror-realm-watchman-probe-16-20",
        world_boot_id="boot-2",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.policy_id == "mirror-realm-watchman-probe-16-20"


def test_nonviable_watchman_falls_back_to_white_stag_probe() -> None:
    policy = policy_for(
        16,
        "mage",
        last_policy_id="mirror-realm-watchman-hunt-16-20",
        policy_xp_deltas={"mirror-realm-watchman-hunt-16-20": 0},
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-hunt-16-20": {
                "observed": False,
                "viable": False,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.policy_id == "crystalmir-white-stag-probe-16-20"
    assert policy.execution == "crystalmir-white-stag-research"


def test_viable_white_stag_probe_promotes_to_bounded_hunt() -> None:
    policy = policy_for(
        16,
        "mage",
        last_policy_id="crystalmir-white-stag-probe-16-20",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "crystalmir-white-stag-hunt-16-20"
    assert policy.execution == "crystalmir-white-stag-hunt"
    assert policy.segment_kill_limit == 1


def test_nonviable_white_stag_falls_back_to_shadow_keep_soldier_probe() -> None:
    policy = policy_for(
        16,
        "mage",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "shadow-keep-undead-soldier-probe-16-20"
    assert policy.execution == "shadow-keep-undead-soldier-research"


def test_viable_shadow_keep_soldier_probe_promotes_to_bounded_hunt() -> None:
    policy = policy_for(
        16,
        "mage",
        last_policy_id="shadow-keep-undead-soldier-probe-16-20",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "shadow-keep-undead-soldier-hunt-16-20"
    assert policy.execution == "shadow-keep-undead-soldier-hunt"
    assert policy.segment_kill_limit == 1


def test_viable_shadow_probe_repromotes_hunt_after_outside_progress() -> None:
    policy = policy_for(
        17,
        "thief",
        last_policy_id="mahntor-rock-toad-thief-circuit-16-18",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "shadow-keep-undead-soldier-hunt-16-20"
    assert policy.execution == "shadow-keep-undead-soldier-hunt"


def test_level_seventeen_uses_galaxy_probe_after_earlier_targets_reject() -> None:
    policy = policy_for(
        17,
        "thief",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-hunt-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "galaxy-white-dwarf-probe-17-20"
    assert policy.execution == "galaxy-white-dwarf-research"
    assert policy.status == "research"


def test_viable_galaxy_probe_promotes_one_bounded_hunt() -> None:
    policy = policy_for(
        17,
        "thief",
        last_policy_id="galaxy-white-dwarf-probe-17-20",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-hunt-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "galaxy-white-dwarf-hunt-17-20"
    assert policy.execution == "galaxy-white-dwarf-hunt"
    assert policy.segment_kill_limit == 1


def test_level_seventeen_uses_nobleman_probe_after_galaxy_is_absent() -> None:
    policy = policy_for(
        17,
        "thief",
        last_policy_id="galaxy-white-dwarf-probe-17-20",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "dwarven-nobleman-thief-probe-17-18"
    assert policy.execution == "dwarven-nobleman-research"
    assert policy.status == "research"


def test_level_seventeen_selects_red_supergiant_probe_after_white_is_absent() -> None:
    policy = policy_for(
        17,
        "thief",
        has_flight=True,
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True, "viable": False, "boot_id": "boot-1"
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
        },
    )

    assert policy.policy_id == "galaxy-red-supergiant-probe-17-20"
    assert policy.execution == "galaxy-red-supergiant-research"


def test_viable_red_supergiant_probe_promotes_one_bounded_hunt() -> None:
    policy = policy_for(
        17,
        "thief",
        has_flight=True,
        last_policy_id="galaxy-red-supergiant-probe-17-20",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True, "viable": False, "boot_id": "boot-1"
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": True, "viable": True, "boot_id": "boot-1"
            },
        },
    )

    assert policy.policy_id == "galaxy-red-supergiant-hunt-17-20"
    assert policy.execution == "galaxy-red-supergiant-hunt"
    assert policy.segment_kill_limit == 1


def test_level_eighteen_uses_horsehead_probe_after_red_supergiant_absence() -> None:
    policy = policy_for(
        18,
        "thief",
        has_flight=True,
        last_policy_id="galaxy-horsehead-nebula-probe-18-20",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True, "viable": False, "boot_id": "boot-1"
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "galaxy-red-supergiant-hunt-17-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
        },
    )

    assert policy.policy_id == "galaxy-horsehead-nebula-probe-18-20"
    assert policy.execution == "galaxy-horsehead-nebula-research"
    assert policy.status == "research"


def test_galaxy_policy_is_deferred_when_flight_purchase_has_failed() -> None:
    policy = policy_for(
        18,
        "thief",
        has_flight=False,
        can_attempt_flight_purchase=True,
        flight_purchase_failed=True,
        flight_loan_attempted=True,
        last_policy_id="galaxy-white-dwarf-secondary-probe-17-20",
        world_boot_id="boot-1",
    )

    assert policy.execution is None
    assert "requires active fly or levitation" in policy.summary
    assert "galaxy-white-dwarf-secondary" not in policy.policy_id


def test_failed_flight_purchase_uses_source_funding_after_loan_is_used() -> None:
    policy = policy_for(
        18,
        "thief",
        has_food=True,
        needs_provision_funding=True,
        has_flight=False,
        flight_purchase_failed=True,
        flight_loan_attempted=True,
        last_policy_id="galaxy-white-dwarf-secondary-probe-17-20",
        world_boot_id="boot-1",
    )

    assert policy.policy_id == "provision-funding"
    assert policy.execution == "provision-funding"


def test_completed_flight_funding_allows_loot_liquidation_before_retry() -> None:
    policy = policy_for(
        18,
        "thief",
        has_sellable_loot=True,
        has_flight=False,
        flight_purchase_failed=True,
        flight_loan_attempted=True,
        flight_funding_retry_pending=True,
        last_policy_id="galaxy-white-dwarf-secondary-probe-17-20",
        world_boot_id="boot-1",
    )

    assert policy.policy_id == "liquidate-loot"
    assert policy.execution == "sell-loot"


def test_completed_flight_funding_retries_purchase_after_maintenance() -> None:
    policy = policy_for(
        18,
        "thief",
        has_flight=False,
        flight_purchase_failed=True,
        flight_loan_attempted=True,
        flight_funding_retry_pending=True,
        last_policy_id="galaxy-white-dwarf-secondary-probe-17-20",
        world_boot_id="boot-1",
    )

    assert policy.policy_id == "buy-flight-potion"
    assert policy.execution == "buy-flight"


def test_galaxy_policy_takes_one_bounded_loan_after_flight_purchase_failure() -> None:
    policy = policy_for(
        18,
        "thief",
        has_flight=False,
        flight_purchase_failed=True,
        last_policy_id="galaxy-white-dwarf-secondary-probe-17-20",
        world_boot_id="boot-1",
    )

    assert policy.policy_id == "borrow-flight-potion"
    assert policy.execution == "borrow-flight"


def test_excluded_current_policy_takes_bounded_loan_after_flight_failure() -> None:
    policy = policy_for(
        18,
        "thief",
        has_flight=False,
        flight_purchase_failed=True,
        excluded_policy_ids=frozenset(
            {"mahntor-rock-toad-thief-circuit-16-18"}
        ),
        last_policy_id="galaxy-white-dwarf-secondary-probe-17-20",
        world_boot_id="boot-1",
    )

    assert policy.policy_id == "borrow-flight-potion"
    assert policy.execution == "borrow-flight"


def test_galaxy_policy_requests_flight_before_launch_when_purchase_is_available() -> None:
    policy = policy_for(
        18,
        "thief",
        has_flight=False,
        can_attempt_flight_purchase=True,
        last_policy_id="galaxy-white-dwarf-secondary-probe-17-20",
        world_boot_id="boot-1",
    )

    assert policy.policy_id == "buy-flight-potion"
    assert policy.execution == "buy-flight"


def test_viable_horsehead_probe_promotes_one_bounded_hunt() -> None:
    policy = policy_for(
        18,
        "warrior",
        has_flight=True,
        last_policy_id="galaxy-horsehead-nebula-probe-18-20",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True, "viable": False, "boot_id": "boot-1"
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "galaxy-horsehead-nebula-probe-18-20": {
                "observed": True, "viable": True, "boot_id": "boot-1"
            },
        },
    )

    assert policy.policy_id == "galaxy-horsehead-nebula-hunt-18-20"
    assert policy.execution == "galaxy-horsehead-nebula-hunt"
    assert policy.segment_kill_limit == 1


def _level_eighteen_research_outcomes() -> dict[str, dict[str, object]]:
    return {
        "mirror-realm-watchman-probe-16-20": {
            "observed": True, "viable": False, "boot_id": "boot-1"
        },
        "mirror-realm-watchman-hunt-16-20": {
            "observed": False, "viable": False, "boot_id": "boot-1"
        },
        "crystalmir-white-stag-probe-16-20": {
            "observed": False, "viable": False, "absent": True,
            "boot_id": "boot-1"
        },
        "crystalmir-white-stag-hunt-16-20": {
            "observed": False, "viable": False, "absent": True,
            "boot_id": "boot-1"
        },
        "shadow-keep-undead-soldier-probe-16-20": {
            "observed": False, "viable": False, "absent": True,
            "boot_id": "boot-1"
        },
        "shadow-keep-undead-soldier-hunt-16-20": {
            "observed": False, "viable": False, "absent": True,
            "boot_id": "boot-1"
        },
        "galaxy-white-dwarf-probe-17-20": {
            "observed": False, "viable": False, "absent": True,
            "boot_id": "boot-1"
        },
        "galaxy-red-supergiant-probe-17-20": {
            "observed": False, "viable": False, "absent": True,
            "boot_id": "boot-1"
        },
        "galaxy-red-supergiant-hunt-17-20": {
            "observed": False, "viable": False, "absent": True,
            "boot_id": "boot-1"
        },
        "galaxy-horsehead-nebula-probe-18-20": {
            "observed": False, "viable": False, "absent": True,
            "boot_id": "boot-1"
        },
        "dwarven-nobleman-thief-probe-17-18": {
            "observed": True, "viable": False, "boot_id": "boot-1"
        },
        "dwarven-servant-thief-probe-17-18": {
            "observed": True, "viable": True, "boot_id": "boot-1"
        },
        "dwarven-servant-thief-hunt-17-18": {
            "observed": True, "viable": False, "boot_id": "boot-1"
        },
        "hightower-jailor-probe-17-20": {
            "observed": True, "viable": True, "boot_id": "boot-1"
        },
        "hightower-jailor-hunt-17-20": {
            "observed": True, "viable": False, "boot_id": "boot-1"
        },
        "shire-thain-probe-17-20": {
            "observed": False, "viable": False, "absent": True,
            "boot_id": "boot-1"
        },
        "shire-elven-wizard-probe-17-20": {
            "observed": True, "viable": True, "boot_id": "boot-1"
        },
        "shire-elven-wizard-hunt-17-20": {
            "observed": True, "viable": False, "boot_id": "boot-1"
        },
        "pyramid-ali-baba-probe-18-20": {
            "observed": False, "viable": False, "absent": True,
            "boot_id": "boot-1"
        },
    }


def test_level_eighteen_uses_secondary_white_dwarf_after_horsehead_absence() -> None:
    policy = policy_for(
        18,
        "thief",
        has_flight=True,
        last_policy_id="galaxy-horsehead-nebula-probe-18-20",
        world_boot_id="boot-1",
        research_results=_level_eighteen_research_outcomes(),
    )

    assert policy.policy_id == "galaxy-white-dwarf-secondary-probe-17-20"
    assert policy.execution == "galaxy-white-dwarf-secondary-research"
    assert policy.status == "research"


def test_level_eighteen_thief_opens_pyramid_after_secondary_routes_are_consumed() -> None:
    results = _level_eighteen_research_outcomes()
    results.pop("pyramid-ali-baba-probe-18-20")
    results["galaxy-white-dwarf-secondary-probe-17-20"] = {
        "observed": False,
        "viable": False,
        "absent": True,
        "boot_id": "boot-1",
    }

    policy = policy_for(
        18,
        "thief",
        has_flight=True,
        last_policy_id="galaxy-horsehead-nebula-probe-18-20",
        world_boot_id="boot-1",
        research_results=results,
    )

    assert policy.policy_id == "pyramid-ali-baba-probe-18-20"
    assert policy.execution == "pyramid-ali-baba-research"
    assert policy.status == "research"


@pytest.mark.parametrize("character_class", ["thief", "warrior", "mage"])
def test_level_eighteen_opens_generic_lord_doom_probe_after_registered_routes(
    character_class: str,
) -> None:
    results = _level_eighteen_research_outcomes()
    results["galaxy-white-dwarf-secondary-probe-17-20"] = {
        "observed": False,
        "viable": False,
        "absent": True,
        "boot_id": "boot-1",
    }

    policy = policy_for(
        18,
        character_class,
        has_flight=True,
        last_policy_id="crystalmir-white-stag-probe-16-20",
        world_boot_id="boot-1",
        research_results=results,
    )

    assert policy.policy_id == "solace-lord-doom-probe-18-20"
    assert policy.execution == "solace-lord-doom-research"
    assert policy.status == "research"


def test_level_eighteen_uses_highland_keeper_after_current_routes_are_consumed() -> None:
    results = _level_eighteen_research_outcomes()
    results.update(
        {
            "galaxy-white-dwarf-secondary-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shire-dwarven-prince-thief-probe-17-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "shire-dwarven-prince-thief-hunt-17-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "solace-lord-doom-probe-18-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "solace-lord-doom-hunt-18-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "argent-bandit-leader-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
        }
    )

    policy = policy_for(
        18,
        "thief",
        has_flight=True,
        last_policy_id="argent-bandit-leader-probe-17-20",
        world_boot_id="boot-1",
        research_results=results,
    )

    assert policy.policy_id == "highland-keeper-probe-17-20"
    assert policy.execution == "highland-keeper-research"
    assert policy.status == "research"


def test_level_eighteen_absence_cooldown_defers_highland_after_another_policy() -> None:
    results = _level_eighteen_research_outcomes()
    results.update(
        {
            "galaxy-white-dwarf-secondary-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shire-dwarven-prince-thief-probe-17-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "shire-dwarven-prince-thief-hunt-17-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "solace-lord-doom-probe-18-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "solace-lord-doom-hunt-18-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "argent-bandit-leader-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
        }
    )

    policy = policy_for(
        18,
        "thief",
        has_flight=True,
        last_policy_id="shadow-keep-undead-soldier-hunt-16-20",
        world_boot_id="boot-1",
        research_results=results,
        research_absence_cooldowns={
            "highland-keeper-probe-17-20": 3,
        },
    )

    assert policy.policy_id != "highland-keeper-probe-17-20"


def test_viable_highland_keeper_probe_promotes_one_bounded_hunt() -> None:
    results = _level_eighteen_research_outcomes()
    results.update(
        {
            "galaxy-white-dwarf-secondary-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shire-dwarven-prince-thief-probe-17-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "shire-dwarven-prince-thief-hunt-17-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "solace-lord-doom-probe-18-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "solace-lord-doom-hunt-18-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "argent-bandit-leader-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "highland-keeper-probe-17-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
        }
    )
    policy = policy_for(
        18,
        "thief",
        last_policy_id="highland-keeper-probe-17-20",
        world_boot_id="boot-1",
        research_results=results,
    )

    assert policy.policy_id == "highland-keeper-hunt-17-20"
    assert policy.execution == "highland-keeper-hunt"
    assert policy.segment_kill_limit == 1


def test_viable_lord_doom_probe_promotes_one_bounded_hunt() -> None:
    results = _level_eighteen_research_outcomes()
    results["galaxy-white-dwarf-secondary-probe-17-20"] = {
        "observed": False,
        "viable": False,
        "absent": True,
        "boot_id": "boot-1",
    }
    results["solace-lord-doom-probe-18-20"] = {
        "observed": True,
        "viable": True,
        "boot_id": "boot-1",
    }

    policy = policy_for(
        18,
        "thief",
        has_flight=True,
        last_policy_id="solace-lord-doom-probe-18-20",
        world_boot_id="boot-1",
        research_results=results,
    )

    assert policy.policy_id == "solace-lord-doom-hunt-18-20"
    assert policy.execution == "solace-lord-doom-hunt"
    assert policy.segment_kill_limit == 1


def test_failed_lord_doom_hunt_opens_sanctuary_recovery() -> None:
    results = _level_eighteen_research_outcomes()
    results["galaxy-white-dwarf-secondary-probe-17-20"] = {
        "observed": False,
        "viable": False,
        "absent": True,
        "boot_id": "boot-1",
    }
    results["solace-lord-doom-probe-18-20"] = {
        "observed": True,
        "viable": True,
        "boot_id": "boot-1",
    }
    results["solace-lord-doom-hunt-18-20"] = {
        "observed": True,
        "viable": False,
        "completed_kill": False,
        "boot_id": "boot-1",
    }
    results["moria-sanctuary-thief-17-20"] = {
        "observed": False,
        "viable": False,
        "absent": True,
        "boot_id": "boot-1",
    }

    policy = policy_for(
        18,
        "thief",
        has_flight=True,
        has_sanctuary_potion=False,
        has_acquired_sanctuary_potion=False,
        last_policy_id="solace-lord-doom-hunt-18-20",
        world_boot_id="boot-1",
        research_results=results,
        excluded_policy_ids=frozenset({"moria-sanctuary-thief-17-20"}),
    )

    assert policy.policy_id == "moria-sanctuary-thief-17-20"
    assert policy.execution == "moria-sanctuary-hunt"


def test_moria_sanctuary_acquisition_promotes_distinct_lord_doom_retry() -> None:
    results = _level_eighteen_research_outcomes()
    results["galaxy-white-dwarf-secondary-probe-17-20"] = {
        "observed": False,
        "viable": False,
        "absent": True,
        "boot_id": "boot-1",
    }
    results["solace-lord-doom-hunt-18-20"] = {
        "observed": True,
        "viable": False,
        "completed_kill": False,
        "boot_id": "boot-1",
    }
    results["moria-sanctuary-thief-17-20"] = {
        "observed": True,
        "viable": True,
        "objective_kill": True,
        "boot_id": "boot-1",
    }

    policy = policy_for(
        18,
        "thief",
        has_flight=True,
        has_sanctuary_potion=True,
        has_acquired_sanctuary_potion=True,
        last_policy_id="moria-sanctuary-thief-17-20",
        world_boot_id="boot-1",
        research_results=results,
    )

    assert policy.policy_id == "solace-lord-doom-sanctuary-hunt-18-20"
    assert policy.execution == "solace-lord-doom-hunt"
    assert "purple sanctuary potion" in policy.summary


def test_recorded_failed_lord_doom_hunt_is_not_promoted_from_stale_probe() -> None:
    results = _level_eighteen_research_outcomes()
    results["galaxy-white-dwarf-secondary-probe-17-20"] = {
        "observed": False,
        "viable": False,
        "absent": True,
        "boot_id": "boot-1",
    }
    results["solace-lord-doom-probe-18-20"] = {
        "observed": True,
        "viable": True,
        "boot_id": "boot-1",
    }
    results["solace-lord-doom-hunt-18-20"] = {
        "observed": True,
        "viable": False,
        "completed_kill": False,
        "boot_id": "boot-1",
    }

    policy = policy_for(
        18,
        "thief",
        has_flight=True,
        has_sanctuary_potion=False,
        last_policy_id="solace-lord-doom-probe-18-20",
        world_boot_id="boot-1",
        research_results=results,
    )

    assert policy.policy_id == "moria-sanctuary-thief-17-20"
    assert policy.policy_id != "solace-lord-doom-hunt-18-20"


def test_failed_lord_doom_keeps_absent_sanctuary_recovery_live_after_maintenance() -> None:
    results = _level_eighteen_research_outcomes()
    results["galaxy-white-dwarf-secondary-probe-17-20"] = {
        "observed": False,
        "viable": False,
        "absent": True,
        "boot_id": "boot-1",
    }
    results["solace-lord-doom-probe-18-20"] = {
        "observed": True,
        "viable": True,
        "boot_id": "boot-1",
    }
    results["solace-lord-doom-hunt-18-20"] = {
        "observed": True,
        "viable": False,
        "completed_kill": False,
        "boot_id": "boot-1",
    }
    results["moria-sanctuary-thief-17-20"] = {
        "observed": False,
        "viable": False,
        "absent": True,
        "boot_id": "boot-1",
    }

    policy = policy_for(
        18,
        "thief",
        has_flight=True,
        has_sanctuary_potion=False,
        has_acquired_sanctuary_potion=False,
        last_policy_id="restock-provisions",
        world_boot_id="boot-1",
        research_results=results,
        excluded_policy_ids=frozenset({"moria-sanctuary-thief-17-20"}),
    )

    assert policy.policy_id == "moria-sanctuary-thief-17-20"
    assert policy.execution == "moria-sanctuary-hunt"


def test_moria_reset_cooldown_opens_shire_research_without_sanctuary() -> None:
    results = _level_eighteen_research_outcomes()
    results["galaxy-white-dwarf-secondary-probe-17-20"] = {
        "observed": False,
        "viable": False,
        "absent": True,
        "boot_id": "boot-1",
    }
    results["solace-lord-doom-hunt-18-20"] = {
        "observed": True,
        "viable": False,
        "completed_kill": False,
        "boot_id": "boot-1",
    }
    results["moria-sanctuary-thief-17-20"] = {
        "observed": False,
        "viable": False,
        "absent": True,
        "boot_id": "boot-1",
    }

    policy = policy_for(
        18,
        "thief",
        has_flight=True,
        has_sanctuary_potion=False,
        last_policy_id="moria-sanctuary-thief-17-20",
        world_boot_id="boot-1",
        research_results=results,
        research_absence_cooldowns={
            "moria-sanctuary-thief-17-20": 3,
        },
    )

    assert policy.policy_id == "shire-dwarven-prince-thief-probe-17-20"
    assert policy.execution == "shire-dwarven-prince-research"
    assert policy.status == "research"


def test_level_nineteen_magnus_sanctuary_gate_hands_off_to_fresh_argent_research() -> None:
    results = _level_eighteen_research_outcomes()
    results.update(
        {
            "mirror-realm-watchman-probe-19-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "mirror-realm-watchman-hunt-19-20": {
                "observed": True,
                "viable": False,
                "completed_kill": False,
                "boot_id": "boot-1",
            },
            "plains-aruncus-thief-probe-19-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "shire-dwarven-prince-thief-probe-19-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "shire-dwarven-prince-thief-hunt-19-20": {
                "observed": True,
                "viable": False,
                "completed_kill": False,
                "boot_id": "boot-1",
            },
            "shire-dwarven-prince-thief-probe-17-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "shire-dwarven-prince-thief-hunt-17-20": {
                "observed": True,
                "viable": False,
                "completed_kill": False,
                "boot_id": "boot-1",
            },
            "solace-magnus-probe-19-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "moria-sanctuary-thief-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
        }
    )
    results.pop("shire-thain-probe-17-20", None)
    results.pop("shire-thain-hunt-17-20", None)

    policy = policy_for(
        19,
        "thief",
        has_flight=True,
        has_sanctuary_potion=False,
        last_policy_id="moria-sanctuary-thief-17-20",
        world_boot_id="boot-1",
        research_results=results,
        research_absence_cooldowns={
            "moria-sanctuary-thief-17-20": 3,
        },
    )

    assert policy.policy_id == "argent-bandit-leader-probe-19-20"
    assert policy.execution == "argent-bandit-leader-research"
    assert policy.status == "research"


def test_level_nineteen_sanctuary_gate_uses_one_kill_toad_trial_after_research() -> None:
    results = _level_eighteen_research_outcomes()
    results.update(
        {
            "mirror-realm-watchman-probe-19-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "mirror-realm-watchman-hunt-19-20": {
                "observed": True,
                "viable": False,
                "completed_kill": False,
                "boot_id": "boot-1",
            },
            "plains-aruncus-thief-probe-19-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "shire-dwarven-prince-thief-probe-19-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "shire-dwarven-prince-thief-hunt-19-20": {
                "observed": True,
                "viable": False,
                "completed_kill": False,
                "boot_id": "boot-1",
            },
            "shire-dwarven-prince-thief-probe-17-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "shire-dwarven-prince-thief-hunt-17-20": {
                "observed": True,
                "viable": False,
                "completed_kill": False,
                "boot_id": "boot-1",
            },
            "shire-thain-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "argent-bandit-leader-probe-19-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "argent-bandit-leader-hunt-19-20": {
                "observed": True,
                "viable": False,
                "completed_kill": False,
                "boot_id": "boot-1",
            },
            "solace-magnus-probe-19-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "moria-sanctuary-thief-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
        }
    )

    policy = policy_for(
        19,
        "thief",
        has_flight=True,
        has_sanctuary_potion=False,
        last_policy_id="shire-thain-probe-17-20",
        world_boot_id="boot-1",
        research_results=results,
        research_absence_cooldowns={
            "moria-sanctuary-thief-17-20": 3,
            "shire-thain-probe-17-20": 3,
        },
    )

    assert policy.policy_id == "mahntor-rock-toad-thief-circuit-16-18"
    assert policy.maximum_level == 20
    assert policy.segment_kill_limit == 1


def test_level_nineteen_productive_argent_hunt_survives_maintenance() -> None:
    results = _level_eighteen_research_outcomes()
    results.update(
        {
            "mirror-realm-watchman-probe-19-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "mirror-realm-watchman-hunt-19-20": {
                "observed": True,
                "viable": False,
                "completed_kill": False,
                "boot_id": "boot-1",
            },
            "argent-bandit-leader-probe-19-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "argent-bandit-leader-hunt-19-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
        }
    )

    policy = policy_for(
        19,
        "thief",
        has_flight=True,
        has_sanctuary_potion=False,
        last_policy_id="liquidate-loot",
        world_boot_id="boot-1",
        research_results=results,
        policy_xp_deltas={"argent-bandit-leader-hunt-19-20": 794},
        productive_policy_ids=frozenset({"argent-bandit-leader-hunt-19-20"}),
    )

    assert policy.policy_id == "argent-bandit-leader-hunt-19-20"
    assert policy.execution == "argent-bandit-leader-hunt"


def test_viable_secondary_white_dwarf_probe_promotes_one_bounded_hunt() -> None:
    results = _level_eighteen_research_outcomes()
    results["galaxy-white-dwarf-secondary-probe-17-20"] = {
        "observed": True,
        "viable": True,
        "boot_id": "boot-1",
    }
    policy = policy_for(
        18,
        "warrior",
        has_flight=True,
        last_policy_id="galaxy-white-dwarf-secondary-probe-17-20",
        world_boot_id="boot-1",
        research_results=results,
    )

    assert policy.policy_id == "galaxy-white-dwarf-secondary-hunt-17-20"
    assert policy.execution == "galaxy-white-dwarf-secondary-hunt"
    assert policy.segment_kill_limit == 1


def test_level_seventeen_thief_uses_jailor_after_nobleman_and_servant_reject() -> None:
    research_results = {
        "mirror-realm-watchman-probe-16-20": {
            "observed": True, "viable": False, "boot_id": "boot-1"
        },
        "crystalmir-white-stag-probe-16-20": {
            "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
        },
        "shadow-keep-undead-soldier-probe-16-20": {
            "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
        },
        "galaxy-white-dwarf-probe-17-20": {
            "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
        },
        "galaxy-red-supergiant-probe-17-20": {
            "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
        },
        "dwarven-nobleman-thief-probe-17-18": {
            "observed": True, "viable": False, "boot_id": "boot-1"
        },
        "dwarven-servant-thief-probe-17-18": {
            "observed": True, "viable": False, "boot_id": "boot-1"
        },
        "dwarven-servant-thief-hunt-17-18": {
            "observed": True, "viable": False, "boot_id": "boot-1"
        },
    }

    policy = policy_for(
        17,
        "thief",
        last_policy_id="dwarven-servant-thief-hunt-17-18",
        world_boot_id="boot-1",
        research_results=research_results,
    )

    assert policy.policy_id == "hightower-jailor-probe-17-20"
    assert policy.execution == "hightower-jailor-research"


def test_level_seventeen_non_thief_uses_jailor_probe_after_earlier_targets_reject() -> None:
    policy = policy_for(
        17,
        "warrior",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True, "viable": False, "boot_id": "boot-1"
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
        },
    )

    assert policy.policy_id == "hightower-jailor-probe-17-20"
    assert policy.execution == "hightower-jailor-research"


def test_viable_jailor_probe_promotes_one_bounded_hunt() -> None:
    policy = policy_for(
        17,
        "warrior",
        last_policy_id="hightower-jailor-probe-17-20",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True, "viable": False, "boot_id": "boot-1"
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "hightower-jailor-probe-17-20": {
                "observed": True, "viable": True, "boot_id": "boot-1"
            },
        },
    )

    assert policy.policy_id == "hightower-jailor-hunt-17-20"
    assert policy.execution == "hightower-jailor-hunt"
    assert policy.segment_kill_limit == 1


def test_failed_jailor_hunt_acquires_sanctuary_before_retry() -> None:
    policy = policy_for(
        17,
        "thief",
        has_flight=True,
        has_sanctuary_potion=False,
        last_policy_id="hightower-jailor-hunt-17-20",
        last_fastwalk_abort_reason=(
            "field combat aborted for safety: health at or below 10%"
        ),
        research_results={
            "hightower-jailor-probe-17-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "hightower-jailor-hunt-17-20": {
                "observed": True,
                "viable": False,
                "completed_kill": False,
                "boot_id": "boot-1",
            },
        },
        world_boot_id="boot-1",
    )

    assert policy.policy_id == "moria-sanctuary-thief-17-20"
    assert policy.execution == "moria-sanctuary-hunt"
    assert policy.status == "research"
    assert policy.segment_kill_limit == 1


def test_sanctuary_acquisition_returns_to_jailor_hunt() -> None:
    policy = policy_for(
        17,
        "thief",
        has_flight=True,
        has_sanctuary_potion=True,
        last_policy_id="moria-sanctuary-thief-17-20",
        research_results={
            "moria-sanctuary-thief-17-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            }
        },
        world_boot_id="boot-1",
    )

    assert policy.policy_id == "hightower-jailor-hunt-17-20"
    assert policy.execution == "hightower-jailor-hunt"


def test_missing_sanctuary_does_not_block_the_level_seventeen_fallback() -> None:
    policy = policy_for(
        17,
        "thief",
        has_flight=True,
        has_sanctuary_potion=False,
        last_policy_id="moria-sanctuary-thief-17-20",
        world_boot_id="boot-1",
        excluded_policy_ids=frozenset(
            {
                "mahntor-rock-toad-thief-circuit-16-18",
                "plains-aruncus-thief-fallback-17-18",
            }
        ),
        policy_xp_deltas={"dwarven-nobleman-thief-hunt-17-18": 670},
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-nobleman-thief-probe-17-18": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "dwarven-nobleman-thief-hunt-17-18": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "moria-sanctuary-thief-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "dwarven-nobleman-thief-hunt-17-18"
    assert policy.execution == "dwarven-nobleman-hunt"


def test_migrated_jailor_probe_can_be_replayed_after_its_stale_result_is_cleared() -> None:
    policy = policy_for(
        17,
        "thief",
        last_policy_id="hightower-jailor-probe-17-20",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True, "viable": False, "boot_id": "boot-1"
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": False, "viable": False, "absent": True, "boot_id": "boot-1"
            },
            "dwarven-nobleman-thief-probe-17-18": {
                "observed": True, "viable": True, "boot_id": "boot-1"
            },
            "dwarven-nobleman-thief-hunt-17-18": {
                "observed": True, "viable": True, "boot_id": "boot-1"
            },
            "dwarven-servant-thief-probe-17-18": {
                "observed": True, "viable": True, "boot_id": "boot-1"
            },
            "dwarven-servant-thief-hunt-17-18": {
                "observed": True, "viable": False, "boot_id": "boot-1"
            },
        },
    )

    assert policy.policy_id == "hightower-jailor-probe-17-20"
    assert policy.execution == "hightower-jailor-research"


def test_level_nineteen_reopens_watchman_research_after_level_seventeen_rejection() -> None:
    policy = policy_for(
        19,
        "thief",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "mirror-realm-watchman-probe-19-20"
    assert policy.execution == "mirror-realm-watchman-research"


def test_viable_level_nineteen_watchman_promotes_bounded_hunt() -> None:
    policy = policy_for(
        19,
        "warrior",
        last_policy_id="mirror-realm-watchman-probe-19-20",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-19-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "mirror-realm-watchman-hunt-19-20"
    assert policy.execution == "mirror-realm-watchman-hunt"
    assert policy.segment_kill_limit == 1


def test_viable_level_seventeen_nobleman_probe_promotes_one_hunt() -> None:
    research_results = {
        "mirror-realm-watchman-probe-16-20": {
            "observed": True,
            "viable": False,
            "boot_id": "boot-1",
        },
        "crystalmir-white-stag-probe-16-20": {
            "observed": False,
            "viable": False,
            "absent": True,
            "boot_id": "boot-1",
        },
        "shadow-keep-undead-soldier-probe-16-20": {
            "observed": False,
            "viable": False,
            "absent": True,
            "boot_id": "boot-1",
        },
        "galaxy-white-dwarf-probe-17-20": {
            "observed": False,
            "viable": False,
            "absent": True,
            "boot_id": "boot-1",
        },
        "galaxy-red-supergiant-probe-17-20": {
            "observed": False,
            "viable": False,
            "absent": True,
            "boot_id": "boot-1",
        },
        "dwarven-nobleman-thief-probe-17-18": {
            "observed": True,
            "viable": True,
            "boot_id": "boot-1",
        },
    }

    policy = policy_for(
        17,
        "thief",
        last_policy_id="dwarven-nobleman-thief-probe-17-18",
        world_boot_id="boot-1",
        research_results=research_results,
    )

    assert policy.policy_id == "dwarven-nobleman-thief-hunt-17-18"
    assert policy.execution == "dwarven-nobleman-hunt"
    assert policy.segment_kill_limit == 1


def test_completed_level_seventeen_nobleman_hunt_rotates_onward() -> None:
    policy = policy_for(
        17,
        "thief",
        last_policy_id="dwarven-nobleman-thief-hunt-17-18",
        world_boot_id="boot-1",
        policy_xp_deltas={"dwarven-nobleman-thief-hunt-17-18": 500},
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-nobleman-thief-probe-17-18": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "dwarven-nobleman-thief-hunt-17-18": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "dwarven-servant-thief-probe-17-18"
    assert policy.execution == "dwarven-servant-research"


def test_viable_dwarven_servant_probe_promotes_one_bounded_hunt() -> None:
    policy = policy_for(
        17,
        "thief",
        last_policy_id="dwarven-servant-thief-probe-17-18",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-nobleman-thief-probe-17-18": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-servant-thief-probe-17-18": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "dwarven-servant-thief-hunt-17-18"
    assert policy.execution == "dwarven-servant-hunt"
    assert policy.segment_kill_limit == 1


def test_level_eighteen_thief_adds_shire_prince_probe_after_known_paths() -> None:
    research_results = {
        "mirror-realm-watchman-probe-16-20": {
            "observed": True,
            "viable": False,
            "boot_id": "boot-1",
        },
        "crystalmir-white-stag-probe-16-20": {
            "observed": False,
            "viable": False,
            "absent": True,
            "boot_id": "boot-1",
        },
        "shadow-keep-undead-soldier-probe-16-20": {
            "observed": True,
            "viable": True,
            "boot_id": "boot-1",
        },
        "shadow-keep-undead-soldier-hunt-16-20": {
            "observed": False,
            "viable": False,
            "absent": True,
            "boot_id": "boot-1",
        },
        "galaxy-white-dwarf-probe-17-20": {
            "observed": False,
            "viable": False,
            "absent": True,
            "boot_id": "boot-1",
        },
        "galaxy-red-supergiant-probe-17-20": {
            "observed": False,
            "viable": False,
            "absent": True,
            "boot_id": "boot-1",
        },
        "dwarven-nobleman-thief-probe-17-18": {
            "observed": False,
            "viable": False,
            "absent": True,
            "boot_id": "boot-1",
        },
        "dwarven-nobleman-thief-hunt-17-18": {
            "observed": False,
            "viable": False,
            "absent": True,
            "boot_id": "boot-1",
        },
        "dwarven-servant-thief-probe-17-18": {
            "observed": True,
            "viable": True,
            "boot_id": "boot-1",
        },
        "dwarven-servant-thief-hunt-17-18": {
            "observed": True,
            "viable": False,
            "unattackable": "dwarven servant",
            "boot_id": "boot-1",
        },
        "ambush-bardoosh-thief-kill-research-17-18": {
            "observed": True,
            "viable": False,
            "below_band": True,
            "boot_id": "boot-1",
        },
    }

    policy = policy_for(
        18,
        "thief",
        last_policy_id="mahntor-rock-toad-thief-circuit-16-18",
        stalled_segments=1,
        policy_xp_deltas={
            "mahntor-rock-toad-thief-circuit-16-18": 0,
        },
        excluded_policy_ids=frozenset(
            {"plains-aruncus-thief-fallback-17-18"}
        ),
        world_boot_id="boot-1",
        research_results=research_results,
    )

    assert policy.policy_id == "shire-dwarven-prince-thief-probe-17-20"
    assert policy.execution == "shire-dwarven-prince-research"
    assert policy.status == "research"


def test_level_eighteen_thief_opens_pyramid_probe_after_known_paths() -> None:
    recorded_results = {
        policy_id: {
            "observed": False,
            "viable": False,
            "absent": True,
            "boot_id": "boot-1",
        }
        for policy_id in (
            "mirror-realm-watchman-probe-16-20",
            "crystalmir-white-stag-probe-16-20",
            "shadow-keep-undead-soldier-probe-16-20",
            "galaxy-white-dwarf-probe-17-20",
            "galaxy-red-supergiant-probe-17-20",
            "dwarven-nobleman-thief-probe-17-18",
            "dwarven-nobleman-thief-hunt-17-18",
            "dwarven-servant-thief-probe-17-18",
            "dwarven-servant-thief-hunt-17-18",
            "hightower-jailor-probe-17-20",
            "hightower-jailor-hunt-17-20",
            "shire-dwarven-prince-thief-probe-17-20",
            "shire-dwarven-prince-thief-hunt-17-20",
            "shire-thain-probe-17-20",
            "shire-thain-hunt-17-20",
            "moria-sanctuary-thief-17-20",
        )
    }
    recorded_results["shire-elven-wizard-probe-17-20"] = {
        "observed": True,
        "viable": True,
        "boot_id": "boot-1",
    }

    policy = policy_for(
        18,
        "thief",
        last_policy_id="moria-sanctuary-thief-17-20",
        world_boot_id="boot-1",
        research_results=recorded_results,
    )

    assert policy.policy_id == "pyramid-ali-baba-probe-18-20"
    assert policy.execution == "pyramid-ali-baba-research"
    assert policy.status == "research"


def test_level_eighteen_thief_opens_unrecorded_prince_probe_after_late_route() -> None:
    recorded_results = {
        policy_id: {
            "observed": False,
            "viable": False,
            "absent": True,
            "boot_id": "boot-1",
        }
        for policy_id in (
            "mirror-realm-watchman-probe-16-20",
            "crystalmir-white-stag-probe-16-20",
            "shadow-keep-undead-soldier-probe-16-20",
            "galaxy-white-dwarf-probe-17-20",
            "galaxy-red-supergiant-probe-17-20",
            "hightower-jailor-probe-17-20",
            "hightower-jailor-hunt-17-20",
            "dwarven-nobleman-thief-probe-17-18",
            "dwarven-servant-thief-probe-17-18",
            "dwarven-servant-thief-hunt-17-18",
            "moria-sanctuary-thief-17-20",
            "pyramid-ali-baba-probe-18-20",
        )
    }
    recorded_results["shire-elven-wizard-probe-17-20"] = {
        "observed": True,
        "viable": True,
        "boot_id": "boot-1",
    }

    policy = policy_for(
        18,
        "thief",
        last_policy_id="pyramid-ali-baba-probe-18-20",
        world_boot_id="boot-1",
        research_results=recorded_results,
    )

    assert policy.policy_id == "shire-dwarven-prince-thief-probe-17-20"
    assert policy.execution == "shire-dwarven-prince-research"
    assert policy.status == "research"


def test_level_eighteen_thief_opens_thain_after_absent_prince_probe() -> None:
    recorded_results = {
        policy_id: {
            "observed": False,
            "viable": False,
            "absent": True,
            "boot_id": "boot-1",
        }
        for policy_id in (
            "mirror-realm-watchman-probe-16-20",
            "crystalmir-white-stag-probe-16-20",
            "shadow-keep-undead-soldier-probe-16-20",
            "galaxy-white-dwarf-probe-17-20",
            "galaxy-red-supergiant-probe-17-20",
            "hightower-jailor-probe-17-20",
            "hightower-jailor-hunt-17-20",
            "dwarven-nobleman-thief-probe-17-18",
            "dwarven-servant-thief-probe-17-18",
            "dwarven-servant-thief-hunt-17-18",
            "moria-sanctuary-thief-17-20",
            "pyramid-ali-baba-probe-18-20",
            "shire-dwarven-prince-thief-probe-17-20",
            "shire-dwarven-prince-thief-hunt-17-20",
        )
    }
    recorded_results["shire-elven-wizard-probe-17-20"] = {
        "observed": True,
        "viable": True,
        "boot_id": "boot-1",
    }

    policy = policy_for(
        18,
        "thief",
        last_policy_id="pyramid-ali-baba-probe-18-20",
        world_boot_id="boot-1",
        research_results=recorded_results,
    )

    assert policy.policy_id == "shire-thain-probe-17-20"
    assert policy.execution == "shire-thain-research"
    assert policy.status == "research"


def test_viable_pyramid_probe_promotes_to_hunt_without_sanctuary() -> None:
    recorded_results = {
        policy_id: {
            "observed": False,
            "viable": False,
            "absent": True,
            "boot_id": "boot-1",
        }
        for policy_id in (
            "mirror-realm-watchman-probe-16-20",
            "crystalmir-white-stag-probe-16-20",
            "shadow-keep-undead-soldier-probe-16-20",
            "galaxy-white-dwarf-probe-17-20",
            "galaxy-red-supergiant-probe-17-20",
            "dwarven-nobleman-thief-probe-17-18",
            "dwarven-nobleman-thief-hunt-17-18",
            "dwarven-servant-thief-probe-17-18",
            "dwarven-servant-thief-hunt-17-18",
            "hightower-jailor-probe-17-20",
            "hightower-jailor-hunt-17-20",
            "shire-dwarven-prince-thief-probe-17-20",
            "shire-dwarven-prince-thief-hunt-17-20",
            "shire-thain-probe-17-20",
            "shire-thain-hunt-17-20",
        )
    }
    recorded_results["pyramid-ali-baba-probe-18-20"] = {
        "observed": True,
        "viable": True,
        "boot_id": "boot-1",
    }

    policy = policy_for(
        18,
        "thief",
        has_sanctuary_potion=False,
        last_policy_id="pyramid-ali-baba-probe-18-20",
        world_boot_id="boot-1",
        research_results=recorded_results,
    )

    assert policy.policy_id == "pyramid-ali-baba-hunt-18-20"
    assert policy.execution == "pyramid-ali-baba-hunt"
    assert policy.segment_kill_limit == 1


def test_crowded_research_probe_rotates_before_immediate_retry() -> None:
    recorded_results = {
        policy_id: {
            "observed": False,
            "viable": False,
            "boot_id": "boot-1",
        }
        for policy_id in (
            "mirror-realm-watchman-probe-16-20",
            "crystalmir-white-stag-probe-16-20",
            "shadow-keep-undead-soldier-probe-16-20",
            "galaxy-white-dwarf-probe-17-20",
            "galaxy-red-supergiant-probe-17-20",
            "dwarven-nobleman-thief-probe-17-18",
            "dwarven-nobleman-thief-hunt-17-18",
            "dwarven-servant-thief-probe-17-18",
            "dwarven-servant-thief-hunt-17-18",
            "shire-dwarven-prince-thief-probe-17-20",
            "shire-dwarven-prince-thief-hunt-17-20",
        )
    }

    policy = policy_for(
        18,
        "thief",
        last_policy_id="shire-dwarven-prince-thief-probe-17-20",
        last_fastwalk_abort_reason=(
            "field room contained 3 observed mobiles while evaluating "
            "'dwarven prince'"
        ),
        world_boot_id="boot-1",
        research_results=recorded_results,
    )

    assert policy.policy_id == "shire-thain-probe-17-20"
    assert policy.execution == "shire-thain-research"


def test_viable_shire_thain_probe_promotes_bounded_hunt() -> None:
    research_results = {
        policy_id: {
            "observed": True,
            "viable": False,
            "boot_id": "boot-1",
        }
        for policy_id in (
            "mirror-realm-watchman-probe-16-20",
            "crystalmir-white-stag-probe-16-20",
            "shadow-keep-undead-soldier-probe-16-20",
            "galaxy-white-dwarf-probe-17-20",
            "galaxy-red-supergiant-probe-17-20",
            "dwarven-nobleman-thief-probe-17-18",
            "dwarven-nobleman-thief-hunt-17-18",
            "dwarven-servant-thief-probe-17-18",
            "dwarven-servant-thief-hunt-17-18",
            "shire-dwarven-prince-thief-probe-17-20",
            "shire-dwarven-prince-thief-hunt-17-20",
        )
    }
    research_results["shire-thain-probe-17-20"] = {
        "observed": True,
        "viable": True,
        "boot_id": "boot-1",
    }
    policy = policy_for(
        18,
        "thief",
        last_policy_id="shire-thain-probe-17-20",
        world_boot_id="boot-1",
        research_results=research_results,
    )

    assert policy.policy_id == "shire-thain-hunt-17-20"
    assert policy.execution == "shire-thain-hunt"


def test_absent_shire_thain_rotates_to_the_next_shire_research_probe() -> None:
    recorded_results = {
        policy_id: {
            "observed": True,
            "viable": False,
            "boot_id": "boot-1",
        }
        for policy_id in (
            "mirror-realm-watchman-probe-16-20",
            "crystalmir-white-stag-probe-16-20",
            "shadow-keep-undead-soldier-probe-16-20",
            "galaxy-white-dwarf-probe-17-20",
            "galaxy-red-supergiant-probe-17-20",
            "hightower-jailor-probe-17-20",
            "dwarven-nobleman-thief-probe-17-18",
            "dwarven-nobleman-thief-hunt-17-18",
            "dwarven-servant-thief-probe-17-18",
            "dwarven-servant-thief-hunt-17-18",
            "shire-dwarven-prince-thief-probe-17-20",
            "shire-dwarven-prince-thief-hunt-17-20",
        )
    }
    recorded_results["shire-thain-probe-17-20"] = {
        "absent": True,
        "observed": False,
        "viable": False,
        "boot_id": "boot-1",
    }

    policy = policy_for(
        18,
        "thief",
        last_policy_id="shire-thain-probe-17-20",
        world_boot_id="boot-1",
        research_results=recorded_results,
    )

    assert policy.policy_id == "shire-elven-wizard-probe-17-20"
    assert policy.execution == "shire-elven-wizard-research"
    assert policy.status == "research"


def test_absent_shire_thain_enters_viable_wizard_sanctuary_path() -> None:
    recorded_results = {
        policy_id: {
            "observed": True,
            "viable": False,
            "boot_id": "boot-1",
        }
        for policy_id in (
            "mirror-realm-watchman-probe-16-20",
            "crystalmir-white-stag-probe-16-20",
            "shadow-keep-undead-soldier-probe-16-20",
            "galaxy-white-dwarf-probe-17-20",
            "galaxy-red-supergiant-probe-17-20",
            "hightower-jailor-probe-17-20",
            "dwarven-nobleman-thief-probe-17-18",
            "dwarven-nobleman-thief-hunt-17-18",
            "dwarven-servant-thief-probe-17-18",
            "dwarven-servant-thief-hunt-17-18",
            "shire-dwarven-prince-thief-probe-17-20",
            "shire-dwarven-prince-thief-hunt-17-20",
        )
    }
    recorded_results["shire-thain-probe-17-20"] = {
        "absent": True,
        "observed": False,
        "viable": False,
        "boot_id": "boot-1",
    }
    recorded_results["shire-elven-wizard-probe-17-20"] = {
        "observed": True,
        "viable": True,
        "boot_id": "boot-1",
    }

    policy = policy_for(
        18,
        "thief",
        has_sanctuary_potion=False,
        last_policy_id="shire-thain-probe-17-20",
        world_boot_id="boot-1",
        research_results=recorded_results,
    )

    assert policy.policy_id == "moria-sanctuary-thief-17-20"
    assert policy.execution == "moria-sanctuary-hunt"
    assert policy.status == "research"


def test_absent_thain_reuses_productive_wizard_hunt_after_probe_and_hunt() -> None:
    recorded_results = {
        policy_id: {
            "observed": True,
            "viable": False,
            "boot_id": "boot-1",
        }
        for policy_id in (
            "mirror-realm-watchman-probe-16-20",
            "crystalmir-white-stag-probe-16-20",
            "shadow-keep-undead-soldier-probe-16-20",
            "galaxy-white-dwarf-probe-17-20",
            "galaxy-red-supergiant-probe-17-20",
            "hightower-jailor-probe-17-20",
            "dwarven-nobleman-thief-probe-17-18",
            "dwarven-nobleman-thief-hunt-17-18",
            "dwarven-servant-thief-probe-17-18",
            "dwarven-servant-thief-hunt-17-18",
            "shire-dwarven-prince-thief-probe-17-20",
            "shire-dwarven-prince-thief-hunt-17-20",
        )
    }
    recorded_results["shire-thain-probe-17-20"] = {
        "absent": True,
        "observed": False,
        "viable": False,
        "boot_id": "boot-1",
    }
    recorded_results["shire-elven-wizard-probe-17-20"] = {
        "observed": True,
        "viable": True,
        "boot_id": "boot-1",
    }
    recorded_results["shire-elven-wizard-hunt-17-20"] = {
        "observed": True,
        "viable": True,
        "boot_id": "boot-1",
    }

    policy = policy_for(
        18,
        "thief",
        has_sanctuary_potion=True,
        last_policy_id="shire-thain-probe-17-20",
        policy_xp_deltas={"shire-elven-wizard-hunt-17-20": 1048},
        world_boot_id="boot-1",
        research_results=recorded_results,
    )

    assert policy.policy_id == "shire-elven-wizard-hunt-17-20"
    assert policy.execution == "shire-elven-wizard-hunt"


def test_viable_shire_wizard_requires_sanctuary_before_hunt() -> None:
    recorded_results = {
        policy_id: {
            "observed": True,
            "viable": False,
            "boot_id": "boot-1",
        }
        for policy_id in (
            "mirror-realm-watchman-probe-16-20",
            "crystalmir-white-stag-probe-16-20",
            "shadow-keep-undead-soldier-probe-16-20",
            "galaxy-white-dwarf-probe-17-20",
            "galaxy-red-supergiant-probe-17-20",
            "hightower-jailor-probe-17-20",
            "dwarven-nobleman-thief-probe-17-18",
            "dwarven-nobleman-thief-hunt-17-18",
            "dwarven-servant-thief-probe-17-18",
            "dwarven-servant-thief-hunt-17-18",
            "shire-dwarven-prince-thief-probe-17-20",
            "shire-dwarven-prince-thief-hunt-17-20",
        )
    }
    recorded_results["shire-elven-wizard-probe-17-20"] = {
        "observed": True,
        "viable": True,
        "boot_id": "boot-1",
    }

    policy = policy_for(
        18,
        "thief",
        last_policy_id="shire-elven-wizard-probe-17-20",
        world_boot_id="boot-1",
        research_results=recorded_results,
    )

    assert policy.policy_id == "moria-sanctuary-thief-17-20"
    assert policy.execution == "moria-sanctuary-hunt"


def test_productive_shire_wizard_history_cannot_bypass_sanctuary_gate() -> None:
    research_results = _level_eighteen_research_outcomes()
    research_results.update(
        {
            "shire-elven-wizard-probe-17-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "shire-elven-wizard-hunt-17-20": {
                "observed": True,
                "viable": True,
                "completed_kill": True,
                "boot_id": "boot-1",
            },
        }
    )

    policy = policy_for(
        18,
        "thief",
        last_policy_id="shadow-keep-undead-soldier-hunt-16-20",
        policy_xp_deltas={"shire-elven-wizard-hunt-17-20": 1_048},
        world_boot_id="boot-1",
        research_results=research_results,
    )

    assert policy.policy_id == "moria-sanctuary-thief-17-20"
    assert policy.execution == "moria-sanctuary-hunt"


def test_productive_shire_wizard_history_defers_while_moria_is_crowded() -> None:
    research_results = _level_eighteen_research_outcomes()
    research_results.update(
        {
            "moria-sanctuary-thief-17-20": {
                "observed": False,
                "viable": False,
                "crowded": True,
                "boot_id": "boot-1",
            },
            "shire-elven-wizard-probe-17-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "shire-elven-wizard-hunt-17-20": {
                "observed": True,
                "viable": True,
                "completed_kill": True,
                "boot_id": "boot-1",
            },
        }
    )

    policy = policy_for(
        18,
        "thief",
        last_policy_id="shadow-keep-undead-soldier-hunt-16-20",
        policy_xp_deltas={"shire-elven-wizard-hunt-17-20": 1_048},
        research_results=research_results,
        research_crowd_cooldowns={"moria-sanctuary-thief-17-20": 1},
        world_boot_id="boot-1",
    )

    assert policy.executable is False
    assert policy.policy_id == "unregistered-10-100"
    assert "crowd cooldown" in policy.summary


@pytest.mark.parametrize(
    "last_policy_id",
    [
        "shire-elven-wizard-probe-17-20",
        "moria-sanctuary-thief-17-20",
    ],
)
def test_shire_wizard_hunt_requires_and_uses_sanctuary(
    last_policy_id: str,
) -> None:
    recorded_results = {
        policy_id: {
            "observed": True,
            "viable": False,
            "boot_id": "boot-1",
        }
        for policy_id in (
            "mirror-realm-watchman-probe-16-20",
            "crystalmir-white-stag-probe-16-20",
            "shadow-keep-undead-soldier-probe-16-20",
            "galaxy-white-dwarf-probe-17-20",
            "galaxy-red-supergiant-probe-17-20",
            "hightower-jailor-probe-17-20",
            "dwarven-nobleman-thief-probe-17-18",
            "dwarven-nobleman-thief-hunt-17-18",
            "dwarven-servant-thief-probe-17-18",
            "dwarven-servant-thief-hunt-17-18",
            "shire-dwarven-prince-thief-probe-17-20",
            "shire-dwarven-prince-thief-hunt-17-20",
        )
    }
    recorded_results["shire-elven-wizard-probe-17-20"] = {
        "observed": True,
        "viable": True,
        "boot_id": "boot-1",
    }

    policy = policy_for(
        18,
        "thief",
        has_sanctuary_potion=True,
        last_policy_id=last_policy_id,
        world_boot_id="boot-1",
        research_results=recorded_results,
    )

    assert policy.policy_id == "shire-elven-wizard-hunt-17-20"
    assert policy.execution == "shire-elven-wizard-hunt"
    assert policy.segment_kill_limit == 1


def test_cleared_moria_absence_reopens_the_required_wizard_reserve() -> None:
    research_results = {
        policy_id: {
            "observed": True,
            "viable": False,
            "boot_id": "boot-1",
        }
        for policy_id in (
            "mirror-realm-watchman-probe-16-20",
            "crystalmir-white-stag-probe-16-20",
            "shadow-keep-undead-soldier-probe-16-20",
            "galaxy-white-dwarf-probe-17-20",
            "galaxy-red-supergiant-probe-17-20",
            "hightower-jailor-probe-17-20",
            "dwarven-nobleman-thief-probe-17-18",
            "dwarven-nobleman-thief-hunt-17-18",
            "dwarven-servant-thief-probe-17-18",
            "dwarven-servant-thief-hunt-17-18",
            "shire-dwarven-prince-thief-probe-17-20",
            "shire-dwarven-prince-thief-hunt-17-20",
        )
    }
    research_results["shire-elven-wizard-probe-17-20"] = {
        "observed": True,
        "viable": True,
        "boot_id": "boot-1",
    }
    policy = policy_for(
        18,
        "thief",
        last_policy_id="moria-sanctuary-thief-17-20",
        world_boot_id="boot-1",
        research_results=research_results,
    )

    assert policy.policy_id == "moria-sanctuary-thief-17-20"
    assert policy.execution == "moria-sanctuary-hunt"


def test_incomplete_moria_sanctuary_recovery_retries_missing_potion() -> None:
    research_results = {
        policy_id: {
            "observed": True,
            "viable": False,
            "boot_id": "boot-1",
        }
        for policy_id in (
            "mirror-realm-watchman-probe-16-20",
            "crystalmir-white-stag-probe-16-20",
            "shadow-keep-undead-soldier-probe-16-20",
            "galaxy-white-dwarf-probe-17-20",
            "galaxy-red-supergiant-probe-17-20",
            "hightower-jailor-probe-17-20",
            "dwarven-nobleman-thief-probe-17-18",
            "dwarven-nobleman-thief-hunt-17-18",
            "dwarven-servant-thief-probe-17-18",
            "dwarven-servant-thief-hunt-17-18",
            "shire-dwarven-prince-thief-probe-17-20",
            "shire-dwarven-prince-thief-hunt-17-20",
        )
    }
    research_results["shire-elven-wizard-probe-17-20"] = {
        "observed": True,
        "viable": True,
        "boot_id": "boot-1",
    }
    research_results["moria-sanctuary-thief-17-20"] = {
        "observed": True,
        "viable": False,
        "completed_kill": False,
        "boot_id": "boot-1",
    }

    policy = policy_for(
        18,
        "thief",
        has_sanctuary_potion=False,
        last_policy_id="moria-sanctuary-thief-17-20",
        world_boot_id="boot-1",
        research_results=research_results,
        excluded_policy_ids=frozenset({"moria-sanctuary-thief-17-20"}),
    )

    assert policy.policy_id == "moria-sanctuary-thief-17-20"
    assert policy.execution == "moria-sanctuary-hunt"


def test_historical_sanctuary_recovery_reopens_after_caster_hunt_failure() -> None:
    research_results = {
        policy_id: {
            "observed": False,
            "viable": False,
            "absent": True,
            "boot_id": "boot-1",
        }
        for policy_id in (
            "mirror-realm-watchman-probe-16-20",
            "crystalmir-white-stag-probe-16-20",
            "shadow-keep-undead-soldier-probe-16-20",
            "shadow-keep-undead-soldier-hunt-16-20",
            "galaxy-white-dwarf-probe-17-20",
            "dwarven-nobleman-thief-probe-17-18",
            "dwarven-nobleman-thief-hunt-17-18",
            "dwarven-servant-thief-probe-17-18",
            "dwarven-servant-thief-hunt-17-18",
            "shire-dwarven-prince-thief-probe-17-20",
            "shire-dwarven-prince-thief-hunt-17-20",
            "shire-thain-probe-17-20",
            "shire-thain-hunt-17-20",
            "pyramid-ali-baba-probe-18-20",
            "pyramid-ali-baba-hunt-18-20",
            "galaxy-red-supergiant-hunt-17-20",
        )
    }
    research_results.update(
        {
            "hightower-jailor-probe-17-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "hightower-jailor-hunt-17-20": {
                "observed": True,
                "viable": False,
                "completed_kill": False,
                "boot_id": "boot-1",
            },
            "shire-elven-wizard-probe-17-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "shire-elven-wizard-hunt-17-20": {
                "observed": True,
                "viable": False,
                "completed_kill": False,
                "boot_id": "boot-1",
            },
            "moria-sanctuary-thief-17-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
        }
    )

    policy = policy_for(
        18,
        "thief",
        has_sanctuary_potion=False,
        has_acquired_sanctuary_potion=True,
        has_flight=True,
        last_policy_id="galaxy-red-supergiant-hunt-17-20",
        world_boot_id="boot-1",
        research_results=research_results,
        excluded_policy_ids=frozenset(
            {
                "moria-sanctuary-thief-17-20",
                "mahntor-rock-toad-thief-circuit-16-18",
                "plains-aruncus-thief-fallback-17-18",
            }
        ),
    )

    assert policy.policy_id == "moria-sanctuary-thief-17-20"
    assert policy.execution == "moria-sanctuary-hunt"
    assert "Replenish" in policy.summary


def test_explicit_moria_absence_does_not_loop_after_historical_acquisition() -> None:
    policy = policy_for(
        18,
        "thief",
        has_sanctuary_potion=False,
        has_acquired_sanctuary_potion=True,
        has_flight=True,
        last_policy_id="galaxy-red-supergiant-hunt-17-20",
        world_boot_id="boot-1",
        research_results={
            "moria-sanctuary-thief-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shire-elven-wizard-hunt-17-20": {
                "observed": True,
                "viable": False,
                "completed_kill": False,
                "boot_id": "boot-1",
            },
            "hightower-jailor-hunt-17-20": {
                "observed": True,
                "viable": False,
                "completed_kill": False,
                "boot_id": "boot-1",
            },
        },
        excluded_policy_ids=frozenset(
            {
                "moria-sanctuary-thief-17-20",
                "mahntor-rock-toad-thief-circuit-16-18",
                "plains-aruncus-thief-fallback-17-18",
            }
        ),
    )

    assert policy.policy_id != "moria-sanctuary-thief-17-20"


def test_level_eighteen_reuses_productive_hunt_after_crowded_probe() -> None:
    research_results = {
        policy_id: {
            "observed": False,
            "viable": False,
            "absent": True,
            "boot_id": "boot-1",
        }
        for policy_id in (
            "mirror-realm-watchman-probe-16-20",
            "crystalmir-white-stag-probe-16-20",
            "shadow-keep-undead-soldier-probe-16-20",
            "galaxy-red-supergiant-probe-17-20",
            "dwarven-nobleman-thief-probe-17-18",
            "dwarven-servant-thief-probe-17-18",
            "dwarven-servant-thief-hunt-17-18",
        )
    }
    research_results.update(
        {
            "galaxy-white-dwarf-probe-17-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-hunt-17-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
        }
    )

    policy = policy_for(
        18,
        "thief",
        last_policy_id="shire-dwarven-prince-thief-probe-17-20",
        last_fastwalk_abort_reason=(
            "field room contained 3 observed mobiles while evaluating "
            "'dwarven prince'"
        ),
        policy_xp_deltas={"galaxy-white-dwarf-hunt-17-20": 655},
        excluded_policy_ids=frozenset(
            {"mahntor-rock-toad-thief-circuit-16-18"}
        ),
        world_boot_id="boot-1",
        research_results=research_results,
    )

    assert policy.policy_id == "galaxy-white-dwarf-hunt-17-20"
    assert policy.execution == "galaxy-white-dwarf-hunt"


def test_level_eighteen_crowded_moria_defers_to_productive_keeper_hunt() -> None:
    research_results = _level_eighteen_research_outcomes()
    research_results.update(
        {
            "moria-sanctuary-thief-17-20": {
                "observed": False,
                "viable": False,
                "crowded": True,
                "boot_id": "boot-1",
            },
            "highland-keeper-probe-17-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "highland-keeper-hunt-17-20": {
                "observed": True,
                "viable": True,
                "completed_kill": True,
                "boot_id": "boot-1",
            },
        }
    )

    policy = policy_for(
        18,
        "thief",
        has_flight=True,
        has_acquired_sanctuary_potion=True,
        last_policy_id="moria-sanctuary-thief-17-20",
        policy_xp_deltas={"highland-keeper-hunt-17-20": 1159},
        research_results=research_results,
        research_crowd_cooldowns={"moria-sanctuary-thief-17-20": 3},
        world_boot_id="boot-1",
    )

    assert policy.policy_id == "highland-keeper-hunt-17-20"
    assert policy.execution == "highland-keeper-hunt"


def test_viable_shire_prince_probe_promotes_bounded_hunt() -> None:
    research_results = {
        "mirror-realm-watchman-probe-16-20": {
            "observed": True,
            "viable": False,
            "boot_id": "boot-1",
        },
        "crystalmir-white-stag-probe-16-20": {
            "observed": False,
            "viable": False,
            "absent": True,
            "boot_id": "boot-1",
        },
        "shadow-keep-undead-soldier-probe-16-20": {
            "observed": True,
            "viable": True,
            "boot_id": "boot-1",
        },
        "shadow-keep-undead-soldier-hunt-16-20": {
            "observed": False,
            "viable": False,
            "absent": True,
            "boot_id": "boot-1",
        },
        "galaxy-white-dwarf-probe-17-20": {
            "observed": False,
            "viable": False,
            "absent": True,
            "boot_id": "boot-1",
        },
        "galaxy-red-supergiant-probe-17-20": {
            "observed": False,
            "viable": False,
            "absent": True,
            "boot_id": "boot-1",
        },
        "dwarven-nobleman-thief-probe-17-18": {
            "observed": False,
            "viable": False,
            "absent": True,
            "boot_id": "boot-1",
        },
        "dwarven-nobleman-thief-hunt-17-18": {
            "observed": False,
            "viable": False,
            "absent": True,
            "boot_id": "boot-1",
        },
        "dwarven-servant-thief-probe-17-18": {
            "observed": True,
            "viable": True,
            "boot_id": "boot-1",
        },
        "dwarven-servant-thief-hunt-17-18": {
            "observed": True,
            "viable": False,
            "unattackable": "dwarven servant",
            "boot_id": "boot-1",
        },
        "shire-dwarven-prince-thief-probe-17-20": {
            "observed": True,
            "viable": True,
            "boot_id": "boot-1",
        },
    }

    policy = policy_for(
        18,
        "thief",
        last_policy_id="shire-dwarven-prince-thief-probe-17-20",
        world_boot_id="boot-1",
        research_results=research_results,
    )

    assert policy.policy_id == "shire-dwarven-prince-thief-hunt-17-20"
    assert policy.execution == "shire-dwarven-prince-hunt"
    assert policy.segment_kill_limit == 1


def test_uncompleted_nobleman_hunt_retries_after_resource_withdrawal() -> None:
    policy = policy_for(
        17,
        "thief",
        last_policy_id="dwarven-nobleman-thief-hunt-17-18",
        last_fastwalk_abort_reason=(
            "field expedition withdrew before target evaluation because "
            "food reserve was unavailable"
        ),
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-nobleman-thief-probe-17-18": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "dwarven-nobleman-thief-hunt-17-18"
    assert policy.execution == "dwarven-nobleman-hunt"


def test_completed_level_seventeen_nobleman_hunt_repeats_when_fallbacks_are_excluded() -> None:
    policy = policy_for(
        17,
        "thief",
        last_policy_id="dwarven-nobleman-thief-hunt-17-18",
        world_boot_id="boot-1",
        policy_xp_deltas={"dwarven-nobleman-thief-hunt-17-18": 670},
        excluded_policy_ids=frozenset(
            {
                "mahntor-rock-toad-thief-circuit-16-18",
                "plains-aruncus-thief-fallback-17-18",
            }
        ),
        research_results={
            "dwarven-nobleman-thief-probe-17-18": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "dwarven-nobleman-thief-hunt-17-18": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "dwarven-nobleman-thief-hunt-17-18"
    assert policy.execution == "dwarven-nobleman-hunt"


def test_level_seventeen_nobleman_retries_known_approach_interrupt() -> None:
    policy = policy_for(
        17,
        "thief",
        last_policy_id="dwarven-nobleman-thief-hunt-17-18",
        last_fastwalk_abort_reason=(
            "unexpected combat interrupted fastwalk 'dwarven nobleman' "
            "before its objective"
        ),
        world_boot_id="boot-1",
        policy_xp_deltas={"dwarven-nobleman-thief-hunt-17-18": -208},
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-nobleman-thief-probe-17-18": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "dwarven-nobleman-thief-hunt-17-18": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "dwarven-nobleman-thief-hunt-17-18"
    assert policy.execution == "dwarven-nobleman-hunt"


def test_crowded_level_seventeen_nobleman_hunt_retries_probe() -> None:
    policy = policy_for(
        17,
        "thief",
        last_policy_id="dwarven-nobleman-thief-hunt-17-18",
        last_fastwalk_abort_reason=(
            "field room contained 4 observed mobiles while evaluating "
            "'dwarven nobleman'"
        ),
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-nobleman-thief-probe-17-18": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "dwarven-nobleman-thief-probe-17-18"
    assert policy.execution == "dwarven-nobleman-research"


def test_assisted_level_seventeen_nobleman_hunt_retries_bounded_hunt() -> None:
    policy = policy_for(
        17,
        "thief",
        last_policy_id="dwarven-nobleman-thief-hunt-17-18",
        last_fastwalk_abort_reason=(
            "field combat aborted after unapproved attacker 'A guest' joined"
        ),
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-nobleman-thief-probe-17-18": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "dwarven-nobleman-thief-hunt-17-18"
    assert policy.execution == "dwarven-nobleman-hunt"


def test_level_sixteen_waits_after_both_fallbacks_reject() -> None:
    policy = policy_for(
        16,
        "mage",
        last_policy_id="shadow-keep-undead-soldier-probe-16-20",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.status == "unavailable"
    assert "wait for a new reboot" in policy.summary


def test_level_sixteen_thief_uses_proven_toad_after_both_probes_reject() -> None:
    policy = policy_for(
        16,
        "thief",
        last_policy_id="shadow-keep-undead-soldier-probe-16-20",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "mahntor-rock-toad-thief-circuit-16-18"
    assert policy.execution == "mahntor-rock-toad-circuit"
    assert policy.status == "verified"
    assert policy.segment_kill_limit == 2


def test_level_sixteen_thief_tries_bardoosh_once_after_empty_toads() -> None:
    policy = policy_for(
        16,
        "thief",
        world_boot_id="boot-1",
        policy_xp_deltas={
            "mahntor-rock-toad-thief-circuit-16-18": 0,
        },
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-nobleman-thief-probe-17-18": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "ambush-bardoosh-thief-kill-research-16"
    assert policy.execution == "ambush-bardoosh-hunt"
    assert policy.status == "research"
    assert policy.segment_kill_limit == 1


def test_level_sixteen_thief_returns_to_toads_after_bardoosh_attempt() -> None:
    policy = policy_for(
        16,
        "thief",
        world_boot_id="boot-1",
        policy_xp_deltas={
            "mahntor-rock-toad-thief-circuit-16-18": 0,
            "ambush-bardoosh-thief-kill-research-16": 0,
        },
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-nobleman-thief-probe-17-18": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-servant-thief-probe-17-18": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "mahntor-rock-toad-thief-circuit-16-18"


@pytest.mark.parametrize("level", [17, 18])
@pytest.mark.parametrize("toad_xp", [0, 325])
def test_later_thief_rotates_every_toad_pass_to_aruncus(
    level: int,
    toad_xp: int,
) -> None:
    policy = policy_for(
        level,
        "thief",
        last_policy_id="mahntor-rock-toad-thief-circuit-16-18",
        world_boot_id="boot-1",
        policy_xp_deltas={
            "mahntor-rock-toad-thief-circuit-16-18": toad_xp,
        },
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-nobleman-thief-probe-17-18": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-servant-thief-probe-17-18": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "plains-aruncus-thief-fallback-17-18"
    assert policy.execution == "plains-aruncus-hunt"
    assert policy.status == "verified"
    assert policy.segment_kill_limit == 1
    assert any("strange amulet" in item for item in policy.evidence)


def test_later_thief_keeps_toad_fallback_when_aruncus_is_excluded() -> None:
    policy = policy_for(
        18,
        "thief",
        last_policy_id="mahntor-rock-toad-thief-circuit-16-18",
        world_boot_id="boot-1",
        excluded_policy_ids=frozenset(
            {"plains-aruncus-thief-fallback-17-18"}
        ),
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-hunt-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "galaxy-red-supergiant-hunt-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-nobleman-thief-probe-17-18": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-servant-thief-probe-17-18": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "dwarven-servant-thief-hunt-17-18": {
                "observed": True,
                "viable": False,
                "unattackable": "dwarven servant",
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "mahntor-rock-toad-thief-circuit-16-18"
    assert policy.execution == "mahntor-rock-toad-circuit"
    assert policy.executable is True


def test_level_eighteen_thief_uses_late_bardoosh_after_excluded_empty_toads() -> None:
    policy = policy_for(
        18,
        "thief",
        last_policy_id="mahntor-rock-toad-thief-circuit-16-18",
        world_boot_id="boot-1",
        excluded_policy_ids=frozenset(
            {"plains-aruncus-thief-fallback-17-18"}
        ),
        policy_xp_deltas={
            "mahntor-rock-toad-thief-circuit-16-18": 0,
        },
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "galaxy-red-supergiant-hunt-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-nobleman-thief-probe-17-18": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-servant-thief-probe-17-18": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "ambush-bardoosh-thief-kill-research-17-18"
    assert policy.execution == "ambush-bardoosh-hunt"
    assert policy.status == "research"
    assert policy.segment_kill_limit == 1


def test_level_eighteen_thief_enters_late_bardoosh_after_aruncus_exclusion() -> None:
    policy = policy_for(
        18,
        "thief",
        last_policy_id="plains-aruncus-thief-fallback-17-18",
        world_boot_id="boot-1",
        excluded_policy_ids=frozenset(
            {
                "mahntor-rock-toad-thief-circuit-16-18",
                "plains-aruncus-thief-fallback-17-18",
            }
        ),
        policy_xp_deltas={
            "mahntor-rock-toad-thief-circuit-16-18": 0,
            "plains-aruncus-thief-fallback-17-18": 0,
        },
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "dwarven-nobleman-thief-probe-17-18": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "dwarven-servant-thief-probe-17-18": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "ambush-bardoosh-thief-kill-research-17-18"
    assert policy.execution == "ambush-bardoosh-hunt"
    assert policy.status == "research"


def test_level_eighteen_thief_advances_from_rejected_bardoosh_to_hightower() -> None:
    policy = policy_for(
        18,
        "thief",
        last_policy_id="ambush-bardoosh-thief-kill-research-17-18",
        world_boot_id="boot-1",
        excluded_policy_ids=frozenset(
            {
                "mahntor-rock-toad-thief-circuit-16-18",
                "plains-aruncus-thief-fallback-17-18",
                "ambush-bardoosh-thief-kill-research-17-18",
            }
        ),
        policy_xp_deltas={
            "ambush-bardoosh-thief-kill-research-17-18": 0,
        },
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "dwarven-nobleman-thief-probe-17-18": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "dwarven-servant-thief-probe-17-18": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "ambush-bardoosh-thief-kill-research-17-18": {
                "observed": True,
                "viable": False,
                "completed_kill": False,
                "boot_id": "boot-1",
            },
            "hightower-jailor-probe-17-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "hightower-jailor-hunt-17-20"
    assert policy.execution == "hightower-jailor-hunt"
    assert policy.status == "research"


def test_level_eighteen_thief_revisits_hightower_after_current_band_probes() -> None:
    policy = policy_for(
        18,
        "thief",
        last_policy_id="crystalmir-white-stag-probe-16-20",
        world_boot_id="boot-1",
        excluded_policy_ids=frozenset(
            {
                "mahntor-rock-toad-thief-circuit-16-18",
                "plains-aruncus-thief-fallback-17-18",
            }
        ),
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "dwarven-nobleman-thief-probe-17-18": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "dwarven-servant-thief-probe-17-18": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "hightower-jailor-probe-17-20": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "hightower-jailor-hunt-17-20"
    assert policy.execution == "hightower-jailor-hunt"
    assert policy.status == "research"


def test_late_bardoosh_probe_promotes_then_returns_to_toads() -> None:
    promoted = policy_for(
        18,
        "thief",
        last_policy_id="ambush-bardoosh-thief-kill-research-17-18",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "galaxy-red-supergiant-hunt-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-nobleman-thief-probe-17-18": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-servant-thief-probe-17-18": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "ambush-bardoosh-thief-kill-research-17-18": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            }
        },
    )

    assert promoted.policy_id == "ambush-bardoosh-thief-hunt-17-18"
    assert promoted.status == "verified"

    returned = policy_for(
        18,
        "thief",
        last_policy_id="ambush-bardoosh-thief-hunt-17-18",
        world_boot_id="boot-1",
        policy_xp_deltas={
            "ambush-bardoosh-thief-hunt-17-18": 450,
        },
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "galaxy-red-supergiant-hunt-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-nobleman-thief-probe-17-18": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-servant-thief-probe-17-18": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "ambush-bardoosh-thief-kill-research-17-18": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
            "ambush-bardoosh-thief-hunt-17-18": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert returned.policy_id == "mahntor-rock-toad-thief-circuit-16-18"


@pytest.mark.parametrize("level", [17, 18])
@pytest.mark.parametrize("aruncus_xp", [0, 400])
def test_later_thief_returns_to_toads_after_aruncus(
    level: int,
    aruncus_xp: int,
) -> None:
    policy = policy_for(
        level,
        "thief",
        last_policy_id="plains-aruncus-thief-fallback-17-18",
        world_boot_id="boot-1",
        policy_xp_deltas={
            "plains-aruncus-thief-fallback-17-18": aruncus_xp,
            "mahntor-rock-toad-thief-circuit-16-18": 0,
        },
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-white-dwarf-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "galaxy-red-supergiant-probe-17-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-nobleman-thief-probe-17-18": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "dwarven-servant-thief-probe-17-18": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "mahntor-rock-toad-thief-circuit-16-18"


def test_level_sixteen_thief_promotes_bardoosh_after_productive_toads() -> None:
    policy = policy_for(
        16,
        "thief",
        last_policy_id="mahntor-rock-toad-thief-circuit-16-18",
        world_boot_id="boot-1",
        policy_xp_deltas={
            "mahntor-rock-toad-thief-circuit-16-18": 478,
            "ambush-bardoosh-thief-kill-research-16": 535,
        },
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "ambush-bardoosh-thief-hunt-16"
    assert policy.execution == "ambush-bardoosh-hunt"
    assert policy.status == "verified"
    assert policy.segment_kill_limit == 1


def test_level_sixteen_thief_rotates_empty_toads_to_productive_bardoosh() -> None:
    policy = policy_for(
        16,
        "thief",
        last_policy_id="mahntor-rock-toad-thief-circuit-16-18",
        world_boot_id="boot-1",
        policy_xp_deltas={
            "mahntor-rock-toad-thief-circuit-16-18": 0,
            "ambush-bardoosh-thief-kill-research-16": 535,
            "ambush-bardoosh-thief-hunt-16": 358,
        },
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "ambush-bardoosh-thief-hunt-16"
    assert policy.execution == "ambush-bardoosh-hunt"


def test_level_sixteen_thief_does_not_repoll_bardoosh_after_empty_toads() -> None:
    policy = policy_for(
        16,
        "thief",
        last_policy_id="mahntor-rock-toad-thief-circuit-16-18",
        world_boot_id="boot-1",
        policy_xp_deltas={
            "mahntor-rock-toad-thief-circuit-16-18": 0,
            "ambush-bardoosh-thief-kill-research-16": 535,
            "ambush-bardoosh-thief-hunt-16": 0,
        },
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "mahntor-rock-toad-thief-circuit-16-18"


def test_level_sixteen_thief_rotates_to_toads_after_bardoosh_hunt() -> None:
    policy = policy_for(
        16,
        "thief",
        last_policy_id="ambush-bardoosh-thief-hunt-16",
        world_boot_id="boot-1",
        policy_xp_deltas={
            "mahntor-rock-toad-thief-circuit-16-18": 478,
            "ambush-bardoosh-thief-kill-research-16": 535,
            "ambush-bardoosh-thief-hunt-16": 510,
        },
        research_results={
            "mirror-realm-watchman-probe-16-20": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "crystalmir-white-stag-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
            "shadow-keep-undead-soldier-probe-16-20": {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "mahntor-rock-toad-thief-circuit-16-18"


@pytest.mark.parametrize("character_class", ["mage", "thief", "warrior", "psionic"])
def test_levels_twenty_one_to_twenty_five_start_with_no_combat_gardener_probe(
    character_class: str,
) -> None:
    policy = policy_for(21, character_class)

    assert policy.policy_id == "mirror-realm-watchman-probe-21-25"
    assert policy.status == "research"
    assert policy.execution == "mirror-realm-watchman-research"
    assert policy.executable


def test_level_twenty_one_promotes_a_viable_watchman_probe_to_a_hunt() -> None:
    policy = policy_for(
        21,
        "warrior",
        last_policy_id="mirror-realm-watchman-probe-21-25",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-21-25": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.policy_id == "mirror-realm-watchman-hunt-21-25"
    assert policy.execution == "mirror-realm-watchman-hunt"


def test_level_twenty_one_falls_back_to_gardener_research_after_watchman_rejects() -> None:
    policy = policy_for(
        21,
        "warrior",
        last_policy_id="mirror-realm-watchman-probe-21-25",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-21-25": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.policy_id == "mirror-realm-gardener-probe-21-25"


def test_level_twenty_one_promotes_a_viable_gardener_probe_to_a_hunt() -> None:
    policy = policy_for(
        21,
        "warrior",
        last_policy_id="mirror-realm-gardener-probe-21-25",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-21-25": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "mirror-realm-gardener-probe-21-25": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.policy_id == "mirror-realm-gardener-hunt-21-25"
    assert policy.execution == "mirror-realm-gardener-hunt"
    assert policy.segment_kill_limit == 1


def test_level_twenty_one_waits_after_watchman_and_gardener_probes() -> None:
    policy = policy_for(
        21,
        "mage",
        last_policy_id="mirror-realm-gardener-probe-21-25",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-watchman-probe-21-25": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "mirror-realm-gardener-probe-21-25": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.status == "unavailable"
    assert not policy.executable
    assert "do not authorize combat" in policy.summary


@pytest.mark.parametrize("character_class", ["mage", "thief", "warrior", "psionic"])
def test_levels_twenty_six_to_thirty_start_with_no_combat_battle_master_probe(
    character_class: str,
) -> None:
    policy = policy_for(26, character_class)

    assert policy.policy_id == "mirror-realm-guardian-probe-26-30"
    assert policy.status == "research"
    assert policy.execution == "mirror-realm-guardian-research"
    assert policy.executable


def test_level_twenty_six_promotes_a_viable_guardian_probe_to_a_hunt() -> None:
    policy = policy_for(
        26,
        "warrior",
        last_policy_id="mirror-realm-guardian-probe-26-30",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-guardian-probe-26-30": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.policy_id == "mirror-realm-guardian-hunt-26-30"
    assert policy.execution == "mirror-realm-guardian-hunt"


def test_level_twenty_six_waits_after_guardian_and_battle_master_probes() -> None:
    policy = policy_for(
        26,
        "mage",
        last_policy_id="shire-battle-master-probe-26-30",
        world_boot_id="boot-1",
        research_results={
            "mirror-realm-guardian-probe-26-30": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "shire-battle-master-probe-26-30": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.status == "unavailable"
    assert not policy.executable
    assert "do not authorize combat" in policy.summary


@pytest.mark.parametrize("character_class", ["mage", "thief", "warrior", "psionic"])
def test_levels_thirty_one_to_thirty_five_start_with_no_combat_cancer_probe(
    character_class: str,
) -> None:
    policy = policy_for(31, character_class)

    assert policy.policy_id == "minotaur-gatekeeper-probe-31-35"
    assert policy.status == "research"
    assert policy.execution == "minotaur-gatekeeper-research"
    assert policy.executable


def test_level_thirty_one_promotes_a_viable_gatekeeper_probe_to_a_hunt() -> None:
    policy = policy_for(
        31,
        "warrior",
        last_policy_id="minotaur-gatekeeper-probe-31-35",
        world_boot_id="boot-1",
        research_results={
            "minotaur-gatekeeper-probe-31-35": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.policy_id == "minotaur-gatekeeper-hunt-31-35"
    assert policy.execution == "minotaur-gatekeeper-hunt"


def test_level_thirty_one_waits_after_gatekeeper_and_cancer_probes() -> None:
    policy = policy_for(
        31,
        "mage",
        last_policy_id="galaxy-cancer-probe-31-35",
        world_boot_id="boot-1",
        research_results={
            "minotaur-gatekeeper-probe-31-35": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "galaxy-cancer-probe-31-35": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.status == "unavailable"
    assert not policy.executable
    assert "do not authorize combat" in policy.summary


@pytest.mark.parametrize("character_class", ["mage", "thief", "warrior", "psionic"])
def test_levels_thirty_six_to_forty_start_with_no_combat_jerry_probe(
    character_class: str,
) -> None:
    policy = policy_for(36, character_class)

    assert policy.policy_id == "mirror-realm-jerry-garcia-probe-36-40"
    assert policy.status == "research"
    assert policy.execution == "mirror-realm-jerry-garcia-research"
    assert policy.executable


def test_level_thirty_six_waits_for_review_after_jerry_probe() -> None:
    policy = policy_for(
        36,
        "mage",
        policy_xp_deltas={"mirror-realm-jerry-garcia-probe-36-40": 0},
    )

    assert policy.status == "unavailable"
    assert not policy.executable
    assert "do not authorize combat" in policy.summary


def test_level_forty_one_starts_with_no_combat_pit_official_probe() -> None:
    policy = policy_for(41, "mage")

    assert policy.policy_id == "pit-official-probe-41-45"
    assert policy.status == "research"
    assert policy.execution == "pit-official-research"
    assert policy.executable


def test_level_forty_one_waits_for_review_after_pit_official_probe() -> None:
    policy = policy_for(
        41,
        "mage",
        policy_xp_deltas={"pit-official-probe-41-45": 0},
    )

    assert policy.status == "unavailable"
    assert not policy.executable
    assert "do not authorize combat" in policy.summary


def test_level_forty_six_starts_with_dwarven_home_chess_dwarf_probe() -> None:
    policy = policy_for(46, "warrior")

    assert policy.policy_id == "dwarven-home-chess-dwarf-probe-46-50"
    assert policy.status == "research"
    assert policy.execution == "dwarven-home-chess-dwarf-research"
    assert policy.executable


def test_level_forty_six_promotes_viable_chess_dwarf_to_one_hunt() -> None:
    policy = policy_for(
        46,
        "warrior",
        last_policy_id="dwarven-home-chess-dwarf-probe-46-50",
        world_boot_id="boot-1",
        research_results={
            "dwarven-home-chess-dwarf-probe-46-50": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.policy_id == "dwarven-home-chess-dwarf-hunt-46-50"
    assert policy.execution == "dwarven-home-chess-dwarf-hunt"
    assert policy.segment_kill_limit == 1


def test_level_forty_six_uses_storn_after_chess_dwarf_rejection() -> None:
    policy = policy_for(
        46,
        "warrior",
        last_policy_id="dwarven-home-chess-dwarf-probe-46-50",
        world_boot_id="boot-1",
        research_results={
            "dwarven-home-chess-dwarf-probe-46-50": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.policy_id == "mirror-realm-storn-probe-46-50"
    assert policy.execution == "mirror-realm-storn-research"


def test_level_forty_six_waits_after_both_registered_probes() -> None:
    policy = policy_for(
        46,
        "warrior",
        world_boot_id="boot-1",
        research_results={
            "dwarven-home-chess-dwarf-probe-46-50": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "mirror-realm-storn-probe-46-50": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.status == "unavailable"
    assert policy.minimum_level == 46
    assert policy.maximum_level == 50
    assert not policy.executable


def test_level_fifty_one_starts_with_darkwood_strange_mist_probe() -> None:
    policy = policy_for(51, "warrior")

    assert policy.policy_id == "darkwood-strange-mist-probe-51-55"
    assert policy.status == "research"
    assert policy.execution == "darkwood-strange-mist-research"
    assert policy.executable


def test_level_fifty_one_promotes_viable_strange_mist_to_one_hunt() -> None:
    policy = policy_for(
        51,
        "warrior",
        last_policy_id="darkwood-strange-mist-probe-51-55",
        world_boot_id="boot-1",
        research_results={
            "darkwood-strange-mist-probe-51-55": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.policy_id == "darkwood-strange-mist-hunt-51-55"
    assert policy.execution == "darkwood-strange-mist-hunt"
    assert policy.segment_kill_limit == 1


def test_level_fifty_one_uses_dwarven_home_gambler_after_mist_rejection() -> None:
    policy = policy_for(
        51,
        "warrior",
        last_policy_id="darkwood-strange-mist-probe-51-55",
        world_boot_id="boot-1",
        research_results={
            "darkwood-strange-mist-probe-51-55": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.policy_id == "dwarven-home-gambler-probe-51-55"
    assert policy.execution == "dwarven-home-gambler-research"


def test_level_fifty_one_waits_after_both_registered_probes() -> None:
    policy = policy_for(
        51,
        "warrior",
        world_boot_id="boot-1",
        research_results={
            "darkwood-strange-mist-probe-51-55": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
            "dwarven-home-gambler-probe-51-55": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            },
        },
    )

    assert policy.status == "unavailable"
    assert policy.minimum_level == 51
    assert policy.maximum_level == 55
    assert not policy.executable


def test_level_fifty_six_starts_with_dwarven_home_master_probe() -> None:
    policy = policy_for(56, "warrior")

    assert policy.policy_id == "dwarven-home-master-probe-56-60"
    assert policy.status == "research"
    assert policy.execution == "dwarven-home-master-research"
    assert policy.executable


def test_level_fifty_six_promotes_viable_master_to_one_hunt() -> None:
    policy = policy_for(
        56,
        "warrior",
        last_policy_id="dwarven-home-master-probe-56-60",
        world_boot_id="boot-1",
        research_results={
            "dwarven-home-master-probe-56-60": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.policy_id == "dwarven-home-master-hunt-56-60"
    assert policy.execution == "dwarven-home-master-hunt"
    assert policy.segment_kill_limit == 1


def test_level_fifty_six_waits_after_master_probe_rejection() -> None:
    policy = policy_for(
        56,
        "warrior",
        world_boot_id="boot-1",
        research_results={
            "dwarven-home-master-probe-56-60": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.status == "unavailable"
    assert policy.minimum_level == 56
    assert policy.maximum_level == 60
    assert not policy.executable


def test_level_sixty_one_starts_with_wounded_vampire_probe() -> None:
    policy = policy_for(61, "warrior")

    assert policy.policy_id == "vampire-hive-wounded-vampire-probe-61-65"
    assert policy.status == "research"
    assert policy.execution == "vampire-hive-wounded-vampire-research"
    assert policy.executable


def test_level_sixty_one_promotes_viable_wounded_vampire_to_one_hunt() -> None:
    policy = policy_for(
        61,
        "warrior",
        last_policy_id="vampire-hive-wounded-vampire-probe-61-65",
        world_boot_id="boot-1",
        research_results={
            "vampire-hive-wounded-vampire-probe-61-65": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.policy_id == "vampire-hive-wounded-vampire-hunt-61-65"
    assert policy.execution == "vampire-hive-wounded-vampire-hunt"
    assert policy.segment_kill_limit == 1


def test_level_sixty_one_waits_after_wounded_vampire_probe_rejection() -> None:
    policy = policy_for(
        61,
        "warrior",
        world_boot_id="boot-1",
        research_results={
            "vampire-hive-wounded-vampire-probe-61-65": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.status == "unavailable"
    assert policy.minimum_level == 61
    assert policy.maximum_level == 65
    assert not policy.executable


def test_level_sixty_six_starts_with_hulking_beast_probe() -> None:
    policy = policy_for(66, "warrior")

    assert policy.policy_id == "tabernacle-hulking-beast-probe-66-70"
    assert policy.status == "research"
    assert policy.execution == "tabernacle-hulking-beast-research"
    assert policy.executable


def test_level_sixty_six_promotes_viable_hulking_beast_to_one_hunt() -> None:
    policy = policy_for(
        66,
        "warrior",
        last_policy_id="tabernacle-hulking-beast-probe-66-70",
        world_boot_id="boot-1",
        research_results={
            "tabernacle-hulking-beast-probe-66-70": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.policy_id == "tabernacle-hulking-beast-hunt-66-70"
    assert policy.execution == "tabernacle-hulking-beast-hunt"
    assert policy.segment_kill_limit == 1


def test_level_sixty_six_waits_after_hulking_beast_probe_rejection() -> None:
    policy = policy_for(
        66,
        "warrior",
        world_boot_id="boot-1",
        research_results={
            "tabernacle-hulking-beast-probe-66-70": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.status == "unavailable"
    assert policy.minimum_level == 66
    assert policy.maximum_level == 70
    assert not policy.executable


def test_level_seventy_one_starts_with_rastafarians_probe() -> None:
    policy = policy_for(71, "warrior")

    assert policy.policy_id == "pirates-seas-rastafarians-probe-71-75"
    assert policy.status == "research"
    assert policy.execution == "pirates-seas-rastafarians-research"
    assert policy.executable


def test_level_seventy_one_promotes_viable_rastafarians_to_one_hunt() -> None:
    policy = policy_for(
        71,
        "warrior",
        last_policy_id="pirates-seas-rastafarians-probe-71-75",
        world_boot_id="boot-1",
        research_results={
            "pirates-seas-rastafarians-probe-71-75": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.policy_id == "pirates-seas-rastafarians-hunt-71-75"
    assert policy.execution == "pirates-seas-rastafarians-hunt"
    assert policy.segment_kill_limit == 1


def test_level_seventy_one_waits_after_rastafarians_probe_rejection() -> None:
    policy = policy_for(
        71,
        "warrior",
        world_boot_id="boot-1",
        research_results={
            "pirates-seas-rastafarians-probe-71-75": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.status == "unavailable"
    assert policy.minimum_level == 71
    assert policy.maximum_level == 75
    assert not policy.executable


def test_level_seventy_six_starts_with_crypt_thing_probe() -> None:
    policy = policy_for(76, "warrior")

    assert policy.policy_id == "ghost-town-crypt-thing-probe-76"
    assert policy.status == "research"
    assert policy.execution == "ghost-town-crypt-thing-research"
    assert policy.executable


def test_level_seventy_six_promotes_viable_crypt_thing_to_one_hunt() -> None:
    policy = policy_for(
        76,
        "warrior",
        last_policy_id="ghost-town-crypt-thing-probe-76",
        world_boot_id="boot-1",
        research_results={
            "ghost-town-crypt-thing-probe-76": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.policy_id == "ghost-town-crypt-thing-hunt-76"
    assert policy.execution == "ghost-town-crypt-thing-hunt"
    assert policy.segment_kill_limit == 1


def test_level_seventy_six_waits_after_crypt_thing_probe_rejection() -> None:
    policy = policy_for(
        76,
        "warrior",
        world_boot_id="boot-1",
        research_results={
            "ghost-town-crypt-thing-probe-76": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.status == "unavailable"
    assert policy.minimum_level == 76
    assert policy.maximum_level == 76
    assert not policy.executable


def test_level_seventy_seven_starts_with_retriever_probe() -> None:
    policy = policy_for(77, "warrior")

    assert policy.policy_id == "ghost-town-retriever-probe-77-80"
    assert policy.status == "research"
    assert policy.execution == "ghost-town-retriever-research"
    assert policy.executable


def test_level_seventy_seven_promotes_viable_retriever_to_one_hunt() -> None:
    policy = policy_for(
        77,
        "warrior",
        last_policy_id="ghost-town-retriever-probe-77-80",
        world_boot_id="boot-1",
        research_results={
            "ghost-town-retriever-probe-77-80": {
                "observed": True,
                "viable": True,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.policy_id == "ghost-town-retriever-hunt-77-80"
    assert policy.execution == "ghost-town-retriever-hunt"
    assert policy.segment_kill_limit == 1


def test_level_seventy_seven_waits_after_retriever_probe_rejection() -> None:
    policy = policy_for(
        77,
        "warrior",
        world_boot_id="boot-1",
        research_results={
            "ghost-town-retriever-probe-77-80": {
                "observed": True,
                "viable": False,
                "boot_id": "boot-1",
            }
        },
    )

    assert policy.status == "unavailable"
    assert policy.minimum_level == 77
    assert policy.maximum_level == 80
    assert not policy.executable


def test_level_ten_thief_retires_empty_verified_combined_rotation() -> None:
    policy = policy_for(
        10,
        "thief",
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "fleshmonger-thief-guard-research-10-11": 423,
            "fleshmonger-thief-guard-10-11": 0,
            "fleshmonger-mufti-probe-10-11": 0,
            "fleshmonger-cook-probe-v2-10-11": 0,
            "fleshmonger-cook-10-11": 0,
            "ambush-archer-probe-10-11": 0,
            "ambush-archer-kill-research-10-11": 3,
            "gnome-guard-hut-probe-10-11": 0,
            "fleshmonger-thief-rotation-research-v8-10-11": 472,
            "fleshmonger-thief-rotation-10-11": 0,
        },
    )

    assert policy.status == "unavailable"
    assert not policy.executable


def test_level_ten_warrior_extends_completed_guard_research_to_two_kills() -> None:
    policy = policy_for(
        10,
        "warrior",
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "fleshmonger-guard-kill-research-10-11": 430,
        },
    )

    assert policy.policy_id == "fleshmonger-two-guard-research-v2-10-11"
    assert policy.status == "research"
    assert policy.execution == "fleshmonger-guard-circuit-research"
    assert policy.segment_kill_limit == 2


@pytest.mark.parametrize("level", [10, 11])
def test_level_ten_and_eleven_warrior_promotes_completed_two_guard_research(
    level: int,
) -> None:
    policy = policy_for(
        level,
        "warrior",
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "fleshmonger-guard-kill-research-10-11": 703,
            "fleshmonger-two-guard-research-v2-10-11": 1200,
        },
    )

    assert policy.policy_id == "fleshmonger-guard-circuit-10-11"
    assert policy.status == "verified"
    assert policy.execution == "fleshmonger-guard-circuit"
    assert policy.segment_kill_limit == 2
    assert "Live run 1414" in " ".join(policy.evidence)


def test_level_ten_warrior_delegates_empty_guard_loop_to_reset_controller() -> None:
    policy = policy_for(
        10,
        "warrior",
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "fleshmonger-guard-kill-research-10-11": 703,
            "fleshmonger-two-guard-research-v2-10-11": 1200,
            "fleshmonger-guard-circuit-10-11": 0,
        },
    )

    assert policy.policy_id == "fleshmonger-guard-circuit-10-11"
    assert policy.status == "verified"
    assert policy.executable


def test_level_eleven_mage_collects_same_bounded_source_probe() -> None:
    policy = policy_for(11, "mage")

    assert policy.policy_id == "fleshmonger-guard-probe-10-12"
    assert policy.minimum_level == 11
    assert policy.status == "research"
    assert policy.executable


def test_level_eleven_mage_continues_to_protected_moria_after_source_probe() -> None:
    policy = policy_for(
        11,
        "mage",
        policy_xp_deltas={"fleshmonger-guard-probe-10-12": 0},
    )

    assert policy.policy_id == "moria-sanctuary-11-12"
    assert policy.execution == "moria-sanctuary-hunt"
    assert policy.status == "verified"
    assert policy.practice_skill == "magic missile"


def test_level_eleven_mage_does_not_repeat_zero_xp_moria_hunt() -> None:
    policy = policy_for(
        11,
        "mage",
        policy_xp_deltas={
            "fleshmonger-guard-probe-10-12": 0,
            "moria-sanctuary-11-12": 0,
        },
    )

    assert policy.status == "unavailable"
    assert policy.minimum_level == 11
    assert policy.maximum_level == 12
    assert not policy.executable


def test_psionicist_alias_uses_the_level_ten_shared_scout() -> None:
    policy = policy_for(10, "psionicist")

    assert policy.policy_id == "fleshmonger-guard-probe-10-12"
    assert policy.status == "research"
    assert policy.practice_skill == "mind thrust"


def test_unknown_class_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown class"):
        policy_for(2, "illusionist")
