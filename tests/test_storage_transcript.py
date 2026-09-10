import json
import sqlite3
from pathlib import Path

from dd4tester.storage import (
    RunStorage,
    _SQLITE_BUSY_TIMEOUT_MS,
    _SQLITE_JOURNAL_MODE,
)
from dd4tester.transcript import TranscriptRecorder


def test_storage_and_transcript_record_run_events(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    transcript_dir = tmp_path / "transcripts"

    storage = RunStorage(database)
    run_id = storage.create_run(scenario_name="login", scenario_path=Path("scenarios/login.yaml"))
    recorder = TranscriptRecorder.create(transcript_dir, scenario_name="login", run_id=run_id)
    storage.set_transcript_path(run_id, recorder.path)

    event = recorder.record("command", {"command": "guest"})
    source_event_id = storage.record_event(
        run_id,
        kind=event.kind,
        payload=event.payload,
        timestamp=event.timestamp,
    )
    state = {
        "schema_version": 1,
        "revision": 1,
        "name": "Ararisa",
        "level": 2,
    }
    snapshot_id = storage.record_state_snapshot(
        run_id,
        source_event_id=source_event_id,
        reason="progress_changed",
        state=state,
        timestamp=event.timestamp,
    )
    sale_id = storage.record_loot_sale(
        run_id,
        character_name="Ararisa",
        item_keyword="buckler",
        item_description="a metal buckler",
        shop_name="Leather Shop",
        shop_room_vnum="3035",
        offered_coins=10,
        sold_coins=10,
    )
    storage.finish_run(run_id, status="success")

    runs = storage.list_runs()
    stored_run = storage.get_run(run_id)
    snapshots = storage.list_state_snapshots(run_id)
    latest_snapshot = storage.get_latest_state_snapshot(run_id)
    latest_character_state = storage.get_latest_character_state("ararisa")
    sales = storage.list_loot_sales("Ararisa")
    run_sales = storage.list_loot_sales_for_run(run_id)

    recorder.close()
    storage.close()

    transcript_lines = recorder.path.read_text(encoding="utf-8").splitlines()
    transcript_event = json.loads(transcript_lines[0])
    assert transcript_event["kind"] == "command"
    assert transcript_event["payload"] == {"command": "guest"}

    with sqlite3.connect(database) as connection:
        run = connection.execute("SELECT status, transcript_path FROM runs").fetchone()
        stored_event = connection.execute("SELECT kind, payload_json FROM events").fetchone()

    assert run == ("success", str(recorder.path))
    assert stored_event[0] == "command"
    assert json.loads(stored_event[1]) == {"command": "guest"}
    assert runs[0]["id"] == run_id
    assert stored_run is not None
    assert stored_run["transcript_path"] == str(recorder.path)
    assert snapshots[0]["id"] == snapshot_id
    assert snapshots[0]["source_event_id"] == source_event_id
    assert json.loads(snapshots[0]["state_json"]) == state
    assert latest_snapshot is not None
    assert latest_snapshot["reason"] == "progress_changed"
    assert latest_character_state == state
    assert sales[0]["id"] == sale_id
    assert sales[0]["run_id"] == run_id
    assert sales[0]["boot_id"] is None
    assert sales[0]["item_keyword"] == "buckler"
    assert sales[0]["offered_coins"] == 10
    assert sales[0]["sold_coins"] == 10
    assert run_sales[0]["id"] == sale_id


def test_storage_finds_latest_campaign_checkpoint_for_character(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Aeloria to HERO",
            config_path=Path("runs/heroes/aeloria/campaign.yaml"),
            character_profile_path=Path("runs/heroes/aeloria/character.yaml"),
            target_level=100,
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=None,
            run_id=None,
            phase="source-ranked-hunt-test",
            reason="segment_complete",
            state={"name": "Aeloria", "campaign_known_skills": ["armor"]},
        )

        campaign = storage.get_latest_campaign_for_character("aeloria")

    assert campaign is not None
    assert campaign["id"] == campaign_id


def test_storage_uses_bounded_busy_timeout_for_shared_campaign_database(
    tmp_path,
) -> None:
    storage = RunStorage(tmp_path / "runs.sqlite3")

    timeout = storage.connection.execute("PRAGMA busy_timeout").fetchone()[0]

    storage.close()

    assert timeout == _SQLITE_BUSY_TIMEOUT_MS


def test_storage_uses_wal_for_shared_campaign_database(tmp_path) -> None:
    storage = RunStorage(tmp_path / "runs.sqlite3")

    journal_mode = storage.connection.execute(
        "PRAGMA journal_mode"
    ).fetchone()[0]
    synchronous = storage.connection.execute(
        "PRAGMA synchronous"
    ).fetchone()[0]

    storage.close()

    assert journal_mode.casefold() == _SQLITE_JOURNAL_MODE.casefold()
    assert synchronous == 1


def test_state_snapshots_commit_their_recovery_boundary(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    storage = RunStorage(database, event_commit_interval=100)
    run_id = storage.create_run(
        scenario_name="campaign:Ararisa",
        scenario_path=Path("character.yaml"),
    )

    storage.record_state_snapshot(
        run_id,
        source_event_id=None,
        reason="checkpoint",
        state={"name": "Ararisa", "level": 2},
    )

    with sqlite3.connect(database) as observer:
        persisted = observer.execute(
            "SELECT state_json FROM state_snapshots WHERE run_id = ?",
            (run_id,),
        ).fetchone()
    storage.close()

    assert persisted is not None
    assert json.loads(persisted[0]) == {"name": "Ararisa", "level": 2}


def test_storage_replays_missing_transcript_suffix_idempotently(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    storage = RunStorage(database, event_commit_interval=100)
    run_id = storage.create_run(
        scenario_name="fastwalk:Kestrel",
        scenario_path=Path("character.yaml"),
    )
    recorder = TranscriptRecorder.create(
        tmp_path / "transcripts",
        scenario_name="fastwalk",
        run_id=run_id,
    )
    storage.set_transcript_path(run_id, recorder.path)

    first = recorder.record("command", {"command": "look"})
    storage.record_event(
        run_id,
        kind=first.kind,
        payload=first.payload,
        timestamp=first.timestamp,
    )
    game_event = recorder.record(
        "game_event",
        {
            "type": "room_entered",
            "source": "text",
            "data": {"room_vnum": "3054"},
        },
    )
    recorder.record(
        "state_snapshot",
        {
            "reason": "room_entered",
            "source": "text",
            "state": {"name": "Kestrel", "level": 19, "room_vnum": "3054"},
        },
    )

    imported = storage.repair_run_events_from_transcript(run_id)
    assert imported == 2
    assert storage.repair_run_events_from_transcript(run_id) == 0
    assert len(storage.list_events(run_id)) == 3
    snapshot = storage.get_latest_state_snapshot(run_id)
    recorder.close()
    storage.close()

    assert snapshot is not None
    assert snapshot["source_event_id"] == 2
    assert json.loads(snapshot["state_json"])["room_vnum"] == "3054"


def test_storage_binds_unique_interrupted_campaign_run(tmp_path) -> None:
    storage = RunStorage(tmp_path / "runs.sqlite3")
    campaign_id = storage.create_campaign(
        name="Kestrel to HERO",
        config_path=tmp_path / "campaign.yaml",
        character_profile_path=tmp_path / "character.yaml",
        target_level=100,
    )
    segment_id = storage.start_campaign_segment(
        campaign_id,
        phase="source-ranked-hunt",
        start_state={"name": "Kestrel", "level": 19},
    )
    run_id = storage.create_run(
        scenario_name="fastwalk-source-ranked-hunt:Kestrel",
        scenario_path=tmp_path / "character.yaml",
    )

    assert storage.bind_unlinked_campaign_runs() == 1
    segment = storage.list_campaign_segments(campaign_id)[0]
    storage.close()

    assert segment["id"] == segment_id
    assert segment["run_id"] == run_id


def test_storage_lists_bounded_recent_campaign_history_in_sequence_order(
    tmp_path,
) -> None:
    storage = RunStorage(tmp_path / "runs.sqlite3")
    campaign_id = storage.create_campaign(
        name="campaign",
        config_path=tmp_path / "campaign.yaml",
        character_profile_path=tmp_path / "character.yaml",
        target_level=100,
    )
    for sequence in range(4):
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase=f"phase-{sequence}",
            start_state={"sequence": sequence},
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=segment_id,
            run_id=None,
            phase=f"phase-{sequence}",
            reason="test",
            state={"sequence": sequence},
        )

    assert [
        row["sequence"]
        for row in storage.list_recent_campaign_segments(campaign_id, limit=3)
    ] == [2, 3, 4]
    assert [
        row["phase"]
        for row in storage.list_recent_campaign_checkpoints(campaign_id, limit=2)
    ] == ["phase-2", "phase-3"]

    summaries = storage.list_campaign_segment_summaries(campaign_id)
    assert summaries[0]["sequence"] == 1
    assert summaries[0]["phase"] == "phase-0"
    assert "start_state_json" not in summaries[0].keys()
    assert "end_state_json" not in summaries[0].keys()
    assert [
        row["phase"]
        for row in storage.list_campaign_segments_for_phases(
            campaign_id,
            ["phase-3", "phase-1", "phase-3"],
        )
    ] == ["phase-1", "phase-3"]

    segment_id = storage.start_campaign_segment(
        campaign_id,
        phase="phase-4",
        start_state={"sequence": 4},
    )
    storage.record_campaign_checkpoint(
        campaign_id,
        segment_id=segment_id,
        run_id=None,
        phase="phase-4",
        reason="test",
        state={"sequence": 4},
    )
    segments = storage.list_recent_campaign_segments(campaign_id, limit=3)
    checkpoints = storage.list_recent_campaign_checkpoints(campaign_id, limit=2)
    storage.close()

    assert [row["sequence"] for row in segments] == [3, 4, 5]
    assert [row["phase"] for row in segments] == ["phase-2", "phase-3", "phase-4"]
    assert [row["phase"] for row in checkpoints] == ["phase-3", "phase-4"]


def test_storage_maintains_exact_campaign_usage_after_segment_updates(tmp_path) -> None:
    storage = RunStorage(tmp_path / "runs.sqlite3")
    campaign_id = storage.create_campaign(
        name="campaign",
        config_path=tmp_path / "campaign.yaml",
        character_profile_path=tmp_path / "character.yaml",
        target_level=100,
    )
    segment_id = storage.start_campaign_segment(
        campaign_id,
        phase="field-hunt",
        start_state={"level": 12},
    )

    assert dict(storage.campaign_totals(campaign_id)) == {
        "segment_count": 1,
        "command_count": 0,
        "duration_seconds": 0.0,
    }

    storage.finish_campaign_segment(
        segment_id,
        status="success",
        run_id=7,
        end_state={"level": 12},
        command_count=11,
        duration_seconds=4.5,
    )
    storage.finish_campaign_segment(
        segment_id,
        status="success",
        run_id=7,
        end_state={"level": 12},
        command_count=13,
        duration_seconds=5.0,
    )

    assert dict(storage.campaign_totals(campaign_id)) == {
        "segment_count": 1,
        "command_count": 13,
        "duration_seconds": 5.0,
    }
    storage.close()


def test_storage_filters_campaign_game_events_by_level_and_skill(tmp_path) -> None:
    storage = RunStorage(tmp_path / "runs.sqlite3")
    campaign_id = storage.create_campaign(
        name="campaign",
        config_path=tmp_path / "campaign.yaml",
        character_profile_path=tmp_path / "character.yaml",
        target_level=100,
    )
    segment_id = storage.start_campaign_segment(
        campaign_id,
        phase="training",
        start_state={"level": 19},
    )
    run_id = storage.create_run(
        scenario_name="starter:Kestrel",
        scenario_path=tmp_path / "character.yaml",
    )
    storage.connection.execute(
        "UPDATE campaign_segments SET run_id = ? WHERE id = ?",
        (run_id, segment_id),
    )
    storage.connection.commit()
    storage.record_event(
        run_id,
        kind="game_event",
        payload={
            "type": "training_completed",
            "data": {"practice_type": "physical", "skill": "counterbalance"},
        },
    )
    storage.record_event(
        run_id,
        kind="game_event",
        payload={
            "type": "training_rejected",
            "data": {"skill": "backstab", "reason": "trainer level requirement"},
        },
    )
    storage.finish_run(run_id, status="success")

    recent_segment_id = storage.start_campaign_segment(
        campaign_id,
        phase="training",
        start_state={"level": 20},
    )
    recent_run_id = storage.create_run(
        scenario_name="starter:Kestrel",
        scenario_path=tmp_path / "character.yaml",
    )
    storage.connection.execute(
        "UPDATE campaign_segments SET run_id = ? WHERE id = ?",
        (recent_run_id, recent_segment_id),
    )
    storage.connection.commit()
    storage.record_event(
        recent_run_id,
        kind="game_event",
        payload={
            "type": "training_completed",
            "data": {"practice_type": "physical", "skill": "backstab"},
        },
    )
    storage.finish_run(recent_run_id, status="success")

    events = storage.list_campaign_game_events(campaign_id, level=19)
    counterbalance = storage.list_campaign_game_events(
        campaign_id,
        skill="COUNTERBALANCE",
    )
    recent_events = storage.list_campaign_game_events(
        campaign_id,
        segment_limit=1,
    )
    rejected_events = storage.list_campaign_game_events(
        campaign_id,
        event_types=("training_rejected",),
    )

    assert len(events) == 2
    assert len(counterbalance) == 1
    assert json.loads(counterbalance[0]["payload_json"])["type"] == (
        "training_completed"
    )
    assert len(recent_events) == 1
    assert json.loads(recent_events[0]["payload_json"])["data"]["skill"] == (
        "backstab"
    )
    assert len(rejected_events) == 1
    assert json.loads(rejected_events[0]["payload_json"])["data"]["skill"] == (
        "backstab"
    )
    storage.close()


def test_character_snapshot_lookups_are_indexed_and_case_insensitive(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    storage = RunStorage(database)
    run_id = storage.create_run(
        scenario_name="starter:Kestrel",
        scenario_path=Path("profile.yaml"),
    )
    storage.record_state_snapshot(
        run_id,
        source_event_id=None,
        reason="progress_changed",
        state={"name": "Kestrel", "level": 1, "xp": 0},
    )
    storage.record_state_snapshot(
        run_id,
        source_event_id=None,
        reason="item_acquired",
        state={
            "name": "kEsTrEl",
            "level": 2,
            "acquired_items": [{"item": "a large sack"}],
        },
    )

    assert storage.get_latest_character_state("KESTREL")["level"] == 2
    assert storage.character_has_acquired_item("kestrel", "large sack")

    latest_plan = storage.connection.execute(
        """
        EXPLAIN QUERY PLAN
        SELECT state_json
        FROM state_snapshots
        WHERE lower(json_extract(state_json, '$.name')) = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        ("kestrel",),
    ).fetchall()
    item_plan = storage.connection.execute(
        """
        EXPLAIN QUERY PLAN
        SELECT state_json
        FROM state_snapshots
        WHERE reason = 'item_acquired'
          AND lower(json_extract(state_json, '$.name')) = ?
        ORDER BY id DESC
        """,
        ("kestrel",),
    ).fetchall()
    storage.close()

    assert any(
        "idx_state_snapshots_character_id" in row[3]
        for row in latest_plan
    )
    assert any(
        "idx_state_snapshots_reason_character_id" in row[3]
        for row in item_plan
    )


def test_run_scoped_evidence_lookups_are_indexed(tmp_path) -> None:
    storage = RunStorage(tmp_path / "runs.sqlite3")

    loot_plan = storage.connection.execute(
        """
        EXPLAIN QUERY PLAN
        SELECT id
        FROM loot_sales
        WHERE run_id = ?
        ORDER BY id
        """,
        (1,),
    ).fetchall()
    kill_plan = storage.connection.execute(
        """
        EXPLAIN QUERY PLAN
        SELECT id
        FROM mob_kills
        WHERE run_id = ?
        ORDER BY id
        """,
        (1,),
    ).fetchall()
    storage.close()

    assert any("idx_loot_sales_run_id" in row[3] for row in loot_plan)
    assert any("idx_mob_kills_run_id" in row[3] for row in kill_plan)


def test_storage_marks_interrupted_runs_as_failed(tmp_path) -> None:
    storage = RunStorage(tmp_path / "runs.sqlite3")
    run_id = storage.create_run(scenario_name="arena", scenario_path=Path("arena.yaml"))

    recovered = storage.fail_interrupted_runs(reason="test interruption")
    run = storage.get_run(run_id)
    storage.close()

    assert recovered == 1
    assert run is not None
    assert run["status"] == "failed"
    assert run["error"] == "test interruption"


def test_storage_timeout_closes_unbound_campaign_run(tmp_path) -> None:
    storage = RunStorage(tmp_path / "runs.sqlite3")
    campaign_id = storage.create_campaign(
        name="Kestrel to HERO",
        config_path=tmp_path / "campaign.yaml",
        character_profile_path=tmp_path / "character.yaml",
        target_level=100,
    )
    segment_id = storage.start_campaign_segment(
        campaign_id,
        phase="shadow-keep-hunt",
        start_state={"name": "Kestrel", "level": 19},
    )
    run_id = storage.create_run(
        scenario_name="fastwalk-shadow-keep:Kestrel",
        scenario_path=tmp_path / "character.yaml",
    )

    closed_segments = storage.fail_campaign_after_timeout(
        campaign_id,
        reason="bounded runner timeout",
        character_name="Kestrel",
    )
    run = storage.get_run(run_id)
    segment = storage.list_campaign_segments(campaign_id)[0]
    storage.close()

    assert closed_segments == 1
    assert run is not None
    assert run["status"] == "failed"
    assert run["error"] == "bounded runner timeout"
    assert segment["id"] == segment_id
    assert segment["run_id"] == run_id
    assert segment["status"] == "failed"


def test_storage_remembers_exact_commands_for_each_character(tmp_path) -> None:
    storage = RunStorage(tmp_path / "runs.sqlite3")
    run_id = storage.create_run(
        scenario_name="starter:Ararisa",
        scenario_path=Path("profile.yaml"),
    )
    storage.record_event(
        run_id,
        kind="command",
        payload={"command": "description Ararisa studies every hinge."},
    )
    other_run_id = storage.create_run(
        scenario_name="starter:NotArarisa",
        scenario_path=Path("profile.yaml"),
    )
    storage.record_event(
        other_run_id,
        kind="command",
        payload={"command": "description This newer command belongs elsewhere."},
    )
    storage.record_event(
        run_id,
        kind="command",
        payload={"command": "train con"},
    )

    assert storage.character_command_recorded(
        "ararisa",
        "description Ararisa studies every hinge.",
    )
    assert not storage.character_command_recorded(
        "Ararisa",
        "description Ararisa studies every lock.",
    )
    assert not storage.character_command_recorded(
        "Kestrel",
        "description Ararisa studies every hinge.",
    )
    assert (
        storage.latest_character_command("Ararisa", prefix="description ")
        == "description Ararisa studies every hinge."
    )
    assert storage.latest_character_command("ARARISA", prefix="train ") == "train con"
    assert storage.latest_character_command("Kestrel", prefix="description ") is None
    storage.close()


def test_storage_marks_interrupted_campaign_work_as_failed(tmp_path) -> None:
    storage = RunStorage(tmp_path / "runs.sqlite3")
    campaign_id = storage.create_campaign(
        name="Ararisa to HERO",
        config_path=tmp_path / "campaign.yaml",
        character_profile_path=tmp_path / "character.yaml",
        target_level=100,
    )
    storage.start_campaign_segment(
        campaign_id,
        phase="ambush-exterior-8-10",
        start_state={"name": "Ararisa", "level": 8},
    )

    segments, campaigns = storage.fail_interrupted_campaign_segments(
        reason="test interruption"
    )
    campaign = storage.get_campaign(campaign_id)
    segment = storage.list_campaign_segments(campaign_id)[0]
    storage.close()

    assert (segments, campaigns) == (1, 1)
    assert campaign is not None
    assert campaign["status"] == "failed"
    assert campaign["error"] == "test interruption"
    assert segment["status"] == "failed"
    assert segment["error"] == "test interruption"
    assert segment["finished_at"] is not None


def test_storage_remembers_historically_acquired_items(tmp_path) -> None:
    storage = RunStorage(tmp_path / "runs.sqlite3")
    run_id = storage.create_run(
        scenario_name="fastwalk-ambush:Ararisa",
        scenario_path=Path("profile.yaml"),
    )
    storage.record_state_snapshot(
        run_id,
        source_event_id=None,
        reason="item_acquired",
        state={
            "name": "Ararisa",
            "acquired_items": [{"item": "large sack"}],
        },
    )
    storage.record_state_snapshot(
        run_id,
        source_event_id=None,
        reason="inventory_changed",
        state={"name": "Ararisa", "acquired_items": []},
    )

    assert storage.character_has_acquired_item("ararisa", "large sack") is True
    assert storage.character_has_acquired_item("ararisa", "backpack") is False
    storage.record_state_snapshot(
        run_id,
        source_event_id=None,
        reason="item_acquired",
        state={
            "name": "Ararisa",
            "acquired_items": [{"item": "a canvas backpack"}],
        },
    )
    assert storage.character_has_acquired_item("ararisa", "backpack") is True
    storage.close()


def test_storage_scopes_sales_and_kills_by_boot_identity(tmp_path) -> None:
    storage = RunStorage(tmp_path / "runs.sqlite3")
    run_id = storage.create_run(
        scenario_name="hunt",
        scenario_path=Path("profile.yaml"),
    )
    boot_id = "Sun Jul 19 12:00:00 2026"
    storage.set_run_boot_id(run_id, boot_id)
    storage.record_loot_sale(
        run_id,
        character_name="Ararisa",
        boot_id=boot_id,
        item_keyword="cap",
        item_description="an iron cap",
        shop_name="Leather Shop",
        shop_room_vnum="3035",
        offered_coins=20,
        sold_coins=20,
    )
    kill_id = storage.record_mob_kill(
        run_id,
        character_name="Ararisa",
        boot_id=boot_id,
        mob_name="Olog",
        xp_gained=45,
        source_mobile_vnum=10247,
        source_policy_id="source-ranked-hunt-solace-10247-10312-24",
    )

    run = storage.get_run(run_id)
    sales = storage.list_loot_sales("Ararisa")
    kills = storage.list_mob_kills("Ararisa", boot_id=boot_id)
    storage.close()

    assert run is not None
    assert run["boot_id"] == boot_id
    assert sales[0]["boot_id"] == boot_id
    assert kills[0]["id"] == kill_id
    assert kills[0]["mob_name"] == "Olog"
    assert kills[0]["xp_gained"] == 45
    assert kills[0]["source_mobile_vnum"] == 10247
    assert kills[0]["source_policy_id"] == (
        "source-ranked-hunt-solace-10247-10312-24"
    )


def test_kill_evidence_commits_before_run_cleanup(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    storage = RunStorage(database, event_commit_interval=100)
    run_id = storage.create_run(
        scenario_name="fastwalk-source-ranked-hunt:Ararisa",
        scenario_path=Path("profile.yaml"),
    )
    storage.record_event(
        run_id,
        kind="response",
        payload={"text": "Bardoosh is DEAD!!"},
    )
    storage.record_mob_kill(
        run_id,
        character_name="Ararisa",
        boot_id=None,
        mob_name="Bardoosh",
        xp_gained=460,
        source_mobile_vnum=4515,
        source_policy_id="source-ranked-hunt-ambush-4515-4514-15",
    )

    with sqlite3.connect(database) as observer:
        persisted = observer.execute(
            "SELECT mob_name, xp_gained, boot_id FROM mob_kills WHERE run_id = ?",
            (run_id,),
        ).fetchone()

    storage.set_run_boot_id(run_id, "boot-1")
    run_kills = storage.list_mob_kills_for_run(run_id)
    storage.close()

    assert persisted == ("Bardoosh", 460, None)
    assert len(run_kills) == 1
    assert run_kills[0]["boot_id"] == "boot-1"
    assert run_kills[0]["source_mobile_vnum"] == 4515


def test_storage_persists_below_band_kill_as_non_objective(tmp_path) -> None:
    storage = RunStorage(tmp_path / "runs.sqlite3")
    run_id = storage.create_run(
        scenario_name="fastwalk-source-ranked-hunt:Ararisa",
        scenario_path=Path("profile.yaml"),
    )

    storage.record_mob_kill(
        run_id,
        character_name="Ararisa",
        boot_id="boot-1",
        mob_name="the goblin leader",
        xp_gained=90,
        below_useful_band=True,
        objective_eligible=False,
    )

    kills = storage.list_mob_kills_for_run(run_id)
    storage.close()

    assert len(kills) == 1
    assert kills[0]["below_useful_band"] == 1
    assert kills[0]["objective_eligible"] == 0
