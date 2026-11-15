from types import SimpleNamespace

from dd4tester.character import CharacterSpec
from dd4tester.hunt_candidates import MobileSource
from dd4tester.starter import FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


def setup_policy(monkeypatch):
    spec = CharacterSpec.from_mapping({
        "name": "Tester", "race": "dwarf", "gender": "male",
        "class": "warrior", "subclass": "knight", "title": "",
    })
    policy = StarterPolicy(spec, "test-password")
    mobile = MobileSource(
        29129, "guard stoic pirate", "the pirate guard", 46, 34, -600, "freeport.are",
        room_description="A stoic guard stands here, barring the way.",
        description="The guard is heavily armed and moves with military precision.",
    )
    policy.source_world = SimpleNamespace(mobiles={29129: mobile})
    policy.current_room = policy.enemy_snapshot_room = "29169"
    policy.world_boot_id = "boot"
    policy.source_mobile_targets = {"pirate guard", "scruffy pirate"}
    policy.room_target_selectors = {"29169": {"pirate guard": ["#123"], "scruffy pirate": ["#456"]}}
    enemies = [{"name": mobile.short_description, "isnpc": 29129,
                "long_desc": mobile.room_description, "look_desc": mobile.description}]
    monkeypatch.setattr(policy, "_current_room_enemy_records", lambda state, **kwargs: enemies)
    monkeypatch.setattr(policy, "_current_room_target_counts", lambda state: {"pirate guard": 1, "scruffy pirate": 1})
    for name in ("_source_mobile_name_is_known_below_useful_band_in_room",
                 "_source_mobile_name_is_known_below_useful_band",
                 "_source_mobile_name_is_non_assisting_target_bystander",
                 "_source_mobile_name_is_non_assisting_bystander"):
        monkeypatch.setattr(policy, name, lambda *args, **kwargs: False)
    state = CharacterState(level=45, room_vnum="29169", room_listing={
        "render_complete": True, "room_vnum": "29169",
        "targeted_lines": [{"target_id": "123", "description": "The pirate guard is here, fighting YOU!"}],
    })
    stop = FieldHuntStop((), "stoic guard", exact_target=True, source_mobile_vnum=29129,
                         source_reset_room_vnum="29169", source_policy_id="source-test")
    return policy, state, stop, enemies


def test_fighting_short_name_is_not_a_second_mobile_but_real_bystander_remains(monkeypatch):
    policy, state, stop, _ = setup_policy(monkeypatch)
    assert policy._source_mobile_room_material_bystanders(state, stop.target, stop) == (("scruffy pirate", 1),)
    assert len(policy._combat_session.source_attacker_aliases) == 1
    policy._source_mobile_room_material_bystanders(state, stop.target, stop)
    assert len(policy._combat_session.source_attacker_aliases) == 1


def test_primary_bystander_correction_requires_exact_fresh_identity(monkeypatch):
    policy, state, stop, enemies = setup_policy(monkeypatch)
    enemies[0]["isnpc"] = 29130
    assert not policy._room_name_is_source_confirmed_primary(state, "pirate guard", stop)
    enemies[0]["isnpc"] = 29129
    enemies.append(dict(enemies[0]))
    assert not policy._room_name_is_source_confirmed_primary(state, "pirate guard", stop)
    enemies.pop()
    state.room_listing["render_complete"] = False
    assert not policy._room_name_is_source_confirmed_primary(state, "pirate guard", stop)
    state.room_listing["render_complete"] = True
    enemies[0]["look_desc"] = "another guard"
    assert not policy._room_name_is_source_confirmed_primary(state, "pirate guard", stop)
