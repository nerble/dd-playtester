from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


_DATA_PATH = Path(__file__).with_name("data") / "archetypes.json"
_LEVEL_GAIN_METRICS = {
    "intellectual_practices",
    "physical_practices",
    "hitpoints",
    "mana",
    "movement",
}


@dataclass(frozen=True)
class ClassProfile:
    name: str
    aliases: tuple[str, ...]
    primary_stat: str
    practice_skill: str
    level_gain_priorities: tuple[str, ...]
    progression_track: str
    capabilities: frozenset[str]


@dataclass(frozen=True)
class SubclassProfile:
    name: str
    base_class: str
    available: bool
    capabilities: frozenset[str]


@dataclass(frozen=True)
class ArchetypeRegistry:
    classes: dict[str, ClassProfile]
    class_aliases: dict[str, str]
    subclasses: dict[str, SubclassProfile]

    def class_profile(self, value: str) -> ClassProfile:
        normalized = _normalize(value)
        canonical = self.class_aliases.get(normalized)
        if canonical is None:
            available = ", ".join(sorted(self.classes))
            raise ValueError(
                f"unknown class {value!r}; choose one of: {available}"
            )
        return self.classes[canonical]

    def subclass_profile(self, value: str) -> SubclassProfile:
        normalized = _normalize(value)
        try:
            return self.subclasses[normalized]
        except KeyError as error:
            available = ", ".join(sorted(self.subclasses))
            raise ValueError(
                f"unknown subclass {value!r}; choose one of: {available}"
            ) from error


@lru_cache(maxsize=1)
def archetype_registry() -> ArchetypeRegistry:
    return load_archetype_registry(_DATA_PATH)


def load_archetype_registry(path: Path) -> ArchetypeRegistry:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must contain an object")
    raw_classes = _mapping(raw.get("classes"), "classes")
    raw_subclasses = _mapping(raw.get("subclasses"), "subclasses")

    classes: dict[str, ClassProfile] = {}
    aliases: dict[str, str] = {}
    for raw_name, value in raw_classes.items():
        name = _normalize(raw_name)
        data = _mapping(value, f"class {name}")
        class_aliases = tuple(
            dict.fromkeys(
                [name, *(_normalize(item) for item in _list(data, "aliases"))]
            )
        )
        priorities = tuple(
            _normalize(item) for item in _list(data, "level_gain_priorities")
        )
        if set(priorities) - _LEVEL_GAIN_METRICS:
            raise ValueError(f"class {name} has unknown level-gain priorities")
        profile = ClassProfile(
            name=name,
            aliases=class_aliases,
            primary_stat=_required_text(data, "primary_stat"),
            practice_skill=_required_text(data, "practice_skill"),
            level_gain_priorities=priorities,
            progression_track=_required_identifier(data, "progression_track"),
            capabilities=frozenset(
                _identifier(item) for item in _list(data, "capabilities")
            ),
        )
        classes[name] = profile
        for alias in class_aliases:
            previous = aliases.setdefault(alias, name)
            if previous != name:
                raise ValueError(f"class alias {alias!r} is ambiguous")

    subclasses: dict[str, SubclassProfile] = {}
    for raw_name, value in raw_subclasses.items():
        name = _normalize(raw_name)
        data = _mapping(value, f"subclass {name}")
        base_class = _normalize(_required_text(data, "base_class"))
        if base_class not in classes:
            raise ValueError(
                f"subclass {name} references unknown base class {base_class}"
            )
        subclasses[name] = SubclassProfile(
            name=name,
            base_class=base_class,
            available=bool(data.get("available", True)),
            capabilities=frozenset(
                _identifier(item) for item in _list(data, "capabilities")
            ),
        )
    return ArchetypeRegistry(classes, aliases, subclasses)


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _list(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return value


def _required_text(data: dict[str, Any], key: str) -> str:
    value = _normalize(data.get(key, ""))
    if not value:
        raise ValueError(f"{key} must not be empty")
    return value


def _required_identifier(data: dict[str, Any], key: str) -> str:
    value = _identifier(data.get(key, ""))
    if not value:
        raise ValueError(f"{key} must not be empty")
    return value


def _normalize(value: Any) -> str:
    return " ".join(str(value).strip().casefold().replace("-", " ").split())


def _identifier(value: Any) -> str:
    return " ".join(str(value).strip().casefold().split())
