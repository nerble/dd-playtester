from dataclasses import replace
from types import SimpleNamespace

import pytest

import dd4tester.campaign as campaign


@pytest.mark.parametrize("case,commit", [
    ("winner", True), ("none", False), ("mismatch", False),
    ("circuit", False), ("wounded", False), ("quest", False), ("stored", True),
    ("foreign-stored", False), ("provisional", True), ("foreign-provisional", False),
])
def test_final_measured_hunt_comparison_precedes_optional_gear_and_owns_only_winner(monkeypatch, case, commit):
    runner = campaign.CampaignRunner.__new__(campaign.CampaignRunner)
    original = SimpleNamespace(mobile_vnum=1)
    winner = SimpleNamespace(mobile_vnum=2)
    runner._selected_source_ranked_candidate = original
    runner._selected_source_ranked_circuit = (original,) if case == "circuit" else ()
    runner._source_ranked_protection_retry_selected_policy_id = "original-retry"
    runner._campaign_policy_storage = object()
    runner._emit_progress = lambda _: None
    selected = replace(campaign._SOURCE_RANKED_HUNT_POLICY, policy_id="original")
    measured = replace(selected, policy_id="measured")
    if case in {"provisional", "foreign-provisional"}:
        selected = campaign._SOURCE_RANKED_HUNT_POLICY
    calls = []

    def compare(state, candidate):
        calls.append(candidate)
        state["winner-only"] = True
        runner._selected_source_ranked_candidate = winner
        runner._selected_source_ranked_circuit = ()
        runner._source_ranked_protection_retry_selected_policy_id = "winner-retry"
        return None if case == "none" else measured

    runner._productive_registered_hunt_policy = compare
    monkeypatch.setattr(campaign, "_source_ranked_policy_id",
                        lambda candidate, **_kw: (
                            "wrong" if case == "foreign-stored" else "original")
                        if candidate is original else ("wrong" if case == "mismatch" else "measured"))
    state = {"level": 46, "world_boot_id": "boot", "room_vnum": "3054",
             "hp": 1000, "max_hp": 1000, "mana": 500, "max_mana": 500,
             "move": 500, "max_move": 500, "quest_status": {"active": 0, "total_points": 18}}
    if case == "wounded":
        state["hp"] = 200
    elif case == "quest":
        state["quest_status"]["active"] = 1
    if case in {"stored", "foreign-stored", "provisional", "foreign-provisional"}:
        runner._selected_source_ranked_candidate = None
        state[campaign._SOURCE_RANKED_CANDIDATE_KEY] = {
            "source_revision": "source", "policy_id": "foreign" if case == "foreign-provisional" else "original"}
        monkeypatch.setattr(campaign, "_source_ranked_candidate_from_record", lambda *_a, **_kw: original)
    result = runner._compare_source_hunt_before_gear(state, selected)
    assert ("winner-only" in state) is commit
    assert result.policy_id == ("measured" if commit else selected.policy_id)
    assert runner._selected_source_ranked_candidate is (
        winner if commit else None if case in {"foreign-stored", "foreign-provisional"} else original)
    assert runner._source_ranked_protection_retry_selected_policy_id == (
        "winner-retry" if commit else "original-retry")
    assert bool(calls) is (case not in {"circuit", "wounded", "quest", "foreign-stored", "foreign-provisional"})
    if case == "circuit":
        assert runner._selected_source_ranked_circuit == (original,)
