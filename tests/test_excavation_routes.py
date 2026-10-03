from dataclasses import replace

import pytest

from dd4tester.excavation_routes import hoard_return_plan
from dd4tester.hunt_candidates import (
    ACT_AGGRESSIVE, ACT_SENTINEL, ExitSource, MobileSource, MobReset, RoomSource, WorldSource,
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
        4: RoomSource(4, "Registered healer", "test.are", room_flags=1 << 16),
    })


def test_every_open_escape_has_an_independent_physical_return():
    world = world_with_returns()
    plan = hoard_return_plan(world, 1, registered_healer_vnum=4, character_level=29)
    assert plan.expected_open_exits == {"north": 2, "east": 3}
    assert plan.physical_return.rooms == (1, 2, 4)
    assert plan.physical_return.movement == 7
    assert plan.movement_reserve == 9
    assert all(1 not in branch.return_route.rooms for branch in plan.escape_branches)
    assert world.rooms[1].exits["east"].destination == 3
    assert plan.live_exit_issue({"north": 2, "east": 3}) is None


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


def test_guardian_escape_cannot_walk_back_through_its_room():
    world = world_with_returns()
    del world.rooms[3].exits["north"]
    with pytest.raises(ValueError, match="no bounded physical return"):
        hoard_return_plan(world, 1, registered_healer_vnum=4, character_level=29)


def test_return_cannot_depend_on_a_locked_door():
    world = world_with_returns()
    world.rooms[3].exits["north"] = ExitSource("north", 4, 6, 99)
    with pytest.raises(ValueError):
        hoard_return_plan(world, 1, registered_healer_vnum=4, character_level=29)


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
