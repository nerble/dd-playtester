import asyncio
from pathlib import Path

import pytest

from dataclasses import replace

from dd4tester.campaign import CampaignResult
from dd4tester.credentials import CredentialStoreError
from dd4tester.dd4_catalog import load_character_catalog
from dd4tester.matrix import (
    live_matrix_coverage,
    load_matrix_spec,
    matrix_coverage,
    prepare_validation_matrix,
    provision_matrix_passwords,
    run_matrix_file,
)
from dd4tester.storage import RunStorage


def test_repository_matrix_covers_requested_contrasting_classes() -> None:
    spec = load_matrix_spec(Path("matrices/level-10.yaml"))

    assert spec.target_level == 10
    assert spec.inter_character_delay == 75
    assert [entry.campaign.character.character_class for entry in spec.entries] == [
        "mage",
        "thief",
        "warrior",
    ]
    assert len({entry.campaign.character.race for entry in spec.entries}) == 3
    assert len({entry.campaign.character.gender for entry in spec.entries}) == 3
    assert all(entry.campaign.character.subclass for entry in spec.entries)


def test_matrix_coverage_reports_missing_source_legal_pairs(tmp_path) -> None:
    matrix_path = _write_matrix(tmp_path)
    catalog = load_character_catalog()

    coverage = matrix_coverage(matrix_path, catalog=catalog)

    assert coverage.legal_pair_count == len(catalog.races) * len(catalog.classes)
    assert coverage.covered_pairs == (
        ("human", "mage"),
        ("human", "thief"),
        ("human", "warrior"),
    )
    assert len(coverage.missing_pairs) == coverage.legal_pair_count - 3
    assert coverage.missing_classes == (
        "brawler",
        "cleric",
        "psionic",
        "ranger",
        "shifter",
        "smithy",
    )
    assert coverage.observed_sexes == ("female",)


def test_live_matrix_coverage_requires_persisted_target_level_evidence(tmp_path) -> None:
    matrix_path = _write_matrix(tmp_path)
    spec = load_matrix_spec(matrix_path)

    initial = live_matrix_coverage(matrix_path)

    assert initial.validated_pairs == ()
    assert len(initial.pending_pairs) == 3
    assert all(entry.campaign_status is None for entry in initial.entries)

    mage = spec.entries[0]
    with RunStorage(mage.campaign.database) as storage:
        campaign_id = storage.create_campaign(
            name=mage.campaign.name,
            config_path=mage.campaign_path,
            character_profile_path=mage.campaign.character_profile,
            target_level=mage.campaign.target_level,
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=None,
            run_id=None,
            phase="validation",
            reason="target_reached",
            state={"level": 10},
        )
        storage.finish_campaign(campaign_id, status="success")

    covered = live_matrix_coverage(matrix_path)

    assert covered.validated_pairs == (("human", "mage"),)
    assert len(covered.pending_pairs) == 2
    assert covered.validated_sexes == ("female",)
    assert covered.entries[0].campaign_status == "success"
    assert covered.entries[0].level == 10


def test_prepare_validation_matrix_generates_each_legal_pair_once(tmp_path) -> None:
    catalog = load_character_catalog()
    catalog = replace(catalog, races=catalog.races[:2], classes=catalog.classes[:3])

    prepared = prepare_validation_matrix(
        catalog=catalog,
        workspace=tmp_path / "validation",
    )
    matrix = load_matrix_spec(prepared.matrix_path)

    assert len(prepared.preparations) == 6
    assert len(matrix.entries) == 6
    assert {item.character.gender for item in prepared.preparations} == {
        "female",
        "male",
    }
    assert len({item.character.name for item in prepared.preparations}) == 6
    assert all(item.campaign_path.is_file() for item in matrix.entries)


def test_matrix_runs_round_robin_and_continues_after_one_failure(tmp_path) -> None:
    matrix_path = _write_matrix(tmp_path)
    calls: list[tuple[str, bool, int]] = []
    levels = {"mage": 10, "thief": 8, "warrior": 10}

    async def fake_campaign_runner(path, *, force_new, segments):
        entry_id = Path(path).stem
        calls.append((entry_id, force_new, segments))
        if entry_id == "thief" and sum(call[0] == "thief" for call in calls) == 1:
            raise RuntimeError("temporary thief research gate")
        level = levels[entry_id]
        return CampaignResult(
            campaign_id=len(calls),
            status="success" if level == 10 else "blocked",
            checkpoint_id=None,
            message=None,
            state={"level": level},
        )

    result = asyncio.run(
        run_matrix_file(
            matrix_path,
            rounds=2,
            segments_per_character=3,
            force_new=True,
            campaign_runner=fake_campaign_runner,
        )
    )

    assert [entry.entry_id for entry in result.entries] == [
        "mage",
        "thief",
        "warrior",
    ]
    assert result.status == "incomplete"
    assert [call[0] for call in calls] == ["mage", "thief", "warrior", "thief"]
    assert calls[:3] == [
        ("mage", True, 3),
        ("thief", True, 3),
        ("warrior", True, 3),
    ]
    assert calls[-1] == ("thief", False, 3)


def test_matrix_rejects_repeated_classes(tmp_path) -> None:
    matrix_path = _write_matrix(tmp_path, classes=("mage", "mage", "warrior"))

    with pytest.raises(ValueError, match="at least three classes"):
        load_matrix_spec(matrix_path)


def test_matrix_applies_reset_delay_even_after_an_entry_failure(tmp_path) -> None:
    matrix_path = _write_matrix(tmp_path, inter_character_delay=12)
    slept: list[float] = []

    async def failing_runner(path, **_kwargs):
        if Path(path).stem == "mage":
            raise RuntimeError("depleted tutorial")
        return CampaignResult(1, "blocked", None, None, {"level": 2})

    async def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    asyncio.run(
        run_matrix_file(
            matrix_path,
            campaign_runner=failing_runner,
            sleep=fake_sleep,
        )
    )

    assert slept == [12, 12]


def test_matrix_password_provisioning_preserves_existing_credentials(tmp_path) -> None:
    matrix_path = _write_matrix(tmp_path)
    stored = {"character:matrim": "existing-password"}

    def load(name: str) -> str:
        try:
            return stored[name]
        except KeyError as error:
            raise CredentialStoreError("missing") from error

    def save(name: str, password: str) -> None:
        stored[name] = password

    results = provision_matrix_passwords(
        matrix_path,
        password_loader=load,
        password_saver=save,
        password_factory=lambda: "generated-password",
    )

    assert [result.status for result in results] == [
        "existing",
        "generated",
        "generated",
    ]
    assert stored["character:matrim"] == "existing-password"
    assert stored["character:selene"] == "generated-password"
    assert stored["character:dorrin"] == "generated-password"


def _write_matrix(
    root: Path,
    *,
    classes: tuple[str, str, str] = ("mage", "thief", "warrior"),
    inter_character_delay: float = 0,
) -> Path:
    entries: list[str] = []
    subclasses = {"mage": "warlock", "thief": "ninja", "warrior": "knight"}
    names = ("Matrim", "Selene", "Dorrin")
    for index, character_class in enumerate(classes):
        entry_id = ("mage", "thief", "warrior")[index]
        profile = root / f"{entry_id}.profile.yaml"
        profile.write_text(
            "\n".join(
                [
                    f"name: {names[index]}",
                    "race: human",
                    "gender: female",
                    f"class: {character_class}",
                    f"subclass: {subclasses[character_class]}",
                    f"database: {root / 'runs.sqlite3'}",
                    f"transcript_dir: {root / 'transcripts'}",
                ]
            ),
            encoding="utf-8",
        )
        campaign = root / f"{entry_id}.yaml"
        campaign.write_text(
            "\n".join(
                [
                    f"character_profile: {profile.name}",
                    f"name: {entry_id} proof",
                    "target_level: 10",
                ]
            ),
            encoding="utf-8",
        )
        entries.extend(
            [
                f"  - id: {entry_id}",
                f"    campaign: {campaign.name}",
            ]
        )
    matrix_path = root / "matrix.yaml"
    matrix_path.write_text(
        "\n".join(
            [
                "name: test matrix",
                "target_level: 10",
                f"inter_character_delay: {inter_character_delay}",
                "entries:",
                *entries,
            ]
        ),
        encoding="utf-8",
    )
    return matrix_path
