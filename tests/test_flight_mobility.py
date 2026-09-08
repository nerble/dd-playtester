import json

import pytest

import dd4tester.campaign as campaign
from dd4tester.hunt_candidates import HuntCandidate
from dd4tester.state import CharacterState
from dd4tester.storage import RunStorage


def fixture(tmp_path, *, start_changes=None, field_changes=None, end_changes=None, kill=True):
    target = HuntCandidate(
        status="caution", score=100, area_file="moria.are", mobile_vnum=4002,
        target="the centipede", target_keyword="centipede", level=3,
        room_vnum=4023, room_name="Cave", route=("south",), source_spawn_limit=3,
        room_spawn_count=1, boot_kills=0, loot=(), source_value=0, contained_coins=0,
        hazards=(), estimated_level_range=(1, 5), estimated_move_cost=130,
        estimated_flying_move_cost=37,
    )
    policy_id = campaign._source_ranked_policy_id(target, character_level=8)
    start = CharacterState(
        level=8, xp=27000, hp=113, max_hp=113, mana=324, max_mana=324,
        move=220, max_move=220, room_vnum="3054", position=7, affects=[],
    ).to_dict()
    start.update(world_boot_id="boot", campaign_source_ranked_hunt_candidate=
                 campaign._source_ranked_candidate_record(target, character_level=8, source_revision="source"))
    start.update(start_changes or {})
    field = {**start, "move": 8, "room_vnum": "4016", **(field_changes or {})}
    end = {**start, "xp": 27095, **(end_changes or {})}
    storage = RunStorage(tmp_path / "evidence.sqlite3")
    run_id = storage.create_run(scenario_name="source hunt", scenario_path=tmp_path / "test.yaml")
    for state in (start, field, end):
        event = storage.record_event(run_id, kind="fixture", payload={})
        storage.record_state_snapshot(run_id, source_event_id=event, reason="vitals", state=state)
    if kill:
        storage.record_mob_kill(run_id, character_name="Testmage", boot_id="boot",
                                mob_name=target.target, xp_gained=95,
                                source_mobile_vnum=4002, source_policy_id=policy_id)
    storage.finish_run(run_id, status="success")
    segment = {"id": 1, "run_id": run_id, "phase": policy_id, "status": "success",
               "start_state_json": json.dumps(start), "end_state_json": json.dumps(end)}
    return storage, end, segment


def test_productive_movement_limit_enters_existing_funding_once(tmp_path):
    storage, state, segment = fixture(tmp_path)
    with storage:
        updated = campaign._repair_movement_limited_flight_funding(state, [segment], storage=storage)
        evidence = updated["campaign_optional_flight_evidence"]
        assert evidence["run_id"] == segment["run_id"]
        assert (evidence["ground_cost"], evidence["flying_cost"]) == (130, 37)
        assert updated[campaign._FLIGHT_FUNDING_REQUIRED_KEY]
        assert updated[campaign._FLIGHT_FUNDING_RETRY_KEY]
        assert "campaign_optional_flight_evidence" not in state
        updated.pop(campaign._FLIGHT_FUNDING_REQUIRED_KEY)
        updated.pop(campaign._FLIGHT_FUNDING_RETRY_KEY)
        assert campaign._repair_movement_limited_flight_funding(updated, [segment], storage=storage) == updated
        merged = campaign._campaign_segment_end_state(updated, state, execution="return-home")
        assert merged["campaign_optional_flight_evidence"] == evidence


@pytest.mark.parametrize("changes", [
    {"field_changes": {"move": 9}}, {"field_changes": {"move": None}},
    {"field_changes": {"move": True}}, {"field_changes": {"move": -1}},
    {"field_changes": {"hp": 20}}, {"field_changes": {"hp": float("nan")}},
    {"field_changes": {"in_combat": True}}, {"field_changes": {"position": 6}},
    {"field_changes": {"room_vnum": "3054"}}, {"field_changes": {"room_vnum": "3001"}},
    {"start_changes": {"affects": None}},
    {"start_changes": {"world_boot_id": None}},
    {"start_changes": {"affects": [[{"name": "fly", "duration": 10}]]}},
    {"end_changes": {"xp": 26999}}, {"end_changes": {"xp": 27040}},
    {"start_changes": {"xp": None}}, {"start_changes": {"xp": True}},
    {"start_changes": {"xp": float("nan")}}, {"end_changes": {"xp": None}},
    {"end_changes": {"campaign_xp_loss_observed": True}},
    {"end_changes": {"campaign_died_during_segment": True}},
    {"end_changes": {"room_vnum": "3019"}},
    {"end_changes": {"enemies": [[{"name": "orc"}]]}},
    {"end_changes": {"world_boot_id": "new-boot"}}, {"end_changes": {"level": 9}},
    {"end_changes": {"campaign_known_skill_levels": {"fly": 30}}},
    {"kill": False},
])
def test_movement_handoff_requires_productive_healthy_ground_evidence(tmp_path, changes):
    storage, state, segment = fixture(tmp_path, **changes)
    with storage:
        assert "campaign_optional_flight_evidence" not in campaign._repair_movement_limited_flight_funding(
            state, [segment], storage=storage,
        )


def test_small_savings_and_unfinished_runs_do_not_trigger_funding(tmp_path):
    storage, state, segment = fixture(tmp_path)
    with storage:
        for status in ("running", "failed", "ready"):
            changed = {**segment, "status": status}
            assert campaign._repair_movement_limited_flight_funding(state, [changed], storage=storage) == state
        start = json.loads(segment["start_state_json"])
        start[campaign._SOURCE_RANKED_CANDIDATE_KEY]["estimated_move_cost"] = 50
        segment["start_state_json"] = json.dumps(start)
        assert campaign._repair_movement_limited_flight_funding(state, [segment], storage=storage) == state


def test_snapshot_limit_returns_latest_in_chronological_order(tmp_path):
    storage, _state, segment = fixture(tmp_path)
    with storage:
        all_rows = storage.list_state_snapshots(segment["run_id"])
        assert len(all_rows) == 3
        assert storage.list_state_snapshots(segment["run_id"], limit=2) == all_rows[-2:]
        for invalid in (0, -1, True, 1.5):
            with pytest.raises(ValueError):
                storage.list_state_snapshots(segment["run_id"], limit=invalid)
