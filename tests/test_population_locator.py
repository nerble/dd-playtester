from dataclasses import replace

import pytest

from dd4tester.character import CharacterSpec
from dd4tester.hunt_candidates import (
    ACT_AGGRESSIVE, ACT_STAY_AREA, ExitSource, MobileSource, MobReset,
    ObjectSource, RoomSource, WorldSource,
)
from dd4tester.starter import FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


def population_locator_case():
    policy_id = "source-ranked-hunt-test-100-201-30"
    world = WorldSource(
        rooms={
            201: RoomSource(201, "hall", "test.are", exits={"east": ExitSource("east", 202, 0, -1)}),
            202: RoomSource(202, "hall", "test.are", exits={"west": ExitSource("west", 201, 0, -1)}),
        },
        mobiles={100: MobileSource(100, "clan member", "a clan member", 30, ACT_STAY_AREA, 0, "test.are")},
        objects={200: ObjectSource(200, "ring", "a ring", 9, (0, 0, 0, 0), 0)},
        mob_resets=[MobReset(100, room, 2, (200,), ((1, 200),)) for room in (201, 202)],
    )
    locator = FieldHuntStop(
        (), where_target="clan member", actions=("where clan",),
        where_source_mobile_vnum=100, preserve_where_route_waypoints=True,
        maximum_where_relocations=8,
        where_location_routes=(("hall", ("201", "202")),),
        where_relocation_routes=(("201", "hall", ("202",)),),
    )
    target = FieldHuntStop(
        (), "clan member", exact_target=True, require_isolated=True,
        source_mobile_vnum=100, source_policy_id=policy_id,
        source_target_armed=False, source_loot_object_vnums=(200,),
        allow_unprotected_hp_fuzz_probe=True, route_vnums=("201",),
    )
    policy = StarterPolicy(
        CharacterSpec.from_mapping({"name": "Testpilot", "race": "human", "gender": "male", "class": "warrior"}),
        "unused", fastwalk_hunt_stops=(locator, target), fastwalk_kill_limit=3,
        source_world=world,
    )
    policy.fastwalk_hunt_stop_index = 1
    policy.fastwalk_hunt_stop_skipped = True
    policy.fastwalk_hunt_looked = True
    policy.current_room = "201"
    policy.fastwalk_target_present_observed = True
    policy.fastwalk_below_band_targets.add("clan member")
    policy.fastwalk_below_band_sightings.add(("201", "clan member"))
    policy.fastwalk_source_below_band_sightings.add((policy_id, "201", "clan member"))
    policy.fastwalk_consider_outcomes["clan member"] = False
    state = CharacterState(
        level=30, room_vnum="201", hp=700, max_hp=700, mana=100, max_mana=100,
        move=100, max_move=100, position=7, exits={"east": "202"},
    )
    return policy, state


def test_below_band_individual_keeps_remaining_population_search_and_negative_evidence():
    policy, state = population_locator_case()
    decision = policy._fastwalk_hunt_plan_decision(state)
    assert decision.command == "where clan"
    assert "below-band individual" in decision.reason
    assert policy.fastwalk_consider_outcomes == {"clan member": False}
    assert policy.fastwalk_where_relocation_attempts == 1


def test_population_locator_takes_only_registered_route_and_requires_fresh_target_audit():
    policy, state = population_locator_case()
    policy.fastwalk_where_relocation_result_ready = True
    policy.fastwalk_where_locations = ("hall",)
    policy.fastwalk_locator_target_present_observed = True
    policy.fastwalk_where_decisions = [{"room_vnum": "201"}]
    decision = policy._fastwalk_where_relocation_decision(state)
    assert decision.command == "east"
    assert policy.fastwalk_hunt_stops[-1].route_vnums == ("202",)
    assert policy.consider_viable is None and policy.consider_target_selector is None
    assert policy.fastwalk_where_decisions[-1]["after_below_band_instance"] == "201"
    assert policy.fastwalk_source_below_band_sightings


@pytest.mark.parametrize("change", [
    "aggressor", "special", "single", "unknown_object", "weapon", "required_item",
    "protected", "wrong_identity", "no_sighting", "loss", "combat", "health",
    "hunger", "abort", "runtime", "kill_limit", "locator_limit", "asleep",
    "wrong_room", "unknown_vitals",
])
def test_population_locator_retains_source_survival_resource_and_finite_action_gates(change):
    policy, state = population_locator_case()
    target = policy.fastwalk_where_target_template
    if change == "aggressor":
        policy.source_world.mobiles[100] = replace(policy.source_world.mobiles[100], act_flags=ACT_AGGRESSIVE | ACT_STAY_AREA)
    elif change == "special":
        policy.source_world.mobile_specials[100] = ("spec_poison",)
    elif change == "single":
        policy.source_world.mob_resets = policy.source_world.mob_resets[:1]
    elif change == "unknown_object":
        policy.source_world.objects.clear()
    elif change == "weapon":
        policy.source_world.objects[200] = replace(policy.source_world.objects[200], item_type=5)
    elif change == "required_item":
        policy.fastwalk_where_target_template = replace(target, required_items=("a ring",))
    elif change == "protected":
        policy.fastwalk_where_target_template = replace(target, require_sanctuary=True)
    elif change == "wrong_identity":
        policy.fastwalk_where_target_template = replace(target, source_mobile_vnum=999)
    elif change == "no_sighting":
        policy.fastwalk_source_below_band_sightings.clear()
        policy.fastwalk_below_band_sightings.clear()
    elif change == "loss":
        state.xp_loss_observed = True
    elif change == "combat":
        state.in_combat = True
    elif change == "health":
        state.hp = 1
    elif change == "hunger":
        policy.needs_food = True
    elif change == "abort":
        policy.fastwalk_abort_reason = "route hazard"
    elif change == "runtime":
        policy.runtime_boundary_requested = True
    elif change == "kill_limit":
        policy.fastwalk_kill_limit = 0
    elif change == "locator_limit":
        policy.fastwalk_where_relocation_attempts = 8
    elif change == "asleep":
        state.position = 4
    elif change == "wrong_room":
        state.room_vnum = "202"
    elif change == "unknown_vitals":
        state.max_hp = None
    assert policy._fastwalk_where_relocation_decision(state) is None


def test_population_locator_never_rechecks_known_below_band_room_when_graph_is_exhausted():
    policy, state = population_locator_case()
    policy.fastwalk_where_locator_stop = replace(
        policy.fastwalk_where_locator_stop,
        where_relocation_routes=(("201", "hall", ()),),
    )
    policy.fastwalk_where_relocation_result_ready = True
    policy.fastwalk_where_locations = ("hall",)
    assert policy._fastwalk_where_relocation_decision(state) is None
    assert policy.fastwalk_where_relocation_closed


def test_population_locator_keeps_same_visit_empty_room_receipts_without_reopening_them():
    policy, state = population_locator_case()
    policy.fastwalk_where_relocation_result_ready = True
    policy.fastwalk_where_locations = ("hall",)
    policy.fastwalk_where_decisions = [{
        "room_vnum": "202", "source_mobile_vnum": 100, "target": "clan member",
    }]
    assert policy._fastwalk_where_relocation_decision(state) is None
    assert policy.fastwalk_where_relocation_closed


def empty_room_after_weak_member_case():
    policy, state = population_locator_case()
    policy.source_world.rooms[202] = replace(
        policy.source_world.rooms[202],
        exits={"west": ExitSource("west", 201, 0, -1), "east": ExitSource("east", 203, 0, -1)},
    )
    policy.source_world.rooms[203] = RoomSource(
        203, "hall", "test.are", exits={"west": ExitSource("west", 202, 0, -1)},
    )
    policy.source_world.mob_resets = [
        MobReset(100, room, 3, (200,), ((1, 200),)) for room in (201, 202, 203)
    ]
    locator = replace(
        policy.fastwalk_where_locator_stop,
        where_location_routes=(("hall", ("201", "202", "203")),),
        where_relocation_routes=(("202", "hall", ("201",)), ("202", "hall", ("203",))),
    )
    target = replace(policy.fastwalk_where_target_template, route_vnums=("202",))
    policy.fastwalk_where_locator_stop = locator
    policy.fastwalk_hunt_stops = (locator, target)
    policy.current_room = state.room_vnum = "202"
    state.exits = {"west": "201", "east": "203"}
    policy.fastwalk_target_absent = True
    policy.fastwalk_where_decisions = [{
        "room_vnum": "201", "source_mobile_vnum": 100, "target": "clan member",
    }]
    return policy, state


def test_empty_room_after_weak_member_continues_same_bounded_population_search():
    policy, state = empty_room_after_weak_member_case()
    decision = policy._fastwalk_hunt_plan_decision(state)
    assert decision.command == "where clan"
    assert policy.fastwalk_hunt_stop_index == 1
    assert policy.fastwalk_where_relocation_attempts == 1
    assert policy.fastwalk_consider_outcomes == {"clan member": False}
    policy.fastwalk_where_relocation_result_ready = True
    policy.fastwalk_where_locations = ("hall",)
    policy.fastwalk_locator_target_present_observed = True
    decision = policy._fastwalk_where_relocation_decision(state)
    assert decision.command == "east"
    assert policy.fastwalk_hunt_stops[-1].route_vnums == ("203",)
    assert policy.consider_viable is None
    assert policy.fastwalk_source_below_band_sightings


@pytest.mark.parametrize("change", [
    "no_live_weak_receipt", "other_policy", "other_target", "no_absence", "not_looked",
    "not_skipped", "crowded", "mismatched_target", "unattackable", "loss", "limit",
])
def test_empty_room_continuation_requires_same_visit_evidence_and_keeps_all_stops(change):
    policy, state = empty_room_after_weak_member_case()
    if change == "no_live_weak_receipt":
        policy.fastwalk_source_below_band_sightings.clear()
    elif change == "other_policy":
        policy.fastwalk_source_below_band_sightings = {("other", "201", "clan member")}
    elif change == "other_target":
        policy.fastwalk_source_below_band_sightings = {
            (policy.fastwalk_where_target_template.source_policy_id, "201", "other target"),
        }
    elif change == "no_absence":
        policy.fastwalk_target_absent = False
    elif change == "not_looked":
        policy.fastwalk_hunt_looked = False
    elif change == "not_skipped":
        policy.fastwalk_hunt_stop_skipped = False
    elif change == "crowded":
        policy.fastwalk_crowded = True
    elif change == "mismatched_target":
        policy.fastwalk_target_vnum_mismatch = 999
    elif change == "unattackable":
        policy.fastwalk_unattackable_target = "clan member"
    elif change == "loss":
        state.xp_loss_observed = True
    else:
        policy.fastwalk_where_relocation_attempts = 8
    assert policy._fastwalk_where_relocation_decision(state) is None


def productive_population_case():
    policy, state = population_locator_case()
    policy.fastwalk_below_band_targets.clear()
    policy.fastwalk_below_band_sightings.clear()
    policy.fastwalk_source_below_band_sightings.clear()
    policy.fastwalk_consider_outcomes = {"clan member": True}
    policy.completed_kills = [{
        "mob_name": "a clan member", "source_mobile_vnum": 100,
        "source_policy_id": policy.fastwalk_where_target_template.source_policy_id,
        "xp_gained": 1500,
    }]
    policy.fastwalk_hunt_stop_index = len(policy.fastwalk_hunt_stops)
    policy.fastwalk_target_present_observed = False
    policy.fastwalk_locator_target_present_observed = False
    return policy, state


def test_useful_population_kill_can_start_locator_after_an_outbound_interception():
    policy, state = productive_population_case()
    decision = policy._fastwalk_where_relocation_decision(state)
    assert decision.command == "where clan"
    assert policy.fastwalk_where_relocation_attempts == 1
    assert not policy.fastwalk_locator_target_present_observed


def test_population_post_kill_route_retains_live_combat_probes_and_separate_health_floors():
    policy, state = productive_population_case()
    policy.fastwalk_where_relocation_result_ready = True
    policy.fastwalk_locator_target_present_observed = True
    policy.fastwalk_where_locations = ("hall",)
    policy.fastwalk_where_decisions = [{"source_mobile_vnum": 100, "room_vnum": "201"}]
    decision = policy._fastwalk_where_relocation_decision(state)
    assert decision.command == "east"
    stop = policy.fastwalk_hunt_stops[-1]
    assert stop.allow_unprotected_hp_fuzz_probe
    assert stop.source_loot_object_vnums == (200,)
    assert stop.minimum_health_ratio == policy._plain_population_continuation_floor(state, stop)
    assert stop.minimum_combat_health_ratio == policy.fastwalk_where_target_template.minimum_combat_health_ratio
    assert stop.require_isolated and stop.maximum_target_count == 1


def test_productive_population_keeps_weak_instance_evidence_and_searches_other_rooms():
    policy, state = productive_population_case()
    policy_id = policy.fastwalk_where_target_template.source_policy_id
    weak_sighting = (policy_id, "203", "clan member")
    policy.fastwalk_below_band_targets.add("clan member")
    policy.fastwalk_source_below_band_sightings.add(weak_sighting)
    policy.fastwalk_where_locator_stop = replace(
        policy.fastwalk_where_locator_stop,
        where_relocation_routes=(
            ("201", "hall", ("203",)),
            ("201", "hall", ("202",)),
        ),
    )
    policy.fastwalk_where_relocation_result_ready = True
    policy.fastwalk_locator_target_present_observed = True
    policy.fastwalk_where_locations = ("hall",)
    policy.fastwalk_where_decisions = [{"source_mobile_vnum": 100, "room_vnum": "201"}]
    decision = policy._fastwalk_where_relocation_decision(state)
    assert decision.command == "east"
    assert policy.fastwalk_hunt_stops[-1].route_vnums == ("202",)
    assert weak_sighting in policy.fastwalk_source_below_band_sightings
    assert policy.consider_viable is None


def test_weak_individual_after_useful_kill_retains_the_continuation_entry_floor():
    policy, state = productive_population_case()
    target = replace(policy.fastwalk_where_target_template, minimum_health_ratio=.85)
    policy.fastwalk_where_target_template = target
    policy.fastwalk_hunt_stops = (policy.fastwalk_hunt_stops[0], target)
    policy.fastwalk_hunt_stop_index = 1
    policy.fastwalk_source_below_band_sightings.add((target.source_policy_id, "201", "clan member"))
    policy.fastwalk_below_band_targets.add("clan member")
    policy.fastwalk_consider_outcomes["clan member"] = False
    policy.fastwalk_target_present_observed = True
    state.hp = 560
    assert state.hp / state.max_hp < target.minimum_health_ratio
    assert policy._below_band_population_locator_allowed(state)
    policy.fastwalk_where_relocation_result_ready = True
    policy.fastwalk_locator_target_present_observed = True
    policy.fastwalk_where_locations = ("hall",)
    decision = policy._fastwalk_where_relocation_decision(state)
    assert decision.command == "east"
    assert policy.fastwalk_hunt_stops[-1].minimum_health_ratio == policy._plain_population_continuation_floor(state, target)
    assert policy.consider_viable is None


@pytest.mark.parametrize("change", ["no_receipt", "other_policy", "other_target", "negative_consider"])
def test_productive_population_does_not_ignore_unscoped_or_latest_negative_consider(change):
    policy, state = productive_population_case()
    policy_id = policy.fastwalk_where_target_template.source_policy_id
    policy.fastwalk_below_band_targets.add("clan member")
    if change == "other_target":
        policy.fastwalk_below_band_targets.add("a stranger")
    if change != "no_receipt":
        policy.fastwalk_source_below_band_sightings.add((
            "different-policy" if change == "other_policy" else policy_id,
            "203", "clan member",
        ))
    if change == "negative_consider":
        policy.fastwalk_consider_outcomes["clan member"] = False
    assert not policy._post_kill_locator_allowed(
        state, policy.fastwalk_where_locator_stop, policy.fastwalk_where_target_template,
    )


@pytest.mark.parametrize("change", [
    "low_hp", "unknown_hp", "unknown_position", "asleep", "unknown_damage", "damage_bonus",
    "incidental_xp", "unknown_loot", "required_loot", "sanctuary", "special", "loss",
    "registered_peak", "registered_critical",
])
def test_population_post_kill_lookup_preserves_source_health_and_objective_gates(change):
    policy, state = productive_population_case()
    target = policy.fastwalk_where_target_template
    if change == "low_hp":
        state.hp = 100
    elif change == "unknown_hp":
        state.hp = None
    elif change == "unknown_position":
        state.position = None
    elif change == "asleep":
        state.position = 4
    elif change == "unknown_damage":
        policy.source_world.mobiles[100] = replace(policy.source_world.mobiles[100], damage_modifier=None)
    elif change == "damage_bonus":
        policy.source_world.mobiles[100] = replace(policy.source_world.mobiles[100], damage_modifier=200)
    elif change == "incidental_xp":
        policy.completed_kills[0]["xp_gained"] = state.level * 10
    elif change == "unknown_loot":
        policy.source_world.objects.clear()
    elif change == "required_loot":
        target = replace(target, required_items=("a ring",))
    elif change == "sanctuary":
        target = replace(target, require_sanctuary=True)
    elif change == "special":
        policy.source_world.mobile_specials[100] = ("spec_poison",)
    elif change == "loss":
        state.xp_loss_observed = True
    elif change == "registered_peak":
        target = replace(target, source_peak_round_damage=state.max_hp)
    elif change == "registered_critical":
        target = replace(target, source_critical_hit_damage=state.max_hp * 2)
    assert not policy._post_kill_locator_allowed(state, policy.fastwalk_where_locator_stop, target)
