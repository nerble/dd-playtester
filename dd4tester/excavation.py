"""Source-derived hoard budgets and response-driven digging, not route admission.

This controller is not wired into live quest dispatch. A caller must first
prove tool identity, an empty endpoint, a curse-safe physical return, and a
guardian escape plan. Unearthing never proves possession or quest completion.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import re

from .equipment import ITEM_DIGGER, normalize_item_name
from .hunt_candidates import (
    ObjectSource, WorldSource, _apply_mobile_damage_modifier,
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
_SUCCESS = "With a final effortful thrust, you unearth something!"
_FUTILE = "You dig into the earth... but get the feeling you're wasting your time."
_REFUSALS = (
    "You're in no position to do any digging right now.",
    "You can't dig, you've been SWALLOWED!", "Not in your current state.",
    "While you're fighting?  No.", "Dismount first.",
    "Your arms are too badly damaged to dig.",
    "You can't dig in this sort of terrain.", "You have no way of doing that.",
    "You're too inexperienced to use that digging implement effectively.",
    "You're too exhausted to dig.",
)


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
        return self.maximum_digs * self.maximum_move_per_dig

    @property
    def maximum_wait_seconds(self) -> float:
        # WAIT_STATE is measured in server pulses, four per second.
        return self.maximum_wait_pulses / 4.0


def tool_dig_budget(
    tool: ObjectSource, *, sector_type: int, race: str, level: int,
    observed_tool_level: int, strength: int, constitution: int, dexterity: int,
    swiftness: int, enhanced_swiftness_percent: int,
    depth: int = 200, haste: bool = False,
    quicken: bool = False, bonus_attack: bool = False,
    cannot_see_self: bool = False, slow: bool = False,
) -> DigBudget:
    """Bound one ITEM_DIGGER excavation using act_obj.c and db.c.

    swiftness is Char.Stats.swift (GET_SWIFT). Digging omits its learned
    enhanced-swiftness bonus, but retains its dex_app[].toswift contribution.
    Tool load-level admission requires its observed instance level.
    """
    numbers = (sector_type, level, observed_tool_level, strength, constitution,
               dexterity, swiftness, enhanced_swiftness_percent, depth)
    if any(type(value) is not int or value == 50000 for value in numbers):
        raise ValueError("digging requires complete revealed integer observations")
    if not 1 <= level <= 100 or not 0 <= observed_tool_level <= level or not 1 <= depth <= 200:
        raise ValueError("invalid character, tool level, or excavation depth")
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


@dataclass(frozen=True)
class DigStep:
    status: str
    reason: str
    command: str | None = None


class HoardDigSession:
    """One dig per acknowledged response, with no trap retry or auto-pickup."""

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
        self.quest_identity = quest_identity
        self.minimum_hp = minimum_hp
        self.return_movement = return_movement
        self.commands = 0
        self.stage = "ready"
        self.reason = ""
        self._buffer = ""
        self._sent_sequence = -1
        self._ready_at = 0.0
        self._deadline = 0.0

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
            self._stop("a hoard trap fired; recover without another dig")
        elif any(line in lines for line in _REFUSALS):
            self._stop("the server refused digging")
        elif _FUTILE in lines:
            self._stop("the server reported futile digging")

    def _stop(self, reason: str) -> DigStep:
        self.stage, self.reason = "stopped", reason
        return DigStep(self.stage, reason)

    def poll(self, observed: DigObservation, *, now: float) -> DigStep:
        if self.stage in {"stopped", "unearthed"}:
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
            or observed.current_budget != self.budget
        ):
            return self._stop("excavation identity, endpoint, or current budget changed")
        if observed.in_combat or observed.occupants != 0:
            return self._stop("combat or an occupied endpoint requires recovery")
        if not observed.standing or observed.hp < self.minimum_hp:
            return self._stop("excavation health or posture is no longer ready")
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
                return DigStep(self.stage, self.reason)
            self.stage = "ready"
        if self.commands >= self.budget.maximum_digs:
            return self._stop("source digging budget exhausted without unearthing")
        remaining = (self.budget.maximum_digs - self.commands) * self.budget.maximum_move_per_dig
        if observed.movement < remaining + self.return_movement:
            return self._stop("movement no longer covers excavation and physical return")
        self.commands += 1
        self.stage, self._buffer = "waiting", ""
        self._sent_sequence = observed.sequence
        self._ready_at = now + self.budget.maximum_wait_seconds + 0.5
        self._deadline = self._ready_at + 5.0
        return DigStep("waiting", "one bounded excavation command", "dig")

    def audit(self) -> dict[str, object]:
        return {
            "stage": self.stage, "reason": self.reason, "commands": self.commands,
            "quest_identity": self.quest_identity, "budget": asdict(self.budget),
            "minimum_hp": self.minimum_hp, "return_movement": self.return_movement,
            "quest_object_acquired": False,
        }
