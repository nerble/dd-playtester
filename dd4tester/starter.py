from __future__ import annotations

import asyncio
import json
import os
import re
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from .character import CharacterSpec, load_character_spec
from .connection import ReadResult, TelnetConnection
from .credentials import CredentialStoreError, load_character_password
from .fastwalks import Fastwalk, route_named
from .observations import GameEvent, ObservationParser
from .runner import RunResult
from .shops import SafeShop, safe_shop_for_item, sale_keyword
from .state import CharacterState
from .storage import RunStorage
from .transcript import TranscriptRecorder


_ANSI_ESCAPE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
_ATTRIBUTE_ROLL = re.compile(
    r"Str:\s*(?P<str>\d+)\s+Int:\s*(?P<int>\d+)\s+"
    r"Wis:\s*(?P<wis>\d+)\s+Dex:\s*(?P<dex>\d+)\s+Con:\s*(?P<con>\d+)",
    re.IGNORECASE,
)
_DIRECTION = re.compile(
    r"\b(?:head|go|move|continue|points?|motions?|through|towards?)\b"
    r".{0,80}?\b(?P<direction>north|south|east|west|up|down)\b",
    re.IGNORECASE | re.DOTALL,
)
_AFFORDABLE_QUANTITY = re.compile(r"can only afford\s+(?P<quantity>\d+)", re.IGNORECASE)
_VALUE_OFFER = re.compile(
    r"tells you 'I'll give you (?P<coins>\d+) coins? for (?P<item>.+?)'\.",
    re.IGNORECASE,
)
_SALE_COMPLETED = re.compile(
    r"You sell (?P<item>.+?) for (?P<coins>\d+) coins?\.",
    re.IGNORECASE,
)
_BOOT_TIME = re.compile(
    r"DD was started at\s+(?P<boot>[^\r\n]+)",
    re.IGNORECASE,
)
_TOTAL_XP_GAIN = re.compile(
    r"You gained a total of (?P<xp>\d+) experience points?!",
    re.IGNORECASE,
)
_MOB_DEATH = re.compile(
    r"(?:^|\n)\s*(?P<target>[A-Za-z][A-Za-z '-]{0,60}?) is DEAD!!",
    re.IGNORECASE,
)
_MOB_LEAVES = re.compile(
    r"(?:^|\n)\s*(?P<target>[A-Za-z][A-Za-z '-]{0,60}?) leaves "
    r"(?P<direction>north|south|east|west|up|down)\.",
    re.IGNORECASE,
)
_DIRECTION_SHORTCUTS = {
    "n": "north",
    "s": "south",
    "e": "east",
    "w": "west",
    "u": "up",
    "d": "down",
}
_STARTER_SKILLS = {
    "mage": "magic missile",
    "cleric": "cure light",
    "thief": "backstab",
    "warrior": "kick",
    "psionic": "mind thrust",
    "shifter": "shapeshift",
    "brawler": "kick",
    "ranger": "kick",
    "smithy": "repair",
}
_TRAINING_CENTERS = {
    "3712": (("3713", "3714"), "3715"),
    "3715": (("3717", "3718"), "3716"),
    "3716": (("3719", "3720"), "3722"),
}
_TRAINING_SIDE_ROOMS = {
    "3713": "3712",
    "3714": "3712",
    "3717": "3715",
    "3718": "3715",
    "3719": "3716",
    "3720": "3716",
}
_ARENA_RESPAWN_WAIT_SECONDS = 90
_HEALTH_CHECK_WAIT_SECONDS = 30
_COMMAND_PROMPT_MIN_SECONDS = 0.05
_MOVEMENT_COMMANDS = {
    "north",
    "east",
    "south",
    "west",
    "up",
    "down",
    "recall",
    "enter portal",
}
_PURGATORY_DESTINATION_PATH = {
    "401": "410",
    "410": "411",
    "411": "423",
    "423": "422",
    "422": "426",
    "426": "427",
}


@dataclass(frozen=True)
class BotDecision:
    command: str
    reason: str
    secret: bool = False


class StarterPolicy:
    """Deterministic rules for creation and DD4's first training sequence."""

    def __init__(
        self,
        spec: CharacterSpec,
        password: str,
        *,
        objective_level: int = 2,
        resupply_only: bool = False,
        return_home: bool = False,
        city_restock: bool = False,
        guildmaster_research: bool = False,
        magic_shop_research: bool = False,
        magic_shop_buy_fly: bool = False,
        liquidate_loot: bool = False,
        loot_sale_counts: Mapping[tuple[str, str], int] | None = None,
        loot_sale_history: list[Mapping[str, Any]] | None = None,
        query_world_time: bool = False,
        fastwalk_route: Fastwalk | None = None,
        fastwalk_explore_direction: str | None = None,
        fastwalk_explore_depth: int = 1,
        fastwalk_attack_target: str | None = None,
        moria_research: bool = False,
        moria_depth: int = 0,
    ) -> None:
        if objective_level < 2:
            raise ValueError("objective_level must be at least 2")
        if moria_depth < 0:
            raise ValueError("moria_depth must not be negative")
        if not 1 <= fastwalk_explore_depth <= 6:
            raise ValueError("fastwalk_explore_depth must be between 1 and 6")
        self.spec = spec
        self.password = password
        self.objective_level = objective_level
        self.resupply_only = resupply_only
        self.return_home = return_home
        self.city_restock = city_restock
        self.guildmaster_research = guildmaster_research
        self.magic_shop_research = magic_shop_research
        self.magic_shop_buy_fly = magic_shop_buy_fly
        self.liquidate_loot = liquidate_loot
        self.loot_sale_counts = dict(loot_sale_counts or {})
        self.loot_sale_history = [dict(row) for row in loot_sale_history or []]
        self.query_world_time = query_world_time
        self.world_time_queried = False
        self.world_boot_id: str | None = None
        self.completed_kills: list[dict[str, Any]] = []
        self.fastwalk_route = fastwalk_route
        self.fastwalk_explore_direction = fastwalk_explore_direction
        self.fastwalk_explore_depth = fastwalk_explore_depth
        self.fastwalk_attack_target = fastwalk_attack_target
        self.moria_research = moria_research
        self.moria_depth = moria_depth
        self.stage = "login"
        self.done = False
        self.failure: str | None = None
        self.awaiting_reconnect = False
        self.in_world = False
        self.prompt_ready = False
        self.last_command_at: float | None = None
        self.pending_travel_origin: str | None = None
        self.text = ""
        self.roll_count = 0
        self.course_started = False
        self.course_complete = False
        self.visited_course_rooms: set[str] = set()
        self.room_query_counts: dict[str, int] = {}
        self.current_room: str | None = None
        self.previous_room: str | None = None
        self.advice_direction: str | None = None
        self.pending_move: str | None = None
        self.loremaster_step = 0
        self.practiced = False
        self.arena_queried = False
        self.arena_visited_rooms: set[str] = set()
        self.arena_respawn_due: float | None = None
        self.arena_pending_loot = False
        self.arena_loot_step = 0
        self.combat_active = False
        self.needs_stand = False
        self.waiting_for_heal = False
        self.healer_menu_checked = False
        self.health_check_due: float | None = None
        self.resume_recovery_after_resupply = False
        self.waiting_for_move = False
        self.room_targets: dict[str, list[str]] = {}
        self.defeated_targets: dict[str, set[str]] = {}
        self.missing_targets: dict[str, set[str]] = {}
        self.active_target: str | None = None
        self.pending_loot_rooms: set[str] = set()
        self.cleared_training_rooms: set[str] = set()
        self.post_kill_steps: dict[str, int] = {}
        self.magic_missile_cast = False
        self.store_step = 0
        self.provisioned = False
        self.saved = False
        self.needs_food = resupply_only
        self.needs_drink = resupply_only
        self.food_attempted = False
        self.drink_attempted = False
        self.food_ordered = False
        self.skin_ordered = False
        self.last_consumption: str | None = None
        self.insufficient_funds = False
        self.city_restock_step = 0
        self.affordable_pies: int | None = None
        self.affordable_pies_ordered = False
        self.guildmaster_step = 0
        self.magic_shop_step = 0
        self.magic_shop_purchase_failed = False
        self.sale_plan: list[tuple[str, SafeShop]] = []
        self.sale_index = 0
        self.sale_route_index = 0
        self.sale_phase = "plan"
        self.sale_offer_coins: int | None = None
        self.completed_sales: list[dict[str, Any]] = []
        self.sale_container_step = 0
        self.fastwalk_recall_started = False
        self.fastwalk_arrival_observed = False
        self.fastwalk_returning = False
        self.fastwalk_outbound_index = 0
        self.fastwalk_return_index = 0
        self.fastwalk_explore_step = 0
        self.fastwalk_explore_distance = 0
        self.fastwalk_explore_look_pending = False
        self.fastwalk_withdrawing = False
        self.fastwalk_return_steps_remaining = 0
        self.fastwalk_attack_started = False
        self.fastwalk_pursuit_direction: str | None = None
        self.fastwalk_pursuit_steps = 0
        self.fastwalk_target_absent = False
        self.fastwalk_loot_step = 0
        self.fastwalk_recall_after_loot = False
        self.fastwalk_last_kill_target: str | None = None
        self.pending_fastwalk_outbound_move = False
        self.return_home_recall_started = False
        self.return_home_gear_checked = False
        self.return_home_equipment_plan: list[str] | None = None
        self.return_home_equipment_index = 0
        self.purgatory_recovery_active = False
        self.purgatory_judgement_step = 0
        self.purgatory_portal_entered = False
        self.purgatory_sleep_started = False
        self.purgatory_recovery_complete = False
        self.moria_seen = False
        self.moria_returning = False
        self.moria_observed_rooms: set[str] = set()

    def observe_text(self, text: str) -> None:
        cleaned = _ANSI_ESCAPE.sub("", text).replace("\r", "")
        recent = cleaned.casefold()
        self.text = (self.text + cleaned)[-24_000:]
        folded = self.text.casefold()
        if "you launch a volley of" in recent and "magic missile" in recent:
            self.magic_missile_cast = False
        if any(
            warning in folded
            for warning in ("lack of food", "dying of hunger", "you are hungry")
        ):
            self.needs_food = True
        if any(
            warning in folded
            for warning in ("throat is parched", "dying of thirst", "you are thirsty")
        ):
            self.needs_drink = True
        if "you eat" in folded or "you are full" in folded:
            self.needs_food = False
        if "you drink" in folded or "do not feel thirsty" in folded:
            self.needs_drink = False
        if "you can't afford" in folded or "you do not have enough" in folded:
            self.insufficient_funds = True
            if self.magic_shop_research and self.magic_shop_buy_fly:
                self.magic_shop_purchase_failed = True
        affordable = _AFFORDABLE_QUANTITY.search(cleaned)
        if affordable is not None:
            self.affordable_pies = int(affordable.group("quantity"))
        offer = _VALUE_OFFER.search(cleaned)
        if offer is not None:
            self.sale_offer_coins = int(offer.group("coins"))
        completed_sale = _SALE_COMPLETED.search(cleaned)
        if completed_sale is not None and self.sale_index < len(self.sale_plan):
            keyword, shop = self.sale_plan[self.sale_index]
            self.completed_sales.append(
                {
                    "item_keyword": keyword,
                    "item_description": completed_sale.group("item"),
                    "shop_name": shop.name,
                    "shop_room_vnum": shop.room_vnum,
                    "offered_coins": self.sale_offer_coins,
                    "sold_coins": int(completed_sale.group("coins")),
                }
            )
            self.sale_offer_coins = None
        boot_time = _BOOT_TIME.search(cleaned)
        if boot_time is not None:
            self.world_boot_id = " ".join(boot_time.group("boot").split())
        if "you don't have that item" in folded or "is empty" in folded:
            if self.last_consumption == "food":
                self.needs_food = True
                self.food_ordered = False
            if self.last_consumption == "drink":
                self.needs_drink = True
                self.skin_ordered = False
        targets = _training_targets(cleaned)
        if self.current_room and targets and not self.combat_active:
            known = self.room_targets.setdefault(self.current_room, [])
            known.extend(target for target in targets if target not in known)

        direction = _DIRECTION.search(self.text)
        if direction is not None and "imp" in folded:
            self.advice_direction = direction.group("direction").casefold()
        if "hole in the north wall" in folded:
            self.advice_direction = "north"
        if "is dead" in recent or "you receive" in recent and "experience" in recent:
            was_in_combat = self.combat_active
            defeated_target = self.active_target or _defeated_mobile(cleaned)
            self.combat_active = False
            if self.current_room and (self.active_target or was_in_combat):
                if self.fastwalk_route is not None:
                    self.fastwalk_last_kill_target = self.active_target
                if defeated_target:
                    xp_gain = _TOTAL_XP_GAIN.search(cleaned)
                    self.completed_kills.append(
                        {
                            "mob_name": defeated_target,
                            "xp_gained": (
                                int(xp_gain.group("xp"))
                                if xp_gain is not None
                                else None
                            ),
                        }
                    )
                if self.active_target:
                    self.defeated_targets.setdefault(self.current_room, set()).add(
                        self.active_target
                    )
                if self.current_room != "3722":
                    if _is_arena_vnum(self.current_room):
                        self.arena_pending_loot = True
                        self.arena_loot_step = 0
                    else:
                        self.pending_loot_rooms.add(self.current_room)
                else:
                    self.cleared_training_rooms.add(self.current_room)
                self.post_kill_steps.setdefault(self.current_room, 0)
            self.active_target = None
            self.magic_missile_cast = False
        fleeing_mobile = _MOB_LEAVES.search(cleaned)
        if (
            fleeing_mobile is not None
            and self.fastwalk_attack_target is not None
            and self.active_target is not None
            and _targets_match(
                fleeing_mobile.group("target").casefold(),
                self.fastwalk_attack_target.casefold(),
            )
        ):
            self.combat_active = False
            self.active_target = None
            self.magic_missile_cast = False
            self.fastwalk_pursuit_direction = fleeing_mobile.group(
                "direction"
            ).casefold()
        if (
            "you attack " in recent
            or " attacks you" in recent
            or "fighting you" in recent
        ):
            self.combat_active = True
        if "aren't fighting anyone" in recent:
            self.combat_active = False
            self.active_target = None
            self.magic_missile_cast = False
        if "aren't here" in recent or "do not see that here" in recent:
            self.combat_active = False
            if self.current_room and self.active_target:
                if self.active_target == self.fastwalk_attack_target:
                    self.fastwalk_target_absent = True
                self.missing_targets.setdefault(self.current_room, set()).add(
                    self.active_target
                )
                targets = self.room_targets.get(self.current_room, [])
                self.room_targets[self.current_room] = [
                    target for target in targets if target != self.active_target
                ]
            self.active_target = None
            self.magic_missile_cast = False
        if "too relaxed" in folded or "you must be standing" in folded:
            self.needs_stand = True
        if "you are still fighting" in recent:
            self.combat_active = True
            if self.pending_fastwalk_outbound_move:
                self.fastwalk_outbound_index = max(
                    0,
                    self.fastwalk_outbound_index - 1,
                )
                self.pending_fastwalk_outbound_move = False
            self.pending_travel_origin = None
        if "alas, you cannot go that way" in folded:
            if (
                self.fastwalk_explore_look_pending
                and self.fastwalk_explore_distance > 0
            ):
                self.fastwalk_explore_distance -= 1
                self.fastwalk_explore_look_pending = False
                self.fastwalk_target_absent = (
                    self.fastwalk_attack_target is not None
                )
                self.fastwalk_withdrawing = True
                self.fastwalk_return_steps_remaining = (
                    self.fastwalk_explore_distance
                )
            self.pending_travel_origin = None

    def observe_events(
        self,
        events: list[GameEvent],
        state: CharacterState,
    ) -> None:
        for event in events:
            if event.type == "prompt_seen":
                if (
                    (
                        self.pending_travel_origin is None
                        or _room_key(state) != self.pending_travel_origin
                    )
                    and (
                        self.last_command_at is None
                        or time.monotonic() - self.last_command_at
                        >= _COMMAND_PROMPT_MIN_SECONDS
                    )
                ):
                    self.prompt_ready = True
            if event.type in {"room_entered", "room_updated"}:
                room = _room_key(state)
                if room and room != self.current_room:
                    self.previous_room = self.current_room
                    self.current_room = room
                    self.pending_travel_origin = None
                    self.pending_fastwalk_outbound_move = False
                    self.advice_direction = None
                    self.pending_move = None
                targets = _training_targets(self.text)
                if room and targets:
                    known = self.room_targets.setdefault(room, [])
                    known.extend(target for target in targets if target not in known)
                if state.room_vnum and state.room_vnum.startswith("37"):
                    if _is_training_vnum(state.room_vnum):
                        self.course_started = True
                    if self.course_started and state.room_vnum != "3725":
                        self.visited_course_rooms.add(state.room_vnum)
                if (
                    state.room_vnum == "3725"
                    and self.course_started
                    and len(self.visited_course_rooms) >= 2
                ):
                    self.course_complete = True
                if state.room_vnum == "3724":
                    self.course_started = True
                    self.course_complete = True
            if event.type == "combat_started":
                self.combat_active = True
                target = event.data.get("target", event.data.get("name"))
                if isinstance(target, str) and target.strip():
                    self.active_target = target.strip()
            if event.type == "character_died":
                self.failure = "character died during starter training"
        if self.waiting_for_move and _move_ratio(state) >= 0.5:
            self.prompt_ready = True
        if self.waiting_for_heal and _health_ratio(state) >= 0.5:
            self.prompt_ready = True
        if (
            self.arena_respawn_due is not None
            and time.monotonic() >= self.arena_respawn_due
            and state.room_vnum == "3737"
        ):
            self.prompt_ready = True

    def next_decision(self, state: CharacterState) -> BotDecision | None:
        if self.done or self.failure:
            return None

        login = self._login_decision()
        if login is not None:
            return login

        if not self.in_world and self.prompt_ready and state.room_name:
            self.in_world = True
            self.stage = "tutorial"

        if not self.in_world or not self.prompt_ready:
            return None
        return self._tutorial_decision(state)

    def after_command(self, decision: BotDecision) -> None:
        self.prompt_ready = False
        self.last_command_at = time.monotonic() if self.in_world else None
        if decision.command in _MOVEMENT_COMMANDS and self.current_room:
            self.pending_travel_origin = self.current_room
        if (
            decision.command in _MOVEMENT_COMMANDS
            and decision.reason.startswith("follow official fastwalk")
        ):
            self.pending_fastwalk_outbound_move = True
        self.text = ""
        if decision.command == "eat pie":
            self.food_attempted = True
            self.last_consumption = "food"
            self.needs_food = False
            self.resume_recovery_after_resupply = self.waiting_for_heal
        elif decision.command == "drink skin":
            self.drink_attempted = True
            self.last_consumption = "drink"
            self.needs_drink = False
            self.resume_recovery_after_resupply = self.waiting_for_heal
        elif decision.command == "buy 6 pie":
            self.food_ordered = True
        elif decision.command == "buy skin":
            self.skin_ordered = True
        elif (
            decision.command == "look"
            and self.fastwalk_route is not None
            and self.fastwalk_arrival_observed
            and self.current_room
        ):
            # A mobile can wander between visits; make this probe depend on this look.
            self.room_targets[self.current_room] = []
        if decision.command == "sleep" and self.waiting_for_heal:
            self.health_check_due = time.monotonic() + _HEALTH_CHECK_WAIT_SECONDS
        if decision.command == "quit":
            self.done = True

    def on_connection_closed(self) -> None:
        if self.done:
            return
        self.prompt_ready = False
        self.text = ""
        if self.awaiting_reconnect:
            self.stage = "login"

    def _login_decision(self) -> BotDecision | None:
        folded = self.text.casefold()

        if "enter thy name:" in folded:
            self.stage = "login_name"
            return BotDecision(self.spec.name, "submit configured character name")
        if "did i get that right" in folded:
            self.stage = "create_confirm_name"
            return BotDecision("y", "confirm new character name")
        if "please retype the password:" in folded:
            self.stage = "create_retype_password"
            return BotDecision(self.password, "confirm new character password", True)
        if "give me a password for" in folded or re.search(
            r"(?:^|\n)password:\s*$",
            self.text,
            re.IGNORECASE,
        ):
            self.stage = "login_password"
            return BotDecision(self.password, "submit character password", True)
        if "do you want to enable colour?" in folded:
            self.stage = "create_colour"
            return BotDecision(
                "y" if self.spec.colour else "n",
                "apply configured colour preference",
            )
        if "to create your character" in folded and "press" in folded:
            self.stage = "create_intro"
            return BotDecision("", "continue to race selection")
        if "please choose a race for your character" in folded:
            self.stage = "create_race"
            return BotDecision(
                self.spec.race_choice,
                f"select configured race {self.spec.race}",
            )
        if "are you sure you want to choose this race?" in folded:
            self.stage = "create_confirm_race"
            return BotDecision("y", "confirm configured race")
        if "male, female or neuter?" in folded:
            self.stage = "create_gender"
            return BotDecision(
                self.spec.gender_choice,
                f"select configured gender {self.spec.gender}",
            )
        if "are you sure you want this gender?" in folded:
            self.stage = "create_confirm_gender"
            return BotDecision("y", "confirm configured gender")
        if "please choose a class for your character:" in folded:
            self.stage = "create_class"
            return BotDecision(
                self.spec.character_class,
                f"select base class for target {self.spec.subclass or self.spec.character_class}",
            )
        if "are you sure you want this class?" in folded:
            self.stage = "create_confirm_class"
            return BotDecision("y", "confirm configured class")
        if "begin rolling your character's attributes" in folded:
            self.stage = "create_attributes"
            return BotDecision("", "roll initial attributes")

        roll = _ATTRIBUTE_ROLL.search(self.text)
        if roll is not None and "accept?" in folded:
            self.roll_count += 1
            primary = int(roll.group(self.spec.primary_stat))
            accept = (
                primary >= self.spec.minimum_primary_stat
                or self.roll_count >= self.spec.max_attribute_rolls
            )
            self.stage = "create_accept_attributes"
            return BotDecision(
                "y" if accept else "n",
                (
                    f"accept roll {self.roll_count}; {self.spec.primary_stat}={primary}"
                    if accept
                    else f"reroll; {self.spec.primary_stat}={primary} below "
                    f"{self.spec.minimum_primary_stat}"
                ),
            )
        if "character generation complete" in folded:
            self.stage = "create_complete"
            self.awaiting_reconnect = True
            return BotDecision(
                "",
                "finish character generation before reconnecting",
            )
        if "to enter the dragons domain press <return>" in folded:
            self.stage = "enter_world"
            return BotDecision("", "enter the game after the message of the day")
        if "welcome to the dragons domain" in folded and self.prompt_ready:
            self.in_world = True
            self.stage = "tutorial"
        return None

    def _tutorial_decision(self, state: CharacterState) -> BotDecision | None:
        if state.dead:
            self.failure = "character died during starter training"
            return None

        if _has_inventory_item(state.inventory, "water skin"):
            self.provisioned = True
        if (
            state.level is not None
            and state.level >= 2
            and state.room_vnum == "3725"
        ):
            self.course_started = True
            self.course_complete = True

        if self.waiting_for_move:
            if _move_ratio(state) < 0.5:
                self.prompt_ready = False
                return None
            self.waiting_for_move = False
            self.needs_stand = True

        if self.needs_stand:
            self.needs_stand = False
            return BotDecision("stand", "stand before continuing tutorial actions")

        room_vnum = state.room_vnum
        room_name = (state.room_name or "").casefold()
        if room_vnum == "3737" and self.arena_respawn_due is not None:
            if time.monotonic() < self.arena_respawn_due:
                if _is_sleeping(state):
                    self.prompt_ready = False
                    return None
                return BotDecision(
                    "sleep",
                    "wait safely for arena opponents to respawn",
                )
            self.arena_respawn_due = None
        if room_vnum == "2" or room_name == "limbo":
            return BotDecision("look", "return from Limbo to the previous room")

        if self.waiting_for_heal:
            if self.needs_food or self.needs_drink:
                if _is_sleeping(state):
                    return BotDecision("stand", "wake to address hunger or thirst")
            elif _recovery_ready(state):
                self.waiting_for_heal = False
                self.health_check_due = None
                return BotDecision("stand", "resume after safe-room recovery")
            elif _is_sleeping(state):
                if (
                    self.health_check_due is not None
                    and time.monotonic() >= self.health_check_due
                ):
                    self.health_check_due = (
                        time.monotonic() + _HEALTH_CHECK_WAIT_SECONDS
                    )
                    return BotDecision("score", "check health while sleeping safely")
                self.prompt_ready = False
                return None
            else:
                if self.resume_recovery_after_resupply:
                    self.resume_recovery_after_resupply = False
                    return BotDecision("sleep", "resume safe-room recovery after resupply")
                self.prompt_ready = False
                return None

        if _is_sleeping(state):
            return BotDecision("stand", "wake before travel or arena actions")

        if self.combat_active:
            if self.needs_food or self.needs_drink or _health_ratio(state) < 0.25:
                if self.return_home:
                    return BotDecision(
                        "recall",
                        "use emergency recall when reconnecting to trapped combat",
                    )
                return BotDecision("flee", "leave combat before emergency resupply")
            spell = self._combat_spell_decision(state)
            if spell is not None:
                return spell
            self.prompt_ready = False
            return None

        if self.query_world_time and not self.world_time_queried:
            self.world_time_queried = True
            return BotDecision(
                "time",
                "identify the current reboot for dynamic world-state evidence",
            )

        if self.return_home and (
            self.purgatory_recovery_active
            or (state.area or "").casefold() == "purgatory"
            or state.room_vnum in _PURGATORY_DESTINATION_PATH
            or state.room_vnum == "427"
        ):
            self.purgatory_recovery_active = True
            purgatory = self._purgatory_recovery_decision(state)
            if purgatory is not None:
                return purgatory

        if self.city_restock:
            restock = self._city_restock_decision(state)
            if restock is not None:
                return restock
            if not self.saved:
                self.saved = True
                self.stage = "saving"
                return BotDecision("save", "persist city food-and-water restock")
            self.stage = "complete"
            return BotDecision("quit", "city food-and-water restock complete")

        resupply = self._resupply_decision(state)
        if resupply is not None:
            return resupply

        if self.resupply_only and self.food_attempted and self.drink_attempted:
            if not self.saved:
                self.saved = True
                self.stage = "saving"
                return BotDecision("save", "persist emergency resupply recovery")
            self.stage = "complete"
            return BotDecision("quit", "emergency resupply complete")

        recovery = self._recovery_decision(state)
        if recovery is not None:
            return recovery

        if self.return_home:
            home = self._return_home_decision(state)
            if home is not None:
                return home
            if not self.return_home_gear_checked:
                self.return_home_gear_checked = True
                return BotDecision(
                    "wear all",
                    "restore equipment after any interrupted or post-death run",
                )
            if self.return_home_equipment_plan is None:
                self.return_home_equipment_plan = [
                    sale_keyword(description)
                    for description in _inventory_descriptions(state.inventory)
                    if safe_shop_for_item(description) is not None
                ]
            if self.return_home_equipment_index < len(
                self.return_home_equipment_plan
            ):
                keyword = self.return_home_equipment_plan[
                    self.return_home_equipment_index
                ]
                self.return_home_equipment_index += 1
                return BotDecision(
                    f"wear {keyword}",
                    "let remaining recovered equipment replace a conflicting item",
                )
            if not self.saved:
                self.saved = True
                self.stage = "saving"
                return BotDecision("save", "persist safe recall recovery")
            self.stage = "complete"
            return BotDecision("quit", "safe recall recovery complete")

        if self.guildmaster_research:
            research = self._guildmaster_research_decision(state)
            if research is not None:
                return research
            if not self.saved:
                self.saved = True
                self.stage = "saving"
                return BotDecision("save", "persist mage Guildmaster route evidence")
            self.stage = "complete"
            return BotDecision("quit", "mage Guildmaster route research complete")

        if self.magic_shop_research:
            research = self._magic_shop_research_decision(state)
            if research is not None:
                return research
            if not self.saved:
                self.saved = True
                self.stage = "saving"
                return BotDecision("save", "persist Magic Shop stock evidence")
            self.stage = "complete"
            return BotDecision("quit", "Magic Shop research complete")

        if self.liquidate_loot:
            sale = self._liquidate_loot_decision(state)
            if sale is not None:
                return sale
            if not self.saved:
                self.saved = True
                self.stage = "saving"
                return BotDecision("save", "persist safe Midgaard loot sales")
            self.stage = "complete"
            return BotDecision("quit", "safe loot liquidation complete")

        if self.fastwalk_route is not None:
            research = self._fastwalk_research_decision(state)
            if research is not None:
                return research
            if self.failure is not None:
                return None
            if not self.saved:
                self.saved = True
                self.stage = "saving"
                return BotDecision("save", "persist official fastwalk route evidence")
            self.stage = "complete"
            return BotDecision("quit", "official fastwalk research complete")

        if self.moria_research:
            research = self._moria_research_decision(state)
            if research is not None:
                return research
            if not self.saved:
                self.saved = True
                self.stage = "saving"
                return BotDecision("save", "persist Moria approach route evidence")
            self.stage = "complete"
            return BotDecision("quit", "Moria approach route research complete")

        if room_vnum == "3724" or room_name == "general supplies":
            return self._store_decision()

        if _move_ratio(state) <= 0.1:
            self.waiting_for_move = True
            return BotDecision("sleep", "recover movement before continuing arena patrol")

        if (
            state.level is not None
            and state.level >= self.objective_level
            and self.course_complete
            and self.provisioned
            and self.practiced
        ):
            if not self.saved:
                self.saved = True
                self.stage = "saving"
                return BotDecision(
                    "save",
                    f"persist progress through level {self.objective_level}",
                )
            self.stage = "complete"
            return BotDecision("quit", "starter objective complete")

        if room_vnum == "3001" or "temple of midgaard" in room_name:
            return BotDecision("up", "return to the Mud School entrance")
        if room_vnum == "3054" or "altar of the temple" in room_name:
            return BotDecision("south", "return from the Temple healer")
        if room_vnum == "3009" or room_name == "the bakery":
            return BotDecision("south", "leave the Bakery for the Mud School")
        guild_to_school_routes = {
            "3019": "west",
            "3018": "north",
            "3017": "north",
            "3012": "east",
        }
        direction = guild_to_school_routes.get(room_vnum or "")
        if direction is not None:
            return BotDecision(
                direction,
                "follow the Midgaard map from the Mage Guild to Mud School",
            )
        if room_vnum == "3013" or room_name == "main street":
            return BotDecision("east", "return through Market Square to the Temple")
        if room_vnum == "3014" or room_name == "market square":
            return BotDecision("north", "return from Market Square to Temple Square")
        if room_vnum == "3005" or room_name == "the temple square":
            return BotDecision("north", "return from Temple Square to the Mud School")
        if room_vnum == "3737" or room_name == "safety":
            return BotDecision(
                "enter portal",
                "return from the arena safety room to the Mud School",
            )

        if room_vnum == "3725" or "entrance to the mud school" in room_name:
            if not self.course_started:
                return self._open_then_move("north", "enter the obstacle course")
            if not self.course_complete:
                self.course_complete = len(self.visited_course_rooms) >= 2
            if not self.practiced:
                return BotDecision("east", "visit the Loremaster after basic training")
            return self._open_then_move("south", "enter the level-one combat arena")

        if room_vnum == "3726" or "loremaster" in room_name:
            return self._loremaster_decision()

        if room_vnum == "3728" or "arena" in room_name:
            return self._arena_decision(state)

        if self.course_started or _is_training_vnum(room_vnum):
            return self._course_decision(state)

        if _health_ratio(state) < 0.25:
            return BotDecision("sleep", "recover below 25 percent health")

        key = _room_key(state)
        if self.room_query_counts.get(key, 0) == 0:
            self.room_query_counts[key] = 1
            return BotDecision("look imp", "request deterministic tutorial guidance")
        self.failure = f"no starter rule for room {state.room_name!r} ({state.room_vnum})"
        return None

    def _resupply_decision(self, state: CharacterState) -> BotDecision | None:
        if not (self.needs_food or self.needs_drink):
            return None

        if _is_sleeping(state):
            return BotDecision("stand", "wake before eating or drinking")

        if self.needs_food and (
            _has_inventory_item(state.inventory, "pie") or self.food_ordered
        ):
            return BotDecision("eat pie", "address hunger before further recovery")
        if self.needs_drink and (
            _has_inventory_item(state.inventory, "water skin") or self.skin_ordered
        ):
            return BotDecision("drink skin", "address thirst before further recovery")

        room_vnum = state.room_vnum
        room_name = (state.room_name or "").casefold()
        if room_vnum == "3724" or room_name == "general supplies":
            if self.insufficient_funds:
                sale = _sellable_inventory_keyword(state.inventory)
                if sale is None:
                    self.failure = "insufficient funds for emergency supplies and no sellable equipment"
                    return None
                self.insufficient_funds = False
                return BotDecision(
                    f"sell {sale}",
                    f"sell scavenged equipment ({sale}) for emergency supplies",
                )
            if self.needs_food and not self.food_ordered:
                return BotDecision("buy 6 pie", "stock emergency food from the Quartermaster")
            if self.needs_drink and not self.skin_ordered:
                return BotDecision("buy skin", "buy a full buffalo water skin from the Quartermaster")
            return None

        if room_vnum == "3737" or room_name == "safety":
            return BotDecision("enter portal", "leave the arena safety room for supplies")
        if _is_arena_vnum(room_vnum):
            return BotDecision("up", "leave the arena for emergency supplies")
        if room_vnum == "3725" or "entrance to the mud school" in room_name:
            return BotDecision("up", "visit General Supplies for emergency provisions")
        if room_vnum == "3001" or "temple of midgaard" in room_name:
            return BotDecision("up", "return to the Mud School supplies")
        if room_vnum == "3054" or "altar of the temple" in room_name:
            return BotDecision("south", "return from the Temple toward supplies")
        return None

    def _combat_spell_decision(self, state: CharacterState) -> BotDecision | None:
        if (
            self.spec.character_class != "mage"
            or not self.active_target
            or self.magic_missile_cast
        ):
            return None
        if _mana_ratio(state) < 0.15:
            return None
        target = _target_keyword(self.active_target)
        self.magic_missile_cast = True
        return BotDecision(
            f"cast 'magic missile' {target}",
            f"cast magic missile at arena opponent {self.active_target}",
        )

    def _city_restock_decision(self, state: CharacterState) -> BotDecision | None:
        """Use the verified Midgaard fountain and bakery route, then stop."""
        if _is_sleeping(state):
            return BotDecision("stand", "wake before travelling to city supplies")

        room_vnum = state.room_vnum
        room_name = (state.room_name or "").casefold()
        if room_vnum == "3737" or room_name == "safety":
            return BotDecision("enter portal", "leave arena Safety for Midgaard")
        if room_vnum == "3725" or "entrance to the mud school" in room_name:
            return BotDecision("down", "travel from Mud School to the Temple")
        if room_vnum == "3001" or "temple of midgaard" in room_name:
            return BotDecision("south", "travel from the Temple to Temple Square")
        if self.city_restock_step < 3:
            fountain_routes = {
                "3019": "west",
                "3018": "north",
                "3017": "north",
                "3012": "east",
                "3013": "east",
                "3014": "north",
            }
            direction = fountain_routes.get(room_vnum or "")
            if direction is not None:
                return BotDecision(
                    direction,
                    "walk from the Mage Guild to the Temple Square fountain",
                )
        if room_vnum == "3005" or room_name == "the temple square":
            commands = (
                ("fill skin", "fill the buffalo water skin at Temple Square"),
                ("drink skin", "drink from the freshly filled water skin"),
                ("south", "continue from Temple Square to the market"),
            )
            index = min(self.city_restock_step, len(commands) - 1)
            self.city_restock_step += 1
            command, reason = commands[index]
            return BotDecision(command, reason)
        if room_vnum == "3014" or room_name == "market square":
            return BotDecision("west", "take Main Street toward the Bakery")
        if room_vnum == "3013" or room_name == "main street":
            return BotDecision("north", "enter the Midgaard Bakery")
        if room_vnum == "3009" or room_name == "the bakery":
            if (
                self.affordable_pies
                and not self.affordable_pies_ordered
                and self.city_restock_step >= 5
            ):
                self.affordable_pies_ordered = True
                return BotDecision(
                    f"buy {self.affordable_pies} pie",
                    "retry the quantity the baker says is currently affordable",
                )
            commands = (
                ("list", "inspect the baker's current pie stock"),
                ("buy 6 pie", "buy six big pot pies from the baker"),
                ("inventory", "verify the city restock in carried inventory"),
            )
            index = self.city_restock_step - 3
            if 0 <= index < len(commands):
                self.city_restock_step += 1
                command, reason = commands[index]
                return BotDecision(command, reason)
            return None
        self.failure = (
            "no verified city-restock route for "
            f"room {state.room_name!r} ({state.room_vnum})"
        )
        return None

    def _guildmaster_research_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        """Visit Midgaard's Mage Guildmaster using source-backed room routes."""
        if _is_sleeping(state):
            return BotDecision("stand", "wake before travelling to the Mage Guild")
        room_vnum = state.room_vnum
        room_name = (state.room_name or "").casefold()
        if room_vnum == "3737" or room_name == "safety":
            return BotDecision("enter portal", "leave arena Safety for Midgaard")
        if _is_arena_vnum(room_vnum):
            return BotDecision("up", "leave the arena before travelling to Midgaard")
        if room_vnum == "3725" or "entrance to the mud school" in room_name:
            return BotDecision("down", "leave Mud School for the Temple")
        if room_vnum == "3033" or room_name == "the magic shop":
            return BotDecision("south", "return from the Magic Shop to the Mage Guild route")
        routes = {
            "3001": "south",
            "3005": "south",
            "3014": "west",
            "3013": "west",
            "3012": "south",
            "3017": "south",
            "3018": "east",
        }
        direction = routes.get(room_vnum or "")
        if direction is not None:
            return BotDecision(direction, "follow the source-backed route to the Mage Guild")
        if room_vnum == "3019" or "mage's laboratory" in room_name:
            commands = (
                ("look guildmaster", "confirm the Magic Users Guildmaster"),
                ("practice", "inspect the Guildmaster's available mage training"),
            )
            if self.guildmaster_step < len(commands):
                command, reason = commands[self.guildmaster_step]
                self.guildmaster_step += 1
                return BotDecision(command, reason)
            return None
        self.failure = (
            "no verified Mage Guild route for "
            f"room {state.room_name!r} ({state.room_vnum})"
        )
        return None

    def _moria_research_decision(self, state: CharacterState) -> BotDecision | None:
        """Verify the safe Midgaard-to-Moria approach, then return to the Mage Guild."""
        room_vnum = state.room_vnum
        room_name = (state.room_name or "").casefold()
        area = (state.area or "").casefold()

        if room_vnum == "300":
            if room_vnum not in self.moria_observed_rooms:
                self.moria_seen = True
                self.moria_observed_rooms.add(room_vnum)
                return BotDecision("look", "record the Moria-to-plains boundary room")
            self.moria_returning = True
            return self._moria_return_decision(state)

        if area == "moria":
            room = room_vnum or room_name
            if room not in self.moria_observed_rooms:
                self.moria_seen = True
                self.moria_observed_rooms.add(room)
                return BotDecision("look", "record the current Moria trail room")
            if (
                not self.moria_returning
                and len(self.moria_observed_rooms) <= self.moria_depth
            ):
                outward_routes = {
                    "3900": "north",
                    "3901": "north",
                    "3902": "east",
                    "3903": "east",
                    "3904": "north",
                }
                direction = outward_routes.get(room_vnum or "")
                if direction is not None:
                    return BotDecision(
                        direction,
                        "extend the bounded Moria trail scout",
                    )
                self.failure = (
                    "no verified forward Moria trail route for "
                    f"room {state.room_name!r} ({state.room_vnum})"
                )
                return None
            self.moria_returning = True
            return self._moria_return_decision(state)

        if self.moria_returning:
            if "outside the west gate" in room_name:
                return BotDecision("east", "return through Midgaard's West Gate")
            if "inside the west gate" in room_name:
                return BotDecision("east", "return from the West Gate to Main Street")
            return_routes = {
                "3012": "south",
                "3017": "south",
                "3018": "east",
            }
            direction = return_routes.get(room_vnum or "")
            if direction is not None:
                return BotDecision(direction, "return from Moria to the Mage Guild")
            if room_vnum == "3019" or "mage's laboratory" in room_name:
                return None
        else:
            outward_routes = {
                "3019": "west",
                "3018": "north",
                "3017": "north",
                "3012": "west",
            }
            direction = outward_routes.get(room_vnum or "")
            if direction is not None:
                return BotDecision(direction, "follow the verified route to Midgaard's West Gate")
            if "inside the west gate" in room_name:
                return BotDecision("west", "leave Midgaard through the West Gate")
            if "outside the west gate" in room_name:
                return BotDecision("north", "enter Moria from the West Gate")

        self.failure = (
            "no verified Moria approach route for "
            f"room {state.room_name!r} ({state.room_vnum})"
        )
        return None

    def _magic_shop_research_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        """Record shop stock without buying an unverified item."""
        room_vnum = state.room_vnum
        room_name = (state.room_name or "").casefold()
        if room_vnum == "3033" or room_name == "the magic shop":
            if self.magic_shop_purchase_failed:
                return BotDecision(
                    "south",
                    "return after the current light blue potion price was unaffordable",
                )
            commands = [("list", "record Magic Shop stock and potion prices")]
            if self.magic_shop_buy_fly:
                commands.extend(
                    (
                        ("buy light", "buy the requested light blue travel potion"),
                        ("inventory", "confirm the light blue potion was bought"),
                        ("quaff light", "use the light blue travel potion"),
                        ("affects", "record the potion's active travel effect"),
                    )
                )
            if self.magic_shop_step < len(commands):
                command, reason = commands[self.magic_shop_step]
                self.magic_shop_step += 1
                return BotDecision(command, reason)
            return BotDecision("south", "return from the Magic Shop to the Mage Guild")

        if self.magic_shop_step == 0:
            outward_routes = {
                "3019": "west",
                "3018": "north",
                "3017": "north",
                "3012": "north",
            }
            direction = outward_routes.get(room_vnum or "")
            if direction is not None:
                return BotDecision(direction, "follow the verified route to the Magic Shop")
        else:
            return_routes = {
                "3012": "south",
                "3017": "south",
                "3018": "east",
            }
            direction = return_routes.get(room_vnum or "")
            if direction is not None:
                return BotDecision(direction, "return from the Magic Shop to the Mage Guild")
            if room_vnum == "3019" or "mage's laboratory" in room_name:
                return None

        self.failure = (
            "no verified Magic Shop route for "
            f"room {state.room_name!r} ({state.room_vnum})"
        )
        return None

    def _fastwalk_research_decision(self, state: CharacterState) -> BotDecision | None:
        """Exercise an official recall-origin route one command at a time."""
        assert self.fastwalk_route is not None
        room_vnum = state.room_vnum
        room_name = (state.room_name or "").casefold()
        room_key = room_vnum or ""

        if (
            not self.combat_active
            and self.active_target is None
            and room_key in self.pending_loot_rooms
        ):
            if self.fastwalk_loot_step == 0:
                self.fastwalk_loot_step = 1
                return BotDecision(
                    "get all corpse",
                    "collect equipment and money from a fastwalk-route kill",
                )
            if (
                self.fastwalk_loot_step == 1
                and self.fastwalk_route.loot_container is not None
            ):
                self.fastwalk_loot_step = 2
                return BotDecision(
                    f"open {self.fastwalk_route.loot_container}",
                    "open the source-backed loot container before extraction",
                )
            if (
                self.fastwalk_loot_step == 2
                and self.fastwalk_route.loot_container is not None
            ):
                self.fastwalk_loot_step = 3
                return BotDecision(
                    f"get all {self.fastwalk_route.loot_container}",
                    "extract money and useful contents from the opened loot container",
                )
            self.fastwalk_loot_step = 0
            self.pending_loot_rooms.discard(room_key)
            objective_killed = (
                self.fastwalk_attack_target is not None
                and self.fastwalk_last_kill_target is not None
                and _targets_match(
                    self.fastwalk_last_kill_target,
                    self.fastwalk_attack_target,
                )
            )
            self.fastwalk_recall_after_loot = (
                self.fastwalk_route.recall_after_loot
                and (objective_killed or _health_ratio(state) < 0.8)
            )
            self.fastwalk_last_kill_target = None
            return BotDecision(
                "inventory",
                "record loot before choosing whether to continue or recall",
            )

        if not self.fastwalk_returning:
            if self.fastwalk_recall_after_loot:
                self.fastwalk_recall_after_loot = False
                self.fastwalk_returning = True
                return BotDecision(
                    "recall",
                    "leave a one-way hunt immediately after securing loot",
                )
            if not self.fastwalk_recall_started:
                if room_vnum == "3001":
                    self.fastwalk_recall_started = True
                elif room_vnum == "3737" or room_name == "safety":
                    return BotDecision(
                        "enter portal",
                        "leave arena Safety without paying the recall movement penalty",
                    )
                elif room_vnum == "3725" or "entrance to the mud school" in room_name:
                    return BotDecision(
                        "down",
                        "walk from Mud School to the fastwalk recall origin",
                    )
                elif _is_arena_vnum(room_vnum):
                    return BotDecision(
                        "up",
                        "leave the arena through Safety before the field hunt",
                    )
                elif room_vnum in {
                    "3005",
                    "3014",
                    "3013",
                    "3012",
                    "3017",
                    "3018",
                    "3019",
                    "3025",
                    "3054",
                    "3009",
                }:
                    origin_routes = {
                        "3019": "west",
                        "3018": "north",
                        "3017": "north",
                        "3012": "east",
                        "3013": "east",
                        "3014": "north",
                        "3005": "north",
                        "3025": "north",
                        "3054": "south",
                        "3009": "south",
                    }
                    return BotDecision(
                        origin_routes[room_vnum],
                        "walk to the fastwalk origin without paying the recall movement penalty",
                    )
                else:
                    self.fastwalk_recall_started = True
                    return BotDecision("recall", "start the official recall-origin fastwalk")
            if self.fastwalk_outbound_index == 0 and room_vnum != "3001":
                self.failure = (
                    "recall did not reach the Midgaard Temple before fastwalk "
                    f"{self.fastwalk_route.name!r}"
                )
                return None
            if self.fastwalk_outbound_index < len(self.fastwalk_route.commands):
                command = self.fastwalk_route.commands[self.fastwalk_outbound_index]
                self.fastwalk_outbound_index += 1
                return BotDecision(command, f"follow official fastwalk {self.fastwalk_route.name}")
            if not self.fastwalk_arrival_observed:
                self.fastwalk_arrival_observed = True
                return BotDecision("look", "record the official fastwalk endpoint")
            if (
                self.fastwalk_attack_started
                and not self.combat_active
                and self.active_target is None
            ):
                if self.fastwalk_objective_killed:
                    if (
                        self.fastwalk_explore_distance > 0
                        and not self.fastwalk_withdrawing
                    ):
                        self.fastwalk_withdrawing = True
                        self.fastwalk_return_steps_remaining = (
                            self.fastwalk_explore_distance
                        )
                    if self.fastwalk_return_steps_remaining > 0:
                        self.fastwalk_return_steps_remaining -= 1
                        return BotDecision(
                            _opposite_direction(self.fastwalk_explore_direction),
                            "return from the one-hop fastwalk combat room",
                        )
                    self.fastwalk_returning = True
                    return BotDecision("recall", "return after endpoint fastwalk combat")
                if (
                    self.fastwalk_pursuit_direction is not None
                    and self.fastwalk_pursuit_steps < 3
                ):
                    direction = self.fastwalk_pursuit_direction
                    self.fastwalk_pursuit_direction = None
                    self.fastwalk_pursuit_steps += 1
                    return BotDecision(
                        direction,
                        "pursue the requested target after it fled",
                    )
                if any(
                    _targets_match(target, self.fastwalk_attack_target or "")
                    for target in self.room_targets.get(room_vnum or "", [])
                ):
                    self.active_target = self.fastwalk_attack_target
                    self.combat_active = True
                    return BotDecision(
                        f"kill {_target_keyword(self.fastwalk_attack_target or '')}",
                        "re-engage the requested target after bounded pursuit",
                    )
                self.fastwalk_target_absent = True
                if (
                    self.fastwalk_explore_distance > 0
                    and not self.fastwalk_withdrawing
                ):
                    self.fastwalk_withdrawing = True
                    self.fastwalk_return_steps_remaining = (
                        self.fastwalk_explore_distance
                    )
                if self.fastwalk_return_steps_remaining > 0:
                    self.fastwalk_return_steps_remaining -= 1
                    return BotDecision(
                        _opposite_direction(self.fastwalk_explore_direction),
                        "return from the one-hop fastwalk combat room",
                    )
                self.fastwalk_returning = True
                return BotDecision("recall", "return after endpoint fastwalk combat")
            if (
                self.fastwalk_attack_target is not None
                and not self.fastwalk_attack_started
                and any(
                    _targets_match(target, self.fastwalk_attack_target)
                    for target in self.room_targets.get(room_vnum or "", [])
                )
            ):
                self.fastwalk_attack_started = True
                self.active_target = self.fastwalk_attack_target
                self.combat_active = True
                return BotDecision(
                    f"kill {_target_keyword(self.fastwalk_attack_target)}",
                    "attack the requested target found in the bounded fastwalk search",
                )
            if self.fastwalk_explore_direction is not None:
                if self.fastwalk_withdrawing:
                    if self.fastwalk_return_steps_remaining > 0:
                        self.fastwalk_return_steps_remaining -= 1
                        return BotDecision(
                            _opposite_direction(self.fastwalk_explore_direction),
                            "backtrack the bounded fastwalk search",
                        )
                    self.fastwalk_returning = True
                    return BotDecision("recall", "return from the fastwalk endpoint")
                if self.fastwalk_explore_look_pending:
                    self.fastwalk_explore_look_pending = False
                    self.fastwalk_explore_step = self.fastwalk_explore_distance * 2
                    return BotDecision(
                        "look",
                        "record the current bounded fastwalk exploration room",
                    )
                if self.fastwalk_explore_distance < self.fastwalk_explore_depth:
                    self.fastwalk_explore_distance += 1
                    self.fastwalk_explore_step = (
                        self.fastwalk_explore_distance * 2 - 1
                    )
                    self.fastwalk_explore_look_pending = True
                    return BotDecision(
                        self.fastwalk_explore_direction,
                        "inspect the next room in the bounded fastwalk search",
                    )
                if (
                    self.fastwalk_attack_target is not None
                    and not self.fastwalk_attack_started
                ):
                    self.fastwalk_target_absent = True
                self.fastwalk_withdrawing = True
                self.fastwalk_return_steps_remaining = self.fastwalk_explore_distance
                if self.fastwalk_return_steps_remaining > 0:
                    self.fastwalk_return_steps_remaining -= 1
                    return BotDecision(
                        _opposite_direction(self.fastwalk_explore_direction),
                        "withdraw after the bounded target search",
                    )
            self.fastwalk_returning = True
            return BotDecision("recall", "return from the fastwalk endpoint")

        if room_vnum == "3054":
            return BotDecision("south", "leave the healer after fastwalk recovery")
        if room_vnum == "3001":
            home_routes = {
                "3001": "south",
                "3005": "south",
                "3014": "west",
                "3013": "west",
                "3012": "south",
                "3017": "south",
                "3018": "east",
            }
            return BotDecision("south", "return from recall to the Mage Guild")
        if room_vnum in {"3005", "3014", "3013", "3012", "3017", "3018"}:
            home_routes = {
                "3005": "south",
                "3014": "west",
                "3013": "west",
                "3012": "south",
                "3017": "south",
                "3018": "east",
            }
            return BotDecision(home_routes[room_vnum], "return from recall to the Mage Guild")
        if room_vnum == "3019" or "mage's laboratory" in room_name:
            return None

        if self.fastwalk_route.recall_after_loot:
            self.failure = (
                "recall-only fastwalk did not reach Midgaard Temple or Mage Guild "
                f"from room {state.room_name!r} ({state.room_vnum})"
            )
            return None
        reverse = _reverse_fastwalk_commands(self.fastwalk_route.commands)
        if self.fastwalk_return_index >= len(reverse):
            self.failure = (
                "fastwalk return did not reach Midgaard Temple or Mage Guild from "
                f"room {state.room_name!r} ({state.room_vnum})"
            )
            return None
        command = reverse[self.fastwalk_return_index]
        self.fastwalk_return_index += 1
        return BotDecision(command, "reverse the official fastwalk after recall failed")

    @property
    def fastwalk_objective_killed(self) -> bool:
        if self.fastwalk_attack_target is None:
            return True
        return any(
            _targets_match(
                str(kill["mob_name"]).casefold(),
                self.fastwalk_attack_target.casefold(),
            )
            for kill in self.completed_kills
        )

    def _liquidate_loot_decision(self, state: CharacterState) -> BotDecision | None:
        """Sell known equipment through source-backed safe Midgaard shops."""
        room_vnum = state.room_vnum
        if self.sale_phase == "plan":
            if room_vnum != "3019":
                self.failure = "safe loot liquidation must start in the Mage's Laboratory"
                return None
            has_purse = any(
                "purse" in description.casefold()
                for description in _inventory_descriptions(state.inventory)
            )
            if has_purse and self.sale_container_step == 0:
                self.sale_container_step = 1
                return BotDecision(
                    "open purse",
                    "open a carried purse before extracting its coins",
                )
            if has_purse and self.sale_container_step == 1:
                self.sale_container_step = 2
                return BotDecision(
                    "get all purse",
                    "extract carried coins before planning equipment sales",
                )
            projected_counts = Counter(self.loot_sale_counts)
            if self.world_boot_id is not None:
                projected_counts.update(
                    (row["item_keyword"], row["shop_name"])
                    for row in self.loot_sale_history
                    if row.get("boot_id") == self.world_boot_id
                )
            for description in _inventory_descriptions(state.inventory):
                shop = safe_shop_for_item(description, projected_counts)
                if shop is not None:
                    keyword = sale_keyword(description)
                    self.sale_plan.append((keyword, shop))
                    projected_counts[(keyword, shop.name)] += 1
            self.sale_phase = "outbound"

        if self.sale_index >= len(self.sale_plan):
            return None

        keyword, shop = self.sale_plan[self.sale_index]
        if self.sale_phase == "outbound":
            if self.sale_route_index < len(shop.route_from_mage_lab):
                command = shop.route_from_mage_lab[self.sale_route_index]
                self.sale_route_index += 1
                return BotDecision(
                    command,
                    f"walk safely to the {shop.name} for {shop.payout_percent}% base payout",
                )
            if room_vnum != shop.room_vnum:
                self.failure = (
                    f"safe shop route reached {state.room_name!r} ({room_vnum}), "
                    f"expected {shop.name} ({shop.room_vnum})"
                )
                return None
            self.sale_phase = "value"

        if self.sale_phase == "value":
            self.sale_phase = "sell"
            return BotDecision(
                f"value {keyword}",
                f"record the keeper's duplicate-adjusted offer for {keyword}",
            )
        if self.sale_phase == "sell":
            self.sale_phase = "inventory"
            return BotDecision(
                f"sell {keyword}",
                f"sell {keyword} to the best verified safe compatible shop",
            )
        if self.sale_phase == "inventory":
            self.sale_phase = "home"
            self.sale_route_index = 0
            return BotDecision("inventory", "confirm the sold item left inventory")
        if self.sale_route_index < len(shop.route_to_mage_lab):
            command = shop.route_to_mage_lab[self.sale_route_index]
            self.sale_route_index += 1
            return BotDecision(command, f"return safely from the {shop.name}")
        if room_vnum != "3019":
            self.failure = (
                f"safe return from {shop.name} reached {state.room_name!r} ({room_vnum})"
            )
            return None
        self.sale_index += 1
        self.sale_route_index = 0
        self.sale_phase = "outbound"
        return self._liquidate_loot_decision(state)

    def _return_home_decision(self, state: CharacterState) -> BotDecision | None:
        """Recall from an interrupted field run and return to the Mage Guild."""
        room_vnum = state.room_vnum
        room_name = (state.room_name or "").casefold()
        home_routes = {
            "3054": "south",
            "3025": "north",
            "3001": "south",
            "3005": "south",
            "3014": "west",
            "3013": "west",
            "3012": "south",
            "3017": "south",
            "3018": "east",
        }
        if not self.return_home_recall_started:
            self.return_home_recall_started = True
            if room_vnum not in home_routes and room_vnum != "3019":
                return BotDecision("recall", "recover an interrupted character to Midgaard")
        direction = home_routes.get(room_vnum or "")
        if direction is not None:
            return BotDecision(direction, "return from recall to the Mage Guild")
        if room_vnum == "3019" or "mage's laboratory" in room_name:
            return None
        self.failure = (
            "recall recovery did not reach Midgaard from "
            f"room {state.room_name!r} ({state.room_vnum})"
        )
        return None

    def _purgatory_recovery_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        """Retrieve the player's corpse and leave Purgatory before disconnecting."""
        room_vnum = state.room_vnum or ""
        if room_vnum == "427":
            if self.purgatory_judgement_step == 0:
                self.purgatory_judgement_step = 1
                return BotDecision(
                    "get all corpse",
                    "reclaim every possession from the protected player corpse",
                )
            if self.purgatory_judgement_step == 1:
                self.purgatory_judgement_step = 2
                return BotDecision(
                    "inventory",
                    "verify the corpse contents were reclaimed before leaving",
                )
            self.purgatory_judgement_step = 3
            self.purgatory_portal_entered = True
            return BotDecision("enter portal", "leave Purgatory through its portal")

        if self.purgatory_portal_entered and room_vnum == "3054":
            if not self.purgatory_sleep_started:
                self.purgatory_sleep_started = True
                return BotDecision(
                    "sleep",
                    "recover safely beside the healer after corpse retrieval",
                )
            if _is_sleeping(state):
                self.purgatory_recovery_complete = True
                return BotDecision(
                    "stand",
                    "wake after post-death recovery before walking home",
                )
            self.purgatory_recovery_complete = True
            return None

        if self.purgatory_recovery_complete:
            return None

        destination = _PURGATORY_DESTINATION_PATH.get(room_vnum)
        if destination is None:
            return BotDecision(
                "look",
                "refresh Purgatory position without disconnecting",
            )
        direction = _direction_to_destination(state, {destination})
        if direction is None:
            return BotDecision(
                "look",
                f"refresh randomized Purgatory exits toward room {destination}",
            )
        return BotDecision(
            direction,
            f"follow the Purgatory room graph toward protected corpse room {destination}",
        )

    def _moria_return_decision(self, state: CharacterState) -> BotDecision:
        return_routes = {
            "3903": "west",
            "3904": "west",
            "3905": "west",
            "300": "south",
            "3902": "south",
            "3901": "south",
            "3900": "south",
        }
        direction = return_routes.get(state.room_vnum or "", "south")
        return BotDecision(direction, "return from Moria to the West Gate")

    def _recovery_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        ratio = _health_ratio(state)
        if self.waiting_for_heal:
            self.health_check_due = None
            self.waiting_for_heal = False
            return BotDecision("stand", "resume training after sanctuary recovery")
        room_name = (state.room_name or "").casefold()
        is_safe_room = (
            state.room_vnum in {"3054", "3721", "3737"}
            or "sanctuary" in room_name
            or "altar of the temple" in room_name
            or room_name == "safety"
            or "safe" in state.room_flags
        )
        if ratio >= 0.25:
            if _move_ratio(state) >= 0.5 and _mana_ratio(state) >= 0.5:
                return None
            if self.fastwalk_route is not None and state.room_vnum == "3001":
                return BotDecision(
                    "north",
                    "recover faster with the healer north of recall",
                )
            if not is_safe_room:
                return None
            if (
                self.fastwalk_route is not None
                and state.room_vnum == "3054"
                and not self.healer_menu_checked
            ):
                self.healer_menu_checked = True
                return BotDecision("heal", "record the healer's current services")
            self.waiting_for_heal = True
            return BotDecision("sleep", "recover movement or mana in a safe room")

        if (
            is_safe_room
        ):
            self.waiting_for_heal = True
            return BotDecision("sleep", "recover under a safe-room healer")

        sanctuary_routes = {
            "3725": "down",
            "3001": "north",
            "3722": "south",
            "3716": "south",
            "3715": "south",
            "3712": "south",
            "3711": "north",
        }
        direction = sanctuary_routes.get(state.room_vnum or "")
        if direction is None and _is_arena_vnum(state.room_vnum):
            direction = "up"
        if direction is None:
            direction = _direction_to_destination(
                state,
                {"3712", "3715", "3716"},
            )
        if direction is not None:
            return BotDecision(direction, "retreat to the tutorial Sanctuary")
        return None

    def _store_decision(self) -> BotDecision:
        commands = (
            ("list", "inspect the real DD4 starter shop inventory"),
            ("buy 3 pie", "buy food for tutorial and early adventuring"),
            ("buy skin", "buy a refillable water container"),
            ("eat pie", "remove current hunger before further training"),
            ("drink skin", "remove current thirst before further training"),
            ("down", "leave General Supplies after provisioning"),
        )
        index = min(self.store_step, len(commands) - 1)
        self.store_step += 1
        if index == 4:
            self.provisioned = True
        command, reason = commands[index]
        return BotDecision(command, reason)

    def _course_decision(self, state: CharacterState) -> BotDecision | None:
        key = _room_key(state)
        room_name = (state.room_name or "").casefold()
        if self.pending_move is not None:
            direction = self.pending_move
            self.pending_move = None
            return BotDecision(direction, f"follow course route {direction}")

        if self.advice_direction is not None:
            direction = self.advice_direction
            self.advice_direction = None
            return self._open_then_move(direction, "follow the Imp's course guidance")

        if state.room_vnum == "3710" or "end of the obstacle course" in room_name:
            if self.room_query_counts.get(key, 0) == 0:
                self.room_query_counts[key] = 1
                return BotDecision(
                    "look imp",
                    "ask how to leave the end of the obstacle course",
                )
            return BotDecision("enter portal", "leave the completed obstacle course")

        if state.room_vnum in {"3700", "3701", "3702", "3703"}:
            direction = _unvisited_exit(state, self.visited_course_rooms)
            if direction is not None:
                return self._open_then_move(
                    direction,
                    "follow the new-character training prelude",
                )

        if state.room_vnum == "3723" or room_name == "victory":
            if self.room_query_counts.get(key, 0) == 0:
                self.room_query_counts[key] = 1
                return BotDecision(
                    "look imp",
                    "confirm combat-training completion",
                )
            return BotDecision(
                "enter portal",
                "continue after completing combat training",
            )

        if state.room_vnum in {"3711", "3721"}:
            return BotDecision("north", "continue from the tutorial staging area")

        if state.room_vnum in _TRAINING_CENTERS:
            side_rooms, onward = _TRAINING_CENTERS[state.room_vnum]
            for destination in side_rooms:
                if destination in self.cleared_training_rooms:
                    continue
                direction = _direction_to_destination(state, {destination})
                if direction is not None:
                    return self._open_then_move(
                        direction,
                        "enter the next required combat-training room",
                    )
            direction = _direction_to_destination(state, {onward})
            if direction is not None:
                return self._open_then_move(
                    direction,
                    "continue after completing this combat-training section",
                )

        if state.room_vnum in _TRAINING_SIDE_ROOMS:
            return self._training_fight_decision(
                state,
                return_vnum=_TRAINING_SIDE_ROOMS[state.room_vnum],
            )

        if state.room_vnum == "3722" or "final combat" in room_name:
            return self._final_combat_decision(state)

        if self.room_query_counts.get(key, 0) == 0:
            self.room_query_counts[key] = 1
            return BotDecision("look imp", "ask the Imp for obstacle-course guidance")

        direction = _unvisited_exit(state, self.visited_course_rooms)
        if direction is not None:
            return self._open_then_move(
                direction,
                "take the next unvisited obstacle-course exit",
            )

        if self.room_query_counts.get(key, 0) < 2:
            self.room_query_counts[key] = 2
            return BotDecision(
                "look imp",
                "retry tutorial guidance after delayed server output",
            )
        self.failure = (
            f"obstacle course is stuck in {state.room_name!r} ({state.room_vnum})"
        )
        return None

    def _training_fight_decision(
        self,
        state: CharacterState,
        *,
        return_vnum: str,
    ) -> BotDecision:
        key = _room_key(state)
        if key in self.pending_loot_rooms:
            step = self.post_kill_steps.get(key, 0)
            if step == 0:
                self.post_kill_steps[key] = 1
                return BotDecision(
                    "get all corpse",
                    "loot the defeated tutorial opponent",
                )
            self.post_kill_steps[key] = 0
            self.pending_loot_rooms.discard(key)
            known = set(self.room_targets.get(key, []))
            defeated = self.defeated_targets.get(key, set())
            if known and known <= defeated:
                self.cleared_training_rooms.add(key)
            return BotDecision("wear all", "equip useful tutorial loot")

        if key not in self.cleared_training_rooms:
            targets = self.room_targets.get(key, [])
            defeated = self.defeated_targets.get(key, set())
            target = next(
                (candidate for candidate in targets if candidate not in defeated),
                None,
            )
            if target is None:
                if self.room_query_counts.get(key, 0) == 0:
                    self.room_query_counts[key] = 1
                    return BotDecision(
                        "look",
                        "identify the combat-training opponent",
                    )
                self.cleared_training_rooms.add(key)
                return self._return_from_training_room(state, return_vnum)
            self.combat_active = True
            self.active_target = target
            return BotDecision(
                f"kill {_target_keyword(target)}",
                f"fight required tutorial opponent {target}",
            )

        return self._return_from_training_room(state, return_vnum)

    @staticmethod
    def _return_from_training_room(
        state: CharacterState,
        return_vnum: str,
    ) -> BotDecision:
        direction = _direction_to_destination(state, {return_vnum})
        if direction is None:
            direction = "out"
        return BotDecision(direction, "return to the combat-training corridor")

    def _final_combat_decision(self, state: CharacterState) -> BotDecision:
        key = _room_key(state)
        if key not in self.cleared_training_rooms:
            targets = self.room_targets.get(key, ["gladiator"])
            target = targets[0]
            self.combat_active = True
            self.active_target = target
            self.magic_missile_cast = False
            return BotDecision(
                f"kill {_target_keyword(target)}",
                "defeat the final tutorial gladiator",
            )

        step = self.post_kill_steps.get(key, 0)
        commands = (
            ("get all corpse", "loot the gladiator's key and equipment"),
            ("wear all", "equip the final tutorial rewards"),
            ("unlock north", "unlock the final tutorial door with the key"),
            ("open north", "open the unlocked final tutorial door"),
            ("north", "leave final combat"),
        )
        index = min(step, len(commands) - 1)
        self.post_kill_steps[key] = step + 1
        command, reason = commands[index]
        return BotDecision(command, reason)

    def _loremaster_decision(self) -> BotDecision:
        if self.loremaster_step == 0:
            self.loremaster_step = 1
            return BotDecision("look loremaster", "ask the Loremaster about training")
        if self.loremaster_step == 1:
            self.loremaster_step = 2
            return BotDecision("practice", "list skills available to practice")
        if self.loremaster_step == 2:
            self.loremaster_step = 3
            candidates = _practice_candidates(self.text)
            preferred = _STARTER_SKILLS[self.spec.character_class]
            skill = (
                preferred
                if preferred in candidates
                else candidates[0] if candidates else preferred
            )
            return BotDecision(
                f"practice {skill}",
                f"practice a starter {self.spec.character_class} ability",
            )
        self.practiced = True
        return BotDecision("west", "return to the Mud School entrance")

    def _arena_decision(self, state: CharacterState) -> BotDecision:
        if state.level is not None and state.level >= self.objective_level:
            return BotDecision(
                "up",
                f"leave the arena after reaching level {self.objective_level}",
            )

        key = _room_key(state)
        self.arena_visited_rooms.add(key)
        if state.in_combat or state.combat_target:
            self.combat_active = True
            self.prompt_ready = False
            return None
        if not self.arena_queried:
            self.arena_queried = True
            return BotDecision("look imp", "ask the Imp for combat-arena guidance")

        if self.arena_pending_loot:
            if self.arena_loot_step == 0:
                self.arena_loot_step = 1
                return BotDecision("get all corpse", "loot the arena opponent")
            self.arena_pending_loot = False
            self.arena_loot_step = 0
            self.room_targets[key] = []
            self.defeated_targets.pop(key, None)
            self.room_query_counts[key] = 0
            return BotDecision("sacrifice corpse", "clear the arena corpse")

        targets = sorted(
            self.room_targets.get(key, []),
            key=_arena_target_priority,
        )
        if targets:
            target = targets[0]
            self.combat_active = True
            self.active_target = target
            return BotDecision(
                f"kill {_target_keyword(target)}",
                f"fight arena opponent {target}",
            )

        if self.room_query_counts.get(key, 0) == 0:
            self.room_query_counts[key] = 1
            return BotDecision("look", "identify arena opponents")

        direction = _unvisited_arena_exit(state, self.arena_visited_rooms)
        if direction is not None:
            return BotDecision(direction, "search the next arena section")
        self._reset_arena_patrol()
        self.arena_respawn_due = time.monotonic() + _ARENA_RESPAWN_WAIT_SECONDS
        return BotDecision("up", "reset arena route through the safe entrance")

    def _reset_arena_patrol(self) -> None:
        """Forget stale creature sightings before a fresh arena circuit."""
        self.arena_visited_rooms.clear()
        for room in tuple(self.room_query_counts):
            if _is_arena_vnum(room):
                self.room_query_counts.pop(room)
        for room in tuple(self.room_targets):
            if _is_arena_vnum(room):
                self.room_targets.pop(room)
                self.defeated_targets.pop(room, None)

    def _open_then_move(self, direction: str, reason: str) -> BotDecision:
        if self.pending_move == direction:
            self.pending_move = None
            return BotDecision(direction, reason)
        self.pending_move = direction
        return BotDecision(f"open {direction}", f"open the way before: {reason}")


class StarterBotRunner:
    def __init__(
        self,
        spec: CharacterSpec,
        profile_path: Path,
        *,
        connection_factory: Callable[[CharacterSpec], TelnetConnection] | None = None,
        observation_parser: ObservationParser | None = None,
        character_state: CharacterState | None = None,
        objective_level: int = 2,
        resupply_only: bool = False,
        return_home: bool = False,
        city_restock: bool = False,
        guildmaster_research: bool = False,
        magic_shop_research: bool = False,
        magic_shop_buy_fly: bool = False,
        liquidate_loot: bool = False,
        fastwalk_route: Fastwalk | None = None,
        fastwalk_explore_direction: str | None = None,
        fastwalk_explore_depth: int = 1,
        fastwalk_attack_target: str | None = None,
        moria_research: bool = False,
        moria_depth: int = 0,
    ) -> None:
        self.spec = spec
        self.profile_path = profile_path
        self.connection_factory = connection_factory or self._default_connection
        self.observation_parser = observation_parser or ObservationParser()
        self.character_state = character_state or CharacterState()
        self.objective_level = objective_level
        self.resupply_only = resupply_only
        self.return_home = return_home
        self.city_restock = city_restock
        self.guildmaster_research = guildmaster_research
        self.magic_shop_research = magic_shop_research
        self.magic_shop_buy_fly = magic_shop_buy_fly
        self.liquidate_loot = liquidate_loot
        self.fastwalk_route = fastwalk_route
        self.fastwalk_explore_direction = fastwalk_explore_direction
        self.fastwalk_explore_depth = fastwalk_explore_depth
        self.fastwalk_attack_target = fastwalk_attack_target
        self.moria_research = moria_research
        self.moria_depth = moria_depth

    async def run(self) -> RunResult:
        storage = RunStorage(self.spec.database)
        run_id = storage.create_run(
            scenario_name=(
                f"restock:{self.spec.name}"
                if self.city_restock
                else f"sell-loot:{self.spec.name}"
                if self.liquidate_loot
                else f"return-home:{self.spec.name}"
                if self.return_home
                else f"guildmaster:{self.spec.name}"
                if self.guildmaster_research
                else f"magic-shop:{self.spec.name}"
                if self.magic_shop_research
                else f"fastwalk-{self.fastwalk_route.name}:{self.spec.name}"
                if self.fastwalk_route is not None
                else f"moria:{self.spec.name}"
                if self.moria_research
                else f"resupply:{self.spec.name}"
                if self.resupply_only
                else f"starter:{self.spec.name}"
            ),
            scenario_path=self.profile_path,
        )
        recorder = TranscriptRecorder.create(
            self.spec.transcript_dir,
            scenario_name=(
                f"restock-{self.spec.name}"
                if self.city_restock
                else f"sell-loot-{self.spec.name}"
                if self.liquidate_loot
                else f"return-home-{self.spec.name}"
                if self.return_home
                else f"guildmaster-{self.spec.name}"
                if self.guildmaster_research
                else f"magic-shop-{self.spec.name}"
                if self.magic_shop_research
                else f"fastwalk-{self.fastwalk_route.name}-{self.spec.name}"
                if self.fastwalk_route is not None
                else f"moria-{self.spec.name}"
                if self.moria_research
                else f"resupply-{self.spec.name}"
                if self.resupply_only
                else f"starter-{self.spec.name}"
            ),
            run_id=run_id,
        )
        storage.set_transcript_path(run_id, recorder.path)
        password = os.environ.get(self.spec.password_env)
        policy: StarterPolicy | None = None
        connection: TelnetConnection | None = None
        policy_research_persisted = False

        def persist_policy_research() -> None:
            nonlocal policy_research_persisted
            if policy is None or policy_research_persisted:
                return
            policy_research_persisted = True
            storage.set_run_boot_id(run_id, policy.world_boot_id)
            for kill in policy.completed_kills:
                storage.record_mob_kill(
                    run_id,
                    character_name=self.spec.name,
                    boot_id=policy.world_boot_id,
                    **kill,
                )
            for sale in policy.completed_sales:
                storage.record_loot_sale(
                    run_id,
                    character_name=self.spec.name,
                    boot_id=policy.world_boot_id,
                    **sale,
                )

        def record(kind: str, payload: dict[str, Any]) -> None:
            event = recorder.record(kind, payload)
            source_event_id = storage.record_event(
                run_id,
                kind=kind,
                payload=payload,
                timestamp=event.timestamp,
            )
            if kind != "game_event":
                return
            game_event = GameEvent(
                type=str(payload["type"]),
                source=str(payload["source"]),
                data=dict(payload["data"]),
            )
            if not self.character_state.apply(game_event):
                return
            snapshot_payload = {
                "reason": game_event.type,
                "source": game_event.source,
                "state": self.character_state.to_dict(),
            }
            snapshot_event = recorder.record("state_snapshot", snapshot_payload)
            storage.record_event(
                run_id,
                kind="state_snapshot",
                payload=snapshot_payload,
                timestamp=snapshot_event.timestamp,
            )
            storage.record_state_snapshot(
                run_id,
                source_event_id=source_event_id,
                reason=game_event.type,
                state=snapshot_payload["state"],
                timestamp=snapshot_event.timestamp,
            )

        try:
            if password is None:
                try:
                    password = load_character_password(self.spec.credential_name)
                except CredentialStoreError as exc:
                    raise RuntimeError(str(exc)) from exc
            policy = StarterPolicy(
                self.spec,
                password,
                objective_level=self.objective_level,
                resupply_only=self.resupply_only,
                return_home=self.return_home,
                city_restock=self.city_restock,
                guildmaster_research=self.guildmaster_research,
                magic_shop_research=self.magic_shop_research,
                magic_shop_buy_fly=self.magic_shop_buy_fly,
                liquidate_loot=self.liquidate_loot,
                loot_sale_history=[
                    dict(row) for row in storage.list_loot_sales(self.spec.name)
                ]
                if self.liquidate_loot
                else None,
                query_world_time=(
                    self.liquidate_loot or self.fastwalk_route is not None
                ),
                fastwalk_route=self.fastwalk_route,
                fastwalk_explore_direction=self.fastwalk_explore_direction,
                fastwalk_explore_depth=self.fastwalk_explore_depth,
                fastwalk_attack_target=self.fastwalk_attack_target,
                moria_research=self.moria_research,
                moria_depth=self.moria_depth,
            )
            deadline = asyncio.get_running_loop().time() + self.spec.max_runtime
            commands = 0
            reconnects = 0
            repeated_command = ""
            repeated_count = 0

            while not policy.done:
                if policy.failure:
                    raise RuntimeError(policy.failure)
                if asyncio.get_running_loop().time() >= deadline:
                    raise TimeoutError(
                        f"Starter bot exceeded {self.spec.max_runtime:g} second runtime"
                    )
                if commands >= self.spec.max_commands:
                    raise RuntimeError(
                        f"Starter bot exceeded {self.spec.max_commands} command budget"
                    )

                if connection is None or connection.closed:
                    if connection is not None:
                        await connection.close()
                        policy.on_connection_closed()
                        reconnects += 1
                        if reconnects > 3:
                            raise ConnectionError("Starter bot exceeded reconnect limit")
                        record(
                            "state",
                            {"state": "reconnecting", "attempt": reconnects},
                        )
                        await asyncio.sleep(1)
                    connection = self.connection_factory(self.spec)
                    record(
                        "state",
                        {
                            "state": "connecting",
                            "host": self.spec.host,
                            "port": self.spec.port,
                        },
                    )
                    await connection.connect()
                    record("state", {"state": "connected"})

                result = await connection.read_available(timeout=0.25)
                if result.empty:
                    self._flush_observations(record, policy)
                else:
                    self._record_read(result, record, policy)

                decision = policy.next_decision(self.character_state)
                if decision is None:
                    continue

                decision_payload = {
                    "stage": policy.stage,
                    "reason": decision.reason,
                    "command": "[REDACTED]" if decision.secret else decision.command,
                    "redacted": decision.secret,
                }
                if decision.command == repeated_command:
                    repeated_count += 1
                else:
                    repeated_command = decision.command
                    repeated_count = 1
                repeat_limit = 6
                if self.fastwalk_route is not None:
                    route_commands = self.fastwalk_route.commands
                    if not self.fastwalk_route.recall_after_loot:
                        route_commands += _reverse_fastwalk_commands(
                            self.fastwalk_route.commands
                        )
                    repeat_limit = max(
                        repeat_limit,
                        _max_consecutive_command(route_commands, decision.command),
                    )
                if repeated_count > repeat_limit:
                    raise RuntimeError(
                        f"Starter bot repeated {decision.command!r} too many times"
                    )
                record("decision", decision_payload)
                record(
                    "command",
                    {
                        "command": "[REDACTED]" if decision.secret else decision.command,
                        "environment": self.spec.password_env if decision.secret else None,
                        "redacted": decision.secret,
                    },
                )
                await connection.send_command(decision.command)
                commands += 1
                policy.after_command(decision)

            if not policy.fastwalk_objective_killed:
                raise RuntimeError(
                    "bounded fastwalk attack returned safely without a "
                    f"confirmed {self.fastwalk_attack_target} kill"
                )
            record(
                "state",
                {
                    "state": "completed",
                    "commands": commands,
                    "stage": policy.stage,
                    "target_subclass": self.spec.subclass,
                    "objective_level": self.objective_level,
                    "resupply_only": self.resupply_only,
                    "return_home": self.return_home,
                    "city_restock": self.city_restock,
                    "guildmaster_research": self.guildmaster_research,
                    "magic_shop_research": self.magic_shop_research,
                    "magic_shop_buy_fly": self.magic_shop_buy_fly,
                    "magic_shop_purchase_failed": policy.magic_shop_purchase_failed,
                    "liquidate_loot": self.liquidate_loot,
                    "world_boot_id": policy.world_boot_id,
                    "completed_kills": policy.completed_kills,
                    "sale_plan": [
                        {"keyword": keyword, "shop": shop.name}
                        for keyword, shop in policy.sale_plan
                    ],
                    "fastwalk_route": self.fastwalk_route.name if self.fastwalk_route else None,
                    "fastwalk_explore_direction": self.fastwalk_explore_direction,
                    "fastwalk_explore_depth": self.fastwalk_explore_depth,
                    "fastwalk_attack_target": self.fastwalk_attack_target,
                    "fastwalk_target_absent": policy.fastwalk_target_absent,
                    "fastwalk_objective_killed": policy.fastwalk_objective_killed,
                    "missing_targets": {
                        room: sorted(targets)
                        for room, targets in sorted(policy.missing_targets.items())
                    },
                    "moria_research": self.moria_research,
                    "moria_depth": self.moria_depth,
                },
            )
            persist_policy_research()
            storage.finish_run(run_id, status="success")
            return RunResult(
                run_id,
                "success",
                recorder.path,
                storage.path,
                self.character_state.to_dict(),
            )
        except Exception as exc:
            if policy is not None:
                self._flush_observations(record, policy)
            persist_policy_research()
            record("state", {"state": "failed", "error": str(exc)})
            storage.finish_run(run_id, status="failed", error=str(exc))
            raise
        finally:
            if connection is not None:
                await connection.close()
            recorder.close()
            storage.close()

    def _record_read(
        self,
        result: ReadResult,
        record: Callable[[str, dict[str, Any]], None],
        policy: StarterPolicy,
    ) -> None:
        events: list[GameEvent] = []
        if result.text:
            record("response", {"text": result.text})
            policy.observe_text(result.text)
            events.extend(self.observation_parser.feed_text(result.text))
        for message in result.gmcp_messages:
            record("gmcp", {"message": message})
            events.extend(self.observation_parser.feed_gmcp(message))
        for negotiation in result.negotiations:
            record(
                "state",
                {
                    "state": "telnet_negotiation",
                    "command": negotiation.command,
                    "option": negotiation.option,
                },
            )
        self._record_game_events(events, record, policy)

    def _flush_observations(
        self,
        record: Callable[[str, dict[str, Any]], None],
        policy: StarterPolicy,
    ) -> None:
        self._record_game_events(
            self.observation_parser.flush_text(),
            record,
            policy,
        )

    def _record_game_events(
        self,
        events: list[GameEvent],
        record: Callable[[str, dict[str, Any]], None],
        policy: StarterPolicy,
    ) -> None:
        for event in events:
            record("game_event", event.as_payload())
        policy.observe_events(events, self.character_state)

    def _default_connection(self, spec: CharacterSpec) -> TelnetConnection:
        return TelnetConnection(spec.host, spec.port, timeout=spec.timeout)


async def run_starter_profile(path: str | Path) -> RunResult:
    profile_path = Path(path)
    spec = load_character_spec(profile_path)
    return await StarterBotRunner(spec, profile_path).run()


async def run_arena_research_profile(
    path: str | Path,
    *,
    target_level: int = 3,
) -> RunResult:
    if not 3 <= target_level <= 10:
        raise ValueError("target_level must be between 3 and 10")
    profile_path = Path(path)
    spec = load_character_spec(profile_path)
    return await StarterBotRunner(
        spec,
        profile_path,
        objective_level=target_level,
    ).run()


async def run_resupply_profile(path: str | Path) -> RunResult:
    profile_path = Path(path)
    spec = load_character_spec(profile_path)
    return await StarterBotRunner(
        spec,
        profile_path,
        resupply_only=True,
    ).run()


async def run_return_home_profile(path: str | Path) -> RunResult:
    profile_path = Path(path)
    spec = load_character_spec(profile_path)
    return await StarterBotRunner(
        spec,
        profile_path,
        return_home=True,
    ).run()


async def run_restock_profile(path: str | Path) -> RunResult:
    profile_path = Path(path)
    spec = load_character_spec(profile_path)
    return await StarterBotRunner(
        spec,
        profile_path,
        city_restock=True,
    ).run()


async def run_sell_loot_profile(path: str | Path) -> RunResult:
    profile_path = Path(path)
    spec = load_character_spec(profile_path)
    return await StarterBotRunner(
        spec,
        profile_path,
        liquidate_loot=True,
    ).run()


async def run_guildmaster_research_profile(path: str | Path) -> RunResult:
    profile_path = Path(path)
    spec = load_character_spec(profile_path)
    return await StarterBotRunner(
        spec,
        profile_path,
        guildmaster_research=True,
    ).run()


async def run_magic_shop_research_profile(
    path: str | Path,
    *,
    buy_fly: bool = False,
) -> RunResult:
    profile_path = Path(path)
    spec = load_character_spec(profile_path)
    return await StarterBotRunner(
        spec,
        profile_path,
        magic_shop_research=True,
        magic_shop_buy_fly=buy_fly,
    ).run()


async def run_fastwalk_research_profile(
    path: str | Path,
    route_name: str,
    *,
    explore_direction: str | None = None,
    explore_depth: int = 1,
    attack_target: str | None = None,
) -> RunResult:
    profile_path = Path(path)
    spec = load_character_spec(profile_path)
    return await StarterBotRunner(
        spec,
        profile_path,
        fastwalk_route=route_named(route_name),
        fastwalk_explore_direction=explore_direction,
        fastwalk_explore_depth=explore_depth,
        fastwalk_attack_target=attack_target,
    ).run()


async def run_moria_research_profile(
    path: str | Path,
    *,
    depth: int = 0,
) -> RunResult:
    profile_path = Path(path)
    spec = load_character_spec(profile_path)
    return await StarterBotRunner(
        spec,
        profile_path,
        moria_research=True,
        moria_depth=depth,
    ).run()


def _room_key(state: CharacterState) -> str:
    return state.room_vnum or (state.room_name or "").casefold()


def _is_training_vnum(vnum: str | None) -> bool:
    return bool(vnum and vnum.isdigit() and 3700 <= int(vnum) <= 3723)


def _health_ratio(state: CharacterState) -> float:
    if state.hp is None or state.max_hp in (None, 0):
        return 1.0
    return float(state.hp) / float(state.max_hp)


def _move_ratio(state: CharacterState) -> float:
    if state.move is None or state.max_move in (None, 0):
        return 1.0
    return float(state.move) / float(state.max_move)


def _mana_ratio(state: CharacterState) -> float:
    if state.mana is None or state.max_mana in (None, 0):
        return 1.0
    return float(state.mana) / float(state.max_mana)


def _recovery_ready(state: CharacterState) -> bool:
    return (
        _health_ratio(state) >= 0.5
        and _move_ratio(state) >= 0.5
        and _mana_ratio(state) >= 0.5
    )


def _is_sleeping(state: CharacterState) -> bool:
    position = state.position
    return position == 4 or str(position).casefold() == "sleeping"


def _reverse_fastwalk_commands(commands: tuple[str, ...]) -> tuple[str, ...]:
    opposite = {
        "north": "south",
        "south": "north",
        "east": "west",
        "west": "east",
        "up": "down",
        "down": "up",
    }
    try:
        return tuple(opposite[command] for command in reversed(commands))
    except KeyError as exc:
        raise ValueError(
            "fastwalk route cannot be reversed safely because it includes "
            f"{exc.args[0]!r}"
        ) from exc


def _max_consecutive_command(commands: tuple[str, ...], command: str) -> int:
    longest = 0
    current = 0
    for candidate in commands:
        if candidate == command:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _opposite_direction(direction: str) -> str:
    return {
        "north": "south",
        "south": "north",
        "east": "west",
        "west": "east",
        "up": "down",
        "down": "up",
    }[direction]


def _unvisited_exit(
    state: CharacterState,
    visited: set[str],
) -> str | None:
    ordered = ("n", "e", "s", "w", "u", "d")
    for short in ordered:
        if short not in state.exits:
            continue
        destination = state.exits[short]
        if destination is None or destination not in visited:
            return _DIRECTION_SHORTCUTS[short]
    return None


def _direction_to_destination(
    state: CharacterState,
    destinations: set[str],
) -> str | None:
    for short, destination in state.exits.items():
        if destination in destinations:
            return _DIRECTION_SHORTCUTS.get(short, short)
    return None


def _practice_candidates(text: str) -> list[str]:
    marker = "skills which may be learned:"
    folded = text.casefold()
    marker_index = folded.find(marker)
    if marker_index == -1:
        return []
    section = text[marker_index + len(marker) :]
    section = section.split("You have", maxsplit=1)[0]
    candidates: list[str] = []
    pattern = re.compile(r"([A-Za-z][A-Za-z '-]{1,30}?):\s*\d+%")
    for match in pattern.finditer(section):
        candidate = " ".join(match.group(1).casefold().split())
        if candidate not in candidates:
            candidates.append(candidate)
    return candidates


def _training_targets(text: str) -> list[str]:
    pattern = re.compile(
        r"(?:^|\n)\s*(?:\([^)]*\)\s*)*(?:A|An|The)\s+"
        r"(?P<target>[A-Za-z][A-Za-z'-]*(?:\s+[A-Za-z][A-Za-z'-]*){0,2}?)\s+"
        r"(?:[A-Za-z]+ly\s+)?"
        r"(?:is|are|sits?|circles?|stands?|waits?|prepares?|paces?|growls?|"
        r"prowls?|hisses?|snarls?|cowers?|lies?|looks?|watches?|spits?|barks?|"
        r"glares?|grunts?|screams?|cries?|lunges?|shuffles?|crouches?|"
        r"scowls?|yells?|cringes?|tries?|makes?)\b",
        re.IGNORECASE,
    )
    ignored_keywords = {
        "ceiling",
        "cleric",
        "corpse",
        "door",
        "floor",
        "gate",
        "heart",
        "imp",
        "officer",
        "portal",
        "recruit",
        "recruits",
        "room",
        "soldier",
        "soldiers",
        "staircase",
        "tunnel",
        "wall",
        "yard",
    }
    targets: list[str] = []
    for match in pattern.finditer(text):
        target = " ".join(match.group("target").casefold().split())
        words = set(target.replace("'s", "").split())
        if (
            not words.intersection(ignored_keywords)
            and not target.startswith("imp ")
            and target not in targets
        ):
            targets.append(target)
    return targets


def _defeated_mobile(text: str) -> str | None:
    match = _MOB_DEATH.search(text)
    if match is None:
        return None
    words = match.group("target").casefold().split()
    while words and words[0] in {"a", "an", "the"}:
        words.pop(0)
    return " ".join(words) or None


def _target_keyword(target: str) -> str:
    return target.rsplit(maxsplit=1)[-1]


def _targets_match(observed: str, requested: str) -> bool:
    """Treat a requested descriptor and the MUD's shorter mobile name as equivalent."""
    return observed == requested or _target_keyword(observed) == _target_keyword(requested)


def _arena_target_priority(target: str) -> tuple[int, str]:
    normalized = target.casefold()
    return (0 if "wolf" in normalized else 1, normalized)


def _is_arena_vnum(vnum: str | None) -> bool:
    return bool(vnum and vnum.isdigit() and 3728 <= int(vnum) <= 3737)


def _unvisited_arena_exit(
    state: CharacterState,
    visited: set[str],
) -> str | None:
    for short in ("w", "e", "s", "n"):
        destination = state.exits.get(short)
        if destination and _is_arena_vnum(destination) and destination not in visited:
            return _DIRECTION_SHORTCUTS[short]
    return None


def _has_inventory_item(value: Any, needle: str) -> bool:
    if isinstance(value, dict):
        return any(_has_inventory_item(item, needle) for item in value.values())
    if isinstance(value, list):
        return any(_has_inventory_item(item, needle) for item in value)
    return needle in str(value).casefold()


def _sellable_inventory_keyword(value: Any) -> str | None:
    """Choose a conservative equipment keyword, never food or water storage."""
    names = _inventory_descriptions(value)
    equipment_words = {
        "armor", "axe", "blade", "boots", "bracer", "dagger", "gloves",
        "helm", "mace", "shield", "sword", "wand", "weapon",
    }
    for name in names:
        words = name.casefold().replace("'", "").split()
        if {"pie", "skin", "water", "food"}.intersection(words):
            continue
        for word in reversed(words):
            if word in equipment_words:
                return word
    return None


def _inventory_descriptions(value: Any) -> list[str]:
    if isinstance(value, str):
        cleaned = _ANSI_ESCAPE.sub("", value).strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            return []
        return _inventory_descriptions(parsed)
    if isinstance(value, dict):
        description = value.get("short_desc")
        result = [str(description)] if isinstance(description, str) else []
        for item in value.values():
            result.extend(_inventory_descriptions(item))
        return result
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(_inventory_descriptions(item))
        return result
    return []
