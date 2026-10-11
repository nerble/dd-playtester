import json
from copy import deepcopy

import pytest

from dd4tester.observations import ObservationParser
from dd4tester.state import CharacterState


def _room() -> dict:
    return {
        "vnum": "3054", "name": "By the Temple Altar", "area": "Midgaard",
        "area_id": "3001", "sector": "0", "sector_text": "inside",
        "description": "An altar stands here.", "flags": "no_mob indoors safe healing",
        "exits": {"s": "3001"},
        "exit_details": {"s": {"to": 3001, "state": "open", "door": "", "cost": 1}},
        "arrival": {"from": 0, "direction": None, "kind": "login"},
        "tags": ["healer", "safe"],
    }


def _feed(parser: ObservationParser, package: str, value) -> list:
    return parser.feed_gmcp(f"{package} {json.dumps(value)}")


def test_flight_cost_refresh_preserves_fresh_carrying_and_inventory() -> None:
    parser = ObservationParser(expected_character_name="Aldrin")
    state = CharacterState()
    room = _room()
    events = _feed(parser, "Room.Info", room)
    events += _feed(parser, "Char.Stats", {"carry_num": "39", "maxcarry_num": "38"})
    room["exit_details"]["s"]["cost"] = 2
    events += _feed(parser, "Room.Info", room)
    events += _feed(parser, "Char.Stats", {"carry_num": "38", "maxcarry_num": "38"})
    items = [[{"quan": "5", "short_desc": "an I.Q. Vine"}]]
    events += _feed(parser, "Char.Items", items)
    for event in events:
        state.apply(event)
    assert not parser._discarding_duplicate_login_snapshot
    assert state.stats["carry_num"] == 38
    assert state.inventory == items
    assert any(event.type == "room_updated" for event in events)


@pytest.mark.parametrize("field", [
    "name", "vnum", "description", "flags", "arrival", "exits", "area_id", "tags",
])
def test_changed_room_identity_still_quarantines_login_snapshot(field: str) -> None:
    parser = ObservationParser()
    room = _room()
    _feed(parser, "Room.Info", room)
    changed = deepcopy(room)
    changed[field] = (
        {"from": 3001, "direction": None, "kind": "login"}
        if field == "arrival" else "changed"
    )
    assert _feed(parser, "Room.Info", changed) == []
    assert _feed(parser, "Char.Stats", {"carry_num": "1"}) == []


@pytest.mark.parametrize("change", ["destination", "state", "door", "cost", "missing", "extra"])
def test_refresh_rejects_non_cost_exit_changes_and_invalid_cost(change: str) -> None:
    parser = ObservationParser()
    room = _room()
    _feed(parser, "Room.Info", room)
    changed = deepcopy(room)
    detail = changed["exit_details"]["s"]
    if change == "destination":
        detail["to"] = 3005
    elif change == "missing":
        del detail["cost"]
    elif change == "extra":
        detail["unknown"] = True
    else:
        detail[change] = -1 if change == "cost" else "changed"
    assert _feed(parser, "Room.Info", changed) == []
    assert parser._discarding_duplicate_login_snapshot


def test_valid_refresh_does_not_clear_existing_quarantine() -> None:
    parser = ObservationParser()
    room = _room()
    _feed(parser, "Room.Info", room)
    _feed(parser, "Room.Info", dict(room, name="By \0\0"))
    assert _feed(parser, "Room.Info", room) == []
    assert _feed(parser, "Char.Stats", {"carry_num": "38"}) == []


def test_reset_discards_the_room_refresh_baseline() -> None:
    parser = ObservationParser()
    _feed(parser, "Room.Info", _room())
    parser.reset_connection()
    assert parser._last_room_snapshot is None
