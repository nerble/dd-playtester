from dataclasses import replace
from pathlib import Path

import dd4tester.campaign as campaign_module
from dd4tester.economic_hunts import economic_hunt_candidate
from dd4tester.hunt_candidates import load_world_source, rank_hunt_candidates
from dd4tester.campaign import (
    _source_ranked_area_circuit_route_admission_allowed,
    _source_ranked_hunt_stops,
)


SOURCE = Path("runs/dd4-source/server/area")


def _candidates():
    world = load_world_source(SOURCE, include_all_areas=True)
    candidates = rank_hunt_candidates(
        world,
        character_level=39,
        character_class="warrior",
        character_subclass="knight",
        character_alignment=-7,
        character_max_hp=937,
        include_xp_only=True,
        include_level_ceiling_candidates=True,
        level_ceiling_offset=5,
        include_all_areas=True,
        recall_origins={0: 3001},
    )
    return world, {
        (candidate.mobile_vnum, candidate.room_vnum): candidate
        for candidate in candidates
        if candidate.mobile_vnum in {19007, 19033, 19047}
    }


def _state(copper: int = 444):
    return {
        "world_boot_id": "test-boot",
        "character_class": "Warrior",
        "character_subclass": "Knight",
        "currencies": {"copper": copper, "silver": 0, "gold": 0, "platinum": 0},
        "hp": 937,
        "max_hp": 937,
        "combat_pouch_potions": {"purple": 1},
        "verified_combat_pouch_potions": {"purple": 1},
    }


def test_mirror_realm_plain_target_uses_exact_economic_transit_exception():
    world, candidates = _candidates()
    candidate = candidates[(19007, 19078)]

    assert campaign_module._source_ranked_mirror_realm_gardener_transit_allowed(
        candidate,
        _state(),
        character_level=39,
        character_max_hp=937,
        source_world=world,
    )
    assert _source_ranked_area_circuit_route_admission_allowed(
        candidate,
        world,
        {**_state(), "max_hp": 937},
        character_level=39,
    )
    assert campaign_module._select_source_ranked_hunt_candidate(
        (candidate,),
        _state(),
        world=world,
        character_level=39,
        character_max_hp=937,
    ) == candidate


def test_mirror_realm_transit_admits_exact_audited_king_mage_endpoint():
    world = load_world_source(
        SOURCE,
        include_all_areas=True,
        live_deployment=True,
    )
    state = {
        **_state(copper=444),
        "level": 45,
        "room_vnum": "3054",
        "character_alignment": -66,
        "affects": [],
    }
    candidate = next(
        candidate
        for candidate in rank_hunt_candidates(
            world,
            character_level=45,
            character_class="Warrior",
            character_subclass="Knight",
            character_alignment=-66,
            character_max_hp=937,
            include_xp_only=True,
            include_level_ceiling_candidates=True,
            level_ceiling_offset=5,
            include_all_areas=True,
            recall_origins={0: 3001},
        )
        if candidate.mobile_vnum == 19003 and candidate.room_vnum == 19020
    )

    assert candidate.specials == ("spec_cast_mage",)
    assert campaign_module._source_ranked_mirror_realm_gardener_transit_allowed(
        candidate,
        state,
        character_level=45,
        character_max_hp=937,
        source_world=world,
        allow_audited_special_target=True,
    )
    assert campaign_module._source_ranked_mirror_realm_endpoint_target_allowed(
        candidate,
        state,
        character_max_hp=937,
        source_world=world,
    )
    assert campaign_module._source_ranked_candidate_is_runtime_autonomous_safe(
        candidate,
        state,
        character_level=45,
        character_max_hp=937,
        source_world=world,
    )
    stops = _source_ranked_hunt_stops(
        candidate,
        world,
        character_level=45,
        state=state,
    )
    target_stop = next(stop for stop in stops if stop.target is not None)
    assert target_stop.allow_lucky_consider is True
    assert target_stop.maximum_level_offset == 5
    assert "built like a tank" not in target_stop.rejected_consider_fragments
    assert campaign_module._select_source_ranked_hunt_candidate(
        (candidate,),
        state,
        world=world,
        character_level=45,
        character_max_hp=937,
        allow_cooldown_retry=True,
        allow_low_probability_current_band=True,
        allow_retry_exhausted_repeat=True,
        allow_protection_recovery_fallback=True,
    ) == candidate


def test_mirror_realm_level_45_target_allows_bounded_midgaard_drunk_transit():
    world = load_world_source(
        SOURCE,
        include_all_areas=True,
        live_deployment=True,
    )
    state = {
        **_state(copper=53),
        "level": 45,
        "character_alignment": -210,
    }
    candidate = next(
        candidate
        for candidate in rank_hunt_candidates(
            world,
            character_level=45,
            character_class="Warrior",
            character_subclass="Knight",
            known_skills=("grip",),
            known_skill_levels={"grip": 99},
            character_alignment=-210,
            character_max_hp=1095,
            include_xp_only=True,
            include_level_ceiling_candidates=True,
            level_ceiling_offset=5,
            include_all_areas=True,
            recall_origins={0: 3001},
        )
        if candidate.mobile_vnum == 19069 and candidate.room_vnum == 19166
    )
    candidate = economic_hunt_candidate(candidate, state, world)

    route_rooms = campaign_module._source_route_room_vnums(
        world,
        candidate.route_origin_room_vnum,
        candidate.route,
    )
    candidate = replace(
        candidate,
        route_preflight_room_vnum="3001",
        route_preflight_command="where drunk",
        route_preflight_target="the drunk",
        route_preflight_source_mobile_vnum=3064,
        route_preflight_checks=(("where drunk", "the drunk"),),
        route_preflight_level_range=(1, 4),
        route_preflight_hard_hazard=True,
        route_preflight_route_room_names=tuple(
            world.rooms[room_vnum].name for room_vnum in route_rooms
        ),
        route_attack_program_mobile_vnums=(3064,),
        route_hazard_mobile_vnums=tuple(
            sorted({*candidate.route_hazard_mobile_vnums, 3064})
        ),
    )
    assert campaign_module._source_ranked_route_program_preflight_allowed(
        candidate,
        character_level=45,
        source_world=world,
    )
    assert campaign_module._source_ranked_mirror_realm_gardener_transit_allowed(
        candidate,
        state,
        character_level=45,
        character_max_hp=1095,
        source_world=world,
    )
    assert campaign_module._source_ranked_candidate_in_current_band(
        candidate,
        state,
        world=world,
        character_level=45,
        character_max_hp=1095,
        allow_relative_level_target=True,
    )


def test_mirror_realm_plain_storn_allows_equipped_thief_transit():
    world = load_world_source(
        SOURCE,
        include_all_areas=True,
        live_deployment=True,
    )
    state = {
        **_state(copper=53),
        "level": 45,
        "room_vnum": "3054",
        "character_alignment": -66,
        "affects": [],
    }
    candidate = next(
        candidate
        for candidate in rank_hunt_candidates(
            world,
            character_level=45,
            character_class="Warrior",
            character_subclass="Knight",
            character_alignment=-66,
            character_max_hp=1095,
            include_xp_only=True,
            include_level_ceiling_candidates=True,
            level_ceiling_offset=5,
            include_all_areas=True,
            recall_origins={0: 3001},
            route_economic_transit_allow_equipped_mobile_vnums=(
                *campaign_module._MIRROR_REALM_FIXED_ECONOMIC_TRANSIT_MOBILE_VNUMS,
            ),
        )
        if candidate.mobile_vnum == 19034 and candidate.room_vnum == 19114
    )

    assert set(candidate.route_special_mobile_vnums) == {
        19036, 19044, 19045, 19046, 19052, 19053,
    }
    assert candidate.autonomy_rejections == (
        "an economic special mobile can reach the route",
    )
    assert campaign_module._source_ranked_mirror_realm_gardener_transit_allowed(
        candidate,
        state,
        character_level=45,
        character_max_hp=1095,
        source_world=world,
    )
    assert campaign_module._source_ranked_candidate_in_current_band(
        candidate,
        state,
        world=world,
        character_level=45,
        character_max_hp=1095,
        allow_relative_level_target=True,
    )
    assert campaign_module._source_ranked_candidate_is_runtime_autonomous_safe(
        candidate,
        state,
        character_level=45,
        character_max_hp=1095,
        source_world=world,
    )
    assert campaign_module._select_source_ranked_hunt_candidate(
        (candidate,),
        state,
        world=world,
        character_level=45,
        character_max_hp=1095,
    ) == candidate


def test_mirror_realm_grey_mare_closes_corridor_for_hitroll_thief_loadout():
    world = load_world_source(
        SOURCE,
        include_all_areas=True,
        live_deployment=True,
    )
    candidate = next(
        candidate
        for candidate in rank_hunt_candidates(
            world,
            character_level=45,
            character_class="warrior",
            character_subclass="knight",
            character_alignment=-229,
            character_max_hp=1098,
            include_xp_only=True,
            include_level_ceiling_candidates=True,
            level_ceiling_offset=5,
            include_all_areas=True,
            recall_origins={0: 3001},
            route_economic_transit_allow_equipped_mobile_vnums=(
                *campaign_module._MIRROR_REALM_FIXED_ECONOMIC_TRANSIT_MOBILE_VNUMS,
            ),
        )
        if candidate.mobile_vnum == 19013 and candidate.room_vnum == 19119
    )

    assert set(candidate.route_special_mobile_vnums) == {
        19036, 19044, 19045, 19046, 19052, 19053,
    }
    # Economic transit does not waive a possible combat-output hazard.  The
    # lady of ill repute carries hitroll gear, so this corridor must stay closed.
    assert not campaign_module._source_ranked_mirror_realm_gardener_transit_allowed(
        candidate,
        {**_state(), "level": 45},
        character_level=45,
        character_max_hp=1098,
        source_world=world,
        allow_audited_special_target=True,
    )


def test_bounded_bear_transit_admits_plain_endpoint_only():
    world = load_world_source(
        SOURCE,
        include_all_areas=True,
        live_deployment=True,
    )
    state = {
        **_state(copper=53),
        "level": 45,
        "room_vnum": "3054",
        "character_alignment": -66,
        "affects": [],
    }
    candidate = next(
        candidate
        for candidate in rank_hunt_candidates(
            world,
            character_level=45,
            character_class="Warrior",
            character_subclass="Knight",
            character_alignment=-66,
            character_max_hp=1095,
            include_xp_only=True,
            include_level_ceiling_candidates=True,
            level_ceiling_offset=5,
            include_all_areas=True,
            recall_origins={0: 3001},
        )
        if candidate.mobile_vnum == 20515 and candidate.room_vnum == 20531
    )

    assert candidate.specials == ()
    assert candidate.autonomy_rejections == (
        "a non-safe special mobile can reach the route",
    )
    assert candidate.route_special_mobile_vnums == (18001,)
    assert campaign_module._source_ranked_bounded_bear_transit_route_allowed(
        candidate,
        character_level=45,
        source_world=world,
    )
    assert campaign_module._source_ranked_candidate_is_runtime_autonomous_safe(
        candidate,
        state,
        character_level=45,
        character_max_hp=1095,
        source_world=world,
    )
    assert campaign_module._select_source_ranked_hunt_candidate(
        (candidate,),
        state,
        world=world,
        character_level=45,
        character_max_hp=1095,
    ) == candidate

    assert not campaign_module._source_ranked_bounded_bear_transit_route_allowed(
        candidate,
        character_level=20,
        source_world=world,
    )
    assert not campaign_module._source_ranked_bounded_bear_transit_route_allowed(
        replace(candidate, route_special_mobile_vnums=(18001, 19036)),
        character_level=45,
        source_world=world,
    )
    assert not campaign_module._source_ranked_bounded_bear_transit_route_allowed(
        replace(candidate, specials=("spec_cast_mage",)),
        character_level=45,
        source_world=world,
    )


def test_mirror_realm_black_lord_per_room_singleton_can_run_without_sanctuary():
    world, candidates = _candidates()
    black_lord = candidates[(19033, 19103)]
    state = _state()
    state["combat_pouch_potions"] = {}
    state["verified_combat_pouch_potions"] = {}

    assert campaign_module._source_ranked_mirror_realm_gardener_transit_allowed(
        black_lord,
        state,
        character_level=39,
        character_max_hp=937,
        source_world=world,
    )
    assert campaign_module._select_source_ranked_hunt_candidate(
        (black_lord,),
        state,
        world=world,
        character_level=39,
        character_max_hp=937,
    ) == black_lord


def test_mirror_realm_below_band_black_lord_is_not_promoted_by_fuzz():
    world, candidates = _candidates()
    black_lord = candidates[(19033, 19103)]

    assert black_lord.level == 35
    assert black_lord.estimated_level_range == (33, 37)
    assert not campaign_module._source_ranked_mirror_realm_gardener_transit_allowed(
        black_lord,
        _state(),
        character_level=41,
        character_max_hp=988,
        source_world=world,
    )
    assert campaign_module._select_source_ranked_hunt_candidate(
        (black_lord,),
        _state(),
        world=world,
        character_level=41,
        character_max_hp=988,
    ) is None


def test_mirror_realm_black_lord_route_with_extra_combat_special_stays_closed():
    world, candidates = _candidates()
    black_lord = candidates[(19033, 19097)]

    assert not campaign_module._source_ranked_mirror_realm_gardener_transit_allowed(
        black_lord,
        _state(),
        character_level=39,
        character_max_hp=937,
        source_world=world,
    )
    assert campaign_module._select_source_ranked_hunt_candidate(
        (black_lord,),
        _state(),
        world=world,
        character_level=39,
        character_max_hp=937,
    ) is None


def test_grey_fox_aggressive_variant_stays_closed_below_useful_floor():
    world, candidates = _candidates()
    grey_fox = candidates[(19047, 19146)]
    altered = replace(grey_fox, mobile_vnum=19018)

    assert not campaign_module._source_ranked_mirror_realm_gardener_transit_allowed(
        grey_fox,
        _state(),
        character_level=39,
        character_max_hp=937,
        source_world=world,
        allow_aggressive_target=True,
    )
    assert not campaign_module._source_ranked_mirror_realm_gardener_transit_allowed(
        altered,
        _state(),
        character_level=39,
        character_max_hp=937,
        source_world=world,
        allow_aggressive_target=True,
    )
    assert campaign_module._select_source_ranked_hunt_candidate(
        (grey_fox,),
        _state(),
        world=world,
        character_level=39,
        character_max_hp=937,
    ) is None


def test_gardener_route_closes_when_purse_exceeds_source_thief_bound():
    world, candidates = _candidates()
    candidate = candidates[(19007, 19078)]

    assert not campaign_module._source_ranked_mirror_realm_gardener_transit_allowed(
        candidate,
        _state(copper=1251),
        character_level=39,
        character_max_hp=937,
        source_world=world,
    )


def test_gardener_route_shape_must_remain_source_exact():
    world, candidates = _candidates()
    candidate = candidates[(19007, 19078)]
    altered = replace(candidate, route_special_mobile_vnums=(19045,))

    assert not campaign_module._source_ranked_mirror_realm_gardener_transit_allowed(
        altered,
        _state(),
        character_level=39,
        character_max_hp=937,
        source_world=world,
    )
    assert not _source_ranked_area_circuit_route_admission_allowed(
        altered,
        world,
        {**_state(), "max_hp": 937},
        character_level=39,
    )


def test_orange_lord_locator_follows_audited_openable_mirror_door():
    world, candidates = _candidates()
    candidate = next(
        candidate
        for candidate in rank_hunt_candidates(
            world,
            character_level=40,
            character_class="warrior",
            character_subclass="knight",
            character_alignment=-52,
            character_max_hp=1018,
            include_xp_only=True,
            include_level_ceiling_candidates=True,
            level_ceiling_offset=5,
            include_all_areas=True,
            recall_origins={0: 3001},
        )
        if candidate.mobile_vnum == 19017 and candidate.room_vnum == 19057
    )
    stops = _source_ranked_hunt_stops(
        candidate,
        world,
        character_level=40,
        state={
            **_state(copper=341),
            "character_class": "Warrior",
            "character_subclass": "Knight",
            "max_hp": 1018,
            "hp": 1018,
        },
    )
    locator = stops[0]

    assert dict(locator.where_location_routes)[
        "along the path above the realm"
    ] == ("19007",)
    assert any(
        origin == "19057"
        and label == "along the path above the realm"
        and route[-1] == "19007"
        for origin, label, route in locator.where_relocation_routes
    )


def test_lotus_sentinel_circuit_drops_secondary_room_with_buddha_companion():
    world = load_world_source(SOURCE, include_all_areas=True)
    candidates = rank_hunt_candidates(
        world,
        character_level=40,
        character_class="warrior",
        character_subclass="knight",
        character_alignment=-52,
        character_max_hp=962,
        include_xp_only=True,
        include_all_areas=True,
        recall_origins={0: 3001},
    )
    primary = next(
        candidate
        for candidate in candidates
        if candidate.mobile_vnum == 10730 and candidate.room_vnum == 10821
    )
    rejected_secondary = next(
        candidate
        for candidate in candidates
        if candidate.mobile_vnum == 10730 and candidate.room_vnum == 10820
    )

    assert "target room has a dangerous reset companion" not in (
        rejected_secondary.autonomy_rejections
    )
    assert any(
        "source-backed noncombat special" in hazard
        for hazard in rejected_secondary.hazards
    )

    stops = _source_ranked_hunt_stops(
        primary,
        world,
        character_level=40,
        state={
            "level": 40,
            "max_hp": 962,
            "hp": 962,
            "character_class": "warrior",
            "character_subclass": "knight",
            "alignment": -52,
            "world_boot_id": "test-boot",
        },
    )

    assert "10820" not in {
        stop.route_vnums[-1]
        for stop in stops
        if stop.target is not None and stop.route_vnums
    }


def test_live_safe_adept_route_does_not_require_missing_target_warning():
    world = load_world_source(
        SOURCE,
        include_all_areas=True,
        live_deployment=True,
    )
    state = {
        "level": 45,
        "max_hp": 1090,
        "hp": 1090,
        "world_boot_id": "mirror-route-safe-adept-boot",
        "currencies": {"platinum": 0, "gold": 1, "silver": 2, "copper": 2},
        "affects": [],
    }
    candidate = next(
        item
        for item in rank_hunt_candidates(
            world,
            character_level=45,
            character_class="Warrior",
            character_subclass="Knight",
            character_max_hp=1090,
            include_xp_only=True,
            include_level_ceiling_candidates=True,
            level_ceiling_offset=5,
            include_all_areas=True,
            recall_origins={0: 3001},
        )
        if item.mobile_vnum == 19031 and item.room_vnum == 19077
    )

    assert candidate.specials == ("spec_cast_adept",)
    assert candidate.autonomy_rejections == (
        "an economic special mobile can reach the route",
    )
    assert campaign_module._source_ranked_mirror_realm_gardener_transit_allowed(
        candidate,
        state,
        character_level=45,
        character_max_hp=1090,
        source_world=world,
        allow_audited_special_target=True,
    )
    assert campaign_module._audited_source_special_candidate_allowed(
        candidate,
        state=state,
        character_max_hp=1090,
        source_world=world,
        route_preflight_admitted=True,
    )
    assert campaign_module._source_ranked_candidate_in_current_band(
        candidate,
        state,
        world=world,
        character_level=45,
        character_max_hp=1090,
    )


def test_mirror_realm_cleric_range_reaches_live_consider_probe():
    world = load_world_source(
        SOURCE,
        include_all_areas=True,
        live_deployment=True,
    )
    state = {
        "level": 45,
        "max_hp": 1090,
        "hp": 1090,
        "world_boot_id": "mirror-route-cleric-boot",
        "currencies": {"platinum": 0, "gold": 1, "silver": 2, "copper": 2},
        "combat_pouch_potions": {"purple": 1},
        "verified_combat_pouch_potions": {"purple": 1},
        "inventory": [{"short_desc": "a red dragonorb"}],
        "campaign_source_resource_reserves": {
            "sanctuary": {
                "charges_remaining": 1,
                "effect": "sanctuary",
                "mode": "staff",
                "object_description": "a red dragonorb",
            },
        },
        "affects": [],
    }
    candidate = next(
        item
        for item in rank_hunt_candidates(
            world,
            character_level=45,
            character_class="Warrior",
            character_subclass="Knight",
            character_max_hp=1090,
            include_xp_only=True,
            include_level_ceiling_candidates=True,
            level_ceiling_offset=5,
            include_all_areas=True,
            recall_origins={0: 3001},
        )
        if item.mobile_vnum == 19023 and item.room_vnum == 19067
    )
    candidate = economic_hunt_candidate(candidate, state, world)

    assert candidate.level == 39
    assert candidate.estimated_level_range == (37, 41)
    assert campaign_module._source_ranked_mirror_realm_gardener_transit_allowed(
        candidate,
        state,
        character_level=45,
        character_max_hp=1090,
        source_world=world,
        allow_audited_special_target=True,
    )
    assert campaign_module._audited_source_special_candidate_allowed(
        candidate,
        state=state,
        character_max_hp=1090,
        source_world=world,
        route_preflight_admitted=True,
    )
    assert campaign_module._source_ranked_candidate_in_current_band(
        candidate,
        state,
        world=world,
        character_level=45,
        character_max_hp=1090,
    )
