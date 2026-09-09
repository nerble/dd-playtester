import pytest

from dd4tester.encounters import solo_continuation_budget
from dd4tester.starter import BotDecision
from test_considered_solo import confirm_solo, solo_fixture


def live_window(monkeypatch):
    policy, state, clock = solo_fixture(monkeypatch)
    confirm_solo(policy, state)
    opening = policy._consider_fastwalk_target(state)
    policy.after_command(opening)
    # Run 12816: snapshots 8020315/8020323, before decision 8020328.
    state.hp, state.mana = 107, 212
    state.in_combat, state.position = True, 6
    state.enemies = [[dict(name="the large orc", isnpc="4005", level="6", hp="64", maxhp="79")]]
    policy.enemy_snapshot_stale = False
    policy.active_target_mobile_vnum = 4005
    policy.field_combat_probe_started_at = 0.0
    policy.field_combat_probe_samples = 3
    policy.field_combat_probe_total_damage = 15
    policy.field_combat_probe_player_damage = 6
    policy.field_combat_probe_regenerated_hp = 0
    clock[0] = 4.222
    policy.after_command(BotDecision("cast 'chill touch' #23798", "recorded first spell"))
    clock[0] = 4.743
    policy.observe_text("Your chilling touch misses the large orc.\n")
    clock[0] = 7.32
    return policy, state, clock


def test_run_12816_one_missed_spell_does_not_trigger_a_one_point_fraction_flee(monkeypatch):
    policy, state, clock = live_window(monkeypatch)
    assert policy.source_pair_encounter.damage_commands == 2
    assert policy._source_pair_combat_decision(state) == (True, None)
    assert policy.fastwalk_abort_reason is None
    assert not policy.fastwalk_emergency_recall_pending
    # The next cast still waits for the acknowledged source cooldown.
    clock[0] = 8.01
    handled, decision = policy._source_pair_combat_decision(state)
    assert handled and decision.command == "cast 'chill touch' #23798"
    assert policy.source_pair_encounter.started_at == 0


@pytest.mark.parametrize("boundary", ["mana", "hp", "observed-loss", "time", "commands", "no-progress", "companion"])
def test_solo_continuation_keeps_resource_and_observation_limits(monkeypatch, boundary):
    policy, state, clock = live_window(monkeypatch)
    if boundary == "mana":
        state.mana = 198
    elif boundary == "hp":
        state.hp = 80
    elif boundary == "observed-loss":
        policy.field_combat_probe_player_damage = 15
    elif boundary == "time":
        clock[0] = 30
    elif boundary == "commands":
        policy.source_pair_encounter.damage_commands = 4
    elif boundary == "no-progress":
        policy.field_combat_probe_total_damage = 0
        clock[0] = 12
    else:
        policy.familiar_standby.stage = "awake"
    handled, decision = policy._source_pair_combat_decision(state)
    assert handled and decision.command == "flee"
    assert policy.source_pair_encounter is None


def test_measured_solo_finish_never_uses_the_legacy_fraction_probe(monkeypatch):
    policy, state, _ = live_window(monkeypatch)
    monkeypatch.setattr(policy, "_damage_window_probe_decision", lambda state: pytest.fail("not the solo controller"))
    assert policy._source_pair_combat_decision(state) == (True, None)


def test_continuation_prices_actual_remaining_hp_and_preserves_the_reserve(monkeypatch):
    policy, state, _ = live_window(monkeypatch)
    enemy = state.enemies[0][0]
    values = dict(
        character_level=8, hp=107, max_hp=113, mana=212, max_mana=324,
        output=policy._encounter_output(state, (4005,)), elapsed=7.32,
        effective_damage=15, received_damage=6, remaining_seconds=37.68,
        remaining_commands=7,
    )
    budget = solo_continuation_budget(policy.source_world, [enemy], **values)
    assert budget.allowed and budget.actions == 4
    assert budget.mana_cost == 150 and budget.health_reserve == 46
    assert not solo_continuation_budget(policy.source_world, [enemy, enemy], **values).allowed
    assert not solo_continuation_budget(policy.source_world, [enemy], **(values | {"output": None})).allowed
