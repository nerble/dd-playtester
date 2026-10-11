from dataclasses import replace

import pytest

from dd4tester.campaign import _source_food_bakery_preferred
from dd4tester.hunt_candidates import ITEM_FOOD, ObjectSource, WorldSource


def _world() -> WorldSource:
    return WorldSource(objects={
        3009: ObjectSource(3009, "potpie pot pie", "a big pot pie", ITEM_FOOD,
                           (40, 0, 0, 0), 100),
    })


def _state() -> dict:
    return {
        "room_vnum": "3054", "level": 32, "stats": {"fame": 0},
        "world_boot_id": "boot", "currencies": {"copper": 341},
        "campaign_magic_shop_flight_price": 141,
        "campaign_magic_shop_flight_price_boot_id": "boot",
    }


def test_nourishing_bakery_preference_keeps_a_flight_selection_budget() -> None:
    state = _state()
    assert _source_food_bakery_preferred(state, source_world=_world())
    state["currencies"] = {"copper": 340}
    assert not _source_food_bakery_preferred(state, source_world=_world())


@pytest.mark.parametrize("changes", (
    {"room_vnum": "3001"}, {"dead": True}, {"in_combat": True},
    {"stats": {"fame": -1}}, {"stats": {}},
    {"campaign_city_shop_route_cooldown": 1},
    {"magic_shop_route_blocked_by_drunk": True},
    {"campaign_last_policy": "restock-provisions"},
))
def test_bakery_preference_preserves_location_reputation_and_retry_gates(changes) -> None:
    assert not _source_food_bakery_preferred({**_state(), **changes}, source_world=_world())


@pytest.mark.parametrize("changes", (
    {"values": (40, 0, 0, 1)}, {"values": ()}, {"source_cost": 0},
    {"values": (0, 0, 0, 0)}, {"keywords": "unknown meal"},
))
def test_bakery_preference_requires_current_source_food(changes) -> None:
    world = _world()
    world.objects[3009] = replace(world.objects[3009], **changes)
    assert not _source_food_bakery_preferred(_state(), source_world=world)
    assert not _source_food_bakery_preferred(_state(), source_world=None)
