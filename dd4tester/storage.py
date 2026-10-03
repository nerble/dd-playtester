from __future__ import annotations

import json
import logging
import math
import queue
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Collection, Iterator

from . import __version__
from .lease import CampaignLease, CampaignLeaseBusyError, campaign_lease_path


_CAMPAIGN_EVENT_HISTORY_LIMIT = 256
_SQLITE_BUSY_TIMEOUT_MS = 30_000
_SQLITE_JOURNAL_MODE = "WAL"
_CAMPAIGN_PHASE_INDEX_BUILD_MAX_BYTES = 1_000_000_000
# Full campaign state is intentionally JSON-heavy. Keep large shared
# databases from turning a bounded row tail into an oversized memory/read
# operation during autonomous resume. Eight rows cover the latest interrupted
# segment plus the short retry/no-progress window without making a cold
# startup scan hundreds of megabytes of JSON.
_CAMPAIGN_LARGE_DATABASE_HISTORY_LIMIT = 8
RUN_REPORT_SUMMARY_VERSION = 6
_OBSERVATION_QUEUE_SIZE = 512
_OBSERVATION_WRITE_TIMEOUT_SECONDS = 0.25
_OBSERVATION_CONTROL_TIMEOUT_SECONDS = 10.0
_OBSERVATION_COMMIT_MAX_AGE_SECONDS = 0.5
_OBSERVATION_CHECKPOINT_EVENTS = frozenset(
    {"character_identity_observed", "progress_changed", "item_acquired", "character_died", "quest_status_changed"}
)
_FULL_CHECKPOINT_REASONS = _OBSERVATION_CHECKPOINT_EVENTS | frozenset(
    {"initial_state", "run_finished"}
)
_CURRENT_STATE_FIELDS = (
    "schema_version", "revision", "name", "race", "character_class", "subclass",
    "sex", "level", "xp", "max_xp", "xp_to_next_level", "practice",
    "hp", "max_hp", "mana", "max_mana", "move", "max_move", "rage",
    "max_rage", "hunger", "max_hunger", "thirst", "max_thirst", "drunk",
    "max_drunk", "position", "form", "room_name", "room_vnum", "area",
    "sector", "room_flags", "exits", "stats", "progress", "progress_source",
    "xp_loss_observed", "xp_loss_total", "currencies", "inventory", "equipment",
    "affects", "quests", "quest_status", "quest_points", "total_quest_points",
    "quest_level_qp_required", "quest_level_qp_shortfall", "recall_points",
    "recall_points_observed", "current_recall", "in_combat", "combat_target", "dead",
    "world_boot_id",
)
_EXPERIMENT_METRIC_FIELDS = frozenset(
    {
        "net_xp", "elapsed_seconds", "confirmed_kills", "deaths", "xp_lost",
        "quest_points_gained", "productive_combat_seconds", "travel_seconds",
        "maintenance_seconds", "waiting_seconds",
    }
)
_EXPERIMENT_STARTING_STATE_FIELDS = frozenset(
    {
        "name", "race", "sex", "character_class", "subclass", "level", "xp",
        "world_boot_id", "room_vnum", "hp", "max_hp", "mana", "max_mana",
        "move", "max_move", "stats", "currencies", "inventory", "equipment",
        "quest_points", "total_quest_points",
    }
)

@dataclass(frozen=True)
class _WriterControl:
    command: str
    completed: threading.Event


def _index_game_event(
    connection: sqlite3.Connection,
    *,
    event_id: int,
    run_id: int,
    timestamp: str,
    payload: dict[str, Any],
) -> None:
    event_type = payload.get("type")
    data = payload.get("data")
    skill = data.get("skill") if isinstance(data, dict) else None
    if not isinstance(event_type, str) or not event_type.strip():
        return
    connection.execute(
        """
        INSERT OR IGNORE INTO campaign_game_event_lookup (
            event_id, run_id, timestamp, event_type, skill
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            event_id,
            run_id,
            timestamp,
            event_type,
            skill.casefold() if isinstance(skill, str) else None,
        ),
    )


def _validate_experiment_metrics(metrics: object) -> dict[str, Any]:
    if not isinstance(metrics, dict):
        raise ValueError("metrics must be a non-empty object")
    missing = _EXPERIMENT_METRIC_FIELDS - metrics.keys()
    if missing:
        raise ValueError(
            "metrics are missing comparable fields: "
            + ", ".join(sorted(missing))
        )
    count_fields = {
        "confirmed_kills", "deaths", "xp_lost", "quest_points_gained",
    }
    numeric_fields = _EXPERIMENT_METRIC_FIELDS - count_fields
    for field in count_fields:
        value = metrics[field]
        if type(value) is not int or value < 0:
            raise ValueError(f"metrics.{field} must be a nonnegative integer")
    for field in numeric_fields:
        value = metrics[field]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or (field != "net_xp" and value < 0)
        ):
            raise ValueError(f"metrics.{field} must be a finite numeric value")
    return dict(metrics)


def _validate_experiment_starting_state(state: object) -> dict[str, Any]:
    if not isinstance(state, dict) or not state:
        raise ValueError("starting_state must be a non-empty object")
    missing = _EXPERIMENT_STARTING_STATE_FIELDS - state.keys()
    if missing:
        raise ValueError(
            "starting_state is missing reproducibility fields: "
            + ", ".join(sorted(missing))
        )
    for field in (
        "name", "race", "sex", "character_class", "world_boot_id", "room_vnum",
    ):
        if not isinstance(state[field], (str, int)) or not str(state[field]).strip():
            raise ValueError(f"starting_state.{field} must identify the live character/world")
    if type(state["level"]) is not int or state["level"] < 1:
        raise ValueError("starting_state.level must be a positive integer")
    if type(state["xp"]) is not int or state["xp"] < 0:
        raise ValueError("starting_state.xp must be a nonnegative integer")
    for field in ("hp", "max_hp", "move", "max_move"):
        value = state[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"starting_state.{field} must be numeric")
        if not math.isfinite(value):
            raise ValueError(f"starting_state.{field} must be finite")
    if state["max_hp"] <= 0 or state["max_move"] < 0:
        raise ValueError("starting_state has invalid maximum vitals")
    if not isinstance(state["stats"], dict) or not state["stats"]:
        raise ValueError("starting_state.stats must contain the observed stats")
    if not isinstance(state["currencies"], dict):
        raise ValueError("starting_state.currencies must be an object")
    if state["inventory"] is None or state["equipment"] is None:
        raise ValueError("starting_state must include observed inventory and equipment")
    for field in ("quest_points", "total_quest_points"):
        value = state[field]
        if type(value) is not int or value < 0:
            raise ValueError(f"starting_state.{field} must be a nonnegative integer")
    try:
        json.dumps(state, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("starting_state must contain JSON-safe values") from exc
    return dict(state)


def _canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _compact_current_state(state: dict[str, Any]) -> dict[str, Any]:
    return {
        field: state[field]
        for field in _CURRENT_STATE_FIELDS
        if field in state
    }


def _split_snapshot_event(
    kind: str, payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None, str | None]:
    """Keep full state out of ordered events; return it for sparse checkpoints."""
    state = payload.get("state") if kind == "state_snapshot" else None
    if not isinstance(state, dict):
        return dict(payload), None, None
    reason = payload.get("reason")
    checkpoint_reason = (
        reason.strip()
        if isinstance(reason, str)
        and reason.strip() in _FULL_CHECKPOINT_REASONS
        else None
    )
    return (
        {key: value for key, value in payload.items() if key != "state"},
        state,
        checkpoint_reason,
    )


def _upsert_current_state(
    connection: sqlite3.Connection,
    *,
    run_id: int,
    event_id: int,
    timestamp: str,
    state: dict[str, Any],
) -> None:
    connection.execute(
        """
        INSERT INTO run_current_states (run_id, event_id, timestamp, state_json)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(run_id) DO UPDATE SET
            event_id = excluded.event_id,
            timestamp = excluded.timestamp,
            state_json = excluded.state_json
        """,
        (run_id, event_id, timestamp, json.dumps(state, sort_keys=True)),
    )


class _BoundedObservationWriter:
    """Persist ordered live observations away from the Telnet reader task."""

    def __init__(self, path: Path, *, commit_interval: int) -> None:
        self._path = path
        self._commit_interval = commit_interval
        self._queue: queue.Queue[object] = queue.Queue(_OBSERVATION_QUEUE_SIZE)
        self._error: BaseException | None = None
        self._thread = threading.Thread(
            target=self._run,
            name="dd4tester-sqlite-writer",
            daemon=True,
        )
        self._thread.start()

    def submit(self, item: dict[str, Any]) -> None:
        self._raise_error()
        try:
            self._queue.put(item, timeout=_OBSERVATION_WRITE_TIMEOUT_SECONDS)
        except queue.Full as exc:
            raise RuntimeError(
                "SQLite observation queue remained full; stopping the live run "
                "so transcript repair can recover its recorded events"
            ) from exc
        self._raise_error()

    def flush(self) -> None:
        self._raise_error()
        control = self._enqueue_control("flush")
        if not control.completed.wait(_OBSERVATION_CONTROL_TIMEOUT_SECONDS):
            raise RuntimeError("SQLite observation writer did not flush within 10 seconds")
        self._raise_error()

    def close(self) -> None:
        control: _WriterControl | None = None
        if self._thread.is_alive():
            control = self._enqueue_control("stop", check_error=False)
            if not control.completed.wait(_OBSERVATION_CONTROL_TIMEOUT_SECONDS):
                raise RuntimeError("SQLite observation writer did not stop within 10 seconds")
        self._thread.join(timeout=1.0)
        if self._thread.is_alive():
            raise RuntimeError("SQLite observation writer thread is still running")
        self._raise_error()

    def _enqueue_control(
        self, command: str, *, check_error: bool = True,
    ) -> _WriterControl:
        if check_error:
            self._raise_error()
        control = _WriterControl(command, threading.Event())
        try:
            self._queue.put(control, timeout=_OBSERVATION_CONTROL_TIMEOUT_SECONDS)
        except queue.Full as exc:
            raise RuntimeError(
                "SQLite observation queue remained full; stopping the live run "
                "before a storage barrier could complete"
            ) from exc
        return control

    def _raise_error(self) -> None:
        if self._error is not None:
            raise RuntimeError("SQLite observation writer failed") from self._error

    def _run(self) -> None:
        connection: sqlite3.Connection | None = None
        pending = 0
        pending_current_states: dict[int, tuple[int, str, dict[str, Any]]] = {}
        try:
            connection = sqlite3.connect(
                self._path,
                timeout=_OBSERVATION_WRITE_TIMEOUT_SECONDS,
            )
            connection.row_factory = sqlite3.Row
            connection.execute(
                f"PRAGMA busy_timeout = {int(_OBSERVATION_WRITE_TIMEOUT_SECONDS * 1000)}"
            )
            connection.execute("PRAGMA foreign_keys = ON")
            last_commit = time.monotonic()
            stopping = False
            while not stopping:
                try:
                    item = self._queue.get(timeout=0.1)
                except queue.Empty:
                    if (
                        pending
                        and time.monotonic() - last_commit
                        >= _OBSERVATION_COMMIT_MAX_AGE_SECONDS
                    ):
                        self._flush_current_states(connection, pending_current_states)
                        connection.commit()
                        pending = 0
                        pending_current_states.clear()
                        last_commit = time.monotonic()
                    continue
                try:
                    if isinstance(item, _WriterControl):
                        if item.command == "stop":
                            stopping = True
                            if pending and self._error is None:
                                self._flush_current_states(
                                    connection, pending_current_states,
                                )
                                connection.commit()
                                pending = 0
                                pending_current_states.clear()
                                last_commit = time.monotonic()
                        elif item.command == "flush":
                            if self._error is None:
                                self._flush_current_states(
                                    connection, pending_current_states,
                                )
                                connection.commit()
                                pending = 0
                                pending_current_states.clear()
                                last_commit = time.monotonic()
                        else:
                            raise ValueError(
                                f"unknown observation writer command: {item.command}"
                            )
                        continue
                    if self._error is None:
                        current_state = self._write_item(connection, item)
                        if current_state is not None:
                            run_id, event_id, timestamp, state = current_state
                            pending_current_states[run_id] = (
                                event_id, timestamp, state,
                            )
                        pending += 1
                        if (
                            pending >= self._commit_interval
                            or time.monotonic() - last_commit
                            >= _OBSERVATION_COMMIT_MAX_AGE_SECONDS
                        ):
                            self._flush_current_states(
                                connection, pending_current_states,
                            )
                            connection.commit()
                            pending = 0
                            pending_current_states.clear()
                            last_commit = time.monotonic()
                except BaseException as exc:
                    connection.rollback()
                    pending = 0
                    pending_current_states.clear()
                    self._error = exc
                finally:
                    self._queue.task_done()
                    if isinstance(item, _WriterControl):
                        item.completed.set()
            if self._error is None and pending:
                self._flush_current_states(connection, pending_current_states)
                connection.commit()
        except BaseException as exc:
            self._error = exc
            # Always release submitters waiting in flush/close after a worker
            # startup or connection failure.
            while True:
                try:
                    queued_item = self._queue.get_nowait()
                except queue.Empty:
                    break
                else:
                    self._queue.task_done()
                    if isinstance(queued_item, _WriterControl):
                        queued_item.completed.set()
        finally:
            if connection is not None:
                connection.close()

    @staticmethod
    def _write_item(
        connection: sqlite3.Connection,
        item: object,
    ) -> tuple[int, int, str, dict[str, Any]] | None:
        if not isinstance(item, dict):
            raise TypeError("observation writer received an invalid item")
        run_id = int(item["run_id"])
        kind = str(item["kind"])
        payload = item["payload"]
        timestamp = str(item["timestamp"])
        payload_json = json.dumps(payload, sort_keys=True)
        cursor = connection.execute(
            "INSERT INTO events (run_id, timestamp, kind, payload_json) VALUES (?, ?, ?, ?)",
            (run_id, timestamp, kind, payload_json),
        )
        event_id = int(cursor.lastrowid)
        connection.execute("DELETE FROM run_summaries WHERE run_id = ?", (run_id,))
        if kind == "game_event":
            _index_game_event(
                connection,
                event_id=event_id,
                run_id=run_id,
                timestamp=timestamp,
                payload=payload,
            )
        command = payload.get("command") if kind == "command" else None
        if isinstance(command, str):
            run = connection.execute(
                "SELECT scenario_name FROM runs WHERE id = ?", (run_id,),
            ).fetchone()
            if run is not None:
                character_name = str(run["scenario_name"]).rpartition(":")[2]
                connection.execute(
                    """
                    INSERT OR IGNORE INTO character_commands (
                        event_id, run_id, character_name, command, timestamp
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (event_id, run_id, character_name, command, timestamp),
                )
        full_state = item.get("checkpoint_state")
        reason = item.get("checkpoint_reason")
        if isinstance(full_state, dict) and isinstance(reason, str) and reason:
            if reason == "initial_state":
                has_initial = connection.execute(
                    """
                    SELECT 1 FROM state_snapshots
                    WHERE run_id = ?
                      AND json_extract(state_json, '$.level') IS NOT NULL
                      AND json_extract(state_json, '$.xp') IS NOT NULL
                      AND json_extract(state_json, '$.hp') IS NOT NULL
                      AND json_extract(state_json, '$.max_hp') IS NOT NULL
                    LIMIT 1
                    """,
                    (run_id,),
                ).fetchone() is not None
                if has_initial:
                    reason = None
            if reason:
                snapshot = connection.execute(
                    """
                    INSERT INTO state_snapshots (
                        run_id, source_event_id, timestamp, reason, state_json
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        run_id, event_id, timestamp, reason,
                        json.dumps(full_state, sort_keys=True),
                    ),
                )
                if reason == "item_acquired":
                    _record_character_acquired_items(
                        connection,
                        int(snapshot.lastrowid),
                        full_state,
                        timestamp=timestamp,
                    )
        state = item.get("current_state")
        if isinstance(state, dict):
            return run_id, event_id, timestamp, state
        return None

    @staticmethod
    def _flush_current_states(
        connection: sqlite3.Connection,
        states: dict[int, tuple[int, str, dict[str, Any]]],
    ) -> None:
        for run_id, (event_id, timestamp, state) in states.items():
            connection.execute(
                """
                INSERT INTO run_current_states (run_id, event_id, timestamp, state_json)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    event_id = excluded.event_id,
                    timestamp = excluded.timestamp,
                    state_json = excluded.state_json
                """,
                (run_id, event_id, timestamp, json.dumps(state, sort_keys=True)),
            )


def _campaign_database_is_large(path: Path) -> bool:
    try:
        return path.stat().st_size > _CAMPAIGN_PHASE_INDEX_BUILD_MAX_BYTES
    except OSError:
        return False


def _bounded_campaign_history_limit(path: Path, requested: int) -> int:
    if _campaign_database_is_large(path):
        return min(requested, _CAMPAIGN_LARGE_DATABASE_HISTORY_LIMIT)
    return requested


def _campaign_state_projection(
    column: str,
    fields: tuple[str, ...],
) -> tuple[str, tuple[str, ...]]:
    pairs: list[str] = []
    parameters: list[str] = []
    for field in fields:
        if not field.isidentifier():
            raise ValueError("campaign state field names must be identifiers")
        pairs.extend(("?", f"json_extract({column}, ?)"))
        parameters.extend((field, f"$.{field}"))
    return f"json_object({', '.join(pairs)})", tuple(parameters)


class RunStorage:
    def __init__(
        self,
        path: Path,
        *,
        event_commit_interval: int = 25,
        read_only: bool = False,
    ) -> None:
        if event_commit_interval < 1:
            raise ValueError("event_commit_interval must be at least 1")
        self.path = path
        self.event_commit_interval = event_commit_interval
        self.read_only = read_only
        self._events_since_commit = 0
        self._observation_writer: _BoundedObservationWriter | None = None
        self._recent_campaign_segments_cache: dict[
            tuple[int, int], list[sqlite3.Row]
        ] = {}
        self._recent_campaign_checkpoints_cache: dict[
            tuple[int, int], list[sqlite3.Row]
        ] = {}
        if read_only:
            if not self.path.is_file():
                raise FileNotFoundError(self.path)
            database_uri = f"file:{self.path.resolve().as_posix()}?mode=ro"
            self.connection = sqlite3.connect(
                database_uri,
                uri=True,
                timeout=_SQLITE_BUSY_TIMEOUT_MS / 1000,
            )
            self.connection.row_factory = sqlite3.Row
            self.connection.execute(
                f"PRAGMA busy_timeout = {_SQLITE_BUSY_TIMEOUT_MS}"
            )
            self.connection.execute("PRAGMA foreign_keys = ON")
            self._run_summaries_available = self._table_exists("run_summaries")
            self._campaign_experiments_available = self._table_exists(
                "campaign_experiments"
            )
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Several character campaigns share the durable database.  Wait for
        # a bounded interval when another process is committing instead of
        # failing a live segment on a transient ``database is locked`` error.
        self.connection = sqlite3.connect(
            self.path,
            timeout=_SQLITE_BUSY_TIMEOUT_MS / 1000,
        )
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(
            f"PRAGMA busy_timeout = {_SQLITE_BUSY_TIMEOUT_MS}"
        )
        # WAL lets campaign readers and checkpoint writers coexist while a
        # different character is recording a long live segment.  The busy
        # timeout remains bounded because SQLite still serializes writers.
        self.connection.execute(
            f"PRAGMA journal_mode = {_SQLITE_JOURNAL_MODE}"
        )
        self.connection.execute("PRAGMA synchronous = NORMAL")
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._ensure_schema()
        self._run_summaries_available = True
        self._campaign_experiments_available = True

    def _ensure_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_name TEXT NOT NULL,
                scenario_path TEXT NOT NULL,
                boot_id TEXT,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                transcript_path TEXT,
                error TEXT,
                execution_status TEXT,
                objective_outcome TEXT,
                safety_outcome TEXT
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                timestamp TEXT NOT NULL,
                kind TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS campaign_game_event_index (
                event_id INTEGER PRIMARY KEY REFERENCES events(id) ON DELETE CASCADE,
                run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                skill TEXT,
                payload_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS campaign_game_event_lookup (
                event_id INTEGER PRIMARY KEY REFERENCES events(id) ON DELETE CASCADE,
                run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                skill TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_campaign_game_event_lookup_run_id
            ON campaign_game_event_lookup(run_id, event_id);

            CREATE INDEX IF NOT EXISTS idx_campaign_game_event_lookup_filters
            ON campaign_game_event_lookup(run_id, event_type, skill, event_id);

            CREATE INDEX IF NOT EXISTS idx_campaign_game_event_index_run_id
            ON campaign_game_event_index(run_id, event_id);

            CREATE INDEX IF NOT EXISTS idx_campaign_game_event_index_filters
            ON campaign_game_event_index(run_id, event_type, skill, event_id);

            CREATE TABLE IF NOT EXISTS state_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                source_event_id INTEGER REFERENCES events(id) ON DELETE SET NULL,
                timestamp TEXT NOT NULL,
                reason TEXT NOT NULL,
                state_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_events_run_id
            ON events(run_id, id);

            CREATE INDEX IF NOT EXISTS idx_state_snapshots_run_id
            ON state_snapshots(run_id, id);

            CREATE TABLE IF NOT EXISTS run_current_states (
                run_id INTEGER PRIMARY KEY REFERENCES runs(id) ON DELETE CASCADE,
                event_id INTEGER REFERENCES events(id) ON DELETE SET NULL,
                timestamp TEXT NOT NULL,
                state_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS run_summaries (
                run_id INTEGER PRIMARY KEY REFERENCES runs(id) ON DELETE CASCADE,
                completed_at TEXT NOT NULL,
                summary_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS character_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL UNIQUE
                    REFERENCES events(id) ON DELETE CASCADE,
                run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                character_name TEXT NOT NULL COLLATE NOCASE,
                command TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_character_commands_name_id
            ON character_commands(character_name, id DESC);

            CREATE TABLE IF NOT EXISTS character_acquired_items (
                character_name TEXT NOT NULL COLLATE NOCASE,
                item_description TEXT NOT NULL COLLATE NOCASE,
                first_snapshot_id INTEGER
                    REFERENCES state_snapshots(id) ON DELETE SET NULL,
                first_seen_at TEXT NOT NULL,
                PRIMARY KEY (character_name, item_description)
            );

            CREATE TABLE IF NOT EXISTS character_item_backfills (
                character_name TEXT PRIMARY KEY COLLATE NOCASE,
                completed_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_state_snapshots_character_id
            ON state_snapshots(
                lower(json_extract(state_json, '$.name')), id DESC
            );

            CREATE INDEX IF NOT EXISTS idx_state_snapshots_reason_character_id
            ON state_snapshots(
                reason, lower(json_extract(state_json, '$.name')), id DESC
            );

            CREATE TABLE IF NOT EXISTS loot_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                character_name TEXT NOT NULL,
                boot_id TEXT,
                item_keyword TEXT NOT NULL,
                item_description TEXT NOT NULL,
                shop_name TEXT NOT NULL,
                shop_room_vnum TEXT NOT NULL,
                offered_coins INTEGER,
                sold_coins INTEGER NOT NULL,
                timestamp TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_loot_sales_character
            ON loot_sales(character_name, item_keyword, shop_name, id);

            CREATE INDEX IF NOT EXISTS idx_loot_sales_run_id
            ON loot_sales(run_id, id);

            CREATE TABLE IF NOT EXISTS mob_kills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                character_name TEXT NOT NULL,
                boot_id TEXT,
                mob_name TEXT NOT NULL,
                xp_gained INTEGER,
                source_mobile_vnum INTEGER,
                source_policy_id TEXT,
                below_useful_band INTEGER NOT NULL DEFAULT 0,
                objective_eligible INTEGER NOT NULL DEFAULT 1,
                route_gate INTEGER NOT NULL DEFAULT 0,
                selector TEXT,
                timestamp TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_mob_kills_character
            ON mob_kills(character_name, boot_id, mob_name, id);

            CREATE INDEX IF NOT EXISTS idx_mob_kills_run_id
            ON mob_kills(run_id, id);

            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                config_path TEXT NOT NULL,
                character_profile_path TEXT NOT NULL,
                target_level INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                status TEXT NOT NULL,
                error TEXT
            );

            CREATE TABLE IF NOT EXISTS campaign_experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER REFERENCES campaigns(id) ON DELETE SET NULL,
                run_id INTEGER REFERENCES runs(id) ON DELETE SET NULL,
                comparison_key TEXT NOT NULL,
                variant TEXT NOT NULL,
                test_mode TEXT NOT NULL,
                tester_version TEXT NOT NULL,
                dd4_version TEXT,
                source_revision TEXT,
                starting_state_json TEXT NOT NULL,
                objective_json TEXT NOT NULL,
                metrics_json TEXT,
                bot_error TEXT,
                game_defect TEXT,
                created_at TEXT NOT NULL,
                finished_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_campaign_experiments_comparison
            ON campaign_experiments(comparison_key, variant, id);

            CREATE INDEX IF NOT EXISTS idx_campaigns_config_path
            ON campaigns(config_path, id DESC);

            CREATE TABLE IF NOT EXISTS campaign_segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
                sequence INTEGER NOT NULL,
                phase TEXT NOT NULL,
                run_id INTEGER,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                start_state_json TEXT NOT NULL,
                end_state_json TEXT,
                command_count INTEGER,
                duration_seconds REAL,
                error TEXT,
                execution_status TEXT,
                objective_outcome TEXT,
                safety_outcome TEXT,
                metrics_json TEXT,
                UNIQUE(campaign_id, sequence)
            );

            CREATE INDEX IF NOT EXISTS idx_campaign_segments_campaign_id
            ON campaign_segments(campaign_id, sequence);

            CREATE TABLE IF NOT EXISTS campaign_run_links (
                campaign_id INTEGER NOT NULL
                    REFERENCES campaigns(id) ON DELETE CASCADE,
                run_id INTEGER NOT NULL,
                first_sequence INTEGER NOT NULL,
                PRIMARY KEY(campaign_id, run_id)
            );

            CREATE INDEX IF NOT EXISTS idx_campaign_run_links_sequence
            ON campaign_run_links(campaign_id, first_sequence, run_id);

            CREATE TABLE IF NOT EXISTS campaign_run_link_backfills (
                campaign_id INTEGER PRIMARY KEY
                    REFERENCES campaigns(id) ON DELETE CASCADE,
                last_sequence INTEGER NOT NULL,
                is_complete INTEGER NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TRIGGER IF NOT EXISTS campaign_run_link_after_insert
            AFTER INSERT ON campaign_segments
            WHEN NEW.run_id IS NOT NULL
            BEGIN
                INSERT INTO campaign_run_links (
                    campaign_id, run_id, first_sequence
                ) VALUES (NEW.campaign_id, NEW.run_id, NEW.sequence)
                ON CONFLICT(campaign_id, run_id) DO UPDATE SET
                    first_sequence = MIN(
                        campaign_run_links.first_sequence,
                        excluded.first_sequence
                    );
            END;

            CREATE TRIGGER IF NOT EXISTS campaign_run_link_after_update
            AFTER UPDATE OF run_id ON campaign_segments
            WHEN NEW.run_id IS NOT NULL
            BEGIN
                INSERT INTO campaign_run_links (
                    campaign_id, run_id, first_sequence
                ) VALUES (NEW.campaign_id, NEW.run_id, NEW.sequence)
                ON CONFLICT(campaign_id, run_id) DO UPDATE SET
                    first_sequence = MIN(
                        campaign_run_links.first_sequence,
                        excluded.first_sequence
                    );
            END;

            CREATE TABLE IF NOT EXISTS campaign_usage (
                campaign_id INTEGER PRIMARY KEY
                    REFERENCES campaigns(id) ON DELETE CASCADE,
                segment_count INTEGER NOT NULL,
                command_count INTEGER NOT NULL,
                duration_seconds REAL NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS campaign_checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
                segment_id INTEGER REFERENCES campaign_segments(id) ON DELETE SET NULL,
                run_id INTEGER,
                phase TEXT NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL,
                state_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_campaign_checkpoints_campaign_id
            ON campaign_checkpoints(campaign_id, id);
            """
        )
        loot_sale_columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(loot_sales)")
        }
        if "boot_id" not in loot_sale_columns:
            self.connection.execute(
                "ALTER TABLE loot_sales ADD COLUMN boot_id TEXT"
            )
        run_columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(runs)")
        }
        if "boot_id" not in run_columns:
            self.connection.execute("ALTER TABLE runs ADD COLUMN boot_id TEXT")
        for column in ("execution_status", "objective_outcome", "safety_outcome"):
            if column not in run_columns:
                self.connection.execute(f"ALTER TABLE runs ADD COLUMN {column} TEXT")
        segment_columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(campaign_segments)")
        }
        for column in (
            "execution_status", "objective_outcome", "safety_outcome", "metrics_json",
        ):
            if column not in segment_columns:
                self.connection.execute(
                    f"ALTER TABLE campaign_segments ADD COLUMN {column} TEXT"
                )
        experiment_columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(campaign_experiments)")
        }
        if "run_id" not in experiment_columns:
            self.connection.execute(
                "ALTER TABLE campaign_experiments ADD COLUMN run_id INTEGER"
            )
        self.connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_campaign_experiments_run_id
            ON campaign_experiments(run_id)
            """
        )
        mob_kill_columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(mob_kills)")
        }
        if "source_mobile_vnum" not in mob_kill_columns:
            self.connection.execute(
                "ALTER TABLE mob_kills ADD COLUMN source_mobile_vnum INTEGER"
            )
        if "source_policy_id" not in mob_kill_columns:
            self.connection.execute(
                "ALTER TABLE mob_kills ADD COLUMN source_policy_id TEXT"
            )
        if "below_useful_band" not in mob_kill_columns:
            self.connection.execute(
                "ALTER TABLE mob_kills ADD COLUMN below_useful_band "
                "INTEGER NOT NULL DEFAULT 0"
            )
        if "objective_eligible" not in mob_kill_columns:
            self.connection.execute(
                "ALTER TABLE mob_kills ADD COLUMN objective_eligible "
                "INTEGER NOT NULL DEFAULT 1"
            )
        if "route_gate" not in mob_kill_columns:
            self.connection.execute(
                "ALTER TABLE mob_kills ADD COLUMN route_gate "
                "INTEGER NOT NULL DEFAULT 0"
            )
        if "selector" not in mob_kill_columns:
            self.connection.execute(
                "ALTER TABLE mob_kills ADD COLUMN selector TEXT"
            )
        self.connection.commit()
        self._ensure_campaign_phase_index()
        self._events_since_commit = 0

    def _ensure_campaign_phase_index(self) -> None:
        """Build the phase index only during bounded-size schema setup."""
        try:
            database_size = self.path.stat().st_size
        except OSError:
            return
        if database_size > _CAMPAIGN_PHASE_INDEX_BUILD_MAX_BYTES:
            return
        self.connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_campaign_segments_campaign_phase
            ON campaign_segments(campaign_id, phase, sequence)
            """
        )
        self.connection.commit()

    def campaign_phase_index_available(self) -> bool:
        """Return whether phase-scoped campaign history can use its index."""
        return any(
            row["name"] == "idx_campaign_segments_campaign_phase"
            for row in self.connection.execute(
                "PRAGMA index_list(campaign_segments)"
            )
        )

    def _table_exists(self, table: str) -> bool:
        return self.connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table,),
        ).fetchone() is not None

    def _table_columns(self, table: str) -> set[str]:
        if not table.isidentifier():
            raise ValueError("table name must be an identifier")
        try:
            return {
                str(row["name"])
                for row in self.connection.execute(f"PRAGMA table_info({table})")
            }
        except sqlite3.OperationalError:
            return set()

    def create_run(self, *, scenario_name: str, scenario_path: Path) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO runs (scenario_name, scenario_path, started_at, status)
            VALUES (?, ?, ?, ?)
            """,
            (scenario_name, str(scenario_path), _now(), "running"),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def set_transcript_path(self, run_id: int, transcript_path: Path) -> None:
        self.connection.execute(
            "UPDATE runs SET transcript_path = ? WHERE id = ?",
            (str(transcript_path), run_id),
        )
        self.connection.commit()

    def set_run_boot_id(self, run_id: int, boot_id: str | None) -> None:
        if boot_id is None:
            return
        self.connection.execute(
            "UPDATE runs SET boot_id = ? WHERE id = ?",
            (boot_id, run_id),
        )
        self.connection.execute(
            "UPDATE mob_kills SET boot_id = ? WHERE run_id = ? AND boot_id IS NULL",
            (boot_id, run_id),
        )
        self.connection.execute(
            "UPDATE loot_sales SET boot_id = ? WHERE run_id = ? AND boot_id IS NULL",
            (boot_id, run_id),
        )
        self.connection.commit()
        self._events_since_commit = 0

    def record_event(
        self,
        run_id: int,
        *,
        kind: str,
        payload: dict[str, Any],
        timestamp: str | None = None,
    ) -> int:
        event_timestamp = timestamp or _now()
        payload, snapshot_state, snapshot_reason = _split_snapshot_event(
            kind, payload,
        )
        cursor = self.connection.execute(
            """
            INSERT INTO events (run_id, timestamp, kind, payload_json)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, event_timestamp, kind, json.dumps(payload, sort_keys=True)),
        )
        event_id = int(cursor.lastrowid)
        if kind == "game_event":
            _index_game_event(
                self.connection,
                event_id=event_id,
                run_id=run_id,
                timestamp=event_timestamp,
                payload=payload,
            )
        command = payload.get("command") if kind == "command" else None
        if isinstance(command, str):
            run = self.connection.execute(
                "SELECT scenario_name FROM runs WHERE id = ?",
                (run_id,),
            ).fetchone()
            if run is not None:
                character_name = str(run["scenario_name"]).rpartition(":")[2]
                self.connection.execute(
                    """
                    INSERT OR IGNORE INTO character_commands (
                        event_id, run_id, character_name, command, timestamp
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        run_id,
                        character_name,
                        command,
                        event_timestamp,
                    ),
                )
        self.connection.execute(
            "DELETE FROM run_summaries WHERE run_id = ?",
            (run_id,),
        )
        if snapshot_state is not None:
            previous_game_event = self.connection.execute(
                """
                SELECT id FROM events
                WHERE run_id = ? AND kind = 'game_event' AND id < ?
                ORDER BY id DESC LIMIT 1
                """,
                (run_id, event_id),
            ).fetchone()
            _upsert_current_state(
                self.connection,
                run_id=run_id,
                event_id=event_id,
                timestamp=event_timestamp,
                state=_compact_current_state(snapshot_state),
            )
            if snapshot_reason is not None:
                self.record_state_snapshot(
                    run_id,
                    source_event_id=(
                        int(previous_game_event["id"])
                        if previous_game_event is not None else None
                    ),
                    reason=snapshot_reason,
                    state=snapshot_state,
                    timestamp=event_timestamp,
                )
                return event_id
        self._events_since_commit += 1
        if (
            self._events_since_commit >= self.event_commit_interval
            or self._observation_writer is not None
        ):
            self.connection.commit()
            self._events_since_commit = 0
        return event_id

    def queue_observation(
        self,
        run_id: int,
        *,
        kind: str,
        payload: dict[str, Any],
        timestamp: str | None = None,
        current_state: dict[str, Any] | None = None,
        checkpoint_reason: str | None = None,
    ) -> None:
        """Queue one canonical event and optionally replace the run's live state."""
        if self.read_only:
            raise RuntimeError("cannot queue writes through read-only storage")
        payload, snapshot_state, snapshot_reason = _split_snapshot_event(
            kind, payload,
        )
        snapshot_event = snapshot_state is not None
        if snapshot_event:
            current_state = current_state or snapshot_state
            checkpoint_reason = checkpoint_reason or snapshot_reason
        if (
            current_state is not None
            and checkpoint_reason is None
            and not snapshot_event
        ):
            event_type = payload.get("type") if kind == "game_event" else None
            if isinstance(event_type, str) and event_type in _OBSERVATION_CHECKPOINT_EVENTS:
                checkpoint_reason = event_type
            elif all(
                current_state.get(field) is not None
                for field in ("level", "xp", "hp", "max_hp")
            ):
                checkpoint_reason = "initial_state"
        if checkpoint_reason not in _FULL_CHECKPOINT_REASONS:
            checkpoint_reason = None
        if self._observation_writer is None:
            # Release any batched synchronous event writes before a second
            # SQLite connection starts the ordered observation stream.
            self.connection.commit()
            self._events_since_commit = 0
            self._observation_writer = _BoundedObservationWriter(
                self.path,
                commit_interval=self.event_commit_interval,
            )
        self._observation_writer.submit(
            {
                "run_id": run_id,
                "kind": kind,
                "payload": payload,
                "timestamp": timestamp or _now(),
                "current_state": (
                    _compact_current_state(current_state)
                    if isinstance(current_state, dict)
                    else None
                ),
                "checkpoint_state": (
                    current_state if checkpoint_reason is not None else None
                ),
                "checkpoint_reason": checkpoint_reason,
            }
        )

    def record_state_snapshot(
        self,
        run_id: int,
        *,
        source_event_id: int | None,
        reason: str,
        state: dict[str, Any],
        timestamp: str | None = None,
    ) -> int:
        snapshot_timestamp = timestamp or _now()
        cursor = self.connection.execute(
            """
            INSERT INTO state_snapshots (
                run_id, source_event_id, timestamp, reason, state_json
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                run_id,
                source_event_id,
                snapshot_timestamp,
                reason,
                json.dumps(state, sort_keys=True),
            ),
        )
        snapshot_id = int(cursor.lastrowid)
        if reason == "item_acquired":
            self._record_character_acquired_items(
                snapshot_id,
                state,
                timestamp=snapshot_timestamp,
            )
        # State snapshots are the recovery boundary for live campaigns. Do
        # not keep their write transaction open until another protocol event
        # or final cleanup, because another character may need to checkpoint
        # while this one remains connected.
        self.connection.commit()
        self._events_since_commit = 0
        return snapshot_id

    def _record_character_acquired_items(
        self,
        snapshot_id: int,
        state: dict[str, Any],
        *,
        timestamp: str,
    ) -> None:
        _record_character_acquired_items(
            self.connection, snapshot_id, state, timestamp=timestamp,
        )

    def finish_run(
        self,
        run_id: int,
        *,
        status: str,
        error: str | None = None,
        execution_status: str | None = None,
        objective_outcome: str | None = None,
        safety_outcome: str | None = None,
    ) -> None:
        self.flush()
        finished_at = _now()
        self.connection.execute(
            """
            UPDATE runs
            SET finished_at = ?, status = ?, error = ?,
                execution_status = ?, objective_outcome = ?, safety_outcome = ?
            WHERE id = ?
            """,
            (
                finished_at,
                status,
                error,
                execution_status or status,
                objective_outcome,
                safety_outcome,
                run_id,
            ),
        )
        current = self.connection.execute(
            """
            SELECT event_id, timestamp, state_json
            FROM run_current_states WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()
        if current is not None:
            cursor = self.connection.execute(
                """
                INSERT INTO state_snapshots (
                    run_id, source_event_id, timestamp, reason, state_json
                ) VALUES (?, ?, ?, 'run_finished', ?)
                """,
                (
                    run_id,
                    current["event_id"],
                    finished_at,
                    current["state_json"],
                ),
            )
            try:
                final_state = json.loads(current["state_json"])
            except (TypeError, json.JSONDecodeError):
                final_state = None
            if isinstance(final_state, dict):
                self._record_character_acquired_items(
                    int(cursor.lastrowid),
                    final_state,
                    timestamp=finished_at,
                )
        self.connection.commit()
        try:
            from .report import _build_run_report_uncached

            summary = _build_run_report_uncached(self, run_id, commentary_limit=100)
            outcomes = summary.get("outcomes", {})
            self.connection.execute(
                """
                UPDATE runs
                SET execution_status = ?, objective_outcome = ?, safety_outcome = ?
                WHERE id = ?
                """,
                (
                    outcomes.get("execution") or execution_status or status,
                    outcomes.get("objective") or objective_outcome or "unknown",
                    outcomes.get("safety") or safety_outcome or "unknown",
                    run_id,
                ),
            )
            self.connection.commit()
            self.save_run_summary(run_id, summary)
        except Exception:
            logging.getLogger(__name__).exception(
                "Could not cache the completed run summary for run %s", run_id,
            )

    def _invalidate_campaign_history(self, campaign_id: int | None = None) -> None:
        if campaign_id is None:
            self._recent_campaign_segments_cache.clear()
            self._recent_campaign_checkpoints_cache.clear()
            return
        self._recent_campaign_segments_cache = {
            key: value
            for key, value in self._recent_campaign_segments_cache.items()
            if key[0] != campaign_id
        }
        self._recent_campaign_checkpoints_cache = {
            key: value
            for key, value in self._recent_campaign_checkpoints_cache.items()
            if key[0] != campaign_id
        }

    def fail_interrupted_runs(self, *, reason: str) -> int:
        """Mark orphaned running records as failed after their process has ended."""
        cursor = self.connection.execute(
            """
            UPDATE runs
            SET finished_at = ?, status = 'failed', error = ?
            WHERE status = 'running'
            """,
            (_now(), reason),
        )
        self.connection.commit()
        return int(cursor.rowcount)

    def fail_interrupted_campaign_segments(self, *, reason: str) -> tuple[int, int]:
        """Close orphaned campaign work after its runner process has ended."""
        timestamp = _now()
        campaigns = self.connection.execute(
            """
            UPDATE campaigns
            SET status = 'failed', error = ?, updated_at = ?
            WHERE status = 'running'
              AND EXISTS (
                  SELECT 1
                  FROM campaign_segments
                  WHERE campaign_segments.campaign_id = campaigns.id
                    AND campaign_segments.status = 'running'
              )
            """,
            (reason, timestamp),
        )
        segments = self.connection.execute(
            """
            UPDATE campaign_segments
            SET finished_at = ?, status = 'failed', error = ?
            WHERE status = 'running'
            """,
            (timestamp, reason),
        )
        self.connection.commit()
        self._invalidate_campaign_history()
        return int(segments.rowcount), int(campaigns.rowcount)

    def recover_orphaned_campaigns(self, *, reason: str) -> int:
        """Make running campaigns without a running segment resumable.

        A worker can be interrupted after opening a campaign but before it
        creates its next segment.  In that narrow window there is no segment
        for ``fail_interrupted_campaign_segments`` to repair, leaving the
        campaign display stuck at ``running`` even though its lease is gone.
        The CLI calls this after the operator has checked for live workers.
        """
        candidates = self.connection.execute(
            """
            SELECT id, config_path
            FROM campaigns
            WHERE status = 'running'
              AND NOT EXISTS (
                  SELECT 1
                  FROM campaign_segments
                  WHERE campaign_segments.campaign_id = campaigns.id
                    AND campaign_segments.status = 'running'
              )
            """
        ).fetchall()
        recovered = 0
        for candidate in candidates:
            lease = CampaignLease(
                campaign_lease_path(
                    self.path,
                    Path(str(candidate["config_path"])),
                )
            )
            try:
                lease.acquire()
            except CampaignLeaseBusyError:
                # A live worker can briefly exist between campaign creation
                # and its first segment insert. Leave that worker's campaign
                # untouched; the next recovery pass can revisit it.
                continue
            try:
                cursor = self.connection.execute(
                    """
                    UPDATE campaigns
                    SET status = 'ready', error = ?, updated_at = ?
                    WHERE id = ?
                      AND status = 'running'
                      AND NOT EXISTS (
                          SELECT 1
                          FROM campaign_segments
                          WHERE campaign_segments.campaign_id = campaigns.id
                            AND campaign_segments.status = 'running'
                      )
                    """,
                    (reason, _now(), candidate["id"]),
                )
                self.connection.commit()
                recovered += int(cursor.rowcount)
            finally:
                lease.release()
        self._invalidate_campaign_history()
        return recovered

    def recover_interrupted_campaign_segments(
        self,
        campaign_id: int,
        *,
        reason: str,
        character_name: str | None = None,
        running_segments: Collection[Any] | None = None,
    ) -> int:
        """Close orphaned work for one campaign before it is resumed.

        Resume already loads a bounded newest-segment tail. Reuse that tail
        when supplied; filtering the wide segment table by status can scan
        gigabytes of historical JSON when the shared database is large.
        """
        if running_segments is None:
            running_segments = list(
                self.connection.execute(
                    """
                    SELECT id, run_id, started_at
                    FROM campaign_segments INDEXED BY idx_campaign_segments_campaign_id
                    WHERE campaign_id = ? AND status = 'running'
                    ORDER BY sequence DESC
                    LIMIT 1
                    """,
                    (campaign_id,),
                )
            )
        else:
            running_segments = [
                row
                for row in running_segments
                if int(row["campaign_id"]) == campaign_id
                and row["status"] == "running"
            ][:1]
        if not running_segments:
            return 0

        timestamp = _now()
        run_ids = {
            int(row["run_id"])
            for row in running_segments
            if row["run_id"] is not None
        }
        if character_name:
            character_suffixes = (
                f":{character_name.casefold()}",
                f"-{character_name.casefold()}",
            )
            segment_started_at = min(
                str(row["started_at"]) for row in running_segments
            )
            for row in self.connection.execute(
                """
                SELECT id, scenario_name, started_at, finished_at, status
                FROM runs
                ORDER BY id DESC
                LIMIT 1024
                """,
            ):
                if (
                    row["status"] == "running"
                    and str(row["started_at"]) >= segment_started_at
                    and str(row["scenario_name"]).casefold().endswith(
                        character_suffixes
                    )
                ):
                    run_ids.add(int(row["id"]))
        if run_ids:
            placeholders = ", ".join("?" for _ in run_ids)
            self.connection.execute(
                f"""
                UPDATE runs
                SET finished_at = ?, status = 'failed', error = ?
                WHERE status = 'running' AND id IN ({placeholders})
                """,
                (timestamp, reason, *run_ids),
            )

        segment_ids = [int(row["id"]) for row in running_segments]
        placeholders = ", ".join("?" for _ in segment_ids)
        cursor = self.connection.execute(
            f"""
            UPDATE campaign_segments
            SET finished_at = ?, status = 'failed', error = ?
            WHERE status = 'running' AND id IN ({placeholders})
            """,
            (timestamp, reason, *segment_ids),
        )
        self.connection.execute(
            """
            UPDATE campaigns
            SET status = 'failed', error = ?, updated_at = ?
            WHERE id = ?
            """,
            (reason, timestamp, campaign_id),
        )
        self.connection.commit()
        self._invalidate_campaign_history(campaign_id)
        return int(cursor.rowcount)

    def recover_campaign(
        self,
        campaign_id: int,
        *,
        reason: str,
        character_name: str | None = None,
    ) -> tuple[int, int, int]:
        """Recover one campaign without scanning the shared run history.

        The global recovery command is useful for small databases, but it is
        an unsafe maintenance primitive once many characters share a large
        event store.  This path only reads the campaign's newest running
        segment and its associated transcript, then repairs that campaign.
        """
        campaign = self.get_campaign(campaign_id)
        if campaign is None:
            raise KeyError(f"campaign {campaign_id} does not exist")

        running_segments = list(
            self.connection.execute(
                """
                SELECT id, campaign_id, run_id, started_at, status
                FROM campaign_segments INDEXED BY idx_campaign_segments_campaign_id
                WHERE campaign_id = ? AND status = 'running'
                ORDER BY sequence DESC
                LIMIT 1
                """,
                (campaign_id,),
            )
        )
        repaired_events = 0
        for segment in running_segments:
            if segment["run_id"] is None:
                continue
            repaired_events += self.repair_run_events_from_transcript(
                int(segment["run_id"])
            )

        if running_segments:
            recovered_runs = sum(
                1 for segment in running_segments if segment["run_id"] is not None
            )
            segments = self.recover_interrupted_campaign_segments(
                campaign_id,
                reason=reason,
                character_name=character_name,
                running_segments=running_segments,
            )
            return repaired_events, recovered_runs, segments

        # A worker can fail after closing its campaign segment but before its
        # run cleanup. Repair that orphaned run through the campaign index so
        # scoped recovery does not leave a stale "running" row behind.
        orphaned_runs = list(
            self.connection.execute(
                """
                SELECT DISTINCT runs.id
                FROM runs
                JOIN campaign_segments
                  ON campaign_segments.run_id = runs.id
                WHERE campaign_segments.campaign_id = ?
                  AND runs.status = 'running'
                """,
                (campaign_id,),
            )
        )
        recovered_runs = len(orphaned_runs)
        if orphaned_runs:
            timestamp = _now()
            run_ids = [int(row["id"]) for row in orphaned_runs]
            placeholders = ", ".join("?" for _ in run_ids)
            self.connection.execute(
                f"""
                UPDATE runs
                SET finished_at = ?, status = 'failed', error = ?
                WHERE status = 'running' AND id IN ({placeholders})
                """,
                (
                    timestamp,
                    reason,
                    *run_ids,
                ),
            )
            self.connection.commit()
            return repaired_events, recovered_runs, 0

        lease = CampaignLease(
            campaign_lease_path(
                self.path,
                Path(str(campaign["config_path"])),
            )
        )
        try:
            lease.acquire()
        except CampaignLeaseBusyError:
            return repaired_events, 0, 0
        try:
            cursor = self.connection.execute(
                """
                UPDATE campaigns
                SET status = 'ready', error = ?, updated_at = ?
                WHERE id = ? AND status = 'running'
                """,
                (reason, _now(), campaign_id),
            )
            self.connection.commit()
            return repaired_events, 0, int(cursor.rowcount)
        finally:
            lease.release()

    def fail_campaign_after_timeout(
        self,
        campaign_id: int,
        *,
        reason: str,
        character_name: str | None = None,
        running_segments: Collection[Any] | None = None,
    ) -> int:
        """Close one campaign's running records after its bounded runner expires."""
        if running_segments is None:
            running_segments = list(
                self.connection.execute(
                    """
                    SELECT id, run_id, started_at
                    FROM campaign_segments INDEXED BY idx_campaign_segments_campaign_id
                    WHERE campaign_id = ? AND status = 'running'
                    ORDER BY sequence DESC
                    LIMIT 1
                    """,
                    (campaign_id,),
                )
            )
        else:
            running_segments = [
                row
                for row in running_segments
                if int(row["campaign_id"]) == campaign_id
                and row["status"] == "running"
            ][:1]
        run_ids = {
            int(row["run_id"])
            for row in running_segments
            if row["run_id"] is not None
        }
        if character_name and running_segments:
            character_suffixes = (
                f":{character_name.casefold()}",
                f"-{character_name.casefold()}",
            )
            segment_started_at = min(
                str(row["started_at"]) for row in running_segments
            )
            for row in self.connection.execute(
                """
                SELECT id, scenario_name, started_at, finished_at, status
                FROM runs
                ORDER BY id DESC
                LIMIT 1024
                """,
            ):
                scenario_name = str(row["scenario_name"]).casefold()
                if (
                    (
                        row["status"] == "running"
                        or row["finished_at"] is not None
                    )
                    and str(row["started_at"]) >= segment_started_at
                    and scenario_name.endswith(character_suffixes)
                ):
                    run_ids.add(int(row["id"]))
        timestamp = _now()
        if run_ids:
            placeholders = ", ".join("?" for _ in run_ids)
            self.connection.execute(
                f"""
                UPDATE runs
                SET finished_at = ?, status = 'failed', error = ?
                WHERE id IN ({placeholders}) AND status = 'running'
                """,
                (timestamp, reason, *run_ids),
            )
            unbound_segments = [
                row for row in running_segments if row["run_id"] is None
            ]
            if len(run_ids) == 1:
                run_id = next(iter(run_ids))
                for segment in unbound_segments:
                    self.connection.execute(
                        """
                        UPDATE campaign_segments
                        SET run_id = ?
                        WHERE id = ? AND status = 'running'
                        """,
                        (run_id, int(segment["id"])),
                    )
        segment_cursor = self.connection.execute(
            """
            UPDATE campaign_segments
            SET finished_at = ?, status = 'failed', error = ?
            WHERE campaign_id = ? AND status = 'running'
            """,
            (timestamp, reason, campaign_id),
        )
        self.connection.execute(
            """
            UPDATE campaigns
            SET status = 'failed', error = ?, updated_at = ?
            WHERE id = ?
            """,
            (reason, timestamp, campaign_id),
        )
        self.connection.commit()
        self._invalidate_campaign_history(campaign_id)
        return int(segment_cursor.rowcount)

    def list_runs(self, *, limit: int = 20) -> list[sqlite3.Row]:
        columns = self._table_columns("runs")
        outcomes = ", execution_status, objective_outcome, safety_outcome" if {
            "execution_status", "objective_outcome", "safety_outcome",
        } <= columns else ", NULL AS execution_status, NULL AS objective_outcome, NULL AS safety_outcome"
        cursor = self.connection.execute(
            f"""
            SELECT id, scenario_name, scenario_path, boot_id, started_at,
                   finished_at, status, transcript_path, error{outcomes}
            FROM runs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return list(cursor.fetchall())

    def get_run(self, run_id: int) -> sqlite3.Row | None:
        columns = self._table_columns("runs")
        outcomes = ", execution_status, objective_outcome, safety_outcome" if {
            "execution_status", "objective_outcome", "safety_outcome",
        } <= columns else ", NULL AS execution_status, NULL AS objective_outcome, NULL AS safety_outcome"
        cursor = self.connection.execute(
            f"""
            SELECT id, scenario_name, scenario_path, boot_id, started_at,
                   finished_at, status, transcript_path, error{outcomes}
            FROM runs
            WHERE id = ?
            """,
            (run_id,),
        )
        return cursor.fetchone()

    def latest_boot_id(self) -> str | None:
        cursor = self.connection.execute(
            """
            SELECT boot_id
            FROM runs
            WHERE boot_id IS NOT NULL
            ORDER BY id DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        return str(row["boot_id"]) if row is not None else None

    def list_events(self, run_id: int, *, limit: int | None = None) -> list[sqlite3.Row]:
        """Return the recorded evidence for a run in chronological storage order."""
        if limit is not None and limit < 1:
            raise ValueError("event limit must be positive")
        cursor = self.connection.execute(
            """
            SELECT id, run_id, timestamp, kind, payload_json
            FROM events
            WHERE run_id = ?
            ORDER BY id
            """ + (" LIMIT ?" if limit is not None else ""),
            (run_id, limit) if limit is not None else (run_id,),
        )
        return list(cursor.fetchall())

    def list_recent_events(
        self,
        run_id: int,
        *,
        limit: int = 512,
    ) -> list[sqlite3.Row]:
        """Return a bounded chronological tail of one run's evidence."""
        if limit < 1:
            raise ValueError("event limit must be positive")
        cursor = self.connection.execute(
            """
            SELECT id, run_id, timestamp, kind, payload_json
            FROM events
            WHERE run_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (run_id, limit),
        )
        return list(reversed(cursor.fetchall()))

    def get_latest_run_kill_event(self, run_id: int) -> sqlite3.Row | None:
        """Read the latest kill ledger without materializing a run's transcript."""
        return self.connection.execute(
            """
            SELECT id, run_id, timestamp, kind, payload_json
            FROM events
            WHERE run_id = ? AND kind = 'state'
              AND (
                  json_type(payload_json, '$.objective_kills') = 'array'
                  OR json_type(payload_json, '$.completed_kills') = 'array'
              )
            ORDER BY id DESC
            LIMIT 1
            """,
            (run_id,),
        ).fetchone()

    def get_latest_run_state_event(
        self, run_id: int, *, states: tuple[str, ...],
    ) -> sqlite3.Row | None:
        """Read one latest matching boundary without loading the transcript."""
        if not states:
            return None
        placeholders = ", ".join("?" for _ in states)
        return self.connection.execute(
            f"""
            SELECT id, run_id, timestamp, kind, payload_json
            FROM events
            WHERE run_id = ? AND kind = 'state'
              AND json_extract(payload_json, '$.state') IN ({placeholders})
            ORDER BY id DESC
            LIMIT 1
            """,
            (run_id, *states),
        ).fetchone()

    def repair_run_events_from_transcript(self, run_id: int) -> int:
        """Replay a transcript suffix that was not committed before a stop.

        Transcripts flush each JSONL record immediately, while event rows are
        batched for performance.  A stopped process can therefore leave a
        durable transcript suffix missing from SQLite.  Only an exact stored
        prefix is repaired so a malformed or unrelated transcript cannot
        duplicate or reorder evidence.
        """
        run = self.get_run(run_id)
        if run is None or not run["transcript_path"]:
            return 0
        raw_path = Path(str(run["transcript_path"]))
        candidates = (raw_path, self.path.parent / raw_path, self.path.parent.parent / raw_path)
        transcript_path = next(
            (candidate for candidate in candidates if candidate.exists()),
            None,
        )
        if transcript_path is None:
            return 0
        transcript_events: list[dict[str, Any]] = []
        try:
            lines = transcript_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return 0
        for line in lines:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (
                not isinstance(event, dict)
                or int(event.get("run_id", run_id)) != run_id
                or not isinstance(event.get("kind"), str)
                or not isinstance(event.get("payload"), dict)
                or not isinstance(event.get("timestamp"), str)
            ):
                continue
            transcript_events.append(event)

        stored_events = self.list_events(run_id)
        if len(stored_events) > len(transcript_events):
            return 0
        for index, stored in enumerate(stored_events):
            try:
                stored_payload = json.loads(stored["payload_json"])
            except (TypeError, json.JSONDecodeError):
                return 0
            transcript = transcript_events[index]
            normalized_payload, _, _ = _split_snapshot_event(
                transcript["kind"], transcript["payload"],
            )
            if (
                stored["kind"] != transcript["kind"]
                or stored["timestamp"] != transcript["timestamp"]
                or not (
                    stored_payload == transcript["payload"]
                    or stored_payload == normalized_payload
                )
            ):
                return 0

        imported = 0
        for transcript in transcript_events[len(stored_events) :]:
            event_id = self.record_event(
                run_id,
                kind=transcript["kind"],
                payload=transcript["payload"],
                timestamp=transcript["timestamp"],
            )
            imported += 1
        if imported:
            self.connection.commit()
            self._events_since_commit = 0
        return imported

    def repair_transcript_events(
        self,
        *,
        statuses: tuple[str, ...] = ("running",),
    ) -> tuple[int, int]:
        """Replay missing transcript suffixes for selected recorded runs."""
        if not statuses:
            return 0, 0
        repaired_runs = 0
        repaired_events = 0
        placeholders = ", ".join("?" for _ in statuses)
        run_ids = [
            int(row["id"])
            for row in self.connection.execute(
                """
                SELECT id
                FROM runs
                WHERE transcript_path IS NOT NULL
                  AND status IN (%s)
                ORDER BY id
                """ % placeholders,
                statuses,
            )
        ]
        for run_id in run_ids:
            imported = self.repair_run_events_from_transcript(run_id)
            if imported:
                repaired_runs += 1
                repaired_events += imported
        return repaired_runs, repaired_events

    def bind_unlinked_campaign_runs(self) -> int:
        """Bind a uniquely matching run to an interrupted campaign segment."""
        segments = list(
            self.connection.execute(
                """
                SELECT id, started_at, finished_at
                FROM campaign_segments
                WHERE run_id IS NULL AND status IN ('running', 'failed')
                ORDER BY id
                """
            )
        )
        runs = list(
            self.connection.execute(
                """
                SELECT id, started_at
                FROM runs
                WHERE status IN ('running', 'failed')
                ORDER BY id
                """
            )
        )
        bound = 0
        for segment in segments:
            matching_runs = [
                run
                for run in runs
                if str(run["started_at"]) >= str(segment["started_at"])
                and (
                    segment["finished_at"] is None
                    or str(run["started_at"]) <= str(segment["finished_at"])
                )
            ]
            if len(matching_runs) != 1:
                continue
            cursor = self.connection.execute(
                """
                UPDATE campaign_segments
                SET run_id = ?
                WHERE id = ? AND run_id IS NULL
                """,
                (int(matching_runs[0]["id"]), int(segment["id"])),
            )
            bound += int(cursor.rowcount)
        if bound:
            self.connection.commit()
        return bound

    def list_campaign_game_events(
        self,
        campaign_id: int,
        *,
        level: int | None = None,
        skill: str | None = None,
        event_types: tuple[str, ...] | None = None,
        segment_limit: int = _CAMPAIGN_EVENT_HISTORY_LIMIT,
    ) -> list[sqlite3.Row]:
        """Return filtered game events for a campaign in one indexed join."""
        if segment_limit < 1:
            raise ValueError("segment_limit must be positive")
        effective_segment_limit = (
            _bounded_campaign_history_limit(self.path, segment_limit)
            if segment_limit <= _CAMPAIGN_EVENT_HISTORY_LIMIT
            else segment_limit
        )
        large_database = _campaign_database_is_large(self.path)
        clauses = [] if large_database else ["e.kind = 'game_event'"]
        parameters: list[Any] = [campaign_id, effective_segment_limit]
        if level is not None:
            clauses.append(
                "CAST(json_extract(s.start_state_json, '$.level') AS INTEGER) = ?"
            )
            parameters.append(level)
        if skill is not None:
            clauses.append(
                "i.skill = ?" if large_database
                else "lower(json_extract(e.payload_json, '$.data.skill')) = ?"
            )
            parameters.append(skill.casefold())
        if event_types:
            placeholders = ", ".join("?" for _ in event_types)
            clauses.append(
                (
                    f"i.event_type IN ({placeholders})"
                    if large_database
                    else f"json_extract(e.payload_json, '$.type') IN ({placeholders})"
                )
            )
            parameters.extend(event_types)
        if large_database:
            source = (
                "(SELECT event_id, run_id, timestamp, event_type, skill "
                "FROM campaign_game_event_lookup "
                "UNION ALL "
                "SELECT legacy.event_id, legacy.run_id, legacy.timestamp, "
                "legacy.event_type, legacy.skill "
                "FROM campaign_game_event_index AS legacy "
                "INDEXED BY idx_campaign_game_event_index_run_id "
                "WHERE NOT EXISTS (SELECT 1 FROM campaign_game_event_lookup "
                "AS compact WHERE compact.event_id = legacy.event_id)) AS i "
                "JOIN events AS e ON e.id = i.event_id"
            )
            select = (
                "i.event_id AS id, i.run_id, i.timestamp, "
                "'game_event' AS kind, e.payload_json"
            )
            join_condition = "i.run_id = s.run_id"
        else:
            source = "events AS e INDEXED BY idx_events_run_id"
            select = "e.id, e.run_id, e.timestamp, e.kind, e.payload_json"
            join_condition = "e.run_id = s.run_id"
        where = f"WHERE {join_condition}"
        if clauses:
            where += " AND " + " AND ".join(clauses)
        cursor = self.connection.execute(
            f"""
            WITH recent_segments AS MATERIALIZED (
                SELECT run_id, start_state_json
                FROM campaign_segments
                WHERE campaign_id = ?
                ORDER BY sequence DESC
                LIMIT ?
            )
            SELECT {select},
                   CAST(json_extract(s.start_state_json, '$.level') AS INTEGER)
                       AS character_level
            FROM recent_segments AS s
            CROSS JOIN {source}
            {where}
            ORDER BY id
            """,
            parameters,
        )
        return list(cursor.fetchall())

    def character_command_recorded(
        self,
        character_name: str,
        command: str,
    ) -> bool:
        """Return whether this character previously issued an exact command."""
        return self._latest_character_command(
            character_name,
            exact=command,
        ) is not None

    def latest_character_command(
        self,
        character_name: str,
        *,
        prefix: str | None = None,
    ) -> str | None:
        """Return the newest recorded command for a character."""
        return self._latest_character_command(character_name, prefix=prefix)

    def _latest_character_command(
        self,
        character_name: str,
        *,
        exact: str | None = None,
        prefix: str | None = None,
    ) -> str | None:
        """Query the compact write-time command ledger for one character."""
        if exact is not None and prefix is not None:
            raise ValueError("exact and prefix command filters are mutually exclusive")
        filters = ["character_name = ? COLLATE NOCASE"]
        parameters: list[object] = [character_name]
        if exact is not None:
            filters.append("command = ?")
            parameters.append(exact)
        elif prefix is not None:
            filters.append("substr(command, 1, length(?)) = ?")
            parameters.extend((prefix, prefix))
        cursor = self.connection.execute(
            f"""
            SELECT command
            FROM character_commands
            WHERE {' AND '.join(filters)}
            ORDER BY id DESC
            LIMIT 1
            """,
            parameters,
        )
        row = cursor.fetchone()
        if row is None or not isinstance(row["command"], str):
            return None
        return str(row["command"])

    def count_events(self, run_id: int, *, kind: str | None = None) -> int:
        if kind is None:
            cursor = self.connection.execute(
                "SELECT COUNT(*) FROM events WHERE run_id = ?",
                (run_id,),
            )
        else:
            cursor = self.connection.execute(
                "SELECT COUNT(*) FROM events WHERE run_id = ? AND kind = ?",
                (run_id, kind),
            )
        return int(cursor.fetchone()[0])

    def record_loot_sale(
        self,
        run_id: int,
        *,
        character_name: str,
        boot_id: str | None = None,
        item_keyword: str,
        item_description: str,
        shop_name: str,
        shop_room_vnum: str,
        offered_coins: int | None,
        sold_coins: int,
        timestamp: str | None = None,
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO loot_sales (
                run_id, character_name, boot_id, item_keyword, item_description,
                shop_name, shop_room_vnum, offered_coins, sold_coins, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                character_name,
                boot_id,
                item_keyword,
                item_description,
                shop_name,
                shop_room_vnum,
                offered_coins,
                sold_coins,
                timestamp or _now(),
            ),
        )
        # Sales are compact campaign evidence. Commit them at write time so a
        # killed worker cannot erase completed money-loop observations.
        self.connection.commit()
        self._events_since_commit = 0
        return int(cursor.lastrowid)

    def list_loot_sales(self, character_name: str) -> list[sqlite3.Row]:
        cursor = self.connection.execute(
            """
            SELECT id, run_id, character_name, boot_id, item_keyword, item_description,
                   shop_name, shop_room_vnum, offered_coins, sold_coins, timestamp
            FROM loot_sales
            WHERE character_name = ?
            ORDER BY id
            """,
            (character_name,),
        )
        return list(cursor.fetchall())

    def list_loot_sales_for_run(self, run_id: int) -> list[sqlite3.Row]:
        """Return completed sales recorded for one run in execution order."""
        cursor = self.connection.execute(
            """
            SELECT id, run_id, character_name, boot_id, item_keyword, item_description,
                   shop_name, shop_room_vnum, offered_coins, sold_coins, timestamp
            FROM loot_sales
            WHERE run_id = ?
            ORDER BY id
            """,
            (run_id,),
        )
        return list(cursor.fetchall())

    def record_mob_kill(
        self,
        run_id: int,
        *,
        character_name: str,
        boot_id: str | None,
        mob_name: str,
        xp_gained: int | None,
        source_mobile_vnum: int | None = None,
        source_policy_id: str | None = None,
        below_useful_band: bool = False,
        objective_eligible: bool | None = None,
        route_gate: bool = False,
        selector: str | None = None,
        timestamp: str | None = None,
    ) -> int:
        if objective_eligible is None:
            objective_eligible = not below_useful_band
        cursor = self.connection.execute(
            """
            INSERT INTO mob_kills (
                run_id, character_name, boot_id, mob_name, xp_gained,
                source_mobile_vnum, source_policy_id, below_useful_band,
                objective_eligible, route_gate, selector, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                character_name,
                boot_id,
                mob_name,
                xp_gained,
                source_mobile_vnum,
                source_policy_id,
                int(below_useful_band),
                int(objective_eligible),
                int(route_gate),
                selector,
                timestamp or _now(),
            ),
        )
        # Kill evidence drives reboot-local target ranking and interrupted-run
        # recovery, so it must survive before the runner reaches final cleanup.
        self.connection.commit()
        self._events_since_commit = 0
        return int(cursor.lastrowid)

    def list_mob_kills_for_run(self, run_id: int) -> list[sqlite3.Row]:
        """Return durable kill evidence for one run in execution order."""
        cursor = self.connection.execute(
            """
            SELECT id, run_id, character_name, boot_id, mob_name,
                   xp_gained, source_mobile_vnum, source_policy_id,
                   below_useful_band, objective_eligible, route_gate,
                   selector, timestamp
            FROM mob_kills
            WHERE run_id = ?
            ORDER BY id
            """,
            (run_id,),
        )
        return list(cursor.fetchall())

    def list_mob_kills(
        self,
        character_name: str,
        *,
        boot_id: str | None = None,
    ) -> list[sqlite3.Row]:
        if boot_id is None:
            cursor = self.connection.execute(
                """
                SELECT id, run_id, character_name, boot_id, mob_name,
                       xp_gained, source_mobile_vnum, source_policy_id,
                       below_useful_band, objective_eligible, route_gate,
                       selector, timestamp
                FROM mob_kills
                WHERE character_name = ?
                ORDER BY id
                """,
                (character_name,),
            )
        else:
            cursor = self.connection.execute(
                """
                SELECT id, run_id, character_name, boot_id, mob_name,
                       xp_gained, source_mobile_vnum, source_policy_id,
                       below_useful_band, objective_eligible, route_gate,
                       selector, timestamp
                FROM mob_kills
                WHERE character_name = ? AND boot_id = ?
                ORDER BY id
                """,
                (character_name, boot_id),
            )
        return list(cursor.fetchall())

    def create_campaign(
        self,
        *,
        name: str,
        config_path: Path,
        character_profile_path: Path,
        target_level: int,
    ) -> int:
        now = _now()
        cursor = self.connection.execute(
            """
            INSERT INTO campaigns (
                name, config_path, character_profile_path, target_level,
                started_at, updated_at, status
            )
            VALUES (?, ?, ?, ?, ?, ?, 'running')
            """,
            (
                name,
                str(config_path),
                str(character_profile_path),
                target_level,
                now,
                now,
            ),
        )
        campaign_id = int(cursor.lastrowid)
        self.connection.execute(
            """
            INSERT INTO campaign_usage (
                campaign_id, segment_count, command_count,
                duration_seconds, updated_at
            )
            VALUES (?, 0, 0, 0, ?)
            """,
            (campaign_id, now),
        )
        self.connection.execute(
            """
            INSERT INTO campaign_run_link_backfills (
                campaign_id, last_sequence, is_complete, updated_at
            ) VALUES (?, 0, 1, ?)
            """,
            (campaign_id, now),
        )
        self.connection.commit()
        return campaign_id

    def get_campaign(self, campaign_id: int) -> sqlite3.Row | None:
        cursor = self.connection.execute(
            """
            SELECT id, name, config_path, character_profile_path, target_level,
                   started_at, updated_at, status, error
            FROM campaigns
            WHERE id = ?
            """,
            (campaign_id,),
        )
        return cursor.fetchone()

    def get_latest_campaign_for_config(self, config_path: Path) -> sqlite3.Row | None:
        cursor = self.connection.execute(
            """
            SELECT id, name, config_path, character_profile_path, target_level,
                   started_at, updated_at, status, error
            FROM campaigns
            WHERE config_path = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (str(config_path),),
        )
        return cursor.fetchone()

    def get_run_summary(self, run_id: int) -> dict[str, Any] | None:
        if not self._run_summaries_available:
            return None
        row = self.connection.execute(
            "SELECT summary_json FROM run_summaries WHERE run_id = ?", (run_id,),
        ).fetchone()
        if row is None:
            return None
        try:
            value = json.loads(row["summary_json"])
        except (TypeError, json.JSONDecodeError):
            return None
        return value if isinstance(value, dict) else None

    def get_campaign_run_link_backfill_state(
        self,
        campaign_id: int,
    ) -> dict[str, Any]:
        if not self._table_exists("campaign_run_link_backfills"):
            return {"last_sequence": 0, "complete": False}
        row = self.connection.execute(
            """
            SELECT last_sequence, is_complete
            FROM campaign_run_link_backfills
            WHERE campaign_id = ?
            """,
            (campaign_id,),
        ).fetchone()
        if row is None:
            return {"last_sequence": 0, "complete": False}
        return {
            "last_sequence": int(row["last_sequence"]),
            "complete": bool(row["is_complete"]),
        }

    def backfill_campaign_run_links(
        self,
        campaign_id: int,
        *,
        limit: int = 256,
    ) -> dict[str, Any]:
        """Materialize a bounded, resumable page of legacy segment/run links."""
        if self.read_only:
            raise RuntimeError("cannot backfill campaign links read-only")
        if type(limit) is not int or not 1 <= limit <= 256:
            raise ValueError("limit must be between 1 and 256")
        if self.get_campaign(campaign_id) is None:
            raise LookupError(f"No campaign with id {campaign_id}")
        state = self.get_campaign_run_link_backfill_state(campaign_id)
        last_sequence = int(state["last_sequence"])
        if state["complete"]:
            return {
                "segments_scanned": 0,
                "runs_linked": 0,
                "last_sequence": last_sequence,
                "complete": True,
            }
        rows = self.connection.execute(
            """
            SELECT sequence, run_id
            FROM campaign_segments
            WHERE campaign_id = ? AND sequence > ?
            ORDER BY sequence
            LIMIT ?
            """,
            (campaign_id, last_sequence, limit),
        ).fetchall()
        linked_run_ids: set[int] = set()
        for row in rows:
            if row["run_id"] is None:
                continue
            run_id = int(row["run_id"])
            linked_run_ids.add(run_id)
            self.connection.execute(
                """
                INSERT INTO campaign_run_links (
                    campaign_id, run_id, first_sequence
                ) VALUES (?, ?, ?)
                ON CONFLICT(campaign_id, run_id) DO UPDATE SET
                    first_sequence = MIN(
                        campaign_run_links.first_sequence,
                        excluded.first_sequence
                    )
                """,
                (campaign_id, run_id, int(row["sequence"])),
            )
        if rows:
            last_sequence = int(rows[-1]["sequence"])
        complete = len(rows) < limit
        self.connection.execute(
            """
            INSERT INTO campaign_run_link_backfills (
                campaign_id, last_sequence, is_complete, updated_at
            ) VALUES (?, ?, ?, ?)
            ON CONFLICT(campaign_id) DO UPDATE SET
                last_sequence = excluded.last_sequence,
                is_complete = excluded.is_complete,
                updated_at = excluded.updated_at
            """,
            (campaign_id, last_sequence, int(complete), _now()),
        )
        self.connection.commit()
        return {
            "segments_scanned": len(rows),
            "runs_linked": len(linked_run_ids),
            "last_sequence": last_sequence,
            "complete": complete,
        }

    def _campaign_run_ids(self, campaign_id: int) -> list[int]:
        """Read compact, materialized run links in campaign order."""
        if not self._table_exists("campaign_run_links"):
            return []
        rows = self.connection.execute(
            """
            SELECT run_id
            FROM campaign_run_links
            WHERE campaign_id = ? AND run_id IS NOT NULL
            ORDER BY first_sequence, run_id
            """,
            (campaign_id,),
        ).fetchall()
        return list(dict.fromkeys(int(row["run_id"]) for row in rows))

    def list_campaign_run_records(
        self, campaign_id: int,
    ) -> dict[int, tuple[dict[str, Any], dict[str, Any] | None]]:
        """Fetch run metadata and cached summaries from compact campaign links."""
        if not self._table_exists("campaign_run_links"):
            return {}
        outcome_columns = {
            "execution_status", "objective_outcome", "safety_outcome",
        }
        run_columns = self._table_columns("runs")
        if outcome_columns <= run_columns:
            outcome_select = (
                "run.execution_status, run.objective_outcome, run.safety_outcome"
            )
        else:
            outcome_select = (
                "NULL AS execution_status, NULL AS objective_outcome, "
                "NULL AS safety_outcome"
            )
        if self._run_summaries_available:
            summary_select = "summary.summary_json"
            summary_join = "LEFT JOIN run_summaries AS summary ON summary.run_id = run.id"
        else:
            summary_select = "NULL AS summary_json"
            summary_join = ""
        rows = self.connection.execute(
            f"""
            SELECT run.id, run.scenario_name, run.scenario_path, run.status,
                   run.started_at, run.finished_at, run.transcript_path,
                   run.error, {outcome_select}, {summary_select}
            FROM campaign_run_links AS link
            JOIN runs AS run ON run.id = link.run_id
            {summary_join}
            WHERE link.campaign_id = ?
            ORDER BY link.first_sequence, link.run_id
            """,
            (campaign_id,),
        ).fetchall()
        records: dict[int, tuple[dict[str, Any], dict[str, Any] | None]] = {}
        for row in rows:
            run = {
                key: row[key]
                for key in row.keys()
                if key != "summary_json"
            }
            summary = None
            raw_summary = row["summary_json"]
            if raw_summary is not None:
                try:
                    decoded = json.loads(raw_summary)
                except (TypeError, json.JSONDecodeError):
                    decoded = None
                if (
                    isinstance(decoded, dict)
                    and decoded.get("summary_version")
                    == RUN_REPORT_SUMMARY_VERSION
                ):
                    summary = decoded
                elif (
                    isinstance(decoded, dict)
                    and decoded.get("summary_version")
                    == RUN_REPORT_SUMMARY_VERSION - 1
                ):
                    # Keep compact historical metrics available to campaign
                    # reports, but do not carry forward an unverified positive
                    # objective claim from the previous report contract.
                    summary = dict(decoded)
                    outcomes = dict(summary.get("outcomes") or {})
                    if outcomes.get("objective") == "achieved":
                        outcomes["objective"] = "unknown"
                        summary["outcomes"] = outcomes
            if summary is None and run.get("objective_outcome") == "achieved":
                # Legacy run claims lack enough evidence for a verified
                # campaign completion.
                run["objective_outcome"] = "unknown"
            records[int(row["id"])] = run, summary
        return records

    def list_campaign_mob_kills(self, campaign_id: int) -> list[sqlite3.Row]:
        run_ids = self._campaign_run_ids(campaign_id)
        kills: list[sqlite3.Row] = []
        batch_size = 400
        for offset in range(0, len(run_ids), batch_size):
            batch = run_ids[offset:offset + batch_size]
            placeholders = ", ".join("?" for _ in batch)
            kills.extend(self.connection.execute(
                f"SELECT * FROM mob_kills WHERE run_id IN ({placeholders})",
                batch,
            ).fetchall())
        kills.sort(key=lambda row: int(row["id"]))
        return kills

    def save_run_summary(self, run_id: int, summary: dict[str, Any]) -> None:
        if self.read_only:
            raise RuntimeError("cannot save summaries through read-only storage")
        self.connection.execute(
            """
            INSERT INTO run_summaries (run_id, completed_at, summary_json)
            VALUES (?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                completed_at = excluded.completed_at,
                summary_json = excluded.summary_json
            """,
            (run_id, _now(), json.dumps(summary, sort_keys=True)),
        )
        outcomes = summary.get("outcomes")
        if isinstance(outcomes, dict):
            execution = outcomes.get("execution")
            objective = outcomes.get("objective")
            safety = outcomes.get("safety")
            self.connection.execute(
                """
                UPDATE runs
                SET execution_status = COALESCE(?, execution_status),
                    objective_outcome = COALESCE(?, objective_outcome),
                    safety_outcome = COALESCE(?, safety_outcome)
                WHERE id = ?
                """,
                (execution, objective, safety, run_id),
            )
            self.connection.execute(
                """
                UPDATE campaign_segments
                SET execution_status = COALESCE(?, execution_status),
                    objective_outcome = COALESCE(?, objective_outcome),
                    safety_outcome = COALESCE(?, safety_outcome)
                WHERE run_id = ?
                """,
                (execution, objective, safety, run_id),
            )
        self.connection.commit()

    def summarize_legacy_runs(
        self, *, after_run_id: int = 0, limit: int = 100,
    ) -> list[int]:
        """Backfill a bounded page of completed runs outside normal reporting."""
        if self.read_only:
            raise RuntimeError("cannot summarize runs through read-only storage")
        if after_run_id < 0 or not 1 <= limit <= 1000:
            raise ValueError("after_run_id must be nonnegative and limit 1..1000")
        run_ids = [
            int(row["id"])
            for row in self.connection.execute(
                """
                SELECT run.id FROM runs AS run
                LEFT JOIN run_summaries AS summary ON summary.run_id = run.id
                WHERE run.id > ? AND run.finished_at IS NOT NULL
                  AND (
                      summary.run_id IS NULL
                      OR COALESCE(
                          CASE WHEN json_valid(summary.summary_json)
                               THEN json_extract(
                                   summary.summary_json, '$.summary_version'
                               )
                               ELSE 0
                          END,
                          0
                      ) != ?
                  )
                ORDER BY run.id LIMIT ?
                """,
                (after_run_id, RUN_REPORT_SUMMARY_VERSION, limit),
            )
        ]
        if not run_ids:
            return []
        from .report import _build_run_report_uncached

        for run_id in run_ids:
            self.save_run_summary(
                run_id,
                _build_run_report_uncached(self, run_id, commentary_limit=100),
            )
        return run_ids

    def create_campaign_experiment(
        self,
        *,
        comparison_key: str,
        variant: str,
        test_mode: str,
        starting_state: dict[str, Any],
        objective: dict[str, Any],
        campaign_id: int | None = None,
        run_id: int | None = None,
        tester_version: str = __version__,
        dd4_version: str | None = None,
        source_revision: str | None = None,
    ) -> int:
        """Register one reproducible arm of a controlled comparison."""
        if test_mode not in {"source-informed", "ordinary-player"}:
            raise ValueError("test_mode must be source-informed or ordinary-player")
        if not comparison_key.strip() or not variant.strip():
            raise ValueError("comparison_key and variant must not be empty")
        if not tester_version.strip() or not (dd4_version or "").strip():
            raise ValueError("tester_version and dd4_version are required")
        tester_version = tester_version.strip()
        if test_mode == "source-informed" and not (source_revision or "").strip():
            raise ValueError("source_revision is required for source-informed experiments")
        starting_state = _validate_experiment_starting_state(starting_state)
        if not isinstance(objective, dict) or not objective:
            raise ValueError("objective must be a non-empty object")
        try:
            starting_state_json = _canonical_json(starting_state)
            objective_json = _canonical_json(objective)
        except (TypeError, ValueError) as exc:
            raise ValueError("objective must contain JSON-safe values") from exc
        if campaign_id is not None and self.get_campaign(campaign_id) is None:
            raise ValueError(f"no campaign with id {campaign_id}")
        if run_id is not None and self.get_run(run_id) is None:
            raise ValueError(f"no run with id {run_id}")
        previous = self.connection.execute(
            """
            SELECT tester_version, dd4_version, source_revision, test_mode,
                   objective_json
            FROM campaign_experiments
            WHERE comparison_key = ?
            ORDER BY id
            LIMIT 1
            """,
            (comparison_key.strip(),),
        ).fetchone()
        if previous is not None:
            try:
                previous_objective = json.loads(previous["objective_json"])
                previous_objective_json = _canonical_json(previous_objective)
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ValueError(
                    "existing comparison has unreadable objective evidence"
                ) from exc
            if previous["dd4_version"] != dd4_version.strip():
                raise ValueError(
                    "all arms in a comparison must use the same DD4 version"
                )
            if previous["tester_version"] != tester_version.strip():
                raise ValueError(
                    "all arms in a comparison must use the same tester version"
                )
            if previous["test_mode"] != test_mode:
                raise ValueError(
                    "all arms in a comparison must use the same test mode"
                )
            normalized_source_revision = (
                source_revision.strip() if source_revision else None
            )
            if previous["source_revision"] != normalized_source_revision:
                raise ValueError(
                    "all arms in a comparison must use the same source revision"
                )
            if previous_objective_json != objective_json:
                raise ValueError(
                    "all arms in a comparison must use the same objective"
                )
        cursor = self.connection.execute(
            """
            INSERT INTO campaign_experiments (
                campaign_id, run_id, comparison_key, variant, test_mode, tester_version,
                dd4_version, source_revision, starting_state_json, objective_json,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                campaign_id,
                run_id,
                comparison_key.strip(),
                variant.strip(),
                test_mode,
                tester_version,
                dd4_version.strip(),
                source_revision.strip() if source_revision else None,
                starting_state_json,
                objective_json,
                _now(),
            ),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def finish_campaign_experiment(
        self,
        experiment_id: int,
        *,
        metrics: dict[str, Any],
        run_id: int | None = None,
        bot_error: str | None = None,
        game_defect: str | None = None,
    ) -> None:
        if run_id is not None and self.get_run(run_id) is None:
            raise ValueError(f"no run with id {run_id}")
        existing = self.connection.execute(
            """
            SELECT campaign_id, run_id, finished_at
            FROM campaign_experiments WHERE id = ?
            """,
            (experiment_id,),
        ).fetchone()
        if existing is None:
            raise ValueError(f"no experiment with id {experiment_id}")
        if existing["finished_at"] is not None:
            raise ValueError("a finished experiment is immutable")
        if (
            run_id is not None
            and existing["run_id"] is not None
            and int(run_id) != int(existing["run_id"])
        ):
            raise ValueError("an experiment cannot be reassigned to another run")
        linked_run_id = run_id if run_id is not None else existing["run_id"]
        if linked_run_id is None and existing["campaign_id"] is None:
            raise ValueError("a completed experiment must link to a run or campaign")
        if linked_run_id is not None:
            linked_run = self.get_run(int(linked_run_id))
            if linked_run is None or linked_run["finished_at"] is None:
                raise ValueError("the linked run must be finished before the experiment")
            if existing["campaign_id"] is not None:
                belongs_to_campaign = self.connection.execute(
                    """
                    SELECT 1 FROM campaign_segments
                    WHERE campaign_id = ? AND run_id = ?
                    LIMIT 1
                    """,
                    (existing["campaign_id"], linked_run_id),
                ).fetchone()
                if belongs_to_campaign is None:
                    raise ValueError(
                        "the linked run must belong to the experiment campaign"
                    )
        metrics = _validate_experiment_metrics(metrics)
        self.connection.execute(
            """
            UPDATE campaign_experiments
            SET run_id = COALESCE(?, run_id), metrics_json = ?, bot_error = ?,
                game_defect = ?, finished_at = ?
            WHERE id = ? AND finished_at IS NULL
            """,
            (
                run_id, json.dumps(metrics, sort_keys=True), bot_error,
                game_defect, _now(), experiment_id,
            ),
        )
        if self.connection.execute("SELECT changes()").fetchone()[0] != 1:
            raise ValueError("experiment changed while it was being completed")
        self.connection.commit()

    def list_campaign_experiments(
        self, *, comparison_key: str | None = None,
    ) -> list[sqlite3.Row]:
        if not self._campaign_experiments_available:
            return []
        if comparison_key is None:
            rows = self.connection.execute(
                "SELECT * FROM campaign_experiments ORDER BY id"
            ).fetchall()
        else:
            rows = self.connection.execute(
                """
                SELECT * FROM campaign_experiments
                WHERE comparison_key = ? ORDER BY variant, id
                """,
                (comparison_key,),
            ).fetchall()
        return list(rows)

    def get_latest_campaign_for_character(
        self,
        character_name: str,
    ) -> sqlite3.Row | None:
        """Return the newest campaign checkpoint for a named character."""
        cursor = self.connection.execute(
            """
            SELECT c.id, c.name, c.config_path, c.character_profile_path,
                   c.target_level, c.started_at, c.updated_at, c.status,
                   c.error
            FROM campaigns AS c
            JOIN campaign_checkpoints AS checkpoint
              ON checkpoint.campaign_id = c.id
            WHERE lower(json_extract(checkpoint.state_json, '$.name')) = ?
            ORDER BY checkpoint.id DESC
            LIMIT 1
            """,
            (character_name.casefold(),),
        )
        return cursor.fetchone()

    def get_latest_campaign_checkpoint_for_character_bounded(
        self,
        character_name: str,
    ) -> sqlite3.Row | None:
        """Find a character's newest checkpoint without scanning checkpoint history."""
        cursor = self.connection.execute(
            """
            SELECT campaign.id AS campaign_id, checkpoint.id AS checkpoint_id,
                   checkpoint.state_json
            FROM campaigns AS campaign
            JOIN campaign_checkpoints AS checkpoint
              ON checkpoint.id = (
                  SELECT MAX(latest.id)
                  FROM campaign_checkpoints AS latest
                  WHERE latest.campaign_id = campaign.id
              )
            ORDER BY checkpoint.id DESC
            """
        )
        expected_name = character_name.casefold()
        for row in cursor:
            try:
                state = json.loads(row["state_json"])
            except (TypeError, json.JSONDecodeError):
                continue
            if (
                isinstance(state, dict)
                and str(state.get("name") or "").casefold() == expected_name
            ):
                return row
        return None

    def list_campaigns(self, *, limit: int = 20) -> list[sqlite3.Row]:
        cursor = self.connection.execute(
            """
            SELECT id, name, config_path, character_profile_path, target_level,
                   started_at, updated_at, status, error
            FROM campaigns
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return list(cursor.fetchall())

    def resume_campaign(self, campaign_id: int) -> None:
        self.connection.execute(
            """
            UPDATE campaigns
            SET status = 'running', error = NULL, updated_at = ?
            WHERE id = ?
            """,
            (_now(), campaign_id),
        )
        self.connection.commit()

    def update_campaign_target_level(
        self,
        campaign_id: int,
        target_level: int,
    ) -> None:
        self.connection.execute(
            """
            UPDATE campaigns
            SET target_level = ?, updated_at = ?
            WHERE id = ?
            """,
            (target_level, _now(), campaign_id),
        )
        self.connection.commit()

    def update_campaign_name(self, campaign_id: int, name: str) -> None:
        """Synchronize a campaign's display name with its YAML contract."""
        self.connection.execute(
            """
            UPDATE campaigns
            SET name = ?, updated_at = ?
            WHERE id = ?
            """,
            (name, _now(), campaign_id),
        )
        self.connection.commit()

    def finish_campaign(
        self,
        campaign_id: int,
        *,
        status: str,
        error: str | None = None,
    ) -> None:
        self.connection.execute(
            """
            UPDATE campaigns
            SET status = ?, error = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, error, _now(), campaign_id),
        )
        self.connection.commit()

    def start_campaign_segment(
        self,
        campaign_id: int,
        *,
        phase: str,
        start_state: dict[str, Any],
    ) -> int:
        self._ensure_campaign_usage(campaign_id)
        sequence = int(
            self.connection.execute(
                "SELECT COALESCE(MAX(sequence), 0) + 1 FROM campaign_segments "
                "WHERE campaign_id = ?",
                (campaign_id,),
            ).fetchone()[0]
        )
        cursor = self.connection.execute(
            """
            INSERT INTO campaign_segments (
                campaign_id, sequence, phase, started_at, status, start_state_json
            )
            VALUES (?, ?, ?, ?, 'running', ?)
            """,
            (
                campaign_id,
                sequence,
                phase,
                _now(),
                json.dumps(start_state, sort_keys=True),
            ),
        )
        self.connection.execute(
            """
            UPDATE campaign_usage
            SET segment_count = segment_count + 1, updated_at = ?
            WHERE campaign_id = ?
            """,
            (_now(), campaign_id),
        )
        self.connection.commit()
        self._invalidate_campaign_history(campaign_id)
        return int(cursor.lastrowid)

    def finish_campaign_segment(
        self,
        segment_id: int,
        *,
        status: str,
        run_id: int | None,
        end_state: dict[str, Any] | None,
        command_count: int | None,
        duration_seconds: float | None,
        error: str | None = None,
        execution_status: str | None = None,
        objective_outcome: str | None = None,
        safety_outcome: str | None = None,
        metrics: dict[str, Any] | None = None,
    ) -> None:
        campaign_row = self.connection.execute(
            """
            SELECT campaign_id, sequence, command_count, duration_seconds,
                   start_state_json
            FROM campaign_segments
            WHERE id = ?
            """,
            (segment_id,),
        ).fetchone()
        if campaign_row is None:
            return
        campaign_id = int(campaign_row["campaign_id"])
        linked_summary = self.get_run_summary(run_id) if run_id is not None else None
        linked_outcomes = (
            linked_summary.get("outcomes")
            if isinstance(linked_summary, dict)
            and linked_summary.get("summary_version") == RUN_REPORT_SUMMARY_VERSION
            and isinstance(linked_summary.get("outcomes"), dict)
            else None
        )
        if linked_outcomes is not None:
            execution_status = str(linked_outcomes.get("execution") or "unknown")
            objective_outcome = str(linked_outcomes.get("objective") or "unknown")
            safety_outcome = str(linked_outcomes.get("safety") or "unknown")
        try:
            start_state = json.loads(campaign_row["start_state_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            start_state = {}
        if safety_outcome is None and end_state is not None:
            if end_state.get("dead") is True:
                safety_outcome = "unsafe"
            else:
                try:
                    before_loss = int(start_state["xp_loss_total"])
                    after_loss = int(end_state["xp_loss_total"])
                except (KeyError, TypeError, ValueError):
                    safety_outcome = "unknown"
                else:
                    safety_outcome = "loss" if after_loss > before_loss else "safe"
        if objective_outcome is None and end_state is not None:
            objective_kills = end_state.get("campaign_objective_kills")
            if isinstance(objective_kills, (list, tuple)) and objective_kills:
                objective_outcome = "achieved"
            elif (
                end_state.get("campaign_fastwalk_target_absent")
                or end_state.get("campaign_fastwalk_abort_reason")
            ):
                objective_outcome = "not_achieved"
            else:
                objective_outcome = "unknown"
        objective_outcome = objective_outcome or "unknown"
        segment_metrics = dict(metrics or {})
        if linked_summary is not None:
            segment_metrics.setdefault(
                "activity", dict(linked_summary.get("activity") or {}),
            )
        self._ensure_campaign_usage(campaign_id)
        old_commands = int(campaign_row["command_count"] or 0)
        old_duration = float(campaign_row["duration_seconds"] or 0)
        self.connection.execute(
            """
            UPDATE campaign_segments
            SET run_id = ?, finished_at = ?, status = ?, end_state_json = ?,
                command_count = ?, duration_seconds = ?, error = ?,
                execution_status = ?, objective_outcome = ?, safety_outcome = ?,
                metrics_json = ?
            WHERE id = ?
            """,
            (
                run_id,
                _now(),
                status,
                json.dumps(end_state, sort_keys=True) if end_state is not None else None,
                command_count,
                duration_seconds,
                error,
                execution_status or status,
                objective_outcome,
                safety_outcome or "unknown",
                json.dumps(segment_metrics, sort_keys=True),
                segment_id,
            ),
        )
        self.connection.execute(
            """
            UPDATE campaign_usage
            SET command_count = command_count + ?,
                duration_seconds = duration_seconds + ?,
                updated_at = ?
            WHERE campaign_id = ?
            """,
            (
                int(command_count or 0) - old_commands,
                float(duration_seconds or 0) - old_duration,
                _now(),
                campaign_id,
            ),
        )
        self.connection.commit()
        self._invalidate_campaign_history(campaign_id)

    def list_campaign_segments(self, campaign_id: int) -> list[sqlite3.Row]:
        cursor = self.connection.execute(
            """
            SELECT id, campaign_id, sequence, phase, run_id, started_at, finished_at,
                   status, start_state_json, end_state_json, command_count,
                   duration_seconds, error
            FROM campaign_segments
            WHERE campaign_id = ?
            ORDER BY sequence
            """,
            (campaign_id,),
        )
        return list(cursor.fetchall())

    def campaign_totals(self, campaign_id: int) -> sqlite3.Row:
        if self.read_only:
            cached = self.connection.execute(
                """
                SELECT segment_count, command_count, duration_seconds
                FROM campaign_usage
                WHERE campaign_id = ?
                """,
                (campaign_id,),
            ).fetchone()
            if cached is not None:
                return cached
            # Read-only reports must not materialize a missing cache row in a
            # shared database. Return the same aggregate shape without a write.
            return self.connection.execute(
                """
                SELECT COUNT(*) AS segment_count,
                       COALESCE(SUM(command_count), 0) AS command_count,
                       COALESCE(SUM(duration_seconds), 0) AS duration_seconds
                FROM campaign_segments
                WHERE campaign_id = ?
                """,
                (campaign_id,),
            ).fetchone()
        self._ensure_campaign_usage(campaign_id)
        cursor = self.connection.execute(
            """
            SELECT segment_count, command_count, duration_seconds
            FROM campaign_usage
            WHERE campaign_id = ?
            """,
            (campaign_id,),
        )
        return cursor.fetchone()

    def _ensure_campaign_usage(self, campaign_id: int) -> None:
        existing = self.connection.execute(
            "SELECT 1 FROM campaign_usage WHERE campaign_id = ?",
            (campaign_id,),
        ).fetchone()
        if existing is not None:
            return
        aggregate = self.connection.execute(
            """
            SELECT COUNT(*) AS segment_count,
                   COALESCE(SUM(command_count), 0) AS command_count,
                   COALESCE(SUM(duration_seconds), 0) AS duration_seconds
            FROM campaign_segments
            WHERE campaign_id = ?
            """,
            (campaign_id,),
        ).fetchone()
        self.connection.execute(
            """
            INSERT OR IGNORE INTO campaign_usage (
                campaign_id, segment_count, command_count,
                duration_seconds, updated_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                campaign_id,
                int(aggregate["segment_count"]),
                int(aggregate["command_count"]),
                float(aggregate["duration_seconds"]),
                _now(),
            ),
        )
        self.connection.commit()

    def record_campaign_checkpoint(
        self,
        campaign_id: int,
        *,
        segment_id: int | None,
        run_id: int | None,
        phase: str,
        reason: str,
        state: dict[str, Any],
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO campaign_checkpoints (
                campaign_id, segment_id, run_id, phase, reason, created_at, state_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                campaign_id,
                segment_id,
                run_id,
                phase,
                reason,
                _now(),
                json.dumps(state, sort_keys=True),
            ),
        )
        self.connection.commit()
        self._invalidate_campaign_history(campaign_id)
        return int(cursor.lastrowid)

    def get_campaign_checkpoint(self, checkpoint_id: int) -> sqlite3.Row | None:
        """Fetch one exact checkpoint for reproducible experiment setup."""
        return self.connection.execute(
            """
            SELECT id, campaign_id, segment_id, run_id, phase, reason, created_at,
                   state_json
            FROM campaign_checkpoints
            WHERE id = ?
            """,
            (checkpoint_id,),
        ).fetchone()

    def get_latest_campaign_checkpoint(self, campaign_id: int) -> sqlite3.Row | None:
        cursor = self.connection.execute(
            """
            SELECT id, campaign_id, segment_id, run_id, phase, reason, created_at,
                   state_json
            FROM campaign_checkpoints
            WHERE campaign_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (campaign_id,),
        )
        return cursor.fetchone()

    def get_latest_campaign_checkpoint_at_or_above_level(
        self,
        campaign_id: int,
        *,
        target_level: int,
        reasons: Collection[str],
    ) -> sqlite3.Row | None:
        """Return the newest checkpoint that can prove a target level.

        Matrix inspection only needs an existence check.  Keep that path in
        SQLite so a large campaign does not deserialize every historical
        checkpoint just to find one accepted target record.
        """
        reason_values = tuple(dict.fromkeys(str(reason) for reason in reasons if reason))
        if not reason_values:
            return None
        placeholders = ", ".join("?" for _ in reason_values)
        cursor = self.connection.execute(
            f"""
            SELECT id, campaign_id, segment_id, run_id, phase, reason, created_at,
                   state_json
            FROM campaign_checkpoints
            WHERE campaign_id = ?
              AND reason IN ({placeholders})
              AND COALESCE(
                    CAST(json_extract(state_json, '$.level') AS INTEGER), 0
                  ) >= ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (campaign_id, *reason_values, target_level),
        )
        return cursor.fetchone()

    def campaign_has_creation_evidence(self, campaign_id: int) -> bool:
        """Return whether a campaign has a persisted creation decision.

        Join only the starter-run subset to the event index and stop at the
        first matching decision.  Creation decisions are emitted by
        ``StarterBotRunner`` with the durable ``starter:<name>`` scenario
        prefix; avoiding later field runs keeps HERO inspection bounded.
        """
        cursor = self.connection.execute(
            """
            SELECT 1
            FROM campaign_segments AS segment
            JOIN runs AS run ON run.id = segment.run_id
            JOIN events AS event ON event.run_id = segment.run_id
            WHERE segment.campaign_id = ?
              AND run.scenario_name LIKE 'starter:%'
              AND event.kind = 'decision'
              AND json_valid(event.payload_json)
              AND (
                    lower(COALESCE(json_extract(event.payload_json, '$.stage'), ''))
                        LIKE 'create%'
                    OR lower(
                        COALESCE(json_extract(event.payload_json, '$.category'), '')
                    ) = 'creation'
                  )
            LIMIT 1
            """,
            (campaign_id,),
        )
        return cursor.fetchone() is not None

    def list_campaign_checkpoints(self, campaign_id: int) -> list[sqlite3.Row]:
        cursor = self.connection.execute(
            """
            SELECT id, campaign_id, segment_id, run_id, phase, reason, created_at,
                   state_json
            FROM campaign_checkpoints
            WHERE campaign_id = ?
            ORDER BY id
            """,
            (campaign_id,),
        )
        return list(cursor.fetchall())

    def list_campaign_segment_summaries(
        self,
        campaign_id: int,
        *,
        include_state_progress: bool = False,
    ) -> list[sqlite3.Row]:
        """Return compact report fields, projecting state only on explicit request."""
        columns = self._table_columns("campaign_segments")
        optional = ", ".join(
            name if name in columns else f"NULL AS {name}"
            for name in (
                "execution_status", "objective_outcome", "safety_outcome",
                "metrics_json",
            )
        )
        start_projection = (
            "json_object('level', json_extract(start_state_json, '$.level'), "
            "'xp', json_extract(start_state_json, '$.xp'))"
            if include_state_progress else "NULL"
        )
        end_projection = (
            "json_object('level', json_extract(end_state_json, '$.level'), "
            "'xp', json_extract(end_state_json, '$.xp'))"
            if include_state_progress else "NULL"
        )
        cursor = self.connection.execute(
            f"""
            SELECT id, sequence, phase, status, run_id, command_count,
                   duration_seconds, error, started_at, finished_at,
                   {optional},
                   {start_projection} AS start_state_json,
                   {end_projection} AS end_state_json
            FROM campaign_segments
            WHERE campaign_id = ?
            ORDER BY sequence
            """,
            (campaign_id,),
        )
        return list(cursor.fetchall())

    def get_campaign_segment_boundary_states(
        self,
        campaign_id: int,
    ) -> tuple[str | None, str | None]:
        """Read only the first starting state and latest completed end state."""
        start = self.connection.execute(
            """
            SELECT start_state_json
            FROM campaign_segments
            WHERE campaign_id = ?
            ORDER BY sequence
            LIMIT 1
            """,
            (campaign_id,),
        ).fetchone()
        end = self.connection.execute(
            """
            SELECT end_state_json
            FROM campaign_segments
            WHERE campaign_id = ? AND end_state_json IS NOT NULL
            ORDER BY sequence DESC
            LIMIT 1
            """,
            (campaign_id,),
        ).fetchone()
        return (
            str(start["start_state_json"]) if start is not None else None,
            str(end["end_state_json"]) if end is not None else None,
        )

    def get_campaign_checkpoint_boundaries(
        self, campaign_id: int,
    ) -> list[sqlite3.Row]:
        """Read only the first and latest full checkpoints for a report."""
        ids = self.connection.execute(
            """
            SELECT MIN(id) AS first_id, MAX(id) AS last_id
            FROM campaign_checkpoints WHERE campaign_id = ?
            """,
            (campaign_id,),
        ).fetchone()
        values = tuple(dict.fromkeys(
            int(value) for value in (ids["first_id"], ids["last_id"])
            if value is not None
        ))
        if not values:
            return []
        placeholders = ", ".join("?" for _ in values)
        return list(self.connection.execute(
            f"""
            SELECT id, campaign_id, segment_id, run_id, phase, reason,
                   created_at, state_json
            FROM campaign_checkpoints WHERE id IN ({placeholders}) ORDER BY id
            """,
            values,
        ).fetchall())

    def list_recent_campaign_segments(
        self,
        campaign_id: int,
        *,
        limit: int,
    ) -> list[sqlite3.Row]:
        """Return a bounded tail in normal campaign sequence order."""
        if limit < 1:
            raise ValueError("limit must be positive")
        effective_limit = _bounded_campaign_history_limit(self.path, limit)
        cache_key = (campaign_id, effective_limit)
        cached = self._recent_campaign_segments_cache.get(cache_key)
        if cached is not None:
            return list(cached)
        # Select the bounded tail using the narrow campaign index before
        # materializing the large state JSON columns.  Sorting full payloads
        # made resume time grow with the entire shared campaign history.
        id_rows = self.connection.execute(
            """
            SELECT id
            FROM campaign_segments
            WHERE campaign_id = ?
            ORDER BY sequence DESC
            LIMIT ?
            """,
            (campaign_id, effective_limit),
        ).fetchall()
        if not id_rows:
            self._recent_campaign_segments_cache[cache_key] = []
            return []
        ids = tuple(int(row["id"]) for row in id_rows)
        placeholders = ", ".join("?" for _ in ids)
        rows = list(
            self.connection.execute(
                f"""
                SELECT id, campaign_id, sequence, phase, run_id, started_at,
                       finished_at, status, start_state_json, end_state_json,
                       command_count, duration_seconds, error
                FROM campaign_segments
                WHERE id IN ({placeholders})
                ORDER BY sequence, id
                """,
                ids,
            ).fetchall()
        )
        self._recent_campaign_segments_cache[cache_key] = rows
        return list(rows)

    def get_latest_campaign_segment_for_phase(
        self,
        campaign_id: int,
        phase: str,
        *,
        search_limit: int = 256,
    ) -> sqlite3.Row | None:
        """Find one phase without loading historical checkpoint JSON payloads."""
        if type(search_limit) is not int or not 1 <= search_limit <= 256:
            raise ValueError("search_limit must be between 1 and 256")
        # The narrow campaign/sequence index bounds the scan even when the
        # optional phase index is absent from a large production database.
        row = self.connection.execute(
            """
            SELECT id FROM (
                SELECT id, phase, sequence FROM campaign_segments
                WHERE campaign_id = ? ORDER BY sequence DESC LIMIT ?
            ) WHERE phase = ? ORDER BY sequence DESC LIMIT 1
            """,
            (campaign_id, search_limit, phase),
        ).fetchone()
        if row is None:
            return None
        return self.connection.execute(
            "SELECT * FROM campaign_segments WHERE id = ?",
            (row["id"],),
        ).fetchone()

    def get_latest_campaign_segment_summary_for_phase(
        self,
        campaign_id: int,
        phase: str,
        *,
        state_fields: Collection[str],
        search_limit: int = 256,
    ) -> sqlite3.Row | None:
        """Find one phase using only selected fields from its saved states."""
        if type(search_limit) is not int or not 1 <= search_limit <= 256:
            raise ValueError("search_limit must be between 1 and 256")
        fields = tuple(dict.fromkeys(str(field) for field in state_fields))
        if not fields:
            raise ValueError("state_fields must not be empty")
        start_projection, start_parameters = _campaign_state_projection(
            "segment.start_state_json",
            fields,
        )
        end_projection, end_parameters = _campaign_state_projection(
            "segment.end_state_json",
            fields,
        )
        return self.connection.execute(
            f"""
            WITH recent AS MATERIALIZED (
                SELECT id, phase, sequence
                FROM campaign_segments
                WHERE campaign_id = ?
                ORDER BY sequence DESC
                LIMIT ?
            )
            SELECT segment.sequence, segment.phase, segment.status,
                   {start_projection} AS start_state_json,
                   {end_projection} AS end_state_json
            FROM recent
            JOIN campaign_segments AS segment ON segment.id = recent.id
            WHERE recent.phase = ?
            ORDER BY recent.sequence DESC
            LIMIT 1
            """,
            (
                campaign_id,
                search_limit,
                *start_parameters,
                *end_parameters,
                phase,
            ),
        ).fetchone()

    def iter_campaign_segment_summaries_after(
        self,
        campaign_id: int,
        sequence: int,
        *,
        state_fields: Collection[str],
        limit: int = 256,
    ) -> Iterator[sqlite3.Row]:
        """Stream a bounded forward window without full checkpoint states."""
        if type(limit) is not int or not 1 <= limit <= 256:
            raise ValueError("limit must be between 1 and 256")
        fields = tuple(dict.fromkeys(str(field) for field in state_fields))
        if not fields:
            raise ValueError("state_fields must not be empty")
        start_projection, start_parameters = _campaign_state_projection(
            "segment.start_state_json",
            fields,
        )
        end_projection, end_parameters = _campaign_state_projection(
            "segment.end_state_json",
            fields,
        )
        cursor = self.connection.execute(
            f"""
            SELECT segment.sequence, segment.phase, segment.status,
                   {start_projection} AS start_state_json,
                   {end_projection} AS end_state_json
            FROM campaign_segments AS segment
            WHERE segment.campaign_id = ? AND segment.sequence > ?
            ORDER BY segment.sequence
            LIMIT ?
            """,
            (
                *start_parameters,
                *end_parameters,
                campaign_id,
                sequence,
                limit,
            ),
        )
        try:
            yield from cursor
        finally:
            cursor.close()

    def list_campaign_segments_for_phases(
        self,
        campaign_id: int,
        phases: Collection[str],
    ) -> list[sqlite3.Row]:
        """Return all durable segments for a bounded set of phase ids."""
        phase_values = tuple(dict.fromkeys(str(phase) for phase in phases if phase))
        if not phase_values:
            return []
        placeholders = ", ".join("?" for _ in phase_values)
        cursor = self.connection.execute(
            f"""
            SELECT id, campaign_id, sequence, phase, run_id, started_at,
                   finished_at, status, start_state_json, end_state_json,
                   command_count, duration_seconds, error
            FROM campaign_segments
            WHERE campaign_id = ? AND phase IN ({placeholders})
            ORDER BY sequence
            """,
            (campaign_id, *phase_values),
        )
        return list(cursor.fetchall())

    def list_recent_campaign_checkpoints(
        self,
        campaign_id: int,
        *,
        limit: int,
    ) -> list[sqlite3.Row]:
        """Return a bounded checkpoint tail in normal insertion order."""
        if limit < 1:
            raise ValueError("limit must be positive")
        effective_limit = _bounded_campaign_history_limit(self.path, limit)
        cache_key = (campaign_id, effective_limit)
        cached = self._recent_campaign_checkpoints_cache.get(cache_key)
        if cached is not None:
            return list(cached)
        id_rows = self.connection.execute(
            """
            SELECT id
            FROM campaign_checkpoints
            WHERE campaign_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (campaign_id, effective_limit),
        ).fetchall()
        if not id_rows:
            self._recent_campaign_checkpoints_cache[cache_key] = []
            return []
        ids = tuple(int(row["id"]) for row in id_rows)
        placeholders = ", ".join("?" for _ in ids)
        rows = list(
            self.connection.execute(
                f"""
                SELECT id, campaign_id, segment_id, run_id, phase, reason,
                       created_at, state_json
                FROM campaign_checkpoints
                WHERE id IN ({placeholders})
                ORDER BY id
                """,
                ids,
            ).fetchall()
        )
        self._recent_campaign_checkpoints_cache[cache_key] = rows
        return list(rows)

    def list_state_snapshots(
        self, run_id: int, *, limit: int | None = None,
    ) -> list[sqlite3.Row]:
        if limit is not None:
            if type(limit) is not int or limit < 1:
                raise ValueError("snapshot limit must be a positive integer")
            rows = self.connection.execute(
                "SELECT id, run_id, source_event_id, timestamp, reason, state_json "
                "FROM state_snapshots WHERE run_id = ? ORDER BY id DESC LIMIT ?",
                (run_id, limit),
            ).fetchall()
            if rows:
                return list(reversed(rows))
            if not self._table_columns("run_current_states"):
                return []
            current = self.connection.execute(
                """
                SELECT event_id AS id, run_id, event_id AS source_event_id,
                       timestamp, 'current_state' AS reason, state_json
                FROM run_current_states WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()
            return [current] if current is not None else []
        cursor = self.connection.execute(
            """
            SELECT id, run_id, source_event_id, timestamp, reason, state_json
            FROM state_snapshots
            WHERE run_id = ?
            ORDER BY id
            """,
            (run_id,),
        )
        rows = list(cursor.fetchall())
        if rows:
            return rows
        if not self._table_columns("run_current_states"):
            return []
        current = self.connection.execute(
            """
            SELECT event_id AS id, run_id, event_id AS source_event_id,
                   timestamp, 'current_state' AS reason, state_json
            FROM run_current_states WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()
        return [current] if current is not None else []

    def get_latest_state_snapshot(self, run_id: int) -> sqlite3.Row | None:
        cursor = self.connection.execute(
            """
            SELECT id, run_id, source_event_id, timestamp, reason, state_json
            FROM state_snapshots
            WHERE run_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (run_id,),
        )
        row = cursor.fetchone()
        if row is not None:
            return row
        if not self._table_columns("run_current_states"):
            return None
        return self.connection.execute(
            """
            SELECT event_id AS id, run_id, event_id AS source_event_id,
                   timestamp, 'current_state' AS reason, state_json
            FROM run_current_states WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()

    def get_latest_character_state(self, character_name: str) -> dict[str, Any] | None:
        """Return the newest persisted snapshot for one named character."""
        row = None
        if self._table_columns("run_current_states"):
            row = self.connection.execute(
                """
                SELECT state_json FROM run_current_states
                WHERE lower(json_extract(state_json, '$.name')) = ?
                ORDER BY timestamp DESC LIMIT 1
                """,
                (character_name.casefold(),),
            ).fetchone()
        if row is None:
            row = self.connection.execute(
                """
                SELECT state_json FROM state_snapshots
                WHERE lower(json_extract(state_json, '$.name')) = ?
                ORDER BY id DESC LIMIT 1
                """,
                (character_name.casefold(),),
            ).fetchone()
        if row is None:
            return None
        try:
            state = json.loads(row["state_json"])
        except (TypeError, json.JSONDecodeError):
            return None
        if isinstance(state, dict):
            return dict(state)
        return None

    def character_has_acquired_item(
        self,
        character_name: str,
        item_name: str,
    ) -> bool:
        """Return whether observations show this character acquiring an item."""
        expected_item = item_name.casefold()
        known = self.connection.execute(
            """
            SELECT 1
            FROM character_acquired_items
            WHERE character_name = ? COLLATE NOCASE
              AND instr(lower(item_description), ?) > 0
            LIMIT 1
            """,
            (character_name, expected_item),
        ).fetchone()
        if known is not None:
            return True
        backfilled = self.connection.execute(
            """
            SELECT 1
            FROM character_item_backfills
            WHERE character_name = ? COLLATE NOCASE
            """,
            (character_name,),
        ).fetchone()
        if backfilled is not None:
            return False

        cursor = self.connection.execute(
            """
            SELECT id, timestamp, state_json
            FROM state_snapshots
            WHERE reason = 'item_acquired'
              AND lower(json_extract(state_json, '$.name')) = ?
            ORDER BY id DESC
            """,
            (character_name.casefold(),),
        )
        found = False
        for row in cursor:
            try:
                state = json.loads(row["state_json"])
            except (TypeError, json.JSONDecodeError):
                continue
            if not isinstance(state, dict):
                continue
            self._record_character_acquired_items(
                int(row["id"]),
                state,
                timestamp=str(row["timestamp"]),
            )
            for acquisition in state.get("acquired_items", []):
                if not isinstance(acquisition, dict):
                    continue
                description = acquisition.get("item")
                if (
                    isinstance(description, str)
                    and expected_item in description.casefold()
                ):
                    found = True
        self.connection.execute(
            """
            INSERT OR REPLACE INTO character_item_backfills (
                character_name, completed_at
            )
            VALUES (?, ?)
            """,
            (character_name, _now()),
        )
        self.connection.commit()
        return found

    def flush(self) -> None:
        """Release a buffered write transaction before yielding to live I/O."""
        if self._observation_writer is not None:
            self._observation_writer.flush()
        if self.connection.in_transaction:
            self.connection.commit()
        self._events_since_commit = 0

    def close(self) -> None:
        error: BaseException | None = None
        try:
            if self._observation_writer is not None:
                self._observation_writer.close()
                self._observation_writer = None
            if not self.read_only:
                self.flush()
        except BaseException as exc:
            error = exc
        finally:
            self.connection.close()
        if error is not None:
            raise error

    def __enter__(self) -> "RunStorage":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _record_character_acquired_items(
    connection: sqlite3.Connection,
    snapshot_id: int,
    state: dict[str, Any],
    *,
    timestamp: str,
) -> None:
    character_name = state.get("name")
    acquisitions = state.get("acquired_items")
    if not isinstance(character_name, str) or not isinstance(acquisitions, list):
        return
    for acquisition in acquisitions:
        if not isinstance(acquisition, dict):
            continue
        description = acquisition.get("item")
        if not isinstance(description, str) or not description.strip():
            continue
        connection.execute(
            """
            INSERT OR IGNORE INTO character_acquired_items (
                character_name, item_description, first_snapshot_id, first_seen_at
            ) VALUES (?, ?, ?, ?)
            """,
            (character_name, description, snapshot_id, timestamp),
        )
