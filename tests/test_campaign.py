import asyncio
from pathlib import Path

from dd4tester.campaign import (
    CampaignRunner,
    _run_policy_segment,
    load_campaign_spec,
    run_campaign_file,
)
from dd4tester.progression import policy_for
from dd4tester.runner import RunResult
from dd4tester.storage import RunStorage


def test_campaign_checkpoints_starter_segment_and_resumes_safely(tmp_path) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    calls: list[int] = []

    async def starter_segment(spec, profile_path: Path) -> RunResult:
        calls.append(spec.max_commands)
        return _record_segment_run(spec.database, profile_path, {"level": 2, "xp": 100})

    spec = load_campaign_spec(config_path)
    result = asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=starter_segment).run()
    )

    assert result.status == "blocked"
    assert result.state["level"] == 2
    assert "checkpointed for the next verified segment" in result.message
    assert calls == [250]

    with RunStorage(database) as storage:
        campaign = storage.get_campaign(result.campaign_id)
        segments = storage.list_campaign_segments(result.campaign_id)
        checkpoint = storage.get_latest_campaign_checkpoint(result.campaign_id)

    assert campaign["status"] == "blocked"
    assert len(segments) == 1
    assert segments[0]["phase"] == "starter-0-2"
    assert segments[0]["command_count"] == 1
    assert checkpoint["reason"] == "segment_complete"

    async def arena_segment(spec, profile_path: Path) -> RunResult:
        return _record_segment_run(spec.database, profile_path, {"level": 6, "xp": 100})

    resumed = asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=arena_segment).run()
    )

    assert resumed.campaign_id == result.campaign_id
    assert resumed.status == "blocked"
    assert "checkpointed for the next verified segment" in resumed.message


def test_campaign_completes_when_a_segment_reaches_target(tmp_path) -> None:
    config_path, database = _write_campaign_files(tmp_path, target_level=2)

    async def starter_segment(spec, profile_path: Path) -> RunResult:
        return _record_segment_run(spec.database, profile_path, {"level": 2, "xp": 100})

    result = asyncio.run(
        CampaignRunner(
            load_campaign_spec(config_path),
            config_path,
            segment_runner=starter_segment,
        ).run()
    )

    assert result.status == "success"
    assert result.message == "Target level 2 reached."
    with RunStorage(database) as storage:
        assert storage.get_campaign(result.campaign_id)["status"] == "success"


def test_campaign_resumes_from_newer_external_character_state(tmp_path) -> None:
    config_path, database = _write_campaign_files(tmp_path)

    async def segment(spec, profile_path: Path) -> RunResult:
        return _record_segment_run(
            spec.database,
            profile_path,
            {"level": 2, "xp": 100},
        )

    spec = load_campaign_spec(config_path)
    initial = asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=segment).run()
    )
    with RunStorage(database) as storage:
        run_id = storage.create_run(
            scenario_name="external:Campaignmage",
            scenario_path=config_path,
        )
        event_id = storage.record_event(
            run_id,
            kind="game_event",
            payload={"type": "progress_changed"},
        )
        storage.record_state_snapshot(
            run_id,
            source_event_id=event_id,
            reason="progress_changed",
            state={"name": "Campaignmage", "level": 7, "xp": 20_000},
        )
        storage.finish_run(run_id, status="success")

    resumed = asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=segment).run()
    )

    assert resumed.campaign_id == initial.campaign_id
    with RunStorage(database) as storage:
        segments = storage.list_campaign_segments(resumed.campaign_id)
    assert segments[-1]["phase"] == "midennir-goblin-7-8"


def test_campaign_selects_sack_phase_from_persisted_inventory(tmp_path) -> None:
    config_path, _database = _write_campaign_files(tmp_path)
    runner = CampaignRunner(load_campaign_spec(config_path), config_path)

    before = runner._policy_for_state(
        {"level": 8, "inventory": [[{"short_desc": "a big pot pie"}]]}
    )
    after = runner._policy_for_state(
        {"level": 8, "inventory": [[{"short_desc": "a large sack"}]]}
    )

    assert before.policy_id == "midennir-sack-8-10"
    assert after.policy_id == "midennir-goblin-8-10"


def test_midennir_campaign_hunt_allows_retryable_empty_spawn(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 7, "xp": 20_000})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy_for(7, "mage"),
        )
    )

    assert captured["fastwalk_attack_target"] == "goblin"
    assert captured["fastwalk_explore_direction"] == "east"
    assert captured["fastwalk_explore_depth"] == 1
    assert captured["fastwalk_train_before_departure"] is True
    assert captured["require_fastwalk_kill"] is False


def test_midennir_campaign_sack_requires_verified_invisibility(
    tmp_path,
    monkeypatch,
) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    spec = load_campaign_spec(config_path)
    captured: dict[str, object] = {}

    class FakeRunner:
        def __init__(self, character, profile_path, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return _record_segment_run(database, config_path, {"level": 8, "xp": 25_000})

    monkeypatch.setattr("dd4tester.campaign.StarterBotRunner", FakeRunner)

    asyncio.run(
        _run_policy_segment(
            spec.character,
            spec.character_profile,
            policy_for(8, "mage"),
        )
    )

    assert captured["fastwalk_train_before_departure"] is True
    assert captured["fastwalk_require_invisibility"] is True
    assert captured["allow_safe_fastwalk_abort"] is True
    assert captured["vault_required_free_weight"] == 60
    assert captured["vault_stow_items"] == (
        "sleeves",
        "vest",
        "cape",
        "belt",
        "bracer",
        "guards",
    )
    stops = captured["fastwalk_hunt_stops"]
    assert stops[0].required_items == ("large sack",)


def test_campaign_file_runs_multiple_ready_segments(tmp_path, monkeypatch) -> None:
    config_path, database = _write_campaign_files(tmp_path)
    calls = 0

    async def segment(spec, profile_path: Path) -> RunResult:
        nonlocal calls
        calls += 1
        return _record_segment_run(
            spec.database,
            profile_path,
            {"level": min(2, calls), "xp": calls * 100},
        )

    class TestRunner(CampaignRunner):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, segment_runner=segment, **kwargs)

    monkeypatch.setattr("dd4tester.campaign.CampaignRunner", TestRunner)

    result = asyncio.run(run_campaign_file(config_path, segments=2))

    assert result.status == "blocked"
    assert calls == 2
    with RunStorage(database) as storage:
        assert len(storage.list_campaign_segments(result.campaign_id)) == 2


def test_campaign_caps_segment_with_remaining_aggregate_budget(tmp_path) -> None:
    config_path, _database = _write_campaign_files(tmp_path, max_total_commands=7)
    requested_commands: list[int] = []

    async def starter_segment(spec, profile_path: Path) -> RunResult:
        requested_commands.append(spec.max_commands)
        return _record_segment_run(spec.database, profile_path, {"level": 2})

    asyncio.run(
        CampaignRunner(
            load_campaign_spec(config_path),
            config_path,
            segment_runner=starter_segment,
        ).run()
    )

    assert requested_commands == [7]


def test_campaign_stops_after_configured_stalled_segments(tmp_path) -> None:
    config_path, database = _write_campaign_files(tmp_path, max_stalled_segments=2)
    calls = 0

    async def starter_segment(spec, profile_path: Path) -> RunResult:
        nonlocal calls
        calls += 1
        return _record_segment_run(spec.database, profile_path, {"level": 1, "xp": 0})

    spec = load_campaign_spec(config_path)
    first = asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=starter_segment).run()
    )
    second = asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=starter_segment).run()
    )
    third = asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=starter_segment).run()
    )

    assert first.status == "blocked"
    assert second.status == "blocked"
    assert third.message == "Campaign stalled for 2 completed segment(s)."
    assert calls == 3
    with RunStorage(database) as storage:
        assert len(storage.list_campaign_segments(third.campaign_id)) == 3

    resumed = asyncio.run(
        CampaignRunner(spec, config_path, segment_runner=starter_segment).run()
    )
    assert resumed.message == "Campaign stalled for 2 completed segment(s)."
    assert calls == 3


def test_campaign_records_a_returned_failed_segment(tmp_path) -> None:
    config_path, database = _write_campaign_files(tmp_path)

    async def failed_segment(spec, profile_path: Path) -> RunResult:
        result = _record_segment_run(spec.database, profile_path, {"level": 1})
        return RunResult(
            result.run_id,
            "failed",
            result.transcript_path,
            result.database_path,
            result.final_state,
        )

    result = asyncio.run(
        CampaignRunner(
            load_campaign_spec(config_path),
            config_path,
            segment_runner=failed_segment,
        ).run()
    )

    assert result.status == "failed"
    with RunStorage(database) as storage:
        segment = storage.list_campaign_segments(result.campaign_id)[0]
        assert segment["status"] == "failed"
        assert segment["error"] == "starter segment returned status failed"


def _write_campaign_files(
    tmp_path: Path,
    *,
    target_level: int = 100,
    max_total_commands: int = 10_000,
    max_stalled_segments: int = 2,
) -> tuple[Path, Path]:
    database = tmp_path / "runs.sqlite3"
    profile_path = tmp_path / "character.yaml"
    profile_path.write_text(
        "\n".join(
            [
                "name: Campaignmage",
                "password_env: TEST_PASSWORD",
                "race: human",
                "gender: female",
                "class: mage",
                f"database: '{database.as_posix()}'",
                f"transcript_dir: '{(tmp_path / 'transcripts').as_posix()}'",
            ]
        ),
        encoding="utf-8",
    )
    config_path = tmp_path / "campaign.yaml"
    config_path.write_text(
        "\n".join(
            [
                "name: Campaignmage to HERO",
                "character_profile: character.yaml",
                f"target_level: {target_level}",
                "max_segments: 10",
                "max_total_runtime: 3600",
                f"max_total_commands: {max_total_commands}",
                f"max_stalled_segments: {max_stalled_segments}",
            ]
        ),
        encoding="utf-8",
    )
    return config_path, database


def _record_segment_run(
    database: Path,
    profile_path: Path,
    final_state: dict[str, int],
) -> RunResult:
    with RunStorage(database) as storage:
        run_id = storage.create_run(
            scenario_name="starter:Campaignmage",
            scenario_path=profile_path,
        )
        storage.record_event(run_id, kind="command", payload={"command": "look"})
        storage.finish_run(run_id, status="success")
    return RunResult(
        run_id=run_id,
        status="success",
        transcript_path=Path("transcripts/campaign.jsonl"),
        database_path=database,
        final_state=final_state,
    )
