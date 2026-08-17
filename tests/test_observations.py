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

    assert [event.type for event in events] == [
        "level_gained",
        "prompt_seen",
        "health_changed",
    ]
    assert parser.flush_text() == []


def test_text_observations_track_sleep_and_wake_posture() -> None:
    parser = ObservationParser()

    sleeping = parser.feed_text("You sleep.\n")
    waking = parser.feed_text("You wake and ready yourself for action.\n")

    assert sleeping[0].as_payload() == {
        "type": "posture_changed",
        "source": "text",
        "data": {"position": 4, "text": "You sleep."},
    }
    assert waking[0].data["position"] == 7


def test_text_score_reports_authoritative_progress_and_currency() -> None:
    parser = ObservationParser()

    events = parser.feed_text(
        "You are level 20, have 229913 experience and need 387 to level.\n"
        "Coin:  Platinum: 24  Gold: 277  Silver: 9  Copper: 3\n"
    )

    progress = [event for event in events if event.type == "progress_changed"]
    assert progress[0].data == {
        "level": 20,
        "xp": 229913,
        "maxxp": 230300,
        "xptnl": 387,
        "text": "You are level 20, have 229913 experience and need 387 to level.",
    }
    assert progress[1].data == {
        "platinum": 24,
        "gold": 277,
        "silver": 9,
        "copper": 3,
    }


def test_text_flee_reports_authoritative_experience_loss() -> None:
    parser = ObservationParser()

    events = parser.feed_text(
        "You flee from combat! You lose 385 exp. "
        "However, you damaged your opponent sufficiently for 7 experience.\n"
    )

    assert [event.type for event in events] == ["experience_lost"]
    assert events[0].data == {
        "xp": 385,
        "text": (
            "You flee from combat! You lose 385 exp. "
            "However, you damaged your opponent sufficiently for 7 experience."
        ),
    }


def test_duplicate_login_snapshot_is_discarded_until_next_room_update() -> None:
    parser = ObservationParser()

    assert parser.feed_gmcp(
        'Room.Info {"name":"By the Temple Altar","vnum":"3054",'
        '"arrival":{"kind":"login"}}'
    )
    assert parser.feed_gmcp(
        'Char.Worth {"level":"20","xp":"229913","xptnl":"387"}'
    )

    assert parser.feed_gmcp(
        'Room.Info {"name":"By \\u0000\\u0000","vnum":"3054",'
        '"arrival":{"kind":"login"}}'
    ) == []
    assert parser.feed_gmcp(
        'Char.Worth {"level":"20","xp":"216813","xptnl":"13487"}'
    ) == []
    assert parser.feed_gmcp(
        'Char.Items [[{"quan":"1","short_desc":"a stale item"}]]'
    ) == []

    room = parser.feed_gmcp(
        'Room.Info {"name":"The Temple Of Midgaard","vnum":"3001",'
        '"arrival":{"kind":"walk"}}'
    )
    assert room[0].type == "room_entered"
    progress = parser.feed_gmcp(
        'Char.Worth {"level":"20","xp":"229914","xptnl":"386"}'
    )
    assert progress[0].data["xp"] == "229914"


def test_first_login_room_info_enriches_text_room_before_duplicate_guard() -> None:
    parser = ObservationParser()

    text_room = parser.feed_text("Room: By the Temple Altar\n")
    assert text_room[0].type == "room_entered"

    room = parser.feed_gmcp(
        'Room.Info {"name":"By the Temple Altar","vnum":"3054",'
        '"arrival":{"kind":"login"}}'
    )
    assert room[0].type == "room_updated"
    assert room[0].data["vnum"] == "3054"

    assert parser.feed_gmcp(
        'Room.Info {"name":"By \\u0000\\u0000","vnum":"3054",'
        '"arrival":{"kind":"login"}}'
    ) == []


def test_complete_dd4_prompt_is_not_held_behind_gmcp_only_traffic() -> None:
    parser = ObservationParser()

    events = parser.feed_text(
        "The steep foothills\n"
        "<205/205 hits 207/207 mana 247/280 move [Plains of the North]>"
    )
    gmcp_events = parser.feed_gmcp(
        'Room.Info {"area":"Plains of the North","vnum":"324"}'
    )

    assert [event.type for event in events] == [
        "prompt_seen",
        "health_changed",
    ]
    assert [event.type for event in gmcp_events] == ["room_entered"]
    assert parser.flush_text() == []


def test_text_observations_recognize_existing_room_combat() -> None:
    parser = ObservationParser()

    events = parser.feed_text(
        "Muddy Tunnel\n"
        "Olog is here, fighting YOU!\n"
    )

    combat = [event for event in events if event.type == "combat_started"]
    assert combat[0].data["target"] == "Olog"


def test_experience_reward_is_not_recorded_as_an_item() -> None:
    parser = ObservationParser()

    events = parser.feed_text(
        "You receive 153 experience points for the kill.\n"
        "You receive a snowy white stone.\n"
    )

    assert [event.type for event in events] == ["item_acquired"]
    assert events[0].data["item"] == "snowy white stone"


def test_purchase_is_recorded_as_an_item_acquisition() -> None:
    parser = ObservationParser()

    events = parser.feed_text("The weaponsmith nods solemnly at you.\nYou buy a dagger.\n")

    acquisitions = [event for event in events if event.type == "item_acquired"]
    assert len(acquisitions) == 1
    assert acquisitions[0].data["item"] == "dagger"


def test_purchase_preserves_item_quantity() -> None:
    parser = ObservationParser()

    events = parser.feed_text("You buy 3 big pot pies.\n")

    assert events[0].type == "item_acquired"
    assert events[0].data == {
        "item": "big pot pies",
        "quantity": 3,
        "text": "You buy 3 big pot pies.",
    }


def test_room_atmosphere_is_not_recorded_as_an_item() -> None:
    parser = ObservationParser()

    events = parser.feed_text(
        "As you enter the mine shaft, you get a sudden fear of the walls closing.\n"
    )

    assert [event for event in events if event.type == "item_acquired"] == []


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


def test_gmcp_enemy_snapshot_is_preserved() -> None:
    parser = ObservationParser()

    events = parser.feed_gmcp(
        'Char.Enemies [ [ { "name": "Olog", "level": "4", "hp": "48" } ] ]'
    )

    assert [event.type for event in events] == ["enemies_changed"]
    assert events[0].data["value"][0][0]["name"] == "Olog"


def test_gmcp_equipment_snapshot_is_preserved() -> None:
    parser = ObservationParser()

    events = parser.feed_gmcp(
        'Char.Equipment {"equipment":{"head":{"id":3706,'
        '"name":"a steel barrel-helm"}}}'
    )

    assert [event.type for event in events] == ["equipment_changed"]
    assert events[0].data["equipment"]["head"]["id"] == 3706


def test_gmcp_worn_snapshot_is_preserved_as_equipment() -> None:
    parser = ObservationParser()

    events = parser.feed_gmcp(
        'Char.Worn [{"slot":"wield","wear_loc":16,'
        '"vnum":3020,"name":"a dagger"}]'
    )

    assert [event.type for event in events] == ["equipment_changed"]
    assert events[0].data["package"] == "Char.Worn"
    assert events[0].data["value"][0]["vnum"] == 3020


def test_gmcp_targetmode_inventory_descriptions_preserve_exact_instance_id() -> None:
    parser = ObservationParser()

    events = parser.feed_gmcp(
        'Char.Items [[{"quan":"1",'
        '"short_desc":"[#18446744073709551615] a notched scimitar"}]]'
    )

    assert [event.type for event in events] == ["inventory_changed"]
    item = events[0].data["value"][0][0]
    assert item == {
        "quan": "1",
        "short_desc": "a notched scimitar",
        "target_id": "18446744073709551615",
        "target_selector": "#18446744073709551615",
    }


def test_gmcp_targetmode_equipment_and_item_add_are_normalized() -> None:
    parser = ObservationParser()

    equipment = parser.feed_gmcp(
        'Char.Equipment {"equipment":{"wield":{'
        '"short_desc":"[#4871] a notched scimitar"}}}'
    )
    acquired = parser.feed_gmcp(
        'Char.Items.Add {"location":"inv","item":{'
        '"short_desc":"[#4872] a purple potion"}}'
    )

    wielded = equipment[0].data["equipment"]["wield"]
    assert wielded["short_desc"] == "a notched scimitar"
    assert wielded["target_id"] == "4871"
    assert wielded["target_selector"] == "#4871"
    item = acquired[0].data["item"]
    assert item["short_desc"] == "a purple potion"
    assert item["target_id"] == "4872"
    assert item["target_selector"] == "#4872"


def test_gmcp_unprefixed_item_descriptions_are_unchanged() -> None:
    parser = ObservationParser()

    events = parser.feed_gmcp(
        'Char.Items [[{"quan":"2","short_desc":"a big pot pie"}]]'
    )

    assert events[0].data["value"][0][0] == {
        "quan": "2",
        "short_desc": "a big pot pie",
    }


def test_connection_reset_reemits_snapshots_and_discards_partial_text() -> None:
    parser = ObservationParser()
    inventory = (
        'Char.Items [[{"quan":"1",'
        '"short_desc":"[#4871] a notched scimitar"}]]'
    )

    assert parser.feed_text("stale partial") == []
    assert [event.type for event in parser.feed_gmcp(inventory)] == [
        "inventory_changed"
    ]
    assert parser.feed_gmcp(inventory) == []

    parser.reset_connection()

    assert parser.feed_text("fresh line\n") == []
    events = parser.feed_gmcp(inventory)
    assert [event.type for event in events] == ["inventory_changed"]
    assert events[0].data["value"][0][0]["target_selector"] == "#4871"


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


def test_text_room_header_strips_a_concatenated_dd4_prompt() -> None:
    parser = ObservationParser()

    events = parser.feed_text(
        "<47/73 hits 100/107 mana 120/160 move [Mud School]> "
        "Advanced Combat Training\n"
        "[Exits: east]\n"
    )

    assert len(events) == 1
    assert events[0].type == "room_entered"
    assert events[0].data["name"] == "Advanced Combat Training"
