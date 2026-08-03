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

    stag = route_named("Crystalmir White Stag")
    assert stag.route_hard_hazard_targets == ("Fewmaster Toede",)

    keeper = route_named("Highland Keeper")
    assert keeper.minimum_level == 17
    assert keeper.maximum_level == 20
    assert keeper.commands[-6:] == (
        "west", "west", "west", "west", "west", "west"
    )
    assert keeper.recall_after_loot is True

    troll = route_named("Gnome Small Troll")
    assert troll.commands[-3:] == ("south", "east", "north")
    assert troll.recall_after_loot is True

    treasury = route_named("Gnome Treasury")
    assert treasury.minimum_level == 13
    assert treasury.maximum_level == 15
    assert treasury.commands == (
        "south",
        "south",
        "east",
        "east",
        "east",
        "east",
        "east",
        "south",
        "east",
        "east",
        "east",
        "east",
        "east",
        "east",
        "north",
        "east",
        "east",
        "east",
        "south",
        "south",
        "south",
    )
    assert treasury.recall_after_loot is True

    aruncus = route_named("Plains Aruncus")
    assert aruncus.minimum_level == 13
    assert aruncus.maximum_level == 18
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

    pyramid = route_named("Pyramid Ali Baba")
    assert pyramid.commands[22:] == (
        "east",
        "up",
        "north",
        "east",
        "up",
        "open down",
        "down",
        "down",
        "east",
        "east",
        "east",
        "east",
        "north",
    )
    assert pyramid.live_navigation_resume_index == 22

    white_dwarf = route_named("Galaxy White Dwarf")
    assert white_dwarf.minimum_level == 17
    assert white_dwarf.maximum_level == 20
    assert white_dwarf.commands == (
        ("south",) * 2
        + ("west",) * 13
        + ("south",)
        + ("west",) * 2
        + ("south",) * 2
        + ("west", "south")
        + ("west",) * 3
        + ("north", "west")
        + ("north",)
    )
    assert white_dwarf.recall_after_loot is True

    horsehead = route_named("Galaxy Horsehead Nebula")
    assert horsehead.minimum_level == 18
    assert horsehead.maximum_level == 20
    assert horsehead.commands == white_dwarf.commands
    assert horsehead.recall_after_loot is True

    jailor = route_named("HighTower Jailor")
    assert jailor.minimum_level == 17
    assert jailor.maximum_level == 20
    assert jailor.commands == white_dwarf.commands
    assert jailor.recall_after_loot is True

    workers = route_named("Dwarven Workers")
    assert workers.minimum_level == 13
    assert workers.maximum_level == 15
    assert workers.commands == (
        "south",
        "south",
        "east",
        "east",
        "east",
        "east",
        "east",
        "east",
        "down",
        "north",
    )
    assert workers.recall_after_loot is True

    nobleman = route_named("Dwarven Nobleman")
    assert nobleman.minimum_level == 13
    assert nobleman.maximum_level == 18
    assert nobleman.commands == (
        "south", "south", "south", "south", "south", "south", "west",
        "south", "south", "west", "south", "west", "south", "south",
        "west", "south", "south", "open south", "south", "south",
        "south", "south", "south", "south", "west", "west", "south",
        "south", "south", "west", "west", "south", "south", "east",
        "east", "east", "east", "north", "open east", "east", "north",
        "north", "north", "east", "east", "north",
    )
    assert nobleman.recall_after_loot is True

    servant = route_named("Dwarven Servant")
    assert servant.minimum_level == 17
    assert servant.maximum_level == 18
    assert servant.commands[-9:] == (
        "east",
        "north",
        "north",
        "north",
        "east",
        "east",
        "north",
        "north",
        "west",
    )
    assert servant.recall_after_loot is True

    prince = route_named("Shire Dwarven Prince")
    assert prince.minimum_level == 17
    assert prince.maximum_level == 20
    assert prince.commands == (
        "south", "south", "west", "west", "west", "west", "west",
        "north", "north", "north", "north", "west", "west",
        "north", "north", "north", "north", "north", "west",
    )
    assert prince.recall_after_loot is True

    thain = route_named("Shire Thain")
    assert thain.minimum_level == 17
    assert thain.maximum_level == 20
    assert thain.commands == (
        "south", "south", "west", "west", "west", "west", "west",
        "north", "north", "north", "north", "east", "east", "east",
        "east", "east",
    )
    assert thain.recall_after_loot is True

    argent = route_named("Argent Bandit Leader")
    assert argent.minimum_level == 17
    assert argent.maximum_level == 20
    assert argent.commands == (
        ("south",) * 2
        + ("east",) * 6
        + ("south",) * 4
        + ("east",) * 2
        + ("south", "east", "east", "down", "east", "east")
        + ("north",) * 5
        + ("east",) * 5
        + ("south",)
    )
    assert argent.recall_after_loot is True

    wizard = route_named("Shire Elven Wizard")
    assert wizard.minimum_level == 17
    assert wizard.maximum_level == 20
    assert wizard.commands == thain.commands[:-5] + ("west",) * 5
    assert wizard.recall_after_loot is True

    ali_baba = route_named("Pyramid Ali Baba")
    assert ali_baba.minimum_level == 18
    assert ali_baba.maximum_level == 20
    assert ali_baba.commands == (
        ("south",) * 3
        + ("east",) * 2
        + ("south",) * 2
        + ("east",) * 9
        + ("east", "west")
        + ("north",) * 2
        + ("east",) * 2
        + ("east", "up", "north", "east", "up", "open down", "down", "down")
        + ("east",) * 4
        + ("north",)
    )
    assert ali_baba.recall_after_loot is True

    rock_toads = route_named("Mahn-Tor Rock Toads")
    assert rock_toads.minimum_level == 14
    assert rock_toads.maximum_level == 18
    assert rock_toads.commands[-8:] == (
        "south",
        "south",
        "east",
        "south",
        "south",
        "west",
        "south",
        "west",
    )
    assert rock_toads.recall_after_loot is True

    watchman = route_named("Mirror Realm Watchman")
    assert watchman.minimum_level == 16
    assert watchman.maximum_level == 20
    assert watchman.commands[-7:] == (
        "north",
        "north",
        "open north",
        "north",
        "north",
        "north",
        "west",
    )
    assert watchman.recall_after_loot is True

    white_stag = route_named("Crystalmir White Stag")
    assert white_stag.minimum_level == 16
    assert white_stag.maximum_level == 20
    assert white_stag.commands[-8:] == (
        "down",
        "west",
        "west",
        "north",
        "north",
        "west",
        "west",
        "west",
    )
    assert white_stag.recall_after_loot is True

    soldier = route_named("Shadow Keep Soldier")
    assert soldier.minimum_level == 16
    assert soldier.maximum_level == 20
    assert soldier.commands == (
        "south", "south", "south", "south", "south", "south", "west",
        "south", "south", "west", "west", "south", "west", "west",
        "west", "north", "west", "west", "south", "east",
    )
    assert soldier.recall_after_loot is True

    gardener = route_named("Mirror Realm Gardener")
    assert gardener.minimum_level == 21
    assert gardener.maximum_level == 25
    assert gardener.commands[-13:] == (
        "north",
        "north",
        "open north",
        "north",
        "north",
        "north",
        "east",
        "down",
        "down",
        "open east",
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

    chess_dwarf = route_named("Dwarven Home Chess Dwarf")
    assert chess_dwarf.minimum_level == 46
    assert chess_dwarf.maximum_level == 50
    assert chess_dwarf.commands == (
        ("south",) * 6
        + ("west", "south", "west", "south", "west")
        + ("south",) * 2
        + ("open south",)
        + ("south",) * 7
        + ("west",) * 2
        + ("south",) * 3
        + ("west",) * 2
        + ("south",)
        + ("east",) * 4
        + ("north", "open east", "east")
        + ("north",) * 3
        + ("east",) * 5
        + ("south",) * 2
        + ("east",) * 2
        + ("south",)
    )
    assert chess_dwarf.recall_after_loot is True

    storn = route_named("Mirror Realm Storn")
    assert storn.minimum_level == 46
    assert storn.maximum_level == 50
    assert storn.commands == (
        ("south",) * 2
        + ("west",) * 4
        + ("north",) * 3
        + ("east",) * 2
        + ("north",) * 3
        + ("east",)
        + ("north",) * 3
        + ("east",) * 2
        + ("north",) * 2
        + ("open north",)
        + ("north",) * 4
        + ("east",)
        + ("down",) * 2
        + ("open east",)
        + ("east",) * 6
        + ("south",) * 2
    )
    assert storn.recall_after_loot is True

    strange_mist = route_named("Darkwood Strange Mist")
    assert strange_mist.minimum_level == 51
    assert strange_mist.maximum_level == 55
    assert strange_mist.commands == (
        ("south",) * 2
        + ("east",) * 6
        + ("south",) * 4
        + ("east",) * 2
        + ("south", "east")
        + ("east", "down")
        + ("north",) * 4
        + ("west",) * 3
        + ("north",) * 2
        + ("west", "north", "west")
        + ("north",) * 4
    )
    assert strange_mist.recall_after_loot is True

    gambler = route_named("Dwarven Home Gambler")
    assert gambler.minimum_level == 51
    assert gambler.maximum_level == 55
    assert gambler.commands == (
        ("south",) * 6
        + ("west", "south", "west", "south", "west")
        + ("south",) * 2
        + ("open south",)
        + ("south",) * 7
        + ("west",) * 2
        + ("south",) * 3
        + ("west",) * 2
        + ("south",)
        + ("east",) * 4
        + ("north", "open east", "east")
        + ("north",) * 3
        + ("east",) * 5
        + ("south",) * 2
        + ("east",) * 3
    )
    assert gambler.recall_after_loot is True

    master = route_named("Dwarven Home Master")
    assert master.minimum_level == 56
    assert master.maximum_level == 60
    assert master.commands == (
        ("south",) * 6
        + ("west", "south", "west", "south", "west")
        + ("south",) * 2
        + ("open south",)
        + ("south",) * 7
        + ("west",) * 2
        + ("south",) * 3
        + ("west",) * 2
        + ("south",) * 3
        + ("east",) * 4
        + ("north", "open east", "east")
        + ("north",) * 3
        + ("east",) * 5
        + ("north",) * 3
    )
    assert master.recall_after_loot is True

    vampire = route_named("Vampire Hive Wounded Vampire")
    assert vampire.minimum_level == 61
    assert vampire.maximum_level == 65
    assert vampire.commands == (
        ("south",) * 6
        + ("west", "south", "south", "west", "south", "west")
        + ("south",) * 2
        + ("west",)
        + ("south",) * 2
        + ("open south",)
        + ("south",) * 6
        + ("west",) * 2
        + ("south",) * 3
        + ("west",) * 2
        + ("south",) * 5
        + ("west", "north", "west")
        + ("south",) * 2
        + ("west", "south", "down", "west")
        + ("north",) * 7
        + ("east",) * 2
        + ("north",) * 3
        + ("open down", "down")
        + ("north",) * 4
        + ("open down", "down")
        + ("south",) * 7
        + ("east",)
    )
    assert vampire.recall_after_loot is True

    beast = route_named("Tabernacle Hulking Beast")
    assert beast.minimum_level == 66
    assert beast.maximum_level == 70
    assert beast.commands == (
        ("south",) * 6
        + ("west", "south", "south", "west", "south", "west")
        + ("south",) * 2
        + ("west",)
        + ("south",) * 2
        + ("open south",)
        + ("south",) * 6
        + ("west",) * 2
        + ("south",) * 3
        + ("west",) * 2
        + ("south",) * 5
        + ("west", "north", "west")
        + ("south",) * 2
        + ("west", "south", "down")
        + ("west",) * 3
        + ("north",)
        + ("west",) * 10
        + ("up",) * 2
        + ("east",) * 3
        + ("south",) * 3
        + ("east", "west", "south")
    )
    assert beast.recall_after_loot is True

    rastafarians = route_named("Pirates Seas Rastafarians")
    assert rastafarians.minimum_level == 71
    assert rastafarians.maximum_level == 75
    assert rastafarians.commands == (
        ("south",) * 6
        + ("west", "south", "south", "west", "south", "west")
        + ("south",) * 2
        + ("west", "south", "south", "open south")
        + ("south",) * 6
        + ("west",) * 2
        + ("south",) * 3
        + ("west",) * 2
        + ("south",) * 5
        + ("west", "north", "west", "south", "south", "west", "south", "down")
        + ("west",) * 3
        + ("north",)
        + ("west",) * 10
        + ("north",) * 4
        + ("east",) * 3
        + ("south",) * 2
        + ("open down", "down")
        + ("west",) * 2
        + ("south",) * 3
        + ("east",)
        + ("north",) * 2
        + ("west",) * 6
        + ("north", "east", "north", "east", "north", "east")
        + ("north",) * 6
    )
    assert rastafarians.recall_after_loot is True

    crypt = route_named("Ghost Town Crypt Thing")
    assert crypt.minimum_level == 76
    assert crypt.maximum_level == 76
    assert len(crypt.commands) == 146
    assert crypt.commands[-8:] == (
        "open west",
        "west",
        "west",
        "west",
        "up",
        "east",
        "open north",
        "north",
    )
    assert crypt.recall_after_loot is True

    retriever = route_named("Ghost Town Retriever")
    assert retriever.minimum_level == 77
    assert retriever.maximum_level == 80
    assert len(retriever.commands) == 142
    assert retriever.commands[-4:] == (
        "open west",
        "west",
        "open north",
        "north",
    )
    assert retriever.recall_after_loot is True


@pytest.mark.parametrize(
    "name",
    [
        "galaxy white dwarf",
        "galaxy red supergiant",
        "galaxy horsehead nebula",
        "hightower jailor",
        "galaxy cancer",
    ],
)
def test_shadow_grove_routes_declare_the_source_hazard_preflight(name: str) -> None:
    route = route_named(name)

    assert route.route_preflight_room_vnum == "1300"
    assert route.route_preflight_command == "where shadow guardian"
    assert route.route_preflight_target == "shadow guardian"


def test_solace_lord_doom_route_is_source_derived_and_recall_safe() -> None:
    route = route_named("Solace Lord Doom")

    assert route.minimum_level == 18
    assert route.maximum_level == 20
    assert route.recall_after_loot is True
    assert len(route.commands) == 66
    assert route.commands[:7] == (
        "south",
        "south",
        "south",
        "south",
        "south",
        "south",
        "west",
    )
    assert route.commands[-7:] == (
        "north",
        "north",
        "east",
        "east",
        "east",
        "open south",
        "south",
    )

