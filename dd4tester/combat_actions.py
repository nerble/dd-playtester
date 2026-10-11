"""Source timing estimates for already-admitted between-round attacks."""

from __future__ import annotations

from typing import Collection, Mapping


def preferred_timed_damage_skill(
    available: Collection[str],
    *,
    level: int | None,
    proficiency: Mapping[str, int] | None,
) -> str | None:
    """Choose kick or headbutt by expected raw damage per second, not power.

    Callers admit anatomy, class, equipment and live combat first. Both attacks
    have the same blunt/nonmagic resistance flags. fight.c:do_headbutt waits
    six seconds on success, three on failure; do_kick always waits two.
    violence_update does not suspend ordinary NPC attacks for that wait.
    This estimate is not observed damage or permission to fight.
    """
    if (
        not {"headbutt", "kick"}.issubset(available)
        or isinstance(level, bool)
        or not isinstance(level, int)
        or not 1 <= level <= 100
        or not isinstance(proficiency, Mapping)
    ):
        return None
    observed = {
        " ".join(str(name).casefold().split()): value
        for name, value in proficiency.items()
    }

    def probability(name: str) -> float | None:
        value = observed.get(name)
        if isinstance(value, bool) or not isinstance(value, int):
            return None
        if not 0 <= value <= 100:
            return None
        # rng.c:number_percent is 1..100; these attacks use a strict '<'.
        return max(0, value - 1) / 100.0

    headbutt = probability("headbutt")
    kick = probability("kick")
    if headbutt is None or kick is None or headbutt <= 0 or kick <= 0:
        return None
    second = probability("second headbutt") or 0.0
    base = level // 2
    headbutt_damage = headbutt * (
        base + (1 + level * 3) / 2
        + second * (base + (10 + max(10, level * 3)) / 2)
    )
    headbutt_wait = 3.0 * (1.0 + headbutt)
    kick_damage = kick * (base + (1 + level) / 2)
    return "headbutt" if headbutt_damage / headbutt_wait > kick_damage / 2.0 else "kick"
