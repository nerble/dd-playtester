from dd4tester.campaign import _active_source_ranked_reset_policy_id


FAILED = "source-ranked-hunt-mirror-realm-19034-19114-45"
ABSENT = "source-ranked-hunt-example-900-901-45"


def state():
    return {
        "level": 45, "world_boot_id": "boot",
        "campaign_research_absence_cooldowns": {FAILED: 1, ABSENT: 2},
        "campaign_research_results": {
            key: {"boot_id": "boot", "absent": True}
            for key in (FAILED, ABSENT)
        },
        "campaign_source_ranked_xp_loss_policies": [{
            "boot_id": "boot", "level": 45, "policy_id": FAILED,
            "sanctuary_protected": True, "loss_count": 1,
        }],
    }


def test_recorded_loss_cannot_be_presented_as_reset_wait():
    current = state()
    assert _active_source_ranked_reset_policy_id(current) == ABSENT
    current["campaign_research_absence_cooldowns"].pop(ABSENT)
    assert _active_source_ranked_reset_policy_id(current) is None
    assert current["campaign_source_ranked_xp_loss_policies"][0]["loss_count"] == 1


def test_prior_level_loss_does_not_close_a_current_level_absence():
    current = state()
    current["campaign_source_ranked_xp_loss_policies"][0]["level"] = 44
    assert _active_source_ranked_reset_policy_id(current) == FAILED
