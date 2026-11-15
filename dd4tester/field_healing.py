"""Finite standing self-healing before an already-selected field stop."""

from dataclasses import dataclass, field

from .combat_timing import CombatCommandWindow


HEALING_SPELLS = (("heal", 50), ("cure critical", 20), ("cure serious", 15), ("cure light", 10))


@dataclass
class FieldHealingSession:
    scope: tuple | None = None
    baseline_sequence: int = 0
    started_at: float = 0.0
    initial_hp: int = 0
    attempts: int = 0
    closed: bool = False
    reason: str | None = None
    window: CombatCommandWindow = field(default_factory=CombatCommandWindow)
    attempted: set[tuple] = field(default_factory=set)
    records: list[dict] = field(default_factory=list)
    audited_sequence: int | None = None
    room_allowed: bool = False

    def begin(self, scope: tuple, *, sequence: int, hp: int, now: float) -> bool:
        if scope in self.attempted or len(self.attempted) >= 8:
            return False
        if self.window.blocked(now) and not self.window.expired(now):
            return False
        self.attempted.add(scope)
        self.scope, self.baseline_sequence = scope, sequence
        self.started_at, self.initial_hp = now, hp
        self.attempts, self.closed, self.reason = 0, False, None
        self.audited_sequence, self.room_allowed = None, False
        self.window.reset()
        return True

    def finish(self, reason: str, *, hp: int) -> None:
        if self.closed or self.scope is None:
            return
        self.closed, self.reason = True, reason
        self.records.append({
            "scope": list(self.scope), "attempts": self.attempts,
            "initial_hp": self.initial_hp, "final_hp": hp, "outcome": reason,
        })
        self.records = self.records[-8:]

    def receipt(self) -> dict:
        return {
            "records": list(self.records),
            "pending": ({"scope": list(self.scope), "attempts": self.attempts,
                         "window": self.window.evidence()}
                        if self.scope is not None and not self.closed else None),
        }

    def advance(
        self, scope: tuple, *, sequence: int, hp: int, max_hp: int,
        minimum_ratio: float, mana: int, max_mana: int,
        spell: str, mana_cost: int, room_allowed: bool, now: float,
    ) -> tuple[bool, str | None]:
        if self.scope != scope or self.closed:
            return False, None
        if now - self.started_at >= 45 or self.window.expired(now):
            self.finish("reply_or_session_deadline", hp=hp)
            return False, None
        if self.window.blocked(now):
            return True, None
        if hp >= max_hp * minimum_ratio:
            self.finish("ready", hp=hp)
            return False, None
        if sequence <= self.baseline_sequence:
            if now - self.started_at >= 5:
                self.finish("room_reply_deadline", hp=hp)
                return False, None
            return True, None
        if not room_allowed:
            self.finish("room_not_verified", hp=hp)
            return False, None
        if self.attempts >= 8 or mana - mana_cost < max(20, int(max_mana * .3)):
            self.finish("attempt_or_mana_limit", hp=hp)
            return False, None
        self.attempts += 1
        command = f"cast '{spell}'"
        self.window.issue(command, target="self", scope=scope, now=now)
        return True, command
