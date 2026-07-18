from pathlib import Path

from dd4tester.observations import ObservationParser


def test_text_observations_cover_core_game_events() -> None:
    parser = ObservationParser()

    events = parser.feed_text(
        "\x1b[1mRoom: Market Square\x1b[0m\n"
        "<75/100 hp 40 mana>\n"
        "A sewer rat attacks you.\n"
        "New quest: Clear the Cellar!\n"
        "You receive a bronze sword.\n"
        "You have gained level 2!\n"
        "You have died.\n"
    )

    assert [event.type for event in events] == [
        "room_entered",
        "prompt_seen",
        "health_changed",
        "combat_started",
        "quest_received",
        "item_acquired",
        "level_gained",
        "character_died",
    ]
    assert events[0].data["name"] == "Market Square"
    assert events[2].data == {
        "text": "<75/100 hp 40 mana>",
        "current": 75,
        "previous": None,
        "maximum": 100,
    }
    assert events[3].data["target"] == "A sewer rat"
    assert events[6].data["level"] == 2


def test_text_observations_handle_split_chunks_and_unterminated_prompts() -> None:
    parser = ObservationParser()

    assert parser.feed_text("You have gain") == []
    events = parser.feed_text("ed level 3!\n<60/100 hp 20 mana>")

    assert [event.type for event in events] == ["level_gained"]
    flushed = parser.flush_text()
    assert [event.type for event in flushed] == ["prompt_seen", "health_changed"]


def test_gmcp_observations_track_changes_without_duplicate_events() -> None:
    parser = ObservationParser()

    room = parser.feed_gmcp(
        'Room.Info {"num": 42, "name": "Training Yard", "exits": {"n": 43}}'
    )
    initial = parser.feed_gmcp('Char.Vitals {"hp": "100", "maxhp": 120, "level": 2}')
    changed = parser.feed_gmcp('Char.Vitals {"hp": 90, "maxhp": 120, "level": 3}')
    duplicate = parser.feed_gmcp('Char.Vitals {"hp": 90, "maxhp": 120, "level": 3}')

    assert room[0].as_payload() == {
        "type": "room_entered",
        "source": "gmcp",
        "data": {
            "package": "Room.Info",
            "num": 42,
            "name": "Training Yard",
            "exits": {"n": 43},
        },
    }
    assert [event.type for event in initial] == ["health_changed", "vitals_changed"]
    assert [event.type for event in changed] == [
        "health_changed",
        "level_gained",
        "vitals_changed",
    ]
    assert changed[0].data["previous"] == 100
    assert changed[1].data == {
        "package": "Char.Vitals",
        "level": 3,
        "previous": 2,
    }
    assert duplicate == []


def test_gmcp_non_json_payload_is_preserved() -> None:
    parser = ObservationParser()

    events = parser.feed_gmcp("Core.Prompt ready>")

    assert events[0].data == {"package": "Core.Prompt", "value": "ready>"}


def test_real_dd4_text_fixture_produces_room_and_prompt_state() -> None:
    parser = ObservationParser()
    fixture = (Path(__file__).parent / "fixtures" / "dd4_room_prompt.txt").read_text(
        encoding="utf-8"
    )

    events = parser.feed_text(fixture)

    room = next(event for event in events if event.type == "room_entered")
    prompt = next(event for event in events if event.type == "prompt_seen")
    health = next(event for event in events if event.type == "health_changed")
    assert room.data["name"] == "The Temple Of Midgaard"
    assert room.data["exits"] == ["north", "south", "up"]
    assert prompt.data == {
        "text": "<60/60 hits 180/180 mana 160/160 move [Midgaard]>",
        "hits": 60,
        "max_hits": 60,
        "mana": 180,
        "max_mana": 180,
        "move": 160,
        "max_move": 160,
        "area": "Midgaard",
    }
    assert health.data["current"] == 60
    assert health.data["maximum"] == 60


def test_real_dd4_gmcp_fixture_maps_character_state_and_deduplicates_room() -> None:
    parser = ObservationParser()
    fixture_path = Path(__file__).parent / "fixtures" / "dd4_gmcp.txt"
    messages = fixture_path.read_text(encoding="utf-8").splitlines()

    events = [event for message in messages for event in parser.feed_gmcp(message)]
    types = [event.type for event in events]

    assert "character_identity_observed" in types
    assert "vitals_changed" in types
    assert "stats_changed" in types
    assert "progress_changed" in types
    assert "affects_changed" in types
    assert "inventory_changed" in types
    assert types.count("room_entered") == 1
    progress = next(event for event in events if event.type == "progress_changed")
    assert progress.data["level"] == "2"
    assert parser.feed_gmcp(messages[-1]) == []


def test_gmcp_room_enriches_a_text_room_without_reentering() -> None:
    parser = ObservationParser()
    text_fixture = (
        Path(__file__).parent / "fixtures" / "dd4_room_prompt.txt"
    ).read_text(encoding="utf-8")
    gmcp_room = (
        Path(__file__).parent / "fixtures" / "dd4_gmcp.txt"
    ).read_text(encoding="utf-8").splitlines()[-1]

    parser.feed_text(text_fixture)
    events = parser.feed_gmcp(gmcp_room)

    assert [event.type for event in events] == ["room_updated"]
    assert events[0].data["vnum"] == "3001"
