from copy import deepcopy
import json

import pytest

from dd4tester.city_travel import FIELD_CITY_OBSERVATION_KEY, field_city_observation_request
from dd4tester.character import CharacterSpec
from dd4tester.state import CharacterState
from dd4tester.starter import StarterPolicy


def observation_case():
    state = {
        "level": 30, "world_boot_id": "boot", "campaign_source_revision": "source",
        "xp": 1000, "campaign_xp_loss_total": 50, "room_vnum": "3054",
        "hp": 700, "max_hp": 700, "dead": False, "in_combat": False,
        "campaign_field_city_preflight": {
            "run_id": 10, "policy_id": "source-ranked-hunt-test-100-201-30",
            "complete": True, "blocked": True, "boot_id": "boot", "level": 30,
            "stopped_before_departure": True, "outbound_index": 0, "wait_attempts": 3,
            "route_rooms": ["temple square"], "locations": ["temple square"],
        },
    }
    segment = {
        "run_id": 10, "phase": state["campaign_field_city_preflight"]["policy_id"],
        "status": "success", "execution_status": "success", "safety_outcome": "safe",
        "command_count": 20, "finished_at": "finished",
        "start_state_json": json.dumps(state), "end_state_json": json.dumps(state),
    }
    return state, segment


def test_city_observation_is_finite_read_only_admission_without_clearing_failures():
    state, segment = observation_case()
    original = deepcopy(state)
    request = field_city_observation_request(state, [segment])
    assert request["prior_run_id"] == 10 and request["route_rooms"] == ["temple square"]
    assert state == original
    state[FIELD_CITY_OBSERVATION_KEY] = request
    assert field_city_observation_request(state, [segment]) is None


@pytest.mark.parametrize("change", [
    "unlinked", "failed", "unsafe", "running", "no_commands", "travel", "loss",
    "xp_change", "revision_change", "low_hp", "dead", "combat", "missing_waits", "unknown_loss",
])
def test_city_observation_rejects_unproved_or_changed_boundary(change):
    state, segment = observation_case()
    if change == "unlinked":
        segment["run_id"] = None
    elif change == "failed":
        segment["execution_status"] = "failed"
    elif change == "unsafe":
        segment["safety_outcome"] = "loss"
    elif change == "running":
        segment["finished_at"] = None
    elif change == "no_commands":
        segment["command_count"] = 0
    elif change == "travel":
        state["room_vnum"] = "3001"
    elif change == "loss":
        state["campaign_xp_loss_total"] = 51
    elif change == "xp_change":
        state["xp"] = 1001
    elif change == "revision_change":
        state["campaign_source_revision"] = "changed"
    elif change == "low_hp":
        state["hp"] = 500
    elif change == "dead":
        state["dead"] = True
    elif change == "combat":
        state["in_combat"] = True
    elif change == "missing_waits":
        state["campaign_field_city_preflight"]["wait_attempts"] = 2
    else:
        start = json.loads(segment["start_state_json"])
        start.pop("campaign_xp_loss_total")
        segment["start_state_json"] = json.dumps(start)
    assert field_city_observation_request(state, [segment]) is None


def test_city_observation_queries_then_waits_without_departing_and_caps_rechecks():
    spec = CharacterSpec.from_mapping({"name": "Observer", "race": "dwarf", "gender": "male", "class": "warrior"})
    policy = StarterPolicy(spec, "test-password", return_home=True, world_time_probe=True,
                           recheck_field_city_route_rooms=("temple square",))
    policy.world_time_queried = True
    state = CharacterState(level=30, hp=700, max_hp=700, room_vnum="3054", position=7)
    assert policy._world_time_probe_completion_decision(state).command == "where drunk"
    policy.magic_shop_drunk_preflight_pending = False
    policy.magic_shop_drunk_preflight_complete = True
    policy.magic_shop_route_blocked_by_drunk = True
    assert policy._world_time_probe_completion_decision(state).command == "sleep"
    policy.city_shop_route_wait_due = None
    policy.city_shop_route_wait_attempts = 3
    assert policy._world_time_probe_completion_decision(state).command == "save"


def test_clear_city_observation_is_not_an_area_reset_or_progression_success():
    from dd4tester.campaign import CampaignResult, _world_time_probe_message
    message = _world_time_probe_message(
        "boot", "boot", reset_wait_completed=False, defer_policy_selection=True,
        field_city_observation={"status": "completed", "run_id": 11},
        field_city_preflight={"complete": True, "blocked": False, "run_id": 11},
    )
    result = CampaignResult(7, "ready", 1, message, {"level": 30})
    assert result.ready_for_next_segment and not result.awaiting_area_reset
    assert result.status != "success"
