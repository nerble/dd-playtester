import asyncio
import json
from dataclasses import replace
from pathlib import Path

from dd4tester.campaign import (
    CampaignRunner,
    _advance_daycare_ring_cooldown,
    _advance_piercing_weapon_upgrade_cooldown,
    _advance_war_dog_collar_cooldown,
    _campaign_counterbalance_preparation_required,
    _campaign_segment_end_state,
    _campaign_flight_purchase_failed,
    _campaign_policy_xp_deltas,
    _campaign_liquidation_signature,
    _campaign_practice_types_spent,
    _campaign_rejected_practice_skills,
    _campaign_vault_stow_items,
    _has_campaign_sellable_loot,
    _needs_piercing_weapon_upgrade,
    _maintenance_failure_state,
    _newer_progress_state,
    _refresh_policy_revision,
    _run_has_unrecovered_weapon_loss,
    _run_policy_segment,
    _stalled_count,
    load_campaign_spec,
    run_campaign_file,
)
from dd4tester.equipment import GearCatalog
from dd4tester.hunt_candidates import ObjectSource
from dd4tester.progression import ProgressionPolicy, policy_for
from dd4tester.runner import RunResult
from dd4tester.starter import ambush_exterior_hunt_stops
from dd4tester.storage import RunStorage


def test_live_state_merge_preserves_campaign_checkpoint_metadata() -> None:
    merged = _newer_progress_state(
        {
            "level": 8,
            "xp": 29_613,
            "campaign_stalled_segments": 1,
            "room_name": "Mage's Laboratory",
        },
        {
            "level": 8,
            "xp": 29_613,
            "room_name": "The Healer",
        },
    )

    assert merged["campaign_stalled_segments"] == 1
    assert merged["room_name"] == "The Healer"


def test_live_state_merge_accepts_same_level_death_xp_loss() -> None:
    merged = _newer_progress_state(
        {
            "level": 8,
            "xp": 27_215,
            "campaign_stalled_segments": 1,
            "room_vnum": "3054",
        },
        {
            "level": 8,
            "xp": 26_153,
            "hp": 120,
            "dead": True,
            "area": "Midgaard",
            "room_vnum": "3054",
        },
    )

    assert merged["xp"] == 26_153
    assert merged["dead"] is False
    assert merged["campaign_stalled_segments"] == 1


def test_non_shop_segment_preserves_failed_flight_purchase() -> None:
    merged = _campaign_segment_end_state(
        {"magic_shop_purchase_failed": True},
        {"level": 9, "magic_shop_purchase_failed": False},
        execution="field-hunt",
    )

    assert merged["magic_shop_purchase_failed"] is True


def test_flight_purchase_segment_can_clear_its_failure_state() -> None:
    merged = _campaign_segment_end_state(
        {"magic_shop_purchase_failed": True},
        {"level": 9, "magic_shop_purchase_failed": False},
        execution="buy-flight-potion",
    )

    assert merged["magic_shop_purchase_failed"] is False


def test_required_loot_segment_preserves_same_level_outfit_attempt() -> None:
    merged = _campaign_segment_end_state(
        {"campaign_outfit_attempted_level": 8},
        {"level": 8},
        execution="recover-basic-body",
    )

    assert merged["campaign_outfit_attempted_level"] == 8


def test_failed_daycare_ring_errand_is_not_retried_at_same_level() -> None:
    failed = _maintenance_failure_state(
        {"level": 10, "campaign_empty_equipment_categories": ["finger"]},
        execution="recover-daycare-ring",
        boot_id="Mon Jul 27 09:12:49 2026",
    )

    assert failed["campaign_daycare_ring_attempted_level"] == 10
    assert (
        failed["campaign_daycare_ring_attempted_boot_id"]
        == "Mon Jul 27 09:12:49 2026"
    )
    assert failed["campaign_daycare_ring_cooldown"] == 3


def test_failed_war_dog_collar_errand_is_not_retried_at_same_level() -> None:
    failed = _maintenance_failure_state(
        {"level": 10, "campaign_empty_equipment_categories": ["neck"]},
        execution="recover-war-dog-collar",
        boot_id="Mon Jul 27 09:12:49 2026",
    )

    assert failed["campaign_war_dog_collar_attempted_level"] == 10
    assert (
        failed["campaign_war_dog_collar_attempted_boot_id"]
        == "Mon Jul 27 09:12:49 2026"
    )
    assert failed["campaign_war_dog_collar_cooldown"] == 3


def test_failed_combat_segment_does_not_gain_a_maintenance_marker() -> None:
    state = {"level": 10}

    assert _maintenance_failure_state(
        state,
        execution="fleshmonger-guard-hunt",
    ) is state


def test_campaign_reconstructs_latest_flight_purchase_result(tmp_path) -> None:
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        campaign_id = storage.create_campaign(
            name="flight",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=10,
        )
        first = storage.start_campaign_segment(
            campaign_id,
            phase="buy-flight-potion",
            start_state={"level": 9},
        )
        storage.finish_campaign_segment(
            first,
            status="success",
            run_id=None,
            end_state={"level": 9, "magic_shop_purchase_failed": True},
            command_count=1,
            duration_seconds=1.0,
        )
        field = storage.start_campaign_segment(
            campaign_id,
            phase="field-hunt",
            start_state={"level": 9},
        )
        storage.finish_campaign_segment(
            field,
            status="success",
            run_id=None,
            end_state={"level": 9, "magic_shop_purchase_failed": False},
            command_count=1,
            duration_seconds=1.0,
        )

        assert _campaign_flight_purchase_failed(storage, campaign_id) is True


def test_campaign_retries_flight_purchase_after_money_increases(tmp_path) -> None:
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        campaign_id = storage.create_campaign(
            name="flight",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=10,
        )
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="buy-flight-potion",
            start_state={"level": 9},
        )
        storage.finish_campaign_segment(
            segment_id,
            status="success",
            run_id=None,
            end_state={
                "level": 9,
                "currencies": {"silver": 10, "copper": 18},
                "magic_shop_purchase_failed": True,
                "world_boot_id": "boot-a",
            },
            command_count=1,
            duration_seconds=1.0,
        )

        assert (
            _campaign_flight_purchase_failed(
                storage,
                campaign_id,
                current_state={
                    "currencies": {"silver": 10, "copper": 18},
                    "world_boot_id": "boot-a",
                },
            )
            is True
        )
        assert (
            _campaign_flight_purchase_failed(
                storage,
                campaign_id,
                current_state={
                    "currencies": {"silver": 16, "copper": 19},
                    "world_boot_id": "boot-a",
                },
            )
            is False
        )


def test_campaign_retries_flight_purchase_after_reboot(tmp_path) -> None:
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        campaign_id = storage.create_campaign(
            name="flight",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=10,
        )
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="buy-flight-potion",
            start_state={"level": 9},
        )
        storage.finish_campaign_segment(
            segment_id,
            status="success",
            run_id=None,
            end_state={
                "level": 9,
                "currencies": {"silver": 10, "copper": 18},
                "magic_shop_purchase_failed": True,
                "world_boot_id": "boot-a",
            },
            command_count=1,
            duration_seconds=1.0,
        )

        assert (
            _campaign_flight_purchase_failed(
                storage,
                campaign_id,
                current_state={
                    "currencies": {"silver": 10, "copper": 18},
                    "world_boot_id": "boot-b",
                },
            )
            is False
        )


def test_piercing_upgrade_signal_compares_known_source_weapon_damage() -> None:
    dagger = ObjectSource(
        3020,
        "dagger",
        "a dagger",
        5,
        (0, 2, 4, 11),
        10,
    )
    claws = ObjectSource(
        18000,
        "claws bears",
        "a pair of bears claws",
        5,
        (0, 6, 12, 11),
        0,
    )
    ambiguous_high_level_dagger = ObjectSource(
        999,
        "dagger",
        "a dagger",
        5,
        (0, 20, 20, 11),
        1000,
        level=50,
    )
    catalog = GearCatalog(
        {
            dagger.vnum: dagger,
            claws.vnum: claws,
            ambiguous_high_level_dagger.vnum: ambiguous_high_level_dagger,
        }
    )

    assert _needs_piercing_weapon_upgrade(
        {"campaign_worn_equipment": ["a dagger"]},
        gear_catalog=catalog,
        character_class="thief",
        subclass="ninja",
    )
    assert not _needs_piercing_weapon_upgrade(
        {
            "campaign_worn_equipment": ["a dagger"],
            "inventory": [[{"quan": "1", "short_desc": "a pair of bears claws"}]],
        },
        gear_catalog=catalog,
        character_class="thief",
        subclass="ninja",
    )


def test_campaign_suppresses_piercing_upgrade_after_same_boot_attempt(
    tmp_path,
) -> None:
    config_path, _ = _write_campaign_files(tmp_path)
    mage_spec = load_campaign_spec(config_path)
    thief_character = replace(
        mage_spec.character,
        character_class="thief",
        subclass="ninja",
    )
    runner = CampaignRunner(
        replace(mage_spec, character=thief_character),
        config_path,
    )
    dagger = ObjectSource(
        3020,
        "dagger",
        "a dagger",
        5,
        (0, 2, 4, 11),
        10,
    )
    claws = ObjectSource(
        18000,
        "claws bears",
        "a pair of bears claws",
        5,
        (0, 6, 12, 11),
        0,
    )
    runner._gear_catalog = GearCatalog(
        {dagger.vnum: dagger, claws.vnum: claws}
    )
    runner._boot_id = 77
    state = {
        "level": 11,
        "campaign_has_weapon": True,
        "campaign_worn_equipment": ["a dagger"],
        "campaign_empty_equipment_categories": [],
        "inventory": [[{"quan": "1", "short_desc": "a big pot pie"}]],
        "affects": [[{"name": "fly"}]],
    }

    assert runner._policy_for_state(state).execution == "upgrade-piercing-weapon"
    state["campaign_piercing_weapon_upgrade_attempted_boot_id"] = 77
    state["campaign_piercing_weapon_upgrade_cooldown"] = 3
    assert runner._policy_for_state(state).policy_id == (
        "fleshmonger-thief-rotation-11-12"
    )
    state["campaign_piercing_weapon_upgrade_cooldown"] = 0
    assert runner._policy_for_state(state).execution == "upgrade-piercing-weapon"


def test_piercing_upgrade_retries_after_three_productive_field_segments() -> None:
    state = {
        "campaign_piercing_weapon_upgrade_attempted_boot_id": 77,
        "campaign_piercing_weapon_upgrade_cooldown": 3,
    }

    for _ in range(3):
        state = _advance_piercing_weapon_upgrade_cooldown(
            state,
            execution="fleshmonger-thief-rotation-research",
            xp_delta=50,
        )

    assert state["campaign_piercing_weapon_upgrade_cooldown"] == 0
    unchanged = _advance_piercing_weapon_upgrade_cooldown(
        state,
        execution="sell-loot",
        xp_delta=500,
    )
    assert unchanged is state


def test_policy_revision_resets_stale_campaign_stall_count_once() -> None:
    migrated = _refresh_policy_revision(
        {
            "level": 7,
            "campaign_policy_revision": 1,
            "campaign_stalled_segments": 10,
            "campaign_piercing_weapon_upgrade_attempted_boot_id": "boot-1",
        }
    )

    assert migrated["campaign_stalled_segments"] == 0
    assert migrated["campaign_policy_revision"] == 37
    assert "campaign_piercing_weapon_upgrade_attempted_boot_id" not in migrated
    assert "campaign_piercing_weapon_upgrade_cooldown" not in migrated


def test_policy_revision_retries_body_recovery_after_named_mobile_parser_fix() -> None:
    migrated = _refresh_policy_revision(
        {
            "level": 8,
            "campaign_policy_revision": 19,
            "campaign_body_gear_attempted_level": 8,
        }
    )

    assert "campaign_body_gear_attempted_level" not in migrated
    assert _refresh_policy_revision(migrated) is migrated


def test_stalled_count_ignores_checkpoint_from_previous_policy_revision() -> None:
    checkpoint = {
        "state_json": json.dumps(
            {
                "campaign_policy_revision": 2,
                "campaign_stalled_segments": 10,
            }
        )
    }

    stalled = _stalled_count(
        {
            "level": 7,
            "xp": 22_913,
            "campaign_policy_revision": 7,
            "campaign_stalled_segments": 0,
        },
        {"level": 7, "xp": 22_913},
        checkpoint,
    )

    assert stalled == 1


def test_campaign_policy_xp_deltas_reconstruct_latest_segment_result(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="outcomes",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=10,
        )
        first = storage.start_campaign_segment(
            campaign_id,
            phase="gnome-hermit-7-8",
            start_state={"level": 7, "xp": 24_100},
        )
        storage.finish_campaign_segment(
            first,
            status="success",
            run_id=None,
            end_state={"level": 7, "xp": 24_220},
            command_count=1,
            duration_seconds=1.0,
        )
        second = storage.start_campaign_segment(
            campaign_id,
            phase="gnome-hermit-7-8",
            start_state={"level": 7, "xp": 24_220},
        )
        storage.finish_campaign_segment(
            second,
            status="success",
            run_id=None,
            end_state={"level": 7, "xp": 24_220},
            command_count=1,
            duration_seconds=1.0,
        )
        level_gain = storage.start_campaign_segment(
            campaign_id,
            phase="foundry-circuit-7-8",
            start_state={"level": 7, "xp": 24_700},
        )
        storage.finish_campaign_segment(
            level_gain,
            status="success",
            run_id=None,
            end_state={"level": 8, "xp": 25_000},
            command_count=1,
            duration_seconds=1.0,
        )

        results = _campaign_policy_xp_deltas(storage.list_campaign_segments(campaign_id))

    assert results == {"gnome-hermit-7-8": 0, "foundry-circuit-7-8": 1}


def test_campaign_policy_xp_deltas_discounts_positive_xp_without_a_kill(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="outcomes",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=10,
        )
        run_id = storage.create_run(
            scenario_name="field-hunt",
            scenario_path=tmp_path / "character.yaml",
        )
        storage.record_event(
            run_id,
            kind="state",
            payload={"state": "completed", "completed_kills": []},
        )
        storage.finish_run(run_id, status="success")
        segment = storage.start_campaign_segment(
            campaign_id,
            phase="fleshmonger-thief-rotation-11-12",
            start_state={"level": 11, "xp": 56_663},
        )
        storage.finish_campaign_segment(
            segment,
            status="success",
            run_id=run_id,
            end_state={"level": 11, "xp": 56_742},
            command_count=1,
            duration_seconds=1.0,
        )

        results = _campaign_policy_xp_deltas(
            storage.list_campaign_segments(campaign_id), storage=storage
        )

    assert results == {"fleshmonger-thief-rotation-11-12": 0}


def test_campaign_policy_xp_deltas_excludes_incidental_route_combat(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="outcomes",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=10,
        )
        segment = storage.start_campaign_segment(
            campaign_id,
            phase="forest-bear-claws-upgrade-10-14",
            start_state={"level": 12, "xp": 58_961},
        )
        storage.finish_campaign_segment(
            segment,
            status="success",
            run_id=None,
            end_state={
                "level": 12,
                "xp": 59_021,
                "campaign_completed_kills": [
                    {"mob_name": "the goblin lieutenant", "xp_gained": 60}
                ],
                "campaign_objective_kills": [],
            },
            command_count=1,
            duration_seconds=1.0,
        )

        results = _campaign_policy_xp_deltas(storage.list_campaign_segments(campaign_id))

    assert results == {"forest-bear-claws-upgrade-10-14": 0}


def test_recorded_weapon_loss_requires_a_later_wield_to_clear(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        run_id = storage.create_run(
            scenario_name="weapon-loss",
            scenario_path=tmp_path / "profile.yaml",
        )
        storage.record_event(
            run_id,
            kind="response",
            payload={"text": "Your weapon slips from your hand."},
        )

        assert _run_has_unrecovered_weapon_loss(storage, run_id) is True

        storage.record_event(
            run_id,
            kind="response",
            payload={"text": "You wield a spiked metal rod."},
        )

        assert _run_has_unrecovered_weapon_loss(storage, run_id) is False


def test_equipment_audit_without_wield_slot_records_weapon_loss(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        run_id = storage.create_run(
            scenario_name="false-rearm",
            scenario_path=tmp_path / "profile.yaml",
        )
        storage.record_event(
            run_id,
            kind="command",
            payload={"command": "equipment"},
        )
        storage.record_event(
            run_id,
            kind="response",
            payload={"text": "<worn on head> a steel barrel-helm\n[held] a diploma"},
        )

        assert _run_has_unrecovered_weapon_loss(storage, run_id) is True


def test_equipment_audit_ignores_stale_response_before_wield_slot(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        run_id = storage.create_run(
            scenario_name="delayed-equipment",
            scenario_path=tmp_path / "profile.yaml",
        )
        storage.record_event(
            run_id,
            kind="command",
            payload={"command": "equipment"},
        )
        storage.record_event(
            run_id,
            kind="response",
            payload={"text": "Ok.\n<157/157 hits 138/138 mana 210/210 move [Midgaard]>"},
        )
        storage.record_event(
            run_id,
            kind="response",
            payload={"text": "[weapon] a sharp steel broadsword"},
        )

        assert _run_has_unrecovered_weapon_loss(storage, run_id) is False


def test_serialized_coloured_inventory_preserves_duplicate_quantity() -> None:
    state = {
        "inventory": (
            '[[{"quan":"3","short_desc":"\u001b[32ma war dog collar\u001b[0m"}]]'
        ),
        "stats": {"carry_wt": 129, "maxcarry_wt": 140},
    }

    assert _has_campaign_sellable_loot(state) is True


def test_campaign_source_catalog_recognizes_unfamiliar_sellable_loot() -> None:
    piping = ObjectSource(
        9010,
        "piping metal",
        "a length of metal piping",
        5,
        (0, 1, 4, 6),
        8,
        wear_flags=1 | (1 << 13),
    )
    state = {
        "inventory": (
            '[[{"quan":"2","short_desc":"a length of metal piping"},'
            '{"quan":"2","short_desc":"a big pot pie"}]]'
        ),
        "stats": {"carry_wt": 112, "maxcarry_wt": 115},
    }

    assert _has_campaign_sellable_loot(
        state,
        gear_catalog=GearCatalog({piping.vnum: piping}),
    ) is True


def test_campaign_vaults_plain_and_protected_spare_armour_when_capacity_is_low() -> None:
    buckler = ObjectSource(
        4100,
        "metal buckler",
        "a metal buckler",
        9,
        (2, 0, 0, 0),
        20,
        wear_flags=1 | (1 << 9),
        weight=3,
    )
    circlet = ObjectSource(
        4101,
        "silver circlet",
        "a silver circlet",
        9,
        (1, 0, 0, 0),
        30,
        wear_flags=1 | (1 << 4),
        affects=((3, 1),),
        weight=3,
    )
    pie = ObjectSource(
        4102,
        "big pot pie",
        "a big pot pie",
        19,
        (5, 0, 0, 0),
        2,
    )
    state = {
        "inventory": [[
            {"short_desc": "a metal buckler"},
            {"short_desc": "a silver circlet"},
            {"short_desc": "a big pot pie"},
        ]],
        "stats": {"carry_wt": 110, "maxcarry_wt": 115},
    }

    assert _campaign_vault_stow_items(
        state,
        gear_catalog=GearCatalog(
            {
                buckler.vnum: buckler,
                circlet.vnum: circlet,
                pie.vnum: pie,
            }
        ),
    ) == ("buckler", "circlet")

    state["stats"]["carry_wt"] = 100
    assert _campaign_vault_stow_items(
        state,
        gear_catalog=GearCatalog({buckler.vnum: buckler}),
    ) == ()


def test_campaign_does_not_vault_equipped_item_reported_in_inventory() -> None:
    diploma = ObjectSource(
        3715,
        "school diploma",
        "a Mud School diploma",
        8,
        (0, 0, 0, 0),
        0,
        wear_flags=1 << 14,
        affects=((5, 1),),
    )
    state = {
        "inventory": [[{"short_desc": "a Mud School diploma"}]],
        "stats": {"carry_wt": 131, "maxcarry_wt": 140},
        "campaign_worn_equipment": ["a Mud School diploma"],
    }

    assert _campaign_vault_stow_items(
        state,
        gear_catalog=GearCatalog({diploma.vnum: diploma}),
    ) == ()


def test_campaign_skips_a_vault_detour_that_cannot_restore_capacity() -> None:
    tophat = ObjectSource(
        4421,
        "tophat hat",
        "a tophat",
        9,
        (0, 0, 0, 0),
        0,
        wear_flags=1 | (1 << 4),
        affects=((12, 10), (17, 4)),
        weight=1,
    )
    state = {
        "inventory": [[{"short_desc": "a tophat"}]],
        "stats": {"carry_wt": 113, "maxcarry_wt": 115},
    }

    assert _campaign_vault_stow_items(
        state,
        gear_catalog=GearCatalog({tophat.vnum: tophat}),
    ) == ()


def test_campaign_temporarily_vaults_oversized_sack_when_it_blocks_capacity() -> None:
    sack = ObjectSource(
        4529,
        "large sack",
        "a large sack",
        15,
        (100, 1, 0, 0),
        0,
        weight=50,
    )
    state = {
        "inventory": [[{"short_desc": "a large sack"}]],
        "stats": {"carry_wt": 138, "maxcarry_wt": 115},
    }

    assert _campaign_vault_stow_items(
        state,
        gear_catalog=GearCatalog({sack.vnum: sack}),
    ) == ("sack",)


def test_campaign_liquidates_ambiguous_spare_spear_under_weight_pressure() -> None:
    ordinary = ObjectSource(
        4520,
        "spear bloody",
        "a wooden spear",
        5,
        (0, 6, 6, 0),
        100,
        wear_flags=1 << 13,
    )
    lance = ObjectSource(
        4521,
        "spear wooden",
        "a wooden spear",
        5,
        (0, 2, 2, 0),
        55,
        wear_flags=1 << 13,
        extra_flags=1 << 27,
    )
    state = {
        "inventory": [[
            {"short_desc": "a wooden spear"},
            {"short_desc": "a big pot pie"},
            {"short_desc": "a buffalo water skin"},
        ]],
        "stats": {"carry_wt": 90, "maxcarry_wt": 90},
        "campaign_liquidation_baseline": ["wooden spear"],
    }

    assert _has_campaign_sellable_loot(
        state,
        gear_catalog=GearCatalog(
            {
                ordinary.vnum: ordinary,
                lance.vnum: lance,
            }
        ),
    ) is True


def test_campaign_vaults_ambiguous_weapon_when_protected_match_blocks_sale() -> None:
    protected = ObjectSource(
        966,
        "spear",
        "a wooden spear",
        5,
        (0, 0, 0, 6),
        5,
        wear_flags=1 << 13,
        affects=((19, 50), (18, 50)),
        weight=10,
    )
    ordinary = ObjectSource(
        4521,
        "spear wooden",
        "a wooden spear",
        5,
        (0, 0, 0, 2),
        0,
        wear_flags=1 << 13,
        weight=10,
    )
    state = {
        "inventory": [[
            {"short_desc": "a wooden spear"},
            {"short_desc": "a big pot pie"},
            {"short_desc": "a buffalo water skin"},
        ]],
        "stats": {"carry_wt": 90, "maxcarry_wt": 90},
    }
    catalog = GearCatalog(
        {
            protected.vnum: protected,
            ordinary.vnum: ordinary,
        }
    )

    assert _has_campaign_sellable_loot(state, gear_catalog=catalog) is False
    assert _campaign_vault_stow_items(
        state,
        gear_catalog=catalog,
    ) == ("spear",)


def test_campaign_ignores_wearable_key_without_a_safe_buyer() -> None:
    key = ObjectSource(
        4405,
        "key shimmering",
        "a shimmering key",
        18,
        (4423, 0, 0, 0),
        1,
        wear_flags=1 | (1 << 14),
    )
    state = {
        "inventory": [[
            {"short_desc": "a shimmering key"},
            {"short_desc": "a big pot pie"},
        ]],
    }

    assert _has_campaign_sellable_loot(
        state,
        gear_catalog=GearCatalog({key.vnum: key}),
    ) is False


def test_liquidation_baseline_suppresses_retained_gear_until_loot_changes() -> None:
    state = {
        "inventory": [[
            {"short_desc": "a metal shield"},
            {"short_desc": "a big pot pie"},
        ]],
    }
    state["campaign_liquidation_baseline"] = list(
        _campaign_liquidation_signature(state)
    )

    assert _has_campaign_sellable_loot(state) is False

    state["inventory"][0].append({"short_desc": "hard leather boots"})

    assert _has_campaign_sellable_loot(state) is True


def test_liquidation_signature_counts_only_redundant_protected_copies() -> None:
    tophat = ObjectSource(
        4421,
        "tophat hat",
        "a tophat",
        9,
        (0, 0, 0, 0),
        0,
        wear_flags=1 | (1 << 4),
        affects=((12, 10), (17, 4)),
    )
    catalog = GearCatalog({tophat.vnum: tophat})
    state = {
        "inventory": [[
            {"short_desc": "a tophat", "quan": "4"},
            {"short_desc": "a big pot pie", "quan": "6"},
        ]],
        "campaign_liquidation_baseline": [],
    }

    assert _campaign_liquidation_signature(
        state,
        gear_catalog=catalog,
    ) == ("tophat", "tophat", "tophat")
    assert _has_campaign_sellable_loot(state, gear_catalog=catalog) is True

    state["inventory"][0][0]["quan"] = "1"
    assert _campaign_liquidation_signature(state, gear_catalog=catalog) == ()
    assert _has_campaign_sellable_loot(state, gear_catalog=catalog) is False


def test_weight_pressure_does_not_reaudit_gear_for_an_empty_legal_slot() -> None:
    pouch = ObjectSource(
        3720,
        "small leather pouch",
        "a small leather pouch",
        9,
        (0, 0, 0, 0),
        0,
        wear_flags=1 << 16,
    )
    state = {
        "inventory": [[{"short_desc": "a small leather pouch"}]],
        "stats": {"carry_wt": 130, "maxcarry_wt": 140},
        "campaign_empty_equipment_categories": ["pouch"],
        "campaign_liquidation_baseline": ["small leather pouch"],
    }

    assert _has_campaign_sellable_loot(
        state,
        gear_catalog=GearCatalog({pouch.vnum: pouch}),
    ) is False


def test_liquidation_baseline_ignores_consumable_quantity_changes() -> None:
    state = {
        "inventory": [[
            {"short_desc": "a metal shield"},
            {"short_desc": "a big pot pie", "quan": "1"},
        ]],
        "campaign_liquidation_baseline": ["metal shield"],
    }

    state["inventory"][0][1]["quan"] = "6"

    assert _has_campaign_sellable_loot(state) is False


def test_legacy_completed_liquidation_checkpoint_gains_a_baseline(tmp_path) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name=spec.name,
            config_path=config_path.resolve(),
            character_profile_path=spec.character_profile,
            target_level=spec.target_level,
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=None,
            run_id=None,
            phase="liquidate-loot",
            reason="segment_complete",
            state={
                "level": 7,
                "xp": 21_058,
                "inventory": [[
                    {"short_desc": "a metal shield"},
                    {"short_desc": "a big pot pie"},
                ]],
            },
        )

        runner = CampaignRunner(spec, config_path)
        resumed_id, state = runner._open_campaign(storage)

    assert resumed_id == campaign_id
    assert state["campaign_liquidation_baseline"] == ["metal shield"]
    assert runner._policy_for_state(state).policy_id != "liquidate-loot"


def test_successful_liquidation_checkpoints_retained_gear_baseline(tmp_path) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name=spec.name,
            config_path=config_path.resolve(),
            character_profile_path=spec.character_profile,
            target_level=spec.target_level,
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=None,
            run_id=None,
            phase="foundry-circuit-7-8",
            reason="segment_complete",
            state={
                "level": 7,
                "xp": 21_058,
                "inventory": [[
                    {"short_desc": "hard leather boots"},
                    {"short_desc": "a big pot pie"},
                ]],
            },
        )

    async def liquidate_segment(spec, profile_path: Path) -> RunResult:
        return _record_segment_run(
            spec.database,
            profile_path,
            {
                "level": 7,
                "xp": 21_058,
                "inventory": [[
                    {"short_desc": "a metal shield"},
                    {"short_desc": "a big pot pie"},
                ]],
            },
        )

    result = asyncio.run(
        CampaignRunner(
            spec,
            config_path,
            segment_runner=liquidate_segment,
        ).run()
    )

    with RunStorage(database) as storage:
        checkpoint = storage.get_latest_campaign_checkpoint(result.campaign_id)
    state = json.loads(checkpoint["state_json"])
    assert state["campaign_liquidation_baseline"] == ["metal shield"]


def test_campaign_checkpoints_starter_segment_and_resumes_safely(tmp_path) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    calls: list[int] = []

    async def starter_segment(spec, profile_path: Path) -> RunResult:
        calls.append(spec.max_commands)
        return _record_segment_run(spec.database, profile_path, {"level": 2, "xp": 100})

    spec = load_campaign_spec(config_path)
    result = asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=starter_segment).run()
    )

    assert result.status == "blocked"
    assert result.state["level"] == 2
    assert "checkpointed for the next verified segment" in result.message
    assert calls == [250]

    with RunStorage(database) as storage:
        campaign = storage.get_campaign(result.campaign_id)
        segments = storage.list_campaign_segments(result.campaign_id)
        checkpoint = storage.get_latest_campaign_checkpoint(result.campaign_id)

    assert campaign["status"] == "blocked"
    assert len(segments) == 1
    assert segments[0]["phase"] == "starter-0-2"
    assert segments[0]["command_count"] == 1
    assert checkpoint["reason"] == "segment_complete"

    async def arena_segment(spec, profile_path: Path) -> RunResult:
        return _record_segment_run(spec.database, profile_path, {"level": 6, "xp": 100})

    resumed = asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=arena_segment).run()
    )

    assert resumed.campaign_id == result.campaign_id
    assert resumed.status == "blocked"
    assert "checkpointed for the next verified segment" in resumed.message


def test_campaign_recovers_practice_types_spent_at_current_level(tmp_path) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name=spec.name,
            config_path=config_path.resolve(),
            character_profile_path=spec.character_profile,
            target_level=spec.target_level,
        )
        run_id = storage.create_run(
            scenario_name="starter:Campaignmage",
            scenario_path=config_path,
        )
        storage.record_event(
            run_id,
            kind="game_event",
            payload={
                "type": "training_completed",
                "source": "text",
                "data": {"practice_type": "intellectual"},
            },
        )
        storage.finish_run(run_id, status="success")
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="mud-school-2-6",
            start_state={"level": 5, "xp": 10_000},
        )
        storage.finish_campaign_segment(
            segment_id,
            status="success",
            run_id=run_id,
            end_state={"level": 5, "xp": 10_500},
            command_count=1,
            duration_seconds=1.0,
        )
        failed_run_id = storage.create_run(
            scenario_name="starter:Campaignmage",
            scenario_path=config_path,
        )
        storage.record_event(
            failed_run_id,
            kind="game_event",
            payload={
                "type": "training_completed",
                "source": "text",
                "data": {"practice_type": "physical"},
            },
        )
        storage.finish_run(failed_run_id, status="failed", error="bounded abort")
        failed_segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="mud-school-2-6",
            start_state={"level": 5, "xp": 10_500},
        )
        storage.finish_campaign_segment(
            failed_segment_id,
            status="failed",
            run_id=failed_run_id,
            end_state={"level": 5, "xp": 10_500},
            command_count=1,
            duration_seconds=1.0,
            error="bounded abort",
        )

        at_level_five = _campaign_practice_types_spent(
            storage, campaign_id, level=5
        )
        at_level_six = _campaign_practice_types_spent(
            storage, campaign_id, level=6
        )

    assert at_level_five == frozenset({"physical", "intellectual"})
    assert at_level_six == frozenset()


def test_campaign_recovers_unfinished_counterbalance_preparation(tmp_path) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name=spec.name,
            config_path=config_path.resolve(),
            character_profile_path=spec.character_profile,
            target_level=spec.target_level,
        )
        training_run_id = storage.create_run(
            scenario_name="fastwalk-foundry:Campaignsmith",
            scenario_path=config_path,
        )
        storage.record_event(
            training_run_id,
            kind="game_event",
            payload={
                "type": "training_completed",
                "source": "text",
                "data": {
                    "skill": "counterbalance",
                    "practice_type": "physical",
                },
            },
        )
        storage.finish_run(training_run_id, status="failed", error="disconnect")
        training_segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="field-hunt",
            start_state={"level": 10, "xp": 45_000},
        )
        storage.finish_campaign_segment(
            training_segment_id,
            status="failed",
            run_id=training_run_id,
            end_state={"level": 10, "xp": 45_000},
            command_count=1,
            duration_seconds=1.0,
            error="disconnect",
        )

        assert _campaign_counterbalance_preparation_required(
            storage,
            campaign_id,
        )

        preparation_run_id = storage.create_run(
            scenario_name="fastwalk-foundry:Campaignsmith",
            scenario_path=config_path,
        )
        storage.record_event(
            preparation_run_id,
            kind="game_event",
            payload={
                "type": "equipment_preparation_completed",
                "source": "text",
                "data": {
                    "skill": "counterbalance",
                    "outcome": "completed",
                },
            },
        )
        storage.finish_run(preparation_run_id, status="success")
        preparation_segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="field-hunt",
            start_state={"level": 10, "xp": 45_000},
        )
        storage.finish_campaign_segment(
            preparation_segment_id,
            status="success",
            run_id=preparation_run_id,
            end_state={"level": 10, "xp": 45_100},
            command_count=1,
            duration_seconds=1.0,
        )

        assert not _campaign_counterbalance_preparation_required(
            storage,
            campaign_id,
        )


def test_campaign_recovers_permanent_trainer_rejections_at_current_level(
    tmp_path,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name=spec.name,
            config_path=config_path.resolve(),
            character_profile_path=spec.character_profile,
            target_level=spec.target_level,
        )
        run_id = storage.create_run(
            scenario_name="fastwalk-circus:Campaignmage",
            scenario_path=config_path,
        )
        for skill, reason in (
            ("stealth techniques", "trainer proficiency cap"),
            ("backstab", "unmet prerequisites"),
        ):
            storage.record_event(
                run_id,
                kind="game_event",
                payload={
                    "type": "training_rejected",
                    "source": "text",
                    "data": {
                        "skill": skill,
                        "practice_type": "intellectual",
                        "reason": reason,
                    },
                },
            )
        storage.finish_run(run_id, status="success")
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="circus-freak-show-8-9",
            start_state={"level": 8, "xp": 25_000},
        )
        storage.finish_campaign_segment(
            segment_id,
            status="success",
            run_id=run_id,
            end_state={"level": 8, "xp": 25_100},
            command_count=1,
            duration_seconds=1.0,
        )

        at_level_eight = _campaign_rejected_practice_skills(
            storage, campaign_id, level=8
        )
        at_level_nine = _campaign_rejected_practice_skills(
            storage, campaign_id, level=9
        )

    assert at_level_eight == frozenset({"stealth techniques"})
    assert at_level_nine == frozenset()


def test_campaign_rechecks_deferred_practice_type_at_current_level(tmp_path) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name=spec.name,
            config_path=config_path.resolve(),
            character_profile_path=spec.character_profile,
            target_level=spec.target_level,
        )
        run_id = storage.create_run(
            scenario_name="fastwalk-foundry:Campaignmage",
            scenario_path=config_path,
        )
        storage.record_event(
            run_id,
            kind="game_event",
            payload={
                "type": "training_deferred",
                "source": "text",
                "data": {"practice_type": "physical"},
            },
        )
        storage.finish_run(run_id, status="success")
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="foundry-circuit-7-8",
            start_state={"level": 7, "xp": 20_000},
        )
        storage.finish_campaign_segment(
            segment_id,
            status="success",
            run_id=run_id,
            end_state={"level": 7, "xp": 20_100},
            command_count=1,
            duration_seconds=1.0,
        )

        handled = _campaign_practice_types_spent(
            storage, campaign_id, level=7
        )

    assert handled == frozenset()


def test_campaign_preserves_per_level_practice_budget_across_segments(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    async def policy_segment(character, profile_path, policy, **kwargs):
        captured.update(kwargs)
        return _record_segment_run(database, profile_path, {"level": 5, "xp": 10_500})

    monkeypatch.setattr("dd4tester.campaign._run_policy_segment", policy_segment)

    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name=spec.name,
            config_path=config_path.resolve(),
            character_profile_path=spec.character_profile,
            target_level=spec.target_level,
        )
        prior_run_id = storage.create_run(
            scenario_name="mud-school:Campaignmage",
            scenario_path=config_path,
        )
        storage.record_event(
            prior_run_id,
            kind="game_event",
            payload={
                "type": "training_completed",
                "source": "text",
                "data": {"practice_type": "intellectual"},
            },
        )
        storage.finish_run(prior_run_id, status="success")
        prior_segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="mud-school-2-6",
            start_state={"level": 5, "xp": 10_000},
        )
        storage.finish_campaign_segment(
            prior_segment_id,
            status="success",
            run_id=prior_run_id,
            end_state={"level": 5, "xp": 10_400},
            command_count=1,
            duration_seconds=1.0,
        )
        runner = CampaignRunner(spec, config_path)
        asyncio.run(
            runner._run_starter(
                storage,
                campaign_id,
                {"level": 5, "xp": 10_400},
                storage.campaign_totals(campaign_id),
                policy_for(5, "mage"),
            )
        )

    assert captured["practice_types_spent"] == frozenset({"intellectual"})


def test_arena_segment_receives_campaign_practice_history(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 5})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy_for(5, "mage"),
            practice_types_spent=frozenset({"intellectual"}),
            counterbalance_preparation_required=True,
        )
    )

    assert captured["practice_types_spent"] == frozenset({"intellectual"})
    assert captured["counterbalance_preparation_required"] is True


def test_level_six_campaign_uses_the_verified_arena_after_foundry_retirement(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 6})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy_for(6, "warrior"),
            practice_types_spent=frozenset({"physical"}),
        )
    )

    assert captured["objective_level"] == 10
    assert captured["arena_kill_limit"] == 10
    assert captured["practice_types_spent"] == frozenset({"physical"})


def test_level_seven_campaign_starts_with_the_daycare_route(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 7})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy_for(7, "warrior"),
        )
    )

    assert captured["fastwalk_route"].name == "dwarven-daycare"
    assert [stop.target for stop in captured["fastwalk_hunt_stops"]] == [
        "old wrinkled nanny",
        "old wrinkled nanny",
    ]
    assert captured["fastwalk_kill_limit"] == 2


def test_level_seven_mage_campaign_uses_the_same_daycare_route(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 7})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy_for(7, "mage"),
        )
    )

    assert captured["fastwalk_route"].name == "dwarven-daycare"
    assert [stop.target for stop in captured["fastwalk_hunt_stops"]] == [
        "old wrinkled nanny",
        "old wrinkled nanny",
    ]
    assert captured["fastwalk_kill_limit"] == 2


def test_negative_nanny_result_runs_the_verified_circus_sweep(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 7})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(
        7,
        "thief",
        last_policy_id="moria-orc-circuit-7-8",
        policy_xp_deltas={"daycare-nanny-circuit-7-8": -46},
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_route"].name == "circus bearded lady"
    assert "vault_claim_items" not in captured
    assert "fastwalk_post_return_vault_items" not in captured
    assert captured["fastwalk_world_cache_items"] == ("ticket",)
    assert [stop.target for stop in captured["fastwalk_hunt_stops"]] == [
        "Bearded Lady",
        "Illusionist",
        "Midget",
        "Ivan the Strongman",
        None,
        None,
        "Ringmaster",
    ]
    assert captured["fastwalk_hunt_stops"][1].allowed_bystanders == ()
    assert captured["fastwalk_kill_limit"] == 3


def test_level_seven_daycare_fallback_runs_toward_level_eight(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 7})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy_for(7, "warrior", stalled_segments=1),
        )
    )

    assert captured["objective_level"] == 8
    assert [
        stop.target for stop in captured["fastwalk_hunt_stops"]
    ] == ["old wrinkled nanny", "old wrinkled nanny"]
    assert captured["fastwalk_kill_limit"] == 2


def test_depleted_level_seven_foundry_rotates_to_moria_orc_circuit(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 7})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(
        7,
        "thief",
        boot_kill_counts={
            "Lobuk": 4,
            "Golgog": 4,
            "Uburz": 4,
            "nanny": 2,
        },
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
            practice_types_spent=frozenset({"physical"}),
        )
    )

    assert captured["objective_level"] == 8
    assert captured["fastwalk_route"].name == "moria"
    assert [stop.target for stop in captured["fastwalk_hunt_stops"]] == [
        "large orc",
        "large orc",
        "orc",
        "small green garter snake",
    ]
    assert captured["fastwalk_hunt_stops"][2].allowed_bystanders == (
        "small green garter snake",
    )
    assert captured["fastwalk_kill_limit"] == 3
    assert captured["fastwalk_require_invisibility"] is False
    assert captured["practice_types_spent"] == frozenset({"physical"})


def test_level_eight_martial_moria_rotation_stops_after_large_orc(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 8})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(
        8,
        "warrior",
        last_policy_id="circus-freak-show-8-9",
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
            practice_types_spent=frozenset({"physical"}),
        )
    )

    assert captured["objective_level"] == 9
    assert captured["fastwalk_route"].name == "moria"
    assert [stop.target for stop in captured["fastwalk_hunt_stops"]] == [
        "large orc",
        "large orc",
    ]
    assert captured["fastwalk_hunt_stops"][0].route == (
        "west",
        "west",
        "north",
        "west",
    )
    assert captured["fastwalk_hunt_stops"][1].route == ("south",)
    assert captured["fastwalk_kill_limit"] == 1
    assert captured["fastwalk_require_invisibility"] is False
    assert captured["practice_types_spent"] == frozenset({"physical"})


def test_level_nine_martial_moria_rotation_sweeps_orcs_and_snake(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 9})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(
        9,
        "warrior",
        last_policy_id="circus-freak-show-9-10",
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
            practice_types_spent=frozenset({"physical"}),
        )
    )

    assert [stop.target for stop in captured["fastwalk_hunt_stops"]] == [
        "large orc",
        "large orc",
        "orc",
        "small green garter snake",
    ]
    assert captured["fastwalk_hunt_stops"][-1].minimum_health_ratio == 0.675
    assert captured["fastwalk_kill_limit"] == 3
    assert captured["fastwalk_require_invisibility"] is False


def test_level_eight_daycare_guard_hunt_uses_adaptive_maze_route(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 8})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(
        8,
        "warrior",
        last_policy_id="gnome-guard-circuit-8-9",
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_route"].name == "daycare-armed-guard"
    assert captured["fastwalk_route"].commands[-4:] == (
        "west",
        "south",
        "west",
        "down",
    )
    stops = captured["fastwalk_hunt_stops"]
    assert [stop.target for stop in stops] == ["armed guard"]
    assert stops[0].consider_only is False
    assert stops[0].route_vnums == ("6613", "6614", "6616", "6624")
    assert captured["fastwalk_kill_limit"] == 1
    assert captured["require_fastwalk_kill"] is False
    assert captured["allow_safe_fastwalk_abort"] is True


def test_level_eight_martial_ambush_dispatches_bounded_exterior_sweep(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 8})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(
        8,
        "warrior",
        last_policy_id="daycare-armed-guard-8-9",
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
            practice_types_spent=frozenset({"physical"}),
        )
    )

    assert captured["fastwalk_route"].name == "ambush"
    assert [stop.target for stop in captured["fastwalk_hunt_stops"]] == [
        "wounded goblin",
        "war dog",
        "goblin looter",
    ]
    assert captured["fastwalk_kill_limit"] == 3
    assert captured["fastwalk_require_invisibility"] is False
    assert captured["allow_safe_fastwalk_abort"] is True
    assert captured["practice_types_spent"] == frozenset({"physical"})


def test_depleted_level_seven_caster_dispatches_invisible_troll_hunt(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 7})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
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

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_route"].name == "gnome small troll"
    assert [stop.target for stop in captured["fastwalk_hunt_stops"]] == [
        "small troll"
    ]
    assert captured["fastwalk_hunt_stops"][0].minimum_health_ratio == 0.675
    assert captured["fastwalk_require_invisibility"] is True
    assert captured["fastwalk_train_before_departure"] is True
    assert captured["fastwalk_kill_limit"] == 1


def test_retired_cult_fanatic_research_dispatch_never_initiates_combat(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 8})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="cult-fanatic-research-8-9",
        minimum_level=8,
        maximum_level=9,
        status="retired",
        execution="cult-fanatic-research",
        summary="Retired live-consider research route.",
        evidence=(),
        practice_skill=None,
    )
    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_route"].name == "dragon cult"
    assert captured["fastwalk_route"].commands == (
        "south",
        "south",
        "south",
        "west",
        "north",
    )
    stops = captured["fastwalk_hunt_stops"]
    assert [stop.target for stop in stops] == ["fanatic monk"]
    assert stops[0].allowed_bystanders == ("receptionist",)
    assert stops[0].consider_only is True
    assert captured["require_fastwalk_kill"] is False


def test_fleshmonger_guard_research_dispatch_never_initiates_combat(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 8})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="fleshmonger-guard-research-8-9",
        minimum_level=8,
        maximum_level=9,
        status="retired",
        execution="fleshmonger-guard-research",
        summary="Retired live-consider research route.",
        evidence=(),
        practice_skill=None,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_route"].name == "fleshmonger"
    assert captured["fastwalk_route"].recall_after_loot is True
    stops = captured["fastwalk_hunt_stops"]
    assert [stop.target for stop in stops] == ["patrolling guard"]
    assert stops[0].consider_only is True
    assert captured["require_fastwalk_kill"] is False


def test_fleshmonger_guard_kill_research_dispatch_is_bounded(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 10})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="fleshmonger-guard-kill-research-10-11",
        minimum_level=10,
        maximum_level=11,
        status="research",
        execution="fleshmonger-guard-hunt",
        summary="One bounded live combat probe.",
        evidence=(),
        practice_skill="enhanced damage",
        segment_kill_limit=1,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_route"].name == "fleshmonger"
    assert captured["fastwalk_route"].recall_after_loot is True
    assert captured["fastwalk_kill_limit"] == 1
    stops = captured["fastwalk_hunt_stops"]
    assert [stop.target for stop in stops] == ["patrolling guard"]
    assert stops[0].consider_only is False
    assert stops[0].minimum_health_ratio == 0.85
    assert captured["require_fastwalk_kill"] is False


def test_fleshmonger_mufti_research_dispatch_never_initiates_combat(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 10})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="fleshmonger-mufti-probe-10-11",
        minimum_level=10,
        maximum_level=11,
        status="research",
        execution="fleshmonger-mufti-research",
        summary="No-combat barracks probe.",
        evidence=(),
        practice_skill="backstab",
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_route"].name == "fleshmonger"
    assert captured["fastwalk_route"].recall_after_loot is True
    stops = captured["fastwalk_hunt_stops"]
    assert [stop.target for stop in stops] == ["mufti guard"]
    assert stops[0].route == ("open south", "south")
    assert stops[0].consider_only is True
    assert captured["require_fastwalk_kill"] is False


def test_fleshmonger_servant_research_dispatch_never_opens_laboratory(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 10})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="fleshmonger-servant-probe-v1-10-11",
        minimum_level=10,
        maximum_level=11,
        status="research",
        execution="fleshmonger-servant-research",
        summary="No-combat Study probe.",
        evidence=(),
        practice_skill="backstab",
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_route"].name == "fleshmonger"
    assert captured["fastwalk_route"].recall_after_loot is True
    stops = captured["fastwalk_hunt_stops"]
    assert [stop.route for stop in stops] == [("up", "up")]
    assert [stop.target for stop in stops] == ["hobgoblin servant"]
    assert stops[0].consider_only is True
    assert "open up" not in stops[0].route
    assert captured["require_fastwalk_kill"] is False


def test_fleshmonger_servant_kill_research_dispatch_is_one_fight(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 10})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="fleshmonger-servant-kill-research-v1-10-11",
        minimum_level=10,
        maximum_level=11,
        status="research",
        execution="fleshmonger-servant-hunt",
        summary="One bounded Study fight.",
        evidence=(),
        practice_skill="backstab",
        segment_kill_limit=1,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_route"].name == "fleshmonger"
    assert captured["fastwalk_route"].recall_after_loot is True
    assert captured["fastwalk_kill_limit"] == 1
    stops = captured["fastwalk_hunt_stops"]
    assert [stop.target for stop in stops] == ["hobgoblin servant"]
    assert stops[0].consider_only is False
    assert stops[0].minimum_health_ratio == 0.85
    assert captured["require_fastwalk_kill"] is False


def test_fleshmonger_extended_rotation_dispatch_retains_two_kill_cap(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 10})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="fleshmonger-thief-extended-rotation-research-v1-10-11",
        minimum_level=10,
        maximum_level=11,
        status="research",
        execution="fleshmonger-thief-extended-rotation-research",
        summary="Bounded four-target rotation.",
        evidence=(),
        practice_skill="backstab",
        segment_kill_limit=2,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_route"].name == "fleshmonger"
    assert captured["fastwalk_route"].recall_after_loot is True
    assert captured["fastwalk_kill_limit"] == 2
    assert captured["fastwalk_xp_first_capacity_threshold"] == 20
    stops = captured["fastwalk_hunt_stops"]
    assert stops[-1].target == "hobgoblin servant"
    assert stops[-1].route == ("west", "up", "up")
    assert captured["require_fastwalk_kill"] is False


def test_fleshmonger_cook_research_dispatch_allows_only_helper(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 10})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="fleshmonger-cook-probe-v2-10-11",
        minimum_level=10,
        maximum_level=11,
        status="research",
        execution="fleshmonger-cook-research",
        summary="No-combat kitchen probe.",
        evidence=(),
        practice_skill="backstab",
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    stops = captured["fastwalk_hunt_stops"]
    assert [stop.target for stop in stops] == ["cook", "cook"]
    assert stops[0].route == ("open east", "east")
    assert [stop.command_keyword for stop in stops] == ["cook", "2.cook"]
    assert all(stop.allowed_bystanders == ("cook's boy",) for stop in stops)
    assert all(stop.consider_only is True for stop in stops)
    assert captured["require_fastwalk_kill"] is False


def test_fleshmonger_cook_kill_research_dispatch_is_one_kill(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 10})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="fleshmonger-cook-10-11",
        minimum_level=10,
        maximum_level=11,
        status="verified",
        execution="fleshmonger-cook-hunt",
        summary="One bounded kitchen fight.",
        evidence=(),
        practice_skill="backstab",
        segment_kill_limit=1,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_kill_limit"] == 1
    stops = captured["fastwalk_hunt_stops"]
    assert [stop.target for stop in stops] == ["cook", "cook"]
    assert [stop.command_keyword for stop in stops] == ["cook", "2.cook"]
    assert all(stop.trivial_bystanders == ("cook's boy",) for stop in stops)
    assert all(stop.consider_only is False for stop in stops)


def test_ambush_archer_research_dispatch_never_initiates_combat(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 10})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="ambush-archer-probe-10-11",
        minimum_level=10,
        maximum_level=11,
        status="research",
        execution="ambush-archer-research",
        summary="No-combat archer probe.",
        evidence=(),
        practice_skill="backstab",
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_route"].name == "ambush"
    assert captured["fastwalk_route"].recall_after_loot is True
    stops = captured["fastwalk_hunt_stops"]
    assert [stop.target for stop in stops] == ["goblin archer"]
    assert stops[0].consider_only is True
    assert captured["require_fastwalk_kill"] is False


def test_ambush_archer_kill_research_dispatch_is_one_kill(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 10})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="ambush-archer-kill-research-10-11",
        minimum_level=10,
        maximum_level=11,
        status="research",
        execution="ambush-archer-hunt",
        summary="One bounded archer fight.",
        evidence=(),
        practice_skill="backstab",
        segment_kill_limit=1,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_kill_limit"] == 1
    stops = captured["fastwalk_hunt_stops"]
    assert [stop.target for stop in stops] == ["goblin archer"]
    assert stops[0].consider_only is False
    assert stops[0].minimum_health_ratio == 0.85


def test_gnome_guard_level_ten_research_dispatch_is_noncombat(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 10})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="gnome-guard-hut-probe-10-11",
        minimum_level=10,
        maximum_level=11,
        status="research",
        execution="gnome-guard-research",
        summary="Inspect the hut guard without attacking.",
        evidence=(),
        practice_skill="backstab",
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["objective_level"] == 11
    assert captured["fastwalk_route"].name == "gnome guard hut"
    stops = captured["fastwalk_hunt_stops"]
    assert len(stops) == 1
    assert stops[0].consider_only is True
    assert captured["require_fastwalk_kill"] is False
    assert captured["allow_safe_fastwalk_abort"] is True


def test_fleshmonger_thief_rotation_research_dispatch_is_two_kills(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 10})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="fleshmonger-thief-rotation-research-v5-10-11",
        minimum_level=10,
        maximum_level=11,
        status="research",
        execution="fleshmonger-thief-rotation-research",
        summary="Sweep three evidenced targets.",
        evidence=(),
        practice_skill="backstab",
        segment_kill_limit=2,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_kill_limit"] == 2
    assert captured["fastwalk_route"].recall_after_loot is True
    stops = captured["fastwalk_hunt_stops"]
    assert [stop.target for stop in stops] == [
        "patrolling guard",
        "on-duty guard",
        "cook",
        "cook",
    ]
    assert [stop.command_keyword for stop in stops[2:]] == ["cook", "2.cook"]
    assert captured["require_fastwalk_kill"] is False
    assert captured["allow_safe_fastwalk_abort"] is True


def test_level_eleven_thief_rotation_targets_level_twelve(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 11})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(11, "thief")

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["objective_level"] == 12
    assert captured["fastwalk_kill_limit"] == 2
    assert [stop.target for stop in captured["fastwalk_hunt_stops"]] == [
        "patrolling guard",
        "on-duty guard",
        "cook",
        "cook",
        "hobgoblin servant",
    ]


def test_fleshmonger_two_guard_research_dispatch_excludes_basement(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 10})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="fleshmonger-two-guard-research-v2-10-11",
        minimum_level=10,
        maximum_level=11,
        status="research",
        execution="fleshmonger-guard-circuit-research",
        summary="Two bounded live combat probes.",
        evidence=(),
        practice_skill="enhanced damage",
        segment_kill_limit=2,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_kill_limit"] == 2
    stops = captured["fastwalk_hunt_stops"]
    assert [stop.target for stop in stops] == [
        "patrolling guard",
        "on-duty guard",
    ]
    assert stops[1].route == ("open north", "north")
    assert stops[1].minimum_health_ratio == 0.60
    assert all("down" not in stop.route for stop in stops)


def test_depleted_level_seven_foundry_tries_daycare_before_moria(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 7})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(
        7,
        "warrior",
        boot_kill_counts={"Lobuk": 4, "Golgog": 4, "Uburz": 4},
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
            practice_types_spent=frozenset({"physical"}),
        )
    )

    assert captured["fastwalk_route"].name == "dwarven-daycare"
    assert captured["fastwalk_route"].commands == (
        "south",
        "south",
        "east",
        "east",
        "east",
        "east",
        "east",
        "east",
        "down",
        "south",
        "south",
    )
    assert [stop.target for stop in captured["fastwalk_hunt_stops"]] == [
        "old wrinkled nanny",
        "old wrinkled nanny",
    ]
    assert captured["fastwalk_kill_limit"] == 2


def test_depleted_level_seven_daycare_rotates_to_moria(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 7})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(
        7,
        "warrior",
        boot_kill_counts={"Lobuk": 4, "Golgog": 4, "Uburz": 4},
        last_policy_id="daycare-nanny-circuit-7-8",
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
            practice_types_spent=frozenset({"physical"}),
        )
    )

    assert captured["fastwalk_route"].name == "moria"
    assert [stop.target for stop in captured["fastwalk_hunt_stops"]] == [
        "large orc",
        "large orc",
        "orc",
        "small green garter snake",
    ]
    assert captured["fastwalk_kill_limit"] == 3
    assert captured["fastwalk_require_invisibility"] is False
    assert captured["practice_types_spent"] == frozenset({"physical"})


def test_depleted_level_seven_moria_rotates_to_gnome_hermit(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 7})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(
        7,
        "warrior",
        boot_kill_counts={"Lobuk": 4, "Golgog": 4, "Uburz": 4},
        last_policy_id="moria-orc-circuit-7-8",
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
            practice_types_spent=frozenset({"physical"}),
        )
    )

    assert captured["fastwalk_route"].name == "gnome-hermit"
    assert [stop.target for stop in captured["fastwalk_hunt_stops"]] == [
        "hermit",
        "hobgoblin miner",
        "hobgoblin miner",
    ]
    assert captured["fastwalk_kill_limit"] == 3
    assert captured["fastwalk_require_invisibility"] is False
    assert captured["practice_types_spent"] == frozenset({"physical"})


def test_campaign_completes_when_a_segment_reaches_target(tmp_path) -> None:
    config_path, database = _write_campaign_files(tmp_path, target_level=2)

    async def starter_segment(spec, profile_path: Path) -> RunResult:
        return _record_segment_run(spec.database, profile_path, {"level": 2, "xp": 100})

    result = asyncio.run(
        CampaignRunner(
            load_campaign_spec(config_path),
            config_path,
            segment_runner=starter_segment,
        ).run()
    )

    assert result.status == "success"
    assert result.message == "Target level 2 reached."
    with RunStorage(database) as storage:
        assert storage.get_campaign(result.campaign_id)["status"] == "success"


def test_campaign_reopens_stale_success_below_target(tmp_path) -> None:
    config_path, database = _write_campaign_files(tmp_path, target_level=3)
    levels = iter((2, 3))
    calls: list[int] = []

    async def starter_segment(spec, profile_path: Path) -> RunResult:
        level = next(levels)
        calls.append(level)
        return _record_segment_run(
            spec.database,
            profile_path,
            {"level": level, "xp": level * 100},
        )

    spec = load_campaign_spec(config_path)
    first = asyncio.run(
        CampaignRunner(
            spec,
            config_path,
            segment_runner=starter_segment,
        ).run()
    )
    with RunStorage(database) as storage:
        storage.finish_campaign(first.campaign_id, status="success")

    resumed = asyncio.run(
        CampaignRunner(
            spec,
            config_path,
            segment_runner=starter_segment,
        ).run()
    )

    assert calls == [2, 3]
    assert resumed.status == "success"
    assert resumed.state["level"] == 3
    with RunStorage(database) as storage:
        checkpoint = storage.get_latest_campaign_checkpoint(first.campaign_id)
        assert checkpoint is not None
        assert json.loads(checkpoint["state_json"])["level"] == 3


def test_campaign_checkpoints_newer_external_state_that_reached_target(
    tmp_path,
) -> None:
    config_path, database = _write_campaign_files(tmp_path, target_level=3)

    async def starter_segment(spec, profile_path: Path) -> RunResult:
        return _record_segment_run(
            spec.database,
            profile_path,
            {"level": 2, "xp": 100},
        )

    spec = load_campaign_spec(config_path)
    initial = asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=starter_segment).run()
    )
    with RunStorage(database) as storage:
        run_id = storage.create_run(
            scenario_name="external:Campaignmage",
            scenario_path=config_path,
        )
        event_id = storage.record_event(
            run_id,
            kind="game_event",
            payload={"type": "progress_changed"},
        )
        storage.record_state_snapshot(
            run_id,
            source_event_id=event_id,
            reason="progress_changed",
            state={"name": "Campaignmage", "level": 3, "xp": 300},
        )
        storage.finish_run(run_id, status="success")
        storage.finish_campaign(initial.campaign_id, status="success")

    resumed = asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=starter_segment).run()
    )

    assert resumed.status == "success"
    with RunStorage(database) as storage:
        checkpoint = storage.get_latest_campaign_checkpoint(initial.campaign_id)
        assert checkpoint is not None
        assert checkpoint["reason"] == "target_reconciled"
        assert json.loads(checkpoint["state_json"])["level"] == 3


def test_campaign_resumes_from_newer_external_character_state(tmp_path) -> None:
    config_path, database = _write_campaign_files(tmp_path)

    async def segment(spec, profile_path: Path) -> RunResult:
        return _record_segment_run(
            spec.database,
            profile_path,
            {"level": 2, "xp": 100},
        )

    spec = load_campaign_spec(config_path)
    initial = asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=segment).run()
    )
    with RunStorage(database) as storage:
        run_id = storage.create_run(
            scenario_name="external:Campaignmage",
            scenario_path=config_path,
        )
        event_id = storage.record_event(
            run_id,
            kind="game_event",
            payload={"type": "progress_changed"},
        )
        storage.record_state_snapshot(
            run_id,
            source_event_id=event_id,
            reason="progress_changed",
            state={"name": "Campaignmage", "level": 7, "xp": 20_000},
        )
        storage.finish_run(run_id, status="success")

    resumed = asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=segment).run()
    )

    assert resumed.campaign_id == initial.campaign_id
    with RunStorage(database) as storage:
        segments = storage.list_campaign_segments(resumed.campaign_id)
    assert segments[-1]["phase"] == "daycare-nanny-circuit-7-8"


def test_campaign_selects_sack_phase_from_persisted_inventory(tmp_path) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    runner = CampaignRunner(load_campaign_spec(config_path), config_path)

    before = runner._policy_for_state(
        {"level": 8, "inventory": [[{"short_desc": "a big pot pie"}]]}
    )
    after = runner._policy_for_state(
        {
            "level": 8,
            "inventory": [[
                {"short_desc": "a large sack"},
                {"short_desc": "a big pot pie"},
            ]],
        }
    )

    assert before.policy_id == "midennir-sack-8-10"
    assert after.policy_id == "ambush-war-dog-8-9"

    runner._historical_large_sack = True
    after_lodging = runner._policy_for_state(
        {"level": 8, "inventory": [[{"short_desc": "a big pot pie"}]]}
    )
    assert after_lodging.policy_id == "ambush-war-dog-8-9"
    with_loot = runner._policy_for_state(
        {"level": 8, "inventory": [[{"short_desc": "hard leather boots"}]]}
    )
    assert with_loot.policy_id == "liquidate-loot"
    after_own_corpse_recovery = runner._policy_for_state(
        {
            "level": 8,
            "inventory": [[
                {"short_desc": "hard leather boots"},
                {"short_desc": "a big pot pie"},
            ]],
            "acquired_items": [
                {
                    "item": (
                        "hard leather boots from the corpse of Campaignmage"
                    )
                }
            ],
        }
    )
    assert after_own_corpse_recovery.policy_id == "ambush-war-dog-8-9"

    with_useful_carried_collars = runner._policy_for_state(
        {
            "level": 8,
            "inventory": [[
                {"short_desc": "a war dog collar", "quan": "2"},
                {"short_desc": "a big pot pie"},
            ]],
            "stats": {"carry_wt": 102, "maxcarry_wt": 140},
        }
    )
    assert with_useful_carried_collars.policy_id == "ambush-war-dog-8-9"

    with_two_collars_under_temporary_capacity_pressure = runner._policy_for_state(
        {
            "level": 8,
            "inventory": [[
                {"short_desc": "a war dog collar", "quan": "2"},
                {"short_desc": "a big pot pie", "quan": "5"},
            ]],
            "stats": {"carry_wt": 126, "maxcarry_wt": 140},
        }
    )
    assert (
        with_two_collars_under_temporary_capacity_pressure.policy_id
        == "ambush-war-dog-8-9"
    )

    sack = ObjectSource(
        4529,
        "sack large",
        "a large sack",
        15,
        (400, 0, 0, 0),
        0,
        weight=50,
    )
    runner._gear_catalog = GearCatalog({sack.vnum: sack})
    with_oversized_sack_after_full_vault = runner._policy_for_state(
        {
            "level": 8,
            "inventory": [[
                {"short_desc": "a large sack"},
                {"short_desc": "a big pot pie"},
                {"short_desc": "a buffalo water skin"},
            ]],
            "stats": {"carry_wt": 135, "maxcarry_wt": 140},
            "campaign_has_weapon": True,
            "vault_storage_rejected": True,
        }
    )
    assert with_oversized_sack_after_full_vault.policy_id == "vault-spare-gear"

    with_collar_weight_pressure = runner._policy_for_state(
        {
            "level": 8,
            "inventory": [[{"short_desc": "a war dog collar", "quan": "3"}]],
            "stats": {"carry_wt": 126, "maxcarry_wt": 140},
        }
    )
    assert with_collar_weight_pressure.policy_id == "liquidate-loot"

    without_food = runner._policy_for_state(
        {
            "level": 8,
            "inventory": [[{"short_desc": "a buffalo water skin"}]],
            "stats": {"carry_wt": 102, "maxcarry_wt": 250},
        }
    )
    assert without_food.policy_id == "restock-provisions"

    with_serialized_food = runner._policy_for_state(
        {
            "level": 8,
            "inventory": (
                '[[{"quan":"10","short_desc":"a big pot pie"},'
                '{"quan":"1","short_desc":"a buffalo water skin"}]]'
            ),
        }
    )
    assert with_serialized_food.policy_id == "ambush-war-dog-8-9"


def test_campaign_selects_rearm_after_persisted_weapon_loss(tmp_path) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    runner = CampaignRunner(load_campaign_spec(config_path), config_path)

    policy = runner._policy_for_state(
        {
            "level": 7,
            "inventory": [[{"short_desc": "a big pot pie"}]],
            "campaign_has_weapon": False,
        }
    )

    assert policy.policy_id == "rearm-primary-weapon"
    assert policy.execution == "rearm-weapon"


def test_campaign_selects_outfit_for_recorded_empty_basic_slots(tmp_path) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    runner = CampaignRunner(load_campaign_spec(config_path), config_path)

    policy = runner._policy_for_state(
        {
            "level": 8,
            "inventory": [[{"short_desc": "a big pot pie"}]],
            "campaign_has_weapon": True,
            "campaign_empty_equipment_categories": ["head", "neck", "arms"],
        }
    )

    assert policy.policy_id == "outfit-basic-gear"
    assert policy.execution == "outfit-basic-gear"


def test_campaign_does_not_repeat_deferred_outfit_at_same_level(tmp_path) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    runner = CampaignRunner(load_campaign_spec(config_path), config_path)

    policy = runner._policy_for_state(
        {
            "level": 8,
            "inventory": [[{"short_desc": "a big pot pie"}]],
            "campaign_has_weapon": True,
            "campaign_empty_equipment_categories": ["body"],
            "campaign_outfit_attempted_level": 8,
        }
    )

    assert policy.policy_id == "recover-basic-body-gear"
    assert policy.execution == "recover-basic-body"


def test_campaign_suppresses_repeated_body_recovery_at_same_level(tmp_path) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    runner = CampaignRunner(load_campaign_spec(config_path), config_path)

    policy = runner._policy_for_state(
        {
            "level": 8,
            "inventory": [[{"short_desc": "a big pot pie"}]],
            "campaign_has_weapon": True,
            "campaign_empty_equipment_categories": ["body"],
            "campaign_outfit_attempted_level": 8,
            "campaign_body_gear_attempted_level": 8,
        }
    )

    assert policy.execution not in {"outfit-basic-gear", "recover-basic-body"}


def test_campaign_prioritizes_school_accessories_before_waist_and_ring(
    tmp_path,
) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    runner = CampaignRunner(load_campaign_spec(config_path), config_path)
    state = {
        "level": 8,
        "inventory": [[{"short_desc": "a big pot pie"}]],
        "campaign_has_weapon": True,
        "campaign_empty_equipment_categories": [
            "float",
            "wrist",
            "waist",
            "finger",
        ],
        "campaign_outfit_attempted_level": 8,
    }

    policy = runner._policy_for_state(state)
    assert policy.execution == "recover-school-wrist-float"

    state["campaign_school_wrist_float_attempted_level"] = 8
    policy = runner._policy_for_state(state)
    assert policy.execution == "recover-gremlin-waist"

    state["campaign_gremlin_waist_attempted_level"] = 8
    policy = runner._policy_for_state(state)
    assert policy.execution == "recover-daycare-ring"


def test_campaign_retries_missing_daycare_rings_after_reboot(tmp_path) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    runner = CampaignRunner(load_campaign_spec(config_path), config_path)
    runner._boot_id = "new boot"
    state = {
        "level": 8,
        "inventory": [[{"short_desc": "a big pot pie"}]],
        "campaign_has_weapon": True,
        "campaign_empty_equipment_categories": ["finger"],
        "campaign_outfit_attempted_level": 8,
        "campaign_daycare_ring_attempted_level": 8,
        "campaign_daycare_ring_attempted_boot_id": "old boot",
        "campaign_daycare_ring_cooldown": 3,
    }

    assert runner._policy_for_state(state).execution == "recover-daycare-ring"

    state["campaign_daycare_ring_attempted_boot_id"] = "new boot"

    assert runner._policy_for_state(state).execution != "recover-daycare-ring"
    state["campaign_daycare_ring_cooldown"] = 0

    assert runner._policy_for_state(state).execution == "recover-daycare-ring"


def test_daycare_ring_retry_cooldown_counts_productive_field_segments() -> None:
    state = {"campaign_daycare_ring_cooldown": 3}

    for _ in range(3):
        state = _advance_daycare_ring_cooldown(
            state,
            execution="fleshmonger-thief-rotation",
            xp_delta=50,
        )

    assert state["campaign_daycare_ring_cooldown"] == 0
    unchanged = _advance_daycare_ring_cooldown(
        {"campaign_daycare_ring_cooldown": 3},
        execution="sell-loot",
        xp_delta=500,
    )
    assert unchanged["campaign_daycare_ring_cooldown"] == 3


def test_war_dog_collar_retry_cooldown_counts_productive_field_segments() -> None:
    state = {"campaign_war_dog_collar_cooldown": 3}

    for _ in range(3):
        state = _advance_war_dog_collar_cooldown(
            state,
            execution="fleshmonger-thief-rotation",
            xp_delta=50,
        )

    assert state["campaign_war_dog_collar_cooldown"] == 0
    unchanged = _advance_war_dog_collar_cooldown(
        {"campaign_war_dog_collar_cooldown": 3},
        execution="sell-loot",
        xp_delta=500,
    )
    assert unchanged["campaign_war_dog_collar_cooldown"] == 3


def test_policy_revision_migrates_missing_daycare_ring_to_cooldown() -> None:
    migrated = _refresh_policy_revision(
        {
            "level": 11,
            "campaign_policy_revision": 32,
            "campaign_daycare_ring_attempted_level": 11,
            "campaign_daycare_ring_attempted_boot_id": "current boot",
            "campaign_empty_equipment_categories": ["finger"],
        }
    )

    assert migrated["campaign_policy_revision"] == 37
    assert migrated["campaign_daycare_ring_cooldown"] == 3


def test_campaign_retries_missing_war_dog_collar_after_reboot(tmp_path) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    runner = CampaignRunner(load_campaign_spec(config_path), config_path)
    runner._boot_id = "new boot"
    state = {
        "level": 8,
        "inventory": [[{"short_desc": "a big pot pie"}]],
        "campaign_has_weapon": True,
        "campaign_empty_equipment_categories": ["neck"],
        "campaign_outfit_attempted_level": 8,
        "campaign_war_dog_collar_attempted_level": 8,
        "campaign_war_dog_collar_attempted_boot_id": "old boot",
        "campaign_war_dog_collar_cooldown": 3,
    }

    assert runner._policy_for_state(state).execution == "recover-war-dog-collar"
    state["campaign_war_dog_collar_attempted_boot_id"] = "new boot"

    assert runner._policy_for_state(state).execution != "recover-war-dog-collar"
    state["campaign_war_dog_collar_cooldown"] = 0

    assert runner._policy_for_state(state).execution == "recover-war-dog-collar"


def test_policy_revision_retries_collar_after_a_preflight_defect() -> None:
    migrated = _refresh_policy_revision(
        {
            "level": 11,
            "campaign_policy_revision": 36,
            "campaign_war_dog_collar_attempted_level": 11,
            "campaign_war_dog_collar_attempted_boot_id": "current boot",
            "campaign_war_dog_collar_cooldown": 3,
            "campaign_empty_equipment_categories": ["neck"],
        }
    )

    assert migrated["campaign_policy_revision"] == 37
    assert "campaign_war_dog_collar_attempted_level" not in migrated
    assert "campaign_war_dog_collar_attempted_boot_id" not in migrated
    assert "campaign_war_dog_collar_cooldown" not in migrated


def test_campaign_skips_gear_recovery_without_required_free_weight(tmp_path) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    runner = CampaignRunner(load_campaign_spec(config_path), config_path)

    policy = runner._policy_for_state(
        {
            "level": 8,
            "inventory": [[{"short_desc": "a big pot pie"}]],
            "stats": {"carry_wt": 124, "maxcarry_wt": 140},
            "campaign_has_weapon": True,
            "campaign_empty_equipment_categories": ["wrist", "finger"],
            "campaign_outfit_attempted_level": 8,
        }
    )

    assert policy.execution not in {
        "recover-school-wrist-float",
        "recover-daycare-ring",
    }


def test_campaign_uses_feasible_lighter_recovery_when_heavier_one_will_not_fit(
    tmp_path,
) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    runner = CampaignRunner(load_campaign_spec(config_path), config_path)

    policy = runner._policy_for_state(
        {
            "level": 8,
            "inventory": [[{"short_desc": "a big pot pie"}]],
            "stats": {"carry_wt": 115, "maxcarry_wt": 140},
            "campaign_has_weapon": True,
            "campaign_empty_equipment_categories": ["wrist", "finger"],
            "campaign_outfit_attempted_level": 8,
        }
    )

    assert policy.execution == "recover-daycare-ring"


def test_campaign_prioritizes_no_recall_school_exit_over_city_maintenance(
    tmp_path,
) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    runner = CampaignRunner(load_campaign_spec(config_path), config_path)

    policy = runner._policy_for_state(
        {
            "level": 8,
            "room_vnum": "3722",
            "area": "Mud School",
            "inventory": [[{"short_desc": "a pair of spare sleeves"}]],
            "campaign_has_weapon": True,
            "campaign_empty_equipment_categories": ["wrist", "waist", "finger"],
            "campaign_outfit_attempted_level": 8,
            "campaign_school_wrist_float_attempted_level": 8,
        }
    )

    assert policy.policy_id == "recover-school-wrist-float"
    assert policy.execution == "recover-school-wrist-float"


def test_campaign_recognizes_steak_as_food_during_gear_recovery(tmp_path) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    runner = CampaignRunner(load_campaign_spec(config_path), config_path)

    policy = runner._policy_for_state(
        {
            "level": 8,
            "room_vnum": "3054",
            "inventory": [[{"short_desc": "a juicy steak"}]],
            "campaign_has_weapon": True,
            "campaign_empty_equipment_categories": ["wrist"],
            "campaign_outfit_attempted_level": 8,
        }
    )

    assert policy.execution == "recover-school-wrist-float"


def test_campaign_outfit_policy_uses_verified_leather_shop_route(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 8})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(8, "mage", needs_basic_gear=True)

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
            practice_types_spent=frozenset({"physical"}),
            rejected_practice_skills=frozenset({"second attack"}),
        )
    )

    assert captured == {"city_outfit": True}


def test_campaign_body_recovery_uses_registered_foundry_stop(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 8})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(8, "mage", needs_body_gear_recovery=True)

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
            practice_types_spent=frozenset({"physical"}),
            rejected_practice_skills=frozenset({"second attack"}),
        )
    )

    assert captured["fastwalk_route"].name == "foundry"
    assert captured["objective_level"] == 100
    assert captured["fastwalk_required_free_weight"] == 7
    assert captured["fastwalk_kill_limit"] == 1
    assert captured["require_fastwalk_kill"] is False
    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.target == "oshu"
    assert stop.required_items == ("leather jerkin",)


def test_campaign_school_accessory_recovery_uses_bounded_tutorial_stops(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 8})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(8, "mage", needs_school_wrist_float=True)

    asyncio.run(_run_policy_segment(spec.character, spec.character_profile, policy))

    assert captured["fastwalk_route"].name == "mud-school-accessories"
    assert captured["objective_level"] == 100
    assert captured["fastwalk_required_free_weight"] == 30
    assert "fastwalk_kill_limit" not in captured
    portal, lizardman, cleanup, gladiator, exit_stop = captured[
        "fastwalk_hunt_stops"
    ]
    assert portal.actions == ("enter portal",)
    assert lizardman.required_items == ("copper bracer",)
    assert cleanup.actions == ("sacrifice cape",)
    assert gladiator.required_items == (
        "copper bracer",
        "copper bracer",
        "snowy white stone",
    )
    assert exit_stop.actions[-3:] == ("down", "down", "north")
    assert all(
        stop.allow_below_band_for_required_loot
        for stop in (lizardman, gladiator)
    )


def test_campaign_daycare_ring_recovery_targets_source_old_doll(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 8})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(8, "mage", needs_daycare_ring=True)

    asyncio.run(_run_policy_segment(spec.character, spec.character_profile, policy))

    assert captured["fastwalk_route"].name == "dwarven-daycare-ring"
    assert captured["objective_level"] == 100
    assert captured["fastwalk_required_free_weight"] == 21
    assert captured["fastwalk_kill_limit"] == 3
    first, second, nanny = captured["fastwalk_hunt_stops"]
    assert first.target == "abused and old doll"
    assert first.required_items == ("pink ice ring",)
    assert first.maximum_target_count == 2
    assert second.target == "abused and old doll"
    assert second.required_items == ("pink ice ring", "pink ice ring")
    assert second.maximum_target_count == 1
    assert nanny.target == "old wrinkled nanny"
    assert nanny.required_items == ("linen robe",)


def test_campaign_war_dog_collar_recovery_targets_source_carrier(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 8})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(8, "thief", needs_war_dog_collar=True)

    asyncio.run(_run_policy_segment(spec.character, spec.character_profile, policy))

    assert captured["fastwalk_route"].name == "ambush"
    assert captured["objective_level"] == 100
    assert captured["fastwalk_required_free_weight"] == 20
    assert captured["fastwalk_kill_limit"] == 1
    assert captured["fastwalk_require_invisibility"] is False
    assert captured["fastwalk_origin_actions"][:2] == ("wear collar", "eq all")
    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.target == "war dog"
    assert stop.required_items == ("war dog collar",)
    assert stop.exact_target is True


def test_campaign_piercing_upgrade_dispatches_bounded_forest_hunt(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 11})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(
        11,
        "thief",
        needs_piercing_weapon_upgrade=True,
        has_flight=True,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
            practice_types_spent=frozenset({"physical"}),
            rejected_practice_skills=frozenset({"second attack"}),
        )
    )

    assert captured["fastwalk_route"].name == "forest bear claws"
    assert captured["objective_level"] == 14
    assert captured["fastwalk_required_free_weight"] == 5
    assert captured["fastwalk_required_move"] == 246
    assert captured["fastwalk_kill_limit"] == 1
    assert captured["fastwalk_train_before_departure"] is True
    assert captured["require_fastwalk_kill"] is False
    assert captured["allow_safe_fastwalk_abort"] is True
    assert captured["practice_types_spent"] == frozenset({"physical"})
    assert captured["rejected_practice_skills"] == frozenset({"second attack"})
    stops = captured["fastwalk_hunt_stops"]
    assert len(stops) == 5
    assert all(stop.target == "giant kodiak bear" for stop in stops)
    assert all(
        stop.required_items == ("pair of bears claws",) for stop in stops
    )


def test_campaign_waist_recovery_targets_source_baby_gremlin(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 8})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(8, "mage", needs_gremlin_waist=True)

    asyncio.run(_run_policy_segment(spec.character, spec.character_profile, policy))

    assert captured["fastwalk_route"].name == "gremlin-lair-waist"
    assert captured["objective_level"] == 100
    assert captured["fastwalk_required_free_weight"] == 5
    assert captured["fastwalk_kill_limit"] == 1
    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.target == "baby gremlin"
    assert stop.required_items == ("diaper",)


def test_level_eight_mage_campaign_uses_unprotected_dog_stop(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 8})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(8, "mage", has_large_sack=True)

    asyncio.run(_run_policy_segment(spec.character, spec.character_profile, policy))

    assert captured["fastwalk_kill_limit"] == 1
    (dog,) = captured["fastwalk_hunt_stops"]
    assert dog.target == "war dog"


def test_level_eight_mage_campaign_uses_protected_two_stop_ambush_circuit(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 8})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(
        8,
        "mage",
        has_large_sack=True,
        has_sanctuary_potion=True,
    )

    asyncio.run(_run_policy_segment(spec.character, spec.character_profile, policy))

    assert captured["fastwalk_kill_limit"] == 2
    dog, looter = captured["fastwalk_hunt_stops"]
    assert dog.target == "war dog"
    assert looter.target == "goblin looter"


def test_campaign_restock_policy_uses_verified_city_route(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 8})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(8, "mage", has_large_sack=True, has_food=False)

    asyncio.run(_run_policy_segment(spec.character, spec.character_profile, policy))

    assert captured == {"city_restock": True}


def test_campaign_capacity_relief_uses_verified_vault_route(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 7})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(7, "mage", needs_capacity_relief=True)

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
            vault_stow_items=("buckler", "cape"),
        )
    )

    assert captured == {
        "vault_stow_items": ("buckler", "cape"),
        "vault_required_free_weight": 10,
        "vault_only": True,
    }


def test_protected_level_eight_ambush_campaign_continues_to_the_goblin_looter(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 7, "xp": 20_000})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy_for(
                8,
                "mage",
                has_large_sack=True,
                has_sanctuary_potion=True,
            ),
        )
    )

    stops = captured["fastwalk_hunt_stops"]
    assert [stop.target for stop in stops] == ["war dog", "goblin looter"]
    exterior = ambush_exterior_hunt_stops()
    assert stops[0].route == exterior[0].route + exterior[1].route
    assert "vault_stow_items" not in captured
    assert "vault_claim_items" not in captured
    assert "vault_required_free_weight" not in captured
    assert captured["fastwalk_origin_actions"] == (
        "get all.pie",
        "eat pie",
        "drink skin",
    )
    assert captured["fastwalk_require_invisibility"] is True
    assert captured["fastwalk_train_before_departure"] is True
    assert captured["fastwalk_kill_limit"] == 2
    assert captured["require_fastwalk_kill"] is False
    assert captured["allow_safe_fastwalk_abort"] is True


def test_level_nine_ambush_campaign_uses_only_proven_war_dog(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 9, "xp": 32_000})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy_for(9, "mage", has_large_sack=True),
        )
    )

    stops = captured["fastwalk_hunt_stops"]
    assert [stop.target for stop in stops] == ["war dog"]
    assert captured["fastwalk_train_before_departure"] is True
    assert captured["fastwalk_kill_limit"] == 1


def test_level_ten_mage_campaign_reuses_bounded_moria_carrier_loop(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(
                database,
                config_path,
                {"level": 10, "xp": 40_000},
            )

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy_for(10, "mage", has_large_sack=True),
        )
    )

    assert captured["objective_level"] == 11
    assert captured["fastwalk_kill_limit"] == 1
    assert captured["require_fastwalk_kill"] is False
    assert captured["allow_safe_fastwalk_abort"] is True


def test_campaign_buys_and_uses_flight_potion_as_maintenance(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 9})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(
        9,
        "mage",
        has_large_sack=True,
        has_flight=False,
        can_attempt_flight_purchase=True,
        stalled_segments=2,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured == {
        "magic_shop_research": True,
        "magic_shop_buy_fly": True,
    }


def test_campaign_state_detects_active_flight_and_converts_coins(tmp_path) -> None:
    config_path, _ = _write_campaign_files(tmp_path)
    runner = CampaignRunner(load_campaign_spec(config_path), config_path)

    policy = runner._policy_for_state(
        {
            "level": 9,
            "inventory": [[
                {"short_desc": "a large sack"},
                {"short_desc": "a big pot pie"},
            ]],
            "affects": [[{"name": "fly", "duration": "12"}]],
            "currencies": {"silver": 17},
            "campaign_stalled_segments": 2,
        }
    )

    assert policy.policy_id == "ambush-exterior-9-10"

    less_than_an_hour_policy = runner._policy_for_state(
        {
            "level": 9,
            "inventory": [[
                {"short_desc": "a large sack"},
                {"short_desc": "a big pot pie"},
            ]],
            "affects": [[{"name": "fly", "duration": "0"}]],
            "currencies": {"silver": 17},
            "campaign_stalled_segments": 2,
        }
    )

    assert less_than_an_hour_policy.policy_id == "ambush-exterior-9-10"

    levitating_policy = runner._policy_for_state(
        {
            "level": 9,
            "inventory": [[
                {"short_desc": "a large sack"},
                {"short_desc": "a big pot pie"},
            ]],
            "affects": [[{"name": "levitation", "duration": "12"}]],
            "currencies": {"silver": 17},
            "campaign_stalled_segments": 2,
        }
    )

    assert levitating_policy.policy_id == "ambush-exterior-9-10"


def test_campaign_buys_affordable_flight_without_waiting_for_a_stall(
    tmp_path,
) -> None:
    config_path, _ = _write_campaign_files(tmp_path)
    runner = CampaignRunner(load_campaign_spec(config_path), config_path)

    policy = runner._policy_for_state(
        {
            "level": 9,
            "inventory": [[
                {"short_desc": "a large sack"},
                {"short_desc": "a big pot pie"},
            ]],
            "affects": [],
            "currencies": {"silver": 17},
            "campaign_stalled_segments": 0,
        }
    )

    assert policy.policy_id == "buy-flight-potion"


def test_level_nine_campaign_rotates_to_moria_sanctuary_hunt_after_depletion(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(
                database,
                config_path,
                {"level": 9, "xp": 33_000},
            )

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(
        9,
        "mage",
        has_large_sack=True,
        boot_kill_counts={"war dog": 16, "wounded goblin": 4},
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    stops = captured["fastwalk_hunt_stops"]
    assert {stop.target for stop in stops} == {"large hobgoblin"}
    assert captured["fastwalk_train_before_departure"] is True
    assert captured["fastwalk_require_invisibility"] is True
    assert captured["fastwalk_kill_limit"] == 1
    assert captured["require_fastwalk_kill"] is False
    assert captured["allow_safe_fastwalk_abort"] is True


def test_level_ten_thief_moria_fallback_does_not_require_mage_invisibility(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    thief = replace(
        spec.character,
        character_class="thief",
        subclass="ninja",
    )
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(
                database,
                config_path,
                {"level": 10, "xp": 47_625},
            )

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="moria-sanctuary-10-11",
        minimum_level=10,
        maximum_level=11,
        status="verified",
        execution="moria-sanctuary-hunt",
        summary="Acquire sanctuary after an empty thief rotation.",
        evidence=(),
        practice_skill="backstab",
        segment_kill_limit=1,
    )

    asyncio.run(
        _run_policy_segment(
            thief,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_require_invisibility"] is False
    assert captured["fastwalk_kill_limit"] == 1
    assert {stop.target for stop in captured["fastwalk_hunt_stops"]} == {
        "large hobgoblin"
    }


def test_level_nine_campaign_uses_potion_backed_vile_goblin_hunt(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(
                database,
                config_path,
                {"level": 9, "xp": 33_000},
            )

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(
        9,
        "mage",
        has_large_sack=True,
        has_sanctuary_potion=True,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    stops = captured["fastwalk_hunt_stops"]
    assert [stop.target for stop in stops] == ["vile goblin"]
    assert captured["fastwalk_train_before_departure"] is True
    assert captured["fastwalk_require_invisibility"] is True
    assert captured["fastwalk_kill_limit"] == 1


def test_level_ten_campaign_uses_protected_fresh_raider_hunt(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(
                database,
                config_path,
                {"level": 10, "xp": 41_169},
            )

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(
        10,
        "mage",
        has_large_sack=True,
        has_sanctuary_potion=True,
        boot_kill_counts={"goblin raider": 1, "vile goblin": 11},
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    stops = captured["fastwalk_hunt_stops"]
    assert [stop.target for stop in stops] == ["goblin raider"]
    assert stops[0].minimum_health_ratio == 0.675
    assert stops[0].exact_target is True
    assert captured["fastwalk_train_before_departure"] is True
    assert captured["fastwalk_require_invisibility"] is True
    assert captured["fastwalk_kill_limit"] == 1
    assert captured["require_fastwalk_kill"] is False
    assert captured["allow_safe_fastwalk_abort"] is True


def test_level_nine_campaign_recognizes_loose_sanctuary_potion(tmp_path) -> None:
    config_path, _ = _write_campaign_files(tmp_path)
    runner = CampaignRunner(load_campaign_spec(config_path), config_path)

    policy = runner._policy_for_state(
        {
            "level": 9,
            "inventory": [[
                {"short_desc": "a large sack"},
                {"short_desc": "a big pot pie"},
                {"short_desc": "a purple potion"},
            ]],
        }
    )

    assert policy.policy_id == "ambush-vile-goblin-9-10"


def test_campaign_liquidates_loot_in_a_safe_dedicated_segment(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 8, "xp": 25_000})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy_for(8, "mage", has_sellable_loot=True),
        )
    )

    assert captured == {"liquidate_loot": True}


def test_campaign_rearms_in_a_safe_dedicated_segment(tmp_path, monkeypatch) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 9, "xp": 32_000})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy_for(9, "mage", has_large_sack=True, has_weapon=False),
        )
    )

    assert captured == {"city_rearm": True}


def test_midennir_campaign_sack_requires_verified_invisibility(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 8, "xp": 25_000})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy_for(8, "mage"),
        )
    )

    assert captured["fastwalk_train_before_departure"] is True
    assert captured["fastwalk_require_invisibility"] is True
    assert captured["allow_safe_fastwalk_abort"] is True
    assert captured["vault_required_free_weight"] == 60
    assert captured["vault_stow_items"] == (
        "sleeves",
        "vest",
        "cape",
        "belt",
        "bracer",
        "guards",
    )
    stops = captured["fastwalk_hunt_stops"]
    assert stops[0].required_items == ("large sack",)


def test_campaign_file_runs_multiple_ready_segments(tmp_path, monkeypatch) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    calls = 0

    async def segment(spec, profile_path: Path) -> RunResult:
        nonlocal calls
        calls += 1
        return _record_segment_run(
            spec.database,
            profile_path,
            {"level": min(2, calls), "xp": calls * 100},
        )

    class TestRunner(CampaignRunner):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, segment_runner=segment, **kwargs)

    monkeypatch.setattr("dd4tester.campaign.CampaignRunner", TestRunner)

    result = asyncio.run(run_campaign_file(config_path, segments=2))

    assert result.status == "blocked"
    assert calls == 2
    with RunStorage(database) as storage:
        assert len(storage.list_campaign_segments(result.campaign_id)) == 2


def test_campaign_caps_segment_with_remaining_aggregate_budget(tmp_path) -> None:
    config_path, _database = _write_campaign_files(tmp_path, max_total_commands=7)
    requested_commands: list[int] = []

    async def starter_segment(spec, profile_path: Path) -> RunResult:
        requested_commands.append(spec.max_commands)
        return _record_segment_run(spec.database, profile_path, {"level": 2})

    asyncio.run(
        CampaignRunner(
            load_campaign_spec(config_path),
            config_path,
            segment_runner=starter_segment,
        ).run()
    )

    assert requested_commands == [7]


def test_campaign_stops_after_configured_stalled_segments(tmp_path) -> None:
    config_path, database = _write_campaign_files(tmp_path, max_stalled_segments=2)
    calls = 0

    async def starter_segment(spec, profile_path: Path) -> RunResult:
        nonlocal calls
        calls += 1
        return _record_segment_run(spec.database, profile_path, {"level": 1, "xp": 0})

    spec = load_campaign_spec(config_path)
    first = asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=starter_segment).run()
    )
    second = asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=starter_segment).run()
    )
    third = asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=starter_segment).run()
    )

    assert first.status == "blocked"
    assert second.status == "blocked"
    assert third.message == "Campaign stalled for 2 completed segment(s)."
    assert calls == 3
    with RunStorage(database) as storage:
        assert len(storage.list_campaign_segments(third.campaign_id)) == 3

    resumed = asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=starter_segment).run()
    )
    assert resumed.message == "Campaign stalled for 2 completed segment(s)."
    assert calls == 3


def test_campaign_allows_maintenance_to_clear_stall_limit(tmp_path) -> None:
    config_path, database = _write_campaign_files(tmp_path, max_stalled_segments=2)
    spec = load_campaign_spec(config_path)
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name=spec.name,
            config_path=config_path.resolve(),
            character_profile_path=spec.character_profile,
            target_level=spec.target_level,
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=None,
            run_id=None,
            phase="restock-provisions",
            reason="stalled",
            state={
                "level": 8,
                "xp": 30_000,
                "inventory": [[{"short_desc": "a buffalo water skin"}]],
                "campaign_stalled_segments": 2,
            },
        )
    calls = 0

    async def restock_segment(character, profile_path: Path) -> RunResult:
        nonlocal calls
        calls += 1
        return _record_segment_run(
            character.database,
            profile_path,
            {
                "level": 8,
                "xp": 30_000,
                "inventory": [[{"short_desc": "a big pot pie"}]],
            },
        )

    result = asyncio.run(
        CampaignRunner(
            spec,
            config_path,
            segment_runner=restock_segment,
        ).run()
    )

    assert calls == 1
    assert result.message is not None
    assert "checkpointed for the next verified segment" in result.message
    with RunStorage(database) as storage:
        checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)
        assert checkpoint is not None
        assert '"campaign_stalled_segments": 0' in checkpoint["state_json"]


def test_campaign_research_does_not_consume_stall_budget(tmp_path) -> None:
    config_path, database = _write_campaign_files(
        tmp_path,
        max_stalled_segments=1,
    )
    spec = load_campaign_spec(config_path)
    policy = ProgressionPolicy(
        policy_id="source-probe",
        minimum_level=1,
        maximum_level=2,
        status="research",
        execution="probe",
        summary="Collect bounded evidence.",
        evidence=(),
        practice_skill=None,
    )
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name=spec.name,
            config_path=config_path.resolve(),
            character_profile_path=spec.character_profile,
            target_level=spec.target_level,
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=None,
            run_id=None,
            phase="source-probe",
            reason="research-ready",
            state={
                "level": 1,
                "xp": 0,
                "campaign_stalled_segments": 1,
            },
        )

    async def research_segment(character, profile_path: Path) -> RunResult:
        return _record_segment_run(
            character.database,
            profile_path,
            {"level": 1, "xp": 0},
        )

    class ResearchRunner(CampaignRunner):
        def _policy_for_state(self, state) -> ProgressionPolicy:
            return policy

    result = asyncio.run(
        ResearchRunner(
            spec,
            config_path,
            segment_runner=research_segment,
        ).run()
    )

    assert result.message != "Campaign stalled for 1 completed segment(s)."
    with RunStorage(database) as storage:
        checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)
        assert checkpoint is not None
        assert '"campaign_stalled_segments": 0' in checkpoint["state_json"]


def test_campaign_records_a_returned_failed_segment(tmp_path) -> None:
    config_path, database = _write_campaign_files(tmp_path)

    async def failed_segment(spec, profile_path: Path) -> RunResult:
        result = _record_segment_run(spec.database, profile_path, {"level": 1})
        return RunResult(
            result.run_id,
            "failed",
            result.transcript_path,
            result.database_path,
            result.final_state,
        )

    result = asyncio.run(
        CampaignRunner(
            load_campaign_spec(config_path),
            config_path,
            segment_runner=failed_segment,
        ).run()
    )

    assert result.status == "failed"
    with RunStorage(database) as storage:
        segment = storage.list_campaign_segments(result.campaign_id)[0]
        assert segment["status"] == "failed"
        assert segment["error"] == "starter segment returned status failed"


def test_campaign_checkpoints_failed_maintenance_attempt_at_current_level(
    tmp_path,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    policy = ProgressionPolicy(
        policy_id="recover-daycare-ring",
        minimum_level=7,
        maximum_level=None,
        status="verified",
        execution="recover-daycare-ring",
        summary="Recover missing ring gear.",
        evidence=(),
        practice_skill=None,
    )
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name=spec.name,
            config_path=config_path.resolve(),
            character_profile_path=spec.character_profile,
            target_level=spec.target_level,
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=None,
            run_id=None,
            phase=policy.policy_id,
            reason="ready",
            state={
                "level": 10,
                "campaign_empty_equipment_categories": ["finger"],
            },
        )

    async def failed_segment(character, profile_path: Path) -> RunResult:
        raise RuntimeError("route watchdog")

    class MaintenanceRunner(CampaignRunner):
        def _policy_for_state(self, state) -> ProgressionPolicy:
            return policy

    result = asyncio.run(
        MaintenanceRunner(
            spec,
            config_path,
            segment_runner=failed_segment,
        ).run()
    )

    assert result.status == "failed"
    assert result.state["campaign_daycare_ring_attempted_level"] == 10
    with RunStorage(database) as storage:
        checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)
        segment = storage.list_campaign_segments(campaign_id)[0]
    assert checkpoint is not None
    assert json.loads(checkpoint["state_json"])[
        "campaign_daycare_ring_attempted_level"
    ] == 10
    assert json.loads(segment["end_state_json"])[
        "campaign_daycare_ring_attempted_level"
    ] == 10


def test_campaign_resume_migrates_legacy_failed_maintenance_checkpoint(
    tmp_path,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    runner = CampaignRunner(spec, config_path)
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name=spec.name,
            config_path=config_path.resolve(),
            character_profile_path=spec.character_profile,
            target_level=spec.target_level,
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=None,
            run_id=None,
            phase="recover-daycare-ring",
            reason="segment_failed",
            state={
                "level": 10,
                "campaign_empty_equipment_categories": ["finger"],
            },
        )
        storage.finish_campaign(
            campaign_id,
            status="failed",
            error="legacy route watchdog",
        )

        resumed_campaign_id, state = runner._open_campaign(storage)

    assert resumed_campaign_id == campaign_id
    assert state["campaign_daycare_ring_attempted_level"] == 10


def _write_campaign_files(
    tmp_path: Path,
    *,
    target_level: int = 100,
    max_total_commands: int = 10_000,
    max_stalled_segments: int = 2,
) -> tuple[Path, Path]:
    database = tmp_path / "runs.sqlite3"
    profile_path = tmp_path / "character.yaml"
    profile_path.write_text(
        "\n".join(
            [
                "name: Campaignmage",
                "password_env: TEST_PASSWORD",
                "race: human",
                "gender: female",
                "class: mage",
                f"database: '{database.as_posix()}'",
                f"transcript_dir: '{(tmp_path / 'transcripts').as_posix()}'",
            ]
        ),
        encoding="utf-8",
    )
    config_path = tmp_path / "campaign.yaml"
    config_path.write_text(
        "\n".join(
            [
                "name: Campaignmage to HERO",
                "character_profile: character.yaml",
                f"target_level: {target_level}",
                "max_segments: 10",
                "max_total_runtime: 3600",
                f"max_total_commands: {max_total_commands}",
                f"max_stalled_segments: {max_stalled_segments}",
            ]
        ),
        encoding="utf-8",
    )
    return config_path, database


def _record_segment_run(
    database: Path,
    profile_path: Path,
    final_state: dict[str, int],
) -> RunResult:
    with RunStorage(database) as storage:
        run_id = storage.create_run(
            scenario_name="starter:Campaignmage",
            scenario_path=profile_path,
        )
        storage.record_event(run_id, kind="command", payload={"command": "look"})
        storage.finish_run(run_id, status="success")
    return RunResult(
        run_id=run_id,
        status="success",
        transcript_path=Path("transcripts/campaign.jsonl"),
        database_path=database,
        final_state=final_state,
    )
