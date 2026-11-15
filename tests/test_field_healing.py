import pytest

from dd4tester.field_healing import FieldHealingSession


SCOPE = ("100", 46, "boot-1", 0, "source-ranked-hunt-test-1-100-46", 1, "100")


def advance(session, now, **changes):
    values = dict(sequence=2, hp=600, max_hp=1000, minimum_ratio=.85,
                  mana=500, max_mana=600, spell="cure serious", mana_cost=15,
                  room_allowed=True)
    values.update(changes)
    return session.advance(SCOPE, now=now, **values)


def test_field_healing_requires_fresh_room_and_exact_reply_plus_source_lag():
    session = FieldHealingSession()
    assert session.begin(SCOPE, sequence=1, hp=600, now=0)
    assert advance(session, 0, sequence=1) == (True, None)
    assert advance(session, .1) == (True, "cast 'cure serious'")
    session.window.observe("You are no longer protected by sanctuary.\n", now=.2)
    assert advance(session, 3.5) == (True, None)
    session.window.observe("You feel better!\n", now=3.6)
    assert advance(session, 3.7, hp=900) == (True, None)
    assert advance(session, 7, hp=900) == (False, None)
    assert session.records[-1]["outcome"] == "ready"
    assert session.records[-1]["attempts"] == 1


@pytest.mark.parametrize("case", ["room", "mana", "no_reply", "deadline"])
def test_failed_field_preparation_is_bounded_not_combat_permission(case):
    session = FieldHealingSession()
    session.begin(SCOPE, sequence=1, hp=600, now=0)
    if case == "room":
        result = advance(session, 1, room_allowed=False)
    elif case == "mana":
        result = advance(session, 1, mana=180)
    elif case == "no_reply":
        assert advance(session, 1)[1] == "cast 'cure serious'"
        result = advance(session, 11.1)
    else:
        result = advance(session, 45)
    assert result == (False, None)
    assert session.closed
    assert not session.begin(SCOPE, sequence=3, hp=600, now=50)


def test_repeated_failures_spend_a_fixed_attempt_budget():
    session = FieldHealingSession()
    session.begin(SCOPE, sequence=1, hp=600, now=0)
    now = 1.0
    for _ in range(8):
        assert advance(session, now)[1] == "cast 'cure serious'"
        session.window.observe("You fail to correctly recite the spell!\n", now=now + .1)
        now += 3.5
    assert advance(session, now) == (False, None)
    assert session.attempts == 8
    assert session.records[-1]["outcome"] == "attempt_or_mana_limit"


def test_another_scope_does_not_reuse_a_pending_heal():
    session = FieldHealingSession()
    session.begin(SCOPE, sequence=1, hp=600, now=0)
    advance(session, 1)
    assert not session.begin(("101", *SCOPE[1:]), sequence=1, hp=600, now=2)


def test_source_field_healing_does_not_advance_the_hunt_before_heal_lag(monkeypatch):
    from dd4tester.character import CharacterSpec
    from dd4tester.hunt_candidates import MobileSource, RoomSource, WorldSource
    from dd4tester.starter import FieldHuntStop, StarterPolicy
    from dd4tester.state import CharacterState

    clock = [0.0]
    monkeypatch.setattr("dd4tester.starter.time.monotonic", lambda: clock[0])
    policy = StarterPolicy(CharacterSpec.from_mapping({
        "name": "Tester", "race": "human", "gender": "male", "class": "warrior",
    }), "password", source_world=WorldSource(
        rooms={100: RoomSource(100, "Empty room", "test.are")},
        mobiles={1: MobileSource(1, "guard", "a guard", 45, 0, 0, "test.are")},
    ))
    policy.known_skills.add("cure serious")
    policy.known_skill_levels["cure serious"] = 49
    stop = FieldHuntStop((), "a guard", source_mobile_vnum=1,
                         source_policy_id=SCOPE[4], source_reset_room_vnum="101",
                         minimum_health_ratio=.85)
    state = CharacterState(level=46, room_vnum="100", hp=700, max_hp=1000,
                           mana=500, max_mana=600, position=7)
    handled, decision = policy._field_readiness_healing_decision(state, stop)
    assert handled and decision.command == "look"
    state.room_listing = {"room_vnum": "100", "sequence": 1, "render_complete": True,
                          "targeted_lines": [], "unkeyed_lines": []}
    handled, decision = policy._field_readiness_healing_decision(state, stop)
    assert handled and decision.command == "cast 'cure serious'"
    policy._recovery_session.field_healing.window.observe("You feel better!\n", now=.1)
    state.hp = 900
    clock[0] = .2
    assert policy._field_readiness_healing_decision(state, stop) == (True, None)
    clock[0] = 4
    assert policy._field_readiness_healing_decision(state, stop) == (False, None)
    assert policy.fastwalk_hunt_stop_index == 0
