from pathlib import Path

from dd4tester.observations import GameEvent, ObservationParser
from dd4tester.state import CharacterState, replay_events


def test_replays_real_dd4_observations_into_character_state() -> None:
    parser = ObservationParser()
    fixture = Path(__file__).parent / "fixtures" / "dd4_gmcp.txt"
    events = [
        event
        for message in fixture.read_text(encoding="utf-8").splitlines()
        for event in parser.feed_gmcp(message)
    ]

    state = replay_events(events)

    assert state.name == "FixtureGuy"
    assert state.race == "Human"
    assert state.character_class == "Mage"
    assert state.level == 2
    assert state.xp == 2300
    assert state.xp_to_next_level == 1700
    assert state.hp == 60
    assert state.max_hp == 60
    assert state.mana == 180
    assert state.room_name == "The Temple Of Midgaard"
    assert state.room_vnum == "3001"
    assert state.exits == {"n": "3054", "s": "3005", "u": "3725"}
    assert state.stats["int"] == 20
    assert state.currencies["gold"] == 4
    assert state.inventory == [[[]]]
    assert state.revision == 8
    assert CharacterState.from_dict(state.to_dict()).to_dict() == state.to_dict()


def test_state_changes_only_when_event_changes_domain_state() -> None:
    state = CharacterState()
    room = GameEvent(
        "room_entered",
        "gmcp",
        {
            "name": "Training Yard",
            "vnum": "42",
            "area": "Academy",
            "exits": {"n": "43"},
        },
    )

    assert state.apply(room) is True
    assert state.apply(room) is False
    assert state.revision == 1

    assert state.apply(
        GameEvent(
            "room_updated",
            "gmcp",
            {
                "name": "Training Yard",
                "vnum": "42",
                "area": "Academy",
                "flags": "safe indoors",
                "exits": {"n": "43"},
            },
        )
    )
    assert state.room_flags == ["safe", "indoors"]

    assert state.apply(
        GameEvent("combat_started", "text", {"target": "a practice dummy"})
    )
    assert state.in_combat is True
    assert state.combat_target == "a practice dummy"

    assert state.apply(GameEvent("character_died", "text", {"text": "You have died."}))
    assert state.dead is True
    assert state.in_combat is False
    assert state.combat_target is None
