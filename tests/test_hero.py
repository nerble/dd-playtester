import asyncio
import json
import os
import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from dd4tester.campaign import CampaignResult, load_campaign_spec
from dd4tester.character import load_character_spec
from dd4tester.dd4_catalog import ClassOption, SubclassOption, parse_character_catalog
from dd4tester.hero import (
    HeroRequest,
    load_existing_hero_request,
    prepare_hero_request,
    run_hero_request,
)


SOURCE = r'''
const struct class_type class_table[MAX_CLASS] =
{
    {"Mag", "Mage", APPLY_INT, 1, 3018, 95, 18, 6, 6, 9, TRUE,
     "Necromancer", "Warlock", "Nec", "Wlk", {-1, 3, 1, 1, -1}},
    {"War", "Warrior", APPLY_STR, 1, 3022, 85, 18, 0, 12, 15, FALSE,
     "Thug", "Knight", "Thg", "Kni", {3, -1, -2, 1, 2}}
};
const struct sub_class_type sub_class_table[MAX_SUB_CLASS] =
{
    {"Non", "None", APPLY_STR, FALSE},
    {"Nec", "Necromancer", APPLY_WIS, TRUE},
    {"Wlk", "Warlock", APPLY_STR, TRUE},
    {"Thg", "Thug", APPLY_CON, FALSE},
    {"Kni", "Knight", APPLY_WIS, TRUE}
};
const struct race_struct race_table[MAX_RACE] =
{
    {"None", "None", 0, 0, 0, 0, 0, 0, 0, 0, "NULL", "NULL", 0},
    {"Human", "Human", 0, 1, 0, 0, 0, 0, 0, 0,
     "Identify", "Detect Evil", CHAR_SIZE_MEDIUM},
    {"Elf", "Elf", -2, 2, 1, 1, -1, -20, 20, 10,
     "Infravision", "Refresh", CHAR_SIZE_MEDIUM}
};
'''


def test_hero_uses_segment_budget_for_default_reset_retries(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}
    prepared = type(
        "Prepared",
        (),
        {
            "campaign_path": tmp_path / "campaign.yaml",
            "resumed": True,
            "character": type(
                "Character",
                (),
                {"password_env": "DD4_VALORA_PASSWORD"},
            )(),
        },
    )()

    async def fake_campaign(path, **options):
        captured["path"] = path
        captured.update(options)
        return CampaignResult(
            1,
            "ready",
            2,
            "Campaign checkpointed while awaiting the field area reset.",
            {"level": 8},
        )

    monkeypatch.setattr(
        "dd4tester.hero.prepare_hero_request",
        lambda request, **options: prepared,
    )
    monkeypatch.setattr("dd4tester.hero.run_campaign_file", fake_campaign)

    _prepared, result = asyncio.run(
        run_hero_request(
            HeroRequest(
                name="Valora",
                race="human",
                sex="female",
                character_class="mage",
                ),
                workspace=tmp_path / "heroes",
                segments=17,
                password="test-password",
            )
    )

    assert result.status == "ready"
    assert captured["segments"] == 17
    assert captured["reset_retries"] == 17
    assert captured["retry_stalled"] is False


def test_hero_forwards_progress_callback(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}
    prepared = type(
        "Prepared",
        (),
        {
            "campaign_path": tmp_path / "campaign.yaml",
            "resumed": True,
            "character": type(
                "Character",
                (),
                {"password_env": "DD4_VALORA_PASSWORD"},
            )(),
        },
    )()

    async def fake_campaign(path, **options):
        captured["path"] = path
        captured.update(options)
        return CampaignResult(1, "ready", 2, "checkpoint", {"level": 8})

    monkeypatch.setattr(
        "dd4tester.hero.prepare_hero_request",
        lambda request, **options: prepared,
    )
    monkeypatch.setattr("dd4tester.hero.run_campaign_file", fake_campaign)

    progress = lambda _message: None
    asyncio.run(
        run_hero_request(
            HeroRequest(
                name="Valora",
                race="human",
                sex="female",
                character_class="mage",
            ),
            workspace=tmp_path / "heroes",
            segments=1,
            progress_callback=progress,
            password="test-password",
        )
    )

    assert captured["progress_callback"] is progress


def test_hero_forwards_explicit_retry_stalled_rotation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}
    prepared = type(
        "Prepared",
        (),
        {
            "campaign_path": tmp_path / "campaign.yaml",
            "resumed": True,
            "character": type(
                "Character",
                (),
                {"password_env": "DD4_VALORA_PASSWORD"},
            )(),
        },
    )()

    async def fake_campaign(path, **options):
        captured.update(options)
        return CampaignResult(1, "ready", 2, "checkpoint", {"level": 17})

    monkeypatch.setattr(
        "dd4tester.hero.prepare_hero_request",
        lambda request, **options: prepared,
    )
    monkeypatch.setattr("dd4tester.hero.run_campaign_file", fake_campaign)

    asyncio.run(
        run_hero_request(
            HeroRequest(
                name="Valora",
                race="human",
                sex="female",
                character_class="mage",
            ),
                workspace=tmp_path / "heroes",
                segments=1,
                retry_stalled=True,
                password="test-password",
            )
    )

    assert captured["retry_stalled"] is True


def test_hero_disables_default_reset_retries_for_bounded_runs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}
    prepared = type(
        "Prepared",
        (),
        {
            "campaign_path": tmp_path / "campaign.yaml",
            "resumed": True,
            "character": type(
                "Character",
                (),
                {"password_env": "DD4_VALORA_PASSWORD"},
            )(),
        },
    )()

    async def fake_campaign(path, **options):
        captured.update(options)
        return CampaignResult(
            1,
            "ready",
            2,
            "Campaign checkpointed while awaiting the field area reset.",
            {"level": 8},
        )

    monkeypatch.setattr(
        "dd4tester.hero.prepare_hero_request",
        lambda request, **options: prepared,
    )
    monkeypatch.setattr("dd4tester.hero.run_campaign_file", fake_campaign)

    asyncio.run(
        run_hero_request(
            HeroRequest(
                name="Valora",
                race="human",
                sex="female",
                character_class="mage",
            ),
                workspace=tmp_path / "heroes",
                segments=17,
                max_segment_runtime=180,
                password="test-password",
            )
    )

    assert captured["segments"] == 17
    assert captured["reset_retries"] == 0


def test_hero_uses_plaintext_password_only_for_campaign_process(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}
    prepared = type(
        "Prepared",
        (),
        {
            "campaign_path": tmp_path / "campaign.yaml",
            "resumed": True,
            "character": type(
                "Character",
                (),
                {"password_env": "DD4_VALORA_PASSWORD"},
            )(),
        },
    )()

    def fake_prepare(request, **options):
        captured["prepare_options"] = options
        return prepared

    async def fake_campaign(path, **options):
        captured["campaign_password"] = os.environ.get("DD4_VALORA_PASSWORD")
        return CampaignResult(1, "ready", 2, "checkpoint", {"level": 15})

    monkeypatch.setattr("dd4tester.hero.prepare_hero_request", fake_prepare)
    monkeypatch.setattr("dd4tester.hero.run_campaign_file", fake_campaign)
    monkeypatch.setenv("DD4_VALORA_PASSWORD", "previous-secret")

    asyncio.run(
        run_hero_request(
            HeroRequest(
                name="Valora",
                race="human",
                sex="female",
                character_class="mage",
            ),
            workspace=tmp_path / "heroes",
            target_level=30,
            password="command-line-secret",
        )
    )

    assert captured["prepare_options"]["target_level"] == 30
    assert captured["campaign_password"] == "command-line-secret"
    assert os.environ["DD4_VALORA_PASSWORD"] == "previous-secret"


def test_hero_can_remember_plaintext_password_for_checkpoint_resume(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}
    prepared = type(
        "Prepared",
        (object,),
        {
            "campaign_path": tmp_path / "campaign.yaml",
            "character": type(
                "Character",
                (object,),
                {
                    "password_env": "DD4_VALORA_PASSWORD",
                    "credential_name": "character:valora",
                },
            )(),
        },
    )()

    def fake_prepare(request, **options):
        return prepared

    async def fake_campaign(path, **options):
        return CampaignResult(1, "ready", 2, "checkpoint", {"level": 2})

    def fake_save(credential_name: str, password: str) -> None:
        captured["credential_name"] = credential_name
        captured["password"] = password

    monkeypatch.setattr("dd4tester.hero.prepare_hero_request", fake_prepare)
    monkeypatch.setattr("dd4tester.hero.run_campaign_file", fake_campaign)
    monkeypatch.setattr("dd4tester.hero.save_character_password", fake_save)

    asyncio.run(
        run_hero_request(
            HeroRequest(
                name="Valora",
                race="human",
                sex="female",
                character_class="mage",
            ),
            workspace=tmp_path / "heroes",
            password="command-line-secret",
            remember_password=True,
        )
    )

    assert captured == {
        "credential_name": "character:valora",
        "password": "command-line-secret",
    }


def test_new_hero_generates_and_stores_a_password_without_logging_it(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}
    prepared = type(
        "Prepared",
        (),
        {
            "campaign_path": tmp_path / "campaign.yaml",
            "resumed": False,
            "character": type(
                "Character",
                (),
                {
                    "password_env": "DD4_VALORA_PASSWORD",
                    "credential_name": "character:valora",
                },
            )(),
        },
    )()

    def fake_prepare(request, **options):
        return prepared

    def fake_save(credential_name: str, password: str) -> None:
        captured["credential_name"] = credential_name
        captured["stored_password"] = password

    async def fake_campaign(path, **options):
        captured["campaign_password"] = os.environ.get("DD4_VALORA_PASSWORD")
        return CampaignResult(1, "ready", 2, "checkpoint", {"level": 2})

    monkeypatch.setattr("dd4tester.hero.prepare_hero_request", fake_prepare)
    async def no_stored_password(_credential_name: str) -> str | None:
        return None

    monkeypatch.setattr(
        "dd4tester.hero._load_character_password_with_timeout",
        no_stored_password,
    )
    monkeypatch.setattr("dd4tester.hero.save_character_password", fake_save)
    monkeypatch.setattr("dd4tester.hero.run_campaign_file", fake_campaign)

    asyncio.run(
        run_hero_request(
            HeroRequest(
                name="Valora",
                race="human",
                sex="female",
                character_class="mage",
            ),
            workspace=tmp_path / "heroes",
        )
    )

    stored_password = captured["stored_password"]
    assert captured["credential_name"] == "character:valora"
    assert captured["campaign_password"] == stored_password
    assert isinstance(stored_password, str)
    assert len(stored_password) == 24
    assert stored_password.isalnum()
    assert os.environ.get("DD4_VALORA_PASSWORD") is None


def test_prepared_but_unstarted_hero_generates_its_first_password(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}
    prepared = type(
        "Prepared",
        (),
        {
            "campaign_path": tmp_path / "campaign.yaml",
            "resumed": True,
            "character": type(
                "Character",
                (),
                {
                    "password_env": "DD4_VALORA_PASSWORD",
                    "credential_name": "character:valora",
                    "database": tmp_path / "runs.sqlite3",
                },
            )(),
        },
    )()

    def fake_save(credential_name: str, password: str) -> None:
        captured["credential_name"] = credential_name
        captured["stored_password"] = password

    async def no_stored_password(_credential_name: str) -> str | None:
        return None

    async def fake_campaign(path, **options):
        captured["campaign_password"] = os.environ.get("DD4_VALORA_PASSWORD")
        return CampaignResult(1, "ready", 2, "checkpoint", {"level": 2})

    monkeypatch.setattr(
        "dd4tester.hero.prepare_hero_request",
        lambda request, **options: prepared,
    )
    monkeypatch.setattr(
        "dd4tester.hero._load_character_password_with_timeout",
        no_stored_password,
    )
    monkeypatch.setattr("dd4tester.hero.save_character_password", fake_save)
    monkeypatch.setattr("dd4tester.hero.run_campaign_file", fake_campaign)

    asyncio.run(
        run_hero_request(
            HeroRequest(
                name="Valora",
                race="human",
                sex="female",
                character_class="mage",
            ),
            workspace=tmp_path / "heroes",
        )
    )

    assert captured["credential_name"] == "character:valora"
    assert captured["campaign_password"] == captured["stored_password"]


def test_prepared_hero_with_campaign_stays_strict_about_missing_password(
    tmp_path: Path,
    monkeypatch,
) -> None:
    database = tmp_path / "runs.sqlite3"
    campaign_path = (tmp_path / "campaign.yaml").resolve()
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE campaigns (config_path TEXT NOT NULL)")
        connection.execute(
            "INSERT INTO campaigns (config_path) VALUES (?)",
            (str(campaign_path),),
        )
    prepared = type(
        "Prepared",
        (),
        {
            "campaign_path": campaign_path,
            "resumed": True,
            "character": type(
                "Character",
                (),
                {
                    "name": "Valora",
                    "password_env": "DD4_VALORA_PASSWORD",
                    "credential_name": "character:valora",
                    "database": database,
                },
            )(),
        },
    )()

    async def no_stored_password(_credential_name: str) -> str | None:
        return None

    monkeypatch.setattr(
        "dd4tester.hero.prepare_hero_request",
        lambda request, **options: prepared,
    )
    monkeypatch.setattr(
        "dd4tester.hero._load_character_password_with_timeout",
        no_stored_password,
    )

    with pytest.raises(RuntimeError, match="no stored password"):
        asyncio.run(
            run_hero_request(
                HeroRequest(
                    name="Valora",
                    race="human",
                    sex="female",
                    character_class="mage",
                ),
                workspace=tmp_path / "heroes",
            )
        )


def test_existing_character_password_is_reused_before_generation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}
    prepared = type(
        "Prepared",
        (),
        {
            "campaign_path": tmp_path / "campaign.yaml",
            "resumed": False,
            "character": type(
                "Character",
                (),
                {
                    "password_env": "DD4_VALORA_PASSWORD",
                    "credential_name": "character:valora",
                },
            )(),
        },
    )()

    async def fake_campaign(path, **options):
        captured["campaign_password"] = os.environ.get("DD4_VALORA_PASSWORD")
        return CampaignResult(1, "ready", 2, "checkpoint", {"level": 15})

    async def stored_password(_credential_name: str) -> str:
        return "existing-secret"

    def unexpected_save(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("an existing character password must not be replaced")

    monkeypatch.setattr(
        "dd4tester.hero.prepare_hero_request",
        lambda request, **options: prepared,
    )
    monkeypatch.setattr(
        "dd4tester.hero._load_character_password_with_timeout",
        stored_password,
    )
    monkeypatch.setattr("dd4tester.hero.save_character_password", unexpected_save)
    monkeypatch.setattr("dd4tester.hero.run_campaign_file", fake_campaign)

    asyncio.run(
        run_hero_request(
            HeroRequest(
                name="Valora",
                race="human",
                sex="female",
                character_class="mage",
            ),
            workspace=tmp_path / "heroes",
        )
    )

    assert captured["campaign_password"] == "existing-secret"


def test_resumed_hero_reuses_stored_password_after_process_restart(
    tmp_path: Path,
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}
    prepared = type(
        "Prepared",
        (),
        {
            "campaign_path": tmp_path / "campaign.yaml",
            "resumed": True,
            "character": type(
                "Character",
                (),
                {
                    "name": "Valora",
                    "password_env": "DD4_VALORA_PASSWORD",
                    "credential_name": "character:valora",
                },
            )(),
        },
    )()

    async def stored_password(_credential_name: str) -> str:
        return "resume-secret"

    async def fake_campaign(path, **options):
        captured["campaign_password"] = os.environ.get("DD4_VALORA_PASSWORD")
        return CampaignResult(1, "ready", 2, "checkpoint", {"level": 15})

    monkeypatch.delenv("DD4_VALORA_PASSWORD", raising=False)
    monkeypatch.setattr(
        "dd4tester.hero.prepare_hero_request",
        lambda request, **options: prepared,
    )
    monkeypatch.setattr(
        "dd4tester.hero._load_character_password_with_timeout",
        stored_password,
    )
    monkeypatch.setattr("dd4tester.hero.run_campaign_file", fake_campaign)

    asyncio.run(
        run_hero_request(
            HeroRequest(
                name="Valora",
                race="human",
                sex="female",
                character_class="mage",
            ),
            workspace=tmp_path / "heroes",
        )
    )

    assert captured["campaign_password"] == "resume-secret"
    assert os.environ.get("DD4_VALORA_PASSWORD") is None


def test_prepare_hero_request_writes_resumable_secret_free_configuration(
    tmp_path: Path,
) -> None:
    catalog = parse_character_catalog(SOURCE, source="fixture")
    request = HeroRequest(
        name="Valora",
        race="human",
        sex="female",
        character_class="mage",
        subclass="warlock",
        personality="dryly funny, patient, and fascinated by old mechanisms",
    )

    prepared = prepare_hero_request(
        request,
        catalog=catalog,
        workspace=tmp_path / "heroes",
    )

    assert not prepared.resumed
    assert prepared.character.name == "Valora"
    assert prepared.character.subclass == "warlock"
    assert prepared.character.personality == request.personality
    assert "dryly funny" in prepared.character.description
    loaded_profile = load_character_spec(prepared.profile_path)
    assert loaded_profile.title == prepared.character.title
    assert loaded_profile.description == prepared.character.description
    assert loaded_profile.personality == request.personality
    assert load_campaign_spec(prepared.campaign_path).target_level == 100
    manifest_text = prepared.manifest_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_text)
    assert manifest["coverage_dimensions"] == ["race", "class", "subclass"]
    assert manifest["cosmetic_dimensions"] == ["sex"]
    assert "password" not in manifest_text.casefold()

    resumed = prepare_hero_request(
        request,
        catalog=catalog,
        workspace=tmp_path / "heroes",
    )
    assert resumed.resumed
    assert resumed.directory == prepared.directory
    assert resumed.character.description == prepared.character.description
    assert resumed.character.personality == request.personality

    resumed_without_optional_identity = prepare_hero_request(
        HeroRequest(
            name="Valora",
            race="human",
            sex="female",
            character_class="mage",
        ),
        catalog=catalog,
        workspace=tmp_path / "heroes",
    )
    assert resumed_without_optional_identity.resumed
    assert resumed_without_optional_identity.request.subclass == "warlock"
    assert (
        resumed_without_optional_identity.request.personality
        == request.personality
    )


def test_prepare_hero_request_pins_the_selected_source_area_directory(
    tmp_path: Path,
) -> None:
    catalog = parse_character_catalog(SOURCE, source="fixture")
    source_root = tmp_path / "dd4" / "server"
    source_dir = source_root / "src"
    area_dir = source_root / "area"
    source_dir.mkdir(parents=True)
    area_dir.mkdir()
    const_path = source_dir / "const.c"
    const_path.write_text(SOURCE, encoding="utf-8")

    prepared = prepare_hero_request(
        HeroRequest(
            name="Valora",
            race="human",
            sex="female",
            character_class="mage",
        ),
        catalog=catalog,
        source=const_path,
        workspace=tmp_path / "heroes",
    )

    campaign = load_campaign_spec(prepared.campaign_path)
    assert campaign.source_directory == area_dir.resolve()
    manifest = json.loads(prepared.manifest_path.read_text(encoding="utf-8"))
    assert manifest["catalog"]["source_directory"] == str(area_dir.resolve())


def test_prepare_hero_request_updates_resumed_level_goal(tmp_path: Path) -> None:
    catalog = parse_character_catalog(SOURCE, source="fixture")
    request = HeroRequest(
        name="Valora",
        race="human",
        sex="female",
        character_class="mage",
    )
    prepared = prepare_hero_request(
        request,
        catalog=catalog,
        workspace=tmp_path / "heroes",
        target_level=30,
    )
    assert load_campaign_spec(prepared.campaign_path).target_level == 30

    resumed = prepare_hero_request(
        request,
        catalog=catalog,
        workspace=tmp_path / "heroes",
        target_level=40,
    )

    assert resumed.resumed
    assert load_campaign_spec(resumed.campaign_path).target_level == 40
    assert "password" not in resumed.manifest_path.read_text(
        encoding="utf-8"
    ).casefold()

    shortened = prepare_hero_request(
        request,
        catalog=catalog,
        workspace=tmp_path / "heroes",
        target_level=20,
    )
    assert shortened.resumed
    assert load_campaign_spec(shortened.campaign_path).target_level == 40


def test_named_resume_finds_a_manifest_inside_a_matrix_workspace(
    tmp_path: Path,
) -> None:
    catalog = parse_character_catalog(SOURCE, source="fixture")
    request = HeroRequest(
        name="Corararfen",
        race="human",
        sex="male",
        character_class="warrior",
    )
    nested_workspace = tmp_path / "heroes" / "validation"
    first = prepare_hero_request(
        request,
        catalog=catalog,
        workspace=nested_workspace,
    )

    loaded = load_existing_hero_request(
        "Corararfen",
        workspace=tmp_path / "heroes",
    )
    resumed = prepare_hero_request(
        request,
        catalog=catalog,
        workspace=tmp_path / "heroes",
        target_level=30,
    )

    assert loaded.race == "human"
    assert loaded.character_class == "warrior"
    assert resumed.resumed
    assert resumed.directory == first.directory
    assert load_campaign_spec(resumed.campaign_path).target_level == 100


def test_named_resume_prefers_the_longest_duplicate_campaign_horizon(
    tmp_path: Path,
) -> None:
    catalog = parse_character_catalog(SOURCE, source="fixture")
    request = HeroRequest(
        name="Corararfen",
        race="human",
        sex="male",
        character_class="warrior",
    )
    short_workspace = tmp_path / "heroes" / "validation-all"
    long_workspace = tmp_path / "heroes" / "validation"
    short = prepare_hero_request(
        request,
        catalog=catalog,
        workspace=short_workspace,
        target_level=10,
    )
    long = prepare_hero_request(
        request,
        catalog=catalog,
        workspace=long_workspace,
        target_level=100,
    )

    loaded = load_existing_hero_request(
        "Corararfen",
        workspace=tmp_path / "heroes",
        target_level=5,
    )
    resumed_short = prepare_hero_request(
        request,
        catalog=catalog,
        workspace=tmp_path / "heroes",
        target_level=5,
    )
    resumed_long = prepare_hero_request(
        request,
        catalog=catalog,
        workspace=tmp_path / "heroes",
        target_level=25,
    )

    assert short.directory != long.directory
    assert loaded.character_class == "warrior"
    assert resumed_short.resumed
    assert resumed_short.directory == short.directory
    assert load_campaign_spec(resumed_short.campaign_path).target_level == 10
    assert resumed_long.resumed
    assert resumed_long.directory == long.directory
    assert load_campaign_spec(resumed_long.campaign_path).target_level == 100


def test_named_resume_rejects_equal_duplicate_campaign_horizons(
    tmp_path: Path,
) -> None:
    catalog = parse_character_catalog(SOURCE, source="fixture")
    request = HeroRequest(
        name="Corararfen",
        race="human",
        sex="male",
        character_class="warrior",
    )
    prepare_hero_request(
        request,
        catalog=catalog,
        workspace=tmp_path / "heroes" / "first",
        target_level=100,
    )
    prepare_hero_request(
        request,
        catalog=catalog,
        workspace=tmp_path / "heroes" / "second",
        target_level=100,
    )

    with pytest.raises(ValueError, match="same campaign horizon"):
        load_existing_hero_request("Corararfen", workspace=tmp_path / "heroes")


def test_prepare_hero_request_generates_stable_name_when_omitted(
    tmp_path: Path,
) -> None:
    catalog = parse_character_catalog(SOURCE)
    request = HeroRequest(
        race="elf",
        sex="neuter",
        character_class="warrior",
    )

    first = prepare_hero_request(
        request,
        catalog=catalog,
        workspace=tmp_path / "heroes",
    )
    second = prepare_hero_request(
        request,
        catalog=catalog,
        workspace=tmp_path / "heroes",
    )

    assert first.character.name == second.character.name
    assert 3 <= len(first.character.name) <= 12
    assert first.character.name.isalpha()
    assert second.resumed


def test_prepare_hero_request_persists_mudlet_transport(tmp_path: Path) -> None:
    catalog = parse_character_catalog(SOURCE)
    bridge_directory = tmp_path / "shared-mudlet"
    request = HeroRequest(
        name="Valora",
        race="human",
        sex="female",
        character_class="mage",
        transport="mudlet",
        mudlet_directory=bridge_directory,
    )

    prepared = prepare_hero_request(
        request,
        catalog=catalog,
        workspace=tmp_path / "heroes",
    )

    profile = load_character_spec(prepared.profile_path)
    manifest = json.loads(prepared.manifest_path.read_text(encoding="utf-8"))
    assert profile.transport == "mudlet"
    assert profile.mudlet_directory == bridge_directory
    assert manifest["request"]["transport"] == "mudlet"
    assert (bridge_directory / "dd4tester_bridge.lua").is_file()
    assert (bridge_directory / "commands.txt").is_file()
    assert (bridge_directory / "events.jsonl").is_file()


def test_prepare_hero_request_requires_mudlet_directory(tmp_path: Path) -> None:
    catalog = parse_character_catalog(SOURCE)

    with pytest.raises(ValueError, match="mudlet_directory"):
        prepare_hero_request(
            HeroRequest(
                name="Valora",
                race="human",
                sex="female",
                character_class="mage",
                transport="mudlet",
            ),
            catalog=catalog,
            workspace=tmp_path / "heroes",
        )


def test_cosmetic_sex_is_preserved_without_becoming_a_coverage_dimension(
    tmp_path: Path,
) -> None:
    catalog = parse_character_catalog(SOURCE)
    female = prepare_hero_request(
        HeroRequest(race="human", sex="female", character_class="mage"),
        catalog=catalog,
        workspace=tmp_path / "heroes",
    )
    male = prepare_hero_request(
        HeroRequest(race="human", sex="male", character_class="mage"),
        catalog=catalog,
        workspace=tmp_path / "heroes",
    )

    assert female.directory != male.directory
    assert female.character.gender == "female"
    assert male.character.gender == "male"
    manifest = json.loads(female.manifest_path.read_text(encoding="utf-8"))
    assert "sex" not in manifest["coverage_dimensions"]
    assert manifest["cosmetic_dimensions"] == ["sex"]


def test_prepare_hero_request_rejects_subclass_from_another_class(
    tmp_path: Path,
) -> None:
    catalog = parse_character_catalog(SOURCE)

    with pytest.raises(ValueError, match="requires base class 'warrior'"):
        prepare_hero_request(
            HeroRequest(
                name="Valora",
                race="human",
                sex="female",
                character_class="mage",
                subclass="knight",
            ),
            catalog=catalog,
            workspace=tmp_path / "heroes",
        )


def test_prepare_hero_request_rejects_source_options_missing_from_runtime(
    tmp_path: Path,
) -> None:
    catalog = replace(parse_character_catalog(SOURCE), sexes=("male", "other"))

    with pytest.raises(
        ValueError,
        match="sex 'other' is not supported by the runtime model",
    ):
        prepare_hero_request(
            HeroRequest(race="human", sex="male", character_class="mage"),
            catalog=catalog,
            workspace=tmp_path / "heroes",
        )

    assert not (tmp_path / "heroes").exists()


def test_prepare_hero_request_accepts_source_legal_research_subclass(
    tmp_path: Path,
) -> None:
    base_catalog = parse_character_catalog(SOURCE)
    catalog = replace(
        base_catalog,
        classes=(*base_catalog.classes, ClassOption("smithy", "Smithy")),
        subclasses=(
            *base_catalog.subclasses,
            SubclassOption("engineer", "Engineer", "smithy"),
        ),
    )

    prepared = prepare_hero_request(
        HeroRequest(
            name="Valora",
            race="human",
            sex="female",
            character_class="smithy",
            subclass="engineer",
        ),
        catalog=catalog,
        workspace=tmp_path / "heroes",
    )

    assert prepared.character.character_class == "smithy"
    assert prepared.character.subclass == "engineer"
