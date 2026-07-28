from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .campaign import CampaignResult, run_campaign_file
from .character import (
    CLASSES,
    GENDERS,
    RACES,
    SUBCLASS_BASE_CLASSES,
    UNAVAILABLE_SUBCLASSES,
    CharacterSpec,
    load_character_spec,
)
from .dd4_catalog import CharacterCatalog, load_character_catalog


DEFAULT_HERO_WORKSPACE = Path("runs/heroes")
_MANIFEST_SCHEMA = 1
_NAME_SYLLABLES = (
    "al",
    "an",
    "ar",
    "bel",
    "cor",
    "dar",
    "el",
    "fen",
    "gal",
    "hal",
    "is",
    "jor",
    "kel",
    "lor",
    "mor",
    "nel",
    "or",
    "pra",
    "quil",
    "ran",
    "sel",
    "tor",
    "ul",
    "ver",
)


@dataclass(frozen=True)
class HeroRequest:
    race: str
    sex: str
    character_class: str
    subclass: str | None = None
    name: str | None = None
    personality: str | None = None


@dataclass(frozen=True)
class HeroPreparation:
    request: HeroRequest
    character: CharacterSpec
    directory: Path
    manifest_path: Path
    profile_path: Path
    campaign_path: Path
    resumed: bool


def prepare_hero_request(
    request: HeroRequest,
    *,
    catalog: CharacterCatalog | None = None,
    source: str | Path | None = None,
    workspace: Path = DEFAULT_HERO_WORKSPACE,
) -> HeroPreparation:
    catalog = catalog or load_character_catalog(source)
    validate_runtime_catalog(catalog)
    race = catalog.race_name(request.race)
    sex = catalog.sex_name(request.sex)
    character_class = catalog.class_name(request.character_class)
    subclass = None
    if request.subclass:
        subclass_option = catalog.subclass_option(request.subclass)
        if subclass_option.base_class != character_class:
            raise ValueError(
                f"subclass {subclass_option.name!r} requires base class "
                f"{subclass_option.base_class!r}"
            )
        subclass = subclass_option.name
        if subclass in UNAVAILABLE_SUBCLASSES:
            raise ValueError(
                f"subclass {subclass!r} is source-legal but has no autonomous "
                "HERO policy yet"
            )

    personality = _optional_identity_text(request.personality, "personality", 180)
    name = request.name.strip().title() if request.name else _generated_name(
        race, sex, character_class, subclass
    )
    canonical_request = HeroRequest(
        name=name,
        race=race,
        sex=sex,
        character_class=character_class,
        subclass=subclass,
        personality=personality,
    )

    directory_name = (
        name.casefold()
        if request.name
        else "-".join(
            part
            for part in (race, sex, character_class, subclass or "base")
            if part
        ).replace(" ", "-")
    )
    directory = (workspace / directory_name).resolve()
    manifest_path = directory / "hero.json"
    profile_path = directory / "character.yaml"
    campaign_path = directory / "campaign.yaml"
    request_mapping = _request_mapping(canonical_request)

    resumed = manifest_path.exists()
    if resumed:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("request") != request_mapping:
            raise ValueError(
                f"hero workspace {directory} belongs to a different request"
            )
        if not profile_path.is_file() or not campaign_path.is_file():
            raise ValueError(f"hero workspace is incomplete: {directory}")
        character = load_character_spec(profile_path)
        return HeroPreparation(
            canonical_request,
            character,
            directory,
            manifest_path,
            profile_path,
            campaign_path,
            resumed=True,
        )

    character_mapping = _profile_mapping(canonical_request)
    character = CharacterSpec.from_mapping(character_mapping)
    if personality:
        character_mapping["description"] = (
            f"{character.description} In company, {name} is {personality}."
        )
        character = CharacterSpec.from_mapping(character_mapping)

    directory.mkdir(parents=True, exist_ok=False)
    profile_path.write_text(_render_yaml(character_mapping), encoding="utf-8")
    campaign_path.write_text(
        _render_yaml(
            {
                "character_profile": "character.yaml",
                "name": f"{name} to HERO",
                "target_level": 100,
                "max_segments": 10000,
                "max_total_runtime": 604800,
                "max_total_commands": 1000000,
                "max_stalled_segments": 3,
            }
        ),
        encoding="utf-8",
    )
    manifest_path.write_text(
        json.dumps(
            {
                "schema": _MANIFEST_SCHEMA,
                "request": request_mapping,
                "catalog": {
                    "source": catalog.source,
                    "source_revision": catalog.source_revision,
                },
                "profile": profile_path.name,
                "campaign": campaign_path.name,
                "coverage_dimensions": ["race", "class", "subclass"],
                "cosmetic_dimensions": ["sex"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return HeroPreparation(
        canonical_request,
        character,
        directory,
        manifest_path,
        profile_path,
        campaign_path,
        resumed=False,
    )


def validate_runtime_catalog(catalog: CharacterCatalog) -> None:
    """Reject source options that the autonomous identity model cannot execute."""
    differences: list[str] = []
    for option in catalog.races:
        runtime_choice = RACES.get(option.name)
        if runtime_choice != option.creation_choice:
            differences.append(
                f"race {option.name!r} maps to {runtime_choice!r}, expected "
                f"{option.creation_choice!r}"
            )
    for sex in catalog.sexes:
        if sex not in GENDERS:
            differences.append(f"sex {sex!r} is not supported by the runtime model")
    for option in catalog.classes:
        if option.name not in CLASSES:
            differences.append(
                f"class {option.name!r} is not supported by the runtime model"
            )
    for option in catalog.subclasses:
        runtime_base = SUBCLASS_BASE_CLASSES.get(option.name)
        if runtime_base != option.base_class:
            differences.append(
                f"subclass {option.name!r} has runtime base {runtime_base!r}, "
                f"expected {option.base_class!r}"
            )
    if differences:
        detail = "; ".join(differences)
        raise ValueError(f"runtime character catalog drift: {detail}")


async def run_hero_request(
    request: HeroRequest,
    *,
    source: str | Path | None = None,
    workspace: Path = DEFAULT_HERO_WORKSPACE,
    force_new: bool = False,
    segments: int = 10000,
) -> tuple[HeroPreparation, CampaignResult]:
    preparation = prepare_hero_request(
        request,
        source=source,
        workspace=workspace,
    )
    result = await run_campaign_file(
        preparation.campaign_path,
        force_new=force_new,
        segments=segments,
    )
    return preparation, result


def _profile_mapping(request: HeroRequest) -> dict[str, Any]:
    assert request.name is not None
    mapping: dict[str, Any] = {
        "name": request.name,
        "password_env": f"DD4_{request.name.upper()}_PASSWORD",
        "credential_name": f"character:{request.name.casefold()}",
        "race": request.race,
        "gender": request.sex,
        "class": request.character_class,
        "colour": True,
        "max_attribute_rolls": 1,
        "minimum_primary_stat": 0,
        "max_runtime": 900,
        "max_commands": 500,
        "database": "runs/dd4tester.sqlite3",
        "transcript_dir": "transcripts",
    }
    if request.subclass:
        mapping["subclass"] = request.subclass
    return mapping


def _request_mapping(request: HeroRequest) -> dict[str, Any]:
    return {
        "name": request.name,
        "race": request.race,
        "sex": request.sex,
        "class": request.character_class,
        "subclass": request.subclass,
        "personality": request.personality,
    }


def _generated_name(
    race: str,
    sex: str,
    character_class: str,
    subclass: str | None,
) -> str:
    identity = "\0".join((race, sex, character_class, subclass or ""))
    digest = hashlib.sha256(identity.encode("utf-8")).digest()
    syllables = [
        _NAME_SYLLABLES[digest[index] % len(_NAME_SYLLABLES)] for index in range(4)
    ]
    name = "".join(syllables)
    if len(name) > 12:
        name = name[:12]
    return name.title()


def _optional_identity_text(
    value: str | None,
    label: str,
    maximum_length: int,
) -> str | None:
    if value is None:
        return None
    text = " ".join(value.strip().split())
    if not text:
        return None
    if len(text) > maximum_length:
        raise ValueError(f"{label} must not exceed {maximum_length} characters")
    if any(character in text for character in ("\r", "\n", "~")):
        raise ValueError(f"{label} must be a single line without tildes")
    return text


def _render_yaml(mapping: dict[str, Any]) -> str:
    return "".join(f"{key}: {_yaml_scalar(value)}\n" for key, value in mapping.items())


def _yaml_scalar(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=True)
