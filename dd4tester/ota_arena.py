"""Source-verified Ota'ar Dar arena progression routes.

The arena is not a normal hunt.  DD4 forces an outsider into the floor, and
the exit opens only after five exact favour tokens have been collected.  Keep
that world rule in a small data module so the live controller and its tests
share one route and identity definition.
"""

from __future__ import annotations

from dataclasses import dataclass


OTA_ARENA_AREA = "sahuagin_arena_jail.are"
OTA_ARENA_GUARD_ROOM_VNUM = 27243
OTA_ARENA_FORCED_ENTRY_ROOM_VNUM = 27227
OTA_ARENA_WIZINVIS_ROOM_VNUM = 27239
OTA_ARENA_STAGING_ROOM_VNUM = 27278
OTA_ARENA_EXIT_ROOM_VNUM = 27307

# This is the source route from Midgaard recall through the canals to the
# cityguard.  The final south command triggers the forced arena transfer.
OTA_ARENA_ENTRY_ROUTE = (
    "south", "south", "south", "east", "east", "south", "south",
    "west", "west", "west", "west", "west", "west", "west", "west",
    "west", "west", "west", "west", "west", "down", "down", "down",
    "down", "east", "east", "south", "west", "north", "down", "down",
    "open south", "south", "open south", "south",
)

# After all five tokens are present, the source program transfers the player
# to the staging zone.  This route passes back through the eastern gate.
OTA_ARENA_EXIT_ROUTE = (
    "east", "east", "south", "east", "east", "north",
)


@dataclass(frozen=True)
class OtaArenaTarget:
    """One source reset and the favour object it supplies."""

    mobile_vnum: int
    room_vnum: int
    command_keyword: str
    token_vnum: int
    token_terms: tuple[str, ...]
    route_from_previous: tuple[str, ...]
    requires_sanctuary: bool = True


OTA_ARENA_TARGETS = (
    OtaArenaTarget(
        mobile_vnum=27352,
        room_vnum=27224,
        command_keyword="kaerl",
        token_vnum=27481,
        token_terms=("favour", "kaer'l", "kaerl"),
        route_from_previous=("west", "west", "west"),
    ),
    OtaArenaTarget(
        mobile_vnum=27353,
        room_vnum=27215,
        command_keyword="luvht",
        token_vnum=27482,
        token_terms=("favour", "luv'ht", "luvht"),
        route_from_previous=("south",),
    ),
    OtaArenaTarget(
        mobile_vnum=27354,
        room_vnum=27229,
        command_keyword="maland",
        token_vnum=27483,
        token_terms=("favour", "maland"),
        route_from_previous=("north", "east", "east", "east", "east", "east"),
    ),
    OtaArenaTarget(
        mobile_vnum=27355,
        room_vnum=27526,
        command_keyword="heiral",
        token_vnum=27484,
        token_terms=("favour", "heiral"),
        route_from_previous=("up", "west", "west", "west"),
    ),
    OtaArenaTarget(
        mobile_vnum=27356,
        room_vnum=27529,
        command_keyword="urmda",
        token_vnum=27485,
        token_terms=("favour", "urm'da", "urmda"),
        route_from_previous=("east", "east", "east"),
    ),
)

# Useful reconnect points inside the lower arena circuit.  These are only
# recovery prefixes; normal entry still uses the forced transfer above.
OTA_ARENA_RECOVERY_ROUTES = {
    "27227": OTA_ARENA_TARGETS[0].route_from_previous,
    "27226": ("west", "west"),
    "27225": ("west",),
    "27224": (),
}


def ota_arena_target(index: int) -> OtaArenaTarget | None:
    """Return the target at ``index`` without allowing an out-of-range alias."""

    if not 0 <= int(index) < len(OTA_ARENA_TARGETS):
        return None
    return OTA_ARENA_TARGETS[int(index)]


def ota_arena_token_terms_present(
    descriptions: list[str] | tuple[str, ...],
    target: OtaArenaTarget,
) -> bool:
    """Match a favour by its source-backed name, not by an ordinal alone."""

    for description in descriptions:
        folded = str(description).casefold()
        if "favour" in folded and any(term.casefold() in folded for term in target.token_terms[1:]):
            return True
    return False
