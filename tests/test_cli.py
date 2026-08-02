import json
from pathlib import Path

import dd4tester.cli
from dd4tester.campaign import CampaignResult
from dd4tester.cli import main
from dd4tester.matrix import (
    MatrixCredentialResult,
    MatrixEntryResult,
    MatrixResult,
)
from dd4tester.money import MoneyLoopResult
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


def test_hero_prepare_only_builds_source_validated_campaign(tmp_path, capsys) -> None:
    source = tmp_path / "const.c"
    source.write_text(
        """
        const struct class_type class_table[MAX_CLASS] = {
            {"Mag", "Mage", APPLY_INT, 1, 3018, 95, 18, 6, 6, 9, TRUE,
             "Necromancer", "Warlock", "Nec", "Wlk", {-1, 3, 1, 1, -1}}
        };
        const struct sub_class_type sub_class_table[MAX_SUB_CLASS] = {
            {"Non", "None", APPLY_STR, FALSE},
            {"Nec", "Necromancer", APPLY_WIS, TRUE},
            {"Wlk", "Warlock", APPLY_STR, TRUE}
        };
        const struct race_struct race_table[MAX_RACE] = {
            {"None", "None", 0, 0, 0, 0, 0, 0, 0, 0, "NULL", "NULL", 0},
            {"Human", "Human", 0, 1, 0, 0, 0, 0, 0, 0,
             "Identify", "Detect Evil", CHAR_SIZE_MEDIUM}
        };
        """,
        encoding="utf-8",
    )
    source.with_name("comm.c").write_text(
        """
        case CON_GET_NEW_SEX:
            switch (argument[0]) {
            case 'm': ch->sex = SEX_MALE; break;
            case 'f': ch->sex = SEX_FEMALE; break;
            case 'n': ch->sex = SEX_NEUTRAL; break;
            }
            break;
        case CON_DISPLAY_CLASS:
        """,
        encoding="utf-8",
    )

    exit_code = main(
        [
            "hero",
            "--name",
            "Valora",
            "--race",
            "human",
            "--sex",
            "female",
            "--class",
            "mage",
            "--source",
            str(source),
            "--workspace",
            str(tmp_path / "heroes"),
            "--transport",
            "mudlet",
            "--mudlet-directory",
            str(tmp_path / "shared-mudlet"),
            "--prepare-only",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Character: Valora (human mage)" in captured.out
    assert "Prepared: new" in captured.out
    assert (tmp_path / "heroes" / "valora" / "campaign.yaml").is_file()
    profile = (tmp_path / "heroes" / "valora" / "character.yaml").read_text(
        encoding="utf-8"
    )
    assert 'transport: "mudlet"' in profile


def test_hero_command_accepts_reset_gated_ready_campaign(tmp_path, capsys, monkeypatch) -> None:
    captured_request: dict[str, object] = {}

    async def fake_hero(request, **kwargs):
        captured_request["request"] = request
        captured_request["options"] = kwargs
        prepared = type(
            "Prepared",
            (),
            {
                "character": type(
                    "Character",
                    (), {"name": "Valora", "race": "human", "character_class": "mage"},
                )(),
                "manifest_path": tmp_path / "hero.json",
                "profile_path": tmp_path / "character.yaml",
                "campaign_path": tmp_path / "campaign.yaml",
                "resumed": True,
            },
        )()
        result = CampaignResult(
            4,
            "ready",
            9,
            "mud-school-2-6 arena circuit was empty at level 3. "
            "Campaign checkpointed while awaiting the Mud School area reset.",
            {"level": 3},
        )
        return prepared, result

    monkeypatch.setattr(dd4tester.cli, "run_hero_request", fake_hero)

    exit_code = main(
        [
            "hero",
            "--race",
            "human",
            "--sex",
            "female",
            "--class",
            "mage",
            "--username",
            "Valora",
            "--password",
            "command-line-secret",
            "--target-level",
            "30",
        ]
    )

    assert exit_code == 0
    request = captured_request["request"]
    assert isinstance(request, dd4tester.cli.HeroRequest)
    assert (request.race, request.sex, request.character_class) == (
        "human",
        "female",
        "mage",
    )
    assert request.name == "Valora"
    assert captured_request["options"]["reset_retries"] is None
    assert captured_request["options"]["target_level"] == 30
    assert captured_request["options"]["password"] == "command-line-secret"
    captured = capsys.readouterr()
    assert "awaiting the Mud School area reset" in captured.out
    assert "command-line-secret" not in captured.out


def test_hero_command_rejects_conflicting_name_and_username(capsys) -> None:
    exit_code = main(
        [
            "hero",
            "--race",
            "human",
            "--class",
            "mage",
            "--name",
            "Valora",
            "--username",
            "Someoneelse",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "must identify the same DD4 character" in captured.err


def test_recover_runs_marks_orphaned_records(tmp_path, capsys) -> None:
    database, _transcript = _create_recorded_run(tmp_path)
    with RunStorage(database) as storage:
        storage.create_run(scenario_name="arena", scenario_path=tmp_path / "arena.yaml")
        campaign_id = storage.create_campaign(
            name="Ararisa to HERO",
            config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml",
            target_level=100,
        )
        storage.start_campaign_segment(
            campaign_id,
            phase="ambush-exterior-8-10",
            start_state={"name": "Ararisa", "level": 8},
        )

    exit_code = main(["recover-runs", "--database", str(database)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Marked 1 interrupted run(s) as failed." in captured.out
    assert (
        "Marked 1 interrupted campaign segment(s) across 1 campaign(s) as failed."
        in captured.out
    )
    with RunStorage(database) as storage:
        assert storage.get_campaign(campaign_id)["status"] == "failed"
        assert storage.list_campaign_segments(campaign_id)[0]["status"] == "failed"


def test_arena_research_passes_kill_limit_to_runner(tmp_path, capsys, monkeypatch) -> None:
    captured_args: dict[str, object] = {}

    async def run_arena(profile, *, target_level, kill_limit):
        captured_args.update(
            profile=profile,
            target_level=target_level,
            kill_limit=kill_limit,
        )
        return RunResult(1, "success", tmp_path / "run.jsonl", tmp_path / "runs.sqlite3", {})

    monkeypatch.setattr(dd4tester.cli, "run_arena_research_profile", run_arena)

    exit_code = main(
        ["arena-research", str(tmp_path / "character.yaml"), "--target-level", "7", "--kill-limit", "2"]
    )

    assert exit_code == 0
    assert captured_args["target_level"] == 7
    assert captured_args["kill_limit"] == 2


def test_money_loop_passes_level_trip_limit_and_source(tmp_path, capsys, monkeypatch) -> None:
    captured_args: dict[str, object] = {}
    profile = tmp_path / "character.yaml"
    source = tmp_path / "area"
    run = RunResult(
        8,
        "success",
        tmp_path / "run.jsonl",
        tmp_path / "runs.sqlite3",
        {},
    )

    async def run_money(profile_path, *, character_level, trip_limit, source_directory):
        captured_args.update(
            profile=profile_path,
            character_level=character_level,
            trip_limit=trip_limit,
            source_directory=source_directory,
        )
        return MoneyLoopResult((run,), run, run, ("Uburz",))

    monkeypatch.setattr(dd4tester.cli, "run_money_loop_profile", run_money)

    exit_code = main(
        [
            "money-loop",
            str(profile),
            "--level",
            "6",
            "--trips",
            "2",
            "--source",
            str(source),
        ]
    )

    assert exit_code == 0
    assert captured_args == {
        "profile": profile,
        "character_level": 6,
        "trip_limit": 2,
        "source_directory": source,
    }
    assert "Money loop completed runs: 8, 8, 8" in capsys.readouterr().out


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


def test_mudlet_bridge_command_generates_shared_files(tmp_path, capsys) -> None:
    directory = tmp_path / "mudlet-shared"

    exit_code = main(["mudlet-bridge", "--directory", str(directory)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert (directory / "dd4tester_bridge.lua").is_file()
    assert (directory / "commands.txt").is_file()
    assert (directory / "events.jsonl").is_file()
    assert "Mudlet script:" in captured.out


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

    async def fake_campaign(path: Path, **_kwargs) -> CampaignResult:
        assert path == config
        assert _kwargs["force_new"] is True
        assert _kwargs["segments"] == 1
        assert _kwargs["reset_retries"] is None
        assert _kwargs["max_segment_runtime"] is None
        return CampaignResult(4, "blocked", 9, "awaiting verified policy", {"level": 2})

    monkeypatch.setattr(dd4tester.cli, "run_campaign_file", fake_campaign)

    exit_code = main(["campaign", str(config), "--new"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Campaign 4 blocked" in captured.out
    assert "Checkpoint: 9" in captured.out
    assert "Level: 2" in captured.out


def test_campaign_command_passes_per_segment_runtime_cap(tmp_path, capsys, monkeypatch) -> None:
    config = tmp_path / "campaign.yaml"
    captured_options: dict[str, object] = {}

    async def fake_campaign(path: Path, **kwargs) -> CampaignResult:
        assert path == config
        captured_options.update(kwargs)
        return CampaignResult(4, "ready", 9, "checkpointed", {"level": 2})

    monkeypatch.setattr(dd4tester.cli, "run_campaign_file", fake_campaign)

    exit_code = main(
        ["campaign", str(config), "--max-segment-runtime", "180"]
    )

    assert exit_code == 0
    assert captured_options["max_segment_runtime"] == 180
    assert "Campaign 4 ready" in capsys.readouterr().out


def test_campaign_command_returns_success_for_ready_checkpoint(tmp_path, capsys, monkeypatch) -> None:
    config = tmp_path / "campaign.yaml"

    async def fake_campaign(path: Path, **_kwargs) -> CampaignResult:
        return CampaignResult(
            4,
            "ready",
            9,
            "mud-school-6-10 segment completed at level 6. "
            "Campaign checkpointed for the next verified segment.",
            {"level": 6},
        )

    monkeypatch.setattr(dd4tester.cli, "run_campaign_file", fake_campaign)

    exit_code = main(["campaign", str(config)])

    assert exit_code == 0
    assert "Campaign 4 ready" in capsys.readouterr().out


def test_campaign_command_returns_success_when_an_empty_area_is_reset_gated(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    config = tmp_path / "campaign.yaml"

    async def fake_campaign(path: Path, **_kwargs) -> CampaignResult:
        return CampaignResult(
            4,
            "ready",
            9,
            "mud-school-2-6 arena circuit was empty at level 3. "
            "Campaign checkpointed while awaiting the Mud School area reset.",
            {"level": 3},
        )

    monkeypatch.setattr(dd4tester.cli, "run_campaign_file", fake_campaign)

    exit_code = main(["campaign", str(config)])

    assert exit_code == 0
    assert "awaiting the Mud School area reset" in capsys.readouterr().out


def test_arena_research_command_runs_with_requested_target(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "level-two.yaml"
    transcript = tmp_path / "arena-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_arena_research(
        path: Path,
        *,
        target_level: int,
        kill_limit: int | None,
    ) -> RunResult:
        assert path == profile
        assert target_level == 3
        assert kill_limit is None
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


def test_rearm_command_runs_verified_weapon_recovery(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "rearm-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_rearm(path: Path) -> RunResult:
        assert path == profile
        return RunResult(16, "success", transcript, database, {"level": 13})

    monkeypatch.setattr(dd4tester.cli, "run_rearm_profile", fake_rearm)

    exit_code = main(["rearm", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 16 success" in captured.out
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
        consider_target: str | None = None,
        maximum_target_count: int = 1,
    ) -> RunResult:
        assert path == profile
        assert route == "moria"
        assert explore_direction is None
        assert explore_depth == 1
        assert attack_target is None
        assert consider_target is None
        assert maximum_target_count == 1
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
        consider_target: str | None = None,
        maximum_target_count: int = 1,
    ) -> RunResult:
        assert path == profile
        assert route == "moria"
        assert explore_direction == "north"
        assert explore_depth == 2
        assert attack_target is None
        assert consider_target is None
        assert maximum_target_count == 1
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


def test_fastwalk_research_command_can_consider_without_attacking(
    tmp_path, capsys, monkeypatch
) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "fastwalk-consider.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_fastwalk_research(
        path: Path,
        route: str,
        *,
        explore_direction: str | None = None,
        explore_depth: int = 1,
        attack_target: str | None = None,
        consider_target: str | None = None,
        maximum_target_count: int = 1,
        allowed_bystanders: tuple[str, ...] = (),
    ) -> RunResult:
        assert path == profile
        assert route == "gnome mine"
        assert explore_direction is None
        assert explore_depth == 1
        assert attack_target is None
        assert consider_target == "hobgoblin miner"
        assert maximum_target_count == 1
        assert allowed_bystanders == ("mine foreman",)
        return RunResult(17, "success", transcript, database, {"level": 7})

    monkeypatch.setattr(
        dd4tester.cli,
        "run_fastwalk_research_profile",
        fake_fastwalk_research,
    )

    exit_code = main(
        [
            "fastwalk-research",
            str(profile),
            "gnome mine",
            "--consider",
            "hobgoblin miner",
            "--allow-bystander",
            "mine foreman",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 17 success" in captured.out


def test_midennir_research_command_collects_large_sack(
    tmp_path, capsys, monkeypatch
) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "midennir-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_midennir_research(path: Path) -> RunResult:
        assert path == profile
        return RunResult(17, "success", transcript, database, {"level": 7})

    monkeypatch.setattr(
        dd4tester.cli,
        "run_midennir_research_profile",
        fake_midennir_research,
    )

    exit_code = main(["midennir-research", str(profile)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 17 success" in captured.out


def test_ambush_research_command_runs_exterior_circuit(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "ambush-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_ambush_research(
        path: Path,
        *,
        guard_probe: bool,
        vile_probe: bool,
        raider_probe: bool,
        horseman_probe: bool,
        vile_hunt: bool,
    ) -> RunResult:
        assert path == profile
        assert guard_probe is True
        assert vile_probe is False
        assert raider_probe is False
        assert horseman_probe is False
        assert vile_hunt is False
        return RunResult(18, "success", transcript, database, {"level": 9})

    monkeypatch.setattr(
        dd4tester.cli,
        "run_ambush_research_profile",
        fake_ambush_research,
    )

    exit_code = main(["ambush-research", str(profile), "--guard-probe"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Run 18 success" in captured.out
    assert f"Transcript: {transcript}" in captured.out


def test_ambush_research_command_selects_vile_goblin_probe(
    tmp_path,
    monkeypatch,
) -> None:
    profile = tmp_path / "character.yaml"

    async def fake_ambush_research(
        path: Path,
        *,
        guard_probe: bool,
        vile_probe: bool,
        raider_probe: bool,
        horseman_probe: bool,
        vile_hunt: bool,
    ) -> RunResult:
        assert path == profile
        assert guard_probe is False
        assert vile_probe is True
        assert raider_probe is False
        assert horseman_probe is False
        assert vile_hunt is False
        return RunResult(
            19,
            "success",
            tmp_path / "ambush-2.jsonl",
            tmp_path / "runs.sqlite3",
            {"level": 8},
        )

    monkeypatch.setattr(
        dd4tester.cli,
        "run_ambush_research_profile",
        fake_ambush_research,
    )

    assert main(["ambush-research", str(profile), "--vile-probe"]) == 0


def test_ambush_research_command_selects_raider_probe(
    tmp_path,
    monkeypatch,
) -> None:
    profile = tmp_path / "character.yaml"

    async def fake_ambush_research(
        path: Path,
        *,
        guard_probe: bool,
        vile_probe: bool,
        raider_probe: bool,
        horseman_probe: bool,
        vile_hunt: bool,
    ) -> RunResult:
        assert path == profile
        assert guard_probe is False
        assert vile_probe is False
        assert raider_probe is True
        assert horseman_probe is False
        assert vile_hunt is False
        return RunResult(
            20,
            "success",
            tmp_path / "ambush-raider.jsonl",
            tmp_path / "runs.sqlite3",
            {"level": 10},
        )

    monkeypatch.setattr(
        dd4tester.cli,
        "run_ambush_research_profile",
        fake_ambush_research,
    )

    assert main(["ambush-research", str(profile), "--raider-probe"]) == 0


def test_ambush_research_command_selects_bounded_raider_hunt(
    tmp_path,
    monkeypatch,
) -> None:
    profile = tmp_path / "character.yaml"

    async def fake_ambush_research(path: Path, **options: bool) -> RunResult:
        assert path == profile
        assert options == {
            "guard_probe": False,
            "vile_probe": False,
            "raider_probe": False,
            "raider_hunt": True,
            "horseman_probe": False,
            "vile_hunt": False,
        }
        return RunResult(
            21,
            "success",
            tmp_path / "ambush-raider-hunt.jsonl",
            tmp_path / "runs.sqlite3",
            {"level": 10},
        )

    monkeypatch.setattr(
        dd4tester.cli,
        "run_ambush_research_profile",
        fake_ambush_research,
    )

    assert main(["ambush-research", str(profile), "--raider-hunt"]) == 0


def test_ambush_research_command_selects_horseman_probe(
    tmp_path,
    monkeypatch,
) -> None:
    profile = tmp_path / "character.yaml"

    async def fake_ambush_research(
        path: Path,
        *,
        guard_probe: bool,
        vile_probe: bool,
        raider_probe: bool,
        horseman_probe: bool,
        vile_hunt: bool,
    ) -> RunResult:
        assert path == profile
        assert guard_probe is False
        assert vile_probe is False
        assert raider_probe is False
        assert horseman_probe is True
        assert vile_hunt is False
        return RunResult(
            20,
            "success",
            tmp_path / "ambush-horseman.jsonl",
            tmp_path / "runs.sqlite3",
            {"level": 9},
        )

    monkeypatch.setattr(
        dd4tester.cli,
        "run_ambush_research_profile",
        fake_ambush_research,
    )

    assert main(["ambush-research", str(profile), "--horseman-probe"]) == 0


def test_ambush_research_command_selects_bounded_vile_hunt(
    tmp_path,
    monkeypatch,
) -> None:
    profile = tmp_path / "character.yaml"

    async def fake_ambush_research(
        path: Path,
        *,
        guard_probe: bool,
        vile_probe: bool,
        raider_probe: bool,
        horseman_probe: bool,
        vile_hunt: bool,
    ) -> RunResult:
        assert path == profile
        assert guard_probe is False
        assert vile_probe is False
        assert raider_probe is False
        assert horseman_probe is False
        assert vile_hunt is True
        return RunResult(
            21,
            "success",
            tmp_path / "ambush-vile-hunt.jsonl",
            tmp_path / "runs.sqlite3",
            {"level": 9},
        )

    monkeypatch.setattr(
        dd4tester.cli,
        "run_ambush_research_profile",
        fake_ambush_research,
    )

    assert main(["ambush-research", str(profile), "--vile-hunt"]) == 0


def test_moria_research_command_runs_bounded_route(tmp_path, capsys, monkeypatch) -> None:
    profile = tmp_path / "character.yaml"
    transcript = tmp_path / "moria-1.jsonl"
    database = tmp_path / "runs.sqlite3"

    async def fake_moria_research(
        path: Path,
        *,
        depth: int,
        sanctuary_probe: bool,
        sanctuary_hunt: bool,
    ) -> RunResult:
        assert path == profile
        assert depth == 0
        assert sanctuary_probe is False
        assert sanctuary_hunt is False
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


def test_moria_research_command_selects_sanctuary_probe(
    tmp_path,
    monkeypatch,
) -> None:
    profile = tmp_path / "character.yaml"

    async def fake_moria_research(
        path: Path,
        *,
        depth: int,
        sanctuary_probe: bool,
        sanctuary_hunt: bool,
    ) -> RunResult:
        assert path == profile
        assert depth == 0
        assert sanctuary_probe is True
        assert sanctuary_hunt is False
        return RunResult(
            22,
            "success",
            tmp_path / "moria-sanctuary.jsonl",
            tmp_path / "runs.sqlite3",
            {"level": 9},
        )

    monkeypatch.setattr(
        dd4tester.cli,
        "run_moria_research_profile",
        fake_moria_research,
    )

    assert (
        main(["moria-research", str(profile), "--sanctuary-probe"])
        == 0
    )


def test_moria_research_command_selects_sanctuary_hunt(
    tmp_path,
    monkeypatch,
) -> None:
    profile = tmp_path / "character.yaml"

    async def fake_moria_research(
        path: Path,
        *,
        depth: int,
        sanctuary_probe: bool,
        sanctuary_hunt: bool,
    ) -> RunResult:
        assert path == profile
        assert depth == 0
        assert sanctuary_probe is False
        assert sanctuary_hunt is True
        return RunResult(
            23,
            "success",
            tmp_path / "moria-sanctuary-hunt.jsonl",
            tmp_path / "runs.sqlite3",
            {"level": 9},
        )

    monkeypatch.setattr(
        dd4tester.cli,
        "run_moria_research_profile",
        fake_moria_research,
    )

    assert main(["moria-research", str(profile), "--sanctuary-hunt"]) == 0


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
            "10",
            "--source",
            str(source),
            "--database",
            str(tmp_path / "missing.sqlite3"),
            "--include-xp-only",
            "--all-areas",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Current reboot: unknown" in captured.out
    assert "Character max HP: unknown" in captured.out
    assert "fuzzed_levels\tbase_hp\tpeak_round\troom" in captured.out
    assert "room_spawns\tspawn_limit\tboot_kills" in captured.out
    assert "autonomy_rejections" in captured.out
    assert "reject\t" in captured.out
    assert "the dangerous guard" in captured.out
    assert "reachable wanderer: a cellar rat L3" in captured.out
    assert "a cellar rat\t3\t1-5" not in captured.out


def test_show_hunt_candidates_ignores_hp_from_a_different_level(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    source = tmp_path / "area"
    source.mkdir()
    fixture = Path(__file__).parent / "fixtures" / "hunt_area.are"
    (source / "foundry.are").write_text(
        fixture.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    database = tmp_path / "runs.sqlite3"
    storage = RunStorage(database)
    run_id = storage.create_run(
        scenario_name="starter",
        scenario_path=Path("scenarios/starter.yaml"),
    )
    storage.record_state_snapshot(
        run_id,
        source_event_id=None,
        reason="prompt_seen",
        state={"name": "Ararisa", "level": 6, "max_hp": 136},
    )
    storage.finish_run(run_id, status="success")
    storage.close()
    captured_max_hp: list[int | None] = []
    original_rank = dd4tester.cli.rank_hunt_candidates

    def capture_rank(*args, **kwargs):
        captured_max_hp.append(kwargs["character_max_hp"])
        return original_rank(*args, **kwargs)

    monkeypatch.setattr(dd4tester.cli, "rank_hunt_candidates", capture_rank)

    exit_code = main(
        [
            "show-hunt-candidates",
            "--level",
            "20",
            "--source",
            str(source),
            "--database",
            str(database),
            "--include-xp-only",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured_max_hp == [None]
    assert "Character max HP: unknown" in captured.out


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


def test_matrix_cli_reports_each_character_without_hiding_incomplete_work(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    async def fake_run_matrix_file(*_args, **_kwargs):
        return MatrixResult(
            "Mage Thief Warrior",
            10,
            "incomplete",
            (
                MatrixEntryResult("mage", "Aeloria", "mage", 1, "success", 10, None),
                MatrixEntryResult(
                    "thief",
                    "Kestrel",
                    "thief",
                    2,
                    "blocked",
                    8,
                    "awaiting policy evidence",
                ),
                MatrixEntryResult("warrior", "Dorrik", "warrior", 3, "success", 10, None),
            ),
        )

    monkeypatch.setattr(dd4tester.cli, "run_matrix_file", fake_run_matrix_file)

    exit_code = main(
        [
            "matrix",
            str(tmp_path / "matrix.yaml"),
            "--rounds",
            "2",
            "--segments-per-character",
            "3",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Matrix: Mage Thief Warrior" in captured.out
    assert "mage\tAeloria\tmage\t10\tsuccess\t1\t-" in captured.out
    assert "thief\tKestrel\tthief\t8\tblocked\t2\tawaiting policy evidence" in captured.out
    assert "warrior\tDorrik\twarrior\t10\tsuccess\t3\t-" in captured.out


def test_configure_matrix_passwords_reports_status_without_secrets(
    tmp_path,
    capsys,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        dd4tester.cli,
        "provision_matrix_passwords",
        lambda _path: (
            MatrixCredentialResult("mage", "character:aeloria", "existing"),
            MatrixCredentialResult("thief", "character:kestrel", "generated"),
        ),
    )

    exit_code = main(
        ["configure-matrix-passwords", str(tmp_path / "matrix.yaml")]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "mage: existing credential character:aeloria" in captured.out
    assert "thief: generated credential character:kestrel" in captured.out
    assert "password" not in captured.out.casefold()


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


def test_show_policy_coverage_makes_unavailable_hero_bands_explicit(capsys) -> None:
    exit_code = main(
        [
            "show-policy-coverage",
            "--class",
            "thief",
            "--from-level",
            "12",
            "--to-level",
            "16",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "levels\tpolicy\tstatus\texecution" in captured.out
    assert "12\tfleshmonger-thief-rotation-research-12-13\tresearch" in captured.out
    assert (
        "16\tmirror-realm-watchman-probe-16-20\tresearch\t"
        "mirror-realm-watchman-research"
    ) in captured.out


def test_matrix_coverage_reports_legal_pair_gap(capsys) -> None:
    exit_code = main(["matrix-coverage", "matrices/level-10.yaml"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Legal race/class pairs: 225" in captured.out
    assert "Declared pairs: 3" in captured.out
    assert "Undeclared pairs: 222" in captured.out
    assert "Live-validated pairs at level 10:" in captured.out
    assert "Live-pending declared pairs:" in captured.out
    assert "entry\tlevel\tstatus\tcampaign" in captured.out


def test_show_prereqs_displays_bundled_skill_requirements(capsys) -> None:
    exit_code = main(["show-prereqs", "--class", "mage", "--skill", "fireball"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Skill: fireball" in captured.out
    assert "group evocation: 75%" in captured.out


def test_skill_analysis_displays_ranked_source_backed_class_value(capsys) -> None:
    exit_code = main(["skill-analysis", "--class", "psionic"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Class: psionic" in captured.out
    assert "Strategy:" in captured.out
    assert "Practice policy:" in captured.out
    assert "Highest leveling value:" in captured.out
    assert "Automation gaps:" in captured.out
    assert "Ordered leveling priorities:" in captured.out
    assert "telepathy disciplines" in captured.out
    assert "damage-gateway, automated" in captured.out
    assert "mind thrust 10%" in captured.out
    assert "psychic crush" in captured.out


def test_skill_analysis_supports_subclass_alias_and_priorities(capsys) -> None:
    exit_code = main(["skill-analysis", "--class", "bounty hunter"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Class: bounty hunter" in captured.out
    assert "assassinate" in captured.out
    assert "group stealth 85%" in captured.out


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
