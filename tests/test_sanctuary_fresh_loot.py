import pytest

from dd4tester.campaign import _campaign_segment_objective_outcome
from dd4tester.character import CharacterSpec
from dd4tester.equipment import GearCatalog
from dd4tester.hunt_candidates import ObjectSource
from dd4tester.starter import FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


@pytest.mark.parametrize("maintenance", [True, False])
def test_carried_empty_staff_does_not_prove_fresh_sanctuary_replenishment(maintenance):
    item = ObjectSource(905, "staff ivory", "an ivory staff", 4, (30, 3, 3, 0), 36)
    spec = CharacterSpec.from_mapping({
        "name": "Tester", "race": "human", "gender": "male", "class": "warrior",
    })
    policy = StarterPolicy(spec, "test-password", gear_catalog=GearCatalog({905: item}),
                           source_resource_reserve={"effect": "sanctuary", "mode": "staff",
                                                    "object_vnum": 905, "object_description": "an ivory staff",
                                                    "charges_remaining": 3})
    stop = FieldHuntStop(
        route=(), target="the carrier", required_items=("an ivory staff",),
        source_policy_id="source-ranked-hunt-test-1-100-46-sanctuary-maintenance"
        if maintenance else "source-ranked-hunt-test-1-100-46",
        allow_below_band_for_required_loot=maintenance, source_loot_object_vnums=(905,),
    )
    state = CharacterState(inventory=[[{"short_desc": "an ivory staff", "quan": "1"}]])
    assert policy._missing_fastwalk_required_items(state, stop) == (
        ["an ivory staff"] if maintenance else []
    )
    assert not policy.fastwalk_acquired_required_object_vnums
    policy.fastwalk_acquired_required_object_vnums.add(905)
    assert policy._missing_fastwalk_required_items(state, stop) == []


@pytest.mark.parametrize("execution", ["moria-sanctuary-hunt", "moria-deep-sanctuary-hunt"])
def test_carrier_kill_without_any_acquisition_cannot_report_resupply_achieved(execution):
    assert _campaign_segment_objective_outcome(
        execution, [{"source_mobile_vnum": 916}],
        final_state={"campaign_fastwalk_required_object_vnums": []},
    ) == ("not_achieved", True)
    assert _campaign_segment_objective_outcome(
        execution, [], final_state={"campaign_fastwalk_required_object_vnums": [905]},
    ) == (None, False)
