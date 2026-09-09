from dataclasses import replace
from pathlib import Path

import pytest

from dd4tester.campaign import (
    _source_ranked_early_locator_route, _source_ranked_hunt_stops,
)
from dd4tester.character import CharacterSpec
from dd4tester.fastwalks import Fastwalk
from dd4tester.hunt_candidates import (
    ACT_SENTINEL, ACT_STAY_AREA, ROOM_NO_MOB,
    ExitSource, HuntCandidate, MobileSource, MobReset, RoomSource, WorldSource,
    load_world_source, rank_hunt_candidates,
)
from dd4tester.starter import StarterPolicy


def _world():
    rooms = {
        3001: RoomSource(3001, "Recall", "town.are", room_flags=ROOM_NO_MOB),
        4000: RoomSource(4000, "The entrance", "hunt.are", room_flags=ROOM_NO_MOB),
        4001: RoomSource(4001, "The junction", "hunt.are"),
        4002: RoomSource(4002, "The reset room", "hunt.are"),
        4031: RoomSource(4031, "The valley", "hunt.are"),
    }
    for origin, direction, destination, reverse in (
        (3001, "north", 4000, "south"), (4000, "north", 4001, "south"),
        (4001, "north", 4002, "south"), (4001, "east", 4031, "west"),
    ):
        rooms[origin].exits[direction] = ExitSource(direction, destination, 0, -1)
        rooms[destination].exits[reverse] = ExitSource(reverse, origin, 0, -1)
    world = WorldSource(
        rooms=rooms,
        mobiles={1: MobileSource(
            1, "orc large", "the large orc", 5, ACT_STAY_AREA, 0, "hunt.are",
            room_description="A large orc is here.",
        )},
        mob_resets=[MobReset(1, 4002, 1, ())],
    )
    candidate = HuntCandidate(
        "candidate", 100, "hunt.are", 1, "the large orc", "orc", 5,
        4002, "The reset room", ("north",) * 3, 1, 1, 0, (), 0, 20, (),
        estimated_level_range=(3, 7), route_preflight_room_vnum="3001",
    )
    return world, candidate


def test_early_locator_preserves_city_preflight_and_uses_same_area():
    world, candidate = _world()
    assert _source_ranked_early_locator_route(world, candidate, character_level=8) == (("north",), 4000)
    assert candidate.room_vnum == 4002 and candidate.route == ("north",) * 3
    assert candidate.route_preflight_room_vnum == "3001"


@pytest.mark.parametrize("boundary", [
    "sentinel", "missing_mobile", "missing_room", "missing_exit", "wrong_endpoint",
    "random", "closed", "locked", "late_preflight", "hard_hazard", "unknown_command",
])
def test_early_locator_does_not_shorten_an_unverified_approach(boundary):
    world, candidate = _world()
    if boundary == "sentinel":
        world.mobiles[1] = replace(world.mobiles[1], act_flags=ACT_SENTINEL)
    elif boundary == "missing_mobile":
        world.mobiles.clear()
    elif boundary == "missing_room":
        world.rooms.pop(4002)
    elif boundary == "missing_exit":
        world.rooms[4001].exits.pop("north")
    elif boundary == "wrong_endpoint":
        candidate = replace(candidate, room_vnum=4031)
    elif boundary == "random":
        world.rooms[4001].random_exits = True
    elif boundary in {"closed", "locked"}:
        world.rooms[4001].exits["north"] = replace(
            world.rooms[4001].exits["north"], reset_state=1 if boundary == "closed" else 2,
        )
    elif boundary == "late_preflight":
        candidate = replace(candidate, route_preflight_room_vnum="4002")
    elif boundary == "hard_hazard":
        candidate = replace(candidate, route_hard_hazard_targets=("a danger",))
    else:
        candidate = replace(candidate, route=("north", "open gate", "north", "north"))
    assert _source_ranked_early_locator_route(world, candidate, character_level=8) == (candidate.route, None)


def test_locator_uses_first_safe_area_room_and_keeps_reset_fallback():
    world, candidate = _world()
    world.rooms[4000].room_flags |= 1 << 13  # No recall.
    route, origin = _source_ranked_early_locator_route(world, candidate, character_level=8)
    assert route == ("north", "north") and origin == 4001
    stops = _source_ranked_hunt_stops(
        candidate, world, character_level=8,
        hunt_route_origin_room_vnum=origin, locate_before_reset=True,
    )
    assert stops[0].actions == ("where orc",) and not stops[0].route_vnums
    assert stops[1].route_vnums == ("4002",)
    assert stops[0].maximum_where_relocations == 1


def test_late_locator_remains_default_for_legacy_staging():
    world, candidate = _world()
    stops = _source_ranked_hunt_stops(
        candidate, world, character_level=8, hunt_route_origin_room_vnum=4000,
    )
    assert stops[0].route_vnums == ("4001", "4002")


def _policy(world, candidate, origin):
    stops = _source_ranked_hunt_stops(
        candidate, world, character_level=8,
        hunt_route_origin_room_vnum=origin, locate_before_reset=True,
    )
    spec = CharacterSpec.from_mapping({
        "name": "Testchar", "race": "human", "gender": "female", "class": "mage",
    })
    policy = StarterPolicy(
        spec, "test-password", source_world=world,
        fastwalk_route=Fastwalk("funding", 1, 100, "n"), fastwalk_hunt_stops=stops,
    )
    policy.current_room = str(origin)
    policy.fastwalk_hunt_action_index = 1
    policy.fastwalk_where_response_pending = True
    return policy


def test_fresh_exact_locator_routes_from_entrance_not_from_reset_room():
    world, candidate = _world()
    policy = _policy(world, candidate, 4000)
    policy.observe_text(
        "You detect the presence of:\n"
        "The orc                      The reset room\n"
        "The large orc                The valley\n"
    )
    assert policy.fastwalk_where_locations == ("the valley",)
    assert len(policy.fastwalk_hunt_stops) == 2
    target = policy.fastwalk_hunt_stops[1]
    assert target.route_vnums == ("4001", "4031")
    assert target.source_mobile_vnum == 1 and target.exact_target
    assert target.require_isolated and not target.consider_only
    assert not policy.fastwalk_attack_started


def test_locator_does_not_map_an_unsafe_new_origin_path():
    world, candidate = _world()
    world.rooms[4031].room_flags |= 1 << 13
    policy = _policy(world, candidate, 4000)
    assert not any(
        origin == "4000" and label == "the valley"
        for origin, label, _ in policy.fastwalk_hunt_stops[0].where_relocation_routes
    )


def test_run_12800_source_replay_saves_ten_moves_before_valley():
    world = load_world_source(Path("runs/dd4-source/server/area"), include_all_areas=True)
    candidate = next(candidate for candidate in rank_hunt_candidates(
        world, character_level=8, include_below_band=True,
        character_max_hp=113, include_all_areas=True,
    ) if candidate.mobile_vnum == 4005 and candidate.room_vnum == 4022)
    route, origin = _source_ranked_early_locator_route(world, candidate, character_level=8)
    assert origin == 4000 and len(route) == 11
    policy = _policy(world, candidate, origin)
    policy.observe_text(
        "You detect the presence of:\n"
        "The orc                      The foothills path\n"
        "The large orc                The valley\n"
        "The orc                      The cave entrance\n"
        "The orc                      The large tunnel\n"
    )
    target = policy.fastwalk_hunt_stops[1]
    assert target.route_vnums == (
        "4001", "4002", "4010", "4011", "4014", "4015",
        "4019", "4026", "4027", "4029", "4031",
    )
    assert len(route) + len(target.route_vnums) == 22
    assert "4022" not in target.route_vnums
    old_stops = _source_ranked_hunt_stops(candidate, world, character_level=8)
    old_path = next(path for start, label, path in old_stops[0].where_relocation_routes
                    if start == "4022" and label == "the valley")
    assert len(candidate.route) + len(old_path) == 32
