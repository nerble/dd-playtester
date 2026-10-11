import asyncio
import time
from pathlib import Path

import pytest

from dd4tester.character import CharacterSpec
from dd4tester.connection import ReadResult
from dd4tester.logout import LogoutConfirmation
from dd4tester.observations import GameEvent
from dd4tester.sessions import LiveSessionState
from dd4tester.starter import StarterBotRunner, StarterPolicy
from dd4tester.state import CharacterState


FAREWELL = "You bid farewell to the Dragons Domain."
PROMPT = "<743/767 hits 340/340 mana 460/460 moves [Midgaard]> "


def _confirmation() -> LogoutConfirmation:
    confirmation = LogoutConfirmation()
    confirmation.begin(now=10)
    return confirmation


def test_logout_requires_complete_exact_farewell() -> None:
    confirmation = _confirmation()
    confirmation.observe("The Healer says '" + FAREWELL + "'\n", now=11)
    assert confirmation.status == "waiting"
    confirmation.observe(FAREWELL[:-1] + "\n", now=12)
    assert confirmation.status == "waiting"
    confirmation.observe(FAREWELL, now=13)
    assert not confirmation.acknowledged
    confirmation.observe("\n\r", now=14)
    assert confirmation.acknowledged
    assert confirmation.receipt()["reply"] == FAREWELL


def test_logout_preserves_split_prompt_farewell_and_ansi() -> None:
    confirmation = _confirmation()
    confirmation.observe(PROMPT[:30], now=10.1)
    confirmation.observe(PROMPT[30:] + "\x1b[38;5;", now=10.2)
    confirmation.observe("15m" + FAREWELL[:17], now=10.3)
    confirmation.observe(FAREWELL[17:] + "\x1b[0m\n\r", now=10.4)
    assert confirmation.acknowledged
    assert confirmation.receipt()["elapsed_seconds"] == pytest.approx(0.4)
    assert "_buffer" not in confirmation.receipt()


def test_logout_does_not_split_a_prompt_quoted_inside_chatter() -> None:
    confirmation = _confirmation()
    confirmation.observe("Someone says '" + PROMPT + FAREWELL + "\n", now=11)
    assert not confirmation.acknowledged
    confirmation.observe(PROMPT + FAREWELL + "\n", now=12)
    assert confirmation.acknowledged


@pytest.mark.parametrize("reply", [
    "Wimping out eh?  Mobs can't quit!",
    "No way! You are fighting.",
    "You're not DEAD yet... lie still!",
    "You can't quit from a tournament!  Recall to leave.",
    "Wait until you have bought the item on auction.",
    "Wait until you have sold the item on auction.",
])
def test_logout_records_source_refusal_without_retry(reply: str) -> None:
    confirmation = _confirmation()
    confirmation.observe(PROMPT + reply + "\n\r", now=11)
    assert confirmation.status == "rejected"
    confirmation.observe(FAREWELL + "\n", now=12)
    assert not confirmation.acknowledged
    with pytest.raises(ValueError, match="only once"):
        confirmation.begin(now=12)


def test_logout_chatter_never_extends_deadline_or_accepts_late_reply() -> None:
    confirmation = _confirmation()
    confirmation.observe("The Healer smiles.\n", now=14.99)
    assert confirmation.deadline == 15
    confirmation.observe(FAREWELL + "\n", now=15)
    assert confirmation.status == "timed_out"
    confirmation.observe(FAREWELL + "\n", now=16)
    assert not confirmation.acknowledged


@pytest.mark.parametrize("text", ["", "You bid farewell", FAREWELL])
def test_logout_eof_is_not_a_complete_farewell(text: str) -> None:
    confirmation = _confirmation()
    confirmation.observe(text, now=11)
    confirmation.connection_closed(now=11.1)
    assert confirmation.status == "closed_unconfirmed"


def test_logout_has_bounded_incomplete_line_and_escape_buffers() -> None:
    for text in ("x" * 4097, "\x1b[" + "1;" * 100):
        confirmation = _confirmation()
        confirmation.observe(text, now=11)
        assert confirmation.status == "read_failed"
        assert not confirmation.acknowledged


def test_logout_receipt_is_owned_by_one_session() -> None:
    first = LiveSessionState(CharacterState())
    second = LiveSessionState(CharacterState())
    first.logout.begin(now=0)
    first.logout.fail("send_failed", "bounded write timeout", now=0.1)
    assert first.logout.receipt()["status"] == "send_failed"
    assert second.logout.status == "not_requested"


class _LogoutConnection:
    def __init__(self, replies: list[ReadResult], *, hang: bool = False) -> None:
        self.replies = list(replies)
        self.closed = False
        self.hang = hang
        self.sent: list[str] = []

    async def read_available(self, timeout: float = 0.25) -> ReadResult:
        if self.hang:
            await asyncio.sleep(60)
        if self.replies:
            return self.replies.pop(0)
        self.closed = True
        return ReadResult()

    async def send_command(self, command: str) -> None:
        self.sent.append(command)
        raise AssertionError("confirmation must not dispatch extra commands")


def _runner_and_policy():
    spec = CharacterSpec("Testbot", "TEST_PASSWORD", "human", "neuter", "warrior")
    runner = StarterBotRunner(spec, Path("starter.yaml"))
    policy = StarterPolicy(spec, "not-recorded")
    policy.bind_session_state(runner.session_state)
    runner.session_state.authenticated = True
    runner.session_state.in_world = True
    return runner, policy


def test_runner_logout_records_final_text_and_gmcp_without_more_commands() -> None:
    runner, policy = _runner_and_policy()
    connection = _LogoutConnection([
        ReadResult(text=FAREWELL[:10]),
        ReadResult(text=FAREWELL[10:] + "\n\r", gmcp_messages=['Char.Vitals {"hp": 700}']),
    ])
    records = []

    def record(kind, payload):
        records.append((kind, payload))
        if kind == "game_event":
            runner.session_state.apply(GameEvent(payload["type"], payload["source"], payload["data"]))

    asyncio.run(runner._confirm_logout(connection, record, policy))
    assert connection.sent == []
    assert [p["text"] for k, p in records if k == "response"] == [FAREWELL[:10], FAREWELL[10:] + "\n\r"]
    assert any(k == "gmcp" for k, _ in records)
    receipts = [p for k, p in records if k == "logout_confirmation"]
    assert [p["status"] for p in receipts] == ["waiting", "confirmed"]
    assert not runner.session_state.in_world
    assert not runner.session_state.authenticated


@pytest.mark.parametrize("replies,status", [
    ([], "closed_unconfirmed"),
    ([ReadResult(text="No way! You are fighting.\n")], "rejected"),
    ([ReadResult(text="The Healer smiles.\n")], "closed_unconfirmed"),
])
def test_runner_logout_failure_is_visible_and_never_reconnects(replies, status) -> None:
    runner, policy = _runner_and_policy()
    connection = _LogoutConnection(replies)
    records = []
    with pytest.raises(RuntimeError, match="logout was not confirmed"):
        asyncio.run(runner._confirm_logout(connection, lambda k, p: records.append((k, p)), policy))
    assert runner.session_state.logout.status == status
    assert connection.sent == []
    assert runner.session_state.in_world
    assert records[-1][0] == "logout_confirmation"
    assert records[-1][1]["acknowledged"] is False


def test_runner_logout_hard_bounds_a_hanging_adapter() -> None:
    runner, policy = _runner_and_policy()
    runner.session_state.logout.timeout_seconds = 0.02
    connection = _LogoutConnection([], hang=True)
    records = []
    started = time.monotonic()
    with pytest.raises(TimeoutError, match="hard timeout"):
        asyncio.run(runner._confirm_logout(connection, lambda k, p: records.append((k, p)), policy))
    assert time.monotonic() - started < 0.5
    assert runner.session_state.logout.status == "read_failed"
    assert connection.sent == []
