from dataclasses import replace

import pytest

from dd4tester.character import CharacterSpec
from dd4tester.equipment import STANCE_COMBAT, STANCE_PRE_LEVEL, STANCE_RECOVERY
from dd4tester.hunt_candidates import (
    MobileSource, MobReset, SourceCombatOutput, WorldSource, _parse_area_xp_modifier,
)
from dd4tester.level_gear import single_kill_gear_window
from dd4tester.starter import FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


def _world() -> WorldSource:
    return WorldSource(
        mobiles={100: MobileSource(100, "target", "the target", 22, 2, 0, "test.are")},
        mob_resets=[MobReset(100, 200, 1, ())],
        area_xp_modifiers={"test.are": 100},
    )


def _window(world: WorldSource, **changes) -> int | None:
    values = dict(character_level=26, maximum_action_damage=210, maximum_runtime=180)
    return single_kill_gear_window(world, 100, **(values | changes))


def test_plain_reward_window_includes_damage_regeneration_and_best_reward() -> None:
    # level 24: 952 base, +119 popularity, ceiling 1179 random reward.
    # 768 max HP, 20 * 36 regeneration, 630 amplified final hit, 11 allowance.
    assert _window(_world()) == 3308
    world = _world()
    world.area_xp_modifiers["test.are"] = 125
    assert _window(world) > 3308
    assert _window(_world(), maximum_runtime=900) > 3308


@pytest.mark.parametrize("unknown", ("area", "special", "gear", "hp", "template"))
def test_complex_rewards_do_not_narrow_stat_gear_window(unknown: str) -> None:
    world = _world()
    if unknown == "area":
        world.area_xp_modifiers.clear()
    elif unknown == "special":
        world.mobile_specials[100] = ("spec_guard",)
    elif unknown == "gear":
        world.mob_resets[0] = replace(world.mob_resets[0], equipment=((16, 300),))
    elif unknown == "hp":
        world.mobiles[100] = replace(world.mobiles[100], hp_modifier_known=False)
    else:
        world.mobiles[100] = replace(world.mobiles[100], template_name="unknown")
    assert _window(world) is None


@pytest.mark.parametrize(
    "lines,expected",
    ((["exp_mod 125", "$"], 125), (["school", "$"], 100),
     (["exp_mod -1", "$"], 100), (["exp_mod broken", "$"], None),
     (["reset_msg", "exp_mod 1", "~", "$"], None), (["exp_mod 125"], None)),
)
def test_area_reward_modifier_retains_unknown_syntax(lines, expected) -> None:
    assert _parse_area_xp_modifier(lines, (0, len(lines))) == expected
    assert _parse_area_xp_modifier([], None) == 100


def test_stat_gear_waits_for_next_kill_window_and_preserves_recovery(monkeypatch) -> None:
    spec = CharacterSpec("Aldrin", "DD4_TEST_PASSWORD", "human", "male", "warrior", max_runtime=180)
    policy = StarterPolicy(spec, "swordfish", source_world=_world(),
                           fastwalk_hunt_stops=(FieldHuntStop((), "target", source_mobile_vnum=100),))
    output = SourceCombatOutput("kick", 14, 96, 210, "actions", 0, 76, 12, "source")
    monkeypatch.setattr(policy, "_encounter_output", lambda state, vnums: output)
    state = CharacterState(level=26, xp_to_next_level=4175, progress={"xplvl": 45550},
                           hp=594, max_hp=594, mana=250, max_mana=250, move=400, max_move=400)
    assert policy._desired_gear_stance(state) == STANCE_COMBAT
    assert policy._desired_gear_stance(replace(state, xp_to_next_level=3308)) == STANCE_PRE_LEVEL
    assert policy.pre_level_xp_windows[(26, 100)] == 3308
    monkeypatch.setattr(policy, "_encounter_output", lambda state, vnums: replace(output, maximum_damage=700))
    assert policy._desired_gear_stance(state) == STANCE_PRE_LEVEL
    wider_window = policy.pre_level_xp_windows[(26, 100)]
    monkeypatch.setattr(policy, "_encounter_output", lambda state, vnums: output)
    assert policy._desired_gear_stance(state) == STANCE_PRE_LEVEL
    assert policy.pre_level_xp_windows[(26, 100)] == wider_window
    policy.waiting_for_heal = True
    assert policy._desired_gear_stance(state) == STANCE_RECOVERY
    policy.waiting_for_heal = False
    policy.fastwalk_hunt_stops = (replace(policy.fastwalk_hunt_stops[0], allow_source_bystander_encounter=True),)
    assert policy._desired_gear_stance(state) == STANCE_PRE_LEVEL
