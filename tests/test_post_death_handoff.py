from test_combat_timing import policy_fixture


def test_post_death_healer_handoff_does_not_wake_before_resource_recovery(monkeypatch):
    policy, state, clock = policy_fixture(monkeypatch)
    policy.combat_active = state.in_combat = False
    policy.active_target = None
    state.enemies = []
    state.room_vnum = "3054"
    state.position = 7
    state.hp, state.mana = 10, 19
    policy.current_room = "3054"
    policy.return_home = True
    policy.purgatory_portal_entered = True
    policy.purgatory_gear_restore_step = 3
    decision = policy._purgatory_recovery_decision(state)
    assert decision.command == "sleep"
    assert policy.purgatory_recovery_complete and policy.waiting_for_heal
    state.position = 4
    for _ in range(4):
        assert policy._purgatory_recovery_decision(state) is None
    normal = policy._recovery_decision(state)
    assert normal is None or normal.command == "score"


def test_already_sleeping_after_gear_audit_hands_off_without_extra_command(monkeypatch):
    policy, state, clock = policy_fixture(monkeypatch)
    policy.purgatory_portal_entered = True
    policy.purgatory_gear_restore_step = 3
    state.room_vnum = "3054"
    state.position = 4
    state.hp, state.mana = 10, 19
    assert policy._purgatory_recovery_decision(state) is None
    assert policy.purgatory_recovery_complete and policy.waiting_for_heal
