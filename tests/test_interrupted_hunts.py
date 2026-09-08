import json
from dataclasses import replace

import pytest

import dd4tester.campaign as campaign
from dd4tester.hunt_candidates import HuntCandidate
from dd4tester.state import CharacterState


def candidate():
    return HuntCandidate(
        status="reject", score=100, area_file="moria.are", mobile_vnum=4002,
        target="the centipede", target_keyword="centipede", level=5,
        room_vnum=4023, room_name="Tunnel", route=("south",),
        source_spawn_limit=4, room_spawn_count=1, boot_kills=0,
        loot=(), source_value=0, contained_coins=0, hazards=(),
        estimated_level_range=(3, 7), estimated_base_hp_range=(26, 105),
        estimated_peak_round_damage=55,
        autonomy_rejections=("target reset capacity exceeds one",),
    )


def evidence(*, interrupted=None, recovered=None, end=None, start=None, error=None):
    initial = CharacterState(
        level=8, xp=27000, hp=113, max_hp=113, move=220, max_move=220,
        room_vnum="3054", position=7,
    ).to_dict()
    initial.update(world_boot_id="boot", campaign_xp_loss_total=600)
    initial.update(start or {})
    last_live = {**initial, "room_vnum": "4023", "hp": 101, **(interrupted or {})}
    home_live = {**initial, "xp": 27162, **(recovered or {})}
    home_end = {**home_live, **(end or {})}
    policy_id = campaign._source_ranked_policy_id(candidate(), character_level=8)
    state = {**home_end, campaign._SOURCE_RANKED_TIMEOUT_POLICIES_KEY: [{
        "boot_id": "boot", "level": 8, "policy_id": policy_id,
        "reason": "previous campaign worker was interrupted before the next invocation",
        "objective_kill_count": 0,
    }]}
    state.update(campaign_research_results={policy_id: {
        "boot_id": "boot", "completed_kill": False, "consider_viable": True,
        "observed": True, "retryable_failure": True, "viable": False,
    }}, campaign_research_absence_cooldowns={policy_id: 2})
    segments = [{
        "id": 10, "phase": policy_id, "status": "ready", "run_id": 100,
        "error": error or "previous campaign worker was interrupted before the next invocation",
        "start_state_json": json.dumps(initial), "end_state_json": json.dumps(last_live),
    }, {
        "id": 20, "phase": "return-home", "status": "success", "run_id": 101,
        "error": None, "start_state_json": json.dumps(last_live),
        "end_state_json": json.dumps(home_end),
    }]

    class Storage:
        def get_latest_state_snapshot(self, run_id):
            return {"state_json": json.dumps({100: last_live, 101: home_live}[run_id])}

    return state, segments, Storage(), policy_id


def repair(**kwargs):
    state, segments, storage, _ = evidence(**kwargs)
    return campaign._repair_recovered_source_interruption(state, segments, storage=storage)


def proof(state):
    return state[campaign._SOURCE_RANKED_TIMEOUT_POLICIES_KEY][0].get("recovered_interruption")


def test_recovered_interruption_preserves_failure_and_admits_one_capacity_retry():
    state, segments, storage, policy_id = evidence()
    updated = campaign._repair_recovered_source_interruption(state, segments, storage=storage)
    assert proof(updated)["interrupted_run_id"] == 100
    assert proof(updated)["recovery_run_id"] == 101
    assert not proof(state)
    assert updated[campaign._SOURCE_RANKED_TIMEOUT_POLICIES_KEY][0]["reason"] == segments[0]["error"]
    selected = campaign._source_ranked_timeout_revalidation_candidate(
        [candidate()], updated, character_level=8, character_max_hp=113,
    )
    assert selected == candidate()
    updated[campaign._SOURCE_RANKED_REVALIDATION_POLICY_KEY] = policy_id
    assert campaign._select_source_ranked_hunt_candidate(
        [candidate()], updated, character_level=8, character_max_hp=113,
    ) == candidate()
    campaign._mark_source_ranked_timeout_revalidation(updated, policy_id=policy_id)
    assert campaign._source_ranked_recovered_interruption_candidate(
        candidate(), updated, character_level=8,
    )  # The already-dispatched segment can build its stop.
    updated.pop(campaign._SOURCE_RANKED_REVALIDATION_POLICY_KEY)
    updated = campaign._rearm_source_ranked_timeout_revalidation_after_reset(updated)
    assert campaign._source_ranked_timeout_revalidation_candidate(
        [candidate()], updated, character_level=8, character_max_hp=113,
    ) is None
    assert campaign._select_source_ranked_hunt_candidate(
        [candidate()], updated, character_level=8, character_max_hp=113,
    ) is None


@pytest.mark.parametrize("changes", [
    {"interrupted": {"hp": 20}}, {"interrupted": {"hp": None}},
    {"interrupted": {"max_hp": None}}, {"interrupted": {"xp": None}},
    {"interrupted": {"level": 9}},
    {"interrupted": {"xp": 26999}}, {"interrupted": {"xp_loss_observed": True}},
    {"interrupted": {"dead": True}}, {"start": {"xp": None}},
    {"start": {"campaign_xp_loss_total": None}},
    {"recovered": {"room_vnum": "3019"}}, {"recovered": {"hp": 0}},
    {"recovered": {"hp": float("inf")}},
    {"recovered": {"enemies": [[{"name": "orc", "level": 5}]]}},
    {"recovered": {"in_combat": True}}, {"recovered": {"position": 6}},
    {"recovered": {"xp": None}}, {"recovered": {"xp": 26999}},
    {"recovered": {"world_boot_id": "new-boot"}}, {"recovered": {"level": 9}},
    {"end": {"campaign_xp_loss_total": 601}},
    {"end": {"campaign_died_during_segment": True}},
    {"end": {"campaign_fastwalk_abort_reason": "unresolved recovery"}},
    {"error": "segment runtime boundary requested a safe healer return"},
])
def test_missing_or_negative_evidence_cannot_authorize_replay(changes):
    assert proof(repair(**changes)) is None


@pytest.mark.parametrize("changes", [
    {"equipped_weapons": ("sword",)}, {"specials": ("spec_poison",)},
    {"estimated_base_hp_range": (26, 200)}, {"source_spawn_limit": 10},
    {"estimated_base_hp_range": (0, 0)}, {"estimated_peak_round_damage": 200},
    {"autonomy_rejections": ("target room has a dangerous reset companion",)},
])
def test_recovery_does_not_widen_source_safety(changes):
    assert campaign._source_ranked_timeout_revalidation_candidate(
        [replace(candidate(), **changes)], repair(), character_level=8, character_max_hp=113,
    ) is None


def test_later_combat_failure_does_not_reuse_older_recovery_proof():
    state, segments, storage, policy_id = evidence()
    state = campaign._repair_recovered_source_interruption(state, segments, storage=storage)
    segments.append({**segments[0], "id": 30, "error": "combat capacity exhausted"})
    assert not proof(campaign._repair_recovered_source_interruption(state, segments, storage=storage))


def test_recovery_must_follow_interruption_and_succeed():
    for changes in ({"id": 5}, {"status": "failed"}, {"run_id": None}):
        state, segments, storage, _ = evidence()
        segments[1].update(changes)
        assert not proof(campaign._repair_recovered_source_interruption(state, segments, storage=storage))


@pytest.mark.parametrize("extra", [
    {"absent": True}, {"crowded": True}, {"crowd_exhausted": True},
    {"consider_viable": False}, {"unattackable": True},
    {"route_hazard": "unsafe corridor"}, {"target_vnum_mismatch": True},
])
def test_retry_keeps_actual_negative_research_evidence(extra):
    state = repair()
    policy_id = campaign._source_ranked_policy_id(candidate(), character_level=8)
    state["campaign_research_results"][policy_id].update(extra)
    assert campaign._source_ranked_timeout_revalidation_candidate(
        [candidate()], state, character_level=8, character_max_hp=113,
    ) is None
