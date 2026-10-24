from dataclasses import replace

import dd4tester.campaign as campaign_module
from dd4tester.hunt_candidates import load_world_source, rank_hunt_candidates
from dd4tester.source_paths import current_source_directory


def _candidate_and_world():
    world = load_world_source(current_source_directory(), include_all_areas=True)
    candidates = rank_hunt_candidates(
        world,
        character_level=39,
        character_class="Warrior",
        character_subclass="Knight",
        character_alignment=933,
        character_max_hp=919,
        include_xp_only=True,
        include_level_ceiling_candidates=True,
        level_ceiling_offset=5,
        include_all_areas=True,
        recall_origins={0: 3001},
    )
    candidate = next(
        candidate
        for candidate in candidates
        if candidate.mobile_vnum == 9934 and candidate.room_vnum == 9943
    )
    return world, candidate


def _state(candidate, *, source_policy_ids):
    return {
        "level": 39,
        "max_hp": 919,
        "hp": 919,
        "room_vnum": "3054",
        "world_boot_id": "boot-1",
        campaign_module._SOURCE_REVISION_KEY: "source-1",
        campaign_module._SOURCE_RANKED_TRANSIT_HAZARDS_KEY: {
            "9933": {
                "boot_id": "boot-1",
                "level": 39,
                "source_revision": "source-1",
                "mobile_vnum": 9933,
                "source_policy_ids": list(source_policy_ids),
            }
        },
        "campaign_research_results": {},
    }


def test_kaladim_mirror_route_risk_is_exact_and_selectable():
    world, candidate = _candidate_and_world()
    state = _state(
        candidate,
        source_policy_ids=[
            campaign_module._source_ranked_policy_id(
                candidate,
                character_level=39,
            )
        ],
    )

    assert campaign_module._source_ranked_kaladim_mirror_route_risk_allowed(
        candidate,
        state,
        character_level=39,
        character_max_hp=919,
        source_world=world,
    )
    assert campaign_module._select_source_ranked_hunt_candidate(
        (candidate,),
        state,
        world=world,
        character_level=39,
        character_max_hp=919,
    ) == candidate


def test_kaladim_mirror_route_risk_does_not_borrow_another_policy_receipt():
    world, candidate = _candidate_and_world()
    state = _state(candidate, source_policy_ids=["source-ranked-hunt-kaladim-9936-9951-39"])

    assert not campaign_module._source_ranked_kaladim_mirror_route_risk_allowed(
        candidate,
        state,
        character_level=39,
        character_max_hp=919,
        source_world=world,
    )
    assert not campaign_module._source_ranked_candidate_excluded_by_transit_hazard(
        candidate,
        state,
        character_level=39,
        source_world=world,
    )


def test_kaladim_mirror_route_risk_survives_productive_kill_cap():
    world, candidate = _candidate_and_world()
    candidate = replace(candidate, boot_kills=6)
    policy_id = campaign_module._source_ranked_policy_id(
        candidate,
        character_level=39,
    )
    state = _state(candidate, source_policy_ids=[policy_id])

    assert campaign_module._source_ranked_kaladim_mirror_route_risk_allowed(
        candidate,
        state,
        character_level=39,
        character_max_hp=919,
        source_world=world,
    )
    assert campaign_module._select_source_ranked_hunt_candidate(
        (candidate,),
        state,
        world=world,
        character_level=39,
        character_max_hp=919,
        allow_repeated_policy_ids=(policy_id,),
    ) == candidate
