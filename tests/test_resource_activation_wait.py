import pytest

from dd4tester.temporal_evidence import resource_activation_waiting
from dd4tester.character import CharacterSpec
from dd4tester.starter import BotDecision, FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


def test_fullness_refusal_expires_without_consuming_or_reboot_ban():
    record = {"activation_failure": "too_full", "charges_remaining": 1,
              "activation_retry_after_epoch": 300}
    assert resource_activation_waiting(record, now=299)
    assert not resource_activation_waiting(record, now=300)
    assert record["charges_remaining"] == 1
    assert not resource_activation_waiting({}, now=0)


@pytest.mark.parametrize("deadline", ["later", True, float("nan"), float("inf")])
def test_malformed_activation_wait_is_not_ready(deadline):
    assert resource_activation_waiting({"activation_retry_after_epoch": deadline}, now=0)


def test_live_fullness_refusal_retains_the_pill_in_checkpoint(monkeypatch):
    monkeypatch.setattr("dd4tester.starter.time.time", lambda: 1000)
    record = {"object_vnum": 926, "object_description": "nectar", "effect": "sanctuary",
              "mode": "pill", "command": "eat", "command_keyword": "nectar",
              "charges_remaining": 1}
    policy = StarterPolicy(
        CharacterSpec.from_mapping({"name": "Tester", "race": "human", "gender": "male", "class": "warrior"}),
        "password", verified_source_resources={"sanctuary": record},
    )
    policy.pending_source_resource_effect = "sanctuary"
    policy.observe_text("You are too full to eat more.\n")
    state = CharacterState(inventory=[[{"short_desc": "nectar"}]])
    saved = policy.source_resource_checkpoint(state)["sanctuary"]
    assert saved["activation_retry_after_epoch"] == 1300
    assert saved["activation_failure"] == "too_full"
    assert saved["charges_remaining"] == 1
    assert policy.pending_source_resource_effect is None


@pytest.mark.parametrize("hunger,maximum,prior_refusal,expected", [
    (48, 48, False, True), (44, 48, False, True), (43, 48, False, False),
    (20, 48, False, False), (None, 48, False, False), (48, None, False, False),
    (20, 48, True, True),
])
def test_required_pill_checks_known_fullness_before_leaving_healer(monkeypatch, hunger, maximum, prior_refusal, expected):
    policy = StarterPolicy(
        CharacterSpec.from_mapping({"name": "Tester", "race": "human", "gender": "male", "class": "warrior"}),
        "password", verified_source_resources={"sanctuary": {
            "effect": "sanctuary", "mode": "pill",
            **({"activation_failure": "too_full"} if prior_refusal else {}),
        }}, fastwalk_hunt_stops=(FieldHuntStop((), "target", require_sanctuary=True),),
    )
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(room_vnum="3054", room_flags=["healing"], position=7,
                           hunger=hunger, max_hunger=maximum)
    command = BotDecision("eat nectar", "verify the actual effect")
    monkeypatch.setattr(policy, "_source_resource_decision", lambda *_a, **_kw: command)
    assert policy._healer_source_pill_preparation_decision(state) is (command if expected else None)


@pytest.mark.parametrize("blocker", ["field", "sleeping", "combat", "return", "optional", "other_effect", "waiting"])
def test_healer_pill_preparation_keeps_scope_and_wait_guards(monkeypatch, blocker):
    record = {"effect": "sanctuary", "mode": "pill"}
    policy = StarterPolicy(
        CharacterSpec.from_mapping({"name": "Tester", "race": "human", "gender": "male", "class": "warrior"}),
        "password", verified_source_resources={"sanctuary": record},
        fastwalk_hunt_stops=(FieldHuntStop((), "target", require_sanctuary=blocker != "optional"),),
    )
    policy.in_world = policy.prompt_ready = True
    state = CharacterState(room_vnum="3054", room_flags=["healing"], position=7, hunger=48, max_hunger=48)
    if blocker == "field":
        state.room_vnum = "39004"
    elif blocker == "sleeping":
        state.position = 4
    elif blocker == "combat":
        state.in_combat = True
    elif blocker == "return":
        policy.fastwalk_returning = True
    elif blocker == "other_effect":
        policy.verified_source_resources["sanctuary"]["effect"] = "detect hidden"
    elif blocker == "waiting":
        policy.verified_source_resources["sanctuary"]["activation_retry_after_epoch"] = float("inf")
    monkeypatch.setattr(policy, "_source_resource_decision", lambda *_a, **_kw: pytest.fail("preparation must stay closed"))
    assert policy._healer_source_pill_preparation_decision(state) is None
