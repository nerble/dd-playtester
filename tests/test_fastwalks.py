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


def test_route_named_includes_source_backed_hunt_routes() -> None:
    route = route_named("Foundry")

    assert route.minimum_level == 1
    assert route.maximum_level == 6
    assert route.recall_after_loot is True
    assert route.commands == (
        "south",
        "south",
        "west",
        "west",
        "west",
        "north",
        "north",
        "north",
        "north",
        "east",
        "down",
        "down",
        "north",
        "north",
    )

    captain = route_named("Foundry Captain")
    assert captain.minimum_level == 7
    assert captain.commands[-3:] == ("west", "open south", "south")
    assert captain.recall_after_loot is True

    midget = route_named("Circus Midget")
    assert midget.minimum_level == 3
    assert midget.maximum_level == 6
    assert midget.commands == (
        "south",
        "south",
        "east",
        "east",
        "east",
        "south",
        "south",
        "south",
        "south",
        "south",
        "south",
        "east",
        "east",
        "east",
        "south",
    )
    assert midget.recall_after_loot is True
    assert midget.loot_container == "purse"

    guards = route_named("Gnome Guard Hut")
    assert guards.minimum_level == 7
    assert guards.maximum_level == 10
    assert guards.commands[-5:] == ("south", "south", "south", "west", "west")

    troll = route_named("Gnome Small Troll")
    assert troll.commands[-3:] == ("south", "east", "north")
    assert troll.recall_after_loot is True

