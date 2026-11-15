from dataclasses import replace

import pytest

import dd4tester.campaign as campaign
from dd4tester.hunt_candidates import (
    ACT_SENTINEL, HuntCandidate, MobileSource, MobReset,
    RoomSource, WorldSource,
)


def probe_plan():
    runner = campaign.CampaignRunner.__new__(campaign.CampaignRunner)
    runner._source_world = WorldSource(
        mobiles={1: MobileSource(1, "target", "a target", 45, ACT_SENTINEL, 0, "test.are")},
        rooms={100: RoomSource(100, "Target room", "test.are")},
        mob_resets=[MobReset(1, 100, 1)],
    )
    runner._selected_source_ranked_candidate = None
    runner._selected_source_ranked_circuit = ()
    runner._emit_progress = lambda _message: None
    state = {
        "level": 45, "room_vnum": "3054", "room_flags": ["safe", "healing"],
        "hp": 1000, "max_hp": 1000, "mana": 500, "max_mana": 500,
        "move": 500, "max_move": 500, campaign._SOURCE_REVISION_KEY: "source-1",
        "inventory": [[{"short_desc": "a big pot pie"}, {"short_desc": "a buffalo water skin"}]],
    }
    candidate = HuntCandidate(
        "caution", 1, "test.are", 1, "a target", "target", 45,
        100, "Target room", (), 1, 1, 0, (), 0, 0, (),
    )
    policy = replace(campaign._DWARVEN_HOME_CHESS_DWARF_RESEARCH_POLICY,
                     source_mobile_vnums=(1,))
    return runner, state, candidate, policy


@pytest.mark.parametrize("visit", [
    "none", "sale", "flight", "old_hunt", "hunt", "failed_hunt",
    "running_hunt", "unproductive_hunt", "missing_summary", "partial_combat",
    "partial_combat_loss", "sanctuary",
])
def test_acquired_upgrade_keeps_its_xp_turn_through_maintenance(visit):
    observed = {
        "level": 46, "world_boot_id": "boot-1",
        campaign._SOURCE_GEAR_ATTEMPTS_KEY: [{
            "level": 46, "boot_id": "boot-1", "status": "acquired",
            "object_acquired": True, "finished_at": "2026-11-14T11:09:19+00:00",
        }],
    }
    segments = []
    if visit != "none":
        segments = [{
            "phase": {
                "sale": "liquidate-loot", "flight": "buy-flight",
                "sanctuary": "source-ranked-hunt-test-1-100-46-sanctuary-maintenance",
            }.get(visit, "source-ranked-hunt-test-1-100-46"),
            "run_id": 20, "status": "running" if visit == "running_hunt" else (
                "failed" if visit == "failed_hunt" else "success"
            ),
            "started_at": "2026-11-14T11:08:00+00:00" if visit == "old_hunt"
            else "2026-11-14T11:10:00+00:00",
            "finished_at": None if visit == "running_hunt" else "2026-11-14T11:11:00+00:00",
        }]
    class Summaries:
        def get_run_summary(self, run_id):
            assert run_id == 20
            if visit == "missing_summary":
                return None
            return {"outcomes": {
                "safety": "loss" if visit == "partial_combat_loss" else "safe",
            }, "progress": {
                "experience": {"change": -532 if visit == "failed_hunt" else 10},
                "combat_starts": 2 if visit == "partial_combat" else 1,
                "confirmed_kills": [{
                    "xp_gained": 4000 if visit == "hunt" else 10,
                    "objective_eligible": visit == "hunt",
                    "source_policy_id": "source-ranked-hunt-test-1-100-46",
                }],
            }}

    assert campaign._source_gear_upgrade_waiting_for_xp_trip(
        observed, segments, storage=Summaries(),
    ) is (
        visit not in {"hunt", "failed_hunt", "partial_combat", "partial_combat_loss"}
    )


@pytest.mark.parametrize("phase,running,waiting", [
    ("liquidate-loot", False, True),
    ("source-ranked-hunt-test-1-100-46-sanctuary-maintenance", False, True),
    ("source-ranked-hunt-test-1-100-46", True, True),
    ("source-ranked-hunt-test-1-100-46", False, False),
])
def test_failed_optional_gear_detour_gives_ordinary_hunt_a_turn(phase, running, waiting):
    observed = {
        "level": 46, "world_boot_id": "boot-1",
        campaign._SOURCE_GEAR_ATTEMPTS_KEY: [{
            "level": 46, "boot_id": "boot-1", "status": "not_acquired",
            "object_acquired": False, "finished_at": "2026-11-14T11:09:19+00:00",
        }],
    }
    assert campaign._source_gear_upgrade_waiting_for_xp_trip(observed, [])
    segments = [{
        "id": 30, "phase": phase, "run_id": 20,
        "status": "running" if running else "success",
        "started_at": "2026-11-14T11:10:00+00:00",
        "finished_at": None if running else "2026-11-14T11:11:00+00:00",
    }]
    assert campaign._source_gear_upgrade_waiting_for_xp_trip(observed, segments) is waiting


@pytest.mark.parametrize("accepted", [False, True])
def test_registered_probe_uses_exact_normal_selector(monkeypatch, accepted):
    runner, state, candidate, policy = probe_plan()
    identity = campaign._source_ranked_policy_id(candidate, character_level=45)
    calls = []

    def select(projection, **kwargs):
        calls.append(kwargs)
        assert projection is not state
        projection["selection_evidence"] = "selected"
        return candidate if accepted else None

    monkeypatch.setattr(runner, "_select_source_ranked_candidate", select, raising=False)
    result = runner._executable_registered_probe_hunt(state, policy)
    assert calls == [{}]
    if accepted:
        assert result.execution == "source-ranked-hunt"
        assert result.policy_id == identity
        assert state[campaign._SOURCE_RANKED_CANDIDATE_KEY]["mobile_vnum"] == 1
        assert state["selection_evidence"] == "selected"
    else:
        assert result is None
        assert "selection_evidence" not in state


@pytest.mark.parametrize("hazard", [
    "field", "wounded", "dead", "combat", "negative_fame", "unregistered", "food", "water",
])
def test_registered_probe_preserves_preparation_and_source_gates(monkeypatch, hazard):
    runner, state, _candidate, policy = probe_plan()
    if hazard == "field":
        state["room_vnum"] = "100"
    elif hazard == "wounded":
        state["hp"] = 100
    elif hazard in {"dead", "combat"}:
        state["dead" if hazard == "dead" else "in_combat"] = True
    elif hazard == "negative_fame":
        state["fame"] = -1
    elif hazard == "food":
        state["inventory"] = [[{"short_desc": "a buffalo water skin"}]]
    elif hazard == "water":
        state["inventory"] = [[{"short_desc": "a big pot pie"}]]
    else:
        policy = replace(policy, execution="some-other-research")
    monkeypatch.setattr(runner, "_select_source_ranked_candidate", lambda *_a, **_k: pytest.fail(
        "unsafe probe must not reach hunt selection",
    ), raising=False)
    assert runner._executable_registered_probe_hunt(state, policy) is None


def test_registered_probe_can_choose_an_independent_admitted_target(monkeypatch):
    runner, state, candidate, policy = probe_plan()
    independent = replace(candidate, mobile_vnum=2, room_vnum=200)
    monkeypatch.setattr(runner, "_select_source_ranked_candidate",
                        lambda *_a, **_k: independent, raising=False)
    result = runner._executable_registered_probe_hunt(state, policy)
    assert result.source_mobile_vnums == (2,)
    assert state[campaign._SOURCE_RANKED_CANDIDATE_KEY]["mobile_vnum"] == 2


def test_registered_probe_keeps_selected_circuit(monkeypatch):
    runner, state, candidate, policy = probe_plan()
    sibling = replace(candidate, mobile_vnum=2, room_vnum=200)

    def select(_state, **_kwargs):
        runner._selected_source_ranked_circuit = (sibling,)
        return candidate

    monkeypatch.setattr(runner, "_select_source_ranked_candidate", select, raising=False)
    assert runner._executable_registered_probe_hunt(state, policy) is not None
    assert state[campaign._SOURCE_RANKED_CANDIDATE_KEY]["circuit"][0]["mobile_vnum"] == 2


@pytest.mark.parametrize("result", ["winner", "none", "mismatch", "named", "failed_alias"])
def test_scout_handoff_compares_measured_source_hunts_without_leaking_a_loser(monkeypatch, result):
    runner, state, candidate, scout = probe_plan()
    runner._campaign_policy_storage = object()
    runner._campaign_policy_campaign_id = 1
    winner = replace(candidate, mobile_vnum=2, room_vnum=200)
    if result == "failed_alias":
        winner = replace(winner, mobile_vnum=20515)
        state["world_boot_id"] = "boot"
        state[campaign._REGISTERED_RESEARCH_XP_LOSS_POLICIES_KEY] = [{
            "policy_id": campaign._DWARVEN_HOME_GAMBLER_LEVEL_45_HUNT_POLICY.policy_id,
            "level": 45, "loss_count": 1, "boot_id": "boot",
        }]
    winner_id = campaign._source_ranked_policy_id(winner, character_level=45)
    generic_id = campaign._source_ranked_policy_id(candidate, character_level=45)
    monkeypatch.setattr(runner, "_select_source_ranked_candidate", lambda *_a, **_kw: candidate, raising=False)

    def compare(projection, selected):
        assert selected is candidate
        assert projection is not state
        projection["comparison_only"] = True
        projection[campaign._SOURCE_RANKED_CANDIDATE_KEY] = campaign._source_ranked_candidate_record(
            winner, character_level=45, source_revision=state[campaign._SOURCE_REVISION_KEY],
        )
        runner._selected_source_ranked_candidate = winner
        runner._selected_source_ranked_circuit = ()
        runner._source_ranked_protection_retry_selected_policy_id = winner_id
        if result == "none":
            return None
        return replace(campaign._SOURCE_RANKED_HUNT_POLICY,
                       policy_id="wrong" if result == "mismatch" else winner_id,
                       execution="some-named-hunt" if result == "named" else "source-ranked-hunt")

    monkeypatch.setattr(runner, "_productive_registered_hunt_policy", compare)
    selected = runner._executable_registered_probe_hunt(state, scout)
    assert selected.policy_id == (winner_id if result == "winner" else generic_id)
    assert ("comparison_only" in state) is (result == "winner")
    assert state[campaign._SOURCE_RANKED_CANDIDATE_KEY]["mobile_vnum"] == (2 if result == "winner" else 1)
    assert runner._source_ranked_protection_retry_selected_policy_id == (winner_id if result == "winner" else None)


def test_scout_handoff_never_compares_single_target_rates_over_a_selected_circuit(monkeypatch):
    runner, state, candidate, scout = probe_plan()
    runner._campaign_policy_storage = object()
    runner._campaign_policy_campaign_id = 1

    def select(*_a, **_kw):
        runner._selected_source_ranked_circuit = (replace(candidate, mobile_vnum=2, room_vnum=200),)
        return candidate

    monkeypatch.setattr(runner, "_select_source_ranked_candidate", select, raising=False)
    monkeypatch.setattr(runner, "_productive_registered_hunt_policy",
                        lambda *_a: pytest.fail("a circuit must keep ownership"))
    selected = runner._executable_registered_probe_hunt(state, scout)
    assert selected.source_mobile_vnums == (1,)
    assert len(state[campaign._SOURCE_RANKED_CANDIDATE_KEY]["circuit"]) == 1


@pytest.mark.parametrize("selector_respects_exclusion", [False, True])
def test_registered_failure_cannot_gain_permission_from_generic_alias(monkeypatch, selector_respects_exclusion):
    runner, state, candidate, policy = probe_plan()
    state["world_boot_id"] = "boot"
    loss = {"policy_id": campaign._DWARVEN_HOME_GAMBLER_LEVEL_45_HUNT_POLICY.policy_id,
            "level": 45, "boot_id": "boot", "loss_event_id": 7, "loss_count": 1}
    state[campaign._REGISTERED_RESEARCH_XP_LOSS_POLICIES_KEY] = [loss]
    runner._source_world.rooms[200] = RoomSource(200, "Gambler room", "test.are")
    runner._source_world.mob_resets.append(MobReset(20515, 200, 1))

    def select(_state, **kwargs):
        assert campaign._source_identity_policy_id("test.are", 20515, 200, 45) in kwargs["excluded_policy_ids"]
        return candidate if selector_respects_exclusion else replace(candidate, mobile_vnum=20515, room_vnum=200)

    monkeypatch.setattr(runner, "_select_source_ranked_candidate", select, raising=False)
    result = runner._executable_registered_probe_hunt(state, policy)
    assert (result is not None) is selector_respects_exclusion
    assert state[campaign._REGISTERED_RESEARCH_XP_LOSS_POLICIES_KEY] == [loss]


def test_gear_repair_counts_distinct_registered_and_source_loss_receipts():
    state = {"level": 46, "world_boot_id": "boot",
             campaign._REGISTERED_RESEARCH_XP_LOSS_POLICIES_KEY: [
                 {"policy_id": "registered-one", "level": 46, "boot_id": "boot", "loss_event_id": 7, "loss_count": 1},
                 {"policy_id": "registered-two", "level": 46, "boot_id": "boot", "loss_event_id": 8, "loss_count": 1},
             ], campaign._SOURCE_RANKED_XP_LOSS_POLICIES_KEY: [
                 {"policy_id": "source-ranked-hunt-test-1-100-46", "level": 46, "boot_id": "boot", "loss_event_id": 7, "loss_count": 1},
             ]}
    assert campaign._current_level_progression_loss_count(state, character_level=46) == 2
    assert campaign._current_level_progression_loss_count(state, character_level=47) == 0
    state["world_boot_id"] = "other"
    assert campaign._current_level_progression_loss_count(state, character_level=46) == 0
