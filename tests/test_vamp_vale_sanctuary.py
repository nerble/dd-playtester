from pathlib import Path

from dd4tester import campaign
from dd4tester.hunt_candidates import load_world_source


SOURCE_DIRECTORY = Path("runs/dd4-source/server/area")


def _level_39_state() -> dict[str, object]:
    return {
        "level": 39,
        "max_hp": 937,
        "max_move": 583,
        "world_boot_id": "test-boot",
        campaign._SOURCE_REVISION_KEY: "test-source",
    }


def test_vamp_vale_ground_sanctuary_plan_keeps_wolf_preflight() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)

    plan = campaign._select_source_ground_sanctuary_plan(
        _level_39_state(),
        source_directory=SOURCE_DIRECTORY,
        source_world=world,
    )

    assert plan is not None
    candidate, placement = plan
    assert (placement.object_vnum, placement.room_vnum) == (20645, 20679)
    assert placement.source_kind == "ground-reset"
    assert placement.activation is not None
    assert placement.activation.mode == "pill"
    assert placement.activation.spell == "sanctuary"
    assert candidate.route_preflight_room_vnum == "20694"
    assert candidate.route_preflight_checks == (
        ("where great", "the great wolf"),
    )
    assert candidate.route_preflight_level_range == (48, 52)
    assert candidate.route_hazard_mobile_vnums == (20604, 20605)
    assert candidate.route_attack_program_mobile_vnums == (20604, 20605)
    assert candidate.route_preflight_hard_hazard is True
    assert candidate.autonomy_rejections == (
        "a higher-level aggressive wanderer can reach the route",
    )


def test_vamp_vale_ground_pill_uses_exact_local_keyword() -> None:
    world = load_world_source(SOURCE_DIRECTORY, include_all_areas=True)
    candidate, placement = campaign._select_source_ground_sanctuary_plan(
        _level_39_state(),
        source_directory=SOURCE_DIRECTORY,
        source_world=world,
    )
    assert (
        campaign._source_resource_reserve_record(
            world,
            world.objects[20645],
            required_spell="sanctuary",
            candidate=candidate,
            placement=placement,
        )
        == {
            "effect": "sanctuary",
            "object_vnum": 20645,
            "object_description": "purple herbs",
            "item_type": campaign.ITEM_PILL,
            "source_mobile_vnum": None,
            "source_room_vnum": 20679,
            "spell": "sanctuary",
            "command": "eat",
            "mode": "pill",
            "requires_hold": False,
            "consumes_object": True,
            "consumes_charge": False,
            "target": None,
            "command_keyword": "purple",
            "charges_remaining": 1,
            "source_kind": "ground-reset",
            "container_object_vnums": [],
            "required_key_object_vnums": [],
            "required_key_source_mobile_vnums": [],
            "source_object_room_vnum": 20679,
        }
    )


def test_vamp_vale_ground_acquisition_promotes_research_result() -> None:
    previous = _level_39_state()
    current = {
        **previous,
        campaign._SOURCE_CONSUMABLE_SPELL_KEY: "sanctuary",
        "campaign_fastwalk_required_object_vnums": [20645],
        "campaign_died_during_segment": False,
        campaign._VAMP_VALE_GROUND_SANCTUARY_ATTEMPT_KEY: {
            "boot_id": "test-boot",
            "level": 39,
            "source_revision": "test-source",
            "status": "attempted",
        },
    }

    merged = campaign._merge_campaign_research_result(
        previous,
        current,
        policy=campaign._SOURCE_RANKED_SANCTUARY_GROUND_POLICY,
    )

    result = merged["campaign_research_results"][
        campaign._SOURCE_RANKED_SANCTUARY_GROUND_POLICY.policy_id
    ]
    assert result["required_object_acquired"] is True
    assert result["required_object_vnums"] == [20645]
    assert (
        merged[campaign._VAMP_VALE_GROUND_SANCTUARY_ATTEMPT_KEY]["status"]
        == "succeeded"
    )


def test_vamp_vale_ground_attempt_is_one_shot_per_boot() -> None:
    state = _level_39_state()
    state[campaign._VAMP_VALE_GROUND_SANCTUARY_ATTEMPT_KEY] = {
        "boot_id": "test-boot",
        "level": 39,
        "source_revision": "test-source",
        "status": "closed",
    }

    assert (
        campaign._select_source_ground_sanctuary_plan(
            state,
            source_directory=SOURCE_DIRECTORY,
        )
        is None
    )
