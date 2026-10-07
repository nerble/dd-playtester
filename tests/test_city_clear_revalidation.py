import json
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

import pytest

from dd4tester import campaign as cp
from dd4tester.hunt_candidates import ExitSource, HuntCandidate, RoomSource, WorldSource


@pytest.fixture
def clear_city_case(monkeypatch):
    candidate = HuntCandidate(
        status="caution", score=10, area_file="test.are", mobile_vnum=123,
        target="a plain target", target_keyword="target", level=25,
        room_vnum=4000, room_name="Endpoint", route=("south", "south"),
        source_spawn_limit=1, room_spawn_count=1, boot_kills=0, loot=(),
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
        "room_flags": ["safe", "healing"], "hp": 666, "max_hp": 666,
        "move": 482, "max_move": 482, "mana": 100, "max_mana": 100,
        "xp": 1000, "xp_loss_total": 0, cp._SOURCE_REVISION_KEY: "old-revision",
        cp._SOURCE_RANKED_CANDIDATE_KEY: cp._source_ranked_candidate_record(
            candidate, character_level=29, source_revision="old-revision",
        ),
    }
    end = {**start, "campaign_field_city_preflight": old_city}
    current_city = {
        **old_city, "blocked": False, "locations": ["new road"], "run_id": 101,
    }
    observation_start = {**end, cp._SOURCE_REVISION_KEY: "current-revision"}
    state = {
        **observation_start, "affects": [],
        "campaign_field_city_preflight": current_city,
        cp._FIELD_CITY_BLOCKED_POLICIES_KEY: {
            "boot_id": "boot", "level": 29, "policy_ids": [policy],
        },
    }
    segments = [
        {"id": 42, "run_id": 100, "phase": policy, "status": "success",
         "start_state_json": json.dumps(start), "end_state_json": json.dumps(end)},
        {"id": 43, "run_id": 101, "phase": "maintenance", "status": "success",
         "start_state_json": json.dumps(observation_start), "end_state_json": json.dumps(state)},
    ]
    world = WorldSource(rooms={
        3054: RoomSource(3054, "Healer", "midgaard.are"),
        3001: RoomSource(3001, "Temple", "midgaard.are", {
            "south": ExitSource("south", 3002, 0, 0),
        }),
        3002: RoomSource(3002, "Old Road", "midgaard.are", {
            "south": ExitSource("south", 4000, 0, 0),
        }),
        3011: RoomSource(3011, "New Road", "midgaard.are"),
        4000: RoomSource(4000, "Endpoint", "test.are"),
    })
    monkeypatch.setattr(cp, "_source_ranked_candidate_in_current_band", lambda *a, **kw: True)
    monkeypatch.setattr(cp, "_source_ranked_hp_probe_admission_available", lambda *a, **kw: True)
    monkeypatch.setattr(cp, "_source_ranked_candidate_requires_sanctuary_for_state", lambda *a, **kw: False)
    return candidate, policy, state, world, segments


def arm(case, **kwargs):
    candidate, _policy, state, world, segments = case
    return cp._arm_field_city_clear_route_revalidation(
        state, [candidate], source_world=world, segments=segments, **kwargs,
    )


def test_clear_route_recheck_is_one_shot_and_preserves_old_closure(clear_city_case):
    candidate, policy, state, _world, _segments = clear_city_case
    ledger = deepcopy(state[cp._FIELD_CITY_BLOCKED_POLICIES_KEY])
    assert arm(clear_city_case) == policy
    marker = state[cp._FIELD_CITY_CLEAR_ROUTE_REVALIDATION_KEY]
    assert marker["prior_blocked_room_vnums"] == [3002]
    assert marker["blocked_room_vnums"] == [3011]
    assert marker["observation_run_id"] == 101
    assert marker["prior_source_revision"] == "old-revision"
    assert marker["source_revision"] == "current-revision"
    assert state[cp._FIELD_CITY_BLOCKED_POLICIES_KEY] == ledger
    assert cp._mark_field_city_alternate_route_revalidation(state, candidate, character_level=29)
    assert marker is not state[cp._FIELD_CITY_CLEAR_ROUTE_REVALIDATION_KEY]
    assert arm(clear_city_case) is None


@pytest.mark.parametrize("change", [
    "unknown_location", "on_route", "duplicate_on_route", "inherited_locator",
    "changed_xp", "prior_loss", "prior_kill", "left_healer", "changed_route",
    "second_wait", "detour", "old_boot", "target_loss", "requires_flight",
])
def test_clear_route_recheck_rejects_incomplete_or_changed_evidence(clear_city_case, change):
    candidate, policy, state, world, segments = clear_city_case
    old_end = json.loads(segments[0]["end_state_json"])
    observation = json.loads(segments[1]["end_state_json"])
    if change == "unknown_location":
        state["campaign_field_city_preflight"]["locations"] = ["unknown"]
    elif change == "on_route":
        state["campaign_field_city_preflight"]["locations"] = ["old road"]
    elif change == "duplicate_on_route":
        world.rooms[3002].name = "New Road"
    elif change == "inherited_locator":
        observation["campaign_field_city_preflight"]["run_id"] = 99
    elif change == "changed_xp":
        observation["xp"] += 1
    elif change == "prior_loss":
        old_end["xp_loss_total"] = 1
    elif change == "prior_kill":
        old_end["campaign_objective_kills"] = ["a target"]
    elif change == "left_healer":
        old_end["room_vnum"] = "3001"
    elif change == "changed_route":
        candidate = replace(candidate, route=("north",))
    elif change == "second_wait":
        old_end["campaign_field_city_preflight"]["wait_attempts"] = 2
    elif change == "detour":
        old_end["campaign_field_city_preflight"]["detour"] = {"attempted": True}
    elif change == "old_boot":
        state["world_boot_id"] = "new-boot"
    elif change == "target_loss":
        state[cp._SOURCE_RANKED_XP_LOSS_POLICIES_KEY] = [{
            "boot_id": "boot", "level": 29, "policy_id": policy, "xp_delta": -10,
        }]
    else:
        candidate = replace(candidate, requires_flight=True)
    segments[0]["end_state_json"] = json.dumps(old_end)
    segments[1]["end_state_json"] = json.dumps(observation)
    assert arm((candidate, policy, state, world, segments)) is None


def test_clear_route_requires_independent_combat_admission(clear_city_case, monkeypatch):
    monkeypatch.setattr(cp, "_source_ranked_hp_probe_admission_available", lambda *a, **kw: False)
    assert arm(clear_city_case) is None


def test_clear_route_can_find_one_indexed_old_segment_without_broad_history(clear_city_case):
    candidate, policy, state, world, segments = clear_city_case
    reads = []

    def get_identity(campaign_id, phase):
        reads.append((campaign_id, phase))
        return 42

    storage = SimpleNamespace(
        get_latest_campaign_segment_for_phase=lambda *a, **kw: None,
        get_indexed_campaign_phase_segment_id=get_identity,
        get_campaign_segment_by_id=lambda campaign_id, segment_id: segments[0],
    )
    assert arm(
        (candidate, policy, state, world, segments[1:]), storage=storage, campaign_id=7,
    ) == policy
    assert reads == [(7, policy)]


def completed_recheck(case):
    candidate, policy, state, _world, _segments = case
    assert arm(case) == policy
    assert cp._mark_field_city_alternate_route_revalidation(state, candidate, character_level=29)
    start = deepcopy(state)
    start[cp._SOURCE_RANKED_CANDIDATE_KEY] = cp._source_ranked_candidate_record(
        candidate, character_level=29, source_revision="current-revision",
    )
    end = deepcopy(start)
    end["xp"] += 250
    end["campaign_field_city_preflight"].update(run_id=102, outbound_index=2)
    end["campaign_objective_kills"] = [{
        "source_policy_id": policy, "source_mobile_vnum": candidate.mobile_vnum,
        "xp_gained": 250,
    }]
    segment = {
        "id": 44, "run_id": 102, "phase": policy, "status": "success",
        "start_state_json": json.dumps(start), "end_state_json": json.dumps(end),
    }
    return end, segment


def test_only_verified_success_supersedes_the_exact_old_route_block(clear_city_case):
    _candidate, policy, _state, _world, _segments = clear_city_case
    end, segment = completed_recheck(clear_city_case)
    old_ledger = deepcopy(end[cp._FIELD_CITY_BLOCKED_POLICIES_KEY])
    promoted = cp._verify_field_city_clear_route_revalidation(end, [segment])
    assert promoted[cp._FIELD_CITY_CLEAR_ROUTE_REVALIDATION_KEY]["status"] == "succeeded"
    assert promoted[cp._FIELD_CITY_CLEAR_ROUTE_REVALIDATION_KEY]["verified_net_xp"] == 250
    assert policy not in cp._field_city_departure_blocked_policy_ids(promoted)
    assert promoted[cp._FIELD_CITY_BLOCKED_POLICIES_KEY] == old_ledger

    fresh_block = deepcopy(promoted)
    fresh_block["campaign_field_city_preflight"].update(
        blocked=True, stopped_before_departure=True, outbound_index=0, policy_id=policy,
    )
    assert policy in cp._field_city_departure_blocked_policy_ids(fresh_block)


@pytest.mark.parametrize("change", [
    "no_kill", "loss", "failed", "wrong_run", "wrong_mobile", "blocked",
    "not_home", "changed_level", "changed_source", "unfinished_route",
])
def test_clear_route_success_needs_the_whole_hunt_and_return(clear_city_case, change):
    end, segment = completed_recheck(clear_city_case)
    if change == "no_kill":
        end["campaign_objective_kills"] = []
    elif change == "loss":
        end["xp_loss_total"] = 1
    elif change == "failed":
        segment["status"] = "failed"
    elif change == "wrong_run":
        end["campaign_field_city_preflight"]["run_id"] = 99
    elif change == "wrong_mobile":
        end["campaign_objective_kills"][0]["source_mobile_vnum"] = 999
    elif change == "blocked":
        end["campaign_field_city_preflight"]["blocked"] = True
    elif change == "not_home":
        end["room_vnum"] = "3001"
    elif change == "changed_level":
        end["level"] = 30
    elif change == "changed_source":
        end[cp._SOURCE_REVISION_KEY] = "different"
    else:
        end["campaign_field_city_preflight"]["outbound_index"] = 1
    segment["end_state_json"] = json.dumps(end)
    checked = cp._verify_field_city_clear_route_revalidation(end, [segment])
    assert checked[cp._FIELD_CITY_CLEAR_ROUTE_REVALIDATION_KEY]["status"] == "attempted"


def productive_absence_case(case):
    candidate, policy, _state, world, _segments = case
    productive_end, productive_segment = completed_recheck(case)
    # The preceding helper's reward must exceed the meaningful-kill floor.
    productive_end["xp"] = 2409
    productive_end["campaign_objective_kills"][0]["xp_gained"] = 1409
    productive_segment["end_state_json"] = json.dumps(productive_end)
    start = deepcopy(productive_end)
    end = deepcopy(start)
    end["campaign_objective_kills"] = []
    end["campaign_completed_kills"] = []
    end["campaign_fastwalk_target_absent"] = True
    end["campaign_fastwalk_source_absent_sightings"] = [{
        "policy_id": policy, "room_vnum": str(candidate.room_vnum),
    }]
    absence = {
        "id": 45, "run_id": 103, "phase": policy, "status": "success",
        "start_state_json": json.dumps(start), "end_state_json": json.dumps(end),
    }
    end["campaign_last_policy"] = policy
    end[cp._RESEARCH_ABSENCE_COOLDOWN_KEY] = {policy: 3}
    end["campaign_research_results"] = {
        policy: {"absent": True, "observed": False, "viable": False, "boot_id": "boot"},
    }
    # Productive route proof supersedes only the historical city closure.
    end[cp._FIELD_CITY_CLEAR_ROUTE_REVALIDATION_KEY].update(
        status="succeeded", verified_run_id=102,
    )
    return policy, end, world, [productive_segment, absence]


def test_fresh_productive_absence_can_enter_first_wait_without_changing_state(clear_city_case):
    policy, state, world, segments = productive_absence_case(clear_city_case)
    before = deepcopy(state)
    assert cp._productive_source_hunt_absence_wait_policy(
        state, segments, source_world=world,
    ) == policy
    assert state == before


@pytest.mark.parametrize("change", [
    "no_productive_run", "changed_source", "loss", "missing_absence",
    "wrong_kill", "city_block", "route_hazard", "not_home", "aged", "protection",
    "changed_route",
])
def test_first_productive_absence_wait_preserves_independent_gates(
    clear_city_case, monkeypatch, change,
):
    policy, state, world, segments = productive_absence_case(clear_city_case)
    old_end = json.loads(segments[0]["end_state_json"])
    absence_end = json.loads(segments[1]["end_state_json"])
    if change == "no_productive_run":
        segments = segments[1:]
    elif change == "changed_source":
        old_end[cp._SOURCE_REVISION_KEY] = "other"
    elif change == "loss":
        old_end["xp_loss_total"] = 1
    elif change == "missing_absence":
        absence_end["campaign_fastwalk_source_absent_sightings"] = []
    elif change == "wrong_kill":
        old_end["campaign_objective_kills"][0]["source_mobile_vnum"] = 999
    elif change == "city_block":
        state["campaign_field_city_preflight"]["blocked"] = True
    elif change == "route_hazard":
        state["campaign_research_results"][policy]["route_hazard"] = "unsafe"
    elif change == "not_home":
        state["room_vnum"] = "3001"
    elif change == "aged":
        state[cp._RESEARCH_ABSENCE_COOLDOWN_KEY][policy] = 2
    elif change == "changed_route":
        old_start = json.loads(segments[0]["start_state_json"])
        old_start[cp._SOURCE_RANKED_CANDIDATE_KEY]["route"] = ["north"]
        segments[0]["start_state_json"] = json.dumps(old_start)
    else:
        monkeypatch.setattr(cp, "_source_ranked_candidate_requires_sanctuary_for_state", lambda *a, **kw: True)
    if change != "no_productive_run":
        segments[0]["end_state_json"] = json.dumps(old_end)
        segments[1]["end_state_json"] = json.dumps(absence_end)
    assert cp._productive_source_hunt_absence_wait_policy(
        state, segments, source_world=world,
    ) is None
