from dataclasses import replace

import pytest

from dd4tester.companions import FamiliarPreparation, FamiliarStandby
from dd4tester.encounters import source_solo_budget
from dd4tester.hunt_candidates import MobileSource, MobReset, SourceCombatOutput, WEAR_WIELD
from dd4tester.starter import BotDecision
from test_combat_timing import policy_fixture
from test_encounters import _world


def solo_fixture(monkeypatch):
    policy, state, clock = policy_fixture(monkeypatch)
    policy.combat_active = policy.fastwalk_attack_started = False
    policy.active_target = policy.active_target_selector = None
    policy.current_room = state.room_vnum = "4024"
    policy.last_character_level = state.level
    policy.world_boot_id = "fixture-boot"
    state.in_combat, state.position, state.enemies = False, 7, None
    policy.source_world.mobiles[4005] = MobileSource(
        4005, "orc large", "the large orc", 7, 0, 0, "moria.are",
        "This large orc is looking for someone small to pick on.",
    )
    policy.source_world.mob_resets.append(MobReset(4005, 4022, 1, ()))
    policy.fastwalk_hunt_stops = (replace(
        policy.fastwalk_hunt_stops[0], target="the large orc", source_mobile_vnum=4005,
        source_target_armed=False, exact_target=True,
        source_policy_id="source-ranked-hunt-moria-4005-4022-8",
    ),)
    policy.consider_target = "the large orc"
    policy.fastwalk_attack_target = "the large orc"
    policy.consider_target_selector = "#23798"
    policy.room_target_selectors["4024"] = {"the large orc": ["#23798"]}
    policy.room_target_selector_descriptions["4024"] = {
        "#23800": policy._staged_familiar_description(),
        "#23798": "this large orc is looking for someone small to pick on.",
    }
    policy.familiar_preparation = FamiliarPreparation(
        stage="ready", selector="#23800", summoned=True, grouped=True,
    )
    policy.familiar_active = True
    policy.after_command(BotDecision("consider #23798", "fresh exact consider"))
    policy.observe_text("The large orc looks like an easy kill.\n")
    return policy, state, clock


def solo_decision(policy, state):
    return policy._considered_solo_decision(state, policy.fastwalk_hunt_stops[0])


def confirm_solo(policy, state):
    handled, decision = solo_decision(policy, state)
    assert handled and decision.command == "order #23800 sleep"
    policy.after_command(decision)
    policy.observe_text("The pony sleeps.\nOk.\n")
    assert solo_decision(policy, state) == (False, None)
    assert policy._considered_solo_ready(state)
    assert not policy.familiar_active


def test_easy_consider_at_funded_boundary_reserves_full_solo_damage(monkeypatch):
    policy, state, _ = solo_fixture(monkeypatch)
    confirm_solo(policy, state)
    budget = policy.source_pair_encounter.budget
    assert budget.allowed and budget.mobile_vnums == (4005,)
    assert budget.target_hp_ceiling == 84 and budget.level_ceiling == 6
    assert budget.actions == 5 and budget.mana_cost == 175
    assert budget.peak_round == 50 and budget.health_reserve == 46
    assert not policy.familiar_preparation.order_pending
    assert policy.fastwalk_encounter_budgets[-1]["mode"] == "considered-solo"


def test_run_12811_actual_mana_keeps_the_familiar_path(monkeypatch):
    policy, state, _ = solo_fixture(monkeypatch)
    # Snapshot 8017877 precedes consider 8017878 and the NPC order 8017886.
    state.mana, state.move = 182, 78
    assert solo_decision(policy, state) == (False, None)
    assert policy.source_pair_encounter is None
    assert "mana reserve" in policy.fastwalk_encounter_budgets[-1]["reason"]
    decision = policy._familiar_precombat_decision(
        state, target="the large orc", allow_start=True,
    )
    assert decision.command == "order #23800 kill #23798"


@pytest.mark.parametrize("split", [1, 6, 22, 26, 33])
def test_fresh_fragmented_easy_consider_completes_the_normal_decision(monkeypatch, split):
    policy, state, _ = solo_fixture(monkeypatch)
    policy.consider_viable = None
    policy.after_command(BotDecision("consider #23798", "fresh exact consider"))
    response = "The large orc looks like an easy kill.\n"
    policy.observe_text(response[:split])
    assert policy.consider_viable is None and policy.consider_response_pending
    policy.observe_text(response[split:])
    assert policy.consider_viable is True and not policy.consider_response_pending
    assert policy.fastwalk_source_consider_outcomes[policy.fastwalk_hunt_stops[0].source_policy_id]
    assert solo_decision(policy, state)[1].command == "order #23800 sleep"


@pytest.mark.parametrize("boundary", ["room", "level", "boot", "stop", "selector", "timeout"])
def test_fragmented_consider_cannot_cross_its_request_scope(monkeypatch, boundary):
    policy, state, clock = solo_fixture(monkeypatch)
    policy.consider_viable = None
    policy.after_command(BotDecision("consider #23798", "fresh exact consider"))
    policy.observe_text("The large orc looks li")
    if boundary == "room":
        policy.current_room = "4022"
    elif boundary == "level":
        policy.last_character_level = 9
    elif boundary == "boot":
        policy.world_boot_id = "new-boot"
    elif boundary == "stop":
        policy.fastwalk_hunt_stop_index = 1
    elif boundary == "selector":
        policy.consider_target_selector = "#999"
    else:
        clock[0] = 20
    policy.observe_text("ke an easy kill.\n")
    assert policy.solo_consider_identity is None
    assert policy.consider_viable is not True


def test_fragmented_consider_retains_explicit_stop_rejection(monkeypatch):
    policy, state, _ = solo_fixture(monkeypatch)
    policy.consider_viable = None
    policy.fastwalk_hunt_stops = (replace(
        policy.fastwalk_hunt_stops[0], rejected_consider_fragments=("looks like an easy kill",),
    ),)
    policy.after_command(BotDecision("consider #23798", "fresh exact consider"))
    policy.observe_text("The large orc looks li")
    policy.observe_text("ke an easy kill.\n")
    assert policy.consider_viable is False
    assert solo_decision(policy, state) == (False, None)


def test_considered_solo_opens_through_normal_field_controller(monkeypatch):
    policy, state, _ = solo_fixture(monkeypatch)
    confirm_solo(policy, state)
    decision = policy._consider_fastwalk_target(state)
    assert decision.command in {"kill #23798", "cast 'chill touch' #23798"}
    assert policy.field_combat_damage_probe_required
    assert not policy.familiar_active
    policy.after_command(decision)
    assert policy.source_pair_encounter.started_at == 0
    assert policy.source_pair_encounter.damage_commands == 1


@pytest.mark.parametrize("boundary", [
    "unknown_consider", "room", "level", "boot", "stop", "expired", "target",
    "duplicate_target", "crowd", "owner", "duplicate_companion", "missing_companion",
    "practice", "damage_practice", "mana", "hp", "food", "drink", "runtime",
    "returning", "emergency", "combat", "no_recall", "required_loot", "sanctuary",
    "order_pending", "aggressive", "special", "population", "armed",
])
def test_solo_substitution_preserves_admission_boundaries(monkeypatch, boundary):
    policy, state, clock = solo_fixture(monkeypatch)
    if boundary == "unknown_consider":
        policy.solo_consider_identity = None
    elif boundary in {"room", "level"}:
        setattr(state, "room_vnum" if boundary == "room" else "level", "4022" if boundary == "room" else 9)
    elif boundary == "boot":
        policy.world_boot_id = "new-boot"
    elif boundary == "stop":
        policy.solo_consider_identity = replace(policy.solo_consider_identity, stop_index=1)
    elif boundary == "expired":
        clock[0] = 20
    elif boundary == "target":
        policy.consider_target_selector = "#999"
    elif boundary == "duplicate_target":
        policy.room_target_selectors["4024"]["the large orc"].append("#999")
    elif boundary in {"crowd", "duplicate_companion"}:
        policy.room_target_selector_descriptions["4024"]["#999"] = (
            "a guard" if boundary == "crowd" else policy._staged_familiar_description()
        )
    elif boundary == "missing_companion":
        del policy.room_target_selector_descriptions["4024"]["#23800"]
    elif boundary == "owner":
        policy.familiar_preparation.grouped = False
    elif boundary in {"practice", "damage_practice"}:
        policy.known_skill_levels["summon familiar" if boundary == "practice" else "chill touch"] = 0
    elif boundary in {"hp", "mana"}:
        setattr(state, boundary, 100 if boundary == "hp" else 223)
    elif boundary in {"food", "drink"}:
        setattr(policy, "needs_" + boundary, True)
    elif boundary == "runtime":
        policy.runtime_boundary_requested = True
    elif boundary == "returning":
        policy.fastwalk_returning = True
    elif boundary == "emergency":
        policy.fastwalk_emergency_recall_pending = True
    elif boundary == "combat":
        state.in_combat = True
    elif boundary == "no_recall":
        state.room_flags = ["no_recall"]
    elif boundary in {"required_loot", "sanctuary"}:
        key = "allow_below_band_for_required_loot" if boundary == "required_loot" else "require_sanctuary"
        policy.fastwalk_hunt_stops = (replace(policy.fastwalk_hunt_stops[0], **{key: True}),)
    elif boundary == "order_pending":
        policy.familiar_preparation.expect_order()
    elif boundary == "aggressive":
        policy.source_world.mobiles[4005] = replace(policy.source_world.mobiles[4005], act_flags=32)
    elif boundary == "special":
        policy.source_world.mobile_specials[4005] = ("spec_poison",)
    elif boundary == "population":
        policy.source_world.mob_resets[0] = replace(policy.source_world.mob_resets[0], maximum_count=5)
    elif boundary == "armed":
        policy.source_world.mob_resets[0] = replace(policy.source_world.mob_resets[0], equipment=((WEAR_WIELD, 999),))
    assert solo_decision(policy, state) == (False, None)
    assert policy.source_pair_encounter is None
    assert policy.familiar_standby is None


@pytest.mark.parametrize("reply", [
    "Ok.\n", "Someone says 'The pony sleeps.'\n", "The other pony sleeps.\n",
    "The pony wakes and readies himself for action.\n",
])
def test_sleep_requires_exact_positive_outcome_not_order_ack(monkeypatch, reply):
    policy, state, clock = solo_fixture(monkeypatch)
    _, decision = solo_decision(policy, state)
    policy.after_command(decision)
    policy.observe_text(reply)
    assert solo_decision(policy, state) == (True, None)
    assert not policy._considered_solo_ready(state)
    clock[0] = 5
    handled, decision = solo_decision(policy, state)
    assert handled and decision.command == "recall"
    assert policy.source_pair_encounter is None
    assert policy.familiar_unavailable


def test_pending_sleep_timeout_reopens_suppressed_policy_prompt(monkeypatch):
    policy, state, clock = solo_fixture(monkeypatch)
    _, decision = solo_decision(policy, state)
    policy.after_command(decision)
    assert not policy.prompt_ready
    clock[0] = 5
    policy.next_decision(state)
    assert policy.familiar_standby is None or policy.familiar_standby.failure


@pytest.mark.parametrize("enemy_snapshot", [False, True])
def test_completed_solo_wakes_owned_companion_before_return(monkeypatch, enemy_snapshot):
    policy, state, clock = solo_fixture(monkeypatch)
    confirm_solo(policy, state)
    policy.active_target = "the large orc"
    policy.active_target_selector = "#23798"
    policy.active_target_mobile_vnum = 4005 if enemy_snapshot else None
    policy.fastwalk_attack_started = policy.combat_active = True
    policy.after_command(BotDecision("kill #23798", "player opens solo"))
    policy.observe_text("The large orc is DEAD!!\nYou receive 195 experience points.\n")
    assert policy.objective_kills[0]["xp_gained"] == 195
    assert policy.source_pair_encounter is None
    handled, decision = policy._familiar_standby_return_decision(state)
    assert handled and decision.command == "order #23800 stand"
    policy.after_command(decision)
    policy.observe_text("Ok.\n")
    assert policy._familiar_standby_return_decision(state) == (True, None)
    clock[0] = 1
    policy.observe_text("The pony wakes and readies himself for action.\nOk.\n")
    assert policy._familiar_standby_return_decision(state) == (False, None)
    assert policy.familiar_standby is None


@pytest.mark.parametrize("boundary", ["mana", "hp", "selector", "owner"])
def test_admitted_solo_rechecks_resources_and_binding_after_sleep(monkeypatch, boundary):
    policy, state, _ = solo_fixture(monkeypatch)
    confirm_solo(policy, state)
    if boundary in {"mana", "hp"}:
        setattr(state, boundary, 100)
    elif boundary == "selector":
        policy.consider_target_selector = "#999"
    else:
        policy.familiar_preparation.grouped = False
    handled, decision = solo_decision(policy, state)
    assert handled and decision.command == "recall"


def test_solo_reuses_live_encounter_bounds_and_does_not_require_npc_damage(monkeypatch):
    policy, state, clock = solo_fixture(monkeypatch)
    confirm_solo(policy, state)
    policy.active_target, policy.active_target_selector = "the large orc", "#23798"
    policy.fastwalk_attack_started = policy.combat_active = state.in_combat = True
    state.enemies = [[dict(name="the large orc", isnpc="4005", level="6", hp="70", maxhp="84")]]
    state.position = 6
    policy.after_command(BotDecision("kill #23798", "player opens solo"))
    assert policy._required_familiar_loss_decision(state) is None
    clock[0] = .5
    policy.observe_text("Your pierce hits the large orc.\n")
    handled, decision = policy._source_pair_combat_decision(state)
    assert handled and (decision is None or decision.command != "flee")
    state.enemies[0][0]["level"] = "7"
    handled, decision = policy._source_pair_combat_decision(state)
    assert handled and decision.command == "flee"


@pytest.mark.parametrize("boundary", ["connection", "movement", "runtime", "emergency"])
def test_standby_does_not_restore_ownership_or_block_emergency_return(monkeypatch, boundary):
    policy, state, _ = solo_fixture(monkeypatch)
    confirm_solo(policy, state)
    if boundary == "connection":
        policy.on_connection_closed()
        assert policy.solo_consider_identity is None
    elif boundary == "movement":
        policy.after_command(BotDecision("north", "travel"))
        state.room_vnum = "4022"
    elif boundary == "runtime":
        policy.runtime_boundary_requested = True
    else:
        policy.fastwalk_emergency_recall_pending = True
    assert policy._familiar_standby_return_decision(state) == (False, None)
    assert policy.familiar_standby is None


@pytest.mark.parametrize("reply", [
    "The large orc is no match for you.\n", "The perfect match!\n",
    "Someone says 'The large orc looks like an easy kill.'\n",
    "The ordinary orc looks like an easy kill.\n",
])
def test_solo_consider_requires_exact_source_subject_and_level_band(monkeypatch, reply):
    policy, state, _ = solo_fixture(monkeypatch)
    policy.after_command(BotDecision("consider #23798", "new consider"))
    policy.observe_text(reply)
    assert policy.solo_consider_identity is None
    assert solo_decision(policy, state) == (False, None)


def test_fragmented_consider_and_companion_replies(monkeypatch):
    policy, state, _ = solo_fixture(monkeypatch)
    policy.after_command(BotDecision("consider #23798", "new consider"))
    policy.observe_text("The large orc looks like an ea")
    policy.observe_text("sy kill.\n")
    assert policy.solo_consider_identity is not None
    _, decision = solo_decision(policy, state)
    policy.after_command(decision)
    policy.observe_text("The pony sle")
    policy.observe_text("eps.\nOk.\n")
    assert policy._considered_solo_ready(state)


def test_easy_consider_accepts_appended_health_comparison(monkeypatch):
    policy, state, _ = solo_fixture(monkeypatch)
    policy.consider_viable = None
    policy.after_command(BotDecision("consider #23798", "fresh exact consider"))
    policy.observe_text(
        "The large orc looks like an easy kill. Also, you are a teensy bit "
        "healthier than he.\n"
    )

    assert policy.solo_consider_identity is not None
    handled, decision = solo_decision(policy, state)
    assert handled and decision.command == "order #23800 sleep"


def test_standby_deadline_does_not_accept_late_success_or_retry_silence():
    standby = FamiliarStandby("#12", "4024")
    assert standby.command(wake=False, now=0) == "order #12 sleep"
    assert standby.command(wake=False, now=1) is None
    standby.observe("The pony sleeps.\n", now=5)
    assert standby.failure and standby.stage == "sleeping"
    assert standby.command(wake=False, now=6) is None


def test_source_solo_budget_prices_highest_easy_load_not_nominal_level():
    world = _world()
    world.mobiles[1] = replace(world.mobiles[1], level=7)
    budget = source_solo_budget(
        world, 1, character_level=8, hp=113, max_hp=113, mana=224, max_mana=324,
        output=SourceCombatOutput("chill touch", 18, 23, 28, "mana", 25, 18),
    )
    assert budget.allowed and budget.level_ceiling == 6 and budget.target_hp_ceiling == 84
