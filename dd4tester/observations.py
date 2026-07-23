from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


_ANSI_ESCAPE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
_ROOM = re.compile(r"^Room:\s*(?P<name>.+)$", re.IGNORECASE)
_EXITS = re.compile(r"^\[Exits:\s*(?P<exits>[^\]]*)\]$", re.IGNORECASE)
_PROMPT = re.compile(
    r"(?:<[^>\n]*(?:hp|health|mana|moves?|mv)[^>\n]*>"
    r"|.*\b\d+\s*(?:hp|health|mana|moves?|mv)\b.*>)\s*$",
    re.IGNORECASE,
)
_HEALTH_WITH_MAX = re.compile(
    r"\b(?P<current>\d+)\s*(?:/|of)\s*(?P<maximum>\d+)\s*"
    r"(?:hp|health|hits?)\b",
    re.IGNORECASE,
)
_HEALTH_IN_PROMPT = re.compile(
    r"\b(?P<current>\d+)\s*(?:hp|health|hits?)\b",
    re.IGNORECASE,
)
_DD4_PROMPT = re.compile(
    r"<\s*(?P<hits>\d+)/(?P<max_hits>\d+)\s+hits?\s+"
    r"(?P<mana>\d+)/(?P<max_mana>\d+)\s+mana\s+"
    r"(?P<move>\d+)/(?P<max_move>\d+)\s+moves?"
    r"(?:\s+\[(?P<area>[^\]]+)\])?\s*>",
    re.IGNORECASE,
)
_OUTGOING_COMBAT = re.compile(
    r"\bYou (?:attack|engage) (?P<target>.+?)(?:[.!]|$)",
    re.IGNORECASE,
)
_INCOMING_COMBAT = re.compile(
    r"^\s*(?P<target>.+?) (?:(?:attacks|engages) you|is here,\s*fighting you)"
    r"(?:[.!]|$)",
    re.IGNORECASE | re.MULTILINE,
)
_QUEST = re.compile(
    r"\b(?:Quest received|New quest):\s*(?P<name>.+?)(?:[.!]|$)",
    re.IGNORECASE,
)
_ITEM = re.compile(
    r"\bYou (?:get|pick up|receive|are given) "
    r"(?:(?:an?|the)\s+)?(?P<item>.+?)(?:[.!]|$)",
    re.IGNORECASE,
)
_NON_ITEM_ACQUISITION = re.compile(
    r"^(?:(?:sudden|bad|strange|eerie|deep|easy peaceful)\s+)?"
    r"(?:fear|feeling|sense|impression|urge)\b|^back on your feet\b",
    re.IGNORECASE,
)
_LEVEL = re.compile(
    r"\b(?:You (?:have )?)?"
    r"(?:gain(?:ed)?|advance(?:d)?|reach(?:ed)?|attain(?:ed)?) "
    r"(?:to )?(?:hero )?level\s+(?P<level>\d+)\b",
    re.IGNORECASE,
)
_DEATH = re.compile(
    r"\bYou (?:are dead|have died|were killed|have been killed)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class GameEvent:
    type: str
    source: str
    data: dict[str, Any]

    def as_payload(self) -> dict[str, Any]:
        return {"type": self.type, "source": self.source, "data": self.data}


class ObservationParser:
    """Convert raw MUD text and GMCP messages into deterministic game events."""

    def __init__(self) -> None:
        self._pending_text = ""
        self._health: int | float | None = None
        self._level: int | None = None
        self._dead = False
        self._previous_line: str | None = None
        self._room_name: str | None = None
        self._room_vnum: str | None = None
        self._gmcp_snapshots: dict[str, Any] = {}

    def feed_text(self, text: str) -> list[GameEvent]:
        cleaned = _ANSI_ESCAPE.sub("", text).replace("\r\n", "\n").replace("\r", "\n")
        self._pending_text += cleaned
        lines = self._pending_text.split("\n")
        self._pending_text = lines.pop()
        events: list[GameEvent] = []
        for line in lines:
            events.extend(self._parse_line(line))
        return events

    def flush_text(self) -> list[GameEvent]:
        if not self._pending_text:
            return []
        line = self._pending_text
        self._pending_text = ""
        return self._parse_line(line)

    def feed_gmcp(self, message: str) -> list[GameEvent]:
        package, separator, body = message.partition(" ")
        payload = self._decode_gmcp_body(body) if separator else None
        normalized = package.casefold()
        events: list[GameEvent] = []

        if normalized == "core.prompt":
            events.append(
                GameEvent("prompt_seen", "gmcp", self._gmcp_data(package, payload))
            )

        if normalized == "room.info":
            room_event = self._room_event(package, payload)
            if room_event is not None:
                events.append(room_event)

        if normalized in {"char.vitals", "char.status", "char.worth"} and isinstance(
            payload, dict
        ):
            current = self._number(payload, "hp", "currenthp", "current_hp")
            maximum = self._number(payload, "maxhp", "max_hp", "maximumhp")
            if current is not None:
                health_event = self._health_event(
                    current,
                    maximum=maximum,
                    source="gmcp",
                    extra={"package": package},
                )
                if health_event is not None:
                    events.append(health_event)

            level = self._integer(payload, "level", "lvl")
            level_event = self._level_event(
                level,
                source="gmcp",
                extra={"package": package},
                explicit=False,
            )
            if level_event is not None:
                events.append(level_event)

            status = str(payload.get("state", payload.get("status", ""))).casefold()
            if status in {"dead", "deceased"}:
                death_event = self._death_event("gmcp", {"package": package})
                if death_event is not None:
                    events.append(death_event)
            elif status:
                self._dead = False

        snapshot_types = {
            "char.base": "character_identity_observed",
            "char.vitals": "vitals_changed",
            "char.stats": "stats_changed",
            "char.worth": "progress_changed",
            "char.affect": "affects_changed",
            "char.items": "inventory_changed",
            "char.equipment": "equipment_changed",
            "char.enemies": "enemies_changed",
        }
        snapshot_type = snapshot_types.get(normalized)
        if snapshot_type is not None and self._gmcp_snapshots.get(normalized) != payload:
            self._gmcp_snapshots[normalized] = payload
            events.append(
                GameEvent(snapshot_type, "gmcp", self._gmcp_data(package, payload))
            )

        if normalized == "char.items.add":
            events.append(
                GameEvent("item_acquired", "gmcp", self._gmcp_data(package, payload))
            )

        if normalized in {"quest.add", "quest.start", "quests.add", "quests.start"}:
            events.append(
                GameEvent("quest_received", "gmcp", self._gmcp_data(package, payload))
            )

        if normalized in {"combat.start", "char.combat.start"}:
            events.append(
                GameEvent("combat_started", "gmcp", self._gmcp_data(package, payload))
            )

        return events

    def _parse_line(self, line: str) -> list[GameEvent]:
        text = line.strip()
        if not text:
            return []

        events: list[GameEvent] = []
        room = _ROOM.match(text)
        if room:
            room_event = self._text_room_event(
                room.group("name").strip(),
                text=text,
            )
            if room_event is not None:
                events.append(room_event)

        exits = _EXITS.match(text)
        if exits and self._previous_line:
            directions = exits.group("exits").split()
            room_event = self._text_room_event(
                self._previous_line,
                text=text,
                exits=directions,
            )
            if room_event is not None:
                events.append(room_event)

        prompt = _PROMPT.search(text)
        if prompt:
            prompt_data: dict[str, Any] = {"text": prompt.group(0)}
            dd4_prompt = _DD4_PROMPT.search(prompt.group(0))
            if dd4_prompt:
                prompt_data.update(
                    {
                        "hits": int(dd4_prompt.group("hits")),
                        "max_hits": int(dd4_prompt.group("max_hits")),
                        "mana": int(dd4_prompt.group("mana")),
                        "max_mana": int(dd4_prompt.group("max_mana")),
                        "move": int(dd4_prompt.group("move")),
                        "max_move": int(dd4_prompt.group("max_move")),
                        "area": dd4_prompt.group("area"),
                    }
                )
            events.append(GameEvent("prompt_seen", "text", prompt_data))
            health = _HEALTH_WITH_MAX.search(prompt.group(0))
            if health is None:
                health = _HEALTH_IN_PROMPT.search(prompt.group(0))
            if health is not None:
                maximum = health.groupdict().get("maximum")
                health_event = self._health_event(
                    int(health.group("current")),
                    maximum=int(maximum) if maximum is not None else None,
                    source="text",
                    extra={"text": text},
                )
                if health_event is not None:
                    events.append(health_event)

        combat = _OUTGOING_COMBAT.search(text) or _INCOMING_COMBAT.search(text)
        if combat:
            events.append(
                GameEvent(
                    "combat_started",
                    "text",
                    {"target": combat.group("target").strip(), "text": text},
                )
            )

        quest = _QUEST.search(text)
        if quest:
            events.append(
                GameEvent(
                    "quest_received",
                    "text",
                    {"name": quest.group("name").strip(), "text": text},
                )
            )

        item = _ITEM.search(text)
        item_text = item.group("item").strip() if item is not None else ""
        if (
            item is not None
            and "experience point" not in item_text.casefold()
            and _NON_ITEM_ACQUISITION.match(item_text) is None
        ):
            events.append(
                GameEvent(
                    "item_acquired",
                    "text",
                    {"item": item_text, "text": text},
                )
            )

        level = _LEVEL.search(text)
        if level:
            level_event = self._level_event(
                int(level.group("level")),
                source="text",
                extra={"text": text},
                explicit=True,
            )
            if level_event is not None:
                events.append(level_event)

        if _DEATH.search(text):
            death_event = self._death_event("text", {"text": text})
            if death_event is not None:
                events.append(death_event)
        elif self._dead and prompt:
            self._dead = False

        self._previous_line = text
        return events

    def _room_event(self, package: str, payload: Any) -> GameEvent | None:
        data = self._gmcp_data(package, payload)
        name = str(payload.get("name", "")).strip() if isinstance(payload, dict) else ""
        vnum = str(payload.get("vnum", "")).strip() if isinstance(payload, dict) else ""
        same_room = bool(name and self._same_room(name, vnum))
        enriches_room = bool(same_room and vnum and not self._room_vnum)
        if same_room and not enriches_room:
            if vnum:
                self._room_vnum = vnum
            return None
        self._room_name = name.casefold() or None
        self._room_vnum = vnum or None
        event_type = "room_updated" if same_room else "room_entered"
        return GameEvent(event_type, "gmcp", data)

    def _text_room_event(
        self,
        name: str,
        *,
        text: str,
        exits: list[str] | None = None,
    ) -> GameEvent | None:
        if self._same_room(name, ""):
            return None
        self._room_name = name.casefold()
        self._room_vnum = None
        data: dict[str, Any] = {"name": name, "text": text}
        if exits is not None:
            data["exits"] = exits
        return GameEvent("room_entered", "text", data)

    def _same_room(self, name: str, vnum: str) -> bool:
        if self._room_name != name.casefold():
            return False
        return not vnum or not self._room_vnum or self._room_vnum == vnum

    def _health_event(
        self,
        current: int | float,
        *,
        maximum: int | float | None,
        source: str,
        extra: dict[str, Any],
    ) -> GameEvent | None:
        previous = self._health
        self._health = current
        if previous == current:
            return None
        data = dict(extra)
        data.update({"current": current, "previous": previous})
        if maximum is not None:
            data["maximum"] = maximum
        return GameEvent("health_changed", source, data)

    def _level_event(
        self,
        level: int | None,
        *,
        source: str,
        extra: dict[str, Any],
        explicit: bool,
    ) -> GameEvent | None:
        if level is None:
            return None
        previous = self._level
        self._level = level
        if previous == level or (not explicit and (previous is None or level < previous)):
            return None
        data = dict(extra)
        data.update({"level": level, "previous": previous})
        return GameEvent("level_gained", source, data)

    def _death_event(self, source: str, data: dict[str, Any]) -> GameEvent | None:
        if self._dead:
            return None
        self._dead = True
        return GameEvent("character_died", source, data)

    @staticmethod
    def _decode_gmcp_body(body: str) -> Any:
        body = body.strip()
        if not body:
            return None
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return body

    @staticmethod
    def _gmcp_data(package: str, payload: Any) -> dict[str, Any]:
        if isinstance(payload, dict):
            return {**payload, "package": package}
        return {"package": package, "value": payload}

    @staticmethod
    def _number(payload: dict[str, Any], *keys: str) -> int | float | None:
        for key in keys:
            value = payload.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return value
            if isinstance(value, str):
                try:
                    number = float(value)
                except ValueError:
                    continue
                return int(number) if number.is_integer() else number
        return None

    @classmethod
    def _integer(cls, payload: dict[str, Any], *keys: str) -> int | None:
        value = cls._number(payload, *keys)
        if value is None:
            return None
        return int(value)
