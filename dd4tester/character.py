from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .scenario import load_yaml_mapping


RACES = {
    "human": "a",
    "elf": "b",
    "wild elf": "c",
    "orc": "d",
    "giant": "e",
    "satyr": "f",
    "ogre": "g",
    "goblin": "h",
    "half dragon": "i",
    "halfling": "j",
    "dwarf": "k",
    "centaur": "l",
    "drow": "m",
    "troll": "n",
    "alaghi": "o",
    "hobgoblin": "p",
    "yuan ti": "q",
    "fae": "r",
    "sahuagin": "s",
    "tiefling": "t",
    "jotun": "u",
    "genasi": "v",
    "illithid": "w",
    "grung": "x",
    "duergar": "y",
}

CLASSES = {
    "mage": "mage",
    "cleric": "cleric",
    "thief": "thief",
    "warrior": "warrior",
    "psionic": "psionic",
    "psionicist": "psionic",
    "shifter": "shifter",
    "shape shifter": "shifter",
    "brawler": "brawler",
    "ranger": "ranger",
    "smithy": "smithy",
}

SUBCLASS_BASE_CLASSES = {
    "necromancer": "mage",
    "warlock": "mage",
    "templar": "cleric",
    "druid": "cleric",
    "ninja": "thief",
    "bounty hunter": "thief",
    "knight": "warrior",
    "thug": "warrior",
    "infernalist": "psionic",
    "witch": "psionic",
    "monk": "brawler",
    "martial artist": "brawler",
    "werewolf": "shifter",
    "vampire": "shifter",
    "barbarian": "ranger",
    "bard": "ranger",
    "engineer": "smithy",
    "runesmith": "smithy",
}

UNAVAILABLE_SUBCLASSES = {"engineer", "runesmith"}

GENDERS = {
    "male": "m",
    "female": "f",
    "neuter": "n",
}

PRIMARY_STATS = {
    "mage": "int",
    "cleric": "wis",
    "thief": "dex",
    "warrior": "str",
    "psionic": "int",
    "shifter": "con",
    "brawler": "str",
    "ranger": "dex",
    "smithy": "str",
}

LEVEL_GAIN_METRICS = {
    "intellectual_practices",
    "physical_practices",
    "hitpoints",
    "mana",
    "movement",
}

CLASS_LEVEL_GAIN_PRIORITIES = {
    "mage": (
        "intellectual_practices",
        "mana",
        "hitpoints",
        "movement",
        "physical_practices",
    ),
    "cleric": (
        "intellectual_practices",
        "mana",
        "hitpoints",
        "movement",
        "physical_practices",
    ),
    "psionic": (
        "intellectual_practices",
        "mana",
        "hitpoints",
        "movement",
        "physical_practices",
    ),
}
_PHYSICAL_LEVEL_GAIN_PRIORITIES = (
    "physical_practices",
    "hitpoints",
    "movement",
    "intellectual_practices",
    "mana",
)


@dataclass(frozen=True)
class CharacterSpec:
    name: str
    password_env: str
    race: str
    gender: str
    character_class: str
    credential_name: str = ""
    subclass: str | None = None
    colour: bool = True
    max_attribute_rolls: int = 1
    minimum_primary_stat: int = 0
    level_gain_priorities: tuple[str, ...] = ()
    host: str = "dragons-domain.org"
    port: int = 8888
    timeout: float = 10.0
    max_runtime: float = 900.0
    max_commands: int = 250
    database: Path = Path("runs/dd4tester.sqlite3")
    transcript_dir: Path = Path("transcripts")

    @property
    def race_choice(self) -> str:
        return RACES[self.race]

    @property
    def gender_choice(self) -> str:
        return GENDERS[self.gender]

    @property
    def primary_stat(self) -> str:
        return PRIMARY_STATS[self.character_class]

    @property
    def effective_level_gain_priorities(self) -> tuple[str, ...]:
        if self.level_gain_priorities:
            return self.level_gain_priorities
        return CLASS_LEVEL_GAIN_PRIORITIES.get(
            self.character_class,
            _PHYSICAL_LEVEL_GAIN_PRIORITIES,
        )

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "CharacterSpec":
        name = str(data.get("name", "")).strip()
        if not re.fullmatch(r"[A-Za-z]{3,12}", name):
            raise ValueError("name must contain 3-12 letters")

        password_env = str(data.get("password_env", "DD4_CHARACTER_PASSWORD")).strip()
        if not password_env:
            raise ValueError("password_env must not be empty")
        credential_name = str(
            data.get("credential_name", f"character:{name.casefold()}")
        ).strip()
        if not credential_name:
            raise ValueError("credential_name must not be empty")

        race = _choice(data.get("race"), RACES, "race")
        gender = _choice(data.get("gender"), GENDERS, "gender")
        subclass = _optional_choice(
            data.get("subclass"),
            SUBCLASS_BASE_CLASSES,
            "subclass",
        )
        if subclass in UNAVAILABLE_SUBCLASSES:
            raise ValueError(f"DD4 reports subclass {subclass!r} as not implemented")

        requested_class = data.get("class", data.get("character_class"))
        if requested_class is None and subclass is None:
            raise ValueError("class or subclass must be provided")
        character_class = (
            _choice(requested_class, CLASSES, "class")
            if requested_class is not None
            else SUBCLASS_BASE_CLASSES[subclass]
        )
        if subclass is not None:
            required_class = SUBCLASS_BASE_CLASSES[subclass]
            if character_class != required_class:
                raise ValueError(
                    f"subclass {subclass!r} requires base class {required_class!r}"
                )

        max_attribute_rolls = int(data.get("max_attribute_rolls", 1))
        if max_attribute_rolls < 1 or max_attribute_rolls > 20:
            raise ValueError("max_attribute_rolls must be between 1 and 20")
        minimum_primary_stat = int(data.get("minimum_primary_stat", 0))
        if minimum_primary_stat < 0 or minimum_primary_stat > 25:
            raise ValueError("minimum_primary_stat must be between 0 and 25")
        raw_priorities = data.get("level_gain_priorities", ())
        if not isinstance(raw_priorities, (list, tuple)):
            raise ValueError("level_gain_priorities must be a YAML list")
        level_gain_priorities = tuple(
            str(priority).strip().casefold() for priority in raw_priorities
        )
        if len(level_gain_priorities) != len(set(level_gain_priorities)):
            raise ValueError("level_gain_priorities must not contain duplicates")
        unknown_priorities = set(level_gain_priorities) - LEVEL_GAIN_METRICS
        if unknown_priorities:
            available = ", ".join(sorted(LEVEL_GAIN_METRICS))
            unknown = ", ".join(sorted(unknown_priorities))
            raise ValueError(
                f"unknown level_gain_priorities {unknown}; choose from: {available}"
            )

        max_runtime = float(data.get("max_runtime", 900))
        max_commands = int(data.get("max_commands", 250))
        if max_runtime <= 0:
            raise ValueError("max_runtime must be positive")
        if max_commands < 1:
            raise ValueError("max_commands must be positive")

        return cls(
            name=name,
            password_env=password_env,
            credential_name=credential_name,
            race=race,
            gender=gender,
            character_class=character_class,
            subclass=subclass,
            colour=bool(data.get("colour", True)),
            max_attribute_rolls=max_attribute_rolls,
            minimum_primary_stat=minimum_primary_stat,
            level_gain_priorities=level_gain_priorities,
            host=str(data.get("host", "dragons-domain.org")),
            port=int(data.get("port", 8888)),
            timeout=float(data.get("timeout", 10)),
            max_runtime=max_runtime,
            max_commands=max_commands,
            database=Path(str(data.get("database", "runs/dd4tester.sqlite3"))),
            transcript_dir=Path(str(data.get("transcript_dir", "transcripts"))),
        )


def load_character_spec(path: str | Path) -> CharacterSpec:
    return CharacterSpec.from_mapping(load_yaml_mapping(Path(path)))


def _choice(value: Any, choices: dict[str, Any], label: str) -> str:
    normalized = _normalize(value)
    if normalized not in choices:
        available = ", ".join(sorted(choices))
        raise ValueError(f"unknown {label} {value!r}; choose one of: {available}")
    return normalized


def _optional_choice(
    value: Any,
    choices: dict[str, Any],
    label: str,
) -> str | None:
    if value is None or not str(value).strip():
        return None
    return _choice(value, choices, label)


def _normalize(value: Any) -> str:
    return " ".join(str(value).strip().casefold().replace("-", " ").split())
