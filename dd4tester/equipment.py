"""Source-backed equipment scoring for levelling and recovery stances."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .hunt_candidates import (
    ObjectSetSource,
    ObjectSource,
    load_object_set_sources,
    load_object_sources,
)


APPLY_STATS = frozenset({1, 2, 3, 4, 5})
APPLY_MANA = 12
APPLY_HIT = 13
APPLY_HITROLL = 18
APPLY_DAMROLL = 19
APPLY_CRIT = 50
APPLY_SWIFTNESS = 51
ITEM_LIGHT = 1
ITEM_WEAPON = 5
ITEM_PAINT = 28
ITEM_FOOD = 19
ITEM_NODROP = 1 << 7
ITEM_NOREMOVE = 1 << 12
ITEM_INVENTORY = 1 << 13
ITEM_BODY_PART = 1 << 26
ITEM_LANCE = 1 << 27
ITEM_BOW = 1 << 30
ITEM_CURSED = 1 << 61
PIERCING_DAMAGE_TYPES = frozenset({2, 11})
BLUNT_DAMAGE_TYPES = frozenset({6, 7, 8})

# ``str_app`` from DD4 const.c. Values are (to-hit, to-damage).
_STR_APP = (
    (-5, -4),
    (-5, -4),
    (-3, -2),
    (-3, -1),
    (-2, -1),
    (-2, -1),
    (-1, 0),
    (-1, 0),
    (0, 0),
    (0, 0),
    (0, 0),
    (0, 0),
    (0, 0),
    (0, 0),
    (0, 1),
    (1, 1),
    (1, 2),
    (2, 3),
    (2, 4),
    (3, 5),
    (3, 6),
    (4, 7),
    (5, 7),
    (6, 8),
    (8, 10),
    (10, 12),
    (12, 13),
    (13, 14),
    (16, 16),
    (18, 18),
    (20, 20),
    (22, 22),
)

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
    def __init__(
        self,
        objects: Mapping[int, ObjectSource],
        object_sets: Mapping[int, ObjectSetSource] | None = None,
    ) -> None:
        self.objects = dict(objects)
        self.object_sets = dict(object_sets or {})
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
        return cls(
            load_object_sources(area_directory),
            load_object_set_sources(area_directory),
        )

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
    return _stance_score_from_totals(
        bonuses,
        stance,
        level_gain_priorities=level_gain_priorities,
        armor=item.values[0] if item.item_type == 9 and item.values else 0,
        weapon=weapon_damage_score(item),
    )


def _stance_score_from_totals(
    bonuses: Mapping[int, int],
    stance: str,
    *,
    level_gain_priorities: tuple[str, ...],
    armor: int = 0,
    weapon: int = 0,
    aggregate_combat: bool = False,
) -> tuple[int, ...]:
    stats = sum(max(0, bonuses.get(location, 0)) for location in APPLY_STATS)
    damroll = max(0, bonuses.get(APPLY_DAMROLL, 0))
    hitroll = max(0, bonuses.get(APPLY_HITROLL, 0))
    swiftness = max(0, bonuses.get(APPLY_SWIFTNESS, 0))
    critical = max(0, bonuses.get(APPLY_CRIT, 0))
    hitpoints = max(0, bonuses.get(APPLY_HIT, 0))
    mana = max(0, bonuses.get(APPLY_MANA, 0))
    recovery = hitpoints + mana
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
    direct_damage = (
        weapon + 2 * damroll
        if aggregate_combat or weapon
        else damroll
    )
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


def is_releasable_funding_item(item: ObjectSource) -> bool:
    """Return whether a source loot object can safely become sale proceeds."""
    blocked_flags = (
        ITEM_NODROP
        | ITEM_NOREMOVE
        | ITEM_INVENTORY
        | ITEM_BODY_PART
        | ITEM_CURSED
    )
    return not bool(item.extra_flags & blocked_flags)


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


def _independent_loadout(
    carried: Sequence[ObjectSource],
    worn: Sequence[ObjectSource],
    stance: str,
    *,
    level_gain_priorities: tuple[str, ...],
    weapon_preference: str | None,
) -> dict[str, tuple[ObjectSource, ...]]:
    categories = {
        category
        for item in (*carried, *worn)
        if (category := item_category(item)) is not None
    }
    loadout: dict[str, tuple[ObjectSource, ...]] = {}
    for category in sorted(categories):
        current = [item for item in worn if item_category(item) == category]
        available = [item for item in carried if item_category(item) == category]
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
        loadout[category] = tuple(item for item, _ in ranked if item is not None)
    return loadout


def _category_options(
    items: Sequence[ObjectSource],
    category: str,
) -> tuple[tuple[ObjectSource, ...], ...]:
    eligible = [
        item
        for item in items
        if item_category(item) == category
        and not is_strength_penalty_ring(item)
        and not any(
            location in APPLY_STATS and modifier < 0
            for location, modifier in item.affects
        )
    ]
    count = min(_CATEGORY_CAPACITY.get(category, 1), len(eligible))
    if count == 0:
        return ((),)
    options: dict[tuple[int, ...], tuple[ObjectSource, ...]] = {}
    for indices in combinations(range(len(eligible)), count):
        option = tuple(eligible[index] for index in indices)
        key = tuple(sorted(item.vnum for item in option))
        options.setdefault(key, option)
    return tuple(options[key] for key in sorted(options))


def _loadout_items(
    loadout: Mapping[str, Sequence[ObjectSource]],
) -> tuple[ObjectSource, ...]:
    return tuple(
        item
        for category in sorted(loadout)
        for item in loadout[category]
    )


def _loadout_bonus_totals(
    items: Sequence[ObjectSource],
    object_sets: Sequence[ObjectSetSource],
) -> dict[int, int]:
    totals: dict[int, int] = {}
    for item in items:
        for location, modifier in item.affects:
            totals[location] = totals.get(location, 0) + modifier

    worn_vnums = {item.vnum for item in items}
    for object_set in object_sets:
        distinct_count = len(worn_vnums.intersection(object_set.object_vnums))
        for bonus in object_set.bonuses:
            if distinct_count >= bonus.required_count:
                totals[bonus.location] = (
                    totals.get(bonus.location, 0) + bonus.modifier
                )
    return totals


def _loadout_rank(
    loadout: Mapping[str, Sequence[ObjectSource]],
    *,
    stance: str,
    level_gain_priorities: tuple[str, ...],
    weapon_preference: str | None,
    object_sets: Sequence[ObjectSetSource],
    worn: Sequence[ObjectSource],
    current_strength: int | None,
) -> tuple[object, ...]:
    items = _loadout_items(loadout)
    bonuses = _loadout_bonus_totals(items, object_sets)
    if current_strength is not None:
        current_bonuses = _loadout_bonus_totals(worn, object_sets)
        strength_delta = bonuses.get(1, 0) - current_bonuses.get(1, 0)
        old_strength = max(3, min(len(_STR_APP) - 1, current_strength))
        new_strength = max(
            3,
            min(len(_STR_APP) - 1, current_strength + strength_delta),
        )
        bonuses[APPLY_HITROLL] = bonuses.get(APPLY_HITROLL, 0) + (
            _STR_APP[new_strength][0] - _STR_APP[old_strength][0]
        )
        bonuses[APPLY_DAMROLL] = bonuses.get(APPLY_DAMROLL, 0) + (
            _STR_APP[new_strength][1] - _STR_APP[old_strength][1]
        )

    preferred_weapon = sum(
        item_category(item) == "wield"
        and (
            weapon_preference == "piercing"
            and is_piercing_weapon(item)
            or weapon_preference == "blunt"
            and is_blunt_weapon(item)
        )
        for item in items
    )
    score = _stance_score_from_totals(
        bonuses,
        stance,
        level_gain_priorities=level_gain_priorities,
        armor=sum(
            item.values[0]
            for item in items
            if item.item_type == 9 and item.values
        ),
        weapon=sum(weapon_damage_score(item) for item in items),
        aggregate_combat=True,
    )
    desired_counts = Counter(item.vnum for item in items)
    worn_counts = Counter(item.vnum for item in worn)
    retained = sum((desired_counts & worn_counts).values())
    deterministic = tuple(-item.vnum for item in sorted(items, key=lambda item: item.vnum))
    return (
        preferred_weapon,
        *score,
        len(items),
        retained,
        deterministic,
    )


def _force_set_members(
    loadout: Mapping[str, tuple[ObjectSource, ...]],
    members: Sequence[ObjectSource],
    category_options: Mapping[str, tuple[tuple[ObjectSource, ...], ...]],
    rank,
) -> dict[str, tuple[ObjectSource, ...]] | None:
    forced_by_category: dict[str, set[int]] = {}
    for item in members:
        category = item_category(item)
        if category is None:
            return None
        forced_by_category.setdefault(category, set()).add(item.vnum)

    result = dict(loadout)
    for category, required_vnums in forced_by_category.items():
        matching = [
            option
            for option in category_options[category]
            if required_vnums.issubset({item.vnum for item in option})
        ]
        if not matching:
            return None
        result[category] = max(
            matching,
            key=lambda option: rank({**result, category: option}),
        )
    return result


def _desired_loadout(
    carried: Sequence[ObjectSource],
    worn: Sequence[ObjectSource],
    stance: str,
    *,
    level_gain_priorities: tuple[str, ...],
    weapon_preference: str | None,
    object_sets: Sequence[ObjectSetSource],
    current_strength: int | None,
) -> dict[str, tuple[ObjectSource, ...]]:
    baseline = _independent_loadout(
        carried,
        worn,
        stance,
        level_gain_priorities=level_gain_priorities,
        weapon_preference=weapon_preference,
    )
    if not object_sets:
        return baseline

    all_items = (*carried, *worn)
    available_by_vnum = {item.vnum: item for item in all_items}
    relevant_sets = [
        object_set
        for object_set in object_sets
        if object_set.bonuses
        and len(set(object_set.object_vnums).intersection(available_by_vnum))
        >= min(bonus.required_count for bonus in object_set.bonuses)
    ]
    if not relevant_sets:
        return baseline

    category_options = {
        category: _category_options(all_items, category)
        for category in baseline
    }
    rank = lambda loadout: _loadout_rank(
        loadout,
        stance=stance,
        level_gain_priorities=level_gain_priorities,
        weapon_preference=weapon_preference,
        object_sets=object_sets,
        worn=worn,
        current_strength=current_strength,
    )

    def optimize(
        seed: Mapping[str, tuple[ObjectSource, ...]],
    ) -> dict[str, tuple[ObjectSource, ...]]:
        result = dict(seed)
        changed = True
        while changed:
            changed = False
            for category in sorted(category_options):
                best = max(
                    category_options[category],
                    key=lambda option: rank({**result, category: option}),
                )
                if best != result.get(category, ()):
                    trial = {**result, category: best}
                    if rank(trial) > rank(result):
                        result = trial
                        changed = True
        return result

    seeds: list[dict[str, tuple[ObjectSource, ...]]] = [optimize(baseline)]
    for object_set in relevant_sets:
        member_items = [
            available_by_vnum[vnum]
            for vnum in object_set.object_vnums
            if vnum in available_by_vnum
        ]
        expanded = list(seeds)
        for seed in seeds:
            for required_count in sorted(
                {bonus.required_count for bonus in object_set.bonuses}
            ):
                for members in combinations(member_items, required_count):
                    forced = _force_set_members(
                        seed,
                        members,
                        category_options,
                        rank,
                    )
                    if forced is not None:
                        expanded.append(optimize(forced))
        deduplicated = {
            tuple(
                (category, tuple(item.vnum for item in loadout[category]))
                for category in sorted(loadout)
            ): loadout
            for loadout in expanded
        }
        seeds = sorted(deduplicated.values(), key=rank, reverse=True)[:256]
    return max(seeds, key=rank)


def plan_stance(
    carried: Iterable[ObjectSource],
    worn: Iterable[ObjectSource],
    stance: str,
    *,
    character_level: int | None = None,
    level_gain_priorities: tuple[str, ...] = (),
    weapon_preference: str | None = None,
    object_sets: Iterable[ObjectSetSource] = (),
    current_strength: int | None = None,
) -> list[GearChoice]:
    """Return carried items that should replace or fill the current gear set."""
    carried_items = [
        item
        for item in carried
        if character_level is None or item.effective_level <= character_level
    ]
    worn_items = list(worn)
    desired = _desired_loadout(
        carried_items,
        worn_items,
        stance,
        level_gain_priorities=level_gain_priorities,
        weapon_preference=weapon_preference,
        object_sets=tuple(object_sets),
        current_strength=current_strength,
    )
    worn_counts = Counter(item.vnum for item in worn_items)
    selected_worn: Counter[int] = Counter()
    choices: list[GearChoice] = []
    for category in sorted(desired):
        for item in desired[category]:
            if selected_worn[item.vnum] < worn_counts[item.vnum]:
                selected_worn[item.vnum] += 1
            else:
                choices.append(GearChoice(item, category, False))
    return choices


def plan_stance_swaps(
    carried: Iterable[ObjectSource],
    worn: Iterable[ObjectSource],
    stance: str,
    *,
    level_gain_priorities: tuple[str, ...] = (),
    weapon_preference: str | None = None,
    object_sets: Iterable[ObjectSetSource] = (),
    current_strength: int | None = None,
) -> tuple[list[ObjectSource], list[ObjectSource]]:
    """Return worn removals and carried additions needed for a stance."""
    carried_items = list(carried)
    worn_items = list(worn)
    desired_loadout = _desired_loadout(
        carried_items,
        worn_items,
        stance,
        level_gain_priorities=level_gain_priorities,
        weapon_preference=weapon_preference,
        object_sets=tuple(object_sets),
        current_strength=current_strength,
    )
    desired = _loadout_items(desired_loadout)
    removals: list[ObjectSource] = []
    additions: list[ObjectSource] = []
    desired_counts = Counter(item.vnum for item in desired)
    kept_counts: Counter[int] = Counter()
    for item in worn_items:
        if kept_counts[item.vnum] < desired_counts[item.vnum]:
            kept_counts[item.vnum] += 1
        else:
            removals.append(item)
    worn_counts = Counter(item.vnum for item in worn_items)
    added_counts: Counter[int] = Counter()
    for item in desired:
        needed = max(0, desired_counts[item.vnum] - worn_counts[item.vnum])
        if added_counts[item.vnum] < needed:
            additions.append(item)
            added_counts[item.vnum] += 1
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
