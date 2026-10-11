from dataclasses import replace

import pytest

from dd4tester.carrier_inspection import CarrierEquipmentInspection, equipped_carrier_requirements
from dd4tester.character import CharacterSpec
from dd4tester.hunt_candidates import ACT_SENTINEL, MobileSource, MobReset, ObjectSource, RoomSource, WorldSource
from dd4tester.observations import GameEvent
from dd4tester.starter import StarterPolicy, daycare_ring_hunt_stops
from dd4tester.state import CharacterState


DESCRIPTION = "This doll has been hugged until there is almost nothing left."
LOOK = DESCRIPTION + "\nAn old doll is in perfect health.\n\nAn old doll is using:\n<worn on finger> a pink ice ring\n"


def _world() -> WorldSource:
    return WorldSource(
        mobiles={6605: MobileSource(
            6605, "doll old", "an old doll", 1, ACT_SENTINEL, -2, "test.are",
            room_description="An abused and old doll is here.", description=DESCRIPTION,
        )},
        objects={6601: ObjectSource(6601, "ring pink ice", "a pink ice ring", 9, (1, 0, 0, 0), 7000)},
        rooms={6605: RoomSource(6605, "Playroom", "test.are")},
        mob_resets=[MobReset(6605, 6605, 2, (6601,), ((1, 6601),))],
    )


def _start(controller: CarrierEquipmentInspection, **changes) -> bool:
    plan = dict(room="6605", selector="#123", mobile_vnum=6605, name="an old doll",
                description=DESCRIPTION, required=("pink ice ring",), level=31,
                boot="boot", visit=0, now=10)
    return controller.begin(**(plan | changes))


def _verified(controller: CarrierEquipmentInspection, **changes) -> bool:
    plan = dict(room="6605", selector="#123", mobile_vnum=6605, required=("pink ice ring",),
                level=31, boot="boot", visit=0, now=12)
    return controller.verified(**(plan | changes))


def test_single_carrier_source_plan_covers_only_its_actual_equipped_quantity() -> None:
    world = _world()
    options = dict(mobile_vnum=6605, reset_room="6605", object_vnums=(6601,))
    assert equipped_carrier_requirements(world, **options, missing=["pink ice ring"]) == ("pink ice ring",)
    assert equipped_carrier_requirements(world, **options, missing=["pink ice ring"] * 2) is None
    assert equipped_carrier_requirements(world, **options, missing=[]) is None


@pytest.mark.parametrize("failure", ("wrong_room", "carried_not_worn", "ambiguous_object", "wrong_vnum"))
def test_carrier_source_plan_rejects_unproved_reset_worn_identity(failure: str) -> None:
    world = _world()
    vnums = (6601,)
    if failure == "wrong_room":
        world.mob_resets = [replace(world.mob_resets[0], room_vnum=6604)]
    elif failure == "carried_not_worn":
        world.mob_resets = [replace(world.mob_resets[0], equipment=())]
    elif failure == "ambiguous_object":
        world.objects[999] = replace(world.objects[6601], vnum=999)
    else:
        vnums = (999,)
    assert equipped_carrier_requirements(
        world, mobile_vnum=6605, reset_room="6605", object_vnums=vnums, missing=["pink ice ring"],
    ) is None


def test_carrier_inspection_waits_for_complete_reply_and_counts_worn_item() -> None:
    controller = CarrierEquipmentInspection()
    assert _start(controller)
    controller.observe(LOOK[:25], now=11)
    controller.observe(LOOK[25:], now=11.2)
    assert not _verified(controller)
    controller.complete(now=11.3)
    assert _verified(controller)
    assert controller.records[0]["worn"] == {"pink ice ring": 1}


@pytest.mark.parametrize("reply", (
    "A ring is mentioned in a description.\nAn old doll is in perfect health.\n",
    DESCRIPTION + "\nAn old doll is in perfect health.\nYou peek at the inventory:\na pink ice ring\n",
    DESCRIPTION + "\nAnother doll is in perfect health.\nAn old doll is using:\n<worn on finger> a pink ice ring\n",
    DESCRIPTION + "\nAn old doll is in perfect health.\nAn old doll is using:\n<worn on body> a linen robe\n",
))
def test_description_inventory_and_other_target_text_do_not_prove_worn_loot(reply: str) -> None:
    controller = CarrierEquipmentInspection()
    assert _start(controller)
    controller.observe(reply, now=11)
    controller.complete(now=11.1)
    assert not _verified(controller)
    assert not _start(controller)


@pytest.mark.parametrize("change", (
    {"selector": "#124"}, {"room": "6604"}, {"level": 32}, {"boot": "later"},
    {"visit": 1}, {"now": 32}, {"required": ("pink ice ring", "pink ice ring")},
))
def test_carrier_receipt_never_survives_changed_context_or_quantity(change: dict) -> None:
    controller = CarrierEquipmentInspection()
    assert _start(controller)
    controller.observe(LOOK, now=11)
    controller.complete(now=11.1)
    assert not _verified(controller, **change)


def test_carrier_timeout_and_new_combat_fail_visibly_without_retry() -> None:
    for now, combat in ((15, False), (11, True)):
        controller = CarrierEquipmentInspection()
        assert _start(controller)
        controller.observe(DESCRIPTION, now=11)
        assert not controller.poll(room="6605", level=31, boot="boot", in_combat=combat, now=now)
        assert controller.receipt["status"] == "failed"
        controller.observe(LOOK, now=16)
        assert not _verified(controller)
        assert not _start(controller)


def test_lone_required_loot_carrier_is_inspected_before_consider(monkeypatch) -> None:
    stop = daycare_ring_hunt_stops()[0]
    spec = CharacterSpec.from_mapping({
        "name": "CarrierTest", "race": "human", "gender": "female", "class": "warrior",
        "subclass": None, "title": "",
    })
    policy = StarterPolicy(spec, "test-password", fastwalk_hunt_stops=(stop,), source_world=_world())
    policy.in_world = policy.prompt_ready = True
    policy.world_boot_id = "boot"
    policy.current_room = "6605"
    policy.fastwalk_attack_target = stop.target
    policy.room_targets["6605"] = [stop.target]
    policy.room_target_counts["6605"] = {stop.target: 1}
    policy.room_target_selectors["6605"] = {stop.target: ["#123"]}
    policy.room_target_selector_descriptions["6605"] = {"#123": stop.source_mobile_room_description}
    state = CharacterState(level=31, hp=740, max_hp=740, mana=290, max_mana=290,
                           move=500, max_move=500, room_vnum="6605", position=7)
    monkeypatch.setattr(policy, "_missing_fastwalk_required_items", lambda _state, _stop: ["pink ice ring"])
    decision = policy._consider_fastwalk_target(state)
    assert decision is not None and decision.command == "look #123"
    assert policy.fastwalk_attack_started is False
    policy.observe_text(LOOK)
    policy.observe_events([GameEvent("prompt_seen", "text", {})], state)
    following = policy._consider_fastwalk_target(state)
    assert following is not None and following.command == "consider #123"
    assert policy.room_target_counts["6605"][stop.target] == 1
