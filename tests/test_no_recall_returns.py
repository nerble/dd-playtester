import pytest

from dd4tester.character import CharacterSpec
from dd4tester.fastwalks import Fastwalk
from dd4tester.hunt_candidates import (
    ExitSource, RoomSource, WorldSource, ROOM_NO_RECALL, SECT_WATER_NOSWIM,
)
from dd4tester.starter import StarterPolicy
from dd4tester.state import CharacterState


def escape_policy():
    world = WorldSource(rooms={
        17299: RoomSource(
            17299, "Ice Hall", "test.are", room_flags=ROOM_NO_RECALL,
            exits={"up": ExitSource("up", 17278, 0, -1)},
        ),
        17278: RoomSource(17278, "Inside the Iceberg", "test.are", sector_type=SECT_WATER_NOSWIM),
    })
    policy = StarterPolicy(
        CharacterSpec.from_mapping({
            "name": "Tester", "race": "human", "gender": "male", "class": "warrior",
        }),
        "password", source_world=world,
        fastwalk_route=Fastwalk(name="gear route", minimum_level=1, maximum_level=100,
                               notation="recall;south", recall_after_loot=True),
    )
    return policy


@pytest.mark.parametrize("returning", [False, True])
def test_flying_return_prefers_checked_local_exit_before_long_graph(returning):
    policy = escape_policy()
    state = CharacterState(
        level=46, room_vnum="17299", room_flags=["no_recall"], position=7,
        hp=900, max_hp=1100, affects=[[{"name": "fly", "duration": "18"}]],
    )
    if returning:
        policy.fastwalk_returning = True
        decision = policy._fastwalk_research_decision(state)
        assert policy.fastwalk_recovery_commands == ("up", "recall")
    else:
        policy.fastwalk_route = None
        decision = policy._return_home_decision(state)
        assert policy.return_home_recovery_commands == ("up", "recall")
    assert decision.command == "up"


@pytest.mark.parametrize("hazard", ["no_flight", "combat", "dead"])
def test_local_escape_keeps_movement_and_combat_gates(hazard):
    policy = escape_policy()
    state = CharacterState(
        level=46, room_vnum="17299", room_flags=["no_recall"], position=7,
        affects=[] if hazard == "no_flight" else [[{"name": "fly"}]],
        in_combat=hazard == "combat", dead=hazard == "dead",
    )
    assert policy._source_recall_escape_for_state(state) is None
