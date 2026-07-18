import json
from pathlib import Path

from dd4tester.cli import main
from dd4tester.evidence import collect_run_evidence
from dd4tester.storage import RunStorage


def test_collect_run_evidence_summarizes_observations_without_raw_text(tmp_path) -> None:
    database = _record_evidence_run(tmp_path)

    with RunStorage(database) as storage:
        evidence = collect_run_evidence(storage, 1)

    observations = evidence["observations"]
    assert observations["rooms"] == [
        {
            "name": "The Mud School Arena",
            "vnum": "3728",
            "area": "Mud School",
            "exits": ["e", "s", "u", "w"],
            "flags": "safe",
        }
    ]
    assert observations["latest_progress"] == {
        "level": "2",
        "xp": "3675",
        "xptnl": "325",
        "practice": "1",
    }
    assert observations["lowest_health"] == {"current": 37, "maximum": 60}
    assert observations["observed_targets"] == ["giant lizard", "wild boar"]
    rendered = json.dumps(evidence)
    assert "secret-command" not in rendered
    assert "sensitive response fragment" not in rendered


def test_collect_evidence_cli_writes_json(tmp_path, capsys) -> None:
    database = _record_evidence_run(tmp_path)
    output = tmp_path / "evidence" / "run-1.json"

    exit_code = main(
        [
            "collect-evidence",
            "1",
            "--database",
            str(database),
            "--output",
            str(output),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert str(output.resolve()) in captured.out
    exported = json.loads(output.read_text(encoding="utf-8"))
    assert exported["observations"]["observed_targets"] == [
        "giant lizard",
        "wild boar",
    ]


def _record_evidence_run(tmp_path: Path) -> Path:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        run_id = storage.create_run(
            scenario_name="dd4-arena-research",
            scenario_path=Path("scenarios/arena.yaml"),
        )
        storage.record_event(
            run_id,
            kind="command",
            payload={"command": "secret-command"},
        )
        storage.record_event(
            run_id,
            kind="response",
            payload={
                "text": (
                    "\x1b[37mA giant lizard makes a horrible rasping sound.\n"
                    "A wild boar grunts and snorts at you.\n"
                    "sensitive response fragment"
                )
            },
        )
        storage.record_event(
            run_id,
            kind="game_event",
            payload={
                "type": "room_updated",
                "source": "gmcp",
                "data": {
                    "name": "The Mud School Arena",
                    "vnum": "3728",
                    "area": "Mud School",
                    "exits": {"e": "3730", "s": "3732", "u": "3737", "w": "3729"},
                    "flags": "safe",
                },
            },
        )
        storage.record_event(
            run_id,
            kind="game_event",
            payload={
                "type": "progress_changed",
                "source": "gmcp",
                "data": {"level": "2", "xp": "3675", "xptnl": "325", "practice": "1"},
            },
        )
        storage.record_event(
            run_id,
            kind="game_event",
            payload={
                "type": "health_changed",
                "source": "gmcp",
                "data": {"current": 37, "maximum": 60},
            },
        )
        storage.finish_run(run_id, status="success")
    return database
