import json

import pytest

from dd4tester.archetypes import archetype_registry, load_archetype_registry


def test_registry_resolves_aliases_and_character_capabilities() -> None:
    registry = archetype_registry()

    assert registry.class_profile("Psionicist").name == "psionic"
    assert registry.class_profile("shape-shifter").name == "shifter"
    assert registry.class_profile("mage").progression_track == (
        "verified-field-caster"
    )
    assert "stealth" in registry.class_profile("thief").capabilities
    assert registry.subclass_profile("knight").base_class == "warrior"


def test_registry_rejects_subclass_with_unknown_base_class(tmp_path) -> None:
    path = tmp_path / "archetypes.json"
    path.write_text(
        json.dumps(
            {
                "classes": {
                    "mage": {
                        "aliases": ["mage"],
                        "primary_stat": "int",
                        "practice_skill": "magic missile",
                        "level_gain_priorities": ["mana"],
                        "progression_track": "tutorial-arena",
                        "capabilities": [],
                    }
                },
                "subclasses": {
                    "knight": {
                        "base_class": "warrior",
                        "available": True,
                        "capabilities": [],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unknown base class warrior"):
        load_archetype_registry(path)
