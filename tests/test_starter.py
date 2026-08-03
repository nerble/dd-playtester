import asyncio
import time
from dataclasses import replace
from pathlib import Path

import pytest

from dd4tester import starter
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
from dd4tester.hunt_candidates import parse_area_file
from dd4tester.mudlet import MudletConnection
from dd4tester.observations import GameEvent, ObservationParser
from dd4tester.shops import safe_shop_for_item
from dd4tester.starter import (
    BotDecision,
    FieldHuntStop,
    StarterBotRunner,
    StarterPolicy,
    _equipment_empty_categories,
    _equipment_slot_categories,
    _capacity_relief_inventory_keyword,
    _emergency_provision_potion_keyword,
    _has_named_affect,
    _inventory_descriptions,
    _load_source_mobile_level_ranges,
    _load_source_mobile_targets,
    _max_consecutive_command,
    _practice_balances,
    _repeated_command_watchdog_applies,
    _room_mobile_target_counts,
    _room_mobile_target_selectors,
    _route_cycle_watchdog_applies,
    _sellable_inventory_keyword,
    _stop_target_matches,
    _training_target_counts,
    _where_location_from_response,
    _watchdog_progress_marker,
    _policy_inactivity_due,
    ambush_archer_hunt_stops,
    ambush_archer_research_stops,
    ambush_bardoosh_hunt_stops,
    ambush_exterior_hunt_stops,
    ambush_caster_level_eight_hunt_stops,
    ambush_level_seven_consider_stops,
    ambush_martial_level_eight_hunt_stops,
    ambush_raider_consider_stops,
    ambush_raider_hunt_stops,
    ambush_vile_goblin_hunt_stops,
    ambush_war_dog_collar_hunt_stops,
    argent_bandit_leader_hunt_stops,
    argent_bandit_leader_research_stops,
    circus_freak_show_hunt_stops,
    crystalmir_white_stag_hunt_stops,
    crystalmir_white_stag_research_stops,
    daycare_armed_guard_hunt_route,
    daycare_armed_guard_hunt_stops,
    daycare_nanny_hunt_route,
    daycare_nanny_hunt_stops,
    daycare_ring_hunt_stops,
    dwarven_home_chess_dwarf_hunt_stops,
    dwarven_home_chess_dwarf_research_stops,
    dwarven_home_gambler_hunt_stops,
    dwarven_home_gambler_research_stops,
    dwarven_home_master_hunt_stops,
    dwarven_home_master_research_stops,
    darkwood_strange_mist_hunt_stops,
    darkwood_strange_mist_research_stops,
    dwarven_nobleman_hunt_stops,
    dwarven_nobleman_research_stops,
    dwarven_worker_research_stops,
    foundry_body_gear_hunt_stops,
    foundry_set_circlet_hunt_stops,
    foundry_level_six_hunt_stops,
    foundry_level_seven_hunt_stops,
    forest_bear_claws_hunt_route,
    forest_bear_claws_hunt_stops,
    thalos_long_dagger_hunt_route,
    thalos_long_dagger_hunt_stops,
    vampire_hive_wounded_vampire_hunt_stops,
    vampire_hive_wounded_vampire_research_stops,
    tabernacle_hulking_beast_hunt_stops,
    tabernacle_hulking_beast_research_stops,
    galaxy_cancer_research_stops,
    galaxy_horsehead_nebula_hunt_stops,
    galaxy_horsehead_nebula_research_stops,
    galaxy_red_supergiant_hunt_stops,
    galaxy_red_supergiant_research_stops,
    galaxy_white_dwarf_secondary_hunt_stops,
    galaxy_white_dwarf_secondary_research_stops,
    galaxy_white_dwarf_hunt_stops,
    galaxy_white_dwarf_research_stops,
    hightower_jailor_hunt_stops,
    hightower_jailor_research_stops,
    fleshmonger_cook_hunt_stops,
    fleshmonger_cook_research_stops,
    fleshmonger_guard_circuit_research_stops,
    fleshmonger_guard_research_stops,
    fleshmonger_mufti_research_stops,
    fleshmonger_servant_hunt_stops,
    fleshmonger_servant_research_stops,
    fleshmonger_thief_extended_rotation_stops,
    fleshmonger_thief_rotation_research_stops,
    gnome_guard_hunt_stops,
    gnome_guard_research_stops,
    gnome_hermit_hunt_route,
    gnome_hermit_hunt_stops,
    gnome_treasurer_hunt_stops,
    gnome_treasurer_research_stops,
    ghost_town_crypt_thing_hunt_stops,
    ghost_town_crypt_thing_research_stops,
    ghost_town_retriever_hunt_stops,
    ghost_town_retriever_research_stops,
    mahntor_rock_toad_hunt_stops,
    mahntor_rock_toad_circuit_hunt_stops,
    mahntor_rock_toad_research_stops,
    midennir_mountain_goblin_hunt_stops,
    midennir_horseman_consider_stops,
    midennir_horseman_probe_route,
    mirror_realm_gardener_research_stops,
    mirror_realm_gardener_hunt_stops,
    mirror_realm_jerry_garcia_research_stops,
    mirror_realm_storn_hunt_stops,
    mirror_realm_storn_research_stops,
    moria_level_seven_orc_hunt_stops,
    moria_sanctuary_potion_consider_stops,
    moria_sanctuary_potion_hunt_stops,
    mirror_realm_watchman_research_stops,
    plains_aruncus_hunt_stops,
    plains_aruncus_research_stops,
    pirates_seas_rastafarians_hunt_stops,
    pirates_seas_rastafarians_research_stops,
    pyramid_ali_baba_hunt_stops,
    pyramid_ali_baba_research_stops,
    solace_lord_doom_hunt_stops,
    solace_lord_doom_research_stops,
    shire_bull_hunt_route,
    shire_bull_hunt_stops,
    shire_battle_master_research_stops,
    shire_dwarven_prince_hunt_stops,
    shire_dwarven_prince_research_stops,
    shire_elven_wizard_hunt_stops,
    shire_elven_wizard_research_stops,
    shire_thain_hunt_stops,
    shire_thain_research_stops,
    shire_mill_worker_consider_route,
    shire_mill_worker_consider_stops,
    shire_mill_worker_hunt_stops,
    gnome_small_troll_hunt_stops,
    highland_keeper_hunt_stops,
    highland_keeper_research_stops,
    shadow_keep_soldier_hunt_stops,
    shadow_keep_soldier_research_stops,
)

from dd4tester.state import CharacterState
from dd4tester.training import parse_practice_listing


def test_runtime_cap_error_is_distinct_from_other_timeouts() -> None:
    assert starter._is_runtime_cap_error(
        TimeoutError("Starter bot exceeded 180 second runtime")
    )
    assert not starter._is_runtime_cap_error(TimeoutError("socket read timed out"))
    assert not starter._is_runtime_cap_error(
        RuntimeError("Starter bot exceeded 180 second runtime")
    )


def test_bardoosh_hunt_is_exact_isolated_and_source_fuzz_bounded() -> None:
    (stop,) = ambush_bardoosh_hunt_stops()

    assert stop.target == "Bardoosh"
    assert stop.command_keyword == "bardoosh"
    assert stop.exact_target is True
    assert stop.consider_only is False
    assert stop.maximum_target_count == 1
    assert stop.minimum_health_ratio == 0.9
    assert stop.maximum_level_offset == 1
    assert stop.route[-1] == "west"
    assert stop.allowed_bystanders == ("wyvern",)
    assert stop.trivial_bystanders == ("goblin", "goblin lieutenant")


def test_dwarven_nobleman_probe_cannot_initiate_combat() -> None:
    (stop,) = dwarven_nobleman_research_stops()

    assert stop.target == "dwarven nobleman"
    assert stop.command_keyword == "nobleman"
    assert stop.consider_only is True
    assert stop.exact_target is True
    assert stop.route_vnums == ()
    assert stop.maximum_target_count == 1
    assert stop.abort_after_consider_rejection is True


def test_dwarven_nobleman_hunt_requires_full_health_and_bounds_live_level() -> None:
    (stop,) = dwarven_nobleman_hunt_stops()

    assert stop.target == "dwarven nobleman"
    assert stop.consider_only is False
    assert stop.exact_target is True
    assert stop.minimum_health_ratio == 0.90
    assert stop.maximum_level_offset == 1
    assert stop.maximum_target_count == 1
    assert stop.allowed_bystanders == ("maid",)
    assert stop.trivial_bystanders == ("mountain goblin",)


def test_pyramid_ali_baba_probe_and_hunt_are_bounded() -> None:
    research_stops = pyramid_ali_baba_research_stops()
    hunt_stops = pyramid_ali_baba_hunt_stops()
    research_stop = research_stops[0]
    hunt_stop = hunt_stops[0]

    assert research_stop.target == "Ali Baba"
    assert research_stop.command_keyword == "ali baba"
    assert research_stop.actions == ("where ali baba",)
    assert research_stop.consider_only is True
    assert research_stop.exact_target is True
    assert research_stop.require_isolated is True
    assert research_stop.abort_after_consider_rejection is True
    assert tuple(stop.route_vnums for stop in research_stops) == (
        (),
        ("2642",),
        ("2641",),
        ("2640",),
        ("2639",),
        ("2640", "2641", "2642", "2636"),
        ("2635",),
        ("2634",),
    )
    assert tuple(stop.route_vnums for stop in hunt_stops) == tuple(
        stop.route_vnums for stop in research_stops
    )
    assert hunt_stop.consider_only is False
    assert hunt_stop.minimum_health_ratio == 0.90
    assert hunt_stop.maximum_level_offset == 1


def test_solace_lord_doom_probe_and_hunt_allow_only_source_trivial_bystanders() -> None:
    research_stop = solace_lord_doom_research_stops()[0]
    hunt_stop = solace_lord_doom_hunt_stops()[0]

    assert research_stop.target == "Lord Doom"
    assert research_stop.command_keyword == "doom"
    assert research_stop.actions == ("where doom",)
    assert research_stop.abort_if_where_target_absent is True
    assert research_stop.consider_only is True
    assert research_stop.exact_target is True
    assert research_stop.require_isolated is True
    assert research_stop.maximum_level_offset == 2
    assert "a Giant Kodiak bear" in research_stop.trivial_bystanders
    assert hunt_stop.consider_only is False
    assert hunt_stop.minimum_health_ratio == 0.90
    assert hunt_stop.maximum_level_offset == 2


def test_pyramid_fastwalk_has_a_no_recall_return_to_the_healer() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("pyramid ali baba"),
        fastwalk_hunt_stops=pyramid_ali_baba_research_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_returning = True
    state = CharacterState(
        room_vnum="5027",
        room_name="The Great Eastern Desert",
        room_flags=["no_recall"],
        exits={"n": "5007", "e": "5028"},
    )

    assert policy._fastwalk_research_decision(state).command == "north"
    state.room_vnum = "5007"
    state.exits = {"w": "5006"}
    expected = (
        *("west",) * 9,
        *("north",) * 2,
        *("west",) * 2,
        *("north",) * 4,
    )
    actual = []
    for index, _command in enumerate(expected):
        decision = policy._fastwalk_research_decision(state)
        assert decision is not None
        actual.append(decision.command)
        state.room_vnum = "5000" if index < len(expected) - 1 else "3054"
        policy.prompt_ready = True

    assert tuple(actual) == expected
    assert policy._fastwalk_research_decision(state) is None


def test_shadow_grove_return_home_uses_live_maze_and_source_route() -> None:
    policy = StarterPolicy(_spec(), "swordfish", return_home=True)
    state = CharacterState(room_vnum="1305", exits={"e": "1308"})

    assert policy._return_home_decision(state).command == "east"
    state.room_vnum = "1308"
    state.exits = {"w": "1300"}
    assert policy._return_home_decision(state).command == "west"
    state.room_vnum = "1300"
    state.exits = {"s": "6137"}
    assert policy._return_home_decision(state).command == "south"

    source_route = (
        ("south", "6137"),
        ("east", "6136"),
        ("south", "6135"),
        ("east", "6129"),
        ("east", "6128"),
        ("east", "6126"),
        ("north", "6127"),
        ("east", "6112"),
        ("north", "6111"),
        ("north", "6110"),
        ("east", "6109"),
        ("east", "6108"),
        ("north", "6103"),
        ("east", "6102"),
        ("east", "6101"),
        ("east", "6100"),
        ("east", "6004"),
        ("east", "6003"),
        ("east", "6002"),
        ("east", "6001"),
        ("east", "6000"),
        ("east", "3052"),
        ("east", "3040"),
        ("east", "3012"),
        ("east", "3013"),
        ("east", "3014"),
        ("north", "3005"),
        ("north", "3001"),
        ("north", "3054"),
    )
    assert tuple(command for command, _ in source_route) == (
        "south",
        *starter._SHADOW_GROVE_HEALER_RETURN_COMMANDS[1:],
    )
    state.room_vnum = "6137"
    for command, destination in source_route[1:]:
        decision = policy._return_home_decision(state)
        assert decision is not None
        assert decision.command == command
        state.room_vnum = destination

    assert policy._return_home_decision(state) is None


def test_shadow_grove_fastwalk_return_uses_the_same_source_route() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("galaxy white dwarf"),
        fastwalk_hunt_stops=galaxy_white_dwarf_research_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_returning = True
    state = CharacterState(room_vnum="1305", exits={"e": "1308"})

    assert policy._fastwalk_research_decision(state).command == "east"
    state.room_vnum = "1308"
    state.exits = {"w": "1300"}
    assert policy._fastwalk_research_decision(state).command == "west"
    state.room_vnum = "1300"
    state.exits = {"s": "6137"}
    assert policy._fastwalk_research_decision(state).command == "south"


def test_pyramid_fastwalk_uses_live_exits_to_cross_the_randomized_desert() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("pyramid ali baba"),
        fastwalk_hunt_stops=pyramid_ali_baba_research_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = 16
    state = CharacterState(room_vnum="5007", exits={"e": "5027", "w": "5006"})

    live_steps = (
        ("east", "5027", {"n": "5025", "e": "5028", "w": "5007"}),
        ("north", "5025", {"e": "5056", "s": "5027"}),
        ("east", "5056", {"e": "2600", "w": "5025"}),
        ("east", "2600", {"e": "2601"}),
    )
    actual = []
    for expected_command, room_vnum, exits in live_steps:
        decision = policy._fastwalk_research_decision(state)
        assert decision is not None
        actual.append(decision.command)
        assert decision.command == expected_command
        state.room_vnum = room_vnum
        state.exits = exits
        policy.prompt_ready = True

    post_maze = policy._fastwalk_research_decision(state)
    assert post_maze is not None
    assert policy.fastwalk_outbound_index == 23
    assert post_maze.command == "east"

    state.room_vnum = "2601"
    state.exits = {"u": "2602"}
    policy.prompt_ready = True
    next_step = policy._fastwalk_research_decision(state)
    assert next_step is not None
    assert next_step.command == "up"
    assert policy.fastwalk_outbound_index == 24


def test_fastwalk_skips_a_route_waypoint_that_is_already_current_room() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_hunt_stops=(
            FieldHuntStop((), None, route_vnums=("2636",)),
        ),
    )
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        hp=100,
        max_hp=100,
        mana=100,
        max_mana=100,
        move=100,
        max_move=100,
        room_vnum="2636",
        exits={"n": "2642"},
    )

    decision = policy._fastwalk_hunt_plan_decision(state)

    assert decision is not None
    assert decision.command == "look"
    assert policy.fastwalk_hunt_move_index == 1
    assert policy.fastwalk_returning is False


def test_pyramid_live_maze_backtracks_using_parent_destination() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    allowed = frozenset({"5007", "5027", "5029", "5025"})
    state = CharacterState(room_vnum="5007", exits={"e": "5027"})

    assert policy._live_maze_navigation_decision(
        state,
        context="test-pyramid-maze",
        target="5025",
        allowed_rooms=allowed,
    ).command == "east"
    state.room_vnum = "5027"
    state.exits = {"e": "5029"}
    assert policy._live_maze_navigation_decision(
        state,
        context="test-pyramid-maze",
        target="5025",
        allowed_rooms=allowed,
    ).command == "east"
    state.room_vnum = "5029"
    state.exits = {"n": "5027"}
    assert policy._live_maze_navigation_decision(
        state,
        context="test-pyramid-maze",
        target="5025",
        allowed_rooms=allowed,
    ).command == "north"
    state.room_vnum = "5027"
    state.exits = {"e": "5029", "s": "5025"}
    assert policy._live_maze_navigation_decision(
        state,
        context="test-pyramid-maze",
        target="5025",
        allowed_rooms=allowed,
    ).command == "south"


def test_gnome_treasurer_probe_collects_only_source_keyed_coins() -> None:
    (stop,) = gnome_treasurer_research_stops()

    assert stop.target == "treasurer"
    assert stop.actions == ("get all.coins",)
    assert stop.consider_only is True
    assert stop.exact_target is True


def test_gnome_treasurer_hunt_is_isolated_and_bounded() -> None:
    (stop,) = gnome_treasurer_hunt_stops()

    assert stop.target == "treasurer"
    assert stop.actions == ("get all.coins",)
    assert stop.consider_only is False
    assert stop.minimum_health_ratio == 0.90
    assert stop.maximum_level_offset == 1


def test_bardoosh_hunt_finishes_lone_trivial_attacker_beside_wyvern() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=ambush_bardoosh_hunt_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.current_room = "3570"
    policy.combat_active = True
    policy.active_target = "the goblin lieutenant"
    policy.active_target_level = 7
    policy.active_enemy_count = 1
    policy.room_target_counts["3570"] = {
        "the wyvern": 1,
        "the goblin lieutenant": 1,
    }
    enemies = [[{"name": "the goblin lieutenant", "level": "7", "hp": "100"}]]
    state = CharacterState(
        level=13,
        hp=194,
        max_hp=194,
        mana=199,
        max_mana=199,
        room_name="South of the Inn",
        room_vnum="3570",
        position=6,
        enemies=enemies,
    )

    decision = policy.next_decision(state)

    assert decision is None
    assert policy.fastwalk_attack_started is True
    assert policy.fastwalk_attack_target == "the goblin lieutenant"
    assert policy.fastwalk_emergency_recall_pending is False
    assert policy.fastwalk_abort_reason is None


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


def test_configured_test_identity_is_applied_when_not_previously_recorded() -> None:
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
    description = policy.next_decision(state)
    assert description is not None
    assert description.command.startswith("description Rulemage is a human")
    policy.after_command(description)
    policy.prompt_ready = True
    assert policy.next_decision(state).command != description.command


def test_previously_recorded_identity_is_not_reapplied() -> None:
    policy = StarterPolicy(
        _spec(title="the Suspiciously Methodical"),
        "swordfish",
        title_configured=True,
        description_configured=True,
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
    assert not decision.command.startswith(("title ", "description "))


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


def test_level_seven_ambush_probe_considers_only_viable_targets() -> None:
    exterior = ambush_exterior_hunt_stops()
    stops = ambush_level_seven_consider_stops()

    assert [stop.target for stop in stops] == ["wounded goblin", "goblin looter"]
    assert all(stop.consider_only and stop.exact_target for stop in stops)
    assert stops[0].route == exterior[0].route
    assert stops[1].route == exterior[1].route + exterior[2].route + exterior[3].route


def test_circus_bearded_lady_route_stops_before_the_illusionist_tent() -> None:
    route = route_named("circus bearded lady")

    assert route.commands == (
        "south",
        "south",
        "east",
        "east",
        "east",
        "south",
        "south",
        "south",
        "south",
        "south",
        "south",
        "east",
        "east",
    )
    assert route.recall_after_loot is True


def test_circus_strongman_route_turns_south_at_the_freak_show_entrance() -> None:
    route = route_named("circus strongman")

    assert route.commands[-2:] == ("east", "south")
    assert len(route.commands) == 13
    assert route.recall_after_loot is True


def test_shire_watermill_probe_is_passive_and_recalls() -> None:
    route = shire_mill_worker_consider_route()
    stops = shire_mill_worker_consider_stops()

    assert route.commands == (
        "south", "south", "west", "west", "west", "west", "west",
        "north", "north", "north", "north", "west", "west", "west", "south",
    )
    assert route.recall_after_loot is True
    assert [stop.target for stop in stops] == ["mill worker"]
    assert stops[0].consider_only is True


def test_shire_watermill_hunt_keeps_high_health_and_one_worker_gates() -> None:
    stops = shire_mill_worker_hunt_stops()

    assert [stop.target for stop in stops] == ["mill worker"]
    assert stops[0].consider_only is False
    assert stops[0].allowed_bystanders == ("miller",)
    assert stops[0].minimum_health_ratio == 0.675
    assert stops[0].maximum_target_count == 1


def test_circus_hunt_sweeps_freak_show_and_ticketed_big_top() -> None:
    stops = circus_freak_show_hunt_stops()

    assert [stop.target for stop in stops] == [
        "Bearded Lady",
        "Illusionist",
        "Midget",
        "Ivan the Strongman",
        None,
        None,
        "Ringmaster",
    ]
    assert [stop.route for stop in stops] == [
        (),
        ("east",),
        ("south",),
        ("west", "west"),
        (),
        (),
        (),
    ]
    assert [stop.route_vnums for stop in stops[4:]] == [
        ("4408", "4406", "4403", "4402"),
        ("4403", "4406", "4414", "4415"),
        ("4416", "4419"),
    ]
    assert stops[0].allowed_bystanders == ()
    assert stops[1].allowed_bystanders == ()
    assert stops[1].trivial_bystanders == ("Beastly Fido",)
    assert stops[2].allowed_bystanders == ()
    assert stops[2].exact_target is True
    assert stops[3].allowed_bystanders == ("beastly fido",)
    assert stops[3].trivial_bystanders == ("Little Bobby", "Sword Swallower")
    assert stops[0].allow_local_recovery is True
    assert stops[1].allow_local_recovery is True
    assert stops[2].allow_local_recovery is True
    assert stops[3].minimum_health_ratio == 0.6
    assert stops[4].actions == ("buy ticket",)
    assert stops[4].required_items == ("ticket",)
    assert stops[5].actions == ("unlock south", "open south")
    assert stops[6].trivial_bystanders == ("member of the audience",)
    assert stops[6].exact_target is True


def test_level_eight_martial_ambush_circuit_prioritizes_three_loot_targets() -> None:
    stops = ambush_martial_level_eight_hunt_stops()

    assert [stop.target for stop in stops] == [
        "wounded goblin",
        "war dog",
        "goblin looter",
    ]
    assert all(stop.exact_target for stop in stops)
    assert stops[0].minimum_health_ratio == 0.675
    assert stops[1].minimum_health_ratio == 0.225
    assert stops[2].minimum_health_ratio == 0.225


def test_shire_watermill_hunt_skips_two_workers_before_combat() -> None:
    route = shire_mill_worker_consider_route()
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=shire_mill_worker_hunt_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    policy.fastwalk_hunt_looked = True
    policy.current_room = "1123"
    policy.room_targets["1123"] = ["miller", "mill worker"]
    policy.room_target_counts["1123"] = {"miller": 1, "mill worker": 2}
    state = CharacterState(
        level=7,
        hp=123,
        max_hp=123,
        mana=145,
        max_mana=145,
        move=192,
        max_move=210,
        position=7,
        room_name="Entrance to Watermill",
        room_vnum="1123",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "look"
    assert policy.fastwalk_hunt_stop_skipped is True
    assert policy.combat_active is False


def test_room_target_parser_recognizes_mobile_activity_text() -> None:
    assert _training_target_counts(
        "The mill worker runs to and fro.\n"
        "An ugly kobold mumbles something under its breath.\n"
        "The patrolling guard greets you as you enter the room.\n"
        "A dwarven mining worker is here.\n"
        "A pig wallows in the mud and oinks in contentment.\n"
    ) == {
        "mill worker": 1,
        "ugly kobold": 1,
        "patrolling guard": 1,
        "dwarven mining worker": 1,
    }


def test_affect_identity_does_not_confuse_detect_invis_with_invis() -> None:
    affects = [[{
        "name": "detect invis",
        "gives": "detect invisibility",
        "modifies": "none",
    }]]

    assert _has_named_affect(affects, "detect invis") is True
    assert _has_named_affect(affects, "invis") is False


def test_room_target_parser_ignores_circus_static_place_prose() -> None:
    assert _training_target_counts(
        "The place is deserted of spectators.\n"
        "The Bearded Lady is here.\n"
    ) == {"bearded lady": 1}


def test_room_target_parser_recognizes_proper_name_bystanders() -> None:
    assert _training_target_counts(
        "The Bearded Lady is here.\n"
        "Bobby's mother is here, frantically calling out her son's name.\n"
        "Beastly Fido is here wagging his tail.\n"
    ) == {
        "bearded lady": 1,
        "bobby's mother": 1,
        "beastly fido": 1,
    }


def test_room_target_parser_recognizes_ivan_the_strongman_live_text() -> None:
    assert _training_target_counts(
        "Ivan the Strongman poses for the crowd.\n"
    ) == {"ivan the strongman": 1}


def test_room_target_parser_recognizes_ambush_looter_activity_alias() -> None:
    assert _training_target_counts(
        "A corpse with arrows in it is here.\n"
        "A goblin is here, looting the dead.\n"
    ) == {"goblin looter": 1}


def test_circus_hunt_allows_safe_and_below_band_bystanders_beside_ivan() -> None:
    route = route_named("circus bearded lady")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=circus_freak_show_hunt_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    policy.fastwalk_hunt_stop_index = 3
    policy.fastwalk_hunt_move_index = 2
    policy.fastwalk_hunt_looked = True
    policy.current_room = "4413"
    policy.room_targets["4413"] = [
        "beastly fido",
        "little bobby",
        "sword swallower",
        "ivan the strongman",
    ]
    policy.room_target_counts["4413"] = {
        "beastly fido": 1,
        "little bobby": 1,
        "sword swallower": 1,
        "ivan the strongman": 1,
    }
    state = CharacterState(
        level=9,
        hp=110,
        max_hp=110,
        mana=297,
        max_mana=297,
        move=163,
        max_move=210,
        position=7,
        room_name="The Strongman's Tent",
        room_vnum="4413",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "consider Strongman"

    policy.room_targets["4413"].append("animal keeper")
    policy.room_target_counts["4413"]["animal keeper"] = 1
    policy.consider_target = None
    policy.consider_viable = None
    policy.prompt_ready = True
    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "look"
    assert policy.fastwalk_hunt_stop_skipped is True


def test_circus_hunt_does_not_let_level_zero_fido_block_illusionist() -> None:
    route = route_named("circus bearded lady")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=circus_freak_show_hunt_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    policy.fastwalk_hunt_stop_index = 1
    policy.fastwalk_hunt_move_index = 1
    policy.fastwalk_hunt_looked = True
    policy.current_room = "4410"
    policy.room_targets["4410"] = ["beastly fido", "illusionist"]
    policy.room_target_counts["4410"] = {
        "beastly fido": 1,
        "illusionist": 1,
    }

    decision = policy.next_decision(
        CharacterState(
            level=9,
            hp=197,
            max_hp=197,
            mana=146,
            max_mana=146,
            move=215,
            max_move=230,
            position=7,
            room_name="The Tent of the Illusionist",
            room_vnum="4410",
        )
    )

    assert decision is not None
    assert decision.command == "consider Illusionist"
    assert policy.fastwalk_hunt_stop_skipped is False


def test_circus_ticket_purchase_is_skipped_after_vault_claim() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("circus bearded lady"),
        fastwalk_hunt_stops=circus_freak_show_hunt_stops(),
    )
    policy.fastwalk_hunt_stop_index = 4
    policy.fastwalk_hunt_move_index = 4
    policy.fastwalk_hunt_looked = True
    policy.current_room = "4402"

    decision = policy._fastwalk_hunt_plan_decision(
        CharacterState(
            level=9,
            hp=197,
            max_hp=197,
            mana=146,
            max_mana=146,
            move=220,
            max_move=230,
            room_name="The Entrance to the Circus",
            room_vnum="4402",
            inventory=[[{"short_desc": "a ticket", "quan": "1"}]],
        )
    )

    assert decision is not None
    assert decision.command == "look"
    assert policy.fastwalk_hunt_action_index == 1
    assert policy.fastwalk_hunt_stop_skipped is True


def test_circus_ticket_purchase_becomes_visible_and_retries_without_recasting() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("circus bearded lady"),
        fastwalk_hunt_stops=circus_freak_show_hunt_stops(),
        fastwalk_require_invisibility=True,
    )
    policy.fastwalk_hunt_stop_index = 4
    policy.fastwalk_hunt_move_index = 4
    policy.fastwalk_hunt_looked = True
    state = CharacterState(
        level=8,
        hp=120,
        max_hp=120,
        mana=300,
        max_mana=323,
        move=180,
        max_move=220,
        room_name="The Entrance to the Circus",
        room_vnum="4402",
        affects=[[{"name": "invis", "gives": "invisibility"}]],
        inventory=[[]],
    )

    purchase = policy._fastwalk_hunt_plan_decision(state)
    assert purchase is not None
    assert purchase.command == "buy ticket"

    policy.observe_text(
        "The Ticket Clerk says 'I don't trade with folks I can't see.'"
    )
    visible = policy._fastwalk_hunt_plan_decision(state)
    assert visible is not None
    assert visible.command == "vis"

    state.affects = []
    retry = policy._fastwalk_hunt_plan_decision(state)
    assert retry is not None
    assert retry.command == "buy ticket"
    assert policy.fastwalk_shop_visible_action_pending is False


def test_room_description_prose_is_not_counted_as_a_visible_mobile() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.current_room = "4410"
    state = CharacterState(
        room_name="The Tent of the Illusionist",
        room_vnum="4410",
    )
    description = (
        "You turn, and see a very large, very evil looking creature. "
        "The Dragon snorts a cloud of smoke at you."
    )
    policy.observe_events(
        [
            GameEvent(
                "room_updated",
                "gmcp",
                {"description": description},
            )
        ],
        state,
    )

    policy.observe_text(
        f"{description}\n"
        "The Illusionist is here, doing tricks to amaze the crowd.\n"
    )

    assert policy.room_target_counts["4410"] == {"illusionist": 1}


def test_retired_foundry_level_six_template_keeps_the_historical_uburz_stop() -> None:
    stops = foundry_level_six_hunt_stops()

    assert [stop.target for stop in stops] == ["uburz"]
    assert stops[0].route == (
        "south",
        "south",
        "west",
        "west",
        "down",
        "east",
    )
    assert all(not stop.consider_only for stop in stops)
    assert stops[0].minimum_health_ratio == 0.225


def test_foundry_circlet_recovery_is_bounded_required_loot() -> None:
    stops = foundry_set_circlet_hunt_stops()

    assert len(stops) == 12
    assert all(stop.target == "uburz" for stop in stops)
    assert stops[-2].route == ("down",)
    assert stops[-1].route == ("east",)
    assert all(stop.required_items == ("silver circlet",) for stop in stops)
    assert all(
        stop.post_actions == ("wear circlet", "eq all")
        for stop in stops
    )
    assert all(stop.allow_below_band_for_required_loot for stop in stops)
    assert all(stop.exact_target for stop in stops)
    assert all("hoobuk" in stop.trivial_bystanders for stop in stops)


def test_dwarven_worker_probe_covers_complete_safe_wandering_range() -> None:
    research = dwarven_worker_research_stops()

    assert len(research) == 11
    assert [stop.route for stop in research[:4]] == [
        (),
        ("south",),
        ("north", "north"),
        ("north",),
    ]
    assert research[0].route_vnums == ()
    assert research[-1].route == ("west",)
    assert research[-1].route_vnums == ("6522",)
    assert all("6505" not in stop.route_vnums for stop in research)
    assert all(stop.target == "dwarven mining worker" for stop in research)
    assert all(stop.command_keyword == "worker" for stop in research)
    assert all(stop.consider_only for stop in research)
    assert all(stop.exact_target for stop in research)
    assert all(stop.maximum_target_count == 1 for stop in research)


def test_mahntor_rock_toad_probe_visits_all_four_reset_rooms_without_combat() -> None:
    stops = mahntor_rock_toad_research_stops()

    assert [stop.route for stop in stops] == [
        (),
        (),
        (),
        (),
    ]
    assert [stop.route_vnums for stop in stops] == [
        (),
        ("2313",),
        ("2311", "2310", "2312"),
        ("2315", "2319"),
    ]
    assert all(stop.target == "rather large rock toad" for stop in stops)
    assert all(stop.command_keyword == "toad" for stop in stops)
    assert all(stop.consider_only for stop in stops)
    assert all(stop.exact_target for stop in stops)
    assert all(stop.maximum_target_count == 1 for stop in stops)


def test_mahntor_rock_toad_hunt_is_one_strictly_bounded_target() -> None:
    (stop,) = mahntor_rock_toad_hunt_stops()

    assert stop.route == ()
    assert stop.target == "rather large rock toad"
    assert stop.consider_only is False
    assert stop.exact_target is True
    assert stop.maximum_target_count == 1
    assert stop.minimum_health_ratio == 0.90
    assert stop.maximum_level_offset == 1


def test_mahntor_rock_toad_circuit_retains_every_per_stop_gate() -> None:
    stops = mahntor_rock_toad_circuit_hunt_stops()

    assert len(stops) == 4
    assert [stop.route for stop in stops] == [
        (),
        (),
        (),
        (),
    ]
    assert [stop.minimum_health_ratio for stop in stops] == [
        0.675,
        0.225,
        0.225,
        0.225,
    ]
    assert all(not stop.consider_only for stop in stops)
    assert all(stop.exact_target for stop in stops)
    assert all(stop.maximum_target_count == 1 for stop in stops)
    assert all(stop.maximum_level_offset == 1 for stop in stops)


def test_same_target_circuit_routes_before_evaluating_next_stop() -> None:
    stops = mahntor_rock_toad_circuit_hunt_stops()
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("mahn tor rock toads"),
        fastwalk_hunt_stops=stops,
    )
    policy.fastwalk_hunt_stop_index = 2
    policy.fastwalk_hunt_stop_skipped = True
    policy.current_room = "2312"
    policy.room_targets["2312"] = [
        "rather large rock toad",
        "rather large rock toad",
    ]
    policy.room_target_counts["2312"] = {"rather large rock toad": 2}

    decision = policy._fastwalk_hunt_plan_decision(
        CharacterState(
            level=16,
            hp=233,
            max_hp=233,
            mana=228,
            max_mana=228,
            move=155,
            max_move=300,
            position=7,
            room_name="The sparse foothills",
            room_vnum="2312",
            exits={"s": "2315"},
        )
    )

    assert decision is not None
    assert decision.command == "south"
    assert policy.fastwalk_hunt_stop_index == 3
    assert policy.fastwalk_hunt_stop_skipped is False


def test_crowded_circuit_skip_does_not_report_an_expedition_abort() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("mahn tor rock toads"),
        fastwalk_hunt_stops=mahntor_rock_toad_circuit_hunt_stops(),
    )
    policy.current_room = "2311"
    policy.fastwalk_attack_target = "rather large rock toad"
    policy.room_targets["2311"] = [
        "rather large rock toad",
        "rather large rock toad",
    ]
    policy.room_target_counts["2311"] = {"rather large rock toad": 2}

    decision = policy._consider_fastwalk_target(
        CharacterState(
            level=16,
            hp=233,
            max_hp=233,
            mana=228,
            max_mana=228,
            move=155,
            max_move=300,
            position=7,
            room_name="The sparse foothills",
            room_vnum="2311",
        )
    )

    assert decision is not None
    assert decision.command == "look"
    assert policy.fastwalk_hunt_stop_skipped is True
    assert policy.fastwalk_abort_reason is None


def test_crowded_single_target_remains_retryable_research_evidence() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_hunt_stops=(
            FieldHuntStop((), "dwarven nobleman"),
        ),
    )
    policy.current_room = "20506"
    policy.fastwalk_attack_target = "dwarven nobleman"
    policy.room_targets["20506"] = [
        "dwarven nobleman",
        "house guest",
        "house guest",
        "house guest",
    ]
    policy.room_target_counts["20506"] = {
        "dwarven nobleman": 1,
        "house guest": 3,
    }

    decision = policy._consider_fastwalk_target(
        CharacterState(
            level=17,
            hp=242,
            max_hp=242,
            mana=235,
            max_mana=235,
            move=310,
            max_move=310,
            position=7,
            room_name="The nobleman's house",
            room_vnum="20506",
        )
    )

    assert decision is not None
    assert decision.command == "look"
    assert policy.fastwalk_hunt_stop_skipped is True
    assert policy.fastwalk_target_absent is False
    assert "contained 4 observed mobiles" in (policy.fastwalk_abort_reason or "")


def test_crowded_consider_only_probe_skips_before_considering() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_hunt_stops=(
            FieldHuntStop(
                (),
                "dwarven prince",
                consider_only=True,
                exact_target=True,
                require_isolated=True,
            ),
        ),
    )
    policy.current_room = "1136"
    policy.fastwalk_attack_target = "dwarven prince"
    policy.room_targets["1136"] = [
        "dwarven prince",
        "elven warrior",
        "halfling youth",
    ]
    policy.room_target_counts["1136"] = {
        "dwarven prince": 1,
        "elven warrior": 1,
        "halfling youth": 1,
    }

    decision = policy._consider_fastwalk_target(
        CharacterState(
            level=18,
            hp=254,
            max_hp=254,
            mana=242,
            max_mana=242,
            move=300,
            max_move=320,
            position=7,
            room_name="Bedroom",
            room_vnum="1136",
        )
    )

    assert decision is not None
    assert decision.command == "look"
    assert policy.fastwalk_hunt_stop_skipped is True
    assert policy.fastwalk_target_absent is False
    assert "contained 3 observed mobiles" in (policy.fastwalk_abort_reason or "")


def test_source_known_below_band_bystanders_do_not_block_wizard_hunt() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_hunt_stops=(
            FieldHuntStop(
                (),
                "elven wizard",
                command_keyword="wizard",
                exact_target=True,
                require_isolated=True,
            ),
        ),
        source_mobile_level_ranges={
            "elven wizard": (16, 20),
            "shiriff": (6, 10),
            "halfling beauty": (4, 8),
        },
    )
    policy.current_room = "1128"
    policy.fastwalk_attack_target = "elven wizard"
    policy.room_target_counts["1128"] = {
        "shiriff": 1,
        "elven wizard": 1,
        "halfling beauty": 1,
    }

    decision = policy._consider_fastwalk_target(
        CharacterState(
            level=18,
            hp=254,
            max_hp=254,
            mana=242,
            max_mana=242,
            move=303,
            max_move=320,
            position=7,
            room_name="A grassy field",
            room_vnum="1128",
        )
    )

    assert decision is not None
    assert decision.command == "consider wizard"
    assert policy.fastwalk_hunt_stop_skipped is False
    assert policy.fastwalk_abort_reason is None


def test_crowded_circuit_completion_does_not_mark_target_absent() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_hunt_stops=(FieldHuntStop((), "dwarven nobleman"),),
    )
    policy.fastwalk_hunt_stop_index = 1
    policy.fastwalk_abort_reason = (
        "field room contained 2 observed mobiles while evaluating "
        "'dwarven nobleman'"
    )

    decision = policy._fastwalk_hunt_plan_decision(
        CharacterState(
            level=17,
            hp=242,
            max_hp=242,
            mana=235,
            max_mana=235,
            move=310,
            max_move=310,
            position=7,
            room_name="The healer's room",
            room_vnum="3055",
        )
        )

    assert decision is not None
    assert decision.command == "recall"
    assert policy.fastwalk_target_absent is False


def test_retired_foundry_level_seven_template_excludes_pit_and_captain() -> None:
    stops = foundry_level_seven_hunt_stops()

    assert [stop.target for stop in stops] == [
        "golgog",
        "shargook",
        "lobuk",
        "uburz",
    ]
    assert all(stop.exact_target for stop in stops)
    assert stops[0].route == ("south", "south", "east")
    assert all("open east" not in stop.route for stop in stops)


def test_moria_level_seven_hunt_puts_poison_target_last() -> None:
    stops = moria_level_seven_orc_hunt_stops()

    assert [stop.target for stop in stops] == [
        "large orc",
        "large orc",
        "orc",
        "small green garter snake",
    ]
    assert stops[0].route == ("west", "west", "north", "west")
    assert stops[1].route == ("south",)
    assert stops[2].route == (
        "north", "east", "south", "east", "east", "east"
    )
    assert stops[2].allowed_bystanders == ("small green garter snake",)
    assert stops[3].route == ()
    assert stops[3].minimum_health_ratio == 0.675
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
    assert "abused and old doll" in stops[0].allowed_bystanders
    assert "abused and old doll" in stops[1].allowed_bystanders
    assert all(stop.exact_target for stop in stops)


def test_daycare_ring_recovery_allows_stationary_nanny_bystander() -> None:
    stops = daycare_ring_hunt_stops()
    doll_stops = stops[:4]

    assert all(
        "old wrinkled nanny" in stop.allowed_bystanders
        for stop in doll_stops
    )
    assert all(stop.allow_below_band_for_required_loot for stop in doll_stops)
    assert [stop.route for stop in doll_stops] == [
        ("west",),
        (),
        ("south",),
        (),
    ]
    assert all(
        stop.required_items == ("pink ice ring", "pink ice ring")
        for stop in doll_stops
    )
    assert stops[4].route == ("north", "east")


def test_war_dog_collar_recovery_uses_exact_required_loot_target() -> None:
    exterior = ambush_exterior_hunt_stops()
    (stop,) = ambush_war_dog_collar_hunt_stops()

    assert stop.route == exterior[0].route + exterior[1].route
    assert stop.target == "war dog"
    assert stop.post_actions == ("wear collar", "eq all")
    assert stop.required_items == ("war dog collar",)
    assert stop.exact_target is True
    assert stop.allow_below_band_for_required_loot is True


def test_forest_bear_claws_upgrade_uses_source_route_and_live_safety_gates() -> None:
    route = forest_bear_claws_hunt_route()
    stops = forest_bear_claws_hunt_stops()

    assert len(route.commands) == 42
    assert route.commands[:7] == (
        "south",
        "south",
        "south",
        "south",
        "south",
        "south",
        "west",
    )
    assert route.commands[17] == "open south"
    assert route.commands[-5:] == (
        "north",
        "north",
        "north",
        "west",
        "west",
    )
    assert route.recall_after_loot is True
    assert [stop.route_vnums for stop in stops[:5]] == [
        (),
        ("18025",),
        ("18023",),
        ("18024",),
        ("18023", "18022"),
    ]
    searched_vnums = {
        vnum for stop in stops for vnum in stop.route_vnums
    }
    assert {"18000", "18016", "18046", "18048", "18053", "18054"} <= (
        searched_vnums
    )
    assert searched_vnums.isdisjoint(
        {"18027", "18028", "18029", "18030", "18042"}
    )
    assert stops[-1].route_vnums == ("18053",)
    assert stops[0].actions == ("where kodiak",)
    assert stops[0].abort_if_where_target_absent is True
    assert stops[0].abort_if_where_room_names == (
        "River bed",
        "Medicine man's Lair",
    )
    assert all(stop.target == "giant kodiak bear" for stop in stops)
    assert all(stop.command_keyword == "bear" for stop in stops)
    assert all(
        stop.required_items == ("pair of bears claws",) for stop in stops
    )
    assert all(stop.maximum_target_count == 1 for stop in stops)
    assert all(stop.maximum_level_offset == 0 for stop in stops)
    assert all(stop.allowed_bystanders == ("small boy",) for stop in stops)
    assert all(
        stop.trivial_bystanders == ("mountain goblin",) for stop in stops
    )
    assert all(stop.allow_below_band_for_required_loot for stop in stops)


def test_thalos_dagger_upgrade_uses_isolated_reversible_carrier_routes() -> None:
    route = thalos_long_dagger_hunt_route()
    stops = thalos_long_dagger_hunt_stops()

    assert route.commands == route_named("thalos").commands
    assert route.recall_after_loot is True
    assert stops[0].actions == ("where lamia",)
    assert stops[0].abort_if_where_target_absent is True
    assert [stop.route_vnums[-1] for stop in stops[1:]] == [
        "5240",
        "5242",
        "5224",
        "5225",
        "5220",
        "5237",
        "5204",
        "5203",
        "5206",
        "5221",
        "5218",
        "5216",
        "5235",
        "5205",
    ]
    assert all("5236" not in stop.route_vnums for stop in stops)
    assert all(stop.target == "lamia" for stop in stops)
    assert all(stop.command_keyword == "lamia" for stop in stops)
    assert all(stop.required_items == ("long slim dagger",) for stop in stops)
    assert all(stop.post_actions == ("wear long", "eq all") for stop in stops)
    assert all(stop.maximum_target_count == 1 for stop in stops)
    assert all(stop.maximum_level_offset == 0 for stop in stops)
    assert all(stop.allow_below_band_for_required_loot for stop in stops)


def test_exhausted_absent_hunt_circuit_preserves_terminal_absence() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=forest_bear_claws_hunt_route(),
        fastwalk_hunt_stops=forest_bear_claws_hunt_stops()[:1],
    )
    policy.fastwalk_hunt_stop_skipped = True
    policy.fastwalk_target_absent = True
    state = CharacterState(
        level=14,
        hp=205,
        max_hp=205,
        mana=207,
        max_mana=207,
        move=200,
        max_move=280,
        room_vnum="18026",
        position=7,
    )

    decision = policy._fastwalk_hunt_plan_decision(state)

    assert decision is not None
    assert decision.command == "recall"
    assert policy.fastwalk_target_absent is True


def test_bear_claws_route_finishes_below_band_goblin_beside_small_boy() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=forest_bear_claws_hunt_route(),
        fastwalk_hunt_stops=forest_bear_claws_hunt_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.known_skills.add("chill touch")
    policy.current_room = "3575"
    policy.room_target_counts["3575"] = {
        "mountain goblin": 1,
        "small boy": 1,
    }
    policy.active_target = "the goblin"
    policy.active_target_level = 8
    state = CharacterState(
        level=13,
        hp=194,
        max_hp=194,
        mana=199,
        max_mana=199,
        room_name="The Ambush Point",
        room_vnum="3575",
        position=6,
        enemies=[[{"name": "the goblin", "level": "8", "hp": "86"}]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "cast 'chill touch' goblin"
    assert policy.fastwalk_attack_started is True
    assert policy.fastwalk_emergency_recall_pending is False
    assert policy.fastwalk_abort_reason is None


def test_nobleman_route_finishes_source_level_trivial_approach_interruptor() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("thalos"),
        fastwalk_hunt_stops=(
            FieldHuntStop(
                (),
                "dwarven nobleman",
                trivial_bystanders=("mountain goblin",),
            ),
        ),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.current_room = "3504"
    policy.room_target_counts["3504"] = {
        "goblin lieutenant": 1,
        "mountain goblin": 1,
    }
    policy.active_target = "the goblin lieutenant"
    policy.active_target_level = 7
    state = CharacterState(
        level=17,
        hp=242,
        max_hp=242,
        mana=235,
        max_mana=235,
        move=306,
        max_move=310,
        room_name="The South Bridge",
        room_vnum="3504",
        position=7,
        enemies=[[{"name": "the goblin lieutenant", "level": "7", "hp": "73"}]],
    )

    decision = policy.next_decision(state)

    assert policy.fastwalk_attack_started is True
    assert policy.fastwalk_emergency_recall_pending is False
    assert policy.fastwalk_abort_reason is None


def test_shire_battle_master_probe_uses_an_exact_no_combat_target() -> None:
    (stop,) = shire_battle_master_research_stops()

    assert stop.target == "the battle master"
    assert stop.command_keyword == "battle"
    assert stop.consider_only is True
    assert stop.exact_target is True
    assert stop.route_vnums == ("1117",)


def test_galaxy_cancer_probe_uses_an_exact_no_combat_target() -> None:
    (stop,) = galaxy_cancer_research_stops()

    assert stop.target == "Cancer"
    assert stop.command_keyword == "cancer"
    assert stop.consider_only is True
    assert stop.exact_target is True
    assert stop.route_vnums == ("9345",)


def test_mirror_realm_jerry_garcia_probe_uses_an_exact_no_combat_target() -> None:
    (stop,) = mirror_realm_jerry_garcia_research_stops()

    assert stop.target == "Jerry Garcia"
    assert stop.command_keyword == "jerry"
    assert stop.consider_only is True
    assert stop.exact_target is True
    assert stop.route_vnums == ("19170",)


def test_dwarven_home_chess_dwarf_probe_and_hunt_are_level_bounded() -> None:
    (research,) = dwarven_home_chess_dwarf_research_stops()
    (hunt,) = dwarven_home_chess_dwarf_hunt_stops()
    source_targets = _load_source_mobile_targets(
        str(Path("runs/dd4-source/server/area").resolve())
    )

    assert research.target == "dwarf"
    assert research.command_keyword == "dwarf"
    assert research.consider_only is True
    assert research.exact_target is True
    assert research.maximum_target_count == 1
    assert research.route_vnums == ("20530",)
    assert hunt.consider_only is False
    assert hunt.minimum_health_ratio == pytest.approx(0.85)
    assert hunt.maximum_level_offset == 1
    text = "[#20514] A dwarf sits here, putting a puzzle together.\n"
    assert _room_mobile_target_counts(text, source_targets) == {"dwarf": 1}
    assert _room_mobile_target_selectors(text, source_targets) == {
        "dwarf": ["#20514"]
    }
    assert _stop_target_matches("dwarf", research.target, research) is True


def test_mirror_realm_storn_probe_and_hunt_are_level_bounded() -> None:
    (research,) = mirror_realm_storn_research_stops()
    (hunt,) = mirror_realm_storn_hunt_stops()
    source_targets = _load_source_mobile_targets(
        str(Path("runs/dd4-source/server/area").resolve())
    )

    assert research.target == "storn the assassin"
    assert research.command_keyword == "storn"
    assert research.consider_only is True
    assert research.exact_target is True
    assert research.maximum_target_count == 1
    assert research.route_vnums == ("19114",)
    assert hunt.consider_only is False
    assert hunt.minimum_health_ratio == pytest.approx(0.85)
    assert hunt.maximum_level_offset == 1
    text = "[#19034] Storn the Assassin is here, practicing his backstab.\n"
    assert _room_mobile_target_counts(text, source_targets) == {
        "storn the assassin": 1
    }
    assert _room_mobile_target_selectors(text, source_targets) == {
        "storn the assassin": ["#19034"]
    }
    assert _stop_target_matches(
        "storn the assassin", research.target, research
    ) is True


def test_darkwood_strange_mist_probe_and_hunt_are_level_bounded() -> None:
    (research,) = darkwood_strange_mist_research_stops()
    (hunt,) = darkwood_strange_mist_hunt_stops()
    source_targets = _load_source_mobile_targets(
        str(Path("runs/dd4-source/server/area").resolve())
    )

    assert research.target == "strange mist"
    assert research.command_keyword == "mist"
    assert research.consider_only is True
    assert research.exact_target is True
    assert research.maximum_target_count == 1
    assert research.route_vnums == ("11211",)
    assert hunt.consider_only is False
    assert hunt.minimum_health_ratio == pytest.approx(0.85)
    assert hunt.maximum_level_offset == 1
    text = "[#11200] A figure forms out the mist.\n"
    assert _room_mobile_target_counts(text, source_targets) == {
        "strange mist": 1
    }
    assert _room_mobile_target_selectors(text, source_targets) == {
        "strange mist": ["#11200"]
    }
    assert _stop_target_matches("strange mist", research.target, research) is True


def test_dwarven_home_gambler_probe_and_hunt_are_level_bounded() -> None:
    (research,) = dwarven_home_gambler_research_stops()
    (hunt,) = dwarven_home_gambler_hunt_stops()
    source_targets = _load_source_mobile_targets(
        str(Path("runs/dd4-source/server/area").resolve())
    )

    assert research.target == "dwarf"
    assert research.command_keyword == "dwarf"
    assert research.consider_only is True
    assert research.exact_target is True
    assert research.maximum_target_count == 1
    assert research.route_vnums == ("20531",)
    assert hunt.consider_only is False
    assert hunt.minimum_health_ratio == pytest.approx(0.85)
    assert hunt.maximum_level_offset == 1
    text = "[#20515] A dwarf is standing here, gambling all of his money away.\n"
    assert _room_mobile_target_counts(text, source_targets) == {"dwarf": 1}
    assert _room_mobile_target_selectors(text, source_targets) == {
        "dwarf": ["#20515"]
    }
    assert _stop_target_matches("dwarf", research.target, research) is True


def test_dwarven_home_master_probe_and_hunt_are_level_bounded() -> None:
    (research,) = dwarven_home_master_research_stops()
    (hunt,) = dwarven_home_master_hunt_stops()
    source_targets = _load_source_mobile_targets(
        str(Path("runs/dd4-source/server/area").resolve())
    )

    assert research.target == "master of the house"
    assert research.command_keyword == "master"
    assert research.consider_only is True
    assert research.exact_target is True
    assert research.maximum_target_count == 1
    assert research.route_vnums == ("20537",)
    assert hunt.consider_only is False
    assert hunt.minimum_health_ratio == pytest.approx(0.85)
    assert hunt.maximum_level_offset == 1
    text = "[#20517] The master of the house stands here, watching over his home.\n"
    assert _room_mobile_target_counts(text, source_targets) == {
        "master of the house": 1
    }
    assert _room_mobile_target_selectors(text, source_targets) == {
        "master of the house": ["#20517"]
    }
    assert _stop_target_matches(
        "master of the house", research.target, research
    ) is True


def test_vampire_hive_wounded_vampire_probe_and_hunt_are_level_bounded() -> None:
    (research,) = vampire_hive_wounded_vampire_research_stops()
    (hunt,) = vampire_hive_wounded_vampire_hunt_stops()
    source_targets = _load_source_mobile_targets(
        str(Path("runs/dd4-source/server/area").resolve())
    )

    assert research.target == "wounded vampire"
    assert research.command_keyword == "vampire"
    assert research.actions == ("where vampire",)
    assert research.abort_if_where_target_absent is True
    assert research.consider_only is True
    assert research.exact_target is True
    assert research.maximum_target_count == 1
    assert research.route_vnums == ("25641",)
    assert hunt.consider_only is False
    assert hunt.minimum_health_ratio == pytest.approx(0.85)
    assert hunt.maximum_level_offset == 1
    text = (
        "[#25652] A young man wanders about the sewers looking confused and "
        "disorientated.\n"
    )
    assert _room_mobile_target_counts(text, source_targets) == {
        "wounded vampire": 1
    }
    assert _room_mobile_target_selectors(text, source_targets) == {
        "wounded vampire": ["#25652"]
    }
    assert _stop_target_matches(
        "wounded vampire", research.target, research
    ) is True


def test_tabernacle_hulking_beast_probe_and_hunt_are_level_bounded() -> None:
    (research,) = tabernacle_hulking_beast_research_stops()
    (hunt,) = tabernacle_hulking_beast_hunt_stops()
    source_targets = _load_source_mobile_targets(
        str(Path("runs/dd4-source/server/area").resolve())
    )

    assert research.target == "hulking beast"
    assert research.command_keyword == "beast"
    assert research.consider_only is True
    assert research.exact_target is True
    assert research.maximum_target_count == 1
    assert research.route_vnums == ("39016",)
    assert hunt.consider_only is False
    assert hunt.minimum_health_ratio == pytest.approx(0.85)
    assert hunt.maximum_level_offset == 1
    text = "[#39013] A hulking beast flees in terror.\n"
    assert _room_mobile_target_counts(text, source_targets) == {
        "hulking beast": 1
    }
    assert _room_mobile_target_selectors(text, source_targets) == {
        "hulking beast": ["#39013"]
    }
    assert _stop_target_matches(
        "hulking beast", research.target, research
    ) is True


def test_pirates_seas_rastafarians_probe_and_hunt_are_level_bounded() -> None:
    (research,) = pirates_seas_rastafarians_research_stops()
    (hunt,) = pirates_seas_rastafarians_hunt_stops()
    source_targets = _load_source_mobile_targets(
        str(Path("runs/dd4-source/server/area").resolve())
    )

    assert research.target == "rastafarians"
    assert research.command_keyword == "rastafarians"
    assert research.actions == ("where rastafarians",)
    assert research.abort_if_where_target_absent is True
    assert research.consider_only is True
    assert research.exact_target is True
    assert research.maximum_target_count == 1
    assert research.require_isolated is True
    assert research.route_vnums == ("17141",)
    assert hunt.consider_only is False
    assert hunt.minimum_health_ratio == pytest.approx(0.85)
    assert hunt.maximum_level_offset == 1
    text = "[#17099] The Rastafarians load up a huge bowl and\n"
    assert _room_mobile_target_counts(text, source_targets) == {
        "rastafarians": 1
    }
    assert _room_mobile_target_selectors(text, source_targets) == {
        "rastafarians": ["#17099"]
    }
    assert _stop_target_matches(
        "rastafarians", research.target, research
    ) is True


@pytest.mark.parametrize(
    (
        "research_factory",
        "hunt_factory",
        "target",
        "keyword",
        "room",
        "selector_text",
        "selector",
    ),
    [
        (
            ghost_town_crypt_thing_research_stops,
            ghost_town_crypt_thing_hunt_stops,
            "crypt thing",
            "crypt",
            "8850",
            "[#8809] a crypt thing\n",
            "#8809",
        ),
        (
            ghost_town_retriever_research_stops,
            ghost_town_retriever_hunt_stops,
            "retriever",
            "retriever",
            "8843",
            "[#8829] a retriever\n",
            "#8829",
        ),
    ],
)
def test_ghost_town_progression_stops_are_exact_and_level_bounded(
    research_factory,
    hunt_factory,
    target: str,
    keyword: str,
    room: str,
    selector_text: str,
    selector: str,
) -> None:
    (research,) = research_factory()
    (hunt,) = hunt_factory()
    source_targets = _load_source_mobile_targets(
        str(Path("runs/dd4-source/server/area").resolve())
    )

    assert research.target == target
    assert research.command_keyword == keyword
    assert research.consider_only is True
    assert research.exact_target is True
    assert research.maximum_target_count == 1
    assert research.require_isolated is True
    assert research.route_vnums == (room,)
    assert hunt.consider_only is False
    assert hunt.minimum_health_ratio == pytest.approx(0.85)
    assert hunt.maximum_level_offset == 1
    assert _room_mobile_target_counts(selector_text, source_targets) == {
        target: 1
    }
    assert _room_mobile_target_selectors(selector_text, source_targets) == {
        target: [selector]
    }
    assert _stop_target_matches(target, research.target, research) is True


def test_field_combat_plateau_tracks_new_low_health_before_withdrawing() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=forest_bear_claws_hunt_route(),
        fastwalk_hunt_stops=forest_bear_claws_hunt_stops(),
    )
    state = CharacterState(
        level=11,
        enemies=[[{"name": "the cook", "level": "10", "hp": "100", "maxhp": "144"}]],
    )

    assert policy._field_combat_plateau_elapsed(state, now=0.0) is None
    state.enemies = [
        [{"name": "the cook", "level": "10", "hp": "90", "maxhp": "144"}]
    ]
    assert policy._field_combat_plateau_elapsed(state, now=30.0) is None
    assert policy._field_combat_plateau_elapsed(state, now=89.0) is None
    assert policy._field_combat_plateau_elapsed(state, now=90.0) == 60.0


def test_field_combat_plateau_triggers_safe_flee(monkeypatch) -> None:
    clock = {"now": 0.0}
    monkeypatch.setattr(starter.time, "monotonic", lambda: clock["now"])
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=forest_bear_claws_hunt_route(),
        fastwalk_hunt_stops=forest_bear_claws_hunt_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.fastwalk_attack_started = True
    policy.active_target = "the cook"
    state = CharacterState(
        level=11,
        hp=150,
        max_hp=165,
        mana=180,
        max_mana=183,
        move=200,
        max_move=250,
        room_name="The Kitchens and Mess Hall",
        room_vnum="9403",
        enemies=[[{"name": "the cook", "level": "10", "hp": "100", "maxhp": "144"}]],
    )

    assert policy.next_decision(state) is None
    clock["now"] = 60.0
    policy.prompt_ready = True
    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "flee"
    assert "damage plateau" in decision.reason
    assert policy.fastwalk_emergency_recall_pending is True


def test_source_costed_fastwalk_waits_for_absolute_movement_budget() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=forest_bear_claws_hunt_route(),
        fastwalk_required_move=246,
        fastwalk_hunt_stops=forest_bear_claws_hunt_stops(),
    )
    recovering = CharacterState(
        hp=165,
        max_hp=165,
        mana=183,
        max_mana=183,
        move=225,
        max_move=250,
        position=7,
        room_name="By the Temple Altar",
        room_vnum="3054",
        room_flags=["safe", "healing"],
    )

    decision = policy._recovery_decision(recovering)

    assert decision is not None
    assert decision.command == "sleep"
    recovering.position = 4
    recovering.move = 236
    assert policy._recovery_ready_for_objective(recovering) is False
    recovering.move = 246
    assert policy._recovery_ready_for_objective(recovering) is True
    recovering.position = 7
    recovering.move = 250
    wake = policy._recovery_decision(recovering)
    assert wake is not None
    assert wake.command == "stand"
    assert policy._recovery_decision(recovering) is None
    policy.fastwalk_outbound_index = 1
    recovering.area = "Midgaard"
    recovering.room_name = "The Temple Square"
    recovering.room_vnum = "3005"
    recovering.room_flags = []
    recovering.move = 245

    assert policy._recovery_decision(recovering) is None


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
    assert stops[0].minimum_health_ratio == 0.675
    assert stops[0].exact_target is True


def test_shire_dwarven_prince_probe_allows_source_safe_companion() -> None:
    probe = shire_dwarven_prince_research_stops()
    hunt = shire_dwarven_prince_hunt_stops()

    assert len(probe) == 1
    assert probe[0].target == "dwarven prince"
    assert probe[0].command_keyword == "prince"
    assert probe[0].allowed_bystanders == ("elven warrior",)
    assert probe[0].trivial_bystanders == ("shiriff",)
    assert probe[0].consider_only is True
    assert probe[0].maximum_target_count == 1
    assert probe[0].require_isolated is True
    assert hunt[0].consider_only is False
    assert hunt[0].allowed_bystanders == ("elven warrior",)
    assert hunt[0].trivial_bystanders == ("shiriff",)
    assert hunt[0].minimum_health_ratio == 0.95
    assert hunt[0].maximum_level_offset == 1


def test_shire_prince_probe_considers_with_only_registered_companion() -> None:
    stop = shire_dwarven_prince_research_stops()[0]
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": None}),
        "swordfish",
        fastwalk_hunt_stops=(stop,),
    )
    policy.current_room = "1136"
    policy.fastwalk_attack_target = stop.target
    policy.room_target_counts["1136"] = {
        "dwarven prince": 1,
        "elven warrior": 1,
        "shiriff": 1,
    }

    decision = policy._consider_fastwalk_target(
        CharacterState(
            level=18,
            hp=254,
            max_hp=254,
            mana=242,
            max_mana=242,
            move=300,
            max_move=320,
            position=7,
            room_name="Bedroom",
            room_vnum="1136",
        )
    )

    assert decision is not None
    assert decision.command == "consider prince"
    assert policy.fastwalk_hunt_stop_skipped is False


def test_shire_thain_probe_and_hunt_keep_special_risk_bounded() -> None:
    probe = shire_thain_research_stops()
    hunt = shire_thain_hunt_stops()
    route = route_named("shire thain")

    assert route.commands == (
        "south", "south", "west", "west", "west", "west", "west",
        "north", "north", "north", "north", "east", "east", "east",
        "east", "east",
    )
    assert route.recall_after_loot is True
    assert len(probe) > 1
    assert probe[0].target == "the Thain"
    assert probe[0].command_keyword == "thain"
    assert probe[0].actions == ("where thain",)
    assert probe[0].abort_if_where_target_absent is True
    assert probe[0].consider_only is True
    assert probe[0].require_isolated is True
    assert probe[0].maximum_level_offset == 0
    assert probe[0].abort_after_consider_rejection is True
    assert probe[0].route_vnums == ()
    routes = dict(probe[0].where_location_routes)
    assert routes["delving lane"] == (
        "1110", "1109", "1106", "1104", "1103", "1118",
        "1120", "1131", "1132", "1133", "1134",
    )
    assert routes["gamgee residence"] == (
        "1110", "1109", "1106", "1104", "1103", "1118",
        "1120", "1131", "1132", "1133", "1138", "1139",
        "1140", "1141",
    )
    assert routes["a grassy field"] == (
        "1110", "1109", "1106", "1104", "1103", "1118",
        "1120", "1122", "1126", "1128", "1126", "1122",
        "1120", "1131", "1132", "1133", "1138",
    )
    assert probe[1].route_vnums == ("1110",)
    assert probe[-1].route_vnums == ("1120",)
    assert len(hunt) == len(probe)
    assert hunt[0].consider_only is False
    assert hunt[0].minimum_health_ratio == 0.90
    assert hunt[0].maximum_level_offset == 0


def test_where_locator_narrows_a_wandering_target_to_source_room_group() -> None:
    stops = shire_thain_research_stops()
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_hunt_stops=stops,
    )
    policy.fastwalk_hunt_action_index = 1

    response = (
        "You detect the presence of:\n"
        "The Thain                    Delving Lane\n"
        "\n<254/254 hits 242/242 mana 248/320 move [The Shire]>"
    )
    policy.observe_text(response)

    assert _where_location_from_response(response, "the Thain") == (
        "delving lane"
    )
    assert policy.fastwalk_where_location == "delving lane"
    assert tuple(
        stop.route_vnums[0]
        for stop in policy.fastwalk_hunt_stops[1:]
    ) == (
        "1110", "1109", "1106", "1104", "1103", "1118",
        "1120", "1131", "1132", "1133", "1134",
    )


def test_where_locator_narrows_to_gamgee_residence() -> None:
    stops = shire_thain_research_stops()
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_hunt_stops=stops,
    )
    policy.fastwalk_hunt_action_index = 1

    response = (
        "You detect the presence of:\n"
        "The Thain                    Gamgee Residence\n"
        "\n<254/254 hits 242/242 mana 251/320 move [The Shire]>"
    )
    policy.observe_text(response)

    assert _where_location_from_response(response, "the Thain") == (
        "gamgee residence"
    )
    assert tuple(
        stop.route_vnums[0]
        for stop in policy.fastwalk_hunt_stops[1:]
    ) == (
        "1110", "1109", "1106", "1104", "1103", "1118",
        "1120", "1131", "1132", "1133", "1138", "1139",
        "1140", "1141",
    )


def test_argent_bandit_leader_probe_allows_only_source_companion() -> None:
    probe = argent_bandit_leader_research_stops()
    hunt = argent_bandit_leader_hunt_stops()
    route = route_named("argent bandit leader")

    assert route.commands == (
        "south", "south", "east", "east", "east", "east", "east", "east",
        "south", "south", "south", "south", "east", "east", "south",
        "east", "east", "down", "east", "east", "north", "north",
        "north", "north", "north", "east", "east", "east", "east",
        "east", "south",
    )
    assert route.recall_after_loot is True
    assert len(probe) == 5
    assert probe[0].target == "bandit leader"
    assert probe[0].command_keyword == "leader"
    assert probe[0].actions == ("where leader",)
    assert probe[0].allowed_bystanders == ("bandit",)
    assert probe[0].consider_only is True
    assert probe[0].exact_target is True
    assert probe[0].maximum_target_count == 1
    assert probe[0].require_isolated is True
    assert probe[0].maximum_level_offset == 1
    assert probe[0].abort_if_where_target_absent is True
    assert probe[0].abort_after_consider_rejection is True
    assert probe[0].route_vnums == ()
    assert tuple(stop.route_vnums for stop in probe[1:]) == (
        ("25203", "25202"),
        ("25203",),
        ("25202", "25204"),
        ("25205",),
    )
    assert len(hunt) == len(probe)
    assert hunt[0].consider_only is False
    assert hunt[0].minimum_health_ratio == 0.90
    assert hunt[0].maximum_level_offset == 1


def test_argent_bandit_route_follows_adjacent_gmcp_exits_between_stops() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("argent bandit leader"),
        fastwalk_hunt_stops=argent_bandit_leader_research_stops(),
    )
    policy.fastwalk_hunt_stop_index = 1
    policy.fastwalk_hunt_route_before_target = True
    policy.current_room = "25205"

    first = policy._fastwalk_hunt_plan_decision(
        CharacterState(
            level=18,
            hp=254,
            max_hp=254,
            mana=242,
            max_mana=242,
            move=130,
            max_move=320,
            position=7,
            room_vnum="25205",
            exits={"n": "25203", "w": "25204"},
        )
    )

    assert first is not None
    assert first.command == "north"
    assert policy.fastwalk_hunt_move_index == 1

    policy.current_room = "25203"
    second = policy._fastwalk_hunt_plan_decision(
        CharacterState(
            level=18,
            hp=254,
            max_hp=254,
            mana=242,
            max_mana=242,
            move=129,
            max_move=320,
            position=7,
            room_vnum="25203",
            exits={"w": "25202", "s": "25205"},
        )
    )

    assert second is not None
    assert second.command == "west"
    assert policy.fastwalk_hunt_move_index == 2


def test_shire_elven_wizard_probe_allows_only_trivial_beauty_bystander() -> None:
    stops = shire_elven_wizard_research_stops()
    route = route_named("shire elven wizard")

    assert route.commands == (
        "south", "south", "west", "west", "west", "west", "west",
        "north", "north", "north", "north", "west", "west", "west",
        "west", "west",
    )
    assert route.recall_after_loot is True
    assert len(stops) == 1
    stop = stops[0]
    assert stop.target == "elven wizard"
    assert stop.command_keyword == "wizard"
    assert stop.trivial_bystanders == ("halfling beauty",)
    assert stop.consider_only is True
    assert stop.exact_target is True
    assert stop.require_isolated is True
    assert stop.maximum_level_offset == 1
    assert stop.abort_after_consider_rejection is True


def test_shire_elven_wizard_hunt_requires_a_full_health_bounded_fight() -> None:
    (stop,) = shire_elven_wizard_hunt_stops()

    assert stop.consider_only is False
    assert stop.minimum_health_ratio == 0.95
    assert stop.maximum_level_offset == 1
    assert stop.maximum_target_count == 1
    assert stop.require_isolated is True
    assert stop.trivial_bystanders == ("halfling beauty",)


def test_gnome_hermit_hunt_extends_to_two_isolated_miner_resets() -> None:
    route = gnome_hermit_hunt_route()
    stops = gnome_hermit_hunt_stops()

    assert route.commands == (
        "south",
        "south",
        "east",
        "east",
        "east",
        "east",
        "east",
        "south",
        "east",
        "east",
        "east",
        "east",
        "east",
        "east",
        "north",
        "east",
        "north",
        "north",
        "north",
    )
    assert len(stops) == 3
    assert stops[0].target == "hermit"
    assert stops[0].route == ()
    assert stops[0].minimum_health_ratio == 0.675
    assert stops[0].exact_target is True
    assert stops[1].target == "hobgoblin miner"
    assert stops[1].route == ("south", "south", "south")
    assert stops[1].exact_target is True
    assert stops[2].target == "hobgoblin miner"
    assert stops[2].route == ("east", "east")
    assert stops[2].exact_target is True


def test_gnome_guard_hunt_sweeps_three_source_resets() -> None:
    route = route_named("gnome guard hut")
    stops = gnome_guard_hunt_stops()

    assert route.commands == (
        "south",
        "south",
        "east",
        "east",
        "east",
        "east",
        "east",
        "south",
        "east",
        "east",
        "south",
        "south",
        "south",
        "west",
        "west",
    )
    assert [stop.target for stop in stops] == [
        "gnome guard",
        "gnome guard",
        "gnome guard",
    ]
    assert stops[0].route == ()
    assert stops[1].route == (
        "east",
        "east",
        "north",
        "north",
        "north",
        "north",
        "north",
        "north",
        "west",
    )
    assert stops[2].route == ("west", "west", "south")
    assert all(stop.exact_target for stop in stops)


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


def test_raider_hunt_requires_high_health_and_enables_combat() -> None:
    stops = ambush_raider_hunt_stops()

    assert len(stops) == 1
    assert stops[0].route == ambush_raider_consider_stops()[0].route
    assert stops[0].target == "goblin raider"
    assert stops[0].minimum_health_ratio == 0.675
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


def test_moria_sanctuary_hunt_requires_high_health_and_enables_combat() -> None:
    stops = moria_sanctuary_potion_hunt_stops()

    assert len(stops) == 1
    assert stops[0].route == moria_sanctuary_potion_consider_stops()[0].route
    assert all(stop.minimum_health_ratio == 0.675 for stop in stops)
    assert all(stop.consider_only is False for stop in stops)
    assert all(stop.exact_target for stop in stops)
    assert stops[0].actions == ("where hobgoblin",)
    assert stops[0].required_items == ("purple potion",)
    assert stops[0].allow_below_band_for_required_loot is True


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


def test_unfunded_funding_run_takes_one_bounded_healer_sleep() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
        fastwalk_hunt_stops=(
            FieldHuntStop(
                (),
                "safe soldier",
                command_keyword="soldier",
                exact_target=True,
                minimum_health_ratio=0.27,
            ),
        ),
        fastwalk_defer_provision_resupply=True,
    )
    policy.in_world = True
    policy.course_started = True
    policy.course_complete = True
    policy.prompt_ready = True
    state = CharacterState(
        level=18,
        hp=20,
        max_hp=100,
        mana=100,
        max_mana=100,
        move=100,
        max_move=100,
        position=7,
        room_name="By the Temple Altar",
        room_vnum="3054",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "sleep"
    assert policy.fastwalk_funding_recovery_attempted is True


def test_unfunded_funding_run_stays_asleep_while_below_field_ready_floor() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
        fastwalk_hunt_stops=(
            FieldHuntStop(
                (),
                "safe soldier",
                command_keyword="soldier",
                exact_target=True,
                minimum_health_ratio=0.27,
            ),
        ),
        fastwalk_defer_provision_resupply=True,
    )
    policy.needs_food = True
    policy.health_check_due = time.monotonic() + 60
    state = CharacterState(
        level=18,
        hp=73,
        max_hp=254,
        move=179,
        max_move=320,
        mana=242,
        max_mana=242,
        position=4,
        room_name="By the Temple Altar",
        room_vnum="3054",
    )

    handled, decision = policy._unfunded_funding_recovery_decision(state)

    assert handled is True
    assert decision is None
    assert policy.prompt_ready is False


def test_funding_run_withdraws_at_hard_health_boundary() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
        fastwalk_hunt_stops=(
            FieldHuntStop(
                (),
                "safe soldier",
                command_keyword="soldier",
                exact_target=True,
                minimum_health_ratio=0.27,
            ),
        ),
        fastwalk_defer_provision_resupply=True,
    )
    policy.fastwalk_funding_recovery_attempted = True
    state = CharacterState(
        level=18,
        hp=27,
        max_hp=100,
        room_name="By the Temple Altar",
        room_vnum="3054",
    )

    decision = policy._recovery_decision(state)

    assert decision is None
    assert policy.fastwalk_returning is True
    assert policy.fastwalk_abort_reason is not None


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

    assert policy.room_targets["3713"] == []
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


def test_level_eight_mage_refreshes_listing_after_gateway_training() -> None:
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
        "practice",
    ]
    assert policy.chill_touch_unavailable is False


def test_level_nine_mage_refreshes_listing_after_damage_gateway() -> None:
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
        "practice",
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


def test_smithy_practises_and_applies_counterbalance_before_leaving_trainer() -> None:
    sword = ObjectSource(
        3021,
        "sword",
        "a steel sword",
        5,
        (0, 2, 5, 1),
        10,
        wear_flags=1 | (1 << 13),
    )
    policy = StarterPolicy(
        _spec(**{"class": "smithy", "subclass": None}),
        "swordfish",
        gear_catalog=GearCatalog({sword.vnum: sword}),
    )
    policy.in_world = True
    policy.loremaster_step = 2
    policy.prompt_ready = True
    policy.gear_worn = [sword]
    policy.text = """
Skills known:
                 weaponsmithing:  30%
Skills which may be learned:
                  counterbalance:   0%                 shield block:   0%
You have 1 physical and 0 intellectual practices remaining.
"""
    state = CharacterState(
        level=10,
        hp=120,
        max_hp=120,
        room_name="The Forge",
        room_vnum="3050",
    )

    commands: list[str] = []
    responses = (
        "The craftsman says 'I hope my knowledge helps you, Rulemage.'\n",
        "You stop using a steel sword.\n",
        "You counterbalance a steel sword.\nIt's a 17/83 weighting split.\n",
        "You wield a steel sword.\n",
    )
    for response in responses:
        decision = policy._loremaster_decision(state)
        assert decision is not None
        commands.append(decision.command)
        policy.after_command(decision)
        policy.observe_text(response)
        policy.prompt_ready = True
    leave = policy._loremaster_decision(state)
    assert leave is not None
    commands.append(leave.command)

    assert commands == [
        "practice counterbalance",
        "remove sword",
        "counterbalance sword",
        "wield sword",
        "north",
    ]
    events = policy.drain_training_events()
    assert [event.type for event in events] == [
        "training_completed",
        "equipment_preparation_completed",
    ]
    assert events[1].data["skill"] == "counterbalance"
    assert any("APPLY_BALANCE" in ref for ref in events[1].data["source_refs"])


def test_smithy_defers_weapon_training_when_no_wielded_weapon_is_known() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "smithy", "subclass": None}),
        "swordfish",
    )
    policy.in_world = True
    policy.loremaster_step = 2
    policy.prompt_ready = True
    policy.text = """
Skills known:
Skills which may be learned:
                 weaponsmithing:   0%                  counterbalance:   0%
You have 0 physical and 1 intellectual practices remaining.
"""
    state = CharacterState(
        level=10,
        hp=120,
        max_hp=120,
        room_name="The Forge",
        room_vnum="3050",
    )

    decision = policy._loremaster_decision(state)

    assert decision is not None
    assert decision.command == "north"
    assert not decision.command.startswith("practice ")


def test_smithy_resumes_stored_counterbalance_preparation_without_repractice() -> None:
    sword = ObjectSource(
        3021,
        "sword",
        "a steel sword",
        5,
        (0, 2, 5, 1),
        10,
        wear_flags=1 | (1 << 13),
    )
    policy = StarterPolicy(
        _spec(**{"class": "smithy", "subclass": None}),
        "swordfish",
        gear_catalog=GearCatalog({sword.vnum: sword}),
        practice_types_spent=frozenset({"physical"}),
        counterbalance_preparation_required=True,
    )
    policy.in_world = True
    policy.loremaster_step = 2
    policy.prompt_ready = True
    policy.gear_worn = [sword]
    policy.text = """
Skills known:
                  counterbalance:  35%               weaponsmithing:  35%
You have 0 physical and 1 intellectual practices remaining.
"""
    state = CharacterState(
        level=10,
        hp=120,
        max_hp=120,
        room_name="The Forge",
        room_vnum="3050",
    )

    decision = policy._loremaster_decision(state)

    assert decision is not None
    assert decision.command == "remove sword"


def test_smithy_re_equips_after_counterbalance_command_is_unconfirmed() -> None:
    sword = ObjectSource(
        3021,
        "sword",
        "a steel sword",
        5,
        (0, 2, 5, 1),
        10,
        wear_flags=1 | (1 << 13),
    )
    policy = StarterPolicy(
        _spec(**{"class": "smithy", "subclass": None}),
        "swordfish",
        gear_catalog=GearCatalog({sword.vnum: sword}),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.loremaster_step = 3
    policy.practice_plan = ()
    policy.gear_worn = [sword]
    policy.smithy_counterbalance_step = 1
    state = CharacterState(
        level=10,
        hp=120,
        max_hp=120,
        room_name="The Forge",
        room_vnum="3050",
    )

    remove = policy._loremaster_decision(state)
    assert remove is not None
    policy.after_command(remove)
    policy.observe_text("You stop using a steel sword.\n")
    policy.prompt_ready = True
    counterbalance = policy._loremaster_decision(state)
    assert counterbalance is not None
    policy.after_command(counterbalance)
    policy.observe_text("Your hands aren't steady enough to safely sharpen your blade.\n")
    policy.prompt_ready = True
    re_equip = policy._loremaster_decision(state)

    assert remove.command == "remove sword"
    assert counterbalance.command == "counterbalance sword"
    assert re_equip is not None
    assert re_equip.command == "wield sword"
    (event,) = policy.drain_training_events()
    assert event.type == "equipment_preparation_deferred"
    assert event.data["outcome"] == "deferred"


def test_ranger_only_practises_archery_when_a_source_bow_is_equipped() -> None:
    bow = ObjectSource(
        18001,
        "bow",
        "a short bow",
        5,
        (0, 2, 4, 4),
        20,
        wear_flags=1 | (1 << 17),
        extra_flags=1 << 30,
    )
    listing = """
Skills known:
          armed combat knowledge:  20%
Skills which may be learned:
             archery knowledge:   0%
You have 0 physical and 1 intellectual practices remaining.
"""
    state = CharacterState(
        level=10,
        hp=120,
        max_hp=120,
        room_name="The Lusty Ogres Tavern",
        room_vnum="3048",
    )
    equipped = StarterPolicy(
        _spec(**{"class": "ranger", "subclass": None}),
        "swordfish",
        gear_catalog=GearCatalog({bow.vnum: bow}),
    )
    equipped.in_world = True
    equipped.loremaster_step = 2
    equipped.gear_worn = [bow]
    equipped.text = listing

    without_bow = StarterPolicy(
        _spec(**{"class": "ranger", "subclass": None}),
        "swordfish",
    )
    without_bow.in_world = True
    without_bow.loremaster_step = 2
    without_bow.text = listing

    train = equipped._loremaster_decision(state)
    preserve = without_bow._loremaster_decision(state)

    assert train.command == "practice archery knowledge"
    assert preserve.command == "north"


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


def test_target_level_does_not_intercept_fastwalk_training_route() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        objective_level=11,
        fastwalk_route=route_named("fleshmonger"),
    )
    temple = CharacterState(
        level=11,
        hp=165,
        max_hp=165,
        room_name="The Temple Of Midgaard",
        room_vnum="3001",
    )

    assert policy._arena_completion_route_decision(temple) is None


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


def test_required_loot_stop_can_attack_below_band_without_relaxing_xp_policy() -> None:
    stop = foundry_body_gear_hunt_stops()[0]
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_hunt_stops=(stop,),
    )
    policy.current_room = "110"
    policy.room_target_counts["110"] = {"oshu": 1}
    policy.fastwalk_attack_target = "oshu"
    policy.consider_target = "oshu"
    policy.consider_viable = False
    policy.last_response = "Oshu is no match for you.\n"

    decision = policy._consider_fastwalk_target(
        CharacterState(level=8, room_vnum="110", inventory=[])
    )

    assert decision is not None
    assert decision.command == "kill oshu"
    assert "required replacement gear, not XP" in decision.reason
    assert policy.combat_active is True


def test_required_loot_exception_never_accepts_a_dangerous_consider_result() -> None:
    stop = foundry_body_gear_hunt_stops()[0]
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_hunt_stops=(stop,),
    )
    policy.current_room = "110"
    policy.room_target_counts["110"] = {"oshu": 1}
    policy.fastwalk_attack_target = "oshu"
    policy.consider_target = "oshu"
    policy.consider_viable = False
    policy.last_response = "Oshu laughs at you mercilessly.\n"

    decision = policy._consider_fastwalk_target(
        CharacterState(level=2, room_vnum="110", inventory=[])
    )

    assert decision is not None
    assert decision.command == "look"
    assert policy.combat_active is False


def test_required_loot_retry_bypasses_persisted_below_band_skip() -> None:
    stop = foundry_body_gear_hunt_stops()[0]
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_hunt_stops=(stop,),
    )
    policy.current_room = "110"
    policy.room_targets["110"] = ["oshu"]
    policy.room_target_counts["110"] = {"oshu": 1}
    policy.fastwalk_attack_target = "oshu"
    policy.consider_target = "oshu"
    policy.consider_viable = False
    policy.fastwalk_below_band_sightings.add(("110", "oshu"))
    policy.last_response = "Oshu is no match for you.\n"

    decision = policy._fastwalk_hunt_plan_decision(
        CharacterState(level=8, room_vnum="110", inventory=[])
    )

    assert decision is not None
    assert decision.command == "kill oshu"
    assert policy.combat_active is True


def test_persisted_below_band_skip_remains_terminal_for_xp_hunts() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_hunt_stops=(FieldHuntStop((), "oshu"),),
    )
    policy.current_room = "110"
    policy.room_targets["110"] = ["oshu"]
    policy.room_target_counts["110"] = {"oshu": 1}
    policy.fastwalk_below_band_sightings.add(("110", "oshu"))

    decision = policy._fastwalk_hunt_plan_decision(
        CharacterState(level=8, room_vnum="110", inventory=[])
    )

    assert decision is not None
    assert decision.command == "look"
    assert "persisted below-band" in decision.reason
    assert policy.fastwalk_hunt_stop_skipped is True
    assert policy.fastwalk_attack_started is False


def test_foundry_body_recovery_is_one_room_and_requires_the_jerkin() -> None:
    (stop,) = foundry_body_gear_hunt_stops()

    assert stop.route == ("open east", "east")
    assert stop.target == "oshu"
    assert stop.required_items == ("leather jerkin",)
    assert stop.allow_below_band_for_required_loot is True


def test_level_eight_caster_ambush_continues_from_dog_to_looter() -> None:
    dog, looter = ambush_caster_level_eight_hunt_stops()

    assert dog.target == "war dog"
    assert dog.exact_target is True
    assert looter.route == ("south", "south")
    assert looter.target == "goblin looter"
    assert looter.exact_target is True
    assert looter.minimum_combat_health_ratio == 0.5


def test_training_target_parser_recognizes_source_mobile_room_description() -> None:
    foundry = parse_area_file(
        Path("runs/dd4-source/server/area/foundry.are"),
        include_objects=False,
    )
    targets = _training_target_counts(foundry.mobiles[107].room_description)

    assert targets == {"oshu": 1}


def test_training_target_parser_recognizes_ambush_looter_source_line() -> None:
    ambush = parse_area_file(
        Path("runs/dd4-source/server/area/ambush.are"),
        include_objects=False,
    )

    assert _training_target_counts(
        ambush.mobiles[4505].room_description
    ) == {"goblin looter": 1}


def test_source_mobile_index_uses_exact_area_file_display_lines() -> None:
    targets = _load_source_mobile_targets(
        str(Path("runs/dd4-source/server/area").resolve())
    )

    assert targets[
        "a mountain goblin is wandering about, mumbling to himself."
    ] == ("mountain goblin",)
    assert targets["a goblin is here, looting the dead."] == ("goblin looter",)
    assert targets["a goblin is here sleeping."] == ("bardoosh",)
    assert targets[
        "oshu, the goblin soldier, monitors the pit."
    ] == ("oshu",)


def test_source_mobile_level_ranges_include_both_dd4_fuzz_steps() -> None:
    ranges = _load_source_mobile_level_ranges(
        str(Path("runs/dd4-source/server/area").resolve())
    )

    assert ranges["aruncus the druid"] == (11, 15)
    assert ranges["bardoosh"] == (10, 14)


def test_source_mobile_index_covers_high_level_targetmode_lines_and_levels() -> None:
    area_directory = str(Path("runs/dd4-source/server/area").resolve())
    source_targets = _load_source_mobile_targets(area_directory)
    source_levels = _load_source_mobile_level_ranges(area_directory)

    rastafarians = "[#17099] The Rastafarians load up a huge bowl and\n"
    hulking_beast = "[#39013] a hulking beast\n"

    assert _room_mobile_target_counts(rastafarians, source_targets) == {
        "rastafarians": 1
    }
    assert _room_mobile_target_selectors(rastafarians, source_targets) == {
        "rastafarians": ["#17099"]
    }
    assert _room_mobile_target_counts(hulking_beast, source_targets) == {
        "hulking beast": 1
    }
    assert source_levels["rastafarians"] == (68, 72)
    assert source_levels["hulking beast"] == (62, 67)
    assert source_targets["the keeper greets you."] == (
        "keeper of the tower",
    )
    assert source_levels["keeper of the tower"] == (14, 18)


def test_bardoosh_generic_live_line_binds_exact_targetmode_selector() -> None:
    source_targets = _load_source_mobile_targets(
        str(Path("runs/dd4-source/server/area").resolve())
    )
    text = "[#3095] A goblin is here sleeping.\n"

    assert _room_mobile_target_counts(text, source_targets) == {"bardoosh": 1}
    assert _room_mobile_target_selectors(text, source_targets) == {
        "bardoosh": ["#3095"]
    }


def test_keeper_generic_live_line_binds_proper_source_identity() -> None:
    source_targets = _load_source_mobile_targets(
        str(Path("runs/dd4-source/server/area").resolve())
    )
    text = "[#6577] The keeper greets you.\n"

    assert _room_mobile_target_counts(text, source_targets) == {
        "keeper of the tower": 1
    }
    assert _room_mobile_target_selectors(text, source_targets) == {
        "keeper of the tower": ["#6577"]
    }


def test_dwarven_nobleman_live_line_binds_registered_exact_target() -> None:
    source_targets = _load_source_mobile_targets(
        str(Path("runs/dd4-source/server/area").resolve())
    )
    text = "[#10736] A dwarven nobleman watches you.\n"
    (stop,) = dwarven_nobleman_research_stops()

    counts = _room_mobile_target_counts(text, source_targets)

    assert counts == {"dwarven nobleman": 1}
    assert _room_mobile_target_selectors(text, source_targets) == {
        "dwarven nobleman": ["#10736"]
    }
    assert _stop_target_matches(next(iter(counts)), stop.target, stop) is True


def test_dwarven_nobleman_allows_only_the_source_maid_as_a_bystander() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_hunt_stops=dwarven_nobleman_research_stops(),
    )
    policy.current_room = "20506"
    policy.fastwalk_attack_target = "dwarven nobleman"
    policy.room_target_counts["20506"] = {
        "dwarven nobleman": 1,
        "maid": 1,
    }
    policy.room_target_selectors["20506"] = {
        "dwarven nobleman": ["#10736"],
        "maid": ["#10727"],
    }

    decision = policy._consider_fastwalk_target(
        CharacterState(
            level=17,
            hp=242,
            max_hp=242,
            mana=235,
            max_mana=235,
            move=310,
            max_move=310,
            position=7,
            room_name="The nobleman's house",
            room_vnum="20506",
        )
    )

    assert decision is not None
    assert decision.command == "consider #10736"
    assert policy.fastwalk_abort_reason is None


def test_room_mobile_parser_prefers_source_lines_and_keeps_unknown_mobiles() -> None:
    targets = _room_mobile_target_counts(
        "A pig wallows in the mud and oinks in contentment.\n"
        "An ugly kobold mumbles something under its breath.\n",
        {
            "a pig wallows in the mud and oinks in contentment.": ("pig",),
        },
    )

    assert targets == {"pig": 1, "ugly kobold": 1}


def test_room_mobile_parser_counts_repeated_source_lines() -> None:
    targets = _room_mobile_target_counts(
        "A war dog is here, eating carrion.\n"
        "A war dog is here, eating carrion.\n",
        {
            "a war dog is here, eating carrion.": ("war dog",),
        },
    )

    assert targets == {"war dog": 2}


def test_targetmode_prefix_preserves_source_identity_and_exact_selectors() -> None:
    text = (
        "[#184467] A war dog is here, eating carrion.\n"
        "[#184468] A war dog is here, eating carrion.\n"
    )
    source_targets = {
        "a war dog is here, eating carrion.": ("war dog",),
    }

    assert _room_mobile_target_counts(text, source_targets) == {"war dog": 2}
    assert _room_mobile_target_selectors(text, source_targets) == {
        "war dog": ["#184467", "#184468"],
    }


def test_targetmode_aura_prefix_preserves_exact_mobile_selector() -> None:
    text = (
        "[#22616] \x1b[38;5;15m(White Aura)\x1b[0m "
        "A rather large rock toad sits here, croaking loudly.\n"
    )
    source_targets = {
        "a rather large rock toad sits here, croaking loudly.": ("rock toad",),
    }

    assert _room_mobile_target_counts(text, source_targets) == {"rock toad": 1}
    assert _room_mobile_target_selectors(text, source_targets) == {
        "rock toad": ["#22616"],
    }


def test_targetmode_does_not_promote_an_object_selector_to_a_mobile() -> None:
    assert _room_mobile_target_selectors(
        "[#9911] A silver sword lies here.\n",
        {"a war dog is here, eating carrion.": ("war dog",)},
    ) == {}


def test_target_selector_prefers_the_latest_room_observation() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.current_room = "4014"
    policy.room_target_selectors["4014"] = {
        "ugly kobold": ["#938475", "#938499"],
    }

    assert policy._target_selector_for("ugly kobold") == "#938499"


def test_between_round_spell_refreshes_a_stale_targetmode_selector() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.current_room = "4014"
    policy.active_target = "ugly kobold"
    policy.active_target_selector = "#938475"
    policy.room_target_selectors["4014"] = {
        "ugly kobold": ["#938475", "#938499"],
    }
    policy.known_skills.add("magic missile")
    state = CharacterState(mana=100, max_mana=100)

    decision = policy._between_round_combat_decision(state)

    assert decision is not None
    assert decision.command == "cast 'magic missile' #938499"
    assert policy.active_target_selector == "#938499"


def test_imminent_arena_level_routes_to_loremaster_and_selects_stat() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    state = CharacterState(
        level=5,
        xp_to_next_level=200,
        progress={"xplvl": 2500},
        room_vnum="3725",
    )

    outbound = policy._imminent_stat_training_decision(state)
    assert outbound is not None
    assert outbound.command == "east"

    state.room_vnum = "3726"
    train = policy._imminent_stat_training_decision(state)
    assert train is not None
    assert train.command == "train int"


def test_imminent_level_routes_from_mud_school_general_supplies_to_loremaster() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.selected_training_stat = None
    state = CharacterState(
        level=1,
        xp_to_next_level=100,
        progress={"xplvl": 2500},
        room_name="General Supplies",
        room_vnum="3724",
    )

    decision = policy._imminent_stat_training_decision(state)

    assert decision is not None
    assert decision.command == "down"
    assert "Loremaster" in decision.reason


def test_fastwalk_uses_one_exact_selector_for_consider_attack_and_spell() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
        fastwalk_attack_target="ugly kobold",
    )
    policy.current_room = "4014"
    policy.room_target_counts["4014"] = {"ugly kobold": 1}
    policy.room_target_selectors["4014"] = {
        "ugly kobold": ["#938475"],
    }
    state = CharacterState(
        level=11,
        room_vnum="4014",
        mana=100,
        max_mana=100,
    )

    consider = policy._consider_fastwalk_target(state)
    assert consider is not None
    assert consider.command == "consider #938475"

    policy.consider_viable = True
    attack = policy._consider_fastwalk_target(state)
    assert attack is not None
    assert attack.command == "kill #938475"
    assert policy.active_target == "ugly kobold"
    assert policy.active_target_selector == "#938475"

    policy.known_skills.add("magic missile")
    spell = policy._between_round_combat_decision(state)
    assert spell is not None
    assert spell.command == "cast 'magic missile' #938475"


def test_required_loot_capacity_preflight_donates_only_excess_food() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_required_free_weight=7,
        fastwalk_hunt_stops=foundry_body_gear_hunt_stops(),
    )
    state = CharacterState(
        level=8,
        room_vnum="3001",
        inventory=[[{"short_desc": "a big pot pie", "quan": "3"}]],
        stats={"carry_wt": 111, "maxcarry_wt": 115},
    )

    decision = policy._fastwalk_research_decision(state)

    assert decision is not None
    assert decision.command == "donate pie"
    assert policy.fastwalk_capacity_preflight_complete is False


def test_required_loot_capacity_preflight_aborts_before_last_two_pies() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_required_free_weight=7,
        fastwalk_hunt_stops=foundry_body_gear_hunt_stops(),
    )
    state = CharacterState(
        level=8,
        room_vnum="3001",
        inventory=[[{"short_desc": "a big pot pie", "quan": "2"}]],
        stats={"carry_wt": 111, "maxcarry_wt": 115},
    )

    decision = policy._fastwalk_research_decision(state)

    assert decision is not None
    assert decision.command == "north"
    assert policy.fastwalk_returning is True
    assert "capacity" in (policy.fastwalk_abort_reason or "")


def test_capacity_pressed_multi_target_hunt_preserves_space_for_experience() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("fleshmonger"),
        fastwalk_xp_first_capacity_threshold=20,
        fastwalk_hunt_stops=fleshmonger_thief_rotation_research_stops(),
        fastwalk_kill_limit=2,
    )
    state = CharacterState(
        level=12,
        room_vnum="3001",
        stats={"carry_wt": 133, "maxcarry_wt": 140},
    )

    departure = policy._fastwalk_research_decision(state)

    assert departure is not None
    assert departure.command == "config -autoloot"
    assert policy.fastwalk_collect_loot is False

    policy.current_room = "9400"
    policy.pending_loot_rooms.add("9400")
    sacrifice = policy._fastwalk_research_decision(
        CharacterState(level=12, room_vnum="9400")
    )

    assert sacrifice is not None
    assert sacrifice.command == "sacrifice corpse"


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


def test_campaign_arena_patrol_checkpoints_instead_of_waiting_for_reset() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        objective_level=6,
        arena_respawn_wait=False,
    )
    policy.in_world = True
    policy.arena_queried = True
    policy.prompt_ready = True
    policy.arena_visited_rooms.update(str(vnum) for vnum in range(3728, 3738))
    policy.room_query_counts["3736"] = 1
    state = CharacterState(
        level=5,
        hp=90,
        max_hp=90,
        room_name="The Mud School Arena",
        room_vnum="3736",
        exits={"n": "3733", "u": "3737", "w": "3735"},
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "up"
    assert "checkpoint" in decision.reason
    assert policy.arena_segment_leaving is True
    assert policy.arena_respawn_due is None


def test_arena_checkpoint_saves_after_reaching_the_midgaard_healer() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        objective_level=6,
        arena_respawn_wait=False,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.arena_segment_leaving = True
    state = CharacterState(
        level=2,
        hp=63,
        max_hp=63,
        room_name="By the Temple Altar",
        room_vnum="3054",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "save"
    assert "arena checkpoint" in decision.reason


def test_level_one_arena_segment_does_not_quit_before_dd4_can_save() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=2)
    policy.in_world = True
    policy.prompt_ready = True
    policy.course_complete = True
    policy.provisioned = True
    policy.practiced = True
    policy.arena_segment_leaving = True
    state = CharacterState(
        level=1,
        hp=50,
        max_hp=50,
        room_name="By the Temple Altar",
        room_vnum="3054",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "south"


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


def test_unsaveable_level_one_arena_waits_outside_for_a_reset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(starter.time, "monotonic", lambda: 100.0)
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        objective_level=2,
        arena_respawn_wait=False,
    )
    policy.in_world = True
    policy.arena_queried = True
    policy.prompt_ready = True
    policy.arena_skipped_outside_safe_band = True
    policy.arena_visited_rooms.update(str(vnum) for vnum in range(3728, 3738))
    policy.room_query_counts["3736"] = 1
    state = CharacterState(
        level=1,
        hp=50,
        max_hp=50,
        room_name="The Mud School Arena",
        room_vnum="3736",
        exits={"n": "3733", "u": "3737", "w": "3735"},
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "up"
    assert "level-one arena reset" in decision.reason
    assert policy.arena_segment_leaving is False
    assert policy.arena_respawn_due == 280.0


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
        if room_vnum == "3007" and expected == "west":
            policy.observe_text("The teller says 'after borrowing: 300 coins.'")
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


def test_emergency_bank_loan_withdraws_existing_balance_once() -> None:
    policy = StarterPolicy(_spec(), "swordfish", resupply_only=True)
    policy.in_world = True
    policy.emergency_borrowing = True

    first = policy._resupply_decision(
        CharacterState(room_name="Dragonhoard Bank", room_vnum="3007", position=7)
    )
    assert first is not None
    assert first.command == "borrow 300"

    policy.observe_text(
        "The teller says 'If you are only borrowing that much, withdraw the coins instead Kestrel.'"
    )
    withdraw = policy._resupply_decision(
        CharacterState(room_name="Dragonhoard Bank", room_vnum="3007", position=7)
    )
    assert withdraw is not None
    assert withdraw.command == "withdraw 3 gold"

    policy.observe_text("The teller says 'Thank you for your custom Kestrel.'")
    leave = policy._resupply_decision(
        CharacterState(room_name="Dragonhoard Bank", room_vnum="3007", position=7)
    )
    assert leave is not None
    assert leave.command == "west"


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


def test_resupply_consumes_new_purchase_before_leaving_supplies() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.prompt_ready = True
    policy.food_ordered = True
    policy.needs_food = True
    policy.needs_drink = False
    policy.food_unavailable = True
    state = CharacterState(
        hp=96,
        max_hp=96,
        room_name="General Supplies",
        room_vnum="3724",
        inventory=[[
            {"short_desc": "a big pot pie"},
            {"short_desc": "a buffalo water skin"},
        ]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "eat pie"
    assert "before leaving supplies" in decision.reason


def test_route_cycle_watchdog_routes_supplies_directly_toward_healer() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        room_name="General Supplies",
        room_vnum="3724",
        room_flags=["indoors", "safe"],
        position=7,
    )

    decision = policy.recover_from_stall(state, "down route cycle")

    assert decision is not None
    assert decision.command == "down"
    assert policy.return_home is True
    assert "watchdog" in decision.reason


def test_resupply_drinks_new_skin_before_leaving_supplies() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.prompt_ready = True
    policy.needs_food = False
    policy.needs_drink = True
    state = CharacterState(
        hp=96,
        max_hp=96,
        room_name="General Supplies",
        room_vnum="3724",
        inventory=[[{"short_desc": "a buffalo water skin"}]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "drink skin"


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


def test_emergency_resupply_reduces_bulk_order_after_capacity_rejection() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.prompt_ready = True
    policy.needs_food = True
    policy.needs_drink = False
    supplies = CharacterState(
        hp=96,
        max_hp=96,
        room_name="General Supplies",
        room_vnum="3724",
        inventory=[[{"short_desc": "a buffalo water skin"}]],
    )

    first = policy.next_decision(supplies)

    assert first is not None
    assert first.command == "buy 6 pie"
    policy.after_command(first)
    policy.observe_text("You can't carry that much weight.")
    policy.prompt_ready = True

    retry = policy.next_decision(supplies)

    assert retry is not None
    assert retry.command == "buy 5 pie"
    assert policy.failure is None


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
        ("Main Street", "3013", "east"),
        ("Market Square", "3014", "north"),
        ("The Temple Square", "3005", "north"),
        ("The Temple Of Midgaard", "3001", "north"),
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
        CharacterState(room_name="By the Temple Altar", room_vnum="3054", position=7)
    )
    assert decision is not None
    assert decision.command == "save"


def test_city_restock_leaves_general_supplies_for_temple_route() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_restock=True)
    policy.in_world = True
    policy.prompt_ready = True

    decision = policy.next_decision(
        CharacterState(
            room_name="General Supplies",
            room_vnum="3724",
            position=7,
        )
    )

    assert decision is not None
    assert decision.command == "down"


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


def test_city_restock_policy_leaves_healer_for_temple_route() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_restock=True)
    policy.in_world = True
    policy.prompt_ready = True

    decision = policy.next_decision(
        CharacterState(
            room_name="By the Temple Altar",
            room_vnum="3054",
            position=7,
        )
    )

    assert decision is not None
    assert decision.command == "south"
    assert "fountain" in decision.reason


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


def test_city_restock_caps_pie_order_to_free_item_slots() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_restock=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.city_restock_step = 4

    decision = policy.next_decision(
        CharacterState(
            room_name="The Bakery",
            room_vnum="3009",
            position=7,
            stats={
                "carry_num": 43,
                "maxcarry_num": 46,
                "carry_wt": 117,
                "maxcarry_wt": 250,
            },
        )
    )

    assert decision is not None
    assert decision.command == "buy 3 pie"


def test_city_restock_audits_then_uses_carried_food_to_free_capacity() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_restock=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.city_restock_step = 4
    full_bakery = CharacterState(
        room_name="The Bakery",
        room_vnum="3009",
        position=7,
        stats={"carry_wt": 89, "maxcarry_wt": 90},
        inventory=[[]],
    )

    audit = policy.next_decision(full_bakery)

    assert audit is not None
    assert audit.command == "inventory"

    policy.prompt_ready = True
    audited_bakery = CharacterState(
        room_name="The Bakery",
        room_vnum="3009",
        position=7,
        stats={"carry_wt": 89, "maxcarry_wt": 90},
        inventory=[[{"short_desc": "a big pot pie"}]],
    )
    relief = policy.next_decision(audited_bakery)

    assert relief is not None
    assert relief.command == "eat pie"

    policy.prompt_ready = True
    assert policy.next_decision(audited_bakery) is None
    assert policy.prompt_ready is False

    policy.observe_text("You eat a big pot pie.")
    policy.prompt_ready = True
    decision = policy.next_decision(
        CharacterState(
            room_name="The Bakery",
            room_vnum="3009",
            position=7,
            stats={"carry_wt": 84, "maxcarry_wt": 90},
        )
    )

    assert decision is not None
    assert decision.command == "buy 1 pie"


def test_city_restock_fails_after_a_capacity_audit_finds_no_food() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_restock=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.city_restock_step = 4
    full_bakery = CharacterState(
        room_name="The Bakery",
        room_vnum="3009",
        position=7,
        stats={"carry_wt": 89, "maxcarry_wt": 90},
        inventory=[[]],
    )

    assert policy.next_decision(full_bakery) is not None
    policy.prompt_ready = True
    decision = policy.next_decision(full_bakery)

    assert decision is None
    assert policy.failure == "no carry capacity remained for one essential pie"


def test_city_restock_sacrifices_one_duplicate_paint_consumable_for_capacity() -> None:
    paste = ObjectSource(
        11525,
        "leechblood paste blood",
        "leechblood paste",
        28,
        (13,),
        0,
        wear_flags=1,
    )
    catalog = GearCatalog({paste.vnum: paste})
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        city_restock=True,
        gear_catalog=catalog,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.gear_audited = True
    policy.gear_allowed_categories = set()
    policy.city_restock_step = 4
    full_bakery = CharacterState(
        room_name="The Bakery",
        room_vnum="3009",
        position=7,
        stats={"carry_num": 46, "maxcarry_num": 46, "carry_wt": 189, "maxcarry_wt": 300},
        inventory=[[{"short_desc": "leechblood paste", "quan": "2"}]],
    )

    audit = policy.next_decision(full_bakery)
    assert audit is not None
    assert audit.command == "inventory"

    policy.prompt_ready = True
    relief = policy.next_decision(full_bakery)
    assert relief is not None
    assert relief.command == "drop paste"

    policy.after_command(relief)
    policy.observe_text("You drop the leechblood paste.")
    policy.prompt_ready = True
    sacrifice = policy.next_decision(full_bakery)
    assert sacrifice is not None
    assert sacrifice.command == "sacrifice paste"

    policy.after_command(sacrifice)
    policy.observe_text("You sacrifice the leechblood paste to your god.")
    policy.prompt_ready = True
    decision = policy.next_decision(
        CharacterState(
            room_name="The Bakery",
            room_vnum="3009",
            position=7,
            stats={"carry_num": 45, "maxcarry_num": 46, "carry_wt": 188, "maxcarry_wt": 300},
        )
    )

    assert decision is not None
    assert decision.command == "buy 1 pie"


def test_capacity_relief_does_not_discard_duplicate_potions() -> None:
    potion = ObjectSource(
        11526,
        "light blue potion",
        "a light blue potion",
        10,
        (10,),
        100,
        wear_flags=1,
    )

    assert (
        _capacity_relief_inventory_keyword(
            [[{"short_desc": "a light blue potion", "quan": "2"}]],
            GearCatalog({potion.vnum: potion}),
        )
        is None
    )


def test_returning_fastwalk_at_healer_does_not_divert_to_supplies_when_overweight() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("hightower jailor"),
        fastwalk_hunt_stops=hightower_jailor_hunt_stops(),
    )
    policy.fastwalk_returning = True
    policy.needs_food = True

    decision = policy._resupply_decision(
        CharacterState(
            area="Midgaard",
            room_name="By the Temple Altar",
            room_vnum="3054",
            position=7,
            stats={"carry_wt": 175, "maxcarry_wt": 140},
            inventory=[[{"short_desc": "a juicy steak"}]],
        )
    )

    assert decision is not None
    assert decision.command == "eat steak"
    assert policy.failure is None


def test_resupply_eats_a_carried_steak_when_hungry() -> None:
    policy = StarterPolicy(_spec(), "swordfish", resupply_only=True)
    policy.needs_food = True

    decision = policy._resupply_decision(
        CharacterState(
            room_name="By the Temple Altar",
            room_vnum="3054",
            position=7,
            inventory=[[{"short_desc": "a juicy steak"}]],
        )
    )

    assert decision is not None
    assert decision.command == "eat steak"


def test_room_prose_is_empty_does_not_mark_drink_unavailable() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.after_command(BotDecision("drink skin", "drink before travel"))

    policy.observe_text(
        "Obstacle Course\n"
        "The room is empty and dirty.\n"
        "<254/254 hits 242/242 mana 315/320 move>"
    )

    assert policy.needs_drink is False
    assert policy.water_unavailable is False


def test_unrelated_command_failure_does_not_consume_stale_drink_context() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.after_command(BotDecision("drink skin", "drink before travel"))
    policy.needs_drink = True

    policy.after_command(BotDecision("sacrifice corpse", "clean up loot"))
    policy.observe_text("You can't find it.\n")

    assert policy.needs_drink is True
    assert policy.water_unavailable is False


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


def test_city_restock_backs_off_after_item_count_rejection() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_restock=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.city_restock_step = 5
    policy.last_pie_order_quantity = 6
    policy.observe_text("You can't carry that many items.")

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
        if room_vnum == "3007" and expected == "west":
            policy.observe_text("The teller says 'after borrowing: 300 coins.'")
        decision = policy.next_decision(
            CharacterState(room_name=room_name, room_vnum=room_vnum, position=7)
        )
        assert decision is not None
        assert decision.command == expected
        policy.after_command(decision)
        policy.prompt_ready = True


def test_city_restock_withdraws_existing_bank_balance_once() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_restock=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.restock_borrowing = True

    first = policy.next_decision(
        CharacterState(room_name="Dragonhoard Bank", room_vnum="3007", position=7)
    )
    assert first is not None
    assert first.command == "borrow 300"

    policy.observe_text(
        "The teller says 'If you are only borrowing that much, withdraw the coins instead Kestrel.'"
    )
    withdraw = policy.next_decision(
        CharacterState(room_name="Dragonhoard Bank", room_vnum="3007", position=7)
    )
    assert withdraw is not None
    assert withdraw.command == "withdraw 3 gold"

    policy.observe_text("The teller says 'Thank you for your custom Kestrel.'")
    leave = policy.next_decision(
        CharacterState(room_name="Dragonhoard Bank", room_vnum="3007", position=7)
    )
    assert leave is not None
    assert leave.command == "west"


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
        ("The Temple Of Midgaard", "3001", "help teacher clue"),
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
    assert policy.practice_types_spent == {"intellectual"}
    assert "no eligible source-backed priority skill" in policy.practice_exit_reason


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


def test_fastwalk_unexpected_combat_audits_after_flee_before_recalling() -> None:
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

    audit = policy.next_decision(
        CharacterState(room_name="Forest path", room_vnum="6011", position=7)
    )

    assert audit is not None
    assert audit.command == "look"
    policy.after_command(audit)
    policy.prompt_ready = True
    policy.fastwalk_post_flee_audit_due = 0.0

    recall = policy.next_decision(
        CharacterState(room_name="Forest path", room_vnum="6011", position=7)
    )

    assert recall is not None
    assert recall.command == "recall"
    assert recall.reason == "leave the fastwalk immediately after unexpected combat"


def test_multistop_hunt_skips_crowded_endpoint_after_flee_and_continues() -> None:
    route = route_named("highland keeper")
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=highland_keeper_hunt_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_stop_index = 0
    policy.current_room = "11536"
    policy.combat_active = True
    policy.active_target = "a gigantic frog"
    policy.active_target_level = 16
    policy.active_enemy_count = 1
    policy.room_target_counts["11536"] = {
        "keeper of the tower": 1,
        "a sheep": 1,
        "a gigantic frog": 1,
    }
    endpoint = CharacterState(
        level=18,
        hp=254,
        max_hp=254,
        mana=242,
        max_mana=242,
        move=271,
        max_move=320,
        room_name="Before the southwestern tower",
        room_vnum="11536",
        position=7,
        enemies=[[{"name": "a gigantic frog", "level": "16", "hp": "202"}]],
    )

    flee = policy.next_decision(endpoint)

    assert flee is not None
    assert flee.command == "flee"
    assert policy.fastwalk_resume_hunt_after_interrupt is True
    assert policy.fastwalk_abort_reason is None
    policy.after_command(flee)
    policy.observe_text("You flee from combat!")
    policy.prompt_ready = True

    audit = policy.next_decision(
        CharacterState(
            level=18,
            hp=254,
            max_hp=254,
            mana=242,
            max_mana=242,
            move=271,
            max_move=320,
            room_name="A path uphill",
            room_vnum="11535",
            position=7,
        )
    )

    assert audit is not None
    assert audit.command == "look"
    policy.after_command(audit)
    policy.prompt_ready = True
    policy.fastwalk_post_flee_audit_due = 0.0

    continue_route = policy.next_decision(
        CharacterState(
            level=18,
            hp=254,
            max_hp=254,
            mana=242,
            max_mana=242,
            move=271,
            max_move=320,
            room_name="A path uphill",
            room_vnum="11535",
            position=7,
            exits={"east": "11534", "west": "11536"},
        )
    )

    assert continue_route is not None
    assert continue_route.command == "east"
    assert policy.fastwalk_hunt_stop_index == 1
    assert policy.fastwalk_resume_hunt_after_interrupt is False
    assert policy.fastwalk_abort_reason is None


def test_multistop_research_skips_crowded_endpoint_after_flee_and_continues() -> None:
    route = route_named("highland keeper")
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=highland_keeper_research_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.current_room = "11536"
    policy.combat_active = True
    policy.active_target = "a gigantic frog"
    policy.active_target_level = 16
    policy.active_enemy_count = 1
    policy.room_target_counts["11536"] = {
        "keeper of the tower": 1,
        "a gigantic frog": 1,
    }

    flee = policy.next_decision(
        CharacterState(
            level=18,
            hp=254,
            max_hp=254,
            mana=242,
            max_mana=242,
            move=271,
            max_move=320,
            room_name="Before the southwestern tower",
            room_vnum="11536",
            position=7,
            enemies=[[{"name": "a gigantic frog", "level": "16", "hp": "202"}]],
        )
    )

    assert flee is not None
    assert flee.command == "flee"
    assert policy.fastwalk_resume_hunt_after_interrupt is True
    assert policy.fastwalk_abort_reason is None
    policy.after_command(flee)
    policy.observe_text("You flee from combat!")
    policy.prompt_ready = True

    audit = policy.next_decision(
        CharacterState(
            level=18,
            hp=254,
            max_hp=254,
            mana=242,
            max_mana=242,
            move=271,
            max_move=320,
            room_name="A path uphill",
            room_vnum="11535",
            position=7,
        )
    )

    assert audit is not None
    assert audit.command == "look"
    policy.after_command(audit)
    policy.prompt_ready = True
    policy.fastwalk_post_flee_audit_due = 0.0

    continue_route = policy.next_decision(
        CharacterState(
            level=18,
            hp=254,
            max_hp=254,
            mana=242,
            max_mana=242,
            move=271,
            max_move=320,
            room_name="A path uphill",
            room_vnum="11535",
            position=7,
            exits={"east": "11534", "west": "11536"},
        )
    )

    assert continue_route is not None
    assert continue_route.command == "east"
    assert policy.fastwalk_hunt_stop_index == 1
    assert policy.fastwalk_resume_hunt_after_interrupt is False
    assert policy.fastwalk_abort_reason is None


def test_multistop_research_resumes_registered_waypoint_after_flee() -> None:
    route = route_named("highland keeper")
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=highland_keeper_research_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_stop_index = 1
    policy.fastwalk_hunt_move_index = 8
    policy.current_room = "11524"
    policy.combat_active = True
    policy.active_target = "a gigantic frog"
    policy.active_target_level = 15
    policy.active_enemy_count = 1
    waypoint = CharacterState(
        level=18,
        hp=254,
        max_hp=254,
        mana=242,
        max_mana=242,
        move=271,
        max_move=320,
        room_name="A path uphill",
        room_vnum="11524",
        position=7,
        exits={"e": "11525", "w": "11523"},
        enemies=[[{"name": "a gigantic frog", "level": "15", "hp": "202"}]],
    )

    flee = policy.next_decision(waypoint)

    assert flee is not None
    assert flee.command == "flee"
    assert "resuming the interrupted research waypoint" in flee.reason
    assert policy.fastwalk_resume_current_route_after_interrupt is True
    assert policy.fastwalk_resume_hunt_after_interrupt is False
    assert policy.fastwalk_abort_reason is None
    policy.after_command(flee)
    policy.observe_text("You flee from combat!")
    policy.prompt_ready = True

    safe_waypoint = CharacterState(
        level=18,
        hp=254,
        max_hp=254,
        mana=242,
        max_mana=242,
        move=271,
        max_move=320,
        room_name="A path uphill",
        room_vnum="11524",
        position=7,
        exits={"e": "11525", "w": "11523"},
    )
    audit = policy.next_decision(safe_waypoint)

    assert audit is not None
    assert audit.command == "look"
    policy.after_command(audit)
    policy.prompt_ready = True
    policy.fastwalk_post_flee_audit_due = 0.0

    continue_route = policy.next_decision(safe_waypoint)

    assert continue_route is not None
    assert continue_route.command == "east"
    assert policy.fastwalk_hunt_stop_index == 1
    assert policy.fastwalk_hunt_move_index == 9
    assert policy.fastwalk_resume_current_route_after_interrupt is False
    assert policy.fastwalk_intermediate_route_resume_attempts == {(1, "11524")}
    assert policy.fastwalk_abort_reason is None


def test_multistop_research_rewinds_cursor_after_flee_to_prior_waypoint() -> None:
    route = route_named("highland keeper")
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=highland_keeper_research_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_stop_index = 2
    policy.fastwalk_hunt_move_index = 5
    policy.current_room = "11526"
    policy.combat_active = True
    policy.active_target = "a gigantic frog"
    policy.active_target_level = 15
    policy.active_enemy_count = 1
    waypoint = CharacterState(
        level=18,
        hp=254,
        max_hp=254,
        mana=242,
        max_mana=242,
        move=271,
        max_move=320,
        room_name="A path uphill",
        room_vnum="11526",
        position=7,
        exits={"e": "11527", "w": "11525"},
        enemies=[[{"name": "a gigantic frog", "level": "16", "hp": "202"}]],
    )

    flee = policy.next_decision(waypoint)

    assert flee is not None
    assert flee.command == "flee"
    assert policy.fastwalk_resume_current_route_after_interrupt is True
    policy.after_command(flee)
    policy.observe_text("You flee from combat!")
    policy.prompt_ready = True
    safe_waypoint = CharacterState(
        level=18,
        hp=254,
        max_hp=254,
        mana=242,
        max_mana=242,
        move=271,
        max_move=320,
        room_name="A path uphill",
        room_vnum="11526",
        position=7,
        exits={"e": "11527", "w": "11525"},
    )

    audit = policy.next_decision(safe_waypoint)

    assert audit is not None
    assert audit.command == "look"
    policy.after_command(audit)
    policy.prompt_ready = True
    policy.fastwalk_post_flee_audit_due = 0.0

    resume = policy.next_decision(safe_waypoint)

    assert resume is not None
    assert resume.command == "west"
    assert policy.fastwalk_hunt_move_index == 5
    assert policy.fastwalk_abort_reason is None


def test_multistop_hunt_does_not_adopt_unapproved_waypoint_attacker() -> None:
    route = route_named("highland keeper")
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=highland_keeper_hunt_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_stop_index = 1
    policy.fastwalk_hunt_move_index = 9
    policy.current_room = "11525"
    policy.fastwalk_attack_target = "keeper of the tower"
    policy.combat_active = True
    policy.active_target = "a gigantic frog"
    policy.active_target_level = 16
    policy.active_enemy_count = 1

    decision = policy.next_decision(
        CharacterState(
            level=18,
            hp=254,
            max_hp=254,
            mana=242,
            max_mana=242,
            move=271,
            max_move=320,
            room_name="A path uphill",
            room_vnum="11525",
            position=7,
            exits={"e": "11526", "w": "11524"},
            enemies=[[{"name": "a gigantic frog", "level": "16", "hp": "202"}]],
        )
    )

    assert decision is not None
    assert decision.command == "flee"
    assert policy.fastwalk_resume_current_route_after_interrupt is True
    assert policy.fastwalk_attack_started is False
    assert policy.fastwalk_attack_target == "keeper of the tower"
    assert policy.fastwalk_abort_reason is None


def test_multistop_research_keeps_intermediate_hazard_as_hard_boundary_without_next_exit() -> None:
    route = route_named("highland keeper")
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=highland_keeper_research_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_stop_index = 1
    policy.fastwalk_hunt_move_index = 8
    policy.current_room = "11524"
    policy.combat_active = True
    policy.active_target = "a gigantic frog"
    policy.active_target_level = 15
    policy.active_enemy_count = 1

    decision = policy.next_decision(
        CharacterState(
            level=18,
            hp=254,
            max_hp=254,
            mana=242,
            max_mana=242,
            move=271,
            max_move=320,
            room_name="A path uphill",
            room_vnum="11524",
            position=7,
            exits={"w": "11523"},
            enemies=[[{"name": "a gigantic frog", "level": "15", "hp": "202"}]],
        )
    )

    assert decision is not None
    assert decision.command == "flee"
    assert policy.fastwalk_resume_current_route_after_interrupt is False
    assert policy.fastwalk_resume_hunt_after_interrupt is False
    assert policy.fastwalk_abort_reason == (
        "unexpected combat interrupted a no-combat field probe"
    )


def test_fastwalk_finishes_source_backed_midgaard_drunk_without_fleeing() -> None:
    route = route_named("fleshmonger")
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=fleshmonger_thief_rotation_research_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.active_target = "the drunk"
    policy.active_enemy_count = 1
    policy.field_combat_started_at = time.monotonic()
    policy.fastwalk_outbound_index = 1
    state = CharacterState(
        area="Midgaard",
        room_name="The Temple Square",
        room_vnum="3005",
        level=10,
        hp=154,
        max_hp=154,
        mana=176,
        max_mana=176,
        move=193,
        max_move=240,
        position=6,
    )

    decision = policy.next_decision(state)

    assert decision is None or decision.command != "flee"
    assert policy.fastwalk_emergency_recall_pending is False
    assert policy.fastwalk_attack_started is False


def test_fastwalk_withdraws_if_midgaard_drunk_interruption_becomes_costly() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("fleshmonger"),
        fastwalk_hunt_stops=fleshmonger_thief_rotation_research_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.active_target = "the drunk"
    policy.active_enemy_count = 1
    policy.field_combat_started_at = time.monotonic()
    state = CharacterState(
        area="Midgaard",
        room_name="The Temple Square",
        room_vnum="3005",
        level=10,
        hp=100,
        max_hp=154,
        mana=176,
        max_mana=176,
        move=193,
        max_move=240,
        position=6,
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "flee"
    assert "trivial Midgaard interruption" in decision.reason
    assert policy.fastwalk_emergency_recall_pending is True


def test_post_flee_emergency_return_preempts_world_cache_routing() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_world_cache_preflight_complete = True
    policy.fastwalk_world_cache_post_started = True
    policy.fastwalk_emergency_recall_pending = True
    policy.fastwalk_post_flee_audit_requested = True
    policy.fastwalk_post_flee_audit_due = 0.0

    decision = policy.next_decision(
        CharacterState(
            room_name="Common Road",
            room_vnum="3006",
            area="Midgaard",
            position=7,
        )
    )

    assert decision is not None
    assert decision.command == "recall"
    assert "unexpected combat" in decision.reason
    assert policy.fastwalk_world_cache_post_index == 0


def test_post_flee_emergency_return_uses_healer_route_from_recall() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_world_cache_preflight_complete = True
    policy.fastwalk_world_cache_post_started = True
    policy.fastwalk_emergency_recall_pending = True
    policy.fastwalk_post_flee_audit_requested = True
    policy.fastwalk_post_flee_audit_due = 0.0

    decision = policy.next_decision(
        CharacterState(
            room_name="The Temple Of Midgaard",
            room_vnum="3001",
            area="Midgaard",
            position=7,
        )
    )

    assert decision is not None
    assert decision.command == "north"
    assert "healer" in decision.reason


def test_noop_recall_prompt_at_temple_continues_to_healer() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_world_cache_preflight_complete = True
    policy.fastwalk_world_cache_post_complete = True
    policy.fastwalk_returning = True
    policy.pending_recall_origin = "3001"

    decision = policy.next_decision(
        CharacterState(
            room_name="The Temple Of Midgaard",
            room_vnum="3001",
            area="Midgaard",
            position=7,
        )
    )

    assert decision is not None
    assert decision.command == "north"
    assert policy.pending_recall_origin is None


def test_fastwalk_post_flee_audit_flees_a_new_pursuer_before_recall() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry"),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.fastwalk_emergency_recall_pending = True
    policy.flee_succeeded = True
    pit = CharacterState(room_name="The Pit", room_vnum="122", position=7)

    audit = policy.next_decision(pit)

    assert audit is not None
    assert audit.command == "look"
    policy.after_command(audit)
    policy.prompt_ready = True
    assert policy.next_decision(pit) is None
    pit_beast = [[{"name": "the Pit Beast", "level": "4"}]]
    policy.observe_events(
        [GameEvent("enemies_changed", "gmcp", {"value": pit_beast})],
        CharacterState(enemies=pit_beast, position=6),
    )
    policy.fastwalk_post_flee_audit_due = 0.0

    flee = policy.next_decision(
        CharacterState(
            enemies=pit_beast,
            room_name="The Pit",
            room_vnum="122",
            position=6,
        )
    )

    assert flee is not None
    assert flee.command == "flee"
    assert "post-flee pursuer" in flee.reason


def test_no_combat_probe_does_not_reengage_pursuer_after_flee_audit() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("pyramid ali baba"),
        fastwalk_hunt_stops=pyramid_ali_baba_research_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.fastwalk_emergency_recall_pending = True
    policy.flee_succeeded = True
    state = CharacterState(
        level=18,
        hp=254,
        max_hp=254,
        room_name="The Great Eastern Desert",
        room_vnum="5030",
        position=7,
    )

    audit = policy.next_decision(state)
    assert audit is not None and audit.command == "look"
    policy.after_command(audit)
    policy.prompt_ready = True
    assert policy.next_decision(state) is None
    policy.fastwalk_post_flee_audit_due = 0.0
    pursuer = [[{"name": "the dustdigger", "level": "8", "hp": "100"}]]

    flee = policy.next_decision(
        CharacterState(
            level=18,
            hp=254,
            max_hp=254,
            room_name="The Great Eastern Desert",
            room_vnum="5030",
            position=6,
            enemies=pursuer,
        )
    )

    assert flee is not None
    assert flee.command == "flee"
    assert "post-flee pursuer" in flee.reason


def test_field_hunt_adopts_lone_attacker_that_blocks_a_movement_step() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=ambush_martial_level_eight_hunt_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.pending_travel_origin = "3555"
    policy.pending_fastwalk_hunt_move = True
    policy.combat_active = True
    policy.active_target = "the goblin lieutenant"
    policy.active_target_level = 7
    policy.active_enemy_count = 1
    state = CharacterState(
        level=8,
        hp=135,
        max_hp=135,
        mana=151,
        max_mana=151,
        room_name="The Ambush Point",
        room_vnum="3555",
        position=6,
        enemies=[[{"name": "the goblin lieutenant", "level": "7"}]],
    )

    decision = policy.next_decision(state)

    assert decision is None
    assert policy.fastwalk_attack_started is True
    assert policy.fastwalk_attack_target == "the goblin lieutenant"
    assert policy.fastwalk_returning is False
    assert policy.fastwalk_abort_reason is None


def test_field_hunt_waits_one_cycle_before_missing_gmcp_withdrawal() -> None:
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

    decision = policy.next_decision(state)

    assert decision is None
    assert policy.awaiting_enemy_assessment is True

    policy.prompt_ready = True
    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "flee"
    assert policy.fastwalk_emergency_recall_pending is True


def test_field_hunt_adopts_text_attacker_after_delayed_gmcp_assessment() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "warrior", "subclass": "knight"}),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=ambush_martial_level_eight_hunt_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.observe_text(
        "The South Bridge\n"
        "[Exits: north south]\n"
        "A goblin lieutenant stands here, attempting to get his men in order.\n"
        "The goblin lieutenant scratches you.\n"
    )
    state = CharacterState(
        level=9,
        hp=189,
        max_hp=197,
        mana=146,
        max_mana=146,
        room_name="The South Bridge",
        room_vnum="3504",
        position=6,
    )

    assert policy.next_decision(state) is None
    assert policy.active_target == "The goblin lieutenant"
    assert policy.awaiting_enemy_assessment is True

    enemies = [[{"name": "the goblin lieutenant", "level": "7", "hp": "97"}]]
    policy.observe_events(
        [GameEvent("enemies_changed", "gmcp", {"value": enemies})],
        CharacterState(
            level=9,
            hp=189,
            max_hp=197,
            mana=146,
            max_mana=146,
            room_name="The South Bridge",
            room_vnum="3504",
            position=6,
            enemies=enemies,
        ),
    )

    decision = policy.next_decision(
        CharacterState(
            level=9,
            hp=189,
            max_hp=197,
            mana=146,
            max_mana=146,
            room_name="The South Bridge",
            room_vnum="3504",
            position=6,
            enemies=enemies,
        )
    )

    assert decision is None
    assert policy.fastwalk_attack_started is True
    assert policy.fastwalk_attack_target == "the goblin lieutenant"
    assert policy.fastwalk_emergency_recall_pending is False


def test_incoming_damage_text_with_unknown_attacker_flees_field_combat() -> None:
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
    policy.fastwalk_hunt_stop_index = 0
    policy.fastwalk_hunt_move_index = len(
        policy.fastwalk_hunt_stops[0].route
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
        room_name="Lower Chamber",
        room_vnum="120",
    )

    policy.observe_text("Ushog's slash injures you! Ushog is in excellent condition.")
    decision = policy.next_decision(state)

    assert policy.combat_active is True
    assert policy.awaiting_enemy_assessment is True
    assert decision is None

    policy.prompt_ready = True
    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "flee"
    assert policy.fastwalk_emergency_recall_pending is True


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


def test_fastwalk_flees_when_a_second_attacker_joins_field_combat() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
        fastwalk_attack_target="bull",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_attack_started = True
    policy.combat_active = True
    policy.active_target = "bull"
    policy.observe_text("The Thain's slash hits you.")

    decision = policy.next_decision(
        CharacterState(
            level=7,
            hp=123,
            max_hp=123,
            position=7,
            room_name="A grassy field",
            room_vnum="1138",
        )
    )

    assert decision is not None
    assert decision.command == "flee"
    assert "unapproved attacker" in decision.reason
    assert policy.fastwalk_abort_reason == (
        "field combat aborted after unapproved attacker 'The Thain' joined"
    )


def test_fastwalk_does_not_treat_poison_damage_as_a_joining_attacker() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
        fastwalk_attack_target="snake",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_attack_started = True
    policy.combat_active = True
    policy.active_target = "snake"
    policy.observe_text("Your poisoned blood scratches you.")

    decision = policy.next_decision(
        CharacterState(
            level=14,
            hp=201,
            max_hp=205,
            position=7,
            room_name="The maze",
            room_vnum="4058",
        )
    )

    assert decision is not None
    assert decision.command != "flee"
    assert policy.unapproved_field_attacker is None
    assert policy.fastwalk_abort_reason is None


def test_fastwalk_keeps_fighting_when_live_level_proves_joiner_below_band() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
        fastwalk_attack_target="bull",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_attack_started = True
    policy.combat_active = True
    policy.active_target = "bull"
    policy.observe_text("The Thain's slash hits you.")
    state = CharacterState(
        level=9,
        hp=150,
        max_hp=180,
        mana=140,
        max_mana=140,
        position=6,
        room_name="A grassy field",
        room_vnum="1138",
        enemies=[[
            {"name": "bull", "level": "7", "hp": "50", "maxhp": "80"},
            {"name": "The Thain", "level": "4", "hp": "15", "maxhp": "15"},
        ]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "cast 'magic missile' bull"
    assert policy.unapproved_field_attacker is None
    assert policy.fastwalk_emergency_recall_pending is False
    assert policy.fastwalk_abort_reason is None
    assert policy.active_target == "bull"


def test_fastwalk_keeps_fighting_source_registered_trivial_joiner() -> None:
    route = route_named("circus bearded lady")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=circus_freak_show_hunt_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_attack_started = True
    policy.fastwalk_hunt_stop_index = 3
    policy.combat_active = True
    policy.active_target = "Ivan the Strongman"
    policy.observe_text("Little Bobby's punch misses you.")

    decision = policy.next_decision(
        CharacterState(
            level=9,
            hp=160,
            max_hp=190,
            mana=140,
            max_mana=140,
            position=6,
            room_name="The Strongman's Tent",
            room_vnum="4413",
        )
    )

    assert decision is not None
    assert decision.command == "cast 'magic missile' Strongman"
    assert policy.unapproved_field_attacker is None
    assert policy.fastwalk_emergency_recall_pending is False
    assert policy.fastwalk_abort_reason is None


def test_enemy_snapshot_preserves_planned_target_when_trivial_joiner_is_first() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("circus bearded lady"),
        fastwalk_attack_target="Ivan the Strongman",
    )
    policy.active_target = "Ivan the Strongman"
    state = CharacterState(level=9)

    policy.observe_events(
        [
            GameEvent(
                "enemies_changed",
                "gmcp",
                {
                    "value": [[
                        {"name": "Little Bobby", "level": "3"},
                        {"name": "Ivan", "level": "7"},
                    ]]
                },
            )
        ],
        state,
    )

    assert policy.active_target == "Ivan"
    assert policy.active_target_level == 7


def test_fastwalk_flees_when_field_combat_exceeds_bounded_duration() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_attack_target="wounded goblin",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_attack_started = True
    policy.combat_active = True
    policy.active_target = "wounded goblin"
    policy.field_combat_started_at = time.monotonic() - 361

    decision = policy.next_decision(
        CharacterState(
            level=8,
            hp=135,
            max_hp=135,
            position=7,
            room_name="In a forest clearing",
            room_vnum="4510",
        )
    )

    assert decision is not None
    assert decision.command == "flee"
    assert "bounded duration" in decision.reason
    assert policy.fastwalk_emergency_recall_pending is True
    assert policy.fastwalk_abort_reason == (
        "field combat exceeded the 360-second bounded duration"
    )


def test_fastwalk_repeated_attack_from_adopted_mobile_is_not_a_joiner() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=ambush_martial_level_eight_hunt_stops(),
    )
    policy.in_world = True

    policy.observe_text("The goblin lieutenant's slash misses you.")
    policy.observe_text("The goblin lieutenant's slash grazes you.")

    assert policy.combat_active is True
    assert policy.active_target == "The goblin lieutenant"
    assert policy.unapproved_field_attacker is None


def test_fastwalk_accepts_short_proper_name_for_full_room_target() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("circus bearded lady"),
        fastwalk_attack_target="Ivan the Strongman",
    )
    policy.fastwalk_attack_started = True
    policy.combat_active = True

    policy.observe_text("Ivan misses you.")

    assert policy.unapproved_field_attacker is None


def test_fastwalk_flees_when_attacked_before_target_is_established() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
        fastwalk_hunt_stops=foundry_level_six_hunt_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.observe_text("A dark horseman's slash hits you.")

    decision = policy.next_decision(
        CharacterState(
            level=7,
            hp=123,
            max_hp=123,
            position=7,
            room_name="The South Bridge",
            room_vnum="3505",
        )
    )

    assert decision is not None
    assert decision.command == "flee"
    assert policy.fastwalk_abort_reason == (
        "field combat aborted after unapproved attacker 'A dark horseman' joined"
    )


def test_fastwalk_flees_and_recalls_when_field_health_reaches_withdrawal_threshold() -> None:
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
        hp=14,
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
    assert "15%" in flee.reason
    assert policy.fastwalk_emergency_recall_pending is True
    assert policy.fastwalk_abort_reason is not None
    policy.after_command(flee)
    policy.prompt_ready = True
    assert policy.next_decision(state) is None

    policy.observe_text("You flee from combat!\n")
    policy.prompt_ready = True

    audit = policy.next_decision(state)

    assert audit is not None
    assert audit.command == "look"
    policy.after_command(audit)
    policy.prompt_ready = True
    policy.fastwalk_post_flee_audit_due = 0.0

    recall = policy.next_decision(state)

    assert recall is not None
    assert recall.command == "recall"


def test_fastwalk_finishes_lower_level_half_dead_attacker_above_thirty_percent() -> None:
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


def test_field_stop_combat_floor_overrides_aggressive_finisher() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(
            FieldHuntStop(
                (),
                "goblin looter",
                minimum_combat_health_ratio=0.5,
            ),
        ),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_attack_started = True
    policy.combat_active = True
    policy.active_target = "The goblin looter"
    state = CharacterState(
        level=8,
        hp=49,
        max_hp=100,
        mana=200,
        max_mana=240,
        position=6,
        room_name="Ambush trail",
        room_vnum="4507",
        enemies=[
            [
                {
                    "name": "The goblin looter",
                    "level": "7",
                    "hp": "29",
                    "maxhp": "70",
                }
            ]
        ],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "flee"
    assert "50%" in decision.reason


def test_fastwalk_continues_even_fight_above_forty_percent_health() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(FieldHuntStop((), "goblin"),),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_attack_started = True
    policy.combat_active = True
    policy.active_target = "the goblin"
    state = CharacterState(
        level=9,
        hp=41,
        max_hp=100,
        mana=200,
        max_mana=240,
        position=6,
        room_name="The Front of the Inn",
        room_vnum="3570",
        enemies=[[
            {
                "name": "the goblin",
                "level": "9",
                "hp": "80",
                "maxhp": "80",
            }
        ]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "cast 'magic missile' goblin"
    assert policy.fastwalk_abort_reason is None


def test_field_combat_flees_first_snapshot_above_stop_level_ceiling() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("fleshmonger"),
        fastwalk_hunt_stops=(
            FieldHuntStop(
                (),
                "on-duty guard",
                maximum_level_offset=0,
            ),
        ),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_attack_started = True
    policy.combat_active = True
    policy.active_target = "the on-duty guard"
    state = CharacterState(
        level=10,
        hp=129,
        max_hp=154,
        mana=176,
        max_mana=176,
        position=6,
        room_name="A Guard Room",
        room_vnum="9401",
        enemies=[[
            {
                "name": "the on-duty guard",
                "level": "11",
                "hp": "162",
                "maxhp": "169",
            }
        ]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "flee"
    assert "first combat snapshot" in decision.reason
    assert policy.fastwalk_emergency_recall_pending is True
    assert "above the verified live ceiling" in policy.fastwalk_abort_reason


def test_fastwalk_keeps_fighting_hungry_when_usable_food_is_carried() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(FieldHuntStop((), "goblin"),),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(policy.fastwalk_route.commands)
    policy.fastwalk_attack_started = True
    policy.combat_active = True
    policy.active_target = "the goblin"
    policy.needs_food = True
    state = CharacterState(
        level=7,
        hp=80,
        max_hp=100,
        mana=200,
        max_mana=240,
        position=6,
        room_name="The Front of the Inn",
        room_vnum="3570",
        inventory=[[{"short_desc": "a big pot pie"}]],
        enemies=[[
            {
                "name": "the goblin",
                "level": "7",
                "hp": "80",
                "maxhp": "80",
            }
        ]],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "cast 'magic missile' goblin"
    assert policy.fastwalk_abort_reason is None


def test_fastwalk_sleeps_locally_after_kill_at_vetted_stop() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("circus bearded lady"),
        fastwalk_hunt_stops=(
            FieldHuntStop((), "Bearded Lady", allow_local_recovery=True),
            FieldHuntStop(("east",), "Illusionist"),
        ),
    )
    policy.fastwalk_hunt_stop_killed = True
    state = CharacterState(
        hp=20,
        max_hp=100,
        mana=200,
        max_mana=240,
        move=150,
        max_move=200,
        position=7,
        room_name="The Tent of the Bearded Lady",
        room_vnum="4409",
    )

    decision = policy._fastwalk_hunt_plan_decision(state)

    assert decision is not None
    assert decision.command == "sleep"
    assert policy.waiting_for_heal is True


def test_fastwalk_continues_circuit_above_aggressive_reserves() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(FieldHuntStop(("south",), "goblin"),),
    )
    state = CharacterState(
        hp=56,
        max_hp=100,
        mana=21,
        max_mana=100,
        move=16,
        max_move=100,
        position=7,
        room_name="Deep Forest",
        room_vnum="3514",
    )

    decision = policy._fastwalk_hunt_plan_decision(state)

    assert decision is not None
    assert decision.command == "south"
    assert policy.fastwalk_returning is False


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


def test_fastwalk_rejects_opportunistic_attacker_beside_source_known_danger() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=midennir_mountain_goblin_hunt_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.current_room = "3505"
    policy.room_target_counts["3505"] = {
        "goblin lieutenant": 1,
        "dark horseman": 1,
    }
    state = CharacterState(
        level=8,
        hp=120,
        max_hp=120,
        mana=216,
        max_mana=327,
        room_name="The Trail to Miden'nir",
        room_vnum="3505",
        position=6,
        enemies=[[{"name": "the goblin lieutenant", "level": "7"}]],
    )
    policy.observe_events(
        [
            GameEvent(
                "enemies_changed",
                "gmcp",
                {"value": [[{"name": "the goblin lieutenant", "level": "7"}]]},
            )
        ],
        state,
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "flee"
    assert policy.fastwalk_attack_started is False


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


def test_fastwalk_text_initial_attacker_reaches_trivial_enemy_gate() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=gnome_hermit_hunt_route(),
        fastwalk_hunt_stops=gnome_hermit_hunt_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.known_skills.add("chill touch")
    state = CharacterState(
        level=7,
        hp=110,
        max_hp=110,
        mana=293,
        max_mana=293,
        room_name="The Temple Square",
        room_vnum="3005",
        position=6,
    )

    policy.observe_text(
        "The drunk yells exclaiming 'Monster! Kill! Banzai!'\n"
        "The drunk scratches you.\n"
    )
    policy.observe_events(
        [
            GameEvent(
                "enemies_changed",
                "gmcp",
                {"value": [[{"name": "the drunk", "level": "1", "hp": "8"}]]},
            )
        ],
        state,
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "cast 'chill touch' drunk"
    assert policy.unapproved_field_attacker is None
    assert policy.fastwalk_attack_target == "the drunk"
    assert policy.fastwalk_attack_started is True


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


@pytest.mark.parametrize(
    ("step", "room_vnum", "exits", "expected"),
    (
        (0, "6612", {"e": "6613", "u": "6607"}, "east"),
        (
            1,
            "6613",
            {"n": "6615", "e": "6614", "w": "6612"},
            "east",
        ),
        (2, "6614", {"n": "6616", "w": "6613"}, "north"),
        (3, "6616", {"n": "6614", "w": "6615", "s": "6624"}, "south"),
    ),
)
def test_daycare_maze_follows_destination_vnums_despite_exit_shuffle(
    step: int,
    room_vnum: str,
    exits: dict[str, str],
    expected: str,
) -> None:
    route = daycare_armed_guard_hunt_route()
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=daycare_armed_guard_hunt_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    policy.fastwalk_hunt_move_index = step
    state = CharacterState(
        level=8,
        hp=177,
        max_hp=177,
        mana=142,
        max_mana=142,
        move=180,
        max_move=220,
        position=7,
        room_vnum=room_vnum,
        exits=exits,
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == expected
    assert str(policy.fastwalk_hunt_stops[0].route_vnums[step]) in decision.reason


def test_field_stop_continues_fixed_route_after_destination_vnums() -> None:
    route = route_named("hightower jailor")
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(
            FieldHuntStop(
                ("open down", "down", "east"),
                "jailor",
                route_vnums=("1308",),
            ),
        ),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    policy.fastwalk_hunt_move_index = 1
    policy.current_room = "1308"
    state = CharacterState(
        level=17,
        hp=242,
        max_hp=242,
        mana=235,
        max_mana=235,
        move=247,
        max_move=310,
        position=7,
        room_vnum="1308",
        exits={"w": "1305"},
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "open down"
    assert policy.fastwalk_hunt_move_index == 2


def test_fleshmonger_guard_research_stop_is_exact_and_consider_only() -> None:
    stops = fleshmonger_guard_research_stops()

    assert len(stops) == 1
    assert stops[0].target == "patrolling guard"
    assert stops[0].exact_target is True
    assert stops[0].consider_only is True
    assert stops[0].route == ()


def test_plains_aruncus_research_checks_the_source_backed_safe_area_loop() -> None:
    stops = plains_aruncus_research_stops()
    grassy_circuit = [
        "330", "319", "318", "316", "300", "315", "320", "305",
        "321", "338", "317", "303", "315", "320", "322", "324",
        "323",
    ]
    broad_grassy_circuit = [
        "330", "319", "318", "316", "300", "301", "302", "303",
        "304", "305", "321", "338", "317", "303", "315", "320",
        "322", "324", "323",
    ]

    assert stops[0].route == ()
    observed_vnums = [
        stop.route_vnums[0] for stop in stops[1:] if stop.route_vnums
    ]
    assert stops[1].route_vnums == ("330",)
    assert stops[2].route == ("open west", "west")
    assert stops[2].route_vnums == ()
    assert stops[3].route == ("open east", "east")
    assert stops[3].route_vnums == ()
    assert observed_vnums[:53] == broad_grassy_circuit + grassy_circuit * 2
    assert observed_vnums[-4:] == ["341", "340", "342", "343"]
    assert [stop.target for stop in stops] == ["Aruncus the Druid"] * 85
    assert stops[0].actions == ("where aruncus",)
    assert sum(stop.actions == ("where aruncus",) for stop in stops) == 4
    assert all(stop.command_keyword == "aruncus" for stop in stops)
    assert all(stop.consider_only and stop.exact_target for stop in stops)
    assert all("the cute rabbit" in stop.trivial_bystanders for stop in stops)
    assert all("the citizen" in stop.trivial_bystanders for stop in stops)


def test_mirror_realm_watchman_probe_uses_exact_source_room() -> None:
    first, second = mirror_realm_watchman_research_stops()

    assert first.target == "watchman"
    assert first.command_keyword == "watchman"
    assert first.consider_only is True
    assert first.exact_target is True
    assert first.maximum_level_offset == 1
    assert first.abort_after_consider_rejection is True
    assert first.route_vnums == ()
    assert second.target == "watchman"
    assert second.command_keyword == "watchman"
    assert second.consider_only is True
    assert second.exact_target is True
    assert second.maximum_level_offset == 1
    assert second.abort_after_consider_rejection is True
    assert second.route == ("east", "east")
    assert second.route_vnums == ("19008", "19010")


def test_watchman_perfect_match_ignores_separate_hp_addendum() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("mirror realm watchman"),
        fastwalk_hunt_stops=mirror_realm_watchman_research_stops(),
    )
    policy.consider_target = "watchman"

    policy.observe_text(
        "The perfect match! Also, he is much healthier than you.\n"
    )

    assert policy.consider_viable is True


def test_crystalmir_white_stag_probe_searches_only_low_risk_reachable_rooms() -> None:
    stops = crystalmir_white_stag_research_stops()
    destinations = [stop.route_vnums[0] for stop in stops[1:]]

    assert len(stops) == 67
    assert stops[0].target == "beautiful white stag"
    assert stops[0].command_keyword == "stag"
    assert stops[0].actions == ("where stag",)
    assert stops[0].abort_if_where_target_absent is True
    assert all(stop.consider_only and stop.exact_target for stop in stops)
    assert {"10005", "10030", "10039"}.isdisjoint(destinations)
    assert {
        "10001", "10002", "10003", "10004", "10006", "10007", "10008",
        "10009", "10010", "10011", "10012", "10013", "10014", "10015",
        "10016", "10017", "10019", "10020", "10021", "10022", "10023",
        "10025", "10026", "10027", "10028", "10029", "10031", "10032",
        "10033", "10034", "10035", "10036", "10037", "10038",
    } == set(destinations) | {"10016"}


def test_crystalmir_probe_flees_a_fewmaster_route_hazard_before_attacking() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("crystalmir white stag"),
        fastwalk_hunt_stops=crystalmir_white_stag_research_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    enemies = [[{"name": "Fewmaster Toede", "level": "12", "hp": "218"}]]
    state = CharacterState(
        level=18,
        hp=254,
        max_hp=254,
        mana=242,
        max_mana=242,
        move=307,
        max_move=320,
        room_name="Jakanth Vale",
        room_vnum="10016",
        position=6,
        enemies=enemies,
    )

    policy.observe_events(
        [GameEvent("enemies_changed", "gmcp", {"value": enemies})],
        state,
    )
    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "flee"
    assert "Fewmaster Toede" in decision.reason
    assert policy.fastwalk_emergency_recall_pending is True


def test_where_absence_latch_survives_prompt_overwrite() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("crystalmir white stag"),
        fastwalk_hunt_stops=crystalmir_white_stag_research_stops(),
    )
    policy.fastwalk_hunt_looked = True
    policy.fastwalk_hunt_action_index = 1

    policy.observe_text("You fail to find anyone by that name.\n")
    policy.observe_text("<254/254 hp 242/242 mana 320/320 mv>\n")

    decision = policy._fastwalk_hunt_plan_decision(
        CharacterState(
            level=18,
            hp=254,
            max_hp=254,
            mana=242,
            max_mana=242,
            move=320,
            max_move=320,
            room_vnum="10016",
        )
    )

    assert policy.fastwalk_where_target_absent_observed is True
    assert policy.fastwalk_target_absent is True
    assert decision is not None
    assert decision.command == "recall"


def test_crystalmir_white_stag_hunt_reconsiders_one_bounded_target() -> None:
    stops = crystalmir_white_stag_hunt_stops()

    assert all(stop.consider_only is False for stop in stops)
    assert all(stop.minimum_health_ratio == 0.85 for stop in stops)
    assert all(stop.maximum_level_offset == 1 for stop in stops)


def test_repeated_consider_target_preserves_any_viable_outcome() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("mirror realm watchman"),
        fastwalk_hunt_stops=mirror_realm_watchman_research_stops(),
    )
    policy.consider_target = "watchman"

    policy.observe_text("The perfect match! Also, you are healthier than he.\n")
    policy.consider_viable = None
    policy.observe_text(
        "He would have to be dreadfully unlucky to lose to you. "
        "Also, he has more than 100 hit points on you.\n"
    )

    assert policy.fastwalk_consider_outcomes == {"watchman": True}


def test_shadow_keep_soldier_probe_uses_exact_source_identity() -> None:
    first_soldier, second_soldier, third_soldier, first_wraith, second_wraith = (
        shadow_keep_soldier_research_stops()
    )

    assert first_soldier.target == "undead soldier"
    assert first_soldier.command_keyword == "soldier"
    assert first_soldier.consider_only is True
    assert first_soldier.exact_target is True
    assert first_soldier.route_vnums == ()
    assert second_soldier.route == (
        "west",
        "north",
        "north",
        "west",
        "up",
    )
    assert second_soldier.target == "undead soldier"
    assert third_soldier.route == (
        "down",
        "east",
        "south",
        "west",
        "west",
    )
    assert third_soldier.target == "undead soldier"
    assert first_wraith.route == ("east", "east", "east")
    assert first_wraith.target == "shadow wraith"
    assert first_wraith.command_keyword == "wraith"
    assert first_wraith.consider_only is True
    assert first_wraith.exact_target is True
    assert second_wraith.route == ("east", "south", "east")
    assert second_wraith.target == "shadow wraith"
    assert second_wraith.exact_target is True


def test_shadow_keep_soldier_hunt_reconsiders_one_bounded_target() -> None:
    stops = shadow_keep_soldier_hunt_stops()

    assert len(stops) == 5
    assert all(stop.consider_only is False for stop in stops)
    assert all(stop.minimum_health_ratio == 0.85 for stop in stops)
    assert all(stop.maximum_level_offset == 1 for stop in stops)
    assert all(stop.exact_target is True for stop in stops)


def test_highland_keeper_probe_requires_exact_isolation() -> None:
    stops = highland_keeper_research_stops()

    assert len(stops) == 4
    assert [stop.target for stop in stops] == ["keeper of the tower"] * 4
    assert all(stop.command_keyword == "keeper" for stop in stops)
    assert all(stop.consider_only is True for stop in stops)
    assert all(stop.exact_target is True for stop in stops)
    assert all(stop.require_isolated is True for stop in stops)
    assert all(stop.maximum_target_count == 1 for stop in stops)
    assert all(stop.maximum_level_offset == 1 for stop in stops)
    assert all(stop.trivial_bystanders == ("hideous bogleech",) for stop in stops)
    assert [stop.route_vnums for stop in stops] == [
        ("11536",),
        (
            "11535", "11534", "11533", "11532", "11531", "11522",
            "11523", "11524", "11525", "11526", "11527", "11528",
            "11529", "11530",
        ),
        (
            "11529", "11528", "11527", "11526", "11525", "11524",
            "11523", "11522", "11537", "11538", "11539", "11572",
            "11571", "11570", "11569", "11568", "11567", "11566",
            "11565", "11564", "11563", "11562", "11561", "11578",
            "11579", "11580", "11581", "11582", "11583", "11584",
        ),
        (
            "11583", "11582", "11581", "11580", "11579", "11578",
            "11561", "11560", "11559", "11558", "11557", "11556",
            "11555", "11554", "11553", "11552", "11585", "11586",
            "11587", "11588", "11589", "11590", "11591",
        ),
    ]


def test_highland_keeper_hunt_retains_probe_safety_gates() -> None:
    stops = highland_keeper_hunt_stops()

    assert len(stops) == 4
    assert all(stop.consider_only is False for stop in stops)
    assert all(stop.minimum_health_ratio == 0.85 for stop in stops)
    assert all(stop.exact_target is True for stop in stops)
    assert all(stop.require_isolated is True for stop in stops)
    assert all(stop.maximum_level_offset == 1 for stop in stops)


def test_highland_keeper_crowd_advances_to_next_source_reset() -> None:
    stops = highland_keeper_research_stops()
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("highland keeper"),
        fastwalk_hunt_stops=stops,
    )
    policy.current_room = "11536"
    policy.fastwalk_attack_target = "keeper of the tower"
    policy.room_targets["11536"] = ["keeper of the tower", "sheep"]
    policy.room_target_counts["11536"] = {
        "keeper of the tower": 1,
        "sheep": 1,
    }

    decision = policy._consider_fastwalk_target(
        CharacterState(
            level=18,
            hp=254,
            max_hp=254,
            mana=242,
            max_mana=242,
            move=252,
            max_move=320,
            position=7,
            room_vnum="11536",
            exits={"e": "11535"},
        )
    )

    assert decision is not None
    assert decision.command == "look"
    assert policy.fastwalk_hunt_stop_skipped is True
    assert policy.fastwalk_abort_reason is None

    next_decision = policy._fastwalk_hunt_plan_decision(
        CharacterState(
            level=18,
            hp=254,
            max_hp=254,
            mana=242,
            max_mana=242,
            move=252,
            max_move=320,
            position=7,
            room_vnum="11536",
            exits={"e": "11535"},
        )
    )

    assert next_decision is not None
    assert next_decision.command == "east"
    assert policy.fastwalk_hunt_stop_index == 1
    assert policy.fastwalk_hunt_move_index == 1


def test_mirror_realm_gardener_probe_uses_exact_source_room() -> None:
    (stop,) = mirror_realm_gardener_research_stops()

    assert stop.target == "the gardener"
    assert stop.command_keyword == "gardener"
    assert stop.consider_only is True
    assert stop.exact_target is True
    assert stop.route_vnums == ("19091",)


def test_mirror_realm_gardener_hunt_reconsiders_one_bounded_target() -> None:
    (stop,) = mirror_realm_gardener_hunt_stops()

    assert stop.target == "the gardener"
    assert stop.command_keyword == "gardener"
    assert stop.consider_only is False
    assert stop.minimum_health_ratio == 0.85
    assert stop.maximum_level_offset == 1
    assert stop.exact_target is True
    assert stop.route_vnums == ("19091",)


def test_shire_battle_master_probe_uses_exact_source_room() -> None:
    (stop,) = shire_battle_master_research_stops()

    assert stop.target == "the battle master"
    assert stop.command_keyword == "battle"
    assert stop.consider_only is True
    assert stop.exact_target is True
    assert stop.route_vnums == ("1117",)


def test_plains_aruncus_hunt_stops_preserve_route_and_bound_source_fuzz() -> None:
    stops = plains_aruncus_hunt_stops()

    assert len(stops) == 85
    assert [stop.target for stop in stops] == ["Aruncus the Druid"] * 85
    assert stops[0].actions == ("where aruncus",)
    assert all(
        stop.selective_loot_keywords == ("staff", "scroll", "ivy")
        for stop in stops
    )
    assert stops[0].abort_if_where_target_absent is True
    assert stops[1].route_vnums == ("330",)
    assert stops[2].route == ("open west", "west")
    assert stops[3].route == ("open east", "east")
    assert all(not stop.consider_only for stop in stops)
    assert all(stop.minimum_health_ratio == 0.85 for stop in stops)
    assert all(stop.maximum_level_offset == 2 for stop in stops)
    assert all(stop.exact_target for stop in stops)


def test_fastwalk_where_absence_aborts_remaining_area_search() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=forest_bear_claws_hunt_route(),
        fastwalk_hunt_stops=forest_bear_claws_hunt_stops(),
    )
    policy.fastwalk_hunt_looked = True
    policy.fastwalk_hunt_action_index = 1
    policy.last_response = (
        "You fail to find anyone by that name.\n"
        "<205/205 hits 207/207 mana 222/280 move [Forest]>"
    )
    state = CharacterState(
        level=14,
        hp=205,
        max_hp=205,
        mana=207,
        max_mana=207,
        move=222,
        max_move=280,
        position=7,
        room_vnum="18026",
    )

    decision = policy._fastwalk_hunt_plan_decision(state)

    assert decision is not None
    assert decision.command == "recall"
    assert policy.fastwalk_returning is True
    assert policy.fastwalk_target_absent is True
    assert policy.fastwalk_abort_reason == (
        "`where` confirmed 'giant kodiak bear' absent from the current area"
    )


def test_fastwalk_where_absence_records_explicit_locator_identity() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_hunt_stops=(
            FieldHuntStop(
                (),
                where_target="horsehead nebula",
                actions=("where horsehead",),
                abort_if_where_target_absent=True,
            ),
        ),
    )
    policy.fastwalk_hunt_looked = True
    policy.fastwalk_hunt_action_index = 1
    policy.last_response = "You fail to find anyone by that name."
    state = CharacterState(
        level=18,
        hp=205,
        max_hp=205,
        mana=207,
        max_mana=207,
        move=222,
        max_move=280,
        position=7,
        room_vnum="9304",
    )

    decision = policy._fastwalk_hunt_plan_decision(state)

    assert decision is not None
    assert decision.command == "recall"
    assert policy.fastwalk_abort_reason == (
        "`where` confirmed 'horsehead nebula' absent from the current area"
    )


def test_fastwalk_where_unsafe_room_aborts_without_marking_target_absent() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=forest_bear_claws_hunt_route(),
        fastwalk_hunt_stops=forest_bear_claws_hunt_stops(),
    )
    policy.fastwalk_hunt_looked = True
    policy.fastwalk_hunt_action_index = 1
    policy.last_response = (
        "You detect the presence of:\n"
        "A Giant Kodiak bear          River bed\n"
        "<205/205 hits 207/207 mana 208/280 move [Forest]>"
    )
    state = CharacterState(
        level=14,
        hp=205,
        max_hp=205,
        mana=207,
        max_mana=207,
        move=208,
        max_move=280,
        position=7,
        room_vnum="18026",
    )

    decision = policy._fastwalk_hunt_plan_decision(state)

    assert decision is not None
    assert decision.command == "recall"
    assert policy.fastwalk_returning is True
    assert policy.fastwalk_target_absent is False
    assert policy.fastwalk_abort_reason == (
        "`where` located 'giant kodiak bear' in excluded room 'River bed'"
    )


def test_route_preflight_allows_a_clear_shadow_grove_boundary() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("galaxy horsehead nebula"),
        fastwalk_hunt_stops=galaxy_horsehead_nebula_research_stops(),
    )
    state = CharacterState(
        level=18,
        hp=205,
        max_hp=205,
        mana=207,
        max_mana=207,
        move=280,
        max_move=280,
        room_vnum="1300",
    )

    decision = policy._fastwalk_route_preflight_decision(state)
    assert decision is not None
    assert decision.command == "where shadow guardian"

    policy.observe_text("You fail to find anyone by that name.")

    assert policy._fastwalk_route_preflight_decision(state) is None
    assert policy.fastwalk_route_preflight_complete is True
    assert policy.fastwalk_abort_reason is None


def test_route_preflight_recalls_before_a_shadow_grove_hazard() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("galaxy horsehead nebula"),
        fastwalk_hunt_stops=galaxy_horsehead_nebula_research_stops(),
    )
    state = CharacterState(
        level=18,
        hp=205,
        max_hp=205,
        mana=207,
        max_mana=207,
        move=280,
        max_move=280,
        room_vnum="1300",
    )

    assert policy._fastwalk_route_preflight_decision(state).command == (
        "where shadow guardian"
    )
    policy.observe_text(
        "You detect the presence of:\n"
        "A shadow guardian          The Shadow Grove\n"
    )

    decision = policy._fastwalk_route_preflight_decision(state)

    assert decision is not None
    assert decision.command == "recall"
    assert policy.fastwalk_returning is True
    assert policy.fastwalk_abort_reason == (
        "field route preflight found source-registered hazard "
        "'shadow guardian' in room 1300"
    )


def test_route_preflight_keeps_hard_below_band_hazard_blocked() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("galaxy horsehead nebula"),
        fastwalk_hunt_stops=galaxy_horsehead_nebula_research_stops(),
        source_mobile_level_ranges={
            "shadow guardian": (7, 11),
            "an ancient shadow guardian": (99, 101),
        },
    )
    state = CharacterState(
        level=18,
        hp=205,
        max_hp=205,
        mana=207,
        max_mana=207,
        move=280,
        max_move=280,
        room_vnum="1300",
    )

    assert policy._fastwalk_route_preflight_decision(state).command == (
        "where shadow guardian"
    )
    policy.observe_text(
        "You detect the presence of:\n"
        "A shadow guardian          The Shadow Grove\n"
    )

    decision = policy._fastwalk_route_preflight_decision(state)

    assert decision is not None
    assert decision.command == "recall"
    assert policy.fastwalk_route_preflight_complete is True
    assert policy.fastwalk_returning is True
    assert policy.fastwalk_abort_reason == (
        "field route preflight found source-registered hazard "
        "'shadow guardian' in room 1300"
    )


def test_active_hard_route_hazard_cannot_resume_a_randomized_waypoint() -> None:
    route = route_named("galaxy white dwarf")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=galaxy_white_dwarf_research_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_stop_index = 0
    policy.fastwalk_hunt_move_index = 1
    policy.current_room = "1308"
    policy.combat_active = True
    policy.active_target = "a shadow guardian"
    policy.active_target_level = 9
    policy.active_enemy_count = 1

    decision = policy.next_decision(
        CharacterState(
            level=18,
            hp=225,
            max_hp=254,
            mana=242,
            max_mana=242,
            move=279,
            max_move=320,
            room_name="The Shadow Grove",
            room_vnum="1308",
            position=7,
            exits={"east": "1305", "west": "1307"},
            enemies=[[{"name": "a shadow guardian", "level": "9", "hp": "100"}]],
        )
    )

    assert decision is not None
    assert decision.command == "flee"
    assert "source-registered route hazard" in decision.reason
    assert policy.fastwalk_resume_current_route_after_interrupt is False
    assert policy.fastwalk_resume_hunt_after_interrupt is False
    assert policy.fastwalk_emergency_recall_pending is True
    assert policy.fastwalk_returning is True
    assert policy.fastwalk_abort_reason == (
        "unexpected combat interrupted a no-combat field probe"
    )


def test_plains_aruncus_hunt_opens_the_hermit_hut_before_searching() -> None:
    route = route_named("plains aruncus")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=plains_aruncus_hunt_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    policy.fastwalk_hunt_stop_index = 2
    state = CharacterState(
        level=14,
        hp=205,
        max_hp=205,
        mana=207,
        max_mana=207,
        move=200,
        max_move=280,
        position=7,
        room_vnum="330",
        exits={"n": "323", "e": "322", "s": "319", "w": "331"},
    )

    open_door = policy.next_decision(state)
    enter_hut = policy.next_decision(state)

    assert open_door is not None and open_door.command == "open west"
    assert enter_hut is not None and enter_hut.command == "west"


def test_ambush_archer_research_uses_source_path_without_combat() -> None:
    stops = ambush_archer_research_stops()

    assert len(stops) == 1
    assert stops[0].target == "goblin archer"
    assert stops[0].route[-2:] == ("open south", "south")
    assert stops[0].consider_only is True
    assert stops[0].exact_target is True


def test_ambush_archer_hunt_preserves_route_and_adds_health_gate() -> None:
    research = ambush_archer_research_stops()[0]
    hunt = ambush_archer_hunt_stops()[0]

    assert hunt.route == research.route
    assert hunt.target == "goblin archer"
    assert hunt.consider_only is False
    assert hunt.minimum_health_ratio == 0.85


def test_gnome_guard_research_only_checks_the_unarmed_hut_guard() -> None:
    stops = gnome_guard_research_stops()

    assert len(stops) == 1
    assert stops[0].route == ()
    assert stops[0].target == "gnome guard"
    assert stops[0].consider_only is True
    assert stops[0].exact_target is True


def test_fleshmonger_thief_rotation_combines_evidenced_stops() -> None:
    stops = fleshmonger_thief_rotation_research_stops()

    assert [stop.target for stop in stops] == [
        "patrolling guard",
        "on-duty guard",
        "cook",
        "cook",
    ]
    assert stops[1].route == ("open north", "north")
    assert stops[2].route == ("south", "open east", "east")
    assert stops[2].command_keyword == "cook"
    assert stops[3].route == ()
    assert stops[3].command_keyword == "2.cook"
    assert stops[2].trivial_bystanders == ("cook's boy",)
    assert stops[2].rejected_consider_subjects == ("cook's boy",)
    assert stops[0].maximum_level_offset == 0
    assert stops[1].maximum_level_offset == 0
    assert stops[2].maximum_level_offset is None
    assert all(stop.consider_only is False for stop in stops)


def test_fleshmonger_guard_circuit_allows_perfect_match_level_fuzz() -> None:
    stops = fleshmonger_guard_circuit_research_stops()

    assert len(stops) == 2
    assert all(stop.maximum_level_offset == 1 for stop in stops)


def test_consider_ignores_healthier_hp_addendum_for_configured_stop() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("fleshmonger"),
        fastwalk_hunt_stops=(
            FieldHuntStop(
                (),
                "on-duty guard",
            ),
        ),
    )
    policy.consider_target = "on-duty guard"

    policy.observe_text(
        "The perfect match! Also, he is a teensy bit healthier than you.\n"
    )

    assert policy.consider_viable is True


def test_consider_accepts_target_when_character_is_healthier() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("fleshmonger"),
        fastwalk_hunt_stops=(
            FieldHuntStop(
                (),
                "on-duty guard",
            ),
        ),
    )
    policy.consider_target = "on-duty guard"

    policy.observe_text(
        "The perfect match! Also, you are currently slightly healthier than he.\n"
    )

    assert policy.consider_viable is True
    assert policy.fastwalk_consider_outcomes == {"on-duty guard": True}


def test_consider_records_below_band_target_for_campaign_exclusion() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("gnome treasury"),
        fastwalk_hunt_stops=(FieldHuntStop((), "the treasurer"),),
    )
    policy.current_room = "1570"
    policy.consider_target = "the treasurer"

    policy.observe_text(
        "The treasurer is no match for you. "
        "Also, you are currently healthier than he.\n"
    )

    assert policy.consider_viable is False
    assert policy.fastwalk_below_band_targets == {"the treasurer"}
    assert policy.fastwalk_below_band_sightings == {
        ("1570", "the treasurer")
    }


def test_partial_field_hunt_skips_only_a_persisted_room_sighting() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("mahn tor rock toads"),
        fastwalk_hunt_stops=(
            FieldHuntStop((), "rather large rock toad"),
        ),
        fastwalk_skip_target_sightings=frozenset(
            {("2311", "rather large rock toad")}
        ),
    )
    policy.current_room = "2311"
    policy.fastwalk_hunt_looked = True
    policy.room_targets["2311"] = ["rather large rock toad"]
    policy.room_target_counts["2311"] = {"rather large rock toad": 1}

    decision = policy._fastwalk_hunt_plan_decision(
        CharacterState(
            level=18,
            hp=300,
            max_hp=300,
            mana=300,
            max_mana=300,
            move=300,
            max_move=300,
            position=7,
            room_vnum="2311",
        )
    )

    assert decision is not None
    assert decision.command == "look"
    assert "persisted below-band" in decision.reason
    assert policy.fastwalk_hunt_stop_skipped is True
    assert policy.fastwalk_attack_started is False


def test_aruncus_hunt_recalls_after_unique_target_is_below_band() -> None:
    stop = plains_aruncus_hunt_stops()[0]
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("plains aruncus"),
        fastwalk_hunt_stops=(stop,),
    )
    policy.current_room = "323"
    policy.room_targets["323"] = ["aruncus the druid"]
    policy.room_target_counts["323"] = {"aruncus the druid": 1}
    policy.room_target_selectors["323"] = {
        "aruncus the druid": ["#147"],
    }
    policy.fastwalk_attack_target = "Aruncus the Druid"
    policy.consider_target = "Aruncus the Druid"
    policy.consider_target_selector = "#147"
    policy.consider_viable = False
    policy.fastwalk_below_band_targets.add("aruncus the druid")

    decision = policy._consider_fastwalk_target(
        CharacterState(level=17, room_vnum="323", hp=242, max_hp=242)
    )

    assert stop.abort_after_consider_rejection is True
    assert decision is not None
    assert decision.command == "recall"
    assert "unique field target" in decision.reason
    assert policy.fastwalk_returning is True
    assert policy.fastwalk_target_absent is False


def test_galaxy_white_dwarf_probe_is_exact_and_consider_only() -> None:
    (stop,) = galaxy_white_dwarf_research_stops()

    assert stop.target == "tiny white dwarf"
    assert stop.command_keyword == "white"
    assert stop.actions == ("where white",)
    assert stop.abort_if_where_target_absent is True
    assert stop.consider_only is True
    assert stop.exact_target is True
    assert stop.maximum_level_offset == 1
    assert stop.abort_after_consider_rejection is True
    assert stop.route_vnums == (
        "1308",
        "1305",
        "1306",
        "9301",
        "9302",
        "9303",
        "9304",
        "9305",
        "9306",
    )


def test_galaxy_white_dwarf_hunt_retains_probe_safety_gates() -> None:
    (stop,) = galaxy_white_dwarf_hunt_stops()

    assert stop.consider_only is False
    assert stop.minimum_health_ratio == pytest.approx(0.85)
    assert stop.maximum_level_offset == 1
    assert stop.abort_after_consider_rejection is True


def test_secondary_galaxy_white_dwarf_probe_targets_only_room_9314() -> None:
    stops = galaxy_white_dwarf_secondary_research_stops()

    assert len(stops) == 3
    assert stops[0].target is None
    assert stops[1].target is None
    assert stops[0].route_vnums == (
        "1308",
        "1305",
        "1306",
        "9301",
        "9302",
        "9303",
    )
    assert stops[1].route_vnums == ("9303", "9308")
    assert stops[-1].target == "tiny white dwarf"
    assert stops[-1].command_keyword == "white"
    assert stops[-1].route_vnums == ("9312", "9313", "9314")
    assert stops[-1].consider_only is True
    assert stops[-1].exact_target is True
    assert stops[-1].maximum_level_offset == 1
    assert stops[-1].abort_after_consider_rejection is True


def test_secondary_galaxy_white_dwarf_hunt_retains_bounded_gates() -> None:
    stops = galaxy_white_dwarf_secondary_hunt_stops()

    assert len(stops) == 3
    assert stops[-1].consider_only is False
    assert stops[-1].minimum_health_ratio == pytest.approx(0.85)
    assert stops[-1].maximum_level_offset == 1


def test_galaxy_red_supergiant_probe_covers_source_reset_rooms() -> None:
    stops = galaxy_red_supergiant_research_stops()

    assert [stop.target for stop in stops] == ["red supergiant"] * 4
    assert [stop.route_vnums for stop in stops] == [
        ("1308", "1305", "1306", "9301", "9302", "9303", "9304"),
        ("9303", "9308"),
        ("9312", "9313"),
        ("9314", "9309"),
    ]
    first = stops[0]
    assert first.actions == ("where red",)
    assert first.abort_if_where_target_absent is True
    assert all(stop.command_keyword == "red" for stop in stops)
    assert all(stop.consider_only for stop in stops)
    assert all(stop.exact_target for stop in stops)
    assert all(stop.maximum_level_offset == 1 for stop in stops)


def test_galaxy_red_supergiant_hunt_retains_probe_safety_gates() -> None:
    stops = galaxy_red_supergiant_hunt_stops()

    assert len(stops) == 4
    assert all(not stop.consider_only for stop in stops)
    assert all(stop.minimum_health_ratio == pytest.approx(0.85) for stop in stops)
    assert all(stop.maximum_level_offset == 1 for stop in stops)


def test_galaxy_horsehead_probe_uses_allowed_nonaggressive_bystanders() -> None:
    stops = galaxy_horsehead_nebula_research_stops()

    assert len(stops) == 5
    assert stops[0].target is None
    assert stops[0].where_target == "horsehead nebula"
    assert stops[0].actions == ("where horsehead",)
    assert stops[0].abort_if_where_target_absent is True
    assert stops[-1].route == ("north",)
    assert stops[-1].target == "horsehead nebula"
    assert stops[-1].command_keyword == "horsehead"
    assert stops[-1].allowed_bystanders == ("young nebula",)
    assert stops[-1].consider_only is True
    assert stops[-1].exact_target is True
    assert stops[-1].maximum_target_count == 1
    assert stops[-1].maximum_level_offset == 2
    assert stops[-1].abort_after_consider_rejection is True


def test_galaxy_horsehead_hunt_retains_bounded_combat_gates() -> None:
    stops = galaxy_horsehead_nebula_hunt_stops()

    assert stops[-1].consider_only is False
    assert stops[-1].minimum_health_ratio == pytest.approx(0.85)
    assert stops[-1].allowed_bystanders == ("young nebula",)
    assert stops[-1].maximum_level_offset == 2


def test_hightower_jailor_probe_uses_randomized_grove_and_consider_only_gates() -> None:
    (stop,) = hightower_jailor_research_stops()

    assert stop.route == ("open down", "down", "down", "east", "east")
    assert stop.target == "jailor"
    assert stop.command_keyword == "jailor"
    assert stop.consider_only is True
    assert stop.exact_target is True
    assert stop.maximum_target_count == 1
    assert stop.maximum_level_offset == 1
    assert stop.abort_after_consider_rejection is True
    assert stop.route_vnums == (
        "1308", "1305", "1302", "1311", "1312", "1313", "1314", "1317"
    )


def test_hightower_jailor_hunt_retains_bounded_combat_gates() -> None:
    (stop,) = hightower_jailor_hunt_stops()

    assert stop.consider_only is False
    assert stop.minimum_health_ratio == pytest.approx(0.90)
    assert stop.maximum_level_offset == 1
    assert stop.maximum_target_count == 1
    assert stop.abort_after_consider_rejection is True


def test_field_hunt_considers_wandering_target_before_next_route_step() -> None:
    stop = FieldHuntStop(
        (),
        "Aruncus the Druid",
        exact_target=True,
        route_vnums=("316",),
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("plains aruncus"),
        fastwalk_hunt_stops=(stop,),
    )
    policy.current_room = "318"
    policy.room_targets["318"] = ["aruncus the druid"]
    policy.room_target_counts["318"] = {"aruncus the druid": 1}
    policy.room_target_selectors["318"] = {
        "aruncus the druid": ["#24981"],
    }
    state = CharacterState(
        level=14,
        hp=205,
        max_hp=205,
        mana=207,
        max_mana=207,
        move=255,
        max_move=280,
        position=7,
        room_vnum="318",
        exits={"s": "316"},
    )

    decision = policy._fastwalk_hunt_plan_decision(state)

    assert decision is not None
    assert decision.command == "consider #24981"
    assert policy.fastwalk_hunt_move_index == 0


def test_field_hunt_forgets_defeated_selector_before_next_same_target_route() -> None:
    target = "rather large rock toad"
    stops = (
        FieldHuntStop((), target, exact_target=True),
        FieldHuntStop(
            ("south",),
            target,
            exact_target=True,
            route_vnums=("2313",),
        ),
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("mahn tor rock toads"),
        fastwalk_hunt_stops=stops,
        fastwalk_kill_limit=2,
    )
    policy.current_room = "2311"
    policy.combat_active = True
    policy.active_target = target
    policy.active_target_selector = "#25220"
    policy.room_targets["2311"] = [target]
    policy.room_target_counts["2311"] = {target: 1}
    policy.room_target_selectors["2311"] = {target: ["#25220"]}

    policy.observe_text(
        "The Rock Toad is DEAD!!\n"
        "You receive 269 experience points for the kill.\n"
        "You gained a total of 561 experience points!\n"
    )
    decision = policy._fastwalk_hunt_plan_decision(
        CharacterState(
            level=15,
            hp=151,
            max_hp=217,
            mana=215,
            max_mana=215,
            move=230,
            max_move=290,
            position=7,
            room_vnum="2311",
            exits={"e": "2310", "s": "2313"},
        )
    )

    assert policy.room_targets["2311"] == []
    assert policy.room_target_counts["2311"] == {}
    assert policy.room_target_selectors["2311"] == {}
    assert decision is not None
    assert decision.command == "south"
    assert policy.fastwalk_hunt_stop_index == 1


def test_field_hunt_preserves_other_same_identity_selector_after_kill() -> None:
    target = "rather large rock toad"
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("mahn tor rock toads"),
        fastwalk_hunt_stops=(FieldHuntStop((), target, exact_target=True),),
    )
    policy.current_room = "2311"
    policy.combat_active = True
    policy.active_target = target
    policy.active_target_selector = "#25220"
    policy.room_targets["2311"] = [target]
    policy.room_target_counts["2311"] = {target: 2}
    policy.room_target_selectors["2311"] = {
        target: ["#25220", "#25221"],
    }

    policy.observe_text(
        "The Rock Toad is DEAD!!\n"
        "You receive 269 experience points for the kill.\n"
    )

    assert policy.room_targets["2311"] == [target]
    assert policy.room_target_counts["2311"] == {target: 1}
    assert policy.room_target_selectors["2311"] == {target: ["#25221"]}


def test_consider_skips_target_above_stop_live_level_ceiling() -> None:
    stop = FieldHuntStop(
        (),
        "on-duty guard",
        exact_target=True,
        maximum_level_offset=0,
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("fleshmonger"),
        fastwalk_hunt_stops=(stop,),
    )
    policy.fastwalk_attack_target = "on-duty guard"
    policy.current_room = "9401"
    policy.room_targets["9401"] = ["on-duty guard"]
    policy.room_target_counts["9401"] = {"on-duty guard": 1}
    policy.consider_target = "on-duty guard"
    policy.consider_viable = True
    state = CharacterState(
        level=10,
        hp=154,
        max_hp=154,
        position=7,
        room_name="A Guard Room",
        room_vnum="9401",
        enemies=[[
            {
                "name": "the on-duty guard",
                "level": "11",
                "hp": "169",
                "maxhp": "169",
            }
        ]],
    )

    decision = policy._consider_fastwalk_target(state)

    assert decision is not None
    assert decision.command == "look"
    assert "live level ceiling" in decision.reason
    assert policy.fastwalk_hunt_stop_skipped is True
    assert policy.fastwalk_attack_started is False
    assert policy.combat_active is False


def test_consider_skips_source_fuzz_range_above_ceiling_before_combat() -> None:
    stop = FieldHuntStop(
        (),
        "Aruncus the Druid",
        exact_target=True,
        maximum_level_offset=0,
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("plains aruncus"),
        fastwalk_hunt_stops=(stop,),
        source_mobile_level_ranges={"aruncus the druid": (11, 15)},
    )
    policy.fastwalk_attack_target = "Aruncus the Druid"
    policy.current_room = "333"
    policy.room_targets["333"] = ["aruncus the druid"]
    policy.room_target_counts["333"] = {"aruncus the druid": 1}
    policy.consider_target = "Aruncus the Druid"
    policy.consider_viable = True

    decision = policy._consider_fastwalk_target(
        CharacterState(level=13, room_vnum="333", hp=194, max_hp=194)
    )

    assert decision is not None
    assert decision.command == "look"
    assert "source-fuzzed" in decision.reason
    assert policy.fastwalk_hunt_stop_skipped is True
    assert policy.fastwalk_attack_started is False


def test_exact_live_level_overrides_broader_source_fuzz_range() -> None:
    stop = FieldHuntStop(
        (),
        "on-duty guard",
        exact_target=True,
        maximum_level_offset=1,
    )
    policy = StarterPolicy(
        _spec(**{"class": "warrior", "subclass": "knight"}),
        "swordfish",
        fastwalk_route=route_named("fleshmonger"),
        fastwalk_hunt_stops=(stop,),
        source_mobile_level_ranges={"on-duty guard": (8, 12)},
    )
    policy.fastwalk_attack_target = "on-duty guard"
    policy.current_room = "9401"
    policy.room_targets["9401"] = ["on-duty guard"]
    policy.room_target_counts["9401"] = {"on-duty guard": 1}
    policy.consider_target = "on-duty guard"
    policy.consider_target_selector = "#22801"
    policy.consider_viable = True
    state = CharacterState(
        level=10,
        hp=217,
        max_hp=217,
        position=7,
        room_name="A Guard Room",
        room_vnum="9401",
        enemies=[[{
            "name": "the on-duty guard",
            "level": "11",
            "hp": "169",
            "maxhp": "169",
        }]],
    )

    decision = policy._consider_fastwalk_target(state)

    assert decision is not None
    assert decision.command != "look"
    assert policy.fastwalk_attack_started is True
    assert policy.active_target_selector == "#22801"


def test_aruncus_hunt_pursuit_excludes_the_level_twenty_four_room() -> None:
    stops = plains_aruncus_hunt_stops()

    assert stops
    assert all(stop.maximum_pursuit_steps == 3 for stop in stops)
    assert all("343" in stop.pursuit_room_vnums for stop in stops)
    assert all("344" not in stop.pursuit_room_vnums for stop in stops)


def test_aruncus_hunt_allows_source_trivial_citizen_after_pursuit() -> None:
    stop = plains_aruncus_hunt_stops()[0]
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("plains aruncus"),
        fastwalk_hunt_stops=(stop,),
    )
    policy.fastwalk_attack_target = "Aruncus the Druid"
    policy.current_room = "318"
    policy.room_targets["318"] = ["aruncus the druid", "the citizen"]
    policy.room_target_counts["318"] = {
        "aruncus the druid": 1,
        "the citizen": 1,
    }

    decision = policy._consider_fastwalk_target(
        CharacterState(
            level=13,
            hp=143,
            max_hp=194,
            mana=199,
            max_mana=199,
            move=132,
            max_move=270,
            position=7,
            room_name="Grassy plains",
            room_vnum="318",
        )
    )

    assert decision is not None
    assert decision.command == "consider aruncus"
    assert policy.fastwalk_hunt_stop_skipped is False


def test_aruncus_hunt_allows_trivial_rabbit_with_different_article() -> None:
    stop = plains_aruncus_hunt_stops()[0]
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("plains aruncus"),
        fastwalk_hunt_stops=(stop,),
    )
    policy.fastwalk_attack_target = "Aruncus the Druid"
    policy.current_room = "322"
    policy.room_targets["322"] = ["aruncus the druid", "a cute rabbit"]
    policy.room_target_counts["322"] = {
        "aruncus the druid": 1,
        "a cute rabbit": 1,
    }

    decision = policy._consider_fastwalk_target(
        CharacterState(
            level=14,
            hp=205,
            max_hp=205,
            mana=207,
            max_mana=207,
            move=257,
            max_move=280,
            position=7,
            room_name="Grassy foothills",
            room_vnum="322",
        )
    )

    assert decision is not None
    assert decision.command == "consider aruncus"
    assert policy.fastwalk_hunt_stop_skipped is False


def test_aruncus_hunt_ignores_source_object_in_crowd_count() -> None:
    stop = plains_aruncus_hunt_stops()[0]
    gyvel = ObjectSource(
        301,
        "herbs herb gyvel",
        "a small dusk of black gyvel",
        19,
        (1, 0, 0, 0),
        25,
        room_description=(
            "Some black gyvel is lying here. It is dark green with black leaves "
            "and tiny blood-red flowers."
        ),
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("plains aruncus"),
        fastwalk_hunt_stops=(stop,),
        gear_catalog=GearCatalog({gyvel.vnum: gyvel}),
    )
    policy.fastwalk_attack_target = "Aruncus the Druid"
    policy.current_room = "322"
    policy.room_targets["322"] = ["aruncus the druid", "black gyvel"]
    policy.room_target_counts["322"] = {
        "aruncus the druid": 1,
        "black gyvel": 1,
    }

    decision = policy._consider_fastwalk_target(
        CharacterState(
            level=14,
            hp=205,
            max_hp=205,
            mana=207,
            max_mana=207,
            move=257,
            max_move=280,
            position=7,
            room_name="Grassy foothills",
            room_vnum="322",
        )
    )

    assert decision is not None
    assert decision.command == "consider aruncus"
    assert policy.fastwalk_hunt_stop_skipped is False


def test_field_pursuit_refuses_an_unregistered_gmcp_destination() -> None:
    stop = replace(
        plains_aruncus_hunt_stops()[0],
        pursuit_room_vnums=("342", "343"),
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("plains aruncus"),
        fastwalk_hunt_stops=(stop,),
    )
    policy.fastwalk_attack_started = True
    policy.fastwalk_pursuit_direction = "west"

    decision = policy._fastwalk_hunt_plan_decision(
        CharacterState(
            level=13,
            hp=194,
            max_hp=194,
            mana=199,
            max_mana=199,
            move=250,
            max_move=270,
            room_name="Dark smelly tunnels",
            room_vnum="343",
            exits={"e": "342", "w": "344"},
            position=7,
        )
    )

    assert decision is not None
    assert decision.command == "recall"
    assert "unregistered pursuit room" in decision.reason
    assert "room 344" in (policy.fastwalk_abort_reason or "")
    assert policy.fastwalk_returning is True


def test_perfect_match_consider_overrides_broader_source_fuzz_range() -> None:
    stop = FieldHuntStop(
        (),
        "on-duty guard",
        exact_target=True,
        maximum_level_offset=1,
    )
    policy = StarterPolicy(
        _spec(**{"class": "warrior", "subclass": "knight"}),
        "swordfish",
        fastwalk_route=route_named("fleshmonger"),
        fastwalk_hunt_stops=(stop,),
        source_mobile_level_ranges={"on-duty guard": (8, 12)},
    )
    policy.fastwalk_attack_target = "on-duty guard"
    policy.current_room = "9401"
    policy.room_targets["9401"] = ["on-duty guard"]
    policy.room_target_counts["9401"] = {"on-duty guard": 1}
    policy.consider_target = "on-duty guard"
    policy.consider_target_selector = "#22801"
    policy.observe_text(
        "The perfect match!\n"
        "However, you are a teensy bit healthier than he.\n"
    )

    decision = policy._consider_fastwalk_target(
        CharacterState(
            level=10,
            hp=217,
            max_hp=217,
            position=7,
            room_name="A Guard Room",
            room_vnum="9401",
        )
    )

    assert decision is not None
    assert decision.command != "look"
    assert policy.consider_level_offset_ceiling == 1
    assert policy.fastwalk_attack_started is True
    assert policy.active_target_selector == "#22801"


def test_exact_target_fuzz_gate_ignores_unrelated_generic_source_keywords() -> None:
    stop = FieldHuntStop(
        (),
        "Aruncus the Druid",
        exact_target=True,
        maximum_level_offset=2,
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("plains aruncus"),
        fastwalk_hunt_stops=(stop,),
        source_mobile_level_ranges={
            "aruncus the druid": (11, 15),
            "druid": (8, 53),
        },
    )
    policy.fastwalk_attack_target = "Aruncus the Druid"
    policy.current_room = "333"
    policy.room_targets["333"] = ["aruncus the druid"]
    policy.room_target_counts["333"] = {"aruncus the druid": 1}
    policy.consider_target = "Aruncus the Druid"
    policy.consider_viable = True

    decision = policy._consider_fastwalk_target(
        CharacterState(level=13, room_vnum="333", hp=194, max_hp=194)
    )

    assert policy._source_mobile_level_range("Aruncus the Druid", stop) == (11, 15)
    assert decision is not None
    assert "source-fuzzed" not in decision.reason
    assert policy.fastwalk_hunt_stop_skipped is False
    assert policy.fastwalk_attack_started is True


def test_fleshmonger_mufti_research_opens_south_and_never_attacks() -> None:
    stops = fleshmonger_mufti_research_stops()

    assert len(stops) == 1
    assert stops[0].route == ("open south", "south")
    assert stops[0].target == "mufti guard"
    assert stops[0].consider_only is True
    assert stops[0].exact_target is True


def test_fleshmonger_servant_research_stays_below_the_laboratory() -> None:
    stops = fleshmonger_servant_research_stops()

    assert len(stops) == 1
    assert stops[0].route == ("up", "up")
    assert stops[0].target == "hobgoblin servant"
    assert stops[0].consider_only is True
    assert stops[0].exact_target is True
    assert stops[0].maximum_target_count == 1


def test_fleshmonger_servant_hunt_adds_bounded_combat_gates() -> None:
    stops = fleshmonger_servant_hunt_stops()

    assert len(stops) == 1
    assert stops[0].route == ("up", "up")
    assert stops[0].target == "hobgoblin servant"
    assert stops[0].consider_only is False
    assert stops[0].minimum_health_ratio == 0.85
    assert stops[0].maximum_target_count == 1
    assert stops[0].maximum_level_offset == 0


def test_fleshmonger_extended_rotation_reaches_study_from_kitchen() -> None:
    stops = fleshmonger_thief_extended_rotation_stops()

    assert [stop.target for stop in stops] == [
        "patrolling guard",
        "on-duty guard",
        "cook",
        "cook",
        "hobgoblin servant",
    ]
    servant = stops[-1]
    assert servant.route == ("west", "up", "up")
    assert servant.minimum_health_ratio == 0.60
    assert servant.maximum_target_count == 1
    assert servant.maximum_level_offset == 0


def test_fleshmonger_cook_research_allows_only_the_helper() -> None:
    stops = fleshmonger_cook_research_stops()

    assert len(stops) == 2
    assert stops[0].route == ("open east", "east")
    assert stops[0].target == "cook"
    assert [stop.command_keyword for stop in stops] == ["cook", "2.cook"]
    assert all(stop.allowed_bystanders == ("cook's boy",) for stop in stops)
    assert all(
        stop.rejected_consider_subjects == ("cook's boy",)
        for stop in stops
    )
    assert all(stop.consider_only is True for stop in stops)
    assert all(stop.exact_target is True for stop in stops)


def test_fleshmonger_cook_hunt_targets_adult_beside_trivial_helper() -> None:
    stops = fleshmonger_cook_hunt_stops()

    assert len(stops) == 2
    assert [stop.command_keyword for stop in stops] == ["cook", "2.cook"]
    assert all(stop.trivial_bystanders == ("cook's boy",) for stop in stops)
    assert all(stop.consider_only is False for stop in stops)
    assert all(stop.minimum_health_ratio == 0.85 for stop in stops)


def test_consider_rejects_ambiguous_keyword_when_it_resolves_to_helper() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("fleshmonger"),
        fastwalk_hunt_stops=fleshmonger_cook_hunt_stops(),
    )
    policy.fastwalk_hunt_stop_index = 1
    policy.consider_target = "cook"

    policy.observe_text(
        "The cook's boy looks like an easy kill. "
        "Also, you are currently healthier than he.\n"
    )

    assert policy.consider_viable is False


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


def test_fastwalk_continues_after_loot_when_next_stop_health_floor_is_met() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("fleshmonger"),
        fastwalk_hunt_stops=fleshmonger_thief_rotation_research_stops(),
        fastwalk_kill_limit=2,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(policy.fastwalk_route.commands)
    policy.fastwalk_hunt_stop_index = 1
    policy.fastwalk_last_kill_target = "on-duty guard"
    policy.fastwalk_hunt_stop_killed = True
    policy.completed_kills.append({"target": "on-duty guard", "xp": 476})
    policy.pending_loot_rooms.add("9401")
    state = CharacterState(
        level=10,
        hp=113,
        max_hp=154,
        mana=176,
        max_mana=176,
        move=166,
        max_move=240,
        room_name="Guard Post",
        room_vnum="9401",
        position=7,
    )

    loot = policy.next_decision(state)
    policy.prompt_ready = True
    sacrifice = policy.next_decision(state)
    policy.prompt_ready = True
    inventory = policy.next_decision(state)

    assert loot is not None and loot.command == "get all corpse"
    assert sacrifice is not None and sacrifice.command == "sacrifice corpse"
    assert inventory is not None and inventory.command == "inventory"
    assert policy.fastwalk_recall_after_loot is False


def test_fastwalk_recalls_after_loot_below_next_stop_health_floor() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("fleshmonger"),
        fastwalk_hunt_stops=fleshmonger_thief_rotation_research_stops(),
        fastwalk_kill_limit=2,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(policy.fastwalk_route.commands)
    policy.fastwalk_hunt_stop_index = 1
    policy.fastwalk_last_kill_target = "on-duty guard"
    policy.fastwalk_hunt_stop_killed = True
    policy.completed_kills.append({"target": "on-duty guard", "xp": 476})
    policy.pending_loot_rooms.add("9401")
    state = CharacterState(
        level=10,
        hp=90,
        max_hp=154,
        mana=176,
        max_mana=176,
        move=166,
        max_move=240,
        room_name="Guard Post",
        room_vnum="9401",
        position=7,
    )

    commands: list[str] = []
    for _ in range(5):
        decision = policy.next_decision(state)
        if decision is not None:
            commands.append(decision.command)
            if decision.command == "recall":
                break
        policy.prompt_ready = True

    assert "recall" in commands


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
        hp=31,
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


def test_fastwalk_flees_before_an_enemy_snapshot_can_bypass_consider() -> None:
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

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "flee"
    assert "identified and considered" in (policy.fastwalk_abort_reason or "")


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


def test_fastwalk_recovery_honors_first_hunt_stop_health_floor() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("fleshmonger"),
        fastwalk_hunt_stops=(
            FieldHuntStop(
                (),
                "patrolling guard",
                minimum_health_ratio=0.85,
            ),
        ),
    )
    policy.in_world = True
    policy.prompt_ready = True
    at_healer = CharacterState(
        room_name="The Healer",
        room_vnum="3054",
        room_flags=["safe", "healing"],
        position=7,
        hp=163,
        max_hp=217,
        mana=160,
        max_mana=160,
        move=240,
        max_move=240,
    )

    recovery = policy.next_decision(at_healer)

    assert recovery is not None
    assert recovery.command == "sleep"
    assert policy.fastwalk_recovery_ready is False


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


@pytest.mark.parametrize("duration", [4, 0])
def test_blind_character_waits_at_healer_until_affect_is_cured(
    duration: int,
) -> None:
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
        affects=[[{"name": "blindness", "duration": str(duration)}]],
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
    assert policy.utility_abort_reason is None


def test_field_hunt_follows_considered_target_once_after_observed_departure() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
        fastwalk_hunt_stops=(FieldHuntStop((), "nanny"),),
    )
    policy.fastwalk_hunt_looked = True
    policy.fastwalk_attack_target = "nanny"
    policy.consider_target = "nanny"
    policy.consider_response_pending = True

    policy.observe_text("The nanny leaves east.\n")
    state = CharacterState(
        room_vnum="6604",
        hp=123,
        max_hp=123,
        mana=145,
        max_mana=145,
        move=210,
        max_move=210,
        position=7,
    )

    follow = policy._fastwalk_hunt_plan_decision(state)

    assert follow is not None
    assert follow.command == "east"
    assert "fresh safety check" in follow.reason
    assert policy.consider_response_pending is False
    assert policy.consider_target is None

    look = policy._fastwalk_hunt_plan_decision(state)
    assert look is not None
    assert look.command == "look"


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


def test_combat_gear_uses_unique_source_keyword_for_long_dagger() -> None:
    ordinary = ObjectSource(
        3020,
        "dagger",
        "a dagger",
        5,
        (0, 2, 4, 11),
        10,
        wear_flags=1 | (1 << 13),
    )
    long_dagger = ObjectSource(
        5252,
        "long dagger slim",
        "a long slim dagger",
        5,
        (0, 2, 5, 11),
        10,
        wear_flags=1 | (1 << 13),
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": None}),
        "swordfish",
        gear_catalog=GearCatalog({ordinary.vnum: ordinary, long_dagger.vnum: long_dagger}),
    )
    policy.gear_worn = [ordinary]
    policy.gear_audited = True
    policy.gear_allowed_categories = {"wield"}
    state = CharacterState(
        hp=100,
        max_hp=100,
        mana=100,
        max_mana=100,
        move=100,
        max_move=100,
        room_name="Dwarven Homestead",
        room_vnum="20506",
        inventory=[[{"short_desc": "a long slim dagger"}]],
    )

    remove = policy._gear_decision(state)
    wear = policy._gear_decision(state)

    assert remove is not None
    assert remove.command == "remove dagger"
    assert wear is not None
    assert wear.command == "wear long"


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


def test_runtime_boundary_recalls_from_healthy_active_combat() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.request_runtime_boundary()
    fighting = CharacterState(
        area="Ambush",
        room_name="Inside a Shack",
        room_vnum="4514",
        position=7,
        hp=153,
        max_hp=194,
    )

    decision = policy.next_decision(fighting)

    assert policy.return_home is True
    assert decision is not None
    assert decision.command == "recall"
    assert "before the bounded segment disconnects" in decision.reason


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


def test_emergency_liquidation_flees_even_from_a_trivial_city_attacker() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        liquidate_loot=True,
        emergency_provision_sale=True,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.active_target_level = 4

    decision = policy.next_decision(
        CharacterState(
            level=18,
            hp=180,
            max_hp=254,
            room_name="Main Street",
            room_vnum="3013",
            room_flags=["safe"],
            position=7,
            enemies=[[{"name": "the drunk", "level": "4"}]],
        )
    )

    assert decision is not None
    assert decision.command == "flee"
    assert policy.return_home is True
    assert policy.utility_abort_reason == (
        "unexpected combat interrupted emergency loot liquidation"
    )


def test_emergency_liquidation_fails_after_returning_home_without_sale() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        liquidate_loot=True,
        emergency_provision_sale=True,
        return_home=True,
    )
    policy.in_world = True
    policy.login_authenticated = True
    policy.prompt_ready = True
    policy.utility_abort_reason = (
        "unexpected combat interrupted emergency loot liquidation"
    )

    decision = policy.next_decision(
        CharacterState(
            room_name="By the Temple Altar",
            room_vnum="3054",
            room_flags=["safe", "healing"],
            hp=180,
            max_hp=254,
            mana=200,
            max_mana=242,
            move=320,
            max_move=320,
            position=7,
        )
    )

    assert decision is None
    assert policy.failure == (
        "unexpected combat interrupted emergency loot liquidation"
    )


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


def test_progress_watchdog_marker_tracks_enemy_health_changes() -> None:
    before = CharacterState(
        room_vnum="2311",
        hp=233,
        mana=228,
        move=244,
        xp=118986,
        level=16,
        in_combat=True,
        position=6,
        enemies=[
            [
                {
                    "name": "the Rock Toad",
                    "isnpc": "2303",
                    "level": "13",
                    "hp": "225",
                    "maxhp": "225",
                }
            ]
        ],
    )
    after_knife = CharacterState(
        room_vnum="2311",
        hp=233,
        mana=228,
        move=244,
        xp=118986,
        level=16,
        in_combat=True,
        position=6,
        enemies=[
            [
                {
                    "name": "the Rock Toad",
                    "isnpc": "2303",
                    "level": "13",
                    "hp": "211",
                    "maxhp": "225",
                }
            ]
        ],
    )
    unchanged = CharacterState.from_dict(after_knife.to_dict())

    assert _watchdog_progress_marker(before) != _watchdog_progress_marker(after_knife)
    assert _watchdog_progress_marker(after_knife) == _watchdog_progress_marker(unchanged)


def test_progress_watchdog_marker_tracks_inventory_disposal() -> None:
    before = CharacterState(
        room_vnum="3019",
        hp=194,
        mana=199,
        move=212,
        stats={"carry_num": 29, "carry_wt": 127},
        currencies={"silver": 3, "copper": 8},
    )
    after_donation = CharacterState(
        room_vnum="3019",
        hp=194,
        mana=199,
        move=212,
        stats={"carry_num": 28, "carry_wt": 126},
        currencies={"silver": 3, "copper": 8},
    )
    after_sale = CharacterState(
        room_vnum="3019",
        hp=194,
        mana=199,
        move=212,
        stats={"carry_num": 28, "carry_wt": 126},
        currencies={"silver": 4, "copper": 2},
    )

    assert _watchdog_progress_marker(before) != _watchdog_progress_marker(
        after_donation
    )
    assert _watchdog_progress_marker(after_donation) != _watchdog_progress_marker(
        after_sale
    )


def test_route_cycle_watchdog_ignores_repeated_combat_actions() -> None:
    assert _route_cycle_watchdog_applies("south", 5) is True
    assert (
        _route_cycle_watchdog_applies(
            "north",
            5,
            safe_city_return=True,
        )
        is False
    )
    assert _route_cycle_watchdog_applies("cast 'chill touch' troll", 5) is False
    assert _route_cycle_watchdog_applies("kick troll", 9) is False


def test_repeated_command_watchdog_allows_registered_trainer_return() -> None:
    assert _repeated_command_watchdog_applies(7, 6) is True
    assert (
        _repeated_command_watchdog_applies(
            7,
            6,
            registered_trainer_return=True,
        )
        is False
    )


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

    policy.health_check_due = None
    policy.combat_active = True
    assert not _policy_inactivity_due(
        policy,
        now=300.0,
        last_progress=0.0,
        timeout=45.0,
    )

    policy.combat_active = False
    policy.waiting_for_move = True
    assert not _policy_inactivity_due(
        policy,
        now=300.0,
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
    wear = policy.next_decision(healer)
    assert wear is not None
    assert wear.command == "wear all"
    policy.after_command(wear)
    policy.prompt_ready = True

    audit = policy.next_decision(healer)
    assert audit is not None
    assert audit.command == "eq all"
    policy.after_command(audit)
    policy.observe_text("<<worn on head>      -")
    policy.prompt_ready = True

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


def test_field_inventory_pulls_container_out_of_another_container() -> None:
    backpack = ObjectSource(
        1,
        "backpack pack",
        "a backpack",
        15,
        (100, 0, 0, 0),
        10,
    )
    sack = ObjectSource(
        2,
        "sack large",
        "a large sack",
        15,
        (400, 0, 0, 0),
        10,
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        gear_catalog=GearCatalog({1: backpack, 2: sack}),
    )
    policy.last_response = (
        "Your backpack contains:\n"
        "     a large sack\n"
        "     a big pot pie\n"
        "You are carrying 13/38 items.\n"
    )

    decision = policy._nested_container_extraction_decision()

    assert decision is not None
    assert decision.command == "get sack backpack"
    assert policy._nested_container_extraction_decision() is None


def test_fastwalk_audits_container_separation_at_recall() -> None:
    backpack = ObjectSource(
        1,
        "backpack pack",
        "a backpack",
        15,
        (100, 0, 0, 0),
        10,
    )
    sack = ObjectSource(
        2,
        "sack large",
        "a large sack",
        15,
        (400, 0, 0, 0),
        10,
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        gear_catalog=GearCatalog({1: backpack, 2: sack}),
    )
    policy.fastwalk_recall_started = True
    state = CharacterState(
        room_vnum="3001",
        position=7,
        hp=100,
        max_hp=100,
        mana=100,
        max_mana=100,
        move=100,
        max_move=100,
    )

    audit = policy._fastwalk_research_decision(state)
    assert audit is not None
    assert audit.command == "inventory"

    policy.last_response = "Your backpack contains:\n     a large sack\n"
    extraction = policy._fastwalk_research_decision(state)
    assert extraction is not None
    assert extraction.command == "get sack backpack"


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
    targetmode = policy.next_decision(state)
    assert targetmode is not None
    assert targetmode.command == "config +targetmode"
    policy.after_command(targetmode)

    policy.prompt_ready = True
    prepare = policy.next_decision(state)
    assert prepare is not None
    assert prepare.command == "drop cap"


def test_aruncus_hunt_disables_autoloot_before_departure() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("plains aruncus"),
        fastwalk_hunt_stops=plains_aruncus_hunt_stops(),
        fastwalk_kill_limit=1,
    )
    state = CharacterState(
        room_name="The Temple Of Midgaard",
        room_vnum="3001",
        position=7,
    )

    configure = policy._fastwalk_research_decision(state)

    assert configure is not None
    assert configure.command == "config -autoloot"
    assert "cursed drop" in configure.reason


def test_aruncus_hunt_collects_only_source_approved_corpse_drops() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("plains aruncus"),
        fastwalk_hunt_stops=plains_aruncus_hunt_stops(),
        fastwalk_kill_limit=1,
    )
    policy.current_room = "323"
    policy.fastwalk_last_kill_target = "Aruncus the Druid"
    policy.pending_loot_rooms.add("323")
    state = CharacterState(room_vnum="323", position=7)

    commands = []
    for _ in range(5):
        decision = policy._fastwalk_research_decision(state)
        assert decision is not None
        commands.append(decision.command)

    assert commands == [
        "get all.staff corpse",
        "get all.scroll corpse",
        "get all.ivy corpse",
        "sacrifice corpse",
        "inventory",
    ]


def test_aruncus_hunt_restores_autoloot_at_healer() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("plains aruncus"),
        fastwalk_hunt_stops=plains_aruncus_hunt_stops(),
        fastwalk_kill_limit=1,
    )

    wake = policy._restore_fastwalk_autoloot_decision(
        CharacterState(room_vnum="3054", position=4)
    )
    restore = policy._restore_fastwalk_autoloot_decision(
        CharacterState(room_vnum="3054", position=7)
    )

    assert wake is not None
    assert wake.command == "stand"
    assert restore is not None
    assert restore.command == "config +autoloot"
    assert (
        policy._restore_fastwalk_autoloot_decision(
            CharacterState(room_vnum="3054", position=7)
        )
        is None
    )


def test_fastwalk_discards_expendable_key_when_capacity_is_critical() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
        fastwalk_hunt_stops=moria_level_seven_orc_hunt_stops(),
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_autoloot_configured = True
    policy.fastwalk_targetmode_configured = True
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
        inventory=[[{"short_desc": "a shimmering key", "quan": "1"}]],
        stats={"carry_wt": 111, "maxcarry_wt": 115},
    )

    policy.prompt_ready = True
    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "sacrifice shimmering"
    assert "carrying capacity" in decision.reason


def test_fastwalk_preserves_expendable_key_with_adequate_capacity() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
        fastwalk_hunt_stops=moria_level_seven_orc_hunt_stops(),
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_autoloot_configured = True
    policy.fastwalk_targetmode_configured = True
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
        inventory=[[{"short_desc": "a shimmering key", "quan": "1"}]],
        stats={"carry_wt": 90, "maxcarry_wt": 115},
    )

    policy.prompt_ready = True
    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "south"


def test_fastwalk_discards_expendable_key_between_safe_field_fights() -> None:
    route = route_named("circus bearded lady")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=circus_freak_show_hunt_stops(),
        fastwalk_kill_limit=3,
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_stop_killed = True
    policy.completed_kills.append({"target": "Illusionist"})
    policy.prompt_ready = True
    state = CharacterState(
        level=7,
        hp=103,
        max_hp=110,
        mana=237,
        max_mana=297,
        move=204,
        max_move=210,
        position=7,
        room_name="The Tent of the Illusionist",
        room_vnum="4410",
        inventory=[[{"short_desc": "a shimmering key", "quan": "1"}]],
        stats={"carry_wt": 111, "maxcarry_wt": 115},
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "sacrifice shimmering"
    assert policy.fastwalk_returning is False


def test_fastwalk_uses_sneak_but_not_hide_before_city_transit() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_attack_target="war dog",
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_autoloot_configured = True
    policy.fastwalk_targetmode_configured = True
    policy.known_skills.update(("sneak", "hide"))
    origin = CharacterState(
        room_name="The Temple Of Midgaard",
        room_vnum="3001",
        position=7,
    )

    policy.prompt_ready = True
    sneak = policy.next_decision(origin)
    assert sneak is not None
    assert sneak.command == "sneak"
    policy.after_command(sneak)

    policy.prompt_ready = True
    departure = policy.next_decision(origin)
    assert departure is not None
    assert departure.command != "hide"
    assert "hide" not in policy.fastwalk_concealment_attempted


def test_thief_field_training_routes_to_the_midgaard_guildmaster() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("circus bearded lady"),
        fastwalk_hunt_stops=circus_freak_show_hunt_stops(),
        fastwalk_train_before_departure=True,
    )
    policy.in_world = True
    policy.latest_practice_balances = (2, 2)
    policy.selected_training_stat = "con"
    policy.fastwalk_stat_training_configured = True
    expected = (
        ("3054", "south"),
        ("3001", "south"),
        ("3005", "south"),
        ("3014", "south"),
        ("3025", "east"),
        ("3026", "south"),
        ("3027", "east"),
        ("3028", "south"),
    )

    for room_vnum, command in expected:
        state = CharacterState(
            level=10,
            hp=135,
            max_hp=135,
            mana=151,
            max_mana=151,
            move=220,
            max_move=220,
            position=7,
            room_name="Midgaard",
            room_vnum=room_vnum,
        )
        decision = policy._fastwalk_training_decision(state)
        assert decision is not None
        assert decision.command == command
        assert "level-10 thief trainer" in decision.reason


def test_thief_guildmaster_practices_priority_then_recalls() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
    )
    state = CharacterState(level=10, room_name="The Secret Yard", room_vnum="3029")

    first = policy._loremaster_decision(state)
    assert first.command == "look guildmaster"
    second = policy._loremaster_decision(state)
    assert second.command == "practice"
    policy.text = (
        "Skills known:\n"
        "second attack: 37%    sneak: 99%    stealth techniques: 46%\n"
        "Skills which may be learned:\n"
        "backstab: 0%\n"
        "You have 2 physical and 2 intellectual practices remaining."
    )
    third = policy._loremaster_decision(state)
    assert third.command == "practice stealth techniques"
    policy._resolve_pending_practice("accepted", "trained")
    fourth = policy._loremaster_decision(state)
    assert fourth.command == "practice backstab"
    policy._resolve_pending_practice("accepted", "trained")
    final = policy._loremaster_decision(state)
    assert final.command == "north"
    assert "class trainer" in final.reason


def test_class_trainer_refreshes_listing_after_gateway_unlock() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
    )
    state = CharacterState(level=15, room_name="Olive Grove", room_vnum="25204")
    policy._loremaster_decision(state)
    policy._loremaster_decision(state)
    policy.text = (
        "Skills known:\n"
        "second attack: 65%    sneak: 99%    stealth techniques: 56%\n"
        "Skills which may be learned:\n"
        "You have 2 physical and 2 intellectual practices remaining."
    )
    gateway = policy._loremaster_decision(state)
    assert gateway.command == "practice stealth techniques"

    policy._resolve_pending_practice("accepted", "trained")
    refresh = policy._loremaster_decision(state)

    assert refresh.command == "practice"
    assert "refresh" in refresh.reason
    assert policy.loremaster_step == 2


def test_advanced_trainer_recalls_to_healer_after_practising() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
    )
    policy.loremaster_step = 3
    state = CharacterState(level=15, room_name="Olive Grove", room_vnum="25204")

    decision = policy._loremaster_decision(state)

    assert decision.command == "recall"
    assert policy.waiting_for_move
    assert policy.practiced


def test_class_trainer_waits_for_practice_listing_after_stale_prompt() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
    )
    policy.loremaster_step = 2
    policy.prompt_ready = True
    state = CharacterState(level=13, room_name="The Secret Yard", room_vnum="3029")

    decision = policy._loremaster_decision(state)

    assert decision is None
    assert policy.loremaster_step == 2
    assert policy.prompt_ready is False


@pytest.mark.parametrize(
    ("character_class", "trainer_room", "trainer_keyword", "expected_path"),
    (
        (
            "mage",
            "3019",
            "guildmaster",
            (
                ("3054", "south"),
                ("3001", "south"),
                ("3005", "south"),
                ("3014", "west"),
                ("3013", "west"),
                ("3012", "south"),
                ("3017", "south"),
                ("3018", "east"),
            ),
        ),
        (
            "cleric",
            "3002",
            "guildmaster",
            (
                ("3054", "south"),
                ("3001", "south"),
                ("3005", "west"),
                ("3004", "north"),
                ("3003", "west"),
            ),
        ),
        (
            "thief",
            "3029",
            "guildmaster",
            (
                ("3054", "south"),
                ("3001", "south"),
                ("3005", "south"),
                ("3014", "south"),
                ("3025", "east"),
                ("3026", "south"),
                ("3027", "east"),
                ("3028", "south"),
            ),
        ),
        (
            "warrior",
            "3023",
            "guildmaster",
            (
                ("3054", "south"),
                ("3001", "south"),
                ("3005", "south"),
                ("3014", "east"),
                ("3015", "east"),
                ("3016", "south"),
                ("3021", "east"),
                ("3022", "south"),
            ),
        ),
        (
            "psionic",
            "3150",
            "guildmaster",
            (
                ("3054", "south"),
                ("3001", "south"),
                ("3005", "south"),
                ("3014", "east"),
                ("3015", "east"),
                ("3016", "east"),
                ("3041", "north"),
                ("3152", "north"),
                ("3151", "west"),
            ),
        ),
        (
            "brawler",
            "3218",
            "guildmaster",
            (
                ("3054", "south"),
                ("3001", "south"),
                ("3005", "south"),
                ("3014", "south"),
                ("3025", "west"),
                ("3024", "west"),
                ("3044", "south"),
                ("3206", "south"),
                ("3207", "east"),
            ),
        ),
        (
            "shifter",
            "3221",
            "guildmaster",
            (
                ("3054", "south"),
                ("3001", "south"),
                ("3005", "south"),
                ("3014", "south"),
                ("3025", "east"),
                ("3026", "east"),
                ("3045", "east"),
                ("3046", "north"),
                ("3219", "north"),
                ("3220", "west"),
            ),
        ),
        (
            "ranger",
            "3048",
            "ranger",
            (
                ("3054", "south"),
                ("3001", "south"),
                ("3005", "south"),
                ("3014", "south"),
                ("3025", "west"),
                ("3024", "south"),
            ),
        ),
        (
            "smithy",
            "3050",
            "craftsman",
            (
                ("3054", "south"),
                ("3001", "south"),
                ("3005", "south"),
                ("3014", "south"),
                ("3025", "east"),
                ("3026", "east"),
                ("3045", "east"),
                ("3046", "south"),
            ),
        ),
    ),
)
def test_level_ten_field_training_uses_each_midgaard_class_trainer(
    character_class: str,
    trainer_room: str,
    trainer_keyword: str,
    expected_path: tuple[tuple[str, str], ...],
) -> None:
    policy = StarterPolicy(
        _spec(**{"class": character_class, "subclass": None}),
        "swordfish",
        fastwalk_route=route_named("moria"),
        fastwalk_train_before_departure=True,
    )
    policy.latest_practice_balances = (2, 2)
    policy.selected_training_stat = "con"
    policy.fastwalk_stat_training_configured = True

    for room_vnum, expected_command in expected_path:
        decision = policy._fastwalk_training_decision(
            CharacterState(level=10, room_name="Midgaard", room_vnum=room_vnum)
        )
        assert decision is not None
        assert decision.command == expected_command

    trainer_decision = policy._fastwalk_training_decision(
        CharacterState(level=10, room_name="Trainer", room_vnum=trainer_room)
    )
    assert trainer_decision is not None
    assert trainer_decision.command == f"look {trainer_keyword}"


def test_level_fifteen_thief_uses_olive_grove_trainer_tier() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("plains aruncus"),
        fastwalk_train_before_departure=True,
    )
    policy.latest_practice_balances = (2, 2)
    policy.selected_training_stat = "con"
    policy.fastwalk_stat_training_configured = True
    expected_steps = (
        ("3054", "south"),
        ("3001", "south"),
        ("3005", "south"),
        ("3014", "east"),
        ("3015", "east"),
        ("3016", "east"),
        ("3041", "east"),
        ("3053", "east"),
        ("3503", "east"),
        ("3502", "south"),
        ("5261", "south"),
        ("5260", "south"),
        ("5259", "south"),
        ("5258", "east"),
        ("5262", "east"),
        ("5263", "south"),
        ("5264", "east"),
        ("5265", "east"),
        ("5266", "down"),
        ("5267", "east"),
        ("1701", "east"),
        ("1702", "north"),
        ("1704", "north"),
        ("1705", "north"),
        ("1706", "north"),
        ("1707", "north"),
        ("1708", "east"),
        ("1720", "east"),
        ("25200", "east"),
        ("25201", "east"),
        ("25202", "east"),
        ("25203", "south"),
        ("25205", "west"),
    )

    for room_vnum, expected_command in expected_steps:
        decision = policy._fastwalk_training_decision(
            CharacterState(level=15, room_name="Route", room_vnum=room_vnum)
        )
        assert decision is not None
        assert decision.command == expected_command
        assert "level-15 thief trainer" in decision.reason

    trainer = CharacterState(
        level=15,
        room_name="Olive Grove",
        room_vnum="25204",
    )
    decision = policy._fastwalk_training_decision(trainer)

    assert decision is not None
    assert decision.command == "look leader"
    route = policy._level_ten_class_trainer(trainer)
    assert route is not None
    assert route.return_to_healer["25205"] == "north"
    assert route.return_to_healer["25204"] == "east"
    assert route.healer_return_paths["25205"][-1] == "south"
    assert route.healer_return_paths["25204"][-1] == "west"


def test_level_fifteen_thief_stops_for_wandering_trainer_on_route() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("plains aruncus"),
        fastwalk_train_before_departure=True,
    )
    policy.latest_practice_balances = (2, 2)
    policy.selected_training_stat = "con"
    policy.fastwalk_stat_training_configured = True
    policy.room_targets["25202"] = ["bandit leader"]

    decision = policy._fastwalk_training_decision(
        CharacterState(level=15, room_name="Olive Grove", room_vnum="25202")
    )

    assert decision is not None
    assert decision.command == "look leader"


def test_class_training_does_not_continue_after_missing_trainer() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("plains aruncus"),
        fastwalk_train_before_departure=True,
    )
    policy.latest_practice_balances = (2, 2)
    policy.selected_training_stat = "con"
    policy.fastwalk_stat_training_configured = True
    trainer = CharacterState(
        level=15,
        room_name="Olive Grove",
        room_vnum="25204",
    )
    first = policy._fastwalk_training_decision(trainer)
    policy.observe_text("You do not see that here.\n")

    second = policy._fastwalk_training_decision(trainer)

    assert first is not None
    assert first.command == "look leader"
    assert second is not None
    assert second.command == "recall"
    assert policy.practiced
    assert policy.waiting_for_move
    assert policy.pending_training_events[-1].type == "training_deferred"


def test_level_eight_thief_does_not_visit_level_ten_guildmaster() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("moria"),
        fastwalk_hunt_stops=moria_level_seven_orc_hunt_stops(),
        fastwalk_train_before_departure=True,
    )
    policy.in_world = True
    policy.latest_practice_balances = (2, 2)
    policy.selected_training_stat = "con"
    policy.fastwalk_stat_training_configured = True
    state = CharacterState(
        level=8,
        hp=135,
        max_hp=135,
        mana=151,
        max_mana=151,
        move=220,
        max_move=220,
        position=7,
        room_name="By the Temple Altar",
        room_vnum="3054",
    )

    decision = policy._fastwalk_training_decision(state)

    assert decision is not None
    assert decision.command == "south"
    assert "Loremaster" in decision.reason


def test_fastwalk_walks_back_from_thief_guild_to_recall() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("moria"),
    )
    policy.in_world = True
    expected = (
        ("3028", "west"),
        ("3027", "north"),
        ("3026", "west"),
        ("3025", "north"),
        ("3014", "north"),
        ("3005", "north"),
    )
    for room_vnum, command in expected:
        policy.prompt_ready = True
        decision = policy.next_decision(
            CharacterState(
                level=10,
                hp=150,
                max_hp=150,
                mana=150,
                max_mana=150,
                move=220,
                max_move=220,
                position=7,
                room_name="Midgaard",
                room_vnum=room_vnum,
            )
        )
        assert decision is not None
        assert decision.command == command


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


def test_fastwalk_hunt_refills_water_before_long_route() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
        fastwalk_hunt_stops=(FieldHuntStop((), "goblin"),),
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_autoloot_configured = True
    policy.fastwalk_targetmode_configured = True
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
        inventory=[[{"short_desc": "a buffalo water skin", "quan": "1"}]],
    )

    commands = []
    for _ in range(6):
        policy.prompt_ready = True
        decision = policy.next_decision(state)
        assert decision is not None
        commands.append(decision.command)
        policy.after_command(decision)
        if decision.command == "south":
            state.room_vnum = "3005"
            state.room_name = "The Temple Square"
        elif decision.command == "north":
            state.room_vnum = "3001"
            state.room_name = "The Temple Of Midgaard"

    assert commands == [
        "south",
        "fill skin",
        "drink skin",
        "north",
        "get all.pie",
        "south",
    ]


def test_fastwalk_withdrawal_records_unavailable_field_resources() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(FieldHuntStop((), "goblin"),),
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(policy.fastwalk_route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_looked = True
    policy.needs_food = True

    decision = policy._fastwalk_hunt_plan_decision(
        CharacterState(
            level=17,
            hp=200,
            max_hp=200,
            mana=200,
            max_mana=200,
            move=200,
            max_move=200,
            position=7,
            room_name="The Front of the Inn",
            room_vnum="3570",
            inventory=[],
        )
    )

    assert decision is not None
    assert decision.command == "recall"
    assert policy.fastwalk_abort_reason == (
        "field expedition withdrew before target evaluation because "
        "food reserve was unavailable"
    )


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


def test_vault_preflight_verifies_oversized_sack_is_empty_before_stowing() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        vault_stow_items=("sack",),
        vault_required_free_weight=10,
    )
    state = CharacterState(
        room_name="Dragonhoard Bank, Midgaard Branch",
        room_vnum="3007",
        position=7,
        stats={"carry_wt": 138, "maxcarry_wt": 115},
    )

    assert policy._vault_stow_decision(state).command == "look in sack"
    policy.last_response = "A large sack contains:\n\r     Nothing.\n\r"
    assert policy._vault_stow_decision(state).command == "remove sack"
    assert policy._vault_stow_decision(state).command == "lodge sack"


def test_vault_preflight_preserves_nonempty_sack() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        vault_stow_items=("sack",),
        vault_required_free_weight=10,
    )
    state = CharacterState(
        room_name="Dragonhoard Bank, Midgaard Branch",
        room_vnum="3007",
        position=7,
    )

    assert policy._vault_stow_decision(state).command == "look in sack"
    policy.last_response = (
        "A large sack contains:\n\r"
        "     a black potion\n\r"
    )

    assert policy._vault_stow_decision(state) is None
    assert policy.failure == (
        "refused to vault 'sack' without proof that it is empty"
    )


def test_vault_preflight_leaves_after_first_capacity_rejection() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        vault_stow_items=("sack", "bracer"),
        vault_required_free_weight=10,
    )
    state = CharacterState(
        room_name="Dragonhoard Bank, Midgaard Branch",
        room_vnum="3007",
        position=7,
    )

    assert policy._vault_stow_decision(state).command == "look in sack"
    policy.last_response = "A large sack contains:\n\r     Nothing.\n\r"
    assert policy._vault_stow_decision(state).command == "remove sack"
    assert policy._vault_stow_decision(state).command == "lodge sack"
    policy.observe_text("You can't put that much weight into your vault.\n\r")

    decision = policy._vault_stow_decision(state)

    assert decision is not None
    assert decision.command == "west"
    assert policy.vault_storage_rejected is True
    assert policy.vault_stow_command_index == 2


def test_vault_preflight_records_acknowledged_lodges_and_wears_claims() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        vault_stow_items=("sleeves",),
        vault_claim_items=("collar", "vest"),
        vault_wear_claimed_items=True,
    )
    state = CharacterState(
        room_name="Dragonhoard Bank, Midgaard Branch",
        room_vnum="3007",
        position=7,
    )

    assert policy._vault_stow_decision(state).command == "remove sleeves"
    assert policy._vault_stow_decision(state).command == "lodge sleeves"
    policy.observe_text(
        "You lodge a pair of green scalemail sleeves in your vault.\n\r"
    )
    assert policy._vault_stow_decision(state).command == "claim collar"
    policy.observe_text("You get a war dog collar from your vault.\n\r")
    assert policy._vault_stow_decision(state).command == "wear collar"
    assert policy._vault_stow_decision(state).command == "claim vest"
    policy.observe_text("vest: you can't carry that much weight.\n\r")

    assert policy.vault_lodged_items == ["sleeves"]
    assert policy.vault_claimed_items == ["collar"]
    assert policy._vault_stow_decision(state).command == "score"


def test_vault_preflight_donates_verified_empty_oversized_container_when_full() -> None:
    sack = ObjectSource(
        4529,
        "sack large",
        "a large sack",
        15,
        (400, 0, 0, 0),
        0,
        weight=50,
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        vault_stow_items=("sack",),
        vault_required_free_weight=10,
        gear_catalog=GearCatalog({sack.vnum: sack}),
    )
    state = CharacterState(
        room_name="Dragonhoard Bank, Midgaard Branch",
        room_vnum="3007",
        position=7,
        stats={"carry_wt": 135, "maxcarry_wt": 140},
    )

    assert policy._vault_stow_decision(state).command == "look in sack"
    policy.last_response = "A large sack contains:\n\r     Nothing.\n\r"
    assert policy._vault_stow_decision(state).command == "remove sack"
    assert policy._vault_stow_decision(state).command == "lodge sack"
    policy.observe_text("You can't put that much weight into your vault.\n\r")

    disposal = policy._vault_stow_decision(state)

    assert disposal is not None
    assert disposal.command == "donate sack"
    policy.observe_text("You donate a large sack.\n\r")
    relieved_state = CharacterState(
        room_name="Dragonhoard Bank, Midgaard Branch",
        room_vnum="3007",
        position=7,
        stats={"carry_wt": 85, "maxcarry_wt": 140},
    )
    assert policy._vault_stow_decision(relieved_state).command == "score"
    assert policy.vault_storage_rejected is False


def test_vault_capacity_relief_can_resume_from_the_bakery() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        vault_stow_items=("circlet",),
        vault_required_free_weight=10,
    )

    decision = policy._vault_stow_decision(
        CharacterState(
            room_name="The Bakery",
            room_vnum="3009",
            position=7,
        )
    )

    assert decision is not None
    assert decision.command == "south"


def test_vault_capacity_relief_audits_and_stows_heavy_worn_gear() -> None:
    circlet = ObjectSource(
        108,
        "silver circlet",
        "a silver circlet",
        8,
        (0, 0, 0, 0),
        0,
        wear_flags=1 | (1 << 2),
        affects=((3, 1),),
        weight=1,
    )
    collar = ObjectSource(
        4538,
        "collar war dog",
        "a war dog collar",
        9,
        (0, 0, 0, 0),
        0,
        wear_flags=1 | (1 << 2),
        affects=((19, 1),),
        weight=20,
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        gear_catalog=GearCatalog({circlet.vnum: circlet, collar.vnum: collar}),
        vault_stow_items=("circlet",),
        vault_required_free_weight=10,
    )
    state = CharacterState(
        room_name="Dragonhoard Bank, Midgaard Branch",
        room_vnum="3007",
        position=7,
        stats={"carry_wt": 86, "maxcarry_wt": 90},
    )

    assert policy._vault_stow_decision(state).command == "remove circlet"
    assert policy._vault_stow_decision(state).command == "lodge circlet"
    assert policy._vault_stow_decision(state).command == "score"
    assert policy._vault_stow_decision(state).command == "eq all"

    policy.last_response = (
        "<worn around neck> a war dog collar\n"
        "<worn around neck> a silver circlet\n"
        "[weapon] a dagger"
    )
    assert policy._vault_stow_decision(state).command == "remove collar"
    assert policy._vault_stow_decision(state).command == "lodge collar"
    assert policy._vault_stow_decision(state).command == "score"

    state.stats["carry_wt"] = 66
    assert policy._vault_stow_decision(state).command == "west"


def test_empty_field_circuit_does_not_report_an_objective_kill() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(FieldHuntStop((), "war dog"),),
    )

    assert policy.fastwalk_objective_killed is False

    policy.completed_kills.append({"mob_name": "the war dog", "xp_gained": 295})

    assert policy.fastwalk_objective_killed is True


def test_field_circuit_excludes_unrelated_route_combat_from_objective_kills() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(FieldHuntStop((), "war dog"),),
    )
    policy.completed_kills.append(
        {"mob_name": "the goblin lieutenant", "xp_gained": 60}
    )

    assert policy.objective_kills == []
    assert policy.fastwalk_objective_killed is False


def test_noncombat_fastwalk_does_not_require_a_kill() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
    )

    assert policy.objective_kills == []
    assert policy.fastwalk_objective_killed is True


def test_required_field_items_respect_duplicate_quantity() -> None:
    inventory = [[{"short_desc": "a pink ice ring", "quan": "1"}]]

    assert starter._missing_required_inventory_items(
        inventory,
        ("pink ice ring", "pink ice ring"),
    ) == ["pink ice ring"]


def test_standalone_vault_maintenance_logs_out_at_healer() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        vault_stow_items=("cape",),
        vault_required_free_weight=10,
        vault_only=True,
    )
    policy.in_world = True
    policy.vault_stow_complete = True
    recall = CharacterState(
        level=7,
        hp=110,
        max_hp=110,
        mana=297,
        max_mana=297,
        move=130,
        max_move=210,
        room_name="The Temple Of Midgaard",
        room_vnum="3001",
    )

    policy.prompt_ready = True
    go_healer = policy.next_decision(recall)
    assert go_healer is not None
    assert go_healer.command == "north"
    policy.after_command(go_healer)

    healer = CharacterState(
        level=7,
        hp=110,
        max_hp=110,
        mana=297,
        max_mana=297,
        move=128,
        max_move=210,
        room_name="By the Temple Altar",
        room_vnum="3054",
    )
    policy.prompt_ready = True
    save = policy.next_decision(healer)
    assert save is not None
    assert save.command == "save"
    policy.after_command(save)

    policy.prompt_ready = True
    quit_game = policy.next_decision(healer)
    assert quit_game is not None
    assert quit_game.command == "quit"


@pytest.mark.parametrize(
    ("deposit", "cache_command"),
    ((False, "get ticket"), (True, "drop ticket")),
)
def test_fastwalk_world_cache_round_trip(
    deposit: bool,
    cache_command: str,
) -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("circus bearded lady"),
        fastwalk_world_cache_items=("ticket",),
    )

    states_and_commands = (
        (CharacterState(room_vnum="3054", position=7), "south"),
        (CharacterState(room_vnum="3001", position=7), "south"),
        (CharacterState(room_vnum="3005", position=7), "east"),
        (CharacterState(room_vnum="3006", position=7), "east"),
        (CharacterState(room_vnum="3007", position=7), cache_command),
        (CharacterState(room_vnum="3007", position=7), "west"),
        (CharacterState(room_vnum="3006", position=7), "west"),
        (CharacterState(room_vnum="3005", position=7), "north"),
    )
    for state, expected in states_and_commands:
        decision = policy._fastwalk_world_cache_decision(state, deposit=deposit)
        assert decision is not None
        assert decision.command == expected

    assert (
        policy._fastwalk_world_cache_decision(
            CharacterState(room_vnum="3001", position=7),
            deposit=deposit,
        )
        is None
    )
    phase = "post" if deposit else "preflight"
    assert getattr(policy, f"fastwalk_world_cache_{phase}_complete") is True


def test_post_hunt_cache_return_finishes_before_healer_recovery() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("circus bearded lady"),
        fastwalk_world_cache_items=("ticket",),
    )
    policy.fastwalk_world_cache_post_started = True
    policy.fastwalk_world_cache_post_returning = True
    state = CharacterState(
        area="Midgaard",
        room_name="The Temple Square",
        room_vnum="3005",
        hp=100,
        max_hp=110,
        mana=30,
        max_mana=300,
        move=20,
        max_move=210,
        position=7,
    )

    assert policy._recovery_decision(state) is None
    decision = policy._fastwalk_world_cache_decision(state, deposit=True)
    assert decision is not None
    assert decision.command == "north"
    assert decision.reason == "return from the Midgaard world-item cache"


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
    for index in range(7):
        policy.prompt_ready = True
        decision = policy.next_decision(state)
        assert decision is not None
        commands.append(decision.command)
        policy.after_command(decision)
        if index == 0:
            policy.last_response = "A large sack contains:\n\r     Nothing.\n\r"

    assert commands == [
        "look in sack",
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


def test_level_seven_fastwalk_uses_known_invisibility() -> None:
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
    policy.known_skills.add("invis")
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
    assert decision.command == "cast invis"


def test_mage_casts_known_armor_before_field_travel() -> None:
    policy = StarterPolicy(_spec(character_class="mage"), "swordfish")
    policy.known_skills.add("armor")
    state = CharacterState(mana=50, max_mana=100, affects=[])

    decision = policy._fastwalk_caster_mitigation_decision(state)

    assert decision is not None
    assert decision.command == "cast 'armor'"
    assert policy._fastwalk_caster_mitigation_decision(state) is None


def test_active_mitigation_is_not_recast() -> None:
    policy = StarterPolicy(_spec(character_class="psionic"), "swordfish")
    policy.known_skills.add("thought shield")
    state = CharacterState(
        mana=50,
        max_mana=100,
        affects=[[{"name": "thought shield", "duration": "8"}]],
    )

    assert policy._fastwalk_caster_mitigation_decision(state) is None


def test_mitigation_preserves_field_mana_reserve() -> None:
    policy = StarterPolicy(_spec(character_class="cleric"), "swordfish")
    policy.known_skills.add("armor")
    state = CharacterState(mana=7, max_mana=100, affects=[])

    assert policy._fastwalk_caster_mitigation_decision(state) is None


def test_mage_fastwalk_runner_enables_invisibility_from_capability(tmp_path) -> None:
    runner = StarterBotRunner(
        _spec(),
        tmp_path / "profile.yaml",
        fastwalk_route=gnome_hermit_hunt_route(),
    )

    assert runner.fastwalk_require_invisibility is True


def test_level_eight_fastwalk_detours_to_loremaster_with_new_practices() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_train_before_departure=True,
        selected_training_stat="int",
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
        selected_training_stat="con",
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
        selected_training_stat="con",
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


def test_level_ten_thief_reopens_spent_types_for_missing_backstab_chain() -> None:
    policy = StarterPolicy(
        _spec(
            name="Kestrel",
            race="drow",
            gender="male",
            **{"class": "thief", "subclass": "ninja"},
        ),
        "swordfish",
        fastwalk_route=route_named("plains aruncus"),
        fastwalk_train_before_departure=True,
        practice_types_spent=frozenset({"physical", "intellectual"}),
        selected_training_stat="con",
    )
    policy.in_world = True
    policy.capability_audit_complete = True
    policy.known_skills.update(
        {
            "second attack",
            "hide",
            "sneak",
            "stealth techniques",
            "dodge",
            "parry",
        }
    )
    policy.latest_practice_balances = (1, 1)
    policy.fastwalk_stat_training_configured = True
    state = CharacterState(
        level=13,
        hp=194,
        max_hp=194,
        mana=199,
        max_mana=199,
        move=270,
        max_move=270,
        room_name="By the Temple Altar",
        room_vnum="3054",
    )

    assert policy._critical_damage_unlock(state) == "backstab"
    assert policy._training_practice_type_exclusions(state) == frozenset()
    assert policy._needs_fastwalk_training(state)
    decision = policy._fastwalk_training_decision(state)

    assert decision is not None
    assert decision.command == "south"
    assert "thief trainer" in decision.reason


def test_thief_uses_physical_practice_when_intellectual_gateways_are_blocked() -> None:
    policy = StarterPolicy(
        _spec(
            name="Kestrel",
            race="drow",
            gender="male",
            **{"class": "thief", "subclass": "ninja"},
        ),
        "swordfish",
    )
    listing = parse_practice_listing(
        """
Skills known:
armed combat knowledge: 41%    second attack: 65%
stealth techniques: 56%       hide: 23%
sneak: 99%                    defense knowledge: 55%
dodge: 50%                    parry: 43%
Skills which may be learned:
unarmed combat knowledge: 1%
You have 2 physical and 0 intellectual practices remaining.
"""
    )
    policy.known_skills.update(listing.known)
    policy.known_skill_levels.update(listing.known)

    assert policy._critical_damage_unlock(
        CharacterState(level=14),
        listing,
    ) == "second attack"


def test_thief_trainer_spends_available_physical_practice_on_second_attack() -> None:
    policy = StarterPolicy(
        _spec(
            name="Kestrel",
            race="drow",
            gender="male",
            **{"class": "thief", "subclass": "ninja"},
        ),
        "swordfish",
        practice_types_spent=frozenset({"physical", "intellectual"}),
    )
    policy.loremaster_step = 2
    policy.text = """
Skills known:
armed combat knowledge: 41%    second attack: 65%
stealth techniques: 56%       hide: 23%
sneak: 99%                    defense knowledge: 55%
dodge: 50%                    parry: 43%
Skills which may be learned:
unarmed combat knowledge: 1%
You have 2 physical and 0 intellectual practices remaining.
"""
    state = CharacterState(
        level=14,
        room_name="The Thieves Guild",
        room_vnum="3029",
    )

    decision = policy._loremaster_decision(state)

    assert decision is not None
    assert decision.command == "practice second attack"


def test_level_capped_damage_gateway_advances_the_next_control_chain() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("plains aruncus"),
        fastwalk_train_before_departure=True,
        practice_types_spent=frozenset({"physical", "intellectual"}),
        rejected_practice_skills=frozenset({"stealth techniques"}),
        selected_training_stat="con",
    )
    policy.known_skills.update(
        {
            "second attack",
            "hide",
            "sneak",
            "stealth techniques",
            "dodge",
            "parry",
        }
    )
    policy.known_skill_levels.update(
        {
            "second attack": 65,
            "hide": 23,
            "sneak": 99,
            "stealth techniques": 56,
            "dodge": 50,
            "parry": 29,
        }
    )
    policy.latest_practice_balances = (1, 1)
    policy.fastwalk_stat_training_configured = True
    state = CharacterState(level=13)

    assert policy._critical_damage_unlock(state) == "knife toss"
    assert policy._training_practice_type_exclusions(state) == frozenset()
    assert policy._needs_fastwalk_training(state)


def test_smithy_unfinished_counterbalance_forces_trainer_visit_without_practices() -> None:
    sword = ObjectSource(
        3021,
        "sword",
        "a steel sword",
        5,
        (0, 2, 5, 1),
        10,
        wear_flags=1 | (1 << 13),
    )
    policy = StarterPolicy(
        _spec(**{"class": "smithy", "subclass": None}),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_train_before_departure=True,
        practice_types_spent=frozenset({"physical", "intellectual"}),
        counterbalance_preparation_required=True,
        selected_training_stat="con",
        gear_catalog=GearCatalog({sword.vnum: sword}),
    )
    policy.in_world = True
    policy.latest_practice_balances = (0, 0)
    policy.fastwalk_stat_training_configured = True
    policy.gear_worn = [sword]
    state = CharacterState(
        level=10,
        hp=120,
        max_hp=120,
        mana=150,
        max_mana=150,
        move=220,
        max_move=220,
        room_name="By the Temple Altar",
        room_vnum="3054",
    )

    assert policy._needs_fastwalk_training(state)
    decision = policy._fastwalk_training_decision(state)

    assert decision is not None
    assert decision.command == "south"
    assert "smithy trainer" in decision.reason


def test_fastwalk_audits_unknown_practice_balance_before_departure() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_train_before_departure=True,
        selected_training_stat="int",
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
        selected_training_stat="con",
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
        selected_training_stat="int",
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
        selected_training_stat="int",
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
        selected_training_stat="int",
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
        selected_training_stat="int",
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
        "field expedition could not establish invisibility at the safe origin"
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
        hp=20,
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


def test_fastwalk_hunt_circuit_continues_between_fights_above_threshold() -> None:
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
    assert decision.command == "south"


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


def test_consider_only_fastwalk_flees_unexpected_combat() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(
            FieldHuntStop((), "fanatical goblin guard", consider_only=True),
        ),
    )
    policy.in_world = True
    policy.combat_active = True
    policy.prompt_ready = True
    state = CharacterState(
        level=10,
        hp=130,
        max_hp=130,
        mana=350,
        max_mana=350,
        move=120,
        max_move=240,
        position=8,
        room_name="On a small trail",
        room_vnum="4521",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "flee"
    assert "no-combat field probe" in decision.reason
    assert policy.fastwalk_emergency_recall_pending is True


def test_consider_only_fastwalk_allows_source_confirmed_active_below_band_mobile() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(
            FieldHuntStop(
                (),
                "fanatical goblin guard",
                consider_only=True,
                trivial_bystanders=("hideous bogleech",),
            ),
        ),
        source_mobile_level_ranges={"hideous bogleech": (10, 14)},
    )
    policy.in_world = True
    policy.combat_active = True
    policy.active_target = "a hideous bogleech"
    policy.prompt_ready = True
    state = CharacterState(
        level=18,
        hp=254,
        max_hp=254,
        mana=242,
        max_mana=242,
        move=150,
        max_move=320,
        position=8,
        room_name="The Bog",
        room_vnum="11502",
    )

    decision = policy.next_decision(state)

    assert decision is None or decision.command != "flee"
    assert policy.fastwalk_emergency_recall_pending is False
    assert policy.fastwalk_abort_reason is None


def test_consider_only_fastwalk_finishes_confirmed_below_band_interruption() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("gnome treasury"),
        fastwalk_hunt_stops=gnome_treasurer_research_stops(),
    )
    policy.in_world = True
    policy.combat_active = True
    policy.prompt_ready = True
    policy.active_target = "the hobgoblin soldier"
    state = CharacterState(
        level=13,
        hp=194,
        max_hp=194,
        mana=199,
        max_mana=199,
        move=180,
        max_move=270,
        position=8,
        room_name="Guarded Room",
        room_vnum="1571",
        enemies=[[
            {
                "name": "the hobgoblin soldier",
                "level": "5",
                "hp": "100",
            }
        ]],
    )

    decision = policy.next_decision(state)

    assert decision is None
    assert policy.fastwalk_emergency_recall_pending is False
    assert policy.fastwalk_abort_reason is None


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
        move=10,
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


def test_fastwalk_research_builds_a_target_stop_at_requested_exit(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    class CapturingRunner:
        def __init__(self, *_args, **kwargs) -> None:
            captured.update(kwargs)

        async def run(self) -> None:
            return None

    monkeypatch.setattr(starter, "StarterBotRunner", CapturingRunner)
    monkeypatch.setattr(starter, "load_character_spec", lambda _path: _spec())

    asyncio.run(
        starter.run_fastwalk_research_profile(
            "profiles/test.yaml",
            "gnome mine",
            explore_direction="north",
            explore_depth=3,
            attack_target="hermit",
        )
    )

    assert captured["fastwalk_hunt_stops"] == (
        FieldHuntStop(("north", "north", "north"), "hermit"),
    )


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


def test_fastwalk_research_recalls_when_an_outbound_step_is_blocked() -> None:
    route = route_named("moria")
    policy = StarterPolicy(_spec(), "swordfish", fastwalk_route=route)
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = 3
    policy.pending_fastwalk_outbound_move = True

    policy.observe_text("Alas, you cannot go that way.\n")

    assert policy.fastwalk_abort_reason == (
        "official fastwalk 'moria' was blocked before its endpoint"
    )
    assert policy.fastwalk_returning is True
    policy.prompt_ready = True
    recall = policy.next_decision(CharacterState(room_vnum="4011", position=7))

    assert recall is not None
    assert recall.command == "recall"
    assert recall.reason == "return safely after a blocked fastwalk step"


def test_fastwalk_exhaustion_rolls_back_failed_step_and_recalls() -> None:
    route = route_named("moria")
    policy = StarterPolicy(_spec(), "swordfish", fastwalk_route=route)
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = 3
    policy.pending_fastwalk_outbound_move = True
    policy.pending_travel_origin = "4011"
    policy.waiting_for_move = True

    policy.observe_text("You are too exhausted.\n")

    assert policy.fastwalk_outbound_index == 2
    assert policy.pending_fastwalk_outbound_move is False
    assert policy.pending_travel_origin is None
    assert policy.waiting_for_move is False
    assert policy.fastwalk_emergency_recall_pending is True
    recall = policy.next_decision(CharacterState(room_vnum="4011", position=7))

    assert recall is not None
    assert recall.command == "recall"
    assert recall.reason == "return safely after fastwalk movement exhaustion"


def test_fastwalk_accepts_an_expected_aggressive_endpoint_target() -> None:
    route = gnome_hermit_hunt_route()
    policy = StarterPolicy(
        _spec(**{"class": "warrior", "subclass": "knight"}),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=gnome_hermit_hunt_stops(),
        fastwalk_kill_limit=1,
    )
    policy.fastwalk_outbound_index = len(route.commands)

    policy.observe_text("A hermit misses you.\n")

    assert policy.combat_active is True
    assert policy.fastwalk_attack_target == "hermit"
    assert policy.unapproved_field_attacker is None
    policy.in_world = True
    policy.prompt_ready = True

    assert (
        policy.next_decision(
            CharacterState(
                level=7,
                hp=150,
                max_hp=150,
                mana=100,
                max_mana=100,
                position=6,
                room_vnum="1589",
            )
        )
        is None
    )
    assert policy.fastwalk_attack_started is True


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


def test_fastwalk_consider_waits_for_its_delayed_response() -> None:
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
    policy.observe_text("You discover a toy soldier's hands in your wallet!\n")
    policy.prompt_ready = True

    assert policy.next_decision(cave) is None

    policy.observe_text("The kobold looks like an easy kill.\n")
    policy.prompt_ready = True
    attack = policy.next_decision(cave)

    assert attack is not None
    assert attack.command == "kill kobold"


def test_consider_response_does_not_replace_exact_field_target_identity() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.current_room = "6602"
    policy.room_targets["6602"] = ["old wrinkled nanny"]
    policy.room_target_counts["6602"] = {"old wrinkled nanny": 1}
    policy.consider_response_pending = True

    policy.observe_text("The nanny looks like an easy kill.\n")

    assert policy.consider_response_pending is False
    assert policy.room_target_counts["6602"] == {"old wrinkled nanny": 1}


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


def test_consider_only_probe_records_an_absent_target_for_campaign_evidence() -> None:
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

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "look"
    assert policy.fastwalk_hunt_stop_skipped is True
    assert policy.fastwalk_target_absent is True


def test_fastwalk_research_matches_cli_target_case_after_stale_room_update() -> None:
    route = route_named("circus midget")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(
            FieldHuntStop(("north",), "Illusionist", consider_only=True),
        ),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    policy.fastwalk_hunt_move_index = 1
    policy.fastwalk_hunt_looked = True
    policy.current_room = "4410"
    policy.room_targets["4410"] = ["bobby's mother", "illusionist"]
    policy.room_target_counts["4410"] = {
        "bobby's mother": 1,
        "illusionist": 1,
    }
    state = CharacterState(
        level=7,
        hp=123,
        max_hp=123,
        mana=145,
        max_mana=145,
        move=193,
        max_move=210,
        room_name="The Tent of the Illusionist",
        room_vnum="4410",
        position=7,
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "consider Illusionist"
    assert policy.fastwalk_hunt_stop_skipped is False


def test_consider_only_probe_can_assess_duplicate_matching_targets() -> None:
    route = route_named("gnome mine")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(
            FieldHuntStop((), "hobgoblin miner", consider_only=True),
        ),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    policy.fastwalk_hunt_looked = True
    policy.current_room = "1563"
    state = CharacterState(
        level=7,
        hp=157,
        max_hp=157,
        mana=138,
        max_mana=138,
        move=145,
        max_move=210,
        room_name="Mine Shaft",
        room_vnum="1563",
        position=7,
    )
    policy.observe_text(
        "A hobgoblin miner stands here looking for gold.\n"
        "A hobgoblin miner stands here looking for gold.\n"
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "consider miner"
    assert policy.fastwalk_hunt_stop_skipped is False


def test_field_hunt_can_allow_a_bounded_count_of_identical_targets() -> None:
    route = route_named("gnome mine")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(
            FieldHuntStop(
                (),
                "hobgoblin miner",
                maximum_target_count=2,
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
    policy.current_room = "1563"
    state = CharacterState(
        level=7,
        hp=157,
        max_hp=157,
        mana=138,
        max_mana=138,
        move=145,
        max_move=210,
        room_name="Mine Shaft",
        room_vnum="1563",
        position=7,
    )
    policy.observe_text(
        "A hobgoblin miner stands here looking for gold.\n"
        "A hobgoblin miner stands here looking for gold.\n"
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "consider miner"
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


def test_field_circuit_treats_zero_duration_invisibility_as_active() -> None:
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
    assert decision.command == "west"
    assert policy.fastwalk_hunt_move_index == 1


def test_field_training_selects_constitution_for_martial_survivability() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief"}, subclass="ninja"),
        "swordfish",
        fastwalk_route=route_named("circus bearded lady"),
        fastwalk_train_before_departure=True,
    )
    state = CharacterState(
        level=7,
        xp_to_next_level=78,
        progress={"xplvl": 5800},
        position=7,
    )

    decision = policy._fastwalk_training_decision(state)

    assert decision is not None
    assert decision.command == "train con"
    assert "next stat advance" in decision.reason


def test_field_training_selects_constitution_before_final_level_window() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "warrior"}, subclass="knight"),
        "swordfish",
        fastwalk_route=route_named("circus bearded lady"),
        fastwalk_train_before_departure=True,
    )
    state = CharacterState(
        level=7,
        xp_to_next_level=1478,
        progress={"xplvl": 5800},
        position=7,
    )

    assert policy._needs_fastwalk_training(state)
    decision = policy._fastwalk_training_decision(state)

    assert decision is not None
    assert decision.command == "train con"


def test_field_training_selects_strength_under_carry_pressure() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "mage"}, subclass="warlock"),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_train_before_departure=True,
        selected_training_stat="int",
    )
    state = CharacterState(
        level=8,
        position=7,
        stats={"carry_wt": 98, "maxcarry_wt": 115},
    )

    decision = policy._fastwalk_training_decision(state)

    assert decision is not None
    assert decision.command == "train str"


def test_field_training_keeps_persisted_preferred_stat_selection() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "warrior"}, subclass="knight"),
        "swordfish",
        fastwalk_route=route_named("circus bearded lady"),
        fastwalk_train_before_departure=True,
        selected_training_stat="con",
    )
    policy.practiced = True
    state = CharacterState(
        level=7,
        xp_to_next_level=1478,
        progress={"xplvl": 5800},
        position=7,
    )

    assert not policy._needs_fastwalk_training(state)


def test_stat_training_skips_stats_marked_maxed_in_score() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "mage"}, subclass="warlock"),
        "swordfish",
        fastwalk_route=route_named("circus bearded lady"),
        fastwalk_train_before_departure=True,
    )
    policy.observe_text(
        "Int: 25 (25)+      Aggro dam: 0\n"
        "Con: 13 (12)      Move: 180/180\n"
    )
    state = CharacterState(
        level=7,
        xp_to_next_level=78,
        progress={"xplvl": 5800},
        position=7,
    )

    decision = policy._fastwalk_training_decision(state)

    assert policy.maxed_stats == {"int"}
    assert policy.permanent_stats == {"int": 25, "con": 12}
    assert decision is not None
    assert decision.command == "train con"


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
    assert "2 useful-band or unknown active enemies" in decision.reason
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


def test_fastwalk_equips_and_audits_required_loot_before_leaving_stop() -> None:
    route = route_named("ambush")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=(
            FieldHuntStop(
                (),
                "war dog",
                post_actions=("wear collar", "eq all"),
                required_items=("war dog collar",),
            ),
        ),
    )
    policy.in_world = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_stop_killed = True
    policy.prompt_ready = True
    state = CharacterState(
        hp=105,
        max_hp=105,
        mana=289,
        max_mana=289,
        move=210,
        max_move=210,
        position=7,
        room_name="In a forest clearing",
        room_vnum="4505",
        inventory=[{"short_desc": "a war dog collar", "quan": "1"}],
    )

    wear = policy.next_decision(state)
    audit = policy.next_decision(state)

    assert wear is not None
    assert wear.command == "wear collar"
    assert audit is not None
    assert audit.command == "eq all"


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


def test_gnome_small_troll_hunt_requires_high_health_and_exact_target() -> None:
    stops = gnome_small_troll_hunt_stops()

    assert len(stops) == 1
    assert stops[0].target == "small troll"
    assert stops[0].minimum_health_ratio == 0.675
    assert stops[0].exact_target is True


def test_field_circuit_waits_for_pending_invisibility_result() -> None:
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
    policy.after_command(cast)
    policy.prompt_ready = True

    assert policy.next_decision(state) is None
    assert policy.fastwalk_invisibility_attempts == 1


@pytest.mark.parametrize(
    "failure_text",
    (
        "You fail to correctly recite the spell!\n\r",
        "You fail miserably.\n\r",
    ),
)
def test_failed_pending_invisibility_can_be_retried(
    failure_text: str,
) -> None:
    route = route_named("ambush")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_require_invisibility=True,
        fastwalk_hunt_stops=(FieldHuntStop((), "goblin"),),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_preflight_food_attempted = True
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
    policy.after_command(cast)
    policy.observe_text(failure_text)
    policy.prompt_ready = True

    retry = policy.next_decision(state)

    assert retry is not None
    assert retry.command == "cast invis"
    assert policy.fastwalk_invisibility_attempts == 2


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


def test_fastwalk_tracks_short_proper_name_when_full_room_target_flees() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("circus bearded lady"),
        fastwalk_attack_target="Ivan the Strongman",
    )
    policy.fastwalk_attack_started = True
    policy.combat_active = True
    policy.active_target = "Ivan the Strongman"

    policy.observe_text("Ivan leaves east.\nIvan has fled!\n")

    assert policy.combat_active is False
    assert policy.fastwalk_pursuit_direction == "east"


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


def test_instant_trivial_combat_remains_resolved_for_utility_run() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        liquidate_loot=True,
    )
    policy.current_room = "3015"

    policy.observe_text(
        "The drunk yells exclaiming 'Monster! Kill! Banzai!'\n"
        "The drunk misses you.\n"
        "Your pierce grazes the drunk.\n"
        "The drunk is DEAD!!\n"
        "You receive 10 experience points for the kill.\n"
    )

    assert policy.combat_active is False
    assert policy.utility_abort_reason is None


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


def test_combat_can_reserve_sanctuary_for_a_later_high_risk_policy() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=forest_bear_claws_hunt_route(),
        use_sanctuary_potions=False,
    )
    policy.combat_pouch_potions.update({"purple": 1})
    state = CharacterState(
        hp=100,
        max_hp=100,
        position=6,
        room_name="Forest",
        room_vnum="18026",
    )

    decision = policy._combat_pouch_potion_decision(state)

    assert decision is None
    assert policy.combat_pouch_potions == {"purple": 1}


def test_combat_reserves_sanctuary_for_below_band_required_loot_kill() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=starter.daycare_ring_hunt_route(),
    )
    policy.active_target = "abused and old doll"
    policy.fastwalk_below_band_targets.add("abused and old doll")
    policy.combat_pouch_potions.update({"purple": 1})
    state = CharacterState(
        hp=100,
        max_hp=100,
        position=6,
        room_name="Day Care Center",
        room_vnum="6605",
    )

    decision = policy._combat_pouch_potion_decision(state)

    assert decision is None
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


def test_hunt_records_safe_abort_after_low_health_incidental_kill() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("highland keeper"),
        fastwalk_hunt_stops=highland_keeper_hunt_stops(),
        fastwalk_attack_target="keeper",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = 1
    policy.fastwalk_requested_target = "keeper of the tower"
    policy.current_room = "11518"
    policy.pending_loot_rooms.add("11518")
    policy.fastwalk_last_kill_target = "hideous bogleech"
    highlands = CharacterState(
        room_name="The Highlands",
        room_vnum="11518",
        position=7,
        hp=70,
        max_hp=100,
    )

    loot = policy.next_decision(highlands)
    assert loot is not None
    policy.after_command(loot)
    policy.prompt_ready = True
    sacrifice = policy.next_decision(highlands)
    assert sacrifice is not None
    assert sacrifice.command == "sacrifice corpse"
    policy.after_command(sacrifice)
    policy.prompt_ready = True
    inventory = policy.next_decision(highlands)
    assert inventory is not None
    assert inventory.command == "inventory"
    policy.after_command(inventory)
    policy.prompt_ready = True

    recall = policy.next_decision(highlands)

    assert recall is not None
    assert recall.command == "recall"
    assert "incidental" in (policy.fastwalk_abort_reason or "")
    assert "before its endpoint" in (policy.fastwalk_abort_reason or "")


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


def test_fastwalk_withdraws_from_unidentified_aggressive_combat() -> None:
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

    policy.prompt_ready = True
    flee = policy.next_decision(tunnel)

    assert flee is not None
    assert flee.command == "flee"
    assert "bypass consider" in flee.reason


def test_fastwalk_returns_when_a_field_move_does_not_leave_its_origin() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_hunt_stops=foundry_level_seven_hunt_stops(),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.current_room = "109"
    policy.pending_travel_origin = "109"
    policy.pending_fastwalk_hunt_move = True

    decision = policy.next_decision(
        CharacterState(room_name="Muddy Tunnel", room_vnum="109", position=7)
    )

    assert decision is not None
    assert decision.command == "recall"
    assert "did not complete" in decision.reason


def test_field_hunt_returns_after_a_drop_leaves_less_than_five_weight_free() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_hunt_stops=foundry_level_seven_hunt_stops(),
    )
    policy.completed_kills.append({"mob_name": "Golgog", "xp_gained": 100})
    state = CharacterState(
        room_name="Golgog's Hall",
        room_vnum="113",
        position=7,
        stats={"carry_wt": 86, "maxcarry_wt": 90},
    )

    decision = policy._fastwalk_hunt_plan_decision(state)

    assert decision is not None
    assert decision.command == "recall"
    assert "carry capacity" in decision.reason


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


def test_fastwalk_flees_a_directly_worded_attacker_without_level_evidence() -> None:
    route = route_named("gnome mine")
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_attack_target="hobgoblin miner",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = 4
    state = CharacterState(
        room_name="The Main Street",
        room_vnum="3016",
        hp=157,
        max_hp=157,
        mana=138,
        max_mana=138,
        move=193,
        max_move=210,
        position=6,
    )

    policy.observe_text("The drunk misses you.\n")
    decision = policy.next_decision(state)

    assert policy.unapproved_field_attacker is None
    assert policy.active_target == "The drunk"
    assert policy.awaiting_enemy_assessment is True
    assert decision is None

    policy.prompt_ready = True
    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "flee"
    assert "unidentified field attacker" in decision.reason


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


def test_school_accessory_route_resumes_from_northern_cage_hall() -> None:
    route = starter.school_accessory_hunt_route()
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=starter.school_wrist_float_hunt_stops(),
    )
    state = CharacterState(
        area="Mud School",
        room_name="Advanced Combat Training",
        room_vnum="3716",
        hp=100,
        max_hp=100,
        mana=100,
        max_mana=100,
        move=100,
        max_move=100,
        position=7,
    )

    decision = policy._fastwalk_research_decision(state)

    assert decision is not None
    assert decision.command == "open east"
    assert policy.fastwalk_hunt_stop_index == 1
    assert policy.fastwalk_hunt_move_index == 6


def test_school_accessory_route_resumes_through_obstacle_course_portal() -> None:
    route = starter.school_accessory_hunt_route()
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=starter.school_wrist_float_hunt_stops(),
    )
    endpoint = CharacterState(
        area="Mud School",
        room_name="End of the Obstacle Course",
        room_vnum="3710",
        hp=100,
        max_hp=100,
        mana=100,
        max_mana=100,
        move=100,
        max_move=100,
        position=7,
    )

    inspect = policy._fastwalk_research_decision(endpoint)
    enter = policy._fastwalk_research_decision(endpoint)

    assert inspect is not None and inspect.command == "look"
    assert enter is not None and enter.command == "enter portal"
    assert policy.fastwalk_hunt_stop_index == 0


def test_school_accessory_portal_exit_precedes_missing_food_gate() -> None:
    route = starter.school_accessory_hunt_route()
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=starter.school_wrist_float_hunt_stops(),
    )
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_looked = True
    policy.needs_food = True
    endpoint = CharacterState(
        area="Mud School",
        room_name="End of the Obstacle Course",
        room_vnum="3710",
        room_flags=["indoors", "safe", "no_recall"],
        hp=100,
        max_hp=100,
        mana=100,
        max_mana=100,
        move=100,
        max_move=100,
        position=7,
    )

    decision = policy._fastwalk_hunt_plan_decision(endpoint)

    assert decision is not None and decision.command == "enter portal"
    assert policy.fastwalk_hunt_action_index == 1
    assert policy.failure is None


def test_school_accessory_route_recovers_from_rejected_endpoint_recall() -> None:
    route = starter.school_accessory_hunt_route()
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=starter.school_wrist_float_hunt_stops(),
    )
    policy.fastwalk_returning = True
    endpoint = CharacterState(
        area="Mud School",
        room_name="End of the Obstacle Course",
        room_vnum="3710",
        hp=100,
        max_hp=100,
        mana=100,
        max_mana=100,
        move=100,
        max_move=100,
        position=7,
    )

    decision = policy._fastwalk_research_decision(endpoint)

    assert decision is not None and decision.command == "look"
    assert policy.fastwalk_returning is False
    assert policy.failure is None


def test_liquidation_escapes_no_recall_school_before_planning_sales() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        liquidate_loot=True,
    )
    policy.in_world = True
    policy.prompt_ready = True
    endpoint = CharacterState(
        area="Mud School",
        room_name="End of the Obstacle Course",
        room_vnum="3710",
        room_flags=["indoors", "safe", "no_recall"],
        hp=100,
        max_hp=100,
        mana=100,
        max_mana=100,
        move=100,
        max_move=100,
        position=7,
    )

    inspect = policy.next_decision(endpoint)
    policy.prompt_ready = True
    enter = policy.next_decision(endpoint)

    assert inspect is not None and inspect.command == "look imp"
    assert enter is not None and enter.command == "enter portal"
    assert policy.failure is None


def test_utility_run_allows_required_combat_while_escaping_school() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        liquidate_loot=True,
    )

    assert policy._is_noncombat_utility_run is True

    policy.course_started = True

    assert policy._is_noncombat_utility_run is False

    policy.course_complete = True

    assert policy._is_noncombat_utility_run is True


def test_school_accessory_route_finishes_without_recalling_from_healer() -> None:
    route = starter.school_accessory_hunt_route()
    stops = starter.school_wrist_float_hunt_stops()
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=stops,
    )
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_stop_index = len(stops)
    healer = CharacterState(
        area="Midgaard",
        room_name="By the Temple Altar",
        room_vnum="3054",
        hp=100,
        max_hp=100,
        mana=100,
        max_mana=100,
        move=100,
        max_move=100,
        position=7,
    )

    decision = policy._fastwalk_research_decision(healer)

    assert decision is None
    assert policy.fastwalk_returning is True
    assert policy.failure is None


def test_school_accessory_route_resumes_exit_from_final_combat() -> None:
    route = starter.school_accessory_hunt_route()
    stops = starter.school_wrist_float_hunt_stops()
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route,
        fastwalk_hunt_stops=stops,
    )
    final_combat = CharacterState(
        area="Mud School",
        room_name="Final Combat",
        room_vnum="3722",
        hp=100,
        max_hp=100,
        mana=100,
        max_mana=100,
        move=100,
        max_move=100,
        position=7,
    )

    unlock = policy._fastwalk_research_decision(final_combat)
    policy.fastwalk_hunt_action_index = 1
    open_door = policy._fastwalk_research_decision(final_combat)

    assert unlock is not None and unlock.command == "unlock north"
    assert open_door is not None and open_door.command == "open north"
    assert policy.fastwalk_hunt_stop_index == len(stops) - 1


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


def test_fastwalk_recall_accepts_midgaard_text_header_without_room_info() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry captain"),
        fastwalk_attack_target="Ushog",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.fastwalk_returning = True
    # Reproduce stale GMCP identity: the tracked room already says 3001 even
    # though the character has travelled into the field.
    policy.current_room = "3001"
    policy.after_command(BotDecision("recall", "return after field combat"))

    policy.observe_text(
        "The Temple Of Midgaard\n"
        "[Exits: north south up]\n"
        "<110/110 hits 293/293 mana 105/210 move [Midgaard]>\n"
    )
    policy.prompt_ready = True
    temple = CharacterState(
        area="Midgaard",
        room_name="The Temple Of Midgaard",
        room_vnum="3001",
        hp=110,
        max_hp=110,
        move=105,
        max_move=210,
        position=7,
    )

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


def test_targetmode_inventory_remains_usable_by_starter_policy() -> None:
    parser = ObservationParser()
    state = CharacterState()

    for event in parser.feed_gmcp(
        'Char.Items [[{"quan":"1",'
        '"short_desc":"[#4871] a notched scimitar"}]]'
    ):
        state.apply(event)

    assert _inventory_descriptions(state.inventory) == ["a notched scimitar"]
    assert state.inventory[0][0]["target_selector"] == "#4871"


def test_connection_close_discards_all_ephemeral_mobile_selectors() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.room_target_selectors = {
        "4014": {"the patrolling guard": ["#4866", "#4872"]}
    }
    policy.active_target_selector = "#4866"
    policy.consider_target_selector = "#4866"

    policy.on_connection_closed()

    assert policy.room_target_selectors == {}
    assert policy.active_target_selector is None
    assert policy.consider_target_selector is None


def test_connection_close_during_field_run_forces_safe_healer_return() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("foundry"),
        fastwalk_hunt_stops=foundry_level_six_hunt_stops(),
    )
    policy.in_world = True
    policy.login_authenticated = True
    policy.prompt_ready = True
    policy.query_world_time = False
    policy.provisioned = True
    policy.food_attempted = True
    policy.drink_attempted = True
    policy.pending_travel_origin = "1124"
    policy.pending_fastwalk_hunt_move = True

    policy.on_connection_closed()
    policy.prompt_ready = True

    assert policy.return_home is True
    assert policy.fastwalk_abort_reason == (
        "field route interrupted by connection loss; return home before retrying"
    )
    assert policy.pending_travel_origin is None
    assert policy.pending_fastwalk_hunt_move is False

    decision = policy.next_decision(
        CharacterState(
            hp=177,
            max_hp=177,
            mana=142,
            max_mana=142,
            move=220,
            max_move=220,
            position=7,
            room_name="Market Square",
            room_vnum="3014",
        )
    )

    assert decision is not None
    assert decision.command == "north"
    assert "healer" in decision.reason


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


def test_liquidation_leaves_healer_awake_before_planning_sales() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    healer = CharacterState(
        room_name="By the Temple Altar",
        room_vnum="3054",
        position=7,
        inventory=[[{"short_desc": "a length of metal piping", "quan": "1"}]],
    )

    decision = policy._liquidate_loot_decision(healer)

    assert decision is not None
    assert decision.command == "south"
    assert "awake" in decision.reason


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


def test_liquidation_sells_poison_ivy_to_source_compatible_grocer() -> None:
    poison_ivy = ObjectSource(
        302,
        "plant ivy",
        "a small dusk of poison ivy",
        19,
        (1, 0, 0, 1),
        1,
    )
    policy = StarterPolicy(
        _spec(race="drow"),
        "swordfish",
        liquidate_loot=True,
        gear_catalog=GearCatalog({poison_ivy.vnum: poison_ivy}),
    )
    policy.gear_audited = True
    home = CharacterState(
        room_name="Mage's Laboratory",
        room_vnum="3019",
        position=7,
        inventory=[[{
            "short_desc": poison_ivy.short_description,
            "quan": "24",
        }]],
    )

    decision = policy._liquidate_loot_decision(home)

    assert decision is not None
    assert decision.command == "west"
    assert policy.donation_plan == []
    assert [(keyword, shop.name) for keyword, shop in policy.sale_plan] == [
        ("ivy", "General Store"),
    ] * 24


def test_liquidation_routes_source_scroll_keyword_to_magic_shop() -> None:
    scroll = ObjectSource(
        312,
        "scroll jhyfrdow",
        "a scroll titled 'jhyfrdow'",
        2,
        (0, 0, 0, 0),
        0,
    )
    policy = StarterPolicy(
        _spec(race="drow"),
        "swordfish",
        liquidate_loot=True,
        gear_catalog=GearCatalog({scroll.vnum: scroll}),
    )
    policy.gear_audited = True
    home = CharacterState(
        room_name="Mage's Laboratory",
        room_vnum="3019",
        position=7,
        inventory=[[{
            "short_desc": "a scroll titled 'jhyfrdow'",
            "quan": "7",
        }]],
    )

    decision = policy._liquidate_loot_decision(home)

    assert decision is not None
    assert decision.command == "west"
    assert policy.donation_plan == []
    assert [(keyword, shop.name) for keyword, shop in policy.sale_plan] == [
        ("scroll", "Magic Shop"),
    ] * 7


def test_liquidation_preserves_positive_stat_gear_with_unreliable_source_level() -> None:
    stone = ObjectSource(
        3721,
        "snowy white stone",
        "a snowy white stone",
        8,
        (0, 0, 0, 0),
        90,
        wear_flags=1 | (1 << 15),
        level=2000,
        affects=((4, 2),),
    )
    robe = ObjectSource(
        6621,
        "robe linen",
        "a linen robe",
        9,
        (1, 0, 0, 0),
        13,
        wear_flags=1 | (1 << 10),
        level=2000,
        affects=((4, 1), (12, 5)),
    )
    penalty_ring = ObjectSource(
        4000,
        "yellow green ring",
        "a yellow and green ring",
        9,
        (1, 0, 0, 0),
        63,
        wear_flags=1 | (1 << 1),
        affects=((1, -2), (5, 1)),
    )
    policy = StarterPolicy(
        _spec(race="elf"),
        "swordfish",
        liquidate_loot=True,
        gear_catalog=GearCatalog(
            {
                stone.vnum: stone,
                robe.vnum: robe,
                penalty_ring.vnum: penalty_ring,
            }
        ),
    )
    policy.gear_audited = True
    home = CharacterState(
        room_name="Mage's Laboratory",
        room_vnum="3019",
        position=7,
        level=8,
        inventory=[[
            {"short_desc": "a snowy white stone"},
            {"short_desc": "a linen robe"},
            {"short_desc": "a yellow and green ring"},
        ]],
    )

    decision = policy._liquidate_loot_decision(home)

    assert decision is not None
    assert [(keyword, shop.name) for keyword, shop in policy.sale_plan] == [
        ("ring", "Leather Shop"),
    ]
    assert policy.donation_plan == []


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


def test_liquidation_heals_and_destroys_every_no_drop_sale_copy() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    shop = safe_shop_for_item("a strange amulet", item_type=9)
    assert shop is not None
    policy.sale_plan = [("amulet", shop)] * 3
    policy.sale_phase = "sell"

    policy.observe_text("You can't let go of it.\n")

    assert policy.cursed_sale_keyword == "amulet"
    assert policy.curse_recovery_step == "return"

    healer = CharacterState(
        room_name="By the Temple Altar",
        room_vnum="3054",
        position=7,
        inventory=[[{"short_desc": "a strange amulet", "quan": "3"}]],
    )
    heal = policy._liquidate_loot_decision(healer)
    assert heal is not None
    assert heal.command == "heal curse"

    policy.observe_text(
        "The Healer makes a magical pass over you.\n"
        "You toss a strange amulet away.\n"
        "You toss a strange amulet away.\n"
        "You toss a strange amulet away.\n"
    )
    destroys = [
        policy._liquidate_loot_decision(healer),
        policy._liquidate_loot_decision(healer),
        policy._liquidate_loot_decision(healer),
    ]
    assert [decision.command for decision in destroys if decision is not None] == [
        "sacrifice amulet",
        "sacrifice amulet",
        "sacrifice amulet",
    ]
    refresh = policy._liquidate_loot_decision(healer)
    assert refresh is not None
    assert refresh.command == "inventory"


def test_liquidation_drops_an_ordinary_cursed_sale_item_before_destroying_it() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    shop = safe_shop_for_item("a strange amulet", item_type=9)
    assert shop is not None
    policy.sale_plan = [("amulet", shop)]
    policy.sale_phase = "sell"
    policy.observe_text("You can't let go of it.\n")
    healer = CharacterState(
        room_name="By the Temple Altar",
        room_vnum="3054",
        position=7,
        inventory=[[{"short_desc": "a strange amulet", "quan": "1"}]],
    )
    policy._liquidate_loot_decision(healer)
    policy.observe_text(
        "The Healer makes a magical pass over you.\n"
        "You notice a strange amulet flash brightly.\n"
    )

    drop = policy._liquidate_loot_decision(healer)
    destroy = policy._liquidate_loot_decision(healer)

    assert drop is not None
    assert drop.command == "drop amulet"
    assert destroy is not None
    assert destroy.command == "sacrifice amulet"


def test_liquidation_stops_when_healer_remove_curse_is_unaffordable() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    shop = safe_shop_for_item("a strange amulet", item_type=9)
    assert shop is not None
    policy.sale_plan = [("amulet", shop)]
    policy.sale_phase = "sell"
    policy.observe_text("You can't let go of it.\n")
    healer = CharacterState(
        room_name="By the Temple Altar",
        room_vnum="3054",
        position=7,
        inventory=[[{"short_desc": "a strange amulet", "quan": "1"}]],
    )
    policy._liquidate_loot_decision(healer)
    policy.observe_text(
        "The Healer says 'You do not have enough money for my services.'\n"
    )

    decision = policy._liquidate_loot_decision(healer)

    assert decision is not None
    assert decision.command == "south"
    assert policy.curse_recovery_step == "borrow"


def test_liquidation_withdraws_existing_funds_and_retries_remove_curse() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    shop = safe_shop_for_item("a strange amulet", item_type=9)
    assert shop is not None
    policy.sale_plan = [("amulet", shop)]
    policy.sale_phase = "sell"
    policy.observe_text("You can't let go of it.\n")
    policy.curse_recovery_step = "borrow"

    rooms = (
        ("By the Temple Altar", "3054", "south"),
        ("The Temple Of Midgaard", "3001", "south"),
        ("The Fountain", "3005", "east"),
        ("Market Square", "3006", "east"),
        ("Dragonhoard Bank", "3007", "withdraw 5 gold"),
        ("Dragonhoard Bank", "3007", "west"),
        ("Market Square", "3006", "west"),
        ("The Fountain", "3005", "north"),
        ("The Temple Of Midgaard", "3001", "north"),
        ("By the Temple Altar", "3054", "heal curse"),
    )
    for index, (room_name, room_vnum, expected) in enumerate(rooms):
        if index == 5:
            policy.observe_text(
                "The teller says 'Thank you for your custom Kestrel.'\n"
            )
        decision = policy._liquidate_loot_decision(
            CharacterState(
                room_name=room_name,
                room_vnum=room_vnum,
                position=7,
            )
        )
        assert decision is not None
        assert decision.command == expected

    assert policy.curse_borrow_complete is True
    assert policy.curse_recovery_step == "heal"


def test_liquidation_borrows_when_bank_cannot_withdraw_remove_curse_fee() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    shop = safe_shop_for_item("a strange amulet", item_type=9)
    assert shop is not None
    policy.sale_plan = [("amulet", shop)]
    policy.sale_phase = "sell"
    policy.observe_text("You can't let go of it.\n")
    policy.curse_recovery_step = "borrow"
    bank = CharacterState(
        room_name="Dragonhoard Bank",
        room_vnum="3007",
        position=7,
    )

    withdraw = policy._liquidate_loot_decision(bank)
    assert withdraw is not None
    assert withdraw.command == "withdraw 5 gold"

    policy.observe_text(
        "The teller says 'Kestrel, you do not have 5 gold coins to withdraw.'\n"
    )
    borrow = policy._liquidate_loot_decision(bank)
    assert borrow is not None
    assert borrow.command == "borrow 500"

    policy.observe_text(
        "The teller says 'Kestrel, you now owe us: 3 coins,'\n"
        "The teller says 'after borrowing: 500 coins.'\n"
    )
    leave = policy._liquidate_loot_decision(bank)
    assert leave is not None
    assert leave.command == "west"
    assert policy.curse_borrow_complete is True


def test_liquidation_does_not_treat_rejected_borrow_as_funded() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    shop = safe_shop_for_item("a strange amulet", item_type=9)
    assert shop is not None
    policy.sale_plan = [("amulet", shop)]
    policy.sale_phase = "sell"
    policy.observe_text("You can't let go of it.\n")
    policy.curse_recovery_step = "borrow"
    policy.curse_borrow_step = 2
    bank = CharacterState(
        room_name="Dragonhoard Bank",
        room_vnum="3007",
        position=7,
    )
    policy.observe_text(
        "The teller says 'If you are only borrowing that much, withdraw "
        "the coins instead Kestrel.'\n"
    )

    decision = policy._liquidate_loot_decision(bank)

    assert decision is None
    assert policy.curse_borrow_complete is False
    assert policy.failure == (
        "the bank did not confirm the bounded remove-curse loan"
    )


def test_liquidation_stops_if_remove_curse_is_unaffordable_after_borrowing() -> None:
    policy = StarterPolicy(_spec(), "swordfish", liquidate_loot=True)
    shop = safe_shop_for_item("a strange amulet", item_type=9)
    assert shop is not None
    policy.sale_plan = [("amulet", shop)]
    policy.sale_phase = "sell"
    policy.observe_text("You can't let go of it.\n")
    policy.curse_recovery_step = "heal"
    policy.curse_borrow_complete = True
    policy.observe_text(
        "The Healer says 'You do not have enough money for my services.'\n"
    )
    healer = CharacterState(
        room_name="By the Temple Altar",
        room_vnum="3054",
        position=7,
    )

    decision = policy._liquidate_loot_decision(healer)

    assert decision is None
    assert policy.failure == (
        "the healer's remove-curse service remained unaffordable for amulet "
        "after one bounded bank loan"
    )


def test_liquidation_preserves_a_source_identified_potion() -> None:
    potion = ObjectSource(
        6646,
        "potion amber",
        "an amber potion",
        10,
        (30, 1, 2, 0),
        500,
        wear_flags=1,
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        liquidate_loot=True,
        gear_catalog=GearCatalog({potion.vnum: potion}),
    )
    policy.gear_audited = True
    policy.sale_identify_plan = []
    home = CharacterState(
        room_name="Mage's Laboratory",
        room_vnum="3019",
        position=7,
        inventory=[[{"short_desc": "an amber potion", "quan": "1"}]],
    )

    decision = policy._liquidate_loot_decision(home)

    assert decision is None
    assert policy.sale_plan == []
    assert policy.donation_plan == []


def test_emergency_provision_sale_selects_weakest_sellable_potion() -> None:
    pink = ObjectSource(
        5019,
        "potion pink",
        "a pink potion",
        10,
        (25, 1, 2, 0),
        600,
    )
    amber = ObjectSource(
        6646,
        "potion amber",
        "an amber potion",
        10,
        (30, 1, 2, 0),
        1500,
    )
    purple = ObjectSource(
        6647,
        "potion purple",
        "a purple potion",
        10,
        (40, 1, 2, 0),
        2000,
    )
    catalog = GearCatalog({item.vnum: item for item in (pink, amber, purple)})

    assert _emergency_provision_potion_keyword(
        ["a pink potion", "an amber potion", "a purple potion"],
        catalog,
    ) == "pink"


def test_emergency_provision_sale_plans_the_selected_potion_by_source_keyword() -> None:
    pink = ObjectSource(
        5019,
        "potion pink",
        "a pink potion",
        10,
        (25, 1, 2, 0),
        600,
    )
    amber = ObjectSource(
        6646,
        "potion amber",
        "an amber potion",
        10,
        (30, 1, 2, 0),
        1500,
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        liquidate_loot=True,
        emergency_provision_sale=True,
        gear_catalog=GearCatalog({pink.vnum: pink, amber.vnum: amber}),
    )
    policy.gear_audited = True
    policy.sale_identify_plan = []
    home = CharacterState(
        room_name="Mage's Laboratory",
        room_vnum="3019",
        position=7,
        inventory=[[{"short_desc": "a pink potion", "quan": "1"},
                    {"short_desc": "an amber potion", "quan": "1"}]],
    )

    decision = policy._liquidate_loot_decision(home)

    assert decision is not None
    assert decision.command == "west"
    assert [keyword for keyword, _ in policy.sale_plan] == ["pink"]


def test_emergency_provision_sale_recovery_skips_ordinary_resupply() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        liquidate_loot=True,
        emergency_provision_sale=True,
    )
    policy.in_world = True
    policy.login_authenticated = True
    policy.prompt_ready = True
    state = CharacterState(
        hp=4,
        max_hp=254,
        mana=242,
        max_mana=242,
        move=320,
        max_move=320,
        position=7,
        room_name="By the Temple Altar",
        room_vnum="3054",
        room_flags=["safe", "healing"],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "sleep"


def test_emergency_provision_sale_can_start_above_hard_health_floor() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        liquidate_loot=True,
        emergency_provision_sale=True,
    )
    state = CharacterState(
        hp=140,
        max_hp=254,
        mana=242,
        max_mana=242,
        move=320,
        max_move=320,
        position=4,
        room_name="By the Temple Altar",
        room_vnum="3054",
        room_flags=["safe", "healing"],
    )

    assert policy._recovery_decision(state) is None


def test_emergency_provision_sale_reenables_resupply_after_sale() -> None:
    pink = ObjectSource(
        5019,
        "potion pink",
        "a pink potion",
        10,
        (25, 1, 2, 0),
        600,
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        liquidate_loot=True,
        emergency_provision_sale=True,
        gear_catalog=GearCatalog({pink.vnum: pink}),
    )
    policy.sale_plan = [
        ("pink", safe_shop_for_item("a pink potion", item_type=10))
    ]
    policy.sale_index = 0
    policy.sale_phase = "inventory"

    policy.observe_text("You sell a pink potion for 22 coins.")

    assert policy.emergency_provision_sale is False
    assert policy.completed_sales[0]["item_keyword"] == "pink"


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
    assert audit.command == "eq all"
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


def test_liquidation_sells_inferior_carried_piercing_weapon_when_primary_is_worn() -> None:
    long_dagger = ObjectSource(
        115,
        "long slim dagger",
        "a long slim dagger",
        5,
        (0, 1, 5, 2),
        80,
        wear_flags=1 | (1 << 13),
        level=8,
    )
    plain_dagger = ObjectSource(
        116,
        "dagger",
        "a dagger",
        5,
        (0, 1, 3, 2),
        20,
        wear_flags=1 | (1 << 13),
        level=1,
        affects=((18, 4), (19, -2)),
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja", "race": "drow"}),
        "swordfish",
        liquidate_loot=True,
        gear_catalog=GearCatalog(
            {long_dagger.vnum: long_dagger, plain_dagger.vnum: plain_dagger}
        ),
    )
    policy.in_world = True
    policy.gear_audited = True
    policy.gear_worn = [long_dagger]
    policy.known_skills.add("backstab")
    home = CharacterState(
        level=17,
        room_name="Mage's Laboratory",
        room_vnum="3019",
        inventory=[[{"short_desc": "a dagger", "quan": "1"}]],
    )

    policy._liquidate_loot_decision(home)

    assert [(keyword, shop.name) for keyword, shop in policy.sale_plan] == [
        ("dagger", "Weapon Shop")
    ]


def test_liquidation_sells_positive_modifier_weapon_when_primary_is_better() -> None:
    primary = ObjectSource(
        117,
        "long slim dagger",
        "a long slim dagger",
        5,
        (0, 2, 5, 2),
        80,
        wear_flags=1 | (1 << 13),
        affects=((18, 1), (19, 1)),
    )
    inferior = ObjectSource(
        118,
        "long sword",
        "a long sword",
        5,
        (0, 1, 8, 3),
        100,
        wear_flags=1 | (1 << 13),
        affects=((18, 1), (19, 2)),
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja", "race": "drow"}),
        "swordfish",
        liquidate_loot=True,
        gear_catalog=GearCatalog(
            {primary.vnum: primary, inferior.vnum: inferior}
        ),
    )
    policy.in_world = True
    policy.gear_audited = True
    policy.gear_worn = [primary]
    home = CharacterState(
        level=17,
        room_name="Mage's Laboratory",
        room_vnum="3019",
        inventory=[[{"short_desc": "a long sword", "quan": "1"}]],
    )

    policy._liquidate_loot_decision(home)

    assert [(keyword, shop.name) for keyword, shop in policy.sale_plan] == [
        ("sword", "Weapon Shop")
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


def test_flight_funding_borrows_once_and_returns_to_healer() -> None:
    policy = StarterPolicy(_spec(), "swordfish", flight_borrowing=True)

    outbound = (
        ("3054", "south"),
        ("3001", "south"),
        ("3005", "east"),
        ("3006", "east"),
        ("3007", "borrow 300"),
    )
    for room_vnum, expected_command in outbound:
        decision = policy._flight_borrow_decision(
            CharacterState(room_vnum=room_vnum, position=7)
        )
        assert decision is not None
        assert decision.command == expected_command

    policy.observe_text(
        "The teller says 'after borrowing: 300 coins.'\n"
    )
    route = (
        ("3007", "west"),
        ("3006", "west"),
        ("3005", "south"),
        ("3014", "west"),
        ("3013", "west"),
        ("3012", "north"),
        ("3033", "south"),
        ("3012", "east"),
        ("3013", "east"),
        ("3014", "north"),
        ("3005", "north"),
        ("3001", "north"),
    )
    for room_vnum, expected_command in route:
        decision = policy._flight_borrow_decision(
            CharacterState(room_vnum=room_vnum, position=7)
        )
        assert decision is not None
        assert decision.command == expected_command

    assert (
        policy._flight_borrow_decision(
            CharacterState(room_vnum="3054", position=7)
        )
        is None
    )
    assert policy.flight_borrow_complete is True


def test_flight_funding_uses_existing_bank_balance_when_borrow_is_unnecessary() -> None:
    policy = StarterPolicy(_spec(), "swordfish", flight_borrowing=True)
    bank = CharacterState(room_vnum="3007", position=7)

    first = policy._flight_borrow_decision(bank)
    assert first is not None
    assert first.command == "borrow 300"

    policy.observe_text(
        "The teller says 'If you are only borrowing that much, withdraw the coins instead.'"
    )
    withdraw = policy._flight_borrow_decision(bank)
    assert withdraw is not None
    assert withdraw.command == "withdraw 3 gold"

    policy.observe_text("The teller says 'Thank you for your custom.'")
    leave = policy._flight_borrow_decision(bank)
    assert leave is not None
    assert leave.command == "west"


def test_flight_funding_stops_after_unconfirmed_bank_response() -> None:
    policy = StarterPolicy(_spec(), "swordfish", flight_borrowing=True)
    first = policy._flight_borrow_decision(
        CharacterState(room_vnum="3007", position=7)
    )

    assert first is not None
    assert first.command == "borrow 300"

    policy.observe_text("The teller says 'Your credit limit is 10 coins.'")
    assert (
        policy._flight_borrow_decision(
            CharacterState(room_vnum="3007", position=7)
        )
        is None
    )
    assert "do not retry" in (policy.failure or "")


def test_magic_shop_retries_flight_purchase_after_using_carried_food() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        magic_shop_research=True,
        magic_shop_buy_fly=True,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.magic_shop_step = 2
    policy.observe_text("You can't carry that much weight.")
    shop = CharacterState(
        room_name="The Magic Shop",
        room_vnum="3033",
        position=7,
        inventory=[[{"short_desc": "a big pot pie"}]],
    )

    relief = policy.next_decision(shop)

    assert relief is not None
    assert relief.command == "eat pie"

    policy.prompt_ready = True
    assert policy.next_decision(shop) is None
    assert policy.prompt_ready is False

    policy.observe_text("You eat a big pot pie.")
    policy.prompt_ready = True
    retry = policy.next_decision(shop)

    assert retry is not None
    assert retry.command == "buy light"
    assert policy.magic_shop_purchase_failed is False


def test_magic_shop_temporarily_drops_and_recovers_worn_diploma_for_capacity() -> None:
    diploma = ObjectSource(
        3715,
        "diploma",
        "a Mud School diploma",
        8,
        (0, 0, 0, 0),
        1,
        wear_flags=1 | (1 << 14),
    )
    tophat = ObjectSource(
        4421,
        "tophat hat",
        "a tophat",
        9,
        (0, 0, 0, 0),
        1,
        wear_flags=1 | (1 << 4),
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        gear_catalog=GearCatalog(
            {diploma.vnum: diploma, tophat.vnum: tophat}
        ),
        magic_shop_research=True,
        magic_shop_buy_fly=True,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.magic_shop_step = 2
    policy.gear_worn = [diploma, tophat]
    policy.gear_audited = True
    policy.observe_text("You can't carry that much weight.")
    shop = CharacterState(
        room_name="The Magic Shop",
        room_vnum="3033",
        position=7,
        inventory="[]",
    )

    commands = []
    for _ in range(5):
        decision = policy.next_decision(shop)
        assert decision is not None
        commands.append(decision.command)
        policy.after_command(decision)
        policy.prompt_ready = True

    assert commands == [
        "remove diploma",
        "drop diploma",
        "remove tophat",
        "drop tophat",
        "buy light",
    ]

    shop.inventory = '[[{"quan": "1", "short_desc": "a light blue potion"}]]'
    for _ in range(3):
        decision = policy.next_decision(shop)
        assert decision is not None
        commands.append(decision.command)
        policy.after_command(decision)
        policy.prompt_ready = True

    shop.inventory = "[]"
    for _ in range(4):
        decision = policy.next_decision(shop)
        assert decision is not None
        commands.append(decision.command)
        policy.after_command(decision)
        policy.prompt_ready = True

    assert commands == [
        "remove diploma",
        "drop diploma",
        "remove tophat",
        "drop tophat",
        "buy light",
        "inventory",
        "quaff light",
        "affects",
        "get diploma",
        "hold diploma",
        "get tophat",
        "wear tophat",
    ]
    leave_shop = policy.next_decision(shop)
    assert leave_shop is not None
    assert leave_shop.command == "south"


def test_magic_shop_recovers_dropped_diploma_after_retry_failure() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        magic_shop_research=True,
        magic_shop_buy_fly=True,
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.magic_shop_step = 2
    policy.magic_shop_capacity_relief_attempted = True
    policy.magic_shop_diploma_relief_step = 5
    policy.magic_shop_diploma_dropped = True
    policy.observe_text("You can't carry that much weight.")
    shop = CharacterState(
        room_name="The Magic Shop",
        room_vnum="3033",
        position=7,
    )

    recover = policy.next_decision(shop)

    assert recover is not None
    assert recover.command == "get diploma"
    assert policy.magic_shop_purchase_failed is True


def test_excess_coin_banking_keeps_one_gold_working_reserve() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        bank_excess_coins=True,
    )
    route = (
        ("3054", "south"),
        ("3001", "south"),
        ("3014", "north"),
        ("3005", "east"),
        ("3006", "east"),
        ("3007", "deposit all"),
        ("3007", "withdraw 1 gold"),
        ("3007", "west"),
        ("3006", "west"),
        ("3005", "north"),
        ("3001", "north"),
    )

    for room_vnum, expected in route:
        decision = policy._bank_excess_coin_decision(
            CharacterState(room_vnum=room_vnum, position=7)
        )
        assert decision is not None
        assert decision.command == expected

    assert (
        policy._bank_excess_coin_decision(
            CharacterState(room_vnum="3054", position=7)
        )
        is None
    )


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


def test_healer_movement_recovery_wakes_to_drink_before_waiting_for_move() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=10)
    policy.in_world = True
    policy.prompt_ready = True
    policy.waiting_for_move = True
    policy.needs_drink = True
    state = CharacterState(
        hp=79,
        max_hp=79,
        move=110,
        max_move=270,
        position=4,
        room_name="The Altar of the Temple",
        room_vnum="3054",
        room_flags=["safe", "healing"],
        inventory=[[{"short_desc": "a buffalo water skin"}]],
    )

    wake = policy.next_decision(state)

    assert wake is not None
    assert wake.command == "stand"
    policy.after_command(wake)

    state.position = 7
    policy.prompt_ready = True
    drink = policy.next_decision(state)

    assert drink is not None
    assert drink.command == "drink skin"
    policy.after_command(drink)

    policy.prompt_ready = True
    resume = policy.next_decision(state)

    assert resume is not None
    assert resume.command == "sleep"


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
        ("The Mud School Arena", "3734", "up"),
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


def test_arena_recovery_wakes_before_leaving_for_the_temple_healer() -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=10)
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        level=6,
        hp=87,
        max_hp=138,
        mana=70,
        max_mana=127,
        move=200,
        max_move=200,
        position=4,
        room_name="The Mud School Arena",
        room_vnum="3734",
        room_flags=["safe"],
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "stand"
    policy.after_command(decision)
    state.position = 7
    policy.prompt_ready = True

    leave = policy.next_decision(state)

    assert leave is not None
    assert leave.command == "up"
    assert "temple healer" in leave.reason


def test_arena_recovery_does_not_route_through_an_active_enemy(tmp_path) -> None:
    policy = StarterPolicy(_spec(), "swordfish", objective_level=6)
    state = CharacterState(
        level=3,
        hp=68,
        max_hp=69,
        mana=75,
        max_mana=191,
        move=155,
        max_move=170,
        room_name="The Mud School Arena",
        room_vnum="3734",
        room_flags=["safe"],
        enemies=[[{"name": "a wolf", "level": "3", "hp": "4", "maxhp": "30"}]],
    )

    assert policy._recovery_decision(state) is None


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


def test_cleric_uses_bounded_self_healing_before_withdrawal() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "cleric", "subclass": "templar"}),
        "swordfish",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.active_target = "a wild boar"
    policy.known_skills.update(("cause serious", "cure light", "cure serious"))
    state = CharacterState(
        level=10,
        hp=35,
        max_hp=100,
        mana=100,
        max_mana=150,
        position=6,
        room_name="The Mud School Arena",
        room_vnum="3730",
    )

    first = policy.next_decision(state)

    assert first is not None
    assert first.command == "cast 'cure serious'"
    assert "1 of 2" in first.reason
    policy.observe_text("You feel better!\n")
    policy.prompt_ready = True
    second = policy.next_decision(state)

    assert second is not None
    assert second.command == "cast 'cure serious'"
    assert "2 of 2" in second.reason
    policy.observe_text("You feel better!\n")
    policy.prompt_ready = True
    state.hp = 20
    withdrawal = policy.next_decision(state)

    assert withdrawal is not None
    assert withdrawal.command == "flee"


def test_cleric_preserves_mana_reserve_instead_of_self_healing() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "cleric", "subclass": "templar"}),
        "swordfish",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.active_target = "a wild boar"
    policy.known_skills.update(("cause serious", "cure serious"))
    state = CharacterState(
        level=10,
        hp=20,
        max_hp=100,
        mana=55,
        max_mana=150,
        position=6,
        room_name="The Mud School Arena",
        room_vnum="3730",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "flee"
    assert policy.cleric_combat_heals == 0


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


def test_brawler_uses_punch_while_automatic_unarmed_rounds_continue() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "brawler", "subclass": "monk"}),
        "swordfish",
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.active_target = "a wild boar"
    policy.known_skills.add("punch")
    state = CharacterState(
        level=10,
        hp=120,
        max_hp=130,
        position=6,
        room_name="The Mud School Arena",
        room_vnum="3730",
    )

    decision = policy.next_decision(state)

    assert decision is not None
    assert decision.command == "punch"
    assert "automatic unarmed combat rounds continue" in decision.reason
    policy.observe_text("Your punch wounds a wild boar.\n")
    assert policy.between_round_action_issued is False


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


def test_ranger_opens_with_shoot_only_when_a_source_bow_is_equipped() -> None:
    bow = ObjectSource(
        18001,
        "bow",
        "a short bow",
        5,
        (0, 2, 4, 4),
        20,
        wear_flags=1 | (1 << 17),
        extra_flags=1 << 30,
    )
    policy = StarterPolicy(
        _spec(**{"class": "ranger", "subclass": None}),
        "swordfish",
    )
    policy.known_skills.add("shoot")
    policy.gear_worn = [bow]

    decision = policy._combat_opener_decision(
        "a wild boar",
        "fight arena opponent a wild boar",
    )

    assert decision.command == "shoot boar"
    assert policy.shoot_pending_target == "a wild boar"
    policy.gear_worn = []
    fallback = policy._combat_opener_decision(
        "another boar",
        "fight arena opponent another boar",
    )
    assert fallback.command == "kill boar"


def test_rejected_shoot_falls_back_to_normal_attack_once() -> None:
    bow = ObjectSource(
        18001,
        "bow",
        "a short bow",
        5,
        (0, 2, 4, 4),
        20,
        wear_flags=1 | (1 << 17),
        extra_flags=1 << 30,
    )
    policy = StarterPolicy(
        _spec(**{"class": "ranger", "subclass": None}),
        "swordfish",
    )
    policy.known_skills.add("shoot")
    policy.gear_worn = [bow]
    first = policy._combat_opener_decision(
        "a wild boar",
        "fight arena opponent a wild boar",
    )
    assert first.command == "shoot boar"

    policy.observe_text("You must have a bow equipped to shoot.\n")
    fallback = policy._combat_opener_decision(
        "a wild boar",
        "fight arena opponent a wild boar",
    )

    assert fallback.command == "kill boar"
    assert policy.shoot_pending_target is None


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


def test_thief_backstab_opener_uses_exact_targetmode_selector() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
    )
    policy.known_skills.add("backstab")
    policy.active_target_selector = "#22332"
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
        "the patrolling guard",
        "fight the patrolling guard",
    )

    assert decision.command == "backstab #22332"


def test_bounty_hunter_stuns_with_pounding_weapon_then_switches_to_piercing_backstab() -> None:
    sword = ObjectSource(
        4002,
        "rusty sword",
        "a rusty sword",
        5,
        (0, 4, 8, 3),
        100,
        wear_flags=1 | (1 << 13),
    )
    mace = ObjectSource(
        4003,
        "mace",
        "a mace",
        5,
        (0, 2, 5, 7),
        100,
        wear_flags=1 | (1 << 13),
    )
    dagger = ObjectSource(
        5252,
        "long dagger slim",
        "a long slim dagger",
        5,
        (0, 2, 5, 11),
        100,
        wear_flags=1 | (1 << 13),
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "bounty hunter"}),
        "swordfish",
        gear_catalog=GearCatalog(
            {item.vnum: item for item in (sword, mace, dagger)}
        ),
    )
    policy.known_skills.update(("backstab", "stun"))
    policy.gear_worn = [sword]
    policy.active_target_selector = "#22332"
    state = CharacterState(
        inventory=[
            [
                {"short_desc": "a mace"},
                {"short_desc": "a long slim dagger"},
            ]
        ],
        position=7,
    )

    first = policy._combat_opener_decision(
        "the patrolling guard",
        "fight the patrolling guard",
        state=state,
    )
    assert first.command == "wield mace"
    policy.observe_text("You wield a mace.\n")

    stun = policy._stun_opener_decision()
    assert stun is not None
    assert stun.command == "stun #22332"
    policy.observe_text(
        "You viciously pound the patrolling guard, causing it to buckle and collapse.\n"
    )

    switch = policy._stun_opener_decision()
    assert switch is not None
    assert switch.command == "wield dagger"
    policy.observe_text("You wield a long slim dagger.\n")

    backstab = policy._stun_opener_decision()
    assert backstab is not None
    assert backstab.command == "backstab #22332"
    assert policy.combat_active is True


def test_stun_miss_still_switches_to_piercing_backstab() -> None:
    mace = ObjectSource(
        4003,
        "mace",
        "a mace",
        5,
        (0, 2, 5, 7),
        100,
        wear_flags=1 | (1 << 13),
    )
    dagger = ObjectSource(
        5252,
        "long dagger slim",
        "a long slim dagger",
        5,
        (0, 2, 5, 11),
        100,
        wear_flags=1 | (1 << 13),
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "bounty hunter"}),
        "swordfish",
        gear_catalog=GearCatalog(
            {item.vnum: item for item in (mace, dagger)}
        ),
    )
    policy.known_skills.update(("backstab", "stun"))
    policy.gear_worn = [mace]
    policy.active_target_selector = "#22332"
    state = CharacterState(
        inventory=[[{"short_desc": "a long slim dagger"}]],
        position=7,
    )

    first = policy._combat_opener_decision(
        "the patrolling guard",
        "fight the patrolling guard",
        state=state,
    )
    assert first.command == "stun #22332"
    policy.observe_text("Your attempted stun misses the patrolling guard.\n")

    switch = policy._stun_opener_decision()
    assert switch is not None
    assert switch.command == "wield dagger"
    policy.observe_text("You wield a long slim dagger.\n")

    backstab = policy._stun_opener_decision()
    assert backstab is not None
    assert backstab.command == "backstab #22332"


def test_thief_rearm_keeps_stronger_carried_piercing_weapon() -> None:
    club = ObjectSource(
        4002,
        "club",
        "a club",
        5,
        (0, 2, 4, 7),
        100,
        wear_flags=1 | (1 << 13),
    )
    basic_dagger = ObjectSource(
        3001,
        "dagger",
        "a dagger",
        5,
        (0, 1, 4, 11),
        94,
        wear_flags=1 | (1 << 13),
    )
    long_dagger = ObjectSource(
        5252,
        "long dagger slim",
        "a long slim dagger",
        5,
        (0, 2, 5, 11),
        100,
        wear_flags=1 | (1 << 13),
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        city_rearm=True,
        gear_catalog=GearCatalog(
            {item.vnum: item for item in (club, basic_dagger, long_dagger)}
        ),
    )
    policy.gear_worn = [club]
    policy.primary_weapon_observed = True
    state = CharacterState(
        room_vnum="3054",
        inventory=[
            [
                {"short_desc": "a dagger"},
                {"short_desc": "a long slim dagger"},
            ]
        ],
        stats={"carry_wt": 100, "maxcarry_wt": 250},
    )

    first = policy._city_rearm_decision(state)

    assert first is not None
    assert first.command == "wield long"
    policy.observe_text(
        "You stop using a club.\nYou wield a long slim dagger.\n"
    )

    assert policy._wielded_weapon() == long_dagger
    assert policy._city_rearm_decision(state) is None
    assert policy.city_rearm_returning is True


def test_thief_alternates_disarm_and_repeatable_circle_with_exact_selector(
    monkeypatch,
) -> None:
    clock = {"now": 100.0}
    monkeypatch.setattr(
        "dd4tester.starter.time.monotonic",
        lambda: clock["now"],
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
    )
    policy.active_target = "the patrolling guard"
    policy.active_target_selector = "#22332"
    policy.known_skills.update(("circle", "disarm"))
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
    state = CharacterState(hp=120, max_hp=140, position=6)

    first = policy._between_round_combat_decision(state)
    policy.observe_text(
        "Your disarm attempt failed.\n"
        "<120/140 hits 100/100 mana 100/100 move [Fleshmonger's Tower]>\n"
    )
    clock["now"] = 103.1
    second = policy._between_round_combat_decision(state)
    policy.observe_text(
        "You attempt to circle around your opponent.\n"
        "<120/140 hits 100/100 mana 100/100 move [Fleshmonger's Tower]>\n"
    )
    clock["now"] = 106.2
    third = policy._between_round_combat_decision(state)
    policy.observe_text(
        "You disarm the patrolling guard!\n"
        "<120/140 hits 100/100 mana 100/100 move [Fleshmonger's Tower]>\n"
    )
    clock["now"] = 109.3
    fourth = policy._between_round_combat_decision(state)
    policy.observe_text(
        "You attempt to circle around your opponent.\n"
        "<120/140 hits 100/100 mana 100/100 move [Fleshmonger's Tower]>\n"
    )
    clock["now"] = 112.4
    fifth = policy._between_round_combat_decision(state)

    assert first is not None
    assert first.command == "disarm #22332"
    assert second is not None
    assert second.command == "circle #22332"
    assert third is not None
    assert third.command == "disarm #22332"
    assert fourth is not None
    assert fourth.command == "circle #22332"
    assert fifth is not None
    assert fifth.command == "circle #22332"


def test_thief_repeats_knife_toss_with_exact_selector(monkeypatch) -> None:
    clock = {"now": 100.0}
    monkeypatch.setattr(
        "dd4tester.starter.time.monotonic",
        lambda: clock["now"],
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
    )
    policy.active_target = "the patrolling guard"
    policy.active_target_selector = "#22332"
    policy.known_skills.add("knife toss")
    state = CharacterState(hp=120, max_hp=140, position=6)

    first = policy._between_round_combat_decision(state)
    policy.observe_text(
        "Your knife toss scratches the patrolling guard.\n"
    )
    clock["now"] = 103.1
    second = policy._between_round_combat_decision(state)

    assert first is not None
    assert first.command == "knife #22332"
    assert "without consuming carried ammunition" in first.reason
    assert second is not None
    assert second.command == "knife #22332"


def test_disarm_retries_when_no_other_active_attack_is_known(monkeypatch) -> None:
    clock = {"now": 100.0}
    monkeypatch.setattr(
        "dd4tester.starter.time.monotonic",
        lambda: clock["now"],
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
    )
    policy.active_target = "an armed sentry"
    policy.known_skills.add("disarm")
    policy.primary_weapon_observed = True
    state = CharacterState(hp=100, max_hp=100, position=6)

    first = policy._between_round_combat_decision(state)
    policy.observe_text(
        "Your disarm attempt failed.\n"
        "<100/100 hits 100/100 mana 100/100 move [Midgaard]>\n"
    )
    clock["now"] = 103.1
    second = policy._between_round_combat_decision(state)

    assert first is not None
    assert first.command == "disarm sentry"
    assert second is not None
    assert second.command == "disarm sentry"


def test_disarm_stops_after_opponent_is_confirmed_unarmed(monkeypatch) -> None:
    clock = {"now": 100.0}
    monkeypatch.setattr(
        "dd4tester.starter.time.monotonic",
        lambda: clock["now"],
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
    )
    policy.active_target = "an unarmed sentry"
    policy.known_skills.add("disarm")
    policy.primary_weapon_observed = True
    state = CharacterState(hp=100, max_hp=100, position=6)

    first = policy._between_round_combat_decision(state)
    policy.observe_text(
        "Your opponent is not wielding a weapon.\n"
        "<100/100 hits 100/100 mana 100/100 move [Midgaard]>\n"
    )
    clock["now"] = 103.1
    second = policy._between_round_combat_decision(state)

    assert first is not None
    assert second is None


def test_disarm_resets_for_same_named_opponent_with_new_selector(
    monkeypatch,
) -> None:
    clock = {"now": 100.0}
    monkeypatch.setattr(
        "dd4tester.starter.time.monotonic",
        lambda: clock["now"],
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
    )
    policy.active_target = "a patrolling guard"
    policy.active_target_selector = "#22332"
    policy.known_skills.add("disarm")
    policy.primary_weapon_observed = True
    state = CharacterState(hp=100, max_hp=100, position=6)

    first = policy._between_round_combat_decision(state)
    policy.observe_text(
        "You disarm the patrolling guard!\n"
        "<100/100 hits 100/100 mana 100/100 move [Fleshmonger's Tower]>\n"
    )
    policy.active_target_selector = "#22347"
    clock["now"] = 103.1
    second = policy._between_round_combat_decision(state)

    assert first is not None
    assert first.command == "disarm #22332"
    assert second is not None
    assert second.command == "disarm #22347"


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


def test_field_hunt_rejected_backstab_reengages_before_room_reassessment() -> None:
    target = "rather large rock toad"
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("mahn tor rock toads"),
        fastwalk_hunt_stops=mahntor_rock_toad_circuit_hunt_stops(),
    )
    policy.fastwalk_attack_started = True
    policy.active_target = target
    policy.active_target_selector = "#25443"
    policy.backstab_skip_once_target = target
    policy.room_targets["2311"] = [target, "the Rock Toad is hurt and suspicious"]
    policy.room_target_counts["2311"] = {
        target: 1,
        "the Rock Toad is hurt and suspicious": 1,
    }
    state = CharacterState(
        level=16,
        hp=233,
        max_hp=233,
        mana=228,
        max_mana=228,
        move=111,
        max_move=300,
        position=7,
        room_name="The sparse foothills",
        room_vnum="2311",
    )

    decision = policy._fastwalk_hunt_plan_decision(state)

    assert decision is not None
    assert decision.command == "kill #25443"
    assert policy.combat_active is True
    assert policy.backstab_skip_once_target is None


def test_field_hunt_current_form_rejection_returns_without_opener_retry() -> None:
    target = "the dwarven servant"
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        fastwalk_route=route_named("dwarven servant"),
        fastwalk_hunt_stops=(FieldHuntStop((), target, exact_target=True),),
    )
    policy.fastwalk_attack_started = True
    policy.fastwalk_attack_target = target
    policy.active_target = target
    policy.active_target_selector = "#10740"
    policy.backstab_pending_target = target
    policy.combat_active = True

    policy.observe_text("You can't attack them in their current form.\n")

    assert policy.backstab_pending_target is None
    assert policy.stun_opener_step is None
    assert policy.combat_active is False
    assert policy.fastwalk_returning is True
    assert policy.fastwalk_hunt_stop_skipped is True
    assert policy.fastwalk_unattackable_target == target
    assert policy.fastwalk_abort_reason == (
        "field target 'the dwarven servant' was non-corporeal and could not be attacked"
    )
    assert policy.backstab_skip_once_target is None

    policy.fastwalk_arrival_observed = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(policy.fastwalk_route.commands)
    decision = policy._fastwalk_research_decision(
        CharacterState(
            level=17,
            hp=200,
            max_hp=200,
            mana=200,
            max_mana=200,
            move=200,
            max_move=200,
            position=7,
            room_vnum="20508",
        )
    )

    assert decision is not None
    assert decision.command == "recall"
    assert policy.fastwalk_returning is True


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


def test_enemy_snapshot_clears_successful_shoot_pending_marker() -> None:
    policy = StarterPolicy(
        _spec(**{"class": "ranger", "subclass": None}),
        "swordfish",
    )
    policy.shoot_pending_target = "a wolf"
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

    assert policy.shoot_pending_target is None
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
    policy.observe_text("You get a dagger.")
    policy.prompt_ready = True
    rearm = policy.next_decision(state)

    assert recover is not None
    assert recover.command == "get dagger"
    assert rearm is not None
    assert rearm.command == "wield dagger"


def test_combat_disarm_does_not_rearm_after_get_autowields_weapon() -> None:
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
    assert recover is not None
    assert recover.command == "get dagger"

    policy.observe_events([GameEvent("prompt_seen", "text", {})], state)
    stale_prompt_action = policy.next_decision(state)

    assert stale_prompt_action is None
    assert policy.disarm_recovery_step == 2

    policy.observe_text("You get a dagger.\nYou wield a dagger.")
    policy.prompt_ready = True

    next_action = policy.next_decision(state)
    assert next_action is None or next_action.command != "wield dagger"
    assert policy.primary_weapon_lost is False


def test_combat_disarm_reliefs_capacity_before_retrying_weapon_recovery() -> None:
    dagger = ObjectSource(
        3020,
        "dagger",
        "a dagger",
        5,
        (0, 2, 4, 11),
        10,
        wear_flags=1 | (1 << 13),
    )
    shield = ObjectSource(
        4536,
        "shield hard leather",
        "hard leather shield",
        9,
        (0, 0, 0, 0),
        35,
        wear_flags=1 | (1 << 9),
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": None}),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        gear_catalog=GearCatalog({dagger.vnum: dagger, shield.vnum: shield}),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.fastwalk_attack_started = True
    policy.active_target = "the war dog"
    policy.gear_worn = [dagger]
    state = CharacterState(
        level=18,
        hp=110,
        max_hp=254,
        position=6,
        room_name="In a forest clearing",
        room_vnum="4505",
        inventory=[[{"short_desc": "hard leather shield", "quan": "1"}]],
        stats={"carry_wt": 207, "maxcarry_wt": 200},
    )

    policy.observe_text("The war dog DISARMS you!")
    recover = policy.next_decision(state)
    assert recover is not None and recover.command == "get dagger"

    policy.observe_text("Long: you can't carry that much weight.")
    policy.prompt_ready = True
    relief = policy.next_decision(state)
    assert relief is not None
    assert relief.command == "sacrifice shield"
    policy.after_command(relief)

    policy.observe_text("You sacrifice a hard leather shield.")
    policy.prompt_ready = True
    retry = policy.next_decision(state)
    assert retry is not None and retry.command == "get dagger"

    policy.observe_text("You get a dagger.")
    policy.prompt_ready = True
    rearm = policy.next_decision(state)
    assert rearm is not None and rearm.command == "wield dagger"


def test_combat_disarm_clears_after_missing_weapon_get() -> None:
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
        _spec(**{"class": "thief", "subclass": None}),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        gear_catalog=GearCatalog({dagger.vnum: dagger}),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.fastwalk_attack_started = True
    policy.active_target = "the war dog"
    policy.gear_worn = [dagger]
    state = CharacterState(
        level=9,
        hp=120,
        max_hp=126,
        position=6,
        room_name="In a forest clearing",
        room_vnum="4505",
    )

    policy.observe_text("The war dog DISARMS you!")
    assert policy.next_decision(state).command == "get dagger"
    policy.observe_text("You do not see that here.")
    policy.prompt_ready = True

    decision = policy.next_decision(state)
    assert decision is None or decision.command != "get dagger"
    assert policy.disarm_recovery_step == 0


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
    policy.observe_text("You get a dagger.")
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

    quote = policy.next_decision(shop)
    policy.prompt_ready = True
    buy = policy.next_decision(shop)
    policy.prompt_ready = True
    wield = policy.next_decision(shop)
    policy.prompt_ready = True
    audit = policy.next_decision(shop)
    policy.observe_text("[weapon] a dagger")
    policy.prompt_ready = True
    return_move = policy.next_decision(shop)

    assert quote is not None
    assert quote.command == "list dagger"
    assert buy is not None
    assert buy.command == "buy dagger"
    assert wield is not None
    assert wield.command == "wield dagger"
    assert audit is not None
    assert audit.command == "eq all"
    assert return_move is not None
    assert return_move.command == "south"


def test_city_rearm_resumes_from_weapon_shop_with_any_wielded_weapon() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_rearm=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.observe_text("[weapon] a length of metal piping\n")
    shop = CharacterState(
        room_name="The Weapon Shop",
        room_vnum="3011",
        position=7,
    )

    decision = policy.next_decision(shop)

    assert decision is not None
    assert decision.command == "south"
    assert policy.primary_weapon_observed is True


def test_thief_city_rearm_prefers_carried_piercing_weapon_over_other_wielded_weapon() -> None:
    sword = ObjectSource(
        4002,
        "rusty sword",
        "a rusty sword",
        5,
        (0, 4, 8, 3),
        100,
        wear_flags=1 | (1 << 13),
    )
    dagger = ObjectSource(
        5252,
        "long dagger slim",
        "a long slim dagger",
        5,
        (0, 2, 5, 11),
        100,
        wear_flags=1 | (1 << 13),
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        city_rearm=True,
        gear_catalog=GearCatalog({sword.vnum: sword, dagger.vnum: dagger}),
    )
    policy.gear_worn = [sword]
    healer = CharacterState(
        room_name="By the Temple Altar",
        room_vnum="3054",
        position=7,
        inventory=[[{"short_desc": "a long slim dagger", "quan": "1"}]],
        stats={"carry_wt": 90, "maxcarry_wt": 100},
    )

    direct_wield = policy._city_rearm_decision(healer)

    assert direct_wield is not None
    assert direct_wield.command == "wield dagger"
    policy.gear_worn = [dagger]
    assert policy._city_rearm_decision(healer) is None


def test_empty_weapon_slot_overrides_stale_persisted_rearm_state() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_rearm=True)
    policy.in_world = True
    policy.prompt_ready = True
    policy.city_rearm_route_index = 6
    policy.primary_weapon_observed = True
    policy.primary_weapon_lost = False

    policy.observe_text("[weapon]            -\n")
    decision = policy.next_decision(
        CharacterState(
            room_name="The Weapon Shop",
            room_vnum="3011",
            position=7,
        )
    )

    assert policy.primary_weapon_observed is False
    assert policy.primary_weapon_lost is True
    assert decision is not None
    assert decision.command == "list dagger"


def test_city_rearm_borrows_for_an_unaffordable_primary_weapon() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_rearm=True)
    policy.city_rearm_route_index = 6
    policy.city_rearm_capacity_checked = True
    shop = CharacterState(
        room_name="The Weapon Shop",
        room_vnum="3011",
        position=7,
    )

    assert policy._city_rearm_decision(shop).command == "list dagger"
    assert policy._city_rearm_decision(shop).command == "buy dagger"
    policy.observe_text("The weaponsmith tells you 'You can't afford to buy a dagger'.")

    expected = (
        ("3011", "south"),
        ("3016", "west"),
        ("3015", "west"),
        ("3014", "north"),
        ("3005", "east"),
        ("3006", "east"),
        ("3007", "withdraw 5 gold"),
    )
    for room_vnum, command in expected:
        decision = policy._city_rearm_decision(
            CharacterState(
                room_name="Midgaard",
                room_vnum=room_vnum,
                position=7,
            )
        )
        assert decision is not None
        assert decision.command == command

    policy.observe_text("Kestrel, you do not have 5 gold coins to withdraw.")
    loan = policy._city_rearm_decision(
        CharacterState(room_name="Dragonhoard Bank", room_vnum="3007", position=7)
    )
    assert loan is not None
    assert loan.command == "borrow 500"

    policy.observe_text("The teller says 'after borrowing: 500 coins.'")
    leave = policy._city_rearm_decision(
        CharacterState(room_name="Dragonhoard Bank", room_vnum="3007", position=7)
    )
    assert leave is not None
    assert leave.command == "west"

    expected_return = (
        ("3006", "west"),
        ("3005", "south"),
        ("3014", "east"),
        ("3015", "east"),
        ("3016", "north"),
        ("3011", "buy dagger"),
    )
    for room_vnum, command in expected_return:
        decision = policy._city_rearm_decision(
            CharacterState(
                room_name="Midgaard",
                room_vnum=room_vnum,
                position=7,
            )
        )
        assert decision is not None
        assert decision.command == command


def test_city_rearm_stops_after_an_unconfirmed_bank_loan() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_rearm=True)
    policy.city_rearm_borrowing = True
    policy.city_rearm_borrow_step = 2
    policy.city_rearm_borrow_withdraw_issued = True
    policy.observe_text("The teller says 'Your credit limit is 10 coins.'")

    decision = policy._city_rearm_decision(
        CharacterState(room_name="Dragonhoard Bank", room_vnum="3007", position=7)
    )

    assert decision is None
    assert policy.failure == (
        "Dragonhoard Bank did not confirm the bounded primary-weapon loan; "
        "do not retry it automatically"
    )


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

    quote = policy._city_rearm_decision(shop)
    buy = policy._city_rearm_decision(shop)
    policy.observe_text("You can't carry that much weight.")
    after_rejection = policy._city_rearm_decision(shop)

    assert quote is not None
    assert quote.command == "list dagger"
    assert buy is not None
    assert buy.command == "buy dagger"
    assert after_rejection is None
    assert policy.failure == "insufficient carry capacity for the source-backed dagger"


def test_equipment_empty_categories_uses_only_visible_empty_slots() -> None:
    categories = _equipment_empty_categories(
        "<worn on head>      -\n"
        "<worn on arms>      studded leather sleeves\n"
        "<worn around neck>  -\n"
        "<secured to belt>   -\n"
        "[weapon]            -\n"
    )

    assert categories == {"head", "neck", "pouch", "wield"}


def test_city_outfit_plans_only_empty_source_stock_slots() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_outfit=True)
    healer = CharacterState(
        room_name="By the Temple Altar",
        room_vnum="3054",
        position=7,
    )

    assert policy._city_outfit_decision(healer).command == "eq all"
    policy.observe_text(
        "<worn on head>      -\n"
        "<worn around neck>  -\n"
        "<worn on arms>      -\n"
        "<worn on body>      -\n"
        "<worn on legs>      studded leather leggings\n"
        "<worn on feet>      blue snakeskin boots\n"
        "<secured to belt>   -\n"
        "[weapon]            a spiked metal rod\n"
    )

    departure = policy._city_outfit_decision(healer)

    assert departure is not None
    assert departure.command == "south"
    assert policy.city_outfit_plan == [
        ("pouch", "pouch"),
        ("head", "cap"),
        ("arms", "sleeves"),
        ("body", "jerkin"),
    ]


def test_city_outfit_donates_one_excess_pie_to_fit_arm_armour() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_outfit=True)
    policy.city_outfit_audited = True
    policy.city_outfit_plan = [("arms", "sleeves")]
    policy.city_outfit_initial_empty = {"arms"}
    healer = CharacterState(
        level=8,
        room_name="By the Temple Altar",
        room_vnum="3054",
        position=7,
        inventory=[[{"short_desc": "a big pot pie", "quan": "4"}]],
        stats={"carry_wt": 113, "maxcarry_wt": 115},
    )

    decision = policy._city_outfit_decision(healer)

    assert decision is not None
    assert decision.command == "donate pie"

    relieved = CharacterState(
        level=8,
        room_name="By the Temple Altar",
        room_vnum="3054",
        position=7,
        inventory=[[{"short_desc": "a big pot pie", "quan": "3"}]],
        stats={"carry_wt": 108, "maxcarry_wt": 115},
    )

    departure = policy._city_outfit_decision(relieved)

    assert departure is not None
    assert departure.command == "south"


def test_city_outfit_buys_verifies_and_returns_from_leather_shop() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_outfit=True)
    policy.city_outfit_audited = True
    policy.city_outfit_route_index = 7
    policy.city_outfit_plan = [("head", "cap")]
    shop = CharacterState(
        room_name="The Leather Shop",
        room_vnum="3035",
        position=7,
    )

    assert policy._city_outfit_decision(shop).command == "list cap"
    assert policy._city_outfit_decision(shop).command == "buy cap"
    assert policy._city_outfit_decision(shop).command == "wear cap"
    assert policy._city_outfit_decision(shop).command == "eq all"
    policy.observe_text("<worn on head> a hard leather cap\n")

    return_move = policy._city_outfit_decision(shop)

    assert return_move is not None
    assert return_move.command == "south"


def test_city_rearm_acquires_pounding_weapon_then_restores_piercing_primary() -> None:
    mace = ObjectSource(
        3352,
        "standard mace",
        "a standard mace",
        5,
        (0, 4, 4, 7),
        5,
        wear_flags=1 | (1 << 13),
    )
    dagger = ObjectSource(
        5252,
        "long dagger slim",
        "a long slim dagger",
        5,
        (0, 2, 5, 11),
        100,
        wear_flags=1 | (1 << 13),
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "bounty hunter"}),
        "swordfish",
        city_rearm=True,
        city_rearm_pounding=True,
        gear_catalog=GearCatalog({mace.vnum: mace, dagger.vnum: dagger}),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.city_rearm_role = "pounding"
    policy.city_rearm_route_index = 16
    policy.city_rearm_capacity_checked = True
    shop = CharacterState(
        room_name="Road Crossing",
        room_vnum="3120",
        position=7,
        inventory=[[{"short_desc": "a long slim dagger"}]],
    )

    quote = policy._city_rearm_decision(shop)
    buy = policy._city_rearm_decision(shop)
    wield_mace = policy._city_rearm_decision(shop)
    policy.gear_worn = [mace]
    audit = policy._city_rearm_decision(shop)
    policy.observe_text("[weapon] a standard mace")
    switch = policy._city_rearm_decision(shop)
    policy.gear_worn = [dagger]
    policy.observe_text("[weapon] a long slim dagger")
    return_move = policy._city_rearm_decision(shop)

    assert quote is not None and quote.command == "list mace"
    assert buy is not None and buy.command == "buy mace"
    assert wield_mace is not None and wield_mace.command == "wield mace"
    assert audit is not None and audit.command == "eq all"
    assert switch is not None and switch.command == "wield dagger"
    assert return_move is not None and return_move.command == "west"
    assert policy.failure is None


def test_city_outfit_defers_shop_basic_more_than_five_levels_high() -> None:
    policy = StarterPolicy(_spec(), "swordfish", city_outfit=True)
    policy.city_outfit_audited = True
    policy.city_outfit_route_index = 7
    policy.city_outfit_plan = [("body", "jerkin")]
    shop = CharacterState(
        level=8,
        room_name="The Leather Shop",
        room_vnum="3035",
        position=7,
    )

    assert policy._city_outfit_decision(shop).command == "list jerkin"
    policy.observe_text("[ 14   266]  a studded leather jerkin\n")

    audit = policy._city_outfit_decision(shop)

    assert audit is not None
    assert audit.command == "eq all"
    assert policy.city_outfit_deferred_categories == {"body"}

    policy.observe_text("<worn on body>      -\n")
    return_move = policy._city_outfit_decision(shop)

    assert return_move is not None
    assert return_move.command == "south"
    assert policy.failure is None


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


def test_mage_waits_for_combat_action_cooldown_after_spell_feedback(
    monkeypatch,
) -> None:
    clock = {"now": 100.0}
    monkeypatch.setattr(
        "dd4tester.starter.time.monotonic",
        lambda: clock["now"],
    )
    policy = StarterPolicy(_spec(), "swordfish", objective_level=7)
    policy.combat_active = True
    policy.active_target = "a prowling wolf"
    state = CharacterState(
        hp=90,
        max_hp=96,
        mana=180,
        max_mana=268,
        position=6,
    )

    first = policy._between_round_combat_decision(state)
    policy.observe_text("You launch a volley of 3 magic missiles at a wolf!\n")
    clock["now"] = 102.0
    premature = policy._between_round_combat_decision(state)
    clock["now"] = 103.1
    ready = policy._between_round_combat_decision(state)

    assert first is not None
    assert first.command == "cast 'magic missile' wolf"
    assert premature is None
    assert ready is not None
    assert ready.command == "cast 'magic missile' wolf"


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


def test_generic_dd4_flee_failure_clears_pending_state_for_retry() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("ambush"),
        fastwalk_hunt_stops=(
            FieldHuntStop(
                (),
                "goblin looter",
                minimum_combat_health_ratio=0.5,
            ),
        ),
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.combat_active = True
    policy.fastwalk_attack_started = True
    policy.active_target = "The goblin looter"
    policy.flee_pending = True
    state = CharacterState(
        level=8,
        hp=34,
        max_hp=120,
        mana=174,
        max_mana=327,
        position=6,
        room_name="In a forest clearing",
        room_vnum="4513",
        enemies=[[{"name": "The goblin looter", "level": "7"}]],
    )

    policy.observe_text(
        "You failed! The goblin looter has some big nasty wounds and scratches.\n"
    )
    decision = policy.next_decision(state)

    assert policy.flee_pending is False
    assert decision is not None
    assert decision.command == "flee"


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


def test_starter_runner_uses_mudlet_connection_for_mudlet_profile(tmp_path) -> None:
    spec = _spec(
        transport="mudlet",
        mudlet_directory=str(tmp_path / "shared-mudlet"),
    )
    runner = StarterBotRunner(spec, tmp_path / "starter.yaml")

    connection = runner._default_connection(spec)

    assert isinstance(connection, MudletConnection)
    assert connection.bridge.paths.directory == tmp_path / "shared-mudlet"


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
    assert audit.command == "eq all"
    policy.after_command(audit)

    policy.observe_text("<<worn on head>      -")
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
    assert confirm.command == "eq all"
    policy.after_command(confirm)

    policy.observe_text("<<worn on head>      a recovery circlet")
    policy.prompt_ready = True
    sleep = policy.next_decision(state)
    assert sleep is not None
    assert sleep.command == "sleep"


def test_thief_recovery_stance_preserves_piercing_primary() -> None:
    dagger = ObjectSource(
        5252,
        "long dagger slim",
        "a long slim dagger",
        5,
        (0, 2, 5, 11),
        100,
        wear_flags=1 | (1 << 13),
    )
    sword = ObjectSource(
        4002,
        "rusty sword",
        "a rusty sword",
        5,
        (0, 4, 8, 3),
        100,
        wear_flags=1 | (1 << 13),
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        gear_catalog=GearCatalog({dagger.vnum: dagger, sword.vnum: sword}),
    )
    policy.in_world = True
    policy.gear_audited = True
    policy.gear_allowed_categories = {"wield"}
    policy.gear_worn = [dagger]
    state = CharacterState(
        level=18,
        hp=100,
        max_hp=100,
        mana=100,
        max_mana=100,
        move=10,
        max_move=100,
        position=7,
        room_name="By the Temple Altar",
        room_vnum="3054",
        room_flags=["safe", "healing"],
        inventory=[[{"short_desc": "a rusty sword"}]],
    )

    assert policy._gear_decision(state) is None
    assert policy.gear_worn == [dagger]


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


def test_stand_waits_for_server_confirmation_before_another_wake_command() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.in_world = True
    sleeping = CharacterState(
        hp=100,
        max_hp=100,
        mana=100,
        max_mana=100,
        move=100,
        max_move=100,
        position=4,
        room_name="By the Temple Altar",
        room_vnum="3054",
        room_flags=["safe"],
    )

    policy.after_command(BotDecision("stand", "resume after safe-room recovery"))
    policy.prompt_ready = True

    assert policy.next_decision(sleeping) is None
    assert policy.stand_confirmation_pending is True

    policy.observe_text("You wake and ready yourself for action.")
    sleeping.position = 7
    policy.prompt_ready = True
    decision = policy.next_decision(sleeping)

    assert policy.stand_confirmation_pending is False
    assert decision is None or decision.command != "stand"


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
    assert audit.command == "eq all"
    policy.after_command(audit)

    policy.observe_text("You're dying of hunger!")
    policy.prompt_ready = True
    retry = policy.next_decision(state)
    assert retry is not None
    assert retry.command == "eq all"
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
    assert audit.command == "eq all"
    policy.after_command(audit)

    # DD4 can send the prior command's prompt before the equipment listing.
    policy.prompt_ready = True
    assert policy.next_decision(state) is None

    policy.observe_text("[weapon]            -")
    policy.prompt_ready = True
    wear = policy.next_decision(state)

    assert wear is not None
    assert wear.command == "wear broadsword"


def test_gmcp_equipment_does_not_replace_pending_eq_all_slot_audit() -> None:
    buckler = ObjectSource(
        9002,
        "metal buckler",
        "a metal buckler",
        9,
        (1, 0, 0, 0),
        5,
        wear_flags=1 << 9,
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        gear_catalog=GearCatalog({buckler.vnum: buckler}),
    )
    policy.in_world = True
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
        inventory=[[{"short_desc": "a metal buckler"}]],
    )

    audit = policy._gear_decision(state)
    assert audit is not None
    assert audit.command == "eq all"
    policy.after_command(audit)
    policy.observe_events(
        [GameEvent("equipment_changed", "gmcp", {"value": []})],
        state,
    )
    policy.last_response = "Your description is unchanged."

    retry = policy._gear_decision(state)

    assert retry is not None
    assert retry.command == "eq all"
    assert policy.gear_allowed_categories is None


@pytest.mark.parametrize(
    "rejection",
    [
        "You cannot use lances.",
        "It is too heavy for you to wield.",
    ],
)
def test_rejected_weapon_is_blacklisted_and_previous_weapon_is_rearmed(
    rejection: str,
) -> None:
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
    policy.gear_allowed_categories = {"wield"}
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
    policy.observe_text(rejection)

    state.inventory = [[
        {"short_desc": "a wooden spear"},
        {"short_desc": "a dagger"},
    ]]
    audit = policy._gear_decision(state)
    assert audit is not None
    assert audit.command == "eq all"

    policy.observe_text("[weapon]            -")
    rearm = policy._gear_decision(state)
    assert rearm is not None
    assert rearm.command == "wear dagger"
    assert policy.gear_unusable_keywords == {"spear"}


def test_profession_rejected_wear_is_blacklisted_without_retrying() -> None:
    buckler = ObjectSource(
        9002,
        "metal buckler",
        "a metal buckler",
        9,
        (1, 0, 0, 0),
        5,
        wear_flags=1 << 9,
    )
    policy = StarterPolicy(
        _spec(race="drow"),
        "swordfish",
        gear_catalog=GearCatalog({buckler.vnum: buckler}),
    )
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
    assert policy.gear_prohibited_categories == {"shield"}
    assert policy.gear_pending_wear_keyword is None
    assert policy.gear_command_queue == []
    assert policy.gear_audit_pending is False
    assert policy.gear_audited is False
    assert policy.gear_confirmation_required is False
    assert policy.gear_applied_stance is None


def test_eq_all_records_empty_and_occupied_profession_wear_slots() -> None:
    categories = _equipment_slot_categories(
        "<<worn on head>      -\n"
        "[shield]             -\n"
        "[weapon]             a dagger\n"
    )

    assert categories == {"head", "shield", "wield"}
    assert starter._equipment_audit_descriptions(
        "<<worn on head>      -\n"
        "[shield]             a metal buckler\n"
        "[weapon]             [Rare] a dagger\n"
    ) == ["a metal buckler", "[Rare] a dagger"]


def test_field_readiness_fills_audited_empty_slots_from_carried_gear() -> None:
    banner = ObjectSource(
        3716,
        "banner illumination",
        "banner of illumination",
        1,
        (0, 0, -1, 0),
        0,
        wear_flags=1,
    )
    pouch = ObjectSource(
        3720,
        "small leather pouch",
        "a small leather pouch",
        9,
        (0, 0, 0, 0),
        0,
        wear_flags=1 << 16,
    )
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        gear_catalog=GearCatalog({banner.vnum: banner, pouch.vnum: pouch}),
    )
    policy.gear_allowed_categories = {"light", "pouch"}
    policy.gear_empty_category_counts = starter._equipment_empty_category_counts(
        "[used as light]     -\n"
        "<<secured to belt>   -\n"
    )
    state = CharacterState(
        level=8,
        inventory=[[
            {"short_desc": "a small leather pouch"},
            {"short_desc": "(Glowing) banner of illumination"},
        ]],
    )

    first = policy._fastwalk_carried_gear_readiness_decision(state)
    second = policy._fastwalk_carried_gear_readiness_decision(state)
    complete = policy._fastwalk_carried_gear_readiness_decision(state)

    assert first is not None
    assert first.command == "wear pouch"
    assert second is not None
    assert second.command == "wear illumination"
    assert complete is None


def test_field_readiness_does_not_replace_verified_primary_weapon() -> None:
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
        _spec(**{"class": "thief", "subclass": "ninja"}),
        "swordfish",
        gear_catalog=GearCatalog({dagger.vnum: dagger}),
    )
    policy.gear_allowed_categories = {"wield"}
    policy.gear_empty_category_counts = starter._equipment_empty_category_counts(
        "[weapon] -\n"
    )
    policy.primary_weapon_observed = True
    policy.primary_weapon_lost = False

    decision = policy._fastwalk_carried_gear_readiness_decision(
        CharacterState(level=17, inventory=[[{"short_desc": "a dagger"}]]),
    )

    assert decision is None


def test_weapon_switch_acknowledgements_update_primary_state() -> None:
    policy = StarterPolicy(_spec(), "swordfish")
    policy.primary_weapon_observed = True
    policy.primary_weapon_lost = False

    policy.observe_text("You stop using a long slim dagger.\n")
    assert policy.primary_weapon_observed is False
    assert policy.primary_weapon_lost is True

    policy.observe_text("You wield a long slim dagger.\n")
    assert policy.primary_weapon_observed is True
    assert policy.primary_weapon_lost is False


def test_field_route_recalls_immediately_after_pitch_black_response() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
    )
    policy.observe_text("It is pitch black...")
    state = CharacterState(
        level=8,
        room_name="The large cave",
        room_vnum="4023",
        area="Moria",
        position=7,
    )

    decision = policy._fastwalk_research_decision(state)

    assert decision is not None
    assert decision.command == "recall"
    assert policy.fastwalk_returning is True
    assert "functioning light" in (policy.fastwalk_abort_reason or "")


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


def test_field_hunt_departs_at_forty_percent_move_while_flying() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
        fastwalk_hunt_stops=(FieldHuntStop((), "large orc"),),
    )
    healer = CharacterState(
        hp=177,
        max_hp=177,
        mana=142,
        max_mana=142,
        move=100,
        max_move=220,
        room_name="By the Temple Altar",
        room_vnum="3054",
        room_flags=["safe", "healing"],
        affects=[[{"name": "fly", "gives": "flight"}]],
    )

    assert policy._recovery_decision(healer) is None
    assert policy.fastwalk_recovery_ready is True


def test_field_hunt_departs_at_aggressive_health_and_mana_reserve() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
        fastwalk_hunt_stops=(FieldHuntStop((), "large orc"),),
    )
    healer = CharacterState(
        hp=75,
        max_hp=100,
        mana=30,
        max_mana=100,
        move=200,
        max_move=220,
        room_name="By the Temple Altar",
        room_vnum="3054",
        room_flags=["safe", "healing"],
        affects=[[]],
    )

    assert policy._recovery_decision(healer) is None
    assert policy.fastwalk_recovery_ready is True


def test_field_hunt_requires_ninety_percent_move_without_flight() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
        fastwalk_hunt_stops=(FieldHuntStop((), "large orc"),),
    )
    healer = CharacterState(
        hp=177,
        max_hp=177,
        mana=142,
        max_mana=142,
        move=100,
        max_move=220,
        room_name="By the Temple Altar",
        room_vnum="3054",
        room_flags=["safe", "healing"],
        affects=[[]],
    )

    decision = policy._recovery_decision(healer)

    assert decision is not None
    assert decision.command == "sleep"
    assert policy.fastwalk_recovery_ready is False


def test_fastwalk_departure_gate_catches_low_move_after_split_gmcp_updates() -> None:
    policy = StarterPolicy(
        _spec(),
        "swordfish",
        fastwalk_route=route_named("moria"),
        fastwalk_hunt_stops=(FieldHuntStop((), "large orc"),),
    )
    policy.in_world = True
    policy.prompt_ready = True
    healer = CharacterState(
        hp=242,
        max_hp=242,
        mana=235,
        max_mana=235,
        move=125,
        max_move=310,
        room_name="By the Temple Altar",
        room_vnum="3054",
        room_flags=["safe", "healing"],
        affects=[[]],
    )

    decision = policy._fastwalk_research_decision(healer)

    assert decision is not None
    assert decision.command == "sleep"


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


def test_sellable_inventory_releases_redundant_protected_headgear() -> None:
    tophat = _gear_item(
        4421,
        "tophat hat",
        "a tophat",
        (12, 10),
        (17, 4),
    )
    catalog = GearCatalog({tophat.vnum: tophat})

    assert _sellable_inventory_keyword(
        [[{"short_desc": "a tophat", "quan": "4"}]],
        catalog,
    ) == "tophat"
    assert _sellable_inventory_keyword(
        [[{"short_desc": "a tophat", "quan": "1"}]],
        catalog,
    ) is None


def test_liquidation_retains_one_stat_tophat_and_sells_three_duplicates() -> None:
    tophat = _gear_item(
        4421,
        "tophat hat",
        "a tophat",
        (12, 10),
        (17, 4),
    )
    policy = StarterPolicy(
        _spec(**{"class": "thief", "subclass": "ninja", "race": "drow"}),
        "swordfish",
        liquidate_loot=True,
        gear_catalog=GearCatalog({tophat.vnum: tophat}),
    )
    policy.gear_audited = True
    state = CharacterState(
        level=11,
        room_name="Mage's Laboratory",
        room_vnum="3019",
        inventory=[[{"short_desc": "a tophat", "quan": "4"}]],
    )

    policy._liquidate_loot_decision(state)

    assert [keyword for keyword, _ in policy.sale_plan] == [
        "tophat",
        "tophat",
        "tophat",
    ]


def test_liquidation_sells_carried_collars_when_two_are_already_worn() -> None:
    collar = ObjectSource(
        4538,
        "collar war dog",
        "a war dog collar",
        9,
        (0, 0, 0, 0),
        0,
        wear_flags=1 | (1 << 2),
        affects=((19, 1),),
        weight=20,
    )
    policy = StarterPolicy(
        _spec(race="drow"),
        "swordfish",
        liquidate_loot=True,
        gear_catalog=GearCatalog({collar.vnum: collar}),
    )
    policy.gear_audited = True
    policy.gear_worn = [collar, collar]
    state = CharacterState(
        level=8,
        room_name="Mage's Laboratory",
        room_vnum="3019",
        inventory=[[{"short_desc": "a war dog collar", "quan": "2"}]],
        stats={"carry_wt": 161, "maxcarry_wt": 170},
    )

    policy._liquidate_loot_decision(state)

    assert [keyword for keyword, _ in policy.sale_plan] == [
        "collar",
        "collar",
    ]


def test_sellable_inventory_uses_source_keyword_for_unfamiliar_equipment() -> None:
    jerkin = _gear_item(9004, "jerkin leather", "a leather jerkin")

    assert _sellable_inventory_keyword(
        [[{"short_desc": "a leather jerkin"}]],
        GearCatalog({jerkin.vnum: jerkin}),
    ) == "jerkin"


def test_sellable_inventory_releases_strength_penalty_ring() -> None:
    ring = ObjectSource(
        4000,
        "yellow green ring",
        "a yellow and green ring",
        9,
        (1, 0, 0, 0),
        50,
        wear_flags=1 | (1 << 1),
        affects=((1, -2), (5, 1)),
    )

    assert _sellable_inventory_keyword(
        [[{"short_desc": "a yellow and green ring"}]],
        GearCatalog({ring.vnum: ring}),
    ) == "yellow"


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
