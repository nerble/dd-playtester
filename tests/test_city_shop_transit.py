import asyncio
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from dd4tester.character import CharacterSpec
from dd4tester.city_travel import (
    CITY_TRANSIT_KEY, CityShopTransit, bounded_city_shop_transit_available,
)
from dd4tester.hunt_candidates import load_world_source
from dd4tester.starter import StarterPolicy
from dd4tester.state import CharacterState


@pytest.fixture(scope="module")
def world():
    return load_world_source(Path("runs/dd4-source/server/area"), include_all_areas=True)


def state():
    return CharacterState(
        level=8, hp=113, max_hp=113, mana=324, max_mana=324,
        move=220, max_move=220, room_vnum="3054", room_name="By the Temple Altar",
        position=7, area="Midgaard", hunger=30, thirst=30,
    )


def enemy(**changes):
    return {"isnpc": "3064", "name": "the drunk", "level": "2",
            "hp": "18", "maxhp": "18", **changes}


def policy(world, **changes):
    result = StarterPolicy(
        CharacterSpec.from_mapping({
            "name": "Testmage", "race": "human", "gender": "female", "class": "mage",
        }), "fixture-password", magic_shop_research=True, magic_shop_buy_fly=True,
        source_world=world, allow_bounded_city_shop_transit=True,
        title_configured=True, description_configured=True, **changes,
    )
    result.in_world = result.prompt_ready = True
    result.world_boot_id = "boot"
    return result


def test_source_accepts_the_current_character_without_changing_boundaries(world):
    assert bounded_city_shop_transit_available(world, state().to_dict())
    assert not bounded_city_shop_transit_available(None, state().to_dict())
    assert not bounded_city_shop_transit_available(world, replace(state(), level=7).to_dict())
    assert not bounded_city_shop_transit_available(world, replace(state(), max_hp=30).to_dict())


def test_shop_preflight_admits_source_bounded_transit_without_a_cast(world):
    bot = policy(world)
    decision = bot.next_decision(state())
    assert decision.command == "south"
    assert bot.city_shop_transit.status == "admitted"
    assert not bot.magic_shop_invisibility_attempted


@pytest.mark.parametrize("changes", [{"hp": 70}, {"position": 4}, {"level": 7}])
def test_departure_retains_live_readiness_gates(world, changes):
    bot = policy(world)
    bot._midgaard_city_shop_preflight_decision(replace(state(), **changes), operation="shop")
    assert bot.city_shop_transit.status == "idle"


def test_one_verified_interruption_can_finish_and_cannot_be_reused(world):
    transit = CityShopTransit()
    transit.admit()
    here = replace(state(), room_vnum="3014").to_dict()
    assert transit.combat_allowed(world, here, [enemy()], now=0, nutrition_ready=True)
    assert transit.combat_allowed(world, here, [enemy(hp="5")], now=10, nutrition_ready=True)
    transit.finish_combat()
    assert not transit.combat_allowed(world, here, [enemy()], now=11, nutrition_ready=True)
    assert transit.status == "aborted"


@pytest.mark.parametrize("boundary", [
    "crowd", "wrong-id", "missing-id", "too-high", "missing-level", "large-hp",
    "missing-hp", "low-health", "nutrition", "timeout", "runtime", "wrong-room",
])
def test_interruption_enforces_live_bounds(world, boundary):
    transit = CityShopTransit()
    transit.admit()
    here = replace(state(), room_vnum="3014").to_dict()
    assert transit.combat_allowed(world, here, [enemy()], now=0, nutrition_ready=True)
    enemies = [enemy()]
    if boundary == "crowd":
        enemies.append(enemy())
    elif boundary == "wrong-id":
        enemies = [enemy(isnpc="999")]
    elif boundary == "missing-id":
        enemies = [enemy(isnpc=None)]
    elif boundary == "too-high":
        enemies = [enemy(level="5")]
    elif boundary == "missing-level":
        enemies = [enemy(level=None)]
    elif boundary == "large-hp":
        enemies = [enemy(maxhp="49")]
    elif boundary == "missing-hp":
        enemies = [enemy(maxhp=None)]
    elif boundary == "low-health":
        here["hp"] = 70
    elif boundary == "wrong-room":
        here["room_vnum"] = "4028"
    assert not transit.combat_allowed(
        world, here, enemies, now=60 if boundary == "timeout" else 10,
        nutrition_ready=boundary != "nutrition", runtime_boundary=boundary == "runtime",
    )
    assert transit.status == "aborted" and transit.reason


def test_live_policy_uses_bounded_combat_before_the_utility_flee(world):
    bot = policy(world)
    bot.next_decision(state())
    bot.combat_active = True
    bot.active_target = "the drunk"
    bot.active_target_level = 2
    combat = replace(state(), room_vnum="3014", in_combat=True, position=6, enemies=[[enemy()]])
    decision = bot.next_decision(combat)
    assert decision is None or decision.command != "flee"
    assert bot.city_shop_transit.status == "fighting"
    bot.prompt_ready = True
    decision = bot.next_decision(replace(combat, hp=70))
    assert decision.command == "flee"
    assert bot.return_home and bot.utility_emergency_recall_pending
    assert bot.magic_shop_route_blocked_by_drunk


@pytest.mark.parametrize("changed_scope", [False, True])
def test_failed_transit_stays_excluded_until_its_level_or_reboot_changes(world, changed_scope):
    previous = {**state().to_dict(), "world_boot_id": "boot", CITY_TRANSIT_KEY: {
        "status": "aborted", "level": 8, "boot_id": "boot",
    }}
    if changed_scope:
        previous["world_boot_id"] = "new-boot"
    original = deepcopy(previous)
    assert bounded_city_shop_transit_available(world, previous) is changed_scope
    assert previous == original


@pytest.mark.parametrize("aborted", [False, True])
def test_public_flight_adapter_passes_only_current_source_permission(world, monkeypatch, aborted):
    from dd4tester import campaign
    captured = {}

    class Runner:
        def __init__(self, spec, path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return "finished"

    monkeypatch.setattr(campaign, "StarterBotRunner", Runner)
    bot = policy(world)
    current = {**state().to_dict(), "world_boot_id": "boot"}
    if aborted:
        current[CITY_TRANSIT_KEY] = {"status": "aborted", "level": 8, "boot_id": "boot"}
    asyncio.run(campaign._run_policy_segment(
        bot.spec, Path("unused.yaml"), campaign._BUY_FLIGHT_POLICY,
        current_state=current, source_world=world,
    ))
    assert bool(captured.get("allow_bounded_city_shop_transit")) is not aborted


def test_transit_checkpoint_never_contains_a_resumable_timer():
    transit = CityShopTransit(status="fighting", started_at=100.0)
    proof = transit.evidence(level=8, boot_id="boot")[CITY_TRANSIT_KEY]
    assert "started_at" not in proof
    assert CityShopTransit().status == "idle"


@pytest.mark.parametrize("prior_boot,current_boot", [(None, "boot"), ("boot", None), (None, None)])
def test_missing_reboot_evidence_cannot_reopen_an_aborted_transit(world, prior_boot, current_boot):
    current = {**state().to_dict(), "world_boot_id": current_boot, CITY_TRANSIT_KEY: {
        "status": "aborted", "level": 8, "boot_id": prior_boot,
    }}
    assert not bounded_city_shop_transit_available(world, current)


@pytest.mark.parametrize("observed_boot", [None, "new-boot"])
def test_short_city_segment_binds_only_missing_reboot_evidence(world, observed_boot):
    from dd4tester import campaign
    previous = {**state().to_dict(), "world_boot_id": "boot"}
    current = {**state().to_dict(), "world_boot_id": observed_boot, CITY_TRANSIT_KEY: {
        "status": "aborted", "level": 8, "boot_id": observed_boot,
    }}
    merged = campaign._campaign_segment_end_state(previous, current, execution="buy-flight")
    assert merged[CITY_TRANSIT_KEY]["boot_id"] == (observed_boot or "boot")
    assert not bounded_city_shop_transit_available(world, merged)
    assert current[CITY_TRANSIT_KEY]["boot_id"] == observed_boot
