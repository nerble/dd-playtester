import asyncio
import time

import pytest

from dd4tester.character import CharacterSpec
from dd4tester.connection import ReadResult
from dd4tester.fastwalks import route_named
from dd4tester.observations import GameEvent
from dd4tester.starter import (
    StarterBotRunner,
    StarterPolicy,
    _max_consecutive_command,
)
from dd4tester.state import CharacterState


def _spec(**overrides: object) -> CharacterSpec:
    values: dict[str, object] = {
        "name": "Rulemage",
        "race": "human",
        "gender": "female",
        "class": "mage",
        "subclass": "warlock",
        "minimum_primary_stat": 16,
        "max_attribute_rolls": 2,
    }
    values.update(overrides)
    return CharacterSpec.from_mapping(values)


def _respond(
    policy: StarterPolicy,
    state: CharacterState,
    text: str,
) -> tuple[str, bool]:
    policy.observe_text(text)
    decision = policy.next_decision(state)
    assert decision is not None
    result = (decision.command, decision.secret)
    policy.after_command(decision)
    return result


def test_creation_policy_follows_configured_character_profile() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    state = CharacterState()
    prompts = [
        ("Enter thy Name:", ("Rulemage", False)),
        ("Did I get that right, Rulemage? [y/n]", ("y", False)),
        ("Give me a password for Rulemage:", ("swordfish", True)),
        ("Please retype the password:", ("swordfish", True)),
        ("Do you want to enable colour? [y/n]", ("y", False)),
        ("Press [Enter] to create your character.", ("", False)),
        ("Please choose a race for your character. [a-y]", ("a", False)),
        ("Are you sure you want to choose this race? [y/n]", ("y", False)),
        ("Male, female or neuter? [m/f/n]", ("f", False)),
        ("Are you sure you want this gender? [y/n]", ("y", False)),
        ("Please choose a class for your character:", ("mage", False)),
        ("Are you sure you want this class? [y/n]", ("y", False)),
        (
            "Press ENTER to begin rolling your character's attributes.",
            ("", False),
        ),
    ]

    for prompt, expected in prompts:
        assert _respond(policy, state, prompt) == expected

    assert _respond(
        policy,
        state,
        "Str: 14 Int: 15 Wis: 16 Dex: 13 Con: 13\nAccept? [y/n]",
    ) == ("n", False)
    assert _respond(
        policy,
        state,
        "Str: 12 Int: 14 Wis: 14 Dex: 12 Con: 12\nAccept? [y/n]",
    ) == ("y", False)
    assert policy.roll_count == 2
    assert _respond(
        policy,
        state,
        "Character generation complete. You are now ready to enter.",
    ) == ("", False)
    assert policy.awaiting_reconnect is True


def test_existing_character_login_enters_world() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    state = CharacterState()

    assert _respond(policy, state, "Enter thy Name:") == ("Rulemage", False)
    assert _respond(policy, state, "Password:") == ("swordfish", True)
    assert _respond(
        policy,
        state,
        "To Enter the Dragons Domain press <Return>.",
    ) == ("", False)

    state.apply(
        GameEvent(
            "room_entered",
            "gmcp",
            {"name": "The Temple Of Midgaard", "vnum": "3001"},
        )
    )
    prompt = GameEvent("prompt_seen", "gmcp", {"package": "Core.Prompt"})
    state.apply(prompt)
    policy.observe_events([prompt], state)

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "up"
    assert policy.in_world is True


def test_course_policy_asks_imp_then_follows_direction() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.course_started = True
    state = CharacterState()
    room = GameEvent(
        "room_entered",
        "gmcp",
        {
            "name": "Obstacle Course",
            "vnum": "3705",
            "exits": {"e": "3706", "s": "3704"},
        },
    )
    prompt = GameEvent("prompt_seen", "gmcp", {"package": "Core.Prompt"})
    state.apply(room)
    state.apply(prompt)
    policy.observe_events([room, prompt], state)

    decision = policy.next_decision(state)
    assert decision is not None
    assert decision.command == "look imp"
    policy.after_command(decision)

    policy.observe_text("The Imp motions you to head EAST along the tunnel.")
    policy.prompt_ready = True
    decision = policy.next_decision(state)
    assert decision is not None
    assert decision.command == "open east"
    policy.after_command(decision)

    policy.prompt_ready = True
    decision = policy.next_decision(state)
    assert decision is not None
    assert decision.command == "east"


def test_level_two_course_graduate_saves_then_quits() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.course_started = True
    policy.course_complete = True
    policy.provisioned = True
    policy.practiced = True
    state = CharacterState(level=2, room_name="The Entrance to the Mud School")
    policy.prompt_ready = True

    save = policy.next_decision(state)
    assert save is not None
    assert save.command == "save"
    policy.after_command(save)
    policy.prompt_ready = True

    quit_decision = policy.next_decision(state)
    assert quit_decision is not None
    assert quit_decision.command == "quit"
    policy.after_command(quit_decision)

    assert policy.done is True


def test_end_of_course_uses_portal_exit() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    state = CharacterState(
        room_name="End of the Obstacle Course",
        room_vnum="3710",
    )
    room = GameEvent(
        "room_entered",
        "gmcp",
        {"name": state.room_name, "vnum": state.room_vnum, "exits": {}},
    )
    prompt = GameEvent("prompt_seen", "gmcp", {"package": "Core.Prompt"})
    policy.observe_events([room, prompt], state)
    policy.room_query_counts["3710"] = 1

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "enter portal"
    assert policy.course_started is True


def test_tutorial_stands_after_position_rejection() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.course_started = True
    policy.prompt_ready = True
    policy.observe_text("Nah... You feel too relaxed...")
    state = CharacterState(
        room_name="End of the Obstacle Course",
        room_vnum="3710",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "stand"


def test_low_health_final_combat_retreats_to_sanctuary() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.course_started = True
    policy.prompt_ready = True
    state = CharacterState(
        hp=3,
        max_hp=60,
        room_name="Final Combat",
        room_vnum="3722",
        exits={"n": "3723", "s": "3716"},
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "south"
    assert "Sanctuary" in decision.reason


def test_sanctuary_waits_for_healing_then_stands() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.course_started = True
    policy.prompt_ready = True
    state = CharacterState(
        hp=10,
        max_hp=60,
        room_name="Sanctuary",
        room_vnum="3721",
    )

    sleep = policy.next_decision(state)
    assert sleep is not None
    assert sleep.command == "sleep"
    policy.after_command(sleep)

    policy.prompt_ready = True
    assert policy.next_decision(state) is None

    state.hp = 40
    policy.prompt_ready = True
    stand = policy.next_decision(state)
    assert stand is not None
    assert stand.command == "stand"


def test_general_supplies_provisions_before_leaving() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.course_started = True
    policy.course_complete = True
    state = CharacterState(
        hp=1,
        max_hp=60,
        level=2,
        room_name="General Supplies",
        room_vnum="3724",
    )

    commands = []
    for _index in range(6):
        policy.prompt_ready = True
        decision = policy.next_decision(state)
        assert decision is not None
        commands.append(decision.command)
        policy.after_command(decision)

    assert commands == [
        "list",
        "buy 3 pie",
        "buy skin",
        "eat pie",
        "drink skin",
        "down",
    ]
    assert policy.provisioned is True


def test_low_health_entrance_routes_to_temple_healer() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.course_complete = True
    policy.provisioned = True
    policy.prompt_ready = True
    state = CharacterState(
        hp=1,
        max_hp=60,
        level=2,
        room_name="The Entrance to the Mud School",
        room_vnum="3725",
        exits={"d": "3001"},
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "down"
    assert "Sanctuary" in decision.reason


def test_combat_center_routes_to_required_side_room() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.course_started = True
    policy.prompt_ready = True
    state = CharacterState(
        hp=60,
        max_hp=60,
        room_name="Combat Training",
        room_vnum="3712",
        exits={"e": "3713", "n": "3715", "s": "3721", "w": "3714"},
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "open east"


def test_training_room_identifies_and_fights_opponent() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.course_started = True
    state = CharacterState(
        hp=60,
        max_hp=60,
        room_name="Combat Training Cage",
        room_vnum="3713",
        exits={"w": "3712"},
    )
    policy.text = "A large wolf is chained to a peg.\n"
    room = GameEvent(
        "room_entered",
        "gmcp",
        {
            "name": state.room_name,
            "vnum": state.room_vnum,
            "exits": state.exits,
        },
    )
    prompt = GameEvent("prompt_seen", "gmcp", {"package": "Core.Prompt"})
    policy.observe_events([room, prompt], state)

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "kill wolf"
    assert policy.combat_active is True


def test_training_room_tracks_two_targets_and_loots_each() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.course_started = True
    policy.current_room = "3713"
    policy.room_targets["3713"] = ["wolf", "large snake"]
    policy.active_target = "wolf"
    policy.combat_active = True
    policy.observe_text("The wolf is DEAD!! You receive 100 experience points.")
    policy.prompt_ready = True
    state = CharacterState(
        hp=60,
        max_hp=60,
        room_name="Combat Training",
        room_vnum="3713",
        exits={"w": "3712"},
    )

    loot = policy.next_decision(state)
    assert loot is not None
    assert loot.command == "get all corpse"
    policy.after_command(loot)
    policy.prompt_ready = True

    wear = policy.next_decision(state)
    assert wear is not None
    assert wear.command == "wear all"
    policy.after_command(wear)
    policy.prompt_ready = True

    second_fight = policy.next_decision(state)
    assert second_fight is not None
    assert second_fight.command == "kill snake"


def test_training_room_parses_descriptive_dd4_mob_lines() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.course_started = True
    state = CharacterState(
        hp=60,
        max_hp=60,
        room_name="Combat Training",
        room_vnum="3714",
        exits={"e": "3712"},
    )
    policy.text = (
        "A mountain lion spits and scratches at you.\n"
        "A wild dog barks and growls.\n"
    )
    room = GameEvent(
        "room_entered",
        "gmcp",
        {
            "name": state.room_name,
            "vnum": state.room_vnum,
            "exits": state.exits,
        },
    )
    prompt = GameEvent("prompt_seen", "gmcp", {"package": "Core.Prompt"})
    policy.observe_events([room, prompt], state)

    decision = policy.next_decision(state)

    assert policy.room_targets["3714"] == ["mountain lion", "wild dog"]
    assert decision is not None
    assert decision.command == "kill lion"


def test_resumed_room_extracts_targets_without_new_room_event() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.course_started = True
    policy.current_room = "3714"
    policy.prompt_ready = True
    policy.observe_text(
        "A mountain lion spits and scratches at you.\n"
        "A wild dog barks and growls.\n"
    )
    state = CharacterState(
        hp=60,
        max_hp=60,
        room_name="Combat Training",
        room_vnum="3714",
        exits={"e": "3712"},
    )

    decision = policy.next_decision(state)

    assert policy.room_targets["3714"] == ["mountain lion", "wild dog"]
    assert decision is not None
    assert decision.command == "kill lion"


def test_combat_death_narration_does_not_add_false_target() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.current_room = "3713"
    policy.room_targets["3713"] = ["wolf"]
    policy.active_target = "wolf"
    policy.combat_active = True

    policy.observe_text(
        "A wolf is DEAD!!\n"
        "You receive 100 experience points for the kill.\n"
        "A wolf's heart is torn from its chest.\n"
    )

    assert policy.room_targets["3713"] == ["wolf"]
    assert policy.defeated_targets["3713"] == {"wolf"}


def test_flee_rejection_clears_the_combat_state() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.current_room = "3737"
    policy.active_target = "wild boar"
    policy.combat_active = True

    policy.observe_text("You aren't fighting anyone.\n")

    assert policy.combat_active is False
    assert policy.active_target is None


def test_resumed_empty_training_room_returns_after_inspection() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.course_started = True
    policy.current_room = "3713"
    policy.room_query_counts["3713"] = 1
    policy.prompt_ready = True
    state = CharacterState(
        hp=60,
        max_hp=60,
        room_name="Combat Training",
        room_vnum="3713",
        exits={"w": "3712"},
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "west"
    assert "3713" in policy.cleared_training_rooms


def test_room_description_structures_are_not_combat_targets() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.current_room = "3713"

    policy.observe_text(
        "The yard is quite large.\n"
        "The door is closed.\n"
        "A wolf circles as far as its chain will let it.\n"
    )

    assert policy.room_targets["3713"] == ["wolf"]


def test_prowling_wolf_is_registered_as_an_attackable_target() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.current_room = "3728"

    policy.observe_text("A wolf prowls the arena.\n")

    assert policy.room_targets["3728"] == ["wolf"]


def test_advanced_training_target_descriptions_are_parsed() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.current_room = "3717"

    policy.observe_text(
        "A small goblin cringes and scowls.\n"
        "A kobold tries desperately to escape.\n"
        "A human prisoner nervously circles you.\n"
    )

    assert policy.room_targets["3717"] == [
        "small goblin",
        "kobold",
        "human prisoner",
    ]


def test_victory_room_uses_completion_portal() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.course_started = True
    policy.current_room = "3723"
    policy.room_query_counts["3723"] = 1
    policy.prompt_ready = True
    state = CharacterState(
        hp=60,
        max_hp=60,
        room_name="Victory",
        room_vnum="3723",
        exits={"s": "3722"},
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "enter portal"


def test_loremaster_prefers_class_skill_from_real_practice_list() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.loremaster_step = 2
    policy.prompt_ready = True
    policy.text = """
Skills which may be learned:
               continual light:   0%                   detect good:   0%
                 magic missile:   0%               summon familiar:   0%
You have 1 physical and 3 intellectual practices remaining.
"""
    state = CharacterState(
        hp=60,
        max_hp=60,
        room_name="The Loremaster",
        room_vnum="3726",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "practice magic missile"


def test_arena_fights_discovered_target_and_leaves_at_level_two() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.arena_queried = True
    policy.current_room = "3729"
    policy.room_targets["3729"] = ["wild boar"]
    policy.prompt_ready = True
    state = CharacterState(
        hp=60,
        max_hp=60,
        level=1,
        room_name="The Mud School Arena",
        room_vnum="3729",
        exits={"e": "3728", "s": "3731", "u": "3737"},
    )

    fight = policy.next_decision(state)
    assert fight is not None
    assert fight.command == "kill boar"

    policy.combat_active = False
    policy.prompt_ready = True
    state.level = 2
    leave = policy.next_decision(state)
    assert leave is not None
    assert leave.command == "up"


def test_arena_research_continues_at_level_two_until_its_target() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=3)
    policy.in_world = True
    policy.arena_queried = True
    policy.current_room = "3729"
    policy.room_targets["3729"] = ["wild boar"]
    policy.prompt_ready = True
    state = CharacterState(
        level=2,
        hp=60,
        max_hp=60,
        room_name="The Mud School Arena",
        room_vnum="3729",
    )

    fight = policy.next_decision(state)

    assert fight is not None
    assert fight.command == "kill boar"

    policy.combat_active = False
    policy.prompt_ready = True
    state.level = 3
    leave = policy.next_decision(state)

    assert leave is not None
    assert leave.command == "up"
    assert "level 3" in leave.reason


def test_arena_prioritizes_wolves_when_multiple_targets_are_observed() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=4)
    policy.in_world = True
    policy.arena_queried = True
    policy.current_room = "3729"
    policy.room_targets["3729"] = ["wild boar", "wolf"]
    policy.prompt_ready = True
    state = CharacterState(
        level=3,
        hp=70,
        max_hp=70,
        room_name="The Mud School Arena",
        room_vnum="3729",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "kill wolf"


def test_arena_waits_for_gmcp_combat_to_end_before_issuing_another_kill() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=7)
    policy.in_world = True
    policy.arena_queried = True
    policy.current_room = "3736"
    policy.room_targets["3736"] = ["lizard"]
    policy.prompt_ready = True
    state = CharacterState(
        level=6,
        hp=80,
        max_hp=96,
        in_combat=True,
        combat_target="a giant lizard",
        room_name="The Mud School Arena",
        room_vnum="3736",
    )

    assert policy.next_decision(state) is None
    assert policy.combat_active is True


def test_low_movement_sleeps_without_repeating_movement_commands() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=4)
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        level=3,
        hp=70,
        max_hp=70,
        move=0,
        max_move=170,
        room_name="The Mud School Arena",
        room_vnum="3736",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "sleep"
    policy.after_command(decision)
    policy.prompt_ready = True
    assert policy.next_decision(state) is None


def test_arena_safety_room_sleeps_until_health_recovers() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=4)
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        level=3,
        hp=17,
        max_hp=70,
        room_name="Safety",
        room_vnum="3737",
    )

    sleep = policy.next_decision(state)

    assert sleep is not None
    assert sleep.command == "sleep"
    policy.after_command(sleep)
    state.hp = 40
    policy.prompt_ready = True
    stand = policy.next_decision(state)
    assert stand is not None
    assert stand.command == "stand"


def test_missing_arena_target_is_removed_before_the_next_decision() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=3)
    policy.current_room = "3728"
    policy.active_target = "wild boar"
    policy.room_targets["3728"] = ["wild boar"]

    policy.observe_text("They aren't here.")

    assert policy.combat_active is False
    assert policy.active_target is None
    assert policy.room_targets["3728"] == []


def test_completed_arena_patrol_forgets_stale_room_sightings() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=3)
    policy.in_world = True
    policy.arena_queried = True
    policy.prompt_ready = True
    policy.arena_visited_rooms.update(str(vnum) for vnum in range(3728, 3738))
    policy.room_query_counts.update({"3728": 1, "3736": 1, "3713": 1})
    policy.room_targets.update({"3728": ["wolf"], "3713": ["snake"]})
    policy.defeated_targets["3728"] = {"wolf"}
    state = CharacterState(
        level=2,
        hp=60,
        max_hp=60,
        room_name="The Mud School Arena",
        room_vnum="3736",
        exits={"n": "3733", "u": "3737", "w": "3735"},
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "up"
    assert policy.arena_visited_rooms == set()
    assert "3728" not in policy.room_query_counts
    assert policy.room_query_counts["3713"] == 1
    assert "3728" not in policy.room_targets
    assert policy.room_targets["3713"] == ["snake"]
    assert "3728" not in policy.defeated_targets
    assert policy.arena_respawn_due is not None


def test_empty_arena_patrol_sleeps_safely_until_the_respawn_window() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=3)
    policy.in_world = True
    policy.prompt_ready = True
    policy.arena_respawn_due = time.monotonic() + 60
    state = CharacterState(
        level=2,
        hp=60,
        max_hp=60,
        position=7,
        room_name="Safety",
        room_vnum="3737",
    )

    sleep = policy.next_decision(state)

    assert sleep is not None
    assert sleep.command == "sleep"
    state.position = 4
    policy.prompt_ready = True
    assert policy.next_decision(state) is None


def test_safe_room_gmcp_update_reopens_expired_respawn_wait() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=3)
    policy.in_world = True
    policy.arena_respawn_due = time.monotonic() - 1
    state = CharacterState(
        level=2,
        hp=60,
        max_hp=60,
        position=4,
        room_name="Safety",
        room_vnum="3737",
    )

    policy.observe_events(
        [GameEvent(type="room_updated", source="gmcp", data={})],
        state,
    )
    decision = policy.next_decision(state)

    assert policy.prompt_ready is True
    assert decision is not None
    assert decision.command == "stand"
    assert policy.arena_respawn_due is None


def test_arena_safety_room_reenters_the_mud_school_portal() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=3)
    policy.in_world = True
    policy.course_started = True
    policy.course_complete = True
    policy.practiced = True
    policy.prompt_ready = True
    state = CharacterState(
        level=2,
        hp=60,
        max_hp=60,
        room_name="Safety",
        room_vnum="3737",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "enter portal"


def test_resupply_policy_returns_from_limbo_then_eats_and_drinks() -> None:
    policy = StarterPolicy(_spec(), "swordfish", resupply_only=True)
    policy.in_world = True
    policy.prompt_ready = True

    limbo = CharacterState(room_name="Limbo", room_vnum="2")
    decision = policy.next_decision(limbo)
    assert decision is not None
    assert decision.command == "look"
    policy.after_command(decision)

    policy.prompt_ready = True
    safety = CharacterState(
        hp=10,
        max_hp=60,
        position=4,
        room_name="Safety",
        room_vnum="3737",
        inventory=[[{"short_desc": "a buffalo water skin"}, {"short_desc": "a big pot pie"}]],
    )
    decision = policy.next_decision(safety)
    assert decision is not None
    assert decision.command == "stand"
    policy.after_command(decision)

    policy.prompt_ready = True
    safety.position = 7
    decision = policy.next_decision(safety)
    assert decision is not None
    assert decision.command == "eat pie"
    policy.after_command(decision)

    policy.prompt_ready = True
    decision = policy.next_decision(safety)
    assert decision is not None
    assert decision.command == "drink skin"
    policy.after_command(decision)

    policy.prompt_ready = True
    decision = policy.next_decision(safety)
    assert decision is not None
    assert decision.command == "save"


def test_hunger_warning_preempts_low_health_sleep() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=3)
    policy.in_world = True
    policy.prompt_ready = True
    policy.observe_text("You are dying of hunger! Your throat is parched.")
    state = CharacterState(
        hp=5,
        max_hp=60,
        position=7,
        room_name="Safety",
        room_vnum="3737",
        inventory=[[{"short_desc": "a buffalo water skin"}, {"short_desc": "a big pot pie"}]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "eat pie"


def test_resupply_policy_sells_equipment_after_an_insufficient_funds_response() -> None:
    policy = StarterPolicy(_spec(), "swordfish", resupply_only=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.observe_text("You can't afford that.")
    state = CharacterState(
        room_name="General Supplies",
        room_vnum="3724",
        inventory=[[{"short_desc": "a battered sword"}]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "sell sword"


def test_city_restock_policy_uses_fountain_then_bakery() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_restock=True)
    policy.in_world = True
    policy.prompt_ready = True

    rooms_and_commands = (
        ("Safety", "3737", "enter portal"),
        ("The Entrance to the Mud School", "3725", "down"),
        ("The Temple Of Midgaard", "3001", "south"),
        ("The Temple Square", "3005", "fill skin"),
        ("The Temple Square", "3005", "drink skin"),
        ("The Temple Square", "3005", "south"),
        ("Market Square", "3014", "west"),
        ("Main Street", "3013", "north"),
        ("The Bakery", "3009", "list"),
        ("The Bakery", "3009", "buy 6 pie"),
        ("The Bakery", "3009", "inventory"),
    )
    for room_name, room_vnum, expected_command in rooms_and_commands:
        decision = policy.next_decision(
            CharacterState(room_name=room_name, room_vnum=room_vnum, position=7)
        )
        assert decision is not None
        assert decision.command == expected_command
        policy.after_command(decision)
        policy.prompt_ready = True

    decision = policy.next_decision(
        CharacterState(room_name="The Bakery", room_vnum="3009", position=7)
    )
    assert decision is not None
    assert decision.command == "save"


def test_guildmaster_research_reaches_mage_laboratory_and_records_training() -> None:
    policy = StarterPolicy(_spec(), "swordfish", guildmaster_research=True)
    policy.in_world = True
    policy.prompt_ready = True

    rooms_and_commands = (
        ("The Magic Shop", "3033", "south"),
        ("Safety", "3737", "enter portal"),
        ("The Entrance to the Mud School", "3725", "down"),
        ("The Temple Of Midgaard", "3001", "south"),
        ("The Temple Square", "3005", "south"),
        ("Market Square", "3014", "west"),
        ("Main Street", "3013", "west"),
        ("Mage's Guild Entrance", "3012", "south"),
        ("Mage Bar", "3017", "south"),
        ("Mage's Laboratory", "3018", "east"),
        ("Mage's Laboratory", "3019", "look guildmaster"),
        ("Mage's Laboratory", "3019", "practice"),
    )
    for room_name, room_vnum, expected_command in rooms_and_commands:
        decision = policy.next_decision(
            CharacterState(room_name=room_name, room_vnum=room_vnum, position=7)
        )
        assert decision is not None
        assert decision.command == expected_command
        policy.after_command(decision)
        policy.prompt_ready = True

    decision = policy.next_decision(
        CharacterState(room_name="Mage's Laboratory", room_vnum="3019", position=7)
    )
    assert decision is not None
    assert decision.command == "save"


def test_guildmaster_research_leaves_an_arena_room_before_city_travel() -> None:
    policy = StarterPolicy(_spec(), "swordfish", guildmaster_research=True)
    policy.in_world = True
    policy.prompt_ready = True

    decision = policy.next_decision(
        CharacterState(room_name="The Arena", room_vnum="3728", position=7)
    )

    assert decision is not None
    assert decision.command == "up"


def test_guildmaster_research_sleeps_to_recover_in_a_safe_city_room() -> None:
    policy = StarterPolicy(_spec(), "swordfish", guildmaster_research=True)
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        hp=15,
        max_hp=96,
        position=7,
        room_name="Mage's Laboratory",
        room_vnum="3019",
        room_flags=["indoors", "safe"],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "sleep"
    assert policy.waiting_for_heal is True


def test_safe_room_recovery_checks_health_without_waking() -> None:
    policy = StarterPolicy(_spec(), "swordfish", guildmaster_research=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.waiting_for_heal = True
    policy.health_check_due = time.monotonic() - 1
    state = CharacterState(
        hp=15,
        max_hp=96,
        position=4,
        room_name="Mage's Laboratory",
        room_vnum="3019",
        room_flags=["indoors", "safe"],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "score"


def test_safe_room_recovery_wakes_for_hunger_then_resumes_sleeping() -> None:
    policy = StarterPolicy(_spec(), "swordfish", guildmaster_research=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.waiting_for_heal = True
    policy.needs_food = True
    sleeping = CharacterState(
        hp=15,
        max_hp=96,
        position=4,
        room_name="Mage's Laboratory",
        room_vnum="3019",
        room_flags=["indoors", "safe"],
        inventory=[[{"short_desc": "a big pot pie"}]],
    )

    wake = policy.next_decision(sleeping)
    assert wake is not None
    assert wake.command == "stand"
    policy.after_command(wake)

    policy.prompt_ready = True
    sleeping.position = 7
    eat = policy.next_decision(sleeping)
    assert eat is not None
    assert eat.command == "eat pie"
    policy.after_command(eat)

    policy.prompt_ready = True
    resume = policy.next_decision(sleeping)
    assert resume is not None
    assert resume.command == "sleep"


def test_moria_research_reaches_the_entry_and_returns_to_mage_laboratory() -> None:
    policy = StarterPolicy(_spec(), "swordfish", moria_research=True)
    policy.in_world = True
    policy.prompt_ready = True

    outward = (
        ("Mage's Laboratory", "3019", "west"),
        ("Mage's Bar", "3018", "north"),
        ("Entrance to Mage's Guild", "3017", "north"),
        ("Main Street", "3012", "west"),
        ("Inside the West Gate of Midgaard", "3040", "west"),
        ("Outside the West Gate of Midgaard", "3041", "north"),
    )
    for room_name, room_vnum, expected_command in outward:
        decision = policy.next_decision(
            CharacterState(room_name=room_name, room_vnum=room_vnum, position=7)
        )
        assert decision is not None
        assert decision.command == expected_command
        policy.after_command(decision)
        policy.prompt_ready = True

    moria = CharacterState(
        area="Moria", room_name="East trail around Midgaard", room_vnum="4000", position=7
    )
    decision = policy.next_decision(moria)
    assert decision is not None
    assert decision.command == "look"
    policy.after_command(decision)
    policy.prompt_ready = True

    decision = policy.next_decision(moria)
    assert decision is not None
    assert decision.command == "south"
    policy.after_command(decision)
    policy.prompt_ready = True

    return_path = (
        ("Outside the West Gate of Midgaard", "3041", "east"),
        ("Inside the West Gate of Midgaard", "3040", "east"),
        ("Main Street", "3012", "south"),
        ("Entrance to Mage's Guild", "3017", "south"),
        ("Mage's Bar", "3018", "east"),
    )
    for room_name, room_vnum, expected_command in return_path:
        decision = policy.next_decision(
            CharacterState(room_name=room_name, room_vnum=room_vnum, position=7)
        )
        assert decision is not None
        assert decision.command == expected_command
        policy.after_command(decision)
        policy.prompt_ready = True

    decision = policy.next_decision(
        CharacterState(room_name="Mage's Laboratory", room_vnum="3019", position=7)
    )
    assert decision is not None
    assert decision.command == "save"


def test_fastwalk_research_requires_recall_and_reverses_when_needed() -> None:
    route = route_named("moria")
    policy = StarterPolicy(_spec(), "swordfish", fastwalk_route=route)
    policy.in_world = True
    policy.prompt_ready = True

    recall = policy.next_decision(
        CharacterState(room_name="Mage's Laboratory", room_vnum="3019", position=7)
    )
    assert recall is not None
    assert recall.command == "recall"
    policy.after_command(recall)
    policy.prompt_ready = True

    first_step = policy.next_decision(
        CharacterState(room_name="The Temple Of Midgaard", room_vnum="3001", position=7)
    )
    assert first_step is not None
    assert first_step.command == "south"

    policy.fastwalk_outbound_index = len(route.commands)
    policy.prompt_ready = True
    endpoint = CharacterState(room_name="Moria entrance", room_vnum="3900", position=7)
    look = policy.next_decision(endpoint)
    assert look is not None
    assert look.command == "look"
    policy.after_command(look)
    policy.prompt_ready = True

    return_recall = policy.next_decision(endpoint)
    assert return_recall is not None
    assert return_recall.command == "recall"
    policy.after_command(return_recall)
    policy.prompt_ready = True

    reverse = policy.next_decision(endpoint)
    assert reverse is not None
    assert reverse.command == "south"


def test_fastwalk_research_can_inspect_one_endpoint_exit_and_return() -> None:
    route = route_named("moria")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_explore_direction="north",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    endpoint = CharacterState(room_name="The tunnel", room_vnum="4014", position=7)

    enter_cave = policy.next_decision(endpoint)
    assert enter_cave is not None
    assert enter_cave.command == "north"
    policy.after_command(enter_cave)
    policy.prompt_ready = True

    cave = CharacterState(room_name="A cave", room_vnum="4018", position=7)
    look = policy.next_decision(cave)
    assert look is not None
    assert look.command == "look"
    policy.after_command(look)
    policy.prompt_ready = True

    return_south = policy.next_decision(cave)
    assert return_south is not None
    assert return_south.command == "south"


def test_fastwalk_repeat_limit_allows_the_route_run_but_not_extra_steps() -> None:
    route = route_named("moria")

    assert _max_consecutive_command(route.commands, "north") == 8
    assert _max_consecutive_command(route.commands, "south") == 2


def test_magic_shop_research_lists_stock_and_returns_to_mage_laboratory() -> None:
    policy = StarterPolicy(_spec(), "swordfish", magic_shop_research=True)
    policy.in_world = True
    policy.prompt_ready = True

    outward = (
        ("Mage's Laboratory", "3019", "west"),
        ("Mage's Bar", "3018", "north"),
        ("Entrance to Mage's Guild", "3017", "north"),
        ("Main Street", "3012", "north"),
    )
    for room_name, room_vnum, expected_command in outward:
        decision = policy.next_decision(
            CharacterState(room_name=room_name, room_vnum=room_vnum, position=7)
        )
        assert decision is not None
        assert decision.command == expected_command
        policy.after_command(decision)
        policy.prompt_ready = True

    shop = CharacterState(room_name="The Magic Shop", room_vnum="3033", position=7)
    listing = policy.next_decision(shop)
    assert listing is not None
    assert listing.command == "list"
    policy.after_command(listing)
    policy.prompt_ready = True

    leave_shop = policy.next_decision(shop)
    assert leave_shop is not None
    assert leave_shop.command == "south"

    return_path = (
        ("Main Street", "3012", "south"),
        ("Entrance to Mage's Guild", "3017", "south"),
        ("Mage's Bar", "3018", "east"),
    )
    for room_name, room_vnum, expected_command in return_path:
        decision = policy.next_decision(
            CharacterState(room_name=room_name, room_vnum=room_vnum, position=7)
        )
        assert decision is not None
        assert decision.command == expected_command
        policy.after_command(decision)
        policy.prompt_ready = True

    finish = policy.next_decision(
        CharacterState(room_name="Mage's Laboratory", room_vnum="3019", position=7)
    )
    assert finish is not None
    assert finish.command == "save"


def test_magic_shop_research_can_buy_and_verify_a_fly_potion() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        magic_shop_research=True,
        magic_shop_buy_fly=True,
    )
    policy.in_world = True
    policy.prompt_ready = True
    shop = CharacterState(room_name="The Magic Shop", room_vnum="3033", position=7)

    commands = []
    for _ in range(5):
        decision = policy.next_decision(shop)
        assert decision is not None
        commands.append(decision.command)
        policy.after_command(decision)
        policy.prompt_ready = True

    assert commands == ["list", "buy light", "inventory", "quaff light", "affects"]
    leave_shop = policy.next_decision(shop)
    assert leave_shop is not None
    assert leave_shop.command == "south"


def test_magic_shop_research_returns_when_flight_potion_price_is_unaffordable() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        magic_shop_research=True,
        magic_shop_buy_fly=True,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.magic_shop_step = 2
    policy.observe_text("You can't afford that item.")

    decision = policy.next_decision(
        CharacterState(room_name="The Magic Shop", room_vnum="3033", position=7)
    )

    assert decision is not None
    assert decision.command == "south"
    assert policy.magic_shop_purchase_failed is True


def test_moria_research_depth_one_inspects_one_additional_trail_room() -> None:
    policy = StarterPolicy(_spec(), "swordfish", moria_research=True, moria_depth=1)
    policy.in_world = True
    policy.prompt_ready = True
    entry = CharacterState(
        area="Moria", room_name="West trail around Midgaard", room_vnum="3900", position=7
    )

    look_entry = policy.next_decision(entry)
    assert look_entry is not None
    assert look_entry.command == "look"
    policy.after_command(look_entry)
    policy.prompt_ready = True

    deeper = policy.next_decision(entry)
    assert deeper is not None
    assert deeper.command == "north"
    policy.after_command(deeper)
    policy.prompt_ready = True

    north_trail = CharacterState(
        area="Moria", room_name="Dusty trail along north wall", room_vnum="3901", position=7
    )
    look_north = policy.next_decision(north_trail)
    assert look_north is not None
    assert look_north.command == "look"
    policy.after_command(look_north)
    policy.prompt_ready = True

    return_south = policy.next_decision(north_trail)
    assert return_south is not None
    assert return_south.command == "south"


def test_moria_research_follows_the_verified_east_turn_and_returns() -> None:
    policy = StarterPolicy(_spec(), "swordfish", moria_research=True, moria_depth=3)
    policy.in_world = True
    policy.prompt_ready = True

    entry = CharacterState(
        area="Moria",
        room_name="West trail around Midgaard",
        room_vnum="3900",
        position=7,
    )
    look_entry = policy.next_decision(entry)
    assert look_entry is not None
    assert look_entry.command == "look"
    policy.after_command(look_entry)
    policy.prompt_ready = True

    north_trail = CharacterState(
        area="Moria",
        room_name="West trail around Midgaard",
        room_vnum="3901",
        position=7,
    )
    look_north = policy.next_decision(north_trail)
    assert look_north is not None
    assert look_north.command == "look"
    policy.after_command(look_north)
    policy.prompt_ready = True

    corner = CharacterState(
        area="Moria",
        room_name="Northwest corner of dusty trail.",
        room_vnum="3902",
        position=7,
    )
    look_corner = policy.next_decision(corner)
    assert look_corner is not None
    assert look_corner.command == "look"
    policy.after_command(look_corner)
    policy.prompt_ready = True

    turn_east = policy.next_decision(corner)
    assert turn_east is not None
    assert turn_east.command == "east"
    policy.after_command(turn_east)
    policy.prompt_ready = True

    east_trail = CharacterState(
        area="Moria",
        room_name="North wall trail",
        room_vnum="3903",
        position=7,
    )
    look_east = policy.next_decision(east_trail)
    assert look_east is not None
    assert look_east.command == "look"
    policy.after_command(look_east)
    policy.prompt_ready = True

    return_west = policy.next_decision(east_trail)
    assert return_west is not None
    assert return_west.command == "west"


def test_moria_research_probes_the_verified_north_branch_and_returns() -> None:
    policy = StarterPolicy(_spec(), "swordfish", moria_research=True, moria_depth=5)
    policy.in_world = True
    policy.prompt_ready = True

    for room_vnum, room_name in (
        ("3900", "West trail around Midgaard"),
        ("3901", "West trail around Midgaard"),
        ("3902", "Northwest corner of dusty trail."),
        ("3903", "Dusty trail along north wall."),
        ("3904", "The long dusty trail following the north wall."),
    ):
        decision = policy.next_decision(
            CharacterState(
                area="Moria",
                room_name=room_name,
                room_vnum=room_vnum,
                position=7,
            )
        )
        assert decision is not None
        assert decision.command == "look"
        policy.after_command(decision)
        policy.prompt_ready = True

    move_north = policy.next_decision(
        CharacterState(
            area="Moria",
            room_name="The long dusty trail following the north wall.",
            room_vnum="3904",
            position=7,
        )
    )
    assert move_north is not None
    assert move_north.command == "north"
    policy.after_command(move_north)
    policy.prompt_ready = True

    north_room = CharacterState(
        area="The Plains",
        room_name="Path in the plains",
        room_vnum="300",
        position=7,
    )
    look_north = policy.next_decision(north_room)
    assert look_north is not None
    assert look_north.command == "look"
    policy.after_command(look_north)
    policy.prompt_ready = True

    return_south = policy.next_decision(north_room)
    assert return_south is not None
    assert return_south.command == "south"


def test_safe_room_recovery_waits_for_movement_before_travel() -> None:
    policy = StarterPolicy(_spec(), "swordfish", moria_research=True)
    policy.in_world = True
    policy.prompt_ready = True
    resting = CharacterState(
        hp=90,
        max_hp=96,
        mana=268,
        max_mana=268,
        move=30,
        max_move=200,
        position=7,
        room_name="Mage's Laboratory",
        room_vnum="3019",
        room_flags=["safe"],
    )

    sleep = policy.next_decision(resting)
    assert sleep is not None
    assert sleep.command == "sleep"
    policy.after_command(sleep)
    policy.prompt_ready = True

    resting.position = 4
    assert policy.next_decision(resting) is None

    policy.prompt_ready = True
    resting.move = 100
    wake = policy.next_decision(resting)
    assert wake is not None
    assert wake.command == "stand"


def test_arena_policy_returns_from_midgaard_bakery_to_mud_school() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=5)
    policy.in_world = True
    policy.prompt_ready = True
    policy.course_started = True
    policy.course_complete = True
    policy.practiced = True

    rooms_and_commands = (
        ("The Bakery", "3009", "south"),
        ("Main Street", "3013", "east"),
        ("Market Square", "3014", "north"),
        ("The Temple Square", "3005", "north"),
        ("The Temple Of Midgaard", "3001", "up"),
    )
    for room_name, room_vnum, expected_command in rooms_and_commands:
        decision = policy.next_decision(
            CharacterState(
                level=4,
                hp=79,
                max_hp=79,
                position=7,
                room_name=room_name,
                room_vnum=room_vnum,
                inventory=[[{"short_desc": "a buffalo water skin"}]],
            )
        )
        assert decision is not None
        assert decision.command == expected_command
        policy.after_command(decision)
        policy.prompt_ready = True


def test_gmcp_recovery_vitals_resume_waiting_arena_policy() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=5)
    policy.in_world = True
    policy.course_started = True
    policy.course_complete = True
    policy.practiced = True
    policy.waiting_for_move = True
    state = CharacterState(
        level=4,
        hp=79,
        max_hp=79,
        move=90,
        max_move=180,
        position=4,
        room_name="Safety",
        room_vnum="3737",
    )

    policy.observe_events(
        [GameEvent(type="vitals_changed", source="gmcp", data={})],
        state,
    )
    decision = policy.next_decision(state)

    assert policy.prompt_ready is True
    assert decision is not None
    assert decision.command == "stand"


def test_gmcp_health_recovery_reopens_safe_room_decisions() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=5)
    policy.in_world = True
    policy.waiting_for_heal = True
    state = CharacterState(hp=40, max_hp=79, room_name="Safety", room_vnum="3737")

    policy.observe_events(
        [GameEvent(type="vitals_changed", source="gmcp", data={})],
        state,
    )

    assert policy.prompt_ready is True


def test_normal_arena_policy_wakes_before_leaving_safety() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=5)
    policy.in_world = True
    policy.prompt_ready = True
    policy.course_started = True
    policy.course_complete = True
    policy.practiced = True
    state = CharacterState(
        level=4,
        hp=79,
        max_hp=79,
        move=180,
        max_move=180,
        position=4,
        room_name="Safety",
        room_vnum="3737",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "stand"


def test_mage_casts_magic_missile_while_fighting_an_arena_target() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=6)
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.active_target = "a prowling wolf"
    state = CharacterState(
        hp=70,
        max_hp=88,
        mana=220,
        max_mana=240,
        position=6,
        room_name="The Mud School Arena",
        room_vnum="3736",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "cast 'magic missile' wolf"

    policy.prompt_ready = True
    assert policy.next_decision(state) is None


def test_mage_casts_again_after_the_server_confirms_the_previous_volley() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=7)
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.active_target = "a prowling wolf"
    policy.magic_missile_cast = True
    state = CharacterState(
        hp=70,
        max_hp=96,
        mana=180,
        max_mana=268,
        position=6,
        room_name="The Mud School Arena",
        room_vnum="3736",
    )

    policy.observe_text("You launch a volley of 3 magic missiles at a wolf!\n")
    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "cast 'magic missile' wolf"


def test_mage_preserves_low_mana_for_arena_recovery() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=6)
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.active_target = "a wild boar"
    state = CharacterState(
        hp=70,
        max_hp=88,
        mana=20,
        max_mana=240,
        position=6,
        room_name="The Mud School Arena",
        room_vnum="3736",
    )

    decision = policy.next_decision(state)

    assert decision is None


def test_starter_policy_rejects_invalid_objective_level() -> None:
    with pytest.raises(ValueError, match="objective_level"):
        StarterPolicy(_spec(), "swordfish", objective_level=1)


def test_new_character_prelude_follows_down_exit() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        hp=50,
        max_hp=50,
        level=1,
        room_name="Floating in Space",
        room_vnum="3700",
        exits={"d": "3701"},
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "open down"


def test_level_two_resume_infers_training_and_provisions() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        hp=50,
        max_hp=61,
        level=2,
        room_name="The Entrance to the Mud School",
        room_vnum="3725",
        inventory=[[{"short_desc": "a buffalo water skin"}]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "east"
    assert policy.course_complete is True
    assert policy.provisioned is True


class _LoginOnlyConnection:
    def __init__(self) -> None:
        self.closed = False
        self.sent: list[str] = []
        self.reads = [
            ReadResult(text="Enter thy Name:", raw=b"name"),
            ReadResult(text="Password:", raw=b"password"),
        ]

    async def connect(self) -> None:
        return None

    async def close(self) -> None:
        self.closed = True

    async def send_command(self, command: str) -> None:
        self.sent.append(command)

    async def read_available(self, timeout: float = 0.25) -> ReadResult:
        if self.reads:
            return self.reads.pop(0)
        return ReadResult()


def test_starter_runner_redacts_password_on_failed_run(
    tmp_path,
    monkeypatch,
) -> None:
    connection = _LoginOnlyConnection()
    spec = _spec(
        password_env="STARTER_TEST_PASSWORD",
        max_commands=2,
        max_runtime=2,
        database=str(tmp_path / "runs.sqlite3"),
        transcript_dir=str(tmp_path / "transcripts"),
    )
    monkeypatch.setenv("STARTER_TEST_PASSWORD", "not-for-transcripts")
    runner = StarterBotRunner(
        spec,
        tmp_path / "starter.yaml",
        connection_factory=lambda _spec: connection,
    )

    with pytest.raises(RuntimeError, match="command budget"):
        asyncio.run(runner.run())

    transcript = next((tmp_path / "transcripts").glob("*.jsonl")).read_text(
        encoding="utf-8"
    )
    assert connection.sent == ["Rulemage", "not-for-transcripts"]
    assert "not-for-transcripts" not in transcript
    assert "[REDACTED]" in transcript


def test_final_combat_loots_and_unlocks_after_kill() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.course_started = True
    policy.prompt_ready = True
    policy.current_room = "3722"
    policy.cleared_training_rooms.add("3722")
    policy.post_kill_steps["3722"] = 2
    state = CharacterState(
        hp=60,
        max_hp=60,
        room_name="Final Combat",
        room_vnum="3722",
        exits={"n": "3723", "s": "3716"},
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "unlock north"
