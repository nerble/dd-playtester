"""Source-backed safe Midgaard shop choices for low-level liquidation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Collection, Mapping


_HEALER_TO_MARKET_SQUARE = ("south", "south", "south")
_SHOP_SUFFIXES_FROM_MARKET_SQUARE = {
    "3010": ("east", "north"),
    "3011": ("east", "east", "north"),
    "3020": ("west", "south"),
    "3033": ("west", "west", "north"),
    "3034": ("east", "south"),
    "3035": ("south", "west", "west", "north"),
}


@dataclass(frozen=True)
class SafeShop:
    name: str
    room_vnum: str
    item_type: int
    payout_percent: int
    route_from_mage_lab: tuple[str, ...]

    @property
    def route_from_healer(self) -> tuple[str, ...]:
        """Return the source route from the safe Midgaard healer room."""
        suffix = _SHOP_SUFFIXES_FROM_MARKET_SQUARE.get(self.room_vnum)
        if suffix is None:
            raise ValueError(f"no healer-origin route for shop {self.room_vnum}")
        return _HEALER_TO_MARKET_SQUARE + suffix

    @property
    def route_to_mage_lab(self) -> tuple[str, ...]:
        opposites = {
            "north": "south",
            "east": "west",
            "south": "north",
            "west": "east",
        }
        return tuple(opposites[command] for command in reversed(self.route_from_mage_lab))

    @property
    def route_to_healer(self) -> tuple[str, ...]:
        opposites = {
            "north": "south",
            "east": "west",
            "south": "north",
            "west": "east",
        }
        return tuple(opposites[command] for command in reversed(self.route_from_healer))


# Source: server/area/midgaard.are #SHOPS. Each room has ROOM_SAFE, and each
# route has been derived from the same area's room exits.
SAFE_MIDGAARD_SHOPS = (
    SafeShop(
        "Magic Shop",
        "3033",
        2,
        15,
        ("west", "north", "north", "north"),
    ),
    SafeShop(
        "Magic Shop",
        "3033",
        3,
        15,
        ("west", "north", "north", "north"),
    ),
    SafeShop(
        "Magic Shop",
        "3033",
        4,
        15,
        ("west", "north", "north", "north"),
    ),
    SafeShop(
        "Magic Shop",
        "3033",
        10,
        15,
        ("west", "north", "north", "north"),
    ),
    SafeShop(
        "General Store",
        "3010",
        15,
        40,
        ("west", "north", "north", "east", "east", "east", "north"),
    ),
    SafeShop(
        "General Store",
        "3010",
        19,
        40,
        ("west", "north", "north", "east", "east", "east", "north"),
    ),
    SafeShop(
        "Leather Shop",
        "3035",
        9,
        90,
        ("west", "north", "north", "west", "south", "south", "east", "north"),
    ),
    SafeShop(
        "Armoury",
        "3020",
        9,
        50,
        ("west", "north", "north", "east", "south"),
    ),
    SafeShop(
        "Weapon Shop",
        "3011",
        5,
        40,
        ("west", "north", "north", "east", "east", "east", "east", "north"),
    ),
    SafeShop(
        "Jeweller",
        "3034",
        8,
        50,
        ("west", "north", "north", "east", "east", "east", "south"),
    ),
)

# The source route from healer room 3054 to the Leather Shop uses the Temple
# Square, Market Square, Common Square, and the two Poor Alley rooms.  The
# other registered buyers use Main Street on the way out.  Keep the source
# room names here so a wandering greet-program mobile can block only the
# route that would actually cross it.
_MIDGAARD_DRUNK_ROUTE_ROOMS_BY_SHOP = {
    "3010": frozenset(
        {
            "temple square",
            "market square",
            "main street",
            "general store",
        }
    ),
    "3011": frozenset(
        {
            "temple square",
            "market square",
            "main street",
            "weapon shop",
        }
    ),
    "3020": frozenset(
        {
            "temple square",
            "market square",
            "main street",
            "armoury",
        }
    ),
    "3033": frozenset(
        {
            "temple square",
            "market square",
            "main street",
            "magic shop",
        }
    ),
    "3034": frozenset(
        {
            "temple square",
            "market square",
            "main street",
            "jeweller's shop",
        }
    ),
    "3035": frozenset(
        {
            "temple square",
            "market square",
            "common square",
            "eastern end of poor alley",
            "poor alley",
            "leather shop",
        }
    ),
}

_ARMOUR_WORDS = {
    "armour",
    "armor",
    "boots",
    "bracers",
    "buckler",
    "cap",
    "circlet",
    "gloves",
    "hat",
    "helm",
    "helmet",
    "jerkin",
    "guards",
    "leggings",
    "shield",
}
_WEAPON_WORDS = {
    "axe",
    "club",
    "dagger",
    "knife",
    "mace",
    "pipe",
    "piping",
    "rod",
    "spear",
    "staff",
    "sword",
    "whip",
}
_CONTAINER_WORDS = {
    "bag",
    "box",
    "bucket",
    "pouch",
    "purse",
}


def safe_shop_for_item(
    description: str,
    sale_counts: Mapping[tuple[str, str], int] | None = None,
    *,
    item_type: int | None = None,
    item_value: int | None = None,
    excluded_shop_rooms: Collection[str] | None = None,
) -> SafeShop | None:
    """Choose the best compatible safe shop after known duplicate penalties."""
    words = set(re.findall(r"[a-z]+", description.casefold()))
    if item_type is None:
        item_type = (
            9
            if words & _ARMOUR_WORDS
            else 5
            if words & _WEAPON_WORDS
            else 15
            if words & _CONTAINER_WORDS
            else None
        )
    compatible = [
        shop
        for shop in SAFE_MIDGAARD_SHOPS
        if shop.item_type == item_type
        and shop.room_vnum not in {str(room) for room in (excluded_shop_rooms or ())}
    ]
    keyword = sale_keyword(description)
    counts = sale_counts or {}
    if item_value is not None:
        compatible = [
            shop
            for shop in compatible
            if int(
                item_value
                * shop.payout_percent
                / 100
                / (2 ** counts.get((keyword, shop.name), 0))
            )
            >= 1
        ]
    return max(
        compatible,
        key=lambda shop: (
            shop.payout_percent / (2 ** counts.get((keyword, shop.name), 0)),
            -len(shop.route_from_mage_lab),
        ),
        default=None,
    )


def safe_shop_route_drunk_rooms(shop: SafeShop) -> frozenset[str]:
    """Return source room names crossed by a shop's healer-origin route."""
    return _MIDGAARD_DRUNK_ROUTE_ROOMS_BY_SHOP.get(
        shop.room_vnum,
        frozenset(),
    )


def alternate_safe_shop_for_item(
    description: str,
    sale_counts: Mapping[tuple[str, str], int] | None = None,
    *,
    current_shop: SafeShop,
    observed_locations: Collection[str],
    item_type: int | None = None,
    item_value: int | None = None,
) -> SafeShop | None:
    """Choose another compatible buyer whose route avoids observed hazards."""
    blocked_rooms = {
        " ".join(str(location).casefold().split()).removeprefix("the ")
        for location in observed_locations
    }
    excluded_rooms = {current_shop.room_vnum}
    while True:
        candidate = safe_shop_for_item(
            description,
            sale_counts,
            item_type=item_type,
            item_value=item_value,
            excluded_shop_rooms=excluded_rooms,
        )
        if candidate is None:
            return None
        if not blocked_rooms.intersection(
            safe_shop_route_drunk_rooms(candidate)
        ):
            return candidate
        excluded_rooms.add(candidate.room_vnum)


def sale_keyword(description: str) -> str:
    words = [
        word.strip("[](){}.,!?").casefold()
        for word in description.split()
        if word.strip("[](){}.,!?")
    ]
    ignored = {"a", "an", "the", "of", "from", "corpse"}
    for word in reversed(words):
        if word not in ignored and word.isalpha():
            return word
    return words[-1] if words else description.casefold()
