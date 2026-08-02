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
APPLY_CRIT = 50
APPLY_SWIFTNESS = 51
ITEM_LIGHT = 1
ITEM_WEAPON = 5
ITEM_FOOD = 19
ITEM_BODY_PART = 1 << 26
ITEM_LANCE = 1 << 27
ITEM_BOW = 1 << 30
PIERCING_DAMAGE_TYPES = frozenset({2, 11})
BLUNT_DAMAGE_TYPES = frozenset({6, 7, 8})

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
    r"^(?:\[[^\]]+\]|\([^)]*\)|a|an|some|the)\s+",
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
            short_name = normalize_item_name(item.short_description)
            if short_name:
                by_name.setdefault(short_name, []).append(item)
            room_name = normalize_room_item_name(item.room_description)
            if room_name:
                by_name.setdefault(room_name, []).append(item)
        self._by_name = by_name
        self._names_by_length = sorted(by_name, key=len, reverse=True)

    @classmethod
    def from_area_directory(cls, area_directory: Path) -> "GearCatalog":
        return cls(load_object_sources(area_directory))

    def match(self, description: str) -> ObjectSource | None:
        candidates = self.candidates(description)
        if not candidates:
            return None
        # Exact duplicate descriptions exist. Prefer the lowest reset-derived
        # load level for a low-level character.
        return min(candidates, key=lambda item: (item.effective_level, item.vnum))

    def candidates(self, description: str) -> tuple[ObjectSource, ...]:
        """Return distinct source prototypes sharing an observed description."""
        candidates = self._by_name.get(normalize_item_name(description), ())
        return tuple({item.vnum: item for item in candidates}.values())

    def match_many(self, descriptions: Iterable[str]) -> list[ObjectSource]:
        return [
            item
            for description in descriptions
            if (item := self.match(description)) is not None
        ]

    def match_many_usable(
        self,
        descriptions: Iterable[str],
        *,
        character_class: str,
        subclass: str | None,
    ) -> list[ObjectSource]:
        """Exclude ambiguous names when any matching prototype is class-restricted."""
        result: list[ObjectSource] = []
        for description in descriptions:
            candidates = self._by_name.get(normalize_item_name(description), ())
            if not self.is_unambiguously_usable(
                description,
                character_class=character_class,
                subclass=subclass,
            ):
                continue
            result.append(
                min(candidates, key=lambda item: (item.effective_level, item.vnum))
            )
        return result

    def is_unambiguously_usable(
        self,
        description: str,
        *,
        character_class: str,
        subclass: str | None,
    ) -> bool:
        candidates = self._by_name.get(normalize_item_name(description), ())
        return bool(candidates) and all(
            character_can_use_item(
                item,
                character_class=character_class,
                subclass=subclass,
            )
            for item in candidates
        )

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
    cleaned = re.sub(r"^\s*\[#\d+\]\s*", "", cleaned)
    cleaned = " ".join(cleaned.casefold().split())
    while True:
        reduced = _DISPLAY_PREFIX.sub("", cleaned)
        if reduced == cleaned:
            return cleaned.strip(" .")
        cleaned = reduced


def normalize_room_item_name(value: str) -> str:
    cleaned = normalize_item_name(value)
    return re.sub(
        r"\s+(?:is|are|lies?|sits?|rests?|waits?)\b.*$",
        "",
        cleaned,
    )


def item_category(item: ObjectSource) -> str | None:
    if item.item_type == ITEM_LIGHT:
        return "light"
    for bit, category in _WEAR_CATEGORIES.items():
        if item.wear_flags & (1 << bit):
            return category
    return None


def is_piercing_weapon(item: ObjectSource) -> bool:
    """Mirror DD4's is_piercing_weapon check for backstab-capable weapons."""
    return (
        item.item_type == ITEM_WEAPON
        and len(item.values) > 3
        and item.values[3] in PIERCING_DAMAGE_TYPES
    )


def is_blunt_weapon(item: ObjectSource) -> bool:
    """Mirror DD4's blunt-weapon check used by the stun command."""
    return (
        item.item_type == ITEM_WEAPON
        and len(item.values) > 3
        and item.values[3] in BLUNT_DAMAGE_TYPES
    )


def is_bow(item: ObjectSource) -> bool:
    """Mirror DD4's ITEM_BOW requirement used by do_shoot."""
    return bool(item.extra_flags & ITEM_BOW)


def weapon_damage_score(item: ObjectSource) -> int:
    """Return twice the source weapon's average dice damage."""
    if item.item_type != ITEM_WEAPON or len(item.values) < 3:
        return 0
    dice_count, die_size = item.values[1:3]
    if dice_count <= 0 or die_size <= 0:
        return 0
    return dice_count * (die_size + 1)


def stance_score(
    item: ObjectSource,
    stance: str,
    *,
    level_gain_priorities: tuple[str, ...] = (),
) -> tuple[int, ...]:
    bonuses = _bonus_totals(item)
    stats = sum(max(0, bonuses.get(location, 0)) for location in APPLY_STATS)
    damroll = max(0, bonuses.get(APPLY_DAMROLL, 0))
    hitroll = max(0, bonuses.get(APPLY_HITROLL, 0))
    swiftness = max(0, bonuses.get(APPLY_SWIFTNESS, 0))
    critical = max(0, bonuses.get(APPLY_CRIT, 0))
    hitpoints = max(0, bonuses.get(APPLY_HIT, 0))
    mana = max(0, bonuses.get(APPLY_MANA, 0))
    recovery = hitpoints + mana
    armor = item.values[0] if item.item_type == 9 and item.values else 0
    weapon = weapon_damage_score(item)
    if stance == STANCE_PRE_LEVEL:
        if level_gain_priorities:
            level_metrics = {
                "intellectual_practices": (
                    2 * bonuses.get(3, 0) + bonuses.get(2, 0)
                ),
                "physical_practices": (
                    bonuses.get(3, 0)
                    + bonuses.get(1, 0)
                    + bonuses.get(4, 0)
                ),
                "hitpoints": bonuses.get(5, 0),
                "mana": 2 * bonuses.get(2, 0) + bonuses.get(3, 0),
                "movement": bonuses.get(5, 0) + bonuses.get(4, 0),
            }
            return tuple(
                level_metrics[priority] for priority in level_gain_priorities
            ) + (
                stats,
                damroll,
                hitroll,
                swiftness,
                critical,
                recovery,
                armor,
                weapon,
            )
        return (
            stats,
            damroll,
            hitroll,
            swiftness,
            critical,
            recovery,
            armor,
            weapon,
        )
    if stance == STANCE_RECOVERY:
        resource_priorities = tuple(
            priority
            for priority in level_gain_priorities
            if priority in {"hitpoints", "mana"}
        )
        resource_scores = {"hitpoints": hitpoints, "mana": mana}
        prioritized_recovery = (
            tuple(resource_scores[priority] for priority in resource_priorities)
            if resource_priorities
            else (recovery,)
        )
        return prioritized_recovery + (
            recovery,
            stats,
            damroll,
            hitroll,
            swiftness,
            critical,
            armor,
            weapon,
        )
    if stance != STANCE_COMBAT:
        raise ValueError(f"Unknown equipment stance: {stance}")
    direct_damage = weapon + 2 * damroll if weapon else damroll
    return (
        direct_damage,
        hitroll,
        swiftness,
        critical,
        stats,
        recovery,
        armor,
        weapon,
    )


def protects_from_sale(item: ObjectSource) -> bool:
    protected = APPLY_STATS | {
        APPLY_MANA,
        APPLY_HIT,
        APPLY_HITROLL,
        APPLY_DAMROLL,
        APPLY_CRIT,
        APPLY_SWIFTNESS,
    }
    if item.item_type == ITEM_WEAPON and any(
        location == APPLY_DAMROLL and modifier < 0
        for location, modifier in item.affects
    ):
        # A weapon with a damage penalty is not protected merely because it
        # also carries a positive hit-roll modifier. The stance planner still
        # retains it when its source dice make it the best available weapon.
        return False
    return item.item_type == ITEM_LIGHT or is_capacity_infrastructure(item) or any(
        location in protected and modifier > 0
        for location, modifier in item.affects
    )


def is_disposable_food(item: ObjectSource) -> bool:
    """Identify source food that explicitly poisons the eater."""
    return (
        item.item_type == ITEM_FOOD
        and len(item.values) >= 4
        and item.values[3] > 0
    )


def character_can_use_item(
    item: ObjectSource,
    *,
    character_class: str,
    subclass: str | None,
) -> bool:
    """Apply source-backed class restrictions that affect equipment planning."""
    if item.extra_flags & ITEM_BODY_PART:
        return False
    normalized_class = character_class.casefold()
    normalized_subclass = (subclass or "").casefold()
    if item.extra_flags & ITEM_LANCE and normalized_subclass != "knight":
        return False
    if item.extra_flags & ITEM_BOW and normalized_class != "ranger":
        return False
    return True


def is_capacity_infrastructure(item: ObjectSource) -> bool:
    name = normalize_item_name(item.short_description)
    return (
        "large sack" in name
        or "backpack" in name
        or "girdle of many pouches" in name
    )


def is_strength_penalty_ring(item: ObjectSource) -> bool:
    """Reject finger items that reduce strength in every equipment stance."""
    return item_category(item) == "finger" and any(
        location == 1 and modifier < 0 for location, modifier in item.affects
    )


def _stance_rank(
    item: ObjectSource | None,
    stance: str,
    *,
    level_gain_priorities: tuple[str, ...],
    weapon_preference: str | None = None,
) -> tuple[int, ...]:
    """Rank usable gear above emptiness without overlooking harmful stat gear."""
    if stance == STANCE_PRE_LEVEL:
        score_length = 8 + len(level_gain_priorities)
    elif stance == STANCE_RECOVERY:
        resource_priority_count = sum(
            priority in {"hitpoints", "mana"}
            for priority in level_gain_priorities
        )
        score_length = 8 + max(1, resource_priority_count)
    else:
        score_length = 8
    if item is None:
        return (0, 0) + (0,) * score_length
    if is_strength_penalty_ring(item) or any(
        location in APPLY_STATS and modifier < 0
        for location, modifier in item.affects
    ):
        return (-1, 0) + (0,) * score_length
    preferred_weapon = int(
        item_category(item) == "wield"
        and (
            weapon_preference == "piercing"
            and is_piercing_weapon(item)
            or weapon_preference == "blunt"
            and is_blunt_weapon(item)
        )
    )
    return (1, preferred_weapon) + stance_score(
        item,
        stance,
        level_gain_priorities=level_gain_priorities,
    )


def plan_stance(
    carried: Iterable[ObjectSource],
    worn: Iterable[ObjectSource],
    stance: str,
    *,
    character_level: int | None = None,
    level_gain_priorities: tuple[str, ...] = (),
    weapon_preference: str | None = None,
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
            and (
                character_level is None
                or item.effective_level <= character_level
            )
        ]
        capacity = _CATEGORY_CAPACITY.get(category, 1)
        ranked = sorted(
            [(item, True) for item in current]
            + [(item, False) for item in available]
            + [(None, False)] * capacity,
            key=lambda entry: (
                _stance_rank(
                    entry[0],
                    stance,
                    level_gain_priorities=level_gain_priorities,
                    weapon_preference=weapon_preference,
                ),
                entry[1],
            ),
            reverse=True,
        )[:capacity]
        choices.extend(
            GearChoice(item, category, worn)
            for item, worn in ranked
            if item is not None and not worn
        )
    return choices


def plan_stance_swaps(
    carried: Iterable[ObjectSource],
    worn: Iterable[ObjectSource],
    stance: str,
    *,
    level_gain_priorities: tuple[str, ...] = (),
    weapon_preference: str | None = None,
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
                + [(item, False) for item in available]
                + [(None, False)] * capacity,
                key=lambda entry: (
                    _stance_rank(
                        entry[0],
                        stance,
                        level_gain_priorities=level_gain_priorities,
                        weapon_preference=weapon_preference,
                    ),
                    entry[1],
                ),
                reverse=True,
            )[:capacity]
            if item is not None
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
    removals.sort(
        key=lambda item: stance_score(
            item,
            stance,
            level_gain_priorities=level_gain_priorities,
        )
    )
    additions.sort(
        key=lambda item: stance_score(
            item,
            stance,
            level_gain_priorities=level_gain_priorities,
        )
    )
    return removals, additions


def item_keyword(item: ObjectSource) -> str:
    description_words = normalize_item_name(item.short_description).split()
    keyword_words = item.keywords.split()
    if description_words and keyword_words:
        noun = description_words[-1]
        if noun in keyword_words and len(noun) >= 5:
            return noun
        if noun not in keyword_words:
            return keyword_words[0]
        return max(keyword_words, key=len)
    if keyword_words:
        return keyword_words[0]
    return description_words[-1] if description_words else ""


def item_command_keyword(
    item: ObjectSource,
    peers: Iterable[ObjectSource] = (),
) -> str:
    """Choose a source keyword that will select ``item`` among ``peers``.

    DD4's ``wear`` and ``remove`` commands consume one keyword, so a generic
    noun such as ``dagger`` can select the wrong prototype when a better
    ``long dagger slim`` is also carried.  Prefer a source keyword that is
    absent from the other prototypes and keep the legacy noun fallback for
    genuinely ambiguous or uncontextualized items.
    """
    keyword_words = [word.casefold() for word in item.keywords.split() if word]
    if not keyword_words:
        return item_keyword(item)
    other_keywords = {
        word.casefold()
        for peer in peers
        if peer.vnum != item.vnum
        for word in peer.keywords.split()
    }
    description_words = normalize_item_name(item.short_description).split()
    noun = description_words[-1] if description_words else ""
    if noun in keyword_words and len(noun) >= 5 and noun not in other_keywords:
        return noun
    unique_words = [word for word in keyword_words if word not in other_keywords]
    if unique_words:
        return next(
            (word for word in unique_words if word in description_words),
            unique_words[0],
        )
    return item_keyword(item)


def _bonus_totals(item: ObjectSource) -> dict[int, int]:
    totals: dict[int, int] = {}
    for location, modifier in item.affects:
        totals[location] = totals.get(location, 0) + modifier
    return totals
