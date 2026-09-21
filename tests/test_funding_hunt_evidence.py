import asyncio
import json
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

import pytest

from dd4tester.campaign import (
    CampaignRunner, _PROVISION_FUNDING_POLICY, _funding_sale_below_flight_shortfall,
    _funding_source_identity, _repair_confirmed_research_kills, _research_segment_views,
    _source_ranked_policy_id, load_campaign_spec,
)
from dd4tester.storage import RunStorage
from test_campaign import _record_segment_run, _source_test_candidate, _write_campaign_files
from test_funding_hazard_replay import _evidence, _segment


POLICY = "source-ranked-hunt-moria-4005-4022-8"
KILL = {"mob_name": "the large orc", "source_mobile_vnum": 4005,
        "source_policy_id": POLICY, "xp_gained": 175}


def _fixture():
    start, end, _ = _evidence()
    old = {"observed": True, "viable": True, "completed_kill": True,
           "boot_id": "test-boot", "low_reward": True,
           "objective_xp": 0, "max_objective_kill_xp": 0}
    start["campaign_research_results"][POLICY] = deepcopy(old)
    end["campaign_research_results"][POLICY] = deepcopy(old)
    end["campaign_objective_kills"] = [deepcopy(KILL)]
    return start, end


def _storage(segments, checkpoints=()):
    return SimpleNamespace(
        list_campaign_segments=lambda cid: segments,
        list_campaign_checkpoints=lambda cid: checkpoints,
        list_events=lambda rid: [], list_mob_kills_for_run=lambda rid: [],
    )


def test_funding_view_uses_exact_carrier_not_inherited_field_abort():
    start, end = _fixture()
    views = _research_segment_views(None, _segment(start, end))
    assert set(views) == {"provision-funding"}
    assert views["provision-funding"]["_research_objective_kills"] == []
    assert json.loads(views["provision-funding"]["end_state_json"]) == end


@pytest.mark.parametrize("existing", [True, False])
def test_funding_repair_does_not_promote_zero_xp_or_missing_source_result(existing):
    start, end = _fixture()
    current = deepcopy(end)
    if not existing:
        current["campaign_research_results"].pop(POLICY)
    st = _storage([_segment(start, end)])
    repaired = _repair_confirmed_research_kills(st, 1, current)
    result = repaired.get("campaign_research_results", {}).get(POLICY, {})
    assert result.get("objective_xp", 0) == 0
    assert _repair_confirmed_research_kills(st, 1, repaired) == repaired


@pytest.mark.parametrize("change", [
    "empty", "wrong_policy", "wrong_vnum", "incidental", "no_identity",
    "wrong_boot", "failed", "loss", "death", "unknown_xp", "zero_reward",
    "cleared", "newer_absence", "newer_failure", "newer_funding_absence",
])
def test_funding_does_not_promote_wrong_or_superseded_evidence(change):
    start, end = _fixture()
    current = deepcopy(end)
    segment_changes = {}
    if change == "empty": end["campaign_objective_kills"] = []
    elif change == "wrong_policy": end["campaign_objective_kills"][0]["source_policy_id"] = "source-ranked-hunt-other-4005-4022-8"
    elif change == "wrong_vnum": end["campaign_objective_kills"][0]["source_mobile_vnum"] = 999
    elif change == "incidental": end["campaign_objective_kills"][0]["objective_eligible"] = False
    elif change == "no_identity": end.pop("campaign_provision_funding_last_attempt")
    elif change == "wrong_boot": current["world_boot_id"] = "new-boot"
    elif change == "failed": segment_changes["status"] = "failed"
    elif change == "loss": end["xp_loss_observed"] = True
    elif change == "death": end["campaign_died_during_segment"] = True
    elif change == "unknown_xp": end["xp"] = None
    elif change == "zero_reward": end["campaign_objective_kills"][0]["xp_gained"] = 0
    elif change == "cleared": current["campaign_cleared_research_policies"] = [POLICY]
    segments = [_segment(start, end, **segment_changes)]
    if change.startswith("newer_"):
        later = deepcopy(end)
        later["campaign_objective_kills"] = []
        later["campaign_fastwalk_abort_reason"] = None
        later["campaign_fastwalk_target_absent"] = True
        later["campaign_research_results"][POLICY] = {
            "observed": False, "viable": False, "completed_kill": False,
            "absent": True, "boot_id": "test-boot",
        }
        if change == "newer_funding_absence":
            later["campaign_provision_funding_last_attempt"].update(
                completed_kill=False, unavailable_reason="absent",
            )
        segments.append(_segment(
            end, later, sequence=2, id=11,
            phase="provision-funding" if change == "newer_funding_absence" else POLICY,
            status="failed" if change == "newer_failure" else "success",
        ))
        current = deepcopy(later)
    repaired = _repair_confirmed_research_kills(_storage(segments), 1, current)
    result = repaired["campaign_research_results"][POLICY]
    assert not (result.get("completed_kill") and result.get("objective_xp") == 175)


@pytest.mark.parametrize("key", ["bad", "a.are:0:1", "a.are:1:0", "a.are:x:1", ":1:2"])
def test_invalid_funding_identity_is_not_a_source_target(key):
    _, end = _fixture()
    end["campaign_provision_funding_last_attempt"]["candidate_key"] = key
    assert _funding_source_identity(end) is None


@pytest.mark.parametrize("ordering", ["newer", "older", "equal", "unknown", "naive", "newer_reset"])
def test_funding_kill_never_supersedes_a_cleared_source_result(ordering):
    start, end = _fixture()
    current = deepcopy(end)
    current["campaign_cleared_research_policies"] = [POLICY]
    retired = "2026-09-08T08:59:00+00:00"
    began = {
        "newer": "2026-09-08T12:15:00+00:00",
        "older": "2026-09-08T08:58:00+00:00",
        "equal": retired, "unknown": None,
        "naive": "2026-09-08T12:15:00",
        "newer_reset": "2026-09-08T12:15:00+00:00",
    }[ordering]
    checkpoints = [{
        "reason": "research_policy_retried", "created_at": retired,
        "state_json": json.dumps(current),
    }]
    if ordering == "newer_reset":
        checkpoints.append({**checkpoints[0], "created_at": "2026-09-08T13:00:00+00:00"})
    storage = _storage([_segment(start, end, started_at=began)], checkpoints)
    repaired = _repair_confirmed_research_kills(storage, 1, current)
    result = repaired["campaign_research_results"][POLICY]
    assert result.get("objective_xp", 0) == 0
    assert POLICY in repaired.get("campaign_cleared_research_policies", [])
    assert _repair_confirmed_research_kills(storage, 1, repaired) == repaired


def _funding_state(candidate):
    return {
        "level": 9, "world_boot_id": "boot-1", "room_vnum": "3054",
        "inventory": [[{"short_desc": "a big pot pie"}, {"short_desc": "a buffalo water skin"}]],
        "affects": [], "currencies": {"silver": 11, "copper": 5},
        "campaign_magic_shop_flight_price": 135,
        "campaign_magic_shop_flight_price_boot_id": "boot-1",
        "campaign_has_weapon": True, "campaign_empty_equipment_categories": [],
        "campaign_flight_funding_required": True,
        "campaign_flight_funding_retry_pending": True,
        "campaign_provision_funding_proceeds": [{
            "boot_id": "boot-1", "candidate_key": f"{candidate.area_file}:{candidate.mobile_vnum}:{candidate.room_vnum}",
            "proceeds": 17, "last_proceeds": 8,
        }],
    }


@pytest.mark.parametrize("change", ["fresh", "old_price", "old_sale", "no_last_sale", "enough", "affordable", "zero", "coin_carrier", "wrong_target"])
def test_shortfall_comparison_uses_current_exact_sale_not_prototype_cost(change):
    candidate = _source_test_candidate(target="a carrier", level_range=(5, 9))
    state = _funding_state(candidate)
    sale = state["campaign_provision_funding_proceeds"][0]
    if change == "old_price": state["campaign_magic_shop_flight_price_boot_id"] = "old"
    elif change == "old_sale": sale["boot_id"] = "old"
    elif change == "no_last_sale": sale.pop("last_proceeds")
    elif change == "enough": sale["last_proceeds"] = 20
    elif change == "affordable": state["currencies"]["gold"] = 10
    elif change == "zero": sale["last_proceeds"] = 0
    elif change == "coin_carrier": candidate = replace(candidate, contained_coins=10)
    elif change == "wrong_target": sale["candidate_key"] = "other:1:2"
    assert _funding_sale_below_flight_shortfall(state, candidate) == (change == "fresh")


@pytest.mark.parametrize("boundary", ["none", "no_ground", "no_food", "good_yield", "needs_protection"])
def test_low_yield_funding_uses_existing_ground_fallback(tmp_path, monkeypatch, boundary):
    path, _ = _write_campaign_files(tmp_path)
    runner = CampaignRunner(load_campaign_spec(path), path)
    candidate = _source_test_candidate(target="a reachable target", level_range=(8, 10), mobile_vnum=901, room_vnum=902)
    state = _funding_state(candidate)
    if boundary == "no_food":
        state["inventory"] = []
        state["campaign_provision_funding_required"] = True
    elif boundary == "good_yield": state["campaign_provision_funding_proceeds"][0]["last_proceeds"] = 30
    calls = []
    monkeypatch.setattr(runner, "_select_provision_funding_candidate", lambda state: candidate)
    monkeypatch.setattr(
        "dd4tester.campaign._source_ranked_candidate_requires_sanctuary_for_state",
        lambda *args, **kw: boundary == "needs_protection",
    )

    def ground(state, *, require_no_flight=False, **kw):
        calls.append(require_no_flight)
        return candidate if require_no_flight and boundary != "no_ground" else None

    monkeypatch.setattr(runner, "_select_source_ranked_candidate", ground)
    selected = runner._policy_for_state(state)
    expected_execution = (
        "restock"
        if boundary == "no_food"
        else "source-ranked-hunt"
        if boundary == "none"
        else "provision-funding"
    )
    assert selected.execution == expected_execution
    if boundary == "none":
        assert calls == [True, True]
        assert not selected.requires_flight
    if boundary == "no_food":
        assert calls == []
    assert state["campaign_flight_funding_required"]
    assert state["campaign_flight_funding_retry_pending"]


@pytest.mark.parametrize("runtime", [None, 180])
@pytest.mark.parametrize("outcome", ["success", "failed", "loss", "unknown_xp"])
def test_live_completion_records_carrier_xp_without_promoting_incidental_kill(tmp_path, monkeypatch, runtime, outcome):
    path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(path)
    start, end = _fixture()
    start["campaign_source_revision"] = end["campaign_source_revision"] = "test-revision"
    monkeypatch.setattr("dd4tester.campaign._current_dd4_source_revision", lambda: "test-revision")
    candidate = _source_test_candidate(target="the large orc", level_range=(5, 9), mobile_vnum=4005, room_vnum=4022)
    candidate = replace(candidate, area_file="moria.are", target="the large orc", loot=())
    end["campaign_objective_kills"].append({"mob_name": "the drunk", "source_mobile_vnum": 3064, "xp_gained": 20})
    end["xp"] = start["xp"] + 195
    if outcome == "loss":
        end["xp_loss_observed"] = True
    elif outcome == "unknown_xp":
        end["xp"] = None

    async def segment(character, profile):
        result = _record_segment_run(database, profile, end)
        with RunStorage(database) as events:
            events.record_event(result.run_id, kind="state", payload={
                "state": "completed", "objective_kills": end["campaign_objective_kills"],
            })
        return replace(result, status="failed") if outcome == "failed" else result

    runner = CampaignRunner(spec, path, segment_runner=segment, max_segment_runtime=runtime)
    monkeypatch.setattr(runner, "_select_provision_funding_candidate", lambda state: candidate)
    with RunStorage(database) as storage:
        cid = storage.create_campaign(name=spec.name, config_path=path.resolve(), character_profile_path=spec.character_profile, target_level=spec.target_level)
        result = asyncio.run(runner._run_starter(
            storage, cid, start, {"command_count": 0, "duration_seconds": 0}, _PROVISION_FUNDING_POLICY,
        ))
    own = result.state.get("campaign_research_results", {}).get(POLICY, {})
    assert own.get("objective_xp", 0) == 0
    assert "source-ranked-hunt-midgaard-3064" not in result.state["campaign_research_results"]
