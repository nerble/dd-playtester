"""Verify reset-ambiguous equipped loot on one current, exact mobile."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from .equipment import normalize_item_name


def equipped_carrier_requirements(
    world: Any, *, mobile_vnum: int, reset_room: str,
    object_vnums: tuple[int, ...], missing: list[str],
) -> tuple[str, ...] | None:
    """Require unique source names and enough reset-worn loot on one carrier."""
    if world is None or not missing or len(missing) > 8:
        return None
    try:
        room_vnum = int(reset_room)
    except (TypeError, ValueError):
        return None
    requirements = Counter(normalize_item_name(name) for name in missing)
    selected = {}
    for name in requirements:
        matches = [item for item in world.objects.values()
                   if normalize_item_name(item.short_description) == name]
        if len(matches) != 1 or matches[0].vnum not in object_vnums:
            return None
        selected[name] = matches[0].vnum
    for reset in world.mob_resets:
        if (reset.mobile_vnum, reset.room_vnum) != (mobile_vnum, room_vnum):
            continue
        if len({slot for slot, _vnum in reset.equipment}) != len(reset.equipment):
            continue
        counts = Counter(vnum for _slot, vnum in reset.equipment)
        if all(counts[selected[name]] >= count for name, count in requirements.items()):
            return tuple(sorted(requirements.elements()))
    return None


@dataclass
class CarrierEquipmentInspection:
    pending: dict[str, Any] | None = None
    receipt: dict[str, Any] | None = None
    records: list[dict[str, Any]] = field(default_factory=list)
    attempted: set[tuple[str, str, int]] = field(default_factory=set)
    buffer: str = ""

    def begin(
        self, *, room: str, selector: str, mobile_vnum: int, name: str,
        description: str, required: tuple[str, ...], level: int,
        boot: str | None, visit: int, now: float,
    ) -> bool:
        key = (room, selector, visit)
        if (
            self.pending is not None or key in self.attempted or len(self.attempted) >= 8
            or not re.fullmatch(r"#[0-9]+", selector) or not description.strip()
            or not name.strip() or not required or boot is None
        ):
            return False
        self.attempted.add(key)
        self.receipt = None
        self.buffer = ""
        self.pending = {
            "room": room, "selector": selector, "mobile_vnum": mobile_vnum,
            "name": name, "description": description, "required": required,
            "level": level, "boot": boot, "visit": visit, "deadline": now + 5,
        }
        return True

    def observe(self, text: str, *, now: float) -> None:
        if self.pending is None:
            return
        if now >= self.pending["deadline"]:
            self.finish("failed", now=now, reason="carrier look exceeded five seconds")
            return
        self.buffer = (self.buffer + text)[-8192:]

    def complete(self, *, now: float) -> None:
        plan = self.pending
        if plan is None:
            return
        if now >= plan["deadline"]:
            self.finish("failed", now=now, reason="carrier look exceeded five seconds")
            return
        health = re.search(
            r"^\s*" + re.escape(plan["name"])
            + r"\s+(?:is in perfect health|is slightly scratched|has a few bruises|"
            r"has some cuts|has several wounds|has many nasty wounds|is bleeding freely|"
            r"is covered in blood|is leaking guts|is almost dead|is DYING)\.\s*$",
            self.buffer, re.IGNORECASE | re.MULTILINE,
        )
        if health is None or not " ".join(self.buffer[:health.start()].split()).casefold().endswith(
            " ".join(plan["description"].split()).casefold()
        ):
            self.finish("failed", now=now, reason="carrier look did not confirm its source description")
            return
        after = self.buffer[health.end():]
        heading = re.search(r"^\s*" + re.escape(plan["name"]) + r" is using:\s*$",
                            after, re.IGNORECASE | re.MULTILINE)
        if heading is None:
            self.finish("absent", now=now, reason="carrier is not visibly wearing the required loot")
            return
        worn = Counter()
        for line in after[heading.end():].splitlines():
            if line.strip().casefold() == "you peek at the inventory:":
                break
            match = re.fullmatch(r"\s*<[^<>\r\n]+>\s+(.+?)\s*", line)
            if match:
                worn[normalize_item_name(match[1])] += 1
        needed = Counter(plan["required"])
        status = "verified" if all(worn[name] >= count for name, count in needed.items()) else "absent"
        self.finish(status, now=now, worn=dict(worn), reason=None if status == "verified"
                    else "carrier does not visibly wear the full missing quantity")

    def finish(self, status: str, *, now: float, reason: str | None,
               worn: dict[str, int] | None = None) -> None:
        if self.pending is None:
            return
        self.receipt = {key: self.pending[key] for key in (
            "room", "selector", "mobile_vnum", "required", "level", "boot", "visit",
        )}
        self.receipt.update(status=status, observed=now, reason=reason, worn=worn or {})
        self.records.append(dict(self.receipt))
        self.pending = None
        self.buffer = ""

    def poll(self, *, room: str, level: int | None, boot: str | None,
             in_combat: bool, now: float) -> bool:
        if self.pending is None:
            return False
        plan = self.pending
        if in_combat or (room, level, boot) != (plan["room"], plan["level"], plan["boot"]):
            self.finish("failed", now=now, reason="carrier look context changed")
        elif now >= plan["deadline"]:
            self.finish("failed", now=now, reason="carrier look exceeded five seconds")
        return self.pending is not None

    def verified(self, *, room: str, selector: str | None, mobile_vnum: int,
                 required: tuple[str, ...], level: int | None, boot: str | None,
                 visit: int, now: float) -> bool:
        record = self.receipt
        return bool(
            record and record["status"] == "verified" and 0 <= now - record["observed"] <= 20
            and (room, selector, mobile_vnum, required, level, boot, visit)
            == tuple(record[key] for key in (
                "room", "selector", "mobile_vnum", "required", "level", "boot", "visit",
            ))
        )

    def invalidate(self) -> None:
        self.receipt = None
