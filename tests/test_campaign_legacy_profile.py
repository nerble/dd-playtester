from pathlib import Path

import pytest

from dd4tester.campaign import load_campaign_spec


def test_load_campaign_spec_resumes_legacy_character_profile(tmp_path: Path) -> None:
    profile = tmp_path / "legacy-hero.yaml"
    profile.write_text(
        "\n".join(
            [
                "name: Ararisa",
                "credential_name: character:ararisa",
                "race: human",
                "gender: female",
                "class: mage",
                "subclass: warlock",
                f"database: '{(tmp_path / 'runs.sqlite3').as_posix()}'",
                f"transcript_dir: '{(tmp_path / 'transcripts').as_posix()}'",
            ]
        ),
        encoding="utf-8",
    )

    campaign = load_campaign_spec(profile)

    assert campaign.character_profile == profile.resolve()
    assert campaign.name == "Ararisa to HERO"
    assert campaign.character.name == "Ararisa"
    assert campaign.character.character_class == "mage"
    assert campaign.character.subclass == "warlock"
    assert campaign.target_level == 100


def test_load_campaign_spec_still_requires_profile_for_campaign_yaml(
    tmp_path: Path,
) -> None:
    config = tmp_path / "campaign.yaml"
    config.write_text("name: Missing profile\ntarget_level: 100\n", encoding="utf-8")

    with pytest.raises(ValueError, match="character_profile is required"):
        load_campaign_spec(config)
