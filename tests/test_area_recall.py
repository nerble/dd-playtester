import pytest

from dd4tester.area_recall import AreaRecallEscape, source_allows_failed_local_recall_logout
from dd4tester.equipment import GearCatalog, ITEM_WEAPON
from dd4tester.hunt_candidates import ObjectSource, ROOM_NO_MOB, RoomSource, WorldSource
from dd4tester.state import CharacterState


PROMPT = "<702/702 hits 100/267 mana 230/492 move [Sea]> "


def advance(session, room="27647", now=1.0, **changes):
    state = CharacterState(room_vnum=room, hp=702, max_hp=702, move=230,
                           level=30, exits={"u": "27132"})
    options = dict(now=now, inventory=(), coins=947, flight=True, infrared=True,
                   sanctuary=True, purple_available=True, water_breathing=True)
    options.update(changes)
    return session.next_command(state, **options)


def test_escape_rechecks_an_adjacent_mobile_before_closing():
    session = AreaRecallEscape()
    assert advance(session) == "scan up"
    session.observe("Old Higue who is one room upwards.\n")
    assert advance(session, now=2) is None
    session.observe(PROMPT)
    assert advance(session, now=3) is None
    assert session.failure is None
    assert session.scan_retry_count == 1
    assert advance(session, now=7.9) is None
    assert advance(session, now=8) == "scan up"
    assert session.scans[0]["room_vnum"] == "27647"


def test_escape_does_not_mistake_a_distant_mobile_for_an_adjacent_one():
    session = AreaRecallEscape()
    assert advance(session) == "scan up"
    session.observe("Old Higue who is two rooms upwards.\n" + PROMPT)
    assert advance(session, now=2) == "up"
    assert session.pending_room == "27132"


def test_escape_accepts_a_verified_active_light_without_buying_the_pie():
    session = AreaRecallEscape()
    state = CharacterState(
        room_vnum="27347", hp=702, max_hp=702, move=230, level=30,
        exits={"u": "27647"},
    )
    assert session.next_command(
        state, now=1.0, inventory=(), coins=104, flight=True,
        infrared=False, sanctuary=True, purple_available=True,
        water_breathing=True, light_available=True,
    ) == "up"
    assert session.purchase.stage == "new"


def test_expired_vision_restarts_the_shop_loop_at_local_recall():
    session = AreaRecallEscape(stage="escape")
    state = CharacterState(
        room_vnum="27347", hp=702, max_hp=702, move=230, level=30,
        exits={"s": "27341", "u": "27647"},
    )

    assert session.next_command(
        state, now=1.0, inventory=(), coins=947, flight=True,
        infrared=False, sanctuary=True, purple_available=True,
        water_breathing=True,
    ) == "south"
    assert session.stage == "shop"
    assert session.shop_index == 1
    assert session.purchase.stage == "new"


def test_escape_resumes_from_the_bakery_by_backtracking_to_local_recall():
    session = AreaRecallEscape.from_room("27331")
    state = CharacterState(
        room_vnum="27331", hp=702, max_hp=702, move=230, level=30,
        exits={"e": "27332"},
    )
    assert session.next_command(
        state, now=1.0, inventory=(), coins=104, flight=True,
        infrared=False, sanctuary=True, purple_available=True,
        water_breathing=True, light_available=True,
    ) == "east"
    assert session.pending_room == "27332"


def test_water_loss_at_a_local_shop_route_recalls_before_preparation():
    session = AreaRecallEscape.from_room("27331")
    state = CharacterState(
        room_vnum="27331", hp=702, max_hp=702, move=230, level=30,
        exits={"e": "27332"},
    )
    assert session.next_command(
        state, now=1.0, inventory=(), coins=104, flight=True,
        infrared=True, sanctuary=True, purple_available=True,
        water_breathing=False,
    ) == "recall"
    assert session.water_prep_stage == "water-await-recall"
    session.observe(PROMPT)
    state.room_vnum = "27347"
    state.exits = {"s": "27341"}
    assert session.next_command(
        state, now=2.0, inventory=(), coins=104, flight=True,
        infrared=True, sanctuary=True, purple_available=True,
        water_breathing=False, gear_catalog=object(),
    ) == "south"
    assert session.water_prep_stage == "water-outbound"


def test_water_preparation_wakes_before_moving_from_an_underwater_recall_room():
    session = AreaRecallEscape()
    state = CharacterState(
        room_vnum="27347", hp=345, max_hp=925, move=269, level=40,
        position=4, exits={"s": "27341"},
    )
    assert session.next_command(
        state, now=1.0, inventory=(), coins=104, flight=True,
        infrared=True, sanctuary=True, purple_available=True,
        water_breathing=False, gear_catalog=object(),
    ) == "stand"
    session.observe(PROMPT)
    state.position = 7
    assert session.next_command(
        state, now=2.0, inventory=(), coins=104, flight=True,
        infrared=True, sanctuary=True, purple_available=True,
        water_breathing=False, gear_catalog=object(),
    ) == "south"
    assert session.water_prep_stage == "water-outbound"


def test_water_funding_uses_the_source_weaponsmith_before_water_shop():
    current = ObjectSource(
        9001, "axe current", "a current axe", ITEM_WEAPON,
        (0, 0, 0, 1), 0, wear_flags=1 << 13, level=40,
    )
    spare = ObjectSource(
        9002, "axe spare", "a spare axe", ITEM_WEAPON,
        (0, 0, 0, 1), 120, wear_flags=1 << 13, level=1,
    )
    catalog = GearCatalog({current.vnum: current, spare.vnum: spare})
    session = AreaRecallEscape()
    session.water_prep_origin = "27347"
    session.water_prep_stage = "water-purchase"
    state = CharacterState(
        room_vnum="27340", level=40, hp=925, max_hp=925, move=541,
        exits={"w": "27339"},
        equipment=[{"name": "a current axe", "slot": "wield"}],
        inventory=[[{"short_desc": "a spare axe"}]],
    )
    inventory = (("a spare axe", "#9002"),)
    assert session.next_command(
        state, now=1.0, inventory=inventory, coins=335, flight=True,
        infrared=True, sanctuary=True, purple_available=True,
        water_breathing=False, gear_catalog=catalog,
    ) == "list shark"
    session.observe("[ 29   626] [#14952] shark's wine\n" + PROMPT)
    assert session.next_command(
        state, now=2.0, inventory=inventory, coins=335, flight=True,
        infrared=True, sanctuary=True, purple_available=True,
        water_breathing=False, gear_catalog=catalog,
    ) == "west"
    assert session.water_prep_stage == "water-funding-outbound"


@pytest.mark.parametrize("options", [dict(flight=False), dict(infrared=False),
                                     dict(sanctuary=False, purple_available=False)])
def test_dark_escape_missing_a_required_capability_never_moves(options):
    session = AreaRecallEscape()
    assert advance(session, **options) is None
    assert session.failure


def test_water_loss_backtracks_to_local_recall_before_preparing_water():
    session = AreaRecallEscape(stage="escape")
    options = dict(
        now=1.0, inventory=(), coins=947, flight=True, infrared=True,
        sanctuary=True, purple_available=True, water_breathing=False,
    )

    state = CharacterState(
        room_vnum="27132", hp=702, max_hp=702, move=230, level=30,
        exits={"d": "27648"},
    )
    assert session.next_command(state, **options) == "down"
    session.observe(PROMPT)

    state = CharacterState(
        room_vnum="27648", hp=702, max_hp=702, move=229, level=30,
        exits={"w": "27647"},
    )
    assert session.next_command(state, now=2.0, **{k: v for k, v in options.items() if k != "now"}) == "west"
    session.observe(PROMPT)

    state = CharacterState(
        room_vnum="27647", hp=702, max_hp=702, move=228, level=30,
        exits={"d": "27347"},
    )
    assert session.next_command(state, now=3.0, **{k: v for k, v in options.items() if k != "now"}) == "down"
    session.observe(PROMPT)

    state = CharacterState(
        room_vnum="27347", hp=702, max_hp=702, move=227, level=30,
        exits={"s": "27341"},
    )
    assert session.next_command(state, now=4.0, **{k: v for k, v in options.items() if k != "now"}) == "south"
    assert session.water_loss_return_active is False
    assert session.water_prep_stage == "water-outbound"


def test_water_loss_at_the_potion_shop_recalls_before_preparation():
    session = AreaRecallEscape(stage="escape")
    state = CharacterState(
        room_vnum="27340", hp=702, max_hp=702, move=230, level=30,
        exits={},
    )

    assert session.next_command(
        state, now=1.0, inventory=(), coins=947, flight=True, infrared=True,
        sanctuary=True, purple_available=True, water_breathing=False,
    ) == "recall"
    assert session.water_prep_stage == "water-await-recall"


def test_water_funding_uses_distinct_redundant_armour_items():
    first = ObjectSource(
        101, "first cloak", "a first cloak", 9, (1, 0, 0, 0), 10,
        wear_flags=1 << 10,
    )
    second = ObjectSource(
        102, "second cloak", "a second cloak", 9, (1, 0, 0, 0), 20,
        wear_flags=1 << 10,
    )
    better = ObjectSource(
        103, "better cloak", "a better cloak", 9, (1, 0, 0, 0), 30,
        wear_flags=1 << 10, affects=((19, 1),),
    )
    catalog = GearCatalog({item.vnum: item for item in (first, second, better)})
    session = AreaRecallEscape()

    funding = session._funding_item(
        (("a first cloak", "#101"), ("a second cloak", "#102")),
        [{"name": "a better cloak"}],
        catalog,
    )
    assert funding is not None and funding[2].vnum == 102

    next_funding = session._funding_item(
        (("a first cloak", "#101"), ("a second cloak", "#102")),
        [{"name": "a better cloak"}],
        catalog,
        excluded_vnums=(102,),
    )
    assert next_funding is not None and next_funding[2].vnum == 101


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
