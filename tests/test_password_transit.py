from dataclasses import replace

import pytest

from dd4tester.hunt_candidates import (
    MobileProgram, MobileSource, MobReset, RoomSource, WorldSource,
    _source_mobile_is_route_hazard, _source_route_hazard_rejections,
    source_mobile_has_password_only_transfer,
)
from dd4tester.mobile_programs import explicit_speech_transfer_programs_only


PASSWORD = MobileProgram("speech_prog", "p Hesad sent me", ("mptransfer $n 101 group",))


def source():
    return WorldSource(
        mobiles={1: MobileSource(1, "teleporter", "a teleporter", 100, 2, 1000,
                                 "test.are", programs=(PASSWORD,))},
        rooms={100: RoomSource(100, "Entrance", "test.are"),
               101: RoomSource(101, "Destination", "test.are")},
        objects={}, mob_resets=[MobReset(1, 100, 1)],
    )


def test_password_transfer_is_not_a_walking_hazard_but_remains_relocation_evidence():
    world = source()
    mobile = world.mobiles[1]
    assert explicit_speech_transfer_programs_only(mobile.programs)
    assert source_mobile_has_password_only_transfer(world, mobile)
    assert mobile.player_relocation_programs == (PASSWORD,)
    assert not _source_mobile_is_route_hazard(world, mobile)
    assert not _source_route_hazard_rejections(world, (100,), character_level=45)


@pytest.mark.parametrize("program", [
    replace(PASSWORD, trigger="all_greet_prog", condition="100"),
    replace(PASSWORD, trigger="rand_prog", condition="100"),
    replace(PASSWORD, condition="p"),
    replace(PASSWORD, condition="Hesad sent me"),
    replace(PASSWORD, commands=("mptransfer all 101 group",)),
    replace(PASSWORD, commands=("mpforce $n say Hesad sent me",)),
    replace(PASSWORD, commands=("mptransfer $n 101 group", "mpkill $n")),
    replace(PASSWORD, commands=("mpat $n mptransfer 101",)),
])
def test_other_triggers_commands_and_broad_conditions_stay_excluded(program):
    assert not explicit_speech_transfer_programs_only((program,))


@pytest.mark.parametrize("hazard", ["aggressive", "wanders", "special", "loadout",
                                  "population", "missing_destination", "extra_program"])
def test_transit_proof_requires_fixed_unarmed_inert_source(hazard):
    world = source()
    if hazard == "aggressive":
        world.mobiles[1] = replace(world.mobiles[1], act_flags=34)
    elif hazard == "wanders":
        world.mobiles[1] = replace(world.mobiles[1], act_flags=0)
    elif hazard == "special":
        world.mobile_specials[1] = ("spec_cast_psionicist",)
    elif hazard == "loadout":
        world.mob_resets[0] = replace(world.mob_resets[0], object_vnums=(999,))
    elif hazard == "population":
        world.mob_resets[0] = replace(world.mob_resets[0], maximum_count=2)
    elif hazard == "missing_destination":
        del world.rooms[101]
    else:
        world.mobiles[1] = replace(world.mobiles[1], programs=(
            PASSWORD, MobileProgram("rand_prog", "10", ("mpkill $n",)),
        ))
    assert not source_mobile_has_password_only_transfer(world, world.mobiles[1])


def test_automatic_transfer_remains_a_hard_route_hazard():
    world = source()
    world.mobiles[1] = replace(world.mobiles[1], programs=(
        replace(PASSWORD, trigger="all_greet_prog", condition="100"),
    ))
    assert _source_mobile_is_route_hazard(world, world.mobiles[1])
    assert any("player-relocation" in reason for reason in
               _source_route_hazard_rejections(world, (100,), character_level=45))
