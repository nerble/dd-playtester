import pytest

from dd4tester.fastwalks import expand_fastwalk, route_named, routes_for_level


def test_expand_fastwalk_expands_repeated_directions_and_commands() -> None:
    assert expand_fastwalk("2s3e2se;open east;e") == (
        "south",
        "south",
        "east",
        "east",
        "east",
        "south",
        "south",
        "east",
        "open east",
        "east",
    )


@pytest.mark.parametrize("notation", ["0s", "2", "2q", "s;;e", "say hello"])
def test_expand_fastwalk_rejects_malformed_segments(notation: str) -> None:
    with pytest.raises(ValueError):
        expand_fastwalk(notation)


def test_official_routes_are_searchable_by_level_and_name() -> None:
    level_six_names = {route.name for route in routes_for_level(6)}

    assert {"ambush", "moria", "fleshmonger"}.issubset(level_six_names)
    assert route_named("Dragon-Cult").commands == ("south", "south", "south", "west", "north")


def test_route_named_includes_live_verified_map_routes() -> None:
    route = route_named("Miden'nir")

    assert route.minimum_level == 5
    assert route.maximum_level == 15
    assert route.commands == (
        "south",
        "south",
        "east",
        "east",
        "east",
        "east",
        "east",
    )

