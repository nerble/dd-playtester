import pytest

from dd4tester.character import CharacterSpec
from dd4tester.equipment import STANCE_COMBAT, STANCE_RECOVERY
from dd4tester.fastwalks import route_named
from dd4tester.starter import FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


def _policy() -> StarterPolicy:
    policy = StarterPolicy(
        CharacterSpec("Aldrin", "DD4_TEST_PASSWORD", "human", "male", "warrior"),
        "swordfish", fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(FieldHuntStop((), "war dog"),),
    )
    policy.gear_applied_stance = STANCE_COMBAT
    policy.fastwalk_recovery_ready = True
    return policy


def _state() -> CharacterState:
    return CharacterState(
        hp=743, max_hp=743, mana=329, max_mana=290,
        move=450, max_move=502, position=7, room_vnum="3005", room_flags=["safe"],
    )


@pytest.mark.parametrize("step", [1, 2, 3])
def test_registered_fountain_preflight_keeps_combat_boots(step: int) -> None:
    policy = _policy()
    policy.fastwalk_water_preflight_step = step
    assert policy._desired_gear_stance(_state()) == STANCE_COMBAT


@pytest.mark.parametrize("gate", ["unready", "step", "returning", "outbound", "room", "health", "mana"])
def test_fountain_retention_keeps_existing_recovery_gates(gate: str) -> None:
    policy = _policy()
    policy.fastwalk_water_preflight_step = 2
    state = _state()
    if gate == "unready":
        policy.fastwalk_recovery_ready = False
    elif gate == "step":
        policy.fastwalk_water_preflight_step = 4
    elif gate == "returning":
        policy.fastwalk_returning = True
    elif gate == "outbound":
        policy.fastwalk_outbound_index = 1
        state.hp = 500
    elif gate == "room":
        state.room_vnum = "3006"
    elif gate == "health":
        state.hp = 500
    else:
        state.mana = 50
    assert policy._desired_gear_stance(state) == STANCE_RECOVERY


def test_healer_return_keeps_applied_recovery_gear_after_waking() -> None:
    policy = _policy()
    policy.fastwalk_returning = True
    policy.fastwalk_outbound_index = 15
    policy.gear_applied_stance = STANCE_RECOVERY
    state = _state()
    state.room_vnum = "3054"
    state.max_move = 450
    assert policy._desired_gear_stance(state) == STANCE_RECOVERY
    policy.fastwalk_returning = False
    assert policy._desired_gear_stance(state) == STANCE_COMBAT
