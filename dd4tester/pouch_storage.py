"""Free inventory count through confirmed storage, without approving potion use."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Mapping

from .equipment import (
    GearCatalog, ITEM_BODY_PART, ITEM_CURSED, ITEM_POISONED, normalize_item_name,
)
from .hunt_candidates import ITEM_CONTAINER, ITEM_POTION
from .observations import _DD4_PROMPT


@dataclass(frozen=True)
class PouchStoragePlan:
    pouch_vnum: int
    pouch_name: str
    pouch_keyword: str
    potion_name: str
    potion_keyword: str
    potion_vnums: tuple[int, ...]
    quantity: int


def empty_pouch_storage_plan(
    descriptions: Iterable[str], equipment: Iterable[Mapping], catalog: GearCatalog,
) -> PouchStoragePlan | None:
    """Use exact worn-container identity and keywords safe for every candidate."""
    descriptions = tuple(descriptions)
    records = tuple(equipment)
    pouches = [record for record in records if record.get("slot") == "pouch"]
    if len(pouches) != 1:
        return None
    record = pouches[0]
    pouch = catalog.objects.get(record.get("vnum"))
    if (pouch is None or pouch.item_type != ITEM_CONTAINER or not pouch.values
            or normalize_item_name(str(record.get("name", "")))
            != normalize_item_name(pouch.short_description)
            or (len(pouch.values) > 1 and pouch.values[1] & 4)):
        return None
    candidates = [catalog.candidates(description) for description in descriptions]
    if any(not group for group in candidates):
        return None
    peers = [item for group in candidates for item in group]
    for worn in records:
        if worn is record:
            continue
        item = catalog.objects.get(worn.get("vnum"))
        if item is None:
            return None
        peers.append(item)
    pouch_keyword = next((word for word in sorted(pouch.keywords.split(), key=len, reverse=True)
                          if all(word.casefold() not in item.keywords.casefold().split()
                                 for item in peers)), None)
    if pouch_keyword is None:
        return None
    counts = Counter(normalize_item_name(description) for description in descriptions)
    for description, group in zip(descriptions, candidates):
        if any(item.item_type != ITEM_POTION
               or item.extra_flags & (ITEM_BODY_PART | ITEM_CURSED | ITEM_POISONED)
               for item in group):
            continue
        name = normalize_item_name(description)
        shared = set.intersection(*(set(item.keywords.casefold().split()) for item in group))
        other_items = [item for item in peers if normalize_item_name(item.short_description) != name]
        keyword = next((word for word in sorted(shared, key=len, reverse=True)
                        if word != "potion" and all(word not in item.keywords.casefold().split()
                                                    for item in other_items)), None)
        weight = max(item.weight for item in group)
        if keyword is None or weight <= 0:
            continue
        quantity = min(4, counts[name], max(0, (pouch.values[0] - pouch.weight) // weight))
        if quantity:
            return PouchStoragePlan(
                pouch.vnum, pouch.short_description, pouch_keyword,
                group[0].short_description, keyword,
                tuple(sorted(item.vnum for item in group)), quantity,
            )
    return None


@dataclass
class HealerPouchStorage:
    plan: PouchStoragePlan | None = None
    phase: str = "new"
    deadline: float | None = None
    buffer: str = ""
    before_count: int = 0
    packed: int = 0
    failure: str | None = None

    @property
    def pending(self) -> bool:
        return self.phase in {"audit", "put", "inventory"}

    def _begin_reply(self, phase: str, now: float) -> None:
        self.phase, self.deadline, self.buffer = phase, now + 5, ""

    def begin(self, plan: PouchStoragePlan, count: int, *, now: float) -> str:
        self.plan, self.before_count = plan, count
        self._begin_reply("audit", now)
        return f"look in {plan.pouch_keyword}"

    def observe(self, text: str, *, now: float) -> None:
        if self.pending and not self.expire(now):
            self.buffer = (self.buffer + text)[-4096:]

    def expire(self, now: float) -> bool:
        if self.pending and self.deadline is not None and now >= self.deadline:
            self.failure = f"healer pouch {self.phase} reply exceeded five seconds"
            self.phase = "failed"
            return True
        return False

    def next_command(self, count: int, maximum: int, *, now: float) -> str | None:
        plan = self.plan
        if plan is None or not self.pending:
            return None
        response = _DD4_PROMPT.sub("\n", self.buffer).replace("\r", "")
        if self.phase == "audit":
            header = re.search(r"^\s*" + re.escape(plan.pouch_name) + r" contains:\s*\n",
                               self.buffer, re.MULTILINE | re.IGNORECASE)
            prompt = _DD4_PROMPT.search(self.buffer, header.end()) if header else None
            if prompt is None:
                return None
            contents = self.buffer[header.end():prompt.start()].strip()
            if contents.casefold() != "nothing.":
                self.phase = "unavailable"
                self.deadline = None
                return None
            self._begin_reply("put", now)
            return f"put {plan.potion_keyword} {plan.pouch_keyword}"
        if self.phase == "put":
            replies = re.findall(r"^\s*You put (.+?) in (.+)\.[ \t]*\n", response, re.MULTILINE)
            if any(normalize_item_name(item) == normalize_item_name(plan.potion_name)
                   and normalize_item_name(container) == normalize_item_name(plan.pouch_name)
                   for item, container in replies):
                self.packed += 1
                if self.packed < plan.quantity:
                    self._begin_reply("put", now)
                    return f"put {plan.potion_keyword} {plan.pouch_keyword}"
                self._begin_reply("inventory", now)
                return "inventory"
            if any(marker in response.casefold() for marker in (
                "it won't fit", "you do not have that item", "you can't let go",
                "too high level", "that's not a container", "is closed",
            )):
                # A release/fit refusal is harmless and does not prove a free slot.
                self.phase, self.deadline = "unavailable", None
        elif self.phase == "inventory":
            match = re.search(r"^\s*You are carrying (\d+)/(\d+) items\.\s*$", response, re.MULTILINE)
            if match and "your backpack contains:" in response.casefold():
                observed = int(match[1]), int(match[2])
                if observed[0] != self.before_count - self.packed:
                    self.failure = "healer pouch storage did not free the acknowledged item count"
                    self.phase = "failed"
                elif observed == (count, maximum):
                    self.phase, self.deadline = "complete", None
        return None

    def receipt(self) -> dict | None:
        if self.plan is None:
            return None
        return {
            "status": self.phase, "storage_only": True,
            "pouch_vnum": self.plan.pouch_vnum, "potion_vnums": list(self.plan.potion_vnums),
            "potion_name": self.plan.potion_name, "quantity": self.packed,
            "before_count": self.before_count, "reason": self.failure,
        }
