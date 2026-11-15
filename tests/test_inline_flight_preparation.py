import json
import sqlite3
from types import SimpleNamespace

import pytest

import dd4tester.campaign as campaign
from dd4tester.campaign_migrations import recover_inline_flight_funds_failure
from dd4tester.character import CharacterSpec
from dd4tester.starter import StarterPolicy
from dd4tester.state import CharacterState
from dd4tester.storage import RunStorage


def state():
    return {"name": "Tester", "level": 46, "world_boot_id": "boot", "xp": 2000000,
            "room_vnum": "3054", "dead": False, "in_combat": False}


def segment(run_id, snapshot, **kwargs):
    return {"id": run_id, "run_id": run_id, "phase": "source-ranked-hunt-test-1-200-46",
            "status": "success", "start_state_json": json.dumps(state()),
            "end_state_json": json.dumps(snapshot), **kwargs}


def event(kind, **payload):
    return {"kind": kind, "payload_json": json.dumps(payload)}


def policy():
    value = StarterPolicy(CharacterSpec.from_mapping({
        "name": "Tester", "race": "human", "gender": "male", "class": "warrior",
    }), "password", magic_shop_buy_fly=True)
    value.world_boot_id = "boot"
    return value


def test_dynamic_flight_failure_belongs_to_policy_not_initial_runner_request():
    value = policy()
    value.magic_shop_purchase_failed = True
    value._recovery_session.flight_purchase_failure_reason = "funds"
    result = value.flight_preparation_checkpoint(CharacterState(level=46), run_id=20)
    assert result["campaign_flight_preparation"]["status"] == "failed"
    assert result["campaign_flight_purchase_failure"]["reason"] == "funds"
    assert result["campaign_flight_purchase_failure"]["run_id"] == 20


def test_prepared_flight_requires_fresh_affect_and_clears_prior_failure():
    value = policy()
    observed = CharacterState(level=46, affects=[[{"name": "fly", "duration": "32"}]])
    assert value.flight_preparation_checkpoint(observed, run_id=21) == {}
    value.learned_flight_affect_revision = 1
    result = value.flight_preparation_checkpoint(observed, run_id=21)
    assert result["magic_shop_purchase_failed"] is False
    assert result["campaign_flight_purchase_failure"] == {}
    assert result["campaign_flight_preparation"]["status"] == "prepared"
    value.magic_shop_buy_fly = False
    assert value.flight_preparation_checkpoint(observed, run_id=21) == {}


@pytest.mark.parametrize("prepared", [False, True])
def test_latest_inline_owner_precedes_older_standalone_purchase(monkeypatch, prepared):
    latest = {**state(), "magic_shop_purchase_failed": not prepared,
              "campaign_flight_preparation": {"run_id": 20, "level": 46, "boot_id": "boot",
                                              "status": "prepared" if prepared else "failed"}}
    rows = [segment(10, {**state(), "magic_shop_purchase_failed": prepared}, phase="buy-flight-potion"),
            segment(20, latest)]
    monkeypatch.setattr(campaign, "_runtime_campaign_segments", lambda *_a: rows)
    assert campaign._latest_flight_purchase_state(SimpleNamespace(), 1) == latest


def test_inherited_inline_receipt_is_not_a_new_attempt(monkeypatch):
    own = {**state(), "magic_shop_purchase_failed": False,
           "campaign_flight_preparation": {"run_id": 20, "level": 46, "boot_id": "boot", "status": "prepared"}}
    rows = [segment(20, own), segment(21, {**own, "magic_shop_purchase_failed": True})]
    monkeypatch.setattr(campaign, "_runtime_campaign_segments", lambda *_a: rows)
    assert campaign._latest_flight_purchase_state(SimpleNamespace(), 1) == own


@pytest.mark.parametrize("case", ["linked", "missing-header", "missing-row", "foreign-row", "newer-success"])
def test_checkpoint_owner_outside_short_tail_cannot_restore_older_success(monkeypatch, case):
    receipt = {"run_id": 20, "level": 46, "boot_id": "boot", "status": "failed"}
    failed = {**state(), "magic_shop_purchase_failed": True,
              "campaign_flight_preparation": receipt}
    linked = segment(20, failed)
    recent = [segment(10, {**state(), "magic_shop_purchase_failed": False}, phase="buy-flight-potion"),
              segment(30, state())]
    if case == "newer-success":
        recent.append(segment(35, {**state(), "magic_shop_purchase_failed": False,
            "campaign_flight_preparation": {**receipt, "run_id": 35, "status": "prepared"}}))
    calls = []

    def headers(campaign_id, *, limit):
        calls.append((campaign_id, limit))
        return [] if case == "missing-header" else [{"id": 20, "run_id": 20}]

    def load(campaign_id, segment_id):
        calls.append(("load", campaign_id, segment_id))
        if case == "missing-row":
            return None
        return {**linked, "run_id": 21} if case == "foreign-row" else linked

    store = SimpleNamespace(list_recent_campaign_segment_headers=headers,
                            get_campaign_segment_by_id=load)
    monkeypatch.setattr(campaign, "_runtime_campaign_segments", lambda *_a: recent)
    result = campaign._latest_flight_purchase_state(store, 1, failed)
    assert calls[0] == (1, 256)
    assert len(calls) <= 2
    if case == "linked":
        assert result == failed
    elif case == "newer-success":
        assert result["campaign_flight_preparation"]["run_id"] == 35
        assert result["magic_shop_purchase_failed"] is False
    else:
        assert result is None


def test_flight_owner_and_funding_resolution_survive_unrelated_boundary():
    receipt = {"run_id": 20, "level": 46, "boot_id": "boot", "status": "failed"}
    resolution = {"failed_run_id": 20, "prior_purchase_cooldown": 3}
    previous = {**state(), "campaign_flight_preparation": receipt,
                "campaign_flight_funding_resolution": resolution}
    result = campaign._campaign_segment_end_state(previous, state(), execution="bank-excess-coins")
    assert result["campaign_flight_preparation"] == receipt
    assert result["campaign_flight_funding_resolution"] == resolution
    prepared = {**receipt, "run_id": 30, "status": "prepared"}
    result = campaign._campaign_segment_end_state(previous, {
        **state(), "campaign_flight_preparation": prepared,
        "campaign_flight_purchase_failure": {},
    }, execution="source-ranked-hunt")
    assert result["campaign_flight_preparation"] == prepared
    assert result["campaign_flight_purchase_failure"] == {}


@pytest.mark.parametrize("key,value", [("level", 45), ("boot_id", "other"), ("status", "unknown")])
def test_invalid_newer_owner_does_not_restore_older_success(monkeypatch, key, value):
    receipt = {"run_id": 20, "level": 46, "boot_id": "boot", "status": "failed", key: value}
    rows = [segment(10, {**state(), "magic_shop_purchase_failed": False}, phase="buy-flight-potion"),
            segment(20, {**state(), "magic_shop_purchase_failed": True, "campaign_flight_preparation": receipt})]
    monkeypatch.setattr(campaign, "_runtime_campaign_segments", lambda *_a: rows)
    assert campaign._latest_flight_purchase_state(SimpleNamespace(), 1) is None


def test_command_response_projection_retains_order_scope_and_limit():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("CREATE TABLE events (id INTEGER, run_id INTEGER, timestamp TEXT, kind TEXT, payload_json TEXT)")
        connection.executemany("INSERT INTO events VALUES (?, ?, '', ?, '{}')", [
            (1, 1, "command"), (2, 1, "gmcp"), (3, 1, "response"),
            (4, 1, "game_event"), (5, 2, "response"), (6, 1, "command"),
        ])
        owner = SimpleNamespace(connection=connection)
        rows = RunStorage.list_recent_command_responses(owner, 1, limit=2)
        assert [row["id"] for row in rows] == [3, 6]
        with pytest.raises(ValueError):
            RunStorage.list_recent_command_responses(owner, 1, limit=0)
    finally:
        connection.close()


@pytest.mark.parametrize("duration,requires_funding", [
    (0, True), (1, True), (2, True), (3, False), (30, False), (-1, False), (None, False),
])
def test_short_active_flight_does_not_clear_recorded_funding(duration, requires_funding):
    affect = {"name": "fly"}
    if duration is not None:
        affect["duration"] = str(duration)
    observed = {**state(), "magic_shop_purchase_failed": True, "affects": [[affect]],
                "campaign_flight_purchase_failure": {"reason": "funds", "boot_id": "boot", "level": 46}}
    assert campaign._recorded_flight_funding_shortfall(observed) is requires_funding


@pytest.mark.parametrize("case", ["capacity", "other_boot", "other_level", "cleared"])
def test_flight_funding_requires_current_funds_failure(case):
    receipt = {"reason": "funds", "boot_id": "boot", "level": 46}
    observed = {**state(), "affects": [], "magic_shop_purchase_failed": True,
                "campaign_flight_purchase_failure": receipt}
    if case == "capacity":
        receipt["reason"] = "capacity"
    elif case == "other_boot":
        receipt["boot_id"] = "earlier"
    elif case == "other_level":
        receipt["level"] = 45
    else:
        observed["magic_shop_purchase_failed"] = False
    assert not campaign._recorded_flight_funding_shortfall(observed)


def test_recorded_funding_uses_requested_long_route_reserve():
    observed = {**state(), "magic_shop_purchase_failed": True,
                "affects": [[{"name": "fly", "duration": "5"}]],
                "campaign_flight_purchase_failure": {
                    "reason": "funds", "boot_id": "boot", "level": 46,
                    "minimum_flight_duration": 10,
                }}
    assert campaign._recorded_flight_funding_shortfall(observed)


@pytest.mark.parametrize("case,still_failed", [
    ("funded", False), ("no-increase", True), ("unknown-price", True),
    ("old-price", True), ("still-short", True), ("capacity", True),
    ("route-block", False), ("route-cooldown", False),
])
def test_new_funding_covers_quote_without_erasing_failure_or_cooldown(monkeypatch, case, still_failed):
    receipt = {"reason": "capacity" if case == "capacity" else "funds",
               "run_id": 20, "level": 46, "boot_id": "boot"}
    failed = {**state(), "magic_shop_purchase_failed": True,
              "currencies": {"copper": 101}, "campaign_flight_purchase_failure": receipt}
    current = {**state(), "currencies": {"platinum": 1},
               campaign._MAGIC_SHOP_FLIGHT_PRICE_KEY: 164,
               campaign._MAGIC_SHOP_FLIGHT_PRICE_BOOT_KEY: "boot",
               campaign._FLIGHT_PURCHASE_COOLDOWN_KEY: 2}
    if case == "no-increase":
        current["currencies"] = {"copper": 101}
    elif case == "unknown-price":
        current.pop(campaign._MAGIC_SHOP_FLIGHT_PRICE_KEY)
    elif case == "old-price":
        current[campaign._MAGIC_SHOP_FLIGHT_PRICE_BOOT_KEY] = "older"
    elif case == "still-short":
        current["currencies"] = {"copper": 150}
    elif case == "route-block":
        current[campaign._MAGIC_SHOP_ROUTE_BLOCKED_KEY] = True
    elif case == "route-cooldown":
        current[campaign._CITY_SHOP_ROUTE_COOLDOWN_KEY] = 2
    monkeypatch.setattr(campaign, "_latest_flight_purchase_state", lambda *_a: failed)
    assert campaign._campaign_flight_purchase_failed(SimpleNamespace(), 1, current_state=current) is still_failed
    assert current[campaign._FLIGHT_PURCHASE_COOLDOWN_KEY] == (0 if case == "funded" else 2)
    assert current["campaign_flight_purchase_failure"] == receipt
    if case == "funded":
        assert current["campaign_flight_funding_resolution"] == {
            "failed_run_id": 20, "boot_id": "boot", "level": 46,
            "failed_purse_copper": 101, "funded_purse_copper": 1000,
            "quoted_price_copper": 164, "prior_purchase_cooldown": 2,
        }
    else:
        assert "campaign_flight_funding_resolution" not in current


@pytest.mark.parametrize("case", ["funds", "capacity", "success", "chatter", "truncated", "wrong_character"])
def test_legacy_inline_funds_repair_is_command_local_and_bounded(case):
    snapshot = state()
    row = segment(20, snapshot, status="failed", error="flight purchase failed: funds")
    text = {"capacity": "You can't carry that many items.\n", "success": "You buy a light blue potion.\n"}.get(
        case, "You can't afford to buy it.\n")
    events = [event("command", command="buy light"), event("response", text=text)]
    if case == "chatter":
        events.insert(1, event("command", command="look"))
    elif case == "truncated":
        events *= 128
    elif case == "wrong_character":
        row["start_state_json"] = json.dumps({**state(), "name": "Another"})
    store = SimpleNamespace(list_recent_events=lambda *_a, **_k: events)
    receipt = recover_inline_flight_funds_failure(store, row, snapshot)
    assert (receipt is not None) is (case == "funds")
    if receipt:
        assert receipt["reason"] == "funds"
        assert receipt["run_id"] == 20
