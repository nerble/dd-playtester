from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Awaitable, Protocol, TypeVar

from .telnet import TelnetNegotiation, TelnetNegotiator


_T = TypeVar("_T")


def _consume_task_result(task: asyncio.Task[object]) -> None:
    try:
        task.result()
    except BaseException:
        pass


async def _await_hard_bounded(
    awaitable: Awaitable[_T],
    *,
    timeout: float,
    operation: str,
) -> _T:
    """Bound an adapter await without waiting for resistant cancellation."""
    task = asyncio.create_task(awaitable)
    try:
        done, _pending = await asyncio.wait(
            (task,),
            timeout=max(0.01, timeout),
        )
    except BaseException:
        if not task.done():
            task.cancel()
            task.add_done_callback(_consume_task_result)
        raise
    if not done:
        task.cancel()
        task.add_done_callback(_consume_task_result)
        raise TimeoutError(f"{operation} exceeded its {timeout:g} second bound")
    return task.result()


@dataclass
class ReadResult:
    text: str = ""
    raw: bytes = b""
    gmcp_messages: list[str] = field(default_factory=list)
    negotiations: list[TelnetNegotiation] = field(default_factory=list)

    @property
    def empty(self) -> bool:
        return not self.text and not self.raw and not self.gmcp_messages and not self.negotiations


class CommandConnection(Protocol):
    """Transport contract shared by direct Telnet and visible-client adapters."""

    closed: bool

    async def connect(self) -> None: ...

    async def close(self) -> None: ...

    async def send_command(self, command: str) -> None: ...

    async def read_available(self, timeout: float = 0.25) -> ReadResult: ...

    async def read_until_quiet(
        self,
        *,
        quiet_timeout: float = 0.25,
        max_wait: float = 2.0,
    ) -> list[ReadResult]: ...


class TelnetConnection:
    def __init__(
        self,
        host: str,
        port: int,
        *,
        timeout: float = 10.0,
        encoding: str = "utf-8",
        negotiator: TelnetNegotiator | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.encoding = encoding
        self.negotiator = negotiator or TelnetNegotiator()
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self.closed = False

    async def connect(self) -> None:
        self.reader, self.writer = await _await_hard_bounded(
            asyncio.open_connection(self.host, self.port),
            timeout=self.timeout,
            operation="Telnet connection",
        )
        self.closed = False

    async def send_command(self, command: str) -> None:
        if self.writer is None:
            raise RuntimeError("Telnet connection is not open")
        self.writer.write((command + "\n").encode(self.encoding))
        await _await_hard_bounded(
            self.writer.drain(),
            timeout=self.timeout,
            operation="Telnet command send",
        )

    async def read_available(self, timeout: float = 0.25) -> ReadResult:
        if self.reader is None or self.writer is None or self.closed:
            return ReadResult()
        try:
            raw = await _await_hard_bounded(
                self.reader.read(4096),
                timeout=timeout,
                operation="Telnet read",
            )
        except TimeoutError:
            return ReadResult()

        if raw == b"":
            self.closed = True
            return ReadResult(raw=raw)

        chunk = self.negotiator.feed(raw)
        for response in chunk.responses:
            self.writer.write(response)
        if chunk.responses:
            await _await_hard_bounded(
                self.writer.drain(),
                timeout=self.timeout,
                operation="Telnet negotiation send",
            )

        return ReadResult(
            text=chunk.data.decode(self.encoding, errors="replace"),
            raw=raw,
            gmcp_messages=chunk.gmcp_messages,
            negotiations=chunk.negotiations,
        )

    async def read_until_quiet(
        self,
        *,
        quiet_timeout: float = 0.25,
        max_wait: float = 2.0,
    ) -> list[ReadResult]:
        deadline = asyncio.get_running_loop().time() + max_wait
        results: list[ReadResult] = []
        while not self.closed and asyncio.get_running_loop().time() < deadline:
            remaining = max(0.0, deadline - asyncio.get_running_loop().time())
            result = await self.read_available(timeout=min(quiet_timeout, remaining))
            if result.empty:
                break
            results.append(result)
        return results

    async def close(self) -> None:
        self.closed = True
        if self.writer is None:
            return
        self.writer.close()
        try:
            await _await_hard_bounded(
                self.writer.wait_closed(),
                timeout=min(5.0, self.timeout),
                operation="Telnet connection close",
            )
        except (ConnectionError, TimeoutError):
            pass
