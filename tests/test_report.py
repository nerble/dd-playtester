import json
from collections import Counter
from pathlib import Path

from dd4tester.cli import main
from dd4tester.report import (
    _commentary,
    _balance_signals,
    _item_acquisition_count,
    _progress_summary,
    build_campaign_report,
    build_run_report,
    render_campaign_markdown,
    render_markdown,
    write_campaign_report,
)
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
    assert report["progress"]["combat_decisions"] == 2
    assert report["progress"]["confirmed_kills"] == [
        {"mob_name": "tutorial wolf", "xp_gained": 75}
    ]
    assert report["progress"]["level_gains_observed"] == 1
    assert report["progress"]["items_acquired"] == 1
    assert [item["skill"] for item in report["progress"]["training"]["accepted"]] == [
        "magic missile"
    ]
    assert [item["skill"] for item in report["progress"]["training"]["rejected"]] == [
        "kick"
    ]
    assert report["progress"]["loot_sales"] == {
        "count": 1,
        "coins": 10,
        "shops": ["Leather Shop"],
        "items": [
            {"item": "a metal buckler", "shop": "Leather Shop", "coins": 10}
        ],
    }
    assert report["progress"]["loot_sale_rejections"] == [
        {
            "item_description": "a patched leather jerkin",
            "shopkeeper": "The armourer",
            "reason": "shopkeeper refused item",
        }
    ]
    assert report["character"] == {
        "name": "Reportmage",
        "race": "human",
        "gender": "female",
        "class": "mage",
        "subclass": "warlock",
    }

    assert report["decision_analysis"]["category_counts"] == {
        "combat": 2,
        "safety": 1,
    }
    assert report["decision_analysis"]["safety_critical_count"] == 1
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
    assert "I gained 75 experience points." in report["commentary"]
    assert report["commentary"][-1] == "The run stopped: command budget reached."

    markdown = render_markdown(report)
    assert "# Run 1: starter:Reportmage" in markdown
    assert "## Balance Signals" in markdown
    assert "## Decision Analysis" in markdown
    assert "Character: Reportmage, female, human, mage (warlock)" in markdown
    assert "Confirmed kills: tutorial wolf (+75 XP)" in markdown
    assert "Loot sales: 1 item(s) for 10 coins" in markdown
    assert "Loot sale refusals: 1 item offer(s) refused" in markdown
    assert "Training: accepted magic missile; rejected kick" in markdown
    assert "**critical - health pressure:** Health reached 10% of maximum." in markdown


def test_report_counts_purchase_quantity_as_multiple_items() -> None:
    event = {
        "payload": {
            "type": "item_acquired",
            "data": {"item": "big pot pies", "quantity": 3},
        }
    }

    assert _item_acquisition_count(event) == 3


def test_report_infers_combat_from_confirmed_kills_when_start_text_is_missing() -> None:
    progress = _progress_summary(
        {},
        {},
        [],
        Counter(),
        [],
        [],
        [{"mob_name": "patrolling guard", "xp_gained": 257}],
        [],
    )

    assert progress["combat_starts"] == 1
    combat_signal = next(
        signal
        for signal in _balance_signals(progress, Counter())
        if signal["name"] == "combat"
    )
    assert "detected 1 combat start(s)" in combat_signal["detail"]


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


def test_campaign_report_aggregates_runs_and_writes_hero_artifacts(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    config_path = tmp_path / "campaign.yaml"
    config_path.write_text("target_level: 2\n", encoding="utf-8")

    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Reportmage to HERO",
            config_path=config_path,
            character_profile_path=tmp_path / "character.yaml",
            target_level=2,
        )
        run_id = storage.create_run(
            scenario_name="starter:Reportmage",
            scenario_path=Path("scenarios/starter.yaml"),
        )
        storage.record_event(
            run_id,
            kind="run_context",
            payload={
                "character": {
                    "name": "Reportmage",
                    "race": "human",
                    "gender": "female",
                    "class": "mage",
                }
            },
        )
        start_state = {
            "name": "Reportmage",
            "level": 1,
            "xp": 0,
            "hp": 40,
            "max_hp": 40,
            "room_name": "Mud School",
            "room_vnum": "3725",
            "dead": False,
        }
        end_state = {
            **start_state,
            "level": 2,
            "xp": 100,
            "room_name": "By the Temple Altar",
            "room_vnum": "3054",
            "quest_points": 3,
            "total_quest_points": 7,
            "quest_level_qp_required": 1,
            "quest_level_qp_shortfall": 0,
        }
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="starter-0-2",
            start_state=start_state,
        )
        storage.record_mob_kill(
            run_id,
            character_name="Reportmage",
            boot_id="test-boot",
            mob_name="tutorial wolf",
            xp_gained=100,
            source_mobile_vnum=3729,
            source_policy_id="mud-school-2-6",
        )
        storage.finish_campaign_segment(
            segment_id,
            status="success",
            run_id=run_id,
            end_state=end_state,
            command_count=12,
            duration_seconds=3.5,
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=segment_id,
            run_id=run_id,
            phase="starter-0-2",
            reason="segment_complete",
            state=end_state,
        )
        storage.finish_run(run_id, status="success")
        storage.finish_campaign(campaign_id, status="success")

        report = build_campaign_report(storage, campaign_id)
        json_path, markdown_path = write_campaign_report(
            storage,
            campaign_id,
            directory=tmp_path / "hero-workspace",
        )

    assert report["target"] == {"level": 2, "reached": True}
    assert report["character"]["name"] == "Reportmage"
    assert report["progress"]["level_change"] == 1
    assert report["progress"]["xp_change"] == 100
    assert report["progress"]["quest"] == {
        "points": 3,
        "total_points": 7,
        "level_required": 1,
        "shortfall": 0,
    }
    assert report["totals"]["kills"] == 1
    assert report["kills"][0]["source_mobile_vnum"] == 3729
    assert json_path.is_file()
    assert markdown_path.is_file()
    assert "# Campaign" in markdown_path.read_text(encoding="utf-8")
    assert "tutorial wolf (+100 XP" in render_campaign_markdown(report)
    assert "Quest points: 3 total; next gate 1; shortfall 0." in markdown_path.read_text(
        encoding="utf-8"
    )


def test_campaign_report_cli_renders_json(tmp_path, capsys) -> None:
    database = tmp_path / "runs.sqlite3"
    config_path = tmp_path / "campaign.yaml"
    config_path.write_text("target_level: 2\n", encoding="utf-8")
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Empty campaign",
            config_path=config_path,
            character_profile_path=tmp_path / "character.yaml",
            target_level=2,
        )

    output = tmp_path / "campaign-report.json"
    exit_code = main(
        [
            "campaign-report",
            str(campaign_id),
            "--database",
            str(database),
            "--format",
            "json",
            "--output",
            str(output),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert str(output.resolve()) in captured.out
    rendered = json.loads(output.read_text(encoding="utf-8"))
    assert rendered["campaign"]["name"] == "Empty campaign"


def test_commentary_explains_an_empty_run_has_no_experience_progress() -> None:
    commentary = _commentary(
        [],
        "success",
        None,
        {"experience": {"change": 0}, "confirmed_kills": []},
        3,
    )

    assert commentary == [
        "I made no experience progress this run.",
        "I completed the run successfully.",
    ]


def _create_report_run(tmp_path, *, status: str, error: str | None) -> Path:
    database = tmp_path / "runs.sqlite3"
    storage = RunStorage(database)
    run_id = storage.create_run(
        scenario_name="starter:Reportmage",
        scenario_path=Path("profiles/reportmage.yaml"),
    )
    storage.record_event(
        run_id,
        kind="run_context",
        payload={
            "character": {
                "name": "Reportmage",
                "race": "human",
                "gender": "female",
                "class": "mage",
                "subclass": "warlock",
            },
            "objective": {"level": 2},
        },
        timestamp="2026-07-17T23:59:58+00:00",
    )
    storage.record_event(
        run_id,
        kind="response",
        payload={
            "text": "The armourer looks uninterested in a patched leather jerkin.\n"
        },
        timestamp="2026-07-17T23:59:59+00:00",
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
        state={"revision": 0, "room_name": "Training Yard"},
        timestamp="2026-07-17T23:59:59+00:00",
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
        kind="decision",
        payload={
            "stage": "course",
            "reason": "use the strongest known mage combat spell, chill touch",
            "command": "cast 'chill touch' wolf",
            "redacted": False,
            "category": "combat",
            "safety_critical": False,
        },
        timestamp="2026-07-18T00:00:01.500000+00:00",
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
    storage.record_event(
        run_id,
        kind="decision",
        payload={
            "stage": "course",
            "reason": "withdraw below 25 percent health",
            "command": "flee",
            "redacted": False,
            "category": "safety",
            "safety_critical": True,
        },
        timestamp="2026-07-18T00:00:02.500000+00:00",
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
    storage.record_event(
        run_id,
        kind="game_event",
        payload={
            "type": "training_completed",
            "source": "text",
            "data": {
                "skill": "magic missile",
                "practice_type": "intellectual",
                "outcome": "accepted",
                "reason": "trainer confirmed the lesson",
            },
        },
        timestamp="2026-07-18T00:00:04.100000+00:00",
    )
    storage.record_event(
        run_id,
        kind="game_event",
        payload={
            "type": "training_rejected",
            "source": "text",
            "data": {
                "skill": "kick",
                "practice_type": "physical",
                "outcome": "rejected",
                "reason": "unmet prerequisites",
            },
        },
        timestamp="2026-07-18T00:00:04.200000+00:00",
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
    storage.record_event(
        run_id,
        kind="state",
        payload={
            "state": "completed",
            "completed_kills": [{"mob_name": "tutorial wolf", "xp_gained": 75}],
        },
        timestamp="2026-07-18T00:00:07+00:00",
    )
    storage.record_loot_sale(
        run_id,
        character_name="Reportmage",
        item_keyword="buckler",
        item_description="a metal buckler",
        shop_name="Leather Shop",
        shop_room_vnum="3035",
        offered_coins=10,
        sold_coins=10,
    )
    storage.finish_run(run_id, status=status, error=error)
    storage.close()
    return database
