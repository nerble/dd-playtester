from pathlib import Path

from dd4tester.hunt_candidates import parse_area_file
from dd4tester.shops import SAFE_MIDGAARD_SHOPS, safe_shop_for_item, sale_keyword


def _follow_source_route(area, start: int, route: tuple[str, ...]) -> int:
    room_vnum = start
    for direction in route:
        exit_source = area.rooms[room_vnum].exits[direction]
        room_vnum = exit_source.destination
    return room_vnum


def test_safe_shop_routes_reach_their_source_rooms() -> None:
    area = parse_area_file(
        Path(__file__).resolve().parents[1]
        / "runs/dd4-source/server/area/midgaard.are",
        include_resets=False,
        include_entities=True,
        include_objects=False,
    )

    seen: set[tuple[str, str]] = set()
    for shop in SAFE_MIDGAARD_SHOPS:
        identity = (shop.name, shop.room_vnum)
        if identity in seen:
            continue
        seen.add(identity)
        assert _follow_source_route(area, 3054, shop.route_from_healer) == int(
            shop.room_vnum
        )
        assert _follow_source_route(
            area,
            3019,
            shop.route_from_mage_lab,
        ) == int(shop.room_vnum)


def test_safe_shop_selection_prefers_margin_within_verified_safe_routes() -> None:
    armour = safe_shop_for_item("a metal buckler")
    weapon = safe_shop_for_item("[-?-] a spiked metal rod")

    assert armour is not None
    assert armour.name == "Leather Shop"
    assert armour.payout_percent == 90
    assert weapon is not None
    assert weapon.name == "Weapon Shop"
    assert weapon.payout_percent == 40


def test_safe_shop_selection_accounts_for_recorded_duplicate_penalties() -> None:
    shop = safe_shop_for_item(
        "a metal buckler",
        {("buckler", "Leather Shop"): 1},
    )

    assert shop is not None
    assert shop.name == "Armoury"


def test_safe_shop_selection_can_exclude_a_refusing_shop() -> None:
    shop = safe_shop_for_item(
        "some leather leg guards",
        item_type=9,
        excluded_shop_rooms={"3035"},
    )

    assert shop is not None
    assert shop.name == "Armoury"
    assert shop.room_vnum == "3020"


def test_foundry_item_descriptions_are_classified() -> None:
    pipe_shop = safe_shop_for_item("a length of metal piping")
    guards_shop = safe_shop_for_item("a pair of leather leg guards")

    assert pipe_shop is not None
    assert pipe_shop.name == "Weapon Shop"
    assert guards_shop is not None
    assert guards_shop.name == "Leather Shop"
    assert safe_shop_for_item("a steel barrel-helm") is not None


def test_empty_purse_uses_the_safe_general_store_container_buyer() -> None:
    shop = safe_shop_for_item("the midget's purse")

    assert shop is not None
    assert shop.name == "General Store"
    assert shop.room_vnum == "3010"
    assert shop.payout_percent == 40
    assert shop.route_from_mage_lab == (
        "west",
        "north",
        "north",
        "east",
        "east",
        "east",
        "north",
    )
    assert shop.route_from_healer == (
        "south",
        "south",
        "south",
        "east",
        "north",
    )
    assert "3019" not in shop.route_from_healer
    assert shop.route_to_healer == tuple(
        {"north": "south", "south": "north", "east": "west", "west": "east"}[step]
        for step in reversed(shop.route_from_healer)
    )


def test_sale_keyword_uses_the_distinctive_final_noun() -> None:
    assert sale_keyword("a metal buckler") == "buckler"
    assert sale_keyword("[-?-] a spiked metal rod") == "rod"


def test_unknown_item_is_not_sent_to_an_incompatible_shop() -> None:
    assert safe_shop_for_item("a buffalo water skin") is None


def test_source_item_type_overrides_name_based_shop_guess() -> None:
    shop = safe_shop_for_item("a silver circlet", item_type=8)

    assert shop is not None
    assert shop.name == "Jeweller"
    assert shop.room_vnum == "3034"
    assert shop.payout_percent == 50
    assert shop.route_from_healer == (
        "south",
        "south",
        "south",
        "east",
        "south",
    )
    assert shop.route_from_mage_lab == (
        "west",
        "north",
        "north",
        "east",
        "east",
        "east",
        "south",
    )


def test_safe_magic_and_food_buyers_cover_aruncus_drops() -> None:
    scroll_shop = safe_shop_for_item(
        "a scroll titled 'jhyfrdow'",
        item_type=2,
    )
    ivy_shop = safe_shop_for_item(
        "a small dusk of poison ivy",
        item_type=19,
    )

    assert scroll_shop is not None
    assert scroll_shop.name == "Magic Shop"
    assert scroll_shop.room_vnum == "3033"
    assert scroll_shop.route_from_mage_lab == (
        "west",
        "north",
        "north",
        "north",
    )
    assert ivy_shop is not None
    assert ivy_shop.name == "General Store"
    assert ivy_shop.room_vnum == "3010"


def test_exhausted_duplicate_value_is_not_routed_to_a_shop() -> None:
    shop = safe_shop_for_item(
        "a length of metal piping",
        {("piping", "Weapon Shop"): 4},
        item_type=5,
        item_value=28,
    )

    assert shop is None
