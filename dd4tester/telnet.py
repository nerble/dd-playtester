from __future__ import annotations

import json
from dataclasses import dataclass, field

IAC = 255
DONT = 254
DO = 253
WONT = 252
WILL = 251
SB = 250
SE = 240
GMCP = 201
GMCP_CLIENT_NAME = "dd4tester"
GMCP_CLIENT_VERSION = "0.1.0"
GMCP_SUPPORTS = ("Char 1", "Char.Items 1", "Room 1", "Comm 1")

COMMAND_NAMES = {
    DONT: "DONT",
    DO: "DO",
    WONT: "WONT",
    WILL: "WILL",
}


@dataclass(frozen=True)
class TelnetNegotiation:
    command: str
    option: int


@dataclass
class TelnetChunk:
    data: bytes = b""
    responses: list[bytes] = field(default_factory=list)
    gmcp_messages: list[str] = field(default_factory=list)
    negotiations: list[TelnetNegotiation] = field(default_factory=list)


class TelnetNegotiator:
    """Small Telnet state machine that handles option replies and GMCP frames."""

    def __init__(self) -> None:
        self.gmcp_enabled = False
        self._state = "data"
        self._command: int | None = None
        self._sb_option: int | None = None
        self._sb_buffer = bytearray()
        self._gmcp_initialized = False

    def feed(self, chunk: bytes) -> TelnetChunk:
        out = TelnetChunk()
        data = bytearray()

        for byte in chunk:
            if self._state == "data":
                if byte == IAC:
                    self._state = "iac"
                else:
                    data.append(byte)
            elif self._state == "iac":
                self._handle_iac(byte, data)
            elif self._state == "negotiate":
                self._finish_negotiation(byte, out)
            elif self._state == "sb_option":
                self._sb_option = byte
                self._sb_buffer.clear()
                self._state = "sb_data"
            elif self._state == "sb_data":
                if byte == IAC:
                    self._state = "sb_iac"
                else:
                    self._sb_buffer.append(byte)
            elif self._state == "sb_iac":
                self._handle_subnegotiation_iac(byte, out)

        out.data = bytes(data)
        return out

    def _handle_iac(self, byte: int, data: bytearray) -> None:
        if byte == IAC:
            data.append(IAC)
            self._state = "data"
        elif byte in (DO, DONT, WILL, WONT):
            self._command = byte
            self._state = "negotiate"
        elif byte == SB:
            self._state = "sb_option"
        else:
            self._state = "data"

    def _finish_negotiation(self, option: int, out: TelnetChunk) -> None:
        command = self._command
        self._command = None
        self._state = "data"
        if command is None:
            return

        out.negotiations.append(
            TelnetNegotiation(command=COMMAND_NAMES.get(command, str(command)), option=option)
        )
        response = self._negotiate_response(command, option)
        if response:
            out.responses.append(response)
        if option == GMCP and self.gmcp_enabled and not self._gmcp_initialized:
            out.responses.extend(self._gmcp_initialization())
            self._gmcp_initialized = True

    def _negotiate_response(self, command: int, option: int) -> bytes | None:
        if command == WILL:
            if option == GMCP:
                self.gmcp_enabled = True
                return bytes([IAC, DO, GMCP])
            return bytes([IAC, DONT, option])
        if command == DO:
            if option == GMCP:
                self.gmcp_enabled = True
                return bytes([IAC, WILL, GMCP])
            return bytes([IAC, WONT, option])
        if command in (WONT, DONT) and option == GMCP:
            self.gmcp_enabled = False
        return None

    def _handle_subnegotiation_iac(self, byte: int, out: TelnetChunk) -> None:
        if byte == SE:
            if self._sb_option == GMCP:
                out.gmcp_messages.append(self._sb_buffer.decode("utf-8", errors="replace"))
            self._sb_option = None
            self._sb_buffer.clear()
            self._state = "data"
        elif byte == IAC:
            self._sb_buffer.append(IAC)
            self._state = "sb_data"
        else:
            self._state = "sb_data"

    @staticmethod
    def _gmcp_initialization() -> list[bytes]:
        hello = json.dumps(
            {"client": GMCP_CLIENT_NAME, "version": GMCP_CLIENT_VERSION},
            separators=(",", ":"),
        )
        supports = json.dumps(GMCP_SUPPORTS, separators=(",", ":"))
        return [
            gmcp_subnegotiation(f"Core.Hello {hello}"),
            gmcp_subnegotiation(f"Core.Supports.Set {supports}"),
        ]


def gmcp_subnegotiation(payload: str) -> bytes:
    body = payload.encode("utf-8").replace(bytes([IAC]), bytes([IAC, IAC]))
    return bytes([IAC, SB, GMCP]) + body + bytes([IAC, SE])
