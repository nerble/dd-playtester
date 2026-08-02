import json
import sqlite3
from pathlib import Path

from dd4tester.storage import RunStorage
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
