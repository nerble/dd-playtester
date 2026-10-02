from dataclasses import replace
import json
from types import SimpleNamespace

import pytest

from dd4tester.hunt_candidates import ObjectSource, SourceTeacherRoute
from dd4tester.campaign import _restore_training_travel_result
from dd4tester.training_travel import (
    TrainingTravelPlan, TrainingTravelSession, carried_potion_keyword,
    inventory_footer_mismatch,
)


PROMPT = "<100/100 hits 40/40 mana 90/100 move [Town]> "
PLAN = TrainingTravelPlan(
    SourceTeacherRoute(7, 8, "Teacher", "master", "warrior",
                       (("3001", "east", "8"),)),
    9231, "anti-cyclops elixir", (3054, 3001, 8), (("dodge", 40, 60),), (28, 24, 20), 26, "boot",
)
ITEM = (("anti-cyclops elixir", "#42"),)


def step(session, now=1.0, **overrides):
    args = dict(inventory=ITEM, inventory_revision=1, affect_revision=1, duration=None, now=now)
    args.update(overrides)
    return session.next_command(**args)


def prepared_session():
    session = TrainingTravelSession(PLAN)
    start_inventory(session)
    session.observe("Your backpack contains:\n[#42] anti-cyclops elixir\n" + PROMPT)
    assert step(session, 2) == "quaff #42"
    session.observe("You quaff anti-cyclops elixir.\nYou fade out of existence.\n" + PROMPT)
    assert step(session, 3, inventory=(), inventory_revision=2, affect_revision=2, duration=17) == "inventory"
    return session


def start_inventory(session):
    assert step(session, 0) == "config +targetmode"
    session.observe("Targetmode is now ON.\n" + PROMPT)
    assert step(session, 1) == "inventory"


def test_activation_requires_consumption_and_new_affect_not_duplicate_inventory_event():
    session = prepared_session()
    session.observe("Your backpack contains:\na pie\n" + PROMPT)
    assert step(session, 4, inventory=(), inventory_revision=2, affect_revision=2, duration=17) is None
    assert session.stage == "ready"
    assert session.check_route(room="3054", move=28, duration=17)
    assert session.check_route(room="3001", move=24, duration=17)
    assert session.check_route(room="8", move=20, duration=17)


@pytest.mark.parametrize("change", [
    dict(affect_revision=1), dict(inventory_revision=1), dict(inventory=ITEM),
    dict(duration=None), dict(duration=1),
])
def test_unconfirmed_consumption_or_effect_never_opens_route(change):
    session = prepared_session()
    session.observe("Your backpack contains:\na pie\n" + PROMPT)
    values = dict(inventory=(), inventory_revision=2, affect_revision=2, duration=17)
    values.update(change)
    assert step(session, 4, **values) is None
    assert session.stage == "failed"
    assert not session.check_route(room="3054", move=100, duration=17)


@pytest.mark.parametrize("listing", [
    "Your backpack contains:\nanti-cyclops elixir\n",
    "Your backpack contains:\n[#43] anti-cyclops elixir\n",
    "Your backpack contains:\n[#42] anti-cyclops elixir\n[#43] anti-cyclops elixir\n",
    "Somebody says '[#42] anti-cyclops elixir'\n",
])
def test_carried_selector_requires_exact_request_local_listing(listing):
    session = TrainingTravelSession(PLAN)
    start_inventory(session)
    session.observe(listing + PROMPT)
    assert step(session, 2) is None
    session.expire(6)
    assert session.stage == "failed"


def test_split_listing_and_finite_confirmation_timeout():
    session = TrainingTravelSession(PLAN)
    start_inventory(session)
    session.observe("Your backpack contains:\n[#42] anti-cyclops ")
    assert step(session, 2) is None
    session.observe("elixir\n" + PROMPT)
    assert step(session, 3) == "quaff #42"
    assert session.expire(8)
    assert step(session, 9) is None


def test_previous_prompt_cannot_complete_the_inventory_request():
    session = TrainingTravelSession(PLAN)
    start_inventory(session)
    session.observe("Targetmode is now ON.\n" + PROMPT)
    assert step(session, 2) is None
    assert session.stage == "inventory"
    session.observe("Your backpack contains:\n[#42] anti-cyclops ")
    assert step(session, 3) is None
    session.observe("elixir\n" + PROMPT)
    assert step(session, 4) == "quaff #42"


def test_saved_zero_id_object_uses_only_a_source_unique_keyword():
    session = TrainingTravelSession(replace(PLAN, unique_keyword="anti-cyclops"))
    start_inventory(session)
    session.observe("Your backpack contains:\nanti-cyclops elixir\n" + PROMPT)
    assert step(session, 2, inventory=(("anti-cyclops elixir", None),)) == "quaff anti-cyclops"
    assert session.selector == "anti-cyclops"


def test_duplicate_zero_id_potions_remain_ambiguous():
    session = TrainingTravelSession(replace(PLAN, unique_keyword="anti-cyclops"))
    start_inventory(session)
    session.observe("Your backpack contains:\nanti-cyclops elixir\nanti-cyclops elixir\n" + PROMPT)
    assert step(session, 2, inventory=(("anti-cyclops elixir", None),) * 2) is None
    assert session.stage == "failed"


def potion_sources():
    return {
        9231: ObjectSource(9231, "elixir anti", "anti-cyclops elixir", 10, (15,), 1),
        2: ObjectSource(2, "elixir healing", "a healing elixir", 10, (15,), 1),
        3: ObjectSource(3, "antidote potion", "an antidote", 10, (15,), 1),
        4: ObjectSource(4, "pie", "a pie", 19, (1,), 1),
    }


def test_source_keyword_can_be_unique_in_complete_carried_inventory():
    sources = potion_sources()
    assert carried_potion_keyword(sources, 9231, [PLAN.description, "a pie"]) == "elixir"
    assert carried_potion_keyword(
        sources, 9231, [PLAN.description, "a healing elixir"],
    ) == "anti"
    assert carried_potion_keyword(
        sources, 9231, [PLAN.description, "a healing elixir", "an antidote"],
    ) is None
    assert carried_potion_keyword(sources, 9231, [PLAN.description, "unknown relic"]) is None
    assert carried_potion_keyword(sources, 9231, [PLAN.description] * 2) is None


@pytest.mark.parametrize("text,inventory,expected", [
    ("anti-cyclops elixir\n( 2) a pie\n",
     ((PLAN.description, None), ("a pie", None), ("a pie", None)), "quaff elixir"),
    ("anti-cyclops elixir\na healing elixir\n",
     ((PLAN.description, None), ("a healing elixir", None)), "quaff anti"),
    ("anti-cyclops elixir\nan antidote\n",
     ((PLAN.description, None),), None),
    ("anti-cyclops elixir\n",
     ((PLAN.description, None), ("a healing elixir", None)), None),
    ("anti-cyclops elixir\na renamed bottle\n",
     ((PLAN.description, None), ("a renamed bottle", None)), None),
])
def test_carried_keyword_requires_complete_matching_text_and_gmcp(text, inventory, expected):
    session = TrainingTravelSession(PLAN)
    start_inventory(session)
    session.observe("Your backpack contains:\n" + text + PROMPT)
    assert step(session, 2, inventory=inventory, source_objects=potion_sources()) == expected
    assert session.stage == ("quaff" if expected else "failed")


def test_carried_source_alias_cannot_hide_a_conflicting_keyword():
    sources = potion_sources()
    sources[5] = ObjectSource(5, "anti elixir", "a pie", 10, (15,), 1)
    assert carried_potion_keyword(sources, 9231, [PLAN.description, "a pie"]) is None


def test_carried_total_footer_is_not_an_inventory_item():
    session = TrainingTravelSession(PLAN)
    start_inventory(session)
    text = (
        "Your backpack contains:\n\ranti-cyclops elixir\n\ra pie\n\ra pie\n\r"
        "You are carrying 23/38 items.\n\r\n\r" + PROMPT
    )
    session.observe(text)
    inventory = ((PLAN.description, None), ("a pie", None), ("a pie", None))
    assert step(session, 2, inventory=inventory, source_objects=potion_sources()) == "quaff elixir"
    names = [name for name, _ in inventory]
    assert inventory_footer_mismatch(text, names)
    assert not inventory_footer_mismatch(text, [PLAN.description, "a pie"])
    assert not inventory_footer_mismatch(text.replace("23/38 items.", "a mystery item."), names)
    assert not inventory_footer_mismatch(text.replace(PROMPT, "a hidden bottle\n" + PROMPT), names)


def test_footer_repair_requires_the_recorded_request_and_exact_failed_result():
    marker = {
        "level": 29, "boot_id": "boot", "setup_revision": 3,
        "object_vnum": 9231, "teacher_vnum": 7, "teacher_room_vnum": 8,
    }
    result = {
        **marker, "failure": "no unique freshly observed carried potion selector",
        "selector": None, "route_index": 0, "accepted_lessons": 0,
    }
    state = {
        "level": 29, "world_boot_id": "boot", "room_vnum": "3054",
        "campaign_consumable_training_travel": marker,
        "campaign_training_travel_result": result,
        "inventory": [[{"quan": "1", "short_desc": PLAN.description}]],
    }
    events = [
        {"kind": "command", "payload_json": json.dumps({"command": "inventory"})},
        {"kind": "response", "payload_json": json.dumps({"text":
         "Your backpack contains:\nanti-cyclops elixir\nYou are carrying 21/38 items.\n" + PROMPT})},
        {"kind": "command", "payload_json": json.dumps({"command": "save"})},
    ]

    def latest(campaign_id, phase, *, search_limit):
        assert search_limit == 256
        return {"status": "success", "finished_at": "finished", "run_id": 55,
                "end_state_json": json.dumps(state)}

    def recent(run_id, *, limit):
        assert (run_id, limit) == (55, 64)
        return events

    storage = SimpleNamespace(get_latest_campaign_segment_for_phase=latest,
                              list_recent_events=recent)
    repaired = _restore_training_travel_result(storage, 7, state)
    assert repaired["campaign_training_travel_result"]["inventory_footer_repair"]["run_id"] == 55
    assert _restore_training_travel_result(storage, 7, repaired) is repaired
    events[0]["payload_json"] = json.dumps({"command": "score"})
    assert _restore_training_travel_result(storage, 7, state) is state
    events[0]["payload_json"] = json.dumps({"command": "inventory"})
    events[2]["payload_json"] = json.dumps({"command": "quaff elixir"})
    assert _restore_training_travel_result(storage, 7, state) is state


def test_legacy_training_result_is_restored_only_from_the_exact_completed_attempt():
    marker = {
        "level": 29, "boot_id": "boot", "setup_revision": 2,
        "object_vnum": 9231, "teacher_vnum": 7, "teacher_room_vnum": 8,
    }
    state = {
        "level": 29, "world_boot_id": "boot", "room_vnum": "3054",
        "campaign_consumable_training_travel": marker,
    }
    result = {**marker, "selector": None, "route_index": 0, "accepted_lessons": 0}
    end = {**state, "campaign_training_travel_result": result}
    calls = []

    def latest(campaign_id, phase, *, search_limit):
        calls.append((campaign_id, phase, search_limit))
        return {
            "status": "success", "finished_at": "2026-10-02T05:00:00+00:00",
            "run_id": 55, "end_state_json": json.dumps(end),
        }

    storage = SimpleNamespace(get_latest_campaign_segment_for_phase=latest)
    restored = _restore_training_travel_result(storage, 7, state)
    assert restored["campaign_training_travel_result"]["restored_from_run_id"] == 55
    assert calls == [(7, "consumable-training-travel-20-29", 256)]
    assert "campaign_training_travel_result" not in state
    assert _restore_training_travel_result(storage, 7, restored) is restored
    assert len(calls) == 1
    end["campaign_consumable_training_travel"] = {**marker, "teacher_vnum": 9}
    assert _restore_training_travel_result(storage, 7, state) is state
    explicit = {**state, "campaign_training_travel_result": None}
    assert _restore_training_travel_result(storage, 7, explicit) is explicit


@pytest.mark.parametrize("room,move,duration", [
    ("8", 100, 17), ("999", 100, 17), ("3054", 27, 17),
    ("3054", 100, 1), ("3054", 100, None),
])
def test_changed_route_or_expiring_effect_stops_the_trip(room, move, duration):
    session = TrainingTravelSession(PLAN, stage="ready")
    assert not session.check_route(room=room, move=move, duration=duration)
    assert session.failure


def test_route_tracks_repeated_rooms_in_order():
    plan = replace(PLAN, rooms=(3054, 3001, 9, 3001, 8), movement_remaining=(36, 32, 28, 24, 20))
    session = TrainingTravelSession(plan, stage="ready")
    for index, room in enumerate(plan.rooms):
        assert session.check_route(room=str(room), move=100, duration=17)
        assert session.route_index == index
