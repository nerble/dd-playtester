from dataclasses import replace

import pytest

from dd4tester.hunt_candidates import (
    ACT_AGGRESSIVE, ROOM_NO_RECALL, ExitSource, MobileSource, MobReset,
    RoomSource, WorldSource,
)
from dd4tester.recall_recovery import AdjacentRecallEscape, adjacent_recall_exit
from dd4tester.state import CharacterState


PROMPT = "<690/717 hits 291/273 mana 484/492 move [Underdark]> "


def source_case(tmp_path):
    (tmp_path / "test.are").write_text("#AREA test~ Test~\n20 60 0 100\n", encoding="utf-8")
    origin = RoomSource(100, "hallway", "test.are", room_flags=ROOM_NO_RECALL,
                        exits={"north": ExitSource("north", 101, 0, -1)})
    world = WorldSource(rooms={100: origin, 101: RoomSource(101, "hallway", "test.are")})
    return world


def state_case():
    return CharacterState(room_vnum="100", area="Test", level=30, position=7,
                          hp=690, max_hp=717, move=484, exits={"n": "101"})


def test_adjacent_recall_escape_requires_scan_step_and_exact_recall_confirmation():
    state = state_case()
    escape = AdjacentRecallEscape("100", "north", "101")
    assert escape.next_command(state, now=0) == "scan north"
    escape.observe("You can't see anything to the north.\n")
    assert escape.next_command(state, now=1) is None
    escape.observe(PROMPT)
    assert escape.next_command(state, now=2) == "north"
    state.room_vnum = "101"
    escape.observe(PROMPT)
    assert escape.next_command(state, now=3) == "recall"
    state.room_vnum = "3001"
    escape.observe(PROMPT)
    assert escape.next_command(state, now=4) is None
    assert escape.stage == "complete"
    assert escape.commands_sent == 3
    assert "can't see anything" in escape.evidence()["scan_response"]


def test_adjacent_recall_escape_accepts_temple_text_before_room_info():
    state = state_case()
    escape = AdjacentRecallEscape("100", "north", "101")
    assert escape.next_command(state, now=0) == "scan north"
    escape.observe("You can't see anything to the north.\n" + PROMPT)
    assert escape.next_command(state, now=1) == "north"
    state.room_vnum = "101"
    escape.observe(PROMPT)
    assert escape.next_command(state, now=2) == "recall"
    # The server's text parser has the old room until the later Room.Info
    # packet, but the canonical Temple header proves the recall arrived.
    state.room_vnum = "101"
    escape.observe("The Temple Of Midgaard\n" + PROMPT)
    assert escape.next_command(state, now=3) is None
    assert escape.stage == "complete"
    assert escape.failure is None


def test_adjacent_recall_escape_waits_for_authoritative_room_after_movement_prompt():
    state = state_case()
    escape = AdjacentRecallEscape("100", "north", "101")
    assert escape.next_command(state, now=0) == "scan north"
    escape.observe("You can't see anything to the north.\n" + PROMPT)
    assert escape.next_command(state, now=1) == "north"

    # The text prompt can arrive while CharacterState still has the origin;
    # the later Room.Info packet is the authoritative movement receipt.
    escape.observe("A quiet hallway.\n" + PROMPT)
    assert escape.next_command(state, now=2) is None
    assert escape.failure is None
    state.room_vnum = "101"
    assert escape.next_command(state, now=2.2) == "recall"


@pytest.mark.parametrize("reply", [
    "A demon who is one room to the north.",
    "A closed door right here to the north.",
    "It is pitch black...", "You can't see anything to the south.",
])
def test_adjacent_recall_escape_rejects_occupied_closed_or_incomplete_scan(reply):
    state = state_case()
    escape = AdjacentRecallEscape("100", "north", "101")
    escape.next_command(state, now=0)
    escape.observe(reply + "\n" + PROMPT)
    assert escape.next_command(state, now=1) is None
    assert escape.failure
    assert escape.commands_sent == 1


def test_adjacent_recall_escape_preserves_distant_scan_distance():
    state = state_case()
    escape = AdjacentRecallEscape("100", "north", "101")
    escape.next_command(state, now=0)
    escape.observe("A demon who is three rooms to the north.\n" + PROMPT)
    assert escape.next_command(state, now=1) == "north"


@pytest.mark.parametrize("change", ["wrong_exit", "combat", "low_health", "unknown_position", "wrong_room"])
def test_adjacent_recall_escape_stops_on_changed_live_state(change):
    state = state_case()
    if change == "wrong_exit":
        state.exits = {"north": "102"}
    elif change == "combat":
        state.in_combat = True
    elif change == "low_health":
        state.hp = 10
    elif change == "unknown_position":
        state.position = "unknown"
    else:
        state.room_vnum = "102"
    escape = AdjacentRecallEscape("100", "north", "101")
    assert escape.next_command(state, now=0) is None
    assert escape.failure
    assert escape.commands_sent == 0


def test_adjacent_recall_escape_times_out_without_retry():
    state = state_case()
    escape = AdjacentRecallEscape("100", "north", "101")
    escape.next_command(state, now=0)
    assert escape.next_command(state, now=5) is None
    assert "five seconds" in escape.failure
    assert escape.next_command(state, now=6) is None
    assert escape.commands_sent == 1


def test_adjacent_recall_plan_requires_source_default_midgaard(tmp_path):
    world = source_case(tmp_path)
    assert adjacent_recall_exit(world, tmp_path, "100", 30) == ("north", "101")
    (tmp_path / "test.are").write_text("#RECALL 27347\n", encoding="utf-8")
    assert adjacent_recall_exit(world, tmp_path, "100", 30) is None


def test_adjacent_recall_plan_never_bypasses_purgatory_corpse_recovery(tmp_path):
    world = source_case(tmp_path)
    world.rooms[100] = replace(world.rooms[100], area_file="purgator.are")
    assert adjacent_recall_exit(world, tmp_path, "100", 30) is None


@pytest.mark.parametrize("change", ["locked", "closed", "random", "no_recall", "air", "underwater", "aggressor"])
def test_adjacent_recall_plan_rejects_changed_source_destination(tmp_path, change):
    world = source_case(tmp_path)
    if change in {"locked", "closed"}:
        world.rooms[100].exits["north"] = ExitSource("north", 101, 4 if change == "locked" else 2, -1)
    elif change == "random":
        world.rooms[101] = replace(world.rooms[101], random_exits=True)
    elif change == "no_recall":
        world.rooms[101] = replace(world.rooms[101], room_flags=ROOM_NO_RECALL)
    elif change in {"air", "underwater"}:
        world.rooms[101] = replace(world.rooms[101], sector_type=9 if change == "air" else 8)
    else:
        world.mobiles[200] = MobileSource(200, "demon", "a demon", 30, ACT_AGGRESSIVE, 0, "test.are")
        world.mob_resets = [MobReset(200, 101, 1, ())]
    assert adjacent_recall_exit(world, tmp_path, "100", 30) is None
