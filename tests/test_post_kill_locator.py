from dataclasses import replace

import pytest

from dd4tester.character import CharacterSpec
from dd4tester.hunt_candidates import ACT_SENTINEL, MobileSource, MobReset, WorldSource
from dd4tester.starter import BotDecision, FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


@pytest.fixture
def hunt():
    locator = FieldHuntStop(
        (), None, where_target="wanderer", actions=("where wanderer",),
        where_source_mobile_vnum=100, preserve_where_route_waypoints=True,
        where_location_routes=(("next room", ("203",)),),
        where_relocation_routes=(("202", "next room", ("203",)),),
        maximum_where_relocations=2,
    )
    target = FieldHuntStop(
        (), "wanderer", exact_target=True, source_mobile_vnum=100,
        source_policy_id="source-ranked-hunt-test-100-202-8",
        source_target_armed=False, route_vnums=("202",),
        allow_source_bystander_encounter=True,
    )
    world = WorldSource(
        mobiles={100: MobileSource(100, "wanderer", "a wanderer", 6, 0, 0, "test.are")},
        mob_resets=[MobReset(100, 202, 3, ())],
    )
    policy = StarterPolicy(
        CharacterSpec.from_mapping({"name": "Testor", "race": "human", "gender": "male", "class": "ranger"}),
        "test-password", source_world=world, fastwalk_hunt_stops=(locator, target),
        fastwalk_kill_limit=3,
    )
    policy.fastwalk_hunt_stop_index = 2
    policy.fastwalk_locator_target_present_observed = True
    policy.fastwalk_consider_outcomes = {"wanderer": True}
    policy.completed_kills = [{
        "mob_name": "a wanderer", "source_mobile_vnum": 100,
        "source_policy_id": target.source_policy_id, "xp_gained": 80,
    }]
    policy.needs_food = policy.needs_drink = False
    policy.current_room = "202"
    state = CharacterState(
        level=8, hp=100, max_hp=100, mana=100, max_mana=100,
        move=100, max_move=100, position=7, room_vnum="202",
    )
    return policy, state, locator, target


def test_productive_hunt_queries_next_target_with_original_locator_cap(hunt):
    policy, state, _, _ = hunt
    decision = policy._fastwalk_where_relocation_decision(state)
    assert decision is not None and decision.command == "where wanderer"
    assert policy.fastwalk_where_relocation_attempts == 1
    policy.fastwalk_locator_target_present_observed = True
    policy.fastwalk_where_relocation_attempts = 2
    assert policy._fastwalk_where_relocation_decision(state) is None


def test_post_kill_locator_requires_new_isolated_target_check(hunt, monkeypatch):
    policy, state, _, _ = hunt
    policy.fastwalk_where_relocation_result_ready = True
    policy.fastwalk_where_locations = ("next room",)
    policy.fastwalk_where_decisions = [{}]
    policy.consider_target = "wanderer"
    policy.consider_target_selector = "#old"
    policy.consider_viable = True
    monkeypatch.setattr(policy, "_fastwalk_hunt_plan_decision", lambda state: BotDecision("look", "fresh target"))
    decision = policy._fastwalk_where_relocation_decision(state)
    assert decision is not None and decision.command == "look"
    assert policy.fastwalk_hunt_stops[-1].route_vnums == ("203",)
    assert policy.fastwalk_hunt_stops[-1].allow_source_bystander_encounter is False
    assert policy.fastwalk_hunt_stops[-1].require_isolated
    assert policy.fastwalk_hunt_stops[-1].maximum_target_count == 1
    assert policy.consider_target is policy.consider_target_selector is policy.consider_viable is None
    assert policy.fastwalk_where_decisions[-1]["after_objective_kills"] == 1


def test_no_further_registered_destination_ends_productive_search_without_failure(hunt):
    policy, state, _, _ = hunt
    policy.fastwalk_where_relocation_result_ready = True
    policy.fastwalk_where_locations = ("unregistered room",)
    assert policy._fastwalk_where_relocation_decision(state) is None
    assert policy.fastwalk_where_relocation_closed
    assert policy.fastwalk_abort_reason is None


@pytest.mark.parametrize("reason", (
    "kill-cap", "spawn-cap", "no-world", "sentinel", "special", "equipped",
    "loot", "probe", "sanctuary", "familiar", "unproven-weapon",
    "below-band", "loss", "injured", "hungry", "returning", "runtime",
    "other-kill", "no-xp", "route-hazard",
))
def test_post_kill_lookup_does_not_extend_other_hunt_contracts(hunt, reason):
    policy, state, locator, target = hunt
    world = policy.source_world
    if reason == "kill-cap":
        policy.fastwalk_kill_limit = 1
    elif reason == "spawn-cap":
        world.mob_resets = [MobReset(100, 202, 1, ())]
    elif reason == "no-world":
        policy.source_world = None
    elif reason == "sentinel":
        world.mobiles[100] = replace(world.mobiles[100], act_flags=ACT_SENTINEL)
    elif reason == "special":
        world.mobile_specials[100] = ("spec_poison",)
    elif reason == "equipped":
        world.mob_resets = [MobReset(100, 202, 3, (), ((1, 900),))]
    elif reason in {"loot", "probe", "sanctuary", "familiar", "unproven-weapon"}:
        target = replace(target, **{
            "loot": {"source_loot_object_vnums": (900,)},
            "probe": {"require_damage_window_probe": True},
            "sanctuary": {"require_sanctuary": True},
            "familiar": {"require_familiar": True},
            "unproven-weapon": {"source_target_armed": None},
        }[reason])
    elif reason == "below-band":
        policy.fastwalk_consider_outcomes["wanderer"] = False
    elif reason == "loss":
        state.xp_loss_observed = True
    elif reason == "injured":
        state.hp = 10
    elif reason == "hungry":
        policy.needs_food = True
    elif reason == "returning":
        policy.fastwalk_returning = True
    elif reason == "runtime":
        policy.runtime_boundary_requested = True
    elif reason == "other-kill":
        policy.completed_kills.append({"mob_name": "interrupter", "source_mobile_vnum": 101, "xp_gained": 10})
    elif reason == "no-xp":
        policy.completed_kills[0]["xp_gained"] = None
    elif reason == "route-hazard":
        policy.fastwalk_abort_reason = "source-registered hazardous bystander"
    assert not policy._post_kill_locator_allowed(state, locator, target)
