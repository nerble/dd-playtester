from pathlib import Path

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
