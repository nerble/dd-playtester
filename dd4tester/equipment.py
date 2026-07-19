"""Source-backed equipment scoring for levelling and recovery stances."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Mapping

from .hunt_candidates import ObjectSource, load_object_sources


APPLY_STATS = frozenset({1, 2, 3, 4, 5})
APPLY_MANA = 12
APPLY_HIT = 13
APPLY_HITROLL = 18
APPLY_DAMROLL = 19

STANCE_COMBAT = "combat"
STANCE_PRE_LEVEL = "pre_level"
STANCE_RECOVERY = "recovery"

_WEAR_CATEGORIES = {
    1: "finger",
    2: "neck",
    3: "body",
    4: "head",
    5: "legs",
    6: "feet",
    7: "hands",
    8: "arms",
    9: "shield",
    10: "about",
    11: "waist",
    12: "wrist",
    13: "wield",
    14: "hold",
    15: "float",
    16: "pouch",
    17: "ranged_weapon",
}
_CATEGORY_CAPACITY = {"finger": 2, "neck": 2, "wrist": 2}
_DISPLAY_PREFIX = re.compile(
    r"^(?:\[[^\]]+\]|\([^)]*\)|a|an|the)\s+",
    re.IGNORECASE,
)
_COLOUR_CODE = re.compile(r"\{.")
_NUMERIC_COLOUR_CODE = re.compile(r"<\d+>")


@dataclass(frozen=True)
class GearChoice:
    item: ObjectSource
    category: str
    worn: bool


class GearCatalog:
    def __init__(self, objects: Mapping[int, ObjectSource]) -> None:
        self.objects = dict(objects)
        by_name: dict[str, list[ObjectSource]] = {}
        for item in self.objects.values():
            by_name.setdefault(normalize_item_name(item.short_description), []).append(
                item
            )
        self._by_name = by_name
        self._names_by_length = sorted(by_name, key=len, reverse=True)

    @classmethod
    def from_area_directory(cls, area_directory: Path) -> "GearCatalog":
        return cls(load_object_sources(area_directory))

    def match(self, description: str) -> ObjectSource | None:
        candidates = self._by_name.get(normalize_item_name(description), ())
        if not candidates:
            return None
        # Exact duplicate descriptions exist. Prefer the lowest-level prototype;
        # it is the conservative match for a low-level character.
        return min(candidates, key=lambda item: (item.level, item.vnum))

    def match_many(self, descriptions: Iterable[str]) -> list[ObjectSource]:
        return [
            item
            for description in descriptions
            if (item := self.match(description)) is not None
        ]

    def match_equipment_text(self, text: str) -> list[ObjectSource]:
        found: list[ObjectSource] = []
        for raw_line in text.splitlines():
            line = normalize_item_name(raw_line)
            for name in self._names_by_length:
                if line.endswith(name):
                    item = self.match(name)
                    if item is not None:
                        found.append(item)
                    break
        return found


@lru_cache(maxsize=4)
def load_gear_catalog(area_directory: str) -> GearCatalog:
    return GearCatalog.from_area_directory(Path(area_directory))


def normalize_item_name(value: str) -> str:
    cleaned = _COLOUR_CODE.sub("", value)
    cleaned = _NUMERIC_COLOUR_CODE.sub("", cleaned)
    cleaned = re.sub(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])", "", cleaned)
    cleaned = " ".join(cleaned.casefold().split())
    while True:
        reduced = _DISPLAY_PREFIX.sub("", cleaned)
        if reduced == cleaned:
            return cleaned.strip(" .")
        cleaned = reduced


def item_category(item: ObjectSource) -> str | None:
    for bit, category in _WEAR_CATEGORIES.items():
        if item.wear_flags & (1 << bit):
            return category
    return None


def stance_score(item: ObjectSource, stance: str) -> tuple[int, ...]:
    bonuses = _bonus_totals(item)
    stats = sum(max(0, bonuses.get(location, 0)) for location in APPLY_STATS)
    damroll = max(0, bonuses.get(APPLY_DAMROLL, 0))
    hitroll = max(0, bonuses.get(APPLY_HITROLL, 0))
    recovery = max(0, bonuses.get(APPLY_HIT, 0)) + max(
        0, bonuses.get(APPLY_MANA, 0)
    )
    armor = item.values[0] if item.item_type == 9 and item.values else 0
    weapon = (
        sum(item.values[1:3])
        if item.item_type == 5 and len(item.values) >= 3
        else 0
    )
    if stance == STANCE_PRE_LEVEL:
        return stats, damroll, hitroll, recovery, armor, weapon
    if stance == STANCE_RECOVERY:
        return recovery, stats, damroll, hitroll, armor, weapon
    if stance != STANCE_COMBAT:
        raise ValueError(f"Unknown equipment stance: {stance}")
    return damroll, hitroll, stats, recovery, armor, weapon


def protects_from_sale(item: ObjectSource) -> bool:
    protected = APPLY_STATS | {
        APPLY_MANA,
        APPLY_HIT,
        APPLY_HITROLL,
        APPLY_DAMROLL,
    }
    return is_capacity_infrastructure(item) or any(
        location in protected and modifier > 0
        for location, modifier in item.affects
    )


def is_capacity_infrastructure(item: ObjectSource) -> bool:
    name = normalize_item_name(item.short_description)
    return (
        "large sack" in name
        or "backpack" in name
        or "girdle of many pouches" in name
    )


def plan_stance(
    carried: Iterable[ObjectSource],
    worn: Iterable[ObjectSource],
    stance: str,
    *,
    character_level: int | None = None,
) -> list[GearChoice]:
    """Return carried items that should replace or fill the current gear set."""
    carried_items = list(carried)
    worn_items = list(worn)
    categories = {
        category
        for item in carried_items + worn_items
        if (category := item_category(item)) is not None
    }
    choices: list[GearChoice] = []
    for category in sorted(categories):
        current = [item for item in worn_items if item_category(item) == category]
        available = [
            item
            for item in carried_items
            if item_category(item) == category
            and (character_level is None or item.level <= character_level)
        ]
        capacity = _CATEGORY_CAPACITY.get(category, 1)
        ranked = sorted(
            [(item, True) for item in current] + [(item, False) for item in available],
            key=lambda entry: (stance_score(entry[0], stance), entry[1]),
            reverse=True,
        )[:capacity]
        choices.extend(
            GearChoice(item, category, worn)
            for item, worn in ranked
            if not worn
        )
    return choices


def plan_stance_swaps(
    carried: Iterable[ObjectSource],
    worn: Iterable[ObjectSource],
    stance: str,
) -> tuple[list[ObjectSource], list[ObjectSource]]:
    """Return worn removals and carried additions needed for a stance."""
    carried_items = list(carried)
    worn_items = list(worn)
    removals: list[ObjectSource] = []
    additions: list[ObjectSource] = []
    categories = {
        category
        for item in carried_items + worn_items
        if (category := item_category(item)) is not None
    }
    for category in sorted(categories):
        current = [item for item in worn_items if item_category(item) == category]
        available = [item for item in carried_items if item_category(item) == category]
        capacity = _CATEGORY_CAPACITY.get(category, 1)
        desired = [
            item
            for item, _ in sorted(
                [(item, True) for item in current]
                + [(item, False) for item in available],
                key=lambda entry: (stance_score(entry[0], stance), entry[1]),
                reverse=True,
            )[:capacity]
        ]
        desired_counts: dict[int, int] = {}
        for item in desired:
            desired_counts[item.vnum] = desired_counts.get(item.vnum, 0) + 1
        kept_counts: dict[int, int] = {}
        for item in current:
            kept = kept_counts.get(item.vnum, 0)
            if kept < desired_counts.get(item.vnum, 0):
                kept_counts[item.vnum] = kept + 1
            else:
                removals.append(item)
        current_counts: dict[int, int] = {}
        for item in current:
            current_counts[item.vnum] = current_counts.get(item.vnum, 0) + 1
        added_counts: dict[int, int] = {}
        for item in desired:
            already = current_counts.get(item.vnum, 0)
            added = added_counts.get(item.vnum, 0)
            if added < max(0, desired_counts[item.vnum] - already):
                additions.append(item)
                added_counts[item.vnum] = added + 1
    removals.sort(key=lambda item: stance_score(item, stance))
    additions.sort(key=lambda item: stance_score(item, stance))
    return removals, additions


def item_keyword(item: ObjectSource) -> str:
    return item.keywords.split()[0] if item.keywords.split() else normalize_item_name(
        item.short_description
    ).split()[0]


def _bonus_totals(item: ObjectSource) -> dict[int, int]:
    totals: dict[int, int] = {}
    for location, modifier in item.affects:
        totals[location] = totals.get(location, 0) + modifier
    return totals
