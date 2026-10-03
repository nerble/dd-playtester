import json
from copy import deepcopy
from dataclasses import replace

import pytest

from dd4tester import campaign as cp
from dd4tester.hunt_candidates import HuntCandidate, RoomSource, WorldSource


@pytest.fixture
def city_repeat_case(monkeypatch):
    candidate = HuntCandidate(
        status="caution", score=10, area_file="test.are", mobile_vnum=123,
        target="a plain target", target_keyword="target", level=25,
        room_vnum=4000, room_name="Test endpoint", route=("south", "south"),
        source_spawn_limit=1, room_spawn_count=1, boot_kills=9, loot=(),
        source_value=0, contained_coins=0, hazards=(),
        estimated_level_range=(23, 27), estimated_base_hp_range=(100, 200),
        estimated_peak_round_damage=20, estimated_move_cost=30,
    )
    policy = cp._source_ranked_policy_id(candidate, character_level=29)
    old_city = {
        "boot_id": "boot", "level": 29, "complete": True, "blocked": True,
        "locations": ["old road"], "policy_id": policy, "run_id": 100,
        "stopped_before_departure": True, "outbound_index": 0,
        "wait_attempts": 3, "detour": None, "route_correction": None,
        "route_correction_attempted": False,
    }
    start = {
        "world_boot_id": "boot", "level": 29, "room_vnum": "3054",
        "hp": 666, "max_hp": 666, "move": 482, "max_move": 482,
        "xp": 1000, "xp_loss_total": 0, cp._SOURCE_REVISION_KEY: "revision",
        cp._SOURCE_RANKED_CANDIDATE_KEY: cp._source_ranked_candidate_record(
            candidate, character_level=29, source_revision="revision",
        ),
    }
    end = {**start, "campaign_field_city_preflight": old_city}
    current_city = {
        **old_city, "blocked": False, "locations": ["new road"], "run_id": 101,
    }
    state = {
        **end, "campaign_field_city_preflight": current_city,
        cp._FIELD_CITY_BLOCKED_POLICIES_KEY: {
            "boot_id": "boot", "level": 29, "policy_ids": [policy],
        },
    }
    segments = [
        {"id": 42, "run_id": 100, "phase": policy, "status": "success",
         "start_state_json": json.dumps(start), "end_state_json": json.dumps(end)},
        {"id": 43, "run_id": 101, "phase": "quest-request", "status": "success",
         "start_state_json": json.dumps(end), "end_state_json": json.dumps(state)},
    ]
    world = WorldSource(rooms={3054: RoomSource(3054, "Healer", "midgaard.are")})
    monkeypatch.setattr(cp, "_source_ranked_observed_route_blocked_room_vnums",
                        lambda *args, **kwargs: (3002,))
    direct = (("south", "south"), (3001, 3002, 4000))
    alternate = (("east",) * 24, (3001, *range(3100, 3123), 4000))
    monkeypatch.setattr(cp, "_shortest_paths_from", lambda *args, **kwargs: {
        4000: alternate if kwargs.get("blocked_rooms") else direct,
    })
    return candidate, policy, state, world, segments


def arm(case, *, latest_xp=1435):
    candidate, _, state, world, segments = case
    repeats = cp._source_ranked_repeatable_policy_ids(
        [candidate], state, character_level=29, policy_xp_deltas={},
        source_mobile_xp_deltas={candidate.mobile_vnum: latest_xp},
    )
    return cp._arm_field_city_alternate_route_revalidation(
        state, [candidate], source_world=world, segments=segments,
        allow_repeated_policy_ids=repeats,
    )


def test_productive_kill_history_can_admit_one_exact_city_route_recheck(city_repeat_case):
    candidate, policy, state, _, _ = city_repeat_case
    old_blocked = deepcopy(state[cp._FIELD_CITY_BLOCKED_POLICIES_KEY])
    assert arm(city_repeat_case) == policy
    marker = state[cp._FIELD_CITY_ALTERNATE_ROUTE_REVALIDATION_KEY]
    assert marker["repeat_after_kill_cap"] is True
    assert marker["prior_run_id"] == 100
    assert state[cp._FIELD_CITY_BLOCKED_POLICIES_KEY] == old_blocked
    assert cp._mark_field_city_alternate_route_revalidation(
        state, candidate, character_level=29,
    )
    assert arm(city_repeat_case) is None


@pytest.mark.parametrize("latest_xp", [0, 10])
def test_kill_count_without_meaningful_xp_cannot_reopen_city_route(city_repeat_case, latest_xp):
    assert arm(city_repeat_case, latest_xp=latest_xp) is None


@pytest.mark.parametrize("change", ["stale_locator", "changed_xp", "old_boot", "hazard", "below_band"])
def test_productive_repeat_never_bypasses_other_city_recheck_gates(city_repeat_case, change):
    candidate, policy, state, world, segments = city_repeat_case
    if change == "stale_locator":
        state["campaign_field_city_preflight"]["run_id"] = 99
        observation = json.loads(segments[1]["end_state_json"])
        observation["campaign_field_city_preflight"]["run_id"] = 99
        segments[1]["end_state_json"] = json.dumps(observation)
    elif change == "changed_xp":
        observation = json.loads(segments[1]["end_state_json"])
        observation["xp"] += 10
        segments[1]["end_state_json"] = json.dumps(observation)
    elif change == "old_boot":
        state["world_boot_id"] = "new-boot"
    elif change == "hazard":
        candidate = replace(candidate, autonomy_rejections=("unknown hazard",))
    else:
        candidate = replace(candidate, estimated_level_range=(20, 24))
    assert arm((candidate, policy, state, world, segments)) is None
