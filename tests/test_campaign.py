import asyncio
import json
from dataclasses import replace
from pathlib import Path

import pytest

from dd4tester.campaign import (
    CampaignResult,
    CampaignRunner,
    _MAINTENANCE_EXECUTIONS,
    _advance_daycare_ring_cooldown,
    _advance_intermediate_piercing_weapon_upgrade_cooldown,
    _advance_piercing_weapon_upgrade_cooldown,
    _advance_war_dog_collar_cooldown,
    _campaign_counterbalance_preparation_required,
    _campaign_below_band_policy_ids,
    _campaign_below_band_sightings,
    _campaign_has_item,
    _campaign_segment_end_state,
    _campaign_flight_purchase_failed,
    _clear_absent_research_results,
    _retry_current_absent_research_policy,
    _campaign_policy_xp_deltas,
    _campaign_liquidation_signature,
    _campaign_practice_types_spent,
    _clear_crowd_absence_marker,
    _merge_campaign_research_result,
    _merge_campaign_below_band_policy_exclusions,
    _campaign_rejected_practice_skills,
    _campaign_vault_stow_items,
    _has_campaign_food,
    _has_campaign_sellable_loot,
    _needs_piercing_weapon_upgrade,
    _maintenance_failure_state,
    _newer_progress_state,
    _latest_character_run,
    _prioritize_sack_vault_claims,
    _repair_reconciled_campaign_metadata,
    _refresh_policy_revision,
    _run_equipment_empty_categories,
    _run_primary_weapon_slot,
    _run_has_unrecovered_weapon_loss,
    _run_policy_segment,
    _run_successful_vault_lodges,
    _run_worn_equipment_descriptions,
    _state_needs_better_piercing_weapon,
    _state_needs_coin_deposit,
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


def test_coin_banking_is_campaign_maintenance() -> None:
    assert "bank-excess-coins" in _MAINTENANCE_EXECUTIONS


def test_aruncus_safe_drops_trigger_campaign_liquidation() -> None:
    catalog = GearCatalog(
        {
            302: ObjectSource(
                302,
                "plant ivy",
                "a small dusk of poison ivy",
                19,
                (1, 0, 0, 1),
                5,
            ),
            308: ObjectSource(
                308,
                "staff stick druidic",
                "a druidic staff",
                12,
                (0, 0, 0, 0),
                15,
            ),
            312: ObjectSource(
                312,
                "scroll jhyfrdow",
                "a scroll titled 'jhyfrdow'",
                2,
                (0, 0, 0, 0),
                500,
            ),
        }
    )
    state = {
        "inventory": [[
            {"quan": "3", "short_desc": "a small dusk of poison ivy"},
            {"quan": "3", "short_desc": "a druidic staff"},
            {"quan": "3", "short_desc": "a scroll titled 'jhyfrdow'"},
        ]],
        "stats": {
            "carry_num": 37,
            "maxcarry_num": 46,
            "carry_wt": 153,
            "maxcarry_wt": 300,
        },
        "campaign_liquidation_baseline": [],
    }

    assert _has_campaign_sellable_loot(state, gear_catalog=catalog) is True
    assert _campaign_liquidation_signature(
        state,
        gear_catalog=catalog,
    ) == (
        "scroll titled 'jhyfrdow'",
        "scroll titled 'jhyfrdow'",
        "scroll titled 'jhyfrdow'",
        "small dusk of poison ivy",
        "small dusk of poison ivy",
        "small dusk of poison ivy",
    )


def test_below_band_policy_exclusion_is_scoped_to_level_and_reboot() -> None:
    policy = ProgressionPolicy(
        policy_id="gnome-treasurer-thief-kill-research-13-15",
        minimum_level=13,
        maximum_level=15,
        status="verified",
        execution="gnome-treasurer-hunt",
        summary="Hunt the treasurer.",
        evidence=(),
        practice_skill=None,
    )
    state = _merge_campaign_below_band_policy_exclusions(
        {},
        {"campaign_fastwalk_below_band_targets": ["the treasurer"]},
        policy=policy,
        level=14,
        boot_id="boot-1",
    )

    assert _campaign_below_band_policy_ids(
        state,
        level=14,
        boot_id="boot-1",
    ) == frozenset({policy.policy_id})
    assert not _campaign_below_band_policy_ids(
        state,
        level=15,
        boot_id="boot-1",
    )
    assert not _campaign_below_band_policy_ids(
        state,
        level=14,
        boot_id="boot-2",
    )


def test_partial_below_band_policy_keeps_room_specific_sightings() -> None:
    policy = ProgressionPolicy(
        policy_id="mahntor-rock-toad-thief-circuit-16-18",
        minimum_level=16,
        maximum_level=18,
        status="verified",
        execution="mahntor-rock-toad-circuit",
        summary="Hunt the circuit.",
        evidence=(),
        practice_skill=None,
        allow_partial_below_band=True,
    )
    state = _merge_campaign_below_band_policy_exclusions(
        {},
        {
            "campaign_fastwalk_below_band_targets": ["rather large rock toad"],
            "campaign_fastwalk_below_band_sightings": [
                {"room_vnum": "2311", "target": "rather large rock toad"}
            ],
            "campaign_fastwalk_consider_outcomes": {
                "another source-matched target": True,
            },
        },
        policy=policy,
        level=18,
        boot_id="boot-1",
    )

    assert not _campaign_below_band_policy_ids(
        state,
        level=18,
        boot_id="boot-1",
    )
    assert _campaign_below_band_sightings(
        state,
        policy.policy_id,
        level=18,
        boot_id="boot-1",
    ) == frozenset({("2311", "rather large rock toad")})


def test_partial_below_band_policy_excludes_all_below_band_segment() -> None:
    policy = ProgressionPolicy(
        policy_id="mahntor-rock-toad-thief-circuit-16-18",
        minimum_level=16,
        maximum_level=18,
        status="verified",
        execution="mahntor-rock-toad-circuit",
        summary="Hunt the circuit.",
        evidence=(),
        practice_skill=None,
        allow_partial_below_band=True,
    )
    state = _merge_campaign_below_band_policy_exclusions(
        {},
        {
            "campaign_fastwalk_below_band_sightings": [
                {"room_vnum": "2311", "target": "rather large rock toad"}
            ],
            "campaign_fastwalk_consider_outcomes": {
                "rather large rock toad": False,
            },
        },
        policy=policy,
        level=18,
        boot_id="boot-1",
    )

    assert _campaign_below_band_policy_ids(
        state,
        level=18,
        boot_id="boot-1",
    ) == frozenset({policy.policy_id})


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


def test_maintenance_segment_preserves_known_world_boot_identity() -> None:
    merged = _campaign_segment_end_state(
        {"world_boot_id": "boot-1"},
        {"level": 16, "world_boot_id": None},
        execution="buy-flight-potion",
    )

    assert merged["world_boot_id"] == "boot-1"


def test_non_pouch_segment_preserves_audited_combat_potions() -> None:
    merged = _campaign_segment_end_state(
        {"combat_pouch_potions": {"purple": 1}},
        {"level": 14, "room_vnum": "3054"},
        execution="buy-flight-potion",
    )

    assert merged["combat_pouch_potions"] == {"purple": 1}


def test_audited_empty_pouch_can_clear_stale_combat_potions() -> None:
    merged = _campaign_segment_end_state(
        {"combat_pouch_potions": {"purple": 1}},
        {"level": 14, "combat_pouch_potions": {}},
        execution="mahntor-rock-toad-circuit",
    )

    assert merged["combat_pouch_potions"] == {}


def test_campaign_end_state_preserves_autonomy_metadata_after_runner_failure() -> None:
    previous = {
        "campaign_research_results": {
            "watchman-probe": {
                "boot_id": "boot-1",
                "observed": True,
                "viable": False,
            }
        },
        "campaign_research_absence_cooldowns": {"stag-probe": 2},
        "campaign_below_band_policy_exclusions": {
            "old-policy": {"level": 17, "boot_id": "boot-1"}
        },
        "campaign_worn_equipment": ["a long slim dagger"],
        "campaign_empty_equipment_categories": ["neck"],
        "campaign_policy_revision": 100,
    }

    merged = _campaign_segment_end_state(
        previous,
        {"level": 17, "xp": 1234, "world_boot_id": "boot-1"},
        execution="dwarven-nobleman-hunt",
    )

    assert merged["campaign_research_results"]["watchman-probe"]["viable"] is False
    assert merged["campaign_research_absence_cooldowns"] == {"stag-probe": 2}
    assert merged["campaign_below_band_policy_exclusions"]["old-policy"]
    assert merged["campaign_worn_equipment"] == ["a long slim dagger"]
    assert merged["campaign_empty_equipment_categories"] == ["neck"]


def test_repair_reconciled_campaign_metadata_uses_failed_segment_start_state(
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
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="field-hunt",
            start_state={
                "level": 17,
                "campaign_research_results": {
                    "watchman-probe": {
                        "boot_id": "boot-1",
                        "observed": True,
                        "viable": False,
                    }
                },
            },
        )
        storage.finish_campaign_segment(
            segment_id,
            status="ready",
            run_id=None,
            end_state={"level": 17},
            command_count=None,
            duration_seconds=None,
            error="legacy reconciliation",
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=segment_id,
            run_id=None,
            phase="field-hunt",
            reason="segment_failed_progress_reconciled",
            state={"level": 17},
        )
        checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)
        assert checkpoint is not None
        repaired = _repair_reconciled_campaign_metadata(
            storage,
            campaign_id,
            checkpoint,
            {"level": 17},
        )
        latest = storage.get_latest_campaign_checkpoint(campaign_id)

    assert repaired["campaign_research_results"]["watchman-probe"]["viable"] is False
    assert latest is not None
    assert latest["reason"] == "campaign_metadata_repaired"


def test_repair_reconciled_campaign_metadata_respects_later_research_clear(
    tmp_path,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    absent_result = {
        "boot_id": "boot-1",
        "observed": False,
        "viable": False,
        "absent": True,
    }
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name=spec.name,
            config_path=config_path.resolve(),
            character_profile_path=spec.character_profile,
            target_level=spec.target_level,
        )
        reconciled_segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="legacy-hunt",
            start_state={
                "level": 17,
                "campaign_research_results": {
                    "stag-probe": absent_result,
                    "watchman-probe": {
                        "boot_id": "boot-1",
                        "observed": True,
                        "viable": False,
                    },
                },
                "campaign_research_absence_cooldowns": {"stag-probe": 1},
            },
        )
        storage.finish_campaign_segment(
            reconciled_segment_id,
            status="ready",
            run_id=None,
            end_state={"level": 17},
            command_count=None,
            duration_seconds=None,
            error="legacy reconciliation",
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=reconciled_segment_id,
            run_id=None,
            phase="legacy-hunt",
            reason="segment_failed_progress_reconciled",
            state={"level": 17},
        )
        clear_segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="productive-hunt",
            start_state={
                "level": 17,
                "campaign_research_results": {"stag-probe": absent_result},
                "campaign_research_absence_cooldowns": {"stag-probe": 1},
            },
        )
        storage.finish_campaign_segment(
            clear_segment_id,
            status="success",
            run_id=None,
            end_state={"level": 17},
            command_count=None,
            duration_seconds=None,
            error=None,
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=clear_segment_id,
            run_id=None,
            phase="productive-hunt",
            reason="segment_complete",
            state={"level": 17},
        )
        checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)
        assert checkpoint is not None
        repaired = _repair_reconciled_campaign_metadata(
            storage,
            campaign_id,
            checkpoint,
            {
                "level": 17,
                "campaign_research_results": {"stag-probe": absent_result},
                "campaign_research_absence_cooldowns": {"stag-probe": 1},
            },
        )
        latest = storage.get_latest_campaign_checkpoint(campaign_id)

    assert "stag-probe" not in repaired.get("campaign_research_results", {})
    assert "stag-probe" not in repaired.get(
        "campaign_research_absence_cooldowns", {}
    )
    assert "watchman-probe" in repaired["campaign_research_results"]
    assert "stag-probe" in repaired["campaign_cleared_research_policies"]
    assert latest is not None
    assert latest["reason"] == "campaign_metadata_repaired"


def test_research_segment_persists_a_reboot_scoped_consider_outcome() -> None:
    policy = ProgressionPolicy(
        policy_id="watchman-probe",
        minimum_level=16,
        maximum_level=20,
        status="research",
        execution="mirror-realm-watchman-research",
        summary="probe",
        evidence=(),
        practice_skill=None,
    )

    merged = _merge_campaign_research_result(
        {},
        {
            "world_boot_id": "boot-1",
            "campaign_fastwalk_consider_outcomes": {"a watchman": True},
        },
        policy=policy,
    )

    assert merged["campaign_research_results"] == {
        "watchman-probe": {
            "observed": True,
            "viable": True,
            "boot_id": "boot-1",
        }
    }


def test_research_hunt_requires_a_confirmed_objective_kill() -> None:
    policy = ProgressionPolicy(
        policy_id="jailor-hunt",
        minimum_level=17,
        maximum_level=20,
        status="research",
        execution="hightower-jailor-hunt",
        summary="hunt",
        evidence=(),
        practice_skill="backstab",
    )

    merged = _merge_campaign_research_result(
        {},
        {
            "world_boot_id": "boot-1",
            "campaign_fastwalk_consider_outcomes": {"jailor": True},
            "campaign_fastwalk_abort_reason": (
                "field combat aborted for safety: health at or below 10%"
            ),
            "campaign_objective_kills": [],
        },
        policy=policy,
    )

    assert merged["campaign_research_results"]["jailor-hunt"] == {
        "observed": True,
        "viable": False,
        "completed_kill": False,
        "boot_id": "boot-1",
    }


def test_unattackable_research_target_overrides_positive_consider_evidence() -> None:
    policy = ProgressionPolicy(
        policy_id="servant-hunt",
        minimum_level=17,
        maximum_level=18,
        status="research",
        execution="dwarven-servant-hunt",
        summary="hunt",
        evidence=(),
        practice_skill="backstab",
    )

    merged = _merge_campaign_research_result(
        {},
        {
            "world_boot_id": "boot-1",
            "campaign_fastwalk_consider_outcomes": {
                "the dwarven servant": True
            },
            "campaign_fastwalk_unattackable_target": "the dwarven servant",
        },
        policy=policy,
    )

    assert merged["campaign_research_results"]["servant-hunt"] == {
        "observed": True,
        "viable": False,
        "unattackable": "the dwarven servant",
        "boot_id": "boot-1",
    }


def test_research_segment_promotes_when_any_considered_target_is_viable() -> None:
    policy = ProgressionPolicy(
        policy_id="multi-target-probe",
        minimum_level=16,
        maximum_level=20,
        status="research",
        execution="mirror-realm-watchman-research",
        summary="probe",
        evidence=(),
        practice_skill=None,
    )

    merged = _merge_campaign_research_result(
        {},
        {
            "world_boot_id": "boot-1",
            "campaign_fastwalk_consider_outcomes": {
                "first target": False,
                "second target": True,
            },
        },
        policy=policy,
    )

    assert merged["campaign_research_results"]["multi-target-probe"] == {
        "observed": True,
        "viable": True,
        "boot_id": "boot-1",
    }


def test_research_segment_records_a_missing_target_without_reusing_old_evidence() -> None:
    policy = ProgressionPolicy(
        policy_id="watchman-probe",
        minimum_level=16,
        maximum_level=20,
        status="research",
        execution="mirror-realm-watchman-research",
        summary="probe",
        evidence=(),
        practice_skill=None,
    )

    merged = _merge_campaign_research_result(
        {
            "campaign_research_results": {
                "watchman-probe": {
                    "observed": True,
                    "viable": True,
                    "boot_id": "boot-1",
                }
            }
        },
        {"world_boot_id": "boot-1"},
        policy=policy,
    )

    assert merged["campaign_research_results"]["watchman-probe"] == {
        "observed": False,
        "viable": False,
        "boot_id": "boot-1",
    }


def test_aborted_research_segment_does_not_retire_an_unobserved_target() -> None:
    policy = ProgressionPolicy(
        policy_id="soldier-probe",
        minimum_level=16,
        maximum_level=20,
        status="research",
        execution="shadow-keep-undead-soldier-research",
        summary="probe",
        evidence=(),
        practice_skill=None,
    )

    merged = _merge_campaign_research_result(
        {},
        {
            "world_boot_id": "boot-1",
            "campaign_fastwalk_abort_reason": (
                "unexpected combat interrupted a no-combat field probe"
            ),
        },
        policy=policy,
    )

    assert "campaign_research_results" not in merged


def test_absent_reset_target_replaces_stale_viability_with_temporary_marker() -> None:
    policy = ProgressionPolicy(
        policy_id="soldier-probe",
        minimum_level=16,
        maximum_level=20,
        status="research",
        execution="shadow-keep-undead-soldier-research",
        summary="probe",
        evidence=(),
        practice_skill=None,
    )

    merged = _merge_campaign_research_result(
        {
            "campaign_research_results": {
                "soldier-probe": {
                    "observed": True,
                    "viable": True,
                    "boot_id": "boot-1",
                }
            }
        },
        {
            "world_boot_id": "boot-1",
            "campaign_fastwalk_target_absent": True,
        },
        policy=policy,
    )

    assert merged["campaign_research_results"]["soldier-probe"] == {
        "observed": False,
        "viable": False,
        "absent": True,
        "boot_id": "boot-1",
    }


def test_crowded_research_result_does_not_become_absence_evidence() -> None:
    policy = ProgressionPolicy(
        policy_id="nobleman-hunt",
        minimum_level=17,
        maximum_level=18,
        status="research",
        execution="dwarven-nobleman-hunt",
        summary="hunt",
        evidence=(),
        practice_skill=None,
    )

    merged = _merge_campaign_research_result(
        {
            "campaign_research_results": {
                "nobleman-hunt": {
                    "observed": False,
                    "viable": False,
                    "absent": True,
                    "boot_id": "boot-1",
                }
            },
            "campaign_research_absence_cooldowns": {"nobleman-hunt": 3},
        },
        {
            "world_boot_id": "boot-1",
            "campaign_fastwalk_abort_reason": (
                "field room contained 4 observed mobiles while evaluating "
                "'dwarven nobleman'"
            ),
            "campaign_fastwalk_target_absent": False,
        },
        policy=policy,
    )

    assert "nobleman-hunt" not in merged.get("campaign_research_results", {})
    assert "campaign_research_absence_cooldowns" not in merged


def test_crowded_absence_migration_clears_only_the_current_policy() -> None:
    repaired = _clear_crowd_absence_marker(
        {
            "campaign_last_policy": "nobleman-hunt",
            "campaign_fastwalk_abort_reason": (
                "field room contained 4 observed mobiles while evaluating "
                "'dwarven nobleman'"
            ),
            "campaign_research_results": {
                "nobleman-hunt": {
                    "observed": False,
                    "viable": False,
                    "absent": True,
                },
                "stag-probe": {
                    "observed": False,
                    "viable": False,
                    "absent": True,
                },
            },
            "campaign_research_absence_cooldowns": {
                "nobleman-hunt": 3,
                "stag-probe": 2,
            },
        }
    )

    assert "nobleman-hunt" not in repaired["campaign_research_results"]
    assert "stag-probe" in repaired["campaign_research_results"]
    assert repaired["campaign_research_absence_cooldowns"] == {"stag-probe": 2}
    assert repaired["campaign_fastwalk_target_absent"] is False


def test_productive_work_clears_other_temporary_absence_markers() -> None:
    cleared = _clear_absent_research_results(
        {
            "campaign_research_results": {
                "soldier-probe": {
                    "observed": False,
                    "viable": False,
                    "absent": True,
                },
                "watchman-probe": {
                    "observed": True,
                    "viable": False,
                },
            }
        },
        except_policy_id="toad-hunt",
    )

    assert cleared["campaign_research_results"] == {
        "watchman-probe": {
            "observed": True,
            "viable": False,
        }
    }
    assert cleared["campaign_cleared_research_policies"] == [
        "soldier-probe"
    ]


def test_stag_absence_requires_three_productive_segments_before_retry() -> None:
    policy_id = "crystalmir-white-stag-probe-16-20"
    policy = ProgressionPolicy(
        policy_id=policy_id,
        minimum_level=16,
        maximum_level=20,
        status="research",
        execution="crystalmir-white-stag-research",
        summary="probe",
        evidence=(),
        practice_skill=None,
    )
    state = _merge_campaign_research_result(
        {},
        {
            "world_boot_id": "boot-1",
            "campaign_fastwalk_target_absent": True,
        },
        policy=policy,
    )

    assert state["campaign_research_absence_cooldowns"] == {policy_id: 3}
    for expected_remaining in (2, 1):
        state = _clear_absent_research_results(
            state,
            except_policy_id="toad-hunt",
        )
        assert policy_id in state["campaign_research_results"]
        assert state["campaign_research_absence_cooldowns"] == {
            policy_id: expected_remaining
        }

    state = _clear_absent_research_results(
        state,
        except_policy_id="toad-hunt",
    )

    assert policy_id not in state.get("campaign_research_results", {})
    assert "campaign_research_absence_cooldowns" not in state
    assert state["campaign_cleared_research_policies"] == [policy_id]


def test_shadow_hunt_absence_requires_productive_work_before_retry() -> None:
    policy_id = "shadow-keep-undead-soldier-hunt-16-20"
    policy = ProgressionPolicy(
        policy_id=policy_id,
        minimum_level=16,
        maximum_level=20,
        status="research",
        execution="shadow-keep-undead-soldier-hunt",
        summary="hunt",
        evidence=(),
        practice_skill=None,
    )
    state = _merge_campaign_research_result(
        {},
        {
            "world_boot_id": "boot-1",
            "campaign_fastwalk_target_absent": True,
        },
        policy=policy,
    )

    assert state["campaign_research_absence_cooldowns"] == {policy_id: 3}
    for _ in range(3):
        state = _clear_absent_research_results(
            state,
            except_policy_id="toad-hunt",
        )

    assert policy_id not in state.get("campaign_research_results", {})
    assert "campaign_research_absence_cooldowns" not in state
    assert state["campaign_cleared_research_policies"] == [policy_id]


def test_level_seventeen_nobleman_hunt_absence_is_temporarily_retryable() -> None:
    policy_id = "dwarven-nobleman-thief-hunt-17-18"
    policy = ProgressionPolicy(
        policy_id=policy_id,
        minimum_level=17,
        maximum_level=18,
        status="research",
        execution="dwarven-nobleman-hunt",
        summary="hunt",
        evidence=(),
        practice_skill=None,
    )

    state = _merge_campaign_research_result(
        {},
        {
            "world_boot_id": "boot-1",
            "campaign_fastwalk_target_absent": True,
        },
        policy=policy,
    )

    assert state["campaign_research_absence_cooldowns"] == {policy_id: 3}


def test_expired_absence_retry_reopens_the_current_research_policy() -> None:
    policy_id = "dwarven-nobleman-thief-hunt-17-18"
    retried = _retry_current_absent_research_policy(
        {
            "campaign_last_policy": policy_id,
            "world_boot_id": "boot-1",
            "campaign_fastwalk_target_absent": True,
            "campaign_fastwalk_abort_reason": "target absent",
            "campaign_research_results": {
                policy_id: {
                    "observed": False,
                    "viable": False,
                    "absent": True,
                    "boot_id": "boot-1",
                }
            },
            "campaign_research_absence_cooldowns": {policy_id: 1},
        }
    )

    assert policy_id not in retried.get("campaign_research_results", {})
    assert "campaign_research_absence_cooldowns" not in retried
    assert retried["campaign_fastwalk_target_absent"] is False
    assert "campaign_fastwalk_abort_reason" not in retried


def test_expired_nobleman_probe_retry_clears_its_paired_hunt_result() -> None:
    probe_id = "dwarven-nobleman-thief-probe-17-18"
    hunt_id = "dwarven-nobleman-thief-hunt-17-18"
    retried = _retry_current_absent_research_policy(
        {
            "campaign_last_policy": probe_id,
            "world_boot_id": "boot-1",
            "campaign_fastwalk_target_absent": True,
            "campaign_research_results": {
                probe_id: {
                    "observed": False,
                    "viable": False,
                    "absent": True,
                    "boot_id": "boot-1",
                },
                hunt_id: {
                    "observed": False,
                    "viable": False,
                    "absent": True,
                    "boot_id": "boot-1",
                },
            },
            "campaign_research_absence_cooldowns": {
                probe_id: 1,
                hunt_id: 1,
            },
        }
    )

    assert probe_id not in retried.get("campaign_research_results", {})
    assert hunt_id not in retried.get("campaign_research_results", {})
    assert "campaign_research_absence_cooldowns" not in retried


def test_level_twenty_one_gardener_absence_is_temporarily_retryable() -> None:
    policy_id = "mirror-realm-gardener-probe-21-25"
    policy = ProgressionPolicy(
        policy_id=policy_id,
        minimum_level=21,
        maximum_level=25,
        status="research",
        execution="mirror-realm-gardener-research",
        summary="probe",
        evidence=(),
        practice_skill=None,
    )
    state = _merge_campaign_research_result(
        {},
        {
            "world_boot_id": "boot-1",
            "campaign_fastwalk_target_absent": True,
        },
        policy=policy,
    )

    assert state["campaign_research_absence_cooldowns"] == {policy_id: 3}


def test_stag_observation_clears_an_existing_absence_cooldown() -> None:
    policy_id = "crystalmir-white-stag-probe-16-20"
    policy = ProgressionPolicy(
        policy_id=policy_id,
        minimum_level=16,
        maximum_level=20,
        status="research",
        execution="crystalmir-white-stag-research",
        summary="probe",
        evidence=(),
        practice_skill=None,
    )

    merged = _merge_campaign_research_result(
        {
            "campaign_research_absence_cooldowns": {policy_id: 2},
            "campaign_research_results": {
                policy_id: {
                    "observed": False,
                    "viable": False,
                    "absent": True,
                    "boot_id": "boot-1",
                }
            },
        },
        {
            "world_boot_id": "boot-1",
            "campaign_fastwalk_consider_outcomes": {
                "beautiful white stag": True
            },
        },
        policy=policy,
    )

    assert merged["campaign_research_results"][policy_id]["viable"] is True
    assert "campaign_research_absence_cooldowns" not in merged


def test_required_loot_segment_preserves_same_level_outfit_attempt() -> None:
    merged = _campaign_segment_end_state(
        {"campaign_outfit_attempted_level": 8},
        {"level": 8},
        execution="recover-basic-body",
    )

    assert merged["campaign_outfit_attempted_level"] == 8


def test_failed_daycare_ring_errand_gets_bounded_retry_cooldown() -> None:
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


def test_campaign_item_check_includes_newly_acquired_required_loot() -> None:
    assert _campaign_has_item(
        {
            "acquired_items": [
                {
                    "item": (
                        "silver circlet from the corpse of Uburz"
                    )
                }
            ]
        },
        "silver circlet",
    )


def test_martial_with_pink_ring_selects_one_foundry_circlet_recovery(
    tmp_path,
) -> None:
    config_path, _ = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    thief = replace(spec.character, character_class="thief", subclass="ninja")
    runner = CampaignRunner(replace(spec, character=thief), config_path)
    state = {
        "level": 14,
        "campaign_has_weapon": True,
        "campaign_empty_equipment_categories": [],
        "campaign_worn_equipment": ["a tophat", "a dagger"],
        "inventory": [[
            {"short_desc": "a big pot pie", "quan": "2"},
            {"short_desc": "[SET] a pink ice ring", "quan": "1"},
        ]],
        "stats": {
            "carry_wt": 152,
            "maxcarry_wt": 170,
        },
    }

    assert runner._policy_for_state(state).execution == (
        "recover-foundry-set-circlet"
    )
    state["campaign_foundry_set_circlet_attempted_level"] = 14
    assert runner._policy_for_state(state).execution != (
        "recover-foundry-set-circlet"
    )


def test_campaign_retries_piercing_upgrade_after_other_field_segments(
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
    state["campaign_piercing_weapon_upgrade_cooldown"] = 6
    assert runner._policy_for_state(state).policy_id == (
        "fleshmonger-thief-rotation-11-12"
    )
    runner._boot_id = 78
    assert runner._policy_for_state(state).policy_id == (
        "fleshmonger-thief-rotation-11-12"
    )
    for _ in range(6):
        state = _advance_piercing_weapon_upgrade_cooldown(
            state,
            execution="fleshmonger-thief-rotation",
            xp_delta=1,
        )
    assert runner._policy_for_state(state).execution == "upgrade-piercing-weapon"


def test_campaign_selects_intermediate_upgrade_during_forest_cooldown(
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
    intermediate = ObjectSource(
        5252,
        "long dagger slim",
        "a long slim dagger",
        5,
        (0, 2, 5, 11),
        1000,
        affects=((18, 1), (19, 1)),
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
        {
            dagger.vnum: dagger,
            intermediate.vnum: intermediate,
            claws.vnum: claws,
        }
    )
    state = {
        "level": 15,
        "campaign_has_weapon": True,
        "campaign_worn_equipment": ["a dagger"],
        "campaign_empty_equipment_categories": [],
        "inventory": [[{"quan": "1", "short_desc": "a big pot pie"}]],
        "campaign_piercing_weapon_upgrade_cooldown": 6,
    }

    assert runner._policy_for_state(state).policy_id == (
        "thalos-long-dagger-upgrade-10-29"
    )
    state["campaign_intermediate_piercing_weapon_upgrade_cooldown"] = 3
    assert runner._policy_for_state(state).execution != (
        "upgrade-piercing-weapon"
    )


def test_piercing_upgrade_cooldown_counts_productive_field_segments_only() -> None:
    state = {"campaign_piercing_weapon_upgrade_cooldown": 6}

    empty_field = _advance_piercing_weapon_upgrade_cooldown(
        state,
        execution="fleshmonger-thief-rotation",
        xp_delta=0,
    )
    productive_field = _advance_piercing_weapon_upgrade_cooldown(
        empty_field,
        execution="fleshmonger-thief-rotation",
        xp_delta=1,
    )
    maintenance = _advance_piercing_weapon_upgrade_cooldown(
        productive_field,
        execution="sell-loot",
        xp_delta=0,
    )
    own_attempt = _advance_piercing_weapon_upgrade_cooldown(
        maintenance,
        execution="upgrade-piercing-weapon",
        xp_delta=0,
    )

    assert empty_field["campaign_piercing_weapon_upgrade_cooldown"] == 6
    assert productive_field["campaign_piercing_weapon_upgrade_cooldown"] == 5
    assert maintenance["campaign_piercing_weapon_upgrade_cooldown"] == 5
    assert own_attempt["campaign_piercing_weapon_upgrade_cooldown"] == 5


def test_intermediate_upgrade_has_independent_productive_cooldown() -> None:
    state = {"campaign_intermediate_piercing_weapon_upgrade_cooldown": 3}

    for _ in range(3):
        state = _advance_intermediate_piercing_weapon_upgrade_cooldown(
            state,
            execution="mahntor-rock-toad-hunt",
            xp_delta=1,
        )

    assert state["campaign_intermediate_piercing_weapon_upgrade_cooldown"] == 0


def test_policy_refresh_discards_nonobservations_but_preserves_absence() -> None:
    refreshed = _refresh_policy_revision(
        {
            "campaign_policy_revision": 100,
            "campaign_research_results": {
                "aborted-probe": {
                    "observed": False,
                    "viable": False,
                    "boot_id": "boot-1",
                },
                "absent-probe": {
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
                "observed-probe": {
                    "observed": True,
                    "viable": False,
                    "boot_id": "boot-1",
                },
            },
        }
    )

    assert "aborted-probe" not in refreshed["campaign_research_results"]
    assert "absent-probe" in refreshed["campaign_research_results"]
    assert "observed-probe" in refreshed["campaign_research_results"]
    assert refreshed["campaign_research_absence_cooldowns"] == {
        "shadow-keep-undead-soldier-probe-16-20": 3
    }


def test_policy_revision_retries_expanded_thalos_search_once() -> None:
    migrated = _refresh_policy_revision(
        {
            "level": 15,
            "campaign_policy_revision": 92,
            "campaign_intermediate_piercing_weapon_upgrade_cooldown": 3,
        }
    )

    assert migrated["campaign_policy_revision"] == 110
    assert (
        "campaign_intermediate_piercing_weapon_upgrade_cooldown"
        not in migrated
    )


def test_policy_revision_extends_active_forest_upgrade_cooldown() -> None:
    migrated = _refresh_policy_revision(
        {
            "level": 15,
            "campaign_policy_revision": 93,
            "campaign_piercing_weapon_upgrade_cooldown": 3,
        }
    )

    assert migrated["campaign_policy_revision"] == 110
    assert migrated["campaign_piercing_weapon_upgrade_cooldown"] == 6


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
    assert migrated["campaign_policy_revision"] == 110
    assert "campaign_piercing_weapon_upgrade_attempted_boot_id" not in migrated
    assert "campaign_piercing_weapon_upgrade_cooldown" not in migrated


def test_policy_revision_retries_bear_claws_after_trivial_route_fix() -> None:
    migrated = _refresh_policy_revision(
        {
            "level": 13,
            "campaign_policy_revision": 84,
            "campaign_last_policy": "fleshmonger-thief-rotation-12-13",
            "campaign_fastwalk_abort_reason": None,
            "campaign_piercing_weapon_upgrade_attempted_boot_id": "boot-1",
            "campaign_piercing_weapon_upgrade_cooldown": 2,
        }
    )

    assert migrated["campaign_policy_revision"] == 110
    assert "campaign_piercing_weapon_upgrade_attempted_boot_id" not in migrated
    assert "campaign_piercing_weapon_upgrade_cooldown" not in migrated


def test_policy_revision_retires_false_trainer_cap_gear_markers() -> None:
    migrated = _refresh_policy_revision(
        {
            "level": 14,
            "campaign_policy_revision": 86,
            "campaign_training_cap_gear_attempted_level": 14,
            "campaign_training_cap_gear_recovered_level": 14,
        }
    )

    assert migrated["campaign_policy_revision"] == 110
    assert "campaign_training_cap_gear_attempted_level" not in migrated
    assert "campaign_training_cap_gear_recovered_level" not in migrated


def test_policy_revision_retries_worker_probe_with_complete_safe_search() -> None:
    migrated = _refresh_policy_revision(
        {
            "level": 14,
            "campaign_policy_revision": 90,
            "campaign_last_policy": "dwarven-workers-thief-probe-13-15",
            "campaign_research_results": {
                "dwarven-workers-thief-probe-13-15": {
                    "observed": False,
                    "viable": False,
                }
            },
        }
    )

    assert migrated["campaign_policy_revision"] == 110
    assert migrated["campaign_fastwalk_abort_reason"] == (
        "policy revision bound the worker survey to its exact source room line"
    )


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


def test_policy_revision_retries_bardoosh_after_final_route_fix() -> None:
    migrated = _refresh_policy_revision(
        {
            "level": 13,
            "campaign_policy_revision": 77,
            "campaign_last_policy": "ambush-bardoosh-thief-kill-research-13",
            "campaign_fastwalk_abort_reason": None,
            "campaign_research_results": {
                "ambush-bardoosh-thief-kill-research-13": {
                    "observed": False,
                    "viable": False,
                }
            },
        }
    )

    assert migrated["campaign_policy_revision"] == 110
    assert migrated["campaign_fastwalk_abort_reason"] == (
        "policy revision corrected the Bardoosh final route from south to west"
    )
    assert _refresh_policy_revision(migrated) is migrated


def test_policy_revision_retries_bardoosh_after_identity_fix() -> None:
    migrated = _refresh_policy_revision(
        {
            "level": 13,
            "campaign_policy_revision": 78,
            "campaign_last_policy": "ambush-bardoosh-thief-kill-research-13",
            "campaign_research_results": {
                "ambush-bardoosh-thief-kill-research-13": {
                    "observed": False,
                    "viable": False,
                }
            },
        }
    )

    assert migrated["campaign_policy_revision"] == 110
    assert migrated["campaign_fastwalk_abort_reason"] == (
        "policy revision bound Bardoosh's generic live line to his source identity"
    )


def test_policy_revision_clears_consumed_bardoosh_retry_reason() -> None:
    migrated = _refresh_policy_revision(
        {
            "level": 13,
            "campaign_policy_revision": 79,
            "campaign_last_policy": "ambush-bardoosh-thief-kill-research-13",
            "campaign_fastwalk_abort_reason": (
                "policy revision bound Bardoosh's generic live line to his "
                "source identity"
            ),
            "campaign_research_results": {
                "ambush-bardoosh-thief-kill-research-13": {
                    "observed": True,
                    "viable": True,
                }
            },
        }
    )

    assert migrated["campaign_policy_revision"] == 110
    assert "campaign_fastwalk_abort_reason" not in migrated


def test_policy_revision_does_not_rearm_retry_after_recorded_bardoosh_attempt() -> None:
    policy_id = "ambush-bardoosh-thief-kill-research-13"
    migrated = _refresh_policy_revision(
        {
            "level": 13,
            "campaign_last_policy": policy_id,
        },
        completed_policy_ids={policy_id},
    )

    assert migrated["campaign_policy_revision"] == 110
    assert "campaign_fastwalk_abort_reason" not in migrated


def test_policy_revision_retries_nobleman_after_redundant_destination_fix() -> None:
    policy_id = "dwarven-nobleman-thief-probe-13-15"
    migrated = _refresh_policy_revision(
        {
            "level": 13,
            "campaign_policy_revision": 80,
            "campaign_last_policy": "plains-aruncus-thief-hunt-13-15",
            "campaign_research_results": {
                policy_id: {
                    "observed": False,
                    "viable": False,
                }
            },
        },
        completed_policy_ids={policy_id},
    )

    assert migrated["campaign_policy_revision"] == 110
    assert migrated["campaign_fastwalk_abort_reason"] == (
        "policy revision removed the redundant nobleman destination hop"
    )


def test_policy_revision_retries_nobleman_after_exact_identity_fix() -> None:
    policy_id = "dwarven-nobleman-thief-probe-13-15"
    migrated = _refresh_policy_revision(
        {
            "level": 13,
            "campaign_policy_revision": 81,
            "campaign_last_policy": policy_id,
            "campaign_research_results": {
                policy_id: {
                    "observed": False,
                    "viable": False,
                }
            },
        },
        completed_policy_ids={policy_id},
    )

    assert migrated["campaign_policy_revision"] == 110
    assert migrated["campaign_fastwalk_abort_reason"] == (
        "policy revision aligned the nobleman stop with its source identity"
    )


def test_policy_revision_retries_watchman_after_endpoint_route_fix() -> None:
    policy_id = "mirror-realm-watchman-probe-16-20"
    migrated = _refresh_policy_revision(
        {
            "level": 16,
            "campaign_policy_revision": 95,
            "campaign_last_policy": policy_id,
            "campaign_research_results": {
                policy_id: {
                    "boot_id": "boot-1",
                    "observed": False,
                    "viable": False,
                },
                "other-policy": {
                    "boot_id": "boot-1",
                    "observed": True,
                    "viable": True,
                },
            },
        },
        completed_policy_ids={policy_id},
    )

    assert migrated["campaign_policy_revision"] == 110
    assert policy_id not in migrated["campaign_research_results"]
    assert migrated["campaign_research_results"]["other-policy"]["viable"] is True


def test_policy_revision_retries_absent_shadow_keep_reset_target() -> None:
    policy_id = "shadow-keep-undead-soldier-probe-16-20"
    migrated = _refresh_policy_revision(
        {
            "level": 16,
            "campaign_policy_revision": 96,
            "campaign_last_policy": policy_id,
            "campaign_research_results": {
                policy_id: {
                    "boot_id": "boot-1",
                    "observed": False,
                    "viable": False,
                },
                "other-policy": {
                    "boot_id": "boot-1",
                    "observed": True,
                    "viable": False,
                },
            },
        }
    )

    assert migrated["campaign_policy_revision"] == 110
    assert policy_id not in migrated["campaign_research_results"]
    assert migrated["campaign_research_results"]["other-policy"]["observed"] is True


def test_policy_revision_retries_nonviable_watchman_after_second_stop_added() -> None:
    policy_id = "mirror-realm-watchman-probe-16-20"
    migrated = _refresh_policy_revision(
        {
            "level": 16,
            "campaign_policy_revision": 98,
            "campaign_research_results": {
                policy_id: {
                    "boot_id": "boot-1",
                    "observed": True,
                    "viable": False,
                }
            },
        }
    )

    assert migrated["campaign_policy_revision"] == 110
    assert policy_id not in migrated.get("campaign_research_results", {})


def test_policy_revision_delays_retry_of_existing_absent_stag() -> None:
    policy_id = "crystalmir-white-stag-probe-16-20"
    migrated = _refresh_policy_revision(
        {
            "level": 16,
            "campaign_policy_revision": 99,
            "campaign_research_results": {
                policy_id: {
                    "boot_id": "boot-1",
                    "observed": False,
                    "viable": False,
                    "absent": True,
                }
            },
        }
    )

    assert migrated["campaign_policy_revision"] == 110
    assert migrated["campaign_research_absence_cooldowns"] == {
        policy_id: 3
    }


def test_policy_revision_retries_pyramid_after_redundant_extended_route_stop() -> None:
    policy_id = "pyramid-ali-baba-probe-18-20"
    migrated = _refresh_policy_revision(
        {
            "level": 18,
            "campaign_policy_revision": 109,
            "campaign_last_policy": policy_id,
            "campaign_fastwalk_target_absent": True,
            "campaign_fastwalk_abort_reason": "old Pyramid route abort",
            "campaign_research_results": {
                policy_id: {
                    "boot_id": "boot-1",
                    "observed": False,
                    "viable": False,
                    "absent": True,
                },
                "other-policy": {
                    "boot_id": "boot-1",
                    "observed": True,
                    "viable": True,
                },
            },
            "campaign_research_absence_cooldowns": {policy_id: 3},
        }
    )

    assert migrated["campaign_policy_revision"] == 110
    assert policy_id not in migrated["campaign_research_results"]
    assert migrated["campaign_research_results"]["other-policy"]["viable"] is True
    assert policy_id not in migrated.get("campaign_research_absence_cooldowns", {})
    assert "campaign_fastwalk_target_absent" not in migrated
    assert "campaign_fastwalk_abort_reason" not in migrated


def test_policy_revision_retries_jailor_after_mixed_route_fix() -> None:
    migrated = _refresh_policy_revision(
        {
            "campaign_policy_revision": 100,
            "campaign_last_policy": "hightower-jailor-probe-17-20",
            "campaign_fastwalk_target_absent": True,
            "campaign_research_results": {
                "hightower-jailor-probe-17-20": {
                    "observed": False,
                    "viable": False,
                    "absent": True,
                },
                "hightower-jailor-hunt-17-20": {
                    "observed": True,
                    "viable": False,
                },
                "stag-probe": {
                    "observed": False,
                    "viable": False,
                    "absent": True,
                },
            },
            "campaign_research_absence_cooldowns": {
                "hightower-jailor-probe-17-20": 3,
                "hightower-jailor-hunt-17-20": 3,
                "stag-probe": 2,
            },
        }
    )

    assert migrated["campaign_policy_revision"] == 110
    assert "hightower-jailor-probe-17-20" not in migrated[
        "campaign_research_results"
    ]
    assert "hightower-jailor-hunt-17-20" not in migrated[
        "campaign_research_results"
    ]
    assert migrated["campaign_research_results"]["stag-probe"]["absent"] is True
    assert migrated["campaign_research_absence_cooldowns"] == {"stag-probe": 2}
    assert migrated["campaign_cleared_research_policies"] == [
        "hightower-jailor-hunt-17-20",
        "hightower-jailor-probe-17-20",
    ]
    assert "campaign_fastwalk_target_absent" not in migrated


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


def test_replayed_research_result_clears_only_its_migration_tombstone() -> None:
    policy = ProgressionPolicy(
        policy_id="hightower-jailor-probe-17-20",
        minimum_level=17,
        maximum_level=20,
        status="research",
        execution="hightower-jailor-research",
        summary="Probe the Jailor.",
        evidence=(),
        practice_skill=None,
    )

    merged = _merge_campaign_research_result(
        {
            "campaign_cleared_research_policies": [
                "hightower-jailor-hunt-17-20",
                "hightower-jailor-probe-17-20",
            ],
        },
        {
            "world_boot_id": "boot-1",
            "campaign_fastwalk_consider_outcomes": {"the jailor": True},
        },
        policy=policy,
    )

    assert merged["campaign_research_results"][policy.policy_id]["viable"] is True
    assert merged["campaign_cleared_research_policies"] == [
        "hightower-jailor-hunt-17-20"
    ]


def test_current_revision_repairs_unfinished_jailor_absence_migration() -> None:
    repaired = _refresh_policy_revision(
        {
            "campaign_policy_revision": 110,
            "campaign_last_policy": "hightower-jailor-probe-17-20",
            "campaign_fastwalk_target_absent": True,
            "campaign_research_results": {
                "hightower-jailor-probe-17-20": {
                    "observed": False,
                    "viable": False,
                    "absent": True,
                },
                "other-policy": {
                    "observed": True,
                    "viable": False,
                },
            },
            "campaign_research_absence_cooldowns": {
                "hightower-jailor-probe-17-20": 3,
                "other-policy": 2,
            },
        }
    )

    assert repaired["campaign_policy_revision"] == 110
    assert "hightower-jailor-probe-17-20" not in repaired[
        "campaign_research_results"
    ]
    assert repaired["campaign_research_results"]["other-policy"]["viable"] is False
    assert repaired["campaign_research_absence_cooldowns"] == {
        "other-policy": 2
    }
    assert repaired["campaign_cleared_research_policies"] == [
        "hightower-jailor-hunt-17-20",
        "hightower-jailor-probe-17-20",
    ]
    assert "campaign_fastwalk_target_absent" not in repaired


def test_current_revision_repairs_a_failed_jailor_hunt_promotion() -> None:
    repaired = _refresh_policy_revision(
        {
            "campaign_policy_revision": 110,
            "campaign_last_policy": "hightower-jailor-hunt-17-20",
            "campaign_fastwalk_abort_reason": (
                "field combat aborted for safety: health at or below 10%"
            ),
            "campaign_objective_kills": [],
            "campaign_research_results": {
                "hightower-jailor-hunt-17-20": {
                    "observed": True,
                    "viable": True,
                    "boot_id": "boot-1",
                }
            },
        }
    )

    assert repaired["campaign_research_results"][
        "hightower-jailor-hunt-17-20"
    ] == {
        "observed": True,
        "viable": False,
        "completed_kill": False,
        "boot_id": "boot-1",
    }


def test_policy_revision_retries_shire_prince_after_identity_fix() -> None:
    migrated = _refresh_policy_revision(
        {
            "campaign_policy_revision": 104,
            "campaign_last_policy": "shire-dwarven-prince-thief-probe-17-20",
            "campaign_fastwalk_target_absent": True,
            "campaign_research_results": {
                "shire-dwarven-prince-thief-probe-17-20": {
                    "observed": False,
                    "viable": False,
                    "absent": True,
                    "boot_id": "boot-1",
                },
                "shire-dwarven-prince-thief-hunt-17-20": {
                    "observed": False,
                    "viable": False,
                    "absent": True,
                    "boot_id": "boot-1",
                },
                "other-policy": {"observed": True, "viable": False},
            },
            "campaign_research_absence_cooldowns": {
                "shire-dwarven-prince-thief-probe-17-20": 3,
                "shire-dwarven-prince-thief-hunt-17-20": 3,
                "other-policy": 2,
            },
        }
    )

    assert migrated["campaign_policy_revision"] == 110
    assert "shire-dwarven-prince-thief-probe-17-20" not in migrated[
        "campaign_research_results"
    ]
    assert "shire-dwarven-prince-thief-hunt-17-20" not in migrated[
        "campaign_research_results"
    ]
    assert migrated["campaign_research_absence_cooldowns"] == {
        "other-policy": 2
    }
    assert "campaign_fastwalk_target_absent" not in migrated
    assert _refresh_policy_revision(migrated) is migrated


def test_policy_revision_clears_crowded_shire_prince_promotion() -> None:
    migrated = _refresh_policy_revision(
        {
            "campaign_policy_revision": 105,
            "campaign_last_policy": "shire-dwarven-prince-thief-probe-17-20",
            "campaign_fastwalk_consider_outcomes": {
                "dwarven prince": True,
                "other target": False,
            },
            "campaign_research_results": {
                "shire-dwarven-prince-thief-probe-17-20": {
                    "observed": True,
                    "viable": True,
                    "boot_id": "boot-1",
                },
                "other-policy": {"observed": True, "viable": False},
            },
        }
    )

    assert migrated["campaign_policy_revision"] == 110
    assert "shire-dwarven-prince-thief-probe-17-20" not in migrated[
        "campaign_research_results"
    ]
    assert migrated["campaign_research_results"]["other-policy"]
    assert migrated["campaign_fastwalk_consider_outcomes"] == {
        "other target": False
    }
    assert _refresh_policy_revision(migrated) is migrated


def test_policy_revision_clears_stale_mahntor_route_abort() -> None:
    migrated = _refresh_policy_revision(
        {
            "campaign_policy_revision": 102,
            "campaign_last_policy": "mahntor-rock-toad-thief-circuit-16-18",
            "campaign_fastwalk_abort_reason": (
                "field route could not find GMCP exit to room 2311"
            ),
        }
    )

    assert migrated["campaign_policy_revision"] == 110
    assert "campaign_fastwalk_abort_reason" not in migrated


def test_policy_revision_removes_anonymous_mahntor_below_band_exclusion() -> None:
    policy_id = "mahntor-rock-toad-thief-circuit-16-18"
    migrated = _refresh_policy_revision(
        {
            "campaign_policy_revision": 103,
            "campaign_last_policy": policy_id,
            "campaign_below_band_policy_exclusions": {
                policy_id: {
                    "level": 18,
                    "boot_id": "boot-1",
                    "targets": ["rather large rock toad"],
                }
            },
        }
    )

    assert migrated["campaign_policy_revision"] == 110
    assert policy_id not in migrated.get(
        "campaign_below_band_policy_exclusions", {}
    )


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


def test_campaign_policy_xp_deltas_records_runtime_capped_no_kill_attempt(
    tmp_path,
) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="outcomes",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=100,
        )
        run_id = storage.create_run(
            scenario_name="field-hunt",
            scenario_path=tmp_path / "character.yaml",
        )
        storage.record_event(
            run_id,
            kind="state",
            payload={
                "state": "runtime_cap",
                "completed_kills": [],
                "objective_kills": [],
            },
        )
        storage.finish_run(
            run_id,
            status="ready",
            error="Starter bot exceeded 300 second runtime",
        )
        segment = storage.start_campaign_segment(
            campaign_id,
            phase="ambush-bardoosh-thief-kill-research-13",
            start_state={"level": 13, "xp": 75_979},
        )
        storage.finish_campaign_segment(
            segment,
            status="ready",
            run_id=run_id,
            end_state={
                "level": 13,
                "xp": 76_104,
            },
            command_count=38,
            duration_seconds=300.0,
            error="Starter bot exceeded 300 second runtime",
        )

        results = _campaign_policy_xp_deltas(
            storage.list_campaign_segments(campaign_id),
            storage=storage,
        )

    assert results == {"ambush-bardoosh-thief-kill-research-13": 0}


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


def test_latest_character_run_prefers_newer_maintenance_evidence(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        storage.create_run(
            scenario_name="fastwalk-ambush:Kestrel",
            scenario_path=tmp_path / "character.yaml",
        )
        latest_id = storage.create_run(
            scenario_name="rearm:Kestrel",
            scenario_path=tmp_path / "character.yaml",
        )
        storage.create_run(
            scenario_name="rearm:Dorrik",
            scenario_path=tmp_path / "other.yaml",
        )

        latest = _latest_character_run(storage, "Kestrel")

    assert latest is not None
    assert int(latest["id"]) == latest_id


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


def test_campaign_liquidates_carried_collars_after_worn_slots_are_filled() -> None:
    state = {
        "inventory": [[{"quan": "2", "short_desc": "a war dog collar"}]],
        "campaign_worn_equipment": [
            "a war dog collar",
            "a war dog collar",
        ],
        "stats": {"carry_wt": 161, "maxcarry_wt": 170},
    }

    assert _has_campaign_sellable_loot(state) is True

    state["campaign_worn_equipment"] = []
    assert _has_campaign_sellable_loot(state) is False


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


def test_campaign_recognizes_selector_prefixed_no_drop_amulet_as_loot() -> None:
    amulet = ObjectSource(
        307,
        "amulet",
        "a strange amulet",
        9,
        (2, 0, 0, 0),
        300,
        wear_flags=1 | (1 << 2),
        extra_flags=192,
        affects=((21, 5),),
    )
    state = {
        "inventory": (
            '[[{"quan":"1","short_desc":"[#24943] a strange amulet"},'
            '{"quan":"3","short_desc":"a big pot pie"}]]'
        ),
        "campaign_liquidation_baseline": [],
        "stats": {"carry_wt": 150, "maxcarry_wt": 250},
    }

    assert _has_campaign_sellable_loot(
        state,
        gear_catalog=GearCatalog({amulet.vnum: amulet}),
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

    assert result.status == "ready"
    assert result.state["level"] == 2
    assert "checkpointed for the next verified segment" in result.message
    assert calls == [250]

    with RunStorage(database) as storage:
        campaign = storage.get_campaign(result.campaign_id)
        segments = storage.list_campaign_segments(result.campaign_id)
        checkpoint = storage.get_latest_campaign_checkpoint(result.campaign_id)

    assert campaign["status"] == "ready"
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
    assert resumed.status == "ready"
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


def test_plains_aruncus_research_dispatch_never_initiates_combat(
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
            return _record_segment_run(database, config_path, {"level": 13})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="plains-aruncus-probe-13-15",
        minimum_level=13,
        maximum_level=15,
        status="research",
        execution="plains-aruncus-research",
        summary="Bounded live-consider research route.",
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

    assert captured["fastwalk_route"].name == "plains aruncus"
    assert captured["fastwalk_route"].recall_after_loot is True
    stops = captured["fastwalk_hunt_stops"]
    assert [stop.target for stop in stops] == ["Aruncus the Druid"] * 85
    assert [stop.route_vnums for stop in stops[1:]][:10] == [
        ("330",), (), (), ("319",), ("318",),
        ("316",), ("300",), ("301",), ("302",), ("303",),
    ]
    assert stops[2].route == ("open west", "west")
    assert stops[3].route == ("open east", "east")
    assert [stop.route_vnums for stop in stops[1:]][-4:] == [
        ("341",), ("340",), ("342",), ("343",),
    ]
    assert stops[0].actions == ("where aruncus",)
    assert all(stop.command_keyword == "aruncus" for stop in stops)
    assert all(stop.consider_only for stop in stops)
    assert captured["require_fastwalk_kill"] is False


def test_dwarven_nobleman_research_dispatch_never_initiates_combat(
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
            return _record_segment_run(database, config_path, {"level": 13})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="dwarven-nobleman-thief-probe-13-15",
        minimum_level=13,
        maximum_level=15,
        status="research",
        execution="dwarven-nobleman-research",
        summary="Source-backed no-combat probe.",
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

    assert captured["fastwalk_route"].name == "dwarven nobleman"
    assert captured["fastwalk_route"].recall_after_loot is True
    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.target == "dwarven nobleman"
    assert stop.consider_only is True
    assert captured["require_fastwalk_kill"] is False


def test_mahntor_rock_toad_research_dispatch_surveys_four_rooms_without_combat(
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
            return _record_segment_run(database, config_path, {"level": 14})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="mahntor-rock-toad-thief-probe-14-15",
        minimum_level=14,
        maximum_level=15,
        status="research",
        execution="mahntor-rock-toad-research",
        summary="Source-backed four-room no-combat survey.",
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

    assert captured["fastwalk_route"].name == "mahn tor rock toads"
    assert captured["fastwalk_route"].recall_after_loot is True
    stops = captured["fastwalk_hunt_stops"]
    assert len(stops) == 4
    assert all(stop.target == "rather large rock toad" for stop in stops)
    assert all(stop.consider_only for stop in stops)
    assert captured["fastwalk_kill_limit"] is None
    assert captured["require_fastwalk_kill"] is False


def test_mahntor_rock_toad_hunt_dispatch_is_bounded_to_one_kill(
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
            return _record_segment_run(database, config_path, {"level": 14})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="mahntor-rock-toad-thief-kill-research-14-15",
        minimum_level=14,
        maximum_level=15,
        status="research",
        execution="mahntor-rock-toad-hunt",
        summary="One bounded source-backed combat probe.",
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

    assert captured["fastwalk_route"].name == "mahn tor rock toads"
    assert captured["fastwalk_kill_limit"] == 1
    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.target == "rather large rock toad"
    assert stop.consider_only is False
    assert stop.maximum_level_offset == 1
    assert captured["require_fastwalk_kill"] is False


def test_mahntor_rock_toad_circuit_dispatch_uses_all_rooms_and_three_kill_cap(
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
            return _record_segment_run(database, config_path, {"level": 14})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="mahntor-rock-toad-thief-circuit-14-15",
        minimum_level=14,
        maximum_level=15,
        status="verified",
        execution="mahntor-rock-toad-circuit",
        summary="Three-kill source-backed circuit.",
        evidence=(),
        practice_skill="backstab",
        segment_kill_limit=3,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_route"].name == "mahn tor rock toads"
    assert captured["fastwalk_kill_limit"] == 3
    stops = captured["fastwalk_hunt_stops"]
    assert len(stops) == 4
    assert all(stop.target == "rather large rock toad" for stop in stops)
    assert all(stop.consider_only is False for stop in stops)
    assert captured["require_fastwalk_kill"] is False


def test_dwarven_nobleman_hunt_dispatch_is_bounded_to_one_kill(
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
            return _record_segment_run(database, config_path, {"level": 13})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="dwarven-nobleman-thief-kill-research-13-15",
        minimum_level=13,
        maximum_level=15,
        status="research",
        execution="dwarven-nobleman-hunt",
        summary="Bounded combat research.",
        evidence=(),
        practice_skill=None,
        segment_kill_limit=1,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.consider_only is False
    assert stop.maximum_level_offset == 1
    assert captured["fastwalk_kill_limit"] == 1
    assert captured["require_fastwalk_kill"] is False


@pytest.mark.parametrize(
    ("execution", "consider_only", "kill_limit"),
    (
        ("shire-thain-research", True, None),
        ("shire-thain-hunt", False, 1),
    ),
)
def test_shire_thain_dispatch_keeps_probe_and_hunt_bounded(
    tmp_path,
    monkeypatch,
    execution: str,
    consider_only: bool,
    kill_limit: int | None,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 17})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id=execution,
        minimum_level=17,
        maximum_level=20,
        status="research",
        execution=execution,
        summary="Bounded Thain research.",
        evidence=(),
        practice_skill="backstab",
        segment_kill_limit=kill_limit,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    route = captured["fastwalk_route"]
    assert route.name == "shire thain"
    assert route.commands == (
        "south", "south", "west", "west", "west", "west", "west",
        "north", "north", "north", "north", "east", "east", "east",
        "east", "east",
    )
    assert route.recall_after_loot is True
    assert captured["fastwalk_kill_limit"] == kill_limit
    stops = captured["fastwalk_hunt_stops"]
    assert len(stops) == 92
    assert stops[0].target == "the Thain"
    assert stops[0].actions == ("where thain",)
    assert stops[0].abort_if_where_target_absent is True
    assert stops[0].consider_only is consider_only
    assert all(stop.consider_only is consider_only for stop in stops)
    assert all(stop.exact_target is True for stop in stops)
    assert all(stop.maximum_level_offset == 0 for stop in stops)
    assert captured["require_fastwalk_kill"] is False


def test_shire_elven_wizard_dispatches_research_only(
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
            return _record_segment_run(database, config_path, {"level": 18})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="shire-elven-wizard-probe-17-20",
        minimum_level=17,
        maximum_level=20,
        status="research",
        execution="shire-elven-wizard-research",
        summary="Bounded wizard research.",
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

    route = captured["fastwalk_route"]
    assert route.name == "shire elven wizard"
    assert route.recall_after_loot is True
    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.target == "elven wizard"
    assert stop.command_keyword == "wizard"
    assert stop.trivial_bystanders == ("halfling beauty",)
    assert stop.consider_only is True
    assert captured.get("fastwalk_kill_limit") is None
    assert captured["require_fastwalk_kill"] is False


def test_shire_elven_wizard_dispatches_one_bounded_hunt(
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
            return _record_segment_run(database, config_path, {"level": 18})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="shire-elven-wizard-hunt-17-20",
        minimum_level=17,
        maximum_level=20,
        status="research",
        execution="shire-elven-wizard-hunt",
        summary="Bounded wizard hunt.",
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

    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.consider_only is False
    assert stop.minimum_health_ratio == 0.95
    assert stop.maximum_level_offset == 1
    assert captured["fastwalk_kill_limit"] == 1
    assert captured["require_fastwalk_kill"] is False


def test_pyramid_ali_baba_dispatches_research_and_bounded_hunt(
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
            return _record_segment_run(database, config_path, {"level": 18})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)

    for execution, consider_only in (
        ("pyramid-ali-baba-research", True),
        ("pyramid-ali-baba-hunt", False),
    ):
        captured.clear()
        policy = ProgressionPolicy(
            policy_id=(
                "pyramid-ali-baba-probe-18-20"
                if consider_only
                else "pyramid-ali-baba-hunt-18-20"
            ),
            minimum_level=18,
            maximum_level=20,
            status="research",
            execution=execution,
            summary="Source-backed Pyramid policy.",
            evidence=(),
            practice_skill="backstab" if not consider_only else None,
            segment_kill_limit=None if consider_only else 1,
        )

        asyncio.run(
            _run_policy_segment(
                spec.character,
                spec.character_profile,
                policy,
            )
        )

        route = captured["fastwalk_route"]
        assert route.name == "pyramid ali baba"
        stops = captured["fastwalk_hunt_stops"]
        assert len(stops) == 9
        for stop in stops:
            assert stop.target == "Ali Baba"
            assert stop.command_keyword == "ali baba"
            assert stop.consider_only is consider_only
            assert stop.exact_target is True
            assert stop.require_isolated is True
        assert captured["require_fastwalk_kill"] is False
        assert captured.get("fastwalk_kill_limit") == (
            None if consider_only else 1
        )


def test_gnome_treasurer_research_collects_coins_without_target_combat(
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
            return _record_segment_run(database, config_path, {"level": 13})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="gnome-treasurer-thief-probe-13-15",
        minimum_level=13,
        maximum_level=15,
        status="research",
        execution="gnome-treasurer-research",
        summary="Source-backed no-combat money probe.",
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

    assert captured["fastwalk_route"].name == "gnome treasury"
    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.actions == ("get all.coins",)
    assert stop.consider_only is True
    assert captured["require_fastwalk_kill"] is False


def test_gnome_treasurer_hunt_dispatch_is_bounded_to_one_kill(
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
            return _record_segment_run(database, config_path, {"level": 13})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="gnome-treasurer-thief-kill-research-13-15",
        minimum_level=13,
        maximum_level=15,
        status="research",
        execution="gnome-treasurer-hunt",
        summary="Bounded combat research.",
        evidence=(),
        practice_skill=None,
        segment_kill_limit=1,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.consider_only is False
    assert stop.maximum_level_offset == 1
    assert captured["fastwalk_kill_limit"] == 1
    assert captured["require_fastwalk_kill"] is False


def test_mirror_realm_watchman_research_dispatch_never_initiates_combat(
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
            return _record_segment_run(database, config_path, {"level": 16})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="mirror-realm-watchman-probe-16-20",
        minimum_level=16,
        maximum_level=20,
        status="research",
        execution="mirror-realm-watchman-research",
        summary="Bounded live-consider research route.",
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

    assert captured["fastwalk_route"].name == "mirror realm watchman"
    assert captured["fastwalk_route"].recall_after_loot is True
    first, second = captured["fastwalk_hunt_stops"]
    assert first.target == "watchman"
    assert first.command_keyword == "watchman"
    assert first.consider_only is True
    assert first.exact_target is True
    assert first.route_vnums == ()
    assert second.target == "watchman"
    assert second.command_keyword == "watchman"
    assert second.consider_only is True
    assert second.exact_target is True
    assert second.route_vnums == ("19008", "19010")
    assert captured["require_fastwalk_kill"] is False


def test_mirror_realm_watchman_hunt_dispatches_one_reconsidered_kill(
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
            return _record_segment_run(database, config_path, {"level": 16})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="mirror-realm-watchman-hunt-16-20",
        minimum_level=16,
        maximum_level=20,
        status="research",
        execution="mirror-realm-watchman-hunt",
        summary="Bounded live-consider hunt.",
        evidence=(),
        practice_skill=None,
        segment_kill_limit=1,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_route"].name == "mirror realm watchman"
    assert captured["fastwalk_kill_limit"] == 1
    first, second = captured["fastwalk_hunt_stops"]
    assert all(stop.consider_only is False for stop in (first, second))
    assert all(stop.minimum_health_ratio == 0.85 for stop in (first, second))
    assert all(stop.exact_target is True for stop in (first, second))
    assert second.route_vnums == ("19008", "19010")


@pytest.mark.parametrize(
    ("execution", "expected_consider_only", "kill_limit"),
    (
        ("crystalmir-white-stag-research", True, None),
        ("crystalmir-white-stag-hunt", False, 1),
    ),
)
def test_crystalmir_white_stag_dispatches_source_safe_search(
    tmp_path,
    monkeypatch,
    execution: str,
    expected_consider_only: bool,
    kill_limit: int | None,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 16})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id=execution,
        minimum_level=16,
        maximum_level=20,
        status="research",
        execution=execution,
        summary="Bounded White Stag search.",
        evidence=(),
        practice_skill=None,
        segment_kill_limit=kill_limit,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_route"].name == "crystalmir white stag"
    assert captured["fastwalk_kill_limit"] == kill_limit
    assert captured["fastwalk_required_move"] == 246
    stops = captured["fastwalk_hunt_stops"]
    assert len(stops) == 67
    assert all(
        stop.consider_only is expected_consider_only for stop in stops
    )
    assert stops[0].target == "beautiful white stag"
    assert stops[0].command_keyword == "stag"
    assert captured["require_fastwalk_kill"] is False


def test_shadow_keep_soldier_research_dispatch_never_initiates_combat(
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
            return _record_segment_run(database, config_path, {"level": 16})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="shadow-keep-undead-soldier-probe-16-20",
        minimum_level=16,
        maximum_level=20,
        status="research",
        execution="shadow-keep-undead-soldier-research",
        summary="Bounded live-consider research route.",
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

    assert captured["fastwalk_route"].name == "shadow keep soldier"
    assert captured["fastwalk_route"].recall_after_loot is True
    stops = captured["fastwalk_hunt_stops"]
    assert [stop.target for stop in stops] == [
        "undead soldier",
        "undead soldier",
        "undead soldier",
        "shadow wraith",
        "shadow wraith",
    ]
    assert all(stop.consider_only is True for stop in stops)
    assert all(stop.exact_target is True for stop in stops)
    assert captured["require_fastwalk_kill"] is False


def test_shadow_keep_soldier_hunt_dispatches_one_reconsidered_kill(
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
            return _record_segment_run(database, config_path, {"level": 16})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="shadow-keep-undead-soldier-hunt-16-20",
        minimum_level=16,
        maximum_level=20,
        status="research",
        execution="shadow-keep-undead-soldier-hunt",
        summary="Bounded live-consider hunt.",
        evidence=(),
        practice_skill=None,
        segment_kill_limit=1,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_route"].name == "shadow keep soldier"
    assert captured["fastwalk_kill_limit"] == 1
    stops = captured["fastwalk_hunt_stops"]
    assert len(stops) == 5
    assert all(stop.consider_only is False for stop in stops)
    assert all(stop.minimum_health_ratio == 0.85 for stop in stops)
    assert all(stop.maximum_level_offset == 1 for stop in stops)
    assert all(stop.exact_target is True for stop in stops)


def test_mirror_realm_gardener_research_dispatch_never_initiates_combat(
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
            return _record_segment_run(database, config_path, {"level": 21})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="mirror-realm-gardener-probe-21-25",
        minimum_level=21,
        maximum_level=25,
        status="research",
        execution="mirror-realm-gardener-research",
        summary="Bounded live-consider research route.",
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

    assert captured["fastwalk_route"].name == "mirror realm gardener"
    assert captured["fastwalk_route"].recall_after_loot is True
    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.target == "the gardener"
    assert stop.command_keyword == "gardener"
    assert stop.consider_only is True
    assert stop.exact_target is True
    assert stop.route_vnums == ("19091",)
    assert captured["require_fastwalk_kill"] is False


def test_mirror_realm_gardener_hunt_dispatches_one_reconsidered_kill(
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
            return _record_segment_run(database, config_path, {"level": 21})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="mirror-realm-gardener-hunt-21-25",
        minimum_level=21,
        maximum_level=25,
        status="research",
        execution="mirror-realm-gardener-hunt",
        summary="Bounded live-consider hunt.",
        evidence=(),
        practice_skill=None,
        segment_kill_limit=1,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_route"].name == "mirror realm gardener"
    assert captured["fastwalk_kill_limit"] == 1
    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.target == "the gardener"
    assert stop.command_keyword == "gardener"
    assert stop.consider_only is False
    assert stop.minimum_health_ratio == 0.85
    assert stop.maximum_level_offset == 1
    assert stop.exact_target is True
    assert stop.route_vnums == ("19091",)
    assert captured["require_fastwalk_kill"] is False


def test_galaxy_cancer_research_dispatch_never_initiates_combat(
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
            return _record_segment_run(database, config_path, {"level": 31})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="galaxy-cancer-probe-31-35",
        minimum_level=31,
        maximum_level=35,
        status="research",
        execution="galaxy-cancer-research",
        summary="Bounded live-consider research route.",
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

    assert captured["fastwalk_route"].name == "galaxy cancer"
    assert captured["fastwalk_route"].recall_after_loot is True
    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.target == "Cancer"
    assert stop.command_keyword == "cancer"
    assert stop.consider_only is True
    assert stop.exact_target is True
    assert stop.route_vnums == ("9345",)
    assert captured["require_fastwalk_kill"] is False


@pytest.mark.parametrize(
    ("execution", "consider_only"),
    [
        ("galaxy-white-dwarf-research", True),
        ("galaxy-white-dwarf-hunt", False),
        ("galaxy-red-supergiant-research", True),
        ("galaxy-red-supergiant-hunt", False),
    ],
)
def test_galaxy_white_dwarf_dispatch_preserves_probe_and_hunt_modes(
    tmp_path,
    monkeypatch,
    execution: str,
    consider_only: bool,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 17})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id=execution,
        minimum_level=17,
        maximum_level=20,
        status="research",
        execution=execution,
        summary="Bounded Galaxy target policy.",
        evidence=(),
        practice_skill=None,
        segment_kill_limit=1,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    expected_route = (
        "galaxy red supergiant"
        if execution.startswith("galaxy-red-supergiant")
        else "galaxy white dwarf"
    )
    expected_target = (
        "red supergiant"
        if execution.startswith("galaxy-red-supergiant")
        else "tiny white dwarf"
    )
    assert captured["fastwalk_route"].name == expected_route
    assert captured["fastwalk_route"].recall_after_loot is True
    stops = captured["fastwalk_hunt_stops"]
    assert stops
    assert all(stop.target == expected_target for stop in stops)
    assert all(stop.consider_only is consider_only for stop in stops)
    assert all(stop.exact_target is True for stop in stops)
    assert captured["fastwalk_kill_limit"] == 1
    assert captured["require_fastwalk_kill"] is False


@pytest.mark.parametrize(
    ("execution", "consider_only"),
    [
        ("hightower-jailor-research", True),
        ("hightower-jailor-hunt", False),
    ],
)
def test_hightower_jailor_dispatch_preserves_probe_and_hunt_modes(
    tmp_path,
    monkeypatch,
    execution: str,
    consider_only: bool,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 17})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id=execution,
        minimum_level=17,
        maximum_level=20,
        status="research",
        execution=execution,
        summary="Bounded High Tower Jailor policy.",
        evidence=(),
        practice_skill=None,
        segment_kill_limit=1,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_route"].name == "hightower jailor"
    assert captured["fastwalk_route"].recall_after_loot is True
    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.target == "jailor"
    assert stop.command_keyword == "jailor"
    assert stop.consider_only is consider_only
    assert stop.exact_target is True
    assert captured["fastwalk_required_move"] == 246
    assert captured["fastwalk_kill_limit"] == 1
    assert captured["require_fastwalk_kill"] is False


def test_mirror_realm_jerry_garcia_research_dispatch_never_initiates_combat(
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
            return _record_segment_run(database, config_path, {"level": 36})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="mirror-realm-jerry-garcia-probe-36-40",
        minimum_level=36,
        maximum_level=40,
        status="research",
        execution="mirror-realm-jerry-garcia-research",
        summary="Bounded live-consider research route.",
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

    assert captured["fastwalk_route"].name == "mirror realm jerry garcia"
    assert captured["fastwalk_route"].recall_after_loot is True
    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.target == "Jerry Garcia"
    assert stop.command_keyword == "jerry"
    assert stop.consider_only is True
    assert stop.exact_target is True
    assert stop.route_vnums == ("19170",)
    assert captured["require_fastwalk_kill"] is False


@pytest.mark.parametrize(
    ("execution", "consider_only"),
    [
        ("dwarven-home-chess-dwarf-research", True),
        ("dwarven-home-chess-dwarf-hunt", False),
        ("mirror-realm-storn-research", True),
        ("mirror-realm-storn-hunt", False),
    ],
)
def test_level_46_dispatch_preserves_probe_and_hunt_modes(
    tmp_path,
    monkeypatch,
    execution: str,
    consider_only: bool,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 46})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id=execution,
        minimum_level=46,
        maximum_level=50,
        status="research",
        execution=execution,
        summary="Bounded level-46 target policy.",
        evidence=(),
        practice_skill=None,
        segment_kill_limit=1,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    expected_route = (
        "dwarven home chess dwarf"
        if execution.startswith("dwarven-home-chess-dwarf")
        else "mirror realm storn"
    )
    expected_target = (
        "dwarf"
        if execution.startswith("dwarven-home-chess-dwarf")
        else "storn the assassin"
    )
    assert captured["fastwalk_route"].name == expected_route
    assert captured["fastwalk_route"].recall_after_loot is True
    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.target == expected_target
    assert stop.consider_only is consider_only
    assert stop.exact_target is True
    assert captured["fastwalk_kill_limit"] == 1
    assert captured["require_fastwalk_kill"] is False


@pytest.mark.parametrize(
    ("execution", "consider_only"),
    [
        ("darkwood-strange-mist-research", True),
        ("darkwood-strange-mist-hunt", False),
        ("dwarven-home-gambler-research", True),
        ("dwarven-home-gambler-hunt", False),
    ],
)
def test_level_51_dispatch_preserves_probe_and_hunt_modes(
    tmp_path,
    monkeypatch,
    execution: str,
    consider_only: bool,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 51})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id=execution,
        minimum_level=51,
        maximum_level=55,
        status="research",
        execution=execution,
        summary="Bounded level-51 target policy.",
        evidence=(),
        practice_skill=None,
        segment_kill_limit=1,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    expected_route = (
        "darkwood strange mist"
        if execution.startswith("darkwood-strange-mist")
        else "dwarven home gambler"
    )
    expected_target = (
        "strange mist"
        if execution.startswith("darkwood-strange-mist")
        else "dwarf"
    )
    assert captured["fastwalk_route"].name == expected_route
    assert captured["fastwalk_route"].recall_after_loot is True
    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.target == expected_target
    assert stop.consider_only is consider_only
    assert stop.exact_target is True
    assert captured["fastwalk_kill_limit"] == 1
    assert captured["require_fastwalk_kill"] is False


@pytest.mark.parametrize(
    ("execution", "consider_only"),
    [
        ("dwarven-home-master-research", True),
        ("dwarven-home-master-hunt", False),
    ],
)
def test_level_56_dispatch_preserves_master_probe_and_hunt_modes(
    tmp_path,
    monkeypatch,
    execution: str,
    consider_only: bool,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 56})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id=execution,
        minimum_level=56,
        maximum_level=60,
        status="research",
        execution=execution,
        summary="Bounded level-56 target policy.",
        evidence=(),
        practice_skill=None,
        segment_kill_limit=1,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_route"].name == "dwarven home master"
    assert captured["fastwalk_route"].recall_after_loot is True
    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.target == "master of the house"
    assert stop.consider_only is consider_only
    assert stop.exact_target is True
    assert captured["fastwalk_kill_limit"] == 1
    assert captured["require_fastwalk_kill"] is False


@pytest.mark.parametrize(
    ("execution", "consider_only"),
    [
        ("vampire-hive-wounded-vampire-research", True),
        ("vampire-hive-wounded-vampire-hunt", False),
    ],
)
def test_level_61_dispatch_preserves_vampire_probe_and_hunt_modes(
    tmp_path,
    monkeypatch,
    execution: str,
    consider_only: bool,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 61})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id=execution,
        minimum_level=61,
        maximum_level=65,
        status="research",
        execution=execution,
        summary="Bounded level-61 target policy.",
        evidence=(),
        practice_skill=None,
        segment_kill_limit=1,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_route"].name == "vampire hive wounded vampire"
    assert captured["fastwalk_route"].recall_after_loot is True
    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.target == "wounded vampire"
    assert stop.actions == ("where vampire",)
    assert stop.consider_only is consider_only
    assert stop.exact_target is True
    assert captured["fastwalk_kill_limit"] == 1
    assert captured["require_fastwalk_kill"] is False


@pytest.mark.parametrize(
    ("execution", "consider_only"),
    [
        ("tabernacle-hulking-beast-research", True),
        ("tabernacle-hulking-beast-hunt", False),
    ],
)
def test_level_66_dispatch_preserves_beast_probe_and_hunt_modes(
    tmp_path,
    monkeypatch,
    execution: str,
    consider_only: bool,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 66})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id=execution,
        minimum_level=66,
        maximum_level=70,
        status="research",
        execution=execution,
        summary="Bounded level-66 target policy.",
        evidence=(),
        practice_skill=None,
        segment_kill_limit=1,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_route"].name == "tabernacle hulking beast"
    assert captured["fastwalk_route"].recall_after_loot is True
    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.target == "hulking beast"
    assert stop.consider_only is consider_only
    assert stop.exact_target is True
    assert captured["fastwalk_kill_limit"] == 1
    assert captured["require_fastwalk_kill"] is False


@pytest.mark.parametrize(
    ("execution", "consider_only"),
    [
        ("pirates-seas-rastafarians-research", True),
        ("pirates-seas-rastafarians-hunt", False),
    ],
)
def test_level_71_dispatch_preserves_rastafarians_probe_and_hunt_modes(
    tmp_path,
    monkeypatch,
    execution: str,
    consider_only: bool,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 71})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id=execution,
        minimum_level=71,
        maximum_level=75,
        status="research",
        execution=execution,
        summary="Bounded level-71 target policy.",
        evidence=(),
        practice_skill=None,
        segment_kill_limit=1,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_route"].name == "pirates seas rastafarians"
    assert captured["fastwalk_route"].recall_after_loot is True
    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.target == "rastafarians"
    assert stop.actions == ("where rastafarians",)
    assert stop.consider_only is consider_only
    assert stop.exact_target is True
    assert captured["fastwalk_kill_limit"] == 1
    assert captured["require_fastwalk_kill"] is False


@pytest.mark.parametrize(
    ("execution", "consider_only", "route_name", "target"),
    [
        (
            "ghost-town-crypt-thing-research",
            True,
            "ghost town crypt thing",
            "crypt thing",
        ),
        (
            "ghost-town-crypt-thing-hunt",
            False,
            "ghost town crypt thing",
            "crypt thing",
        ),
        (
            "ghost-town-retriever-research",
            True,
            "ghost town retriever",
            "retriever",
        ),
        (
            "ghost-town-retriever-hunt",
            False,
            "ghost town retriever",
            "retriever",
        ),
    ],
)
def test_ghost_town_dispatch_preserves_probe_and_hunt_modes(
    tmp_path,
    monkeypatch,
    execution: str,
    consider_only: bool,
    route_name: str,
    target: str,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 77})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    minimum_level = 76 if "crypt" in execution else 77
    maximum_level = 76 if "crypt" in execution else 80
    policy = ProgressionPolicy(
        policy_id=execution,
        minimum_level=minimum_level,
        maximum_level=maximum_level,
        status="research",
        execution=execution,
        summary="Bounded Ghost Town target policy.",
        evidence=(),
        practice_skill=None,
        segment_kill_limit=1,
    )

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy,
        )
    )

    assert captured["fastwalk_route"].name == route_name
    assert captured["fastwalk_route"].recall_after_loot is True
    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.target == target
    assert stop.actions == ()
    assert stop.consider_only is consider_only
    assert stop.exact_target is True
    assert captured["fastwalk_kill_limit"] == 1
    assert captured["require_fastwalk_kill"] is False


def test_shire_battle_master_research_dispatch_never_initiates_combat(
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
            return _record_segment_run(database, config_path, {"level": 26})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="shire-battle-master-probe-26-30",
        minimum_level=26,
        maximum_level=30,
        status="research",
        execution="shire-battle-master-research",
        summary="Bounded live-consider research route.",
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

    assert captured["fastwalk_route"].name == "shire battle master"
    assert captured["fastwalk_route"].recall_after_loot is True
    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.target == "the battle master"
    assert stop.command_keyword == "battle"
    assert stop.consider_only is True
    assert stop.exact_target is True
    assert stop.route_vnums == ("1117",)
    assert captured["require_fastwalk_kill"] is False


def test_plains_aruncus_kill_research_dispatch_is_source_fuzz_bounded(
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
            return _record_segment_run(database, config_path, {"level": 13})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="plains-aruncus-thief-kill-research-v3-13-15",
        minimum_level=13,
        maximum_level=15,
        status="research",
        execution="plains-aruncus-hunt",
        summary="One bounded Aruncus fight.",
        evidence=(),
        practice_skill="backstab",
        segment_kill_limit=1,
    )

    asyncio.run(_run_policy_segment(spec.character, spec.character_profile, policy))

    stops = captured["fastwalk_hunt_stops"]
    assert captured["fastwalk_kill_limit"] == 1
    assert all(not stop.consider_only for stop in stops)
    assert all(stop.minimum_health_ratio == 0.85 for stop in stops)
    assert all(stop.maximum_level_offset == 2 for stop in stops)
    assert all(stop.exact_target for stop in stops)


def test_bardoosh_kill_research_dispatch_is_strictly_bounded(
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
            return _record_segment_run(database, config_path, {"level": 13})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = ProgressionPolicy(
        policy_id="ambush-bardoosh-thief-kill-research-13",
        minimum_level=13,
        maximum_level=13,
        status="research",
        execution="ambush-bardoosh-hunt",
        summary="One bounded Bardoosh fight.",
        evidence=(),
        practice_skill="backstab",
        segment_kill_limit=1,
    )

    asyncio.run(_run_policy_segment(spec.character, spec.character_profile, policy))

    assert captured["fastwalk_route"].name == "ambush"
    assert captured["fastwalk_kill_limit"] == 1
    (stop,) = captured["fastwalk_hunt_stops"]
    assert stop.target == "Bardoosh"
    assert stop.minimum_health_ratio == 0.9
    assert stop.maximum_level_offset == 1
    assert stop.exact_target is True
    assert captured["allow_safe_fastwalk_abort"] is True


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


def test_campaign_requires_piercing_weapon_in_the_primary_slot(tmp_path) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    spec = replace(
        load_campaign_spec(config_path),
        character=replace(
            load_campaign_spec(config_path).character,
            character_class="thief",
        ),
    )
    runner = CampaignRunner(spec, config_path)
    mace = ObjectSource(
        3352,
        "standard mace",
        "a standard mace",
        5,
        (0, 4, 4, 7),
        5,
        wear_flags=1 | (1 << 13),
    )
    dagger = ObjectSource(
        5252,
        "long dagger slim",
        "a long slim dagger",
        5,
        (0, 2, 5, 11),
        5,
        wear_flags=1 | (1 << 13),
    )
    runner._gear_catalog = GearCatalog({mace.vnum: mace, dagger.vnum: dagger})
    state = {
        "level": 17,
        "room_vnum": "3054",
        "campaign_has_weapon": True,
        "campaign_worn_equipment": ["a standard mace", "a long slim dagger"],
        "campaign_primary_weapon": "a standard mace",
        "campaign_empty_equipment_categories": [],
        "inventory": [[{"short_desc": "a big pot pie"}]],
    }

    assert runner._needs_piercing_weapon(state) is True
    state["campaign_primary_weapon"] = "a long slim dagger"
    assert runner._needs_piercing_weapon(state) is False


def test_campaign_upgrades_a_weaker_piercing_primary_from_inventory(tmp_path) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    spec = replace(
        load_campaign_spec(config_path),
        character=replace(
            load_campaign_spec(config_path).character,
            character_class="thief",
        ),
    )
    runner = CampaignRunner(spec, config_path)
    basic_dagger = ObjectSource(
        3001,
        "dagger",
        "a dagger",
        5,
        (0, 1, 4, 11),
        94,
        wear_flags=1 | (1 << 13),
    )
    long_dagger = ObjectSource(
        5252,
        "long dagger slim",
        "a long slim dagger",
        5,
        (0, 2, 5, 11),
        100,
        wear_flags=1 | (1 << 13),
    )
    runner._gear_catalog = GearCatalog(
        {item.vnum: item for item in (basic_dagger, long_dagger)}
    )
    state = {
        "level": 18,
        "room_vnum": "3054",
        "campaign_has_weapon": True,
        "campaign_worn_equipment": ["[#22311] a dagger"],
        "campaign_primary_weapon": "[#22311] a dagger",
        "campaign_empty_equipment_categories": [],
        "inventory": [
            [{"short_desc": "[_?_] a long slim dagger"}],
        ],
    }

    assert runner._needs_piercing_weapon(state) is False
    assert _state_needs_better_piercing_weapon(
        state,
        gear_catalog=runner._gear_catalog,
        character_class="thief",
        subclass=None,
    ) is True


def test_campaign_extracts_primary_weapon_from_the_latest_equipment_audit(
    tmp_path,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    with RunStorage(database) as storage:
        run_id = storage.create_run(
            scenario_name="equipment-audit",
            scenario_path=config_path,
        )
        storage.record_event(
            run_id,
            kind="command",
            payload={"command": "eq all"},
        )
        storage.record_event(
            run_id,
            kind="response",
            payload={
                "text": (
                    "<worn on head> a tophat\n"
                    "[weapon] a standard mace\n"
                    "[second weapon] a long slim dagger\n"
                )
            },
        )
        storage.record_event(
            run_id,
            kind="command",
            payload={"command": "eq all"},
        )
        storage.record_event(
            run_id,
            kind="response",
            payload={
                "text": (
                    "<worn on head> a tophat\n"
                    "[weapon] [_?_] a long slim dagger\n"
                )
            },
        )

        assert _run_primary_weapon_slot(storage, run_id) == (
            True,
            "[_?_] a long slim dagger",
        )


def test_campaign_primary_weapon_replay_keeps_later_wield_acknowledgement(
    tmp_path,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    with RunStorage(database) as storage:
        run_id = storage.create_run(
            scenario_name="equipment-replay",
            scenario_path=config_path,
        )
        storage.record_event(
            run_id,
            kind="command",
            payload={"command": "eq all"},
        )
        storage.record_event(
            run_id,
            kind="response",
            payload={"text": "[weapon] -\n"},
        )
        storage.record_event(
            run_id,
            kind="response",
            payload={"text": "You wield a long slim dagger.\n"},
        )

        assert _run_primary_weapon_slot(storage, run_id) == (
            True,
            "a long slim dagger",
        )


def test_campaign_equipment_replay_updates_stale_empty_weapon_audit(
    tmp_path,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    with RunStorage(database) as storage:
        run_id = storage.create_run(
            scenario_name="equipment-empty-replay",
            scenario_path=config_path,
        )
        storage.record_event(
            run_id,
            kind="command",
            payload={"command": "eq all"},
        )
        storage.record_event(
            run_id,
            kind="response",
            payload={"text": "[weapon] a long slim dagger\n"},
        )
        storage.record_event(
            run_id,
            kind="command",
            payload={"command": "eq all"},
        )
        storage.record_event(
            run_id,
            kind="response",
            payload={"text": "[weapon] -\n"},
        )
        storage.record_event(
            run_id,
            kind="response",
            payload={"text": "You wield a long slim dagger.\n"},
        )

        assert _run_equipment_empty_categories(storage, run_id) == set()
        assert _run_worn_equipment_descriptions(storage, run_id) == [
            "a long slim dagger"
        ]


def test_open_campaign_uses_audited_weapon_slot_when_worn_list_omits_weapon(
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
        run_id = storage.create_run(
            scenario_name=f"rearm:{spec.character.name}",
            scenario_path=config_path,
        )
        storage.record_event(run_id, kind="command", payload={"command": "eq all"})
        storage.record_event(
            run_id,
            kind="response",
            payload={
                "text": (
                    "<worn on head> a tophat\n"
                    "[weapon] [_?_] a long slim dagger\n"
                )
            },
        )
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="dwarven-nobleman-thief-hunt-17-18",
            start_state={"level": 17, "xp": 144638},
        )
        storage.finish_campaign_segment(
            segment_id,
            status="success",
            run_id=run_id,
            end_state={
                "level": 17,
                "xp": 144638,
                "campaign_has_weapon": False,
                "campaign_worn_equipment": ["a tophat"],
                "campaign_primary_weapon": "[_?_] a long slim dagger",
            },
            command_count=2,
            duration_seconds=1.0,
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=segment_id,
            run_id=run_id,
            phase="dwarven-nobleman-thief-hunt-17-18",
            reason="segment_complete",
            state={
                "level": 17,
                "xp": 144638,
                "campaign_has_weapon": False,
                "campaign_worn_equipment": ["a tophat"],
                "campaign_primary_weapon": "[_?_] a long slim dagger",
            },
        )

        _campaign_id, state = runner._open_campaign(storage)

    assert state["campaign_has_weapon"] is True
    assert state["campaign_primary_weapon"] == "[_?_] a long slim dagger"


def test_open_campaign_preserves_disarm_loss_over_stale_weapon_audit(
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
        run_id = storage.create_run(
            scenario_name=f"fastwalk:Kestrel",
            scenario_path=config_path,
        )
        storage.record_event(
            run_id,
            kind="command",
            payload={"command": "eq all"},
        )
        storage.record_event(
            run_id,
            kind="response",
            payload={"text": "[weapon] [_?_] a long slim dagger"},
        )
        storage.record_event(
            run_id,
            kind="response",
            payload={"text": "A speedy comet DISARMS you!"},
        )
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="galaxy-red-supergiant-probe-17-20",
            start_state={"level": 18, "xp": 154682},
        )
        storage.finish_campaign_segment(
            segment_id,
            status="success",
            run_id=run_id,
            end_state={
                "level": 18,
                "xp": 154682,
                "campaign_has_weapon": False,
                "campaign_worn_equipment": ["a long slim dagger"],
                "campaign_primary_weapon": "[_?_] a long slim dagger",
            },
            command_count=3,
            duration_seconds=1.0,
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=segment_id,
            run_id=run_id,
            phase="galaxy-red-supergiant-probe-17-20",
            reason="segment_complete",
            state={
                "level": 18,
                "xp": 154682,
                "campaign_has_weapon": False,
                "campaign_worn_equipment": ["a long slim dagger"],
                "campaign_primary_weapon": "[_?_] a long slim dagger",
            },
        )

        _campaign_id, state = runner._open_campaign(storage)

    assert state["campaign_has_weapon"] is False
    assert runner._policy_for_state(state).policy_id == "rearm-primary-weapon"


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


def test_campaign_reclaims_sack_vault_gear_after_same_level_outfit(
    tmp_path,
) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    runner = CampaignRunner(load_campaign_spec(config_path), config_path)

    policy = runner._policy_for_state(
        {
            "level": 8,
            "inventory": [
                [
                    {"short_desc": "a large sack"},
                    {"short_desc": "a big pot pie"},
                ]
            ],
            "campaign_has_weapon": True,
            "campaign_empty_equipment_categories": ["neck", "finger"],
            "campaign_outfit_attempted_level": 8,
            "campaign_sack_vault_items": ["collar", "vest"],
        }
    )

    assert policy.policy_id == "outfit-basic-gear"


def test_campaign_defers_remaining_sack_vault_gear_until_next_level(
    tmp_path,
) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    runner = CampaignRunner(load_campaign_spec(config_path), config_path)
    state = {
        "level": 8,
        "inventory": [
            [
                {"short_desc": "a large sack"},
                {"short_desc": "a big pot pie"},
            ]
        ],
        "campaign_has_weapon": True,
        "campaign_empty_equipment_categories": ["neck", "finger"],
        "campaign_outfit_attempted_level": 8,
        "campaign_sack_vault_items": ["vest"],
        "campaign_sack_vault_reclaim_attempted_level": 8,
    }

    assert runner._policy_for_state(state).policy_id != "outfit-basic-gear"
    state["level"] = 9
    assert runner._policy_for_state(state).policy_id == "outfit-basic-gear"


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


def test_campaign_retries_missing_daycare_rings_after_cooldown_or_reboot(
    tmp_path,
) -> None:
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

    for _ in range(3):
        state = _advance_daycare_ring_cooldown(
            state,
            execution="fleshmonger-thief-rotation",
            xp_delta=50,
        )

    assert state["campaign_daycare_ring_cooldown"] == 0
    assert runner._policy_for_state(state).execution == "recover-daycare-ring"


def test_daycare_ring_retry_cooldown_ignores_maintenance_and_zero_xp() -> None:
    state = {"campaign_daycare_ring_cooldown": 3}

    maintenance = _advance_daycare_ring_cooldown(
        state,
        execution="sell-loot",
        xp_delta=500,
    )
    empty_hunt = _advance_daycare_ring_cooldown(
        state,
        execution="fleshmonger-thief-rotation",
        xp_delta=0,
    )

    assert maintenance["campaign_daycare_ring_cooldown"] == 3
    assert empty_hunt["campaign_daycare_ring_cooldown"] == 3


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


def test_policy_revision_migrates_ring_attempt_to_bounded_cooldown() -> None:
    migrated = _refresh_policy_revision(
        {
            "level": 11,
            "campaign_policy_revision": 64,
            "campaign_daycare_ring_attempted_level": 11,
            "campaign_daycare_ring_attempted_boot_id": "current boot",
            "campaign_empty_equipment_categories": ["finger"],
        }
    )

    assert migrated["campaign_policy_revision"] == 110
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

    assert migrated["campaign_policy_revision"] == 110
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
            vault_claim_items=("collar", "vest"),
        )
    )

    assert captured == {
        "city_outfit": True,
        "vault_claim_items": ("collar", "vest"),
        "vault_wear_claimed_items": True,
    }


def test_sack_vault_claims_prioritize_combat_value() -> None:
    assert _prioritize_sack_vault_claims(
        ["vest", "sleeves", "collar", "belt", "bracer", "collar"]
    ) == ("collar", "bracer", "belt", "sleeves", "vest")


def test_successful_vault_lodges_are_reconstructed_from_run_evidence(
    tmp_path,
) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        run_id = storage.create_run(
            scenario_name="starter:Campaignmage",
            scenario_path=tmp_path / "character.yaml",
        )
        for kind, payload in (
            ("command", {"command": "lodge sleeves"}),
            (
                "response",
                {"text": "You lodge green sleeves in your vault.\n\r"},
            ),
            ("command", {"command": "lodge vest"}),
            (
                "response",
                {"text": "You can't put that much weight into your vault.\n\r"},
            ),
            ("command", {"command": "look"}),
            ("response", {"text": "Dragonhoard Bank\n\r"}),
        ):
            storage.record_event(run_id, kind=kind, payload=payload)

        assert _run_successful_vault_lodges(storage, run_id) == ("sleeves",)


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
    assert captured["fastwalk_train_before_departure"] is True
    assert captured["practice_types_spent"] == frozenset()
    assert captured["rejected_practice_skills"] == frozenset()
    first, second, third, fourth, nanny = captured["fastwalk_hunt_stops"]
    doll_stops = (first, second, third, fourth)
    assert [stop.route for stop in doll_stops] == [
        ("west",),
        (),
        ("south",),
        (),
    ]
    assert all(stop.target == "abused and old doll" for stop in doll_stops)
    assert all(
        stop.required_items == ("pink ice ring", "pink ice ring")
        for stop in doll_stops
    )
    assert all(stop.maximum_target_count == 2 for stop in doll_stops)
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
    assert captured["objective_level"] == 29
    assert captured["fastwalk_required_free_weight"] == 5
    assert captured["fastwalk_required_move"] == 246
    assert captured["fastwalk_kill_limit"] == 1
    assert captured["fastwalk_train_before_departure"] is True
    assert captured["require_fastwalk_kill"] is False
    assert captured["allow_safe_fastwalk_abort"] is True
    assert captured["use_sanctuary_potions"] is False
    assert captured["practice_types_spent"] == frozenset({"physical"})
    assert captured["rejected_practice_skills"] == frozenset({"second attack"})
    stops = captured["fastwalk_hunt_stops"]
    assert len(stops) == 80
    assert stops[-1].route_vnums == ("18053",)
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


def test_critical_coin_weight_requires_bank_deposit() -> None:
    assert _state_needs_coin_deposit(
        {
            "stats": {"carry_wt": 141, "maxcarry_wt": 140},
            "currencies": {
                "platinum": 0,
                "gold": 12,
                "silver": 97,
                "copper": 125,
            },
        }
    )
    assert _state_needs_coin_deposit(
        {
            "stats": {"carry_wt": 139, "maxcarry_wt": 140},
            "currencies": {"gold": 12, "silver": 97, "copper": 125},
        }
    )
    assert _state_needs_coin_deposit(
        {
            "stats": {"carry_wt": 161, "maxcarry_wt": 170},
            "currencies": {"gold": 15, "silver": 58, "copper": 167},
        }
    )
    assert not _state_needs_coin_deposit(
        {
            "stats": {"carry_wt": 160, "maxcarry_wt": 170},
            "currencies": {"gold": 15, "silver": 58, "copper": 167},
        }
    )


def test_campaign_banks_heavy_coins_before_vaulting_protected_gear(
    tmp_path,
) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    runner = CampaignRunner(load_campaign_spec(config_path), config_path)
    policy = runner._policy_for_state(
        {
            "level": 14,
            "inventory": [[
                {"short_desc": "a silver circlet"},
                {"short_desc": "a big pot pie", "quan": "2"},
                {"short_desc": "a buffalo water skin"},
            ]],
            "stats": {"carry_wt": 161, "maxcarry_wt": 170},
            "currencies": {"gold": 15, "silver": 58, "copper": 167},
            "campaign_has_weapon": True,
        }
    )

    assert policy.policy_id == "bank-excess-coins"


def test_poisoned_source_food_does_not_suppress_restock() -> None:
    poison_ivy = ObjectSource(
        302,
        "plant ivy",
        "a small dusk of poison ivy",
        19,
        (1, 0, 0, 1),
        1,
    )
    safe_meat = ObjectSource(
        303,
        "meat",
        "a slice of meat",
        19,
        (2, 0, 0, 0),
        1,
    )
    catalog = GearCatalog(
        {poison_ivy.vnum: poison_ivy, safe_meat.vnum: safe_meat}
    )

    assert not _has_campaign_food(
        {"inventory": [[{"short_desc": poison_ivy.short_description}]]},
        gear_catalog=catalog,
    )
    assert _has_campaign_food(
        {"inventory": [[{"short_desc": safe_meat.short_description}]]},
        gear_catalog=catalog,
    )


def test_full_inventory_with_poisoned_food_selects_liquidation() -> None:
    poison_ivy = ObjectSource(
        302,
        "plant ivy",
        "a small dusk of poison ivy",
        19,
        (1, 0, 0, 1),
        1,
    )
    catalog = GearCatalog({poison_ivy.vnum: poison_ivy})
    state = {
        "inventory": [[{
            "short_desc": poison_ivy.short_description,
            "quan": "24",
        }]],
        "stats": {
            "carry_num": 46,
            "maxcarry_num": 46,
            "carry_wt": 131,
            "maxcarry_wt": 250,
        },
        "campaign_liquidation_baseline": [],
    }

    assert _has_campaign_sellable_loot(state, gear_catalog=catalog)


def test_campaign_excess_coin_policy_uses_verified_bank_route(
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
            return _record_segment_run(database, config_path, {"level": 13})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)
    policy = policy_for(13, "thief", needs_coin_deposit=True)

    asyncio.run(_run_policy_segment(spec.character, spec.character_profile, policy))

    assert captured == {"bank_excess_coins": True}


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
            policy_for(
                10,
                "mage",
                has_large_sack=True,
                policy_xp_deltas={"fleshmonger-guard-probe-10-12": 0},
            ),
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
        policy_xp_deltas={"fleshmonger-guard-probe-10-12": 0},
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


def test_campaign_thief_with_nonpiercing_weapon_requests_primary_rearm(
    tmp_path,
) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    spec = replace(
        spec,
        character=replace(spec.character, character_class="thief"),
    )
    runner = CampaignRunner(spec, config_path)
    mace = ObjectSource(
        3352,
        "standard mace",
        "a standard mace",
        5,
        (0, 4, 4, 7),
        5,
        wear_flags=1 | (1 << 13),
    )
    runner._gear_catalog = GearCatalog({mace.vnum: mace})
    state = {
        "level": 17,
        "room_vnum": "3054",
        "campaign_has_weapon": True,
        "campaign_worn_equipment": ["a standard mace"],
        "campaign_empty_equipment_categories": [],
        "inventory": [[{"short_desc": "a big pot pie"}]],
    }

    assert runner._needs_piercing_weapon(state) is True
    policy = runner._policy_for_state(state)

    assert policy.policy_id == "rearm-primary-weapon"
    assert policy.execution == "rearm-weapon"


def test_campaign_empty_wield_slot_overrides_stale_piercing_primary(
    tmp_path,
) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    spec = replace(
        spec,
        character=replace(spec.character, character_class="thief"),
    )
    runner = CampaignRunner(spec, config_path)
    dagger = ObjectSource(
        5252,
        "long dagger slim",
        "a long slim dagger",
        5,
        (0, 2, 5, 11),
        100,
        wear_flags=1 | (1 << 13),
    )
    runner._gear_catalog = GearCatalog({dagger.vnum: dagger})
    state = {
        "level": 17,
        "room_vnum": "3054",
        "campaign_has_weapon": True,
        "campaign_worn_equipment": [],
        "campaign_primary_weapon": "a long slim dagger",
        "campaign_empty_equipment_categories": ["wield"],
        "inventory": [[{"short_desc": "a big pot pie"}]],
    }

    assert runner._needs_piercing_weapon(state) is True
    policy = runner._policy_for_state(state)

    assert policy.policy_id == "rearm-primary-weapon"
    assert policy.execution == "rearm-weapon"


def test_campaign_rearm_can_request_the_bounty_hunter_pounding_weapon(
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
            return _record_segment_run(database, config_path, {"level": 30, "xp": 32_000})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy_for(
                30,
                "thief",
                subclass="bounty hunter",
                has_weapon=True,
                needs_pounding_weapon=True,
            ),
            pounding_weapon_required=True,
        )
    )

    assert captured == {
        "city_rearm": True,
        "city_rearm_pounding": True,
    }


def test_campaign_warrior_missing_pounding_weapon_requests_stun_rearm(
    tmp_path,
) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    spec = replace(
        spec,
        character=replace(spec.character, character_class="warrior"),
    )
    runner = CampaignRunner(spec, config_path)
    dagger = ObjectSource(
        5252,
        "long dagger slim",
        "a long slim dagger",
        5,
        (0, 2, 5, 11),
        100,
        wear_flags=1 | (1 << 13),
    )
    runner._gear_catalog = GearCatalog({dagger.vnum: dagger})
    state = {
        "level": 30,
        "room_vnum": "3054",
        "campaign_has_weapon": True,
        "campaign_worn_equipment": ["a long slim dagger"],
        "campaign_empty_equipment_categories": [],
        "inventory": [[{"short_desc": "a big pot pie"}]],
    }

    assert runner._needs_pounding_weapon(state) is True
    policy = runner._policy_for_state(state)

    assert policy.policy_id == "rearm-primary-weapon"
    assert policy.execution == "rearm-weapon"


@pytest.mark.parametrize(
    ("character_class", "subclass", "level", "expected"),
    [
        ("warrior", None, 29, False),
        ("warrior", None, 30, True),
        ("thief", "ninja", 30, False),
        ("thief", "bounty hunter", 29, False),
        ("thief", "bounty hunter", 30, True),
    ],
)
def test_campaign_pounding_weapon_gate_matches_source_stun_users(
    tmp_path,
    character_class,
    subclass,
    level,
    expected,
) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    spec = replace(
        spec,
        character=replace(
            spec.character,
            character_class=character_class,
            subclass=subclass,
        ),
    )
    runner = CampaignRunner(spec, config_path)
    dagger = ObjectSource(
        5252,
        "long dagger slim",
        "a long slim dagger",
        5,
        (0, 2, 5, 11),
        100,
        wear_flags=1 | (1 << 13),
    )
    mace = ObjectSource(
        3352,
        "standard mace",
        "a standard mace",
        5,
        (0, 4, 4, 7),
        5,
        wear_flags=1 | (1 << 13),
    )
    runner._gear_catalog = GearCatalog(
        {item.vnum: item for item in (dagger, mace)}
    )
    state = {
        "level": level,
        "room_vnum": "3054",
        "campaign_has_weapon": True,
        "campaign_worn_equipment": ["a long slim dagger"],
        "campaign_empty_equipment_categories": [],
        "inventory": [[{"short_desc": "a big pot pie"}]],
    }

    assert runner._needs_pounding_weapon(state) is expected
    state["campaign_worn_equipment"] = [
        "a long slim dagger",
        "a standard mace",
    ]
    assert runner._needs_pounding_weapon(state) is False


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

    assert result.status == "ready"
    assert calls == 2
    with RunStorage(database) as storage:
        assert len(storage.list_campaign_segments(result.campaign_id)) == 2


def test_campaign_file_retries_a_reset_gated_checkpoint_outside_the_area(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    calls: list[bool] = []
    waits: list[float] = []
    results = iter(
        (
            CampaignResult(
                7,
                "ready",
                10,
                "arena circuit was empty. Campaign checkpointed while awaiting "
                "the Mud School area reset.",
                {"level": 3},
            ),
            CampaignResult(
                7,
                "ready",
                11,
                "mud-school-2-6 segment completed at level 3. Campaign "
                "checkpointed for the next verified segment.",
                {"level": 3},
            ),
        )
    )

    class TestRunner:
        def __init__(self, _spec, _path, *, force_new=False, **_options):
            calls.append(force_new)

        async def run(self) -> CampaignResult:
            return next(results)

    async def fake_sleep(seconds: float) -> None:
        waits.append(seconds)

    monkeypatch.setattr("dd4tester.campaign.CampaignRunner", TestRunner)
    monkeypatch.setattr("dd4tester.campaign.asyncio.sleep", fake_sleep)

    result = asyncio.run(
        run_campaign_file(
            config_path,
            force_new=True,
            reset_retries=1,
            reset_wait=42,
        )
    )

    assert calls == [True, False]
    assert waits == [42]
    assert result.checkpoint_id == 11


def test_campaign_file_defaults_reset_retries_to_segment_budget(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    calls: list[tuple[bool, bool]] = []
    waits: list[float] = []
    results = iter(
        (
            CampaignResult(
                7,
                "ready",
                10,
                "Campaign checkpointed while awaiting the field area reset.",
                {"level": 15},
            ),
            CampaignResult(
                7,
                "success",
                11,
                "Target level 100 reached.",
                {"level": 100},
            ),
        )
    )

    class TestRunner:
        def __init__(self, _spec, _path, **options):
            calls.append(
                (
                    bool(options.get("defer_stall_for_reset")),
                    bool(options.get("retry_stalled")),
                )
            )

        async def run(self) -> CampaignResult:
            return next(results)

    async def fake_sleep(seconds: float) -> None:
        waits.append(seconds)

    monkeypatch.setattr("dd4tester.campaign.CampaignRunner", TestRunner)
    monkeypatch.setattr("dd4tester.campaign.asyncio.sleep", fake_sleep)

    result = asyncio.run(
        run_campaign_file(
            config_path,
            segments=2,
            reset_wait=42,
        )
    )

    assert result.status == "success"
    assert calls == [(True, False), (True, True)]
    assert waits == [42]


def test_campaign_file_disables_default_reset_retries_for_bounded_runs(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    calls: list[tuple[bool, bool]] = []
    waits: list[float] = []

    class TestRunner:
        def __init__(self, _spec, _path, **options):
            calls.append(
                (
                    bool(options.get("defer_stall_for_reset")),
                    bool(options.get("retry_stalled")),
                )
            )

        async def run(self) -> CampaignResult:
            return CampaignResult(
                7,
                "ready",
                10,
                "Campaign checkpointed while awaiting the field area reset.",
                {"level": 15},
            )

    async def fake_sleep(seconds: float) -> None:
        waits.append(seconds)

    monkeypatch.setattr("dd4tester.campaign.CampaignRunner", TestRunner)
    monkeypatch.setattr("dd4tester.campaign.asyncio.sleep", fake_sleep)

    result = asyncio.run(
        run_campaign_file(
            config_path,
            segments=1,
            reset_wait=42,
            max_segment_runtime=180,
        )
    )

    assert result.status == "ready"
    assert calls == [(False, False)]
    assert waits == []


def test_campaign_file_resumes_normal_segments_after_productive_reset_retry(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    calls: list[bool] = []
    waits: list[float] = []
    results = iter(
        (
            CampaignResult(
                7,
                "ready",
                10,
                "Campaign checkpointed while awaiting the field area reset.",
                {"level": 8},
            ),
            CampaignResult(
                7,
                "ready",
                11,
                "ambush segment completed at level 8. Campaign checkpointed "
                "for the next verified segment.",
                {"level": 8, "xp": 100},
            ),
            CampaignResult(
                7,
                "success",
                12,
                "Target level 100 reached.",
                {"level": 100},
            ),
        )
    )

    class TestRunner:
        def __init__(self, _spec, _path, **options):
            calls.append(bool(options.get("retry_stalled")))

        async def run(self) -> CampaignResult:
            return next(results)

    async def fake_sleep(seconds: float) -> None:
        waits.append(seconds)

    monkeypatch.setattr("dd4tester.campaign.CampaignRunner", TestRunner)
    monkeypatch.setattr("dd4tester.campaign.asyncio.sleep", fake_sleep)

    result = asyncio.run(
        run_campaign_file(
            config_path,
            segments=2,
            reset_retries=1,
            reset_wait=42,
        )
    )

    assert calls == [False, True, False]
    assert waits == [42]
    assert result.status == "success"
    assert result.state["level"] == 100


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


def test_campaign_caps_segment_runtime_for_an_outer_launcher(tmp_path) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    requested_runtimes: list[float] = []

    async def starter_segment(spec, profile_path: Path) -> RunResult:
        requested_runtimes.append(spec.max_runtime)
        return _record_segment_run(spec.database, profile_path, {"level": 2})

    asyncio.run(
        CampaignRunner(
            load_campaign_spec(config_path),
            config_path,
            segment_runner=starter_segment,
            max_segment_runtime=180,
        ).run()
    )

    assert requested_runtimes == [180]


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

    assert first.status == "ready"
    assert second.status == "ready"
    assert third.message == "Campaign stalled for 2 completed segment(s)."
    assert calls == 3
    with RunStorage(database) as storage:
        assert len(storage.list_campaign_segments(third.campaign_id)) == 3

    resumed = asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=starter_segment).run()
    )
    assert resumed.message == "Campaign stalled for 2 completed segment(s)."
    assert calls == 3


def test_stalled_checkpoint_does_not_treat_checkpoint_id_as_segment_id(
    tmp_path,
) -> None:
    config_path, database = _write_campaign_files(tmp_path, max_stalled_segments=1)
    spec = load_campaign_spec(config_path)

    async def starter_segment(spec, profile_path: Path) -> RunResult:
        return _record_segment_run(
            spec.database,
            profile_path,
            {"level": 1, "xp": 0},
        )

    asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=starter_segment).run()
    )
    asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=starter_segment).run()
    )
    third = asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=starter_segment).run()
    )
    with RunStorage(database) as storage:
        storage.record_campaign_checkpoint(
            third.campaign_id,
            segment_id=None,
            run_id=None,
            phase="id-separation",
            reason="test-only",
            state={
                "level": 1,
                "xp": 0,
                "campaign_stalled_segments": 1,
                "campaign_policy_revision": 110,
            },
        )

    stalled = asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=starter_segment).run()
    )

    assert stalled.message == "Campaign stalled for 1 completed segment(s)."
    with RunStorage(database) as storage:
        checkpoint = storage.get_latest_campaign_checkpoint(stalled.campaign_id)
    assert checkpoint is not None
    assert checkpoint["segment_id"] is None


def test_campaign_can_wait_and_retry_a_field_stall(tmp_path) -> None:
    config_path, _database = _write_campaign_files(
        tmp_path,
        max_stalled_segments=1,
    )
    calls = 0

    async def starter_segment(spec, profile_path: Path) -> RunResult:
        nonlocal calls
        calls += 1
        return _record_segment_run(spec.database, profile_path, {"level": 1, "xp": 0})

    spec = load_campaign_spec(config_path)
    baseline = asyncio.run(
        CampaignRunner(
            spec,
            config_path,
            segment_runner=starter_segment,
            defer_stall_for_reset=True,
        ).run()
    )
    stalled = asyncio.run(
        CampaignRunner(
            spec,
            config_path,
            segment_runner=starter_segment,
            defer_stall_for_reset=True,
        ).run()
    )

    assert baseline.status == "ready"
    assert stalled.status == "ready"
    assert stalled.awaiting_area_reset is True
    assert calls == 2

    retried = asyncio.run(
        CampaignRunner(
            spec,
            config_path,
            segment_runner=starter_segment,
            defer_stall_for_reset=True,
            retry_stalled=True,
        ).run()
    )

    assert retried.status == "ready"
    assert retried.awaiting_area_reset is True
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


def test_campaign_allows_maintenance_after_absent_field_checkpoint(tmp_path) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    absent_policy = "shadow-keep-undead-soldier-hunt-16-20"
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
            phase=absent_policy,
            reason="segment_complete",
            state={
                "level": 17,
                "xp": 154_000,
                "room_name": "By the Temple Altar",
                "room_vnum": "3054",
                "world_boot_id": "boot-1",
                "campaign_last_policy": absent_policy,
                "campaign_liquidation_baseline": [],
                "campaign_research_results": {
                    absent_policy: {
                        "absent": True,
                        "boot_id": "boot-1",
                        "observed": False,
                        "viable": False,
                    }
                },
                "inventory": [[
                    {"short_desc": "a dagger", "quan": "1"},
                    {"short_desc": "a big pot pie", "quan": "1"},
                    {"short_desc": "a buffalo water skin", "quan": "1"},
                ]],
                "stats": {
                    "carry_num": 3,
                    "maxcarry_num": 46,
                    "carry_wt": 30,
                    "maxcarry_wt": 300,
                },
            },
        )

    calls = 0

    async def maintenance_segment(character, profile_path: Path) -> RunResult:
        nonlocal calls
        calls += 1
        return _record_segment_run(
            character.database,
            profile_path,
            {
                "level": 17,
                "xp": 154_000,
                "room_name": "By the Temple Altar",
                "room_vnum": "3054",
                "inventory": [[
                    {"short_desc": "a big pot pie", "quan": "1"},
                    {"short_desc": "a buffalo water skin", "quan": "1"},
                ]],
                "stats": {
                    "carry_num": 2,
                    "maxcarry_num": 46,
                    "carry_wt": 20,
                    "maxcarry_wt": 300,
                },
            },
        )

    result = asyncio.run(
        CampaignRunner(
            spec,
            config_path,
            segment_runner=maintenance_segment,
        ).run()
    )

    assert calls == 1
    with RunStorage(database) as storage:
        segments = storage.list_campaign_segments(campaign_id)
    assert [segment["phase"] for segment in segments] == ["liquidate-loot"]
    assert result.status == "ready"


def test_campaign_does_not_let_stale_absence_block_new_field_policy(tmp_path) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    stale_policy = "dwarven-nobleman-thief-probe-17-18"
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
            phase=stale_policy,
            reason="segment_complete",
            state={
                "level": 17,
                "xp": 154_000,
                "room_name": "By the Temple Altar",
                "room_vnum": "3054",
                "world_boot_id": "boot-1",
                "campaign_policy_revision": 101,
                "campaign_last_policy": stale_policy,
                "campaign_fastwalk_target_absent": False,
                "campaign_has_weapon": True,
                "campaign_worn_equipment": ["a long slim dagger"],
                "campaign_primary_weapon": "a long slim dagger",
                "campaign_empty_equipment_categories": [],
                "campaign_liquidation_baseline": [],
                "campaign_research_results": {
                    "mirror-realm-watchman-probe-16-20": {
                        "observed": True,
                        "viable": False,
                        "boot_id": "boot-1",
                    },
                    "crystalmir-white-stag-probe-16-20": {
                        "absent": True,
                        "observed": False,
                        "viable": False,
                        "boot_id": "boot-1",
                    },
                    "shadow-keep-undead-soldier-probe-16-20": {
                        "absent": True,
                        "observed": False,
                        "viable": False,
                        "boot_id": "boot-1",
                    },
                    "galaxy-white-dwarf-probe-17-20": {
                        "absent": True,
                        "observed": False,
                        "viable": False,
                        "boot_id": "boot-1",
                    },
                    stale_policy: {
                        "absent": True,
                        "observed": False,
                        "viable": False,
                        "boot_id": "boot-1",
                    },
                },
                "inventory": [[
                    {"short_desc": "a big pot pie", "quan": "1"},
                    {"short_desc": "a buffalo water skin", "quan": "1"},
                ]],
            },
        )

    calls = 0

    async def field_segment(character, profile_path: Path) -> RunResult:
        nonlocal calls
        calls += 1
        return _record_segment_run(
            character.database,
            profile_path,
            {"level": 17, "xp": 154_000},
        )

    result = asyncio.run(
        CampaignRunner(
            spec,
            config_path,
            segment_runner=field_segment,
        ).run()
    )

    assert calls == 1
    assert result.status == "ready"
    with RunStorage(database) as storage:
        segments = storage.list_campaign_segments(campaign_id)
    assert [segment["phase"] for segment in segments] == [
        "galaxy-red-supergiant-probe-17-20"
    ]


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


def test_empty_arena_checkpoint_waits_instead_of_blocking_campaign(tmp_path) -> None:
    config_path, database = _write_campaign_files(
        tmp_path,
        max_stalled_segments=1,
    )
    spec = load_campaign_spec(config_path)
    policy = ProgressionPolicy(
        policy_id="mud-school-2-6",
        minimum_level=2,
        maximum_level=6,
        status="verified",
        execution="arena",
        summary="Bounded Mud School arena progression.",
        evidence=(),
        practice_skill=None,
        segment_kill_limit=10,
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
            phase="ready",
            reason="ready",
            state={"level": 2, "xp": 2_825},
        )

    async def empty_arena_segment(character, profile_path: Path) -> RunResult:
        return _record_segment_run(
            character.database,
            profile_path,
            {"level": 2, "xp": 2_825},
        )

    class ArenaRunner(CampaignRunner):
        def _policy_for_state(self, state) -> ProgressionPolicy:
            return policy

    result = asyncio.run(
        ArenaRunner(
            spec,
            config_path,
            segment_runner=empty_arena_segment,
        ).run()
    )

    assert result.status == "ready"
    assert result.ready_for_next_segment is False
    assert result.message is not None
    assert "awaiting the Mud School area reset" in result.message
    with RunStorage(database) as storage:
        checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)
        campaign = storage.get_campaign(campaign_id)
    assert checkpoint is not None
    assert campaign is not None
    assert campaign["status"] == "ready"
    assert '"campaign_stalled_segments": 0' in checkpoint["state_json"]


def test_optional_moria_absence_falls_through_to_productive_policy(
    tmp_path,
) -> None:
    config_path, database = _write_campaign_files(
        tmp_path,
        max_stalled_segments=1,
    )
    spec = load_campaign_spec(config_path)
    policy = ProgressionPolicy(
        policy_id="moria-sanctuary-thief-17-20",
        minimum_level=17,
        maximum_level=20,
        status="research",
        execution="moria-sanctuary-hunt",
        summary="Acquire the optional reserve.",
        evidence=(),
        practice_skill=None,
    )
    fallback = ProgressionPolicy(
        policy_id="dwarven-nobleman-thief-hunt-17-18",
        minimum_level=17,
        maximum_level=18,
        status="verified",
        execution="dwarven-nobleman-hunt",
        summary="Continue productive progression.",
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
            phase="ready",
            reason="ready",
            state={"level": 17, "xp": 137_426},
        )

    async def absent_target_segment(character, profile_path: Path) -> RunResult:
        return _record_segment_run(
            character.database,
            profile_path,
            {
                "level": 17,
                "xp": 137_426,
                "world_boot_id": "boot-1",
                "campaign_fastwalk_target_absent": True,
            },
        )

    class OptionalReserveRunner(CampaignRunner):
        def _policy_for_state(self, state) -> ProgressionPolicy:
            results = state.get("campaign_research_results") or {}
            return fallback if policy.policy_id in results else policy

    result = asyncio.run(
        OptionalReserveRunner(
            spec,
            config_path,
            segment_runner=absent_target_segment,
        ).run()
    )

    assert result.status == "ready"
    assert result.ready_for_next_segment is True
    assert result.awaiting_area_reset is False
    assert result.message is not None
    assert "segment completed" in result.message
    with RunStorage(database) as storage:
        checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)
    assert checkpoint is not None
    checkpoint_state = json.loads(checkpoint["state_json"])
    assert checkpoint_state["campaign_research_results"][policy.policy_id][
        "absent"
    ] is True


@pytest.mark.parametrize(
    "policy_id",
    [
        "shadow-keep-undead-soldier-probe-16-20",
        "dwarven-nobleman-thief-probe-17-18",
    ],
)
def test_absent_research_target_waits_outside_area_for_bounded_reset(
    tmp_path,
    policy_id,
) -> None:
    config_path, database = _write_campaign_files(
        tmp_path,
        max_stalled_segments=1,
    )
    spec = load_campaign_spec(config_path)
    policy = ProgressionPolicy(
        policy_id=policy_id,
        minimum_level=16,
        maximum_level=20,
        status="research",
        execution="shadow-keep-undead-soldier-research",
        summary="Probe an isolated reset target.",
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
            phase="ready",
            reason="ready",
            state={"level": 16, "xp": 115_037},
        )

    async def absent_target_segment(character, profile_path: Path) -> RunResult:
        return _record_segment_run(
            character.database,
            profile_path,
            {
                "level": 16,
                "xp": 115_037,
                "world_boot_id": "boot-1",
                "campaign_fastwalk_target_absent": True,
            },
        )

    class ResearchRunner(CampaignRunner):
        def _policy_for_state(self, state) -> ProgressionPolicy:
            results = state.get("campaign_research_results") or {}
            if policy.policy_id in results:
                return ProgressionPolicy(
                    policy_id="unavailable",
                    minimum_level=16,
                    maximum_level=20,
                    status="unavailable",
                    execution=None,
                    summary="No alternate field policy is available.",
                    evidence=(),
                    practice_skill=None,
                )
            return policy

    result = asyncio.run(
        ResearchRunner(
            spec,
            config_path,
            segment_runner=absent_target_segment,
        ).run()
    )

    assert result.status == "ready"
    assert result.awaiting_area_reset is True
    assert result.message is not None
    assert "reset target was absent" in result.message
    with RunStorage(database) as storage:
        checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)
    assert checkpoint is not None
    checkpoint_state = json.loads(checkpoint["state_json"])
    assert checkpoint_state["campaign_research_results"][policy.policy_id][
        "absent"
    ] is True


def test_empty_verified_field_circuit_waits_before_reopening_same_area(tmp_path) -> None:
    config_path, database = _write_campaign_files(tmp_path, max_stalled_segments=3)
    spec = load_campaign_spec(config_path)
    policy = ProgressionPolicy(
        policy_id="mahntor-rock-toad-thief-circuit-16-18",
        minimum_level=16,
        maximum_level=18,
        status="verified",
        execution="mahntor-rock-toad-circuit",
        summary="Run a registered multi-stop field circuit.",
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
            phase="ready",
            reason="ready",
            state={"level": 18, "xp": 154_782},
        )

    async def absent_field_segment(character, profile_path: Path) -> RunResult:
        return _record_segment_run(
            character.database,
            profile_path,
            {
                "level": 18,
                "xp": 154_782,
                "world_boot_id": "boot-1",
                "campaign_fastwalk_target_absent": True,
            },
        )

    class EmptyFieldRunner(CampaignRunner):
        def _policy_for_state(self, state) -> ProgressionPolicy:
            return policy

    result = asyncio.run(
        EmptyFieldRunner(
            spec,
            config_path,
            segment_runner=absent_field_segment,
            defer_stall_for_reset=True,
        ).run()
    )

    assert result.status == "ready"
    assert result.awaiting_area_reset is True
    assert result.message is not None
    assert "no registered target" in result.message

    async def unexpected_reopen(*_args) -> RunResult:
        pytest.fail("an empty verified field circuit must wait before reopening")

    reopened = asyncio.run(
        EmptyFieldRunner(
            spec,
            config_path,
            segment_runner=unexpected_reopen,
            defer_stall_for_reset=True,
        ).run()
    )

    assert reopened.status == "ready"
    assert reopened.awaiting_area_reset is True
    assert reopened.message is not None
    assert "no registered target" in reopened.message


@pytest.mark.parametrize(
    "abort_reason",
    [
        (
            "field room contained 2 observed mobiles while evaluating "
            "'dwarven nobleman'"
        ),
        "field combat aborted after unapproved attacker 'A guest' joined",
    ],
)
def test_crowded_research_target_waits_without_recording_absence(
    tmp_path,
    abort_reason,
) -> None:
    config_path, database = _write_campaign_files(
        tmp_path,
        max_stalled_segments=1,
    )
    spec = load_campaign_spec(config_path)
    policy = ProgressionPolicy(
        policy_id="dwarven-nobleman-thief-probe-17-18",
        minimum_level=17,
        maximum_level=18,
        status="research",
        execution="dwarven-nobleman-research",
        summary="Probe a source-backed target.",
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
            phase="ready",
            reason="ready",
            state={"level": 17, "xp": 137_426},
        )

    async def crowded_target_segment(
        character,
        profile_path: Path,
    ) -> RunResult:
        return _record_segment_run(
            character.database,
            profile_path,
            {
                "level": 17,
                "xp": 137_426,
                "world_boot_id": "boot-1",
                "campaign_fastwalk_abort_reason": abort_reason,
                "campaign_fastwalk_target_absent": False,
            },
        )

    class CrowdRunner(CampaignRunner):
        def _policy_for_state(self, state) -> ProgressionPolicy:
            return policy

    result = asyncio.run(
        CrowdRunner(
            spec,
            config_path,
            segment_runner=crowded_target_segment,
            defer_stall_for_reset=True,
        ).run()
    )

    assert result.status == "ready"
    assert result.awaiting_area_reset is True
    assert result.message is not None
    assert "crowded field room" in result.message
    with RunStorage(database) as storage:
        checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)
    assert checkpoint is not None
    checkpoint_state = json.loads(checkpoint["state_json"])
    assert checkpoint_state["campaign_fastwalk_target_absent"] is False
    assert "campaign_research_results" not in checkpoint_state


@pytest.mark.parametrize(
    "abort_reason",
    [
        (
            "field room contained 2 observed mobiles while evaluating "
            "'dwarven nobleman'"
        ),
        "field combat aborted after unapproved attacker 'A guest' joined",
    ],
)
def test_existing_crowd_checkpoint_waits_before_reopening_field(
    tmp_path,
    abort_reason,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    policy = ProgressionPolicy(
        policy_id="dwarven-nobleman-thief-probe-17-18",
        minimum_level=17,
        maximum_level=18,
        status="research",
        execution="dwarven-nobleman-research",
        summary="Probe a source-backed target.",
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
                "level": 17,
                "xp": 137_426,
                "world_boot_id": "boot-1",
                "campaign_last_policy": policy.policy_id,
                "campaign_fastwalk_abort_reason": abort_reason,
                "campaign_fastwalk_target_absent": False,
            },
        )

    async def unexpected_segment(*_args) -> RunResult:
        pytest.fail("an existing crowd checkpoint must wait before field entry")

    class CrowdRunner(CampaignRunner):
        def _policy_for_state(self, state) -> ProgressionPolicy:
            return policy

    result = asyncio.run(
        CrowdRunner(
            spec,
            config_path,
            segment_runner=unexpected_segment,
            defer_stall_for_reset=True,
        ).run()
    )

    assert result.status == "ready"
    assert result.awaiting_area_reset is True
    assert result.message is not None
    assert "crowded field room" in result.message
    with RunStorage(database) as storage:
        assert storage.list_campaign_segments(campaign_id) == []


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


def test_campaign_checkpoints_configured_runtime_cap_for_resumption(tmp_path) -> None:
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
            phase="starter",
            reason="ready",
            state={
                "level": 1,
                "campaign_sack_vault_items": ["vest"],
                "campaign_sack_vault_reclaim_attempted_level": 1,
                "campaign_fastwalk_abort_reason": "stale retry",
            },
        )

    async def capped_segment(spec, profile_path: Path) -> RunResult:
        result = _record_segment_run(
            spec.database,
            profile_path,
            {"level": 2, "xp": 125},
            scenario_name="fastwalk-moria:Campaignmage",
        )
        with RunStorage(spec.database) as storage:
            storage.record_event(
                result.run_id,
                kind="state",
                payload={
                    "state": "runtime_cap",
                    "completed_kills": [],
                    "objective_kills": [],
                    "fastwalk_abort_reason": None,
                },
            )
            storage.finish_run(
                result.run_id,
                status="failed",
                error="Starter bot exceeded 180 second runtime",
            )
        raise TimeoutError("Starter bot exceeded 180 second runtime")

    result = asyncio.run(
        CampaignRunner(
            load_campaign_spec(config_path),
            config_path,
            segment_runner=capped_segment,
            max_segment_runtime=180,
        ).run()
    )

    assert result.status == "ready"
    assert result.message is not None
    assert "runtime cap" in result.message
    with RunStorage(database) as storage:
        segment = storage.list_campaign_segments(result.campaign_id)[0]
        checkpoint = storage.get_latest_campaign_checkpoint(result.campaign_id)
        campaign = storage.get_campaign(result.campaign_id)
    assert segment["status"] == "ready"
    assert segment["run_id"] is not None
    assert checkpoint is not None
    assert checkpoint["reason"] == "segment_runtime_cap"
    checkpoint_state = json.loads(checkpoint["state_json"])
    assert checkpoint_state["campaign_sack_vault_items"] == ["vest"]
    assert checkpoint_state["campaign_sack_vault_reclaim_attempted_level"] == 1
    assert "campaign_fastwalk_abort_reason" not in checkpoint_state
    assert campaign is not None
    assert campaign["status"] == "ready"


def test_campaign_preserves_objective_kill_when_runner_fails_afterward(tmp_path) -> None:
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
            phase="starter-0-2",
            reason="ready",
            state={"name": "Campaignmage", "level": 1, "xp": 0},
        )

    async def failed_after_kill(spec, profile_path: Path) -> RunResult:
        state = {
            "name": "Campaignmage",
            "level": 1,
            "xp": 321,
            "room_vnum": "3054",
            "area": "Midgaard",
            "world_boot_id": "boot-1",
        }
        with RunStorage(spec.database) as storage:
            run_id = storage.create_run(
                scenario_name="fastwalk-test:Campaignmage",
                scenario_path=profile_path,
            )
            storage.record_state_snapshot(
                run_id,
                source_event_id=None,
                reason="prompt_seen",
                state=state,
            )
            storage.record_event(
                run_id,
                kind="state",
                payload={
                    "state": "failed",
                    "completed_kills": [
                        {"mob_name": "the test rat", "xp_gained": 321}
                    ],
                    "objective_kills": [
                        {"mob_name": "the test rat", "xp_gained": 321}
                    ],
                },
            )
            storage.record_mob_kill(
                run_id,
                character_name="Campaignmage",
                boot_id="boot-1",
                mob_name="the test rat",
                xp_gained=321,
            )
            storage.finish_run(
                run_id,
                status="failed",
                error="post-kill recovery watchdog",
            )
        raise RuntimeError("post-kill recovery watchdog")

    result = asyncio.run(
        CampaignRunner(
            spec,
            config_path,
            segment_runner=failed_after_kill,
        ).run()
    )

    assert result.status == "ready"
    assert result.state["xp"] == 321
    assert result.state["campaign_last_policy"] == "starter-0-2"
    assert result.state["campaign_objective_kills"]
    with RunStorage(database) as storage:
        segment = storage.list_campaign_segments(result.campaign_id)[0]
        checkpoint = storage.get_latest_campaign_checkpoint(result.campaign_id)
        deltas = _campaign_policy_xp_deltas(
            storage.list_campaign_segments(result.campaign_id),
            storage=storage,
        )
    assert segment["status"] == "ready"
    assert segment["run_id"] is not None
    assert checkpoint["reason"] == "segment_failed_progress_reconciled"
    assert deltas["starter-0-2"] == 321


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


def test_first_live_maintenance_attempt_records_its_observed_boot(
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
            phase="ready",
            reason="ready",
            state={
                "level": 10,
                "campaign_empty_equipment_categories": ["finger"],
            },
        )

    async def observed_boot_segment(character, profile_path: Path) -> RunResult:
        return _record_segment_run(
            character.database,
            profile_path,
            {
                "level": 10,
                "world_boot_id": "new boot",
                "campaign_empty_equipment_categories": ["finger"],
            },
        )

    class MaintenanceRunner(CampaignRunner):
        def _policy_for_state(self, state) -> ProgressionPolicy:
            return policy

    result = asyncio.run(
        MaintenanceRunner(
            spec,
            config_path,
            segment_runner=observed_boot_segment,
        ).run()
    )

    assert result.state["campaign_daycare_ring_attempted_boot_id"] == "new boot"


def test_predeparture_invisibility_abort_retries_daycare_ring_preparation(
    tmp_path,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    policy = ProgressionPolicy(
        policy_id="recover-daycare-ring",
        minimum_level=8,
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
                "level": 8,
                "campaign_empty_equipment_categories": ["finger"],
            },
        )

    async def aborted_segment(character, profile_path: Path) -> RunResult:
        return _record_segment_run(
            character.database,
            profile_path,
            {
                "level": 8,
                "campaign_empty_equipment_categories": ["finger"],
                "campaign_fastwalk_abort_reason": (
                    "field expedition could not establish invisibility at "
                    "the safe origin"
                ),
            },
        )

    class MaintenanceRunner(CampaignRunner):
        def _policy_for_state(self, state) -> ProgressionPolicy:
            return policy

    result = asyncio.run(
        MaintenanceRunner(
            spec,
            config_path,
            segment_runner=aborted_segment,
        ).run()
    )

    assert result.status == "ready"
    assert "repair mandatory preparation" in result.message
    assert "campaign_daycare_ring_attempted_level" not in result.state
    with RunStorage(database) as storage:
        checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)
    assert checkpoint is not None
    assert checkpoint["reason"] == "segment_preparation_aborted"


def test_successful_sack_preparation_reopens_aborted_ring_recovery(
    tmp_path,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    policy = ProgressionPolicy(
        policy_id="midennir-sack-8-10",
        minimum_level=8,
        maximum_level=10,
        status="verified",
        execution="midennir-sack",
        summary="Acquire capacity infrastructure.",
        evidence=(),
        practice_skill="invis",
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
                "level": 8,
                "campaign_empty_equipment_categories": ["finger"],
                "campaign_daycare_ring_attempted_level": 8,
                "campaign_daycare_ring_attempted_boot_id": "current boot",
            },
        )

    async def sack_segment(character, profile_path: Path) -> RunResult:
        return _record_segment_run(
            character.database,
            profile_path,
            {
                "level": 8,
                "inventory": [[{"short_desc": "a large sack", "quan": "1"}]],
                "campaign_empty_equipment_categories": ["finger"],
            },
        )

    class SackRunner(CampaignRunner):
        def _policy_for_state(self, state) -> ProgressionPolicy:
            return policy

    result = asyncio.run(
        SackRunner(
            spec,
            config_path,
            segment_runner=sack_segment,
        ).run()
    )

    assert "campaign_daycare_ring_attempted_level" not in result.state
    assert "campaign_daycare_ring_attempted_boot_id" not in result.state


def test_maintenance_without_equipment_audit_preserves_known_slot_debt(
    tmp_path,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    policy = ProgressionPolicy(
        policy_id="vault-spare-gear",
        minimum_level=1,
        maximum_level=100,
        status="verified",
        execution="vault-spare-gear",
        summary="Free carrying capacity.",
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
                "level": 8,
                "campaign_empty_equipment_categories": ["finger", "waist"],
                "campaign_worn_equipment": ["a war dog collar"],
            },
        )

    async def vault_segment(character, profile_path: Path) -> RunResult:
        return _record_segment_run(
            character.database,
            profile_path,
            {"level": 8, "stats": {"carry_wt": 120, "maxcarry_wt": 170}},
        )

    class VaultRunner(CampaignRunner):
        def _policy_for_state(self, state) -> ProgressionPolicy:
            return policy

    result = asyncio.run(
        VaultRunner(
            spec,
            config_path,
            segment_runner=vault_segment,
        ).run()
    )

    assert result.state["campaign_empty_equipment_categories"] == [
        "finger",
        "waist",
    ]
    assert result.state["campaign_worn_equipment"] == ["a war dog collar"]


def test_campaign_resume_reopens_ring_recovery_after_sack_checkpoint(
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
            phase="midennir-sack-8-10",
            reason="segment_complete",
            state={
                "level": 8,
                "inventory": [[{"short_desc": "a large sack", "quan": "1"}]],
                "campaign_empty_equipment_categories": ["finger"],
                "campaign_daycare_ring_attempted_level": 8,
                "campaign_daycare_ring_attempted_boot_id": "current boot",
            },
        )

        opened_campaign_id, state = runner._open_campaign(storage)

    assert opened_campaign_id == campaign_id
    assert "campaign_daycare_ring_attempted_level" not in state
    assert "campaign_daycare_ring_attempted_boot_id" not in state


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


def test_open_campaign_updates_stored_target_for_resumed_level_goal(
    tmp_path: Path,
) -> None:
    config_path, database = _write_campaign_files(tmp_path, target_level=30)
    spec = load_campaign_spec(config_path)
    runner = CampaignRunner(spec, config_path)

    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name=spec.name,
            config_path=config_path.resolve(),
            character_profile_path=spec.character_profile,
            target_level=100,
        )

        resumed_campaign_id, _state = runner._open_campaign(storage)
        campaign = storage.get_campaign(campaign_id)

    assert resumed_campaign_id == campaign_id
    assert campaign is not None
    assert campaign["target_level"] == 30


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
    *,
    scenario_name: str = "starter:Campaignmage",
) -> RunResult:
    with RunStorage(database) as storage:
        run_id = storage.create_run(
            scenario_name=scenario_name,
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
