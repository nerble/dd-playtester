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
    state = {"schema_version": 1, "revision": 1, "level": 2}
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
    sales = storage.list_loot_sales("Ararisa")

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
    assert sales[0]["id"] == sale_id
    assert sales[0]["run_id"] == run_id
    assert sales[0]["item_keyword"] == "buckler"
    assert sales[0]["offered_coins"] == 10
    assert sales[0]["sold_coins"] == 10
