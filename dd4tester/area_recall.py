"""Bounded, noncombat escape from an audited area-local recall point."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from .equipment import normalize_item_name
from .hunt_candidates import (
    WorldSource, _wanderer_reachable_rooms, _wandering_aggressors,
    source_room_level_rejection, source_route_hazard_rejections,
)
from .observations import _DD4_PROMPT
from .source_purchases import SourcePurchase, SourcePurchaseSession
from .specials import SAFE_NONCOMBAT_SPECIALS, TRANSIT_SAFE_COMBAT_ONLY_SPECIALS
from .state import CharacterState


LOCAL_RECALL_ROOMS = frozenset({"27347", "27647", "27132", "27071"})
SHOP_STEPS = (
    (27347, "south", 27341), (27341, "south", 27336),
    (27336, "east", 27337), (27337, "south", 27332),
    (27332, "west", 27331),
)
ESCAPE_STEPS = (
    (27347, "up", 27647), (27647, "up", 27132),
    (27132, "up", 27071),
)


def undersea_escape_source_issue(world: WorldSource, directory: Path, level: int) -> str | None:
    """Keep this maintenance exception tied to the exact current source shape."""
    for filename, expected in (("sahuagin_market.are", 27347), ("undersea.are", 3001)):
        text = (directory / filename).read_text(encoding="utf-8", errors="replace")
        match = re.search(r"(?m)^#RECALL\s+(\d+)", text)
        if (int(match[1]) if match else 3001) != expected:
            return "the audited area's recall destination changed"
    for origin, direction, destination in (*SHOP_STEPS, *ESCAPE_STEPS):
        room = world.rooms.get(origin)
        target = world.rooms.get(destination)
        exit_source = room.exits.get(direction) if room else None
        if (room is None or target is None or room.random_exits or target.random_exits
                or exit_source is None or exit_source.destination != destination
                or exit_source.closed or exit_source.locked
                or source_room_level_rejection(target, level)):
            return "the audited local-recall escape route changed"
    if not world.rooms[27647].no_mob or world.rooms[27071].no_recall:
        return "the escape staging or final recall room changed"
    item = world.objects.get(27292)
    stock = [r for r in world.mob_resets if r.mobile_vnum == 27231 and r.room_vnum == 27331]
    if (item is None or item.item_type != 26 or item.level > level
            or item.value_strings != ("40", "infravision", "", "")
            or len(stock) != 1 or 27292 not in stock[0].object_vnums
            or 27231 not in world.shopkeepers):
        return "the exact night-vision supply is not source-usable"
    # The local thief can steal coins, but has no aggression or executable
    # program. Its ordinary dagger does not start a fight by itself.
    thief = world.mobiles.get(27246)
    thief_resets = [r for r in world.mob_resets if r.mobile_vnum == 27246]
    if (thief is None or thief.aggressive or thief.fear_aura or thief.programs
            or set(world.mobile_specials.get(27246, ())) != {"spec_thief"}
            or not thief_resets
            or any(set(r.equipment) != {(13, 27231), (16, 27370)} for r in thief_resets)):
        return "the audited economic-only local thief changed"
    shop_hazards = source_route_hazard_rejections(
        world, (27347, *(s[2] for s in SHOP_STEPS)),
        character_level=level, combat_at_destination=False,
    )
    if any(reason != "a non-safe special mobile can reach the route: a sahuagin thief"
           for reason in shop_hazards):
        return "the night-vision shop route has an additional source hazard"
    # Only visible pre-combat threats can be excluded by the infrared scan.
    # Passive invisible combat-only casters cannot start this noncombat route.
    dangerous = set()
    for mobile, reset in _wandering_aggressors(world):
        reachable = _wanderer_reachable_rooms(world, mobile, reset.room_vnum)
        if not reachable.intersection({27132, 27071}):
            continue
        if not set(world.mobile_specials.get(mobile.vnum, ())) <= (
                SAFE_NONCOMBAT_SPECIALS | TRANSIT_SAFE_COMBAT_ONLY_SPECIALS | {"spec_thief"}):
            return "the escape contains an unknown or pre-combat special"
        if mobile.aggressive or mobile.attack_programs or mobile.fear_aura:
            if mobile.affected_flags & ((1 << 1) | (1 << 16)):
                return "an escape attacker is invisible or hidden"
            dangerous.add(mobile.vnum)
    if dangerous != {27103, 27106, 27000, 27009, 27013}:
        return "the source-reachable escape attackers changed"
    endpoint_resets = [r for r in world.mob_resets if r.room_vnum in {27647, 27132, 27071}]
    if (len(endpoint_resets) != 1 or endpoint_resets[0].mobile_vnum != 27105
            or endpoint_resets[0].room_vnum != 27132
            or world.mobiles[27105].aggressive or world.mobiles[27105].programs
            or set(world.mobile_specials.get(27105, ())) != {"spec_cast_undead"}):
        return "the escape's passive room reset changed"
    return None


@dataclass
class AreaRecallEscape:
    """Own one local supply purchase and three scanned escape steps."""

    stage: str = "new"
    shop_index: int = 0
    pending_room: str | None = None
    pending_kind: str | None = None
    response: str = ""
    deadline: float | None = None
    failure: str | None = None
    purchase: SourcePurchaseSession = field(default_factory=lambda: SourcePurchaseSession(
        SourcePurchase(27292, 27231, 27331, "a goblin shark pie", "shark", 500, 100),
    ))
    scans: list[dict[str, str]] = field(default_factory=list)
    commands_sent: int = 0

    def observe(self, text: str) -> None:
        self.purchase.observe(text)
        if self.pending_kind:
            self.response = (self.response + text)[-8000:]

    def expire(self, now: float) -> bool:
        if self.purchase.expire(now):
            self.failure = self.purchase.failure
            return True
        if self.deadline is not None and now >= self.deadline:
            if not _DD4_PROMPT.search(self.response):
                self.failure = "local-recall escape response timed out after five seconds"
                return True
        return False

    def _send(self, command: str, now: float, *, kind: str = "reply", room: int | None = None) -> str:
        self.commands_sent += 1
        self.pending_kind, self.pending_room = kind, str(room) if room else None
        self.response, self.deadline = "", now + 5
        return command

    def next_command(
        self, state: CharacterState, *, now: float, inventory: Sequence[tuple[str, str | None]],
        coins: int, flight: bool, infrared: bool, sanctuary: bool, purple_available: bool,
    ) -> str | None:
        self.expire(now)
        if self.failure or self.stage == "complete":
            return None
        if self.commands_sent >= 30:
            self.failure = "local-recall escape reached its thirty-command limit"
            return None
        if state.dead or state.in_combat or state.combat_target:
            self.failure = "local-recall escape observed combat; no attack is authorized"
            return None
        if not flight or not state.hp or not state.max_hp or state.hp < state.max_hp * 0.95:
            self.failure = "local-recall escape requires fresh flight and full recovery"
            return None
        if not state.move or state.move < 30:
            self.failure = "local-recall escape has insufficient movement"
            return None
        room = state.room_vnum
        if self.pending_kind:
            if not _DD4_PROMPT.search(self.response):
                return None
            kind, expected, response = self.pending_kind, self.pending_room, self.response
            self.pending_kind = self.pending_room = self.deadline = None
            if expected and room != expected:
                self.failure = "local-recall escape did not reach its exact registered room"
                return None
            if kind == "scan":
                self.scans.append({"room_vnum": str(room), "text": response})
                if re.search(r"\b(?:one room|a closed .+? right here)\b", response, re.I):
                    self.failure = "the immediate escape destination is occupied or closed"
                    return None
                if not ("You can't see anything upwards." in response
                        or re.search(r"\b(?:two|three|four|five|six) rooms? upwards", response)):
                    self.failure = "the infrared escape scan had no complete direction response"
                    return None
                self.stage = "scanned"
            elif kind == "vision-consumed":
                return self._send("affects", now, kind="vision")
            elif kind == "sanctuary-consumed":
                return self._send("affects", now, kind="sanctuary")
            elif kind == "vision" and not infrared:
                self.failure = "the purchased pie did not produce observed infrared vision"
                return None
            elif kind == "sanctuary" and not sanctuary:
                self.failure = "the escape sanctuary potion was not confirmed"
                return None
        if room == "3001":
            self.stage = "complete"
            return None
        if self.stage == "new":
            self.stage = "escape" if infrared else "shop"
            if not infrared and room != "27347":
                self.failure = "night-vision supply must start at the audited local recall room"
                return None
        if self.stage == "shop":
            if self.shop_index < len(SHOP_STEPS):
                origin, direction, destination = SHOP_STEPS[self.shop_index]
                if room != str(origin) or state.exits.get(direction[0], state.exits.get(direction)) != str(destination):
                    self.failure = "the live night-vision shop exit differs from source"
                    return None
                self.shop_index += 1
                return self._send(direction, now, room=destination)
            command = self.purchase.next_command(
                room_vnum=room, level=state.level or 0, coins=coins,
                inventory=inventory, now=now,
            )
            if self.purchase.failure:
                self.failure = self.purchase.failure
            if command:
                self.commands_sent += 1
                return command
            if self.purchase.stage != "complete":
                return None
            pies = [(name, selector) for name, selector in inventory
                    if normalize_item_name(name) == normalize_item_name(self.purchase.plan.description)]
            if len(pies) != 1 or not pies[0][1]:
                self.failure = "the purchased night-vision pie has no unique live selector"
                return None
            self.stage = "supplied"
            return self._send(f"eat {pies[0][1]}", now, kind="vision-consumed")
        if self.stage == "supplied":
            self.stage = "escape"
            return self._send("recall", now, room=27347)
        if not infrared:
            self.failure = "infrared vision expired before the dark-room escape"
            return None
        if not sanctuary:
            if not purple_available:
                self.failure = "the scanned escape has no verified sanctuary reserve"
                return None
            return self._send("quaff purple", now, kind="sanctuary-consumed")
        if room == "27071":
            return self._send("recall", now, room=3001)
        step = next((s for s in ESCAPE_STEPS if str(s[0]) == room), None)
        if step is None:
            self.failure = "the local-recall escape left its registered room graph"
            return None
        _, direction, destination = step
        if state.exits.get(direction[0], state.exits.get(direction)) != str(destination):
            self.failure = "the live local-recall escape exit differs from source"
            return None
        if destination != 27647 and self.stage != "scanned":
            return self._send("scan up", now, kind="scan")
        self.stage = "escape"
        return self._send(direction, now, room=destination)

    def evidence(self) -> dict:
        return {"stage": self.stage, "commands_sent": self.commands_sent,
                "failure": self.failure, "purchase": self.purchase.evidence(), "scans": self.scans}
