from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from dd4tester.populations import (
    POPULATION_LOCATOR_ABORT_PREFIX,
    POPULATION_LOCATOR_DETECT_INVIS_VERIFIED_KEY,
    POPULATION_LOCATOR_MISMATCHES_KEY,
    merge_population_locator_mismatches,
    population_locator_mismatch_blocks,
    population_locator_mismatch_receipt,
)
from dd4tester.campaign import (
    _SEE_INVISIBLE_FUNDING_REQUIRED_KEY,
    _MAGIC_SHOP_SEE_INVISIBLE_RETRY_KEY,
    _MAGIC_SHOP_SEE_INVISIBLE_RETRY_REVISION,
    _MAGIC_SHOP_SEE_INVISIBLE_PRICE_KEY,
    _magic_shop_see_invisible_failure_active,
    _repair_observed_see_invisible_state,
    _record_population_locator_mismatch,
    _source_ranked_visibility_preparation_policy,
)
from dd4tester.progression import ProgressionPolicy


def observation():
    return {
        "level": 39,
        "world_boot_id": "boot-A",
        "campaign_source_revision": "source-A",
        "campaign_last_policy": "source-ranked-hunt-test-area-10730-10821-39",
        "campaign_population_locator_run_id": 18113,
        "campaign_fastwalk_abort_reason": POPULATION_LOCATOR_ABORT_PREFIX + "required at the reset rooms",
        "campaign_fastwalk_where_decisions": [{
            "source_mobile_vnum": 10730,
            "locations": ["shrine"],
            "location_counts": {"shrine": 4},
        }],
    }


def test_live_population_mismatch_blocks_sibling_reset_not_independent_mobile():
    state = observation()
    for room in (10817, 10820, 10821, 10822):
        assert population_locator_mismatch_blocks(
            state, SimpleNamespace(mobile_vnum=10730, room_vnum=room), character_level=39,
        )
    assert not population_locator_mismatch_blocks(
        state, SimpleNamespace(mobile_vnum=10731), character_level=39,
    )
    assert population_locator_mismatch_receipt(state)["run_id"] == 18113


def test_population_mismatch_survives_a_different_successful_run():
    state = observation()
    saved = {
        "level": 39, "world_boot_id": "boot-A", "campaign_source_revision": "source-A",
        POPULATION_LOCATOR_MISMATCHES_KEY: merge_population_locator_mismatches(state, {}),
    }
    assert population_locator_mismatch_blocks(
        saved, SimpleNamespace(mobile_vnum=10730), character_level=39,
    )
    for key in ("world_boot_id", "campaign_source_revision"):
        changed = {**saved, key: "new"}
        assert not population_locator_mismatch_blocks(
            changed, SimpleNamespace(mobile_vnum=10730), character_level=39,
        )
    assert not population_locator_mismatch_blocks(
        saved, SimpleNamespace(mobile_vnum=10730), character_level=40,
    )


def test_checkpoint_run_id_is_promoted_to_the_durable_mismatch_ledger():
    from dd4tester.campaign import _checkpoint_state

    state = observation()
    state.pop("campaign_population_locator_run_id")
    checkpoint = {
        "state_json": json.dumps(state),
        "run_id": 18113,
    }

    restored = _checkpoint_state(checkpoint)

    assert restored[POPULATION_LOCATOR_MISMATCHES_KEY] == [
        population_locator_mismatch_receipt(observation()),
    ]
    assert population_locator_mismatch_blocks(
        restored, SimpleNamespace(mobile_vnum=10730, room_vnum=10817),
        character_level=39,
    )


@pytest.mark.parametrize("change", [
    {"campaign_population_locator_run_id": None},
    {"campaign_population_locator_run_id": True},
    {"campaign_last_policy": "source-ranked-hunt-test-area-10731-10821-39"},
    {"campaign_fastwalk_abort_reason": "field target absent"},
    {"campaign_source_ranked_hunt_candidate": {"mobile_vnum": 10731}},
    {"campaign_fastwalk_where_decisions": [{"source_mobile_vnum": 10730, "locations": [], "location_counts": {}}]},
    {"campaign_fastwalk_where_decisions": [{"source_mobile_vnum": 10730, "locations": [{}], "location_counts": {"shrine": 4}}]},
])
def test_incomplete_foreign_or_absence_evidence_does_not_close_a_family(change):
    state = {**observation(), **deepcopy(change)}
    assert population_locator_mismatch_receipt(state) is None


def test_population_ledger_is_bounded_and_deduplicates_identity():
    previous = {}
    for mobile in range(1, 12):
        state = observation()
        state["campaign_last_policy"] = f"source-ranked-hunt-test-area-{mobile}-100-39"
        state["campaign_fastwalk_where_decisions"][0]["source_mobile_vnum"] = mobile
        previous[POPULATION_LOCATOR_MISMATCHES_KEY] = merge_population_locator_mismatches(previous, state)
    assert len(previous[POPULATION_LOCATOR_MISMATCHES_KEY]) == 8
    records = merge_population_locator_mismatches(previous, state)
    assert len(records) == 8
    assert records[-1]["mobile_vnum"] == 11


def test_invisible_population_miss_without_detection_is_not_saved_or_blocking():
    state = observation()
    state["campaign_source_ranked_hunt_candidate"] = {
        "mobile_vnum": 10730,
        "requires_detect_invisibility": True,
    }

    recorded = _record_population_locator_mismatch(state, run_id=18113)

    assert recorded[POPULATION_LOCATOR_DETECT_INVIS_VERIFIED_KEY] is False
    assert population_locator_mismatch_receipt(recorded) is None
    old_unverified = {
        **state,
        POPULATION_LOCATOR_MISMATCHES_KEY: [{
            "run_id": 18112,
            "mobile_vnum": 10730,
            "level": 39,
            "boot_id": "boot-A",
            "source_revision": "source-A",
            "location_counts": {"weapon shop": 1},
            "reason": "population_mismatch",
        }],
    }
    assert not population_locator_mismatch_blocks(
        old_unverified,
        SimpleNamespace(mobile_vnum=10730, requires_detect_invisibility=True),
        character_level=39,
    )


def test_invisible_population_miss_with_detection_is_saved_and_blocks():
    state = observation()
    state["campaign_source_ranked_hunt_candidate"] = {
        "mobile_vnum": 10730,
        "requires_detect_invisibility": True,
    }
    state["affects"] = [[{"name": "detect invis", "duration": "5"}]]

    recorded = _record_population_locator_mismatch(state, run_id=18113)
    receipt = population_locator_mismatch_receipt(recorded)

    assert receipt is not None
    assert receipt["detect_invisibility_verified"] is True
    recorded[POPULATION_LOCATOR_MISMATCHES_KEY] = [receipt]
    assert population_locator_mismatch_blocks(
        recorded,
        SimpleNamespace(mobile_vnum=10730, requires_detect_invisibility=True),
        character_level=39,
    )


@pytest.mark.parametrize(
    ("affects", "failed", "can_prepare", "expected"),
    [
        ([], False, True, True),
        ([[{"name": "detect invis", "duration": "5"}]], False, True, False),
        ([], True, True, False),
        ([], False, False, False),
    ],
)
def test_source_ranked_invisible_target_schedules_only_needed_healer_preparation(
    affects, failed, can_prepare, expected,
):
    selected = ProgressionPolicy(
        policy_id="source-ranked-hunt-test-917-936-39",
        minimum_level=39,
        maximum_level=39,
        status="research",
        execution="source-ranked-hunt",
        summary="hunt",
        evidence=(),
        practice_skill=None,
    )
    candidate = SimpleNamespace(requires_detect_invisibility=True)
    state = {
        "affects": affects,
        "magic_shop_see_invisible_purchase_failed": failed,
    }

    policy = _source_ranked_visibility_preparation_policy(
        selected,
        candidate,
        state,
        character_level=39,
        can_prepare=can_prepare,
    )

    assert (policy is not None) is expected
    if expected:
        assert policy.execution == "buy-see-invisible"


def test_pending_same_boot_visibility_retry_overrides_one_old_failure():
    selected = ProgressionPolicy(
        policy_id="source-ranked-hunt-test-908-937-39",
        minimum_level=39,
        maximum_level=39,
        status="research",
        execution="source-ranked-hunt",
        summary="hunt",
        evidence=(),
        practice_skill=None,
    )
    state = {
        "level": 39,
        "world_boot_id": "boot-A",
        "affects": [],
        "magic_shop_see_invisible_purchase_failed": True,
        "magic_shop_see_invisible_purchase_failed_boot": "boot-A",
        _MAGIC_SHOP_SEE_INVISIBLE_RETRY_KEY: {
            "boot_id": "boot-A",
            "level": 39,
            "policy_revision": _MAGIC_SHOP_SEE_INVISIBLE_RETRY_REVISION,
            "status": "pending",
        },
    }

    assert not _magic_shop_see_invisible_failure_active(state)
    policy = _source_ranked_visibility_preparation_policy(
        selected,
        SimpleNamespace(requires_detect_invisibility=True),
        state,
        character_level=39,
        can_prepare=True,
    )

    assert policy is not None
    assert policy.execution == "buy-see-invisible"
    assert state[_MAGIC_SHOP_SEE_INVISIBLE_RETRY_KEY]["status"] == "attempted"
    assert _magic_shop_see_invisible_failure_active(state)


def test_unaffordable_visibility_preparation_switches_to_bounded_funding():
    selected = ProgressionPolicy(
        policy_id="source-ranked-hunt-test-903-947-39",
        minimum_level=39,
        maximum_level=39,
        status="research",
        execution="source-ranked-hunt",
        summary="hunt",
        evidence=(),
        practice_skill=None,
    )
    state = {
        "level": 39,
        "world_boot_id": "boot-A",
        "affects": [],
        "currencies": {
            "platinum": 0,
            "gold": 2,
            "electrum": 0,
            "silver": 0,
            "copper": 8,
        },
        _MAGIC_SHOP_SEE_INVISIBLE_PRICE_KEY: 254,
        "magic_shop_see_invisible_price_boot_id": "boot-A",
        "magic_shop_see_invisible_purchase_failed": True,
        "magic_shop_see_invisible_purchase_failed_boot": "boot-A",
    }

    policy = _source_ranked_visibility_preparation_policy(
        selected,
        SimpleNamespace(requires_detect_invisibility=True),
        state,
        character_level=39,
        can_prepare=True,
    )

    assert policy is not None
    assert policy.execution == "provision-funding"
    assert state[_SEE_INVISIBLE_FUNDING_REQUIRED_KEY] is True


def test_rejected_visibility_research_does_not_trigger_funding():
    selected = ProgressionPolicy(
        policy_id="source-ranked-hunt-test-25000-25011-41",
        minimum_level=41,
        maximum_level=41,
        status="research",
        execution="source-ranked-hunt",
        summary="research",
        evidence=(),
        practice_skill=None,
    )
    state = {
        "level": 41,
        "world_boot_id": "boot-A",
        "affects": [],
        "currencies": {"gold": 1, "silver": 6, "copper": 5},
        _MAGIC_SHOP_SEE_INVISIBLE_PRICE_KEY: 254,
        "magic_shop_see_invisible_price_boot_id": "boot-A",
    }

    policy = _source_ranked_visibility_preparation_policy(
        selected,
        SimpleNamespace(status="reject", requires_detect_invisibility=True),
        state,
        character_level=41,
        can_prepare=True,
    )

    assert policy is None
    assert _SEE_INVISIBLE_FUNDING_REQUIRED_KEY not in state


def test_visibility_retry_repair_recovers_same_boot_quote_and_funding():
    class StorageStub:
        def list_campaign_segments(self, campaign_id: int):
            return [{
                "phase": "buy-see-invisible-potion",
                "status": "success",
                "run_id": 22,
                "start_state_json": json.dumps({"world_boot_id": "boot-A"}),
                "end_state_json": json.dumps({
                    "world_boot_id": "boot-A",
                    "magic_shop_see_invisible_price": None,
                }),
            }]

        def get_latest_run_state_event(self, run_id: int, *, states):
            assert run_id == 22
            return {
                "payload_json": json.dumps({
                    "state": "completed",
                    "world_boot_id": None,
                    "magic_shop_see_invisible_price": 254,
                    "magic_shop_see_invisible_stock": 11,
                }),
            }

    state = {
        "level": 39,
        "world_boot_id": "boot-A",
        "magic_shop_see_invisible_purchase_failed": True,
        "magic_shop_see_invisible_purchase_failed_boot": "boot-A",
        "currencies": {
            "platinum": 0,
            "gold": 3,
            "silver": 0,
            "copper": 0,
        },
    }

    repaired = _repair_observed_see_invisible_state(StorageStub(), 8, state)

    assert repaired["magic_shop_see_invisible_price"] == 254
    assert repaired["magic_shop_see_invisible_price_boot_id"] == "boot-A"
    assert repaired["magic_shop_see_invisible_stock"] == 11
    assert repaired[_MAGIC_SHOP_SEE_INVISIBLE_RETRY_KEY]["status"] == "pending"


def test_visibility_failure_repair_keeps_quote_and_arms_funding_from_ready_segment():
    class StorageStub:
        def list_campaign_segments(self, campaign_id: int):
            return [{
                "phase": "buy-see-invisible-potion",
                "status": "ready",
                "end_state_json": json.dumps({
                    "world_boot_id": "boot-A",
                    _MAGIC_SHOP_SEE_INVISIBLE_PRICE_KEY: 254,
                    "magic_shop_see_invisible_price_boot_id": "boot-A",
                    "magic_shop_see_invisible_stock": 11,
                    "magic_shop_see_invisible_purchase_failed": True,
                }),
            }]

    repaired = _repair_observed_see_invisible_state(
        StorageStub(),
        8,
        {
            "level": 39,
            "world_boot_id": "boot-A",
            "magic_shop_see_invisible_purchase_failed": True,
            "magic_shop_see_invisible_purchase_failed_boot": "boot-A",
            "currencies": {
                "platinum": 0,
                "gold": 2,
                "electrum": 0,
                "silver": 0,
                "copper": 8,
            },
        },
    )

    assert repaired[_MAGIC_SHOP_SEE_INVISIBLE_PRICE_KEY] == 254
    assert repaired[_SEE_INVISIBLE_FUNDING_REQUIRED_KEY] is True


def test_visibility_retry_repair_discards_old_boot_quote():
    class StorageStub:
        def list_campaign_segments(self, campaign_id: int):
            return []

    state = {
        "level": 39,
        "world_boot_id": "boot-B",
        "magic_shop_see_invisible_price": 254,
        "magic_shop_see_invisible_price_boot_id": "boot-A",
        "magic_shop_see_invisible_stock": 11,
    }

    repaired = _repair_observed_see_invisible_state(StorageStub(), 8, state)

    assert "magic_shop_see_invisible_price" not in repaired
    assert "magic_shop_see_invisible_price_boot_id" not in repaired
    assert "magic_shop_see_invisible_stock" not in repaired
