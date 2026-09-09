import asyncio
from dataclasses import replace
from pathlib import Path

import pytest

import dd4tester.campaign as campaign
from dd4tester.character import CharacterSpec
from dd4tester.hunt_candidates import ACT_SENTINEL, load_world_source, rank_hunt_candidates
from dd4tester.starter import StarterPolicy
from test_early_funding_locator import _world


def _capture_dispatch(monkeypatch, world, candidate, state, **kwargs):
    captured = {}

    class CaptureRunner:
        def __init__(self, *args, **options):
            captured.update(options)

        async def run(self):
            return None

    monkeypatch.setattr(campaign, "StarterBotRunner", CaptureRunner)
    monkeypatch.setattr(campaign, "load_world_source", lambda *args, **kw: world)
    spec = CharacterSpec.from_mapping({
        "name": "Testchar", "race": "human", "gender": "female", "class": "mage",
    })
    asyncio.run(campaign._run_policy_segment(
        spec, Path("unused.yaml"), campaign._SOURCE_RANKED_HUNT_POLICY,
        source_world=world, source_ranked_hunt_candidate=candidate,
        character_level=8, current_state=state, **kwargs,
    ))
    return captured, spec


@pytest.mark.parametrize("waypoints,expected", [
    ((), (("north",), 4000)),
    ((4001,), (("north", "north"), 4001)),
    (("4001",), (("north", "north"), 4001)),
    ((4000, 4001), (("north", "north"), 4001)),
    ((4002,), (("north",) * 3, None)),
    ((4031,), (("north",) * 3, None)),
])
def test_early_hunt_locator_keeps_every_required_waypoint(waypoints, expected):
    world, candidate = _world()
    assert campaign._source_ranked_early_locator_route(
        world, candidate, character_level=8, required_waypoints=waypoints,
    ) == expected


def test_normal_dispatch_locates_before_reset_and_preserves_target_contract(monkeypatch):
    world, candidate = _world()
    state = {"level": 8, "max_hp": 113, "max_move": 220}
    old = campaign._source_ranked_circuit_hunt_stops(candidate, (), world, character_level=8, state=state)
    captured, _ = _capture_dispatch(monkeypatch, world, candidate, state)
    route, stops = captured["fastwalk_route"], captured["fastwalk_hunt_stops"]
    assert route.commands == ("north",)
    assert stops[0].actions == ("where orc",) and not stops[0].route_vnums
    assert stops[1].route_vnums == ("4001", "4002")
    for new, previous in zip(stops[1:], old[1:], strict=True):
        assert replace(new, route=previous.route, route_vnums=previous.route_vnums) == previous
    assert candidate.route == ("north",) * 3
    assert route.route_preflight_room_vnum == candidate.route_preflight_room_vnum
    assert captured["fastwalk_required_move"] == campaign._source_candidate_required_move(candidate, state)
    assert captured["fastwalk_kill_limit"] == campaign._source_ranked_segment_kill_limit(
        (candidate,), old, minimum=campaign._SOURCE_RANKED_HUNT_POLICY.segment_kill_limit or 1,
    )


@pytest.mark.parametrize("boundary", ["sentinel", "closed", "late_preflight", "hard_hazard"])
def test_normal_dispatch_retains_unshortenable_approach(monkeypatch, boundary):
    world, candidate = _world()
    if boundary == "sentinel":
        world.mobiles[1] = replace(world.mobiles[1], act_flags=ACT_SENTINEL)
    elif boundary == "closed":
        world.rooms[4001].exits["north"] = replace(world.rooms[4001].exits["north"], reset_state=1)
    elif boundary == "late_preflight":
        candidate = replace(candidate, route_preflight_room_vnum="4002")
    else:
        candidate = replace(candidate, route_hard_hazard_targets=("a danger",))
    captured, _ = _capture_dispatch(monkeypatch, world, candidate, {"level": 8, "max_hp": 113})
    assert captured["fastwalk_route"].commands == candidate.route


def test_specialised_transit_return_is_not_shortened_again(monkeypatch):
    world, candidate = _world()
    original = campaign._source_ranked_circuit_hunt_stops(candidate, (), world, character_level=8)
    monkeypatch.setattr(campaign, "_source_ranked_route_with_transit_recovery", lambda *args: (("north",), original, candidate.route))
    monkeypatch.setattr(campaign, "_source_ranked_early_locator_route", lambda *args, **kw: pytest.fail("must retain the transit return plan"))
    captured, _ = _capture_dispatch(monkeypatch, world, candidate, {"level": 8})
    assert captured["fastwalk_route"].return_commands == candidate.route
    assert captured["fastwalk_hunt_stops"] == original


def test_early_origin_changes_only_the_first_circuit_leg():
    world, candidate = _world()
    # The existing second-leg controller still starts from the first source
    # endpoint, not the new initial locator waypoint.
    secondary = replace(candidate, room_vnum=4031, room_name="The valley")
    before = campaign._source_ranked_circuit_hunt_stops(candidate, (secondary,), world, character_level=8)
    after = campaign._source_ranked_circuit_hunt_stops(
        candidate, (secondary,), world, character_level=8,
        hunt_route_origin_room_vnum=4000, locate_before_reset=True,
    )
    first_count = len(campaign._source_ranked_hunt_stops(candidate, world, character_level=8))
    assert after[first_count:] == before[first_count:]


def test_run_12812_dispatch_preserves_staging_and_locates_before_expensive_reset(monkeypatch):
    world = load_world_source(Path("runs/dd4-source/server/area"), include_all_areas=True)
    state = {
        "level": 8, "character_class": "mage", "max_hp": 113, "max_mana": 324, "max_move": 220,
        "campaign_known_skills": ["chill touch", "summon familiar"],
        "campaign_known_skill_levels": {"chill touch": 35, "summon familiar": 36},
    }
    candidate = next(c for c in rank_hunt_candidates(
        world, character_level=8, character_class="mage", character_max_hp=113,
        known_skills=state["campaign_known_skills"], known_skill_levels=state["campaign_known_skill_levels"],
        include_xp_only=True, include_level_ceiling_candidates=True, level_ceiling_offset=1, include_all_areas=True,
    ) if c.mobile_vnum == 4005 and c.room_vnum == 4022)
    captured, spec = _capture_dispatch(monkeypatch, world, candidate, state)
    route, stops = captured["fastwalk_route"], captured["fastwalk_hunt_stops"]
    assert len(candidate.route) == 21 and len(route.commands) == 13
    assert all(stop.familiar_staging_room_vnum == "4002" for stop in stops if stop.target)
    assert all(stop.require_familiar for stop in stops if stop.target)
    assert stops[0].actions == ("where orc",) and not stops[0].route_vnums
    policy = StarterPolicy(spec, "fixture-password", source_world=world, fastwalk_route=route, fastwalk_hunt_stops=stops)
    policy.current_room = "4002"
    policy.fastwalk_hunt_action_index = 1
    policy.fastwalk_where_response_pending = True
    policy.observe_text(
        "You detect the presence of:\n"
        "The large orc                The cave\n"
        "The orc                      The cave entrance\n"
        "The orc                      The tunnel\n"
    )
    assert policy.fastwalk_where_locations == ("the cave",)
    target = policy.fastwalk_hunt_stops[1]
    assert target.source_mobile_vnum == 4005 and target.require_familiar and target.require_isolated
    assert target.familiar_staging_room_vnum == "4002"
    assert len(route.commands) + len(target.route_vnums) < len(candidate.route) + 7
    assert "4022" not in target.route_vnums
