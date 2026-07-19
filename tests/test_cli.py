import json
from pathlib import Path

import dd4tester.cli
from dd4tester.campaign import CampaignResult
from dd4tester.cli import main
from dd4tester.runner import RunResult
from dd4tester.storage import RunStorage
from dd4tester.transcript import TranscriptRecorder


def test_show_runs_lists_existing_runs(tmp_path, capsys) -> None:
    database, _transcript = _create_recorded_run(tmp_path)

    exit_code = main(["show-runs", "--database", str(database), "--limit", "5"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert str(database.resolve()) in captured.out
    assert "id\tstatus\tscenario" in captured.out
    assert "login" in captured.out
    assert "success" in captured.out


def test_recover_runs_marks_orphaned_records(tmp_path, capsys) -> None:
    database, _transcript = _create_recorded_run(tmp_path)
    with RunStorage(database) as storage:
        storage.create_run(scenario_name="arena", scenario_path=tmp_path / "arena.yaml")

    exit_code = main(["recover-runs", "--database", str(database)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Marked 1 interrupted run(s) as failed." in captured.out


def test_show_sales_lists_recorded_proceeds(tmp_path, capsys) -> None:
    database, _transcript = _create_recorded_run(tmp_path)
    with RunStorage(database) as storage:
        storage.record_loot_sale(
            1,
            character_name="Ararisa",
            item_keyword="cap",
            item_description="an iron cap",
            shop_name="Leather Shop",
            shop_room_vnum="3035",
            offered_coins=11,
            sold_coins=11,
        )

    exit_code = main(
        ["show-sales", "--database", str(database), "--character", "Ararisa"]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "an iron cap" in captured.out
    assert "Total shown: 11 coins" in captured.out


def test_show_transcript_reads_run_id_from_database(tmp_path, capsys) -> None:
    database, transcript = _create_recorded_run(tmp_path)

    exit_code = main(["show-transcript", "1", "--database", str(database)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert str(transcript.resolve()) in captured.out
    assert "command" in captured.out
    assert '"command": "guest"' in captured.out


def test_show_transcript_reads_direct_path(tmp_path, capsys) -> None:
    _database, transcript = _create_recorded_run(tmp_path)

    exit_code = main(["show-transcript", str(transcript), "--raw"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out.splitlines()[0])["kind"] == "command"


def test_show_state_prints_latest_snapshot_and_history(tmp_path, capsys) -> None:
    database, _transcript = _create_recorded_run(tmp_path)

    exit_code = main(["show-state", "1", "--database", str(database)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "state revision 1" in captured.out
    assert '"room_name": "The Entrance"' in captured.out

    exit_code = main(
        ["show-state", "1", "--database", str(database), "--history"]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "snapshot\ttimestamp\trevision\treason" in captured.out
    assert "room_entered" in captured.out


def test_starter_command_runs_character_profile(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "starter.yaml"
    profile.write_text("name: Rulemage", encoding="utf-8")
    transcript = tmp_path / "starter-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_run(path: Path) -> RunResult:
        assert path == profile
        return RunResult(7, "success", transcript, database, {"level": 2})

    monkeypatch.setattr(dd4tester.cli, "run_starter_profile", fake_run)

    exit_code = main(["starter", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 7 success" in captured.out
    assert f"Transcript: {transcript}" in captured.out


def test_campaign_command_prints_checkpointed_status(tmp_path, capsys, monkeypatch) -> None:
    config = tmp_path / "campaign.yaml"

    async def fake_campaign(path: Path, *, force_new: bool) -> CampaignResult:
        assert path == config
        assert force_new is True
        return CampaignResult(4, "blocked", 9, "awaiting verified policy", {"level": 2})

    monkeypatch.setattr(dd4tester.cli, "run_campaign_file", fake_campaign)

    exit_code = main(["campaign", str(config), "--new"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Campaign 4 blocked" in captured.out
    assert "Checkpoint: 9" in captured.out
    assert "Level: 2" in captured.out


def test_arena_research_command_runs_with_requested_target(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "level-two.yaml"
    transcript = tmp_path / "arena-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_arena_research(path: Path, *, target_level: int) -> RunResult:
        assert path == profile
        assert target_level == 3
        return RunResult(8, "success", transcript, database, {"level": 3})

    monkeypatch.setattr(dd4tester.cli, "run_arena_research_profile", fake_arena_research)

    exit_code = main(["arena-research", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 8 success" in captured.out
    assert f"Transcript: {transcript}" in captured.out


def test_resupply_command_runs_bounded_recovery(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "resupply-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_resupply(path: Path) -> RunResult:
        assert path == profile
        return RunResult(9, "success", transcript, database, {"level": 4})

    monkeypatch.setattr(dd4tester.cli, "run_resupply_profile", fake_resupply)

    exit_code = main(["resupply", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 9 success" in captured.out
    assert f"Transcript: {transcript}" in captured.out


def test_restock_command_runs_city_provisioning(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "restock-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_restock(path: Path) -> RunResult:
        assert path == profile
        return RunResult(10, "success", transcript, database, {"level": 4})

    monkeypatch.setattr(dd4tester.cli, "run_restock_profile", fake_restock)

    exit_code = main(["restock", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 10 success" in captured.out
    assert f"Transcript: {transcript}" in captured.out


def test_guildmaster_research_command_runs_bounded_route(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "guildmaster-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_guildmaster_research(path: Path) -> RunResult:
        assert path == profile
        return RunResult(11, "success", transcript, database, {"level": 6})

    monkeypatch.setattr(
        dd4tester.cli,
        "run_guildmaster_research_profile",
        fake_guildmaster_research,
    )

    exit_code = main(["guildmaster-research", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 11 success" in captured.out
    assert f"Transcript: {transcript}" in captured.out


def test_magic_shop_research_command_runs_bounded_route(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "magic-shop-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_magic_shop_research(path: Path, *, buy_fly: bool) -> RunResult:
        assert path == profile
        assert buy_fly is False
        return RunResult(13, "success", transcript, database, {"level": 6})

    monkeypatch.setattr(
        dd4tester.cli,
        "run_magic_shop_research_profile",
        fake_magic_shop_research,
    )

    exit_code = main(["magic-shop-research", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 13 success" in captured.out
    assert f"Transcript: {transcript}" in captured.out


def test_magic_shop_research_command_can_buy_and_use_fly_potion(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "magic-shop-2.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_magic_shop_research(path: Path, *, buy_fly: bool) -> RunResult:
        assert path == profile
        assert buy_fly is True
        return RunResult(14, "success", transcript, database, {"level": 6})

    monkeypatch.setattr(
        dd4tester.cli,
        "run_magic_shop_research_profile",
        fake_magic_shop_research,
    )

    exit_code = main(["magic-shop-research", str(profile), "--buy-fly"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 14 success" in captured.out


def test_return_home_command_runs_safe_recall(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "return-home-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_return_home(path: Path) -> RunResult:
        assert path == profile
        return RunResult(15, "success", transcript, database, {"level": 6})

    monkeypatch.setattr(
        dd4tester.cli,
        "run_return_home_profile",
        fake_return_home,
    )

    exit_code = main(["return-home", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 15 success" in captured.out


def test_fastwalk_research_command_runs_named_route(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "fastwalk-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_fastwalk_research(
        path: Path,
        route: str,
        *,
        explore_direction: str | None = None,
        explore_depth: int = 1,
        attack_target: str | None = None,
    ) -> RunResult:
        assert path == profile
        assert route == "moria"
        assert explore_direction is None
        assert explore_depth == 1
        assert attack_target is None
        return RunResult(15, "success", transcript, database, {"level": 6})

    monkeypatch.setattr(
        dd4tester.cli,
        "run_fastwalk_research_profile",
        fake_fastwalk_research,
    )

    exit_code = main(["fastwalk-research", str(profile), "moria"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 15 success" in captured.out


def test_fastwalk_research_command_can_inspect_one_exit(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "fastwalk-2.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_fastwalk_research(
        path: Path,
        route: str,
        *,
        explore_direction: str | None = None,
        explore_depth: int = 1,
        attack_target: str | None = None,
    ) -> RunResult:
        assert path == profile
        assert route == "moria"
        assert explore_direction == "north"
        assert explore_depth == 2
        assert attack_target is None
        return RunResult(16, "success", transcript, database, {"level": 6})

    monkeypatch.setattr(
        dd4tester.cli,
        "run_fastwalk_research_profile",
        fake_fastwalk_research,
    )

    exit_code = main(
        [
            "fastwalk-research",
            str(profile),
            "moria",
            "--exit",
            "north",
            "--depth",
            "2",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 16 success" in captured.out


def test_moria_research_command_runs_bounded_route(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "moria-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_moria_research(path: Path, *, depth: int) -> RunResult:
        assert path == profile
        assert depth == 0
        return RunResult(12, "success", transcript, database, {"level": 6})

    monkeypatch.setattr(
        dd4tester.cli,
        "run_moria_research_profile",
        fake_moria_research,
    )

    exit_code = main(["moria-research", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 12 success" in captured.out
    assert f"Transcript: {transcript}" in captured.out


def test_show_fastwalks_filters_official_routes_by_level(capsys) -> None:
    exit_code = main(["show-fastwalks", "--level", "6"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "name\tlevels\tnotation\tcommands" in captured.out
    assert "ambush\t6-16\t6s" in captured.out
    assert "moria\t5-15\t2s6e8n" in captured.out


def test_show_hunt_candidates_reports_source_risk_and_spawn_limits(
    tmp_path,
    capsys,
) -> None:
    source = tmp_path / "area"
    source.mkdir()
    fixture = Path(__file__).parent / "fixtures" / "hunt_area.are"
    (source / "foundry.are").write_text(
        fixture.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "show-hunt-candidates",
            "--level",
            "6",
            "--source",
            str(source),
            "--database",
            str(tmp_path / "missing.sqlite3"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Current reboot: unknown" in captured.out
    assert "room_spawns\tinstance_limit\tboot_kills" in captured.out
    assert "reject\t" in captured.out
    assert "a cellar rat" in captured.out
    assert "route: the dangerous guard L8 in 3002" in captured.out


def test_configure_login_command_uses_named_credential(capsys, monkeypatch) -> None:
    configured: list[str] = []
    monkeypatch.setattr(
        dd4tester.cli,
        "configure_login",
        lambda name: configured.append(name),
    )

    exit_code = main(["configure-login", "--credential-name", "research-login"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert configured == ["research-login"]
    assert "Stored login credential: research-login" in captured.out


def test_configure_character_password_uses_profile_credential(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "character.yaml"
    configured: list[str] = []

    monkeypatch.setattr(
        dd4tester.cli,
        "load_character_spec",
        lambda _path: type("Spec", (), {"credential_name": "character:rulemira"})(),
    )
    monkeypatch.setattr(
        dd4tester.cli,
        "configure_character_password",
        lambda name: configured.append(name),
    )

    exit_code = main(["configure-character-password", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert configured == ["character:rulemira"]
    assert "Stored character password credential: character:rulemira" in captured.out


def test_show_campaign_prints_checkpoint_and_segments(tmp_path, capsys) -> None:
    database = tmp_path / "runs.sqlite3"
    with RunStorage(database) as storage:
        campaign_id = storage.create_campaign(
            name="Rulemage to HERO",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=100,
        )
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase="starter",
            start_state={"level": 1},
        )
        storage.finish_campaign_segment(
            segment_id,
            status="success",
            run_id=7,
            end_state={"level": 2},
            command_count=42,
            duration_seconds=12.5,
        )
        storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=segment_id,
            run_id=7,
            phase="starter",
            reason="segment_complete",
            state={"level": 2},
        )
        storage.finish_campaign(
            campaign_id,
            status="blocked",
            error="awaiting verified policy",
        )

    exit_code = main(["show-campaign", str(campaign_id), "--database", str(database)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Campaign 1: Rulemage to HERO" in captured.out
    assert "Checkpoint 1: starter (segment_complete), level 2" in captured.out
    assert "1\tstarter\tsuccess\t7\t42\t12.5s\t-" in captured.out


def test_show_policies_displays_evidence_and_practice_candidate(capsys) -> None:
    exit_code = main(["show-policies", "--level", "2", "--class", "mage"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Policy: mud-school-2-6" in captured.out
    assert "Status: verified" in captured.out
    assert "Practice candidate: magic missile" in captured.out
    assert "Live run 56" in captured.out


def test_show_prereqs_displays_bundled_skill_requirements(capsys) -> None:
    exit_code = main(["show-prereqs", "--class", "mage", "--skill", "fireball"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Skill: fireball" in captured.out
    assert "group evocation: 75%" in captured.out


def _create_recorded_run(tmp_path) -> tuple[Path, Path]:
    database = tmp_path / "runs.sqlite3"
    storage = RunStorage(database)
    run_id = storage.create_run(scenario_name="login", scenario_path=Path("scenarios/login.yaml"))
    recorder = TranscriptRecorder.create(tmp_path / "transcripts", scenario_name="login", run_id=run_id)
    storage.set_transcript_path(run_id, recorder.path)
    event = recorder.record("command", {"command": "guest"})
    source_event_id = storage.record_event(
        run_id,
        kind=event.kind,
        payload=event.payload,
        timestamp=event.timestamp,
    )
    storage.record_state_snapshot(
        run_id,
        source_event_id=source_event_id,
        reason="room_entered",
        state={
            "schema_version": 1,
            "revision": 1,
            "level": 2,
            "hp": 60,
            "max_hp": 60,
            "room_name": "The Entrance",
        },
        timestamp=event.timestamp,
    )
    storage.finish_run(run_id, status="success")
    transcript_path = recorder.path
    recorder.close()
    storage.close()
    return database, transcript_path
