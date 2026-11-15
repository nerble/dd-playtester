import pytest

from dd4tester.campaign import CampaignRunner, STANCE_COMBAT, STANCE_RECOVERY


@pytest.mark.parametrize("preferred,alternate", [
    (STANCE_COMBAT, STANCE_RECOVERY), (STANCE_RECOVERY, STANCE_COMBAT),
])
def test_empty_preferred_gear_search_checks_other_mode_once(monkeypatch, preferred, alternate):
    runner = CampaignRunner.__new__(CampaignRunner)
    state = {"level": 46, "room_vnum": "3054"}
    calls = []
    placement = object()

    def select(actual_state, *, preferred_stance=None):
        assert actual_state is state
        calls.append(preferred_stance)
        runner._selected_source_gear_stance = preferred_stance or preferred
        return placement if preferred_stance == alternate else None

    monkeypatch.setattr(runner, "_select_source_gear_placement_for_stance", select)
    assert runner._select_source_gear_placement(state) is placement
    assert calls == [None, alternate]
    assert runner._selected_source_gear_stance == alternate


def test_selected_preferred_upgrade_keeps_its_turn(monkeypatch):
    runner = CampaignRunner.__new__(CampaignRunner)
    calls = []
    placement = object()

    def select(state, *, preferred_stance=None):
        calls.append(preferred_stance)
        runner._selected_source_gear_stance = STANCE_COMBAT
        return placement

    monkeypatch.setattr(runner, "_select_source_gear_placement_for_stance", select)
    assert runner._select_source_gear_placement({}) is placement
    assert calls == [None]


def test_both_empty_modes_end_without_a_third_search(monkeypatch):
    runner = CampaignRunner.__new__(CampaignRunner)
    calls = []

    def select(state, *, preferred_stance=None):
        calls.append(preferred_stance)
        runner._selected_source_gear_stance = preferred_stance or STANCE_RECOVERY
        return None

    monkeypatch.setattr(runner, "_select_source_gear_placement_for_stance", select)
    assert runner._select_source_gear_placement({}) is None
    assert calls == [None, STANCE_COMBAT]
