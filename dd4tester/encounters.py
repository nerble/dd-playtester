"""Source-backed budgets for finishing already-active ordinary encounters."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from itertools import permutations
from math import ceil
from typing import Any, Mapping, Sequence

from .combat_timing import COMBAT_WAIT_SECONDS

from .hunt_candidates import (
    ACT_SENTINEL,
    EX_WALL,
    ITEM_WEAPON,
    WEAR_DUAL,
    WEAR_WIELD,
    SourceCombatOutput,
    WorldSource,
    _mobile_critical_hit_damage,
    _mobile_base_hp_range,
    _mobile_level_range,
    _mobile_peak_round_damage,
    mobile_expected_round_damage,
)


@dataclass(frozen=True)
class EncounterBudget:
    allowed: bool
    reason: str
    mobile_vnums: tuple[int, ...] = ()
    actions: int = 0
    expected_incoming: int = 0
    peak_round: int = 0
    health_reserve: int = 0
    mana_cost: int = 0


@dataclass(frozen=True)
class ObservedTargetIdentity:
    """Connection-local binding of a unique room selector to live GMCP."""

    selector: str
    mobile_vnum: int
    room_vnum: str
    stop_index: int
    level: int | None
    boot_id: str | None
    observed_at: float


@dataclass(frozen=True)
class DisplacedTargetIdentity(ObservedTargetIdentity):
    """Source-description inference, not a live GMCP VNUM observation."""

    reset_room_vnum: str
    description: str


def displaced_sentinel_reset_room(
    world: WorldSource, mobile_vnum: int, *, room_vnum: int,
    direction: str, destination: int, description: str,
) -> int | None:
    """Identify a single-reset sentinel beside its planned destination."""
    mobile = world.mobiles.get(mobile_vnum)
    room = world.rooms.get(room_vnum)
    reset_room = world.rooms.get(destination)
    def normalize(value: str) -> str:
        return " ".join(value.casefold().split())

    if (
        mobile is None or room is None or reset_room is None
        or not mobile.act_flags & ACT_SENTINEL or mobile.wanders
        or mobile.aggressive or mobile.programs
        or not description or normalize(mobile.room_description) != description
        or room_vnum == destination
        or room.area_file != reset_room.area_file
        or mobile.area_file != room.area_file
        or room.random_exits or reset_room.random_exits
        or room.no_mob or reset_room.no_mob
        or room.sector_type not in range(6) or reset_room.sector_type not in range(6)
    ):
        return None
    identities = [
        candidate.vnum for candidate in world.mobiles.values()
        if normalize(candidate.room_description) == description
    ]
    resets = [reset for reset in world.mob_resets if reset.mobile_vnum == mobile_vnum]
    if identities != [mobile_vnum] or len(resets) != 1:
        return None
    if resets[0].room_vnum != destination or resets[0].maximum_count != 1:
        return None
    outward = room.exits.get(direction)
    opposite = {
        "north": "south", "south": "north", "east": "west", "west": "east",
        "up": "down", "down": "up",
    }.get(direction)
    inward = reset_room.exits.get(opposite)
    if (
        outward is None or inward is None
        or outward.destination != destination or inward.destination != room_vnum
        or outward.locked or inward.locked
        or (outward.flags | inward.flags) & EX_WALL
    ):
        return None
    return destination


@dataclass(frozen=True)
class SourcePairBudget(EncounterBudget):
    level_ceiling: int = 0
    target_hp_ceiling: int = 0


@dataclass
class SourcePairEncounter:
    """One or two considered targets, sharing the measured encounter controller."""

    budget: SourcePairBudget
    selectors: tuple[str, ...]
    room_vnum: str
    stop_index: int
    level: int
    boot_id: str | None
    prepared_at: float
    started_at: float | None = None
    defeated: set[str] = field(default_factory=set)
    damage_commands: int = 0

    @property
    def remaining(self) -> tuple[str, ...]:
        return tuple(value for value in self.selectors if value not in self.defeated)


def source_solo_budget(
    world: WorldSource, mobile_vnum: int, *, character_level: int,
    hp: int, max_hp: int, mana: int, max_mana: int,
    output: SourceCombatOutput | None,
) -> SourcePairBudget:
    """Price a useful easy-kill source load without pretending it is live GMCP.

    The caller must bind a fresh exact-instance easy-kill consider. Use the
    full source HP ceiling and the existing short-encounter cost calculation;
    no companion, armor, or opening damage receives credit.
    """
    mobile = world.mobiles.get(mobile_vnum)
    if mobile is None or mobile.aggressive:
        return SourcePairBudget(False, "missing or aggressive solo source target")
    resets = [reset for reset in world.mob_resets if reset.mobile_vnum == mobile_vnum]
    if not resets or max(reset.maximum_count for reset in resets) > 4:
        return SourcePairBudget(False, "missing or excessive source reset population")
    if any(slot in {WEAR_WIELD, WEAR_DUAL} for reset in resets for slot, _ in reset.equipment):
        return SourcePairBudget(False, "armed solo target retains its protection gate")
    lower, upper = _mobile_level_range(mobile.level)
    lower, upper = max(lower, character_level - 4), min(upper, character_level - 2)
    if character_level <= 0 or lower <= 0 or lower > upper:
        return SourcePairBudget(False, "no useful easy-kill source intersection")
    if not 0 < hp <= max_hp or hp < ceil(max_hp * .95):
        return SourcePairBudget(False, "solo admission requires near-full health")
    hp_ceiling = _mobile_base_hp_range((lower, upper), rank=mobile.rank)[1]
    budget = active_encounter_budget(
        world, [{"isnpc": mobile_vnum, "level": upper, "hp": hp_ceiling, "maxhp": hp_ceiling}],
        character_level=character_level, hp=hp, max_hp=max_hp,
        mana=mana, max_mana=max_mana, output=output,
    )
    return SourcePairBudget(
        budget.allowed, "source-bounded solo: " + budget.reason,
        budget.mobile_vnums, budget.actions, budget.expected_incoming,
        budget.peak_round, budget.health_reserve, budget.mana_cost,
        upper, hp_ceiling,
    )


def source_pair_budget(
    world: WorldSource, mobile_vnum: int, *, character_level: int,
    hp: int, max_hp: int, mana: int, max_mana: int,
    output: SourceCombatOutput | None,
) -> SourcePairBudget:
    """Admit an observed easy-kill pair to a measured probe, not a predicted win.

    Both instances must separately pass exact live easy-kill considers at the
    caller. Source ceilings reserve damage actions for two full-health loads.
    Initial admission covers two expected rounds plus the withdrawal reserve;
    subsequent continuation requires the measured combined incoming damage.
    No armor, avoided attacks, sanctuary or opening damage receives credit.
    """
    mobile = world.mobiles.get(mobile_vnum)
    if mobile is None or output is None or output.conservative_damage <= 0:
        return SourcePairBudget(False, "missing source mobile or executable damage")
    if (
        mobile.aggressive or mobile.programs or mobile.non_corporeal
        or mobile.costs_fame or world.mobile_specials.get(mobile_vnum)
        or mobile_vnum in world.shopkeepers
    ):
        return SourcePairBudget(False, "pair requires a separate source hazard policy")
    resets = [reset for reset in world.mob_resets if reset.mobile_vnum == mobile_vnum]
    if not resets or max(reset.maximum_count for reset in resets) > 4:
        return SourcePairBudget(False, "missing or excessive source reset population")
    if any(slot in {WEAR_WIELD, WEAR_DUAL} for reset in resets for slot, _ in reset.equipment):
        return SourcePairBudget(False, "armed pair retains its protection gate")
    lower, upper = _mobile_level_range(mobile.level)
    upper = min(upper, character_level - 2)
    if character_level <= 0 or upper < max(lower, character_level - 4):
        return SourcePairBudget(False, "source range has no useful easy-kill intersection")
    if not 0 < hp <= max_hp or hp < ceil(max_hp * .95):
        return SourcePairBudget(False, "pair admission requires fresh near-full health")
    hp_ceiling = _mobile_base_hp_range((lower, upper), rank=mobile.rank)[1]
    actions = 2 * ceil(hp_ceiling / output.conservative_damage)
    peak = 2 * _mobile_peak_round_damage(upper, wielding=False, dual_wielding=False)
    reserve = max(ceil(max_hp * .4), 2 * _mobile_critical_hit_damage(upper, wielding=False))
    probe_damage = 4 * mobile_expected_round_damage(upper, wielding=False, dual_wielding=False)
    mana_cost = (actions + 2) * output.resource_cost if output.resource == "mana" else 0
    values = dict(
        mobile_vnums=(mobile_vnum, mobile_vnum), actions=actions,
        expected_incoming=probe_damage, peak_round=peak, health_reserve=reserve,
        mana_cost=mana_cost, level_ceiling=upper, target_hp_ceiling=hp_ceiling,
    )
    if actions > min(10, output.maximum_actions):
        return SourcePairBudget(False, "pair exceeds the bounded damage-action budget", **values)
    if peak >= hp or probe_damage >= hp - reserve:
        return SourcePairBudget(False, "pair probe exceeds the current health reserve", **values)
    if output.resource == "mana":
        if max_mana <= 0 or mana - mana_cost < ceil(max_mana * .15):
            return SourcePairBudget(False, "pair exceeds the current mana reserve", **values)
    elif output.resource != "actions" or output.resource_cost:
        return SourcePairBudget(False, "unsupported pair damage resource", **values)
    return SourcePairBudget(True, "source-estimated pair fits a measured probe", **values)


def solo_continuation_budget(
    world: WorldSource, enemies: Sequence[Mapping[str, Any]], *,
    character_level: int, hp: int, max_hp: int, mana: int, max_mana: int,
    output: SourceCombatOutput | None, elapsed: float, effective_damage: int,
    received_damage: int, remaining_seconds: float, remaining_commands: int,
) -> EncounterBudget:
    """Reprice an already-bound solo fight against its remaining resources.

    A fixed fraction of initial target HP is not a remaining-fight estimate.
    Retain source ceilings and measured loss/time projections instead. This
    function never admits a new target or extends the controller's deadline.
    """
    if len(enemies) != 1:
        return EncounterBudget(False, "solo continuation requires one live opponent")
    budget = active_encounter_budget(
        world, enemies, character_level=character_level, hp=hp, max_hp=max_hp,
        mana=mana, max_mana=max_mana, output=output,
    )
    if not budget.allowed:
        return budget
    reason = None
    if remaining_commands < budget.actions + 2:
        reason = "solo finish exceeds the remaining command reserve"
    elif remaining_seconds <= COMBAT_WAIT_SECONDS or elapsed < 0:
        reason = "solo finish has no remaining time reserve"
    elif elapsed >= 12 and effective_damage <= 0:
        reason = "solo opponent made no net damage progress within twelve seconds"
    elif elapsed >= 2 * COMBAT_WAIT_SECONDS and effective_damage > 0:
        remaining_hp = int(enemies[0]["hp"])
        projected_loss = ceil(remaining_hp * max(0, received_damage) / effective_damage)
        # The observed wall-clock rate already includes input and round waits.
        projected_seconds = remaining_hp * elapsed / effective_damage
        if projected_loss >= hp - budget.health_reserve:
            reason = "solo measured exchange exceeds the remaining health reserve"
        elif projected_seconds >= remaining_seconds:
            reason = "solo measured finish exceeds the original encounter deadline"
    return replace(budget, allowed=False, reason=reason) if reason else budget


def active_encounter_budget(
    world: WorldSource,
    enemies: Sequence[Mapping[str, Any]],
    *,
    character_level: int,
    hp: int,
    max_hp: int,
    mana: int,
    max_mana: int,
    output: SourceCombatOutput | None,
) -> EncounterBudget:
    """Estimate a short finish without granting permission to start combat.

    Assume every active enemy contributes damage, including below-band mobs.
    Budget the worst defeat order and two utility/acknowledgement rounds; no
    armor, sanctuary, opening attack, or unobserved skill receives credit.
    Live HP, resource, plateau, and identity checks remain runtime authorities.
    """
    if not 1 <= len(enemies) <= 3:
        return EncounterBudget(False, "active encounter must contain one to three enemies")
    if output is None or output.conservative_damage <= 0:
        return EncounterBudget(False, "no executable source-backed damage action")
    if not 0 < hp <= max_hp or character_level <= 0:
        return EncounterBudget(False, "missing live health or level")
    members: list[tuple[int, int, int]] = []
    peak = critical = 0
    for enemy in enemies:
        try:
            vnum = int(enemy["isnpc"])
            level = int(enemy["level"])
            enemy_hp = int(enemy["hp"])
            enemy_max_hp = int(enemy["maxhp"])
        except (KeyError, ValueError, TypeError):
            return EncounterBudget(False, "incomplete live enemy identity or HP")
        mobile = world.mobiles.get(vnum)
        if mobile is None or any(member[0] == vnum for member in members):
            return EncounterBudget(False, "unknown or ambiguous source mobile")
        lower, upper = _mobile_level_range(mobile.level)
        if not lower <= level <= min(upper, character_level + 1):
            return EncounterBudget(False, "live enemy level exceeds the source or character band")
        if not 0 < enemy_hp <= enemy_max_hp:
            return EncounterBudget(False, "invalid live enemy HP")
        if (
            mobile.programs or mobile.non_corporeal or mobile.costs_fame
            or world.mobile_specials.get(vnum) or vnum in world.shopkeepers
        ):
            return EncounterBudget(False, "enemy requires a separate source-special policy")
        if any(
            slot in {WEAR_WIELD, WEAR_DUAL}
            and (
                (item := world.objects.get(object_vnum)) is None
                or item.item_type == ITEM_WEAPON
            )
            for reset in world.mob_resets if reset.mobile_vnum == vnum
            for slot, object_vnum in reset.equipment
        ):
            return EncounterBudget(False, "armed enemy retains its separate protection gate")
        if not any(reset.mobile_vnum == vnum for reset in world.mob_resets):
            return EncounterBudget(False, "missing source reset equipment evidence")
        actions = ceil(enemy_hp / output.conservative_damage)
        incoming = mobile_expected_round_damage(level, wielding=False, dual_wielding=False)
        members.append((vnum, actions, incoming))
        peak += _mobile_peak_round_damage(level, wielding=False, dual_wielding=False)
        critical += _mobile_critical_hit_damage(level, wielding=False)

    actions = sum(member[1] for member in members)
    expected = max(
        sum(
            member[1] * sum(other[2] for other in order[index:])
            for index, member in enumerate(order)
        )
        for order in permutations(members)
    ) + 2 * sum(member[2] for member in members)
    reserve = max(ceil(max_hp * 0.4), critical)
    mana_cost = (
        actions * output.resource_cost + 2 * max(20, output.resource_cost)
        if output.resource == "mana" else 0
    )
    values = dict(
        mobile_vnums=tuple(member[0] for member in members), actions=actions,
        expected_incoming=expected, peak_round=peak,
        health_reserve=reserve, mana_cost=mana_cost,
    )
    if actions > min(6, output.maximum_actions):
        return EncounterBudget(False, "encounter exceeds the six-action finishing window", **values)
    if peak >= hp or expected >= hp - reserve:
        return EncounterBudget(False, "combined damage exceeds the current health reserve", **values)
    if output.resource == "mana":
        if max_mana <= 0 or mana - mana_cost < ceil(max_mana * 0.15):
            return EncounterBudget(False, "combined actions exceed the current mana reserve", **values)
    elif output.resource != "actions" or output.resource_cost:
        return EncounterBudget(False, "unsupported action resource", **values)
    return EncounterBudget(True, "live ordinary encounter fits the finishing budget", **values)
