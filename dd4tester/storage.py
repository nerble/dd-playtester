from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class RunStorage:
    def __init__(self, path: Path, *, event_commit_interval: int = 25) -> None:
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
        return int(segments.rowcount), int(campaigns.rowcount)

    def fail_campaign_after_timeout(
        self,
        campaign_id: int,
        *,
        reason: str,
        character_name: str | None = None,
    ) -> int:
        """Close one campaign's running records after its bounded runner expires."""
        running_segments = list(
            self.connection.execute(
                """
                SELECT id, run_id, started_at
                FROM campaign_segments
                WHERE campaign_id = ? AND status = 'running'
                ORDER BY id
                """,
                (campaign_id,),
            )
        )
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
                SELECT id, scenario_name, started_at
                FROM runs
                WHERE status = 'running' AND started_at >= ?
                """,
                (segment_started_at,),
            ):
                scenario_name = str(row["scenario_name"]).casefold()
                if scenario_name.endswith(character_suffixes):
                    run_ids.add(int(row["id"]))
        timestamp = _now()
        if run_ids:
            placeholders = ", ".join("?" for _ in run_ids)
            self.connection.execute(
                f"""
                UPDATE runs
                SET finished_at = ?, status = 'failed', error = ?
                WHERE id IN ({placeholders})
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
        return int(segment_cursor.rowcount)

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
            if (
                stored["kind"] != transcript["kind"]
                or stored["timestamp"] != transcript["timestamp"]
                or stored_payload != transcript["payload"]
            ):
                return 0

        last_game_event_id = next(
            (
                int(event["id"])
                for event in reversed(stored_events)
                if event["kind"] == "game_event"
            ),
            None,
        )
        imported = 0
        for transcript in transcript_events[len(stored_events) :]:
            event_id = self.record_event(
                run_id,
                kind=transcript["kind"],
                payload=transcript["payload"],
                timestamp=transcript["timestamp"],
            )
            imported += 1
            if transcript["kind"] == "game_event":
                last_game_event_id = event_id
            elif transcript["kind"] == "state_snapshot":
                payload = transcript["payload"]
                state = payload.get("state")
                if isinstance(state, dict):
                    self.record_state_snapshot(
                        run_id,
                        source_event_id=last_game_event_id,
                        reason=str(payload.get("reason") or "transcript_replay"),
                        state=state,
                        timestamp=transcript["timestamp"],
                    )
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
    ) -> list[sqlite3.Row]:
        """Return filtered game events for a campaign in one indexed join."""
        clauses = [
            "s.campaign_id = ?",
            "e.kind = 'game_event'",
        ]
        parameters: list[Any] = [campaign_id]
        if level is not None:
            clauses.append(
                "CAST(json_extract(s.start_state_json, '$.level') AS INTEGER) = ?"
            )
            parameters.append(level)
        if skill is not None:
            clauses.append(
                "lower(json_extract(e.payload_json, '$.data.skill')) = ?"
            )
            parameters.append(skill.casefold())
        cursor = self.connection.execute(
            f"""
            SELECT e.id, e.run_id, e.timestamp, e.kind, e.payload_json
            FROM events AS e
            JOIN campaign_segments AS s ON s.run_id = e.run_id
            WHERE {' AND '.join(clauses)}
            ORDER BY e.id
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
        cursor = self.connection.execute(
            """
            SELECT r.scenario_name, e.payload_json
            FROM events AS e
            JOIN runs AS r ON r.id = e.run_id
            WHERE e.kind = 'command'
            ORDER BY e.id DESC
            """
        )
        expected_name = character_name.casefold()
        for row in cursor:
            scenario_character = str(row["scenario_name"]).rpartition(":")[2]
            if scenario_character.casefold() != expected_name:
                continue
            try:
                payload = json.loads(row["payload_json"])
            except (TypeError, json.JSONDecodeError):
                continue
            if payload.get("command") == command:
                return True
        return False

    def latest_character_command(
        self,
        character_name: str,
        *,
        prefix: str | None = None,
    ) -> str | None:
        """Return the newest recorded command for a character."""
        cursor = self.connection.execute(
            """
            SELECT r.scenario_name, e.payload_json
            FROM events AS e
            JOIN runs AS r ON r.id = e.run_id
            WHERE e.kind = 'command'
            ORDER BY e.id DESC
            """
        )
        expected_name = character_name.casefold()
        for row in cursor:
            scenario_character = str(row["scenario_name"]).rpartition(":")[2]
            if scenario_character.casefold() != expected_name:
                continue
            try:
                payload = json.loads(row["payload_json"])
            except (TypeError, json.JSONDecodeError):
                continue
            command = payload.get("command")
            if not isinstance(command, str):
                continue
            if prefix is None or command.startswith(prefix):
                return command
        return None

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
            WHERE lower(json_extract(state_json, '$.name')) = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (character_name.casefold(),),
        )
        row = cursor.fetchone()
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
        cursor = self.connection.execute(
            """
            SELECT state_json
            FROM state_snapshots
            WHERE reason = 'item_acquired'
              AND lower(json_extract(state_json, '$.name')) = ?
            ORDER BY id DESC
            """,
            (character_name.casefold(),),
        )
        expected_item = item_name.casefold()
        for row in cursor:
            try:
                state = json.loads(row["state_json"])
            except (TypeError, json.JSONDecodeError):
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
