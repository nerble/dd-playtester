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
