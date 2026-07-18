import json
from pathlib import Path

import dd4tester.cli
from dd4tester.cli import main
from dd4tester.runner import RunResult
from dd4tester.storage import RunStorage
from dd4tester.transcript import TranscriptRecorder


def test_show_runs_lists_existing_runs(tmp_path, capsys) -> None:
    database, _transcript = _create_recorded_run(tmp_path)

    exit_code = main(["show-runs", "--database", str(database), "--limit", "5"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert str(database.resolve()) in captured.out
    assert "id\tstatus\tscenario" in captured.out
    assert "login" in captured.out
    assert "success" in captured.out


def test_show_transcript_reads_run_id_from_database(tmp_path, capsys) -> None:
    database, transcript = _create_recorded_run(tmp_path)

    exit_code = main(["show-transcript", "1", "--database", str(database)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert str(transcript.resolve()) in captured.out
    assert "command" in captured.out
    assert '"command": "guest"' in captured.out


def test_show_transcript_reads_direct_path(tmp_path, capsys) -> None:
    _database, transcript = _create_recorded_run(tmp_path)

    exit_code = main(["show-transcript", str(transcript), "--raw"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out.splitlines()[0])["kind"] == "command"


def test_show_state_prints_latest_snapshot_and_history(tmp_path, capsys) -> None:
    database, _transcript = _create_recorded_run(tmp_path)

    exit_code = main(["show-state", "1", "--database", str(database)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "state revision 1" in captured.out
    assert '"room_name": "The Entrance"' in captured.out

    exit_code = main(
        ["show-state", "1", "--database", str(database), "--history"]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "snapshot\ttimestamp\trevision\treason" in captured.out
    assert "room_entered" in captured.out


def test_starter_command_runs_character_profile(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "starter.yaml"
    profile.write_text("name: Rulemage", encoding="utf-8")
    transcript = tmp_path / "starter-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_run(path: Path) -> RunResult:
        assert path == profile
        return RunResult(7, "success", transcript, database, {"level": 2})

    monkeypatch.setattr(dd4tester.cli, "run_starter_profile", fake_run)

    exit_code = main(["starter", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 7 success" in captured.out
    assert f"Transcript: {transcript}" in captured.out


def _create_recorded_run(tmp_path) -> tuple[Path, Path]:
    database = tmp_path / "runs.sqlite3"
    storage = RunStorage(database)
    run_id = storage.create_run(scenario_name="login", scenario_path=Path("scenarios/login.yaml"))
    recorder = TranscriptRecorder.create(tmp_path / "transcripts", scenario_name="login", run_id=run_id)
    storage.set_transcript_path(run_id, recorder.path)
    event = recorder.record("command", {"command": "guest"})
    source_event_id = storage.record_event(
        run_id,
        kind=event.kind,
        payload=event.payload,
        timestamp=event.timestamp,
    )
    storage.record_state_snapshot(
        run_id,
        source_event_id=source_event_id,
        reason="room_entered",
        state={
            "schema_version": 1,
            "revision": 1,
            "level": 2,
            "hp": 60,
            "max_hp": 60,
            "room_name": "The Entrance",
        },
        timestamp=event.timestamp,
    )
    storage.finish_run(run_id, status="success")
    transcript_path = recorder.path
    recorder.close()
    storage.close()
    return database, transcript_path
