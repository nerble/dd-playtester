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
    assert spec.identity.progression_track == "verified-field-caster"
    assert {"spellcasting", "warlock-magic"} <= spec.identity.capabilities


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
    assert spec.title
    assert "Rulemage" in spec.description
    assert "human" in spec.description
    assert spec.effective_level_gain_priorities[:2] == (
        "intellectual_practices",
        "mana",
    )


def test_profile_accepts_explicit_test_character_title() -> None:
    spec = CharacterSpec.from_mapping(
        {
            "name": "Rulemage",
            "race": "human",
            "gender": "female",
            "class": "mage",
            "title": "the Walking Bug Report",
        }
    )

    assert spec.title == "the Walking Bug Report"


def test_profile_accepts_explicit_character_description() -> None:
    spec = CharacterSpec.from_mapping(
        {
            "name": "Rulemage",
            "race": "human",
            "gender": "female",
            "class": "mage",
            "description": "Rulemage keeps a brass astrolabe and a patient distrust of shortcuts.",
        }
    )

    assert spec.description.startswith("Rulemage keeps")


@pytest.mark.parametrize("description", ["", "two\nlines", "a tilde ~ here"])
def test_profile_rejects_invalid_character_description(description: str) -> None:
    with pytest.raises(ValueError, match="description"):
        CharacterSpec.from_mapping(
            {
                "name": "Rulemage",
                "race": "human",
                "gender": "female",
                "class": "mage",
                "description": description,
            }
        )


def test_profile_accepts_explicit_level_gain_priorities() -> None:
    spec = CharacterSpec.from_mapping(
        {
            "name": "Rulemage",
            "race": "human",
            "gender": "female",
            "class": "mage",
            "level_gain_priorities": ["hitpoints", "mana"],
        }
    )

    assert spec.effective_level_gain_priorities == ("hitpoints", "mana")


def test_profile_selects_mudlet_transport_from_a_shared_directory(tmp_path) -> None:
    bridge_directory = tmp_path / "mudlet"
    spec = CharacterSpec.from_mapping(
        {
            "name": "Rulemage",
            "race": "human",
            "gender": "female",
            "class": "mage",
            "transport": "mudlet",
            "mudlet_directory": str(bridge_directory),
        }
    )

    assert spec.transport == "mudlet"
    assert spec.mudlet_directory == bridge_directory


def test_profile_requires_directory_for_mudlet_transport() -> None:
    with pytest.raises(ValueError, match="mudlet_directory"):
        CharacterSpec.from_mapping(
            {
                "name": "Rulemage",
                "race": "human",
                "gender": "female",
                "class": "mage",
                "transport": "mudlet",
            }
        )


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


@pytest.mark.parametrize(
    ("character_class", "subclass", "practice_skill", "capability"),
    [
        ("mage", "warlock", "magic missile", "spellcasting"),
        ("thief", "ninja", "backstab", "stealth"),
        ("warrior", "knight", "kick", "weapon-combat"),
    ],
)
def test_representative_matrix_derives_data_driven_identity(
    character_class: str,
    subclass: str,
    practice_skill: str,
    capability: str,
) -> None:
    spec = CharacterSpec.from_mapping(
        {
            "name": "Matrixhero",
            "race": "human",
            "gender": "neuter",
            "class": character_class,
            "subclass": subclass,
        }
    )

    assert spec.identity.practice_skill == practice_skill
    assert capability in spec.identity.capabilities
