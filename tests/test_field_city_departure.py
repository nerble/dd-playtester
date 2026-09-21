from dataclasses import replace
from pathlib import Path

import pytest

from dd4tester.character import CharacterSpec
from dd4tester.city_travel import (
    field_city_route_rooms,
    observed_guard_safe_alignment,
    revealed_gmcp_alignment,
)
from dd4tester.fastwalks import Fastwalk
from dd4tester.hunt_candidates import WorldSource, load_world_source
from dd4tester.starter import FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


@pytest.fixture(scope="module")
def world():
    return load_world_source(Path("runs/dd4-source/server/area"), include_all_areas=True)


@pytest.mark.parametrize("value", [50000, "50000", None, True, 299, -1000, 1001, 300.0, "bad"])
def test_hidden_or_invalid_alignment_does_not_prove_guard_nonassistance(value):
    assert not observed_guard_safe_alignment(value, level=10)


@pytest.mark.parametrize("value", [300, "300", 349, 1000])
def test_revealed_alignment_matches_guard_threshold(value):
    assert observed_guard_safe_alignment(value, level=10)
    assert observed_guard_safe_alignment(value, level=24)
    assert not observed_guard_safe_alignment(value, level=9)


@pytest.mark.parametrize(
    ("value", "level", "expected"),
    [("1000", "24", 1000), (-347, 10, -347), (50000, 9, None),
     (50000, 10, None), (1001, 24, None), ("bad", 24, None)],
)
def test_revealed_gmcp_alignment_preserves_only_authoritative_values(
    value, level, expected,
):
    assert revealed_gmcp_alignment(value, level=level) == expected


def test_source_city_scope_includes_refill_and_actual_route_only(world):
    route = Fastwalk("moria", 1, 100, "2s6e8n")
    rooms = field_city_route_rooms(
        world, route.commands, origin=3001, alignment=50000, level=8,
    )
    assert world.rooms[3005].name in rooms
    market = world.rooms[world.rooms[3005].exits["south"].destination]
    assert market.name in rooms
    assert world.rooms[3033].name not in rooms  # Magic Shop is not on this route.
    assert world.rooms[4017].name not in rooms


@pytest.mark.parametrize("source,origin,alignment", [
    (False, 3001, 50000), (True, 9999, 50000), (True, 3001, 300),
])
def test_departure_scope_does_not_invent_source_or_override_other_origins(world, source, origin, alignment):
    assert not field_city_route_rooms(
        world if source else None, ("south",), origin=origin,
        alignment=alignment, level=10,
    )


def test_no_guard_or_greeter_source_does_not_add_a_city_gate():
    assert not field_city_route_rooms(
        WorldSource(), ("south",), origin=3001, alignment=0, level=10,
    )


def setup(world, monkeypatch, character_class="mage"):
    clock = [100.0]
    monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: clock[0])
    bot = StarterPolicy(
        CharacterSpec.from_mapping({"name": "Testsubject", "race": "human", "gender": "female", "class": character_class}),
        "fixture-password", source_world=world,
        fastwalk_route=Fastwalk("source-ranked hunt centipede 4017", 1, 100, "2s6e8n"),
        fastwalk_hunt_stops=(FieldHuntStop((), "the centipede", source_mobile_vnum=4002),),
        title_configured=True, description_configured=True,
    )
    bot.in_world = bot.prompt_ready = True
    bot.world_boot_id = "boot"
    state = CharacterState(
        level=8, hp=113, max_hp=113, mana=324, max_mana=324, move=220, max_move=220,
        room_vnum="3054", room_name="By the Temple Altar", position=7, area="Midgaard",
        progress={"alignment": 50000}, hunger=30, thirst=30,
    )
    return bot, state, clock


def locate(bot, state, response):
    handled, decision = bot._field_city_departure_decision(state)
    assert handled and decision.command == "where drunk"
    bot.after_command(decision)
    bot.observe_text(response + "\n<113/113 hits 324/324 mana 220/220 move [Midgaard]>")
    bot.prompt_ready = True


@pytest.mark.parametrize("character_class", ["mage", "thief", "warrior"])
def test_run_12792_city_departure_checks_before_moving(world, monkeypatch, character_class):
    bot, state, _ = setup(world, monkeypatch, character_class)
    decision = bot._fastwalk_research_decision(state)
    assert decision.command == "where drunk"
    assert bot.fastwalk_outbound_index == 0
    assert not bot.fastwalk_recall_started
    assert not bot.magic_shop_invisibility_attempted
    assert bot.city_shop_transit.status == "idle"


def test_bounded_city_transit_can_admit_a_funding_departure(world, monkeypatch):
    bot, state, _ = setup(world, monkeypatch)
    bot.allow_bounded_city_shop_transit = True
    handled, decision = bot._field_city_departure_decision(state)
    assert (handled, decision) == (False, None)
    assert bot.city_shop_transit.status == "admitted"


@pytest.mark.parametrize(
    ("need_food", "need_drink", "command"),
    [(True, False, "eat pie"), (False, True, "drink skin")],
)
def test_field_departure_consumes_carried_provisions_before_city_preflight(
    world, monkeypatch, need_food, need_drink, command,
):
    bot, state, _ = setup(world, monkeypatch)
    bot.needs_food = need_food
    bot.needs_drink = need_drink
    state = replace(
        state,
        inventory=[
            {"short_desc": "a big pot pie"},
            {"short_desc": "a buffalo water skin"},
        ],
    )
    handled, decision = bot._field_city_departure_decision(state)
    assert handled and decision.command == command


@pytest.mark.parametrize("response", [
    "You fail to find anyone by that name.",
    "You detect the presence of:\nThe drunk                    Grubby Inn",
])
def test_positive_clearance_continues_the_same_field_route(world, monkeypatch, response):
    bot, state, _ = setup(world, monkeypatch)
    locate(bot, state, response)
    assert bot._field_city_departure_decision(state) == (False, None)
    assert bot._fastwalk_research_decision(state).command == "south"
    audit = bot.field_city_preflight_checkpoint(state)["campaign_field_city_preflight"]
    assert audit["complete"] and not audit["blocked"]
    assert audit["wait_attempts"] == 0
    assert not audit["stopped_before_departure"]


def test_crowded_fountain_waits_then_rechecks_at_healer(world, monkeypatch):
    bot, state, clock = setup(world, monkeypatch)
    locate(bot, state, "You detect the presence of:\nThe drunk                    The Temple Square")
    handled, wait = bot._field_city_departure_decision(state)
    assert handled and wait.command == "sleep"
    assert bot.fastwalk_outbound_index == 0
    bot.after_command(wait)
    clock[0] += 12
    wake = bot.next_decision(replace(state, position=4))
    assert wake.command == "stand"
    bot.after_command(wake)
    bot.prompt_ready = True
    locate(bot, state, "You fail to find anyone by that name.")
    assert bot._field_city_departure_decision(state) == (False, None)
    assert not bot.magic_shop_route_blocked_by_drunk
    assert bot.city_shop_route_wait_attempts == 1


def test_persistent_fountain_hazard_saves_at_healer_after_three_waits(world, monkeypatch):
    bot, state, clock = setup(world, monkeypatch)
    for _ in range(3):
        locate(bot, state, "You detect the presence of:\nThe drunk                    The Temple Square")
        handled, wait = bot._field_city_departure_decision(state)
        assert handled and wait.command == "sleep"
        bot.after_command(wait)
        clock[0] += 12
        wake = bot.next_decision(replace(state, position=4))
        assert wake.command == "stand"
        bot.after_command(wake)
        bot.prompt_ready = True
    locate(bot, state, "You detect the presence of:\nThe drunk                    The Temple Square")
    handled, save = bot._field_city_departure_decision(state)
    assert handled and save.command == "save"
    assert bot.fastwalk_outbound_index == 0
    assert bot.city_shop_route_wait_attempts == 3
    assert "greeter/guard" in bot.fastwalk_abort_reason
    audit = bot.field_city_preflight_checkpoint(state)["campaign_field_city_preflight"]
    assert audit["stopped_before_departure"] and audit["outbound_index"] == 0


def test_missing_locator_is_not_a_clear_city(world, monkeypatch):
    bot, state, clock = setup(world, monkeypatch)
    locate(bot, state, "The healer smiles.")
    assert bot.magic_shop_drunk_preflight_pending
    clock[0] += 6
    bot.next_decision(state)
    assert bot.magic_shop_route_blocked_by_drunk


@pytest.mark.parametrize("change", ["return", "runtime", "moved", "other_room"])
def test_city_departure_never_reopens_after_its_boundary(world, monkeypatch, change):
    bot, state, _ = setup(world, monkeypatch)
    if change == "return":
        bot.fastwalk_returning = True
    elif change == "runtime":
        bot.request_runtime_boundary()
    elif change == "moved":
        bot.fastwalk_outbound_index = 1
    else:
        state = replace(state, room_vnum="3001")
    assert bot._field_city_departure_decision(state) == (False, None)


def test_hidden_alignment_cannot_discount_a_live_source_guard(world, monkeypatch):
    bot, state, _ = setup(world, monkeypatch)
    bot.source_mobile_special_profiles["ofcol cityguard"] = (("spec_guard",),)
    bot.fastwalk_crowd_retry_attempts[0] = 1
    assert not bot._source_mobile_name_is_non_assisting_bystander("ofcol cityguard", state)
