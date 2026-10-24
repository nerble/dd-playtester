"""Bounded, noncombat escape from an audited area-local recall point."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Collection, Mapping, Sequence

from .equipment import (
    GearCatalog,
    ITEM_WEAPON,
    STANCE_COMBAT,
    STANCE_RECOVERY,
    is_capacity_infrastructure,
    is_releasable_funding_item,
    item_category,
    normalize_item_name,
    stance_score,
)
from .hunt_candidates import (
    WorldSource, _wanderer_reachable_rooms, _wandering_aggressors,
    source_room_level_rejection, source_route_hazard_rejections,
)
from .observations import _DD4_PROMPT
from .source_purchases import (
    SourceLiquidation,
    SourceLiquidationSession,
    SourcePurchase,
    SourcePurchaseSession,
)
from .specials import SAFE_NONCOMBAT_SPECIALS, TRANSIT_SAFE_COMBAT_ONLY_SPECIALS
from .state import CharacterState


LOCAL_RECALL_ROOMS = frozenset({
    "27331", "27332", "27336", "27337", "27341",
    "27347", "27647", "27132", "27071",
})
SHOP_STEPS = (
    (27347, "south", 27341), (27341, "south", 27336),
    (27336, "east", 27337), (27337, "south", 27332),
    (27332, "west", 27331),
)
ESCAPE_STEPS = (
    (27347, "up", 27647), (27647, "up", 27132),
    (27132, "up", 27071),
)
WATER_LOSS_RETURN_STEPS = (
    (27132, "down", 27648), (27648, "west", 27647),
    (27647, "down", 27347),
)
SHOP_RETURN_STEPS = (
    (27331, "east", 27332), (27332, "north", 27337),
    (27337, "west", 27336), (27336, "north", 27341),
    (27341, "north", 27347),
)
LOCAL_WATER_SHOP_STEPS = {
    "27331": (
        (27331, "east", 27332), (27332, "north", 27337),
        (27337, "north", 27342), (27342, "east", 27343),
        (27343, "east", 27344), (27344, "south", 27339),
        (27339, "east", 27340),
    ),
    "27332": (
        (27332, "north", 27337), (27337, "north", 27342),
        (27342, "east", 27343), (27343, "east", 27344),
        (27344, "south", 27339), (27339, "east", 27340),
    ),
    "27336": (
        (27336, "east", 27337), (27337, "north", 27342),
        (27342, "east", 27343), (27343, "east", 27344),
        (27344, "south", 27339), (27339, "east", 27340),
    ),
    "27337": (
        (27337, "north", 27342), (27342, "east", 27343),
        (27343, "east", 27344), (27344, "south", 27339),
        (27339, "east", 27340),
    ),
    "27341": (
        (27341, "east", 27342), (27342, "east", 27343),
        (27343, "east", 27344), (27344, "south", 27339),
        (27339, "east", 27340),
    ),
    "27347": (
        (27347, "south", 27341), (27341, "east", 27342),
        (27342, "east", 27343), (27343, "east", 27344),
        (27344, "south", 27339), (27339, "east", 27340),
    ),
}
LOCAL_WATER_RECALL_ROOMS = frozenset(
    str(room)
    for route in LOCAL_WATER_SHOP_STEPS.values()
    for origin, _direction, destination in route
    for room in (origin, destination)
)
LOCAL_WATER_POTION_VNUM = 27333
LOCAL_WATER_POTION_DESCRIPTION = "shark's wine"
LOCAL_WATER_POTION_KEYWORD = "shark"
LOCAL_WATER_POTION_SHOPKEEPER_VNUM = 27235
LOCAL_WATER_POTION_SHOP_ROOM = 27340
LOCAL_WEAPON_SHOPKEEPER_VNUM = 27233
LOCAL_WEAPON_SHOP_ROOM = 27334
LOCAL_WEAPON_SHOP_STEPS = {
    "27340": (
        (27340, "west", 27339), (27339, "south", 27334),
    ),
    "27347": (
        (27347, "south", 27341), (27341, "east", 27342),
        (27342, "east", 27343), (27343, "east", 27344),
        (27344, "south", 27339), (27339, "south", 27334),
    ),
}
LOCAL_WEAPON_TO_WATER_STEPS = (
    (27334, "north", 27339), (27339, "east", 27340),
)
LOCAL_WEAPON_LIQUIDATION = SourceLiquidation(
    LOCAL_WEAPON_SHOPKEEPER_VNUM,
    LOCAL_WEAPON_SHOP_ROOM,
    (ITEM_WEAPON,),
    maximum_items=1,
)
LOCAL_VALUE_OFFER = re.compile(
    r"tells you 'I'll give you (?P<coins>\d+) coins? for (?P<item>.+?)'\.",
    re.IGNORECASE,
)
LOCAL_SALE_COMPLETED = re.compile(
    r"You sell (?P<item>.+?) for (?P<coins>\d+) coins?\.",
    re.IGNORECASE,
)
_OPPOSITE_DIRECTIONS = {
    "north": "south", "south": "north", "east": "west", "west": "east",
}


def _reverse_route(
    steps: Sequence[tuple[int, str, int]],
) -> tuple[tuple[int, str, int], ...]:
    return tuple(
        (destination, _OPPOSITE_DIRECTIONS[direction], origin)
        for origin, direction, destination in reversed(steps)
    )


def _inventory_count(
    inventory: Sequence[tuple[str, str | None]], description: str,
) -> int:
    target = normalize_item_name(description)
    return sum(normalize_item_name(name) == target for name, _ in inventory)


def _equipment_names(equipment: Any) -> set[str]:
    if isinstance(equipment, Mapping):
        equipment = equipment.values()
    if not isinstance(equipment, (list, tuple)):
        return set()
    names = set()
    for record in equipment:
        if not isinstance(record, Mapping):
            continue
        name = record.get("name") or record.get("short_desc")
        if name:
            names.add(normalize_item_name(str(name)))
    return names


def source_allows_failed_local_recall_logout(world: WorldSource | None, state: CharacterState) -> bool:
    """A failed return must not leave a live character link-dead underwater."""
    try:
        commandable = state.position is not None and int(state.position) >= 4
    except (TypeError, ValueError):
        commandable = False
    if (world is None or state.room_vnum != "27347" or "no_mob" not in state.room_flags
            or state.dead or state.in_combat or state.combat_target
            or state.hp is None or state.hp <= 0
            or not commandable):
        return False
    room = world.rooms.get(27347)
    return bool(room and room.no_mob and not source_route_hazard_rejections(
        world, (27347,), character_level=state.level or 0,
        require_no_combat_hazards=True, combat_at_destination=False,
    ))


def undersea_escape_source_issue(world: WorldSource, directory: Path, level: int) -> str | None:
    """Keep this maintenance exception tied to the exact current source shape."""
    for filename, expected in (("sahuagin_market.are", 27347), ("undersea.are", 3001)):
        text = (directory / filename).read_text(encoding="utf-8", errors="replace")
        match = re.search(r"(?m)^#RECALL\s+(\d+)", text)
        if (int(match[1]) if match else 3001) != expected:
            return "the audited area's recall destination changed"
    for origin, direction, destination in (
        *SHOP_STEPS,
        *ESCAPE_STEPS,
        *WATER_LOSS_RETURN_STEPS,
        *{
            step
            for route in LOCAL_WATER_SHOP_STEPS.values()
            for step in route
        },
        *{
            step
            for route in LOCAL_WEAPON_SHOP_STEPS.values()
            for step in route
        },
        *LOCAL_WEAPON_TO_WATER_STEPS,
    ):
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
    water_item = world.objects.get(LOCAL_WATER_POTION_VNUM)
    water_stock = [
        reset
        for reset in world.mob_resets
        if reset.mobile_vnum == LOCAL_WATER_POTION_SHOPKEEPER_VNUM
        and reset.room_vnum == LOCAL_WATER_POTION_SHOP_ROOM
    ]
    if (
        water_item is None
        or water_item.item_type != 10
        or water_item.level > level
        or water_item.value_strings != ("60", "breathe water", "", "")
        or len(water_stock) != 1
        or LOCAL_WATER_POTION_VNUM not in water_stock[0].object_vnums
        or LOCAL_WATER_POTION_SHOPKEEPER_VNUM not in world.shopkeepers
    ):
        return "the exact local water-breathing potion is not source-usable"
    local_water_hazards = source_route_hazard_rejections(
        world,
        tuple(
            step[0]
            for step in LOCAL_WATER_SHOP_STEPS["27347"]
        ) + (LOCAL_WATER_POTION_SHOP_ROOM,),
        character_level=level,
        combat_at_destination=False,
    )
    if any(
        reason != "a non-safe special mobile can reach the route: a sahuagin thief"
        for reason in local_water_hazards
    ):
        return "the local water-breathing shop route has an additional source hazard"
    market_text = (directory / "sahuagin_market.are").read_text(
        encoding="utf-8", errors="replace",
    )
    weapon_stock = [
        reset
        for reset in world.mob_resets
        if reset.mobile_vnum == LOCAL_WEAPON_SHOPKEEPER_VNUM
        and reset.room_vnum == LOCAL_WEAPON_SHOP_ROOM
    ]
    if (
        LOCAL_WEAPON_SHOPKEEPER_VNUM not in world.shopkeepers
        or len(weapon_stock) != 1
        or not re.search(r"(?m)^27233\s+5\s+0\s+0\s+0\s+0\s+", market_text)
    ):
        return "the exact local weaponsmith liquidation route is not source-usable"
    weapon_route_hazards = source_route_hazard_rejections(
        world,
        tuple(step[0] for step in LOCAL_WEAPON_SHOP_STEPS["27347"])
        + (LOCAL_WEAPON_SHOP_ROOM,),
        character_level=level,
        combat_at_destination=False,
    )
    if any(
        reason != "a non-safe special mobile can reach the route: a sahuagin thief"
        for reason in weapon_route_hazards
    ):
        return "the local weaponsmith liquidation route has an additional source hazard"
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
    """Own bounded local preparation and three scanned escape steps.

    The local pie is a source-audited way to obtain infravision, but it is
    not the only valid illumination source. DD4's active light-slot object
    also makes the escape usable, so a verified permanent light can avoid an
    unnecessary reboot-priced purchase. A reconnect that clears water
    breathing can also buy the source-verified local potion, funding it with
    a bounded set of distinct redundant source armour items when necessary.
    """

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
    scan_retry_count: int = 0
    scan_retry_due: float | None = None
    commands_sent: int = 0
    backtrack_index: int = 0
    water_purchase: SourcePurchaseSession = field(default_factory=lambda: SourcePurchaseSession(
        SourcePurchase(
            LOCAL_WATER_POTION_VNUM,
            LOCAL_WATER_POTION_SHOPKEEPER_VNUM,
            LOCAL_WATER_POTION_SHOP_ROOM,
            LOCAL_WATER_POTION_DESCRIPTION,
            LOCAL_WATER_POTION_KEYWORD,
            5000,
            0,
        ),
    ))
    water_prep_stage: str | None = None
    water_prep_origin: str | None = None
    water_route_index: int = 0
    water_return_index: int = 0
    water_loss_return_active: bool = False
    water_loss_return_index: int = 0
    water_funding_attempted: bool = False
    water_funding_attempts: int = 0
    water_funding_item_vnums: tuple[int, ...] = ()
    water_funding_origin: str | None = None
    water_funding_route_index: int = 0
    water_funding_return_index: int = 0
    water_funding_liquidation: SourceLiquidationSession = field(
        default_factory=lambda: SourceLiquidationSession(LOCAL_WEAPON_LIQUIDATION),
    )
    water_sale_description: str | None = None
    water_sale_keyword: str | None = None
    water_sale_selector: str | None = None
    water_sale_vnum: int | None = None
    water_sale_offer: int | None = None
    water_sale_initial_count: int = 0

    @classmethod
    def from_room(cls, room_vnum: str | None) -> "AreaRecallEscape":
        """Resume at an audited shop-route room after a partial escape."""
        session = cls()
        room = str(room_vnum or "")
        for index, (origin, _direction, _destination) in enumerate(SHOP_RETURN_STEPS):
            if room == str(origin):
                session.stage = "backtrack"
                session.backtrack_index = index
                break
        return session

    def observe(self, text: str) -> None:
        self.purchase.observe(text)
        self.water_purchase.observe(text)
        self.water_funding_liquidation.observe(text)
        if self.pending_kind:
            self.response = (self.response + text)[-8000:]

    def expire(self, now: float) -> bool:
        if self.purchase.expire(now):
            self.failure = self.purchase.failure
            return True
        if self.water_purchase.expire(now):
            self.failure = self.water_purchase.failure
            return True
        if self.water_funding_liquidation.expire(now):
            self.failure = self.water_funding_liquidation.failure
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

    def _funding_item(
        self,
        inventory: Sequence[tuple[str, str | None]],
        equipment: Any,
        gear_catalog: GearCatalog | None,
        excluded_vnums: Collection[int] = (),
        accepted_item_types: Collection[int] = (9,),
    ) -> tuple[str, str | None, Any] | None:
        """Choose one redundant, source-safe item for a local quote."""
        if gear_catalog is None:
            return None
        worn_names = _equipment_names(equipment)
        source_items: list[tuple[str, str | None, Any]] = []
        for description, selector in inventory:
            if normalize_item_name(description) in worn_names:
                continue
            candidates = gear_catalog.candidates(description)
            if len(candidates) != 1:
                continue
            item = candidates[0]
            if (
                item.vnum in excluded_vnums
                or item.item_type not in accepted_item_types
                or not is_releasable_funding_item(item)
                or is_capacity_infrastructure(item)
                or item_category(item) is None
            ):
                continue
            source_items.append((description, selector, item))
        if not source_items:
            return None
        all_items = [item for _description, _selector, item in source_items]
        for name in worn_names:
            candidates = gear_catalog.candidates(name)
            if len(candidates) == 1:
                all_items.append(candidates[0])
        ranked: list[tuple[int, tuple[int, ...], str, str, int, Any]] = []
        for description, selector, item in source_items:
            category = item_category(item)
            peers = [
                peer for peer in all_items
                if peer.vnum != item.vnum and item_category(peer) == category
            ]
            if not peers:
                continue
            recovery = stance_score(item, STANCE_RECOVERY)
            combat = stance_score(item, STANCE_COMBAT)
            if not any(
                stance_score(peer, STANCE_RECOVERY) > recovery
                or stance_score(peer, STANCE_COMBAT) > combat
                for peer in peers
            ):
                continue
            words = {
                word.casefold()
                for word in normalize_item_name(description).split()
            }
            keyword = next(
                (
                    word for word in item.keywords.split()
                    if word.casefold() in words
                ),
                None,
            )
            if keyword is None:
                continue
            ranked.append(
                (
                    int(item.source_cost),
                    recovery,
                    normalize_item_name(description),
                    selector or "",
                    int(item.vnum),
                    item,
                )
            )
        if not ranked:
            return None
        _cost, _score, description, selector, _vnum, item = max(ranked)
        return description, selector or None, item

    def _water_preparation_command(
        self,
        state: CharacterState,
        *,
        inventory: Sequence[tuple[str, str | None]],
        coins: int,
        gear_catalog: GearCatalog | None,
        equipment: Any,
        now: float,
        invisible: bool,
    ) -> str | None:
        """Buy and consume local water breathing before the air-sector exit."""
        if state.position == 4 or str(state.position).casefold() == "sleeping":
            return self._send(
                "stand",
                now,
                kind="water-wake",
            )
        origin = self.water_prep_origin
        route = LOCAL_WATER_SHOP_STEPS.get(str(origin or ""), ())
        if not route:
            self.failure = "no source-registered local water-breathing route from this room"
            return None
        if self.water_prep_stage == "water-await-recall":
            self.failure = "local water-breathing recall did not complete"
            return None
        if self.water_prep_stage == "water-outbound":
            if self.water_route_index < len(route):
                source_origin, direction, destination = route[self.water_route_index]
                if (
                    str(state.room_vnum) != str(source_origin)
                    or state.exits.get(direction[0], state.exits.get(direction))
                    != str(destination)
                ):
                    self.failure = "the live local water-breathing route differs from source"
                    return None
                self.water_route_index += 1
                return self._send(direction, now, room=destination)
            self.water_prep_stage = "water-purchase"

        if self.water_prep_stage == "water-purchase":
            command = self.water_purchase.next_command(
                room_vnum=state.room_vnum,
                level=state.level or 0,
                coins=coins,
                inventory=inventory,
                now=now,
                invisible=invisible,
            )
            if self.water_purchase.failure:
                quote_failure = self.water_purchase.failure == (
                    "quoted price exceeds the reserved purchase balance"
                )
                if quote_failure and self.water_funding_attempts < 4:
                    self.water_funding_attempted = True
                    self.water_funding_attempts += 1
                    self.water_funding_origin = str(state.room_vnum)
                    if self.water_funding_origin not in LOCAL_WEAPON_SHOP_STEPS:
                        self.failure = (
                            "the local water-breathing potion is unaffordable and "
                            "the source weaponsmith route has no registered origin"
                        )
                        return None
                    self.water_funding_route_index = 0
                    self.water_funding_liquidation = SourceLiquidationSession(
                        LOCAL_WEAPON_LIQUIDATION,
                    )
                    self.water_prep_stage = "water-funding-outbound"
                    return self._water_funding_command(
                        state,
                        inventory=inventory,
                        coins=coins,
                        gear_catalog=gear_catalog,
                        equipment=equipment,
                        now=now,
                        invisible=invisible,
                    )
                self.failure = self.water_purchase.failure
                return None
            if command:
                return command
            if self.water_purchase.stage != "complete":
                return None
            potions = [
                (name, selector)
                for name, selector in inventory
                if normalize_item_name(name)
                == normalize_item_name(LOCAL_WATER_POTION_DESCRIPTION)
            ]
            if len(potions) != 1 or not potions[0][1]:
                self.failure = "the purchased local water-breathing potion has no unique selector"
                return None
            self.water_prep_stage = "water-quaff"
            return self._send(
                f"quaff {potions[0][1]}",
                now,
                kind="water-consumed",
            )

        if self.water_prep_stage == "water-return":
            reverse_route = _reverse_route(route)
            if self.water_return_index < len(reverse_route):
                source_origin, direction, destination = reverse_route[self.water_return_index]
                if (
                    str(state.room_vnum) != str(source_origin)
                    or state.exits.get(direction[0], state.exits.get(direction))
                    != str(destination)
                ):
                    self.failure = "the live local water-breathing return route differs from source"
                    return None
                self.water_return_index += 1
                return self._send(direction, now, room=destination)
            self.water_prep_stage = None
            if origin == "27347":
                self.stage = "new"
            else:
                self.stage = "backtrack"
                self.backtrack_index = next(
                    (
                        index for index, (source_origin, _direction, _destination)
                        in enumerate(SHOP_RETURN_STEPS)
                        if str(source_origin) == str(origin)
                    ),
                    0,
                )
            return None
        return None

    def _water_funding_command(
        self,
        state: CharacterState,
        *,
        inventory: Sequence[tuple[str, str | None]],
        coins: int,
        gear_catalog: GearCatalog | None,
        equipment: Any,
        now: float,
        invisible: bool,
    ) -> str | None:
        """Sell one source-safe weapon before retrying the water quote."""
        if self.water_prep_stage == "water-funding-outbound":
            route = LOCAL_WEAPON_SHOP_STEPS.get(str(self.water_funding_origin or ""), ())
            if self.water_funding_route_index < len(route):
                origin, direction, destination = route[self.water_funding_route_index]
                if (
                    str(state.room_vnum) != str(origin)
                    or state.exits.get(direction[0], state.exits.get(direction))
                    != str(destination)
                ):
                    self.failure = "the live local weaponsmith funding route differs from source"
                    return None
                self.water_funding_route_index += 1
                return self._send(direction, now, kind="water-funding", room=destination)
            self.water_prep_stage = "water-funding-sale"

        if self.water_prep_stage == "water-funding-sale":
            funding = self._funding_item(
                inventory,
                equipment,
                gear_catalog,
                excluded_vnums=self.water_funding_item_vnums,
                accepted_item_types=(ITEM_WEAPON,),
            )
            command = self.water_funding_liquidation.next_command(
                room_vnum=state.room_vnum,
                inventory=inventory,
                now=now,
                funding_item=(funding[0], funding[1] or "", funding[2].vnum)
                if funding is not None else None,
            )
            if self.water_funding_liquidation.failure:
                self.failure = self.water_funding_liquidation.failure
                return None
            if command:
                return self._send(
                    command,
                    now,
                    kind="water-funding",
                    room=LOCAL_WEAPON_SHOP_ROOM,
                )
            if self.water_funding_liquidation.stage != "complete":
                return None
            sold = self.water_funding_liquidation.funding_item_vnums
            if not sold:
                self.failure = (
                    "the local water-breathing potion is unaffordable and no "
                    "source-safe weapon is available for weaponsmith funding"
                )
                return None
            self.water_funding_item_vnums = tuple(dict.fromkeys(
                (*self.water_funding_item_vnums, *sold),
            ))
            self.water_funding_return_index = 0
            self.water_prep_stage = "water-funding-return"

        if self.water_prep_stage == "water-funding-return":
            if self.water_funding_return_index < len(LOCAL_WEAPON_TO_WATER_STEPS):
                origin, direction, destination = LOCAL_WEAPON_TO_WATER_STEPS[
                    self.water_funding_return_index
                ]
                if (
                    str(state.room_vnum) != str(origin)
                    or state.exits.get(direction[0], state.exits.get(direction))
                    != str(destination)
                ):
                    self.failure = "the live weaponsmith-to-water route differs from source"
                    return None
                self.water_funding_return_index += 1
                return self._send(direction, now, kind="water-funding", room=destination)
            self.water_funding_liquidation = SourceLiquidationSession(
                LOCAL_WEAPON_LIQUIDATION,
            )
            self.water_purchase = SourcePurchaseSession(self.water_purchase.plan)
            self.water_prep_stage = "water-purchase"
            return self._water_preparation_command(
                state,
                inventory=inventory,
                coins=coins,
                gear_catalog=gear_catalog,
                equipment=equipment,
                now=now,
                invisible=invisible,
            )
        return None

    def next_command(
        self, state: CharacterState, *, now: float, inventory: Sequence[tuple[str, str | None]],
        coins: int, flight: bool, infrared: bool, sanctuary: bool, purple_available: bool,
        water_breathing: bool, light_available: bool = False,
        gear_catalog: GearCatalog | None = None,
        equipment: Any = None,
        invisible: bool = False,
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
                if re.search(r"\ba closed .+? right here\b", response, re.I):
                    self.failure = "the immediate escape destination is occupied or closed"
                    return None
                if re.search(r"\bone room upwards\b", response, re.I):
                    if self.scan_retry_count < 2:
                        self.scan_retry_count += 1
                        self.scan_retry_due = now + 5.0
                        return None
                    self.failure = "the immediate escape destination is occupied or closed"
                    return None
                if not ("You can't see anything upwards." in response
                        or re.search(r"\b(?:two|three|four|five|six) rooms? upwards", response)):
                    self.failure = "the infrared escape scan had no complete direction response"
                    return None
                self.scan_retry_count = 0
                self.stage = "scanned"
            elif kind == "vision-consumed":
                return self._send("affects", now, kind="vision")
            elif kind == "sanctuary-consumed":
                return self._send("affects", now, kind="sanctuary")
            elif kind == "water-direct-recall":
                if room != "27347":
                    self.failure = "local water-breathing preparation did not return to recall"
                    return None
                self.water_prep_origin = "27347"
                self.water_prep_stage = "water-outbound"
                self.water_route_index = 0
                return self._water_preparation_command(
                    state,
                    inventory=inventory,
                    coins=coins,
                    gear_catalog=gear_catalog,
                    equipment=equipment,
                    now=now,
                    invisible=invisible,
                )
            elif kind == "water-consumed":
                if not re.search(r"\byou\s+quaff\b", response, re.IGNORECASE):
                    self.failure = "the local water-breathing potion was not acknowledged"
                    return None
                return self._send("affects", now, kind="water-affects")
            elif kind == "water-affects":
                if not water_breathing:
                    self.failure = "the local potion did not establish water breathing"
                    return None
                self.water_prep_stage = "water-return"
                self.water_return_index = 0
                return self._water_preparation_command(
                    state,
                    inventory=inventory,
                    coins=coins,
                    gear_catalog=gear_catalog,
                    equipment=equipment,
                    now=now,
                    invisible=invisible,
                )
            elif kind == "water-funding":
                return self._water_funding_command(
                    state,
                    inventory=inventory,
                    coins=coins,
                    gear_catalog=gear_catalog,
                    equipment=equipment,
                    now=now,
                    invisible=invisible,
                )
            elif kind == "water-sale-value":
                offer = LOCAL_VALUE_OFFER.search(response)
                if offer is None or normalize_item_name(offer.group("item")) != normalize_item_name(
                    self.water_sale_description or ""
                ):
                    self.failure = "the local funding shop did not quote the exact source item"
                    return None
                self.water_sale_offer = int(offer.group("coins"))
                if self.water_sale_offer <= 0:
                    self.failure = "the local funding shop offered no coins for the source item"
                    return None
                self.water_prep_stage = "water-sale-sell"
                return self._send(
                    f"sell {self.water_sale_selector or self.water_sale_keyword}",
                    now,
                    kind="water-sale-sell",
                )
            elif kind == "water-sale-sell":
                sold = LOCAL_SALE_COMPLETED.search(response)
                if sold is None or normalize_item_name(sold.group("item")) != normalize_item_name(
                    self.water_sale_description or ""
                ):
                    self.failure = "the local funding shop did not confirm the exact sale"
                    return None
                self.water_prep_stage = "water-sale-inventory"
                return self._send("inventory", now, kind="water-sale-inventory")
            elif kind == "water-sale-inventory":
                if _inventory_count(inventory, self.water_sale_description or "") >= self.water_sale_initial_count:
                    self.failure = "the source funding item remained in inventory after sale"
                    return None
                self.water_purchase = SourcePurchaseSession(
                    self.water_purchase.plan,
                )
                self.water_prep_stage = "water-purchase"
                return self._water_preparation_command(
                    state,
                    inventory=inventory,
                    coins=coins,
                    gear_catalog=gear_catalog,
                    equipment=equipment,
                    now=now,
                    invisible=invisible,
                )
            elif kind == "vision" and not infrared:
                self.failure = "the purchased pie did not produce observed infrared vision"
                return None
            elif kind == "sanctuary" and not sanctuary:
                self.failure = "the escape sanctuary potion was not confirmed"
                return None
        if self.water_prep_stage is not None:
            return self._water_preparation_command(
                state,
                inventory=inventory,
                coins=coins,
                gear_catalog=gear_catalog,
                equipment=equipment,
                now=now,
                invisible=invisible,
            )
        if self.scan_retry_due is not None:
            if now < self.scan_retry_due:
                return None
            self.scan_retry_due = None
        if not water_breathing:
            if not self.water_loss_return_active and room != "27347":
                if any(
                    str(origin) == str(room)
                    for origin, _direction, _destination in WATER_LOSS_RETURN_STEPS
                ):
                    self.water_loss_return_active = True
                    self.water_loss_return_index = 0
                elif str(room or "") not in LOCAL_WATER_RECALL_ROOMS:
                    self.failure = "underwater escape requires water breathing independently of flight"
                    return None
            if self.water_loss_return_active:
                if not state.move or state.move < 6:
                    self.failure = "water-loss return has insufficient movement"
                    return None
                if room == "27347":
                    self.water_loss_return_active = False
                    self.water_loss_return_index = 0
                    self.water_prep_origin = "27347"
                    self.water_prep_stage = "water-outbound"
                    self.water_route_index = 0
                    return self._water_preparation_command(
                        state,
                        inventory=inventory,
                        coins=coins,
                        gear_catalog=gear_catalog,
                        equipment=equipment,
                        now=now,
                        invisible=invisible,
                    )
                if self.water_loss_return_index >= len(WATER_LOSS_RETURN_STEPS):
                    self.failure = "water-loss return reached an unexpected room"
                    return None
                origin, direction, destination = WATER_LOSS_RETURN_STEPS[
                    self.water_loss_return_index
                ]
                if (
                    room != str(origin)
                    or state.exits.get(direction[0], state.exits.get(direction))
                    != str(destination)
                ):
                    self.failure = "the live water-loss return differs from source"
                    return None
                self.water_loss_return_index += 1
                return self._send(direction, now, room=destination)
            if room != "27347":
                self.water_prep_origin = "27347"
                self.water_prep_stage = "water-await-recall"
                return self._send("recall", now, kind="water-direct-recall", room=27347)
            if gear_catalog is None:
                self.failure = "local water-breathing preparation requires the source item catalog"
                return None
            self.water_prep_origin = "27347"
            self.water_prep_stage = "water-outbound"
            self.water_route_index = 0
            return self._water_preparation_command(
                state,
                inventory=inventory,
                coins=coins,
                gear_catalog=gear_catalog,
                equipment=equipment,
                now=now,
                invisible=invisible,
            )
        if not flight or not state.hp or not state.max_hp or state.hp < state.max_hp * 0.95:
            self.failure = "local-recall escape requires fresh flight and full recovery"
            return None
        if not state.move or state.move < 30:
            self.failure = "local-recall escape has insufficient movement"
            return None
        if room == "3001":
            self.stage = "complete"
            return None
        if (
            room == "27347"
            and self.stage in {"escape", "scanned", "supplied"}
            and not infrared
            and not light_available
        ):
            # A reconnect or a long safe wait can let the temporary pie
            # expire after the cursor has already entered the escape phase.
            # Re-enter the audited shop loop only from the safe local recall
            # room; dark-room states remain fail-closed below.
            self.stage = "new"
            self.shop_index = 0
            self.scans.clear()
            self.purchase = SourcePurchaseSession(self.purchase.plan)
        if self.stage == "backtrack":
            if room == "27347":
                self.stage = "new"
            else:
                if self.backtrack_index >= len(SHOP_RETURN_STEPS):
                    self.failure = "local-recall shop-route backtrack reached an unexpected room"
                    return None
                origin, direction, destination = SHOP_RETURN_STEPS[self.backtrack_index]
                if (
                    room != str(origin)
                    or state.exits.get(direction[0], state.exits.get(direction))
                    != str(destination)
                ):
                    self.failure = "the live local-recall shop backtrack differs from source"
                    return None
                self.backtrack_index += 1
                return self._send(direction, now, room=destination)
        if self.stage == "new":
            illuminated = infrared or light_available
            self.stage = "escape" if illuminated else "shop"
            if not illuminated and room != "27347":
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
        if not infrared and not light_available:
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
                "failure": self.failure, "purchase": self.purchase.evidence(),
                "scans": self.scans,
                "scan_retry_count": self.scan_retry_count,
                "scan_retry_due": self.scan_retry_due,
                "backtrack_index": self.backtrack_index,
                "water_prep_stage": self.water_prep_stage,
                "water_prep_origin": self.water_prep_origin,
                "water_loss_return_active": self.water_loss_return_active,
                "water_loss_return_index": self.water_loss_return_index,
                "water_purchase": self.water_purchase.evidence(),
                "water_sale": {
                    "description": self.water_sale_description,
                    "vnum": self.water_sale_vnum,
                    "offer": self.water_sale_offer,
                    "initial_count": self.water_sale_initial_count,
                },
                "water_funding_attempted": self.water_funding_attempted,
                "water_funding_attempts": self.water_funding_attempts,
                "water_funding_item_vnums": list(self.water_funding_item_vnums),
                "water_funding_origin": self.water_funding_origin,
                "water_funding_route_index": self.water_funding_route_index,
                "water_funding_return_index": self.water_funding_return_index,
                "water_funding_liquidation": self.water_funding_liquidation.evidence(),
                }
