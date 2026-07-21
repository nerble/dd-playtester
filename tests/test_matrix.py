import asyncio
from pathlib import Path

import pytest

from dd4tester.campaign import CampaignResult
from dd4tester.matrix import load_matrix_spec, run_matrix_file


def test_repository_matrix_covers_requested_contrasting_classes() -> None:
    spec = load_matrix_spec(Path("matrices/level-10.yaml"))

    assert spec.target_level == 10
    assert [entry.campaign.character.character_class for entry in spec.entries] == [
        "mage",
        "thief",
        "warrior",
    ]
    assert len({entry.campaign.character.race for entry in spec.entries}) == 3
    assert len({entry.campaign.character.gender for entry in spec.entries}) == 3
    assert all(entry.campaign.character.subclass for entry in spec.entries)


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


def _write_matrix(
    root: Path,
    *,
    classes: tuple[str, str, str] = ("mage", "thief", "warrior"),
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
                "entries:",
                *entries,
            ]
        ),
        encoding="utf-8",
    )
    return matrix_path
