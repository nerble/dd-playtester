import json
from copy import deepcopy

import pytest

import dd4tester.campaign as campaign
from dd4tester.hunt_candidates import MobReset, WorldSource


POLICY = "source-ranked-hunt-mirror-realm-19004-19068-46-sanctuary-maintenance"


@pytest.mark.parametrize("blocker", [None, "new-source", "right-kill", "mixed-kills", "right-object", "different-segment"])
def test_wrong_carrier_receipt_is_invalidated_only_with_linked_current_source_proof(blocker):
    result = {"boot_id": "boot", "observed": True, "viable": True,
              "required_object_acquired": True, "required_object_vnums": [4050],
              "acquisition_segment_id": 20}
    state = {"name": "Tester", "level": 46, "world_boot_id": "boot",
             campaign._SOURCE_REVISION_KEY: "source", "combat_pouch_potions": {"purple": 1},
             "campaign_research_results": {POLICY: result},
             campaign._SANCTUARY_CARRIER_ACQUISITIONS_KEY: [{**result, "policy_id": POLICY}]}
    if blocker == "right-object":
        result["required_object_vnums"] = [19173]
    original = deepcopy(state)
    snapshot = {"name": "Tester", "level": 46, "world_boot_id": "boot",
                campaign._SOURCE_REVISION_KEY: "other" if blocker == "new-source" else "source"}

    class History:
        def list_recent_campaign_segment_headers(self, campaign_id, *, limit):
            assert limit == 256
            return [{"id": 20, "phase": POLICY, "run_id": 7, "sequence": 2}]

        def get_latest_campaign_segment_summary_for_phase(self, campaign_id, phase, **kwargs):
            assert kwargs["search_limit"] == 256
            return {"sequence": 3 if blocker == "different-segment" else 2,
                    "end_state_json": json.dumps(snapshot)}

        def get_run_summary(self, run_id):
            assert run_id == 7
            mobiles = [19004] if blocker == "right-kill" else [4055, 19004] if blocker == "mixed-kills" else [4055]
            return {"progress": {"confirmed_kills": [{"source_mobile_vnum": vnum} for vnum in mobiles]}}

    world = WorldSource(mob_resets=[MobReset(19004, 19068, 1, (19173,))])
    repaired = campaign._invalidate_mismatched_sanctuary_acquisitions(
        state, storage=History(), campaign_id=39, source_world=world,
    )
    assert state == original
    assert repaired["combat_pouch_potions"] == {"purple": 1}
    if blocker is None:
        corrected = repaired["campaign_research_results"][POLICY]
        assert corrected["required_object_acquired"] is False
        assert corrected["viable"] is False
        assert corrected["invalidated_acquisition"] == result
        assert corrected["actual_mobile_vnums"] == [4055]
        assert repaired[campaign._SANCTUARY_CARRIER_ACQUISITIONS_KEY][0]["dispatch_identity_mismatch"]
        assert campaign._source_resource_dispatch_contract_repair_applies(
            repaired, {"id": 20, "phase": POLICY}, policy_id=POLICY,
        )
        assert not campaign._source_resource_dispatch_contract_repair_applies(
            repaired, {"id": 21, "phase": POLICY}, policy_id=POLICY,
        )
        historical = {**repaired, "campaign_research_results": {POLICY: result}}
        campaign._remember_sanctuary_carrier_acquisitions(historical)
        assert historical[campaign._SANCTUARY_CARRIER_ACQUISITIONS_KEY][0]["dispatch_identity_mismatch"]
    else:
        assert repaired == state


def test_failed_run_retains_owned_visibility_funding_receipt(monkeypatch):
    receipt = {"failed": True, "funding_required": True, "price": 248}
    monkeypatch.setattr(campaign, "_run_latest_state", lambda *a: {"room_vnum": "3054"})
    monkeypatch.setattr(campaign, "_run_failed_terminal_state", lambda *a: {"campaign_visibility_preparation": receipt})
    result = campaign._campaign_failure_state_from_run(
        object(), 7, {}, character_name="Tester",
    )
    assert result["campaign_visibility_preparation"] == receipt


def test_intervening_maintenance_does_not_erase_visibility_quote_failure():
    receipt = {"failed": True, "funding_required": True, "price": 248,
               "boot_id": "boot", "level": 46}
    previous = {"name": "Tester", "level": 46, "world_boot_id": "boot",
                "campaign_visibility_preparation": receipt}
    current = {"name": "Tester", "level": 46, "world_boot_id": "boot"}
    result = campaign._campaign_segment_end_state(previous, current, execution="return-home")
    assert result["campaign_visibility_preparation"] == receipt
