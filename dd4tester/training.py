from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


_DATA_PATH = Path(__file__).with_name("data") / "training_priorities.json"
_ANSI_ESCAPE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
_SKILL = re.compile(r"([A-Za-z][A-Za-z '-]{1,34}?):\s*(\d+)%")
_BALANCE = re.compile(
    r"You have\s+(?P<physical>\d+).*?physical.*?"
    r"and\s+(?P<intellectual>\d+).*?intellectual practices remaining",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class TrainingPriority:
    skill: str
    source_skill: str
    practice_type: str
    target_percent: int
    utility: str
    reason: str
    automated: bool
    source_refs: tuple[str, ...]


@dataclass(frozen=True)
class PracticeListing:
    known: dict[str, int]
    learnable: dict[str, int]
    physical_practices: int | None
    intellectual_practices: int | None

    @property
    def trainable(self) -> dict[str, int]:
        return {**self.learnable, **self.known}


@dataclass(frozen=True)
class TrainingChoice:
    skill: str
    practice_type: str
    utility: str
    current_percent: int
    target_percent: int
    reason: str
    source_refs: tuple[str, ...]

    @property
    def explanation(self) -> str:
        return (
            f"train {self.skill} for {self.utility}: {self.reason} "
            f"({self.current_percent}% toward {self.target_percent}%)"
        )


@lru_cache(maxsize=1)
def training_priorities() -> dict[str, tuple[TrainingPriority, ...]]:
    raw = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    classes = raw.get("classes")
    if not isinstance(classes, dict):
        raise ValueError("training priorities must contain a classes object")
    result: dict[str, tuple[TrainingPriority, ...]] = {}
    for class_name, values in classes.items():
        if not isinstance(values, list) or not values:
            raise ValueError(f"training priorities for {class_name} must be a list")
        priorities = tuple(
            TrainingPriority(
                skill=_normalize(item["skill"]),
                source_skill=_normalize(item.get("source_skill", item["skill"])),
                practice_type=str(item["type"]),
                target_percent=int(item["target"]),
                utility=str(item["utility"]),
                reason=str(item["reason"]),
                automated=bool(item.get("automated", True)),
                source_refs=tuple(str(ref) for ref in item.get("source_refs", ())),
            )
            for item in values
        )
        if any(item.practice_type not in {"physical", "intellectual"} for item in priorities):
            raise ValueError(f"training priorities for {class_name} use an invalid type")
        result[_normalize(class_name)] = priorities
    return result


def parse_practice_listing(text: str) -> PracticeListing:
    cleaned = _ANSI_ESCAPE.sub("", text).replace("\r", "")
    marker = "skills known:"
    marker_index = cleaned.casefold().rfind(marker)
    if marker_index == -1:
        return PracticeListing({}, {}, None, None)
    block = cleaned[marker_index + len(marker) :]
    balance = _BALANCE.search(block)
    if balance is not None:
        skill_text = block[: balance.start()]
        physical = int(balance.group("physical"))
        intellectual = int(balance.group("intellectual"))
    else:
        skill_text = block
        physical = intellectual = None
    learnable_marker = "skills which may be learned:"
    split = skill_text.casefold().find(learnable_marker)
    if split == -1:
        known_text, learnable_text = skill_text, ""
    else:
        known_text = skill_text[:split]
        learnable_text = skill_text[split + len(learnable_marker) :]
    return PracticeListing(
        known=_parse_skills(known_text),
        learnable=_parse_skills(learnable_text),
        physical_practices=physical,
        intellectual_practices=intellectual,
    )


def plan_training(
    character_class: str,
    text: str,
    *,
    excluded_practice_types: set[str] | frozenset[str] = frozenset(),
) -> tuple[TrainingChoice, ...]:
    listing = parse_practice_listing(text)
    budgets = {
        "physical": listing.physical_practices or 0,
        "intellectual": listing.intellectual_practices or 0,
    }
    skills = listing.trainable
    choices: list[TrainingChoice] = []
    priorities = training_priorities().get(_normalize(character_class), ())
    spent_types = set(excluded_practice_types)

    for selected in priorities:
        if (
            not selected.automated
            or selected.practice_type in spent_types
            or budgets[selected.practice_type] <= 0
            or selected.skill not in skills
            or skills[selected.skill] >= selected.target_percent
        ):
            continue
        current = skills[selected.skill]
        choices.append(
            TrainingChoice(
                skill=selected.skill,
                practice_type=selected.practice_type,
                utility=selected.utility,
                current_percent=current,
                target_percent=selected.target_percent,
                reason=selected.reason,
                source_refs=selected.source_refs,
            )
        )
        spent_types.add(selected.practice_type)
    return tuple(choices)


def _parse_skills(text: str) -> dict[str, int]:
    return {
        _normalize(match.group(1)): int(match.group(2))
        for match in _SKILL.finditer(text)
    }


def _normalize(value: str) -> str:
    return " ".join(value.casefold().replace("_", " ").split())
