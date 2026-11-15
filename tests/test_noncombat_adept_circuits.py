from dataclasses import replace

import pytest

import dd4tester.campaign as campaign
from dd4tester.hunt_candidates import (
    ACT_SENTINEL, ExitSource, HuntCandidate, MobileSource, MobReset,
    RoomSource, WorldSource,
)


def circuit_world():
    world = WorldSource(
        mobiles={i: MobileSource(i, f"adept{i}", f"the adept {i}", 20,
                                ACT_SENTINEL, 0, "test.are") for i in (1, 2)},
        rooms={
            601: RoomSource(601, "First chamber", "test.are",
                           exits={"east": ExitSource("east", 602, 0, -1)}),
            602: RoomSource(602, "Second chamber", "test.are",
                           exits={"west": ExitSource("west", 601, 0, -1)}),
        },
        mob_resets=[MobReset(1, 601, 1), MobReset(2, 602, 1)],
        mobile_specials={1: ("spec_cast_adept",), 2: ("spec_cast_adept",)},
    )
    candidates = tuple(HuntCandidate(
        status="caution", score=100, area_file="test.are", mobile_vnum=i,
        target=f"the adept {i}", target_keyword=f"adept{i}", level=20,
        room_vnum=600+i, room_name=f"Chamber {i}", route=(),
        source_spawn_limit=1, room_spawn_count=1, boot_kills=0,
        loot=(), source_value=0, contained_coins=0, hazards=(),
        specials=("spec_cast_adept",), estimated_level_range=(18, 22),
    ) for i in (1, 2))
    state = {"level": 22, "world_boot_id": "boot", "hp": 1000, "max_hp": 1000,
             "move": 500, "max_move": 500, "affects": []}
    return world, candidates, state


@pytest.mark.parametrize("declared,actual,allowed", [
    ((), (), True), (("spec_cast_adept",), ("spec_cast_adept",), True),
    (("spec_cast_adept",), (), False), ((), ("spec_cast_adept",), False),
    (("spec_cast_adept", "spec_cast_psionicist"), ("spec_cast_adept", "spec_cast_psionicist"), False),
    (("spec_poison",), ("spec_poison",), False),
    (("unknown",), ("unknown",), False),
])
def test_circuit_noncombat_exception_is_exact_and_source_matched(declared, actual, allowed):
    world, candidates, _ = circuit_world()
    world.mobile_specials[1] = actual
    assert campaign._source_ranked_circuit_noncombat_specials_allowed(
        replace(candidates[0], specials=declared), world,
    ) is allowed


@pytest.mark.parametrize("blocker", [None, "mixed-special", "source-mismatch", "exact-loss"])
def test_adept_pair_uses_existing_circuit_without_dangerous_special_or_loss_bypass(blocker):
    world, (primary, secondary), state = circuit_world()
    if blocker == "mixed-special":
        secondary = replace(secondary, specials=("spec_cast_adept", "spec_cast_psionicist"))
        world.mobile_specials[2] = secondary.specials
    elif blocker == "source-mismatch":
        world.mobile_specials[2] = ()
    elif blocker == "exact-loss":
        state["campaign_source_ranked_xp_loss_policies"] = [{
            "policy_id": campaign._source_ranked_policy_id(secondary, character_level=22),
            "level": 22, "boot_id": "boot", "loss_count": 1,
            "exact_stop_loss": True,
        }]
    extras = campaign._source_ranked_area_circuit_candidates(
        primary, (primary, secondary), world, state, character_level=22,
    )
    assert extras == ((secondary,) if blocker is None else ())
    if blocker is None:
        stops = campaign._source_ranked_circuit_hunt_stops(
            primary, extras, world, character_level=22, state=state,
        )
        target_stops = [stop for stop in stops if stop.target]
        assert [stop.source_mobile_vnum for stop in target_stops] == [1, 2]
        assert target_stops[1].minimum_health_ratio <= campaign._SOURCE_RANKED_CONTINUATION_HEALTH_RATIO
        assert target_stops[1].source_policy_id == campaign._source_ranked_policy_id(secondary, character_level=22)


@pytest.mark.parametrize("prior_room", [602, 999])
def test_circuit_follow_on_cannot_borrow_primary_retry_even_if_selector_admits(monkeypatch, prior_room):
    world, (primary, secondary), state = circuit_world()
    state["combat_pouch_potions"] = {"purple": 1}
    state["campaign_source_ranked_xp_loss_policies"] = [{
        "policy_id": f"source-ranked-hunt-test-2-{prior_room}-22",
        "level": 22, "boot_id": "boot", "loss_count": 1, "exact_stop_loss": True,
    }]
    monkeypatch.setattr(campaign, "_select_source_ranked_hunt_candidate",
                        lambda candidates, *_a, **_kw: tuple(candidates)[0])
    assert campaign._source_ranked_area_circuit_candidates(
        primary, (primary, secondary), world, state, character_level=22,
    ) == ()
    stops = campaign._source_ranked_circuit_hunt_stops(
        primary, (secondary,), world, character_level=22, state=state,
    )
    assert [stop.source_mobile_vnum for stop in stops if stop.target] == [1]
