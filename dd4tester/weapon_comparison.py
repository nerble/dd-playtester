"""One healer-side comparison to resolve a carried weapon's ambiguous name."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import re
from typing import Any, Mapping, Sequence

from .equipment import (
    GearCatalog, character_can_use_item, is_releasable_funding_item,
    item_category, normalize_item_name, weapon_combat_score,
    weapon_preference_for_character, is_piercing_weapon,
)
from .hunt_candidates import ITEM_WEAPON, ObjectSource
from .observations import _DD4_PROMPT
from .training_travel import _listed_inventory
from .weapon_inspection import weapon_record


COMPARISON_KEY = "campaign_carried_weapon_comparison"
RECOVERY_IDENTITY_REVISION = 2
RESPONSE_PARSER_REVISION = 2


def weapon_comparison_request(
    plan: Mapping[str, Any] | None, previous: Any, *, level: int, boot_id: str,
) -> dict[str, Any] | None:
    """Admit a new comparison or one fresh check after a verified reversal."""
    if plan is None or not boot_id:
        return None
    restoration = None
    recovery_repair = False
    prompt_repair = False
    if isinstance(previous, Mapping) and (
        previous.get("level") == level and previous.get("boot_id") == boot_id
    ):
        if any(previous.get(key) != value for key, value in plan.items()):
            return None
        prompt_repair = bool(
            "response_parser_revision" not in previous
            and previous.get("stage") == "failed" and previous.get("commands") == 3
            and previous.get("failure") == "weapon comparison timed out during compare"
        )
        if not prompt_repair and (
            previous.get("stage") != "verified" or previous.get("failure") is not None
            or previous.get("commands") != 5
        ):
            return None
        if "restoration_of" in previous and not prompt_repair:
            old = previous.get("restoration_of")
            if (
                "recovery_identity_revision" in previous
                or not isinstance(old, Mapping)
                or old.get("stage") != "verified" or old.get("commands") != 5
                or old.get("level") != level or old.get("boot_id") != boot_id
                or any(old.get(key) != value for key, value in plan.items())
            ):
                return None
            recovery_repair = True
        # An old instance cannot be identified across reconnects from its name.
        # Keep the earlier result, but require the complete fresh comparison.
        if prompt_repair and isinstance(previous.get("restoration_of"), Mapping):
            restoration = dict(previous["restoration_of"])
        elif not prompt_repair:
            restoration = {key: previous[key] for key in (
                *plan, "level", "boot_id", "stage", "commands",
            )}
    return {
        **plan, "level": level, "boot_id": boot_id, "stage": "dispatched",
        "recovery_identity_revision": RECOVERY_IDENTITY_REVISION,
        "response_parser_revision": RESPONSE_PARSER_REVISION,
        **({"restoration_of": restoration} if restoration is not None else {}),
        **({"recovery_identity_repair_of": dict(previous)} if recovery_repair else {}),
        **({"prompt_repair_of": dict(previous)} if prompt_repair else {}),
    }


def plan_weapon_comparison(
    catalog: GearCatalog, primary: ObjectSource,
    descriptions: Sequence[str], *, character_class: str,
    subclass: str | None, level: int,
) -> dict[str, Any] | None:
    """Plan a read-only comparison, never infer an ambiguous object's type."""
    counts = Counter(normalize_item_name(name) for name in descriptions)
    if not counts or any(not catalog.candidates(name) for name in counts):
        return None
    preference = weapon_preference_for_character(character_class, subclass=subclass)
    choices = []
    for name, count in counts.items():
        variants = catalog.candidates(name)
        weapons = [item for item in variants if item_category(item) == "wield"]
        if count != 1 or len(variants) < 2 or len(weapons) != 1:
            continue
        item = weapons[0]
        if (
            item.vnum == primary.vnum or item.effective_level > level
            or not is_releasable_funding_item(item)
            or not character_can_use_item(item, character_class=character_class, subclass=subclass)
            or (preference == "piercing" and not is_piercing_weapon(item))
            or weapon_combat_score(item) <= weapon_combat_score(primary)
        ):
            continue
        # get_obj_carry uses one keyword prefix and excludes worn objects.
        keyword = next((word for word in item.keywords.casefold().split() if (
            re.fullmatch(r"[a-z][a-z0-9-]*", word)
            and all(any(k.startswith(word) for k in v.keywords.casefold().split()) for v in variants)
            and all(
                not any(k.startswith(word) for k in v.keywords.casefold().split())
                for other in counts if other != name for v in catalog.candidates(other)
            )
        )), None)
        if keyword is not None:
            choices.append((weapon_combat_score(item), item.vnum, {
                "candidate_vnum": item.vnum, "candidate_name": item.short_description,
                "primary_vnum": primary.vnum, "primary_name": primary.short_description,
                "keyword": keyword,
            }))
    return max(choices, default=(None, None, None), key=lambda value: value[:2])[2]


@dataclass
class WeaponComparison:
    request: Mapping[str, Any]
    stage: str = "new"
    deadline: float = 0.0
    buffer: str = ""
    failure: str | None = None
    commands: int = 0

    @property
    def complete(self) -> bool:
        return self.stage in {"verified", "rejected", "failed"}

    def observe(self, text: str) -> None:
        if not self.complete:
            self.buffer = (self.buffer + text)[-8192:]

    def _send(self, command: str, stage: str, now: float) -> tuple[str, str]:
        self.stage, self.deadline, self.buffer = stage, now + 5.0, ""
        self.commands += 1
        return command, "verify the ambiguous carried weapon at the healer"

    def _fail(self, reason: str) -> None:
        self.stage, self.failure = "failed", reason

    def _reply_lines(self) -> set[str]:
        # Async healer output can leave a prompt directly before the command
        # reply. Split on complete prompts, not on arbitrary sentence text.
        return {
            normalize_item_name(line)
            for line in _DD4_PROMPT.sub("\n", self.buffer).splitlines()
            if line.rstrip().endswith(".")
        }

    def decide(
        self, *, now: float, equipment: Any, descriptions: Sequence[str],
        catalog: GearCatalog, character_class: str, subclass: str | None,
        level: int, at_healer: bool, in_combat: bool,
    ) -> tuple[str, str] | None:
        if self.complete:
            return None
        if not at_healer or in_combat:
            self._fail("weapon comparison left its noncombat healer boundary")
            return None
        record = weapon_record(equipment)
        candidate = catalog.objects.get(self.request.get("candidate_vnum"))
        primary = catalog.objects.get(self.request.get("primary_vnum"))
        if candidate is None or primary is None:
            self._fail("weapon comparison lacks exact source or equipment identity")
            return None
        if self.stage == "new":
            return self._send("eq all", "equipment", now)
        if record is None:
            if now >= self.deadline:
                self._fail("weapon comparison lacks a fresh equipped reference")
            return None
        if self.stage in {"equipment", "inventory", "compare"} and (
            record.get("vnum") != primary.vnum or record.get("item_type") != ITEM_WEAPON
            or normalize_item_name(str(record.get("name", "")))
            != normalize_item_name(primary.short_description)
        ):
            self._fail("the comparison's equipped reference changed")
            return None
        if self.stage == "equipment":
            slot = re.search(r"(?im)^\s*\[weapon\]\s+([^\r\n]+)", self.buffer)
            if slot is not None and _DD4_PROMPT.search(self.buffer[slot.end():]):
                if (
                    not isinstance(equipment, list)
                    or any(not isinstance(item, Mapping) for item in equipment)
                    or sum(item.get("item_type") == ITEM_WEAPON for item in equipment) != 1
                    or normalize_item_name(slot[1]) != normalize_item_name(primary.short_description)
                ):
                    self._fail("compare requires one confirmed equipped weapon")
                    return None
                return self._send("inventory", "inventory", now)
        if self.stage == "inventory" and _DD4_PROMPT.search(
            self.buffer.partition("Your backpack contains:")[2]
        ):
            names = Counter(normalize_item_name(name) for name in descriptions)
            plan = plan_weapon_comparison(
                catalog, primary, descriptions, character_class=character_class,
                subclass=subclass, level=level,
            )
            if _listed_inventory(self.buffer) != names or plan is None or any(
                plan.get(key) != self.request.get(key) for key in plan
            ):
                self._fail("fresh inventory does not prove the planned comparison selector")
                return None
            return self._send(f"compare {plan['keyword']}", "compare", now)
        if self.stage == "compare":
            lines = self._reply_lines()
            better = normalize_item_name(
                f"{candidate.short_description} looks better than {primary.short_description}."
            )
            rejected = {
                normalize_item_name(f"{candidate.short_description} looks worse than {primary.short_description}."),
                normalize_item_name(f"{candidate.short_description} and {primary.short_description} look about the same."),
                normalize_item_name(f"You can't compare {candidate.short_description} and {primary.short_description}."),
                normalize_item_name("You aren't wearing anything comparable."),
                normalize_item_name("You do not have that item."),
            }
            if lines & rejected:
                self.stage = "rejected"
                return None
            if better in lines:
                return self._send(f"wield {self.request['keyword']}", "wield", now)
        if self.stage == "wield":
            expected = normalize_item_name(f"You wield {candidate.short_description}.")
            if expected in self._reply_lines():
                return self._send("eq all", "verify", now)
        if self.stage == "verify":
            slot = re.search(r"(?im)^\s*\[weapon\]\s+([^\r\n]+)", self.buffer)
            if slot is not None and _DD4_PROMPT.search(self.buffer[slot.end():]):
                if (
                    normalize_item_name(slot[1]) == normalize_item_name(candidate.short_description)
                    and record.get("vnum") == candidate.vnum
                    and record.get("item_type") == ITEM_WEAPON
                    and normalize_item_name(str(record.get("name", "")))
                    == normalize_item_name(candidate.short_description)
                ):
                    self.stage = "verified"
                else:
                    self._fail("the wielded object did not match the compared source weapon")
                return None
        if now >= self.deadline:
            self._fail(f"weapon comparison timed out during {self.stage}")
        return None

    def audit(self) -> dict[str, Any]:
        return {**self.request, "stage": self.stage, "failure": self.failure,
                "commands": self.commands}
