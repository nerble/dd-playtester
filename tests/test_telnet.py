import asyncio

import pytest

from dd4tester.connection import TelnetConnection
from dd4tester.telnet import (
    DO,
    GMCP,
    IAC,
    SB,
    SE,
    WILL,
    TelnetNegotiator,
    gmcp_subnegotiation,
)


class _SlowWriter:
    def __init__(self) -> None:
        self.written: list[bytes] = []

    def write(self, data: bytes) -> None:
        self.written.append(data)

    async def drain(self) -> None:
        await asyncio.sleep(1)

    def close(self) -> None:
        return None

    async def wait_closed(self) -> None:
        return None


def test_telnet_command_send_has_a_transport_timeout() -> None:
    connection = TelnetConnection("mud", 8888, timeout=0.01)
    writer = _SlowWriter()
    connection.writer = writer

    with pytest.raises(TimeoutError):
        asyncio.run(connection.send_command("west"))

    assert writer.written == [b"west\n"]


def test_telnet_negotiates_gmcp_and_captures_payload() -> None:
    negotiator = TelnetNegotiator()

    chunk = negotiator.feed(
        bytes([IAC, WILL, GMCP])
        + b"hello "
        + gmcp_subnegotiation('Core.Hello {"client": "dd4tester"}')
        + b"world"
    )

    assert negotiator.gmcp_enabled is True
    assert chunk.responses == [
        bytes([IAC, DO, GMCP]),
        gmcp_subnegotiation(
            'Core.Hello {"client":"dd4tester","version":"0.1.0"}'
        ),
        gmcp_subnegotiation(
            'Core.Supports.Set ["Char 1","Char.Items 1","Char.Equipment 1","Room 1","Comm 1"]'
        ),
    ]
    assert chunk.data == b"hello world"
    assert chunk.gmcp_messages == ['Core.Hello {"client": "dd4tester"}']
    assert chunk.negotiations[0].command == "WILL"
    assert chunk.negotiations[0].option == GMCP


def test_telnet_parser_handles_partial_negotiation() -> None:
    negotiator = TelnetNegotiator()

    first = negotiator.feed(bytes([IAC, WILL]))
    second = negotiator.feed(bytes([GMCP, IAC, SB, GMCP]) + b"Char.Status {}" + bytes([IAC, SE]))

    assert first.responses == []
    assert second.responses == [
        bytes([IAC, DO, GMCP]),
        gmcp_subnegotiation(
            'Core.Hello {"client":"dd4tester","version":"0.1.0"}'
        ),
        gmcp_subnegotiation(
            'Core.Supports.Set ["Char 1","Char.Items 1","Char.Equipment 1","Room 1","Comm 1"]'
        ),
    ]
    assert second.gmcp_messages == ["Char.Status {}"]
