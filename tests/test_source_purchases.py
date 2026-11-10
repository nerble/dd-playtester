from dataclasses import replace
from types import SimpleNamespace

import pytest

from dd4tester.hunt_candidates import (
    ACT_AGGRESSIVE, ACT_SENTINEL, AFF_DETECT_INVIS, ExitSource, MobileProgram,
    MobileSource, MobReset, ObjectSource, RoomSource, WorldSource,
    source_invisibility_blocks_mobile_aggression,
)
from dd4tester.source_purchases import (
    ROUTE_INVISIBILITY_SUPPLY_KEY,
    TRAINING_TRAVEL_SUPPLY_KEY, SourceLiquidation, SourceLiquidationSession,
    SourcePurchase, SourcePurchaseSession,
    route_invisibility_supply,
    training_travel_supply,
)


PROMPT = "<100/100 hits 40/40 mana 90/100 move [Town]> "
PLAN = SourcePurchase(9231, 9238, 9203, "anti-cyclops elixir", "elixir", 100)


def step(session, now=1.0, **changes):
    values = dict(room_vnum="9203", level=26, coins=500, inventory=(), now=now)
    values.update(changes)
    return session.next_command(**values)


def test_purchase_uses_live_price_selector_and_confirmed_inventory_gain():
    session = SourcePurchaseSession(PLAN)
    assert step(session) == "list elixir"
    session.observe("[Lvl Price] Item for sale\n[2 27] [#123] anti-cyclops ")
    assert step(session, 2) is None
    session.observe("elixir\n" + PROMPT)
    assert step(session, 3) == "buy #123"
    assert session.price == 27
    session.observe("You buy anti-cyclops elixir.\n" + PROMPT)
    assert step(session, 4) == "inventory"
    session.observe("You are carrying:\n[#456] anti-cyclops elixir\n" + PROMPT)
    assert step(session, 5, inventory=(("anti-cyclops elixir", "#456"),)) is None
    assert session.stage == "complete"
    assert step(session, 6) is None


def test_purchase_records_capacity_rejection_separately_from_missing_ack():
    session = SourcePurchaseSession(PLAN)
    assert step(session) == "list elixir"
    session.observe("[Lvl Price] Item for sale\n[2 27] [#123] anti-cyclops elixir\n" + PROMPT)
    assert step(session, 2) == "buy #123"
    session.observe("You can't carry that many items.\n" + PROMPT)
    assert step(session, 3) is None
    assert session.stage == "failed"
    assert session.failure == (
        "shop rejected purchase because carrying capacity was full"
    )


def test_purchase_can_fund_one_live_price_with_confirmed_redundant_sale():
    session = SourcePurchaseSession(PLAN)
    funding = ("a spare cloak", "#777", 777)
    assert step(session, coins=20, inventory=(("a spare cloak", "#777"),)) == "list elixir"
    session.observe("[2 27] [#123] anti-cyclops elixir\n" + PROMPT)
    assert step(
        session,
        now=2,
        coins=20,
        inventory=(("a spare cloak", "#777"),),
        funding_item=funding,
    ) == "value #777"
    session.observe("The vendor tells you 'I'll give you 200 coins for a spare cloak'.\n" + PROMPT)
    assert step(session, now=3, coins=20, inventory=(("a spare cloak", "#777"),)) == "sell #777"
    session.observe("You sell a spare cloak for 200 coins.\n" + PROMPT)
    assert step(session, now=4, coins=220, inventory=(("a spare cloak", "#777"),)) == "inventory"
    session.observe("You are carrying:\n" + PROMPT)
    assert step(session, now=5, coins=220, inventory=()) == "list elixir"
    session.observe("[2 27] [#123] anti-cyclops elixir\n" + PROMPT)
    assert step(session, now=6, coins=220, inventory=()) == "buy #123"
    session.observe("You buy anti-cyclops elixir.\n" + PROMPT)
    assert step(session, now=7, coins=193, inventory=()) == "inventory"
    session.observe("You are carrying:\n[#456] anti-cyclops elixir\n" + PROMPT)
    assert step(session, now=8, coins=193, inventory=(("anti-cyclops elixir", "#456"),)) is None
    assert session.stage == "complete"
    assert session.funding_attempts == 1


def test_liquidation_requires_exact_value_sale_and_inventory_receipts():
    session = SourceLiquidationSession(
        SourceLiquidation(27233, 9203, (5,), maximum_items=1)
    )
    item = ("one-eyed whip", "#777", 777)
    assert session.next_command(
        room_vnum="9203", inventory=(item[:2],), now=1, funding_item=item
    ) == "value #777"
    session.observe(
        "Ahomar tells you 'I'll give you 250 coins for one-eyed whip'.\n"
        + PROMPT
    )
    assert session.next_command(
        room_vnum="9203", inventory=(item[:2],), now=2
    ) == "sell #777"
    session.observe("You sell one-eyed whip for 250 coins.\n" + PROMPT)
    assert session.next_command(
        room_vnum="9203", inventory=(item[:2],), now=3
    ) == "inventory"
    session.observe("You are carrying:\n" + PROMPT)
    assert session.next_command(room_vnum="9203", inventory=(), now=4) is None
    assert session.stage == "complete"
    assert session.funding_item_vnums == (777,)


def test_liquidation_room_identity_and_sale_name_are_fail_closed():
    session = SourceLiquidationSession(
        SourceLiquidation(27233, 9203, (5,), maximum_items=1)
    )
    assert session.next_command(
        room_vnum="9204", inventory=(), now=1,
        funding_item=("one-eyed whip", "#777", 777),
    ) is None
    assert session.stage == "failed"

    session = SourceLiquidationSession(
        SourceLiquidation(27233, 9203, (5,), maximum_items=1)
    )
    item = ("one-eyed whip", "#777", 777)
    assert session.next_command(
        room_vnum="9203", inventory=(item[:2],), now=1, funding_item=item
    ) == "value #777"
    session.observe("Ahomar tells you 'I'll give you 250 coins for a different item'.\n" + PROMPT)
    assert session.next_command(
        room_vnum="9203", inventory=(item[:2],), now=2
    ) is None
    assert session.stage == "failed"


def test_liquidation_can_start_the_next_item_after_inventory_confirmation():
    session = SourceLiquidationSession(
        SourceLiquidation(27233, 9203, (5,), maximum_items=2)
    )
    first = ("one-eyed whip", "#777", 777)
    second = ("standard issue mace", "#778", 778)
    assert session.next_command(
        room_vnum="9203", inventory=(first[:2], second[:2]), now=1,
        funding_item=first,
    ) == "value #777"
    session.observe("Ahomar tells you 'I'll give you 78 coins for one-eyed whip'.\n" + PROMPT)
    assert session.next_command(
        room_vnum="9203", inventory=(first[:2], second[:2]), now=2
    ) == "sell #777"
    session.observe("You sell one-eyed whip for 78 coins.\n" + PROMPT)
    assert session.next_command(
        room_vnum="9203", inventory=(first[:2], second[:2]), now=3
    ) == "inventory"
    session.observe("You are carrying:\nstandard issue mace\n" + PROMPT)
    assert session.next_command(
        room_vnum="9203", inventory=(second[:2],), now=4
    ) is None
    assert session.stage == "new"
    assert session.next_command(
        room_vnum="9203", inventory=(second[:2],), now=4,
        funding_item=second,
    ) == "value #778"


@pytest.mark.parametrize("offer", [
    "[2 101] [#123] anti-cyclops elixir",
    "[27 20] [#123] anti-cyclops elixir",
    "[2 20] anti-cyclops elixir",
    "[2 20] [#123] a different potion",
    "[2 20] [#123] anti-cyclops elixir\n[2 20] [#456] anti-cyclops elixir",
])
def test_ambiguous_or_unusable_offers_do_not_buy(offer):
    session = SourcePurchaseSession(PLAN)
    step(session)
    session.observe(offer + "\n" + PROMPT)
    assert step(session, 2) is None
    assert session.failure and session.stage == "failed"


def test_live_balance_preserves_coin_reserve():
    session = SourcePurchaseSession(PLAN)
    step(session)
    session.observe("[2 27] [#123] anti-cyclops elixir\n" + PROMPT)
    assert step(session, 2, coins=126) is None
    assert session.stage == "failed"
    assert session.price == 27
    assert session.selector == "#123"


def test_incomplete_quote_times_out_without_buying():
    session = SourcePurchaseSession(PLAN)
    step(session, 1)
    session.observe("[2 27] [#123] anti-cyclops elixir\n")
    assert session.expire(6)
    session.observe(PROMPT)
    assert step(session, 7) is None
    assert session.stage == "failed"


def test_one_visibility_attempt_cannot_loop():
    session = SourcePurchaseSession(PLAN)
    assert step(session, invisible=True) == "vis"
    session.observe("Ok.\n" + PROMPT)
    assert step(session, 2, invisible=True) is None
    assert session.stage == "failed"


def test_purchase_acknowledgement_alone_does_not_prove_acquisition():
    session = SourcePurchaseSession(PLAN)
    step(session, inventory=(("anti-cyclops elixir", "#old"),))
    session.observe("[2 27] [#123] anti-cyclops elixir\n" + PROMPT)
    step(session, 2)
    session.observe("You buy anti-cyclops elixir.\n" + PROMPT)
    assert step(session, 3) == "inventory"
    session.observe(PROMPT)
    step(session, 4, inventory=(("anti-cyclops elixir", "#old"),))
    assert session.stage == "failed"


def test_purchase_room_change_fails_closed():
    session = SourcePurchaseSession(PLAN)
    assert step(session, room_vnum="9204") is None
    assert session.stage == "failed"


def equipped_world():
    mobile = MobileSource(1, "rock", "a rolling rock", 15, ACT_AGGRESSIVE, 0, "field.are")
    item = ObjectSource(2, "rock", "a rock", 5, (0, 1, 6, 8), 0)
    return WorldSource(mobiles={1: mobile}, objects={2: item},
                       mob_resets=[MobReset(1, 10, 1, (2,), ((16, 2),))])


def test_known_ordinary_equipment_does_not_grant_detection():
    assert not source_invisibility_blocks_mobile_aggression(equipped_world(), 1)
    assert source_invisibility_blocks_mobile_aggression(equipped_world(), 1, audit_equipment=True)


@pytest.mark.parametrize("hazard", ["detecting-gear", "missing-gear", "detecting-mobile", "program", "unknown-special"])
def test_invisibility_does_not_bypass_detection_or_unknown_sources(hazard):
    world = equipped_world()
    if hazard == "detecting-gear":
        world.objects[2] = replace(world.objects[2], affects=((29, 1),))
    elif hazard == "missing-gear":
        world.objects.clear()
    elif hazard == "detecting-mobile":
        world.mobiles[1] = replace(world.mobiles[1], affected_flags=AFF_DETECT_INVIS)
    elif hazard == "program":
        world.mobiles[1] = replace(world.mobiles[1], programs=(MobileProgram("greet_prog", "10", ("mpkill $n",)),))
    else:
        world.mobile_specials[1] = ("spec_unknown",)
    assert not source_invisibility_blocks_mobile_aggression(world, 1, audit_equipment=True)


@pytest.fixture
def supply_state(monkeypatch):
    item = ObjectSource(9231, "elixir anti", "anti-cyclops elixir", 10, (15,), 10,
                        value_strings=("15", "invis", "", ""), weight=1)
    world = WorldSource(
        rooms={3001: RoomSource(3001, "Temple", "city.are", {"east": ExitSource("east", 9203, 0, -1)}),
               9203: RoomSource(9203, "Shop", "field.are")},
        mobiles={9238: MobileSource(9238, "vendor", "the vendor", 130, ACT_SENTINEL, 900, "field.are"),
                 50: MobileSource(50, "captain", "the captain", 40, ACT_SENTINEL, 0, "field.are", teachings=(("dodge", 80),))},
        objects={9231: item}, shopkeepers={9238}, mob_resets=[MobReset(9238, 9203, 1, (9231,))],
    )
    teacher = SimpleNamespace(steps=(("3001", "west", "99"),), mobile_vnum=50, room_vnum=99)
    monkeypatch.setattr("dd4tester.source_purchases.source_class_teacher_route_for_level", lambda *a: teacher)
    monkeypatch.setattr("dd4tester.source_purchases.source_route_hazard_rejections",
                        lambda w, rooms, **kw: ("aggressor",) if 99 in rooms and not kw.get("invisible") else ())
    state = {
        "level": 26, "world_boot_id": "boot", "room_vnum": "3054", "hp": 500, "max_hp": 500, "max_move": 300,
        "stats": {"fame": 0, "str": 26, "int": 12, "dex": 16, "carry_num": 1, "maxcarry_num": 10, "carry_wt": 2, "maxcarry_wt": 100},
        "progress": {"gold": 5},
        "campaign_training_audit": {"observed": True, "level": 26, "boot_id": "boot", "known_skill_levels": {"dodge": 49},
                                    "learnable_skill_levels": {}, "physical_practices": 2},
        "campaign_training_deficit_repair": {"attempted": True, "level": 26, "boot_id": "boot"},
    }
    return world, state


def test_supply_requires_useful_lesson_and_distinct_persisted_attempt(supply_state):
    world, state = supply_state
    plan = training_travel_supply(world, state, "warrior")
    assert plan is not None and plan.purchase.object_vnum == 9231
    assert plan.useful_skills == ("dodge",)
    state[TRAINING_TRAVEL_SUPPLY_KEY] = {"level": 26, "boot_id": "boot", "status": "attempted"}
    assert training_travel_supply(world, state, "warrior") is None


def test_carried_supply_or_spent_practices_do_not_trigger_a_purchase(supply_state):
    world, state = supply_state
    assert training_travel_supply(world, state, "warrior", carried_descriptions=("anti-cyclops elixir",)) is None
    state["campaign_training_audit"]["physical_practices"] = 0
    assert training_travel_supply(world, state, "warrior") is None


def test_legacy_unbought_quote_reopens_once_with_reserved_live_budget(supply_state):
    world, state = supply_state
    old = {"level": 26, "boot_id": "boot", "status": "attempted", "maximum_price": 100,
           "object_vnum": 9231, "shopkeeper_vnum": 9238, "room_vnum": 9203}
    state[TRAINING_TRAVEL_SUPPLY_KEY] = old
    state["campaign_source_purchases"] = [{
        "object_vnum": 9231, "shopkeeper_vnum": 9238, "room_vnum": 9203,
        "stage": "failed", "price": None,
        "failure": "no single affordable, level-usable exact shop offer",
    }]
    plan = training_travel_supply(world, state, "warrior")
    assert plan is not None and plan.purchase.maximum_price == 400
    state[TRAINING_TRAVEL_SUPPLY_KEY] = {**old, **plan.evidence()}
    assert training_travel_supply(world, state, "warrior") is None


@pytest.mark.parametrize("change", [
    {"stage": "complete"}, {"price": 20}, {"object_vnum": 999},
    {"failure": "shop room identity changed"},
])
def test_other_purchase_outcomes_do_not_reopen_a_legacy_attempt(supply_state, change):
    world, state = supply_state
    state[TRAINING_TRAVEL_SUPPLY_KEY] = {
        "level": 26, "boot_id": "boot", "maximum_price": 100,
        "object_vnum": 9231, "shopkeeper_vnum": 9238, "room_vnum": 9203,
    }
    state["campaign_source_purchases"] = [{
        "object_vnum": 9231, "shopkeeper_vnum": 9238, "room_vnum": 9203,
        "stage": "failed", "price": None,
        "failure": "no single affordable, level-usable exact shop offer", **change,
    }]
    assert training_travel_supply(world, state, "warrior") is None


def test_route_invisibility_supply_accepts_source_potion_and_safe_vendor_special(
    monkeypatch,
):
    item = ObjectSource(
        19021,
        "potion invisibility",
        "a clear potion of invisibility",
        10,
        (15,),
        10,
        value_strings=("20", "invis", "detect magic", ""),
        weight=1,
    )
    world = WorldSource(
        rooms={
            3001: RoomSource(
                3001,
                "Temple",
                "city.are",
                {"east": ExitSource("east", 19070, 0, -1)},
            ),
            19070: RoomSource(19070, "Mirror shop", "mirror.are"),
        },
        mobiles={
            19024: MobileSource(
                19024,
                "wizard",
                "a standard issue wizard",
                130,
                ACT_SENTINEL,
                900,
                "mirror.are",
            ),
        },
        objects={19021: item},
        shopkeepers={19024},
        mob_resets=[MobReset(19024, 19070, 1, (19021,))],
    )
    world.mobile_specials[19024] = ("spec_cast_mage",)
    monkeypatch.setattr(
        "dd4tester.source_purchases.source_route_hazard_rejections",
        lambda *args, **kwargs: (),
    )
    state = {
        "level": 45,
        "world_boot_id": "boot",
        "room_vnum": "3054",
        "hp": 1098,
        "max_hp": 1098,
        "currencies": {
            "copper": 50,
            "silver": 0,
            "gold": 0,
            "platinum": 0,
        },
    }

    plan = route_invisibility_supply(world, state)

    assert plan is not None
    assert plan.purchase.object_vnum == 19021
    assert plan.purchase.shopkeeper_vnum == 19024
    assert plan.commands == ("east",)
    assert plan.required_move > 0
    state[ROUTE_INVISIBILITY_SUPPLY_KEY] = {
        "boot_id": "boot",
        "level": 45,
        "status": "attempted",
    }
    assert route_invisibility_supply(world, state) is None


def test_route_invisibility_supply_rejects_unknown_vendor_special(monkeypatch):
    item = ObjectSource(
        19021,
        "potion invisibility",
        "a clear potion of invisibility",
        10,
        (15,),
        10,
        value_strings=("20", "invis", "detect magic", ""),
        weight=1,
    )
    world = WorldSource(
        rooms={
            3001: RoomSource(
                3001,
                "Temple",
                "city.are",
                {"east": ExitSource("east", 19070, 0, -1)},
            ),
            19070: RoomSource(19070, "Mirror shop", "mirror.are"),
        },
        mobiles={
            19024: MobileSource(
                19024,
                "wizard",
                "a standard issue wizard",
                130,
                ACT_SENTINEL,
                900,
                "mirror.are",
            ),
        },
        objects={19021: item},
        shopkeepers={19024},
        mob_resets=[MobReset(19024, 19070, 1, (19021,))],
    )
    world.mobile_specials[19024] = ("spec_unknown",)
    monkeypatch.setattr(
        "dd4tester.source_purchases.source_route_hazard_rejections",
        lambda *args, **kwargs: (),
    )
    state = {
        "level": 45,
        "world_boot_id": "boot",
        "room_vnum": "3054",
        "hp": 1098,
        "max_hp": 1098,
        "currencies": {"copper": 50},
    }

    assert route_invisibility_supply(world, state) is None
