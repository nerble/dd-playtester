"""Static planning and proof-gap audits for the autonomous HERO goal."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .archetypes import archetype_registry
from .dd4_catalog import load_character_catalog
from .progression import ProgressionPolicy, policy_for
from .training import training_analysis_for, training_priorities_for


@dataclass(frozen=True)
class PolicyBand:
    """One contiguous portion of the static progression graph."""

    minimum_level: int
    maximum_level: int
    policy_id: str
    status: str
    execution: str | None

    @property
    def registered(self) -> bool:
        return self.execution is not None and self.status in {
            "verified",
            "research",
        }

    def to_mapping(self) -> dict[str, Any]:
        return {
            "minimum_level": self.minimum_level,
            "maximum_level": self.maximum_level,
            "policy_id": self.policy_id,
            "status": self.status,
            "execution": self.execution,
            "registered": self.registered,
        }


@dataclass(frozen=True)
class AutonomyAudit:
    """Source legality and declared template coverage, without live proof."""

    race: str
    sex: str
    character_class: str
    subclass: str | None
    target_level: int
    source: str
    source_revision: str | None
    identity_legal: bool
    training_priority_count: int
    automated_combat_skills: tuple[str, ...]
    automation_gaps: tuple[str, ...]
    combat_automation_status: str
    policy_bands: tuple[PolicyBand, ...]
    registered_through_target: bool
    templates_marked_verified_through_target: bool
    first_proof_gap_level: int | None
    first_proof_gap_policy: str | None
    blockers: tuple[str, ...]
    next_action: str

    @property
    def request_mapping(self) -> dict[str, Any]:
        return {
            "race": self.race,
            "sex": self.sex,
            "class": self.character_class,
            "subclass": self.subclass,
            "target_level": self.target_level,
        }

    def to_mapping(self) -> dict[str, Any]:
        return {
            "audit_scope": "static_templates",
            "live_progression_assessed": False,
            "request": self.request_mapping,
            "source": self.source,
            "source_revision": self.source_revision,
            "identity_legal": self.identity_legal,
            "training": {
                "priority_count": self.training_priority_count,
                "automated_combat_skills": list(self.automated_combat_skills),
                "combat_automation_status": self.combat_automation_status,
                "automation_gaps": list(self.automation_gaps),
            },
            "policy_bands": [band.to_mapping() for band in self.policy_bands],
            "registered_through_target": self.registered_through_target,
            "templates_marked_verified_through_target": (
                self.templates_marked_verified_through_target
            ),
            "first_unverified_template_level": self.first_proof_gap_level,
            "first_unverified_template_policy": self.first_proof_gap_policy,
            "blockers": list(self.blockers),
            "next_action": self.next_action,
        }


def audit_hero_request(
    *,
    race: str,
    sex: str,
    character_class: str,
    subclass: str | None = None,
    target_level: int = 100,
    source: str | Path | None = None,
) -> AutonomyAudit:
    """Audit a declarative HERO request without opening a live connection.

    Registered handlers and declared policy status do not establish runtime
    capability or per-character proof. This audit does not read live evidence.
    """
    if not 2 <= target_level <= 100:
        raise ValueError("target level must be between 2 and 100")

    catalog = load_character_catalog(source)
    canonical_race = catalog.race_name(race)
    canonical_sex = catalog.sex_name(sex)
    canonical_class = catalog.class_name(character_class)
    canonical_subclass: str | None = None
    if subclass:
        option = catalog.subclass_option(subclass)
        if option.base_class != canonical_class:
            raise ValueError(
                f"subclass {option.name!r} requires base class "
                f"{option.base_class!r}"
            )
        canonical_subclass = option.name

    registry = archetype_registry()
    profile = registry.class_profile(canonical_class)
    priorities = training_priorities_for(
        canonical_class,
        subclass=canonical_subclass,
    )
    automated_combat_skills = tuple(
        dict.fromkeys(
            priority.skill
            for priority in priorities
            if priority.automated and priority.utility in {"damage", "control"}
        )
    )
    automation_gaps = _automation_gaps_for(
        canonical_class,
        canonical_subclass,
    )
    combat_automation_status = (
        "missing"
        if not automated_combat_skills
        else "partial"
        if automation_gaps
        else "covered"
    )

    selections = [
        (
            level,
            _static_policy_for_level(
                level,
                canonical_class,
                canonical_subclass,
            ),
        )
        for level in range(0, target_level + 1)
    ]
    bands = _collapse_policy_bands(selections)
    first_gap = next(
        (
            band
            for band in bands
            if band.minimum_level <= target_level
            and band.status != "verified"
        ),
        None,
    )
    registered_through_target = all(
        policy.executable for _level, policy in selections if _level >= 2
    )
    templates_marked_verified_through_target = all(
        policy.status == "verified"
        for _level, policy in selections
        if _level >= 2
    )

    blockers: list[str] = []
    if first_gap is not None:
        if first_gap.status == "research":
            blockers.append(
                f"level {first_gap.minimum_level} begins research policy "
                f"{first_gap.policy_id}; live route, combat, and XP proof "
                "are incomplete"
            )
        else:
            blockers.append(
                f"level {first_gap.minimum_level} has no executable policy "
                f"({first_gap.policy_id})"
            )
    if canonical_subclass is not None and target_level >= 30:
        blockers.append(
            f"level 30 requires a fresh live {canonical_subclass} teacher "
            "handoff before subclass-specific progression can be proven"
        )
    if not automated_combat_skills:
        blockers.append(
            f"{canonical_class} has no automated damage or control training "
            "priority"
        )
    blockers.append(
        "static policy coverage is not a substitute for a fresh autonomous "
        "creation-to-target live run"
    )

    if first_gap is None and registered_through_target:
        next_action = (
            "Run a fresh bounded live campaign and promote each segment only "
            "after its route, combat, XP, and healer-return evidence passes."
        )
    elif first_gap is not None and first_gap.status == "research":
        next_action = (
            "Inspect the character's latest checkpoint and live outcomes, then "
            "remove the next executable blocker at that character's level. "
            f"The template gap at level {first_gap.minimum_level} does not "
            "reset an existing character's frontier."
        )
    else:
        next_action = (
            f"Implement an executable {canonical_class} policy at the first "
            "uncovered level before attempting a HERO run."
        )

    return AutonomyAudit(
        race=canonical_race,
        sex=canonical_sex,
        character_class=profile.name,
        subclass=canonical_subclass,
        target_level=target_level,
        source=catalog.source,
        source_revision=catalog.source_revision,
        identity_legal=True,
        training_priority_count=len(priorities),
        automated_combat_skills=automated_combat_skills,
        automation_gaps=automation_gaps,
        combat_automation_status=combat_automation_status,
        policy_bands=bands,
        registered_through_target=registered_through_target,
        templates_marked_verified_through_target=templates_marked_verified_through_target,
        first_proof_gap_level=(
            first_gap.minimum_level if first_gap is not None else None
        ),
        first_proof_gap_policy=(
            first_gap.policy_id if first_gap is not None else None
        ),
        blockers=tuple(blockers),
        next_action=next_action,
    )


def audit_all_base_classes(
    *,
    race: str,
    sex: str,
    target_level: int = 100,
    source: str | Path | None = None,
) -> tuple[AutonomyAudit, ...]:
    """Audit every source-legal base class for one cosmetic identity."""
    catalog = load_character_catalog(source)
    return tuple(
        audit_hero_request(
            race=race,
            sex=sex,
            character_class=option.name,
            target_level=target_level,
            source=source,
        )
        for option in catalog.classes
    )


def render_autonomy_audit(audit: AutonomyAudit) -> str:
    """Render the audit for an operator while preserving its key decisions."""
    subclass = f" -> {audit.subclass}" if audit.subclass else ""
    target = "HERO (100)" if audit.target_level == 100 else str(audit.target_level)
    lines = [
        f"Request: {audit.race}/{audit.sex} {audit.character_class}{subclass}",
        f"Target level: {target}",
        f"Identity: {'source-legal' if audit.identity_legal else 'invalid'}",
        "Template coverage: "
        + (
            "registered through target (runtime capability unassessed)"
            if audit.registered_through_target
            else "incomplete before target"
        ),
        "Templates marked verified: "
        + ("all" if audit.templates_marked_verified_through_target else "not all"),
        "Live progression proof: not assessed by this static audit",
        f"Training priorities: {audit.training_priority_count}",
        "Automated combat skills: "
        + (", ".join(audit.automated_combat_skills) or "none"),
        f"Combat automation: {audit.combat_automation_status}",
        "Automation gaps:",
    ]
    lines.extend(f"- {gap}" for gap in audit.automation_gaps)
    if not audit.automation_gaps:
        lines.append("- none declared")
    lines.append("Policy bands:")
    lines.extend(
        f"- {band.minimum_level}-{band.maximum_level}: {band.policy_id} "
        f"[{band.status}; {band.execution or 'blocked'}]"
        for band in audit.policy_bands
    )
    if audit.first_proof_gap_level is None:
        lines.append("First unverified template: none in the static graph")
    else:
        lines.append(
            f"First unverified template: level {audit.first_proof_gap_level} "
            f"({audit.first_proof_gap_policy})"
        )
    lines.append("Blockers:")
    lines.extend(f"- {blocker}" for blocker in audit.blockers)
    lines.append(f"Next action: {audit.next_action}")
    return "\n".join(lines) + "\n"


def _automation_gaps_for(
    character_class: str,
    subclass: str | None,
) -> tuple[str, ...]:
    """Return declared runtime gaps without treating templates as proof."""
    analyses = [(character_class, training_analysis_for(character_class))]
    if subclass:
        analyses.insert(0, (subclass, training_analysis_for(subclass)))
    gaps: list[str] = []
    for label, analysis in analyses:
        if analysis is None:
            continue
        gaps.extend(f"{label}: {gap}" for gap in analysis.automation_gaps)
    return tuple(dict.fromkeys(gaps))


def _static_policy_for_level(
    level: int,
    character_class: str,
    subclass: str | None,
) -> ProgressionPolicy:
    if subclass and level > 30:
        return policy_for(
            level,
            character_class,
            subclass=subclass,
            target_subclass=subclass,
        )
    return policy_for(
        level,
        character_class,
        target_subclass=subclass,
    )


def _collapse_policy_bands(
    selections: list[tuple[int, ProgressionPolicy]],
) -> tuple[PolicyBand, ...]:
    if not selections:
        return ()
    start, current = selections[0]
    bands: list[PolicyBand] = []
    for level, policy in selections[1:]:
        if (
            policy.policy_id,
            policy.status,
            policy.execution,
        ) != (
            current.policy_id,
            current.status,
            current.execution,
        ):
            bands.append(
                PolicyBand(
                    minimum_level=start,
                    maximum_level=level - 1,
                    policy_id=current.policy_id,
                    status=current.status,
                    execution=current.execution,
                )
            )
            start, current = level, policy
    bands.append(
        PolicyBand(
            minimum_level=start,
            maximum_level=selections[-1][0],
            policy_id=current.policy_id,
            status=current.status,
            execution=current.execution,
        )
    )
    return tuple(bands)


def audit_json(audit: AutonomyAudit) -> str:
    """Return stable JSON for CI and later orchestration."""
    return json.dumps(audit.to_mapping(), indent=2, sort_keys=True) + "\n"
