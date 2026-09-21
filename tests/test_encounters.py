from dataclasses import replace

import pytest

from dd4tester.encounters import (
    active_encounter_budget,
    source_multi_encounter_budget,
    source_pair_budget,
)
from dd4tester.hunt_candidates import (
    ITEM_WEAPON, WEAR_WIELD, MobileProgram, MobileSource, MobReset,
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


def test_active_encounter_can_finish_two_low_hp_enemies():
    budget = _budget()
    assert budget.allowed
    assert budget.actions == 2
    assert budget.expected_incoming == 49
    assert budget.peak_round == 80
    assert budget.health_reserve == 46
    assert budget.mana_cost == 60


def test_active_encounter_accounts_for_every_enemy_and_worst_defeat_order():
    first = _enemies(10, 30)
    budget = _budget(enemies=first)
    assert budget.expected_incoming == 63
    assert _budget(enemies=list(reversed(first))) == replace(budget, mobile_vnums=(2, 1))
    three = _budget(enemies=_enemies(10, 10, 10), hp=240, max_hp=240)
    assert three.allowed
    assert three.actions == 3
    assert three.expected_incoming == 84


@pytest.mark.parametrize("changes,reason", [
    ({"hp": 80}, "health reserve"),
    ({"mana": 100}, "mana reserve"),
    ({"max_mana": 0}, "mana reserve"),
    ({"output": None}, "damage action"),
    ({"enemies": _enemies(100, 100)}, "six-action"),
    ({"enemies": _enemies(10, 10, 10, 10)}, "one to three"),
])
def test_active_encounter_rejects_insufficient_budget(changes, reason):
    budget = _budget(**changes)
    assert not budget.allowed
    assert reason in budget.reason


@pytest.mark.parametrize("field,value", [
    ("hp", "unknown"), ("hp", "0"), ("hp", "101"), ("maxhp", None),
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
    assert budget.actions == 2
    assert budget.mana_cost == 0
    assert not _budget(output=output, enemies=_enemies(100, 100)).allowed


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
    assert budget.level_ceiling == 5 and budget.target_hp_ceiling == 65
    assert budget.peak_round == 80 and budget.health_reserve == 46
    assert budget.actions == 8 and budget.mana_cost == 250
    assert budget.expected_incoming == 28  # Initial two-round probe, not the whole fight.


@pytest.mark.parametrize("changes", [
    {"hp": 100}, {"hp": 80, "max_hp": 80}, {"mana": 298}, {"max_mana": 0},
    {"character_level": 11}, {"output": None},
    {"output": SourceCombatOutput("kick", 4, 6, 8, "actions", 0, 4)},
])
def test_source_pair_rejects_inadequate_initial_budget(changes):
    assert not _source_pair(**changes).allowed


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
    assert budget.actions > 0
    assert budget.expected_incoming > 0
    assert "two-mobile encounter" in budget.reason


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
