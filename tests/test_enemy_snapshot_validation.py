import json

import pytest

from dd4tester.observations import GameEvent, ObservationParser
from dd4tester.state import CharacterState
from test_combat_timing import policy_fixture


ENEMY = [{"name": "Katrina the Shepherd", "hp": "31", "maxhp": "54", "isnpc": "2405", "level": "5"}]


@pytest.mark.parametrize("body", [
    "[  ] ]", '"[]"', "null", "false", "1", "{}",
    '["not an enemy"]', '[{"hp": 1}]', '{"name": ""}',
])
def test_invalid_enemy_packet_is_audited_without_poisoning_snapshot_cache(body):
    parser = ObservationParser()
    initial = parser.feed_gmcp("Char.Enemies " + json.dumps([ENEMY]))
    state = CharacterState(in_combat=True)
    state.apply(initial[0])
    rejected = parser.feed_gmcp("Char.Enemies " + body)
    assert [event.type for event in rejected] == ["gmcp_snapshot_rejected"]
    state.apply(rejected[0])
    assert state.enemies == [ENEMY] and state.in_combat
    assert parser.feed_gmcp("Char.Enemies " + json.dumps([ENEMY])) == []
    ended = parser.feed_gmcp("Char.Enemies []")
    state.apply(ended[0])
    assert state.enemies == [] and not state.in_combat


@pytest.mark.parametrize("value", [[], [[]], ENEMY, [ENEMY], ENEMY[0]])
def test_real_dd4_enemy_shapes_remain_accepted(value):
    events = ObservationParser().feed_gmcp("Char.Enemies " + json.dumps(value))
    assert [event.type for event in events] == ["enemies_changed"]
    assert events[0].data["value"] == value


def test_single_record_enemy_packet_updates_character_and_policy(monkeypatch):
    policy, state, clock = policy_fixture(monkeypatch)
    events = ObservationParser().feed_gmcp("Char.Enemies " + json.dumps(ENEMY[0]))
    state.apply(events[0])
    policy.observe_events(events, state)
    assert state.enemies == ENEMY[0]
    assert policy.combat_active and policy.active_target == "Katrina the Shepherd"
    assert policy.active_target_mobile_vnum == 2405


def test_legacy_malformed_event_cannot_erase_policy_or_character_encounter(monkeypatch):
    policy, state, clock = policy_fixture(monkeypatch)
    policy.enemy_snapshot_room = "2415"
    policy.enemy_snapshot_stale = False
    event = GameEvent("enemies_changed", "gmcp", {"value": "[  ] ]"})
    state.apply(event)
    policy.observe_events([event], state)
    assert state.in_combat and state.enemies
    assert policy.combat_active
    assert policy.active_target == "Katrina the Shepherd"
    assert policy.active_target_selector == "#22916"


def test_run_12756_departure_and_malformed_gmcp_preserve_player_finisher(monkeypatch):
    policy, state, clock = policy_fixture(monkeypatch)
    policy.familiar_active = True
    policy.familiar_preparation.selector = "#23706"
    policy.enemy_snapshot_room = "2415"
    policy.enemy_snapshot_stale = False
    assert policy._between_round_combat_decision(state).command == "order #23706 flee"
    clock[0] = 4
    policy.observe_text("The pony leaves west.\nThe pony has fled!\nOk.\n<113/113 hits 169/324 mana 202/220 move [Ultima]> ")
    events = ObservationParser().feed_gmcp("Char.Enemies [  ] ]")
    for event in events:
        state.apply(event)
    policy.observe_events(events, state)
    assert not policy.familiar_active and policy.familiar_withdrawal.confirmed
    assert policy.combat_active and policy.active_target
    assert policy._between_round_combat_decision(state).command == "cast 'chill touch' #22916"
    assert policy.fastwalk_abort_reason is None
