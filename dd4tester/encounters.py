"""Source-backed budgets for finishing already-active ordinary encounters."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from itertools import permutations
from math import ceil
from typing import Any, Collection, Mapping, Sequence

from .combat_timing import COMBAT_WAIT_SECONDS

from .hunt_candidates import (
    ACT_SENTINEL,
    EX_WALL,
    ITEM_STAFF,
    ITEM_WEAPON,
    WEAR_DUAL,
    WEAR_HOLD,
    WEAR_WIELD,
    SourceCombatOutput,
    WorldSource,
    _mobile_critical_hit_damage,
    _mobile_base_hp_range,
    _mobile_level_range,
    _mobile_peak_round_damage,
    mobile_expected_round_damage,
    mobile_sanctuary_peak_round_damage,
)
from .populations import source_sequential_duplicate_reset_limit


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
    # This is a source-verified duplicate reset fought one instance at a
    # time.  Its admission never uses a live or estimated target HP value.
    source_only: bool = False


@dataclass
class SourcePairEncounter:
    """A bounded set of considered targets sharing one encounter controller."""

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
    finisher_grace_used: bool = False

    @property
    def remaining(self) -> tuple[str, ...]:
        return tuple(value for value in self.selectors if value not in self.defeated)


@dataclass
class SourceMaterialEncounter:
    """A primary target with one source-verified room bystander."""

    budget: EncounterBudget
    target: str
    target_selector: str
    target_vnum: int
    bystander: str
    bystander_selector: str | None
    bystander_vnum: int
    room_vnum: str
    stop_index: int
    level: int
    boot_id: str | None
    prepared_at: float
    started_at: float | None = None


def source_solo_budget(
    world: WorldSource, mobile_vnum: int, *, character_level: int,
    hp: int, max_hp: int, mana: int, max_mana: int,
    output: SourceCombatOutput | None,
) -> SourcePairBudget:
    """Price a useful easy-kill source load without pretending it is live GMCP.

    The caller must bind a fresh exact-instance easy-kill consider. Use source
    level and incoming-damage bounds only; target HP remains evidence rather
    than a permission or action-count gate.
    """
    mobile = world.mobiles.get(mobile_vnum)
    if (
        mobile is None
        or mobile.aggressive
        or mobile.programs
        or mobile.non_corporeal
        or mobile.costs_fame
        or world.mobile_specials.get(mobile_vnum)
        or mobile_vnum in world.shopkeepers
    ):
        return SourcePairBudget(False, "missing or aggressive solo source target")
    if output is None or output.conservative_damage <= 0:
        return SourcePairBudget(False, "missing source solo damage action")
    if not mobile.hp_modifier_known:
        return SourcePairBudget(False, "source mobile HP modifier is unavailable")
    if not mobile.damage_modifier_known:
        return SourcePairBudget(False, "source mobile damage modifier is unavailable")
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
    expected = mobile_expected_round_damage(
        upper,
        wielding=False,
        dual_wielding=False,
        damage_modifier=mobile.damage_modifier,
    )
    peak = _mobile_peak_round_damage(
        upper,
        wielding=False,
        dual_wielding=False,
        damage_modifier=mobile.damage_modifier,
    )
    reserve = ceil(max_hp * 0.20)
    # Keep a finite opening window and two command acknowledgements. This is a
    # player-resource boundary, not an estimate of how much target HP remains.
    actions = max(2, min(5, max(1, output.maximum_actions)))
    mana_cost = (
        (actions + 2) * output.resource_cost
        if output.resource == "mana"
        else 0
    )
    values = dict(
        mobile_vnums=(mobile_vnum,),
        actions=actions,
        expected_incoming=expected,
        peak_round=peak,
        health_reserve=reserve,
        mana_cost=mana_cost,
        level_ceiling=upper,
        target_hp_ceiling=0,
    )
    if peak >= hp - reserve:
        return SourcePairBudget(
            False,
            "source solo incoming bound reaches the player's health reserve",
            **values,
        )
    if output.resource == "mana" and (
        max_mana <= 0 or mana - mana_cost < ceil(max_mana * .15)
    ):
        return SourcePairBudget(
            False,
            "source solo actions exceed the 15% mana reserve",
            **values,
        )
    if output.resource not in {"actions", "mana"} or (
        output.resource == "actions" and output.resource_cost
    ):
        return SourcePairBudget(False, "unsupported solo damage resource", **values)
    return SourcePairBudget(
        True,
        "source-bounded solo: target HP is not used",
        **values,
    )


def source_pair_budget(
    world: WorldSource, mobile_vnum: int, *, character_level: int,
    hp: int, max_hp: int, mana: int, max_mana: int,
    output: SourceCombatOutput | None,
) -> SourcePairBudget:
    """Admit an observed easy-kill pair to a measured probe, not a predicted win.

    Both instances must separately pass exact live easy-kill considers at the
    caller. Source level and incoming-damage bounds reserve a finite measured
    window. Subsequent continuation uses the player's own health, time, and
    command reserves rather than target HP.
    No armor, avoided attacks, sanctuary or opening damage receives credit.
    """
    mobile = world.mobiles.get(mobile_vnum)
    if mobile is None or output is None or output.conservative_damage <= 0:
        return SourcePairBudget(False, "missing source mobile or executable damage")
    if not mobile.hp_modifier_known:
        return SourcePairBudget(False, "source mobile HP modifier is unavailable")
    if not mobile.damage_modifier_known:
        return SourcePairBudget(False, "source mobile damage modifier is unavailable")
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
    if character_level <= 0 or hp <= 0 or max_hp <= 0:
        return SourcePairBudget(False, "pair admission requires fresh near-full health")
    # Equipment changes can briefly deliver a current HP/mana value before the
    # matching GMCP maximum.  The current value is a hard lower bound for the
    # cap; rejecting that transient ordering would turn healthy live state into
    # a false "missing resources" result.
    max_hp = max(max_hp, hp)
    if max_mana > 0:
        max_mana = max(max_mana, mana)
    if hp < ceil(max_hp * .95):
        return SourcePairBudget(False, "pair admission requires fresh near-full health")
    actions = max(4, min(8, 2 * max(1, output.maximum_actions)))
    peak = 2 * _mobile_peak_round_damage(
        upper,
        wielding=False,
        dual_wielding=False,
        damage_modifier=mobile.damage_modifier,
    )
    reserve = max(
        ceil(max_hp * .4),
        2 * _mobile_critical_hit_damage(
            upper,
            wielding=False,
            damage_modifier=mobile.damage_modifier,
        ),
    )
    probe_damage = 4 * mobile_expected_round_damage(
        upper,
        wielding=False,
        dual_wielding=False,
        damage_modifier=mobile.damage_modifier,
    )
    mana_cost = (actions + 2) * output.resource_cost if output.resource == "mana" else 0
    values = dict(
        mobile_vnums=(mobile_vnum, mobile_vnum), actions=actions,
        expected_incoming=probe_damage, peak_round=peak, health_reserve=reserve,
        mana_cost=mana_cost, level_ceiling=upper, target_hp_ceiling=0,
    )
    if peak >= hp or probe_damage >= hp - reserve:
        return SourcePairBudget(False, "pair probe exceeds the current health reserve", **values)
    if output.resource == "mana":
        if max_mana <= 0 or mana - mana_cost < ceil(max_mana * .15):
            return SourcePairBudget(False, "pair exceeds the current mana reserve", **values)
    elif output.resource != "actions" or output.resource_cost:
        return SourcePairBudget(False, "unsupported pair damage resource", **values)
    return SourcePairBudget(
        True,
        "source-level pair fits a measured probe; target HP is not used",
        **values,
    )


def source_duplicate_pair_budget(
    world: WorldSource,
    mobile_vnum: int,
    *,
    room_vnum: int,
    character_level: int,
    hp: int,
    max_hp: int,
    mana: int,
    max_mana: int,
    output: SourceCombatOutput | None,
    sanctuary_mitigation: bool = False,
) -> SourcePairBudget:
    """Admit two exact copies of one plain armed reset for sequential kills.

    The reset, mobile flags, live ``consider`` results, and the player's own
    resources are the admission evidence.  Target HP is deliberately absent:
    the runtime controller owns the 20% withdrawal floor and the finite
    encounter deadline.
    """
    mobile = world.mobiles.get(mobile_vnum)
    if mobile is None or output is None or output.conservative_damage <= 0:
        return SourcePairBudget(False, "missing source mobile or executable damage")
    if (
        not mobile.sentinel or mobile.wanders or mobile.aggressive
        or mobile.fear_aura or mobile.programs or mobile.attack_programs
        or mobile.non_corporeal or mobile.costs_fame
        or world.mobile_specials.get(mobile_vnum)
        or mobile_vnum in world.shopkeepers
    ):
        return SourcePairBudget(False, "duplicate pair requires a plain sentinel reset")
    if not mobile.damage_modifier_known:
        return SourcePairBudget(False, "source mobile damage modifier is unavailable")
    resets = [
        reset for reset in world.mob_resets
        if reset.mobile_vnum == mobile_vnum
    ]
    if len(resets) != 1 or resets[0].room_vnum != room_vnum:
        return SourcePairBudget(False, "duplicate pair reset is not unique to this room")
    reset = resets[0]
    if reset.maximum_count != 2:
        return SourcePairBudget(False, "duplicate pair reset does not load exactly two copies")
    weapons = [
        object_vnum
        for slot, object_vnum in reset.equipment
        if slot in {WEAR_WIELD, WEAR_DUAL}
    ]
    if len(reset.equipment) != 1 or len(weapons) != 1:
        return SourcePairBudget(False, "duplicate pair reset is not a single-weapon loadout")
    weapon = world.objects.get(weapons[0])
    if weapon is None or weapon.item_type != ITEM_WEAPON:
        return SourcePairBudget(False, "duplicate pair weapon is not source-verified")
    if character_level <= 0 or hp <= 0 or max_hp <= 0:
        return SourcePairBudget(False, "duplicate pair is missing live player resources")
    max_hp = max(max_hp, hp)
    if max_mana > 0:
        max_mana = max(max_mana, mana)
    if hp < ceil(max_hp * .95):
        return SourcePairBudget(False, "duplicate pair admission requires near-full health")
    lower, upper = _mobile_level_range(mobile.level)
    lower = max(lower, character_level - 4)
    upper = min(upper, character_level + 5)
    if lower <= 0 or lower > upper:
        return SourcePairBudget(False, "duplicate pair has no source level intersection")
    expected_one = mobile_expected_round_damage(
        upper,
        wielding=True,
        dual_wielding=False,
        damage_modifier=mobile.damage_modifier,
    )
    peak_one = (
        mobile_sanctuary_peak_round_damage(
            upper,
            wielding=True,
            dual_wielding=False,
            damage_modifier=mobile.damage_modifier,
        )
        if sanctuary_mitigation
        else _mobile_peak_round_damage(
            upper,
            wielding=True,
            dual_wielding=False,
            damage_modifier=mobile.damage_modifier,
        )
    )
    reserve = ceil(max_hp * .20)
    values = dict(
        mobile_vnums=(mobile_vnum, mobile_vnum),
        # This is a time/command bound, not a target-HP estimate.
        actions=max(4, min(24, 2 * max(1, output.maximum_actions))),
        expected_incoming=(expected_one // 2 if sanctuary_mitigation else expected_one) * 2,
        peak_round=peak_one,
        health_reserve=reserve,
        mana_cost=(2 * output.resource_cost if output.resource == "mana" else 0),
        level_ceiling=upper,
        target_hp_ceiling=0,
        source_only=True,
    )
    if peak_one >= hp - reserve:
        return SourcePairBudget(False, "duplicate pair source damage reaches the 20% reserve", **values)
    if output.resource == "mana" and (
        max_mana <= 0 or mana - values["mana_cost"] < ceil(max_mana * .15)
    ):
        return SourcePairBudget(False, "duplicate pair would consume the 15% mana reserve", **values)
    if output.resource not in {"actions", "mana"} or (
        output.resource == "actions" and output.resource_cost
    ):
        return SourcePairBudget(False, "unsupported duplicate pair damage resource", **values)
    return SourcePairBudget(
        True,
        "source duplicate reset and live considers fit a sequential pair",
        **values,
    )


def source_sequential_duplicate_budget(
    world: WorldSource,
    mobile_vnum: int,
    *,
    room_vnum: int,
    instance_count: int,
    character_level: int,
    hp: int,
    max_hp: int,
    mana: int,
    max_mana: int,
    output: SourceCombatOutput | None,
    maximum_level_offset: int = 1,
) -> SourcePairBudget:
    """Admit a small plain reset for sequential, one-at-a-time kills.

    The caller supplies fresh exact selectors and live ``consider`` results.
    This function only proves the source reset and prices one bounded opening
    window per observed copy; it never uses target HP as an admission gate.
    """
    if not 2 <= instance_count <= 4:
        return SourcePairBudget(
            False,
            "sequential duplicate encounter needs two to four live copies",
        )
    mobile = world.mobiles.get(mobile_vnum)
    if mobile is None or output is None or output.conservative_damage <= 0:
        return SourcePairBudget(False, "missing source mobile or executable damage")
    if (
        not mobile.sentinel
        or mobile.wanders
        or mobile.aggressive
        or mobile.fear_aura
        or mobile.programs
        or mobile.attack_programs
        or mobile.non_corporeal
        or mobile.costs_fame
        or world.mobile_specials.get(mobile_vnum)
        or mobile_vnum in world.shopkeepers
    ):
        return SourcePairBudget(
            False,
            "sequential duplicate encounter requires a plain sentinel reset",
        )
    if not mobile.damage_modifier_known:
        return SourcePairBudget(False, "source mobile damage modifier is unavailable")
    reset_limit = source_sequential_duplicate_reset_limit(
        world,
        mobile_vnum=mobile_vnum,
        room_vnum=room_vnum,
    )
    if reset_limit is None or instance_count > reset_limit:
        return SourcePairBudget(
            False,
            "sequential duplicate reset is not a bounded plain population",
        )
    if character_level <= 0 or hp <= 0 or max_hp <= 0:
        return SourcePairBudget(False, "sequential duplicate is missing live player resources")
    max_hp = max(max_hp, hp)
    if max_mana > 0:
        max_mana = max(max_mana, mana)
    if hp < ceil(max_hp * .95):
        return SourcePairBudget(
            False,
            "sequential duplicate admission requires near-full health",
        )
    if not 0 <= maximum_level_offset <= 5:
        return SourcePairBudget(False, "sequential duplicate level ceiling is outside consider range")
    lower, upper = _mobile_level_range(mobile.level)
    lower = max(lower, character_level - 4)
    upper = min(upper, character_level + maximum_level_offset)
    if lower <= 0 or lower > upper:
        return SourcePairBudget(
            False,
            "sequential duplicate has no source level intersection",
        )
    expected_one = mobile_expected_round_damage(
        upper,
        wielding=False,
        dual_wielding=False,
        damage_modifier=mobile.damage_modifier,
    )
    peak_one = _mobile_peak_round_damage(
        upper,
        wielding=False,
        dual_wielding=False,
        damage_modifier=mobile.damage_modifier,
    )
    critical_one = _mobile_critical_hit_damage(
        upper,
        wielding=False,
        damage_modifier=mobile.damage_modifier,
    )
    reserve = ceil(max_hp * .20)
    # One measured opening window per copy keeps the source admission finite;
    # the live controller still owns the actual 20% withdrawal decision.
    actions_per_copy = max(2, min(8, max(1, output.maximum_actions // 2)))
    actions = instance_count * actions_per_copy
    expected_incoming = instance_count * expected_one
    mana_cost = instance_count * output.resource_cost if output.resource == "mana" else 0
    values = dict(
        mobile_vnums=tuple(mobile_vnum for _ in range(instance_count)),
        actions=actions,
        expected_incoming=expected_incoming,
        peak_round=peak_one,
        health_reserve=reserve,
        mana_cost=mana_cost,
        level_ceiling=upper,
        target_hp_ceiling=0,
        source_only=True,
    )
    if max(peak_one, critical_one) >= hp - reserve:
        return SourcePairBudget(
            False,
            "sequential duplicate source damage reaches the 20% reserve",
            **values,
        )
    if expected_incoming >= hp - reserve:
        return SourcePairBudget(
            False,
            "sequential duplicate opening window reaches the 20% reserve",
            **values,
        )
    if output.resource == "mana" and (
        max_mana <= 0 or mana - mana_cost < ceil(max_mana * .15)
    ):
        return SourcePairBudget(
            False,
            "sequential duplicate would consume the 15% mana reserve",
            **values,
        )
    if output.resource not in {"actions", "mana"} or (
        output.resource == "actions" and output.resource_cost
    ):
        return SourcePairBudget(
            False,
            "unsupported sequential duplicate damage resource",
            **values,
        )
    return SourcePairBudget(
        True,
        "source plain duplicate reset and live considers fit sequential rotation",
        **values,
    )


def solo_continuation_budget(
    world: WorldSource, enemies: Sequence[Mapping[str, Any]], *,
    character_level: int, hp: int, max_hp: int, mana: int, max_mana: int,
    output: SourceCombatOutput | None, elapsed: float, effective_damage: int,
    received_damage: int, remaining_seconds: float, remaining_commands: int,
) -> EncounterBudget:
    """Reprice an already-bound solo fight against its remaining resources.

    Target HP is not a remaining-fight estimate. Retain source level checks,
    the player's own health/resource floors, and the fixed time/command
    boundary. This function never admits a new target or extends the deadline.
    """
    if len(enemies) != 1:
        return EncounterBudget(False, "solo continuation requires one live opponent")
    budget = active_encounter_budget(
        world, enemies, character_level=character_level, hp=hp, max_hp=max_hp,
        mana=mana, max_mana=max_mana, output=output,
        target_hp_evidence_only=True,
    )
    if not budget.allowed:
        return budget
    reason = None
    if remaining_commands < budget.actions + 2:
        reason = "solo finish exceeds the remaining command reserve"
    elif remaining_seconds <= COMBAT_WAIT_SECONDS or elapsed < 0:
        reason = "solo finish has no remaining time reserve"
    # Target HP and measured target progress are retained by the caller for
    # evidence/reporting, but never decide whether this already-open fight
    # continues. The player's own health, resources, time, and command caps
    # remain authoritative.
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
    # Target HP is observation data by default. The compatibility flag is
    # retained for checkpoint callers, but current callers should leave it on.
    target_hp_evidence_only: bool = True,
    maximum_level_offsets_by_vnum: Mapping[int, int] | None = None,
    allowed_adept_special_vnums: Collection[int] = (),
    allowed_caerlin_special_vnums: Collection[int] = (),
    allowed_hephaestus_special_vnums: Collection[int] = (),
    allowed_red_dragon_fire_special_vnums: Collection[int] = (),
) -> EncounterBudget:
    """Estimate a short finish without granting permission to start combat.

    Assume every active enemy contributes damage, including below-band mobs.
    Validate source identities, relative levels, source hazards, resources,
    and the player's own health floor. Target HP and predicted finish length
    are observation/report data; no armor, Sanctuary, opening attack, or
    unobserved skill receives credit.
    """
    if not 1 <= len(enemies) <= 3:
        return EncounterBudget(False, "active encounter must contain one to three enemies")
    if output is None or output.conservative_damage <= 0:
        return EncounterBudget(False, "no executable source-backed damage action")
    if not 0 < hp <= max_hp or character_level <= 0:
        return EncounterBudget(False, "missing live health or level")
    if target_hp_evidence_only:
        return _active_level_encounter_budget(
            world,
            enemies,
            character_level=character_level,
            hp=hp,
            max_hp=max_hp,
            mana=mana,
            max_mana=max_mana,
            output=output,
            maximum_level_offsets_by_vnum=maximum_level_offsets_by_vnum or {},
            allowed_adept_special_vnums=allowed_adept_special_vnums,
            allowed_caerlin_special_vnums=allowed_caerlin_special_vnums,
            allowed_hephaestus_special_vnums=allowed_hephaestus_special_vnums,
            allowed_red_dragon_fire_special_vnums=(
                allowed_red_dragon_fire_special_vnums
            ),
        )
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
        if not mobile.hp_modifier_known:
            return EncounterBudget(False, "source mobile HP modifier is unavailable")
        if not mobile.damage_modifier_known:
            return EncounterBudget(False, "source mobile damage modifier is unavailable")
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
        incoming = mobile_expected_round_damage(
            level,
            wielding=False,
            dual_wielding=False,
            damage_modifier=mobile.damage_modifier,
        )
        members.append((vnum, actions, incoming))
        peak += _mobile_peak_round_damage(
            level,
            wielding=False,
            dual_wielding=False,
            damage_modifier=mobile.damage_modifier,
        )
        critical += _mobile_critical_hit_damage(
            level,
            wielding=False,
            damage_modifier=mobile.damage_modifier,
        )

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


def _active_level_encounter_budget(
    world: WorldSource,
    enemies: Sequence[Mapping[str, Any]],
    *,
    character_level: int,
    hp: int,
    max_hp: int,
    mana: int,
    max_mana: int,
    output: SourceCombatOutput | None,
    maximum_level_offsets_by_vnum: Mapping[int, int],
    allowed_adept_special_vnums: Collection[int],
    allowed_caerlin_special_vnums: Collection[int],
    allowed_hephaestus_special_vnums: Collection[int],
    allowed_red_dragon_fire_special_vnums: Collection[int],
) -> EncounterBudget:
    """Validate live source identities and levels without using enemy HP."""
    if not 1 <= len(enemies) <= 3:
        return EncounterBudget(False, "level-bound encounter must contain one to three enemies")
    if output is None or output.conservative_damage <= 0:
        return EncounterBudget(False, "no executable source-backed damage action")
    if hp <= ceil(max_hp * 0.20):
        return EncounterBudget(False, "the character reached the 20% withdrawal floor")

    vnums: list[int] = []
    expected = peak = critical = 0
    for enemy in enemies:
        try:
            vnum = int(enemy["isnpc"])
            level = int(enemy["level"])
        except (KeyError, ValueError, TypeError):
            return EncounterBudget(False, "incomplete live source identity or level")
        mobile = world.mobiles.get(vnum)
        if mobile is None or vnum in vnums:
            return EncounterBudget(False, "unknown or ambiguous source mobile")
        lower, upper = _mobile_level_range(mobile.level)
        maximum_offset = maximum_level_offsets_by_vnum.get(vnum, 1)
        if (
            not lower <= level <= upper
            or level > character_level + maximum_offset
        ):
            return EncounterBudget(False, "live mobile level left its audited band")
        red_dragon_allowed = bool(
            vnum in allowed_red_dragon_fire_special_vnums
            and _red_dragon_fire_reset_shape_allowed(world, vnum)
        )
        if (
            mobile.programs or mobile.non_corporeal or mobile.costs_fame
            or not _encounter_special_is_allowed(
                world,
                vnum,
                allowed_adept_special_vnums,
                allowed_caerlin_special_vnums,
                allowed_hephaestus_special_vnums,
                allowed_red_dragon_fire_special_vnums,
            )
            or vnum in world.shopkeepers
        ):
            return EncounterBudget(False, "enemy requires a separate source-hazard policy")
        if not mobile.damage_modifier_known:
            return EncounterBudget(False, "source mobile damage modifier is unavailable")
        resets = [reset for reset in world.mob_resets if reset.mobile_vnum == vnum]
        if not resets or (
            not red_dragon_allowed
            and any(
            slot in {WEAR_WIELD, WEAR_DUAL}
            and (
                (item := world.objects.get(object_vnum)) is None
                or item.item_type == ITEM_WEAPON
            )
            for reset in resets
            for slot, object_vnum in reset.equipment
            )
        ):
            return EncounterBudget(False, "armed or unreset enemy retains its source gate")
        wielding = bool(
            red_dragon_allowed
            and any(
                slot == WEAR_WIELD
                and (item := world.objects.get(object_vnum)) is not None
                and item.item_type == ITEM_WEAPON
                for reset in resets
                for slot, object_vnum in reset.equipment
            )
        )
        dual_wielding = bool(
            red_dragon_allowed
            and any(
                slot == WEAR_DUAL
                and (item := world.objects.get(object_vnum)) is not None
                and item.item_type == ITEM_WEAPON
                for reset in resets
                for slot, object_vnum in reset.equipment
            )
        )
        vnums.append(vnum)
        expected += mobile_expected_round_damage(
            level,
            wielding=wielding,
            dual_wielding=dual_wielding,
            damage_modifier=mobile.damage_modifier,
        )
        peak += _mobile_peak_round_damage(
            level,
            wielding=wielding,
            dual_wielding=dual_wielding,
            damage_modifier=mobile.damage_modifier,
        )
        critical += _mobile_critical_hit_damage(
            level,
            wielding=wielding,
            damage_modifier=mobile.damage_modifier,
        )

    reserve = ceil(max_hp * 0.20)
    mana_cost = 2 * output.resource_cost if output.resource == "mana" else 0
    if output.resource == "mana" and (
        max_mana <= 0 or mana - mana_cost < ceil(max_mana * 0.15)
    ):
        return EncounterBudget(
            False,
            "level-bound encounter would consume the 15% mana reserve",
            tuple(vnums), 0, expected, peak, reserve, mana_cost,
        )
    return EncounterBudget(
        True,
        "live identities and levels pass; enemy HP does not gate this encounter",
        tuple(vnums), 0, expected, peak, reserve, mana_cost,
    )


def _red_dragon_fire_reset_shape_allowed(
    world: WorldSource,
    mobile_vnum: int,
) -> bool:
    """Match the exact armed fire-breath Sanctuary maintenance reset."""
    if mobile_vnum != 7040:
        return False
    mobile = world.mobiles.get(mobile_vnum)
    resets = [reset for reset in world.mob_resets if reset.mobile_vnum == 7040]
    orb = world.objects.get(7303)
    weapon = world.objects.get(7216)
    expected_equipment = {
        (5, 7304),
        (7, 7305),
        (9, 7306),
        (6, 7307),
        (11, 7308),
        (10, 7309),
        (8, 7310),
        (WEAR_WIELD, 7216),
        (WEAR_HOLD, 7303),
    }
    return bool(
        mobile is not None
        and mobile.level == 30
        and mobile.sentinel
        and not mobile.wanders
        and mobile.aggressive
        and not mobile.fear_aura
        and not mobile.confused
        and not mobile.programs
        and not mobile.attack_programs
        and not mobile.non_corporeal
        and not mobile.costs_fame
        and set(world.mobile_specials.get(7040, ())) == {"spec_breath_fire"}
        and len(resets) == 1
        and resets[0].room_vnum == 7428
        and resets[0].maximum_count == 1
        and set(resets[0].equipment) == expected_equipment
        and set(resets[0].object_vnums)
        == {7304, 7305, 7306, 7307, 7308, 7309, 7310, 7216, 7303}
        and weapon is not None
        and weapon.item_type == ITEM_WEAPON
        and orb is not None
        and orb.item_type == ITEM_STAFF
    )


def _encounter_special_is_allowed(
    world: WorldSource,
    mobile_vnum: int,
    allowed_adept_special_vnums: Collection[int],
    allowed_caerlin_special_vnums: Collection[int] = (),
    allowed_hephaestus_special_vnums: Collection[int] = (),
    allowed_red_dragon_fire_special_vnums: Collection[int] = (),
) -> bool:
    specials = set(world.mobile_specials.get(mobile_vnum, ()))
    if not specials:
        return True
    mobile = world.mobiles.get(mobile_vnum)
    resets = [reset for reset in world.mob_resets if reset.mobile_vnum == mobile_vnum]
    adept_allowed = (
        mobile_vnum in allowed_adept_special_vnums
        and specials == {"spec_cast_adept"}
        and mobile is not None
        and mobile.sentinel
        and not mobile.aggressive
        and not mobile.wanders
        and not mobile.fear_aura
        and not mobile.programs
        and not mobile.non_corporeal
        and not mobile.costs_fame
        and len(resets) == 1
        and resets[0].maximum_count == 1
    )
    caerlin_allowed = (
        mobile_vnum in allowed_caerlin_special_vnums
        and mobile_vnum == 19004
        and specials == {"spec_cast_cleric"}
        and mobile is not None
        and mobile.level == 35
        and (mobile.sentinel or (mobile.wanders and mobile.stay_area))
        and not mobile.aggressive
        and not mobile.fear_aura
        and not mobile.confused
        and not mobile.programs
        and not mobile.non_corporeal
        and not mobile.costs_fame
        and len(resets) == 1
        and resets[0].room_vnum == 19068
        and resets[0].maximum_count == 1
        and any(
            object_vnum == 19173
            for _slot, object_vnum in resets[0].equipment
        )
        and all(
            (item := world.objects.get(object_vnum)) is not None
            and item.item_type != ITEM_WEAPON
            for reset in resets
            for _slot, object_vnum in reset.equipment
        )
    )
    hephaestus_allowed = (
        mobile_vnum in allowed_hephaestus_special_vnums
        and mobile_vnum == 908
        and specials == {"spec_breath_lightning"}
        and mobile is not None
        and mobile.level == 38
        and mobile.sentinel
        and not mobile.wanders
        and not mobile.aggressive
        and not mobile.fear_aura
        and not mobile.confused
        and not mobile.programs
        and not mobile.non_corporeal
        and not mobile.costs_fame
        and len(resets) == 1
        and resets[0].room_vnum == 937
        and resets[0].maximum_count == 1
        and 926 in resets[0].object_vnums
        and all(
            (item := world.objects.get(object_vnum)) is not None
            and item.item_type != ITEM_WEAPON
            for reset in resets
            for _slot, object_vnum in reset.equipment
        )
    )
    red_dragon_allowed = (
        mobile_vnum in allowed_red_dragon_fire_special_vnums
        and specials == {"spec_breath_fire"}
        and _red_dragon_fire_reset_shape_allowed(world, mobile_vnum)
    )
    return (
        adept_allowed
        or caerlin_allowed
        or hephaestus_allowed
        or red_dragon_allowed
    )


def source_multi_encounter_budget(
    world: WorldSource,
    mobile_vnums: Sequence[int],
    *,
    character_level: int,
    hp: int,
    max_hp: int,
    mana: int,
    max_mana: int,
    output: SourceCombatOutput | None,
    # Target HP is observation data by default; level/consider and the
    # player's own-health floor remain the live admission boundaries.
    target_hp_evidence_only: bool = True,
    target_maximum_level_offset: int = 1,
    allowed_adept_special_vnums: Collection[int] = (),
    require_near_full_health: bool = True,
) -> EncounterBudget:
    """Price two exact easy-band source mobiles before either one engages.

    The caller must separately bind unique room selectors and fresh easy-kill
    considers. Use the upper source level bounds for both mobiles so this
    admission never relies on concealed live values for the bystander; target
    HP remains observation/report data.
    """
    if len(mobile_vnums) != 2 or len(set(mobile_vnums)) != 2:
        return EncounterBudget(False, "source material encounter needs two distinct mobiles")
    if output is None or output.conservative_damage <= 0:
        return EncounterBudget(False, "no executable source-backed damage action")
    if (
        character_level <= 0
        or not 0 < hp <= max_hp
        or (
            require_near_full_health
            and hp < ceil(max_hp * .95)
        )
        or (
            not require_near_full_health
            and hp <= ceil(max_hp * .20)
        )
    ):
        return EncounterBudget(False, "source material admission is below its health boundary")

    if target_hp_evidence_only:
        if not 0 <= target_maximum_level_offset <= 5:
            return EncounterBudget(False, "source target level offset is outside consider range")
        levels: list[tuple[int, Any]] = []
        for index, mobile_vnum in enumerate(mobile_vnums):
            mobile = world.mobiles.get(mobile_vnum)
            if mobile is None:
                return EncounterBudget(False, "source material mobile is unavailable")
            if (
                mobile.aggressive or mobile.programs or mobile.non_corporeal
                or mobile.costs_fame
                or not _encounter_special_is_allowed(
                    world,
                    mobile_vnum,
                    allowed_adept_special_vnums,
                )
                or mobile_vnum in world.shopkeepers
            ):
                return EncounterBudget(False, "source material mobile requires a separate hazard policy")
            if not mobile.damage_modifier_known:
                return EncounterBudget(False, "source mobile damage modifier is unavailable")
            resets = [
                reset for reset in world.mob_resets
                if reset.mobile_vnum == mobile_vnum
            ]
            if not resets or max(reset.maximum_count for reset in resets) > 4:
                return EncounterBudget(False, "source material mobile has no bounded reset population")
            if any(
                slot in {WEAR_WIELD, WEAR_DUAL}
                and (
                    (item := world.objects.get(object_vnum)) is None
                    or item.item_type == ITEM_WEAPON
                )
                for reset in resets
                for slot, object_vnum in reset.equipment
            ):
                return EncounterBudget(False, "source material mobile retains the armed-target gate")
            lower, upper = _mobile_level_range(mobile.level)
            lower = max(lower, character_level - 4)
            upper = min(
                upper,
                character_level + target_maximum_level_offset
                if index == 0
                else character_level - 2,
            )
            if lower <= 0 or lower > upper:
                return EncounterBudget(False, "source material mobile has no considered level-band intersection")
            levels.append((upper, mobile))

        expected = sum(
            mobile_expected_round_damage(
                level,
                wielding=False,
                dual_wielding=False,
                damage_modifier=mobile.damage_modifier,
            )
            for level, mobile in levels
        )
        peak = sum(
            _mobile_peak_round_damage(
                level,
                wielding=False,
                dual_wielding=False,
                damage_modifier=mobile.damage_modifier,
            )
            for level, mobile in levels
        )
        reserve = ceil(max_hp * 0.20)
        mana_cost = 2 * output.resource_cost if output.resource == "mana" else 0
        if output.resource == "mana" and (
            max_mana <= 0 or mana - mana_cost < ceil(max_mana * 0.15)
        ):
            return EncounterBudget(
                False,
                "source material encounter would consume the 15% mana reserve",
                tuple(mobile_vnums), 0, expected, peak, reserve, mana_cost,
            )
        return EncounterBudget(
            True,
            "source identities and consider levels pass; target HP is not used",
            tuple(mobile_vnums), 0, expected, peak, reserve, mana_cost,
        )

    enemies: list[dict[str, int | str]] = []
    for mobile_vnum in mobile_vnums:
        mobile = world.mobiles.get(mobile_vnum)
        if mobile is None:
            return EncounterBudget(False, "source material mobile is unavailable")
        if (
            mobile.aggressive or mobile.programs or mobile.non_corporeal
            or mobile.costs_fame or world.mobile_specials.get(mobile_vnum)
            or mobile_vnum in world.shopkeepers
        ):
            return EncounterBudget(False, "source material mobile requires a separate hazard policy")
        if not mobile.hp_modifier_known:
            return EncounterBudget(False, "source mobile HP modifier is unavailable")
        if not mobile.damage_modifier_known:
            return EncounterBudget(False, "source mobile damage modifier is unavailable")
        resets = [
            reset for reset in world.mob_resets
            if reset.mobile_vnum == mobile_vnum
        ]
        if not resets or max(reset.maximum_count for reset in resets) > 4:
            return EncounterBudget(False, "source material mobile has no bounded reset population")
        if any(
            slot in {WEAR_WIELD, WEAR_DUAL}
            and (
                (item := world.objects.get(object_vnum)) is None
                or item.item_type == ITEM_WEAPON
            )
            for reset in resets
            for slot, object_vnum in reset.equipment
        ):
            return EncounterBudget(False, "source material mobile retains the armed-target gate")
        lower, upper = _mobile_level_range(mobile.level)
        lower = max(lower, character_level - 4)
        upper = min(upper, character_level - 2)
        if lower <= 0 or lower > upper:
            return EncounterBudget(False, "source material mobile has no easy-band level intersection")
        enemies.append({
            "isnpc": str(mobile_vnum),
            "level": str(upper),
            "hp": "1",
            "maxhp": "1",
        })

    budget = active_encounter_budget(
        world,
        enemies,
        character_level=character_level,
        hp=hp,
        max_hp=max_hp,
        mana=mana,
        max_mana=max_mana,
        output=output,
        target_hp_evidence_only=True,
        maximum_level_offsets_by_vnum={
            int(mobile_vnum): target_maximum_level_offset
            for mobile_vnum in mobile_vnums
        },
    )
    if budget.allowed and not target_hp_evidence_only:
        # This is a finite command window for the source-ranked fallback, not
        # a claim about how many attacks the target's HP requires.
        budget = replace(
            budget,
            actions=max(1, min(6, 2 * max(1, output.maximum_actions))),
        )
    return replace(
        budget,
        reason="source-estimated two-mobile encounter: " + budget.reason,
    )
