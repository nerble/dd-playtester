from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionMetadata:
    category: str
    safety_critical: bool = False


def classify_decision(command: str, reason: str, stage: str) -> DecisionMetadata:
    """Classify a recorded bot action without coupling callers to policy internals."""
    command_text = command.strip().casefold()
    verb = command_text.split(maxsplit=1)[0] if command_text else ""
    reason_text = reason.casefold()
    stage_text = stage.casefold()

    if _contains(
        reason_text,
        "character died",
        "emergency",
        "purgatory",
        "retreat",
        "withdraw",
        "watchdog",
        "below 25 percent",
        "below 50 percent",
        "abort for safety",
    ) or verb == "flee":
        return DecisionMetadata("safety", True)
    if stage_text.startswith(("login", "create", "enter_world")):
        category = "creation" if stage_text.startswith("create") else "authentication"
        return DecisionMetadata(category)
    if verb in {
        "donate",
        "drop",
        "equipment",
        "get",
        "give",
        "inventory",
        "put",
        "remove",
        "sacrifice",
        "sell",
        "vault",
        "wear",
    }:
        return DecisionMetadata("inventory")
    if verb in {
        "north",
        "east",
        "south",
        "west",
        "up",
        "down",
        "out",
        "enter",
        "recall",
        "open",
        "unlock",
    }:
        return DecisionMetadata("navigation")
    if verb in {"consider", "help", "identify", "list", "look", "score", "time", "where"}:
        return DecisionMetadata("research")
    if verb in {"save", "quit"}:
        return DecisionMetadata("checkpoint")
    if verb in {"practice", "train", "gain"}:
        return DecisionMetadata("training")
    if verb in {"cast", "kill", "murder", "backstab", "bash", "kick"} or _contains(
        reason_text, "fight", "combat", "attack", "quaff"
    ):
        return DecisionMetadata("combat")
    if verb in {"sleep", "rest", "wake", "heal"} or _contains(
        reason_text, "recover", "healing room", "restore health", "restore mana"
    ):
        return DecisionMetadata("recovery")
    if verb in {"eat", "drink", "fill"} or _contains(
        reason_text,
        "food",
        "thirst",
        "provision",
        "water container",
        "water skin",
        "restock",
    ):
        return DecisionMetadata("provisioning")
    if _contains(
        reason_text, "practice", "training", "guildmaster"
    ):
        return DecisionMetadata("training")
    if verb in {
        "donate",
        "drop",
        "equipment",
        "get",
        "give",
        "inventory",
        "put",
        "remove",
        "sacrifice",
        "sell",
        "vault",
        "wear",
    } or _contains(reason_text, "gear", "inventory", "loot", "sale"):
        return DecisionMetadata("inventory")
    if _contains(reason_text, "route", "travel", "fastwalk", "return home"):
        return DecisionMetadata("navigation")
    return DecisionMetadata("other")


def _contains(value: str, *needles: str) -> bool:
    return any(needle in value for needle in needles)
