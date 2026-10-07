import json
from collections import Counter
from pathlib import Path

from dd4tester.cli import main
from dd4tester.report import (
    _commentary,
    _balance_signals,
    _item_acquisition_count,
    _objective_outcome,
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
        "title": "the Procedurally Curious",
        "description": "Reportmage keeps a brass astrolabe and distrusts shortcuts.",
        "personality": "patient, observant, and dryly funny",
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
    assert "Title: the Procedurally Curious" in markdown
    assert "Personality: patient, observant, and dryly funny" in markdown
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


def test_report_infers_distinct_combat_starts_from_enemy_stream_transitions() -> None:
    def enemies(value):
        return {
            "payload": {
                "type": "enemies_changed",
                "data": {"package": "Char.Enemies", "value": value},
            }
        }

    progress = _progress_summary(
        {},
        {},
        [],
        Counter(),
        [
            enemies([[{"name": "the bard", "isnpc": "20509"}]]),
            enemies([]),
            enemies([[{"name": "a guard", "isnpc": "1519"}]]),
        ],
        [],
        [],
        [],
    )

    assert progress["combat_starts"] == 2


def test_terminal_required_item_failure_is_not_objective_success() -> None:
    reason = "field expedition did not acquire required item(s): some blackberries"
    events = [
        {
            "kind": "state",
            "payload": {"state": "completed", "fastwalk_abort_reason": reason},
        },
    ]

    outcome = _objective_outcome(
        {"objective": {"fastwalk_route": "source food reserve blackberries 6023"}},
        {}, [], events,
    )

    assert outcome == "not_achieved"


def test_kill_objective_ignores_route_gate_and_below_band_kills() -> None:
    objective = {"objective": {"fastwalk_kill_limit": 1}}

    assert _objective_outcome(
        objective,
        {},
        [{"mob_name": "gate guard", "route_gate": True}],
        [],
    ) == "not_achieved"
    assert _objective_outcome(
        objective,
        {},
        [{"mob_name": "weak mob", "below_useful_band": True}],
        [],
    ) == "not_achieved"


def test_report_refreshes_stale_kill_summary_from_compact_ledger(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Dorrik progression",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "dorrik.yaml",
            target_level=100,
        )
        run_id = storage.create_run(
            scenario_name="fastwalk-source-ranked hunt dwarven 20514:Dorrik",
            scenario_path=Path("profiles/dorrik.yaml"),
        )
        storage.record_event(
            run_id,
            kind="run_context",
            payload={
                "character": {"name": "Dorrik"},
                "objective": {
                    "fastwalk_route": "source-ranked hunt dwarven 20514",
                    "fastwalk_kill_limit": 1,
                },
            },
            timestamp="2026-10-04T05:40:00+00:00",
        )
        storage.finish_run(
            run_id,
            status="failed",
            error="interrupted during finalization",
            execution_status="interrupted",
            objective_outcome="not_achieved",
            safety_outcome="safe",
            finished_at="2026-10-04T05:44:48+00:00",
        )
        storage.record_mob_kill(
            run_id,
            character_name="Dorrik",
            boot_id="Sun Sep 27 23:55:43 2026",
            mob_name="the bard",
            xp_gained=1542,
            source_mobile_vnum=20509,
            source_policy_id="source-ranked-hunt-dwarven-home-20509-20514-29",
            objective_eligible=True,
            timestamp="2026-10-04T05:44:07+00:00",
        )
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="source-ranked-hunt",
            start_state={"name": "Dorrik", "level": 29, "xp_loss_total": 0},
        )
        storage.finish_campaign_segment(
            segment_id,
            status="ready",
            run_id=run_id,
            end_state={
                "name": "Dorrik",
                "level": 29,
                "dead": False,
                "xp_loss_total": 0,
            },
            command_count=131,
            duration_seconds=212.1,
            execution_status="interrupted",
            objective_outcome="not_achieved",
            safety_outcome="safe",
        )

        report = build_run_report(storage, run_id)
        storage.connection.execute(
            "UPDATE runs SET objective_outcome = 'not_achieved' WHERE id = ?",
            (run_id,),
        )
        storage.connection.execute(
            """
            UPDATE campaign_segments SET objective_outcome = 'not_achieved'
            WHERE id = ?
            """,
            (segment_id,),
        )
        storage.connection.commit()
        cached_report = build_run_report(storage, run_id)
        run = storage.get_run(run_id)
        segment = storage.connection.execute(
            """
            SELECT execution_status, objective_outcome, safety_outcome
            FROM campaign_segments WHERE id = ?
            """,
            (segment_id,),
        ).fetchone()

    assert report["outcomes"] == {
        "execution": "interrupted",
        "objective": "achieved",
        "safety": "safe",
    }
    assert cached_report["outcomes"] == report["outcomes"]
    assert run is not None and run["objective_outcome"] == "achieved"
    assert segment is not None
    assert tuple(segment) == ("interrupted", "achieved", "safe")
    assert report["progress"]["confirmed_kills"] == [
        {
            "mob_name": "the bard",
            "xp_gained": 1542,
            "source_mobile_vnum": 20509,
            "source_policy_id": "source-ranked-hunt-dwarven-home-20509-20514-29",
        }
    ]


def test_refresh_run_summary_cli_persists_reconciled_outcomes(tmp_path, capsys) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Dorrik progression",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "dorrik.yaml",
            target_level=100,
        )
        run_id = storage.create_run(
            scenario_name="fastwalk-source-ranked hunt dwarven 20514:Dorrik",
            scenario_path=tmp_path / "dorrik.yaml",
        )
        storage.record_event(
            run_id,
            kind="run_context",
            payload={
                "character": {"name": "Dorrik"},
                "objective": {"fastwalk_kill_limit": 1},
            },
        )
        storage.finish_run(
            run_id,
            status="failed",
            execution_status="interrupted",
            objective_outcome="not_achieved",
            safety_outcome="safe",
        )
        storage.record_mob_kill(
            run_id,
            character_name="Dorrik",
            boot_id="test-boot",
            mob_name="the bard",
            xp_gained=1542,
            source_mobile_vnum=20509,
            source_policy_id="source-ranked-hunt-dwarven-home-20509-20514-29",
            objective_eligible=True,
        )
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="source-ranked-hunt",
            start_state={"name": "Dorrik", "level": 29, "xp_loss_total": 0},
        )
        storage.finish_campaign_segment(
            segment_id,
            status="ready",
            run_id=run_id,
            end_state={"name": "Dorrik", "level": 29, "xp_loss_total": 0},
            command_count=131,
            duration_seconds=212.1,
            execution_status="interrupted",
            objective_outcome="not_achieved",
            safety_outcome="safe",
        )

    assert main(
        ["refresh-run-summary", str(run_id), "--database", str(database)]
    ) == 0
    assert "objective=achieved" in capsys.readouterr().out

    with RunStorage(database, read_only=True) as storage:
        run = storage.get_run(run_id)
        segment = storage.connection.execute(
            """
            SELECT execution_status, objective_outcome, safety_outcome
            FROM campaign_segments WHERE id = ?
            """,
            (segment_id,),
        ).fetchone()

    assert run is not None and run["objective_outcome"] == "achieved"
    assert segment is not None
    assert tuple(segment) == ("interrupted", "achieved", "safe")


def test_pounding_rearm_objective_requires_the_source_weapon() -> None:
    run_context = {
        "objective": {
            "kind": "city_rearm",
            "weapon_role": "pounding",
            "required_items": ["a steel mace"],
        }
    }

    assert _objective_outcome(
        run_context, {"inventory": [{"name": "a chipped dagger"}]}, [], [],
    ) == "not_achieved"
    assert _objective_outcome(
        run_context, {"inventory": [{"name": "a steel mace"}]}, [], [],
    ) == "achieved"


def test_flight_objective_requires_a_fresh_active_flight_affect() -> None:
    run_context = {"objective": {"kind": "flight_active"}}

    assert _objective_outcome(
        run_context,
        {
            "affects": [[
                {"name": "fly", "gives": "flight", "duration": "33"}
            ]]
        },
        [],
        [],
    ) == "achieved"
    assert _objective_outcome(
        run_context, {"affects": []}, [], [],
    ) == "not_achieved"
    assert _objective_outcome(run_context, {}, [], []) == "unknown"


def test_training_objective_requires_observed_skill_gain() -> None:
    objective = {
        "objective": {
            "kind": "training_gain",
            "initial_skill_levels": {"enhanced damage": 67, "kick": 41},
        }
    }
    events = [
        {
            "kind": "state",
            "payload": {
                "state": "completed",
                "training_audit": {
                    "observed": True,
                    "known_skill_levels": {
                        "enhanced damage": 67,
                        "kick": 41,
                    },
                },
            },
        },
    ]

    assert _objective_outcome(objective, {}, [], events) == "not_achieved"


def test_training_objective_is_achieved_by_a_skill_gain() -> None:
    objective = {
        "objective": {
            "kind": "training_gain",
            "initial_skill_levels": {"enhanced damage": 67},
        }
    }
    final_state = {
        "campaign_training_audit": {
            "observed": True,
            "known_skill_levels": {"enhanced damage": 68},
        },
    }

    assert _objective_outcome(objective, final_state, [], []) == "achieved"


def test_training_objective_stays_unknown_without_comparable_evidence() -> None:
    objective = {"objective": {"kind": "training_gain"}}

    assert _objective_outcome(objective, {}, [], []) == "unknown"

    empty_baseline = {
        "objective": {
            "kind": "training_gain",
            "initial_skill_levels": {},
        }
    }
    final_state = {
        "campaign_training_audit": {
            "observed": True,
            "known_skill_levels": {"enhanced damage": 1},
        },
    }
    assert _objective_outcome(empty_baseline, final_state, [], []) == "unknown"


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
    assert report["commentary"][-1] == (
        "I finished the run; objective completion is unverified."
    )

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
                    "title": "the Procedurally Curious",
                    "description": "Reportmage keeps a brass astrolabe and distrusts shortcuts.",
                    "personality": "patient, observant, and dryly funny",
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

        report = build_campaign_report(
            storage,
            campaign_id,
            full_history=True,
        )
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
    assert report["segments"][0]["start_xp"] == 0
    assert report["segments"][0]["end_xp"] == 100
    assert report["evidence"]["segment_details_included"] is True
    assert report["totals"]["kills"] == 1
    assert report["kills"][0]["source_mobile_vnum"] == 3729
    assert json_path.is_file()
    assert markdown_path.is_file()
    assert "# Campaign" in markdown_path.read_text(encoding="utf-8")
    assert "Personality: patient, observant, and dryly funny" in render_campaign_markdown(
        report
    )
    assert "tutorial wolf (+100 XP" in render_campaign_markdown(report)
    assert "Quest points: 3 total; next gate 1; shortfall 0." in markdown_path.read_text(
        encoding="utf-8"
    )


def test_default_campaign_report_aggregates_cached_kills_without_detail_scan(
    tmp_path,
) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Summary campaign",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=30,
        )
        run_id = storage.create_run(
            scenario_name="starter:Summary",
            scenario_path=tmp_path / "character.yaml",
        )
        kill = {
            "mob_name": "tutorial wolf",
            "xp_gained": 100,
            "source_mobile_vnum": 3729,
            "source_policy_id": "school-wolf",
        }
        storage.record_event(
            run_id,
            kind="run_context",
            payload={
                "character": {"name": "Summary"},
                "objective": {"level": 30},
            },
        )
        storage.record_event(
            run_id,
            kind="state",
            payload={"completed_kills": [kill]},
        )
        storage.record_mob_kill(
            run_id,
            character_name="Summary",
            boot_id="test-boot",
            mob_name="tutorial wolf",
            xp_gained=100,
            source_mobile_vnum=3729,
            source_policy_id="school-wolf",
        )
        storage.finish_run(run_id, status="success")
        build_run_report(storage, run_id)

        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="level-29",
            start_state={"name": "Summary", "level": 29, "xp": 0},
        )
        storage.finish_campaign_segment(
            segment_id,
            status="success",
            run_id=run_id,
            end_state={"name": "Summary", "level": 29, "xp": 100},
            command_count=1,
            duration_seconds=1,
        )
        storage.list_campaign_mob_kills = lambda *_args, **_kwargs: (
            _ for _ in ()
        ).throw(AssertionError("summary report scanned historical kill rows"))

        report = build_campaign_report(storage, campaign_id)

    assert report["totals"]["kills"] == 1
    assert report["kills"] == []
    assert report["kill_groups"] == [{
        "mob_name": "tutorial wolf",
        "source_mobile_vnum": 3729,
        "source_policy_id": "school-wolf",
        "kill_count": 1,
        "xp_gained": 100,
    }]
    assert report["runs"][0]["progress"]
    assert "confirmed_kills" not in report["runs"][0]["progress"]
    assert report["evidence"]["run_summary_coverage"] == 1.0
    markdown = render_campaign_markdown(report)
    assert "tutorial wolf: 1 kill(s), +100 XP" in markdown
    assert "Chronological per-kill detail is omitted" in markdown


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
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="test",
            start_state={"level": 1, "xp": 0},
        )
        storage.finish_campaign_segment(
            segment_id,
            status="success",
            run_id=None,
            end_state={"level": 2, "xp": 100},
            command_count=1,
            duration_seconds=1,
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
            "--full-history",
            "--output",
            str(output),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert str(output.resolve()) in captured.out
    rendered = json.loads(output.read_text(encoding="utf-8"))
    assert rendered["campaign"]["name"] == "Empty campaign"
    assert rendered["segments"][0]["start_level"] == 1
    assert rendered["segments"][0]["end_level"] == 2


def test_campaign_run_link_backfill_cli_reports_completion(tmp_path, capsys) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="New campaign",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=100,
        )

    exit_code = main(
        [
            "backfill-campaign-runs",
            str(campaign_id),
            "--database",
            str(database),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run-link backfill complete." in captured.out


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
        "I finished the run; objective completion is unverified.",
    ]


def test_commentary_does_not_call_a_safe_abort_objective_success() -> None:
    commentary = _commentary(
        [],
        "success",
        None,
        {"experience": {"change": 0}, "confirmed_kills": []},
        2,
        objective_outcome="not_achieved",
        safety_outcome="safe",
    )

    assert commentary[-1] == "I finished safely, but did not achieve the objective."


def test_cached_summary_ending_tracks_its_objective_outcome(tmp_path) -> None:
    database = _create_report_run(tmp_path, status="success", error=None)

    with RunStorage(database) as storage:
        summary = storage.get_run_summary(1)
        assert summary is not None
        summary["outcomes"]["objective"] = "not_achieved"
        summary["outcomes"]["safety"] = "safe"
        summary["commentary"][-1] = "I completed the run successfully."
        storage.save_run_summary(1, summary)
        report = build_run_report(storage, 1)

    assert report["commentary"][-1] == "I finished safely, but did not achieve the objective."


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
                "title": "the Procedurally Curious",
                "description": "Reportmage keeps a brass astrolabe and distrusts shortcuts.",
                "personality": "patient, observant, and dryly funny",
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
