import pytest

from dd4tester.character import CharacterSpec
from dd4tester.fastwalks import Fastwalk
from dd4tester.starter import FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


@pytest.mark.parametrize("kind,pending", [("xp", False), ("maintenance", True), ("legacy", True)])
def test_field_scan_abort_ends_ordinary_xp_trip_without_replaying_long_route(kind, pending):
    spec = CharacterSpec.from_mapping({
        "name": "Tester", "race": "human", "gender": "male", "class": "warrior",
    })
    route = Fastwalk(
        "source route", 1, 100, "s",
        route_preflight_room_vnum="3001", route_preflight_command="where crewman",
        route_preflight_target="the crewman", route_preflight_hard_hazard=True,
        route_preflight_retryable=True, route_preflight_route_room_names=("corridor",),
    )
    policy_id = "source-ranked-hunt-test-1-100-46" if kind != "legacy" else None
    required = ("an ivory staff",) if kind == "maintenance" else ()
    stop = FieldHuntStop(route=(), target="the carrier", source_policy_id=policy_id,
                         required_items=required)
    policy = StarterPolicy(spec, "test-password", fastwalk_route=route,
                           fastwalk_hunt_stops=(stop,))
    policy.in_world = True
    assert policy._fastwalk_route_preflight_retry_enabled()
    decision = policy._abort_fastwalk_route_pre_entry_scan("exact route hazard", "adjacent crewman")
    assert decision.command == "recall"
    assert policy.fastwalk_route_preflight_retry_pending is pending
    assert policy.fastwalk_route_hazards == ["adjacent crewman"]
    assert policy.fastwalk_abort_reason == "exact route hazard"
    assert policy.fastwalk_returning
    if kind == "xp":
        healer = CharacterState(level=46, room_vnum="3054", hp=1000, max_hp=1000,
                                mana=600, max_mana=600, move=600, max_move=600, position=7)
        assert policy._fastwalk_route_preflight_retry_decision(healer) is None
        # The cheap origin check remains available on a later ordinary visit.
        assert policy._fastwalk_route_preflight_retry_enabled()
