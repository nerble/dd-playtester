import asyncio
import time

import pytest

from dd4tester.character import CharacterSpec
from dd4tester.connection import ReadResult
from dd4tester.equipment import (
    GearCatalog,
    STANCE_COMBAT,
    STANCE_PRE_LEVEL,
    STANCE_RECOVERY,
)
from dd4tester.fastwalks import route_named
from dd4tester.hunt_candidates import ObjectSource
from dd4tester.observations import GameEvent
from dd4tester.shops import safe_shop_for_item
from dd4tester.starter import (
    BotDecision,
    FieldHuntStop,
    StarterBotRunner,
    StarterPolicy,
    _inventory_descriptions,
    _max_consecutive_command,
    _practice_balances,
    _sellable_inventory_keyword,
    _stop_target_matches,
    _watchdog_progress_marker,
    _policy_inactivity_due,
    ambush_exterior_hunt_stops,
    ambush_raider_consider_stops,
    ambush_raider_hunt_stops,
    ambush_vile_goblin_hunt_stops,
    daycare_nanny_hunt_route,
    daycare_nanny_hunt_stops,
    foundry_level_six_hunt_stops,
    foundry_level_seven_hunt_stops,
    midennir_horseman_consider_stops,
    midennir_horseman_probe_route,
    moria_level_seven_orc_hunt_stops,
    moria_sanctuary_potion_consider_stops,
    moria_sanctuary_potion_hunt_stops,
    shire_bull_hunt_route,
    shire_bull_hunt_stops,
)
from dd4tester.state import CharacterState


def _spec(**overrides: object) -> CharacterSpec:
    values: dict[str, object] = {
        "name": "Rulemage",
        "race": "human",
        "gender": "female",
        "class": "mage",
        "subclass": "warlock",
        "title": "",
        "minimum_primary_stat": 16,
        "max_attribute_rolls": 2,
    }
    values.update(overrides)
    return CharacterSpec.from_mapping(values)


def test_configured_test_title_is_applied_once_per_run() -> None:
    policy = StarterPolicy(
        _spec(title="the Suspiciously Methodical"),
        "swordfish",
    )
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        area="Midgaard",
        hp=79,
        max_hp=79,
        move=180,
        max_move=180,
        position=7,
        room_name="Mage's Laboratory",
        room_vnum="3019",
        room_flags=["safe"],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "title the Suspiciously Methodical"
    policy.after_command(decision)
    policy.prompt_ready = True
    assert policy.next_decision(state).command != decision.command


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


def test_ambush_exterior_research_stays_out_of_the_cave_complex() -> None:
    stops = ambush_exterior_hunt_stops()
    commands = [command for stop in stops for command in stop.route]

    assert [stop.target for stop in stops] == [
        "wounded goblin",
        "war dog",
        "goblin",
        "goblin looter",
        "goblin archer",
    ]
    assert "down" not in commands
    assert commands[-2:] == ["open south", "south"]


def test_foundry_level_six_circuit_links_two_source_backed_targets() -> None:
    stops = foundry_level_six_hunt_stops()

    assert [stop.target for stop in stops] == ["uburz", "ushog"]
    assert stops[0].route == (
        "south",
        "south",
        "west",
        "west",
        "down",
        "east",
    )
    assert stops[1].route == (
        "west",
        "up",
        "east",
        "east",
        "north",
        "north",
        "west",
        "open south",
        "south",
    )
    assert all(not stop.consider_only for stop in stops)
    assert stops[0].minimum_health_ratio == 0.8
    assert stops[1].minimum_health_ratio == 1.0


def test_foundry_level_seven_sweep_links_named_targets_around_poison_pit() -> None:
    stops = foundry_level_seven_hunt_stops()

    assert [stop.target for stop in stops] == [
        "oshu",
        "golgog",
        "shargook",
        "lobuk",
        "uburz",
        "ushog",
    ]
    assert all(stop.exact_target for stop in stops)
    assert all("down" not in stop.route for stop in stops[:3])
    assert stops[-1].minimum_health_ratio == 1.0


def test_moria_level_seven_hunt_puts_poison_target_last() -> None:
    stops = moria_level_seven_orc_hunt_stops()

    assert [stop.target for stop in stops] == [
        "large orc",
        "orc",
        "small green garter snake",
    ]
    assert stops[0].route == ("west", "west", "north", "west", "south")
    assert stops[1].route == (
        "north", "east", "south", "east", "east", "east"
    )
    assert stops[1].allowed_bystanders == ("small green garter snake",)
    assert stops[2].route == ()
    assert stops[2].minimum_health_ratio == 1.0
    assert all(stop.exact_target for stop in stops)


def test_daycare_nanny_hunt_uses_source_route_and_explicit_bystanders() -> None:
    route = daycare_nanny_hunt_route()
    stops = daycare_nanny_hunt_stops()

    assert route.commands == (
        "south",
        "south",
        "east",
        "east",
        "east",
        "east",
        "east",
        "east",
        "down",
        "south",
        "south",
    )
    assert [stop.route for stop in stops] == [(), ("south",)]
    assert all(stop.target == "old wrinkled nanny" for stop in stops)
    assert "young dwarf" in stops[0].allowed_bystanders
    assert "abused and old doll" in stops[1].allowed_bystanders
    assert all(stop.exact_target for stop in stops)


def test_shire_bull_hunt_uses_isolated_source_reset_route() -> None:
    route = shire_bull_hunt_route()
    stops = shire_bull_hunt_stops()

    assert route.commands == (
        "south",
        "south",
        "west",
        "west",
        "west",
        "west",
        "west",
        "north",
        "north",
        "north",
        "north",
        "west",
        "west",
        "north",
        "north",
        "north",
        "west",
    )
    assert len(stops) == 1
    assert stops[0].target == "bull"
    assert stops[0].route == ()
    assert stops[0].minimum_health_ratio == 1.0
    assert stops[0].exact_target is True


def test_moria_level_seven_stop_matches_captured_large_orc_description() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("moria"),
        fastwalk_hunt_stops=moria_level_seven_orc_hunt_stops(),
    )
    policy.in_world = True
    policy.current_room = "4022"
    policy.observe_text(
        "This large orc is looking for someone small to pick on.\n"
    )

    stop = moria_level_seven_orc_hunt_stops()[0]

    assert policy.room_targets["4022"] == ["large orc"]
    assert _stop_target_matches(
        policy.room_targets["4022"][0],
        stop.target or "",
        stop,
    )


def test_midennir_horseman_probe_searches_source_trail_and_never_attacks() -> None:
    assert midennir_horseman_probe_route().commands == ("south",) * 5
    stops = midennir_horseman_consider_stops()

    assert [stop.route for stop in stops] == [
        (),
        ("south",),
        ("west",),
        ("south",),
        ("south",),
        ("west",),
        ("west",),
        ("south",),
        ("west",),
    ]
    assert all(stop.target == "dark horseman" for stop in stops)
    assert all(stop.consider_only for stop in stops)


def test_raider_probe_reaches_reset_and_never_attacks() -> None:
    stops = ambush_raider_consider_stops()

    assert len(stops) == 1
    assert stops[0].route == (
        "west",
        "south",
        "south",
        "west",
        "south",
        "west",
        "south",
        "south",
        "west",
    )
    assert stops[0].target == "goblin raider"
    assert stops[0].consider_only is True
    assert stops[0].exact_target is True


def test_raider_hunt_requires_full_health_and_enables_combat() -> None:
    stops = ambush_raider_hunt_stops()

    assert len(stops) == 1
    assert stops[0].route == ambush_raider_consider_stops()[0].route
    assert stops[0].target == "goblin raider"
    assert stops[0].minimum_health_ratio == 1.0
    assert stops[0].consider_only is False
    assert stops[0].exact_target is True


def test_vile_goblin_hunt_keeps_bystander_exception_but_allows_combat() -> None:
    stops = ambush_vile_goblin_hunt_stops()

    assert len(stops) == 1
    assert stops[0].target == "vile goblin"
    assert stops[0].allowed_bystanders == ("half clothed human female",)
    assert stops[0].consider_only is False


def test_moria_sanctuary_probe_searches_resets_and_nearby_wander_rooms() -> None:
    stops = moria_sanctuary_potion_consider_stops()

    assert len(stops) == 13
    assert stops[0].route == (
        "east",
        "north",
        "north",
        "east",
        "south",
        "down",
    )
    assert [stop.route for stop in stops[1:]] == [
        ("west",),
        ("north",),
        ("west",),
        ("south",),
        ("east",),
        ("east",),
        ("east",),
        ("west", "south"),
        ("west",),
        ("south",),
        ("east",),
        ("east",),
    ]
    assert {stop.target for stop in stops} == {"large hobgoblin"}
    assert all(stop.consider_only for stop in stops)
    assert all(stop.exact_target for stop in stops)
    assert stops[0].actions == ("where hobgoblin",)


def test_moria_sanctuary_hunt_requires_full_health_and_enables_combat() -> None:
    stops = moria_sanctuary_potion_hunt_stops()

    assert len(stops) == 13
    assert all(stop.minimum_health_ratio == 1.0 for stop in stops)
    assert all(stop.consider_only is False for stop in stops)
    assert all(stop.exact_target for stop in stops)
    assert stops[0].actions == ("where hobgoblin",)


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


def test_reboot_login_ignores_stale_in_world_prompt_until_authenticated() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.active_target = "vile goblin"
    policy.active_target_level = 9
    policy.flee_pending = True
    policy.waiting_for_heal = True
    state = CharacterState(
        hp=80,
        max_hp=100,
        mana=100,
        max_mana=100,
        move=50,
        max_move=100,
        position=4,
        room_name="By the Temple Altar",
        room_vnum="3054",
    )

    name = _respond(policy, state, "Enter thy Name:")

    assert name == ("Rulemage", False)
    assert policy.in_world is False
    stale_prompt = GameEvent("prompt_seen", "gmcp", {"package": "Core.Prompt"})
    state.apply(stale_prompt)
    policy.observe_events([stale_prompt], state)
    assert policy.next_decision(state) is None

    assert _respond(policy, state, "Password:") == ("swordfish", True)
    assert _respond(
        policy,
        state,
        "To Enter the Dragons Domain press <Return>.",
    ) == ("", False)
    assert policy.login_authenticated is True


def test_existing_character_direct_reconnect_authenticates_from_server_prompt() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    state = CharacterState(
        hp=100,
        max_hp=100,
        mana=100,
        max_mana=100,
        move=100,
        max_move=100,
        room_name="The Trail to Miden'nir",
        room_vnum="2300",
    )

    assert _respond(policy, state, "Enter thy Name:") == ("Rulemage", False)
    assert _respond(policy, state, "Password:") == ("swordfish", True)
    policy.observe_text(
        "Reconnecting.\n"
        "You must take a few moments to adjust to your new surroundings...\n"
    )
    policy.prompt_ready = True

    policy.next_decision(state)
    assert policy.login_authenticated is True
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
    policy.observe_text("You sleep.")
    state.position = 4

    policy.prompt_ready = True
    assert policy.next_decision(state) is None

    state.hp = 58
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


def test_emergency_resupply_routes_from_mage_guild_to_mud_school_supplies() -> None:
    policy = StarterPolicy(_spec(), "swordfish", resupply_only=True)
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(room_name="Mage's Laboratory", room_vnum="3019")

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "west"


def test_emergency_resupply_leaves_rooms_above_the_altar_for_supplies() -> None:
    policy = StarterPolicy(_spec(), "swordfish", resupply_only=True)
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(room_name="Rooms Above the Altar", room_vnum="3060")

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "down"


def test_emergency_resupply_leaves_implementors_room_for_supplies() -> None:
    policy = StarterPolicy(_spec(), "swordfish", resupply_only=True)
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(room_name="Implementors' Room", room_vnum="3063")

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "north"


def test_emergency_resupply_routes_to_healer_when_safe_room_recovery_stalls() -> None:
    policy = StarterPolicy(_spec(), "swordfish", resupply_only=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.waiting_for_heal = True
    policy.needs_food = False
    policy.needs_drink = False
    state = CharacterState(
        hp=28,
        max_hp=96,
        position=7,
        room_name="Implementors' Room",
        room_vnum="3063",
        room_flags=["no_mob", "indoors", "safe"],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "north"
    assert policy.waiting_for_heal is False


def test_emergency_resupply_sleeps_after_reaching_the_healer() -> None:
    policy = StarterPolicy(_spec(), "swordfish", resupply_only=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.needs_food = False
    policy.needs_drink = False
    state = CharacterState(
        hp=28,
        max_hp=96,
        position=7,
        room_name="The Altar of the Temple",
        room_vnum="3054",
        room_flags=["no_mob", "indoors", "safe"],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "sleep"


def test_emergency_resupply_heals_before_leaving_for_missing_food() -> None:
    policy = StarterPolicy(_spec(), "swordfish", resupply_only=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.needs_food = True
    policy.needs_drink = False
    state = CharacterState(
        hp=9,
        max_hp=96,
        position=7,
        room_name="The Altar of the Temple",
        room_vnum="3054",
        room_flags=["no_mob", "indoors", "safe"],
        inventory=[[{"short_desc": "a buffalo water skin"}]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "sleep"
    assert policy.waiting_for_heal is True


def test_emergency_resupply_stays_asleep_when_missing_food() -> None:
    policy = StarterPolicy(_spec(), "swordfish", resupply_only=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.waiting_for_heal = True
    policy.needs_food = True
    policy.needs_drink = False
    state = CharacterState(
        hp=15,
        max_hp=96,
        position=4,
        room_name="The Altar of the Temple",
        room_vnum="3054",
        room_flags=["no_mob", "indoors", "safe"],
        inventory=[[{"short_desc": "a buffalo water skin"}]],
    )

    decision = policy.next_decision(state)

    assert decision is None
    assert policy.prompt_ready is False


def test_general_supplies_leaves_without_rebuying_existing_provisions() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.course_started = True
    policy.course_complete = True
    policy.provisioned = True
    policy.prompt_ready = True
    state = CharacterState(room_name="General Supplies", room_vnum="3724")

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "down"


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


def test_resumed_room_extracts_moria_snake_description() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.course_started = True
    policy.current_room = "4015"
    policy.prompt_ready = True

    policy.observe_text(
        "A small beat-up hobgoblin cringes in the corner.\n"
        "A small green garter snake slithers along the floor.\n"
    )

    assert policy.room_targets["4015"] == [
        "small beat-up hobgoblin",
        "small green garter snake",
    ]


def test_resumed_room_extracts_moria_crawling_centipede() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.course_started = True
    policy.current_room = "4060"
    policy.prompt_ready = True

    policy.observe_text(
        "A small beat-up hobgoblin cringes in the corner.\n"
        "A white centipede crawls along the cave floors randomly.\n"
    )

    assert policy.room_targets["4060"] == [
        "small beat-up hobgoblin",
        "white centipede",
    ]


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


def test_loremaster_prefers_combat_damage_from_real_practice_list() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.loremaster_step = 2
    policy.prompt_ready = True
    policy.text = """
Skills known:
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
    assert "proficiency does not change its damage" in decision.reason


def test_level_eight_mage_only_trains_skills_in_current_listing() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.loremaster_step = 2
    policy.prompt_ready = True
    policy.text = """
Skills known:
                 magic missile:  46%               illusion magiks:  24%
You have 2 physical and 3 intellectual practices remaining.
"""
    state = CharacterState(
        level=8,
        hp=110,
        max_hp=110,
        room_name="The Loremaster",
        room_vnum="3726",
    )

    commands: list[str] = []
    for index in range(2):
        decision = policy.next_decision(state)
        assert decision is not None
        commands.append(decision.command)
        policy.after_command(decision)
        if index == 0:
            policy.observe_text(
                "The Loremaster says 'I hope my knowledge helps you, Rulemage.'\n"
            )
        policy.prompt_ready = True

    assert commands == [
        "practice illusion magiks",
        "west",
    ]
    assert policy.chill_touch_unavailable is False


def test_level_nine_mage_trains_damage_gateway_before_utility() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.loremaster_step = 2
    policy.prompt_ready = True
    policy.text = """
Skills known:
                 magic missile:  46%              evocation magiks:  23%
You have 2 physical and 3 intellectual practices remaining.
"""
    state = CharacterState(
        level=9,
        hp=115,
        max_hp=115,
        room_name="The Loremaster",
        room_vnum="3726",
    )

    commands: list[str] = []
    for index in range(2):
        decision = policy.next_decision(state)
        assert decision is not None
        commands.append(decision.command)
        policy.after_command(decision)
        if index == 0:
            policy.observe_text(
                "The Loremaster says 'I hope my knowledge helps you, Rulemage.'\n"
            )
        policy.prompt_ready = True

    assert commands == [
        "practice evocation magiks",
        "west",
    ]


def test_loremaster_credits_skill_only_after_trainer_confirmation() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.loremaster_step = 2
    policy.prompt_ready = True
    policy.text = """
Skills known:
Skills which may be learned:
                 magic missile:   0%
You have 1 physical and 1 intellectual practices remaining.
"""
    state = CharacterState(
        level=1,
        hp=60,
        max_hp=60,
        room_name="The Loremaster",
        room_vnum="3726",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "practice magic missile"
    assert "magic missile" not in policy.known_skills
    assert policy.practice_plan_index == 0

    policy.observe_text(
        "The Loremaster says 'I hope my knowledge helps you, Rulemage.'\n"
    )

    assert "magic missile" in policy.known_skills
    assert policy.practice_plan_index == 1
    events = policy.drain_training_events()
    assert [event.type for event in events] == ["training_completed"]
    assert any("magic.c" in ref for ref in events[0].data["source_refs"])


def test_loremaster_rejection_preserves_point_and_records_reason() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.loremaster_step = 2
    policy.prompt_ready = True
    policy.text = """
Skills known:
Skills which may be learned:
                 magic missile:   0%
You have 1 physical and 1 intellectual practices remaining.
"""
    state = CharacterState(
        level=1,
        hp=60,
        max_hp=60,
        room_name="The Loremaster",
        room_vnum="3726",
    )
    decision = policy.next_decision(state)
    assert decision is not None

    policy.observe_text(
        "The Loremaster says 'I'm sorry Rulemage, but you are not ready for that "
        "knowledge.'\n"
    )
    events = policy.drain_training_events()

    assert "magic missile" not in policy.known_skills
    assert policy.rejected_practice_skills == {"magic missile"}
    assert policy.practice_plan_index == 1
    assert events[0].type == "training_rejected"
    assert events[0].data["reason"] == "unmet prerequisites"
    assert "preserve the practice point" in policy.practice_exit_reason


def test_loremaster_unconfirmed_prompt_cannot_leave_training_pending() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.loremaster_step = 2
    policy.prompt_ready = True
    policy.text = """
Skills known:
Skills which may be learned:
                 magic missile:   0%
You have 1 physical and 1 intellectual practices remaining.
"""
    state = CharacterState(
        level=1,
        hp=60,
        max_hp=60,
        room_name="The Loremaster",
        room_vnum="3726",
    )
    decision = policy.next_decision(state)
    assert decision is not None

    policy.observe_events([GameEvent("prompt_seen", "text", {})], state)
    events = policy.drain_training_events()

    assert policy.pending_practice_choice is None
    assert policy.practice_plan_index == 1
    assert events[0].type == "training_rejected"
    assert events[0].data["reason"] == (
        "trainer returned without confirming the lesson"
    )


def test_loremaster_does_not_practice_without_relevant_points() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.loremaster_step = 2
    policy.prompt_ready = True
    policy.text = """
Skills known:
                 magic missile:  46%              evocation magiks:  23%
You have 1 physical and 0 intellectual practices remaining.
"""
    state = CharacterState(
        level=7,
        hp=105,
        max_hp=105,
        room_name="The Loremaster",
        room_vnum="3726",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "west"


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
    assert fight.command == "consider boar"
    policy.after_command(fight)
    policy.observe_text("The perfect match!\n")
    policy.prompt_ready = True
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
    assert fight.command == "consider boar"
    policy.after_command(fight)
    policy.observe_text("A wild boar looks like an easy kill.\n")
    policy.prompt_ready = True
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


def test_arena_kill_limit_exits_before_the_target_level() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=7, arena_kill_limit=2)
    policy.in_world = True
    policy.arena_queried = True
    policy.current_room = "3729"
    policy.prompt_ready = True
    policy.completed_kills = [
        {"mob_name": "wild boar", "xp_gained": 20},
        {"mob_name": "giant lizard", "xp_gained": 20},
    ]
    state = CharacterState(
        level=6,
        hp=80,
        max_hp=96,
        room_name="The Mud School Arena",
        room_vnum="3729",
    )

    leave = policy.next_decision(state)

    assert leave is not None
    assert leave.command == "up"
    assert "2 kills" in leave.reason


def test_arena_kill_limit_routes_from_safety_to_the_healer() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=7, arena_kill_limit=2)
    policy.in_world = True
    policy.prompt_ready = True
    policy.course_complete = True
    policy.provisioned = True
    policy.practiced = True
    policy.arena_segment_leaving = True
    policy.completed_kills = [
        {"mob_name": "wild boar", "xp_gained": 20},
        {"mob_name": "giant lizard", "xp_gained": 20},
    ]
    safety = CharacterState(
        level=6,
        hp=96,
        max_hp=96,
        room_name="Safety",
        room_vnum="3737",
    )

    decision = policy.next_decision(safety)

    assert decision is not None
    assert decision.command == "enter portal"
    assert "healer recovery" in decision.reason


def test_target_level_exits_to_healer_before_saving() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=7)
    policy.in_world = True
    policy.prompt_ready = True
    policy.course_complete = True
    policy.provisioned = True
    policy.practiced = True
    arena = CharacterState(
        level=7,
        hp=105,
        max_hp=105,
        room_name="The Mud School Arena",
        room_vnum="3729",
    )

    leave = policy.next_decision(arena)

    assert leave is not None
    assert leave.command == "up"

    policy.prompt_ready = True
    leave_safety = policy.next_decision(
        CharacterState(
            level=7,
            hp=105,
            max_hp=105,
            room_name="Safety",
            room_vnum="3737",
        )
    )

    assert leave_safety is not None
    assert leave_safety.command == "enter portal"

    policy.prompt_ready = True
    descend = policy.next_decision(
        CharacterState(
            level=7,
            hp=105,
            max_hp=105,
            room_name="The Entrance to the Mud School",
            room_vnum="3725",
        )
    )
    assert descend is not None
    assert descend.command == "down"

    policy.prompt_ready = True
    reach_healer = policy.next_decision(
        CharacterState(
            level=7,
            hp=105,
            max_hp=105,
            room_name="The Temple Of Midgaard",
            room_vnum="3001",
        )
    )
    assert reach_healer is not None
    assert reach_healer.command == "north"

    policy.prompt_ready = True
    save = policy.next_decision(
        CharacterState(
            level=7,
            hp=105,
            max_hp=105,
            move=200,
            max_move=200,
            mana=100,
            max_mana=100,
            room_name="By the Temple Altar",
            room_vnum="3054",
            room_flags=["safe", "healing"],
        )
    )
    assert save is not None
    assert save.command == "save"


def test_target_level_exit_precedes_safe_arena_recovery() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=7)
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        level=7,
        hp=90,
        max_hp=120,
        mana=80,
        max_mana=100,
        move=180,
        max_move=200,
        room_name="The Mud School Arena",
        room_vnum="3729",
        room_flags=["safe"],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "up"
    assert policy.waiting_for_heal is False


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
    assert decision.command == "consider wolf"
    policy.after_command(decision)
    policy.observe_text("The perfect match!\n")
    policy.prompt_ready = True
    decision = policy.next_decision(state)
    assert decision is not None
    assert decision.command == "kill wolf"


def test_arena_skips_runtime_target_in_the_no_match_band() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=8)
    policy.in_world = True
    policy.arena_queried = True
    policy.current_room = "3729"
    policy.room_targets["3729"] = ["wolf", "wild boar"]
    policy.prompt_ready = True
    state = CharacterState(
        level=7,
        hp=105,
        max_hp=105,
        room_name="The Mud School Arena",
        room_vnum="3729",
    )

    consider_wolf = policy.next_decision(state)
    assert consider_wolf is not None
    assert consider_wolf.command == "consider wolf"
    policy.after_command(consider_wolf)
    policy.observe_text("A wolf is no match for you.\n")
    policy.prompt_ready = True
    skip = policy.next_decision(state)

    assert skip is not None
    assert skip.command == "look"
    assert "wolf" in policy.defeated_targets["3729"]
    policy.after_command(skip)
    policy.prompt_ready = True
    consider_boar = policy.next_decision(state)
    assert consider_boar is not None
    assert consider_boar.command == "consider boar"


@pytest.mark.parametrize(
    "message",
    [
        "You can kill a wolf naked and weaponless.\n",
        "A wolf is no match for you.\n",
        "You can destroy a dummy naked and weaponless.\n",
        "A dummy is no match for your offensive capabilities.\n",
    ],
)
def test_consider_rejects_every_low_xp_branch(message: str) -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.consider_target = "target"

    policy.observe_text(message)

    assert policy.consider_viable is False


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


def test_arena_safety_room_routes_to_the_temple_healer() -> None:
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

    route = policy.next_decision(state)

    assert route is not None
    assert route.command == "enter portal"
    assert "temple healer" in route.reason


def test_missing_arena_target_is_removed_before_the_next_decision() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=3)
    policy.current_room = "3728"
    policy.active_target = "wild boar"
    policy.room_targets["3728"] = ["wild boar"]

    policy.observe_text("They aren't here.")

    assert policy.combat_active is False
    assert policy.active_target is None
    assert policy.room_targets["3728"] == []
    assert policy.defeated_targets.get("3728", set()) == set()
    assert policy.missing_targets["3728"] == {"wild boar"}


def test_fastwalk_target_absence_is_recorded_without_marking_a_kill() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
        fastwalk_attack_target="kobold",
    )
    policy.current_room = "4018"
    policy.active_target = "kobold"
    policy.room_targets["4018"] = ["kobold"]

    policy.observe_text("They aren't here.")

    assert policy.fastwalk_target_absent is True
    assert policy.defeated_targets.get("4018", set()) == set()
    assert policy.missing_targets["4018"] == {"kobold"}


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


def test_completed_arena_patrol_leaves_center_via_a_wall() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=6)
    policy.in_world = True
    policy.arena_queried = True
    policy.prompt_ready = True
    policy.arena_visited_rooms.update(str(vnum) for vnum in range(3728, 3738))
    policy.room_query_counts["3732"] = 1
    state = CharacterState(
        level=5,
        hp=90,
        max_hp=90,
        room_name="The Mud School Arena",
        room_vnum="3732",
        exits={"n": "3728", "e": "3733", "s": "3735", "w": "3731"},
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "north"
    assert "reach an arena wall" in decision.reason
    assert policy.arena_respawn_due is not None


def test_outside_safe_band_arena_patrol_finishes_without_waiting_for_respawn() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        objective_level=8,
        arena_kill_limit=10,
    )
    policy.in_world = True
    policy.arena_queried = True
    policy.prompt_ready = True
    policy.arena_skipped_outside_safe_band = True
    policy.arena_visited_rooms.update(str(vnum) for vnum in range(3728, 3738))
    policy.room_query_counts["3736"] = 1
    state = CharacterState(
        level=7,
        hp=105,
        max_hp=105,
        room_name="The Mud School Arena",
        room_vnum="3736",
        exits={"n": "3733", "u": "3737", "w": "3735"},
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "up"
    assert "outside the safe live-consider band" in decision.reason
    assert policy.arena_segment_leaving is True
    assert policy.arena_no_viable_targets is True
    assert policy.arena_respawn_due is None


def test_empty_arena_patrol_vacates_mud_school_for_the_respawn_window() -> None:
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

    leave = policy.next_decision(state)

    assert leave is not None
    assert leave.command == "enter portal"

    state.room_name = "The Entrance to the Mud School"
    state.room_vnum = "3725"
    policy.prompt_ready = True
    outside = policy.next_decision(state)
    assert outside is not None
    assert outside.command == "down"

    state.room_name = "The Temple Of Midgaard"
    state.room_vnum = "3001"
    policy.prompt_ready = True
    healer = policy.next_decision(state)
    assert healer is not None
    assert healer.command == "north"

    state.room_name = "By the Temple Altar"
    state.room_vnum = "3054"
    policy.prompt_ready = True
    sleep = policy.next_decision(state)
    assert sleep is not None
    assert sleep.command == "sleep"


def test_safe_room_gmcp_update_reopens_expired_respawn_wait() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=3)
    policy.in_world = True
    policy.arena_respawn_due = time.monotonic() - 1
    state = CharacterState(
        level=2,
        hp=60,
        max_hp=60,
        position=4,
        room_name="By the Temple Altar",
        room_vnum="3054",
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


def test_expired_arena_reset_reenters_school_from_midgaard() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=3)
    policy.in_world = True
    policy.prompt_ready = True
    policy.arena_respawn_due = time.monotonic() - 1

    decision = policy.next_decision(
        CharacterState(
            level=2,
            hp=60,
            max_hp=60,
            position=7,
            room_name="The Temple Of Midgaard",
            room_vnum="3001",
        )
    )

    assert decision is not None
    assert decision.command == "up"
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
    assert decision.command == "enter portal"
    policy.after_command(decision)

    policy.prompt_ready = True
    decision = policy.next_decision(
        CharacterState(room_name="The Temple Of Midgaard", room_vnum="3001", position=7)
    )
    assert decision is not None
    assert decision.command == "north"

    policy.prompt_ready = True
    decision = policy.next_decision(
        CharacterState(room_name="By the Temple Altar", room_vnum="3054", position=7)
    )
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


def test_resupply_policy_borrows_after_an_insufficient_funds_response() -> None:
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
    assert decision.command == "down"
    assert policy.emergency_borrowing is True


def test_resupply_policy_recognizes_live_bulk_purchase_rejection() -> None:
    policy = StarterPolicy(_spec(), "swordfish", resupply_only=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.food_ordered = True
    policy.observe_text(
        "The Quartermaster tells you 'A big pot pie? You must be kidding - "
        "you can't even afford a single one, let alone 6!'"
    )
    assert policy.insufficient_funds is True
    assert policy.food_ordered is False
    state = CharacterState(
        room_name="General Supplies",
        room_vnum="3724",
        inventory=[[{"short_desc": "a steel barrel-helm"}]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "down"
    assert policy.emergency_borrowing is True


def test_emergency_bank_loan_returns_to_general_supplies_once() -> None:
    policy = StarterPolicy(_spec(), "swordfish", resupply_only=True)
    policy.in_world = True
    policy.emergency_borrowing = True
    route = (
        ("General Supplies", "3724", "down"),
        ("The Entrance to the Mud School", "3725", "down"),
        ("The Temple Of Midgaard", "3001", "south"),
        ("The Temple Square", "3005", "east"),
        ("Bank Entrance", "3006", "east"),
        ("Dragonhoard Bank", "3007", "borrow 300"),
        ("Dragonhoard Bank", "3007", "west"),
        ("Bank Entrance", "3006", "west"),
        ("The Temple Square", "3005", "north"),
        ("The Temple Of Midgaard", "3001", "up"),
        ("The Entrance to the Mud School", "3725", "up"),
        ("General Supplies", "3724", "buy 6 pie"),
    )

    for room_name, room_vnum, expected in route:
        decision = policy._resupply_decision(
            CharacterState(
                room_name=room_name,
                room_vnum=room_vnum,
                position=7,
                move=180,
                max_move=180,
            )
        )
        assert decision is not None
        assert decision.command == expected

    assert policy.emergency_borrowing is False
    assert policy.emergency_borrow_complete is True


def test_resupply_policy_does_not_eat_until_purchase_is_in_inventory() -> None:
    policy = StarterPolicy(_spec(), "swordfish", resupply_only=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.food_ordered = True
    policy.needs_food = True
    policy.needs_drink = False
    state = CharacterState(
        hp=96,
        max_hp=96,
        room_name="General Supplies",
        room_vnum="3724",
        inventory=[[{"short_desc": "a buffalo water skin"}]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command != "eat pie"


def test_resupply_policy_retries_affordable_quartermaster_quantity() -> None:
    policy = StarterPolicy(_spec(), "swordfish", resupply_only=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.food_ordered = True
    policy.needs_food = True
    policy.needs_drink = False
    policy.observe_text(
        "The Quartermaster tells you 'You can only afford 1 of those!'"
    )
    state = CharacterState(
        hp=96,
        max_hp=96,
        room_name="General Supplies",
        room_vnum="3724",
        inventory=[[{"short_desc": "a buffalo water skin"}]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "buy 1 pie"
    assert policy.food_ordered is True
    assert policy.affordable_pies_ordered is True


def test_emergency_resupply_becomes_visible_and_retries_rejected_order() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.prompt_ready = True
    policy.needs_food = True
    policy.food_ordered = True
    policy.observe_text(
        "The Quartermaster says 'I don't trade with folks I can't see.'"
    )
    supplies = CharacterState(
        room_name="General Supplies",
        room_vnum="3724",
        position=7,
        affects=[[{"name": "invis", "duration": "8"}]],
    )

    visible = policy.next_decision(supplies)

    assert visible is not None
    assert visible.command == "vis"
    assert policy.food_ordered is False
    policy.after_command(visible)
    policy.prompt_ready = True
    supplies.affects = [[]]

    retry = policy.next_decision(supplies)

    assert retry is not None
    assert retry.command == "buy 6 pie"


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
        ("The Bakery", "3009", "south"),
        ("Main Street", "3013", "west"),
        ("Main Street", "3012", "south"),
        ("Entrance to Mage's Guild", "3017", "south"),
        ("Mage's Bar", "3018", "east"),
    )
    for room_name, room_vnum, expected_command in rooms_and_commands:
        decision = policy.next_decision(
            CharacterState(
                room_name=room_name,
                room_vnum=room_vnum,
                position=7,
                inventory=[[{"short_desc": "a big pot pie"}]],
            )
        )
        assert decision is not None
        assert decision.command == expected_command
        policy.after_command(decision)
        policy.prompt_ready = True

    decision = policy.next_decision(
        CharacterState(room_name="Mage's Laboratory", room_vnum="3019", position=7)
    )
    assert decision is not None
    assert decision.command == "west"

    policy.prompt_ready = True
    decision = policy.next_decision(
        CharacterState(room_name="By the Temple Altar", room_vnum="3054", position=7)
    )
    assert decision is not None
    assert decision.command == "save"


def test_liquidation_groups_items_by_shop_and_stays_for_the_next_sale() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    policy.in_world = True
    policy.prompt_ready = True
    home = CharacterState(
        room_name="Mage's Laboratory",
        room_vnum="3019",
        position=7,
        inventory=[
            [
                {"short_desc": "a leather jerkin", "quan": "1"},
                {"short_desc": "a length of metal piping", "quan": "1"},
                {"short_desc": "a pair of black leather boots", "quan": "1"},
            ]
        ],
    )

    policy.next_decision(home)

    assert [(keyword, shop.name) for keyword, shop in policy.sale_plan] == [
        ("jerkin", "Leather Shop"),
        ("boots", "Leather Shop"),
        ("piping", "Weapon Shop"),
    ]

    policy.sale_index = 0
    policy.sale_phase = "inventory"
    policy.prompt_ready = True
    next_sale = policy.next_decision(
        CharacterState(
            room_name="Leather Shop",
            room_vnum=policy.sale_plan[0][1].room_vnum,
            position=7,
        )
    )

    assert next_sale is not None
    assert next_sale.command == "value boots"
    assert policy.sale_index == 1
    assert policy.sale_phase == "sell"

    sale = policy._liquidate_loot_decision(
        CharacterState(
            room_name="Leather Shop",
            room_vnum=policy.sale_plan[1][1].room_vnum,
            position=7,
        )
    )

    assert sale is not None
    assert sale.command == "sell boots"


def test_city_restock_policy_reaches_fountain_from_mage_laboratory() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_restock=True)
    policy.in_world = True
    policy.prompt_ready = True

    route = (
        ("Mage's Laboratory", "3019", "west"),
        ("Mage's Bar", "3018", "north"),
        ("Entrance to Mage's Guild", "3017", "north"),
        ("Main Street", "3012", "east"),
        ("Main Street", "3013", "east"),
        ("Market Square", "3014", "north"),
    )
    for room_name, room_vnum, expected_command in route:
        decision = policy.next_decision(
            CharacterState(room_name=room_name, room_vnum=room_vnum, position=7)
        )
        assert decision is not None
        assert decision.command == expected_command
        policy.after_command(decision)
        policy.prompt_ready = True

    at_fountain = policy.next_decision(
        CharacterState(room_name="The Temple Square", room_vnum="3005", position=7)
    )
    assert at_fountain is not None
    assert at_fountain.command == "fill skin"


def test_city_restock_restarts_safely_when_reconnected_in_bakery() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_restock=True)
    policy.in_world = True
    policy.prompt_ready = True

    decision = policy.next_decision(
        CharacterState(
            room_name="The Bakery",
            room_vnum="3009",
            position=7,
            inventory=[[{"short_desc": "a buffalo water skin"}]],
        )
    )

    assert decision is not None
    assert decision.command == "south"


def test_city_restock_cannot_complete_outside_mage_laboratory() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_restock=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.city_restock_step = 7

    decision = policy.next_decision(
        CharacterState(
            room_name="An Unknown Room",
            room_vnum="9999",
            position=7,
            inventory=[[{"short_desc": "a big pot pie"}]],
        )
    )

    assert decision is None
    assert policy.failure is not None


def test_city_restock_retries_the_quantity_the_baker_says_is_affordable() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_restock=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.city_restock_step = 5
    policy.observe_text("The baker tells you 'You can only afford 2 of those!'")

    decision = policy.next_decision(
        CharacterState(room_name="The Bakery", room_vnum="3009", position=7)
    )

    assert decision is not None
    assert decision.command == "buy 2 pie"
    assert policy.affordable_pies_ordered is True


def test_city_restock_becomes_visible_and_retries_rejected_purchase() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_restock=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.city_restock_step = 5
    policy.observe_text("The baker says 'I don't trade with folks I can't see.'")
    bakery = CharacterState(
        room_name="The Bakery",
        room_vnum="3009",
        position=7,
        affects=[[{"name": "invis", "duration": "5"}]],
    )

    visible = policy.next_decision(bakery)

    assert visible is not None
    assert visible.command == "vis"
    assert policy.city_restock_step == 4
    policy.after_command(visible)
    policy.prompt_ready = True
    bakery.affects = [[]]

    retry = policy.next_decision(bakery)

    assert retry is not None
    assert retry.command == "buy 6 pie"


def test_city_restock_caps_pie_order_to_free_carry_weight() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_restock=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.city_restock_step = 4

    decision = policy.next_decision(
        CharacterState(
            room_name="The Bakery",
            room_vnum="3009",
            position=7,
            stats={"carry_wt": 111, "maxcarry_wt": 140},
        )
    )

    assert decision is not None
    assert decision.command == "buy 5 pie"


def test_city_restock_backs_off_after_weight_rejection() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_restock=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.city_restock_step = 5
    policy.last_pie_order_quantity = 6
    policy.observe_text("You can't carry that much weight.")

    decision = policy.next_decision(
        CharacterState(
            room_name="The Bakery",
            room_vnum="3009",
            position=7,
        )
    )

    assert decision is not None
    assert decision.command == "buy 5 pie"


def test_city_restock_fails_when_purchase_audit_has_no_pie() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_restock=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.city_restock_step = 6

    decision = policy.next_decision(
        CharacterState(
            room_name="The Bakery",
            room_vnum="3009",
            position=7,
            inventory=[[{"short_desc": "a buffalo water skin"}]],
        )
    )

    assert decision is None
    assert policy.failure == "city restock inventory audit found no pie after purchase"


def test_city_restock_borrows_for_food_when_no_pie_is_affordable() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_restock=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.city_restock_step = 5
    policy.observe_text(
        "The baker tells you 'You can't even afford a single one!'"
    )
    route = (
        ("The Bakery", "3009", "south"),
        ("Main Street", "3013", "east"),
        ("Market Square", "3014", "north"),
        ("The Temple Square", "3005", "east"),
        ("Bank Entrance", "3006", "east"),
        ("Dragonhoard Bank", "3007", "borrow 300"),
        ("Dragonhoard Bank", "3007", "west"),
        ("Bank Entrance", "3006", "west"),
        ("The Temple Square", "3005", "south"),
        ("Market Square", "3014", "west"),
        ("Main Street", "3013", "north"),
        ("The Bakery", "3009", "buy 6 pie"),
    )

    for room_name, room_vnum, expected in route:
        decision = policy.next_decision(
            CharacterState(room_name=room_name, room_vnum=room_vnum, position=7)
        )
        assert decision is not None
        assert decision.command == expected
        policy.after_command(decision)
        policy.prompt_ready = True


def test_fastwalk_research_walks_from_bakery_toward_recall() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
    )
    policy.in_world = True
    policy.prompt_ready = True

    decision = policy.next_decision(
        CharacterState(
            room_name="The Bakery",
            room_vnum="3009",
            position=7,
            hp=100,
            max_hp=100,
            mana=200,
            max_mana=200,
            move=200,
            max_move=200,
        )
    )

    assert decision is not None
    assert decision.command == "south"
    assert policy.fastwalk_recall_started is False


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
    assert decision.command == "west"

    policy.prompt_ready = True
    decision = policy.next_decision(
        CharacterState(room_name="By the Temple Altar", room_vnum="3054", position=7)
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


def test_guildmaster_research_routes_to_healer_instead_of_sleeping_at_mage_lab() -> None:
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
    assert decision.command == "west"
    assert "healer" in decision.reason


def test_liquidation_routes_movement_recovery_to_temple_healer() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    state = CharacterState(
        hp=157,
        max_hp=157,
        mana=133,
        max_mana=133,
        move=104,
        max_move=210,
        position=7,
        room_name="Mage's Bar",
        room_vnum="3018",
        room_flags=["safe"],
    )

    decision = policy._recovery_decision(state)

    assert decision is not None
    assert decision.command == "north"
    assert "temple healer" in decision.reason
    assert policy.waiting_for_heal is False


def test_recovery_decision_names_the_midgaard_healer_when_sleeping() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=8)
    state = CharacterState(
        hp=110,
        max_hp=110,
        mana=206,
        max_mana=293,
        move=40,
        max_move=210,
        position=7,
        room_name="By the Temple Altar",
        room_vnum="3054",
        room_flags=["safe", "healing"],
    )

    decision = policy._recovery_decision(state)

    assert decision is not None
    assert decision.command == "sleep"
    assert decision.reason == (
        "sleep beside the Midgaard healer to recover movement or mana"
    )


def test_liquidation_does_not_interrupt_an_active_safe_shop_route() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    policy.sale_phase = "home"
    state = CharacterState(
        hp=110,
        max_hp=110,
        mana=293,
        max_mana=293,
        move=95,
        max_move=210,
        position=7,
        room_name="Mage's Bar",
        room_vnum="3018",
        room_flags=["safe"],
    )

    assert policy._recovery_decision(state) is None


def test_leveling_routes_loremaster_recovery_to_temple_healer() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=8)
    state = CharacterState(
        hp=123,
        max_hp=123,
        mana=145,
        max_mana=145,
        move=95,
        max_move=210,
        position=7,
        room_name="The Loremaster",
        room_vnum="3726",
        room_flags=["safe"],
    )

    decision = policy._recovery_decision(state)

    assert decision is not None
    assert decision.command == "west"
    assert "temple healer" in decision.reason


def test_loremaster_records_unspendable_combat_practice_as_deferred() -> None:
    policy = StarterPolicy(
        _spec(
            name="Kestrel",
            race="drow",
            gender="male",
            **{"class": "thief", "subclass": "ninja"},
        ),
        "swordfish",
        practice_types_spent=frozenset({"intellectual"}),
    )
    policy.in_world = True
    policy.loremaster_step = 2
    policy.prompt_ready = True
    policy.text = """
Skills known:
                 hide:  23%                 second attack:  35%
                sneak:  99%             stealth techniques:  45%
       armed combat knowledge:  41%
You have 2 physical and 1 intellectual practices remaining.
"""
    state = CharacterState(
        level=7,
        hp=123,
        max_hp=123,
        room_name="The Loremaster",
        room_vnum="3726",
    )

    decision = policy.next_decision(state)
    events = policy.drain_training_events()

    assert decision is not None
    assert decision.command == "west"
    assert [event.type for event in events] == ["training_deferred"]
    assert events[0].data["practice_type"] == "physical"
    assert policy.practice_types_spent == {"physical", "intellectual"}


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
    assert decision.command == "west"

    policy.prompt_ready = True
    decision = policy.next_decision(
        CharacterState(room_name="By the Temple Altar", room_vnum="3054", position=7)
    )
    assert decision is not None
    assert decision.command == "save"


def test_fastwalk_research_requires_recall_and_reverses_when_needed() -> None:
    route = route_named("moria")
    policy = StarterPolicy(_spec(), "swordfish", fastwalk_route=route)
    policy.in_world = True
    policy.prompt_ready = True

    recall = policy.next_decision(
        CharacterState(room_name="The Lane", room_vnum="3501", position=7)
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


def test_fastwalk_unexpected_combat_flees_then_recalls_and_records_failure() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True

    flee = policy.next_decision(
        CharacterState(room_name="Forest clearing", room_vnum="6008", position=7)
    )

    assert flee is not None
    assert flee.command == "flee"
    assert policy.fastwalk_abort_reason is not None
    policy.after_command(flee)
    policy.observe_text("You flee from combat!")
    policy.prompt_ready = True

    recall = policy.next_decision(
        CharacterState(room_name="Forest path", room_vnum="6011", position=7)
    )

    assert recall is not None
    assert recall.command == "recall"
    assert "unexpected combat" in recall.reason


def test_field_hunt_waits_for_delayed_gmcp_enemy_assessment() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "warrior", "subclass": "knight"}),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_hunt_stops=foundry_level_six_hunt_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.active_target = "Olog"
    state = CharacterState(
        level=6,
        hp=138,
        max_hp=138,
        position=6,
        room_name="Muddy Tunnel",
        room_vnum="109",
    )

    assessment_wait = policy.next_decision(state)

    assert assessment_wait is None
    assert policy.awaiting_enemy_assessment is True
    assert policy.fastwalk_emergency_recall_pending is False

    policy.observe_events(
        [
            GameEvent(
                "enemies_changed",
                "gmcp",
                {"value": [[{"name": "Olog", "level": "2"}]]},
            )
        ],
        state,
    )
    decision = policy.next_decision(state)

    assert policy.fastwalk_attack_started is True
    assert policy.fastwalk_attack_target == "Olog"
    assert decision is None
    assert policy.fastwalk_emergency_recall_pending is False


def test_incoming_damage_text_blocks_field_navigation_before_gmcp_enemy() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_hunt_stops=foundry_level_six_hunt_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(policy.fastwalk_route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_stop_index = 1
    policy.fastwalk_hunt_move_index = len(
        policy.fastwalk_hunt_stops[1].route
    )
    state = CharacterState(
        level=6,
        hp=74,
        max_hp=100,
        mana=147,
        max_mana=267,
        move=131,
        max_move=200,
        position=7,
        room_name="Ushog's Quarters",
        room_vnum="112",
    )

    policy.observe_text("Ushog's slash injures you! Ushog is in excellent condition.")
    decision = policy.next_decision(state)

    assert policy.combat_active is True
    assert policy.awaiting_enemy_assessment is True
    assert decision is None
    assert policy.fastwalk_returning is False


def test_fastwalk_defends_against_the_configured_endpoint_target() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_attack_target="Olog",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(policy.fastwalk_route.commands)
    policy.combat_active = True
    policy.observe_text("Olog, the Goblin Soldier, crouches in the muck.\n")

    decision = policy.next_decision(
        CharacterState(
            room_name="Muddy Tunnel",
            room_vnum="108",
            mana=268,
            max_mana=268,
            position=7,
        )
    )

    assert decision is not None
    assert decision.command == "cast 'magic missile' Olog"
    assert policy.fastwalk_attack_started is True
    assert policy.fastwalk_abort_reason is None


def test_fastwalk_flees_and_recalls_when_field_health_reaches_seventy_percent() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_attack_target="Olog",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(policy.fastwalk_route.commands)
    policy.fastwalk_attack_started = True
    policy.combat_active = True
    policy.active_target = "Olog"
    state = CharacterState(
        hp=70,
        max_hp=100,
        mana=200,
        max_mana=240,
        position=6,
        room_name="Muddy Tunnel",
        room_vnum="108",
    )

    flee = policy.next_decision(state)

    assert flee is not None
    assert flee.command == "flee"
    assert "70%" in flee.reason
    assert policy.fastwalk_emergency_recall_pending is True
    assert policy.fastwalk_abort_reason is not None
    policy.after_command(flee)
    policy.prompt_ready = True
    assert policy.next_decision(state) is None

    policy.observe_text("You flee from combat!\n")
    policy.prompt_ready = True

    recall = policy.next_decision(state)

    assert recall is not None
    assert recall.command == "recall"


def test_fastwalk_finishes_single_lower_level_wounded_attacker_to_fifty_percent() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(FieldHuntStop(("west",), required_items=("large sack",)),),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(policy.fastwalk_route.commands)
    policy.fastwalk_attack_started = True
    policy.combat_active = True
    policy.active_target = "the goblin lieutenant"
    state = CharacterState(
        level=7,
        hp=60,
        max_hp=100,
        mana=200,
        max_mana=240,
        position=6,
        room_name="The Front of the Inn",
        room_vnum="3570",
        enemies=[
            [
                {
                    "name": "the goblin lieutenant",
                    "level": "6",
                    "hp": "29",
                    "maxhp": "70",
                }
            ]
        ],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "cast 'magic missile' lieutenant"
    assert policy.fastwalk_abort_reason is None


def test_fastwalk_fights_viable_opportunistic_attacker_instead_of_fleeing() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry captain"),
        fastwalk_attack_target="Ushog",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = 14
    state = CharacterState(
        level=6,
        hp=96,
        max_hp=96,
        mana=268,
        max_mana=268,
        room_name="Muddy Tunnel",
        room_vnum="109",
        position=6,
    )
    policy.observe_events(
        [
            GameEvent(
                "enemies_changed",
                "gmcp",
                {"value": [[{"name": "Olog", "level": "4"}]]},
            )
        ],
        state,
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "cast 'magic missile' Olog"
    assert policy.fastwalk_attack_target == "Olog"
    assert policy.fastwalk_attack_started is True
    assert policy.fastwalk_abort_reason is None


def test_fastwalk_defends_against_one_level_higher_interceptor() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=moria_level_seven_orc_hunt_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    state = CharacterState(
        level=7,
        hp=123,
        max_hp=123,
        mana=145,
        max_mana=145,
        room_name="The Trail to Miden'nir",
        room_vnum="3505",
        position=6,
        enemies=[[{"name": "the goblin", "level": "8", "hp": "86"}]],
    )
    policy.observe_events(
        [
            GameEvent(
                "enemies_changed",
                "gmcp",
                {"value": [[{"name": "the goblin", "level": "8"}]]},
            )
        ],
        state,
    )

    decision = policy.next_decision(state)

    assert decision is None
    assert policy.fastwalk_attack_started is True
    assert policy.fastwalk_attack_target == "the goblin"
    assert policy.fastwalk_emergency_recall_pending is False


def test_fastwalk_does_not_adopt_multiple_opportunistic_attackers() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=moria_level_seven_orc_hunt_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.combat_active = True
    policy.active_target = "the goblin"
    policy.active_target_level = 7
    state = CharacterState(
        level=7,
        hp=110,
        max_hp=110,
        room_name="The Trail to Miden'nir",
        room_vnum="3505",
        position=6,
        enemies=[[
            {"name": "the goblin", "level": "7"},
            {"name": "the goblin lieutenant", "level": "7"},
        ]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "flee"
    assert policy.fastwalk_emergency_recall_pending is True


def test_fastwalk_failed_recall_does_not_adopt_a_pursuing_mobile() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_attack_target="mountain goblin",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(policy.fastwalk_route.commands)
    policy.fastwalk_returning = True
    policy.fastwalk_abort_reason = "unexpected combat interrupted the field hunt"
    policy.combat_active = True
    policy.active_target = "the goblin lieutenant"
    state = CharacterState(
        level=7,
        hp=110,
        max_hp=110,
        mana=293,
        max_mana=293,
        room_name="Deep in the Forest of Miden'nir",
        room_vnum="3556",
        position=6,
        enemies=[[{"name": "the goblin lieutenant", "level": "7"}]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "flee"
    assert "recall was interrupted" in decision.reason
    assert policy.fastwalk_emergency_recall_pending is True
    assert policy.fastwalk_attack_target == "mountain goblin"
    assert policy.fastwalk_attack_started is False


def test_fastwalk_fights_trivial_attacker_instead_of_paying_flee_penalty() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
        fastwalk_attack_target="large hobgoblin",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.known_skills.add("chill touch")
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = 4
    state = CharacterState(
        level=9,
        hp=126,
        max_hp=126,
        mana=321,
        max_mana=343,
        room_name="Main Street",
        room_vnum="3013",
        position=6,
    )
    policy.observe_events(
        [
            GameEvent(
                "enemies_changed",
                "gmcp",
                {"value": [[{"name": "the drunk", "level": "1"}]]},
            )
        ],
        state,
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "cast 'chill touch' drunk"
    assert policy.fastwalk_attack_target == "the drunk"
    assert policy.fastwalk_attack_started is True
    assert policy.fastwalk_abort_reason is None


def test_field_expedition_fights_viable_outbound_attacker_from_gmcp() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(
            FieldHuntStop(("south",), actions=("get sack",)),
        ),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = 3
    policy.combat_active = True
    state = CharacterState(
        level=7,
        hp=105,
        max_hp=105,
        mana=289,
        max_mana=289,
        room_name="The South Bridge",
        room_vnum="3504",
        position=6,
        enemies=[[{"name": "the goblin lieutenant", "level": "5"}]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "cast 'magic missile' lieutenant"
    assert policy.active_target == "the goblin lieutenant"
    assert policy.fastwalk_attack_target == "the goblin lieutenant"
    assert policy.fastwalk_attack_started is True
    assert policy.fastwalk_abort_reason is None


def test_field_expedition_records_incidental_kill_with_action_only_stop() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(
            FieldHuntStop((), actions=("get sack",)),
        ),
    )
    policy.current_room = "3508"
    policy.combat_active = True
    policy.active_target = "the goblin"

    policy.observe_text(
        "The goblin is DEAD!!\n"
        "You receive 150 experience points for the kill.\n"
        "You gained a total of 219 experience points!\n"
    )

    assert policy.completed_kills == [
        {"mob_name": "the goblin", "xp_gained": 219}
    ]
    assert policy.fastwalk_hunt_stop_killed is False


def test_field_expedition_retries_move_rejected_by_combat() -> None:
    route = route_named("ambush")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(
            FieldHuntStop(("west", "south"), actions=("get sack",)),
        ),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    policy.current_room = "3505"
    state = CharacterState(
        hp=105,
        max_hp=105,
        mana=289,
        max_mana=289,
        position=7,
        room_vnum="3505",
    )

    move = policy.next_decision(state)
    assert move is not None
    assert move.command == "west"
    policy.after_command(move)
    assert policy.fastwalk_hunt_move_index == 1

    policy.observe_text("No way!  You are still fighting!\n")

    assert policy.fastwalk_hunt_move_index == 0
    assert policy.pending_fastwalk_hunt_move is False


def test_fastwalk_continues_to_requested_target_after_safe_incidental_loot() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry captain"),
        fastwalk_attack_target="Ushog",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = 14
    policy.fastwalk_attack_target = "Olog"
    policy.fastwalk_attack_started = True
    policy.fastwalk_last_kill_target = "Olog"
    policy.pending_loot_rooms.add("108")
    state = CharacterState(
        level=6,
        hp=96,
        max_hp=96,
        room_name="Muddy Tunnel",
        room_vnum="108",
        position=7,
    )

    loot = policy.next_decision(state)
    policy.prompt_ready = True
    sacrifice = policy.next_decision(state)
    policy.prompt_ready = True
    inventory = policy.next_decision(state)

    assert loot is not None
    assert loot.command == "get all corpse"
    assert sacrifice is not None
    assert sacrifice.command == "sacrifice corpse"
    assert inventory is not None
    assert inventory.command == "inventory"
    assert policy.fastwalk_recall_after_loot is False
    assert policy.fastwalk_attack_target == "Ushog"
    assert policy.fastwalk_attack_started is False


def test_fastwalk_eats_fresh_body_part_without_waiting_for_hunger() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.current_room = "4505"
    policy.pending_loot_rooms.add("4505")
    policy.needs_food = False
    policy.observe_text("The war dog's leg is sliced from his body.")
    state = CharacterState(
        room_name="In a forest clearing",
        room_vnum="4505",
        position=7,
    )

    commands: list[str] = []
    for _ in range(5):
        decision = policy.next_decision(state)
        assert decision is not None
        commands.append(decision.command)
        policy.after_command(decision)
        policy.prompt_ready = True

    assert commands == [
        "get leg",
        "eat leg",
        "get all corpse",
        "sacrifice corpse",
        "inventory",
    ]


@pytest.mark.parametrize(
    "rejection",
    [
        "You are too full to eat more.",
        "That's not edible.",
    ],
)
def test_uneaten_body_part_is_dropped_and_sacrificed(rejection: str) -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.current_room = "4505"
    policy.pending_loot_rooms.add("4505")
    policy.observe_text("The war dog's head is separated from his body.")
    state = CharacterState(
        hp=60,
        max_hp=60,
        room_name="In a forest clearing",
        room_vnum="4505",
        position=7,
    )

    commands: list[str] = []
    for _ in range(2):
        decision = policy.next_decision(state)
        assert decision is not None
        commands.append(decision.command)
        policy.after_command(decision)
        policy.prompt_ready = True

    policy.observe_text(rejection)
    policy.prompt_ready = True
    for _ in range(2):
        decision = policy.next_decision(state)
        assert decision is not None
        commands.append(decision.command)
        policy.after_command(decision)
        policy.prompt_ready = True

    assert commands == ["get head", "eat head", "drop head", "sacrifice head"]


def test_fastwalk_waits_for_enemy_snapshot_before_fleeing() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry captain"),
        fastwalk_attack_target="Ushog",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = 14
    policy.combat_active = True
    state = CharacterState(
        level=6,
        hp=96,
        max_hp=96,
        mana=268,
        max_mana=268,
        room_name="Muddy Tunnel",
        room_vnum="109",
        position=6,
    )

    assert policy.next_decision(state) is None
    assert policy.awaiting_enemy_assessment is True
    assert policy.active_target is None
    assert policy.fastwalk_abort_reason is None

    state.enemies = [[{"name": "Olog", "level": "4"}]]
    policy.observe_events(
        [
            GameEvent(
                "enemies_changed",
                "gmcp",
                {"value": state.enemies},
            )
        ],
        state,
    )
    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "cast 'magic missile' Olog"
    assert policy.fastwalk_abort_reason is None


def test_fastwalk_research_walks_from_arena_safety_to_preserve_movement() -> None:
    route = route_named("moria")
    policy = StarterPolicy(_spec(), "swordfish", fastwalk_route=route)
    policy.in_world = True
    policy.prompt_ready = True

    leave_safety = policy.next_decision(
        CharacterState(room_name="Safety", room_vnum="3737", position=7)
    )
    assert leave_safety is not None
    assert leave_safety.command == "enter portal"
    assert policy.fastwalk_recall_started is False
    policy.after_command(leave_safety)
    policy.prompt_ready = True

    leave_school = policy.next_decision(
        CharacterState(
            room_name="The Entrance to the Mud School",
            room_vnum="3725",
            position=7,
        )
    )
    assert leave_school is not None
    assert leave_school.command == "down"
    assert policy.fastwalk_recall_started is False
    policy.after_command(leave_school)
    policy.prompt_ready = True

    first_step = policy.next_decision(
        CharacterState(
            room_name="The Temple Of Midgaard",
            room_vnum="3001",
            position=7,
        )
    )
    assert first_step is not None
    assert first_step.command == route.commands[0]
    assert policy.fastwalk_recall_started is True


def test_fastwalk_research_leaves_arena_for_safety_before_field_hunt() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
    )
    policy.in_world = True
    policy.prompt_ready = True

    decision = policy.next_decision(
        CharacterState(
            room_name="The Mud School Arena",
            room_vnum="3735",
            position=7,
        )
    )

    assert decision is not None
    assert decision.command == "up"
    assert policy.fastwalk_recall_started is False


def test_fastwalk_research_walks_from_mage_lab_to_preserve_movement() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
    )
    policy.in_world = True
    policy.prompt_ready = True

    decision = policy.next_decision(
        CharacterState(
            room_name="Mage's Laboratory",
            room_vnum="3019",
            position=7,
            hp=100,
            max_hp=100,
            mana=200,
            max_mana=200,
            move=200,
            max_move=200,
        )
    )

    assert decision is not None
    assert decision.command == "west"
    assert policy.fastwalk_recall_started is False


def test_movement_waits_for_room_change_instead_of_reusing_an_old_prompt() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.current_room = "3012"
    state = CharacterState(
        room_name="Main Street",
        room_vnum="3012",
        position=7,
        hp=100,
        max_hp=100,
        mana=200,
        max_mana=200,
        move=200,
        max_move=200,
    )

    move = policy.next_decision(state)
    assert move is not None
    assert move.command == "east"
    policy.after_command(move)
    policy.last_command_at = time.monotonic() - 1
    policy.observe_events([GameEvent("prompt_seen", "text", {})], state)

    assert policy.prompt_ready is False

    state.apply(
        GameEvent(
            "room_entered",
            "gmcp",
            {"name": "Main Street", "vnum": "3013"},
        )
    )
    policy.observe_events(
        [
            GameEvent("room_entered", "gmcp", {}),
            GameEvent("prompt_seen", "text", {}),
        ],
        state,
    )
    assert policy.prompt_ready is True
    assert policy.pending_travel_origin is None


def test_fastwalk_recovery_uses_healer_without_polling_heal_menu() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
    )
    policy.in_world = True
    policy.prompt_ready = True
    low_move = CharacterState(
        room_name="The Temple Of Midgaard",
        room_vnum="3001",
        room_flags=["safe"],
        position=7,
        hp=100,
        max_hp=100,
        mana=200,
        max_mana=200,
        move=40,
        max_move=200,
    )

    healer = policy.next_decision(low_move)
    assert healer is not None
    assert healer.command == "north"

    policy.prompt_ready = True
    at_healer = CharacterState(
        room_name="The Healer",
        room_vnum="3054",
        room_flags=["safe"],
        position=7,
        hp=100,
        max_hp=100,
        mana=200,
        max_mana=200,
        move=40,
        max_move=200,
    )
    sleep = policy.next_decision(at_healer)
    assert sleep is not None
    assert sleep.command == "sleep"
    assert sleep.command != "heal"


def test_fastwalk_recovery_casts_invisibility_before_crossing_to_healer() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
        fastwalk_hunt_stops=(FieldHuntStop((), "large hobgoblin"),),
        fastwalk_require_invisibility=True,
    )
    policy.in_world = True
    policy.prompt_ready = True
    home = CharacterState(
        level=9,
        room_name="Mage's Laboratory",
        room_vnum="3019",
        room_flags=["safe"],
        position=7,
        hp=126,
        max_hp=126,
        mana=319,
        max_mana=343,
        move=146,
        max_move=230,
        affects=[[]],
    )

    decision = policy.next_decision(home)

    assert decision is not None
    assert decision.command == "cast invis"
    assert "healer" in decision.reason


def test_recall_accepts_a_prompt_without_a_room_change() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.current_room = "3001"

    policy.after_command(BotDecision("recall", "return safely"))

    assert policy.pending_travel_origin is None
    policy.last_command_at = time.monotonic() - 1
    policy.observe_events(
        [GameEvent("prompt_seen", "text", {})],
        CharacterState(room_vnum="3001"),
    )
    assert policy.prompt_ready is True


def test_level_nine_mage_restock_uses_invisibility_between_city_shops() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_restock=True)
    policy.in_world = True
    policy.prompt_ready = True
    home = CharacterState(
        level=9,
        room_name="Mage's Laboratory",
        room_vnum="3019",
        position=7,
        affects=[[]],
    )

    departure = policy.next_decision(home)

    assert departure is not None
    assert departure.command == "cast invis"

    policy.restock_borrowing = True
    policy.prompt_ready = True
    bank = CharacterState(
        level=9,
        room_name="Dragonhoard Bank",
        room_vnum="3007",
        position=7,
        affects=[[{"name": "invis", "duration": "5"}]],
    )

    visible = policy.next_decision(bank)

    assert visible is not None
    assert visible.command == "vis"

    policy.prompt_ready = True
    policy.restock_borrow_step = 2
    bank_road = CharacterState(
        level=9,
        room_name="East Temple Road",
        room_vnum="3006",
        position=7,
        affects=[[]],
    )

    protected_return = policy.next_decision(bank_road)

    assert protected_return is not None
    assert protected_return.command == "cast invis"


def test_critical_fastwalk_recovery_reaches_healer_north_of_recall() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
    )
    policy.in_world = True
    policy.prompt_ready = True
    critical = CharacterState(
        room_name="The Temple Of Midgaard",
        room_vnum="3001",
        room_flags=["safe"],
        position=7,
        hp=7,
        max_hp=115,
        mana=262,
        max_mana=316,
        move=44,
        max_move=220,
    )

    healer = policy.next_decision(critical)

    assert healer is not None
    assert healer.command == "north"
    assert "critical" in healer.reason


def test_blind_field_character_flees_before_recalling_to_healer() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
    )
    policy.in_world = True
    policy.title_configured = True
    policy.prompt_ready = True
    policy.combat_active = True
    blinded = CharacterState(
        area="Dwarven Day Care",
        room_name="Nap Time",
        room_vnum="6602",
        position=8,
        in_combat=True,
        affects=[[{"name": "blindness", "duration": "4"}]],
    )

    flee = policy.next_decision(blinded)

    assert flee is not None
    assert flee.command == "flee"
    assert "blindness" in flee.reason

    policy.after_command(flee)
    policy.prompt_ready = True
    assert policy.next_decision(blinded) is None

    policy.combat_active = False
    policy.flee_pending = False
    policy.prompt_ready = True
    blinded.in_combat = False
    recall = policy.next_decision(blinded)

    assert recall is not None
    assert recall.command == "recall"
    assert "blindness" in recall.reason


def test_blind_character_waits_at_healer_until_affect_is_cured() -> None:
    policy = StarterPolicy(_spec(), "swordfish", return_home=True)
    policy.in_world = True
    policy.title_configured = True
    policy.prompt_ready = True
    healer = CharacterState(
        area="Midgaard",
        room_name="By the Temple Altar",
        room_vnum="3054",
        room_flags=["safe", "healing"],
        hp=126,
        max_hp=126,
        mana=343,
        max_mana=343,
        move=230,
        max_move=230,
        position=7,
        affects=[[{"name": "blindness", "duration": "4"}]],
    )

    sleep = policy.next_decision(healer)

    assert sleep is not None
    assert sleep.command == "sleep"
    assert "cure blindness" in sleep.reason
    assert policy._recovery_ready_for_objective(healer) is False

    policy.after_command(sleep)
    policy.prompt_ready = True
    healer.position = 4
    healer.affects = [[]]
    stand = policy.next_decision(healer)

    assert stand is not None
    assert stand.command == "stand"
    assert policy.blindness_recovery_active is False


def test_fastwalk_completion_does_not_take_a_token_nap_in_mage_lab() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(FieldHuntStop((), "war dog"),),
    )
    policy.fastwalk_returning = True
    home = CharacterState(
        hp=115,
        max_hp=115,
        mana=316,
        max_mana=316,
        move=196,
        max_move=220,
        room_name="Mage's Laboratory",
        room_vnum="3019",
        room_flags=["safe"],
    )

    assert policy._recovery_decision(home) is None


def test_fastwalk_return_does_not_reverse_to_healer_after_recovery() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(FieldHuntStop((), "war dog"),),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_returning = True
    market = CharacterState(
        hp=126,
        max_hp=126,
        mana=343,
        max_mana=343,
        move=204,
        max_move=230,
        room_name="Market Square",
        room_vnum="3014",
        room_flags=["safe"],
        position=7,
    )

    decision = policy.next_decision(market)

    assert decision is not None
    assert decision.command == "north"
    assert decision.reason == "finish the fastwalk at the Midgaard healer"


def test_fastwalk_completion_saves_and_quits_at_midgaard_healer() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(FieldHuntStop((), "war dog"),),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_returning = True
    healer = CharacterState(
        area="Midgaard",
        room_name="By the Temple Altar",
        room_vnum="3054",
        room_flags=["safe", "healing"],
        hp=126,
        max_hp=126,
        mana=145,
        max_mana=145,
        move=210,
        max_move=210,
        position=7,
    )

    save = policy.next_decision(healer)
    assert save is not None
    assert save.command == "save"
    policy.after_command(save)
    policy.prompt_ready = True

    quit_decision = policy.next_decision(healer)
    assert quit_decision is not None
    assert quit_decision.command == "quit"


def test_fastwalk_outbound_does_not_reverse_after_reserves_are_approved() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(FieldHuntStop((), "war dog"),),
    )
    ready = CharacterState(
        hp=126,
        max_hp=126,
        mana=343,
        max_mana=343,
        move=217,
        max_move=230,
        room_name="Mage's Laboratory",
        room_vnum="3019",
        room_flags=["safe"],
        position=7,
    )

    assert policy._recovery_decision(ready) is None
    assert policy.fastwalk_recovery_ready is True

    market = CharacterState(
        hp=126,
        max_hp=126,
        mana=343,
        max_mana=343,
        move=204,
        max_move=230,
        room_name="Market Square",
        room_vnum="3014",
        room_flags=["safe"],
        position=7,
    )

    assert policy._recovery_decision(market) is None


def test_fastwalk_low_reserves_route_from_mage_lab_to_temple_healer() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(FieldHuntStop((), "war dog"),),
    )
    home = CharacterState(
        hp=115,
        max_hp=115,
        mana=316,
        max_mana=316,
        move=100,
        max_move=220,
        room_name="Mage's Laboratory",
        room_vnum="3019",
        room_flags=["safe"],
    )

    decision = policy._recovery_decision(home)

    assert decision is not None
    assert decision.command == "west"
    assert "temple healer" in decision.reason


def test_fastwalk_low_reserves_leave_general_supplies_for_temple_healer() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(FieldHuntStop((), "war dog"),),
    )
    supplies = CharacterState(
        hp=87,
        max_hp=115,
        mana=251,
        max_mana=316,
        move=46,
        max_move=220,
        room_name="General Supplies",
        room_vnum="3724",
        room_flags=["safe"],
        position=7,
    )

    decision = policy._recovery_decision(supplies)

    assert decision is not None
    assert decision.command == "down"
    assert "temple healer" in decision.reason


def test_field_hunt_does_not_recover_again_after_outbound_departure() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(FieldHuntStop((), "war dog"),),
    )
    policy.fastwalk_outbound_index = 3
    dump = CharacterState(
        hp=115,
        max_hp=115,
        mana=303,
        max_mana=316,
        move=194,
        max_move=220,
        room_name="The Dump",
        room_vnum="3030",
        room_flags=["safe"],
        position=7,
    )

    assert policy._recovery_decision(dump) is None
    assert policy._desired_gear_stance(dump) == STANCE_COMBAT


def test_short_fastwalk_continues_from_safe_city_room_at_forty_percent_move() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
    )
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        room_name="Main Street",
        room_vnum="3013",
        room_flags=["safe"],
        position=7,
        hp=100,
        max_hp=100,
        mana=200,
        max_mana=200,
        move=90,
        max_move=200,
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "east"


def test_deep_field_circuit_routes_to_healer_for_ninety_percent_reserve() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(FieldHuntStop(("west",), "goblin"),),
    )
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        room_name="Main Street",
        room_vnum="3013",
        room_flags=["safe"],
        position=7,
        hp=100,
        max_hp=100,
        mana=200,
        max_mana=200,
        move=100,
        max_move=200,
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "east"
    assert "temple healer" in decision.reason


def test_return_home_recalls_then_follows_verified_mage_guild_route() -> None:
    policy = StarterPolicy(_spec(), "swordfish", return_home=True)
    policy.in_world = True
    policy.prompt_ready = True

    recall = policy.next_decision(
        CharacterState(room_name="The Lane", room_vnum="3501", position=7)
    )
    assert recall is not None
    assert recall.command == "recall"
    policy.after_command(recall)
    policy.prompt_ready = True

    north = policy.next_decision(
        CharacterState(
            room_name="The Temple Of Midgaard",
            room_vnum="3001",
            position=7,
            room_flags=["safe"],
            move=120,
            max_move=200,
            mana=200,
            max_mana=200,
            hp=100,
            max_hp=100,
        )
    )
    assert north is not None
    assert north.command == "north"


def test_return_home_continues_from_common_square_without_another_recall() -> None:
    policy = StarterPolicy(_spec(), "swordfish", return_home=True)
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        room_name="The Common Square",
        room_vnum="3025",
        position=7,
        room_flags=["safe"],
        move=118,
        max_move=200,
        mana=268,
        max_mana=268,
        hp=96,
        max_hp=96,
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "north"


def test_return_home_routes_low_health_mage_to_healer_before_saving() -> None:
    policy = StarterPolicy(_spec(), "swordfish", return_home=True)
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        room_name="Mage's Laboratory",
        room_vnum="3019",
        position=7,
        move=180,
        max_move=200,
        mana=260,
        max_mana=268,
        hp=51,
        max_hp=96,
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "west"


def test_return_home_routes_low_movement_from_recall_to_healer() -> None:
    policy = StarterPolicy(_spec(), "swordfish", return_home=True)
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        room_name="The Temple Of Midgaard",
        room_vnum="3001",
        position=7,
        room_flags=["safe"],
        move=69,
        max_move=230,
        mana=343,
        max_mana=343,
        hp=126,
        max_hp=126,
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "north"
    assert "healer" in decision.reason


def test_return_home_leaves_mud_school_entrance_after_recall() -> None:
    policy = StarterPolicy(_spec(), "swordfish", return_home=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.return_home_recall_started = True
    state = CharacterState(
        room_name="The Entrance to the Mud School",
        room_vnum="3725",
        position=7,
        room_flags=["safe"],
        move=150,
        max_move=200,
        mana=200,
        max_mana=200,
        hp=96,
        max_hp=96,
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "down"


def test_return_home_leaves_general_supplies_after_recall() -> None:
    policy = StarterPolicy(_spec(), "swordfish", return_home=True)
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        room_name="General Supplies",
        room_vnum="3724",
        position=7,
        room_flags=["safe"],
        move=150,
        max_move=200,
        mana=200,
        max_mana=200,
        hp=96,
        max_hp=96,
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "down"


def test_return_home_low_health_leaves_general_supplies_for_healer() -> None:
    policy = StarterPolicy(_spec(), "swordfish", return_home=True)
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        room_name="General Supplies",
        room_vnum="3724",
        position=7,
        room_flags=["safe"],
        hp=12,
        max_hp=96,
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "down"


def test_return_home_low_health_leaves_rooms_above_the_altar_for_healer() -> None:
    policy = StarterPolicy(_spec(), "swordfish", return_home=True)
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        room_name="Rooms Above the Altar",
        room_vnum="3060",
        position=7,
        room_flags=["safe"],
        hp=58,
        max_hp=96,
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "down"


def test_return_home_low_health_leaves_implementors_room_for_healer() -> None:
    policy = StarterPolicy(_spec(), "swordfish", return_home=True)
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        room_name="Implementors' Room",
        room_vnum="3063",
        position=7,
        room_flags=["safe"],
        hp=10,
        max_hp=96,
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "north"


def test_return_home_saves_without_blindly_replacing_scored_equipment() -> None:
    policy = StarterPolicy(_spec(), "swordfish", return_home=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.return_home_recall_started = True
    home = CharacterState(
        room_name="Mage's Laboratory",
        room_vnum="3019",
        position=7,
        hp=100,
        max_hp=100,
        mana=100,
        max_mana=100,
        move=100,
        max_move=100,
        room_flags=["safe"],
    )

    healer_route = policy.next_decision(home)
    assert healer_route is not None
    assert healer_route.command == "west"


def test_return_home_does_not_cycle_stacked_carried_equipment() -> None:
    policy = StarterPolicy(_spec(), "swordfish", return_home=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.return_home_recall_started = True
    home = CharacterState(
        room_name="Mage's Laboratory",
        room_vnum="3019",
        position=7,
        hp=100,
        max_hp=100,
        mana=100,
        max_mana=100,
        move=100,
        max_move=100,
        room_flags=["safe"],
        inventory=[
            [
                {"short_desc": "a steel barrel-helm", "quan": "1"},
                {"short_desc": "a big pot pie", "quan": "2"},
            ]
        ],
    )

    healer_route = policy.next_decision(home)

    assert healer_route is not None
    assert healer_route.command == "west"


def test_return_home_uses_recall_for_trapped_emergency_combat() -> None:
    policy = StarterPolicy(_spec(), "swordfish", return_home=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    trapped = CharacterState(
        area="The Foundry",
        room_name="Ushog's Quarters",
        room_vnum="112",
        position=7,
        hp=10,
        max_hp=100,
    )

    decision = policy.next_decision(trapped)

    assert decision is not None
    assert decision.command == "recall"


def test_return_home_follows_randomized_purgatory_exit_by_destination() -> None:
    policy = StarterPolicy(_spec(), "swordfish", return_home=True)
    policy.in_world = True
    policy.prompt_ready = True
    purgatory = CharacterState(
        area="Purgatory",
        room_name="The Purgatory",
        room_vnum="401",
        dead=True,
        position=7,
        exits={"north": "410", "down": "410"},
    )

    decision = policy.next_decision(purgatory)

    assert decision is not None
    assert decision.command in {"north", "down"}
    assert decision.command != "recall"


def test_reconnect_in_purgatory_recovers_even_without_transient_dead_flag() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.prompt_ready = True
    purgatory = CharacterState(
        area="Purgatory",
        room_name="The Purgatory",
        room_vnum="401",
        dead=False,
        position=7,
        exits={"west": "410", "down": "410"},
    )

    decision = policy.next_decision(purgatory)

    assert decision is not None
    assert decision.command in {"west", "down"}
    assert policy.return_home is True
    assert policy.purgatory_recovery_active is True


def test_death_event_enters_recovery_instead_of_blocking_decisions() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.prompt_ready = True
    purgatory = CharacterState(
        area="Purgatory",
        room_name="The Purgatory",
        room_vnum="401",
        dead=True,
        position=7,
        exits={"north": "410"},
    )

    policy.observe_events(
        [GameEvent("character_died", "text", {})],
        purgatory,
    )
    decision = policy.next_decision(purgatory)

    assert policy.failure is None
    assert decision is not None
    assert decision.command == "north"
    assert policy.combat_active is False
    assert policy.active_target is None
    assert policy.flee_pending is False


def test_noncombat_utility_flees_then_recalls_after_unexpected_combat() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.active_target_level = 4

    flee = policy.next_decision(
        CharacterState(
            level=6,
            hp=111,
            max_hp=111,
            room_name="Main Street",
            room_vnum="3012",
            room_flags=["safe"],
            position=7,
            enemies=[[{"name": "the vagabond", "level": "4"}]],
        )
    )

    assert flee is not None
    assert flee.command == "flee"
    assert policy.return_home is True
    assert policy.utility_abort_reason is not None
    policy.after_command(flee)
    policy.observe_text("You flee from combat!\n")
    stale_enemies = [[{"name": "the drunk", "level": "2"}]]
    policy.observe_events(
        [
            GameEvent(
                "enemies_changed",
                "gmcp",
                {"value": stale_enemies},
            )
        ],
        CharacterState(enemies=stale_enemies, position=6),
    )
    policy.prompt_ready = True

    recall = policy.next_decision(
        CharacterState(
            enemies=stale_enemies,
            room_name="Market Square",
            room_vnum="3014",
            position=6,
        )
    )

    assert recall is not None
    assert recall.command == "recall"


def test_noncombat_utility_waits_for_enemy_assessment_before_fleeing() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True

    decision = policy.next_decision(
        CharacterState(room_name="Main Street", room_vnum="3012", position=6)
    )

    assert decision is None
    assert policy.awaiting_enemy_assessment is True
    assert policy.return_home is False


def test_noncombat_utility_attacks_trivial_safe_room_attacker() -> None:
    policy = StarterPolicy(_spec(race="drow"), "swordfish", liquidate_loot=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.active_target = "the drunk"
    policy.active_target_level = 2
    state = CharacterState(
        level=6,
        hp=111,
        max_hp=111,
        room_name="Main Street",
        room_vnum="3012",
        room_flags=["safe"],
        position=6,
        enemies=[[{"name": "the drunk", "level": "2"}]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "cast 'magic missile' drunk"
    assert policy.return_home is False
    assert policy.utility_abort_reason is None


def test_noncombat_mage_uses_known_spell_on_trivial_safe_room_attacker() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.active_target = "the drunk"
    policy.active_target_level = 2
    policy.known_skills.add("chill touch")
    state = CharacterState(
        level=7,
        hp=108,
        max_hp=110,
        mana=234,
        max_mana=293,
        room_name="The Main Street",
        room_vnum="3015",
        room_flags=["safe"],
        position=6,
        enemies=[[{"name": "the drunk", "level": "2"}]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "cast 'chill touch' drunk"
    assert policy.return_home is False
    assert policy.utility_abort_reason is None


@pytest.mark.parametrize(
    "state",
    [
        CharacterState(
            level=6,
            hp=111,
            max_hp=111,
            room_vnum="3012",
            room_flags=["safe"],
            enemies=[[{"name": "the vagabond", "level": "4"}]],
        ),
        CharacterState(
            level=6,
            hp=80,
            max_hp=111,
            room_vnum="3012",
            room_flags=["safe"],
            enemies=[[{"name": "the drunk", "level": "2"}]],
        ),
        CharacterState(
            level=6,
            hp=111,
            max_hp=111,
            room_vnum="3012",
            room_flags=["safe"],
            enemies=[
                [
                    {"name": "the drunk", "level": "2"},
                    {"name": "the vagabond", "level": "2"},
                ]
            ],
        ),
    ],
)
def test_noncombat_utility_withdraws_from_nontrivial_attackers(
    state: CharacterState,
) -> None:
    policy = StarterPolicy(_spec(race="drow"), "swordfish", liquidate_loot=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.active_target_level = 2

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "flee"
    assert policy.return_home is True
    assert policy.utility_abort_reason is not None


def test_progress_watchdog_recalls_a_stalled_noncombat_run() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(room_name="Main Street", room_vnum="3012", position=7)

    decision = policy.recover_from_stall(state, "west")

    assert decision is not None
    assert decision.command == "recall"
    assert policy.return_home is True
    assert policy.utility_abort_reason == (
        "progress watchdog stopped after repeating 'west' without state progress"
    )


def test_progress_watchdog_does_not_recall_for_safe_equipment_stall() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        room_name="General Supplies",
        room_vnum="3724",
        room_flags=["indoors", "safe"],
        position=7,
    )

    decision = policy.recover_from_stall(state, "remove guards")

    assert decision is None
    assert policy.failure == (
        "progress watchdog stopped after repeating 'remove guards' "
        "without state progress"
    )


def test_progress_watchdog_flees_before_recalling_from_combat() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    state = CharacterState(room_name="Main Street", room_vnum="3012", position=7)

    decision = policy.recover_from_stall(state, "west")

    assert decision is not None
    assert decision.command == "flee"
    assert policy.utility_emergency_recall_pending is True


def test_progress_watchdog_preserves_purgatory_recovery() -> None:
    policy = StarterPolicy(_spec(), "swordfish", return_home=True)
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        area="Purgatory",
        dead=True,
        room_name="Judgement Hall",
        room_vnum="427",
        position=7,
    )

    decision = policy.recover_from_stall(state, "look")

    assert decision is None
    assert policy.purgatory_recovery_active is True


def test_progress_watchdog_marker_tracks_combat_resource_changes() -> None:
    before = CharacterState(
        room_vnum="4015",
        hp=105,
        mana=289,
        move=50,
        xp=21578,
        level=7,
        in_combat=True,
        position=6,
    )
    after_cast = CharacterState(
        room_vnum="4015",
        hp=100,
        mana=275,
        move=50,
        xp=21578,
        level=7,
        in_combat=True,
        position=6,
    )

    assert _watchdog_progress_marker(before) != _watchdog_progress_marker(after_cast)


def test_empty_gmcp_enemy_list_releases_combat_policy() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.combat_active = True
    policy.active_target = "Olog"
    policy.active_target_level = 1
    policy.between_round_action_issued = True
    policy.awaiting_enemy_assessment = True
    policy.prompt_ready = False
    state = CharacterState(room_vnum="108", position=7)

    policy.observe_events(
        [GameEvent("enemies_changed", "gmcp", {"value": []})],
        state,
    )

    assert policy.combat_active is False
    assert policy.active_target is None
    assert policy.active_target_level is None
    assert policy.between_round_action_issued is False
    assert policy.awaiting_enemy_assessment is False
    assert policy.prompt_ready is True


def test_policy_inactivity_watchdog_respects_deliberate_waits() -> None:
    policy = StarterPolicy(_spec(), "swordfish")

    assert _policy_inactivity_due(
        policy,
        now=60.0,
        last_progress=0.0,
        timeout=45.0,
    )

    policy.health_check_due = 90.0
    assert not _policy_inactivity_due(
        policy,
        now=60.0,
        last_progress=0.0,
        timeout=45.0,
    )
    assert _policy_inactivity_due(
        policy,
        now=90.0,
        last_progress=0.0,
        timeout=45.0,
    )


def test_return_home_loots_corpse_enters_portal_and_sleeps() -> None:
    policy = StarterPolicy(_spec(), "swordfish", return_home=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.utility_abort_reason = (
        "character died; completed Purgatory recovery is required"
    )
    judgement = CharacterState(
        area="Purgatory",
        room_name="The Judgement Room",
        room_vnum="427",
        position=7,
    )

    loot = policy.next_decision(judgement)
    assert loot is not None
    assert loot.command == "get all corpse"
    policy.after_command(loot)
    policy.prompt_ready = True

    inventory = policy.next_decision(judgement)
    assert inventory is not None
    assert inventory.command == "inventory"
    policy.after_command(inventory)
    policy.prompt_ready = True

    portal = policy.next_decision(judgement)
    assert portal is not None
    assert portal.command == "enter portal"
    policy.after_command(portal)
    policy.prompt_ready = True

    healer = CharacterState(
        area="Midgaard",
        room_name="By the Temple Altar",
        room_vnum="3054",
        position=7,
        hp=100,
        max_hp=100,
        mana=90,
        max_mana=100,
        move=90,
        max_move=100,
        room_flags=["safe"],
    )
    sleep = policy.next_decision(healer)
    assert sleep is not None
    assert sleep.command == "sleep"
    policy.after_command(sleep)
    policy.prompt_ready = True

    healer.position = 4
    stand = policy.next_decision(healer)
    assert stand is not None
    assert stand.command == "stand"
    policy.after_command(stand)
    policy.prompt_ready = True

    healer.position = 7
    save = policy.next_decision(healer)
    assert save is not None
    assert save.command == "save"
    assert policy.utility_abort_reason is None


def test_prompt_arriving_immediately_after_command_is_ignored_as_stale() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.after_command(BotDecision("south", "test command"))
    state = CharacterState()
    prompt = GameEvent("prompt_seen", "text", {})

    policy.observe_events([prompt], state)

    assert policy.prompt_ready is False
    policy.last_command_at = time.monotonic() - 1
    policy.observe_events([prompt], state)
    assert policy.prompt_ready is True


def test_fastwalk_hunt_circuit_skips_an_absent_stop_and_continues() -> None:
    route = route_named("moria")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(
            FieldHuntStop(("north", "north"), "garter snake"),
            FieldHuntStop(("south",), "large orc"),
        ),
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    state = CharacterState(
        hp=105,
        max_hp=105,
        mana=289,
        max_mana=289,
        move=100,
        max_move=210,
        position=7,
        room_name="The tunnel",
        room_vnum="4014",
        inventory=[[{"quan": "1", "short_desc": "a big pot pie"}]],
    )

    policy.prompt_ready = True
    first = policy.next_decision(state)
    assert first is not None
    assert first.command == "north"
    policy.after_command(first)

    policy.prompt_ready = True
    second = policy.next_decision(state)
    assert second is not None
    assert second.command == "north"
    policy.after_command(second)

    state.room_vnum = "4025"
    state.room_name = "The cave"
    policy.prompt_ready = True
    inspect = policy.next_decision(state)
    assert inspect is not None
    assert inspect.command == "look"
    policy.after_command(inspect)

    policy.prompt_ready = True
    absent = policy.next_decision(state)
    assert absent is not None
    assert absent.command == "look"
    policy.after_command(absent)

    policy.prompt_ready = True
    continue_route = policy.next_decision(state)
    assert continue_route is not None
    assert continue_route.command == "south"


def test_fastwalk_field_stop_performs_actions_then_recalls() -> None:
    route = route_named("ambush")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(
            FieldHuntStop((), actions=("get sack", "inventory")),
        ),
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    state = CharacterState(
        hp=105,
        max_hp=105,
        mana=289,
        max_mana=289,
        move=210,
        max_move=210,
        position=7,
        room_name="On a small trail",
        room_vnum="4518",
    )

    commands = []
    for _ in range(5):
        policy.prompt_ready = True
        decision = policy.next_decision(state)
        assert decision is not None
        commands.append(decision.command)
        policy.after_command(decision)

    assert commands == ["look", "get sack", "inventory", "look", "recall"]


def test_fastwalk_field_stop_with_missing_required_item_recalls_and_aborts() -> None:
    route = route_named("ambush")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(
            FieldHuntStop(
                (),
                actions=("get sack", "inventory"),
                required_items=("large sack",),
            ),
        ),
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_looked = True
    policy.fastwalk_hunt_action_index = 2
    policy.prompt_ready = True
    state = CharacterState(
        hp=105,
        max_hp=105,
        mana=289,
        max_mana=289,
        move=210,
        max_move=210,
        position=7,
        room_name="On a small trail",
        room_vnum="4518",
        inventory=[{"short_desc": "a buffalo water skin", "quan": "1"}],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "recall"
    assert policy.fastwalk_returning is True
    assert policy.fastwalk_abort_reason == (
        "field expedition did not acquire required item(s): large sack"
    )


def test_fastwalk_field_stop_accepts_required_inventory_item() -> None:
    route = route_named("ambush")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(
            FieldHuntStop((), required_items=("large sack",)),
        ),
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_looked = True
    policy.prompt_ready = True
    state = CharacterState(
        hp=105,
        max_hp=105,
        mana=289,
        max_mana=289,
        move=210,
        max_move=210,
        position=7,
        room_name="On a small trail",
        room_vnum="4518",
        inventory=[{"short_desc": "a large sack", "quan": "1"}],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "look"
    assert policy.fastwalk_abort_reason is None


def test_fastwalk_origin_actions_run_before_route_commands() -> None:
    route = route_named("ambush")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_origin_actions=("drop all.piping", "drop cap"),
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    state = CharacterState(
        hp=105,
        max_hp=105,
        mana=289,
        max_mana=289,
        move=210,
        max_move=210,
        position=7,
        room_name="The Temple Of Midgaard",
        room_vnum="3001",
    )

    commands = []
    for _ in range(3):
        policy.prompt_ready = True
        decision = policy.next_decision(state)
        assert decision is not None
        commands.append(decision.command)
        policy.after_command(decision)

    assert commands == ["drop all.piping", "drop cap", "south"]


def test_combat_fastwalk_enables_autoloot_before_origin_actions() -> None:
    route = route_named("ambush")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_attack_target="war dog",
        fastwalk_origin_actions=("drop cap",),
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    state = CharacterState(
        room_name="The Temple Of Midgaard",
        room_vnum="3001",
        position=7,
    )

    policy.prompt_ready = True
    configure = policy.next_decision(state)
    assert configure is not None
    assert configure.command == "config +autoloot"
    policy.after_command(configure)

    policy.prompt_ready = True
    prepare = policy.next_decision(state)

    assert prepare is not None
    assert prepare.command == "drop cap"


def test_fastwalk_origin_does_not_waste_food_or_water_without_need() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    state = CharacterState(
        hp=105,
        max_hp=105,
        mana=289,
        max_mana=289,
        move=210,
        max_move=210,
        position=7,
        room_name="The Temple Of Midgaard",
        room_vnum="3001",
        inventory=[[
            {"short_desc": "a big pot pie", "quan": "1"},
            {"short_desc": "a buffalo water skin", "quan": "1"},
        ]],
    )

    commands = []
    for _ in range(2):
        policy.prompt_ready = True
        decision = policy.next_decision(state)
        assert decision is not None
        commands.append(decision.command)
        policy.after_command(decision)

    assert commands == ["get all.pie", "south"]


def test_fastwalk_origin_consumes_food_and_water_after_live_warnings() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.needs_food = True
    policy.needs_drink = True
    state = CharacterState(
        hp=105,
        max_hp=105,
        mana=289,
        max_mana=289,
        move=210,
        max_move=210,
        position=7,
        room_name="The Temple Of Midgaard",
        room_vnum="3001",
        inventory=[[
            {"short_desc": "a big pot pie", "quan": "1"},
            {"short_desc": "a buffalo water skin", "quan": "1"},
        ]],
    )

    commands = []
    for _ in range(4):
        policy.prompt_ready = True
        decision = policy.next_decision(state)
        assert decision is not None
        commands.append(decision.command)
        policy.after_command(decision)

    assert commands == ["eat pie", "drink skin", "get all.pie", "south"]


def test_vault_preflight_stows_gear_and_verifies_free_weight() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        vault_stow_items=("vest", "cape"),
        vault_required_free_weight=60,
    )
    policy.in_world = True
    state = CharacterState(
        level=8,
        hp=110,
        max_hp=110,
        mana=310,
        max_mana=310,
        move=220,
        max_move=220,
        room_name="Dragonhoard Bank, Midgaard Branch",
        room_vnum="3007",
        stats={"carry_wt": 70, "maxcarry_wt": 140},
    )

    commands = []
    for _ in range(5):
        policy.prompt_ready = True
        decision = policy.next_decision(state)
        assert decision is not None
        commands.append(decision.command)
        policy.after_command(decision)

    assert commands == [
        "remove vest",
        "lodge vest",
        "remove cape",
        "lodge cape",
        "score",
    ]

    policy.prompt_ready = True
    return_to_recall = policy.next_decision(state)

    assert return_to_recall is not None
    assert return_to_recall.command == "west"
    assert policy.failure is None


def test_vault_preflight_can_lodge_capacity_gear_and_reclaim_armour() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        vault_stow_items=("sack",),
        vault_claim_items=("vest", "cape"),
        vault_required_free_weight=30,
    )
    policy.in_world = True
    state = CharacterState(
        level=8,
        hp=110,
        max_hp=110,
        mana=310,
        max_mana=310,
        move=220,
        max_move=220,
        room_name="Dragonhoard Bank, Midgaard Branch",
        room_vnum="3007",
        stats={"carry_wt": 95, "maxcarry_wt": 140},
    )

    commands = []
    for _ in range(6):
        policy.prompt_ready = True
        decision = policy.next_decision(state)
        assert decision is not None
        commands.append(decision.command)
        policy.after_command(decision)

    assert commands == [
        "remove sack",
        "lodge sack",
        "claim vest",
        "claim cape",
        "score",
        "west",
    ]
    assert policy.failure is None


def test_level_eight_midennir_casts_and_verifies_invisibility() -> None:
    route = route_named("ambush")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_require_invisibility=True,
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.prompt_ready = True
    state = CharacterState(
        level=8,
        hp=110,
        max_hp=110,
        mana=310,
        max_mana=310,
        move=220,
        max_move=220,
        room_name="The Temple of Midgaard",
        room_vnum="3001",
    )

    cast = policy.next_decision(state)
    assert cast is not None
    assert cast.command == "cast invis"
    policy.after_command(cast)

    state.affects = [[{"name": "invis", "duration": "8"}]]
    policy.prompt_ready = True
    move = policy.next_decision(state)

    assert move is not None
    assert move.command == "south"
    assert policy.fastwalk_invisibility_attempts == 0


def test_level_seven_midennir_does_not_require_unavailable_invisibility() -> None:
    route = route_named("ambush")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_require_invisibility=True,
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.prompt_ready = True
    state = CharacterState(
        level=7,
        hp=105,
        max_hp=105,
        mana=289,
        max_mana=289,
        move=210,
        max_move=210,
        room_name="The Temple of Midgaard",
        room_vnum="3001",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "south"


def test_level_eight_fastwalk_detours_to_loremaster_with_new_practices() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_train_before_departure=True,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.observe_text(
        "Physical pracs: 1.  Intellectual pracs: 3.\n"
    )
    state = CharacterState(
        level=8,
        practice=1,
        hp=110,
        max_hp=110,
        mana=310,
        max_mana=310,
        move=220,
        max_move=220,
        room_name="Mage's Laboratory",
        room_vnum="3019",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "west"
    assert "Loremaster" in decision.reason


def test_level_seven_warrior_fastwalk_trains_unspent_combat_practice() -> None:
    policy = StarterPolicy(
        _spec(
            name="Dorrik",
            race="dwarf",
            gender="neuter",
            **{"class": "warrior", "subclass": "knight"},
        ),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_train_before_departure=True,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.observe_text("Physical pracs: 1.  Intellectual pracs: 0.\n")
    state = CharacterState(
        level=7,
        practice=1,
        hp=157,
        max_hp=157,
        mana=133,
        max_mana=133,
        move=210,
        max_move=210,
        room_name="The Temple Of Midgaard",
        room_vnum="3001",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "up"
    assert "Loremaster" in decision.reason


def test_fastwalk_skips_practice_type_already_spent_at_current_level() -> None:
    policy = StarterPolicy(
        _spec(
            name="Kestrel",
            race="drow",
            gender="male",
            **{"class": "thief", "subclass": "ninja"},
        ),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_train_before_departure=True,
        practice_types_spent=frozenset({"physical", "intellectual"}),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.observe_text("Physical pracs: 2.  Intellectual pracs: 1.\n")
    state = CharacterState(
        level=7,
        practice=1,
        hp=123,
        max_hp=123,
        mana=145,
        max_mana=145,
        move=210,
        max_move=210,
        room_name="The Temple Of Midgaard",
        room_vnum="3001",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "south"


def test_fastwalk_audits_unknown_practice_balance_before_departure() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_train_before_departure=True,
    )
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        level=8,
        practice=1,
        hp=110,
        max_hp=110,
        mana=310,
        max_mana=310,
        move=220,
        max_move=220,
        room_name="The Temple Of Midgaard",
        room_vnum="3001",
    )

    audit = policy.next_decision(state)

    assert audit is not None
    assert audit.command == "score"
    assert "practices" in audit.reason


def test_fastwalk_retries_score_after_interleaved_healer_output() -> None:
    policy = StarterPolicy(
        _spec(
            name="Kestrel",
            race="drow",
            gender="male",
            **{"class": "thief", "subclass": "ninja"},
        ),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_train_before_departure=True,
    )
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        level=7,
        hp=123,
        max_hp=123,
        mana=145,
        max_mana=145,
        move=210,
        max_move=210,
        room_name="By the Temple Altar",
        room_vnum="3054",
    )

    first = policy.next_decision(state)
    assert first is not None
    assert first.command == "score"
    policy.after_command(first)
    policy.observe_text("The Healer utters the word 'Sifircas'.\n")
    policy.prompt_ready = True

    retry = policy.next_decision(state)

    assert retry is not None
    assert retry.command == "score"
    assert "interleaved" in retry.reason
    assert policy.failure is None


def test_fastwalk_fails_after_three_missing_practice_audits() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_train_before_departure=True,
    )
    policy.in_world = True
    state = CharacterState(
        level=7,
        hp=110,
        max_hp=110,
        mana=293,
        max_mana=293,
        move=210,
        max_move=210,
        room_name="By the Temple Altar",
        room_vnum="3054",
    )

    for _ in range(3):
        policy.prompt_ready = True
        decision = policy.next_decision(state)
        assert decision is not None
        assert decision.command == "score"
        policy.after_command(decision)

    policy.prompt_ready = True
    assert policy.next_decision(state) is None
    assert policy.failure == (
        "score did not report the practice balance before field departure"
    )


def test_fastwalk_remembers_practice_balance_during_loremaster_travel() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_train_before_departure=True,
    )
    policy.in_world = True
    policy.prompt_ready = True
    temple = CharacterState(
        level=8,
        practice=1,
        hp=110,
        max_hp=110,
        mana=310,
        max_mana=310,
        move=220,
        max_move=220,
        room_name="The Temple Of Midgaard",
        room_vnum="3001",
    )

    audit = policy.next_decision(temple)
    assert audit is not None
    policy.after_command(audit)
    policy.observe_text("Physical pracs: 1.  Intellectual pracs: 3.\n")
    policy.prompt_ready = True
    up = policy.next_decision(temple)
    assert up is not None
    assert up.command == "up"
    policy.after_command(up)
    policy.observe_text("The Entrance to the Mud School\n")
    policy.prompt_ready = True

    east = policy.next_decision(
        CharacterState(
            level=8,
            practice=1,
            hp=110,
            max_hp=110,
            mana=310,
            max_mana=310,
            move=218,
            max_move=220,
            room_name="The Entrance to the Mud School",
            room_vnum="3725",
        )
    )

    assert east is not None
    assert east.command == "east"
    assert policy.failure is None


def test_fastwalk_skips_loremaster_after_zero_practice_audit() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_train_before_departure=True,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.observe_text("Physical pracs: 1.  Intellectual pracs: 0.\n")
    state = CharacterState(
        level=8,
        practice=1,
        hp=110,
        max_hp=110,
        mana=310,
        max_mana=310,
        move=220,
        max_move=220,
        room_name="The Temple Of Midgaard",
        room_vnum="3001",
    )

    departure = policy.next_decision(state)

    assert departure is not None
    assert departure.command == "south"


def test_practice_balances_use_latest_supported_score_format() -> None:
    text = (
        "You have 1 physical and 3 intellectual practices remaining.\n"
        "Physical pracs: 1.  Intellectual pracs: 0.\n"
    )

    assert _practice_balances(text) == (1, 0)


def test_trained_fastwalk_leaves_mud_school_for_temple_origin() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_train_before_departure=True,
    )
    policy.in_world = True
    policy.practiced = True
    policy.prompt_ready = True
    state = CharacterState(
        level=8,
        practice=1,
        hp=110,
        max_hp=110,
        mana=310,
        max_mana=310,
        move=220,
        max_move=220,
        room_name="Entrance to the Mud School",
        room_vnum="3725",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "down"


def test_fastwalk_training_finishes_after_practice_balance_drops() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_train_before_departure=True,
    )
    policy.in_world = True
    policy.fastwalk_training_started = True
    policy.loremaster_step = 3
    policy.practice_plan = (
        "illusion magiks",
        "invis",
        "invis",
    )
    policy.practice_plan_index = 3
    policy.prompt_ready = True
    state = CharacterState(
        level=8,
        practice=1,
        hp=110,
        max_hp=110,
        mana=310,
        max_mana=310,
        move=220,
        max_move=220,
        room_name="The Loremaster",
        room_vnum="3726",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "west"
    assert policy.practiced is True


def test_midennir_aborts_safely_when_invisibility_is_unknown() -> None:
    route = route_named("ambush")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_require_invisibility=True,
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.prompt_ready = True
    state = CharacterState(
        level=8,
        hp=110,
        max_hp=110,
        mana=310,
        max_mana=310,
        move=220,
        max_move=220,
        room_name="The Temple of Midgaard",
        room_vnum="3001",
    )

    cast = policy.next_decision(state)
    assert cast is not None
    policy.after_command(cast)
    policy.observe_text("You don't know any spells of that name.\n")
    policy.prompt_ready = True
    abort = policy.next_decision(state)

    assert abort is not None
    assert abort.command == "south"
    assert policy.fastwalk_returning is True
    assert policy.fastwalk_abort_reason == (
        "Miden'nir expedition could not establish invisibility at the safe origin"
    )


def test_field_reserve_withdrawal_fails_when_required_item_is_missing() -> None:
    route = route_named("ambush")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(
            FieldHuntStop((), required_items=("large sack",)),
        ),
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.prompt_ready = True
    state = CharacterState(
        hp=77,
        max_hp=105,
        mana=219,
        max_mana=289,
        move=185,
        max_move=210,
        position=7,
        room_name="The Front of the Inn",
        room_vnum="3570",
        inventory=[{"short_desc": "a buffalo water skin", "quan": "1"}],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "recall"
    assert policy.fastwalk_abort_reason == (
        "field expedition withdrew before acquiring required item(s): large sack"
    )


def test_fastwalk_hunt_circuit_recalls_between_fights_on_low_reserves() -> None:
    route = route_named("moria")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(
            FieldHuntStop(("north", "north"), "garter snake"),
            FieldHuntStop(("south",), "large orc"),
        ),
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_stop_killed = True
    policy.prompt_ready = True
    state = CharacterState(
        hp=75,
        max_hp=105,
        mana=200,
        max_mana=289,
        move=100,
        max_move=210,
        position=7,
        room_name="The cave",
        room_vnum="4025",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "recall"


def test_fastwalk_hunt_respects_bounded_field_kill_limit() -> None:
    route = route_named("ambush")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(
            FieldHuntStop((), "war dog"),
            FieldHuntStop(("south",), "goblin"),
        ),
        fastwalk_kill_limit=1,
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    policy.fastwalk_hunt_stop_killed = True
    policy.completed_kills.append({"target": "war dog"})
    policy.prompt_ready = True
    state = CharacterState(
        level=8,
        hp=115,
        max_hp=115,
        mana=300,
        max_mana=316,
        move=200,
        max_move=220,
        position=7,
        room_name="In a forest clearing",
        room_vnum="4505",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "recall"
    assert "bounded 1-kill" in decision.reason
    assert policy.fastwalk_returning is True


def test_optional_second_hunt_requires_its_stop_specific_health_reserve() -> None:
    route = route_named("ambush")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(
            FieldHuntStop((), "war dog"),
            FieldHuntStop(
                ("south", "south"),
                "goblin",
                minimum_health_ratio=0.95,
            ),
        ),
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    policy.fastwalk_hunt_stop_killed = True
    policy.prompt_ready = True
    state = CharacterState(
        hp=104,
        max_hp=115,
        mana=248,
        max_mana=316,
        move=108,
        max_move=220,
        position=7,
        room_name="In a forest clearing",
        room_vnum="4505",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "recall"
    assert policy.fastwalk_returning is True


def test_consider_only_hunt_stop_records_evidence_without_attacking() -> None:
    route = route_named("ambush")
    stop = FieldHuntStop(
        (),
        "fanatical goblin guard",
        consider_only=True,
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(stop,),
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    policy.fastwalk_hunt_looked = True
    policy.current_room = "4521"
    policy.room_targets["4521"] = ["The fanatical goblin guard"]
    policy.consider_target = "fanatical goblin guard"
    policy.consider_viable = True
    policy.prompt_ready = True
    state = CharacterState(
        level=10,
        hp=130,
        max_hp=130,
        mana=350,
        max_mana=350,
        move=120,
        max_move=240,
        position=7,
        room_name="On a small trail",
        room_vnum="4521",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "look"
    assert "without engaging" in decision.reason
    assert policy.fastwalk_hunt_stop_skipped is True
    assert policy.combat_active is False


def test_fastwalk_hunt_circuit_recalls_before_movement_is_exhausted() -> None:
    route = route_named("ambush")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(
            FieldHuntStop(("south",), "goblin"),
        ),
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    policy.prompt_ready = True
    state = CharacterState(
        hp=115,
        max_hp=115,
        mana=316,
        max_mana=316,
        move=50,
        max_move=220,
        position=7,
        room_name="Deep Forest",
        room_vnum="3514",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "recall"
    assert policy.fastwalk_returning is True


def test_fastwalk_hunt_circuit_recovers_to_ninety_percent_movement() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
        fastwalk_hunt_stops=(
            FieldHuntStop(("west",), "hobgoblin"),
        ),
    )
    policy.in_world = True
    policy.waiting_for_heal = True
    policy.prompt_ready = True
    state = CharacterState(
        hp=105,
        max_hp=105,
        mana=289,
        max_mana=289,
        move=150,
        max_move=210,
        position=4,
        room_name="By the Temple Altar",
        room_vnum="3054",
        room_flags=["safe"],
    )

    assert policy.next_decision(state) is None

    state.move = 190
    policy.prompt_ready = True
    stand = policy.next_decision(state)
    assert stand is not None
    assert stand.command == "stand"


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


def test_fastwalk_research_can_inspect_two_rooms_and_backtrack_exactly() -> None:
    route = route_named("moria")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_explore_direction="north",
        fastwalk_explore_depth=2,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True

    endpoint = CharacterState(room_name="The tunnel", room_vnum="4014", position=7)
    first_north = policy.next_decision(endpoint)
    assert first_north is not None
    assert first_north.command == "north"
    policy.after_command(first_north)
    policy.prompt_ready = True

    first_room = CharacterState(room_name="The cave", room_vnum="4018", position=7)
    first_look = policy.next_decision(first_room)
    assert first_look is not None
    assert first_look.command == "look"
    policy.after_command(first_look)
    policy.prompt_ready = True

    second_north = policy.next_decision(first_room)
    assert second_north is not None
    assert second_north.command == "north"
    policy.after_command(second_north)
    policy.prompt_ready = True

    second_room = CharacterState(room_name="The cave", room_vnum="4019", position=7)
    second_look = policy.next_decision(second_room)
    assert second_look is not None
    assert second_look.command == "look"
    policy.after_command(second_look)
    policy.prompt_ready = True

    first_south = policy.next_decision(second_room)
    assert first_south is not None
    assert first_south.command == "south"
    policy.after_command(first_south)
    policy.prompt_ready = True

    second_south = policy.next_decision(first_room)
    assert second_south is not None
    assert second_south.command == "south"


def test_fastwalk_research_stops_at_a_blocked_exploration_exit() -> None:
    route = route_named("moria")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_explore_direction="north",
        fastwalk_explore_depth=3,
        fastwalk_attack_target="wolf",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    endpoint = CharacterState(room_name="The tunnel", room_vnum="4014", position=7)

    blocked_north = policy.next_decision(endpoint)
    assert blocked_north is not None
    assert blocked_north.command == "north"
    policy.after_command(blocked_north)

    policy.observe_text("Alas, you cannot go that way.\n")
    policy.prompt_ready = True
    recall = policy.next_decision(endpoint)

    assert recall is not None
    assert recall.command == "recall"
    assert policy.fastwalk_explore_distance == 0
    assert policy.fastwalk_target_absent is True


def test_fastwalk_research_can_attack_one_explicit_exploration_target() -> None:
    route = route_named("moria")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_explore_direction="north",
        fastwalk_attack_target="ugly kobold",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_explore_step = 2
    policy.fastwalk_explore_distance = 1
    policy.room_targets["4018"] = ["kobold"]

    decision = policy.next_decision(
        CharacterState(room_name="The cave", room_vnum="4018", position=7)
    )

    assert decision is not None
    assert decision.command == "consider kobold"
    policy.after_command(decision)
    policy.observe_text("The perfect match!\n")
    policy.prompt_ready = True

    attack = policy.next_decision(
        CharacterState(room_name="The cave", room_vnum="4018", position=7)
    )

    assert attack is not None
    assert attack.command == "kill kobold"
    assert policy.active_target == "ugly kobold"
    assert policy.combat_active is True


def test_fastwalk_research_attacks_target_at_endpoint_before_exploring() -> None:
    route = route_named("moria")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_explore_direction="north",
        fastwalk_attack_target="kobold",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.room_targets["4014"] = ["ugly kobold"]

    decision = policy.next_decision(
        CharacterState(room_name="The tunnel", room_vnum="4014", position=7)
    )

    assert decision is not None
    assert decision.command == "consider kobold"
    policy.after_command(decision)
    policy.observe_text("The perfect match!\n")
    policy.prompt_ready = True

    attack = policy.next_decision(
        CharacterState(room_name="The tunnel", room_vnum="4014", position=7)
    )

    assert attack is not None
    assert attack.command == "kill kobold"
    assert policy.fastwalk_explore_step == 0
    assert policy.combat_active is True


def test_fastwalk_research_rejects_target_that_is_no_match() -> None:
    route = route_named("moria")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_explore_direction="north",
        fastwalk_attack_target="kobold",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_explore_distance = 1
    policy.current_room = "3506"
    policy.room_targets["4018"] = ["kobold"]
    cave = CharacterState(room_name="The cave", room_vnum="4018", position=7)

    consider = policy.next_decision(cave)
    assert consider is not None
    assert consider.command == "consider kobold"
    policy.after_command(consider)
    policy.observe_text("The kobold is no match for you.\n")
    policy.prompt_ready = True

    withdraw = policy.next_decision(cave)

    assert withdraw is not None
    assert withdraw.command == "recall"
    assert policy.fastwalk_target_absent is True
    assert policy.combat_active is False


def test_fastwalk_research_skips_a_mixed_crowd_before_considering() -> None:
    route = route_named("moria")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_explore_direction="north",
        fastwalk_attack_target="goblin",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_explore_distance = 1
    policy.current_room = "3506"
    state = CharacterState(
        level=8,
        hp=115,
        max_hp=115,
        mana=316,
        max_mana=316,
        room_name="The Miden'nir",
        room_vnum="3506",
        position=7,
    )
    policy.observe_text(
        "A mountain goblin is wandering about, mumbling to himself.\n"
        "A dark horseman is here, mounted on his black steed.\n"
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "recall"
    assert "crowded field room" in decision.reason
    assert policy.room_target_counts["3506"]["mountain goblin"] == 1
    assert policy.room_target_counts["3506"]["dark horseman"] == 1


def test_field_probe_allows_one_source_verified_noncombat_bystander() -> None:
    route = route_named("ambush")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(
            FieldHuntStop(
                (),
                "vile goblin",
                allowed_bystanders=("half clothed human female",),
                consider_only=True,
            ),
        ),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    policy.fastwalk_hunt_looked = True
    policy.current_room = "4519"
    state = CharacterState(
        level=9,
        hp=126,
        max_hp=126,
        mana=343,
        max_mana=343,
        move=150,
        max_move=230,
        room_name="On a small trail",
        room_vnum="4519",
        position=7,
    )
    policy.observe_text(
        "A half clothed human female is here, whimpering.\n"
        "A goblin is here molesting a human female.\n"
    )
    policy.observe_text(
        "A half clothed human female is here, whimpering.\n"
        "A goblin is here molesting a human female.\n"
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "consider goblin"
    assert policy.room_target_counts["4519"] == {
        "half clothed human female": 1,
        "goblin": 1,
    }


def test_consider_only_probe_can_assess_a_target_in_a_crowded_room() -> None:
    route = route_named("moria")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(
            FieldHuntStop((), "large hobgoblin", consider_only=True),
        ),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    policy.fastwalk_hunt_looked = True
    policy.current_room = "4071"
    state = CharacterState(
        level=9,
        hp=126,
        max_hp=126,
        mana=343,
        max_mana=343,
        move=167,
        max_move=230,
        room_name="The large cave",
        room_vnum="4071",
        position=7,
    )
    policy.observe_text(
        "An orc is here, looking for something to eat.\n"
        "A large hobgoblin is here wondering if he should tear you apart.\n"
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "consider hobgoblin"
    assert policy.fastwalk_hunt_stop_skipped is False


def test_exact_field_target_ignores_smaller_same_keyword_mobile() -> None:
    route = route_named("moria")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(
            FieldHuntStop(
                (),
                "large hobgoblin",
                consider_only=True,
                exact_target=True,
            ),
        ),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    policy.fastwalk_hunt_looked = True
    policy.current_room = "4069"
    state = CharacterState(
        level=9,
        hp=126,
        max_hp=126,
        mana=343,
        max_mana=343,
        move=167,
        max_move=230,
        room_name="The tunnel",
        room_vnum="4069",
        position=7,
    )
    policy.observe_text(
        "A veteran warrior is preparing for battle.\n"
        "A small, beat-up hobgoblin is here.\n"
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "look"
    assert policy.consider_target is None


def test_exact_field_probe_rejects_ambiguous_hobgoblin_keyword() -> None:
    route = route_named("moria")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(
            FieldHuntStop(
                (),
                "large hobgoblin",
                consider_only=True,
                exact_target=True,
            ),
        ),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    policy.fastwalk_hunt_looked = True
    policy.current_room = "4071"
    state = CharacterState(
        level=9,
        hp=126,
        max_hp=126,
        mana=343,
        max_mana=343,
        move=167,
        max_move=230,
        room_name="The large cave",
        room_vnum="4071",
        position=7,
    )
    policy.observe_text(
        "A large hobgoblin is here wondering if he should tear you apart.\n"
        "A small hobgoblin is looking for someone to bully.\n"
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "look"
    assert policy.fastwalk_abort_reason is not None


def test_field_circuit_recasts_a_zero_duration_invisibility_affect() -> None:
    route = route_named("moria")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(FieldHuntStop(("west",), "large hobgoblin"),),
        fastwalk_require_invisibility=True,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    state = CharacterState(
        level=9,
        hp=126,
        max_hp=126,
        mana=343,
        max_mana=343,
        move=186,
        max_move=230,
        room_name="The tunnel",
        room_vnum="4064",
        position=7,
        affects=[[{"name": "invis", "duration": "0"}]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "cast invis"
    assert policy.fastwalk_hunt_move_index == 0


def test_field_target_count_excludes_source_identified_ground_objects() -> None:
    collar = ObjectSource(
        4500,
        "war dog collar",
        "a war dog collar",
        9,
        (1, 0, 0, 0),
        30,
        wear_flags=1 | (1 << 4),
        affects=((19, 1),),
    )
    route = route_named("ambush")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(FieldHuntStop((), "war dog"),),
        gear_catalog=GearCatalog({collar.vnum: collar}),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    policy.fastwalk_hunt_looked = True
    policy.current_room = "4505"
    policy.gear_audited = True
    state = CharacterState(
        level=8,
        hp=115,
        max_hp=115,
        mana=316,
        max_mana=316,
        move=200,
        max_move=220,
        room_name="In a forest clearing",
        room_vnum="4505",
        position=7,
    )
    policy.observe_text(
        "A war dog collar is here.\n"
        "A war dog collar is here.\n"
        "A war dog is here, eating carrion.\n"
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "consider dog"
    assert policy.failure is None


def test_planned_fastwalk_combat_flees_as_soon_as_gmcp_reports_two_enemies() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_attack_target="goblin",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.fastwalk_attack_started = True
    state = CharacterState(
        level=8,
        hp=108,
        max_hp=115,
        mana=316,
        max_mana=316,
        position=6,
        room_name="The Miden'nir",
        room_vnum="3506",
        enemies=[
            [
                {"name": "the goblin", "level": "5"},
                {"name": "the goblin", "level": "5"},
            ]
        ],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "flee"
    assert "2 active enemies" in decision.reason
    assert policy.fastwalk_emergency_recall_pending is True


def test_field_sweep_finishes_a_lone_trivial_interceptor_instead_of_fleeing() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_hunt_stops=foundry_level_seven_hunt_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(policy.fastwalk_route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_attack_started = True
    policy.combat_active = True
    policy.active_target = "Olog"
    policy.current_room = "108"
    fighting = CharacterState(
        level=7,
        hp=123,
        max_hp=123,
        mana=145,
        max_mana=145,
        position=6,
        room_name="Muddy Tunnel",
        room_vnum="108",
        enemies=[[{"name": "Olog", "level": "1", "hp": "3", "maxhp": "9"}]],
    )

    decision = policy.next_decision(fighting)

    assert decision is None
    assert policy.combat_active is True
    assert policy.active_target == "Olog"
    assert policy.fastwalk_emergency_recall_pending is False
    assert policy.fastwalk_abort_reason is None


def test_field_circuit_restores_invisibility_after_a_kill_before_moving() -> None:
    route = route_named("ambush")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_require_invisibility=True,
        fastwalk_hunt_stops=(
            FieldHuntStop((), "goblin"),
            FieldHuntStop(("east",), "goblin"),
        ),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    policy.fastwalk_hunt_stop_killed = True
    state = CharacterState(
        level=8,
        hp=115,
        max_hp=115,
        mana=300,
        max_mana=316,
        move=200,
        max_move=220,
        room_name="The Trail to Miden'nir",
        room_vnum="3505",
        position=7,
        affects=[[]],
    )

    cast = policy.next_decision(state)

    assert cast is not None
    assert cast.command == "cast invis"
    assert "next circuit stop" in cast.reason
    policy.after_command(cast)
    state.affects = [[{"name": "invis", "duration": "10"}]]
    policy.prompt_ready = True

    move = policy.next_decision(state)

    assert move is not None
    assert move.command == "east"
    assert policy.fastwalk_invisibility_attempts == 0


def test_field_circuit_does_not_eat_preflight_pie_when_not_hungry() -> None:
    route = route_named("ambush")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(FieldHuntStop((), "goblin"),),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    state = CharacterState(
        level=8,
        hp=115,
        max_hp=115,
        mana=316,
        max_mana=316,
        move=200,
        max_move=220,
        room_name="The Trail to Miden'nir",
        room_vnum="3505",
        position=7,
        inventory=[[{"short_desc": "a big pot pie"}]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "look"
    assert policy.fastwalk_hunt_preflight_food_attempted is True


def test_field_circuit_eats_preflight_pie_when_hungry() -> None:
    route = route_named("ambush")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(FieldHuntStop((), "goblin"),),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.needs_food = True
    state = CharacterState(
        level=8,
        hp=115,
        max_hp=115,
        mana=316,
        max_mana=316,
        move=200,
        max_move=220,
        room_name="The Trail to Miden'nir",
        room_vnum="3505",
        position=7,
        inventory=[[{"short_desc": "a big pot pie"}]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "eat pie"


def test_fastwalk_pursues_and_reengages_a_fleeing_requested_target() -> None:
    route = route_named("circus midget")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_attack_target="midget",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.room_targets["4411"] = ["midget"]
    tent = CharacterState(room_name="The Midget's Tent", room_vnum="4411", position=7)

    attack = policy.next_decision(tent)
    assert attack is not None
    assert attack.command == "consider midget"
    policy.after_command(attack)
    policy.observe_text("The perfect match!\n")
    policy.prompt_ready = True

    attack = policy.next_decision(tent)
    assert attack is not None
    assert attack.command == "kill midget"
    policy.after_command(attack)
    policy.observe_text(
        "Your pound scratches the Midget.\n"
        "The Midget leaves north.\n"
        "The Midget has fled!\n"
    )
    policy.prompt_ready = True

    pursuit = policy.next_decision(tent)
    assert pursuit is not None
    assert pursuit.command == "north"
    policy.after_command(pursuit)
    policy.current_room = "4410"
    policy.room_targets["4410"] = ["midget"]
    policy.prompt_ready = True

    reengage = policy.next_decision(
        CharacterState(room_name="The Illusionist's Tent", room_vnum="4410", position=7)
    )
    assert reengage is not None
    assert reengage.command == "kill midget"
    assert policy.combat_active is True


def test_fastwalk_return_leaves_mud_school_after_recovery() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_returning = True

    decision = policy.next_decision(
        CharacterState(room_name="The Entrance to the Mud School", room_vnum="3725")
    )

    assert decision is not None
    assert decision.command == "down"


def test_fastwalk_return_leaves_general_supplies_after_recovery() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry"),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_returning = True

    decision = policy.next_decision(
        CharacterState(room_name="General Supplies", room_vnum="3724")
    )

    assert decision is not None
    assert decision.command == "down"


def test_fastwalk_outbound_returns_from_healer_to_recall_origin() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry"),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True

    decision = policy.next_decision(
        CharacterState(room_name="By the Temple Altar", room_vnum="3054")
    )

    assert decision is not None
    assert decision.command == "south"


def test_fastwalk_records_an_incidental_kill_name_from_death_text() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("circus midget"),
    )
    policy.current_room = "2172"
    policy.combat_active = True

    policy.observe_text(
        "The drunk is DEAD!!\n"
        "You receive 46 experience points for the kill.\n"
        "You gained a total of 82 experience points!\n"
    )

    assert policy.completed_kills == [{"mob_name": "drunk", "xp_gained": 82}]


def test_fastwalk_probe_withdraws_when_fresh_look_does_not_show_requested_target() -> None:
    route = route_named("moria")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_explore_direction="north",
        fastwalk_attack_target="kobold",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_explore_step = 2
    policy.fastwalk_explore_distance = 1
    policy.room_targets["4018"] = []

    decision = policy.next_decision(
        CharacterState(room_name="The cave", room_vnum="4018", position=7)
    )

    assert decision is not None
    assert decision.command == "south"
    assert policy.active_target is None
    assert policy.fastwalk_attack_started is False
    assert policy.fastwalk_target_absent is True
    policy.after_command(decision)
    policy.prompt_ready = True

    endpoint = CharacterState(room_name="The tunnel", room_vnum="4014", position=7)
    recall = policy.next_decision(endpoint)

    assert recall is not None
    assert recall.command == "recall"


def test_fastwalk_research_loots_confirmed_endpoint_kill_before_recall() -> None:
    route = route_named("moria")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_explore_direction="north",
        fastwalk_attack_target="kobold",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_attack_started = True
    policy.current_room = "4014"
    policy.pending_loot_rooms.add("4014")
    endpoint = CharacterState(room_name="The tunnel", room_vnum="4014", position=7)

    loot = policy.next_decision(endpoint)
    assert loot is not None
    assert loot.command == "get all corpse"
    policy.after_command(loot)
    policy.prompt_ready = True

    sacrifice = policy.next_decision(endpoint)
    assert sacrifice is not None
    assert sacrifice.command == "sacrifice corpse"
    policy.after_command(sacrifice)
    policy.prompt_ready = True

    inventory = policy.next_decision(endpoint)
    assert inventory is not None
    assert inventory.command == "inventory"
    policy.after_command(inventory)
    policy.prompt_ready = True

    recall = policy.next_decision(endpoint)
    assert recall is not None
    assert recall.command == "recall"


def test_fastwalk_stows_source_identified_sanctuary_potion_before_recall() -> None:
    route = route_named("moria")
    policy = StarterPolicy(_spec(), "swordfish", fastwalk_route=route)
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.current_room = "4064"
    policy.pending_loot_rooms.add("4064")
    policy.fastwalk_loot_step = 1
    policy.fastwalk_last_kill_target = "the large hobgoblin"
    state = CharacterState(
        room_name="A Moria tunnel",
        room_vnum="4064",
        position=7,
        inventory=[[{"quan": "1", "short_desc": "a purple potion"}]],
    )

    audit = policy.next_decision(state)
    assert audit is not None
    assert audit.command == "inventory"
    policy.prompt_ready = True

    stow = policy.next_decision(state)
    assert stow is not None
    assert stow.command == "put all.purple pouch"
    policy.observe_text("You put a purple potion in a small leather pouch.\n")
    policy.prompt_ready = True

    sacrifice = policy.next_decision(state)

    assert sacrifice is not None
    assert sacrifice.command == "sacrifice corpse"
    assert policy.combat_pouch_potions == {"purple": 1}


def test_fastwalk_does_not_stow_an_unregistered_potion() -> None:
    route = route_named("moria")
    policy = StarterPolicy(_spec(), "swordfish", fastwalk_route=route)
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.current_room = "4064"
    policy.pending_loot_rooms.add("4064")
    policy.fastwalk_loot_step = 1
    policy.fastwalk_last_kill_target = "the large hobgoblin"
    state = CharacterState(
        room_name="A Moria tunnel",
        room_vnum="4064",
        position=7,
        inventory=[[{"quan": "1", "short_desc": "a cloudy potion"}]],
    )

    audit = policy.next_decision(state)
    assert audit is not None
    assert audit.command == "inventory"
    policy.prompt_ready = True

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "sacrifice corpse"


def test_fastwalk_audits_known_combat_potions_at_recall_before_departure() -> None:
    route = route_named("moria")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        audit_combat_pouch=True,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    origin = CharacterState(
        room_name="The Temple Of Midgaard",
        room_vnum="3001",
        position=7,
    )

    audit = policy.next_decision(origin)
    assert audit is not None
    assert audit.command == "look in pouch"
    policy.observe_text(
        "A small leather pouch contains:\n"
        "     a purple potion\n"
        "     a purple potion\n"
        "     a black potion\n"
    )
    policy.prompt_ready = True

    departure = policy.next_decision(origin)

    assert departure is not None
    assert departure.command == route.commands[0]
    assert policy.combat_pouch_potions == {"black": 1, "purple": 2}


def test_fastwalk_stows_loose_known_potion_at_origin_before_departure() -> None:
    route = route_named("ambush")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        audit_combat_pouch=True,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_pouch_audited = True
    origin = CharacterState(
        room_name="The Temple Of Midgaard",
        room_vnum="3001",
        position=7,
        inventory=[[{"short_desc": "a purple potion"}]],
    )

    stow = policy.next_decision(origin)

    assert stow is not None
    assert stow.command == "put all.purple pouch"


def test_combat_uses_identified_pouch_potions_at_bounded_health_thresholds() -> None:
    route = route_named("ambush")
    policy = StarterPolicy(_spec(), "swordfish", fastwalk_route=route)
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.fastwalk_attack_started = True
    policy.active_target = "war dog"
    policy.combat_pouch_potions.update({"black": 1, "purple": 1})
    state = CharacterState(
        hp=50,
        max_hp=100,
        mana=200,
        max_mana=250,
        position=6,
        room_name="In a forest clearing",
        room_vnum="4505",
    )

    healing = policy.next_decision(state)
    assert healing is not None
    assert healing.command == "quaff black"
    policy.prompt_ready = True
    state.hp = 75

    protection = policy.next_decision(state)

    assert protection is not None
    assert protection.command == "quaff purple"
    assert policy.combat_pouch_potions == {}


def test_combat_uses_sanctuary_reserve_before_health_falls() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.fastwalk_attack_started = True
    policy.active_target = "vile goblin"
    policy.combat_pouch_potions.update({"purple": 2})
    state = CharacterState(
        hp=100,
        max_hp=100,
        mana=200,
        max_mana=250,
        position=6,
        room_name="On a small trail",
        room_vnum="4519",
    )

    protection = policy.next_decision(state)

    assert protection is not None
    assert protection.command == "quaff purple"
    assert policy.combat_pouch_potions == {"purple": 1}


def test_fastwalk_research_loots_incidental_kill_before_resuming_route() -> None:
    route = route_named("foundry captain")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_attack_target="Ushog",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands) - 1
    policy.current_room = "109"
    policy.pending_loot_rooms.add("109")
    policy.fastwalk_last_kill_target = "Olog"
    tunnel = CharacterState(
        room_name="Muddy Tunnel",
        room_vnum="109",
        position=7,
        hp=90,
        max_hp=100,
    )

    loot = policy.next_decision(tunnel)
    assert loot is not None
    assert loot.command == "get all corpse"
    policy.after_command(loot)
    policy.prompt_ready = True

    sacrifice = policy.next_decision(tunnel)
    assert sacrifice is not None
    assert sacrifice.command == "sacrifice corpse"
    policy.after_command(sacrifice)
    policy.prompt_ready = True

    inventory = policy.next_decision(tunnel)
    assert inventory is not None
    assert inventory.command == "inventory"
    policy.after_command(inventory)
    policy.prompt_ready = True

    leave = policy.next_decision(tunnel)
    assert leave is not None
    assert leave.command == "south"
    assert policy.fastwalk_attack_started is False


def test_recall_only_fastwalk_recalls_after_low_health_incidental_kill() -> None:
    route = route_named("foundry captain")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_attack_target="Ushog",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.current_room = "109"
    policy.pending_loot_rooms.add("109")
    policy.fastwalk_last_kill_target = "Olog"
    tunnel = CharacterState(
        room_name="Muddy Tunnel",
        room_vnum="109",
        position=7,
        hp=70,
        max_hp=100,
    )

    loot = policy.next_decision(tunnel)
    assert loot is not None
    policy.after_command(loot)
    policy.prompt_ready = True
    sacrifice = policy.next_decision(tunnel)
    assert sacrifice is not None
    assert sacrifice.command == "sacrifice corpse"
    policy.after_command(sacrifice)
    policy.prompt_ready = True
    inventory = policy.next_decision(tunnel)
    assert inventory is not None
    policy.after_command(inventory)
    policy.prompt_ready = True

    recall = policy.next_decision(tunnel)

    assert recall is not None
    assert recall.command == "recall"


def test_recall_only_fastwalk_recalls_after_objective_kill() -> None:
    route = route_named("foundry captain")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_attack_target="Ushog",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.current_room = "112"
    policy.pending_loot_rooms.add("112")
    policy.fastwalk_last_kill_target = "Ushog"
    quarters = CharacterState(
        room_name="Ushog's Quarters",
        room_vnum="112",
        position=7,
        hp=90,
        max_hp=100,
    )

    loot = policy.next_decision(quarters)
    assert loot is not None
    policy.after_command(loot)
    policy.prompt_ready = True
    sacrifice = policy.next_decision(quarters)
    assert sacrifice is not None
    assert sacrifice.command == "sacrifice corpse"
    policy.after_command(sacrifice)
    policy.prompt_ready = True
    inventory = policy.next_decision(quarters)
    assert inventory is not None
    policy.after_command(inventory)
    policy.prompt_ready = True

    recall = policy.next_decision(quarters)

    assert recall is not None
    assert recall.command == "recall"


def test_fastwalk_research_claims_corpse_from_aggressive_combat() -> None:
    route = route_named("foundry")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_attack_target="Oshu",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = 14
    policy.current_room = "109"
    tunnel = CharacterState(room_name="Muddy Tunnel", room_vnum="109", position=7)

    blocked_move = BotDecision("east", "follow official fastwalk foundry")
    policy.after_command(blocked_move)
    assert policy.pending_travel_origin == "109"

    policy.observe_text("No way! You are still fighting!\n")
    assert policy.pending_travel_origin is None
    assert policy.combat_active is True
    assert policy.fastwalk_outbound_index == 13

    policy.observe_text(
        "Olog is DEAD!!\n"
        "You receive 10 experience points for the kill.\n"
    )
    policy.prompt_ready = True
    loot = policy.next_decision(tunnel)

    assert loot is not None
    assert loot.command == "get all corpse"
    assert policy.combat_active is False


def test_fastwalk_recognizes_mob_attack_text_on_its_final_route_step() -> None:
    route = route_named("foundry")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_attack_target="Olog",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    state = CharacterState(
        room_name="Muddy Tunnel",
        room_vnum="108",
        hp=96,
        max_hp=96,
        mana=268,
        max_mana=268,
        position=7,
    )

    policy.observe_text("Olog's pound misses you.\n")
    decision = policy.next_decision(state)

    assert policy.combat_active is True
    assert policy.fastwalk_arrival_observed is True
    assert decision is not None
    assert decision.command == "cast 'magic missile' Olog"


def test_fastwalk_research_does_not_claim_unrelated_corpse() -> None:
    route = route_named("foundry")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_attack_target="Oshu",
    )
    policy.current_room = "109"

    policy.observe_text("A goblin is DEAD!!\n")

    assert policy.pending_loot_rooms == set()


def test_fastwalk_records_mob_kill_and_observed_xp() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_attack_target="Olog",
    )
    policy.current_room = "109"
    policy.combat_active = True
    policy.active_target = "Olog"

    policy.observe_text(
        "Olog is DEAD!!\n"
        "You receive 20 experience points for the kill.\n"
        "You gained a total of 45 experience points!\n"
    )

    assert policy.completed_kills == [
        {"mob_name": "Olog", "xp_gained": 45}
    ]


def test_fastwalk_records_post_circuit_attacker_without_indexing_finished_stop() -> None:
    route = route_named("foundry")
    policy = StarterPolicy(
        _spec(race="drow"),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=foundry_level_six_hunt_stops(),
    )
    policy.current_room = "3013"
    policy.fastwalk_returning = True
    policy.fastwalk_hunt_stop_index = len(policy.fastwalk_hunt_stops)
    policy.combat_active = True
    policy.active_target = "the drunk"

    policy.observe_text(
        "The drunk is DEAD!!\n"
        "You receive 10 experience points for the kill.\n"
        "You gained a total of 20 experience points!\n"
    )

    assert policy.fastwalk_hunt_stop_killed is False
    assert policy.completed_kills == [
        {"mob_name": "the drunk", "xp_gained": 20}
    ]


def test_fastwalk_research_recognizes_existing_room_combat() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_attack_target="Olog",
    )

    policy.observe_text("Olog is here, fighting YOU!\n")

    assert policy.combat_active is True


def test_fastwalk_repeat_limit_allows_the_route_run_but_not_extra_steps() -> None:
    route = route_named("moria")

    assert _max_consecutive_command(route.commands, "north") == 8
    assert _max_consecutive_command(route.commands, "south") == 2


def test_recall_only_fastwalk_with_door_command_fails_cleanly_if_recall_fails() -> None:
    route = route_named("foundry captain")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_attack_target="Ushog",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_returning = True
    foundry = CharacterState(
        area="The Foundry",
        room_name="Ushog's Quarters",
        room_vnum="112",
        position=7,
    )

    decision = policy.next_decision(foundry)

    assert decision is None
    assert policy.failure is not None
    assert policy.failure.startswith("recall-only fastwalk did not reach")


def test_fastwalk_recall_ignores_delayed_same_room_prompt_until_room_changes() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry captain"),
        fastwalk_attack_target="Ushog",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_returning = True
    policy.current_room = "112"
    policy.after_command(BotDecision("recall", "return after field combat"))
    policy.prompt_ready = True
    foundry = CharacterState(
        area="The Foundry",
        room_name="Ushog's Quarters",
        room_vnum="112",
        position=7,
    )

    delayed_prompt = policy.next_decision(foundry)

    assert delayed_prompt is None
    assert policy.failure is None
    assert policy.pending_recall_origin == "112"

    temple = CharacterState(
        area="Midgaard",
        room_name="The Temple Of Midgaard",
        room_vnum="3001",
        position=7,
    )
    policy.observe_events(
        [GameEvent("room_entered", "gmcp", {"value": {"vnum": "3001"}})],
        temple,
    )
    policy.prompt_ready = True

    homeward = policy.next_decision(temple)

    assert homeward is not None
    assert homeward.command == "north"
    assert policy.pending_recall_origin is None


def test_fastwalk_recall_rejection_clears_pending_wait_and_fails_cleanly() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry captain"),
        fastwalk_attack_target="Ushog",
    )
    policy.in_world = True
    policy.fastwalk_returning = True
    policy.current_room = "112"
    policy.after_command(BotDecision("recall", "return after field combat"))

    policy.observe_text("God has forsaken you.\n")
    policy.prompt_ready = True
    decision = policy.next_decision(
        CharacterState(
            area="The Foundry",
            room_name="Ushog's Quarters",
            room_vnum="112",
            position=7,
        )
    )

    assert decision is None
    assert policy.pending_recall_origin is None
    assert policy.failure is not None
    assert policy.failure.startswith("recall-only fastwalk did not reach")


def test_inventory_descriptions_parse_serialized_gmcp_inventory() -> None:
    value = (
        '[ [ { "quan": "1", "short_desc": "a metal buckler" }, '
        '{ "quan": "1", "short_desc": "\\u001b[38;5;39m[-?-]\\u001b[0m '
        'a spiked metal rod" } ] ]'
    )

    assert _inventory_descriptions(value) == [
        "a metal buckler",
        "\x1b[38;5;39m[-?-]\x1b[0m a spiked metal rod",
    ]


def test_inventory_descriptions_expand_stacked_quantities() -> None:
    value = [[{"quan": "2", "short_desc": "a pair of blue snakeskin boots"}]]

    assert _inventory_descriptions(value) == [
        "a pair of blue snakeskin boots",
        "a pair of blue snakeskin boots",
    ]


def test_liquidation_plans_distinct_items_for_best_safe_shops() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    policy.in_world = True
    policy.prompt_ready = True
    home = CharacterState(
        room_name="Mage's Laboratory",
        room_vnum="3019",
        position=7,
        inventory=[
            [
                {"short_desc": "a metal buckler", "quan": "1"},
                {"short_desc": "[-?-] a spiked metal rod", "quan": "1"},
                {"short_desc": "a big pot pie", "quan": "2"},
            ]
        ],
    )

    first_move = policy.next_decision(home)

    assert first_move is not None
    assert first_move.command == "west"
    assert [(keyword, shop.name) for keyword, shop in policy.sale_plan] == [
        ("buckler", "Leather Shop"),
        ("rod", "Weapon Shop"),
    ]


def test_liquidation_uses_vis_before_shop_travel_or_trade() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    home = CharacterState(
        room_name="Mage's Laboratory",
        room_vnum="3019",
        position=7,
        affects=[[{"name": "invis", "duration": "5"}]],
        inventory=[[{"short_desc": "a war dog collar"}]],
    )

    decision = policy._liquidate_loot_decision(home)

    assert decision is not None
    assert decision.command == "vis"
    assert policy.sale_plan == []


def test_liquidation_donates_known_unsellable_redundant_overflow() -> None:
    trinket = ObjectSource(
        110,
        "broken trinket",
        "a broken trinket",
        13,
        (0, 0, 0, 0),
        0,
        wear_flags=1,
    )
    policy = StarterPolicy(
        _spec(race="elf"),
        "swordfish",
        liquidate_loot=True,
        gear_catalog=GearCatalog({trinket.vnum: trinket}),
    )
    policy.gear_audited = True
    home = CharacterState(
        room_name="Mage's Laboratory",
        room_vnum="3019",
        position=7,
        inventory=[[{"short_desc": "a broken trinket", "quan": "1"}]],
    )

    decision = policy._liquidate_loot_decision(home)

    assert decision is not None
    assert decision.command == "donate trinket"
    assert policy.sale_plan == []


def test_liquidation_donates_low_value_class_restricted_loot_under_pressure() -> None:
    ordinary = ObjectSource(
        1,
        "spear",
        "a wooden spear",
        5,
        (0, 6, 6, 0),
        100,
        wear_flags=1 << 13,
    )
    lance = ObjectSource(
        2,
        "wooden spear",
        "a wooden spear",
        5,
        (0, 2, 2, 0),
        55,
        wear_flags=1 << 13,
        extra_flags=1 << 27,
    )
    policy = StarterPolicy(
        _spec(race="elf"),
        "swordfish",
        liquidate_loot=True,
        gear_catalog=GearCatalog({ordinary.vnum: ordinary, lance.vnum: lance}),
    )
    policy.gear_audited = True
    policy.sale_identified_values["spear"] = 55
    home = CharacterState(
        room_name="Mage's Laboratory",
        room_vnum="3019",
        position=7,
        stats={"carry_wt": 136, "maxcarry_wt": 140},
        inventory=[[{"short_desc": "a wooden spear", "quan": "1"}]],
    )

    decision = policy._liquidate_loot_decision(home)

    assert decision is not None
    assert decision.command == "donate spear"
    assert policy.sale_plan == []


def test_liquidation_donates_expendable_item_after_best_shop_is_uninterested() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    shop = safe_shop_for_item("some leather leg guards")
    assert shop is not None
    policy.sale_plan = [("guards", shop)]
    policy.sale_phase = "sell"

    policy.observe_text("The armourer looks uninterested in some leather leg guards.\n")

    assert policy.sale_phase == "inventory"
    assert policy.donation_plan == ["guards"]

    policy.observe_text("The armourer looks uninterested in some leather leg guards.\n")

    assert policy.donation_plan == ["guards"]


def test_liquidation_collapses_rejected_duplicate_keyword_into_donations() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    weapon_shop = safe_shop_for_item("a length of metal piping")
    armour_shop = safe_shop_for_item("some leather leg guards")
    assert weapon_shop is not None
    assert armour_shop is not None
    policy.sale_plan = [
        ("piping", weapon_shop),
        ("piping", weapon_shop),
        ("piping", weapon_shop),
        ("piping", weapon_shop),
        ("guards", armour_shop),
    ]
    policy.sale_phase = "sell"

    policy.observe_text("The weaponsmith looks uninterested in metal piping.\n")

    assert policy.sale_plan == [
        ("piping", weapon_shop),
        ("guards", armour_shop),
    ]
    assert policy.donation_plan == ["piping"] * 4
    assert policy.sale_phase == "inventory"


def test_liquidation_preserves_water_storage_even_when_unsellable() -> None:
    skin = ObjectSource(
        3138,
        "skin water buffalo",
        "a buffalo water skin",
        17,
        (100, 100, 0, 0),
        30,
        wear_flags=1,
    )
    policy = StarterPolicy(
        _spec(race="elf"),
        "swordfish",
        liquidate_loot=True,
        gear_catalog=GearCatalog({skin.vnum: skin}),
    )
    policy.gear_audited = True
    home = CharacterState(
        room_name="Mage's Laboratory",
        room_vnum="3019",
        position=7,
        inventory=[[{"short_desc": "a buffalo water skin", "quan": "1"}]],
    )

    decision = policy._liquidate_loot_decision(home)

    assert decision is None
    assert policy.sale_plan == []
    assert policy.donation_plan == []


def test_invisible_shop_rejection_retries_the_unsold_item_after_vis() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    policy.sale_phase = "inventory"
    policy.observe_text("The armourer says 'I don't trade with folks I can't see.'")
    shop = safe_shop_for_item("a war dog collar", item_type=9)
    assert shop is not None
    policy.sale_plan = [("collar", shop)]
    policy.sale_index = 0
    at_shop = CharacterState(
        room_name=shop.name,
        room_vnum=shop.room_vnum,
        position=7,
    )

    visible = policy._liquidate_loot_decision(at_shop)

    assert visible is not None
    assert visible.command == "vis"
    assert policy.sale_phase == "sell"
    retry = policy._liquidate_loot_decision(at_shop)
    assert retry is not None
    assert retry.command == "sell collar"


def test_liquidation_recalls_an_interrupted_field_character_before_planning() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    policy.in_world = True
    policy.prompt_ready = True
    field = CharacterState(
        area="Miden'nir",
        room_name="The Trail to Miden'nir",
        room_vnum="2300",
        hp=115,
        max_hp=115,
        mana=316,
        max_mana=316,
        move=220,
        max_move=220,
        position=7,
    )

    recall = policy.next_decision(field)

    assert recall is not None
    assert recall.command == "recall"
    assert policy.failure is None


def test_human_identifies_loot_and_keeps_stat_circlet_before_sale() -> None:
    circlet = ObjectSource(
        108,
        "silver circlet",
        "a silver circlet",
        8,
        (0, 0, 0, 0),
        0,
        wear_flags=1 | (1 << 2),
        affects=((3, 1),),
    )
    cap = ObjectSource(
        109,
        "iron cap",
        "an iron cap",
        9,
        (5, 0, 0, 0),
        0,
        wear_flags=1 | (1 << 4),
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        liquidate_loot=True,
        gear_catalog=GearCatalog({circlet.vnum: circlet, cap.vnum: cap}),
    )
    policy.in_world = True
    policy.gear_audited = True
    home = CharacterState(
        room_name="Mage's Laboratory",
        room_vnum="3019",
        position=7,
        inventory=[
            [
                {"short_desc": "[SET] a silver circlet", "quan": "1"},
                {"short_desc": "an iron cap", "quan": "1"},
            ]
        ],
    )

    policy.prompt_ready = True
    identify_circlet = policy.next_decision(home)
    policy.prompt_ready = True
    identify_cap = policy.next_decision(home)
    policy.prompt_ready = True
    first_move = policy.next_decision(home)

    assert identify_circlet is not None
    assert identify_circlet.command == "cast 'identify' circlet"
    assert identify_cap is not None
    assert identify_cap.command == "cast 'identify' cap"
    assert first_move is not None
    assert first_move.command == "west"
    assert policy.sale_plan == []


def test_liquidation_sells_one_copy_after_retaining_the_best_stacked_item() -> None:
    boots = ObjectSource(
        112,
        "blue snakeskin boots",
        "a pair of blue snakeskin boots",
        8,
        (2, 0, 0, 0),
        60,
        wear_flags=1 | (1 << 6),
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        liquidate_loot=True,
        gear_catalog=GearCatalog({boots.vnum: boots}),
    )
    policy.in_world = True
    policy.gear_audited = True
    home = CharacterState(
        room_name="Mage's Laboratory",
        room_vnum="3019",
        level=7,
        position=7,
        inventory=[
            [{"short_desc": "a pair of blue snakeskin boots", "quan": "2"}]
        ],
    )

    policy.prompt_ready = True
    identify = policy.next_decision(home)
    assert identify is not None
    assert identify.command == "cast 'identify' boots"
    policy.after_command(identify)
    policy.observe_text(
        "It is worn on the feet.\n"
        "It is worth 60 copper coins and is level 1.\n"
    )
    policy.prompt_ready = True
    first_move = policy.next_decision(home)

    assert first_move is not None
    assert [(keyword, shop.name) for keyword, shop in policy.sale_plan] == [
        ("boots", "Jeweller")
    ]


def test_liquidation_keeps_best_carried_combat_item_for_an_empty_slot() -> None:
    better = ObjectSource(
        110,
        "leather jerkin",
        "a leather jerkin",
        9,
        (4, 0, 0, 0),
        0,
        wear_flags=1 | (1 << 3),
    )
    weaker = ObjectSource(
        111,
        "cloth shirt",
        "a cloth shirt",
        9,
        (1, 0, 0, 0),
        0,
        wear_flags=1 | (1 << 3),
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        liquidate_loot=True,
        gear_catalog=GearCatalog({better.vnum: better, weaker.vnum: weaker}),
    )
    policy.in_world = True
    policy.gear_audited = True
    home = CharacterState(
        room_name="Mage's Laboratory",
        room_vnum="3019",
        level=6,
        position=7,
        inventory=[
            [
                {"short_desc": "a leather jerkin", "quan": "1"},
                {"short_desc": "a cloth shirt", "quan": "1"},
            ]
        ],
    )

    for _ in range(3):
        policy.prompt_ready = True
        policy.next_decision(home)

    assert [(keyword, shop.name) for keyword, shop in policy.sale_plan] == [
        ("shirt", "Leather Shop")
    ]


def test_liquidation_audits_worn_gear_before_retaining_carried_items() -> None:
    chainmail = ObjectSource(
        113,
        "chainmail vest",
        "a chainmail vest",
        9,
        (4, 0, 0, 0),
        20,
        wear_flags=1 | (1 << 3),
    )
    jerkin = ObjectSource(
        114,
        "leather jerkin",
        "a leather jerkin",
        9,
        (2, 0, 0, 0),
        40,
        wear_flags=1 | (1 << 3),
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        liquidate_loot=True,
        gear_catalog=GearCatalog(
            {chainmail.vnum: chainmail, jerkin.vnum: jerkin}
        ),
    )
    policy.in_world = True
    home = CharacterState(
        room_name="Mage's Laboratory",
        room_vnum="3019",
        level=7,
        position=7,
        inventory=[[{"short_desc": "a leather jerkin", "quan": "1"}]],
    )

    policy.prompt_ready = True
    audit = policy.next_decision(home)
    assert audit is not None
    assert audit.command == "equipment"
    policy.after_command(audit)
    policy.observe_text("<worn on body> a chainmail vest\n")
    policy.prompt_ready = True
    identify = policy.next_decision(home)
    assert identify is not None
    assert identify.command == "cast 'identify' jerkin"
    policy.after_command(identify)
    policy.observe_text("It is worth 40 copper coins and is level 1.\n")
    policy.prompt_ready = True
    first_move = policy.next_decision(home)

    assert first_move is not None
    assert [(keyword, shop.name) for keyword, shop in policy.sale_plan] == [
        ("jerkin", "Leather Shop")
    ]


def test_liquidation_uses_character_sale_history() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        liquidate_loot=True,
        loot_sale_counts={("buckler", "Leather Shop"): 1},
    )
    policy.in_world = True
    policy.prompt_ready = True
    home = CharacterState(
        room_name="Mage's Laboratory",
        room_vnum="3019",
        position=7,
        inventory=[[{"short_desc": "a metal buckler", "quan": "1"}]],
    )

    first_move = policy.next_decision(home)

    assert first_move is not None
    assert [(keyword, shop.name) for keyword, shop in policy.sale_plan] == [
        ("buckler", "Armoury"),
    ]


def test_liquidation_opens_and_extracts_a_purse_before_planning_sales() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    policy.in_world = True
    policy.prompt_ready = True
    home = CharacterState(
        room_name="Mage's Laboratory",
        room_vnum="3019",
        position=7,
        inventory=[[{"short_desc": "the midget's purse", "quan": "1"}]],
    )

    opened = policy.next_decision(home)

    assert opened is not None
    assert opened.command == "open purse"
    policy.after_command(opened)
    policy.prompt_ready = True

    extracted = policy.next_decision(home)

    assert extracted is not None
    assert extracted.command == "get all purse"


def test_fastwalk_extracts_source_backed_container_before_inventory() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("circus midget"),
        fastwalk_attack_target="midget",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.current_room = "4411"
    policy.pending_loot_rooms.add("4411")
    tent = CharacterState(
        room_name="The Midget's Tent",
        room_vnum="4411",
        position=7,
    )

    corpse = policy.next_decision(tent)
    assert corpse is not None
    assert corpse.command == "get all corpse"
    policy.after_command(corpse)
    policy.prompt_ready = True

    opened = policy.next_decision(tent)

    assert opened is not None
    assert opened.command == "open purse"
    policy.after_command(opened)
    policy.prompt_ready = True

    purse = policy.next_decision(tent)

    assert purse is not None
    assert purse.command == "get all purse"


def test_liquidation_scopes_sale_history_to_time_boot_identity() -> None:
    current_boot = "Sun Jul 19 12:00:00 2026"
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        liquidate_loot=True,
        query_world_time=True,
        loot_sale_history=[
            {
                "boot_id": "Sat Jul 18 12:00:00 2026",
                "item_keyword": "buckler",
                "shop_name": "Leather Shop",
            },
            {
                "boot_id": current_boot,
                "item_keyword": "buckler",
                "shop_name": "Leather Shop",
            },
        ],
    )
    policy.in_world = True
    policy.prompt_ready = True
    home = CharacterState(
        room_name="Mage's Laboratory",
        room_vnum="3019",
        position=7,
        inventory=[[{"short_desc": "a metal buckler", "quan": "1"}]],
    )

    time_query = policy.next_decision(home)
    assert time_query is not None
    assert time_query.command == "time"
    policy.after_command(time_query)
    policy.observe_text(f"DD was started at {current_boot}\n")
    policy.prompt_ready = True

    first_move = policy.next_decision(home)

    assert first_move is not None
    assert policy.world_boot_id == current_boot
    assert [(keyword, shop.name) for keyword, shop in policy.sale_plan] == [
        ("buckler", "Armoury"),
    ]


def test_liquidation_ignores_duplicate_sales_from_previous_boot() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        liquidate_loot=True,
        query_world_time=True,
        loot_sale_history=[
            {
                "boot_id": "Sat Jul 18 12:00:00 2026",
                "item_keyword": "buckler",
                "shop_name": "Leather Shop",
            }
        ],
    )
    policy.in_world = True
    policy.prompt_ready = True
    home = CharacterState(
        room_name="Mage's Laboratory",
        room_vnum="3019",
        position=7,
        inventory=[[{"short_desc": "a metal buckler", "quan": "1"}]],
    )

    time_query = policy.next_decision(home)
    assert time_query is not None
    policy.after_command(time_query)
    policy.observe_text("DD was started at Sun Jul 19 12:00:00 2026\n")
    policy.prompt_ready = True
    policy.next_decision(home)

    assert [(keyword, shop.name) for keyword, shop in policy.sale_plan] == [
        ("buckler", "Leather Shop"),
    ]


def test_liquidation_captures_offer_and_completed_sale() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    shop = safe_shop_for_item("a metal buckler")
    assert shop is not None
    policy.sale_plan = [("buckler", shop)]

    policy.observe_text(
        "The leather worker tells you "
        "'I'll give you 10 coins for a metal buckler'.\n"
    )
    policy.observe_text("You sell a metal buckler for 10 coins.\n")

    assert policy.completed_sales == [
        {
            "item_keyword": "buckler",
            "item_description": "a metal buckler",
            "shop_name": "Leather Shop",
            "shop_room_vnum": "3035",
            "offered_coins": 10,
            "sold_coins": 10,
        }
    ]


def test_magic_shop_research_lists_stock_and_returns_to_healer() -> None:
    policy = StarterPolicy(_spec(), "swordfish", magic_shop_research=True)
    policy.in_world = True
    policy.prompt_ready = True

    outward = (
        ("By the Temple Altar", "3054", "south"),
        ("Temple Square", "3001", "south"),
        ("The Fountain", "3005", "south"),
        ("Market Square", "3006", "west"),
        ("Main Street", "3014", "west"),
        ("Main Street", "3013", "west"),
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
        ("Main Street", "3012", "east"),
        ("Main Street", "3013", "east"),
        ("Main Street", "3014", "north"),
        ("Market Square", "3006", "north"),
        ("The Fountain", "3005", "north"),
        ("Temple Square", "3001", "north"),
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
        CharacterState(room_name="By the Temple Altar", room_vnum="3054", position=7)
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
    for index in range(5):
        if index >= 3:
            shop.inventory = (
                '[[{"quan": "1", "short_desc": "a light blue potion"}]]'
            )
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


def test_magic_shop_research_becomes_visible_and_restarts_stock_check() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        magic_shop_research=True,
        magic_shop_buy_fly=True,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.magic_shop_step = 2
    policy.observe_text("The wizard says 'I don't trade with folks I can't see.'")
    shop = CharacterState(
        room_name="The Magic Shop",
        room_vnum="3033",
        position=7,
    )

    visible = policy.next_decision(shop)

    assert visible is not None
    assert visible.command == "vis"
    assert policy.magic_shop_step == 0
    policy.after_command(visible)
    policy.prompt_ready = True

    listing = policy.next_decision(shop)
    assert listing is not None
    assert listing.command == "list"


def test_magic_shop_research_does_not_quaff_an_unconfirmed_purchase() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        magic_shop_research=True,
        magic_shop_buy_fly=True,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.magic_shop_step = 3

    decision = policy.next_decision(
        CharacterState(
            room_name="The Magic Shop",
            room_vnum="3033",
            position=7,
            inventory="[]",
        )
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


def test_mage_lab_recovery_routes_to_healer_before_sleeping() -> None:
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

    route = policy.next_decision(resting)
    assert route is not None
    assert route.command == "west"
    assert "healer" in route.reason
    policy.after_command(route)
    policy.prompt_ready = True

    resting.room_name = "The Altar of the Temple"
    resting.room_vnum = "3054"
    sleep = policy.next_decision(resting)
    assert sleep is not None
    assert sleep.command == "sleep"
    policy.after_command(sleep)

    policy.prompt_ready = True
    resting.position = 4
    resting.move = 100
    resting.hp = 96
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


def test_arena_policy_follows_midgaard_map_from_mage_guild_to_school() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=7)
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        level=6,
        hp=96,
        max_hp=96,
        mana=268,
        max_mana=268,
        move=173,
        max_move=200,
        position=7,
        room_name="Mage's Laboratory",
        room_vnum="3019",
        room_flags=["safe"],
        inventory=[
            [
                {"quan": "3", "short_desc": "a big pot pie"},
                {"quan": "1", "short_desc": "a buffalo water skin"},
            ]
        ],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "west"


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


def test_movement_exhaustion_routes_from_mud_school_to_healer() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=5)
    policy.in_world = True
    policy.prompt_ready = True
    policy.waiting_for_move = True
    state = CharacterState(
        hp=79,
        max_hp=79,
        move=2,
        max_move=180,
        position=7,
        room_name="The Entrance to the Mud School",
        room_vnum="3725",
        room_flags=["no_mob", "indoors", "safe"],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "down"
    assert "healer" in decision.reason


def test_low_movement_routes_to_healer_before_emergency_supply_travel() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=5)
    policy.in_world = True
    policy.prompt_ready = True
    policy.needs_drink = True
    state = CharacterState(
        hp=79,
        max_hp=79,
        move=2,
        max_move=180,
        position=7,
        room_name="The Temple Of Midgaard",
        room_vnum="3001",
        room_flags=["no_mob", "indoors", "safe"],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "north"
    assert "healer" in decision.reason


@pytest.mark.parametrize(
    ("room_name", "room_vnum", "command"),
    [
        ("Mage's Laboratory", "3019", "west"),
        ("Entrance to Mage's Guild", "3017", "north"),
        ("The Temple Of Midgaard", "3001", "north"),
    ],
)
def test_exhausted_midgaard_character_routes_to_healer_instead_of_sleeping(
    room_name: str,
    room_vnum: str,
    command: str,
) -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=10)
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        hp=79,
        max_hp=79,
        move=20,
        max_move=220,
        position=7,
        room_name=room_name,
        room_vnum=room_vnum,
        room_flags=["safe"],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == command
    assert "healer" in decision.reason


def test_healer_movement_recovery_returns_to_interrupted_mage_lab_route() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=10)
    policy.in_world = True
    policy.prompt_ready = True
    exhausted = CharacterState(
        hp=79,
        max_hp=79,
        move=20,
        max_move=220,
        position=7,
        room_name="Mage's Laboratory",
        room_vnum="3019",
        room_flags=["safe"],
    )

    outbound = policy.next_decision(exhausted)

    assert outbound is not None
    assert outbound.command == "west"
    assert policy.movement_recovery_return_route

    recovered = CharacterState(
        hp=79,
        max_hp=79,
        move=150,
        max_move=220,
        position=4,
        room_name="The Altar of the Temple",
        room_vnum="3054",
        room_flags=["safe"],
    )
    policy.prompt_ready = True
    stand = policy.next_decision(recovered)

    assert stand is not None
    assert stand.command == "stand"

    recovered.position = 7
    policy.prompt_ready = True
    return_step = policy.next_decision(recovered)

    assert return_step is not None
    assert return_step.command == "south"
    assert return_step.reason == "return to the route interrupted by healer recovery"


def test_healer_route_waits_for_each_room_transition_and_round_trips() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=10)
    policy.in_world = True
    policy.prompt_ready = True
    policy.current_room = "3019"
    state = CharacterState(
        area="Midgaard",
        hp=79,
        max_hp=79,
        move=20,
        max_move=220,
        position=7,
        room_name="Mage's Laboratory",
        room_vnum="3019",
        room_flags=["safe"],
    )
    outbound = [
        ("west", "3018"),
        ("north", "3017"),
        ("north", "3012"),
        ("east", "3013"),
        ("east", "3014"),
        ("north", "3005"),
        ("north", "3001"),
        ("north", "3054"),
    ]

    for command, destination in outbound:
        decision = policy.next_decision(state)
        assert decision is not None
        assert decision.command == command
        policy.after_command(decision)

        policy.observe_events([GameEvent("vitals_changed", "gmcp", {})], state)
        assert policy.next_decision(state) is None

        state.apply(
            GameEvent(
                "room_updated",
                "gmcp",
                {"area": "Midgaard", "name": destination, "vnum": destination},
            )
        )
        policy.last_command_at = time.monotonic() - 1
        policy.observe_events(
            [
                GameEvent("room_updated", "gmcp", {}),
                GameEvent("prompt_seen", "text", {}),
            ],
            state,
        )

    sleep = policy.next_decision(state)
    assert sleep is not None
    assert sleep.command == "sleep"
    policy.after_command(sleep)
    state.position = 4
    state.move = 150
    policy.observe_events([GameEvent("vitals_changed", "gmcp", {})], state)

    stand = policy.next_decision(state)
    assert stand is not None
    assert stand.command == "stand"
    policy.after_command(stand)
    state.position = 7
    policy.last_command_at = time.monotonic() - 1
    policy.observe_events([GameEvent("prompt_seen", "text", {})], state)

    returning = [
        ("south", "3001"),
        ("south", "3005"),
        ("south", "3014"),
        ("west", "3013"),
        ("west", "3012"),
        ("south", "3017"),
        ("south", "3018"),
        ("east", "3019"),
    ]
    for command, destination in returning:
        decision = policy.next_decision(state)
        assert decision is not None
        assert decision.command == command
        policy.after_command(decision)
        state.apply(
            GameEvent(
                "room_updated",
                "gmcp",
                {"area": "Midgaard", "name": destination, "vnum": destination},
            )
        )
        policy.last_command_at = time.monotonic() - 1
        policy.observe_events(
            [
                GameEvent("room_updated", "gmcp", {}),
                GameEvent("prompt_seen", "text", {}),
            ],
            state,
        )

    assert policy.movement_recovery_return_index == len(returning)


@pytest.mark.parametrize("position, command", [(7, "recall"), (4, "stand")])
def test_diverted_midgaard_recovery_never_sleeps_in_magic_shop(
    position: int,
    command: str,
) -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=10)
    policy.in_world = True
    policy.prompt_ready = True
    policy.waiting_for_move = True
    policy.movement_recovery_return_route = ("south",)
    state = CharacterState(
        area="Midgaard",
        hp=79,
        max_hp=79,
        move=20,
        max_move=220,
        position=position,
        room_name="The Magic Shop",
        room_vnum="3033",
        room_flags=["safe"],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == command
    assert decision.command != "sleep"
    assert "healer" in decision.reason or "recall" in decision.reason


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


@pytest.mark.parametrize(
    ("room_name", "room_vnum", "command"),
    [
        ("Safety", "3737", "enter portal"),
        ("The Entrance to the Mud School", "3725", "down"),
        ("The Temple Of Midgaard", "3001", "north"),
    ],
)
def test_arena_recovery_routes_to_the_temple_healer(
    room_name: str,
    room_vnum: str,
    command: str,
) -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=10)
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        level=6,
        hp=87,
        max_hp=138,
        mana=127,
        max_mana=127,
        move=200,
        max_move=200,
        position=7,
        room_name=room_name,
        room_vnum=room_vnum,
        room_flags=["safe"],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == command
    assert "temple healer" in decision.reason


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


def test_level_nine_mage_prefers_chill_touch() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=9)
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.active_target = "a mountain goblin"
    policy.known_skills.add("chill touch")
    state = CharacterState(
        level=9,
        hp=105,
        max_hp=110,
        mana=250,
        max_mana=310,
        position=6,
        room_name="The Trail to Miden'nir",
        room_vnum="3505",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "cast 'chill touch' goblin"


@pytest.mark.parametrize(
    ("character_class", "subclass", "skills", "expected"),
    [
        ("cleric", "templar", {"cause light", "cause serious"}, "cause serious"),
        ("psionic", "witch", {"mind thrust", "psychic crush"}, "psychic crush"),
    ],
)
def test_caster_classes_use_strongest_known_automated_spell(
    character_class: str,
    subclass: str,
    skills: set[str],
    expected: str,
) -> None:
    policy = StarterPolicy(
        _spec(**{"class": character_class, "subclass": subclass}),
        "swordfish",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.active_target = "a wild boar"
    policy.known_skills.update(skills)
    state = CharacterState(
        level=5,
        hp=90,
        max_hp=100,
        mana=120,
        max_mana=150,
        position=6,
        room_name="The Mud School Arena",
        room_vnum="3730",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == f"cast '{expected}' boar"


def test_warrior_uses_kick_between_automatic_combat_rounds() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "warrior", "subclass": "knight"}),
        "swordfish",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.active_target = "a wild boar"
    policy.known_skills.add("kick")
    state = CharacterState(
        level=5,
        hp=100,
        max_hp=110,
        position=6,
        room_name="The Mud School Arena",
        room_vnum="3730",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "kick"
    assert "between automatic weapon rounds" in decision.reason


def test_warrior_does_not_use_kick_as_a_combat_opener() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "warrior", "subclass": "knight"}),
        "swordfish",
    )
    policy.known_skills.add("kick")

    decision = policy._combat_opener_decision(
        "a wild boar",
        "fight arena opponent a wild boar",
    )

    assert decision.command == "kill boar"


def test_thief_opens_with_backstab_only_with_a_verified_piercing_weapon() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
    )
    policy.known_skills.add("backstab")
    policy.gear_worn = [
        ObjectSource(
            3701,
            "jewel-studded dagger",
            "a jewel-studded dagger",
            5,
            (0, 2, 3, 11),
            5,
            wear_flags=1 << 13,
        )
    ]

    decision = policy._combat_opener_decision(
        "a wild boar",
        "fight arena opponent a wild boar",
    )

    assert decision.command == "backstab boar"
    assert "piercing weapon" in decision.reason


def test_rejected_backstab_falls_back_to_normal_attack_once() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
    )
    policy.known_skills.add("backstab")
    policy.gear_worn = [
        ObjectSource(
            3701,
            "jewel-studded dagger",
            "a jewel-studded dagger",
            5,
            (0, 2, 3, 11),
            5,
            wear_flags=1 << 13,
        )
    ]
    policy._combat_opener_decision("a wolf", "fight arena opponent a wolf")

    policy.observe_text("A wolf is hurt and suspicious... you can't sneak up on him.\n")
    decision = policy._combat_opener_decision(
        "a wolf",
        "fight arena opponent a wolf",
    )

    assert decision.command == "kill wolf"
    assert policy.backstab_pending_target is None


def test_enemy_snapshot_clears_successful_backstab_pending_marker() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
    )
    policy.backstab_pending_target = "a wolf"
    state = CharacterState()

    policy.observe_events(
        [
            GameEvent(
                "enemies_changed",
                "gmcp",
                {"value": [[{"name": "a wolf", "level": "4"}]]},
            )
        ],
        state,
    )

    assert policy.backstab_pending_target is None
    assert policy.combat_active is True


def test_enemy_snapshot_collapses_exact_duplicate_gmcp_rows() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    state = CharacterState()
    enemy = {
        "name": "the orc",
        "level": "6",
        "hp": "34",
        "maxhp": "81",
        "isnpc": "4004",
    }

    policy.observe_events(
        [GameEvent("enemies_changed", "gmcp", {"value": [[enemy, enemy.copy()]]})],
        state,
    )

    assert policy.active_enemy_count == 1


def test_enemy_snapshot_preserves_distinct_same_vnum_attackers() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    state = CharacterState()

    policy.observe_events(
        [
            GameEvent(
                "enemies_changed",
                "gmcp",
                {
                    "value": [[
                        {
                            "name": "the orc",
                            "level": "6",
                            "hp": "34",
                            "maxhp": "81",
                            "isnpc": "4004",
                        },
                        {
                            "name": "the orc",
                            "level": "6",
                            "hp": "81",
                            "maxhp": "81",
                            "isnpc": "4004",
                        },
                    ]]
                },
            )
        ],
        state,
    )

    assert policy.active_enemy_count == 2


def test_level_eight_mage_keeps_magic_missile_until_offense_training() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=9)
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.active_target = "a mountain goblin"
    state = CharacterState(
        level=8,
        hp=105,
        max_hp=110,
        mana=250,
        max_mana=310,
        position=6,
        room_name="The Trail to Miden'nir",
        room_vnum="3505",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "cast 'magic missile' goblin"


def test_level_nine_mage_falls_back_when_chill_touch_is_unknown() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=9)
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.active_target = "a mountain goblin"
    policy.between_round_action_issued = True
    state = CharacterState(
        level=9,
        hp=105,
        max_hp=110,
        mana=250,
        max_mana=310,
        position=6,
        room_name="The Trail to Miden'nir",
        room_vnum="3505",
    )

    policy.observe_text("You don't know any spells of that name.\n")
    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "cast 'magic missile' goblin"


def test_reconnected_arena_session_refreshes_known_skills_before_combat() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=6)
    policy.in_world = True
    policy.login_authenticated = True
    policy.prompt_ready = True
    state = CharacterState(
        level=5,
        hp=90,
        max_hp=90,
        mana=245,
        max_mana=245,
        room_name="The Mud School Arena",
        room_vnum="3732",
    )

    audit = policy.next_decision(state)

    assert audit is not None
    assert audit.command == "practice"
    assert "refresh known combat capabilities" in audit.reason
    policy.after_command(audit)
    policy.observe_text(
        """
Skills known:
                 magic missile:  46%                   chill touch:  23%
You have 2 physical and 2 intellectual practices remaining.
"""
    )
    policy.prompt_ready = True
    next_decision = policy.next_decision(state)

    assert policy.capability_audit_complete is True
    assert {"magic missile", "chill touch"} <= policy.known_skills
    assert next_decision is not None
    assert next_decision.command == "look imp"


def test_reconnected_field_session_refreshes_known_skills_before_travel() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "warrior", "subclass": "knight"}),
        "swordfish",
        objective_level=7,
        fastwalk_route=route_named("foundry"),
        fastwalk_hunt_stops=foundry_level_six_hunt_stops(),
    )
    policy.in_world = True
    policy.login_authenticated = True
    policy.prompt_ready = True
    state = CharacterState(
        level=6,
        hp=120,
        max_hp=120,
        mana=100,
        max_mana=100,
        move=200,
        max_move=200,
        room_name="The Temple Of Midgaard",
        room_vnum="3001",
    )

    audit = policy.next_decision(state)

    assert audit is not None
    assert audit.command == "practice"
    assert "field decisions" in audit.reason
    policy.after_command(audit)
    policy.observe_text(
        """
Skills known:
                 second attack:  43%                           kick:  31%
You have 1 physical and 0 intellectual practices remaining.
"""
    )
    policy.prompt_ready = True
    next_decision = policy.next_decision(state)

    assert policy.capability_audit_complete is True
    assert {"second attack", "kick"} <= policy.known_skills
    assert next_decision is not None
    assert next_decision.command == "config +autoloot"


def test_reconnected_capability_audit_cannot_wait_past_prompt() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=6)
    policy.in_world = True
    policy.login_authenticated = True
    policy.prompt_ready = True
    state = CharacterState(
        level=5,
        hp=90,
        max_hp=90,
        room_name="The Mud School Arena",
        room_vnum="3732",
    )
    audit = policy.next_decision(state)
    assert audit is not None

    policy.observe_events([GameEvent("prompt_seen", "text", {})], state)

    assert policy.capability_audit_pending is False
    assert policy.capability_audit_complete is True


def test_late_skill_listing_survives_prompt_before_audit_response() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=6)
    policy.in_world = True
    policy.login_authenticated = True
    policy.prompt_ready = True
    state = CharacterState(
        level=5,
        hp=90,
        max_hp=90,
        room_name="The Mud School Arena",
        room_vnum="3732",
    )
    audit = policy.next_decision(state)
    assert audit is not None

    policy.observe_events([GameEvent("prompt_seen", "text", {})], state)
    policy.observe_text(
        """
Skills known:
                 magic missile:  46%                   chill touch:  23%
You have 2 physical and 2 intellectual practices remaining.
"""
    )

    assert {"magic missile", "chill touch"} <= policy.known_skills


def test_combat_disarm_recovers_and_rearms_audited_weapon() -> None:
    dagger = ObjectSource(
        3020,
        "dagger",
        "a dagger",
        5,
        (0, 2, 4, 11),
        10,
        wear_flags=1 | (1 << 13),
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        gear_catalog=GearCatalog({dagger.vnum: dagger}),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.fastwalk_attack_started = True
    policy.active_target = "The war dog"
    policy.gear_worn = [dagger]
    state = CharacterState(
        level=9,
        hp=120,
        max_hp=126,
        mana=300,
        max_mana=343,
        position=6,
        room_name="In a forest clearing",
        room_vnum="4505",
    )

    policy.observe_text("The war dog DISARMS you!")
    recover = policy.next_decision(state)
    policy.prompt_ready = True
    rearm = policy.next_decision(state)

    assert recover is not None
    assert recover.command == "get dagger"
    assert rearm is not None
    assert rearm.command == "wield dagger"


def test_poison_strength_weapon_slip_is_persisted_until_rearmed() -> None:
    rod = ObjectSource(
        3021,
        "spiked metal rod",
        "a spiked metal rod",
        5,
        (0, 2, 4, 11),
        10,
        wear_flags=1 | (1 << 13),
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("moria"),
        gear_catalog=GearCatalog({rod.vnum: rod}),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.fastwalk_attack_started = True
    policy.active_target = "the garter snake"
    policy.gear_worn = [rod]
    state = CharacterState(
        level=7,
        hp=119,
        max_hp=123,
        mana=145,
        max_mana=145,
        position=6,
        room_name="The cave",
        room_vnum="4025",
    )

    policy.observe_text(
        "A spiked metal rod is too heavy for you to hold!\n"
        "Your weapon slips from your hand."
    )
    recover = policy.next_decision(state)

    assert policy.primary_weapon_lost is True
    assert recover is not None
    assert recover.command == "get spiked"

    policy.observe_text("You wield a spiked metal rod.")

    assert policy.primary_weapon_lost is False


def test_combat_disarm_recovers_unknown_weapon_without_fleeing() -> None:
    dagger = ObjectSource(
        3020,
        "dagger",
        "a dagger",
        5,
        (0, 2, 4, 11),
        10,
        wear_flags=1 | (1 << 13),
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_hunt_stops=foundry_level_six_hunt_stops(),
        gear_catalog=GearCatalog({dagger.vnum: dagger}),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.fastwalk_attack_started = True
    policy.active_target = "Uburz"
    fighting = CharacterState(
        level=6,
        hp=111,
        max_hp=111,
        mana=138,
        max_mana=138,
        position=6,
        room_name="Muddy Tunnel",
        room_vnum="117",
    )

    policy.observe_text("Uburz DISARMS you!")
    recover = policy.next_decision(fighting)

    assert recover is not None
    assert recover.command == "get all"
    assert policy.fastwalk_emergency_recall_pending is False
    policy.prompt_ready = True
    rearm = policy.next_decision(
        CharacterState(
            level=6,
            hp=111,
            max_hp=111,
            mana=138,
            max_mana=138,
            position=6,
            room_name="Muddy Tunnel",
            room_vnum="117",
            inventory=[[{"short_desc": "a dagger", "quan": "1"}]],
        )
    )

    assert rearm is not None
    assert rearm.command == "wield dagger"


def test_city_rearm_buys_verifies_and_returns_with_source_dagger() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_rearm=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.city_rearm_route_index = 6
    shop = CharacterState(
        room_name="The Weapon Shop",
        room_vnum="3011",
        position=7,
    )

    buy = policy.next_decision(shop)
    policy.prompt_ready = True
    wield = policy.next_decision(shop)
    policy.prompt_ready = True
    audit = policy.next_decision(shop)
    policy.observe_text("[weapon] a dagger")
    policy.prompt_ready = True
    return_move = policy.next_decision(shop)

    assert buy is not None
    assert buy.command == "buy dagger"
    assert wield is not None
    assert wield.command == "wield dagger"
    assert audit is not None
    assert audit.command == "equipment"
    assert return_move is not None
    assert return_move.command == "south"


def test_city_rearm_resumes_from_weapon_shop_when_dagger_is_already_wielded() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_rearm=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.gear_worn = [
        ObjectSource(
            3020,
            "dagger",
            "a dagger",
            5,
            (0, 2, 4, 11),
            10,
            wear_flags=1 | (1 << 13),
        )
    ]
    shop = CharacterState(
        room_name="The Weapon Shop",
        room_vnum="3011",
        position=7,
    )

    decision = policy.next_decision(shop)

    assert decision is not None
    assert decision.command == "south"


def test_city_rearm_departs_from_and_returns_to_midgaard_healer() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_rearm=True)
    policy.in_world = True
    policy.prompt_ready = True
    healer = CharacterState(
        room_name="By the Temple Altar",
        room_vnum="3054",
        position=7,
        stats={"carry_wt": 90, "maxcarry_wt": 100},
    )

    departure = policy._city_rearm_decision(healer)

    assert departure is not None
    assert departure.command == "south"

    policy.city_rearm_returning = True
    policy.city_rearm_route_index = 6

    assert policy._city_rearm_decision(healer) is None
    assert policy.failure is None


def test_city_rearm_donates_carried_gear_when_one_pound_will_not_fit() -> None:
    buckler = ObjectSource(
        9010,
        "metal buckler",
        "a metal buckler",
        9,
        (3, 0, 0, 0),
        20,
        wear_flags=1 | (1 << 9),
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        city_rearm=True,
        gear_catalog=GearCatalog({buckler.vnum: buckler}),
    )
    policy.in_world = True
    policy.prompt_ready = True
    full = CharacterState(
        room_name="By the Temple Altar",
        room_vnum="3054",
        position=7,
        inventory=[[{"short_desc": "a metal buckler", "quan": "1"}]],
        stats={"carry_wt": 102, "maxcarry_wt": 100},
    )

    donation = policy._city_rearm_decision(full)

    assert donation is not None
    assert donation.command == "donate buckler"

    freed = CharacterState(
        room_name="By the Temple Altar",
        room_vnum="3054",
        position=7,
        inventory=[[]],
        stats={"carry_wt": 99, "maxcarry_wt": 100},
    )

    departure = policy._city_rearm_decision(freed)

    assert departure is not None
    assert departure.command == "south"


def test_city_rearm_stops_after_shop_rejects_purchase_weight() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_rearm=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.city_rearm_route_index = 6
    policy.city_rearm_capacity_checked = True
    shop = CharacterState(
        room_name="The Weapon Shop",
        room_vnum="3011",
        position=7,
    )

    buy = policy._city_rearm_decision(shop)
    policy.observe_text("You can't carry that much weight.")
    after_rejection = policy._city_rearm_decision(shop)

    assert buy is not None
    assert buy.command == "buy dagger"
    assert after_rejection is None
    assert policy.failure == "insufficient carry capacity for the source-backed dagger"


def test_mage_casts_again_after_the_server_confirms_the_previous_volley() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=7)
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.active_target = "a prowling wolf"
    policy.between_round_action_issued = True
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


def test_mage_casts_again_after_the_previous_spell_misses() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_attack_target="Olog",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_attack_started = True
    policy.combat_active = True
    policy.active_target = "Olog"
    policy.between_round_action_issued = True
    state = CharacterState(
        hp=90,
        max_hp=100,
        mana=200,
        max_mana=240,
        position=6,
        room_name="Muddy Tunnel",
        room_vnum="108",
    )

    policy.observe_text("Your spell misses Olog.\n")
    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "cast 'magic missile' Olog"


def test_pending_flee_suppresses_a_late_spell_response() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(FieldHuntStop((), "war dog"),),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.fastwalk_attack_started = True
    policy.active_target = "The war dog"
    policy.flee_pending = True
    state = CharacterState(
        level=8,
        hp=75,
        max_hp=115,
        mana=281,
        max_mana=316,
        position=6,
        room_name="In a forest clearing",
        room_vnum="4505",
        enemies=[[
            {
                "name": "The war dog",
                "level": "7",
                "hp": "40",
                "maxhp": "80",
            }
        ]],
    )

    policy.observe_text(
        "You launch a volley of 4 magic missiles at The war dog!\n"
        "Your spell grazes The war dog.\n"
    )
    decision = policy.next_decision(state)

    assert decision is None
    assert policy.flee_pending is True


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


class _SilentConnection:
    def __init__(self) -> None:
        self.closed = False

    async def connect(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True

    async def send_command(self, command: str) -> None:
        return None

    async def read_available(self, timeout: float = 0.25) -> ReadResult:
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


def test_starter_runner_reconnects_after_silent_connection_timeout(
    tmp_path,
    monkeypatch,
) -> None:
    connections: list[_SilentConnection] = []

    def connection_factory(_spec):
        connection = _SilentConnection()
        connections.append(connection)
        return connection

    async def skip_sleep(_seconds: float) -> None:
        return None

    spec = _spec(
        password_env="STARTER_TEST_PASSWORD",
        max_commands=20,
        max_runtime=2,
        database=str(tmp_path / "runs.sqlite3"),
        transcript_dir=str(tmp_path / "transcripts"),
    )
    monkeypatch.setenv("STARTER_TEST_PASSWORD", "not-for-transcripts")
    monkeypatch.setattr("dd4tester.starter.asyncio.sleep", skip_sleep)
    runner = StarterBotRunner(
        spec,
        tmp_path / "starter.yaml",
        connection_factory=connection_factory,
        inactivity_timeout=0.0001,
    )

    with pytest.raises(ConnectionError, match="reconnect limit"):
        asyncio.run(runner.run())

    transcript = next((tmp_path / "transcripts").glob("*.jsonl")).read_text(
        encoding="utf-8"
    )
    assert len(connections) == 4
    assert "connection_inactivity_timeout" in transcript


def test_starter_runner_accepts_safe_withdrawal_after_reaching_objective(
    tmp_path,
) -> None:
    spec = _spec(
        database=str(tmp_path / "runs.sqlite3"),
        transcript_dir=str(tmp_path / "transcripts"),
    )
    runner = StarterBotRunner(
        spec,
        tmp_path / "starter.yaml",
        objective_level=8,
    )

    runner.character_state.level = 7
    assert runner._fastwalk_abort_is_failure(
        "field combat aborted for safety: health at or below 70%"
    )

    runner.character_state.level = 8
    assert not runner._fastwalk_abort_is_failure(
        "field combat aborted for safety: health at or below 70%"
    )


def _gear_item(
    vnum: int,
    keywords: str,
    description: str,
    *affects: tuple[int, int],
) -> ObjectSource:
    return ObjectSource(
        vnum,
        keywords,
        description,
        9,
        (1, 0, 0, 0),
        100,
        wear_flags=1 | (1 << 4),
        affects=affects,
    )


def test_recovery_gear_is_equipped_before_sleeping() -> None:
    recovery = _gear_item(
        9001,
        "circlet recovery",
        "a recovery circlet",
        (12, 20),
        (13, 15),
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        gear_catalog=GearCatalog({recovery.vnum: recovery}),
    )
    policy.in_world = True
    state = CharacterState(
        level=6,
        hp=50,
        max_hp=100,
        mana=50,
        max_mana=200,
        move=100,
        max_move=200,
        position=7,
        room_name="The Altar of the Temple",
        room_vnum="3054",
        room_flags=["safe"],
        inventory=[[{"quan": "1", "short_desc": "a recovery circlet"}]],
    )

    policy.prompt_ready = True
    audit = policy.next_decision(state)
    assert audit is not None
    assert audit.command == "equipment"
    policy.after_command(audit)

    policy.observe_text("You are not using any equipment.")
    policy.prompt_ready = True
    equip = policy.next_decision(state)
    assert equip is not None
    assert equip.command == "wear circlet"
    policy.after_command(equip)

    state.inventory = [[]]
    policy.observe_text("You wear a recovery circlet on your head.")
    policy.prompt_ready = True
    confirm = policy.next_decision(state)
    assert confirm is not None
    assert confirm.command == "equipment"
    policy.after_command(confirm)

    policy.observe_text("<<worn on head>      a recovery circlet")
    policy.prompt_ready = True
    sleep = policy.next_decision(state)
    assert sleep is not None
    assert sleep.command == "sleep"


def test_sleep_waits_for_server_confirmation_before_queued_gear_commands() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        gear_catalog=GearCatalog({}),
    )
    policy.in_world = True
    policy.gear_command_queue = [
        ("remove collar", "switch away from combat gear"),
    ]
    awake = CharacterState(
        hp=100,
        max_hp=100,
        mana=100,
        max_mana=100,
        move=50,
        max_move=100,
        position=7,
        room_name="Mage's Laboratory",
        room_vnum="3019",
        room_flags=["safe"],
    )
    sleep = BotDecision("sleep", "recover movement in a safe room")

    policy.after_command(sleep)
    policy.prompt_ready = True
    assert policy.next_decision(awake) is None
    assert policy.sleep_confirmation_pending is True

    sleeping = CharacterState(
        hp=100,
        max_hp=100,
        mana=100,
        max_mana=100,
        move=50,
        max_move=100,
        position=4,
        room_name="Mage's Laboratory",
        room_vnum="3019",
        room_flags=["safe"],
    )
    policy.prompt_ready = True
    decision = policy.next_decision(sleeping)

    assert decision is not None
    assert decision.command == "stand"
    assert policy.gear_command_queue == [
        ("remove collar", "switch away from combat gear"),
    ]
    policy.after_command(decision)
    policy.observe_text("You wake and ready yourself for action.")
    assert policy.sleep_confirmation_pending is False
    assert policy.sleep_gear_locked is False


def test_rejected_sleep_clears_recovery_lock_and_resumes_combat() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.waiting_for_heal = True
    policy.active_target = "a wild boar"
    policy.after_command(BotDecision("sleep", "recover in a safe room"))

    policy.observe_text("Not while you are fighting!")

    assert policy.sleep_confirmation_pending is False
    assert policy.sleep_gear_locked is False
    assert policy.waiting_for_heal is False
    assert policy.health_check_due is None
    assert policy.combat_active is True


def test_equipment_audit_retries_when_hunger_tick_replaces_response() -> None:
    recovery = _gear_item(
        9001,
        "circlet recovery",
        "a recovery circlet",
        (12, 20),
        (13, 15),
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        gear_catalog=GearCatalog({recovery.vnum: recovery}),
    )
    policy.in_world = True
    state = CharacterState(
        level=6,
        hp=96,
        max_hp=96,
        mana=268,
        max_mana=268,
        move=200,
        max_move=200,
        position=7,
        room_name="General Supplies",
        room_vnum="3724",
        room_flags=["safe"],
        inventory=[[{"short_desc": "a buffalo water skin"}]],
    )

    policy.prompt_ready = True
    audit = policy.next_decision(state)
    assert audit is not None
    assert audit.command == "equipment"
    policy.after_command(audit)

    policy.observe_text("You're dying of hunger!")
    policy.prompt_ready = True
    retry = policy.next_decision(state)
    assert retry is not None
    assert retry.command == "equipment"
    assert "interrupted" in retry.reason


def test_gear_audit_waits_for_delayed_paper_doll_response() -> None:
    broadsword = ObjectSource(
        9001,
        "sharp steel broadsword",
        "a sharp steel broadsword",
        5,
        (0, 3, 6, 0),
        10,
        wear_flags=1 << 13,
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        gear_catalog=GearCatalog({broadsword.vnum: broadsword}),
    )
    policy.in_world = True
    policy.title_configured = True
    policy.prompt_ready = True
    state = CharacterState(
        level=7,
        hp=100,
        max_hp=100,
        mana=100,
        max_mana=100,
        move=100,
        max_move=100,
        position=7,
        room_name="By the Temple Altar",
        room_vnum="3054",
        room_flags=["safe", "healing"],
        inventory=[[{"short_desc": "a sharp steel broadsword"}]],
    )

    audit = policy.next_decision(state)
    assert audit is not None
    assert audit.command == "equipment"
    policy.after_command(audit)

    # DD4 can send the prior command's prompt before the equipment listing.
    policy.prompt_ready = True
    assert policy.next_decision(state) is None

    policy.observe_text("You are not using any equipment.")
    policy.prompt_ready = True
    wear = policy.next_decision(state)

    assert wear is not None
    assert wear.command == "wear broadsword"


def test_rejected_weapon_is_blacklisted_and_previous_weapon_is_rearmed() -> None:
    dagger = ObjectSource(
        3020,
        "dagger",
        "a dagger",
        5,
        (0, 1, 2, 0),
        10,
        wear_flags=1 << 13,
    )
    spear = ObjectSource(
        4801,
        "wooden spear lance",
        "a wooden spear",
        5,
        (0, 4, 4, 0),
        20,
        wear_flags=1 << 13,
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        gear_catalog=GearCatalog({dagger.vnum: dagger, spear.vnum: spear}),
    )
    policy.in_world = True
    policy.gear_audited = True
    policy.gear_worn = [dagger]
    state = CharacterState(
        level=9,
        hp=100,
        max_hp=100,
        mana=200,
        max_mana=200,
        move=200,
        max_move=200,
        position=7,
        room_name="In a forest clearing",
        room_vnum="4510",
        inventory=[[{"short_desc": "a wooden spear"}]],
    )

    remove = policy._gear_decision(state)
    assert remove is not None
    assert remove.command == "remove dagger"
    policy.after_command(remove)

    wear = policy._gear_decision(state)
    assert wear is not None
    assert wear.command == "wear spear"
    policy.after_command(wear)
    policy.observe_text("You cannot use lances.")

    state.inventory = [[
        {"short_desc": "a wooden spear"},
        {"short_desc": "a dagger"},
    ]]
    audit = policy._gear_decision(state)
    assert audit is not None
    assert audit.command == "equipment"

    policy.observe_text("You are not using any equipment.")
    rearm = policy._gear_decision(state)
    assert rearm is not None
    assert rearm.command == "wear dagger"
    assert policy.gear_unusable_keywords == {"spear"}


def test_profession_rejected_wear_is_blacklisted_without_retrying() -> None:
    policy = StarterPolicy(_spec(race="drow"), "swordfish")
    policy.gear_command_queue = [
        ("wear buckler", "equip combat gear: a metal buckler")
    ]
    policy.gear_audit_pending = True
    policy.gear_audited = True
    policy.gear_confirmation_required = True
    policy.gear_applied_stance = STANCE_COMBAT
    policy.after_command(
        BotDecision("wear buckler", "equip combat gear: a metal buckler")
    )

    policy.observe_text(
        "Your profession prohibits wearing anything in that location."
    )

    assert policy.gear_unusable_keywords == {"buckler"}
    assert policy.gear_pending_wear_keyword is None
    assert policy.gear_command_queue == []
    assert policy.gear_audit_pending is False
    assert policy.gear_audited is False
    assert policy.gear_confirmation_required is False
    assert policy.gear_applied_stance is None


def test_gear_stance_switches_to_stats_only_near_level_gain() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        gear_catalog=GearCatalog({}),
    )
    ordinary = CharacterState(
        xp_to_next_level=1200,
        progress={"xplvl": 4900},
        hp=100,
        max_hp=100,
        mana=200,
        max_mana=200,
        move=200,
        max_move=200,
    )
    near_level = CharacterState(
        xp_to_next_level=450,
        progress={"xplvl": 4900},
        hp=100,
        max_hp=100,
        mana=200,
        max_mana=200,
        move=200,
        max_move=200,
    )

    assert policy._desired_gear_stance(ordinary) == STANCE_COMBAT
    assert policy._desired_gear_stance(near_level) == STANCE_PRE_LEVEL
    policy.waiting_for_heal = True
    assert policy._desired_gear_stance(ordinary) == STANCE_RECOVERY


def test_field_hunt_keeps_recovery_gear_until_ninety_percent_move() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(FieldHuntStop((), "war dog"),),
    )
    healer = CharacterState(
        hp=115,
        max_hp=115,
        mana=316,
        max_mana=316,
        move=160,
        max_move=220,
        room_name="By the Temple Altar",
        room_vnum="3054",
        room_flags=["safe"],
    )

    assert policy._desired_gear_stance(healer) == STANCE_RECOVERY


def test_emergency_sale_protects_bonus_gear_and_capacity_items() -> None:
    damage = _gear_item(9001, "helm damage", "a damage helm", (19, 2))
    backpack = ObjectSource(
        9002,
        "backpack leather",
        "a leather backpack",
        15,
        (100, 1, 0, 0),
        20,
        wear_flags=1 | (1 << 3),
    )
    plain = _gear_item(9003, "helm plain", "a plain helm")
    catalog = GearCatalog(
        {item.vnum: item for item in (damage, backpack, plain)}
    )
    inventory = [[
        {"short_desc": "a damage helm"},
        {"short_desc": "a leather backpack"},
        {"short_desc": "a plain helm"},
    ]]

    assert _sellable_inventory_keyword(inventory, catalog) == "helm"


def test_sellable_inventory_uses_source_keyword_for_unfamiliar_equipment() -> None:
    jerkin = _gear_item(9004, "jerkin leather", "a leather jerkin")

    assert _sellable_inventory_keyword(
        [[{"short_desc": "a leather jerkin"}]],
        GearCatalog({jerkin.vnum: jerkin}),
    ) == "jerkin"


def test_sellable_inventory_schedules_carried_war_dog_collars_for_audit() -> None:
    one_collar = [[{"short_desc": "a war dog collar", "quan": "1"}]]

    assert _sellable_inventory_keyword(one_collar) == "collar"


def test_sellable_inventory_recognizes_plain_leg_guards() -> None:
    guards = [[{"short_desc": "some leather leg guards", "quan": "1"}]]

    assert _sellable_inventory_keyword(guards) == "guards"


def test_resupply_preserves_worn_armour_and_uses_emergency_credit() -> None:
    cloak = ObjectSource(
        9004,
        "dark blue cloak",
        "a dark-blue cloak",
        9,
        (2, 0, 0, 0),
        0,
        wear_flags=1 | (1 << 2),
    )
    diploma = ObjectSource(
        3715,
        "diploma",
        "a Mud School diploma",
        8,
        (0, 0, 0, 0),
        0,
        wear_flags=1 | (1 << 14),
        affects=((4, 1), (5, 1)),
    )
    catalog = GearCatalog({cloak.vnum: cloak, diploma.vnum: diploma})
    policy = StarterPolicy(_spec(), "swordfish", gear_catalog=catalog)
    policy.gear_worn = [cloak, cloak, diploma]
    policy.needs_food = True
    policy.insufficient_funds = True
    state = CharacterState(
        room_name="General Supplies",
        room_vnum="3724",
        position=7,
        inventory=[[{"short_desc": "a buffalo water skin"}]],
    )

    decision = policy._resupply_decision(state)

    assert decision is not None
    assert decision.command == "down"
    assert policy.gear_worn == [cloak, cloak, diploma]
    assert policy.emergency_sale_in_progress is False


def test_resupply_borrows_without_removing_the_only_stat_item_for_food() -> None:
    diploma = ObjectSource(
        3715,
        "diploma",
        "a Mud School diploma",
        8,
        (0, 0, 0, 0),
        0,
        wear_flags=1 | (1 << 14),
        affects=((4, 1), (5, 1)),
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        gear_catalog=GearCatalog({diploma.vnum: diploma}),
    )
    policy.gear_worn = [diploma]
    policy.needs_food = True
    policy.insufficient_funds = True
    state = CharacterState(
        room_name="General Supplies",
        room_vnum="3724",
        position=7,
        inventory=[[{"short_desc": "a buffalo water skin"}]],
    )

    decision = policy._resupply_decision(state)

    assert decision is not None
    assert decision.command == "down"
    assert policy.gear_worn == [diploma]


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


def test_absent_final_gladiator_saves_and_quits_for_reset_retry() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    state = CharacterState(
        hp=50,
        max_hp=50,
        room_name="Final Combat",
        room_vnum="3722",
        exits={"n": "3723", "s": "3716"},
    )

    assert policy._final_combat_decision(state).command == "look"
    assert policy._final_combat_decision(state).command == "save"
    assert "area-reset retry" in str(policy.utility_abort_reason)
    assert policy._final_combat_decision(state).command == "quit"
