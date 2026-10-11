import json
from copy import deepcopy

import pytest

from dd4tester.campaign import (
    _funding_candidate_is_below_band, _source_ranked_candidate_excluded_by_below_band_evidence,
    _source_ranked_result_status,
)
from dd4tester.hunt_candidates import ACT_STAY_AREA, HuntCandidate, MobileSource, MobReset, RoomSource, WorldSource
from dd4tester.populations import (
    POPULATION_SEARCH_REVALIDATIONS_KEY, incomplete_population_search_evidence,
    population_search_revalidation_pending,
)


def incomplete_search_case():
    policy_id = "source-ranked-hunt-test-100-201-30"
    candidate = HuntCandidate(
        status="reject", score=1, area_file="test.are", mobile_vnum=100,
        target="clan member", target_keyword="clan", level=27, room_vnum=201,
        room_name="hall", route=("south",), source_spawn_limit=3, room_spawn_count=1,
        boot_kills=2, loot=(), source_value=0, contained_coins=0, hazards=(),
        autonomy_rejections=("target reset capacity exceeds one",), stay_area=True,
    )
    world = WorldSource(
        rooms={room: RoomSource(room, "hall", "test.are") for room in (201, 202, 203)},
        mobiles={100: MobileSource(100, "clan member", "a clan member", 27, ACT_STAY_AREA, 0, "test.are")},
        mob_resets=[MobReset(100, room, 3, ()) for room in (201, 202, 203)],
    )
    state = {
        "level": 30, "world_boot_id": "boot", "campaign_source_revision": "revision",
        "xp": 5000, "campaign_xp_loss_total": 500, "room_vnum": "3054",
        "hp": 710, "max_hp": 700, "dead": False, "in_combat": False,
    }
    start = {
        **state, "campaign_source_ranked_hunt_candidate": {
            "policy_id": policy_id, "mobile_vnum": 100, "room_vnum": 201,
            "source_revision": "revision", "route": ["south"],
        },
    }
    end = {
        **state, "campaign_fastwalk_where_relocation_attempts": 7,
        "campaign_fastwalk_source_below_band_sightings": [
            {"policy_id": policy_id, "room_vnum": "202", "target": "clan member"},
        ],
        "campaign_fastwalk_where_decisions": [{
            "source_mobile_vnum": 100, "room_vnum": "201", "locations": ["hall"],
            "mapped_rooms": {"hall": ["201", "202", "203"]},
            "planned_endpoints": ["202", "203"],
        }],
    }
    segment = {
        "id": 1, "run_id": 2, "phase": policy_id, "status": "success",
        "command_count": 100, "finished_at": "finished", "error": None,
        "start_state_json": json.dumps(start), "end_state_json": json.dumps(end),
    }
    summary = {
        "run": {"id": 2},
        "outcomes": {"execution": "success", "objective": "not_achieved", "safety": "safe"},
        "progress": {"combat_starts": 0, "confirmed_kills": 0},
    }
    return state, segment, summary, candidate, world, policy_id


def receipt_for(case):
    state, segment, summary, candidate, world, policy_id = case
    return incomplete_population_search_evidence(
        state, segment, summary, candidate, world, policy_id=policy_id,
        location_routes={"hall": ("201", "202", "203")}, maximum_relocations=8,
    )


def test_incomplete_population_search_preserves_old_evidence_and_only_unchecked_rooms():
    case = incomplete_search_case()
    original = deepcopy(case[:3])
    receipt = receipt_for(case)
    assert receipt["remaining_rooms"] == ["203"]
    assert receipt["checked_rooms"] == ["201", "202"]
    assert receipt["prior_relocations"] == 7 and receipt["maximum_relocations"] == 8
    assert case[:3] == original


@pytest.mark.parametrize("change", [
    "combat", "loss", "xp", "boot", "source", "run", "unsafe", "crowd", "abort",
    "wrong_mobile", "wrong_policy", "route", "exhausted", "all_checked", "not_reported",
    "not_planned", "consumed", "no_combat_evidence", "bad_map", "bad_plan", "wrong_target",
])
def test_incomplete_population_search_rejects_other_failures_and_spent_searches(change):
    case = incomplete_search_case()
    state, segment, summary, candidate, world, policy_id = case
    end = json.loads(segment["end_state_json"])
    if change == "combat":
        summary["progress"]["combat_starts"] = 1
    elif change == "loss":
        end["campaign_xp_loss_total"] += 1
    elif change == "xp":
        state["xp"] += 1
    elif change == "boot":
        state["world_boot_id"] = "other"
    elif change == "source":
        state["campaign_source_revision"] = "other"
    elif change == "run":
        summary["run"]["id"] = 3
    elif change == "unsafe":
        summary["outcomes"]["safety"] = "loss"
    elif change == "crowd":
        end["campaign_fastwalk_crowded"] = True
    elif change == "abort":
        end["campaign_fastwalk_abort_reason"] = "unsafe route"
    elif change == "wrong_mobile":
        end["campaign_fastwalk_where_decisions"][0]["source_mobile_vnum"] = 101
    elif change == "wrong_policy":
        end["campaign_fastwalk_source_below_band_sightings"][0]["policy_id"] = "other"
    elif change == "route":
        start = json.loads(segment["start_state_json"])
        start["campaign_source_ranked_hunt_candidate"]["route"] = ["east"]
        segment["start_state_json"] = json.dumps(start)
    elif change == "exhausted":
        end["campaign_fastwalk_where_relocation_attempts"] = 8
    elif change == "all_checked":
        end["campaign_fastwalk_where_decisions"].append({"source_mobile_vnum": 100, "room_vnum": "203"})
    elif change == "not_reported":
        end["campaign_fastwalk_where_decisions"][0]["mapped_rooms"]["hall"] = ["201", "202"]
    elif change == "not_planned":
        end["campaign_fastwalk_where_decisions"][0]["planned_endpoints"] = ["202"]
    elif change == "consumed":
        state[POPULATION_SEARCH_REVALIDATIONS_KEY] = {policy_id: {"status": "attempted"}}
    elif change == "no_combat_evidence":
        summary["progress"].pop("combat_starts")
    elif change == "bad_map":
        end["campaign_fastwalk_where_decisions"][0]["mapped_rooms"]["hall"] = None
    elif change == "bad_plan":
        end["campaign_fastwalk_where_decisions"][0]["planned_endpoints"] = None
    elif change == "wrong_target":
        end["campaign_fastwalk_source_below_band_sightings"][0]["target"] = "other mobile"
    segment["end_state_json"] = json.dumps(end)
    assert receipt_for(case) is None


def test_pending_search_is_retryable_not_productive_and_does_not_clear_negative_ledger():
    case = incomplete_search_case()
    state, _segment, _summary, candidate, _world, policy_id = case
    state[POPULATION_SEARCH_REVALIDATIONS_KEY] = {policy_id: receipt_for(case)}
    state["campaign_below_band_policy_exclusions"] = {
        policy_id: {"level": 30, "boot_id": "boot", "source_mobile_keys": ["mobile:100"], "targets": ["clan member"]},
    }
    state["campaign_research_results"] = {
        policy_id: {"boot_id": "boot", "observed": True, "viable": False,
                    "consider_viable": False, "completed_kill": False},
    }
    original = deepcopy(state["campaign_below_band_policy_exclusions"])
    assert population_search_revalidation_pending(state, candidate, policy_id)
    assert _source_ranked_result_status(candidate, state, character_level=30) == "retryable"
    assert not _source_ranked_candidate_excluded_by_below_band_evidence(candidate, state, character_level=30)
    assert not _funding_candidate_is_below_band(state, candidate, character_level=30, boot_id="boot")
    assert state["campaign_below_band_policy_exclusions"] == original
    state[POPULATION_SEARCH_REVALIDATIONS_KEY][policy_id]["status"] = "attempted"
    assert not population_search_revalidation_pending(state, candidate, policy_id)
    assert _source_ranked_result_status(candidate, state, character_level=30) == "cooldown"
    assert _source_ranked_candidate_excluded_by_below_band_evidence(candidate, state, character_level=30)
