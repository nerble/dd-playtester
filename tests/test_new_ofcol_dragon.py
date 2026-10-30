import json
from dataclasses import replace
from pathlib import Path

import dd4tester.campaign as campaign_module
from dd4tester.hunt_candidates import load_world_source, rank_hunt_candidates


SOURCE = Path("runs/dd4-source/server/area")


def _dragon_candidate_and_world():
    world = load_world_source(SOURCE, include_all_areas=True)
    candidates = rank_hunt_candidates(
        world,
        character_level=39,
        character_class="warrior",
        character_subclass="knight",
        character_alignment=-7,
        character_max_hp=937,
        include_xp_only=True,
        include_level_ceiling_candidates=True,
        level_ceiling_offset=5,
        include_all_areas=True,
        recall_origins={0: 3001},
    )
    candidate = next(
        item
        for item in candidates
        if item.mobile_vnum == 631 and item.room_vnum == 693
    )
    return candidate, world


def _state():
    return {
        "world_boot_id": "test-boot",
        "character_class": "Warrior",
        "character_subclass": "Knight",
        "character_alignment": -7,
        "combat_pouch_potions": {"purple": 1},
        "verified_combat_pouch_potions": {"purple": 1},
    }


def _ra_candidate_and_world():
    world = load_world_source(
        SOURCE,
        include_all_areas=True,
        live_deployment=True,
    )
    candidates = rank_hunt_candidates(
        world,
        character_level=41,
        character_class="knight",
        character_subclass="knight",
        character_alignment=97,
        character_max_hp=987,
        include_xp_only=True,
        include_level_ceiling_candidates=True,
        level_ceiling_offset=5,
        include_all_areas=True,
        recall_origins={3001: 3001},
    )
    candidate = next(
        item
        for item in candidates
        if item.mobile_vnum == 919 and item.room_vnum == 931
    )
    return candidate, world


def test_exact_ra_mixed_breath_shape_is_admitted_with_live_protections():
    candidate, world = _ra_candidate_and_world()
    state = {
        **_state(),
        "level": 41,
        "max_hp": 987,
        "hp": 987,
        "room_vnum": "3054",
        "affects": [{"name": "detect invis", "duration": "10"}],
    }

    assert campaign_module._source_ra_breath_shape_allowed(candidate, world)
    assert campaign_module._audited_source_special_candidate_allowed(
        candidate,
        state=state,
        character_max_hp=987,
        source_world=world,
    )
    assert campaign_module._source_ranked_special_candidate_in_live_level_ceiling(
        candidate,
        character_level=41,
    )
    target_stop = next(
        stop
        for stop in campaign_module._source_ranked_hunt_stops(
            candidate,
            world,
            character_level=41,
            state=state,
        )
        if stop.target is not None
    )
    assert target_stop.allow_lucky_consider is True
    assert target_stop.maximum_level_offset == 5
    assert campaign_module._select_source_ranked_hunt_candidate(
        (candidate,),
        state,
        world=world,
        character_level=41,
        character_max_hp=987,
    ) == candidate


def test_ra_breath_exception_does_not_generalize_to_another_reset():
    candidate, world = _ra_candidate_and_world()
    altered = replace(candidate, room_vnum=930)

    assert not campaign_module._source_ra_breath_shape_allowed(altered, world)
    assert not campaign_module._audited_source_special_candidate_allowed(
        altered,
        state=_state(),
        character_max_hp=987,
        source_world=world,
    )


def test_ra_lucky_consider_repair_uses_raw_level_line_not_target_hp():
    candidate, world = _ra_candidate_and_world()
    policy_id = campaign_module._source_ranked_policy_id(
        candidate,
        character_level=41,
    )
    state = {
        **_state(),
        "level": 41,
        "max_hp": 987,
        "campaign_research_results": {
            policy_id: {
                "boot_id": "boot-1",
                "observed": True,
                "viable": False,
                "completed_kill": False,
                "consider_viable": False,
            }
        },
        "campaign_fastwalk_source_consider_outcomes": {
            policy_id: False,
        },
    }

    class EventStore:
        def list_recent_events(self, run_id, *, limit):
            assert run_id == 9001
            assert limit == 512
            return [
                {
                    "kind": "command",
                    "payload_json": json.dumps({"command": "consider #578"}),
                },
                {
                    "kind": "response",
                    "payload_json": json.dumps(
                        {
                            "text": (
                                "Ra the Sun God says 'Do you feel lucky, punk?'.\n"
                                "Also, he is much healthier than you."
                            )
                        }
                    ),
                },
            ]

    segments = [
        {
            "phase": policy_id,
            "run_id": 9001,
            "end_state_json": json.dumps(
                {
                    "dead": False,
                    "campaign_xp_loss_observed": False,
                    "in_combat": False,
                }
            ),
        }
    ]

    repaired = campaign_module._repair_source_ranked_ra_lucky_consider_history(
        state,
        segments,
        storage=EventStore(),
        source_world=world,
    )

    result = repaired["campaign_research_results"][policy_id]
    assert result["consider_viable"] is True
    assert result["source_consider_repair"]["original_consider_viable"] is False
    assert repaired["campaign_fastwalk_source_consider_outcomes"][policy_id] is True


def test_exact_gold_dragon_shape_is_admitted_with_sanctuary():
    candidate, world = _dragon_candidate_and_world()
    state = _state()

    assert campaign_module._source_ancient_gold_dragon_breath_shape_allowed(
        candidate,
        world,
    )
    assert campaign_module._audited_source_special_candidate_allowed(
        candidate,
        state=state,
        character_max_hp=937,
        source_world=world,
    )
    selected = campaign_module._select_source_ranked_hunt_candidate(
        (candidate,),
        state,
        world=world,
        character_level=39,
        character_max_hp=937,
    )
    assert selected == candidate


def test_breath_exception_does_not_generalize_to_another_room():
    candidate, world = _dragon_candidate_and_world()
    altered = replace(candidate, room_vnum=692)

    assert not campaign_module._source_ancient_gold_dragon_breath_shape_allowed(
        altered,
        world,
    )
    assert not campaign_module._audited_source_special_candidate_allowed(
        altered,
        state=_state(),
        character_max_hp=937,
        source_world=world,
    )
