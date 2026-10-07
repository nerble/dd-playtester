from dataclasses import replace

import pytest

from dd4tester.excavation import DigBudget
from dd4tester.excavation_routes import (
    build_source_hoard_execution_plan, hoard_return_plan,
    plan_hoard_movement_circuits,
)
from dd4tester.hunt_candidates import (
    ACT_AGGRESSIVE, ACT_SENTINEL, ExitSource, MobileSource, MobReset,
    ObjectSource, RoomSource, WorldSource,
)


def world_with_returns():
    return WorldSource(rooms={
        1: RoomSource(1, "Hoard", "test.are", exits={
            "north": ExitSource("north", 2, 0, 0),
            "east": ExitSource("east", 3, 0, 0),
        }, sector_type=2),
        2: RoomSource(2, "North", "test.are", exits={
            "south": ExitSource("south", 1, 0, 0),
            "west": ExitSource("west", 4, 0, 0),
        }, sector_type=2),
        3: RoomSource(3, "East", "test.are", exits={
            "west": ExitSource("west", 1, 0, 0),
            "north": ExitSource("north", 4, 0, 0),
        }, sector_type=3),
        4: RoomSource(4, "Registered healer", "test.are", exits={
            "west": ExitSource("west", 2, 0, 0),
            "south": ExitSource("south", 3, 0, 0),
        }, room_flags=1 << 16),
    })


def hoard_execution_world():
    world = world_with_returns()
    world.rooms[1] = replace(world.rooms[1], sector_type=1)
    world.objects[3393] = ObjectSource(
        3393, "spade", "a spade", 6, (36, 3, 9, 160), 100, level=1,
    )
    world.objects[585] = ObjectSource(585, "coin", "a coin", 20, (), 0)
    world.mobiles[83] = MobileSource(
        83, "spirit guardian", "a spirit guardian", 64, 98, -1000,
        "limbo.are", affected_flags=1572904, body_form_flags=336,
    )
    return world


def active_hoard_status():
    evidence = {
        "method": "hoard",
        "source": "requested-questmaster-narrative",
        "giver_vnum": 10001,
        "room_vnum": 1,
        "object_vnum": 585,
    }
    return {
        "active": 1,
        "complete": 0,
        "type": "retrieve",
        "giver_vnum": 10001,
        "room_vnum": 1,
        "object_vnum": 585,
        "retrieval_evidence": evidence,
    }


def source_hoard_plan(**changes):
    options = dict(
        world=hoard_execution_world(),
        quest_status=active_hoard_status(),
        tool_vnum=3393,
        carried_tool_vnums=(3393,),
        character_level=29,
        race="dwarf",
        healer_vnum=4,
        maximum_movement=430,
        starting_movement=430,
        strength=30,
        constitution=25,
        dexterity=16,
        swiftness=5,
        enhanced_swiftness_percent=0,
        armor_class=1,
        sanctuary=True,
        source_tool_level_bounds=(1, 2),
        allow_exact_live_where_hazards=False,
    )
    options.update(changes)
    return build_source_hoard_execution_plan(**options)


def test_source_hoard_plan_composes_tool_digs_escape_and_healer_circuits():
    plan = source_hoard_plan()

    assert plan.quest_identity == (10001, 1, 585)
    assert plan.tool.vnum == 3393
    assert plan.dig_budget.maximum_digs == 15
    assert plan.movement_plan.required_digs == 15
    assert plan.return_plan.expected_open_exits == {"north": 2, "east": 3}
    assert plan.maximum_direct_trap_damage > 0
    assert plan.maximum_guardian_damage_before_next_command > 0
    assert not plan.live_dispatch_authorized


def test_source_hoard_plan_honors_its_finite_long_route_budget():
    world = hoard_execution_world()
    route = (1, *range(100, 164), 4)
    rooms = {}
    for index, room_vnum in enumerate(route):
        exits = {}
        if index > 0:
            exits["north"] = ExitSource("north", route[index - 1], 0, 0)
        if index + 1 < len(route):
            exits["south"] = ExitSource("south", route[index + 1], 0, 0)
        name = "Safe corridor"
        if room_vnum == 1:
            name = "Hoard"
        elif room_vnum == 4:
            name = "Registered healer"
        rooms[room_vnum] = RoomSource(
            room_vnum,
            name,
            "test.are",
            exits=exits,
            room_flags=(1 << 16) if room_vnum == 4 else 0,
        )
    world.rooms = rooms

    plan = source_hoard_plan(
        world=world,
        maximum_movement=10_000,
        starting_movement=10_000,
        maximum_route_commands=200,
    )

    assert len(plan.return_plan.outbound.commands) == 65
    assert len(plan.return_plan.physical_return.commands) == 65
    assert plan.movement_plan.total_route_commands <= 200


@pytest.mark.parametrize("changes", [
    {"quest_status": {"active": 0, "type": "none"}},
    {"carried_tool_vnums": ()},
    {"source_tool_level_bounds": (0, 1)},
    {"quest_status": {
        **active_hoard_status(),
        "retrieval_evidence": {
            **active_hoard_status()["retrieval_evidence"], "room_vnum": 2,
        },
    }},
])
def test_source_hoard_plan_rejects_incomplete_assignment_or_tool_evidence(changes):
    with pytest.raises(ValueError):
        source_hoard_plan(**changes)


def test_every_open_escape_has_an_independent_physical_return():
    world = world_with_returns()
    plan = hoard_return_plan(world, 1, registered_healer_vnum=4, character_level=29)
    assert plan.expected_open_exits == {"north": 2, "east": 3}
    assert plan.outbound.rooms[0] == 4 and plan.outbound.rooms[-1] == 1
    assert plan.physical_return.rooms == (1, 2, 4)
    assert plan.physical_return.movement == 7
    assert plan.movement_reserve == 9
    assert all(1 not in branch.return_route.rooms for branch in plan.escape_branches)
    assert world.rooms[1].exits["east"].destination == 3
    assert plan.live_exit_issue({"north": 2, "east": 3}) is None


def test_flying_route_budget_requires_fresh_flight_for_each_leg():
    world = world_with_returns()
    walking = hoard_return_plan(
        world, 1, registered_healer_vnum=4, character_level=29,
    )
    flying = hoard_return_plan(
        world, 1, registered_healer_vnum=4, character_level=29, flying=True,
    )
    budget = DigBudget(
        tool_vnum=3393, tool_name="a spade", sector_type=2,
        minimum_damage=19, maximum_digs=11, maximum_move_per_dig=51,
        maximum_wait_pulses=3,
    )

    walking_circuits = plan_hoard_movement_circuits(
        walking, budget, maximum_movement=430, starting_movement=219,
    )
    flying_circuits = plan_hoard_movement_circuits(
        flying, budget, maximum_movement=430, starting_movement=219,
    )

    assert flying.outbound.movement < walking.outbound.movement
    assert flying.movement_reserve < walking.movement_reserve
    assert flying_circuits.circuits[0].dig_commands > walking_circuits.circuits[0].dig_commands
    assert flying_circuits.circuits[0].digging_movement == (
        flying_circuits.circuits[0].dig_commands * budget.maximum_move_per_dig
    )
    assert "active flight" in flying.live_route_issue(
        flying.outbound, {},
    )
    assert flying.live_route_issue(
        flying.outbound, {}, flying_active=True,
    ) is None
    assert "active flight" in flying.live_escape_issue({})
    assert flying.live_escape_issue({}, flying_active=True) is None


@pytest.mark.parametrize("exits", [None, {}, {"north": 2}, {"north": 2, "east": 5},
                                  {"north": 2, "east": 3, "down": 6},
                                  {"north": 2, "east": "3"}])
def test_changed_or_incomplete_live_exits_cannot_authorize_digging(exits):
    plan = hoard_return_plan(world_with_returns(), 1, registered_healer_vnum=4,
                            character_level=29)
    assert plan.live_exit_issue(exits)


@pytest.mark.parametrize("change", ["missing", "private", "random", "water", "air", "level"])
def test_one_unsupported_flee_destination_rejects_the_whole_plan(change):
    world = world_with_returns()
    if change == "missing":
        del world.rooms[3]
    else:
        kwargs = {
            "private": {"room_flags": 1 << 9}, "random": {"random_exits": True},
            "water": {"sector_type": 6}, "air": {"sector_type": 9},
            "level": {"area_low_enforced": 40, "area_high_enforced": 100},
        }[change]
        world.rooms[3] = replace(world.rooms[3], **kwargs)
    with pytest.raises(ValueError):
        hoard_return_plan(world, 1, registered_healer_vnum=4, character_level=29)


def test_guardian_escape_may_reenter_endpoint_only_after_clearance_check():
    world = world_with_returns()
    del world.rooms[3].exits["north"]
    plan = hoard_return_plan(world, 1, registered_healer_vnum=4, character_level=29)
    east = next(branch for branch in plan.escape_branches if branch.direction == "east")
    assert east.return_route.rooms == (3, 1, 2, 4)
    assert east.return_route.required_absent_mobile_vnums == (83,)


def test_dead_end_flee_branch_can_reenter_endpoint_only_with_guardian_clearance():
    world = world_with_returns()
    del world.rooms[2].exits["west"]
    plan = hoard_return_plan(world, 1, registered_healer_vnum=4, character_level=29)
    north = next(branch for branch in plan.escape_branches if branch.direction == "north")
    assert north.return_route.rooms == (2, 1, 3, 4)
    assert north.return_route.required_absent_mobile_vnums == (83,)
    assert plan.live_route_issue(north.return_route, {83: ()}) is None
    assert plan.live_route_issue(north.return_route, {83: (1,)})
    assert plan.live_route_issue(north.return_route, {})


def test_every_post_dig_return_checks_for_a_live_guardian():
    plan = hoard_return_plan(world_with_returns(), 1, registered_healer_vnum=4,
                            character_level=29)
    assert plan.live_route_issue(plan.physical_return, {83: ()}) is None
    assert plan.live_route_issue(plan.physical_return, {83: (1,)})


def test_live_locator_clearance_covers_every_flee_and_return_branch():
    plan = hoard_return_plan(
        world_with_returns(), 1, registered_healer_vnum=4, character_level=29,
    )
    plan = replace(plan, live_locator_mobile_vnums=(3060, 3064))
    assert plan.live_escape_issue({3060: (), 3064: ()}) is None
    assert plan.live_escape_issue({3060: (2,), 3064: ()})
    assert plan.live_escape_issue({3060: (), 3064: None})


def test_return_cannot_depend_on_a_locked_door():
    world = world_with_returns()
    world.rooms[3].exits["north"] = ExitSource("north", 4, 6, 99)
    plan = hoard_return_plan(world, 1, registered_healer_vnum=4, character_level=29)
    east = next(branch for branch in plan.escape_branches if branch.direction == "east")
    assert east.return_route.rooms == (3, 1, 2, 4)
    assert east.return_route.required_absent_mobile_vnums == (83,)


def test_ordinary_unlocked_return_door_has_an_explicit_open_step():
    world = world_with_returns()
    world.rooms[3].exits["north"] = ExitSource("north", 4, 2, 0)
    plan = hoard_return_plan(world, 1, registered_healer_vnum=4, character_level=29)
    east = next(b for b in plan.escape_branches if b.direction == "east")
    assert east.return_route.commands == ("open north", "north")


def test_endpoint_return_door_must_be_opened_and_reobserved_before_dig():
    world = world_with_returns()
    world.rooms[1].exits = {"north": ExitSource("north", 2, 2, 0)}
    plan = hoard_return_plan(world, 1, registered_healer_vnum=4, character_level=29)
    assert plan.preparation_commands == ("open north",)
    assert plan.live_exit_issue({})
    assert plan.live_exit_issue({"north": 2}) is None
    assert world.rooms[1].exits["north"].closed


def test_source_closed_exit_must_remain_closed_in_live_observation():
    world = world_with_returns()
    world.rooms[1].exits["down"] = ExitSource("down", 999, 2, 0)
    plan = hoard_return_plan(world, 1, registered_healer_vnum=4, character_level=29)
    assert plan.live_exit_issue({"north": 2, "east": 3, "down": 999})


def test_registered_healer_requires_source_healing_flag_not_its_name():
    world = world_with_returns()
    world.rooms[4].room_flags = 0
    with pytest.raises(ValueError, match="healing endpoint"):
        hoard_return_plan(world, 1, registered_healer_vnum=4, character_level=29)


def test_slow_reserve_includes_flee_edge_and_worst_return():
    plan = hoard_return_plan(world_with_returns(), 1, registered_healer_vnum=4,
                            character_level=29, slow=True)
    assert plan.movement_reserve == 27


def test_finite_route_bound_includes_the_flee_step():
    with pytest.raises(ValueError):
        hoard_return_plan(world_with_returns(), 1, registered_healer_vnum=4,
                          character_level=29, maximum_commands=1)


@pytest.mark.parametrize("special,aggressive,sentinel", [
    ("spec_guard", False, True), ("spec_unknown", False, True),
    (None, True, True), (None, True, False),
])
def test_one_source_hazard_rejects_escape_even_when_another_exit_is_safe(
    special, aggressive, sentinel,
):
    world = world_with_returns()
    flags = (ACT_AGGRESSIVE if aggressive else 0) | (ACT_SENTINEL if sentinel else 0)
    world.mobiles[10] = MobileSource(10, "guard", "a guard", 29, flags, 0, "test.are")
    world.mob_resets.append(MobReset(10, 3, 1, ()))
    if special:
        world.mobile_specials[10] = (special,)
    with pytest.raises(ValueError):
        hoard_return_plan(world, 1, registered_healer_vnum=4, character_level=29)


def test_missing_mobile_prototype_is_not_an_empty_safe_reset():
    world = world_with_returns()
    world.mob_resets.append(MobReset(10, 3, 1, ()))
    with pytest.raises(ValueError, match="unresolved"):
        hoard_return_plan(world, 1, registered_healer_vnum=4, character_level=29)


def test_unrelated_disconnected_source_reset_does_not_block_return():
    world = world_with_returns()
    world.rooms[5] = RoomSource(5, "Disconnected", "other.are")
    world.mob_resets.append(MobReset(10, 5, 1, ()))
    assert hoard_return_plan(world, 1, registered_healer_vnum=4,
                             character_level=29).movement_reserve == 9


def test_low_throughput_spade_is_split_into_healer_return_circuits():
    route = hoard_return_plan(
        world_with_returns(), 1, registered_healer_vnum=4, character_level=29,
    )
    budget = DigBudget(
        tool_vnum=3393, tool_name="a spade", sector_type=2,
        minimum_damage=19, maximum_digs=11, maximum_move_per_dig=51,
        maximum_wait_pulses=3,
    )

    plan = plan_hoard_movement_circuits(
        route, budget, maximum_movement=430, starting_movement=230,
    )

    assert [circuit.dig_commands for circuit in plan.circuits] == [4, 7]
    assert all(circuit.total_movement <= 430 for circuit in plan.circuits)
    assert plan.required_digs == 11
    assert plan.total_route_commands == 19


def test_movement_circuit_keeps_routes_and_preopens_its_physical_return():
    world = world_with_returns()
    del world.rooms[1].exits["east"]
    world.rooms[1].exits["north"] = ExitSource("north", 2, 2, 0)
    route = hoard_return_plan(
        world, 1, registered_healer_vnum=4, character_level=29,
    )
    budget = DigBudget(
        tool_vnum=3393, tool_name="a spade", sector_type=2,
        minimum_damage=19, maximum_digs=2, maximum_move_per_dig=51,
        maximum_wait_pulses=3,
    )

    plan = plan_hoard_movement_circuits(
        route, budget, maximum_movement=430, starting_movement=230,
    )

    circuit = plan.circuits[0]
    assert circuit.outbound_commands == route.outbound.commands
    assert circuit.preparation_commands == ("open north",)
    assert circuit.return_commands == ("north", "west")
    assert circuit.total_route_commands == plan.total_route_commands


def test_spade_circuit_requires_movement_for_a_physical_return():
    route = hoard_return_plan(
        world_with_returns(), 1, registered_healer_vnum=4, character_level=29,
    )
    budget = DigBudget(
        tool_vnum=3393, tool_name="a spade", sector_type=2,
        minimum_damage=19, maximum_digs=11, maximum_move_per_dig=51,
        maximum_wait_pulses=3,
    )

    with pytest.raises(ValueError, match="outbound, one dig, and return"):
        plan_hoard_movement_circuits(
            route, budget, maximum_movement=430, starting_movement=20,
        )


def test_spade_circuits_enforce_a_total_route_command_bound():
    route = hoard_return_plan(
        world_with_returns(), 1, registered_healer_vnum=4, character_level=29,
    )
    budget = DigBudget(
        tool_vnum=3393, tool_name="a spade", sector_type=2,
        minimum_damage=19, maximum_digs=11, maximum_move_per_dig=51,
        maximum_wait_pulses=3,
    )

    with pytest.raises(ValueError, match="command bound"):
        plan_hoard_movement_circuits(
            route, budget, maximum_movement=430, starting_movement=230,
            maximum_route_commands=18,
        )


def test_live_locator_hazard_exception_requires_exact_source_profiles():
    with pytest.raises(ValueError, match="profiles"):
        hoard_return_plan(
            world_with_returns(), 1, registered_healer_vnum=4,
            character_level=29, allow_exact_live_where_hazards=True,
        )


def test_return_uses_bounded_safe_detour_around_intermediate_attacker():
    world = world_with_returns()
    world.rooms[2].exits = {
        "north": ExitSource("north", 5, 0, 0),
        "west": ExitSource("west", 6, 0, 0),
    }
    world.rooms[5] = RoomSource(5, "Danger", "test.are", exits={
        "north": ExitSource("north", 4, 0, 0),
    })
    world.rooms[6] = RoomSource(6, "Detour", "test.are", exits={
        "north": ExitSource("north", 7, 0, 0),
    })
    world.rooms[7] = RoomSource(7, "Detour end", "test.are", exits={
        "north": ExitSource("north", 4, 0, 0),
    })
    world.mobiles[10] = MobileSource(10, "attacker", "an attacker", 29,
                                    ACT_SENTINEL | ACT_AGGRESSIVE, 0, "test.are")
    world.mob_resets.append(MobReset(10, 5, 1, ()))
    plan = hoard_return_plan(world, 1, registered_healer_vnum=4, character_level=29)
    north = next(b for b in plan.escape_branches if b.direction == "north")
    assert north.return_route.rooms == (2, 6, 7, 4)
