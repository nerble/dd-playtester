"""Bounded command acknowledgements and DD4's source-defined combat lag."""

from __future__ import annotations

import re
from dataclasses import dataclass
from math import ceil

from .hunt_candidates import mobile_expected_round_damage


COMBAT_WAIT_SECONDS = 3.25  # Twelve wait pulses, then the next 4-Hz input pulse.
ACK_TIMEOUT_SECONDS = 10.0

# const.c damage nouns for the registered direct spells. Authorization stays
# in combat_capabilities; these names only recognize commands already issued.
SPELL_NOUNS = {
    "acid blast": "acid blast", "fireball": "fireball",
    "lightning bolt": "lightning bolt", "shocking grasp": "shocking grasp",
    "colour spray": "colour spray",
    "burning hands": "burning hand", "chill touch": "chilling touch",
    "magic missile": "spell", "cause light": "spell",
    "cause serious": "spell", "cause critical": "spell",
    "psychic crush": "psychic crush", "agitation": "agitation",
    "mind thrust": "mind thrust", "harm": "harm spell",
    "wither": "withering grasp", "flamestrike": "flamestrike",
    "hellfire": "hellfire",
}
SPELL_MIN_MANA = {
    "acid blast": 20, "fireball": 15, "lightning bolt": 15,
    "shocking grasp": 15, "colour spray": 15,
    "burning hands": 15, "chill touch": 10, "magic missile": 5,
    "cause light": 15, "cause serious": 17, "cause critical": 20,
    "psychic crush": 15, "agitation": 10, "mind thrust": 8,
    "harm": 35, "wither": 20, "flamestrike": 20,
    "hellfire": 20,
}


@dataclass
class CombatCommandWindow:
    command: str | None = None
    target: str = ""
    noun: str | None = None
    issued_at: float | None = None
    acknowledged_at: float | None = None
    ready_at: float = 0.0
    buffer: str = ""
    sent: int = 0
    acknowledged: int = 0
    timeouts: int = 0
    early_withdrawals: int = 0
    suspended: bool = False

    def issue(self, command: str, *, target: str, now: float) -> None:
        if not target.strip():
            return
        match = re.fullmatch(r"cast '([^']+)' .+", command)
        noun = SPELL_NOUNS.get(match.group(1)) if match else None
        if noun is None and not command.startswith("kill "):
            return
        self.command, self.noun = command, noun
        self.target = re.sub(r"^(?:the|an|a)\s+", "", " ".join(target.casefold().split()))
        self.issued_at = now
        self.suspended = False
        self.acknowledged_at = None
        self.ready_at = now + COMBAT_WAIT_SECONDS
        self.buffer = ""
        self.sent += 1

    @property
    def pending(self) -> bool:
        return self.command is not None and self.acknowledged_at is None

    def observe(self, text: str, *, now: float) -> None:
        if not self.pending:
            return
        self.buffer = (self.buffer + text)[-4000:]
        lines = [" ".join(line.casefold().split()) for line in self.buffer.splitlines()]
        refusals = {
            "you don't have enough mana.", "you don't know any spells of that name.",
            "they aren't here.", "you aren't fighting anyone.",
            "you can't concentrate enough.", "you do the best you can!",
            "they are immune to this spell's effects!",
            "you can't attack them in their current form.",
        }
        refused = bool(set(lines) & refusals)
        prefix = f"your {self.noun} " if self.noun else "your "
        damage = any(
            line.startswith(prefix)
            and re.search(
                rf"\b{re.escape(self.target)}[.!]+(?: \*critical hit\*)?(?:\s|$)",
                line,
            )
            and not any(marker in line for marker in (" says ", " tells "))
            for line in lines
        )
        target_head = self.target.split()[0] if self.target else ""
        attack_resolved = bool(
            self.noun is None
            and self.command is not None
            and self.command.startswith("kill ")
            and target_head
            and any(
                re.fullmatch(
                    rf"(?:(?:the|an|a) )?{re.escape(target_head)}"
                    rf"(?: [^.!?]+)? (?:dodges|parries) your attack[.!]",
                    line,
                )
                for line in lines
            )
        )
        if not refused and not damage and not attack_resolved:
            return
        self.acknowledged_at = now
        self.suspended = False
        self.acknowledged += 1
        # A reply proves execution, not completion of the ensuing WAIT_STATE.
        self.ready_at = max(self.ready_at, now + COMBAT_WAIT_SECONDS)

    def blocked(self, now: float) -> bool:
        return self.suspended or self.pending or now < self.ready_at

    def expired(self, now: float) -> bool:
        return bool(not self.suspended and self.pending and self.issued_at is not None
                    and now - self.issued_at >= ACK_TIMEOUT_SECONDS)

    def suspend(self) -> None:
        if not self.suspended:
            self.timeouts += 1
        self.suspended = True

    def reset(self) -> None:
        self.command = None
        self.target = ""
        self.noun = None
        self.issued_at = self.acknowledged_at = None
        self.ready_at = 0.0
        self.buffer = ""
        self.suspended = False

    def evidence(self) -> dict[str, int]:
        return {
            "sent": self.sent, "acknowledged": self.acknowledged,
            "timeouts": self.timeouts, "early_withdrawals": self.early_withdrawals,
        }


def anticipatory_companion_withdrawal(
    *, enemy_hp: int, enemy_max_hp: int, companion_level: int,
    companion_damage_modifier: int | None = 0,
    player_hp: int, player_max_hp: int, mana: int, max_mana: int,
    source_peak: int, source_critical: int, action_damage: int,
    action_cost: int, maximum_actions: int, expected_incoming_per_round: int,
) -> bool:
    """Reserve two NPC rounds before another lagged action, only for a short finish.

    This changes the timing of an existing companion's withdrawal, never target
    admission. The ordinary player survival and damage-window checks still run.
    """
    if (
        min(enemy_hp, enemy_max_hp, companion_level, player_hp, player_max_hp,
            max_mana, source_peak, source_critical, action_damage, action_cost,
            maximum_actions, expected_incoming_per_round) <= 0
        or companion_damage_modifier is None
        or enemy_hp > enemy_max_hp or player_hp > player_max_hp
        or player_hp < ceil(player_max_hp * .8)
        or enemy_hp > player_hp // 2 or enemy_hp > enemy_max_hp * .75
        or source_peak >= player_hp or source_critical >= player_hp // 2
    ):
        return False
    actions = ceil(enemy_hp / action_damage)
    if actions > min(6, maximum_actions) or mana - actions * action_cost < ceil(max_mana * .15):
        return False
    health_reserve = max(ceil(player_max_hp * .4), source_critical)
    if (actions + 1) * expected_incoming_per_round >= player_hp - health_reserve:
        return False
    reserve = 2 * mobile_expected_round_damage(
        companion_level,
        wielding=False,
        dual_wielding=False,
        damage_modifier=companion_damage_modifier,
    )
    return enemy_hp <= reserve
