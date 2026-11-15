from dataclasses import replace

import pytest

from dd4tester.character import CharacterSpec
from dd4tester.equipment import GearCatalog, ITEM_ANTI_GOOD
from dd4tester.hunt_candidates import ObjectSource, ITEM_STAFF, ITEM_WEAPON
from dd4tester import campaign
from dd4tester.starter import StarterPolicy
from dd4tester.state import CharacterState


def resource_policy():
    item = ObjectSource(7303, "red dragonorb", "the Red DragonOrb", ITEM_STAFF, (), 0)
    peer = ObjectSource(7304, "blue dragonorb", "the Blue DragonOrb", ITEM_STAFF, (), 0)
    policy = StarterPolicy(
        CharacterSpec.from_mapping({"name": "Tester", "race": "human", "gender": "male", "class": "warrior"}),
        "password", gear_catalog=GearCatalog({7303: item, 7304: peer}),
    )
    record = {"object_vnum": 7303, "object_description": "red dragonorb",
              "command_keyword": "2.dragonorb"}
    return policy, record


def test_resource_hold_does_not_reuse_an_old_inventory_ordinal():
    policy, record = resource_policy()
    state = CharacterState(inventory=[[{"short_desc": "the Red DragonOrb"}]])
    assert policy._current_source_resource_keyword(state, record) == "dragonorb"
    assert record["command_keyword"] == "2.dragonorb"


def test_resource_prefers_current_exact_selector_over_old_ordinal():
    policy, record = resource_policy()
    state = CharacterState(inventory=[[{"short_desc": "[#123] the Red DragonOrb"}]])
    assert policy._current_source_resource_keyword(state, record) == "#123"


def test_resource_with_multiple_prototypes_uses_a_source_unique_word():
    policy, record = resource_policy()
    state = CharacterState(inventory=[[{"short_desc": "the Red DragonOrb"},
                                       {"short_desc": "the Blue DragonOrb"}]])
    assert policy._current_source_resource_keyword(state, record) == "red"


@pytest.mark.parametrize("inventory", [
    [[{"short_desc": "the Blue DragonOrb"}]],
    [[{"short_desc": "the Red DragonOrb", "quan": "2"}]],
    [[{"short_desc": "the Red DragonOrb"}, {"short_desc": "an unknown object"}]],
])
def test_resource_rebinding_does_not_guess_missing_duplicate_or_unknown_inventory(inventory):
    policy, record = resource_policy()
    assert policy._current_source_resource_keyword(CharacterState(inventory=inventory), record) is None


def test_resource_keyword_prefix_collisions_remain_ambiguous():
    policy, record = resource_policy()
    policy.gear_catalog.objects[7304] = replace(
        policy.gear_catalog.objects[7304], keywords="reddish dragonorbs",
    )
    # Rebuild the lookup with the changed source definition.
    policy.gear_catalog = GearCatalog(policy.gear_catalog.objects)
    state = CharacterState(inventory=[[{"short_desc": "the Red DragonOrb"},
                                       {"short_desc": "the Blue DragonOrb"}]])
    assert policy._current_source_resource_keyword(state, record) is None


def test_dropped_held_resource_is_not_a_weapon_disarm_or_successful_hold():
    policy, record = resource_policy()
    weapon = ObjectSource(20, "bishop piece", "a bishop piece", ITEM_WEAPON, (), 0,
                          wear_flags=1 | (1 << 13))
    policy.gear_worn = [weapon]
    policy.combat_active = True
    policy.active_target = "the dwarf"
    policy.pending_source_resource_hold = "sanctuary"
    policy.observe_text("You hold the Red DragonOrb in your hands.\n"
                        "You are zapped by the Red DragonOrb and drop it.\n")
    assert policy.disarm_recovery_step == 0
    assert policy.pending_source_resource_hold is None
    assert policy.source_resource_hold_ready is None
    assert "sanctuary" in policy.failed_source_resource_effects
    policy.observe_text("You are zapped by a bishop piece and drop it.\n")
    assert policy.disarm_recovery_step == 1


def test_current_alignment_rejects_an_unholdable_resource_before_command():
    policy, record = resource_policy()
    item = replace(policy.gear_catalog.objects[7303], extra_flags=ITEM_ANTI_GOOD)
    policy.gear_catalog = GearCatalog({7303: item})
    policy.verified_source_resources = {"sanctuary": {
        **record, "effect": "sanctuary", "mode": "staff", "command": "brandish",
        "requires_hold": True, "charges_remaining": 10,
    }}
    state = CharacterState(level=46, inventory=[[{"short_desc": "the Red DragonOrb"}]],
                           progress={"alignment": 515})
    assert policy._source_resource_record(state, effect="sanctuary") is None


def test_campaign_does_not_count_an_unusable_held_reserve_as_protection():
    state = {
        "inventory": [[{"short_desc": "the Red DragonOrb"}]],
        campaign._SOURCE_RESOURCE_RESERVES_KEY: {"sanctuary": {
            "object_description": "red dragonorb", "mode": "staff",
            "charges_remaining": 10, "activation_usable": False,
        }},
    }
    assert not campaign._STATE_HAS_SANCTUARY_RESERVE_UNCACHED(state)
    assert not campaign._state_has_source_sanctuary_resource_reserve(state)


def test_source_missing_pickup_reply_ends_disarm_recovery():
    policy, _ = resource_policy()
    policy.disarm_recovery_step = 2
    policy.observe_text("I see no bishop here.\n")
    assert policy.disarm_recovery_step == 0
    assert policy.disarm_recovery_failed
