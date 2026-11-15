from dataclasses import replace

import pytest

from dd4tester.character import CharacterSpec
from dd4tester.equipment import STANCE_COMBAT, STANCE_RECOVERY
from dd4tester.hunt_candidates import MobReset, MobileSource, RoomSource, WorldSource
from dd4tester.starter import FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


def _policy():
    spec = CharacterSpec.from_mapping({
        "name": "Searcher", "race": "human", "gender": "female", "class": "mage",
    })
    locator = FieldHuntStop((), "carrier", where_target="carrier")
    current = FieldHuntStop(
        (), "carrier", source_mobile_vnum=100, exact_target=True,
        allow_below_band_for_required_loot=True, required_items=("potion",),
        route_vnums=("200",),
    )
    following = replace(current, route_vnums=("201",))
    policy = StarterPolicy(
        spec, "not-a-real-password", fastwalk_hunt_stops=(locator, current, following),
        source_mobile_vnums_by_target_room={"orc": {"200": (101,)}},
        source_mobile_level_ranges_by_vnum={101: (8, 12)},
    )
    policy.fastwalk_where_locator_stop = locator
    policy.fastwalk_hunt_stop_index = 1
    policy.current_room = "200"
    policy.room_target_counts["200"] = {"orc": 1}
    return policy, current, CharacterState(level=46, room_vnum="200")


def test_absent_carrier_keeps_bounded_search_without_inventing_presence():
    policy, stop, state = _policy()
    decision = policy._continue_required_loot_endpoint_sweep(
        state, "carrier", stop, (("orc", 1, ("101",)),),
    )
    assert decision.command == "look"
    assert policy.fastwalk_hunt_stop_skipped
    assert not policy.fastwalk_returning
    assert not policy.fastwalk_room_target_present_observed
    assert not policy.fastwalk_target_present_observed


@pytest.mark.parametrize("blocker", ["unknown", "level", "combat", "no-next", "different-target"])
def test_absent_carrier_search_retains_existing_boundaries(blocker):
    policy, stop, state = _policy()
    if blocker == "unknown":
        policy.source_mobile_vnums_by_target_room.clear()
    elif blocker == "level":
        policy.source_mobile_level_ranges_by_vnum[101] = (43, 47)
    elif blocker == "combat":
        policy.combat_active = True
    elif blocker == "no-next":
        policy.fastwalk_hunt_stops = policy.fastwalk_hunt_stops[:2]
    else:
        policy.fastwalk_hunt_stops = (*policy.fastwalk_hunt_stops[:2], replace(stop, target="other"))
    assert policy._continue_required_loot_endpoint_sweep(
        state, "carrier", stop, (("orc", 1, ("101",)),),
    ) is None


def test_search_uses_clear_alternative_after_shortest_registered_path_has_special():
    policy, _, state = _policy()
    policy.source_world = WorldSource(
        rooms={vnum: RoomSource(vnum, "maze", "maze.are") for vnum in (200, 201, 202, 203)},
        mobiles={101: MobileSource(101, "snake", "a snake", 10, 2, 0, "maze.are")},
        mob_resets=[MobReset(101, 201, 1)],
        mobile_specials={101: ("spec_poison",)},
    )
    policy.fastwalk_where_decisions = [{}]
    unsafe = (1, "maze", ("201",), "200")
    clear = (2, "maze", ("202", "203"), "200")
    assert policy._required_loot_relocation_choices(state, [unsafe, clear]) == [clear]
    assert policy.fastwalk_where_decisions[-1]["rejected_search_routes"][0]["route_vnums"] == ["201"]


@pytest.mark.parametrize("path", [("999",), tuple("201" for _ in range(33)), ()])
def test_search_rejects_missing_or_unbounded_paths(path):
    policy, _, state = _policy()
    policy.source_world = WorldSource(rooms={200: RoomSource(200, "maze", "maze.are")})
    assert policy._required_loot_relocation_choices(state, [(len(path), "maze", path, "200")]) == []


def test_visibility_failure_checkpoint_retains_quote_not_a_successful_effect():
    policy, _, state = _policy()
    state.currencies = {"copper": 19}
    policy.magic_shop_buy_see_invisible = True
    policy.magic_shop_see_invisible_step = 2
    policy.magic_shop_see_invisible_price = 248
    policy.magic_shop_see_invisible_stock = 11
    policy.magic_shop_see_invisible_purchase_failed = True
    policy.world_boot_id = "boot-1"
    policy.magic_shop_see_invisible_price_boot_id = "boot-1"
    record = policy.visibility_preparation_checkpoint(state)["campaign_visibility_preparation"]
    assert record["funding_required"] is True
    assert record["verified"] is False
    assert record["price"] == 248
    policy.magic_shop_see_invisible_stock = None
    assert policy.visibility_preparation_checkpoint(state)["campaign_visibility_preparation"]["funding_required"] is False


def test_failed_flight_purchase_leaves_shop_without_reentering():
    policy, _, state = _policy()
    policy.magic_shop_research = True
    policy.magic_shop_buy_fly = True
    policy.magic_shop_purchase_failed = True
    policy._recovery_session.flight_purchase_failure_reason = "capacity"
    state.room_vnum = "3033"
    state.room_name = "The Magic Shop"
    leave = policy._magic_shop_research_decision(state)
    assert leave.command == "south"
    assert policy.magic_shop_step >= 1
    state.room_vnum = "3012"
    state.room_name = "Main Street"
    returning = policy._magic_shop_research_decision(state)
    assert returning.command == "east"
    assert "return" in returning.reason


@pytest.mark.parametrize("blocker", [None, "wounded", "low-mana", "waiting", "unknown-room"])
def test_city_potion_walk_preserves_combat_gear_for_movement_only(blocker):
    policy, _, state = _policy()
    policy.magic_shop_research = True
    policy.gear_applied_stance = STANCE_COMBAT
    state.room_vnum = "3014"
    state.room_flags = ["safe"]
    state.hp = state.max_hp = state.mana = state.max_mana = state.max_move = 100
    state.move = 10
    if blocker == "wounded":
        state.hp = 50
    elif blocker == "low-mana":
        state.mana = 20
    elif blocker == "waiting":
        policy.waiting_for_heal = True
    elif blocker == "unknown-room":
        state.room_vnum = "999"
    assert policy._desired_gear_stance(state) == (STANCE_COMBAT if blocker is None else STANCE_RECOVERY)


def test_dynamic_flight_renewal_requires_a_fresh_carrying_check():
    policy, _, state = _policy()
    state.room_vnum = "3054"
    state.affects = []
    policy.fastwalk_require_flight = True
    policy.fastwalk_flight_reacquisition_allowed = True
    policy.fastwalk_required_loot_capacity_preflight_complete = True
    policy._recovery_session.carrying_capacity.initial_count = 20
    policy._recovery_session.carrying_capacity.limit = 0
    decision = policy._fastwalk_flight_requirement_decision(state)
    assert decision.command == "affects"
    assert not policy.fastwalk_required_loot_capacity_preflight_complete
    assert policy._recovery_session.carrying_capacity.initial_count is None
    assert policy._recovery_session.carrying_capacity.limit is None
