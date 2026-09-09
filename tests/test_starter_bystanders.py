from dataclasses import replace
import json
from pathlib import Path

import pytest

from dd4tester import starter
from dd4tester.character import CharacterSpec
from dd4tester.connection import ReadResult
from dd4tester.fastwalks import route_named
from dd4tester.hunt_candidates import (
    ACT_AGGRESSIVE,
    ACT_SENTINEL,
    AFF_NON_CORPOREAL,
    MobileProgram,
    MobileSource,
    MobReset,
    ObjectSource,
    ITEM_WEAPON,
    WorldSource,
)
from dd4tester.observations import GameEvent
from dd4tester.starter import BotDecision, FieldHuntStop, StarterBotRunner, StarterPolicy
from dd4tester.state import CharacterState


def _encounter(character_class: str = "mage") -> tuple[StarterPolicy, CharacterState]:
    spec = CharacterSpec.from_mapping({
        "name": "Testchar", "race": "human", "gender": "female",
        "class": character_class, "subclass": None, "title": "",
    })
    world = WorldSource(mobiles={
        100: MobileSource(
            100, "illusionist", "the illusionist", 7, ACT_SENTINEL, 0,
            "test.are", room_description="The illusionist is doing tricks here.",
        ),
        101: MobileSource(
            101, "midget", "a midget", 3, ACT_SENTINEL, 0,
            "test.are", room_description="A midget is doing acrobatics here.",
        ),
    })
    stop = FieldHuntStop(
        (), "illusionist", source_mobile_vnum=100,
        exact_target=True, require_isolated=True,
    )
    policy = StarterPolicy(
        spec, "test-password", source_world=world,
        fastwalk_route=route_named("moria"),
        fastwalk_hunt_stops=(stop,), fastwalk_attack_target="illusionist",
        source_mobile_targets={
            "the illusionist is doing tricks here.": ("illusionist",),
            "a midget is doing acrobatics here.": ("midget",),
        },
        source_mobile_vnums_by_target_room={"illusionist": {"200": (100,)}},
        source_mobile_level_ranges_by_vnum={100: (5, 9), 101: (1, 5)},
    )
    policy.in_world = True
    policy.prompt_ready = True
    policy.current_room = "200"
    policy.world_boot_id = "test-boot"
    policy.room_target_counts["200"] = {"illusionist": 1, "midget": 1}
    policy.room_target_selectors["200"] = {
        "illusionist": ("#10",), "midget": ("#11",),
    }
    policy.room_target_selector_descriptions["200"] = {
        "#10": "the illusionist is doing tricks here.",
        "#11": "a midget is doing acrobatics here.",
    }
    state = CharacterState(
        level=8, room_vnum="200", hp=113, max_hp=113,
        mana=324, max_mana=324, move=220, max_move=220,
        position=7, enemies=[],
    )
    return policy, state


def _inspect(policy: StarterPolicy, state: CharacterState) -> None:
    decision = policy._consider_fastwalk_target(state)
    assert decision is not None
    assert decision.command == "consider #11"
    policy.after_command(decision)
    assert not policy.consider_response_pending


@pytest.mark.parametrize("character_class", ["mage", "thief", "warrior"])
@pytest.mark.parametrize("response", [
    "A midget is no match for you.\n",
    "You can kill a midget naked and weaponless.\n",
])
def test_bystander_consider_unblocks_only_ordinary_target_consider(
    character_class: str, response: str,
) -> None:
    policy, state = _encounter(character_class)
    _inspect(policy, state)
    policy.observe_text(response)
    policy.observe_events([GameEvent("prompt_seen", "gmcp", {})], state)

    assert policy._source_mobile_name_is_non_assisting_bystander("midget", state)
    assert policy.fastwalk_consider_outcomes == {}
    assert policy.fastwalk_source_consider_outcomes == {}
    assert policy.consider_target is None
    assert not policy.fastwalk_crowded
    decision = policy._consider_fastwalk_target(state)
    assert decision.command == "consider #10"
    assert policy.fastwalk_bystander_consider_outcomes == [{
        "room_vnum": "200", "level": 8, "selector": "#11",
        "source_mobile_vnum": 101, "boot_id": "test-boot",
        "below_assistance_band": True,
    }]


def test_bystander_consider_accepts_split_response_without_target_contamination() -> None:
    policy, state = _encounter()
    policy.consider_target = "illusionist"
    policy.consider_viable = True
    _inspect(policy, state)
    policy.observe_text("A midget is no mat")
    assert policy.bystander_consider_pending is not None
    policy.observe_text("ch for you.\n")
    policy.observe_text("It looks much healthier than you.\n")
    assert policy.consider_target is None
    assert policy.consider_viable is None
    assert not policy.consider_health_warning
    assert policy.fastwalk_source_consider_outcomes == {}
    assert policy._live_bystander_below_assistance_band("midget", state)


@pytest.mark.parametrize("response", [
    "The illusionist is no match for you.\n",
    "A midget looks like an easy kill.\n",
    "The perfect match!\n",
    "They are not here.\n",
    "Someone says 'A midget is no match for you.'\n",
    "",
])
def test_bystander_consider_refusals_and_wrong_subjects_do_not_authorize(response: str) -> None:
    policy, state = _encounter()
    _inspect(policy, state)
    policy.observe_text(response)
    policy.observe_events([GameEvent("prompt_seen", "gmcp", {})], state)
    assert policy.bystander_consider_pending is None
    assert not policy._live_bystander_below_assistance_band("midget", state)
    assert not policy.fastwalk_bystander_consider_outcomes[-1]["below_assistance_band"]
    assert policy._consider_fastwalk_target(state).command != "consider #11"
    assert policy.fastwalk_crowded


@pytest.mark.parametrize("change", ["move", "level", "boot", "selector", "description", "expiry", "familiar"])
def test_bystander_consider_authorization_is_exact_and_ephemeral(change: str, monkeypatch) -> None:
    policy, state = _encounter()
    monkeypatch.setattr(starter.time, "monotonic", lambda: 100.0)
    _inspect(policy, state)
    policy.observe_text("A midget is no match for you.\n")
    assert policy._live_bystander_below_assistance_band("midget", state)
    if change == "move":
        state.room_vnum = "201"
    elif change == "level":
        state.level = 9
    elif change == "boot":
        policy.world_boot_id = "another-boot"
    elif change == "selector":
        policy.room_target_selectors["200"]["midget"] = ("#12",)
    elif change == "description":
        policy.room_target_selector_descriptions["200"]["#11"] = "a stranger is here."
    elif change == "expiry":
        monkeypatch.setattr(starter.time, "monotonic", lambda: 130.0)
    else:
        policy.familiar_active = True
    assert not policy._live_bystander_below_assistance_band("midget", state)


@pytest.mark.parametrize("hazard", ["aggression", "script", "special", "shop", "form", "high_level", "duplicate"])
def test_bystander_consider_requires_unique_ordinary_source_identity(hazard: str) -> None:
    policy, state = _encounter()
    world = policy.source_world
    mobile = world.mobiles[101]
    if hazard == "aggression":
        world.mobiles[101] = replace(mobile, act_flags=ACT_AGGRESSIVE)
    elif hazard == "script":
        world.mobiles[101] = replace(mobile, programs=(MobileProgram("greet_prog", "100", ("kill $n",)),))
    elif hazard == "special":
        world.mobile_specials[101] = ("spec_poison",)
    elif hazard == "shop":
        world.shopkeepers.add(101)
    elif hazard == "form":
        world.mobiles[101] = replace(mobile, affected_flags=AFF_NON_CORPOREAL)
    elif hazard == "high_level":
        world.mobiles[101] = replace(mobile, level=6)
    else:
        world.mobiles[102] = replace(mobile, vnum=102)
    assert policy._bystander_source_instance("midget", state) is None
    assert policy._start_bystander_consider(state, "illusionist", {"midget": 1}) is None


def test_bystander_consider_rejects_multiple_live_instances_and_missing_selector() -> None:
    policy, state = _encounter()
    policy.room_target_selectors["200"]["midget"] = ("#11", "#12")
    assert policy._bystander_source_instance("midget", state) is None
    policy.room_target_selectors["200"]["midget"] = ("midget",)
    assert policy._bystander_source_instance("midget", state) is None


@pytest.mark.parametrize("boundary", ["north", "recall", "flee", "disconnect"])
def test_bystander_consider_does_not_survive_departure_or_disconnect(boundary: str) -> None:
    policy, state = _encounter()
    _inspect(policy, state)
    policy.observe_text("A midget is no match for you.\n")
    if boundary == "disconnect":
        policy.on_connection_closed()
    else:
        policy.after_command(BotDecision(boundary, "test boundary"))
    assert not policy.bystander_consider_results
    assert policy.bystander_consider_pending is None
    assert policy.bystander_consider_attempts == 0
    assert len(policy.fastwalk_bystander_consider_outcomes) == 1


@pytest.mark.parametrize("interruption", ["timeout", "combat"])
def test_bystander_consider_wait_is_bounded_and_combat_preemptible(interruption: str, monkeypatch) -> None:
    policy, state = _encounter()
    monkeypatch.setattr(starter.time, "monotonic", lambda: 100.0)
    _inspect(policy, state)
    if interruption == "timeout":
        monkeypatch.setattr(starter.time, "monotonic", lambda: 105.0)
    else:
        state.in_combat = True
    policy.next_decision(state)
    assert policy.bystander_consider_pending is None
    assert not policy.fastwalk_bystander_consider_outcomes[-1]["below_assistance_band"]


def test_bystander_consider_limits_per_visit_inspections() -> None:
    policy, state = _encounter()
    policy.bystander_consider_attempts = 3
    assert policy._start_bystander_consider(state, "illusionist", {"midget": 1}) is None


def test_bystander_consider_endpoint_uses_same_precombat_evidence() -> None:
    policy, state = _encounter()
    policy.text = (
        "[#11] A midget is doing acrobatics here.\n"
        "[#10] The illusionist is doing tricks here.\n"
    )
    allowed, decision = policy._fastwalk_endpoint_attacker_gate(
        state, "illusionist", policy.fastwalk_hunt_stops[0],
    )
    assert not allowed
    assert decision.command == "consider #11"
    policy.after_command(decision)
    policy.observe_text("A midget is no match for you.\n")
    policy._fastwalk_endpoint_attacker_gate(state, "illusionist", policy.fastwalk_hunt_stops[0])
    assert not policy.fastwalk_crowded
    assert policy.fastwalk_abort_reason is None


def _runner_read(policy, state, messages, text=""):
    runner = StarterBotRunner(policy.spec, Path("test-profile.yaml"))
    runner.character_state = state

    def record(kind, payload):
        if kind == "game_event":
            state.apply(GameEvent(payload["type"], payload["source"], payload["data"]))

    runner._record_read(ReadResult(text=text, gmcp_messages=messages), record, policy)
    return runner


@pytest.mark.parametrize("character_class", ["mage", "thief", "warrior"])
@pytest.mark.parametrize("enemy_first", [True, False])
def test_runner_arrival_reconciles_same_read_enemy(character_class, enemy_first) -> None:
    policy, state = _encounter(character_class)
    enemy = {"name": "the drunk", "level": "2", "isnpc": "3064", "hp": "20"}
    room = 'Room.Info {"name":"Arrival","vnum":"201","exits":{}}'
    enemies = "Char.Enemies " + json.dumps([[enemy]])
    _runner_read(policy, state, [enemies, room] if enemy_first else [room, enemies])
    assert state.room_vnum == "201"
    assert policy.enemy_snapshot_room == "201"
    assert not policy.enemy_snapshot_stale
    assert policy._current_room_enemy_records(state) == [enemy]


def test_runner_arrival_does_not_revive_old_visit_enemy() -> None:
    policy, state = _encounter()
    state.enemies = [[{"name": "old enemy", "level": "2"}]]
    policy.enemy_snapshot_room = "201"
    policy.enemy_snapshot_stale = True
    _runner_read(policy, state, ['Room.Info {"name":"Arrival","vnum":"201","exits":{}}'])
    assert not policy._current_room_enemy_records(state)


def test_runner_arrival_does_not_bind_ambiguous_early_enemy() -> None:
    policy, state = _encounter()
    _runner_read(policy, state, [
        'Char.Enemies [[{"name":"old enemy","level":"2"}]]',
        'Room.Info {"name":"Arrival","vnum":"201","exits":{}}',
        'Room.Info {"name":"Later","vnum":"202","exits":{}}',
    ])
    assert state.room_vnum == "202"
    assert not policy._current_room_enemy_records(state)


def test_bystander_consider_runner_records_response_before_prompt() -> None:
    policy, state = _encounter()
    _inspect(policy, state)
    _runner_read(policy, state, ['Core.Prompt "ready"'], "A midget is no match for you.\n")
    assert policy._live_bystander_below_assistance_band("midget", state)


def test_bystander_consider_holds_only_for_fight_started_with_fresh_evidence(monkeypatch) -> None:
    policy, state = _encounter()
    monkeypatch.setattr(starter.time, "monotonic", lambda: 100.0)
    _inspect(policy, state)
    policy.observe_text("A midget is no match for you.\n")
    state.in_combat = True
    policy.combat_active = policy.fastwalk_attack_started = True
    policy.active_target = "the illusionist"
    policy.active_target_selector = "#10"
    assert policy._live_bystander_below_assistance_band("midget", state)
    monkeypatch.setattr(starter.time, "monotonic", lambda: 140.0)
    assert policy._live_bystander_below_assistance_band("midget", state)
    policy.completed_kills.append({"target": "the illusionist"})
    assert not policy._live_bystander_below_assistance_band("midget", state)


def test_bystander_consider_expired_evidence_cannot_be_revived_by_combat(monkeypatch) -> None:
    policy, state = _encounter()
    monkeypatch.setattr(starter.time, "monotonic", lambda: 100.0)
    _inspect(policy, state)
    policy.observe_text("A midget is no match for you.\n")
    monkeypatch.setattr(starter.time, "monotonic", lambda: 140.0)
    state.in_combat = True
    policy.combat_active = policy.fastwalk_attack_started = True
    policy.active_target = "the illusionist"
    policy.active_target_selector = "#10"
    assert not policy._live_bystander_below_assistance_band("midget", state)


def _active_pair(character_class="mage"):
    policy, state = _encounter(character_class)
    policy.source_world.mob_resets = [MobReset(vnum, 200, 1, ()) for vnum in (100, 101)]
    skill = {"mage": "chill touch", "thief": "circle", "warrior": "kick"}[character_class]
    policy.known_skills = {skill}
    policy.known_skill_levels = {skill: 35}
    if character_class != "mage":
        weapon = ObjectSource(500, "dagger", "a dagger", ITEM_WEAPON, (0, 5, 7, 2), 10)
        policy.gear_worn = [weapon]
        policy.gear_worn_structured_current = True
        policy.gear_wielded_vnum = 500
        policy.primary_weapon_observed = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(policy.fastwalk_route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_attack_started = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    policy.fastwalk_hunt_looked = True
    policy.consider_target = "illusionist"
    policy.consider_viable = True
    state.in_combat = True
    state.enemies = [[
        {"name": "the illusionist", "isnpc": "100", "level": "5", "hp": "10", "maxhp": "70"},
        {"name": "a midget", "isnpc": "101", "level": "5", "hp": "10", "maxhp": "50"},
    ]]
    policy.observe_events([GameEvent("enemies_changed", "gmcp", {"value": state.enemies})], state)
    policy.prompt_ready = True
    return policy, state


@pytest.mark.parametrize("character_class,action", [("mage", "cast 'chill touch'"), ("thief", "circle"), ("warrior", "kick")])
def test_active_encounter_runtime_finishes_affordable_pair_instead_of_count_only_flee(character_class, action):
    policy, state = _active_pair(character_class)
    if character_class != "mage":
        state.hp = state.max_hp = 150
    decision = policy.next_decision(state)
    assert decision is not None
    assert decision.command.startswith(action)
    assert "2-enemy encounter" in decision.reason
    assert policy.active_encounter_vnums == frozenset({100, 101})
    assert policy.fastwalk_encounter_budgets[-1]["allowed"]


@pytest.mark.parametrize("character_class", ["thief", "warrior"])
def test_active_encounter_weaker_physical_output_requires_more_health(character_class):
    policy, state = _active_pair(character_class)
    assert policy._active_encounter_decision(state) == (False, None)
    assert policy.fastwalk_encounter_budgets[-1]["actions"] == 4
    assert policy.fastwalk_encounter_budgets[-1]["expected_incoming"] == 70


@pytest.mark.parametrize("character_class", ["thief", "warrior"])
def test_active_encounter_gmcp_hidden_stats_do_not_invent_damage(character_class):
    policy, state = _active_pair(character_class)
    parser = starter.ObservationParser()
    captured_stats = next(
        line for line in (Path(__file__).parent / "fixtures" / "dd4_gmcp.txt")
        .read_text(encoding="utf-8").splitlines() if line.startswith("Char.Stats ")
    )
    for event in parser.feed_gmcp(captured_stats):
        state.apply(event)
        policy.observe_events([event], state)
    assert state.stats["damroll"] == 50000  # Raw evidence is not rewritten.
    assert policy._active_encounter_decision(state) == (False, None)
    assert policy.fastwalk_encounter_budgets[-1]["actions"] == 4
    assert policy.fastwalk_encounter_budgets[-1]["expected_incoming"] == 70


@pytest.mark.parametrize("change", ["hp", "mana", "unknown", "armed", "duplicate", "special", "unconsidered_level", "stale"])
def test_active_encounter_runtime_preserves_rejection_boundaries(change):
    policy, state = _active_pair()
    if change == "hp":
        state.hp = 75
    elif change == "mana":
        state.mana = 50
    elif change == "unknown":
        state.enemies[0][1]["isnpc"] = "9999"
    elif change == "armed":
        policy.source_world.mob_resets[1] = replace(policy.source_world.mob_resets[1], equipment=((16, 900),))
    elif change == "duplicate":
        policy.active_enemy_duplicate_count = 1
    elif change == "special":
        policy.source_world.mobile_specials[101] = ("spec_poison",)
    elif change == "unconsidered_level":
        state.enemies[0][0]["level"] = "3"
    else:
        policy.enemy_snapshot_stale = True
    handled, decision = policy._active_encounter_decision(state)
    assert not handled
    assert decision is None


def test_active_encounter_runtime_never_opens_an_unengaged_crowd():
    policy, state = _active_pair()
    policy.fastwalk_attack_started = False
    state.in_combat = False
    assert policy._active_encounter_decision(state) == (False, None)


def test_active_encounter_retains_only_already_admitted_remaining_attacker():
    policy, state = _active_pair()
    assert policy._active_encounter_decision(state)[0]
    state.enemies = [[state.enemies[0][1]]]
    policy.observe_events([GameEvent("enemies_changed", "gmcp", {"value": state.enemies})], state)
    policy.between_round_action_issued = False
    policy.between_round_action_ready_at = 0
    handled, decision = policy._active_encounter_decision(state)
    assert handled
    assert decision is not None and "1-enemy encounter" in decision.reason
    state.enemies[0][0]["isnpc"] = "102"
    assert policy._active_encounter_decision(state) == (False, None)


def test_active_encounter_permission_expires_without_rearming(monkeypatch):
    policy, state = _active_pair()
    monkeypatch.setattr(starter.time, "monotonic", lambda: 100.0)
    assert policy._active_encounter_decision(state)[0]
    monkeypatch.setattr(starter.time, "monotonic", lambda: 130.0)
    assert policy._active_encounter_decision(state) == (False, None)
    assert policy.active_encounter_started_at == 100.0


def test_active_encounter_respects_existing_failed_damage_window(monkeypatch):
    policy, state = _active_pair()
    monkeypatch.setattr(starter.time, "monotonic", lambda: 100.0)
    assert policy._active_encounter_decision(state)[0]
    assert policy.field_combat_damage_probe_required
    policy.field_combat_probe_started_at = 1.0
    policy.field_combat_probe_total_damage = 0
    policy.field_combat_probe_player_damage = 20
    handled, decision = policy._active_encounter_decision(state)
    assert handled
    assert decision is not None and decision.command == "flee"
    assert "damage" in decision.reason


@pytest.mark.parametrize("boundary", ["north", "flee", "recall", "disconnect"])
def test_active_encounter_authorization_never_survives_a_departure(boundary):
    policy, state = _active_pair()
    assert policy._active_encounter_decision(state)[0]
    if boundary == "disconnect":
        policy.on_connection_closed()
    else:
        policy.after_command(BotDecision(boundary, "test"))
    assert not policy.active_encounter_vnums
    assert policy.active_encounter_started_at is None
    assert policy.fastwalk_encounter_budgets


def _below_band_endpoint(character_class="mage"):
    policy, state = _active_pair(character_class)
    mobile = MobileSource(
        1524, "hermit crab", "a hermit", 5, ACT_AGGRESSIVE, 0,
        "gnome.are", room_description="A hermit crab crawls towards you.",
    )
    policy.source_world.mobiles = {1524: mobile}
    policy.source_world.mob_resets = [MobReset(1524, 1589, 1, ())]
    policy.fastwalk_hunt_stops = (FieldHuntStop(
        (), "hermit crab", source_mobile_vnum=1524,
        source_reset_room_vnum=1589,
        source_mobile_room_description=mobile.room_description,
        exact_target=True, require_isolated=True,
    ),)
    policy.fastwalk_attack_target = "hermit crab"
    policy.fastwalk_attack_started = False
    policy.current_room = state.room_vnum = "1589"
    policy.room_target_counts["1589"] = {"hermit crab": 1}
    policy.room_target_selectors["1589"] = {"hermit crab": ("#23779",)}
    policy.room_target_selector_descriptions["1589"] = {
        "#23779": "a hermit crab crawls towards you.",
    }
    policy.source_mobile_level_ranges_by_vnum[1524] = (3, 7)
    policy.source_mobile_vnums_by_target_room["hermit crab"] = {"1589": (1524,)}
    state.position = 6
    state.hunger, state.thirst = 11, 48
    state.enemies = [[{
        "name": "a hermit", "level": "3", "hp": "26", "maxhp": "29",
        "isnpc": "1524", "long_desc": "A hermit crab crawls towards you.  ",
    }]]
    policy.observe_events([GameEvent("enemies_changed", "gmcp", {"value": state.enemies})], state)
    policy.active_target = "a hermit"
    policy.active_target_selector = "#23779"
    policy.unapproved_field_attacker = None
    policy.active_enemy_duplicate_count = 0
    return policy, state


@pytest.mark.parametrize("character_class,action", [
    ("mage", "cast 'chill touch'"), ("thief", "circle"), ("warrior", "kick"),
])
def test_run_12798_finishes_engaged_low_load_without_spending_xp_to_flee(character_class, action):
    policy, state = _below_band_endpoint(character_class)
    decision = policy.next_decision(state)
    assert decision is not None and decision.command.startswith(action)
    if character_class != "warrior":
        assert decision.command.endswith("#23779")
    assert policy.active_encounter_target.selector == "#23779"
    assert policy.fastwalk_hunt_stop_skipped
    assert not policy.fastwalk_emergency_recall_pending
    assert not policy.fastwalk_attack_started  # No new XP-target authorization.
    audit = policy.fastwalk_encounter_budgets[-1]
    assert audit["mode"] == "below-band-endpoint-defense" and audit["allowed"]
    if character_class == "mage":
        assert audit["actions"] == 2 and audit["mana_cost"] == 100


@pytest.mark.parametrize("boundary", [
    "not_engaged", "hp", "mana", "nutrition", "runtime", "return", "no_recall",
    "familiar", "require_familiar", "consider_only", "no_source", "unknown",
    "duplicate", "add", "special", "armed", "missing_selector", "replacement", "room",
])
def test_below_band_endpoint_defense_preserves_survival_and_identity_gates(boundary):
    policy, state = _below_band_endpoint()
    if boundary == "not_engaged":
        state.in_combat = False
    elif boundary == "hp":
        state.hp = 50
    elif boundary == "mana":
        state.mana = 120  # Enough for minimum-cost fiction, not practiced cost.
    elif boundary == "nutrition":
        policy.needs_food = True
    elif boundary == "runtime":
        policy.runtime_boundary_requested = True
    elif boundary == "return":
        policy.return_home = True
    elif boundary == "no_recall":
        state.room_flags = {"no_recall"}
    elif boundary == "familiar":
        policy.familiar_active = True
    elif boundary in {"require_familiar", "consider_only"}:
        policy.fastwalk_hunt_stops = (replace(policy.fastwalk_hunt_stops[0], **{boundary: True}),)
    elif boundary == "no_source":
        policy.source_world = None
    elif boundary == "unknown":
        state.enemies[0][0]["isnpc"] = "99999"
    elif boundary in {"duplicate", "add"}:
        state.enemies[0].append(dict(state.enemies[0][0]))
        if boundary == "add":
            state.enemies[0][-1]["isnpc"] = "100"
    elif boundary == "special":
        policy.source_world.mobile_specials[1524] = ("spec_poison",)
    elif boundary == "armed":
        policy.source_world.mob_resets[0] = replace(
            policy.source_world.mob_resets[0], equipment=((16, 900),),
        )
    elif boundary == "missing_selector":
        policy.active_target_selector = None
    elif boundary == "room":
        state.room_vnum = "1588"
    else:
        policy.room_target_selectors["1589"] = {"hermit crab": ("#999",)}
    assert policy._active_encounter_decision(state, defensive_endpoint=True) == (False, None)


@pytest.mark.parametrize("change", ["timeout", "level", "boot", "selector"])
def test_below_band_defense_cannot_reopen_on_scope_change(monkeypatch, change):
    policy, state = _below_band_endpoint()
    monkeypatch.setattr(starter.time, "monotonic", lambda: 100.0)
    assert policy._active_encounter_decision(state, defensive_endpoint=True)[0]
    if change == "timeout":
        monkeypatch.setattr(starter.time, "monotonic", lambda: 130.0)
    elif change == "level":
        state.level += 1
    elif change == "boot":
        policy.world_boot_id = "new boot"
    else:
        policy.active_target_selector = "#999"
        policy.room_target_selectors["1589"] = {"hermit crab": ("#999",)}
    assert policy._active_encounter_decision(state, defensive_endpoint=True) == (False, None)
    assert policy.active_encounter_started_at == 100.0


def test_below_band_defensive_kill_is_not_objective_progression():
    policy, state = _below_band_endpoint()
    assert policy.next_decision(state).command.startswith("cast")
    policy.observe_events([GameEvent("experience_gained", "text", {"xp": 30})], state)
    policy.observe_text("A hermit is DEAD!!\n")
    assert policy.completed_kills
    assert policy.completed_kills[-1]["below_useful_band"]
    assert policy.completed_kills[-1]["objective_eligible"] is False
    assert not policy.objective_kills


def test_below_band_defense_uses_captured_gmcp_and_damage_acknowledgement(monkeypatch):
    policy, state = _below_band_endpoint()
    parser = starter.ObservationParser()
    packet = 'Char.Enemies [ [ { "name": "a hermit", "level": "3", "hp": "26", "maxhp": "29", "isnpc": "1524", "long_desc": "A hermit crab crawls towards you.  " } ] ]'
    for event in parser.feed_gmcp(packet):
        state.apply(event)
        policy.observe_events([event], state)
    monkeypatch.setattr(starter.time, "monotonic", lambda: 100.0)
    decision = policy.next_decision(state)
    assert decision.command == "cast 'chill touch' #23779"
    policy.after_command(decision)
    policy.observe_text("A hermit misses you.\n")
    policy.prompt_ready = True
    assert policy.next_decision(state) is None
    assert not policy.fastwalk_emergency_recall_pending
    policy.observe_text("Your chilling touch wounds a hermit.\n")
    monkeypatch.setattr(starter.time, "monotonic", lambda: 103.3)
    policy.prompt_ready = True
    assert policy.next_decision(state).command == "cast 'chill touch' #23779"


@pytest.mark.parametrize("boundary", ["north", "flee", "recall", "disconnect"])
def test_below_band_defense_identity_is_session_local(boundary):
    policy, state = _below_band_endpoint()
    assert policy.next_decision(state).command.startswith("cast")
    if boundary == "disconnect":
        policy.on_connection_closed()
    else:
        policy.after_command(BotDecision(boundary, "test"))
    assert policy.active_encounter_target is None
    assert policy.active_encounter_started_at is None


def test_empty_enemy_update_does_not_grant_a_second_defensive_endpoint_fight():
    policy, state = _below_band_endpoint()
    assert policy.next_decision(state).command.startswith("cast")
    saved_enemies = state.enemies
    event = GameEvent("enemies_changed", "gmcp", {"value": []})
    state.apply(event)
    policy.observe_events([event], state)
    assert policy.active_encounter_target is None
    assert policy.defensive_endpoint_used
    event = GameEvent("enemies_changed", "gmcp", {"value": saved_enemies})
    state.apply(event)
    policy.observe_events([event], state)
    policy.active_target_selector = "#23779"
    assert policy._active_encounter_decision(state, defensive_endpoint=True) == (False, None)


def _centipede_crowd():
    policy, state = _encounter()
    description = "A small centipede here is looking for vegetation."
    target = "small centipede"
    mobile = MobileSource(
        4002, "centipede", "the centipede", 3, ACT_SENTINEL, 0,
        "moria.are", room_description=description,
    )
    policy.source_world.mobiles = {4002: mobile}
    policy.fastwalk_hunt_stops = (FieldHuntStop(
        (), target, source_mobile_vnum=4002,
        source_mobile_room_description=description,
        exact_target=True, require_isolated=True,
    ),)
    policy.fastwalk_attack_target = target
    policy.source_mobile_targets = {description.lower(): (target,)}
    policy.source_mobile_vnums_by_target_room = {target: {"200": (4002,)}}
    policy.source_mobile_level_ranges_by_vnum = {4002: (1, 5)}
    policy.room_targets["200"] = [target]
    policy.room_target_counts["200"] = {target: 3}
    policy.room_target_selectors["200"] = {
        target: ["#23772", "#23724", "#23653"],
    }
    policy.room_target_selector_descriptions["200"] = {
        selector: description.lower() for selector in ("#23772", "#23724", "#23653")
    }
    policy.known_skills = {"chill touch"}
    policy.known_skill_levels = {"chill touch": 35}
    return policy, state


def _probe_centipedes(policy, state, replies):
    for selector, reply in zip(("#23772", "#23724", "#23653"), replies, strict=True):
        decision = policy._consider_fastwalk_target(state)
        assert decision.command == f"consider {selector}"
        policy.after_command(decision)
        _runner_read(policy, state, ['Core.Prompt "ready"'], reply + "\n")


def test_same_prototype_crowd_reconsiders_only_remaining_material_instance(monkeypatch):
    policy, state = _centipede_crowd()
    clock = [100.0]
    monkeypatch.setattr(starter.time, "monotonic", lambda: clock[0])
    _probe_centipedes(policy, state, (
        "The centipede looks like an easy kill.",
        "The centipede is no match for you.",
        "The centipede is no match for you.",
    ))
    decision = policy._consider_fastwalk_target(state)
    assert decision.command == "consider #23772"
    assert policy.consider_viable is None
    assert policy.consider_target_selector == "#23772"
    assert not policy.fastwalk_crowded
    assert policy.bystander_consider_attempts == 3
    assert not policy.fastwalk_source_consider_outcomes

    policy.after_command(decision)
    _runner_read(policy, state, ['Core.Prompt "ready"'],
                 "The centipede looks like an easy kill.\nAlso, you are currently healthier than it.\n")
    opener = policy._consider_fastwalk_target(state)
    assert opener.command == "kill #23772"
    policy.after_command(opener)
    enemy = {"name": "the centipede", "isnpc": "4002", "level": "5", "hp": "46", "maxhp": "55"}
    clock[0] = 100.5
    _runner_read(policy, state, ["Char.Enemies " + json.dumps([[enemy]])],
                 "Your pierce grazes the centipede.\n")
    assert policy.active_target_selector == "#23772"
    policy.between_round_action_issued = False
    policy.between_round_action_ready_at = 0
    clock[0] = 104.0
    assert policy._between_round_combat_decision(state).command == "cast 'chill touch' #23772"


@pytest.mark.parametrize("reply", [
    "The centipede looks like an easy kill.", "The perfect match!",
    "Someone says 'The centipede is no match for you.'", "They are not here.", "",
])
def test_same_prototype_crowd_never_treats_uncertain_or_material_adds_as_harmless(reply):
    policy, state = _centipede_crowd()
    _probe_centipedes(policy, state, (reply,) * 3)
    assert policy._consider_fastwalk_target(state).command == "look"
    assert policy.fastwalk_crowded
    assert not policy.fastwalk_attack_started
    assert policy.bystander_consider_attempts == 3


@pytest.mark.parametrize("change", ["expired", "boot", "level", "replacement", "description"])
def test_same_prototype_crowd_does_not_reuse_changed_instance_evidence(change, monkeypatch):
    policy, state = _centipede_crowd()
    clock = [100.0]
    monkeypatch.setattr(starter.time, "monotonic", lambda: clock[0])
    _probe_centipedes(policy, state, (
        "The centipede looks like an easy kill.",
        "The centipede is no match for you.", "The centipede is no match for you.",
    ))
    if change == "expired":
        clock[0] = 130.0
    elif change == "boot":
        policy.world_boot_id = "new-boot"
    elif change == "level":
        state.level = 7
    elif change == "replacement":
        policy.room_target_selectors["200"]["small centipede"][1] = "#99999"
    else:
        policy.room_target_selector_descriptions["200"]["#23724"] = "a different mobile."
    assert policy._consider_fastwalk_target(state).command == "look"
    assert policy.fastwalk_crowded


def test_all_below_band_copies_still_require_ordinary_negative_consider():
    policy, state = _centipede_crowd()
    _probe_centipedes(policy, state, ("The centipede is no match for you.",) * 3)
    decision = policy._consider_fastwalk_target(state)
    # Two audits suffice to isolate the final instance. Its own consider is
    # an objective-level check, not permission inferred from the crowd audit.
    assert decision.command == "look"
    assert policy.consider_viable is False
    assert policy.bystander_consider_attempts == 2
    assert not policy.fastwalk_attack_started


@pytest.mark.parametrize("selectors", [
    ["#1", "#2"], ["#1", "#1", "#2"], ["#1", "#2", "#3", "#4"],
])
def test_same_prototype_probe_requires_complete_unique_bounded_listing(selectors):
    policy, state = _centipede_crowd()
    policy.room_target_selectors["200"]["small centipede"] = selectors
    assert policy._consider_fastwalk_target(state).command == "look"
    assert policy.bystander_consider_attempts == 0


@pytest.mark.parametrize("replace_selected", [False, True])
def test_active_source_combat_does_not_switch_to_a_same_name_bystander(replace_selected):
    policy, state = _centipede_crowd()
    policy.fastwalk_attack_started = policy.combat_active = True
    policy.consider_target = "small centipede"
    policy.consider_target_selector = policy.active_target_selector = "#23772"
    policy.active_target = "the centipede"
    if replace_selected:
        policy.room_target_selectors["200"]["small centipede"][0] = "#99999"
    assert policy._target_selector_for("the centipede") == "#23772"
    assert policy._between_round_combat_decision(state).command == "cast 'chill touch' #23772"


def test_precombat_instance_replacement_requires_a_new_consider():
    policy, state = _centipede_crowd()
    policy.room_target_counts["200"]["small centipede"] = 1
    policy.room_target_selectors["200"]["small centipede"] = ["#23724"]
    policy.consider_target = "small centipede"
    policy.consider_target_selector = "#23772"
    policy.consider_viable = True
    assert policy._consider_fastwalk_target(state).command == "consider #23724"
    assert policy.consider_viable is None
    assert not policy.fastwalk_attack_started


@pytest.mark.parametrize("collection", [list, tuple])
def test_defeated_combat_name_removes_only_its_source_room_instance(collection):
    policy, _ = _centipede_crowd()
    policy.room_target_selectors["200"]["small centipede"] = collection(
        policy.room_target_selectors["200"]["small centipede"],
    )
    policy._forget_defeated_room_target("the centipede", "#23772")
    assert policy.room_target_selectors["200"]["small centipede"] == ["#23724", "#23653"]
    assert policy.room_target_counts["200"]["small centipede"] == 2


def test_absent_defeated_selector_does_not_remove_a_live_same_name_replacement():
    policy, _ = _centipede_crowd()
    policy._forget_defeated_room_target("small centipede", "#99999")
    assert policy.room_target_selectors["200"]["small centipede"] == ["#23772", "#23724", "#23653"]
    assert policy.room_target_counts["200"]["small centipede"] == 3


def _prepared_source_pair(monkeypatch):
    policy, state = _centipede_crowd()
    policy.fastwalk_requested_target = None
    clock = [100.0]
    monkeypatch.setattr(starter.time, "monotonic", lambda: clock[0])
    policy.source_world.mob_resets = [MobReset(4002, 200, 3, ())]
    _probe_centipedes(policy, state, (
        "The centipede looks like an easy kill.",
        "The centipede looks like an easy kill.",
        "The centipede is no match for you.",
    ))
    decision = policy._consider_fastwalk_target(state)
    assert decision.command == "consider #23724"
    assert policy.source_pair_encounter is not None
    assert policy.source_pair_encounter.budget.mana_cost == 250
    policy.after_command(decision)
    _runner_read(policy, state, ['Core.Prompt "ready"'],
                 "The centipede looks like an easy kill.\n")
    opener = policy._consider_fastwalk_target(state)
    assert opener.command == "kill #23724"
    policy.after_command(opener)
    enemy = {"name": "the centipede", "isnpc": "4002", "level": "5", "hp": "46", "maxhp": "55"}
    clock[0] = 100.5
    _runner_read(policy, state, ["Char.Enemies " + json.dumps([[enemy, enemy]])],
                 "Your pierce grazes the centipede.\n")
    state.in_combat = True
    policy.fastwalk_recall_started = True
    policy.fastwalk_outbound_index = len(policy.fastwalk_route.commands)
    policy.fastwalk_arrival_observed = True
    policy.fastwalk_hunt_preflight_food_attempted = True
    policy.fastwalk_hunt_looked = True
    policy.between_round_action_ready_at = 0
    policy.between_round_action_issued = False
    policy.prompt_ready = True
    clock[0] = 104
    return policy, state, clock


def test_source_pair_live_duplicate_packet_keeps_exact_damage_target(monkeypatch):
    policy, state, _ = _prepared_source_pair(monkeypatch)
    assert policy.active_enemy_duplicate_count == 1
    decision = policy.next_decision(state)
    assert decision.command == "cast 'chill touch' #23724"
    assert not policy.fastwalk_emergency_recall_pending
    assert policy.fastwalk_encounter_budgets[-1]["mode"] == "source-pair"


def test_source_pair_first_kill_keeps_second_target_and_original_deadline(monkeypatch):
    policy, state, clock = _prepared_source_pair(monkeypatch)
    pair = policy.source_pair_encounter
    started = pair.started_at
    policy.after_command(policy.next_decision(state))
    clock[0] = 104.5
    policy.observe_text(
        "Your chilling touch mauls the centipede!\nThe centipede is DEAD!!\n"
        "You receive 111 experience points for the kill.\n"
    )
    assert pair.remaining == ("#23772",)
    assert not policy.fastwalk_hunt_stop_killed
    assert not policy.fastwalk_objective_budget_complete
    enemy = {"name": "the centipede", "isnpc": "4002", "level": "5", "hp": "50", "maxhp": "60"}
    _runner_read(policy, state, ["Char.Enemies " + json.dumps([[enemy]])])
    assert policy.active_target_selector == "#23772"
    clock[0] = 108
    policy.prompt_ready = True
    policy.between_round_action_issued = False
    handled, decision = policy._source_pair_combat_decision(state)
    assert handled and decision.command == "cast 'chill touch' #23772"
    assert pair.started_at == started
    policy.after_command(decision)
    policy.observe_text(
        "Your chilling touch mauls the centipede!\nThe centipede is DEAD!!\n"
        "You receive 112 experience points for the kill.\n"
    )
    assert policy.source_pair_encounter is None
    assert policy.fastwalk_hunt_stop_killed
    assert len(policy.objective_kills) == 2


@pytest.mark.parametrize("change", ["health", "timeout", "commands", "extra", "wrong_vnum", "hp_ceiling", "level", "boot"])
def test_source_pair_runtime_rejects_changed_or_exhausted_envelope(change, monkeypatch):
    policy, state, clock = _prepared_source_pair(monkeypatch)
    if change == "health":
        state.hp = 46
    elif change == "timeout":
        clock[0] = 145
    elif change == "commands":
        policy.source_pair_encounter.damage_commands = 12
    elif change == "extra":
        policy.active_enemy_duplicate_count = 2
    elif change == "wrong_vnum":
        state.enemies[0][0]["isnpc"] = "4004"
    elif change == "hp_ceiling":
        state.enemies[0][0]["maxhp"] = "100"
    elif change == "level":
        state.enemies[0][0]["level"] = "6"
    else:
        policy.world_boot_id = "new-boot"
    handled, decision = policy._source_pair_combat_decision(state)
    assert handled and decision.command == "flee"
    assert policy.source_pair_encounter is None
    assert policy.fastwalk_emergency_recall_pending


@pytest.mark.parametrize("boundary", ["north", "recall", "flee", "disconnect"])
def test_source_pair_never_restores_a_departed_encounter(boundary, monkeypatch):
    policy, _, _ = _prepared_source_pair(monkeypatch)
    if boundary == "disconnect":
        policy.on_connection_closed()
    else:
        policy.after_command(BotDecision(boundary, "boundary"))
    assert policy.source_pair_encounter is None


def test_source_pair_can_decline_after_losing_measured_exchange(monkeypatch):
    policy, state, clock = _prepared_source_pair(monkeypatch)
    clock[0] = 108
    policy.field_combat_probe_started_at = 100
    policy.field_combat_probe_total_damage = 20
    policy.field_combat_probe_player_damage = 15
    state.hp = 98
    handled, decision = policy._source_pair_combat_decision(state)
    assert handled and decision.command == "flee"
    assert "both remaining" in decision.reason


def test_source_pair_disengaged_second_target_needs_fresh_consider(monkeypatch):
    policy, state, clock = _prepared_source_pair(monkeypatch)
    pair = policy.source_pair_encounter
    policy.observe_text("The centipede is DEAD!!\nYou receive 111 experience points for the kill.\n")
    _runner_read(policy, state, ["Char.Enemies []"])
    state.in_combat = False
    policy.combat_active = False
    clock[0] = 108
    decision = policy._consider_fastwalk_target(state)
    assert decision.command == "consider #23772"
    assert policy.consider_viable is None
    assert pair.started_at == 100
    policy.after_command(decision)
    _runner_read(policy, state, ['Core.Prompt "ready"'], "The centipede looks like an easy kill.\n")
    assert policy._consider_fastwalk_target(state).command == "kill #23772"
    assert pair.started_at == 100


@pytest.mark.parametrize("change", ["mana", "missing_practice", "zero_practice", "wrong_class"])
def test_source_pair_requires_executable_and_funded_damage(change):
    policy, state = _centipede_crowd()
    policy.source_world.mob_resets = [MobReset(4002, 200, 3, ())]
    if change == "mana":
        state.mana = 298
    elif change == "missing_practice":
        policy.known_skill_levels = {}
    elif change == "zero_practice":
        policy.known_skill_levels = {"chill touch": 0}
    else:
        policy.spec = CharacterSpec.from_mapping({
            "name": "Otherchar", "race": "human", "gender": "male", "class": "warrior",
        })
    _probe_centipedes(policy, state, (
        "The centipede looks like an easy kill.", "The centipede looks like an easy kill.",
        "The centipede is no match for you.",
    ))
    assert policy._consider_fastwalk_target(state).command == "look"
    assert policy.source_pair_encounter is None


@pytest.mark.parametrize("change", ["mana", "health", "expiry"])
def test_source_pair_prepared_reserve_is_rechecked_before_attack(change, monkeypatch):
    policy, state, clock = _prepared_source_pair(monkeypatch)
    pair = policy.source_pair_encounter
    pair.started_at = None
    if change == "mana":
        state.mana = 298
    elif change == "health":
        state.hp = 100
    else:
        clock[0] = 130
    assert policy._source_pair_scope_issue(state, clock[0]) is not None
