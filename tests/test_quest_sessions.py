import asyncio
import json
import sqlite3
from dataclasses import replace

import pytest

from dd4tester import campaign, starter
from dd4tester.character import CharacterSpec
from dd4tester.connection import ReadResult
from dd4tester.equipment import GearCatalog
from dd4tester.fastwalks import Fastwalk
from dd4tester.hunt_candidates import ACT_SENTINEL, ExitSource, MobileSource, MobReset, RoomSource, WorldSource
from dd4tester.sessions import QuestCooldownWait, QuestPhase, resume_policy_at_healer
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
    original = QuestCooldownWait.poll
    monkeypatch.setattr(QuestCooldownWait, "poll", lambda self, *a, **kw: replace(
        original(self, *a, **kw), wait_seconds=0,
    ))
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
    assert initial.command == "quest time" and initial.wait_seconds == 30
    assert controller.poll(state, now=179, food_keyword=None, has_water_skin=False).status == "waiting"
    assert controller.poll(state, now=180, food_keyword=None, has_water_skin=False).status == "stopped"
    state.quest_status["nextquest"] = 13
    assert controller.poll(state, now=181, food_keyword=None, has_water_skin=False).status == "waiting"
    state.quest_status["nextquest"] = 0
    assert controller.poll(state, now=182, food_keyword=None, has_water_skin=False).status == "ready"


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
    original_poll = QuestCooldownWait.poll
    original_decision = ScriptedQuestPolicy.next_decision
    monkeypatch.setattr(QuestCooldownWait, "poll", lambda self, *a, **kw: replace(
        original_poll(self, *a, **kw), wait_seconds=0,
    ))

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


def test_cooldown_completion_plans_the_source_questmaster_request(tmp_path):
    planned = campaign._quest_session_next_phase(
        "quest-cooldown", healer(quest_status={"active": 0, "nextquest": 0}).to_dict(),
        world=quest_world(), gear_catalog=GearCatalog({}), character=spec(tmp_path),
    )
    assert planned.name == "quest-request"
    assert planned.hunt_stops[0].actions == ("quest request",)


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
    original = QuestCooldownWait.poll
    monkeypatch.setattr(QuestCooldownWait, "poll", lambda self, *a, **kw: replace(
        original(self, *a, **kw), wait_seconds=0,
    ))
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


def test_cleared_cooldown_does_not_start_a_quest_with_insufficient_remaining_time(tmp_path, monkeypatch):
    original_spec = spec
    monkeypatch.setattr(__import__(__name__), "spec", lambda path: replace(original_spec(path), max_runtime=30))
    connection = QuestConnection()
    connection.quest["nextquest"] = 1
    original = QuestCooldownWait.poll
    monkeypatch.setattr(QuestCooldownWait, "poll", lambda self, *a, **kw: replace(
        original(self, *a, **kw), wait_seconds=0,
    ))
    result, connection = run_session(tmp_path, monkeypatch, connection=connection, initial="quest-cooldown")
    assert result.final_state["quest_status"]["nextquest"] == 0
    assert result.final_state["campaign_quest_request_deferred"] is True
    assert "quest request" not in connection.sent
    assert "quest abort" not in connection.sent
    assert connection.sent[-1] == "quit"
