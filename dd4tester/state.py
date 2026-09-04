from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field, fields
from typing import Any, Iterable

from .observations import GameEvent


_MAX_CHARACTER_LEVEL = 100

_DIRECTION_NAMES = {
    "n": "north",
    "e": "east",
    "s": "south",
    "w": "west",
    "u": "up",
    "d": "down",
}


def _canonical_direction(value: Any) -> str:
    normalized = str(value).casefold()
    return _DIRECTION_NAMES.get(normalized, normalized)


@dataclass
class CharacterState:
    schema_version: int = field(default=1, init=False)
    revision: int = 0
    name: str | None = None
    race: str | None = None
    character_class: str | None = None
    subclass: str | None = None
    sex: str | int | None = None
    level: int | None = None
    xp: int | None = None
    max_xp: int | None = None
    xp_to_next_level: int | None = None
    practice: int | None = None
    hp: int | float | None = None
    max_hp: int | float | None = None
    mana: int | float | None = None
    max_mana: int | float | None = None
    move: int | float | None = None
    max_move: int | float | None = None
    rage: int | float | None = None
    max_rage: int | float | None = None
    hunger: int | float | None = None
    max_hunger: int | float | None = None
    thirst: int | float | None = None
    max_thirst: int | float | None = None
    drunk: int | float | None = None
    max_drunk: int | float | None = None
    position: str | int | None = None
    form: str | None = None
    room_name: str | None = None
    room_vnum: str | None = None
    area: str | None = None
    sector: str | None = None
    room_flags: list[str] = field(default_factory=list)
    exits: dict[str, str | None] = field(default_factory=dict)
    stats: dict[str, Any] = field(default_factory=dict)
    progress: dict[str, Any] = field(default_factory=dict)
    progress_source: str | None = None
    xp_loss_observed: bool = False
    xp_loss_total: int = 0
    currencies: dict[str, int | float] = field(default_factory=dict)
    inventory: Any = None
    equipment: Any = None
    affects: Any = None
    enemies: Any = None
    quests: list[dict[str, Any]] = field(default_factory=list)
    quest_status: dict[str, Any] = field(default_factory=dict)
    quest_points: int | None = None
    total_quest_points: int | None = None
    quest_level_qp_required: int | None = None
    quest_level_qp_shortfall: int | None = None
    recall_points: list[dict[str, Any]] = field(default_factory=list)
    recall_points_observed: bool = False
    current_recall: int = 0
    acquired_items: list[dict[str, Any]] = field(default_factory=list)
    last_prompt: dict[str, Any] = field(default_factory=dict)
    in_combat: bool = False
    combat_target: str | None = None
    dead: bool = False

    def apply(self, event: GameEvent) -> bool:
        before = self._content()
        self._apply(event)
        if self._content() == before:
            return False
        self.revision += 1
        return True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CharacterState":
        accepted = {item.name for item in fields(cls) if item.init}
        values = {key: deepcopy(value) for key, value in data.items() if key in accepted}
        if (
            "recall_points_observed" not in values
            and isinstance(values.get("recall_points"), list)
            and values["recall_points"]
        ):
            # Older checkpoints only persisted the parsed list. Its presence
            # is sufficient evidence that the live recall command completed.
            values["recall_points_observed"] = True
        return cls(**values)

    def _content(self) -> dict[str, Any]:
        content = self.to_dict()
        content.pop("revision")
        return content

    def _apply(self, event: GameEvent) -> None:
        data = event.data
        if event.type == "character_identity_observed":
            self.name = _text(data.get("name"))
            self.race = _text(data.get("race"))
            self.character_class = _text(data.get("class"))
            self.subclass = _text(data.get("subclass"))
            self.sex = _scalar(data.get("sex"))
            return

        if event.type == "vitals_changed":
            self.hp = _number(data.get("hp"), self.hp)
            self.max_hp = _number(data.get("maxhp"), self.max_hp)
            self.mana = _number(data.get("mana"), self.mana)
            self.max_mana = _number(data.get("maxmana"), self.max_mana)
            self.move = _number(data.get("move"), self.move)
            self.max_move = _number(data.get("maxmove"), self.max_move)
            self.rage = _number(data.get("rage"), self.rage)
            self.max_rage = _number(data.get("maxrage"), self.max_rage)
            self.hunger = _number(data.get("hunger"), self.hunger)
            self.max_hunger = _number(data.get("maxhunger"), self.max_hunger)
            self.thirst = _number(data.get("thirst"), self.thirst)
            self.max_thirst = _number(data.get("maxthirst"), self.max_thirst)
            self.drunk = _number(data.get("drunk"), self.drunk)
            self.max_drunk = _number(data.get("maxdrunk"), self.max_drunk)
            self.position = _scalar(data.get("position"), self.position)
            self.form = _text(data.get("form"), self.form)
            return

        if event.type == "health_changed":
            self.hp = _number(data.get("current"), self.hp)
            self.max_hp = _number(data.get("maximum"), self.max_hp)
            return

        if event.type == "stats_changed":
            self.stats = _payload(data)
            return

        if event.type == "experience_lost":
            self.xp_loss_observed = True
            amount = max(0, _integer(data.get("xp"), 0) or 0)
            self.xp_loss_total += amount
            if amount == 0:
                return

            # A single DD4 response can contain the authoritative GMCP
            # Char.Worth packet before the textual recall/flee message. In
            # that ordering the packet has already applied this loss; only
            # the evidence counters need updating here.
            pending = getattr(self, "_pending_progress_loss", None)
            if pending is not None:
                pending_amount, previous_xp, previous_xptnl, incoming_xptnl = (
                    pending
                )
                if pending_amount == amount:
                    if (
                        previous_xp is not None
                        and self.xp != previous_xp - amount
                    ):
                        self.xp = max(0, (self.xp or previous_xp) - amount)
                    if (
                        previous_xptnl is not None
                        and self.xp_to_next_level == incoming_xptnl
                        and incoming_xptnl == previous_xptnl
                    ):
                        self.xp_to_next_level += amount
                    if isinstance(self.progress, dict):
                        progress = dict(self.progress)
                        progress_xp = _integer(progress.get("xp"))
                        if (
                            previous_xp is not None
                            and progress_xp != previous_xp - amount
                        ):
                            progress["xp"] = max(
                                0,
                                (progress_xp or previous_xp) - amount,
                            )
                        progress_xptnl = _integer(progress.get("xptnl"))
                        if (
                            previous_xptnl is not None
                            and progress_xptnl == incoming_xptnl
                            and incoming_xptnl == previous_xptnl
                        ):
                            progress["xptnl"] = progress_xptnl + amount
                        self.progress = progress
                    self._pending_progress_loss = None
                    return
            self._pending_progress_loss = None

            # DD4 can report the loss in text without following it with a
            # Char.Worth packet. Keep the durable progress snapshot accurate
            # instead of waiting for the next reconnect to correct the XP.
            known_xp = self.xp
            if known_xp is None and isinstance(self.progress, dict):
                known_xp = _integer(self.progress.get("xp"))
            if known_xp is not None:
                self.xp = max(0, known_xp - amount)

            if self.xp_to_next_level is not None:
                self.xp_to_next_level += amount

            if isinstance(self.progress, dict):
                progress = dict(self.progress)
                progress_xp = _integer(progress.get("xp"))
                if progress_xp is not None:
                    progress["xp"] = max(0, progress_xp - amount)
                progress_xptnl = _integer(progress.get("xptnl"))
                if progress_xptnl is not None:
                    progress["xptnl"] = progress_xptnl + amount
                self.progress = progress
            return

        if event.type == "progress_changed":
            previous_level = self.level
            previous_xp = self.xp
            previous_xptnl = self.xp_to_next_level
            incoming_level = _integer(data.get("level"), self.level)
            incoming_xp = _integer(data.get("xp"), self.xp)
            incoming_max_xp = _integer(data.get("maxxp"), self.max_xp)
            incoming_xp_to_next_level = _integer(
                data.get("xptnl"),
                self.xp_to_next_level,
            )
            if (
                any(
                    key in data
                    for key in ("level", "lvl", "xp", "maxxp", "xptnl")
                )
                and not _valid_progress_values(
                    incoming_level,
                    incoming_xp,
                    incoming_max_xp,
                    incoming_xp_to_next_level,
                )
            ):
                return
            if (
                event.source == "gmcp"
                and self.progress_source == "text"
                and not self.dead
                and not self.xp_loss_observed
                and incoming_level == self.level
                and incoming_xp is not None
                and self.xp is not None
                and incoming_xp < self.xp
            ):
                # A stale login-style GMCP snapshot can arrive after a
                # textual score response. A same-level XP regression is not a
                # valid progression update unless death or explicit DD4 loss
                # evidence has been observed.
                return

            payload = _payload(data)
            if event.source == "text":
                self.progress = {**self.progress, **payload}
                self.progress_source = "text"
            else:
                self.progress = payload
                self.progress_source = "gmcp"
            self.level = incoming_level
            self.xp = incoming_xp
            self.max_xp = incoming_max_xp
            self.xp_to_next_level = incoming_xp_to_next_level
            if (
                not self.xp_loss_observed
                and previous_xp is not None
                and incoming_xp is not None
                and incoming_level == previous_level
                and incoming_xp < previous_xp
            ):
                self._pending_progress_loss = (
                    previous_xp - incoming_xp,
                    previous_xp,
                    previous_xptnl,
                    incoming_xp_to_next_level,
                )
            else:
                self._pending_progress_loss = None
            self.practice = _integer(data.get("practice"), self.practice)
            currency_names = (
                "platinum",
                "gold",
                "silver",
                "copper",
                "steel",
                "titanium",
                "adamantite",
                "electrum",
                "starmetal",
            )
            currency_values = {
                name: value
                for name in currency_names
                if (value := _number(data.get(name))) is not None
            }
            if currency_values:
                self.currencies = currency_values
            return

        if event.type == "level_gained":
            incoming_level = _integer(data.get("level"), self.level)
            if incoming_level is not None and not _valid_progress_values(
                incoming_level,
                None,
                None,
                None,
            ):
                return
            self.level = incoming_level
            return

        if event.type == "posture_changed":
            self.position = _scalar(data.get("position"), self.position)
            return

        if event.type in {"room_entered", "room_updated"}:
            previous_area = self.area
            text_vnum = _text(data.get("vnum"))
            if (
                event.source == "text"
                and text_vnum is not None
                and self.room_vnum is not None
                and text_vnum != str(self.room_vnum)
                and data.get("vnum_inferred") is not True
            ):
                # A delayed text room line can describe the room before a
                # newer GMCP update. Never move a confirmed state backward.
                return
            self.room_name = _text(data.get("name"), self.room_name)
            if event.source == "text" and "vnum" not in data:
                # Text confirms a transition before GMCP can identify its VNUM.
                # Retaining the previous VNUM would combine two different rooms.
                self.room_vnum = None
            else:
                self.room_vnum = _text(data.get("vnum"), self.room_vnum)
            self.area = _text(data.get("area"), self.area)
            if (
                self.dead
                and previous_area is not None
                and previous_area.casefold() == "purgatory"
                and self.area is not None
                and self.area.casefold() != "purgatory"
            ):
                self.dead = False
            self.sector = _text(
                data.get("sector_text", data.get("sector")),
                self.sector,
            )
            flags = data.get("flags")
            if isinstance(flags, str):
                self.room_flags = flags.split()
            elif isinstance(flags, list):
                self.room_flags = [str(flag) for flag in flags]
            exits = data.get("exits")
            if isinstance(exits, dict):
                self.exits = {
                    str(direction): _text(destination)
                    for direction, destination in exits.items()
                }
            elif isinstance(exits, list):
                # Text room output often follows GMCP by a few milliseconds.
                # Keep the richer GMCP destinations instead of replacing them
                # with null placeholders from the text-only exit list.
                cached_destinations = data.get("exit_destinations")
                if isinstance(cached_destinations, dict):
                    known_destinations = {
                        _canonical_direction(direction): _text(destination)
                        for direction, destination in cached_destinations.items()
                        if _text(destination) is not None
                    }
                else:
                    known_destinations = {
                        _canonical_direction(direction): destination
                        for direction, destination in self.exits.items()
                    }
                self.exits = {
                    str(direction): known_destinations.get(
                        _canonical_direction(direction)
                    )
                    for direction in exits
                }
            return

        if event.type == "prompt_seen":
            self.last_prompt = _payload(data, keep_text=True)
            self.hp = _number(data.get("hits"), self.hp)
            self.max_hp = _number(data.get("max_hits"), self.max_hp)
            self.mana = _number(data.get("mana"), self.mana)
            self.max_mana = _number(data.get("max_mana"), self.max_mana)
            self.move = _number(data.get("move"), self.move)
            self.max_move = _number(data.get("max_move"), self.max_move)
            previous_area = self.area
            self.area = _text(data.get("area"), self.area)
            if (
                self.dead
                and previous_area is not None
                and previous_area.casefold() == "purgatory"
                and self.area is not None
                and self.area.casefold() != "purgatory"
            ):
                self.dead = False
            return

        if event.type == "inventory_changed":
            value = data.get("value", _payload(data))
            self.inventory = deepcopy(value)
            return

        if event.type == "equipment_changed":
            value = data.get("value", _payload(data))
            self.equipment = deepcopy(value)
            return

        if event.type == "affects_changed":
            value = data.get("value", _payload(data))
            self.affects = deepcopy(value)
            return

        if event.type == "enemies_changed":
            value = data.get("value", _payload(data))
            self.enemies = deepcopy(value)
            if _enemy_snapshot_empty(value):
                self.in_combat = False
                self.combat_target = None
            return

        if event.type == "item_acquired":
            self.acquired_items.append(_payload(data, keep_text=True))
            return

        if event.type == "quest_received":
            self.quests.append(_payload(data, keep_text=True))
            return

        if event.type == "quest_status_changed":
            self.quest_status = _payload(data)
            self.quest_points = _integer(
                data.get("points"),
                self.quest_points,
            )
            self.total_quest_points = _integer(
                data.get("total_points"),
                self.total_quest_points,
            )
            self.quest_level_qp_required = _integer(
                data.get("level_qp_required"),
                self.quest_level_qp_required,
            )
            self.quest_level_qp_shortfall = _integer(
                data.get("level_qp_shortfall"),
                self.quest_level_qp_shortfall,
            )
            return

        if event.type == "recall_points_changed":
            points = data.get("points")
            if isinstance(points, list):
                self.recall_points = deepcopy(points)
            self.recall_points_observed = True
            self.current_recall = _integer(
                data.get("current"),
                self.current_recall,
            ) or 0
            return

        if event.type == "recall_selection_changed":
            self.current_recall = _integer(
                data.get("current"),
                self.current_recall,
            ) or 0
            return

        if event.type == "combat_started":
            self.in_combat = True
            self.combat_target = _text(data.get("target", data.get("name")))
            return

        if event.type == "character_died":
            self.dead = True
            self.in_combat = False
            self.combat_target = None
            self._progress_source = None


def replay_events(
    events: Iterable[GameEvent],
    *,
    initial: CharacterState | None = None,
) -> CharacterState:
    state = initial or CharacterState()
    for event in events:
        state.apply(event)
    return state


def _enemy_snapshot_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, list):
        return all(_enemy_snapshot_empty(item) for item in value)
    if isinstance(value, dict):
        return not value
    return False


def _payload(data: dict[str, Any], *, keep_text: bool = False) -> dict[str, Any]:
    ignored = {"package"}
    if not keep_text:
        ignored.add("text")
    return {
        key: _coerce(value)
        for key, value in data.items()
        if key not in ignored
    }


def _coerce(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _coerce(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_coerce(item) for item in value]
    return _scalar(value)


def _scalar(value: Any, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, str):
        try:
            number = float(value)
        except ValueError:
            return value
        return int(number) if number.is_integer() else number
    return value


def _number(value: Any, default: int | float | None = None) -> int | float | None:
    converted = _scalar(value, default)
    if isinstance(converted, (int, float)) and not isinstance(converted, bool):
        return converted
    return default


def _integer(value: Any, default: int | None = None) -> int | None:
    converted = _number(value, default)
    return int(converted) if converted is not None else default


def _valid_progress_values(
    level: int | None,
    xp: int | None,
    max_xp: int | None,
    xp_to_next_level: int | None,
) -> bool:
    if level is not None and not 1 <= level <= _MAX_CHARACTER_LEVEL:
        return False
    if xp is not None and xp < 0:
        return False
    if max_xp is not None and max_xp < 0:
        return False
    if xp_to_next_level is not None and xp_to_next_level < 0:
        return False
    if xp is not None and max_xp is not None and max_xp < xp:
        return False
    return True


def _text(value: Any, default: str | None = None) -> str | None:
    if value is None:
        return default
    return str(value)
