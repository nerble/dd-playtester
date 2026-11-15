import json

import pytest

from dd4tester.report import render_markdown
from dd4tester.storage import RunStorage


@pytest.mark.parametrize("queued", [False, True])
def test_failed_fights_survive_compact_summary_and_storage_restart(tmp_path, queued):
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="pilot", config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml", target_level=100,
        )
        initial = {"level": 46, "xp": 1000, "hp": 1000, "max_hp": 1000}
        segment_id = storage.start_campaign_segment(
            campaign_id, phase="source-ranked-hunt-test-1-100-46", start_state=initial,
        )
        run_id = storage.create_run(scenario_name="failed fight", scenario_path=tmp_path / "scenario.yaml")
        write = storage.queue_observation if queued else storage.record_event

        def enemies(value):
            write(run_id, kind="game_event", payload={
                "type": "enemies_changed", "data": {"value": value},
            })

        enemies([[{"name": "a guard", "isnpc": "1"}]])
        write(run_id, kind="game_event", payload={"type": "combat_started"})
        # A malformed observation must not invent an empty room or a new fight.
        enemies("not json")
        enemies([[{"name": "a guard", "isnpc": "1"}]])
        write(run_id, kind="decision", payload={"category": "combat", "command": "kick"})
        enemies([])
        enemies(json.dumps([[{"name": "another guard", "isnpc": "2"}]]))
        write(run_id, kind="decision", payload={"command": "kill #2", "stage": "combat"})
        storage.finish_run(run_id, status="success", build_summary=False)

    with RunStorage(database) as storage:
        statements = []
        storage.connection.set_trace_callback(statements.append)
        storage.finish_campaign_segment(
            segment_id, status="success", run_id=run_id,
            end_state={**initial, "xp": 950}, command_count=2, duration_seconds=30,
            objective_outcome="not_achieved", safety_outcome="loss",
        )
        summary = storage.get_run_summary(run_id)
        assert summary["progress"]["combat_starts"] == 2
        assert summary["progress"]["combat_decisions"] == 2
        assert summary["progress"]["confirmed_kills"] == []
        assert summary["outcomes"]["objective"] == "not_achieved"
        assert summary["evidence"]["combat_metrics_basis"] == "observed_events"
        assert not any("FROM EVENTS" in statement.upper() for statement in statements)


def test_legacy_compact_report_labels_unobserved_counts(tmp_path):
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        run_id = storage.create_run(scenario_name="legacy fight", scenario_path=tmp_path / "scenario.yaml")
        run = dict(storage.get_run(run_id))
    report = {
        "run": run, "progress": {"combat_starts": 0, "combat_decisions": 0},
        "evidence": {"compact": True},
    }
    text = render_markdown(report)
    assert "Combat starts (known minimum): 0" in text
    assert "Combat decisions (known minimum): unknown" in text


def test_multiple_kills_do_not_invent_multiple_fights(tmp_path):
    from collections import Counter
    from dd4tester.report import _progress_summary

    progress = _progress_summary(
        {}, {}, [], Counter(), [{"payload": {"type": "combat_started"}}], [],
        [{"mob_name": "first guard"}, {"mob_name": "second guard"}], [],
    )
    assert progress["combat_starts"] == 1
