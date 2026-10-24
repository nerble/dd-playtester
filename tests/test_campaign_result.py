from pathlib import Path
from types import SimpleNamespace

from dd4tester.campaign import (
    CampaignResult,
    _decorate_campaign_result,
)
from dd4tester.storage import RunStorage


def test_campaign_result_exposes_independent_outcomes() -> None:
    result = CampaignResult(
        7,
        "ready",
        None,
        "safe checkpoint",
        {"level": 39},
        execution_status="success",
        objective_outcome="not_achieved",
        safety_outcome="safe",
        target_outcome="not_achieved",
    )

    assert result.outcomes == {
        "execution": "success",
        "objective": "not_achieved",
        "safety": "safe",
    }
    assert result.objective_achieved is False
    assert result.ran_safely is True
    assert result.target_achieved is False


def test_campaign_result_decorates_from_the_checkpointed_segment(
    tmp_path: Path,
) -> None:
    database = tmp_path / "campaign.sqlite3"
    config_path = tmp_path / "campaign.yaml"
    profile_path = tmp_path / "character.yaml"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Dorrik to HERO",
            config_path=config_path,
            character_profile_path=profile_path,
            target_level=100,
        )
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="source-ranked-hunt",
            start_state={"level": 39, "xp": 1_000},
        )
        storage.finish_campaign_segment(
            segment_id,
            status="ready",
            run_id=None,
            end_state={"level": 39, "xp": 1_000},
            command_count=3,
            duration_seconds=1.5,
            execution_status="success",
            objective_outcome="not_achieved",
            safety_outcome="safe",
        )
        checkpoint_id = storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=segment_id,
            run_id=None,
            phase="source-ranked-hunt",
            reason="segment_complete",
            state={"level": 39, "xp": 1_000},
        )

    decorated = _decorate_campaign_result(
        CampaignResult(
            campaign_id,
            "ready",
            checkpoint_id,
            "checkpointed",
            {"level": 39, "xp": 1_000},
        ),
        SimpleNamespace(database=database, target_level=100),
    )

    assert decorated.outcomes == {
        "execution": "success",
        "objective": "not_achieved",
        "safety": "safe",
    }
    assert decorated.objective_achieved is False
    assert decorated.ran_safely is True
    assert decorated.target_outcome == "not_achieved"


def test_campaign_segment_safety_uses_cumulative_loss_across_connections(
    tmp_path: Path,
) -> None:
    database = tmp_path / "campaign.sqlite3"
    config_path = tmp_path / "campaign.yaml"
    profile_path = tmp_path / "character.yaml"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Dorrik to HERO",
            config_path=config_path,
            character_profile_path=profile_path,
            target_level=100,
        )
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="source-ranked-hunt",
            start_state={
                "level": 40,
                "xp": 1_000,
                "xp_loss_total": 1_060,
                "campaign_xp_loss_total": 10_000,
            },
        )
        storage.finish_campaign_segment(
            segment_id,
            status="success",
            run_id=None,
            end_state={
                "level": 40,
                "xp": 1_007,
                # The MUD repeats the last loss amount on this connection;
                # only the campaign total proves that a new loss occurred.
                "xp_loss_total": 1_060,
                "campaign_xp_loss_total": 11_060,
            },
            command_count=3,
            duration_seconds=1.5,
        )

        segment = storage.list_campaign_segments(campaign_id)[0]

    assert segment["safety_outcome"] == "loss"


def test_unlinked_checkpoint_does_not_reuse_an_older_objective(tmp_path: Path) -> None:
    database = tmp_path / "campaign.sqlite3"
    config_path = tmp_path / "campaign.yaml"
    profile_path = tmp_path / "character.yaml"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Dorrik to HERO",
            config_path=config_path,
            character_profile_path=profile_path,
            target_level=100,
        )
        old_segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="source-ranked-hunt",
            start_state={"level": 39, "xp": 1_000},
        )
        storage.finish_campaign_segment(
            old_segment_id,
            status="success",
            run_id=None,
            end_state={"level": 39, "xp": 2_000},
            command_count=4,
            duration_seconds=2.0,
            execution_status="success",
            objective_outcome="achieved",
            safety_outcome="safe",
        )
        checkpoint_id = storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=None,
            run_id=None,
            phase="source-ranked-hunt-unavailable-39",
            reason="awaiting_area_reset",
            state={"level": 39, "xp": 2_000, "dead": False},
        )

    decorated = _decorate_campaign_result(
        CampaignResult(
            campaign_id,
            "ready",
            checkpoint_id,
            "checkpointed while awaiting the field area reset",
            {"level": 39, "xp": 2_000, "dead": False},
        ),
        SimpleNamespace(database=database, target_level=100),
    )

    assert decorated.outcomes == {
        "execution": "success",
        "objective": "not_achieved",
        "safety": "safe",
    }
    assert decorated.target_outcome == "not_achieved"


def test_successful_target_result_marks_objective_achieved(tmp_path: Path) -> None:
    result = _decorate_campaign_result(
        CampaignResult(
            9,
            "success",
            None,
            "Target level 100 reached.",
            {"level": 100, "xp": 10_000},
        ),
        SimpleNamespace(
            database=tmp_path / "missing.sqlite3",
            target_level=100,
        ),
    )

    assert result.objective_achieved is True
    assert result.outcomes == {
        "execution": "success",
        "objective": "achieved",
        "safety": "unknown",
    }
    assert result.target_outcome == "achieved"
    assert result.target_achieved is True
