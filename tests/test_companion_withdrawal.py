from dataclasses import replace
from pathlib import Path

import pytest

from dd4tester.companions import (
    FamiliarPreparation, FamiliarWithdrawal, companion_finishing_blow,
)
from dd4tester.hunt_candidates import AFF_CHARM
from test_combat_timing import policy_fixture


def test_run_12749_ok_is_not_departure_and_allows_one_confirmed_retry():
    withdrawal = FamiliarWithdrawal(selector="#23691")
    assert withdrawal.next_command(now=0) == "order #23691 flee Fear"
    withdrawal.observe("Ok.\n", now=3.2)
    assert withdrawal.pending and not withdrawal.confirmed
    assert withdrawal.next_command(now=3.2) == "order #23691 flee Fear"
    withdrawal.observe("The pony has fled!\nOk.\n", now=3.8)
    assert withdrawal.confirmed and not withdrawal.pending
    assert withdrawal.next_command(now=4) is None
    assert withdrawal.evidence() == {
        "attempts": 2, "confirmed": True, "failure": None,
        "control": "departure", "sleeping_attempts": 0,
    }


@pytest.mark.parametrize("reply", [
    "The pony grazes Katrina the Shepherd.\n", "Ok.\n", "The guard has fled!\n",
    "Someone says 'The pony has fled!'\n", "<113/113 hits 224/324 mana 197/220 move> ",
])
def test_only_exact_departure_confirms_withdrawal(reply):
    withdrawal = FamiliarWithdrawal(selector="#1")
    withdrawal.next_command(now=0)
    withdrawal.observe(reply, now=1)
    assert not withdrawal.confirmed


def test_fragmented_departure_before_order_ack_does_not_repeat():
    withdrawal = FamiliarWithdrawal(selector="#1")
    withdrawal.next_command(now=0)
    withdrawal.observe("The pony has fl", now=1)
    assert withdrawal.next_command(now=1.05) is None
    withdrawal.observe("ed!\nOk.\n", now=1.08)
    assert withdrawal.next_command(now=1.5) is None
    assert withdrawal.confirmed and withdrawal.attempts == 1


def test_silence_stops_after_deadline_without_retry_or_claiming_success():
    withdrawal = FamiliarWithdrawal(selector="#1")
    withdrawal.next_command(now=0)
    assert withdrawal.next_command(now=4.9) is None
    assert withdrawal.next_command(now=5) is None
    assert not withdrawal.pending and not withdrawal.confirmed
    assert withdrawal.attempts == 1 and "deadline" in withdrawal.failure


def test_acknowledged_unsuccessful_orders_are_limited_to_three():
    withdrawal = FamiliarWithdrawal(selector="#1")
    for attempt in range(3):
        assert withdrawal.next_command(now=attempt) == "order #1 flee"
        withdrawal.observe("Ok.\n", now=attempt + .1)
    assert withdrawal.next_command(now=3) is None
    assert not withdrawal.pending and not withdrawal.confirmed
    assert withdrawal.attempts == 3 and "three" in withdrawal.failure


@pytest.mark.parametrize("selector", [None, "pony", "#1 flee", ""])
def test_no_withdrawal_without_exact_session_identity(selector):
    withdrawal = FamiliarWithdrawal(selector=selector)
    assert withdrawal.next_command(now=0) is None
    assert withdrawal.attempts == 0


def test_live_replay_prioritizes_retry_over_cast_and_requires_departure(monkeypatch):
    policy, state, clock = policy_fixture(monkeypatch)
    policy.familiar_active = True
    policy.familiar_preparation.selector = "#23691"
    first = policy._between_round_combat_decision(state)
    assert first.command == "order #23691 flee"
    assert policy.familiar_active
    clock[0] = 3.2
    policy.observe_text("Ok.\n<113/113 hits 224/324 mana 197/220 move [Ultima]> ")
    assert policy._between_round_combat_decision(state).command == "order #23691 flee"
    assert policy.familiar_active and policy.familiar_withdrawal.attempts == 2
    clock[0] = 3.8
    policy.observe_text("\nThe pony has fled!\nOk.\n<113/113 hits 224/324 mana 197/220 move [Ultima]> ")
    assert not policy.familiar_active and policy.familiar_withdrawal.confirmed
    assert policy._between_round_combat_decision(state).command == "cast 'chill touch' #22916"


def test_lost_companion_cannot_leave_withdrawal_pending_forever(monkeypatch):
    policy, state, clock = policy_fixture(monkeypatch)
    policy.familiar_active = True
    policy.familiar_preparation.selector = "#23691"
    policy._between_round_combat_decision(state)
    policy.familiar_active = False
    clock[0] = 11
    policy._between_round_combat_decision(state)
    assert not policy.familiar_withdrawal.pending
    assert not policy.familiar_withdrawal.confirmed


def test_source_order_ack_follows_synchronous_interpret_without_player_wait():
    text = Path("runs/dd4-source/server/src/act_comm.c").read_text(encoding="utf-8")
    order = text.split("void do_order(", 1)[1].split("void do_group(", 1)[0]
    assert order.index("interpret(och, argument)") < order.index('send_to_char("Ok.')
    assert "WAIT_STATE" not in order


def test_summoned_familiar_source_handles_charm_and_fear_override():
    db = Path("runs/dd4-source/server/src/db.c").read_text(encoding="utf-8")
    magic = Path("runs/dd4-source/server/src/magic.c").read_text(encoding="utf-8")
    summon = magic.split("void spell_summon_familiar(", 1)[1].split(
        "void spell_summon_demon(", 1
    )[0]
    assert "REMOVE_BIT(pMobIndex->affected_by, AFF_CHARM);" in db
    assert "add_follower(victim, ch);" in summon
    assert "affect_to_char" not in summon

    text = Path("runs/dd4-source/server/src/fight.c").read_text(encoding="utf-8")
    flee = text.split("void do_flee(", 1)[1].split("void do_bomb(", 1)[0]
    assert 'number_bits(1) && str_cmp("Fear", argument)' in flee
    withdrawal = FamiliarWithdrawal(selector="#1")
    assert withdrawal.next_command(now=0) == "order #1 flee Fear"
    withdrawal.observe("The pony leaves west.\nThe pony has fled!\nOk.\n", now=1)
    assert withdrawal.confirmed


def test_summoned_familiar_runtime_ignores_prototype_charm_for_withdrawal(
    monkeypatch,
):
    policy, _state, _clock = policy_fixture(monkeypatch)
    pony = policy.source_world.mobiles[19900]
    policy.source_world.mobiles[19900] = replace(
        pony,
        affected_flags=AFF_CHARM,
    )

    assert policy.source_world.mobiles[19900].affected_flags & AFF_CHARM
    assert not policy._summoned_familiar_requires_in_place_sleep()


@pytest.mark.parametrize("attack,expected", [
    ("The pony grazes Katrina the Shepherd.", True),
    ("Your pierce grazes Katrina the Shepherd.", False),
    ("Someone says 'The pony grazes Katrina the Shepherd.'", False),
    ("The pony misses Katrina the Shepherd.", False),
    ("The pony grazes another target.", False),
])
def test_only_actual_companion_damage_death_pair_identifies_no_xp_finish(attack, expected):
    assert companion_finishing_blow(
        attack + "\nKatrina the Shepherd is DEAD!!\n",
        target="Katrina the Shepherd",
    ) is expected


def test_run_12749_companion_kill_keeps_encounter_but_not_objective_xp(monkeypatch):
    policy, state, clock = policy_fixture(monkeypatch)
    policy.familiar_active = True
    policy.familiar_preparation.selector = "#23691"
    policy.observe_text("The pony grazes Katrina the Shepherd.\n")
    policy.observe_text("Katrina the Shepherd is DEAD!!\n")
    assert policy.completed_kills[-1]["xp_gained"] == 0
    assert policy.completed_kills[-1]["objective_eligible"] is False
    assert policy.objective_kills == []


def test_charmed_companion_requires_positive_sleep_not_departure():
    withdrawal = FamiliarWithdrawal(selector="#1", settle_in_place=True)
    assert withdrawal.next_command(now=0) == "order #1 flee Fear"
    withdrawal.observe("Ok. The bard has quite a few wounds.\n", now=3)
    assert withdrawal.next_command(now=3) == "order #1 sleep"
    assert not withdrawal.confirmed
    withdrawal.observe("The pony sleeps.\nOk.\n", now=3.5)
    assert withdrawal.confirmed and not withdrawal.pending
    assert withdrawal.next_command(now=4) is None
    assert withdrawal.evidence()["sleeping_attempts"] == 1


def test_optional_familiar_handoff_skips_endpoint_with_only_no_mob_exits(monkeypatch):
    from dataclasses import replace

    from dd4tester.hunt_candidates import ExitSource, RoomSource, ROOM_NO_MOB
    from dd4tester.starter import FieldHuntStop

    policy, state, _clock = policy_fixture(monkeypatch)
    policy.source_world.rooms.update({
        3577: RoomSource(
            3577,
            "The Bard's Table",
            "midennir.are",
            exits={"e": ExitSource("e", 3574, 0, 0)},
        ),
        3574: RoomSource(
            3574,
            "The Woodsman Inn",
            "midennir.are",
            room_flags=ROOM_NO_MOB,
        ),
    })
    stop = replace(
        policy.fastwalk_hunt_stops[0],
        target="Katrina the Shepherd",
        source_reset_room_vnum="3577",
        require_familiar=False,
        familiar_withdraw_before_opener=True,
    )
    policy.fastwalk_hunt_stops = (stop,)
    policy.consider_viable = True
    policy.combat_active = False
    policy.fastwalk_attack_started = False
    policy.current_room = "3577"
    state.room_vnum = "3577"
    state.position = 7
    state.in_combat = False

    assert policy._familiar_precombat_decision(
        state,
        target=stop.target,
        allow_start=True,
    ) is None
    assert policy.familiar_unavailable
    assert not policy.familiar_active
    assert not policy.familiar_preparation.summoned


def test_familiar_handoff_rejects_any_random_exit_with_a_source_attacker(monkeypatch):
    from dd4tester.hunt_candidates import (
        ExitSource,
        MobReset,
        MobileSource,
        RoomSource,
    )

    policy, state, _clock = policy_fixture(monkeypatch)
    policy.source_world.rooms.update({
        1570: RoomSource(
            1570,
            "Gnome Treasury",
            "gnome.are",
            exits={
                "north": ExitSource("north", 1571, 0, 0),
                "east": ExitSource("east", 1572, 0, 0),
            },
        ),
        1571: RoomSource(1571, "Guarded Room", "gnome.are"),
        1572: RoomSource(1572, "Quiet Passage", "gnome.are"),
    })
    policy.source_world.mobiles[1517] = MobileSource(
        1517,
        "hobgoblin soldier hobgoblin",
        "a hobgoblin soldier",
        8,
        1 << 5,
        0,
        "gnome.are",
    )
    policy.source_world.mob_resets.append(MobReset(1517, 1571, 6, ()))
    policy.source_mobile_vnums_by_target_room = {
        "hobgoblin soldier": {"1571": (1517,)},
    }
    stop = replace(
        policy.fastwalk_hunt_stops[0],
        target="the treasurer",
        source_reset_room_vnum="1570",
        require_familiar=True,
    )

    assert not policy._source_familiar_withdrawal_room_available(stop, state)


def test_familiar_handoff_accepts_parsed_mobile_without_specials(monkeypatch):
    from dataclasses import replace

    from dd4tester.hunt_candidates import (
        ExitSource,
        MobReset,
        MobileSource,
        RoomSource,
    )

    policy, state, _clock = policy_fixture(monkeypatch)
    policy.source_world.rooms.update({
        1570: RoomSource(
            1570,
            "Gnome Treasury",
            "gnome.are",
            exits={
                "north": ExitSource("north", 1571, 0, 0),
                "east": ExitSource("east", 1572, 0, 0),
            },
        ),
        1571: RoomSource(1571, "Quiet Room", "gnome.are"),
        1572: RoomSource(1572, "Quiet Passage", "gnome.are"),
    })
    policy.source_world.mobiles[1500] = MobileSource(
        1500,
        "a sleepy resident",
        "a sleepy resident",
        1,
        0,
        0,
        "gnome.are",
    )
    policy.source_world.mob_resets.append(MobReset(1500, 1571, 1, ()))
    stop = replace(
        policy.fastwalk_hunt_stops[0],
        target="the treasurer",
        source_reset_room_vnum="1570",
        require_familiar=True,
    )

    assert policy._source_familiar_withdrawal_room_available(stop, state)


def test_failed_familiar_handoff_tries_recall_once_in_combat(monkeypatch):
    policy, state, _clock = policy_fixture(monkeypatch)
    policy.familiar_disengagement_attempted = True
    policy.familiar_withdrawal.failure = "withdrawal was not confirmed"

    first = policy._familiar_disengagement_decision(state, now=10)
    assert first is not None and first.command == "recall"

    policy.after_command(first)
    assert policy._familiar_disengagement_decision(state, now=11) is None


def test_completed_familiar_failure_flee_hands_off_to_return(monkeypatch):
    policy, state, _clock = policy_fixture(monkeypatch)
    policy.familiar_disengagement_attempted = True
    policy.familiar_withdrawal.failure = "withdrawal was not confirmed"
    policy.familiar_failure_return_started = True
    policy.fastwalk_emergency_recall_pending = True
    policy.flee_succeeded = True
    state.in_combat = False
    state.position = 7

    decision = policy._tutorial_decision(state)

    assert decision is not None and decision.command == "recall"
    assert policy.return_home is True
    assert policy.fastwalk_emergency_recall_pending is False


def test_no_xp_familiar_withdraws_after_low_hp_opening_hit_before_player_opener(monkeypatch):
    policy, state, clock = policy_fixture(monkeypatch)
    policy.fastwalk_hunt_stops = (
        replace(policy.fastwalk_hunt_stops[0], require_familiar=False),
    )
    policy.source_world.mobiles[19900] = replace(
        policy.source_world.mobiles[19900], affected_flags=1 << 18,
    )
    policy.familiar_preparation = FamiliarPreparation(
        stage="ready", selector="#23700", summoned=True, grouped=True,
        order_confirmed=True, order_pending=True,
    )
    policy.familiar_active = True
    policy.familiar_precombat_step = "attack"
    policy.familiar_precombat_target = state.enemies[0][0]["name"]
    policy.familiar_ordered_target = policy.familiar_precombat_target
    policy.familiar_order_room = state.room_vnum
    policy.familiar_preparation_room = state.room_vnum
    policy.fastwalk_attack_started = False
    policy.combat_active = False
    policy.room_target_selector_descriptions[state.room_vnum] = {
        "#23700": policy._staged_familiar_description(),
    }
    state.subclass = "warlock"
    state.in_combat = False
    state.position = 7
    state.enemies[0][0].update(hp="30", maxhp="50")

    flee = policy._familiar_precombat_decision(state)
    assert flee.command == "order #23700 flee Fear"
    assert not policy.fastwalk_attack_started

    policy.observe_text("Ok.\n<prompt>")
    sleep = policy._familiar_precombat_decision(state)
    assert sleep is not None and sleep.command == "order #23700 sleep"
    policy.observe_text("Ok.\n<prompt>")
    assert policy.familiar_active and not policy.familiar_withdrawal.confirmed
    policy.observe_text("The pony sleeps.\n<prompt>")
    opener = policy._familiar_precombat_decision(state)
    assert opener is not None
    assert not opener.command.startswith("order #23700")
    assert policy.fastwalk_attack_started


def test_failed_npc_flee_and_sleep_pair_retries_but_never_more_than_three_pairs():
    withdrawal = FamiliarWithdrawal(selector="#1", settle_in_place=True)
    for index in range(3):
        now = index * 2
        assert withdrawal.next_command(now=now) == "order #1 flee Fear"
        withdrawal.observe("Ok.\n", now=now + .5)
        assert withdrawal.next_command(now=now + .5) == "order #1 sleep"
        withdrawal.observe("Ok.\n", now=now + 1)
    assert withdrawal.next_command(now=6) is None
    assert not withdrawal.confirmed and not withdrawal.pending
    assert withdrawal.attempts == withdrawal.sleeping_attempts == 3


def test_sleep_without_pending_sleep_order_is_not_confirmation():
    withdrawal = FamiliarWithdrawal(selector="#1", settle_in_place=True)
    withdrawal.next_command(now=0)
    withdrawal.observe("The pony sleeps.\n", now=1)
    assert not withdrawal.confirmed


def test_runtime_source_charmed_pony_requires_positive_sleep(monkeypatch):
    from dataclasses import replace
    policy, state, clock = policy_fixture(monkeypatch)
    policy.source_world.mobiles[19900] = replace(
        policy.source_world.mobiles[19900], affected_flags=1 << 18,
    )
    policy.familiar_active = True
    policy.familiar_preparation.selector = "#23700"
    assert policy._between_round_combat_decision(state).command == "order #23700 flee Fear"
    assert policy.familiar_withdrawal.settle_in_place
    clock[0] = 3
    policy.observe_text("Ok.\n<prompt>")
    assert policy._between_round_combat_decision(state).command == (
        "order #23700 sleep"
    )
    policy.observe_text("Ok.\n<prompt>")
    assert policy.familiar_active and not policy.familiar_withdrawal.confirmed
    policy.observe_text("The pony sleeps.\n<prompt>")
    assert not policy.familiar_active
    assert policy._between_round_combat_decision(state).command == "cast 'chill touch' #22916"


def test_source_charm_blocks_departure_and_sleep_requires_no_fighting():
    text = Path("runs/dd4-source/server/src/act_move.c").read_text(encoding="utf-8")
    assert "IS_AFFECTED(ch, AFF_CHARM) && ch->master && in_room == ch->master->in_room" in text
    sleep = text.split("void do_sleep(", 1)[1].split("void ", 1)[0]
    assert sleep.index("if (ch->fighting)") < sleep.index("ch->position = POS_SLEEPING")
    assert 'act("$n sleeps."' in sleep
    fight = Path("runs/dd4-source/server/src/fight.c").read_text(encoding="utf-8")
    flee = fight.split("void do_flee(", 1)[1].split("void do_bomb(", 1)[0]
    assert flee.index("stop_fighting(ch, TRUE)") < flee.index("move_char(ch, door)")


def test_companion_kill_uses_death_name_even_when_room_alias_differs(monkeypatch):
    policy, state, clock = policy_fixture(monkeypatch)
    policy.active_target = "small centipede"
    policy.familiar_preparation.selector = "#1"
    policy.observe_text("The pony grazes the centipede.\nThe centipede is DEAD!!\n")
    assert policy.completed_kills[-1]["objective_eligible"] is False
    assert policy.completed_kills[-1]["xp_gained"] == 0
