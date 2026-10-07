from copy import deepcopy
from dataclasses import replace
from fractions import Fraction

import pytest

from dd4tester.combat_defenses import normal_attack_landing_probability
from dd4tester.campaign import (
    _SOURCE_RANKED_XP_LOSS_POLICIES_KEY,
    _TRAINING_AUDIT_KEY,
    _source_ranked_plain_defense_probability,
    _source_ranked_policy_id,
    _source_ranked_post_loss_plain_probe_allowed,
)
from dd4tester.hunt_candidates import (
    ACT_SENTINEL, HuntCandidate, MobileSource, MobReset, ObjectSource, WorldSource,
)


def _probability(**changes):
    options = {
        "character_level": 29,
        "attacker_level": 30,
        "character_class": "warrior",
        "known_skills": ["shield block", "parry", "dodge"],
        "known_skill_levels": {"shield block": 47, "parry": 62, "dodge": 60},
        "wielding": True,
        "shield": True,
    }
    options.update(changes)
    return normal_attack_landing_probability(**options)


def test_defenses_use_sequential_strict_percent_rolls():
    assert _probability() == Fraction(80, 100) * Fraction(72, 100) * Fraction(73, 100)


def test_missing_weapon_and_shield_receive_no_defense_credit():
    assert _probability(wielding=False, shield=False) == Fraction(73, 100)


@pytest.mark.parametrize("percent", [0, -1, 101, True, "60", None])
def test_invalid_or_hidden_proficiency_receives_no_credit(percent):
    assert _probability(known_skill_levels={"dodge": percent}) == 1


def test_skill_name_without_observed_proficiency_receives_no_credit():
    assert _probability(known_skill_levels={}) == 1
    assert _probability(known_skills=[]) == 1


def test_one_percent_chance_cannot_succeed_on_a_one_to_hundred_roll():
    assert _probability(
        attacker_level=29, known_skill_levels={"dodge": 2},
    ) == 1


def test_defense_cap_and_trauma_order_match_source():
    assert _probability(
        attacker_level=1, known_skill_levels={"shield block": 100},
        arm_trauma=True, blind=True,
    ) == Fraction(48, 100)
    assert _probability(
        attacker_level=1, known_skill_levels={"parry": 100},
        arm_trauma=True, blind=True,
    ) == Fraction(85, 100)


def test_disabled_defenses_and_dodge_remain_disabled():
    assert _probability(defenses_disabled=True) == 1
    assert _probability(
        wielding=False, shield=False, dodge_disabled=True,
    ) == 1


def test_brawler_preempt_does_not_require_a_weapon():
    assert _probability(
        character_class="brawler", wielding=False, shield=False,
        known_skills=["pre-empt"], known_skill_levels={"pre-empt": 62},
    ) == Fraction(72, 100)


@pytest.fixture
def defended_plain_probe():
    candidate = HuntCandidate(
        status="caution", score=100, area_file="test.are", mobile_vnum=105,
        target="the plain target", target_keyword="target", level=28,
        room_vnum=205, room_name="Test Room", route=("south",),
        source_spawn_limit=1, room_spawn_count=1, boot_kills=0, loot=(),
        source_value=0, contained_coins=0, hazards=(),
        target_body_form_flags=0, estimated_level_range=(26, 30),
        estimated_base_hp_range=(377, 1140),
        estimated_peak_round_damage=360, estimated_min_peak_round_damage=270,
    )
    world = WorldSource(
        mobiles={105: MobileSource(
            105, "plain target", "the plain target", 28, ACT_SENTINEL, 0, "test.are",
        )},
        mob_resets=[MobReset(105, 205, 1, ())],
        objects={
            1000: ObjectSource(1000, "sword", "a sword", 5, (0, 10, 25, 3), 100),
            1001: ObjectSource(1001, "shield", "a shield", 9, (0, 0, 0, 0), 10),
        },
    )
    levels = {
        "headbutt": 49, "enhanced damage": 67, "second attack": 62,
        "third attack": 50, "shield block": 47, "parry": 62, "dodge": 60,
        "unarmed combat knowledge": 60,
    }
    state = {
        "level": 29, "max_hp": 676, "hp": 676, "world_boot_id": "boot-1",
        "character_class": "warrior", "form": "normal", "position": 7,
        "affects": [], "stats": {"damroll": 20, "swift": 5},
        "campaign_known_skills": list(levels),
        "campaign_known_skill_levels": dict(levels),
        _TRAINING_AUDIT_KEY: {
            "observed": True, "level": 29, "boot_id": "boot-1",
            "known_skill_levels": dict(levels),
        },
        "equipment": [
            {"name": "a sword", "slot": "wield", "vnum": 1000, "wear_loc": 16},
            {"name": "a shield", "slot": "shield", "vnum": 1001, "wear_loc": 11},
        ],
        _SOURCE_RANKED_XP_LOSS_POLICIES_KEY: [{
            "level": 29, "boot_id": "boot-1", "policy_id": "another-policy",
            "xp_delta": -100, "loss_count": 1,
        }],
    }
    return candidate, world, state


def test_fresh_defenses_support_only_a_bounded_plain_post_loss_probe(defended_plain_probe):
    candidate, world, state = defended_plain_probe
    assert _source_ranked_plain_defense_probability(
        candidate, state, character_level=29, source_world=world,
    ) == Fraction(1314, 3125)
    assert _source_ranked_post_loss_plain_probe_allowed(
        candidate, state, character_level=29, source_world=world,
    ) is True
    stale = deepcopy(state)
    stale[_TRAINING_AUDIT_KEY]["boot_id"] = "old-boot"
    assert _source_ranked_post_loss_plain_probe_allowed(
        candidate, stale, character_level=29, source_world=world,
    ) is False


@pytest.mark.parametrize("change", [
    {"affects": ["blindness"]}, {"affects": "unknown"}, {"form": "wolf"},
    {"position": 4}, {"campaign_known_skill_levels": {"dodge": 100}},
])
def test_incomplete_or_impaired_defense_evidence_stays_closed(defended_plain_probe, change):
    candidate, world, state = defended_plain_probe
    assert _source_ranked_plain_defense_probability(
        candidate, {**state, **change}, character_level=29, source_world=world,
    ) is None


def test_defenses_never_reduce_raw_peak_or_clear_a_target_loss(defended_plain_probe):
    candidate, world, state = defended_plain_probe
    assert _source_ranked_post_loss_plain_probe_allowed(
        replace(candidate, estimated_peak_round_damage=454), state,
        character_level=29, source_world=world,
    ) is False
    lost = deepcopy(state)
    lost[_SOURCE_RANKED_XP_LOSS_POLICIES_KEY][0]["policy_id"] = (
        _source_ranked_policy_id(candidate, character_level=29)
    )
    assert _source_ranked_post_loss_plain_probe_allowed(
        candidate, lost, character_level=29, source_world=world,
    ) is False


@pytest.mark.parametrize("change", [
    {"specials": ("spec_poison",)}, {"equipped_weapons": ("a sword",)},
    {"room_spawn_count": 2}, {"source_spawn_limit": 2},
])
def test_defense_credit_excludes_nonplain_or_multiple_resets(defended_plain_probe, change):
    candidate, world, state = defended_plain_probe
    assert _source_ranked_plain_defense_probability(
        replace(candidate, **change), state, character_level=29, source_world=world,
    ) is None
