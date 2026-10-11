"""Bounded, session-owned evidence for a dispatched DD4 quit command."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .observations import _DD4_PROMPT, strip_ansi_stream


LOGOUT_CONFIRMATION_SECONDS = 5.0
_FAREWELL = "You bid farewell to the Dragons Domain."
_LINE_START_PROMPT = re.compile(r"^[ \t]*" + _DD4_PROMPT.pattern, _DD4_PROMPT.flags | re.MULTILINE)
_REFUSALS = frozenset({
    "Wimping out eh?  Mobs can't quit!",
    "No way! You are fighting.",
    "You're not DEAD yet... lie still!",
    "You can't quit from a tournament!  Recall to leave.",
    "Wait until you have bought the item on auction.",
    "Wait until you have sold the item on auction.",
})


@dataclass
class LogoutConfirmation:
    status: str = "not_requested"
    started_at: float | None = None
    finished_at: float | None = None
    timeout_seconds: float = LOGOUT_CONFIRMATION_SECONDS
    reply: str | None = None
    error: str | None = None
    _buffer: str = field(default="", repr=False)
    _pending_escape: str = field(default="", repr=False)

    @property
    def acknowledged(self) -> bool:
        return self.status == "confirmed"

    @property
    def deadline(self) -> float | None:
        if self.started_at is None:
            return None
        return self.started_at + self.timeout_seconds

    def begin(self, *, now: float) -> None:
        if self.status != "not_requested":
            raise ValueError("logout confirmation may begin only once per session")
        self.started_at = now
        self.status = "waiting"

    def expire(self, *, now: float) -> None:
        if self.status == "waiting" and self.deadline is not None and now >= self.deadline:
            self.fail("timed_out", "DD4 farewell was not observed before the deadline", now=now)

    def observe(self, text: str, *, now: float) -> None:
        self.expire(now=now)
        if self.status != "waiting":
            return
        cleaned, self._pending_escape = strip_ansi_stream(text, self._pending_escape)
        self._buffer = (self._buffer + cleaned).replace("\r", "\n")
        self._buffer = _LINE_START_PROMPT.sub("\n", self._buffer)
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.strip()
            if line == _FAREWELL:
                self.reply = line
                self.status = "confirmed"
                self.finished_at = now
                self._buffer = self._pending_escape = ""
                return
            if line in _REFUSALS:
                self.reply = line
                self.fail("rejected", line, now=now)
                return
        if len(self._buffer) > 4096 or len(self._pending_escape) > 128:
            self.fail("read_failed", "logout reply exceeded the bounded line buffer", now=now)

    def connection_closed(self, *, now: float) -> None:
        self.expire(now=now)
        if self.status == "waiting":
            self.fail("closed_unconfirmed", "connection closed without a complete DD4 farewell", now=now)

    def fail(self, status: str, error: str, *, now: float) -> None:
        if self.status != "waiting":
            return
        self.status = status
        self.error = error
        self.finished_at = now
        self._buffer = self._pending_escape = ""

    def receipt(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "attempted": self.started_at is not None,
            "acknowledged": self.acknowledged,
            "timeout_seconds": self.timeout_seconds,
            "elapsed_seconds": (
                max(0.0, self.finished_at - self.started_at)
                if self.finished_at is not None and self.started_at is not None
                else None
            ),
            "reply": self.reply,
            "error": self.error,
        }
