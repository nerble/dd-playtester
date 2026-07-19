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
                boot_id TEXT,
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

            CREATE TABLE IF NOT EXISTS mob_kills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                character_name TEXT NOT NULL,
                boot_id TEXT,
                mob_name TEXT NOT NULL,
                xp_gained INTEGER,
                timestamp TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_mob_kills_character
            ON mob_kills(character_name, boot_id, mob_name, id);

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
                UNIQUE(campaign_id, sequence)
            );

            CREATE INDEX IF NOT EXISTS idx_campaign_segments_campaign_id
            ON campaign_segments(campaign_id, sequence);

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

    def set_run_boot_id(self, run_id: int, boot_id: str | None) -> None:
        if boot_id is None:
            return
        self.connection.execute(
            "UPDATE runs SET boot_id = ? WHERE id = ?",
            (boot_id, run_id),
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

    def list_runs(self, *, limit: int = 20) -> list[sqlite3.Row]:
        cursor = self.connection.execute(
            """
            SELECT id, scenario_name, scenario_path, boot_id, started_at,
                   finished_at, status, transcript_path, error
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
            SELECT id, scenario_name, scenario_path, boot_id, started_at,
                   finished_at, status, transcript_path, error
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

    def list_events(self, run_id: int) -> list[sqlite3.Row]:
        """Return the recorded evidence for a run in chronological storage order."""
        cursor = self.connection.execute(
            """
            SELECT id, run_id, timestamp, kind, payload_json
            FROM events
            WHERE run_id = ?
            ORDER BY id
            """,
            (run_id,),
        )
        return list(cursor.fetchall())

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
        timestamp: str | None = None,
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO mob_kills (
                run_id, character_name, boot_id, mob_name, xp_gained, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                character_name,
                boot_id,
                mob_name,
                xp_gained,
                timestamp or _now(),
            ),
        )
        return int(cursor.lastrowid)

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
                       xp_gained, timestamp
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
                       xp_gained, timestamp
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
        self.connection.commit()
        return int(cursor.lastrowid)

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
        self.connection.commit()
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
    ) -> None:
        self.connection.execute(
            """
            UPDATE campaign_segments
            SET run_id = ?, finished_at = ?, status = ?, end_state_json = ?,
                command_count = ?, duration_seconds = ?, error = ?
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
                segment_id,
            ),
        )
        self.connection.commit()

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
        cursor = self.connection.execute(
            """
            SELECT COUNT(*) AS segment_count,
                   COALESCE(SUM(command_count), 0) AS command_count,
                   COALESCE(SUM(duration_seconds), 0) AS duration_seconds
            FROM campaign_segments
            WHERE campaign_id = ?
            """,
            (campaign_id,),
        )
        return cursor.fetchone()

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
        return int(cursor.lastrowid)

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

    def get_latest_character_state(self, character_name: str) -> dict[str, Any] | None:
        """Return the newest persisted snapshot for one named character."""
        cursor = self.connection.execute(
            """
            SELECT state_json
            FROM state_snapshots
            ORDER BY id DESC
            """
        )
        expected = character_name.casefold()
        for row in cursor:
            try:
                state = json.loads(row["state_json"])
            except (TypeError, json.JSONDecodeError):
                continue
            name = state.get("name")
            if isinstance(name, str) and name.casefold() == expected:
                return dict(state)
        return None

    def character_has_acquired_item(
        self,
        character_name: str,
        item_name: str,
    ) -> bool:
        """Return whether observations show this character acquiring an item."""
        cursor = self.connection.execute(
            """
            SELECT state_json
            FROM state_snapshots
            WHERE reason = 'item_acquired'
            ORDER BY id DESC
            """
        )
        expected_name = character_name.casefold()
        expected_item = item_name.casefold()
        for row in cursor:
            try:
                state = json.loads(row["state_json"])
            except (TypeError, json.JSONDecodeError):
                continue
            name = state.get("name")
            if not isinstance(name, str) or name.casefold() != expected_name:
                continue
            for acquisition in state.get("acquired_items", []):
                if not isinstance(acquisition, dict):
                    continue
                description = acquisition.get("item")
                if (
                    isinstance(description, str)
                    and expected_item in description.casefold()
                ):
                    return True
        return False

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
