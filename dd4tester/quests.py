"""Source-backed helpers for DD4 random quest progression.

The quest command is deliberately kept separate from ordinary XP policy.  A
quest target is selected by the live server, so the campaign must preserve
the GMCP identity and route from that evidence rather than guessing from a
name or a remembered room.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


QUESTMASTER_MAX_LEVEL = 25
QUESTMASTER_VNUM = 25305
QUESTMASTER_ROOM_VNUM = 25306
QUESTMASTER_ROUTE_FROM_RECALL = (
    "south",
    "east",
    "up",
    "east",
    "north",
    "down",
    "down",
)

# The checked-in source graph identifies Goldmoon (mobile 10001) in room
# 10024 as the next ordinary questmaster after Suturb.  Keep this route
# explicit, like the other maintained fastwalks, so a source revision can be
# audited and replaced without turning quest travel into name-based guessing.
GOLDMOON_QUESTMASTER_VNUM = 10001
GOLDMOON_QUESTMASTER_ROOM_VNUM = 10024
GOLDMOON_QUESTMASTER_ROUTE_FROM_RECALL = (
    "south",
    "south",
    "south",
    "south",
    "south",
    "south",
    "west",
    "south",
    "south",
    "west",
    "south",
    "west",
    "south",
    "south",
    "west",
    "south",
    "south",
    "open south",
    "south",
    "south",
    "south",
    "south",
    "south",
    "south",
    "west",
    "west",
    "south",
    "south",
    "south",
    "west",
    "west",
    "south",
    "south",
    "south",
    "south",
    "south",
    "west",
    "north",
    "west",
    "south",
    "south",
    "west",
    "south",
    "down",
    "west",
    "south",
    "south",
    "west",
)

# Source: server/src/update.c, questpoints_required_for_advance().  The
# server checks the character's current level before granting the next level.
# The older level-69 reminder in act_info.c is display-only and disagrees with
# the executable advancement check; update.c is authoritative here.
QUEST_LEVEL_QP_REQUIREMENTS = {
    29: 1,
    49: 200,
    79: 500,
    99: 1000,
}

# Source: server/src/quest.c, generate_quest(). The comparison is strictly
# ``level_diff < upper_limit``, so the largest legal nominal target offset is
# one less than each band limit.
QUEST_TARGET_MAXIMUM_LEVEL_OFFSETS = (
    (20, 4),
    (50, 9),
    (80, 14),
    (101, 19),
)

# Source: server/src/quest.c, generate_quest(). Keep this separate from
# ordinary hunt eligibility: some of these mobiles remain valid XP targets,
# but the live quest generator will never select them.
QUEST_MOBILE_INELIGIBLE_ACT_FLAGS = sum(
    1 << bit
    for bit in (3, 8, 9, 10, 13, 15, 16, 17, 19, 24)
)

# Source: server/src/act_obj.c and grave.are. The two low-level digging
# implements reset on the ground in room 3613; the shovel is the primary
# deterministic acquisition target and the rake remains a source-documented
# fallback for a future alternative-item route.
QUEST_DIGGING_TOOL_OBJECT_VNUM = 3604
QUEST_DIGGING_TOOL_FALLBACK_OBJECT_VNUM = 3605
QUEST_DIGGING_TOOL_ROOM_VNUM = 3613
QUEST_DIGGING_TOOL_KEYWORD = "shovel"


def quest_points_required_for_advance(level: int) -> int:
    """Return DD4's source-defined total quest points for the next level."""
    try:
        normalized_level = int(level)
    except (TypeError, ValueError):
        return 0
    return QUEST_LEVEL_QP_REQUIREMENTS.get(normalized_level, 0)


def quest_points_shortfall_for_advance(level: int, total_points: int) -> int:
    """Return the missing total quest points at a source-defined gate."""
    try:
        normalized_total = int(total_points)
    except (TypeError, ValueError):
        normalized_total = 0
    return max(0, quest_points_required_for_advance(level) - normalized_total)


def quest_target_maximum_level_offset(level: int) -> int:
    """Return the largest nominal mobile-level offset DD4 can quest-select."""
    try:
        normalized_level = int(level)
    except (TypeError, ValueError) as exc:
        raise ValueError("quest levels must be integers from 1 through 100") from exc
    if not 1 <= normalized_level <= 100:
        raise ValueError("quest levels must be integers from 1 through 100")
    for upper_level, offset in QUEST_TARGET_MAXIMUM_LEVEL_OFFSETS:
        if normalized_level < upper_level:
            return offset
    raise AssertionError("quest target level bands are incomplete")


def quest_mobile_is_source_eligible(
    mobile: Any,
    *,
    is_shopkeeper: bool = False,
) -> bool:
    """Mirror generate_quest()'s prototype exclusions for a source mobile."""
    if is_shopkeeper:
        return False
    return not bool(
        int(getattr(mobile, "act_flags", 0))
        & QUEST_MOBILE_INELIGIBLE_ACT_FLAGS
    )


@dataclass(frozen=True)
class QuestSnapshot:
    """Normalized live quest fields used by the campaign selector."""

    active: bool
    complete: bool
    kind: str
    countdown: int
    nextquest: int
    points: int
    total_points: int
    mob_vnum: int
    object_vnum: int
    room_vnum: int
    target_name: str
    area_name: str

    @property
    def needs_target_run(self) -> bool:
        return self.active and not self.complete and self.kind in {
            "kill",
            "object",
            "retrieve",
            "hoard",
        }


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def snapshot_quest_status(status: Mapping[str, Any] | None) -> QuestSnapshot:
    """Return a stable snapshot even when an older checkpoint lacks fields."""
    data = status or {}
    mob_vnum = _int(data.get("mob_vnum"))
    object_vnum = _int(data.get("object_vnum"))
    active = bool(data.get("active")) or mob_vnum > 0 or object_vnum > 0
    complete = bool(data.get("complete")) or mob_vnum == -1
    kind = str(data.get("type") or "none").strip().casefold()
    if kind == "none" and mob_vnum:
        kind = "kill"
    elif kind == "none" and object_vnum:
        kind = "object"
    return QuestSnapshot(
        active=active,
        complete=complete,
        kind=kind,
        countdown=_int(data.get("countdown")),
        nextquest=_int(data.get("nextquest")),
        points=_int(data.get("points")),
        total_points=_int(data.get("total_points")),
        mob_vnum=mob_vnum,
        object_vnum=object_vnum,
        room_vnum=_int(data.get("room_vnum")),
        target_name=str(data.get("target_name") or "").strip(),
        area_name=str(data.get("area_name") or "").strip(),
    )


def questmaster_name_for_level(level: int) -> str:
    """Return the source-registered questmaster for the current level band."""
    if level < 1 or level > 100:
        raise ValueError("questmaster routes are registered for levels 1 through 100")
    return "Suturb" if level <= QUESTMASTER_MAX_LEVEL else "Goldmoon"


def questmaster_route_for_level(level: int) -> tuple[str, ...]:
    """Return a source-registered route for the current questmaster band."""
    if level < 1 or level > 100:
        raise ValueError("questmaster routes are registered for levels 1 through 100")
    if level <= QUESTMASTER_MAX_LEVEL:
        return QUESTMASTER_ROUTE_FROM_RECALL
    return GOLDMOON_QUESTMASTER_ROUTE_FROM_RECALL


def quest_object_keyword(world: Any, object_vnum: int) -> str | None:
    """Choose the source-listed keyword for a generated quest object."""
    item = getattr(world, "objects", {}).get(int(object_vnum))
    if item is None:
        return None
    words = str(item.keywords or "").split()
    if not words:
        return None
    # Generated quest objects use a common type word plus a distinctive name.
    # Prefer the first word that is not a generic object category.
    generic = {
        "amulet",
        "bowl",
        "book",
        "coin",
        "scroll",
        "tome",
        "wooden",
        "ivory",
        "ripped",
        "ancient",
        "cities",
        "city",
    }
    return next((word for word in words if word.casefold() not in generic), words[0])
