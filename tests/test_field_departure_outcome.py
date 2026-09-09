import asyncio
from copy import deepcopy
from dataclasses import replace

import pytest

from dd4tester.campaign import (
    CampaignRunner, _PROVISION_FUNDING_POLICY, _field_city_departure_was_deferred,
    load_campaign_spec, run_campaign_file,
)
from dd4tester.state import CharacterState
from dd4tester.storage import RunStorage
from test_campaign import _record_segment_run, _write_campaign_files
from test_early_funding_locator import _world


def _states():
    state = CharacterState(
        level=8, hp=113, max_hp=113, mana=324, max_mana=324,
        move=220, max_move=220, room_vnum="3054", position=7,
        enemies=None, xp=28365, progress={"xp": 28365},
    ).to_dict()
    state["world_boot_id"] = "test-boot"
    previous = deepcopy(state)
    previous.update({
        "campaign_provision_funding_required": True,
        "campaign_provision_funding_attempts": [{
            "candidate_key": "other:1:2", "boot_id": "test-boot", "completed_kill": False,
        }],
        "campaign_provision_funding_last_attempt": {"candidate_key": "other:1:2"},
        "campaign_research_results": {"old-hunt": {"fatal_failure": True}},
        "campaign_xp_loss_total": 68,
    })
    state["campaign_field_city_preflight"] = {
        "stopped_before_departure": True, "outbound_index": 0,
        "complete": True, "blocked": True, "level": 8, "boot_id": "test-boot",
        "locations": ["temple square", "the bakery"], "wait_attempts": 3,
    }
    return previous, state


@pytest.mark.parametrize("change", [
    "missing", "not_stopped", "outbound", "incomplete", "clear", "level",
    "boot", "missing_boot", "room", "hp", "position", "dead", "combat",
    "enemy", "missing_enemies", "target", "kill", "xp_loss", "xp_changed",
    "xp_missing",
])
def test_departure_deferral_requires_fresh_independent_no_travel_proof(change):
    previous, observed = _states()
    assert _field_city_departure_was_deferred(previous, observed)
    evidence = observed["campaign_field_city_preflight"]
    if change == "missing":
        previous["campaign_field_city_preflight"] = observed.pop("campaign_field_city_preflight")
    elif change == "not_stopped": evidence["stopped_before_departure"] = False
    elif change == "outbound": evidence["outbound_index"] = 1
    elif change == "incomplete": evidence["complete"] = False
    elif change == "clear": evidence["blocked"] = False
    elif change == "level": evidence["level"] = 9
    elif change == "boot": evidence["boot_id"] = "old-boot"
    elif change == "missing_boot": observed.pop("world_boot_id")
    elif change == "room": observed["room_vnum"] = "4022"
    elif change == "hp": observed["hp"] = 0
    elif change == "position": observed["position"] = 0
    elif change == "dead": observed["dead"] = True
    elif change == "combat": observed["in_combat"] = True
    elif change == "enemy": observed["enemies"] = [{"name": "the cityguard"}]
    elif change == "missing_enemies": observed.pop("enemies")
    elif change == "target": observed["combat_target"] = "the drunk"
    elif change == "kill": observed["campaign_completed_kills"] = [{"source_mobile_vnum": 3064}]
    elif change == "xp_loss": observed["xp_loss_observed"] = True
    elif change == "xp_changed": observed["xp"] += 1
    else: observed["xp"] = None
    assert not _field_city_departure_was_deferred(previous, observed)


@pytest.mark.parametrize("execution", ["provision-funding", "source-ranked-hunt"])
@pytest.mark.parametrize("runner_status", ["success", "failed"])
def test_blocked_departure_does_not_invent_a_target_attempt(tmp_path, monkeypatch, execution, runner_status):
    config, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config)
    previous, observed = _states()
    policy = replace(_PROVISION_FUNDING_POLICY, policy_id=execution, execution=execution)

    async def segment(character, profile):
        return replace(_record_segment_run(database, profile, observed), status=runner_status)

    runner = CampaignRunner(spec, config, segment_runner=segment)
    _, candidate = _world()
    monkeypatch.setattr(runner, "_select_provision_funding_candidate", lambda state: candidate)
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name=spec.name, config_path=config.resolve(),
            character_profile_path=spec.character_profile, target_level=spec.target_level,
        )
        result = asyncio.run(runner._run_starter(
            storage, campaign_id, previous, {"command_count": 0, "duration_seconds": 0}, policy,
        ))
        checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)
        segments = storage.list_campaign_segments(campaign_id)
    if runner_status != "success":
        assert result.status == "failed"
        assert checkpoint["reason"] != "field_city_departure_blocked"
        if execution == "provision-funding":
            assert len(result.state["campaign_provision_funding_attempts"]) == 2
        return
    assert result.status == "ready", result.message
    assert not result.ready_for_next_segment and not result.awaiting_area_reset
    assert checkpoint["reason"] == "field_city_departure_blocked"
    assert len(segments) == 1 and segments[0]["run_id"] is not None
    for key in ("campaign_provision_funding_attempts", "campaign_provision_funding_last_attempt",
                "campaign_research_results", "campaign_xp_loss_total"):
        assert result.state[key] == previous[key]
    assert result.state["campaign_provision_funding_required"]
    assert result.state["campaign_field_city_preflight"]["run_id"] == segments[0]["run_id"]

    calls, waits = [], []

    class DeferredRunner:
        def __init__(self, *args, **kwargs): calls.append(kwargs)
        async def run(self): return result

    async def sleep(seconds): waits.append(seconds)

    monkeypatch.setattr("dd4tester.campaign.CampaignRunner", DeferredRunner)
    monkeypatch.setattr("dd4tester.campaign.asyncio.sleep", sleep)
    public = asyncio.run(run_campaign_file(config, segments=4, reset_retries=1, reset_wait=180))
    assert public == result
    assert len(calls) == 1 and not waits
