"""Source-bounded city shopping and one session-local defensive interruption."""

from dataclasses import dataclass, replace
from typing import Any, Mapping, Sequence

from .fastwalks import Fastwalk
from .hunt_candidates import (
    WorldSource, _mobile_base_hp_range, _mobile_level_range,
    _shortest_paths_from,
    source_mobile_route_program_attacker_is_bounded,
    source_route_hazard_rejections,
    source_route_movement_cost,
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
_FIELD_CITY_DETOUR_MAX_EXTRA_COMMANDS = 16
_FIELD_CITY_DETOUR_MOVE_RESERVE = 15
_FASTWALK_DIRECTION_CODES = {
    "north": "n", "east": "e", "south": "s", "west": "w",
    "up": "u", "down": "d",
}


@dataclass(frozen=True)
class FieldCityDetour:
    route: Fastwalk
    blocked_locations: tuple[str, ...]
    boundary_room_vnum: int
    original_city_commands: tuple[str, ...]
    detour_city_commands: tuple[str, ...]
    ground_move_delta: int
    flying_move_delta: int
    required_ground_move: int
    required_flying_move: int

    def evidence(self) -> dict[str, Any]:
        return {
            "blocked_locations": list(self.blocked_locations),
            "boundary_room_vnum": self.boundary_room_vnum,
            "original_city_commands": list(self.original_city_commands),
            "detour_city_commands": list(self.detour_city_commands),
            "ground_move_delta": self.ground_move_delta,
            "flying_move_delta": self.flying_move_delta,
            "required_ground_move": self.required_ground_move,
            "required_flying_move": self.required_flying_move,
        }


def _normalized_room_name(value: Any) -> str:
    return " ".join(str(value).casefold().split()).removeprefix("the ")


def _route_room_path(
    world: WorldSource,
    origin: int,
    commands: Sequence[str],
) -> tuple[int, ...] | None:
    room = world.rooms.get(origin)
    if room is None:
        return None
    path = [origin]
    for raw_command in commands:
        command = str(raw_command).casefold().strip()
        if command.startswith(("open ", "unlock ", "pick ")):
            continue
        exit_source = room.exits.get(command)
        if exit_source is None:
            return None
        room = world.rooms.get(exit_source.destination)
        if room is None:
            return None
        path.append(room.vnum)
    return tuple(path)


def _fastwalk_notation(commands: Sequence[str]) -> str | None:
    segments = []
    for raw_command in commands:
        command = str(raw_command).casefold().strip()
        if command in _FASTWALK_DIRECTION_CODES:
            segments.append(_FASTWALK_DIRECTION_CODES[command])
        elif command.startswith(("open ", "unlock ", "pick ")):
            segments.append(command)
        else:
            return None
    return ";".join(segments) if segments else None


def field_city_detour_for_locations(
    world: WorldSource | None,
    route: Fastwalk | None,
    locations: Sequence[str],
    *,
    character_level: int,
    character_max_hp: int | None,
) -> FieldCityDetour | None:
    """Find one source-checked city-prefix detour around a live greet mobile."""
    if (
        world is None
        or route is None
        or route.route_origin_room_vnum != 3001
        or route.route_origin_recall_index != 0
        or route.return_commands
        or character_level < 2
        or not locations
        or len(locations) > 8
    ):
        return None
    mobile = world.mobiles.get(CITY_GREETER_VNUM)
    if mobile is None or not source_mobile_route_program_attacker_is_bounded(
        world,
        mobile,
        character_level=character_level,
        character_max_hp=character_max_hp,
    ):
        return None

    normalized_locations = tuple(dict.fromkeys(
        _normalized_room_name(location)
        for location in locations
        if _normalized_room_name(location)
    ))
    if not normalized_locations:
        return None
    rooms_by_name: dict[str, set[int]] = {}
    for room in world.rooms.values():
        if room.area_file.casefold() == "midgaard.are":
            rooms_by_name.setdefault(_normalized_room_name(room.name), set()).add(
                room.vnum
            )
    if any(name not in rooms_by_name for name in normalized_locations):
        return None
    blocked_rooms = set().union(*(rooms_by_name[name] for name in normalized_locations))

    original_commands = route.commands
    original_path = _route_room_path(world, 3001, original_commands)
    if original_path is None:
        return None
    room = world.rooms[3001]
    original_prefix_rooms = [3001]
    boundary_command_end = None
    for command_index, raw_command in enumerate(original_commands):
        command = str(raw_command).casefold().strip()
        if command.startswith(("open ", "unlock ", "pick ")):
            continue
        exit_source = room.exits.get(command)
        if exit_source is None:
            return None
        room = world.rooms.get(exit_source.destination)
        if room is None:
            return None
        original_prefix_rooms.append(room.vnum)
        if room.area_file.casefold() != "midgaard.are":
            boundary_command_end = command_index + 1
            break
    if boundary_command_end is None:
        return None
    original_prefix_commands = original_commands[:boundary_command_end]
    boundary_path_index = len(original_prefix_rooms) - 1
    if blocked_rooms.isdisjoint(original_prefix_rooms):
        return None
    later_route_names = {
        _normalized_room_name(world.rooms[room_vnum].name)
        for room_vnum in original_path[boundary_path_index:]
    }
    if later_route_names.intersection(normalized_locations):
        return None

    boundary_room_vnum = original_prefix_rooms[-1]
    alternative = _shortest_paths_from(
        world.rooms,
        3001,
        blocked_rooms=blocked_rooms,
    ).get(boundary_room_vnum)
    if alternative is None:
        return None
    detour_commands, detour_path, _ = alternative
    if (
        not blocked_rooms.isdisjoint(detour_path)
        or detour_commands == original_prefix_commands
        or len(detour_commands)
        > len(original_prefix_commands) + _FIELD_CITY_DETOUR_MAX_EXTRA_COMMANDS
        or world.rooms[detour_path[-1]].area_file.casefold() == "midgaard.are"
    ):
        return None
    if any(
        world.rooms[room_vnum].random_exits
        for room_vnum in detour_path
        if room_vnum in world.rooms
    ):
        return None

    hazards = source_route_hazard_rejections(
        world,
        detour_path,
        character_level=character_level,
        combat_at_destination=False,
    )
    expected_greeter_warning = (
        "a program-triggered attacker inside the useful XP band can reach the "
        f"route: {mobile.short_description}"
    )
    if hazards and hazards != (expected_greeter_warning,):
        return None

    updated_commands = (*detour_commands, *original_commands[boundary_command_end:])
    updated_path = _route_room_path(world, 3001, updated_commands)
    notation = _fastwalk_notation(updated_commands)
    if (
        updated_path is None
        or updated_path[-1] != original_path[-1]
        or notation is None
    ):
        return None
    if route.route_preflight_command:
        preflight_names = tuple(dict.fromkeys(
            _normalized_room_name(world.rooms[room_vnum].name)
            for room_vnum in updated_path
        ))
        updated_route = replace(
            route,
            notation=notation,
            route_preflight_route_room_names=preflight_names,
        )
    else:
        updated_route = replace(route, notation=notation)

    ground_old = source_route_movement_cost(world, original_path)
    ground_new = source_route_movement_cost(world, updated_path)
    flying_old = source_route_movement_cost(world, original_path, flying=True)
    flying_new = source_route_movement_cost(world, updated_path, flying=True)
    return FieldCityDetour(
        route=updated_route,
        blocked_locations=normalized_locations,
        boundary_room_vnum=boundary_room_vnum,
        original_city_commands=original_prefix_commands,
        detour_city_commands=tuple(detour_commands),
        ground_move_delta=ground_new - ground_old,
        flying_move_delta=flying_new - flying_old,
        required_ground_move=ground_new + _FIELD_CITY_DETOUR_MOVE_RESERVE,
        required_flying_move=flying_new + _FIELD_CITY_DETOUR_MOVE_RESERVE,
    )


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
    """Return Midgaard route rooms where the visible Drunk can greet the player."""
    if world is None or origin != 3001:
        return ()
    greeter = world.mobiles.get(CITY_GREETER_VNUM)
    if greeter is None or greeter.area_file != "midgaard.are" or not greeter.attack_programs:
        return ()
    # DD4's Drunk greet_prog attacks visible entrants regardless of alignment.
    names = [world.rooms[vnum].name for vnum in (3054, origin)
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

    def allows_proactive_hunt(self, room_vnum: Any) -> bool:
        """Keep field hunts out of the city corridor during bounded transit."""
        return (
            self.status == "idle"
            or str(room_vnum) not in MAGIC_SHOP_ROUTE_ROOMS
        )

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
