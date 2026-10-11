from dataclasses import replace

import pytest

from dd4tester import campaign, hunt_candidates
from dd4tester.hunt_candidates import (
    ACT_AGGRESSIVE, ACT_STAY_AREA, ExitSource, MobileSource, MobReset,
    RoomSource, SourceRouteHazardIndex, WorldSource, source_route_hazard_rejections,
)
from dd4tester.locator_paths import source_locator_path_is_safe


def source_case():
    mobile = MobileSource(100, "guard", "a guard", 32, ACT_AGGRESSIVE, 0, "test.are")
    rooms = {
        1: RoomSource(1, "origin", "test.are", {"east": ExitSource("east", 2, 0, -1)}),
        2: RoomSource(2, "border", "test.are", {"east": ExitSource("east", 3, 0, -1)}),
        3: RoomSource(3, "destination", "other.are"),
    }
    return WorldSource(mobiles={100: mobile}, rooms=rooms, mob_resets=[MobReset(100, 1, 1, ())])


@pytest.mark.parametrize("strict,invisible,combat", [
    (False, False, True), (True, False, False), (False, True, False),
])
def test_route_index_preserves_complete_hazard_verdicts(strict, invisible, combat):
    world = source_case()
    options = dict(character_level=30, require_no_combat_hazards=strict,
                   invisible=invisible, combat_at_destination=combat)
    expected = source_route_hazard_rejections(world, (3,), **options)
    if not invisible:
        assert expected
    index = SourceRouteHazardIndex(world)
    assert source_route_hazard_rejections(world, (3,), hazard_index=index, **options) == expected
    assert not source_locator_path_is_safe(world, (3,), character_level=30, hazard_index=index)


def test_route_index_reuses_one_full_world_range_without_losing_other_area_hazards(monkeypatch):
    world = source_case()
    original = hunt_candidates._wanderer_reachable_rooms
    calls = []

    def record(world, mobile, origin):
        calls.append((mobile.vnum, origin))
        return original(world, mobile, origin)

    monkeypatch.setattr(hunt_candidates, "_wanderer_reachable_rooms", record)
    index = SourceRouteHazardIndex(world)
    for room in (2, 3, 2):
        assert source_route_hazard_rejections(world, (room,), character_level=30, hazard_index=index)
    assert calls == [(100, 1)]
    assert index.reachable[(100, 1)] == frozenset((1, 2, 3))


def test_route_index_never_reuses_a_different_source_world():
    world = source_case()
    index = SourceRouteHazardIndex(world)
    with pytest.raises(ValueError, match="different source world"):
        source_route_hazard_rejections(source_case(), (3,), character_level=30, hazard_index=index)
    world.mobiles[100] = replace(world.mobiles[100], act_flags=ACT_AGGRESSIVE | ACT_STAY_AREA)
    fresh_index = SourceRouteHazardIndex(world)
    assert not source_route_hazard_rejections(world, (3,), character_level=30, hazard_index=fresh_index)


def test_noncombat_joiner_has_no_destination_range_to_search(monkeypatch):
    world = source_case()
    world.mobiles[100] = replace(world.mobiles[100], act_flags=0)
    world.mobile_specials[100] = ("spec_guard",)
    index = SourceRouteHazardIndex(world)

    def unexpected_range(*args):
        pytest.fail("combat-only joiner cannot affect a noncombat endpoint")

    monkeypatch.setattr(hunt_candidates, "_wanderer_reachable_rooms", unexpected_range)
    assert not source_route_hazard_rejections(
        world, (3,), character_level=30, combat_at_destination=False, hazard_index=index,
    )
    assert not index.reachable


@pytest.mark.parametrize("special", ["spec_guard", "spec_thief", "spec_mage"])
def test_cached_source_classification_does_not_cache_route_permissions(special):
    world = source_case()
    world.mobiles[100] = replace(world.mobiles[100], act_flags=0)
    world.mobile_specials[100] = (special,)
    index = SourceRouteHazardIndex(world)
    for level in (30, 40):
        for combat in (False, True):
            options = dict(character_level=level, combat_at_destination=combat,
                           economic_special_mobile_vnums=(100,))
            assert source_route_hazard_rejections(world, (2, 3), hazard_index=index, **options) == (
                source_route_hazard_rejections(world, (2, 3), **options)
            )


def test_hunt_preparation_timeout_precedes_candidate_or_connection_work(monkeypatch):
    ticks = iter((0.0, 61.0))
    monkeypatch.setattr(campaign.time, "monotonic", lambda: next(ticks, 61.0))
    monkeypatch.setattr(campaign, "_check_campaign_preparation_deadline", lambda: None)
    with pytest.raises(TimeoutError, match="60-second budget"):
        campaign._source_ranked_hunt_stops(None, WorldSource(), character_level=30)
