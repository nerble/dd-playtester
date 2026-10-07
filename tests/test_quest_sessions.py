import asyncio
import json
import sqlite3
from dataclasses import replace

import pytest

from dd4tester import campaign, starter
from dd4tester.character import CharacterSpec
from dd4tester.connection import ReadResult
from dd4tester.excavation import DigBudget, DigObservation, HoardDigSession
from dd4tester.equipment import GearCatalog
from dd4tester.fastwalks import Fastwalk
from dd4tester.hunt_candidates import (
    ACT_SENTINEL, ExitSource, MobileSource, MobReset, ObjectSource, RoomSource,
    WorldSource,
)
from dd4tester.sessions import (
    LiveSessionState,
    QuestCooldownWait,
    QuestPhase,
    QuestSessionController,
    resume_policy_at_healer,
)
from dd4tester.starter import BotDecision, FieldHuntStop, StarterPolicy
from dd4tester.state import CharacterState
from dd4tester.storage import RunStorage


def spec(tmp_path):
    return CharacterSpec(
        name="Sessiontest", password_env="QUEST_TEST_PASSWORD", race="human",
        gender="female", character_class="mage", max_runtime=300,
        database=tmp_path / "runs.sqlite3", transcript_dir=tmp_path / "transcripts",
    )


def healer(**changes):
    return replace(CharacterState(
        level=8, hp=100, max_hp=100, mana=100, max_mana=100,
        move=100, max_move=100, room_vnum="3054", room_name="The Healer",
        position=7, enemies=[],
        hunger=40, thirst=40,
    ), **changes)


def route(name):
    return Fastwalk(name=name, minimum_level=1, maximum_level=100, notation="s")


def phase(name):
    return QuestPhase(
        name, "scripted phase transition", route=route(name),
        hunt_stops=(FieldHuntStop((), "target", source_mobile_vnum=4003),)
        if name == "quest-target-run" else (FieldHuntStop((), None),),
    )


HOARD_IDENTITY = (25305, 18022, 1777)


def hoard_status(identity=HOARD_IDENTITY):
    giver_vnum, room_vnum, object_vnum = identity
    return {
        "active": 1,
        "type": "retrieve",
        "giver_vnum": giver_vnum,
        "room_vnum": room_vnum,
        "object_vnum": object_vnum,
        "retrieval_evidence": {
            "method": "hoard",
            "source": "requested-questmaster-narrative",
            "giver_vnum": giver_vnum,
            "room_vnum": room_vnum,
            "object_vnum": object_vnum,
        },
    }


def hoard_checkpoint(identity=HOARD_IDENTITY):
    excavation = HoardDigSession(
        DigBudget(3604, "shovel", 2, 2, 5, 6, 8),
        quest_identity=identity,
        minimum_hp=100,
        return_movement=30,
    )
    excavation._last_observed_sequence = 4
    return excavation.checkpoint()


def test_quest_session_controller_owns_phase_history_and_rejects_repeats():
    controller = QuestSessionController(
        phase="quest-request",
        planner=lambda _phase, _state: phase("quest-target-run"),
    )
    session = LiveSessionState(CharacterState(), quest_session=controller)
    state = {"quest_status": {"active": 1}}

    assert session.quest_session is controller
    assert controller.plan_next_phase(state, permitted=False) is None
    controller.observe_quest_status()
    next_phase = controller.plan_next_phase(state, permitted=True)
    assert next_phase is not None

    first = controller.checkpoint(
        {"room_vnum": "3054"}, objective_kills=[], commands=4,
    )
    assert first["phase"] == "quest-request"
    controller.activate(next_phase)
    assert controller.phase == "quest-target-run"
    controller.checkpoint({"room_vnum": "3054"}, objective_kills=[], commands=7)

    with pytest.raises(RuntimeError, match="repetition"):
        controller.activate(next_phase)

    controller.connection_closed()
    assert not controller.observed_on_connection
    assert controller.continuation_closed


def test_quest_session_restores_hoard_checkpoint_for_exact_active_assignment():
    checkpoint = hoard_checkpoint()
    controller = QuestSessionController(
        phase="quest-target-run",
        expected_status=hoard_status(),
        hoard_excavation_checkpoint=checkpoint,
    )

    assert controller.hoard_excavation is not None
    assert controller.hoard_excavation.quest_identity == HOARD_IDENTITY
    assert controller.checkpoint_hoard_excavation() == checkpoint


def test_quest_session_begins_one_dig_only_for_the_observed_assignment():
    status = hoard_status()
    controller = QuestSessionController(
        phase="quest-target-run", expected_status=status,
    )
    budget = DigBudget(3604, "shovel", 2, 2, 5, 6, 8)

    with pytest.raises(ValueError, match="observed on this connection"):
        controller.begin_hoard_excavation(
            budget, minimum_hp=100, return_movement=30,
            current_status=status,
        )

    controller.observe_quest_status()
    session = controller.begin_hoard_excavation(
        budget, minimum_hp=100, return_movement=30,
        current_status=status,
    )

    assert session.quest_identity == HOARD_IDENTITY
    assert controller.begin_hoard_excavation(
        budget, minimum_hp=100, return_movement=30,
        current_status=status,
    ) is session
    with pytest.raises(ValueError, match="different hoard excavation"):
        controller.begin_hoard_excavation(
            replace(budget, maximum_digs=budget.maximum_digs + 1),
            minimum_hp=100, return_movement=30,
            current_status=status,
        )


def test_quest_session_polls_dig_only_for_the_exact_active_assignment():
    controller = QuestSessionController(
        phase="quest-target-run",
        expected_status=hoard_status(),
        hoard_excavation_checkpoint=hoard_checkpoint(),
    )
    budget = controller.hoard_excavation.budget
    observed = DigObservation(
        5, HOARD_IDENTITY, 18022, budget.tool_vnum, 100, 100,
        False, 0, True, True, budget,
    )

    step = controller.poll_hoard_excavation(
        observed, now=1.0, current_status=hoard_status(),
    )

    assert step is not None and step.command == "dig"
    assert controller.hoard_excavation.commands == 1


def test_quest_session_confirms_pickup_for_the_exact_active_hoard():
    status = hoard_status()
    budget = DigBudget(3604, "shovel", 2, 2, 5, 6, 8)
    controller = QuestSessionController(
        phase="quest-target-run", expected_status=status,
    )
    controller.observe_quest_status()
    excavation = HoardDigSession(
        budget, quest_identity=HOARD_IDENTITY, minimum_hp=100,
        return_movement=30,
    )
    observed = DigObservation(
        1, HOARD_IDENTITY, 18022, 3604, 100, 100, False, 0, True, True,
        budget,
    )
    assert excavation.poll(observed, now=0).command == "dig"
    excavation.observe(
        "With a final effortful thrust, you unearth something!"
        "<100/100 hits 100/100 mana 100/100 move [Sessiontest]>"
    )
    assert excavation.poll(
        replace(observed, sequence=2), now=4,
    ).status == "unearthed"
    controller.hoard_excavation = excavation

    pending = controller.prepare_hoard_object_pickup(
        sequence=4,
        quest_object_vnum=HOARD_IDENTITY[2],
        source_object_description="a coin of Serenos",
        source_description_vnums=(HOARD_IDENTITY[2],),
        current_room_vnum=HOARD_IDENTITY[1],
        room_listing={
            "room_vnum": str(HOARD_IDENTITY[1]),
            "sequence": 1,
            "state_revision": 4,
            "render_complete": True,
            "targeted_lines": [{
                "target_id": "58601",
                "description": "a coin of Serenos",
            }],
            "unkeyed_lines": [],
        },
        inventory_items=[[[]]],
        current_status=status,
    )
    step = controller.confirm_hoard_object_acquired(
        sequence=5,
        quest_object_vnum=HOARD_IDENTITY[2],
        source_object_description="a coin of Serenos",
        source_description_vnums=(HOARD_IDENTITY[2],),
        inventory_items=[[ [{"short_desc": "a coin of Serenos", "quan": "1"}] ]],
        current_status=status,
    )

    assert pending is not None and pending.command == "get #58601"
    assert step is not None and step.status == "object_acquired"
    assert controller.checkpoint_hoard_excavation(status)[
        "quest_object_selector"
    ] == "#58601"


def test_quest_session_closes_dig_when_the_assignment_changes():
    controller = QuestSessionController(
        phase="quest-target-run",
        expected_status=hoard_status(),
        hoard_excavation_checkpoint=hoard_checkpoint(),
    )
    budget = controller.hoard_excavation.budget
    observed = DigObservation(
        5, HOARD_IDENTITY, 18022, budget.tool_vnum, 100, 100,
        False, 0, True, True, budget,
    )

    step = controller.poll_hoard_excavation(
        observed,
        now=1.0,
        current_status=hoard_status((25305, 18022, 1778)),
    )

    assert step is not None and step.status == "stopped"
    assert "assignment changed" in step.reason
    assert controller.hoard_excavation is None


def test_quest_session_forwards_trap_response_for_exact_active_hoard():
    status = hoard_status()
    budget = DigBudget(3604, "shovel", 2, 2, 5, 6, 8)
    controller = QuestSessionController(
        phase="quest-target-run", expected_status=status,
    )
    controller.hoard_excavation = HoardDigSession(
        budget, quest_identity=HOARD_IDENTITY, minimum_hp=100,
        return_movement=30,
    )
    first = DigObservation(
        1, HOARD_IDENTITY, 18022, 3604, 100, 50, False, 0, True, True,
        budget,
    )

    assert controller.hoard_excavation.poll(first, now=0).command == "dig"
    response = (
        "You hear a strange noise...\n"
        "You are struck by a small dart... your blood begins to burn!\n"
        "<100/100 hits 100/100 mana 100/100 move [Sessiontest]>"
    )
    assert controller.observe_hoard_text(response, status)
    step = controller.hoard_excavation.poll(
        replace(first, sequence=2), now=3,
    )

    assert step.status == "trap_recovery_required"
    assert step.trap_kind == "poison"
    assert controller.hoard_excavation.audit()["trap_effects"] == ((2, "poison"),)


def test_quest_session_discards_excavation_text_after_assignment_changes():
    controller = QuestSessionController(
        phase="quest-target-run",
        expected_status=hoard_status(),
        hoard_excavation_checkpoint=hoard_checkpoint(),
    )
    assert controller.hoard_excavation is not None

    forwarded = controller.observe_hoard_text(
        "You hear a strange noise...\nYou feel unclean.",
        hoard_status((25305, 18022, 1778)),
    )

    assert not forwarded
    assert controller.hoard_excavation is None


def test_quest_session_drops_excavation_after_explicit_inactive_status():
    controller = QuestSessionController(
        phase="quest-target-run",
        expected_status=hoard_status(),
        hoard_excavation_checkpoint=hoard_checkpoint(),
    )
    inactive = hoard_status()
    inactive["active"] = 0

    forwarded = controller.observe_hoard_text(
        "You hear a strange noise...\nYou feel unclean.", inactive,
    )

    assert not forwarded
    assert controller.hoard_excavation is None


def test_quest_session_rejects_hoard_checkpoint_for_changed_assignment():
    checkpoint = hoard_checkpoint()
    changed_identity = (HOARD_IDENTITY[0], HOARD_IDENTITY[1], 1778)

    controller = QuestSessionController(
        phase="quest-target-run",
        expected_status=hoard_status(changed_identity),
        hoard_excavation_checkpoint=checkpoint,
    )

    assert controller.hoard_excavation is None
    issue = controller.hoard_excavation_restore_issue
    assert issue is not None and "does not match" in issue
    assert controller.checkpoint_hoard_excavation() is None


def test_quest_session_does_not_persist_hoard_checkpoint_after_assignment_changes():
    controller = QuestSessionController(
        phase="quest-target-run",
        expected_status=hoard_status(),
        hoard_excavation_checkpoint=hoard_checkpoint(),
    )

    assert controller.checkpoint_hoard_excavation(
        hoard_status((25305, 18022, 1778)),
    ) is None
    assert controller.checkpoint_hoard_excavation(
        {"active": 0, "type": "none"},
    ) is None


def test_policy_lifecycle_flags_share_the_live_session_owner(tmp_path):
    policy = StarterPolicy(spec(tmp_path), "fixture-password")
    policy.stage = "tutorial"
    policy.login_authenticated = True
    policy.in_world = True
    policy.world_boot_id = "boot-a"
    owner = LiveSessionState(CharacterState())

    policy.bind_session_state(owner)

    assert owner.phase == "tutorial"
    assert owner.authenticated is True
    assert owner.in_world is True
    assert owner.world_boot_id == "boot-a"
    policy.world_boot_id = "boot-b"
    policy.in_world = False
    assert owner.world_boot_id == "boot-b"
    assert owner.in_world is False

    with pytest.raises(RuntimeError, match="another session"):
        policy.bind_session_state(LiveSessionState(CharacterState()))


def test_active_runtime_controllers_have_one_session_owner(tmp_path):
    policy = StarterPolicy(spec(tmp_path), "fixture-password")
    policy.combat_active = True
    policy.combat_disarm_attempts = 2
    policy.fastwalk_outbound_index = 7
    policy.fastwalk_hunt_stop_index = 3
    policy.fastwalk_emergency_recall_pending = True
    policy.recovery_wake_command_pending = True
    owner = LiveSessionState(CharacterState())

    policy.bind_session_state(owner)

    assert owner.combat is policy._combat_session
    assert owner.combat.active is True
    assert owner.combat.disarm_attempts == 2
    assert owner.travel is policy._travel_session
    assert (owner.travel.outbound_index, owner.travel.hunt_stop_index) == (7, 3)
    assert owner.recovery is policy._recovery_session
    assert owner.recovery.emergency_recall_pending is True
    assert owner.recovery.wake_command_pending is True

    following = StarterPolicy(spec(tmp_path), "fixture-password")
    following.bind_session_state(owner)

    assert owner.travel is following._travel_session
    assert owner.travel.hunt_stop_index == 0
    assert owner.combat.active is False
    assert owner.recovery.emergency_recall_pending is False


def immediate_timer_queries(monkeypatch):
    original = QuestCooldownWait.poll

    def poll(self, *args, **kwargs):
        self.next_query_at = 0
        return original(self, *args, **kwargs)

    monkeypatch.setattr(QuestCooldownWait, "poll", poll)


class QuestConnection:
    def __init__(self, *, reject_target=False, omit_quest=False, drop_after_request=False):
        self.closed = False
        self.sent = []
        self.connects = 0
        self.pending = True
        self.reject_target = reject_target
        self.omit_quest = omit_quest
        self.drop_after_request = drop_after_request
        self.dropped = False
        self.quest = {"active": 0, "nextquest": 0, "total_points": 0}

    async def connect(self):
        self.connects += 1
        self.closed = False
        self.pending = True

    async def close(self):
        self.closed = True

    async def send_command(self, command):
        self.sent.append(command)
        self.pending = True
        if command == "quest request":
            self.quest = dict(active=1, complete=0, type="kill", mob_vnum=4003,
                              room_vnum=4010, giver_vnum=25305, countdown=10,
                              total_points=0)
        elif command == "kill target" and not self.reject_target:
            self.quest.update(complete=1, mob_vnum=-1)
        elif command == "quest complete":
            self.quest = dict(active=0, complete=0, mob_vnum=0, nextquest=15,
                              total_points=12, points=12)
        elif command == "quest abort":
            self.quest = dict(active=0, nextquest=15, total_points=0)
        elif command == "quest time":
            self.quest["nextquest"] = max(0, self.quest.get("nextquest", 0) - 1)

    async def read_available(self, timeout=0.25):
        if not self.pending:
            return ReadResult()
        self.pending = False
        if self.drop_after_request and not self.dropped and self.sent[-1:] == ["save"]:
            self.dropped = True
            self.closed = True
            self.quest = dict(active=0, nextquest=15, total_points=0)
            return ReadResult()
        return ReadResult(
            text="<100/100 hits 100/100 mana 100/100 move [Midgaard]>",
            gmcp_messages=[] if self.omit_quest else ["Char.Quest " + json.dumps(self.quest)],
        )


class ScriptedQuestPolicy(StarterPolicy):
    """Keep real policy state/ledger while making route execution deterministic."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_step = 0
        self.action_sent = False
        self.fastwalk_arrival_observed = True

    def on_connection_closed(self):
        super().on_connection_closed()
        self.auth_step = 0

    def next_decision(self, state):
        if not self.in_world:
            if self.auth_step == 0:
                return BotDecision(self.spec.name, "authenticate fixture")
            return BotDecision("fixture-password", "authenticate fixture", secret=True)
        if not self.action_sent and not self.return_home and not self.runtime_boundary_requested:
            return BotDecision({
                "quest-request": "quest request", "quest-target-run": "kill target",
                "quest-complete": "quest complete",
            }[self.fastwalk_route.name], "execute fixture objective")
        if not self.saved:
            return BotDecision("save", "acknowledge healer checkpoint")
        return BotDecision("quit", "end fixture session")

    def after_command(self, decision):
        super().after_command(decision)
        if not self.in_world:
            self.auth_step += 1
            if self.auth_step == 2:
                self.in_world = self.login_authenticated = True
        elif decision.command in {"quest request", "kill target", "quest complete"}:
            self.action_sent = True
            if decision.command == "kill target":
                self.completed_kills.append(dict(
                    mob_name="target", xp_gained=142, source_mobile_vnum=4003,
                    source_policy_id="quest-target-run", objective_eligible=True,
                ))
        elif decision.command == "save":
            self.saved = True


def run_session(tmp_path, monkeypatch, *, connection=None, planner=None, initial="quest-request", expected=None):
    monkeypatch.setenv("QUEST_TEST_PASSWORD", "fixture-password")
    monkeypatch.setattr(starter, "StarterPolicy", ScriptedQuestPolicy)
    connection = connection or QuestConnection()

    def next_phase(completed, state):
        quest = state["quest_status"]
        if completed == "quest-cooldown" and quest.get("nextquest") == 0:
            return phase("quest-request")
        if completed == "quest-request" and quest.get("active"):
            return phase("quest-target-run")
        if completed == "quest-target-run" and quest.get("complete"):
            return phase("quest-complete")
        return None

    runner = starter.StarterBotRunner(
        spec(tmp_path), tmp_path / "profile.yaml", connection_factory=lambda _: connection,
        character_state=healer(), fastwalk_route=route(initial),
        fastwalk_hunt_stops=phase(initial).hunt_stops, require_fastwalk_kill=False,
        allow_safe_fastwalk_abort=True, quest_phase=initial,
        quest_expected_status=expected,
        quest_wait_for_cooldown=initial == "quest-cooldown",
        quest_phase_planner=planner or next_phase, gear_catalog=GearCatalog({}),
        source_mobile_targets={}, source_mobile_level_ranges={},
        source_mobile_level_ranges_by_vnum={}, source_mobile_vnums_by_target_room={},
        source_mobile_special_profiles={}, source_mobile_special_profiles_by_vnum={},
        source_mobile_non_assisting_by_target_room={}, source_mobile_can_join_by_vnum={},
        source_mobile_aggressive_by_vnum={}, source_mobile_attack_programs_by_vnum={},
    )
    return asyncio.run(runner.run()), connection


def test_request_target_turnin_share_one_connection_and_keep_kill_evidence(tmp_path, monkeypatch):
    result, connection = run_session(tmp_path, monkeypatch)
    assert connection.connects == 1
    assert connection.sent.count("Sessiontest") == 1
    assert connection.sent.count("fixture-password") == 1
    assert connection.sent == ["Sessiontest", "fixture-password", "quest request", "save",
                               "kill target", "save", "quest complete", "save", "quit"]
    assert result.final_state["quest_status"]["total_points"] == 12
    assert len(result.final_state["campaign_objective_kills"]) == 1
    assert [item["phase"] for item in result.final_state["campaign_quest_phases"]] == [
        "quest-request", "quest-target-run", "quest-complete",
    ]
    with RunStorage(result.database_path) as storage:
        assert len(storage.list_mob_kills_for_run(result.run_id)) == 1


@pytest.mark.parametrize("options", [{"omit_quest": True}, {"drop_after_request": True}])
def test_missing_live_quest_or_disconnect_never_dispatches_cached_target(tmp_path, monkeypatch, options):
    _, connection = run_session(tmp_path, monkeypatch, connection=QuestConnection(**options))
    assert "kill target" not in connection.sent
    assert "quest complete" not in connection.sent
    assert connection.sent[-1] == "quit"


def test_unfinished_target_aborts_once_at_checkpoint(tmp_path, monkeypatch):
    result, connection = run_session(tmp_path, monkeypatch, connection=QuestConnection(reject_target=True))
    assert connection.sent.count("quest abort") == 1
    assert "quest complete" not in connection.sent
    assert result.final_state["quest_status"]["active"] == 0


def test_stale_target_at_login_is_not_executed(tmp_path, monkeypatch):
    _, connection = run_session(tmp_path, monkeypatch, initial="quest-target-run")
    assert "kill target" not in connection.sent


@pytest.mark.parametrize("changes", [{"room_vnum": "3019"}, {"hp": 0}, {"dead": True},
                                     {"enemies": [{"name": "attacker"}]}])
def test_handoff_requires_actual_live_healer_state(tmp_path, changes):
    old = StarterPolicy(spec(tmp_path), "secret")
    new = StarterPolicy(spec(tmp_path), "secret")
    old.in_world = old.login_authenticated = old.saved = True
    with pytest.raises(ValueError, match="healer checkpoint"):
        resume_policy_at_healer(old, new, healer(**changes))


def test_handoff_copies_capabilities_but_not_old_route_or_kill_state(tmp_path):
    old = StarterPolicy(spec(tmp_path), "secret")
    new = StarterPolicy(spec(tmp_path), "secret")
    old.in_world = old.login_authenticated = old.saved = True
    old.known_skills.add("armor")
    old.known_skill_levels["armor"] = 36
    old.completed_kills.append({"mob_name": "target"})
    old.fastwalk_abort_reason = None
    old.fastwalk_hunt_index = 9
    resume_policy_at_healer(old, new, healer())
    assert new.known_skill_levels == {"armor": 36}
    assert new.in_world and new.login_authenticated and new.prompt_ready
    assert new.completed_kills == []
    assert not new.saved
    new.known_skills.add("identify")
    assert "identify" not in old.known_skills


@pytest.mark.parametrize("structured_current", [True, False])
def test_handoff_retains_only_current_structured_equipment(tmp_path, structured_current):
    branch = ObjectSource(
        6104, "branch", "a long, grey branch", 5, (0, 2, 5, 7), 0,
        wear_flags=1 << 13, level=15,
    )
    light = replace(branch, vnum=6103, item_type=1)
    club = replace(
        branch, vnum=1521, keywords="club",
        short_description="a large club", level=3,
    )
    catalog = GearCatalog({item.vnum: item for item in (branch, light, club)})
    character = replace(spec(tmp_path), character_class="warrior")
    old = StarterPolicy(character, "secret", gear_catalog=catalog)
    new = StarterPolicy(character, "secret", gear_catalog=catalog)
    old.in_world = old.login_authenticated = old.saved = True
    old.gear_worn = [branch]
    old.gear_worn_structured_current = structured_current
    old.gear_wielded_vnum = branch.vnum
    old.gear_instance_sources = {"42": branch.vnum}
    old.gear_worn_instance_ids = {"42"}
    old.gear_inventory_source_hints = {"a large club": club.vnum}
    old.gear_command_queue = [("remove branch", "old phase command")]
    state = healer(level=29, inventory=[{"short_desc": "a large club", "quan": "1"}])

    resume_policy_at_healer(old, new, state)

    assert new.gear_worn_structured_current is structured_current
    assert new.gear_worn == ([branch] if structured_current else [])
    assert new.gear_wielded_vnum == (branch.vnum if structured_current else None)
    assert not new.gear_audited
    assert new.gear_command_queue == []
    if structured_current:
        new.gear_audit_pending = True
        new.last_equipment_audit_response = "[weapon] a long, grey branch\n"
        decision = new._gear_decision(state)
        assert decision is None or decision.command == "eq all"
        assert new.gear_worn == [branch]
        assert all(command != "remove branch" for command, _ in new.gear_command_queue)
        new.gear_instance_sources.clear()
        new.gear_worn_instance_ids.clear()
        new.gear_inventory_source_hints.clear()
        assert old.gear_instance_sources == {"42": branch.vnum}
        assert old.gear_worn_instance_ids == {"42"}
        assert old.gear_inventory_source_hints == {"a large club": club.vnum}


def test_handoff_preserves_weapon_loss_without_positive_identity(tmp_path):
    old = StarterPolicy(spec(tmp_path), "secret")
    new = StarterPolicy(spec(tmp_path), "secret")
    old.in_world = old.login_authenticated = old.saved = True
    old.primary_weapon_lost = old.disarm_recovery_failed = True
    old.primary_weapon_observed = False
    resume_policy_at_healer(old, new, healer())
    assert new.primary_weapon_lost and new.disarm_recovery_failed
    assert not new.primary_weapon_observed


def quest_world(population=1):
    return WorldSource(
        rooms={3001: RoomSource(3001, "Recall", "test.are", exits={
            "east": ExitSource("east", 9901, 0, -1),
        }), 9901: RoomSource(9901, "Quest room", "test.are")},
        mobiles={9900: MobileSource(9900, "guardian", "a guardian", 5,
                                   ACT_SENTINEL, 0, "test.are")},
        mob_resets=[MobReset(9900, 9901, population, ())],
    )


def active_quest(**changes):
    return dict(active=1, complete=0, type="kill", mob_vnum=9900,
                room_vnum=9901, countdown=10, giver_vnum=25305, **changes)


@pytest.mark.parametrize("population,expected", [(1, "quest-target-run"), (4, "quest-target-run"), (6, "quest-abort")])
def test_dynamic_quest_uses_existing_bounded_source_population_gate(tmp_path, population, expected):
    state = healer(level=5, quest_status=active_quest()).to_dict()
    planned = campaign._quest_session_next_phase(
        "quest-request", state, world=quest_world(population),
        gear_catalog=GearCatalog({}), character=spec(tmp_path),
    )
    assert planned.name == expected
    if planned.route:
        assert any(stop.source_mobile_vnum == 9900 for stop in planned.hunt_stops)


@pytest.mark.parametrize("completed,quest_changes,state_changes,expected", [
    ("quest-target-run", {}, {}, "quest-abort"),
    ("quest-request", {"countdown": 1}, {}, "quest-abort"),
    ("quest-request", {}, {"campaign_fastwalk_abort_reason": "route hazard"}, "quest-abort"),
    ("quest-target-run", {"complete": 1, "mob_vnum": -1}, {}, "quest-complete"),
    ("quest-target-run", {"complete": 1, "mob_vnum": -1, "giver_vnum": 123}, {}, "quest-abort"),
    ("quest-complete", {"active": 0, "mob_vnum": 0}, {}, None),
])
def test_quest_phase_planner_uses_live_outcome_not_cached_target(tmp_path, completed, quest_changes, state_changes, expected):
    state = healer(quest_status={**active_quest(), **quest_changes}).to_dict()
    state.update(state_changes)
    planned = campaign._quest_session_next_phase(
        completed, state, world=quest_world(), gear_catalog=GearCatalog({}),
        character=spec(tmp_path),
    )
    assert (planned.name if planned else None) == expected


def test_completed_goldmoon_quest_uses_short_registered_turnin_route(tmp_path):
    state = healer(
        level=29,
        quest_status={
            **active_quest(),
            "complete": 1,
            "mob_vnum": -1,
            "giver_vnum": 10001,
        },
    ).to_dict()

    planned = campaign._quest_session_next_phase(
        "quest-target-run", state, world=quest_world(),
        gear_catalog=GearCatalog({}), character=spec(tmp_path),
    )

    assert planned is not None and planned.name == "quest-complete"
    assert planned.route.name == "questmaster suturb complete"
    assert planned.route.commands == campaign.questmaster_route_for_level(1)


def test_later_phase_failure_preserves_prior_kill_in_terminal_event(tmp_path, monkeypatch):
    connection = QuestConnection()

    def fail_after_target(completed, state):
        if completed == "quest-request":
            return phase("quest-target-run")
        raise RuntimeError("turn-in planning failed")

    with pytest.raises(RuntimeError, match="turn-in planning failed"):
        run_session(tmp_path, monkeypatch, connection=connection, planner=fail_after_target)
    with RunStorage(spec(tmp_path).database) as storage:
        events = storage.list_events(1)
        terminal = [json.loads(row["payload_json"]) for row in events
                    if row["kind"] == "state"][-1]
        assert len(terminal["objective_kills"]) == 1
        assert len(storage.list_mob_kills_for_run(1)) == 1
    assert connection.closed


def test_phase_planner_cannot_repeat_an_already_completed_phase(tmp_path, monkeypatch):
    connection = QuestConnection()
    with pytest.raises(RuntimeError, match="phase repetition"):
        run_session(tmp_path, monkeypatch, connection=connection,
                    planner=lambda *_: phase("quest-request"))
    assert connection.sent.count("quest request") == 1
    assert connection.closed


def test_runtime_boundary_prevents_another_phase_and_aborts_once(tmp_path, monkeypatch):
    original = ScriptedQuestPolicy.next_decision

    def cap_after_request(self, state):
        if self.action_sent:
            self.runtime_boundary_requested = True
        return original(self, state)

    monkeypatch.setattr(ScriptedQuestPolicy, "next_decision", cap_after_request)
    _, connection = run_session(tmp_path, monkeypatch)
    assert "kill target" not in connection.sent
    assert connection.sent.count("quest abort") == 1
    assert connection.sent[-1] == "quit"


def test_changed_live_quest_identity_never_executes_the_saved_target(tmp_path, monkeypatch):
    connection = QuestConnection()
    connection.quest = active_quest()
    _, connection = run_session(
        tmp_path, monkeypatch, connection=connection, initial="quest-target-run",
        expected={**active_quest(), "mob_vnum": 123},
    )
    assert "kill target" not in connection.sent
    assert connection.sent.count("quest abort") == 1


def test_failed_policy_construction_does_not_duplicate_prior_kill(tmp_path, monkeypatch):
    original = ScriptedQuestPolicy.__init__

    def fail_turnin(self, *args, **kwargs):
        if kwargs["fastwalk_route"].name == "quest-complete":
            raise ValueError("fixture turn-in construction failure")
        original(self, *args, **kwargs)

    monkeypatch.setattr(ScriptedQuestPolicy, "__init__", fail_turnin)
    with pytest.raises(ValueError, match="construction failure"):
        run_session(tmp_path, monkeypatch)
    with RunStorage(spec(tmp_path).database) as storage:
        terminal = [json.loads(row["payload_json"]) for row in storage.list_events(1)
                    if row["kind"] == "state"][-1]
        assert len(terminal["objective_kills"]) == 1
        assert len(storage.list_mob_kills_for_run(1)) == 1


def test_online_cooldown_request_target_and_reward_share_one_connection(tmp_path, monkeypatch):
    connection = QuestConnection()
    connection.quest["nextquest"] = 2
    immediate_timer_queries(monkeypatch)
    result, connection = run_session(tmp_path, monkeypatch, connection=connection, initial="quest-cooldown")
    assert connection.connects == 1
    assert connection.sent.count("quest time") == 2
    assert connection.sent.count("quest request") == 1
    assert connection.sent.count("quit") == 1
    assert connection.sent.index("quest time") < connection.sent.index("quest request")
    assert result.final_state["quest_status"]["total_points"] == 12
    assert result.final_state["campaign_quest_frontier_request"]["session_revision"] == 235


def test_cooldown_poll_waits_for_actual_server_progress_and_stops_stall():
    controller = QuestCooldownWait()
    state = healer(quest_status={"nextquest": 14})
    initial = controller.poll(state, now=0, food_keyword=None, has_water_skin=False)
    assert initial.command == "quest time" and initial.wait_seconds == 0
    assert controller.poll(state, now=10, food_keyword=None, has_water_skin=False).command is None
    assert controller.poll(state, now=30, food_keyword=None, has_water_skin=False).command == "quest time"
    assert controller.poll(state, now=179, food_keyword=None, has_water_skin=False).status == "waiting"
    assert controller.poll(state, now=180, food_keyword=None, has_water_skin=False).status == "stopped"
    state.quest_status["nextquest"] = 13
    assert controller.poll(state, now=181, food_keyword=None, has_water_skin=False).status == "waiting"
    state.quest_status["nextquest"] = 0
    assert controller.poll(state, now=182, food_keyword=None, has_water_skin=False).status == "ready"


def test_cooldown_checks_again_quickly_when_less_than_a_minute_remains():
    controller = QuestCooldownWait()
    state = healer(quest_status={"nextquest": 1})
    assert controller.poll(state, now=0, food_keyword=None, has_water_skin=False).command == "quest time"
    assert controller.poll(state, now=4, food_keyword=None, has_water_skin=False).command is None
    assert controller.poll(state, now=5, food_keyword=None, has_water_skin=False).command == "quest time"
    state.quest_status["nextquest"] = 0
    assert controller.poll(state, now=6, food_keyword=None, has_water_skin=False).status == "ready"


def test_cooldown_observes_progress_and_resource_needs_between_queries():
    controller = QuestCooldownWait()
    state = healer(quest_status={"nextquest": 5})
    assert controller.poll(state, now=0, food_keyword="pie", has_water_skin=True).command == "quest time"
    state.quest_status["nextquest"] = 4
    step = controller.poll(state, now=3, food_keyword="pie", has_water_skin=True)
    assert step.status == "waiting" and step.command is None
    assert controller.lowest_remaining == 4 and controller.last_progress_at == 3
    state.hunger = 5
    assert controller.poll(state, now=4, food_keyword="pie", has_water_skin=True).command == "eat pie"
    state.quest_status["nextquest"] = 0
    assert controller.poll(state, now=5, food_keyword="pie", has_water_skin=True).status == "ready"


@pytest.mark.parametrize("field,keyword,water,command", [
    ("hunger", "pie", True, "eat pie"), ("thirst", "pie", True, "drink skin"),
    ("hunger", None, True, None), ("thirst", "pie", False, None),
])
def test_connected_wait_consumes_only_carried_resources_with_two_attempt_bound(field, keyword, water, command):
    controller = QuestCooldownWait()
    state = healer(quest_status={"nextquest": 14}, **{field: 5})
    first = controller.poll(state, now=0, food_keyword=keyword, has_water_skin=water)
    assert first.command == command
    if command is not None:
        assert controller.poll(state, now=1, food_keyword=keyword, has_water_skin=water).command == command
    assert controller.poll(state, now=2, food_keyword=keyword, has_water_skin=water).status == "stopped"


def test_connected_wait_audits_unknown_nutrition_once():
    controller = QuestCooldownWait()
    state = healer(quest_status={"nextquest": 14}, hunger=None)
    assert controller.poll(state, now=0, food_keyword=None, has_water_skin=False).command == "score"
    assert controller.poll(state, now=1, food_keyword=None, has_water_skin=False).status == "stopped"


@pytest.mark.parametrize("remaining,boot,level,blocked", [
    (14, "boot", 8, True), (15, "boot", 8, True), (13, "boot", 8, False),
    (14, "new-boot", 8, False), (14, "boot", 9, False),
])
def test_capped_cooldown_reopens_only_for_observed_progress_or_changed_frontier(remaining, boot, level, blocked):
    state = healer(level=level, quest_status={"nextquest": remaining}).to_dict()
    state.update(world_boot_id=boot, campaign_quest_cooldown_wait={
        "remaining": 14, "boot_id": "boot", "level": 8,
    })
    assert campaign._quest_cooldown_wait_has_no_progress(state) is blocked


@pytest.mark.parametrize("status", [{}, {"nextquest": "bad"}, {"nextquest": -1}])
def test_connected_wait_rejects_missing_or_malformed_cooldown(status):
    assert QuestCooldownWait().poll(
        healer(quest_status=status), now=0, food_keyword=None, has_water_skin=False,
    ).status == "stopped"


def test_capped_wait_preserves_reduced_counter_without_request_attempt(tmp_path, monkeypatch):
    connection = QuestConnection()
    connection.quest["nextquest"] = 3
    original_decision = ScriptedQuestPolicy.next_decision
    immediate_timer_queries(monkeypatch)

    def cap_at_one(self, state):
        if self.return_home and state.quest_status.get("nextquest") == 1:
            self.runtime_boundary_requested = True
            self.fastwalk_abort_reason = "segment runtime boundary requested a safe healer return"
        return original_decision(self, state)

    monkeypatch.setattr(ScriptedQuestPolicy, "next_decision", cap_at_one)
    result, connection = run_session(tmp_path, monkeypatch, connection=connection, initial="quest-cooldown")
    assert result.final_state["quest_status"]["nextquest"] == 1
    assert "campaign_quest_frontier_request" not in result.final_state
    assert "quest request" not in connection.sent
    assert connection.sent[-1] == "quit"


@pytest.mark.parametrize("policy_id", ["quest-cooldown", "quest-frontier-cooldown"])
def test_public_campaign_dispatch_enables_connected_wait(tmp_path, monkeypatch, policy_id):
    from dd4tester.progression import _QUEST_REQUEST_POLICY
    captured = {}

    class FakeRunner:
        def __init__(self, *args, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return None

    monkeypatch.setattr(campaign, "StarterBotRunner", FakeRunner)
    asyncio.run(campaign._run_policy_segment(
        spec(tmp_path), tmp_path / "profile.yaml",
        replace(_QUEST_REQUEST_POLICY, policy_id=policy_id),
        current_state=healer(quest_status={"nextquest": 14}).to_dict(),
        character_level=8,
    ))
    assert captured["quest_wait_for_cooldown"] is True
    assert captured["quest_phase"] == "quest-cooldown"
    assert callable(captured["quest_phase_planner"])
    assert captured["fastwalk_hunt_stops"][0].actions == ("quest request",)
    route = captured["fastwalk_route"]
    assert route.route_origin_room_vnum == 3001
    assert route.commands == campaign.questmaster_route_for_level(8)


def test_public_campaign_dispatch_uses_short_quest_turnin_route(tmp_path, monkeypatch):
    from dd4tester.progression import _QUEST_REQUEST_POLICY
    captured = {}

    class FakeRunner:
        def __init__(self, *args, **kwargs):
            captured.update(kwargs)

        async def run(self):
            return None

    monkeypatch.setattr(campaign, "StarterBotRunner", FakeRunner)
    quest_status = {
        "active": 1,
        "complete": 1,
        "type": "retrieve",
        "object_vnum": 79,
        "giver_vnum": 10001,
    }
    asyncio.run(campaign._run_policy_segment(
        spec(tmp_path), tmp_path / "profile.yaml",
        replace(
            _QUEST_REQUEST_POLICY,
            policy_id="quest-complete-test",
            execution="quest-complete",
        ),
        current_state=healer(level=29, quest_status=quest_status).to_dict(),
        character_level=29,
    ))

    route = captured["fastwalk_route"]
    assert route.name == "questmaster suturb complete"
    assert route.commands == campaign.questmaster_route_for_level(1)


def test_cooldown_completion_plans_the_source_questmaster_request(tmp_path):
    planned = campaign._quest_session_next_phase(
        "quest-cooldown",
        healer(
            level=29,
            quest_status={"active": 0, "nextquest": 0},
        ).to_dict(),
        world=quest_world(), gear_catalog=GearCatalog({}), character=spec(tmp_path),
    )
    assert planned.name == "quest-request"
    assert planned.hunt_stops[0].actions == ("quest request",)
    assert planned.route.route_origin_room_vnum == 3001
    assert planned.route.commands == campaign.questmaster_route_for_level(29)


def test_questmaster_route_keeps_recall_origin_and_rejects_unknown_room():
    route = campaign._questmaster_fastwalk(
        name="questmaster Goldmoon request",
        level=29,
        current_state={"room_vnum": "3001"},
    )
    assert route.route_origin_room_vnum == 3001
    assert route.commands == campaign.questmaster_route_for_level(29)

    with pytest.raises(ValueError, match="registered only"):
        campaign._questmaster_fastwalk(
            name="questmaster Goldmoon request",
            level=29,
            current_state={"room_vnum": "18013"},
        )


def test_request_history_does_not_block_after_the_live_timer_expires(tmp_path):
    state = healer(
        level=29,
        quest_status={"active": 0, "nextquest": 15, "total_points": 0},
    ).to_dict()
    state.update(
        world_boot_id="boot-1",
        stats={"fame": 0},
        campaign_quest_frontier_request={
            "boot_id": "boot-1",
            "level": 29,
            "session_revision": 235,
            "reason": "live quest request dispatched",
        },
    )

    assert campaign._required_quest_cooldown_wait_allowed(
        state, has_food=True,
    )
    cooldown_policy = campaign.policy_for(
        29,
        "warrior",
        has_food=True,
        has_weapon=True,
        quest_level_qp_required=1,
        quest_level_qp_shortfall=1,
        quest_status=state["quest_status"],
        quest_request_allowed=(
            not campaign.snapshot_quest_status(state["quest_status"]).active
            and campaign.snapshot_quest_status(state["quest_status"]).nextquest <= 0
        ),
    )
    assert cooldown_policy.execution != "quest-request"

    state["quest_status"]["nextquest"] = 1
    assert campaign._required_quest_cooldown_wait_allowed(
        state, has_food=True,
    )
    state["quest_status"]["nextquest"] = 0
    next_phase = campaign._quest_session_next_phase(
        "quest-cooldown", state, world=quest_world(),
        gear_catalog=GearCatalog({}), character=spec(tmp_path),
    )
    assert next_phase is not None and next_phase.name == "quest-request"


def test_live_runner_releases_sqlite_writer_at_every_adapter_boundary(tmp_path, monkeypatch):
    class OtherWriterConnection(QuestConnection):
        def __init__(self):
            super().__init__()
            self.boundaries = []

        def check_writer(self, boundary):
            with sqlite3.connect(spec(tmp_path).database, timeout=0.01) as other:
                other.execute("CREATE TABLE IF NOT EXISTS writer_probe (boundary TEXT)")
                other.execute("INSERT INTO writer_probe VALUES (?)", (boundary,))
            self.boundaries.append(boundary)

        async def connect(self):
            self.check_writer("connect")
            await super().connect()

        async def read_available(self, timeout=0.25):
            self.check_writer("read")
            return await super().read_available(timeout)

        async def send_command(self, command):
            self.check_writer("send")
            await super().send_command(command)

        async def close(self):
            self.check_writer("close")
            await super().close()

    connection = OtherWriterConnection()
    connection.quest["nextquest"] = 2
    immediate_timer_queries(monkeypatch)
    result, _ = run_session(tmp_path, monkeypatch, connection=connection, initial="quest-cooldown")
    assert result.status == "success"
    assert set(connection.boundaries) == {"connect", "read", "send", "close"}
    assert len(connection.boundaries) > 20


def test_storage_flush_releases_a_partial_event_batch(tmp_path):
    with RunStorage(spec(tmp_path).database, event_commit_interval=100) as storage:
        run_id = storage.create_run(scenario_name="fixture", scenario_path=tmp_path / "fixture.yaml")
        storage.record_event(run_id, kind="response", payload={"text": "partial batch"})
        assert storage.connection.in_transaction
        storage.flush()
        assert not storage.connection.in_transaction
        assert storage._events_since_commit == 0
        with sqlite3.connect(storage.path, timeout=0.01) as other:
            other.execute("UPDATE runs SET status='running' WHERE id=?", (run_id,))


def test_quest_markers_survive_campaign_checkpoint_merging():
    previous = healer(quest_status={"nextquest": 14}).to_dict()
    previous.update(campaign_quest_cooldown_wait={"remaining": 14, "boot_id": "boot", "level": 8},
                    campaign_quest_frontier_request={"boot_id": "older", "level": 7})
    current = healer(quest_status={"nextquest": 12}).to_dict()
    end = campaign._campaign_segment_end_state(previous, current, execution="quest-request")
    assert end["campaign_quest_cooldown_wait"] == previous["campaign_quest_cooldown_wait"]
    assert end["campaign_quest_frontier_request"] == previous["campaign_quest_frontier_request"]
    current["campaign_quest_frontier_request"] = {"boot_id": "boot", "level": 8}
    end = campaign._campaign_segment_end_state(previous, current, execution="quest-request")
    assert end["campaign_quest_frontier_request"] == current["campaign_quest_frontier_request"]


def test_cleared_cooldown_requests_immediately_with_bounded_time_remaining(tmp_path, monkeypatch):
    original_spec = spec
    monkeypatch.setattr(__import__(__name__), "spec", lambda path: replace(original_spec(path), max_runtime=30))
    connection = QuestConnection()
    connection.quest["nextquest"] = 1
    immediate_timer_queries(monkeypatch)
    result, connection = run_session(tmp_path, monkeypatch, connection=connection, initial="quest-cooldown")
    assert result.final_state["quest_status"]["nextquest"] == 0
    assert "quest request" in connection.sent
    assert "quest abort" not in connection.sent
    assert connection.sent.index("quest time") < connection.sent.index("quest request")


def test_connected_quest_wait_outlives_generic_repeated_command_watchdog(tmp_path, monkeypatch):
    class DelayedCooldownConnection(QuestConnection):
        def __init__(self):
            super().__init__()
            self.quest["nextquest"] = 1
            self.timer_queries = 0

        async def send_command(self, command):
            if command != "quest time":
                return await super().send_command(command)
            self.sent.append(command)
            self.pending = True
            self.timer_queries += 1
            if self.timer_queries > 7:
                self.quest["nextquest"] = 0

    immediate_timer_queries(monkeypatch)
    connection = DelayedCooldownConnection()
    result, connection = run_session(
        tmp_path, monkeypatch, connection=connection, initial="quest-cooldown",
    )

    timer_queries = [
        index for index, command in enumerate(connection.sent)
        if command == "quest time"
    ]
    assert len(timer_queries) == 8
    assert timer_queries[-1] < connection.sent.index("quest request")
    assert result.final_state["quest_status"]["total_points"] == 12


def test_connected_wait_drains_chatter_before_next_query_without_sleeping_reader(tmp_path, monkeypatch):
    waits = []
    original_sleep = asyncio.sleep

    async def observe_sleep(delay, *args, **kwargs):
        waits.append(delay)
        await original_sleep(0)

    class ChatteringConnection(QuestConnection):
        queued = 0
        query_count = 0

        async def send_command(self, command):
            if command != "quest time":
                return await super().send_command(command)
            self.sent.append(command)
            self.query_count += 1
            self.queued = 3

        async def read_available(self, timeout=0.25):
            if self.queued:
                self.queued -= 1
                if self.queued:
                    return ReadResult(text="The Healer chants.\n<100/100 hits 100/100 mana 100/100 move [Midgaard]>")
                self.quest["nextquest"] = 0
                self.pending = True
            return await super().read_available(timeout)

    monkeypatch.setattr(asyncio, "sleep", observe_sleep)
    connection = ChatteringConnection()
    connection.quest["nextquest"] = 1
    result, _ = run_session(tmp_path, monkeypatch, connection=connection, initial="quest-cooldown")
    assert connection.query_count == 1
    assert not any(delay >= 30 for delay in waits)
    assert result.final_state["quest_status"]["total_points"] == 12
