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


def test_vitals_preserve_hunger_and_thirst_for_campaign_decisions() -> None:
    state = CharacterState()

    assert state.apply(
        GameEvent(
            "vitals_changed",
            "gmcp",
            {
                "hunger": "-10",
                "maxhunger": "48",
                "thirst": "6",
                "maxthirst": "48",
                "drunk": "-10",
                "maxdrunk": "48",
            },
        )
    )

    assert state.hunger == -10
    assert state.max_hunger == 48
    assert state.thirst == 6
    assert state.max_thirst == 48
    assert state.drunk == -10
    assert state.max_drunk == 48
    assert CharacterState.from_dict(state.to_dict()).hunger == -10


def test_quest_status_snapshot_tracks_level_gate() -> None:
    state = CharacterState()

    assert state.apply(
        GameEvent(
            "quest_status_changed",
            "gmcp",
            {
                "points": "3",
                "total_points": "7",
                "level_qp_required": "200",
                "level_qp_shortfall": "193",
                "status": "available",
            },
        )
    )

    assert state.quest_points == 3
    assert state.total_quest_points == 7
    assert state.quest_level_qp_required == 200
    assert state.quest_level_qp_shortfall == 193
    restored = CharacterState.from_dict(state.to_dict())
    assert restored.quest_level_qp_shortfall == 193


def test_recall_state_tracks_available_points_and_selected_index() -> None:
    state = CharacterState()

    assert state.apply(
        GameEvent(
            "recall_points_changed",
            "text",
            {
                "current": 2,
                "points": [
                    {
                        "index": 0,
                        "active": False,
                        "name": "Default recall",
                        "area": "Temple of Midgaard",
                    },
                    {
                        "index": 2,
                        "active": True,
                        "name": "Draagdim",
                        "area": "Draagdim",
                    },
                ],
            },
        )
    )
    assert state.current_recall == 2
    assert state.recall_points[1]["name"] == "Draagdim"
    assert state.recall_points_observed is True

    assert state.apply(
        GameEvent(
            "recall_selection_changed",
            "text",
            {"current": 0, "fallback": True},
        )
    )
    assert state.current_recall == 0
    assert CharacterState.from_dict(state.to_dict()).recall_points == state.recall_points


def test_text_posture_evidence_updates_position_without_gmcp_vitals() -> None:
    parser = ObservationParser()
    state = CharacterState(position=4)

    events = parser.feed_text("You wake and ready yourself for action.\n")
    for event in events:
        state.apply(event)

    assert state.position == 7


def test_text_score_prevents_stale_lower_gmcp_progress_regression() -> None:
    state = CharacterState()

    assert state.apply(
        GameEvent(
            "progress_changed",
            "gmcp",
            {"level": "20", "xp": "229913", "xptnl": "387"},
        )
    )
    assert state.apply(
        GameEvent(
            "progress_changed",
            "text",
            {
                "level": 20,
                "xp": 229913,
                "maxxp": 230300,
                "xptnl": 387,
            },
        )
    ) is True

    assert state.apply(
        GameEvent(
            "progress_changed",
            "gmcp",
            {"level": "20", "xp": "216813", "xptnl": "13487"},
        )
    ) is False
    assert state.xp == 229913
    assert state.xp_to_next_level == 387


def test_state_rejects_impossible_level_and_progress_values() -> None:
    state = CharacterState(
        level=16,
        xp=132332,
        max_xp=133600,
        xp_to_next_level=1268,
    )

    assert state.apply(
        GameEvent("level_gained", "gmcp", {"level": "106"})
    ) is False
    assert state.apply(
        GameEvent(
            "progress_changed",
            "gmcp",
            {
                "level": "106",
                "xp": "98627",
                "maxxp": "4096",
                "xptnl": "-94531",
            },
        )
    ) is False
    assert state.level == 16
    assert state.xp == 132332
    assert state.max_xp == 133600
    assert state.xp_to_next_level == 1268


def test_experience_loss_is_preserved_as_state_evidence() -> None:
    state = CharacterState(
        level=24,
        xp=365893,
        max_xp=366100,
        xp_to_next_level=207,
        progress={
            "level": 24,
            "xp": 365893,
            "maxxp": 366100,
            "xptnl": 207,
        },
    )

    assert state.apply(
        GameEvent(
            "experience_lost",
            "text",
            {"xp": 385, "text": "You flee from combat! You lose 385 exp."},
        )
    )

    assert state.xp_loss_observed is True
    assert state.xp_loss_total == 385
    assert state.xp == 365508
    assert state.max_xp == 366100
    assert state.xp_to_next_level == 592
    assert state.progress["xp"] == 365508
    assert state.progress["xptnl"] == 592
    assert CharacterState.from_dict(state.to_dict()).xp_loss_total == 385


def test_corrected_gmcp_snapshot_does_not_double_count_textual_loss() -> None:
    state = CharacterState(
        level=24,
        xp=365893,
        max_xp=366100,
        xp_to_next_level=207,
        progress_source="text",
    )

    assert state.apply(
        GameEvent(
            "experience_lost",
            "text",
            {"xp": 385, "text": "You flee from combat! You lose 385 exp."},
        )
    )
    assert state.apply(
        GameEvent(
            "progress_changed",
            "gmcp",
            {"level": "24", "xp": "365508", "xptnl": "592"},
        )
    )

    assert state.xp == 365508
    assert state.xp_to_next_level == 592
    assert state.xp_loss_total == 385
    assert state.progress_source == "gmcp"


def test_gmcp_snapshot_before_textual_loss_does_not_double_subtract() -> None:
    state = CharacterState(
        level=24,
        xp=365893,
        max_xp=366100,
        xp_to_next_level=207,
        progress_source="gmcp",
    )

    assert state.apply(
        GameEvent(
            "progress_changed",
            "gmcp",
            {"level": "24", "xp": "365508", "xptnl": "592"},
        )
    )
    assert state.apply(
        GameEvent(
            "experience_lost",
            "text",
            {"xp": 385, "text": "You recall from combat! You lose 385 exp."},
        )
    )

    assert state.xp == 365508
    assert state.xp_to_next_level == 592
    assert state.progress["xp"] == 365508
    assert state.progress["xptnl"] == 592
    assert state.xp_loss_total == 385


def test_textual_loss_updates_checkpoint_without_followup_worth_packet() -> None:
    parser = ObservationParser()
    state = replay_events(
        parser.feed_text(
            "You are level 24, have 364415 experience and need 1685 to level.\n"
            "You flee from combat! You lose 385 exp.\n"
        )
    )

    assert state.level == 24
    assert state.xp == 364030
    assert state.max_xp == 366100
    assert state.xp_to_next_level == 2070
    assert state.xp_loss_observed is True
    assert state.xp_loss_total == 385


def test_observed_death_allows_a_real_progress_regression() -> None:
    state = CharacterState(level=20, xp=229913)
    state.apply(GameEvent("character_died", "text", {"text": "You have died."}))

    assert state.apply(
        GameEvent(
            "progress_changed",
            "gmcp",
            {"level": "20", "xp": "216813", "xptnl": "13487"},
        )
    )
    assert state.xp == 216813


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

    assert state.apply(
        GameEvent(
            "enemies_changed",
            "gmcp",
            {"value": [[{"name": "Olog", "level": "4"}]]},
        )
    )
    assert state.enemies[0][0]["level"] == "4"

    assert state.apply(
        GameEvent("enemies_changed", "gmcp", {"value": []})
    )
    assert state.enemies == []
    assert state.in_combat is False
    assert state.combat_target is None

    assert state.apply(
        GameEvent(
            "equipment_changed",
            "gmcp",
            {
                "value": {
                    "equipment": {
                        "head": {"id": 3706, "name": "a steel barrel-helm"}
                    }
                }
            },
        )
    )
    assert state.equipment["equipment"]["head"]["id"] == 3706


def test_text_room_transition_clears_a_stale_gmcp_vnum() -> None:
    state = CharacterState(room_name="Safety", room_vnum="3737")

    assert state.apply(
        GameEvent(
            "room_entered",
            "text",
            {"name": "The Entrance to the Mud School", "exits": ["east", "south"]},
        )
    )

    assert state.room_name == "The Entrance to the Mud School"
    assert state.room_vnum is None

    assert state.apply(GameEvent("character_died", "text", {"text": "You have died."}))
    assert state.dead is True
    assert state.in_combat is False
    assert state.combat_target is None


def test_text_room_exits_preserve_gmcp_destinations() -> None:
    state = CharacterState()

    assert state.apply(
        GameEvent(
            "room_entered",
            "gmcp",
            {
                "name": "Mirrors",
                "vnum": "19040",
                "exits": {
                    "n": "19039",
                    "e": "19041",
                    "s": "19036",
                    "w": "19038",
                },
            },
        )
    )

    assert state.apply(
        GameEvent(
            "room_entered",
            "text",
            {
                "name": "Mirrors",
                "vnum": "19040",
                "exits": ["north", "east", "south", "west"],
            },
        )
    )

    assert state.exits == {
        "north": "19039",
        "east": "19041",
        "south": "19036",
        "west": "19038",
    }


def test_delayed_text_room_cannot_move_state_backward() -> None:
    state = CharacterState(
        room_name="The Corner of the Wooden Path",
        room_vnum="19091",
        exits={"e": "19092", "s": "19090"},
    )

    assert state.apply(
        GameEvent(
            "room_entered",
            "text",
            {
                "name": "The Wooden Path",
                "vnum": "19090",
                "exits": ["north", "east", "south", "west"],
            },
        )
    ) is False

    assert state.room_vnum == "19091"
    assert state.exits == {"e": "19092", "s": "19090"}


def test_inferred_text_room_transition_can_replace_stale_gmcp_vnum() -> None:
    state = CharacterState(
        room_name="A crevice",
        room_vnum="137",
        area="Gremlin Lair",
    )

    assert state.apply(
        GameEvent(
            "room_entered",
            "text",
            {
                "name": "The Temple Of Midgaard",
                "vnum": "3001",
                "vnum_inferred": True,
                "exits": ["north", "south", "up"],
            },
        )
    )

    assert state.room_name == "The Temple Of Midgaard"
    assert state.room_vnum == "3001"


def test_leaving_purgatory_clears_persisted_death_state() -> None:
    state = CharacterState(area="Purgatory", room_vnum="427", dead=True)

    assert state.apply(
        GameEvent(
            "room_entered",
            "gmcp",
            {
                "name": "By the Temple Altar",
                "vnum": "3054",
                "area": "Midgaard",
                "flags": "safe healing",
            },
        )
    )

    assert state.dead is False
    assert state.room_vnum == "3054"


def test_midgaard_prompt_clears_death_before_gmcp_room_update() -> None:
    state = CharacterState(area="Purgatory", room_vnum="427", dead=True)

    assert state.apply(
        GameEvent(
            "room_entered",
            "text",
            {"name": "By the Temple Altar", "exits": ["east", "south", "up"]},
        )
    )
    assert state.dead is True
    assert state.apply(
        GameEvent(
            "prompt_seen",
            "text",
            {"area": "Midgaard", "hits": 1, "max_hits": 334},
        )
    )

    assert state.dead is False
    assert state.area == "Midgaard"
