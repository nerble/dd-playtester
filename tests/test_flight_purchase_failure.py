import json

import pytest

from dd4tester.campaign import _campaign_flight_purchase_failed
from dd4tester.campaign_migrations import recover_flight_capacity_failure


def _rows(reply="You can't carry that many items.\n"):
    return [
        {"kind": "command", "payload_json": json.dumps({"command": "buy light"})},
        {"kind": "response", "payload_json": json.dumps({"text": reply})},
    ]


def _state():
    return {"magic_shop_purchase_failed": True, "room_vnum": "3054", "level": 31,
            "world_boot_id": "boot-one", "campaign_source_revision": "source-one"}


def _segment():
    return {"id": 12, "run_id": 11, "phase": "buy-flight-potion", "status": "success"}


class EventStorage:
    def __init__(self, rows):
        self.rows = rows

    def list_recent_events(self, run_id, *, limit):
        assert run_id == 11 and limit == 256
        return self.rows


def test_legacy_capacity_cause_requires_complete_bounded_canonical_events():
    receipt = recover_flight_capacity_failure(EventStorage(_rows()), _segment(), _state())
    assert receipt["reason"] == "capacity" and receipt["run_id"] == 11
    assert receipt["legacy_canonical_event_count"] == 2
    assert recover_flight_capacity_failure(EventStorage(_rows() * 128), _segment(), _state()) is None


@pytest.mark.parametrize("reply", [
    "You can't afford that.\n", "The healer smiles.\n",
    "You can't carry that many items.\nYou do not have enough money.\n",
    "You can't carry that many items.\nI will not serve the likes of you.\n",
])
def test_legacy_carrying_repair_rejects_other_causes(reply):
    assert recover_flight_capacity_failure(EventStorage(_rows(reply)), _segment(), _state()) is None


def test_unrelated_item_pickup_cannot_prove_flight_purchase_failure():
    rows = _rows()
    rows[0]["payload_json"] = json.dumps({"command": "get arm"})
    assert recover_flight_capacity_failure(EventStorage(rows), _segment(), _state()) is None


def test_earlier_capacity_refusal_cannot_replace_the_latest_purchase_reply():
    rows = _rows() + _rows("You buy a light blue potion.\n")
    assert recover_flight_capacity_failure(EventStorage(rows), _segment(), _state()) is None
    assert recover_flight_capacity_failure(EventStorage(_rows() + _rows("")), _segment(), _state()) is None


def test_capacity_cause_keeps_retry_cooldown_then_stops_requesting_funding(monkeypatch):
    failed = {**_state(), "campaign_flight_purchase_failure": {"reason": "capacity"}}
    monkeypatch.setattr("dd4tester.campaign._latest_flight_purchase_state", lambda *_: failed)
    current = {**_state(), "campaign_flight_purchase_cooldown": 2}
    assert _campaign_flight_purchase_failed(object(), 7, current_state=current) is True
    assert current["campaign_flight_purchase_cooldown"] == 2
    current["campaign_flight_purchase_cooldown"] = 0
    assert _campaign_flight_purchase_failed(object(), 7, current_state=current) is False
    assert current["campaign_flight_purchase_failure"]["reason"] == "capacity"
