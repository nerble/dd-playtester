from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from dd4tester.campaign import CampaignResult
from dd4tester.rotation import load_campaign_rotation, run_campaign_rotation


def test_active_character_rotation_loads_repository_campaigns() -> None:
    spec = load_campaign_rotation(Path("matrices/active-hero-rotation.yaml"))

    assert spec.target_level == 100
    assert [entry.entry_id for entry in spec.entries] == [
        "aeloria",
        "ararisa",
        "astrevo",
        "corararfen",
        "dorrik",
        "fenanallor",
        "kestrel",
        "praelarran",
        "serevian",
    ]
    assert all(entry.campaign_path.is_file() for entry in spec.entries)
    corararfen = next(entry for entry in spec.entries if entry.entry_id == "corararfen")
    assert corararfen.campaign_path == Path(
        "runs/heroes/validation/human-male-cleric-base/campaign.yaml"
    ).resolve()


def test_rotation_gives_each_campaign_one_turn_and_defers_blocked_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for entry_id in ("alpha", "beta", "gamma"):
        (tmp_path / f"{entry_id}.yaml").write_text("name: test\n", encoding="utf-8")
    config = tmp_path / "rotation.yaml"
    config.write_text(
        "name: Test rotation\n"
        "target_level: 100\n"
        "inter_character_delay: 0\n"
        "entries:\n"
        "  - id: alpha\n    campaign: alpha.yaml\n"
        "  - id: beta\n    campaign: beta.yaml\n"
        "  - id: gamma\n    campaign: gamma.yaml\n",
        encoding="utf-8",
    )
    planned_results = {
        "alpha": [
            CampaignResult(
                1,
                "ready",
                11,
                "checkpointed for the next verified segment",
                {"level": 4, "xp": 8000},
            ),
            CampaignResult(1, "success", 12, "target reached", {"level": 100}),
        ],
        "beta": [
            CampaignResult(2, "blocked", 21, "source frontier unavailable", {"level": 8})
        ],
        "gamma": [
            CampaignResult(
                3,
                "ready",
                31,
                "awaiting area reset",
                {"level": 12},
            )
        ],
    }
    calls: list[tuple[str, dict[str, object]]] = []

    async def fake_run_campaign(path: Path, **kwargs: object) -> CampaignResult:
        entry_id = path.stem
        calls.append((entry_id, kwargs))
        return planned_results[entry_id].pop(0)

    monkeypatch.setattr("dd4tester.rotation.run_campaign_file", fake_run_campaign)

    result = asyncio.run(
        run_campaign_rotation(
            config,
            rounds=3,
            max_segment_runtime=60,
        )
    )

    assert [entry_id for entry_id, _kwargs in calls] == [
        "alpha",
        "beta",
        "gamma",
        "alpha",
    ]
    assert all(
        kwargs["segments"] == 1
        and kwargs["reset_retries"] == 0
        and kwargs["max_segment_runtime"] == 60
        for _entry_id, kwargs in calls
    )
    assert result.completed_entry_ids == ("alpha",)
    assert result.deferred_entry_reasons == {
        "beta": "source frontier unavailable",
        "gamma": "awaiting area reset",
    }


def test_rotation_rejects_duplicate_entry_ids(tmp_path: Path) -> None:
    (tmp_path / "campaign.yaml").write_text("name: test\n", encoding="utf-8")
    config = tmp_path / "rotation.yaml"
    config.write_text(
        "entries:\n"
        "  - id: dorrik\n    campaign: campaign.yaml\n"
        "  - id: DORRIK\n    campaign: campaign.yaml\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate campaign rotation id"):
        load_campaign_rotation(config)
