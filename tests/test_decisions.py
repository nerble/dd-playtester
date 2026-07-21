import pytest

from dd4tester.decisions import classify_decision


@pytest.mark.parametrize(
    ("command", "reason", "stage", "category", "safety_critical"),
    [
        ("mage", "select base class", "create_class", "creation", False),
        ("kill wolf", "fight the tutorial wolf", "course", "combat", False),
        ("cast 'magic missile' wolf", "cast a combat spell", "course", "combat", False),
        ("sleep", "recover health and mana", "arena", "recovery", False),
        ("drink skin", "satisfy thirst", "field", "provisioning", False),
        ("practice backstab", "practice class skill", "arena", "training", False),
        ("flee", "withdraw below 25 percent health", "field", "safety", True),
        ("wear sword", "equip combat gear", "field", "inventory", False),
        ("north", "follow verified route", "field", "navigation", False),
        ("east", "return to the combat corridor", "course", "navigation", False),
        ("consider guard", "assess target", "field", "research", False),
        ("look", "identify the combat opponent", "course", "research", False),
        ("save", "save progress", "home", "checkpoint", False),
    ],
)
def test_decision_classification(
    command: str,
    reason: str,
    stage: str,
    category: str,
    safety_critical: bool,
) -> None:
    metadata = classify_decision(command, reason, stage)

    assert metadata.category == category
    assert metadata.safety_critical is safety_critical
