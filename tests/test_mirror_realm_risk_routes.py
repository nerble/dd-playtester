from dataclasses import replace
from pathlib import Path

import dd4tester.campaign as campaign_module
from dd4tester.hunt_candidates import load_world_source, rank_hunt_candidates
from dd4tester.campaign import _source_ranked_hunt_stops


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
    assert campaign_module._select_source_ranked_hunt_candidate(
        (candidate,),
        _state(),
        world=world,
        character_level=39,
        character_max_hp=937,
    ) == candidate


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

    assert "target room has a dangerous reset companion" in (
        rejected_secondary.autonomy_rejections
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
