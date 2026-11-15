"""Source-backed travel supplies and one bounded, live-priced purchase."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .equipment import is_releasable_funding_item, normalize_item_name
from .hunt_candidates import (
    ITEM_POTION, WorldSource, _reset_object_vnums, _shortest_paths_from,
    potion_spell_names, source_class_teacher_route_for_level,
    source_route_hazard_rejections, source_route_movement_cost,
    source_route_requires_flight,
)
from .observations import _DD4_PROMPT
from .specials import SAFE_NONCOMBAT_SPECIALS, TRANSIT_SAFE_COMBAT_ONLY_SPECIALS
from .teaching import practice_gain, teacher_capacity
from .training import training_priorities_for


TRAINING_TRAVEL_SUPPLY_KEY = "campaign_training_travel_supply"
ROUTE_INVISIBILITY_SUPPLY_KEY = "campaign_route_invisibility_supply"
ROUTE_INVISIBILITY_FUNDING_RETRY_STATUS = "funding-required"
SOURCE_PURCHASE_BALANCE_FAILURE = (
    "quoted price exceeds the reserved purchase balance"
)
ROUTE_INVISIBILITY_OBJECT_VNUM = 19021
ROUTE_INVISIBILITY_SHOPKEEPER_VNUM = 19024
ROUTE_INVISIBILITY_SHOP_ROOM_VNUM = 19070
ROUTE_INVISIBILITY_PURCHASE_QUANTITY = 1
_MIRROR_GARDENER_VNUM = 19036
_MIRROR_GARDENER_MAX_PURSE = 6250
SHOP_LIST_ITEM = re.compile(
    r"^\s*\[\s*(?P<level>\d+)\s+(?P<price>\d+)\]\s+"
    r"(?:(?P<target>\[#\d+\])\s+)?(?P<name>.+?)\s*$", re.MULTILINE,
)
SHOP_VALUE_OFFER = re.compile(
    r"tells you 'I'll give you (?P<coins>\d+) coins? for (?P<item>.+?)'\.",
    re.IGNORECASE,
)
SHOP_SALE_COMPLETED = re.compile(
    r"You sell (?P<item>.+?) for (?P<coins>\d+) coins?\.",
    re.IGNORECASE,
)


@dataclass
class ShopCommandReply:
    """Keep one shop reply together across Telnet chunks, with a fixed deadline."""

    command: str | None = None
    response: str = ""
    deadline: float | None = None
    complete: bool = False
    failure: str | None = None

    def begin(self, command: str, *, now: float) -> None:
        self.command = command
        self.response = ""
        self.deadline = now + 5
        self.complete = False
        self.failure = None

    def observe(self, text: str, *, now: float) -> None:
        if self.command is None or self.complete or self.failure:
            return
        if self.expired(now):
            return
        if len(self.response) + len(text) > 8000:
            self.failure = "shop reply exceeded the 8000-character limit"
            return
        self.response += text
        self.complete = _DD4_PROMPT.search(self.response) is not None

    def expired(self, now: float) -> bool:
        if not self.complete and self.deadline is not None and now >= self.deadline:
            self.failure = "shop reply did not complete within five seconds"
        return self.failure is not None


@dataclass(frozen=True)
class SourcePurchase:
    object_vnum: int
    shopkeeper_vnum: int
    room_vnum: int
    description: str
    keyword: str
    maximum_price: int
    coin_reserve: int = 100
    quantity: int = 1


@dataclass(frozen=True)
class SourceLiquidation:
    """Source-audited shop stop for selling a bounded number of items."""

    shopkeeper_vnum: int
    room_vnum: int
    accepted_item_types: tuple[int, ...]
    maximum_items: int = 4


@dataclass(frozen=True)
class TrainingTravelSupply:
    purchase: SourcePurchase
    commands: tuple[str, ...]
    room_vnums: tuple[int, ...]
    required_move: int
    teacher_vnum: int
    teacher_room_vnum: int
    useful_skills: tuple[str, ...]

    def evidence(self) -> dict[str, Any]:
        return {
            "object_vnum": self.purchase.object_vnum,
            "shopkeeper_vnum": self.purchase.shopkeeper_vnum,
            "room_vnum": self.purchase.room_vnum,
            "teacher_vnum": self.teacher_vnum,
            "teacher_room_vnum": self.teacher_room_vnum,
            "useful_skills": list(self.useful_skills),
            "effect": "invis", "maximum_price": self.purchase.maximum_price,
            "budget_revision": 2,
        }


@dataclass(frozen=True)
class RouteInvisibilitySupply:
    """Source-audited invisibility reserve for a blocked field route."""

    purchase: SourcePurchase
    commands: tuple[str, ...]
    room_vnums: tuple[int, ...]
    required_move: int

    def evidence(self) -> dict[str, Any]:
        return {
            "object_vnum": self.purchase.object_vnum,
            "shopkeeper_vnum": self.purchase.shopkeeper_vnum,
            "room_vnum": self.purchase.room_vnum,
            "effect": "invis",
            "route_rooms": list(self.room_vnums),
            "required_move": self.required_move,
            "maximum_price": self.purchase.maximum_price,
            "quantity": max(1, int(self.purchase.quantity)),
            "policy_revision": 2,
        }


def _known_coin_value(state: Mapping[str, Any]) -> int | None:
    currencies = state.get("currencies")
    if not isinstance(currencies, Mapping):
        currencies = state.get("progress")
    if not isinstance(currencies, Mapping):
        return None
    multipliers = {
        "copper": 1,
        "silver": 10,
        "gold": 100,
        "platinum": 1000,
        "electrum": 50,
        "adamantite": 10000,
        "starmetal": 100000,
        "steel": 1000000,
        "titanium": 10000000,
    }
    total = 0
    for name, multiplier in multipliers.items():
        value = currencies.get(name, 0)
        if type(value) is not int or value < 0:
            return None
        total += value * multiplier
    return total


def _state_has_active_invisibility(state: Mapping[str, Any]) -> bool:
    """Recognize a live invisibility affect without trusting stale route data."""
    affects = state.get("affects")
    if not isinstance(affects, (list, tuple, set, frozenset)):
        return False
    for raw_entry in affects:
        entries = (
            raw_entry
            if isinstance(raw_entry, (list, tuple, set, frozenset))
            else (raw_entry,)
        )
        for affect in entries:
            if not isinstance(affect, Mapping):
                continue
            if str(affect.get("name") or "").casefold() not in {
                "invis",
                "invisibility",
            }:
                continue
            duration = affect.get("duration")
            if duration is None:
                return True
            try:
                return int(duration) > 0
            except (TypeError, ValueError):
                return True
    return False


def route_invisibility_supply(
    world: WorldSource | None,
    state: Mapping[str, Any],
    *,
    carried_descriptions: Sequence[str] = (),
    ignore_attempt: bool = False,
) -> RouteInvisibilitySupply | None:
    """Plan the exact Mirror Realm invisibility-potion purchase.

    The route crosses the Mirror gardener's economic-only thief special. DD4
    can steal at most 20 percent per attempt, so the source-backed route is
    admitted only while the known purse is at most 6,250 copper-equivalent.
    The live shop quote, purchase acknowledgement, inventory gain, quaff, and
    active affect remain authoritative.
    """
    level = state.get("level")
    boot = state.get("world_boot_id")
    if (
        world is None
        or type(level) is not int
        or level < 2
        or not boot
        or str(state.get("room_vnum")) != "3054"
        or state.get("dead") is True
        or state.get("in_combat") is True
        or type(state.get("hp")) is not int
        or type(state.get("max_hp")) is not int
        or state.get("max_hp", 0) <= 0
        or state["hp"] < state["max_hp"] * 0.95
        or any(
            normalize_item_name(description)
            == "a clear potion of invisibility"
            for description in carried_descriptions
        )
    ):
        return None
    prior = state.get(ROUTE_INVISIBILITY_SUPPLY_KEY)
    retry_after_funding = bool(
        isinstance(prior, Mapping)
        and prior.get("status") == ROUTE_INVISIBILITY_FUNDING_RETRY_STATUS
        and prior.get("funding_failure") == SOURCE_PURCHASE_BALANCE_FAILURE
    )
    retry_after_expired_acquisition = bool(
        isinstance(prior, Mapping)
        and prior.get("status") == "acquired"
        and not _state_has_active_invisibility(state)
    )
    if (
        not ignore_attempt
        and isinstance(prior, Mapping)
        and prior.get("boot_id") == boot
        and prior.get("level") == level
        and not retry_after_funding
        and not retry_after_expired_acquisition
    ):
        return None
    purse = _known_coin_value(state)
    if purse is None or purse <= 0 or purse > _MIRROR_GARDENER_MAX_PURSE:
        return None

    item = world.objects.get(ROUTE_INVISIBILITY_OBJECT_VNUM)
    vendor = world.mobiles.get(ROUTE_INVISIBILITY_SHOPKEEPER_VNUM)
    item_spells = potion_spell_names(item) if item is not None else ()
    if (
        item is None
        or item.item_type != ITEM_POTION
        or not item_spells
        or item_spells[0] != "invis"
        or vendor is None
        or vendor.vnum not in world.shopkeepers
        or vendor.aggressive
        or not vendor.sentinel
        or vendor.wanders
        or vendor.programs
        or vendor.attack_programs
        or set(world.mobile_specials.get(vendor.vnum, ()))
        - {"spec_cast_mage"}
        or sum(
            normalize_item_name(other.short_description)
            == normalize_item_name(item.short_description)
            for other in world.objects.values()
        ) != 1
    ):
        return None
    reset = next(
        (
            value
            for value in world.mob_resets
            if value.mobile_vnum == vendor.vnum
            and value.room_vnum == ROUTE_INVISIBILITY_SHOP_ROOM_VNUM
            and ROUTE_INVISIBILITY_OBJECT_VNUM in _reset_object_vnums(value)
            and value.maximum_count == 1
        ),
        None,
    )
    if reset is None:
        return None
    paths = _shortest_paths_from(world.rooms, 3001)
    path = paths.get(ROUTE_INVISIBILITY_SHOP_ROOM_VNUM)
    if path is None or not path[0]:
        return None
    commands, rooms = path[0], tuple(path[1])
    if (
        any(world.rooms[vnum].random_exits for vnum in rooms)
        or any(
            world.rooms[vnum].room_flags & ((1 << 9) | (1 << 11) | (1 << 13))
            for vnum in rooms
        )
    ):
        return None
    route_hazards = source_route_hazard_rejections(
        world,
        rooms,
        character_level=level,
        combat_at_destination=False,
        economic_special_mobile_vnums=(_MIRROR_GARDENER_VNUM,),
        economic_transit_allow_equipped_mobile_vnums=(
            _MIRROR_GARDENER_VNUM,
        ),
    )
    if route_hazards:
        gardener = world.mobiles.get(_MIRROR_GARDENER_VNUM)
        if (
            len(route_hazards) != 1
            or "gardener" not in route_hazards[0].casefold()
            or gardener is None
            or gardener.aggressive
            or not gardener.wanders
            or gardener.programs
            or gardener.attack_programs
            or set(world.mobile_specials.get(_MIRROR_GARDENER_VNUM, ()))
            != {"spec_thief"}
        ):
            return None
    keyword = next(
        (
            value
            for value in item.keywords.casefold().split()
            if re.fullmatch(r"[a-z][a-z0-9-]*", value)
        ),
        None,
    )
    if keyword is None:
        return None
    return RouteInvisibilitySupply(
        purchase=SourcePurchase(
            ROUTE_INVISIBILITY_OBJECT_VNUM,
            ROUTE_INVISIBILITY_SHOPKEEPER_VNUM,
            ROUTE_INVISIBILITY_SHOP_ROOM_VNUM,
            item.short_description,
            keyword,
            maximum_price=10000,
            coin_reserve=0,
            quantity=ROUTE_INVISIBILITY_PURCHASE_QUANTITY,
        ),
        commands=tuple(commands),
        room_vnums=rooms,
        required_move=source_route_movement_cost(world, rooms) + 20,
    )


def training_travel_supply(
    world: WorldSource | None, state: Mapping[str, Any], character_class: str,
    *, carried_descriptions: Sequence[str] = (), ignore_attempt: bool = False,
) -> TrainingTravelSupply | None:
    """Supply a blocked advanced lesson; acquiring a potion grants no travel permission."""
    level = state.get("level")
    boot = state.get("world_boot_id")
    audit = state.get("campaign_training_audit")
    repair = state.get("campaign_training_deficit_repair")
    prior = state.get(TRAINING_TRAVEL_SUPPLY_KEY)
    stats = state.get("stats")
    progress = state.get("progress")
    if (
        world is None or type(level) is not int or not 20 <= level < 30
        or not boot or str(state.get("room_vnum")) != "3054"
        or state.get("dead") or state.get("in_combat")
        or not isinstance(audit, Mapping) or audit.get("observed") is not True
        or audit.get("level") != level or audit.get("boot_id") != boot
        or not isinstance(repair, Mapping) or repair.get("attempted") is not True
        or repair.get("level") != level or repair.get("boot_id") != boot
        or not isinstance(stats, Mapping) or not isinstance(progress, Mapping)
        or type(stats.get("fame")) is not int or stats["fame"] < 0
    ):
        return None
    legacy_quote_retry = False
    if (not ignore_attempt and isinstance(prior, Mapping)
            and prior.get("level") == level and prior.get("boot_id") == boot):
        offers = state.get("campaign_source_purchases")
        # The first implementation capped all supplies at 100 copper. Repair
        # only its unbought quote failure once, without reopening other losses.
        legacy_quote_retry = bool(
            prior.get("budget_revision", 1) == 1 and prior.get("maximum_price") == 100
            and isinstance(offers, list) and len(offers) == 1
            and isinstance(offers[0], Mapping)
            and all(offers[0].get(k) == prior.get(k)
                    for k in ("object_vnum", "shopkeeper_vnum", "room_vnum"))
            and offers[0].get("stage") == "failed" and offers[0].get("price") is None
            and offers[0].get("failure") == "no single affordable, level-usable exact shop offer"
        )
        if not legacy_quote_retry:
            return None
    hp, maximum_hp = state.get("hp"), state.get("max_hp")
    if (type(hp) is not int or type(maximum_hp) is not int
            or maximum_hp <= 0 or hp < maximum_hp * 0.95):
        return None
    teacher_route = source_class_teacher_route_for_level(world, character_class, 20)
    if teacher_route is None or not teacher_route.steps:
        return None
    teacher_rooms = (int(teacher_route.steps[0][0]), *(int(s[2]) for s in teacher_route.steps))
    # Invisibility must actually remove all diagnosed route hazards, not merely
    # exist in an item. The later executor still needs a fresh, live affect.
    if (
        not source_route_hazard_rejections(
            world, teacher_rooms, character_level=level, combat_at_destination=False,
        )
        or source_route_hazard_rejections(
            world, teacher_rooms, character_level=level,
            combat_at_destination=False, invisible=True, audit_invisible_equipment=True,
        )
    ):
        return None
    known = audit.get("known_skill_levels")
    learnable = audit.get("learnable_skill_levels")
    if not isinstance(known, Mapping) or not isinstance(learnable, Mapping):
        return None
    skills = {**learnable, **known}
    teachings = dict(world.mobiles[teacher_route.mobile_vnum].teachings)
    useful = []
    for priority in training_priorities_for(character_class, subclass=state.get("subclass")):
        current = skills.get(priority.skill)
        balance = audit.get(f"{priority.practice_type}_practices")
        if (
            not priority.automated or type(current) is not int
            or type(balance) is not int or balance <= 0
            or current >= priority.target_percent or current < 0
            or level < (priority.minimum_level or 0)
        ):
            continue
        gain = practice_gain(current, teacher_capacity(teachings, priority.skill, world.skill_groups),
                             priority.practice_type, stats)
        if gain is not None and gain > current:
            useful.append(priority.skill)
    if not useful:
        return None
    coins = sum(progress.get(name, 0) * multiplier for name, multiplier in
                (("platinum", 1000), ("gold", 100), ("silver", 10), ("copper", 1))
                if type(progress.get(name, 0)) is int)
    budget = coins - 100
    if budget <= 0 or (legacy_quote_retry and budget <= 100):
        return None
    paths = _shortest_paths_from(world.rooms, 3001)
    carried = {normalize_item_name(s) for s in carried_descriptions}
    plans = []
    for reset in world.mob_resets:
        vendor = world.mobiles.get(reset.mobile_vnum)
        if (
            vendor is None or vendor.vnum not in world.shopkeepers
            or not vendor.sentinel or vendor.aggressive or vendor.programs
            or not set(world.mobile_specials.get(vendor.vnum, ())) <= (
                SAFE_NONCOMBAT_SPECIALS | TRANSIT_SAFE_COMBAT_ONLY_SPECIALS
            )
            or reset.maximum_count != 1
            or sum(r.mobile_vnum == vendor.vnum for r in world.mob_resets) != 1
        ):
            continue
        path = paths.get(reset.room_vnum)
        if (
            path is None or not path[0] or len(path[0]) > 40
            or source_route_requires_flight(world, path[1])
            or any(world.rooms[v].random_exits for v in path[1])
            or any(world.rooms[v].room_flags & ((1 << 9) | (1 << 11) | (1 << 13))
                   for v in path[1])
            or source_route_hazard_rejections(
                world, path[1], character_level=level, combat_at_destination=False,
            )
        ):
            continue
        required_move = source_route_movement_cost(world, path[1]) + 20
        if type(state.get("max_move")) is not int or required_move > state["max_move"]:
            continue
        for vnum in _reset_object_vnums(reset):
            item = world.objects.get(vnum)
            if (
                item is None or item.item_type != ITEM_POTION
                or (legacy_quote_retry and item.vnum != prior.get("object_vnum"))
                or potion_spell_names(item) != ("invis",)
                or not is_releasable_funding_item(item)
                or item.source_cost <= 0 or item.source_cost > budget
                or normalize_item_name(item.short_description) in carried
                or sum(normalize_item_name(o.short_description) == normalize_item_name(item.short_description)
                       for o in world.objects.values()) != 1
            ):
                continue
            if any(type(stats.get(k)) is not int for k in
                   ("carry_num", "maxcarry_num", "carry_wt", "maxcarry_wt")):
                continue
            if stats["carry_num"] >= stats["maxcarry_num"] or stats["carry_wt"] + item.weight > stats["maxcarry_wt"]:
                continue
            keyword = next((k for k in item.keywords.split()
                            if k in normalize_item_name(item.short_description).split()), None)
            if keyword is None:
                continue
            plans.append(TrainingTravelSupply(
                SourcePurchase(item.vnum, vendor.vnum, reset.room_vnum,
                               item.short_description, keyword, budget),
                path[0], path[1], required_move, teacher_route.mobile_vnum,
                teacher_route.room_vnum, tuple(dict.fromkeys(useful)),
            ))
    return min(plans, key=lambda p: (len(p.commands), p.purchase.object_vnum), default=None)


@dataclass
class SourcePurchaseSession:
    plan: SourcePurchase
    stage: str = "new"
    response: str = ""
    deadline: float | None = None
    failure: str | None = None
    price: int | None = None
    selector: str | None = None
    initial_count: int = 0
    funding_attempts: int = 0
    funding_item_vnums: tuple[int, ...] = ()
    funding_item_description: str | None = None
    funding_item_selector: str | None = None
    funding_item_initial_count: int = 0
    purchased_count: int = 0

    def observe(self, text: str) -> None:
        if self.stage in {
            "visibility", "listing", "buying", "inventory",
            "funding-value", "funding-sell", "funding-inventory",
        }:
            self.response = (self.response + text)[-8000:]

    def expire(self, now: float) -> bool:
        if self.deadline is not None and now >= self.deadline and not _DD4_PROMPT.search(self.response):
            self.failure = "shop response did not complete within five seconds"
            self.stage, self.deadline = "failed", None
            return True
        return False

    def next_command(
        self, *, room_vnum: str | None, level: int, coins: int,
        inventory: Sequence[tuple[str, str | None]], now: float,
        invisible: bool = False,
        funding_item: tuple[str, str, int] | None = None,
    ) -> str | None:
        self.expire(now)
        if self.failure or self.stage == "complete":
            return None
        if str(room_vnum) != str(self.plan.room_vnum):
            self.failure, self.stage = "shop room identity changed", "failed"
            return None
        count = sum(normalize_item_name(name) == normalize_item_name(self.plan.description)
                    for name, _ in inventory)
        command = None
        if self.stage == "funding-value":
            if not _DD4_PROMPT.search(self.response):
                return None
            offer = SHOP_VALUE_OFFER.search(self.response)
            if (
                offer is None
                or normalize_item_name(offer.group("item"))
                != normalize_item_name(self.funding_item_description or "")
            ):
                self.failure = "funding shop did not quote the exact source item"
                self.stage = "failed"
                return None
            self.stage = "funding-sell"
            command = f"sell {self.funding_item_selector}"
        elif self.stage == "funding-sell":
            if not _DD4_PROMPT.search(self.response):
                return None
            sold = SHOP_SALE_COMPLETED.search(self.response)
            if (
                sold is None
                or normalize_item_name(sold.group("item"))
                != normalize_item_name(self.funding_item_description or "")
            ):
                self.failure = "funding shop did not confirm the exact sale"
                self.stage = "failed"
                return None
            self.stage = "funding-inventory"
            command = "inventory"
        elif self.stage == "funding-inventory":
            if not _DD4_PROMPT.search(self.response):
                return None
            funding_count = sum(
                normalize_item_name(name)
                == normalize_item_name(self.funding_item_description or "")
                for name, _ in inventory
            )
            if funding_count >= self.funding_item_initial_count:
                self.failure = "funding item remained in inventory after sale"
                self.stage = "failed"
                return None
            self.funding_item_description = None
            self.funding_item_selector = None
            self.funding_item_initial_count = 0
            self.stage = "listing"
            command = f"list {self.plan.keyword}"
        elif self.stage == "new":
            self.initial_count = count
            if invisible:
                self.stage, command = "visibility", "vis"
            else:
                self.stage, command = "listing", f"list {self.plan.keyword}"
        elif not _DD4_PROMPT.search(self.response):
            return None
        elif self.stage == "visibility":
            if invisible:
                self.failure, self.stage = "visibility was not confirmed after one request", "failed"
                return None
            self.stage, command = "listing", f"list {self.plan.keyword}"
        elif self.stage == "listing":
            offers = [m for m in SHOP_LIST_ITEM.finditer(self.response)
                      if normalize_item_name(m.group("name")) == normalize_item_name(self.plan.description)
                      and m.group("target") is not None
                      and int(m.group("level")) <= level]
            if len(offers) != 1:
                self.failure, self.stage = "no single level-usable exact shop offer", "failed"
                return None
            offer = offers[0]
            self.price, self.selector = int(offer.group("price")), offer.group("target")[1:-1]
            quantity = max(1, int(self.plan.quantity))
            if not 0 < self.price <= self.plan.maximum_price:
                self.failure, self.stage = "quoted price exceeds the purchase maximum", "failed"
                return None
            available_coins = coins - self.plan.coin_reserve
            if self.price * quantity > available_coins:
                if funding_item is None or self.funding_attempts >= 4:
                    self.failure, self.stage = SOURCE_PURCHASE_BALANCE_FAILURE, "failed"
                    return None
                description, selector, vnum = funding_item
                if (
                    not description
                    or not selector
                    or int(vnum) in self.funding_item_vnums
                ):
                    self.failure, self.stage = "no distinct source item was available for purchase funding", "failed"
                    return None
                self.funding_attempts += 1
                self.funding_item_vnums = (*self.funding_item_vnums, int(vnum))
                self.funding_item_description = description
                self.funding_item_selector = selector
                self.funding_item_initial_count = sum(
                    normalize_item_name(name) == normalize_item_name(description)
                    for name, _ in inventory
                )
                self.stage = "funding-value"
                self.response, self.deadline = "", now + 5.0
                return f"value {selector}"
            if not 0 < self.price * quantity <= available_coins:
                self.failure, self.stage = SOURCE_PURCHASE_BALANCE_FAILURE, "failed"
                return None
            self.purchased_count = 0
            self.stage, command = "buying", f"buy {self.selector}"
        elif self.stage == "buying":
            if not re.search(r"\bYou buy\b", self.response):
                if re.search(
                    r"can't carry that (?:many items|much weight)",
                    self.response,
                    re.IGNORECASE,
                ):
                    self.failure = (
                        "shop rejected purchase because carrying capacity was full"
                    )
                else:
                    self.failure = "shop did not acknowledge the purchase"
                self.stage = "failed"
                return None
            self.purchased_count += 1
            quantity = max(1, int(self.plan.quantity))
            if self.purchased_count < quantity:
                self.response, self.deadline = "", now + 5.0
                command = f"buy {self.selector}"
            else:
                self.stage, command = "inventory", "inventory"
        elif self.stage == "inventory":
            quantity = max(1, int(self.plan.quantity))
            if count < self.initial_count + quantity:
                self.failure, self.stage = "purchased object was not confirmed in inventory", "failed"
            else:
                self.stage = "complete"
            self.deadline = None
            return None
        if command is not None:
            self.response, self.deadline = "", now + 5.0
        return command

    def evidence(self) -> dict[str, Any]:
        return {"object_vnum": self.plan.object_vnum, "room_vnum": self.plan.room_vnum,
                "shopkeeper_vnum": self.plan.shopkeeper_vnum, "stage": self.stage,
                "price": self.price, "selector": self.selector, "failure": self.failure,
                "funding_attempts": self.funding_attempts,
                "quantity": max(1, int(self.plan.quantity)),
                "purchased_count": self.purchased_count,
                "funding_item_vnums": list(self.funding_item_vnums),
                "funding_item_description": self.funding_item_description,
                "funding_item_selector": self.funding_item_selector}


@dataclass
class SourceLiquidationSession:
    """Sell source-identified items with value, sale, and inventory receipts."""

    plan: SourceLiquidation
    stage: str = "new"
    response: str = ""
    deadline: float | None = None
    failure: str | None = None
    funding_item_vnums: tuple[int, ...] = ()
    funding_item_description: str | None = None
    funding_item_selector: str | None = None
    funding_item_initial_count: int = 0

    def observe(self, text: str) -> None:
        if self.stage in {"value", "sell", "inventory"}:
            self.response = (self.response + text)[-8000:]

    def expire(self, now: float) -> bool:
        if (
            self.deadline is not None
            and now >= self.deadline
            and not _DD4_PROMPT.search(self.response)
        ):
            self.failure = "liquidation shop response did not complete within five seconds"
            self.stage, self.deadline = "failed", None
            return True
        return False

    def next_command(
        self,
        *,
        room_vnum: str | None,
        inventory: Sequence[tuple[str, str | None]],
        now: float,
        funding_item: tuple[str, str, int] | None = None,
    ) -> str | None:
        self.expire(now)
        if self.failure or self.stage == "complete":
            return None
        if str(room_vnum) != str(self.plan.room_vnum):
            self.failure, self.stage = "liquidation shop room identity changed", "failed"
            return None
        if self.stage == "new":
            if len(self.funding_item_vnums) >= max(1, self.plan.maximum_items):
                self.stage = "complete"
                return None
            if funding_item is None:
                self.stage = "complete"
                return None
            description, selector, vnum = funding_item
            if (
                not description
                or not selector
                or int(vnum) in self.funding_item_vnums
            ):
                self.failure = "no distinct source item was available for liquidation"
                self.stage = "failed"
                return None
            self.funding_item_description = description
            self.funding_item_selector = selector
            self.funding_item_vnums = (*self.funding_item_vnums, int(vnum))
            self.funding_item_initial_count = sum(
                normalize_item_name(name) == normalize_item_name(description)
                for name, _ in inventory
            )
            self.stage = "value"
            self.response, self.deadline = "", now + 5.0
            return f"value {selector}"
        if not _DD4_PROMPT.search(self.response):
            return None
        if self.stage == "value":
            offer = SHOP_VALUE_OFFER.search(self.response)
            if (
                offer is None
                or normalize_item_name(offer.group("item"))
                != normalize_item_name(self.funding_item_description or "")
            ):
                self.failure = "liquidation shop did not quote the exact source item"
                self.stage = "failed"
                return None
            self.stage = "sell"
            self.response, self.deadline = "", now + 5.0
            return f"sell {self.funding_item_selector}"
        if self.stage == "sell":
            sold = SHOP_SALE_COMPLETED.search(self.response)
            if (
                sold is None
                or normalize_item_name(sold.group("item"))
                != normalize_item_name(self.funding_item_description or "")
            ):
                self.failure = "liquidation shop did not confirm the exact sale"
                self.stage = "failed"
                return None
            self.stage = "inventory"
            self.response, self.deadline = "", now + 5.0
            return "inventory"
        if self.stage == "inventory":
            remaining = sum(
                normalize_item_name(name)
                == normalize_item_name(self.funding_item_description or "")
                for name, _ in inventory
            )
            if remaining >= self.funding_item_initial_count:
                self.failure = "liquidation item remained in inventory after sale"
                self.stage = "failed"
                return None
            self.funding_item_description = None
            self.funding_item_selector = None
            self.funding_item_initial_count = 0
            self.response, self.deadline = "", None
            self.stage = "complete" if len(self.funding_item_vnums) >= max(
                1, self.plan.maximum_items
            ) else "new"
            return None
        self.failure = f"unknown liquidation stage: {self.stage}"
        self.stage = "failed"
        return None

    def evidence(self) -> dict[str, Any]:
        return {
            "shopkeeper_vnum": self.plan.shopkeeper_vnum,
            "room_vnum": self.plan.room_vnum,
            "accepted_item_types": list(self.plan.accepted_item_types),
            "maximum_items": self.plan.maximum_items,
            "stage": self.stage,
            "failure": self.failure,
            "funding_item_vnums": list(self.funding_item_vnums),
            "funding_item_description": self.funding_item_description,
            "funding_item_selector": self.funding_item_selector,
        }
