from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


_ENTRY = re.compile(
    r"^\s*\{\s*&gsn_(?P<skill>[a-z0-9_]+)\s*,\s*"
    r"&gsn_(?P<prerequisite>[a-z0-9_]+)\s*,\s*"
    r"(?P<minimum_percent>\d+)\s*,\s*(?P<scope>[^}]+)\}\s*,?\s*$",
    re.IGNORECASE,
)
_SOURCE_FILE = re.compile(r"^pre_req-(?P<class_name>[a-z0-9_]+)\.c$", re.IGNORECASE)


@dataclass(frozen=True, order=True)
class SkillPrerequisite:
    class_name: str
    skill: str
    prerequisite: str
    minimum_percent: int


def parse_prerequisite_directory(path: str | Path) -> list[SkillPrerequisite]:
    """Parse DD4's pre_req-*.c definitions without compiling server code."""
    directory = Path(path)
    if not directory.is_dir():
        raise ValueError(f"prerequisite directory does not exist: {directory}")

    entries: list[SkillPrerequisite] = []
    for source_path in sorted(directory.glob("pre_req-*.c")):
        match = _SOURCE_FILE.fullmatch(source_path.name)
        if match is None:
            continue
        entries.extend(
            parse_prerequisite_text(
                source_path.read_text(encoding="utf-8"),
                class_name=_normalize(match.group("class_name")),
            )
        )
    if not entries:
        raise ValueError(f"no prerequisite entries found in {directory}")
    return sorted(set(entries))


def parse_prerequisite_text(text: str, *, class_name: str) -> list[SkillPrerequisite]:
    entries: list[SkillPrerequisite] = []
    for line in text.splitlines():
        match = _ENTRY.match(line)
        if match is None:
            continue
        entries.append(
            SkillPrerequisite(
                class_name=_normalize(class_name),
                skill=_normalize(match.group("skill")),
                prerequisite=_normalize(match.group("prerequisite")),
                minimum_percent=int(match.group("minimum_percent")),
            )
        )
    return entries


def write_snapshot(
    path: str | Path,
    entries: Iterable[SkillPrerequisite],
    *,
    repository: str,
    revision: str,
) -> None:
    payload = {
        "repository": repository,
        "revision": revision,
        "prerequisites": [asdict(entry) for entry in sorted(set(entries))],
    }
    Path(path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_snapshot(path: str | Path | None = None) -> tuple[dict[str, str], list[SkillPrerequisite]]:
    snapshot_path = Path(path) if path is not None else _bundled_snapshot_path()
    try:
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"prerequisite snapshot does not exist: {snapshot_path}") from exc

    source = {
        "repository": str(payload.get("repository", "unknown")),
        "revision": str(payload.get("revision", "unknown")),
    }
    entries = [
        SkillPrerequisite(
            class_name=_normalize(str(item["class_name"])),
            skill=_normalize(str(item["skill"])),
            prerequisite=_normalize(str(item["prerequisite"])),
            minimum_percent=int(item["minimum_percent"]),
        )
        for item in payload["prerequisites"]
    ]
    return source, sorted(set(entries))


def requirements_for_skill(
    entries: Iterable[SkillPrerequisite],
    *,
    class_name: str,
    skill: str,
    include_common: bool = True,
) -> list[SkillPrerequisite]:
    normalized_class = _normalize(class_name)
    normalized_skill = _normalize(skill)
    allowed_classes = {normalized_class}
    if include_common:
        allowed_classes.add("common")
    return sorted(
        entry
        for entry in entries
        if entry.class_name in allowed_classes and entry.skill == normalized_skill
    )


def known_skills(
    entries: Iterable[SkillPrerequisite],
    *,
    class_name: str,
    include_common: bool = True,
) -> list[str]:
    normalized_class = _normalize(class_name)
    allowed_classes = {normalized_class}
    if include_common:
        allowed_classes.add("common")
    return sorted({entry.skill for entry in entries if entry.class_name in allowed_classes})


def _bundled_snapshot_path() -> Path:
    return Path(__file__).with_name("data") / "dd4_prerequisites.json"


def _normalize(value: str) -> str:
    return " ".join(value.casefold().replace("_", " ").replace("-", " ").split())
