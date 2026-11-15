from pathlib import Path
import sqlite3
from types import SimpleNamespace

import pytest

import dd4tester.campaign as campaign
from dd4tester.character import CharacterSpec
from dd4tester.hunt_candidates import HuntCandidate, WorldSource
from dd4tester.hunt_efficiency import HuntVisitEfficiency


@pytest.mark.parametrize("case", [
    "new-winner", "same-winner", "owned-circuit", "closed-sibling",
    "missing-result", "missing-unproved", "invalid-result",
    "neutral-absence", "negative-consider", "crowd",
    "recent-challenger", "recent-current", "recent-without-alternative",
    "absent-challenger", "absence-without-alternative",
    "old-absence",
    "sqlite-rows",
])
def test_measured_singleton_winner_can_expand_only_from_admitted_measured_peers(monkeypatch, case):
    candidates = tuple(HuntCandidate(
        status="caution", score=100, area_file="test.are", mobile_vnum=i,
        target=f"adept {i}", target_keyword=f"adept{i}", level=20,
        room_vnum=200+i, room_name=f"Room {i}", route=(),
        source_spawn_limit=1, room_spawn_count=1, boot_kills=0, loot=(),
        source_value=0, contained_coins=0, hazards=(), specials=("spec_cast_adept",),
    ) for i in (1, 2))
    ids = tuple(campaign._source_ranked_policy_id(c, character_level=20) for c in candidates)
    character = CharacterSpec.from_mapping({"name": "Tester", "race": "human", "gender": "male", "class": "warrior"})
    spec = campaign.CampaignSpec("test", Path("character.yaml"), character)
    runner = campaign.CampaignRunner(spec, Path("campaign.yaml"))
    runner._source_world = WorldSource()
    runner._campaign_policy_campaign_id = 1
    runner._campaign_policy_storage = SimpleNamespace(get_run_summary=lambda _: {},
        get_latest_campaign_segment_for_phase=lambda *_a, **_kw: None)
    runner._campaign_policy_segments = [
        {"id": i, "run_id": i, "phase": pid} for i, pid in enumerate(ids, start=1)
    ]
    if case == "sqlite-rows":
        database = sqlite3.connect(":memory:")
        database.row_factory = sqlite3.Row
        runner._campaign_policy_segments = database.execute(
            "SELECT 1 AS id, 1 AS run_id, ? AS phase, 'success' AS status "
            "UNION ALL SELECT 2, 2, ?, 'success'", ids,
        ).fetchall()
        database.close()
    state = {"level": 20, "world_boot_id": "boot", campaign._SOURCE_REVISION_KEY: "source",
             "campaign_research_results": {
                 pid: {"boot_id": "boot", "observed": True, "viable": True,
                       "completed_kill": True, "consider_viable": True} for pid in ids}}
    if case == "closed-sibling":
        state["campaign_research_results"][ids[0]]["xp_loss_observed"] = True
    elif case in {"missing-result", "missing-unproved"}:
        state["campaign_research_results"].pop(ids[0])
    elif case == "invalid-result":
        state["campaign_research_results"][ids[0]] = None
    elif case == "neutral-absence":
        state["campaign_research_results"][ids[0]].update({
            "viable": False, "completed_kill": False, "target_absent": True})
    elif case == "negative-consider":
        state["campaign_research_results"][ids[0]]["consider_viable"] = False
    elif case == "crowd":
        state["campaign_research_results"][ids[0]]["crowded"] = True
    elif case in {"absent-challenger", "absence-without-alternative", "old-absence"}:
        state["campaign_research_results"][ids[1]].update({
            "viable": False, "completed_kill": False, "absent": True})
        runner._campaign_policy_segments.append({
            "id": 3, "run_id": 3, "status": "success",
            "phase": ids[0] if case == "old-absence" else ids[1],
        })
    if case == "owned-circuit":
        runner._selected_source_ranked_circuit = (candidates[0],)
    elif case == "recent-challenger":
        runner._recent_source_mobile_kill_vnums = frozenset({2})
    elif case in {"recent-current", "recent-without-alternative"}:
        runner._recent_source_mobile_kill_vnums = frozenset({1, 2})
    monkeypatch.setattr(campaign, "_state_productive_policy_ids", lambda _: frozenset(ids))
    def select(_state, *, required_policy_id, **kwargs):
        assert kwargs["allow_retry_exhausted_repeat"] is True
        return candidates[ids.index(required_policy_id)]

    monkeypatch.setattr(runner, "_select_source_ranked_candidate", select)
    monkeypatch.setattr(campaign, "observed_hunt_efficiency",
                        lambda _state, _visits, *, source_policy_id, **_kw:
                        None if case == "missing-unproved" and source_policy_id == ids[0] else
                        HuntVisitEfficiency(600 if source_policy_id == ids[0] else 900, 60, (1,), 1))
    offered = []

    def expand(primary, admitted, _world, _state, **_kw):
        offered.extend(admitted)
        return tuple(c for c in admitted if c != primary)

    monkeypatch.setattr(campaign, "_source_ranked_area_circuit_candidates", expand)
    initial = candidates[1] if case in {"same-winner", "recent-current"} else candidates[0]
    if case in {"recent-without-alternative", "absence-without-alternative"}:
        initial = None
    result = runner._productive_registered_hunt_policy(state, initial)
    if case == "owned-circuit":
        assert result is None
        assert offered == []
        assert runner._selected_source_ranked_circuit == (candidates[0],)
    elif case in {"recent-challenger", "recent-current", "absent-challenger"}:
        assert result is None
        assert offered == [initial]
        assert runner._selected_source_ranked_circuit == ()
        assert "campaign_hunt_efficiency_selection" not in state
    else:
        assert result.policy_id == ids[1]
        if case in {"closed-sibling", "missing-unproved", "invalid-result", "negative-consider", "crowd"}:
            assert offered == [candidates[1]]
            assert runner._selected_source_ranked_circuit == ()
            assert "circuit_basis" not in state["campaign_hunt_efficiency_selection"]
        else:
            assert runner._selected_source_ranked_circuit == (candidates[0],)
            receipt = state["campaign_hunt_efficiency_selection"]
            assert receipt["circuit_mobile_vnums"] == [2, 1]
            assert "combined rate unproved" in receipt["circuit_basis"]
            assert len(state[campaign._SOURCE_RANKED_CANDIDATE_KEY]["circuit"]) == 1
