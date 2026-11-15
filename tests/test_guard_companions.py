from dataclasses import replace
import time

import pytest

from dd4tester.hunt_candidates import (
    ACT_SENTINEL, AFF_HIDE, ITEM_ARMOR, ITEM_POTION, ITEM_WEAPON, MobReset, MobileSource,
    ObjectSource, WorldSource,
)
from dd4tester.mobile_loadouts import bounded_low_guard_companion
from dd4tester.character import CharacterSpec
from dd4tester.state import CharacterState
from dd4tester.starter import FieldHuntStop, StarterPolicy
from dd4tester.equipment import GearCatalog
from dd4tester.fastwalks import route_named


def guard_world():
    guard = MobileSource(
        10, "guard", "a guard", 12, ACT_SENTINEL, 0, "test.are",
        room_description="A guard watches the room.",
    )
    armor = ObjectSource(20, "armor", "armor", ITEM_ARMOR, (), 0)
    return WorldSource(
        mobiles={10: guard}, objects={20: armor},
        mob_resets=[MobReset(10, 100, 1, (20,), ((5, 20),))],
        mobile_specials={10: ("spec_guard",)},
    )


def test_low_guard_companion_requires_large_source_level_gap():
    world = guard_world()
    assert bounded_low_guard_companion(world, 10, 100, 45)
    assert not bounded_low_guard_companion(world, 10, 100, 23)
    assert not bounded_low_guard_companion(world, 10, 101, 45)


def test_low_guard_companion_accepts_detrimental_restraints_not_bonuses():
    world = guard_world()
    world.objects[20] = replace(
        world.objects[20], item_type=13, values=(0, 0, 0, 0),
        wear_flags=4097, affects=((2, -3), (18, -5)),
    )
    assert bounded_low_guard_companion(world, 10, 100, 45)
    world.objects[20] = replace(world.objects[20], affects=((19, 100),))
    assert not bounded_low_guard_companion(world, 10, 100, 45)


def test_guard_contract_still_requires_allowlist_and_live_bystander_receipt():
    world = guard_world()
    stop = FieldHuntStop(
        (), "carrier", source_mobile_vnum=11, source_reset_room_vnum="100",
        required_items=("a potion",), allow_below_band_for_required_loot=True,
        allow_source_bystander_encounter=True,
        required_loot_allowed_source_bystander_vnums=(10,),
    )
    policy = StarterPolicy(
        CharacterSpec.from_mapping({"name": "Tester", "race": "human", "gender": "male", "class": "warrior"}),
        "password", source_world=world, fastwalk_hunt_stops=(stop,),
    )
    state = CharacterState(level=45, room_vnum="100")
    guard = world.mobiles[10]
    assert policy._required_loot_source_bystander_is_allowlisted(guard, state)
    assert not policy._live_bystander_below_assistance_band("a guard", state)
    policy.fastwalk_hunt_stops = (replace(stop, required_loot_allowed_source_bystander_vnums=()),)
    assert not policy._required_loot_source_bystander_is_allowlisted(guard, state)


@pytest.mark.parametrize("change", ["weapon", "unknown", "special", "population", "damage", "offensive_gear"])
def test_low_guard_companion_keeps_source_hazards_closed(change):
    world = guard_world()
    if change == "weapon":
        world.objects[20] = replace(world.objects[20], item_type=ITEM_WEAPON)
    elif change == "unknown":
        world.objects.clear()
    elif change == "special":
        world.mobile_specials[10] = ("spec_guard", "spec_poison")
    elif change == "population":
        world.mob_resets.append(MobReset(10, 101, 1, ()))
    elif change == "damage":
        world.mobiles[10] = replace(world.mobiles[10], damage_modifier=100)
    else:
        world.objects[20] = replace(world.objects[20], affects=((19, 100),))
    assert not bounded_low_guard_companion(world, 10, 100, 45)


def test_verified_detection_potion_activates_at_healer():
    potion = ObjectSource(
        4558, "potion inky black", "an inky black potion", ITEM_POTION,
        (13, 0, 0, 0), 0,
        value_strings=("13", "detect hidden", "infravision", ""),
    )
    resource = {
        "effect": "detect hidden", "spell": "detect hidden", "object_vnum": 4558,
        "object_description": "inky black potion", "command": "quaff",
        "command_keyword": "black", "mode": "potion", "consumes_object": True,
    }
    policy = StarterPolicy(
        CharacterSpec.from_mapping({"name": "Tester", "race": "human", "gender": "male", "class": "warrior"}),
        "password", gear_catalog=GearCatalog({4558: potion}),
        verified_source_resources={"detect hidden": resource}, return_home=True,
    )
    policy.in_world = True
    policy.prompt_ready = True
    state = CharacterState(
        name="Tester", level=45, hp=1000, max_hp=1000, room_vnum="3054",
        room_flags=["safe", "healing"], position=7,
        inventory=[[{"short_desc": "an inky black potion"}]],
    )
    decision = policy.next_decision(state)
    assert decision is not None
    assert decision.command == "quaff black"


@pytest.mark.parametrize("hidden,returning,expected", [
    (False, False, False), (True, False, True), (True, True, False),
])
def test_carried_detection_is_not_wasted_on_unrelated_gear_or_return(hidden, returning, expected):
    world = guard_world()
    world.mobiles[10] = replace(world.mobiles[10], affected_flags=AFF_HIDE if hidden else 0)
    policy = StarterPolicy(
        CharacterSpec.from_mapping({"name": "Tester", "race": "human", "gender": "male", "class": "warrior"}),
        "password", source_world=world, fastwalk_route=route_named("moria"),
        fastwalk_hunt_stops=(FieldHuntStop((), "guard", source_mobile_vnum=10),),
    )
    policy.fastwalk_returning = returning
    assert policy._needs_carried_detection_preparation() is expected
    policy.fastwalk_hunt_stop_index = 1
    assert not policy._needs_carried_detection_preparation()


def guard_handoff():
    world = guard_world()
    world.mobiles[11] = MobileSource(
        11, "carrier", "the carrier", 13, ACT_SENTINEL, -1000, "test.are",
    )
    stop = FieldHuntStop(
        (), "carrier", source_mobile_vnum=11, source_reset_room_vnum="100",
        required_items=("a potion",), allow_below_band_for_required_loot=True,
        allow_source_bystander_encounter=True,
        required_loot_allowed_source_bystander_vnums=(10,),
    )
    policy = StarterPolicy(
        CharacterSpec.from_mapping({"name": "Tester", "race": "human", "gender": "male", "class": "warrior"}),
        "password", source_world=world, fastwalk_route=route_named("moria"),
        fastwalk_hunt_stops=(stop,), fastwalk_attack_target="carrier",
    )
    policy.combat_active = True
    policy.current_room = "100"
    policy.fastwalk_attack_started = True
    policy.fastwalk_hunt_stop_killed = True
    policy.fastwalk_last_kill_target = "the carrier"
    policy.active_target = "the carrier"
    policy.completed_kills = [{"mob_name": "the carrier"}]
    policy.fastwalk_target_vnum_mismatch = {"expected": 11, "actual": 10}
    policy.fastwalk_abort_reason = "live mobile VNUM 10 did not match source mobile VNUM 11"
    policy.fastwalk_emergency_recall_pending = True
    policy.unapproved_field_attacker = "a guard"
    policy.room_target_selectors["100"] = {"a guard": ["#42"]}
    policy.room_target_selector_descriptions["100"] = {"#42": "A guard watches the room."}
    policy.bystander_consider_results["#42"] = {
        "room_vnum": "100", "level": 45, "selector": "#42",
        "source_mobile_vnum": 10, "boot_id": policy.world_boot_id,
        "below_assistance_band": True, "expires_at": time.monotonic() + 30,
    }
    enemy = {"name": "a guard", "isnpc": "10", "level": "12",
             "long_desc": "A guard watches the room."}
    state = CharacterState(
        level=45, hp=1000, max_hp=1000, room_vnum="100", position=6,
        enemies=[[enemy]],
    )
    return policy, state, enemy


def test_post_carrier_guard_handoff_clears_only_the_identity_abort():
    policy, state, enemy = guard_handoff()
    policy._combat_session.source_losses.append({"mobile_vnum": 77, "xp_lost": 100})
    assert policy._adopt_required_loot_guard_handoff(state, [enemy])
    assert policy.active_target == "a guard"
    assert policy.active_target_selector == "#42"
    assert policy.fastwalk_target_vnum_mismatch is None
    assert policy.fastwalk_abort_reason is None
    assert policy.unapproved_field_attacker is None
    assert not policy.fastwalk_emergency_recall_pending
    assert policy._combat_session.source_losses == [{"mobile_vnum": 77, "xp_lost": 100}]
    assert len(policy._combat_session.required_loot_guard_handoffs) == 1


@pytest.mark.parametrize("failure", [
    "no_kill", "wrong_kill", "no_receipt", "expired", "crowd", "identity",
    "wrong_level", "wrong_boot", "unknown_loadout", "dangerous_special",
    "not_fighting", "not_allowlisted",
])
def test_post_carrier_guard_handoff_preserves_closed_gates(failure):
    policy, state, enemy = guard_handoff()
    if failure == "no_kill":
        policy.fastwalk_hunt_stop_killed = False
    elif failure == "wrong_kill":
        policy.fastwalk_last_kill_target = "another carrier"
    elif failure == "no_receipt":
        policy.bystander_consider_results.clear()
    elif failure == "expired":
        policy.bystander_consider_results["#42"]["expires_at"] = 0
    elif failure == "crowd":
        state.enemies[0].append(dict(enemy))
    elif failure == "identity":
        enemy["long_desc"] = "Another guard watches the room."
    elif failure == "wrong_level":
        policy.bystander_consider_results["#42"]["level"] = 44
    elif failure == "wrong_boot":
        policy.bystander_consider_results["#42"]["boot_id"] = "old boot"
    elif failure == "unknown_loadout":
        policy.source_world.objects.clear()
    elif failure == "dangerous_special":
        policy.source_world.mobile_specials[10] = ("spec_guard", "spec_poison")
    elif failure == "not_fighting":
        state.position = 7
    else:
        policy.fastwalk_hunt_stops = (replace(
            policy.fastwalk_hunt_stops[0], required_loot_allowed_source_bystander_vnums=(),
        ),)
    assert not policy._adopt_required_loot_guard_handoff(state, [enemy])
    assert policy.fastwalk_target_vnum_mismatch == {"expected": 11, "actual": 10}
    assert policy.fastwalk_emergency_recall_pending
    assert not policy._combat_session.required_loot_guard_handoffs
