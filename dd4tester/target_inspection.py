"""Bounded, instance-specific source identity checks using DD4's look output."""

import re
from dataclasses import dataclass, field
from typing import Mapping


INSPECTION_REVALIDATION_KEY = "campaign_target_inspection_revalidation"


def inspection_revalidation_pending(state: Mapping, candidate, policy_id: str) -> bool:
    record = state.get(INSPECTION_REVALIDATION_KEY)
    return bool(
        isinstance(record, Mapping) and record.get("status") == "pending"
        and record.get("policy_id") == policy_id
        and record.get("mobile_vnum") == candidate.mobile_vnum
        and record.get("room_vnum") == candidate.room_vnum
        and tuple(record.get("route") or ()) == candidate.route
        and all(record.get(key) == state.get(key) and state.get(key) is not None
                for key in ("level", "world_boot_id", "campaign_source_revision", "xp", "campaign_xp_loss_total"))
        and (state.get("campaign_research_results") or {}).get(policy_id) == record.get("prior_result")
    )


def normalized_description(text: str) -> str:
    return " ".join(text.split()).casefold()


def distinguishable_descriptions(descriptions: Mapping[int, str], expected: int) -> bool:
    expected_text = normalized_description(descriptions.get(expected, ""))
    return bool(
        expected_text and len(descriptions) > 1
        and all(normalized_description(text) for text in descriptions.values())
        and sum(normalized_description(text) == expected_text
                for text in descriptions.values()) == 1
    )


@dataclass
class TargetInspectionController:
    """Keep one finite look receipt tied to the current instance and visit."""

    pending: dict | None = None
    receipt: dict | None = None
    records: list[dict] = field(default_factory=list)
    attempted: set[tuple[str, str, int]] = field(default_factory=set)
    rejected_instances: dict[tuple[str, int, int, str | None], tuple[int, str]] = field(default_factory=dict)
    buffer: str = ""

    def is_rejected(self, *, selector: str, expected: int, level: int,
                    boot: str | None) -> bool:
        return (selector, expected, level, boot) in self.rejected_instances

    def record_known_mismatch(self, *, room: str, selector: str, expected: int,
                              level: int, boot: str | None, visit: int) -> bool:
        """Record a new room sighting of the same runtime ID already disproved."""
        key = (selector, expected, level, boot)
        known = self.rejected_instances.get(key)
        if known is None:
            return False
        if any(
            record.get("room") == room
            and record.get("selector") == selector
            and record.get("expected") == expected
            and record.get("level") == level
            and record.get("boot") == boot
            for record in self.records
        ):
            return True
        actual, source_description = known
        self.records.append({
            "room": room, "selector": selector, "expected": expected,
            "level": level, "boot": boot, "visit": visit,
            "status": "different_prototype", "actual": actual,
            "reason": "same runtime instance was already source-identified",
            "source_description": source_description,
        })
        return True

    def different_prototype_rooms(self, *, expected: int, level: int | None,
                                  boot: str | None) -> set[str]:
        return {
            str(record["room"])
            for record in self.records
            if record.get("status") == "different_prototype"
            and record.get("expected") == expected
            and record.get("level") == level
            and record.get("boot") == boot
            and record.get("room")
        }

    def begin(self, *, room: str, selector: str, expected: int,
              descriptions: Mapping[int, str], name: str, level: int,
              boot: str | None, visit: int, now: float) -> bool:
        key = (room, selector, visit)
        if (
            self.pending is not None or len(self.attempted) >= 8 or key in self.attempted
            or self.is_rejected(
                selector=selector, expected=expected, level=level, boot=boot,
            )
            or not re.fullmatch(r"#[0-9]+", selector)
            or not distinguishable_descriptions(descriptions, expected)
        ):
            return False
        self.attempted.add(key)
        self.buffer = ""
        self.receipt = None
        self.pending = {
            "room": room, "selector": selector, "expected": expected,
            "descriptions": dict(descriptions), "name": name, "level": level,
            "boot": boot, "visit": visit, "started": now, "deadline": now + 5,
        }
        return True

    def observe(self, text: str, *, now: float) -> None:
        plan = self.pending
        if plan is None:
            return
        if now >= plan["deadline"]:
            self.finish("failed", now=now, reason="target look exceeded five seconds")
            return
        self.buffer = (self.buffer + text)[-8192:]
        if re.search(
            r"(?im)^[ \t]*You do not see that here\.[ \t]*(?:\n|$)",
            self.buffer,
        ):
            self.finish("absent", now=now, reason="target instance is no longer in the room")
            return
        health = re.search(
            re.escape(plan["name"]) + r"\s+(?:is in perfect health|is slightly scratched|"
            r"has a few bruises|has some cuts|has several wounds|has many nasty wounds|"
            r"is bleeding freely|is covered in blood|is leaking guts|is almost dead|"
            r"is DYING)\.\s*(?:\n|$)", self.buffer, re.IGNORECASE,
        )
        if health is None:
            return
        before = normalized_description(self.buffer[:health.start()])
        matched = [vnum for vnum, description in plan["descriptions"].items()
                   if before.endswith(normalized_description(description))]
        if len(matched) != 1:
            self.finish("failed", now=now, reason="look description did not identify one source mobile")
        else:
            self.finish("verified" if matched[0] == plan["expected"] else "different_prototype",
                        now=now, actual=matched[0])

    def finish(self, status: str, *, now: float, reason: str | None = None,
               actual: int | None = None) -> None:
        if self.pending is None:
            return
        plan = self.pending
        self.receipt = {
            key: plan[key] for key in ("room", "selector", "expected", "level", "boot", "visit")
        }
        self.receipt.update(status=status, actual=actual, reason=reason, observed=now,
                            descriptions=plan["descriptions"])
        self.records.append({key: value for key, value in self.receipt.items()
                             if key not in {"observed", "descriptions"}})
        self.records[-1]["source_description"] = plan["descriptions"].get(actual, "")
        if status == "different_prototype" and actual is not None:
            self.rejected_instances[(
                plan["selector"], plan["expected"], plan["level"], plan["boot"],
            )] = (actual, plan["descriptions"].get(actual, ""))
        self.pending = None
        self.buffer = ""

    def poll(self, *, now: float, room: str, level: int | None, boot: str | None,
             in_combat: bool) -> bool:
        if self.pending is None:
            return False
        plan = self.pending
        if (in_combat or (room, level, boot) != (plan["room"], plan["level"], plan["boot"])):
            self.finish("failed", now=now, reason="target look context changed")
        elif now >= plan["deadline"]:
            self.finish("failed", now=now, reason="target look exceeded five seconds")
        return self.pending is not None

    def verified(self, *, room: str, selector: str | None, expected: int,
                 descriptions: Mapping[int, str], level: int | None,
                 boot: str | None, visit: int, now: float) -> bool:
        record = self.receipt
        return bool(
            record and record["status"] == "verified" and 0 <= now - record["observed"] <= 20
            and (room, selector, expected, level, boot, visit)
            == tuple(record[key] for key in ("room", "selector", "expected", "level", "boot", "visit"))
            and record["descriptions"] == dict(descriptions)
        )

    def absent(self, *, room: str, selector: str | None, expected: int,
               descriptions: Mapping[int, str], level: int | None,
               boot: str | None, visit: int, now: float) -> bool:
        """Confirm an explicit stale-instance reply in its original context."""
        record = self.receipt
        return bool(
            record and record["status"] == "absent" and 0 <= now - record["observed"] <= 20
            and (room, selector, expected, level, boot, visit)
            == tuple(record[key] for key in ("room", "selector", "expected", "level", "boot", "visit"))
            and record["descriptions"] == dict(descriptions)
        )

    def invalidate(self) -> None:
        self.receipt = None
