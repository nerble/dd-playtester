import pytest

from dd4tester.observations import GameEvent, ObservationParser
from dd4tester.state import CharacterState


def test_gmcp_fighting_position_marks_combat_without_text_opener() -> None:
    parser = ObservationParser()
    state = CharacterState(position=7)

    for event in parser.feed_gmcp('Char.Vitals {"position":"6","hp":"670"}'):
        state.apply(event)

    assert state.position == 6
    assert state.in_combat is True
    assert state.combat_target is None
    assert state.hp == 670
    assert CharacterState.from_dict(state.to_dict()).in_combat is True
    assert state.to_compact_dict()["in_combat"] is True


def test_nonempty_enemy_snapshot_marks_combat_without_guessing_target() -> None:
    state = CharacterState(position=7)
    enemies = [[{"name": "the Bartender", "isnpc": "30205", "hp": "478"}]]

    state.apply(GameEvent("enemies_changed", "gmcp", {"value": enemies}))

    assert state.in_combat is True
    assert state.enemies == enemies
    assert state.combat_target is None


def test_saved_live_fight_sequence_clears_combat_at_standing_update() -> None:
    # Sanitized ordering from run 16852: no text combat-start event was emitted.
    parser = ObservationParser()
    state = CharacterState()
    for message in (
        'Char.Vitals {"position":"7","hp":"767"}',
        'Char.Vitals {"position":"6","hp":"767"}',
        'Char.Enemies [[{"name":"the Bartender","isnpc":"30205",'
        '"hp":"478","maxhp":"594"}]]',
        'Char.Vitals {"position":"6","hp":"670"}',
    ):
        for event in parser.feed_gmcp(message):
            state.apply(event)

    assert state.in_combat is True
    assert state.position == 6

    for event in parser.feed_gmcp('Char.Vitals {"position":"7","hp":"530"}'):
        state.apply(event)

    assert state.in_combat is False
    assert state.combat_target is None


@pytest.mark.parametrize("position", [0, 1, 2, 3, 4, 5, 7, "4", "7"])
@pytest.mark.parametrize("event_type", ["vitals_changed", "posture_changed"])
def test_explicit_nonfighting_position_clears_combat(
    position: int | str, event_type: str,
) -> None:
    state = CharacterState(position=6, in_combat=True, combat_target="a dummy")

    state.apply(GameEvent(event_type, "gmcp", {"position": position}))

    assert state.in_combat is False
    assert state.combat_target is None


@pytest.mark.parametrize("position", [None, True, False, -1, 8, 6.5, "unknown"])
@pytest.mark.parametrize("event_type", ["vitals_changed", "posture_changed"])
def test_invalid_position_does_not_clear_observed_combat(
    position: object, event_type: str,
) -> None:
    state = CharacterState(position=6, in_combat=True, combat_target="a dummy")

    state.apply(GameEvent(event_type, "gmcp", {"position": position}))

    assert state.in_combat is True
    assert state.combat_target == "a dummy"


def test_partial_vitals_preserve_combat_until_positive_empty_enemy_snapshot() -> None:
    state = CharacterState(position=6, in_combat=True, combat_target="a dummy")

    state.apply(GameEvent("vitals_changed", "gmcp", {"hp": "530"}))
    assert state.in_combat is True
    assert state.combat_target == "a dummy"

    state.apply(GameEvent("enemies_changed", "gmcp", {"value": []}))
    assert state.in_combat is False
    assert state.combat_target is None


def test_partial_vitals_do_not_revive_combat_from_old_fighting_position() -> None:
    state = CharacterState(position=6, in_combat=True, combat_target="a dummy")
    state.apply(GameEvent("enemies_changed", "gmcp", {"value": []}))

    state.apply(GameEvent("vitals_changed", "gmcp", {"hp": "530"}))

    assert state.position == 6
    assert state.in_combat is False
    assert state.combat_target is None


def test_fighting_updates_preserve_observed_text_target() -> None:
    state = CharacterState()
    state.apply(GameEvent("combat_started", "text", {"target": "a dummy"}))

    state.apply(GameEvent("vitals_changed", "gmcp", {"position": "6"}))
    state.apply(GameEvent("enemies_changed", "gmcp", {"value": [{"name": "a dummy"}]}))

    assert state.in_combat is True
    assert state.combat_target == "a dummy"


@pytest.mark.parametrize("value", [None, "[]", {}, [[{"name": ""}]]])
def test_invalid_enemy_snapshot_preserves_observed_combat(value: object) -> None:
    state = CharacterState(position=6, in_combat=True, combat_target="a dummy")

    state.apply(GameEvent("enemies_changed", "gmcp", {"value": value}))

    assert state.in_combat is True
    assert state.combat_target == "a dummy"


def test_death_clears_combat_and_target() -> None:
    state = CharacterState(position=6, in_combat=True, combat_target="a dummy")

    state.apply(GameEvent("character_died", "text", {"text": "You have died."}))

    assert state.dead is True
    assert state.in_combat is False
    assert state.combat_target is None
