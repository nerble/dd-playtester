"""Source-backed safe Midgaard shop choices for low-level liquidation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SafeShop:
    name: str
    room_vnum: str
    item_type: int
    payout_percent: int
    route_from_mage_lab: tuple[str, ...]

    @property
    def route_to_mage_lab(self) -> tuple[str, ...]:
        opposites = {
            "north": "south",
            "east": "west",
            "south": "north",
            "west": "east",
        }
        return tuple(opposites[command] for command in reversed(self.route_from_mage_lab))


# Source: server/area/midgaard.are #SHOPS. Each room has ROOM_SAFE, and each
# route has been derived from the same area's room exits.
SAFE_MIDGAARD_SHOPS = (
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
)

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
    "helmet",
    "jerkin",
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
    "rod",
    "spear",
    "staff",
    "sword",
    "whip",
}


def safe_shop_for_item(description: str) -> SafeShop | None:
    """Choose the highest-margin compatible safe shop for a described item."""
    words = set(description.casefold().split())
    item_type = 9 if words & _ARMOUR_WORDS else 5 if words & _WEAPON_WORDS else None
    compatible = [
        shop for shop in SAFE_MIDGAARD_SHOPS if shop.item_type == item_type
    ]
    return max(compatible, key=lambda shop: shop.payout_percent, default=None)


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
