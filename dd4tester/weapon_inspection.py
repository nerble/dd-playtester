"""Bounded, connection-local identification of one equipped weapon."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Mapping

from .equipment import ITEM_BODY_PART, ITEM_WEAPON, generated_weapon_damage_floor, normalize_item_name
from .hunt_candidates import ObjectSource


IDENTIFY_SOURCE = "const.c:identify; magic.c:do_cast,spell_identify; handler.c:mana_cost"
_HEADER = re.compile(r"You determine that (.+?) is a weapon\.", re.I)
_LEVEL = re.compile(r"and is level (\d+)\.", re.I)
_DAMAGE = re.compile(r"This weapon does between (\d+) and (\d+) base points of damage\.", re.I)
_WORN_WEAPON = re.compile(r"\[weapon\]\s+([^\n]+)", re.I)


def weapon_record(equipment: Any, *, ranged: bool = False) -> dict[str, Any] | None:
    """Require exactly one structured record in the requested weapon slot."""
    found: list[dict[str, Any]] = []

    def visit(value: Any) -> None:
        if isinstance(value, str):
            try:
                visit(json.loads(value))
            except (ValueError, RecursionError):
                pass
        elif isinstance(value, Mapping):
            slots = {"ranged_weapon", "ranged weapon"} if ranged else {"wield", "weapon"}
            location = 21 if ranged else 16
            if str(value.get("slot", "")).casefold() in slots or value.get("wear_loc") == location:
                if all(type(value.get(key)) is int for key in ("vnum", "level")):
                    found.append(dict(value))
                return
            for nested in value.values():
                if isinstance(nested, (Mapping, list, tuple)):
                    visit(nested)
        elif isinstance(value, (list, tuple)):
            for nested in value:
                visit(nested)

    visit(equipment)
    return found[0] if len(found) == 1 else None


def weapon_signature(record: Mapping[str, Any]) -> tuple[Any, ...]:
    return (record.get("vnum"), record.get("level"), str(record.get("instance_id", "0")),
            normalize_item_name(str(record.get("name", ""))))


def source_weapon_damage(weapon: ObjectSource, record: Mapping[str, Any] | None) -> tuple[int, int] | None:
    """Use generated lower bounds, never ordinary prototype damage values."""
    if weapon.item_type != ITEM_WEAPON or weapon.extra_flags & ITEM_BODY_PART:
        return None
    level = weapon.effective_level
    if record is not None and record.get("vnum") == weapon.vnum:
        level = record.get("level")
    return generated_weapon_damage_floor(level)


def identify_mana_reserve(skill_levels: Mapping[str, int]) -> int | None:
    """The registered inventory spell requires a positive observed practice."""
    percent = skill_levels.get("identify")
    if type(percent) is not int or not 0 < percent <= 100:
        return None
    return max(12, 60 - percent)


@dataclass
class WeaponInspection:
    record: dict[str, Any]
    keyword: str
    stage: str = "new"
    deadline: float = 0.0
    buffer: str = ""
    damage: tuple[int, int] | None = None
    failure: str | None = None
    valid: bool = False
    output_uses: int = 0
    history: list[str] = field(default_factory=list)

    @property
    def pending(self) -> bool:
        return self.stage not in {"complete", "failed"}

    def observe(self, text: str) -> None:
        if not self.pending:
            removed = re.search(r"You stop using (.+?)\.", text)
            if (removed and normalize_item_name(removed[1])
                    == normalize_item_name(str(self.record.get("name", "")))):
                self.valid = False
            if any(message in text.casefold() for message in (
                "disarms you", "your weapon slips from your hand",
            )):
                self.valid = False
            return
        self.buffer = (self.buffer + text)[-4096:]

    def _issue(self, command: str, stage: str, now: float) -> str:
        self.stage, self.deadline, self.buffer = stage, now + 5.0, ""
        self.history.append(command)
        return command

    def next_command(self, *, now: float, equipment: Any) -> str | None:
        name = normalize_item_name(str(self.record.get("name", "")))
        if self.stage == "new":
            return self._issue(f"remove {self.keyword}", "removing", now)
        if self.stage == "removing":
            removed = re.search(r"You stop using (.+?)\.", self.buffer)
            if removed and normalize_item_name(removed[1]) == name:
                return self._issue(f"cast 'identify' {self.keyword}", "identifying", now)
        elif self.stage == "identifying":
            text = " ".join(self.buffer.split())
            header, level, damage = _HEADER.search(text), _LEVEL.search(text), _DAMAGE.search(text)
            if header and level and damage:
                minimum, maximum = int(damage[1]), int(damage[2])
                if (normalize_item_name(header[1]) == name
                        and int(level[1]) == self.record["level"]
                        and 0 < minimum <= maximum <= 10000):
                    self.damage = minimum, maximum
                else:
                    self.failure = "identified weapon did not match the removed item"
                return self._issue(f"wield {self.keyword}", "wielding", now)
        elif self.stage == "wielding":
            wielded = re.search(r"You wield (.+?)\.", self.buffer)
            if wielded and normalize_item_name(wielded[1]) == name:
                return self._issue("eq all", "confirming", now)
        elif self.stage == "confirming":
            current = weapon_record(equipment)
            listed = _WORN_WEAPON.search(self.buffer)
            if (listed and normalize_item_name(listed[1]) == name and current is not None
                    and weapon_signature(current) == weapon_signature(self.record)):
                self.stage = "complete"
                self.valid = self.damage is not None and self.failure is None
                return None
        if now >= self.deadline:
            self.failure = f"weapon inspection timed out during {self.stage}"
            if self.stage in {"removing", "identifying"}:
                return self._issue(f"wield {self.keyword}", "wielding", now)
            self.stage, self.valid = "failed", False
        return None

    def damage_for(self, equipment: Any) -> tuple[int, int] | None:
        current = weapon_record(equipment)
        if (self.valid and current is not None
                and weapon_signature(current) == weapon_signature(self.record)):
            return self.damage
        self.valid = False
        return None

    def audit(self) -> dict[str, Any]:
        return {"stage": self.stage, "weapon": dict(self.record), "damage": self.damage,
                "valid_in_connection": self.valid, "connection_local": True,
                "combat_output_uses": self.output_uses,
                "failure": self.failure, "commands": list(self.history), "source": IDENTIFY_SOURCE}
