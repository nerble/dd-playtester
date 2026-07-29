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
        "foundry captain",
        7,
        7,
        "2s3w4ne2d2n;w;open south;s",
        recall_after_loot=True,
    ),
    Fastwalk(
        "plains aruncus",
        13,
        15,
        "2s4w3n2e5nw",
        recall_after_loot=True,
    ),
    Fastwalk(
        "mirror realm watchman",
        16,
        20,
        "2s4w3n2e3ne3n2e4n;open north;4nw",
        recall_after_loot=True,
    ),
    Fastwalk(
        "mirror realm gardener",
        21,
        25,
        "2s4w3n2e3ne3n2e4n;open north;4ne2d;open east;2e2n",
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
    ),
    Fastwalk(
        "mirror realm jerry garcia",
        36,
        40,
        "2s4w3n2e3ne3n2e2n;open north;3nwd2d;open west;5wswu2e",
        recall_after_loot=True,
    ),
    Fastwalk("pit official", 41, 45, "nund", recall_after_loot=True),
)
