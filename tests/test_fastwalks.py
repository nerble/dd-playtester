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

    aruncus = route_named("Plains Aruncus")
    assert aruncus.minimum_level == 13
    assert aruncus.maximum_level == 15
    assert aruncus.commands == (
        "south",
        "south",
        "west",
        "west",
        "west",
        "west",
        "north",
        "north",
        "north",
        "east",
        "east",
        "north",
        "north",
        "north",
        "north",
        "north",
        "west",
    )
    assert aruncus.recall_after_loot is True

    watchman = route_named("Mirror Realm Watchman")
    assert watchman.minimum_level == 16
    assert watchman.maximum_level == 20
    assert watchman.commands[-6:] == (
        "open north",
        "north",
        "north",
        "north",
        "north",
        "west",
    )
    assert watchman.recall_after_loot is True

    gardener = route_named("Mirror Realm Gardener")
    assert gardener.minimum_level == 21
    assert gardener.maximum_level == 25
    assert gardener.commands[-8:] == (
        "east",
        "down",
        "down",
        "open east",
        "east",
        "east",
        "north",
        "north",
    )
    assert gardener.recall_after_loot is True

    battle_master = route_named("Shire Battle Master")
    assert battle_master.minimum_level == 26
    assert battle_master.maximum_level == 30
    assert battle_master.commands == (
        "south",
        "south",
        "west",
        "west",
        "west",
        "west",
        "west",
        "north",
        "north",
        "north",
        "north",
        "east",
        "east",
        "east",
        "south",
        "east",
    )
    assert battle_master.recall_after_loot is True

    cancer = route_named("Galaxy Cancer")
    assert cancer.minimum_level == 31
    assert cancer.maximum_level == 35
    assert cancer.commands == (
        "south", "south", "west", "west", "west", "west", "west",
        "west", "west", "west", "west", "west", "west", "west",
        "west", "south", "west", "west", "south", "south", "west",
        "south", "west", "west", "west", "north", "west", "north",
        "north", "north", "east", "east", "down", "north", "east",
        "north", "north", "up", "west",
    )
    assert cancer.recall_after_loot is True

    jerry = route_named("Mirror Realm Jerry Garcia")
    assert jerry.minimum_level == 36
    assert jerry.maximum_level == 40
    assert jerry.commands[-11:] == (
        "open west", "west", "west", "west", "west", "west", "south",
        "west", "up", "east", "east",
    )
    assert jerry.recall_after_loot is True

