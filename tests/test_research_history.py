import json
from copy import deepcopy

import pytest

from dd4tester import campaign as c
from dd4tester.state import CharacterState
from dd4tester.storage import RunStorage


PRIMARY = "source-ranked-hunt-moria-4002-4020-8"
SECONDARY = "source-ranked-hunt-moria-4002-4017-8"
FAILURE = "field route interrupted by connection loss; return home before retrying"
KILL = {"mob_name": "the centipede", "source_mobile_vnum": 4002,
        "source_policy_id": SECONDARY, "xp_gained": 111}


def positive():
    return {"observed": True, "viable": True, "completed_kill": True,
            "consider_viable": True, "boot_id": "boot", "objective_xp": 111,
            "max_objective_kill_xp": 111}


def snapshot(**changes):
    return {**CharacterState(level=8, xp=28164, hp=113, max_hp=113,
                            room_vnum="3054", position=7).to_dict(),
            "world_boot_id": "boot", "campaign_policy_revision": 242, **changes}


@pytest.fixture
def history(tmp_path):
    with RunStorage(tmp_path / "runs.sqlite3") as storage:
        campaign_id = storage.create_campaign(
            name="circuit-history", config_path=tmp_path / "campaign.yaml",
            character_profile_path=tmp_path / "character.yaml", target_level=100,
        )

        def add(phase, kills, end, *, status="success", terminal=None):
            run = storage.create_run(scenario_name="fixture", scenario_path="fixture.yaml")
            storage.record_event(run, kind="state", payload={
                "objective_kills": kills if terminal is None else terminal,
            })
            storage.finish_run(run, status=status)
            start = snapshot(**{c._SOURCE_RANKED_CANDIDATE_KEY: {
                "policy_id": phase, "target": "centipede", "room_vnum": "4020",
                "circuit": [{"policy_id": SECONDARY, "target": "centipede",
                             "room_vnum": "4017"}],
            }})
            segment = storage.start_campaign_segment(campaign_id, phase=phase, start_state=start)
            storage.finish_campaign_segment(
                segment, status=status, run_id=run,
                end_state={**end, "campaign_objective_kills": kills},
                command_count=1, duration_seconds=1,
            )
            return storage.list_campaign_segments(campaign_id)[-1]

        yield storage, campaign_id, add


def seed(history):
    storage, campaign_id, add = history
    failed = {"observed": False, "viable": False, "route_hazard": FAILURE, "boot_id": "boot"}
    add(SECONDARY, [], snapshot(campaign_research_results={SECONDARY: failed}), status="failed")
    end = snapshot(
        campaign_research_results={SECONDARY: positive(), PRIMARY: {
            "observed": False, "viable": False, "completed_kill": False,
            "crowded": True, "boot_id": "boot",
        }}, campaign_fastwalk_crowded=True,
        **{c._SOURCE_CONSIDER_OUTCOMES_KEY: {SECONDARY: True}},
    )
    segment = add(PRIMARY, [KILL], end)
    return end, segment


@pytest.mark.parametrize("corrupted", [False, True])
def test_run_12783_secondary_kill_survives_reconnect_without_primary_credit(history, corrupted):
    storage, campaign_id, _ = history
    state, _ = seed(history)
    if corrupted:
        state["campaign_research_results"][SECONDARY] = {
            "observed": False, "viable": False, "route_hazard": FAILURE, "boot_id": "boot",
        }
        state["campaign_research_results"][PRIMARY]["completed_kill"] = True
        state["campaign_research_results"][PRIMARY]["viable"] = True
    state[c._RESEARCH_CROWD_COOLDOWN_KEY] = {PRIMARY: 3}
    state[c._SOURCE_RANKED_XP_LOSS_POLICIES_KEY] = [{"policy_id": "unrelated", "xp_delta": -118}]
    original = deepcopy(state)
    segments = storage.list_campaign_segments(campaign_id)
    for _ in range(2):
        state = c._repair_confirmed_research_kills(storage, campaign_id, state)
        state = c._repair_source_ranked_circuit_consider_history(state, segments)
        assert state["campaign_research_results"][SECONDARY] == positive()
        assert state["campaign_research_results"][PRIMARY].get("completed_kill") is not True
        assert state[c._RESEARCH_CROWD_COOLDOWN_KEY] == {PRIMARY: 3}
        assert state[c._SOURCE_RANKED_XP_LOSS_POLICIES_KEY] == original[c._SOURCE_RANKED_XP_LOSS_POLICIES_KEY]


def test_secondary_view_does_not_inherit_another_stops_crowd(history):
    storage, _, _ = history
    _, segment = seed(history)
    views = c._research_segment_views(storage, segment)
    assert views[PRIMARY]["_research_objective_kills"] == []
    assert views[SECONDARY]["_research_objective_kills"] == [KILL]
    assert json.loads(views[PRIMARY]["end_state_json"])["campaign_fastwalk_crowded"]
    assert not json.loads(views[SECONDARY]["end_state_json"])["campaign_fastwalk_crowded"]


@pytest.mark.parametrize("boundary", ["absent", "negative-consider", "failed", "failed-with-kill", "death", "empty-ledger"])
def test_later_exact_stop_evidence_supersedes_the_old_kill(history, boundary):
    storage, campaign_id, add = history
    state, _ = seed(history)
    negative = {"observed": True, "viable": False, "completed_kill": False, "boot_id": "boot"}
    extra = {c._SOURCE_CONSIDER_OUTCOMES_KEY: {SECONDARY: False}}
    if boundary == "absent":
        negative["absent"] = True
        extra = {c._SOURCE_ABSENT_SIGHTINGS_KEY: [
            {"policy_id": SECONDARY, "room_vnum": "4017", "target": "centipede"},
        ]}
    later = snapshot(campaign_research_results={SECONDARY: negative}, **extra)
    later["campaign_died_during_segment"] = boundary == "death"
    add(PRIMARY, [KILL] if boundary in {"death", "empty-ledger", "failed-with-kill"} else [], later,
        status="failed" if boundary.startswith("failed") else "success",
        terminal=[] if boundary == "empty-ledger" else None)
    repaired = c._repair_confirmed_research_kills(storage, campaign_id, later)
    repaired = c._repair_source_ranked_circuit_consider_history(
        repaired, storage.list_campaign_segments(campaign_id),
    )
    assert not repaired["campaign_research_results"][SECONDARY]["viable"]


def test_untagged_legacy_kill_stays_with_the_original_phase(history):
    storage, _, add = history
    segment = add(PRIMARY, [{"mob_name": "centipede", "xp_gained": 70}], snapshot())
    views = c._research_segment_views(storage, segment)
    assert tuple(views) == (PRIMARY,)
    assert views[PRIMARY]["_research_objective_kills"][0]["xp_gained"] == 70


@pytest.mark.parametrize("boot", [None, "new-boot"])
def test_unknown_or_changed_historical_reboot_cannot_promote_current_negative(history, boot):
    storage, campaign_id, add = history
    end = snapshot(world_boot_id=boot, campaign_research_results={SECONDARY: positive()})
    add(PRIMARY, [KILL], end)
    current = snapshot(campaign_research_results={SECONDARY: {
        "observed": True, "viable": False, "completed_kill": False, "boot_id": "boot",
    }})
    repaired = c._repair_confirmed_research_kills(storage, campaign_id, current)
    assert not repaired["campaign_research_results"][SECONDARY]["viable"]
