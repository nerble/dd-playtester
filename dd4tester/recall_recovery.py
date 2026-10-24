"""One scanned, source-safe step out of a non-recallable room."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Collection, Mapping

from .hunt_candidates import (
    EX_WALL, SECT_AIR, SECT_UNDERWATER, SECT_UNDERWATER_GROUND,
    SECT_WATER_NOSWIM, SECT_WATER_SWIM, HuntCandidate, WorldSource,
    source_room_level_rejection, source_route_hazard_rejections,
)
from .observations import _DD4_PROMPT
from .state import CharacterState


RECALL_ROUTE_REVALIDATION_KEY = "campaign_recall_route_revalidation"


def recall_route_revalidation_pending(state: Mapping[str, Any], candidate: HuntCandidate, policy_id: str) -> bool:
    marker = state.get(RECALL_ROUTE_REVALIDATION_KEY)
    return bool(
        isinstance(marker, Mapping) and marker.get("revision") == 1
        and marker.get("status") == "pending" and marker.get("policy_id") == policy_id
        and marker.get("level") == state.get("level") and marker.get("boot_id") == state.get("world_boot_id")
        and marker.get("source_revision") == state.get("campaign_source_revision")
        and marker.get("mobile_vnum") == candidate.mobile_vnum
        and marker.get("reset_room_vnum") == candidate.room_vnum
    )


def _clear_scan(response: str, direction: str) -> bool:
    phrase = {"up": "upwards", "down": "downwards"}.get(direction, f"to the {direction}")
    return bool(
        _DD4_PROMPT.search(response)
        and not re.search(r"\b(?:one room|a closed .+? right here)\b", response, re.I)
        and (f"You can't see anything {phrase}." in response
             or re.search(rf"\b(?:two|three|four|five|six) rooms {re.escape(phrase)}\.", response))
    )


def _midgaard_recall_arrival(response: str) -> bool:
    """Recognize DD4's canonical recall-room text before GMCP catches up."""
    return re.search(
        r"(?mi)^\s*The Temple Of Midgaard\s*$",
        response,
    ) is not None


def repaired_recall_route_evidence(
    failed: Mapping[str, Any], recovery: Mapping[str, Any],
    kills: Collection[Mapping[str, Any]], current: Mapping[str, Any],
    candidate: HuntCandidate, world: WorldSource, directory: Path,
    *, terminal_evidence: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Bind one failed productive return to its immediately verified escape."""
    try:
        start, end, recovery_start, recovered = (
            json.loads(row.get(column) or "{}")
            for row, column in ((failed, "start_state_json"), (failed, "end_state_json"),
                                (recovery, "start_state_json"), (recovery, "end_state_json"))
        )
    except (TypeError, ValueError):
        return None
    if not all(isinstance(s, Mapping) for s in (start, end, recovery_start, recovered)):
        return None
    level, boot, revision = (current.get(k) for k in ("level", "world_boot_id", "campaign_source_revision"))
    policy_id = failed.get("phase")
    hp, maximum = current.get("hp"), current.get("max_hp")
    error = re.fullmatch(
        r"recall-only fastwalk did not reach the Midgaard healer route from room '.+' \((\d+)\)",
        str(failed.get("error") or ""),
    )
    if (
        type(level) is not int or level < 1 or not boot or not revision
        or type(failed.get("run_id")) is not int or type(recovery.get("run_id")) is not int
        or type(failed.get("sequence")) is not int
        or recovery.get("sequence") != failed["sequence"] + 1
        or failed.get("campaign_id") != recovery.get("campaign_id")
        or failed.get("execution_status") != "failed" or failed.get("safety_outcome") != "safe"
        or recovery.get("phase") != "return-home" or recovery.get("status") != "success"
        or recovery.get("execution_status") != "success" or recovery.get("safety_outcome") != "safe"
        or type(failed.get("command_count")) is not int or failed["command_count"] < 1
        or error is None or error[1] != str(end.get("room_vnum"))
        or str(current.get("room_vnum")) != "3054"
        or current.get("dead") is not False or current.get("in_combat") is not False
        or type(hp) is not int or type(maximum) is not int or maximum <= 0 or hp < maximum * .95
        or any(s.get("level") != level or s.get("world_boot_id") != boot
               or s.get("campaign_source_revision") != revision or s.get("dead") is not False
               or s.get("in_combat") is not False for s in (start, end, recovery_start, recovered))
        or str(start.get("room_vnum")) != "3054" or str(recovered.get("room_vnum")) != "3054"
        or recovery_start.get("room_vnum") != end.get("room_vnum")
        or type(start.get("xp")) is not int or type(end.get("xp")) is not int
        or end["xp"] <= start["xp"] or recovery_start.get("xp") != end["xp"]
        or recovered.get("xp") != end["xp"]
        or any(type(s.get("campaign_xp_loss_total")) is not int for s in (start, end, recovery_start, recovered))
        or len({s["campaign_xp_loss_total"] for s in (start, end, recovery_start, recovered)}) != 1
        or type(current.get("xp")) is not int or current["xp"] < end["xp"]
        or type(current.get("campaign_xp_loss_total")) is not int
        or current["campaign_xp_loss_total"] < end["campaign_xp_loss_total"]
        or terminal_evidence.get("error") != failed.get("error")
        or terminal_evidence.get("state") != "failed"
        or terminal_evidence.get("fastwalk_abort_reason")
        or any(terminal_evidence.get(k) for k in (
            "fastwalk_crowded", "fastwalk_target_absent", "fastwalk_target_vnum_mismatch",
            "fastwalk_unattackable_target", "fastwalk_source_below_band_sightings",
        ))
    ):
        return None
    recorded = start.get("campaign_source_ranked_hunt_candidate")
    consider = terminal_evidence.get("fastwalk_source_consider_outcomes")
    if (
        not isinstance(recorded, Mapping) or not isinstance(consider, Mapping)
        or consider.get(policy_id) is not True or recorded.get("policy_id") != policy_id
        or recorded.get("mobile_vnum") != candidate.mobile_vnum
        or recorded.get("room_vnum") != candidate.room_vnum
        or recorded.get("source_revision") != revision
        or tuple(recorded.get("route") or ()) != candidate.route
    ):
        return None
    eligible_kills = [kill for kill in kills if (
        kill.get("run_id") == failed["run_id"] and kill.get("boot_id") == boot
        and kill.get("source_policy_id") == policy_id
        and kill.get("source_mobile_vnum") == candidate.mobile_vnum
        and kill.get("objective_eligible") in (True, 1)
        and kill.get("below_useful_band") in (False, 0)
        and kill.get("route_gate") in (False, 0)
        and type(kill.get("xp_gained")) is int and kill["xp_gained"] > level * 10
    )]
    audit = recovered.get("campaign_adjacent_recall_escape")
    plan = adjacent_recall_exit(world, directory, end.get("room_vnum"), level)
    if (
        not eligible_kills or not isinstance(audit, Mapping) or plan is None
        or audit.get("stage") != "complete" or audit.get("commands_sent") != 3 or audit.get("failure")
        or audit.get("origin") != str(end.get("room_vnum"))
        or (audit.get("direction"), audit.get("destination")) != plan
        or not _clear_scan(str(audit.get("scan_response") or ""), plan[0])
    ):
        return None
    return {
        "revision": 1, "status": "pending", "policy_id": policy_id,
        "level": level, "boot_id": boot, "source_revision": revision,
        "mobile_vnum": candidate.mobile_vnum, "reset_room_vnum": candidate.room_vnum,
        "failed_run_id": failed["run_id"], "failed_segment_id": failed["id"],
        "recovery_run_id": recovery["run_id"], "recovery_segment_id": recovery["id"],
        "escape": dict(audit), "objective_xp": sum(k["xp_gained"] for k in eligible_kills),
        "max_objective_kill_xp": max(k["xp_gained"] for k in eligible_kills),
        "reason": "one route revalidation after a productive failed recall and its verified adjacent escape",
    }


def adjacent_recall_exit(
    world: WorldSource | None, directory: Path, room_vnum: str | None, level: int,
) -> tuple[str, str] | None:
    """Find one open ordinary exit whose source default recall is Midgaard."""
    try:
        origin = world.rooms.get(int(room_vnum)) if world is not None else None
    except (TypeError, ValueError):
        return None
    if (origin is None or not origin.no_recall or origin.random_exits
            or origin.area_file.casefold() == "purgator.are"):
        return None
    for direction, exit_source in origin.exits.items():
        target = world.rooms.get(exit_source.destination)
        if (
            direction not in {"north", "east", "south", "west", "up", "down"}
            or exit_source.closed or exit_source.locked or exit_source.flags & EX_WALL
            or target is None or target.no_recall or target.random_exits
            or target.sector_type in {
                SECT_AIR, SECT_WATER_SWIM, SECT_WATER_NOSWIM,
                SECT_UNDERWATER, SECT_UNDERWATER_GROUND,
            }
            or source_room_level_rejection(target, level)
            or source_route_hazard_rejections(
                world, (origin.vnum, target.vnum), character_level=level,
                require_no_combat_hazards=True, combat_at_destination=False,
            )
        ):
            continue
        try:
            text = (directory / target.area_file).read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        match = re.search(r"(?m)^#RECALL\s+(\d+)", text)
        if (int(match[1]) if match else 3001) == 3001:
            return direction, str(target.vnum)
    return None


@dataclass
class AdjacentRecallEscape:
    origin: str
    direction: str
    destination: str
    stage: str = "new"
    pending_room: str | None = None
    response: str = ""
    scan_response: str = ""
    deadline: float | None = None
    failure: str | None = None
    commands_sent: int = 0

    def observe(self, text: str) -> None:
        if self.deadline is not None:
            self.response = (self.response + text)[-8000:]

    def expire(self, now: float) -> bool:
        if self.deadline is not None and now >= self.deadline and not _DD4_PROMPT.search(self.response):
            self.failure = "adjacent recall escape response timed out after five seconds"
            return True
        return False

    def _send(self, command: str, stage: str, room: str, now: float) -> str:
        self.commands_sent += 1
        self.stage, self.pending_room = stage, room
        self.response, self.deadline = "", now + 5
        return command

    def next_command(self, state: CharacterState, *, now: float) -> str | None:
        self.expire(now)
        if self.failure or self.stage == "complete":
            return None
        try:
            awake = state.position is not None and int(state.position) >= 6
        except (TypeError, ValueError):
            awake = False
        if (
            state.dead or state.in_combat or state.combat_target
            or not state.hp or not state.max_hp or state.hp < state.max_hp * 0.5
            or state.move is None or state.move < 10
            or not awake
        ):
            self.failure = "adjacent recall escape requires an awake noncombat character with health and movement"
            return None
        if self.deadline is not None:
            if not _DD4_PROMPT.search(self.response):
                return None
            delayed_recall_room = bool(
                self.stage == "recalling"
                and str(self.pending_room) == "3001"
                and _midgaard_recall_arrival(self.response)
            )
            if state.room_vnum != self.pending_room and not delayed_recall_room:
                self.failure = "adjacent recall escape did not reach its exact expected room"
                return None
            self.deadline = None
            if self.stage == "recalling":
                self.stage = "complete"
                return None
            if self.stage == "scanning":
                self.scan_response = self.response
                if not _clear_scan(self.response, self.direction):
                    self.failure = "adjacent recall escape scan is occupied, closed, or incomplete"
                    return None
        if self.stage in {"new", "scanning"}:
            live_exit = state.exits.get(self.direction, state.exits.get(self.direction[0]))
            if state.room_vnum != self.origin or str(live_exit) != self.destination:
                self.failure = "adjacent recall escape live exit differs from the source plan"
                return None
            if self.stage == "new":
                return self._send(f"scan {self.direction}", "scanning", self.origin, now)
            return self._send(self.direction, "stepping", self.destination, now)
        if self.stage == "stepping":
            return self._send("recall", "recalling", "3001", now)
        self.failure = "adjacent recall escape reached an unexpected phase"
        return None

    def evidence(self) -> dict:
        return {"origin": self.origin, "direction": self.direction,
                "destination": self.destination, "stage": self.stage,
                "commands_sent": self.commands_sent, "failure": self.failure,
                "scan_response": self.scan_response}
