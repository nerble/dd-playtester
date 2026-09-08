"""Source-backed teacher capacity and DD4 practice gain calculations."""

from __future__ import annotations

import re
from collections.abc import Mapping

from .dd4_catalog import _initializer_rows, _strings


def parse_skill_groups(text: str) -> dict[str, tuple[tuple[str, int], ...]]:
    """Resolve const.c skill-group membership using its real GSN names."""
    text = re.sub(
        r'("(?:\\.|[^"\\])*")|/\*.*?\*/|//[^\r\n]*',
        lambda match: match.group(1) or "", text, flags=re.DOTALL,
    )
    names = {}
    for row in _initializer_rows(text, "skill_table"):
        symbol = re.search(r"&gsn_(\w+)", row)
        strings = _strings(row)
        if symbol and strings:
            names[symbol.group(1)] = strings[0].strip().casefold()
    declaration = re.search(r"\bspell_groups\s*\[[^]]+\]\s*=\s*\{([^}]*)\}", text)
    if declaration is None:
        raise ValueError("DD4 source does not define spell_groups")
    groups = re.findall(r"&gsn_(\w+)", declaration.group(1))
    if not groups:
        raise ValueError("DD4 source has no skill groups")
    group_index = 0
    current_group = None
    memberships: dict[str, list[tuple[str, int]]] = {}
    rows = _initializer_rows(text, "spell_group_table")
    for row_index, row in enumerate(rows):
        match = re.fullmatch(r"\{\s*&gsn_(\w+)\s*,\s*(\d+)\s*\}", row.strip())
        if match is None:
            raise ValueError("unsupported DD4 skill-group entry")
        symbol, minimum = match.groups()
        if symbol in groups:
            if group_index >= len(groups) or symbol != groups[group_index]:
                raise ValueError("DD4 skill-group order is inconsistent")
            current_group = names.get(symbol)
            if current_group is None:
                if not (
                    symbol == "group_last" and group_index == len(groups) - 1
                    and row_index == len(rows) - 1
                ):
                    raise ValueError(f"DD4 skill group {symbol} has no skill-table name")
            group_index += 1
        elif symbol in names:
            if current_group is None:
                raise ValueError("DD4 skill member precedes its group")
            memberships.setdefault(names[symbol], []).append((current_group, int(minimum)))
    if group_index != len(groups):
        raise ValueError("DD4 skill-group table is incomplete")
    return {skill: tuple(groups) for skill, groups in memberships.items()}


def teacher_capacity(
    teachings: Mapping[str, int], skill: str,
    skill_groups: Mapping[str, tuple[tuple[str, int], ...]],
) -> int | None:
    """Mirror do_practice's explicit skill override, then has_groups minimum."""
    direct = teachings.get(skill, 0)
    if direct:
        return direct
    memberships = skill_groups.get(skill)
    if not memberships:
        return None
    capacities = []
    for group, minimum in memberships:
        capacity = teachings.get(group, 0)
        if capacity < minimum:
            return None
        capacities.append(capacity)
    return min(capacities)


def _stat(stats: Mapping[str, object], name: str) -> int | None:
    raw = stats.get(f"{name}_mod", stats.get(name))
    if isinstance(raw, bool) or not isinstance(raw, (int, str)):
        return None
    try:
        value = int(raw)
    except ValueError:
        return None
    return value if 1 <= value <= 100 else None


def practice_gain(
    current: int, capacity: int | None, practice_type: str,
    stats: Mapping[str, object],
) -> int | None:
    """Return the next percentage only when DD4 can accept this practice."""
    if (
        isinstance(current, bool) or not isinstance(current, int)
        or not 0 <= current < 100
        or isinstance(capacity, bool) or not isinstance(capacity, int)
        or not 1 <= capacity <= 100
    ):
        return None
    intelligence = _stat(stats, "int")
    if practice_type == "physical":
        strength, dexterity = _stat(stats, "str"), _stat(stats, "dex")
        if None in (intelligence, strength, dexterity):
            return None
        penalty = 30 - (strength + dexterity + 2 * intelligence) // 4
    elif practice_type == "intellectual":
        wisdom = _stat(stats, "wis")
        if None in (intelligence, wisdom):
            return None
        penalty = 30 - (wisdom + 2 * intelligence) // 3
    else:
        return None
    if capacity - 1 <= current + penalty:
        return None
    return min(100, (current - penalty + capacity) // 2)
