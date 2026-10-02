from __future__ import annotations

import argparse
import asyncio
from collections import Counter
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from .autonomy import (
    audit_all_base_classes,
    audit_hero_request,
    audit_json,
    render_autonomy_audit,
)
from .campaign import (
    DEFAULT_LIVE_SEGMENT_RUNTIME_SECONDS,
    DEFAULT_RESET_WAIT_SECONDS,
    CampaignResult,
    _BELOW_BAND_POLICY_EXCLUSIONS_KEY,
    _FAME_RECOVERY_MAX_LEVEL_DELTA,
    _FAME_RECOVERY_MIN_LEVEL_DELTA,
    _PROTECTION_RECOVERY_KEY,
    _SOURCE_RANKED_RETRY_EXHAUSTED_BOOT_KEY,
    _SOURCE_RANKED_RETRY_EXHAUSTED_KEY,
    _SOURCE_RANKED_TIMEOUT_POLICIES_KEY,
    _SOURCE_RANKED_TIMEOUT_REVALIDATION_FIELD,
    _SOURCE_RANKED_TIMEOUT_REVALIDATION_MAX_ATTEMPTS,
    _source_ranked_candidate_requires_sanctuary_for_state,
    _source_ranked_caster_output_for_state,
    _source_ranked_candidate_excluded_by_below_band_evidence,
    _source_ranked_fame_level_window,
    _source_ranked_hp_probe_admission_available,
    _source_ranked_invisibility_route_candidate_allowed,
    _source_ranked_plain_aggressive_target_invisibility_allowed,
    _source_ranked_protected_aggressive_hp_fuzz_probe_allowed,
    _source_ranked_protected_hp_fuzz_probe_allowed,
    _source_ranked_protected_level_ceiling_hp_probe_allowed,
    _source_ranked_policy_id,
    _source_ranked_useful_fuzz_probability,
    _source_ranked_familiar_probe_allowed,
    _state_has_sanctuary_reserve,
    run_campaign_file,
)
from .character import load_character_spec
from .city_travel import revealed_gmcp_alignment
from .credentials import (
    DEFAULT_LOGIN_CREDENTIAL,
    configure_character_password,
    configure_login,
)
from .equipment import (
    GearCatalog,
    STANCE_COMBAT,
    STANCE_PRE_LEVEL,
    STANCE_RECOVERY,
    rank_gear_sources,
    weapon_preference_for_character,
)
from .evidence import collect_run_evidence, render_evidence_json
from .fastwalks import FASTWALKS, routes_for_level
from .dd4_catalog import _source_revision, load_character_catalog
from .hero import (
    DEFAULT_AUTONOMOUS_RESET_WAITS,
    HeroRequest,
    load_existing_hero_request,
    prepare_hero_request,
    run_hero_request,
    run_hero_until_target,
)
from .hunt_candidates import (
    load_world_source,
    rank_hunt_candidates,
    rank_resource_sources,
    source_mobile_search_rooms,
)
from .matrix import (
    live_matrix_coverage,
    matrix_coverage,
    prepare_validation_matrix,
    provision_matrix_passwords,
    run_matrix_file,
)
from .mudlet import MudletBridge
from .money import run_money_loop_profile
from .prerequisites import known_skills, load_snapshot, requirements_for_skill
from .progression import policy_for
from .quests import (
    fame_from_state,
    quest_fame_recovery_status,
    quest_points_required_for_advance,
    quest_points_shortfall_for_advance,
    quest_request_blocker,
    quest_request_fame_allowed,
    questmaster_name_for_level,
    questmaster_route_for_level,
    recall_origins_from_state,
    recall_point_for_index,
    snapshot_quest_status,
)
from .report import (
    build_campaign_report,
    build_run_report,
    render_campaign_markdown,
    render_json,
    render_markdown,
)
from .rotation import run_campaign_rotation
from .runner import run_scenario_file
from .starter import (
    _equipment_descriptions,
    _inventory_descriptions,
    run_ambush_research_profile,
    run_arena_research_profile,
    run_guildmaster_research_profile,
    run_fastwalk_research_profile,
    run_magic_shop_research_profile,
    run_midennir_research_profile,
    run_moria_research_profile,
    run_outfit_profile,
    run_rearm_profile,
    run_restock_profile,
    run_return_home_profile,
    run_resupply_profile,
    run_sell_loot_profile,
    run_shire_research_profile,
    run_starter_profile,
)
from .storage import RunStorage
from .training import (
    prerequisite_classes_for,
    subclass_training_priorities,
    training_analysis_for,
    training_priorities,
)


DEFAULT_DATABASE = Path("runs/dd4tester.sqlite3")
# A historical campaign-character join deserializes JSON from every matching
# checkpoint.  Keep inspection bounded for the shared database, which is
# intentionally append-only and can grow into tens of gigabytes.
_MAX_CAMPAIGN_CHARACTER_LOOKUP_BYTES = 2 * 1024 * 1024 * 1024


def _inspection_alignment(state: Mapping[str, Any]) -> int | None:
    """Read the authoritative GMCP alignment from a saved state snapshot."""
    progress = state.get("progress")
    if isinstance(progress, Mapping) and "alignment" in progress:
        value = progress.get("alignment")
        level = state.get("level")
        if level is None:
            level = progress.get("level")
    else:
        value = state.get("alignment")
        level = state.get("level")
    return revealed_gmcp_alignment(value, level=level)


def _inspection_fame(state: Mapping[str, Any]) -> int | None:
    """Read the current GMCP fame value without conflating it with alignment."""
    return fame_from_state(state)


def _latest_inspection_state(storage: RunStorage, character: str) -> dict[str, Any]:
    """Load a named character without scanning large run or checkpoint history."""
    try:
        database_size = storage.path.stat().st_size
    except OSError:
        database_size = 0
    if database_size > _MAX_CAMPAIGN_CHARACTER_LOOKUP_BYTES:
        # Inspect one indexed checkpoint per campaign instead of joining every
        # checkpoint's JSON name across the append-only history.
        checkpoint = storage.get_latest_campaign_checkpoint_for_character_bounded(
            character
        )
        if checkpoint is not None:
            try:
                checkpoint_state = json.loads(checkpoint["state_json"])
            except (TypeError, json.JSONDecodeError):
                checkpoint_state = {}
            if isinstance(checkpoint_state, dict):
                return checkpoint_state
        return dict(storage.get_latest_character_state(character) or {})
    campaign = storage.get_latest_campaign_for_character(character)
    if campaign is None:
        return dict(storage.get_latest_character_state(character) or {})
    campaign_id = int(campaign["id"])
    checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)
    if checkpoint is None:
        return {}
    try:
        checkpoint_state = json.loads(checkpoint["state_json"])
    except (TypeError, json.JSONDecodeError):
        checkpoint_state = {}
    if not isinstance(checkpoint_state, dict):
        checkpoint_state = {}
    run_ids: list[int] = []
    if checkpoint["run_id"] is not None:
        run_ids.append(int(checkpoint["run_id"]))
    for segment in reversed(
        storage.list_recent_campaign_segments(campaign_id, limit=8)
    ):
        if segment["run_id"] is None:
            continue
        run_id = int(segment["run_id"])
        if run_id not in run_ids:
            run_ids.append(run_id)
    for run_id in run_ids:
        snapshot = storage.get_latest_state_snapshot(run_id)
        if snapshot is None:
            continue
        try:
            live_state = json.loads(snapshot["state_json"])
        except (TypeError, json.JSONDecodeError):
            continue
        if not isinstance(live_state, dict):
            continue
        state = dict(live_state)
        for key, value in checkpoint_state.items():
            if key.startswith("campaign_") or key in {
                "character_class",
                "subclass",
                "recall_origins",
            } | _INSPECTION_CHECKPOINT_STATE_KEYS:
                state[key] = value
        return state
    return dict(checkpoint_state)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m dd4tester")
    subcommands = parser.add_subparsers(dest="command", required=True)

    run_parser = subcommands.add_parser("run", help="run a YAML play-test scenario")
    run_parser.add_argument("scenario", type=Path, help="path to the scenario YAML file")

    starter_parser = subcommands.add_parser(
        "starter",
        help="create or resume a rule-based starter character",
    )
    starter_parser.add_argument(
        "profile",
        type=Path,
        help="path to the starter character YAML profile",
    )

    arena_research_parser = subcommands.add_parser(
        "arena-research",
        help="run a bounded Mud School arena progression segment",
    )
    arena_research_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing level-2 character profile",
    )

    resupply_parser = subcommands.add_parser(
        "resupply",
        help="safely return a character from Limbo or the arena, eat, drink, save, and quit",
    )
    resupply_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing character YAML profile",
    )

    return_home_parser = subcommands.add_parser(
        "return-home",
        help="recover an interrupted character or corpse and return to the Midgaard Healer",
    )
    return_home_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing character YAML profile",
    )

    restock_parser = subcommands.add_parser(
        "restock",
        help="visit the Midgaard fountain and Bakery, then save and quit",
    )
    restock_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing character YAML profile",
    )
    rearm_parser = subcommands.add_parser(
        "rearm",
        help="buy, wield, verify, and persist a class-legal primary weapon",
    )
    rearm_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing character YAML profile",
    )
    outfit_parser = subcommands.add_parser(
        "outfit",
        help="fill empty legal equipment slots at the safe Midgaard leather shop",
    )
    outfit_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing character YAML profile",
    )
    sell_loot_parser = subcommands.add_parser(
        "sell-loot",
        help="sell carried weapons and armour through verified safe Midgaard shops",
    )
    sell_loot_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing character YAML profile",
    )
    money_loop_parser = subcommands.add_parser(
        "money-loop",
        help="hunt renewable Foundry drops, sell them safely, and restock food",
    )
    money_loop_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing character YAML profile",
    )
    money_loop_parser.add_argument(
        "--level",
        type=int,
        required=True,
        help="current character level used for source-backed risk filtering",
    )
    money_loop_parser.add_argument(
        "--trips",
        type=int,
        default=3,
        help="maximum bounded hunt trips before liquidation, default: 3",
    )
    money_loop_parser.add_argument(
        "--source",
        type=Path,
        default=Path("runs/dd4-source/server/area"),
        help="path to the DD4 server area directory",
    )
    guildmaster_parser = subcommands.add_parser(
        "guildmaster-research",
        help="read the teacher clue and inspect the trainer for the current level band",
    )
    guildmaster_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing character YAML profile",
    )
    magic_shop_parser = subcommands.add_parser(
        "magic-shop-research",
        help="visit the Midgaard Magic Shop and record stock without buying",
    )
    magic_shop_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing mage character YAML profile",
    )
    magic_shop_parser.add_argument(
        "--buy-fly",
        action="store_true",
        help="buy, use, and verify one light blue travel potion after listing stock",
    )
    fastwalk_parser = subcommands.add_parser(
        "fastwalk-research",
        help="verify an official recall-origin route without initiating combat",
    )
    fastwalk_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing character YAML profile",
    )
    fastwalk_parser.add_argument(
        "route",
        help="official route name, for example: moria",
    )
    fastwalk_parser.add_argument(
        "--exit",
        dest="explore_direction",
        choices=("north", "south", "east", "west", "up", "down"),
        help="inspect rooms through this endpoint exit, then return",
    )
    fastwalk_parser.add_argument(
        "--depth",
        type=int,
        default=1,
        help="maximum rooms to inspect through --exit, from 1 to 6, default: 1",
    )
    fastwalk_target_group = fastwalk_parser.add_mutually_exclusive_group()
    fastwalk_target_group.add_argument(
        "--attack",
        dest="attack_target",
        help="attack one explicit target after the one-room inspection",
    )
    fastwalk_target_group.add_argument(
        "--consider",
        dest="consider_target",
        help="live-consider one endpoint target without attacking it",
    )
    fastwalk_parser.add_argument(
        "--max-matching-targets",
        dest="maximum_target_count",
        type=int,
        default=1,
        help="maximum identical target mobiles permitted for --attack, default: 1",
    )
    fastwalk_parser.add_argument(
        "--allow-bystander",
        dest="allowed_bystanders",
        action="append",
        default=[],
        help="permit one source-verified noncombat mobile; may be repeated",
    )
    midennir_parser = subcommands.add_parser(
        "midennir-research",
        help="collect the source-backed large sack from the Ambush trail",
    )
    midennir_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing character YAML profile",
    )
    ambush_parser = subcommands.add_parser(
        "ambush-research",
        help="live-consider the exterior Ambush goblin circuit and return safely",
    )
    ambush_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing level-9 or higher mage character YAML profile",
    )
    ambush_probe_group = ambush_parser.add_mutually_exclusive_group()
    ambush_probe_group.add_argument(
        "--guard-probe",
        action="store_true",
        help="consider the level-10 fanatical guard under invisibility without attacking",
    )
    ambush_probe_group.add_argument(
        "--vile-probe",
        action="store_true",
        help="consider the unarmed level-9 vile goblin under invisibility without attacking",
    )
    ambush_probe_group.add_argument(
        "--raider-probe",
        action="store_true",
        help="consider the armed goblin raider under invisibility without attacking",
    )
    ambush_probe_group.add_argument(
        "--raider-hunt",
        action="store_true",
        help="live-consider and attack at most one isolated goblin raider",
    )
    ambush_probe_group.add_argument(
        "--horseman-probe",
        action="store_true",
        help="consider a Miden'nir dark horseman without attacking or entering a crowded room",
    )
    ambush_probe_group.add_argument(
        "--vile-hunt",
        action="store_true",
        help="live-consider and attack at most one unarmed vile goblin",
    )
    shire_parser = subcommands.add_parser(
        "shire-research",
        help="live-consider Shire Watermill workers without initiating combat",
    )
    shire_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing character YAML profile",
    )
    shire_parser.add_argument(
        "--hunt",
        action="store_true",
        help="live-consider and attack at most one Watermill worker",
    )
    moria_parser = subcommands.add_parser(
        "moria-research",
        help="verify the safe Midgaard-to-Moria approach and return to the Mage Guild",
    )
    moria_parser.add_argument(
        "profile",
        type=Path,
        help="path to an existing character YAML profile",
    )
    moria_parser.add_argument(
        "--depth",
        type=int,
        default=0,
        help="number of additional northbound Moria trail rooms to inspect, default: 0",
    )
    moria_mode = moria_parser.add_mutually_exclusive_group()
    moria_mode.add_argument(
        "--sanctuary-probe",
        action="store_true",
        help="consider the nearest potion-carrying large hobgoblin without attacking",
    )
    moria_mode.add_argument(
        "--sanctuary-hunt",
        action="store_true",
        help="hunt at most one isolated large hobgoblin for its sanctuary potion",
    )
    moria_mode.add_argument(
        "--sanctuary-deep-hunt",
        action="store_true",
        help=(
            "use the source-audited level-24+ Moria carrier route for one "
            "bounded sanctuary hunt"
        ),
    )

    fastwalks_parser = subcommands.add_parser(
        "show-fastwalks",
        help="list official recall-origin travel routes and their expanded commands",
    )
    fastwalks_parser.add_argument(
        "--level",
        type=int,
        help="only list routes whose suggested level band includes this level",
    )
    hunt_candidates_parser = subcommands.add_parser(
        "show-hunt-candidates",
        help="rank source-backed hunt and loot candidates",
    )
    hunt_candidates_parser.add_argument("--level", type=int, required=True)
    hunt_candidates_parser.add_argument(
        "--character",
        default="Ararisa",
        help="character name used for current-reboot kill history, default: Ararisa",
    )
    hunt_candidates_parser.add_argument(
        "--source",
        type=Path,
        default=Path("runs/dd4-source/server/area"),
        help="path to the DD4 server area directory",
    )
    hunt_candidates_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path, default: {DEFAULT_DATABASE}",
    )
    hunt_candidates_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="maximum candidates to show, default: 20",
    )
    hunt_candidates_parser.add_argument(
        "--include-xp-only",
        action="store_true",
        help="include targets without known saleable loot or coin drops",
    )
    hunt_candidates_parser.add_argument(
        "--all-areas",
        action="store_true",
        help="analyse every area file instead of the conservative starter-area set",
    )
    hunt_candidates_parser.add_argument(
        "--autonomous-safe-only",
        action="store_true",
        help="show only candidates eligible for a source-backed probe-to-hunt policy",
    )
    resource_sources_parser = subcommands.add_parser(
        "show-resource-sources",
        help="list source-backed healing, food, sanctuary, protection, and flight resources",
    )
    resource_sources_parser.add_argument("--level", type=int, required=True)
    resource_sources_parser.add_argument(
        "--effect",
        choices=(
            "all",
            "sanctuary",
            "protection",
            "healing",
            "recovery",
            "flight",
            "fly",
            "levitation",
            "travel",
            "food",
        ),
        default="all",
        help="resource effect to inspect, default: all",
    )
    resource_sources_parser.add_argument(
        "--character",
        default="Ararisa",
        help="character name used for current state and recall origins, default: Ararisa",
    )
    resource_sources_parser.add_argument(
        "--source",
        type=Path,
        default=Path("runs/dd4-source/server/area"),
        help="path to the DD4 server area directory",
    )
    resource_sources_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path, default: {DEFAULT_DATABASE}",
    )
    resource_sources_parser.add_argument(
        "--limit",
        type=int,
        default=40,
        help="maximum placements to show, default: 40",
    )
    resource_sources_parser.add_argument(
        "--all-areas",
        action="store_true",
        help="analyse every area file instead of the conservative starter-area set",
    )
    gear_sources_parser = subcommands.add_parser(
        "show-gear-sources",
        help="rank source-backed equipment placements for a class and stance",
    )
    gear_sources_parser.add_argument("--level", type=int, required=True)
    gear_sources_parser.add_argument(
        "--class",
        dest="character_class",
        required=True,
        help="base class used for source equipment restrictions",
    )
    gear_sources_parser.add_argument(
        "--subclass",
        help="optional subclass used for source equipment restrictions",
    )
    gear_sources_parser.add_argument(
        "--stance",
        choices=(STANCE_COMBAT, STANCE_PRE_LEVEL, STANCE_RECOVERY),
        default=STANCE_COMBAT,
        help="loadout priority to rank, default: combat",
    )
    gear_sources_parser.add_argument(
        "--character",
        default="Ararisa",
        help="character name used for current state and recall origins, default: Ararisa",
    )
    gear_sources_parser.add_argument(
        "--source",
        type=Path,
        default=Path("runs/dd4-source/server/area"),
        help="path to the DD4 server area directory",
    )
    gear_sources_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path, default: {DEFAULT_DATABASE}",
    )
    gear_sources_parser.add_argument(
        "--limit",
        type=int,
        default=40,
        help="maximum placements to show, default: 40",
    )
    gear_sources_parser.add_argument(
        "--all-areas",
        action="store_true",
        help="analyse every area file instead of the conservative starter-area set",
    )
    combat_readiness_parser = subcommands.add_parser(
        "show-combat-readiness",
        help="show source-backed combat output and current target blockers",
    )
    combat_readiness_parser.add_argument("--level", type=int, required=True)
    combat_readiness_parser.add_argument(
        "--class",
        dest="character_class",
        required=True,
        help="base class used for source combat capabilities",
    )
    combat_readiness_parser.add_argument(
        "--subclass",
        help="optional subclass used for source combat capabilities",
    )
    combat_readiness_parser.add_argument(
        "--character",
        default="Ararisa",
        help="character name used for saved state and current-reboot history, default: Ararisa",
    )
    combat_readiness_parser.add_argument(
        "--source",
        type=Path,
        default=Path("runs/dd4-source/server/area"),
        help="path to the DD4 server area directory",
    )
    combat_readiness_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path, default: {DEFAULT_DATABASE}",
    )
    combat_readiness_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="maximum targets and gear upgrades to show, default: 10",
    )
    combat_readiness_parser.add_argument(
        "--all-areas",
        action="store_true",
        help="analyse every area file instead of the conservative starter-area set",
    )
    combat_readiness_parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable readiness JSON",
    )
    arena_research_parser.add_argument(
        "--target-level",
        type=int,
        default=3,
        help="bounded completion level from 3 to 10, default: 3",
    )
    arena_research_parser.add_argument(
        "--kill-limit",
        type=int,
        help="save and exit after this many confirmed arena kills",
    )

    configure_login_parser = subcommands.add_parser(
        "configure-login",
        help="store DD4 login credentials in the operating system credential manager",
    )
    configure_login_parser.add_argument(
        "--credential-name",
        default=DEFAULT_LOGIN_CREDENTIAL,
        help=f"stored login name, default: {DEFAULT_LOGIN_CREDENTIAL}",
    )

    configure_character_parser = subcommands.add_parser(
        "configure-character-password",
        help="store a character password in the operating system credential manager",
    )
    configure_character_parser.add_argument("profile", type=Path)
    configure_character_parser.add_argument(
        "--credential-name",
        help="override the credential name from the character profile",
    )

    campaign_parser = subcommands.add_parser(
        "campaign",
        help="run or resume a checkpointed character campaign",
    )
    campaign_parser.add_argument(
        "config",
        type=Path,
        help="path to the campaign YAML configuration",
    )
    campaign_parser.add_argument(
        "--new",
        action="store_true",
        help="start a new campaign instead of resuming this configuration",
    )
    campaign_parser.add_argument(
        "--segments",
        type=int,
        default=1,
        help="run up to this many ready checkpoint segments, default: 1",
    )
    campaign_parser.add_argument(
        "--reset-retries",
        type=int,
        help=(
            "bounded retries after empty-area checkpoints; defaults to "
            "--segments, or 0 when --max-segment-runtime is set"
        ),
    )
    campaign_parser.add_argument(
        "--reset-wait",
        type=float,
        default=DEFAULT_RESET_WAIT_SECONDS,
        help=(
            "seconds to wait outside a depleted area before each retry, "
            f"default: {DEFAULT_RESET_WAIT_SECONDS:g}; longer waits are opt-in"
        ),
    )
    campaign_parser.add_argument(
        "--max-segment-runtime",
        type=float,
        default=DEFAULT_LIVE_SEGMENT_RUNTIME_SECONDS,
        help=(
            "cap each live segment in seconds; default: "
            f"{DEFAULT_LIVE_SEGMENT_RUNTIME_SECONDS:g}"
        ),
    )
    campaign_parser.add_argument(
        "--retry-stalled",
        action="store_true",
        help="retry a watchdog-stalled segment instead of honoring its stall budget",
    )
    campaign_parser.add_argument(
        "--progress",
        action="store_true",
        help="print bounded attempt start and completion progress to stderr",
    )

    hero_parser = subcommands.add_parser(
        "hero",
        help="create or resume an autonomous character campaign to level 100",
    )
    hero_parser.add_argument(
        "--race",
        help=(
            "DD4 race name; inferred from a named hero workspace or saved "
            "campaign"
        ),
    )
    hero_parser.add_argument(
        "--sex",
        default=None,
        help=(
            "cosmetic DD4 sex: male, female, or neuter; inferred for an "
            "existing named hero or campaign and otherwise defaults to neuter"
        ),
    )
    hero_parser.add_argument(
        "--class",
        dest="character_class",
        help=(
            "DD4 base class name; inferred from a named hero workspace or "
            "saved campaign"
        ),
    )
    hero_parser.add_argument(
        "--subclass",
        help="optional level-30 subclass goal",
    )
    hero_parser.add_argument(
        "--name",
        help="3-12 letter character name; a stable name is generated when omitted",
    )
    hero_parser.add_argument(
        "--username",
        help="alias for --name when resuming an existing DD4 character",
    )
    hero_parser.add_argument(
        "--password",
        help=(
            "plaintext DD4 character password for this process only unless "
            "--remember-password is supplied; it is never written to generated "
            "files or transcripts"
        ),
    )
    hero_parser.add_argument(
        "--remember-password",
        action="store_true",
        help=(
            "store --password in Windows Credential Manager for later "
            "checkpoint resumption"
        ),
    )
    hero_parser.add_argument(
        "--target-level",
        type=int,
        default=100,
        help="stop after reaching this level (2-100), default: 100",
    )
    hero_parser.add_argument(
        "--personality",
        help="short in-world personality used in the initial description",
    )
    hero_parser.add_argument(
        "--transport",
        choices=("telnet", "mudlet"),
        default=None,
        help="execution transport; inherited for an existing hero, otherwise telnet",
    )
    hero_parser.add_argument(
        "--mudlet-directory",
        type=Path,
        help="shared bridge directory required with --transport mudlet",
    )
    hero_parser.add_argument(
        "--source",
        type=Path,
        help="DD4 const.c or source directory; defaults to the local source checkout",
    )
    hero_parser.add_argument(
        "--workspace",
        type=Path,
        default=Path("runs/heroes"),
        help="durable generated hero request directory, default: runs/heroes",
    )
    hero_parser.add_argument(
        "--new",
        action="store_true",
        help="start a new stored campaign for the prepared character",
    )
    hero_parser.add_argument(
        "--segments",
        type=int,
        default=10000,
        help=(
            "maximum checkpoint segments, or autonomous cycles, in this "
            "process; default: 10000"
        ),
    )
    hero_parser.add_argument(
        "--autonomous",
        action="store_true",
        help=(
            "continue bounded workers until the target or a durable blocker; "
            "reset waits use a separate finite budget"
        ),
    )
    hero_parser.add_argument(
        "--reset-retries",
        type=int,
        help=(
            "bounded retries after empty-area checkpoints; defaults to "
            "--segments without a runtime cap, or 0 for a bounded worker; "
            "--autonomous defaults to one per cycle"
        ),
    )
    hero_parser.add_argument(
        "--reset-wait",
        type=float,
        default=DEFAULT_RESET_WAIT_SECONDS,
        help=(
            "seconds to wait outside a depleted area before each retry, "
            f"default: {DEFAULT_RESET_WAIT_SECONDS:g}; longer waits are opt-in"
        ),
    )
    hero_parser.add_argument(
        "--max-reset-waits",
        type=int,
        default=DEFAULT_AUTONOMOUS_RESET_WAITS,
        help=(
            "total area-reset waits allowed by --autonomous, default: "
            f"{DEFAULT_AUTONOMOUS_RESET_WAITS}"
        ),
    )
    hero_parser.add_argument(
        "--max-segment-runtime",
        type=float,
        default=DEFAULT_LIVE_SEGMENT_RUNTIME_SECONDS,
        help=(
            "cap each live segment in seconds; default: "
            f"{DEFAULT_LIVE_SEGMENT_RUNTIME_SECONDS:g}; use an explicit "
            "larger value only for a bounded probe"
        ),
    )
    hero_parser.add_argument(
        "--retry-stalled",
        action="store_true",
        help=(
            "perform one bounded frontier rotation when trailing no-progress "
            "history blocks the normal retry"
        ),
    )
    hero_parser.add_argument(
        "--progress",
        action="store_true",
        help="print bounded attempt start and completion progress to stderr",
    )
    hero_parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="validate and write durable configuration without connecting",
    )

    rotation_parser = subcommands.add_parser(
        "hero-rotation",
        help="run one bounded campaign segment for each configured character",
    )
    rotation_parser.add_argument(
        "--config",
        type=Path,
        default=Path("matrices/active-hero-rotation.yaml"),
        help=(
            "rotation YAML; relative campaign paths resolve from that file, "
            "default: matrices/active-hero-rotation.yaml"
        ),
    )
    rotation_parser.add_argument(
        "--rounds",
        type=int,
        default=1,
        help="maximum passes through the roster, default: 1 (max: 1000)",
    )
    rotation_parser.add_argument(
        "--max-segment-runtime",
        type=float,
        default=DEFAULT_LIVE_SEGMENT_RUNTIME_SECONDS,
        help=(
            "live time cap per character segment in seconds; default: "
            f"{DEFAULT_LIVE_SEGMENT_RUNTIME_SECONDS:g}"
        ),
    )
    rotation_parser.add_argument(
        "--progress",
        action="store_true",
        help="print bounded progress while the roster is being processed",
    )

    subcommands.add_parser(
        "hero-options",
        help="list source-derived DD4 races, classes, and subclasses",
    ).add_argument(
        "--source",
        type=Path,
        help="DD4 const.c or source directory; defaults to the local source checkout",
    )

    autonomy_parser = subcommands.add_parser(
        "autonomy-audit",
        help="audit a race/class request against the executable policy graph",
    )
    autonomy_parser.add_argument("--race", required=True)
    autonomy_parser.add_argument(
        "--sex",
        required=True,
        help="cosmetic DD4 creation sex: male, female, or neuter",
    )
    autonomy_class = autonomy_parser.add_mutually_exclusive_group(required=True)
    autonomy_class.add_argument("--class", dest="character_class")
    autonomy_class.add_argument(
        "--all-classes",
        action="store_true",
        help="audit every source-legal base class for this identity",
    )
    autonomy_parser.add_argument("--subclass")
    autonomy_parser.add_argument("--target-level", type=int, default=100)
    autonomy_parser.add_argument(
        "--source",
        type=Path,
        help="DD4 const.c or source directory; defaults to the bundled catalog",
    )
    autonomy_parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable audit JSON",
    )

    matrix_parser = subcommands.add_parser(
        "matrix",
        help="run or resume a representative character campaign matrix",
    )
    matrix_parser.add_argument(
        "config",
        type=Path,
        help="path to the matrix YAML configuration",
    )
    matrix_parser.add_argument(
        "--new",
        action="store_true",
        help="start new campaigns during the first matrix round",
    )
    matrix_parser.add_argument(
        "--rounds",
        type=int,
        default=1,
        help="maximum round-robin passes, default: 1",
    )
    matrix_parser.add_argument(
        "--segments-per-character",
        type=int,
        default=1,
        help="campaign segments per character in each round, default: 1",
    )
    matrix_parser.add_argument(
        "--max-segment-runtime",
        type=float,
        default=None,
        help=(
            "optional live runtime cap per character segment; use this to "
            "rotate past a temporarily blocked campaign"
        ),
    )
    matrix_parser.add_argument(
        "--progress",
        action="store_true",
        help="print each character's bounded attempt and completion progress to stderr",
    )

    matrix_coverage_parser = subcommands.add_parser(
        "matrix-coverage",
        help="compare a validation matrix with all source-legal race/class pairs",
    )
    matrix_coverage_parser.add_argument("config", type=Path)
    matrix_coverage_parser.add_argument(
        "--source",
        type=Path,
        help="DD4 const.c or source directory; defaults to the local source checkout",
    )

    validation_matrix_parser = subcommands.add_parser(
        "prepare-validation-matrix",
        help="generate resumable level-10 campaigns for every source-legal race/class pair",
    )
    validation_matrix_parser.add_argument(
        "--workspace",
        type=Path,
        default=Path("runs/heroes/validation"),
    )
    validation_matrix_parser.add_argument("--output", type=Path)
    validation_matrix_parser.add_argument("--source", type=Path)

    configure_matrix_parser = subcommands.add_parser(
        "configure-matrix-passwords",
        help="generate and securely store missing passwords for a character matrix",
    )
    configure_matrix_parser.add_argument(
        "config",
        type=Path,
        help="path to the matrix YAML configuration",
    )

    mudlet_bridge_parser = subcommands.add_parser(
        "mudlet-bridge",
        help="generate the shared-file Mudlet command and GMCP bridge",
    )
    mudlet_bridge_parser.add_argument(
        "--directory",
        type=Path,
        default=Path("runs/mudlet-bridge"),
        help="shared directory visible to Mudlet, default: runs/mudlet-bridge",
    )

    show_runs_parser = subcommands.add_parser("show-runs", help="list stored scenario runs")
    show_runs_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path, default: {DEFAULT_DATABASE}",
    )
    show_runs_parser.add_argument("--limit", type=int, default=20, help="maximum runs to show")

    recover_runs_parser = subcommands.add_parser(
        "recover-runs",
        help="mark orphaned run and campaign records as interrupted",
    )
    recover_runs_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path, default: {DEFAULT_DATABASE}",
    )
    recover_runs_parser.add_argument(
        "--reason",
        default="runner process ended before the run could finish",
        help="failure reason to record",
    )
    recover_runs_parser.add_argument(
        "--campaign-id",
        type=int,
        help=(
            "recover one campaign using indexed, campaign-scoped queries; "
            "recommended for the shared large database"
        ),
    )
    recover_runs_parser.add_argument(
        "--character",
        help=(
            "character name used to bind an unlinked run during scoped "
            "campaign recovery"
        ),
    )

    show_sales_parser = subcommands.add_parser(
        "show-sales",
        help="list recorded loot-sale proceeds for a character",
    )
    show_sales_parser.add_argument(
        "--character",
        default="Ararisa",
        help="character whose sales to show, default: Ararisa",
    )
    show_sales_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path, default: {DEFAULT_DATABASE}",
    )
    show_sales_parser.add_argument(
        "--limit", type=int, default=20, help="maximum sales to show"
    )

    show_transcript_parser = subcommands.add_parser(
        "show-transcript",
        help="show a transcript by run id or JSONL transcript path",
    )
    show_transcript_parser.add_argument("target", help="run id or transcript JSONL path")
    show_transcript_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path for run id lookup, default: {DEFAULT_DATABASE}",
    )
    show_transcript_parser.add_argument(
        "--raw",
        action="store_true",
        help="print raw JSONL instead of formatted events",
    )

    show_state_parser = subcommands.add_parser(
        "show-state",
        help="show the latest character state or snapshot history for a run",
    )
    show_state_parser.add_argument("run_id", type=int, help="stored run id")
    show_state_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path, default: {DEFAULT_DATABASE}",
    )
    show_state_parser.add_argument(
        "--history",
        action="store_true",
        help="list all state snapshot revisions instead of the latest state",
    )

    report_parser = subcommands.add_parser(
        "report",
        help="render a Markdown or JSON summary of a stored run",
    )
    report_parser.add_argument("run_id", type=int, help="stored run id")
    report_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path, default: {DEFAULT_DATABASE}",
    )
    report_parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="report format, default: markdown",
    )
    report_parser.add_argument(
        "--output",
        type=Path,
        help="write the report to this file instead of standard output",
    )
    report_parser.add_argument(
        "--commentary-limit",
        type=int,
        default=20,
        help="maximum representative commentary entries, default: 20",
    )

    campaign_report_parser = subcommands.add_parser(
        "campaign-report",
        help="render the durable report for a stored campaign",
    )
    campaign_report_parser.add_argument(
        "campaign_id",
        type=int,
        help="stored campaign id",
    )
    campaign_report_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path, default: {DEFAULT_DATABASE}",
    )
    campaign_report_parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="report format, default: markdown",
    )
    campaign_report_parser.add_argument(
        "--output",
        type=Path,
        help="write the report to this file instead of standard output",
    )
    campaign_report_parser.add_argument(
        "--commentary-limit",
        type=int,
        default=40,
        help="maximum representative commentary entries, default: 40",
    )

    show_campaign_parser = subcommands.add_parser(
        "show-campaign",
        help="show checkpoint and segment history for a campaign",
    )
    show_campaign_parser.add_argument("campaign_id", type=int, help="stored campaign id")
    show_campaign_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path, default: {DEFAULT_DATABASE}",
    )
    show_campaign_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="maximum recent segments to print, default: 20",
    )

    show_policies_parser = subcommands.add_parser(
        "show-policies",
        help="show the evidence and status for a class and level band",
    )
    show_policies_parser.add_argument("--level", type=int, required=True)
    show_policies_parser.add_argument(
        "--class",
        dest="character_class",
        required=True,
    )

    coverage_parser = subcommands.add_parser(
        "show-policy-coverage",
        help="summarize registered policy coverage across a class level range",
    )
    coverage_parser.add_argument("--class", dest="character_class", required=True)
    coverage_parser.add_argument("--from-level", type=int, default=0)
    coverage_parser.add_argument("--to-level", type=int, default=100)

    show_prerequisites_parser = subcommands.add_parser(
        "show-prereqs",
        help="inspect DD4 skill prerequisites from the bundled server-source snapshot",
    )
    show_prerequisites_parser.add_argument("--class", dest="character_class", required=True)
    show_prerequisites_parser.add_argument("--skill")
    show_prerequisites_parser.add_argument(
        "--snapshot",
        type=Path,
        help="use a prerequisite snapshot JSON file instead of the bundled snapshot",
    )

    skill_analysis_parser = subcommands.add_parser(
        "skill-analysis",
        help="show source-backed leveling value and practice priorities for a class",
    )
    skill_analysis_parser.add_argument(
        "--class",
        dest="character_class",
        required=True,
    )
    skill_analysis_parser.add_argument(
        "--snapshot",
        type=Path,
        help="use a prerequisite snapshot JSON file instead of the bundled snapshot",
    )

    collect_evidence_parser = subcommands.add_parser(
        "collect-evidence",
        help="export a redaction-safe evidence record for a stored run",
    )
    collect_evidence_parser.add_argument("run_id", type=int, help="stored run id")
    collect_evidence_parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path, default: {DEFAULT_DATABASE}",
    )
    collect_evidence_parser.add_argument(
        "--output",
        type=Path,
        help="write JSON evidence to this file instead of standard output",
    )
    return parser


def _print_campaign_progress(message: str) -> None:
    """Keep long bounded campaign attempts visibly alive for operators."""
    print(f"Progress: {message}", file=sys.stderr, flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        try:
            result = asyncio.run(run_scenario_file(args.scenario))
        except Exception as exc:
            print(f"Run failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "starter":
        try:
            result = asyncio.run(run_starter_profile(args.profile))
        except Exception as exc:
            print(f"Starter run failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "arena-research":
        try:
            result = asyncio.run(
                run_arena_research_profile(
                    args.profile,
                    target_level=args.target_level,
                    kill_limit=args.kill_limit,
                )
            )
        except Exception as exc:
            print(f"Arena research failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "resupply":
        try:
            result = asyncio.run(run_resupply_profile(args.profile))
        except Exception as exc:
            print(f"Resupply run failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "return-home":
        try:
            result = asyncio.run(run_return_home_profile(args.profile))
        except Exception as exc:
            print(f"Return-home run failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "restock":
        try:
            result = asyncio.run(run_restock_profile(args.profile))
        except Exception as exc:
            print(f"Restock run failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "rearm":
        try:
            result = asyncio.run(run_rearm_profile(args.profile))
        except Exception as exc:
            print(f"Rearm run failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "sell-loot":
        try:
            result = asyncio.run(run_sell_loot_profile(args.profile))
        except Exception as exc:
            print(f"Sell-loot run failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "outfit":
        try:
            result = asyncio.run(run_outfit_profile(args.profile))
        except Exception as exc:
            print(f"Outfit run failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "money-loop":
        try:
            result = asyncio.run(
                run_money_loop_profile(
                    args.profile,
                    character_level=args.level,
                    trip_limit=args.trips,
                    source_directory=args.source,
                )
            )
        except Exception as exc:
            print(f"Money loop failed: {exc}", file=sys.stderr)
            return 1
        print(f"Money loop completed runs: {', '.join(map(str, result.run_ids))}")
        print(f"Targets: {', '.join(result.targets)}")
        print(f"Final restock run: {result.restock_run.run_id}")
        print(f"Database: {result.restock_run.database_path}")
        return 0

    if args.command == "guildmaster-research":
        try:
            result = asyncio.run(run_guildmaster_research_profile(args.profile))
        except Exception as exc:
            print(f"Guildmaster research failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "magic-shop-research":
        try:
            result = asyncio.run(
                run_magic_shop_research_profile(args.profile, buy_fly=args.buy_fly)
            )
        except Exception as exc:
            print(f"Magic Shop research failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "fastwalk-research":
        try:
            research_options = {
                "explore_direction": args.explore_direction,
                "explore_depth": args.depth,
                "attack_target": args.attack_target,
                "consider_target": args.consider_target,
                "maximum_target_count": args.maximum_target_count,
            }
            if args.allowed_bystanders:
                research_options["allowed_bystanders"] = tuple(
                    args.allowed_bystanders
                )
            result = asyncio.run(
                run_fastwalk_research_profile(
                    args.profile,
                    args.route,
                    **research_options,
                )
            )
        except Exception as exc:
            print(f"Fastwalk research failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "midennir-research":
        try:
            result = asyncio.run(run_midennir_research_profile(args.profile))
        except Exception as exc:
            print(f"Miden'nir research failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "ambush-research":
        try:
            research_options = {
                "guard_probe": args.guard_probe,
                "vile_probe": args.vile_probe,
                "raider_probe": args.raider_probe,
                "horseman_probe": args.horseman_probe,
                "vile_hunt": args.vile_hunt,
            }
            if args.raider_hunt:
                research_options["raider_hunt"] = True
            result = asyncio.run(
                run_ambush_research_profile(
                    args.profile,
                    **research_options,
                )
            )
        except Exception as exc:
            print(f"Ambush research failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "shire-research":
        try:
            result = asyncio.run(
                run_shire_research_profile(args.profile, hunt=args.hunt)
            )
        except Exception as exc:
            print(f"Shire research failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "moria-research":
        try:
            result = asyncio.run(
                run_moria_research_profile(
                args.profile,
                depth=args.depth,
                sanctuary_probe=args.sanctuary_probe,
                sanctuary_hunt=args.sanctuary_hunt,
                sanctuary_deep_hunt=args.sanctuary_deep_hunt,
            )
            )
        except Exception as exc:
            print(f"Moria research failed: {exc}", file=sys.stderr)
            return 1
        print(f"Run {result.run_id} {result.status}")
        print(f"Transcript: {result.transcript_path}")
        print(f"Database: {result.database_path}")
        return 0

    if args.command == "show-fastwalks":
        routes = routes_for_level(args.level) if args.level is not None else FASTWALKS
        print("name\tlevels\tnotation\tcommands")
        for route in routes:
            print(
                f"{route.name}\t{route.minimum_level}-{route.maximum_level}\t"
                f"{route.notation}\t{' ; '.join(route.commands)}"
            )
        return 0

    if args.command == "show-hunt-candidates":
        return show_hunt_candidates(
            args.source,
            level=args.level,
            character=args.character,
            database=args.database,
            limit=args.limit,
            include_xp_only=args.include_xp_only,
            include_all_areas=args.all_areas,
            autonomous_safe_only=args.autonomous_safe_only,
        )

    if args.command == "show-resource-sources":
        return show_resource_sources(
            args.source,
            level=args.level,
            effect=args.effect,
            character=args.character,
            database=args.database,
            limit=args.limit,
            include_all_areas=args.all_areas,
        )

    if args.command == "show-gear-sources":
        return show_gear_sources(
            args.source,
            level=args.level,
            character_class=args.character_class,
            subclass=args.subclass,
            stance=args.stance,
            character=args.character,
            database=args.database,
            limit=args.limit,
            include_all_areas=args.all_areas,
        )

    if args.command == "show-combat-readiness":
        return show_combat_readiness(
            args.source,
            level=args.level,
            character_class=args.character_class,
            subclass=args.subclass,
            character=args.character,
            database=args.database,
            limit=args.limit,
            include_all_areas=args.all_areas,
            json_output=args.json,
        )

    if args.command == "configure-login":
        try:
            configure_login(args.credential_name)
        except Exception as exc:
            print(f"Credential setup failed: {exc}", file=sys.stderr)
            return 1
        print(f"Stored login credential: {args.credential_name}")
        return 0

    if args.command == "configure-character-password":
        try:
            spec = load_character_spec(args.profile)
            credential_name = args.credential_name or spec.credential_name
            configure_character_password(credential_name)
        except Exception as exc:
            print(f"Credential setup failed: {exc}", file=sys.stderr)
            return 1
        print(f"Stored character password credential: {credential_name}")
        return 0

    if args.command == "campaign":
        try:
            result = asyncio.run(
                run_campaign_file(
                    args.config,
                    force_new=args.new,
                    segments=args.segments,
                    reset_retries=args.reset_retries,
                    reset_wait=args.reset_wait,
                    max_segment_runtime=args.max_segment_runtime,
                    retry_stalled=args.retry_stalled,
                    progress_callback=(
                        _print_campaign_progress if args.progress else None
                    ),
                )
            )
        except Exception as exc:
            print(f"Campaign failed: {exc}", file=sys.stderr)
            return 1
        print(f"Campaign {result.campaign_id} {result.status}")
        if result.message:
            print(f"Status: {result.message}")
        if result.checkpoint_id is not None:
            print(f"Checkpoint: {result.checkpoint_id}")
        print(f"Level: {result.state.get('level', '-')}")
        return 0 if result.status in {"success", "ready"} else 1

    if args.command == "hero":
        character_name = args.name
        if args.username:
            if (
                character_name
                and character_name.casefold() != args.username.casefold()
            ):
                print(
                    "HERO campaign failed: --name and --username must identify "
                    "the same DD4 character",
                    file=sys.stderr,
                )
                return 1
            character_name = args.username
        try:
            stored_request = None
            if args.new and (not args.race or not args.character_class):
                raise ValueError("--new requires both --race and --class")
            if not args.race or not args.character_class:
                if not character_name:
                    raise ValueError(
                        "--race and --class are required when creating a new hero"
                    )
                stored_request = load_existing_hero_request(
                    character_name,
                    workspace=args.workspace,
                    target_level=args.target_level,
                )
            request = HeroRequest(
                name=character_name,
                race=args.race or stored_request.race,
                sex=(
                    args.sex
                    or (stored_request.sex if stored_request is not None else "neuter")
                ),
                character_class=(
                    args.character_class
                    or stored_request.character_class
                ),
                subclass=(
                    args.subclass
                    if args.subclass is not None
                    else (stored_request.subclass if stored_request else None)
                ),
                personality=(
                    args.personality
                    if args.personality is not None
                    else (stored_request.personality if stored_request else None)
                ),
                transport=(
                    args.transport
                    or (stored_request.transport if stored_request else "telnet")
                ),
                mudlet_directory=(
                    args.mudlet_directory
                    if args.mudlet_directory is not None
                    else (stored_request.mudlet_directory if stored_request else None)
                ),
                legacy_profile_path=(
                    stored_request.legacy_profile_path
                    if stored_request is not None
                    else None
                ),
                legacy_campaign_path=(
                    stored_request.legacy_campaign_path
                    if stored_request is not None
                    else None
                ),
            )
            if args.prepare_only:
                preparation = prepare_hero_request(
                    request,
                    source=args.source,
                    workspace=args.workspace,
                    target_level=args.target_level,
                )
                result = None
            else:
                hero_runner = (
                    run_hero_until_target
                    if args.autonomous
                    else run_hero_request
                )
                hero_options = dict(
                    source=args.source,
                    workspace=args.workspace,
                    force_new=args.new,
                    reset_retries=args.reset_retries,
                    reset_wait=args.reset_wait,
                    max_segment_runtime=args.max_segment_runtime,
                    retry_stalled=args.retry_stalled,
                    progress_callback=(
                        _print_campaign_progress if args.progress else None
                    ),
                    target_level=args.target_level,
                    password=args.password,
                    remember_password=args.remember_password,
                )
                if args.autonomous:
                    hero_options.update(
                        cycles=args.segments,
                        max_reset_waits=args.max_reset_waits,
                    )
                else:
                    hero_options["segments"] = args.segments
                preparation, result = asyncio.run(
                    hero_runner(
                        request,
                        **hero_options,
                    )
                )
        except KeyboardInterrupt:
            print(
                "HERO campaign interrupted; the durable checkpoint is preserved "
                "for the next resume.",
                file=sys.stderr,
            )
            return 130
        except Exception as exc:
            print(f"HERO campaign failed: {exc}", file=sys.stderr)
            return 1
        print(
            f"Character: {preparation.character.name} "
            f"({preparation.character.race} "
            f"{preparation.character.character_class})"
        )
        print(
            "Manifest: "
            + (
                str(preparation.manifest_path)
                if preparation.manifest_path is not None
                else "legacy campaign record"
            )
        )
        print(f"Profile: {preparation.profile_path}")
        print(f"Campaign: {preparation.campaign_path}")
        print("Prepared: resumed" if preparation.resumed else "Prepared: new")
        if result is None:
            return 0
        print(f"Campaign {result.campaign_id} {result.status}")
        if result.message:
            print(f"Status: {result.message}")
        print(f"Level: {result.state.get('level', '-')}")
        return 0 if result.status in {"success", "ready"} else 1

    if args.command == "hero-options":
        try:
            catalog = load_character_catalog(args.source)
        except Exception as exc:
            print(f"Could not load DD4 character options: {exc}", file=sys.stderr)
            return 1
        print(f"Source: {catalog.source}")
        print("Sex (cosmetic): " + ", ".join(catalog.sexes))
        print("Races: " + ", ".join(option.name for option in catalog.races))
        print("Classes: " + ", ".join(option.name for option in catalog.classes))
        print("Subclasses:")
        for option in catalog.subclasses:
            print(f"  {option.base_class}: {option.name}")
        return 0

    if args.command == "hero-rotation":
        try:
            rotation = asyncio.run(
                run_campaign_rotation(
                    args.config,
                    rounds=args.rounds,
                    max_segment_runtime=args.max_segment_runtime,
                    progress_callback=(
                        _print_campaign_progress if args.progress else None
                    ),
                )
            )
        except KeyboardInterrupt:
            print(
                "Character rotation interrupted; campaign checkpoints are "
                "preserved for the next run.",
                file=sys.stderr,
            )
            return 130
        except Exception as exc:
            print(f"Character rotation failed: {exc}", file=sys.stderr)
            return 1

        print(f"Rotation: {rotation.spec.name}")
        print(f"Target level: {rotation.spec.target_level}")
        for attempt in rotation.attempts:
            if attempt.result is None:
                print(
                    f"{attempt.entry_id} (round {attempt.cycle}): deferred; "
                    f"{attempt.error}"
                )
                continue
            state = attempt.result.state
            print(
                f"{attempt.entry_id} (round {attempt.cycle}): "
                f"{attempt.result.status}; level={state.get('level', '-')} "
                f"xp={state.get('xp', '-')}"
            )
        for entry_id, reason in rotation.deferred_entry_reasons.items():
            print(f"Deferred {entry_id}: {reason}")
        if rotation.completed_entry_ids:
            print("Completed: " + ", ".join(rotation.completed_entry_ids))
        return 0

    if args.command == "matrix-coverage":
        try:
            coverage = matrix_coverage(
                args.config,
                catalog=load_character_catalog(args.source),
            )
            live_coverage = live_matrix_coverage(args.config)
        except Exception as exc:
            print(f"Could not inspect matrix coverage: {exc}", file=sys.stderr)
            return 1
        print(f"Source: {coverage.source}")
        print(f"Legal race/class pairs: {coverage.legal_pair_count}")
        print(f"Declared pairs: {len(coverage.covered_pairs)}")
        print(f"Undeclared pairs: {len(coverage.missing_pairs)}")
        print("Declared classes: " + ", ".join(coverage.covered_classes))
        print("Undeclared classes: " + ", ".join(coverage.missing_classes))
        print("Declared sexes: " + ", ".join(coverage.observed_sexes))
        print(
            f"Live-validated pairs at level {live_coverage.target_level}: "
            f"{len(live_coverage.validated_pairs)}"
        )
        print(f"Live-pending declared pairs: {len(live_coverage.pending_pairs)}")
        print("Live-validated sexes: " + ", ".join(live_coverage.validated_sexes))
        print(
            "Creation-to-target proof pairs: "
            f"{len(live_coverage.creation_to_target_pairs)}"
        )
        print(
            "Creation-to-target pending pairs: "
            f"{len(live_coverage.creation_pending_pairs)}"
        )
        print(
            "Creation-to-target proof sexes: "
            + ", ".join(live_coverage.creation_validated_sexes)
        )
        print("entry\tlevel\tstatus\tcampaign\tproof\tcheckpoint")
        for entry in live_coverage.entries:
            print(
                f"{entry.entry_id}\t{entry.level}\t"
                f"{entry.campaign_status or 'not-started'}\t"
                f"{entry.campaign_id if entry.campaign_id is not None else '-'}\t"
                f"{entry.proof_status}\t{entry.target_checkpoint_reason or '-'}"
            )
        return 0

    if args.command == "prepare-validation-matrix":
        try:
            prepared = prepare_validation_matrix(
                source=args.source,
                workspace=args.workspace,
                matrix_path=args.output,
            )
        except Exception as exc:
            print(f"Could not prepare validation matrix: {exc}", file=sys.stderr)
            return 1
        print(f"Matrix: {prepared.matrix_path}")
        print(f"Prepared race/class campaigns: {len(prepared.preparations)}")
        print("Observed sexes: " + ", ".join(
            sorted({item.character.gender for item in prepared.preparations})
        ))
        return 0

    if args.command == "matrix":
        try:
            result = asyncio.run(
                run_matrix_file(
                    args.config,
                    rounds=args.rounds,
                    segments_per_character=args.segments_per_character,
                    max_segment_runtime=args.max_segment_runtime,
                    force_new=args.new,
                    progress_callback=(
                        _print_campaign_progress if args.progress else None
                    ),
                )
            )
        except Exception as exc:
            print(f"Matrix failed: {exc}", file=sys.stderr)
            return 1
        print(f"Matrix: {result.name}")
        print(f"Status: {result.status}; target level: {result.target_level}")
        print("entry\tcharacter\tclass\tlevel\tstatus\tcampaign\tmessage")
        for entry in result.entries:
            print(
                f"{entry.entry_id}\t{entry.character_name}\t"
                f"{entry.character_class}\t{entry.level}\t{entry.status}\t"
                f"{entry.campaign_id or '-'}\t{entry.message or '-'}"
            )
        return 0 if result.status == "success" else 1

    if args.command == "configure-matrix-passwords":
        try:
            results = provision_matrix_passwords(args.config)
        except Exception as exc:
            print(f"Matrix credential setup failed: {exc}", file=sys.stderr)
            return 1
        for result in results:
            print(
                f"{result.entry_id}: {result.status} credential "
                f"{result.credential_name}"
            )
        return 0

    if args.command == "mudlet-bridge":
        try:
            paths = MudletBridge(args.directory).initialize()
        except Exception as exc:
            print(f"Mudlet bridge setup failed: {exc}", file=sys.stderr)
            return 1
        print(f"Mudlet script: {paths.script_path}")
        print(f"Command inbox: {paths.command_path}")
        print(f"Event outbox: {paths.event_path}")
        return 0

    if args.command == "show-runs":
        return show_runs(args.database, limit=args.limit)

    if args.command == "recover-runs":
        return recover_runs(
            args.database,
            reason=args.reason,
            campaign_id=args.campaign_id,
            character=args.character,
        )

    if args.command == "show-sales":
        return show_sales(args.database, character=args.character, limit=args.limit)

    if args.command == "show-transcript":
        return show_transcript(args.target, database=args.database, raw=args.raw)

    if args.command == "show-state":
        return show_state(args.run_id, database=args.database, history=args.history)

    if args.command == "report":
        return show_report(
            args.run_id,
            database=args.database,
            report_format=args.format,
            output=args.output,
            commentary_limit=args.commentary_limit,
        )

    if args.command == "campaign-report":
        return show_campaign_report(
            args.campaign_id,
            database=args.database,
            report_format=args.format,
            output=args.output,
            commentary_limit=args.commentary_limit,
        )

    if args.command == "show-campaign":
        return show_campaign(
            args.campaign_id,
            database=args.database,
            limit=args.limit,
        )

    if args.command == "show-policies":
        return show_policies(args.level, args.character_class)

    if args.command == "show-policy-coverage":
        return show_policy_coverage(
            args.character_class,
            from_level=args.from_level,
            to_level=args.to_level,
        )

    if args.command == "autonomy-audit":
        try:
            if args.all_classes:
                if args.subclass:
                    raise ValueError("--subclass cannot be combined with --all-classes")
                audits = audit_all_base_classes(
                    race=args.race,
                    sex=args.sex,
                    target_level=args.target_level,
                    source=args.source,
                )
            else:
                audits = (
                    audit_hero_request(
                        race=args.race,
                        sex=args.sex,
                        character_class=args.character_class,
                        subclass=args.subclass,
                        target_level=args.target_level,
                        source=args.source,
                    ),
                )
        except (OSError, ValueError, KeyError, TypeError) as exc:
            print(f"Autonomy audit failed: {exc}", file=sys.stderr)
            return 2
        if args.json:
            if args.all_classes:
                print(
                    json.dumps(
                        [audit.to_mapping() for audit in audits],
                        indent=2,
                        sort_keys=True,
                    )
                )
            else:
                print(audit_json(audits[0]), end="")
        else:
            print("\n".join(render_autonomy_audit(audit).rstrip() for audit in audits))
        return 0

    if args.command == "show-prereqs":
        return show_prereqs(
            args.character_class,
            skill=args.skill,
            snapshot=args.snapshot,
        )

    if args.command == "skill-analysis":
        return show_skill_analysis(
            args.character_class,
            snapshot=args.snapshot,
        )

    if args.command == "collect-evidence":
        return collect_evidence(args.run_id, database=args.database, output=args.output)

    parser.error(f"Unknown command: {args.command}")
    return 2


def show_runs(database: Path, *, limit: int) -> int:
    if limit < 1:
        print("--limit must be at least 1", file=sys.stderr)
        return 2
    if not database.exists():
        print(f"No run database found at {database.resolve()}", file=sys.stderr)
        return 1

    with RunStorage(database, read_only=True) as storage:
        runs = storage.list_runs(limit=limit)

    print(f"Database: {database.resolve()}")
    if not runs:
        print("No runs recorded.")
        return 0

    print("id\tstatus\tscenario\tboot_id\tstarted_at\tfinished_at\ttranscript")
    for run in runs:
        print(
            "\t".join(
                [
                    str(run["id"]),
                    run["status"],
                    run["scenario_name"],
                    run["boot_id"] or "-",
                    run["started_at"],
                    run["finished_at"] or "-",
                    run["transcript_path"] or "-",
                ]
            )
        )
    return 0


def recover_runs(
    database: Path,
    *,
    reason: str,
    campaign_id: int | None = None,
    character: str | None = None,
) -> int:
    if not database.exists():
        print(f"No run database found at {database.resolve()}", file=sys.stderr)
        return 1

    if campaign_id is not None:
        try:
            with RunStorage(database) as storage:
                repaired_events, recovered_runs, segments = (
                    storage.recover_campaign(
                        campaign_id,
                        reason=reason,
                        character_name=character,
                    )
                )
        except KeyError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(f"Database: {database.resolve()}")
        print(f"Campaign {campaign_id} recovered with indexed scoped queries.")
        print(
            f"Replayed {repaired_events} transcript event(s) across "
            f"{1 if repaired_events else 0} run(s)."
        )
        print("Bound 0 interrupted campaign segment(s) to a run.")
        print(f"Marked {recovered_runs} interrupted run(s) as failed.")
        print(
            f"Marked {segments} interrupted campaign segment(s) "
            f"in campaign {campaign_id} as failed or ready."
        )
        return 0

    with RunStorage(database) as storage:
        repaired_runs, repaired_events = storage.repair_transcript_events()
        bound_segments = storage.bind_unlinked_campaign_runs()
        recovered = storage.fail_interrupted_runs(reason=reason)
        segments, campaigns = storage.fail_interrupted_campaign_segments(reason=reason)
        orphaned_campaigns = storage.recover_orphaned_campaigns(reason=reason)
    print(f"Database: {database.resolve()}")
    print(
        f"Replayed {repaired_events} transcript event(s) across "
        f"{repaired_runs} run(s)."
    )
    print(f"Bound {bound_segments} interrupted campaign segment(s) to a run.")
    print(f"Marked {recovered} interrupted run(s) as failed.")
    print(
        f"Marked {segments} interrupted campaign segment(s) "
        f"across {campaigns} campaign(s) as failed."
    )
    print(
        f"Returned {orphaned_campaigns} orphaned campaign(s) without a "
        "running segment to ready."
    )
    return 0


def show_sales(database: Path, *, character: str, limit: int) -> int:
    if limit < 1:
        print("--limit must be at least 1", file=sys.stderr)
        return 2
    if not database.exists():
        print(f"No run database found at {database.resolve()}", file=sys.stderr)
        return 1

    with RunStorage(database, read_only=True) as storage:
        sales = storage.list_loot_sales(character)

    print(f"Database: {database.resolve()}")
    print(f"Character: {character}")
    if not sales:
        print("No loot sales recorded.")
        return 0

    visible = sales[-limit:]
    print("id\trun\tboot\titem\tshop\tcoins\ttimestamp")
    for sale in visible:
        print(
            "\t".join(
                [
                    str(sale["id"]),
                    str(sale["run_id"]),
                    sale["boot_id"] or "-",
                    sale["item_description"],
                    sale["shop_name"],
                    str(sale["sold_coins"]),
                    sale["timestamp"],
                ]
            )
        )
    print(f"Total shown: {sum(sale['sold_coins'] for sale in visible)} coins")
    return 0


def show_hunt_candidates(
    source: Path,
    *,
    level: int,
    character: str,
    database: Path,
    limit: int,
    include_xp_only: bool = False,
    include_all_areas: bool = False,
    autonomous_safe_only: bool = False,
) -> int:
    if level < 1:
        print("--level must be at least 1", file=sys.stderr)
        return 2
    if limit < 1:
        print("--limit must be at least 1", file=sys.stderr)
        return 2
    try:
        world = load_world_source(source, include_all_areas=include_all_areas)
    except (OSError, ValueError) as exc:
        print(f"Unable to load DD4 source: {exc}", file=sys.stderr)
        return 1

    boot_id: str | None = None
    kill_counts: Counter[str] = Counter()
    character_max_hp: int | None = None
    character_alignment: int | None = None
    character_fame: int | None = None
    recall_origins: dict[int, int] | None = None
    character_class: str | None = None
    character_subclass: str | None = None
    recorded_known_skills: tuple[str, ...] = ()
    recorded_known_skill_levels: dict[str, int] = {}
    if database.exists():
        with RunStorage(database, read_only=True) as storage:
            boot_id = storage.latest_boot_id()
            latest_state = _latest_inspection_state(storage, character)
            latest_state = dict(latest_state or {})
            campaign = storage.get_latest_campaign_for_character(character)
            if campaign is not None:
                checkpoint = storage.get_latest_campaign_checkpoint(
                    int(campaign["id"])
                )
                if checkpoint is not None:
                    try:
                        checkpoint_state = json.loads(checkpoint["state_json"])
                    except (TypeError, json.JSONDecodeError):
                        checkpoint_state = {}
                    if isinstance(checkpoint_state, dict):
                        for key, value in checkpoint_state.items():
                            if key.startswith("campaign_") or key in {
                                "character_class",
                                "subclass",
                                "recall_origins",
                            }:
                                latest_state[key] = value
            if latest_state is not None:
                character_alignment = _inspection_alignment(latest_state)
                character_fame = _inspection_fame(latest_state)
                recall_origins = recall_origins_from_state(latest_state)
                raw_class = latest_state.get("character_class")
                if isinstance(raw_class, str) and raw_class.strip():
                    character_class = raw_class.strip()
                raw_subclass = latest_state.get("subclass")
                if isinstance(raw_subclass, str) and raw_subclass.strip():
                    character_subclass = raw_subclass.strip()
                raw_known_skills = latest_state.get("campaign_known_skills")
                if isinstance(raw_known_skills, str):
                    recorded_known_skills = (raw_known_skills,)
                elif isinstance(
                    raw_known_skills,
                    (list, tuple, set, frozenset),
                ):
                    recorded_known_skills = tuple(
                        str(skill) for skill in raw_known_skills
                    )
                raw_known_skill_levels = latest_state.get(
                    "campaign_known_skill_levels"
                )
                if isinstance(raw_known_skill_levels, dict):
                    for skill, value in raw_known_skill_levels.items():
                        try:
                            recorded_known_skill_levels[str(skill)] = int(value)
                        except (TypeError, ValueError):
                            continue
                stored_level = latest_state.get("level")
                raw_max_hp = latest_state.get("max_hp")
                if (
                    stored_level == level
                    and isinstance(raw_max_hp, (int, float))
                    and raw_max_hp > 0
                ):
                    character_max_hp = int(raw_max_hp)
            if boot_id is not None:
                kill_counts.update(
                    row["mob_name"]
                    for row in storage.list_mob_kills(
                        character,
                        boot_id=boot_id,
                    )
                )
    rank_kwargs: dict[str, Any] = {
        "character_level": level,
        "boot_kill_counts": kill_counts,
        "include_xp_only": include_xp_only,
        "character_max_hp": character_max_hp,
        "character_alignment": character_alignment,
        "include_all_areas": include_all_areas,
        "recall_origins": recall_origins,
    }
    if recorded_known_skills and character_class:
        rank_kwargs.update(
            {
                "character_class": character_class,
                "character_subclass": character_subclass,
                "known_skills": recorded_known_skills,
                "known_skill_levels": recorded_known_skill_levels,
            }
        )
    candidates = rank_hunt_candidates(world, **rank_kwargs)
    if autonomous_safe_only:
        candidates = [candidate for candidate in candidates if candidate.autonomous_safe]

    print(f"Source: {source.resolve()}")
    print(f"Character: {character}, level {level}")
    print(f"Character class: {character_class or 'unknown'}")
    print(f"Character max HP: {character_max_hp or 'unknown'}")
    print(
        "Player alignment: "
        + (str(character_alignment) if character_alignment is not None else "unknown")
    )
    print(
        "Player fame: "
        + (str(character_fame) if character_fame is not None else "unknown")
    )
    print(f"Current reboot: {boot_id or 'unknown'}")
    if recall_origins:
        origin_names = []
        for index in sorted(recall_origins):
            point = recall_point_for_index(index)
            origin_names.append(
                f"{index} {point.name if point is not None else 'source point'}"
            )
        print("Recall origins: " + ", ".join(origin_names))
    print(
        "status\tscore\tarea\ttarget\tmobility\tsearch_rooms\t"
        "rank\tsource_level\tfuzzed_levels\t"
        "base_hp\tpeak_round\troom\trecall_origin\troute\t"
        "move_cost\tflight_cost\trequires_flight\t"
        "room_spawns\tspawn_limit\t"
        "boot_kills\tloot\thazards\tautonomy_rejections\t"
        "combat_readiness\tcombat_bonus\ttemplate\txp_modifier\t"
        "damage_modifier\tundead"
    )
    for candidate in candidates[:limit]:
        mobile = world.mobiles.get(candidate.mobile_vnum)
        if mobile is None:
            mobility = "unknown"
            search_room_count = 0
        elif mobile.confused:
            mobility = "confused-wanderer"
            search_room_count = len(
                source_mobile_search_rooms(
                    world,
                    candidate.mobile_vnum,
                    maximum_rooms=512,
                )
            )
        elif not mobile.wanders:
            mobility = (
                "fixed-sentinel"
                if mobile.sentinel
                else "fixed-master-bound"
            )
            search_room_count = len(
                source_mobile_search_rooms(
                    world,
                    candidate.mobile_vnum,
                    maximum_rooms=512,
                )
            )
        elif mobile.stay_area:
            mobility = "stay-area-wanderer"
            search_room_count = len(
                source_mobile_search_rooms(
                    world,
                    candidate.mobile_vnum,
                    maximum_rooms=512,
                )
            )
        else:
            mobility = "global-wanderer"
            search_room_count = len(
                source_mobile_search_rooms(
                    world,
                    candidate.mobile_vnum,
                    maximum_rooms=512,
                )
            )
        loot = "; ".join(candidate.loot)
        if candidate.contained_coins:
            loot = "; ".join(
                value
                for value in (loot, f"{candidate.contained_coins} contained coins")
                if value
            )
        print(
            "\t".join(
                [
                    candidate.status,
                    f"{candidate.score:g}",
                    candidate.area_file,
                    candidate.target,
                    mobility,
                    str(search_room_count),
                    candidate.rank,
                    str(candidate.level),
                    f"{candidate.estimated_level_range[0]}-"
                    f"{candidate.estimated_level_range[1]}",
                    f"{candidate.estimated_base_hp_range[0]}-"
                    f"{candidate.estimated_base_hp_range[1]}",
                    str(candidate.estimated_peak_round_damage),
                    f"{candidate.room_vnum} {candidate.room_name}",
                    str(candidate.route_origin_recall_index),
                    ";".join(candidate.route),
                    str(candidate.estimated_move_cost),
                    str(candidate.estimated_flying_move_cost),
                    "yes" if candidate.requires_flight else "no",
                    str(candidate.room_spawn_count),
                    str(candidate.source_spawn_limit),
                    str(candidate.boot_kills),
                    loot or "-",
                    "; ".join(candidate.hazards) or "-",
                    "; ".join(candidate.autonomy_rejections) or "-",
                    candidate.combat_readiness,
                    str(candidate.combat_readiness_bonus),
                    (mobile.template_name if mobile is not None else None) or "-",
                    str(mobile.xp_modifier if mobile is not None else 0),
                    str(
                        candidate.source_damage_modifier
                        if candidate.source_damage_modifier is not None
                        else "unknown"
                    ),
                    "yes" if candidate.undead else "no",
                ]
            )
        )
    return 0


def show_resource_sources(
    source: Path,
    *,
    level: int,
    effect: str,
    character: str,
    database: Path,
    limit: int,
    include_all_areas: bool = False,
) -> int:
    if level < 1:
        print("--level must be at least 1", file=sys.stderr)
        return 2
    if limit < 1:
        print("--limit must be at least 1", file=sys.stderr)
        return 2
    try:
        world = load_world_source(source, include_all_areas=include_all_areas)
    except (OSError, ValueError) as exc:
        print(f"Unable to load DD4 source: {exc}", file=sys.stderr)
        return 1

    boot_id: str | None = None
    character_max_hp: int | None = None
    recall_origins: dict[int, int] | None = None
    if database.exists():
        with RunStorage(database, read_only=True) as storage:
            boot_id = storage.latest_boot_id()
            latest_state = _latest_inspection_state(storage, character)
            if latest_state is not None:
                recall_origins = recall_origins_from_state(latest_state)
                stored_level = latest_state.get("level")
                raw_max_hp = latest_state.get("max_hp")
                if (
                    stored_level == level
                    and isinstance(raw_max_hp, (int, float))
                    and raw_max_hp > 0
                ):
                    character_max_hp = int(raw_max_hp)

    try:
        placements = rank_resource_sources(
            world,
            character_level=level,
            effect=effect,
            character_max_hp=character_max_hp,
            include_all_areas=include_all_areas,
            recall_origins=recall_origins,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    item_type_names = {
        2: "scroll",
        3: "wand",
        4: "staff",
        5: "weapon",
        9: "armour",
        10: "potion",
        26: "pill",
        15: "container",
        19: "food",
        20: "money",
    }

    def clean(value: object) -> str:
        return " ".join(str(value).replace("\t", " ").split())

    def room_label(room_vnum: int, room_name: str) -> str:
        return f"{room_vnum} {clean(room_name)}"

    print(f"Source: {source.resolve()}")
    print(f"Character: {character}, level {level}")
    print(f"Character max HP: {character_max_hp or 'unknown'}")
    print(f"Current reboot: {boot_id or 'unknown'}")
    if recall_origins:
        origin_names = []
        for index in sorted(recall_origins):
            point = recall_point_for_index(index)
            origin_names.append(
                f"{index} {point.name if point is not None else 'source point'}"
            )
        print("Recall origins: " + ", ".join(origin_names))
    print(
        "effect\tstatus\tobject_vnum\tobject\ttype\tsource_kind\t"
        "source_mobile\treset_room\tarea\tcount\tsource_levels\t"
        "route_origin\troute\tactivation\thazards\tautonomy_rejections\t"
        "source_analysis_route\troute_key_objects\troute_key_sources\t"
        "container_objects\tcontainer_keys\tcontainer_key_sources"
    )
    for placement in placements[:limit]:
        source_mobile = (
            f"{placement.source_mobile_vnum} {clean(placement.source_mobile)}"
            if placement.source_mobile_vnum is not None
            else "-"
        )
        minimum, maximum = placement.source_level_range
        source_levels = (
            f"{minimum}-{maximum}"
            if minimum or maximum
            else "unknown"
        )
        route_origin = str(placement.route_origin_recall_index)
        print(
            "\t".join(
                (
                    placement.effect,
                    placement.status,
                    str(placement.object_vnum),
                    clean(placement.object_description),
                    item_type_names.get(placement.item_type, str(placement.item_type)),
                    placement.source_kind,
                    source_mobile,
                    room_label(placement.room_vnum, placement.room_name),
                    placement.area_file,
                    str(placement.maximum_count),
                    source_levels,
                    route_origin,
                    ";".join(placement.route) or "-",
                    (
                        (
                            f"{placement.activation.mode}:"
                            f"{placement.activation.command}"
                            f"{(' ' + placement.activation.target) if placement.activation.target else ''}"
                            f" [{placement.activation.spell}]"
                        )
                        if placement.activation is not None
                        else "-"
                    ),
                    "; ".join(clean(value) for value in placement.hazards) or "-",
                    "; ".join(
                        clean(value) for value in placement.autonomy_rejections
                    )
                    or "-",
                    ";".join(placement.source_analysis_route) or "-",
                    ",".join(
                        str(vnum) for vnum in placement.route_key_object_vnums
                    )
                    or "-",
                    ",".join(
                        str(vnum)
                        for vnum in placement.route_key_source_mobile_vnums
                    )
                    or "-",
                    ",".join(
                        str(vnum) for vnum in placement.container_object_vnums
                    )
                    or "-",
                    ",".join(
                        str(vnum) for vnum in placement.required_key_object_vnums
                    )
                    or "-",
                    ",".join(
                        str(vnum)
                        for vnum in placement.required_key_source_mobile_vnums
                    )
                    or "-",
                )
            )
        )
    print(f"Placements shown: {min(limit, len(placements))} of {len(placements)}")
    return 0


def show_gear_sources(
    source: Path,
    *,
    level: int,
    character_class: str,
    subclass: str | None,
    stance: str,
    character: str,
    database: Path,
    limit: int,
    include_all_areas: bool = False,
) -> int:
    if level < 1:
        print("--level must be at least 1", file=sys.stderr)
        return 2
    if limit < 1:
        print("--limit must be at least 1", file=sys.stderr)
        return 2
    try:
        world = load_world_source(source, include_all_areas=include_all_areas)
    except (OSError, ValueError) as exc:
        print(f"Unable to load DD4 source: {exc}", file=sys.stderr)
        return 1

    boot_id: str | None = None
    character_max_hp: int | None = None
    recall_origins: dict[int, int] | None = None
    current_items = []
    catalog = GearCatalog(getattr(world, "objects", {}))

    def state_descriptions(value: object) -> list[str]:
        if isinstance(value, str):
            try:
                return state_descriptions(json.loads(value))
            except json.JSONDecodeError:
                return []
        if isinstance(value, dict):
            descriptions: list[str] = []
            for key in ("short_desc", "description", "name"):
                candidate = value.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    descriptions.append(candidate)
            for key, item in value.items():
                if key not in {"short_desc", "description", "name"}:
                    descriptions.extend(state_descriptions(item))
            return descriptions
        if isinstance(value, (list, tuple)):
            descriptions: list[str] = []
            for item in value:
                descriptions.extend(state_descriptions(item))
            return descriptions
        return []

    if database.exists():
        with RunStorage(database, read_only=True) as storage:
            boot_id = storage.latest_boot_id()
            latest_state = _latest_inspection_state(storage, character)
            if latest_state is not None:
                recall_origins = recall_origins_from_state(latest_state)
                stored_level = latest_state.get("level")
                raw_max_hp = latest_state.get("max_hp")
                if (
                    stored_level == level
                    and isinstance(raw_max_hp, (int, float))
                    and raw_max_hp > 0
                ):
                    character_max_hp = int(raw_max_hp)
                current_items = catalog.match_many_usable(
                    [
                        *(
                            _equipment_descriptions(latest_state.get("equipment"))
                            or state_descriptions(
                                latest_state.get("campaign_worn_equipment")
                            )
                        ),
                        *_inventory_descriptions(latest_state.get("inventory")),
                    ],
                    character_class=character_class,
                    subclass=subclass,
                )

    try:
        placements = rank_gear_sources(
            world,
            character_level=level,
            character_class=character_class,
            subclass=subclass,
            stance=stance,
            current_items=current_items,
            character_max_hp=character_max_hp,
            include_all_areas=include_all_areas,
            recall_origins=recall_origins,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    def clean(value: object) -> str:
        return " ".join(str(value).replace("\t", " ").split())

    def room_label(room_vnum: int, room_name: str) -> str:
        return f"{room_vnum} {clean(room_name)}"

    print(f"Source: {source.resolve()}")
    print(
        f"Character: {character}, level {level}, class {character_class}"
        + (f", subclass {subclass}" if subclass else "")
    )
    print(f"Stance: {stance}")
    print(
        "Weapon preference: "
        + (
            weapon_preference_for_character(
                character_class,
                subclass=subclass,
            )
            or "none"
        )
    )
    print(f"Character max HP: {character_max_hp or 'unknown'}")
    print(f"Current reboot: {boot_id or 'unknown'}")
    print(
        "object_vnum\tkeywords\tobject\tcategory\tbetter_than_current\tstatus\t"
        "source_kind\tsource_mobile\treset_room\tarea\tcount\t"
        "source_levels\troute_origin\troute\tstance_rank\thazards\t"
        "autonomy_rejections\tweapon_role"
    )
    for placement in placements[:limit]:
        source_mobile = (
            f"{placement.source_mobile_vnum} {clean(placement.source_mobile)}"
            if placement.source_mobile_vnum is not None
            else "-"
        )
        minimum, maximum = placement.source_level_range
        source_levels = (
            f"{minimum}-{maximum}" if minimum or maximum else "unknown"
        )
        print(
            "\t".join(
                (
                    str(placement.object_vnum),
                    clean(placement.object_keywords),
                    clean(placement.object_description),
                    placement.category,
                    "yes" if placement.better_than_current else "no",
                    placement.status,
                    placement.source_kind,
                    source_mobile,
                    room_label(placement.room_vnum, placement.room_name),
                    placement.area_file,
                    str(placement.maximum_count),
                    source_levels,
                    str(placement.route_origin_recall_index),
                    ";".join(placement.route) or "-",
                    ",".join(str(value) for value in placement.stance_rank),
                    "; ".join(clean(value) for value in placement.hazards)
                    or "-",
                    "; ".join(
                        clean(value)
                        for value in placement.autonomy_rejections
                    )
                    or "-",
                    placement.weapon_role,
                )
            )
        )
    print(f"Placements shown: {min(limit, len(placements))} of {len(placements)}")
    return 0


def _inspection_state_descriptions(value: object) -> list[str]:
    """Extract item descriptions from the structured state snapshot."""
    if isinstance(value, str):
        try:
            return _inspection_state_descriptions(json.loads(value))
        except json.JSONDecodeError:
            return []
    if isinstance(value, Mapping):
        descriptions: list[str] = []
        for key in ("short_desc", "description", "name"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                descriptions.append(candidate)
        for key, item in value.items():
            if key not in {"short_desc", "description", "name"}:
                descriptions.extend(_inspection_state_descriptions(item))
        return descriptions
    if isinstance(value, (list, tuple)):
        descriptions: list[str] = []
        for item in value:
            descriptions.extend(_inspection_state_descriptions(item))
        return descriptions
    return []


def _load_inspection_state(
    database: Path,
    character: str,
) -> tuple[dict[str, Any], str | None, Counter[str]]:
    """Load the same compact state/history view used by source reports."""
    if not database.exists():
        return {}, None, Counter()

    with RunStorage(database, read_only=True) as storage:
        state = _latest_inspection_state(storage, character)
        campaign = storage.get_latest_campaign_for_character(character)
        if campaign is not None:
            checkpoint = storage.get_latest_campaign_checkpoint(int(campaign["id"]))
            if checkpoint is not None:
                try:
                    checkpoint_state = json.loads(checkpoint["state_json"])
                except (TypeError, json.JSONDecodeError):
                    checkpoint_state = {}
                if isinstance(checkpoint_state, dict):
                    for key, value in checkpoint_state.items():
                        if key.startswith("campaign_") or key in {
                            "character_class",
                            "subclass",
                            "recall_origins",
                        } | _INSPECTION_CHECKPOINT_STATE_KEYS:
                            state[key] = value

        boot_id = storage.latest_boot_id()
        kill_counts: Counter[str] = Counter()
        if boot_id is not None:
            kill_counts.update(
                str(row["mob_name"])
                for row in storage.list_mob_kills(character, boot_id=boot_id)
            )
    return state, boot_id, kill_counts


def _readiness_candidate_in_band(candidate: Any, level: int) -> bool:
    minimum, maximum = candidate.estimated_level_range
    if minimum <= 0 or maximum < minimum:
        minimum, maximum = candidate.level - 2, candidate.level + 2
    return maximum > level - 5 and minimum <= level + 1


def _readiness_fame_window(
    candidate: Any,
    *,
    level: int,
    source_world: Any,
) -> tuple[str, tuple[int, int]] | None:
    """Return the source fame branch and usable level window for a target."""
    mobiles = getattr(source_world, "mobiles", {})
    mobile = mobiles.get(candidate.mobile_vnum) if hasattr(mobiles, "get") else None
    awards_fame = bool(getattr(mobile, "awards_fame", False))
    window = _source_ranked_fame_level_window(
        candidate,
        character_level=level,
        awards_fame=awards_fame,
    )
    if window is None:
        return None
    return ("famous" if awards_fame else "ordinary", window)


def _readiness_level_range(low: int, high: int) -> list[int]:
    """Clip an inspection range to DD4's playable levels."""
    clipped_low = max(1, low)
    clipped_high = min(100, high)
    return [clipped_low, clipped_high] if clipped_low <= clipped_high else []


def _format_readiness_level_range(level_range: list[int]) -> str:
    """Render an empty HERO-boundary range without indexing it."""
    return (
        f"{level_range[0]}-{level_range[1]}"
        if level_range
        else "none"
    )


def _format_optional_bool(value: bool | None) -> str:
    """Render a three-state inspection flag without implying authorization."""
    if value is None:
        return "unknown"
    return "yes" if value else "no"


_INSPECTION_CHECKPOINT_STATE_KEYS = frozenset(
    {
        "combat_pouch_potions",
        "verified_combat_pouch_potions",
    }
)


def _readiness_candidate_record(
    candidate: Any,
    *,
    level: int,
    output_ceiling: int,
    state: Mapping[str, Any],
    source_world: Any,
) -> dict[str, Any]:
    source_minimum, source_maximum = candidate.estimated_level_range
    hp_minimum, hp_maximum = candidate.estimated_base_hp_range
    in_band = _readiness_candidate_in_band(candidate, level)
    fame_window = _readiness_fame_window(
        candidate,
        level=level,
        source_world=source_world,
    )
    output_fit = bool(output_ceiling and hp_maximum > 0 and hp_maximum <= output_ceiling)
    protected_hp_probe = bool(
        _source_ranked_protected_hp_fuzz_probe_allowed(
            candidate,
            state,
            character_level=level,
            source_world=source_world,
        )
        or _source_ranked_protected_aggressive_hp_fuzz_probe_allowed(
            candidate,
            state,
            character_level=level,
            source_world=source_world,
        )
        or (
            source_maximum > level + 1
            and _source_ranked_protected_level_ceiling_hp_probe_allowed(
                candidate,
                state,
                character_level=level,
                source_world=source_world,
            )
        )
    )
    source_hp_admission: bool | None = None
    requires_sanctuary: bool | None = None
    sanctuary_available: bool | None = None
    admission_fit: bool | None = None
    campaign_rejections: list[str] = []
    useful_xp_probability: float | None = None
    try:
        source_policy_id = _source_ranked_policy_id(
            candidate,
            character_level=level,
        )
    except (AttributeError, TypeError, ValueError):
        source_policy_id = None
    protection = state.get(_PROTECTION_RECOVERY_KEY)
    if (
        source_policy_id is not None
        and isinstance(protection, Mapping)
        and protection.get("boot_id") == state.get("world_boot_id")
        and protection.get("level") in {None, level}
        and protection.get("policy_id") == source_policy_id
    ):
        try:
            loss = int(protection.get("xp_delta"))
        except (TypeError, ValueError):
            loss = 0
        campaign_rejections.append(
            (
                f"this exact source reset already caused a {abs(loss)} XP loss "
                "this reboot"
                if loss < 0
                else "this exact source reset has an active protection-recovery "
                "marker this reboot"
            )
        )
    if (
        isinstance(state.get("max_hp"), (int, float))
        and int(state.get("max_hp") or 0) > 0
        and source_world is not None
    ):
        try:
            source_hp_admission = bool(
                _source_ranked_hp_probe_admission_available(
                    candidate,
                    state,
                    character_level=level,
                    source_world=source_world,
                )
            )
            requires_sanctuary = bool(
                _source_ranked_candidate_requires_sanctuary_for_state(
                    candidate,
                    state,
                    character_level=level,
                    source_world=source_world,
                )
            )
            sanctuary_available = bool(_state_has_sanctuary_reserve(state))
            admission_fit = bool(
                candidate.autonomous_safe
                and in_band
                and source_hp_admission
                and (not requires_sanctuary or sanctuary_available)
            )
            useful_xp_probability = _source_ranked_useful_fuzz_probability(
                candidate,
                character_level=level,
            )
            if _source_ranked_candidate_excluded_by_below_band_evidence(
                candidate,
                state,
                character_level=level,
            ):
                campaign_rejections.append(
                    "live consider evidence says this target is below the useful XP band"
                )
            if (
                _source_ranked_plain_aggressive_target_invisibility_allowed(
                    candidate,
                    source_world,
                )
                and not _source_ranked_invisibility_route_candidate_allowed(
                    candidate,
                    state,
                    character_level=level,
                    source_world=source_world,
                )
                and not _source_ranked_familiar_probe_allowed(
                    candidate,
                    state,
                    character_level=level,
                    source_world=source_world,
                )
            ):
                campaign_rejections.append(
                    "aggressive target requires a practiced invisibility route or familiar"
                )
        except (AttributeError, TypeError, ValueError):
            # Synthetic fixture candidates intentionally exercise the report
            # without a complete source world. Keep those fields unknown
            # rather than turning an inspection-only command into a hard
            # failure.
            pass
    return {
        "target": candidate.target,
        "mobile_vnum": candidate.mobile_vnum,
        "room_vnum": candidate.room_vnum,
        "room": candidate.room_name,
        "source_policy_id": source_policy_id,
        "status": candidate.status,
        "score": candidate.score,
        "source_levels": [source_minimum, source_maximum],
        "base_hp": [hp_minimum, hp_maximum],
        "source_band": in_band,
        "fame_kind": fame_window[0] if fame_window is not None else None,
        "fame_window": (
            list(fame_window[1]) if fame_window is not None else None
        ),
        "autonomous_safe": candidate.autonomous_safe,
        "output_fit": output_fit,
        "source_hp_admission": source_hp_admission,
        "requires_sanctuary": requires_sanctuary,
        "sanctuary_available": sanctuary_available,
        "admission_fit": admission_fit,
        "source_gate_fit": admission_fit,
        "useful_xp_probability": useful_xp_probability,
        "campaign_rejections": campaign_rejections,
        "protected_hp_probe": protected_hp_probe,
        "estimated_peak_round_damage": candidate.estimated_peak_round_damage,
        "source_damage_modifier": getattr(candidate, "source_damage_modifier", 0),
        "estimated_move_cost": candidate.estimated_move_cost,
        "requires_flight": candidate.requires_flight,
        "loot": list(candidate.loot),
        "hazards": list(candidate.hazards),
        "autonomy_rejections": list(candidate.autonomy_rejections),
    }


def _readiness_gear_record(placement: Any) -> dict[str, Any]:
    source_minimum, source_maximum = placement.source_level_range
    return {
        "object_vnum": placement.object_vnum,
        "object": placement.object_description,
        "category": placement.category,
        "weapon_role": placement.weapon_role,
        "stance_rank": list(placement.stance_rank),
        "better_than_current": placement.better_than_current,
        "status": placement.status,
        "source_kind": placement.source_kind,
        "source_mobile_vnum": placement.source_mobile_vnum,
        "source_mobile": placement.source_mobile,
        "room_vnum": placement.room_vnum,
        "room": placement.room_name,
        "source_levels": [source_minimum, source_maximum],
        "route": list(placement.route),
        "requires_flight": placement.requires_flight,
        "hazards": list(placement.hazards),
        "autonomy_rejections": list(placement.autonomy_rejections),
    }


def _readiness_quest_record(
    state: Mapping[str, Any],
    *,
    level: int,
) -> dict[str, Any]:
    """Summarize quest request, progression gates, and fame consequences."""
    quest = snapshot_quest_status(
        state.get("quest_status")
        if isinstance(state.get("quest_status"), Mapping)
        else None
    )
    request_blocker = quest_request_blocker(state, quest=quest)
    required_points = quest_points_required_for_advance(level)
    return {
        "active": quest.active,
        "complete": quest.complete,
        "kind": quest.kind,
        "countdown": quest.countdown,
        "nextquest": quest.nextquest,
        "quest_points": quest.points,
        "total_quest_points": quest.total_points,
        "level_gate_required_points": required_points,
        "level_gate_shortfall": quest_points_shortfall_for_advance(
            level,
            quest.total_points,
        ),
        "target": {
            "mob_vnum": quest.mob_vnum,
            "object_vnum": quest.object_vnum,
            "room_vnum": quest.room_vnum,
            "name": quest.target_name,
            "area": quest.area_name,
        },
        "questmaster": questmaster_name_for_level(level),
        "questmaster_route": list(questmaster_route_for_level(level)),
        "fame_gate_allowed": quest_request_fame_allowed(state),
        "request_allowed": request_blocker is None,
        "request_blocker": request_blocker,
        "fame_recovery_status": quest_fame_recovery_status(
            state,
            quest=quest,
        ),
    }


def _readiness_active_constraints(state: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Summarize durable gates without copying the entire checkpoint."""
    labels = (
        ("campaign_protection_recovery_required", "protection recovery"),
        ("campaign_provision_funding_required", "provision funding"),
        ("campaign_flight_funding_required", "flight funding"),
        ("campaign_source_ranked_xp_loss_policies", "recorded XP-loss policies"),
        ("campaign_below_band_policy_exclusions", "below-band exclusions"),
        (
            "campaign_source_ranked_combat_output_revalidation",
            "combat-output revalidation",
        ),
    )
    constraints: list[dict[str, Any]] = []
    for key, label in labels:
        value = state.get(key)
        if not value:
            continue
        record: dict[str, Any] = {"key": key, "label": label}
        if isinstance(value, Mapping):
            record["kind"] = "mapping"
            record["count"] = len(value)
            record["entries"] = sorted(str(entry) for entry in value)[:20]
        elif isinstance(value, (list, tuple, set, frozenset)):
            record["kind"] = "list"
            record["count"] = len(value)
        else:
            record["kind"] = "value"
            record["value"] = value
        constraints.append(record)
    fame = _inspection_fame(state)
    if fame is not None and fame < 0:
        constraints.append(
            {
                "key": "character_fame",
                "label": "negative fame blocks new quests and shops",
                "kind": "value",
                "value": fame,
            }
        )
    return constraints


def show_combat_readiness(
    source: Path,
    *,
    level: int,
    character_class: str,
    subclass: str | None,
    character: str,
    database: Path,
    limit: int,
    include_all_areas: bool = False,
    json_output: bool = False,
) -> int:
    """Render an offline combat/readiness audit without authorizing a run."""
    if level < 1 or level > 100:
        print("--level must be between 1 and 100", file=sys.stderr)
        return 2
    if limit < 1:
        print("--limit must be at least 1", file=sys.stderr)
        return 2
    try:
        world = load_world_source(
            source,
            include_all_areas=include_all_areas,
            include_all_objects=True,
        )
    except (OSError, ValueError) as exc:
        print(f"Unable to load DD4 source: {exc}", file=sys.stderr)
        return 1
    current_source_revision = _source_revision(source)

    state, boot_id, kill_counts = _load_inspection_state(database, character)
    report_state = dict(state)
    report_state["character_class"] = character_class
    if subclass is not None:
        report_state["subclass"] = subclass
    elif "subclass" not in report_state:
        report_state["subclass"] = "none"

    character_max_hp: int | None = None
    if state.get("level") == level:
        raw_max_hp = state.get("max_hp")
        if isinstance(raw_max_hp, (int, float)) and raw_max_hp > 0:
            character_max_hp = int(raw_max_hp)
    recall_origins = recall_origins_from_state(state)
    raw_known_skills = state.get("campaign_known_skills")
    if isinstance(raw_known_skills, str):
        known_skills: tuple[str, ...] = (raw_known_skills,)
    elif isinstance(raw_known_skills, (list, tuple, set, frozenset)):
        known_skills = tuple(str(skill) for skill in raw_known_skills)
    else:
        known_skills = ()
    raw_skill_levels = state.get("campaign_known_skill_levels")
    known_skill_levels = (
        raw_skill_levels if isinstance(raw_skill_levels, Mapping) else {}
    )
    character_alignment = _inspection_alignment(state)
    character_fame = _inspection_fame(state)
    quest_record = _readiness_quest_record(state, level=level)

    catalog = GearCatalog(getattr(world, "objects", {}))
    current_items = catalog.match_many_usable(
        [
            *(
                _equipment_descriptions(state.get("equipment"))
                or _inspection_state_descriptions(state.get("campaign_worn_equipment"))
            ),
            *_inventory_descriptions(state.get("inventory")),
        ],
        character_class=character_class,
        subclass=subclass or state.get("subclass"),
    )
    try:
        output = _source_ranked_caster_output_for_state(
            report_state,
            character_level=level,
            source_world=world,
        )
    except (TypeError, ValueError):
        output = None
    output_ceiling = 0
    output_record: dict[str, Any] | None = None
    if output is not None:
        output_ceiling = (
            int(output.conservative_damage) * int(output.maximum_actions)
            + int(output.opening_conservative_damage or 0)
        )
        output_record = {
            "action": output.action,
            "opening_action": output.opening_action,
            "minimum_damage": output.minimum_damage,
            "expected_damage": output.expected_damage,
            "maximum_damage": output.maximum_damage,
            "conservative_damage": output.conservative_damage,
            "maximum_actions": output.maximum_actions,
            "opening_conservative_damage": output.opening_conservative_damage,
            "total_conservative_ceiling": output_ceiling,
            "source_reference": output.source_reference,
            "opening_source_reference": output.opening_source_reference,
        }

    try:
        candidates = rank_hunt_candidates(
            world,
            character_level=level,
            character_class=character_class,
            character_subclass=subclass or state.get("subclass"),
            known_skills=known_skills,
            known_skill_levels=known_skill_levels,
            boot_kill_counts=kill_counts,
            include_xp_only=True,
            include_below_band=True,
            character_max_hp=character_max_hp,
            include_level_ceiling_candidates=character_max_hp is not None,
            level_ceiling_offset=(
                _FAME_RECOVERY_MAX_LEVEL_DELTA
                if character_max_hp is not None
                else 1
            ),
            include_all_areas=include_all_areas,
            recall_origins=recall_origins,
            character_alignment=character_alignment,
        )
        placements = rank_gear_sources(
            world,
            character_level=level,
            character_class=character_class,
            subclass=subclass or state.get("subclass"),
            stance=STANCE_COMBAT,
            current_items=current_items,
            character_max_hp=character_max_hp,
            include_all_areas=include_all_areas,
            recall_origins=recall_origins,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    candidate_records = [
        _readiness_candidate_record(
            candidate,
            level=level,
            output_ceiling=output_ceiling,
            state=report_state,
            source_world=world,
        )
        for candidate in candidates
    ]
    candidate_records.sort(
        key=lambda record: (
            record["source_band"],
            record["autonomous_safe"],
            record["output_fit"],
            record["score"],
        ),
        reverse=True,
    )
    fame_records = [
        record
        for record in candidate_records
        if record["fame_window"] is not None
    ]
    fame_records.sort(
        key=lambda record: (
            record["autonomous_safe"],
            record["output_fit"],
            record["protected_hp_probe"],
            record["score"],
        ),
        reverse=True,
    )
    fame_summary = {
        "ordinary_minimum_level_delta": _FAME_RECOVERY_MIN_LEVEL_DELTA,
        "ordinary_maximum_level_delta": None,
        "research_horizon_maximum_level_delta": _FAME_RECOVERY_MAX_LEVEL_DELTA,
        "ordinary_level_rule": (
            "victim level - character level > 5 (at least 6 levels higher)"
        ),
        "ordinary_level_range": _readiness_level_range(
            level + _FAME_RECOVERY_MIN_LEVEL_DELTA,
            100,
        ),
        "famous_level_rule": "ACT_IS_FAMOUS victim is less than 10 levels below",
        "famous_level_range": _readiness_level_range(
            level - 4,
            100,
        ),
        "candidate_count": len(fame_records),
        "ordinary_candidates": sum(
            record["fame_kind"] == "ordinary" for record in fame_records
        ),
        "famous_candidates": sum(
            record["fame_kind"] == "famous" for record in fame_records
        ),
        "autonomous_safe": sum(
            bool(record["autonomous_safe"]) for record in fame_records
        ),
        "output_fit": sum(
            bool(record["output_fit"]) for record in fame_records
        ),
        "safe_and_output_fit": sum(
            bool(record["autonomous_safe"])
            and bool(record["output_fit"])
            for record in fame_records
        ),
        "admission_fit": sum(
            bool(record["admission_fit"]) for record in fame_records
        ),
        "targets": fame_records[:limit],
    }
    better_placements = [
        placement for placement in placements if placement.better_than_current
    ]
    report = {
        "source": str(source.resolve()),
        "source_revision": (
            current_source_revision
            or state.get("campaign_source_revision")
            or "unknown"
        ),
        "character": character,
        "level": level,
        "character_class": character_class,
        "subclass": subclass or state.get("subclass") or "none",
        "database": str(database.resolve()),
        "boot_id": boot_id or "unknown",
        "character_max_hp": character_max_hp,
        "character_alignment": character_alignment,
        "character_fame": character_fame,
        "quest": quest_record,
        "observed_equipment_count": len(current_items),
        "active_constraints": _readiness_active_constraints(state),
        "output": output_record,
        "target_summary": {
            "total": len(candidate_records),
            "source_band": sum(
                bool(record["source_band"]) for record in candidate_records
            ),
            "autonomous_safe": sum(
                bool(record["autonomous_safe"]) for record in candidate_records
            ),
            "output_fit": sum(
                bool(record["output_fit"]) for record in candidate_records
            ),
            "protected_hp_probes": sum(
                bool(record["protected_hp_probe"])
                for record in candidate_records
            ),
            "safe_and_output_fit": sum(
                bool(record["source_band"])
                and bool(record["autonomous_safe"])
                and bool(record["output_fit"])
                for record in candidate_records
            ),
            "admission_fit": sum(
                bool(record["admission_fit"]) for record in candidate_records
            ),
            "source_gate_fit": sum(
                bool(record["source_gate_fit"]) for record in candidate_records
            ),
        },
        "fame_summary": fame_summary,
        "targets": candidate_records[:limit],
        "gear_summary": {
            "total_placements": len(placements),
            "better_than_current": len(better_placements),
        },
        "gear_upgrades": [
            _readiness_gear_record(placement)
            for placement in better_placements[:limit]
        ],
        "live_authorization": False,
    }
    if json_output:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    print("Combat readiness: offline source audit")
    print(f"Source: {report['source']}")
    print(
        f"Character: {character}, level {level}, class {character_class}, "
        f"subclass {report['subclass']}"
    )
    print(f"Source revision: {report['source_revision']}")
    print(f"Current reboot: {report['boot_id']}")
    print(f"Character max HP: {character_max_hp or 'unknown'}")
    print(
        "Player alignment: "
        + (
            str(character_alignment)
            if character_alignment is not None
            else "unknown"
        )
    )
    print(
        "Player fame: "
        + (str(character_fame) if character_fame is not None else "unknown")
    )
    print(
        "Quest request: "
        + (
            f"available via {quest_record['questmaster']}"
            if quest_record["request_allowed"]
            else f"blocked ({quest_record['request_blocker']})"
        )
    )
    print(
        "Quest points: "
        f"{quest_record['total_quest_points']} total; "
        f"next level gate shortfall {quest_record['level_gate_shortfall']}"
    )
    print(f"Quest fame path: {quest_record['fame_recovery_status']}")
    if report["active_constraints"]:
        print(
            "Durable constraints: "
            + ", ".join(
                f"{constraint['label']}"
                + (
                    f" ({constraint['count']})"
                    if "count" in constraint
                    else ""
                )
                for constraint in report["active_constraints"]
            )
        )
    else:
        print("Durable constraints: none recorded")
    if output_record is None:
        print("Output: unassessed (no source-backed repeatable action)")
    else:
        print(
            f"Output: {output_record['action']} at "
            f"{output_record['conservative_damage']} damage x "
            f"{output_record['maximum_actions']} actions; "
            f"total ceiling {output_ceiling}"
        )
        if output_record["opening_action"]:
            print(
                f"Opening: {output_record['opening_action']} at "
                f"{output_record['opening_conservative_damage']} conservative damage"
            )
    summary = report["target_summary"]
    print(
        "Targets: "
        f"{summary['total']} total, {summary['source_band']} source-band, "
        f"{summary['autonomous_safe']} autonomous-safe, "
        f"{summary['output_fit']} output-fit, "
        f"{summary['protected_hp_probes']} protected HP probes, "
        f"{summary['source_gate_fit']} source-gate-fit"
    )
    print(
        "This source shortlist does not include live route checks or all "
        "same-boot target history."
    )
    fame = report["fame_summary"]
    print(
        "Fame bands: ordinary "
        f"{_format_readiness_level_range(fame['ordinary_level_range'])}; "
        "famous "
        f"{_format_readiness_level_range(fame['famous_level_range'])}; "
        f"{fame['candidate_count']} source candidates"
    )
    print(
        "Fame research horizon: "
        f"+{fame['research_horizon_maximum_level_delta']} levels"
    )
    print(f"Fame rule: ordinary targets require {fame['ordinary_level_rule']}")
    print(
        "Fame candidates: "
        f"{fame['autonomous_safe']} autonomous-safe, "
        f"{fame['output_fit']} output-fit, "
        f"{fame['admission_fit']} source-gate-fit"
    )
    print(
        "target\troom\tlevels\tbase_hp\tstatus\tsafe\toutput_fit\t"
        "hp_admission\tsanctuary_required\tsanctuary_available\t"
        "source_gate_fit\tuseful_xp\tprotected_probe\trejections"
    )
    for record in report["targets"]:
        print(
            "\t".join(
                (
                    f"{record['mobile_vnum']} {record['target']}",
                    f"{record['room_vnum']} {record['room']}",
                    f"{record['source_levels'][0]}-{record['source_levels'][1]}",
                    f"{record['base_hp'][0]}-{record['base_hp'][1]}",
                    record["status"],
                    "yes" if record["autonomous_safe"] else "no",
                    "yes" if record["output_fit"] else "no",
                    _format_optional_bool(record["source_hp_admission"]),
                    _format_optional_bool(record["requires_sanctuary"]),
                    _format_optional_bool(record["sanctuary_available"]),
                    _format_optional_bool(record["source_gate_fit"]),
                    (
                        "unknown"
                        if record["useful_xp_probability"] is None
                        else f"{record['useful_xp_probability']:.0%}"
                    ),
                    "yes" if record["protected_hp_probe"] else "no",
                    "; ".join(
                        (*record["autonomy_rejections"], *record["campaign_rejections"])
                    ) or "-",
                )
            )
        )
    print(f"Gear upgrades: {len(better_placements)} better placements")
    if better_placements:
        print("object\tcategory\tstatus\tsource\troom\trejections")
        for record in report["gear_upgrades"]:
            source_mobile = (
                f"{record['source_mobile_vnum']} {record['source_mobile']}"
                if record["source_mobile_vnum"] is not None
                else record["source_kind"]
            )
            print(
                "\t".join(
                    (
                        f"{record['object_vnum']} {record['object']}",
                        record["category"],
                        record["status"],
                        source_mobile,
                        f"{record['room_vnum']} {record['room']}",
                        "; ".join(record["autonomy_rejections"]) or "-",
                    )
                )
            )
    print("Live authorization: no; this command only reports evidence and blockers.")
    return 0


def show_transcript(target: str, *, database: Path, raw: bool) -> int:
    transcript_path = _resolve_transcript_target(target, database)
    if transcript_path is None:
        return 1
    if not transcript_path.exists():
        print(f"No transcript found at {transcript_path.resolve()}", file=sys.stderr)
        return 1

    if not raw:
        print(f"Transcript: {transcript_path.resolve()}")
    with transcript_path.open(encoding="utf-8") as transcript:
        for line in transcript:
            if raw:
                print(line.rstrip())
                continue
            event = json.loads(line)
            payload = json.dumps(event.get("payload", {}), sort_keys=True)
            print(f"{event.get('timestamp', '-')}\t{event.get('kind', '-')}\t{payload}")
    return 0


def show_state(run_id: int, *, database: Path, history: bool) -> int:
    if run_id < 1:
        print("run_id must be at least 1", file=sys.stderr)
        return 2
    if not database.exists():
        print(f"No run database found at {database.resolve()}", file=sys.stderr)
        return 1

    with RunStorage(database, read_only=True) as storage:
        run = storage.get_run(run_id)
        snapshots = (
            storage.list_state_snapshots(run_id)
            if history
            else [storage.get_latest_state_snapshot(run_id)]
        )

    if run is None:
        print(f"No run with id {run_id} in {database.resolve()}", file=sys.stderr)
        return 1

    available = [snapshot for snapshot in snapshots if snapshot is not None]
    if not available:
        print(f"Run {run_id} has no character state snapshots.", file=sys.stderr)
        return 1

    print(f"Database: {database.resolve()}")
    if not history:
        snapshot = available[0]
        print(
            f"Run {run_id} state revision "
            f"{json.loads(snapshot['state_json'])['revision']} "
            f"at {snapshot['timestamp']} ({snapshot['reason']})"
        )
        print(json.dumps(json.loads(snapshot["state_json"]), indent=2, sort_keys=True))
        return 0

    print("snapshot\ttimestamp\trevision\treason\tlevel\thp\troom")
    for snapshot in available:
        state = json.loads(snapshot["state_json"])
        print(
            "\t".join(
                [
                    str(snapshot["id"]),
                    snapshot["timestamp"],
                    str(state["revision"]),
                    snapshot["reason"],
                    str(state.get("level") or "-"),
                    _resource(state.get("hp"), state.get("max_hp")),
                    state.get("room_name") or "-",
                ]
            )
        )
    return 0


def show_report(
    run_id: int,
    *,
    database: Path,
    report_format: str,
    output: Path | None,
    commentary_limit: int,
) -> int:
    if run_id < 1:
        print("run_id must be at least 1", file=sys.stderr)
        return 2
    if commentary_limit < 1:
        print("--commentary-limit must be at least 1", file=sys.stderr)
        return 2
    if not database.exists():
        print(f"No run database found at {database.resolve()}", file=sys.stderr)
        return 1

    try:
        with RunStorage(database, read_only=True) as storage:
            report = build_run_report(
                storage,
                run_id,
                commentary_limit=commentary_limit,
            )
    except LookupError:
        print(f"No run with id {run_id} in {database.resolve()}", file=sys.stderr)
        return 1

    rendered = render_json(report) if report_format == "json" else render_markdown(report)
    if output is None:
        print(rendered, end="")
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(f"Report: {output.resolve()}")
    return 0


def show_campaign_report(
    campaign_id: int,
    *,
    database: Path,
    report_format: str,
    output: Path | None,
    commentary_limit: int,
) -> int:
    if campaign_id < 1:
        print("campaign_id must be at least 1", file=sys.stderr)
        return 2
    if commentary_limit < 1:
        print("--commentary-limit must be at least 1", file=sys.stderr)
        return 2
    if not database.exists():
        print(f"No run database found at {database.resolve()}", file=sys.stderr)
        return 1

    try:
        with RunStorage(database, read_only=True) as storage:
            report = build_campaign_report(
                storage,
                campaign_id,
                commentary_limit=commentary_limit,
            )
    except LookupError:
        print(
            f"No campaign with id {campaign_id} in {database.resolve()}",
            file=sys.stderr,
        )
        return 1

    rendered = (
        render_json(report)
        if report_format == "json"
        else render_campaign_markdown(report)
    )
    if output is None:
        print(rendered, end="")
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(f"Campaign report: {output.resolve()}")
    return 0


def show_campaign(campaign_id: int, *, database: Path, limit: int = 20) -> int:
    if campaign_id < 1:
        print("campaign_id must be at least 1", file=sys.stderr)
        return 2
    if limit < 1:
        print("--limit must be at least 1", file=sys.stderr)
        return 2
    if not database.exists():
        print(f"No run database found at {database.resolve()}", file=sys.stderr)
        return 1

    with RunStorage(database, read_only=True) as storage:
        campaign = storage.get_campaign(campaign_id)
        segments = storage.list_recent_campaign_segments(
            campaign_id,
            limit=limit,
        )
        checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)

    if campaign is None:
        print(f"No campaign with id {campaign_id} in {database.resolve()}", file=sys.stderr)
        return 1

    print(f"Database: {database.resolve()}")
    print(f"Campaign {campaign['id']}: {campaign['name']}")
    print(f"Status: {campaign['status']}")
    print(f"Target level: {campaign['target_level']}")
    print(f"Profile: {campaign['character_profile_path']}")
    if campaign["error"]:
        print(f"Reason: {campaign['error']}")
    if checkpoint is not None:
        state = json.loads(checkpoint["state_json"])
        print(
            f"Checkpoint {checkpoint['id']}: {checkpoint['phase']} "
            f"({checkpoint['reason']}), level {state.get('level', '-')}"
        )
        diagnosis = state.get("campaign_source_ranked_frontier_diagnosis")
        if isinstance(diagnosis, Mapping):
            print(
                "Frontier diagnosis: "
                f"{diagnosis.get('reason', 'unavailable')} "
                f"(boot {diagnosis.get('boot_id', '-')})"
            )
            print(
                "Frontier counts: "
                f"candidates={diagnosis.get('candidate_count', 0)} "
                f"current-band={diagnosis.get('current_band_count', 0)} "
                f"autonomous-safe={diagnosis.get('autonomous_safe_count', 0)} "
                f"sanctuary-required={diagnosis.get('sanctuary_required_count', 0)} "
                f"no-sanctuary={diagnosis.get('no_sanctuary_count', 0)} "
                f"below-band={diagnosis.get('same_boot_below_band_count', 0)}"
            )
            blockers = diagnosis.get("top_blockers")
            if isinstance(blockers, list):
                rendered_blockers = [
                    f"{item.get('reason')}: {item.get('count')}"
                    for item in blockers
                    if isinstance(item, Mapping)
                ]
                if rendered_blockers:
                    print("Frontier blockers: " + "; ".join(rendered_blockers))
            no_sanctuary_candidates = diagnosis.get("no_sanctuary_candidates")
            if isinstance(no_sanctuary_candidates, list) and no_sanctuary_candidates:
                print("No-sanctuary frontier options (diagnostic only):")
                for candidate in no_sanctuary_candidates:
                    if not isinstance(candidate, Mapping):
                        continue
                    levels = candidate.get("level_range", ())
                    level_text = (
                        f"{levels[0]}-{levels[1]}"
                        if isinstance(levels, (list, tuple)) and len(levels) == 2
                        else "unknown level"
                    )
                    print(
                        "  "
                        f"{candidate.get('target', 'unknown target')} "
                        f"[{candidate.get('mobile_vnum', '-')}] at "
                        f"{candidate.get('room_name', 'unknown room')} "
                        f"({candidate.get('area_file', '-')}:"
                        f"{candidate.get('room_vnum', '-')}); "
                        f"levels {level_text}; "
                        f"pool={candidate.get('selection_pool', 'unknown')}; "
                        f"policy={candidate.get('policy_id', '-')}"
                    )
                    policy_id = str(candidate.get("policy_id") or "")
                    same_boot_status = candidate.get("same_boot_status")
                    raw_blockers = candidate.get("same_boot_blockers")
                    same_boot_blockers = (
                        [str(item) for item in raw_blockers if item]
                        if isinstance(raw_blockers, list)
                        else []
                    )
                    current_boot = state.get("world_boot_id")
                    if (
                        policy_id
                        and current_boot
                        and state.get(_SOURCE_RANKED_RETRY_EXHAUSTED_KEY)
                        == policy_id
                        and state.get(_SOURCE_RANKED_RETRY_EXHAUSTED_BOOT_KEY)
                        == current_boot
                    ):
                        same_boot_blockers.append(
                            "nonproductive retry exhausted for this boot"
                        )
                    below_band_exclusions = state.get(
                        _BELOW_BAND_POLICY_EXCLUSIONS_KEY
                    )
                    below_band_exclusion = (
                        below_band_exclusions.get(policy_id)
                        if isinstance(below_band_exclusions, Mapping)
                        else None
                    )
                    if (
                        isinstance(below_band_exclusion, Mapping)
                        and below_band_exclusion.get("boot_id") == current_boot
                        and below_band_exclusion.get("level")
                        in {None, state.get("level")}
                    ):
                        same_boot_blockers.append(
                            "live below-band evidence for this reset"
                        )
                    timeout_records = state.get(
                        _SOURCE_RANKED_TIMEOUT_POLICIES_KEY
                    )
                    if isinstance(timeout_records, list):
                        for record in timeout_records:
                            if not isinstance(record, Mapping):
                                continue
                            try:
                                timeout_attempts = int(
                                    record.get("revalidation_attempts") or 0
                                )
                            except (TypeError, ValueError):
                                timeout_attempts = 0
                            if (
                                record.get("boot_id") == current_boot
                                and record.get("level")
                                in {None, state.get("level")}
                                and record.get("policy_id") == policy_id
                                and (
                                    record.get(
                                        _SOURCE_RANKED_TIMEOUT_REVALIDATION_FIELD
                                    ) is True
                                    or timeout_attempts
                                    >= _SOURCE_RANKED_TIMEOUT_REVALIDATION_MAX_ATTEMPTS
                                )
                            ):
                                same_boot_blockers.append(
                                    "timeout revalidation already used"
                                )
                    last_result = ""
                    research_results = state.get("campaign_research_results")
                    result = (
                        research_results.get(policy_id)
                        if isinstance(research_results, Mapping)
                        else None
                    )
                    if (
                        isinstance(result, Mapping)
                        and result.get("boot_id") == current_boot
                    ):
                        if result.get("consider_viable") is False:
                            same_boot_blockers.append(
                                "live consider is not XP-viable"
                            )
                        if result.get("route_hazard"):
                            last_result = str(result["route_hazard"])
                        elif result.get("absent") is True:
                            last_result = "target was absent"
                    same_boot_blockers = list(dict.fromkeys(same_boot_blockers))
                    history_parts = []
                    if same_boot_status:
                        history_parts.append(f"status={same_boot_status}")
                    if last_result:
                        history_parts.append(f"last result={last_result}")
                    if same_boot_blockers:
                        history_parts.append(
                            "blocked=" + "; ".join(same_boot_blockers)
                        )
                    if history_parts:
                        print(
                            "    same-boot history: "
                            + "; ".join(history_parts)
                        )
    print(
        f"recent segments (up to {limit}; newest segment last)"
    )
    print("sequence\tphase\tstatus\trun\tcommands\tduration\terror")
    for segment in segments:
        print(
            "\t".join(
                [
                    str(segment["sequence"]),
                    segment["phase"],
                    segment["status"],
                    str(segment["run_id"] or "-"),
                    str(segment["command_count"] or 0),
                    _duration(segment["duration_seconds"]),
                    segment["error"] or "-",
                ]
            )
        )
    return 0


def show_policies(level: int, character_class: str) -> int:
    if level < 0 or level > 100:
        print("--level must be between 0 and 100", file=sys.stderr)
        return 2
    try:
        policy = policy_for(level, character_class)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2

    print(f"Policy: {policy.policy_id}")
    print(f"Level band: {policy.minimum_level}-{policy.maximum_level or 100}")
    print(f"Status: {policy.status}")
    print(f"Summary: {policy.summary}")
    print(f"Practice candidate: {policy.practice_skill or '-'}")
    print("Evidence:")
    if policy.evidence:
        for item in policy.evidence:
            print(f"- {item}")
    else:
        print("- None recorded.")
    return 0


def show_policy_coverage(
    character_class: str,
    *,
    from_level: int = 0,
    to_level: int = 100,
) -> int:
    """Print contiguous policy selections to make coverage gaps explicit."""
    if from_level < 0 or to_level > 100 or from_level > to_level:
        print("level range must be between 0 and 100", file=sys.stderr)
        return 2
    try:
        selections = [
            (level, policy_for(level, character_class))
            for level in range(from_level, to_level + 1)
        ]
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2

    print(f"Class: {character_class}")
    print("levels\tpolicy\tstatus\texecution")
    start, current = selections[0]
    for level, policy in selections[1:]:
        if (
            policy.policy_id,
            policy.status,
            policy.execution,
        ) == (
            current.policy_id,
            current.status,
            current.execution,
        ):
            continue
        _print_policy_coverage_row(start, level - 1, current)
        start, current = level, policy
    _print_policy_coverage_row(start, to_level, current)
    return 0


def _print_policy_coverage_row(start: int, end: int, policy: Any) -> None:
    levels = str(start) if start == end else f"{start}-{end}"
    print(
        f"{levels}\t{policy.policy_id}\t{policy.status}\t"
        f"{policy.execution or '-'}"
    )


def show_prereqs(
    character_class: str,
    *,
    skill: str | None,
    snapshot: Path | None,
) -> int:
    try:
        source, entries = load_snapshot(snapshot)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"Could not load prerequisite snapshot: {exc}", file=sys.stderr)
        return 1

    class_skills = known_skills(entries, class_name=character_class)
    if not class_skills:
        print(f"No prerequisite definitions found for {character_class!r}.", file=sys.stderr)
        return 1

    print(f"Source: {source['repository']} @ {source['revision']}")
    if skill is None:
        print(f"Class: {character_class}")
        print(f"Skills with definitions: {len(class_skills)}")
        print("Skills: " + ", ".join(class_skills))
        return 0

    requirements = requirements_for_skill(
        entries,
        class_name=character_class,
        skill=skill,
    )
    if not requirements:
        print(
            f"No prerequisite definition found for {skill!r} in {character_class!r}.",
            file=sys.stderr,
        )
        return 1

    print(f"Class: {character_class}")
    print(f"Skill: {requirements[0].skill}")
    print("Requirements:")
    for requirement in requirements:
        print(f"- {requirement.prerequisite}: {requirement.minimum_percent}%")
    return 0


def show_skill_analysis(
    character_class: str,
    *,
    snapshot: Path | None,
) -> int:
    normalized_class = " ".join(
        character_class.casefold().replace("_", " ").split()
    )
    priorities = (
        training_priorities().get(normalized_class)
        or subclass_training_priorities().get(normalized_class)
    )
    if not priorities:
        print(
            f"No training analysis found for {character_class!r}.",
            file=sys.stderr,
        )
        return 1
    analysis = training_analysis_for(normalized_class)
    if analysis is None:
        print(
            f"No training analysis found for {character_class!r}.",
            file=sys.stderr,
        )
        return 1
    try:
        source, entries = load_snapshot(snapshot)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"Could not load prerequisite snapshot: {exc}", file=sys.stderr)
        return 1

    print(f"Source: {source['repository']} @ {source['revision']}")
    print(f"Class: {normalized_class}")
    print(f"Strategy: {analysis.strategy}")
    print(f"Practice policy: {analysis.practice_policy}")
    print(
        "Highest leveling value: "
        + ", ".join(analysis.highest_value_skills)
    )
    if analysis.automation_gaps:
        print("Automation gaps:")
        for gap in analysis.automation_gaps:
            print(f"- {gap}")
    print("Ordered leveling priorities:")
    for rank, priority in enumerate(priorities, start=1):
        requirements = ()
        for source_class in prerequisite_classes_for(normalized_class):
            requirements = requirements_for_skill(
                entries,
                class_name=source_class,
                skill=priority.source_skill,
            )
            if requirements:
                break
        requirement_text = ", ".join(
            f"{item.prerequisite} {item.minimum_percent}%"
            for item in requirements
        )
        print(
            f"{rank}. {priority.skill} [{priority.practice_type}, "
            f"target {priority.target_percent}%, {priority.utility}, "
            f"{'automated' if priority.automated else 'analysis-only'}]"
        )
        print(f"   Value: {priority.reason}")
        print(f"   Prerequisites: {requirement_text or 'none parsed'}")
    return 0


def collect_evidence(run_id: int, *, database: Path, output: Path | None) -> int:
    if run_id < 1:
        print("run_id must be at least 1", file=sys.stderr)
        return 2
    if not database.exists():
        print(f"No run database found at {database.resolve()}", file=sys.stderr)
        return 1
    try:
        with RunStorage(database, read_only=True) as storage:
            rendered = render_evidence_json(collect_run_evidence(storage, run_id))
    except LookupError:
        print(f"No run with id {run_id} in {database.resolve()}", file=sys.stderr)
        return 1

    if output is None:
        print(rendered, end="")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(f"Evidence: {output.resolve()}")
    return 0


def _resolve_transcript_target(target: str, database: Path) -> Path | None:
    if not target.isdigit():
        return Path(target)

    if not database.exists():
        print(f"No run database found at {database.resolve()}", file=sys.stderr)
        return None

    run_id = int(target)
    with RunStorage(database, read_only=True) as storage:
        run = storage.get_run(run_id)

    if run is None:
        print(f"No run with id {run_id} in {database.resolve()}", file=sys.stderr)
        return None
    if not run["transcript_path"]:
        print(f"Run {run_id} has no transcript path recorded", file=sys.stderr)
        return None
    return Path(run["transcript_path"])


def _resource(current: Any, maximum: Any) -> str:
    if current is None:
        return "-"
    if maximum is None:
        return str(current)
    return f"{current}/{maximum}"


def _duration(value: float | None) -> str:
    return "-" if value is None else f"{value:g}s"
