"""Bounded evidence for reusing an existing banked working reserve."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping, Sequence
from typing import Any


WORKING_RESERVE_COPPER = 1_000
BANK_RESERVE_HANDOFF_KEY = "campaign_bank_reserve_handoff"
_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_BALANCE = re.compile(
    r"You currently have (\d+) platinum, (\d+) gold, (\d+) silver and "
    r"(\d+) copper coins in the bank\.\s*[\r\n]",
)


def bank_reserve_receipt(
    segments: Sequence[Mapping[str, Any]],
    load_events: Callable[[int], Sequence[Mapping[str, Any]]],
    *,
    character_name: str,
) -> dict[str, Any] | None:
    """Use only the latest bank visit; a newer failed visit closes old proof."""
    recent = sorted(segments, key=lambda row: int(row["id"]), reverse=True)[:256]
    bank_visits = [dict(row) for row in recent
                   if row["phase"] == "bank-excess-coins"]
    if not bank_visits:
        return None
    visit = max(bank_visits, key=lambda row: int(row["id"]))
    if visit.get("status") != "success" or not visit.get("run_id"):
        return None
    try:
        end = json.loads(visit.get("end_state_json") or "null")
        if not isinstance(end, Mapping):
            return None
        currencies = end.get("currencies") or {}
        carried = sum(int(currencies.get(key, 0)) * weight for key, weight in (
            ("platinum", 1000), ("gold", 100), ("silver", 10), ("copper", 1),
        ))
    except (TypeError, ValueError, AttributeError):
        return None
    if (str(end.get("name", "")).casefold() != character_name.casefold()
            or str(end.get("room_vnum")) != "3054"
            or end.get("dead") or end.get("in_combat")
            or carried < WORKING_RESERVE_COPPER):
        return None

    # DD4's successful withdrawal prints the teller's thanks and do_balance().
    # Keep both in this command's bounded reply, never in a later command's.
    command = None
    reply = ""
    receipt = None
    thanks = re.compile(r"Thank you for your custom " + re.escape(character_name) + r"\.")
    for event in load_events(int(visit["run_id"]))[-512:]:
        try:
            payload = json.loads(event["payload_json"])
        except (TypeError, ValueError):
            return None
        if not isinstance(payload, Mapping):
            return None
        if event["kind"] == "decision":
            command = payload.get("command")
            reply = ""
            if str(command).startswith(("deposit ", "withdraw ", "borrow ")):
                receipt = None
        elif event["kind"] == "response" and command == "withdraw 1 platinum":
            reply += _ANSI.sub("", str(payload.get("text") or ""))
            if len(reply) > 4096:
                return None
            balance = _BALANCE.search(reply)
            if balance and thanks.search(reply):
                banked = sum(int(amount) * weight for amount, weight in
                             zip(balance.groups(), (1000, 100, 10, 1)))
                receipt = {
                    "segment_id": int(visit["id"]), "run_id": int(visit["run_id"]),
                    "balance_event_id": int(event["id"]), "bank_copper": banked,
                    "working_reserve_copper": WORKING_RESERVE_COPPER,
                }
    return receipt if receipt and receipt["bank_copper"] >= WORKING_RESERVE_COPPER else None
