import json

import pytest

from dd4tester.campaign import (
    _apply_flight_funding_state_transition,
    _campaign_flight_purchase_failed,
    _latest_flight_purchase_state,
)
from dd4tester.campaign_migrations import (
    recover_flight_capacity_failure,
    recover_flight_capacity_preflight_failure,
)
from dd4tester.starter import _flight_purchase_failure_snapshot


@pytest.mark.parametrize(
    ("requested", "failed", "expected"),
    (
        (True, False, {}),
        (False, True, {}),
        (
            True,
            True,
            {
                "campaign_flight_purchase_failure": {
                    "reason": "unconfirmed",
                    "run_id": 17546,
                    "level": 37,
                    "boot_id": "boot-one",
                }
            },
        ),
    ),
)
def test_flight_failure_snapshot_only_marks_an_actual_failed_purchase(
    requested, failed, expected,
):
    assert _flight_purchase_failure_snapshot(
        requested=requested,
        failed=failed,
        reason=None,
        run_id=17546,
        level=37,
        boot_id="boot-one",
    ) == expected


def test_successful_flight_purchase_clears_the_active_failure_receipt():
    previous = {
        "magic_shop_purchase_failed": True,
        "campaign_flight_purchase_failure": {
            "reason": "unconfirmed", "run_id": 17546,
        },
    }
    transitioned = _apply_flight_funding_state_transition(
        previous,
        {"magic_shop_purchase_failed": False},
        execution="buy-flight-potion",
        funding_completed=False,
    )

    assert "campaign_flight_purchase_failure" not in transitioned
    assert transitioned["magic_shop_purchase_failed"] is False


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


def _preflight_state():
    return {
        "room_vnum": "3054", "dead": False, "in_combat": False,
        "level": 36, "world_boot_id": "boot-one", "xp": 1000,
        "campaign_source_revision": "source-one",
    }


def _preflight_segment(state=None):
    checkpoint = _preflight_state() if state is None else state
    return {
        "id": 13, "run_id": 11, "phase": "buy-flight-potion",
        "status": "failed",
        "error": "buy-flight-potion segment failed: no source-identified redundant gear could free the required item slot",
        "start_state_json": json.dumps(checkpoint),
    }


def _preflight_rows():
    return [{
        "kind": "state",
        "payload_json": json.dumps({
            "state": "failed",
            "error": "no source-identified redundant gear could free the required item slot",
            "healer_carrying_capacity": {
                "complete": False, "failure": "no source-identified redundant gear could free the required item slot",
                "room_vnum": "3054", "required_slots": 1,
                "initial_count": 41, "maximum_count": 41,
            },
            "logout_confirmation": {
                "acknowledged": True,
                "reply": "You bid farewell to the Dragons Domain.",
            },
        }),
    }]


def test_legacy_capacity_cause_requires_complete_bounded_canonical_events():
    receipt = recover_flight_capacity_failure(EventStorage(_rows()), _segment(), _state())
    assert receipt["reason"] == "capacity" and receipt["run_id"] == 11
    assert receipt["legacy_canonical_event_count"] == 2
    assert recover_flight_capacity_failure(EventStorage(_rows() * 128), _segment(), _state()) is None


def test_capacity_preflight_failure_is_recovered_from_safe_healer_evidence():
    receipt = recover_flight_capacity_preflight_failure(
        EventStorage(_preflight_rows()), _preflight_segment(), _preflight_state(),
    )
    assert receipt == {
        "reason": "capacity", "run_id": 11, "segment_id": 13,
        "boot_id": "boot-one", "level": 36, "source_revision": "source-one",
        "preflight_failure": True, "initial_count": 41,
        "maximum_count": 41, "required_slots": 1, "canonical_event_count": 1,
    }


def test_unconfirmed_or_dangerous_preflight_failure_is_not_recovered():
    rows = _preflight_rows()
    payload = json.loads(rows[0]["payload_json"])
    payload["logout_confirmation"]["acknowledged"] = False
    rows[0]["payload_json"] = json.dumps(payload)
    assert recover_flight_capacity_preflight_failure(
        EventStorage(rows), _preflight_segment(), _preflight_state(),
    ) is None


def test_latest_flight_state_includes_verified_failed_preflight():
    class CampaignStorage(EventStorage):
        def list_recent_campaign_segments(self, campaign_id, *, limit):
            assert campaign_id == 7
            return [_preflight_segment()]

    state = _latest_flight_purchase_state(
        CampaignStorage(_preflight_rows()), 7,
    )
    assert state["magic_shop_purchase_failed"] is True
    assert state["campaign_flight_purchase_failure"]["reason"] == "capacity"


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
