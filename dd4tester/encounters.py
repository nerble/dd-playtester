"""Source-backed budgets for finishing already-active ordinary encounters."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import permutations
from math import ceil
from typing import Any, Mapping, Sequence

from .hunt_candidates import (
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
class SourcePairBudget(EncounterBudget):
    level_ceiling: int = 0
    target_hp_ceiling: int = 0


@dataclass
class SourcePairEncounter:
    """A room-observed pair; never pretend duplicated GMCP identifies the add."""

    budget: SourcePairBudget
    selectors: tuple[str, str]
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
