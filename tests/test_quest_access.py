from dataclasses import replace

import pytest

from dd4tester.campaign import _quest_source_preflight_issue, _quest_target_runner_options
from dd4tester.equipment import ITEM_KEY
from dd4tester.hunt_candidates import (
    ACT_AGGRESSIVE, ACT_SENTINEL, ExitSource, MobileSource, MobReset,
    ObjectSource, RoomSource, WorldSource,
)
from dd4tester.quest_access import circus_quest_admission
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
