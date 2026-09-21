from dataclasses import replace
from pathlib import Path

import pytest

from dd4tester.campaign import (
    _provision_funding_bounded_exception_allowed,
    _select_source_ranked_hunt_candidate,
    _source_ranked_capacity_research_candidate,
    _source_ranked_hunt_stops,
    _source_ranked_policy_id,
    _source_ranked_route_program_candidate_allowed,
    _source_ranked_route_program_fastwalk_options,
    _source_ranked_segment_kill_limit,
)
from dd4tester.hunt_candidates import (
    ExitSource, HuntCandidate, MobileProgram, MobileSource, MobReset, RoomSource, WorldSource,
    load_world_source, rank_hunt_candidates,
)
from dd4tester.character import CharacterSpec
from dd4tester.fastwalks import Fastwalk
from dd4tester.starter import FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


def _candidate(population=3, entries=2):
    # moria.are mobile 4004: ordinary level-5 orc, global limit 3,
    # two M entries at 4028. The population is three, not 3 * 2.
    return HuntCandidate(
        status="reject", score=100, area_file="moria.are", mobile_vnum=4004,
        target="the orc", target_keyword="orc", level=5, room_vnum=4028,
        room_name="Tunnel", route=("south",), source_spawn_limit=population,
        room_spawn_count=entries, boot_kills=0, loot=(), source_value=0,
        contained_coins=0, hazards=(), estimated_level_range=(3, 7),
        estimated_base_hp_range=(20, 98), estimated_peak_round_damage=55,
        autonomy_rejections=("target reset capacity exceeds one",), specials=(),
    )


def _select(candidate, **updates):
    state = {"world_boot_id": "boot-1", "level": 8, "hp": 113, "max_hp": 113}
    state.update(updates)
    return _select_source_ranked_hunt_candidate(
        (candidate,), state, character_level=8, character_max_hp=113,
    )


@pytest.mark.parametrize("population", [2, 3, 4])
@pytest.mark.parametrize("entries", [1, 2])
@pytest.mark.parametrize("character_class", ["mage", "thief", "warrior"])
def test_global_population_is_not_multiplied_by_local_resets(
    population, entries, character_class,
):
    candidate = _candidate(population, entries)
    assert _select(candidate, character_class=character_class) == candidate
    assert not candidate.autonomous_safe
    assert candidate.status == "reject"  # Still live-isolation research.


@pytest.mark.parametrize("population,entries", [
    (0, 1), (5, 1), (100, 1), (3, 0), (3, 3), (True, 1), (3, True), (3.0, 1),
])
def test_population_research_stays_bounded(population, entries):
    assert not _source_ranked_capacity_research_candidate(
        _candidate(population, entries), character_level=8,
    )


@pytest.mark.parametrize("hazard", [
    "target is aggressive", "target has special procedure spec_poison",
    "target room has a dangerous reset companion",
    "route crosses a higher-level aggressive reset",
    "target is non-corporeal",
])
def test_population_research_cannot_override_other_source_rejections(hazard):
    candidate = _candidate()
    candidate = replace(candidate, autonomy_rejections=(*candidate.autonomy_rejections, hazard))
    assert not _source_ranked_capacity_research_candidate(candidate, character_level=8)
    assert _select(candidate) is None


def test_population_research_preserves_current_reboot_loss():
    candidate = _candidate()
    policy_id = _source_ranked_policy_id(candidate, character_level=8)
    assert _select(candidate, campaign_source_ranked_xp_loss_policies=[{
        "boot_id": "boot-1", "level": 8, "policy_id": policy_id,
        "loss_count": 2, "xp_delta": -68,
    }]) is None


def test_population_research_does_not_admit_entirely_below_band_mobile():
    candidate = replace(_candidate(), level=1, estimated_level_range=(1, 3))
    assert _select(candidate) is None


def test_wandering_population_plan_keeps_exact_isolation_and_global_kill_bound():
    candidate = _candidate()
    world = WorldSource(
        mobiles={4004: MobileSource(4004, "orc", "the orc", 5, 0, 0, "moria.are")},
        rooms={
            4028: RoomSource(4028, "Tunnel", "moria.are", exits={
                "south": ExitSource("south", 4027, 0, -1),
            }),
            4027: RoomSource(4027, "Passage", "moria.are", exits={
                "north": ExitSource("north", 4028, 0, -1),
            }),
        },
        mob_resets=[MobReset(4004, 4028, 3, ()), MobReset(4004, 4028, 3, ())],
    )
    stops = _source_ranked_hunt_stops(
        candidate, world, character_level=8,
        state={"level": 8, "hp": 113, "max_hp": 113},
    )
    assert stops[0].where_target == "orc"
    targets = [stop for stop in stops if stop.target is not None]
    assert len(targets) == 2
    assert all(stop.exact_target and stop.require_isolated for stop in targets)
    assert all(stop.maximum_target_count == 1 for stop in targets)
    assert all(not stop.consider_only for stop in targets)
    assert _source_ranked_segment_kill_limit((candidate,), stops) == 3


def _intercept_policy(*, character_class="mage", kill_limit=3, prior_kills=0):
    policy = StarterPolicy(
        CharacterSpec.from_mapping({
            "name": "Testchar", "race": "human", "gender": "female",
            "class": character_class,
        }),
        "test-password", title_configured=True, description_configured=True,
        fastwalk_route=Fastwalk(
            "source-ranked population", 1, 100, "3e", recall_after_loot=True,
        ),
        fastwalk_hunt_stops=(
            FieldHuntStop((), where_target="orc", actions=("where orc",)),
            FieldHuntStop((), "orc", source_mobile_vnum=4004, exact_target=True),
            FieldHuntStop((), "orc", source_mobile_vnum=4004, exact_target=True),
        ),
        fastwalk_kill_limit=kill_limit,
    )
    policy.in_world = policy.prompt_ready = policy.fastwalk_recall_started = True
    policy.fastwalk_targetmode_configured = True
    policy.fastwalk_outbound_index = 1
    policy.fastwalk_intercept_returning = True
    policy.current_room = "4010"
    policy.active_target = "the orc"
    policy.active_target_mobile_vnum = 4004
    policy.fastwalk_attack_started = policy.combat_active = True
    policy.completed_kills = [
        {"mob_name": "the orc", "source_mobile_vnum": 4004, "xp_gained": 100}
        for _ in range(prior_kills)
    ]
    return policy


def _observe_kill_and_loot(policy, **resource_changes):
    # Captured run 12702: objective intercepted at 4010 before endpoint 4028.
    policy.observe_text(
        "The orc is DEAD!!\nYou receive 89 experience points for the kill.\n"
    )
    state = CharacterState(
        level=8, hp=109, max_hp=113, mana=287, max_mana=324,
        move=207, max_move=220, room_vnum="4010", position=7,
    )
    state = replace(state, **resource_changes)
    for command in ("get all corpse", "sacrifice corpse", "inventory"):
        decision = policy.next_decision(state)
        assert decision is not None and decision.command == command
        policy.after_command(decision)
        policy.prompt_ready = True
    return policy.next_decision(state)


@pytest.mark.parametrize("character_class", ["mage", "thief", "warrior"])
def test_outbound_objective_retains_budget_and_resumes_after_loot(character_class):
    policy = _intercept_policy(character_class=character_class)
    decision = _observe_kill_and_loot(policy)
    assert len(policy.objective_kills) == 1
    assert not policy.fastwalk_objective_budget_complete
    assert not policy.fastwalk_recall_after_loot
    assert not policy.fastwalk_returning
    assert decision.command == "east"
    assert policy.fastwalk_outbound_index == 2


@pytest.mark.parametrize("kill_limit,prior_kills", [(1, 0), (3, 2)])
def test_intercept_returns_after_counting_the_budget_completing_kill(kill_limit, prior_kills):
    policy = _intercept_policy(kill_limit=kill_limit, prior_kills=prior_kills)
    decision = _observe_kill_and_loot(policy)
    assert len(policy.objective_kills) == kill_limit
    assert policy.fastwalk_objective_budget_complete
    assert decision.command == "recall"


@pytest.mark.parametrize("resource_changes", [{"hp": 20}, {"mana": 1}, {"move": 1}])
def test_intercept_continuation_preserves_post_loot_resource_gates(resource_changes):
    policy = _intercept_policy()
    decision = _observe_kill_and_loot(policy, **resource_changes)
    assert not policy.fastwalk_objective_budget_complete
    assert decision.command == "recall"


def test_intercept_continuation_does_not_clear_a_prior_return_request():
    policy = _intercept_policy()
    policy.fastwalk_recall_after_loot = True
    decision = _observe_kill_and_loot(policy)
    assert not policy.fastwalk_objective_budget_complete
    assert decision.command == "recall"


@pytest.mark.parametrize("other_limit", [3, 4, 7])
def test_catalog_population_uses_other_rooms_without_multiplying_entries(other_limit):
    world = WorldSource(
        mobiles={4004: MobileSource(4004, "orc", "the orc", 5, 0, 0, "moria.are")},
        rooms={
            3001: RoomSource(3001, "Recall", "midgaard.are", exits={
                "south": ExitSource("south", 4028, 0, -1),
            }),
            4028: RoomSource(4028, "Tunnel", "moria.are", exits={
                "north": ExitSource("north", 3001, 0, -1),
                "south": ExitSource("south", 4027, 0, -1),
            }),
            4027: RoomSource(4027, "Passage", "another.are", exits={
                "north": ExitSource("north", 4028, 0, -1),
            }),
        },
        mob_resets=[
            MobReset(4004, 4028, 3, ()), MobReset(4004, 4028, 3, ()),
            MobReset(4004, 4027, other_limit, ()),
        ],
    )
    candidates = rank_hunt_candidates(
        world, character_level=8, include_xp_only=True, include_all_areas=True,
        character_max_hp=113,
    )
    candidate = next(item for item in candidates if item.room_vnum == 4028)
    assert candidate.source_spawn_limit == other_limit
    assert candidate.room_spawn_count == 2
    assert (
        f"target reset permits up to {other_limit} matching mobiles in the room"
        in candidate.hazards
    )
    assert _source_ranked_capacity_research_candidate(candidate, character_level=8) == (
        other_limit <= 4
    )


def _population_route():
    candidate = replace(
        _candidate(), route_attack_program_mobile_vnums=(3064,),
        route_preflight_room_vnum="3001", route_preflight_command="where drunk",
        route_preflight_target="the drunk", route_preflight_level_range=(1, 4),
        route_preflight_hard_hazard=True,
        route_preflight_route_room_names=("temple square", "main street"),
    )
    world = WorldSource(
        mobiles={3064: MobileSource(
            3064, "drunk", "the drunk", 2, 0, 400, "midgaard.are",
            programs=(MobileProgram("greet_prog", "10", ("mpkill $n",)),),
        )},
        mob_resets=[MobReset(3064, 3007, 3, ())],
    )
    return candidate, world


@pytest.mark.parametrize("character_class", ["mage", "thief", "warrior"])
def test_capacity_endpoint_does_not_turn_bounded_greeter_into_route_veto(character_class):
    candidate, world = _population_route()
    # This opt-in is only for execution options; ordinary candidate admission
    # continues to require the separate capacity-research selector.
    assert not _source_ranked_route_program_candidate_allowed(
        candidate, character_level=8, source_world=world,
    )
    options = _source_ranked_route_program_fastwalk_options(
        world, candidate, {"max_hp": 113, "character_class": character_class},
        character_level=8,
    )
    assert options["route_preflight_command"] is None
    assert options["route_preflight_scan_room_vnums"] == ()
    assert options["route_source_program_audited"]
    assert candidate.status == "reject"
    assert candidate.autonomy_rejections == ("target reset capacity exceeds one",)


def test_flight_funding_accepts_only_the_audited_moria_route_preflight():
    world = load_world_source(
        Path("runs/dd4-source/server/area"),
        include_all_areas=True,
    )
    candidate = next(
        candidate
        for candidate in rank_hunt_candidates(
            world,
            character_level=8,
            character_max_hp=113,
            boot_kill_counts_by_mobile_vnum={4005: 5},
            include_below_band=True,
            include_all_areas=True,
        )
        if candidate.mobile_vnum == 4005 and candidate.room_vnum == 4022
    )
    state = {
        "level": 8,
        "max_hp": 113,
        "world_boot_id": "boot-1",
        "currencies": {"silver": 2, "copper": 0},
        "campaign_magic_shop_flight_price": 131,
    }

    assert _source_ranked_route_program_candidate_allowed(
        candidate,
        character_level=8,
        source_world=world,
    )
    assert _provision_funding_bounded_exception_allowed(
        state,
        candidate,
        character_level=8,
        boot_id="boot-1",
        prefer_completed_funding_candidate=True,
        source_world=world,
    )
    assert not _provision_funding_bounded_exception_allowed(
        state,
        candidate,
        character_level=8,
        boot_id="boot-1",
        prefer_completed_funding_candidate=True,
    )
    assert not _provision_funding_bounded_exception_allowed(
        state,
        replace(candidate, route_preflight_target="an unknown greeter"),
        character_level=8,
        boot_id="boot-1",
        prefer_completed_funding_candidate=True,
        source_world=world,
    )


@pytest.mark.parametrize("changes", [
    {"source_spawn_limit": 5}, {"room_spawn_count": 3},
    {"equipped_weapons": ("sword",)}, {"specials": ("spec_poison",)},
    {"route_hard_hazard_targets": ("guard",)},
    {"route_special_mobile_vnums": (100,)},
    {"route_attack_program_mobile_vnums": (3064, 100)},
    {"route_preflight_target": "someone else"},
    {"autonomy_rejections": (
        "target reset capacity exceeds one", "target room has a dangerous reset companion",
    )},
])
def test_capacity_route_opt_in_preserves_other_exclusions(changes):
    candidate, world = _population_route()
    options = _source_ranked_route_program_fastwalk_options(
        world, replace(candidate, **changes), {"max_hp": 113}, character_level=8,
    )
    assert options["route_preflight_command"] == "where drunk"
    assert options["route_preflight_hard_hazard"]


@pytest.mark.parametrize("max_hp", [None, 0, 50])
def test_capacity_route_opt_in_still_requires_the_greeter_damage_reserve(max_hp):
    candidate, world = _population_route()
    options = _source_ranked_route_program_fastwalk_options(
        world, candidate, {"max_hp": max_hp}, character_level=8,
    )
    assert options["route_preflight_command"] == "where drunk"
    assert options["route_preflight_hard_hazard"]
