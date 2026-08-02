import asyncio
import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

from dd4tester.campaign import CampaignResult, load_campaign_spec
from dd4tester.character import load_character_spec
from dd4tester.dd4_catalog import ClassOption, SubclassOption, parse_character_catalog
from dd4tester.hero import HeroRequest, prepare_hero_request, run_hero_request


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
        )
    )

    assert result.status == "ready"
    assert captured["segments"] == 17
    assert captured["reset_retries"] == 17


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
    assert "dryly funny" in prepared.character.description
    assert load_character_spec(prepared.profile_path).description == (
        prepared.character.description
    )
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


def test_prepare_hero_request_names_unautomated_source_subclass(
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

    with pytest.raises(
        ValueError,
        match="subclass 'engineer' is source-legal but has no autonomous HERO policy yet",
    ):
        prepare_hero_request(
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

    assert not (tmp_path / "heroes").exists()
