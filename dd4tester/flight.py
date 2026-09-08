"""Source-authorized learned flight and bounded positive confirmation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping

from .archetypes import archetype_registry


FLIGHT_EVIDENCE_KEY = "campaign_learned_flight"
FLIGHT_RETRY_SECONDS = 600


@dataclass(frozen=True)
class FlightSpell:
    name: str
    proficiency: int

    @property
    def mana_cost(self) -> int:
        # handler.c:mana_cost, non-offensive spell; const.c minimum is 10.
        return max(10, 45 - self.proficiency)


def learned_flight_spell(
    character_class: str, subclass: str | None, skills: Mapping[str, object],
) -> FlightSpell | None:
    """Authorize only audited class/subclass paths with observed practice."""
    if not isinstance(skills, Mapping):
        return None
    subclass = str(subclass or "").strip().casefold()
    if subclass == "none":
        subclass = ""
    registry = archetype_registry()
    try:
        base = registry.class_profile(character_class).name
        if subclass:
            profile = registry.subclass_profile(subclass)
            if profile.base_class != base or not profile.available:
                return None
    except ValueError:
        return None
    # pre_req-common.c:29 through mage/cleric alteration; psionic/monk:8.
    names = []
    if base == "psionic" or (subclass or "").casefold() == "monk":
        names.append("levitation")
    if base in {"mage", "cleric"}:
        names.append("fly")
    for name in names:
        percent = skills.get(name)
        if type(percent) is int and 0 < percent <= 100:
            return FlightSpell(name, percent)
    return None


def flight_retry_pending(
    evidence: object, *, spell: FlightSpell, boot_id: object, level: int,
    now: datetime | None = None,
) -> bool:
    if not isinstance(evidence, Mapping) or evidence.get("status") == "confirmed":
        return False
    if (
        evidence.get("spell") != spell.name
        or evidence.get("proficiency") != spell.proficiency
        or evidence.get("boot_id") != boot_id or evidence.get("level") != level
    ):
        return False
    try:
        attempted = datetime.fromisoformat(str(evidence["attempted_at"]))
        if attempted.tzinfo is None:
            return True
        age = ((now or datetime.now(timezone.utc)) - attempted).total_seconds()
    except (KeyError, TypeError, ValueError, OverflowError):
        return True
    return age < FLIGHT_RETRY_SECONDS


@dataclass
class FlightPreparation:
    status: str = "idle"
    spell: FlightSpell | None = None
    attempts: int = 0
    requested_revision: int = 0
    probed: bool = False
    concentration_failed: bool = False
    response: str = ""
    failure: str | None = None
    deadline: float | None = None
    stand_attempted: bool = False
    attempted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def observe(self, text: str) -> None:
        if self.status != "pending":
            return
        self.response = (self.response + text)[-2000:]
        lines = {" ".join(line.casefold().split()) for line in self.response.splitlines()}
        self.concentration_failed = bool(lines & {
            "you lost your concentration.", "you lose your concentration.",
            "you fail to correctly recite the spell!",
        })
        if lines & {
            "you don't have enough mana.", "you don't know any spells of that name.",
            "you can't concentrate enough.",
        }:
            self.fail("the learned flight spell was refused")

    def fail(self, reason: str) -> None:
        self.status = "unavailable"
        self.failure = reason

    def next_command(
        self, spell: FlightSpell | None, *, active: bool, affect_revision: int,
        mana: int | None, standing: bool, now: float,
    ) -> str | None:
        if self.status in {"confirmed", "unavailable"}:
            return None
        if self.spell is None:
            self.spell = spell
        if self.deadline is None:
            self.deadline = now + 30
        if active and (self.attempts == 0 or affect_revision > self.requested_revision):
            self.status = "confirmed"
            return None
        if self.deadline is not None and now >= self.deadline:
            self.fail("learned flight confirmation timed out")
            return None
        if spell is None or (self.spell is not None and spell != self.spell):
            self.fail("no source-authorized practiced flight spell remains")
            return None
        self.spell = spell
        if not standing:
            if self.stand_attempted:
                self.fail("standing was not confirmed before learned flight")
                return None
            self.stand_attempted = True
            return "stand"
        if self.status == "pending" and not self.concentration_failed:
            if self.probed:
                self.fail("no fresh live flight affect after the confirmation probe")
                return None
            self.probed = True
            return "affects"
        if self.attempts >= 3:
            self.fail("three learned flight attempts lost concentration")
            return None
        if mana is None or mana < spell.mana_cost:
            self.fail("insufficient observed mana for the learned flight spell")
            return None
        self.status = "pending"
        self.attempts += 1
        self.requested_revision = affect_revision
        self.probed = self.concentration_failed = False
        self.response = ""
        return f"cast '{spell.name}' self"

    def evidence(self) -> dict[str, object]:
        return {
            "status": self.status, "spell": self.spell.name if self.spell else None,
            "proficiency": self.spell.proficiency if self.spell else None,
            "attempts": self.attempts, "failure": self.failure,
            "attempted_at": self.attempted_at,
        }
