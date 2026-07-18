from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class RunStorage:
    def __init__(self, path: Path, *, event_commit_interval: int = 100) -> None:
        if event_commit_interval < 1:
            raise ValueError("event_commit_interval must be at least 1")
        self.path = path
        self.event_commit_interval = event_commit_interval
        self._events_since_commit = 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_name TEXT NOT NULL,
                scenario_path TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                transcript_path TEXT,
                error TEXT
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                timestamp TEXT NOT NULL,
                kind TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );

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
            """
        )
        self.connection.commit()

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

    def record_event(
        self,
        run_id: int,
        *,
        kind: str,
        payload: dict[str, Any],
        timestamp: str | None = None,
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO events (run_id, timestamp, kind, payload_json)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, timestamp or _now(), kind, json.dumps(payload, sort_keys=True)),
        )
        self._events_since_commit += 1
        if self._events_since_commit >= self.event_commit_interval:
            self.connection.commit()
            self._events_since_commit = 0
        return int(cursor.lastrowid)

    def record_state_snapshot(
        self,
        run_id: int,
        *,
        source_event_id: int | None,
        reason: str,
        state: dict[str, Any],
        timestamp: str | None = None,
    ) -> int:
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
                timestamp or _now(),
                reason,
                json.dumps(state, sort_keys=True),
            ),
        )
        return int(cursor.lastrowid)

    def finish_run(self, run_id: int, *, status: str, error: str | None = None) -> None:
        self.connection.execute(
            """
            UPDATE runs
            SET finished_at = ?, status = ?, error = ?
            WHERE id = ?
            """,
            (_now(), status, error, run_id),
        )
        self.connection.commit()
        self._events_since_commit = 0

    def list_runs(self, *, limit: int = 20) -> list[sqlite3.Row]:
        cursor = self.connection.execute(
            """
            SELECT id, scenario_name, scenario_path, started_at, finished_at,
                   status, transcript_path, error
            FROM runs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return list(cursor.fetchall())

    def get_run(self, run_id: int) -> sqlite3.Row | None:
        cursor = self.connection.execute(
            """
            SELECT id, scenario_name, scenario_path, started_at, finished_at,
                   status, transcript_path, error
            FROM runs
            WHERE id = ?
            """,
            (run_id,),
        )
        return cursor.fetchone()

    def list_state_snapshots(self, run_id: int) -> list[sqlite3.Row]:
        cursor = self.connection.execute(
            """
            SELECT id, run_id, source_event_id, timestamp, reason, state_json
            FROM state_snapshots
            WHERE run_id = ?
            ORDER BY id
            """,
            (run_id,),
        )
        return list(cursor.fetchall())

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
        return cursor.fetchone()

    def close(self) -> None:
        self.connection.commit()
        self._events_since_commit = 0
        self.connection.close()

    def __enter__(self) -> "RunStorage":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


def _now() -> str:
    return datetime.now(UTC).isoformat()
