import json
from dataclasses import replace
from pathlib import Path

from dd4tester.campaign import (
    _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY,
    _CAERLIN_STAFF_RESERVE_REACQUISITION_KEY,
    _SOURCE_RANKED_SANCTUARY_ALTERNATE_POLICY,
    _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY,
    _campaign_segment_end_state,
    _caerlin_staff_handoff_repair_allowed,
    _caerlin_staff_locator_revalidation_allowed,
    _caerlin_staff_locator_retry_allowed,
    _caerlin_staff_reserve_reacquisition_allowed,
    _caerlin_staff_retry_open,
    _select_source_ranked_alternate_sanctuary_candidate,
    _select_source_consumable_candidate,
    _source_caerlin_staff_candidate_shape_allowed,
    _source_ranked_healer_blindness_recovery_allowed,
    _source_ranked_hunt_stops,
    _source_sanctuary_carrier_output_allowed,
)
from dd4tester.encounters import active_encounter_budget
from dd4tester.hunt_candidates import SourceCombatOutput, load_world_source
from dd4tester.starter import StarterPolicy


SOURCE_DIRECTORY = Path("runs/dd4-source/server/area")


def _level_39_healer_state() -> dict[str, object]:
    return {
        "level": 39,
        "hp": 918,
        "max_hp": 918,
        "mana": 500,
        "max_mana": 500,
        "room_vnum": "3054",
        "alignment": 1000,
        "character_class": "warrior",
        "subclass": "knight",
        "affects": (),
        "campaign_known_skills": (
            "armed combat knowledge",
            "armor",
            "defense knowledge",
            "dodge",
            "enhanced damage",
            "headbutt",
            "kick",
            "parry",
            "second attack",
            "shield block",
            "stun",
            "third attack",
            "unarmed combat knowledge",
        ),
        "campaign_known_skill_levels": {
            "enhanced damage": 68,
            "headbutt": 68,
            "kick": 68,
            "parry": 65,
            "second attack": 64,
            "stun": 68,
            "third attack": 63,
        },
        "equipment": [
            {
                "vnum": 20508,
                "item_type": 5,
                "name": "a bishop piece",
                "keywords": "bishop",
                "wear_loc": 16,
                "slot": "wield",
                "level": 36,
            }
        ],
        "currencies": {
            "platinum": 0,
            "gold": 4,
            "silver": 0,
            "copper": 1,
            "electrum": 0,
        },
        "world_boot_id": "test-boot",
    }


def test_caerlin_is_selected_as_exact_staff_recovery_carrier() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()

    selection = _select_source_consumable_candidate(
        state,
        spell_name="sanctuary",
        short_description=None,
        source_directory=SOURCE_DIRECTORY,
        source_world=world,
        require_unarmed=True,
        required_reset=(19004, 19068),
    )

    assert selection is not None
    candidate, object_vnums = selection
    assert (candidate.mobile_vnum, candidate.room_vnum) == (19004, 19068)
    assert object_vnums == (19173,)
    assert _source_caerlin_staff_candidate_shape_allowed(candidate, world)
    assert candidate.route_economic_hunt_mobile_vnums == (19036,)
    assert candidate.autonomy_rejections == (
        "target has special procedure spec_cast_cleric",
    )
    assert _source_ranked_healer_blindness_recovery_allowed(
        candidate,
        state,
        source_world=world,
    )
    assert _source_sanctuary_carrier_output_allowed(
        candidate,
        state,
        policy_id=_SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id,
        character_level=39,
        source_world=world,
    )


def test_alternate_sanctuary_carrier_stays_closed_after_same_boot_absence() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    state["campaign_source_revision"] = "test-source"
    state["campaign_research_results"] = {
        "source-ranked-hunt-olympus-916-927-39": {
            "boot_id": "test-boot",
            "absent": True,
            "observed": False,
            "viable": False,
        }
    }

    assert (
        _select_source_ranked_alternate_sanctuary_candidate(
            state,
            source_directory=SOURCE_DIRECTORY,
            source_world=world,
        )
        is None
    )


def test_alternate_sanctuary_carrier_stays_closed_without_boot_boundary() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    state.pop("world_boot_id")
    state["campaign_source_revision"] = "test-source"
    state["campaign_research_results"] = {
        "source-ranked-hunt-olympus-916-927-39": {
            "absent": True,
            "observed": False,
            "viable": False,
        }
    }

    assert (
        _select_source_ranked_alternate_sanctuary_candidate(
            state,
            source_directory=SOURCE_DIRECTORY,
            source_world=world,
        )
        is None
    )


def test_alternate_sanctuary_carrier_reopens_after_reboot() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    state["campaign_source_revision"] = "test-source"
    state["world_boot_id"] = "next-boot"
    state["campaign_research_results"] = {
        "source-ranked-hunt-olympus-916-927-39": {
            "boot_id": "previous-boot",
            "absent": True,
            "observed": False,
            "viable": False,
        }
    }

    selection = _select_source_ranked_alternate_sanctuary_candidate(
        state,
        source_directory=SOURCE_DIRECTORY,
        source_world=world,
    )

    assert selection is not None
    candidate, object_vnums = selection
    assert (candidate.mobile_vnum, candidate.room_vnum) == (916, 927)
    assert object_vnums == (905, 926)
    assert _SOURCE_RANKED_SANCTUARY_ALTERNATE_POLICY.execution == (
        "moria-sanctuary-hunt"
    )


def test_caerlin_recovery_stop_is_unprotected_but_healer_backed() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    candidate, _object_vnums = _select_source_consumable_candidate(
        state,
        spell_name="sanctuary",
        short_description=None,
        source_directory=SOURCE_DIRECTORY,
        source_world=world,
        require_unarmed=True,
        required_reset=(19004, 19068),
    )
    assert candidate is not None

    stops = _source_ranked_hunt_stops(
        candidate,
        world,
        character_level=39,
        state=state,
    )
    locator = next(stop for stop in stops if stop.where_target == "caerlin")
    endpoint = next(
        stop
        for stop in stops
        if stop.target is not None and "19068" in stop.route_vnums
    )

    assert locator.actions == ("where caerlin",)
    assert locator.where_source_mobile_vnum == 19004
    assert dict(locator.where_location_routes)["the path"] == ("19002",)
    assert any(
        origin == "19068"
        and label == "the path"
        and route
        and route[-1] == "19002"
        for origin, label, route in locator.where_relocation_routes
    )
    assert endpoint.source_mobile_vnum == 19004
    assert endpoint.require_sanctuary is False
    assert endpoint.allow_source_caerlin_special_endpoint is True
    assert endpoint.allow_healer_blindness_recovery is True
    assert endpoint.source_specials == ("spec_cast_cleric",)
    assert endpoint.outbound_intercept_room_vnums == ("19002",)


def test_caerlin_staff_special_follows_the_wanderer_through_opened_doors() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    state = _level_39_healer_state()
    candidate, _object_vnums = _select_source_consumable_candidate(
        state,
        spell_name="sanctuary",
        short_description=None,
        source_directory=SOURCE_DIRECTORY,
        source_world=world,
        require_unarmed=True,
        required_reset=(19004, 19068),
    )
    assert candidate is not None
    endpoint = next(
        stop
        for stop in _source_ranked_hunt_stops(
            candidate,
            world,
            character_level=39,
            state=state,
        )
        if stop.target is not None and "19068" in stop.route_vnums
    )
    policy = StarterPolicy.__new__(StarterPolicy)
    policy.source_world = world
    endpoint = replace(endpoint, source_loot_object_vnums=())

    assert policy._source_stop_has_caerlin_staff_special(endpoint)
    assert policy._source_stop_has_caerlin_staff_special(
        endpoint,
        room_vnum="19002",
    )
    assert policy._source_stop_has_caerlin_staff_special(
        endpoint,
        room_vnum="19003",
    )
    assert not policy._source_stop_has_caerlin_staff_special(
        endpoint,
        room_vnum="3001",
    )


def test_live_budget_requires_the_exact_caerlin_allowlist() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    output = SourceCombatOutput(
        action="weapon strike",
        minimum_damage=40,
        expected_damage=70,
        maximum_damage=100,
        resource="actions",
        resource_cost=0,
        conservative_damage=56,
    )
    enemy = {
        "isnpc": "19004",
        "level": 35,
        "hp": 600,
        "maxhp": 600,
    }
    common = dict(
        world=world,
        enemies=(enemy,),
        character_level=39,
        hp=918,
        max_hp=918,
        mana=500,
        max_mana=500,
        output=output,
        target_hp_evidence_only=True,
        maximum_level_offsets_by_vnum={19004: 1},
    )

    rejected = active_encounter_budget(**common)
    accepted = active_encounter_budget(
        **common,
        allowed_caerlin_special_vnums=(19004,),
    )

    assert rejected.allowed is False
    assert "separate source-hazard" in rejected.reason
    assert accepted.allowed is True


def test_caerlin_locator_miss_is_persisted_and_allows_one_retry() -> None:
    previous = _level_39_healer_state()
    previous.update(
        {
            "campaign_source_revision": "test-source",
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "attempted",
                "retry_count": 0,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
            },
        }
    )
    current = {
        **previous,
        _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: None,
        "campaign_fastwalk_abort_reason": (
            "positive `where` result remains in the already-checked room "
            "with no unsearched source-safe relocation"
        ),
        "campaign_fastwalk_target_present_observed": True,
        "campaign_fastwalk_target_absent": False,
        "campaign_fastwalk_source_absent_sightings": [
            {"target": "caerlin", "room_vnum": "19061"}
        ],
        "campaign_fastwalk_where_decisions": [
            {
                "source_mobile_vnum": 19004,
                "target": "caerlin",
                "locations": ["bend in the path"],
            }
        ],
        "campaign_objective_kills": [],
        "campaign_completed_kills": [],
    }

    merged = _campaign_segment_end_state(
        previous,
        current,
        execution="moria-sanctuary-hunt",
        policy_id=_SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id,
    )

    assert merged[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY]["retry_count"] == 0
    assert _caerlin_staff_locator_retry_allowed(merged)
    merged["campaign_fastwalk_abort_reason"] = (
        "refreshed `where` located the wandering target outside the "
        "source-safe relocation graph"
    )
    assert _caerlin_staff_locator_retry_allowed(merged)


def test_caerlin_locator_retry_closes_after_second_miss() -> None:
    previous = _level_39_healer_state()
    previous.update(
        {
            "campaign_source_revision": "test-source",
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "attempted",
                "retry_count": 1,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
            },
        }
    )
    current = {
        **previous,
        "campaign_fastwalk_route": "source sanctuary reserve caerlin 19068",
    }

    merged = _campaign_segment_end_state(
        previous,
        current,
        execution="moria-sanctuary-hunt",
        policy_id=_SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id,
    )

    marker = merged[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY]
    assert marker["status"] == "closed"
    assert marker["outcome"] == "locator_retry_missed"
    assert not _caerlin_staff_locator_retry_allowed(merged)


def test_closed_caerlin_attempt_stays_closed_for_same_boot_and_source() -> None:
    state = _level_39_healer_state()
    attempt = {
        "boot_id": "test-boot",
        "level": 39,
        "source_revision": "test-source",
        "status": "closed",
    }

    assert not _caerlin_staff_retry_open(
        {**state, "campaign_source_revision": "test-source"},
        attempt,
        locator_retry=False,
        handoff_repair=False,
    )
    assert _caerlin_staff_retry_open(
        {**state, "campaign_source_revision": "new-source"},
        attempt,
        locator_retry=False,
        handoff_repair=False,
    )


def test_caerlin_staff_can_be_reacquired_once_after_liquidation_loss() -> None:
    state = _level_39_healer_state()
    state.update(
        {
            "campaign_source_revision": "test-source",
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "succeeded",
                "outcome": "staff_acquired",
                "retry_count": 1,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
            },
            "campaign_source_resource_reserves": {},
            "inventory": "[ { \"short_desc\": \"a leather jerkin\" } ]",
        }
    )

    assert _caerlin_staff_reserve_reacquisition_allowed(state)
    state[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY][
        _CAERLIN_STAFF_RESERVE_REACQUISITION_KEY
    ] = True
    assert not _caerlin_staff_reserve_reacquisition_allowed(state)


def test_caerlin_reacquisition_handoff_reopens_after_pre_dispatch_return_home() -> None:
    state = _level_39_healer_state()
    state.update(
        {
            "campaign_source_revision": "test-source",
            "inventory": "[ { \"short_desc\": \"a leather jerkin\" } ]",
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "attempted",
                "retry_count": 0,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
                _CAERLIN_STAFF_RESERVE_REACQUISITION_KEY: True,
            },
        }
    )
    prior = dict(state[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY])
    segments = [
        {
            "phase": "return-home",
            "status": "success",
            "start_state_json": json.dumps(
                {_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: prior}
            ),
            "end_state_json": json.dumps(
                {
                    "world_boot_id": "test-boot",
                    "level": 39,
                    "fastwalk_route": None,
                    "campaign_source_resource_reserve": None,
                    "campaign_source_consumable_candidate": None,
                    "campaign_source_consumable_object_vnums": None,
                    "campaign_died_during_segment": False,
                    "xp_loss_observed": False,
                    "campaign_objective_kills": [],
                    "campaign_completed_kills": [],
                    "inventory": "[ { \"short_desc\": \"a leather jerkin\" } ]",
                }
            ),
        }
    ]

    assert _caerlin_staff_handoff_repair_allowed(state, segments)
    state[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY]["handoff_repair_consumed"] = True
    assert not _caerlin_staff_handoff_repair_allowed(state, segments)


def test_closed_caerlin_locator_miss_allows_one_source_map_revalidation() -> None:
    state = _level_39_healer_state()
    state.update(
        {
            "campaign_source_revision": "test-source",
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "closed",
                "outcome": "locator_retry_missed",
                "retry_count": 1,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
            },
        }
    )

    assert _caerlin_staff_locator_revalidation_allowed(state)
    state[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY][
        "locator_revalidation_revision"
    ] = 3
    assert not _caerlin_staff_locator_revalidation_allowed(state)


def test_caerlin_handoff_repair_only_reopens_a_non_caerlin_moria_dispatch() -> None:
    state = _level_39_healer_state()
    state.update(
        {
            "campaign_source_revision": "test-source",
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "attempted",
                "retry_count": 0,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
            },
        }
    )
    prior = dict(state[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY])
    segments = [
        {
            "phase": _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id,
            "start_state_json": json.dumps(
                {_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: prior}
            ),
            "end_state_json": json.dumps(
                {
                    "world_boot_id": "test-boot",
                    "level": 39,
                    "fastwalk_route": "moria",
                    "campaign_source_resource_reserve": None,
                    "campaign_source_consumable_candidate": None,
                    "campaign_source_consumable_object_vnums": None,
                }
            ),
        }
    ]

    assert _caerlin_staff_handoff_repair_allowed(state, segments)
    state[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY] = {
        **prior,
        "handoff_repair_consumed": True,
    }
    assert not _caerlin_staff_handoff_repair_allowed(state, segments)


def test_caerlin_handoff_repair_reopens_pre_dispatch_interruption() -> None:
    state = _level_39_healer_state()
    state.update(
        {
            "campaign_source_revision": "test-source",
            _CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: {
                "boot_id": "test-boot",
                "level": 39,
                "source_revision": "test-source",
                "status": "attempted",
                "retry_count": 0,
                "mobile_vnum": 19004,
                "room_vnum": 19068,
                "object_vnums": [19173],
            },
        }
    )
    prior = dict(state[_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY])
    segments = [
        {
            "phase": _SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id,
            "status": "ready",
            "execution_status": "interrupted",
            "start_state_json": json.dumps(
                {_CAERLIN_STAFF_RECOVERY_ATTEMPT_KEY: prior}
            ),
            "end_state_json": json.dumps(
                {
                    "world_boot_id": "test-boot",
                    "level": 39,
                    "room_vnum": "3001",
                    "fastwalk_route": None,
                    "campaign_source_consumable_candidate": None,
                    "campaign_source_consumable_object_vnums": None,
                }
            ),
        }
    ]

    assert _caerlin_staff_handoff_repair_allowed(state, segments)
