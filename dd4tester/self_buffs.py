"""Bounded healer-side renewal of source-audited learned protection."""

from dataclasses import dataclass
from typing import Mapping

from .archetypes import archetype_registry


@dataclass(frozen=True)
class ProtectionSpell:
    name: str
    proficiency: int

    @property
    def mana_cost(self) -> int:
        # handler.c:mana_cost; const.c gives armor a five-mana minimum.
        return max(5, 45 - self.proficiency)


def learned_protection_spell(
    character_class: str, subclass: str | None, skills: Mapping[str, object],
) -> ProtectionSpell | None:
    # pre_req-cleric.c, pre_req-mage.c and pre_req-knight.c authorize armor.
    subclass = str(subclass or "").casefold().strip()
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
    percent = skills.get("armor")
    if (
        (base in {"cleric", "mage"} or (base == "warrior" and subclass == "knight"))
        and type(percent) is int and 0 < percent <= 100
    ):
        return ProtectionSpell("armor", percent)
    return None


@dataclass
class HealerBuffPreparation:
    status: str = "idle"
    scope: tuple | None = None
    spell: ProtectionSpell | None = None
    attempts: int = 0
    requested_revision: int = 0
    deadline: float | None = None
    ready_at: float = 0.0
    response: str = ""
    acknowledged: bool = False
    awaiting_prompt: bool = False
    failure: str | None = None

    @property
    def pending(self) -> bool:
        return self.status in {"checking", "casting", "confirming"}

    def fail(self, reason: str) -> None:
        self.status, self.failure = "failed", reason

    def observe(self, text: str, *, now: float) -> None:
        if self.status != "casting":
            return
        self.response = (self.response + text)[-2048:]
        lines = {" ".join(line.casefold().split())
                 for line in self.response.replace("\r", "\n").split("\n")[:-1]}
        if "you feel someone protecting you." in lines and not self.acknowledged:
            self.acknowledged = True
            self.ready_at = max(self.ready_at, now + .5)
        if self.failure is None and lines & {
            "you don't have enough mana.", "you don't know any spells of that name.",
            "you can't concentrate enough.", "you fail to correctly recite the spell!",
            "you lost your concentration.", "you lose your concentration.",
        }:
            self.failure = "the learned protection spell was refused or failed"
            self.acknowledged = True
            self.ready_at = max(self.ready_at, now + .5)

    def next_command(
        self, spell: ProtectionSpell | None, *, scope: tuple, active: bool,
        affect_revision: int, mana: int, max_mana: int, now: float,
    ) -> tuple[bool, str | None]:
        if self.status in {"confirmed", "active", "failed", "skipped"}:
            return False, None
        if self.scope is not None and (scope != self.scope or spell != self.spell):
            self.fail("protection preparation scope changed")
            return False, None
        if spell is None:
            return False, None
        if self.deadline is None:
            self.deadline, self.scope, self.spell = now + 12, scope, spell
        if now >= self.deadline:
            self.fail("protection confirmation deadline")
            return False, None
        if self.status == "casting":
            if not self.acknowledged or now < self.ready_at:
                return True, None
            if self.failure:
                self.status = "failed"
                return False, None
            if active and affect_revision > self.requested_revision:
                self.status = "confirmed"
                return False, None
            self.status, self.requested_revision = "confirming", affect_revision
            return True, "affects"
        if self.status in {"checking", "confirming"}:
            if affect_revision <= self.requested_revision:
                return True, None
            if self.status == "confirming" and not active:
                self.fail("no fresh protection affect after the confirmation probe")
                return False, None
        if active and affect_revision > 0:
            self.status = "confirmed" if self.attempts else "active"
            return False, None
        if affect_revision <= 0:
            self.status, self.requested_revision = "checking", affect_revision
            return True, "affects"
        if mana - spell.mana_cost < max(20, int(max_mana * .5)):
            self.status = "skipped"
            self.failure = "keep the observed combat mana reserve"
            return False, None
        self.status, self.attempts = "casting", self.attempts + 1
        self.requested_revision, self.ready_at = affect_revision, now + .5
        return True, f"cast '{spell.name}' self"

    def evidence(self) -> dict:
        return {
            "status": self.status, "scope": list(self.scope) if self.scope else None,
            "spell": self.spell.name if self.spell else None,
            "proficiency": self.spell.proficiency if self.spell else None,
            "attempts": self.attempts, "reply_observed": self.acknowledged,
            "awaiting_prompt": self.awaiting_prompt,
            "failure": self.failure,
        }
