import pytest

from dd4tester.hunt_candidates import RoomSource, WorldSource
from dd4tester.water import can_breathe_underwater, source_route_requires_water_breathing


@pytest.mark.parametrize("affects,expected", [
    ([[{"name": "fly", "duration": "40"}]], False),
    ([[{"name": "breathe water", "duration": "4"}]], True),
    ([[{"name": "breathe water", "duration": "0"}]], False),
    ([[{"name": "breathe water"}]], False), (None, False),
])
def test_water_breathing_is_observed_separately_from_flight(affects, expected):
    assert can_breathe_underwater({"race": "Dwarf", "affects": affects}) is expected


@pytest.mark.parametrize("race,expected", [("Sahuagin", True), ("Grung", True),
                                          ("Human", False), (None, False)])
def test_only_explicit_source_race_exemptions_breathe_without_an_affect(race, expected):
    assert can_breathe_underwater({"race": race}) is expected


def test_underwater_ground_needs_breathing_but_river_crossing_does_not():
    world = WorldSource(rooms={1: RoomSource(1, "river", "test.are", sector_type=7),
                              2: RoomSource(2, "underwater", "test.are", sector_type=8),
                              3: RoomSource(3, "seabed", "test.are", sector_type=12)})
    assert not source_route_requires_water_breathing(world, (1,))
    assert source_route_requires_water_breathing(world, (1, 2))
    assert source_route_requires_water_breathing(world, (3,))
    assert source_route_requires_water_breathing(world, (99,))
