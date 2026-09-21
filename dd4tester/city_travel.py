"""Source-bounded city shopping and one session-local defensive interruption."""

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .hunt_candidates import (
    WorldSource, _mobile_base_hp_range, _mobile_level_range,
    source_mobile_route_program_attacker_is_bounded,
)


CITY_GREETER_VNUM = 3064
MAGIC_SHOP_ROUTE_ROOMS = frozenset({
    "3054", "3001", "3005", "3006", "3014", "3013", "3019", "3018",
    "3017", "3012", "3033",
})
CITY_TRANSIT_KEY = "campaign_city_shop_transit"
GMCP_ALIGNMENT_HIDDEN_VALUE = 50000
GMCP_ALIGNMENT_REVEAL_LEVEL = 10
ALIGNMENT_MIN = -1000
ALIGNMENT_MAX = 1000
GUARD_ASSIST_ALIGNMENT_CEILING = 300


def bounded_city_shop_transit_available(
    world: WorldSource | None, state: Mapping[str, Any],
) -> bool:
    if world is None:
        return False
    level, maximum_hp = state.get("level"), state.get("max_hp")
    if type(level) is not int or type(maximum_hp) is not int:
        return False
    prior = state.get(CITY_TRANSIT_KEY)
    if (isinstance(prior, Mapping) and prior.get("status") == "aborted"
            and prior.get("level") == level
            and (not prior.get("boot_id") or not state.get("world_boot_id")
                 or prior.get("boot_id") == state.get("world_boot_id"))):
        return False
    mobile = world.mobiles.get(CITY_GREETER_VNUM)
    return bool(mobile and mobile.hp_modifier_known
                and mobile.damage_modifier_known
                and mobile.area_file == "midgaard.are"
                and source_mobile_route_program_attacker_is_bounded(
                    world, mobile, character_level=level, character_max_hp=maximum_hp,
                ))


def _number(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def revealed_gmcp_alignment(value: Any, *, level: Any) -> int | None:
    """Return DD4's real alignment value, excluding the pre-level-10 mask."""
    alignment = _number(value)
    observed_level = _number(level)
    if (
        observed_level is None
        or observed_level < GMCP_ALIGNMENT_REVEAL_LEVEL
        or alignment is None
        or alignment == GMCP_ALIGNMENT_HIDDEN_VALUE
        or not ALIGNMENT_MIN <= alignment <= ALIGNMENT_MAX
    ):
        return None
    return alignment


def observed_guard_safe_alignment(value: Any, *, level: Any) -> bool:
    """Return whether GMCP proves the player clears DD4's guard threshold."""
    alignment = revealed_gmcp_alignment(value, level=level)
    return alignment is not None and alignment >= GUARD_ASSIST_ALIGNMENT_CEILING


def field_city_route_rooms(
    world: WorldSource | None, commands: Sequence[str], *, origin: int,
    alignment: Any, level: Any,
) -> tuple[str, ...]:
    """Scope the existing locator to the actual Midgaard departure and refill."""
    if (
        world is None
        or origin != 3001
        or observed_guard_safe_alignment(alignment, level=level)
    ):
        return ()
    greeter = world.mobiles.get(CITY_GREETER_VNUM)
    if greeter is None or greeter.area_file != "midgaard.are" or not greeter.attack_programs:
        return ()
    if not any(
        "spec_guard" in specials and vnum in world.mobiles
        and world.mobiles[vnum].area_file == "midgaard.are"
        for vnum, specials in world.mobile_specials.items()
    ):
        return ()
    names = [world.rooms[vnum].name for vnum in (3054, 3001, 3005)
             if vnum in world.rooms]
    room = world.rooms.get(origin)
    for command in commands:
        if room is None or room.area_file != "midgaard.are" or room.random_exits:
            break
        if command.startswith("open "):
            continue
        exit_ = room.exits.get(command)
        if exit_ is None:
            break
        room = world.rooms.get(exit_.destination)
        if room is not None and room.area_file == "midgaard.are":
            names.append(room.name)
    return tuple(dict.fromkeys(names))


@dataclass
class CityShopTransit:
    status: str = "idle"
    started_at: float | None = None
    reason: str | None = None

    def admit(self) -> None:
        if self.status == "idle":
            self.status = "admitted"

    def finish_combat(self) -> None:
        if self.status == "fighting":
            self.status = "finished"

    def leave_route(self, room_vnum: Any) -> None:
        """Expire an unused or completed city admission after departure."""
        if self.status not in {"admitted", "finished"}:
            return
        if str(room_vnum) in MAGIC_SHOP_ROUTE_ROOMS:
            return
        self.status = "idle"
        self.started_at = None
        self.reason = None

    def combat_allowed(
        self, world: WorldSource | None, state: Mapping[str, Any],
        enemies: list[dict[str, Any]], *, now: float, nutrition_ready: bool,
        runtime_boundary: bool = False,
    ) -> bool:
        if self.status == "aborted":
            return False
        reason = None
        if runtime_boundary:
            reason = "city interruption reached the segment runtime boundary"
        elif self.status not in {"admitted", "fighting"}:
            reason = "another city interruption is outside the one-fight budget"
        elif not bounded_city_shop_transit_available(world, state):
            reason = "city attacker no longer satisfies source combat bounds"
        elif str(state.get("room_vnum")) not in MAGIC_SHOP_ROUTE_ROOMS:
            reason = "city interruption is outside the registered shopping route"
        elif len(enemies) != 1 or _number(enemies[0].get("isnpc")) != CITY_GREETER_VNUM:
            reason = "city interruption lacks one exact source-identified enemy"
        elif not nutrition_ready:
            reason = "city interruption exhausted nutrition reserves"
        else:
            mobile = world.mobiles[CITY_GREETER_VNUM]
            levels = _mobile_level_range(mobile.level)
            maximum_enemy_hp = _mobile_base_hp_range(
                levels,
                rank=mobile.rank,
                hp_modifier=mobile.hp_modifier,
            )[1]
            level = _number(enemies[0].get("level"))
            enemy_hp = _number(enemies[0].get("maxhp"))
            hp, maximum_hp = _number(state.get("hp")), _number(state.get("max_hp"))
            if level is None or not levels[0] <= level <= min(levels[1], state["level"] - 4):
                reason = "live city attacker level exceeds its source admission"
            elif enemy_hp is None or not 0 < enemy_hp <= maximum_enemy_hp:
                reason = "live city attacker health exceeds its source admission"
            elif hp is None or maximum_hp is None or hp < maximum_hp * 0.70:
                reason = "city interruption reached the health withdrawal floor"
            elif self.started_at is not None and now - self.started_at >= 60:
                reason = "city interruption reached its sixty-second deadline"
        if reason is not None:
            self.status, self.reason = "aborted", reason
            return False
        if self.started_at is None:
            self.started_at = now
        self.status = "fighting"
        return True

    def evidence(self, *, level: int | None, boot_id: str | None) -> dict[str, Any]:
        if self.status == "idle":
            return {}
        return {CITY_TRANSIT_KEY: {
            "status": self.status, "reason": self.reason, "level": level,
            "boot_id": boot_id, "source_mobile_vnum": CITY_GREETER_VNUM,
        }}
