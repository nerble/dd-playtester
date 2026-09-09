from dataclasses import replace
from pathlib import Path

import pytest

from dd4tester.hunt_candidates import (
    ACT_AGGRESSIVE, ExitSource, MobileProgram, MobReset, RoomSource,
    load_world_source, rank_hunt_candidates,
)
from dd4tester.state import CharacterState
from test_early_funding_locator import _policy
from test_required_loot_bystanders import _loot_encounter


def _passive_room():
    policy, state, stop = _loot_encounter()
    stop = replace(stop, source_policy_id="funding-fixture")
    world = policy.source_world
    world.rooms = {
        200: RoomSource(200, "The cave", "test.are", {"south": ExitSource("south", 201, 0, -1)}),
        201: RoomSource(201, "Another cave", "test.are"),
    }
    world.mob_resets = [MobReset(101, 200, 2, ())]
    world.mobile_specials[101] = ("spec_poison",)
    policy.source_mobile_special_profiles_by_vnum[101] = ("spec_poison",)
    policy.fastwalk_where_locator_stop = stop
    policy.fastwalk_hunt_stops = (stop, replace(stop, source_reset_room_vnum=201, route_vnums=("201",)))
    policy.room_target_counts["200"] = {"midget": 2}
    policy.room_targets["200"] = ["midget"]
    policy.room_target_selectors["200"] = {"midget": ("#11", "#12")}
    policy.room_target_selector_descriptions["200"]["#12"] = "a midget is doing acrobatics here."
    policy.fastwalk_hunt_looked = True
    state.exits = {"south": "201"}
    return policy, state, stop


def test_absent_carrier_uses_normal_absence_and_next_route_not_combat():
    policy, state, stop = _passive_room()
    assert policy._required_loot_search_can_leave_passive_room(state, stop.target, stop)
    decision = policy._fastwalk_hunt_plan_decision(state)
    assert decision.command == "look"
    assert "absent" in decision.reason
    assert policy.fastwalk_target_absent
    assert not policy.fastwalk_target_present_observed
    assert not policy.fastwalk_crowded
    assert not policy.fastwalk_attack_started
    assert not policy.fastwalk_emergency_recall_pending
    assert policy.fastwalk_source_absent_sightings
    assert not policy.fastwalk_bystander_consider_outcomes
    commands = []
    for _ in range(3):
        next_decision = policy._fastwalk_hunt_plan_decision(state)
        commands.append(next_decision.command)
        if next_decision.command == "south":
            break
    assert commands[-1] == "south"
    assert policy.fastwalk_hunt_stop_index == 1
    assert policy.fastwalk_where_relocation_attempts == 0


@pytest.mark.parametrize("change", [
    "carrier", "aggressive", "script", "unknown_special", "guard", "unknown_mobile",
    "missing_selector", "duplicate_selector", "wrong_description", "combat", "enemy",
    "combat_target", "runtime", "return", "recall", "flee", "no_locator", "last_stop",
    "other_target", "other_source", "no_route", "unknown_room", "no_exit", "closed",
    "locked", "missing_live_exit", "random", "private", "no_recall", "flight", "level",
])
def test_passive_search_does_not_relax_other_boundaries(change):
    policy, state, stop = _passive_room()
    world = policy.source_world
    mobile = world.mobiles[101]
    if change == "carrier": policy.room_target_counts["200"]["illusionist"] = 1
    elif change == "aggressive": world.mobiles[101] = replace(mobile, act_flags=ACT_AGGRESSIVE)
    elif change == "script": world.mobiles[101] = replace(mobile, programs=(MobileProgram("greet_prog", "100", ("mpkill $n",)),))
    elif change == "unknown_special": world.mobile_specials[101] = ("spec_unknown",)
    elif change == "guard": world.mobile_specials[101] = ("spec_guard",)
    elif change == "unknown_mobile": world.mobiles.pop(101)
    elif change == "missing_selector": policy.room_target_selectors["200"].clear()
    elif change == "duplicate_selector": policy.room_target_selectors["200"]["midget"] = ("#11", "#11")
    elif change == "wrong_description": policy.room_target_selector_descriptions["200"]["#12"] = "something else"
    elif change == "combat": state.in_combat = True
    elif change == "enemy": state.enemies = [{"name": "a midget", "isnpc": 101}]
    elif change == "combat_target": state.combat_target = "midget"
    elif change == "runtime": policy.runtime_boundary_requested = True
    elif change == "return": policy.fastwalk_returning = True
    elif change == "recall": policy.fastwalk_emergency_recall_pending = True
    elif change == "flee": policy.flee_pending = True
    elif change == "no_locator": policy.fastwalk_where_locator_stop = None
    elif change == "last_stop": policy.fastwalk_hunt_stops = (stop,)
    elif change in {"other_target", "other_source", "no_route"}:
        kw = {"target": "other"} if change == "other_target" else {"source_mobile_vnum": 999} if change == "other_source" else {"route_vnums": ()}
        policy.fastwalk_hunt_stops = (stop, replace(policy.fastwalk_hunt_stops[1], **kw))
    elif change == "unknown_room": world.rooms.pop(201)
    elif change == "no_exit": world.rooms[200].exits.clear()
    elif change in {"closed", "locked"}: world.rooms[200].exits["south"] = ExitSource("south", 201, 2 if change == "closed" else 4, -1)
    elif change == "missing_live_exit": state.exits.clear()
    elif change == "random": world.rooms[201].random_exits = True
    elif change == "private": world.rooms[201].room_flags = 1 << 9
    elif change == "no_recall": world.rooms[201].room_flags = 1 << 13
    elif change == "flight": world.rooms[201].sector_type = 9
    else: state.level = 0
    assert not policy._required_loot_search_can_leave_passive_room(state, stop.target, stop)
    assert policy.fastwalk_hunt_stop_index == 0
    assert not policy.fastwalk_attack_started


@pytest.mark.parametrize("resource", ["hp", "mana", "move"])
def test_passive_search_retains_normal_circuit_resource_return(resource):
    policy, state, _ = _passive_room()
    setattr(state, resource, 1)
    decision = policy._fastwalk_hunt_plan_decision(state)
    assert decision.command == "recall"
    assert "recovery reserves" in decision.reason
    assert policy.fastwalk_returning


def test_run_12804_search_continues_from_passive_cave_without_new_searches():
    world = load_world_source(Path("runs/dd4-source/server/area"), include_all_areas=True)
    candidate = next(candidate for candidate in rank_hunt_candidates(
        world, character_level=8, include_below_band=True,
        character_max_hp=113, include_all_areas=True,
    ) if candidate.mobile_vnum == 4005 and candidate.room_vnum == 4022)
    policy = _policy(world, candidate, 4000)
    policy.observe_text("You detect the presence of:\nThe large orc                The cave\n")
    prior_area_presence = policy.fastwalk_target_present_observed
    policy.fastwalk_where_locator_stop = policy.fastwalk_hunt_stops[0]
    policy.fastwalk_hunt_stops = tuple(replace(
        stop, required_items=("a yellow and green ring",), allow_below_band_for_required_loot=True,
    ) for stop in policy.fastwalk_hunt_stops)
    original_stops = policy.fastwalk_hunt_stops
    policy.fastwalk_hunt_stop_index = 2
    stop = policy.fastwalk_hunt_stops[2]
    assert stop.route_vnums[-1] == "4025"
    policy.fastwalk_hunt_move_index = len(stop.route_vnums)
    policy.fastwalk_hunt_action_index = 0
    policy.fastwalk_hunt_looked = True
    policy.current_room = "4025"
    policy.room_target_counts["4025"] = {"garter snake": 2}
    policy.room_targets["4025"] = ["garter snake"]
    policy.room_target_selectors["4025"] = {"garter snake": ("#23406", "#2750")}
    policy.room_target_selector_descriptions["4025"] = dict.fromkeys(
        ("#23406", "#2750"), world.mobiles[4001].room_description.strip().casefold(),
    )
    policy.source_mobile_vnums_by_target_room = {"garter snake": {"4025": (4001,)}}
    policy.source_mobile_level_ranges_by_vnum = {4001: (5, 9)}
    policy.source_mobile_special_profiles_by_vnum = {4001: ("spec_poison",)}
    state = CharacterState(
        level=8, hp=113, max_hp=113, mana=324, max_mana=324, move=118, max_move=220,
        room_vnum="4025", position=7, enemies=None, exits={"east": "4026", "south": "4018"},
    )
    decision = policy._fastwalk_hunt_plan_decision(state)
    assert decision.command == "look" and "absent" in decision.reason
    assert policy.fastwalk_hunt_stops == original_stops
    assert not policy.fastwalk_emergency_recall_pending
    assert policy.fastwalk_target_present_observed == prior_area_presence
    assert not policy.fastwalk_room_target_present_observed
    commands = []
    for _ in range(3):
        decision = policy._fastwalk_hunt_plan_decision(state)
        commands.append(decision.command)
        if decision.command == "south":
            break
    assert commands[-1] == "south"
    assert policy.fastwalk_hunt_stop_index == 3
