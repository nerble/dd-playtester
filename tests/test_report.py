import json
from pathlib import Path

from dd4tester.cli import main
from dd4tester.report import build_run_report, render_markdown
from dd4tester.storage import RunStorage


def test_report_summarizes_progress_failures_signals_and_commentary(tmp_path) -> None:
    database = _create_report_run(
        tmp_path,
        status="failed",
        error="command budget reached",
    )

    with RunStorage(database) as storage:
        report = build_run_report(storage, 1)

    assert report["run"]["status"] == "failed"
    assert report["progress"]["level"] == {"initial": 1, "final": 2, "change": 1}
    assert report["progress"]["experience"]["change"] == 75
    assert report["progress"]["health"]["lowest_fraction"] == 0.1
    assert report["progress"]["combat_starts"] == 1
    assert report["progress"]["combat_decisions"] == 1
    assert report["progress"]["level_gains_observed"] == 1
    assert report["progress"]["items_acquired"] == 1
    assert report["failures"] == [
        "command budget reached",
        "Character died 1 time(s).",
    ]
    assert {signal["name"] for signal in report["balance_signals"]} >= {
        "progression",
        "experience",
        "health pressure",
        "combat",
    }
    assert "I chose to fight the tutorial wolf." in report["commentary"]
    assert "I reached level 2." in report["commentary"]
    assert report["commentary"][-1] == "The run stopped: command budget reached."

    markdown = render_markdown(report)
    assert "# Run 1: starter:Reportmage" in markdown
    assert "## Balance Signals" in markdown
    assert "**critical - health pressure:** Health reached 10% of maximum." in markdown


def test_report_cli_writes_json_and_markdown(tmp_path, capsys) -> None:
    database = _create_report_run(tmp_path, status="success", error=None)
    json_path = tmp_path / "reports" / "run-1.json"

    exit_code = main(
        [
            "report",
            "1",
            "--database",
            str(database),
            "--format",
            "json",
            "--output",
            str(json_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert str(json_path.resolve()) in captured.out
    report = json.loads(json_path.read_text(encoding="utf-8"))
    assert report["run"]["status"] == "success"
    assert report["commentary"][-1] == "I completed the run successfully."

    exit_code = main(["report", "1", "--database", str(database)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "# Run 1: starter:Reportmage" in captured.out


def test_report_cli_rejects_invalid_limit(tmp_path, capsys) -> None:
    database = _create_report_run(tmp_path, status="success", error=None)

    exit_code = main(
        ["report", "1", "--database", str(database), "--commentary-limit", "0"]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "--commentary-limit must be at least 1" in captured.err


def _create_report_run(tmp_path, *, status: str, error: str | None) -> Path:
    database = tmp_path / "runs.sqlite3"
    storage = RunStorage(database)
    run_id = storage.create_run(
        scenario_name="starter:Reportmage",
        scenario_path=Path("profiles/reportmage.yaml"),
    )
    initial_event = storage.record_event(
        run_id,
        kind="game_event",
        payload={
            "type": "room_entered",
            "source": "gmcp",
            "data": {"name": "Training Yard"},
        },
        timestamp="2026-07-18T00:00:00+00:00",
    )
    storage.record_state_snapshot(
        run_id,
        source_event_id=initial_event,
        reason="room_entered",
        state={
            "revision": 1,
            "level": 1,
            "xp": 25,
            "hp": 100,
            "max_hp": 100,
            "room_name": "Training Yard",
        },
        timestamp="2026-07-18T00:00:00+00:00",
    )
    storage.record_event(
        run_id,
        kind="decision",
        payload={
            "stage": "course",
            "reason": "fight the tutorial wolf",
            "command": "kill wolf",
            "redacted": False,
        },
        timestamp="2026-07-18T00:00:01+00:00",
    )
    storage.record_event(
        run_id,
        kind="game_event",
        payload={
            "type": "combat_started",
            "source": "text",
            "data": {"target": "tutorial wolf"},
        },
        timestamp="2026-07-18T00:00:02+00:00",
    )
    low_health_event = storage.record_event(
        run_id,
        kind="game_event",
        payload={
            "type": "health_changed",
            "source": "gmcp",
            "data": {"current": 10, "maximum": 100},
        },
        timestamp="2026-07-18T00:00:03+00:00",
    )
    storage.record_state_snapshot(
        run_id,
        source_event_id=low_health_event,
        reason="health_changed",
        state={
            "revision": 2,
            "level": 1,
            "xp": 25,
            "hp": 10,
            "max_hp": 100,
            "room_name": "Training Yard",
        },
        timestamp="2026-07-18T00:00:03+00:00",
    )
    storage.record_event(
        run_id,
        kind="game_event",
        payload={
            "type": "item_acquired",
            "source": "text",
            "data": {"item": "a training sword"},
        },
        timestamp="2026-07-18T00:00:04+00:00",
    )
    level_event = storage.record_event(
        run_id,
        kind="game_event",
        payload={
            "type": "level_gained",
            "source": "text",
            "data": {"level": 2},
        },
        timestamp="2026-07-18T00:00:05+00:00",
    )
    storage.record_state_snapshot(
        run_id,
        source_event_id=level_event,
        reason="level_gained",
        state={
            "revision": 3,
            "level": 2,
            "xp": 100,
            "hp": 90,
            "max_hp": 100,
            "room_name": "Victory Hall",
        },
        timestamp="2026-07-18T00:00:05+00:00",
    )
    storage.record_event(
        run_id,
        kind="game_event",
        payload={"type": "character_died", "source": "text", "data": {}},
        timestamp="2026-07-18T00:00:06+00:00",
    )
    storage.finish_run(run_id, status=status, error=error)
    storage.close()
    return database
