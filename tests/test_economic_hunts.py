from dataclasses import replace

import pytest

from dd4tester.economic_hunts import (
    economic_hunt_candidate, economic_hunt_runtime_issue, known_purse,
)
from dd4tester.fastwalks import Fastwalk
from dd4tester.hunt_candidates import (
    ExitSource, HuntCandidate, MobReset, MobileSource, ObjectSource, RoomSource, WorldSource,
    source_route_hazard_rejections,
)
from dd4tester.locator_paths import source_locator_path_is_safe
from dd4tester.populations import plain_bounded_population
from dd4tester.character import CharacterSpec
from dd4tester.starter import StarterPolicy
from dd4tester.state import CharacterState


def economic_fixture() -> tuple[HuntCandidate, WorldSource, dict]:
    world = WorldSource(
        mobiles={
            101: MobileSource(101, "buck", "a buck", 30, 2, 1000, "test.are"),
            102: MobileSource(102, "gardener", "a gardener", 25, 68, -1000, "test.are"),
        },
        objects={201: ObjectSource(201, "clippers", "some clippers", 5, (0, 0, 0, 13), 0)},
        mob_resets=[MobReset(101, 301, 1, ()),
                    MobReset(102, 302, 1, (201,), equipment=((16, 201),))],
        mobile_specials={102: ("spec_thief",)},
    )
    candidate = HuntCandidate(
        "reject", 100, "test.are", 101, "a buck", "buck", 30, 301, "a field",
        ("north",), 1, 1, 0, (), 0, 0, (), sentinel=True,
        autonomy_rejections=("an economic special mobile can reach the route",),
        route_special_mobile_vnums=(102,), source_damage_modifier=0,
    )
    state = {"level": 30, "currencies": {"platinum": 0, "gold": 6, "silver": 5, "copper": 8}}
    return candidate, world, state


def test_economic_only_travel_preserves_source_risk_and_quest_separation() -> None:
    candidate, world, state = economic_fixture()
    admitted = economic_hunt_candidate(candidate, state, world)
    assert admitted is not candidate
    assert admitted.status == "caution" and admitted.autonomous_safe
    assert admitted.route_economic_hunt_mobile_vnums == (102,)
    assert admitted.route_economic_source_rejections == candidate.autonomy_rejections
    assert candidate.status == "reject"
    route = Fastwalk("economic hunt", 1, 100, "1n", route_economic_hunt_mobile_vnums=(102,))
    assert not route.route_economic_special_mobile_vnums
    assert economic_hunt_runtime_issue(route, world, level=30, currencies=state["currencies"]) is None


def test_known_passive_target_affects_do_not_close_economic_route() -> None:
    candidate, world, state = economic_fixture()
    world.mobiles[101] = replace(
        world.mobiles[101],
        affected_flags=(1 << 3) | (1 << 5) | (1 << 13) | (1 << 20),
    )

    admitted = economic_hunt_candidate(candidate, state, world)

    assert admitted.status == "caution" and admitted.autonomous_safe
    assert admitted.route_economic_hunt_mobile_vnums == (102,)
    assert admitted.route_economic_source_rejections == candidate.autonomy_rejections


def test_economic_route_preserves_a_separately_audited_target_special() -> None:
    candidate, world, state = economic_fixture()
    world.mobile_specials[101] = ("spec_cast_cleric",)
    candidate = replace(
        candidate,
        specials=("spec_cast_cleric",),
        autonomy_rejections=(
            "an economic special mobile can reach the route",
            "target has special procedure spec_cast_cleric",
        ),
    )

    admitted = economic_hunt_candidate(candidate, state, world)

    assert admitted is not candidate
    assert admitted.route_economic_hunt_mobile_vnums == (102,)
    assert admitted.route_economic_source_rejections == (
        "an economic special mobile can reach the route",
    )
    assert admitted.autonomy_rejections == (
        "target has special procedure spec_cast_cleric",
    )
    assert not admitted.autonomous_safe


@pytest.mark.parametrize("change", [
    "rich", "missing_coins", "extra_rejection", "target_special", "target_weapon",
    "wanderer", "aggressive_target", "target_affect", "unknown_object",
    "spell_item", "thief_aggressive", "thief_special", "thief_capacity",
    "thief_damage_modifier", "thief_damage_bonus", "target_hp_bonus",
])
def test_economic_route_does_not_waive_other_hazards(change: str) -> None:
    candidate, world, state = economic_fixture()
    if change == "rich":
        state["currencies"]["gold"] = 13
    elif change == "missing_coins":
        del state["currencies"]["copper"]
    elif change == "extra_rejection":
        candidate = replace(candidate, autonomy_rejections=candidate.autonomy_rejections + (
            "route crosses a higher-level aggressive reset",))
    elif change == "target_special":
        candidate = replace(candidate, specials=("spec_poison",))
    elif change == "target_weapon":
        candidate = replace(candidate, equipped_weapons=("a sword",))
    elif change == "wanderer":
        candidate = replace(candidate, sentinel=False)
    elif change == "aggressive_target":
        world.mobiles[101] = replace(world.mobiles[101], act_flags=34)
    elif change == "target_affect":
        world.mobiles[101] = replace(world.mobiles[101], affected_flags=128)
    elif change == "unknown_object":
        del world.objects[201]
    elif change == "spell_item":
        world.objects[201] = replace(world.objects[201], item_type=4)
    elif change == "thief_aggressive":
        world.mobiles[102] = replace(world.mobiles[102], act_flags=100)
    elif change == "thief_special":
        world.mobile_specials[102] = ("spec_thief", "spec_poison")
    elif change == "thief_capacity":
        world.mob_resets[1] = replace(world.mob_resets[1], maximum_count=2)
    elif change == "thief_damage_modifier":
        world.mobiles[102] = replace(world.mobiles[102], damage_modifier=20)
    elif change == "thief_damage_bonus":
        world.objects[201] = replace(world.objects[201], affects=((19, 50),))
    elif change == "target_hp_bonus":
        world.objects[202] = ObjectSource(202, "armor", "armor", 9, (0, 0, 0, 0), 0,
                                        affects=((13, 100),))
        world.mob_resets[0] = replace(world.mob_resets[0], equipment=((5, 202),))
    assert economic_hunt_candidate(candidate, state, world) is candidate


@pytest.mark.parametrize("purse,allowed", [(1250, True), (1251, False)])
def test_live_purse_gate_is_bounded_and_rechecked(purse: int, allowed: bool) -> None:
    _candidate, world, _state = economic_fixture()
    currencies = {"platinum": 0, "gold": 0, "silver": 0, "copper": purse}
    route = Fastwalk("economic hunt", 1, 100, "1n", route_economic_hunt_mobile_vnums=(102,))
    assert (economic_hunt_runtime_issue(route, world, level=30, currencies=currencies) is None) == allowed
    world.mobile_specials[102] = ("spec_cast_mage",)
    assert economic_hunt_runtime_issue(route, world, level=30, currencies=currencies) is not None


def test_full_loadout_economic_hunt_audit_only_waives_noncombat_transit() -> None:
    _candidate, world, _state = economic_fixture()
    world.rooms = {
        302: RoomSource(302, "route origin", "test.are"),
        303: RoomSource(303, "route endpoint", "test.are"),
    }

    transit = source_route_hazard_rejections(
        world,
        (302, 303),
        character_level=30,
        combat_at_destination=False,
        economic_hunt_mobile_vnums=(102,),
    )
    combat = source_route_hazard_rejections(
        world,
        (302, 303),
        character_level=30,
        combat_at_destination=True,
        economic_hunt_mobile_vnums=(102,),
    )

    assert not any("non-safe special mobile" in rejection for rejection in transit)
    assert any("non-safe special mobile" in rejection for rejection in combat)


def test_unknown_or_invalid_currency_never_counts_as_zero() -> None:
    assert known_purse({}) is None
    assert known_purse({"platinum": 0, "gold": False, "silver": 0, "copper": 0}) is None
    assert known_purse({"platinum": 0, "gold": "-1", "silver": 0, "copper": 0}) is None


def test_economic_identity_survives_candidate_checkpoint_round_trip() -> None:
    from dd4tester.campaign import (
        _source_ranked_candidate_from_record, _source_ranked_candidate_record,
    )

    candidate, world, state = economic_fixture()
    admitted = economic_hunt_candidate(candidate, state, world)
    record = _source_ranked_candidate_record(admitted, character_level=30)
    restored = _source_ranked_candidate_from_record(record)
    assert restored is not None
    assert restored.route_economic_hunt_mobile_vnums == (102,)
    assert restored.route_economic_source_rejections == candidate.autonomy_rejections


def test_live_purse_change_returns_before_an_outbound_action() -> None:
    _candidate, world, _state = economic_fixture()
    policy = StarterPolicy(
        CharacterSpec(name="Sample", password_env="TEST_PASSWORD", race="human",
                      gender="male", character_class="warrior"), "unused",
        source_world=world,
        fastwalk_route=Fastwalk("economic hunt", 1, 100, "1n",
                               route_economic_hunt_mobile_vnums=(102,)),
    )
    state = CharacterState(level=30, room_vnum="3001", currencies={
        "platinum": 0, "gold": 13, "silver": 0, "copper": 0,
    })
    decision = policy._fastwalk_research_decision(state)
    assert decision is not None and decision.command == "recall"
    assert policy.fastwalk_returning
    assert policy.fastwalk_emergency_recall_pending
    assert policy.fastwalk_abort_reason == "ordinary XP route exceeded its known economic coin reserve"


def population_economic_fixture():
    candidate, world, state = economic_fixture()
    world.mobiles[101] = replace(world.mobiles[101], act_flags=64)
    world.mob_resets = [MobReset(101, room, 4, ()) for room in (301, 303, 304, 305)] + [
        MobReset(102, 302, 1, ()),
    ]
    world.rooms = {room: RoomSource(room, "field", "test.are") for room in (301, 302, 303, 304, 305)}
    world.rooms[301] = replace(world.rooms[301], exits={"north": ExitSource("north", 302, 0, -1)})
    world.rooms[302] = replace(world.rooms[302], exits={"south": ExitSource("south", 301, 0, -1)})
    candidate = replace(candidate, source_spawn_limit=4, sentinel=False, stay_area=True,
                        autonomy_rejections=("target reset capacity exceeds one",) + candidate.autonomy_rejections)
    return candidate, world, state


def test_economic_population_remains_capacity_research_with_original_risks() -> None:
    candidate, world, state = population_economic_fixture()
    admitted = economic_hunt_candidate(candidate, state, world)
    assert admitted is not candidate
    assert admitted.status == "reject" and not admitted.autonomous_safe
    assert admitted.autonomy_rejections == ("target reset capacity exceeds one",)
    assert admitted.route_economic_source_rejections == candidate.autonomy_rejections
    assert plain_bounded_population(admitted, world)


@pytest.mark.parametrize("change", ["fifth_reset", "duplicate_room", "spell_loadout", "rich"])
def test_economic_population_requires_every_existing_population_gate(change: str) -> None:
    candidate, world, state = population_economic_fixture()
    if change == "fifth_reset":
        world.mob_resets.append(MobReset(101, 306, 4, ()))
        world.rooms[306] = RoomSource(306, "field", "test.are")
    elif change == "duplicate_room":
        world.mob_resets[1] = replace(world.mob_resets[1], room_vnum=301)
    elif change == "spell_loadout":
        world.objects[202] = ObjectSource(202, "potion", "a potion", 10, (0, 0, 0, 0), 0)
        world.mob_resets[1] = replace(world.mob_resets[1], object_vnums=(202,))
    elif change == "rich":
        state["currencies"]["gold"] = 13
    assert economic_hunt_candidate(candidate, state, world) is candidate


def test_population_locator_keeps_economic_risk_explicit_and_other_hazards_closed() -> None:
    candidate, world, state = population_economic_fixture()
    admitted = economic_hunt_candidate(candidate, state, world)
    assert not source_locator_path_is_safe(world, (301,), character_level=30)
    assert source_locator_path_is_safe(
        world, (301,), character_level=30,
        economic_special_mobile_vnums=admitted.route_economic_hunt_mobile_vnums,
    )
    world.mobile_specials[102] = ("spec_assassin",)
    assert not source_locator_path_is_safe(
        world, (301,), character_level=30,
        economic_special_mobile_vnums=admitted.route_economic_hunt_mobile_vnums,
    )
