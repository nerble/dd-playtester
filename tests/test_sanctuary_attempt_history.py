from copy import deepcopy
from types import SimpleNamespace

import pytest

import dd4tester.campaign as campaign


POLICY = "source-ranked-hunt-moria-4055-4064-46-sanctuary-maintenance"


def quota_state():
    return {"level": 46, "world_boot_id": "boot",
            campaign._SANCTUARY_RESOURCE_ATTEMPTS_KEY: {POLICY: {"boot_id": "boot", "level": 46, "count": 200}},
            "campaign_research_results": {POLICY: {
                "boot_id": "boot", "level": 46, "observed": True, "viable": False,
                "fatal_failure": True, "route_hazard": campaign._SANCTUARY_RESOURCE_EXHAUSTED_HAZARD}}}


def test_count_only_resource_failure_is_archived_not_retry_permission():
    state = quota_state()
    original = deepcopy(state)
    repaired = campaign._retire_sanctuary_attempt_quota_results(state)
    assert state == original
    assert repaired[campaign._SANCTUARY_RESOURCE_ATTEMPTS_KEY] == original[campaign._SANCTUARY_RESOURCE_ATTEMPTS_KEY]
    result = repaired["campaign_research_results"][POLICY]
    assert "fatal_failure" not in result
    assert "route_hazard" not in result
    assert result["retired_attempt_quota"]["fatal_failure"] is True
    target = SimpleNamespace(area_file="moria.are", mobile_vnum=4055, room_vnum=4064, route_origin_recall_index=1)
    assert campaign._source_ranked_sanctuary_candidate_research_open(repaired, target, policy_id=POLICY)


@pytest.mark.parametrize("terminal", ["absent", "crowded", "xp_loss_observed", "target_vnum_mismatch"])
def test_retiring_quota_does_not_clear_terminal_evidence(terminal):
    state = quota_state()
    state["campaign_research_results"][POLICY][terminal] = True
    repaired = campaign._retire_sanctuary_attempt_quota_results(state)
    assert repaired["campaign_research_results"][POLICY][terminal] is True
    target = SimpleNamespace(area_file="moria.are", mobile_vnum=4055, room_vnum=4064, route_origin_recall_index=1)
    assert not campaign._source_ranked_sanctuary_candidate_research_open(repaired, target, policy_id=POLICY)


def test_actual_route_failure_is_not_a_count_only_failure():
    state = quota_state()
    result = state["campaign_research_results"][POLICY]
    result["route_hazard"] = "strict route crosses source combat hazard: the snake in room 4058"
    assert campaign._retire_sanctuary_attempt_quota_results(state) == state


def test_attempt_count_alone_never_exhausts_sanctuary_recovery():
    state = quota_state()
    state.pop("campaign_research_results")
    assert not campaign._sanctuary_recovery_attempts_exhausted(state, policy_id=POLICY)
    generic = campaign._SOURCE_RANKED_SANCTUARY_RECOVERY_POLICY.policy_id
    state[campaign._SANCTUARY_RESOURCE_ATTEMPTS_KEY][generic] = {"count": 200, "boot_id": "boot", "level": 46}
    assert not campaign._sanctuary_recovery_attempts_exhausted(state, policy_id=generic)
    state["campaign_research_results"] = {generic: {
        "fatal_failure": True, "boot_id": "boot", "level": 46,
        "route_hazard": "verified source hazard"}}
    assert campaign._sanctuary_recovery_attempts_exhausted(state, policy_id=generic)
