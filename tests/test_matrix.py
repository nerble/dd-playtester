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
from dd4tester.scenario import load_yaml_mapping
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


def test_active_hero_rotation_includes_all_hero_target_workspaces() -> None:
    data = load_yaml_mapping(Path("matrices/active-hero-rotation.yaml"))

    assert data["target_level"] == 100
    assert [entry["id"] for entry in data["entries"]] == [
        "aeloria",
        "astrevo",
        "dorrik",
        "kestrel",
        "praelarran",
        "serevian",
    ]
    assert all(
        str(entry["campaign"]).startswith("../runs/heroes/")
        for entry in data["entries"]
    )


def test_repository_full_validation_matrix_declares_all_source_legal_pairs() -> None:
    spec = load_matrix_spec(Path("matrices/level-10-all-race-class.yaml"))
    coverage = matrix_coverage(
        Path("matrices/level-10-all-race-class.yaml"),
        catalog=load_character_catalog(),
    )

    assert spec.target_level == 10
    assert len(spec.entries) == coverage.legal_pair_count
    assert coverage.missing_pairs == ()
    assert coverage.missing_classes == ()
    assert coverage.observed_sexes == ("female", "male")


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
    assert covered.entries[0].target_reached is True
    assert covered.entries[0].proof_status == "target-reached"
    assert covered.creation_to_target_pairs == ()
    assert len(covered.creation_pending_pairs) == 3


def test_live_matrix_coverage_requires_creation_evidence_for_strict_proof(
    tmp_path,
    monkeypatch,
) -> None:
    matrix_path = _write_matrix(tmp_path)
    spec = load_matrix_spec(matrix_path)
    mage = spec.entries[0]

    with RunStorage(mage.campaign.database) as storage:
        campaign_id = storage.create_campaign(
            name=mage.campaign.name,
            config_path=mage.campaign_path,
            character_profile_path=mage.campaign.character_profile,
            target_level=mage.campaign.target_level,
        )
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="starter",
            start_state={"name": mage.campaign.character.name, "level": 1},
        )
        run_id = storage.create_run(
            scenario_name=f"starter:{mage.campaign.character.name}",
            scenario_path=mage.campaign.character_profile,
        )
        storage.record_event(
            run_id,
            kind="decision",
            payload={
                "stage": "create_race",
                "category": "creation",
                "command": "human",
            },
        )
        storage.finish_run(run_id, status="success")
        storage.finish_campaign_segment(
            segment_id,
            status="success",
            run_id=run_id,
            end_state={"name": mage.campaign.character.name, "level": 10},
            command_count=1,
            duration_seconds=1,
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=segment_id,
            run_id=run_id,
            phase="starter",
            reason="segment_complete",
            state={"name": mage.campaign.character.name, "level": 10},
        )
        storage.finish_campaign(campaign_id, status="success")

    def unexpected_history_scan(*args, **kwargs):
        raise AssertionError("matrix coverage must use bounded storage queries")

    monkeypatch.setattr(RunStorage, "list_campaign_checkpoints", unexpected_history_scan)
    monkeypatch.setattr(RunStorage, "list_campaign_segments", unexpected_history_scan)
    monkeypatch.setattr(RunStorage, "list_events", unexpected_history_scan)

    covered = live_matrix_coverage(matrix_path)

    assert covered.validated_pairs == (("human", "mage"),)
    assert covered.creation_to_target_pairs == (("human", "mage"),)
    assert covered.creation_validated_sexes == ("female",)
    assert covered.entries[0].creation_observed is True
    assert covered.entries[0].target_checkpoint_reason == "segment_complete"
    assert covered.entries[0].proof_status == "creation-to-target"


def test_live_matrix_coverage_ignores_unrelated_character_snapshot(
    tmp_path,
) -> None:
    matrix_path = _write_matrix(tmp_path)
    spec = load_matrix_spec(matrix_path)
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
            state={"name": mage.campaign.character.name, "level": 10},
        )
        unrelated_run_id = storage.create_run(
            scenario_name=f"other:{mage.campaign.character.name}",
            scenario_path=mage.campaign.character_profile,
        )
        storage.record_state_snapshot(
            unrelated_run_id,
            source_event_id=None,
            reason="progress_changed",
            state={"name": mage.campaign.character.name, "level": 99},
        )
        storage.finish_run(unrelated_run_id, status="success")
        storage.finish_campaign(campaign_id, status="success")

    covered = live_matrix_coverage(matrix_path)

    assert covered.entries[0].level == 10
    assert covered.entries[0].target_reached is True


def test_live_matrix_coverage_rejects_high_level_runtime_cap_checkpoint(
    tmp_path,
) -> None:
    matrix_path = _write_matrix(tmp_path)
    spec = load_matrix_spec(matrix_path)
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
            phase="source-ranked-hunt",
            reason="segment_runtime_cap",
            state={"name": mage.campaign.character.name, "level": 99},
        )
        storage.finish_campaign(campaign_id, status="ready")

    covered = live_matrix_coverage(matrix_path)

    assert covered.entries[0].level == 99
    assert covered.entries[0].target_reached is False
    assert covered.entries[0].proof_status == "in-progress"
    assert covered.validated_pairs == ()


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


def test_matrix_passes_bounded_segment_runtime_to_campaigns(tmp_path) -> None:
    matrix_path = _write_matrix(tmp_path)
    observed: list[dict[str, object]] = []

    async def fake_campaign_runner(path, **kwargs):
        observed.append({"path": Path(path).stem, **kwargs})
        return CampaignResult(
            campaign_id=len(observed),
            status="success",
            checkpoint_id=None,
            message=None,
            state={"level": 10},
        )

    result = asyncio.run(
        run_matrix_file(
            matrix_path,
            max_segment_runtime=180,
            campaign_runner=fake_campaign_runner,
        )
    )

    assert result.status == "success"
    assert [item["path"] for item in observed] == ["mage", "thief", "warrior"]
    assert all(item["max_segment_runtime"] == 180 for item in observed)


def test_matrix_forwards_progress_with_entry_context(tmp_path) -> None:
    matrix_path = _write_matrix(tmp_path)
    messages: list[str] = []

    async def fake_campaign_runner(path, **kwargs):
        progress_callback = kwargs.get("progress_callback")
        assert progress_callback is not None
        progress_callback("bounded attempt started")
        return CampaignResult(
            campaign_id=1,
            status="success",
            checkpoint_id=17,
            message="checkpointed",
            state={"level": 10},
        )

    result = asyncio.run(
        run_matrix_file(
            matrix_path,
            campaign_runner=fake_campaign_runner,
            progress_callback=messages.append,
        )
    )

    assert result.status == "success"
    assert messages[0].startswith("Starting matrix round 1/1")
    assert any("mage: bounded attempt started" in message for message in messages)
    assert any("Completed mage: status=success, level=10" in message for message in messages)


def test_matrix_does_not_promote_blocked_high_level_result(tmp_path) -> None:
    matrix_path = _write_matrix(tmp_path)

    async def blocked_runner(path, **_kwargs):
        return CampaignResult(
            campaign_id=1,
            status="blocked",
            checkpoint_id=None,
            message="stale checkpoint cannot continue",
            state={"level": 10},
        )

    result = asyncio.run(
        run_matrix_file(
            matrix_path,
            campaign_runner=blocked_runner,
        )
    )

    assert result.status == "incomplete"
    assert all(entry.status == "blocked" for entry in result.entries)


def test_matrix_rejects_non_positive_segment_runtime(tmp_path) -> None:
    with pytest.raises(ValueError, match="max_segment_runtime must be positive"):
        asyncio.run(run_matrix_file(tmp_path / "matrix.yaml", max_segment_runtime=0))


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
