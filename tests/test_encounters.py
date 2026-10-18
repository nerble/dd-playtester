from dataclasses import replace

import pytest

from dd4tester.encounters import (
    active_encounter_budget,
    source_duplicate_pair_budget,
    source_multi_encounter_budget,
    source_pair_budget,
)
from dd4tester.hunt_candidates import (
    ACT_SENTINEL, ITEM_WEAPON, WEAR_WIELD, MobileProgram, MobileSource, MobReset,
    ObjectSource, SourceCombatOutput, WorldSource,
)


def _world():
    return WorldSource(
        mobiles={vnum: MobileSource(vnum, f"mob{vnum}", f"mob{vnum}", 5, 0, 0, "test.are")
                 for vnum in (1, 2, 3)},
        mob_resets=[MobReset(vnum, 100, 1, ()) for vnum in (1, 2, 3)],
    )


def _enemies(*hps):
    return [{"isnpc": str(index + 1), "name": f"mob{index + 1}",
             "level": "5", "hp": str(hp), "maxhp": "100"}
            for index, hp in enumerate(hps)]


def _budget(world=None, enemies=None, **overrides):
    params = dict(character_level=8, hp=113, max_hp=113, mana=324, max_mana=324,
                  output=SourceCombatOutput("chill touch", 18, 23, 28, "mana", 10, 18))
    params.update(overrides)
    return active_encounter_budget(world or _world(), enemies or _enemies(10, 10), **params)


def test_active_encounter_accepts_two_source_level_enemies_without_target_hp():
    budget = _budget()
    assert budget.allowed
    assert budget.actions == 0
    assert budget.expected_incoming == 14
    assert budget.peak_round == 80
    assert budget.health_reserve == 23
    assert budget.mana_cost == 20


def test_active_encounter_accounts_for_every_enemy_and_worst_defeat_order():
    first = _enemies(10, 30)
    budget = _budget(enemies=first)
    assert budget.expected_incoming == 14
    assert _budget(enemies=list(reversed(first))) == replace(budget, mobile_vnums=(2, 1))
    three = _budget(enemies=_enemies(10, 10, 10), hp=240, max_hp=240)
    assert three.allowed
    assert three.actions == 0
    assert three.expected_incoming == 21


@pytest.mark.parametrize("changes,reason", [
    ({"hp": 20}, "20% withdrawal"),
    ({"mana": 20}, "mana reserve"),
    ({"max_mana": 0}, "mana reserve"),
    ({"output": None}, "damage action"),
    ({"enemies": _enemies(10, 10, 10, 10)}, "one to three"),
])
def test_active_encounter_rejects_insufficient_budget(changes, reason):
    budget = _budget(**changes)
    assert not budget.allowed
    assert reason in budget.reason


@pytest.mark.parametrize("field,value", [
    ("isnpc", "999"), ("isnpc", "2"), ("level", "9"), ("level", "0"),
])
def test_active_encounter_rejects_missing_or_inconsistent_enemy_state(field, value):
    enemies = _enemies(10, 10)
    enemies[0][field] = value
    assert not _budget(enemies=enemies).allowed


@pytest.mark.parametrize("hazard", ["special", "program", "weapon", "missing_weapon", "missing_reset"])
def test_active_encounter_preserves_source_hazard_and_equipment_gates(hazard):
    world = _world()
    if hazard == "special":
        world.mobile_specials[1] = ("spec_poison",)
    elif hazard == "program":
        world.mobiles[1] = replace(world.mobiles[1], programs=(MobileProgram("fight_prog", "100", ("mpkill $n",)),))
    elif hazard == "missing_reset":
        world.mob_resets = world.mob_resets[1:]
    else:
        world.mob_resets[0] = replace(world.mob_resets[0], equipment=((WEAR_WIELD, 1000),))
        if hazard == "weapon":
            world.objects[1000] = ObjectSource(1000, "knife", "a knife", ITEM_WEAPON, (0, 1, 4, 2), 10)
    assert not _budget(world=world).allowed


def test_active_encounter_rejects_unknown_mobile_damage_modifier():
    world = _world()
    world.mobiles[1] = replace(
        world.mobiles[1],
        damage_modifier=None,
        damage_modifier_known=False,
    )

    budget = _budget(world=world)

    assert not budget.allowed
    assert "damage modifier is unavailable" in budget.reason


def test_active_encounter_physical_damage_does_not_require_mana_or_credit_backstab():
    output = SourceCombatOutput("kick", 10, 15, 20, "actions", 0, 12,
                                opening_conservative_damage=1000)
    budget = _budget(output=output, mana=0, max_mana=0)
    assert budget.allowed
    assert budget.actions == 0
    assert budget.mana_cost == 0
    assert _budget(output=output, enemies=_enemies(100, 100)).allowed


def _source_pair(**overrides):
    world = _world()
    world.mobiles[1] = replace(world.mobiles[1], level=3)
    params = dict(character_level=8, hp=113, max_hp=113, mana=324, max_mana=324,
                  output=SourceCombatOutput("chill touch", 18, 23, 28, "mana", 25, 18))
    params.update(overrides)
    return source_pair_budget(world, 1, **params)


def test_source_pair_reserves_two_full_loads_and_actual_practice_mana_cost():
    budget = _source_pair()
    assert budget.allowed
    assert budget.mobile_vnums == (1, 1)
    assert budget.level_ceiling == 5 and budget.target_hp_ceiling == 0
    assert budget.peak_round == 80 and budget.health_reserve == 46
    assert budget.actions == 8 and budget.mana_cost == 250
    assert budget.expected_incoming == 28  # Initial two-round probe, not the whole fight.


@pytest.mark.parametrize("changes", [
    {"hp": 100}, {"hp": 80, "max_hp": 80}, {"mana": 298}, {"max_mana": 0},
    {"character_level": 11}, {"output": None},
])
def test_source_pair_rejects_inadequate_initial_budget(changes):
    assert not _source_pair(**changes).allowed


def test_source_pair_accepts_action_resource_without_target_hp_gate():
    budget = _source_pair(
        output=SourceCombatOutput("kick", 4, 6, 8, "actions", 0, 4),
    )
    assert budget.allowed
    assert budget.target_hp_ceiling == 0 and budget.mana_cost == 0


@pytest.mark.parametrize("hazard", ["special", "aggressive", "shop", "missing_reset", "population", "armed"])
def test_source_pair_does_not_bypass_source_hazards(hazard):
    world = _world()
    world.mobiles[1] = replace(world.mobiles[1], level=3)
    if hazard == "special":
        world.mobile_specials[1] = ("spec_poison",)
    elif hazard == "aggressive":
        world.mobiles[1] = replace(world.mobiles[1], act_flags=32)
    elif hazard == "shop":
        world.shopkeepers.add(1)
    elif hazard == "missing_reset":
        world.mob_resets.clear()
    elif hazard == "population":
        world.mob_resets[0] = replace(world.mob_resets[0], maximum_count=5)
    else:
        world.mob_resets[0] = replace(world.mob_resets[0], equipment=((WEAR_WIELD, 999),))
    assert not source_pair_budget(
        world, 1, character_level=8, hp=113, max_hp=113, mana=324, max_mana=324,
        output=SourceCombatOutput("chill touch", 18, 23, 28, "mana", 25, 18),
    ).allowed


def _source_duplicate_pair(**overrides):
    world = _world()
    world.mobiles[1] = replace(
        world.mobiles[1],
        level=39,
        act_flags=ACT_SENTINEL,
    )
    world.objects[1000] = ObjectSource(
        1000, "longsword", "a longsword", ITEM_WEAPON,
        (0, 1, 8, 0), 100,
    )
    world.mob_resets[0] = replace(
        world.mob_resets[0],
        room_vnum=100,
        maximum_count=2,
        object_vnums=(1000,),
        equipment=((WEAR_WIELD, 1000),),
    )
    params = dict(
        room_vnum=100,
        character_level=39,
        hp=1000,
        max_hp=1000,
        mana=0,
        max_mana=0,
        output=SourceCombatOutput("kick", 100, 100, 100, "actions", 0, 12),
        sanctuary_mitigation=True,
    )
    params.update(overrides)
    return source_duplicate_pair_budget(world, 1, **params)


def test_source_duplicate_pair_uses_live_consider_and_own_floor_not_target_hp():
    budget = _source_duplicate_pair()

    assert budget.allowed
    assert budget.source_only
    assert budget.mobile_vnums == (1, 1)
    assert budget.target_hp_ceiling == 0
    assert budget.health_reserve == 200
    assert "target HP" not in budget.reason


@pytest.mark.parametrize("change", [
    {"sanctuary_mitigation": False, "hp": 700, "max_hp": 1000},
    {"max_mana": 0, "mana": 0, "output": SourceCombatOutput("spell", 100, 100, 100, "mana", 60, 12)},
])
def test_source_duplicate_pair_keeps_armed_and_resource_boundaries(change):
    assert not _source_duplicate_pair(**change).allowed


def _source_multi(**overrides):
    world = _world()
    world.mobiles[1] = replace(world.mobiles[1], level=5)
    world.mobiles[2] = replace(world.mobiles[2], level=3)
    params = dict(
        character_level=8,
        hp=240,
        max_hp=240,
        mana=324,
        max_mana=324,
        output=SourceCombatOutput("chill touch", 28, 35, 42, "mana", 25, 28),
    )
    params.update(overrides)
    return source_multi_encounter_budget(world, (1, 2), **params)


def test_source_multi_prices_two_distinct_easy_band_mobiles():
    budget = _source_multi()

    assert budget.allowed
    assert budget.mobile_vnums == (1, 2)
    assert budget.actions == 0
    assert budget.expected_incoming > 0
    assert "target HP is not used" in budget.reason


def test_level_only_source_pair_uses_consider_band_not_enemy_hp():
    world = _world()
    world.mobiles[1] = replace(
        world.mobiles[1],
        level=44,
        hp_modifier=50000,
        hp_modifier_known=False,
    )
    world.mobiles[2] = replace(world.mobiles[2], level=37)

    budget = source_multi_encounter_budget(
        world,
        (1, 2),
        character_level=39,
        hp=950,
        max_hp=1000,
        mana=324,
        max_mana=324,
        output=SourceCombatOutput("kick", 28, 35, 42, "actions", 0, 28),
        target_hp_evidence_only=True,
        target_maximum_level_offset=5,
    )

    assert budget.allowed
    assert budget.actions == 0
    assert budget.health_reserve == 200
    assert "target HP is not used" in budget.reason


def test_live_level_only_pair_ignores_enemy_hp_but_keeps_level_and_floor_gates():
    world = _world()
    world.mobiles[1] = replace(world.mobiles[1], level=44)
    enemy = {"name": "mob1", "isnpc": "1", "level": "44"}
    kwargs = dict(
        character_level=39,
        hp=500,
        max_hp=1000,
        mana=324,
        max_mana=324,
        output=SourceCombatOutput("kick", 28, 35, 42, "actions", 0, 28),
        target_hp_evidence_only=True,
        maximum_level_offsets_by_vnum={1: 5},
    )

    assert active_encounter_budget(world, [enemy], **kwargs).allowed
    enemy["level"] = "45"
    assert not active_encounter_budget(world, [enemy], **kwargs).allowed
    enemy["level"] = "44"
    kwargs["hp"] = 199
    assert not active_encounter_budget(world, [enemy], **kwargs).allowed


@pytest.mark.parametrize("hazard", [
    "special", "aggressive", "program", "armed", "missing_reset", "population",
])
def test_source_multi_preserves_source_hazard_boundaries(hazard):
    world = _world()
    world.mobiles[1] = replace(world.mobiles[1], level=5)
    world.mobiles[2] = replace(world.mobiles[2], level=3)
    if hazard == "special":
        world.mobile_specials[2] = ("spec_poison",)
    elif hazard == "aggressive":
        world.mobiles[2] = replace(world.mobiles[2], act_flags=32)
    elif hazard == "program":
        world.mobiles[2] = replace(
            world.mobiles[2],
            programs=(MobileProgram("fight_prog", "100", ("mpkill $n",)),),
        )
    elif hazard == "missing_reset":
        world.mob_resets = world.mob_resets[:1]
    elif hazard == "population":
        world.mob_resets[1] = replace(world.mob_resets[1], maximum_count=5)
    else:
        world.mob_resets[1] = replace(world.mob_resets[1], equipment=((WEAR_WIELD, 999),))

    budget = source_multi_encounter_budget(
        world,
        (1, 2),
        character_level=8,
        hp=113,
        max_hp=113,
        mana=324,
        max_mana=324,
        output=SourceCombatOutput("chill touch", 18, 23, 28, "mana", 25, 18),
    )

    assert not budget.allowed
