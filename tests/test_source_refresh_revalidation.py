from pathlib import Path
from types import SimpleNamespace

import dd4tester.campaign as campaign_module
from dd4tester.hunt_candidates import load_world_source, rank_hunt_candidates


SOURCE = Path("runs/dd4-source/server/area")


def _candidate_and_world():
    world = load_world_source(SOURCE, include_all_areas=True)
    candidates = rank_hunt_candidates(
        world,
        character_level=39,
        character_class="warrior",
        character_subclass="knight",
        include_xp_only=True,
        include_level_ceiling_candidates=True,
        level_ceiling_offset=5,
        include_all_areas=True,
        character_max_hp=927,
        character_alignment=100,
        recall_origins={0: 3001},
    )
    candidate = next(
        item
        for item in candidates
        if item.mobile_vnum == 20513 and item.room_vnum == 20532
    )
    return candidate, world


def _other_plain_candidate(world):
    candidates = rank_hunt_candidates(
        world,
        character_level=39,
        character_class="warrior",
        character_subclass="knight",
        include_xp_only=True,
        include_level_ceiling_candidates=True,
        level_ceiling_offset=5,
        include_all_areas=True,
        character_max_hp=927,
        character_alignment=100,
        recall_origins={0: 3001},
    )
    return next(
        item
        for item in candidates
        if item.mobile_vnum == 917 and item.room_vnum == 936
    )


def _hermes_candidate_and_world():
    world = load_world_source(SOURCE, include_all_areas=True)
    candidates = rank_hunt_candidates(
        world,
        character_level=39,
        character_class="warrior",
        character_subclass="knight",
        include_xp_only=True,
        include_level_ceiling_candidates=True,
        level_ceiling_offset=5,
        include_all_areas=True,
        character_max_hp=927,
        character_alignment=100,
        recall_origins={0: 3001},
    )
    candidate = next(
        item
        for item in candidates
        if item.mobile_vnum == 903 and item.room_vnum == 947
    )
    return candidate, world


def _hephaestus_candidate_and_world():
    world = load_world_source(SOURCE, include_all_areas=True)
    candidates = rank_hunt_candidates(
        world,
        character_level=39,
        character_class="warrior",
        character_subclass="knight",
        include_xp_only=True,
        include_level_ceiling_candidates=True,
        level_ceiling_offset=5,
        include_all_areas=True,
        character_max_hp=927,
        character_alignment=100,
        recall_origins={0: 3001},
    )
    candidate = next(
        item
        for item in candidates
        if item.mobile_vnum == 908 and item.room_vnum == 937
    )
    return candidate, world


def _cave_beast_candidate_and_world():
    world = load_world_source(SOURCE, include_all_areas=True)
    candidates = rank_hunt_candidates(
        world,
        character_level=39,
        character_class="warrior",
        character_subclass="knight",
        include_xp_only=True,
        include_level_ceiling_candidates=True,
        level_ceiling_offset=5,
        include_all_areas=True,
        character_max_hp=937,
        character_alignment=-266,
        recall_origins={0: 3001},
    )
    candidate = next(
        item
        for item in candidates
        if item.mobile_vnum == 9936 and item.room_vnum == 9951
    )
    return candidate, world


def _orca_candidate_and_world():
    world = load_world_source(SOURCE, include_all_areas=True)
    candidates = rank_hunt_candidates(
        world,
        character_level=39,
        character_class="warrior",
        character_subclass="knight",
        include_xp_only=True,
        include_level_ceiling_candidates=True,
        level_ceiling_offset=5,
        include_all_areas=True,
        character_max_hp=937,
        character_alignment=208,
        recall_origins={0: 3001},
    )
    candidate = next(
        item
        for item in candidates
        if item.mobile_vnum == 17051 and item.room_vnum == 17272
    )
    return candidate, world


def _state(candidate, *, source_revision: str = "new-source") -> dict:
    policy_id = campaign_module._source_ranked_policy_id(
        candidate,
        character_level=39,
    )
    return {
        "world_boot_id": "boot-current",
        campaign_module._SOURCE_REVISION_KEY: source_revision,
        "level": 39,
        "max_hp": 927,
        "character_class": "warrior",
        campaign_module._SOURCE_RANKED_XP_LOSS_POLICIES_KEY: [
            {
                "boot_id": "boot-current",
                "level": 39,
                "loss_count": 2,
                "loss_event_id": 17507,
                "policy_id": policy_id,
                "source_revision": "old-source",
                "exact_stop_loss": True,
                "xp_delta": 1587,
            }
        ],
    }


def test_source_refresh_receipt_requires_a_changed_revision_and_exact_plain_target():
    candidate, world = _candidate_and_world()
    state = _state(candidate)

    receipt = campaign_module._source_ranked_source_refresh_revalidation_receipt(
        candidate,
        state,
        character_level=39,
        source_world=world,
    )

    assert receipt is not None
    assert receipt["policy_id"].endswith("dwarven-home-20513-20532-39")
    assert receipt["prior_source_revision"] == "old-source"
    assert receipt["source_revision"] == "new-source"
    assert receipt["status"] == "pending"
    assert state[campaign_module._SOURCE_RANKED_XP_LOSS_POLICIES_KEY][0][
        "loss_count"
    ] == 2

    assert (
        campaign_module._source_ranked_source_refresh_revalidation_receipt(
            candidate,
            _state(candidate, source_revision="old-source"),
            character_level=39,
            source_world=world,
        )
        is None
    )


def test_source_refresh_reopens_plain_singleton_after_historical_boot_kill_cap():
    candidate, world = _candidate_and_world()
    candidate = campaign_module.replace(candidate, boot_kills=6)
    state = _state(candidate)

    receipt = campaign_module._source_ranked_source_refresh_revalidation_receipt(
        candidate,
        state,
        character_level=39,
        source_world=world,
    )

    assert receipt is not None
    assert receipt["source_refresh"] is True
    assert receipt["prior_loss"]["loss_count"] == 2


def test_source_refresh_keeps_new_targets_open_after_eight_other_audits():
    candidate, world = _candidate_and_world()
    state = _state(candidate)
    state[campaign_module._SOURCE_RANKED_SOURCE_REFRESH_HISTORY_KEY] = [
        {
            "boot_id": "boot-current",
            "level": 39,
            "policy_id": f"source-ranked-hunt-other-{index}-39",
            "source_revision": "new-source",
            "status": "closed",
        }
        for index in range(8)
    ]

    receipt = campaign_module._source_ranked_source_refresh_revalidation_receipt(
        candidate,
        state,
        character_level=39,
        source_world=world,
    )

    assert receipt is not None
    assert receipt["policy_id"].endswith("dwarven-home-20513-20532-39")


def test_source_refresh_allows_one_third_loss_for_a_plain_singleton():
    candidate, world = _candidate_and_world()
    state = _state(candidate)
    state[campaign_module._SOURCE_RANKED_XP_LOSS_POLICIES_KEY][0][
        "loss_count"
    ] = 3

    receipt = campaign_module._source_ranked_source_refresh_revalidation_receipt(
        candidate,
        state,
        character_level=39,
        source_world=world,
    )

    assert receipt is not None
    assert receipt["prior_loss"]["loss_count"] == 3
    assert receipt["special_source_refresh"] is False


def test_source_refresh_reopens_only_one_exact_candidate_and_is_one_shot():
    candidate, world = _candidate_and_world()
    state = _state(candidate)
    policy_id = campaign_module._source_ranked_policy_id(
        candidate,
        character_level=39,
    )
    receipt = campaign_module._source_ranked_source_refresh_revalidation_receipt(
        candidate,
        state,
        character_level=39,
        source_world=world,
    )
    assert receipt is not None

    assert campaign_module._source_ranked_candidate_blocked_by_protection_recovery(
        candidate,
        state,
        character_level=39,
        character_max_hp=927,
        allow_protection_recovery_fallback=True,
        source_world=world,
    ) is True

    state[campaign_module._SOURCE_RANKED_SOURCE_REFRESH_REVALIDATION_KEY] = receipt
    state[campaign_module._SOURCE_RANKED_REVALIDATION_POLICY_KEY] = policy_id
    assert campaign_module._source_ranked_candidate_blocked_by_protection_recovery(
        candidate,
        state,
        character_level=39,
        character_max_hp=927,
        allow_protection_recovery_fallback=True,
        source_world=world,
    ) is False

    selected = campaign_module._select_source_ranked_hunt_candidate(
        (candidate,),
        state,
        world=world,
        character_level=39,
        character_max_hp=927,
        allow_retry_exhausted_repeat=True,
        allow_protection_recovery_fallback=True,
        allow_repeated_policy_ids=(policy_id,),
    )
    assert selected == candidate

    state[campaign_module._SOURCE_RANKED_SOURCE_REFRESH_REVALIDATION_KEY] = {
        **receipt,
        "status": "attempted",
        "attempted": True,
    }
    assert campaign_module._source_ranked_candidate_blocked_by_protection_recovery(
        candidate,
        state,
        character_level=39,
        character_max_hp=927,
        allow_protection_recovery_fallback=True,
        source_world=world,
    ) is True


def test_source_refresh_audits_are_per_target_after_one_target_closes():
    candidate, world = _candidate_and_world()
    other = _other_plain_candidate(world)
    state = _state(candidate)
    other_policy_id = campaign_module._source_ranked_policy_id(
        other,
        character_level=39,
    )
    state[campaign_module._SOURCE_RANKED_XP_LOSS_POLICIES_KEY].append(
        {
            "boot_id": "boot-current",
            "level": 39,
            "loss_count": 1,
            "loss_event_id": 19001,
            "policy_id": other_policy_id,
            "source_revision": "old-source",
            "exact_stop_loss": True,
            "xp_delta": -549,
        }
    )
    state["affects"] = [[{"name": "fly", "duration": "18"}]]
    state[campaign_module._MAGIC_SHOP_FLIGHT_PRICE_KEY] = 108
    state[campaign_module._MAGIC_SHOP_FLIGHT_PRICE_BOOT_KEY] = "boot-current"
    first = campaign_module._source_ranked_source_refresh_revalidation_receipt(
        candidate,
        state,
        character_level=39,
        source_world=world,
    )
    assert first is not None
    state[campaign_module._SOURCE_RANKED_SOURCE_REFRESH_REVALIDATION_KEY] = {
        **first,
        "status": "closed",
    }

    second = campaign_module._source_ranked_source_refresh_revalidation_receipt(
        other,
        state,
        character_level=39,
        source_world=world,
    )

    assert second is not None
    assert second["policy_id"] == other_policy_id


def test_source_refresh_allows_one_plain_wandering_invisible_target():
    candidate, world = _hermes_candidate_and_world()
    state = _state(candidate)
    state["affects"] = [{"name": "fly", "duration": "18"}]
    state[campaign_module._MAGIC_SHOP_FLIGHT_PRICE_KEY] = 108
    state[campaign_module._MAGIC_SHOP_FLIGHT_PRICE_BOOT_KEY] = "boot-current"

    receipt = campaign_module._source_ranked_source_refresh_revalidation_receipt(
        candidate,
        state,
        character_level=39,
        source_world=world,
    )

    assert receipt is not None
    assert receipt["policy_id"].endswith("olympus-903-947-39")
    assert candidate.sentinel is False
    assert candidate.requires_detect_invisibility is True


def test_source_refresh_allows_only_the_exact_hephaestus_lightning_retry():
    candidate, world = _hephaestus_candidate_and_world()
    state = _state(candidate)
    state["combat_pouch_potions"] = {"purple": 1}
    state["affects"] = [{"name": "fly", "duration": "18"}]
    state[campaign_module._MAGIC_SHOP_FLIGHT_PRICE_KEY] = 108
    state[campaign_module._MAGIC_SHOP_FLIGHT_PRICE_BOOT_KEY] = "boot-current"

    receipt = campaign_module._source_ranked_source_refresh_revalidation_receipt(
        candidate,
        state,
        character_level=39,
        source_world=world,
    )

    assert receipt is not None
    assert receipt["special_source_refresh"] is True
    assert receipt["revision"] == 2
    assert receipt["policy_id"].endswith("olympus-908-937-39")
    assert "Hephaestus lightning retry" in receipt["reason"]
    assert state[campaign_module._SOURCE_RANKED_XP_LOSS_POLICIES_KEY][0][
        "loss_count"
    ] == 2


def test_source_refresh_allows_one_plain_aggressive_current_band_retry():
    candidate, world = _cave_beast_candidate_and_world()
    state = _state(candidate)

    assert campaign_module._source_ranked_plain_aggressive_current_band_fallback_allowed(
        candidate,
        state,
        character_level=39,
        character_max_hp=927,
        source_world=world,
    ) is True

    receipt = campaign_module._source_ranked_source_refresh_revalidation_receipt(
        candidate,
        state,
        character_level=39,
        source_world=world,
    )

    assert receipt is not None
    assert receipt["mobile_vnum"] == 9936
    assert receipt["room_vnum"] == 9951
    assert receipt["special_source_refresh"] is False
    assert "plain current-band retry" in receipt["reason"]


def test_source_refresh_reaudits_legacy_success_after_source_revision_change():
    candidate, world = _cave_beast_candidate_and_world()
    state = _state(candidate)
    policy_id = campaign_module._source_ranked_policy_id(
        candidate,
        character_level=39,
    )
    state["campaign_research_results"] = {
        policy_id: {
            "boot_id": "boot-current",
            "completed_kill": True,
            "viable": True,
            "objective_xp": 3313,
            "source_revision": "old-source",
        }
    }

    receipt = campaign_module._source_ranked_source_refresh_revalidation_receipt(
        candidate,
        state,
        character_level=39,
        source_world=world,
    )

    assert receipt is not None
    assert receipt["prior_result"]["completed_kill"] is True


def test_source_refresh_does_not_replay_current_source_success():
    candidate, world = _cave_beast_candidate_and_world()
    state = _state(candidate)
    policy_id = campaign_module._source_ranked_policy_id(
        candidate,
        character_level=39,
    )
    state["campaign_research_results"] = {
        policy_id: {
            "boot_id": "boot-current",
            "completed_kill": True,
            "viable": True,
            "objective_xp": 3313,
            "source_revision": "new-source",
        }
    }

    assert (
        campaign_module._source_ranked_source_refresh_revalidation_receipt(
            candidate,
            state,
            character_level=39,
            source_world=world,
        )
        is None
    )


def test_route_level_invisibility_preparation_covers_visible_orca_route():
    candidate, world = _orca_candidate_and_world()
    state = {
        **_state(candidate),
        "affects": [],
        "room_vnum": "3054",
        "currencies": {"platinum": 0, "gold": 4, "silver": 11, "copper": 11},
        campaign_module._MAGIC_SHOP_SEE_INVISIBLE_PRICE_KEY: 254,
        campaign_module._MAGIC_SHOP_SEE_INVISIBLE_PRICE_BOOT_KEY: "boot-current",
    }

    policy = campaign_module._source_ranked_visibility_preparation_policy(
        SimpleNamespace(execution="source-ranked-hunt"),
        candidate,
        state,
        character_level=39,
        can_prepare=True,
        source_world=world,
    )

    assert policy is not None
    assert policy.execution == "buy-see-invisible"


def test_source_selector_can_handoff_hephaestus_to_visibility_preparation():
    candidate, world = _hephaestus_candidate_and_world()
    state = {
        "world_boot_id": "boot-current",
        campaign_module._SOURCE_REVISION_KEY: "new-source",
        "level": 39,
        "max_hp": 927,
        "character_class": "warrior",
        "affects": [],
        "combat_pouch_potions": {"purple": 1},
        "verified_combat_pouch_potions": {"purple": 1},
    }

    selected = campaign_module._select_source_ranked_hunt_candidate(
        (candidate,),
        state,
        world=world,
        character_level=39,
        character_max_hp=927,
        allow_detect_invisibility_preparation=True,
    )

    assert selected == candidate


def test_prior_level_loss_revalidation_reopens_audited_hephaestus_at_level_41():
    candidate, world = _hephaestus_candidate_and_world()
    policy_id = campaign_module._source_ranked_policy_id(
        candidate,
        character_level=41,
    )
    state = {
        "world_boot_id": "boot-current",
        campaign_module._SOURCE_REVISION_KEY: "new-source",
        "level": 41,
        "max_hp": 927,
        "character_class": "warrior",
        "affects": [{"name": "fly", "duration": "18"}],
        "campaign_source_resource_reserves": {
            "sanctuary": {
                "object_vnum": 7303,
                "effect": "sanctuary",
                "charges_remaining": 9,
                "mode": "staff",
            }
        },
        campaign_module._SOURCE_RANKED_XP_LOSS_POLICIES_KEY: [{
            "boot_id": "boot-current",
            "level": 40,
            "loss_count": 2,
            "loss_event_id": 19833,
            "policy_id": "source-ranked-hunt-olympus-908-937-40",
            "sanctuary_protected": True,
        }],
    }

    assert campaign_module._source_ranked_prior_level_loss_revalidation_allowed(
        candidate,
        state,
        character_level=41,
        character_max_hp=927,
        source_world=world,
    ) is True
    assert campaign_module._arm_source_ranked_prior_level_loss_revalidation(
        state,
        (candidate,),
        character_level=41,
        character_max_hp=927,
        source_world=world,
    ) is candidate
    assert state[
        campaign_module._SOURCE_RANKED_PRIOR_LEVEL_LOSS_REVALIDATION_KEY
    ]["policy_id"] == policy_id


def test_source_refresh_rearms_after_protection_only_preparation():
    candidate, world = _hephaestus_candidate_and_world()
    state = _state(candidate)
    state["combat_pouch_potions"] = {"purple": 1}
    state["affects"] = [
        {"name": "detect invis", "duration": "32"},
        {"name": "fly", "duration": "28"},
    ]
    receipt = campaign_module._source_ranked_source_refresh_revalidation_receipt(
        candidate,
        state,
        character_level=39,
        source_world=world,
    )
    assert receipt is not None
    state[campaign_module._SOURCE_RANKED_SOURCE_REFRESH_REVALIDATION_KEY] = {
        **receipt,
        "status": "attempted",
        "attempted": True,
    }
    state["campaign_last_policy"] = "buy-see-invisible-potion"

    assert (
        campaign_module._source_ranked_rearm_preparation_source_refresh_marker(
            state
        )
        is True
    )
    marker = state[campaign_module._SOURCE_RANKED_SOURCE_REFRESH_REVALIDATION_KEY]
    assert marker["status"] == "pending"
    assert marker["attempted"] is False
    assert marker["deferred_for_preparation"] is True


def test_source_refresh_pending_marker_closes_after_newer_loss_event():
    candidate, world = _hephaestus_candidate_and_world()
    state = _state(candidate)
    state["combat_pouch_potions"] = {"purple": 1}
    state["affects"] = [
        {"name": "detect invis", "duration": "32"},
        {"name": "fly", "duration": "28"},
    ]
    receipt = campaign_module._source_ranked_source_refresh_revalidation_receipt(
        candidate,
        state,
        character_level=39,
        source_world=world,
    )
    assert receipt is not None
    state[campaign_module._SOURCE_RANKED_SOURCE_REFRESH_REVALIDATION_KEY] = receipt
    state[campaign_module._SOURCE_RANKED_XP_LOSS_POLICIES_KEY][0] = {
        **state[campaign_module._SOURCE_RANKED_XP_LOSS_POLICIES_KEY][0],
        "loss_count": 3,
        "loss_event_id": 19002,
    }

    assert (
        campaign_module._source_ranked_reconcile_pending_source_refresh_marker(
            state
        )
        is True
    )
    marker = state[campaign_module._SOURCE_RANKED_SOURCE_REFRESH_REVALIDATION_KEY]
    assert marker["status"] == "closed"
    assert marker["outcome"] == "no_kill"
    assert "newer XP-loss" in marker["reason"]


def test_source_refresh_marker_is_consumed_at_field_dispatch():
    candidate, world = _hephaestus_candidate_and_world()
    state = _state(candidate)
    state["combat_pouch_potions"] = {"purple": 1}
    state["affects"] = [
        {"name": "detect invis", "duration": "32"},
        {"name": "fly", "duration": "28"},
    ]
    receipt = campaign_module._source_ranked_source_refresh_revalidation_receipt(
        candidate,
        state,
        character_level=39,
        source_world=world,
    )
    assert receipt is not None
    state[campaign_module._SOURCE_RANKED_SOURCE_REFRESH_REVALIDATION_KEY] = receipt
    selected = campaign_module.replace(
        campaign_module._SOURCE_RANKED_HUNT_POLICY,
        policy_id=receipt["policy_id"],
    )

    assert (
        campaign_module._source_ranked_mark_source_refresh_dispatch(
            state,
            selected,
            character_level=39,
        )
        is True
    )
    marker = state[campaign_module._SOURCE_RANKED_SOURCE_REFRESH_REVALIDATION_KEY]
    assert marker["status"] == "attempted"
    assert marker["attempted"] is True


def test_source_refresh_never_reopens_a_level_40_psionic_without_protection():
    world = load_world_source(SOURCE, include_all_areas=True)
    candidates = rank_hunt_candidates(
        world,
        character_level=39,
        character_class="warrior",
        character_subclass="knight",
        include_xp_only=True,
        include_level_ceiling_candidates=True,
        level_ceiling_offset=5,
        include_all_areas=True,
        character_max_hp=927,
        character_alignment=100,
        recall_origins={0: 3001},
    )
    candidate = next(item for item in candidates if item.mobile_vnum == 17514)
    state = _state(candidate)
    state["affects"] = [{"name": "fly", "duration": "18"}]
    state[campaign_module._MAGIC_SHOP_FLIGHT_PRICE_KEY] = 108
    state[campaign_module._MAGIC_SHOP_FLIGHT_PRICE_BOOT_KEY] = "boot-current"

    assert (
        campaign_module._source_ranked_source_refresh_revalidation_receipt(
            candidate,
            state,
            character_level=39,
            source_world=world,
        )
        is None
    )


def test_catacombs_source_refresh_reopens_one_old_loss_without_erasing_it():
    world = load_world_source(SOURCE, include_all_areas=True)
    current_revision = campaign_module._current_dd4_source_revision()
    assert current_revision
    source_policy_id = campaign_module._source_identity_policy_id(
        "vamp_catacombs.are", 9524, 9568, 39,
    )
    state = {
        "world_boot_id": "boot-current",
        "level": 39,
        "max_hp": 927,
        "affects": [{"name": "fly", "duration": "10"}],
        campaign_module._SOURCE_REVISION_KEY: current_revision,
        campaign_module._SOURCE_RANKED_XP_LOSS_POLICIES_KEY: [
            {
                "boot_id": "boot-current",
                "level": 39,
                "loss_count": 1,
                "loss_event_id": 17835,
                "policy_id": source_policy_id,
                "source_revision": "old-source",
                "exact_stop_loss": True,
                "xp_delta": -183,
            }
        ],
    }

    receipt = campaign_module._catacombs_source_refresh_revalidation_receipt(
        state,
        world,
        character_level=39,
        route_key_object_vnums=(9565,),
        source_mobile_vnums=campaign_module._VAMPIRE_CATACOMBS_LEVEL_38_40_POLICY.source_mobile_vnums,
    )

    assert receipt is not None
    mobile_vnum, marker = receipt
    assert mobile_vnum == 9524
    assert marker["source_policy_id"] == source_policy_id
    assert marker["prior_source_revision"] == "old-source"
    assert state[campaign_module._SOURCE_RANKED_XP_LOSS_POLICIES_KEY][0][
        "loss_count"
    ] == 1

    state[campaign_module._CATACOMBS_SOURCE_REFRESH_REVALIDATION_KEY] = {
        **marker,
        "status": "attempted",
        "attempted": True,
    }
    assert (
        campaign_module._catacombs_source_refresh_revalidation_receipt(
            state,
            world,
            character_level=39,
            route_key_object_vnums=(9565,),
            source_mobile_vnums=(9524,),
        )
        is None
    )


def test_catacombs_source_refresh_marker_is_finalized_after_target_kill():
    policy_id = campaign_module._VAMPIRE_CATACOMBS_LEVEL_38_40_POLICY.policy_id
    marker = {
        "boot_id": "boot-current",
        "level": 39,
        "policy_id": policy_id,
        "source_revision": "new-source",
        "mobile_vnum": 9545,
        "status": "attempted",
        "attempted": True,
    }
    kill = {
        "mob_name": "an art critic",
        "source_mobile_vnum": 9545,
        "source_policy_id": "source-ranked-hunt-vamp-catacombs-9545-9558-39",
        "xp_gained": 3870,
    }

    merged = campaign_module._campaign_segment_end_state(
        {
            "world_boot_id": "boot-current",
            "level": 39,
            "campaign_last_policy": policy_id,
            campaign_module._CATACOMBS_SOURCE_REFRESH_REVALIDATION_KEY: marker,
        },
        {
            "world_boot_id": "boot-current",
            "level": 39,
            "campaign_last_policy": policy_id,
        },
        execution="vampire-catacombs-hunt",
        policy_id=policy_id,
        objective_kills=[kill],
    )

    finalized = merged[
        campaign_module._CATACOMBS_SOURCE_REFRESH_REVALIDATION_KEY
    ]
    assert finalized["status"] == "succeeded"
    assert finalized["outcome"] == "completed_kill"
    assert merged[campaign_module._CATACOMBS_SOURCE_REFRESH_HISTORY_KEY][-1][
        "status"
    ] == "succeeded"
