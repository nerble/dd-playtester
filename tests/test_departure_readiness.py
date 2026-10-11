import pytest

from dd4tester.character import CharacterSpec
from dd4tester.equipment import STANCE_COMBAT, STANCE_RECOVERY
from dd4tester.fastwalks import Fastwalk
from dd4tester.starter import FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


def _policy(origin: int = 3001) -> StarterPolicy:
    spec = CharacterSpec.from_mapping({
        "name": "RouteTester", "race": "human", "gender": "female",
        "class": "warrior", "subclass": None, "title": "",
    })
    route = Fastwalk(
        "departure scan", 1, 100, "e",
        route_origin_room_vnum=origin,
        route_preflight_room_vnum="3001",
        route_preflight_command="where drunk",
        route_preflight_target="the drunk",
        route_preflight_hard_hazard=True,
        route_preflight_retryable=True,
        route_preflight_route_room_names=("wall road",),
        route_preflight_scan_room_vnums=("2171",),
    )
    policy = StarterPolicy(
        spec, "test-password", fastwalk_route=route,
        fastwalk_hunt_stops=(FieldHuntStop((), "bartender"),),
    )
    policy.gear_applied_stance = STANCE_COMBAT
    policy.fastwalk_recovery_ready = True
    return policy


def _origin_state(room: str = "3001") -> CharacterState:
    return CharacterState(
        level=31, hp=753, max_hp=743, mana=329, max_mana=290,
        move=449, max_move=502, room_vnum=room, room_flags=["safe"],
        position=7, exits={"e": "2171"},
    )


@pytest.mark.parametrize("origin", (3001, 3016))
def test_verified_origin_keeps_combat_gear_during_movement_only_checks(origin: int) -> None:
    policy = _policy(origin)
    assert policy._desired_gear_stance(_origin_state(str(origin))) == STANCE_COMBAT


@pytest.mark.parametrize("missing_gate", (
    "readiness", "origin", "health", "mana", "waiting",
    "returning", "combat_stance", "respawn_wait",
))
def test_origin_gear_retention_requires_completed_healthy_departure(missing_gate: str) -> None:
    policy = _policy()
    state = _origin_state()
    if missing_gate == "readiness":
        policy.fastwalk_recovery_ready = False
    elif missing_gate == "origin":
        state.room_vnum = "3005"
    elif missing_gate == "health":
        state.hp = 500
    elif missing_gate == "mana":
        state.mana = 100
    elif missing_gate == "waiting":
        policy.waiting_for_heal = True
    elif missing_gate == "returning":
        policy.fastwalk_returning = True
    elif missing_gate == "combat_stance":
        policy.gear_applied_stance = STANCE_RECOVERY
    else:
        policy.arena_respawn_due = 1.0
    assert policy._desired_gear_stance(state) == STANCE_RECOVERY


@pytest.mark.parametrize("blocked", (False, True))
def test_first_outbound_scan_retains_readiness_until_actual_dispatch(blocked: bool) -> None:
    policy = _policy(3016)
    policy.fastwalk_recall_started = True
    policy.fastwalk_route_preflight_complete = True
    state = _origin_state("3016")
    state.move = state.max_move

    scan = policy._fastwalk_research_decision(state)
    assert scan is not None and scan.command == "scan east"
    assert policy.fastwalk_outbound_index == 0
    assert policy.fastwalk_recovery_ready is True
    assert policy._desired_gear_stance(state) == STANCE_COMBAT

    policy.observe_text(
        "A singing, happy drunk who is one room to the east.\n"
        if blocked else "You can't see anything to the east.\n"
    )
    decision = policy._fastwalk_research_decision(state)
    assert decision is not None
    if blocked:
        assert decision.command == "recall"
        assert policy.fastwalk_outbound_index == 0
        assert policy.fastwalk_returning is True
        assert policy.fastwalk_abort_reason
        assert policy.fastwalk_recovery_ready is True
    else:
        assert decision.command == "east"
        assert policy.fastwalk_outbound_index == 1
        assert policy.fastwalk_recovery_ready is False
