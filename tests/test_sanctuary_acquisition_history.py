import json

import dd4tester.campaign as campaign


POLICY = "source-ranked-hunt-sewer-7040-7428-46-sanctuary-maintenance"


def acquired_state():
    return {
        "level": 46, "world_boot_id": "boot-1",
        campaign._SOURCE_REVISION_KEY: "old-source",
        "campaign_research_results": {POLICY: {
            "boot_id": "boot-1", "observed": True, "viable": True,
            "required_object_acquired": True, "required_object_vnums": [7303],
            "completed_kill": False, "acquisition_segment_id": 20,
        }},
    }


def test_source_refresh_keeps_acquisition_provenance_not_old_permission():
    state = acquired_state()
    campaign._synchronize_source_revision(state, "new-source")
    receipt = state[campaign._SANCTUARY_CARRIER_ACQUISITIONS_KEY][0]
    assert receipt["acquisition_segment_id"] == 20
    assert receipt[campaign._SOURCE_REVISION_KEY] == "old-source"
    assert POLICY not in state.get("campaign_research_results", {})


def test_unacquired_object_never_becomes_a_preferred_carrier():
    state = acquired_state()
    state["campaign_research_results"][POLICY]["required_object_acquired"] = False
    campaign._remember_sanctuary_carrier_acquisitions(state)
    assert campaign._SANCTUARY_CARRIER_ACQUISITIONS_KEY not in state


def test_bounded_repair_does_not_restore_research_or_clear_failures():
    state = {
        "level": 46, "world_boot_id": "boot-1",
        campaign._SOURCE_REVISION_KEY: "new-source",
        "campaign_research_results": {"independent": {"viable": False}},
        campaign._SOURCE_RANKED_XP_LOSS_POLICIES_KEY: [{"policy_id": "failed"}],
    }
    calls = []

    class History:
        def list_recent_campaign_segment_headers(self, campaign_id, *, limit):
            assert campaign_id == 39 and limit == 256
            return [{"id": 20, "phase": POLICY}]

        def get_latest_campaign_segment_summary_for_phase(self, campaign_id, phase, **kwargs):
            calls.append(phase)
            assert kwargs["search_limit"] == 256
            return {"end_state_json": json.dumps(acquired_state())}

    repaired = campaign._repair_sanctuary_acquisition_history(state, storage=History(), campaign_id=39)
    assert calls == [POLICY]
    assert repaired["campaign_research_results"] == state["campaign_research_results"]
    assert repaired[campaign._SOURCE_RANKED_XP_LOSS_POLICIES_KEY] == state[campaign._SOURCE_RANKED_XP_LOSS_POLICIES_KEY]
    assert repaired[campaign._SANCTUARY_CARRIER_ACQUISITIONS_KEY][0]["acquisition_segment_id"] == 20
    assert campaign._repair_sanctuary_acquisition_history(repaired, storage=History(), campaign_id=39) is repaired
