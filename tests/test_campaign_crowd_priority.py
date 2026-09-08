from copy import deepcopy

import pytest

from dd4tester.campaign import (
    _active_crowded_research_policy_id,
    _retry_any_crowded_research_policy,
)


FIELD = "source-ranked-hunt-moria-4004-4028-8"
OLD_FIELD = "source-ranked-hunt-circus-4406-4409-6"


def crowd_state():
    return {
        "level": 8,
        "world_boot_id": "boot-1",
        "campaign_research_results": {
            policy: {"boot_id": "boot-1", "crowded": True}
            for policy in ("liquidate-loot", FIELD, OLD_FIELD)
        },
        "campaign_research_crowd_cooldowns": {
            "liquidate-loot": 1, FIELD: 2, OLD_FIELD: 1,
        },
        "campaign_source_ranked_xp_loss_policies": [
            {"policy_id": FIELD, "boot_id": "boot-1", "level": 8, "loss_count": 1},
        ],
    }


def test_current_field_crowd_precedes_old_shop_record():
    state = crowd_state()
    original = deepcopy(state)
    assert _active_crowded_research_policy_id(state) == FIELD
    assert state == original  # Inspection alone never spends a reset wait.


def test_bounded_reset_reopens_field_without_clearing_shop_or_loss_evidence():
    state = crowd_state()
    original = deepcopy(state)
    retried = _retry_any_crowded_research_policy(state)
    assert retried["campaign_last_policy"] == FIELD
    assert FIELD not in retried["campaign_research_results"]
    assert "liquidate-loot" in retried["campaign_research_results"]
    assert OLD_FIELD in retried["campaign_research_results"]
    assert retried["campaign_source_ranked_xp_loss_policies"] == original[
        "campaign_source_ranked_xp_loss_policies"
    ]
    assert state == original


@pytest.mark.parametrize("restriction", ["exhausted", "old_boot", "no_wait", "excluded"])
def test_ineligible_field_crowd_does_not_override_maintenance(restriction):
    state = crowd_state()
    if restriction == "exhausted":
        state["campaign_research_results"][FIELD]["crowd_exhausted"] = True
    elif restriction == "old_boot":
        state["campaign_research_results"][FIELD]["boot_id"] = "boot-0"
    elif restriction == "no_wait":
        state["campaign_research_crowd_cooldowns"][FIELD] = 0
    excluded = FIELD if restriction == "excluded" else None
    assert _active_crowded_research_policy_id(state, exclude_policy_id=excluded) == "liquidate-loot"
