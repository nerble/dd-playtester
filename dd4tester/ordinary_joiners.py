"""Source and live evidence for one ordinary opponent joining an open fight."""

from dataclasses import dataclass, field
from collections.abc import Callable
import re
from typing import Any

from .hunt_candidates import (
    ITEM_ARMOR, ITEM_CONTAINER, ITEM_FOOD, ITEM_MONEY, ITEM_TREASURE,
    ITEM_WEAPON, WorldSource, _mobile_level_range,
)
from .target_inspection import TargetInspectionController, look_health_match, normalized_description
from .combat_losses import source_stop_identity, source_stop_policy_id
from .observations import _DD4_PROMPT


def ordinary_joiner_source(world: WorldSource, vnum: int, room_vnum: int) -> bool:
    """Audit every reset, including carried magic items, without target HP."""
    mobile = world.mobiles.get(vnum)
    room = world.rooms.get(room_vnum)
    if (mobile is None or room is None or mobile.aggressive or mobile.programs
            or mobile.attack_programs or mobile.fear_aura or mobile.confused
            or mobile.non_corporeal or mobile.costs_fame
            or world.mobile_specials.get(vnum) or vnum in world.shopkeepers
            or not mobile.damage_modifier_known or not mobile.crit_modifier_known
            or not mobile.haste_modifier_known
            or any(value is None for value in (
                mobile.damage_modifier, mobile.crit_modifier, mobile.haste_modifier,
            ))):
        return False
    resets = [reset for reset in world.mob_resets if reset.mobile_vnum == vnum]
    if (not resets or any(type(reset.maximum_count) is not int
                          or not 1 <= reset.maximum_count <= 4 for reset in resets)
            or not any(reset.room_vnum == room_vnum for reset in resets)
            and not (mobile.wanders and mobile.area_file == room.area_file)):
        return False
    # NPCs can use magical objects from inventory (fight.c:use_magical_item).
    # Deliberately whitelist ordinary objects rather than infer harmlessness
    # from the absence of a mobile special. Unknown item types stay excluded.
    # Remaining values: light, trash, drink container, key (merc.h).
    ordinary_types = {ITEM_ARMOR, ITEM_WEAPON, ITEM_TREASURE, ITEM_CONTAINER,
                      ITEM_FOOD, ITEM_MONEY, 1, 13, 17, 18}
    for reset in resets:
        slots = [slot for slot, _ in reset.equipment]
        if len(slots) != len(set(slots)) or any(type(slot) is not int or not 0 <= slot <= 21 for slot in slots):
            return False
        for object_vnum in set(reset.object_vnums) | {v for _, v in reset.equipment}:
            item = world.objects.get(object_vnum)
            if item is None or item.item_type not in ordinary_types:
                return False
            if item.extra_flags & (1 << 2):  # ITEM_EGO: separate item-power review
                return False
            if item.item_type == ITEM_WEAPON:
                if item.extra_flags & (1 << 14):  # ITEM_POISONED
                    return False
    return True


def ordinary_joiner_withdrawal(
    world: WorldSource, encounter, *, enemies: list, primary_killed: bool,
    parent_policy_id: str, level: int, room: str, reason: str,
    normalize: Callable[[str], str] = normalized_description,
) -> dict | None:
    """Attribute a real penalty to the still-fighting actor, preserving its parent."""
    if not encounter.ordinary_joiner or len(enemies) > 3 or not enemies:
        return None
    try:
        live_room = int(room)
    except (TypeError, ValueError):
        return None
    vnum = encounter.bystander_vnum if primary_killed else encounter.target_vnum
    matches = [enemy for enemy in enemies if str(enemy.get("isnpc")) == str(vnum)]
    if not matches or primary_killed and (len(matches) != 1 or len(enemies) != 1):
        return None
    mobile = world.mobiles.get(vnum)
    enemy = matches[0]
    if (mobile is None or normalize(str(enemy.get("name") or "")) != normalize(mobile.short_description)
            or normalize(str(enemy.get("long_desc") or "")) != normalize(mobile.room_description)
            or normalize(str(enemy.get("look_desc") or "")) != normalize(mobile.description)):
        return None
    if primary_killed:
        reset = next((r for r in world.mob_resets if r.mobile_vnum == vnum), None)
        if reset is None:
            return None
        reset_room = reset.room_vnum
        policy_id = source_stop_policy_id(mobile.area_file, vnum, reset_room, level)
    else:
        identity = source_stop_identity(parent_policy_id)
        if identity is None or identity[0] != vnum or identity[2] != level:
            return None
        policy_id, reset_room = parent_policy_id, identity[1]
    return {
        "policy_id": policy_id, "mobile_vnum": vnum, "room_vnum": reset_room,
        "live_room_vnum": live_room, "level": level, "target": enemy["name"], "reason": reason,
        "evidence_source": "ordinary_joiner_withdrawal", "parent_policy_id": parent_policy_id,
        "encounter_mobile_vnums": [encounter.target_vnum, encounter.bystander_vnum],
    }


@dataclass
class OrdinaryJoinerAssessment:
    """One finite room/look/consider exchange, owned by the combat session."""

    plan: dict[str, Any] | None = None
    inspection: TargetInspectionController = field(default_factory=TargetInspectionController)
    attempted: set[tuple] = field(default_factory=set)
    records: list[dict] = field(default_factory=list)
    buffer: str = ""

    @property
    def owns_consider(self) -> bool:
        return bool(self.plan and self.plan.get("consider_started"))

    def begin(self, *, scope: tuple, attacker: str, mobile_vnum: int,
              source_level: int, room_sequence: int, now: float) -> bool:
        if scope in self.attempted or len(self.attempted) >= 8:
            return False
        self.clear()
        self.attempted.add(scope)
        self.plan = {
            "scope": scope, "attacker": attacker, "mobile_vnum": mobile_vnum,
            "source_level": source_level, "stage": "listing", "deadline": now + 5,
            "room_sequence": room_sequence,
        }
        self.buffer = ""
        return True

    def inspect(self, *, selector: str, descriptions: dict[int, str],
                room: str, level: int, boot: str, visit: int, now: float) -> bool:
        plan = self.plan
        if plan is None or plan["stage"] != "listing":
            return False
        if not self.inspection.begin(
            room=room, selector=selector, expected=plan["mobile_vnum"],
            descriptions=descriptions, name=plan["attacker"], level=level,
            boot=boot, visit=visit, now=now,
        ):
            self.fail("joiner look could not bind one source identity")
            return False
        plan.update(stage="identity", selector=selector, deadline=now + 5)
        self.buffer = ""
        return True

    def observe(self, text: str, *, now: float) -> None:
        plan = self.plan
        if plan is None or plan["stage"] in {"admitted", "failed"}:
            return
        if now >= plan["deadline"]:
            self.fail("joiner reply exceeded five seconds")
            return
        if plan["stage"] == "identity":
            self.buffer += text
            if len(self.buffer) > 8192:
                self.fail("joiner look exceeded its reply bound")
                return
            self.inspection.observe(text, now=now)
            health = look_health_match(self.buffer, plan["attacker"])
            plan["identity_complete"] = bool(health and _DD4_PROMPT.search(self.buffer, health.end()))
        elif plan["stage"] == "consider":
            self.buffer += text
            if len(self.buffer) > 2048:
                self.fail("joiner consider exceeded its reply bound")
                return
            name = re.escape(plan["attacker"])
            patterns = (
                (rf"{name} looks like an easy kill\.", -4, -2),
                (r"The perfect match!", -1, 1),
                (rf"{name} is no match for you\.", -9, -5),
                (rf"You can kill {name} naked and weaponless\.", None, -10),
            )
            for pattern, minimum_offset, offset in patterns:
                match = re.search(r"(?im)^\s*" + pattern + r"[ \t]*[\r\n]", self.buffer)
                if match:
                    low, high = _mobile_level_range(plan["source_level"])
                    level = min(high, plan["scope"][2] + offset)
                    minimum_level = (1 if minimum_offset is None else plan["scope"][2] + minimum_offset)
                    if level < max(low, minimum_level):
                        self.fail("joiner consider conflicts with its source level")
                    elif _DD4_PROMPT.search(self.buffer, match.end()):
                        plan.update(stage="admitted", level_ceiling=level, observed_at=now)
                        self.records.append({k: v for k, v in plan.items() if k != "deadline"})
                    return
            if any(value in self.buffer.casefold() for value in (
                "they're not here.", "cannot be physically harmed", "feel lucky",
                "laughs at you", "death will thank", "crush you", "puny insect",
            )):
                self.fail("joiner failed its live relative-level consider")

    def next_command(self, *, now: float) -> str | None:
        plan = self.plan
        if plan is None or plan["stage"] in {"admitted", "failed"}:
            return None
        if now >= plan["deadline"]:
            self.fail("joiner reply exceeded five seconds")
        elif plan["stage"] == "identity" and self.inspection.pending is None:
            receipt = self.inspection.receipt
            if not receipt or receipt["status"] != "verified":
                self.fail("joiner look did not confirm the expected prototype")
            elif plan.get("identity_complete"):
                plan.update(stage="consider", deadline=now + 5, consider_started=True)
                self.buffer = ""
                return f"consider {plan['selector']}"
        return None

    def fail(self, reason: str) -> None:
        if self.plan is not None and self.plan["stage"] != "failed":
            self.plan.update(stage="failed", reason=reason)
            self.records.append({k: v for k, v in self.plan.items() if k != "deadline"})

    def clear(self) -> None:
        self.plan = None
        self.buffer = ""
        self.inspection.pending = None
        self.inspection.buffer = ""
        self.inspection.invalidate()
