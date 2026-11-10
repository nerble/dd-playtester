from dataclasses import replace
from pathlib import Path

import json

import pytest

from dd4tester import campaign
from dd4tester.campaign import _source_ranked_post_loss_plain_probe_allowed
from dd4tester.hunt_candidates import (
    ACT_AGGRESSIVE,
    ACT_SENTINEL,
    ACT_STAY_AREA,
    HuntCandidate,
    MobileProgram,
    MobileSource,
    MobReset,
    ObjectSource,
    RoomSource,
    WorldSource,
    load_world_source,
)
from dd4tester.populations import (
    plain_bounded_population,
    source_sequential_duplicate_reset_limit,
)
import dd4tester.populations as populations


def population_case():
    mobile = MobileSource(100, "clan member", "a clan member", 27, ACT_STAY_AREA, 0, "test.are")
    ring = ObjectSource(200, "ring", "a ring", 9, (0, 0, 0, 0), 0)
    world = WorldSource(
        mobiles={100: mobile},
        objects={200: ring},
        rooms={vnum: RoomSource(vnum, "hallway", "test.are") for vnum in (300, 301, 302)},
        mob_resets=[MobReset(100, vnum, 3, (200,), ((1, 200),)) for vnum in (300, 301, 302)],
    )
    candidate = HuntCandidate(
        status="reject", score=1, area_file="test.are", mobile_vnum=100,
        target="a clan member", target_keyword="clan", level=27, room_vnum=300,
        room_name="hallway", route=("south",), source_spawn_limit=3, room_spawn_count=1,
        boot_kills=0, loot=("a ring",), source_value=0, contained_coins=0, hazards=(),
        estimated_level_range=(25, 29), estimated_base_hp_range=(356, 1073),
        estimated_peak_round_damage=300, estimated_min_peak_round_damage=258,
        estimated_critical_hit_damage=100,
        autonomy_rejections=("target reset capacity exceeds one",), stay_area=True,
    )
    return candidate, world


def test_bounded_population_allows_isolation_research_without_reclassifying_target():
    candidate, world = population_case()
    assert plain_bounded_population(candidate, world)
    assert candidate.status == "reject"
    assert not candidate.autonomous_safe
    state = {"max_hp": 702, "character_class": "warrior"}
    assert not _source_ranked_post_loss_plain_probe_allowed(
        candidate, state, character_level=30, source_world=world,
    )


def test_source_ranked_plain_multiroom_population_is_capacity_researchable():
    candidate, world = population_case()
    world.mobiles[100] = replace(world.mobiles[100], act_flags=ACT_SENTINEL)
    world.objects.clear()
    world.mob_resets = [MobReset(100, vnum, 3, ()) for vnum in (300, 301, 302)]
    candidate = replace(
        candidate,
        status="caution",
        autonomy_rejections=(),
        loot=(),
    )

    assert plain_bounded_population(candidate, world)
    assert campaign._source_ranked_capacity_research_candidate(
        candidate,
        character_level=27,
        source_world=world,
    )
    # The source audit is required; candidate metadata alone must not turn a
    # multi-room population into a research route.
    assert not campaign._source_ranked_capacity_research_candidate(
        candidate,
        character_level=27,
    )


def test_bounded_population_reuses_world_reset_index():
    candidate, world = population_case()

    class CountingResets(list):
        iterations = 0

        def __iter__(self):
            type(self).iterations += 1
            return super().__iter__()

    world.mob_resets = CountingResets(world.mob_resets)
    populations._WORLD_RESET_INDEX_CACHE.pop(id(world), None)

    assert plain_bounded_population(candidate, world)
    assert plain_bounded_population(candidate, world)
    assert CountingResets.iterations == 1


def test_capacity_history_quarantines_source_ranked_plain_population():
    candidate, world = population_case()
    world.mobiles[100] = replace(world.mobiles[100], act_flags=ACT_SENTINEL)
    world.objects.clear()
    world.mob_resets = [MobReset(100, vnum, 3, ()) for vnum in (300, 301, 302)]
    candidate = replace(candidate, status="caution", autonomy_rejections=(), loot=())
    record = campaign._source_ranked_candidate_record(
        candidate,
        character_level=27,
    )
    failed_probe = {
        "phase": "source-ranked-hunt-test-100-300-27",
        "start_state_json": json.dumps(
            {
                "level": 27,
                "campaign_source_ranked_hunt_candidate": record,
            }
        ),
        "end_state_json": json.dumps(
            {
                "level": 27,
                "world_boot_id": "boot-1",
                "campaign_objective_kills": [],
            }
        ),
    }

    assert campaign._source_capacity_research_mobile_keys_from_segments(
        (failed_probe,),
        boot_id="boot-1",
        source_world=world,
    ) == frozenset({("test.are", 100)})

    productive_probe = {
        **failed_probe,
        "end_state_json": json.dumps(
            {
                "level": 27,
                "world_boot_id": "boot-1",
                "campaign_objective_kills": [
                    {"source_mobile_vnum": 100, "xp_gained": 200}
                ],
            }
        ),
    }
    assert campaign._source_capacity_research_mobile_keys_from_segments(
        (productive_probe,),
        boot_id="boot-1",
        source_world=world,
    ) == frozenset()


def sequential_duplicate_case():
    mobile = MobileSource(
        100,
        "living shadow",
        "a living shadow",
        43,
        ACT_SENTINEL,
        0,
        "tabernacle.are",
        description="It's pitch black. You can barely see it.",
    )
    world = WorldSource(
        mobiles={100: mobile},
        mob_resets=[MobReset(100, 200, 2, ())],
    )
    return world


def test_two_copy_sentinel_reset_is_only_admitted_for_sequential_selection():
    world = sequential_duplicate_case()
    assert source_sequential_duplicate_reset_limit(
        world, mobile_vnum=100, room_vnum="200",
    ) == 2


def test_four_copy_sentinel_reset_is_admitted_with_a_finite_sequential_bound():
    world = sequential_duplicate_case()
    world.mob_resets[0] = replace(world.mob_resets[0], maximum_count=4)

    assert source_sequential_duplicate_reset_limit(
        world, mobile_vnum=100, room_vnum="200",
    ) == 4


def test_sequential_duplicate_reset_allows_source_passive_perception_affects():
    world = sequential_duplicate_case()
    world.mobiles[100] = replace(world.mobiles[100], affected_flags=(1 << 2) | (1 << 9))

    assert source_sequential_duplicate_reset_limit(
        world, mobile_vnum=100, room_vnum=200,
    ) == 2


def test_goblin_fortress_visitors_are_a_sequential_source_population():
    world = load_world_source(
        Path("runs/dd4-source/server/area"),
        include_all_areas=True,
    )

    assert world.mobiles[20301].affected_flags == (1 << 2) | (1 << 9)
    assert source_sequential_duplicate_reset_limit(
        world, mobile_vnum=20301, room_vnum=20319,
    ) == 4


def test_stay_area_terra_kan_population_allows_harmless_healing_pill():
    world = load_world_source(
        Path("runs/dd4-source/server/area"),
        include_all_areas=True,
    )

    assert world.mobiles[17044].act_flags == ACT_STAY_AREA
    assert source_sequential_duplicate_reset_limit(
        world, mobile_vnum=17044, room_vnum=17258,
    ) == 4


@pytest.mark.parametrize("mutation", [
    "aggressive", "wanders", "affected", "program", "special",
    "armed", "object", "fifth_copy", "different_room", "second_reset",
])
def test_sequential_duplicate_reset_rejects_any_unverified_source_change(mutation):
    world = sequential_duplicate_case()
    if mutation == "aggressive":
        world.mobiles[100] = replace(
            world.mobiles[100], act_flags=ACT_SENTINEL | ACT_AGGRESSIVE,
        )
    elif mutation == "wanders":
        world.mobiles[100] = replace(world.mobiles[100], act_flags=0)
    elif mutation == "affected":
        world.mobiles[100] = replace(world.mobiles[100], affected_flags=1)
    elif mutation == "program":
        world.mobiles[100] = replace(
            world.mobiles[100],
            programs=(MobileProgram("fight_prog", commands=("say hello",)),),
        )
    elif mutation == "special":
        world.mobile_specials[100] = ("spec_poison",)
    elif mutation == "armed":
        world.mob_resets[0] = replace(
            world.mob_resets[0], equipment=((16, 200),),
        )
    elif mutation == "object":
        world.mob_resets[0] = replace(world.mob_resets[0], object_vnums=(200,))
    elif mutation == "fifth_copy":
        world.mob_resets[0] = replace(world.mob_resets[0], maximum_count=5)
    elif mutation == "different_room":
        world.mob_resets[0] = replace(world.mob_resets[0], room_vnum=201)
    else:
        world.mob_resets.append(MobReset(100, 200, 2, ()))
    assert source_sequential_duplicate_reset_limit(
        world, mobile_vnum=100, room_vnum=200,
    ) is None


@pytest.mark.parametrize("changes", [
    {"status": "eligible"}, {"level": 28}, {"area_file": "other.are"},
    {"source_spawn_limit": 5}, {"source_spawn_limit": True},
    {"room_spawn_count": 2}, {"room_spawn_count": True},
    {"specials": ("spec_poison",)}, {"equipped_weapons": ("a sword",)},
    {"autonomy_rejections": ("target reset capacity exceeds one", "target is aggressive")},
])
def test_bounded_population_rejects_changed_or_additional_source_rejections(changes):
    candidate, world = population_case()
    assert not plain_bounded_population(replace(candidate, **changes), world)


@pytest.mark.parametrize("hazard", [
    "aggressive", "unbounded_wanderer", "special", "random_room", "foreign_room",
    "unknown_object", "weapon", "potion", "armed_reset", "different_limit",
    "duplicate_room", "missing_origin", "extra_resets",
])
def test_bounded_population_requires_complete_plain_reset_proof(hazard):
    candidate, world = population_case()
    if hazard == "aggressive":
        world.mobiles[100] = replace(world.mobiles[100], act_flags=ACT_STAY_AREA | ACT_AGGRESSIVE)
    elif hazard == "unbounded_wanderer":
        world.mobiles[100] = replace(world.mobiles[100], act_flags=0)
    elif hazard == "special":
        world.mobile_specials[100] = ("spec_mage",)
    elif hazard == "random_room":
        world.rooms[301] = replace(world.rooms[301], random_exits=True)
    elif hazard == "foreign_room":
        world.rooms[301] = replace(world.rooms[301], area_file="other.are")
    elif hazard == "unknown_object":
        world.objects.clear()
    elif hazard in {"weapon", "potion"}:
        world.objects[200] = replace(world.objects[200], item_type=5 if hazard == "weapon" else 10)
    elif hazard == "armed_reset":
        world.mob_resets[1] = replace(world.mob_resets[1], equipment=((16, 200),))
    elif hazard == "different_limit":
        world.mob_resets[1] = replace(world.mob_resets[1], maximum_count=2)
    elif hazard == "duplicate_room":
        world.mob_resets[1] = replace(world.mob_resets[1], room_vnum=300)
    elif hazard == "missing_origin":
        world.mob_resets = world.mob_resets[1:]
    elif hazard == "extra_resets":
        world.mob_resets.extend([MobReset(100, 303, 3, ()), MobReset(100, 304, 3, ())])
    assert not plain_bounded_population(candidate, world)


@pytest.mark.parametrize("change", [None, "no_source", "no_output", "higher_nominal", "wider_fuzz"])
def test_bounded_population_fuzz_reuses_combat_proof_without_raising_live_ceiling(monkeypatch, change):
    candidate, world = population_case()
    candidate = replace(candidate, level=30, estimated_level_range=(28, 32))
    world.mobiles[100] = replace(world.mobiles[100], level=30)
    state = {"level": 30, "move": 100, "max_move": 100}
    if change == "higher_nominal":
        candidate = replace(candidate, level=31)
        world.mobiles[100] = replace(world.mobiles[100], level=31)
    elif change == "wider_fuzz":
        candidate = replace(candidate, estimated_level_range=(29, 33))
    monkeypatch.setattr(campaign, "_source_ranked_post_loss_plain_probe_allowed",
                        lambda *args, **kwargs: change != "no_output")
    assert campaign._source_ranked_capacity_research_in_current_band(
        candidate, state, character_level=30,
        source_world=None if change == "no_source" else world,
    ) is (change is None)
    assert campaign._source_ranked_maximum_level_offset(candidate) == 1
