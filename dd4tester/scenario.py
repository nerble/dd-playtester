from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ScenarioStep:
    action: str
    value: str | float | None = None
    timeout: float | None = None


@dataclass(frozen=True)
class Scenario:
    name: str
    host: str
    port: int = 23
    timeout: float = 10.0
    database: Path = Path("runs/dd4tester.sqlite3")
    transcript_dir: Path = Path("transcripts")
    steps: list[ScenarioStep] = field(default_factory=list)


def load_scenario(path: str | Path) -> Scenario:
    scenario_path = Path(path)
    data = _load_yaml_mapping(scenario_path)
    steps = [_parse_step(raw, index) for index, raw in enumerate(data.get("steps", []), start=1)]
    if not steps:
        raise ValueError(f"{scenario_path} must define at least one step")

    name = str(data.get("name") or scenario_path.stem)
    host = data.get("host")
    if not host:
        raise ValueError(f"{scenario_path} must define host")

    return Scenario(
        name=name,
        host=str(host),
        port=int(data.get("port", 23)),
        timeout=float(data.get("timeout", 10.0)),
        database=Path(str(data.get("database", "runs/dd4tester.sqlite3"))),
        transcript_dir=Path(str(data.get("transcript_dir", "transcripts"))),
        steps=steps,
    )


def _parse_step(raw: Any, index: int) -> ScenarioStep:
    if not isinstance(raw, dict):
        raise ValueError(f"Step {index} must be a mapping")

    timeout = float(raw["timeout"]) if "timeout" in raw else None
    if "send" in raw:
        value = raw["send"]
        return ScenarioStep("send", "" if value is None else str(value), timeout)
    if "send_env" in raw:
        return ScenarioStep("send_env", str(raw["send_env"]), timeout)
    if "wait_for" in raw:
        return ScenarioStep("wait_for", str(raw["wait_for"]), timeout)
    if "pause" in raw:
        return ScenarioStep("pause", float(raw["pause"]), timeout)
    if "action" in raw:
        return ScenarioStep(str(raw["action"]), raw.get("value"), timeout)
    raise ValueError(
        f"Step {index} must define send, send_env, wait_for, pause, or action"
    )


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        data = _load_simple_yaml(text)
    else:
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def _load_simple_yaml(text: str) -> dict[str, Any]:
    lines = _logical_lines(text)
    index = 0
    data: dict[str, Any] = {}

    while index < len(lines):
        indent, content = lines[index]
        if indent != 0:
            raise ValueError(f"Unexpected indentation: {content}")
        key, value = _split_key_value(content)
        if value:
            data[key] = _parse_scalar(value)
            index += 1
            continue

        index += 1
        if index >= len(lines):
            data[key] = None
        elif lines[index][1].startswith("- "):
            data[key], index = _parse_list(lines, index, lines[index][0])
        else:
            data[key], index = _parse_mapping(lines, index, lines[index][0])
    return data


def _logical_lines(text: str) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    for raw in text.splitlines():
        stripped = _strip_comment(raw.rstrip())
        if not stripped.strip():
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        result.append((indent, stripped.strip()))
    return result


def _parse_list(
    lines: list[tuple[int, str]],
    index: int,
    indent: int,
) -> tuple[list[Any], int]:
    items: list[Any] = []
    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent != indent or not content.startswith("- "):
            break
        item_content = content[2:].strip()
        if not item_content:
            item: Any = {}
        elif ":" in item_content:
            key, value = _split_key_value(item_content)
            item = {key: _parse_scalar(value)}
        else:
            item = _parse_scalar(item_content)
        index += 1

        if isinstance(item, dict):
            while index < len(lines) and lines[index][0] > indent:
                key, value = _split_key_value(lines[index][1])
                item[key] = _parse_scalar(value)
                index += 1
        items.append(item)
    return items, index


def _parse_mapping(
    lines: list[tuple[int, str]],
    index: int,
    indent: int,
) -> tuple[dict[str, Any], int]:
    data: dict[str, Any] = {}
    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent != indent:
            break
        key, value = _split_key_value(content)
        data[key] = _parse_scalar(value)
        index += 1
    return data, index


def _split_key_value(content: str) -> tuple[str, str]:
    quote: str | None = None
    for index, char in enumerate(content):
        if char in ("'", '"'):
            quote = None if quote == char else char
        elif char == ":" and quote is None:
            return content[:index].strip(), content[index + 1 :].strip()
    raise ValueError(f"Expected key/value pair: {content}")


def _parse_scalar(value: str) -> str | int | float | bool | None:
    if value == "":
        return None
    if value in ("null", "None", "~"):
        return None
    if value in ("true", "True"):
        return True
    if value in ("false", "False"):
        return False
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _strip_comment(line: str) -> str:
    quote: str | None = None
    for index, char in enumerate(line):
        if char in ("'", '"'):
            quote = None if quote == char else char
        elif char == "#" and quote is None:
            return line[:index].rstrip()
    return line
