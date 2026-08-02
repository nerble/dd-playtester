from dd4tester.shops import safe_shop_for_item, sale_keyword


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
