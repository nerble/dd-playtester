"""Bound the acknowledgements required for healer-side carrying relief."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class LootCapacityReply:
    command: str | None = None
    deadline: float | None = None
    buffer: str = ""
    failure: str | None = None

    def begin(self, command: str, *, now: float) -> None:
        self.command = command
        self.deadline = now + 5
        self.buffer = ""
        self.failure = None

    def observe(self, text: str, *, now: float) -> None:
        if self.command is None or self.failure is not None or self.acknowledged():
            return
        if self.expired(now):
            self.failure = f"capacity relief {self.command!r} reply exceeded five seconds"
            return
        self.buffer = (self.buffer + text)[-4096:]

    def capacity(self) -> tuple[int, int] | None:
        header = self.buffer.casefold().find("your backpack contains:")
        if self.command != "inventory" or header < 0:
            return None
        match = re.search(r"^\s*You are carrying (\d+)/(\d+) items\.\s*$",
                          self.buffer[header + len("your backpack contains:"):], re.MULTILINE)
        return (int(match[1]), int(match[2])) if match else None

    def acknowledged(self) -> bool:
        if self.failure is not None or self.command is None:
            return False
        if self.command == "inventory":
            return self.capacity() is not None
        verb = self.command.split()[0]
        return verb in {"drop", "sacrifice"} and bool(re.search(
            r"^\s*You " + verb + r" [^\r\n]+\.[ \t]*\n", self.buffer, re.MULTILINE,
        ))

    def expired(self, now: float) -> bool:
        return self.deadline is not None and now >= self.deadline and not self.acknowledged()

    def clear(self) -> None:
        self.command = self.deadline = None
        self.buffer = ""
        self.failure = None


@dataclass
class HealerCarryingCapacity:
    """Own one fixed-budget healer cleanup shared by loot and shop travel."""

    complete: bool = False
    step: int = 0
    attempts: int = 0
    keyword: str | None = None
    limit: int | None = None
    initial_count: int | None = None
    maximum_count: int | None = None
    required_slots: int = 0
    final_count: int | None = None
    failure: str | None = None
    reply: LootCapacityReply = field(default_factory=LootCapacityReply)

    def receipt(self) -> dict[str, object]:
        return {
            "room_vnum": "3054", "complete": self.complete,
            "initial_count": self.initial_count, "maximum_count": self.maximum_count,
            "required_slots": self.required_slots, "final_count": self.final_count,
            "limit": self.limit, "attempts": self.attempts, "failure": self.failure,
        }
