from dataclasses import replace

import pytest

from dd4tester import hunt_candidates as hunts


def _world(*, endpoint_access: bool = True) -> hunts.WorldSource:
    area = "index.are"
    return hunts.WorldSource(
        mobiles={
            100: hunts.MobileSource(100, "target", "the target", 8, 0, 0, area),
            200: hunts.MobileSource(200, "guard", "the guard", 8, 0, 0, area),
        },
        rooms={
            3001: hunts.RoomSource(
                3001, "Recall", area,
                exits={"north": hunts.ExitSource("north", 7000, 0, -1)},
            ),
            7000: hunts.RoomSource(
                7000, "Transit", area,
                exits={"north": hunts.ExitSource("north", 7001, 0, -1)},
            ),
            7001: hunts.RoomSource(7001, "Target", area),
            7002: hunts.RoomSource(
                7002, "Guard post", area,
                exits={"west": hunts.ExitSource(
                    "west", 7001 if endpoint_access else 7000, 0, -1,
                )},
            ),
        },
        mob_resets=[hunts.MobReset(100, 7001, 1, ()), hunts.MobReset(200, 7002, 1, ())],
        mobile_specials={200: ("spec_guard",)},
    )


def _target(world: hunts.WorldSource) -> hunts.HuntCandidate:
    return next(
        candidate for candidate in hunts.rank_hunt_candidates(
            world, character_level=8, include_xp_only=True, include_all_areas=True,
        ) if candidate.mobile_vnum == 100
    )


def test_joining_wanderer_is_indexed_only_at_the_endpoint() -> None:
    world = _world(endpoint_access=False)
    world.rooms[7000].exits["north"] = hunts.ExitSource("north", 7001, 2, -1)
    assert _target(world).route_hazard_mobile_vnums == ()
    world.rooms[7002].exits["west"] = hunts.ExitSource("west", 7001, 0, -1)
    assert _target(world).route_hazard_mobile_vnums == (200,)


@pytest.mark.parametrize("special", ["spec_guard", "spec_poison", "unknown_special"])
def test_mutating_source_door_rebuilds_reachability(special: str) -> None:
    world = _world()
    world.mobile_specials[200] = (special,)
    world.mobiles[200] = replace(world.mobiles[200], act_flags=hunts.ACT_AGGRESSIVE)
    before = _target(world)
    assert before.route_hazard_mobile_vnums == (200,)
    world.rooms[7002].exits["west"] = hunts.ExitSource("west", 7001, 2, -1)
    assert _target(world).route_hazard_mobile_vnums == ()
    world.rooms[7002].exits["west"] = hunts.ExitSource("west", 7001, 0, -1)
    assert _target(world) == before


def test_reachable_wanderer_evidence_retains_source_reset_order() -> None:
    world = _world()
    world.mobiles[150] = replace(world.mobiles[200], vnum=150, short_description="the watchman")
    world.mobile_specials[150] = ("spec_guard",)
    world.mob_resets.append(hunts.MobReset(150, 7002, 1, ()))
    hazards = _target(world).hazards
    guard = "reachable combat-joining special: the guard L8"
    watchman = "reachable combat-joining special: the watchman L8"
    assert hazards.index(guard) < hazards.index(watchman)
    world.mob_resets.reverse()
    hazards = _target(world).hazards
    assert hazards.index(watchman) < hazards.index(guard)


def test_unreachable_wanderers_are_not_reclassified_for_every_target(monkeypatch) -> None:
    world = _world()
    for vnum in range(1000, 1050):
        world.mobiles[vnum] = replace(world.mobiles[200], vnum=vnum, level=50)
        world.rooms[vnum] = hunts.RoomSource(vnum, "Isolated", "remote.are")
        world.mobile_specials[vnum] = ("unknown_special",)
        world.mob_resets.append(hunts.MobReset(vnum, vnum, 1, ()))
    original = hunts._source_mobile_has_unsafe_special
    calls = 0

    def counted(*args, **kwargs):
        nonlocal calls
        if args[1] >= 1000:
            calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(hunts, "_source_mobile_has_unsafe_special", counted)
    _target(world)
    baseline_calls = calls
    calls = 0
    for vnum in range(101, 121):
        world.mobiles[vnum] = replace(world.mobiles[100], vnum=vnum)
        world.mob_resets.append(hunts.MobReset(vnum, 7001, 1, ()))
    _target(world)
    assert calls == baseline_calls
