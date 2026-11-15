import json
from types import SimpleNamespace

import pytest

from dd4tester.banking import BANK_RESERVE_HANDOFF_KEY, bank_reserve_receipt
from dd4tester.campaign import CampaignRunner, _PROVISION_FUNDING_POLICY


def event(kind, payload, event_id=1):
    return {"id": event_id, "kind": kind, "payload_json": json.dumps(payload)}


def reply(text, event_id=2):
    return event("response", {"text": text}, event_id)


def visit(segment_id=1, **changes):
    return {"id": segment_id, "phase": "bank-excess-coins", "status": "success",
            "run_id": 7, "end_state_json": json.dumps({
                "name": "Tester", "room_vnum": "3054", "dead": False,
                "in_combat": False, "currencies": {"platinum": 1},
            }), **changes}


def replies():
    return [event("decision", {"command": "withdraw 1 platinum"}),
            reply("The teller says 'Thank you for your custom Tester.'\n"
                  "You currently have 133 platinum, 2 gold, 1 silver and "),
            reply("7 copper coins in the bank.\n\r", 3),
            event("decision", {"command": "west"}, 4)]


def test_bank_receipt_requires_complete_command_local_withdrawal():
    receipt = bank_reserve_receipt([visit()], lambda _: replies(), character_name="Tester")
    assert receipt["bank_copper"] == 133217
    assert receipt["balance_event_id"] == 3
    assert receipt["working_reserve_copper"] == 1000
    assert bank_reserve_receipt([visit()], lambda _: replies()[:2],
                               character_name="Tester") is None


@pytest.mark.parametrize("change", [
    {"status": "failed"}, {"status": "running"}, {"run_id": None},
    {"end_state_json": "{}"},
])
def test_latest_bank_failure_does_not_reuse_older_balance(change):
    rows = [visit(2, **change), visit(1)]
    assert bank_reserve_receipt(rows, lambda _: replies(), character_name="Tester") is None


def test_balance_from_another_command_or_character_is_not_withdrawal_proof():
    rows = replies()
    rows.insert(1, event("decision", {"command": "balance"}))
    assert bank_reserve_receipt([visit()], lambda _: rows, character_name="Tester") is None
    assert bank_reserve_receipt([visit()], lambda _: replies(), character_name="Other") is None
    rows = replies() + [event("decision", {"command": "withdraw 1 platinum"}),
                        reply("You have no platinum coins to withdraw.\n")]
    assert bank_reserve_receipt([visit()], lambda _: rows, character_name="Tester") is None
    rows = replies() + [event("decision", {"command": "withdraw 3 gold"})]
    assert bank_reserve_receipt([visit()], lambda _: rows, character_name="Tester") is None


def test_bank_handoff_replaces_funding_only_not_combat_or_recovery(monkeypatch):
    runner = CampaignRunner.__new__(CampaignRunner)
    runner._source_gear_primary_is_stale = lambda _: False
    runner._source_ranked_no_progress_streak = 0
    runner._campaign_policy_segments = [visit()]
    runner._campaign_policy_storage = SimpleNamespace(
        list_recent_events=lambda run_id, limit: replies(),
    )
    runner._emit_progress = lambda _: None
    monkeypatch.setattr(runner, "_policy_for_state_without_bank_reserve",
                        lambda *args, **kwargs: _PROVISION_FUNDING_POLICY)
    state = {"name": "Tester", "level": 45, "room_vnum": "3054",
             "hp": 100, "max_hp": 100, "mana": 100, "max_mana": 100,
             "move": 100, "max_move": 100, "currencies": {"copper": 164}}
    selected = runner._policy_for_state(state)
    assert selected.execution == "bank-excess-coins"
    assert state[BANK_RESERVE_HANDOFF_KEY]["run_id"] == 7
    assert runner._policy_for_state({**state, "hp": 20}).execution == "provision-funding"
    assert runner._policy_for_state({**state, "currencies": {"platinum": 1}}).execution == "provision-funding"
    monkeypatch.setattr(runner, "_policy_for_state_without_bank_reserve",
                        lambda *args, **kwargs: SimpleNamespace(execution="source-ranked-hunt"))
    assert runner._policy_for_state(state).execution == "source-ranked-hunt"


@pytest.mark.parametrize("blocker,expected", [
    (None, "bank-excess-coins"), ("no-bank", "provision-funding"),
    ("capacity", "source-ranked-hunt"), ("old-boot", "source-ranked-hunt"),
    ("ready-flight", "source-ranked-hunt"), ("wounded", "source-ranked-hunt"),
    ("combat", "source-ranked-hunt"), ("quest", "source-ranked-hunt"),
])
def test_inline_flight_funds_failure_reaches_shared_bank_handoff(monkeypatch, blocker, expected):
    runner = CampaignRunner.__new__(CampaignRunner)
    runner._source_gear_primary_is_stale = lambda _: False
    runner._source_ranked_no_progress_streak = 0
    runner._campaign_policy_segments = [] if blocker == "no-bank" else [visit()]
    runner._campaign_policy_storage = SimpleNamespace(list_recent_events=lambda *_a, **_kw: replies())
    runner._emit_progress = lambda _: None
    hunt = SimpleNamespace(execution="source-ranked-hunt", policy_id="test-hunt", practice_skill=None)
    monkeypatch.setattr(runner, "_policy_for_state_without_bank_reserve", lambda *_a, **_kw: hunt)
    receipt = {"reason": "funds", "level": 46, "boot_id": "boot"}
    state = {
        "name": "Tester", "level": 46, "world_boot_id": "boot", "room_vnum": "3054",
        "hp": 100, "max_hp": 100, "mana": 100, "max_mana": 100, "move": 100, "max_move": 100,
        "currencies": {"copper": 101}, "magic_shop_purchase_failed": True,
        "campaign_flight_purchase_failure": receipt,
        "affects": [[{"name": "fly", "duration": "0"}]],
        "quest_status": {"active": 0, "total_points": 18},
    }
    if blocker == "capacity":
        receipt["reason"] = "capacity"
    elif blocker == "old-boot":
        receipt["boot_id"] = "earlier"
    elif blocker == "ready-flight":
        state["affects"][0][0]["duration"] = "32"
    elif blocker == "wounded":
        state["hp"] = 20
    elif blocker == "combat":
        state["in_combat"] = True
    elif blocker == "quest":
        state["quest_status"]["active"] = 1
    assert runner._policy_for_state(state).execution == expected


@pytest.mark.parametrize("blocker", [None, "no-receipt", "old-boot", "affordable", "visible", "wounded", "quest"])
def test_hidden_supply_quote_failure_uses_existing_bank_handoff(monkeypatch, blocker):
    runner = CampaignRunner.__new__(CampaignRunner)
    runner._source_gear_primary_is_stale = lambda _: False
    runner._source_ranked_no_progress_streak = 0
    runner._campaign_policy_segments = [visit()]
    runner._campaign_policy_storage = SimpleNamespace(list_recent_events=lambda run_id, limit: replies())
    runner._selected_source_consumable_candidate = SimpleNamespace(requires_detect_invisibility=blocker != "visible")
    runner._emit_progress = lambda _: None
    supply = SimpleNamespace(execution="moria-sanctuary-hunt", practice_skill=None)
    monkeypatch.setattr(runner, "_policy_for_state_without_bank_reserve", lambda *a, **kw: supply)
    state = {"name": "Tester", "level": 46, "room_vnum": "3054", "world_boot_id": "boot-1",
             "hp": 100, "max_hp": 100, "mana": 100, "max_mana": 100,
             "move": 100, "max_move": 100, "currencies": {"copper": 19},
             "campaign_visibility_preparation": {"level": 46, "boot_id": "boot-1",
                 "price_boot_id": "boot-1", "failed": True, "funding_required": True, "price": 248}}
    if blocker == "no-receipt":
        state.pop("campaign_visibility_preparation")
    elif blocker == "old-boot":
        state["campaign_visibility_preparation"]["boot_id"] = "old"
    elif blocker == "affordable":
        state["currencies"] = {"platinum": 1}
    elif blocker == "wounded":
        state["hp"] = 20
    elif blocker == "quest":
        monkeypatch.setattr("dd4tester.campaign.snapshot_quest_status", lambda _: SimpleNamespace(active=True))
    selected = runner._policy_for_state(state)
    assert selected.execution == ("bank-excess-coins" if blocker is None else "moria-sanctuary-hunt")


@pytest.mark.parametrize("has_food,has_bank", [(False, True), (True, True), (False, False)])
def test_urgent_food_sale_uses_confirmed_bank_before_repeating_liquidation(monkeypatch, has_food, has_bank):
    runner = CampaignRunner.__new__(CampaignRunner)
    runner._campaign_policy_segments = [visit()] if has_bank else []
    runner._campaign_policy_storage = SimpleNamespace(list_recent_events=lambda run_id, limit: replies())
    runner._emit_progress = lambda _: None
    sale = SimpleNamespace(execution="sell-loot", policy_id="liquidate-loot", practice_skill=None)
    monkeypatch.setattr(runner, "_policy_for_state_without_bank_reserve", lambda *a, **kw: sale)
    monkeypatch.setattr("dd4tester.campaign._has_campaign_food", lambda *a, **kw: has_food)
    state = {"name": "Tester", "level": 46, "room_vnum": "3054",
             "hp": 100, "max_hp": 100, "mana": 100, "max_mana": 100,
             "move": 100, "max_move": 100, "currencies": {"copper": 20}}
    selected = runner._policy_for_state(state)
    assert selected.execution == ("bank-excess-coins" if not has_food and has_bank else "sell-loot")


@pytest.mark.parametrize("latest_status", ["success", "failed", "running", None])
def test_bank_handoff_looks_beyond_short_tail_without_resurrecting_old_proof(
    monkeypatch, latest_status,
):
    runner = CampaignRunner.__new__(CampaignRunner)
    runner._campaign_policy_campaign_id = 39
    runner._campaign_policy_segments = [visit(1)]
    calls = []

    def latest_bank(campaign_id, phase, *, search_limit):
        calls.append((campaign_id, phase, search_limit))
        return visit(2, status=latest_status) if latest_status is not None else None

    runner._campaign_policy_storage = SimpleNamespace(
        list_recent_events=lambda run_id, limit: replies(),
        get_latest_campaign_segment_for_phase=latest_bank,
    )
    runner._emit_progress = lambda _: None
    monkeypatch.setattr(runner, "_policy_for_state_without_bank_reserve",
                        lambda *args, **kwargs: _PROVISION_FUNDING_POLICY)
    state = {"name": "Tester", "level": 46, "room_vnum": "3054",
             "hp": 100, "max_hp": 100, "mana": 100, "max_mana": 100,
             "move": 100, "max_move": 100, "currencies": {"copper": 13}}
    selected = runner._policy_for_state(state)
    assert calls == [(39, "bank-excess-coins", 256)]
    if latest_status == "success":
        assert selected.execution == "bank-excess-coins"
        assert state[BANK_RESERVE_HANDOFF_KEY]["segment_id"] == 2
    else:
        assert selected.execution == "provision-funding"
        assert BANK_RESERVE_HANDOFF_KEY not in state
