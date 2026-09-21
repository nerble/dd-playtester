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

# Source: server/src/quest.c and server/src/merc.h.  The command index is the
# same as the persistent pfile slot, so it is the stable identifier used by
# ``recall set <index>`` and by the server's recall array.  Slot 1 is reserved
# for clan recall and is intentionally absent from this purchase table.
DEFAULT_RECALL_POINT = "default"
QUEST_RECALL_POINTS = (
    # index, quest point cost, destination room, purchase name
    (2, 1000, 28003, "Draagdim"),
    (10, 1000, 3101, "Midgaard"),
    (12, 900, 21500, "Demondium"),
    (3, 800, 30050, "Krondor"),
    (4, 500, 31000, "Anon"),
    (5, 500, 29153, "Freeport"),
    (6, 500, 18835, "Dahij"),
    (16, 500, 28503, "Omu"),
    (13, 400, 1313, "HighTower"),
    (14, 400, 27347, "Ota'ar Dar"),
    (15, 400, 16084, "Underdark"),
    (7, 300, 30234, "Kerofk"),
    (11, 250, 12167, "Westreen"),
    (8, 200, 10201, "Solace"),
    (9, 100, 601, "Ofcol"),
)


@dataclass(frozen=True)
class RecallPoint:
    """One source-defined usable or purchasable recall destination."""

    index: int
    cost: int
    room_vnum: int
    name: str


_DEFAULT_RECALL_POINT = RecallPoint(
    index=0,
    cost=0,
    room_vnum=3001,
    name="Default recall",
)
_QUEST_RECALL_POINT_OBJECTS = tuple(
    RecallPoint(index=index, cost=cost, room_vnum=room_vnum, name=name)
    for index, cost, room_vnum, name in QUEST_RECALL_POINTS
)
_RECALL_POINTS_BY_INDEX = {
    point.index: point
    for point in (_DEFAULT_RECALL_POINT, *_QUEST_RECALL_POINT_OBJECTS)
}


def recall_points_for_purchase() -> tuple[RecallPoint, ...]:
    """Return the fifteen destinations offered by ``quest list``."""
    return _QUEST_RECALL_POINT_OBJECTS


def recall_point_for_index(index: int) -> RecallPoint | None:
    """Return the source destination for a ``recall set`` index."""
    try:
        normalized_index = int(index)
    except (TypeError, ValueError):
        return None
    return _RECALL_POINTS_BY_INDEX.get(normalized_index)


def recall_origins_from_state(state: Mapping[str, Any]) -> dict[int, int]:
    """Return source-known recall origins recorded by a live character state."""
    origins = {0: _DEFAULT_RECALL_POINT.room_vnum}
    raw_points = state.get("recall_points")
    if isinstance(raw_points, (list, tuple)):
        for raw_point in raw_points:
            if not isinstance(raw_point, Mapping):
                continue
            try:
                index = int(raw_point.get("index"))
            except (TypeError, ValueError):
                continue
            point = recall_point_for_index(index)
            if point is not None:
                origins[index] = point.room_vnum
    try:
        current_recall = int(state.get("current_recall", 0) or 0)
    except (TypeError, ValueError):
        current_recall = 0
    point = recall_point_for_index(current_recall)
    if point is not None:
        origins[current_recall] = point.room_vnum
    return origins


def _normalize_recall_name(value: Any) -> str:
    return " ".join(
        str(value).replace("\u2019", "'").casefold().split()
    )


def recall_point_for_name(name: str) -> RecallPoint | None:
    """Return a source destination by its command or live-list name."""
    normalized = _normalize_recall_name(name)
    if normalized == _normalize_recall_name(_DEFAULT_RECALL_POINT.name):
        return _DEFAULT_RECALL_POINT
    for point in _QUEST_RECALL_POINT_OBJECTS:
        if normalized == _normalize_recall_name(point.name):
            return point
    return None


def next_recall_point_to_buy(
    available_points: Any,
    quest_points: Any,
    *,
    character_level: int,
) -> RecallPoint | None:
    """Choose the most valuable affordable remote recall after level 25.

    The live ``recall list`` is the ownership proof.  Keep quest points for
    ordinary progression until the character can buy a meaningful remote
    origin; among affordable points, prefer the highest-cost destination so
    a small balance is not spent on a low-band convenience point.
    """
    if character_level < QUESTMASTER_MAX_LEVEL:
        return None
    if not isinstance(available_points, (list, tuple)):
        return None
    owned: set[int] = set()
    for raw_point in available_points:
        if not isinstance(raw_point, Mapping):
            continue
        try:
            index = int(raw_point.get("index"))
        except (TypeError, ValueError):
            continue
        if recall_point_for_index(index) is not None:
            owned.add(index)
    try:
        spendable = int(quest_points)
    except (TypeError, ValueError):
        return None
    if spendable < 0:
        return None
    affordable = [
        point
        for point in _QUEST_RECALL_POINT_OBJECTS
        if point.index not in owned and point.cost <= spendable
    ]
    return max(
        affordable,
        key=lambda point: (point.cost, -point.index),
        default=None,
    )


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


def fame_from_state(state: Mapping[str, Any]) -> int | None:
    """Return GMCP ``Char.Stats`` fame without confusing it with alignment."""
    stats = state.get("stats")
    if isinstance(stats, Mapping):
        fame = stats.get("fame")
        try:
            return int(fame)
        except (TypeError, ValueError):
            pass
    fame = state.get("fame")
    try:
        return int(fame) if fame is not None else None
    except (TypeError, ValueError):
        return None


def quest_request_fame_allowed(state: Mapping[str, Any]) -> bool:
    """Return whether a fresh quest request passes DD4's fame gate."""
    fame = fame_from_state(state)
    return fame is not None and fame >= 0


def quest_request_blocker(
    state: Mapping[str, Any],
    *,
    quest: QuestSnapshot | None = None,
) -> str | None:
    """Explain why ``quest request`` cannot be issued on this state."""
    current = quest or snapshot_quest_status(
        state.get("quest_status")
        if isinstance(state.get("quest_status"), Mapping)
        else None
    )
    if current.active:
        return "a quest is already active"
    if current.nextquest > 0:
        return f"quest cooldown has {current.nextquest} minute(s) remaining"
    fame = fame_from_state(state)
    if fame is None:
        return "live fame is unavailable; do not request a quest"
    if fame < 0:
        return "DD4 rejects new quest requests while fame is below zero"
    return None


def quest_fame_recovery_status(
    state: Mapping[str, Any],
    *,
    quest: QuestSnapshot | None = None,
) -> str:
    """Describe the source-backed fame outcome of the quest path."""
    current = quest or snapshot_quest_status(
        state.get("quest_status")
        if isinstance(state.get("quest_status"), Mapping)
        else None
    )
    fame = fame_from_state(state)
    if current.active and current.complete and current.kind == "kill":
        return "this completed kill quest awards a positive fuzzy fame reward"
    if fame is None:
        return "unavailable: live fame is unknown"
    if fame < 0:
        if current.active and current.kind == "kill":
            return (
                "fresh requests are blocked below zero fame, but this active "
                "kill quest can award positive fuzzy fame on completion"
            )
        return "blocked: DD4 rejects new quest requests while fame is below zero"
    return (
        "only a completed kill quest awards positive fuzzy fame; object, "
        "retrieve, and hoard quests award no fame"
    )


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
