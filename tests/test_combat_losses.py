import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from dd4tester.campaign import (
    _SOURCE_RANKED_XP_LOSS_POLICIES_KEY, _merge_protection_recovery_metadata,
    _xp_loss_event_observed,
)
from dd4tester.character import CharacterSpec
from dd4tester.combat_losses import SOURCE_COMBAT_LOSSES_KEY, recover_source_combat_losses
from dd4tester.fastwalks import Fastwalk
from dd4tester.hunt_candidates import SourceCombatOutput
from dd4tester.observations import GameEvent
from dd4tester.progression import _SOURCE_RANKED_HUNT_POLICY
from dd4tester.starter import BotDecision, FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState


PRIMARY = "source-ranked-hunt-example-101-201-31"
SECONDARY = "source-ranked-hunt-example-102-202-31"


def test_withdrawal_retains_actual_combat_output_only_with_explicit_loss(monkeypatch) -> None:
    spec = CharacterSpec.from_mapping({
        "name": "LossTester", "race": "human", "gender": "female",
        "class": "warrior", "subclass": None, "title": "",
    })
    policy = StarterPolicy(
        spec, "test-password", fastwalk_route=Fastwalk("example", 1, 100, "e"),
        fastwalk_hunt_stops=(FieldHuntStop(
            (), "bartender", source_mobile_vnum=102, source_reset_room_vnum="202",
            source_policy_id=SECONDARY, source_combat_action="kick",
            source_combat_conservative_damage=24, source_combat_max_actions=48,
        ),),
    )
    policy.world_boot_id = "boot"
    policy.combat_active = True
    policy.enemy_snapshot_stale = False
    monkeypatch.setattr(policy, "_encounter_output", lambda *_args: SourceCombatOutput(
        "kick", 20, 30, 40, "movement", 5, 26, maximum_actions=48,
    ))
    monkeypatch.setattr(policy, "_wielded_weapon", lambda: SimpleNamespace(
        vnum=3022, short_description="a long sword",
    ))
    state = CharacterState(level=31, hp=140, max_hp=740, room_vnum="202",
                           stats={"damroll": 22}, enemies=[[
        {"name": "the bartender", "isnpc": "102", "hp": "400", "maxhp": "975"},
    ]])
    policy.after_command(BotDecision("flee", "health withdrawal"), state)
    assert policy._combat_session.source_losses == []
    policy.observe_events([GameEvent("experience_lost", "text", {"xp": 592})], state)
    output = policy._combat_session.source_losses[0]["output_at_withdrawal"]
    assert output["ceiling"] == 1248
    assert output["damroll"] == 22
    assert output["weapon_vnum"] == 3022
    assert output["boot_id"] == "boot"


def test_equal_penalties_on_separate_runs_are_new_campaign_losses() -> None:
    previous = {"xp_loss_total": 592, "xp_loss_observed": True, "campaign_xp_loss_total": 1200}
    current = {"xp_loss_total": 592, "xp_loss_observed": True, "campaign_xp_loss_total": 1792}
    assert _xp_loss_event_observed(previous, current) is True
    assert _xp_loss_event_observed(current, current) is False


def _loss_record(policy_id: str = SECONDARY) -> dict:
    mobile, room = (101, 201) if policy_id == PRIMARY else (102, 202)
    return {"policy_id": policy_id, "mobile_vnum": mobile, "room_vnum": room,
            "level": 31, "target": "the bartender", "xp_lost": 592}


@pytest.mark.parametrize("failed_policy", (PRIMARY, SECONDARY))
def test_positive_first_kill_does_not_clear_explicit_stop_loss(failed_policy: str) -> None:
    current = {
        "level": 31, "world_boot_id": "boot", "xp_loss_observed": True, "xp_loss_total": 592,
        "campaign_objective_kills": [{"source_policy_id": PRIMARY, "xp_gained": 2000}],
        SOURCE_COMBAT_LOSSES_KEY: [_loss_record(failed_policy)],
    }
    policy = replace(_SOURCE_RANKED_HUNT_POLICY, policy_id=PRIMARY)
    updated = _merge_protection_recovery_metadata(
        current, policy=policy, xp_delta=1800, previous={"xp_loss_total": 0}, loss_event_id=77,
    )
    assert {record["policy_id"] for record in updated[_SOURCE_RANKED_XP_LOSS_POLICIES_KEY]} == {failed_policy}
    assert updated[_SOURCE_RANKED_XP_LOSS_POLICIES_KEY][0]["exact_stop_loss"] is True


def test_pending_withdrawal_without_explicit_loss_does_not_close_target() -> None:
    current = {"level": 31, "world_boot_id": "boot", SOURCE_COMBAT_LOSSES_KEY: [_loss_record()]}
    updated = _merge_protection_recovery_metadata(
        current, policy=replace(_SOURCE_RANKED_HUNT_POLICY, policy_id=PRIMARY),
        xp_delta=0, previous={"xp_loss_total": 0}, loss_event_id=77,
    )
    assert not updated.get(_SOURCE_RANKED_XP_LOSS_POLICIES_KEY)


@pytest.mark.parametrize("enemy_vnum", (102, 103))
def test_live_withdrawal_retains_only_exact_source_identity(enemy_vnum: int) -> None:
    spec = CharacterSpec.from_mapping({
        "name": "LossTester", "race": "human", "gender": "female", "class": "warrior",
        "subclass": None, "title": "",
    })
    policy = StarterPolicy(
        spec, "test-password", fastwalk_route=Fastwalk("example", 1, 100, "e"),
        fastwalk_hunt_stops=(FieldHuntStop(
            (), "bartender", source_mobile_vnum=102, source_reset_room_vnum="202",
            source_policy_id=SECONDARY,
        ),),
    )
    policy.active_target = "the bartender"
    policy.active_target_mobile_vnum = enemy_vnum
    policy.combat_active = True
    policy.enemy_snapshot_stale = False
    state = CharacterState(level=31, hp=140, max_hp=740, room_vnum="202", enemies=[[
        {"name": "the bartender", "isnpc": str(enemy_vnum), "hp": "400", "maxhp": "975"},
    ]])
    policy.after_command(BotDecision("flee", "health withdrawal"), state)
    policy.observe_text("You flee from combat! You lose 592 exp.")
    policy.observe_events([GameEvent("experience_lost", "text", {"xp": 592})], state)
    assert policy.active_target is None
    records = policy._combat_session.source_losses
    if enemy_vnum == 102:
        assert records[0]["policy_id"] == SECONDARY
        assert records[0]["mobile_vnum"] == 102
        assert records[0]["xp_lost"] == 592
    else:
        assert records == []


def _row(kind: str, payload: dict, event_id: int) -> dict:
    return {"id": event_id, "run_id": 9, "kind": kind, "payload_json": json.dumps(payload)}


@pytest.mark.parametrize("failure", (None, "wrong_mob", "wrong_room", "no_withdrawal", "new_boot"))
def test_recent_loss_repair_requires_ordered_exact_enemy_room_and_penalty(failure: str | None) -> None:
    start = {
        "level": 31, "world_boot_id": "boot", "campaign_source_revision": "revision",
        "campaign_source_ranked_hunt_candidate": {
            "mobile_vnum": 101, "room_vnum": 201, "policy_id": PRIMARY,
            "circuit": [{"mobile_vnum": 102, "room_vnum": 202, "policy_id": SECONDARY}],
        },
    }
    end = {**start, "xp_loss_observed": True}
    if failure == "new_boot":
        end["world_boot_id"] = "later boot"
    context = [
        _row("game_event", {"type": "enemies_changed", "data": {"value": [[{
            "name": "the bartender", "isnpc": "103" if failure == "wrong_mob" else "102",
        }]]}}, 1),
        _row("decision", {"command": "look" if failure == "no_withdrawal" else "flee"}, 2),
        _row("game_event", {"type": "enemies_changed", "data": {"value": []}}, 3),
        _row("game_event", {"type": "room_entered", "data": {
            "vnum": "203", "arrival": {"from": 204 if failure == "wrong_room" else 202},
        }}, 4),
    ]
    loss = _row("game_event", {"type": "experience_lost", "data": {"xp": 592}}, 5)
    records = recover_source_combat_losses(start, end, [(loss, context)])
    if failure is None:
        assert len(records) == 1 and records[0]["policy_id"] == SECONDARY
        assert records[0]["event_id"] == 5
    else:
        assert records == []
