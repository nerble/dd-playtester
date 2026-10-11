import json

import pytest

from dd4tester.campaign import _sale_rejections_from_run
from dd4tester.character import CharacterSpec
from dd4tester.equipment import GearCatalog
from dd4tester.hunt_candidates import ObjectSource
from dd4tester.report import _sale_rejections_from_events
from dd4tester.shops import SALE_REJECTION_LINE, safe_shop_for_item
from dd4tester.starter import StarterPolicy
from dd4tester.state import CharacterState


@pytest.mark.parametrize("item", ["an I.Q. Vine", "a patched leather jerkin", "a St. John's ring"])
def test_shop_refusal_preserves_internal_full_stops(item: str) -> None:
    match = SALE_REJECTION_LINE.search(f"The leather worker looks uninterested in {item}.\n")
    assert match is not None
    assert match.group("shop") == "The leather worker"
    assert match.group("item") == item


@pytest.mark.parametrize("reply", [
    "The leather worker looks uninterested in an I.Q. Vine",
    "The leather worker looks uninterested in an I.Q.",
    "The leather worker looks uninterested in\nan I.Q. Vine.\n",
    "The leather worker looks uninterested in an I.Q. Vine. extra chatter\n",
    "You sell an I.Q. Vine for 5 coins.\n",
])
def test_only_complete_refusal_lines_close_a_sale(reply: str) -> None:
    assert SALE_REJECTION_LINE.search(reply) is None


@pytest.mark.parametrize("phase", ["sell", "inventory"])
def test_dotted_item_refusal_skips_remaining_copies_at_that_buyer(phase: str) -> None:
    item = ObjectSource(1, "iq vine", "an I.Q. Vine", 9, (0, 0, 0, 0), 50)
    spec = CharacterSpec.from_mapping({
        "name": "SaleTest", "race": "dwarf", "gender": "female",
        "class": "warrior", "subclass": None, "title": "",
    })
    policy = StarterPolicy(spec, "test-password", liquidate_loot=True,
                           gear_catalog=GearCatalog({item.vnum: item}))
    shop = safe_shop_for_item(item.short_description, item_type=item.item_type)
    assert shop is not None and shop.name == "Leather Shop"
    policy.sale_plan = [("vine", shop)] * 3
    policy.sale_phase = phase

    policy.observe_text("The leather worker looks uninterested in an I.Q. Vine.\n")

    assert policy.sale_phase == "home"
    assert policy.sale_plan[0] == ("vine", shop)
    assert len(policy.sale_plan) == 4
    assert all(buyer.name == "Armoury" for _, buyer in policy.sale_plan[1:])
    assert policy.sale_rejections[0]["item_description"] == "an I.Q. Vine"
    assert policy.sale_rejections[0]["reason"] == "compatible shop offered zero coins"
    assert policy.sale_identified_values == {"vine": 0}
    assert policy.completed_sales == []

    policy.sale_index = 1
    policy.sale_phase = phase
    policy.observe_text("The armourer looks uninterested in an I.Q. Vine.\n")

    assert policy.sale_phase == "inventory"
    assert policy.donation_plan == ["vine"] * 3
    assert policy.completed_sales == []
    assert len(policy.sale_rejections) == 2


def test_saved_refusal_and_report_use_the_same_dotted_item_evidence() -> None:
    payload = {"text": "The leather worker looks uninterested in an I.Q. Vine.\n"}

    class SavedRun:
        def list_events(self, run_id: int) -> list[dict]:
            assert run_id == 1
            return [{"kind": "response", "payload_json": json.dumps(payload)}] * 2

    expected = [{
        "item_description": "an I.Q. Vine", "shopkeeper": "The leather worker",
        "reason": "shopkeeper refused item",
    }]
    assert _sale_rejections_from_run(SavedRun(), 1) == expected
    assert _sale_rejections_from_events([{"kind": "response", "payload": payload}] * 2) == expected


def _pending_sale() -> StarterPolicy:
    spec = CharacterSpec.from_mapping({
        "name": "SaleTest", "race": "dwarf", "gender": "female",
        "class": "warrior", "subclass": None, "title": "",
    })
    policy = StarterPolicy(spec, "test-password", liquidate_loot=True)
    shop = safe_shop_for_item("an I.Q. Vine", item_type=9)
    assert shop is not None
    policy.sale_plan = [("vine", shop)]
    policy.sale_phase = "sell"
    return policy


def test_split_dotted_refusal_waits_for_the_complete_line() -> None:
    policy = _pending_sale()
    policy.observe_text("The leather worker looks uninterested in an I.Q.")
    assert policy.sale_rejections == []
    assert policy.sale_phase == "sell"

    policy.observe_text(" Vine.\n")
    assert policy.sale_rejections[0]["item_description"] == "an I.Q. Vine"
    assert policy._recovery_session.sale_reply_buffer == ""


def test_next_sale_command_cannot_reuse_an_old_partial_refusal() -> None:
    policy = _pending_sale()
    policy.observe_text("The leather worker looks uninterested in ")
    decision = policy._liquidate_loot_decision(CharacterState(room_vnum="3035"))
    assert decision is not None and decision.command == "sell vine"
    assert policy._recovery_session.sale_reply_buffer == ""
    policy.observe_text("an I.Q. Vine.\n")
    assert policy.sale_rejections == []


def test_sale_reply_buffer_remains_bounded() -> None:
    policy = _pending_sale()
    policy.observe_text("x" * 3000)
    assert len(policy._recovery_session.sale_reply_buffer) == 2048
    assert policy.sale_rejections == []
