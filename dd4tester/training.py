from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


_DATA_PATH = Path(__file__).with_name("data") / "training_priorities.json"
_SUBCLASS_DATA_PATH = (
    Path(__file__).with_name("data") / "subclass_training_priorities.json"
)
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
    minimum_level: int | None
    utility: str
    reason: str
    automated: bool
    source_refs: tuple[str, ...]


@dataclass(frozen=True)
class ClassTrainingAnalysis:
    strategy: str
    practice_policy: str
    highest_value_skills: tuple[str, ...]
    automation_gaps: tuple[str, ...]
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
    raw = _training_data()
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
                minimum_level=(
                    int(item["minimum_level"])
                    if item.get("minimum_level") is not None
                    else None
                ),
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


@lru_cache(maxsize=1)
def class_training_analysis() -> dict[str, ClassTrainingAnalysis]:
    raw = _training_data()
    values = raw.get("class_analysis")
    if not isinstance(values, dict):
        raise ValueError("training priorities must contain a class_analysis object")
    result: dict[str, ClassTrainingAnalysis] = {}
    priorities = training_priorities()
    for class_name, item in values.items():
        normalized_class = _normalize(class_name)
        if not isinstance(item, dict):
            raise ValueError(f"training analysis for {class_name} must be an object")
        highest_value = tuple(
            _normalize(skill) for skill in item.get("highest_value_skills", ())
        )
        known = {priority.skill for priority in priorities.get(normalized_class, ())}
        if not highest_value or not set(highest_value) <= known:
            raise ValueError(
                f"training analysis for {class_name} references unknown priorities"
            )
        result[normalized_class] = ClassTrainingAnalysis(
            strategy=str(item["strategy"]),
            practice_policy=str(item["practice_policy"]),
            highest_value_skills=highest_value,
            automation_gaps=tuple(str(value) for value in item.get("automation_gaps", ())),
            source_refs=tuple(str(ref) for ref in item.get("source_refs", ())),
        )
    if result.keys() != priorities.keys():
        raise ValueError("class analysis must cover every training-priority class")
    return result


@lru_cache(maxsize=1)
def subclass_training_priorities() -> dict[str, tuple[TrainingPriority, ...]]:
    return _priorities_from_data(_subclass_training_data(), label="subclass")


@lru_cache(maxsize=1)
def subclass_training_analysis() -> dict[str, ClassTrainingAnalysis]:
    return _analyses_from_data(
        _subclass_training_data(),
        subclass_training_priorities(),
        label="subclass",
    )


def training_priorities_for(
    character_class: str,
    *,
    subclass: str | None = None,
) -> tuple[TrainingPriority, ...]:
    base = training_priorities().get(_normalize(character_class), ())
    if not subclass or _normalize(subclass) == "none":
        return base
    specialized = subclass_training_priorities().get(_normalize(subclass), ())
    return specialized + base


def training_analysis_for(name: str) -> ClassTrainingAnalysis | None:
    normalized = _normalize(name)
    return (
        class_training_analysis().get(normalized)
        or subclass_training_analysis().get(normalized)
    )


def prerequisite_class_for(name: str) -> str:
    return prerequisite_classes_for(name)[0]


def prerequisite_classes_for(name: str) -> tuple[str, ...]:
    normalized = _normalize(name)
    aliases = _subclass_training_data().get("prerequisite_class_aliases", {})
    source_class = normalized
    if isinstance(aliases, dict):
        source_class = _normalize(str(aliases.get(normalized, normalized)))
    base_classes = _subclass_training_data().get("base_classes", {})
    if isinstance(base_classes, dict) and normalized in base_classes:
        return source_class, _normalize(str(base_classes[normalized]))
    return (source_class,)


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
    subclass: str | None = None,
    character_level: int | None = None,
    excluded_practice_types: set[str] | frozenset[str] = frozenset(),
    excluded_skills: set[str] | frozenset[str] = frozenset(),
) -> tuple[TrainingChoice, ...]:
    listing = parse_practice_listing(text)
    budgets = {
        "physical": listing.physical_practices or 0,
        "intellectual": listing.intellectual_practices or 0,
    }
    skills = listing.trainable
    choices: list[TrainingChoice] = []
    priorities = training_priorities_for(character_class, subclass=subclass)
    spent_types = set(excluded_practice_types)
    blocked_skills = {_normalize(skill) for skill in excluded_skills}

    for selected in priorities:
        if (
            not selected.automated
            or selected.skill in blocked_skills
            or selected.practice_type in spent_types
            or budgets[selected.practice_type] <= 0
            or selected.skill not in skills
            or skills[selected.skill] >= selected.target_percent
            or (
                character_level is not None
                and selected.minimum_level is not None
                and character_level < selected.minimum_level
            )
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


@lru_cache(maxsize=1)
def _training_data() -> dict[str, object]:
    raw = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("training priorities must contain a JSON object")
    return raw


@lru_cache(maxsize=1)
def _subclass_training_data() -> dict[str, object]:
    raw = json.loads(_SUBCLASS_DATA_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("subclass training priorities must contain a JSON object")
    return raw


def _priorities_from_data(
    raw: dict[str, object],
    *,
    label: str,
) -> dict[str, tuple[TrainingPriority, ...]]:
    classes = raw.get("classes")
    if not isinstance(classes, dict):
        raise ValueError(f"{label} training priorities must contain a classes object")
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
                minimum_level=(
                    int(item["minimum_level"])
                    if item.get("minimum_level") is not None
                    else None
                ),
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


def _analyses_from_data(
    raw: dict[str, object],
    priorities: dict[str, tuple[TrainingPriority, ...]],
    *,
    label: str,
) -> dict[str, ClassTrainingAnalysis]:
    values = raw.get("class_analysis")
    if not isinstance(values, dict):
        raise ValueError(f"{label} training priorities need a class_analysis object")
    result: dict[str, ClassTrainingAnalysis] = {}
    for class_name, item in values.items():
        normalized_class = _normalize(class_name)
        if not isinstance(item, dict):
            raise ValueError(f"training analysis for {class_name} must be an object")
        highest_value = tuple(
            _normalize(skill) for skill in item.get("highest_value_skills", ())
        )
        known = {priority.skill for priority in priorities.get(normalized_class, ())}
        if not highest_value or not set(highest_value) <= known:
            raise ValueError(
                f"training analysis for {class_name} references unknown priorities"
            )
        result[normalized_class] = ClassTrainingAnalysis(
            strategy=str(item["strategy"]),
            practice_policy=str(item["practice_policy"]),
            highest_value_skills=highest_value,
            automation_gaps=tuple(str(value) for value in item.get("automation_gaps", ())),
            source_refs=tuple(str(ref) for ref in item.get("source_refs", ())),
        )
    if result.keys() != priorities.keys():
        raise ValueError(f"{label} analysis must cover every training-priority class")
    return result
