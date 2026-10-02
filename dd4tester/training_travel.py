"""One noncombat teacher journey using a verified, source-backed consumable."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .equipment import is_releasable_funding_item, normalize_item_name
from .hunt_candidates import (
    ITEM_POTION, ObjectSource, SourceTeacherRoute, WorldSource, potion_spell_names,
    source_class_teacher_route_for_level, source_route_hazard_rejections,
    source_route_movement_cost, source_route_requires_flight,
)
from .observations import _DD4_PROMPT
from .source_purchases import TRAINING_TRAVEL_SUPPLY_KEY
from .teaching import practice_gain, teacher_capacity
from .training import training_priorities_for


TRAINING_TRAVEL_KEY = "campaign_consumable_training_travel"
_INVENTORY_FOOTER = re.compile(r"you are carrying \d+/\d+ items")


def carried_potion_keyword(
    objects: Mapping[int, ObjectSource], object_vnum: int,
    descriptions: Sequence[str],
) -> str | None:
    """Prove one source keyword selects only the intended carried potion."""
    item = objects.get(object_vnum)
    if item is None:
        return None
    names = [normalize_item_name(name) for name in descriptions]
    target_name = normalize_item_name(item.short_description)
    if names.count(target_name) != 1:
        return None
    by_name: dict[str, list[ObjectSource]] = {}
    for obj in objects.values():
        by_name.setdefault(normalize_item_name(obj.short_description), []).append(obj)
    if any(name not in by_name for name in names) or len(by_name[target_name]) != 1:
        return None
    for word in item.keywords.casefold().split():
        if re.fullmatch(r"[a-z][a-z0-9-]*", word) and all(
            not any(keyword.startswith(word) for keyword in obj.keywords.casefold().split())
            for name in names if name != target_name for obj in by_name[name]
        ):
            return word
    return None


def _listed_inventory(response: str) -> Counter[str]:
    listing = response.partition("Your backpack contains:")[2]
    prompt = _DD4_PROMPT.search(listing)
    if prompt is None:
        return Counter()
    names: Counter[str] = Counter()
    lines = [normalize_item_name(raw) for raw in listing[:prompt.start()].splitlines()]
    lines = [line for line in lines if line]
    # do_inventory ends with a carried-total footer, which includes worn gear.
    if lines and _INVENTORY_FOOTER.fullmatch(lines[-1]):
        lines.pop()
    for name in lines:
        quantity = re.fullmatch(r"\(\s*(\d+)\)\s*(.+)", name)
        if quantity:
            names[normalize_item_name(quantity[2])] += int(quantity[1])
        else:
            names[name] += 1
    return names


def inventory_footer_mismatch(response: str, descriptions: Sequence[str]) -> bool:
    """Identify the exact legacy mismatch, not a generally incomplete listing."""
    listing = response.partition("Your backpack contains:")[2]
    prompt = _DD4_PROMPT.search(listing)
    if prompt is None:
        return False
    lines = [normalize_item_name(line) for line in listing[:prompt.start()].splitlines()]
    lines = [line for line in lines if line]
    return bool(
        lines and _INVENTORY_FOOTER.fullmatch(lines[-1]) and descriptions
        and _listed_inventory(response) == Counter(normalize_item_name(n) for n in descriptions)
    )


@dataclass(frozen=True)
class TrainingTravelPlan:
    teacher: SourceTeacherRoute
    object_vnum: int
    description: str
    rooms: tuple[int, ...]
    gains: tuple[tuple[str, int, int], ...]
    movement_remaining: tuple[int, ...]
    level: int
    boot_id: str
    setup_repair: bool = False
    unique_keyword: str | None = None

    def evidence(self) -> dict[str, Any]:
        return {
            "setup_revision": 4, "setup_repair": self.setup_repair,
            "unique_keyword": self.unique_keyword,
            "object_vnum": self.object_vnum, "teacher_vnum": self.teacher.mobile_vnum,
            "teacher_room_vnum": self.teacher.room_vnum,
            "route_rooms": list(self.rooms), "required_move": self.movement_remaining[0],
            "expected_gains": [dict(skill=s, current=c, expected=e) for s, c, e in self.gains],
        }


def plan_training_travel(
    world: WorldSource | None, state: Mapping[str, Any], character_class: str,
    *, carried_descriptions: Sequence[str], ignore_attempt: bool = False,
) -> TrainingTravelPlan | None:
    level, boot = state.get("level"), state.get("world_boot_id")
    supply = state.get(TRAINING_TRAVEL_SUPPLY_KEY)
    prior = state.get(TRAINING_TRAVEL_KEY)
    audit, stats = state.get("campaign_training_audit"), state.get("stats")
    if (
        world is None or type(level) is not int or not 20 <= level < 30 or not boot
        or str(state.get("room_vnum")) != "3054" or state.get("dead") or state.get("in_combat")
        or not isinstance(supply, Mapping) or type(supply.get("level")) is not int
        or supply["level"] > level
        or not isinstance(audit, Mapping) or audit.get("observed") is not True
        or audit.get("level") != level or audit.get("boot_id") != boot
        or not isinstance(stats, Mapping) or type(stats.get("fame")) is not int or stats["fame"] < 0
        or type(state.get("hp")) is not int or type(state.get("max_hp")) is not int
        or state["max_hp"] <= 0 or state["hp"] < state["max_hp"] * 0.95
    ):
        return None
    result = state.get("campaign_training_travel_result")
    setup_repair = bool(
        isinstance(prior, Mapping) and prior.get("level") == level and prior.get("boot_id") == boot
        and isinstance(result, Mapping)
        and (
            prior.get("setup_revision", 1) == 1
            or (
                prior.get("setup_revision") == result.get("setup_revision") == 2
                and prior.get("unique_keyword") is None
                and result.get("unique_keyword") is None
                and carried_potion_keyword(
                    world.objects, supply.get("object_vnum"), carried_descriptions,
                ) is not None
            )
            or (
                prior.get("setup_revision") == result.get("setup_revision") == 3
                and result.get("accepted_lessons") == 0
                and isinstance(result.get("inventory_footer_repair"), Mapping)
                and type(result["inventory_footer_repair"].get("run_id")) is int
                and carried_potion_keyword(
                    world.objects, supply.get("object_vnum"), carried_descriptions,
                ) is not None
            )
        )
        and result.get("failure") == "no unique freshly observed carried potion selector"
        and result.get("selector") is None and result.get("route_index") == 0
        and all(result.get(k) == prior.get(k) == supply.get(k)
                for k in ("object_vnum", "teacher_vnum", "teacher_room_vnum"))
    )
    if (not ignore_attempt and isinstance(prior, Mapping)
            and prior.get("level") == level and prior.get("boot_id") == boot and not setup_repair):
        return None
    purchases = state.get("campaign_source_purchases")
    purchase_proved = isinstance(purchases, list) and any(
        isinstance(p, Mapping) and p.get("stage") == "complete"
        and all(p.get(k) == supply.get(k) for k in ("object_vnum", "shopkeeper_vnum", "room_vnum"))
        for p in purchases
    )
    # Revision 1 admitted the proven purchase but overwrote its evidence with
    # an empty shop result. Its exact untouched-item setup failure gets one
    # repair, not a renewed journey after consuming or moving.
    admitted_purchase = bool(
        isinstance(prior, Mapping) and prior.get("purchase_proved") is True
        and all(prior.get(k) == supply.get(k)
                for k in ("object_vnum", "teacher_vnum", "teacher_room_vnum"))
    )
    if not (purchase_proved or setup_repair or admitted_purchase):
        return None
    item = world.objects.get(supply.get("object_vnum"))
    if (
        item is None or item.item_type != ITEM_POTION or potion_spell_names(item) != ("invis",)
        or not is_releasable_funding_item(item)
        or sum(normalize_item_name(s) == normalize_item_name(item.short_description)
               for s in carried_descriptions) != 1
        or sum(normalize_item_name(o.short_description) == normalize_item_name(item.short_description)
               for o in world.objects.values()) != 1
    ):
        return None
    teacher = source_class_teacher_route_for_level(world, character_class, 20)
    if (teacher is None or teacher.wanders or not teacher.steps or len(teacher.steps) > 90
            or teacher.mobile_vnum != supply.get("teacher_vnum")
            or teacher.room_vnum != supply.get("teacher_room_vnum")
            or teacher.steps[0][0] != "3001"):
        return None
    rooms = (3054, 3001, *(int(s[2]) for s in teacher.steps))
    if (
        any(v not in world.rooms or world.rooms[v].random_exits
            or world.rooms[v].room_flags & ((1 << 9) | (1 << 11) | (1 << 13)) for v in rooms)
        or source_route_requires_flight(world, rooms)
        or source_route_hazard_rejections(
            world, rooms, character_level=level, combat_at_destination=False,
            invisible=True, audit_invisible_equipment=True,
        )
    ):
        return None
    remaining = tuple(source_route_movement_cost(world, rooms[i:]) + 20 for i in range(len(rooms)))
    if type(state.get("move")) is not int or state["move"] < remaining[0]:
        return None
    known, learnable = audit.get("known_skill_levels"), audit.get("learnable_skill_levels")
    if not isinstance(known, Mapping) or not isinstance(learnable, Mapping):
        return None
    skills, gains = {**learnable, **known}, []
    teachings = dict(world.mobiles[teacher.mobile_vnum].teachings)
    if not 0 < teachings.get("teacher base", 0) <= level:
        return None
    for priority in training_priorities_for(character_class, subclass=state.get("subclass")):
        current, balance = skills.get(priority.skill), audit.get(f"{priority.practice_type}_practices")
        if (not priority.automated or type(current) is not int or current < 0
                or type(balance) is not int or balance <= 0 or current >= priority.target_percent
                or level < (priority.minimum_level or 0)
                or (current == 0 and learnable.get(priority.skill) != 0)):
            continue
        expected = practice_gain(current, teacher_capacity(teachings, priority.skill, world.skill_groups),
                                 priority.practice_type, stats)
        if expected is not None and expected > current:
            gains.append((priority.skill, current, expected))
    if not gains:
        return None
    # get_obj_carry uses is_name's prefix matching. Saved objects have target_id
    # zero in fread_obj, so only a globally unique source prefix can replace it.
    unique_keyword = next((word for word in item.keywords.casefold().split()
                           if re.fullmatch(r"[a-z][a-z0-9-]*", word)
                           and all(not any(k.startswith(word) for k in other.keywords.casefold().split())
                                   for other in world.objects.values() if other.vnum != item.vnum)), None)
    return TrainingTravelPlan(teacher, item.vnum, item.short_description, rooms, tuple(gains),
                              remaining, level, str(boot), setup_repair, unique_keyword)


@dataclass
class TrainingTravelSession:
    plan: TrainingTravelPlan
    stage: str = "new"
    response: str = ""
    deadline: float | None = None
    failure: str | None = None
    selector: str | None = None
    affect_revision: int = 0
    inventory_revision: int = 0
    route_index: int = 0
    accepted_lessons: int = 0

    def observe(self, text: str) -> None:
        if self.stage in {"configure", "inventory", "quaff", "verify"}:
            self.response = (self.response + text)[-8000:]

    def reject(self, reason: str) -> None:
        self.failure, self.stage, self.deadline = reason, "failed", None

    def expire(self, now: float) -> bool:
        if self.deadline is not None and now >= self.deadline:
            self.reject("potion confirmation did not complete within five seconds")
            return True
        return False

    def next_command(
        self, *, inventory: Sequence[tuple[str, str | None]], inventory_revision: int,
        affect_revision: int, duration: int | None, now: float,
        source_objects: Mapping[int, ObjectSource] | None = None,
    ) -> str | None:
        self.expire(now)
        if self.stage in {"ready", "failed"}:
            return None
        entries = [(name, selector) for name, selector in inventory
                   if normalize_item_name(name) == normalize_item_name(self.plan.description)]
        command = None
        if self.stage == "new":
            self.stage, command = "configure", "config +targetmode"
        elif (self.stage == "configure" and "Targetmode is now ON." in self.response
              and _DD4_PROMPT.search(self.response.partition("Targetmode is now ON.")[2])):
            self.inventory_revision = inventory_revision
            self.stage, command = "inventory", "inventory"
        elif (self.stage == "inventory" and "Your backpack contains:" in self.response
              and _DD4_PROMPT.search(self.response.partition("Your backpack contains:")[2])):
            sightings = [m for m in re.finditer(r"^\s*\[(#\d+)\]\s*(.+?)\s*$", self.response, re.MULTILINE)
                         if normalize_item_name(m[2]) == normalize_item_name(self.plan.description)]
            unnamed = sum(normalize_item_name(line) == normalize_item_name(self.plan.description)
                          for line in self.response.partition("Your backpack contains:")[2].splitlines())
            numeric = bool(len(entries) == 1 and len(sightings) == 1
                           and entries[0][1] == sightings[0][1])
            source_keyword = self.plan.unique_keyword
            if (
                source_keyword is None and source_objects is not None
                and _listed_inventory(self.response)
                == Counter(normalize_item_name(name) for name, _ in inventory)
            ):
                source_keyword = carried_potion_keyword(
                    source_objects, self.plan.object_vnum,
                    [name for name, _ in inventory],
                )
            keyword = bool(len(entries) == 1 and entries[0][1] is None and not sightings
                           and unnamed == 1 and source_keyword)
            if not (numeric or keyword):
                self.reject("no unique freshly observed carried potion selector")
                return None
            if duration is not None:
                self.reject("already invisible; do not waste the carried potion")
                return None
            self.selector = entries[0][1] if numeric else source_keyword
            self.affect_revision = affect_revision
            self.inventory_revision = inventory_revision
            self.stage, command = "quaff", f"quaff {self.selector}"
        elif (self.stage == "quaff" and "You quaff " in self.response
              and _DD4_PROMPT.search(self.response.partition("You quaff ")[2])):
            self.stage, command = "verify", "inventory"
        elif (self.stage == "verify" and "Your backpack contains:" in self.response
              and _DD4_PROMPT.search(self.response.partition("Your backpack contains:")[2])):
            if (inventory_revision <= self.inventory_revision or entries
                    or affect_revision <= self.affect_revision or duration is None or duration < 4):
                self.reject("consumption and fresh lasting invisibility were not both confirmed")
            else:
                self.stage, self.deadline = "ready", None
            return None
        if command is not None:
            self.response, self.deadline = "", now + 5.0
        return command

    def check_route(self, *, room: str, move: int | None, duration: int | None) -> bool:
        if self.stage != "ready":
            return False
        if self.route_index + 1 < len(self.plan.rooms) and room == str(self.plan.rooms[self.route_index + 1]):
            self.route_index += 1
        if room != str(self.plan.rooms[self.route_index]):
            self.reject("live position left the registered teacher route")
        elif duration is None or duration < 2:
            self.reject("teacher-route invisibility expired or is almost finished")
        elif type(move) is not int or move < self.plan.movement_remaining[self.route_index]:
            self.reject("remaining movement no longer covers the teacher route and reserve")
        return self.failure is None

    def evidence(self) -> dict[str, Any]:
        return {**self.plan.evidence(), "stage": self.stage, "selector": self.selector,
                "route_index": self.route_index, "accepted_lessons": self.accepted_lessons,
                "failure": self.failure}
