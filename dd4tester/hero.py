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
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Iterator

from .campaign import (
    DEFAULT_RESET_WAIT_SECONDS,
    CampaignResult,
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
) -> HeroRequest:
    """Load the non-secret request identity for an existing hero workspace."""
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("an existing hero name is required")
    manifest_path = _find_existing_hero_manifest(
        workspace,
        clean_name,
        target_level=target_level,
    )
    if manifest_path is None:
        raise ValueError(
            f"no stored hero workspace exists for {clean_name!r}; provide "
            "--race and --class to create it"
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
    stored horizons are lower, use the longest one. Equal horizons remain an
    explicit ambiguity instead of being selected by filesystem order.
    """
    clean_name = name.strip().casefold()
    if not clean_name:
        return None
    root = workspace.resolve()
    if not root.is_dir():
        return None
    matches: list[tuple[Path, int]] = []
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
                )
            )
    if len(matches) > 1:
        requested_target = max(int(target_level), 0)
        eligible_targets = [
            target for _path, target in matches if target >= requested_target
        ]
        selected_target = (
            min(eligible_targets)
            if eligible_targets
            else max(target for _path, target in matches)
        )
        selected = [
            path for path, target in matches if target == selected_target
        ]
        if len(selected) == 1:
            return selected[0]
        locations = ", ".join(str(path) for path in sorted(selected))
        raise ValueError(
            f"multiple stored hero workspaces with the same campaign horizon "
            f"exist for {name!r} (target level {selected_target}): {locations}"
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


async def run_hero_request(
    request: HeroRequest,
    *,
    source: str | Path | None = None,
    workspace: Path = DEFAULT_HERO_WORKSPACE,
    force_new: bool = False,
    segments: int = 10000,
    reset_retries: int | None = None,
    reset_wait: float = DEFAULT_RESET_WAIT_SECONDS,
    max_segment_runtime: float | None = None,
    retry_stalled: bool = False,
    progress_callback: Callable[[str], None] | None = None,
    target_level: int = 100,
    password: str | None = None,
    remember_password: bool = False,
) -> tuple[HeroPreparation, CampaignResult]:
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
            reset_retries=(
                reset_retries
                if reset_retries is not None
                else (0 if max_segment_runtime is not None else segments)
            ),
            reset_wait=reset_wait,
            max_segment_runtime=max_segment_runtime,
            retry_stalled=retry_stalled,
            progress_callback=progress_callback,
        )
    return preparation, result


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
