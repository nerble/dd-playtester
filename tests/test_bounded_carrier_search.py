from dataclasses import replace
from pathlib import Path

import pytest

from dd4tester import starter
from dd4tester.campaign import _bounded_required_loot_search
from dd4tester.character import CharacterSpec
from dd4tester.fastwalks import Fastwalk, route_named
from dd4tester.hunt_candidates import (
    ACT_AGGRESSIVE, ACT_SENTINEL, ACT_STAY_AREA, AFF_DETECT_INVIS, ExitSource,
    MobileProgram, MobileSource, MobReset, ROOM_NO_MOB, RoomSource, WorldSource,
    load_world_source, source_route_hazard_rejections,
)
from dd4tester.locator_paths import bounded_carrier_locator_paths
from dd4tester.observations import GameEvent
from dd4tester.starter import FieldHuntStop, StarterPolicy, moria_sanctuary_potion_hunt_stops
from dd4tester.state import CharacterState


def world_and_stop():
    rooms = {
        3001: RoomSource(3001, "Recall", "town.are"),
        10: RoomSource(10, "Entrance", "hunt.are"),
        11: RoomSource(11, "Tunnel", "hunt.are"),
        12: RoomSource(12, "Maze", "hunt.are"),
        13: RoomSource(13, "Maze", "hunt.are", room_flags=1 << 13),
    }
    for a, b in ((3001, 10), (10, 11), (11, 12), (12, 13)):
        rooms[a].exits["north"] = ExitSource("north", b, 0, -1)
        rooms[b].exits["south"] = ExitSource("south", a, 0, -1)
    world = WorldSource(
        rooms=rooms, mobiles={1: MobileSource(
            1, "carrier", "the potion carrier", 5, ACT_STAY_AREA, 0, "hunt.are",
            room_description="A potion carrier stands here.",
        )}, mob_resets=[MobReset(1, 11, 2, (100,))],
    )
    stop = FieldHuntStop(
        ("north",), "potion carrier", required_items=("purple potion",),
        source_mobile_vnum=1, source_reset_room_vnum="11", exact_target=True,
        allow_below_band_for_required_loot=True, minimum_health_ratio=.85,
        pre_entry_scan_room_vnums=("11",), pre_entry_scan_hazard_source_mobile_vnums=(2,),
    )
    return world, stop


def test_shared_planner_keeps_ambiguous_label_but_only_accessible_rooms():
    world, _ = world_and_stop()
    plan = bounded_carrier_locator_paths(world, 1, origin=10, character_level=18)
    assert dict(plan.locations)["maze"] == ("12",)
    assert all("13" not in route for _, _, route in plan.relocations)
    assert sum(map(len, plan.search_routes)) <= 24


@pytest.mark.parametrize("hazard", ["random", "private", "solitary", "no_recall", "water", "closed", "locked", "wall", "unknown"])
def test_path_boundary_is_not_opened_by_a_locator(hazard):
    world, _ = world_and_stop()
    if hazard == "random":
        world.rooms[12].random_exits = True
    elif hazard in {"private", "solitary", "no_recall"}:
        world.rooms[12].room_flags = 1 << {"private": 9, "solitary": 11, "no_recall": 13}[hazard]
    elif hazard == "water":
        world.rooms[12].sector_type = 6
    elif hazard == "unknown":
        world.rooms.pop(12)
    else:
        world.rooms[11].exits["north"] = ExitSource(
            "north", 12, 128 if hazard == "wall" else 1, -1,
            reset_state=2 if hazard == "locked" else (1 if hazard == "closed" else 0),
        )
    plan = bounded_carrier_locator_paths(world, 1, origin=10, character_level=18)
    assert plan is not None
    assert all("12" not in route for _, _, route in plan.relocations)


@pytest.mark.parametrize("boundary", ["sentinel", "roaming_area", "missing_mobile", "missing_origin", "wrong_area", "zero_level"])
def test_only_known_same_area_wanderers_get_this_search(boundary):
    world, _ = world_and_stop()
    level = 18
    if boundary == "sentinel":
        world.mobiles[1] = replace(world.mobiles[1], act_flags=ACT_STAY_AREA | ACT_SENTINEL)
    elif boundary == "roaming_area":
        world.mobiles[1] = replace(world.mobiles[1], act_flags=0)
    elif boundary == "missing_mobile":
        world.mobiles.clear()
    elif boundary == "missing_origin":
        world.rooms.pop(10)
    elif boundary == "wrong_area":
        world.rooms[10].area_file = "other.are"
    else:
        level = 0
    assert bounded_carrier_locator_paths(world, 1, origin=10, character_level=level) is None


def test_whole_sweep_and_room_count_have_separate_bounds():
    world, _ = world_and_stop()
    plan = bounded_carrier_locator_paths(
        world, 1, origin=10, character_level=18, maximum_rooms=1, maximum_steps=1,
    )
    assert len(plan.search_routes) == 1
    assert sum(map(len, plan.search_routes)) <= 1
    assert bounded_carrier_locator_paths(world, 1, origin=10, character_level=18, maximum_steps=0) is None


def test_bounded_sweep_reserves_capacity_for_a_distinct_where_label():
    rooms = {
        10: RoomSource(10, "Origin", "hunt.are", room_flags=ROOM_NO_MOB),
        11: RoomSource(11, "Corridor", "hunt.are"),
        12: RoomSource(12, "Corridor", "hunt.are"),
        13: RoomSource(13, "Vault", "hunt.are"),
    }
    for left, right in ((10, 11), (11, 12), (12, 13)):
        rooms[left].exits["east"] = ExitSource("east", right, 0, -1)
        rooms[right].exits["west"] = ExitSource("west", left, 0, -1)
    world = WorldSource(
        rooms=rooms,
        mobiles={
            1: MobileSource(
                1,
                "carrier",
                "the carrier",
                5,
                ACT_STAY_AREA,
                0,
                "hunt.are",
                room_description="A carrier waits here.",
            )
        },
        mob_resets=[MobReset(1, 11, 1, ())],
    )

    plan = bounded_carrier_locator_paths(
        world,
        1,
        origin=10,
        character_level=18,
        maximum_rooms=2,
        maximum_steps=3,
    )

    assert dict(plan.locations)["corridor"] == ("11",)
    assert dict(plan.locations)["vault"] == ("13",)
    assert plan.search_routes == (("11",), ("12", "13"))


def test_source_combat_hazard_is_not_a_new_search_destination():
    world, _ = world_and_stop()
    world.mobiles[2] = MobileSource(2, "guard", "a hostile guard", 40, 34, 0, "hunt.are")
    world.mob_resets.append(MobReset(2, 12, 1, ()))
    plan = bounded_carrier_locator_paths(world, 1, origin=10, character_level=18)
    assert all("12" not in route for _, _, route in plan.relocations)


def test_source_safe_alternate_path_avoids_closed_shortcut():
    world, _ = world_and_stop()
    world.rooms[10].exits["north"] = ExitSource("north", 11, 1, -1, reset_state=1)
    world.rooms[14] = RoomSource(14, "Side passage", "hunt.are", exits={
        "north": ExitSource("north", 11, 0, -1),
    })
    world.rooms[10].exits["east"] = ExitSource("east", 14, 0, -1)
    plan = bounded_carrier_locator_paths(world, 1, origin=10, character_level=18)
    assert ("10", "tunnel", ("14", "11")) in plan.relocations


def test_required_invisibility_opens_route_past_unseeing_aggressor():
    world, _ = world_and_stop()
    world.mobiles[2] = MobileSource(
        2,
        "guard",
        "an aggressive guard",
        10,
        ACT_AGGRESSIVE | ACT_SENTINEL,
        0,
        "hunt.are",
    )
    world.mob_resets.append(MobReset(2, 11, 1, ()))

    visible = bounded_carrier_locator_paths(
        world,
        1,
        origin=10,
        character_level=18,
    )
    invisible = bounded_carrier_locator_paths(
        world,
        1,
        origin=10,
        character_level=18,
        require_invisibility=True,
    )

    assert dict(visible.locations)["maze"] == ()
    assert dict(invisible.locations)["maze"] == ("12",)
    assert source_route_hazard_rejections(
        world,
        (11,),
        character_level=18,
        combat_at_destination=True,
        invisible=True,
    )


def test_combat_only_poison_special_remains_inert_while_unseen():
    world, _ = world_and_stop()
    world.mobiles[2] = MobileSource(
        2,
        "snake",
        "a poisonous snake",
        10,
        ACT_AGGRESSIVE | ACT_SENTINEL,
        0,
        "hunt.are",
    )
    world.mob_resets.append(MobReset(2, 11, 1, ()))
    world.mobile_specials[2] = ("spec_poison",)

    plan = bounded_carrier_locator_paths(
        world,
        1,
        origin=10,
        character_level=18,
        require_invisibility=True,
    )

    assert dict(plan.locations)["maze"] == ("12",)


def test_combat_only_special_uses_source_aggression_level_cutoff():
    world, _ = world_and_stop()
    world.mobiles[2] = MobileSource(
        2,
        "snake",
        "a poisonous snake",
        10,
        ACT_AGGRESSIVE | ACT_SENTINEL,
        0,
        "hunt.are",
    )
    world.mob_resets.append(MobReset(2, 11, 1, ()))
    world.mobile_specials[2] = ("spec_poison",)

    assert source_route_hazard_rejections(
        world,
        (11,),
        character_level=22,
        combat_at_destination=False,
    ) == ("route crosses a non-safe special mobile: a poisonous snake in room 11",)
    assert source_route_hazard_rejections(
        world,
        (11,),
        character_level=23,
        combat_at_destination=False,
    ) == ()

    world.mobile_specials[2] = ("spec_thief",)
    assert source_route_hazard_rejections(
        world,
        (11,),
        character_level=100,
        combat_at_destination=False,
    ) == ("route crosses a non-safe special mobile: a poisonous snake in room 11",)


@pytest.mark.parametrize("boundary", ["detect", "program", "equipment", "special", "hero"])
def test_invisibility_does_not_bypass_unaudited_mobile_hazard(boundary):
    world, _ = world_and_stop()
    blocker = MobileSource(
        2,
        "guard",
        "an aggressive guard",
        10,
        ACT_AGGRESSIVE | ACT_SENTINEL,
        0,
        "hunt.are",
    )
    reset = MobReset(2, 11, 1, ())
    if boundary == "detect":
        blocker = replace(blocker, affected_flags=AFF_DETECT_INVIS)
    elif boundary == "program":
        blocker = replace(
            blocker,
            programs=(MobileProgram("rand_prog", "100", ("mpkill $n",)),),
        )
    elif boundary == "equipment":
        reset = replace(reset, equipment=((17, 99),))
    elif boundary == "special":
        world.mobile_specials[2] = ("spec_thief",)
    else:
        blocker = replace(blocker, level=101)
    world.mobiles[2] = blocker
    world.mob_resets.append(reset)

    plan = bounded_carrier_locator_paths(
        world,
        1,
        origin=10,
        character_level=18,
        require_invisibility=True,
    )

    assert dict(plan.locations)["maze"] == ()


def test_builder_retains_loot_and_target_contracts_and_original_fastwalk():
    world, target = world_and_stop()
    route = Fastwalk("carrier", 1, 100, "n")
    stops = _bounded_required_loot_search((target,), world, route, character_level=18)
    assert stops[0].target is None and stops[0].actions == ("where carrier",)
    assert stops[0].maximum_where_relocations == 1
    for stop in stops[1:]:
        assert replace(stop, route=target.route, route_vnums=()) == target
    assert route.commands == ("north",)


@pytest.fixture(scope="module")
def real_plan():
    directory = Path("runs/dd4-source/server/area")
    if not directory.is_dir():
        pytest.skip("optional DD4 source mirror is not installed")
    world = load_world_source(directory, include_all_areas=True)
    stops = _bounded_required_loot_search(
        moria_sanctuary_potion_hunt_stops(safe_reset_only=True), world,
        route_named("moria"), character_level=18,
    )
    return world, stops


def policy_at_locator(stops, world, origin="4014"):
    policy = StarterPolicy(
        CharacterSpec.from_mapping({"name": "Testchar", "race": "human", "gender": "female", "class": "mage"}),
        "unused", source_world=world, fastwalk_route=route_named("moria"),
        fastwalk_hunt_stops=stops,
    )
    policy.current_room = origin
    policy.fastwalk_hunt_action_index = 1
    policy.fastwalk_where_response_pending = True
    return policy


def test_run_12827_plan_queries_before_six_move_approach_and_can_check_adjacent_room(real_plan):
    world, stops = real_plan
    assert stops[0].actions == ("where hobgoblin",) and stops[0].route_vnums == ()
    assert dict(stops[0].where_location_routes)["the maze"] == ("4063",)
    assert dict(stops[0].where_location_routes)["the large cave"] == ()
    policy = policy_at_locator(stops, world)
    policy.observe_text("You detect the presence of:\nThe large hobgoblin              The maze\n")
    assert policy.fastwalk_where_locations == ("the maze",)
    assert len(policy.fastwalk_hunt_stops) == 2
    assert policy.fastwalk_hunt_stops[1].route_vnums == (
        "4015", "4019", "4026", "4027", "4020", "4064", "4063",
    )
    assert not policy.fastwalk_attack_started
    directory = str(Path("runs/dd4-source/server/area").resolve())
    policy.source_mobile_targets = starter._load_source_mobile_targets(directory)
    policy.source_mobile_vnums_by_target_room = starter._load_source_mobile_vnums_by_target_room(directory)
    policy.source_mobile_level_ranges_by_vnum = starter._load_source_mobile_level_ranges_by_vnum(directory)
    policy.fastwalk_hunt_stop_index = 1
    target = policy.fastwalk_hunt_stops[1]
    policy.fastwalk_hunt_move_index = len(target.route_vnums)
    policy.fastwalk_hunt_looked = True
    policy.fastwalk_hunt_action_index = 0
    policy.fastwalk_attack_target = target.target
    policy.fastwalk_outbound_index = len(policy.fastwalk_route.commands)
    policy.current_room = "4063"
    policy.after_command(starter.BotDecision("look", "observe the located carrier"))
    state = CharacterState(
        level=18, hp=218, max_hp=218, mana=628, max_mana=628, move=190,
        max_move=320, room_vnum="4063", position=7, hunger=35, thirst=40,
        exits={"e": "4064", "n": "4058"},
    )
    policy.observe_text("The maze\n[Exits: north east]\n[#1234] " + world.mobiles[4055].room_description + "\n")
    policy.observe_events([GameEvent("room_updated", "gmcp", {"vnum": "4063"})], state)
    decision = policy._fastwalk_hunt_plan_decision(state)
    assert decision.command == "consider #1234"
    assert not policy.fastwalk_attack_started
    assert policy.fastwalk_abort_reason is None


def test_run_12830_invisibility_maps_the_short_moria_carrier_corridor(real_plan):
    world, _ = real_plan
    plan = bounded_carrier_locator_paths(
        world,
        4055,
        origin=4014,
        character_level=18,
        maximum_rooms=12,
        require_invisibility=True,
    )

    locations = dict(plan.locations)
    assert set(locations["the maze"]) >= {"4063", "4066"}
    assert locations["the large cave"]
    assert locations["the hole"] == ("4074",)
    assert sum(map(len, plan.search_routes)) <= 24


def test_level_cutoff_maps_visible_moria_carrier_rooms_without_snake_combat(real_plan):
    world, _ = real_plan

    level_twenty_two = bounded_carrier_locator_paths(
        world,
        4055,
        origin=4014,
        character_level=22,
        maximum_rooms=8,
    )
    level_twenty_four = bounded_carrier_locator_paths(
        world,
        4055,
        origin=4014,
        character_level=24,
        maximum_rooms=8,
    )

    assert dict(level_twenty_two.locations)["the hole"] == ()
    assert all("4058" not in route for route in level_twenty_two.search_routes)
    locations = dict(level_twenty_four.locations)
    assert locations["end of tunnel"] == ("4073",)
    assert locations["the hole"] == ("4074",)
    assert set(locations["the large cave"]) == {"4069", "4071", "4070"}
    assert locations["the maze"] == ("4063",)
    assert set(locations["the tunnel"]) == {"4064", "4072"}
    assert any("4058" in route for route in level_twenty_four.search_routes)
    assert sum(map(len, level_twenty_four.search_routes)) <= 24


def test_required_loot_builder_uses_the_bounded_invisible_corridor(real_plan):
    world, _ = real_plan
    stops = _bounded_required_loot_search(
        moria_sanctuary_potion_hunt_stops(safe_reset_only=True),
        world,
        route_named("moria"),
        character_level=18,
        require_invisibility=True,
    )

    locations = dict(stops[0].where_location_routes)
    assert locations["the large cave"]
    assert locations["the hole"] == ("4074",)
    assert 1 < len(stops) <= 13
    assert sum(len(stop.route_vnums) for stop in stops[1:]) <= 24


def test_outside_safe_graph_is_presence_not_absence_and_skips_final_approach(real_plan):
    world, stops = real_plan
    policy = policy_at_locator(stops, world)
    policy.observe_text("You detect the presence of:\nThe large hobgoblin              The large cave\n")
    state = CharacterState(level=18, hp=218, max_hp=218, mana=628, max_mana=628,
                           move=250, max_move=320, room_vnum="4014", position=7)
    policy.fastwalk_hunt_looked = True
    policy.fastwalk_attack_target = None
    decision = policy._fastwalk_hunt_plan_decision(state)
    assert decision.command == "recall"
    assert "no safe relocation route" in policy.fastwalk_abort_reason
    assert policy.fastwalk_target_absent is False


def test_other_hobgoblin_does_not_become_carrier_evidence(real_plan):
    world, stops = real_plan
    policy = policy_at_locator(stops, world)
    policy.observe_text("You detect the presence of:\nThe hobgoblin                    The maze\n")
    assert not policy.fastwalk_where_target_present_observed
    assert not policy.fastwalk_where_locations


def test_existing_locator_and_missing_source_keep_original_plan():
    world, target = world_and_stop()
    route = Fastwalk("carrier", 1, 100, "n")
    assert _bounded_required_loot_search((target,), None, route, character_level=18) == (target,)
    existing = replace(target, where_target="potion carrier", actions=("where carrier",))
    assert _bounded_required_loot_search((existing,), world, route, character_level=18) == (existing,)
