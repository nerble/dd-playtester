"""Free inventory count through confirmed storage, without approving potion use."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, replace
from typing import Iterable, Mapping

from .equipment import (
    GearCatalog, ITEM_BODY_PART, ITEM_CURSED, ITEM_NODROP, ITEM_PAINT,
    ITEM_POISONED, normalize_item_name,
)
from .hunt_candidates import ITEM_CONTAINER, ITEM_PILL, ITEM_POTION
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
    """Use exact worn-container identity and keywords safe for every candidate.

    DD4's ordinary pouch accepts potions and pills.  The storage ledger keeps
    the historical ``potion_*`` field names because it is also used by the
    combat-potion audit, but the stored object may be either supported
    consumable type.  This path only frees an item-count slot; it does not
    infer or approve the object's effect.
    """
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
        if any(item.item_type not in {ITEM_POTION, ITEM_PILL}
               or item.extra_flags & (
                   ITEM_BODY_PART | ITEM_CURSED | ITEM_NODROP | ITEM_POISONED
               )
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
    catalog: GearCatalog | None = None

    @property
    def pending(self) -> bool:
        return self.phase in {"audit", "put", "inventory"}

    def _begin_reply(self, phase: str, now: float) -> None:
        self.phase, self.deadline, self.buffer = phase, now + 5, ""

    def begin(
        self,
        plan: PouchStoragePlan,
        count: int,
        *,
        now: float,
        catalog: GearCatalog | None = None,
    ) -> str:
        self.plan, self.before_count, self.catalog = plan, count, catalog
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
        raw_response = self.buffer.replace("\r", "")
        response = _DD4_PROMPT.sub("\n", raw_response)
        if self.phase == "audit":
            header = re.search(
                r"^\s*" + re.escape(plan.pouch_name) + r" contains:\s*\n",
                response,
                re.MULTILINE | re.IGNORECASE,
            )
            raw_header_start = (
                raw_response.casefold().rfind(plan.pouch_name.casefold())
                if header is not None
                else -1
            )
            prompt = (
                _DD4_PROMPT.search(raw_response, raw_header_start)
                if raw_header_start >= 0
                else None
            )
            if prompt is None:
                return None
            # ``header`` is indexed in the prompt-normalized response.  Use
            # that same response for the listing slice; the raw prompt above
            # is only the completion proof.
            contents = response[header.end():].strip()
            if contents.casefold() != "nothing.":
                if not self._existing_contents_fit(contents):
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

    def _existing_contents_fit(self, contents: str) -> bool:
        """Prove that known pouch contents leave room for the planned item.

        ``look in`` exposes descriptions rather than object VNUMs.  Every
        possible source match therefore has to be pouch-compatible and safe,
        and the heaviest possible match is used for the capacity calculation.
        Without a catalog, retain the historical refusal for non-empty pouches.
        """
        plan = self.plan
        catalog = self.catalog
        if plan is None or catalog is None:
            return False
        lines = tuple(line.strip() for line in contents.splitlines() if line.strip())
        if not lines:
            return False
        existing_weight = 0
        for line in lines:
            candidates = catalog.candidates(line)
            if not candidates or any(
                item.item_type not in {ITEM_POTION, ITEM_PILL, ITEM_PAINT}
                or item.extra_flags & (ITEM_BODY_PART | ITEM_CURSED | ITEM_POISONED)
                or item.weight < 0
                for item in candidates
            ):
                return False
            existing_weight += max(item.weight for item in candidates)
        pouch = catalog.objects.get(plan.pouch_vnum)
        potions = tuple(
            catalog.objects.get(vnum) for vnum in plan.potion_vnums
        )
        if (
            pouch is None
            or not pouch.values
            or any(item is None for item in potions)
        ):
            return False
        potion_weight = max(item.weight for item in potions if item is not None)
        if potion_weight <= 0:
            return False
        available = max(
            0,
            pouch.values[0] - pouch.weight - existing_weight,
        )
        quantity = min(plan.quantity, available // potion_weight)
        if quantity <= 0:
            return False
        if quantity != plan.quantity:
            self.plan = replace(plan, quantity=quantity)
        return True

    def receipt(self) -> dict | None:
        if self.plan is None:
            return None
        return {
            "status": self.phase, "storage_only": True,
            "pouch_vnum": self.plan.pouch_vnum, "potion_vnums": list(self.plan.potion_vnums),
            "potion_name": self.plan.potion_name, "quantity": self.packed,
            "before_count": self.before_count, "reason": self.failure,
        }
