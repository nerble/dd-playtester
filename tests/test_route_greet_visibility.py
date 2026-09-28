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
from dd4tester.visibility import invisibility_blocks_source_aggression


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


def test_live_invisibility_does_not_skip_registered_greet_preflight(source_world):
    policy, state = policy_and_state(source_world)
    assert policy.fastwalk_route.route_preflight_source_mobile_vnum == 3064
    decision = policy._fastwalk_route_preflight_decision(state)
    assert decision.command == "where drunk"
    assert not policy.fastwalk_route_preflight_complete

    policy._resolve_fastwalk_route_preflight(locations=("main street", "the main street"))
    decision = policy._fastwalk_route_preflight_decision(state)
    assert decision.command == "recall"
    assert policy.fastwalk_returning
    assert policy.fastwalk_route_preflight_hazard_observed


def test_live_invisibility_does_not_skip_adjacent_greet_scan(source_world):
    policy, state = policy_and_state(source_world)
    decision = policy._fastwalk_route_pre_entry_scan_decision(state, "3005", "south")
    assert decision.command == "scan south"
    assert policy.fastwalk_route_pre_entry_scan_pending is not None


def test_old_missing_source_identity_reproduces_recall_with_correct_location_text(source_world):
    policy, state = policy_and_state(source_world)
    policy.fastwalk_route = replace(policy.fastwalk_route, route_preflight_source_mobile_vnum=None)
    policy._resolve_fastwalk_route_preflight(locations=("main street", "the main street"))
    assert policy._fastwalk_route_preflight_decision(state).command == "recall"
    assert "at main street, the main street" in policy.fastwalk_abort_reason
    assert "observing from room 3001" in policy.fastwalk_abort_reason
    assert "hazard 'the drunk' in room 3001" not in policy.fastwalk_abort_reason
    assert policy.fastwalk_abort_reason.startswith(_FIELD_ROUTE_HAZARD_ABORT_PREFIXES)


def test_scan_ownership_is_preserved_while_invisible(source_world):
    policy, state = policy_and_state(source_world)
    assert policy._fastwalk_route_pre_entry_scan_decision(state, "3005", "south").command == "scan south"
    assert policy.fastwalk_route_pre_entry_scan_pending is not None
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
    policy.fastwalk_outbound_index = 1
    state.room_vnum = "3500"
    decision = policy._source_aggression_invisibility_decision(state)
    assert decision.command == "recall"
    assert policy.fastwalk_returning
    assert policy.fastwalk_abort_reason == (
        "source-aggressive route lacked fresh live invisibility"
    )


@pytest.mark.parametrize("duration", ["0", "1"])
def test_expiring_route_invisibility_waits_at_healer_before_recasting(
    source_world,
    duration,
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
        affects=[[{"name": "invis", "gives": "invisibility", "duration": duration}]],
    )

    assert policy._source_aggression_invisibility_decision(state) is None
    decision = policy._fastwalk_invisibility_decision(
        state,
        failure_command="north",
        failure_reason="return",
        cast_reason="cast",
        abort_reason="abort",
    )

    assert decision is not None
    assert decision.command == "north"
    assert policy.fastwalk_invisibility_expiry_wait_phase == "to_healer"

    state.room_vnum = "3054"
    state.position = 4
    assert policy._fastwalk_invisibility_expiry_wait_decision(state, "3054") is None
    state.affects = [[]]
    assert policy._fastwalk_invisibility_expiry_wait_decision(
        state,
        "3054",
    ).command == "stand"
    state.position = 7
    assert policy._fastwalk_invisibility_expiry_wait_decision(
        state,
        "3054",
    ).command == "south"
    state.room_vnum = "3001"
    assert policy._fastwalk_invisibility_expiry_wait_decision(state, "3001") is None
    assert policy._fastwalk_invisibility_expiry_wait_phase is None
    assert policy._fastwalk_invisibility_decision(
        state,
        failure_command="north",
        failure_reason="return",
        cast_reason="cast",
        abort_reason="abort",
    ).command == "cast invis"


def test_invisibility_expiry_wait_preempts_generic_sleep_wake(source_world):
    policy = StarterPolicy(
        CharacterSpec.from_mapping(
            {"name": "Testchar", "race": "human", "gender": "female", "class": "mage"}
        ),
        "unused",
        source_world=source_world,
        fastwalk_route=replace(
            route_named("moria"),
            route_invisibility_source_mobile_vnums=(4516,),
        ),
    )
    policy.in_world = policy.prompt_ready = True
    policy.fastwalk_invisibility_expiry_wait_phase = "await_sleep"
    state = CharacterState(
        level=18,
        hp=218,
        max_hp=218,
        mana=628,
        max_mana=628,
        move=312,
        max_move=320,
        room_vnum="3054",
        position=4,
        affects=[[]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "stand"
    assert policy.fastwalk_invisibility_expiry_wait_phase == "wake"


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
