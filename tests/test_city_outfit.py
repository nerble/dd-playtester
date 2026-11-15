from copy import deepcopy

import pytest

from dd4tester.campaign import (
    _basic_gear_funding_shortfall, _basic_gear_quote_total,
    _campaign_segment_end_state,
    _campaign_segment_objective_outcome,
    _legacy_pouch_offer_needs_refresh,
)
from dd4tester.character import CharacterSpec
from dd4tester.equipment import GearCatalog
from dd4tester.hunt_candidates import ITEM_ARMOR, ITEM_CONTAINER, MobReset, ObjectSource, WorldSource
from dd4tester.equipment import ITEM_FOOD, ITEM_NODROP
from dd4tester.source_purchases import ShopCommandReply
from dd4tester.starter import StarterPolicy, _city_outfit_shop_offer, _city_outfit_shop_stock
from dd4tester.state import CharacterState


PROMPT = "<100/100 hits 40/40 mana 90/100 move [Midgaard]> "
LISTING = (
    "[Lvl Price] Item for sale\n"
    "[ 24 506] some mithril sleeves\n"
    "[ 11 233] [#2258] a pair of studded leather sleeves\n"
)


def shop_policy(coins=500):
    restricted = ObjectSource(
        5203, "sleeves mithril", "some mithril sleeves", ITEM_ARMOR,
        (3, 0, 0, 0), 24, extra_flags=64 | (1 << 10), wear_flags=257,
    )
    usable = ObjectSource(
        3071, "sleeves studded leather", "a pair of studded leather sleeves",
        ITEM_ARMOR, (2, 0, 0, 0), 11, wear_flags=257,
    )
    spec = CharacterSpec.from_mapping({
        "name": "Dorrik", "race": "dwarf", "gender": "male",
        "class": "warrior", "subclass": "knight", "title": "",
    })
    policy = StarterPolicy(spec, "test-password", city_outfit=True,
                           gear_catalog=GearCatalog({5203: restricted, 3071: usable}))
    policy.in_world = True
    policy.city_outfit_audited = True
    policy.city_outfit_route_index = 7
    policy.city_outfit_initial_empty = {"arms"}
    policy.city_outfit_plan = [("arms", "sleeves")]
    state = CharacterState(
        room_name="The Leather Shop", room_vnum="3035", position=7,
        level=45, progress={"alignment": -755}, currencies={"copper": coins},
    )
    return policy, state


def test_shop_reply_waits_for_fragments_and_stops_at_its_prompt():
    reply = ShopCommandReply()
    reply.begin("list sleeves", now=10)
    reply.observe(LISTING[:50], now=11)
    assert not reply.complete
    reply.observe(LISTING[50:] + PROMPT[:18], now=12)
    assert not reply.complete
    reply.observe(PROMPT[18:], now=13)
    assert reply.complete
    reply.observe("unrelated healer chatter", now=14)
    assert reply.response == LISTING + PROMPT
    reply.begin("list pants", now=20)
    assert reply.response == ""
    assert reply.expired(25)


def test_shop_reply_rejects_overflow_and_late_chunks():
    reply = ShopCommandReply()
    reply.begin("list sleeves", now=10)
    reply.observe("x" * 8001, now=11)
    assert reply.failure
    assert not reply.complete
    reply.begin("list sleeves", now=20)
    reply.observe(LISTING + PROMPT, now=26)
    assert reply.failure
    assert not reply.complete


def test_split_listing_selects_legal_exact_item_and_requires_purchase_ack():
    policy, state = shop_policy()
    assert policy._city_outfit_decision(state).command == "list sleeves"
    policy.observe_text(LISTING[:60])
    assert policy._city_outfit_decision(state) is None
    assert not policy.city_outfit_complete
    policy.observe_text(LISTING[60:] + PROMPT)
    assert policy._city_outfit_decision(state).command == "buy #2258"
    assert policy._city_outfit_decision(state) is None
    policy.observe_text("You buy a pair of studded leather ")
    assert policy._city_outfit_decision(state) is None
    policy.observe_text("sleeves.\n" + PROMPT)
    assert policy._city_outfit_decision(state).command == "wear sleeves"
    assert policy._city_outfit_decision(state).command == "eq all"
    policy.observe_text("<worn on arms> a pair of studded leather sleeves\n" + PROMPT)
    assert policy._city_outfit_decision(state).command == "south"
    assert policy.city_outfit_quotes[0]["outcome"] == "purchased"


def test_missing_listing_never_falls_back_to_keyword_purchase():
    policy, state = shop_policy()
    assert policy._city_outfit_decision(state).command == "list sleeves"
    assert policy._city_outfit_decision(state) is None
    policy.city_outfit_reply.deadline = 0
    assert policy._city_outfit_decision(state).command == "eq all"
    assert policy.city_outfit_deferred_categories == {"arms"}
    assert policy.city_outfit_quotes[0]["outcome"] == "incomplete-listing"


def test_unaffordable_legal_listing_records_budget_without_buying():
    policy, state = shop_policy(coins=52)
    assert policy._city_outfit_decision(state).command == "list sleeves"
    policy.observe_text(LISTING + PROMPT)
    assert policy._city_outfit_decision(state).command == "eq all"
    assert policy.city_outfit_quotes == [{
        "category": "arms", "selector": "#2258",
        "description": "a pair of studded leather sleeves", "price": 233,
        "coins": 52, "outcome": "funding-required",
    }]


def test_refusal_does_not_become_a_purchase_or_wear_command():
    policy, state = shop_policy()
    assert policy._city_outfit_decision(state).command == "list sleeves"
    policy.observe_text(LISTING + PROMPT)
    assert policy._city_outfit_decision(state).command == "buy #2258"
    policy.observe_text("You can't carry that many items.\n" + PROMPT)
    assert policy._city_outfit_decision(state).command == "eq all"
    assert not policy.city_outfit_purchased_categories
    assert policy.city_outfit_quotes[0]["outcome"] == "purchase-unconfirmed"


def funded_state():
    return {
        "level": 45, "world_boot_id": "boot", "currencies": {"copper": 52},
        "campaign_empty_equipment_categories": ["arms", "legs"],
        "campaign_city_outfit": {
            "revision": 2, "level": 45, "boot_id": "boot", "complete": True,
            "room_vnum": "3054", "failure": None,
            "quotes": [
                {"category": "arms", "price": 233, "outcome": "funding-required"},
                {"category": "legs", "price": 186, "outcome": "funding-required"},
            ],
        },
    }


def test_outfit_budget_counts_only_still_empty_slots_and_current_quotes():
    state = funded_state()
    assert _basic_gear_quote_total(state) == 419
    assert _basic_gear_funding_shortfall(state) == 367
    state["campaign_empty_equipment_categories"] = ["legs"]
    assert _basic_gear_funding_shortfall(state) == 134
    state["currencies"] = {"gold": 5}
    assert _basic_gear_funding_shortfall(state) == 0
    state["world_boot_id"] = "new-boot"
    assert _basic_gear_quote_total(state) == 0
    state["world_boot_id"] = "boot"
    state["campaign_city_outfit"]["failure"] = "interrupted"
    assert _basic_gear_quote_total(state) == 0


def test_outfit_quote_survives_an_unrelated_funding_segment():
    previous = funded_state()
    current = deepcopy(previous)
    current.pop("campaign_city_outfit")
    merged = _campaign_segment_end_state(previous, current, execution="provision-funding")
    assert merged["campaign_city_outfit"] == previous["campaign_city_outfit"]


def test_safe_shopping_return_does_not_mean_missing_slots_were_filled():
    state = funded_state()
    state["campaign_city_outfit"]["initial_empty"] = ["arms", "legs"]
    assert _campaign_segment_objective_outcome(
        "outfit-basic-gear", (), final_state=state,
    ) == ("not_achieved", True)
    state["campaign_empty_equipment_categories"] = []
    assert _campaign_segment_objective_outcome(
        "outfit-basic-gear", (), final_state=state,
    ) == ("achieved", True)


def test_outfit_enables_shared_capacity_preflight_and_reserves_food():
    policy, _ = shop_policy()
    assert not policy.fastwalk_required_loot_capacity_preflight_complete
    pie = ObjectSource(3009, "potpie pie", "a big pot pie", ITEM_FOOD, (10, 0, 0, 0), 1)
    policy.gear_catalog = GearCatalog({3009: pie})
    healer = CharacterState(
        level=45, room_vnum="3054", position=7,
        hunger=40, max_hunger=48,
        inventory=[[{"short_desc": "a big pot pie", "quan": "5"}]],
        stats={"carry_num": 37, "maxcarry_num": 37},
    )
    owned, decision = policy._healer_carrying_capacity_preflight_decision(healer, required_slots=2)
    assert owned and decision.command == "eat potpie"
    policy.observe_text("You eat a big pot pie.\n" + PROMPT)
    assert policy._healer_carrying_capacity_preflight_decision(healer, required_slots=2)[1].command == "inventory"
    healer.stats["carry_num"] = 36
    healer.inventory = [[{"short_desc": "a big pot pie", "quan": "4"}]]
    policy.observe_text("Your backpack contains:\na big pot pie\nYou are carrying 36/37 items.\n" + PROMPT)
    owned, decision = policy._healer_carrying_capacity_preflight_decision(healer, required_slots=2)
    assert owned and decision.command.startswith("drop ")
    assert policy._recovery_session.carrying_capacity.food_disposals == 1
    assert policy._recovery_session.carrying_capacity.limit == 1


@pytest.mark.parametrize("wear_flags,item_type,extra_flags,accepted", [
    (65537, ITEM_CONTAINER, 0, True),
    (1, ITEM_CONTAINER, 0, False),
    (65537, ITEM_FOOD, 0, False),
    (65537, ITEM_CONTAINER, ITEM_NODROP, False),
])
def test_source_wearable_pouch_is_a_shop_basic_not_an_ordinary_container(
    wear_flags, item_type, extra_flags, accepted,
):
    pouch = ObjectSource(
        3370, "beltpouch belt pouch", "a small leather pouch", item_type,
        (9, 0, -1, 0), 0, wear_flags=wear_flags, extra_flags=extra_flags,
    )
    offer = _city_outfit_shop_offer(
        "[Lvl Price] Item for sale\n[ 0 50] [#2252] a small leather pouch\n",
        category="pouch", keyword="pouch", gear_catalog=GearCatalog({3370: pouch}),
        character_class="warrior", subclass="knight", character_alignment=0,
        max_level=46,
    )
    assert offer == (("#2252", "a small leather pouch", 50) if accepted else None)


def test_wearable_pouch_still_requires_unique_source_identity():
    pouch = ObjectSource(3370, "pouch", "a small leather pouch", ITEM_CONTAINER,
                         (9, 0, -1, 0), 0, wear_flags=65537)
    other = ObjectSource(9999, "pouch", "a small leather pouch", ITEM_CONTAINER,
                         (9, 0, -1, 0), 0, wear_flags=65537)
    assert _city_outfit_shop_offer(
        "[ 0 50] [#2252] a small leather pouch\n", category="pouch", keyword="pouch",
        gear_catalog=GearCatalog({3370: pouch, 9999: other}),
        character_class="warrior", subclass="knight", character_alignment=0, max_level=46,
    ) is None


def test_shop_source_reset_resolves_unrelated_pouch_namesakes_not_live_ids():
    pouch = ObjectSource(3370, "pouch", "a small leather pouch", ITEM_CONTAINER,
                         (9, 0, -1, 0), 0, wear_flags=65537)
    other = ObjectSource(9999, "pouch", "a small leather pouch", ITEM_CONTAINER,
                         (9, 0, -1, 0), 0, wear_flags=65537)
    world = WorldSource(shopkeepers={3010}, mob_resets=[MobReset(3010, 3035, 1, (3370,))])
    stock = _city_outfit_shop_stock(world, "3035")
    assert stock == frozenset({3370})
    args = dict(category="pouch", keyword="pouch",
                gear_catalog=GearCatalog({3370: pouch, 9999: other}),
                character_class="warrior", subclass="knight", character_alignment=0,
                max_level=46)
    listing = "[ 0 50] [#2252] a small leather pouch\n"
    assert _city_outfit_shop_offer(listing, source_stock_vnums=stock, **args) == (
        "#2252", "a small leather pouch", 50,
    )
    assert _city_outfit_shop_offer(listing, source_stock_vnums={3370, 9999}, **args) is None
    assert _city_outfit_shop_offer(listing, source_stock_vnums=set(), **args) is None
    assert _city_outfit_shop_stock(world, "3007") == frozenset()
    world.mob_resets.append(MobReset(3010, 3035, 1, (9999,)))
    assert _city_outfit_shop_stock(world, "3035") == frozenset()


def test_legacy_pouch_false_refusal_gets_only_one_corrected_completed_visit():
    state = {"campaign_empty_equipment_categories": ["pouch"],
             "campaign_city_outfit": {"complete": True, "room_vnum": "3054", "quotes": [
                 {"category": "pouch", "outcome": "no-legal-offer"},
             ]}}
    assert _legacy_pouch_offer_needs_refresh(state)
    state["campaign_city_outfit"]["shop_stock_identity_revision"] = 1
    assert not _legacy_pouch_offer_needs_refresh(state)
    state["campaign_city_outfit"].pop("shop_stock_identity_revision")
    state["campaign_empty_equipment_categories"] = []
    assert not _legacy_pouch_offer_needs_refresh(state)
    state["campaign_empty_equipment_categories"] = ["pouch"]
    state["campaign_city_outfit"]["quotes"][0]["outcome"] = "purchase-unconfirmed"
    assert not _legacy_pouch_offer_needs_refresh(state)
