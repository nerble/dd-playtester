from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .connection import ReadResult, TelnetConnection
from .credentials import login_environment
from .observations import GameEvent, ObservationParser
from .scenario import Scenario, ScenarioStep, load_scenario
from .state import CharacterState
from .storage import RunStorage
from .transcript import TranscriptRecorder


@dataclass(frozen=True)
class RunResult:
    run_id: int
    status: str
    transcript_path: Path
    database_path: Path
    final_state: dict[str, Any]


class ScenarioRunner:
    def __init__(
        self,
        scenario: Scenario,
        scenario_path: Path,
        *,
        connection_factory: Callable[[Scenario], TelnetConnection] | None = None,
        observation_parser: ObservationParser | None = None,
        character_state: CharacterState | None = None,
    ) -> None:
        self.scenario = scenario
        self.scenario_path = scenario_path
        self.connection_factory = connection_factory or self._default_connection
        self.observation_parser = observation_parser or ObservationParser()
        self.character_state = character_state or CharacterState()
        self._text_buffer = ""

    async def run(self) -> RunResult:
        storage = RunStorage(self.scenario.database)
        run_id = storage.create_run(
            scenario_name=self.scenario.name,
            scenario_path=self.scenario_path,
        )
        recorder = TranscriptRecorder.create(
            self.scenario.transcript_dir,
            scenario_name=self.scenario.name,
            run_id=run_id,
        )
        storage.set_transcript_path(run_id, recorder.path)
        connection = self.connection_factory(self.scenario)

        def record(kind: str, payload: dict[str, Any]) -> None:
            event = recorder.record(kind, payload)
            source_event_id = storage.record_event(
                run_id,
                kind=kind,
                payload=payload,
                timestamp=event.timestamp,
            )
            if kind != "game_event":
                return

            game_event = GameEvent(
                type=str(payload["type"]),
                source=str(payload["source"]),
                data=dict(payload["data"]),
            )
            if not self.character_state.apply(game_event):
                return

            snapshot_payload = {
                "reason": game_event.type,
                "source": game_event.source,
                "state": self.character_state.to_dict(),
            }
            snapshot_event = recorder.record("state_snapshot", snapshot_payload)
            storage.record_event(
                run_id,
                kind="state_snapshot",
                payload=snapshot_payload,
                timestamp=snapshot_event.timestamp,
            )
            storage.record_state_snapshot(
                run_id,
                source_event_id=source_event_id,
                reason=game_event.type,
                state=snapshot_payload["state"],
                timestamp=snapshot_event.timestamp,
            )

        try:
            record("state", {"state": "connecting", "host": self.scenario.host, "port": self.scenario.port})
            await connection.connect()
            record("state", {"state": "connected"})
            await self._capture_reads(connection, record, max_wait=0.5)

            for index, step in enumerate(self.scenario.steps, start=1):
                record("state", {"state": "step_started", "index": index, "action": step.action})
                await self._run_step(step, connection, record)
                record("state", {"state": "step_finished", "index": index, "action": step.action})

            record("state", {"state": "completed"})
            storage.finish_run(run_id, status="success")
            return RunResult(
                run_id,
                "success",
                recorder.path,
                storage.path,
                self.character_state.to_dict(),
            )
        except Exception as exc:
            self._flush_observations(record)
            record("state", {"state": "failed", "error": str(exc)})
            storage.finish_run(run_id, status="failed", error=str(exc))
            raise
        finally:
            await connection.close()
            recorder.close()
            storage.close()

    def _default_connection(self, scenario: Scenario) -> TelnetConnection:
        return TelnetConnection(scenario.host, scenario.port, timeout=scenario.timeout)

    async def _run_step(
        self,
        step: ScenarioStep,
        connection: TelnetConnection,
        record: Callable[[str, dict[str, Any]], None],
    ) -> None:
        if step.action == "send":
            command = str(step.value or "")
            record("command", {"command": command})
            await connection.send_command(command)
            await self._capture_reads(connection, record, max_wait=step.timeout or self.scenario.timeout)
            return

        if step.action == "send_env":
            variable = str(step.value or "")
            command = os.environ.get(variable)
            if command is None:
                raise RuntimeError(f"Required environment variable {variable} is not set")
            record(
                "command",
                {"command": "[REDACTED]", "environment": variable, "redacted": True},
            )
            await connection.send_command(command)
            await self._capture_reads(
                connection,
                record,
                max_wait=step.timeout or self.scenario.timeout,
            )
            return

        if step.action == "wait_for":
            expected = str(step.value or "")
            await self._wait_for_text(
                expected,
                connection,
                record,
                timeout=step.timeout or self.scenario.timeout,
            )
            return

        if step.action == "pause":
            seconds = float(step.value or 0.0)
            record("state", {"state": "paused", "seconds": seconds})
            await asyncio.sleep(seconds)
            await self._capture_reads(connection, record, max_wait=step.timeout or 0.5)
            return

        raise ValueError(f"Unsupported scenario action: {step.action}")

    async def _wait_for_text(
        self,
        expected: str,
        connection: TelnetConnection,
        record: Callable[[str, dict[str, Any]], None],
        *,
        timeout: float,
    ) -> None:
        if self._consume_expected(expected):
            self._flush_observations(record)
            record("state", {"state": "matched", "text": expected})
            return

        deadline = asyncio.get_running_loop().time() + timeout
        while asyncio.get_running_loop().time() < deadline:
            remaining = max(0.0, deadline - asyncio.get_running_loop().time())
            result = await connection.read_available(timeout=min(0.25, remaining))
            self._record_read(result, record)
            if self._consume_expected(expected):
                self._flush_observations(record)
                record("state", {"state": "matched", "text": expected})
                return
            if connection.closed:
                break
        self._flush_observations(record)
        raise TimeoutError(f"Timed out waiting for {expected!r}")

    async def _capture_reads(
        self,
        connection: TelnetConnection,
        record: Callable[[str, dict[str, Any]], None],
        *,
        max_wait: float,
    ) -> None:
        for result in await connection.read_until_quiet(max_wait=max_wait):
            self._record_read(result, record)
        self._flush_observations(record)

    def _record_read(
        self,
        result: ReadResult,
        record: Callable[[str, dict[str, Any]], None],
    ) -> None:
        if result.text:
            self._text_buffer += result.text
            record("response", {"text": result.text})
            self._record_game_events(
                self.observation_parser.feed_text(result.text),
                record,
            )
        for message in result.gmcp_messages:
            record("gmcp", {"message": message})
            self._record_game_events(
                self.observation_parser.feed_gmcp(message),
                record,
            )
        for negotiation in result.negotiations:
            record(
                "state",
                {
                    "state": "telnet_negotiation",
                    "command": negotiation.command,
                    "option": negotiation.option,
                },
            )

    def _flush_observations(
        self,
        record: Callable[[str, dict[str, Any]], None],
    ) -> None:
        self._record_game_events(self.observation_parser.flush_text(), record)

    @staticmethod
    def _record_game_events(
        events: list[GameEvent],
        record: Callable[[str, dict[str, Any]], None],
    ) -> None:
        for event in events:
            record("game_event", event.as_payload())

    def _consume_expected(self, expected: str) -> bool:
        match_index = self._text_buffer.find(expected)
        if match_index == -1:
            return False
        self._text_buffer = self._text_buffer[match_index + len(expected) :]
        return True


async def run_scenario_file(path: str | Path) -> RunResult:
    scenario_path = Path(path)
    scenario = load_scenario(scenario_path)
    if scenario.credential_name is None:
        return await ScenarioRunner(scenario, scenario_path).run()
    with login_environment(scenario.credential_name):
        return await ScenarioRunner(scenario, scenario_path).run()
