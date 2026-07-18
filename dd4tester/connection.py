from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from .telnet import TelnetNegotiation, TelnetNegotiator


@dataclass
class ReadResult:
    text: str = ""
    raw: bytes = b""
    gmcp_messages: list[str] = field(default_factory=list)
    negotiations: list[TelnetNegotiation] = field(default_factory=list)

    @property
    def empty(self) -> bool:
        return not self.raw and not self.gmcp_messages and not self.negotiations


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
        self.reader, self.writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port),
            timeout=self.timeout,
        )
        self.closed = False

    async def send_command(self, command: str) -> None:
        if self.writer is None:
            raise RuntimeError("Telnet connection is not open")
        self.writer.write((command + "\n").encode(self.encoding))
        await self.writer.drain()

    async def read_available(self, timeout: float = 0.25) -> ReadResult:
        if self.reader is None or self.writer is None or self.closed:
            return ReadResult()
        try:
            raw = await asyncio.wait_for(self.reader.read(4096), timeout=timeout)
        except TimeoutError:
            return ReadResult()

        if raw == b"":
            self.closed = True
            return ReadResult(raw=raw)

        chunk = self.negotiator.feed(raw)
        for response in chunk.responses:
            self.writer.write(response)
        if chunk.responses:
            await self.writer.drain()

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
            await self.writer.wait_closed()
        except ConnectionError:
            pass
