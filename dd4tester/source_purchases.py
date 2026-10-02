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
SHOP_LIST_ITEM = re.compile(
    r"^\s*\[\s*(?P<level>\d+)\s+(?P<price>\d+)\]\s+"
    r"(?:(?P<target>\[#\d+\])\s+)?(?P<name>.+?)\s*$", re.MULTILINE,
)


@dataclass(frozen=True)
class SourcePurchase:
    object_vnum: int
    shopkeeper_vnum: int
    room_vnum: int
    description: str
    keyword: str
    maximum_price: int
    coin_reserve: int = 100


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

    def observe(self, text: str) -> None:
        if self.stage in {"visibility", "listing", "buying", "inventory"}:
            self.response = (self.response + text)[-8000:]

    def expire(self, now: float) -> bool:
        if self.deadline is not None and now >= self.deadline and not _DD4_PROMPT.search(self.response):
            self.failure = "shop response did not complete within five seconds"
            self.stage, self.deadline = "failed", None
            return True
        return False

    def next_command(
        self, *, room_vnum: str | None, level: int, coins: int,
        inventory: Sequence[tuple[str, str | None]], now: float, invisible: bool = False,
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
        if self.stage == "new":
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
            if not 0 < self.price <= min(self.plan.maximum_price, coins - self.plan.coin_reserve):
                self.failure, self.stage = "quoted price exceeds the reserved purchase balance", "failed"
                return None
            self.stage, command = "buying", f"buy {self.selector}"
        elif self.stage == "buying":
            if not re.search(r"\bYou buy\b", self.response):
                self.failure, self.stage = "shop did not acknowledge the purchase", "failed"
                return None
            self.stage, command = "inventory", "inventory"
        elif self.stage == "inventory":
            if count <= self.initial_count:
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
                "price": self.price, "selector": self.selector, "failure": self.failure}
