from dataclasses import replace

import pytest

from dd4tester.companions import FamiliarPreparation
from dd4tester.hunt_candidates import MobileSource
from test_combat_timing import policy_fixture


REPLY = (
    "The pony grazes the large orc.\n"
    "The pony hits the large orc.\n"
    "The pony hits the large orc.\n"
    "The large orc is DEAD!!\n"
    "The large orc's leg is sliced from his body.\nOk.\n"
)


def opening_fixture(monkeypatch):
    policy, state, clock = policy_fixture(monkeypatch)
    policy.combat_active = policy.fastwalk_attack_started = False
    policy.active_target = policy.active_target_selector = None
    policy.current_room = state.room_vnum = "4024"
    state.in_combat, state.position, state.enemies = False, 7, None
    policy.source_world.mobiles[4005] = MobileSource(
        4005, "orc large", "the large orc", 7, 0, 0, "moria.are",
        "This large orc is looking for someone small to pick on.",
    )
    policy.fastwalk_hunt_stops = (replace(
        policy.fastwalk_hunt_stops[0], target="the large orc",
        source_mobile_vnum=4005, exact_target=True,
        source_policy_id="source-ranked-hunt-moria-4005-4022-8",
    ),)
    policy.consider_target = "the large orc"
    policy.consider_target_selector = "#23798"
    policy.consider_viable = True
    policy.room_target_selectors["4024"] = {"the large orc": ["#23798"]}
    policy.room_target_selector_descriptions["4024"] = {
        "#23800": policy._staged_familiar_description(),
        "#23798": "this large orc is looking for someone small to pick on.",
    }
    policy.familiar_preparation = FamiliarPreparation(
        stage="ready", selector="#23800", summoned=True, grouped=True,
    )
    decision = policy._familiar_precombat_decision(
        state, target="the large orc", allow_start=True,
    )
    assert decision.command == "order #23800 kill #23798"
    return policy, state


@pytest.mark.parametrize("fragmented", [False, True])
def test_run_12811_opening_death_cancels_player_attack_and_preserves_loot(monkeypatch, fragmented):
    policy, state = opening_fixture(monkeypatch)
    chunks = REPLY.split("DEAD")
    if fragmented:
        policy.observe_text(chunks[0] + "DE")
        policy.observe_text("AD" + chunks[1])
    else:
        policy.observe_text(REPLY)
    assert policy.completed_kills == [{
        "mob_name": "the large orc", "xp_gained": 0,
        "source_mobile_vnum": 4005,
        "source_policy_id": "source-ranked-hunt-moria-4005-4022-8",
        "objective_eligible": False,
    }]
    assert policy.objective_kills == []
    assert "4024" in policy.pending_loot_rooms
    assert policy.fastwalk_hunt_stop_killed
    assert not policy.familiar_preparation.order_pending
    assert policy.familiar_precombat_step is None
    assert policy._familiar_precombat_decision(state) is None
    policy.observe_text("Ok.\n")
    assert len(policy.completed_kills) == 1


@pytest.mark.parametrize("boundary", [
    "room", "target", "selector", "owner", "duplicate_companion", "no_order",
    "source", "other_actor", "quotation", "no_death", "player_xp", "duplicate_target",
])
def test_opening_death_requires_the_pending_owned_exact_encounter(monkeypatch, boundary):
    policy, _ = opening_fixture(monkeypatch)
    reply = REPLY
    if boundary == "room":
        policy.current_room = "4022"
    elif boundary == "target":
        reply = reply.replace("large orc", "ordinary orc")
    elif boundary == "selector":
        policy.consider_target_selector = "#999"
    elif boundary == "owner":
        policy.familiar_preparation.grouped = False
    elif boundary == "duplicate_companion":
        policy.room_target_selector_descriptions["4024"]["#999"] = policy._staged_familiar_description()
    elif boundary == "duplicate_target":
        policy.room_target_selectors["4024"]["the large orc"].insert(0, "#999")
    elif boundary == "no_order":
        policy.familiar_preparation.order_pending = False
    elif boundary == "source":
        policy.source_world.mobiles.pop(4005)
    elif boundary == "other_actor":
        reply = reply.replace("The pony", "The guard")
    elif boundary == "quotation":
        reply = "Someone says 'The pony hits the large orc.'\nThe large orc is DEAD!!\nOk.\n"
    elif boundary == "no_death":
        reply = "The pony hits the large orc.\nOk.\n"
    elif boundary == "player_xp":
        reply += "You receive 195 experience points.\n"
    policy.observe_text(reply)
    assert policy.completed_kills == []
    assert not policy.pending_loot_rooms


def test_actual_companion_death_cancels_opener_without_claiming_target_kill(monkeypatch):
    policy, state = opening_fixture(monkeypatch)
    policy.observe_text("The large orc hits the pony.\nThe pony is DEAD!!\nOk.\n")
    assert not policy.familiar_active and policy.familiar_unavailable
    assert policy.familiar_precombat_step is None
    assert policy._familiar_precombat_decision(state) is None
    assert policy.completed_kills == []


def test_companion_death_does_not_end_the_players_existing_fight(monkeypatch):
    policy, _, _ = policy_fixture(monkeypatch)
    policy.familiar_active = True
    policy.observe_text("Katrina the Shepherd hits the pony.\nThe pony is DEAD!!\n")
    assert policy.active_target == "Katrina the Shepherd"
    assert policy.combat_active
    assert not policy.familiar_active
    assert policy.completed_kills == []


def test_quoted_companion_death_is_not_loss_of_ownership(monkeypatch):
    policy, _, _ = policy_fixture(monkeypatch)
    policy.familiar_active = True
    policy.observe_text("Someone says 'The pony is DEAD!!'\n")
    assert policy.familiar_active and not policy.familiar_unavailable
