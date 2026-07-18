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


def test_sale_keyword_uses_the_distinctive_final_noun() -> None:
    assert sale_keyword("a metal buckler") == "buckler"
    assert sale_keyword("[-?-] a spiked metal rod") == "rod"


def test_unknown_item_is_not_sent_to_an_incompatible_shop() -> None:
    assert safe_shop_for_item("a buffalo water skin") is None
