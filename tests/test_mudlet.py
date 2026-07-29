from __future__ import annotations

import asyncio
import json

import pytest

from dd4tester.mudlet import MudletBridge, MudletBridgeError, MudletConnection
from dd4tester.observations import ObservationParser


def test_bridge_generates_script_and_queues_safe_command(tmp_path) -> None:
    bridge = MudletBridge(tmp_path / "shared")

    paths = bridge.initialize()
    script = paths.script_path.read_text(encoding="utf-8")

    assert "send(command, true)" in script
    assert "registerAnonymousEventHandler" in script
    assert "killAnonymousEventHandler" in script
    assert "tempRegexTrigger('^'" in script
    assert "killTrigger(bridge.line_trigger)" in script
    assert "bridge.poll_generation" in script
    assert "return '[' .. table.concat(entries, ',') .. ']'" in script
    assert "'Char.Vitals'" in script
    assert "'Room.Info'" in script
    assert "\\" not in script.split("bridge.command_path = ", 1)[1].splitlines()[0]

    bridge.queue_command("  look  ")

    assert paths.command_path.read_text(encoding="utf-8") == "look\n"


@pytest.mark.parametrize("command", ("", "kill wolf\nquit", "say\tsecret"))
def test_bridge_rejects_unsafe_command_lines(tmp_path, command) -> None:
    bridge = MudletBridge(tmp_path)

    with pytest.raises(MudletBridgeError):
        bridge.queue_command(command)


def test_bridge_reads_structured_events(tmp_path) -> None:
    bridge = MudletBridge(tmp_path)
    paths = bridge.initialize()
    paths.event_path.write_text(
        "\n".join(
            (
                json.dumps(
                    {
                        "timestamp": 123,
                        "kind": "gmcp",
                        "package": "Char.Vitals",
                        "payload": {"hp": 43, "maxhp": 55},
                    }
                ),
                json.dumps(
                    {
                        "timestamp": 124,
                        "kind": "text",
                        "package": "line",
                        "payload": "A prowling wolf is here.",
                    }
                ),
            )
        )
        + "\n",
        encoding="utf-8",
    )

    events = bridge.read_events()

    assert events[0].package == "Char.Vitals"
    assert events[0].payload == {"hp": 43, "maxhp": 55}
    assert events[1].kind == "text"
    assert events[1].payload == "A prowling wolf is here."


def test_bridge_cursor_waits_for_a_complete_jsonl_record(tmp_path) -> None:
    bridge = MudletBridge(tmp_path)
    paths = bridge.initialize()
    encoded = json.dumps(
        {
            "timestamp": 123,
            "kind": "gmcp",
            "package": "Char.Vitals",
            "payload": {"hp": 43},
        }
    )
    paths.event_path.write_text(encoded, encoding="utf-8")

    events, offset = bridge.read_events_since(0)

    assert events == []
    assert offset == 0

    with paths.event_path.open("a", encoding="utf-8") as output:
        output.write("\n")
    events, offset = bridge.read_events_since(offset)

    assert len(events) == 1
    assert events[0].payload == {"hp": 43}
    assert offset == paths.event_path.stat().st_size


def test_mudlet_connection_bootstraps_then_advances_through_bridge_events(tmp_path) -> None:
    bridge = MudletBridge(tmp_path)
    paths = bridge.initialize()
    paths.event_path.write_text(
        json.dumps(
            {
                "timestamp": 122,
                "kind": "text",
                "package": "line",
                "payload": "<69/69 hits 149/191 mana 135/170 move [Midgaard]>",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    connection = MudletConnection(tmp_path, poll_interval=0.001)

    asyncio.run(connection.connect())
    bootstrap = asyncio.run(connection.read_available())
    assert bootstrap.text.startswith("<69/69 hits")
    with paths.event_path.open("a", encoding="utf-8") as output:
        output.write(
            json.dumps(
                {
                    "timestamp": 123,
                    "kind": "gmcp",
                    "package": "Char.Vitals",
                    "payload": {"hp": 43, "maxhp": 55},
                }
            )
            + "\n"
        )
        output.write(
            json.dumps(
                {
                    "timestamp": 124,
                    "kind": "text",
                    "package": "line",
                    "payload": "A prowling wolf is here.",
                }
            )
            + "\n"
        )

    result = asyncio.run(connection.read_available())

    assert result.text == "A prowling wolf is here.\n"
    assert result.gmcp_messages == ['Char.Vitals {"hp":43,"maxhp":55}']
    assert not result.empty
    assert asyncio.run(connection.read_available(timeout=0)).empty


def test_bridge_reduces_gmcp_and_text_with_existing_observation_parser(tmp_path) -> None:
    bridge = MudletBridge(tmp_path)
    paths = bridge.initialize()
    paths.event_path.write_text(
        "\n".join(
            (
                json.dumps(
                    {
                        "timestamp": 123,
                        "kind": "gmcp",
                        "package": "Char.Vitals",
                        "payload": {"hp": 43, "maxhp": 55},
                    }
                ),
                json.dumps(
                    {
                        "timestamp": 124,
                        "kind": "text",
                        "package": "line",
                        "payload": "You are dead!",
                    }
                ),
            )
        )
        + "\n",
        encoding="utf-8",
    )

    events = bridge.parse_events(ObservationParser())

    assert {event.type for event in events} == {
        "health_changed",
        "vitals_changed",
        "character_died",
    }


def test_bridge_reduces_array_gmcp_payloads_without_losing_structure(tmp_path) -> None:
    bridge = MudletBridge(tmp_path)
    paths = bridge.initialize()
    paths.event_path.write_text(
        json.dumps(
            {
                "timestamp": 123,
                "kind": "gmcp",
                "package": "Char.Affect",
                "payload": [[{"name": "armor", "duration": "12"}]],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    events = bridge.parse_events(ObservationParser())

    assert len(events) == 1
    assert events[0].type == "affects_changed"
    assert events[0].data["value"] == [[{"name": "armor", "duration": "12"}]]
