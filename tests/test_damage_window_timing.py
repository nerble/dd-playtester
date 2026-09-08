from dataclasses import replace

import pytest

from dd4tester.character import CharacterSpec
from dd4tester.fastwalks import route_named
from dd4tester.starter import BotDecision, FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


@pytest.fixture
def willow_probe(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: clock[0])
    policy = StarterPolicy(
        CharacterSpec.from_mapping({
            "name": "Testwarrior", "race": "dwarf", "gender": "male",
            "class": "warrior",
        }),
        "fixture-password",
        title_configured=True, description_configured=True,
        fastwalk_route=route_named("moria"),
        known_skill_levels={"kick": 41, "headbutt": 49},
        fastwalk_hunt_stops=(FieldHuntStop(
            (), "the Weeping Willow", source_mobile_vnum=2304,
            source_target_armed=False,
            source_combat_action="kick", source_combat_max_actions=12,
            require_damage_window_probe=True,
        ),),
    )
    policy.in_world = policy.combat_active = policy.fastwalk_attack_started = True
    policy.field_combat_damage_probe_required = True
    policy.active_target = policy.fastwalk_attack_target = "the Weeping Willow"
    policy.active_target_selector = "#22156"
    policy.current_room = "2330"
    state = CharacterState(
        level=25, hp=569, max_hp=569, mana=250, max_mana=245,
        room_vnum="2330", position=6, in_combat=True,
        affects=[[{"name": "sanctuary", "duration": "4"}]],
    )
    policy._start_field_combat_damage_probe(state)
    policy.after_command(BotDecision("kill #22156", "open"))
    return policy, state, clock


def observe_round(policy, state, clock, elapsed, player_hp, target_hp):
    clock[0] = elapsed
    state.hp = player_hp
    state.enemies = [[{
        "name": "the Weeping Willow", "isnpc": "2304", "level": "24",
        "hp": str(target_hp), "maxhp": "740",
    }]]
    policy.observe_text(
        "Your slash injures The Weeping Willow.\n"
        f"<{player_hp}/569 hits 250/245 mana 400/442 move [Ultima]> "
    )
    policy._record_field_combat_damage_probe(state)
    policy.prompt_ready = True


def replay_12767(policy, state, clock):
    # Relative to the recorded kill command; no skill reply occurred in this run.
    for row in ((.494, 569, 712), (1.021, 553, 685), (4.019, 518, 660)):
        observe_round(policy, state, clock, *row)
    assert policy.field_combat_probe_total_damage == 80
    assert policy.field_combat_probe_player_damage == 51
    assert policy.field_combat_probe_samples == 3


def test_run_12767_probe_allows_first_registered_between_round_attack(willow_probe):
    policy, state, clock = willow_probe
    replay_12767(policy, state, clock)

    assert policy._damage_window_probe_decision(state) is None
    assert policy.field_combat_damage_probe_required
    decision = policy.next_decision(state)
    assert decision is not None and decision.command == "kick"
    assert policy.fastwalk_abort_reason is None


@pytest.mark.parametrize("elapsed,complete", [(6.499, False), (6.5, True), (12, True)])
def test_probe_still_rejects_the_same_poor_exchange_after_a_real_window(
    willow_probe, elapsed, complete,
):
    policy, state, clock = willow_probe
    replay_12767(policy, state, clock)
    clock[0] = elapsed

    decision = policy._damage_window_probe_decision(state)
    assert (decision is not None) is complete
    if complete:
        assert decision.command == "flee"
        assert "protected health budget" in policy.fastwalk_abort_reason


@pytest.mark.parametrize("elapsed", [6.5, 11.999, 12])
def test_probe_deadline_does_not_require_successful_hits(willow_probe, elapsed):
    policy, state, clock = willow_probe
    observe_round(policy, state, clock, .5, 569, 740)
    clock[0] = elapsed

    decision = policy._damage_window_probe_decision(state)
    assert (decision is not None) is (elapsed >= 12)
    if decision:
        assert decision.command == "flee"
        assert "0 damage" in policy.fastwalk_abort_reason


def test_fresh_followup_damage_can_change_the_verdict(willow_probe):
    policy, state, clock = willow_probe
    replay_12767(policy, state, clock)
    # Counterfactual continuation, not claimed as a live outcome.
    observe_round(policy, state, clock, 7, 500, 560)

    assert policy._damage_window_probe_decision(state) is None
    assert not policy.field_combat_damage_probe_required


def test_short_sampling_window_never_delays_emergency_withdrawal(willow_probe):
    policy, state, clock = willow_probe
    replay_12767(policy, state, clock)
    state.hp = 30

    decision = policy.next_decision(state)
    assert decision is not None and decision.command == "flee"
    assert "damage-output probe" not in decision.reason


def test_short_sampling_window_preserves_source_hp_fuzz_ceiling(willow_probe):
    policy, state, clock = willow_probe
    replay_12767(policy, state, clock)
    policy.fastwalk_hunt_stops = (replace(
        policy.fastwalk_hunt_stops[0], allow_unprotected_hp_fuzz_probe=True,
        source_target_hp_ceiling=500, source_combat_conservative_damage=20,
    ),)

    decision = policy.next_decision(state)
    assert decision is not None and decision.command == "flee"
    assert "HP ceiling" in policy.fastwalk_abort_reason


def test_rearming_probe_resets_elapsed_budget(willow_probe):
    policy, state, clock = willow_probe
    replay_12767(policy, state, clock)
    clock[0] = 100
    policy._start_field_combat_damage_probe(state)
    clock[0] = 105
    policy.field_combat_probe_samples = 3

    assert policy._damage_window_probe_decision(state) is None
    assert policy.field_combat_probe_started_at == 100
    policy._clear_field_combat_damage_probe()
    assert policy.field_combat_probe_started_at is None
