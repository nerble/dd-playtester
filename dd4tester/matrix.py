from __future__ import annotations

import asyncio
import json
import os
import secrets
import string
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable

from .campaign import CampaignResult, CampaignSpec, load_campaign_spec, run_campaign_file
from .credentials import (
    CredentialStoreError,
    load_character_password,
    save_character_password,
)
from .dd4_catalog import CharacterCatalog, load_character_catalog
from .hero import HeroRequest, HeroPreparation, prepare_hero_request
from .scenario import load_yaml_mapping
from .storage import RunStorage


CampaignFileRunner = Callable[..., Awaitable[CampaignResult]]


@dataclass(frozen=True)
class MatrixEntry:
    entry_id: str
    campaign_path: Path
    campaign: CampaignSpec


@dataclass(frozen=True)
class MatrixSpec:
    name: str
    target_level: int
    entries: tuple[MatrixEntry, ...]
    inter_character_delay: float = 0.0

    @classmethod
    def from_mapping(cls, data: dict[str, object], *, path: Path) -> "MatrixSpec":
        name = str(data.get("name", path.stem)).strip()
        if not name:
            raise ValueError("matrix name must not be empty")
        target_level = int(data.get("target_level", 10))
        if not 2 <= target_level <= 100:
            raise ValueError("matrix target_level must be between 2 and 100")
        inter_character_delay = float(data.get("inter_character_delay", 0))
        if not 0 <= inter_character_delay <= 900:
            raise ValueError("inter_character_delay must be between 0 and 900 seconds")
        raw_entries = data.get("entries")
        if not isinstance(raw_entries, list) or len(raw_entries) < 3:
            raise ValueError("matrix must define at least three entries")

        entries: list[MatrixEntry] = []
        for index, raw_entry in enumerate(raw_entries, start=1):
            if not isinstance(raw_entry, dict):
                raise ValueError(f"matrix entry {index} must be a mapping")
            entry_id = str(raw_entry.get("id", f"entry-{index}")).strip()
            campaign_value = raw_entry.get("campaign")
            if not entry_id or not campaign_value:
                raise ValueError(f"matrix entry {index} requires id and campaign")
            campaign_path = Path(str(campaign_value))
            if not campaign_path.is_absolute():
                campaign_path = path.parent / campaign_path
            campaign_path = campaign_path.resolve()
            campaign = load_campaign_spec(campaign_path)
            if campaign.target_level < target_level:
                raise ValueError(
                    f"matrix entry {entry_id!r} campaign target "
                    f"{campaign.target_level} is below matrix target {target_level}"
                )
            entries.append(MatrixEntry(entry_id, campaign_path, campaign))

        _validate_representative_entries(entries)
        return cls(name, target_level, tuple(entries), inter_character_delay)


@dataclass(frozen=True)
class MatrixEntryResult:
    entry_id: str
    character_name: str
    character_class: str
    campaign_id: int | None
    status: str
    level: int
    message: str | None


@dataclass(frozen=True)
class MatrixResult:
    name: str
    target_level: int
    status: str
    entries: tuple[MatrixEntryResult, ...]


@dataclass(frozen=True)
class MatrixCredentialResult:
    entry_id: str
    credential_name: str
    status: str


@dataclass(frozen=True)
class MatrixCoverage:
    source: str
    source_revision: str | None
    legal_pair_count: int
    covered_pairs: tuple[tuple[str, str], ...]
    missing_pairs: tuple[tuple[str, str], ...]
    covered_classes: tuple[str, ...]
    missing_classes: tuple[str, ...]
    observed_sexes: tuple[str, ...]


@dataclass(frozen=True)
class MatrixLiveEntry:
    """Persisted execution evidence for one declarative validation entry."""

    entry_id: str
    character_name: str
    race: str
    character_class: str
    sex: str
    campaign_id: int | None
    campaign_status: str | None
    level: int


@dataclass(frozen=True)
class MatrixLiveCoverage:
    """Separate durable validation evidence from YAML representation coverage."""

    target_level: int
    entries: tuple[MatrixLiveEntry, ...]
    validated_pairs: tuple[tuple[str, str], ...]
    pending_pairs: tuple[tuple[str, str], ...]
    validated_sexes: tuple[str, ...]


@dataclass(frozen=True)
class ValidationMatrixPreparation:
    matrix_path: Path
    preparations: tuple[HeroPreparation, ...]
    catalog: CharacterCatalog


def load_matrix_spec(path: str | Path) -> MatrixSpec:
    matrix_path = Path(path).resolve()
    return MatrixSpec.from_mapping(load_yaml_mapping(matrix_path), path=matrix_path)


def matrix_coverage(
    path: str | Path,
    *,
    catalog: CharacterCatalog | None = None,
) -> MatrixCoverage:
    """Compare a level-validation matrix with DD4's creation selections.

    DD4's CON_GET_NEW_CLASS loop exposes every class after race selection
    without a race branch, so the source-legal base coverage is the full
    race/class Cartesian product. Sex stays a separate cosmetic observation.
    """
    spec = load_matrix_spec(path)
    options = catalog or load_character_catalog()
    legal_pairs = {
        (race.name, character_class.name)
        for race in options.races
        for character_class in options.classes
    }
    represented = {
        (entry.campaign.character.race, entry.campaign.character.character_class)
        for entry in spec.entries
    }
    covered_pairs = tuple(sorted(legal_pairs & represented))
    classes = {entry.campaign.character.character_class for entry in spec.entries}
    observed_sexes = tuple(
        sorted({entry.campaign.character.gender for entry in spec.entries})
    )
    all_classes = {option.name for option in options.classes}
    return MatrixCoverage(
        source=options.source,
        source_revision=options.source_revision,
        legal_pair_count=len(legal_pairs),
        covered_pairs=covered_pairs,
        missing_pairs=tuple(sorted(legal_pairs - represented)),
        covered_classes=tuple(sorted(classes & all_classes)),
        missing_classes=tuple(sorted(all_classes - classes)),
        observed_sexes=observed_sexes,
    )


def live_matrix_coverage(path: str | Path) -> MatrixLiveCoverage:
    """Read durable campaign state without treating declared entries as runs."""

    spec = load_matrix_spec(path)
    entries = tuple(_live_matrix_entry(entry) for entry in spec.entries)
    validated_pairs = tuple(
        sorted(
            {
                (entry.race, entry.character_class)
                for entry in entries
                if entry.level >= spec.target_level
            }
        )
    )
    pending_pairs = tuple(
        sorted(
            {
                (entry.race, entry.character_class)
                for entry in entries
                if entry.level < spec.target_level
            }
        )
    )
    validated_sexes = tuple(
        sorted({entry.sex for entry in entries if entry.level >= spec.target_level})
    )
    return MatrixLiveCoverage(
        target_level=spec.target_level,
        entries=entries,
        validated_pairs=validated_pairs,
        pending_pairs=pending_pairs,
        validated_sexes=validated_sexes,
    )


def prepare_validation_matrix(
    *,
    catalog: CharacterCatalog | None = None,
    source: str | Path | None = None,
    workspace: Path,
    matrix_path: Path | None = None,
) -> ValidationMatrixPreparation:
    """Prepare one resumable level-10 validation campaign per legal race/class.

    Sex alternates between female and male because it is cosmetic in DD4 while
    still satisfying the cross-sex validation requirement without multiplying
    every race/class run. The generated campaigns retain their normal level-100
    destination; the matrix scheduler caps this validation pass at level 10.
    """
    options = catalog or load_character_catalog(source)
    validation_sexes = tuple(
        sex for sex in ("female", "male") if sex in options.sexes
    )
    if len(validation_sexes) < 2:
        raise ValueError("DD4 source must expose both female and male creation sexes")

    preparations: list[HeroPreparation] = []
    for index, (race, character_class) in enumerate(
        (race, character_class)
        for race in options.races
        for character_class in options.classes
    ):
        preparations.append(
            prepare_hero_request(
                HeroRequest(
                    race=race.name,
                    sex=validation_sexes[index % len(validation_sexes)],
                    character_class=character_class.name,
                ),
                catalog=options,
                workspace=workspace,
            )
        )

    destination = (matrix_path or workspace / "validation-level-10.yaml").resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    entries = [
        {
            "id": f"{preparation.character.race}-{preparation.character.character_class}",
            "campaign": os.path.relpath(
                preparation.campaign_path,
                destination.parent,
            ).replace(os.sep, "/"),
        }
        for preparation in preparations
    ]
    destination.write_text(
        _render_matrix_yaml(
            {
                "name": "DD4 Source-Legal Race/Class Level 10 Validation",
                "target_level": 10,
                "inter_character_delay": 75,
                "entries": entries,
            }
        ),
        encoding="utf-8",
    )
    return ValidationMatrixPreparation(destination, tuple(preparations), options)


def provision_matrix_passwords(
    path: str | Path,
    *,
    password_loader: Callable[[str], str] = load_character_password,
    password_saver: Callable[[str, str], None] = save_character_password,
    password_factory: Callable[[], str] | None = None,
) -> tuple[MatrixCredentialResult, ...]:
    spec = load_matrix_spec(path)
    make_password = password_factory or _generated_password
    results: list[MatrixCredentialResult] = []
    for entry in spec.entries:
        credential_name = entry.campaign.character.credential_name
        try:
            password_loader(credential_name)
        except CredentialStoreError:
            password_saver(credential_name, make_password())
            status = "generated"
        else:
            status = "existing"
        results.append(
            MatrixCredentialResult(entry.entry_id, credential_name, status)
        )
    return tuple(results)


async def run_matrix_file(
    path: str | Path,
    *,
    rounds: int = 1,
    segments_per_character: int = 1,
    force_new: bool = False,
    campaign_runner: CampaignFileRunner = run_campaign_file,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> MatrixResult:
    if rounds < 1:
        raise ValueError("rounds must be positive")
    if segments_per_character < 1:
        raise ValueError("segments_per_character must be positive")
    spec = load_matrix_spec(path)
    latest: dict[str, MatrixEntryResult] = {}

    for round_index in range(rounds):
        for entry_index, entry in enumerate(spec.entries):
            previous = latest.get(entry.entry_id)
            if previous is not None and previous.level >= spec.target_level:
                continue
            try:
                result = await campaign_runner(
                    entry.campaign_path,
                    force_new=force_new and round_index == 0,
                    segments=segments_per_character,
                )
            except Exception as error:
                latest[entry.entry_id] = MatrixEntryResult(
                    entry.entry_id,
                    entry.campaign.character.name,
                    entry.campaign.character.character_class,
                    None,
                    "failed",
                    previous.level if previous is not None else 0,
                    str(error),
                )
                more_work_follows = (
                    entry_index < len(spec.entries) - 1
                    or round_index < rounds - 1
                )
                if spec.inter_character_delay and more_work_follows:
                    await sleep(spec.inter_character_delay)
                continue
            level = _level(result.state)
            latest[entry.entry_id] = MatrixEntryResult(
                entry.entry_id,
                entry.campaign.character.name,
                entry.campaign.character.character_class,
                result.campaign_id,
                result.status,
                level,
                result.message,
            )
            more_work_follows = (
                entry_index < len(spec.entries) - 1 or round_index < rounds - 1
            )
            if spec.inter_character_delay and more_work_follows:
                await sleep(spec.inter_character_delay)
        if all(
            latest.get(entry.entry_id) is not None
            and latest[entry.entry_id].level >= spec.target_level
            for entry in spec.entries
        ):
            break

    ordered = tuple(latest[entry.entry_id] for entry in spec.entries)
    status = (
        "success"
        if all(result.level >= spec.target_level for result in ordered)
        else "incomplete"
    )
    return MatrixResult(spec.name, spec.target_level, status, ordered)


def _validate_representative_entries(entries: list[MatrixEntry]) -> None:
    ids = [entry.entry_id.casefold() for entry in entries]
    names = [entry.campaign.character.name.casefold() for entry in entries]
    classes = [entry.campaign.character.character_class for entry in entries]
    if len(ids) != len(set(ids)):
        raise ValueError("matrix entry ids must be unique")
    if len(names) != len(set(names)):
        raise ValueError("matrix character names must be unique")
    if len(set(classes)) < 3:
        raise ValueError("representative matrix requires at least three classes")


def _live_matrix_entry(entry: MatrixEntry) -> MatrixLiveEntry:
    character = entry.campaign.character
    database = entry.campaign.database
    if not database.is_file():
        return MatrixLiveEntry(
            entry.entry_id,
            character.name,
            character.race,
            character.character_class,
            character.gender,
            None,
            None,
            0,
        )

    with RunStorage(database) as storage:
        campaign = storage.get_latest_campaign_for_config(entry.campaign_path)
        if campaign is None:
            return MatrixLiveEntry(
                entry.entry_id,
                character.name,
                character.race,
                character.character_class,
                character.gender,
                None,
                None,
                0,
            )
        state = storage.get_latest_character_state(character.name)
        if state is None:
            checkpoint = storage.get_latest_campaign_checkpoint(int(campaign["id"]))
            state = _checkpoint_state(checkpoint["state_json"] if checkpoint else None)
        return MatrixLiveEntry(
            entry.entry_id,
            character.name,
            character.race,
            character.character_class,
            character.gender,
            int(campaign["id"]),
            str(campaign["status"]),
            _level(state),
        )


def _checkpoint_state(value: object) -> dict[str, object]:
    if not isinstance(value, str):
        return {}
    try:
        state = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return state if isinstance(state, dict) else {}


def _level(state: dict[str, object]) -> int:
    value = state.get("level")
    return int(value) if isinstance(value, (int, float)) else 0


def _generated_password() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(16))


def _render_matrix_yaml(data: dict[str, object]) -> str:
    lines = [
        f'name: "{data["name"]}"',
        f'target_level: {data["target_level"]}',
        f'inter_character_delay: {data["inter_character_delay"]}',
        "entries:",
    ]
    for entry in data["entries"]:
        assert isinstance(entry, dict)
        lines.extend(
            (
                f'  - id: "{entry["id"]}"',
                f'    campaign: "{entry["campaign"]}"',
            )
        )
    return "\n".join(lines) + "\n"
