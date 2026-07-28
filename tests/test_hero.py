import json
from dataclasses import replace
from pathlib import Path

import pytest

from dd4tester.campaign import load_campaign_spec
from dd4tester.character import load_character_spec
from dd4tester.dd4_catalog import ClassOption, SubclassOption, parse_character_catalog
from dd4tester.hero import HeroRequest, prepare_hero_request


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
