from types import SimpleNamespace

import pytest

from dd4tester.character import CharacterSpec
from dd4tester.self_buffs import HealerBuffPreparation, ProtectionSpell, learned_protection_spell
from dd4tester.starter import FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


@pytest.mark.parametrize("base,subclass,percent,allowed", [
    ("warrior", "knight", 99, True), ("mage", None, 30, True),
    ("cleric", None, 60, True), ("warrior", None, 99, False),
    ("thief", None, 99, False), ("mage", "knight", 99, False),
    ("warrior", "knight", True, False), ("warrior", "knight", 0, False),
])
def test_only_audited_paths_and_observed_proficiency_authorize_armor(base, subclass, percent, allowed):
    assert bool(learned_protection_spell(base, subclass, {"armor": percent})) is allowed


def step(session, now=0, **changes):
    args = dict(scope=("pilot", "mage", None, 46, "boot", "3054"),
                active=False, affect_revision=1, mana=100, max_mana=100, now=now)
    args.update(changes)
    return session.next_command(ProtectionSpell("armor", 99), **args)


def test_cast_requires_exact_reply_fresh_affect_and_source_wait():
    session = HealerBuffPreparation()
    assert step(session) == (True, "cast 'armor' self")
    session.observe("The healer utters a word.\n", now=.1)
    assert step(session, .2, active=True, affect_revision=2) == (True, None)
    session.observe("You feel someone pro", now=.3)
    assert not session.acknowledged
    session.observe("tecting you.\n", now=.4)
    assert step(session, .6, active=True, affect_revision=2) == (True, None)
    session.observe("The healer smiles.\n", now=.8)
    assert session.ready_at == .9
    assert step(session, 1, active=True, affect_revision=2) == (False, None)
    assert session.status == "confirmed"
    assert session.attempts == 1
    assert step(session, 2) == (False, None)


def test_no_refresh_of_active_protection_and_no_stale_affect_credit():
    session = HealerBuffPreparation()
    assert step(session, active=True, affect_revision=0) == (True, "affects")
    assert step(session, 1, active=True, affect_revision=1) == (False, None)
    assert session.status == "active" and session.attempts == 0


def test_one_confirmation_probe_cannot_loop_or_invent_a_buff():
    session = HealerBuffPreparation()
    step(session)
    session.observe("You feel someone protecting you.\n", now=.1)
    assert step(session, 1) == (True, "affects")
    assert step(session, 2, affect_revision=2) == (False, None)
    assert session.status == "failed" and session.attempts == 1


@pytest.mark.parametrize("failure", ["reply", "scope", "refused", "mana"])
def test_deadlines_scope_refusals_and_mana_reserve_do_not_stall_hunting(failure):
    session = HealerBuffPreparation()
    if failure == "mana":
        assert step(session, mana=50) == (False, None)
        assert session.status == "skipped"
        return
    step(session)
    if failure == "reply":
        result = step(session, 12)
    elif failure == "scope":
        result = step(session, 1, scope=("other-room",))
    else:
        session.observe("You don't have enough mana.\n", now=.1)
        result = step(session, 1)
    assert result == (False, None)
    assert session.status == "failed"
    assert session.attempts == 1


def test_departure_controller_owns_cast_and_cancels_if_moved(monkeypatch):
    spec = CharacterSpec.from_mapping({"name": "Tester", "race": "dwarf", "gender": "male",
                                       "class": "warrior", "subclass": "knight"})
    policy = StarterPolicy(spec, "password", fastwalk_hunt_stops=(FieldHuntStop((), "target"),))
    policy.fastwalk_route = SimpleNamespace()
    policy.in_world = policy.prompt_ready = True
    policy.world_boot_id = "boot"
    policy.known_skill_levels["armor"] = 99
    policy.learned_flight_affect_revision = 1
    state = CharacterState(level=46, subclass="knight", room_vnum="3054", room_flags=["healing"],
                           position=7, hp=100, max_hp=100, mana=100, max_mana=100)
    decision = policy._fastwalk_research_decision(state)
    assert decision.command == "cast 'armor' self"
    policy.prompt_ready = False
    policy._recovery_session.self_buffs.deadline = 1
    monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: 20)
    assert policy._healer_buff_preparation_decision(state) == (True, None)
    assert policy._recovery_session.self_buffs.status == "failed"
    state.room_vnum = "3001"
    assert policy._healer_buff_preparation_decision(state) == (False, None)
    assert policy._recovery_session.self_buffs.status == "failed"
