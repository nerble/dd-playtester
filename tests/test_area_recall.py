import pytest

from dd4tester.area_recall import AreaRecallEscape, source_allows_failed_local_recall_logout
from dd4tester.hunt_candidates import ROOM_NO_MOB, RoomSource, WorldSource
from dd4tester.state import CharacterState


PROMPT = "<702/702 hits 100/267 mana 230/492 move [Sea]> "


def advance(session, room="27647", now=1.0, **changes):
    state = CharacterState(room_vnum=room, hp=702, max_hp=702, move=230,
                           level=30, exits={"u": "27132"})
    options = dict(now=now, inventory=(), coins=947, flight=True, infrared=True,
                   sanctuary=True, purple_available=True, water_breathing=True)
    options.update(changes)
    return session.next_command(state, **options)


def test_escape_waits_for_complete_scan_and_rejects_an_adjacent_mobile():
    session = AreaRecallEscape()
    assert advance(session) == "scan up"
    session.observe("Old Higue who is one room upwards.\n")
    assert advance(session, now=2) is None
    session.observe(PROMPT)
    assert advance(session, now=3) is None
    assert session.failure == "the immediate escape destination is occupied or closed"
    assert session.scans[0]["room_vnum"] == "27647"


def test_escape_does_not_mistake_a_distant_mobile_for_an_adjacent_one():
    session = AreaRecallEscape()
    assert advance(session) == "scan up"
    session.observe("Old Higue who is two rooms upwards.\n" + PROMPT)
    assert advance(session, now=2) == "up"
    assert session.pending_room == "27132"


@pytest.mark.parametrize("options", [dict(flight=False), dict(infrared=False),
                                     dict(water_breathing=False),
                                     dict(sanctuary=False, purple_available=False)])
def test_dark_escape_missing_a_required_capability_never_moves(options):
    session = AreaRecallEscape()
    assert advance(session, **options) is None
    assert session.failure


def test_escape_scan_timeout_does_not_retry_or_move():
    session = AreaRecallEscape()
    assert advance(session) == "scan up"
    assert advance(session, now=6.1) is None
    assert session.failure and session.commands_sent == 1


def test_source_room_expectation_requires_the_actual_destination():
    session = AreaRecallEscape()
    advance(session)
    session.observe("You can't see anything upwards.\n" + PROMPT)
    assert advance(session, now=2) == "up"
    session.observe("You cannot go that way.\n" + PROMPT)
    assert advance(session, now=3) is None
    assert "exact registered room" in session.failure


def test_escape_never_starts_a_fight_even_with_protection():
    session = AreaRecallEscape()
    state = CharacterState(room_vnum="27132", hp=702, max_hp=702,
                           move=230, level=30, in_combat=True)
    assert session.next_command(state, now=1, inventory=(), coins=947,
                                flight=True, infrared=True, sanctuary=True,
                                purple_available=True, water_breathing=True) is None
    assert "no attack is authorized" in session.failure


def test_failed_local_recall_logout_requires_matching_source_and_live_no_mob(monkeypatch):
    world = WorldSource(rooms={27347: RoomSource(27347, "market", "test.are", room_flags=ROOM_NO_MOB)})
    state = CharacterState(room_vnum="27347", room_flags=["no_mob"],
                           level=30, hp=702, max_hp=702, position=8)
    monkeypatch.setattr("dd4tester.area_recall.source_route_hazard_rejections", lambda *a, **k: ())
    assert source_allows_failed_local_recall_logout(world, state)
    state.room_flags = []
    assert not source_allows_failed_local_recall_logout(world, state)
    state.room_flags = ["no_mob"]
    world.rooms[27347].room_flags = 0
    assert not source_allows_failed_local_recall_logout(world, state)


@pytest.mark.parametrize("changes", [
    {"room_vnum": "99"}, {"room_vnum": "3054"}, {"in_combat": True},
    {"combat_target": "a shark"}, {"dead": True}, {"hp": 0},
    {"position": None}, {"position": 3}, {"position": "unknown"},
])
def test_failed_local_recall_logout_never_overrides_survival_or_room_gates(monkeypatch, changes):
    world = WorldSource(rooms={27347: RoomSource(27347, "market", "test.are", room_flags=ROOM_NO_MOB)})
    state = CharacterState(room_vnum="27347", room_flags=["no_mob"],
                           level=30, hp=702, max_hp=702, position=8)
    for name, value in changes.items():
        setattr(state, name, value)
    monkeypatch.setattr("dd4tester.area_recall.source_route_hazard_rejections", lambda *a, **k: ())
    assert not source_allows_failed_local_recall_logout(world, state)


def test_failed_local_recall_logout_rejects_missing_source_and_source_hazards(monkeypatch):
    state = CharacterState(room_vnum="27347", room_flags=["no_mob"],
                           level=30, hp=702, max_hp=702, position=8)
    assert not source_allows_failed_local_recall_logout(None, state)
    world = WorldSource(rooms={27347: RoomSource(27347, "market", "test.are", room_flags=ROOM_NO_MOB)})
    monkeypatch.setattr("dd4tester.area_recall.source_route_hazard_rejections", lambda *a, **k: ("hazard",))
    assert not source_allows_failed_local_recall_logout(world, state)
