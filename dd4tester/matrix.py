from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable

from .campaign import CampaignResult, CampaignSpec, load_campaign_spec, run_campaign_file
from .scenario import load_yaml_mapping


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

    @classmethod
    def from_mapping(cls, data: dict[str, object], *, path: Path) -> "MatrixSpec":
        name = str(data.get("name", path.stem)).strip()
        if not name:
            raise ValueError("matrix name must not be empty")
        target_level = int(data.get("target_level", 10))
        if not 2 <= target_level <= 100:
            raise ValueError("matrix target_level must be between 2 and 100")
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
        return cls(name, target_level, tuple(entries))


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


def load_matrix_spec(path: str | Path) -> MatrixSpec:
    matrix_path = Path(path).resolve()
    return MatrixSpec.from_mapping(load_yaml_mapping(matrix_path), path=matrix_path)


async def run_matrix_file(
    path: str | Path,
    *,
    rounds: int = 1,
    segments_per_character: int = 1,
    force_new: bool = False,
    campaign_runner: CampaignFileRunner = run_campaign_file,
) -> MatrixResult:
    if rounds < 1:
        raise ValueError("rounds must be positive")
    if segments_per_character < 1:
        raise ValueError("segments_per_character must be positive")
    spec = load_matrix_spec(path)
    latest: dict[str, MatrixEntryResult] = {}

    for round_index in range(rounds):
        for entry in spec.entries:
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


def _level(state: dict[str, object]) -> int:
    value = state.get("level")
    return int(value) if isinstance(value, (int, float)) else 0
