from copy import deepcopy
import json
from types import SimpleNamespace

from dd4tester.campaign import (
    _record_source_ranked_protection_recovery_retry,
    _repair_unstarted_protection_retry_selection,
    _source_ranked_unprotected_reserve_retry_allowed,
    _source_ranked_spent_protection_retry_should_rotate,
)


POLICY = "source-ranked-hunt-smuggler-17505-17541-45"
CANDIDATE = SimpleNamespace(
    area_file="smuggler.are", mobile_vnum=17505, room_vnum=17541,
    route_origin_recall_index=0, specials=(), autonomous_safe=True,
)


def initial_state():
    return {
        "name": "Tester", "level": 45, "xp": 2106667, "world_boot_id": "boot",
        "room_vnum": "3054", "campaign_xp_loss_total": 1405,
        "inventory": [{"short_desc": "the Red DragonOrb", "quan": "1"}],
        "campaign_source_resource_reserves": {"sanctuary": {
            "mode": "staff", "object_description": "red dragonorb", "charges_remaining": 5,
        }},
        "campaign_source_ranked_xp_loss_policies": [{
            "boot_id": "boot", "level": 45, "policy_id": POLICY,
            "loss_count": 1, "sanctuary_protected": False,
        }],
    }


def test_selection_reserves_retry_without_consuming_its_own_admission():
    state = initial_state()
    assert _source_ranked_unprotected_reserve_retry_allowed(CANDIDATE, state, character_level=45)
    _record_source_ranked_protection_recovery_retry(state, CANDIDATE, character_level=45)
    marker = state["campaign_protection_recovery_retry"]
    assert marker["attempted"] is False and marker["status"] == "selected"
    assert _source_ranked_unprotected_reserve_retry_allowed(CANDIDATE, state, character_level=45)
    assert not _source_ranked_spent_protection_retry_should_rotate(CANDIDATE, state, character_level=45)
    marker["attempted"] = True
    marker["status"] = "dispatched"
    marker["attempt_segment_id"] = 123
    assert not _source_ranked_unprotected_reserve_retry_allowed(CANDIDATE, state, character_level=45)
    assert _source_ranked_spent_protection_retry_should_rotate(CANDIDATE, state, character_level=45)


def checkpoints(before, after):
    return [
        {"id": 1, "created_at": "2026-11-14T04:00:00+00:00",
         "state_json": json.dumps(before), "reason": "campaign_metadata_repaired",
         "segment_id": 9, "run_id": 9},
        {"id": 2, "created_at": "2026-11-14T04:01:00+00:00",
         "state_json": json.dumps(after), "reason": "awaiting_policy",
         "segment_id": None, "run_id": None},
    ]


def test_legacy_selection_repair_requires_adjacent_no_launch_proof():
    before = initial_state()
    after = deepcopy(before)
    after["campaign_protection_recovery_retry"] = {
        "boot_id": "boot", "level": 45, "policy_id": POLICY, "attempted": True,
    }
    rows = checkpoints(before, after)
    repaired = _repair_unstarted_protection_retry_selection(after, rows, [])
    assert repaired["campaign_protection_recovery_retry"]["attempted"] is False
    assert repaired["campaign_protection_recovery_retry"]["selection_only_repair_of"] == 2
    assert repaired["campaign_source_ranked_xp_loss_policies"] == before["campaign_source_ranked_xp_loss_policies"]
    assert _repair_unstarted_protection_retry_selection(after, rows, [{
        "started_at": "2026-11-14T04:00:30+00:00",
    }]) == after
    missing_origin = checkpoints(after, after)
    assert _repair_unstarted_protection_retry_selection(after, missing_origin, []) == after
    changed = deepcopy(after)
    changed["xp"] -= 1
    assert _repair_unstarted_protection_retry_selection(changed, rows, []) == changed
