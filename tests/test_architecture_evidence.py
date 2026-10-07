import json
import threading
from dataclasses import fields
from pathlib import Path

import pytest

from dd4tester import starter as starter_module
from dd4tester.campaign import (
    _campaign_deferred_practice_types,
    _campaign_practice_types_spent,
    _campaign_rejected_practice_skills,
    _interrupted_provision_funding_evidence,
)
from dd4tester.report import (
    _activity_metrics,
    _objective_outcome,
    build_campaign_report,
    build_run_report,
    render_campaign_markdown,
    render_markdown,
)
from dd4tester.report_migrations import migrate_legacy_run_context
import dd4tester.storage as storage_module
from dd4tester.storage import RUN_REPORT_SUMMARY_VERSION, RunStorage
from dd4tester.state import CharacterState


def test_compact_projection_covers_every_durable_character_field() -> None:
    transient = {"enemies", "acquired_items", "last_prompt"}
    expected = {
        item.name for item in fields(CharacterState)
        if item.name not in transient
    }
    state = CharacterState(
        inventory=[{"name": "ration"}],
        equipment=[{"name": "sword"}],
    )

    compact = state.to_compact_dict()

    assert set(compact) == expected
    assert compact["world_boot_id"] is None
    compact["inventory"][0]["name"] = "changed copy"
    assert state.inventory == [{"name": "ration"}]


def test_routine_cooldown_events_use_the_bounded_writer_without_a_barrier() -> None:
    assert "quest_cooldown" not in starter_module._STORAGE_BARRIER_EVENT_KINDS
    assert {
        "run_context", "quest_request_attempt", "quest_phase_checkpoint",
        "quest_phase_started",
    } == starter_module._STORAGE_BARRIER_EVENT_KINDS


def test_current_training_audit_skips_historical_event_scans() -> None:
    class NoHistoryReads:
        def list_campaign_game_events(self, *_args, **_kwargs):
            raise AssertionError("a current training audit should be reused")

    state = {
        "level": 29,
        "world_boot_id": "boot-1",
        "campaign_training_audit": {
            "observed": True,
            "level": 29,
            "boot_id": "boot-1",
            "known_skill_levels": {"enhanced damage": 67},
        },
    }
    storage = NoHistoryReads()

    assert _campaign_practice_types_spent(
        storage, 7, level=29, state=state,
    ) == frozenset()
    assert _campaign_deferred_practice_types(
        storage, 7, level=29, state=state,
    ) == frozenset()
    assert _campaign_rejected_practice_skills(
        storage, 7, level=29, character_class="warrior", state=state,
    ) == frozenset()


def test_stale_training_audit_keeps_historical_fallback() -> None:
    class CountingHistory:
        calls = 0

        def list_campaign_game_events(self, *_args, **_kwargs):
            self.calls += 1
            return []

    state = {
        "level": 29,
        "world_boot_id": "boot-1",
        "campaign_training_audit": {
            "observed": True,
            "level": 29,
            "boot_id": "older-boot",
            "known_skill_levels": {"enhanced damage": 67},
        },
    }
    storage = CountingHistory()

    _campaign_practice_types_spent(storage, 7, level=29, state=state)
    _campaign_deferred_practice_types(storage, 7, level=29, state=state)
    _campaign_rejected_practice_skills(
        storage, 7, level=29, character_class="warrior", state=state,
    )

    assert storage.calls == 3


def _experiment_starting_state(name: str = "Evidence") -> dict[str, object]:
    return {
        "name": name,
        "race": "human",
        "sex": "neuter",
        "character_class": "warrior",
        "subclass": "knight",
        "level": 29,
        "xp": 599_621,
        "world_boot_id": "boot-1",
        "room_vnum": "3054",
        "hp": 666,
        "max_hp": 666,
        "mana": 100,
        "max_mana": 100,
        "move": 482,
        "max_move": 482,
        "stats": {"str": 26, "con": 24},
        "currencies": {"copper": 1_000},
        "inventory": [{"name": "pie", "quantity": 1}],
        "equipment": [{"name": "branch", "vnum": 6104}],
        "quest_points": 0,
        "total_quest_points": 0,
    }


def test_queued_observations_keep_one_event_and_sparse_checkpoints(
    tmp_path, monkeypatch,
) -> None:
    database = tmp_path / "runs.sqlite3"
    storage = RunStorage(database, event_commit_interval=100)
    run_id = storage.create_run(
        scenario_name="starter:Evidence",
        scenario_path=Path("character.yaml"),
    )
    caller_thread = threading.get_ident()
    writer_threads: list[int] = []
    write_item = storage_module._BoundedObservationWriter._write_item

    def track_writer_thread(connection, item):
        writer_threads.append(threading.get_ident())
        return write_item(connection, item)

    monkeypatch.setattr(
        storage_module._BoundedObservationWriter,
        "_write_item",
        staticmethod(track_writer_thread),
    )
    storage.queue_observation(
        run_id,
        kind="game_event",
        timestamp="2026-10-03T00:00:01+00:00",
        payload={"type": "vitals_changed", "source": "gmcp", "data": {}},
        current_state={"name": "Evidence", "level": 1, "revision": 1},
    )
    storage.queue_observation(
        run_id,
        kind="game_event",
        timestamp="2026-10-03T00:00:02+00:00",
        payload={"type": "progress_changed", "source": "gmcp", "data": {}},
        current_state={
            "name": "Evidence", "level": 2, "xp": 100,
            "hp": 30, "max_hp": 30, "dead": False, "revision": 2,
            "inventory": [{"name": "ration"}],
            "equipment": [{"name": "sword"}],
            "enemies": [{"name": "transient crowd", "details": "large"}],
            "last_prompt": {"text": "duplicate prompt payload"},
        },
    )
    storage.queue_observation(
        run_id,
        kind="state_snapshot",
        timestamp="2026-10-03T00:00:03+00:00",
        payload={
            "reason": "prompt_seen",
            "source": "text",
            "state": {
                "name": "Evidence", "level": 2, "xp": 100,
                "hp": 30, "max_hp": 30, "revision": 2,
                "inventory": [{"name": "ration"}],
                "equipment": [{"name": "sword"}],
                "unbounded_detail": "must remain transcript-only",
            },
        },
    )
    storage.finish_run(
        run_id,
        status="success",
        execution_status="completed",
        objective_outcome="achieved",
        safety_outcome="safe",
    )

    events = storage.list_events(run_id)
    snapshots = storage.list_state_snapshots(run_id)
    latest = storage.get_latest_state_snapshot(run_id)
    summary = storage.get_run_summary(run_id)
    compact_index_count = storage.connection.execute(
        "SELECT COUNT(*) FROM campaign_game_event_lookup WHERE run_id = ?",
        (run_id,),
    ).fetchone()[0]
    legacy_payload_count = storage.connection.execute(
        "SELECT COUNT(*) FROM campaign_game_event_index WHERE run_id = ?",
        (run_id,),
    ).fetchone()[0]
    current_state_count = storage.connection.execute(
        "SELECT COUNT(*) FROM run_current_states WHERE run_id = ?",
        (run_id,),
    ).fetchone()[0]

    assert [row["kind"] for row in events] == [
        "game_event", "game_event", "state_snapshot",
    ]
    compact_event = json.loads(events[2]["payload_json"])
    assert compact_event == {"reason": "prompt_seen", "source": "text"}
    assert len(events[2]["payload_json"]) < 100
    assert compact_index_count == 2
    assert legacy_payload_count == 0
    assert current_state_count == 1
    assert writer_threads
    assert all(thread_id != caller_thread for thread_id in writer_threads)
    assert [row["reason"] for row in snapshots] == [
        "initial_state", "run_finished",
    ]
    assert json.loads(latest["state_json"])["revision"] == 2
    current_state = storage.connection.execute(
        "SELECT state_json FROM run_current_states WHERE run_id = ?",
        (run_id,),
    ).fetchone()
    compact_state = json.loads(current_state["state_json"])
    assert compact_state["inventory"] == [{"name": "ration"}]
    assert compact_state["equipment"] == [{"name": "sword"}]
    assert "enemies" not in compact_state
    assert "last_prompt" not in compact_state
    progress_checkpoint = json.loads(snapshots[0]["state_json"])
    assert progress_checkpoint["enemies"] == [
        {"name": "transient crowd", "details": "large"},
    ]
    assert summary is not None
    assert summary["outcomes"] == {
        "execution": "completed",
        "objective": "achieved",
        "safety": "safe",
    }

    storage.list_events = lambda *_args, **_kwargs: (_ for _ in ()).throw(
        AssertionError("completed reports should use the saved run summary")
    )
    assert build_run_report(storage, run_id)["outcomes"]["objective"] == "achieved"
    storage.close()


def test_item_events_and_level_boundaries_replace_repeated_full_snapshots(
    tmp_path,
) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database, event_commit_interval=100) as storage:
        run_id = storage.create_run(
            scenario_name="starter:Evidence",
            scenario_path=tmp_path / "character.yaml",
        )
        for index in range(25):
            storage.queue_observation(
                run_id,
                kind="game_event",
                payload={
                    "type": "item_acquired",
                    "source": "gmcp",
                    "data": {"item": f"a test relic {index}"},
                },
                current_state={
                    "name": "Evidence",
                    "level": 29,
                    "xp": 100 + index,
                    "hp": 80,
                    "max_hp": 100,
                    "revision": index + 1,
                    "inventory": [{"name": f"a test relic {index}"}],
                    "acquired_items": [
                        {"item": f"a test relic {prior}"}
                        for prior in range(index + 1)
                    ],
                    "enemies": [],
                    "last_prompt": {"text": "transient"},
                },
            )
        storage.queue_observation(
            run_id,
            kind="game_event",
            payload={"type": "progress_changed", "source": "gmcp", "data": {}},
            current_state={
                "name": "Evidence", "level": 30, "xp": 200,
                "hp": 80, "max_hp": 100, "revision": 26,
            },
        )
        storage.queue_observation(
            run_id,
            kind="game_event",
            payload={"type": "progress_changed", "source": "gmcp", "data": {}},
            current_state={
                "name": "Evidence", "level": 30, "xp": 201,
                "hp": 80, "max_hp": 100, "revision": 27,
            },
        )
        storage.flush()
        latest_live_state = storage.get_latest_state_snapshot(run_id)
        assert latest_live_state["reason"] == "current_state"
        assert json.loads(latest_live_state["state_json"])["xp"] == 201
        storage.finish_run(run_id, status="success")

        snapshots = storage.list_state_snapshots(run_id)
        acquired = storage.connection.execute(
            """
            SELECT item_description, first_event_id
            FROM character_acquired_items
            WHERE character_name = ? COLLATE NOCASE
            ORDER BY item_description
            """,
            ("Evidence",),
        ).fetchall()
        has_item_evidence = storage.character_has_acquired_item(
            "Evidence", "test relic 0",
        )
        current_state = json.loads(
            storage.connection.execute(
                "SELECT state_json FROM run_current_states WHERE run_id = ?",
                (run_id,),
            ).fetchone()["state_json"]
        )

    assert [row["reason"] for row in snapshots] == [
        "initial_state", "level_changed", "run_finished",
    ]
    assert len(acquired) == 25
    assert all(row["first_event_id"] is not None for row in acquired)
    assert has_item_evidence
    assert "acquired_items" not in current_state
    assert "enemies" not in current_state
    assert "last_prompt" not in current_state


def test_live_state_writes_coalesce_until_the_writer_barrier(
    tmp_path, monkeypatch,
) -> None:
    database = tmp_path / "runs.sqlite3"
    storage = RunStorage(database, event_commit_interval=100)
    run_id = storage.create_run(
        scenario_name="starter:Evidence",
        scenario_path=tmp_path / "character.yaml",
    )
    storage.connection.executescript(
        """
        CREATE TABLE current_state_write_counts (run_id INTEGER);
        CREATE TRIGGER count_current_state_insert
        AFTER INSERT ON run_current_states
        BEGIN
            INSERT INTO current_state_write_counts VALUES (NEW.run_id);
        END;
        CREATE TRIGGER count_current_state_update
        AFTER UPDATE ON run_current_states
        BEGIN
            INSERT INTO current_state_write_counts VALUES (NEW.run_id);
        END;
        """
    )
    writer_started = threading.Event()
    release_writer = threading.Event()
    original_write_item = storage_module._BoundedObservationWriter._write_item
    first_item = True

    def hold_first_item(connection, item):
        nonlocal first_item
        if first_item:
            first_item = False
            writer_started.set()
            assert release_writer.wait(2)
        return original_write_item(connection, item)

    monkeypatch.setattr(
        storage_module._BoundedObservationWriter,
        "_write_item",
        staticmethod(hold_first_item),
    )
    try:
        storage.queue_observation(
            run_id,
            kind="game_event",
            payload={"type": "vitals_changed", "source": "gmcp", "data": {}},
            current_state={"name": "Evidence", "level": 1, "xp": 10, "revision": 1},
        )
        assert writer_started.wait(2)
        storage.queue_observation(
            run_id,
            kind="game_event",
            payload={"type": "vitals_changed", "source": "gmcp", "data": {}},
            current_state={"name": "Evidence", "level": 1, "xp": 20, "revision": 2},
        )
    finally:
        release_writer.set()
    storage.flush()

    count = storage.connection.execute(
        "SELECT COUNT(*) FROM current_state_write_counts WHERE run_id = ?",
        (run_id,),
    ).fetchone()[0]
    current = storage.get_latest_character_state("Evidence")
    assert count == 1
    assert current["xp"] == 20
    storage.close()


def test_first_complete_observation_preserves_run_start_metrics(tmp_path) -> None:
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        run_id = storage.create_run(
            scenario_name="starter:Evidence",
            scenario_path=tmp_path / "character.yaml",
        )
        storage.queue_observation(
            run_id,
            kind="game_event",
            payload={"type": "vitals_changed", "source": "gmcp", "data": {}},
            current_state={
                "name": "Evidence", "level": 29, "xp": 100,
                "hp": 80, "max_hp": 100, "dead": False,
            },
        )
        storage.finish_run(run_id, status="success")

        report = build_run_report(storage, run_id)
        reasons = [
            row["reason"] for row in storage.list_state_snapshots(run_id)
        ]

    assert reasons == ["initial_state", "run_finished"]
    assert report["progress"]["experience"] == {
        "initial": 100, "final": 100, "change": 0,
    }


def test_activity_metrics_account_for_combat_travel_maintenance_and_waiting() -> None:
    start = "2026-10-03T00:00:00+00:00"
    finish = "2026-10-03T00:00:10+00:00"
    events = [
        {
            "timestamp": "2026-10-03T00:00:02+00:00",
            "kind": "command", "payload": {"command": "north"},
        },
        {
            "timestamp": "2026-10-03T00:00:05+00:00",
            "kind": "command", "payload": {"command": "kill wolf"},
        },
        {
            "timestamp": "2026-10-03T00:00:08+00:00",
            "kind": "command", "payload": {"command": "inventory"},
        },
    ]

    metrics = _activity_metrics(events, start, finish)

    assert metrics["total_seconds"] == 10
    assert metrics["waiting_seconds"] == 2
    assert metrics["travel_seconds"] == 3
    assert metrics["productive_combat_seconds"] == 3
    assert metrics["maintenance_seconds"] == 2
    assert metrics["basis"] == "estimated"


def test_objective_outcome_does_not_equate_success_status_with_completion() -> None:
    assert _objective_outcome(
        {"objective": {"level": 100}},
        {"level": 29},
        [],
        [],
    ) == "not_achieved"
    assert _objective_outcome(
        {"objective": {"level": 2}},
        {"level": 29},
        [],
        [],
        scenario_name="restock:Dorrik",
    ) == "unknown"
    assert _objective_outcome(
        {"objective": {"level": 2}},
        {"level": 2},
        [],
        [],
        scenario_name="starter:Evidence",
    ) == "achieved"


def test_bounded_probe_and_arena_objectives_override_level_ceiling() -> None:
    assert _objective_outcome(
        {"objective": {"level": 100, "arena_kill_limit": 2}},
        {"level": 29},
        [{}, {}],
        [],
    ) == "achieved"
    assert _objective_outcome(
        {"objective": {"level": 100, "world_time_probe": True}},
        {"level": 29},
        [],
        [
            {"kind": "command", "payload": {"command": "time"}},
            {
                "kind": "response",
                "payload": {
                    "text": (
                        "It is 7 o'clock pm, Day of Midian, 1st of the Month of Midian.\n"
                        "DD was started at Fri Sep 4 06:19:51 2026\n"
                        "DD has been running for less than a minute."
                    ),
                },
            },
        ],
    ) == "achieved"


def test_objective_outcome_requires_level_and_required_items() -> None:
    context = {
        "objective": {
            "level": 100,
            "fastwalk_hunt_stop_boundaries": [
                {"actions": ["get blackberries"]},
            ],
        },
    }
    assert _objective_outcome(context, {"level": 100}, [], []) == "not_achieved"
    assert _objective_outcome(
        context,
        {"level": 100},
        [],
        [{
            "kind": "game_event",
            "payload": {
                "type": "item_acquired",
                "data": {"item": "a handful of blackberries"},
            },
        }],
    ) == "achieved"


def test_quest_reward_and_level_checkpoint_survive_database_reopen(
    tmp_path,
) -> None:
    database = tmp_path / "runs.sqlite3"
    initial = {
        "name": "Dorrik",
        "level": 29,
        "xp": 609_449,
        "hp": 676,
        "max_hp": 676,
        "dead": False,
        "quest_points": 0,
        "total_quest_points": 0,
    }
    final = {
        **initial,
        "level": 30,
        "xp": 614_000,
        "quest_points": 1,
        "total_quest_points": 1,
    }

    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Dorrik to HERO",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=100,
        )
        run_id = storage.create_run(
            scenario_name="hero:Dorrik",
            scenario_path=tmp_path / "character.yaml",
        )
        storage.record_event(
            run_id,
            kind="run_context",
            payload={
                "character": {"name": "Dorrik"},
                "objective": {
                    "kind": "quest_reward",
                    "initial_total_quest_points": 0,
                    "required_level": 30,
                },
            },
        )
        storage.queue_observation(
            run_id,
            kind="game_event",
            payload={
                "type": "vitals_changed",
                "source": "gmcp",
                "data": {},
            },
            current_state=initial,
        )
        storage.queue_observation(
            run_id,
            kind="game_event",
            payload={
                "type": "quest_status_changed",
                "source": "gmcp",
                "data": {"points": 1, "total_points": 1},
            },
            current_state=final,
        )
        storage.finish_run(
            run_id,
            status="success",
            execution_status="success",
            safety_outcome="safe",
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=None,
            run_id=run_id,
            phase="quest-complete",
            reason="verified quest reward and level transition",
            state=final,
        )

    with RunStorage(database, read_only=True) as reopened:
        report = build_run_report(reopened, run_id)
        checkpoint = reopened.get_latest_campaign_checkpoint(campaign_id)

    assert report["outcomes"] == {
        "execution": "success",
        "objective": "achieved",
        "safety": "safe",
    }
    assert report["progress"]["level"]["change"] == 1
    assert checkpoint is not None
    restored = json.loads(checkpoint["state_json"])
    assert restored["level"] == 30
    assert restored["total_quest_points"] == 1


def test_city_restock_objective_requires_pie_fill_drink_and_healer_return() -> None:
    context = {
        "objective": {
            "kind": "city_restock",
            "required_items": ["a big pot pie"],
            "required_command_responses": [
                {
                    "command": "fill skin",
                    "response_contains": "You fill a buffalo water skin with water.",
                },
                {
                    "command": "drink skin",
                    "response_contains": "You drink water from a buffalo water skin.",
                },
            ],
            "required_final_room_vnum": "3054",
        },
    }
    final_state = {
        "room_vnum": "3054",
        "inventory": '[[{"quan":"1","short_desc":"a big pot pie"}]]',
    }
    events = [
        {"kind": "command", "payload": {"command": "fill skin"}},
        {
            "kind": "response",
            "payload": {"text": "You fill a buffalo water skin "},
        },
        {
            "kind": "response",
            "payload": {"text": "with water."},
        },
        {"kind": "command", "payload": {"command": "drink skin"}},
        {
            "kind": "response",
            "payload": {"text": "You drink water from a buffalo water skin."},
        },
    ]

    assert _objective_outcome(context, final_state, [], events) == "achieved"
    assert _objective_outcome(
        context,
        {**final_state, "inventory": "[]"},
        [],
        events,
    ) == "not_achieved"
    assert _objective_outcome(
        context,
        {**final_state, "room_vnum": "3009"},
        [],
        events,
    ) == "not_achieved"
    assert _objective_outcome(
        context,
        final_state,
        [],
        [*events[:2], {"kind": "command", "payload": {"command": "drink skin"}}],
    ) == "not_achieved"


def test_required_item_objective_needs_distinct_acquisitions() -> None:
    context = {
        "objective": {
            "required_items": ["pink ice ring", "pink ice ring"],
        },
    }
    one_ring = [{
        "kind": "game_event",
        "payload": {
            "type": "item_acquired",
            "data": {"item": "a pink ice ring"},
        },
    }]
    assert _objective_outcome(context, {}, [], one_ring) == "not_achieved"
    assert _objective_outcome(context, {}, [], [*one_ring, *one_ring]) == "achieved"
    assert _objective_outcome(
        context,
        {"inventory": '[[{"quan":"2","short_desc":"a pink ice ring"}]]'},
        [],
        [],
    ) == "achieved"


def test_legacy_food_route_uses_stop_items_not_its_route_label() -> None:
    raw_context = {
        "objective": {
            "fastwalk_route": "source food reserve wabbit 331",
            "fastwalk_hunt_stop_boundaries": [
                {"required_items": ["a rabbit roast"]},
                {"required_items": ["a small dusk of timian herbs"]},
            ],
        },
    }
    context = migrate_legacy_run_context(raw_context)

    assert "required_items" not in context["objective"]
    inventory = {
        "inventory": (
            '[[{"quan":"1","short_desc":"a rabbit roast"},'
            '{"quan":"1","short_desc":"a small dusk of timian herbs"}]]'
        ),
    }
    assert _objective_outcome(context, inventory, [], []) == "achieved"

    stale_context = {
        "objective": {
            **raw_context["objective"],
            "required_items": ["wabbit"],
            "required_items_source": "legacy_source_food_route",
        },
    }
    migrated = migrate_legacy_run_context(stale_context)
    assert "required_items" not in migrated["objective"]
    assert _objective_outcome(migrated, inventory, [], []) == "achieved"


def test_world_time_probe_requires_a_response_not_just_a_command() -> None:
    context = {"objective": {"world_time_probe": True}}
    command = {"kind": "command", "payload": {"command": "time"}}
    assert _objective_outcome(context, {}, [], [command]) == "not_achieved"
    assert _objective_outcome(
        context, {}, [],
        [command, {"kind": "response", "payload": {"text": "Huh?"}}],
    ) == "not_achieved"
    assert _objective_outcome(
        context,
        {},
        [],
        [
            command,
            {
                "kind": "response",
                "payload": {
                    "text": (
                        "It is 7 o'clock pm, Day of Midian, 1st of the Month of Midian.\n"
                        "DD was started at Fri Sep 4 06:19:51 2026\n"
                        "DD has been running for less than a minute."
                    ),
                },
            },
        ],
    ) == "achieved"


def test_quest_reward_requires_a_verified_positive_point_delta() -> None:
    context = {
        "objective": {
            "kind": "quest_reward",
            "level": 2,
            "fastwalk_route": "questmaster goldmoon request",
            "initial_total_quest_points": 0,
        },
    }
    initial = {"level": 29, "total_quest_points": 0}
    aborted = {
        "level": 29,
        "quest_points": 0,
        "total_quest_points": 0,
        "quest_status": {"status": "cooldown", "total_points": 0},
    }
    request_and_abort = [
        {"kind": "quest_request_attempt", "payload": {"attempted": True}},
        {
            "kind": "game_event",
            "payload": {
                "type": "quest_status_changed",
                "data": {"status": "cooldown", "total_points": "0"},
            },
        },
    ]
    assert _objective_outcome(
        context, aborted, [], request_and_abort, initial_state=initial,
    ) == "not_achieved"

    rewarded = {**aborted, "quest_points": 12, "total_quest_points": 12}
    assert _objective_outcome(
        context, rewarded, [], request_and_abort, initial_state=initial,
    ) == "achieved"

    transition_objective = {
        "objective": {
            **context["objective"],
            "required_level": 30,
        },
    }
    assert _objective_outcome(
        transition_objective,
        {**rewarded, "level": 29},
        [],
        request_and_abort,
        initial_state=initial,
    ) == "not_achieved"
    assert _objective_outcome(
        transition_objective,
        {**rewarded, "level": 30},
        [],
        request_and_abort,
        initial_state=initial,
    ) == "achieved"


def test_quest_reward_and_level_checkpoint_survive_storage_reopen(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    start = {
        "name": "Evidence", "level": 29, "xp": 599621,
        "hp": 100, "max_hp": 100, "dead": False,
        "quest_points": 0, "total_quest_points": 0, "xp_loss_total": 0,
    }
    finish = {
        **start, "level": 30, "xp": 613900,
        "quest_points": 1, "total_quest_points": 1,
    }
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Quest level gate",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=30,
        )
        segment_id = storage.start_campaign_segment(
            campaign_id, phase="verified-quest-level-30", start_state=start,
        )
        run_id = storage.create_run(
            scenario_name="quest-reward:Evidence",
            scenario_path=tmp_path / "quest.yaml",
        )
        storage.record_event(
            run_id,
            kind="run_context",
            payload={
                "character": {"name": "Evidence"},
                "objective": {
                    "kind": "quest_reward",
                    "initial_total_quest_points": 0,
                    "required_level": 30,
                },
            },
        )
        storage.record_state_snapshot(
            run_id, source_event_id=None, reason="initial_state", state=start,
        )
        storage.record_event(
            run_id,
            kind="quest_request_attempt",
            payload={"attempted": True},
        )
        storage.queue_observation(
            run_id,
            kind="game_event",
            payload={
                "type": "quest_status_changed",
                "source": "gmcp",
                "data": {"status": "complete", "total_points": 1},
            },
            current_state=finish,
        )
        storage.finish_run(
            run_id,
            status="success",
            execution_status="success",
            safety_outcome="safe",
        )
        storage.finish_campaign_segment(
            segment_id,
            status="success",
            run_id=run_id,
            end_state=finish,
            command_count=12,
            duration_seconds=45,
            objective_outcome="achieved",
            safety_outcome="safe",
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=segment_id,
            run_id=run_id,
            phase="level-30",
            reason="segment_complete",
            state=finish,
        )

    with RunStorage(database) as storage:
        run_report = build_run_report(storage, run_id)
        campaign_report = build_campaign_report(storage, campaign_id)
        checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)

    assert run_report["outcomes"] == {
        "execution": "success", "objective": "achieved", "safety": "safe",
    }
    assert campaign_report["progress"]["final_level"] == 30
    assert checkpoint is not None
    assert json.loads(checkpoint["state_json"])["total_quest_points"] == 1


def test_linked_run_contract_overrides_campaign_side_effect_inference(tmp_path) -> None:
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        campaign_id = storage.create_campaign(
            name="Objective evidence",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=30,
        )
        run_id = storage.create_run(
            scenario_name="fastwalk-source-food:Dorrik",
            scenario_path=tmp_path / "character.yaml",
        )
        storage.record_event(
            run_id,
            kind="run_context",
            payload={
                "character": {"name": "Dorrik"},
                "objective": {"required_items": ["blackberries"]},
            },
        )
        storage.finish_run(
            run_id,
            status="success",
            execution_status="success",
            objective_outcome="achieved",
            safety_outcome="safe",
        )
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="source-food-reserve",
            start_state={
                "name": "Dorrik", "level": 29, "quest_points": 0,
                "xp_loss_total": 0,
            },
        )
        storage.finish_campaign_segment(
            segment_id,
            status="success",
            execution_status="misleading-caller-value",
            objective_outcome="achieved",
            safety_outcome="unsafe",
            run_id=run_id,
            end_state={
                "name": "Dorrik", "level": 30, "quest_points": 1,
                "xp_loss_total": 0, "dead": False,
            },
            command_count=18,
            duration_seconds=80,
        )
        run_report = build_run_report(storage, run_id)
        campaign_report = build_campaign_report(storage, campaign_id)
        segment = storage.connection.execute(
            """
            SELECT execution_status, objective_outcome, safety_outcome
            FROM campaign_segments WHERE id = ?
            """,
            (segment_id,),
        ).fetchone()

    assert segment["execution_status"] == "success"
    assert segment["objective_outcome"] == "not_achieved"
    assert segment["safety_outcome"] == "safe"
    assert campaign_report["totals"]["outcomes"]["objective"] == {
        "not_achieved": 1,
    }
    assert run_report["outcomes"] == {
        "execution": "success",
        "objective": "not_achieved",
        "safety": "safe",
    }
    markdown = render_markdown(run_report)
    assert "Run record: **finished**" in markdown
    assert "objective: **not_achieved**" in markdown
    assert "Objective: not_achieved 1" in render_campaign_markdown(campaign_report)


def test_campaign_segment_can_override_linked_run_objective_scope(tmp_path) -> None:
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        campaign_id = storage.create_campaign(
            name="funding",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=100,
        )
        run_id = storage.create_run(
            scenario_name="fastwalk-provision funding representative:Evidence",
            scenario_path=tmp_path / "character.yaml",
        )
        storage.record_event(
            run_id,
            kind="run_context",
            payload={
                "character": {"name": "Evidence"},
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
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="provision-funding",
            start_state={"name": "Evidence", "level": 29, "xp_loss_total": 0},
        )
        storage.finish_campaign_segment(
            segment_id,
            status="ready",
            run_id=run_id,
            end_state={"name": "Evidence", "level": 29, "dead": False},
            command_count=1,
            duration_seconds=1,
            execution_status="interrupted",
            objective_outcome="achieved",
            safety_outcome="safe",
            prefer_segment_objective_outcome=True,
        )
        storage.save_run_summary(
            run_id,
            {
                "outcomes": {
                    "execution": "interrupted",
                    "objective": "not_achieved",
                    "safety": "safe",
                }
            },
        )
        run = storage.get_run(run_id)
        segment = storage.list_campaign_segments(campaign_id)[0]

    assert run is not None and run["objective_outcome"] == "not_achieved"
    assert segment["execution_status"] == "interrupted"
    assert segment["objective_outcome"] == "achieved"
    assert segment["safety_outcome"] == "safe"


def test_interrupted_funding_requires_exact_source_kill_and_coin_gain(tmp_path) -> None:
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        run_id = storage.create_run(
            scenario_name="fastwalk-provision funding representative:Evidence",
            scenario_path=tmp_path / "character.yaml",
        )
        storage.record_event(
            run_id,
            kind="run_context",
            payload={
                "character": {"name": "Evidence"},
                "objective": {
                    "level": 29,
                    "fastwalk_route": "provision funding representative 10302",
                    "fastwalk_hunt_stop_boundaries": [
                        {
                            "route_endpoint": "10302",
                            "target": "foreign trade representative",
                            "required_items": [],
                        }
                    ],
                },
            },
        )
        storage.finish_run(
            run_id,
            status="failed",
            execution_status="interrupted",
        )
        start_state = {"level": 29, "currencies": {"copper": 8}}
        end_state = {
            "level": 29,
            "currencies": {"gold": 22, "silver": 91, "copper": 9}
        }
        kills = [
            {
                "mob_name": "Foreign Trade Representative",
                "source_mobile_vnum": 10245,
                "source_policy_id": (
                    "source-ranked-hunt-solace-10245-10302-29"
                ),
            }
        ]

        evidence = _interrupted_provision_funding_evidence(
            storage,
            run_id,
            start_state=start_state,
            end_state=end_state,
            objective_kills=kills,
        )
        no_currency = _interrupted_provision_funding_evidence(
            storage,
            run_id,
            start_state=start_state,
            end_state=start_state,
            objective_kills=kills,
        )

    assert evidence == {
        "candidate_key": "solace.are:10245:10302",
        "target": "Foreign Trade Representative",
        "room_vnum": 10302,
        "mobile_vnum": 10245,
        "source_policy_id": "source-ranked-hunt-solace-10245-10302-29",
        "currency_delta": 3111,
        "run_id": run_id,
        "level": 29,
    }
    assert no_currency is None


def test_stale_report_summary_is_rebuilt_from_quest_evidence(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        run_id = storage.create_run(
            scenario_name="quest-request:Evidence",
            scenario_path=tmp_path / "quest.yaml",
        )
        storage.record_event(
            run_id,
            kind="run_context",
            payload={
                "character": {"name": "Evidence"},
                "objective": {
                    "kind": "quest_reward",
                    "level": 2,
                    "fastwalk_route": "questmaster goldmoon request",
                    "initial_total_quest_points": 0,
                },
            },
        )
        initial = {
            "name": "Evidence", "level": 29, "xp": 1000,
            "hp": 100, "max_hp": 100, "dead": False,
            "quest_points": 0, "total_quest_points": 0,
        }
        final = {
            **initial,
            "quest_status": {
                "active": 0, "status": "cooldown", "total_points": 0,
            },
        }
        storage.record_state_snapshot(
            run_id,
            source_event_id=None,
            reason="initial_state",
            state=initial,
        )
        storage.record_event(
            run_id,
            kind="quest_request_attempt",
            payload={"attempted": True},
        )
        storage.queue_observation(
            run_id,
            kind="game_event",
            payload={
                "type": "quest_status_changed",
                "source": "gmcp",
                "data": {"active": "0", "status": "cooldown", "total_points": "0"},
            },
            current_state=final,
        )
        storage.finish_run(
            run_id,
            status="success",
            execution_status="success",
            safety_outcome="safe",
        )
        summary = storage.get_run_summary(run_id)
        assert summary is not None
        summary["summary_version"] = RUN_REPORT_SUMMARY_VERSION - 1
        summary["outcomes"]["objective"] = "achieved"
        storage.connection.execute(
            "UPDATE run_summaries SET summary_json = ? WHERE run_id = ?",
            (json.dumps(summary, sort_keys=True), run_id),
        )
        storage.connection.execute(
            "UPDATE runs SET objective_outcome = 'achieved' WHERE id = ?",
            (run_id,),
        )
        storage.connection.commit()

        report = build_run_report(storage, run_id)
        run = storage.get_run(run_id)
        refreshed = storage.get_run_summary(run_id)

    assert report["outcomes"] == {
        "execution": "success",
        "objective": "not_achieved",
        "safety": "safe",
    }
    assert run["objective_outcome"] == "not_achieved"
    assert refreshed["summary_version"] == RUN_REPORT_SUMMARY_VERSION


def test_campaign_report_uses_compact_segment_and_checkpoint_queries(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Evidence campaign",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=30,
        )
        start = {"name": "Evidence", "level": 29, "xp": 100, "xp_loss_total": 0}
        end = {
            **start, "level": 30, "xp": 0, "quest_points": 4,
            "dead": False, "xp_loss_total": 0,
        }
        segment_id = storage.start_campaign_segment(
            campaign_id, phase="quest-level-transition", start_state=start,
        )
        storage.finish_campaign_segment(
            segment_id,
            status="success",
            run_id=None,
            end_state=end,
            command_count=12,
            duration_seconds=45,
            objective_outcome="achieved",
            safety_outcome="safe",
            metrics={"activity": {"productive_combat_seconds": 8}},
        )
        storage.record_campaign_checkpoint(
            campaign_id, segment_id=segment_id, run_id=None,
            phase="quest-level-transition", reason="segment_complete", state=end,
        )
        storage.list_campaign_segments = lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("report should use projected segment summaries")
        )
        storage.list_campaign_checkpoints = lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("report should use checkpoint boundaries only")
        )

        report = build_campaign_report(
            storage,
            campaign_id,
            full_history=True,
        )

    segment = report["segments"][0]
    assert report["progress"]["final_level"] == 30
    assert segment["objective_outcome"] == "achieved"
    assert segment["safety_outcome"] == "safe"
    assert segment["metrics"]["activity"]["productive_combat_seconds"] == 8


def test_campaign_segment_can_be_loaded_by_durable_id(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Route evidence",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=30,
        )
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="source-ranked-hunt-example",
            start_state={
                "name": "Dorrik",
                "level": 29,
                "campaign_source_revision": "old-revision",
            },
        )
        storage.finish_campaign_segment(
            segment_id,
            status="success",
            run_id=123,
            end_state={
                "name": "Dorrik",
                "level": 29,
                "campaign_source_revision": "old-revision",
                "campaign_field_city_preflight": {
                    "run_id": 123,
                    "complete": True,
                    "blocked": False,
                    "locations": ["the leather shop"],
                },
            },
            command_count=0,
            duration_seconds=0,
        )

        segment = storage.get_campaign_segment_by_id(campaign_id, segment_id)
        missing = storage.get_campaign_segment_by_id(campaign_id + 1, segment_id)
        projections = storage.list_recent_campaign_segment_state_projections(
            campaign_id,
            state_fields=(
                "campaign_source_revision",
                "campaign_field_city_preflight",
            ),
            limit=256,
        )

    assert segment is not None
    assert segment["id"] == segment_id
    assert segment["run_id"] == 123
    assert missing is None
    assert len(projections) == 1
    projected_end = json.loads(projections[0]["end_state_json"])
    assert projected_end["campaign_source_revision"] == "old-revision"
    assert projected_end["campaign_field_city_preflight"]["locations"] == [
        "the leather shop"
    ]


def test_campaign_report_does_not_scan_events_for_cached_runs(tmp_path) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Cached campaign",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=30,
        )
        run_id = storage.create_run(
            scenario_name="starter:Evidence",
            scenario_path=tmp_path / "character.yaml",
        )
        storage.record_event(
            run_id,
            kind="run_context",
            payload={"character": {"name": "Evidence"}, "objective": {"level": 30}},
        )
        storage.finish_run(run_id, status="success")
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="level-29",
            start_state={"name": "Evidence", "level": 29, "xp": 100},
        )
        end_state = {"name": "Evidence", "level": 29, "xp": 150, "dead": False}
        storage.finish_campaign_segment(
            segment_id,
            status="success",
            run_id=run_id,
            end_state=end_state,
            command_count=3,
            duration_seconds=5,
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=segment_id,
            run_id=run_id,
            phase="level-29",
            reason="segment_complete",
            state=end_state,
        )
        summary = storage.get_run_summary(run_id)
        assert summary is not None
        summary["summary_version"] = RUN_REPORT_SUMMARY_VERSION - 1
        summary["outcomes"]["objective"] = "achieved"
        storage.connection.execute(
            "UPDATE run_summaries SET summary_json = ? WHERE run_id = ?",
            (json.dumps(summary, sort_keys=True), run_id),
        )
        storage.connection.commit()
        storage.list_events = lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("campaign report must use cached run summaries")
        )
        storage.list_state_snapshots = lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("campaign report must not reload run snapshots")
        )
        storage.get_run = lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("campaign report should batch run metadata")
        )
        storage.get_run_summary = lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("campaign report should batch cached summaries")
        )

        report = build_campaign_report(storage, campaign_id)

    assert report["evidence"]["completed_run_summary_count"] == 1
    assert report["segments"] == []
    assert report["evidence"]["segment_details_included"] is False
    assert report["runs"][0]["summary_available"] is True
    assert report["runs"][0]["outcomes"]["objective"] == "unknown"
    assert report["character"]["name"] == "Evidence"


def test_legacy_summary_backfill_is_bounded_and_resumable(tmp_path) -> None:
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        run_ids = [
            storage.create_run(
                scenario_name=f"scenario:{index}",
                scenario_path=tmp_path / f"{index}.yaml",
            )
            for index in range(3)
        ]
        for run_id in run_ids:
            storage.record_event(
                run_id,
                kind="run_context",
                payload={"character": {"name": "Evidence"}, "objective": {}},
            )
            storage.finish_run(run_id, status="success")
        storage.connection.execute("DELETE FROM run_summaries")
        storage.connection.commit()

        first_page = storage.summarize_legacy_runs(limit=1)
        next_page = storage.summarize_legacy_runs(
            after_run_id=first_page[-1], limit=1,
        )

    assert first_page == [run_ids[0]]
    assert next_page == [run_ids[1]]


def test_campaign_summary_backfill_is_scoped_and_resumable(tmp_path) -> None:
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        campaign_ids = [
            storage.create_campaign(
                name=f"campaign-{index}",
                config_path=tmp_path / f"campaign-{index}.yaml",
                character_profile_path=tmp_path / f"character-{index}.yaml",
                target_level=30,
            )
            for index in range(2)
        ]
        run_ids = [
            storage.create_run(
                scenario_name=f"scenario:{index}",
                scenario_path=tmp_path / f"{index}.yaml",
            )
            for index in range(3)
        ]
        for run_id in run_ids:
            storage.record_event(
                run_id,
                kind="run_context",
                payload={"character": {"name": "Evidence"}, "objective": {}},
            )
            storage.finish_run(run_id, status="success")
        storage.connection.execute("DELETE FROM run_summaries")
        storage.connection.executemany(
            """
            INSERT INTO campaign_run_links (campaign_id, run_id, first_sequence)
            VALUES (?, ?, ?)
            """,
            (
                (campaign_ids[0], run_ids[0], 1),
                (campaign_ids[1], run_ids[1], 1),
                (campaign_ids[0], run_ids[2], 2),
            ),
        )
        storage.connection.commit()

        first_page = storage.summarize_legacy_runs(
            limit=1, campaign_id=campaign_ids[0],
        )
        next_page = storage.summarize_legacy_runs(
            after_run_id=first_page[-1], limit=1,
            campaign_id=campaign_ids[0],
        )

    assert first_page == [run_ids[0]]
    assert next_page == [run_ids[2]]


def test_large_database_event_lookup_joins_canonical_payload(tmp_path, monkeypatch) -> None:
    database = tmp_path / "runs.sqlite3"
    monkeypatch.setattr(storage_module, "_campaign_database_is_large", lambda _path: True)
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Indexed campaign",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=30,
        )
        run_id = storage.create_run(
            scenario_name="starter:Evidence",
            scenario_path=tmp_path / "character.yaml",
        )
        storage.record_event(
            run_id,
            kind="game_event",
            payload={"type": "skill_practiced", "data": {"skill": "Kick"}},
        )
        legacy_payload = {"type": "skill_practiced", "data": {"skill": "kick"}}
        legacy_timestamp = "2026-10-03T00:00:02+00:00"
        legacy_event = storage.connection.execute(
            """
            INSERT INTO events (run_id, timestamp, kind, payload_json)
            VALUES (?, ?, 'game_event', ?)
            """,
            (run_id, legacy_timestamp, json.dumps(legacy_payload)),
        )
        storage.connection.execute(
            """
            INSERT INTO campaign_game_event_index (
                event_id, run_id, timestamp, event_type, skill, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                legacy_event.lastrowid, run_id, legacy_timestamp,
                "skill_practiced", "kick", json.dumps(legacy_payload),
            ),
        )
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="training",
            start_state={"name": "Evidence", "level": 29},
        )
        storage.finish_campaign_segment(
            segment_id,
            status="success",
            run_id=run_id,
            end_state={"name": "Evidence", "level": 29},
            command_count=1,
            duration_seconds=1,
        )

        events = storage.list_campaign_game_events(
            campaign_id, skill="kick", event_types=("skill_practiced",),
        )

    assert len(events) == 2
    assert {
        json.loads(event["payload_json"])["data"]["skill"] for event in events
    } == {"Kick", "kick"}


def test_experiment_records_comparable_conditions_and_attribution(tmp_path) -> None:
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        run_id = storage.create_run(
            scenario_name="starter:Evidence",
            scenario_path=tmp_path / "character.yaml",
        )
        experiment_id = storage.create_campaign_experiment(
            comparison_key="warrior-level-29",
            variant="source-informed",
            test_mode="source-informed",
            run_id=run_id,
            tester_version="0.1.0",
            dd4_version="local-test-server",
            source_revision="abc123",
            starting_state=_experiment_starting_state(),
            objective={"quest_points": 1, "target_level": 30},
        )
        storage.finish_run(run_id, status="success")
        storage.finish_campaign_experiment(
            experiment_id,
            run_id=run_id,
            metrics={
                "net_xp": 1200,
                "elapsed_seconds": 90,
                "confirmed_kills": 3,
                "deaths": 0,
                "xp_lost": 0,
                "quest_points_gained": 1,
                "productive_combat_seconds": 45,
                "travel_seconds": 20,
                "maintenance_seconds": 15,
                "waiting_seconds": 10,
            },
            bot_error="missed capacity check",
        )
        row = storage.list_campaign_experiments(
            comparison_key="warrior-level-29",
        )[0]
        with pytest.raises(ValueError, match="immutable"):
            storage.finish_campaign_experiment(experiment_id, metrics={})

    assert row["tester_version"] == "0.1.0"
    assert row["run_id"] == run_id
    assert row["dd4_version"] == "local-test-server"
    assert json.loads(row["starting_state_json"])["world_boot_id"] == "boot-1"
    assert json.loads(row["objective_json"])["target_level"] == 30
    assert json.loads(row["metrics_json"])["net_xp"] == 1200
    assert row["bot_error"] == "missed capacity check"
    assert row["game_defect"] is None


def test_experiment_comparison_summarizes_metrics_and_exposes_start_mismatch(
    tmp_path,
) -> None:
    database = tmp_path / "runs.sqlite3"
    metric_sets = (
        {
            "net_xp": 1200, "elapsed_seconds": 90, "confirmed_kills": 3,
            "deaths": 0, "xp_lost": 0, "quest_points_gained": 1,
            "productive_combat_seconds": 45, "travel_seconds": 20,
            "maintenance_seconds": 15, "waiting_seconds": 10,
        },
        {
            "net_xp": 600, "elapsed_seconds": 60, "confirmed_kills": 2,
            "deaths": 0, "xp_lost": 0, "quest_points_gained": 0,
            "productive_combat_seconds": 30, "travel_seconds": 12,
            "maintenance_seconds": 8, "waiting_seconds": 10,
        },
    )
    variants = ("source-informed", "ordinary-control")
    with RunStorage(database) as storage:
        for index, (variant, metrics) in enumerate(zip(variants, metric_sets)):
            run_id = storage.create_run(
                scenario_name=f"starter:Experiment{index}",
                scenario_path=tmp_path / f"character-{index}.yaml",
            )
            starting_state = _experiment_starting_state(f"Experiment{index}")
            if index:
                starting_state["xp"] += 100
            experiment_id = storage.create_campaign_experiment(
                comparison_key="warrior-level-29-balance",
                variant=variant,
                test_mode="ordinary-player",
                tester_version="0.1.0",
                dd4_version="build-1",
                starting_state=starting_state,
                objective={"target_level": 30},
                run_id=run_id,
            )
            storage.finish_run(run_id, status="success")
            storage.finish_campaign_experiment(
                experiment_id,
                run_id=run_id,
                metrics=metrics,
                bot_error="missed a recovery threshold" if index == 0 else None,
                game_defect="incorrect server XP" if index else None,
            )

        summary = storage.summarize_campaign_experiment_comparison(
            "warrior-level-29-balance",
        )

    assert summary is not None
    assert summary["conditions_consistent"] is True
    assert summary["conditions"]["test_mode"] == "ordinary-player"
    assert summary["objective_consistent"] is True
    assert summary["world_baseline_consistent"] is False
    by_variant = {item["variant"]: item for item in summary["variants"]}
    source = by_variant["source-informed"]
    control = by_variant["ordinary-control"]
    assert source["mean_metrics"]["net_xp"] == 1200
    assert source["mean_net_xp_per_minute"] == 800
    assert source["attribution"]["bot_error_arms"] == 1
    assert source["attribution"]["game_defect_arms"] == 0
    assert control["mean_net_xp_per_minute"] == 600
    assert control["attribution"]["game_defect_arms"] == 1
    assert control["starting_profiles"][0]["xp"] == (
        _experiment_starting_state("Experiment1")["xp"] + 100
    )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("mana", -1),
        ("mana", float("nan")),
        ("max_mana", float("inf")),
    ),
)
def test_experiment_rejects_invalid_starting_vitals(tmp_path, field, value) -> None:
    starting_state = _experiment_starting_state()
    starting_state[field] = value

    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        with pytest.raises(ValueError, match=f"starting_state\\.{field}"):
            storage.create_campaign_experiment(
                comparison_key="mage-level-29",
                variant="invalid-start",
                test_mode="source-informed",
                tester_version="0.1.0",
                dd4_version="build-1",
                source_revision="abc123",
                starting_state=starting_state,
                objective={"target_level": 30},
            )


def test_experiment_comparison_pins_versions_mode_and_objective_per_arm_start(
    tmp_path,
) -> None:
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        common = {
            "comparison_key": "warrior-level-29",
            "test_mode": "ordinary-player",
            "tester_version": "0.1.0",
            "dd4_version": "build-1",
            "objective": {"target_level": 30, "quest_points": 1},
        }
        first = storage.create_campaign_experiment(
            **common,
            variant="pilot-a",
            starting_state=_experiment_starting_state(),
        )
        second_state = _experiment_starting_state("EvidenceTwo")
        second_state["hp"] = 640
        second = storage.create_campaign_experiment(
            **common,
            variant="pilot-b",
            starting_state=second_state,
        )

        assert first != second
        assert json.loads(
            storage.list_campaign_experiments(
                comparison_key="warrior-level-29",
            )[1]["starting_state_json"]
        )["hp"] == 640
        with pytest.raises(ValueError, match="same DD4 version"):
            storage.create_campaign_experiment(
                **{**common, "dd4_version": "build-2"},
                variant="changed-server",
                starting_state=_experiment_starting_state(),
            )
        with pytest.raises(ValueError, match="same tester version"):
            storage.create_campaign_experiment(
                **{**common, "tester_version": "0.2.0"},
                variant="changed-tester",
                starting_state=_experiment_starting_state(),
            )
        with pytest.raises(ValueError, match="same test mode"):
            storage.create_campaign_experiment(
                **{**common, "test_mode": "source-informed"},
                variant="changed-method",
                source_revision="abc123",
                starting_state=_experiment_starting_state(),
            )
        with pytest.raises(ValueError, match="same objective"):
            storage.create_campaign_experiment(
                **{**common, "objective": {"target_level": 31}},
                variant="changed-goal",
                starting_state=_experiment_starting_state(),
            )
        with pytest.raises(ValueError, match="reproducibility fields"):
            storage.create_campaign_experiment(
                **common,
                variant="partial-start",
                starting_state={"name": "Evidence"},
            )


def test_source_informed_comparison_pins_source_revision(tmp_path) -> None:
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        common = {
            "comparison_key": "mage-level-29",
            "test_mode": "source-informed",
            "tester_version": "0.1.0",
            "dd4_version": "build-1",
            "source_revision": "abc123",
            "objective": {"target_level": 30},
        }
        storage.create_campaign_experiment(
            **common,
            variant="source-a",
            starting_state=_experiment_starting_state(),
        )

        with pytest.raises(ValueError, match="same source revision"):
            storage.create_campaign_experiment(
                **{**common, "source_revision": "def456"},
                variant="source-b",
                starting_state=_experiment_starting_state(),
            )


def test_experiment_rejects_incomparable_metrics(tmp_path) -> None:
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        run_id = storage.create_run(
            scenario_name="starter:Evidence",
            scenario_path=tmp_path / "character.yaml",
        )
        storage.finish_run(run_id, status="success")
        experiment_id = storage.create_campaign_experiment(
            comparison_key="mage-level-29",
            variant="source-informed",
            test_mode="source-informed",
            tester_version="0.1.0",
            dd4_version="build-1",
            source_revision="abc123",
            run_id=run_id,
            starting_state=_experiment_starting_state(),
            objective={"target_level": 30},
        )
        with pytest.raises(ValueError, match="comparable fields"):
            storage.finish_campaign_experiment(
                experiment_id,
                run_id=run_id,
                metrics={"net_xp": 100},
            )
