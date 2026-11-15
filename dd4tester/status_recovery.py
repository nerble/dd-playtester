"""Immutable source proof shared by the planner and live status gate."""

from dataclasses import dataclass
from collections.abc import Collection


@dataclass(frozen=True)
class SourceHealerRecovery:
    mobile_vnum: int
    room_vnum: str
    specials: tuple[str, ...]
    maximum_source_level: int
    effects: tuple[str, ...]

    def matches(self, *, mobile_vnum: int | None, reset_room: str | None,
                specials: Collection[str], source_level: int,
                effects: Collection[str]) -> bool:
        return bool(
            self.mobile_vnum == mobile_vnum and self.room_vnum == reset_room
            and tuple(specials) == self.specials
            and self.specials in {("spec_cast_mage",), ("spec_cast_cleric",)}
            and 1 <= source_level <= self.maximum_source_level
            and "blindness" in self.effects and set(effects) <= set(self.effects)
        )
