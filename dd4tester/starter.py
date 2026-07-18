from __future__ import annotations

import asyncio
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .character import CharacterSpec, load_character_spec
from .connection import ReadResult, TelnetConnection
from .credentials import CredentialStoreError, load_character_password
from .observations import GameEvent, ObservationParser
from .runner import RunResult
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
        city_restock: bool = False,
        guildmaster_research: bool = False,
    ) -> None:
        if objective_level < 2:
            raise ValueError("objective_level must be at least 2")
        self.spec = spec
        self.password = password
        self.objective_level = objective_level
        self.resupply_only = resupply_only
        self.city_restock = city_restock
        self.guildmaster_research = guildmaster_research
        self.stage = "login"
        self.done = False
        self.failure: str | None = None
        self.awaiting_reconnect = False
        self.in_world = False
        self.prompt_ready = False
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
        self.health_check_due: float | None = None
        self.waiting_for_move = False
        self.room_targets: dict[str, list[str]] = {}
        self.defeated_targets: dict[str, set[str]] = {}
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
        self.guildmaster_step = 0

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
        if "is dead" in folded or "you receive" in folded and "experience" in folded:
            self.combat_active = False
            if self.current_room and self.active_target:
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
        if "you attack " in folded or " attacks you" in folded:
            self.combat_active = True
        if "aren't fighting anyone" in folded:
            self.combat_active = False
            self.active_target = None
            self.magic_missile_cast = False
        if "aren't here" in folded or "do not see that here" in folded:
            self.combat_active = False
            if self.current_room and self.active_target:
                self.defeated_targets.setdefault(self.current_room, set()).add(
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

    def observe_events(
        self,
        events: list[GameEvent],
        state: CharacterState,
    ) -> None:
        for event in events:
            if event.type == "prompt_seen":
                self.prompt_ready = True
            if event.type in {"room_entered", "room_updated"}:
                room = _room_key(state)
                if room and room != self.current_room:
                    self.previous_room = self.current_room
                    self.current_room = room
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
        self.text = ""
        if decision.command == "eat pie":
            self.food_attempted = True
            self.last_consumption = "food"
            self.needs_food = False
        elif decision.command == "drink skin":
            self.drink_attempted = True
            self.last_consumption = "drink"
            self.needs_drink = False
        elif decision.command == "buy 6 pie":
            self.food_ordered = True
        elif decision.command == "buy skin":
            self.skin_ordered = True
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
            if _health_ratio(state) >= 0.5:
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
                self.prompt_ready = False
                return None

        if _is_sleeping(state):
            return BotDecision("stand", "wake before travel or arena actions")

        if self.combat_active:
            if self.needs_food or self.needs_drink or _health_ratio(state) < 0.25:
                return BotDecision("flee", "leave combat before emergency resupply")
            spell = self._combat_spell_decision(state)
            if spell is not None:
                return spell
            self.prompt_ready = False
            return None

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

    def _recovery_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        ratio = _health_ratio(state)
        if self.waiting_for_heal:
            self.health_check_due = None
            self.waiting_for_heal = False
            return BotDecision("stand", "resume training after sanctuary recovery")
        if ratio >= 0.25:
            return None

        room_name = (state.room_name or "").casefold()
        if (
            state.room_vnum in {"3054", "3721", "3737"}
            or "sanctuary" in room_name
            or "altar of the temple" in room_name
            or room_name == "safety"
            or "safe" in state.room_flags
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
        city_restock: bool = False,
        guildmaster_research: bool = False,
    ) -> None:
        self.spec = spec
        self.profile_path = profile_path
        self.connection_factory = connection_factory or self._default_connection
        self.observation_parser = observation_parser or ObservationParser()
        self.character_state = character_state or CharacterState()
        self.objective_level = objective_level
        self.resupply_only = resupply_only
        self.city_restock = city_restock
        self.guildmaster_research = guildmaster_research

    async def run(self) -> RunResult:
        storage = RunStorage(self.spec.database)
        run_id = storage.create_run(
            scenario_name=(
                f"restock:{self.spec.name}"
                if self.city_restock
                else f"guildmaster:{self.spec.name}"
                if self.guildmaster_research
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
                else f"guildmaster-{self.spec.name}"
                if self.guildmaster_research
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
                city_restock=self.city_restock,
                guildmaster_research=self.guildmaster_research,
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
                if repeated_count > 6:
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

            record(
                "state",
                {
                    "state": "completed",
                    "commands": commands,
                    "stage": policy.stage,
                    "target_subclass": self.spec.subclass,
                    "objective_level": self.objective_level,
                    "resupply_only": self.resupply_only,
                    "city_restock": self.city_restock,
                    "guildmaster_research": self.guildmaster_research,
                },
            )
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


async def run_restock_profile(path: str | Path) -> RunResult:
    profile_path = Path(path)
    spec = load_character_spec(profile_path)
    return await StarterBotRunner(
        spec,
        profile_path,
        city_restock=True,
    ).run()


async def run_guildmaster_research_profile(path: str | Path) -> RunResult:
    profile_path = Path(path)
    spec = load_character_spec(profile_path)
    return await StarterBotRunner(
        spec,
        profile_path,
        guildmaster_research=True,
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


def _is_sleeping(state: CharacterState) -> bool:
    position = state.position
    return position == 4 or str(position).casefold() == "sleeping"


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


def _target_keyword(target: str) -> str:
    return target.rsplit(maxsplit=1)[-1]


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
