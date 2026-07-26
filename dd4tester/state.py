from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field, fields
from typing import Any, Iterable

from .observations import GameEvent


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
    currencies: dict[str, int | float] = field(default_factory=dict)
    inventory: Any = None
    equipment: Any = None
    affects: Any = None
    enemies: Any = None
    quests: list[dict[str, Any]] = field(default_factory=list)
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

        if event.type == "progress_changed":
            self.progress = _payload(data)
            self.level = _integer(data.get("level"), self.level)
            self.xp = _integer(data.get("xp"), self.xp)
            self.max_xp = _integer(data.get("maxxp"), self.max_xp)
            self.xp_to_next_level = _integer(data.get("xptnl"), self.xp_to_next_level)
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
            self.currencies = {
                name: value
                for name in currency_names
                if (value := _number(data.get(name))) is not None
            }
            return

        if event.type == "level_gained":
            self.level = _integer(data.get("level"), self.level)
            return

        if event.type in {"room_entered", "room_updated"}:
            previous_area = self.area
            self.room_name = _text(data.get("name"), self.room_name)
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
                self.exits = {str(direction): None for direction in exits}
            return

        if event.type == "prompt_seen":
            self.last_prompt = _payload(data, keep_text=True)
            self.hp = _number(data.get("hits"), self.hp)
            self.max_hp = _number(data.get("max_hits"), self.max_hp)
            self.mana = _number(data.get("mana"), self.mana)
            self.max_mana = _number(data.get("max_mana"), self.max_mana)
            self.move = _number(data.get("move"), self.move)
            self.max_move = _number(data.get("max_move"), self.max_move)
            self.area = _text(data.get("area"), self.area)
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

        if event.type == "combat_started":
            self.in_combat = True
            self.combat_target = _text(data.get("target", data.get("name")))
            return

        if event.type == "character_died":
            self.dead = True
            self.in_combat = False
            self.combat_target = None


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


def _text(value: Any, default: str | None = None) -> str | None:
    if value is None:
        return default
    return str(value)
