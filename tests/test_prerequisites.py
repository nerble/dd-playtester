from dd4tester.prerequisites import (
    known_skills,
    load_snapshot,
    parse_prerequisite_directory,
    parse_prerequisite_text,
    requirements_for_skill,
)


def test_parser_extracts_skill_requirement_records() -> None:
    entries = parse_prerequisite_text(
        """
        {&gsn_fireball, &gsn_group_evocation, 75, PRE_MAGE},
        {&gsn_fireball, &gsn_mage_base, 60, PRE_MAGE},
        """,
        class_name="mage",
    )

    assert [(entry.skill, entry.prerequisite, entry.minimum_percent) for entry in entries] == [
        ("fireball", "group evocation", 75),
        ("fireball", "mage base", 60),
    ]


def test_directory_parser_and_requirement_lookup_include_common_rules(tmp_path) -> None:
    (tmp_path / "pre_req-mage.c").write_text(
        "{&gsn_fireball, &gsn_group_evocation, 75, PRE_MAGE},\n",
        encoding="utf-8",
    )
    (tmp_path / "pre_req-common.c").write_text(
        "{&gsn_group_evocation, &gsn_magic_missile, 10, 0},\n",
        encoding="utf-8",
    )

    entries = parse_prerequisite_directory(tmp_path)
    requirements = requirements_for_skill(
        entries,
        class_name="mage",
        skill="group evocation",
    )

    assert [(entry.prerequisite, entry.minimum_percent) for entry in requirements] == [
        ("magic missile", 10)
    ]
    assert known_skills(entries, class_name="mage") == ["fireball", "group evocation"]


def test_bundled_snapshot_contains_mage_and_warlock_requirements() -> None:
    source, entries = load_snapshot()

    fireball = requirements_for_skill(entries, class_name="mage", skill="fireball")
    dragon_shield = requirements_for_skill(
        entries,
        class_name="warlock",
        skill="dragon shield",
    )

    assert source["repository"] == "https://github.com/fromage-fraser/dd4"
    assert ("group evocation", 75) in {
        (entry.prerequisite, entry.minimum_percent) for entry in fireball
    }
    assert ("group majorp", 50) in {
        (entry.prerequisite, entry.minimum_percent) for entry in dragon_shield
    }
