from dataclasses import replace

import pytest

from dd4tester.campaign import _quest_target_route
from dd4tester.hunt_candidates import (
    ACT_AGGRESSIVE, ACT_FEAR_AURA, ACT_SENTINEL, ExitSource, MobileProgram,
    MobileSource, MobReset, RoomSource, WorldSource,
    source_mobile_has_only_economic_transit_risk, source_route_hazard_rejections,
)
from dd4tester.quest_access import (
    economic_quest_route_evidence, economic_quest_runtime_issue,
    economic_quest_transit, observed_stealable_copper,
)
from dd4tester.quests import snapshot_quest_status


def world_source():
    rooms = {v: RoomSource(v, str(v), "test.are", exits={}) for v in (3001, 9901, 9911)}
    rooms[3001].exits["north"] = ExitSource("north", 9901, 0, -1)
    rooms[9901].exits["north"] = ExitSource("north", 9911, 0, -1)
    return WorldSource(
        rooms=rooms,
        mobiles={17: MobileSource(17, "pickpocket", "a pickpocket", 10, ACT_SENTINEL, 0, "test.are")},
        mob_resets=[MobReset(17, 9901, 1, ())],
        mobile_specials={17: ("spec_thief",)},
    )


def quest_state():
    return {
        "level": 29,
        "currencies": {"platinum": 0, "gold": 0, "silver": 4, "copper": 0},
        "quest_status": {
            "active": 1, "type": "retrieve", "giver_vnum": 10001,
            "room_vnum": 9911, "object_vnum": 76, "countdown": 12, "mob_vnum": 0,
        },
    }


def planned_route(world, state):
    return _quest_target_route(
        world, snapshot_quest_status(state["quest_status"]), character_level=29, state=state,
    )


@pytest.mark.parametrize("flags", [ACT_SENTINEL, 0])
def test_small_purse_allows_exact_noncombat_quest_but_not_general_route_or_kill(flags):
    world, state = world_source(), quest_state()
    world.mobiles[17] = replace(world.mobiles[17], act_flags=flags)
    route = planned_route(world, state)
    assert route is not None and route.commands == ("north", "north")
    assert route.route_economic_special_mobile_vnums == (17,)
    assert route.route_economic_quest_identity == (10001, 9911, 76)
    evidence = economic_quest_route_evidence(route, state["currencies"])
    assert evidence["observed_purse"] == 40
    assert evidence["whole_purse_limit"] == 250
    assert evidence["combat_authorized"] is False
    assert evidence["quest_identity"] == (10001, 9911, 76)
    assert source_route_hazard_rejections(world, (3001, 9901, 9911), character_level=29)
    assert source_route_hazard_rejections(
        world, (3001, 9901, 9911), character_level=29,
        combat_at_destination=True, economic_special_mobile_vnums=(17,),
    )
    assert economic_quest_runtime_issue(
        route, world, status=state["quest_status"], currencies=state["currencies"],
    ) is None
    state["quest_status"].update(type="kill", mob_vnum=17)
    assert planned_route(world, state) is None


@pytest.mark.parametrize("change", [
    {"platinum": 1}, {"gold": 3}, {"copper": 211}, {"silver": -1},
    {"copper": "0"}, {"copper": False}, {"copper": None},
])
def test_whole_purse_not_one_theft_percentage_limits_route(change):
    state = quest_state()
    state["currencies"].update(change)
    assert planned_route(world_source(), state) is None


def test_wallet_requires_all_ordinary_denominations_and_ignores_unstealable_currency():
    assert observed_stealable_copper({"copper": 1}) is None
    assert observed_stealable_copper(None) is None
    coins = {"platinum": 0, "gold": 2, "silver": 5, "copper": 0, "starmetal": 999}
    assert observed_stealable_copper(coins) == 250
    assert economic_quest_transit(world_source(), 9911, character_level=29, currencies=coins)


@pytest.mark.parametrize("change", ["aggressive", "aura", "armed", "mixed", "unknown", "program", "no_reset"])
def test_special_exception_never_suppresses_other_source_risk(change):
    world = world_source()
    if change in {"aggressive", "aura"}:
        flag = ACT_AGGRESSIVE if change == "aggressive" else ACT_FEAR_AURA
        world.mobiles[17] = replace(world.mobiles[17], act_flags=ACT_SENTINEL | flag)
    elif change == "armed":
        world.mob_resets[0] = replace(world.mob_resets[0], equipment=((16, 123),))
    elif change in {"mixed", "unknown"}:
        world.mobile_specials[17] = ("spec_thief", "spec_cast_mage" if change == "mixed" else "unknown")
    elif change == "program":
        world.mobiles[17] = replace(world.mobiles[17], programs=(MobileProgram("greet_prog", "100", ("say hello",)),))
    else:
        world.mob_resets.clear()
    assert not source_mobile_has_only_economic_transit_risk(world, 17)


@pytest.mark.parametrize("change", [
    {"giver_vnum": 999}, {"room_vnum": 999}, {"object_vnum": 999},
    {"countdown": 0}, {"mob_vnum": 17}, {"type": "hoard"},
    {"active": 0, "object_vnum": 0},
])
def test_runtime_requires_same_positive_active_loose_retrieval(change):
    world, state = world_source(), quest_state()
    route = planned_route(world, state)
    state["quest_status"].update(change)
    assert economic_quest_runtime_issue(
        route, world, status=state["quest_status"], currencies=state["currencies"],
    )


def test_runtime_rechecks_purse_source_and_retains_completed_item_return():
    world, state = world_source(), quest_state()
    route = planned_route(world, state)
    state["quest_status"]["complete"] = 1
    assert economic_quest_runtime_issue(
        route, world, status=state["quest_status"], currencies=state["currencies"],
    ) is None
    state["currencies"]["platinum"] = 1
    assert economic_quest_runtime_issue(
        route, world, status=state["quest_status"], currencies=state["currencies"],
    )
    state["currencies"]["platinum"] = 0
    world.mobile_specials[17] = ("spec_thief", "spec_poison")
    assert economic_quest_runtime_issue(
        route, world, status=state["quest_status"], currencies=state["currencies"],
    )


def test_economic_route_cannot_cross_random_exits_or_an_unrelated_attacker():
    world, state = world_source(), quest_state()
    world.rooms[9901] = replace(world.rooms[9901], random_exits=4)
    assert economic_quest_transit(world, 9911, character_level=29, currencies=state["currencies"]) is None
    world.rooms[9901] = replace(world.rooms[9901], random_exits=0)
    world.mobiles[18] = replace(world.mobiles[17], vnum=18, level=30, act_flags=ACT_AGGRESSIVE)
    world.mob_resets.append(MobReset(18, 9911, 1, ()))
    assert economic_quest_transit(world, 9911, character_level=29, currencies=state["currencies"]) is None
