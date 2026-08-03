"""Official DD4 fastwalk routes expanded into individual MUD commands."""

from __future__ import annotations

from dataclasses import dataclass


_DIRECTIONS = {
    "n": "north",
    "e": "east",
    "s": "south",
    "w": "west",
    "u": "up",
    "d": "down",
}


@dataclass(frozen=True)
class Fastwalk:
    """A route copied from the official DD4 fastwalk list.

    Every listed route begins at Midgaard recall unless the source marks it
    otherwise. Routes are reference data until a live observation verifies an
    arrival room and a safe return.
    """

    name: str
    minimum_level: int
    maximum_level: int
    notation: str
    recall_after_loot: bool = False
    loot_container: str | None = None
    live_navigation_target: str | None = None
    live_navigation_start_index: int | None = None
    live_navigation_resume_index: int | None = None
    live_navigation_room_vnums: tuple[str, ...] = ()
    live_navigation_blocked_room_vnums: tuple[str, ...] = ()
    live_navigation_preferred_destinations: tuple[str, ...] = ()
    route_preflight_room_vnum: str | None = None
    route_preflight_command: str | None = None
    route_preflight_target: str | None = None
    route_preflight_hard_hazard: bool = False
    route_hard_hazard_targets: tuple[str, ...] = ()

    @property
    def commands(self) -> tuple[str, ...]:
        return expand_fastwalk(self.notation)


def expand_fastwalk(notation: str) -> tuple[str, ...]:
    """Expand DD4 compact notation such as ``2s6e8n`` into commands."""
    commands: list[str] = []
    for raw_segment in notation.strip().casefold().split(";"):
        segment = raw_segment.strip().strip("{}")
        if not segment:
            raise ValueError(f"empty fastwalk segment in {notation!r}")
        if " " in segment:
            if not segment.startswith("open ") or segment[5:] not in _DIRECTIONS.values():
                raise ValueError(f"unsupported fastwalk command {segment!r}")
            commands.append(segment)
            continue

        index = 0
        while index < len(segment):
            count_start = index
            while index < len(segment) and segment[index].isdigit():
                index += 1
            count = int(segment[count_start:index] or "1")
            if count < 1 or index == len(segment) or segment[index] not in _DIRECTIONS:
                raise ValueError(f"invalid compact fastwalk segment {segment!r}")
            commands.extend([_DIRECTIONS[segment[index]]] * count)
            index += 1
    return tuple(commands)


def routes_for_level(level: int) -> tuple[Fastwalk, ...]:
    """Return official routes whose suggested level bands include ``level``."""
    return tuple(
        route
        for route in FASTWALKS
        if route.minimum_level <= level <= route.maximum_level
    )


def route_named(name: str) -> Fastwalk:
    normalized = " ".join(name.casefold().replace("-", " ").split())
    for route in (*FASTWALKS, *MAP_ROUTES):
        if route.name == normalized:
            return route
    raise ValueError(f"unknown fastwalk route {name!r}")


# Source: https://dragons-domain.org/world/fastwalks/
FASTWALKS = (
    Fastwalk("thalos", 1, 30, "2s6e4s3w"),
    Fastwalk("arachnos", 2, 20, "2s13ws2wnwu2w"),
    Fastwalk("moria", 5, 15, "2s6e8n"),
    Fastwalk("dangerous neighbourhood", 5, 15, "2s3e2se"),
    Fastwalk("fleshmonger", 5, 12, "2s6e2s;open east;e"),
    Fastwalk("dragon cult", 5, 25, "3swn"),
    Fastwalk("ambush", 6, 16, "6s"),
    Fastwalk("sewer", 5, 30, "4sd"),
    Fastwalk("elemental canyon", 5, 30, "2s6e4s2es2eds2u"),
)


# Source-backed hunt routes omitted from show-fastwalks, which lists only the
# site's official fastwalks.
MAP_ROUTES = (
    Fastwalk("foundry", 1, 6, "2s3w4ne2d2n", recall_after_loot=True),
    Fastwalk(
        "circus midget",
        3,
        6,
        "2s3e6s3es",
        recall_after_loot=True,
        loot_container="purse",
    ),
    Fastwalk(
        "circus bearded lady",
        3,
        10,
        "2s3e6s2e",
        recall_after_loot=True,
    ),
    Fastwalk(
        "circus strongman",
        5,
        12,
        "2s3e6ses",
        recall_after_loot=True,
    ),
    Fastwalk(
        "circus illusionist",
        5,
        12,
        "2s3e6s3e",
        recall_after_loot=True,
    ),
    Fastwalk(
        "gnome mine",
        5,
        10,
        "2s5es6ene",
        recall_after_loot=True,
    ),
    Fastwalk(
        "gnome guard hut",
        7,
        10,
        "2s5es2e3s2w",
        recall_after_loot=True,
    ),
    Fastwalk(
        "gnome small troll",
        7,
        10,
        "2s5es2e5sen",
        recall_after_loot=True,
    ),
    Fastwalk(
        "gnome treasury",
        13,
        15,
        "2s5es6en3e3s",
        recall_after_loot=True,
    ),
    Fastwalk(
        "shire dwarven prince",
        17,
        20,
        "2s5w4n2w5nw",
        recall_after_loot=True,
    ),
    Fastwalk(
        "shire thain",
        17,
        20,
        "2s5w4n5e",
        recall_after_loot=True,
    ),
    Fastwalk(
        "shire elven wizard",
        17,
        20,
        "2s5w4n5w",
        recall_after_loot=True,
    ),
    Fastwalk(
        "argent bandit leader",
        17,
        20,
        "2s6e4s2es2ed2e5n5es",
        recall_after_loot=True,
    ),
    Fastwalk(
        "pyramid ali baba",
        18,
        20,
        "3s;2e;2s;9e;ew2n2e;e;u;n;e;u;open down;2d;4e;n",
        recall_after_loot=True,
        live_navigation_target="2600",
        live_navigation_start_index=16,
        live_navigation_resume_index=22,
        live_navigation_room_vnums=(
            "5007",
            "5024",
            "5025",
            "5026",
            "5027",
            "5028",
            "5029",
            "5030",
            "5031",
            "5032",
            "5056",
            "2600",
        ),
        live_navigation_blocked_room_vnums=("5028",),
        live_navigation_preferred_destinations=("5056",),
    ),
    Fastwalk(
        "solace lord doom",
        18,
        20,
        "6s;w;2s;w;s;w;2s;w;2s;open south;6s;2w;3s;2w;5s;w;n;w;2s;w;s;d;w;9n;open west;w;u;2w;2n;3e;open south;s",
        recall_after_loot=True,
    ),
    Fastwalk(
        "foundry captain",
        7,
        7,
        "2s3w4ne2d2n;w;open south;s",
        recall_after_loot=True,
    ),
    Fastwalk(
        "plains aruncus",
        13,
        18,
        "2s4w3n2e5nw",
        recall_after_loot=True,
    ),
    Fastwalk(
        "dwarven workers",
        13,
        15,
        "2s6edn",
        recall_after_loot=True,
    ),
    Fastwalk(
        "dwarven nobleman",
        13,
        18,
        (
            "6sw2swsw2sw2s;open south;6s2w3s2w2s4en;"
            "open east;e3n2en"
        ),
        recall_after_loot=True,
    ),
    Fastwalk(
        "dwarven servant",
        17,
        18,
        (
            "6sw2swsw2sw2s;open south;6s2w3s2w2s4en;"
            "open east;e3n2e2nw"
        ),
        recall_after_loot=True,
    ),
    Fastwalk(
        "mahn tor rock toads",
        14,
        18,
        "2s6e4s2es2ed3ne3se2swsw",
        recall_after_loot=True,
    ),
    Fastwalk(
        "mirror realm watchman",
        16,
        20,
        "2s4w3n2e3ne3n2e2n;open north;3nw",
        recall_after_loot=True,
    ),
    Fastwalk(
        "crystalmir white stag",
        16,
        20,
        "6sw2swsw2sw2s;open south;6s2w3s2w5swnw2swsd2w2n3w",
        recall_after_loot=True,
        route_hard_hazard_targets=("Fewmaster Toede",),
    ),
    Fastwalk(
        "shadow keep soldier",
        16,
        20,
        "6sw2s2ws3wn2wse",
        recall_after_loot=True,
    ),
    Fastwalk(
        "highland keeper",
        17,
        20,
        "2s6e8ne2ne6n2dnese4n6w",
        recall_after_loot=True,
    ),
    Fastwalk(
        "galaxy white dwarf",
        17,
        20,
        "2s13ws2w2sws3wnwn",
        recall_after_loot=True,
        route_preflight_room_vnum="1300",
        route_preflight_command="where shadow guardian",
        route_preflight_target="shadow guardian",
        route_preflight_hard_hazard=True,
    ),
    Fastwalk(
        "galaxy red supergiant",
        17,
        20,
        "2s13ws2w2sws3wnwn",
        recall_after_loot=True,
        route_preflight_room_vnum="1300",
        route_preflight_command="where shadow guardian",
        route_preflight_target="shadow guardian",
        route_preflight_hard_hazard=True,
    ),
    Fastwalk(
        "galaxy horsehead nebula",
        18,
        20,
        "2s13ws2w2sws3wnwn",
        recall_after_loot=True,
        route_preflight_room_vnum="1300",
        route_preflight_command="where shadow guardian",
        route_preflight_target="shadow guardian",
        route_preflight_hard_hazard=True,
    ),
    Fastwalk(
        "hightower jailor",
        17,
        20,
        "2s13ws2w2sws3wnwn",
        recall_after_loot=True,
        route_preflight_room_vnum="1300",
        route_preflight_command="where shadow guardian",
        route_preflight_target="shadow guardian",
        route_preflight_hard_hazard=True,
    ),
    Fastwalk(
        "mirror realm gardener",
        21,
        25,
        "2s4w3n2e3ne3n2e2n;open north;3ne2d;open east;e2n",
        recall_after_loot=True,
    ),
    Fastwalk(
        "mirror realm guardian",
        26,
        30,
        "2s4w3n2e3ne3n2e2n;open north;6n;open north;6n",
        recall_after_loot=True,
    ),
    Fastwalk(
        "shire battle master",
        26,
        30,
        "2s5w4n3ese",
        recall_after_loot=True,
    ),
    Fastwalk(
        "minotaur gatekeeper",
        31,
        35,
        "2s6e4s2ese2ed3ne3se2sw3sd4se2s2u;open south;ses2e",
        recall_after_loot=True,
    ),
    Fastwalk(
        "galaxy cancer",
        31,
        35,
        "2s13ws2w2sws3wnw3n2edne2nuw",
        recall_after_loot=True,
        route_preflight_room_vnum="1300",
        route_preflight_command="where shadow guardian",
        route_preflight_target="shadow guardian",
        route_preflight_hard_hazard=True,
    ),
    Fastwalk(
        "mirror realm jerry garcia",
        36,
        40,
        "2s4w3n2e3ne3n2e2n;open north;3nwd2d;open west;5wswu2e",
        recall_after_loot=True,
    ),
    Fastwalk("pit official", 41, 45, "nund", recall_after_loot=True),
    Fastwalk(
        "dwarven home chess dwarf",
        46,
        50,
        "6swswsw2s;open south;7s2w3s2ws4en;open east;e3n5e2s2es",
        recall_after_loot=True,
    ),
    Fastwalk(
        "mirror realm storn",
        46,
        50,
        "2s4w3n2e3ne3n2e2n;open north;4ne2d;open east;6e2s",
        recall_after_loot=True,
    ),
    Fastwalk(
        "darkwood strange mist",
        51,
        55,
        "2s6e4s2es2ed4n3w2nwnw4n",
        recall_after_loot=True,
    ),
    Fastwalk(
        "dwarven home gambler",
        51,
        55,
        "6swswsw2s;open south;7s2w3s2ws4en;open east;e3n5e2s3e",
        recall_after_loot=True,
    ),
    Fastwalk(
        "dwarven home master",
        56,
        60,
        "6swswsw2s;open south;7s2w3s2ws2s4en;open east;e3n5e3n",
        recall_after_loot=True,
    ),
    Fastwalk(
        "vampire hive wounded vampire",
        61,
        65,
        "6sw2swsw2sw2s;open south;6s2w3s2w5swnw2swsdw7n2e3n;open down;d4n;open down;d7se",
        recall_after_loot=True,
    ),
    Fastwalk(
        "tabernacle hulking beast",
        66,
        70,
        "6s;w;2s;w;s;w;2s;w;2s;open south;6s;2w;3s;2w;5s;w;n;w;2s;w;s;d;3w;n;10w;2u;3e;3s;e;w;s",
        recall_after_loot=True,
    ),
    Fastwalk(
        "pirates seas rastafarians",
        71,
        75,
        "6s;w;2s;w;s;w;2s;w;2s;open south;6s;2w;3s;2w;5s;w;n;w;2s;w;s;d;3w;n;10w;4n;3e;2s;open down;d;2w;3s;e;2n;6w;n;e;n;e;n;e;6n",
        recall_after_loot=True,
    ),
    Fastwalk(
        "ghost town crypt thing",
        76,
        76,
        "6s;w;2s;w;s;w;2s;w;2s;open south;6s;2w;3s;2w;5s;w;n;w;2s;w;s;d;3w;n;10w;4n;3e;2s;open down;d;2w;3s;e;2n;6w;n;w;17n;2w;3n;2w;2n;3e;2n;e;s;e;2n;w;4n;w;8n;3w;open west;3w;u;e;open north;n",
        recall_after_loot=True,
    ),
    Fastwalk(
        "ghost town retriever",
        77,
        80,
        "6s;w;2s;w;s;w;2s;w;2s;open south;6s;2w;3s;2w;5s;w;n;w;2s;w;s;d;3w;n;10w;4n;3e;2s;open down;d;2w;3s;e;2n;6w;n;w;17n;2w;3n;2w;2n;3e;2n;e;s;e;2n;w;4n;w;8n;3w;open west;w;open north;n",
        recall_after_loot=True,
    ),
)
