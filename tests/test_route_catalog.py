from dd4tester.fastwalks import route_named


def test_gnome_mine_route_reaches_the_source_backed_mine_entrance() -> None:
    route = route_named("Gnome Mine")

    assert route.minimum_level == 5
    assert route.maximum_level == 10
    assert route.commands == (
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
    )
