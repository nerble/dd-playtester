from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any


DEFAULT_DD4_CONST = Path("runs/dd4-source/server/src/const.c")
_QUOTED_STRING = re.compile(r'"((?:\\.|[^"\\])*)"')
_CREATION_SEX_BLOCK = re.compile(
    r"case\s+CON_GET_NEW_SEX\s*:(?P<body>.*?)case\s+CON_DISPLAY_CLASS\s*:",
    re.DOTALL,
)
_CREATION_SEX_ASSIGNMENT = re.compile(
    r"(?:case\s+'[A-Za-z]'\s*:\s*)+"
    r"ch->sex\s*=\s*SEX_(?P<sex>MALE|FEMALE|NEUTRAL)\s*;"
)
_SEX_CONSTANT_NAMES = {"MALE": "male", "FEMALE": "female", "NEUTRAL": "neuter"}


@dataclass(frozen=True)
class RaceOption:
    name: str
    display_name: str
    creation_choice: str


@dataclass(frozen=True)
class ClassOption:
    name: str
    display_name: str


@dataclass(frozen=True)
class SubclassOption:
    name: str
    display_name: str
    base_class: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class CharacterCatalog:
    races: tuple[RaceOption, ...]
    classes: tuple[ClassOption, ...]
    subclasses: tuple[SubclassOption, ...]
    sexes: tuple[str, ...] = ("male", "female", "neuter")
    source: str = ""
    source_revision: str | None = None

    def race_name(self, value: str) -> str:
        normalized = normalize_option(value)
        for option in self.races:
            if normalized in {option.name, normalize_option(option.display_name)}:
                return option.name
        raise _unknown_option("race", value, (option.name for option in self.races))

    def class_name(self, value: str) -> str:
        normalized = normalize_option(value)
        for option in self.classes:
            if normalized in {option.name, normalize_option(option.display_name)}:
                return option.name
        raise _unknown_option(
            "class", value, (option.name for option in self.classes)
        )

    def subclass_option(self, value: str) -> SubclassOption:
        normalized = normalize_option(value)
        for option in self.subclasses:
            accepted = {
                option.name,
                normalize_option(option.display_name),
                *option.aliases,
            }
            if normalized in accepted:
                return option
        raise _unknown_option(
            "subclass", value, (option.name for option in self.subclasses)
        )

    def sex_name(self, value: str) -> str:
        normalized = normalize_option(value)
        if normalized not in self.sexes:
            raise _unknown_option("sex", value, self.sexes)
        return normalized

    def to_mapping(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "source_revision": self.source_revision,
            "sexes": list(self.sexes),
            "races": [
                {
                    "name": option.name,
                    "display_name": option.display_name,
                    "creation_choice": option.creation_choice,
                }
                for option in self.races
            ],
            "classes": [
                {"name": option.name, "display_name": option.display_name}
                for option in self.classes
            ],
            "subclasses": [
                {
                    "name": option.name,
                    "display_name": option.display_name,
                    "base_class": option.base_class,
                    "aliases": list(option.aliases),
                }
                for option in self.subclasses
            ],
        }

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "CharacterCatalog":
        return cls(
            races=tuple(RaceOption(**item) for item in data["races"]),
            classes=tuple(ClassOption(**item) for item in data["classes"]),
            subclasses=tuple(
                SubclassOption(
                    name=item["name"],
                    display_name=item["display_name"],
                    base_class=item["base_class"],
                    aliases=tuple(item.get("aliases", ())),
                )
                for item in data["subclasses"]
            ),
            sexes=tuple(data.get("sexes", ("male", "female", "neuter"))),
            source=str(data.get("source", "")),
            source_revision=data.get("source_revision"),
        )


def load_character_catalog(source: str | Path | None = None) -> CharacterCatalog:
    source_path = _source_const_path(source)
    if source_path is not None:
        comm_path = source_path.with_name("comm.c")
        if not comm_path.is_file():
            raise ValueError(f"DD4 creation source does not exist: {comm_path}")
        catalog = parse_character_catalog(
            source_path.read_text(encoding="utf-8", errors="replace"),
            source=str(source_path.resolve()),
            source_revision=_source_revision(source_path),
        )
        return CharacterCatalog(
            races=catalog.races,
            classes=catalog.classes,
            subclasses=catalog.subclasses,
            sexes=parse_creation_sexes(
                comm_path.read_text(encoding="utf-8", errors="replace")
            ),
            source=catalog.source,
            source_revision=catalog.source_revision,
        )

    snapshot = files("dd4tester").joinpath("data/dd4_character_options.json")
    return CharacterCatalog.from_mapping(json.loads(snapshot.read_text(encoding="utf-8")))


def parse_character_catalog(
    text: str,
    *,
    source: str = "DD4 const.c",
    source_revision: str | None = None,
) -> CharacterCatalog:
    class_rows = _initializer_rows(text, "class_table")
    race_rows = _initializer_rows(text, "race_table")
    subclass_rows = _initializer_rows(text, "sub_class_table")

    classes: list[ClassOption] = []
    subclass_bases: dict[str, str] = {}
    for row in class_rows:
        strings = _strings(row)
        if len(strings) < 4:
            continue
        class_name = normalize_option(strings[1])
        classes.append(ClassOption(class_name, strings[1].strip()))
        for subclass_display in strings[2:4]:
            subclass_bases[normalize_option(subclass_display)] = class_name

    races: list[RaceOption] = []
    for row in race_rows:
        strings = _strings(row)
        if len(strings) < 2 or normalize_option(strings[1]) == "none":
            continue
        index = len(races)
        if index >= 26:
            raise ValueError("DD4 has more races than single-letter creation choices")
        races.append(
            RaceOption(
                normalize_option(strings[1]),
                strings[1].strip(),
                chr(ord("a") + index),
            )
        )

    subclasses: list[SubclassOption] = []
    for row in subclass_rows:
        strings = _strings(row)
        if len(strings) < 2 or normalize_option(strings[1]) == "none":
            continue
        source_name = normalize_option(strings[1])
        base_class = subclass_bases.get(source_name)
        if base_class is None:
            raise ValueError(
                f"DD4 subclass {strings[1]!r} has no base class in class_table"
            )
        canonical, aliases = _canonical_subclass(source_name)
        subclasses.append(
            SubclassOption(
                canonical,
                strings[1].strip(),
                base_class,
                aliases=aliases,
            )
        )

    if not races or not classes or not subclasses:
        raise ValueError("DD4 character tables were missing or empty")
    return CharacterCatalog(
        races=tuple(races),
        classes=tuple(classes),
        subclasses=tuple(subclasses),
        source=source,
        source_revision=source_revision,
    )


def parse_creation_sexes(text: str) -> tuple[str, ...]:
    """Read legal creation sexes from DD4's CON_GET_NEW_SEX state handler."""
    block = _CREATION_SEX_BLOCK.search(text)
    if block is None:
        raise ValueError("DD4 source does not define CON_GET_NEW_SEX")
    sexes = tuple(
        _SEX_CONSTANT_NAMES[match.group("sex")]
        for match in _CREATION_SEX_ASSIGNMENT.finditer(block.group("body"))
    )
    if not sexes or len(set(sexes)) != len(sexes):
        raise ValueError("DD4 creation sex handler was missing or invalid")
    return sexes


def normalize_option(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", str(value).strip().casefold())
    return " ".join(normalized.split())


def _source_const_path(source: str | Path | None) -> Path | None:
    if source is not None:
        path = Path(source)
        if path.is_dir():
            path = path / "const.c"
        if not path.is_file():
            raise ValueError(f"DD4 const.c does not exist: {path}")
        return path
    if DEFAULT_DD4_CONST.is_file():
        return DEFAULT_DD4_CONST
    return None


def _source_revision(source_path: Path) -> str | None:
    repository = next(
        (parent for parent in source_path.resolve().parents if (parent / ".git").exists()),
        None,
    )
    if repository is None:
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(repository), "rev-parse", "HEAD"],
            capture_output=True,
            check=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    revision = result.stdout.strip()
    return revision or None


def _initializer_rows(text: str, table_name: str) -> tuple[str, ...]:
    declaration = re.search(rf"\b{re.escape(table_name)}\s*\[[^\]]+\]\s*=", text)
    if declaration is None:
        raise ValueError(f"DD4 source does not define {table_name}")
    start = text.find("{", declaration.end())
    if start < 0:
        raise ValueError(f"DD4 source has no initializer for {table_name}")

    rows: list[str] = []
    depth = 1
    row_start: int | None = None
    quote = False
    escaped = False
    for index in range(start + 1, len(text)):
        character = text[index]
        if quote:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quote = False
            continue
        if character == '"':
            quote = True
        elif character == "{":
            depth += 1
            if depth == 2:
                row_start = index
        elif character == "}":
            if depth == 2 and row_start is not None:
                rows.append(text[row_start : index + 1])
                row_start = None
            depth -= 1
            if depth == 0:
                return tuple(rows)
    raise ValueError(f"DD4 source has an unterminated {table_name} initializer")


def _strings(row: str) -> tuple[str, ...]:
    return tuple(
        bytes(match, "utf-8").decode("unicode_escape")
        for match in _QUOTED_STRING.findall(row)
    )


def _canonical_subclass(source_name: str) -> tuple[str, tuple[str, ...]]:
    expansions = {
        "b hunter": "bounty hunter",
        "m artist": "martial artist",
    }
    canonical = expansions.get(source_name, source_name)
    aliases = (source_name,) if canonical != source_name else ()
    return canonical, aliases


def _unknown_option(label: str, value: str, choices: Any) -> ValueError:
    available = ", ".join(sorted(choices))
    return ValueError(f"unknown {label} {value!r}; choose one of: {available}")
