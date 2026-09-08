from dataclasses import replace
import json
from pathlib import Path

import pytest

from dd4tester.campaign import _source_ranked_neighbor_area_locator_route
from dd4tester.character import CharacterSpec
from dd4tester.hunt_candidates import (
    ACT_AGGRESSIVE, ACT_SENTINEL, ExitSource, MobileSource, MobReset,
    RoomSource, WorldSource, source_route_hazard_rejections,
)
from dd4tester.starter import FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures/dd4_cross_area_locator_miss.json").read_text()
)


def _world() -> WorldSource:
    return WorldSource(
        mobiles={9808: MobileSource(9808, "fanatic monk", "a fanatic monk", 6, 0, 0, "cult.are")},
        rooms={
            9850: RoomSource(9850, "The Reception Area", "cult.are", exits={
                "south": ExitSource("south", 3024, 0, -1),
            }),
            3024: RoomSource(3024, "Eastern Road", "midgaard.are", exits={
                "north": ExitSource("north", 9850, 0, -1),
            }),
        },
        mob_resets=[MobReset(9808, 9850, 1, ())],
    )


def _route(world: WorldSource, *, level: int | None = 11, blocked=()):
    return _source_ranked_neighbor_area_locator_route(
        world, 9850, tuple(world.rooms), blocked_rooms=blocked, character_level=level,
    )


def _policy() -> tuple[StarterPolicy, CharacterState]:
    area, route, cost = _route(_world())
    locator = FieldHuntStop(
        (), where_target="fanatic monk", command_keyword="fanatic",
        actions=("where fanatic",), abort_if_where_target_unlisted=True,
        where_area_file="cult.are", where_neighbor_area_file=area,
        where_neighbor_route_vnums=route, where_neighbor_move_cost=cost,
        where_source_mobile_vnum=9808,
        where_location_routes=(("eastern road", ("3024",)),),
        where_relocation_routes=(("3024", "eastern road", ()),),
        preserve_where_route_waypoints=True,
    )
    target = FieldHuntStop(
        (), "fanatic monk", route_vnums=("3024",), source_mobile_vnum=9808,
        exact_target=True, require_isolated=True, require_damage_window_probe=True,
    )
    policy = StarterPolicy(
        CharacterSpec.from_mapping({
            "name": "Testchar", "race": "human", "gender": "male", "class": "thief",
        }),
        "test-password", fastwalk_hunt_stops=(locator, target),
    )
    policy.current_room = "9850"
    policy.fastwalk_hunt_looked = True
    policy.fastwalk_hunt_action_index = 1
    policy.observe_text(FIXTURE["response"])
    state = CharacterState(
        level=11, room_vnum="9850", hp=186, max_hp=186,
        mana=172, max_mana=172, move=249, max_move=250,
        position=7, exits={"south": "3024"},
    )
    return policy, state


def _cross_and_query(policy: StarterPolicy, state: CharacterState) -> CharacterState:
    decision = policy._fastwalk_hunt_plan_decision(state)
    assert decision.command == "south"
    assert not policy.fastwalk_returning
    assert not policy.fastwalk_target_absent
    state = replace(state, room_vnum="3024", exits={"north": "9850"})
    policy.current_room = "3024"
    policy.observe_text("Eastern Road\n<186/186 hits 172/172 mana 246/250 move [Midgaard]>")
    assert policy._fastwalk_hunt_plan_decision(state).command == "look"
    query = policy._fastwalk_hunt_plan_decision(state)
    assert query.command == "where fanatic"
    policy.after_command(query)
    assert policy.fastwalk_where_response_pending
    return state


def test_captured_local_miss_checks_exactly_one_neighboring_area():
    policy, state = _policy()
    state = _cross_and_query(policy, state)
    policy.observe_text(FIXTURE["response"].replace("Dragon Cult", "Midgaard"))
    decision = policy._fastwalk_hunt_plan_decision(state)
    assert decision.command == "recall"
    assert "global" not in decision.reason
    assert policy.fastwalk_target_absent
    assert policy.fastwalk_where_area_checks == [
        {"area_file": "cult.are", "room_vnum": "9850", "source_mobile_vnum": 9808,
         "target": "fanatic monk", "result": "unlisted", "scope": "current_area"},
        {"area_file": "midgaard.are", "room_vnum": "3024", "source_mobile_vnum": 9808,
         "target": "fanatic monk", "result": "unlisted", "scope": "current_area"},
    ]
    assert not policy.fastwalk_where_locator_stop.where_neighbor_route_vnums


def test_neighboring_area_presence_rebases_exact_target_without_granting_combat():
    policy, state = _policy()
    state = _cross_and_query(policy, state)
    policy.observe_text(
        "You detect the presence of:\nA fanatic monk        Eastern Road\n"
        "<186/186 hits 172/172 mana 246/250 move [Midgaard]>"
    )
    assert policy._fastwalk_hunt_plan_decision(state).command == "look"
    assert policy.fastwalk_where_area_checks[-1]["result"] == "present"
    assert policy.fastwalk_where_locator_stop is policy.fastwalk_hunt_stops[0]
    target = policy.fastwalk_hunt_stops[1]
    assert target.route_vnums == ()
    assert target.source_mobile_vnum == 9808
    assert target.exact_target and target.require_isolated and target.require_damage_window_probe
    assert not policy.fastwalk_attack_started
    assert policy.consider_viable is None


def test_neighboring_area_unmapped_presence_does_not_replay_old_origin_route():
    policy, state = _policy()
    state = _cross_and_query(policy, state)
    policy.observe_text(
        "You detect the presence of:\nA fanatic monk        Unknown Room\n"
        "<186/186 hits 172/172 mana 246/250 move [Midgaard]>"
    )
    assert policy._fastwalk_hunt_plan_decision(state).command == "recall"
    assert "no source-vetted target route" in policy.fastwalk_abort_reason
    assert not policy.fastwalk_target_absent


def test_known_neighbor_label_without_audited_relocation_is_not_a_route():
    policy, state = _policy()
    locator = replace(policy.fastwalk_hunt_stops[0], where_relocation_routes=())
    policy.fastwalk_hunt_stops = (locator, *policy.fastwalk_hunt_stops[1:])
    policy.fastwalk_where_locator_stop = locator
    state = _cross_and_query(policy, state)
    policy.observe_text(
        "You detect the presence of:\nA fanatic monk        Eastern Road\n"
        "<186/186 hits 172/172 mana 246/250 move [Midgaard]>"
    )
    assert policy._fastwalk_hunt_plan_decision(state).command == "recall"
    assert "no safe relocation route" in policy.fastwalk_abort_reason
    assert not policy.fastwalk_target_absent


@pytest.mark.parametrize("values", [
    {"hp": 1}, {"move": 1}, {"move": None},
])
def test_low_resources_prevent_cross_area_extension(values):
    policy, state = _policy()
    assert policy._fastwalk_hunt_plan_decision(replace(state, **values)).command == "recall"
    assert policy.fastwalk_hunt_stops[0].where_area_file == "cult.are"


def test_missing_live_exit_does_not_issue_source_direction_blindly():
    policy, state = _policy()
    decision = policy._fastwalk_hunt_plan_decision(replace(state, exits={"east": "9000"}))
    assert decision.command == "recall"
    assert "could not find GMCP exit" in policy.fastwalk_abort_reason


def test_missing_room_packet_waits_instead_of_falling_through_to_absence_return():
    policy, state = _policy()
    assert policy._fastwalk_hunt_plan_decision(replace(state, exits={})) is None
    assert not policy.fastwalk_returning
    assert policy.fastwalk_hunt_stops[0].where_area_file == "midgaard.are"


def test_neighbor_locator_still_waits_for_delayed_reply():
    policy, state = _policy()
    state = _cross_and_query(policy, state)
    policy._tutorial_decision = policy._fastwalk_hunt_plan_decision
    policy.in_world = True
    policy.login_authenticated = True
    policy.prompt_ready = True
    assert policy.next_decision(state) is None
    assert len(policy.fastwalk_where_area_checks) == 1


def test_source_crossing_is_short_ground_route():
    assert _route(_world()) == ("midgaard.are", ("3024",), 2)


@pytest.mark.parametrize("flag", [1 << 9, 1 << 11, 1 << 13])
def test_source_crossing_rejects_new_recovery_boundaries(flag):
    world = _world()
    world.rooms[3024].room_flags = flag
    assert _route(world) == (None, (), 0)


@pytest.mark.parametrize("change", ["closed", "water", "random", "same_area", "blocked", "unknown_level"])
def test_source_crossing_rejects_unavailable_paths(change):
    world = _world()
    if change == "closed":
        world.rooms[9850].exits["south"] = ExitSource("south", 3024, 1, 123, reset_state=1)
    elif change == "water":
        world.rooms[3024].sector_type = 6
    elif change == "random":
        world.rooms[9850].random_exits = True
    elif change == "same_area":
        world.rooms[3024].area_file = "cult.are"
    assert _route(
        world, level=None if change == "unknown_level" else 11,
        blocked=(3024,) if change == "blocked" else (),
    ) == (None, (), 0)


@pytest.mark.parametrize("sentinel", [False, True])
def test_combat_only_guard_blocks_fighting_but_not_locator(sentinel):
    world = _world()
    world.mobiles[100] = MobileSource(
        100, "guard", "the cityguard", 30, ACT_SENTINEL if sentinel else 0, 0, "midgaard.are",
    )
    world.mob_resets.append(MobReset(100, 3024, 1, ()))
    world.mobile_specials[100] = ["spec_guard"]
    assert source_route_hazard_rejections(world, (9850, 3024), character_level=11)
    assert _route(world)[0] == "midgaard.are"
    world.mobiles[100] = replace(
        world.mobiles[100], act_flags=world.mobiles[100].act_flags | ACT_AGGRESSIVE,
    )
    assert _route(world) == (None, (), 0)


def test_locator_route_does_not_cross_more_than_six_moves():
    world = _world()
    for number in range(1, 8):
        world.rooms[number] = RoomSource(
            number, f"Passage {number}", "cult.are" if number < 7 else "third.are",
            exits={"east": ExitSource("east", number + 1, 0, -1)} if number < 7 else {},
        )
    world.rooms[9850].exits = {"east": ExitSource("east", 1, 0, -1)}
    assert _route(world) == (None, (), 0)
