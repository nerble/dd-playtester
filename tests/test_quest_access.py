from dataclasses import replace

import pytest

from dd4tester.campaign import _quest_source_preflight_issue, _quest_target_runner_options
from dd4tester.equipment import ITEM_KEY
from dd4tester.hunt_candidates import (
    ACT_AGGRESSIVE, ACT_SENTINEL, ExitSource, MobileProgram, MobileSource, MobReset,
    ObjectSource, RoomSource, WorldSource,
)
from dd4tester.quest_access import (
    circus_quest_admission,
    tentusks_key_source_chain,
)
from dd4tester.quests import snapshot_quest_status


def _world():
    rooms = {
        vnum: RoomSource(vnum, str(vnum), "circus.are", exits={})
        for vnum in (3001, 4402, 4415, 4416, 4444)
    }
    rooms[3001].exits["south"] = ExitSource("south", 4402, 0, -1)
    rooms[4402].exits["south"] = ExitSource("south", 4415, 0, -1)
    rooms[4415].exits["south"] = ExitSource("south", 4416, 33, 4400, reset_state=2)
    rooms[4416].exits["down"] = ExitSource("down", 4444, 0, -1)
    return WorldSource(
        rooms=rooms,
        mobiles={4400: MobileSource(4400, "ticket clerk", "the Ticket Clerk", 31,
                                   ACT_SENTINEL, 250, "circus.are")},
        mob_resets=[MobReset(4400, 4402, 1, (4400,))],
        objects={
            4400: ObjectSource(4400, "ticket", "a ticket", ITEM_KEY, (4415, 0, 0, 0), 0),
            585: ObjectSource(585, "coin serenos", "the coin of Serenos", 8, (0, 0, 0, 0), 0),
        },
        shopkeepers={4400},
    )


def _tentusks_world(*, gate_key_vnum=25405):
    rooms = {
        3001: RoomSource(3001, "Recall", "midgaard.are"),
        25426: RoomSource(25426, "Murky Water", "tentusks.are"),
        25429: RoomSource(25429, "Great Hall", "tentusks.are"),
        25430: RoomSource(25430, "Hall of the Portals", "tentusks.are"),
        25530: RoomSource(25530, "Wastelands", "tentusks.are"),
    }
    rooms[3001].exits["north"] = ExitSource("north", 25426, 0, -1)
    rooms[25426].exits["north"] = ExitSource("north", 25429, 0, -1)
    rooms[25429].exits["north"] = ExitSource(
        "north", 25430, 7, gate_key_vnum, reset_state=2,
    )
    rooms[25430].exits["east"] = ExitSource("east", 25530, 0, -1)
    return WorldSource(
        rooms=rooms,
        mobiles={
            25405: MobileSource(
                25405, "octopus", "an octopus", 26, ACT_SENTINEL, 0,
                "tentusks.are",
            ),
            25408: MobileSource(
                25408, "broken statue", "a broken statue", 60, 0, 750,
                "tentusks.are",
                programs=(MobileProgram(
                    "give_prog", "badly chipped stone head",
                    ("mpoload 25405", "unlock n", "mpjunk head", "mpjunk key"),
                ),),
            ),
        },
        objects={
            25404: ObjectSource(
                25404, "badly chipped stone head", "a stone head", 13,
                (0, 1, 6, 11), 0,
            ),
            25405: ObjectSource(
                25405, "stone key", "a stone key", ITEM_KEY,
                (25429, 1, 6, 11), 0,
            ),
        },
        mob_resets=[
            MobReset(25405, 25426, 1, (25404,)),
            MobReset(25408, 25429, 1, ()),
        ],
    )


def test_circus_retrieval_confirms_ticket_before_unlocking():
    world = _world()
    quest_state = {"active": 1, "type": "retrieve", "room_vnum": 4444, "object_vnum": 585}
    quest = snapshot_quest_status(quest_state)
    assert _quest_source_preflight_issue(
        world, quest, execution="quest-target-run", character_level=9,
    ) is None
    options = _quest_target_runner_options(
        world, {"level": 9, "quest_status": quest_state},
        character_level=9, policy_id="quest-target-run",
    )
    assert options["fastwalk_route"].commands == ("south",)
    purchase, retrieval = options["fastwalk_hunt_stops"]
    assert purchase.actions == ("buy ticket",)
    assert purchase.required_items == ("a ticket",)
    assert purchase.source_loot_object_vnums == (4400,)
    assert retrieval.route == ("south", "unlock south", "open south", "south", "down")
    assert retrieval.source_loot_object_vnums == (585,)
    assert not options["use_sanctuary_potions"]


@pytest.mark.parametrize("change", ["key", "stock", "shop", "door", "duplicate", "circular", "hazard"])
def test_circus_admission_rejects_changed_access_contract(change):
    world = _world()
    if change == "key":
        world.objects.pop(4400)
    elif change == "stock":
        world.mob_resets[0] = replace(world.mob_resets[0], object_vnums=())
    elif change == "shop":
        world.shopkeepers.clear()
    elif change == "door":
        world.rooms[4415].exits["south"] = ExitSource("south", 4416, 33, 999, reset_state=2)
    elif change == "duplicate":
        world.objects[999] = replace(world.objects[4400], vnum=999)
    elif change == "circular":
        world.mob_resets[0] = replace(world.mob_resets[0], room_vnum=4416)
    elif change == "hazard":
        world.mobiles[999] = MobileSource(999, "attacker", "an attacker", 12,
                                         ACT_AGGRESSIVE | ACT_SENTINEL, 0, "circus.are")
        world.mob_resets.append(MobReset(999, 4444, 1, ()))
    assert circus_quest_admission(world, 4444, character_level=9) is None


def test_circus_ticket_does_not_authorize_a_kill_quest():
    world = _world()
    world.mobiles[999] = MobileSource(999, "target", "a target", 9, ACT_SENTINEL, 0, "circus.are")
    world.mob_resets.append(MobReset(999, 4444, 1, ()))
    quest = snapshot_quest_status({"active": 1, "type": "kill", "room_vnum": 4444, "mob_vnum": 999})
    assert _quest_source_preflight_issue(
        world, quest, execution="quest-target-run", character_level=9, character_max_hp=123,
    ) is not None


def test_tentusks_key_chain_keeps_mobile_and_object_vnums_separate():
    world = _tentusks_world()
    chain = tentusks_key_source_chain(world, 25530)

    assert chain is not None
    assert chain.key_object_vnum == 25405
    assert chain.head_object_vnum == 25404
    assert chain.head_carrier_mobile_vnum == 25405
    assert chain.head_carrier_room_vnum == 25426
    assert chain.unlocker_mobile_vnum == 25408


def test_tentusks_key_chain_rejects_a_changed_gate_key():
    world = _tentusks_world(gate_key_vnum=999)
    assert tentusks_key_source_chain(world, 25530) is None
