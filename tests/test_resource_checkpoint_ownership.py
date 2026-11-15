from types import SimpleNamespace

import pytest

from dd4tester.campaign import _campaign_segment_end_state
from dd4tester.character import CharacterSpec
from dd4tester.starter import StarterBotRunner, StarterPolicy
from dd4tester.state import CharacterState


STAFF = {
    "object_vnum": 905, "object_description": "ivory staff",
    "effect": "sanctuary", "mode": "staff", "charges_remaining": 2,
}


def runner():
    value = StarterBotRunner.__new__(StarterBotRunner)
    value.session_state = SimpleNamespace(
        character=CharacterState(inventory=[]), logout=SimpleNamespace(acknowledged=False),
    )
    value.verified_source_resources = {"sanctuary": dict(STAFF)}
    value.source_resource_reserve = {}
    return value


def test_observed_empty_resource_ledger_survives_campaign_merge():
    value = runner()
    policy = SimpleNamespace(login_authenticated=True, training_travel_inventory_revision=1)
    fields = value._source_resource_state_fields(policy, {})
    assert fields == {"campaign_source_resource_reserves": {}}
    previous = {"level": 46, "campaign_source_resource_reserves": {"sanctuary": STAFF}}
    current = {"level": 46, "inventory": [], **fields}
    merged = _campaign_segment_end_state(previous, current, execution="source-ranked-hunt")
    assert merged["campaign_source_resource_reserves"] == {}


@pytest.mark.parametrize("missing", ["login", "inventory_packet", "inventory", "initial", "policy"])
def test_unowned_or_unobserved_empty_ledger_is_not_a_clear(missing):
    value = runner()
    policy = SimpleNamespace(login_authenticated=True, training_travel_inventory_revision=1)
    if missing == "login":
        policy.login_authenticated = False
    elif missing == "inventory_packet":
        policy.training_travel_inventory_revision = 0
    elif missing == "inventory":
        value.character_state.inventory = None
    elif missing == "initial":
        value.verified_source_resources = {}
    else:
        policy = None
    assert value._source_resource_state_fields(policy, {}) == {}


def test_nonempty_and_planned_ledgers_keep_existing_ownership():
    value = runner()
    assert value._source_resource_state_fields(None, {"sanctuary": STAFF}) == {
        "campaign_source_resource_reserves": {"sanctuary": STAFF},
    }
    value.source_resource_reserve = dict(STAFF)
    assert value._source_resource_state_fields(None, {}) == {
        "campaign_source_resource_reserves": {},
    }


def test_confirmed_logout_retains_observed_inventory_ownership():
    value = runner()
    value.session_state.logout.acknowledged = True
    policy = SimpleNamespace(login_authenticated=False, training_travel_inventory_revision=2)
    assert value._source_resource_state_fields(policy, {}) == {
        "campaign_source_resource_reserves": {},
    }
    policy.training_travel_inventory_revision = 0
    assert value._source_resource_state_fields(policy, {}) == {}


def policy():
    value = StarterPolicy(
        CharacterSpec.from_mapping({"name": "Tester", "race": "human", "gender": "male", "class": "warrior"}),
        "password", verified_source_resources={"sanctuary": STAFF},
        source_resource_reserve=STAFF,
    )
    value.fastwalk_acquired_required_object_vnums.add(905)
    return value


def test_acquisition_does_not_restore_original_charge_count():
    value = policy()
    value._consume_source_resource("sanctuary")
    state = CharacterState(inventory=[[{"short_desc": "an ivory staff"}]])
    assert value.source_resource_checkpoint(state)["sanctuary"]["charges_remaining"] == 1
    assert 905 in value.fastwalk_acquired_required_object_vnums


@pytest.mark.parametrize("object_gone", [False, True])
def test_exhausted_or_destroyed_staff_stays_cleared_with_stale_inventory(object_gone):
    value = policy()
    if not object_gone:
        value._consume_source_resource("sanctuary")
    value._consume_source_resource("sanctuary", object_gone=object_gone)
    state = CharacterState(inventory=[[{"short_desc": "an ivory staff"}]])
    assert value.source_resource_checkpoint(state) == {}
    assert 905 in value.fastwalk_acquired_required_object_vnums


def test_used_staff_does_not_clear_an_independent_planned_resource():
    value = policy()
    value.source_resource_reserve = {**STAFF, "object_vnum": 926, "object_description": "nectar"}
    value._consume_source_resource("sanctuary", object_gone=True)
    assert value.source_resource_reserve["object_vnum"] == 926


def test_acquisition_receipt_without_current_item_does_not_restore_reserve():
    value = policy()
    value.verified_source_resources = {}
    assert value.source_resource_checkpoint(CharacterState(inventory=[])) == {}


def test_flight_acquisition_keeps_existing_active_effect_receipt():
    value = policy()
    value.verified_source_resources = {}
    value.source_resource_reserve = {
        "effect": "flight", "mode": "potion", "object_vnum": 4442,
        "object_description": "a clear potion", "consumes_object": True,
    }
    value.fastwalk_acquired_required_object_vnums.add(4442)
    state = CharacterState(inventory=[], affects=[{"name": "fly"}])
    saved = value.source_resource_checkpoint(state)["flight"]
    assert saved["verified_active_affect"] == "fly"
    assert saved["activation_verified"] is True
