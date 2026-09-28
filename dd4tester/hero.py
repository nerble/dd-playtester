from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import secrets
import sqlite3
import string
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Callable, Iterator

from .campaign import (
    DEFAULT_LIVE_SEGMENT_RUNTIME_SECONDS,
    DEFAULT_RESET_WAIT_SECONDS,
    CampaignResult,
    load_campaign_spec,
    run_campaign_file,
)
from .character import (
    CLASSES,
    GENDERS,
    RACES,
    SUBCLASS_BASE_CLASSES,
    CharacterSpec,
    load_character_spec,
)
from .dd4_catalog import (
    CharacterCatalog,
    load_character_catalog,
    source_area_directory,
)
from .credentials import (
    CredentialStoreError,
    load_character_password,
    save_character_password,
)
from .mudlet import MudletBridge
from .scenario import load_yaml_mapping


DEFAULT_HERO_WORKSPACE = Path("runs/heroes")
DEFAULT_AUTONOMOUS_RESET_WAITS = 3
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
_GENERATED_PASSWORD_ALPHABET = string.ascii_letters + string.digits
_GENERATED_PASSWORD_LENGTH = 24
_CREDENTIAL_READ_TIMEOUT_SECONDS = 5.0
_CREDENTIAL_WRITE_TIMEOUT_SECONDS = 5.0
_CAMPAIGN_PROBE_TIMEOUT_SECONDS = 1.0


@dataclass(frozen=True)
class HeroRequest:
    race: str
    sex: str
    character_class: str
    subclass: str | None = None
    name: str | None = None
    personality: str | None = None
    transport: str = "telnet"
    mudlet_directory: Path | None = None
    legacy_profile_path: Path | None = field(default=None, compare=False, repr=False)
    legacy_campaign_path: Path | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True)
class HeroPreparation:
    request: HeroRequest
    character: CharacterSpec
    directory: Path
    manifest_path: Path | None
    profile_path: Path
    campaign_path: Path
    resumed: bool


def prepare_hero_request(
    request: HeroRequest,
    *,
    catalog: CharacterCatalog | None = None,
    source: str | Path | None = None,
    workspace: Path = DEFAULT_HERO_WORKSPACE,
    target_level: int = 100,
) -> HeroPreparation:
    _validate_target_level(target_level)
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
    personality = _optional_identity_text(request.personality, "personality", 180)
    transport = request.transport.strip().casefold()
    if transport not in {"telnet", "mudlet"}:
        raise ValueError("transport must be 'telnet' or 'mudlet'")
    if transport == "mudlet" and request.mudlet_directory is None:
        raise ValueError("mudlet_directory is required for Mudlet transport")
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
        transport=transport,
        mudlet_directory=request.mudlet_directory,
        legacy_profile_path=request.legacy_profile_path,
        legacy_campaign_path=request.legacy_campaign_path,
    )

    if canonical_request.legacy_profile_path or canonical_request.legacy_campaign_path:
        return _prepare_legacy_campaign_request(canonical_request)

    directory_name = (
        name.casefold()
        if request.name
        else "-".join(
            part
            for part in (race, sex, character_class, subclass or "base")
            if part
        ).replace(" ", "-")
    )
    existing_manifest = (
        _find_existing_hero_manifest(
            workspace,
            name,
            target_level=target_level,
        )
        if request.name
        else None
    )
    directory = (
        existing_manifest.parent
        if existing_manifest is not None
        else (workspace / directory_name).resolve()
    )
    manifest_path = (
        existing_manifest
        if existing_manifest is not None
        else directory / "hero.json"
    )
    profile_path = directory / "character.yaml"
    campaign_path = directory / "campaign.yaml"
    request_mapping = _request_mapping(canonical_request)

    resumed = manifest_path.exists()
    if resumed:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        stored_request = manifest.get("request")
        if not _resume_request_matches(stored_request, request_mapping):
            raise ValueError(
                f"hero workspace {directory} belongs to a different request"
            )
        resumed_request = replace(
            canonical_request,
            subclass=(
                canonical_request.subclass
                if canonical_request.subclass is not None
                else stored_request.get("subclass")
            ),
            personality=(
                canonical_request.personality
                if canonical_request.personality is not None
                else stored_request.get("personality")
            ),
        )
        if not profile_path.is_file() or not campaign_path.is_file():
            raise ValueError(f"hero workspace is incomplete: {directory}")
        _update_campaign_target(campaign_path, target_level)
        character = load_character_spec(profile_path)
        if character.personality is None and resumed_request.personality is not None:
            # Older profiles kept the personality only in the manifest and
            # appended it to the generated description.
            character = replace(
                character,
                personality=resumed_request.personality,
            )
        _initialize_mudlet_bridge(resumed_request)
        return HeroPreparation(
            resumed_request,
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

    # Freeze generated identity text into the profile so future loader changes
    # cannot silently rewrite a character's established persona.
    character_mapping["title"] = character.title
    character_mapping["description"] = character.description

    directory.mkdir(parents=True, exist_ok=False)
    profile_path.write_text(_render_yaml(character_mapping), encoding="utf-8")
    campaign_path.write_text(
        _render_yaml(
            {
                "character_profile": "character.yaml",
                "source_directory": str(source_area_directory(source).resolve()),
                "name": (
                    f"{name} to HERO"
                    if target_level == 100
                    else f"{name} to level {target_level}"
                ),
                "target_level": target_level,
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
                    "source_directory": str(source_area_directory(source).resolve()),
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
    _initialize_mudlet_bridge(canonical_request)
    return HeroPreparation(
        canonical_request,
        character,
        directory,
        manifest_path,
        profile_path,
        campaign_path,
        resumed=False,
    )


def _prepare_legacy_campaign_request(
    request: HeroRequest,
) -> HeroPreparation:
    profile_path = request.legacy_profile_path
    campaign_path = request.legacy_campaign_path
    if profile_path is None or campaign_path is None:
        raise ValueError("legacy campaign resume requires both saved profile paths")
    if not profile_path.is_file() or not campaign_path.is_file():
        raise ValueError("the saved campaign profile or configuration is missing")

    campaign = load_campaign_spec(campaign_path)
    profile_path = profile_path.resolve()
    if campaign.character_profile.resolve() != profile_path:
        raise ValueError("saved campaign no longer points to its recorded profile")
    character = campaign.character
    expected_identity = (
        request.name,
        request.race,
        request.sex,
        request.character_class,
        request.subclass or "",
    )
    stored_identity = (
        character.name,
        character.race,
        character.gender,
        character.character_class,
        character.subclass or "",
    )
    if tuple(value.casefold() for value in expected_identity) != tuple(
        value.casefold() for value in stored_identity
    ):
        raise ValueError("saved campaign identity does not match the requested character")
    if request.transport != character.transport:
        raise ValueError("saved campaign transport differs from the requested transport")
    if request.personality and character.personality is None:
        character = replace(character, personality=request.personality)
    _initialize_mudlet_bridge(request)
    return HeroPreparation(
        request,
        character,
        profile_path.parent,
        None,
        profile_path,
        campaign_path,
        resumed=True,
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


def load_existing_hero_request(
    name: str,
    *,
    workspace: Path = DEFAULT_HERO_WORKSPACE,
    target_level: int = 100,
    database: Path = Path("runs/dd4tester.sqlite3"),
) -> HeroRequest:
    """Load identity from a HERO workspace or a saved legacy campaign."""
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("an existing hero name is required")
    manifest_path = _find_existing_hero_manifest(
        workspace,
        clean_name,
        target_level=target_level,
    )
    if manifest_path is None:
        legacy_request = _find_legacy_campaign_request(clean_name, database)
        if legacy_request is not None:
            return legacy_request
        raise ValueError(
            f"no saved character campaign exists for {clean_name!r}; provide "
            "--race and --class to create or resume it"
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not read hero manifest {manifest_path}") from exc
    stored = manifest.get("request")
    if not isinstance(stored, dict):
        raise ValueError(f"hero manifest has no valid request: {manifest_path}")
    required = ("name", "race", "sex", "class")
    if any(not str(stored.get(key, "")).strip() for key in required):
        raise ValueError(f"hero manifest request is incomplete: {manifest_path}")
    mudlet_directory = stored.get("mudlet_directory")
    return HeroRequest(
        name=str(stored["name"]),
        race=str(stored["race"]),
        sex=str(stored["sex"]),
        character_class=str(stored["class"]),
        subclass=(
            str(stored["subclass"])
            if stored.get("subclass") is not None
            else None
        ),
        personality=(
            str(stored["personality"])
            if stored.get("personality") is not None
            else None
        ),
        transport=str(stored.get("transport", "telnet")),
        mudlet_directory=Path(str(mudlet_directory))
        if mudlet_directory
        else None,
    )


def _find_legacy_campaign_request(
    name: str,
    database: Path,
) -> HeroRequest | None:
    database_path = database
    if not database_path.is_absolute():
        database_path = (Path.cwd() / database_path).resolve()
    if not database_path.is_file():
        return None
    try:
        with sqlite3.connect(
            database_path.as_uri() + "?mode=ro",
            uri=True,
            timeout=_CAMPAIGN_PROBE_TIMEOUT_SECONDS,
        ) as connection:
            connection.execute(
                f"PRAGMA busy_timeout = "
                f"{int(_CAMPAIGN_PROBE_TIMEOUT_SECONDS * 1000)}"
            )
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                SELECT campaign.config_path, campaign.character_profile_path,
                       checkpoint.state_json
                FROM campaigns AS campaign
                JOIN campaign_checkpoints AS checkpoint
                  ON checkpoint.id = (
                      SELECT MAX(latest.id)
                      FROM campaign_checkpoints AS latest
                      WHERE latest.campaign_id = campaign.id
                  )
                WHERE lower(json_extract(checkpoint.state_json, '$.name')) = ?
                ORDER BY checkpoint.id DESC
                LIMIT 1
                """,
                (name.casefold(),),
            ).fetchone()
    except sqlite3.OperationalError as exc:
        if "no such table" in str(exc).casefold():
            return None
        raise ValueError("could not inspect saved character campaigns") from exc
    except sqlite3.Error as exc:
        raise ValueError("could not inspect saved character campaigns") from exc
    if row is None:
        return None

    profile_path = Path(str(row["character_profile_path"]))
    campaign_path = Path(str(row["config_path"]))
    if not profile_path.is_file() or not campaign_path.is_file():
        raise ValueError("the latest saved campaign profile or configuration is missing")
    try:
        campaign = load_campaign_spec(campaign_path)
        state = json.loads(row["state_json"])
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("the latest saved character campaign is unreadable") from exc
    if not isinstance(state, dict):
        raise ValueError("the latest saved character campaign has invalid state")
    character = campaign.character
    if (
        campaign.character_profile.resolve() != profile_path.resolve()
        or character.name.casefold() != name.casefold()
        or str(state.get("name", "")).casefold() != name.casefold()
    ):
        raise ValueError("the latest saved campaign does not match that character")
    return HeroRequest(
        name=character.name,
        race=character.race,
        sex=character.gender,
        character_class=character.character_class,
        subclass=character.subclass,
        personality=character.personality,
        transport=character.transport,
        mudlet_directory=character.mudlet_directory,
        legacy_profile_path=profile_path,
        legacy_campaign_path=campaign_path,
    )


def _find_existing_hero_manifest(
    workspace: Path,
    name: str,
    *,
    target_level: int = 100,
) -> Path | None:
    """Find the canonical stored manifest by identity, including matrix workspaces.

    A named character can legitimately have both a short validation campaign
    and a longer HERO campaign under the same workspace root. Choose the
    closest stored horizon that can satisfy the requested target; when all
    stored horizons are lower, use the longest one. When duplicate copies have
    the same horizon, use saved level and XP to identify the more advanced
    campaign; preserve ambiguity if durable progress cannot decide safely.
    """
    clean_name = name.strip().casefold()
    if not clean_name:
        return None
    root = workspace.resolve()
    if not root.is_dir():
        return None
    matches: list[tuple[Path, int, tuple[str, str, str, str]]] = []
    for manifest_path in root.rglob("hero.json"):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        request = manifest.get("request")
        if not isinstance(request, dict):
            continue
        stored_name = str(request.get("name") or "").strip().casefold()
        if stored_name == clean_name:
            matches.append(
                (
                    manifest_path.resolve(),
                    _stored_campaign_target_level(manifest_path),
                    tuple(
                        str(request.get(key) or "").strip().casefold()
                        for key in ("race", "sex", "class", "subclass")
                    ),
                )
            )

    identities = {identity for _path, _target, identity in matches}
    if len(identities) > 1:
        locations = ", ".join(
            str(path)
            for path, _target, _identity in sorted(
                matches,
                key=lambda item: str(item[0]),
            )
        )
        raise ValueError(
            f"stored hero workspaces for {name!r} disagree on race, sex, "
            f"class, or subclass: {locations}"
        )

    def workspace_depth(path: Path) -> int:
        try:
            return len(path.relative_to(root).parts)
        except ValueError:
            return len(path.parts)

    shallowest_depth = min(
        (workspace_depth(path) for path, _target, _identity in matches),
        default=0,
    )
    canonical_matches = [
        path
        for path, _target, _identity in matches
        if workspace_depth(path) == shallowest_depth
    ]
    if len(canonical_matches) == 1:
        # Validation matrices live below the normal hero directory. Prefer the
        # one root-level workspace so routine named resumes do not collide with
        # their test copies.
        return canonical_matches[0]
    if len(matches) > 1:
        requested_target = max(int(target_level), 0)
        eligible_targets = [
            target
            for _path, target, _identity in matches
            if target >= requested_target
        ]
        selected_target = (
            min(eligible_targets)
            if eligible_targets
            else max(target for _path, target, _identity in matches)
        )
        selected = [
            path
            for path, target, _identity in matches
            if target == selected_target
        ]
        if len(selected) == 1:
            return selected[0]
        progress = [
            (path, _stored_campaign_progress(path)) for path in selected
        ]
        progressed = [
            (path, score) for path, score in progress if score is not None
        ]
        untracked = [
            path for path, score in progress if score is None
        ]
        if len(progressed) == 1 and all(
            _stored_campaign_record_exists(path) is False
            for path in untracked
        ):
            return progressed[0][0]
        if all(score is not None for _path, score in progress):
            best_score = max(score for _path, score in progress if score is not None)
            best = [path for path, score in progress if score == best_score]
            if len(best) == 1:
                return best[0]
        locations = ", ".join(str(path) for path in sorted(selected))
        raise ValueError(
            f"multiple stored hero workspaces with the same campaign horizon "
            f"exist for {name!r} (target level {selected_target}) and saved "
            f"progress cannot distinguish them: {locations}"
        )
    return matches[0][0] if matches else None


def _stored_campaign_target_level(manifest_path: Path) -> int:
    """Read a stored campaign horizon for deterministic named resume."""
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        campaign_name = str(manifest.get("campaign") or "campaign.yaml")
        campaign_path = manifest_path.parent / campaign_name
        mapping = load_yaml_mapping(campaign_path)
        return int(mapping.get("target_level", 0) or 0)
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return 0


def _stored_campaign_progress(manifest_path: Path) -> tuple[int, int] | None:
    """Read saved level and XP to resolve duplicate copies of one character."""
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        profile_path = manifest_path.parent / str(
            manifest.get("profile") or "character.yaml"
        )
        profile = load_yaml_mapping(profile_path)
        database_value = profile.get("database")
        if not database_value:
            return None
        database_path = Path(str(database_value))
        if not database_path.is_absolute():
            database_path = (Path.cwd() / database_path).resolve()
        if not database_path.is_file():
            return None
        campaign_name = str(manifest.get("campaign") or "campaign.yaml")
        campaign_path = manifest_path.parent / campaign_name
        config_paths = (str(campaign_path.resolve()), str(campaign_path))
        with sqlite3.connect(
            database_path.as_uri() + "?mode=ro",
            uri=True,
            timeout=_CAMPAIGN_PROBE_TIMEOUT_SECONDS,
        ) as connection:
            connection.execute(
                f"PRAGMA busy_timeout = "
                f"{int(_CAMPAIGN_PROBE_TIMEOUT_SECONDS * 1000)}"
            )
            campaign_ids = connection.execute(
                "SELECT id FROM campaigns WHERE config_path IN (?, ?)",
                config_paths,
            ).fetchall()
            scores: list[tuple[int, int]] = []
            for (campaign_id,) in campaign_ids:
                row = connection.execute(
                    """
                    SELECT state_json FROM campaign_checkpoints
                    WHERE campaign_id = ? ORDER BY id DESC LIMIT 1
                    """,
                    (campaign_id,),
                ).fetchone()
                if row is None:
                    continue
                state = json.loads(row[0])
                level = int(state.get("level", 0) or 0)
                xp = int(state.get("xp", 0) or 0)
                scores.append((level, xp))
            return max(scores) if scores else None
    except (
        OSError,
        sqlite3.Error,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ):
        return None


def _stored_campaign_record_exists(manifest_path: Path) -> bool | None:
    """Distinguish a workspace without a campaign from unreadable history."""
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        profile_path = manifest_path.parent / str(
            manifest.get("profile") or "character.yaml"
        )
        profile = load_yaml_mapping(profile_path)
        database_value = profile.get("database")
        if not database_value:
            return None
        database_path = Path(str(database_value))
        if not database_path.is_absolute():
            database_path = (Path.cwd() / database_path).resolve()
        if not database_path.is_file():
            return None
        campaign_name = str(manifest.get("campaign") or "campaign.yaml")
        campaign_path = manifest_path.parent / campaign_name
        config_paths = (str(campaign_path.resolve()), str(campaign_path))
        with sqlite3.connect(
            database_path.as_uri() + "?mode=ro",
            uri=True,
            timeout=_CAMPAIGN_PROBE_TIMEOUT_SECONDS,
        ) as connection:
            connection.execute(
                f"PRAGMA busy_timeout = "
                f"{int(_CAMPAIGN_PROBE_TIMEOUT_SECONDS * 1000)}"
            )
            row = connection.execute(
                "SELECT 1 FROM campaigns WHERE config_path IN (?, ?) LIMIT 1",
                config_paths,
            ).fetchone()
            return row is not None
    except (
        OSError,
        sqlite3.Error,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ):
        return None


async def run_hero_request(
    request: HeroRequest,
    *,
    source: str | Path | None = None,
    workspace: Path = DEFAULT_HERO_WORKSPACE,
    force_new: bool = False,
    segments: int = 10000,
    reset_retries: int | None = None,
    reset_wait: float = DEFAULT_RESET_WAIT_SECONDS,
    max_segment_runtime: float | None = DEFAULT_LIVE_SEGMENT_RUNTIME_SECONDS,
    retry_stalled: bool = False,
    progress_callback: Callable[[str], None] | None = None,
    target_level: int = 100,
    password: str | None = None,
    remember_password: bool = False,
) -> tuple[HeroPreparation, CampaignResult]:
    # Keep the public HERO API bounded even when a caller explicitly passes
    # None. Longer runs remain available as explicit positive overrides.
    effective_max_segment_runtime = (
        DEFAULT_LIVE_SEGMENT_RUNTIME_SECONDS
        if max_segment_runtime is None
        else max_segment_runtime
    )
    preparation = prepare_hero_request(
        request,
        source=source,
        workspace=workspace,
        target_level=target_level,
    )
    generated_password = False
    if password is None:
        # Explicit CLI input wins; otherwise an operator-provided environment
        # value wins over the bounded credential lookup.  Resumes must reuse
        # the existing password and may never silently create a replacement.
        password = os.environ.get(preparation.character.password_env)
        credential_name = getattr(
            preparation.character,
            "credential_name",
            f"character:{(getattr(preparation.character, 'name', None) or request.name or '').casefold()}",
        )
        if password is None:
            password = await _load_character_password_with_timeout(
                credential_name,
            )
        if password is None:
            if preparation.resumed and _hero_campaign_has_started(preparation):
                character_name = getattr(
                    preparation.character,
                    "name",
                    request.name or "unknown",
                )
                raise RuntimeError(
                    f"no stored password for resumed hero "
                    f"{character_name!r}; provide --password or "
                    f"{preparation.character.password_env}"
                )
            password = _generated_character_password()
            await _save_character_password_with_timeout(
                credential_name,
                password,
            )
            generated_password = True
    if remember_password:
        if password is None:
            raise ValueError("remember_password requires a plaintext password")
        if not generated_password:
            await _save_character_password_with_timeout(
                preparation.character.credential_name,
                password,
            )
    with _temporary_character_password(
        preparation.character.password_env,
        password,
    ):
        result = await run_campaign_file(
            preparation.campaign_path,
            force_new=force_new,
            segments=segments,
            target_level_override=(
                target_level
                if request.legacy_campaign_path is not None
                else None
            ),
            reset_retries=(
                reset_retries
                if reset_retries is not None
                else (0 if effective_max_segment_runtime is not None else segments)
            ),
            reset_wait=reset_wait,
            max_segment_runtime=effective_max_segment_runtime,
            retry_stalled=retry_stalled,
            progress_callback=progress_callback,
        )
    return preparation, result


async def run_hero_until_target(
    request: HeroRequest,
    *,
    source: str | Path | None = None,
    workspace: Path = DEFAULT_HERO_WORKSPACE,
    force_new: bool = False,
    cycles: int = 10000,
    reset_retries: int | None = None,
    reset_wait: float = DEFAULT_RESET_WAIT_SECONDS,
    max_reset_waits: int = DEFAULT_AUTONOMOUS_RESET_WAITS,
    max_segment_runtime: float | None = DEFAULT_LIVE_SEGMENT_RUNTIME_SECONDS,
    retry_stalled: bool = False,
    progress_callback: Callable[[str], None] | None = None,
    target_level: int = 100,
    password: str | None = None,
    remember_password: bool = False,
) -> tuple[HeroPreparation, CampaignResult]:
    """Continue bounded HERO workers until success or a durable frontier.

    Each cycle owns one normal bounded campaign segment. Reset waits are a
    separate total budget so an unchanged world or a missing source target
    returns a resumable checkpoint instead of spinning forever.
    """
    if cycles < 1:
        raise ValueError("cycles must be positive")
    if max_reset_waits < 0:
        raise ValueError("max_reset_waits cannot be negative")
    if reset_retries is not None and reset_retries < 0:
        raise ValueError("reset_retries cannot be negative")

    waits_used = 0
    reset_wait_in_progress = False
    preparation: HeroPreparation | None = None
    result: CampaignResult | None = None

    def relay_progress(message: str) -> None:
        nonlocal reset_wait_in_progress, waits_used
        waiting_for_reset = message.startswith("Waiting for DD4 area reset:")
        if waiting_for_reset and not reset_wait_in_progress:
            waits_used += 1
        reset_wait_in_progress = waiting_for_reset
        if progress_callback is not None:
            progress_callback(message)

    for cycle in range(1, cycles + 1):
        if progress_callback is not None:
            progress_callback(
                f"Starting autonomous HERO cycle {cycle}/{cycles}; "
                f"reset waits used={waits_used}/{max_reset_waits}."
            )
        available_waits = max(0, max_reset_waits - waits_used)
        cycle_reset_retries = (
            (1 if reset_retries is None else reset_retries)
            if available_waits
            else 0
        )
        cycle_reset_retries = min(cycle_reset_retries, available_waits)
        preparation, result = await run_hero_request(
            request,
            source=source,
            workspace=workspace,
            force_new=force_new and cycle == 1,
            segments=1,
            reset_retries=cycle_reset_retries,
            reset_wait=reset_wait,
            max_segment_runtime=max_segment_runtime,
            retry_stalled=retry_stalled,
            progress_callback=relay_progress,
            target_level=target_level,
            password=password,
            remember_password=remember_password and cycle == 1,
        )

        level = _result_level(result)
        if progress_callback is not None:
            progress_callback(
                f"Completed autonomous HERO cycle {cycle}/{cycles}: "
                f"status={result.status}; level={level}; "
                f"reset waits used={waits_used}/{max_reset_waits}."
            )
        if result.status == "success" or level >= target_level:
            return preparation, result
        if result.status != "ready":
            return preparation, result
        if result.awaiting_area_reset:
            if waits_used >= max_reset_waits or cycle_reset_retries == 0:
                return preparation, result
            continue
        if not result.ready_for_next_segment:
            return preparation, result

    assert preparation is not None and result is not None
    return preparation, result


def _result_level(result: CampaignResult) -> int:
    try:
        return int(result.state.get("level", 0) or 0)
    except (TypeError, ValueError):
        return 0


def _generated_character_password() -> str:
    return "".join(
        secrets.choice(_GENERATED_PASSWORD_ALPHABET)
        for _ in range(_GENERATED_PASSWORD_LENGTH)
    )


def _hero_campaign_has_started(preparation: HeroPreparation) -> bool:
    """Keep missing credentials strict once a prepared hero has run."""
    database = getattr(preparation.character, "database", None)
    if database is None:
        # Lightweight test doubles and legacy profiles cannot prove that the
        # workspace is untouched, so preserve the conservative resume rule.
        return True
    database_path = Path(database)
    if not database_path.is_absolute():
        database_path = (Path.cwd() / database_path).resolve()
    if not database_path.is_file():
        return False
    config_path = preparation.campaign_path.resolve()
    try:
        with sqlite3.connect(
            database_path,
            timeout=_CAMPAIGN_PROBE_TIMEOUT_SECONDS,
        ) as connection:
            connection.execute(
                f"PRAGMA busy_timeout = {int(_CAMPAIGN_PROBE_TIMEOUT_SECONDS * 1000)}"
            )
            row = connection.execute(
                """
                SELECT 1
                FROM campaigns
                WHERE config_path IN (?, ?)
                LIMIT 1
                """,
                (str(config_path), str(preparation.campaign_path)),
            ).fetchone()
    except sqlite3.OperationalError as exc:
        if "no such table" in str(exc).casefold():
            return False
        return True
    except (OSError, sqlite3.Error):
        # Do not generate a replacement credential when the campaign state
        # cannot be inspected safely.
        return True
    return row is not None


async def _load_character_password_with_timeout(
    credential_name: str,
    timeout: float = _CREDENTIAL_READ_TIMEOUT_SECONDS,
) -> str | None:
    """Reuse a stored password without allowing keyring access to stall."""
    loop = asyncio.get_running_loop()
    result: asyncio.Future[tuple[str | None, BaseException | None]] = (
        loop.create_future()
    )

    def finish(value: str | None, failure: BaseException | None) -> None:
        if result.done():
            return
        result.set_result((value, failure))

    def publish(value: str | None, failure: BaseException | None) -> None:
        try:
            loop.call_soon_threadsafe(finish, value, failure)
        except RuntimeError:
            # The runner may be shutting down after the timeout fired.
            pass

    def load() -> None:
        try:
            value = load_character_password(credential_name)
        except CredentialStoreError:
            # A missing entry is the normal path for a genuinely new hero.
            publish(None, None)
        except BaseException as exc:
            publish(None, exc)
        else:
            publish(value, None)

    threading.Thread(
        target=load,
        name="dd4-keyring-load",
        daemon=True,
    ).start()
    try:
        value, failure = await asyncio.wait_for(result, timeout=timeout)
    except asyncio.TimeoutError as exc:
        raise RuntimeError(
            f"credential lookup for {credential_name!r} exceeded {timeout:g} seconds"
        ) from exc
    if failure is not None:
        raise failure
    return value


async def _save_character_password_with_timeout(
    credential_name: str,
    password: str,
    timeout: float = _CREDENTIAL_WRITE_TIMEOUT_SECONDS,
) -> None:
    """Persist a password without allowing a keyring prompt to stall the run."""
    loop = asyncio.get_running_loop()
    result: asyncio.Future[BaseException | None] = loop.create_future()

    def finish(value: BaseException | None) -> None:
        if result.done():
            return
        result.set_result(value)

    def publish(value: BaseException | None) -> None:
        try:
            loop.call_soon_threadsafe(finish, value)
        except RuntimeError:
            # The runner may be shutting down after the timeout fired.
            pass

    def save() -> None:
        try:
            save_character_password(credential_name, password)
        except BaseException as exc:
            publish(exc)
        else:
            publish(None)

    threading.Thread(
        target=save,
        name="dd4-keyring-save",
        daemon=True,
    ).start()
    try:
        failure = await asyncio.wait_for(result, timeout=timeout)
    except asyncio.TimeoutError as exc:
        raise RuntimeError(
            f"credential storage for {credential_name!r} exceeded {timeout:g} seconds"
        ) from exc
    if failure is not None:
        raise failure


def _validate_target_level(target_level: int) -> None:
    if not 2 <= target_level <= 100:
        raise ValueError("target_level must be between 2 and 100")


def _update_campaign_target(path: Path, target_level: int) -> None:
    mapping = load_yaml_mapping(path)
    current_target = int(mapping.get("target_level", 100))
    if current_target >= target_level:
        return
    mapping["target_level"] = target_level
    # Keep the generated operator-facing name aligned with the durable goal.
    # Leave hand-written campaign names alone when they do not use the HERO
    # entry point's ``<name> to ...`` convention.
    current_name = str(mapping.get("name", "")).strip()
    prefix_match = re.match(
        r"^(?P<prefix>.+?)\s+to\s+(?:HERO|level\s+\d+)\s*$",
        current_name,
        flags=re.IGNORECASE,
    )
    if prefix_match:
        prefix = prefix_match.group("prefix").strip()
        mapping["name"] = (
            f"{prefix} to HERO"
            if target_level == 100
            else f"{prefix} to level {target_level}"
        )
    path.write_text(_render_yaml(mapping), encoding="utf-8")


@contextmanager
def _temporary_character_password(
    environment_name: str,
    password: str | None,
) -> Iterator[None]:
    if password is None:
        yield
        return
    if not password:
        raise ValueError("password must not be empty")
    previous = os.environ.get(environment_name)
    os.environ[environment_name] = password
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(environment_name, None)
        else:
            os.environ[environment_name] = previous


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
    if request.personality:
        mapping["personality"] = request.personality
    if request.transport == "mudlet":
        assert request.mudlet_directory is not None
        mapping["transport"] = "mudlet"
        mapping["mudlet_directory"] = str(request.mudlet_directory)
    return mapping


def _initialize_mudlet_bridge(request: HeroRequest) -> None:
    if request.transport != "mudlet":
        return
    assert request.mudlet_directory is not None
    MudletBridge(request.mudlet_directory).initialize()


def _request_mapping(request: HeroRequest) -> dict[str, Any]:
    mapping = {
        "name": request.name,
        "race": request.race,
        "sex": request.sex,
        "class": request.character_class,
        "subclass": request.subclass,
        "personality": request.personality,
    }
    if request.transport != "telnet":
        mapping["transport"] = request.transport
        mapping["mudlet_directory"] = str(request.mudlet_directory)
    return mapping


def _resume_request_matches(
    stored: object,
    requested: dict[str, Any],
) -> bool:
    """Match an existing workspace while inheriting omitted optional fields."""
    if not isinstance(stored, dict):
        return False
    for key in ("name", "race", "sex", "class"):
        if stored.get(key) != requested.get(key):
            return False
    for key in ("subclass", "personality"):
        requested_value = requested.get(key)
        if requested_value is not None and stored.get(key) != requested_value:
            return False
    for key in ("transport", "mudlet_directory"):
        if key in requested and stored.get(key) != requested.get(key):
            return False
    return True


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
