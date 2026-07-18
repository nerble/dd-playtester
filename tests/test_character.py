from pathlib import Path

import pytest

from dd4tester.character import CharacterSpec, load_character_spec


def test_subclass_derives_required_base_class() -> None:
    spec = CharacterSpec.from_mapping(
        {
            "name": "Rulemage",
            "password_env": "TEST_PASSWORD",
            "race": "Half-Dragon",
            "gender": "female",
            "subclass": "Warlock",
        }
    )

    assert spec.race == "half dragon"
    assert spec.race_choice == "i"
    assert spec.character_class == "mage"
    assert spec.subclass == "warlock"
    assert spec.primary_stat == "int"


def test_profile_derives_stable_credential_name() -> None:
    spec = CharacterSpec.from_mapping(
        {
            "name": "Rulemage",
            "race": "human",
            "gender": "female",
            "class": "mage",
        }
    )

    assert spec.credential_name == "character:rulemage"


def test_profile_rejects_subclass_and_base_class_mismatch() -> None:
    with pytest.raises(ValueError, match="requires base class 'mage'"):
        CharacterSpec.from_mapping(
            {
                "name": "Badmatch",
                "race": "human",
                "gender": "male",
                "class": "warrior",
                "subclass": "necromancer",
            }
        )


def test_profile_rejects_unimplemented_subclass() -> None:
    with pytest.raises(ValueError, match="not implemented"):
        CharacterSpec.from_mapping(
            {
                "name": "Builder",
                "race": "dwarf",
                "gender": "neuter",
                "subclass": "engineer",
            }
        )


def test_load_character_spec_from_yaml(tmp_path: Path) -> None:
    profile = tmp_path / "starter.yaml"
    profile.write_text(
        "\n".join(
            [
                "name: Testhero",
                "race: wild-elf",
                "gender: male",
                "class: ranger",
                "subclass: bard",
                "colour: false",
                "max_commands: 99",
            ]
        ),
        encoding="utf-8",
    )

    spec = load_character_spec(profile)

    assert spec.name == "Testhero"
    assert spec.race == "wild elf"
    assert spec.gender_choice == "m"
    assert spec.character_class == "ranger"
    assert spec.colour is False
    assert spec.max_commands == 99
