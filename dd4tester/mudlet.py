from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .connection import ReadResult
from .observations import GameEvent, ObservationParser


class MudletBridgeError(ValueError):
    """Raised when bridge files cannot safely exchange a message."""


@dataclass(frozen=True)
class MudletBridgePaths:
    directory: Path
    command_path: Path
    event_path: Path
    script_path: Path

    @classmethod
    def for_directory(cls, directory: Path) -> "MudletBridgePaths":
        return cls(
            directory=directory,
            command_path=directory / "commands.txt",
            event_path=directory / "events.jsonl",
            script_path=directory / "dd4tester_bridge.lua",
        )


@dataclass(frozen=True)
class MudletBridgeEvent:
    timestamp: int | float | str | None
    kind: str
    package: str | None
    payload: Any


class MudletBridge:
    """Shared-file adapter between the autonomy engine and a Mudlet profile."""

    def __init__(self, directory: Path) -> None:
        self.paths = MudletBridgePaths.for_directory(directory)

    def initialize(self) -> MudletBridgePaths:
        self.paths.directory.mkdir(parents=True, exist_ok=True)
        self.paths.command_path.touch(exist_ok=True)
        self.paths.event_path.touch(exist_ok=True)
        self.paths.script_path.write_text(
            render_mudlet_bridge_lua(self.paths),
            encoding="utf-8",
            newline="\n",
        )
        return self.paths

    def queue_command(self, command: str) -> None:
        validated = _validate_command(command)
        self.paths.directory.mkdir(parents=True, exist_ok=True)
        with self.paths.command_path.open("a", encoding="utf-8", newline="\n") as output:
            output.write(validated + "\n")

    def read_events(self) -> list[MudletBridgeEvent]:
        events, _offset = self.read_events_since(0)
        return events

    def read_events_since(self, offset: int) -> tuple[list[MudletBridgeEvent], int]:
        """Read complete JSONL records appended after a byte offset."""

        if offset < 0:
            raise MudletBridgeError("Mudlet event offset cannot be negative")
        if not self.paths.event_path.exists():
            return [], offset

        with self.paths.event_path.open("rb") as input_file:
            input_file.seek(0, 2)
            file_size = input_file.tell()
            if offset > file_size:
                offset = 0
            input_file.seek(offset)
            pending = input_file.read()

        events: list[MudletBridgeEvent] = []
        consumed = 0
        for line_number, raw_line in enumerate(
            pending.splitlines(keepends=True),
            start=1,
        ):
            if not raw_line.endswith(b"\n"):
                break
            consumed += len(raw_line)
            line = raw_line.decode("utf-8").strip()
            if not line:
                continue
            events.append(_decode_bridge_event(line, line_number=line_number))
        return events, offset + consumed

    def parse_events(self, parser: ObservationParser) -> list[GameEvent]:
        """Reduce bridge output through the same parser used by Telnet runs."""

        game_events: list[GameEvent] = []
        for event in self.read_events():
            if event.kind == "gmcp" and event.package:
                encoded_payload = json.dumps(event.payload)
                game_events.extend(
                    parser.feed_gmcp(f"{event.package} {encoded_payload}")
                )
            elif event.kind == "text" and event.package == "line":
                game_events.extend(parser.feed_text(f"{event.payload}\n"))
        return game_events


class MudletConnection:
    """Expose a running Mudlet profile through the direct runner contract."""

    def __init__(
        self,
        directory: Path,
        *,
        poll_interval: float = 0.05,
    ) -> None:
        if poll_interval <= 0:
            raise ValueError("Mudlet poll_interval must be positive")
        self.bridge = MudletBridge(directory)
        self.poll_interval = poll_interval
        self.closed = True
        self._event_offset = 0

    async def connect(self) -> None:
        paths = self.bridge.paths
        missing = [
            path.name
            for path in (paths.command_path, paths.event_path, paths.script_path)
            if not path.is_file()
        ]
        if missing:
            names = ", ".join(missing)
            raise RuntimeError(
                "Mudlet bridge is not initialized; run "
                f"'python -m dd4tester mudlet-bridge --directory {paths.directory}' "
                f"first (missing: {names})"
            )
        # The active Mudlet profile may already have received the initial
        # prompt and GMCP snapshots before DD4Tester starts. Consume that
        # current bridge snapshot once so the policy can bootstrap in-world.
        self._event_offset = 0
        self.closed = False

    async def close(self) -> None:
        self.closed = True

    async def send_command(self, command: str) -> None:
        if self.closed:
            raise RuntimeError("Mudlet bridge is not open")
        self.bridge.queue_command(command)

    async def read_available(self, timeout: float = 0.25) -> ReadResult:
        if self.closed:
            return ReadResult()
        deadline = asyncio.get_running_loop().time() + max(timeout, 0.0)
        while not self.closed:
            result = self._drain_events()
            if not result.empty:
                return result
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                break
            await asyncio.sleep(min(self.poll_interval, remaining))
        return ReadResult()

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

    def _drain_events(self) -> ReadResult:
        events, self._event_offset = self.bridge.read_events_since(self._event_offset)
        text: list[str] = []
        gmcp_messages: list[str] = []
        for event in events:
            if event.kind == "text" and event.package == "line":
                text.append(f"{event.payload}\n")
            elif event.kind == "gmcp" and event.package:
                gmcp_messages.append(
                    f"{event.package} {json.dumps(event.payload, separators=(',', ':'))}"
                )
        return ReadResult(text="".join(text), gmcp_messages=gmcp_messages)


def render_mudlet_bridge_lua(paths: MudletBridgePaths) -> str:
    """Render a Mudlet script which polls commands and records GMCP events."""

    command_path = _lua_path(paths.command_path)
    event_path = _lua_path(paths.event_path)
    return f'''-- Generated by DD4Tester. Do not place credentials in commands.txt.
DD4TesterBridge = DD4TesterBridge or {{}}
local bridge = DD4TesterBridge

bridge.command_path = [[{command_path}]]
bridge.event_path = [[{event_path}]]
bridge.command_offset = bridge.command_offset or 0

local function encode_string(value)
  local escaped = value:gsub('[%z\1-\31\\"]', function(character)
    local escapes = {{['\\'] = '\\\\', ['"'] = '\\"', ['\b'] = '\\b', ['\f'] = '\\f', ['\n'] = '\\n', ['\r'] = '\\r', ['\t'] = '\\t'}}
    return escapes[character] or string.format('\\u%04x', string.byte(character))
  end)
  return '"' .. escaped .. '"'
end

local function array_length(value)
  local count = 0
  local maximum = 0
  for key, _ in pairs(value) do
    if type(key) ~= 'number' or key < 1 or key % 1 ~= 0 then return nil end
    count = count + 1
    if key > maximum then maximum = key end
  end
  if maximum ~= count then return nil end
  return maximum
end

local function encode(value)
  local value_type = type(value)
  if value_type == 'nil' then return 'null' end
  if value_type == 'boolean' or value_type == 'number' then return tostring(value) end
  if value_type == 'string' then return encode_string(value) end
  if value_type ~= 'table' then return encode_string(tostring(value)) end

  local length = array_length(value)
  if length ~= nil then
    local entries = {{}}
    for index = 1, length do table.insert(entries, encode(value[index])) end
    return '[' .. table.concat(entries, ',') .. ']'
  end

  local entries = {{}}
  for key, child in pairs(value) do
    table.insert(entries, encode_string(tostring(key)) .. ':' .. encode(child))
  end
  table.sort(entries)
  return '{{' .. table.concat(entries, ',') .. '}}'
end

function bridge.emit(kind, package, payload)
  local output = io.open(bridge.event_path, 'a')
  if output == nil then return end
  output:write(encode({{timestamp = os.time(), kind = kind, package = package, payload = payload}}) .. '\\n')
  output:close()
end

function bridge.record_line(line)
  if type(line) == 'string' then bridge.emit('text', 'line', line) end
end

if bridge.line_trigger then killTrigger(bridge.line_trigger) end
bridge.line_trigger = tempRegexTrigger('^', function()
  bridge.record_line(line)
end)

local function gmcp_value(package)
  local value = gmcp
  for part in string.gmatch(package, '[^%.]+') do
    if value == nil then return {{}} end
    value = value[part]
  end
  return value or {{}}
end

local function register_gmcp(package)
  local handler = registerAnonymousEventHandler('gmcp.' .. package, function()
    bridge.emit('gmcp', package, gmcp_value(package))
  end)
  table.insert(bridge.gmcp_handlers, handler)
end

if bridge.gmcp_handlers then
  for _, handler in ipairs(bridge.gmcp_handlers) do
    killAnonymousEventHandler(handler)
  end
end
bridge.gmcp_handlers = {{}}

for _, package in ipairs({{
  'Core.Prompt', 'Room.Info', 'Char.Base', 'Char.Vitals', 'Char.Status',
  'Char.Stats', 'Char.Worth', 'Char.Affect', 'Char.Items',
  'Char.Items.Add', 'Char.Equipment', 'Char.Enemies', 'Combat.Start'
}}) do
  register_gmcp(package)
end

function bridge.drain_commands()
  local input = io.open(bridge.command_path, 'r')
  if input == nil then return end
  input:seek('set', bridge.command_offset)
  for command in input:lines() do
    if command ~= '' then
      send(command, true)
      bridge.emit('command', 'outgoing', {{command = command}})
    end
  end
  bridge.command_offset = input:seek()
  input:close()
end

if bridge.poll_timer then killTimer(bridge.poll_timer) end
bridge.poll_generation = (bridge.poll_generation or 0) + 1
local poll_generation = bridge.poll_generation

function bridge.poll(token)
  if token ~= bridge.poll_generation then return end
  bridge.drain_commands()
  bridge.poll_timer = tempTimer(0.25, function() bridge.poll(token) end)
end

bridge.poll(poll_generation)
'''


def _validate_command(command: str) -> str:
    if not isinstance(command, str):
        raise MudletBridgeError("Mudlet commands must be text")
    normalized = command.strip()
    if not normalized:
        raise MudletBridgeError("Mudlet commands cannot be empty")
    if any(ord(character) < 32 or ord(character) == 127 for character in normalized):
        raise MudletBridgeError("Mudlet commands cannot contain control characters")
    return normalized


def _lua_path(path: Path) -> str:
    normalized = str(path.resolve()).replace("\\", "/")
    if "]]" in normalized:
        raise MudletBridgeError("Mudlet bridge paths cannot contain ']]'")
    return normalized


def _decode_bridge_event(line: str, *, line_number: int) -> MudletBridgeEvent:
    try:
        raw_event = json.loads(line)
    except json.JSONDecodeError as exc:
        raise MudletBridgeError(
            f"invalid JSONL bridge event at line {line_number}"
        ) from exc
    if not isinstance(raw_event, dict):
        raise MudletBridgeError(
            f"bridge event at line {line_number} is not an object"
        )
    kind = raw_event.get("kind")
    if not isinstance(kind, str) or not kind:
        raise MudletBridgeError(
            f"bridge event at line {line_number} has no kind"
        )
    package = raw_event.get("package")
    if package is not None and not isinstance(package, str):
        raise MudletBridgeError(
            f"bridge event at line {line_number} has an invalid package"
        )
    return MudletBridgeEvent(
        timestamp=raw_event.get("timestamp"),
        kind=kind,
        package=package,
        payload=raw_event.get("payload"),
    )
