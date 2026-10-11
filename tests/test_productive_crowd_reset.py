from copy import deepcopy
import json

import pytest

from dd4tester.campaign_migrations import restore_productive_population_after_crowd_reset
from dd4tester.hunt_candidates import ACT_STAY_AREA, MobileSource, MobReset, RoomSource, WorldSource
from dd4tester.hunt_outcomes import productive_crowd_reset_result


POLICY = "source-ranked-hunt-test-100-201-30"


def crowd_reset_case():
    state = {
        "level": 30, "world_boot_id": "boot", "campaign_source_revision": "revision",
        "campaign_xp_loss_total": 50, "xp": 101000, "room_vnum": "3054",
        "hp": 700, "max_hp": 700, "dead": False, "in_combat": False, "enemies": [],
        "campaign_last_policy": POLICY, "campaign_cleared_research_policies": [POLICY],
        "campaign_source_ranked_capacity_reset_wait": {
            "boot_id": "boot", "consumed": False, "reason": "automatic area reset wait completed",
        },
        "campaign_below_band_policy_exclusions": {POLICY: {"targets": ["clan member"]}},
    }
    start = {**deepcopy(state), "xp": 100000, "campaign_source_ranked_hunt_candidate": {
        "policy_id": POLICY, "mobile_vnum": 100, "source_revision": "revision",
    }}
    result = {
        "boot_id": "boot", "observed": True, "viable": True, "completed_kill": True,
        "consider_viable": True, "max_objective_kill_xp": 1000, "objective_xp": 1000,
    }
    end = {**deepcopy(state), "campaign_fastwalk_abort_reason": "field room contained 1 observed mobiles",
           "campaign_research_results": {POLICY: result}, "campaign_objective_kills": [{
               "source_policy_id": POLICY, "source_mobile_vnum": 100, "xp_gained": 1000,
           }]}
    segment = {
        "phase": POLICY, "run_id": 1, "status": "success", "execution_status": "success",
        "safety_outcome": "safe", "objective_outcome": "not_achieved", "command_count": 20,
        "finished_at": "finished", "error": None,
        "start_state_json": json.dumps(start), "end_state_json": json.dumps(end),
    }
    timer = {**segment, "phase": "world-time-probe", "run_id": 2,
             "start_state_json": json.dumps(state), "end_state_json": json.dumps(state)}
    world = WorldSource(
        rooms={room: RoomSource(room, "hall", "test.are") for room in (201, 202)},
        mobiles={100: MobileSource(100, "clan member", "a clan member", 27, ACT_STAY_AREA, 0, "test.are")},
        mob_resets=[MobReset(100, room, 2) for room in (201, 202)],
    )
    return state, [segment, timer], world, {POLICY: 1000}


def test_saved_crowd_wait_restores_exact_productive_result_without_changing_old_evidence():
    state, segments, world, ledger = crowd_reset_case()
    original_state, original_segments = deepcopy(state), deepcopy(segments)
    repaired = restore_productive_population_after_crowd_reset(
        state, segments, source_world=world, latest_policy_xp=ledger, loss_policy_ids=(),
    )
    result = repaired["campaign_research_results"][POLICY]
    assert result["completed_kill"] and not result["crowded"]
    assert result["crowd_reset_restored_from_run_id"] == 1
    assert result["crowd_reset_world_time_run_id"] == 2
    assert repaired["campaign_below_band_policy_exclusions"] == state["campaign_below_band_policy_exclusions"]
    assert state == original_state and segments == original_segments
    assert restore_productive_population_after_crowd_reset(
        repaired, segments, source_world=world, latest_policy_xp=ledger, loss_policy_ids=(),
    ) is repaired


@pytest.mark.parametrize("change", [
    "no_wait", "spent_wait", "wrong_wait", "no_clear", "existing_result", "no_timer",
    "wrong_boot", "wrong_revision", "changed_xp", "loss", "known_loss", "unsafe",
    "unlinked", "no_commands", "unknown_status", "unknown_safety", "non_crowd",
    "no_kills", "wrong_mobile", "below_band", "incidental_ledger", "unknown_ledger",
    "timer_loss", "unsafe_timer", "source_special", "single_population",
])
def test_crowd_reset_restore_keeps_uncertain_failed_or_changed_visits_closed(change):
    state, segments, world, ledger = crowd_reset_case()
    start = json.loads(segments[0]["start_state_json"])
    end = json.loads(segments[0]["end_state_json"])
    losses = ()
    if change == "no_wait":
        state.pop("campaign_source_ranked_capacity_reset_wait")
    elif change == "spent_wait":
        state["campaign_source_ranked_capacity_reset_wait"]["consumed"] = True
    elif change == "wrong_wait":
        state["campaign_source_ranked_capacity_reset_wait"]["reason"] = "unobserved"
    elif change == "no_clear":
        state["campaign_cleared_research_policies"] = []
    elif change == "existing_result":
        state["campaign_research_results"] = {POLICY: {"viable": False}}
    elif change == "no_timer":
        segments.pop()
    elif change == "wrong_boot":
        end["world_boot_id"] = "other boot"
    elif change == "wrong_revision":
        end["campaign_source_revision"] = "other revision"
    elif change == "changed_xp":
        state["xp"] += 1
    elif change == "loss":
        end["campaign_xp_loss_total"] += 1
    elif change == "known_loss":
        losses = (POLICY,)
    elif change == "unsafe":
        state["dead"] = True
    elif change == "unlinked":
        segments[0]["run_id"] = None
    elif change == "no_commands":
        segments[0]["command_count"] = 0
    elif change == "unknown_status":
        segments[0]["execution_status"] = None
    elif change == "unknown_safety":
        segments[0]["safety_outcome"] = None
    elif change == "non_crowd":
        end["campaign_fastwalk_abort_reason"] = "output budget exhausted"
    elif change == "no_kills":
        end["campaign_objective_kills"] = []
    elif change == "wrong_mobile":
        end["campaign_objective_kills"][0]["source_mobile_vnum"] = 101
    elif change == "below_band":
        end["campaign_objective_kills"][0]["xp_gained"] = state["level"] * 10
    elif change == "incidental_ledger":
        ledger[POLICY] = 10
    elif change == "unknown_ledger":
        ledger.clear()
    elif change in {"timer_loss", "unsafe_timer"}:
        timer_end = json.loads(segments[1]["end_state_json"])
        timer_end["campaign_xp_loss_total" if change == "timer_loss" else "dead"] = 51 if change == "timer_loss" else True
        segments[1]["end_state_json"] = json.dumps(timer_end)
    elif change == "source_special":
        world.mobile_specials[100] = ("spec_poison",)
    elif change == "single_population":
        world.mob_resets = world.mob_resets[:1]
    segments[0]["start_state_json"] = json.dumps(start)
    segments[0]["end_state_json"] = json.dumps(end)
    assert restore_productive_population_after_crowd_reset(
        state, segments, source_world=world, latest_policy_xp=ledger, loss_policy_ids=losses,
    ) is state


def test_crowd_reset_retains_useful_kill_without_claiming_a_new_objective():
    state, segments, _world, _ledger = crowd_reset_case()
    result = json.loads(segments[0]["end_state_json"])["campaign_research_results"][POLICY]
    result["crowded"] = True
    retained = productive_crowd_reset_result(result, level=30, boot_id=state["world_boot_id"])
    assert retained["completed_kill"] and retained["max_objective_kill_xp"] == 1000
    assert not retained["crowded"] and result["crowded"]
    assert "objective_outcome" not in retained
    for key in ("crowd_exhausted", "fatal_failure", "retryable_failure", "route_hazard", "absent"):
        assert productive_crowd_reset_result({**result, key: True}, level=30, boot_id="boot") is None
