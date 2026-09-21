from dataclasses import replace
from pathlib import Path

import pytest

from dd4tester.campaign import _FIELD_ROUTE_HAZARD_ABORT_PREFIXES, _source_guard_fixed_fastwalk_route
from dd4tester.character import CharacterSpec
from dd4tester.fastwalks import route_named
from dd4tester.hunt_candidates import MobileProgram, load_world_source
from dd4tester.observations import GameEvent
from dd4tester.starter import FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState
from dd4tester.visibility import (
    invisibility_blocks_source_aggression,
    invisibility_blocks_source_greet,
)


@pytest.fixture(scope="module")
def source_world():
    directory = Path("runs/dd4-source/server/area")
    if not directory.is_dir():
        pytest.skip("optional DD4 source mirror is not installed")
    return load_world_source(directory, include_all_areas=True)


def policy_and_state(world):
    route = _source_guard_fixed_fastwalk_route(world, route_named("moria"), character_level=18)
    policy = StarterPolicy(
        CharacterSpec.from_mapping({"name": "Testchar", "race": "human", "gender": "female", "class": "mage"}),
        "unused", source_world=world, fastwalk_route=route,
    )
    policy.in_world = policy.prompt_ready = True
    policy.current_room = "3001"
    state = CharacterState(
        level=18, hp=218, max_hp=218, mana=628, max_mana=628, move=312,
        max_move=320, room_vnum="3001", position=7,
        progress={"alignment": 1000},
        affects=[[{"name": "invis", "gives": "invisibility", "duration": "17"}]],
    )
    policy.observe_events([GameEvent("affects_changed", "gmcp", {})], state)
    return policy, state


def test_run_12828_live_invisibility_prevents_false_greet_departure_veto(source_world):
    policy, state = policy_and_state(source_world)
    assert policy.fastwalk_route.route_preflight_source_mobile_vnum == 3064
    policy._resolve_fastwalk_route_preflight(locations=("main street", "the main street"))
    assert policy._fastwalk_route_preflight_decision(state) is None
    assert not policy.fastwalk_returning
    assert not policy.fastwalk_route_preflight_complete
    assert policy.fastwalk_route_invisibility_checks == [{
        "source_mobile_vnum": 3064, "from_room": "3001", "destination": "3001",
        "reason": "live invisibility blocks source greet visibility",
    }]
    assert policy._fastwalk_route_pre_entry_scan_decision(state, "3005", "south") is None
    assert not policy.fastwalk_route_pre_entry_scan_checked


def test_old_missing_source_identity_reproduces_recall_with_correct_location_text(source_world):
    policy, state = policy_and_state(source_world)
    policy.fastwalk_route = replace(policy.fastwalk_route, route_preflight_source_mobile_vnum=None)
    policy._resolve_fastwalk_route_preflight(locations=("main street", "the main street"))
    assert policy._fastwalk_route_preflight_decision(state).command == "recall"
    assert "at main street, the main street" in policy.fastwalk_abort_reason
    assert "observing from room 3001" in policy.fastwalk_abort_reason
    assert "hazard 'the drunk' in room 3001" not in policy.fastwalk_abort_reason
    assert policy.fastwalk_abort_reason.startswith(_FIELD_ROUTE_HAZARD_ABORT_PREFIXES)


@pytest.mark.parametrize("boundary", [
    "no_live_affect", "disconnect", "expired", "last_tick", "hidden_duration", "wrong_affect",
    "combat", "death", "runtime", "return", "other_hazard", "unaudited", "unknown_destination",
])
def test_visibility_is_not_a_durable_or_general_permission(source_world, boundary):
    policy, state = policy_and_state(source_world)
    destination = "3005"
    if boundary == "no_live_affect":
        policy.route_visibility_affects_observed = False
    elif boundary == "disconnect":
        policy.on_connection_closed()
    elif boundary in {"expired", "last_tick", "hidden_duration"}:
        state.affects[0][0]["duration"] = {"expired": "0", "last_tick": "1", "hidden_duration": "???"}[boundary]
    elif boundary == "wrong_affect":
        state.affects[0][0]["name"] = "detect invis"
    elif boundary == "combat":
        state.in_combat = True
    elif boundary == "death":
        state.dead = True
    elif boundary == "runtime":
        policy.runtime_boundary_requested = True
    elif boundary == "return":
        policy.return_home = True
    elif boundary == "other_hazard":
        policy.fastwalk_route = replace(policy.fastwalk_route, route_hard_hazard_targets=("another hazard",))
    elif boundary == "unaudited":
        policy.fastwalk_route = replace(policy.fastwalk_route, route_source_program_audited=False)
    else:
        destination = None
    if boundary == "unknown_destination":
        assert policy._fastwalk_route_pre_entry_scan_decision(state, destination, "south").command == "recall"
    else:
        assert not policy._route_greet_blocked_by_invisibility(state, destination=destination)


def test_wearoff_restores_next_step_scan_without_reusing_invisible_checks(source_world):
    policy, state = policy_and_state(source_world)
    assert policy._fastwalk_route_pre_entry_scan_decision(state, "3005", "south") is None
    state.affects = []
    policy.observe_events([GameEvent("affects_changed", "gmcp", {})], state)
    assert policy._fastwalk_route_pre_entry_scan_decision(state, "3005", "south").command == "scan south"


def test_fragmented_dispel_message_overrides_a_lingering_affect_record(source_world):
    policy, state = policy_and_state(source_world)
    policy.observe_text("You are no longer inv")
    policy.observe_text("isible.\n\r")
    policy.observe_events([GameEvent("affects_changed", "gmcp", {})], state)
    assert not policy._route_greet_blocked_by_invisibility(state, destination="3005")
    policy.observe_text("You fade out of existence.\n\r")
    assert not policy._route_greet_blocked_by_invisibility(state, destination="3005")
    policy.observe_events([GameEvent("affects_changed", "gmcp", {})], state)
    assert policy._route_greet_blocked_by_invisibility(state, destination="3005")


def test_another_characters_speech_is_not_an_invisibility_loss(source_world):
    policy, state = policy_and_state(source_world)
    policy.observe_text("Someone says 'You are no longer invisible.'\n\r")
    assert policy._route_greet_blocked_by_invisibility(state, destination="3005")


def test_visibility_does_not_erase_already_started_scan_ownership(source_world):
    policy, state = policy_and_state(source_world)
    policy.route_visibility_affects_observed = False
    policy._fastwalk_route_pre_entry_scan_decision(state, "3005", "south")
    policy.route_visibility_affects_observed = True
    policy.fastwalk_route_pre_entry_scan_response_buffer = "You can't see anything southwards."
    assert policy._fastwalk_route_pre_entry_scan_decision(state, "3005", "south") is None
    assert policy.fastwalk_route_pre_entry_scan_pending is None


def test_greet_visibility_does_not_waive_unrelated_required_loot_scan(source_world):
    policy, state = policy_and_state(source_world)
    stop = FieldHuntStop(
        (), "large hobgoblin", required_items=("purple potion",),
        allow_below_band_for_required_loot=True, pre_entry_scan_room_vnums=("4064",),
        pre_entry_scan_hazard_source_mobile_vnums=(4051,),
    )
    assert policy._fastwalk_pre_entry_scan_decision(state, stop, "4064", "down").command == "scan down"


@pytest.mark.parametrize("change", [
    "detect_invis", "all_greet", "random_attack", "casting", "high_level", "special",
    "aggressive", "equipment", "no_reset", "wrong_target", "unknown_source", "no_program",
])
def test_source_visibility_exceptions_retain_preflight(source_world, change):
    world = replace(source_world, mobiles=dict(source_world.mobiles),
                    mob_resets=list(source_world.mob_resets), mobile_specials=dict(source_world.mobile_specials))
    mobile, target, vnum = world.mobiles[3064], "the drunk", 3064
    if change == "detect_invis":
        mobile = replace(mobile, affected_flags=8)
    elif change == "all_greet":
        mobile = replace(mobile, programs=(MobileProgram("all_greet_prog", "10", ("mpkill $n",)),))
    elif change == "random_attack":
        mobile = replace(mobile, programs=(*mobile.programs, MobileProgram("rand_prog", "10", ("mpkill $n",))))
    elif change == "casting":
        mobile = replace(mobile, programs=(*mobile.programs, MobileProgram("rand_prog", "10", ("cast 'detect invis'",))))
    elif change == "high_level":
        mobile = replace(mobile, level=100)
    elif change == "special":
        world.mobile_specials[3064] = ("spec_mage",)
    elif change == "aggressive":
        mobile = replace(mobile, act_flags=32)
    elif change == "equipment":
        world.mob_resets = [replace(r, equipment=((16, 1),)) if r.mobile_vnum == 3064 else r for r in world.mob_resets]
    elif change == "no_reset":
        world.mob_resets = [r for r in world.mob_resets if r.mobile_vnum != 3064]
    elif change == "wrong_target":
        target = "another drunk"
    elif change == "unknown_source":
        vnum = None
    else:
        mobile = replace(mobile, programs=())
    world.mobiles[3064] = mobile
    assert not invisibility_blocks_source_greet(world, vnum, target=target)


@pytest.mark.parametrize("mobile_vnum", [3062, 3501, 3506, 4516])
def test_haglik_route_aggression_is_source_blocked_by_invisibility(
    source_world,
    mobile_vnum,
):
    assert invisibility_blocks_source_aggression(source_world, mobile_vnum)


@pytest.mark.parametrize(
    "change",
    [
        "detect_invis",
        "equipped_detect_invis",
        "missing_equipment_source",
        "missing_reset",
        "program",
        "dangerous_special",
        "peaceful",
        "high_level",
        "unknown",
    ],
)
def test_source_aggression_visibility_rejects_unproved_boundaries(
    source_world,
    change,
):
    world = replace(
        source_world,
        mobiles=dict(source_world.mobiles),
        objects=dict(source_world.objects),
        mob_resets=list(source_world.mob_resets),
        mobile_specials=dict(source_world.mobile_specials),
    )
    mobile_vnum = 4516
    mobile = world.mobiles[mobile_vnum]
    if change == "detect_invis":
        mobile = replace(mobile, affected_flags=mobile.affected_flags | 8)
    elif change == "equipped_detect_invis":
        world.objects[4530] = replace(
            world.objects[4530],
            affects=(*world.objects[4530].affects, (29, 0)),
        )
    elif change == "missing_equipment_source":
        del world.objects[4530]
    elif change == "missing_reset":
        world.mob_resets = [
            reset for reset in world.mob_resets if reset.mobile_vnum != mobile_vnum
        ]
    elif change == "program":
        mobile = replace(
            mobile,
            programs=(MobileProgram("rand_prog", "10", ("say Halt!",)),),
        )
    elif change == "dangerous_special":
        world.mobile_specials[mobile_vnum] = ("spec_poison",)
    elif change == "peaceful":
        mobile = replace(mobile, act_flags=mobile.act_flags & ~32)
    elif change == "high_level":
        mobile = replace(mobile, level=100)
    else:
        mobile_vnum = 999_999
    world.mobiles[4516] = mobile

    assert not invisibility_blocks_source_aggression(world, mobile_vnum)


def test_source_aggression_route_requires_fresh_live_invisibility(source_world):
    policy, state = policy_and_state(source_world)
    policy.fastwalk_route = replace(
        policy.fastwalk_route,
        route_invisibility_source_mobile_vnums=(3062, 3501, 3506, 4516),
    )
    policy.fastwalk_require_invisibility = True

    assert policy._source_aggression_invisibility_decision(state) is None
    assert policy.fastwalk_route_invisibility_checks[-1] == {
        "source_mobile_vnums": [3062, 3501, 3506, 4516],
        "from_room": "3001",
        "outbound_index": 0,
        "duration": 17,
        "reason": "fresh live invisibility blocks source aggression",
    }

    state.affects[0][0]["duration"] = "1"
    decision = policy._source_aggression_invisibility_decision(state)
    assert decision.command == "north"
    assert policy.fastwalk_returning
    assert policy.fastwalk_abort_reason == (
        "source-aggressive route lacked fresh live invisibility"
    )


def test_source_aggression_route_without_invisibility_fails_closed(source_world):
    route = replace(
        route_named("moria"),
        route_invisibility_source_mobile_vnums=(1001,),
    )
    policy = StarterPolicy(
        CharacterSpec.from_mapping(
            {"name": "Testchar", "race": "human", "gender": "female", "class": "warrior"}
        ),
        "unused",
        source_world=source_world,
        fastwalk_route=route,
    )
    state = CharacterState(
        level=11,
        hp=218,
        max_hp=218,
        mana=628,
        max_mana=628,
        move=312,
        max_move=320,
        room_vnum="3001",
        position=7,
        affects=[],
    )

    decision = policy._fastwalk_invisibility_decision(
        state,
        failure_command="north",
        failure_reason="return",
        cast_reason="cast",
        abort_reason="abort",
    )

    assert decision is not None
    assert decision.command == "north"
    assert policy.fastwalk_returning
    assert policy.fastwalk_abort_reason == "abort"


def test_source_aggression_route_casts_only_at_origin_and_recalls_after_wearoff(
    source_world,
):
    route = replace(
        route_named("moria"),
        route_invisibility_source_mobile_vnums=(4516,),
    )
    policy = StarterPolicy(
        CharacterSpec.from_mapping(
            {"name": "Testchar", "race": "human", "gender": "female", "class": "mage"}
        ),
        "unused",
        source_world=source_world,
        fastwalk_route=route,
        known_skill_levels={"invis": 42},
    )
    policy.in_world = policy.prompt_ready = True
    policy.current_room = "3001"
    state = CharacterState(
        level=18,
        hp=218,
        max_hp=218,
        mana=628,
        max_mana=628,
        move=312,
        max_move=320,
        room_vnum="3001",
        position=7,
        progress={"alignment": 1000},
        affects=[],
    )

    assert policy.fastwalk_require_invisibility
    assert policy._source_aggression_invisibility_decision(state) is None
    assert policy._fastwalk_invisibility_decision(
        state,
        failure_command="north",
        failure_reason="return",
        cast_reason="cast",
        abort_reason="abort",
    ).command == "cast invis"

    policy.fastwalk_invisibility_pending = False
    policy.fastwalk_outbound_index = 1
    state.room_vnum = "3500"
    decision = policy._source_aggression_invisibility_decision(state)
    assert decision.command == "recall"
    assert policy.fastwalk_emergency_recall_pending
