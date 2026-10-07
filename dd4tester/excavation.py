"""Source-derived hoard budgets and response-driven digging, not route admission.

This controller is not wired into live quest dispatch. A caller must first
prove tool identity, an empty endpoint, a curse-safe physical return, and a
guardian escape plan. Unearthing alone never proves possession or quest
completion. The controller records possession only from a source-unique
description, a selector from a complete room listing, and a one-item increase
in a later complete carried-inventory snapshot. The selector is not expected
to appear in Char.Items.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import re
from typing import Collection, Mapping

from .equipment import ITEM_DIGGER, normalize_item_name
from .hunt_candidates import (
    ITEM_DONOT_RANDOMISE, ObjectSource, WorldSource,
    _apply_mobile_damage_modifier,
    _mobile_normal_hit_damage, _mobile_peak_round_damage,
    _mobile_critical_hit_damage, _source_dex_swiftness,
    mobile_expected_round_damage,
    mobile_sanctuary_critical_hit_damage, mobile_sanctuary_peak_round_damage,
)
from .observations import _DD4_PROMPT


# const.c:digmod_terrain_list, ordered wait/damage/movement percentages.
_TERRAIN = (
    (50, -25, 50), (75, -50, 75), (-75, 75, -50), (-60, 60, -40),
    (-40, 40, -45), (0, -10, -15), None, None, None, None,
    (-80, 80, -25), (-30, 25, 20), (60, 40, 45),
)
_TRAP = "You hear a strange noise..."
_MUD_COLOUR_CODE = re.compile(r"(?:\{.|<\d+>)")
_MAX_HOARD_TRAP_CHARGES = 3
_SUCCESS = "With a final effortful thrust, you unearth something!"
_FUTILE = "You dig into the earth... but get the feeling you're wasting your time."
_TRAP_EFFECT_MARKERS = {
    "fire": ("a fireball shoots out of",),
    "cold": ("a blast of frost from",),
    "acid": ("a blast of acid erupts from",),
    "energy": ("a pulse of energy from",),
    "blunt": ("you are hit by a blunt object from",),
    "pierce": (
        "you set off a trap and are pierced through the chest!",
        "you are hit by a piercing object!",
    ),
    "slash": (
        "you just got slashed by a trap",
        "one of the blades slashes you in the chest!",
    ),
    "poison": ("you are struck by a small dart",),
    "snare": ("you are entangled in a snare",),
    "curse": (
        "you feel unclean.",
        "dark energy washes over you, but fades harmlessly away.",
    ),
    "hex": (
        "you feel unbelievably dirty.",
        "a dark power gathers in the air... and fizzles.",
        "a malicious curse is cast, but you are already defiled.",
    ),
    "spirit": ("a furious spirit guardian materialises from thin air!",),
}
_REFUSALS = (
    "You're in no position to do any digging right now.",
    "You can't dig, you've been SWALLOWED!", "Not in your current state.",
    "While you're fighting?  No.", "Dismount first.",
    "Your arms are too badly damaged to dig.",
    "You can't dig in this sort of terrain.", "You have no way of doing that.",
    "You're too inexperienced to use that digging implement effectively.",
    "You're too exhausted to dig.",
)


def identify_hoard_trap_effect(text: str) -> str | None:
    """Identify one exact effect message emitted by DD4's hoard trap code.

    ``None`` means either no trap fired or the effect was not uniquely
    identified. Callers must separately confirm the trap marker before
    treating an unclassified response as an unknown trap.
    """
    normalized = _MUD_COLOUR_CODE.sub("", text).casefold()
    if _TRAP.casefold() not in normalized:
        return None
    matches = {
        kind
        for kind, markers in _TRAP_EFFECT_MARKERS.items()
        if any(marker in normalized for marker in markers)
    }
    return next(iter(matches)) if len(matches) == 1 else None


def _inventory_entries(value: object) -> list[Mapping[str, object]] | None:
    """Flatten DD4's nested Char.Items arrays without accepting partial data."""
    entries: list[Mapping[str, object]] = []

    def visit(item: object) -> bool:
        if isinstance(item, Mapping):
            if "short_desc" in item:
                quantity = item.get("quan")
                description = item.get("short_desc")
                if (
                    not isinstance(description, str)
                    or not description.strip()
                    or not (
                        type(quantity) is int and quantity > 0
                        or isinstance(quantity, str)
                        and quantity.isdecimal()
                        and int(quantity) > 0
                    )
                ):
                    return False
                entries.append(item)
                return True
            return bool(item) and all(visit(child) for child in item.values())
        if isinstance(item, (list, tuple)):
            return all(visit(child) for child in item)
        return False

    if not visit(value):
        return None
    return entries


def _inventory_count(value: object, description: str) -> int | None:
    entries = _inventory_entries(value)
    if entries is None:
        return None
    normalized = normalize_item_name(description)
    total = 0
    for item in entries:
        if normalize_item_name(str(item["short_desc"])) == normalized:
            total += int(item["quan"])
    return total


def shop_digger_level_bounds(tool: ObjectSource) -> tuple[int, int]:
    """Bound a source-matched digging tool bought from a DD4 shop.

    ``db.c`` loads ordinary shop stock at ``number_fuzzy(prototype.level)``
    (unless the object is ``ITEM_DONOT_RANDOMISE``), then ``do_buy`` clones
    that stock object's level. This returns a bound, not proof that a carried
    item came from this stock; callers must establish that identity separately.
    """
    if (
        type(tool.level) is not int or tool.level < 0
        or tool.item_type != ITEM_DIGGER
        or type(tool.extra_flags) is not int
    ):
        raise ValueError("shop level bounds require a source-identified digging tool")
    if tool.extra_flags & ITEM_DONOT_RANDOMISE:
        level = min(tool.level, 100)
        return level, level
    if tool.level == 0:
        return 0, 0
    if tool.level >= 100:
        return 99, 100
    return max(1, tool.level - 1), tool.level + 1


@dataclass(frozen=True)
class DigBudget:
    tool_vnum: int
    tool_name: str
    sector_type: int
    minimum_damage: int
    maximum_digs: int
    maximum_move_per_dig: int
    maximum_wait_pulses: int

    @property
    def maximum_movement(self) -> int:
        return self.maximum_dig_commands * self.maximum_move_per_dig

    @property
    def maximum_dig_commands(self) -> int:
        # The final excavation command can trigger a charge and return before
        # the hoard contents spill. Each remaining charge needs another dig,
        # followed by one final command after the charges are spent.
        return self.maximum_digs + _MAX_HOARD_TRAP_CHARGES

    @property
    def maximum_wait_seconds(self) -> float:
        # WAIT_STATE is measured in server pulses, four per second.
        return self.maximum_wait_pulses / 4.0


def tool_dig_budget(
    tool: ObjectSource, *, sector_type: int, race: str, level: int,
    observed_tool_level: int | None, strength: int, constitution: int, dexterity: int,
    swiftness: int, enhanced_swiftness_percent: int,
    source_tool_level_bounds: tuple[int, int] | None = None,
    depth: int = 200, haste: bool = False,
    quicken: bool = False, bonus_attack: bool = False,
    cannot_see_self: bool = False, slow: bool = False,
) -> DigBudget:
    """Bound one ITEM_DIGGER excavation using act_obj.c and db.c.

    swiftness is Char.Stats.swift (GET_SWIFT). Digging omits its learned
    enhanced-swiftness bonus, but retains its dex_app[].toswift contribution.
    Tool load-level admission requires an observed instance level or a
    conservative source-backed range from its exact shop stock.
    """
    numbers = (sector_type, level, strength, constitution, dexterity,
               swiftness, enhanced_swiftness_percent, depth)
    if any(type(value) is not int or value == 50000 for value in numbers):
        raise ValueError("digging requires complete revealed integer observations")
    if observed_tool_level is not None and (
        type(observed_tool_level) is not int or observed_tool_level == 50000
    ):
        raise ValueError("observed digging-tool level is malformed")
    if not 1 <= level <= 100 or not 1 <= depth <= 200:
        raise ValueError("invalid character, tool level, or excavation depth")
    if source_tool_level_bounds is not None:
        if (
            not isinstance(source_tool_level_bounds, tuple)
            or len(source_tool_level_bounds) != 2
            or any(type(value) is not int for value in source_tool_level_bounds)
            or source_tool_level_bounds[0] < 0
            or source_tool_level_bounds[1] < source_tool_level_bounds[0]
            or source_tool_level_bounds[1] > 100
        ):
            raise ValueError("invalid source-backed digging-tool level range")
        if (
            observed_tool_level is not None
            and not source_tool_level_bounds[0]
            <= observed_tool_level
            <= source_tool_level_bounds[1]
        ):
            raise ValueError("observed tool level falls outside its source bound")
        maximum_tool_level = source_tool_level_bounds[1]
    else:
        maximum_tool_level = observed_tool_level
    if (
        type(maximum_tool_level) is not int
        or not 0 <= maximum_tool_level <= level
    ):
        raise ValueError("digging requires a tool whose maximum level is usable")
    if not 0 <= sector_type < len(_TERRAIN) or _TERRAIN[sector_type] is None:
        raise ValueError("unsupported digging terrain")
    if (
        tool.item_type != ITEM_DIGGER or len(tool.values) != 4
        or any(type(value) is not int for value in tool.values)
        or tool.values[0] < 1 or not 1 <= tool.values[1] <= tool.values[2]
        or tool.values[3] < 1 or not 1 <= strength <= 31
        or not 1 <= constitution <= 31
    ):
        raise ValueError("invalid source digger or current stat observations")
    dex_swift = _source_dex_swiftness(dexterity)
    if dex_swift is None or not 0 <= enhanced_swiftness_percent <= 100:
        raise ValueError("dexterity or practiced swiftness is outside the source range")
    wait_mod, damage_mod, move_mod = _TERRAIN[sector_type]
    racial_bonus = race.casefold() in {"dwarf", "duergar"}
    damage = tool.values[1] * (1 + damage_mod / 100) + strength / 3
    if racial_bonus:
        damage *= 1.25
    minimum_damage = max(1, int(damage + 0.5))
    # Both create_object and do_dig independently fuzzy-roll wait and cost.
    # ITEM_DONOT_RANDOMISE does not suppress the ITEM_DIGGER switch case.
    movement = max((tool.values[3] + 2) * (1 + move_mod / 100) - constitution / 2, 1)
    if racial_bonus:
        movement = max(movement * 0.75, 1)
    wait = max((tool.values[0] + 2) * (1 + wait_mod / 100) - dexterity / 6, 1)
    digging_swiftness = swiftness - enhanced_swiftness_percent // 4
    wait = max(wait - digging_swiftness / 20, 1)
    for applies, multiplier in ((haste, 0.8), (quicken, 0.8), (bonus_attack, 0.9),
                                (cannot_see_self, 1.2), (racial_bonus, 0.5), (slow, 3.0)):
        if applies:
            wait = max(wait * multiplier, 1)
    return DigBudget(
        tool.vnum, tool.short_description, sector_type, minimum_damage,
        math.ceil(depth / minimum_damage), int(movement + 0.5), int(wait + 0.5),
    )


def maximum_hoard_direct_damage(level: int, armor_class: int) -> int:
    """Bound unprotected physical/elemental damage, not guardian attacks.

    Room-wide physical traps use full GET_AC; single-target traps use AC/4.
    The cap and any protective reductions can only lower this upper bound.
    """
    if type(level) is not int or not 1 <= level <= 100:
        raise ValueError("invalid hoard level")
    if type(armor_class) is not int or armor_class == 50000:
        raise ValueError("a revealed armor class is required")
    return max(6 * level, 10 * level + int(armor_class / 4), 10 * level + armor_class)


@dataclass(frozen=True)
class HoardGuardianDamage:
    """Raw attacks, not final damage after victim posture/vulnerability effects."""

    level: int
    maximum_hp: int
    expected_round_damage: int
    maximum_peak_round_damage: int
    maximum_ordinary_hit: int
    maximum_critical_hit: int
    maximum_attacks: int
    sanctuary: bool

    @property
    def ordinary_peak_round(self) -> int:
        return self.maximum_ordinary_hit * self.maximum_attacks

    @property
    def all_critical_peak_round(self) -> int:
        return self.maximum_critical_hit * self.maximum_attacks

    def maximum_attack_rounds_before_command(self, wait_pulses: int) -> int:
        """Include trap.c's immediate multi_hit and violence during lag.

        DD4 updates player wait once per quarter-second pulse and violence
        every twelve pulses. Since the violence timer phase is not observable,
        count one immediate burst plus every scheduled tick up to the full
        admitted dig wait. This is a raw bound, not a predicted exchange.
        """
        if type(wait_pulses) is not int or wait_pulses < 0:
            raise ValueError("guardian window needs an integer dig wait in pulses")
        return 1 + math.ceil(wait_pulses / 12)

    def maximum_damage_before_command(
        self, wait_pulses: int, *, every_hit_critical: bool = False,
    ) -> int:
        if type(every_hit_critical) is not bool:
            raise ValueError("guardian critical-hit assumption must be explicit")
        hit = self.maximum_critical_hit if every_hit_critical else self.maximum_ordinary_hit
        return hit * self.maximum_attack_rounds_before_command(wait_pulses) * self.maximum_attacks


def hoard_guardian_damage(
    world: WorldSource, *, character_level: int, sanctuary: bool = False,
) -> HoardGuardianDamage:
    """Bound trap.c's dynamic guardian, not an ordinary level-64 reset.

    Bounds assume every strike lands against a standing victim with no
    damage-increasing victim effects. They are not an expected damage rate or
    a survival guarantee. Admission still needs posture/resistance/mitigation,
    dig lag, return timing, live protection, and a finite escape policy.
    Multiple rounds can occur before the player's next command, including
    the trap's immediate multi_hit.
    """
    if type(character_level) is not int or not 1 <= character_level <= 100:
        raise ValueError("guardian damage requires an observed mortal level")
    if type(sanctuary) is not bool:
        raise ValueError("guardian protection must be explicit")
    mobile = world.mobiles.get(83)  # merc.h:MOB_VNUM_SPIRIT
    if (
        mobile is None or mobile.template_name is not None
        or mobile.act_flags != 98 or mobile.affected_flags != 1572904
        or mobile.body_form_flags != 336 or mobile.programs
        or world.mobile_specials.get(83)
        or not mobile.damage_modifier_known or mobile.damage_modifier is None
    ):
        raise ValueError("guardian source profile is absent, changed, or unaudited")
    level = min(character_level, 99)
    # trap.c sets damroll after create_mobile. NPC STR is 13 (zero damage
    # bonus), and this dynamically created mobile has no reset-loaded gear.
    damage_bonus = level // 2
    expected = mobile_expected_round_damage(
        level, wielding=False, dual_wielding=False,
        damage_modifier=mobile.damage_modifier,
        source_damage_bonus=damage_bonus,
        sanctuary=sanctuary,
    )
    peak = _mobile_peak_round_damage(
        level, wielding=False, dual_wielding=False,
        damage_modifier=mobile.damage_modifier,
        source_damage_bonus=damage_bonus,
    )
    critical = _mobile_critical_hit_damage(
        level, wielding=False, damage_modifier=mobile.damage_modifier,
        source_damage_bonus=damage_bonus,
    )
    ordinary_hit = _apply_mobile_damage_modifier(
        _mobile_normal_hit_damage(level, wielding=False) + damage_bonus,
        mobile.damage_modifier,
    )
    if sanctuary:
        peak = mobile_sanctuary_peak_round_damage(
            level, wielding=False, dual_wielding=False,
            damage_modifier=mobile.damage_modifier,
            source_damage_bonus=damage_bonus,
        )
        critical = mobile_sanctuary_critical_hit_damage(
            level, wielding=False, damage_modifier=mobile.damage_modifier,
            source_damage_bonus=damage_bonus,
        )
        ordinary_hit //= 2
    return HoardGuardianDamage(
        level, 10 * level + 100, expected, peak, ordinary_hit, critical,
        5 + int(level >= 20), sanctuary,
    )


# const.c:str_app carry/wield columns, separate from equipment damage bonuses.
_STRENGTH_CARRY = (
    0, 3, 3, 10, 25, 55, 80, 90, 100, 100, 115, 115, 140, 140, 170, 200,
    250, 300, 350, 400, 500, 600, 700, 800, 900, 950, 1000, 1050, 1100,
    1125, 1150, 1200,
)
_STRENGTH_WIELD = (
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 22, 25,
    30, 35, 40, 45, 50, 55, 60, 70, 80, 85, 90, 99, 99,
)


@dataclass(frozen=True)
class HoardHexInventory:
    minimum_strength: int
    minimum_dexterity: int
    carry_weight_limit: int
    carry_number_limit: int
    wield_weight_limit: int

    def weapon_drop_risk(self, *, primary_weight: int | None, dual_weight: int | None) -> bool:
        """Mirror affect_modify's primary-else-dual check, not a walking gate."""
        if any(weight is not None and (type(weight) is not int or weight < 0 or weight == 50000)
               for weight in (primary_weight, dual_weight)):
            raise ValueError("weapon retention needs complete observed instance weights")
        checked = primary_weight if primary_weight is not None else dual_weight
        return checked is not None and checked > self.wield_weight_limit


def hoard_hex_inventory(*, character_level: int, strength: int, dexterity: int) -> HoardHexInventory:
    """Bound stat loss from a new hex without inventing a movement restriction.

    Subtracting from clamped live stats is a lower bound if hidden surplus
    bonuses exist. Carry limits restrict pickup, not walking or keeping items
    already carried. A trap stop must not discard belongings to meet them.
    """
    if (
        any(type(n) is not int for n in (character_level, strength, dexterity))
        or not 1 <= character_level <= 100 or not 3 <= strength <= 31
        or not 3 <= dexterity <= 31
    ):
        raise ValueError("hex planning requires revealed current stats and level")
    strength = max(3, strength - character_level // 4)
    dexterity = max(3, dexterity - character_level // 4)
    return HoardHexInventory(strength, dexterity, _STRENGTH_CARRY[strength],
                             22 + dexterity, _STRENGTH_WIELD[strength])


@dataclass(frozen=True)
class DigObservation:
    sequence: int
    quest_identity: tuple[int, int, int]  # giver, room, object
    room_vnum: int
    tool_vnum: int
    hp: int
    movement: int
    in_combat: bool
    occupants: int
    standing: bool
    quest_active: bool
    current_budget: DigBudget | None
    trap_recovery_verified: bool = False


def _valid_revised_budget(previous: DigBudget, current: object) -> bool:
    if not isinstance(current, DigBudget):
        return False
    values = (
        current.tool_vnum, current.sector_type, current.minimum_damage,
        current.maximum_digs, current.maximum_move_per_dig,
        current.maximum_wait_pulses,
    )
    return bool(
        all(type(value) is int for value in values)
        and current.tool_vnum == previous.tool_vnum
        and current.tool_name == previous.tool_name
        and current.sector_type == previous.sector_type
        and current.minimum_damage > 0 and current.maximum_digs > 0
        and current.maximum_move_per_dig > 0
        and current.maximum_wait_pulses > 0
    )


@dataclass(frozen=True)
class DigStep:
    status: str
    reason: str
    command: str | None = None
    trap_kind: str | None = None


class HoardDigSession:
    """One dig per response, with bounded recovery handoffs for trap charges."""

    def __init__(
        self, budget: DigBudget, *, quest_identity: tuple[int, int, int],
        minimum_hp: int, return_movement: int,
    ) -> None:
        if (
            len(quest_identity) != 3 or any(type(n) is not int or n <= 0 for n in quest_identity)
            or type(minimum_hp) is not int or minimum_hp <= 0
            or type(return_movement) is not int or return_movement < 0
            or budget.maximum_digs < 1 or budget.maximum_move_per_dig < 1
            or budget.maximum_wait_pulses < 1
        ):
            raise ValueError("excavation needs exact identity and recovery reserves")
        self.budget = budget
        self.earth_dig_limit = budget.maximum_digs
        self.quest_identity = quest_identity
        self.minimum_hp = minimum_hp
        self.return_movement = return_movement
        self.commands = 0
        self.movement_recovery_pauses = 0
        self.trap_pops = 0
        self.trap_sequences: list[int] = []
        self.trap_effects: list[tuple[int, str]] = []
        self.trap_recovery_sequences: list[int] = []
        self._last_observed_sequence = -1
        self._unearthed_sequence = -1
        self.stage = "ready"
        self.reason = ""
        self._buffer = ""
        self._sent_sequence = -1
        self._trap_sequence = -1
        self._resume_after_sequence: int | None = None
        self._trap_seen = False
        self._ready_at = 0.0
        self._deadline = 0.0
        self.quest_object_selector: str | None = None
        self.quest_object_baseline_count = -1
        self.quest_object_pickup_sequence = -1
        self.quest_object_acquired_sequence = -1

    def observe(self, text: str) -> None:
        """Consume cleaned server text, retaining fragments until a full reply."""
        if self.stage != "waiting":
            return
        if len(self._buffer) + len(text) > 8192:
            self._stop("digging response exceeded its bounded buffer")
            return
        self._buffer += text
        lines = {line.strip() for line in _DD4_PROMPT.sub("\n", self._buffer).splitlines()}
        if _TRAP in lines:
            self._trap_seen = True
        elif any(line in lines for line in _REFUSALS):
            self._stop("the server refused digging")
        elif _FUTILE in lines:
            self._stop("the server reported futile digging")

    def _stop(self, reason: str) -> DigStep:
        self.stage, self.reason = "stopped", reason
        return DigStep(self.stage, reason)

    def poll(self, observed: DigObservation, *, now: float) -> DigStep:
        if self.stage in {
            "stopped", "unearthed", "pickup_pending", "object_acquired",
        }:
            return DigStep(self.stage, self.reason)
        if (
            not math.isfinite(now)
            or any(type(value) is not int for value in (
                observed.sequence, observed.room_vnum, observed.tool_vnum,
                observed.hp, observed.movement, observed.occupants,
            ))
            or observed.sequence < 0 or observed.occupants < 0
            or any(type(value) is not bool for value in (
                observed.in_combat, observed.standing, observed.quest_active,
            ))
        ):
            return self._stop("excavation requires complete fresh observations")
        if (
            not observed.quest_active or observed.quest_identity != self.quest_identity
            or observed.room_vnum != self.quest_identity[1]
            or observed.tool_vnum != self.budget.tool_vnum
        ):
            return self._stop("excavation identity, endpoint, or current budget changed")
        self._last_observed_sequence = max(
            self._last_observed_sequence,
            observed.sequence,
        )
        if self.stage == "trap_recovery_required":
            return DigStep(self.stage, self.reason)
        if self._resume_after_sequence is not None:
            if observed.sequence <= self._resume_after_sequence:
                return DigStep("waiting", "wait for state after trap recovery")
            self._resume_after_sequence = None
        if self.stage == "waiting":
            if now >= self._deadline:
                return self._stop("dig reply or fresh state timed out")
            if now < self._ready_at or observed.sequence <= self._sent_sequence:
                return DigStep("waiting", "wait for digging lag and fresh state")
            prompts = tuple(_DD4_PROMPT.finditer(self._buffer))
            if not prompts:
                return DigStep("waiting", "wait for the digging reply's prompt")
            completed = _DD4_PROMPT.sub("\n", self._buffer[:prompts[-1].start()])
            lines = [line.strip() for line in completed.splitlines()]
            if self._trap_seen:
                if (
                    not _valid_revised_budget(self.budget, observed.current_budget)
                    or self.trap_pops >= _MAX_HOARD_TRAP_CHARGES
                ):
                    return self._stop("trap count or digging tool changed unexpectedly")
                self.trap_pops += 1
                self._trap_seen = False
                self._trap_sequence = observed.sequence
                self.trap_sequences.append(observed.sequence)
                trap_kind = identify_hoard_trap_effect(self._buffer)
                if trap_kind is None:
                    self.trap_effects.append((observed.sequence, "unknown"))
                    self._buffer = ""
                    self.stage = "stopped"
                    self.reason = (
                        "a hoard trap fired but its effect was not uniquely identified"
                    )
                    return DigStep(self.stage, self.reason, trap_kind="unknown")
                self.trap_effects.append((observed.sequence, trap_kind))
                self.stage = "trap_recovery_required"
                self.reason = (
                    f"hoard {trap_kind} trap charge {self.trap_pops} fired; verify "
                    "recovery, the endpoint, and the physical return before resuming"
                )
                self._buffer = ""
                return DigStep(self.stage, self.reason, trap_kind=trap_kind)
            success = _SUCCESS in lines
            progress = any(
                re.fullmatch(r"You dig into the earth with .+\.\.\.", line)
                and normalize_item_name(line[len("You dig into the earth with "):-3])
                == normalize_item_name(self.budget.tool_name)
                for line in lines
            )
            if not (success or progress):
                return DigStep("waiting", "wait for the complete digging reply and prompt")
            if success:
                self.stage, self.reason = "unearthed", "contents released; exact quest-object pickup is still required"
                self._unearthed_sequence = observed.sequence
                return DigStep(self.stage, self.reason)
            self.stage = "ready"
        if observed.current_budget != self.budget:
            return self._stop("excavation identity, endpoint, or current budget changed")
        if observed.in_combat or observed.occupants != 0:
            return self._stop("combat or an occupied endpoint requires recovery")
        if not observed.standing or observed.hp < self.minimum_hp:
            return self._stop("excavation health or posture is no longer ready")
        command_limit = self.earth_dig_limit + (
            _MAX_HOARD_TRAP_CHARGES if self.trap_pops else 0
        )
        if self.commands >= command_limit:
            return self._stop("source digging budget exhausted without unearthing")
        required_for_next_dig = (
            self.budget.maximum_move_per_dig + self.return_movement
        )
        if observed.movement < required_for_next_dig:
            if observed.movement < self.return_movement:
                return self._stop(
                    "movement no longer covers the audited physical return"
                )
            if self.stage != "recovery_required":
                self.movement_recovery_pauses += 1
            self.stage = "recovery_required"
            self.reason = (
                "recover movement at the verified endpoint before the next dig; "
                "the return reserve is still intact"
            )
            return DigStep(self.stage, self.reason)
        self.stage = "ready"
        self.reason = ""
        self.commands += 1
        self.stage, self._buffer = "waiting", ""
        self._sent_sequence = observed.sequence
        self._ready_at = now + self.budget.maximum_wait_seconds + 0.5
        self._deadline = self._ready_at + 5.0
        return DigStep("waiting", "one bounded excavation command", "dig")

    def prepare_quest_object_pickup(
        self,
        *,
        sequence: int,
        quest_object_vnum: int,
        source_object_description: str,
        source_description_vnums: Collection[int],
        current_room_vnum: int | str,
        room_listing: Mapping[str, object],
        inventory_items: object,
    ) -> DigStep:
        """Persist one exact ground selector and inventory baseline before get."""
        if self.stage != "unearthed":
            return self._stop("quest-object pickup was prepared before unearthing")
        if (
            type(sequence) is not int or sequence < 0
            or type(quest_object_vnum) is not int
            or quest_object_vnum != self.quest_identity[2]
            or not isinstance(source_object_description, str)
            or not normalize_item_name(source_object_description)
            or isinstance(source_description_vnums, (str, bytes))
            or not isinstance(source_description_vnums, Collection)
            or any(type(vnum) is not int or vnum <= 0 for vnum in source_description_vnums)
            or set(source_description_vnums) != {quest_object_vnum}
            or not (
                type(current_room_vnum) is int
                and current_room_vnum == self.quest_identity[1]
                or isinstance(current_room_vnum, str)
                and current_room_vnum == str(self.quest_identity[1])
            )
            or not isinstance(room_listing, Mapping)
            or not (
                type(room_listing.get("room_vnum")) is int
                and room_listing.get("room_vnum") == self.quest_identity[1]
                or isinstance(room_listing.get("room_vnum"), str)
                and room_listing.get("room_vnum") == str(self.quest_identity[1])
            )
            or room_listing.get("render_complete") is not True
            or type(room_listing.get("state_revision")) is not int
            or room_listing["state_revision"] <= self._unearthed_sequence
            or room_listing["state_revision"] > sequence
            or not isinstance(room_listing.get("targeted_lines"), list)
        ):
            return self._stop("quest-object ground listing or source evidence is incomplete")
        if (
            self._unearthed_sequence < 0
            or sequence <= self._unearthed_sequence
            or sequence <= self._last_observed_sequence
        ):
            return DigStep(self.stage, "wait for a newer room and inventory observation")
        baseline = _inventory_count(inventory_items, source_object_description)
        if baseline is None:
            return self._stop("complete Char.Items baseline is malformed or incomplete")
        self._last_observed_sequence = sequence
        exact_room_objects: list[str] = []
        for item in room_listing["targeted_lines"]:
            if not isinstance(item, Mapping):
                return self._stop("room listing contains malformed target evidence")
            description = item.get("description")
            target_id = item.get("target_id")
            if not isinstance(description, str):
                return self._stop("room listing contains a target without a description")
            if normalize_item_name(description) != normalize_item_name(
                source_object_description
            ):
                continue
            if (
                not isinstance(target_id, str)
                or not target_id.isdecimal()
                or int(target_id) <= 0
            ):
                return self._stop("quest-object room selector is malformed")
            exact_room_objects.append(f"#{target_id}")
        if not exact_room_objects:
            return DigStep(self.stage, "the exact quest object is not visible in the fresh room listing")
        if len(exact_room_objects) != 1:
            return self._stop("multiple matching room objects make the pickup selector ambiguous")

        self.quest_object_selector = exact_room_objects[0]
        self.quest_object_baseline_count = baseline
        self.quest_object_pickup_sequence = sequence
        self._last_observed_sequence = sequence
        self.stage = "pickup_pending"
        self.reason = "exact room selector and inventory baseline saved; issue one pickup"
        return DigStep(self.stage, self.reason, f"get {self.quest_object_selector}")

    def confirm_quest_object_acquired(
        self,
        *,
        sequence: int,
        quest_object_vnum: int,
        source_object_description: str,
        source_description_vnums: Collection[int],
        inventory_items: object,
    ) -> DigStep:
        """Confirm one exact pickup from a newer complete Char.Items snapshot."""
        if self.stage != "pickup_pending":
            return self._stop("quest-object pickup was confirmed without a pending intent")
        if (
            type(sequence) is not int or sequence < 0
            or type(quest_object_vnum) is not int
            or quest_object_vnum != self.quest_identity[2]
            or not isinstance(source_object_description, str)
            or not normalize_item_name(source_object_description)
            or isinstance(source_description_vnums, (str, bytes))
            or not isinstance(source_description_vnums, Collection)
            or any(type(vnum) is not int or vnum <= 0 for vnum in source_description_vnums)
            or set(source_description_vnums) != {quest_object_vnum}
            or self.quest_object_selector is None
            or self.quest_object_baseline_count < 0
            or self.quest_object_pickup_sequence <= self._unearthed_sequence
        ):
            return self._stop("quest-object pickup evidence is incomplete or ambiguous")
        if sequence <= self.quest_object_pickup_sequence or sequence <= self._last_observed_sequence:
            return DigStep(self.stage, "wait for the post-pickup Char.Items snapshot")

        carried_count = _inventory_count(inventory_items, source_object_description)
        if carried_count is None:
            return self._stop("post-pickup Char.Items snapshot is malformed or incomplete")
        if carried_count == self.quest_object_baseline_count:
            self._last_observed_sequence = sequence
            self.reason = "pickup is not confirmed; keep the intent pending without retrying"
            return DigStep(self.stage, self.reason)
        if carried_count != self.quest_object_baseline_count + 1:
            return self._stop("inventory change does not prove exactly one selected quest-object pickup")

        self.quest_object_acquired_sequence = sequence
        self._last_observed_sequence = sequence
        self.stage = "object_acquired"
        self.reason = "exact source quest-object instance confirmed in carried inventory"
        return DigStep(self.stage, self.reason)

    def confirm_trap_recovery(self, observed: DigObservation) -> DigStep:
        """Require an external live safety check before spending another charge."""
        if self.stage != "trap_recovery_required":
            return self._stop("trap recovery was confirmed outside its handoff")
        if (
            any(type(value) is not int for value in (
                observed.sequence, observed.room_vnum, observed.tool_vnum,
                observed.hp, observed.movement, observed.occupants,
            ))
            or not observed.quest_active
            or observed.quest_identity != self.quest_identity
            or observed.room_vnum != self.quest_identity[1]
            or observed.tool_vnum != self.budget.tool_vnum
            or any(type(value) is not bool for value in (
                observed.in_combat, observed.standing, observed.quest_active,
                observed.trap_recovery_verified,
            ))
            or observed.sequence < 0 or observed.hp < 0
            or observed.movement < 0 or observed.occupants < 0
        ):
            return self._stop("trap recovery state or quest identity changed")
        if not _valid_revised_budget(self.budget, observed.current_budget):
            return self._stop("trap recovery lost the source-identified digging tool or terrain")
        if not self.trap_effects or self.trap_effects[-1][1] == "unknown":
            return self._stop("trap recovery cannot proceed without a uniquely identified effect")
        if not observed.trap_recovery_verified or observed.sequence <= self._trap_sequence:
            return DigStep(
                self.stage,
                "fresh explicit recovery evidence for the same quest, room, and tool is required",
            )
        if (
            observed.in_combat or observed.occupants != 0 or not observed.standing
            or observed.hp < self.minimum_hp
            or observed.movement < self.return_movement
        ):
            return DigStep(
                self.stage,
                "recovery evidence does not preserve health, movement, and an empty safe endpoint",
            )
        self.budget = observed.current_budget
        self._last_observed_sequence = observed.sequence
        self._resume_after_sequence = observed.sequence
        self.trap_recovery_sequences.append(observed.sequence)
        self.stage = "ready"
        self.reason = "trap recovery verified; wait for one newer observation before digging"
        return DigStep(self.stage, self.reason)

    def audit(self) -> dict[str, object]:
        return {
            "stage": self.stage, "reason": self.reason, "commands": self.commands,
            "movement_recovery_pauses": self.movement_recovery_pauses,
            "trap_pops": self.trap_pops,
            "trap_sequences": tuple(self.trap_sequences),
            "trap_effects": tuple(self.trap_effects),
            "trap_recovery_sequences": tuple(self.trap_recovery_sequences),
            "maximum_dig_commands": self.earth_dig_limit + _MAX_HOARD_TRAP_CHARGES,
            "maximum_trap_charges": _MAX_HOARD_TRAP_CHARGES,
            "quest_identity": self.quest_identity, "budget": asdict(self.budget),
            "minimum_hp": self.minimum_hp, "return_movement": self.return_movement,
            "quest_object_acquired": self.stage == "object_acquired",
            "quest_object_pickup_pending": self.stage == "pickup_pending",
            "quest_object_selector": self.quest_object_selector,
            "quest_object_baseline_count": self.quest_object_baseline_count,
            "quest_object_pickup_sequence": self.quest_object_pickup_sequence,
            "quest_object_acquired_sequence": self.quest_object_acquired_sequence,
        }

    def checkpoint(self) -> dict[str, object]:
        """Return the bounded state needed to resume at a safe command boundary."""
        return {
            "schema_version": 3,
            "quest_identity": list(self.quest_identity),
            "budget": asdict(self.budget),
            "minimum_hp": self.minimum_hp,
            "return_movement": self.return_movement,
            "commands": self.commands,
            "movement_recovery_pauses": self.movement_recovery_pauses,
            "trap_pops": self.trap_pops,
            "trap_sequences": list(self.trap_sequences),
            "trap_effects": [list(effect) for effect in self.trap_effects],
            "trap_recovery_sequences": list(self.trap_recovery_sequences),
            "stage": self.stage,
            "reason": self.reason,
            "last_observed_sequence": self._last_observed_sequence,
            "unearthed_sequence": self._unearthed_sequence,
            "quest_object_selector": self.quest_object_selector,
            "quest_object_baseline_count": self.quest_object_baseline_count,
            "quest_object_pickup_sequence": self.quest_object_pickup_sequence,
            "quest_object_acquired_sequence": self.quest_object_acquired_sequence,
        }

    @classmethod
    def from_checkpoint(cls, checkpoint: object) -> HoardDigSession:
        """Restore a session without replaying an unacknowledged dig command."""
        checkpoint_fields_v1 = {
            "schema_version", "quest_identity", "budget", "minimum_hp",
            "return_movement", "commands", "movement_recovery_pauses",
            "trap_pops", "trap_sequences", "trap_effects",
            "trap_recovery_sequences", "stage", "reason",
            "last_observed_sequence",
        }
        if (
            not isinstance(checkpoint, dict)
            or type(checkpoint.get("schema_version")) is not int
            or checkpoint.get("schema_version") not in {1, 2, 3}
        ):
            raise ValueError("unsupported hoard excavation checkpoint")
        schema_version = checkpoint["schema_version"]
        checkpoint_fields_v2 = checkpoint_fields_v1 | {
            "unearthed_sequence", "quest_object_selector",
            "quest_object_acquired_sequence",
        }
        checkpoint_fields_v3 = checkpoint_fields_v2 | {
            "quest_object_baseline_count", "quest_object_pickup_sequence",
        }
        if set(checkpoint) != (
            checkpoint_fields_v1 if schema_version == 1
            else checkpoint_fields_v2 if schema_version == 2
            else checkpoint_fields_v3
        ):
            raise ValueError("unsupported hoard excavation checkpoint")
        identity = checkpoint.get("quest_identity")
        raw_budget = checkpoint.get("budget")
        if (
            not isinstance(identity, list) or len(identity) != 3
            or any(type(value) is not int or value <= 0 for value in identity)
            or not isinstance(raw_budget, dict)
            or set(raw_budget) != {
                "tool_vnum", "tool_name", "sector_type", "minimum_damage",
                "maximum_digs", "maximum_move_per_dig", "maximum_wait_pulses",
            }
        ):
            raise ValueError("checkpoint is missing exact quest or tool identity")
        try:
            budget = DigBudget(**raw_budget)
        except (TypeError, ValueError) as exc:
            raise ValueError("checkpoint has an invalid digging budget") from exc
        budget_integers = (
            budget.tool_vnum, budget.sector_type, budget.minimum_damage,
            budget.maximum_digs, budget.maximum_move_per_dig,
            budget.maximum_wait_pulses,
        )
        if (
            not isinstance(budget.tool_name, str) or not budget.tool_name.strip()
            or any(type(value) is not int for value in budget_integers)
            or budget.tool_vnum <= 0
            or not 0 <= budget.sector_type < len(_TERRAIN)
            or _TERRAIN[budget.sector_type] is None
            or min(budget.minimum_damage, budget.maximum_digs,
                   budget.maximum_move_per_dig, budget.maximum_wait_pulses) <= 0
        ):
            raise ValueError("checkpoint has an invalid source digging budget")
        minimum_hp = checkpoint.get("minimum_hp")
        return_movement = checkpoint.get("return_movement")
        if (
            type(minimum_hp) is not int or minimum_hp <= 0
            or type(return_movement) is not int or return_movement < 0
        ):
            raise ValueError("checkpoint has invalid recovery reserves")
        restored = cls(
            budget,
            quest_identity=tuple(identity),
            minimum_hp=minimum_hp,
            return_movement=return_movement,
        )
        counters = (
            "commands", "movement_recovery_pauses", "trap_pops",
            "last_observed_sequence",
        )
        values = {key: checkpoint.get(key) for key in counters}
        if any(type(value) is not int for value in values.values()):
            raise ValueError("checkpoint has invalid excavation counters")
        if (
            values["commands"] < 0
            or values["commands"] > budget.maximum_dig_commands
            or values["movement_recovery_pauses"] < 0
            or values["trap_pops"] < 0
            or values["trap_pops"] > _MAX_HOARD_TRAP_CHARGES
            or values["trap_pops"] > values["commands"]
            or values["last_observed_sequence"] < -1
        ):
            raise ValueError("checkpoint counters exceed source excavation limits")
        sequences = checkpoint.get("trap_sequences")
        effects = checkpoint.get("trap_effects")
        recoveries = checkpoint.get("trap_recovery_sequences")
        if (
            not isinstance(sequences, list)
            or any(type(value) is not int or value < 0 for value in sequences)
            or not isinstance(effects, list)
            or any(
                not isinstance(value, list) or len(value) != 2
                or type(value[0]) is not int or value[0] < 0
                or not isinstance(value[1], str)
                for value in effects
            )
            or not isinstance(recoveries, list)
            or any(type(value) is not int or value < 0 for value in recoveries)
            or len(sequences) != values["trap_pops"]
            or len(effects) != values["trap_pops"]
            or len(recoveries) > values["trap_pops"]
            or tuple(value[0] for value in effects) != tuple(sequences)
            or any(left >= right for left, right in zip(sequences, sequences[1:]))
            or any(
                value[1] not in {*_TRAP_EFFECT_MARKERS, "unknown"}
                for value in effects
            )
            or any(
                recovered <= trap
                for trap, recovered in zip(sequences, recoveries)
            )
            or any(
                recovered >= next_trap
                for recovered, next_trap in zip(recoveries, sequences[1:])
            )
            or any(left >= right for left, right in zip(recoveries, recoveries[1:]))
            or (
                sequences
                and values["last_observed_sequence"] < sequences[-1]
            )
            or (
                recoveries
                and values["last_observed_sequence"] < recoveries[-1]
            )
            or (
                values["last_observed_sequence"] >= 0
                and any(
                    sequence > values["last_observed_sequence"]
                    for sequence in (*sequences, *recoveries)
                )
            )
        ):
            raise ValueError("checkpoint has inconsistent trap evidence")
        stored_stage = checkpoint.get("stage")
        reason = checkpoint.get("reason")
        if not isinstance(stored_stage, str) or stored_stage not in {
            "ready", "waiting", "recovery_required",
            "trap_recovery_required", "stopped", "unearthed",
            "pickup_pending", "object_acquired",
        } or not isinstance(reason, str):
            raise ValueError("checkpoint has an unknown session state")
        legacy_acquired = (
            schema_version < 3 and stored_stage == "object_acquired"
        )
        stage = "stopped" if legacy_acquired else stored_stage
        if legacy_acquired:
            reason = (
                "legacy carried-object evidence lacks a Char.Items quantity delta; "
                "repeat the quest-object proof before turn-in"
            )
        unearthed_sequence = (
            checkpoint.get("unearthed_sequence")
            if schema_version == 2
            or schema_version == 3
            else values["last_observed_sequence"] if stage == "unearthed" else -1
        )
        quest_object_selector = (
            checkpoint.get("quest_object_selector") if schema_version == 2 else None
        )
        if schema_version == 3:
            quest_object_selector = checkpoint.get("quest_object_selector")
        quest_object_acquired_sequence = (
            checkpoint.get("quest_object_acquired_sequence")
            if schema_version in {2, 3} else -1
        )
        pickup_baseline_count = (
            checkpoint.get("quest_object_baseline_count")
            if schema_version == 3 else -1
        )
        pickup_sequence = (
            checkpoint.get("quest_object_pickup_sequence")
            if schema_version == 3 else -1
        )
        if legacy_acquired:
            if (
                quest_object_selector is not None
                and (
                    not isinstance(quest_object_selector, str)
                    or re.fullmatch(r"#[0-9]+", quest_object_selector) is None
                    or int(quest_object_selector[1:]) <= 0
                )
            ) or (
                type(quest_object_acquired_sequence) is not int
                or quest_object_acquired_sequence < -1
            ):
                raise ValueError("checkpoint has inconsistent legacy quest-object evidence")
            quest_object_selector = None
            quest_object_acquired_sequence = -1
        if (
            type(unearthed_sequence) is not int or unearthed_sequence < -1
            or type(quest_object_acquired_sequence) is not int
            or quest_object_acquired_sequence < -1
            or type(pickup_baseline_count) is not int
            or pickup_baseline_count < -1
            or type(pickup_sequence) is not int
            or pickup_sequence < -1
            or (
                quest_object_selector is not None
                and (
                    not isinstance(quest_object_selector, str)
                    or re.fullmatch(r"#[0-9]+", quest_object_selector) is None
                    or int(quest_object_selector[1:]) <= 0
                )
            )
            or (
                stage == "object_acquired"
                and (
                    quest_object_selector is None
                    or pickup_baseline_count < 0
                    or pickup_sequence <= unearthed_sequence
                    or quest_object_acquired_sequence <= pickup_sequence
                    or quest_object_acquired_sequence != values["last_observed_sequence"]
                )
            )
            or (
                stage == "pickup_pending"
                and (
                    quest_object_selector is None
                    or pickup_baseline_count < 0
                    or pickup_sequence <= unearthed_sequence
                    or pickup_sequence > values["last_observed_sequence"]
                    or quest_object_acquired_sequence != -1
                )
            )
            or (
                stage not in {"object_acquired", "pickup_pending", "stopped"}
                and (
                    quest_object_selector is not None
                    or quest_object_acquired_sequence != -1
                    or pickup_baseline_count != -1
                    or pickup_sequence != -1
                )
            )
            or (
                stage == "stopped"
                and (
                    quest_object_selector is None
                    and (
                        quest_object_acquired_sequence != -1
                        or pickup_baseline_count != -1
                        or pickup_sequence != -1
                    )
                    or quest_object_selector is not None
                    and (
                        pickup_baseline_count < 0
                        or pickup_sequence <= unearthed_sequence
                        or pickup_sequence > values["last_observed_sequence"]
                        or quest_object_acquired_sequence != -1
                    )
                )
            )
            or (
                stage in {"unearthed", "pickup_pending", "object_acquired"}
                and (
                    unearthed_sequence < 0
                    or unearthed_sequence > values["last_observed_sequence"]
                )
            )
        ):
            raise ValueError("checkpoint has inconsistent quest-object evidence")
        if stage == "trap_recovery_required" and (
            not effects or effects[-1][1] == "unknown"
            or len(recoveries) != values["trap_pops"] - 1
        ):
            raise ValueError("checkpoint has no recoverable pending trap")
        if stage in {
            "ready", "recovery_required", "unearthed", "pickup_pending",
            "object_acquired",
        } and (
            len(recoveries) != values["trap_pops"]
        ):
            raise ValueError("checkpoint is missing completed trap recovery evidence")
        restored.commands = values["commands"]
        restored.movement_recovery_pauses = values["movement_recovery_pauses"]
        restored.trap_pops = values["trap_pops"]
        restored.trap_sequences = list(sequences)
        restored.trap_effects = [(value[0], value[1]) for value in effects]
        restored.trap_recovery_sequences = list(recoveries)
        restored._last_observed_sequence = values["last_observed_sequence"]
        restored._unearthed_sequence = unearthed_sequence
        restored.quest_object_selector = quest_object_selector
        restored.quest_object_baseline_count = pickup_baseline_count
        restored.quest_object_pickup_sequence = pickup_sequence
        restored.quest_object_acquired_sequence = quest_object_acquired_sequence
        restored._trap_sequence = sequences[-1] if sequences else -1
        restored.stage = stage
        restored.reason = reason
        if stage == "waiting":
            restored.stage = "stopped"
            restored.reason = (
                "interrupted while awaiting a dig response; reconcile recorded "
                "events before any further excavation"
            )
        elif stage in {"ready", "recovery_required"}:
            if values["last_observed_sequence"] < 0:
                restored.stage = "stopped"
                restored.reason = (
                    "checkpoint has no live observation boundary; repeat the "
                    "source and live preflight before excavation"
                )
            else:
                restored._resume_after_sequence = values["last_observed_sequence"]
        return restored
