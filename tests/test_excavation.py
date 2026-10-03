from dataclasses import replace

import pytest

from dd4tester.excavation import (
    DigObservation, HoardDigSession, maximum_hoard_direct_damage, tool_dig_budget,
)
from dd4tester.hunt_candidates import ObjectSource


SHOVEL = ObjectSource(3604, "shovel", "a shovel", 6, (25, 16, 39, 83), 0)
PROMPT = "<666/666 hits 261/261 mana 482/482 move [Plains]> "
IDENTITY = (10001, 309, 586)


def budget(**changes):
    options = dict(
        sector_type=2, race="dwarf", level=29, observed_tool_level=10,
        strength=30, constitution=25, dexterity=16, swiftness=5,
        enhanced_swiftness_percent=0,
    )
    options.update(changes)
    return tool_dig_budget(SHOVEL, **options)


def observed(**changes):
    return replace(DigObservation(1, IDENTITY, 309, 3604, 666, 482, False, 0, True, True, budget()), **changes)


def session():
    return HoardDigSession(budget(), quest_identity=IDENTITY, minimum_hp=400, return_movement=30)


@pytest.mark.parametrize("sector,digs,movement", [(2, 5, 115), (0, 8, 688), (1, 9, 918)])
def test_tool_budget_includes_load_and_use_fuzz(sector, digs, movement):
    result = budget(sector_type=sector)
    assert result.maximum_digs == digs
    assert result.maximum_movement == movement
    assert result.maximum_wait_seconds == result.maximum_wait_pulses / 4


@pytest.mark.parametrize("changes", [
    {"sector_type": 6}, {"sector_type": 9}, {"sector_type": 13},
    {"swiftness": 50000}, {"swiftness": None}, {"strength": True},
    {"observed_tool_level": 30}, {"dexterity": 32}, {"constitution": 0},
    {"depth": 201},
    {"enhanced_swiftness_percent": None}, {"enhanced_swiftness_percent": 101},
])
def test_unknown_or_illegal_digging_inputs_are_not_estimates(changes):
    with pytest.raises(ValueError):
        budget(**changes)


def test_race_affects_budget_and_slow_is_applied_after_racial_wait_bonus():
    dwarf = budget(sector_type=0)
    human = budget(sector_type=0, race="human")
    assert dwarf.maximum_movement < human.maximum_movement
    assert dwarf.maximum_digs < human.maximum_digs
    assert budget(sector_type=0, slow=True).maximum_wait_pulses > dwarf.maximum_wait_pulses
    assert budget(sector_type=0, haste=True).maximum_wait_pulses < dwarf.maximum_wait_pulses


def test_room_wide_physical_trap_uses_full_positive_armor_class():
    assert maximum_hoard_direct_damage(29, 100) == 390
    assert maximum_hoard_direct_damage(29, -17) == 286
    assert maximum_hoard_direct_damage(29, -1000) == 174
    with pytest.raises(ValueError):
        maximum_hoard_direct_damage(29, 50000)


def test_wire_swiftness_already_contains_dex_and_skill_bonus():
    skilled = budget(sector_type=0, dexterity=30, swiftness=25, enhanced_swiftness_percent=80)
    unskilled = budget(sector_type=0, dexterity=30, swiftness=5)
    assert skilled.maximum_wait_pulses == unskilled.maximum_wait_pulses == 18


def test_dig_is_response_driven_and_unearthing_does_not_claim_pickup():
    digging = session()
    assert digging.poll(observed(), now=0).command == "dig"
    digging.observe("You dig into the earth with a shovel...")
    assert digging.poll(observed(sequence=2, movement=459), now=2).command is None
    digging.observe(PROMPT)
    assert digging.poll(observed(sequence=2, movement=459), now=2).command == "dig"
    digging.observe(PROMPT + "With a final effortful thrust, you unearth something!" + PROMPT)
    assert digging.poll(observed(sequence=3, movement=436), now=4).status == "unearthed"
    assert digging.commands == 2
    assert digging.poll(observed(sequence=4), now=20).command is None


def test_no_command_queue_while_lagging_or_waiting_for_fresh_state():
    digging = session()
    digging.poll(observed(), now=0)
    digging.observe("You dig into the earth with a shovel..." + PROMPT)
    assert digging.poll(observed(sequence=2), now=0.1).command is None
    assert digging.poll(observed(), now=2).command is None
    assert digging.poll(observed(), now=20).status == "stopped"
    assert digging.commands == 1


@pytest.mark.parametrize("text", [
    "You hear a strange noise...",
    "You're too exhausted to dig.",
    "You dig into the earth... but get the feeling you're wasting your time.",
])
def test_trap_refusal_and_futility_stop_without_another_dig(text):
    digging = session()
    digging.poll(observed(), now=0)
    for chunk in (text[:12], text[12:]):
        digging.observe(chunk)
    assert digging.poll(observed(sequence=2), now=2).status == "stopped"
    digging.observe("With a final effortful thrust, you unearth something!" + PROMPT)
    assert digging.poll(observed(sequence=3), now=3).status == "stopped"
    assert digging.commands == 1


@pytest.mark.parametrize("changes", [
    {"room_vnum": 310}, {"tool_vnum": 99}, {"quest_active": False},
    {"quest_identity": (10001, 309, 587)}, {"hp": 399}, {"movement": 144},
    {"in_combat": True}, {"occupants": 1}, {"standing": False},
    {"hp": float("nan")}, {"quest_active": "yes"}, {"occupants": -1},
    {"current_budget": None},
])
def test_changed_state_stops_before_dig(changes):
    digging = session()
    assert digging.poll(observed(**changes), now=0).status == "stopped"
    assert digging.commands == 0


def test_source_budget_closes_silent_absence_even_without_futility_text():
    digging = session()
    for index in range(5):
        result = digging.poll(observed(sequence=index + 1, movement=482 - index * 23), now=index * 2)
        assert result.command == "dig"
        digging.observe("You dig into the earth with a shovel..." + PROMPT)
    assert digging.poll(observed(sequence=6, movement=367), now=10).status == "stopped"
    assert digging.commands == 5


@pytest.mark.parametrize("reply", [
    "Someone says 'With a final effortful thrust, you unearth something!'",
    "You dig into the earth with another shovel...",
])
def test_quoted_or_wrong_tool_reply_is_not_progress(reply):
    digging = session()
    digging.poll(observed(), now=0)
    digging.observe(reply + PROMPT)
    assert digging.poll(observed(sequence=2), now=2).command is None
    assert digging.poll(observed(sequence=3), now=20).status == "stopped"
    assert digging.commands == 1


def test_response_overflow_is_a_persistable_failure_not_a_buffer_rewind():
    digging = session()
    digging.poll(observed(), now=0)
    digging.observe("x" * 8193)
    assert digging.poll(observed(sequence=2), now=2).status == "stopped"
    audit = digging.audit()
    assert audit["commands"] == 1
    assert audit["quest_identity"] == IDENTITY
    assert audit["quest_object_acquired"] is False
    assert "buffer" in audit["reason"]


def test_changed_stats_or_buffs_do_not_continue_with_an_old_budget():
    digging = session()
    digging.poll(observed(), now=0)
    digging.observe("You dig into the earth with a shovel..." + PROMPT)
    slower = budget(slow=True)
    assert digging.poll(observed(sequence=2, current_budget=slower), now=2).status == "stopped"
    assert digging.commands == 1
