from __future__ import annotations

import asyncio
import json
import os
import re
import time
from collections import Counter, deque
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Collection, Mapping

from .archetypes import archetype_registry
from .character import CharacterSpec, load_character_spec
from .connection import CommandConnection, ReadResult, TelnetConnection
from .credentials import CredentialStoreError, load_character_password
from .decisions import classify_decision
from .equipment import (
    GearCatalog,
    ITEM_FOOD,
    STANCE_COMBAT,
    STANCE_PRE_LEVEL,
    STANCE_RECOVERY,
    is_capacity_infrastructure,
    is_blunt_weapon,
    is_bow,
    is_disposable_food,
    is_piercing_weapon,
    is_strength_penalty_ring,
    item_category,
    item_command_keyword,
    item_keyword,
    load_gear_catalog,
    normalize_item_name,
    plan_stance,
    plan_stance_swaps,
    protects_from_sale,
    stance_score,
)
from .fastwalks import Fastwalk, route_named
from .hunt_candidates import (
    ITEM_CONTAINER,
    ObjectSource,
    load_world_source,
)
from .observations import GameEvent, ObservationParser
from .mudlet import MudletConnection
from .runner import RunResult
from .shops import SafeShop, safe_shop_for_item, sale_keyword
from .state import CharacterState
from .storage import RunStorage
from .training import (
    TrainingChoice,
    parse_practice_listing,
    plan_training,
    training_priorities_for,
)
from .transcript import TranscriptRecorder


_ANSI_ESCAPE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
_MUD_COLOUR_CODE = re.compile(r"(?:\{.|<\d+>)")
_TARGET_SELECTOR_PREFIX = re.compile(
    r"^\s*\[#(?P<target_id>\d+)\]\s*",
    re.MULTILINE,
)
_MOBILE_STATUS_PREFIX = re.compile(r"^(?:\([^)]*\)\s*)+")
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
_PRACTICE_BALANCE = re.compile(
    r"You have\s+(?P<physical>\d+).*?physical.*?"
    r"and\s+(?P<intellectual>\d+).*?intellectual practices remaining",
    re.IGNORECASE | re.DOTALL,
)
_SCORE_PRACTICE_BALANCE = re.compile(
    r"Physical pracs:\s*(?P<physical>\d+)\.\s*"
    r"Intellectual pracs:\s*(?P<intellectual>\d+)\.",
    re.IGNORECASE,
)
_SCORE_STAT = re.compile(
    r"^(?P<stat>Str|Int|Wis|Dex|Con):\s*(?P<current>\d+)\s*"
    r"\(\s*(?P<permanent>\d+)\s*\)(?P<maxed>\+?)",
    re.IGNORECASE | re.MULTILINE,
)
_EQUIPMENT_WEAPON_SLOT = re.compile(
    r"^\s*\[weapon\]\s+(?P<item>[^\r\n]+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_PRACTICE_REJECTIONS = (
    ("you're in no position to learn anything right now", "invalid posture"),
    ("not in your current form", "invalid form"),
    ("who is going to teach you", "no trainer present"),
    ("i have never heard of that ability", "unknown ability"),
    ("not yet of the right calibre for my knowledge", "trainer level requirement"),
    ("haven't the potential to obtain further knowledge", "no intellectual practices"),
    ("haven't the ability to learn more skills", "no physical practices"),
    ("i have insufficient knowledge to help you", "trainer proficiency cap"),
    ("you are not ready for that knowledge", "unmet prerequisites"),
)
_IDENTIFIED_VALUE = re.compile(
    r"\bis worth\s+(?P<coins>\d+)\s+copper coins?\b",
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
_MOB_ATTACKS_YOU = re.compile(
    r"\b(?P<attacker>[A-Za-z][A-Za-z '-]{0,60})'s .{0,80}\b(?:misses|hits|"
    r"scratches|grazes|injures|wounds|mauls|decimates|mangles|maims|"
    r"mutilates|disembowels|eviscerates|massacres|demolishes|devastates|"
    r"annihilates|obliterates|ravages|cripples|brutalises|vapourises) you\b",
    re.IGNORECASE,
)
_MOB_DIRECT_ATTACKS_YOU = re.compile(
    r"\b(?P<attacker>[A-Za-z][A-Za-z '-]{0,60}?)\s+(?:misses|hits|"
    r"scratches|grazes|injures|wounds|mauls|decimates|mangles|maims|"
    r"mutilates|disembowels|eviscerates|massacres|demolishes|devastates|"
    r"annihilates|obliterates|ravages|cripples|brutalises|vapourises) you\b",
    re.IGNORECASE,
)
_CONSIDER_VIABLE_FRAGMENTS = (
    "looks like an easy kill",
    "looks like it would be easy to destroy",
    "the perfect match",
    "the perfect match for your destructive inclinations",
)
_CONSIDER_BELOW_BAND_FRAGMENTS = (
    # Source do_consider branches at level differences <= -10 and <= -5.
    "naked and weaponless",
    "is no match for you",
    "is no match for your offensive capabilities",
)
_CONSIDER_DANGEROUS_FRAGMENTS = (
    "do you feel lucky, punk?",
    "laughs at you mercilessly",
    "death will thank you",
    "could crush you with my little finger",
    "puny insect",
    "unimaginably more powerful",
    "they're not here",
)
_CONSIDER_REJECTED_FRAGMENTS = (
    _CONSIDER_BELOW_BAND_FRAGMENTS + _CONSIDER_DANGEROUS_FRAGMENTS
)
_EXPENDABLE_FIELD_JUNK = {
    "hairy key": "hairy",
    "shimmering key": "shimmering",
}
_SEVERED_BODY_PART = re.compile(
    r"\b(?P<part>head|heart|arm|leg|tail) is "
    r"(?:separated|torn|sliced)\b",
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
_OPPOSITE_DIRECTIONS = {
    "north": "south",
    "east": "west",
    "south": "north",
    "west": "east",
    "up": "down",
    "down": "up",
}
_CITY_REARM_PRIMARY_ROUTE = (
    "south",
    "south",
    "south",
    "east",
    "east",
    "north",
)
# Source-derived safe Midgaard road path from healer room 3054 to Dave the
# Dealer in road-crossing room 3120, whose reset inventory includes object 3352.
_CITY_REARM_POUNDING_ROUTE = (
    "south",
    "south",
    "south",
    "south",
    "west",
    "west",
    "west",
    "south",
    "south",
    "south",
    "east",
    "south",
    "south",
    "south",
    "south",
    "east",
)
_CITY_REARM_POUNDING_REQUIRED_FREE_WEIGHT = 5


@dataclass(frozen=True)
class _ClassTrainerRoute:
    room_vnum: str
    room_name: str
    keyword: str
    steps: tuple[tuple[str, str, str], ...]
    minimum_level: int = 10
    search_room_vnum: str | None = None

    @property
    def outbound(self) -> dict[str, str]:
        return {origin: command for origin, command, _ in self.steps}

    @property
    def destination_vnum(self) -> str:
        return self.search_room_vnum or self.room_vnum

    @property
    def return_commands(self) -> tuple[str, ...]:
        return tuple(
            _OPPOSITE_DIRECTIONS[command]
            for _, command, _ in reversed(self.steps)
        )

    @property
    def return_to_healer(self) -> dict[str, str]:
        return {
            destination: _OPPOSITE_DIRECTIONS[command]
            for _, command, destination in self.steps
        }

    @property
    def healer_return_paths(self) -> dict[str, tuple[str, ...]]:
        commands = ["south"]
        paths = {"3001": tuple(commands)}
        for _, command, destination in self.steps:
            commands.append(command)
            paths[destination] = tuple(commands)
        return paths


_CLASS_TRAINERS = {
    "mage": _ClassTrainerRoute(
        "3019",
        "Mage's Laboratory",
        "guildmaster",
        (
            ("3001", "south", "3005"),
            ("3005", "south", "3014"),
            ("3014", "west", "3013"),
            ("3013", "west", "3012"),
            ("3012", "south", "3017"),
            ("3017", "south", "3018"),
            ("3018", "east", "3019"),
        ),
    ),
    "cleric": _ClassTrainerRoute(
        "3002",
        "Cleric's Inner Sanctum",
        "guildmaster",
        (
            ("3001", "south", "3005"),
            ("3005", "west", "3004"),
            ("3004", "north", "3003"),
            ("3003", "west", "3002"),
        ),
    ),
    "thief": _ClassTrainerRoute(
        "3029",
        "The Secret Yard",
        "guildmaster",
        (
            ("3001", "south", "3005"),
            ("3005", "south", "3014"),
            ("3014", "south", "3025"),
            ("3025", "east", "3026"),
            ("3026", "south", "3027"),
            ("3027", "east", "3028"),
            ("3028", "south", "3029"),
        ),
    ),
    "warrior": _ClassTrainerRoute(
        "3023",
        "Tournament and Practice Yard",
        "guildmaster",
        (
            ("3001", "south", "3005"),
            ("3005", "south", "3014"),
            ("3014", "east", "3015"),
            ("3015", "east", "3016"),
            ("3016", "south", "3021"),
            ("3021", "east", "3022"),
            ("3022", "south", "3023"),
        ),
    ),
    "psionic": _ClassTrainerRoute(
        "3150",
        "The Psionic Guildmaster's Room",
        "guildmaster",
        (
            ("3001", "south", "3005"),
            ("3005", "south", "3014"),
            ("3014", "east", "3015"),
            ("3015", "east", "3016"),
            ("3016", "east", "3041"),
            ("3041", "north", "3152"),
            ("3152", "north", "3151"),
            ("3151", "west", "3150"),
        ),
    ),
    "brawler": _ClassTrainerRoute(
        "3218",
        "Practice Yard",
        "guildmaster",
        (
            ("3001", "south", "3005"),
            ("3005", "south", "3014"),
            ("3014", "south", "3025"),
            ("3025", "west", "3024"),
            ("3024", "west", "3044"),
            ("3044", "south", "3206"),
            ("3206", "south", "3207"),
            ("3207", "east", "3218"),
        ),
    ),
    "shifter": _ClassTrainerRoute(
        "3221",
        "Shapeshifter's Guild",
        "guildmaster",
        (
            ("3001", "south", "3005"),
            ("3005", "south", "3014"),
            ("3014", "south", "3025"),
            ("3025", "east", "3026"),
            ("3026", "east", "3045"),
            ("3045", "east", "3046"),
            ("3046", "north", "3219"),
            ("3219", "north", "3220"),
            ("3220", "west", "3221"),
        ),
    ),
    "ranger": _ClassTrainerRoute(
        "3048",
        "The Lusty Ogres Tavern",
        "ranger",
        (
            ("3001", "south", "3005"),
            ("3005", "south", "3014"),
            ("3014", "south", "3025"),
            ("3025", "west", "3024"),
            ("3024", "south", "3048"),
        ),
    ),
    "smithy": _ClassTrainerRoute(
        "3050",
        "The Forge",
        "craftsman",
        (
            ("3001", "south", "3005"),
            ("3005", "south", "3014"),
            ("3014", "south", "3025"),
            ("3025", "east", "3026"),
            ("3026", "east", "3045"),
            ("3045", "east", "3046"),
            ("3046", "south", "3050"),
        ),
    ),
}
_ADVANCED_CLASS_TRAINERS = {
    "thief": _ClassTrainerRoute(
        "25205",
        "Olive Grove",
        "leader",
        (
            ("3001", "south", "3005"),
            ("3005", "south", "3014"),
            ("3014", "east", "3015"),
            ("3015", "east", "3016"),
            ("3016", "east", "3041"),
            ("3041", "east", "3053"),
            ("3053", "east", "3503"),
            ("3503", "east", "3502"),
            ("3502", "south", "5261"),
            ("5261", "south", "5260"),
            ("5260", "south", "5259"),
            ("5259", "south", "5258"),
            ("5258", "east", "5262"),
            ("5262", "east", "5263"),
            ("5263", "south", "5264"),
            ("5264", "east", "5265"),
            ("5265", "east", "5266"),
            ("5266", "down", "5267"),
            ("5267", "east", "1701"),
            ("1701", "east", "1702"),
            ("1702", "north", "1704"),
            ("1704", "north", "1705"),
            ("1705", "north", "1706"),
            ("1706", "north", "1707"),
            ("1707", "north", "1708"),
            ("1708", "east", "1720"),
            ("1720", "east", "25200"),
            ("25200", "east", "25201"),
            ("25201", "east", "25202"),
            ("25202", "east", "25203"),
            ("25203", "south", "25205"),
            ("25205", "west", "25204"),
        ),
        minimum_level=15,
        search_room_vnum="25204",
    ),
}
_ALL_CLASS_TRAINERS = (
    *_CLASS_TRAINERS.values(),
    *_ADVANCED_CLASS_TRAINERS.values(),
)
_CLASS_TRAINER_HEALER_ROUTES = {
    room_vnum: direction
    for trainer in _ALL_CLASS_TRAINERS
    for room_vnum, direction in trainer.return_to_healer.items()
}
_CLASS_TRAINER_HEALER_RETURN_PATHS = {
    room_vnum: commands
    for trainer in _ALL_CLASS_TRAINERS
    for room_vnum, commands in trainer.healer_return_paths.items()
}
_MIDGAARD_HEALER_ROUTES = {
    "3724": "down",
    "3725": "down",
    "3726": "west",
    "3001": "north",
    **_CLASS_TRAINER_HEALER_ROUTES,
}
_MIDGAARD_CITY_HEALER_ROOMS = frozenset(
    {"3001", *_CLASS_TRAINER_HEALER_ROUTES}
)
_MIDGAARD_HEALER_RETURN_ROUTES = {
    "3724": ("south", "up", "up"),
    "3725": ("south", "up"),
    "3726": ("south", "up", "east"),
    **_CLASS_TRAINER_HEALER_RETURN_PATHS,
}
_MIDGAARD_HEALER_TO_MAGE_LAB_ROUTES = {
    "3054": "south",
    **_CLASS_TRAINERS["mage"].outbound,
}
# The Great Eastern Desert is a randomized maze and blocks recall. Navigate
# it from live GMCP exits until the stable river-tunnel room, then use the
# source-backed route to the Midgaard healer.
_PYRAMID_DESERT_MAZE_ROOMS = frozenset(
    {
        "5007",
        "5024",
        "5025",
        "5026",
        "5027",
        "5028",
        "5029",
        "5030",
        "5031",
        "5032",
    }
)
_PYRAMID_LIVE_ROUTE_ROOMS = _PYRAMID_DESERT_MAZE_ROOMS | {"5056", "2600"}
_PYRAMID_HEALER_RETURN_COMMANDS = (
    *("west",) * 9,
    *("north",) * 2,
    *("west",) * 2,
    *("north",) * 4,
)
# The Shadow Grove uses randomized exits and blocks recall.  Navigate the
# grove from live GMCP exits to its stable entrance, then use the source-backed
# reverse route through Haon Dor and Midgaard to the healer.
_SHADOW_GROVE_ROOMS = frozenset({str(vnum) for vnum in range(1300, 1310)})
_SHADOW_GROVE_HEALER_RETURN_COMMANDS = (
    "south",
    "east",
    "south",
    *("east",) * 3,
    "north",
    "east",
    "north",
    "north",
    *("east",) * 2,
    "north",
    *("east",) * 13,
    *("north",) * 3,
)
# Mud School resets at age 14. After a reset it starts at 12, and the two
# randomized area pulses each take 30-90 seconds while the area is vacant.
_ARENA_RESPAWN_WAIT_SECONDS = 180
_HEALTH_CHECK_WAIT_SECONDS = 30
_COMMAND_PROMPT_MIN_SECONDS = 0.05
_POST_FLEE_AUDIT_GRACE_SECONDS = 0.75
_COMBAT_ACTION_COOLDOWN_SECONDS = 3.0
# Field play is deliberately 50% more aggressive than the original safety
# profile. These values are half of the original reserve thresholds, with a
# longer combat bound; hard withdrawal conditions still take precedence.
_FIELD_COMBAT_TIMEOUT_SECONDS = 360.0
_FIELD_COMBAT_PLATEAU_SECONDS = 60.0
_MIDGAARD_DRUNK_TIMEOUT_SECONDS = 60.0
_PRE_LEVEL_XP_FRACTION = 0.10
_FIELD_CONTINUE_HEALTH_RATIO = 0.225
_FIELD_CONTINUE_MANA_RATIO = 0.075
_FIELD_CONTINUE_MOVE_RATIO = 0.05
_FIELD_READY_HEALTH_RATIO = 0.375
_FIELD_READY_MANA_RATIO = 0.15
_FIELD_WITHDRAW_HEALTH_RATIO = 0.15
_FIELD_FINISH_HEALTH_RATIO = 0.10
_CASTER_MITIGATION_SPELLS = {
    "mage": (("armor", "armor", 5),),
    "cleric": (("armor", "armor", 5),),
    "psionic": (("thought shield", "thought shield", 5),),
}
_CLERIC_COMBAT_HEAL_RATIO = 0.35
_CLERIC_COMBAT_HEAL_MANA_RESERVE_RATIO = 0.30
_CLERIC_COMBAT_HEAL_LIMIT = 2
# High-risk and aggressive target approaches retain the 67.5% departure gate;
# the 50% setting applies to continuation and withdrawal reserves.
_FIELD_HIGH_RISK_START_HEALTH_RATIO = 0.675
_PIE_WEIGHT = 5
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
_EXIT_COMMANDS = {
    "n": "north",
    "e": "east",
    "s": "south",
    "w": "west",
    "u": "up",
    "d": "down",
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


def _decision_payload(decision: BotDecision, stage: str) -> dict[str, Any]:
    metadata = classify_decision(decision.command, decision.reason, stage)
    return {
        "stage": stage,
        "reason": decision.reason,
        "command": "[REDACTED]" if decision.secret else decision.command,
        "redacted": decision.secret,
        "category": metadata.category,
        "safety_critical": metadata.safety_critical,
    }


@dataclass(frozen=True)
class FieldHuntStop:
    route: tuple[str, ...]
    target: str | None = None
    where_target: str | None = None
    command_keyword: str | None = None
    actions: tuple[str, ...] = ()
    abort_if_where_target_absent: bool = False
    abort_if_where_room_names: tuple[str, ...] = ()
    post_actions: tuple[str, ...] = ()
    required_items: tuple[str, ...] = ()
    allowed_bystanders: tuple[str, ...] = ()
    trivial_bystanders: tuple[str, ...] = ()
    rejected_consider_subjects: tuple[str, ...] = ()
    minimum_health_ratio: float = _FIELD_CONTINUE_HEALTH_RATIO
    consider_only: bool = False
    exact_target: bool = False
    maximum_target_count: int = 1
    require_isolated: bool = False
    allow_local_recovery: bool = False
    allow_below_band_for_required_loot: bool = False
    minimum_combat_health_ratio: float = 0.0
    route_vnums: tuple[str, ...] = ()
    maximum_level_offset: int | None = None
    maximum_pursuit_steps: int = 1
    pursuit_room_vnums: tuple[str, ...] = ()
    selective_loot_keywords: tuple[str, ...] = ()
    abort_after_consider_rejection: bool = False


class StarterPolicy:
    """Deterministic rules for creation and DD4's first training sequence."""

    def __init__(
        self,
        spec: CharacterSpec,
        password: str,
        *,
        objective_level: int = 2,
        arena_kill_limit: int | None = None,
        arena_respawn_wait: bool = True,
        resupply_only: bool = False,
        return_home: bool = False,
        city_restock: bool = False,
        city_rearm: bool = False,
        city_rearm_pounding: bool = False,
        city_outfit: bool = False,
        audit_combat_pouch: bool = False,
        use_sanctuary_potions: bool = True,
        guildmaster_research: bool = False,
        magic_shop_research: bool = False,
        magic_shop_buy_fly: bool = False,
        flight_borrowing: bool = False,
        bank_excess_coins: bool = False,
        liquidate_loot: bool = False,
        emergency_provision_sale: bool = False,
        loot_sale_counts: Mapping[tuple[str, str], int] | None = None,
        loot_sale_history: list[Mapping[str, Any]] | None = None,
        query_world_time: bool = False,
        fastwalk_route: Fastwalk | None = None,
        fastwalk_explore_direction: str | None = None,
        fastwalk_explore_depth: int = 1,
        fastwalk_attack_target: str | None = None,
        fastwalk_origin_actions: tuple[str, ...] = (),
        fastwalk_defer_provision_resupply: bool = False,
        fastwalk_required_free_weight: int = 0,
        fastwalk_xp_first_capacity_threshold: int = 0,
        fastwalk_required_move: int = 0,
        vault_stow_items: tuple[str, ...] = (),
        vault_claim_items: tuple[str, ...] = (),
        vault_wear_claimed_items: bool = False,
        vault_required_free_weight: int = 0,
        vault_only: bool = False,
        fastwalk_world_cache_items: tuple[str, ...] = (),
        fastwalk_train_before_departure: bool = False,
        fastwalk_require_invisibility: bool = False,
        fastwalk_hunt_stops: tuple[FieldHuntStop, ...] = (),
        fastwalk_kill_limit: int | None = None,
        moria_research: bool = False,
        moria_depth: int = 0,
        gear_catalog: GearCatalog | None = None,
        source_mobile_targets: Mapping[str, tuple[str, ...]] | None = None,
        source_mobile_level_ranges: Mapping[str, tuple[int, int]] | None = None,
        practice_types_spent: frozenset[str] = frozenset(),
        rejected_practice_skills: frozenset[str] = frozenset(),
        counterbalance_preparation_required: bool = False,
        title_configured: bool = False,
        description_configured: bool = False,
        selected_training_stat: str | None = None,
        fastwalk_skip_target_sightings: frozenset[tuple[str, str]] = frozenset(),
    ) -> None:
        if objective_level < 2:
            raise ValueError("objective_level must be at least 2")
        if arena_kill_limit is not None and arena_kill_limit < 1:
            raise ValueError("arena_kill_limit must be positive")
        if fastwalk_kill_limit is not None and fastwalk_kill_limit < 1:
            raise ValueError("fastwalk_kill_limit must be positive")
        if fastwalk_required_free_weight < 0:
            raise ValueError("fastwalk_required_free_weight must not be negative")
        if fastwalk_xp_first_capacity_threshold < 0:
            raise ValueError(
                "fastwalk_xp_first_capacity_threshold must not be negative"
            )
        if fastwalk_required_move < 0:
            raise ValueError("fastwalk_required_move must not be negative")
        if moria_depth < 0:
            raise ValueError("moria_depth must not be negative")
        if not 1 <= fastwalk_explore_depth <= 6:
            raise ValueError("fastwalk_explore_depth must be between 1 and 6")
        self.spec = spec
        self.password = password
        self.objective_level = objective_level
        self.arena_kill_limit = arena_kill_limit
        self.arena_respawn_wait = arena_respawn_wait
        self.resupply_only = resupply_only
        self.return_home = return_home
        self.city_restock = city_restock
        self.city_rearm = city_rearm
        self.city_rearm_pounding = city_rearm_pounding
        self.city_outfit = city_outfit
        self.audit_combat_pouch = audit_combat_pouch
        self.use_sanctuary_potions = use_sanctuary_potions
        self.guildmaster_research = guildmaster_research
        self.magic_shop_research = magic_shop_research
        self.magic_shop_buy_fly = magic_shop_buy_fly
        self.flight_borrowing = flight_borrowing
        self.bank_excess_coins = bank_excess_coins
        self.liquidate_loot = liquidate_loot
        self.emergency_provision_sale = emergency_provision_sale
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
        self.fastwalk_requested_target = fastwalk_attack_target
        self.fastwalk_origin_actions = fastwalk_origin_actions
        self.fastwalk_defer_provision_resupply = fastwalk_defer_provision_resupply
        self.fastwalk_origin_action_index = 0
        self.fastwalk_required_free_weight = fastwalk_required_free_weight
        self.fastwalk_xp_first_capacity_threshold = (
            fastwalk_xp_first_capacity_threshold
        )
        self.fastwalk_required_move = fastwalk_required_move
        self.fastwalk_capacity_preflight_complete = (
            fastwalk_required_free_weight == 0
            and fastwalk_xp_first_capacity_threshold == 0
        )
        self.fastwalk_collect_loot = True
        self.fastwalk_autoloot_configured = False
        self.fastwalk_selective_loot = any(
            stop.selective_loot_keywords for stop in fastwalk_hunt_stops
        )
        self.fastwalk_selective_loot_index = 0
        self.fastwalk_autoloot_restored = not self.fastwalk_selective_loot
        self.fastwalk_targetmode_configured = False
        self.fastwalk_container_audited = False
        self.fastwalk_junk_disposal_attempted: set[str] = set()
        self.fastwalk_concealment_attempted: set[str] = set()
        self.fastwalk_mitigation_attempted: set[str] = set()
        self.nested_container_extractions: set[tuple[str, str]] = set()
        self.vault_stow_commands = tuple(
            command
            for item in vault_stow_items
            for command in (f"remove {item}", f"lodge {item}")
        ) + tuple(f"claim {item}" for item in vault_claim_items)
        self.vault_wear_claimed_items = vault_wear_claimed_items
        self.vault_stow_command_index = 0
        self.vault_stow_attempted_keywords = {
            item.casefold() for item in vault_stow_items
        }
        self.vault_empty_container_audits = tuple(
            item
            for item in vault_stow_items
            if "sack" in item.casefold() or "backpack" in item.casefold()
        )
        self.vault_empty_container_audit_index = 0
        self.vault_empty_container_audit_pending = False
        self.vault_verified_empty_containers: set[str] = set()
        self.vault_pending_lodge_keyword: str | None = None
        self.vault_pending_claim_keyword: str | None = None
        self.vault_lodged_items: list[str] = []
        self.vault_claimed_items: list[str] = []
        self.vault_rejected_lodge_keyword: str | None = None
        self.vault_capacity_disposal_pending = False
        self.vault_storage_rejected = False
        self.vault_required_free_weight = vault_required_free_weight
        self.vault_only = vault_only
        self.vault_stow_audit_requested = False
        self.vault_equipment_audit_pending = False
        self.vault_stow_returning = False
        self.vault_stow_complete = not self.vault_stow_commands
        self.fastwalk_world_cache_items = fastwalk_world_cache_items
        self.fastwalk_world_cache_preflight_index = 0
        self.fastwalk_world_cache_preflight_returning = False
        self.fastwalk_world_cache_preflight_complete = (
            not self.fastwalk_world_cache_items
        )
        self.fastwalk_world_cache_post_index = 0
        self.fastwalk_world_cache_post_returning = False
        self.fastwalk_world_cache_post_started = False
        self.fastwalk_world_cache_post_complete = not self.fastwalk_world_cache_items
        self.fastwalk_train_before_departure = fastwalk_train_before_departure
        self.fastwalk_training_started = False
        self.class_trainer_return_pending = False
        self.fastwalk_stat_training_configured = False
        self.selected_training_stat = selected_training_stat
        self.fastwalk_practice_audit_requested = False
        self.fastwalk_practice_audit_attempts = 0
        self.latest_practice_balances: tuple[int | None, int | None] = (None, None)
        self.fastwalk_require_invisibility = fastwalk_require_invisibility
        self.fastwalk_invisibility_attempts = 0
        self.fastwalk_invisibility_pending = False
        self.fastwalk_invisibility_unavailable = False
        self.fastwalk_hunt_stops = fastwalk_hunt_stops
        self.fastwalk_kill_limit = fastwalk_kill_limit
        self.fastwalk_hunt_stop_index = 0
        self.fastwalk_hunt_move_index = 0
        self.fastwalk_hunt_action_index = 0
        self.fastwalk_hunt_post_action_index = 0
        self.fastwalk_hunt_looked = False
        self.fastwalk_hunt_stop_killed = False
        self.fastwalk_hunt_stop_skipped = False
        self.fastwalk_hunt_route_before_target = False
        self.fastwalk_hunt_preflight_food_attempted = False
        self.fastwalk_water_preflight_step = 0
        self.moria_research = moria_research
        self.moria_depth = moria_depth
        self.gear_catalog = gear_catalog
        self.source_mobile_targets = dict(source_mobile_targets or {})
        self.source_mobile_level_ranges = dict(source_mobile_level_ranges or {})
        self.practice_types_spent = set(practice_types_spent)
        self.stage = "login"
        self.done = False
        self.failure: str | None = None
        self.awaiting_reconnect = False
        self.in_world = False
        self.login_authenticated = False
        self.title_configured = title_configured
        self.description_configured = description_configured
        self.maxed_stats: set[str] = set()
        self.permanent_stats: dict[str, int] = {}
        self.sleep_confirmation_pending = False
        self.stand_confirmation_pending = False
        self.sleep_gear_locked = False
        self.prompt_ready = False
        self.last_command_at: float | None = None
        self.pending_travel_origin: str | None = None
        self.pending_recall_origin: str | None = None
        self.text = ""
        self.last_response = ""
        self.roll_count = 0
        self.course_started = False
        self.course_complete = False
        self.tutorial_abort_step = 0
        self.visited_course_rooms: set[str] = set()
        self.room_query_counts: dict[str, int] = {}
        self.current_room: str | None = None
        self.previous_room: str | None = None
        self.advice_direction: str | None = None
        self.pending_move: str | None = None
        self.loremaster_step = 0
        self.practiced = False
        self.practice_plan: tuple[TrainingChoice, ...] = ()
        self.practice_plan_index = 0
        self.practice_listing_refresh_required = False
        self.known_skills: set[str] = set()
        self.known_skill_levels: dict[str, int] = {}
        self.capability_audit_pending = False
        self.capability_audit_complete = False
        self.pending_practice_choice: TrainingChoice | None = None
        self.rejected_practice_skills = set(rejected_practice_skills)
        self.pending_training_events: list[GameEvent] = []
        self.counterbalance_preparation_required = (
            counterbalance_preparation_required
        )
        self.smithy_counterbalance_step = 0
        self.smithy_counterbalance_keyword: str | None = None
        self.practice_exit_reason = "return to the Mud School entrance"
        self.arena_queried = False
        self.arena_segment_leaving = False
        self.arena_no_viable_targets = False
        self.arena_skipped_outside_safe_band = False
        self.arena_viable_target_seen = False
        self.arena_visited_rooms: set[str] = set()
        self.arena_respawn_due: float | None = None
        self.arena_pending_loot = False
        self.arena_loot_step = 0
        self.combat_active = False
        self.field_combat_started_at: float | None = None
        self.field_combat_progress_target: str | None = None
        self.field_combat_lowest_hp: int | None = None
        self.field_combat_last_progress_at: float | None = None
        self.flee_pending = False
        self.flee_succeeded = False
        self.needs_stand = False
        self.waiting_for_heal = False
        self.blindness_recovery_active = False
        self.health_check_due: float | None = None
        self.resume_recovery_after_resupply = False
        self.waiting_for_move = False
        self.movement_recovery_return_route: tuple[str, ...] = ()
        self.movement_recovery_return_index = 0
        self.movement_recovery_reached_healer = False
        self.room_targets: dict[str, list[str]] = {}
        self.room_target_counts: dict[str, dict[str, int]] = {}
        self.room_target_selectors: dict[str, dict[str, list[str]]] = {}
        self.room_description_target_counts: dict[str, dict[str, int]] = {}
        self.defeated_targets: dict[str, set[str]] = {}
        self.missing_targets: dict[str, set[str]] = {}
        self.active_target: str | None = None
        self.active_target_selector: str | None = None
        self.active_target_level: int | None = None
        self.active_enemy_count: int | None = None
        self.unapproved_field_attacker: str | None = None
        self.awaiting_enemy_assessment = False
        self.pending_loot_rooms: set[str] = set()
        self.cleared_training_rooms: set[str] = set()
        self.post_kill_steps: dict[str, int] = {}
        self.between_round_action_issued = False
        self.between_round_action_ready_at = 0.0
        self.combat_action_target: str | None = None
        self.combat_disarm_attempts = 0
        self.combat_actions_since_disarm = 0
        self.combat_disarm_resolved = False
        self.cleric_combat_heals = 0
        self.backstab_pending_target: str | None = None
        self.backstab_skip_once_target: str | None = None
        self.stun_opener_step: str | None = None
        self.stun_opener_target: str | None = None
        self.stun_opener_selector: str | None = None
        self.stun_opener_weapon_keyword: str | None = None
        self.stun_opener_piercing_keyword: str | None = None
        self.shoot_pending_target: str | None = None
        self.shoot_skip_once_target: str | None = None
        self.chill_touch_unavailable = False
        self.store_step = 0
        self.provisioned = False
        self.saved = False
        self.midgaard_logout_pending = False
        self.midgaard_logout_save_reason = "persist safe Midgaard checkpoint"
        self.midgaard_logout_quit_reason = "safe Midgaard checkpoint complete"
        self.needs_food = resupply_only or emergency_provision_sale
        self.needs_drink = resupply_only
        self.food_unavailable = False
        self.water_unavailable = False
        self.food_attempted = False
        self.drink_attempted = False
        self.food_ordered = False
        self.skin_ordered = False
        self.last_consumption: str | None = None
        self.insufficient_funds = False
        self.city_restock_step = 0
        self.city_rearm_step = 0
        self.city_rearm_role = "primary"
        self.city_rearm_route_index = 0
        self.city_rearm_returning = False
        self.city_rearm_direct_wield_attempted = False
        self.city_rearm_piercing_keyword: str | None = None
        self.city_rearm_capacity_item: str | None = None
        self.city_rearm_capacity_checked = False
        self.city_rearm_borrowing = False
        self.city_rearm_borrow_step = 0
        self.city_rearm_borrow_confirmed = False
        self.city_rearm_borrow_rejected = False
        self.city_rearm_borrow_withdraw_required = False
        self.city_rearm_borrow_withdraw_issued = False
        self.city_rearm_funding_attempted = False
        self.city_outfit_route_index = 0
        self.city_outfit_returning = False
        self.city_outfit_audited = False
        self.city_outfit_plan: list[tuple[str, str]] = []
        self.city_outfit_item_index = 0
        self.city_outfit_item_step = 0
        self.city_outfit_verification_requested = False
        self.city_outfit_initial_empty: set[str] = set()
        self.city_outfit_deferred_categories: set[str] = set()
        self.city_outfit_capacity_relief_attempted = False
        self.purchase_carry_rejected = False
        self.purchase_level_rejected = False
        self.affordable_pies: int | None = None
        self.affordable_pies_ordered = False
        self.pie_order_limit = 6
        self.last_pie_order_quantity: int | None = None
        self.city_restock_capacity_audited = False
        self.city_restock_capacity_relief_attempted = False
        self.city_restock_capacity_relief_pending = False
        self.restock_borrowing = False
        self.restock_borrow_step = 0
        self.restock_borrow_confirmed = False
        self.restock_borrow_rejected = False
        self.restock_borrow_withdraw_required = False
        self.restock_borrow_withdraw_issued = False
        self.restock_borrow_complete = False
        self.emergency_borrowing = False
        self.emergency_borrow_step = 0
        self.emergency_borrow_confirmed = False
        self.emergency_borrow_rejected = False
        self.emergency_borrow_withdraw_required = False
        self.emergency_borrow_withdraw_issued = False
        self.emergency_borrow_complete = False
        self.teacher_clue_requested = False
        self.guildmaster_step = 0
        self.magic_shop_step = 0
        self.magic_shop_purchase_failed = False
        self.flight_borrow_step = 0
        self.flight_borrow_confirmed = False
        self.flight_borrow_rejected = False
        self.flight_borrow_withdraw_required = False
        self.flight_borrow_withdraw_issued = False
        self.flight_borrow_complete = False
        self.magic_shop_capacity_relief_attempted = False
        self.magic_shop_capacity_relief_pending = False
        self.magic_shop_diploma_relief_step = 0
        self.magic_shop_diploma_dropped = False
        self.magic_shop_diploma_recovery_step = 0
        self.magic_shop_tophat_relief_planned = False
        self.magic_shop_tophat_dropped = False
        self.bank_excess_coin_step = 0
        self.sale_plan: list[tuple[str, SafeShop]] = []
        self.sale_index = 0
        self.sale_route_index = 0
        self.sale_phase = "plan"
        self.sale_offer_coins: int | None = None
        self.shop_visibility_rejected = False
        self.completed_sales: list[dict[str, Any]] = []
        self.sale_container_step = 0
        self.sale_identify_plan: list[str] | None = None
        self.sale_identify_index = 0
        self.sale_identify_pending_keyword: str | None = None
        self.sale_identified_values: dict[str, int] = {}
        self.donation_plan: list[str] = []
        self.donation_index = 0
        self.donation_pending_keyword: str | None = None
        self.donation_rejected_keywords: set[str] = set()
        self.cursed_sale_keyword: str | None = None
        self.cursed_sale_shop: SafeShop | None = None
        self.cursed_item_count = 0
        self.curse_recovery_step = "idle"
        self.curse_items_tossed = False
        self.curse_drop_pending = False
        self.curse_borrow_step = 0
        self.curse_borrow_complete = False
        self.fastwalk_recall_started = False
        self.fastwalk_arrival_observed = False
        self.fastwalk_route_preflight_complete = not bool(
            fastwalk_route is not None
            and fastwalk_route.route_preflight_room_vnum
            and fastwalk_route.route_preflight_command
        )
        self.fastwalk_route_preflight_issued = False
        self.fastwalk_route_preflight_hazard_observed = False
        self.fastwalk_returning = False
        self.fastwalk_recovery_ready = False
        self.fastwalk_funding_recovery_attempted = False
        self.fastwalk_outbound_index = 0
        self.fastwalk_return_index = 0
        self.fastwalk_recovery_commands: tuple[str, ...] | None = None
        self.live_maze_context: str | None = None
        self.live_maze_target: str | None = None
        self.live_maze_allowed_rooms: frozenset[str] = frozenset()
        self.live_maze_visited: set[str] = set()
        self.live_maze_attempted: dict[str, set[str]] = {}
        self.live_maze_stack: list[tuple[str, str, str]] = []
        self.live_maze_backtrack_room: str | None = None
        self.live_maze_rebases = 0
        self.live_maze_complete = False
        self.fastwalk_explore_step = 0
        self.fastwalk_explore_distance = 0
        self.fastwalk_explore_look_pending = False
        self.fastwalk_withdrawing = False
        self.fastwalk_return_steps_remaining = 0
        self.fastwalk_attack_started = False
        self.body_part_keyword: str | None = None
        self.body_part_cleanup_step = 0
        self.body_part_eat_rejected = False
        self.disarmed_weapon_keyword: str | None = None
        self.disarm_recovery_step = 0
        self.disarm_capacity_relief_keyword: str | None = None
        self.disarm_capacity_relief_attempted = False
        self.primary_weapon_lost = False
        self.primary_weapon_observed: bool | None = None
        self.fastwalk_pursuit_direction: str | None = None
        self.fastwalk_pursuit_steps = 0
        self.fastwalk_target_absent = False
        self.fastwalk_where_target_absent_observed = False
        self.consider_target: str | None = None
        self.consider_target_selector: str | None = None
        self.consider_viable: bool | None = None
        self.consider_level_offset_ceiling: int | None = None
        self.fastwalk_consider_outcomes: dict[str, bool] = {}
        self.fastwalk_below_band_targets: set[str] = set()
        self.fastwalk_below_band_sightings: set[tuple[str, str]] = {
            (str(room_vnum), str(target).casefold())
            for room_vnum, target in fastwalk_skip_target_sightings
        }
        self.consider_response_pending = False
        self.fastwalk_loot_step = 0
        self.fastwalk_recall_after_loot = False
        self.fastwalk_pouch_audit_pending = False
        self.fastwalk_pouch_audited = False
        self.fastwalk_pouch_attempted: set[str] = set()
        self.fastwalk_shop_visible_action_pending = False
        self.combat_pouch_potions: Counter[str] = Counter()
        self.fastwalk_last_kill_target: str | None = None
        self.fastwalk_abort_reason: str | None = None
        self.fastwalk_unattackable_target: str | None = None
        self.fastwalk_emergency_recall_pending = False
        self.fastwalk_resume_hunt_after_interrupt = False
        self.fastwalk_resume_current_route_after_interrupt = False
        self.fastwalk_intermediate_route_resume_attempts: set[tuple[int, str]] = set()
        self.fastwalk_post_flee_audit_requested = False
        self.fastwalk_post_flee_audit_due: float | None = None
        self.runtime_boundary_requested = False
        self.utility_abort_reason: str | None = None
        self.utility_emergency_recall_pending = False
        self.pending_fastwalk_outbound_move = False
        self.pending_fastwalk_hunt_move = False
        self.return_home_recall_started = False
        self.return_home_recovery_commands: tuple[str, ...] | None = None
        self.return_home_recovery_index = 0
        self.purgatory_recovery_active = False
        self.purgatory_judgement_step = 0
        self.purgatory_gear_restore_step = 0
        self.purgatory_portal_entered = False
        self.purgatory_sleep_started = False
        self.purgatory_recovery_complete = False
        self.moria_seen = False
        self.moria_returning = False
        self.moria_observed_rooms: set[str] = set()
        self.gear_audit_pending = False
        self.gear_audited = False
        self.gear_worn = []
        self.gear_command_queue: list[tuple[str, str]] = []
        self.gear_applied_stance: str | None = None
        self.gear_inventory_signature: tuple[str, ...] = ()
        self.gear_confirmation_required = False
        self.gear_pending_wear_keyword: str | None = None
        self.gear_response_expectation: str | None = None
        self.gear_unusable_keywords: set[str] = set()
        self.gear_prohibited_categories: set[str] = set()
        self.gear_allowed_categories: set[str] | None = None
        self.gear_empty_category_counts: Counter[str] = Counter()
        self.fastwalk_readiness_wear_attempts: Counter[int] = Counter()
        self.fastwalk_darkness_detected = False
        self.emergency_sale_in_progress = False

    def observe_text(self, text: str) -> None:
        cleaned = _ANSI_ESCAPE.sub("", text).replace("\r", "")
        self.last_response = cleaned
        recent = cleaned.casefold()
        self.text = (self.text + cleaned)[-24_000:]
        current_stop = (
            self.fastwalk_hunt_stops[self.fastwalk_hunt_stop_index]
            if self.fastwalk_hunt_stop_index < len(self.fastwalk_hunt_stops)
            else None
        )
        if (
            "you fail to find anyone by that name" in recent
            and current_stop is not None
            and current_stop.abort_if_where_target_absent
            and any(
                action.strip().casefold().startswith("where ")
                for action in current_stop.actions[: self.fastwalk_hunt_action_index]
            )
        ):
            # `where` output can arrive immediately before a prompt, which
            # otherwise overwrites last_response before the hunt planner reads it.
            self.fastwalk_where_target_absent_observed = True
        route_preflight = self.fastwalk_route
        if (
            route_preflight is not None
            and not self.fastwalk_route_preflight_complete
            and not self.fastwalk_route_preflight_hazard_observed
            and "you detect the presence of:" in recent
            and route_preflight.route_preflight_target is not None
            and _text_mentions_target(
                recent,
                route_preflight.route_preflight_target,
            )
        ):
            # A route-level `where` check can be followed by a prompt, so latch
            # the exact source hazard before the planner sees only that prompt.
            self.fastwalk_route_preflight_hazard_observed = True
        for match in _SCORE_STAT.finditer(cleaned):
            stat = match.group("stat").casefold()
            self.permanent_stats[stat] = int(match.group("permanent"))
            if match.group("maxed"):
                self.maxed_stats.add(stat)
            else:
                self.maxed_stats.discard(stat)
        is_consider_response = self.consider_response_pending and _consider_response_matches(
            recent
        )
        if self.gear_response_expectation is not None:
            if _gear_response_matches(self.gear_response_expectation, recent):
                self.gear_response_expectation = None
            elif not _is_stale_gear_ack(recent):
                # An unsolicited hunger tick or similar status message should
                # retain the existing retry behavior rather than waiting for a
                # response that may never arrive.
                self.gear_response_expectation = None
        if is_consider_response:
            self.consider_response_pending = False
        if "skills known:" in recent:
            listing = parse_practice_listing(cleaned)
            self.known_skills.update(listing.known)
            self.known_skill_levels.update(listing.known)
            self.capability_audit_pending = False
            self.capability_audit_complete = True
        if self.pending_practice_choice is not None:
            if "i hope my knowledge helps you" in recent:
                self._resolve_pending_practice("accepted", "trainer confirmed the lesson")
            else:
                rejection = next(
                    (
                        reason
                        for phrase, reason in _PRACTICE_REJECTIONS
                        if phrase in recent
                    ),
                    None,
                )
                if rejection is not None:
                    self._resolve_pending_practice("rejected", rejection)
        if self.vault_pending_lodge_keyword is not None:
            if "you lodge " in recent:
                self.vault_lodged_items.append(self.vault_pending_lodge_keyword)
                self.vault_pending_lodge_keyword = None
            elif any(
                phrase in recent
                for phrase in (
                    "you can't put that much weight into your vault",
                    "you can't fit that many items into your vault",
                )
            ):
                self.vault_rejected_lodge_keyword = (
                    self.vault_pending_lodge_keyword
                )
                self.vault_pending_lodge_keyword = None
                self.vault_storage_rejected = True
        if self.vault_pending_claim_keyword is not None:
            claimed_keyword = self.vault_pending_claim_keyword
            if "you get " in recent and " from your vault." in recent:
                self.vault_claimed_items.append(claimed_keyword)
                if self.vault_wear_claimed_items:
                    self.vault_stow_commands = (
                        self.vault_stow_commands[: self.vault_stow_command_index]
                        + (f"wear {claimed_keyword}",)
                        + self.vault_stow_commands[self.vault_stow_command_index :]
                    )
            self.vault_pending_claim_keyword = None
        if (
            self.vault_capacity_disposal_pending
            and "you donate " in recent
        ):
            self.vault_capacity_disposal_pending = False
            self.vault_storage_rejected = False
            self.vault_rejected_lodge_keyword = None
            self.vault_stow_command_index = len(self.vault_stow_commands)
        if self.donation_pending_keyword is not None:
            if "you do not have that item" in recent:
                self.donation_rejected_keywords.add(
                    self.donation_pending_keyword
                )
                self.donation_pending_keyword = None
            elif "you donate " in recent:
                self.donation_pending_keyword = None
        practice_balances = _practice_balances(cleaned)
        if practice_balances != (None, None):
            self.latest_practice_balances = practice_balances
        folded = self.text.casefold()
        if "you sleep." in recent:
            self.sleep_confirmation_pending = False
        if any(
            phrase in recent
            for phrase in (
                "you wake",
                "you stand up",
                "you are already standing",
                "you are already conscious and alert",
            )
        ):
            self.sleep_confirmation_pending = False
            self.stand_confirmation_pending = False
            self.sleep_gear_locked = False
        if "not while you are fighting" in recent:
            # A second mobile can engage after a kill but before a queued sleep
            # reaches the server. The rejected command never changed posture.
            self.sleep_confirmation_pending = False
            self.sleep_gear_locked = False
            self.waiting_for_heal = False
            self.health_check_due = None
            self.combat_active = True
        if self.consider_target is not None:
            previous_consider_viable = self.consider_viable
            stop = (
                self.fastwalk_hunt_stops[self.fastwalk_hunt_stop_index]
                if self.fastwalk_hunt_stop_index < len(self.fastwalk_hunt_stops)
                else None
            )
            resolved_to_rejected_subject = bool(
                stop is not None
                and any(
                    subject.casefold() in recent
                    for subject in stop.rejected_consider_subjects
                )
            )
            if resolved_to_rejected_subject:
                self.consider_viable = False
                self.consider_level_offset_ceiling = None
            elif any(phrase in recent for phrase in _CONSIDER_VIABLE_FRAGMENTS):
                self.consider_viable = True
                self.consider_level_offset_ceiling = (
                    1 if "the perfect match" in recent else 0
                )
            elif any(phrase in recent for phrase in _CONSIDER_REJECTED_FRAGMENTS):
                self.consider_viable = False
                self.consider_level_offset_ceiling = None
                if any(
                    phrase in recent for phrase in _CONSIDER_BELOW_BAND_FRAGMENTS
                ):
                    self.fastwalk_below_band_targets.add(
                        self.consider_target.casefold()
                    )
                    if self.current_room:
                        self.fastwalk_below_band_sightings.add(
                            (
                                str(self.current_room),
                                self.consider_target.casefold(),
                            )
                        )
            if (
                self.consider_viable is not None
                and self.consider_viable != previous_consider_viable
            ):
                target_key = self.consider_target.casefold()
                previous_outcome = self.fastwalk_consider_outcomes.get(target_key)
                self.fastwalk_consider_outcomes[target_key] = bool(
                    self.consider_viable or previous_outcome
                )
        if self.between_round_action_issued and (
            "you launch a volley of" in recent
            or "you launch a magic missile" in recent
            or "chilling touch" in recent
            or "your punch" in recent
            or "your kick" in recent
            or "you attempt to circle" in recent
            or "your knife toss" in recent
            or "your knife catches" in recent
            or "your disarm attempt" in recent
            or "you disarm " in recent
            or "your opponent is not wielding a weapon" in recent
            or "your spell" in recent
            or "you feel better" in recent
            or re.search(r"<\d+/\d+ hits .*? move \[", recent) is not None
        ):
            self.between_round_action_issued = False
        if re.search(r"\byou\s+disarm\s+", recent) is not None:
            self.combat_disarm_resolved = True
        if any(
            phrase in recent
            for phrase in (
                "your opponent is not wielding a weapon",
                "a powerful enchantment prevents you from disarming",
                "you cannot disarm your opponent's body parts",
                "you don't know how to disarm opponents",
            )
        ):
            self.combat_disarm_resolved = True
        if "don't know any spells of that name" in recent:
            if self.fastwalk_invisibility_pending:
                self.fastwalk_invisibility_unavailable = True
                self.fastwalk_invisibility_pending = False
            else:
                self.chill_touch_unavailable = True
            self.between_round_action_issued = False
        if (
            self.fastwalk_invisibility_pending
            and any(
                phrase in recent
                for phrase in (
                    "you fail to correctly recite the spell",
                    "you fail miserably",
                )
            )
        ):
            self.fastwalk_invisibility_pending = False
        if (
            self.stun_opener_step == "wield_pounding"
            and "you wield " in recent
        ):
            self.stun_opener_step = "stun"
        elif self.stun_opener_step == "stun" and any(
            phrase in recent
            for phrase in (
                "you viciously pound",
                "you attempt to stun",
                "your attempted stun",
                "they are already stunned",
                "you cannot stun a fighting person",
                "you need a weapon that pounds",
                "they aren't here",
                "is too large for you to stun",
                "has no head for you to whack",
                "how can you knock yourself out",
                "not while mounted",
            )
        ):
            self.stun_opener_step = "wield_piercing"
        elif (
            self.stun_opener_step == "wield_piercing"
            and "you wield " in recent
        ):
            self.stun_opener_step = "backstab"
        current_form_rejection = any(
            phrase in recent
            for phrase in (
                "you can't attack them in their current form",
                "you cannot attack them in their current form",
            )
        )
        current_form_target = (
            self.backstab_pending_target
            or self.stun_opener_target
            or self.active_target
            or self.fastwalk_attack_target
        )
        if current_form_rejection and current_form_target is not None:
            # The source safety check can reject a live mobile after a positive
            # consider, for example while the mobile has a non-corporeal affect.
            # Do not feed that target into the ordinary opener fallback loop.
            self.backstab_pending_target = None
            self.stun_opener_step = None
            self.stun_opener_target = None
            self.stun_opener_selector = None
            self.stun_opener_weapon_keyword = None
            self.stun_opener_piercing_keyword = None
            self.combat_active = False
            self.active_target = None
            self.active_target_selector = None
            self.active_enemy_count = 0
            self.between_round_action_issued = False
            self.prompt_ready = True
            if self.fastwalk_route is not None:
                self.fastwalk_unattackable_target = current_form_target
                self.fastwalk_abort_reason = (
                    f"field target {current_form_target!r} was non-corporeal "
                    "and could not be attacked"
                )
                self.fastwalk_target_absent = False
                self.fastwalk_attack_target = None
                self.fastwalk_attack_started = False
                self.fastwalk_hunt_stop_skipped = bool(self.fastwalk_hunt_stops)
                self.fastwalk_returning = True
                self.backstab_skip_once_target = None
            else:
                self.backstab_skip_once_target = current_form_target
        if self.backstab_pending_target is not None and any(
            phrase in recent
            for phrase in (
                "you need to wield a piercing or stabbing weapon",
                "you can't backstab a combatant",
                "is too large for you to backstab",
                "is hurt and suspicious",
                "they aren't here",
                "leave the assassin trade to thieves",
                "how can you sneak up on yourself",
            )
        ):
            self.backstab_skip_once_target = self.backstab_pending_target
            self.backstab_pending_target = None
            self.combat_active = False
            self.prompt_ready = True
        if self.shoot_pending_target is not None and any(
            phrase in recent
            for phrase in (
                "you're too close to shoot",
                "shoot whom",
                "you must have a bow equipped to shoot",
                "you can't shoot a fighting person",
                "your arm is too damaged",
                "you can't shoot at yourself",
            )
        ):
            self.shoot_skip_once_target = self.shoot_pending_target
            self.shoot_pending_target = None
            self.combat_active = False
            self.prompt_ready = True
        if "disarms you" in recent or "your weapon slips from your hand" in recent:
            wielded = next(
                (
                    item
                    for item in self.gear_worn
                    if item_category(item) == "wield"
                ),
                None,
            )
            self.disarmed_weapon_keyword = (
                item_command_keyword(
                    wielded,
                    self.gear_catalog.objects.values()
                    if self.gear_catalog is not None
                    else (),
                )
                if wielded is not None
                else None
            )
            self.disarm_recovery_step = 1
            self.primary_weapon_lost = True
            self.primary_weapon_observed = False
            self.gear_applied_stance = None
        if self.disarm_recovery_step == 2:
            if "you get " in recent:
                self.disarm_recovery_step = 3
            elif any(
                phrase in recent
                for phrase in (
                    "you can't carry that much weight",
                    "you cannot carry that much weight",
                    "you can't carry that many items",
                    "you cannot carry that many items",
                )
            ):
                self.disarm_recovery_step = 4
            elif any(
                phrase in recent
                for phrase in (
                    "you can't get ",
                    "you cannot get ",
                    "you do not see that here",
                    "you don't see that here",
                    "you do not have that item",
                    "you don't have that item",
                )
            ):
                # Do not leave the combat loop waiting for a get response that
                # the game has already rejected. Campaign-level rearm remains
                # responsible for replacing a weapon that is truly gone.
                self.disarm_recovery_step = 0
        profession_prohibits_location = (
            "your profession prohibits wearing anything in that location" in recent
        )
        if (
            self.gear_pending_wear_keyword is not None
            and any(
                phrase in recent
                for phrase in (
                    "you cannot use ",
                    "your profession prohibits wearing anything in that location",
                    "it is too heavy for you to wield",
                )
            )
        ):
            if profession_prohibits_location and self.gear_catalog is not None:
                category = _catalog_category_for_keyword(
                    self.gear_catalog,
                    self.gear_pending_wear_keyword,
                )
                if category is not None:
                    self.gear_prohibited_categories.add(category)
            self.gear_unusable_keywords.add(self.gear_pending_wear_keyword)
            self.gear_pending_wear_keyword = None
            self.gear_command_queue.clear()
            self.gear_audit_pending = False
            self.gear_audited = False
            self.gear_confirmation_required = False
            self.gear_applied_stance = None
            self.gear_inventory_signature = ()
        elif self.gear_pending_wear_keyword is not None and any(
            phrase in recent for phrase in ("you wear ", "you wield ")
        ):
            self.gear_pending_wear_keyword = None
        weapon_acknowledgement = _direct_weapon_slot_acknowledgement(cleaned)
        if weapon_acknowledgement is not None and self.gear_catalog is not None:
            if weapon_acknowledgement[0]:
                acknowledged_weapon = self.gear_catalog.match(
                    weapon_acknowledgement[1] or ""
                )
                if (
                    acknowledged_weapon is not None
                    and item_category(acknowledged_weapon) == "wield"
                ):
                    self.gear_worn = [
                        item
                        for item in self.gear_worn
                        if item_category(item) != "wield"
                    ]
                    self.gear_worn.append(acknowledged_weapon)
            else:
                self.gear_worn = [
                    item
                    for item in self.gear_worn
                    if item_category(item) != "wield"
                ]
        if "you stop using " in recent and "you wield " not in recent:
            # A weapon switch can arrive separately from its replacement's
            # acknowledgement.  Mark the primary absent until that second
            # message (or a fresh equipment audit) confirms the new weapon.
            self.primary_weapon_observed = False
            self.primary_weapon_lost = True
            self.gear_applied_stance = None
        if "you wield " in recent:
            self.primary_weapon_lost = False
            self.primary_weapon_observed = True
            self.disarm_recovery_step = 0
        if "it is pitch black" in recent:
            self.fastwalk_darkness_detected = True
        weapon_slot_seen, weapon_description = _equipment_weapon_slot(recent)
        if weapon_slot_seen:
            self.primary_weapon_observed = weapon_description is not None
            self.primary_weapon_lost = weapon_description is None
        if "you put a purple potion" in recent and "pouch" in recent:
            self.combat_pouch_potions["purple"] += max(
                1,
                recent.count("you put a purple potion"),
            )
        if "you put a black potion" in recent and "pouch" in recent:
            self.combat_pouch_potions["black"] += max(
                1,
                recent.count("you put a black potion"),
            )
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
            self.food_unavailable = False
        if self.city_restock_capacity_relief_pending and (
            "you eat" in recent or "you are full" in recent
        ):
            self.city_restock_capacity_relief_pending = False
        if "you drink" in folded or "do not feel thirsty" in folded:
            self.needs_drink = False
            self.water_unavailable = False
        empty_container_response = re.search(
            r"(?im)^\s*it is empty\.\s*$",
            folded,
        ) is not None
        if any(
            warning in folded
            for warning in (
                "you can't afford",
                "you can't even afford",
                "you do not have enough",
            )
        ):
            self.insufficient_funds = True
            if self.food_ordered and self.needs_food:
                self.food_ordered = False
            if self.skin_ordered and self.needs_drink:
                self.skin_ordered = False
            if self.magic_shop_research and self.magic_shop_buy_fly:
                self.magic_shop_purchase_failed = True
        if self.flight_borrowing:
            if "after borrowing:" in folded:
                self.flight_borrow_confirmed = True
            elif "thank you for your custom" in folded:
                self.flight_borrow_confirmed = True
            elif "if you are only borrowing that much" in folded:
                self.flight_borrow_withdraw_required = True
            elif any(
                phrase in folded
                for phrase in (
                    "your credit limit is",
                    "you must borrow at least",
                    "there is no banker here",
                )
            ):
                self.flight_borrow_rejected = True
        if self.emergency_borrowing:
            if "after borrowing:" in folded:
                self.emergency_borrow_confirmed = True
            elif "thank you for your custom" in folded:
                self.emergency_borrow_confirmed = True
            elif "if you are only borrowing that much" in folded:
                self.emergency_borrow_withdraw_required = True
            elif any(
                phrase in folded
                for phrase in (
                    "your credit limit is",
                    "you must borrow at least",
                    "there is no banker here",
                )
            ):
                self.emergency_borrow_rejected = True
        if self.restock_borrowing:
            if "after borrowing:" in folded:
                self.restock_borrow_confirmed = True
            elif "thank you for your custom" in folded:
                self.restock_borrow_confirmed = True
            elif "if you are only borrowing that much" in folded:
                self.restock_borrow_withdraw_required = True
            elif any(
                phrase in folded
                for phrase in (
                    "your credit limit is",
                    "you must borrow at least",
                    "there is no banker here",
                )
            ):
                self.restock_borrow_rejected = True
        if self.city_rearm_borrowing:
            if "after borrowing:" in recent or "thank you for your custom" in recent:
                self.city_rearm_borrow_confirmed = True
            elif any(
                phrase in recent
                for phrase in (
                    "if you are only borrowing that much",
                    "you have no gold coins to withdraw",
                    "you do not have 5 gold coins to withdraw",
                )
            ):
                self.city_rearm_borrow_withdraw_required = True
            elif any(
                phrase in recent
                for phrase in (
                    "your credit limit is",
                    "you must borrow at least",
                    "there is no banker here",
                )
            ):
                self.city_rearm_borrow_rejected = True
        carry_rejected = any(
            phrase in folded
            for phrase in (
                "you can't carry that much weight",
                "you can't carry that many items",
            )
        )
        if carry_rejected:
            self.purchase_carry_rejected = True
            if (
                not self.city_restock
                and self.food_ordered
                and self.needs_food
                and self.last_pie_order_quantity is not None
            ):
                if self.last_pie_order_quantity <= 1:
                    self.failure = (
                        "no carry capacity remained for one essential pie"
                    )
                else:
                    self.pie_order_limit = self.last_pie_order_quantity - 1
                    self.food_ordered = False
        if "you can't use " in folded and " yet" in folded:
            self.purchase_level_rejected = True
        if self.magic_shop_capacity_relief_pending and (
            "you eat" in recent or "you are full" in recent
        ):
            self.magic_shop_capacity_relief_pending = False
            self.purchase_carry_rejected = False
            self.magic_shop_step = 1
        if (
            self.city_restock
            and carry_rejected
            and self.last_pie_order_quantity is not None
        ):
            if self.last_pie_order_quantity <= 1:
                self.failure = "no carry capacity remained for one essential pie"
            else:
                self.pie_order_limit = self.last_pie_order_quantity - 1
                self.city_restock_step = min(self.city_restock_step, 4)
                self.food_ordered = False
        affordable = _AFFORDABLE_QUANTITY.search(cleaned)
        if affordable is not None:
            self.affordable_pies = int(affordable.group("quantity"))
            self.food_ordered = False
            self.affordable_pies_ordered = False
        offer = _VALUE_OFFER.search(cleaned)
        if offer is not None:
            self.sale_offer_coins = int(offer.group("coins"))
        if (
            self.liquidate_loot
            and self.cursed_sale_keyword is None
            and "you can't let go of it" in recent
            and self.sale_index < len(self.sale_plan)
        ):
            keyword, shop = self.sale_plan[self.sale_index]
            self.cursed_sale_keyword = keyword
            self.cursed_sale_shop = shop
            self.cursed_item_count = sum(
                1 for planned_keyword, _ in self.sale_plan if planned_keyword == keyword
            )
            self.curse_recovery_step = "return"
            self.curse_items_tossed = False
            self.curse_drop_pending = False
            self.curse_borrow_step = 0
            self.curse_borrow_complete = False
            self.sale_route_index = 0
        if (
            "looks uninterested in" in recent
            and self.sale_phase == "sell"
            and self.sale_index < len(self.sale_plan)
        ):
            keyword, _ = self.sale_plan[self.sale_index]
            rejected_count = sum(
                1
                for planned_keyword, _ in self.sale_plan[self.sale_index :]
                if planned_keyword == keyword
            )
            self.donation_plan.extend(
                [keyword]
                * max(0, rejected_count - self.donation_plan.count(keyword))
            )
            self.sale_plan = [
                *self.sale_plan[: self.sale_index + 1],
                *(
                    sale
                    for sale in self.sale_plan[self.sale_index + 1 :]
                    if sale[0] != keyword
                ),
            ]
            self.sale_phase = "inventory"
        completed_sale = _SALE_COMPLETED.search(cleaned)
        if "i don't trade with folks i can't see" in recent:
            self.shop_visibility_rejected = True
            if self.city_restock:
                self.city_restock_step = min(self.city_restock_step, 4)
                self.food_ordered = False
            if self.sale_phase == "inventory":
                self.sale_phase = "sell"
        if (
            self.magic_shop_research
            and self.magic_shop_buy_fly
            and "you do not have that potion" in recent
        ):
            self.magic_shop_purchase_failed = True
        if completed_sale is not None and self.emergency_provision_sale:
            # The emergency branch exists only to fund the next ordinary
            # resupply pass. Once the selected item is sold, let that pass buy
            # food instead of waiting for recovery with the same starvation
            # marker still active.
            self.emergency_provision_sale = False
        if completed_sale is not None and self.emergency_sale_in_progress:
            self.emergency_sale_in_progress = False
            self.gear_audited = False
            self.gear_applied_stance = None
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
        identified_value = _IDENTIFIED_VALUE.search(cleaned)
        if (
            identified_value is not None
            and self.sale_identify_pending_keyword is not None
        ):
            self.sale_identified_values[self.sale_identify_pending_keyword] = int(
                identified_value.group("coins")
            )
            self.sale_identify_pending_keyword = None
        boot_time = _BOOT_TIME.search(cleaned)
        if boot_time is not None:
            self.world_boot_id = " ".join(boot_time.group("boot").split())
        if (
            "you don't have that item" in folded
            or "you can't find it" in folded
            or empty_container_response
        ):
            if self.last_consumption == "food":
                self.needs_food = True
                self.food_unavailable = True
                self.food_ordered = False
            if self.last_consumption == "drink":
                self.needs_drink = True
                self.water_unavailable = True
                self.skin_ordered = False
        target_counts = _room_mobile_target_counts(
            cleaned,
            self.source_mobile_targets,
        )
        target_selectors = _room_mobile_target_selectors(
            cleaned,
            self.source_mobile_targets,
        )
        if self.current_room:
            target_counts = _subtract_target_counts(
                target_counts,
                self.room_description_target_counts.get(self.current_room, {}),
            )
            if target_selectors:
                known_selectors = self.room_target_selectors.setdefault(
                    self.current_room,
                    {},
                )
                for target, selectors in target_selectors.items():
                    known = known_selectors.setdefault(target, [])
                    known.extend(
                        selector for selector in selectors if selector not in known
                    )
        targets = list(target_counts)
        if (
            self.current_room
            and targets
            and not self.combat_active
            and not is_consider_response
        ):
            known = self.room_targets.setdefault(self.current_room, [])
            known.extend(target for target in targets if target not in known)
            self.room_target_counts[self.current_room] = target_counts

        direction = _DIRECTION.search(self.text)
        if direction is not None and "imp" in folded:
            self.advice_direction = direction.group("direction").casefold()
        if "hole in the north wall" in folded:
            self.advice_direction = "north"
        combat_resolved = (
            "is dead" in recent
            or ("you receive" in recent and "experience" in recent)
        )
        if combat_resolved:
            was_in_combat = self.combat_active
            defeated_target = self.active_target or _defeated_mobile(cleaned)
            self.combat_active = False
            if self.current_room and (self.active_target or was_in_combat):
                if self.fastwalk_route is not None:
                    self.fastwalk_last_kill_target = self.active_target
                    if (
                        self.fastwalk_hunt_stops
                        and self.active_target is not None
                        and self.fastwalk_hunt_stop_index
                        < len(self.fastwalk_hunt_stops)
                        and self.fastwalk_hunt_stops[
                            self.fastwalk_hunt_stop_index
                        ].target is not None
                        and _targets_match(
                            self.active_target,
                            self.fastwalk_hunt_stops[
                                self.fastwalk_hunt_stop_index
                            ].target,
                        )
                    ):
                        self.fastwalk_hunt_stop_killed = True
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
                    self._forget_defeated_room_target(
                        self.active_target,
                        self.active_target_selector,
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
            self.active_target_selector = None
            self.active_enemy_count = 0
            self.between_round_action_issued = False
            self.cleric_combat_heals = 0
            self.backstab_pending_target = None
            self.shoot_pending_target = None
            self.consider_target = None
            self.consider_target_selector = None
            self.consider_viable = None
        severed_body_part = _SEVERED_BODY_PART.search(cleaned)
        if severed_body_part is not None:
            self.body_part_keyword = severed_body_part.group("part").casefold()
            self.body_part_cleanup_step = 0
            self.body_part_eat_rejected = False
        if self.body_part_cleanup_step == 2 and any(
            phrase in recent
            for phrase in (
                "you are too full to eat more",
                "that's not edible",
            )
        ):
            self.body_part_eat_rejected = True
        fleeing_mobile = _MOB_LEAVES.search(cleaned)
        target_left_during_consider = (
            fleeing_mobile is not None
            and self.consider_response_pending
            and self.consider_target is not None
            and _targets_match(
                fleeing_mobile.group("target"),
                self.consider_target,
            )
        )
        target_fled_combat = (
            fleeing_mobile is not None
            and self.fastwalk_attack_target is not None
            and self.active_target is not None
            and _targets_match(
                fleeing_mobile.group("target"),
                self.fastwalk_attack_target,
            )
        )
        if target_left_during_consider or target_fled_combat:
            self.combat_active = False
            self.active_target = None
            self.active_target_selector = None
            self.active_enemy_count = 0
            self.between_round_action_issued = False
            self.cleric_combat_heals = 0
            self.shoot_pending_target = None
            self.fastwalk_pursuit_direction = fleeing_mobile.group(
                "direction"
            ).casefold()
            if target_left_during_consider:
                self.consider_response_pending = False
                self.consider_target = None
                self.consider_target_selector = None
                self.consider_viable = None
        attacking_mobile = (
            _MOB_ATTACKS_YOU.search(cleaned)
            or _MOB_DIRECT_ATTACKS_YOU.search(cleaned)
        )
        combat_was_active = self.combat_active
        if not combat_resolved and (
            "you attack " in recent
            or " attacks you" in recent
            or "fighting you" in recent
            or attacking_mobile is not None
        ):
            self.combat_active = True
            self.shoot_pending_target = None
        pending_endpoint_target: str | None = None
        if (
            self.fastwalk_attack_target is None
            and self.fastwalk_route is not None
            and self.fastwalk_outbound_index >= len(self.fastwalk_route.commands)
            and self.fastwalk_hunt_stop_index < len(self.fastwalk_hunt_stops)
        ):
            pending_stop = self.fastwalk_hunt_stops[self.fastwalk_hunt_stop_index]
            if not pending_stop.route:
                pending_endpoint_target = pending_stop.target
        if (
            attacking_mobile is not None
            and self.fastwalk_route is not None
        ):
            attacker = attacking_mobile.group("attacker")
            if attacker.casefold().startswith("your "):
                attacker = ""
            approved_target = self.fastwalk_attack_target or pending_endpoint_target
            if attacker and (
                approved_target is None or not _targets_match(
                attacker, approved_target
                )
            ):
                if (
                    self.active_target is not None
                    and _targets_match(attacker, self.active_target)
                ):
                    pass
                elif combat_was_active or self.fastwalk_attack_started:
                    self.unapproved_field_attacker = attacker
                else:
                    self.active_target = attacker
                    self.active_target_selector = self._target_selector_for(attacker)
            else:
                self.fastwalk_attack_target = approved_target
        if "aren't fighting anyone" in recent:
            self.combat_active = False
            self.active_target = None
            self.active_target_selector = None
            self.active_enemy_count = 0
            self.between_round_action_issued = False
            self.cleric_combat_heals = 0
            self.shoot_pending_target = None
        if "you flee from combat" in recent:
            self.combat_active = False
            self.active_target = None
            self.active_target_selector = None
            self.active_enemy_count = 0
            self.unapproved_field_attacker = None
            self.between_round_action_issued = False
            self.cleric_combat_heals = 0
            self.shoot_pending_target = None
            self.flee_pending = False
            self.flee_succeeded = True
        generic_flee_failure = self.flee_pending and any(
            line.strip().casefold().startswith("you failed!")
            for line in cleaned.splitlines()
        )
        if (
            "you failed to flee" in recent
            or "you couldn't escape" in recent
            or generic_flee_failure
        ):
            self.flee_pending = False
            self.flee_succeeded = False
        if self.pending_recall_origin is not None and any(
            phrase in recent
            for phrase in (
                "not in your current form",
                "too powerful to rely on the gods",
                "you are completely lost",
                "god has forsaken you",
                "your enemy must die",
                "you failed!  you lose",
                "gods will not assist carriers of cursed items",
            )
        ):
            self.pending_recall_origin = None
        if (
            self.pending_recall_origin is not None
            and re.search(
                r"(?m)^\s*The Temple Of Midgaard\s*$",
                cleaned,
                re.IGNORECASE,
            )
        ):
            # DD4 can omit Room.Info after recall. The canonical text room
            # header still proves arrival at Midgaard's recall room.
            self.pending_recall_origin = None
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
            self.active_target_selector = None
            self.active_enemy_count = 0
            self.between_round_action_issued = False
            self.cleric_combat_heals = 0
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
            if self.pending_fastwalk_hunt_move:
                self.fastwalk_hunt_move_index = max(
                    0,
                    self.fastwalk_hunt_move_index - 1,
                )
                self.pending_fastwalk_hunt_move = False
            self.pending_travel_origin = None
        if "you are too exhausted" in folded:
            if self.pending_fastwalk_outbound_move:
                self.fastwalk_outbound_index = max(
                    0,
                    self.fastwalk_outbound_index - 1,
                )
                self.pending_fastwalk_outbound_move = False
            if self.pending_fastwalk_hunt_move:
                self.fastwalk_hunt_move_index = max(
                    0,
                    self.fastwalk_hunt_move_index - 1,
                )
                self.pending_fastwalk_hunt_move = False
            if self.fastwalk_route is not None:
                self.fastwalk_abort_reason = (
                    f"official fastwalk {self.fastwalk_route.name!r} exhausted "
                    "movement before its endpoint"
                )
                self.fastwalk_returning = True
                self.fastwalk_emergency_recall_pending = True
            self.pending_travel_origin = None
            self.waiting_for_move = False
            self.prompt_ready = True
        if "alas, you cannot go that way" in folded:
            if (
                self.fastwalk_route is not None
                and self.pending_fastwalk_outbound_move
                and not self.fastwalk_arrival_observed
            ):
                self.fastwalk_abort_reason = (
                    f"official fastwalk {self.fastwalk_route.name!r} was blocked "
                    "before its endpoint"
                )
                self.fastwalk_returning = True
                self.fastwalk_emergency_recall_pending = True
                self.pending_fastwalk_outbound_move = False
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
                if self.capability_audit_pending:
                    self.capability_audit_pending = False
                    self.capability_audit_complete = True
                if self.pending_practice_choice is not None:
                    self._resolve_pending_practice(
                        "rejected",
                        "trainer returned without confirming the lesson",
                    )
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
                if (
                    self.pending_recall_origin is not None
                    and room
                    and room != self.pending_recall_origin
                ):
                    self.pending_recall_origin = None
                if room and room != self.current_room:
                    if self.body_part_cleanup_step == 0:
                        self._clear_body_part_cleanup()
                    self.previous_room = self.current_room
                    self.current_room = room
                    self.pending_travel_origin = None
                    self.pending_fastwalk_outbound_move = False
                    self.pending_fastwalk_hunt_move = False
                    self.advice_direction = None
                    self.pending_move = None
                if room:
                    description = event.data.get("description")
                    if isinstance(description, str):
                        self.room_description_target_counts[room] = (
                            _training_target_counts(description)
                        )
                    latest_counts = _subtract_target_counts(
                        _room_mobile_target_counts(
                            self.last_response or self.text,
                            self.source_mobile_targets,
                        ),
                        self.room_description_target_counts.get(room, {}),
                    )
                    self.room_targets[room] = list(latest_counts)
                    self.room_target_counts[room] = latest_counts
                    self.room_target_selectors[room] = (
                        _room_mobile_target_selectors(
                            self.last_response or self.text,
                            self.source_mobile_targets,
                        )
                    )
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
                self.active_enemy_count = None
                self.backstab_pending_target = None
                self.shoot_pending_target = None
                target = event.data.get("target", event.data.get("name"))
                if isinstance(target, str) and target.strip():
                    self.active_target = target.strip()
                    self.active_target_selector = self._target_selector_for(
                        self.active_target
                    )
            if event.type == "enemies_changed":
                enemies = _enemy_records(event.data.get("value"))
                self.active_enemy_count = len(enemies)
                if enemies:
                    self.backstab_pending_target = None
                    self.shoot_pending_target = None
                    preferred_targets = (
                        self.active_target,
                        self.fastwalk_attack_target,
                    )
                    enemy = next(
                        (
                            candidate
                            for preferred in preferred_targets
                            if preferred is not None
                            for candidate in enemies
                            if _targets_match(
                                str(candidate.get("name", "")),
                                preferred,
                            )
                        ),
                        enemies[0],
                    )
                    target = enemy.get("name")
                    if isinstance(target, str) and target.strip():
                        self.active_target = target.strip()
                        self.active_target_selector = self._target_selector_for(
                            self.active_target
                        )
                    self.active_target_level = _int_or_none(enemy.get("level"))
                    self.combat_active = True
                    self.awaiting_enemy_assessment = False
                    self.prompt_ready = True
                else:
                    self.active_target_level = None
                    self.combat_active = False
                    self.active_target = None
                    self.active_target_selector = None
                    self.unapproved_field_attacker = None
                    self.between_round_action_issued = False
                    self.cleric_combat_heals = 0
                    self.backstab_pending_target = None
                    self.awaiting_enemy_assessment = False
                    self.prompt_ready = True
            if event.type == "equipment_changed" and self.gear_catalog is not None:
                self.gear_worn = self.gear_catalog.match_many(
                    _equipment_descriptions(event.data.get("value", event.data))
                )
                equipment_text = str(event.data.get("value", event.data)).casefold()
                weapon_slot_seen, weapon_description = _equipment_weapon_slot(
                    equipment_text
                )
                if weapon_slot_seen:
                    self.primary_weapon_observed = weapon_description is not None
                    self.primary_weapon_lost = weapon_description is None
                elif any(
                    item_category(item) == "wield" for item in self.gear_worn
                ):
                    self.primary_weapon_observed = True
                    self.primary_weapon_lost = False
                self.gear_audited = True
                # GMCP reports occupied equipment, but only ``eq all`` reveals
                # the empty locations available to this profession.
                if self.gear_allowed_categories is not None:
                    self.gear_audit_pending = False
            if event.type == "character_died":
                self.return_home = True
                self.purgatory_recovery_active = True
                self.fastwalk_resume_hunt_after_interrupt = False
                self.fastwalk_resume_current_route_after_interrupt = False
                self.combat_active = False
                self.active_target = None
                self.active_target_selector = None
                self.active_target_level = None
                self.active_enemy_count = 0
                self.flee_pending = False
                self.flee_succeeded = False
                self.cleric_combat_heals = 0
                self.prompt_ready = True
                self.utility_abort_reason = (
                    "character died; completed Purgatory recovery is required"
                )
        if self.waiting_for_move:
            movement = state.move or 0
            if (
                _move_ratio(state) >= 0.5
                or (
                    state.room_vnum in _MIDGAARD_HEALER_ROUTES
                    and movement >= 2
                )
            ):
                self.prompt_ready = True
        if self.waiting_for_heal and _health_ratio(state) >= 0.5:
            self.prompt_ready = True
        if (
            self.arena_respawn_due is not None
            and time.monotonic() >= self.arena_respawn_due
            and state.room_vnum in {"3001", "3054"}
        ):
            self.prompt_ready = True

    def next_decision(self, state: CharacterState) -> BotDecision | None:
        if self.done or self.failure:
            return None

        login = self._login_decision()
        if login is not None:
            return login

        if (
            not self.in_world
            and self.login_authenticated
            and self.prompt_ready
            and state.room_name
        ):
            self.in_world = True
            self.stage = "tutorial"

        if self.in_world and self.fastwalk_post_flee_audit_due is not None:
            if time.monotonic() < self.fastwalk_post_flee_audit_due:
                self.prompt_ready = False
                return None
            self.fastwalk_post_flee_audit_due = None
            self.prompt_ready = True

        if not self.in_world or not self.prompt_ready:
            return None
        if (
            self.class_trainer_return_pending
            and state.room_vnum == "3054"
        ):
            self.class_trainer_return_pending = False
        if self.pending_recall_origin is not None:
            if _room_key(state) == self.pending_recall_origin:
                if self.pending_recall_origin == "3001":
                    # Recall is a no-op in the Temple recall room. Treat its
                    # prompt as completion so recovery can continue north.
                    self.pending_recall_origin = None
                else:
                    self.prompt_ready = False
                    return None
            else:
                self.pending_recall_origin = None
        if self.pending_travel_origin is not None:
            if _room_key(state) == self.pending_travel_origin:
                if self.pending_fastwalk_hunt_move:
                    self.pending_fastwalk_hunt_move = False
                    self.pending_travel_origin = None
                    if not (
                        self.combat_active or _enemy_records(state.enemies)
                    ):
                        self.fastwalk_abort_reason = (
                            "field-route movement did not leave its origin room"
                        )
                        self.fastwalk_returning = True
                        return BotDecision(
                            "recall",
                            "return safely after a field-route movement did not complete",
                        )
                self.prompt_ready = False
                if not self.combat_active:
                    return None
            self.pending_travel_origin = None
        if self.sleep_confirmation_pending:
            if not _is_sleeping(state):
                self.prompt_ready = False
                return None
            self.sleep_confirmation_pending = False
        if self.stand_confirmation_pending:
            if _is_sleeping(state):
                self.prompt_ready = False
                return None
            self.stand_confirmation_pending = False
        if self.gear_response_expectation is not None:
            self.prompt_ready = False
            return None
        if self.consider_response_pending:
            self.prompt_ready = False
            return None
        if (
            self.city_restock_capacity_relief_pending
            or self.magic_shop_capacity_relief_pending
        ):
            # Room messages can arrive before DD4 processes the queued eat
            # command. Do not mistake their prompt for the food result.
            self.prompt_ready = False
            return None
        return self._tutorial_decision(state)

    def request_runtime_boundary(self) -> None:
        """Convert the runtime cap into a safe healer-return objective."""
        if self.runtime_boundary_requested:
            return
        self.runtime_boundary_requested = True
        self.return_home = True
        self.fastwalk_resume_hunt_after_interrupt = False
        self.fastwalk_resume_current_route_after_interrupt = False
        self.fastwalk_abort_reason = (
            "segment runtime boundary requested a safe healer return"
        )
        if self.fastwalk_route is not None:
            self.fastwalk_emergency_recall_pending = True

    def after_command(self, decision: BotDecision) -> None:
        self.prompt_ready = False
        self.last_command_at = time.monotonic() if self.in_world else None
        if (
            decision.command == "look"
            and decision.reason
            == "confirm no pursuer entered the post-flee room before recall"
            and self.last_command_at is not None
        ):
            self.fastwalk_post_flee_audit_due = (
                self.last_command_at + _POST_FLEE_AUDIT_GRACE_SECONDS
            )
        if (
            decision.command in _MOVEMENT_COMMANDS
            and decision.command != "recall"
            and self.current_room
        ):
            self.pending_travel_origin = self.current_room
        if decision.command == "recall" and self.current_room:
            self.pending_recall_origin = self.current_room
        if (
            decision.command in _MOVEMENT_COMMANDS
            and decision.reason.startswith("follow official fastwalk")
        ):
            self.pending_fastwalk_outbound_move = True
        if (
            decision.command in _MOVEMENT_COMMANDS
            and (
                decision.reason == "follow the verified field-hunt circuit"
                or decision.reason.startswith(
                    "follow the live exit leading to source room"
                )
            )
        ):
            self.pending_fastwalk_hunt_move = True
        self.text = ""
        self.last_consumption = None
        if decision.command.startswith("eat "):
            self.food_attempted = True
            self.last_consumption = "food"
            self.needs_food = False
            self.resume_recovery_after_resupply = self.waiting_for_heal
        elif decision.command == "drink skin":
            self.drink_attempted = True
            self.last_consumption = "drink"
            self.needs_drink = False
            self.resume_recovery_after_resupply = self.waiting_for_heal
        elif decision.command.startswith("train "):
            self.fastwalk_stat_training_configured = True
            self.selected_training_stat = decision.command.removeprefix("train ")
        elif re.fullmatch(r"buy \d+ pie", decision.command):
            self.food_ordered = True
            self.last_pie_order_quantity = int(decision.command.split()[1])
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
            self.room_target_counts[self.current_room] = {}
            self.room_target_selectors[self.current_room] = {}
        if decision.command == "sleep" and self.waiting_for_heal:
            self.health_check_due = time.monotonic() + _HEALTH_CHECK_WAIT_SECONDS
        if decision.command == "sleep":
            self.sleep_confirmation_pending = True
            self.sleep_gear_locked = True
        if decision.command == "stand":
            self.stand_confirmation_pending = True
        if decision.command == "flee":
            self.flee_pending = True
            self.flee_succeeded = False
        if (
            decision.command.startswith("wear ")
            and decision.reason.startswith("equip ")
        ):
            self.gear_pending_wear_keyword = decision.command.removeprefix(
                "wear "
            ).strip()
        if decision.command in {"equipment", "eq all"}:
            self.gear_response_expectation = "audit"
        elif decision.command != "wear all" and decision.command.startswith(
            ("wear ", "remove ")
        ):
            if decision.reason.startswith("equip "):
                self.gear_response_expectation = "wear"
            elif decision.reason.startswith("remove lower-priority gear"):
                self.gear_response_expectation = "remove"
        if decision.command.startswith("consider "):
            self.consider_response_pending = True
        if decision.command == "quit":
            self.done = True

    def on_connection_closed(self) -> None:
        if self.done:
            return
        self.prompt_ready = False
        self.text = ""
        self.stand_confirmation_pending = False
        if self.in_world and self.fastwalk_route is not None:
            # A reconnect normally places the character back in Midgaard while
            # the local field cursor still points at the old remote room.
            # Force a healer return so stale route state cannot be interpreted
            # as a live exit failure in the new session.
            self.return_home = True
            self.fastwalk_resume_hunt_after_interrupt = False
            self.fastwalk_resume_current_route_after_interrupt = False
            self.fastwalk_abort_reason = (
                "field route interrupted by connection loss; "
                "return home before retrying"
            )
            self.pending_travel_origin = None
            self.pending_recall_origin = None
            self.pending_fastwalk_hunt_move = False
            self.pending_fastwalk_outbound_move = False
        self.room_target_selectors.clear()
        self.active_target_selector = None
        self.consider_target_selector = None
        if self.awaiting_reconnect:
            self.stage = "login"

    def recover_from_stall(
        self,
        state: CharacterState,
        repeated_command: str,
    ) -> BotDecision | None:
        """Abandon stalled work only after arranging a safe exit."""
        self.return_home = True
        self.utility_abort_reason = (
            "progress watchdog stopped after repeating "
            f"{repeated_command!r} without state progress"
        )
        in_purgatory = (
            state.dead
            or (state.area or "").casefold() == "purgatory"
            or state.room_vnum in _PURGATORY_DESTINATION_PATH
            or state.room_vnum == "427"
        )
        if in_purgatory:
            self.purgatory_recovery_active = True
            return None
        if self.combat_active:
            self.utility_emergency_recall_pending = True
            return BotDecision(
                "flee",
                "withdraw from combat after the progress watchdog intervened",
            )
        movement_commands = {
            "north",
            "east",
            "south",
            "west",
            "up",
            "down",
            "recall",
            "flee",
        }
        direct_healer_routes = {
            "3724": "down",
            "3725": "down",
            "3001": "north",
            "3054": "quit",
        }
        repeated_verb = repeated_command.split(maxsplit=1)[0]
        direct_healer_command = direct_healer_routes.get(state.room_vnum or "")
        if (
            direct_healer_command is not None
            and repeated_verb in movement_commands
        ):
            return BotDecision(
                direct_healer_command,
                "route directly to the Midgaard healer after watchdog intervention",
            )
        if (
            "safe" in state.room_flags
            and repeated_verb not in movement_commands
        ):
            self.failure = self.utility_abort_reason
            return None
        self.return_home_recall_started = True
        return BotDecision(
            "recall",
            "recall home after the progress watchdog intervened",
        )

    def _login_decision(self) -> BotDecision | None:
        folded = self.text.casefold()

        if "enter thy name:" in folded:
            self.in_world = False
            self.login_authenticated = False
            self.last_command_at = None
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
            self.login_authenticated = True
            self.stage = "enter_world"
            return BotDecision("", "enter the game after the message of the day")
        if "reconnecting." in folded and self.prompt_ready:
            self.login_authenticated = True
            self.in_world = True
            self.stage = "tutorial"
        if "welcome to the dragons domain" in folded and self.prompt_ready:
            self.login_authenticated = True
            self.in_world = True
            self.stage = "tutorial"
        return None

    def _tutorial_decision(self, state: CharacterState) -> BotDecision | None:
        in_purgatory = (
            (state.area or "").casefold() == "purgatory"
            or state.room_vnum in _PURGATORY_DESTINATION_PATH
            or state.room_vnum == "427"
        )
        if state.dead or in_purgatory:
            self.return_home = True
            self.purgatory_recovery_active = True
            if self.utility_abort_reason is None:
                self.utility_abort_reason = (
                    "character died; completed Purgatory recovery is required"
                )

        now = time.monotonic()
        if self.combat_active:
            if self.field_combat_started_at is None:
                self.field_combat_started_at = now
        else:
            self.field_combat_started_at = None
            self.field_combat_progress_target = None
            self.field_combat_lowest_hp = None
            self.field_combat_last_progress_at = None

        route_hazard = self._active_route_preflight_hazard(state)
        if route_hazard is not None:
            # Source-registered route hazards are never opportunistic targets:
            # they can respawn inside a randomized route after the boundary
            # preflight, so this path must not reuse the waypoint-resume logic.
            self.fastwalk_abort_reason = (
                "unexpected combat interrupted a no-combat field probe"
            )
            self.fastwalk_resume_hunt_after_interrupt = False
            self.fastwalk_resume_current_route_after_interrupt = False
            self.fastwalk_emergency_recall_pending = True
            self.fastwalk_returning = True
            if self.flee_pending:
                self.prompt_ready = False
                return None
            if self.combat_active or _enemy_records(state.enemies):
                return BotDecision(
                    "flee",
                    f"withdraw immediately from source-registered route hazard {route_hazard!r}",
                )
            return BotDecision(
                "recall",
                f"leave the route after source-registered hazard {route_hazard!r} appeared",
            )

        if self.runtime_boundary_requested and self.combat_active:
            return BotDecision(
                "recall",
                "leave active combat before the bounded segment disconnects",
            )

        blindness_recovery = self._blindness_recovery_decision(state)
        if blindness_recovery is not None:
            return blindness_recovery

        if self.spec.title and not self.title_configured:
            self.title_configured = True
            return BotDecision(
                f"title {self.spec.title}",
                "apply the configured test-character identity",
            )

        if (
            self.spec.title
            and self.spec.description
            and not self.description_configured
        ):
            self.description_configured = True
            return BotDecision(
                f"description {self.spec.description}",
                "apply the configured character backstory and personality",
            )

        if (
            _is_sleeping(state)
            and (state.area or "").casefold() == "midgaard"
            and state.room_vnum != "3054"
        ):
            return BotDecision(
                "stand",
                "wake because Midgaard recovery is only permitted at the healer",
            )

        stun_opener = self._stun_opener_decision()
        if stun_opener is not None:
            return stun_opener

        if self.midgaard_logout_pending:
            return self._midgaard_logout_decision(state)

        if (
            self.liquidate_loot
            and self.emergency_provision_sale
            and self.return_home
            and self.utility_abort_reason is not None
            and state.room_vnum == "3054"
            and not self.combat_active
            and not _enemy_records(state.enemies)
        ):
            self.failure = self.utility_abort_reason
            return None

        if (
            self.vault_stow_complete
            and not _is_sleeping(state)
            and not self.city_outfit
            and not self.purgatory_recovery_active
        ):
            gear = self._gear_decision(state)
            if gear is not None:
                return gear

        if _has_inventory_item(state.inventory, "water skin"):
            self.provisioned = True
        if (
            state.level is not None
            and state.level >= 2
            and state.room_vnum == "3725"
        ):
            self.course_started = True
            self.course_complete = True

        if (
            not self.waiting_for_move
            and _move_ratio(state) <= 0.1
            and "safe" in state.room_flags
        ):
            self.waiting_for_move = True

        if self.waiting_for_move:
            movement_recovery = self._movement_recovery_decision(state)
            if movement_recovery is not None:
                return movement_recovery
            if self.waiting_for_move:
                return None

        if self.needs_stand:
            self.needs_stand = False
            return BotDecision("stand", "stand before continuing tutorial actions")

        if self.movement_recovery_return_route:
            if self.movement_recovery_return_index < len(
                self.movement_recovery_return_route
            ):
                command = self.movement_recovery_return_route[
                    self.movement_recovery_return_index
                ]
                self.movement_recovery_return_index += 1
                return BotDecision(
                    command,
                    "return to the route interrupted by healer recovery",
                )
            self.movement_recovery_return_route = ()
            self.movement_recovery_return_index = 0
            self.movement_recovery_reached_healer = False

        room_vnum = state.room_vnum
        room_name = (state.room_name or "").casefold()
        if self.arena_respawn_due is not None:
            if room_vnum == "3737":
                return BotDecision(
                    "enter portal",
                    "vacate Mud School so its depleted arena can reset",
                )
            if room_vnum == "3725":
                return BotDecision(
                    "down",
                    "leave the Mud School area during its arena reset",
                )
            if room_vnum == "3001":
                if time.monotonic() >= self.arena_respawn_due:
                    self.arena_respawn_due = None
                    return BotDecision(
                        "up",
                        "re-enter Mud School after the outside-area reset window",
                    )
                return BotDecision(
                    "north",
                    "wait beside the Midgaard healer while Mud School resets",
                )
            if room_vnum == "3054":
                if time.monotonic() >= self.arena_respawn_due:
                    self.arena_respawn_due = None
                    if _is_sleeping(state):
                        return BotDecision(
                            "stand",
                            "wake after the outside-area arena reset window",
                        )
                    return BotDecision(
                        "south",
                        "return to Mud School after its arena reset window",
                    )
                if _is_sleeping(state):
                    self.prompt_ready = False
                    return None
                return BotDecision(
                    "sleep",
                    "recover beside the healer while Mud School resets",
                )
        if room_vnum == "2" or room_name == "limbo":
            return BotDecision("look", "return from Limbo to the previous room")

        if (
            self.return_home
            and room_vnum == "3054"
            and self.needs_food
            and not _has_inventory_food(state.inventory, self.gear_catalog)
        ):
            self.waiting_for_heal = False
            self.health_check_due = None
            if _is_sleeping(state):
                return BotDecision(
                    "stand",
                    "wake at the healer before checkpointing an unfunded field run",
                )

        if self.fastwalk_defer_provision_resupply:
            funding_recovery_handled, funding_recovery = (
                self._unfunded_funding_recovery_decision(state)
            )
            if funding_recovery_handled:
                return funding_recovery

        if self.waiting_for_heal:
            waiting_room_name = (state.room_name or "").casefold()
            waiting_in_healer_room = (
                state.room_vnum in {"3054", "3721", "3737"}
                or "sanctuary" in waiting_room_name
                or "altar of the temple" in waiting_room_name
                or waiting_room_name == "safety"
            )
            if (
                (self.return_home or self.resupply_only)
                and not waiting_in_healer_room
                and _health_ratio(state) < 0.95
            ):
                self.waiting_for_heal = False
                self.health_check_due = None
            elif (
                self.needs_food
                and _has_inventory_food(state.inventory, self.gear_catalog)
                and not self.food_unavailable
            ) or (
                self.needs_drink
                and _has_inventory_item(state.inventory, "water skin")
                and not self.water_unavailable
            ):
                if _is_sleeping(state):
                    return BotDecision("stand", "wake to address hunger or thirst")
            elif self._recovery_ready_for_objective(state):
                self.waiting_for_heal = False
                self.health_check_due = None
                return BotDecision(
                    "stand",
                    (
                        "resume after source-vetted field recovery"
                        if self.fastwalk_route is not None
                        and not waiting_in_healer_room
                        else "resume after safe-room recovery"
                    ),
                )
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

        if self.flee_succeeded:
            self.flee_succeeded = False
            self.combat_active = False
            self.active_target = None
            self.active_target_selector = None
            if self.utility_emergency_recall_pending:
                self.utility_emergency_recall_pending = False
                self.return_home_recall_started = True
                if state.room_vnum in _PYRAMID_DESERT_MAZE_ROOMS:
                    return self._return_home_decision(state)
                return BotDecision(
                    "recall",
                    "recall immediately after fleeing unexpected utility-run combat",
                )
            if self.fastwalk_emergency_recall_pending:
                if not self.fastwalk_post_flee_audit_requested:
                    self.fastwalk_post_flee_audit_requested = True
                    return BotDecision(
                        "look",
                        "confirm no pursuer entered the post-flee room before recall",
                    )
                return self._fastwalk_emergency_return_decision(state)

        if (
            self.fastwalk_emergency_recall_pending
            and self.fastwalk_post_flee_audit_requested
        ):
            if self.fastwalk_post_flee_audit_due is not None:
                self.prompt_ready = False
                return None
            if self.combat_active or _enemy_records(state.enemies):
                # GMCP can repopulate the enemy list after the flee text. The
                # post-flee audit must keep fleeing until that pursuer is gone;
                # it must never reclassify the same attacker as a productive
                # opportunistic target.
                if self.flee_pending:
                    self.prompt_ready = False
                    return None
                self.combat_active = True
                return BotDecision(
                    "flee",
                    "continue withdrawing while the post-flee pursuer remains",
                )
            return self._fastwalk_emergency_return_decision(state)

        if (
            self.return_home
            and (
                state.room_vnum in _PYRAMID_DESERT_MAZE_ROOMS
                or self.return_home_recovery_commands is not None
            )
            and not _enemy_records(state.enemies)
        ):
            # A reconnect can leave the local combat flag set after the server
            # has already cleared the enemy list. Prioritize the bounded return
            # route so a stale flag cannot create a recall loop.
            self.combat_active = False
            self.active_target = None
            self.active_target_selector = None
            self.active_enemy_count = 0
            self.utility_emergency_recall_pending = False
            home = self._return_home_decision(state)
            if home is not None:
                return home

        if self.combat_active:
            if self.flee_pending:
                self.prompt_ready = False
                return None
            if (
                self.fastwalk_route is not None
                and self.fastwalk_hunt_stops
                and all(stop.consider_only for stop in self.fastwalk_hunt_stops)
            ):
                enemies = _enemy_records(state.enemies)
                below_band_interruption = (
                    bool(enemies)
                    and state.level is not None
                    and all(
                        self._enemy_is_known_below_useful_band(enemy, state)
                        for enemy in enemies
                    )
                )
                if (
                    not below_band_interruption
                    and self.active_target is not None
                    and state.level is not None
                ):
                    current_stop = self.fastwalk_hunt_stops[
                        min(
                            self.fastwalk_hunt_stop_index,
                            len(self.fastwalk_hunt_stops) - 1,
                        )
                    ]
                    below_band_interruption = any(
                        _targets_match(self.active_target, bystander)
                        for bystander in current_stop.trivial_bystanders
                    )
                if (
                    not below_band_interruption
                    and self.active_target is not None
                    and state.level is not None
                ):
                    source_range = self._source_mobile_level_range(
                        self.active_target
                    )
                    below_band_interruption = bool(
                        source_range is not None
                        and source_range[1] <= state.level - 5
                    )
                if below_band_interruption:
                    combat = self._between_round_combat_decision(state)
                    if combat is not None:
                        return combat
                    self.prompt_ready = False
                    return None
                else:
                    resume_mode = self._fastwalk_prepare_interrupt_resume(state)
                    resume_hunt = False
                    if resume_mode is None:
                        self.fastwalk_abort_reason = (
                            "unexpected combat interrupted a no-combat field probe"
                        )
                    elif resume_mode == "next-stop":
                        resume_hunt = True
                    else:
                        resume_hunt = False
                    self.fastwalk_emergency_recall_pending = True
                    return BotDecision(
                        "flee",
                        (
                            "withdraw before resuming the interrupted research waypoint"
                            if resume_mode == "current-route"
                            else (
                                "withdraw before skipping the crowded research endpoint"
                                if resume_hunt
                                else "withdraw before combat can contaminate a no-combat field probe"
                            )
                        ),
                    )
            if (
                self.fastwalk_route is not None
                and self.unapproved_field_attacker is not None
            ):
                if self._field_attacker_is_known_below_band(
                    self.unapproved_field_attacker,
                    state,
                ):
                    self.unapproved_field_attacker = None
                else:
                    resume_mode = self._fastwalk_prepare_interrupt_resume(state)
                    if resume_mode is None:
                        self.fastwalk_abort_reason = (
                            "field combat aborted after unapproved attacker "
                            f"{self.unapproved_field_attacker!r} joined"
                        )
                    self.fastwalk_emergency_recall_pending = True
                    return BotDecision(
                        "flee",
                        "withdraw immediately because an unapproved attacker joined field combat",
                    )
            if (
                self.fastwalk_route is not None
                and self.fastwalk_attack_started
                and self._field_combat_plateau_elapsed(state, now=now) is not None
            ):
                self.fastwalk_abort_reason = (
                    "field combat failed to establish a new low enemy-health "
                    f"mark for {_FIELD_COMBAT_PLATEAU_SECONDS:g} seconds"
                )
                self.fastwalk_emergency_recall_pending = True
                return BotDecision(
                    "flee",
                    "withdraw from field combat after sustained damage plateau",
                )
            if (
                self.fastwalk_route is not None
                and self.fastwalk_attack_started
                and self.field_combat_started_at is not None
                and now - self.field_combat_started_at
                >= _FIELD_COMBAT_TIMEOUT_SECONDS
            ):
                self.fastwalk_abort_reason = (
                    "field combat exceeded the "
                    f"{_FIELD_COMBAT_TIMEOUT_SECONDS:g}-second bounded duration"
                )
                self.fastwalk_emergency_recall_pending = True
                return BotDecision(
                    "flee",
                    "withdraw from field combat after its bounded duration elapsed",
                )
            if self._is_noncombat_utility_run:
                if self.liquidate_loot and self.emergency_provision_sale:
                    self.return_home = True
                    self.utility_emergency_recall_pending = True
                    self.utility_abort_reason = (
                        "unexpected combat interrupted emergency loot liquidation"
                    )
                    return BotDecision(
                        "flee",
                        "withdraw from unexpected combat before emergency loot liquidation",
                    )
                if self._utility_attacker_is_trivial(state):
                    combat = self._between_round_combat_decision(state)
                    if combat is not None:
                        return combat
                    self.prompt_ready = False
                    return None
                if (
                    self.active_target_level is None
                    and not self.awaiting_enemy_assessment
                ):
                    self.awaiting_enemy_assessment = True
                    self.prompt_ready = False
                    return None
                self.return_home = True
                self.utility_emergency_recall_pending = True
                self.utility_abort_reason = (
                    "unexpected combat interrupted a non-combat utility run"
                )
                return BotDecision(
                    "flee",
                    "withdraw from unexpected combat before returning home safely",
                )
            if self.fastwalk_route is not None and self.fastwalk_returning:
                self.fastwalk_emergency_recall_pending = True
                return BotDecision(
                    "flee",
                    "continue withdrawing after fastwalk recall was interrupted",
                )
            if self.return_home and state.room_vnum in _PYRAMID_DESERT_MAZE_ROOMS:
                enemies = _enemy_records(state.enemies)
                if (
                    enemies
                    and state.level is not None
                    and all(
                        self._enemy_is_known_below_useful_band(enemy, state)
                        for enemy in enemies
                    )
                ):
                    combat = self._between_round_combat_decision(state)
                    if combat is not None:
                        return combat
                    self.prompt_ready = False
                    return None
            if (
                self.fastwalk_route is not None
                and not self.fastwalk_attack_started
                and self._midgaard_drunk_interruption_is_trivial(state)
            ):
                timed_out = (
                    self.field_combat_started_at is not None
                    and now - self.field_combat_started_at
                    >= _MIDGAARD_DRUNK_TIMEOUT_SECONDS
                )
                if timed_out or _health_ratio(state) < 0.70:
                    self.fastwalk_abort_reason = (
                        "the source-backed Midgaard drunk interruption exceeded "
                        "its combat bound"
                    )
                    self.fastwalk_emergency_recall_pending = True
                    return BotDecision(
                        "flee",
                        "withdraw after the trivial Midgaard interruption exceeded its bound",
                    )
                combat = self._between_round_combat_decision(state)
                if combat is not None:
                    return combat
                self.prompt_ready = False
                return None
            if self.fastwalk_route is not None and self.fastwalk_attack_started:
                enemies = _enemy_records(state.enemies)
                material_enemies = [
                    enemy
                    for enemy in enemies
                    if not self._enemy_is_known_below_useful_band(enemy, state)
                ]
                unsafe_level = False
                if len(material_enemies) == 1 and state.level is not None:
                    enemy_level = _int_or_none(material_enemies[0].get("level"))
                    unsafe_level = (
                        enemy_level is not None
                        and enemy_level > state.level + 1
                    )
                if len(material_enemies) > 1 or unsafe_level:
                    cause = (
                        f"{len(material_enemies)} useful-band or unknown active enemies"
                        if len(material_enemies) > 1
                        else "the live enemy level fell outside the safe field band"
                    )
                    self.fastwalk_abort_reason = (
                        f"field combat aborted after GMCP reported {cause}"
                    )
                    self.fastwalk_emergency_recall_pending = True
                    if self.flee_pending:
                        self.prompt_ready = False
                        return None
                    return BotDecision(
                        "flee",
                        f"withdraw immediately because GMCP reported {cause}",
                    )
            if self.fastwalk_route is not None and not self.fastwalk_attack_started:
                if (
                    self.fastwalk_attack_target is not None
                    and self.fastwalk_outbound_index >= len(self.fastwalk_route.commands)
                    and _text_mentions_target(self.text, self.fastwalk_attack_target)
                ):
                    self.fastwalk_arrival_observed = True
                    self.fastwalk_attack_started = True
                    self.active_target = self.fastwalk_attack_target
                    self.active_target_selector = self._target_selector_for(
                        self.active_target
                    )
                    spell = self._between_round_combat_decision(state)
                    if spell is not None:
                        return spell
                    self.prompt_ready = False
                    return None
                if (
                    (
                        self.fastwalk_attack_target is not None
                        or self.fastwalk_hunt_stops
                    )
                    and self._opportunistic_fastwalk_attacker_is_viable(state)
                ):
                    self.fastwalk_attack_target = self.active_target
                    self.fastwalk_attack_started = True
                    spell = self._between_round_combat_decision(state)
                    if spell is not None:
                        return spell
                    self.prompt_ready = False
                    return None
                if (
                    (
                        self.fastwalk_attack_target is not None
                        or self.fastwalk_hunt_stops
                    )
                    and self.active_target_level is None
                    and not self.awaiting_enemy_assessment
                    and self.active_target is not None
                ):
                    self.awaiting_enemy_assessment = True
                    self.prompt_ready = False
                    return None
                if (
                    (
                        self.fastwalk_attack_target is not None
                        or self.fastwalk_hunt_stops
                    )
                    and self.active_target_level is None
                ):
                    resume_mode = self._fastwalk_prepare_interrupt_resume(state)
                    if resume_mode is None:
                        self.fastwalk_abort_reason = (
                            "field combat aborted before the attacker could be "
                            "identified and considered"
                        )
                    self.fastwalk_emergency_recall_pending = True
                    return BotDecision(
                        "flee",
                        "withdraw before an unidentified field attacker can bypass consider",
                    )
                resume_mode = self._fastwalk_prepare_interrupt_resume(state)
                if resume_mode is None:
                    self.fastwalk_abort_reason = (
                        "unexpected combat interrupted fastwalk "
                        f"{self.fastwalk_route.name!r} before its objective"
                    )
                self.fastwalk_emergency_recall_pending = True
                if self.flee_pending:
                    self.prompt_ready = False
                    return None
                return BotDecision(
                    "flee",
                    "withdraw from unexpected combat during a bounded fastwalk",
                )
            live_level_excess = self._field_live_level_excess(state)
            if self.fastwalk_route is not None and live_level_excess is not None:
                if self.flee_pending:
                    self.prompt_ready = False
                    return None
                target_level, ceiling = live_level_excess
                self.fastwalk_abort_reason = (
                    f"field target loaded at level {target_level}, above the "
                    f"verified live ceiling of {ceiling}"
                )
                self.fastwalk_emergency_recall_pending = True
                return BotDecision(
                    "flee",
                    "withdraw immediately after the first combat snapshot "
                    "reveals an over-ceiling field target",
                )
            emergency_potion = self._combat_pouch_potion_decision(state)
            if emergency_potion is not None:
                return emergency_potion
            cleric_heal = self._cleric_combat_heal_decision(state)
            if cleric_heal is not None:
                return cleric_heal
            missing_food = (
                self.needs_food
                and not self.fastwalk_defer_provision_resupply
                and (
                    self.food_unavailable
                    or not _has_inventory_food(state.inventory, self.gear_catalog)
                )
            )
            missing_water = (
                self.needs_drink
                and (
                    self.water_unavailable
                    or not _has_inventory_item(state.inventory, "water skin")
                )
            )
            if self.fastwalk_route is not None and (
                missing_food
                or missing_water
                or _health_ratio(state) <= self._field_combat_withdraw_ratio(state)
            ):
                if self.flee_pending:
                    self.prompt_ready = False
                    return None
                causes = []
                if missing_food:
                    causes.append("hunger without usable food")
                if missing_water:
                    causes.append("thirst without usable water")
                withdraw_ratio = self._field_combat_withdraw_ratio(state)
                if _health_ratio(state) <= withdraw_ratio:
                    causes.append(
                        f"health at or below "
                        f"{int(withdraw_ratio * 100)}%"
                    )
                cause = ", ".join(causes)
                self.fastwalk_abort_reason = (
                    f"field combat aborted for safety: {cause}"
                )
                self.fastwalk_emergency_recall_pending = True
                return BotDecision(
                    "flee",
                    f"withdraw from field combat because of {cause}",
                )
            unresolved_food = (
                missing_food if self.fastwalk_route is not None else self.needs_food
            )
            unresolved_water = (
                missing_water if self.fastwalk_route is not None else self.needs_drink
            )
            if unresolved_food or unresolved_water or _health_ratio(state) < 0.25:
                if self.return_home:
                    return BotDecision(
                        "recall",
                        "use emergency recall when reconnecting to trapped combat",
                    )
                return BotDecision("flee", "leave combat before emergency resupply")
            if self.disarm_recovery_step == 1:
                if self.disarmed_weapon_keyword is None:
                    self.disarm_recovery_step = 2
                    return BotDecision(
                        "get all",
                        "recover an unidentified weapon dropped by a combat disarm",
                    )
                self.disarm_recovery_step = 2
                return BotDecision(
                    f"get {self.disarmed_weapon_keyword}",
                    "recover the weapon dropped by a combat disarm",
                )
            if self.disarm_recovery_step == 2:
                self.prompt_ready = False
                return None
            if self.disarm_recovery_step == 4:
                relief = self._disarm_capacity_relief_decision(state)
                if relief is not None:
                    return relief
            if self.disarm_recovery_step == 3:
                self.disarm_recovery_step = 0
                if self.disarmed_weapon_keyword is None and self.gear_catalog is not None:
                    recovered = next(
                        (
                            item
                            for item in self.gear_catalog.match_many_usable(
                                _inventory_descriptions(state.inventory),
                                character_class=self.spec.character_class,
                                subclass=self.spec.subclass,
                            )
                            if item_category(item) == "wield"
                        ),
                        None,
                    )
                    if recovered is not None:
                        self.disarmed_weapon_keyword = item_keyword(recovered)
                if self.disarmed_weapon_keyword is None:
                    self.prompt_ready = False
                    return None
                return BotDecision(
                    f"wield {self.disarmed_weapon_keyword}",
                    "rearm the recovered weapon during combat",
                )
            if self.disarm_recovery_step == 5:
                self.disarm_recovery_step = 2
                command = (
                    f"get {self.disarmed_weapon_keyword}"
                    if self.disarmed_weapon_keyword is not None
                    else "get all"
                )
                return BotDecision(
                    command,
                    "retry the dropped weapon after one bounded capacity-relief action",
                )
            spell = self._between_round_combat_decision(state)
            if spell is not None:
                return spell
            self.prompt_ready = False
            return None

        body_part = self._body_part_cleanup_decision(state)
        if body_part is not None:
            return body_part

        if self.query_world_time and not self.world_time_queried:
            self.world_time_queried = True
            return BotDecision(
                "time",
                "identify the current reboot for dynamic world-state evidence",
            )

        if self.utility_emergency_recall_pending:
            self.utility_emergency_recall_pending = False
            self.return_home_recall_started = True
            return BotDecision(
                "recall",
                "recall immediately after fleeing unexpected utility-run combat",
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

        if (
            self.fastwalk_route is None
            and (state.area or "").casefold() == "mud school"
            and "no_recall" in state.room_flags
        ):
            school_escape = self._course_decision(state)
            if school_escape is not None:
                return school_escape
            if self.failure is not None:
                return None

        if self.city_restock:
            restock = self._city_restock_decision(state)
            if restock is not None:
                return restock
            if self.failure:
                return None
            return self._begin_midgaard_logout(
                state,
                save_reason="persist city food-and-water restock",
                quit_reason="city food-and-water restock complete",
            )

        if self.city_rearm:
            rearm = self._city_rearm_decision(state)
            if rearm is not None:
                return rearm
            if self.failure:
                return None
            return self._begin_midgaard_logout(
                state,
                save_reason="persist the verified primary weapon",
                quit_reason="safe primary-weapon rearm complete",
            )

        if self.city_outfit:
            if not self.vault_stow_complete:
                vault = self._vault_stow_decision(state)
                if vault is not None:
                    return vault
                if self.failure or not self.vault_stow_complete:
                    return None
            outfit = self._city_outfit_decision(state)
            if outfit is not None:
                return outfit
            if self.failure:
                return None
            return self._begin_midgaard_logout(
                state,
                save_reason="persist verified basic equipment",
                quit_reason="safe basic-equipment outfit complete",
            )

        if self.flight_borrowing:
            borrowing = self._flight_borrow_decision(state)
            if borrowing is not None:
                return borrowing
            if self.failure:
                return None
            return self._begin_midgaard_logout(
                state,
                save_reason="persist the bounded flight-funding loan",
                quit_reason="safe flight-funding loan complete",
            )

        returning_fastwalk_at_healer = bool(
            self.fastwalk_route is not None
            and self.fastwalk_returning
            and state.room_vnum == "3054"
        )
        if (
            not self.emergency_provision_sale
            and not returning_fastwalk_at_healer
            and not (
                self.fastwalk_route is not None
                and self.fastwalk_defer_provision_resupply
            )
        ):
            resupply = self._resupply_decision(state)
            if resupply is not None:
                return resupply
            if self.failure:
                return None

        if self.resupply_only and self.food_attempted and self.drink_attempted:
            return self._begin_midgaard_logout(
                state,
                save_reason="persist emergency resupply recovery",
                quit_reason="emergency resupply complete",
            )

        if (
            self.arena_segment_leaving
            and _can_persist_character(state)
            and state.room_vnum == "3054"
        ):
            return self._begin_midgaard_logout(
                state,
                save_reason="persist the bounded Mud School arena checkpoint",
                quit_reason="bounded Mud School arena checkpoint complete",
            )

        arena_completion = self._arena_completion_route_decision(state)
        if arena_completion is not None:
            return arena_completion

        recovery = self._recovery_decision(state)
        if recovery is not None:
            return recovery

        if self.return_home:
            home = self._return_home_decision(state)
            if home is not None:
                return home
            return self._begin_midgaard_logout(
                state,
                save_reason="persist safe recall recovery",
                quit_reason="safe recall recovery complete",
            )

        if self.guildmaster_research:
            research = self._guildmaster_research_decision(state)
            if research is not None:
                return research
            return self._begin_midgaard_logout(
                state,
                save_reason="persist class-trainer route evidence",
                quit_reason="class-trainer route research complete",
            )

        if self.magic_shop_research:
            research = self._magic_shop_research_decision(state)
            if research is not None:
                return research
            return self._begin_midgaard_logout(
                state,
                save_reason="persist Magic Shop stock evidence",
                quit_reason="Magic Shop research complete",
            )

        if self.bank_excess_coins:
            banking = self._bank_excess_coin_decision(state)
            if banking is not None:
                return banking
            return self._begin_midgaard_logout(
                state,
                save_reason="persist excess-currency deposit",
                quit_reason="excess-currency banking complete",
            )

        if self.liquidate_loot:
            sale = self._liquidate_loot_decision(state)
            if sale is not None:
                return sale
            return self._begin_midgaard_logout(
                state,
                save_reason="persist safe Midgaard loot sales",
                quit_reason="safe loot liquidation complete",
            )

        if not self.vault_stow_complete:
            vault = self._vault_stow_decision(state)
            if vault is not None:
                return vault
            if self.failure is not None:
                return None
        if self.vault_only:
            return self._begin_midgaard_logout(
                state,
                save_reason="persist safe Midgaard vault storage",
                quit_reason="safe vault storage complete",
            )

        if self._needs_imminent_stat_training(state):
            training = self._imminent_stat_training_decision(state)
            if training is not None:
                return training

        if (
            self.fastwalk_route is not None
            and not self.fastwalk_world_cache_preflight_complete
        ):
            cache = self._fastwalk_world_cache_decision(state, deposit=False)
            if cache is not None:
                return cache
            if not self.fastwalk_world_cache_preflight_complete:
                return None

        if (
            self.fastwalk_route is not None
            and self.fastwalk_hunt_stops
            and self.login_authenticated
            and not self.capability_audit_complete
        ):
            if self.capability_audit_pending:
                self.prompt_ready = False
                return None
            self.capability_audit_pending = True
            return BotDecision(
                "practice",
                "refresh known combat capabilities before field decisions",
            )

        if self._needs_fastwalk_training(state):
            training = self._fastwalk_training_decision(state)
            if training is not None:
                return training
            if self.failure is not None:
                return None

        if self.fastwalk_route is not None:
            if (
                self.fastwalk_world_cache_post_started
                and not self.fastwalk_world_cache_post_complete
            ):
                cache = self._fastwalk_world_cache_decision(state, deposit=True)
                if cache is not None:
                    return cache
                if not self.fastwalk_world_cache_post_complete:
                    return None
            research = self._fastwalk_research_decision(state)
            if research is not None:
                return research
            if not self.prompt_ready:
                return None
            if self.failure is not None:
                return None
            cache = self._fastwalk_world_cache_decision(state, deposit=True)
            if cache is not None:
                return cache
            if not self.fastwalk_world_cache_post_complete:
                return None
            restore_autoloot = self._restore_fastwalk_autoloot_decision(state)
            if restore_autoloot is not None:
                return restore_autoloot
            return self._begin_midgaard_logout(
                state,
                save_reason="persist official fastwalk route evidence",
                quit_reason="official fastwalk research complete",
            )

        if self.moria_research:
            research = self._moria_research_decision(state)
            if research is not None:
                return research
            return self._begin_midgaard_logout(
                state,
                save_reason="persist Moria approach route evidence",
                quit_reason="Moria approach route research complete",
            )

        if room_vnum == "3724" or room_name == "general supplies":
            if self.provisioned:
                return BotDecision(
                    "down",
                    "leave General Supplies with existing provisions",
                )
            return self._store_decision()

        if _move_ratio(state) <= 0.1:
            self.waiting_for_move = True
            return self._movement_recovery_decision(state)

        if (
            (
                (
                    self.objective_level <= 2
                    or state.room_vnum in {"3054", "3737"}
                )
                and (
                    state.level is not None
                    and state.level >= self.objective_level
                    or (
                        self.arena_segment_leaving
                        and _can_persist_character(state)
                    )
                )
            )
            and self.course_complete
            and self.provisioned
            and self.practiced
        ):
            if not self.saved:
                self.saved = True
                self.stage = "saving"
                return BotDecision(
                    "save",
                    self._arena_segment_completion_reason,
                )
            self.stage = "complete"
            return BotDecision("quit", "starter segment checkpoint complete")

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
            return self._loremaster_decision(state)

        if room_vnum == "3728" or "arena" in room_name:
            if self.login_authenticated and not self.capability_audit_complete:
                if self.capability_audit_pending:
                    self.prompt_ready = False
                    return None
                self.capability_audit_pending = True
                return BotDecision(
                    "practice",
                    "refresh known combat capabilities before arena decisions",
                )
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

    def _gear_decision(self, state: CharacterState) -> BotDecision | None:
        """Apply the right source-backed loadout before the next activity."""
        if (
            self.gear_catalog is None
            or state.dead
            or self.combat_active
            or _is_sleeping(state)
            or self.sleep_gear_locked
            or self.waiting_for_heal
            or self.liquidate_loot
            or self.emergency_sale_in_progress
            or (state.area or "").casefold() == "purgatory"
        ):
            return None

        stance = self._desired_gear_stance(state)
        signature = tuple(
            sorted(
                normalize_item_name(description)
                for description in _inventory_descriptions(state.inventory)
            )
        )
        if self.gear_command_queue:
            command, reason = self.gear_command_queue.pop(0)
            return BotDecision(command, reason)

        if self.gear_audit_pending:
            audited_items = self.gear_catalog.match_equipment_text(self.last_response)
            explicit_audit = _equipment_audit_present(self.last_response)
            self.gear_audit_pending = False
            if audited_items or explicit_audit:
                self.gear_worn = audited_items
                self.gear_audited = True
                self.gear_confirmation_required = False
                allowed_categories = _equipment_slot_categories(self.last_response)
                if allowed_categories:
                    self.gear_allowed_categories = allowed_categories
                    self.gear_empty_category_counts = (
                        _equipment_empty_category_counts(self.last_response)
                    )
            else:
                self.gear_audit_pending = True
                return BotDecision(
                    "eq all",
                    "retry a worn-item audit interrupted by a game status tick",
                )

        if self.gear_confirmation_required:
            self.gear_audit_pending = True
            return BotDecision(
                "eq all",
                f"confirm the applied {stance.replace('_', ' ')} stance",
            )

        if (
            self.gear_applied_stance == stance
            and self.gear_inventory_signature == signature
        ):
            return None

        if not self.gear_audited:
            self.gear_audit_pending = True
            return BotDecision(
                "eq all",
                f"audit worn items before applying the {stance.replace('_', ' ')} stance",
            )

        carried_candidates = self.gear_catalog.match_many_usable(
            _inventory_descriptions(state.inventory),
            character_class=self.spec.character_class,
            subclass=self.spec.subclass,
        )
        if self.gear_allowed_categories is None and carried_candidates:
            self.gear_audit_pending = True
            return BotDecision(
                "eq all",
                "record profession-available wear slots before changing equipment",
            )

        carried = [
            item
            for item in carried_candidates
            if item_keyword(item) not in self.gear_unusable_keywords
            if item_category(item) not in self.gear_prohibited_categories
            if (
                self.gear_allowed_categories is None
                or item_category(item) in self.gear_allowed_categories
            )
        ]
        removals, additions = plan_stance_swaps(
            carried,
            self.gear_worn,
            stance,
            level_gain_priorities=self.spec.effective_level_gain_priorities,
            weapon_preference=self._combat_weapon_preference(),
        )
        stance_label = stance.replace("_", " ")
        self.gear_command_queue = [
            (
                f"remove {item_command_keyword(item, (*carried, *self.gear_worn))}",
                f"remove lower-priority gear for the {stance_label} stance",
            )
            for item in removals
        ] + [
            (
                f"wear {item_command_keyword(item, (*carried, *self.gear_worn))}",
                f"equip {stance_label} gear: {item.short_description}",
            )
            for item in additions
        ]
        if not self.gear_command_queue:
            self.gear_applied_stance = stance
            self.gear_inventory_signature = signature
            return None

        # Confirm the resulting paper doll before considering this stance stable.
        self.gear_applied_stance = stance
        self.gear_inventory_signature = ()
        self.gear_audited = False
        self.gear_confirmation_required = True
        command, reason = self.gear_command_queue.pop(0)
        return BotDecision(command, reason)

    def _desired_gear_stance(self, state: CharacterState) -> str:
        room_name = (state.room_name or "").casefold()
        safe_room = (
            state.room_vnum in {"3054", "3721", "3737"}
            or "sanctuary" in room_name
            or "altar of the temple" in room_name
            or room_name == "safety"
            or "safe" in state.room_flags
        )
        recovery_move_ratio = (
            0.9
            if self.fastwalk_hunt_stops
            and (self.fastwalk_outbound_index == 0 or self.fastwalk_returning)
            else 0.25
            if self.fastwalk_hunt_stops
            else 0.5
        )
        recovery_due = (
            self.waiting_for_heal
            or self.arena_respawn_due is not None
            or (
                safe_room
                and (
                    _health_ratio(state) < 0.95
                    or _mana_ratio(state) < 0.5
                    or _move_ratio(state) < recovery_move_ratio
                )
            )
        )
        if recovery_due:
            return STANCE_RECOVERY
        if _near_level_gain(state):
            return STANCE_PRE_LEVEL
        return STANCE_COMBAT

    def _resupply_decision(self, state: CharacterState) -> BotDecision | None:
        room_vnum = state.room_vnum
        room_name = (state.room_name or "").casefold()
        if self.emergency_borrowing:
            return self._emergency_borrow_decision(state)
        healer_room = (
            room_vnum in {"3054", "3721", "3737"}
            or "sanctuary" in room_name
            or "altar of the temple" in room_name
            or room_name == "safety"
        )
        needs_healer_route = (
            self.resupply_only
            and _health_ratio(state) < 0.95
            and not healer_room
        )
        if not (self.needs_food or self.needs_drink or needs_healer_route):
            return None

        if _is_sleeping(state):
            return BotDecision("stand", "wake before eating or drinking")

        food_keyword = _inventory_food_keyword(
            state.inventory,
            self.gear_catalog,
        )
        if self.needs_food and food_keyword is not None:
            if not self.food_unavailable:
                return BotDecision(
                    f"eat {food_keyword}",
                    "address hunger before further recovery",
                )
        if (
            self.needs_drink
            and _has_inventory_item(state.inventory, "water skin")
            and not self.water_unavailable
        ):
            return BotDecision("drink skin", "address thirst before further recovery")

        if self.resupply_only and healer_room and _health_ratio(state) < 0.95:
            self.waiting_for_heal = True
            return BotDecision(
                "sleep",
                "recover safely before travelling for missing provisions",
            )

        if needs_healer_route:
            healer_routes = {
                "3063": "north",
                "3060": "down",
                "3724": "down",
                "3725": "down",
                "3019": "west",
                "3018": "north",
                "3017": "north",
                "3012": "east",
                "3009": "south",
                "3013": "east",
                "3014": "north",
                "3005": "north",
                "3001": "north",
            }
            direction = healer_routes.get(room_vnum or "")
            if direction is not None:
                return BotDecision(direction, "reach the healer before further recovery")

        if room_vnum == "3724" or room_name == "general supplies":
            if (
                self.shop_visibility_rejected
                or _has_named_affect(state.affects, "invis")
            ):
                self.shop_visibility_rejected = False
                if self.needs_food:
                    self.food_ordered = False
                    self.affordable_pies_ordered = False
                if self.needs_drink:
                    self.skin_ordered = False
                return BotDecision(
                    "vis",
                    "become visible before asking the Quartermaster to trade",
                )
            if self.insufficient_funds:
                if not self.emergency_borrow_complete:
                    self.emergency_borrowing = True
                    return self._emergency_borrow_decision(state)
                self.failure = (
                    "insufficient funds for emergency supplies after the "
                    "bounded bank loan"
                )
                return None
            food_keyword = _inventory_food_keyword(
                state.inventory,
                self.gear_catalog,
            )
            if self.needs_food and food_keyword is not None:
                return BotDecision(
                    f"eat {food_keyword}",
                    "consume newly acquired emergency food before leaving supplies",
                )
            if self.needs_drink and _has_inventory_item(
                state.inventory,
                "water skin",
            ):
                return BotDecision(
                    "drink skin",
                    "drink from the newly acquired water skin before leaving supplies",
                )
            if (
                self.needs_food
                and self.affordable_pies is not None
                and self.affordable_pies > 0
                and not self.affordable_pies_ordered
            ):
                self.affordable_pies_ordered = True
                self.food_ordered = True
                return BotDecision(
                    f"buy {self.affordable_pies} pie",
                    "buy the quantity the Quartermaster says is affordable",
                )
            if self.needs_food and not self.food_ordered:
                return BotDecision(
                    f"buy {self.pie_order_limit} pie",
                    "stock emergency food from the Quartermaster",
                )
            if self.needs_drink and not self.skin_ordered:
                return BotDecision("buy skin", "buy a full buffalo water skin from the Quartermaster")
            return None

        if room_vnum == "3737" or room_name == "safety":
            return BotDecision("enter portal", "leave the arena safety room for supplies")
        if _is_arena_vnum(room_vnum):
            return BotDecision("up", "leave the arena for emergency supplies")
        supply_routes = {
            "3063": "north",
            "3060": "down",
            "3054": "south",
            "3019": "west",
            "3018": "north",
            "3017": "north",
            "3012": "east",
            "3013": "east",
            "3014": "north",
            "3005": "north",
            "3001": "up",
        }
        direction = supply_routes.get(room_vnum or "")
        if direction is not None:
            return BotDecision(direction, "reach Mud School supplies before further recovery")
        if room_vnum == "3725" or "entrance to the mud school" in room_name:
            return BotDecision("up", "visit General Supplies for emergency provisions")
        if room_vnum == "3001" or "temple of midgaard" in room_name:
            return BotDecision("up", "return to the Mud School supplies")
        if room_vnum == "3054" or "altar of the temple" in room_name:
            return BotDecision("south", "return from the Temple toward supplies")
        return None

    def _between_round_combat_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        """Issue one active action while automatic combat rounds continue."""
        now = time.monotonic()
        if (
            not self.active_target
            or self.between_round_action_issued
            or now < self.between_round_action_ready_at
        ):
            return None

        latest_selector = self._target_selector_for(self.active_target)
        if latest_selector is not None:
            self.active_target_selector = latest_selector
        combat_identity = self.active_target_selector or self.active_target
        if self.combat_action_target != combat_identity:
            self.combat_action_target = combat_identity
            self.combat_disarm_attempts = 0
            self.combat_actions_since_disarm = 0
            self.combat_disarm_resolved = False

        target = self.active_target_selector or _target_keyword(self.active_target)
        has_wielded_weapon = (
            self.primary_weapon_observed is True
            or any(item_category(item) == "wield" for item in self.gear_worn)
        )
        disarm_available = (
            "disarm" in self.known_skills
            and has_wielded_weapon
            and not self.combat_disarm_resolved
        )
        if disarm_available and (
            self.combat_disarm_attempts == 0
            or self.combat_actions_since_disarm >= 1
        ):
            self.combat_disarm_attempts += 1
            self.combat_actions_since_disarm = 0
            self.between_round_action_issued = True
            self.between_round_action_ready_at = (
                now + _COMBAT_ACTION_COOLDOWN_SECONDS
            )
            return BotDecision(
                f"disarm {target}",
                "reduce the armed opponent's damage and disarm pressure before "
                "the next recurring damage action",
            )

        active_command: str | None = None
        active_reason: str | None = None
        if (
            "circle" in self.known_skills
            and any(
                item_category(item) == "wield" and is_piercing_weapon(item)
                for item in self.gear_worn
            )
        ):
            active_command = f"circle {target}"
            active_reason = (
                "repeat the source-verified circle attack between automatic "
                "weapon rounds"
            )
        elif "knife toss" in self.known_skills:
            active_command = f"knife {target}"
            active_reason = (
                "repeat the source-verified level-scaled knife toss between "
                "automatic rounds without consuming carried ammunition"
            )
        elif "punch" in self.known_skills:
            active_command = "punch"
            active_reason = (
                "repeat the source-verified punch attack while automatic "
                "unarmed combat rounds continue"
            )
        elif "kick" in self.known_skills:
            active_command = "kick"
            active_reason = "repeat kick damage between automatic weapon rounds"

        if active_command is not None and active_reason is not None:
            self.combat_actions_since_disarm += 1
            self.between_round_action_issued = True
            self.between_round_action_ready_at = (
                now + _COMBAT_ACTION_COOLDOWN_SECONDS
            )
            return BotDecision(active_command, active_reason)
        if _mana_ratio(state) < 0.15:
            return self._repeat_disarm_without_damage_action(
                now,
                target,
                disarm_available,
            )
        class_spells = {
            "mage": ("chill touch", "magic missile"),
            "cleric": ("cause critical", "cause serious", "cause light"),
            "psionic": ("psychic crush", "mind thrust"),
        }
        spells = class_spells.get(self.spec.character_class)
        if spells is None:
            return self._repeat_disarm_without_damage_action(
                now,
                target,
                disarm_available,
            )
        spell = next(
            (candidate for candidate in spells if candidate in self.known_skills),
            spells[-1],
        )
        if spell == "chill touch" and self.chill_touch_unavailable:
            spell = "magic missile"
        self.combat_actions_since_disarm += 1
        self.between_round_action_issued = True
        self.between_round_action_ready_at = (
            now + _COMBAT_ACTION_COOLDOWN_SECONDS
        )
        return BotDecision(
            f"cast '{spell}' {target}",
            f"use the strongest known {self.spec.character_class} combat spell, "
            f"{spell}, against {self.active_target}",
        )

    def _repeat_disarm_without_damage_action(
        self,
        now: float,
        target: str,
        disarm_available: bool,
    ) -> BotDecision | None:
        if not disarm_available:
            return None
        self.combat_disarm_attempts += 1
        self.between_round_action_issued = True
        self.between_round_action_ready_at = (
            now + _COMBAT_ACTION_COOLDOWN_SECONDS
        )
        return BotDecision(
            f"disarm {target}",
            "retry the source-verified control action because no other active "
            "between-round attack is currently learned",
        )

    def _disarm_capacity_relief_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        """Free capacity once before retrying a weapon recovery."""
        if self.disarm_capacity_relief_attempted:
            self.disarm_recovery_step = 0
            return None
        self.disarm_capacity_relief_attempted = True
        keyword = _sellable_inventory_keyword(
            state.inventory,
            self.gear_catalog,
            worn_descriptions=tuple(item.short_description for item in self.gear_worn),
        )
        if keyword is None:
            self.disarm_recovery_step = 0
            return None
        self.disarm_capacity_relief_keyword = keyword
        self.disarm_recovery_step = 5
        return BotDecision(
            f"sacrifice {keyword}",
            "free carrying capacity for the disarmed weapon using one "
            "source-matched expendable item",
        )

    def _cleric_combat_heal_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        """Use a bounded self-heal before the field withdrawal threshold."""
        if (
            self.spec.character_class != "cleric"
            or not self.active_target
            or self.between_round_action_issued
            or _health_ratio(state) > _CLERIC_COMBAT_HEAL_RATIO
            or self.cleric_combat_heals >= _CLERIC_COMBAT_HEAL_LIMIT
            or state.mana is None
            or state.max_mana in (None, 0)
        ):
            return None
        healing_spells = (
            ("heal", 50),
            ("cure critical", 20),
            ("cure serious", 15),
            ("cure light", 10),
        )
        available = next(
            (
                (spell, mana_cost)
                for spell, mana_cost in healing_spells
                if spell in self.known_skills
            ),
            None,
        )
        if available is None:
            return None
        spell, mana_cost = available
        mana_reserve = max(
            20,
            int(state.max_mana * _CLERIC_COMBAT_HEAL_MANA_RESERVE_RATIO),
        )
        if state.mana - mana_cost < mana_reserve:
            return None
        self.cleric_combat_heals += 1
        self.between_round_action_issued = True
        self.between_round_action_ready_at = (
            time.monotonic() + _COMBAT_ACTION_COOLDOWN_SECONDS
        )
        return BotDecision(
            f"cast '{spell}'",
            f"use bounded Cleric self-heal {self.cleric_combat_heals} of "
            f"{_CLERIC_COMBAT_HEAL_LIMIT} before crossing the withdrawal threshold",
        )

    def _combat_opener_decision(
        self,
        target: str,
        reason: str,
        *,
        allow_backstab: bool = True,
        command_keyword: str | None = None,
        state: CharacterState | None = None,
    ) -> BotDecision:
        """Choose a source-valid opening attack for the current loadout."""
        exact_selector = self._target_selector_for(target) or self.active_target_selector
        if exact_selector is not None:
            self.active_target_selector = exact_selector
        keyword = (
            exact_selector
            or command_keyword
            or _target_keyword(target)
        )
        skip_backstab = self.backstab_skip_once_target == target
        if skip_backstab:
            self.backstab_skip_once_target = None
        skip_shoot = self.shoot_skip_once_target == target
        if skip_shoot:
            self.shoot_skip_once_target = None
        if (
            state is not None
            and allow_backstab
            and self.spec.character_class.casefold() == "thief"
            and "backstab" in self.known_skills
            and "stun" in self.known_skills
        ):
            weapons = self._state_weapons(state)
            pounding = self._best_weapon(weapons, is_blunt_weapon)
            piercing = self._best_weapon(weapons, is_piercing_weapon)
            if pounding is not None and piercing is not None:
                self.stun_opener_target = target
                self.stun_opener_selector = keyword
                self.stun_opener_weapon_keyword = item_command_keyword(
                    pounding,
                    weapons,
                )
                self.stun_opener_piercing_keyword = item_command_keyword(
                    piercing,
                    weapons,
                )
                self.combat_active = False
                current = next(
                    (
                        item
                        for item in self.gear_worn
                        if item_category(item) == "wield"
                    ),
                    None,
                )
                self.stun_opener_step = (
                    "stun" if current is not None and current.vnum == pounding.vnum
                    else "wield_pounding"
                )
                return self._stun_opener_decision() or BotDecision(
                    f"backstab {keyword}",
                    "begin combat with the piercing weapon after the stun attempt",
                )
        if (
            not skip_shoot
            and self.spec.character_class == "ranger"
            and "shoot" in self.known_skills
            and self._ranger_equipped_bow() is not None
        ):
            self.shoot_pending_target = target
            return BotDecision(
                f"shoot {keyword}",
                f"open against {target} with the source-verified bow volley "
                "before melee begins",
            )
        if (
            allow_backstab
            and not skip_backstab
            and self.spec.character_class == "thief"
            and "backstab" in self.known_skills
            and any(
                item_category(item) == "wield" and is_piercing_weapon(item)
                for item in self.gear_worn
            )
        ):
            self.backstab_pending_target = target
            return BotDecision(
                f"backstab {keyword}",
                f"open against {target} with source-verified backstab damage "
                "while wielding a piercing weapon",
            )
        return BotDecision(f"kill {keyword}", reason)

    def _needs_fastwalk_training(self, state: CharacterState) -> bool:
        if not (
            self.fastwalk_route is not None
            and self.fastwalk_train_before_departure
            and not self.fastwalk_returning
        ):
            return False
        physical, intellectual = self.latest_practice_balances
        balances = {
            "physical": physical,
            "intellectual": intellectual,
        }
        useful_types = self._useful_practice_types(state)
        has_unspent_practice = any(
            practice_type in useful_types
            and practice_type not in self.practice_types_spent
            and (balance is None or balance > 0)
            for practice_type, balance in balances.items()
        )
        critical_unlock = self._critical_damage_unlock(state)
        has_critical_unlock_budget = bool(
            critical_unlock is not None
            and any(balance is None or balance > 0 for balance in balances.values())
        )
        preferred_stat = self._preferred_training_stat(state)
        needs_stat_selection = bool(
            preferred_stat is not None
            and preferred_stat != self.selected_training_stat
            and not self.fastwalk_stat_training_configured
        )
        needs_smithy_preparation = bool(
            self.spec.character_class.casefold() == "smithy"
            and self.counterbalance_preparation_required
        )
        return bool(
            needs_stat_selection
            or needs_smithy_preparation
            or (
                not self.practiced
                and (has_unspent_practice or has_critical_unlock_budget)
            )
        )

    def _needs_imminent_stat_training(self, state: CharacterState) -> bool:
        return bool(
            self.fastwalk_route is None
            and _near_level_gain(state)
            and not self.fastwalk_stat_training_configured
            and self._preferred_training_stat(state) is not None
            and self._preferred_training_stat(state) != self.selected_training_stat
        )

    def _imminent_stat_training_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        if _is_sleeping(state):
            return BotDecision("stand", "wake before selecting the next level stat")
        stat = self._preferred_training_stat(state)
        if stat is None or stat == self.selected_training_stat:
            self.fastwalk_stat_training_configured = True
            return None
        room_vnum = state.room_vnum or ""
        room_name = (state.room_name or "").casefold()
        if room_vnum == "3726" or "loremaster" in room_name:
            return BotDecision(
                f"train {stat}",
                "select the source-backed stat focus before an imminent level",
            )
        if room_vnum == "3737" or room_name == "safety":
            return BotDecision(
                "enter portal",
                "leave arena Safety before selecting the next level stat",
            )
        if _is_arena_vnum(room_vnum):
            return BotDecision(
                "up",
                "leave the arena before selecting the next level stat",
            )
        routes = {
            "3054": "south",
            "3001": "up",
            "3724": "down",
            "3725": "east",
        }
        direction = routes.get(room_vnum)
        if direction is not None:
            return BotDecision(
                direction,
                "visit the Loremaster before an imminent level",
            )
        self.failure = (
            "no verified route to the Loremaster before an imminent level from "
            f"{state.room_name!r} ({state.room_vnum})"
        )
        return None

    def _training_excluded_skills(self) -> set[str]:
        excluded = set(self.rejected_practice_skills)
        if (
            self.spec.character_class.casefold() == "smithy"
            and self._smithy_equipped_weapon() is None
        ):
            excluded.update({"weaponsmithing", "counterbalance"})
        if (
            self.spec.character_class.casefold() == "ranger"
            and self._ranger_equipped_bow() is None
        ):
            excluded.update({"archery knowledge", "shoot"})
        return excluded

    def _useful_practice_types(self, state: CharacterState) -> set[str]:
        excluded = self._training_excluded_skills()
        return {
            priority.practice_type
            for priority in training_priorities_for(
                self.spec.character_class,
                subclass=self._active_training_subclass(state),
            )
            if priority.automated and priority.skill not in excluded
        }

    def _critical_damage_unlock(
        self,
        state: CharacterState,
        listing: Any | None = None,
    ) -> str | None:
        """Return the earliest reachable missing damage or control capability."""
        if (state.level or 0) < 10:
            return None
        balances = {
            "physical": (
                listing.physical_practices
                if listing is not None
                else self.latest_practice_balances[0]
            ),
            "intellectual": (
                listing.intellectual_practices
                if listing is not None
                else self.latest_practice_balances[1]
            ),
        }
        priorities = training_priorities_for(
            self.spec.character_class,
            subclass=self._active_training_subclass(state),
        )
        pending_trainable_gateway = False
        blocked_gateway = False
        for priority in priorities:
            if (
                priority.skill in self.rejected_practice_skills
                and self.known_skill_levels.get(priority.skill, -1)
                < priority.target_percent
            ):
                blocked_gateway = True
            if (
                listing is not None
                and priority.skill in listing.trainable
                and listing.trainable[priority.skill] < priority.target_percent
            ):
                balance = balances.get(priority.practice_type)
                if balance is None or balance > 0:
                    pending_trainable_gateway = True
                else:
                    blocked_gateway = True
            if (
                priority.automated
                and priority.utility == "damage"
                and priority.skill not in self.known_skills
                and (
                    priority.minimum_level is None
                    or (state.level or 0) >= priority.minimum_level
                )
            ):
                if blocked_gateway:
                    pending_trainable_gateway = False
                    blocked_gateway = False
                    continue
                if (
                    listing is None
                    or priority.skill in listing.trainable
                    or pending_trainable_gateway
                ):
                    return priority.skill
                pending_trainable_gateway = False
                blocked_gateway = False
                continue
            if (
                priority.automated
                and priority.utility == "control"
                and priority.skill not in self.known_skills
                and (
                    priority.minimum_level is None
                    or (state.level or 0) >= priority.minimum_level
                )
            ):
                if blocked_gateway:
                    pending_trainable_gateway = False
                    blocked_gateway = False
                    continue
                if (
                    listing is None
                    or priority.skill in listing.trainable
                    or pending_trainable_gateway
                ):
                    return priority.skill
                pending_trainable_gateway = False
                blocked_gateway = False
                continue
            if priority.utility in {"damage", "control"}:
                pending_trainable_gateway = False
                blocked_gateway = False
        if listing is not None:
            return next(
                (
                    priority.skill
                    for priority in priorities
                    if (
                        priority.automated
                        and priority.utility == "damage"
                        and priority.skill in listing.trainable
                        and listing.trainable[priority.skill]
                        < priority.target_percent
                        and (
                            balances.get(priority.practice_type) is None
                            or balances[priority.practice_type] > 0
                        )
                    )
                ),
                None,
            )
        return None

    def _training_practice_type_exclusions(
        self,
        state: CharacterState,
    ) -> frozenset[str]:
        if self._critical_damage_unlock(state) is not None:
            return frozenset()
        return frozenset(self.practice_types_spent)

    @staticmethod
    def _active_training_subclass(state: CharacterState) -> str | None:
        if (state.level or 0) < 30:
            return None
        subclass = (state.subclass or "").strip()
        return subclass if subclass.casefold() not in {"", "none"} else None

    def _smithy_equipped_weapon(self) -> ObjectSource | None:
        return next(
            (
                item
                for item in self.gear_worn
                if item_category(item) == "wield"
            ),
            None,
        )

    def _combat_weapon_preference(self) -> str | None:
        """Select the source-backed weapon type required by the opener."""
        if (
            "backstab" in self.known_skills
            or self.spec.character_class.casefold() == "thief"
        ):
            return "piercing"
        return None

    def _wielded_weapon(self) -> ObjectSource | None:
        return next(
            (
                item
                for item in self.gear_worn
                if item_category(item) == "wield"
            ),
            None,
        )

    def _preferred_primary_weapon(
        self,
        state: CharacterState,
    ) -> ObjectSource | None:
        weapons = self._state_weapons(state)
        preference = self._combat_weapon_preference()
        if preference == "piercing":
            return self._best_weapon(weapons, is_piercing_weapon)
        return self._best_weapon(weapons, lambda _item: True)

    def _preferred_pounding_weapon(
        self,
        state: CharacterState,
    ) -> ObjectSource | None:
        """Return the best source-matched blunt weapon for ``stun``."""
        return self._best_weapon(
            self._state_weapons(state),
            is_blunt_weapon,
        )

    def _primary_weapon_satisfies_preference(
        self,
        weapon: ObjectSource | None,
    ) -> bool:
        if weapon is None:
            return False
        preference = self._combat_weapon_preference()
        return preference is None or (
            preference == "piercing" and is_piercing_weapon(weapon)
        ) or (
            preference == "blunt" and is_blunt_weapon(weapon)
        )

    def _state_weapons(self, state: CharacterState) -> list[ObjectSource]:
        items = list(self.gear_worn)
        if self.gear_catalog is None:
            return items
        items.extend(
            item
            for item in self.gear_catalog.match_many_usable(
                _inventory_descriptions(state.inventory),
                character_class=self.spec.character_class,
                subclass=self.spec.subclass,
            )
            if item_category(item) == "wield"
        )
        return list({item.vnum: item for item in items}.values())

    @staticmethod
    def _best_weapon(
        weapons: list[ObjectSource],
        predicate: Callable[[ObjectSource], bool],
    ) -> ObjectSource | None:
        candidates = [
            item
            for item in weapons
            if item_category(item) == "wield" and predicate(item)
        ]
        return max(
            candidates,
            key=lambda item: stance_score(item, STANCE_COMBAT),
            default=None,
        )

    def _stun_opener_decision(self) -> BotDecision | None:
        if self.stun_opener_step is None or self.stun_opener_target is None:
            return None
        target = self.stun_opener_target
        keyword = self.stun_opener_selector or _target_keyword(target)
        if self.stun_opener_step == "wield_pounding":
            return BotDecision(
                f"wield {self.stun_opener_weapon_keyword}",
                "arm the source-verified pounding weapon before attempting stun",
            )
        if self.stun_opener_step == "stun":
            return BotDecision(
                f"stun {keyword}",
                "attempt the source-verified stun opener before backstab",
            )
        if self.stun_opener_step == "wield_piercing":
            return BotDecision(
                f"wield {self.stun_opener_piercing_keyword}",
                "switch to the source-verified piercing weapon after stun",
            )
        if self.stun_opener_step == "backstab":
            self.stun_opener_step = None
            self.stun_opener_target = None
            self.stun_opener_selector = None
            self.stun_opener_weapon_keyword = None
            self.stun_opener_piercing_keyword = None
            self.combat_active = True
            self.backstab_pending_target = target
            return BotDecision(
                f"backstab {keyword}",
                "begin combat with the piercing weapon after the stun attempt",
            )
        return None

    def _ranger_equipped_bow(self) -> ObjectSource | None:
        return next(
            (
                item
                for item in self.gear_worn
                if item_category(item) == "ranged_weapon" and is_bow(item)
            ),
            None,
        )

    def _level_ten_class_trainer(
        self,
        state: CharacterState,
    ) -> _ClassTrainerRoute | None:
        if (state.level or 0) < 10:
            return None
        character_class = self.spec.character_class.casefold()
        advanced = _ADVANCED_CLASS_TRAINERS.get(character_class)
        if advanced is not None and (state.level or 0) >= advanced.minimum_level:
            return advanced
        return _CLASS_TRAINERS.get(character_class)

    def _class_trainer_present(
        self,
        state: CharacterState,
        trainer: _ClassTrainerRoute,
    ) -> bool:
        """Recognize a wandering teacher from its source-backed room line."""
        room_vnum = state.room_vnum or ""
        return any(
            _targets_match(target, trainer.keyword)
            for target in self.room_targets.get(room_vnum, ())
        )

    def _fastwalk_training_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        self.fastwalk_training_started = True
        if _is_sleeping(state):
            return BotDecision("stand", "wake before visiting the class trainer")
        stat = self._preferred_training_stat(state)
        if (
            stat is not None
            and stat != self.selected_training_stat
            and not self.fastwalk_stat_training_configured
        ):
            reason = (
                "select constitution for the next stat advance to improve "
                "hitpoint growth and survivability"
                if stat == "con"
                else "select strength to relieve measured carrying-capacity pressure"
                if stat == "str"
                else "select the class development stat for the next stat advance"
            )
            return BotDecision(f"train {stat}", reason)
        if stat is None or stat == self.selected_training_stat:
            self.fastwalk_stat_training_configured = True
        room_vnum = state.room_vnum or ""
        room_name = (state.room_name or "").casefold()
        class_trainer = self._level_ten_class_trainer(state)
        if (
            room_vnum == "3726"
            or "loremaster" in room_name
            or (
                class_trainer is not None
                and (
                    room_vnum == class_trainer.destination_vnum
                    or self._class_trainer_present(state, class_trainer)
                )
            )
        ):
            return self._loremaster_decision(state)
        physical, intellectual = self.latest_practice_balances
        if physical is None or intellectual is None:
            if self.fastwalk_practice_audit_attempts >= 3:
                self.failure = (
                    "score did not report the practice balance before field departure"
                )
                return None
            self.fastwalk_practice_audit_requested = True
            self.fastwalk_practice_audit_attempts += 1
            return BotDecision(
                "score",
                (
                    "audit class-relevant practices before field departure"
                    if self.fastwalk_practice_audit_attempts == 1
                    else "retry the practice audit after interleaved room output"
                ),
            )

        available = {
            "physical": physical,
            "intellectual": intellectual,
        }
        useful_types = self._useful_practice_types(state)
        critical_unlock = self._critical_damage_unlock(state)
        needs_smithy_preparation = bool(
            self.spec.character_class.casefold() == "smithy"
            and self.counterbalance_preparation_required
        )
        if not needs_smithy_preparation and not any(
            balance > 0
            and practice_type in useful_types
            and (
                critical_unlock is not None
                or practice_type not in self.practice_types_spent
            )
            for practice_type, balance in available.items()
        ):
            self.practiced = True
            return None
        routes = {
            "3019": "west",
            "3018": "north",
            "3017": "north",
            "3012": "east",
            "3013": "east",
            "3014": "north",
            "3005": "north",
            "3001": "up",
            "3725": "east",
            "3054": "south",
            "3724": "down",
        }
        if class_trainer is not None:
            routes = {
                "3054": "south",
                **class_trainer.outbound,
            }
        direction = routes.get(room_vnum)
        if direction is not None:
            return BotDecision(
                direction,
                (
                    f"visit the level-{class_trainer.minimum_level} "
                    f"{self.spec.character_class} trainer "
                    "for the class-aware field practice plan"
                    if class_trainer is not None
                    else "visit the Loremaster for the level-aware field practice plan"
                ),
            )
        destination = (
            f"the level-{class_trainer.minimum_level} "
            f"{self.spec.character_class} trainer"
            if class_trainer is not None
            else "the Loremaster"
        )
        self.failure = (
            f"no verified route to {destination} before field departure from "
            f"{state.room_name!r} ({state.room_vnum})"
        )
        return None

    def _preferred_training_stat(self, state: CharacterState) -> str | None:
        profile = archetype_registry().class_profile(self.spec.character_class)
        carry_weight = _state_stat(state, "carry_wt")
        maximum_weight = _state_stat(state, "maxcarry_wt")
        capacity_pressure = bool(
            carry_weight is not None
            and maximum_weight not in (None, 0)
            and carry_weight / maximum_weight >= 0.8
            and "str" not in self.maxed_stats
        )
        martial_capabilities = {
            "natural-combat",
            "unarmed-combat",
            "weapon-combat",
        }
        if capacity_pressure:
            candidates = ("str", profile.primary_stat, "con", "wis", "dex", "int")
        elif (
            isinstance(state.level, int)
            and state.level < 20
            and profile.capabilities & martial_capabilities
        ):
            candidates = ("con", profile.primary_stat, "wis", "str", "dex", "int")
        else:
            candidates = (profile.primary_stat, "con", "wis", "str", "dex", "int")
        return next(
            (
                stat
                for stat in dict.fromkeys(candidates)
                if stat not in self.maxed_stats
            ),
            None,
        )

    def _emergency_borrow_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        """Borrow once at Dragonhoard Bank, then return to General Supplies."""
        room_vnum = state.room_vnum
        if self.emergency_borrow_step == 0:
            outbound = {
                "3724": "down",
                "3725": "down",
                "3001": "south",
                "3005": "east",
                "3006": "east",
            }
            direction = outbound.get(room_vnum or "")
            if direction is not None:
                return BotDecision(
                    direction,
                    "visit Dragonhoard Bank for emergency provision credit",
                )
            if room_vnum == "3007":
                self.emergency_borrow_step = 1
                return BotDecision(
                    "borrow 300",
                    "take one bounded loan for food and water storage",
                )
        elif self.emergency_borrow_step == 1:
            if room_vnum != "3007":
                self.failure = (
                    "emergency provision funding left Dragonhoard Bank before "
                    f"confirmation at room {state.room_name!r} ({room_vnum})"
                )
                return None
            if self.emergency_borrow_withdraw_required:
                if not self.emergency_borrow_withdraw_issued:
                    self.emergency_borrow_withdraw_issued = True
                    self.emergency_borrow_confirmed = False
                    return BotDecision(
                        "withdraw 3 gold",
                        "use the existing bank balance when borrowing is unnecessary",
                    )
                if self.emergency_borrow_rejected or not self.emergency_borrow_confirmed:
                    self.failure = (
                        "Dragonhoard Bank did not confirm the bounded emergency "
                        "provision withdrawal; do not retry it automatically"
                    )
                    return None
            if self.emergency_borrow_rejected or not self.emergency_borrow_confirmed:
                self.failure = (
                    "Dragonhoard Bank did not confirm the bounded emergency "
                    "provision loan; do not retry it automatically"
                )
                return None
            self.emergency_borrow_step = 2
            return BotDecision(
                "west",
                "leave Dragonhoard Bank after confirmed emergency funding",
            )
        else:
            returning = {
                "3007": "west",
                "3006": "west",
                "3005": "north",
                "3001": "up",
                "3725": "up",
            }
            direction = returning.get(room_vnum or "")
            if direction is not None:
                return BotDecision(
                    direction,
                    "return to General Supplies after the emergency loan",
                )
            if room_vnum == "3724":
                self.emergency_borrowing = False
                self.emergency_borrow_complete = True
                self.insufficient_funds = False
                return self._resupply_decision(state)
        self.failure = (
            "no verified emergency-bank route for "
            f"room {state.room_name!r} ({state.room_vnum})"
        )
        return None

    def _vault_stow_decision(self, state: CharacterState) -> BotDecision | None:
        if _is_sleeping(state):
            return BotDecision("stand", "wake before visiting the town vault")
        room_vnum = state.room_vnum or ""
        if self.vault_stow_returning:
            routes = {"3007": "west", "3006": "west", "3005": "north"}
            if room_vnum == "3001":
                self.vault_stow_complete = True
                return None
            direction = routes.get(room_vnum)
            if direction is None:
                self.failure = (
                    "no verified return route from the town vault at "
                    f"{state.room_name!r} ({state.room_vnum})"
                )
                return None
            return BotDecision(direction, "return from the town vault to recall")

        if self.vault_storage_rejected:
            rejected_container = self._vault_rejected_oversized_container(state)
            if (
                rejected_container is not None
                and not self.vault_capacity_disposal_pending
            ):
                self.vault_capacity_disposal_pending = True
                return BotDecision(
                    f"donate {rejected_container}",
                    "donate a verified-empty oversized container after both "
                    "carrying and vault capacity were exhausted",
                )
            self.vault_stow_returning = True
            return BotDecision(
                "west",
                "leave the full vault after the first rejected storage attempt",
            )

        if room_vnum != "3007":
            routes = {
                "3019": "west",
                "3018": "north",
                "3017": "north",
                "3012": "east",
                "3009": "south",
                "3013": "east",
                "3014": "north",
                "3726": "west",
                "3725": "down",
                "3001": "south",
                "3005": "east",
                "3006": "east",
                "3054": "south",
            }
            direction = routes.get(room_vnum)
            if direction is None:
                self.failure = (
                    "no verified route to the town vault from "
                    f"{state.room_name!r} ({state.room_vnum})"
                )
                return None
            return BotDecision(direction, "visit the town vault before field departure")

        if self.vault_empty_container_audit_index < len(
            self.vault_empty_container_audits
        ):
            item = self.vault_empty_container_audits[
                self.vault_empty_container_audit_index
            ]
            if self.vault_empty_container_audit_pending:
                response = _ANSI_ESCAPE.sub("", self.last_response).casefold()
                if "contains:" not in response or "nothing." not in response:
                    self.failure = (
                        f"refused to vault {item!r} without proof that it is empty"
                    )
                    return None
                self.vault_verified_empty_containers.add(item.casefold())
                self.vault_empty_container_audit_pending = False
                self.vault_empty_container_audit_index += 1
            else:
                self.vault_empty_container_audit_pending = True
                return BotDecision(
                    f"look in {item}",
                    "verify the oversized container is empty before temporary vault storage",
                )

        if self.vault_stow_command_index < len(self.vault_stow_commands):
            command = self.vault_stow_commands[self.vault_stow_command_index]
            self.vault_stow_command_index += 1
            if command.startswith("lodge "):
                self.vault_pending_lodge_keyword = command.removeprefix("lodge ")
            elif command.startswith("claim "):
                self.vault_pending_claim_keyword = command.removeprefix("claim ")
            reason = (
                "reclaim combat armour from the town vault"
                if command.startswith("claim ")
                else "store low-value heavy gear in the town vault"
            )
            return BotDecision(command, reason)
        if self.vault_equipment_audit_pending:
            self.vault_equipment_audit_pending = False
            candidate = self._vault_worn_capacity_candidate()
            if candidate is not None:
                keyword = item_keyword(candidate)
                self.vault_stow_attempted_keywords.add(keyword.casefold())
                self.vault_stow_commands += (
                    f"remove {keyword}",
                    f"lodge {keyword}",
                )
                self.vault_stow_audit_requested = False
                return self._vault_stow_decision(state)
        if not self.vault_stow_audit_requested:
            self.vault_stow_audit_requested = True
            return BotDecision("score", "verify carry capacity after vault storage")

        carry_weight = _state_stat(state, "carry_wt")
        max_carry_weight = _state_stat(state, "maxcarry_wt")
        if carry_weight is None or max_carry_weight is None:
            self.failure = "carry capacity was unavailable after vault storage"
            return None
        free_weight = max_carry_weight - carry_weight
        if free_weight < self.vault_required_free_weight:
            if self.gear_catalog is not None:
                self.vault_equipment_audit_pending = True
                return BotDecision(
                    "eq all",
                    "find the heaviest removable worn gear for further vault relief",
                )
            self.failure = (
                f"vault storage left only {free_weight} pounds free; "
                f"{self.vault_required_free_weight} required"
            )
            return None
        self.vault_stow_returning = True
        return BotDecision("west", "return from the town vault to recall")

    def _vault_rejected_oversized_container(
        self,
        state: CharacterState,
    ) -> str | None:
        keyword = self.vault_rejected_lodge_keyword
        if (
            keyword is None
            or keyword.casefold() not in self.vault_verified_empty_containers
            or self.gear_catalog is None
        ):
            return None
        maximum_weight = _state_stat(state, "maxcarry_wt")
        if maximum_weight is None or maximum_weight <= 0:
            return None
        candidates = (
            item
            for item in self.gear_catalog.objects.values()
            if keyword.casefold() in item.keywords.casefold().split()
            and is_capacity_infrastructure(item)
        )
        if any(item.weight >= max(20, maximum_weight * 0.2) for item in candidates):
            return keyword
        return None

    def _flight_borrow_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        """Take one confirmed bank loan, then return to the healer."""
        if self.flight_borrow_complete:
            return None

        room_vnum = state.room_vnum or ""
        if self.flight_borrow_step == 0:
            if room_vnum == "3007":
                if (
                    self.shop_visibility_rejected
                    or _has_named_affect(state.affects, "invis")
                ):
                    self.shop_visibility_rejected = False
                    return BotDecision(
                        "vis",
                        "become visible before using Dragonhoard Bank",
                    )
                self.flight_borrow_step = 1
                return BotDecision(
                    "borrow 300",
                    "take one bounded loan to cover the reboot-priced flight potion",
                )
            outbound = {
                "3054": "south",
                "3001": "south",
                "3005": "east",
                "3006": "east",
            }
            direction = outbound.get(room_vnum)
            if direction is not None:
                return BotDecision(
                    direction,
                    "follow the verified route to Dragonhoard Bank",
                )
        elif self.flight_borrow_step == 1:
            if room_vnum != "3007":
                self.failure = (
                    "flight-funding loan route left Dragonhoard Bank before "
                    f"confirmation at room {state.room_name!r} ({room_vnum})"
                )
                return None
            if self.flight_borrow_withdraw_required:
                if not self.flight_borrow_withdraw_issued:
                    self.flight_borrow_withdraw_issued = True
                    self.flight_borrow_confirmed = False
                    return BotDecision(
                        "withdraw 3 gold",
                        "use the bank balance when the teller says borrowing is unnecessary",
                    )
                if self.flight_borrow_rejected or not self.flight_borrow_confirmed:
                    self.failure = (
                        "Dragonhoard Bank did not confirm the bounded flight-funding "
                        "withdrawal; do not retry it automatically"
                    )
                    return None
            if self.flight_borrow_rejected or not self.flight_borrow_confirmed:
                self.failure = (
                    "Dragonhoard Bank did not confirm the bounded flight-funding "
                    "loan; do not retry it automatically"
                )
                return None
            self.flight_borrow_step = 2
            return BotDecision(
                "west",
                "leave Dragonhoard Bank after the confirmed loan",
            )
        elif self.flight_borrow_step == 2:
            if room_vnum == "3033":
                self.flight_borrow_step = 3
                return BotDecision(
                    "south",
                    "return from the Magic Shop route to the healer",
                )
            route = {
                "3006": "west",
                "3005": "south",
                "3014": "west",
                "3013": "west",
                "3012": "north",
            }
            direction = route.get(room_vnum)
            if direction is not None:
                return BotDecision(
                    direction,
                    "follow the verified route toward the Magic Shop",
                )
        else:
            if room_vnum == "3054":
                self.flight_borrow_complete = True
                return None
            route = {
                "3012": "east",
                "3013": "east",
                "3014": "north",
                "3005": "north",
                "3001": "north",
            }
            direction = route.get(room_vnum)
            if direction is not None:
                return BotDecision(
                    direction,
                    "return to the healer after the bounded flight-funding loan",
                )

        self.failure = (
            "no verified flight-funding route for "
            f"room {state.room_name!r} ({state.room_vnum})"
        )
        return None

    def _vault_worn_capacity_candidate(self) -> ObjectSource | None:
        if self.gear_catalog is None:
            return None
        candidates = [
            item
            for item in self.gear_catalog.match_equipment_text(self.last_response)
            if item_keyword(item).casefold() not in self.vault_stow_attempted_keywords
            if item.weight > 0
            if not is_capacity_infrastructure(item)
            if item_category(item) not in {"light", "wield", "pouch"}
        ]
        if not candidates:
            return None
        return max(
            candidates,
            key=lambda item: (
                item.weight,
                not protects_from_sale(item),
                -item.effective_level,
                -item.vnum,
            ),
        )

    def _fastwalk_world_cache_decision(
        self,
        state: CharacterState,
        *,
        deposit: bool,
    ) -> BotDecision | None:
        """Retrieve or deposit reboot-scoped field items in Midgaard bank."""
        phase = "post" if deposit else "preflight"
        complete_attr = f"fastwalk_world_cache_{phase}_complete"
        index_attr = f"fastwalk_world_cache_{phase}_index"
        returning_attr = f"fastwalk_world_cache_{phase}_returning"
        if getattr(self, complete_attr):
            return None
        if deposit:
            self.fastwalk_world_cache_post_started = True
        if _is_sleeping(state):
            return BotDecision("stand", "wake before visiting the world-item cache")

        room_vnum = state.room_vnum or ""
        if getattr(self, returning_attr):
            routes = {"3007": "west", "3006": "west", "3005": "north"}
            if room_vnum == "3001":
                setattr(self, complete_attr, True)
                return None
            direction = routes.get(room_vnum)
            if direction is None:
                self.failure = (
                    "no verified return route from the world-item cache at "
                    f"{state.room_name!r} ({state.room_vnum})"
                )
                return None
            return BotDecision(direction, "return from the Midgaard world-item cache")

        if room_vnum != "3007":
            routes = {
                "3054": "south",
                "3001": "south",
                "3005": "east",
                "3006": "east",
            }
            direction = routes.get(room_vnum)
            if direction is None:
                self.failure = (
                    "no verified route to the world-item cache from "
                    f"{state.room_name!r} ({state.room_vnum})"
                )
                return None
            reason = (
                "visit the reboot-scoped cache before logout"
                if deposit
                else "check the reboot-scoped cache before field departure"
            )
            return BotDecision(direction, reason)

        index = getattr(self, index_attr)
        if index < len(self.fastwalk_world_cache_items):
            keyword = self.fastwalk_world_cache_items[index]
            setattr(self, index_attr, index + 1)
            command = f"drop {keyword}" if deposit else f"get {keyword}"
            reason = (
                "cache a costly field key until reboot"
                if deposit
                else "reuse a cached field key when it is still present"
            )
            return BotDecision(command, reason)

        setattr(self, returning_attr, True)
        return BotDecision("west", "return from the Midgaard world-item cache")

    def _fastwalk_emergency_return_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        """Leave an interrupted field or cache route before other utility work."""
        self.fastwalk_emergency_recall_pending = False
        self.fastwalk_post_flee_audit_requested = False
        self.fastwalk_post_flee_audit_due = None
        if self.fastwalk_resume_current_route_after_interrupt:
            self.fastwalk_resume_current_route_after_interrupt = False
            self.fastwalk_attack_started = False
            if self.fastwalk_hunt_stop_index < len(self.fastwalk_hunt_stops):
                stop = self.fastwalk_hunt_stops[self.fastwalk_hunt_stop_index]
                room_vnum = str(state.room_vnum or "")
                if room_vnum in stop.route_vnums:
                    self.fastwalk_hunt_move_index = (
                        stop.route_vnums.index(room_vnum) + 1
                    )
            self.fastwalk_returning = False
            return self._fastwalk_hunt_plan_decision(state)
        if self.fastwalk_resume_hunt_after_interrupt:
            self.fastwalk_resume_hunt_after_interrupt = False
            self.fastwalk_hunt_stop_skipped = True
            self.fastwalk_attack_started = False
            next_stop_index = self.fastwalk_hunt_stop_index + 1
            next_stop = (
                self.fastwalk_hunt_stops[next_stop_index]
                if next_stop_index < len(self.fastwalk_hunt_stops)
                else None
            )
            if (
                next_stop is not None
                and _health_ratio(state) < next_stop.minimum_health_ratio
            ):
                self.fastwalk_abort_reason = (
                    "field hunt withdrew after skipping an interrupted stop "
                    "without the next target's required health reserve"
                )
                self.fastwalk_returning = True
                return BotDecision(
                    "recall",
                    "return after the interrupted field stop left too little health for the next target",
                )
            self.fastwalk_returning = False
            return self._fastwalk_hunt_plan_decision(state)
        self.fastwalk_returning = True
        room_vnum = state.room_vnum or ""
        if room_vnum == "3054":
            return None
        healer_direction = _MIDGAARD_HEALER_ROUTES.get(room_vnum)
        if healer_direction is not None:
            return BotDecision(
                healer_direction,
                "reach the Midgaard healer after unexpected field combat",
            )
        blocked_route = bool(
            self.fastwalk_abort_reason
            and "was blocked before its endpoint" in self.fastwalk_abort_reason
        )
        exhausted_route = bool(
            self.fastwalk_abort_reason
            and "exhausted movement before its endpoint" in self.fastwalk_abort_reason
        )
        return BotDecision(
            "recall",
            (
                "return safely after a blocked fastwalk step"
                if blocked_route
                else (
                    "return safely after fastwalk movement exhaustion"
                    if exhausted_route
                    else "leave the fastwalk immediately after unexpected combat"
                )
            ),
        )

    def _fastwalk_can_resume_current_route_after_interrupt(
        self,
        state: CharacterState,
    ) -> bool:
        """Allow one audited resume from a registered route waypoint."""
        if (
            self.fastwalk_route is None
            or not self.fastwalk_hunt_stops
            or not self.fastwalk_arrival_observed
            or self.fastwalk_attack_started
            or self.fastwalk_hunt_stop_killed
            or self.fastwalk_hunt_stop_skipped
            or self.fastwalk_hunt_stop_index >= len(self.fastwalk_hunt_stops)
        ):
            return False
        stop = self.fastwalk_hunt_stops[self.fastwalk_hunt_stop_index]
        if stop.target is None or not stop.route_vnums:
            return False
        room_vnum = str(state.room_vnum or "")
        try:
            route_index = stop.route_vnums.index(room_vnum)
        except ValueError:
            return False
        if route_index >= len(stop.route_vnums) - 1:
            return False
        if self.fastwalk_hunt_move_index < route_index + 1:
            return False
        attempt_key = (self.fastwalk_hunt_stop_index, room_vnum)
        if attempt_key in self.fastwalk_intermediate_route_resume_attempts:
            return False
        next_destination = stop.route_vnums[route_index + 1]
        return any(
            _EXIT_COMMANDS.get(direction, direction) in _MOVEMENT_COMMANDS
            and str(destination) == next_destination
            for direction, destination in state.exits.items()
        )

    def _fastwalk_prepare_interrupt_resume(
        self,
        state: CharacterState,
    ) -> str | None:
        """Select a bounded resume mode after an unexpected field attacker."""
        if self._fastwalk_can_resume_current_route_after_interrupt(state):
            room_vnum = str(state.room_vnum or "")
            self.fastwalk_intermediate_route_resume_attempts.add(
                (self.fastwalk_hunt_stop_index, room_vnum)
            )
            self.fastwalk_resume_current_route_after_interrupt = True
            return "current-route"
        if self._fastwalk_can_resume_hunt_after_interrupt(state):
            self.fastwalk_resume_hunt_after_interrupt = True
            return "next-stop"
        return None

    def _fastwalk_can_resume_hunt_after_interrupt(
        self,
        state: CharacterState,
    ) -> bool:
        """Allow a multi-stop hunt to skip a crowded endpoint after fleeing."""
        if (
            self.fastwalk_route is None
            or len(self.fastwalk_hunt_stops) < 2
            or not self.fastwalk_arrival_observed
            or self.fastwalk_attack_started
            or self.fastwalk_hunt_stop_killed
            or self.fastwalk_hunt_stop_index >= len(self.fastwalk_hunt_stops)
        ):
            return False
        stop = self.fastwalk_hunt_stops[self.fastwalk_hunt_stop_index]
        if stop.target is None or stop.route:
            return False
        if not stop.route_vnums:
            return True
        return str(state.room_vnum or "") == str(stop.route_vnums[-1])

    def _city_rearm_decision(self, state: CharacterState) -> BotDecision | None:
        """Buy and verify the source-backed weapon roles through Midgaard."""
        pounding_role = self.city_rearm_role == "pounding"
        outbound = (
            _CITY_REARM_POUNDING_ROUTE
            if pounding_role
            else _CITY_REARM_PRIMARY_ROUTE
        )
        returning = _reverse_fastwalk_commands(outbound)
        shop_room = "3120" if pounding_role else "3011"
        shop_keyword = "mace" if pounding_role else "dagger"
        required_free_weight = (
            _CITY_REARM_POUNDING_REQUIRED_FREE_WEIGHT
            if pounding_role
            else 1
        )
        room_vnum = state.room_vnum
        wielded_weapon = self._wielded_weapon()
        weapon_wielded = (
            bool(self.primary_weapon_observed)
            and not self.primary_weapon_lost
        )

        def reset_for_pounding_role() -> None:
            self.city_rearm_role = "pounding"
            self.city_rearm_step = 0
            self.city_rearm_route_index = 0
            self.city_rearm_returning = False
            self.city_rearm_direct_wield_attempted = False
            self.city_rearm_capacity_item = None
            self.city_rearm_capacity_checked = False
            self.purchase_carry_rejected = False
            self.purchase_level_rejected = False
            self.insufficient_funds = False

        def finish_at_healer() -> BotDecision | None:
            if room_vnum != "3054":
                self.failure = (
                    f"{shop_keyword} rearm return reached {state.room_name!r} "
                    f"({room_vnum}), expected healer room 3054"
                )
                return None
            if self.city_rearm_role == "primary" and self.city_rearm_pounding:
                if self._preferred_pounding_weapon(state) is None:
                    reset_for_pounding_role()
                    return self._city_rearm_decision(state)
            return None

        if self.city_rearm_borrowing and not pounding_role:
            if (
                room_vnum == "3007"
                and (
                    self.shop_visibility_rejected
                    or _has_named_affect(state.affects, "invis")
                )
            ):
                self.shop_visibility_rejected = False
                return BotDecision(
                    "vis",
                    "become visible before asking the Dragonhoard banker for credit",
                )
            if room_vnum == "3007":
                if self.city_rearm_borrow_step == 0:
                    self.city_rearm_borrow_step = 1
                    return BotDecision(
                        "withdraw 5 gold",
                        "use existing bank funds before taking the bounded primary-weapon loan",
                    )
                if self.city_rearm_borrow_step == 1:
                    if self.city_rearm_borrow_rejected:
                        self.failure = (
                            "Dragonhoard Bank rejected the primary-weapon funding request; "
                            "do not retry it automatically"
                        )
                        return None
                    if self.city_rearm_borrow_withdraw_required:
                        if self.city_rearm_borrow_withdraw_issued:
                            self.failure = (
                                "Dragonhoard Bank did not confirm the primary-weapon "
                                "withdrawal or loan; do not retry it automatically"
                            )
                            return None
                        self.city_rearm_borrow_withdraw_issued = True
                        self.city_rearm_borrow_step = 2
                        return BotDecision(
                            "borrow 500",
                            "take one bounded 500-copper loan for the missing primary weapon",
                        )
                    if not self.city_rearm_borrow_confirmed:
                        self.failure = (
                            "Dragonhoard Bank did not confirm the primary-weapon "
                            "withdrawal; do not retry it automatically"
                        )
                        return None
                    self.city_rearm_borrow_step = 3
                    return BotDecision(
                        "west",
                        "leave the bank after confirmed primary-weapon funding",
                    )
                if self.city_rearm_borrow_step == 2:
                    if self.city_rearm_borrow_rejected or not self.city_rearm_borrow_confirmed:
                        self.failure = (
                            "Dragonhoard Bank did not confirm the bounded primary-weapon "
                            "loan; do not retry it automatically"
                        )
                        return None
                    self.city_rearm_borrow_step = 3
                    return BotDecision(
                        "west",
                        "leave the bank after confirmed primary-weapon funding",
                    )
                self.failure = (
                    "primary-weapon funding was already attempted at Dragonhoard Bank"
                )
                return None
            if room_vnum == "3011" and self.city_rearm_borrow_step >= 3:
                self.city_rearm_borrowing = False
                self.city_rearm_step = 1
                self.insufficient_funds = False
            else:
                borrow_routes = (
                    {
                        "3011": "south",
                        "3016": "west",
                        "3015": "west",
                        "3014": "north",
                        "3005": "east",
                        "3006": "east",
                    }
                    if self.city_rearm_borrow_step < 3
                    else {
                        "3006": "west",
                        "3005": "south",
                        "3014": "east",
                        "3015": "east",
                        "3016": "north",
                    }
                )
                direction = borrow_routes.get(room_vnum or "")
                if direction is not None:
                    return BotDecision(
                        direction,
                        "visit Dragonhoard Bank for primary-weapon credit",
                    )
                self.failure = (
                    "primary-weapon credit route could not continue from "
                    f"{state.room_name!r} ({room_vnum})"
                )
                return None

        if (
            room_vnum == shop_room
            and not pounding_role
            and weapon_wielded
            and (
                self._combat_weapon_preference() is None
                or self._primary_weapon_satisfies_preference(wielded_weapon)
            )
        ):
            self.primary_weapon_observed = True
            self.primary_weapon_lost = False
            self.city_rearm_returning = True
            self.city_rearm_route_index = 0

        if (
            not self.city_rearm_returning
            and self.city_rearm_route_index == 0
            and room_vnum != "3054"
        ):
            home = self._return_home_decision(state)
            if home is not None:
                return home
            self.failure = (
                f"{shop_keyword} rearm could not reach healer room 3054 from "
                f"{state.room_name!r} ({room_vnum})"
            )
            return None

        if (
            not self.city_rearm_returning
            and self.city_rearm_route_index == 0
            and room_vnum == "3054"
        ):
            if not pounding_role:
                preferred_weapon = self._preferred_primary_weapon(state)
                if self._primary_weapon_satisfies_preference(wielded_weapon):
                    self.primary_weapon_observed = True
                    self.primary_weapon_lost = False
                    self.city_rearm_piercing_keyword = item_command_keyword(
                        preferred_weapon or wielded_weapon,
                        self._state_weapons(state),
                    )
                    if self.city_rearm_pounding and self._preferred_pounding_weapon(
                        state
                    ) is None:
                        reset_for_pounding_role()
                        return self._city_rearm_decision(state)
                    self.city_rearm_returning = True
                    self.city_rearm_route_index = len(returning)
                    return None
                if (
                    preferred_weapon is not None
                    and not self.city_rearm_direct_wield_attempted
                ):
                    self.city_rearm_direct_wield_attempted = True
                    return BotDecision(
                        f"wield {item_command_keyword(preferred_weapon, self._state_weapons(state))}",
                        "make the source-preferred weapon the thief's primary weapon",
                    )
            else:
                pounding_weapon = self._preferred_pounding_weapon(state)
                primary_weapon = self._preferred_primary_weapon(state)
                if pounding_weapon is not None:
                    if primary_weapon is None:
                        self.failure = (
                            "pounding-weapon rearm found no source-matched "
                            "primary weapon to restore after stun"
                        )
                        return None
                    if (
                        wielded_weapon is None
                        or wielded_weapon.vnum != primary_weapon.vnum
                    ):
                        if not self.city_rearm_direct_wield_attempted:
                            self.city_rearm_direct_wield_attempted = True
                            self.city_rearm_piercing_keyword = item_command_keyword(
                                primary_weapon,
                                self._state_weapons(state),
                            )
                            return BotDecision(
                                f"wield {self.city_rearm_piercing_keyword}",
                                (
                                    "restore the piercing primary after securing the pounding weapon"
                                    if self._combat_weapon_preference() == "piercing"
                                    else "restore the normal primary after securing the pounding weapon"
                                ),
                            )
                        self.failure = (
                            "pounding-weapon rearm could not verify the "
                            "normal primary in the wield slot"
                        )
                        return None
                    self.primary_weapon_observed = True
                    self.primary_weapon_lost = False
                    self.city_rearm_piercing_keyword = item_command_keyword(
                        primary_weapon,
                        self._state_weapons(state),
                    )
                    self.city_rearm_returning = True
                    self.city_rearm_route_index = len(returning)
                    return None

        if (
            not self.city_rearm_returning
            and self.city_rearm_route_index == 0
            and room_vnum == "3054"
            and not self.city_rearm_capacity_checked
        ):
            carry_weight = _state_stat(state, "carry_wt")
            maximum_weight = _state_stat(state, "maxcarry_wt")
            if carry_weight is None or maximum_weight is None:
                self.failure = (
                    "carry capacity was unavailable before "
                    f"{shop_keyword} rearm"
                )
                return None
            if maximum_weight - carry_weight < required_free_weight:
                keyword = _sellable_inventory_keyword(
                    state.inventory,
                    self.gear_catalog,
                )
                if keyword is None:
                    self.failure = (
                        f"{shop_keyword} rearm needs {required_free_weight} pounds "
                        "of free capacity, "
                        "but no disposable carried equipment was available"
                    )
                    return None
                self.city_rearm_capacity_item = keyword
                self.city_rearm_capacity_checked = True
                return BotDecision(
                    f"donate {keyword}",
                    f"free capacity for the {shop_keyword} at the safe healer checkpoint",
                )
            self.city_rearm_capacity_checked = True

        if self.city_rearm_capacity_item is not None:
            carry_weight = _state_stat(state, "carry_wt")
            maximum_weight = _state_stat(state, "maxcarry_wt")
            if (
                carry_weight is None
                or maximum_weight is None
                or maximum_weight - carry_weight < required_free_weight
            ):
                self.failure = (
                    f"donating {self.city_rearm_capacity_item} did not free "
                    f"enough capacity for the {shop_keyword}"
                )
                return None
            self.city_rearm_capacity_item = None

        if not self.city_rearm_returning and not (
            pounding_role and self.city_rearm_step == 5
        ):
            if self.city_rearm_route_index < len(outbound):
                command = outbound[self.city_rearm_route_index]
                self.city_rearm_route_index += 1
                return BotDecision(
                    command,
                    "walk through safe Midgaard to the source-backed weapon shop",
                )
            if room_vnum != shop_room:
                self.failure = (
                    f"weapon-shop route reached {state.room_name!r} ({room_vnum}), "
                    f"expected room {shop_room}"
                )
                return None
            if _has_named_affect(state.affects, "invis"):
                return BotDecision(
                    "vis",
                    f"become visible before buying the source-backed {shop_keyword}",
                )
            if self.city_rearm_step == 0:
                self.city_rearm_step = 1
                return BotDecision(
                    f"list {shop_keyword}",
                    f"record the reboot-priced {shop_keyword} quote before attempting rearm",
                )
            if self.city_rearm_step == 1:
                self.city_rearm_step = 2
                return BotDecision(
                    f"buy {shop_keyword}",
                    (
                        "buy the source mace as the Bounty Hunter's pounding weapon"
                        if pounding_role
                        else "buy the one-pound source dagger as a lightweight primary weapon"
                    ),
                )
            if self.city_rearm_step == 2:
                if self.insufficient_funds:
                    if pounding_role:
                        self.failure = (
                            "the source-backed pounding weapon was unaffordable "
                            "after the safe rearm route"
                        )
                        return None
                    if self.city_rearm_funding_attempted:
                        self.failure = (
                            "the source-backed primary weapon remained unaffordable after "
                            "one bounded Dragonhoard Bank funding attempt"
                        )
                        return None
                    self.city_rearm_funding_attempted = True
                    self.city_rearm_borrowing = True
                    self.city_rearm_borrow_step = 0
                    self.city_rearm_borrow_confirmed = False
                    self.city_rearm_borrow_rejected = False
                    self.city_rearm_borrow_withdraw_required = False
                    self.city_rearm_borrow_withdraw_issued = False
                    self.insufficient_funds = False
                    return self._city_rearm_decision(state)
                if self.purchase_carry_rejected:
                    self.failure = (
                        f"insufficient carry capacity for the source-backed {shop_keyword}"
                    )
                    return None
                self.city_rearm_step = 3
                return BotDecision(
                    f"wield {shop_keyword}",
                    (
                        "equip the purchased pounding weapon before returning to the piercing primary"
                        if pounding_role
                        else "equip the purchased primary weapon"
                    ),
                )
            if self.city_rearm_step == 3:
                self.city_rearm_step = 4
                return BotDecision(
                    "eq all",
                    f"verify the source-backed {shop_keyword} in the wield slot",
                )
            equipment_text = _ANSI_ESCAPE.sub("", self.last_response).casefold()
            weapon_slot_seen, weapon_description = _equipment_weapon_slot(
                equipment_text
            )
            if pounding_role:
                verified_pounding = any(
                    is_blunt_weapon(item)
                    for item in self.gear_worn
                    if item_category(item) == "wield"
                )
                if not verified_pounding:
                    verified_pounding = bool(
                        weapon_slot_seen
                        and weapon_description is not None
                        and "mace" in weapon_description
                    )
                if not verified_pounding:
                    self.failure = (
                        "equipment audit did not verify the purchased source-backed "
                        "mace as wielded"
                    )
                    return None
                primary = self._preferred_primary_weapon(state)
                primary_keyword = (
                    item_command_keyword(primary, self._state_weapons(state))
                    if primary is not None
                    else self.city_rearm_piercing_keyword
                )
                if not primary_keyword:
                    self.failure = (
                        "equipment audit verified the pounding weapon but found "
                        "no primary weapon to restore after stun"
                    )
                    return None
                self.city_rearm_piercing_keyword = primary_keyword
                self.city_rearm_step = 5
                return BotDecision(
                    f"wield {primary_keyword}",
                    (
                        "switch back to the piercing weapon before leaving the rearm shop"
                        if self._combat_weapon_preference() == "piercing"
                        else "switch back to the normal primary before leaving the rearm shop"
                    ),
                )
            if not (
                weapon_slot_seen
                and weapon_description is not None
                and "dagger" in weapon_description
            ):
                self.failure = "equipment audit did not verify the purchased dagger as wielded"
                return None
            self.primary_weapon_observed = True
            self.primary_weapon_lost = False
            self.city_rearm_piercing_keyword = "dagger"
            self.city_rearm_returning = True
            self.city_rearm_route_index = 0

        if pounding_role and self.city_rearm_step == 5:
            equipment_text = _ANSI_ESCAPE.sub("", self.last_response).casefold()
            weapon_slot_seen, weapon_description = _equipment_weapon_slot(
                equipment_text
            )
            verified_primary = any(
                (
                    is_piercing_weapon(item)
                    if self._combat_weapon_preference() == "piercing"
                    else item_command_keyword(
                        item,
                        self._state_weapons(state),
                    )
                    == self.city_rearm_piercing_keyword
                )
                for item in self.gear_worn
                if item_category(item) == "wield"
            )
            if not verified_primary and self._combat_weapon_preference() == "piercing":
                verified_primary = bool(
                    weapon_slot_seen
                    and weapon_description is not None
                    and any(
                        marker in weapon_description
                        for marker in ("dagger", "knife", "rapier", "piercing")
                    )
                )
            if not verified_primary:
                self.failure = (
                    "equipment audit did not verify the primary weapon after "
                    "the pounding-weapon purchase"
                )
                return None
            self.primary_weapon_observed = True
            self.primary_weapon_lost = False
            self.city_rearm_returning = True
            self.city_rearm_route_index = 0

        if self.city_rearm_route_index < len(returning):
            command = returning[self.city_rearm_route_index]
            self.city_rearm_route_index += 1
            return BotDecision(
                command,
                "return safely from the Midgaard weapon shop",
            )
        return finish_at_healer()

    def _city_outfit_decision(self, state: CharacterState) -> BotDecision | None:
        """Fill empty legal armour slots from the safe Midgaard leather shop."""
        outbound = (
            "south",
            "south",
            "south",
            "south",
            "west",
            "west",
            "north",
        )
        returning = _reverse_fastwalk_commands(outbound)
        room_vnum = state.room_vnum

        if _is_sleeping(state):
            return BotDecision("stand", "wake before travelling to buy basic equipment")

        if (
            not self.city_outfit_returning
            and self.city_outfit_route_index == 0
            and room_vnum != "3054"
        ):
            home = self._return_home_decision(state)
            if home is not None:
                return home
            self.failure = (
                f"basic-equipment outfit could not reach healer room 3054 from "
                f"{state.room_name!r} ({room_vnum})"
            )
            return None

        if not self.city_outfit_audited:
            if not _equipment_audit_present(self.last_response):
                return BotDecision(
                    "eq all",
                    "identify empty profession-legal slots before buying basic gear",
                )
            self.city_outfit_initial_empty = _equipment_empty_categories(
                self.last_response
            )
            stock = (
                ("pouch", "pouch"),
                ("hands", "gloves"),
                ("head", "cap"),
                ("arms", "sleeves"),
                ("feet", "boots"),
                ("legs", "pants"),
                ("body", "jerkin"),
            )
            self.city_outfit_plan = [
                (category, keyword)
                for category, keyword in stock
                if category in self.city_outfit_initial_empty
            ]
            self.city_outfit_audited = True
            if not self.city_outfit_plan:
                return None

        if (
            not self.city_outfit_returning
            and self.city_outfit_route_index == 0
            and room_vnum == "3054"
            and not self.city_outfit_capacity_relief_attempted
            and "arms" in self.city_outfit_initial_empty
        ):
            carry_weight = _state_stat(state, "carry_wt")
            maximum_weight = _state_stat(state, "maxcarry_wt")
            pie_count = sum(
                "pie" in description.casefold()
                for description in _inventory_descriptions(state.inventory)
            )
            if (
                carry_weight is not None
                and maximum_weight is not None
                and maximum_weight - carry_weight < 4
                and pie_count > 3
            ):
                self.city_outfit_capacity_relief_attempted = True
                return BotDecision(
                    "donate pie",
                    "trade one replaceable excess pie for room to wear arm armour",
                )

        if not self.city_outfit_returning:
            if self.city_outfit_route_index < len(outbound):
                command = outbound[self.city_outfit_route_index]
                self.city_outfit_route_index += 1
                return BotDecision(
                    command,
                    "walk through safe Midgaard to the source-backed leather shop",
                )
            if room_vnum != "3035":
                self.failure = (
                    f"leather-shop route reached {state.room_name!r} ({room_vnum}), "
                    "expected room 3035"
                )
                return None
            if self.shop_visibility_rejected or _has_named_affect(
                state.affects, "invis"
            ):
                self.shop_visibility_rejected = False
                return BotDecision("vis", "become visible before buying basic gear")

            if self.city_outfit_item_index < len(self.city_outfit_plan):
                category, keyword = self.city_outfit_plan[
                    self.city_outfit_item_index
                ]
                if self.city_outfit_item_step == 0:
                    self.city_outfit_item_step = 1
                    return BotDecision(
                        f"list {keyword}",
                        f"record the reboot-priced {category} basic before buying",
                    )
                if self.city_outfit_item_step == 1:
                    listed_level = _shop_listed_item_level(self.last_response)
                    if (
                        listed_level is not None
                        and state.level is not None
                        and listed_level > state.level + 5
                    ):
                        self.city_outfit_deferred_categories.add(category)
                        self.city_outfit_item_index += 1
                        self.city_outfit_item_step = 0
                        return self._city_outfit_decision(state)
                    self.insufficient_funds = False
                    self.purchase_carry_rejected = False
                    self.purchase_level_rejected = False
                    self.city_outfit_item_step = 2
                    return BotDecision(
                        f"buy {keyword}",
                        f"buy an inexpensive basic for the empty {category} slot",
                    )
                if self.city_outfit_item_step == 2:
                    if (
                        self.insufficient_funds
                        or self.purchase_carry_rejected
                        or self.purchase_level_rejected
                    ):
                        self.city_outfit_deferred_categories.add(category)
                        self.city_outfit_item_index += 1
                        self.city_outfit_item_step = 0
                        return self._city_outfit_decision(state)
                    self.city_outfit_item_step = 3
                    return BotDecision(
                        f"wear {keyword}",
                        f"equip the purchased {category} basic",
                    )
                self.city_outfit_item_index += 1
                self.city_outfit_item_step = 0
                return self._city_outfit_decision(state)

            if not self.city_outfit_verification_requested:
                self.city_outfit_verification_requested = True
                return BotDecision(
                    "eq all",
                    "verify which formerly empty legal slots now hold basic gear",
                )
            remaining = (
                _equipment_empty_categories(self.last_response)
                & (
                    {category for category, _ in self.city_outfit_plan}
                    - self.city_outfit_deferred_categories
                )
            )
            if remaining:
                self.failure = (
                    "basic-equipment audit still showed empty purchased slots: "
                    + ", ".join(sorted(remaining))
                )
                return None
            self.city_outfit_returning = True
            self.city_outfit_route_index = 0

        if self.city_outfit_route_index < len(returning):
            command = returning[self.city_outfit_route_index]
            self.city_outfit_route_index += 1
            return BotDecision(command, "return safely from the Midgaard leather shop")
        if room_vnum != "3054":
            self.failure = (
                f"leather-shop return reached {state.room_name!r} ({room_vnum}), "
                "expected healer room 3054"
            )
        return None

    def _city_restock_decision(self, state: CharacterState) -> BotDecision | None:
        """Use the verified Midgaard fountain and bakery route, then stop."""
        if _is_sleeping(state):
            return BotDecision("stand", "wake before travelling to city supplies")

        room_vnum = state.room_vnum
        room_name = (state.room_name or "").casefold()
        can_use_city_invisibility = bool(
            self.spec.character_class == "mage"
            and (state.level or 0) >= 8
        )
        if (
            can_use_city_invisibility
            and room_vnum == "3019"
            and self.city_restock_step < 3
            and not _has_named_affect(state.affects, "invis")
        ):
            return BotDecision(
                "cast invis",
                "cross Midgaard safely while travelling to city supplies",
            )
        if self.restock_borrowing:
            if (
                room_vnum == "3007"
                and (
                    self.shop_visibility_rejected
                    or _has_named_affect(state.affects, "invis")
                )
            ):
                self.shop_visibility_rejected = False
                return BotDecision(
                    "vis",
                    "become visible before asking the Dragonhoard banker for credit",
                )
            if (
                can_use_city_invisibility
                and room_vnum in {"3013", "3006"}
                and not _has_named_affect(state.affects, "invis")
            ):
                return BotDecision(
                    "cast invis",
                    "cross Temple Square safely during the emergency bank trip",
                )
            if room_vnum == "3009" and self.restock_borrow_step >= 2:
                self.restock_borrowing = False
                self.restock_borrow_complete = True
                self.insufficient_funds = False
                self.city_restock_step = 4
                return self._city_restock_decision(state)
            if room_vnum == "3007":
                if self.restock_borrow_step == 0:
                    self.restock_borrow_step = 1
                    return BotDecision(
                        "borrow 300",
                        "use bank credit to fund essential field provisions",
                    )
                if self.restock_borrow_step == 1:
                    if self.restock_borrow_withdraw_required:
                        if not self.restock_borrow_withdraw_issued:
                            self.restock_borrow_withdraw_issued = True
                            self.restock_borrow_confirmed = False
                            return BotDecision(
                                "withdraw 3 gold",
                                "use the existing bank balance when borrowing is unnecessary",
                            )
                        if (
                            self.restock_borrow_rejected
                            or not self.restock_borrow_confirmed
                        ):
                            self.failure = (
                                "Dragonhoard Bank did not confirm the bounded "
                                "restock withdrawal; do not retry it automatically"
                            )
                            return None
                    if (
                        self.restock_borrow_rejected
                        or not self.restock_borrow_confirmed
                    ):
                        self.failure = (
                            "Dragonhoard Bank did not confirm the bounded "
                            "restock loan; do not retry it automatically"
                        )
                        return None
                self.restock_borrow_step = 2
                return BotDecision(
                    "west",
                    "leave the bank after confirmed restock funding",
                )
            borrow_routes = {
                "3009": "south",
                "3013": "east",
                "3014": "north",
                "3005": "east",
                "3006": "east" if self.restock_borrow_step == 0 else "west",
            }
            if room_vnum == "3005" and self.restock_borrow_step >= 2:
                return BotDecision("south", "return from the bank to the Bakery")
            if room_vnum == "3014" and self.restock_borrow_step >= 2:
                return BotDecision("west", "return from the bank to the Bakery")
            if room_vnum == "3013" and self.restock_borrow_step >= 2:
                return BotDecision("north", "return from the bank to the Bakery")
            direction = borrow_routes.get(room_vnum or "")
            if direction is not None:
                return BotDecision(direction, "visit Dragonhoard Bank for food credit")
        if room_vnum == "3737" or room_name == "safety":
            return BotDecision("enter portal", "leave arena Safety for Midgaard")
        if room_vnum == "3724":
            return BotDecision(
                "down",
                "leave General Supplies for the Mud School entrance",
            )
        if room_vnum == "3725" or "entrance to the mud school" in room_name:
            return BotDecision("down", "travel from Mud School to the Temple")
        if (
            self.city_restock_step < 6
            and (room_vnum == "3001" or "temple of midgaard" in room_name)
        ):
            return BotDecision("south", "travel from the Temple to Temple Square")
        at_bakery = room_vnum == "3009" or room_name == "the bakery"
        if (
            at_bakery
            and (
                self.shop_visibility_rejected
                or _has_named_affect(state.affects, "invis")
            )
        ):
            self.shop_visibility_rejected = False
            return BotDecision(
                "vis",
                "become visible before asking the baker to trade",
            )
        if (
            at_bakery
            and self.city_restock_step >= 6
            and not _has_inventory_item(state.inventory, "pie")
        ):
            self.failure = "city restock inventory audit found no pie after purchase"
            return None
        if self.city_restock_step >= 6:
            home_routes = {
                "3009": "south",
                "3013": "east",
                "3014": "north",
                "3005": "north",
                "3001": "north",
            }
            if room_vnum == "3054":
                return None
            direction = home_routes.get(room_vnum or "")
            if direction is not None:
                return BotDecision(
                    direction,
                    "return safely to the Midgaard healer after city restocking",
                )
            self.failure = (
                "city restock return did not reach healer room 3054 from "
                f"{state.room_name!r} ({room_vnum})"
            )
            return None
        if self.city_restock_step < 3:
            fountain_routes = {
                "3054": "south",
                "3019": "west",
                "3018": "north",
                "3017": "north",
                "3012": "east",
                "3013": "east",
                "3014": "north",
                "3009": "south",
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
        if at_bakery:
            if self.insufficient_funds and not self.restock_borrow_complete:
                self.restock_borrowing = True
                return BotDecision(
                    "south",
                    "visit Dragonhoard Bank after the baker rejects the food order",
                )
            if (
                self.affordable_pies
                and not self.affordable_pies_ordered
                and self.city_restock_step >= 5
            ):
                quantity = min(
                    self.affordable_pies,
                    self._pie_carry_capacity(state),
                )
                if quantity < 1:
                    return self._city_restock_capacity_decision(state)
                self.affordable_pies_ordered = True
                return BotDecision(
                    f"buy {quantity} pie",
                    "retry the quantity the baker says is currently affordable",
                )
            index = self.city_restock_step - 3
            if index == 0:
                self.city_restock_step += 1
                return BotDecision("list", "inspect the baker's current pie stock")
            if index == 1:
                quantity = min(
                    self.pie_order_limit,
                    self._pie_carry_capacity(state),
                )
                if quantity < 1:
                    return self._city_restock_capacity_decision(state)
                self.city_restock_step += 1
                return BotDecision(
                    f"buy {quantity} pie",
                    "buy a carry-safe reserve of big pot pies from the baker",
                )
            if index == 2:
                self.city_restock_step += 1
                return BotDecision(
                    "inventory",
                    "verify the city restock in carried inventory",
                )
            self.failure = "city restock reached the Bakery with invalid progress"
            return None
        self.failure = (
            "no verified city-restock route for "
            f"room {state.room_name!r} ({state.room_vnum})"
        )
        return None

    def _pie_carry_capacity(self, state: CharacterState) -> int:
        carry_weight = _state_stat(state, "carry_wt")
        maximum_weight = _state_stat(state, "maxcarry_wt")
        carry_items = _state_stat(state, "carry_num")
        maximum_items = _state_stat(state, "maxcarry_num")
        capacities = [self.pie_order_limit]
        if carry_weight is not None and maximum_weight is not None:
            capacities.append((maximum_weight - carry_weight) // _PIE_WEIGHT)
        if carry_items is not None and maximum_items is not None:
            capacities.append(maximum_items - carry_items)
        return max(0, min(capacities))

    def _city_restock_capacity_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        """Resolve a full inventory without discarding unknown equipment."""
        if not self.city_restock_capacity_audited:
            self.city_restock_capacity_audited = True
            return BotDecision(
                "inventory",
                "audit carried items before a capacity-limited food purchase",
            )
        food_keyword = _inventory_food_keyword(
            state.inventory,
            self.gear_catalog,
        )
        if (
            not self.city_restock_capacity_relief_attempted
            and food_keyword is not None
        ):
            self.city_restock_capacity_relief_attempted = True
            self.city_restock_capacity_relief_pending = True
            return BotDecision(
                f"eat {food_keyword}",
                "consume confirmed carried food to free capacity for a fresh reserve",
            )
        self.failure = "no carry capacity remained for one essential pie"
        return None

    def _guildmaster_research_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        """Read the teacher clue and visit the character's Midgaard trainer."""
        if _is_sleeping(state):
            return BotDecision("stand", "wake before travelling to the class trainer")
        room_vnum = state.room_vnum
        room_name = (state.room_name or "").casefold()
        trainer = _CLASS_TRAINERS.get(self.spec.character_class.casefold())
        if trainer is None:
            self.failure = (
                "no source-backed level-10 trainer is registered for "
                f"{self.spec.character_class!r}"
            )
            return None
        if room_vnum == "3737" or room_name == "safety":
            return BotDecision("enter portal", "leave arena Safety for Midgaard")
        if _is_arena_vnum(room_vnum):
            return BotDecision("up", "leave the arena before travelling to Midgaard")
        if room_vnum == "3725" or "entrance to the mud school" in room_name:
            return BotDecision("down", "leave Mud School for the Temple")
        if room_vnum == "3033" or room_name == "the magic shop":
            return BotDecision("south", "return from the Magic Shop to central Midgaard")
        if room_vnum == "3001" and not self.teacher_clue_requested:
            self.teacher_clue_requested = True
            return BotDecision(
                "help teacher clue",
                "record the live level-band instruction before visiting the trainer",
            )
        if room_vnum == trainer.room_vnum:
            commands = (
                (f"look {trainer.keyword}", "confirm the class-specific trainer"),
                ("practice", "inspect the trainer's available class training"),
            )
            if self.guildmaster_step < len(commands):
                command, reason = commands[self.guildmaster_step]
                self.guildmaster_step += 1
                return BotDecision(command, reason)
            return None
        routes = {
            "3054": "south",
            **trainer.outbound,
        }
        direction = routes.get(room_vnum or "")
        if direction is not None:
            return BotDecision(
                direction,
                f"follow the source-backed route to the {self.spec.character_class} trainer",
            )
        healer_direction = _MIDGAARD_HEALER_ROUTES.get(room_vnum or "")
        if healer_direction is not None:
            return BotDecision(
                healer_direction,
                "return to the Temple before taking the class-trainer route",
            )
        self.failure = (
            f"no verified {self.spec.character_class} trainer route for "
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
            if (
                self.shop_visibility_rejected
                or _has_named_affect(state.affects, "invis")
            ):
                self.shop_visibility_rejected = False
                self.magic_shop_step = 0
                return BotDecision(
                    "vis",
                    "become visible before asking the Magic Shop wizard to trade",
                )
            if self.magic_shop_purchase_failed:
                recovery = self._magic_shop_diploma_recovery_decision()
                if recovery is not None:
                    return recovery
                return BotDecision(
                    "south",
                    "return after the current light blue potion price was unaffordable",
                )
            if self.purchase_carry_rejected:
                food_keyword = _inventory_food_keyword(
                    state.inventory,
                    self.gear_catalog,
                )
                if (
                    not self.magic_shop_capacity_relief_attempted
                    and food_keyword is not None
                ):
                    self.magic_shop_capacity_relief_attempted = True
                    self.magic_shop_capacity_relief_pending = True
                    return BotDecision(
                        f"eat {food_keyword}",
                        "consume confirmed carried food to free capacity for flight",
                    )
                has_worn_diploma = any(
                    "mud school diploma"
                    in normalize_item_name(item.short_description)
                    for item in self.gear_worn
                )
                has_worn_tophat = any(
                    normalize_item_name(item.short_description) == "tophat"
                    for item in self.gear_worn
                )
                if (
                    not self.magic_shop_capacity_relief_attempted
                    and has_worn_diploma
                ):
                    self.magic_shop_capacity_relief_attempted = True
                    self.magic_shop_diploma_relief_step = 1
                    self.magic_shop_tophat_relief_planned = has_worn_tophat
                    return BotDecision(
                        "remove diploma",
                        "temporarily remove the one-weight diploma for flight capacity",
                    )
                if self.magic_shop_diploma_relief_step == 1:
                    self.magic_shop_diploma_relief_step = 2
                    self.magic_shop_diploma_dropped = True
                    return BotDecision(
                        "drop diploma",
                        "cache the diploma in the safe Magic Shop during purchase",
                    )
                if self.magic_shop_diploma_relief_step == 2:
                    if self.magic_shop_tophat_relief_planned:
                        self.magic_shop_diploma_relief_step = 3
                        return BotDecision(
                            "remove tophat",
                            "temporarily remove the one-weight tophat for flight capacity",
                        )
                    self.magic_shop_diploma_relief_step = 5
                    self.purchase_carry_rejected = False
                    self.magic_shop_step = 1
                elif self.magic_shop_diploma_relief_step == 3:
                    self.magic_shop_diploma_relief_step = 4
                    self.magic_shop_tophat_dropped = True
                    return BotDecision(
                        "drop tophat",
                        "cache the tophat in the safe Magic Shop during purchase",
                    )
                elif self.magic_shop_diploma_relief_step == 4:
                    self.magic_shop_diploma_relief_step = 5
                    self.purchase_carry_rejected = False
                    self.magic_shop_step = 1
                else:
                    self.magic_shop_purchase_failed = True
                    recovery = self._magic_shop_diploma_recovery_decision()
                    if recovery is not None:
                        return recovery
                    return BotDecision(
                        "south",
                        "return because no safe capacity relief was available for flight",
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
            if (
                self.magic_shop_buy_fly
                and self.magic_shop_step == 3
                and not _has_inventory_item(state.inventory, "light blue potion")
            ):
                self.magic_shop_purchase_failed = True
                recovery = self._magic_shop_diploma_recovery_decision()
                if recovery is not None:
                    return recovery
                return BotDecision(
                    "south",
                    "return because the light blue potion purchase was not confirmed",
                )
            if self.magic_shop_step < len(commands):
                command, reason = commands[self.magic_shop_step]
                self.magic_shop_step += 1
                return BotDecision(command, reason)
            recovery = self._magic_shop_diploma_recovery_decision()
            if recovery is not None:
                return recovery
            return BotDecision("south", "return from the Magic Shop to the healer")

        if self.magic_shop_step == 0:
            outward_routes = {
                "3054": "south",
                "3001": "south",
                "3005": "south",
                "3006": "west",
                "3014": "west",
                "3013": "west",
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
                "3012": "east",
                "3013": "east",
                "3014": "north",
                "3006": "north",
                "3005": "north",
                "3001": "north",
            }
            direction = return_routes.get(room_vnum or "")
            if direction is not None:
                return BotDecision(direction, "return from the Magic Shop to the healer")
            if room_vnum == "3054":
                return None

        self.failure = (
            "no verified Magic Shop route for "
            f"room {state.room_name!r} ({state.room_vnum})"
        )
        return None

    def _magic_shop_diploma_recovery_decision(self) -> BotDecision | None:
        if not self.magic_shop_diploma_dropped:
            return None
        if self.magic_shop_diploma_recovery_step == 0:
            self.magic_shop_diploma_recovery_step = 1
            return BotDecision(
                "get diploma",
                "retrieve the temporarily cached Mud School diploma",
            )
        if self.magic_shop_diploma_recovery_step == 1:
            self.magic_shop_diploma_recovery_step = 2
            return BotDecision(
                "hold diploma",
                "restore the Mud School diploma after the flight purchase",
            )
        if (
            self.magic_shop_tophat_dropped
            and self.magic_shop_diploma_recovery_step == 2
        ):
            self.magic_shop_diploma_recovery_step = 3
            return BotDecision(
                "get tophat",
                "retrieve the temporarily cached tophat",
            )
        if (
            self.magic_shop_tophat_dropped
            and self.magic_shop_diploma_recovery_step == 3
        ):
            self.magic_shop_diploma_recovery_step = 4
            return BotDecision(
                "wear tophat",
                "restore the tophat after the flight purchase",
            )
        self.magic_shop_diploma_dropped = False
        self.magic_shop_tophat_dropped = False
        return None

    def _bank_excess_coin_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        room_vnum = state.room_vnum
        if room_vnum == "3007":
            if (
                self.shop_visibility_rejected
                or _has_named_affect(state.affects, "invis")
            ):
                self.shop_visibility_rejected = False
                return BotDecision(
                    "vis",
                    "become visible before using Dragonhoard Bank",
                )
            commands = (
                (
                    "deposit all",
                    "bank the critically encumbering carried coin hoard",
                ),
                (
                    "withdraw 1 gold",
                    "retain one compact gold coin for routine purchases",
                ),
                ("west", "leave Dragonhoard Bank after reducing coin weight"),
            )
            if self.bank_excess_coin_step < len(commands):
                command, reason = commands[self.bank_excess_coin_step]
                self.bank_excess_coin_step += 1
                return BotDecision(command, reason)
        returning = self.bank_excess_coin_step >= 3
        routes = (
            {
                "3006": "west",
                "3005": "north",
                "3001": "north",
            }
            if returning
            else {
                "3054": "south",
                "3001": "south",
                "3014": "north",
                "3005": "east",
                "3006": "east",
            }
        )
        command = routes.get(room_vnum)
        if command is not None:
            return BotDecision(
                command,
                "use the safe Midgaard bank route for excess currency",
            )
        if room_vnum == "3054" and returning:
            return None
        self.failure = (
            "no verified excess-currency bank route for "
            f"room {state.room_name!r} ({state.room_vnum})"
        )
        return None

    def _live_maze_navigation_decision(
        self,
        state: CharacterState,
        *,
        context: str,
        target: str,
        allowed_rooms: frozenset[str],
        blocked_rooms: frozenset[str] = frozenset(),
        preferred_destinations: tuple[str, ...] = (),
    ) -> BotDecision | None:
        """Explore a randomized maze using each room's current GMCP exits."""
        if self.live_maze_context != context:
            self.live_maze_context = context
            self.live_maze_target = target
            self.live_maze_allowed_rooms = allowed_rooms
            self.live_maze_visited = set()
            self.live_maze_attempted = {}
            self.live_maze_stack = []
            self.live_maze_backtrack_room = None
            self.live_maze_rebases = 0
            self.live_maze_complete = False

        room_vnum = str(state.room_vnum or "")
        if room_vnum == target:
            self.live_maze_complete = True
            return None
        if room_vnum not in allowed_rooms:
            self.failure = (
                f"live maze navigation reached unregistered room {room_vnum!r} "
                f"while seeking {target}"
            )
            return None
        if self.live_maze_backtrack_room is not None:
            if room_vnum != self.live_maze_backtrack_room:
                self.live_maze_rebases += 1
                if self.live_maze_rebases > 8:
                    self.failure = (
                        "live maze navigation exceeded eight bounded rebases "
                        f"while seeking {target} (last room {room_vnum!r})"
                    )
                    return None
                self.live_maze_visited = {room_vnum}
                self.live_maze_attempted = {}
                self.live_maze_stack = []
            self.live_maze_backtrack_room = None

        self.live_maze_visited.add(room_vnum)
        attempted = self.live_maze_attempted.setdefault(room_vnum, set())
        exits: dict[str, str] = {}
        for raw_direction, destination in state.exits.items():
            if destination is None:
                continue
            direction = _DIRECTION_SHORTCUTS.get(
                str(raw_direction).casefold(),
                str(raw_direction).casefold(),
            )
            if direction in _MOVEMENT_COMMANDS:
                exits[direction] = str(destination)

        directions = (
            "north",
            "east",
            "south",
            "west",
            "up",
            "down",
        )
        preferred = (*preferred_destinations, target)
        for preferred_destination in preferred:
            for direction in directions:
                destination = exits.get(direction)
                if (
                    destination != preferred_destination
                    or destination in blocked_rooms
                    or destination in self.live_maze_visited
                    or direction in attempted
                ):
                    continue
                attempted.add(direction)
                self.live_maze_stack.append((room_vnum, direction, destination))
                return BotDecision(
                    direction,
                    f"follow the live GMCP exit toward maze room {destination}",
                )
        for direction in directions:
            destination = exits.get(direction)
            if (
                destination is None
                or destination not in allowed_rooms
                or destination in blocked_rooms
                or destination in self.live_maze_visited
                or direction in attempted
            ):
                continue
            attempted.add(direction)
            self.live_maze_stack.append((room_vnum, direction, destination))
            return BotDecision(
                direction,
                f"follow the live GMCP exit toward maze room {destination}",
            )

        if not self.live_maze_stack:
            self.failure = (
                f"live maze navigation exhausted registered exits in room "
                f"{room_vnum!r} while seeking {target}"
            )
            return None
        parent_room, direction, child_room = self.live_maze_stack.pop()
        if room_vnum != child_room:
            self.live_maze_rebases += 1
            if self.live_maze_rebases > 8:
                self.failure = (
                    "live maze navigation exceeded eight bounded rebases "
                    f"while seeking {target} (last room {room_vnum!r})"
                )
                return None
            self.live_maze_visited = {room_vnum}
            self.live_maze_attempted = {}
            self.live_maze_stack = []
            return self._live_maze_navigation_decision(
                state,
                context=context,
                target=target,
                allowed_rooms=allowed_rooms,
                blocked_rooms=blocked_rooms,
                preferred_destinations=preferred_destinations,
            )
        self.live_maze_backtrack_room = parent_room
        backtrack_direction = next(
            (
                candidate
                for candidate, destination in exits.items()
                if destination == parent_room
            ),
            None,
        )
        if backtrack_direction is None:
            self.live_maze_rebases += 1
            if self.live_maze_rebases > 8:
                self.failure = (
                    "live maze navigation could not find a live exit back to "
                    f"room {parent_room!r} while seeking {target}"
                )
                return None
            self.live_maze_visited = {room_vnum}
            self.live_maze_attempted = {}
            self.live_maze_stack = []
            self.live_maze_backtrack_room = None
            return self._live_maze_navigation_decision(
                state,
                context=context,
                target=target,
                allowed_rooms=allowed_rooms,
                blocked_rooms=blocked_rooms,
                preferred_destinations=preferred_destinations,
            )
        return BotDecision(
            backtrack_direction,
            f"backtrack through the live maze toward room {parent_room}",
        )

    def _fastwalk_research_decision(self, state: CharacterState) -> BotDecision | None:
        """Exercise an official recall-origin route one command at a time."""
        assert self.fastwalk_route is not None
        room_vnum = state.room_vnum
        room_name = (state.room_name or "").casefold()
        room_key = room_vnum or ""

        if (
            self.fastwalk_returning
            and self.fastwalk_recovery_commands is None
            and room_key in _PYRAMID_DESERT_MAZE_ROOMS
        ):
            maze_return = self._live_maze_navigation_decision(
                state,
                context=f"fastwalk-return:{self.fastwalk_route.name}",
                target="5007",
                allowed_rooms=_PYRAMID_DESERT_MAZE_ROOMS,
                blocked_rooms=frozenset({"5028"}),
            )
            if maze_return is not None:
                return maze_return
            if not self.live_maze_complete:
                return None
            self.fastwalk_recovery_commands = _PYRAMID_HEALER_RETURN_COMMANDS
            self.fastwalk_return_index = 0

        if (
            self.fastwalk_returning
            and self.fastwalk_recovery_commands is None
            and room_key in _SHADOW_GROVE_ROOMS
        ):
            maze_return = self._live_maze_navigation_decision(
                state,
                context=f"fastwalk-return:shadow-grove:{self.fastwalk_route.name}",
                target="1300",
                allowed_rooms=_SHADOW_GROVE_ROOMS,
            )
            if maze_return is not None:
                return maze_return
            if not self.live_maze_complete:
                return None
            self.fastwalk_recovery_commands = _SHADOW_GROVE_HEALER_RETURN_COMMANDS
            self.fastwalk_return_index = 0

        if (
            self.fastwalk_returning
            and self.fastwalk_unattackable_target is not None
        ):
            if room_key == "3737":
                return BotDecision(
                    "enter portal",
                    "leave arena Safety before recalling from an unattackable target",
                )
            if room_key != "3054" and room_key not in _MIDGAARD_HEALER_ROUTES:
                return BotDecision(
                    "recall",
                    "return immediately after the field target was rejected by its current form",
                )

        nested_container = self._nested_container_extraction_decision()
        if nested_container is not None:
            return nested_container

        if (
            self.fastwalk_darkness_detected
            and not self.fastwalk_returning
            and not self.combat_active
        ):
            self.fastwalk_darkness_detected = False
            self.fastwalk_abort_reason = (
                "field route became pitch black without a functioning light"
            )
            self.fastwalk_returning = True
            return BotDecision(
                "recall",
                "leave a dark field route until a functioning light is equipped",
            )

        if (
            self.fastwalk_route.name == "mud-school-accessories"
            and room_key == "3710"
            and self.fastwalk_returning
        ):
            # Recall is prohibited at the obstacle-course endpoint. Rejoin the
            # registered School circuit so its first action enters the portal.
            self.fastwalk_returning = False
            self.fastwalk_recall_started = True
            self.fastwalk_outbound_index = len(self.fastwalk_route.commands)
            self.fastwalk_arrival_observed = True
            self.fastwalk_hunt_stop_index = 0
            self.fastwalk_hunt_move_index = 0
            self.fastwalk_hunt_action_index = 0
            self.fastwalk_hunt_looked = False

        school_resume_indexes = {
            "3711": 0,
            "3721": 1,
            "3712": 2,
            "3715": 4,
            "3716": 5,
        }
        if (
            self.fastwalk_route.name == "mud-school-accessories"
            and not self.fastwalk_returning
            and not self.fastwalk_recall_started
            and room_key in school_resume_indexes
        ):
            self.fastwalk_recall_started = True
            self.fastwalk_outbound_index = len(self.fastwalk_route.commands)
            self.fastwalk_arrival_observed = True
            self.fastwalk_hunt_stop_index = 1
            self.fastwalk_hunt_move_index = school_resume_indexes[room_key]
        elif (
            self.fastwalk_route.name == "mud-school-accessories"
            and not self.fastwalk_returning
            and not self.fastwalk_recall_started
            and room_key == "3710"
        ):
            self.fastwalk_recall_started = True
            self.fastwalk_outbound_index = len(self.fastwalk_route.commands)
            self.fastwalk_arrival_observed = True
            self.fastwalk_hunt_stop_index = 0
            self.fastwalk_hunt_move_index = 0
        elif (
            self.fastwalk_route.name == "mud-school-accessories"
            and not self.fastwalk_returning
            and not self.fastwalk_recall_started
            and room_key == "3720"
        ):
            self.fastwalk_recall_started = True
            self.fastwalk_outbound_index = len(self.fastwalk_route.commands)
            self.fastwalk_arrival_observed = True
            self.fastwalk_hunt_stop_index = 2
        elif (
            self.fastwalk_route.name == "mud-school-accessories"
            and not self.fastwalk_returning
            and not self.fastwalk_recall_started
            and room_key in {"3722", "3723", "3724", "3725"}
        ):
            exit_action_indexes = {
                "3722": 0,
                "3723": 3,
                "3724": 4,
                "3725": 5,
            }
            self.fastwalk_recall_started = True
            self.fastwalk_outbound_index = len(self.fastwalk_route.commands)
            self.fastwalk_arrival_observed = True
            self.fastwalk_hunt_stop_index = len(self.fastwalk_hunt_stops) - 1
            self.fastwalk_hunt_move_index = len(
                self.fastwalk_hunt_stops[-1].route
            )
            self.fastwalk_hunt_looked = True
            self.fastwalk_hunt_action_index = exit_action_indexes[room_key]

        if self.fastwalk_emergency_recall_pending and not self.combat_active:
            return self._fastwalk_emergency_return_decision(state)

        if (
            not self.combat_active
            and self.active_target is None
            and room_key in self.pending_loot_rooms
        ):
            selective_loot_keywords: tuple[str, ...] = ()
            if (
                self.fastwalk_selective_loot
                and self.fastwalk_last_kill_target is not None
                and self.fastwalk_hunt_stop_index < len(self.fastwalk_hunt_stops)
            ):
                current_stop = self.fastwalk_hunt_stops[
                    self.fastwalk_hunt_stop_index
                ]
                if (
                    current_stop.target is not None
                    and _targets_match(
                        self.fastwalk_last_kill_target,
                        current_stop.target,
                    )
                ):
                    selective_loot_keywords = current_stop.selective_loot_keywords
            if self.fastwalk_loot_step == 0:
                if not self.fastwalk_collect_loot:
                    self.fastwalk_loot_step = 4
                    return BotDecision(
                        "sacrifice corpse",
                        "take the field coin while preserving capacity for the next approved kill",
                    )
                if (
                    self.fastwalk_selective_loot
                    and not selective_loot_keywords
                ):
                    self.fastwalk_loot_step = 4
                    return BotDecision(
                        "sacrifice corpse",
                        "skip unapproved loot while autoloot is disabled for a "
                        "known cursed-drop hunt",
                    )
                if (
                    self.fastwalk_selective_loot_index
                    < len(selective_loot_keywords)
                ):
                    keyword = selective_loot_keywords[
                        self.fastwalk_selective_loot_index
                    ]
                    self.fastwalk_selective_loot_index += 1
                    return BotDecision(
                        f"get all.{keyword} corpse",
                        "collect one source-approved drop while leaving the "
                        "known cursed object in the corpse",
                    )
                if selective_loot_keywords:
                    self.fastwalk_loot_step = 1
                else:
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
            loot_ready = (
                self.fastwalk_loot_step == 1
                and self.fastwalk_route.loot_container is None
            ) or self.fastwalk_loot_step == 3
            sanctuary_carrier_killed = (
                self.fastwalk_last_kill_target is not None
                and _targets_match(
                    self.fastwalk_last_kill_target.casefold(),
                    "large hobgoblin",
                )
            )
            if loot_ready and sanctuary_carrier_killed:
                self.fastwalk_loot_step = 7
                return BotDecision(
                    "inventory",
                    "wait for looted emergency potions before cleaning up the corpse",
                )
            if loot_ready or self.fastwalk_loot_step == 7:
                potion_keyword = _known_combat_potion_keyword(state.inventory)
                if (
                    potion_keyword is not None
                    and potion_keyword not in self.fastwalk_pouch_attempted
                ):
                    self.fastwalk_pouch_attempted.add(potion_keyword)
                    return BotDecision(
                        f"put all.{potion_keyword} pouch",
                        "stow identified emergency potions for in-combat access",
                    )
                self.fastwalk_loot_step = 4
                return BotDecision(
                    "sacrifice corpse",
                    "sacrifice the emptied field corpse for its level-band coin",
                )
            self.fastwalk_loot_step = 0
            self.fastwalk_selective_loot_index = 0
            self.fastwalk_pouch_attempted.clear()
            self.pending_loot_rooms.discard(room_key)
            objective_killed = (
                self.fastwalk_requested_target is not None
                and self.fastwalk_last_kill_target is not None
                and _targets_match(
                    self.fastwalk_last_kill_target,
                    self.fastwalk_requested_target,
                )
            )
            next_stop_index = self.fastwalk_hunt_stop_index + 1
            next_stop = (
                self.fastwalk_hunt_stops[next_stop_index]
                if next_stop_index < len(self.fastwalk_hunt_stops)
                else None
            )
            kill_budget_remaining = (
                self.fastwalk_kill_limit is None
                or len(self.completed_kills) < self.fastwalk_kill_limit
            )
            healthy_for_next_stop = (
                next_stop is not None
                and kill_budget_remaining
                and _health_ratio(state) >= next_stop.minimum_health_ratio
            )
            incidental_kill = bool(
                self.fastwalk_hunt_stops
                and self.fastwalk_last_kill_target is not None
                and not objective_killed
            )
            low_reserve_after_loot = (
                (_health_ratio(state) < 0.8 and not healthy_for_next_stop)
                or _mana_ratio(state) < 0.3
            )
            if (
                incidental_kill
                and self.fastwalk_route.recall_after_loot
                and not self.fastwalk_arrival_observed
                and low_reserve_after_loot
            ):
                self.fastwalk_abort_reason = (
                    "field route withdrew before its endpoint after incidental "
                    f"{self.fastwalk_last_kill_target!r} kill left an "
                    "insufficient health or mana reserve"
                )
            self.fastwalk_recall_after_loot = (
                self.fastwalk_route.recall_after_loot
                and (
                    (
                        not self.fastwalk_hunt_stops
                        and objective_killed
                    )
                    or low_reserve_after_loot
                )
            )
            if not objective_killed and self.fastwalk_last_kill_target is not None:
                self.fastwalk_attack_target = self.fastwalk_requested_target
                self.fastwalk_attack_started = False
                self.consider_target = None
                self.consider_target_selector = None
                self.consider_viable = None
            self.fastwalk_last_kill_target = None
            return BotDecision(
                "inventory",
                "record loot before choosing whether to continue or recall",
            )

        if not self.fastwalk_returning:
            if (
                self.fastwalk_hunt_stops
                and room_key == "3054"
                and not self.fastwalk_recovery_ready
                and not self.fastwalk_returning
                and state.max_move is not None
            ):
                required_move_ratio = 0.4 if (
                    _has_named_affect(state.affects, "fly")
                    or _has_named_affect(state.affects, "levitation")
                ) else 0.9
                if self.fastwalk_required_move:
                    required_move_ratio = max(
                        required_move_ratio,
                        min(
                            1.0,
                            self.fastwalk_required_move / state.max_move,
                        ),
                    )
                if _move_ratio(state) < required_move_ratio:
                    if _is_sleeping(state):
                        self.prompt_ready = False
                        return None
                    return BotDecision(
                        "sleep",
                        "sleep beside the Midgaard healer before a long field departure",
                    )
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
                    *_MIDGAARD_CITY_HEALER_ROOMS,
                    "3054",
                    "3009",
                }:
                    origin_routes = {
                        **_MIDGAARD_HEALER_ROUTES,
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
            if (
                self.fastwalk_outbound_index == 0
                and room_vnum != "3001"
                and not (
                    self.fastwalk_hunt_stops
                    and room_vnum == "3005"
                    and 1 <= self.fastwalk_water_preflight_step <= 3
                )
            ):
                recovery_routes = {
                    "3054": "south",
                    "3725": "down",
                    "3724": "down",
                }
                direction = recovery_routes.get(room_vnum or "")
                if direction is not None:
                    return BotDecision(
                        direction,
                        "return from safe recovery to the fastwalk recall origin",
                    )
                self.failure = (
                    "recall did not reach the Midgaard Temple before fastwalk "
                    f"{self.fastwalk_route.name!r}"
                )
                return None
            if (
                self.audit_combat_pouch
                and room_vnum == "3001"
                and not self.fastwalk_pouch_audited
            ):
                if not self.fastwalk_pouch_audit_pending:
                    self.fastwalk_pouch_audit_pending = True
                    return BotDecision(
                        "look in pouch",
                        "audit identified emergency potions before field departure",
                    )
                pouch_text = _ANSI_ESCAPE.sub("", self.last_response).casefold()
                self.combat_pouch_potions = Counter(
                    {
                        keyword: pouch_text.count(f"a {keyword} potion")
                        for keyword in ("black", "purple")
                        if f"a {keyword} potion" in pouch_text
                    }
                )
                self.fastwalk_pouch_audit_pending = False
                self.fastwalk_pouch_audited = True
            loose_potion = _known_combat_potion_keyword(state.inventory)
            if (
                loose_potion is not None
                and loose_potion not in self.fastwalk_pouch_attempted
            ):
                self.fastwalk_pouch_attempted.add(loose_potion)
                return BotDecision(
                    f"put all.{loose_potion} pouch",
                    "move confirmed loose emergency potions into the worn pouch",
                )
            if (
                room_vnum == "3001"
                and self.fastwalk_outbound_index == 0
                and not self.fastwalk_capacity_preflight_complete
            ):
                carry_weight = _state_stat(state, "carry_wt")
                maximum_weight = _state_stat(state, "maxcarry_wt")
                if carry_weight is None or maximum_weight is None:
                    self.fastwalk_abort_reason = (
                        "required-loot capacity preflight lacked carrying statistics"
                    )
                    self.fastwalk_returning = True
                    return BotDecision(
                        "north",
                        "return to the healer when required-loot capacity is unknown",
                    )
                free_weight = maximum_weight - carry_weight
                if (
                    self.fastwalk_xp_first_capacity_threshold > 0
                    and free_weight < self.fastwalk_xp_first_capacity_threshold
                ):
                    self.fastwalk_collect_loot = False
                    self.fastwalk_capacity_preflight_complete = True
                elif free_weight >= self.fastwalk_required_free_weight:
                    self.fastwalk_capacity_preflight_complete = True
                else:
                    pie_count = sum(
                        "pie" in description.casefold()
                        for description in _inventory_descriptions(state.inventory)
                    )
                    if pie_count > 2:
                        return BotDecision(
                            "donate pie",
                            "trade one replaceable excess pie for required field-loot "
                            "capacity while preserving a food reserve",
                        )
                    self.fastwalk_abort_reason = (
                        "required field loot exceeded carrying capacity without "
                        "replaceable excess food"
                    )
                    self.fastwalk_returning = True
                    return BotDecision(
                        "north",
                        "return to the healer rather than discard protected supplies",
                    )
            if (
                room_vnum == "3001"
                and self.fastwalk_outbound_index == 0
                and (self.fastwalk_attack_target or self.fastwalk_hunt_stops)
                and not self.fastwalk_autoloot_configured
            ):
                self.fastwalk_autoloot_configured = True
                return BotDecision(
                    "config +autoloot"
                    if (
                        self.fastwalk_collect_loot
                        and not self.fastwalk_selective_loot
                    )
                    else "config -autoloot",
                    "secure corpse loot inside the kill before another mobile can interrupt"
                    if (
                        self.fastwalk_collect_loot
                        and not self.fastwalk_selective_loot
                    )
                    else (
                        "leave a source-known cursed drop in its corpse and "
                        "collect only approved items manually"
                        if self.fastwalk_selective_loot
                        else "preserve carrying capacity for a second approved field kill"
                    ),
                )
            if (
                room_vnum == "3001"
                and self.fastwalk_outbound_index == 0
                and (self.fastwalk_attack_target or self.fastwalk_hunt_stops)
                and not self.fastwalk_targetmode_configured
            ):
                self.fastwalk_targetmode_configured = True
                return BotDecision(
                    "config +targetmode",
                    "enable exact live mobile selectors before field targeting",
                )
            if room_vnum == "3001" and self.fastwalk_outbound_index == 0:
                junk_disposal = self._fastwalk_junk_disposal_decision(state)
                if junk_disposal is not None:
                    return junk_disposal
            if (
                room_vnum == "3001"
                and self.fastwalk_outbound_index == 0
                and self.gear_catalog is not None
                and not self.fastwalk_container_audited
            ):
                self.fastwalk_container_audited = True
                return BotDecision(
                    "inventory",
                    "audit container separation before field departure",
                )
            if room_vnum == "3001" and self.fastwalk_outbound_index == 0:
                readiness = self._fastwalk_carried_gear_readiness_decision(state)
                if readiness is not None:
                    return readiness
            if room_vnum == "3001" and self.fastwalk_outbound_index == 0:
                mitigation = self._fastwalk_caster_mitigation_decision(state)
                if mitigation is not None:
                    return mitigation
            if room_vnum == "3001" and self.fastwalk_outbound_index == 0:
                for skill in ("sneak",):
                    if (
                        skill in self.known_skills
                        and skill not in self.fastwalk_concealment_attempted
                    ):
                        self.fastwalk_concealment_attempted.add(skill)
                        return BotDecision(
                            skill,
                            "reduce visibility to city greet-program ambushes before departure",
                        )
            if (
                self.fastwalk_hunt_stops
                and self.fastwalk_outbound_index == 0
                and self.fastwalk_water_preflight_step < 4
            ):
                water_preflight = {
                    (0, "3001"): (
                        1,
                        "south",
                        "reach the Temple Square fountain",
                    ),
                    (1, "3005"): (
                        2,
                        "fill skin",
                        "fill the buffalo water skin before the field route",
                    ),
                    (2, "3005"): (
                        3,
                        "drink skin",
                        "drink before beginning the field route",
                    ),
                    (3, "3005"): (
                        4,
                        "north",
                        "return to recall after replenishing water",
                    ),
                }.get((self.fastwalk_water_preflight_step, room_key))
                if water_preflight is not None:
                    step, command, reason = water_preflight
                    self.fastwalk_water_preflight_step = step
                    return BotDecision(command, reason)
            while self.fastwalk_origin_action_index < len(
                self.fastwalk_origin_actions
            ):
                command = self.fastwalk_origin_actions[
                    self.fastwalk_origin_action_index
                ]
                self.fastwalk_origin_action_index += 1
                if command == "eat pie":
                    food_keyword = _inventory_food_keyword(
                        state.inventory,
                        self.gear_catalog,
                    )
                    if not self.needs_food or food_keyword is None:
                        continue
                    command = f"eat {food_keyword}"
                if (
                    command == "drink skin"
                    and not self.needs_drink
                    and (
                        not self.fastwalk_hunt_stops
                        or self.fastwalk_water_preflight_step >= 4
                    )
                ):
                    continue
                return BotDecision(
                    command,
                    "prepare inventory at the safe fastwalk origin",
                )
            live_navigation_active = (
                self.fastwalk_route.live_navigation_target is not None
                and self.fastwalk_route.live_navigation_start_index is not None
                and self.fastwalk_route.live_navigation_resume_index is not None
                and self.fastwalk_outbound_index
                == self.fastwalk_route.live_navigation_start_index
            )
            if live_navigation_active:
                live_navigation = self._live_maze_navigation_decision(
                    state,
                    context=f"fastwalk-outbound:{self.fastwalk_route.name}",
                    target=self.fastwalk_route.live_navigation_target or "",
                    allowed_rooms=frozenset(
                        self.fastwalk_route.live_navigation_room_vnums
                    ),
                    blocked_rooms=frozenset(
                        self.fastwalk_route.live_navigation_blocked_room_vnums
                    ),
                    preferred_destinations=(
                        self.fastwalk_route.live_navigation_preferred_destinations
                    ),
                )
                if live_navigation is not None:
                    return live_navigation
                if not self.live_maze_complete:
                    return None
                self.fastwalk_outbound_index = (
                    self.fastwalk_route.live_navigation_resume_index
                )
            route_preflight = self._fastwalk_route_preflight_decision(state)
            if route_preflight is not None:
                return route_preflight
            if self.fastwalk_outbound_index < len(self.fastwalk_route.commands):
                invisibility = self._fastwalk_invisibility_decision(
                    state,
                    failure_command="south",
                    failure_reason="return safely after invisibility preparation failed",
                    cast_reason=(
                        "establish invisibility before following "
                        f"{self.fastwalk_route.name}"
                    ),
                    abort_reason=(
                        "field expedition could not establish invisibility at "
                        "the safe origin"
                    ),
                )
                if invisibility is not None:
                    return invisibility
                if self.fastwalk_invisibility_pending:
                    self.prompt_ready = False
                    return None
                if self.fastwalk_outbound_index == 0:
                    self.fastwalk_recovery_ready = False
                command = self.fastwalk_route.commands[self.fastwalk_outbound_index]
                self.fastwalk_outbound_index += 1
                return BotDecision(command, f"follow official fastwalk {self.fastwalk_route.name}")
            if not self.fastwalk_arrival_observed:
                self.fastwalk_arrival_observed = True
                return BotDecision("look", "record the official fastwalk endpoint")
            if self.fastwalk_hunt_stops:
                if not self.fastwalk_hunt_preflight_food_attempted:
                    self.fastwalk_hunt_preflight_food_attempted = True
                    food_keyword = _inventory_food_keyword(
                        state.inventory,
                        self.gear_catalog,
                    )
                    if self.needs_food and food_keyword is not None:
                        return BotDecision(
                            f"eat {food_keyword}",
                            "address hunger before beginning the field circuit",
                        )
                return self._fastwalk_hunt_plan_decision(state)
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
                    return self._combat_opener_decision(
                        self.fastwalk_attack_target or "",
                        "re-engage the requested target after bounded pursuit",
                        allow_backstab=False,
                        state=state,
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
                return self._consider_fastwalk_target(state)
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
            return None
        if room_vnum == "3724":
            return BotDecision("down", "leave General Supplies after fastwalk recovery")
        if room_vnum == "3725":
            return BotDecision("down", "leave the Mud School after fastwalk recovery")
        healer_direction = _MIDGAARD_HEALER_ROUTES.get(room_vnum or "")
        if healer_direction is not None:
            return BotDecision(
                healer_direction,
                "finish the fastwalk at the Midgaard healer",
            )

        if self.fastwalk_recovery_commands is not None:
            if self.fastwalk_return_index >= len(self.fastwalk_recovery_commands):
                self.failure = (
                    "no-recall recovery route did not reach the Midgaard healer "
                    f"from room {state.room_name!r} ({state.room_vnum})"
                )
                return None
            command = self.fastwalk_recovery_commands[self.fastwalk_return_index]
            self.fastwalk_return_index += 1
            return BotDecision(
                command,
                "follow the source-backed no-recall route to the Midgaard healer",
            )

        if self.fastwalk_route.recall_after_loot:
            self.failure = (
                "recall-only fastwalk did not reach the Midgaard healer route "
                f"from room {state.room_name!r} ({state.room_vnum})"
            )
            return None
        reverse = _reverse_fastwalk_commands(self.fastwalk_route.commands)
        if self.fastwalk_return_index >= len(reverse):
            self.failure = (
                "fastwalk return did not reach the Midgaard healer route from "
                f"room {state.room_name!r} ({state.room_vnum})"
            )
            return None
        command = reverse[self.fastwalk_return_index]
        self.fastwalk_return_index += 1
        return BotDecision(command, "reverse the official fastwalk after recall failed")

    def _active_route_preflight_hazard(
        self,
        state: CharacterState,
    ) -> str | None:
        """Return a live hard route hazard currently engaging the bot."""
        route = self.fastwalk_route
        if route is None:
            return None
        targets: list[str] = list(route.route_hard_hazard_targets)
        if route.route_preflight_hard_hazard and route.route_preflight_target:
            targets.append(route.route_preflight_target)
        if not targets:
            return None
        candidates: list[str] = []
        for candidate in (self.active_target, self.unapproved_field_attacker):
            if candidate:
                candidates.append(candidate)
        for enemy in _enemy_records(state.enemies):
            name = enemy.get("name")
            if isinstance(name, str) and name.strip():
                candidates.append(name)
        for target in targets:
            if any(_targets_match(candidate, target) for candidate in candidates):
                return target
        return None

    def _fastwalk_route_preflight_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        """Check source-registered hazards before a route crosses their room."""
        route = self.fastwalk_route
        if (
            route is None
            or self.fastwalk_route_preflight_complete
            or self.fastwalk_returning
            or route.route_preflight_room_vnum is None
            or route.route_preflight_command is None
            or str(state.room_vnum or "")
            != str(route.route_preflight_room_vnum)
        ):
            return None
        if self.fastwalk_route_preflight_hazard_observed:
            target = route.route_preflight_target or "unknown hazard"
            source_level_range = self.source_mobile_level_ranges.get(
                target.casefold()
            )
            if source_level_range is None:
                source_level_range = self._source_mobile_level_range(target)
            if (
                not route.route_preflight_hard_hazard
                and
                source_level_range is not None
                and source_level_range[1] <= int(state.level) - 5
            ):
                # A source-confirmed mobile at least five levels below the
                # character is not a useful XP target or an unsafe crowd.
                self.fastwalk_route_preflight_complete = True
                self.fastwalk_route_preflight_hazard_observed = False
                return None
            self.fastwalk_route_preflight_complete = True
            self.fastwalk_abort_reason = (
                "field route preflight found source-registered hazard "
                f"{target!r} in room {route.route_preflight_room_vnum}"
            )
            self.fastwalk_returning = True
            return BotDecision(
                "recall",
                "return before entering a live source-registered route hazard",
            )
        if not self.fastwalk_route_preflight_issued:
            self.fastwalk_route_preflight_issued = True
            return BotDecision(
                route.route_preflight_command,
                "check the source-registered route hazard before crossing the area boundary",
            )
        self.fastwalk_route_preflight_complete = True
        return None

    @property
    def fastwalk_objective_killed(self) -> bool:
        if self.fastwalk_requested_target is None and not self.fastwalk_hunt_stops:
            return True
        return bool(self.objective_kills)

    @property
    def objective_kills(self) -> list[dict[str, Any]]:
        """Return deliberate fastwalk targets, excluding route interruptions."""
        if self.fastwalk_requested_target is None:
            if self.fastwalk_hunt_stops:
                targets = tuple(
                    stop.target
                    for stop in self.fastwalk_hunt_stops
                    if stop.target is not None
                )
                return [
                    kill
                    for kill in self.completed_kills
                    if any(
                        _targets_match(str(kill.get("mob_name", "")), target)
                        for target in targets
                    )
                ]
            return list(self.completed_kills)
        return [
            kill
            for kill in self.completed_kills
            if _targets_match(
                str(kill.get("mob_name", "")), self.fastwalk_requested_target
            )
        ]

    @property
    def _is_noncombat_utility_run(self) -> bool:
        return not (
            self.course_started and not self.course_complete
        ) and any(
            (
                self.liquidate_loot,
                self.city_restock,
                self.city_rearm,
                self.city_outfit,
                self.guildmaster_research,
                self.magic_shop_research,
                self.flight_borrowing,
                self.bank_excess_coins,
                self.resupply_only,
            )
        )

    def _has_persisted_below_band_sighting(
        self,
        state: CharacterState,
        stop: FieldHuntStop,
    ) -> bool:
        if stop.target is None:
            return False
        # A required-loot hunt gets one controlled attempt against its
        # source-registered carrier even when the first consider result was
        # persisted as below-band. Ordinary XP hunts retain the terminal skip.
        if (
            stop.allow_below_band_for_required_loot
            and stop.required_items
            and _missing_required_inventory_items(state.inventory, stop.required_items)
        ):
            return False
        room_vnum = str(state.room_vnum or self.current_room or "")
        return any(
            sighting_room == room_vnum
            and _stop_target_matches(sighting_target, stop.target, stop)
            for sighting_room, sighting_target in self.fastwalk_below_band_sightings
        )

    def _consider_fastwalk_target(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        """Use DD4's consider bands before committing a field hunt."""
        assert self.fastwalk_attack_target is not None
        target = self.fastwalk_attack_target
        stop = (
            self.fastwalk_hunt_stops[self.fastwalk_hunt_stop_index]
            if self.fastwalk_hunt_stop_index < len(self.fastwalk_hunt_stops)
            else None
        )
        command_keyword = stop.command_keyword if stop is not None else None
        target_count = sum(
            count
            for observed, count in self.room_target_counts.get(
                self.current_room or "", {}
            ).items()
            if _stop_target_matches(observed, target, stop)
        )
        allowed_bystanders = (
            self.fastwalk_hunt_stops[self.fastwalk_hunt_stop_index].allowed_bystanders
            if self.fastwalk_hunt_stop_index < len(self.fastwalk_hunt_stops)
            else ()
        )
        trivial_bystanders = (
            self.fastwalk_hunt_stops[
                self.fastwalk_hunt_stop_index
            ].trivial_bystanders
            if self.fastwalk_hunt_stop_index < len(self.fastwalk_hunt_stops)
            else ()
        )
        consider_only = (
            self.fastwalk_hunt_stops[self.fastwalk_hunt_stop_index].consider_only
            if self.fastwalk_hunt_stop_index < len(self.fastwalk_hunt_stops)
            else False
        )
        observed_mobile_count = sum(
            count
            for observed, count in self.room_target_counts.get(
                self.current_room or "", {}
            ).items()
            if self.gear_catalog is None
            or self.gear_catalog.match(observed) is None
            if not any(
                _targets_match(observed, bystander)
                for bystander in allowed_bystanders + trivial_bystanders
            )
            if not self._source_mobile_name_is_known_below_useful_band(
                observed,
                state.level,
            )
        )
        keyword_match_count = sum(
            count
            for observed, count in self.room_target_counts.get(
                self.current_room or "", {}
            ).items()
            if _target_keyword(observed).casefold()
            == _target_keyword(target).casefold()
        )
        ambiguous_keyword = keyword_match_count > target_count
        maximum_target_count = stop.maximum_target_count if stop is not None else 1
        if (
            (not consider_only and target_count > maximum_target_count)
            or (consider_only and ambiguous_keyword)
            or (not consider_only and observed_mobile_count > target_count)
            or (
                stop is not None
                and stop.require_isolated
                and observed_mobile_count > target_count
            )
        ):
            crowd_reason = (
                f"field room contained {observed_mobile_count} observed mobiles "
                f"while evaluating {target!r}"
            )
            # A crowded room is a retryable area-state miss, not evidence that
            # the requested mobile is absent from the area.
            self.fastwalk_target_absent = False
            if self.fastwalk_hunt_stops:
                if len(self.fastwalk_hunt_stops) == 1:
                    self.fastwalk_abort_reason = crowd_reason
                self.fastwalk_hunt_stop_skipped = True
                self.fastwalk_attack_started = False
                return BotDecision(
                    "look",
                    "skip a crowded circuit target before committing to combat",
                )
            self.fastwalk_abort_reason = crowd_reason
            self.fastwalk_returning = True
            return BotDecision(
                "recall",
                "withdraw after finding a crowded field room",
            )
        if self.consider_target != target:
            self.consider_target = target
            self.consider_target_selector = self._target_selector_for(target, stop)
            self.consider_viable = None
            self.consider_level_offset_ceiling = None
            return BotDecision(
                f"consider "
                f"{self.consider_target_selector or command_keyword or _target_keyword(target)}",
                "consider the field target before committing to combat",
            )
        if self.consider_viable is True:
            source_level_range = self._source_mobile_level_range(target, stop)
            live_target_levels = [
                level
                for enemy in _enemy_records(state.enemies)
                if _targets_match(str(enemy.get("name", "")), target)
                if (level := _int_or_none(enemy.get("level"))) is not None
            ]
            if (
                stop is not None
                and stop.maximum_level_offset is not None
                and state.level is not None
                and source_level_range is not None
                and not live_target_levels
                and (
                    self.consider_level_offset_ceiling is None
                    or self.consider_level_offset_ceiling
                    > stop.maximum_level_offset
                )
                and source_level_range[1] > state.level + stop.maximum_level_offset
            ):
                self.fastwalk_abort_reason = (
                    f"source mobile range {source_level_range[0]}-"
                    f"{source_level_range[1]} for {target!r} exceeds the "
                    f"pre-combat ceiling of character level plus "
                    f"{stop.maximum_level_offset}"
                )
                self.fastwalk_hunt_stop_skipped = True
                self.fastwalk_attack_started = False
                return BotDecision(
                    "look",
                    "skip a target whose source-fuzzed level can exceed the "
                    "pre-combat ceiling",
                )
            if (
                stop is not None
                and stop.maximum_level_offset is not None
                and state.level is not None
                and any(
                    level > state.level + stop.maximum_level_offset
                    for level in live_target_levels
                )
            ):
                self.fastwalk_abort_reason = (
                    f"live level for {target!r} exceeded the stop ceiling of "
                    f"character level plus {stop.maximum_level_offset}"
                )
                self.fastwalk_hunt_stop_skipped = True
                self.fastwalk_attack_started = False
                return BotDecision(
                    "look",
                    "skip a circuit target above its verified live level ceiling",
                )
            self.fastwalk_attack_started = True
            self.active_target = target
            self.active_target_selector = (
                self.consider_target_selector
                or self._target_selector_for(target, stop)
            )
            self.combat_active = True
            return self._combat_opener_decision(
                target,
                "attack the considered viable fastwalk target",
                command_keyword=command_keyword,
                state=state,
            )
        if self.consider_viable is False:
            below_band_required_loot = bool(
                stop is not None
                and stop.allow_below_band_for_required_loot
                and stop.required_items
                and _missing_required_inventory_items(
                    state.inventory,
                    stop.required_items,
                )
                and any(
                    fragment in self.last_response.casefold()
                    for fragment in _CONSIDER_BELOW_BAND_FRAGMENTS
                )
            )
            if below_band_required_loot:
                self.fastwalk_attack_started = True
                self.active_target = target
                self.active_target_selector = (
                    self.consider_target_selector
                    or self._target_selector_for(target, stop)
                )
                self.combat_active = True
                return self._combat_opener_decision(
                    target,
                    "attack a source-registered below-band carrier solely for "
                    "required replacement gear, not XP",
                    command_keyword=command_keyword,
                    state=state,
                )
            if stop is not None and stop.abort_after_consider_rejection:
                self.fastwalk_abort_reason = (
                    f"the unique field target {target!r} failed its live "
                    "consider gate"
                )
                self.fastwalk_hunt_stop_skipped = True
                self.fastwalk_attack_started = False
                self.fastwalk_returning = True
                return BotDecision(
                    "recall",
                    "return after the unique field target fails its live "
                    "consider gate",
                )
            self.fastwalk_target_absent = True
            if self.fastwalk_hunt_stops:
                self.fastwalk_hunt_stop_skipped = True
                self.fastwalk_attack_started = False
                return BotDecision(
                    "look",
                    "skip an unsuitable circuit target before continuing",
                )
            self.fastwalk_returning = True
            return BotDecision(
                "recall",
                "withdraw after considering the field target unsuitable",
            )
        return None

    def _combat_pouch_potion_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        """Use only source-identified emergency potions from the worn pouch."""
        health_ratio = _health_ratio(state)
        if self.combat_pouch_potions["black"] and health_ratio <= 0.55:
            self.combat_pouch_potions["black"] -= 1
            if self.combat_pouch_potions["black"] <= 0:
                del self.combat_pouch_potions["black"]
            return BotDecision(
                "quaff black",
                "use the identified cure-critical potion at low combat health",
            )
        if (
            self.use_sanctuary_potions
            and self.combat_pouch_potions["purple"]
            and not _has_named_affect(state.affects, "sanctuary")
            and (
                not self.active_target
                or self.active_target.casefold()
                not in self.fastwalk_below_band_targets
            )
        ):
            self.combat_pouch_potions["purple"] -= 1
            if self.combat_pouch_potions["purple"] <= 0:
                del self.combat_pouch_potions["purple"]
            return BotDecision(
                "quaff purple",
                "use the identified sanctuary potion before taking avoidable combat damage",
            )
        return None

    def _fastwalk_hunt_plan_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        missing_food = (
            self.needs_food
            and not self.fastwalk_defer_provision_resupply
            and (
                self.food_unavailable
                or not _has_inventory_food(state.inventory, self.gear_catalog)
            )
        )
        missing_water = (
            self.needs_drink
            and (
                self.water_unavailable
                or not _has_inventory_item(state.inventory, "water skin")
            )
        )
        current_stop = (
            self.fastwalk_hunt_stops[self.fastwalk_hunt_stop_index]
            if self.fastwalk_hunt_stop_index < len(self.fastwalk_hunt_stops)
            else None
        )
        must_take_no_recall_exit = bool(
            current_stop is not None
            and current_stop.target is None
            and "no_recall" in state.room_flags
            and any(
                command.casefold() == "enter portal"
                for command in current_stop.actions[self.fastwalk_hunt_action_index :]
            )
        )
        if (
            current_stop is not None
            and current_stop.target is not None
            and self.fastwalk_unattackable_target is not None
            and _targets_match(
                current_stop.target,
                self.fastwalk_unattackable_target,
            )
        ):
            self.fastwalk_hunt_stop_skipped = True
        nested_container = self._nested_container_extraction_decision()
        if nested_container is not None:
            return nested_container
        if (
            not must_take_no_recall_exit
            and (
                missing_food
                or missing_water
                or _health_ratio(state) < _FIELD_CONTINUE_HEALTH_RATIO
                or _mana_ratio(state) < _FIELD_CONTINUE_MANA_RATIO
                or _move_ratio(state) < _FIELD_CONTINUE_MOVE_RATIO
            )
        ):
            local_recovery_allowed = bool(
                current_stop is not None
                and self.fastwalk_hunt_stop_killed
                and current_stop.allow_local_recovery
                and not missing_food
                and not missing_water
                and not _has_named_affect(state.affects, "blindness")
                and not _has_named_affect(state.affects, "poison")
                and _mana_ratio(state) >= _FIELD_CONTINUE_MANA_RATIO
                and _move_ratio(state) >= _FIELD_CONTINUE_MOVE_RATIO
            )
            if local_recovery_allowed:
                self.waiting_for_heal = True
                return BotDecision(
                    "sleep",
                    "recover in the source-vetted hunt room before continuing",
                )
            resource_gaps = []
            if missing_food:
                resource_gaps.append("food")
            if missing_water:
                resource_gaps.append("water")
            if resource_gaps:
                self.fastwalk_abort_reason = (
                    "field expedition withdrew before target evaluation because "
                    + " and ".join(resource_gaps)
                    + " reserve was unavailable"
                )
            missing_items = self._missing_required_field_items(state)
            if missing_items:
                self.fastwalk_abort_reason = (
                    "field expedition withdrew before acquiring required item(s): "
                    + ", ".join(missing_items)
                )
            self.fastwalk_returning = True
            return BotDecision(
                "recall",
                "end the field circuit while recovery reserves remain",
            )

        rejected_opener_target = (
            self.backstab_skip_once_target or self.shoot_skip_once_target
        )
        if (
            current_stop is not None
            and current_stop.target is not None
            and rejected_opener_target == current_stop.target
            and self.fastwalk_attack_started
            and not self.combat_active
        ):
            self.active_target = current_stop.target
            self.combat_active = True
            return self._combat_opener_decision(
                current_stop.target,
                "start direct combat after the specialized opener was rejected",
                command_keyword=current_stop.command_keyword,
                state=state,
            )

        if (
            self.fastwalk_hunt_stop_killed
            and self.fastwalk_kill_limit is not None
            and len(self.completed_kills) >= self.fastwalk_kill_limit
        ):
            self.fastwalk_returning = True
            return BotDecision(
                "recall",
                f"return after the bounded {self.fastwalk_kill_limit}-kill field segment",
            )

        if self.fastwalk_hunt_stop_killed:
            junk_disposal = self._fastwalk_junk_disposal_decision(state)
            if junk_disposal is not None:
                return junk_disposal

        carry_weight = _state_stat(state, "carry_wt")
        maximum_weight = _state_stat(state, "maxcarry_wt")
        if (
            self.completed_kills
            and carry_weight is not None
            and maximum_weight is not None
            and maximum_weight - carry_weight < 5
        ):
            self.fastwalk_returning = True
            return BotDecision(
                "recall",
                "return before another field drop exceeds the remaining carry capacity",
            )

        if not self.fastwalk_shop_visible_action_pending:
            invisibility = self._fastwalk_invisibility_decision(
                state,
                failure_command="recall",
                failure_reason="return safely after field invisibility could not be restored",
                cast_reason="restore invisibility before moving to the next circuit stop",
                abort_reason="field expedition could not restore invisibility",
            )
            if invisibility is not None:
                return invisibility
            if self.fastwalk_invisibility_pending:
                self.prompt_ready = False
                return None

        if (
            self.fastwalk_pursuit_direction is not None
        ):
            stop = self.fastwalk_hunt_stops[self.fastwalk_hunt_stop_index]
            direction = self.fastwalk_pursuit_direction
            if self.fastwalk_pursuit_steps >= stop.maximum_pursuit_steps:
                self.fastwalk_abort_reason = (
                    f"bounded pursuit of {stop.target!r} reached "
                    f"{stop.maximum_pursuit_steps} step(s)"
                )
                self.fastwalk_pursuit_direction = None
                self.fastwalk_returning = True
                return BotDecision(
                    "recall",
                    "return after the bounded target pursuit was exhausted",
                )
            destination = _exit_destination(state.exits, direction)
            if (
                stop.pursuit_room_vnums
                and destination not in stop.pursuit_room_vnums
            ):
                self.fastwalk_abort_reason = (
                    f"pursuit of {stop.target!r} toward {direction} would enter "
                    f"unregistered room {destination or 'unknown'}"
                )
                self.fastwalk_pursuit_direction = None
                self.fastwalk_returning = True
                return BotDecision(
                    "recall",
                    "decline a fleeing target's unregistered pursuit room",
                )
            self.fastwalk_pursuit_direction = None
            self.fastwalk_pursuit_steps += 1
            self.fastwalk_hunt_looked = False
            return BotDecision(
                direction,
                "follow the observed departing target once for a fresh safety check",
            )

        if self.fastwalk_hunt_stop_killed or self.fastwalk_hunt_stop_skipped:
            completed_stop = self.fastwalk_hunt_stops[
                self.fastwalk_hunt_stop_index
            ]
            if (
                self.fastwalk_hunt_stop_killed
                and not _missing_required_inventory_items(
                    state.inventory,
                    completed_stop.required_items,
                )
                and self.fastwalk_hunt_post_action_index
                < len(completed_stop.post_actions)
            ):
                command = completed_stop.post_actions[
                    self.fastwalk_hunt_post_action_index
                ]
                self.fastwalk_hunt_post_action_index += 1
                return BotDecision(
                    command,
                    "equip and verify required field loot before completing the stop",
                )
            self.fastwalk_hunt_stop_index += 1
            self.fastwalk_hunt_move_index = 0
            self.fastwalk_hunt_action_index = 0
            self.fastwalk_hunt_post_action_index = 0
            self.fastwalk_hunt_looked = False
            self.fastwalk_hunt_stop_killed = False
            self.fastwalk_hunt_stop_skipped = False
            self.fastwalk_attack_started = False
            self.fastwalk_target_absent = False
            self.fastwalk_where_target_absent_observed = False
            self.consider_target = None
            self.consider_target_selector = None
            self.consider_viable = None
            next_stop = (
                self.fastwalk_hunt_stops[self.fastwalk_hunt_stop_index]
                if self.fastwalk_hunt_stop_index < len(self.fastwalk_hunt_stops)
                else None
            )
            self.fastwalk_hunt_route_before_target = bool(
                next_stop is not None
                and completed_stop.target is not None
                and next_stop.target is not None
                and _targets_match(completed_stop.target, next_stop.target)
                and (next_stop.route_vnums or next_stop.route)
            )

        if self.fastwalk_hunt_stop_index >= len(self.fastwalk_hunt_stops):
            if (
                not self.objective_kills
                and not self.fastwalk_consider_outcomes
                and not str(self.fastwalk_abort_reason or "").startswith(
                    "field room contained "
                )
            ):
                self.fastwalk_target_absent = True
            self.fastwalk_returning = True
            if state.room_vnum == "3054":
                return None
            return BotDecision("recall", "return after completing the field circuit")

        stop = self.fastwalk_hunt_stops[self.fastwalk_hunt_stop_index]
        if (
            not must_take_no_recall_exit
            and _health_ratio(state) < stop.minimum_health_ratio
        ):
            self.fastwalk_returning = True
            return BotDecision(
                "recall",
                "skip the next field target without its required health reserve",
            )
        self.fastwalk_attack_target = stop.target
        targets = self.room_targets.get(state.room_vnum or "", [])
        route_vnum_count = len(stop.route_vnums)
        route_command_index = max(
            0,
            self.fastwalk_hunt_move_index - route_vnum_count,
        )
        route_length = route_vnum_count + len(stop.route)
        if (
            (
                not self.fastwalk_hunt_route_before_target
                or self.fastwalk_hunt_move_index >= route_length
            )
            and stop.target is not None
            and any(
                _stop_target_matches(target, stop.target, stop)
                for target in targets
            )
        ):
            if self._has_persisted_below_band_sighting(state, stop):
                self.fastwalk_hunt_stop_skipped = True
                self.fastwalk_attack_started = False
                return BotDecision(
                    "look",
                    "skip the same field mobile after its persisted below-band consider result",
                )
            if (
                stop.consider_only
                and self.consider_target == stop.target
                and self.consider_viable is not None
            ):
                self.fastwalk_hunt_stop_skipped = True
                return BotDecision(
                    "look",
                    "record live consideration without engaging the research target",
                )
            return self._consider_fastwalk_target(state)
        # A stop may begin at the room reached by its preceding route. Skip
        # that identity waypoint instead of asking the live exit graph for a
        # nonsensical exit back into the current room.
        while self.fastwalk_hunt_move_index < len(stop.route_vnums):
            destination = stop.route_vnums[self.fastwalk_hunt_move_index]
            if str(state.room_vnum or "") == destination:
                self.fastwalk_hunt_move_index += 1
                continue
            command = next(
                (
                    _EXIT_COMMANDS.get(direction, direction)
                    for direction, target in state.exits.items()
                    if str(target) == destination
                ),
                None,
            )
            if command not in _MOVEMENT_COMMANDS:
                self.fastwalk_abort_reason = (
                    f"field route could not find GMCP exit to room {destination}"
                )
                self.fastwalk_returning = True
                return BotDecision(
                    "recall",
                    "return safely when the destination-guided route is unavailable",
                )
            self.fastwalk_hunt_move_index += 1
            return BotDecision(
                command,
                f"follow the live exit leading to source room {destination}",
            )
        if route_command_index < len(stop.route):
            command = stop.route[route_command_index]
            self.fastwalk_hunt_move_index += 1
            return BotDecision(command, "follow the verified field-hunt circuit")

        if not self.fastwalk_hunt_looked:
            self.fastwalk_hunt_looked = True
            return BotDecision("look", "inspect the next field-hunt stop")

        if self.shop_visibility_rejected:
            self.shop_visibility_rejected = False
            self.fastwalk_hunt_action_index = max(
                0,
                self.fastwalk_hunt_action_index - 1,
            )
            self.fastwalk_shop_visible_action_pending = True
            return BotDecision(
                "vis",
                "become visible before retrying the source-backed field purchase",
            )

        while self.fastwalk_hunt_action_index < len(stop.actions):
            command = stop.actions[self.fastwalk_hunt_action_index]
            self.fastwalk_hunt_action_index += 1
            if (
                command == "buy ticket"
                and _has_inventory_item(state.inventory, "ticket")
            ):
                continue
            self.fastwalk_shop_visible_action_pending = False
            return BotDecision(command, "perform the verified field-expedition action")

        if (
            stop.abort_if_where_target_absent
            and (
                self.fastwalk_where_target_absent_observed
                or "you fail to find anyone by that name"
                in self.last_response.casefold()
            )
        ):
            self.fastwalk_target_absent = True
            where_target = stop.where_target or stop.target
            self.fastwalk_abort_reason = (
                f"`where` confirmed {where_target!r} absent from the current area"
            )
            self.fastwalk_returning = True
            return BotDecision(
                "recall",
                "return after the global locator confirmed the field target absent",
            )

        unsafe_where_room = next(
            (
                room_name
                for room_name in stop.abort_if_where_room_names
                if room_name.casefold() in self.last_response.casefold()
            ),
            None,
        )
        if unsafe_where_room is not None:
            self.fastwalk_abort_reason = (
                f"`where` located {stop.target!r} in excluded room "
                f"{unsafe_where_room!r}"
            )
            self.fastwalk_returning = True
            return BotDecision(
                "recall",
                "return rather than enter the locator-confirmed unsafe target room",
            )

        if stop.target is None:
            missing_items = _missing_required_inventory_items(
                state.inventory,
                stop.required_items,
            )
            if missing_items:
                self.fastwalk_abort_reason = (
                    "field expedition did not acquire required item(s): "
                    + ", ".join(missing_items)
                )
                self.fastwalk_returning = True
                return BotDecision(
                    "recall",
                    "return safely after a required field item was not acquired",
                )
            self.fastwalk_hunt_stop_skipped = True
            return BotDecision("look", "record the completed field-expedition stop")

        targets = self.room_targets.get(state.room_vnum or "", [])
        if any(
            _stop_target_matches(target, stop.target, stop)
            for target in targets
        ):
            if self._has_persisted_below_band_sighting(state, stop):
                self.fastwalk_hunt_stop_skipped = True
                self.fastwalk_attack_started = False
                return BotDecision(
                    "look",
                    "skip the same field mobile after its persisted below-band consider result",
                )
            if (
                stop.consider_only
                and self.consider_target == stop.target
                and self.consider_viable is not None
            ):
                self.fastwalk_hunt_stop_skipped = True
                return BotDecision(
                    "look",
                    "record live consideration without engaging the research target",
                )
            return self._consider_fastwalk_target(state)

        # Preserve an explicit absence signal for campaign evidence and rotation.
        self.fastwalk_target_absent = True
        self.fastwalk_hunt_stop_skipped = True
        return BotDecision("look", "record an absent circuit target before continuing")

    def _nested_container_extraction_decision(self) -> BotDecision | None:
        if self.gear_catalog is None:
            return None
        for outer_description, inner_description in _nested_inventory_items(
            self.last_response
        ):
            inner = self.gear_catalog.match(inner_description)
            if inner is None or inner.item_type != ITEM_CONTAINER:
                continue
            outer = self.gear_catalog.match(outer_description)
            outer_keyword = (
                item_keyword(outer)
                if outer is not None
                else normalize_item_name(outer_description).split()[-1]
            )
            inner_noun = normalize_item_name(inner.short_description).split()[-1]
            inner_keyword = (
                inner_noun
                if inner_noun in inner.keywords.casefold().split()
                else item_keyword(inner)
            )
            pair = (inner_keyword.casefold(), outer_keyword.casefold())
            if pair in self.nested_container_extractions:
                continue
            self.nested_container_extractions.add(pair)
            return BotDecision(
                f"get {inner_keyword} {outer_keyword}",
                "keep containers separate for stable gear and provision storage",
            )
        return None

    def _source_mobile_level_range(
        self,
        target: str,
        stop: FieldHuntStop | None = None,
    ) -> tuple[int, int] | None:
        """Return the conservative source load range for a recognized target."""
        matches = [
            level_range
            for name, level_range in self.source_mobile_level_ranges.items()
            if (
                name.casefold() == target.casefold()
                if stop is not None and stop.exact_target
                else _targets_match(name, target)
            )
        ]
        if not matches:
            return None
        return min(level_range[0] for level_range in matches), max(
            level_range[1] for level_range in matches
        )

    def _target_selector_for(
        self,
        target: str,
        stop: FieldHuntStop | None = None,
    ) -> str | None:
        """Return the exact live selector for a source-identified room mobile."""
        matches = [
            selector
            for observed, selectors in self.room_target_selectors.get(
                self.current_room or "",
                {},
            ).items()
            if (
                _stop_target_matches(observed, target, stop)
                if stop is not None
                else _targets_match(observed, target)
            )
            for selector in selectors
        ]
        # TARGETMODE IDs are ephemeral. A later `look` in the same room
        # supersedes the old selector after a mobile dies, wanders, or resets.
        return matches[-1] if matches else None

    def _forget_defeated_room_target(
        self,
        target: str,
        selector: str | None,
    ) -> None:
        """Remove one defeated mobile without hiding same-identity bystanders."""
        room = self.current_room
        if room is None:
            return
        selectors_by_target = self.room_target_selectors.get(room, {})
        matches = [
            observed
            for observed in self.room_targets.get(room, [])
            if _targets_match(observed, target)
        ]
        if selector is not None:
            selector_matches = [
                observed
                for observed in matches
                if selector in selectors_by_target.get(observed, ())
            ]
            if selector_matches:
                matches = selector_matches
        if not matches:
            return
        observed = matches[0]
        selectors = selectors_by_target.get(observed, [])
        if selector in selectors:
            selectors.remove(selector)
        counts = self.room_target_counts.get(room, {})
        remaining = max(0, counts.get(observed, 1) - 1)
        if remaining:
            counts[observed] = remaining
            return
        counts.pop(observed, None)
        selectors_by_target.pop(observed, None)
        self.room_targets[room] = [
            candidate
            for candidate in self.room_targets.get(room, [])
            if candidate != observed
        ]

    def _fastwalk_carried_gear_readiness_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        """Fill audited empty slots from carried, legal, level-appropriate gear."""
        if self.gear_catalog is None or self.gear_allowed_categories is None:
            return None
        candidates = self.gear_catalog.match_many_usable(
            _inventory_descriptions(state.inventory),
            character_class=self.spec.character_class,
            subclass=self.spec.subclass,
        )
        seen: Counter[int] = Counter()
        for item in candidates:
            category = item_category(item)
            if category is None or category not in self.gear_allowed_categories:
                continue
            if category in self.gear_prohibited_categories:
                continue
            if item_keyword(item) in self.gear_unusable_keywords:
                continue
            if is_strength_penalty_ring(item):
                continue
            if (
                category == "wield"
                and self.primary_weapon_observed is True
                and self.primary_weapon_lost is not True
            ):
                # ``eq all`` may have captured an empty weapon slot while a
                # queued wield command was still being acknowledged.  Never
                # let that stale audit replace a verified primary weapon with
                # an arbitrary carried fallback.
                continue
            if (
                state.level is not None
                and item.effective_level > state.level + 5
            ):
                continue
            seen[item.vnum] += 1
            if (
                self.fastwalk_readiness_wear_attempts[item.vnum]
                >= seen[item.vnum]
            ):
                continue
            attempted_in_category = sum(
                count
                for vnum, count in self.fastwalk_readiness_wear_attempts.items()
                if (
                    catalog_item := self.gear_catalog.objects.get(vnum)
                ) is not None
                and item_category(catalog_item) == category
            )
            if attempted_in_category >= self.gear_empty_category_counts[category]:
                continue
            self.fastwalk_readiness_wear_attempts[item.vnum] += 1
            return BotDecision(
                f"wear {item_keyword(item)}",
                f"fill an empty {category} slot from carried gear before field departure",
            )
        return None

    def _fastwalk_junk_disposal_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        carry_weight = _state_stat(state, "carry_wt")
        maximum_weight = _state_stat(state, "maxcarry_wt")
        if (
            carry_weight is None
            or maximum_weight is None
            or maximum_weight - carry_weight > 5
        ):
            return None
        inventory_names = {
            normalize_item_name(description)
            for description in _inventory_descriptions(state.inventory)
        }
        for description, keyword in _EXPENDABLE_FIELD_JUNK.items():
            if (
                description in inventory_names
                and keyword not in self.fastwalk_junk_disposal_attempted
            ):
                self.fastwalk_junk_disposal_attempted.add(keyword)
                return BotDecision(
                    f"sacrifice {keyword}",
                    "discard an expendable source-identified key before a field "
                    "drop can exceed carrying capacity",
                )
        return None

    def _fastwalk_invisibility_decision(
        self,
        state: CharacterState,
        *,
        failure_command: str,
        failure_reason: str,
        cast_reason: str,
        abort_reason: str,
    ) -> BotDecision | None:
        if not self.fastwalk_require_invisibility:
            return None
        if (state.level or 0) < 8 and "invis" not in self.known_skills:
            return None
        if _has_named_affect(state.affects, "invis"):
            self.fastwalk_invisibility_pending = False
            self.fastwalk_invisibility_attempts = 0
            return None
        if self.fastwalk_invisibility_pending:
            return None
        if (
            self.fastwalk_invisibility_unavailable
            or self.fastwalk_invisibility_attempts >= 8
        ):
            self.fastwalk_abort_reason = abort_reason
            self.fastwalk_returning = True
            return BotDecision(failure_command, failure_reason)
        self.fastwalk_invisibility_attempts += 1
        self.fastwalk_invisibility_pending = True
        return BotDecision("cast invis", cast_reason)

    def _fastwalk_caster_mitigation_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        """Apply one known class mitigation spell before field travel."""
        spells = _CASTER_MITIGATION_SPELLS.get(self.spec.character_class, ())
        for spell, affect_name, mana_cost in spells:
            if (
                spell not in self.known_skills
                or spell in self.fastwalk_mitigation_attempted
                or _has_named_affect(state.affects, affect_name)
            ):
                continue
            if (
                state.mana is None
                or state.max_mana in (None, 0)
                or state.mana - mana_cost
                < state.max_mana * _FIELD_CONTINUE_MANA_RATIO
            ):
                continue
            self.fastwalk_mitigation_attempted.add(spell)
            return BotDecision(
                f"cast '{spell}'",
                f"apply source-verified {spell} mitigation before field combat",
            )
        return None

    def _field_combat_withdraw_ratio(self, state: CharacterState) -> float:
        stop_floor = 0.0
        if self.fastwalk_hunt_stop_index < len(self.fastwalk_hunt_stops):
            stop_floor = self.fastwalk_hunt_stops[
                self.fastwalk_hunt_stop_index
            ].minimum_combat_health_ratio
        enemies = _enemy_records(state.enemies)
        material_enemies = [
            enemy
            for enemy in enemies
            if not self._enemy_is_known_below_useful_band(enemy, state)
        ]
        assessed_enemies = material_enemies or enemies
        if len(assessed_enemies) != 1 or state.level is None:
            return max(_FIELD_WITHDRAW_HEALTH_RATIO, stop_floor)
        enemy = assessed_enemies[0]
        enemy_level = _int_or_none(enemy.get("level"))
        enemy_hp = _int_or_none(enemy.get("hp"))
        enemy_max_hp = _int_or_none(enemy.get("maxhp"))
        if (
            enemy_level is not None
            and enemy_level <= state.level
            and enemy_hp is not None
            and enemy_max_hp not in (None, 0)
            and enemy_hp / enemy_max_hp <= 0.5
        ):
            return max(_FIELD_FINISH_HEALTH_RATIO, stop_floor)
        return max(_FIELD_WITHDRAW_HEALTH_RATIO, stop_floor)

    def _field_combat_plateau_elapsed(
        self,
        state: CharacterState,
        *,
        now: float,
    ) -> float | None:
        """Return elapsed time when one enemy has made no net HP progress."""
        enemies = _enemy_records(state.enemies)
        if len(enemies) != 1:
            return None
        enemy = enemies[0]
        enemy_name = normalize_item_name(str(enemy.get("name", "")))
        enemy_hp = _int_or_none(enemy.get("hp"))
        if not enemy_name or enemy_hp is None or enemy_hp <= 0:
            return None
        if (
            self.field_combat_progress_target != enemy_name
            or self.field_combat_last_progress_at is None
            or self.field_combat_lowest_hp is None
        ):
            self.field_combat_progress_target = enemy_name
            self.field_combat_lowest_hp = enemy_hp
            self.field_combat_last_progress_at = now
            return None
        if enemy_hp < self.field_combat_lowest_hp:
            self.field_combat_lowest_hp = enemy_hp
            self.field_combat_last_progress_at = now
            return None
        elapsed = now - self.field_combat_last_progress_at
        return elapsed if elapsed >= _FIELD_COMBAT_PLATEAU_SECONDS else None

    def _field_live_level_excess(
        self,
        state: CharacterState,
    ) -> tuple[int, int] | None:
        if (
            state.level is None
            or self.fastwalk_hunt_stop_index >= len(self.fastwalk_hunt_stops)
        ):
            return None
        stop = self.fastwalk_hunt_stops[self.fastwalk_hunt_stop_index]
        if stop.maximum_level_offset is None or stop.target is None:
            return None
        ceiling = state.level + stop.maximum_level_offset
        for enemy in _enemy_records(state.enemies):
            if not _targets_match(str(enemy.get("name", "")), stop.target):
                continue
            level = _int_or_none(enemy.get("level"))
            if level is not None and level > ceiling:
                return level, ceiling
        return None

    def _enemy_is_known_below_useful_band(
        self,
        enemy: dict[str, Any],
        state: CharacterState,
    ) -> bool:
        if _enemy_is_below_useful_band(enemy, state.level):
            return True
        if state.level is None:
            return False
        enemy_name = _TARGET_SELECTOR_PREFIX.sub(
            "",
            str(enemy.get("name", "")),
        ).strip()
        source_range = self._source_mobile_level_range(enemy_name)
        return source_range is not None and source_range[1] <= state.level - 5

    def _source_mobile_name_is_known_below_useful_band(
        self,
        name: str,
        level: int | None,
    ) -> bool:
        """Ignore source-identified bystanders that cannot yield useful XP."""
        if level is None:
            return False
        normalized_name = _TARGET_SELECTOR_PREFIX.sub("", str(name)).strip()
        source_range = self._source_mobile_level_range(normalized_name)
        return source_range is not None and source_range[1] <= level - 5

    def _field_attacker_is_known_below_band(
        self,
        attacker: str,
        state: CharacterState,
    ) -> bool:
        if self.fastwalk_hunt_stop_index < len(self.fastwalk_hunt_stops):
            stop = self.fastwalk_hunt_stops[self.fastwalk_hunt_stop_index]
            if any(
                _targets_match(attacker, bystander)
                for bystander in stop.trivial_bystanders
            ):
                return True
        return any(
            _targets_match(str(enemy.get("name", "")), attacker)
            and self._enemy_is_known_below_useful_band(enemy, state)
            for enemy in _enemy_records(state.enemies)
        )

    def _missing_required_field_items(
        self,
        state: CharacterState,
    ) -> list[str]:
        required_counts: Counter[str] = Counter()
        for stop in self.fastwalk_hunt_stops[self.fastwalk_hunt_stop_index :]:
            stop_counts = Counter(stop.required_items)
            for item, count in stop_counts.items():
                required_counts[item] = max(required_counts[item], count)
        requirements = tuple(
            item
            for item, count in required_counts.items()
            for _ in range(count)
        )
        return sorted(
            _missing_required_inventory_items(state.inventory, requirements)
        )

    def _emergency_worn_sale_item(self) -> Any | None:
        """Choose expendable armour, preferring duplicate plain pieces."""
        candidates = [
            item
            for item in self.gear_worn
            if item.item_type == 9 and not protects_from_sale(item)
        ]
        if not candidates:
            return None
        counts = Counter(normalize_item_name(item.short_description) for item in candidates)
        return min(
            candidates,
            key=lambda item: (
                counts[normalize_item_name(item.short_description)] <= 1,
                item.source_cost,
                item.vnum,
            ),
        )

    def _opportunistic_fastwalk_attacker_is_viable(
        self,
        state: CharacterState,
    ) -> bool:
        enemies = _enemy_records(state.enemies)
        enemy_count = len(enemies) if enemies else self.active_enemy_count
        if enemy_count != 1:
            return False
        if enemies:
            enemy = enemies[0]
            if self.active_target is None:
                self.active_target = str(
                    enemy.get("name")
                    or enemy.get("long_desc")
                    or ""
                ).strip() or None
                if self.active_target is not None:
                    self.active_target_selector = self._target_selector_for(
                        self.active_target
                    )
            if self.active_target_level is None:
                self.active_target_level = _int_or_none(enemy.get("level"))
        if (
            self.active_target is None
            or self.active_target_level is None
            or state.level is None
            or _health_ratio(state) < 0.75
        ):
            return False
        stop = (
            self.fastwalk_hunt_stops[self.fastwalk_hunt_stop_index]
            if self.fastwalk_hunt_stop_index < len(self.fastwalk_hunt_stops)
            else None
        )
        permitted_bystanders = (
            stop.allowed_bystanders + stop.trivial_bystanders
            if stop is not None
            else ()
        )
        if (
            stop is not None
            and stop.route_vnums
            and str(state.room_vnum or "") in stop.route_vnums[:-1]
            and not _targets_match(self.active_target or "", stop.target or "")
        ):
            # A route waypoint is navigation evidence, not an opportunistic
            # hunt room.  Keep an unapproved mobile on the registered path in
            # the bounded flee-and-resume hazard flow.
            return False
        observed_bystanders = [
            observed
            for observed, count in self.room_target_counts.get(
                self.current_room or "",
                {},
            ).items()
            if count > 0
            if not _targets_match(observed, self.active_target)
            if not any(
                _targets_match(observed, permitted)
                for permitted in permitted_bystanders
            )
            if self.gear_catalog is None
            or self.gear_catalog.match(observed) is None
        ]
        if observed_bystanders:
            return False
        # This is defensive combat, not target selection: after a lone mobile
        # attacks, a safe-band kill avoids DD4's level-scaled flee penalty.
        return self.active_target_level <= state.level + 1

    @property
    def _arena_kill_limit_reached(self) -> bool:
        return (
            self.arena_kill_limit is not None
            and len(self.completed_kills) >= self.arena_kill_limit
        )

    @property
    def _arena_segment_completion_reason(self) -> str:
        if self._arena_kill_limit_reached:
            return f"finish the bounded arena segment after {self.arena_kill_limit} kills"
        if self.arena_no_viable_targets:
            return (
                "finish the bounded arena segment because all observed opponents "
                "are outside the safe live-consider band"
            )
        return f"leave the arena after reaching level {self.objective_level}"

    def _liquidate_loot_decision(self, state: CharacterState) -> BotDecision | None:
        """Sell known equipment through source-backed safe Midgaard shops."""
        room_vnum = state.room_vnum
        if self.cursed_sale_keyword is not None:
            return self._cursed_sale_recovery_decision(state)
        if (
            self.shop_visibility_rejected
            or _has_named_affect(state.affects, "invis")
        ):
            self.shop_visibility_rejected = False
            return BotDecision(
                "vis",
                "become visible before asking a Midgaard shopkeeper to trade",
            )
        if self.sale_phase == "plan":
            if room_vnum != "3019":
                direction = _MIDGAARD_HEALER_TO_MAGE_LAB_ROUTES.get(
                    room_vnum or ""
                )
                if direction is not None:
                    return BotDecision(
                        direction,
                        "walk awake through safe Midgaard to plan loot sales",
                    )
                if room_vnum not in _MIDGAARD_CITY_HEALER_ROOMS:
                    return BotDecision(
                        "recall",
                        "return from the field before planning safe loot sales",
                    )
                self.failure = (
                    "safe loot-sale route could not reach Mage's Laboratory from "
                    f"{state.room_name!r} ({room_vnum})"
                )
                return None
            if self.gear_catalog is not None and not self.gear_audited:
                if self.gear_audit_pending:
                    audited_items = self.gear_catalog.match_equipment_text(
                        self.last_response
                    )
                    explicit_audit = _equipment_audit_present(self.last_response)
                    if audited_items or explicit_audit:
                        self.gear_worn = audited_items
                        self.gear_audited = True
                        self.gear_audit_pending = False
                    else:
                        return BotDecision(
                            "eq all",
                            "retry the worn-item audit before planning loot sales",
                        )
                else:
                    self.gear_audit_pending = True
                    return BotDecision(
                        "eq all",
                        "audit worn items before planning safe loot sales",
                    )
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
            descriptions = _inventory_descriptions(state.inventory)
            emergency_potion_keyword = (
                _emergency_provision_potion_keyword(
                    descriptions,
                    self.gear_catalog,
                )
                if self.emergency_provision_sale
                else None
            )
            if self.sale_identify_plan is None:
                self.sale_identify_plan = list(
                    dict.fromkeys(
                        _inventory_command_keyword(
                            description,
                            self.gear_catalog,
                        )
                        for description in descriptions
                        if "water skin" not in description.casefold()
                        and "pie" not in description.casefold()
                    )
                )
            if (
                self.spec.race == "human"
                and self.gear_catalog is not None
                and self.sale_identify_index < len(self.sale_identify_plan)
            ):
                keyword = self.sale_identify_plan[self.sale_identify_index]
                self.sale_identify_index += 1
                self.sale_identify_pending_keyword = keyword
                return BotDecision(
                    f"cast 'identify' {keyword}",
                    f"use the Human racial spell to audit {keyword} before sale",
                )
            projected_counts = Counter(self.loot_sale_counts)
            if self.world_boot_id is not None:
                projected_counts.update(
                    (row["item_keyword"], row["shop_name"])
                    for row in self.loot_sale_history
                    if row.get("boot_id") == self.world_boot_id
                )
            retained_counts: Counter[int] = Counter()
            if self.gear_catalog is not None:
                carried = self.gear_catalog.match_many_usable(
                    descriptions,
                    character_class=self.spec.character_class,
                    subclass=self.spec.subclass,
                )
                for stance in (
                    STANCE_COMBAT,
                    STANCE_RECOVERY,
                    STANCE_PRE_LEVEL,
                ):
                    stance_counts = Counter(
                        choice.item.vnum
                        for choice in plan_stance(
                            carried,
                            self.gear_worn,
                            stance,
                            character_level=state.level,
                            level_gain_priorities=(
                                self.spec.effective_level_gain_priorities
                            ),
                            weapon_preference=(
                                self._combat_weapon_preference()
                                if stance == STANCE_COMBAT
                                else None
                            ),
                        )
                        if stance == STANCE_COMBAT
                        or item_category(choice.item) != "wield"
                    )
                    for vnum, count in stance_counts.items():
                        retained_counts[vnum] = max(retained_counts[vnum], count)
                opener_preferences = []
                if "backstab" in self.known_skills:
                    opener_preferences.append(is_piercing_weapon)
                if "stun" in self.known_skills:
                    opener_preferences.append(is_blunt_weapon)
                for preference in opener_preferences:
                    if any(
                        item_category(item) == "wield" and preference(item)
                        for item in self.gear_worn
                    ):
                        continue
                    opener_weapon = self._best_weapon(carried, preference)
                    if opener_weapon is not None:
                        retained_counts[opener_weapon.vnum] = max(
                            retained_counts[opener_weapon.vnum],
                            1,
                        )
                carried_counts = Counter(item.vnum for item in carried)
                worn_counts = Counter(item.vnum for item in self.gear_worn)
                worn_descriptions = [
                    item.short_description for item in self.gear_worn
                ]
                for item in carried:
                    if (
                        not protects_from_sale(item)
                        or is_strength_penalty_ring(item)
                        or _inferior_carried_weapon(
                            item,
                            self.gear_catalog,
                            worn_descriptions,
                        )
                    ):
                        continue
                    category = item_category(item)
                    slot_capacity = {
                        "finger": 2,
                        "neck": 2,
                        "wrist": 2,
                    }.get(category or "", 1)
                    carried_coverage = max(
                        0,
                        slot_capacity - worn_counts[item.vnum],
                    )
                    retained_counts[item.vnum] = max(
                        retained_counts[item.vnum],
                        min(carried_counts[item.vnum], carried_coverage),
                    )
            carry_weight = _state_stat(state, "carry_wt")
            maximum_weight = _state_stat(state, "maxcarry_wt")
            carry_pressure = bool(
                carry_weight is not None
                and maximum_weight
                and carry_weight / maximum_weight >= 0.9
            )
            for description in descriptions:
                normalized_description = normalize_item_name(description)
                if (
                    "water skin" in normalized_description
                    or "pie" in normalized_description
                ):
                    continue
                item = (
                    self.gear_catalog.match(description)
                    if self.gear_catalog is not None
                    else None
                )
                if self.gear_catalog is not None and item is None:
                    continue
                keyword = _inventory_command_keyword(
                    description,
                    self.gear_catalog,
                )
                emergency_item_selected = False
                if emergency_potion_keyword is not None:
                    selected_keyword = _emergency_provision_potion_keyword(
                        [description],
                        self.gear_catalog,
                    )
                    if selected_keyword == emergency_potion_keyword:
                        keyword = selected_keyword
                        emergency_item_selected = True
                identified_value = self.sale_identified_values.get(keyword)
                if (
                    self.gear_catalog is not None
                    and carry_pressure
                    and identified_value is not None
                    and identified_value <= 100
                    and not self.gear_catalog.is_unambiguously_usable(
                        description,
                        character_class=self.spec.character_class,
                        subclass=self.spec.subclass,
                    )
                ):
                    self.donation_plan.append(keyword)
                    continue
                if (
                    item is not None
                    and (
                        is_capacity_infrastructure(item)
                        or (
                            item.item_type in {10, 19}
                            and not is_disposable_food(item)
                            and not emergency_item_selected
                        )
                    )
                ):
                    continue
                if item is not None and retained_counts[item.vnum] > 0:
                    retained_counts[item.vnum] -= 1
                    continue
                shop = safe_shop_for_item(
                    description,
                    projected_counts,
                    item_type=item.item_type if item is not None else None,
                    item_value=self.sale_identified_values.get(
                        keyword
                    ),
                )
                if shop is not None:
                    self.sale_plan.append((keyword, shop))
                    projected_counts[(keyword, shop.name)] += 1
                elif item is not None:
                    self.donation_plan.append(keyword)
            shop_order = list(dict.fromkeys(shop.name for _, shop in self.sale_plan))
            self.sale_plan = [
                sale
                for shop_name in shop_order
                for sale in self.sale_plan
                if sale[1].name == shop_name
            ]
            self.sale_phase = "outbound"

        if self.sale_index >= len(self.sale_plan):
            while (
                self.donation_index < len(self.donation_plan)
                and self.donation_plan[self.donation_index]
                in self.donation_rejected_keywords
            ):
                self.donation_index += 1
            if self.donation_index < len(self.donation_plan):
                if room_vnum != "3019":
                    return self._return_home_decision(state)
                keyword = self.donation_plan[self.donation_index]
                self.donation_index += 1
                self.donation_pending_keyword = keyword
                return BotDecision(
                    f"donate {keyword}",
                    "donate redundant unsellable overflow after preserving useful gear",
                )
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
            next_index = self.sale_index + 1
            if (
                next_index < len(self.sale_plan)
                and self.sale_plan[next_index][1].name == shop.name
            ):
                self.sale_index = next_index
                self.sale_phase = "sell"
                next_keyword, _ = self.sale_plan[self.sale_index]
                return BotDecision(
                    f"value {next_keyword}",
                    f"value the next compatible item without leaving the {shop.name}",
                )
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

    def _cursed_sale_recovery_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        """Clear a no-drop sale item at the healer and destroy expendable copies."""
        keyword = self.cursed_sale_keyword
        if keyword is None:
            return None

        if self.curse_recovery_step == "borrow":
            return self._curse_borrow_decision(state)

        if state.room_vnum != "3054":
            shop = self.cursed_sale_shop
            if (
                shop is not None
                and self.sale_route_index < len(shop.route_to_mage_lab)
            ):
                command = shop.route_to_mage_lab[self.sale_route_index]
                self.sale_route_index += 1
                return BotDecision(
                    command,
                    f"return from the {shop.name} after detecting cursed {keyword}",
                )
            return self._return_home_decision(state)

        if _is_sleeping(state):
            return BotDecision("stand", "wake before buying remove curse")

        if self.curse_recovery_step == "return":
            inventory_count = sum(
                1
                for description in _inventory_descriptions(state.inventory)
                if _inventory_command_keyword(
                    description,
                    self.gear_catalog,
                )
                == keyword
            )
            self.cursed_item_count = max(self.cursed_item_count, inventory_count, 1)
            self.curse_recovery_step = "heal"
            return BotDecision(
                "heal curse",
                f"remove the curse preventing disposal of {keyword}",
            )

        if self.curse_recovery_step == "heal":
            if "you do not have enough money" in self.last_response.casefold():
                if self.curse_borrow_complete:
                    self.failure = (
                        "the healer's remove-curse service remained unaffordable "
                        f"for {keyword} after one bounded bank loan"
                    )
                    return None
                self.insufficient_funds = False
                self.curse_recovery_step = "borrow"
                return self._curse_borrow_decision(state)
            self.curse_items_tossed = "you toss " in self.last_response.casefold()
            self.curse_recovery_step = "destroy"

        if self.curse_recovery_step == "destroy":
            if self.cursed_item_count <= 0:
                self.curse_recovery_step = "refresh"
                return BotDecision(
                    "inventory",
                    f"confirm all cursed {keyword} copies were destroyed",
                )
            if self.curse_items_tossed:
                self.cursed_item_count -= 1
                return BotDecision(
                    f"sacrifice {keyword}",
                    f"destroy a source-confirmed no-drop {keyword} tossed by remove curse",
                )
            if not self.curse_drop_pending:
                self.curse_drop_pending = True
                return BotDecision(
                    f"drop {keyword}",
                    f"drop the now-uncursed expendable {keyword} before destruction",
                )
            self.curse_drop_pending = False
            self.cursed_item_count -= 1
            return BotDecision(
                f"sacrifice {keyword}",
                f"destroy the expendable {keyword} after removing its curse",
            )

        self.cursed_sale_keyword = None
        self.cursed_sale_shop = None
        self.cursed_item_count = 0
        self.curse_recovery_step = "idle"
        self.curse_items_tossed = False
        self.curse_drop_pending = False
        self.curse_borrow_step = 0
        self.curse_borrow_complete = False
        self.sale_plan = []
        self.sale_index = 0
        self.sale_route_index = 0
        self.sale_phase = "plan"
        self.sale_offer_coins = None
        self.sale_identify_plan = None
        self.sale_identify_index = 0
        self.sale_identify_pending_keyword = None
        self.donation_plan = []
        self.donation_index = 0
        self.donation_pending_keyword = None
        self.donation_rejected_keywords.clear()
        return self._liquidate_loot_decision(state)

    def _curse_borrow_decision(self, state: CharacterState) -> BotDecision | None:
        """Fund one remove-curse fee and return directly to the healer."""
        room_vnum = state.room_vnum or ""
        if _is_sleeping(state):
            return BotDecision("stand", "wake before obtaining remove-curse funds")
        if room_vnum == "3007":
            if self.shop_visibility_rejected or _has_named_affect(
                state.affects,
                "invis",
            ):
                self.shop_visibility_rejected = False
                return BotDecision(
                    "vis",
                    "become visible before asking the Dragonhoard banker for credit",
                )
            if self.curse_borrow_step == 0:
                self.curse_borrow_step = 1
                return BotDecision(
                    "withdraw 5 gold",
                    "use existing bank funds for the five-gold remove-curse fee",
                )
            response = self.last_response.casefold()
            if self.curse_borrow_step == 1:
                if "thank you for your custom" in response:
                    self.curse_borrow_complete = True
                    self.curse_borrow_step = 3
                    return BotDecision(
                        "west",
                        "leave the bank after funding remove curse",
                    )
                if (
                    "you have no gold coins to withdraw" in response
                    or "you do not have 5 gold coins to withdraw" in response
                ):
                    self.curse_borrow_step = 2
                    return BotDecision(
                        "borrow 500",
                        "take one bounded loan for the five-gold remove-curse fee",
                    )
                self.failure = (
                    "the bank did not confirm or reject the five-gold "
                    "remove-curse withdrawal"
                )
                return None
            if self.curse_borrow_step == 2:
                if "after borrowing: 500 coins" not in response:
                    self.failure = (
                        "the bank did not confirm the bounded remove-curse loan"
                    )
                    return None
                self.curse_borrow_complete = True
                self.curse_borrow_step = 3
                return BotDecision(
                    "west",
                    "leave the bank after funding remove curse",
                )

        if self.curse_borrow_step == 0:
            outbound = {
                "3054": "south",
                "3001": "south",
                "3005": "east",
                "3006": "east",
            }
            direction = outbound.get(room_vnum)
            if direction is not None:
                return BotDecision(
                    direction,
                    "visit Dragonhoard Bank for remove-curse credit",
                )
        else:
            returning = {
                "3006": "west",
                "3005": "north",
                "3001": "north",
            }
            direction = returning.get(room_vnum)
            if direction is not None:
                return BotDecision(
                    direction,
                    "return to the Midgaard healer with remove-curse funds",
                )
            if room_vnum == "3054":
                if not self.curse_borrow_complete:
                    self.failure = (
                        "the remove-curse bank route returned without confirmed funds"
                    )
                    return None
                self.curse_recovery_step = "heal"
                return BotDecision(
                    "heal curse",
                    f"retry remove curse for {self.cursed_sale_keyword} after funding",
                )

        self.failure = (
            "no verified remove-curse bank route for "
            f"room {state.room_name!r} ({state.room_vnum})"
        )
        return None

    def _begin_midgaard_logout(
        self,
        state: CharacterState,
        *,
        save_reason: str,
        quit_reason: str,
    ) -> BotDecision | None:
        self.midgaard_logout_pending = True
        self.midgaard_logout_save_reason = save_reason
        self.midgaard_logout_quit_reason = quit_reason
        return self._midgaard_logout_decision(state)

    def _restore_fastwalk_autoloot_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        """Restore the standard field-loot setting after selective corpse looting."""
        if not self.fastwalk_selective_loot or self.fastwalk_autoloot_restored:
            return None
        if state.room_vnum != "3054":
            return None
        if _is_sleeping(state):
            return BotDecision(
                "stand",
                "wake before restoring autoloot after selective corpse looting",
            )
        self.fastwalk_autoloot_restored = True
        return BotDecision(
            "config +autoloot",
            "restore normal corpse looting after leaving the known cursed drop behind",
        )

    def _midgaard_logout_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        if state.room_vnum == "3054":
            if _is_sleeping(state):
                return BotDecision("stand", "wake before saving at the Midgaard healer")
            if not self.saved:
                self.saved = True
                self.stage = "saving"
                return BotDecision("save", self.midgaard_logout_save_reason)
            self.stage = "complete"
            return BotDecision("quit", self.midgaard_logout_quit_reason)

        healer_routes = {
            "3063": "north",
            "3060": "down",
            "3737": "enter portal",
            "3025": "north",
            "3009": "south",
            "3033": "south",
            **_MIDGAARD_HEALER_ROUTES,
        }
        direction = healer_routes.get(state.room_vnum or "")
        if direction is not None:
            return BotDecision(
                direction,
                "reach the Midgaard healer before saving and quitting",
            )
        return BotDecision(
            "recall",
            "return to Midgaard before saving and quitting at the healer",
        )

    def _return_home_decision(self, state: CharacterState) -> BotDecision | None:
        """Recall from an interrupted field run and return to the healer."""
        room_vnum = state.room_vnum
        if (
            self.return_home_recovery_commands is None
            and room_vnum in _PYRAMID_DESERT_MAZE_ROOMS
        ):
            maze_return = self._live_maze_navigation_decision(
                state,
                context="return-home:pyramid-desert",
                target="5007",
                allowed_rooms=_PYRAMID_DESERT_MAZE_ROOMS,
                blocked_rooms=frozenset({"5028"}),
            )
            if maze_return is not None:
                return maze_return
            if not self.live_maze_complete:
                return None
            self.return_home_recovery_commands = _PYRAMID_HEALER_RETURN_COMMANDS
            self.return_home_recovery_index = 0
        if (
            self.return_home_recovery_commands is None
            and room_vnum in _SHADOW_GROVE_ROOMS
        ):
            maze_return = self._live_maze_navigation_decision(
                state,
                context="return-home:shadow-grove",
                target="1300",
                allowed_rooms=_SHADOW_GROVE_ROOMS,
            )
            if maze_return is not None:
                return maze_return
            if not self.live_maze_complete:
                return None
            self.return_home_recovery_commands = _SHADOW_GROVE_HEALER_RETURN_COMMANDS
            self.return_home_recovery_index = 0
        if self.return_home_recovery_commands is not None:
            if room_vnum == "3054":
                self.utility_abort_reason = None
                return None
            if self.return_home_recovery_index >= len(
                self.return_home_recovery_commands
            ):
                self.failure = (
                    "no-recall recovery route did not reach the Midgaard healer "
                    f"from room {state.room_name!r} ({state.room_vnum})"
                )
                return None
            command = self.return_home_recovery_commands[
                self.return_home_recovery_index
            ]
            self.return_home_recovery_index += 1
            return BotDecision(
                command,
                "follow the source-backed no-recall route to the Midgaard healer",
            )
        home_routes = {
            "3063": "north",
            "3060": "down",
            "3724": "down",
            "3725": "down",
            "3025": "north",
            **_MIDGAARD_HEALER_ROUTES,
        }
        if not self.return_home_recall_started:
            self.return_home_recall_started = True
            if room_vnum not in home_routes and room_vnum != "3054":
                return BotDecision("recall", "recover an interrupted character to Midgaard")
        if _health_ratio(state) < 0.95:
            healer_routes = {
                "3063": "north",
                "3060": "down",
                "3019": "west",
                "3018": "north",
                "3017": "north",
                "3012": "east",
                "3013": "east",
                "3014": "north",
                "3005": "north",
                "3001": "north",
            }
            direction = healer_routes.get(room_vnum or "")
            if direction is not None:
                return BotDecision(direction, "reach the healer before completing recovery")
        direction = home_routes.get(room_vnum or "")
        if direction is not None:
            return BotDecision(direction, "return from recall to the Midgaard healer")
        if room_vnum == "3054":
            self.utility_abort_reason = None
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
            if self.purgatory_gear_restore_step == 0:
                if _is_sleeping(state):
                    return BotDecision(
                        "stand",
                        "wake before restoring corpse-recovered equipment",
                    )
                self.purgatory_gear_restore_step = 1
                return BotDecision(
                    "wear all",
                    "restore all corpse-recovered equipment before auditing it",
                )
            if self.purgatory_gear_restore_step == 1:
                self.purgatory_gear_restore_step = 2
                self.gear_audit_pending = True
                return BotDecision(
                    "eq all",
                    "audit automatically restored corpse gear for incorrect placements",
                )
            if self.purgatory_gear_restore_step == 2:
                gear = self._gear_decision(state)
                if gear is not None:
                    return gear
                self.purgatory_gear_restore_step = 3
            if not self.purgatory_sleep_started:
                self.purgatory_sleep_started = True
                return BotDecision(
                    "sleep",
                    "recover safely beside the healer after corpse retrieval",
                )
            if _is_sleeping(state):
                self.purgatory_recovery_complete = True
                self.utility_abort_reason = None
                return BotDecision(
                    "stand",
                    "wake after post-death recovery before walking home",
                )
            self.purgatory_recovery_complete = True
            self.utility_abort_reason = None
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

    def _body_part_cleanup_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        """Consume fresh body-part food, sacrificing it only as a fallback."""
        keyword = self.body_part_keyword
        if (
            keyword is None
            or state.dead
            or self.combat_active
            or _is_sleeping(state)
            or _health_ratio(state) < 0.5
        ):
            return None
        if self.body_part_cleanup_step == 0:
            self.body_part_cleanup_step = 1
            return BotDecision(
                f"get {keyword}",
                "collect a fresh severed body part before it decays",
            )
        if self.body_part_cleanup_step == 1:
            self.body_part_cleanup_step = 2
            return BotDecision(
                f"eat {keyword}",
                "try free body-part food before spending carried provisions",
            )
        if self.body_part_cleanup_step == 2:
            if self.body_part_eat_rejected:
                self.body_part_cleanup_step = 3
                return BotDecision(
                    f"drop {keyword}",
                    "return an uneaten body part to the room for sacrifice",
                )
            self._clear_body_part_cleanup()
            return None
        if self.body_part_cleanup_step == 3:
            self.body_part_cleanup_step = 4
            return BotDecision(
                f"sacrifice {keyword}",
                "sacrifice the body part after eating was rejected",
            )
        self._clear_body_part_cleanup()
        return None

    def _clear_body_part_cleanup(self) -> None:
        self.body_part_keyword = None
        self.body_part_cleanup_step = 0
        self.body_part_eat_rejected = False

    def _movement_recovery_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        """Route exhausted Midgaard characters to the healer and back."""
        has_usable_food = (
            self.needs_food
            and _has_inventory_food(state.inventory, self.gear_catalog)
            and not self.food_unavailable
        )
        has_usable_water = (
            self.needs_drink
            and _has_inventory_item(state.inventory, "water skin")
            and not self.water_unavailable
        )
        if has_usable_food or has_usable_water:
            return self._resupply_decision(state)

        room_vnum = state.room_vnum or ""
        if (
            not self.movement_recovery_return_route
            and room_vnum in _MIDGAARD_HEALER_RETURN_ROUTES
        ):
            self.movement_recovery_return_route = (
                _MIDGAARD_HEALER_RETURN_ROUTES[room_vnum]
            )
            self.movement_recovery_return_index = 0
            self.movement_recovery_reached_healer = False

        if room_vnum == "3054":
            self.movement_recovery_reached_healer = True

        if _move_ratio(state) >= 0.5 and (
            not self.movement_recovery_return_route
            or self.movement_recovery_reached_healer
        ):
            self.waiting_for_move = False
            self.needs_stand = _is_sleeping(state)
            return None

        if room_vnum == "3054":
            if not _is_sleeping(state):
                return BotDecision(
                    "sleep",
                    "sleep beside the Midgaard healer after movement exhaustion",
                )
            self.prompt_ready = False
            return None

        healer_direction = _MIDGAARD_HEALER_ROUTES.get(room_vnum)
        movement = state.move or 0
        if healer_direction is not None and movement >= 2:
            return BotDecision(
                healer_direction,
                "reach the Midgaard healer before sleeping",
            )
        if healer_direction is not None:
            # Remain awake until natural regeneration provides the next city step.
            self.prompt_ready = False
            return None

        if (state.area or "").casefold() == "midgaard":
            if _is_sleeping(state):
                return BotDecision(
                    "stand",
                    "wake because Midgaard recovery is only permitted at the healer",
                )
            return BotDecision(
                "recall",
                "abort for safety and restart a diverted healer route from recall",
            )

        if not _is_sleeping(state):
            return BotDecision(
                "sleep",
                "sleep in the tutorial safe room after movement exhaustion",
            )
        self.prompt_ready = False
        return None

    def _recovery_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        # GMCP can report an arena opponent just before it marks combat active.
        # Do not attempt to leave through the arena exit during that gap: the
        # move fails, then creates a navigation/combat cycle without progress.
        if _is_arena_vnum(state.room_vnum) and _enemy_records(state.enemies):
            return None
        # Once the post-hunt bank cache route starts, finish its short safe-room
        # return before healer recovery can divert it and strand the route state.
        if (
            self.fastwalk_route is not None
            and self.fastwalk_world_cache_post_started
            and not self.fastwalk_world_cache_post_complete
        ):
            return None
        ratio = _health_ratio(state)
        if (
            self.fastwalk_defer_provision_resupply
            and self.fastwalk_route is not None
            and self.fastwalk_hunt_stops
            and state.room_vnum == "3054"
            and ratio < 0.5
            and not self.fastwalk_funding_recovery_attempted
        ):
            self.fastwalk_funding_recovery_attempted = True
            self.waiting_for_heal = True
            if _is_sleeping(state):
                self.prompt_ready = False
                return None
            return BotDecision(
                "sleep",
                "take one bounded healer sleep before an unfunded field run",
            )
        if (
            self.return_home
            and state.room_vnum == "3054"
            and self.needs_food
            and not _has_inventory_food(state.inventory, self.gear_catalog)
        ):
            self.waiting_for_heal = False
            self.health_check_due = None
            if _is_sleeping(state):
                return BotDecision(
                    "stand",
                    "wake at the healer before checkpointing an unfunded field run",
                )
            return None
        if self.fastwalk_defer_provision_resupply:
            funding_recovery_handled, funding_recovery = (
                self._unfunded_funding_recovery_decision(state)
            )
            if funding_recovery_handled:
                return funding_recovery
        if (
            self.fastwalk_defer_provision_resupply
            and self.fastwalk_route is not None
            and self.fastwalk_hunt_stops
            and not self.fastwalk_returning
        ):
            if ratio <= 0.27:
                self.fastwalk_returning = True
                self.fastwalk_abort_reason = (
                    "funding expedition withdrew before target evaluation because "
                    "health reached the hard withdrawal threshold"
                )
                self.waiting_for_heal = False
                self.health_check_due = None
                if state.room_vnum == "3054":
                    return None
                return BotDecision(
                    "recall",
                    "withdraw before a funding hunt at the hard 27% health boundary",
                )
            self.waiting_for_heal = False
            self.health_check_due = None
            return None
        if self.waiting_for_heal:
            self.health_check_due = None
            self.waiting_for_heal = False
            return BotDecision("stand", "resume training after sanctuary recovery")
        if (
            self.liquidate_loot
            and (
                self.sale_phase != "plan"
                or self.emergency_provision_sale
            )
            and ratio >= 0.25
        ):
            # Shop routes are bounded and safe. Diverting to the healer would
            # make the remaining route index resume from the wrong room.
            return None
        room_name = (state.room_name or "").casefold()
        is_safe_room = (
            state.room_vnum in {"3054", "3721", "3737"}
            or "sanctuary" in room_name
            or "altar of the temple" in room_name
            or room_name == "safety"
            or "safe" in state.room_flags
        )
        is_healer_room = (
            state.room_vnum in {"3054", "3721", "3737"}
            or "sanctuary" in room_name
            or "altar of the temple" in room_name
            or room_name == "safety"
        )
        is_midgaard = (state.area or "").casefold() == "midgaard"
        at_field_recovery_boundary = bool(
            self.fastwalk_hunt_stops
            and (self.fastwalk_outbound_index == 0 or self.fastwalk_returning)
        )
        has_low_cost_movement = (
            _has_named_affect(state.affects, "fly")
            or _has_named_affect(state.affects, "levitation")
        )
        if (
            self.fastwalk_recovery_ready
            and at_field_recovery_boundary
        ) or self.fastwalk_returning and state.room_vnum in {
            "3001",
            "3005",
            "3014",
            "3013",
            "3012",
            "3017",
            "3018",
            "3019",
        }:
            required_move_ratio = 0.4
        elif self.fastwalk_hunt_stops:
            required_move_ratio = (
                0.4
                if at_field_recovery_boundary and has_low_cost_movement
                else 0.9
                if at_field_recovery_boundary
                else 0.25
            )
        elif self.fastwalk_route is not None:
            required_move_ratio = 0.4
        else:
            required_move_ratio = 0.5
        if (
            self.fastwalk_required_move
            and state.max_move
            and at_field_recovery_boundary
            and not self.fastwalk_recovery_ready
        ):
            required_move_ratio = max(
                required_move_ratio,
                min(1.0, self.fastwalk_required_move / state.max_move),
            )
        if ratio >= 0.25:
            required_health_ratio = (
                _FIELD_READY_HEALTH_RATIO
                if self.fastwalk_hunt_stops
                else 0.95
            )
            if (
                at_field_recovery_boundary
                and not self.fastwalk_returning
                and self.fastwalk_hunt_stop_index < len(self.fastwalk_hunt_stops)
            ):
                required_health_ratio = max(
                    required_health_ratio,
                    self.fastwalk_hunt_stops[
                        self.fastwalk_hunt_stop_index
                    ].minimum_health_ratio,
                )
            required_mana_ratio = (
                _FIELD_READY_MANA_RATIO
                if self.fastwalk_hunt_stops
                else 0.5
            )
            if (
                ratio >= required_health_ratio
                and _move_ratio(state) >= required_move_ratio
                and _mana_ratio(state) >= required_mana_ratio
            ):
                if at_field_recovery_boundary:
                    self.fastwalk_recovery_ready = True
                return None
            healer_approach = {
                "3737": "enter portal",
                **_MIDGAARD_HEALER_ROUTES,
            }.get(state.room_vnum or "")
            if (
                self.fastwalk_route is None
                and (
                    self.objective_level > 2
                    or self._is_noncombat_utility_run
                    or state.room_vnum in _MIDGAARD_CITY_HEALER_ROOMS
                )
                and healer_approach is not None
                and (state.move is None or state.move >= 2)
            ):
                return BotDecision(
                    healer_approach,
                    "use the temple healer instead of recovering in a merely safe room",
                )
            if (
                (self.fastwalk_route is not None or self.return_home)
                and state.room_vnum == "3001"
            ):
                return BotDecision(
                    "north",
                    "recover faster with the healer north of recall",
                )
            if self.return_home and ratio < 0.75 and not is_healer_room:
                return None
            if self.fastwalk_route is not None and not is_healer_room:
                if (
                    state.room_vnum == "3019"
                    and self.fastwalk_require_invisibility
                ):
                    invisibility = self._fastwalk_invisibility_decision(
                        state,
                        failure_command="west",
                        failure_reason=(
                            "leave the Mage Guild for healer recovery after "
                            "invisibility preparation failed"
                        ),
                        cast_reason=(
                            "establish invisibility before crossing Midgaard "
                            "to the healer"
                        ),
                        abort_reason=(
                            "field recovery could not establish invisibility "
                            "before crossing Midgaard"
                        ),
                    )
                    if invisibility is not None:
                        return invisibility
                    if self.fastwalk_invisibility_pending:
                        self.prompt_ready = False
                        return None
                direction = _MIDGAARD_HEALER_ROUTES.get(state.room_vnum or "")
                if direction is not None:
                    return BotDecision(
                        direction,
                        "use the temple healer for field-run recovery",
                    )
            if is_midgaard and not is_healer_room:
                if _is_sleeping(state):
                    return BotDecision(
                    "stand",
                    "wake because Midgaard recovery is only permitted at the healer",
                )
                return BotDecision(
                    "recall",
                    "abort for safety and restart recovery after leaving the healer route",
                )
            if (
                self.objective_level > 2
                and _is_arena_vnum(state.room_vnum)
                and not state.in_combat
                and not state.combat_target
                and (state.move is None or state.move >= 2)
            ):
                if _is_sleeping(state):
                    return BotDecision(
                        "stand",
                        "wake before leaving the arena for healer recovery",
                    )
                return self._arena_exit_decision(
                    state,
                    "reach the temple healer for recovery",
                )
            if not is_safe_room:
                return None
            self.waiting_for_heal = True
            if state.room_vnum == "3054":
                return BotDecision(
                    "sleep",
                    "sleep beside the Midgaard healer to recover movement or mana",
                )
            return BotDecision(
                "sleep",
                "recover movement or mana in a tutorial safe room",
            )

        if (
            self.fastwalk_route is not None
            and state.room_vnum == "3001"
            and not is_healer_room
        ):
            return BotDecision(
                "north",
                "reach the temple healer before critical field-run recovery",
            )
        healer_approach = {
            "3737": "enter portal",
            **_MIDGAARD_HEALER_ROUTES,
        }.get(state.room_vnum or "")
        if (
            (
                self.objective_level > 2
                or state.room_vnum in _MIDGAARD_CITY_HEALER_ROOMS
            )
            and healer_approach is not None
            and (state.move is None or state.move >= 2)
        ):
            return BotDecision(
                healer_approach,
                "reach the temple healer before critical recovery",
            )
        if is_midgaard and not is_healer_room:
            if _is_sleeping(state):
                return BotDecision(
                    "stand",
                    "wake because Midgaard recovery is only permitted at the healer",
                )
            return BotDecision(
                "recall",
                "abort for safety and restart critical recovery after a route diversion",
            )
        if is_safe_room:
            if self.return_home and not is_healer_room:
                return None
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

    def _provision_funding_recovery_ready(
        self,
        state: CharacterState,
    ) -> bool:
        stop = (
            self.fastwalk_hunt_stops[self.fastwalk_hunt_stop_index]
            if self.fastwalk_hunt_stop_index < len(self.fastwalk_hunt_stops)
            else None
        )
        minimum_health = max(
            _FIELD_READY_HEALTH_RATIO,
            stop.minimum_health_ratio if stop is not None else 0.0,
        )
        return (
            _health_ratio(state) >= minimum_health
            and _move_ratio(state) >= 0.9
            and _mana_ratio(state) >= 0.5
        )

    def _unfunded_funding_recovery_decision(
        self,
        state: CharacterState,
    ) -> tuple[bool, BotDecision | None]:
        """Keep an unfunded field run asleep until it is ready or withdraws."""
        if not (
            self.fastwalk_defer_provision_resupply
            and self.fastwalk_route is not None
            and self.fastwalk_hunt_stops
            and not self.fastwalk_returning
            and state.room_vnum == "3054"
            and self.needs_food
            and not _has_inventory_food(state.inventory, self.gear_catalog)
        ):
            return False, None
        ratio = _health_ratio(state)
        if ratio <= 0.27:
            self.fastwalk_returning = True
            self.fastwalk_abort_reason = (
                "funding expedition withdrew before target evaluation because "
                "health reached the hard withdrawal threshold"
            )
            self.waiting_for_heal = False
            self.health_check_due = None
            if _is_sleeping(state):
                return True, BotDecision(
                    "stand",
                    "wake before checkpointing an unfunded field run below the health floor",
                )
            return True, None
        if self._provision_funding_recovery_ready(state):
            self.waiting_for_heal = False
            self.health_check_due = None
            if _is_sleeping(state):
                return True, BotDecision(
                    "stand",
                    "wake after bounded healer recovery for a funding hunt",
                )
            return False, None
        if _is_sleeping(state):
            if (
                self.health_check_due is not None
                and time.monotonic() >= self.health_check_due
            ):
                self.health_check_due = (
                    time.monotonic() + _HEALTH_CHECK_WAIT_SECONDS
                )
                return True, BotDecision(
                    "score",
                    "check bounded healer recovery before an unfunded field run",
                )
            self.prompt_ready = False
            return True, None
        self.waiting_for_heal = True
        return True, BotDecision(
            "sleep",
            "continue bounded healer recovery before an unfunded field run",
        )

    def _blindness_recovery_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        """Withdraw to the Midgaard healer until blindness is cured."""
        blinded = _has_named_affect(state.affects, "blindness")
        if not blinded:
            self.blindness_recovery_active = False
            if self.utility_abort_reason == (
                "blindness triggered healer recovery before further field activity"
            ):
                self.utility_abort_reason = None
            return None

        self.blindness_recovery_active = True
        self.return_home = True
        self.utility_abort_reason = (
            "blindness triggered healer recovery before further field activity"
        )
        if self.combat_active or state.in_combat:
            if self.flee_pending:
                self.prompt_ready = False
                return None
            return BotDecision(
                "flee",
                "leave combat after blindness before recalling to the healer",
            )

        room_vnum = state.room_vnum or ""
        if room_vnum == "3054":
            self.waiting_for_heal = True
            if _is_sleeping(state):
                return None
            return BotDecision(
                "sleep",
                "wait beside the Midgaard healer for cure blindness",
            )
        if _is_sleeping(state):
            return BotDecision(
                "stand",
                "wake before withdrawing to the healer after blindness",
            )
        healer_direction = _MIDGAARD_HEALER_ROUTES.get(room_vnum)
        if healer_direction is not None:
            return BotDecision(
                healer_direction,
                "reach the Midgaard healer after blindness",
            )
        return BotDecision(
            "recall",
            "recall from the field after blindness",
        )

    def _recovery_ready_for_objective(self, state: CharacterState) -> bool:
        return (
            _recovery_ready(state)
            and not _has_named_affect(state.affects, "blindness")
            and (
                not self.fastwalk_hunt_stops
                or _move_ratio(state) >= 0.9
            )
            and (
                not self.fastwalk_required_move
                or (state.move or 0) >= self.fastwalk_required_move
            )
        )

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
            return self._combat_opener_decision(
                target,
                f"fight required tutorial opponent {target}",
                state=state,
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
        if self.tutorial_abort_step == 1:
            self.tutorial_abort_step = 2
            self.stage = "complete"
            return BotDecision(
                "quit",
                "leave the depleted tutorial safely for an area-reset retry",
            )
        if key not in self.cleared_training_rooms:
            targets = self.room_targets.get(key)
            if not targets:
                if self.room_query_counts.get(key, 0) == 0:
                    self.room_query_counts[key] = 1
                    return BotDecision(
                        "look",
                        "confirm whether the final tutorial gladiator has reset",
                    )
                self.utility_abort_reason = (
                    "final tutorial gladiator absent; saved and quit for "
                    "an area-reset retry"
                )
                self.tutorial_abort_step = 1
                self.stage = "saving"
                return BotDecision(
                    "save",
                    "checkpoint safely after finding the tutorial depleted",
                )
            target = targets[0]
            self.combat_active = True
            self.active_target = target
            self.between_round_action_issued = False
            return self._combat_opener_decision(
                target,
                "defeat the final tutorial gladiator",
                state=state,
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

    def _loremaster_decision(self, state: CharacterState) -> BotDecision:
        class_trainer = self._level_ten_class_trainer(state)
        at_class_trainer = bool(
            class_trainer is not None
            and (
                state.room_vnum == class_trainer.destination_vnum
                or self._class_trainer_present(state, class_trainer)
            )
        )
        trainer_keyword = (
            class_trainer.keyword
            if at_class_trainer and class_trainer is not None
            else "loremaster"
        )
        if self.loremaster_step == 0:
            self.loremaster_step = 1
            return BotDecision(
                f"look {trainer_keyword}",
                f"ask the {trainer_keyword} about training",
            )
        if self.loremaster_step == 1:
            if at_class_trainer and "you do not see that here" in self.last_response.casefold():
                self.loremaster_step = 0
                self.practiced = True
                self.practice_exit_reason = (
                    "defer class training because the source-registered teacher "
                    "was absent from the live room"
                )
                self.pending_training_events.append(
                    GameEvent(
                        "training_deferred",
                        "text",
                        {
                            "outcome": "deferred",
                            "reason": "source-registered trainer absent",
                            "trainer_keyword": trainer_keyword,
                            "room_vnum": state.room_vnum,
                        },
                    )
                )
                return_command = class_trainer.return_to_healer.get(
                    state.room_vnum or ""
                )
                if return_command is not None:
                    if class_trainer.minimum_level > 10:
                        self.class_trainer_return_pending = False
                        self.waiting_for_move = True
                        return BotDecision(
                            "recall",
                            "return from the distant mobile trainer before healer recovery",
                        )
                    self.class_trainer_return_pending = True
                    return BotDecision(
                        return_command,
                        "leave the empty trainer room and retry after world movement",
                    )
                self.failure = (
                    "source-registered class trainer was absent and no verified "
                    f"return route exists from {state.room_vnum}"
                )
                return BotDecision("look", self.practice_exit_reason)
            self.loremaster_step = 2
            return BotDecision("practice", "list skills available to practice")
        if self.loremaster_step == 2:
            if "skills known:" not in self.text.casefold():
                self.prompt_ready = False
                return None
            self.loremaster_step = 3
            listing = parse_practice_listing(self.text)
            self.known_skills.update(listing.known)
            self.known_skill_levels.update(listing.known)
            critical_unlock = self._critical_damage_unlock(
                state,
                listing,
            )
            practice_type_exclusions = (
                frozenset()
                if critical_unlock is not None
                else frozenset(self.practice_types_spent)
            )
            self.practice_plan = plan_training(
                self.spec.character_class,
                self.text,
                subclass=self._active_training_subclass(state),
                character_level=state.level,
                excluded_practice_types=practice_type_exclusions,
                excluded_skills=frozenset(self._training_excluded_skills()),
                stop_after_skill=critical_unlock,
            )
            total_practices = sum(
                value or 0
                for value in (
                    listing.physical_practices,
                    listing.intellectual_practices,
                )
            )
            preserved = max(0, total_practices - len(self.practice_plan))
            if self.practice_plan and preserved:
                self.practice_exit_reason = (
                    f"preserve {preserved} practice point"
                    f"{'s' if preserved != 1 else ''} for next-level hit-point "
                    "or mana gains after buying only immediately useful skills"
                )
            if not self.practice_plan:
                balances = {
                    "physical": listing.physical_practices or 0,
                    "intellectual": listing.intellectual_practices or 0,
                }
                useful_types = self._useful_practice_types(state)
                deferred_types: list[str] = []
                for practice_type, balance in balances.items():
                    if (
                        balance > 0
                        and practice_type in useful_types
                        and practice_type not in practice_type_exclusions
                    ):
                        deferred_types.append(practice_type)
                        self.pending_training_events.append(
                            GameEvent(
                                "training_deferred",
                                "text",
                                {
                                    "practice_type": practice_type,
                                    "outcome": "deferred",
                                    "reason": (
                                        "no immediately useful listed skill for "
                                        "this practice type"
                                    ),
                                },
                            )
                        )
                if deferred_types:
                    self.practice_exit_reason = (
                        "retain available practice points because this teacher lists no "
                        "eligible source-backed priority skill"
                    )
        if self.practice_listing_refresh_required:
            self.practice_listing_refresh_required = False
            self.practice_plan = ()
            self.practice_plan_index = 0
            self.loremaster_step = 2
            return BotDecision(
                "practice",
                "refresh the trainer listing after unlocking a prerequisite gateway",
            )
        if self.pending_practice_choice is not None:
            return None
        if self.practice_plan_index < len(self.practice_plan):
            choice = self.practice_plan[self.practice_plan_index]
            self.pending_practice_choice = choice
            return BotDecision(
                f"practice {choice.skill}",
                choice.explanation,
            )
        if (
            at_class_trainer
            and self.spec.character_class.casefold() == "smithy"
        ):
            if (
                self.counterbalance_preparation_required
                and "counterbalance" in self.known_skills
                and self.smithy_counterbalance_step == 0
            ):
                self.smithy_counterbalance_step = 1
            preparation = self._smithy_counterbalance_decision()
            if preparation is not None:
                return preparation
        self.practiced = True
        if at_class_trainer and class_trainer is not None:
            if class_trainer.minimum_level > 10:
                self.class_trainer_return_pending = False
                self.waiting_for_move = True
                return BotDecision(
                    "recall",
                    "return from the distant mobile trainer before healer recovery",
                )
            self.class_trainer_return_pending = True
            return_command = class_trainer.return_to_healer[
                state.room_vnum or class_trainer.destination_vnum
            ]
            return BotDecision(
                return_command,
                "walk back from the class trainer without paying the recall "
                "movement penalty",
            )
        return BotDecision(
            "west",
            self.practice_exit_reason,
        )

    def _smithy_counterbalance_decision(self) -> BotDecision | None:
        if self.smithy_counterbalance_step == 0:
            return None
        if self.smithy_counterbalance_step == 1:
            weapon = self._smithy_equipped_weapon()
            if weapon is None:
                self.pending_training_events.append(
                    GameEvent(
                        "equipment_preparation_deferred",
                        "text",
                        {
                            "skill": "counterbalance",
                            "outcome": "deferred",
                            "reason": "no source-identified wielded weapon",
                        },
                    )
                )
                self.smithy_counterbalance_step = 0
                return None
            self.smithy_counterbalance_keyword = item_keyword(weapon)
            self.smithy_counterbalance_step = 2
            return BotDecision(
                f"remove {self.smithy_counterbalance_keyword}",
                "carry the current weapon before applying counterbalance at "
                "the source-verified smithy anvil",
            )
        if self.smithy_counterbalance_step == 2:
            if "you stop using " not in self.last_response.casefold():
                self.pending_training_events.append(
                    GameEvent(
                        "equipment_preparation_deferred",
                        "text",
                        {
                            "skill": "counterbalance",
                            "item": self.smithy_counterbalance_keyword,
                            "outcome": "deferred",
                            "reason": "the equipped weapon could not be removed",
                        },
                    )
                )
                self.smithy_counterbalance_step = 0
                self.smithy_counterbalance_keyword = None
                return None
            self.smithy_counterbalance_step = 3
            return BotDecision(
                f"counterbalance {self.smithy_counterbalance_keyword}",
                "permanently add the source-verified proficiency-based extra "
                "attack chance to the carried weapon",
            )
        if self.smithy_counterbalance_step == 3:
            response = self.last_response.casefold()
            confirmed = (
                "you counterbalance " in response
                or "that is already counterbalanced" in response
            )
            if confirmed:
                self.counterbalance_preparation_required = False
            self.pending_training_events.append(
                GameEvent(
                    (
                        "equipment_preparation_completed"
                        if confirmed
                        else "equipment_preparation_deferred"
                    ),
                    "text",
                    {
                        "skill": "counterbalance",
                        "item": self.smithy_counterbalance_keyword,
                        "outcome": "completed" if confirmed else "deferred",
                        "reason": (
                            "weapon counterbalance confirmed by the smithing command"
                            if confirmed
                            else "counterbalance command did not confirm the upgrade"
                        ),
                        "source_refs": [
                            "server/src/skill.c: do_counterbalance",
                            "server/src/fight.c: APPLY_BALANCE extra attack",
                            "server/area/midgaard.are: anvil reset in room 3050",
                        ],
                    },
                )
            )
            self.smithy_counterbalance_step = 4
            return BotDecision(
                f"wield {self.smithy_counterbalance_keyword}",
                "restore the prepared weapon before leaving the smithy",
            )
        self.smithy_counterbalance_step = 0
        self.smithy_counterbalance_keyword = None
        self.gear_applied_stance = None
        return None

    def _resolve_pending_practice(self, outcome: str, reason: str) -> None:
        choice = self.pending_practice_choice
        if choice is None:
            return
        self.pending_practice_choice = None
        self.practice_plan_index += 1
        if outcome == "accepted":
            self.known_skills.add(choice.skill)
            self.practice_types_spent.add(choice.practice_type)
            if (
                choice.utility.endswith("-gateway")
                and self.practice_plan_index >= len(self.practice_plan)
            ):
                self.practice_listing_refresh_required = True
            if choice.skill == "chill touch":
                self.chill_touch_unavailable = False
            if (
                choice.skill == "counterbalance"
                and self.spec.character_class.casefold() == "smithy"
            ):
                self.counterbalance_preparation_required = True
                self.smithy_counterbalance_step = 1
            event_type = "training_completed"
        else:
            self.rejected_practice_skills.add(choice.skill)
            self.practice_exit_reason = (
                f"preserve the practice point after {choice.skill} was rejected: {reason}"
            )
            event_type = "training_rejected"
        self.pending_training_events.append(
            GameEvent(
                event_type,
                "text",
                {
                    "skill": choice.skill,
                    "practice_type": choice.practice_type,
                    "target_percent": choice.target_percent,
                    "outcome": outcome,
                    "reason": reason,
                    "source_refs": list(choice.source_refs),
                },
            )
        )

    def _utility_attacker_is_trivial(self, state: CharacterState) -> bool:
        """Allow a healthy character to finish one harmless safe-room attacker."""
        enemies = _enemy_records(state.enemies)
        if len(enemies) != 1 or state.level is None:
            return False
        enemy_level = _int_or_none(enemies[0].get("level"))
        return (
            enemy_level is not None
            and "safe" in state.room_flags
            and enemy_level <= max(1, state.level - 3)
            and _health_ratio(state) >= 0.9
            and not self.needs_food
            and not self.needs_drink
        )

    def _midgaard_drunk_interruption_is_trivial(
        self,
        state: CharacterState,
    ) -> bool:
        """Recognize source-level-two mobile 3064 only in Temple Square."""
        return (
            state.area == "Midgaard"
            and state.room_vnum == "3005"
            and state.level is not None
            and state.level >= 7
            and self.active_target is not None
            and _targets_match(self.active_target, "drunk")
            and not self.needs_food
            and not self.needs_drink
        )

    def drain_training_events(self) -> list[GameEvent]:
        events = self.pending_training_events
        self.pending_training_events = []
        return events

    def _arena_decision(self, state: CharacterState) -> BotDecision:
        if self._arena_kill_limit_reached:
            self.arena_segment_leaving = True
            return self._arena_exit_decision(
                state,
                self._arena_segment_completion_reason,
            )
        if (
            state.level is not None
            and state.level >= self.objective_level
        ):
            return self._arena_exit_decision(
                state,
                self._arena_segment_completion_reason,
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
            (
                target
                for target in self.room_targets.get(key, [])
                if target not in self.defeated_targets.get(key, set())
            ),
            key=_arena_target_priority,
        )
        if targets:
            target = targets[0]
            if self.consider_target != target:
                self.consider_target = target
                self.consider_target_selector = self._target_selector_for(target)
                self.consider_viable = None
                return BotDecision(
                    f"consider "
                    f"{self.consider_target_selector or _target_keyword(target)}",
                    f"check the live level band for arena opponent {target}",
                )
            if self.consider_viable is False:
                self.defeated_targets.setdefault(key, set()).add(target)
                self.arena_skipped_outside_safe_band = True
                self.consider_target = None
                self.consider_target_selector = None
                self.consider_viable = None
                return BotDecision(
                    "look",
                    f"skip arena opponent {target} outside the safe live-consider band",
                )
            if self.consider_viable is None:
                self.prompt_ready = False
                return None
            self.arena_viable_target_seen = True
            self.consider_target = None
            self.active_target_selector = self.consider_target_selector
            self.consider_target_selector = None
            self.consider_viable = None
            self.combat_active = True
            self.active_target = target
            return self._combat_opener_decision(
                target,
                f"fight arena opponent {target}",
                state=state,
            )

        if self.room_query_counts.get(key, 0) == 0:
            self.room_query_counts[key] = 1
            return BotDecision("look", "identify arena opponents")

        direction = _unvisited_arena_exit(state, self.arena_visited_rooms)
        if direction is not None:
            return BotDecision(direction, "search the next arena section")
        if self.arena_skipped_outside_safe_band and not self.arena_viable_target_seen:
            self.arena_no_viable_targets = True
            self._reset_arena_patrol()
            if not _can_persist_character(state):
                self.arena_segment_leaving = False
                self.arena_respawn_due = (
                    time.monotonic() + _ARENA_RESPAWN_WAIT_SECONDS
                )
                return self._arena_exit_decision(
                    state,
                    "wait outside Mud School until a level-one arena reset",
                )
            self.arena_segment_leaving = True
            return self._arena_exit_decision(
                state,
                self._arena_segment_completion_reason,
            )
        if not self.arena_respawn_wait and _can_persist_character(state):
            self.arena_segment_leaving = True
            return self._arena_exit_decision(
                state,
                "checkpoint after the depleted arena circuit",
            )
        self._reset_arena_patrol()
        self.arena_respawn_due = time.monotonic() + _ARENA_RESPAWN_WAIT_SECONDS
        return self._arena_exit_decision(
            state,
            "reset arena route through the safe entrance",
        )

    def _arena_completion_route_decision(
        self,
        state: CharacterState,
    ) -> BotDecision | None:
        if self.fastwalk_route is not None:
            return None
        objective_reached = (
            self.objective_level > 2
            and state.level is not None
            and state.level >= self.objective_level
        )
        can_checkpoint = _can_persist_character(state)
        if not (
            objective_reached
            or (
                can_checkpoint
                and (
                    self.arena_segment_leaving
                    or self._arena_kill_limit_reached
                )
            )
        ):
            return None
        if not (
            _is_arena_vnum(state.room_vnum)
            or state.room_vnum in {"3001", "3054", "3725"}
        ):
            return None

        self.arena_segment_leaving = True
        reason = self._arena_segment_completion_reason
        if state.room_vnum == "3737":
            return BotDecision(
                "enter portal",
                f"leave arena Safety for healer recovery before: {reason}",
            )
        if state.room_vnum == "3725":
            return BotDecision(
                "down",
                f"descend toward the temple healer before: {reason}",
            )
        if state.room_vnum == "3001":
            return BotDecision(
                "north",
                f"reach the temple healer before: {reason}",
            )
        if state.room_vnum == "3054":
            return None
        return self._arena_exit_decision(state, reason)

    def _arena_exit_decision(
        self,
        state: CharacterState,
        reason: str,
    ) -> BotDecision:
        if state.room_vnum == "3732":
            return BotDecision(
                "north",
                f"reach an arena wall before: {reason}",
            )
        return BotDecision("up", reason)

    def _reset_arena_patrol(self) -> None:
        """Forget stale creature sightings before a fresh arena circuit."""
        self.arena_visited_rooms.clear()
        self.arena_skipped_outside_safe_band = False
        self.arena_viable_target_seen = False
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
        connection_factory: Callable[[CharacterSpec], CommandConnection] | None = None,
        observation_parser: ObservationParser | None = None,
        character_state: CharacterState | None = None,
        objective_level: int = 2,
        arena_kill_limit: int | None = None,
        arena_respawn_wait: bool = True,
        resupply_only: bool = False,
        return_home: bool = False,
        city_restock: bool = False,
        city_rearm: bool = False,
        city_rearm_pounding: bool = False,
        city_outfit: bool = False,
        guildmaster_research: bool = False,
        magic_shop_research: bool = False,
        magic_shop_buy_fly: bool = False,
        flight_borrowing: bool = False,
        bank_excess_coins: bool = False,
        liquidate_loot: bool = False,
        emergency_provision_sale: bool = False,
        fastwalk_route: Fastwalk | None = None,
        fastwalk_explore_direction: str | None = None,
        fastwalk_explore_depth: int = 1,
        fastwalk_attack_target: str | None = None,
        fastwalk_origin_actions: tuple[str, ...] = (),
        fastwalk_defer_provision_resupply: bool = False,
        fastwalk_required_free_weight: int = 0,
        fastwalk_xp_first_capacity_threshold: int = 0,
        fastwalk_required_move: int = 0,
        vault_stow_items: tuple[str, ...] = (),
        vault_claim_items: tuple[str, ...] = (),
        vault_wear_claimed_items: bool = False,
        vault_required_free_weight: int = 0,
        vault_only: bool = False,
        fastwalk_world_cache_items: tuple[str, ...] = (),
        fastwalk_train_before_departure: bool = False,
        fastwalk_require_invisibility: bool = False,
        fastwalk_hunt_stops: tuple[FieldHuntStop, ...] = (),
        fastwalk_kill_limit: int | None = None,
        require_fastwalk_kill: bool = True,
        allow_safe_fastwalk_abort: bool = False,
        moria_research: bool = False,
        moria_depth: int = 0,
        gear_catalog: GearCatalog | None = None,
        source_mobile_targets: Mapping[str, tuple[str, ...]] | None = None,
        source_mobile_level_ranges: Mapping[str, tuple[int, int]] | None = None,
        practice_types_spent: frozenset[str] = frozenset(),
        rejected_practice_skills: frozenset[str] = frozenset(),
        counterbalance_preparation_required: bool = False,
        use_sanctuary_potions: bool = True,
        inactivity_timeout: float = 45.0,
        fastwalk_skip_target_sightings: frozenset[tuple[str, str]] = frozenset(),
    ) -> None:
        if inactivity_timeout <= 0:
            raise ValueError("inactivity_timeout must be positive")
        self.spec = spec
        self.profile_path = profile_path
        self.connection_factory = connection_factory or self._default_connection
        self.observation_parser = observation_parser or ObservationParser()
        self.character_state = character_state or CharacterState()
        self.objective_level = objective_level
        self.arena_kill_limit = arena_kill_limit
        self.arena_respawn_wait = arena_respawn_wait
        self.resupply_only = resupply_only
        self.return_home = return_home
        self.city_restock = city_restock
        self.city_rearm = city_rearm
        self.city_rearm_pounding = city_rearm_pounding
        self.city_outfit = city_outfit
        self.guildmaster_research = guildmaster_research
        self.magic_shop_research = magic_shop_research
        self.magic_shop_buy_fly = magic_shop_buy_fly
        self.flight_borrowing = flight_borrowing
        self.bank_excess_coins = bank_excess_coins
        self.liquidate_loot = liquidate_loot
        self.emergency_provision_sale = emergency_provision_sale
        self.fastwalk_route = fastwalk_route
        self.fastwalk_explore_direction = fastwalk_explore_direction
        self.fastwalk_explore_depth = fastwalk_explore_depth
        self.fastwalk_attack_target = fastwalk_attack_target
        self.fastwalk_origin_actions = fastwalk_origin_actions
        self.fastwalk_defer_provision_resupply = fastwalk_defer_provision_resupply
        self.fastwalk_required_free_weight = fastwalk_required_free_weight
        self.fastwalk_xp_first_capacity_threshold = (
            fastwalk_xp_first_capacity_threshold
        )
        self.fastwalk_required_move = fastwalk_required_move
        self.vault_stow_items = vault_stow_items
        self.vault_claim_items = vault_claim_items
        self.vault_wear_claimed_items = vault_wear_claimed_items
        self.vault_required_free_weight = vault_required_free_weight
        self.vault_only = vault_only
        self.fastwalk_world_cache_items = fastwalk_world_cache_items
        self.fastwalk_train_before_departure = fastwalk_train_before_departure
        self.fastwalk_require_invisibility = fastwalk_require_invisibility or bool(
            self.fastwalk_route is not None
            and "invisibility" in self.spec.identity.capabilities
        )
        self.fastwalk_hunt_stops = fastwalk_hunt_stops
        self.fastwalk_kill_limit = fastwalk_kill_limit
        self.require_fastwalk_kill = require_fastwalk_kill
        self.allow_safe_fastwalk_abort = allow_safe_fastwalk_abort
        self.moria_research = moria_research
        self.moria_depth = moria_depth
        self.gear_catalog = gear_catalog
        self.source_mobile_targets = source_mobile_targets
        self.source_mobile_level_ranges = source_mobile_level_ranges
        self.practice_types_spent = practice_types_spent
        self.rejected_practice_skills = rejected_practice_skills
        self.counterbalance_preparation_required = (
            counterbalance_preparation_required
        )
        self.use_sanctuary_potions = use_sanctuary_potions
        self.inactivity_timeout = inactivity_timeout
        self.fastwalk_skip_target_sightings = fastwalk_skip_target_sightings
        self._last_gmcp_messages: dict[str, str] = {}

    async def run(self) -> RunResult:
        storage = RunStorage(self.spec.database)
        run_id = storage.create_run(
            scenario_name=(
                f"restock:{self.spec.name}"
                if self.city_restock
                else f"rearm:{self.spec.name}"
                if self.city_rearm
                else f"outfit:{self.spec.name}"
                if self.city_outfit
                else f"sell-loot:{self.spec.name}"
                if self.liquidate_loot
                else f"return-home:{self.spec.name}"
                if self.return_home
                else f"guildmaster:{self.spec.name}"
                if self.guildmaster_research
                else f"borrow-flight:{self.spec.name}"
                if self.flight_borrowing
                else f"magic-shop:{self.spec.name}"
                if self.magic_shop_research
                else f"bank-excess-coins:{self.spec.name}"
                if self.bank_excess_coins
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
                else f"rearm-{self.spec.name}"
                if self.city_rearm
                else f"outfit-{self.spec.name}"
                if self.city_outfit
                else f"sell-loot-{self.spec.name}"
                if self.liquidate_loot
                else f"return-home-{self.spec.name}"
                if self.return_home
                else f"guildmaster-{self.spec.name}"
                if self.guildmaster_research
                else f"borrow-flight-{self.spec.name}"
                if self.flight_borrowing
                else f"magic-shop-{self.spec.name}"
                if self.magic_shop_research
                else f"bank-excess-coins-{self.spec.name}"
                if self.bank_excess_coins
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
            record(
                "run_context",
                {
                    "character": {
                        "name": self.spec.name,
                        "race": self.spec.race,
                        "gender": self.spec.gender,
                        "class": self.spec.character_class,
                        "subclass": self.spec.subclass,
                        "progression_track": self.spec.identity.progression_track,
                        "capabilities": sorted(self.spec.identity.capabilities),
                    },
                    "objective": {
                        "level": self.objective_level,
                        "arena_kill_limit": self.arena_kill_limit,
                        "fastwalk_route": (
                            self.fastwalk_route.name if self.fastwalk_route else None
                        ),
                        "fastwalk_target": self.fastwalk_attack_target,
                        "fastwalk_required_move": self.fastwalk_required_move,
                    },
                },
            )
            if password is None:
                try:
                    password = load_character_password(self.spec.credential_name)
                except CredentialStoreError as exc:
                    raise RuntimeError(str(exc)) from exc
            gear_catalog = self.gear_catalog
            source_directory = Path("runs/dd4-source/server/area")
            if gear_catalog is None and source_directory.is_dir():
                gear_catalog = load_gear_catalog(str(source_directory.resolve()))
            source_mobile_targets = self.source_mobile_targets
            if source_mobile_targets is None and source_directory.is_dir():
                source_mobile_targets = _load_source_mobile_targets(
                    str(source_directory.resolve())
                )
            source_mobile_level_ranges = self.source_mobile_level_ranges
            if source_mobile_level_ranges is None and source_directory.is_dir():
                source_mobile_level_ranges = _load_source_mobile_level_ranges(
                    str(source_directory.resolve())
                )
            policy = StarterPolicy(
                self.spec,
                password,
                objective_level=self.objective_level,
                arena_kill_limit=self.arena_kill_limit,
                arena_respawn_wait=self.arena_respawn_wait,
                resupply_only=self.resupply_only,
                return_home=self.return_home,
                city_restock=self.city_restock,
                city_rearm=self.city_rearm,
                city_rearm_pounding=self.city_rearm_pounding,
                city_outfit=self.city_outfit,
                audit_combat_pouch=self.fastwalk_route is not None,
                use_sanctuary_potions=self.use_sanctuary_potions,
                guildmaster_research=self.guildmaster_research,
                magic_shop_research=self.magic_shop_research,
                magic_shop_buy_fly=self.magic_shop_buy_fly,
                flight_borrowing=self.flight_borrowing,
                bank_excess_coins=self.bank_excess_coins,
                liquidate_loot=self.liquidate_loot,
                emergency_provision_sale=self.emergency_provision_sale,
                loot_sale_history=[
                    dict(row) for row in storage.list_loot_sales(self.spec.name)
                ]
                if self.liquidate_loot
                else None,
                query_world_time=(
                    self.liquidate_loot
                    or self.flight_borrowing
                    or self.fastwalk_route is not None
                ),
                fastwalk_route=self.fastwalk_route,
                fastwalk_explore_direction=self.fastwalk_explore_direction,
                fastwalk_explore_depth=self.fastwalk_explore_depth,
                fastwalk_attack_target=self.fastwalk_attack_target,
                fastwalk_origin_actions=self.fastwalk_origin_actions,
                fastwalk_defer_provision_resupply=(
                    self.fastwalk_defer_provision_resupply
                ),
                fastwalk_required_free_weight=self.fastwalk_required_free_weight,
                fastwalk_xp_first_capacity_threshold=(
                    self.fastwalk_xp_first_capacity_threshold
                ),
                fastwalk_required_move=self.fastwalk_required_move,
                vault_stow_items=self.vault_stow_items,
                vault_claim_items=self.vault_claim_items,
                vault_wear_claimed_items=self.vault_wear_claimed_items,
                vault_required_free_weight=self.vault_required_free_weight,
                vault_only=self.vault_only,
                fastwalk_world_cache_items=self.fastwalk_world_cache_items,
                fastwalk_train_before_departure=self.fastwalk_train_before_departure,
                fastwalk_require_invisibility=self.fastwalk_require_invisibility,
                fastwalk_hunt_stops=self.fastwalk_hunt_stops,
                fastwalk_kill_limit=self.fastwalk_kill_limit,
                moria_research=self.moria_research,
                moria_depth=self.moria_depth,
                gear_catalog=gear_catalog,
                source_mobile_targets=source_mobile_targets,
                source_mobile_level_ranges=source_mobile_level_ranges,
                practice_types_spent=self.practice_types_spent,
                rejected_practice_skills=self.rejected_practice_skills,
                counterbalance_preparation_required=(
                    self.counterbalance_preparation_required
                ),
                title_configured=(
                    not self.spec.title
                    or storage.latest_character_command(
                        self.spec.name,
                        prefix="title ",
                    )
                    is not None
                ),
                description_configured=(
                    not self.spec.description
                    or storage.latest_character_command(
                        self.spec.name,
                        prefix="description ",
                    )
                    is not None
                ),
                selected_training_stat=_selected_training_stat(
                    storage.latest_character_command(
                        self.spec.name,
                        prefix="train ",
                    )
                ),
                fastwalk_skip_target_sightings=(
                    self.fastwalk_skip_target_sightings
                ),
            )
            deadline = asyncio.get_running_loop().time() + self.spec.max_runtime
            commands = 0
            reconnects = 0
            repeated_command = ""
            repeated_count = 0
            recent_decisions: deque[tuple[str | None, str, str]] = deque(
                maxlen=24
            )
            watchdog_progress = _watchdog_progress_marker(self.character_state)
            loop = asyncio.get_running_loop()
            last_connection_activity = loop.time()
            last_policy_progress = loop.time()

            while not policy.done:
                if policy.failure:
                    raise RuntimeError(policy.failure)
                if asyncio.get_running_loop().time() >= deadline:
                    if not policy.runtime_boundary_requested:
                        policy.request_runtime_boundary()
                        record(
                            "state",
                            {
                                "state": "runtime_boundary_requested",
                                "configured_seconds": self.spec.max_runtime,
                            },
                        )
                if commands >= self.spec.max_commands:
                    raise RuntimeError(
                        f"Starter bot exceeded {self.spec.max_commands} command budget"
                    )

                if connection is None or connection.closed:
                    if connection is not None:
                        await connection.close()
                        policy.on_connection_closed()
                        self.observation_parser.reset_connection()
                        self._last_gmcp_messages.clear()
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
                    last_connection_activity = asyncio.get_running_loop().time()
                    record("state", {"state": "connected"})

                result = await connection.read_available(timeout=0.25)
                if result.empty:
                    self._flush_observations(record, policy)
                    idle_seconds = (
                        asyncio.get_running_loop().time()
                        - last_connection_activity
                    )
                    if idle_seconds >= self.inactivity_timeout:
                        record(
                            "state",
                            {
                                "state": "connection_inactivity_timeout",
                                "idle_seconds": round(idle_seconds, 3),
                            },
                        )
                        await connection.close()
                        continue
                else:
                    last_connection_activity = asyncio.get_running_loop().time()
                    self._record_read(result, record, policy)

                decision = policy.next_decision(self.character_state)
                current_progress = _watchdog_progress_marker(self.character_state)
                if current_progress != watchdog_progress:
                    repeated_command = ""
                    repeated_count = 0
                    watchdog_progress = current_progress
                    last_policy_progress = loop.time()
                if decision is None:
                    if not _policy_inactivity_due(
                        policy,
                        now=loop.time(),
                        last_progress=last_policy_progress,
                        timeout=self.inactivity_timeout,
                    ):
                        continue
                    recovery = policy.recover_from_stall(
                        self.character_state,
                        "no policy decision",
                    )
                    record(
                        "state",
                        {
                            "state": "policy_inactivity_watchdog",
                            "idle_seconds": round(loop.time() - last_policy_progress, 3),
                            "recovery_command": (
                                recovery.command if recovery is not None else None
                            ),
                        },
                    )
                    last_policy_progress = loop.time()
                    if recovery is None:
                        continue
                    decision = recovery

                decision_payload = _decision_payload(decision, policy.stage)
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
                if policy.class_trainer_return_pending:
                    class_trainer = policy._level_ten_class_trainer(
                        self.character_state
                    )
                    if class_trainer is not None:
                        repeat_limit = max(
                            repeat_limit,
                            _max_consecutive_command(
                                class_trainer.return_commands,
                                decision.command,
                            ),
                        )
                if (
                    decision.command == "cast invis"
                    and self.fastwalk_require_invisibility
                ):
                    repeat_limit = max(repeat_limit, 8)
                if _repeated_command_watchdog_applies(
                    repeated_count,
                    repeat_limit,
                    registered_trainer_return=policy.class_trainer_return_pending,
                ):
                    recovery = policy.recover_from_stall(
                        self.character_state,
                        decision.command,
                    )
                    record(
                        "state",
                        {
                            "state": "progress_watchdog",
                            "repeated_command": decision.command,
                            "repeat_limit": repeat_limit,
                            "recovery_command": (
                                recovery.command if recovery is not None else None
                            ),
                        },
                    )
                    if recovery is None:
                        continue
                    decision = recovery
                    decision_payload = _decision_payload(decision, policy.stage)
                    repeated_command = decision.command
                    repeated_count = 1
                decision_key = (
                    self.character_state.room_vnum,
                    decision.command,
                    decision.reason,
                )
                recent_decisions.append(decision_key)
                cycle_repetitions = sum(
                    candidate == decision_key for candidate in recent_decisions
                )
                if _route_cycle_watchdog_applies(
                    decision.command,
                    cycle_repetitions,
                    safe_city_return=(
                        policy.midgaard_logout_pending
                        or policy.class_trainer_return_pending
                    ),
                    randomized_maze=(
                        self.character_state.room_vnum
                        in _PYRAMID_DESERT_MAZE_ROOMS
                        and (
                            policy.return_home
                            or (
                                policy.fastwalk_route is not None
                                and policy.fastwalk_route.live_navigation_target
                                is not None
                            )
                        )
                    ),
                ):
                    recovery = policy.recover_from_stall(
                        self.character_state,
                        f"{decision.command} route cycle",
                    )
                    record(
                        "state",
                        {
                            "state": "route_cycle_watchdog",
                            "room_vnum": self.character_state.room_vnum,
                            "repeated_command": decision.command,
                            "cycle_repetitions": cycle_repetitions,
                            "recovery_command": (
                                recovery.command if recovery is not None else None
                            ),
                        },
                    )
                    recent_decisions.clear()
                    if recovery is None:
                        continue
                    decision = recovery
                    decision_payload = _decision_payload(decision, policy.stage)
                    repeated_command = decision.command
                    repeated_count = 1
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
                last_connection_activity = asyncio.get_running_loop().time()
                last_policy_progress = last_connection_activity
                commands += 1
                policy.after_command(decision)

            if policy.utility_abort_reason is not None:
                raise RuntimeError(policy.utility_abort_reason)
            if (
                policy.fastwalk_abort_reason is not None
                and self._fastwalk_abort_is_failure(policy.fastwalk_abort_reason)
            ):
                raise RuntimeError(policy.fastwalk_abort_reason)
            if (
                self.fastwalk_route is not None
                and not policy.fastwalk_arrival_observed
                and not policy.fastwalk_objective_killed
                and not (
                    self.allow_safe_fastwalk_abort
                    and policy.fastwalk_abort_reason is not None
                )
            ):
                raise RuntimeError(
                    f"fastwalk {self.fastwalk_route.name!r} returned without "
                    "observing its endpoint"
                )
            if self.require_fastwalk_kill and not policy.fastwalk_objective_killed:
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
                    "arena_kill_limit": self.arena_kill_limit,
                    "resupply_only": self.resupply_only,
                    "return_home": self.return_home,
                    "city_restock": self.city_restock,
                    "city_rearm": self.city_rearm,
                    "city_rearm_pounding": self.city_rearm_pounding,
                    "city_outfit": self.city_outfit,
                    "guildmaster_research": self.guildmaster_research,
                    "magic_shop_research": self.magic_shop_research,
                    "magic_shop_buy_fly": self.magic_shop_buy_fly,
                    "magic_shop_purchase_failed": policy.magic_shop_purchase_failed,
                    "flight_borrowing": self.flight_borrowing,
                    "flight_borrow_confirmed": policy.flight_borrow_confirmed,
                    "flight_borrow_complete": policy.flight_borrow_complete,
                    "liquidate_loot": self.liquidate_loot,
                    "vault_storage_rejected": policy.vault_storage_rejected,
                    "vault_lodged_items": list(policy.vault_lodged_items),
                    "vault_claimed_items": list(policy.vault_claimed_items),
                    "world_boot_id": policy.world_boot_id,
                    "completed_kills": policy.completed_kills,
                    "objective_kills": policy.objective_kills,
                    "sale_plan": [
                        {"keyword": keyword, "shop": shop.name}
                        for keyword, shop in policy.sale_plan
                    ],
                    "cursed_sale_keyword": policy.cursed_sale_keyword,
                    "curse_recovery_step": policy.curse_recovery_step,
                    "fastwalk_route": self.fastwalk_route.name if self.fastwalk_route else None,
                    "fastwalk_explore_direction": self.fastwalk_explore_direction,
                    "fastwalk_explore_depth": self.fastwalk_explore_depth,
                    "fastwalk_attack_target": self.fastwalk_attack_target,
                    "fastwalk_target_absent": policy.fastwalk_target_absent,
                    "fastwalk_unattackable_target": (
                        policy.fastwalk_unattackable_target
                    ),
                    "fastwalk_objective_killed": policy.fastwalk_objective_killed,
                    "fastwalk_abort_reason": policy.fastwalk_abort_reason,
                    "fastwalk_route_preflight_hazard_observed": (
                        policy.fastwalk_route_preflight_hazard_observed
                    ),
                    "fastwalk_below_band_targets": sorted(
                        policy.fastwalk_below_band_targets
                    ),
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
            final_state = {
                **self.character_state.to_dict(),
                "magic_shop_purchase_failed": policy.magic_shop_purchase_failed,
                "vault_storage_rejected": policy.vault_storage_rejected,
                "vault_lodged_items": list(policy.vault_lodged_items),
                "vault_claimed_items": list(policy.vault_claimed_items),
                "world_boot_id": policy.world_boot_id,
                # Preserve concrete combat output for the campaign planner.  XP can
                # change after a flee, but it is not useful evidence of a hunt if
                # the runner did not confirm a deliberate kill.
                "campaign_completed_kills": list(policy.completed_kills),
                "campaign_objective_kills": list(policy.objective_kills),
                "campaign_fastwalk_consider_outcomes": dict(
                    policy.fastwalk_consider_outcomes
                ),
                "campaign_fastwalk_target_absent": policy.fastwalk_target_absent,
                "campaign_fastwalk_unattackable_target": (
                    policy.fastwalk_unattackable_target
                ),
                "campaign_fastwalk_below_band_targets": sorted(
                    policy.fastwalk_below_band_targets
                ),
                "campaign_fastwalk_below_band_sightings": [
                    {
                        "room_vnum": room_vnum,
                        "target": target,
                    }
                    for room_vnum, target in sorted(
                        policy.fastwalk_below_band_sightings
                    )
                ],
                "campaign_fastwalk_abort_reason": policy.fastwalk_abort_reason,
                "campaign_fastwalk_route_preflight_hazard_observed": (
                    policy.fastwalk_route_preflight_hazard_observed
                ),
            }
            if self.fastwalk_route is not None:
                final_state["combat_pouch_potions"] = dict(
                    policy.combat_pouch_potions
                )
            if policy.primary_weapon_observed is not None:
                final_state["campaign_has_weapon"] = (
                    policy.primary_weapon_observed
                    and not policy.primary_weapon_lost
                )
            return RunResult(
                run_id,
                "success",
                recorder.path,
                storage.path,
                final_state,
            )
        except Exception as exc:
            runtime_cap_reached = _is_runtime_cap_error(exc)
            if policy is not None:
                self._flush_observations(record, policy)
            persist_policy_research()
            record(
                "state",
                {
                    "state": "runtime_cap" if runtime_cap_reached else "failed",
                    "error": str(exc),
                    "completed_kills": policy.completed_kills if policy else [],
                    "objective_kills": policy.objective_kills if policy else [],
                },
            )
            storage.finish_run(
                run_id,
                status="ready" if runtime_cap_reached else "failed",
                error=str(exc),
            )
            raise
        finally:
            if connection is not None:
                await connection.close()
            recorder.close()
            storage.close()

    def _fastwalk_abort_is_failure(self, abort_reason: str) -> bool:
        if self.allow_safe_fastwalk_abort:
            return False
        final_level = self.character_state.level
        return final_level is None or final_level < self.objective_level

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
            package = message.partition(" ")[0]
            if self._last_gmcp_messages.get(package) == message:
                continue
            self._last_gmcp_messages[package] = message
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
        for event in policy.drain_training_events():
            record("game_event", event.as_payload())

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

    def _default_connection(self, spec: CharacterSpec) -> CommandConnection:
        if spec.transport == "mudlet":
            assert spec.mudlet_directory is not None
            return MudletConnection(spec.mudlet_directory)
        return TelnetConnection(spec.host, spec.port, timeout=spec.timeout)


async def run_starter_profile(path: str | Path) -> RunResult:
    profile_path = Path(path)
    spec = load_character_spec(profile_path)
    return await StarterBotRunner(spec, profile_path).run()


async def run_arena_research_profile(
    path: str | Path,
    *,
    target_level: int = 3,
    kill_limit: int | None = None,
) -> RunResult:
    if not 3 <= target_level <= 10:
        raise ValueError("target_level must be between 3 and 10")
    if kill_limit is not None and kill_limit < 1:
        raise ValueError("kill_limit must be positive")
    profile_path = Path(path)
    spec = load_character_spec(profile_path)
    return await StarterBotRunner(
        spec,
        profile_path,
        objective_level=target_level,
        arena_kill_limit=kill_limit,
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


async def run_rearm_profile(path: str | Path) -> RunResult:
    profile_path = Path(path)
    spec = load_character_spec(profile_path)
    return await StarterBotRunner(
        spec,
        profile_path,
        city_rearm=True,
    ).run()


async def run_outfit_profile(path: str | Path) -> RunResult:
    profile_path = Path(path)
    spec = load_character_spec(profile_path)
    return await StarterBotRunner(
        spec,
        profile_path,
        city_outfit=True,
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
    consider_target: str | None = None,
    maximum_target_count: int = 1,
    allowed_bystanders: tuple[str, ...] = (),
) -> RunResult:
    if attack_target is not None and consider_target is not None:
        raise ValueError("attack_target and consider_target are mutually exclusive")
    if maximum_target_count < 1:
        raise ValueError("maximum_target_count must be positive")
    profile_path = Path(path)
    spec = load_character_spec(profile_path)
    target = consider_target or attack_target
    hunt_route = (
        (explore_direction,) * explore_depth
        if target is not None and explore_direction is not None
        else ()
    )
    hunt_stops = (
        (
            FieldHuntStop(
                hunt_route,
                target,
                allowed_bystanders=allowed_bystanders,
                consider_only=consider_target is not None,
                maximum_target_count=maximum_target_count,
            ),
        )
        if target is not None
        else ()
    )
    return await StarterBotRunner(
        spec,
        profile_path,
        fastwalk_route=route_named(route_name),
        fastwalk_explore_direction=explore_direction,
        fastwalk_explore_depth=explore_depth,
        fastwalk_attack_target=attack_target,
        fastwalk_hunt_stops=hunt_stops,
        fastwalk_kill_limit=1 if attack_target is not None else None,
        require_fastwalk_kill=False,
        allow_safe_fastwalk_abort=True,
    ).run()


async def run_midennir_research_profile(path: str | Path) -> RunResult:
    """Collect the source-backed large sack and return safely through recall."""
    profile_path = Path(path)
    spec = load_character_spec(profile_path)
    return await StarterBotRunner(
        spec,
        profile_path,
        fastwalk_route=route_named("ambush"),
        fastwalk_origin_actions=("drop all.piping", "drop cap"),
        fastwalk_train_before_departure=True,
        fastwalk_require_invisibility=True,
        fastwalk_hunt_stops=(
            FieldHuntStop(
                (
                    "west",
                    "south",
                    "south",
                    "west",
                    "south",
                    "west",
                    "south",
                    "south",
                    "east",
                    "south",
                    "south",
                    "open east",
                    "east",
                    "east",
                ),
                actions=("get sack", "inventory"),
                required_items=("large sack",),
            ),
        ),
    ).run()


def ambush_exterior_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Return the source-backed lower-risk exterior Ambush circuit."""
    return (
        FieldHuntStop(
            (
                "west",
                "south",
                "south",
                "west",
                "south",
                "west",
                "south",
                "south",
                "west",
                "south",
                "south",
            ),
            "wounded goblin",
        ),
        FieldHuntStop(
            ("north", "north", "east", "east"),
            "war dog",
        ),
        FieldHuntStop(("south",), "goblin"),
        FieldHuntStop(("south",), "goblin looter"),
        FieldHuntStop(("open south", "south"), "goblin archer"),
    )


def ambush_level_seven_consider_stops() -> tuple[FieldHuntStop, ...]:
    """Probe the viable level-seven Ambush resets without starting combat."""
    exterior = ambush_exterior_hunt_stops()
    return (
        FieldHuntStop(
            exterior[0].route,
            "wounded goblin",
            consider_only=True,
            exact_target=True,
        ),
        FieldHuntStop(
            exterior[1].route + exterior[2].route + exterior[3].route,
            "goblin looter",
            consider_only=True,
            exact_target=True,
        ),
    )


def ambush_archer_research_stops() -> tuple[FieldHuntStop, ...]:
    """Reach the isolated archer by the shortest source-backed exterior path."""
    return (
        FieldHuntStop(
            (
                "west",
                "south",
                "south",
                "west",
                "south",
                "west",
                "south",
                "south",
                "east",
                "south",
                "south",
                "open south",
                "south",
            ),
            "goblin archer",
            consider_only=True,
            exact_target=True,
        ),
    )


def ambush_bardoosh_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the lone sleeping Bardoosh without authorizing combat."""
    return (
        FieldHuntStop(
            ambush_archer_research_stops()[0].route + ("west",),
            "Bardoosh",
            command_keyword="bardoosh",
            consider_only=True,
            exact_target=True,
        ),
    )


def ambush_bardoosh_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Attack isolated Bardoosh after live consideration at level 13."""
    stop = ambush_bardoosh_research_stops()[0]
    return (
        FieldHuntStop(
            stop.route,
            stop.target,
            command_keyword=stop.command_keyword,
            allowed_bystanders=("wyvern",),
            trivial_bystanders=("goblin", "goblin lieutenant"),
            minimum_health_ratio=0.9,
            exact_target=True,
            maximum_level_offset=1,
        ),
    )


def ambush_archer_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Attack one isolated archer after the route and live band are verified."""
    stop = ambush_archer_research_stops()[0]
    return (
        FieldHuntStop(
            stop.route,
            stop.target,
            minimum_health_ratio=0.85,
            exact_target=True,
        ),
    )


def midennir_mountain_goblin_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt the reset-backed mountain goblin one east of the fastwalk endpoint."""
    return (
        FieldHuntStop(
            ("east",),
            "mountain goblin",
            exact_target=True,
        ),
    )


def moria_level_seven_orc_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt two orcs, then optionally a poison target before recall."""
    return (
        FieldHuntStop(
            ("west", "west", "north", "west"),
            "large orc",
            minimum_health_ratio=_FIELD_HIGH_RISK_START_HEALTH_RATIO,
            exact_target=True,
        ),
        FieldHuntStop(
            ("south",),
            "large orc",
            exact_target=True,
        ),
        FieldHuntStop(
            ("north", "east", "south", "east", "east", "east"),
            "orc",
            allowed_bystanders=("small green garter snake",),
            exact_target=True,
        ),
        FieldHuntStop(
            (),
            "small green garter snake",
            minimum_health_ratio=_FIELD_HIGH_RISK_START_HEALTH_RATIO,
            exact_target=True,
        ),
    )


def moria_level_eight_large_orc_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Probe the reset room and its north exit for the wandering large orc."""
    return moria_level_seven_orc_hunt_stops()[:2]


def daycare_nanny_hunt_route() -> Fastwalk:
    """Return the source-derived recall route to Day Care room 6602."""
    return Fastwalk("dwarven-daycare", 1, 7, "2s6ed2s")


def daycare_nanny_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the two reset-backed nannies without targeting the children."""
    return (
        FieldHuntStop(
            (),
            "old wrinkled nanny",
            allowed_bystanders=(
                "young dwarf",
                "cute and fuzzy teddy bear",
                "raggedy anne doll",
                "abused and old doll",
            ),
            exact_target=True,
            allow_local_recovery=True,
        ),
        FieldHuntStop(
            ("south",),
            "old wrinkled nanny",
            allowed_bystanders=(
                "young dwarf",
                "raggedy anne doll",
                "abused and old doll",
            ),
            exact_target=True,
        ),
    )


def daycare_ring_hunt_route() -> Fastwalk:
    """Return the source-derived recall route to Day Care room 6602."""
    return Fastwalk(
        "dwarven-daycare-ring",
        1,
        9,
        "2s6ed2s",
        recall_after_loot=True,
    )


def daycare_ring_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Acquire both pink ice rings and restore the nearby stat-bearing robe."""
    doll_common = {
        "required_items": ("pink ice ring", "pink ice ring"),
        "allowed_bystanders": ("old wrinkled nanny",),
        "trivial_bystanders": ("young dwarf", "raggedy anne doll"),
        "exact_target": True,
        "maximum_target_count": 2,
        "allow_below_band_for_required_loot": True,
    }
    return (
        FieldHuntStop(
            ("west",),
            "abused and old doll",
            **doll_common,
        ),
        FieldHuntStop(
            (),
            "abused and old doll",
            **doll_common,
        ),
        FieldHuntStop(
            ("south",),
            "abused and old doll",
            **doll_common,
        ),
        FieldHuntStop(
            (),
            "abused and old doll",
            **doll_common,
        ),
        FieldHuntStop(
            ("north", "east"),
            "old wrinkled nanny",
            required_items=("linen robe",),
            trivial_bystanders=(
                "young dwarf",
                "raggedy anne doll",
                "abused and old doll",
            ),
            exact_target=True,
            allow_below_band_for_required_loot=True,
        ),
    )


def forest_bear_claws_hunt_route() -> Fastwalk:
    """Return the source-derived recall route to Forest room 18026."""
    return Fastwalk(
        "forest bear claws",
        10,
        14,
        "6sw2swsw2sw2s;open south;6s2w3s2w2s4e3n2w",
        recall_after_loot=True,
    )


def forest_bear_claws_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Acquire the wandering Forest kodiak's high-damage piercing claws."""
    common = {
        "command_keyword": "bear",
        "required_items": ("pair of bears claws",),
        "exact_target": True,
        "allowed_bystanders": ("small boy",),
        "trivial_bystanders": ("mountain goblin",),
        "allow_below_band_for_required_loot": True,
        "minimum_combat_health_ratio": 0.25,
        "maximum_level_offset": 0,
    }
    stops = [
        FieldHuntStop(
            (),
            "giant kodiak bear",
            actions=("where kodiak",),
            abort_if_where_target_absent=True,
            abort_if_where_room_names=("River bed", "Medicine man's Lair"),
            **common,
        ),
        FieldHuntStop(
            (),
            "giant kodiak bear",
            route_vnums=("18025",),
            **common,
        ),
        FieldHuntStop(
            (),
            "giant kodiak bear",
            route_vnums=("18023",),
            **common,
        ),
        FieldHuntStop(
            (),
            "giant kodiak bear",
            route_vnums=("18024",),
            **common,
        ),
        FieldHuntStop(
            (),
            "giant kodiak bear",
            route_vnums=("18023", "18022"),
            **common,
        ),
    ]
    # The bear is stay-area rather than sentinel. Traverse every source-vetted
    # Forest room while excluding the poison-swarm branch, the medicine man's
    # lair, and exits into adjacent areas.
    safe_search = (
        "18021", "18020", "18019", "18018", "18017", "18013",
        "18012", "18011", "18010", "18009", "18008", "18007",
        "18006", "18005", "18004", "18003", "18002", "18001",
        "18000", "18001", "18002", "18003", "18004", "18031",
        "18032", "18033", "18054", "18033", "18032", "18031",
        "18004", "18034", "18035", "18036", "18037", "18038",
        "18039", "18040", "18041", "18043", "18044", "18045",
        "18046", "18045", "18044", "18043", "18041", "18040",
        "18039", "18038", "18037", "18036", "18035", "18034",
        "18004", "18005", "18006", "18007", "18008", "18009",
        "18010", "18011", "18012", "18013", "18014", "18015",
        "18016", "18048", "18016", "18047", "18049", "18050",
        "18051", "18052", "18053",
    )
    stops.extend(
        FieldHuntStop(
            (),
            "giant kodiak bear",
            route_vnums=(vnum,),
            **common,
        )
        for vnum in safe_search
    )
    return tuple(stops)


def thalos_long_dagger_hunt_route() -> Fastwalk:
    """Return the official Thalos route with required-loot recall behavior."""
    route = route_named("thalos")
    return Fastwalk(
        "thalos long dagger",
        10,
        29,
        route.notation,
        recall_after_loot=True,
    )


def thalos_long_dagger_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Search source-isolated lamia resets for a stronger dagger."""
    common = {
        "command_keyword": "lamia",
        "required_items": ("long slim dagger",),
        "post_actions": ("wear long", "eq all"),
        "exact_target": True,
        "allow_below_band_for_required_loot": True,
        "minimum_combat_health_ratio": 0.4,
        "maximum_level_offset": 0,
    }
    routes = (
        ("5201", "5239", "5240"),
        ("5241", "5243", "5242"),
        ("5243", "5209", "5228", "5224"),
        ("5223", "5222", "5225"),
        ("5207", "5220"),
        (
            "5207", "5225", "5222", "5223", "5224", "5228",
            "5209", "5210", "5211", "5237",
        ),
        ("5211", "5204"),
        ("5203",),
        ("5206",),
        ("5212", "5221"),
        ("5212", "5213", "5214", "5218"),
        ("5215", "5216"),
        (
            "5215", "5218", "5214", "5251", "5252", "5253",
            "5255", "5235",
        ),
        ("5255", "5201", "5202", "5203", "5204", "5205"),
    )
    return (
        FieldHuntStop(
            (),
            "lamia",
            actions=("where lamia",),
            abort_if_where_target_absent=True,
            **common,
        ),
        *(
            FieldHuntStop(
                (),
                "lamia",
                route_vnums=route,
                **common,
            )
            for route in routes
        ),
    )


def daycare_armed_guard_hunt_route() -> Fastwalk:
    """Return the source-derived recall route to the Day Care mini-maze."""
    return Fastwalk("daycare-armed-guard", 1, 8, "2s6ed2swswd")


def daycare_armed_guard_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt the isolated source-level-eight guard after live consideration."""
    return (
        FieldHuntStop(
            (),
            "armed guard",
            exact_target=True,
            route_vnums=("6613", "6614", "6616", "6624"),
        ),
    )


def cult_fanatic_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the isolated cult fanatic while leaving combat disabled."""
    return (
        FieldHuntStop(
            (),
            "fanatic monk",
            allowed_bystanders=("receptionist",),
            consider_only=True,
            exact_target=True,
        ),
    )


def plains_aruncus_research_stops() -> tuple[FieldHuntStop, ...]:
    """Search every source-vetted Plains room reachable from Aruncus's reset."""
    grassy_circuit = (
        "330",
        "319",
        "318",
        "316",
        "300",
        "315",
        "320",
        "305",
        "321",
        "338",
        "317",
        "303",
        "315",
        "320",
        "322",
        "324",
        "323",
    )
    broad_grassy_circuit = (
        "330",
        "319",
        "318",
        "316",
        "300",
        "301",
        "302",
        "303",
        "304",
        "305",
        "321",
        "338",
        "317",
        "303",
        "315",
        "320",
        "322",
        "324",
        "323",
    )
    safe_search_path = (
        *broad_grassy_circuit[1:],
        *grassy_circuit,
        *grassy_circuit,
        "324", "325", "326", "306", "307", "308", "309", "310",
        "327", "313", "314", "313", "312", "311", "310", "311",
        "312", "332", "333", "334", "335", "336", "337", "339",
        "340", "341", "340", "342", "343",
    )
    trivial_bystanders = (
        "the cute rabbit",
        "Sorbus the Hermit",
        "the citizen",
    )

    def research_stop(destination: str) -> FieldHuntStop:
        return FieldHuntStop(
            (),
            "Aruncus the Druid",
            command_keyword="aruncus",
            actions=("where aruncus",) if destination == "323" else (),
            abort_if_where_target_absent=destination == "323",
            consider_only=True,
            exact_target=True,
            route_vnums=(destination,),
            trivial_bystanders=trivial_bystanders,
        )

    def hut_door_stop(*route: str) -> FieldHuntStop:
        return FieldHuntStop(
            route,
            "Aruncus the Druid",
            command_keyword="aruncus",
            consider_only=True,
            exact_target=True,
            trivial_bystanders=trivial_bystanders,
        )

    return (
        FieldHuntStop(
            (),
            "Aruncus the Druid",
            command_keyword="aruncus",
            actions=("where aruncus",),
            abort_if_where_target_absent=True,
            consider_only=True,
            exact_target=True,
            trivial_bystanders=trivial_bystanders,
        ),
        research_stop("330"),
        hut_door_stop("open west", "west"),
        hut_door_stop("open east", "east"),
        *(research_stop(destination) for destination in safe_search_path),
    )


def plains_aruncus_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Make one source-fuzz-bounded Aruncus pursuit available for live research."""
    safe_pursuit_rooms = (
        "300",
        "301",
        "302",
        "303",
        "304",
        "305",
        "306",
        "307",
        "308",
        "309",
        "310",
        "311",
        "312",
        "313",
        "314",
        "315",
        "316",
        "317",
        "318",
        "319",
        "320",
        "321",
        "322",
        "323",
        "324",
        "325",
        "326",
        "327",
        "330",
        "331",
        "332",
        "333",
        "334",
        "335",
        "336",
        "337",
        "339",
        "340",
        "341",
        "342",
        "343",
    )
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.85,
            maximum_level_offset=2,
            maximum_pursuit_steps=3,
            pursuit_room_vnums=safe_pursuit_rooms,
            selective_loot_keywords=("staff", "scroll", "ivy"),
            abort_after_consider_rejection=True,
        )
        for stop in plains_aruncus_research_stops()
    )


def dwarven_worker_research_stops() -> tuple[FieldHuntStop, ...]:
    """Search every safely reversible room reachable by a mountain worker."""
    route_steps = (
        ((), ()),
        (("south",), ("6500",)),
        (("north", "north"), ("6501", "6502")),
        (("north",), ("6503",)),
        (("east",), ("6540",)),
        (("south",), ("6504",)),
        (("north",), ("6506",)),
        (("east",), ("6507",)),
        (("north",), ("6508",)),
        (("north",), ("6509",)),
        (("west",), ("6522",)),
    )
    return tuple(
        FieldHuntStop(
            route,
            "dwarven mining worker",
            command_keyword="worker",
            consider_only=True,
            exact_target=True,
            maximum_target_count=1,
            route_vnums=route_vnums,
        )
        for route, route_vnums in route_steps
    )


def dwarven_nobleman_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the isolated neutral nobleman without authorizing combat."""
    return (
        FieldHuntStop(
            (),
            "dwarven nobleman",
            command_keyword="nobleman",
            allowed_bystanders=("maid",),
            trivial_bystanders=("mountain goblin",),
            consider_only=True,
            exact_target=True,
            maximum_target_count=1,
            abort_after_consider_rejection=True,
        ),
    )


def dwarven_nobleman_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Run one bounded fight after a reboot-scoped viable probe."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.90,
            maximum_level_offset=1,
            maximum_target_count=1,
        )
        for stop in dwarven_nobleman_research_stops()
    )


def dwarven_servant_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the unique Dwarven Home servant without initiating combat."""
    return (
        FieldHuntStop(
            (),
            "dwarven servant",
            command_keyword="servant",
            consider_only=True,
            exact_target=True,
            maximum_target_count=1,
            abort_after_consider_rejection=True,
        ),
    )


def dwarven_servant_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Run one bounded fight after a reboot-scoped viable probe."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.90,
            maximum_level_offset=1,
            maximum_target_count=1,
        )
        for stop in dwarven_servant_research_stops()
    )


def mahntor_rock_toad_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider all four source reset rooms without initiating combat."""
    return (
        FieldHuntStop(
            (),
            "rather large rock toad",
            command_keyword="toad",
            consider_only=True,
            exact_target=True,
        ),
        FieldHuntStop(
            (),
            "rather large rock toad",
            command_keyword="toad",
            consider_only=True,
            exact_target=True,
            route_vnums=("2313",),
        ),
        FieldHuntStop(
            (),
            "rather large rock toad",
            command_keyword="toad",
            consider_only=True,
            exact_target=True,
            route_vnums=("2311", "2310", "2312"),
        ),
        FieldHuntStop(
            (),
            "rather large rock toad",
            command_keyword="toad",
            consider_only=True,
            exact_target=True,
            route_vnums=("2315", "2319"),
        ),
    )


def mahntor_rock_toad_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Attack one live-vetted Rock Toad before enabling the full circuit."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.90,
            maximum_level_offset=1,
        )
        for stop in mahntor_rock_toad_research_stops()[:1]
    )


def mahntor_rock_toad_circuit_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt the four live-vetted resets while health remains serviceable."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=(
                0.675 if index == 0 else _FIELD_CONTINUE_HEALTH_RATIO
            ),
            maximum_level_offset=1,
        )
        for index, stop in enumerate(mahntor_rock_toad_research_stops())
    )


def mirror_realm_watchman_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider both source-isolated Mirror Realm watchmen without combat."""
    common = {
        "command_keyword": "watchman",
        "consider_only": True,
        "exact_target": True,
        "maximum_level_offset": 1,
        "abort_after_consider_rejection": True,
    }
    return (
        FieldHuntStop(
            (),
            "watchman",
            **common,
        ),
        FieldHuntStop(
            ("east", "east"),
            "watchman",
            route_vnums=("19008", "19010"),
            **common,
        ),
    )


def mirror_realm_watchman_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one previously viable watchman under the normal field gates."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.85,
        )
        for stop in mirror_realm_watchman_research_stops()
    )


def crystalmir_white_stag_research_stops() -> tuple[FieldHuntStop, ...]:
    """Search every source-reachable low-risk room for the wandering White Stag."""
    safe_search_path = (
        "10015", "10014", "10013", "10036", "10037", "10033", "10034",
        "10035", "10038", "10032", "10031", "10032", "10038", "10035",
        "10034", "10033", "10037", "10036", "10013", "10007", "10004",
        "10003", "10002", "10029", "10022", "10023", "10022", "10011",
        "10010", "10025", "10026", "10027", "10028", "10021", "10008",
        "10009", "10006", "10009", "10019", "10020", "10019", "10009",
        "10008", "10012", "10008", "10021", "10028", "10027", "10026",
        "10025", "10010", "10011", "10022", "10029", "10002", "10001",
        "10002", "10003", "10004", "10007", "10013", "10014", "10015",
        "10016", "10017", "10016",
    )
    common = {
        "command_keyword": "stag",
        "consider_only": True,
        "exact_target": True,
    }
    return (
        FieldHuntStop(
            (),
            "beautiful white stag",
            actions=("where stag",),
            abort_if_where_target_absent=True,
            **common,
        ),
        *(
            FieldHuntStop(
                (),
                "beautiful white stag",
                route_vnums=(destination,),
                **common,
            )
            for destination in safe_search_path
        ),
    )


def crystalmir_white_stag_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one live-vetted White Stag under the normal field gates."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.85,
            maximum_level_offset=1,
        )
        for stop in crystalmir_white_stag_research_stops()
    )


def shadow_keep_soldier_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the Soldier and two safe Wraith resets without combat."""
    return (
        FieldHuntStop(
            (),
            "undead soldier",
            command_keyword="soldier",
            consider_only=True,
            exact_target=True,
        ),
        FieldHuntStop(
            ("west", "north", "north", "west", "up"),
            "undead soldier",
            command_keyword="soldier",
            consider_only=True,
            exact_target=True,
        ),
        FieldHuntStop(
            ("down", "east", "south", "west", "west"),
            "undead soldier",
            command_keyword="soldier",
            consider_only=True,
            exact_target=True,
        ),
        FieldHuntStop(
            ("east", "east", "east"),
            "shadow wraith",
            command_keyword="wraith",
            consider_only=True,
            exact_target=True,
        ),
        FieldHuntStop(
            ("east", "south", "east"),
            "shadow wraith",
            command_keyword="wraith",
            consider_only=True,
            exact_target=True,
        ),
    )


def shadow_keep_soldier_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one previously viable Shadow Keep target under normal gates."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.85,
            maximum_level_offset=1,
        )
        for stop in shadow_keep_soldier_research_stops()
    )


def highland_keeper_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider each source-isolated Highland Keeper without combat."""
    common = {
        "command_keyword": "keeper",
        "consider_only": True,
        "exact_target": True,
        "maximum_target_count": 1,
        "require_isolated": True,
        "maximum_level_offset": 1,
        "trivial_bystanders": ("hideous bogleech",),
        "abort_after_consider_rejection": True,
    }
    # These are the shortest unlocked source paths between the four Keeper
    # reset rooms.  The initial fastwalk arrives at 11536; later stops use
    # live GMCP exits for every listed room rather than replaying directions.
    route_steps = (
        ("11536",),
        (
            "11535", "11534", "11533", "11532", "11531", "11522",
            "11523", "11524", "11525", "11526", "11527", "11528",
            "11529", "11530",
        ),
        (
            "11529", "11528", "11527", "11526", "11525", "11524",
            "11523", "11522", "11537", "11538", "11539", "11572",
            "11571", "11570", "11569", "11568", "11567", "11566",
            "11565", "11564", "11563", "11562", "11561", "11578",
            "11579", "11580", "11581", "11582", "11583", "11584",
        ),
        (
            "11583", "11582", "11581", "11580", "11579", "11578",
            "11561", "11560", "11559", "11558", "11557", "11556",
            "11555", "11554", "11553", "11552", "11585", "11586",
            "11587", "11588", "11589", "11590", "11591",
        ),
    )
    return tuple(
        FieldHuntStop(
            (),
            "keeper of the tower",
            route_vnums=route_vnums,
            **common,
        )
        for route_vnums in route_steps
    )


def highland_keeper_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one freshly viable Highland Keeper under normal field gates."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.85,
        )
        for stop in highland_keeper_research_stops()
    )


def galaxy_white_dwarf_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the source-isolated room-9306 white dwarf without combat."""
    return (
        FieldHuntStop(
            (),
            "tiny white dwarf",
            command_keyword="white",
            actions=("where white",),
            abort_if_where_target_absent=True,
            consider_only=True,
            exact_target=True,
            maximum_level_offset=1,
            abort_after_consider_rejection=True,
            route_vnums=(
                "1308",
                "1305",
                "1306",
                "9301",
                "9302",
                "9303",
                "9304",
                "9305",
                "9306",
            ),
        ),
    )


def galaxy_white_dwarf_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one freshly viable white dwarf under the normal field gates."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.85,
        )
        for stop in galaxy_white_dwarf_research_stops()
    )


def galaxy_white_dwarf_secondary_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the independent room-9314 white dwarf without combat."""
    return (
        FieldHuntStop(
            (),
            route_vnums=(
                "1308",
                "1305",
                "1306",
                "9301",
                "9302",
                "9303",
            ),
        ),
        FieldHuntStop((), route_vnums=("9303", "9308")),
        FieldHuntStop(
            (),
            "tiny white dwarf",
            command_keyword="white",
            consider_only=True,
            exact_target=True,
            maximum_level_offset=1,
            abort_after_consider_rejection=True,
            route_vnums=("9312", "9313", "9314"),
        ),
    )


def galaxy_white_dwarf_secondary_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one freshly viable room-9314 white dwarf under normal gates."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.85,
        )
        for stop in galaxy_white_dwarf_secondary_research_stops()
    )


def galaxy_red_supergiant_research_stops() -> tuple[FieldHuntStop, ...]:
    """Search the four source-isolated red-supergiant reset rooms."""
    common = {
        "command_keyword": "red",
        "consider_only": True,
        "exact_target": True,
        "maximum_level_offset": 1,
        "abort_after_consider_rejection": True,
    }
    return (
        FieldHuntStop(
            (),
            "red supergiant",
            actions=("where red",),
            abort_if_where_target_absent=True,
            route_vnums=(
                "1308",
                "1305",
                "1306",
                "9301",
                "9302",
                "9303",
                "9304",
            ),
            **common,
        ),
        FieldHuntStop(
            (),
            "red supergiant",
            route_vnums=("9303", "9308"),
            **common,
        ),
        FieldHuntStop(
            (),
            "red supergiant",
            route_vnums=("9312", "9313"),
            **common,
        ),
        FieldHuntStop(
            (),
            "red supergiant",
            route_vnums=("9314", "9309"),
            **common,
        ),
    )


def galaxy_red_supergiant_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one freshly viable red supergiant under the normal field gates."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.85,
        )
        for stop in galaxy_red_supergiant_research_stops()
    )


def galaxy_horsehead_nebula_research_stops() -> tuple[FieldHuntStop, ...]:
    """Reach the source room for the Horsehead Nebula and consider it only."""
    return (
        FieldHuntStop(
            (),
            where_target="horsehead nebula",
            actions=("where horsehead",),
            abort_if_where_target_absent=True,
            route_vnums=(
                "1308",
                "1305",
                "1306",
                "9301",
                "9302",
                "9303",
                "9304",
            ),
        ),
        FieldHuntStop((), route_vnums=("9303", "9308")),
        FieldHuntStop((), route_vnums=("9312", "9313")),
        FieldHuntStop((), route_vnums=("9314", "9309")),
        FieldHuntStop(
            ("north",),
            "horsehead nebula",
            command_keyword="horsehead",
            allowed_bystanders=("young nebula",),
            consider_only=True,
            exact_target=True,
            maximum_target_count=1,
            maximum_level_offset=2,
            abort_after_consider_rejection=True,
        ),
    )


def galaxy_horsehead_nebula_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one freshly viable Horsehead Nebula under normal field gates."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.85,
        )
        for stop in galaxy_horsehead_nebula_research_stops()
    )


def hightower_jailor_research_stops() -> tuple[FieldHuntStop, ...]:
    """Reach the Jailor through the randomized Grove and consider it only."""
    return (
        FieldHuntStop(
            ("open down", "down", "down", "east", "east"),
            "jailor",
            command_keyword="jailor",
            consider_only=True,
            exact_target=True,
            maximum_target_count=1,
            maximum_level_offset=1,
            abort_after_consider_rejection=True,
            route_vnums=(
                "1308",
                "1305",
                "1302",
                "1311",
                "1312",
                "1313",
                "1314",
                "1317",
            ),
        ),
    )


def hightower_jailor_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one freshly viable Jailor under the normal field gates."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.90,
        )
        for stop in hightower_jailor_research_stops()
    )


def mirror_realm_gardener_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the source-isolated Mirror Realm gardener without combat."""
    return (
        FieldHuntStop(
            (),
            "the gardener",
            command_keyword="gardener",
            consider_only=True,
            exact_target=True,
            route_vnums=("19091",),
        ),
    )


def mirror_realm_gardener_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one freshly viable Mirror Realm gardener."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.85,
            maximum_level_offset=1,
        )
        for stop in mirror_realm_gardener_research_stops()
    )


def mirror_realm_guardian_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the isolated Mirror Guardian without initiating combat."""
    return (
        FieldHuntStop(
            (),
            "the mirror guardian",
            command_keyword="guardian",
            consider_only=True,
            exact_target=True,
            route_vnums=("19041",),
        ),
    )


def mirror_realm_guardian_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one viable Mirror Guardian under normal field safeguards."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.85,
        )
        for stop in mirror_realm_guardian_research_stops()
    )


def shire_battle_master_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the Shire battle master without authorizing combat."""
    return (
        FieldHuntStop(
            (),
            "the battle master",
            command_keyword="battle",
            consider_only=True,
            exact_target=True,
            route_vnums=("1117",),
        ),
    )


def minotaur_gatekeeper_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the isolated Mahn-Tor Gatekeeper without combat."""
    return (
        FieldHuntStop(
            (),
            "the Minotaur Gatekeeper",
            command_keyword="gatekeeper",
            consider_only=True,
            exact_target=True,
            route_vnums=("2377",),
        ),
    )


def minotaur_gatekeeper_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one viable Gatekeeper under the normal field safeguards."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.85,
        )
        for stop in minotaur_gatekeeper_research_stops()
    )


def galaxy_cancer_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider Cancer in the Galaxy area without authorizing combat."""
    return (
        FieldHuntStop(
            (),
            "Cancer",
            command_keyword="cancer",
            consider_only=True,
            exact_target=True,
            route_vnums=("9345",),
        ),
    )


def mirror_realm_jerry_garcia_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider Mirror Realm's Jerry Garcia without authorizing combat."""
    return (
        FieldHuntStop(
            (),
            "Jerry Garcia",
            command_keyword="jerry",
            consider_only=True,
            exact_target=True,
            route_vnums=("19170",),
        ),
    )


def pit_official_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the Pit Official without authorizing combat."""
    return (
        FieldHuntStop(
            (), "the Pit Official", command_keyword="pit", consider_only=True,
            exact_target=True, route_vnums=("13703",),
        ),
    )


def dwarven_home_chess_dwarf_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the isolated Dwarven Home chess-room dwarf."""
    return (
        FieldHuntStop(
            (),
            "dwarf",
            command_keyword="dwarf",
            consider_only=True,
            exact_target=True,
            maximum_target_count=1,
            abort_after_consider_rejection=True,
            route_vnums=("20530",),
        ),
    )


def dwarven_home_chess_dwarf_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one freshly viable chess-room dwarf under normal field gates."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.85,
            maximum_level_offset=1,
        )
        for stop in dwarven_home_chess_dwarf_research_stops()
    )


def mirror_realm_storn_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the isolated, non-aggressive Mirror Realm assassin."""
    return (
        FieldHuntStop(
            (),
            "storn the assassin",
            command_keyword="storn",
            consider_only=True,
            exact_target=True,
            maximum_target_count=1,
            abort_after_consider_rejection=True,
            route_vnums=("19114",),
        ),
    )


def mirror_realm_storn_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one freshly viable Storn under normal field gates."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.85,
            maximum_level_offset=1,
        )
        for stop in mirror_realm_storn_research_stops()
    )


def darkwood_strange_mist_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the isolated Darkwood strange mist."""
    return (
        FieldHuntStop(
            (),
            "strange mist",
            command_keyword="mist",
            consider_only=True,
            exact_target=True,
            maximum_target_count=1,
            abort_after_consider_rejection=True,
            route_vnums=("11211",),
        ),
    )


def darkwood_strange_mist_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one freshly viable strange mist under normal field gates."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.85,
            maximum_level_offset=1,
        )
        for stop in darkwood_strange_mist_research_stops()
    )


def dwarven_home_gambler_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the isolated Dwarven Home gambler."""
    return (
        FieldHuntStop(
            (),
            "dwarf",
            command_keyword="dwarf",
            consider_only=True,
            exact_target=True,
            maximum_target_count=1,
            abort_after_consider_rejection=True,
            route_vnums=("20531",),
        ),
    )


def dwarven_home_gambler_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one freshly viable Dwarven Home gambler under normal gates."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.85,
            maximum_level_offset=1,
        )
        for stop in dwarven_home_gambler_research_stops()
    )


def dwarven_home_master_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the isolated Dwarven Home master of the house."""
    return (
        FieldHuntStop(
            (),
            "master of the house",
            command_keyword="master",
            consider_only=True,
            exact_target=True,
            maximum_target_count=1,
            abort_after_consider_rejection=True,
            route_vnums=("20537",),
        ),
    )


def dwarven_home_master_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one freshly viable Dwarven Home master under normal gates."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.85,
            maximum_level_offset=1,
        )
        for stop in dwarven_home_master_research_stops()
    )


def vampire_hive_wounded_vampire_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the source reset of the wandering wounded vampire."""
    return (
        FieldHuntStop(
            (),
            "wounded vampire",
            command_keyword="vampire",
            actions=("where vampire",),
            abort_if_where_target_absent=True,
            consider_only=True,
            exact_target=True,
            maximum_target_count=1,
            abort_after_consider_rejection=True,
            route_vnums=("25641",),
        ),
    )


def vampire_hive_wounded_vampire_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one freshly viable wounded vampire under normal field gates."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.85,
            maximum_level_offset=1,
        )
        for stop in vampire_hive_wounded_vampire_research_stops()
    )


def tabernacle_hulking_beast_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the isolated Tabernacle hulking beast."""
    return (
        FieldHuntStop(
            (),
            "hulking beast",
            command_keyword="beast",
            consider_only=True,
            exact_target=True,
            maximum_target_count=1,
            abort_after_consider_rejection=True,
            route_vnums=("39016",),
        ),
    )


def tabernacle_hulking_beast_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one freshly viable hulking beast under normal field gates."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.85,
            maximum_level_offset=1,
        )
        for stop in tabernacle_hulking_beast_research_stops()
    )


def pirates_seas_rastafarians_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the wandering Pirates Seas Rastafarians at their reset."""
    return (
        FieldHuntStop(
            (),
            "rastafarians",
            command_keyword="rastafarians",
            actions=("where rastafarians",),
            abort_if_where_target_absent=True,
            consider_only=True,
            exact_target=True,
            maximum_target_count=1,
            require_isolated=True,
            abort_after_consider_rejection=True,
            route_vnums=("17141",),
        ),
    )


def pirates_seas_rastafarians_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one freshly viable Rastafarians target under normal field gates."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.85,
            maximum_level_offset=1,
        )
        for stop in pirates_seas_rastafarians_research_stops()
    )


def ghost_town_crypt_thing_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the isolated Ghost Town crypt thing at its reset."""
    return (
        FieldHuntStop(
            (),
            "crypt thing",
            command_keyword="crypt",
            consider_only=True,
            exact_target=True,
            maximum_target_count=1,
            require_isolated=True,
            abort_after_consider_rejection=True,
            route_vnums=("8850",),
        ),
    )


def ghost_town_crypt_thing_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one freshly viable crypt thing under normal field gates."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.85,
            maximum_level_offset=1,
        )
        for stop in ghost_town_crypt_thing_research_stops()
    )


def ghost_town_retriever_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the isolated Ghost Town retriever at its reset."""
    return (
        FieldHuntStop(
            (),
            "retriever",
            command_keyword="retriever",
            consider_only=True,
            exact_target=True,
            maximum_target_count=1,
            require_isolated=True,
            abort_after_consider_rejection=True,
            route_vnums=("8843",),
        ),
    )


def ghost_town_retriever_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one freshly viable retriever under normal field gates."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.85,
            maximum_level_offset=1,
        )
        for stop in ghost_town_retriever_research_stops()
    )


def fleshmonger_guard_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the Fleshmonger foyer guard while leaving combat disabled."""
    return (
        FieldHuntStop(
            (),
            "patrolling guard",
            consider_only=True,
            exact_target=True,
        ),
    )


def fleshmonger_guard_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Attempt one exact-level foyer guard after a separate live probe."""
    return (
        FieldHuntStop(
            (),
            "patrolling guard",
            minimum_health_ratio=0.85,
            exact_target=True,
        ),
    )


def fleshmonger_guard_circuit_research_stops() -> tuple[FieldHuntStop, ...]:
    """Extend the verified foyer kill to the isolated north guard."""
    return (
        FieldHuntStop(
            (),
            "patrolling guard",
            minimum_health_ratio=0.85,
            exact_target=True,
            maximum_level_offset=1,
        ),
        FieldHuntStop(
            ("open north", "north"),
            "on-duty guard",
            minimum_health_ratio=0.60,
            exact_target=True,
            maximum_level_offset=1,
        ),
    )


def fleshmonger_mufti_research_stops() -> tuple[FieldHuntStop, ...]:
    """Count and consider the non-aggressive barracks guards without combat."""
    return (
        FieldHuntStop(
            ("open south", "south"),
            "mufti guard",
            consider_only=True,
            exact_target=True,
        ),
    )


def fleshmonger_cook_research_stops() -> tuple[FieldHuntStop, ...]:
    """Resolve either room ordering while leaving the helper unharmed."""
    return (
        FieldHuntStop(
            ("open east", "east"),
            "cook",
            command_keyword="cook",
            allowed_bystanders=("cook's boy",),
            rejected_consider_subjects=("cook's boy",),
            consider_only=True,
            exact_target=True,
        ),
        FieldHuntStop(
            (),
            "cook",
            command_keyword="2.cook",
            allowed_bystanders=("cook's boy",),
            rejected_consider_subjects=("cook's boy",),
            consider_only=True,
            exact_target=True,
        ),
    )


def fleshmonger_cook_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Attack whichever ordinal live consideration resolves to the adult."""
    return tuple(
        FieldHuntStop(
            stop.route,
            stop.target,
            command_keyword=stop.command_keyword,
            trivial_bystanders=("cook's boy",),
            rejected_consider_subjects=stop.rejected_consider_subjects,
            minimum_health_ratio=0.85,
            exact_target=True,
        )
        for stop in fleshmonger_cook_research_stops()
    )


def fleshmonger_thief_rotation_research_stops() -> tuple[FieldHuntStop, ...]:
    """Combine the three independently evidenced thief targets."""
    return (
        FieldHuntStop(
            (),
            "patrolling guard",
            minimum_health_ratio=0.85,
            exact_target=True,
            maximum_level_offset=0,
        ),
        FieldHuntStop(
            ("open north", "north"),
            "on-duty guard",
            minimum_health_ratio=0.60,
            exact_target=True,
            maximum_level_offset=0,
        ),
        FieldHuntStop(
            ("south", "open east", "east"),
            "cook",
            command_keyword="cook",
            trivial_bystanders=("cook's boy",),
            rejected_consider_subjects=("cook's boy",),
            minimum_health_ratio=0.60,
            exact_target=True,
        ),
        FieldHuntStop(
            (),
            "cook",
            command_keyword="2.cook",
            trivial_bystanders=("cook's boy",),
            rejected_consider_subjects=("cook's boy",),
            minimum_health_ratio=0.60,
            exact_target=True,
        ),
    )


def fleshmonger_servant_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the isolated Study servant without entering the Laboratory."""
    return (
        FieldHuntStop(
            ("up", "up"),
            "hobgoblin servant",
            consider_only=True,
            exact_target=True,
            maximum_target_count=1,
        ),
    )


def fleshmonger_servant_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Attack one isolated Study servant after the live no-combat probe."""
    return (
        FieldHuntStop(
            ("up", "up"),
            "hobgoblin servant",
            minimum_health_ratio=0.85,
            exact_target=True,
            maximum_target_count=1,
            maximum_level_offset=0,
        ),
    )


def fleshmonger_thief_extended_rotation_stops() -> tuple[FieldHuntStop, ...]:
    """Add the verified Study servant to the guard-and-kitchen rotation."""
    return (
        *fleshmonger_thief_rotation_research_stops(),
        FieldHuntStop(
            ("west", "up", "up"),
            "hobgoblin servant",
            minimum_health_ratio=0.60,
            exact_target=True,
            maximum_target_count=1,
            maximum_level_offset=0,
        ),
    )


def circus_freak_show_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Sweep the Freak Show, buy admission, then assess the Big Top."""
    return (
        FieldHuntStop(
            (),
            "Bearded Lady",
            allow_local_recovery=True,
        ),
        FieldHuntStop(
            ("east",),
            "Illusionist",
            trivial_bystanders=("Beastly Fido",),
            allow_local_recovery=True,
        ),
        FieldHuntStop(
            ("south",),
            "Midget",
            allow_local_recovery=True,
            exact_target=True,
        ),
        FieldHuntStop(
            ("west", "west"),
            "Ivan the Strongman",
            allowed_bystanders=("beastly fido",),
            trivial_bystanders=("Little Bobby", "Sword Swallower"),
            minimum_health_ratio=0.60,
        ),
        FieldHuntStop(
            (),
            actions=("buy ticket",),
            required_items=("ticket",),
            route_vnums=("4408", "4406", "4403", "4402"),
        ),
        FieldHuntStop(
            (),
            actions=("unlock south", "open south"),
            route_vnums=("4403", "4406", "4414", "4415"),
        ),
        FieldHuntStop(
            (),
            "Ringmaster",
            trivial_bystanders=("member of the audience",),
            minimum_health_ratio=_FIELD_HIGH_RISK_START_HEALTH_RATIO,
            exact_target=True,
            route_vnums=("4416", "4419"),
        ),
    )


def shire_bull_hunt_route() -> Fastwalk:
    """Return the source-derived recall route to Shire room 1138."""
    return Fastwalk("shire-bull", 1, 7, "2s5w4n2w3nw")


def shire_mill_worker_consider_route() -> Fastwalk:
    """Return the source-derived route to the Watermill entrance (room 1123)."""
    return Fastwalk("shire-watermill", 1, 7, "2s5w4n3ws", recall_after_loot=True)


def shire_mill_worker_consider_stops() -> tuple[FieldHuntStop, ...]:
    """Assess Watermill workers without engaging a potentially crowded room."""
    return (FieldHuntStop((), "mill worker", consider_only=True),)


def shire_mill_worker_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one considered worker only when no second worker is present."""
    return (
        FieldHuntStop(
            (),
            "mill worker",
            allowed_bystanders=("miller",),
            minimum_health_ratio=_FIELD_HIGH_RISK_START_HEALTH_RATIO,
            maximum_target_count=1,
        ),
    )


def shire_bull_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt the isolated bull reset after live enemy assessment."""
    return (
        FieldHuntStop(
            (),
            "bull",
            minimum_health_ratio=_FIELD_HIGH_RISK_START_HEALTH_RATIO,
            exact_target=True,
        ),
    )


def shire_dwarven_prince_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the source-identified Shire prince without authorizing combat."""
    return (
        FieldHuntStop(
            (),
            "dwarven prince",
            command_keyword="prince",
            allowed_bystanders=("elven warrior",),
            trivial_bystanders=("shiriff",),
            consider_only=True,
            exact_target=True,
            maximum_target_count=1,
            require_isolated=True,
            abort_after_consider_rejection=True,
        ),
    )


def shire_dwarven_prince_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one live-vetted prince only after a same-reboot probe."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.95,
            maximum_level_offset=1,
            require_isolated=True,
        )
        for stop in shire_dwarven_prince_research_stops()
    )


def shire_thain_research_stops() -> tuple[FieldHuntStop, ...]:
    """Search Shire rooms for the wandering source-identified Thain."""
    search_path = (
        "1110", "1109", "1106", "1104", "1105", "1104", "1103",
        "1102", "1101", "1100", "1101", "1102", "1103", "1118",
        "1119", "1118", "1120", "1121", "1120", "1122", "1123",
        "1124", "1125", "1124", "1123", "1122", "1126", "1128",
        "1127", "1128", "1129", "1128", "1130", "1128", "1126",
        "1122", "1120", "1131", "1132", "1133", "1134", "1135",
        "1136", "1135", "1134", "1133", "1145", "1133", "1138",
        "1142", "1143", "1142", "1138", "1139", "1140", "1141",
        "1140", "1139", "1138", "1133", "1132", "1144", "1157",
        "1144", "1132", "1131", "1120", "1122", "1120", "1118",
        "1103", "1104", "1106", "1109", "1112", "1117", "1112",
        "1113", "1115", "1113", "1114", "1113", "1116", "1113",
        "1112", "1109", "1106", "1104", "1103", "1118", "1120",
    )
    common = {
        "command_keyword": "thain",
        "consider_only": True,
        "exact_target": True,
        "maximum_target_count": 1,
        "require_isolated": True,
        "maximum_level_offset": 0,
        "abort_after_consider_rejection": True,
    }
    return (
        FieldHuntStop(
            (),
            "the Thain",
            actions=("where thain",),
            abort_if_where_target_absent=True,
            **common,
        ),
        *(
            FieldHuntStop(
                (),
                "the Thain",
                route_vnums=(destination,),
                **common,
            )
            for destination in search_path
        ),
    )


def shire_thain_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one live-vetted Thain after a same-reboot probe."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.90,
        )
        for stop in shire_thain_research_stops()
    )


def argent_bandit_leader_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the source-identified Argent bandit leader without combat."""
    common = {
        "command_keyword": "leader",
        "allowed_bystanders": ("bandit",),
        "consider_only": True,
        "exact_target": True,
        "maximum_target_count": 1,
        "require_isolated": True,
        "maximum_level_offset": 1,
        "abort_after_consider_rejection": True,
    }
    return (
        FieldHuntStop(
            (),
            "bandit leader",
            actions=("where leader",),
            abort_if_where_target_absent=True,
            **common,
        ),
        *(
            FieldHuntStop(
                (),
                "bandit leader",
                route_vnums=route_vnums,
                **common,
            )
            for route_vnums in (
                ("25203", "25202"),
                ("25203",),
                ("25202", "25204"),
                ("25205",),
            )
        ),
    )


def argent_bandit_leader_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one live-vetted bandit leader with its source companion gate."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.90,
            maximum_level_offset=1,
        )
        for stop in argent_bandit_leader_research_stops()
    )


def shire_elven_wizard_research_stops() -> tuple[FieldHuntStop, ...]:
    """Consider the source-identified Wizard without authorizing combat."""
    return (
        FieldHuntStop(
            (),
            "elven wizard",
            command_keyword="wizard",
            trivial_bystanders=("halfling beauty",),
            consider_only=True,
            exact_target=True,
            maximum_target_count=1,
            require_isolated=True,
            maximum_level_offset=1,
            abort_after_consider_rejection=True,
        ),
    )


def shire_elven_wizard_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one live-vetted Wizard only with the caster safeguards active."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.95,
            maximum_level_offset=1,
        )
        for stop in shire_elven_wizard_research_stops()
    )


def pyramid_ali_baba_research_stops() -> tuple[FieldHuntStop, ...]:
    """Probe Ali Baba at reset and the source-connected wandering rooms."""
    common = {
        "command_keyword": "ali baba",
        "consider_only": True,
        "exact_target": True,
        "maximum_target_count": 1,
        "require_isolated": True,
        "maximum_level_offset": 1,
        "abort_after_consider_rejection": True,
    }
    return (
        FieldHuntStop(
            (),
            "Ali Baba",
            actions=("where ali baba",),
            abort_if_where_target_absent=True,
            **common,
        ),
        FieldHuntStop((), "Ali Baba", route_vnums=("2642",), **common),
        FieldHuntStop((), "Ali Baba", route_vnums=("2641",), **common),
        FieldHuntStop((), "Ali Baba", route_vnums=("2640",), **common),
        FieldHuntStop((), "Ali Baba", route_vnums=("2639",), **common),
        FieldHuntStop(
            (),
            "Ali Baba",
            route_vnums=("2640", "2641", "2642", "2636"),
            **common,
        ),
        FieldHuntStop((), "Ali Baba", route_vnums=("2635",), **common),
        FieldHuntStop((), "Ali Baba", route_vnums=("2634",), **common),
    )


def pyramid_ali_baba_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one live-vetted Ali Baba under the ordinary field gates."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.90,
            maximum_level_offset=1,
        )
        for stop in pyramid_ali_baba_research_stops()
    )


def solace_lord_doom_research_stops() -> tuple[FieldHuntStop, ...]:
    """Probe the source-isolated Solace Lord Doom reset."""
    trivial_bystanders = (
        "Fewmaster Toede",
        "a Giant Kodiak bear",
        "the goblin",
        "the goblin lieutenant",
        "the beastly fido",
        "an alley cat",
    )
    return (
        FieldHuntStop(
            (),
            "Lord Doom",
            command_keyword="doom",
            actions=("where doom",),
            abort_if_where_target_absent=True,
            trivial_bystanders=trivial_bystanders,
            consider_only=True,
            exact_target=True,
            maximum_target_count=1,
            require_isolated=True,
            maximum_level_offset=2,
            abort_after_consider_rejection=True,
        ),
    )


def solace_lord_doom_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt one live-vetted Lord Doom after the current-band probe."""
    return tuple(
        replace(
            stop,
            consider_only=False,
            minimum_health_ratio=0.90,
        )
        for stop in solace_lord_doom_research_stops()
    )


def gnome_hermit_hunt_route() -> Fastwalk:
    """Return the source-derived recall route to the Gnome hermit crab."""
    return Fastwalk("gnome-hermit", 1, 7, "2s5es6ene3n")


def gnome_hermit_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Sweep the hermit and two separate miner resets after live assessment."""
    return (
        FieldHuntStop(
            (),
            "hermit",
            minimum_health_ratio=_FIELD_HIGH_RISK_START_HEALTH_RATIO,
            exact_target=True,
        ),
        FieldHuntStop(
            ("south", "south", "south"),
            "hobgoblin miner",
            exact_target=True,
        ),
        FieldHuntStop(
            ("east", "east"),
            "hobgoblin miner",
            exact_target=True,
        ),
    )


def gnome_guard_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Sweep three source-level-eight guard resets with independent gates."""
    return (
        FieldHuntStop((), "gnome guard", exact_target=True),
        FieldHuntStop(
            (
                "east",
                "east",
                "north",
                "north",
                "north",
                "north",
                "north",
                "north",
                "west",
            ),
            "gnome guard",
            exact_target=True,
        ),
        FieldHuntStop(
            ("west", "west", "south"),
            "gnome guard",
            exact_target=True,
        ),
    )


def gnome_guard_research_stops() -> tuple[FieldHuntStop, ...]:
    """Revalidate the unarmed hut guard without starting combat."""
    return (
        FieldHuntStop(
            (),
            "gnome guard",
            consider_only=True,
            exact_target=True,
        ),
    )


def gnome_treasurer_research_stops() -> tuple[FieldHuntStop, ...]:
    """Collect loose source-keyed coins and consider the isolated treasurer."""
    return (
        FieldHuntStop(
            (),
            "treasurer",
            actions=("get all.coins",),
            consider_only=True,
            exact_target=True,
        ),
    )


def gnome_treasurer_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Run one gated treasurer fight after a viable same-reboot probe."""
    return (
        FieldHuntStop(
            (),
            "treasurer",
            actions=("get all.coins",),
            minimum_health_ratio=0.90,
            exact_target=True,
            maximum_level_offset=1,
        ),
    )


def foundry_level_six_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Return the retired level-six Foundry template for evidence tests only."""
    return (
        FieldHuntStop(
            ("south", "south", "west", "west", "down", "east"),
            "uburz",
        ),
    )


def foundry_body_gear_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Acquire Oshu's low-level leather jerkin as missing-slot recovery."""
    return (
        FieldHuntStop(
            ("open east", "east"),
            "oshu",
            required_items=("leather jerkin",),
            exact_target=True,
            allow_below_band_for_required_loot=True,
        ),
    )


def foundry_set_circlet_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Search Uburz's safe Foundry corridor for the trainer-cap circlet."""
    routes = (
        (),
        ("west",),
        ("east", "south"),
        ("south",),
        ("east",),
        ("east",),
        ("west", "south"),
        ("west",),
        ("north", "west"),
        ("west",),
        ("down",),
        ("east",),
    )
    trivial_bystanders = (
        "garshgob",
        "olog",
        "golgog",
        "shargook",
        "lobuk",
        "hoobuk",
    )
    return tuple(
        FieldHuntStop(
            route,
            "uburz",
            required_items=("silver circlet",),
            post_actions=("wear circlet", "eq all"),
            exact_target=True,
            allow_below_band_for_required_loot=True,
            trivial_bystanders=trivial_bystanders,
        )
        for route in routes
    )


def school_accessory_hunt_route() -> Fastwalk:
    """Traverse the repeatable obstacle course to its portal room."""
    return Fastwalk(
        "mud-school-accessories",
        2,
        9,
        "u;open north;n;n;e;u;open west;w;open south;s;d",
        recall_after_loot=True,
    )


def school_wrist_float_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Acquire two copper bracers and the gladiator's floating stone."""
    return (
        FieldHuntStop((), actions=("enter portal",)),
        FieldHuntStop(
            (
                "north",
                "north",
                "open north",
                "north",
                "north",
                "open east",
                "east",
            ),
            "tall lizardman",
            required_items=("copper bracer",),
            exact_target=True,
            allow_below_band_for_required_loot=True,
        ),
        FieldHuntStop(
            (),
            actions=("sacrifice cape",),
        ),
        FieldHuntStop(
            ("west", "open north", "north"),
            "gladiator",
            required_items=(
                "copper bracer",
                "copper bracer",
                "snowy white stone",
            ),
            exact_target=True,
            allow_below_band_for_required_loot=True,
        ),
        FieldHuntStop(
            (),
            actions=(
                "unlock north",
                "open north",
                "north",
                "enter portal",
                "down",
                "down",
                "north",
            ),
        ),
    )


def gremlin_waist_hunt_route() -> Fastwalk:
    """Return the source-derived recall route to Gremlin Lair room 134."""
    return Fastwalk(
        "gremlin-lair-waist",
        2,
        9,
        "2s7w2s3de",
        recall_after_loot=True,
    )


def gremlin_waist_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Acquire a baby gremlin's basic waist-slot diaper."""
    return (
        FieldHuntStop(
            (),
            "baby gremlin",
            required_items=("diaper",),
            exact_target=True,
            allow_below_band_for_required_loot=True,
        ),
    )


def foundry_level_seven_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Return the retired level-seven Foundry template for evidence tests only."""
    return (
        FieldHuntStop(
            ("south", "south", "east"),
            "golgog",
            exact_target=True,
        ),
        FieldHuntStop(("south",), "shargook", exact_target=True),
        FieldHuntStop(
            ("north", "west", "west"),
            "lobuk",
            exact_target=True,
        ),
        FieldHuntStop(
            ("west", "down", "east"),
            "uburz",
            exact_target=True,
        ),
    )


def ambush_war_dog_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Go directly to the lower-HP Ambush target from the fastwalk endpoint."""
    exterior = ambush_exterior_hunt_stops()
    return (
        FieldHuntStop(
            exterior[0].route + exterior[1].route,
            "war dog",
        ),
    )


def ambush_level_eight_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt only the proven lower-burst war dog at level eight."""
    exterior = ambush_exterior_hunt_stops()
    return (
        FieldHuntStop(
            exterior[0].route + exterior[1].route,
            "war dog",
        ),
    )


def ambush_war_dog_collar_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Acquire one source-equipped +1 damroll collar from the war dog."""
    exterior = ambush_exterior_hunt_stops()
    return (
        FieldHuntStop(
            exterior[0].route + exterior[1].route,
            "war dog",
            post_actions=("wear collar", "eq all"),
            required_items=("war dog collar",),
            exact_target=True,
            allow_below_band_for_required_loot=True,
        ),
    )


def ambush_caster_level_eight_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Continue from the war dog to the source-level-seven goblin looter."""
    exterior = ambush_exterior_hunt_stops()
    return (
        FieldHuntStop(
            exterior[0].route + exterior[1].route,
            "war dog",
            exact_target=True,
        ),
        FieldHuntStop(
            exterior[2].route + exterior[3].route,
            "goblin looter",
            exact_target=True,
            minimum_combat_health_ratio=0.5,
        ),
    )


def ambush_martial_level_eight_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Sweep three loot-bearing exterior targets with the riskiest first."""
    exterior = ambush_exterior_hunt_stops()
    return (
        FieldHuntStop(
            exterior[0].route,
            "wounded goblin",
            minimum_health_ratio=_FIELD_HIGH_RISK_START_HEALTH_RATIO,
            exact_target=True,
        ),
        FieldHuntStop(
            exterior[1].route,
            "war dog",
            minimum_health_ratio=_FIELD_CONTINUE_HEALTH_RATIO,
            exact_target=True,
        ),
        FieldHuntStop(
            exterior[2].route + exterior[3].route,
            "goblin looter",
            minimum_health_ratio=_FIELD_CONTINUE_HEALTH_RATIO,
            exact_target=True,
        ),
    )


def ambush_guard_consider_stops() -> tuple[FieldHuntStop, ...]:
    """Reach the source-backed guard under invisibility and consider only."""
    return (
        FieldHuntStop(
            (
                "west",
                "south",
                "south",
                "west",
                "south",
                "west",
                "south",
                "south",
                "west",
                "south",
                "open west",
                "west",
                "south",
            ),
            "fanatical goblin guard",
            consider_only=True,
        ),
    )


def ambush_raider_consider_stops() -> tuple[FieldHuntStop, ...]:
    """Reach the armed raider's reset under invisibility and consider only."""
    return (
        FieldHuntStop(
            (
                "west",
                "south",
                "south",
                "west",
                "south",
                "west",
                "south",
                "south",
                "west",
            ),
            "goblin raider",
            consider_only=True,
            exact_target=True,
        ),
    )


def ambush_raider_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Live-consider one isolated raider with a full-health reserve."""
    stop = ambush_raider_consider_stops()[0]
    return (
        FieldHuntStop(
            stop.route,
            stop.target,
            minimum_health_ratio=_FIELD_HIGH_RISK_START_HEALTH_RATIO,
            exact_target=True,
        ),
    )


def ambush_vile_goblin_consider_stops() -> tuple[FieldHuntStop, ...]:
    """Reach the unarmed level-nine goblin and consider without attacking."""
    stop = ambush_vile_goblin_hunt_stops()[0]
    return (
        FieldHuntStop(
            stop.route,
            stop.target,
            allowed_bystanders=stop.allowed_bystanders,
            consider_only=True,
        ),
    )


def ambush_vile_goblin_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Reach and live-consider one unarmed level-nine goblin before combat."""
    return (
        FieldHuntStop(
            (
                "west",
                "south",
                "south",
                "west",
                "south",
                "west",
                "south",
                "south",
                "east",
                "south",
                "south",
                "open east",
                "east",
                "east",
                "south",
            ),
            "vile goblin",
            allowed_bystanders=("half clothed human female",),
        ),
    )


def midennir_horseman_consider_stops() -> tuple[FieldHuntStop, ...]:
    """Search observed wander rooms and the source trail without attacking."""
    return (
        FieldHuntStop((), "dark horseman", consider_only=True),
        FieldHuntStop(("south",), "dark horseman", consider_only=True),
        FieldHuntStop(("west",), "dark horseman", consider_only=True),
        FieldHuntStop(("south",), "dark horseman", consider_only=True),
        FieldHuntStop(("south",), "dark horseman", consider_only=True),
        FieldHuntStop(("west",), "dark horseman", consider_only=True),
        FieldHuntStop(("west",), "dark horseman", consider_only=True),
        FieldHuntStop(("south",), "dark horseman", consider_only=True),
        FieldHuntStop(("west",), "dark horseman", consider_only=True),
    )


def gnome_small_troll_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt the isolated aggressive troll only after an invisible approach."""
    return (
        FieldHuntStop(
            (),
            "small troll",
            minimum_health_ratio=_FIELD_HIGH_RISK_START_HEALTH_RATIO,
            exact_target=True,
        ),
    )


def midennir_horseman_probe_route() -> Fastwalk:
    """Stop at South Bridge so wandering horsemen are inspected on approach."""
    return Fastwalk(
        "midennir horseman approach",
        6,
        16,
        "5s",
        recall_after_loot=True,
    )


def moria_sanctuary_potion_consider_stops() -> tuple[FieldHuntStop, ...]:
    """Search the potion resets and nearby wander rooms without attacking."""
    def stop(
        route: tuple[str, ...],
        *,
        actions: tuple[str, ...] = (),
    ) -> FieldHuntStop:
        return FieldHuntStop(
            route,
            "large hobgoblin",
            actions=actions,
            consider_only=True,
            exact_target=True,
        )

    return (
        stop(
            ("east", "north", "north", "east", "south", "down"),
            actions=("where hobgoblin",),
        ),
        stop(("west",)),
        stop(("north",)),
        stop(("west",)),
        stop(("south",)),
        stop(("east",)),
        stop(("east",)),
        stop(("east",)),
        stop(("west", "south")),
        stop(("west",)),
        stop(("south",)),
        stop(("east",)),
        stop(("east",)),
    )


def moria_sanctuary_potion_hunt_stops() -> tuple[FieldHuntStop, ...]:
    """Hunt only the carrier's directly accessible reset room."""
    reset_room = moria_sanctuary_potion_consider_stops()[0]
    return (
        FieldHuntStop(
            reset_room.route,
            reset_room.target,
            actions=reset_room.actions,
            required_items=("purple potion", *reset_room.required_items),
            allowed_bystanders=reset_room.allowed_bystanders,
            trivial_bystanders=reset_room.trivial_bystanders,
            minimum_health_ratio=_FIELD_HIGH_RISK_START_HEALTH_RATIO,
            exact_target=reset_room.exact_target,
            allow_below_band_for_required_loot=True,
        )
        ,
    )


async def run_ambush_research_profile(
    path: str | Path,
    *,
    guard_probe: bool = False,
    vile_probe: bool = False,
    raider_probe: bool = False,
    raider_hunt: bool = False,
    horseman_probe: bool = False,
    vile_hunt: bool = False,
) -> RunResult:
    """Live-consider the source-backed exterior Ambush targets and return."""
    if (
        sum(
            (
                guard_probe,
                vile_probe,
                raider_probe,
                raider_hunt,
                horseman_probe,
                vile_hunt,
            )
        )
        > 1
    ):
        raise ValueError("choose only one Ambush probe target")
    profile_path = Path(path)
    spec = load_character_spec(profile_path)
    hunt_stops = ambush_level_seven_consider_stops()
    if guard_probe:
        hunt_stops = ambush_guard_consider_stops()
    elif vile_probe:
        hunt_stops = ambush_vile_goblin_consider_stops()
    elif raider_probe:
        hunt_stops = ambush_raider_consider_stops()
    elif raider_hunt:
        hunt_stops = ambush_raider_hunt_stops()
    elif horseman_probe:
        hunt_stops = midennir_horseman_consider_stops()
    elif vile_hunt:
        hunt_stops = ambush_vile_goblin_hunt_stops()
    return await StarterBotRunner(
        spec,
        profile_path,
        objective_level=11,
        fastwalk_route=(
            midennir_horseman_probe_route()
            if horseman_probe
            else route_named("ambush")
        ),
        fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
        fastwalk_hunt_stops=hunt_stops,
        fastwalk_train_before_departure=guard_probe or raider_hunt or vile_hunt,
        fastwalk_require_invisibility=True,
        fastwalk_kill_limit=1 if raider_hunt or vile_hunt else None,
        require_fastwalk_kill=False,
        allow_safe_fastwalk_abort=True,
    ).run()


async def run_shire_research_profile(
    path: str | Path,
    *,
    hunt: bool = False,
) -> RunResult:
    """Probe, or validate one kill against, the Watermill worker reset."""
    profile_path = Path(path)
    spec = load_character_spec(profile_path)
    return await StarterBotRunner(
        spec,
        profile_path,
        objective_level=8,
        fastwalk_route=shire_mill_worker_consider_route(),
        fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
        fastwalk_hunt_stops=(
            shire_mill_worker_hunt_stops()
            if hunt
            else shire_mill_worker_consider_stops()
        ),
        fastwalk_kill_limit=1 if hunt else None,
        require_fastwalk_kill=False,
        allow_safe_fastwalk_abort=True,
    ).run()


async def run_moria_research_profile(
    path: str | Path,
    *,
    depth: int = 0,
    sanctuary_probe: bool = False,
    sanctuary_hunt: bool = False,
) -> RunResult:
    if sanctuary_probe and sanctuary_hunt:
        raise ValueError("choose either a sanctuary probe or sanctuary hunt")
    profile_path = Path(path)
    spec = load_character_spec(profile_path)
    if sanctuary_probe or sanctuary_hunt:
        return await StarterBotRunner(
            spec,
            profile_path,
            objective_level=11,
            fastwalk_route=route_named("moria"),
            fastwalk_origin_actions=("get all.pie", "drink skin"),
            fastwalk_hunt_stops=(
                moria_sanctuary_potion_hunt_stops()
                if sanctuary_hunt
                else moria_sanctuary_potion_consider_stops()
            ),
            fastwalk_train_before_departure=sanctuary_hunt,
            fastwalk_require_invisibility=True,
            fastwalk_kill_limit=1 if sanctuary_hunt else None,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
        ).run()
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


def _can_persist_character(state: CharacterState) -> bool:
    """DD4 rejects save attempts until a character reaches level two."""
    return state.level is not None and state.level >= 2


def _health_ratio(state: CharacterState) -> float:
    if state.hp is None or state.max_hp in (None, 0):
        return 1.0
    return float(state.hp) / float(state.max_hp)


def _move_ratio(state: CharacterState) -> float:
    if state.move is None or state.max_move in (None, 0):
        return 1.0
    return float(state.move) / float(state.max_move)


def _enemy_records(value: Any) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    def collect(item: Any) -> None:
        if isinstance(item, dict):
            if isinstance(item.get("name"), str):
                records.append(item)
            for nested in item.values():
                collect(nested)
        elif isinstance(item, list):
            for nested in item:
                collect(nested)

    collect(value)
    unique: list[dict[str, Any]] = []
    signatures: set[str] = set()
    for record in records:
        if not {"name", "isnpc", "hp", "maxhp"}.issubset(record):
            unique.append(record)
            continue
        signature = json.dumps(record, sort_keys=True, default=str)
        if signature not in signatures:
            signatures.add(signature)
            unique.append(record)
    return unique


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _enemy_is_below_useful_band(
    enemy: dict[str, Any],
    character_level: int | None,
) -> bool:
    enemy_level = _int_or_none(enemy.get("level"))
    return (
        character_level is not None
        and enemy_level is not None
        and enemy_level <= character_level - 5
    )


def _mana_ratio(state: CharacterState) -> float:
    if state.mana is None or state.max_mana in (None, 0):
        return 1.0
    return float(state.mana) / float(state.max_mana)


def _recovery_ready(state: CharacterState) -> bool:
    return (
        _health_ratio(state) >= 0.95
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


def _watchdog_progress_marker(state: CharacterState) -> tuple[object, ...]:
    return (
        state.room_vnum,
        state.hp,
        state.mana,
        state.move,
        state.xp,
        state.level,
        state.in_combat,
        state.dead,
        state.position,
        _state_stat(state, "carry_num"),
        _state_stat(state, "carry_wt"),
        tuple(sorted((state.currencies or {}).items())),
        _watchdog_enemy_marker(state.enemies),
    )


def _watchdog_enemy_marker(value: Any) -> tuple[tuple[object, ...], ...]:
    """Track material GMCP combat progress without volatile description text."""
    return tuple(
        sorted(
            (
                normalize_item_name(str(enemy.get("name", ""))),
                str(enemy.get("isnpc", "")),
                _int_or_none(enemy.get("level")),
                _int_or_none(enemy.get("hp")),
                _int_or_none(enemy.get("maxhp")),
            )
            for enemy in _enemy_records(value)
        )
    )


def _route_cycle_watchdog_applies(
    command: str,
    repetitions: int,
    *,
    safe_city_return: bool = False,
    randomized_maze: bool = False,
) -> bool:
    """Detect repeated travel without treating normal combat rounds as loops."""
    return (
        not safe_city_return
        and not randomized_maze
        and command in _MOVEMENT_COMMANDS
        and repetitions > 4
    )


def _repeated_command_watchdog_applies(
    repetitions: int,
    limit: int,
    *,
    registered_trainer_return: bool = False,
) -> bool:
    """Allow a verified trainer return to outlive delayed GMCP room updates."""
    return not registered_trainer_return and repetitions > limit


def _gear_response_matches(expectation: str, recent: str) -> bool:
    """Recognize the response which completes a queued equipment command."""
    if expectation == "audit":
        return _equipment_audit_present(recent)
    if expectation == "wear":
        return any(
            phrase in recent
            for phrase in (
                "you wear ",
                "you wield ",
                "you cannot use ",
                "your profession prohibits wearing",
                "you do not have that item",
            )
        )
    if expectation == "remove":
        return any(
            phrase in recent
            for phrase in (
                "you stop using ",
                "you remove ",
                "you do not have that item",
            )
        )
    return False


_EQUIPMENT_SLOT_LABELS = (
    ("ranged weapon", "ranged_weapon"),
    ("second weapon", "wield"),
    ("used as light", "light"),
    ("worn on finger", "finger"),
    ("worn around neck", "neck"),
    ("worn on body", "body"),
    ("worn on head", "head"),
    ("worn on legs", "legs"),
    ("worn on feet", "feet"),
    ("worn on hands", "hands"),
    ("worn on arms", "arms"),
    ("worn about body", "about"),
    ("worn about waist", "waist"),
    ("worn around wrist", "wrist"),
    ("floating nearby", "float"),
    ("secured to belt", "pouch"),
    ("shield", "shield"),
    ("weapon", "wield"),
    ("held", "hold"),
)


def _equipment_slot_categories(text: str) -> set[str]:
    """Extract profession-available wear categories from an ``eq all`` listing."""
    cleaned = _ANSI_ESCAPE.sub("", text).casefold()
    cleaned = re.sub(r"\{.", "", cleaned)
    categories: set[str] = set()
    for line in cleaned.splitlines():
        for label, category in _EQUIPMENT_SLOT_LABELS:
            if label in line:
                categories.add(category)
                break
    return categories


def _equipment_empty_categories(text: str) -> set[str]:
    """Extract empty profession-available categories from an ``eq all`` listing."""
    return set(_equipment_empty_category_counts(text))


def _equipment_audit_descriptions(text: str) -> list[str]:
    """Extract occupied item descriptions from an ``eq all`` listing."""
    cleaned = _ANSI_ESCAPE.sub("", text)
    descriptions: list[str] = []
    for line in cleaned.splitlines():
        match = re.match(
            r"^\s*(?:<[^>]+>|\[[^\]]+\])\s*(?P<item>.+?)\s*$",
            line,
        )
        if match is None:
            continue
        description = match.group("item").strip()
        if description and description != "-":
            descriptions.append(description)
    return descriptions


def _equipment_empty_category_counts(text: str) -> Counter[str]:
    """Count empty profession-available slots in an ``eq all`` listing."""
    cleaned = _ANSI_ESCAPE.sub("", text).casefold()
    cleaned = re.sub(r"\{.", "", cleaned)
    categories: Counter[str] = Counter()
    for line in cleaned.splitlines():
        if not re.search(r"(?:>\s*|\]\s*)-\s*$", line):
            continue
        for label, category in _EQUIPMENT_SLOT_LABELS:
            if label in line:
                categories[category] += 1
                break
    return categories


def _shop_listed_item_level(text: str) -> int | None:
    cleaned = _ANSI_ESCAPE.sub("", text)
    match = re.search(r"\[\s*(\d+)\s+\d+\s*\]\s+\S", cleaned)
    return int(match.group(1)) if match is not None else None


def _equipment_audit_present(text: str) -> bool:
    recent = text.casefold()
    return (
        "you are not using any equipment" in recent
        or bool(_equipment_slot_categories(text))
    )


def _catalog_category_for_keyword(
    catalog: GearCatalog,
    keyword: str,
) -> str | None:
    categories = {
        category
        for item in catalog.objects.values()
        if item_keyword(item).casefold() == keyword.casefold()
        if (category := item_category(item)) is not None
    }
    if len(categories) == 1:
        return categories.pop()
    return None


def _is_stale_gear_ack(recent: str) -> bool:
    """Identify the previous command's acknowledgement before DD4 catches up."""
    if "ok." in recent:
        return True
    return re.fullmatch(
        r"\s*<\d+/\d+ hits .*?\[[^]]+\]>\s*",
        recent,
    ) is not None


def _consider_response_matches(recent: str) -> bool:
    """Recognize a DD4 consideration result after a delayed command pulse."""
    return any(
        phrase in recent
        for phrase in (*_CONSIDER_VIABLE_FRAGMENTS, *_CONSIDER_REJECTED_FRAGMENTS)
    )


def _policy_inactivity_due(
    policy: StarterPolicy,
    *,
    now: float,
    last_progress: float,
    timeout: float,
) -> bool:
    if policy.combat_active:
        # Automatic rounds can run for a long time without requiring another
        # command. Combat has its own bounded timeout, while the connection
        # loop separately detects a silent socket.
        return False
    if policy.waiting_for_move:
        # Sleeping at a vetted recovery point is intentional idle time. Live
        # vitals or prompt updates will wake the policy once movement recovers.
        return False
    wait_deadlines = (
        deadline
        for deadline in (
            policy.arena_respawn_due,
            policy.health_check_due,
            policy.fastwalk_post_flee_audit_due,
        )
        if deadline is not None
    )
    wait_until = max(wait_deadlines, default=None)
    if wait_until is not None and now < wait_until:
        return False
    return now - last_progress >= timeout


def _is_runtime_cap_error(exc: Exception) -> bool:
    return isinstance(exc, TimeoutError) and bool(
        re.fullmatch(r"Starter bot exceeded [0-9]+(?:\.[0-9]+)? second runtime", str(exc))
    )


def _exit_destination(
    exits: dict[str, str | None],
    direction: str,
) -> str | None:
    wanted = direction.casefold()
    for exit_direction, destination in exits.items():
        expanded = _DIRECTION_SHORTCUTS.get(
            str(exit_direction).casefold(),
            str(exit_direction).casefold(),
        )
        if expanded == wanted and destination is not None:
            return str(destination)
    return None


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


def _practice_balances(text: str) -> tuple[int | None, int | None]:
    cleaned = _ANSI_ESCAPE.sub("", text)
    matches = [
        match
        for pattern in (_PRACTICE_BALANCE, _SCORE_PRACTICE_BALANCE)
        for match in pattern.finditer(cleaned)
    ]
    if not matches:
        return None, None
    match = max(matches, key=lambda candidate: candidate.start())
    return int(match.group("physical")), int(match.group("intellectual"))


def _state_stat(state: CharacterState, name: str) -> int | None:
    value = state.stats.get(name)
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _has_named_affect(value: Any, name: str) -> bool:
    target = name.casefold()
    if isinstance(value, str):
        try:
            decoded = json.loads(_ANSI_ESCAPE.sub("", value))
        except json.JSONDecodeError:
            return target in value.casefold()
        return _has_named_affect(decoded, name)
    if isinstance(value, Mapping):
        affect_name = value.get("name")
        if isinstance(affect_name, str):
            return affect_name.casefold() == target
        return any(_has_named_affect(item, name) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_has_named_affect(item, name) for item in value)
    return False


def _training_targets(text: str) -> list[str]:
    return list(_training_target_counts(text))


@lru_cache(maxsize=4)
def _load_source_mobile_targets(
    area_directory: str,
) -> dict[str, tuple[str, ...]]:
    """Index exact mobile display lines from every public DD4 area file."""
    world = load_world_source(Path(area_directory), include_all_areas=True)
    indexed: dict[str, list[str]] = {}
    for mobile in world.mobiles.values():
        targets = _source_mobile_identities(
            mobile.room_description,
            mobile.short_description,
            mobile.keywords,
        )
        for source_line in {
            _normalize_mobile_line(mobile.room_description),
            _normalize_mobile_line(mobile.short_description),
        } - {""}:
            known = indexed.setdefault(source_line, [])
            known.extend(
                target for target in targets if target and target not in known
            )
    return {line: tuple(targets) for line, targets in indexed.items()}


@lru_cache(maxsize=4)
def _load_source_mobile_level_ranges(
    area_directory: str,
) -> dict[str, tuple[int, int]]:
    """Index conservative DD4 mobile levels after its two fuzz operations."""
    world = load_world_source(Path(area_directory), include_all_areas=True)
    indexed: dict[str, tuple[int, int]] = {}
    for mobile in world.mobiles.values():
        targets = _source_mobile_identities(
            mobile.room_description,
            mobile.short_description,
            mobile.keywords,
        )
        level_range = (max(1, mobile.level - 2), mobile.level + 2)
        for target in targets:
            previous = indexed.get(target)
            if previous is None:
                indexed[target] = level_range
            else:
                indexed[target] = (
                    min(previous[0], level_range[0]),
                    max(previous[1], level_range[1]),
                )
    return indexed


def _source_mobile_identities(
    room_description: str,
    short_description: str,
    keywords: str = "",
) -> tuple[str, ...]:
    """Prefer an explicit proper name when a mobile's live line is generic."""
    parsed = tuple(_training_target_counts(room_description))
    cleaned_short = _MUD_COLOUR_CODE.sub(
        "",
        _ANSI_ESCAPE.sub("", short_description),
    ).strip()
    normalized_short = normalize_item_name(cleaned_short)
    normalized_keywords = normalize_item_name(keywords)
    short_tokens = normalized_short.split()
    keyword_tokens = normalized_keywords.split()
    keyword_in_short = bool(
        keyword_tokens
        and any(
            short_tokens[index : index + len(keyword_tokens)] == keyword_tokens
            for index in range(len(short_tokens) - len(keyword_tokens) + 1)
        )
    )
    display_words = cleaned_short.split()
    if display_words and display_words[0].casefold() in {"a", "an", "the"}:
        display_words = display_words[1:]
    has_explicit_name = bool(
        display_words
        and display_words[0][:1].isupper()
    )
    has_title_case_tail = any(
        word[:1].isupper() for word in display_words[1:]
    )
    has_proper_name_shape = len(display_words) == 1 or has_title_case_tail
    if has_explicit_name and has_proper_name_shape and not any(
        _targets_match(normalized_short, target) for target in parsed
    ):
        return (normalized_short,)
    if keyword_in_short and (len(keyword_tokens) > 1 or has_explicit_name):
        return (normalized_keywords,)
    return parsed or (normalized_short or normalized_keywords,)


def _room_mobile_target_counts(
    text: str,
    source_mobile_targets: Mapping[str, tuple[str, ...]],
) -> dict[str, int]:
    """Recognize source-defined mobile lines before parsing unknown live prose."""
    if not source_mobile_targets:
        return _training_target_counts(text)

    lines = text.splitlines()
    normalized = [_normalize_mobile_line(line) for line in lines]
    matched_lines: set[int] = set()
    targets: Counter[str] = Counter()
    for width in range(min(4, len(lines)), 0, -1):
        for start in range(0, len(lines) - width + 1):
            indexes = range(start, start + width)
            if any(index in matched_lines for index in indexes):
                continue
            source_targets = source_mobile_targets.get(
                " ".join(normalized[index] for index in indexes).strip()
            )
            if source_targets is None:
                continue
            matched_lines.update(indexes)
            targets.update(source_targets)

    unmatched = "\n".join(
        line for index, line in enumerate(lines) if index not in matched_lines
    )
    targets.update(_training_target_counts(unmatched))
    return dict(targets)


def _normalize_mobile_line(value: str) -> str:
    value = _TARGET_SELECTOR_PREFIX.sub("", value)
    value = _MUD_COLOUR_CODE.sub("", _ANSI_ESCAPE.sub("", value)).strip()
    value = _MOBILE_STATUS_PREFIX.sub("", value)
    return " ".join(value.casefold().split())


def _training_target_counts(text: str) -> dict[str, int]:
    text = _TARGET_SELECTOR_PREFIX.sub("", text)
    verbs = (
        r"(?:is|are|sits?|circles?|stands?|waits?|prepares?|paces?|runs?|"
        r"greets?|growls?|prowls?|hisses?|snarls?|slithers?|cowers?|lies?|looks?|"
        r"watches?|spits?|barks?|glares?|grunts?|screams?|cries?|crawls?|"
        r"lunges?|shuffles?|crouches?|scowls?|yells?|cringes?|tries?|makes?|"
        r"mumbles?|mutters?|poses?|monitors?)"
    )
    patterns = (
        re.compile(
            r"(?:^|\n)\s*(?:\([^)]*\)\s*)*"
            r"(?P<target>[A-Z][A-Za-z'-]*"
            r"(?:\s+[A-Z][A-Za-z'-]*){0,2}),\s+"
            r"(?:the\s+)?[A-Z][A-Za-z' -]{1,60},\s+"
            rf"(?:[A-Za-z]+ly\s+)?{verbs}\b",
        ),
        re.compile(
            r"(?:^|\n)\s*(?:\([^)]*\)\s*)*(?:A|An|The|This)\s+"
            r"(?P<target>[A-Za-z][A-Za-z'-]*"
            r"(?:\s+[A-Za-z][A-Za-z'-]*){0,3}?)\s+"
            rf"(?:[A-Za-z]+ly\s+)?{verbs}\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"(?:^|\n)\s*(?:\([^)]*\)\s*)*"
            r"(?!(?:A|An|The|This)\s)"
            r"(?P<target>[A-Z][A-Za-z'-]*"
            r"(?:\s+[A-Za-z][A-Za-z'-]*){0,3}?)\s+"
            rf"(?:[A-Za-z]+ly\s+)?{verbs}\b",
        ),
    )
    ignored_keywords = {
        "autoloot",
        "board",
        "chairs",
        "ceiling",
        "cleric",
        "corpse",
        "door",
        "floor",
        "gate",
        "heart",
        "it",
        "imp",
        "officer",
        "place",
        "portal",
        "recruit",
        "recruits",
        "room",
        "soldier",
        "soldiers",
        "staircase",
        "there",
        "tunnel",
        "wall",
        "yard",
        "you",
        "your",
    }
    targets: Counter[str] = Counter()
    for pattern in patterns:
        for match in pattern.finditer(text):
            target = " ".join(match.group("target").casefold().split())
            line_end = text.find("\n", match.end())
            if line_end < 0:
                line_end = len(text)
            activity = text[match.start():line_end].casefold()
            if target == "goblin" and "looting the dead" in activity:
                target = "goblin looter"
            words = set(target.replace("'s", "").split())
            if (
                not words.intersection(ignored_keywords)
                and not target.startswith("imp ")
            ):
                targets[target] += 1
    return dict(targets)


def _room_mobile_target_selectors(
    text: str,
    source_mobile_targets: Mapping[str, tuple[str, ...]],
) -> dict[str, list[str]]:
    """Map DD4 TARGETMODE IDs to source-recognized mobile identities."""
    lines = text.splitlines()
    selectors: dict[str, list[str]] = {}
    for start, line in enumerate(lines):
        prefix = _TARGET_SELECTOR_PREFIX.match(line)
        if prefix is None:
            continue
        selector = f"#{prefix.group('target_id')}"
        segment_end = min(start + 4, len(lines))
        next_selector = next(
            (
                index
                for index in range(start + 1, segment_end)
                if _TARGET_SELECTOR_PREFIX.match(lines[index])
            ),
            segment_end,
        )
        source_targets: tuple[str, ...] | None = None
        for width in range(next_selector - start, 0, -1):
            normalized = " ".join(
                _normalize_mobile_line(lines[index])
                for index in range(start, start + width)
            ).strip()
            source_targets = source_mobile_targets.get(normalized)
            if source_targets is not None:
                break
        if source_targets is None:
            if source_mobile_targets:
                continue
            fallback = _training_target_counts(
                "\n".join(lines[start:next_selector])
            )
            if len(fallback) != 1:
                continue
            source_targets = (next(iter(fallback)),)
        for target in source_targets:
            known = selectors.setdefault(target, [])
            if selector not in known:
                known.append(selector)
    return selectors


def _subtract_target_counts(
    observed: Mapping[str, int],
    description: Mapping[str, int],
) -> dict[str, int]:
    """Remove mobile-shaped prose already identified as static room description."""
    return {
        target: remaining
        for target, count in observed.items()
        if (remaining := count - description.get(target, 0)) > 0
    }


def _defeated_mobile(text: str) -> str | None:
    match = _MOB_DEATH.search(text)
    if match is None:
        return None
    words = match.group("target").casefold().split()
    while words and words[0] in {"a", "an", "the"}:
        words.pop(0)
    return " ".join(words) or None


def _text_mentions_target(text: str, target: str) -> bool:
    keyword = _target_keyword(target)
    return bool(re.search(rf"\b{re.escape(keyword)}\b", text, re.IGNORECASE))


def _target_keyword(target: str) -> str:
    return target.rsplit(maxsplit=1)[-1]


def _targets_match(observed: str, requested: str) -> bool:
    """Treat a requested descriptor and the MUD's shorter mobile name as equivalent."""
    observed_words = observed.split()
    requested_words = requested.split()
    proper_name_prefix = (
        len(observed_words) == 1
        and len(requested_words) > 1
        and observed_words[0][:1].isupper()
        and observed_words[0].casefold() == requested_words[0].casefold()
    ) or (
        len(requested_words) == 1
        and len(observed_words) > 1
        and requested_words[0][:1].isupper()
        and requested_words[0].casefold() == observed_words[0].casefold()
    )
    return (
        observed.casefold() == requested.casefold()
        or _target_keyword(observed).casefold()
        == _target_keyword(requested).casefold()
        or proper_name_prefix
    )


def _stop_target_matches(
    observed: str,
    requested: str,
    stop: FieldHuntStop | None,
) -> bool:
    if stop is not None and stop.exact_target:
        return observed.casefold() == requested.casefold()
    return _targets_match(observed, requested)


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


def _inventory_food_keyword(
    value: Any,
    gear_catalog: GearCatalog | None = None,
) -> str | None:
    """Return a source keyword for one carried, non-poisonous food item."""
    for description in _inventory_descriptions(value):
        normalized = normalize_item_name(description)
        item = gear_catalog.match(description) if gear_catalog is not None else None
        if (
            item is not None
            and item.item_type == ITEM_FOOD
            and len(item.values) >= 4
            and item.values[3] <= 0
        ):
            return item_keyword(item)
        # These are the ordinary food nouns already used by the live parser.
        # Prefer source matching above; retain this narrow fallback for a live
        # inventory line whose prototype cannot yet be matched.
        for keyword in ("pie", "steak"):
            if keyword in normalized:
                return keyword
    return None


def _has_inventory_food(
    value: Any,
    gear_catalog: GearCatalog | None = None,
) -> bool:
    return _inventory_food_keyword(value, gear_catalog) is not None


def _missing_required_inventory_items(
    value: Any,
    required_items: tuple[str, ...],
) -> list[str]:
    descriptions = [
        description.casefold()
        for description in _inventory_descriptions(value)
    ]
    missing: list[str] = []
    for item, required_count in Counter(required_items).items():
        available_count = sum(
            item.casefold() in description for description in descriptions
        )
        missing.extend([item] * max(0, required_count - available_count))
    return missing


def _known_combat_potion_keyword(value: Any) -> str | None:
    """Return only potions whose DD4 source effects are explicitly known."""
    descriptions = {
        normalize_item_name(description)
        for description in _inventory_descriptions(value)
    }
    if "black potion" in descriptions:
        return "black"
    if "purple potion" in descriptions:
        return "purple"
    return None


def _emergency_provision_potion_keyword(
    value: Any,
    gear_catalog: GearCatalog | None,
) -> str | None:
    """Choose the weakest safe healing potion for one emergency food sale."""
    if gear_catalog is None:
        return None
    descriptions = _inventory_descriptions(value)
    if isinstance(value, (list, tuple)):
        descriptions.extend(str(item) for item in value if isinstance(item, str))
    candidates: list[tuple[int, int, str]] = []
    for description in descriptions:
        normalized = normalize_item_name(description)
        if "black potion" in normalized or "purple potion" in normalized:
            continue
        item = gear_catalog.match(description)
        if item is None or item.item_type != 10:
            continue
        shop = safe_shop_for_item(
            item.short_description,
            item_type=item.item_type,
        )
        if shop is None:
            continue
        effect_value = int(item.values[0]) if item.values else 0
        potion_keyword = next(
            (
                keyword
                for keyword in item.keywords.casefold().split()
                if keyword != "potion" and keyword in normalized.split()
            ),
            item_command_keyword(item),
        )
        candidates.append(
            (
                effect_value,
                int(item.source_cost),
                potion_keyword,
            )
        )
    if not candidates:
        return None
    return min(candidates)[2]


def _inventory_command_keyword(
    description: str,
    gear_catalog: GearCatalog | None,
) -> str:
    """Prefer the source keyword over display-text noun inference."""
    inferred = sale_keyword(description)
    item = gear_catalog.match(description) if gear_catalog is not None else None
    if item is None:
        return inferred
    if inferred in item.keywords.casefold().split():
        return inferred
    return item_keyword(item)


def _inferior_carried_weapon(
    item: ObjectSource | None,
    gear_catalog: GearCatalog | None,
    worn_descriptions: Collection[str] | None,
) -> bool:
    """Recognize a protected weapon made redundant by the current primary."""
    if (
        item is None
        or gear_catalog is None
        or item_category(item) != "wield"
        or not worn_descriptions
    ):
        return False
    worn_items = [
        worn
        for description in worn_descriptions
        if (worn := gear_catalog.match(description)) is not None
        and item_category(worn) == "wield"
    ]
    if not worn_items:
        return False
    # Preserve a carried role weapon until the corresponding role is already
    # covered by worn gear; this keeps backstab and stun recovery possible.
    if is_piercing_weapon(item) and not any(
        is_piercing_weapon(worn) for worn in worn_items
    ):
        return False
    if is_blunt_weapon(item) and not any(
        is_blunt_weapon(worn) for worn in worn_items
    ):
        return False
    carried_score = stance_score(item, STANCE_COMBAT)
    return any(
        stance_score(worn, STANCE_COMBAT) > carried_score
        for worn in worn_items
    )


def _sellable_inventory_keyword(
    value: Any,
    gear_catalog: GearCatalog | None = None,
    *,
    worn_descriptions: Collection[str] | None = None,
) -> str | None:
    """Choose a conservative equipment keyword, never food or water storage."""
    names = _inventory_descriptions(value)
    if any("war dog collar" in name.casefold() for name in names):
        return "collar"
    duplicate_counts = Counter(normalize_item_name(name) for name in names)
    equipment_words = {
        "armor", "axe", "belt", "blade", "boots", "bracer", "cape", "cloak",
        "dagger", "gloves", "guards", "helm", "leggings", "mace", "shield",
        "sleeves", "spear", "sword", "vest", "wand", "weapon",
    }
    for name in names:
        item = gear_catalog.match(name) if gear_catalog is not None else None
        redundant_weapon = _inferior_carried_weapon(
            item,
            gear_catalog,
            worn_descriptions,
        )
        if (
            item is not None
            and protects_from_sale(item)
            and not redundant_weapon
            and not is_strength_penalty_ring(item)
        ):
            category = item_category(item)
            retained_capacity = {
                "finger": 2,
                "neck": 2,
                "wrist": 2,
            }.get(category or "", 1)
            if duplicate_counts[normalize_item_name(name)] <= retained_capacity:
                continue
        words = re.findall(r"[a-z0-9]+", name.casefold())
        if {"pie", "skin", "water", "food"}.intersection(words):
            continue
        for word in reversed(words):
            if word in equipment_words:
                return word
        if (
            item is not None
            and not (
                item.item_type in {10, 19}
                and not is_disposable_food(item)
            )
            and safe_shop_for_item(
                item.short_description,
                item_type=item.item_type,
            )
            is not None
        ):
            return item_keyword(item)
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
        quantity = _int_or_none(value.get("quan")) or 1
        result = (
            [str(description)] * max(1, quantity)
            if isinstance(description, str)
            else []
        )
        for item in value.values():
            result.extend(_inventory_descriptions(item))
        return result
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(_inventory_descriptions(item))
        return result
    return []


def _nested_inventory_items(text: str) -> list[tuple[str, str]]:
    """Return items shown inside named containers by DD4's inventory command."""
    nested: list[tuple[str, str]] = []
    outer: str | None = None
    for raw_line in _ANSI_ESCAPE.sub("", text).replace("\r", "").splitlines():
        header = re.fullmatch(r"Your\s+(.+?)\s+contains:", raw_line.strip(), re.I)
        if header is not None:
            outer = header.group(1)
            continue
        if outer is None:
            continue
        if raw_line[:1].isspace() and raw_line.strip():
            nested.append((outer, raw_line.strip()))
            continue
        if raw_line.strip():
            outer = None
    return nested


def _equipment_weapon_slot(text: str) -> tuple[bool, str | None]:
    match = _EQUIPMENT_WEAPON_SLOT.search(_ANSI_ESCAPE.sub("", text))
    if match is None:
        return False, None
    description = match.group("item").strip()
    if description == "-":
        return True, None
    return True, description


def _direct_weapon_slot_acknowledgement(
    response: str,
) -> tuple[bool, str | None] | None:
    """Extract a direct wield or stop-using acknowledgement from game text."""
    wielded = re.search(
        r"(?im)^\s*you wield\s+(?P<item>.+?)(?:[.!]\s*$|\s*$)",
        response,
    )
    if wielded is not None:
        return True, wielded.group("item").strip()
    if re.search(r"(?im)^\s*you stop using\s+", response):
        return False, None
    return None


def _equipment_descriptions(value: Any) -> list[str]:
    if isinstance(value, str):
        cleaned = _ANSI_ESCAPE.sub("", value).strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            return []
        return _equipment_descriptions(parsed)
    if isinstance(value, dict):
        description = value.get("name", value.get("short_desc"))
        result = [str(description)] if isinstance(description, str) else []
        for key, item in value.items():
            if key not in {"name", "short_desc"}:
                result.extend(_equipment_descriptions(item))
        return result
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(_equipment_descriptions(item))
        return result
    return []


def _near_level_gain(state: CharacterState) -> bool:
    if state.xp_to_next_level is None:
        return False
    level_span = state.progress.get("xplvl") if isinstance(state.progress, dict) else None
    if not isinstance(level_span, (int, float)):
        level_span = 2500
    threshold = max(250, int(level_span * _PRE_LEVEL_XP_FRACTION))
    return 0 < state.xp_to_next_level <= threshold


def _selected_training_stat(command: str | None) -> str | None:
    if command is None:
        return None
    match = re.fullmatch(r"train\s+(str|int|wis|dex|con)", command.casefold())
    return match.group(1) if match is not None else None
