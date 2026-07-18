import asyncio
import json
import sqlite3

import pytest

from dd4tester.connection import ReadResult
from dd4tester.runner import ScenarioRunner
from dd4tester.scenario import Scenario, ScenarioStep
from dd4tester.telnet import TelnetNegotiation


class FakeConnection:
    def __init__(self) -> None:
        self.closed = False
        self.sent: list[str] = []
        self.reads = [
            ReadResult(
                text="login:",
                gmcp_messages=[
                    "Core.Hello {}",
                    'Room.Info {"num": 1, "name": "The Entrance"}',
                ],
                negotiations=[TelnetNegotiation("WILL", 201)],
            ),
            ReadResult(text="Password:"),
            ReadResult(text="Welcome"),
        ]

    async def connect(self) -> None:
        return None

    async def close(self) -> None:
        self.closed = True

    async def send_command(self, command: str) -> None:
        self.sent.append(command)

    async def read_available(self, timeout: float = 0.25) -> ReadResult:
        if self.reads:
            return self.reads.pop(0)
        return ReadResult()

    async def read_until_quiet(self, *, quiet_timeout: float = 0.25, max_wait: float = 2.0):
        if self.reads:
            return [self.reads.pop(0)]
        return []


def test_runner_records_commands_responses_gmcp_and_state(tmp_path) -> None:
    connection = FakeConnection()
    scenario = Scenario(
        name="login",
        host="localhost",
        port=4000,
        timeout=1,
        database=tmp_path / "runs.sqlite3",
        transcript_dir=tmp_path / "transcripts",
        steps=[
            ScenarioStep("wait_for", "login:", 1),
            ScenarioStep("send", "guest", 1),
            ScenarioStep("send", "guest", 1),
        ],
    )
    runner = ScenarioRunner(
        scenario,
        tmp_path / "login.yaml",
        connection_factory=lambda _scenario: connection,
    )

    result = asyncio.run(runner.run())

    assert result.status == "success"
    assert connection.sent == ["guest", "guest"]
    events = [
        json.loads(line)
        for line in result.transcript_path.read_text(encoding="utf-8").splitlines()
    ]
    kinds = [event["kind"] for event in events]
    assert "command" in kinds
    assert "response" in kinds
    assert "gmcp" in kinds
    assert "game_event" in kinds
    assert "state_snapshot" in kinds
    assert any(
        event["kind"] == "game_event"
        and event["payload"]["type"] == "room_entered"
        and event["payload"]["source"] == "gmcp"
        for event in events
    )
    assert any(event["payload"].get("state") == "telnet_negotiation" for event in events)
    assert result.final_state["room_name"] == "The Entrance"
    assert result.final_state["revision"] == 1

    with sqlite3.connect(result.database_path) as database:
        stored = database.execute(
            "SELECT payload_json FROM events WHERE kind = 'game_event'"
        ).fetchall()
        snapshots = database.execute(
            "SELECT reason, state_json FROM state_snapshots WHERE run_id = ?",
            (result.run_id,),
        ).fetchall()

    assert any(json.loads(row[0])["type"] == "room_entered" for row in stored)
    assert snapshots[0][0] == "room_entered"
    assert json.loads(snapshots[0][1])["room_name"] == "The Entrance"


def test_runner_redacts_environment_backed_commands(tmp_path, monkeypatch) -> None:
    connection = FakeConnection()
    connection.reads = []
    monkeypatch.setenv("DD4_TEST_SECRET", "swordfish")
    scenario = Scenario(
        name="secret",
        host="localhost",
        database=tmp_path / "runs.sqlite3",
        transcript_dir=tmp_path / "transcripts",
        steps=[ScenarioStep("send_env", "DD4_TEST_SECRET", 1)],
    )
    runner = ScenarioRunner(
        scenario,
        tmp_path / "secret.yaml",
        connection_factory=lambda _scenario: connection,
    )

    result = asyncio.run(runner.run())
    transcript = result.transcript_path.read_text(encoding="utf-8")

    assert connection.sent == ["swordfish"]
    assert "swordfish" not in transcript
    assert "[REDACTED]" in transcript


def test_runner_requires_environment_backed_command(tmp_path) -> None:
    connection = FakeConnection()
    connection.reads = []
    scenario = Scenario(
        name="secret",
        host="localhost",
        database=tmp_path / "runs.sqlite3",
        transcript_dir=tmp_path / "transcripts",
        steps=[ScenarioStep("send_env", "MISSING_DD4_SECRET", 1)],
    )
    runner = ScenarioRunner(
        scenario,
        tmp_path / "secret.yaml",
        connection_factory=lambda _scenario: connection,
    )

    with pytest.raises(RuntimeError, match="MISSING_DD4_SECRET"):
        asyncio.run(runner.run())
