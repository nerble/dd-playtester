from __future__ import annotations

import asyncio
import json
import re
from collections import Counter
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Collection, Mapping

from .character import CharacterSpec, load_character_spec
from .equipment import (
    GearCatalog,
    character_can_use_item,
    is_capacity_infrastructure,
    is_blunt_weapon,
    is_disposable_food,
    is_piercing_weapon,
    item_category,
    item_keyword,
    load_gear_catalog,
    normalize_item_name,
    protects_from_sale,
    weapon_damage_score,
)
from .fastwalks import Fastwalk, route_named
from .hunt_candidates import HuntCandidate, load_world_source, rank_hunt_candidates
from .progression import (
    ProgressionPolicy,
    _SOURCE_RANKED_HUNT_POLICY,
    policy_for,
)
from .runner import RunResult
from .scenario import load_yaml_mapping
from .shops import safe_shop_for_item
from .starter import (
    FieldHuntStop,
    StarterBotRunner,
    _equipment_audit_descriptions,
    _equipment_audit_present,
    _equipment_empty_categories,
    _equipment_weapon_slot,
    _inventory_descriptions,
    _emergency_provision_potion_keyword,
    _sellable_inventory_keyword,
    ambush_archer_hunt_stops,
    ambush_archer_research_stops,
    ambush_bardoosh_hunt_stops,
    ambush_caster_level_eight_hunt_stops,
    ambush_level_eight_hunt_stops,
    ambush_martial_level_eight_hunt_stops,
    ambush_raider_hunt_stops,
    ambush_vile_goblin_hunt_stops,
    ambush_war_dog_collar_hunt_stops,
    argent_bandit_leader_hunt_stops,
    argent_bandit_leader_research_stops,
    circus_freak_show_hunt_stops,
    cult_fanatic_research_stops,
    daycare_armed_guard_hunt_stops,
    daycare_armed_guard_hunt_route,
    daycare_nanny_hunt_route,
    daycare_nanny_hunt_stops,
    daycare_ring_hunt_route,
    daycare_ring_hunt_stops,
    crystalmir_white_stag_hunt_stops,
    crystalmir_white_stag_research_stops,
    darkwood_strange_mist_hunt_stops,
    darkwood_strange_mist_research_stops,
    dwarven_nobleman_hunt_stops,
    dwarven_nobleman_research_stops,
    dwarven_home_chess_dwarf_hunt_stops,
    dwarven_home_chess_dwarf_research_stops,
    dwarven_home_gambler_hunt_stops,
    dwarven_home_gambler_research_stops,
    dwarven_home_master_hunt_stops,
    dwarven_home_master_research_stops,
    dwarven_servant_hunt_stops,
    dwarven_servant_research_stops,
    dwarven_worker_research_stops,
    foundry_body_gear_hunt_stops,
    foundry_set_circlet_hunt_stops,
    foundry_level_six_hunt_stops,
    foundry_level_seven_hunt_stops,
    forest_bear_claws_hunt_route,
    forest_bear_claws_hunt_stops,
    galaxy_cancer_research_stops,
    galaxy_horsehead_nebula_hunt_stops,
    galaxy_horsehead_nebula_research_stops,
    galaxy_red_supergiant_hunt_stops,
    galaxy_red_supergiant_research_stops,
    galaxy_white_dwarf_secondary_hunt_stops,
    galaxy_white_dwarf_secondary_research_stops,
    galaxy_white_dwarf_hunt_stops,
    galaxy_white_dwarf_research_stops,
    hightower_jailor_hunt_stops,
    hightower_jailor_research_stops,
    fleshmonger_cook_hunt_stops,
    fleshmonger_cook_research_stops,
    fleshmonger_guard_circuit_research_stops,
    fleshmonger_guard_hunt_stops,
    fleshmonger_guard_research_stops,
    fleshmonger_mufti_research_stops,
    fleshmonger_servant_hunt_stops,
    fleshmonger_servant_research_stops,
    fleshmonger_thief_extended_rotation_stops,
    fleshmonger_thief_rotation_research_stops,
    gnome_hermit_hunt_route,
    gnome_hermit_hunt_stops,
    gnome_guard_hunt_stops,
    gnome_guard_research_stops,
    gnome_small_troll_hunt_stops,
    gnome_treasurer_hunt_stops,
    gnome_treasurer_research_stops,
    ghost_town_crypt_thing_hunt_stops,
    ghost_town_crypt_thing_research_stops,
    ghost_town_retriever_hunt_stops,
    ghost_town_retriever_research_stops,
    highland_keeper_hunt_stops,
    highland_keeper_research_stops,
    gremlin_waist_hunt_route,
    gremlin_waist_hunt_stops,
    mahntor_rock_toad_hunt_stops,
    mahntor_rock_toad_circuit_hunt_stops,
    mahntor_rock_toad_research_stops,
    midennir_mountain_goblin_hunt_stops,
    minotaur_gatekeeper_hunt_stops,
    minotaur_gatekeeper_research_stops,
    mirror_realm_gardener_research_stops,
    mirror_realm_gardener_hunt_stops,
    mirror_realm_guardian_hunt_stops,
    mirror_realm_guardian_research_stops,
    mirror_realm_jerry_garcia_research_stops,
    mirror_realm_storn_hunt_stops,
    mirror_realm_storn_research_stops,
    mirror_realm_watchman_hunt_stops,
    mirror_realm_watchman_research_stops,
    pit_official_research_stops,
    moria_level_eight_large_orc_hunt_stops,
    moria_level_seven_orc_hunt_stops,
    moria_deep_sanctuary_potion_hunt_stops,
    moria_deep_sanctuary_potion_research_stops,
    moria_sanctuary_potion_hunt_stops,
    plains_aruncus_hunt_stops,
    plains_aruncus_research_stops,
    shire_bull_hunt_route,
    shire_bull_hunt_stops,
    school_accessory_hunt_route,
    school_wrist_float_hunt_stops,
    shadow_keep_soldier_hunt_stops,
    shadow_keep_soldier_research_stops,
    shire_battle_master_research_stops,
    shire_dwarven_prince_hunt_stops,
    shire_dwarven_prince_research_stops,
    shire_elven_wizard_hunt_stops,
    shire_elven_wizard_research_stops,
    shire_thain_hunt_stops,
    shire_thain_research_stops,
    pyramid_ali_baba_hunt_stops,
    pyramid_ali_baba_research_stops,
    pirates_seas_rastafarians_hunt_stops,
    pirates_seas_rastafarians_research_stops,
    solace_lord_doom_hunt_stops,
    solace_lord_doom_research_stops,
    solace_magnus_hunt_stops,
    solace_magnus_research_stops,
    thalos_long_dagger_hunt_route,
    thalos_long_dagger_hunt_stops,
    vampire_hive_wounded_vampire_hunt_stops,
    vampire_hive_wounded_vampire_research_stops,
    tabernacle_hulking_beast_hunt_stops,
    tabernacle_hulking_beast_research_stops,
)
from .storage import RunStorage


SegmentRunner = Callable[[CharacterSpec, Path], Awaitable[RunResult]]
_MAINTENANCE_EXECUTIONS = {
    "bank-excess-coins",
    "restock",
    "sell-loot",
    "vault-spare-gear",
    "rearm-weapon",
    "outfit-basic-gear",
    "recover-basic-body",
    "recover-school-wrist-float",
    "recover-gremlin-waist",
    "recover-daycare-ring",
    "recover-war-dog-collar",
    "recover-foundry-set-circlet",
    "upgrade-piercing-weapon",
    "buy-flight",
    "borrow-flight",
    "provision-funding",
}
_LIQUIDATION_BASELINE_KEY = "campaign_liquidation_baseline"
_PROVISION_FUNDING_REQUIRED_KEY = "campaign_provision_funding_required"
_PROVISION_FUNDING_ATTEMPTS_KEY = "campaign_provision_funding_attempts"
_PROVISION_FUNDING_LAST_ATTEMPT_KEY = "campaign_provision_funding_last_attempt"
_FLIGHT_FUNDING_REQUIRED_KEY = "campaign_flight_funding_required"
_FLIGHT_FUNDING_RETRY_KEY = "campaign_flight_funding_retry_pending"
_FLIGHT_PURCHASE_COOLDOWN_KEY = "campaign_flight_purchase_cooldown"
_FLIGHT_PURCHASE_COOLDOWN_SEGMENTS = 3
_SACK_VAULT_ITEMS_KEY = "campaign_sack_vault_items"
_SACK_VAULT_RECLAIM_LEVEL_KEY = "campaign_sack_vault_reclaim_attempted_level"
_CAMPAIGN_POLICY_REVISION = 111
_FIELD_CROWD_ABORT_PREFIXES = (
    "field room contained ",
    "field combat aborted after unapproved attacker ",
)
_DYNAMIC_FIELD_ROUTE_HAZARD_ABORT_REASON = (
    "unexpected combat interrupted a no-combat field probe"
)
_FIELD_ROUTE_HAZARD_ABORT_PREFIXES = (
    "field route preflight found source-registered hazard ",
    _DYNAMIC_FIELD_ROUTE_HAZARD_ABORT_REASON,
)
_BARDOOSH_POLICY_ID = "ambush-bardoosh-thief-kill-research-13"
_NOBLEMAN_POLICY_ID = "dwarven-nobleman-thief-probe-13-15"
_NOBLEMAN_LEVEL_SEVENTEEN_PROBE_POLICY_ID = (
    "dwarven-nobleman-thief-probe-17-18"
)
_NOBLEMAN_LEVEL_SEVENTEEN_HUNT_POLICY_ID = "dwarven-nobleman-thief-hunt-17-18"
_DWARVEN_WORKERS_POLICY_ID = "dwarven-workers-thief-probe-13-15"
_MIRROR_WATCHMAN_POLICY_ID = "mirror-realm-watchman-probe-16-20"
_MIRROR_WATCHMAN_LEVEL_NINETEEN_POLICY_ID = (
    "mirror-realm-watchman-probe-19-20"
)
_CRYSTALMIR_WHITE_STAG_POLICY_ID = "crystalmir-white-stag-probe-16-20"
_SHADOW_KEEP_SOLDIER_POLICY_ID = "shadow-keep-undead-soldier-probe-16-20"
_SHADOW_KEEP_SOLDIER_HUNT_POLICY_ID = "shadow-keep-undead-soldier-hunt-16-20"
_HIGHLAND_KEEPER_POLICY_ID = "highland-keeper-probe-17-20"
_HIGHLAND_KEEPER_HUNT_POLICY_ID = "highland-keeper-hunt-17-20"
_HIGHLAND_KEEPER_ROUTE_REPAIR_KEY = "campaign_highland_keeper_route_repair"
_HIGHLAND_KEEPER_IDENTITY_REPAIR_KEY = (
    "campaign_highland_keeper_identity_repair"
)
_HARD_ROUTE_HAZARD_REPAIR_KEY = "campaign_hard_route_hazard_repair"
_GALAXY_WHITE_DWARF_POLICY_ID = "galaxy-white-dwarf-probe-17-20"
_GALAXY_WHITE_DWARF_HUNT_POLICY_ID = "galaxy-white-dwarf-hunt-17-20"
_GALAXY_WHITE_DWARF_SECONDARY_POLICY_ID = (
    "galaxy-white-dwarf-secondary-probe-17-20"
)
_GALAXY_WHITE_DWARF_SECONDARY_HUNT_POLICY_ID = (
    "galaxy-white-dwarf-secondary-hunt-17-20"
)
_GALAXY_RED_SUPERGIANT_POLICY_ID = "galaxy-red-supergiant-probe-17-20"
_GALAXY_HORSEHEAD_NEBULA_POLICY_ID = "galaxy-horsehead-nebula-probe-18-20"
_GALAXY_HORSEHEAD_NEBULA_HUNT_POLICY_ID = "galaxy-horsehead-nebula-hunt-18-20"
_GALAXY_ROUTE_HAZARD_POLICY_IDS = frozenset(
    {
        _GALAXY_WHITE_DWARF_POLICY_ID,
        _GALAXY_WHITE_DWARF_HUNT_POLICY_ID,
        _GALAXY_WHITE_DWARF_SECONDARY_POLICY_ID,
        _GALAXY_WHITE_DWARF_SECONDARY_HUNT_POLICY_ID,
        _GALAXY_RED_SUPERGIANT_POLICY_ID,
        "galaxy-red-supergiant-hunt-17-20",
        _GALAXY_HORSEHEAD_NEBULA_POLICY_ID,
        _GALAXY_HORSEHEAD_NEBULA_HUNT_POLICY_ID,
    }
)
_SHIRE_DWARVEN_PRINCE_POLICY_ID = "shire-dwarven-prince-thief-probe-17-20"
_SHIRE_DWARVEN_PRINCE_HUNT_POLICY_ID = "shire-dwarven-prince-thief-hunt-17-20"
_SHIRE_THAIN_POLICY_ID = "shire-thain-probe-17-20"
_SHIRE_THAIN_HUNT_POLICY_ID = "shire-thain-hunt-17-20"
_ARGENT_BANDIT_LEADER_POLICY_ID = "argent-bandit-leader-probe-17-20"
_ARGENT_BANDIT_LEADER_LEVEL_NINETEEN_POLICY_ID = (
    "argent-bandit-leader-probe-19-20"
)
_ARGENT_BANDIT_LEADER_LEVEL_NINETEEN_HUNT_POLICY_ID = (
    "argent-bandit-leader-hunt-19-20"
)
_SHIRE_ELVEN_WIZARD_POLICY_ID = "shire-elven-wizard-probe-17-20"
_SHIRE_ELVEN_WIZARD_HUNT_POLICY_ID = "shire-elven-wizard-hunt-17-20"
_PYRAMID_ALI_BABA_POLICY_ID = "pyramid-ali-baba-probe-18-20"
_PYRAMID_ALI_BABA_HUNT_POLICY_ID = "pyramid-ali-baba-hunt-18-20"
_SOLACE_LORD_DOOM_POLICY_ID = "solace-lord-doom-probe-18-20"
_SOLACE_LORD_DOOM_HUNT_POLICY_ID = "solace-lord-doom-hunt-18-20"
_SOLACE_LORD_DOOM_SANCTUARY_HUNT_POLICY_ID = (
    "solace-lord-doom-sanctuary-hunt-18-20"
)
_SOLACE_MAGNUS_POLICY_ID = "solace-magnus-probe-19-20"
_SOLACE_MAGNUS_HUNT_POLICY_ID = "solace-magnus-hunt-19-20"
_PLAINS_ARUNCUS_THIEF_LEVEL_NINETEEN_POLICY_ID = (
    "plains-aruncus-thief-probe-19-20"
)
_PLAINS_ARUNCUS_THIEF_LEVEL_NINETEEN_HUNT_POLICY_ID = (
    "plains-aruncus-thief-hunt-19-20"
)
_SHIRE_DWARVEN_PRINCE_THIEF_LEVEL_NINETEEN_POLICY_ID = (
    "shire-dwarven-prince-thief-probe-19-20"
)
_SHIRE_DWARVEN_PRINCE_THIEF_LEVEL_NINETEEN_HUNT_POLICY_ID = (
    "shire-dwarven-prince-thief-hunt-19-20"
)
_MAHNTOR_ROCK_TOAD_CIRCUIT_POLICY_ID = (
    "mahntor-rock-toad-thief-circuit-16-18"
)
_MAHNTOR_ROCK_TOAD_HUNT_POLICY_ID = (
    "mahntor-rock-toad-thief-kill-research-14-15"
)
_BELOW_BAND_SIGHTINGS_KEY = "campaign_below_band_sightings"
_HIGHTOWER_JAILOR_POLICY_ID = "hightower-jailor-probe-17-20"
_HIGHTOWER_JAILOR_HUNT_POLICY_ID = "hightower-jailor-hunt-17-20"
_MORIA_SANCTUARY_THIEF_LEVEL_SEVENTEEN_POLICY_ID = (
    "moria-sanctuary-thief-17-20"
)
_MIRROR_REALM_GARDENER_POLICY_ID = "mirror-realm-gardener-probe-21-25"
_MORIA_LARGE_ORC_MAGE_RESEARCH_POLICY_ID = (
    "moria-large-orc-mage-research-10-11"
)
_DWARVEN_HOME_CHESS_DWARF_POLICY_ID = (
    "dwarven-home-chess-dwarf-probe-46-50"
)
_MIRROR_REALM_STORN_POLICY_ID = "mirror-realm-storn-probe-46-50"
_DARKWOOD_STRANGE_MIST_POLICY_ID = "darkwood-strange-mist-probe-51-55"
_DWARVEN_HOME_GAMBLER_POLICY_ID = "dwarven-home-gambler-probe-51-55"
_DWARVEN_HOME_MASTER_POLICY_ID = "dwarven-home-master-probe-56-60"
_VAMPIRE_HIVE_WOUNDED_VAMPIRE_POLICY_ID = (
    "vampire-hive-wounded-vampire-probe-61-65"
)
_TABERNACLE_HULKING_BEAST_POLICY_ID = "tabernacle-hulking-beast-probe-66-70"
_PIRATES_SEAS_RASTAFARIANS_POLICY_ID = (
    "pirates-seas-rastafarians-probe-71-75"
)
_GHOST_TOWN_CRYPT_THING_POLICY_ID = "ghost-town-crypt-thing-probe-76"
_GHOST_TOWN_RETRIEVER_POLICY_ID = "ghost-town-retriever-probe-77-80"
_RESEARCH_ABSENCE_COOLDOWN_KEY = "campaign_research_absence_cooldowns"
_RESEARCH_CROWD_COOLDOWN_KEY = "campaign_research_crowd_cooldowns"
_CLEARED_RESEARCH_POLICIES_KEY = "campaign_cleared_research_policies"
_DEFAULT_RESEARCH_CROWD_COOLDOWN = 3
_MORIA_DEEP_SANCTUARY_THIEF_PROBE_POLICY_ID = (
    "moria-deep-sanctuary-thief-probe-19-20"
)
_MORIA_DEEP_SANCTUARY_THIEF_HUNT_POLICY_ID = (
    "moria-deep-sanctuary-thief-hunt-19-20"
)
_MORIA_SANCTUARY_RESEARCH_POLICY_IDS = frozenset(
    {
        _MORIA_SANCTUARY_THIEF_LEVEL_SEVENTEEN_POLICY_ID,
        _MORIA_DEEP_SANCTUARY_THIEF_PROBE_POLICY_ID,
        _MORIA_DEEP_SANCTUARY_THIEF_HUNT_POLICY_ID,
    }
)
_LAST_PRODUCTIVE_POLICY_KEY = "campaign_last_productive_policy"
_PRODUCTIVE_POLICY_HISTORY_KEY = "campaign_productive_policy_history"
_POLICY_HANDOFF_KEY = "campaign_policy_handoff"
_SOURCE_RANKED_CANDIDATE_KEY = "campaign_source_ranked_hunt_candidate"
_SOURCE_RANKED_POLICY_PREFIX = "source-ranked-hunt-"
_PROTECTION_RECOVERY_KEY = "campaign_protection_recovery_required"
_RESEARCH_ABSENCE_RETRY_COOLDOWNS = {
    _MIRROR_WATCHMAN_LEVEL_NINETEEN_POLICY_ID: 3,
    _CRYSTALMIR_WHITE_STAG_POLICY_ID: 3,
    _SHADOW_KEEP_SOLDIER_POLICY_ID: 3,
    _SHADOW_KEEP_SOLDIER_HUNT_POLICY_ID: 3,
    _HIGHLAND_KEEPER_POLICY_ID: 3,
    _HIGHLAND_KEEPER_HUNT_POLICY_ID: 3,
    _GALAXY_WHITE_DWARF_POLICY_ID: 3,
    _GALAXY_WHITE_DWARF_SECONDARY_POLICY_ID: 3,
    _GALAXY_WHITE_DWARF_SECONDARY_HUNT_POLICY_ID: 3,
    _GALAXY_RED_SUPERGIANT_POLICY_ID: 3,
    "galaxy-red-supergiant-hunt-17-20": 3,
    _GALAXY_HORSEHEAD_NEBULA_POLICY_ID: 3,
    _GALAXY_HORSEHEAD_NEBULA_HUNT_POLICY_ID: 3,
    _HIGHTOWER_JAILOR_POLICY_ID: 3,
    _HIGHTOWER_JAILOR_HUNT_POLICY_ID: 3,
    _MORIA_SANCTUARY_THIEF_LEVEL_SEVENTEEN_POLICY_ID: 3,
    _MORIA_DEEP_SANCTUARY_THIEF_PROBE_POLICY_ID: 3,
    _MORIA_DEEP_SANCTUARY_THIEF_HUNT_POLICY_ID: 3,
    _NOBLEMAN_LEVEL_SEVENTEEN_HUNT_POLICY_ID: 3,
    _NOBLEMAN_LEVEL_SEVENTEEN_PROBE_POLICY_ID: 3,
    "dwarven-servant-thief-hunt-17-18": 3,
    _MIRROR_REALM_GARDENER_POLICY_ID: 3,
    _MORIA_LARGE_ORC_MAGE_RESEARCH_POLICY_ID: 1,
    _SHIRE_DWARVEN_PRINCE_POLICY_ID: 3,
    _SHIRE_DWARVEN_PRINCE_HUNT_POLICY_ID: 3,
    _SHIRE_THAIN_POLICY_ID: 3,
    _SHIRE_THAIN_HUNT_POLICY_ID: 3,
    _ARGENT_BANDIT_LEADER_POLICY_ID: 3,
    "argent-bandit-leader-hunt-17-20": 3,
    _ARGENT_BANDIT_LEADER_LEVEL_NINETEEN_POLICY_ID: 3,
    _ARGENT_BANDIT_LEADER_LEVEL_NINETEEN_HUNT_POLICY_ID: 3,
    _SHIRE_ELVEN_WIZARD_POLICY_ID: 3,
    _SHIRE_ELVEN_WIZARD_HUNT_POLICY_ID: 3,
    _PYRAMID_ALI_BABA_POLICY_ID: 3,
    _PYRAMID_ALI_BABA_HUNT_POLICY_ID: 3,
    _SOLACE_LORD_DOOM_POLICY_ID: 3,
    _SOLACE_LORD_DOOM_HUNT_POLICY_ID: 3,
    _SOLACE_MAGNUS_POLICY_ID: 3,
    _SOLACE_MAGNUS_HUNT_POLICY_ID: 3,
    _PLAINS_ARUNCUS_THIEF_LEVEL_NINETEEN_POLICY_ID: 3,
    _PLAINS_ARUNCUS_THIEF_LEVEL_NINETEEN_HUNT_POLICY_ID: 3,
    _SHIRE_DWARVEN_PRINCE_THIEF_LEVEL_NINETEEN_POLICY_ID: 3,
    _SHIRE_DWARVEN_PRINCE_THIEF_LEVEL_NINETEEN_HUNT_POLICY_ID: 3,
    _SOLACE_LORD_DOOM_SANCTUARY_HUNT_POLICY_ID: 3,
    _DWARVEN_HOME_CHESS_DWARF_POLICY_ID: 3,
    "dwarven-home-chess-dwarf-hunt-46-50": 3,
    _MIRROR_REALM_STORN_POLICY_ID: 3,
    "mirror-realm-storn-hunt-46-50": 3,
    _DARKWOOD_STRANGE_MIST_POLICY_ID: 3,
    "darkwood-strange-mist-hunt-51-55": 3,
    _DWARVEN_HOME_GAMBLER_POLICY_ID: 3,
    "dwarven-home-gambler-hunt-51-55": 3,
    _DWARVEN_HOME_MASTER_POLICY_ID: 3,
    "dwarven-home-master-hunt-56-60": 3,
    _VAMPIRE_HIVE_WOUNDED_VAMPIRE_POLICY_ID: 3,
    "vampire-hive-wounded-vampire-hunt-61-65": 3,
    _TABERNACLE_HULKING_BEAST_POLICY_ID: 3,
    "tabernacle-hulking-beast-hunt-66-70": 3,
    _PIRATES_SEAS_RASTAFARIANS_POLICY_ID: 3,
    "pirates-seas-rastafarians-hunt-71-75": 3,
    _GHOST_TOWN_CRYPT_THING_POLICY_ID: 3,
    "ghost-town-crypt-thing-hunt-76": 3,
    _GHOST_TOWN_RETRIEVER_POLICY_ID: 3,
    "ghost-town-retriever-hunt-77-80": 3,
}


def _is_research_absence_retry_policy(policy_id: str) -> bool:
    return (
        policy_id in _RESEARCH_ABSENCE_RETRY_COOLDOWNS
        or policy_id.startswith(_SOURCE_RANKED_POLICY_PREFIX)
    )


def _research_absence_retry_cooldown(
    policy_id: str,
    *,
    default: int | None = None,
) -> int | None:
    if policy_id in _RESEARCH_ABSENCE_RETRY_COOLDOWNS:
        return _RESEARCH_ABSENCE_RETRY_COOLDOWNS[policy_id]
    if policy_id.startswith(_SOURCE_RANKED_POLICY_PREFIX):
        return _DEFAULT_RESEARCH_CROWD_COOLDOWN
    return default


_BARDOOSH_ROUTE_FIX_RETRY_REASON = (
    "policy revision corrected the Bardoosh final route from south to west"
)
_BARDOOSH_IDENTITY_FIX_RETRY_REASON = (
    "policy revision bound Bardoosh's generic live line to his source identity"
)
_NOBLEMAN_ROUTE_FIX_RETRY_REASON = (
    "policy revision removed the redundant nobleman destination hop"
)
_NOBLEMAN_IDENTITY_FIX_RETRY_REASON = (
    "policy revision aligned the nobleman stop with its source identity"
)
_DWARVEN_WORKERS_SEARCH_FIX_RETRY_REASON = (
    "policy revision bound the worker survey to its exact source room line"
)
_MAHNTOR_ROUTE_ABORT_PREFIX = "field route could not find GMCP exit to room "
_ANSI_ESCAPE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
_RECOVER_BASIC_BODY_REQUIRED_FREE_WEIGHT = 7
_RECOVER_SCHOOL_WRIST_FLOAT_REQUIRED_FREE_WEIGHT = 30
_RECOVER_GREMLIN_WAIST_REQUIRED_FREE_WEIGHT = 5
_RECOVER_DAYCARE_RING_REQUIRED_FREE_WEIGHT = 21
_DAYCARE_RING_ATTEMPT_BOOT_KEY = "campaign_daycare_ring_attempted_boot_id"
_DAYCARE_RING_COOLDOWN_KEY = "campaign_daycare_ring_cooldown"
_DAYCARE_RING_COOLDOWN_SEGMENTS = 3
_RECOVER_WAR_DOG_COLLAR_REQUIRED_FREE_WEIGHT = 20
_RECOVER_FOUNDRY_SET_CIRCLET_REQUIRED_FREE_WEIGHT = 1
_FOUNDRY_SET_CIRCLET_ATTEMPTED_LEVEL_KEY = (
    "campaign_foundry_set_circlet_attempted_level"
)
_WAR_DOG_COLLAR_ATTEMPT_BOOT_KEY = "campaign_war_dog_collar_attempted_boot_id"
_WAR_DOG_COLLAR_COOLDOWN_KEY = "campaign_war_dog_collar_cooldown"
_WAR_DOG_COLLAR_COOLDOWN_SEGMENTS = 3
_PIERCING_WEAPON_UPGRADE_REQUIRED_FREE_WEIGHT = 5
_PIERCING_WEAPON_UPGRADE_REQUIRED_MOVE = 246
_PIERCING_WEAPON_UPGRADE_VNUM = 18000
_INTERMEDIATE_PIERCING_WEAPON_UPGRADE_VNUM = 5252
_INTERMEDIATE_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY = (
    "campaign_intermediate_piercing_weapon_upgrade_cooldown"
)
_INTERMEDIATE_PIERCING_WEAPON_UPGRADE_COOLDOWN_SEGMENTS = 3
_PIERCING_WEAPON_UPGRADE_BOOT_KEY = (
    "campaign_piercing_weapon_upgrade_attempted_boot_id"
)
_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY = (
    "campaign_piercing_weapon_upgrade_cooldown"
)
_PIERCING_WEAPON_UPGRADE_COOLDOWN_SEGMENTS = 6
_BELOW_BAND_POLICY_EXCLUSIONS_KEY = "campaign_below_band_policy_exclusions"
_MAINTENANCE_ATTEMPT_LEVEL_KEYS = {
    "outfit-basic-gear": "campaign_outfit_attempted_level",
    "recover-basic-body": "campaign_body_gear_attempted_level",
    "recover-basic-body-gear": "campaign_body_gear_attempted_level",
    "recover-school-wrist-float": "campaign_school_wrist_float_attempted_level",
    "recover-gremlin-waist": "campaign_gremlin_waist_attempted_level",
    "recover-daycare-ring": "campaign_daycare_ring_attempted_level",
    "recover-war-dog-collar": "campaign_war_dog_collar_attempted_level",
    "recover-foundry-set-circlet": (
        _FOUNDRY_SET_CIRCLET_ATTEMPTED_LEVEL_KEY
    ),
}
_BASIC_SHOP_CATEGORIES = frozenset(
    {"body", "head", "arms", "hands", "legs", "feet", "pouch"}
)
_MUD_SCHOOL_ACCESSORY_ROOMS = frozenset(
    {"3711", "3712", "3715", "3716", "3720", "3721", "3722", "3723", "3724", "3725"}
)
_CAMPAIGN_STICKY_METADATA_KEYS = (
    _BELOW_BAND_POLICY_EXCLUSIONS_KEY,
    _PROVISION_FUNDING_REQUIRED_KEY,
    _PROVISION_FUNDING_ATTEMPTS_KEY,
    _PROVISION_FUNDING_LAST_ATTEMPT_KEY,
    _FLIGHT_FUNDING_REQUIRED_KEY,
    _FLIGHT_FUNDING_RETRY_KEY,
    _FLIGHT_PURCHASE_COOLDOWN_KEY,
    _BELOW_BAND_SIGHTINGS_KEY,
    _RESEARCH_ABSENCE_COOLDOWN_KEY,
    _RESEARCH_CROWD_COOLDOWN_KEY,
    _CLEARED_RESEARCH_POLICIES_KEY,
    "campaign_research_results",
    _LAST_PRODUCTIVE_POLICY_KEY,
    _PRODUCTIVE_POLICY_HISTORY_KEY,
    "campaign_policy_revision",
    "campaign_last_policy",
    _HIGHLAND_KEEPER_ROUTE_REPAIR_KEY,
    _HIGHLAND_KEEPER_IDENTITY_REPAIR_KEY,
    _HARD_ROUTE_HAZARD_REPAIR_KEY,
    "campaign_stalled_segments",
    "campaign_has_weapon",
    "campaign_worn_equipment",
    "campaign_primary_weapon",
    "campaign_empty_equipment_categories",
    "campaign_liquidation_baseline",
    "campaign_flight_loan_attempted",
    "campaign_flight_funding_repair_applied",
    "campaign_training_cap_gear_attempted_level",
    "campaign_training_cap_gear_recovered_level",
    _SOURCE_RANKED_CANDIDATE_KEY,
    _PROTECTION_RECOVERY_KEY,
)
_CAMPAIGN_METADATA_REPAIRED_REASON = "campaign_metadata_repaired"


@dataclass(frozen=True)
class CampaignSpec:
    name: str
    character_profile: Path
    character: CharacterSpec
    target_level: int = 100
    max_segments: int = 100
    max_total_runtime: float = 86_400.0
    max_total_commands: int = 25_000
    max_stalled_segments: int = 3

    @property
    def database(self) -> Path:
        return self.character.database

    @classmethod
    def from_mapping(cls, data: dict[str, Any], *, path: Path) -> "CampaignSpec":
        profile_value = data.get("character_profile")
        if not profile_value:
            raise ValueError("character_profile is required")
        character_profile = Path(str(profile_value))
        if not character_profile.is_absolute():
            character_profile = path.parent / character_profile
        character_profile = character_profile.resolve()
        if not character_profile.exists():
            raise ValueError(f"character_profile does not exist: {character_profile}")

        character = load_character_spec(character_profile)
        name = str(data.get("name", character.name)).strip()
        if not name:
            raise ValueError("name must not be empty")
        target_level = int(data.get("target_level", 100))
        max_segments = int(data.get("max_segments", 100))
        max_total_runtime = float(data.get("max_total_runtime", 86_400))
        max_total_commands = int(data.get("max_total_commands", 25_000))
        max_stalled_segments = int(data.get("max_stalled_segments", 3))

        if not 2 <= target_level <= 100:
            raise ValueError("target_level must be between 2 and 100")
        if max_segments < 1:
            raise ValueError("max_segments must be positive")
        if max_total_runtime <= 0:
            raise ValueError("max_total_runtime must be positive")
        if max_total_commands < 1:
            raise ValueError("max_total_commands must be positive")
        if max_stalled_segments < 1:
            raise ValueError("max_stalled_segments must be positive")

        return cls(
            name=name,
            character_profile=character_profile,
            character=character,
            target_level=target_level,
            max_segments=max_segments,
            max_total_runtime=max_total_runtime,
            max_total_commands=max_total_commands,
            max_stalled_segments=max_stalled_segments,
        )


@dataclass(frozen=True)
class CampaignResult:
    campaign_id: int
    status: str
    checkpoint_id: int | None
    message: str | None
    state: dict[str, Any]

    @property
    def ready_for_next_segment(self) -> bool:
        return bool(
            self.status == "ready"
            and self.message
            and "checkpointed for the next verified segment." in self.message
        )

    @property
    def awaiting_area_reset(self) -> bool:
        return bool(
            self.status == "ready"
            and self.message
            and "awaiting" in self.message.casefold()
            and "area reset" in self.message.casefold()
        )


def _refresh_policy_revision(
    state: dict[str, Any],
    *,
    completed_policy_ids: Collection[str] = (),
) -> dict[str, Any]:
    """Reset stale stall history once when the autonomous policy graph changes."""
    original_research_results = dict(
        state.get("campaign_research_results") or {}
    )
    research_results = dict(original_research_results)
    crowd_abort_reason = str(
        state.get("campaign_fastwalk_abort_reason") or ""
    )
    crowd_policy_id = state.get("campaign_last_policy")
    if (
        isinstance(crowd_policy_id, str)
        and any(
            crowd_abort_reason.startswith(prefix)
            for prefix in _FIELD_CROWD_ABORT_PREFIXES
        )
        and crowd_policy_id in research_results
    ):
        # A combat-assist abort can leave a viable consideration in the
        # checkpoint even though the hunt never completed. Repair that stale
        # promotion before selecting the next bounded segment.
        state = dict(state)
        research_results.pop(crowd_policy_id, None)
        if research_results:
            state["campaign_research_results"] = research_results
        else:
            state.pop("campaign_research_results", None)
        absence_cooldowns = dict(
            state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
        )
        absence_cooldowns.pop(crowd_policy_id, None)
        if absence_cooldowns:
            state[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
        else:
            state.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
    previous_revision = int(state.get("campaign_policy_revision", 0))
    unobserved_policy_ids = {
        policy_id
        for policy_id, result in research_results.items()
        if (
            isinstance(result, dict)
            and result.get("observed") is False
            and not result.get("absent")
            and not result.get("route_hazard")
            and not result.get("crowded")
            and not (
                previous_revision < 112
                and _is_research_absence_retry_policy(policy_id)
                and result.get("completed_kill") is False
                and result.get("boot_id") == state.get("world_boot_id")
            )
        )
    }
    if unobserved_policy_ids:
        state = dict(state)
        state["campaign_research_results"] = {
            policy_id: result
            for policy_id, result in research_results.items()
            if policy_id not in unobserved_policy_ids
        }
        if not state["campaign_research_results"]:
            state.pop("campaign_research_results")
    if previous_revision < 112:
        # A research hunt that ended without a consider outcome was previously
        # recorded as a generic failed hunt, which allowed an empty circuit to
        # repeat immediately. Migrate only same-reboot, unobserved hunt results
        # into the temporary absence rotation introduced by the merge logic.
        migrated_results = dict(
            state.get("campaign_research_results") or {}
        )
        absence_cooldowns = dict(
            state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
        )
        changed = False
        for policy_id, raw_result in list(migrated_results.items()):
            if not (
                _is_research_absence_retry_policy(policy_id)
                and isinstance(raw_result, dict)
                and raw_result.get("completed_kill") is False
                and raw_result.get("observed") is False
                and raw_result.get("boot_id") == state.get("world_boot_id")
                and not raw_result.get("absent")
                and not raw_result.get("route_hazard")
                and not raw_result.get("crowded")
                and not raw_result.get("unattackable")
            ):
                continue
            migrated_result = dict(raw_result)
            migrated_result["absent"] = True
            migrated_result["unobserved"] = True
            migrated_results[policy_id] = migrated_result
            retry_cooldown = _research_absence_retry_cooldown(policy_id)
            if retry_cooldown is None:
                continue
            absence_cooldowns[policy_id] = retry_cooldown
            changed = True
        if changed:
            state = dict(state)
            state["campaign_research_results"] = migrated_results
            state[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
    absence_cooldowns = dict(
        state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
    )
    for policy_id, result in dict(
        state.get("campaign_research_results") or {}
    ).items():
        retry_cooldown = _research_absence_retry_cooldown(policy_id)
        if (
            retry_cooldown is not None
            and isinstance(result, dict)
            and (
                result.get("absent")
                or result.get("route_hazard")
                == _DYNAMIC_FIELD_ROUTE_HAZARD_ABORT_REASON
            )
        ):
            absence_cooldowns.setdefault(policy_id, retry_cooldown)
    if absence_cooldowns != dict(
        state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
    ):
        state = dict(state)
        state[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
    state = _mark_retryable_research_failures(state)

    # A no-combat research probe that has already fled an unexpected attacker
    # is route-risk evidence. Preserve the current checkpoint's result instead
    # of allowing a reconnect or maintenance pass to replay the same hazard.
    if (
        state.get("campaign_policy_revision") == _CAMPAIGN_POLICY_REVISION
        and str(state.get("campaign_fastwalk_abort_reason") or "").startswith(
            _DYNAMIC_FIELD_ROUTE_HAZARD_ABORT_REASON
        )
    ):
        policy_id = state.get("campaign_last_policy")
        if isinstance(policy_id, str) and policy_id:
            current_results = _campaign_research_results(state)
            if policy_id not in current_results:
                state = dict(state)
                current_results[policy_id] = {
                    "observed": False,
                    "viable": False,
                    "route_hazard": state["campaign_fastwalk_abort_reason"],
                    "boot_id": state.get("world_boot_id"),
                }
                state["campaign_research_results"] = current_results

    if state.get("campaign_policy_revision") == _CAMPAIGN_POLICY_REVISION:
        current_route_policy = state.get("campaign_last_policy")
        if (
            current_route_policy in _GALAXY_ROUTE_HAZARD_POLICY_IDS
            and not state.get(_HARD_ROUTE_HAZARD_REPAIR_KEY)
        ):
            # The hard-hazard policy supersedes the old below-band waiver.
            # Clear only the pre-fix generic dynamic result once; explicit
            # source-preflight evidence remains a durable route block.
            repaired = dict(state)
            current_results = _campaign_research_results(state)
            current_result = current_results.get(current_route_policy)
            stale_dynamic_hazard = (
                isinstance(current_result, dict)
                and current_result.get("route_hazard")
                == _DYNAMIC_FIELD_ROUTE_HAZARD_ABORT_REASON
            )
            if stale_dynamic_hazard:
                repaired_results = dict(current_results)
                repaired_results.pop(str(current_route_policy), None)
                if repaired_results:
                    repaired["campaign_research_results"] = repaired_results
                else:
                    repaired.pop("campaign_research_results", None)
                absence_cooldowns = dict(
                    repaired.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
                )
                absence_cooldowns.pop(str(current_route_policy), None)
                if absence_cooldowns:
                    repaired[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
                else:
                    repaired.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
                if (
                    repaired.get("campaign_fastwalk_abort_reason")
                    == _DYNAMIC_FIELD_ROUTE_HAZARD_ABORT_REASON
                ):
                    repaired.pop("campaign_fastwalk_abort_reason", None)
                repaired.pop("campaign_fastwalk_target_absent", None)
            repaired[_HARD_ROUTE_HAZARD_REPAIR_KEY] = True
            return repaired
        current_route_abort = str(
            state.get("campaign_fastwalk_abort_reason") or ""
        )
        current_route_result = _campaign_research_results(state).get(
            current_route_policy
        )
        current_route_hazard = (
            str(current_route_result.get("route_hazard") or "")
            if isinstance(current_route_result, dict)
            else ""
        )
        if (
            current_route_policy
            in {
                _HIGHLAND_KEEPER_POLICY_ID,
                _HIGHLAND_KEEPER_HUNT_POLICY_ID,
            }
            and (
                current_route_abort
                == _DYNAMIC_FIELD_ROUTE_HAZARD_ABORT_REASON
                or current_route_hazard
                == _DYNAMIC_FIELD_ROUTE_HAZARD_ABORT_REASON
            )
            and not state.get(_HIGHLAND_KEEPER_ROUTE_REPAIR_KEY)
        ):
            repaired = dict(state)
            repaired_results = _campaign_research_results(repaired)
            repaired_results.pop(_HIGHLAND_KEEPER_POLICY_ID, None)
            repaired_results.pop(_HIGHLAND_KEEPER_HUNT_POLICY_ID, None)
            if repaired_results:
                repaired["campaign_research_results"] = repaired_results
            else:
                repaired.pop("campaign_research_results", None)
            absence_cooldowns = dict(
                repaired.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
            )
            absence_cooldowns.pop(_HIGHLAND_KEEPER_POLICY_ID, None)
            absence_cooldowns.pop(_HIGHLAND_KEEPER_HUNT_POLICY_ID, None)
            if absence_cooldowns:
                repaired[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
            else:
                repaired.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
            repaired.pop("campaign_fastwalk_target_absent", None)
            repaired.pop("campaign_fastwalk_abort_reason", None)
            repaired[_HIGHLAND_KEEPER_ROUTE_REPAIR_KEY] = True
            return repaired
        if (
            current_route_policy == _HIGHLAND_KEEPER_HUNT_POLICY_ID
            and current_route_abort.startswith(
                "field combat aborted after unapproved attacker "
                "'The Keeper of the Tower'"
            )
            and not state.get(_HIGHLAND_KEEPER_IDENTITY_REPAIR_KEY)
        ):
            repaired = dict(state)
            repaired["campaign_last_policy"] = _HIGHLAND_KEEPER_POLICY_ID
            repaired.pop("campaign_fastwalk_target_absent", None)
            repaired.pop("campaign_fastwalk_abort_reason", None)
            repaired[_HIGHLAND_KEEPER_IDENTITY_REPAIR_KEY] = True
            return repaired
        cleared_research_policies = {
            str(policy_id)
            for policy_id in state.get(_CLEARED_RESEARCH_POLICIES_KEY, ())
        }
        research_results = _campaign_research_results(state)
        failed_jailor_hunt = (
            state.get("campaign_last_policy") == _HIGHTOWER_JAILOR_HUNT_POLICY_ID
            and isinstance(
                research_results.get(_HIGHTOWER_JAILOR_HUNT_POLICY_ID),
                dict,
            )
            and research_results[_HIGHTOWER_JAILOR_HUNT_POLICY_ID].get(
                "viable"
            )
            is True
            and not state.get("campaign_objective_kills")
            and str(state.get("campaign_fastwalk_abort_reason") or "").startswith(
                "field combat aborted"
            )
        )
        if not cleared_research_policies and failed_jailor_hunt:
            repaired = dict(state)
            repaired_results = dict(research_results)
            repaired_results[_HIGHTOWER_JAILOR_HUNT_POLICY_ID] = {
                **repaired_results[_HIGHTOWER_JAILOR_HUNT_POLICY_ID],
                "viable": False,
                "completed_kill": False,
            }
            repaired["campaign_research_results"] = repaired_results
            return repaired
        stale_jailor_evidence = any(
            isinstance(research_results.get(policy_id), dict)
            and research_results[policy_id].get("absent")
            for policy_id in (
                _HIGHTOWER_JAILOR_POLICY_ID,
                _HIGHTOWER_JAILOR_HUNT_POLICY_ID,
            )
        ) or bool(state.get("campaign_fastwalk_target_absent"))
        if not cleared_research_policies and stale_jailor_evidence:
            repaired = dict(state)
            for policy_id in (
                _HIGHTOWER_JAILOR_POLICY_ID,
                _HIGHTOWER_JAILOR_HUNT_POLICY_ID,
            ):
                research_results.pop(policy_id, None)
            if research_results:
                repaired["campaign_research_results"] = research_results
            else:
                repaired.pop("campaign_research_results", None)
            absence_cooldowns = dict(
                repaired.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
            )
            absence_cooldowns.pop(_HIGHTOWER_JAILOR_POLICY_ID, None)
            absence_cooldowns.pop(_HIGHTOWER_JAILOR_HUNT_POLICY_ID, None)
            if absence_cooldowns:
                repaired[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
            else:
                repaired.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
            repaired[_CLEARED_RESEARCH_POLICIES_KEY] = [
                _HIGHTOWER_JAILOR_HUNT_POLICY_ID,
                _HIGHTOWER_JAILOR_POLICY_ID,
            ]
            repaired.pop("campaign_fastwalk_target_absent", None)
            return repaired
        return state
    refreshed = {
        **state,
        "campaign_policy_revision": _CAMPAIGN_POLICY_REVISION,
        "campaign_stalled_segments": 0,
    }
    previous_revision = int(state.get("campaign_policy_revision", 0))
    bardoosh_was_unobserved = bool(
        state.get("campaign_last_policy") == _BARDOOSH_POLICY_ID
        and not bool(
            original_research_results.get(_BARDOOSH_POLICY_ID, {}).get(
                "observed"
            )
        )
    )
    bardoosh_has_result = _BARDOOSH_POLICY_ID in completed_policy_ids
    if (
        previous_revision < 78
        and bardoosh_was_unobserved
        and not bardoosh_has_result
    ):
        refreshed["campaign_fastwalk_abort_reason"] = (
            _BARDOOSH_ROUTE_FIX_RETRY_REASON
        )
    elif (
        previous_revision < 79
        and bardoosh_was_unobserved
        and not bardoosh_has_result
    ):
        refreshed["campaign_fastwalk_abort_reason"] = (
            _BARDOOSH_IDENTITY_FIX_RETRY_REASON
        )
    elif (
        previous_revision < 80
        and state.get("campaign_last_policy") == _BARDOOSH_POLICY_ID
        and (
            bardoosh_has_result
            or state.get("campaign_fastwalk_abort_reason")
            in {
                _BARDOOSH_ROUTE_FIX_RETRY_REASON,
                _BARDOOSH_IDENTITY_FIX_RETRY_REASON,
            }
        )
    ):
        refreshed.pop("campaign_fastwalk_abort_reason", None)
    nobleman_result = original_research_results.get(_NOBLEMAN_POLICY_ID)
    if (
        previous_revision < 81
        and isinstance(nobleman_result, dict)
        and nobleman_result.get("observed") is False
    ):
        refreshed["campaign_fastwalk_abort_reason"] = (
            _NOBLEMAN_ROUTE_FIX_RETRY_REASON
        )
    elif (
        previous_revision < 82
        and isinstance(nobleman_result, dict)
        and nobleman_result.get("observed") is False
    ):
        refreshed["campaign_fastwalk_abort_reason"] = (
            _NOBLEMAN_IDENTITY_FIX_RETRY_REASON
        )
    worker_result = original_research_results.get(_DWARVEN_WORKERS_POLICY_ID)
    if (
        previous_revision < 91
        and isinstance(worker_result, dict)
        and worker_result.get("observed") is False
    ):
        refreshed["campaign_fastwalk_abort_reason"] = (
            _DWARVEN_WORKERS_SEARCH_FIX_RETRY_REASON
        )
    # The Forest target can repopulate during the same reboot. Retire the old
    # reboot-scoped attempt marker and allow one immediate retry.
    if previous_revision < 83:
        refreshed.pop(_PIERCING_WEAPON_UPGRADE_BOOT_KEY, None)
        refreshed.pop(_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY, None)
    if previous_revision < 85 and int(
        state.get(_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY) or 0
    ) > 0:
        refreshed.pop(_PIERCING_WEAPON_UPGRADE_BOOT_KEY, None)
        refreshed.pop(_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY, None)
    if previous_revision < 87:
        refreshed.pop("campaign_training_cap_gear_attempted_level", None)
        refreshed.pop("campaign_training_cap_gear_recovered_level", None)
    if previous_revision < 93:
        refreshed.pop(
            _INTERMEDIATE_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY,
            None,
        )
    if (
        previous_revision < 94
        and int(refreshed.get(_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY) or 0) > 0
    ):
        refreshed[_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY] = max(
            int(refreshed[_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY]),
            _PIERCING_WEAPON_UPGRADE_COOLDOWN_SEGMENTS,
        )
    if previous_revision < 96:
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        watchman_result = research_results.get(_MIRROR_WATCHMAN_POLICY_ID)
        if (
            isinstance(watchman_result, dict)
            and watchman_result.get("observed") is False
        ):
            research_results.pop(_MIRROR_WATCHMAN_POLICY_ID)
            refreshed["campaign_research_results"] = research_results
    if previous_revision < 98:
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        soldier_result = research_results.get(_SHADOW_KEEP_SOLDIER_POLICY_ID)
        if (
            isinstance(soldier_result, dict)
            and soldier_result.get("observed") is False
        ):
            research_results.pop(_SHADOW_KEEP_SOLDIER_POLICY_ID)
            refreshed["campaign_research_results"] = research_results
    if previous_revision < 99:
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        if _MIRROR_WATCHMAN_POLICY_ID in research_results:
            research_results.pop(_MIRROR_WATCHMAN_POLICY_ID)
            refreshed["campaign_research_results"] = research_results
    if previous_revision < 100:
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        stag_result = research_results.get(_CRYSTALMIR_WHITE_STAG_POLICY_ID)
        if isinstance(stag_result, dict) and stag_result.get("absent"):
            absence_cooldowns = dict(
                refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
            )
            absence_cooldowns.setdefault(
                _CRYSTALMIR_WHITE_STAG_POLICY_ID,
                _RESEARCH_ABSENCE_RETRY_COOLDOWNS[
                    _CRYSTALMIR_WHITE_STAG_POLICY_ID
                ],
            )
            refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
    if previous_revision < 101:
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        research_results.pop(_HIGHTOWER_JAILOR_POLICY_ID, None)
        research_results.pop(_HIGHTOWER_JAILOR_HUNT_POLICY_ID, None)
        if research_results:
            refreshed["campaign_research_results"] = research_results
        else:
            refreshed.pop("campaign_research_results", None)
        absence_cooldowns = dict(
            refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
        )
        absence_cooldowns.pop(_HIGHTOWER_JAILOR_POLICY_ID, None)
        absence_cooldowns.pop(_HIGHTOWER_JAILOR_HUNT_POLICY_ID, None)
        if absence_cooldowns:
            refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
        else:
            refreshed.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
        cleared_research_policies = {
            str(policy_id)
            for policy_id in refreshed.get(_CLEARED_RESEARCH_POLICIES_KEY, ())
        }
        cleared_research_policies.update(
            {
                _HIGHTOWER_JAILOR_POLICY_ID,
                _HIGHTOWER_JAILOR_HUNT_POLICY_ID,
            }
        )
        refreshed[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(
            cleared_research_policies
        )
        refreshed.pop("campaign_fastwalk_target_absent", None)
    if previous_revision < 102:
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        research_results.pop(_GALAXY_RED_SUPERGIANT_POLICY_ID, None)
        research_results.pop("galaxy-red-supergiant-hunt-17-20", None)
        if research_results:
            refreshed["campaign_research_results"] = research_results
        else:
            refreshed.pop("campaign_research_results", None)
        absence_cooldowns = dict(
            refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
        )
        absence_cooldowns.pop(_GALAXY_RED_SUPERGIANT_POLICY_ID, None)
        absence_cooldowns.pop("galaxy-red-supergiant-hunt-17-20", None)
        if absence_cooldowns:
            refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
        else:
            refreshed.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
        if refreshed.get("campaign_last_policy") in {
            _GALAXY_RED_SUPERGIANT_POLICY_ID,
            "galaxy-red-supergiant-hunt-17-20",
        }:
            refreshed.pop("campaign_fastwalk_target_absent", None)
            refreshed.pop("campaign_fastwalk_abort_reason", None)
    if (
        previous_revision < 103
        and refreshed.get("campaign_last_policy")
        in {
            _MAHNTOR_ROCK_TOAD_CIRCUIT_POLICY_ID,
            _MAHNTOR_ROCK_TOAD_HUNT_POLICY_ID,
        }
        and str(refreshed.get("campaign_fastwalk_abort_reason") or "")
        .startswith(_MAHNTOR_ROUTE_ABORT_PREFIX)
    ):
        # The old circuit registered a non-contiguous destination sequence and
        # could abort before it reached its next source reset room.
        refreshed.pop("campaign_fastwalk_abort_reason", None)
    if previous_revision < 104:
        # Below-band evidence recorded before room-specific sightings existed
        # could not identify which Mahn-Tor reset produced it. Re-evaluate the
        # route once rather than carrying an anonymous whole-policy exclusion.
        exclusions = dict(
            refreshed.get(_BELOW_BAND_POLICY_EXCLUSIONS_KEY) or {}
        )
        for policy_id in (
            _MAHNTOR_ROCK_TOAD_CIRCUIT_POLICY_ID,
            _MAHNTOR_ROCK_TOAD_HUNT_POLICY_ID,
        ):
            exclusions.pop(policy_id, None)
        if exclusions:
            refreshed[_BELOW_BAND_POLICY_EXCLUSIONS_KEY] = exclusions
        else:
            refreshed.pop(_BELOW_BAND_POLICY_EXCLUSIONS_KEY, None)
        sightings = dict(refreshed.get(_BELOW_BAND_SIGHTINGS_KEY) or {})
        for policy_id in (
            _MAHNTOR_ROCK_TOAD_CIRCUIT_POLICY_ID,
            _MAHNTOR_ROCK_TOAD_HUNT_POLICY_ID,
        ):
            sightings.pop(policy_id, None)
        if sightings:
            refreshed[_BELOW_BAND_SIGHTINGS_KEY] = sightings
        else:
            refreshed.pop(_BELOW_BAND_SIGHTINGS_KEY, None)
    if previous_revision < 105:
        # Revision 104 recorded the Shire prince with an article that the
        # source-backed target parser removes. Clear only that false absence
        # so the corrected exact identity gets one live retry.
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        for policy_id in (
            _SHIRE_DWARVEN_PRINCE_POLICY_ID,
            _SHIRE_DWARVEN_PRINCE_HUNT_POLICY_ID,
        ):
            research_results.pop(policy_id, None)
        if research_results:
            refreshed["campaign_research_results"] = research_results
        else:
            refreshed.pop("campaign_research_results", None)
        absence_cooldowns = dict(
            refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
        )
        for policy_id in (
            _SHIRE_DWARVEN_PRINCE_POLICY_ID,
            _SHIRE_DWARVEN_PRINCE_HUNT_POLICY_ID,
        ):
            absence_cooldowns.pop(policy_id, None)
        if absence_cooldowns:
            refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
        else:
            refreshed.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
        if refreshed.get("campaign_last_policy") in {
            _SHIRE_DWARVEN_PRINCE_POLICY_ID,
            _SHIRE_DWARVEN_PRINCE_HUNT_POLICY_ID,
        }:
            refreshed.pop("campaign_fastwalk_target_absent", None)
            refreshed.pop("campaign_fastwalk_abort_reason", None)
    if previous_revision < 106:
        # The first corrected-identity retry could consider a crowded room
        # before the shared crowd gate was applied to research probes. Remove
        # only that result and cached target outcome for a clean re-probe.
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        for policy_id in (
            _SHIRE_DWARVEN_PRINCE_POLICY_ID,
            _SHIRE_DWARVEN_PRINCE_HUNT_POLICY_ID,
        ):
            research_results.pop(policy_id, None)
        if research_results:
            refreshed["campaign_research_results"] = research_results
        else:
            refreshed.pop("campaign_research_results", None)
        absence_cooldowns = dict(
            refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
        )
        for policy_id in (
            _SHIRE_DWARVEN_PRINCE_POLICY_ID,
            _SHIRE_DWARVEN_PRINCE_HUNT_POLICY_ID,
        ):
            absence_cooldowns.pop(policy_id, None)
        if absence_cooldowns:
            refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
        else:
            refreshed.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
        consider_outcomes = dict(
            refreshed.get("campaign_fastwalk_consider_outcomes") or {}
        )
        consider_outcomes.pop("dwarven prince", None)
        if consider_outcomes:
            refreshed["campaign_fastwalk_consider_outcomes"] = consider_outcomes
        else:
            refreshed.pop("campaign_fastwalk_consider_outcomes", None)
    if previous_revision < 108:
        # The Pyramid probe used to inspect only reset room 2643. A live
        # locator proved that Ali Baba can be elsewhere in the source-vetted
        # tunnel branch, so clear only the stale Pyramid absence for one
        # bounded re-probe.
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        for policy_id in (
            _PYRAMID_ALI_BABA_POLICY_ID,
            _PYRAMID_ALI_BABA_HUNT_POLICY_ID,
        ):
            research_results.pop(policy_id, None)
        if research_results:
            refreshed["campaign_research_results"] = research_results
        else:
            refreshed.pop("campaign_research_results", None)
        absence_cooldowns = dict(
            refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
        )
        for policy_id in (
            _PYRAMID_ALI_BABA_POLICY_ID,
            _PYRAMID_ALI_BABA_HUNT_POLICY_ID,
        ):
            absence_cooldowns.pop(policy_id, None)
        if absence_cooldowns:
            refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
        else:
            refreshed.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
        if refreshed.get("campaign_last_policy") in {
            _PYRAMID_ALI_BABA_POLICY_ID,
            _PYRAMID_ALI_BABA_HUNT_POLICY_ID,
        }:
            refreshed.pop("campaign_fastwalk_target_absent", None)
            refreshed.pop("campaign_fastwalk_abort_reason", None)
    if previous_revision < 109:
        # The first extended Pyramid sweep still stopped on a redundant route
        # destination before reaching the source-connected tunnel rooms. Clear
        # only that stale absence so the corrected route gets one fresh probe.
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        pyramid_result = research_results.get(_PYRAMID_ALI_BABA_POLICY_ID)
        if isinstance(pyramid_result, dict) and pyramid_result.get("absent"):
            research_results.pop(_PYRAMID_ALI_BABA_POLICY_ID, None)
            research_results.pop(_PYRAMID_ALI_BABA_HUNT_POLICY_ID, None)
            if research_results:
                refreshed["campaign_research_results"] = research_results
            else:
                refreshed.pop("campaign_research_results", None)
            absence_cooldowns = dict(
                refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
            )
            absence_cooldowns.pop(_PYRAMID_ALI_BABA_POLICY_ID, None)
            absence_cooldowns.pop(_PYRAMID_ALI_BABA_HUNT_POLICY_ID, None)
            if absence_cooldowns:
                refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
            else:
                refreshed.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
            if refreshed.get("campaign_last_policy") in {
                _PYRAMID_ALI_BABA_POLICY_ID,
                _PYRAMID_ALI_BABA_HUNT_POLICY_ID,
            }:
                refreshed.pop("campaign_fastwalk_target_absent", None)
                refreshed.pop("campaign_fastwalk_abort_reason", None)
    if previous_revision < 110:
        # Run 2604 found Ali Baba in source room 2639, which the previous
        # tunnel sweep did not inspect. Clear that stale absence for one probe
        # using the expanded, source-connected room list.
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        pyramid_result = research_results.get(_PYRAMID_ALI_BABA_POLICY_ID)
        if isinstance(pyramid_result, dict) and pyramid_result.get("absent"):
            research_results.pop(_PYRAMID_ALI_BABA_POLICY_ID, None)
            research_results.pop(_PYRAMID_ALI_BABA_HUNT_POLICY_ID, None)
            if research_results:
                refreshed["campaign_research_results"] = research_results
            else:
                refreshed.pop("campaign_research_results", None)
            absence_cooldowns = dict(
                refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
            )
            absence_cooldowns.pop(_PYRAMID_ALI_BABA_POLICY_ID, None)
            absence_cooldowns.pop(_PYRAMID_ALI_BABA_HUNT_POLICY_ID, None)
            if absence_cooldowns:
                refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
            else:
                refreshed.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
            if refreshed.get("campaign_last_policy") in {
                _PYRAMID_ALI_BABA_POLICY_ID,
                _PYRAMID_ALI_BABA_HUNT_POLICY_ID,
            }:
                refreshed.pop("campaign_fastwalk_target_absent", None)
            refreshed.pop("campaign_fastwalk_abort_reason", None)
    if previous_revision < 111:
        # Galaxy routes now ignore source-confirmed hazards at least five
        # levels below the character. Re-probe any old route-hazard result so
        # the new source-level gate, rather than stale preflight evidence,
        # decides whether the route is executable.
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        cleared_route_hazards = {
            policy_id
            for policy_id in _GALAXY_ROUTE_HAZARD_POLICY_IDS
            if isinstance(research_results.get(policy_id), dict)
            and research_results[policy_id].get("route_hazard")
        }
        for policy_id in cleared_route_hazards:
            research_results.pop(policy_id, None)
        if research_results:
            refreshed["campaign_research_results"] = research_results
        else:
            refreshed.pop("campaign_research_results", None)
        absence_cooldowns = dict(
            refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
        )
        for policy_id in cleared_route_hazards:
            absence_cooldowns.pop(policy_id, None)
        if absence_cooldowns:
            refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
        else:
            refreshed.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
        if refreshed.get("campaign_last_policy") in cleared_route_hazards:
            refreshed.pop("campaign_fastwalk_target_absent", None)
            refreshed.pop("campaign_fastwalk_abort_reason", None)
    if not refreshed.get(_HIGHLAND_KEEPER_ROUTE_REPAIR_KEY):
        # Run 2794 exposed a source-confirmed below-band bogleech interruption
        # before the no-combat probe could apply its incidental-combat rule.
        # Clear that one stale result so the corrected runner gets one retry;
        # preserve any new route hazard after the retry.
        research_results = dict(
            refreshed.get("campaign_research_results") or {}
        )
        keeper_result = research_results.get(_HIGHLAND_KEEPER_POLICY_ID)
        if (
            isinstance(keeper_result, dict)
            and keeper_result.get("route_hazard")
            == _DYNAMIC_FIELD_ROUTE_HAZARD_ABORT_REASON
        ):
            research_results.pop(_HIGHLAND_KEEPER_POLICY_ID, None)
            research_results.pop(_HIGHLAND_KEEPER_HUNT_POLICY_ID, None)
            if research_results:
                refreshed["campaign_research_results"] = research_results
            else:
                refreshed.pop("campaign_research_results", None)
            absence_cooldowns = dict(
                refreshed.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
            )
            absence_cooldowns.pop(_HIGHLAND_KEEPER_POLICY_ID, None)
            absence_cooldowns.pop(_HIGHLAND_KEEPER_HUNT_POLICY_ID, None)
            if absence_cooldowns:
                refreshed[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
            else:
                refreshed.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
            if refreshed.get("campaign_last_policy") in {
                _HIGHLAND_KEEPER_POLICY_ID,
                _HIGHLAND_KEEPER_HUNT_POLICY_ID,
            }:
                refreshed.pop("campaign_fastwalk_target_absent", None)
                refreshed.pop("campaign_fastwalk_abort_reason", None)
            refreshed[_HIGHLAND_KEEPER_ROUTE_REPAIR_KEY] = True
    if previous_revision < 20:
        refreshed.pop("campaign_body_gear_attempted_level", None)
    # Ring carriers can repopulate during the same reboot. Preserve an existing
    # bounded retry delay, and migrate reboot-only attempt markers to one.
    if "campaign_daycare_ring_attempted_level" in refreshed:
        refreshed[_DAYCARE_RING_COOLDOWN_KEY] = max(
            int(refreshed.get(_DAYCARE_RING_COOLDOWN_KEY) or 0),
            _DAYCARE_RING_COOLDOWN_SEGMENTS,
        )
    else:
        refreshed.pop(_DAYCARE_RING_COOLDOWN_KEY, None)
    if previous_revision < 37:
        refreshed.pop("campaign_war_dog_collar_attempted_level", None)
        refreshed.pop(_WAR_DOG_COLLAR_ATTEMPT_BOOT_KEY, None)
        refreshed.pop(_WAR_DOG_COLLAR_COOLDOWN_KEY, None)
    return refreshed


def _source_ranked_fallback_needed(
    state: Mapping[str, Any],
    policy: ProgressionPolicy,
) -> bool:
    """Open generic source ranking after a registered policy is exhausted."""
    level = _level(state)
    if level < _SOURCE_RANKED_HUNT_POLICY.minimum_level:
        return False
    if policy.execution in (
        _MAINTENANCE_EXECUTIONS
        | {"starter", "arena", "source-ranked-hunt"}
    ):
        return False
    if not policy.executable:
        return True
    excluded = _campaign_below_band_policy_ids(
        dict(state),
        level=level,
        boot_id=state.get("world_boot_id"),
    )
    if policy.policy_id in excluded:
        return True
    result = _campaign_research_results(state).get(policy.policy_id)
    if isinstance(result, Mapping) and result.get("boot_id") == state.get(
        "world_boot_id"
    ):
        if any(
            (
                result.get("absent") is True,
                result.get("crowded") is True,
                result.get("route_hazard"),
                result.get("unattackable"),
                result.get("viable") is False,
                result.get("completed_kill") is False,
            )
        ):
            return True
    if policy.policy_id == str(state.get("campaign_last_policy") or ""):
        abort_reason = str(state.get("campaign_fastwalk_abort_reason") or "")
        if state.get("campaign_fastwalk_target_absent") or any(
            abort_reason.startswith(prefix)
            for prefix in (
                *_FIELD_CROWD_ABORT_PREFIXES,
                *_FIELD_ROUTE_HAZARD_ABORT_PREFIXES,
            )
        ):
            return True
    return False


class CampaignRunner:
    """Run verified policy segments with durable checkpoints and aggregate limits."""

    def __init__(
        self,
        spec: CampaignSpec,
        config_path: Path,
        *,
        segment_runner: SegmentRunner | None = None,
        force_new: bool = False,
        max_segment_runtime: float | None = None,
        defer_stall_for_reset: bool = False,
        retry_stalled: bool = False,
    ) -> None:
        if max_segment_runtime is not None and max_segment_runtime <= 0:
            raise ValueError("max_segment_runtime must be positive")
        self.spec = spec
        self.config_path = config_path.resolve()
        self.segment_runner = segment_runner
        self.force_new = force_new
        self.max_segment_runtime = max_segment_runtime
        self.defer_stall_for_reset = defer_stall_for_reset
        self.retry_stalled = retry_stalled
        self._historical_large_sack = False
        self._historical_sanctuary_potion = False
        self._boot_kill_counts: Counter[str] = Counter()
        self._policy_xp_deltas: dict[str, int] = {}
        self._gear_catalog: GearCatalog | None = None
        self._boot_id: int | None = None

    async def run(self) -> CampaignResult:
        with RunStorage(self.spec.database) as storage:
            source_directory = Path("runs/dd4-source/server/area")
            if self._gear_catalog is None and source_directory.is_dir():
                self._gear_catalog = load_gear_catalog(
                    str(source_directory.resolve())
                )
            self._historical_large_sack = storage.character_has_acquired_item(
                self.spec.character.name,
                "large sack",
            )
            self._historical_sanctuary_potion = (
                storage.character_has_acquired_item(
                    self.spec.character.name,
                    "purple potion",
                )
            )
            boot_id = storage.latest_boot_id()
            self._boot_id = boot_id
            if boot_id is not None:
                self._boot_kill_counts.update(
                    str(row["mob_name"])
                    for row in storage.list_mob_kills(
                        self.spec.character.name,
                        boot_id=boot_id,
                    )
            )
            campaign_id, state = self._open_campaign(storage)
            campaign_segments = storage.list_campaign_segments(campaign_id)
            self._policy_xp_deltas = _campaign_policy_xp_deltas(
                campaign_segments, storage=storage
            )
            checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)
            state_before_policy_repair = dict(state)
            state = _with_productive_policy_history(
                state,
                policy_ids=_campaign_productive_policy_ids(
                    campaign_segments,
                    storage=storage,
                    boot_id=state.get("world_boot_id") or boot_id,
                ),
                boot_id=state.get("world_boot_id") or boot_id,
            )
            state = _refresh_policy_revision(
                state,
                completed_policy_ids=self._policy_xp_deltas,
            )
            state = _repair_research_absence_cooldowns(state)
            state = _repair_protection_recovery_metadata(
                state,
                campaign_segments,
                storage=storage,
            )
            state = _remember_last_productive_policy(
                state,
                policy_xp_deltas=self._policy_xp_deltas,
            )
            if checkpoint is not None and state != state_before_policy_repair:
                storage.record_campaign_checkpoint(
                    campaign_id,
                    segment_id=checkpoint["segment_id"],
                    run_id=checkpoint["run_id"],
                    phase=str(checkpoint["phase"]),
                    reason=_CAMPAIGN_METADATA_REPAIRED_REASON,
                    state=state,
                )
                checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)
            checkpoint_id = int(checkpoint["id"]) if checkpoint is not None else None

            if _level(state) >= self.spec.target_level:
                if _level(_checkpoint_state(checkpoint)) < self.spec.target_level:
                    checkpoint_id = storage.record_campaign_checkpoint(
                        campaign_id,
                        segment_id=None,
                        run_id=None,
                        phase="target-complete",
                        reason="target_reconciled",
                        state=state,
                    )
                storage.finish_campaign(campaign_id, status="success")
                return CampaignResult(
                    campaign_id,
                    "success",
                    checkpoint_id,
                    f"Target level {self.spec.target_level} already reached.",
                    state,
                )

            stalled = int(state.get("campaign_stalled_segments", 0))
            if (
                self.retry_stalled
                and stalled >= self.spec.max_stalled_segments
            ):
                stalled = self.spec.max_stalled_segments - 1
                state = {
                    **state,
                    "campaign_stalled_segments": stalled,
                }
            # A productive current-reboot hunt is safe to resume immediately;
            # the other retry paths still require the explicit reset policy.
            state = _retry_current_absent_research_policy(
                state,
                productive_only=True,
            )
            if self.retry_stalled:
                state = _retry_current_absent_research_policy(state)
                state = _retry_required_sanctuary_research_policy(state)
                state = _retry_current_crowded_research_policy(state)
                if not self._policy_for_state(state).executable:
                    state = _retry_any_pending_absent_research_policy(state)
            policy = self._policy_for_state(state)
            state.pop(_POLICY_HANDOFF_KEY, None)

            selected_absent_result = _campaign_research_results(state).get(
                policy.policy_id
            )
            if (
                not self.retry_stalled
                and policy.policy_id
                == _MORIA_SANCTUARY_THIEF_LEVEL_SEVENTEEN_POLICY_ID
                and isinstance(selected_absent_result, dict)
                and selected_absent_result.get("absent") is True
                and selected_absent_result.get("boot_id")
                == state.get("world_boot_id")
                and int(
                    (state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}).get(
                        policy.policy_id,
                        0,
                    )
                    or 0
                )
                > 0
                and _campaign_sanctuary_recovery_required(state)
            ):
                message = (
                    f"{policy.policy_id} target was absent while a sanctuary "
                    "reserve remained required. Campaign checkpointed while "
                    "awaiting the field area reset."
                )
                storage.finish_campaign(campaign_id, status="ready", error=message)
                return CampaignResult(
                    campaign_id,
                    "ready",
                    checkpoint_id,
                    message,
                    state,
                )

            absent_policy_id = str(state.get("campaign_last_policy") or "")
            absent_result = _campaign_research_results(state).get(
                absent_policy_id
            )
            if (
                not self.retry_stalled
                and policy.execution not in _MAINTENANCE_EXECUTIONS
                and (
                    policy.policy_id == absent_policy_id
                    or not policy.executable
                )
                and _is_research_absence_retry_policy(absent_policy_id)
                and (
                    absent_policy_id
                    != _MORIA_SANCTUARY_THIEF_LEVEL_SEVENTEEN_POLICY_ID
                    or not policy.executable
                )
                and isinstance(absent_result, dict)
                and absent_result.get("absent")
                and absent_result.get("boot_id") == state.get("world_boot_id")
            ):
                message = (
                    f"{absent_policy_id} target was absent in the current "
                    "reboot. Campaign checkpointed while awaiting the field "
                    "area reset."
                )
                storage.finish_campaign(campaign_id, status="ready", error=message)
                return CampaignResult(
                    campaign_id,
                    "ready",
                    checkpoint_id,
                    message,
                    state,
                )

            verified_field_target_absent = bool(
                not self.retry_stalled
                and policy.status == "verified"
                and policy.execution not in _MAINTENANCE_EXECUTIONS
                and policy.execution not in {"starter", "arena"}
                and policy.policy_id == absent_policy_id
                and state.get("campaign_fastwalk_target_absent")
            )
            if verified_field_target_absent:
                message = (
                    f"{absent_policy_id} field circuit found no registered "
                    "target. Campaign checkpointed while awaiting the field "
                    "area reset."
                )
                storage.finish_campaign(campaign_id, status="ready", error=message)
                return CampaignResult(
                    campaign_id,
                    "ready",
                    checkpoint_id,
                    message,
                    state,
                )

            crowd_abort_reason = str(
                state.get("campaign_fastwalk_abort_reason") or ""
            )
            crowded_field = any(
                crowd_abort_reason.startswith(prefix)
                for prefix in _FIELD_CROWD_ABORT_PREFIXES
            )
            crowd_policy_id = str(state.get("campaign_last_policy") or "")
            if (
                not self.retry_stalled
                and policy.execution not in _MAINTENANCE_EXECUTIONS
                and crowded_field
                and crowd_policy_id
            ):
                message = (
                    f"{crowd_policy_id} encountered a crowded field room. "
                    "Campaign checkpointed while awaiting the field area reset."
                )
                storage.finish_campaign(campaign_id, status="ready", error=message)
                return CampaignResult(
                    campaign_id,
                    "ready",
                    checkpoint_id,
                    message,
                    state,
                )

            if (
                not self.retry_stalled
                and policy.execution not in _MAINTENANCE_EXECUTIONS
                and policy.policy_id
                == str(state.get("campaign_last_policy") or "")
                and _campaign_has_pending_dynamic_route_hazard(state)
            ):
                message = (
                    f"{crowd_policy_id or policy.policy_id} encountered a "
                    "dynamic field hazard. Campaign checkpointed while "
                    "awaiting the field area reset."
                )
                storage.finish_campaign(campaign_id, status="ready", error=message)
                return CampaignResult(
                    campaign_id,
                    "ready",
                    checkpoint_id,
                    message,
                    state,
                )

            if (
                stalled >= self.spec.max_stalled_segments
                and policy.execution not in _MAINTENANCE_EXECUTIONS
                and policy.status != "research"
            ):
                if self.defer_stall_for_reset:
                    message = (
                        f"Campaign stalled for {stalled} completed segment(s). "
                        "Campaign checkpointed while awaiting the field area reset."
                    )
                    status = "ready"
                else:
                    message = f"Campaign stalled for {stalled} completed segment(s)."
                    status = "blocked"
                checkpoint_id = self._checkpoint(
                    storage,
                    campaign_id,
                    None,
                    phase=policy.policy_id,
                    reason="stalled",
                    state=state,
                )
                storage.finish_campaign(campaign_id, status=status, error=message)
                return CampaignResult(campaign_id, status, checkpoint_id, message, state)

            totals = storage.campaign_totals(campaign_id)
            budget_failure = _budget_failure(self.spec, totals)
            if budget_failure:
                checkpoint_id = self._checkpoint(
                    storage,
                    campaign_id,
                    None,
                    phase=policy.policy_id,
                    reason="budget_exhausted",
                    state=state,
                )
                storage.finish_campaign(campaign_id, status="blocked", error=budget_failure)
                return CampaignResult(campaign_id, "blocked", checkpoint_id, budget_failure, state)

            if not policy.executable:
                crowd_wait_policy_id = _active_crowded_research_policy_id(state)
                if (
                    not self.retry_stalled
                    and crowd_wait_policy_id is not None
                ):
                    message = (
                        f"{crowd_wait_policy_id} is temporarily crowded. "
                        "Campaign checkpointed while awaiting the field area "
                        "reset before retrying the source-vetted route."
                    )
                    storage.finish_campaign(
                        campaign_id,
                        status="ready",
                        error=message,
                    )
                    return CampaignResult(
                        campaign_id,
                        "ready",
                        checkpoint_id,
                        message,
                        state,
                    )
                pending_absence_policy_id = (
                    _next_pending_absent_research_retry_policy(state)
                )
                if (
                    self.defer_stall_for_reset
                    and pending_absence_policy_id is not None
                ):
                    message = (
                        "No executable current-band route is available; "
                        f"{pending_absence_policy_id} is at its final "
                        "reboot-scoped retry step. Campaign checkpointed while "
                        "awaiting the field area reset before reopening it."
                    )
                    storage.finish_campaign(
                        campaign_id,
                        status="ready",
                        error=message,
                    )
                    return CampaignResult(
                        campaign_id,
                        "ready",
                        checkpoint_id,
                        message,
                        state,
                    )
                message = policy.blocks_message(self.spec.character.character_class)
                checkpoint_id = self._checkpoint(
                    storage,
                    campaign_id,
                    None,
                    phase=policy.policy_id,
                    reason="awaiting_policy",
                    state=state,
                )
                storage.finish_campaign(campaign_id, status="blocked", error=message)
                return CampaignResult(campaign_id, "blocked", checkpoint_id, message, state)

            return await self._run_starter(
                storage,
                campaign_id,
                state,
                totals,
                policy,
            )

    def _needs_piercing_weapon(self, state: dict[str, Any]) -> bool:
        """Require a source-matched primary weapon for thief backstab."""
        if self.spec.character.character_class.casefold() != "thief":
            return False
        if self._gear_catalog is None:
            return False
        if not (
            isinstance(state.get("inventory"), (list, tuple, str))
            or isinstance(state.get("campaign_worn_equipment"), (list, tuple))
        ):
            return False
        if not _state_has_source_weapon_role(
            state,
            gear_catalog=self._gear_catalog,
            character_class=self.spec.character.character_class,
            subclass=self.spec.character.subclass,
            predicate=is_piercing_weapon,
            worn_only=True,
        ):
            return True
        # Stronger carried piercing weapons are handled by the dedicated
        # source-backed Forest/Thalos upgrade policies below. Keep this gate
        # limited to the generic requirement for a usable primary slot so
        # those policies remain ahead of rearm maintenance.
        return False

    def _needs_pounding_weapon(self, state: dict[str, Any]) -> bool:
        """Require the source-backed stun weapon for a class that exposes stun."""
        character_class = self.spec.character.character_class.casefold()
        subclass = (self.spec.character.subclass or "").casefold()
        source_stun_user = character_class == "warrior" or subclass == "bounty hunter"
        if not source_stun_user or _level(state) < 30:
            return False
        if self._gear_catalog is None:
            return False
        if not (
            isinstance(state.get("inventory"), (list, tuple, str))
            or isinstance(state.get("campaign_worn_equipment"), (list, tuple))
        ):
            return False
        # A Bounty Hunter with neither role weapon must acquire its piercing
        # primary first; the next maintenance pass can then add the mace.
        if subclass == "bounty hunter" and self._needs_piercing_weapon(state):
            return False
        return not _state_has_source_weapon_role(
            state,
            gear_catalog=self._gear_catalog,
            character_class=self.spec.character.character_class,
            subclass=self.spec.character.subclass,
            predicate=is_blunt_weapon,
        )

    def _select_source_ranked_candidate(
        self,
        state: dict[str, Any],
    ) -> HuntCandidate | None:
        """Rank all source areas for one executable current-band hunt."""
        level = _level(state)
        source_directory = Path("runs/dd4-source/server/area")
        if level < _SOURCE_RANKED_HUNT_POLICY.minimum_level:
            return None
        if not source_directory.is_dir():
            return None
        world = load_world_source(source_directory, include_all_areas=True)
        max_hp = state.get("max_hp")
        candidates = rank_hunt_candidates(
            world,
            character_level=level,
            boot_kill_counts=self._boot_kill_counts,
            include_xp_only=True,
            include_below_band=False,
            character_max_hp=(
                int(max_hp)
                if isinstance(max_hp, (int, float)) and max_hp > 0
                else None
            ),
            include_all_areas=True,
        )
        return _select_source_ranked_hunt_candidate(
            candidates,
            state,
            character_level=level,
        )

    def _policy_for_state(self, state: dict[str, Any]) -> ProgressionPolicy:
        empty_categories = set(
            state.get("campaign_empty_equipment_categories") or ()
        )
        school_exit_required = (
            str(state.get("room_vnum", "")) in _MUD_SCHOOL_ACCESSORY_ROOMS
        )
        recovered_own_corpse = _has_own_corpse_recovery(
            state,
            self.spec.character.name,
        )
        outfit_attempted_this_level = (
            int(state.get("campaign_outfit_attempted_level", -1))
            == _level(state)
        )
        sack_vault_reclaim_attempted_this_level = (
            int(state.get(_SACK_VAULT_RECLAIM_LEVEL_KEY, -1))
            == _level(state)
        )
        school_wrist_float_attempted_this_level = (
            int(state.get("campaign_school_wrist_float_attempted_level", -1))
            == _level(state)
        )
        gremlin_waist_attempted_this_level = (
            int(state.get("campaign_gremlin_waist_attempted_level", -1))
            == _level(state)
        )
        daycare_ring_attempted_this_level = (
            int(state.get("campaign_daycare_ring_attempted_level", -1))
            == _level(state)
            and (
                self._boot_id is None
                or state.get(_DAYCARE_RING_ATTEMPT_BOOT_KEY) == self._boot_id
            )
            and int(state.get(_DAYCARE_RING_COOLDOWN_KEY) or 0) > 0
        )
        war_dog_collar_attempted_this_level = (
            int(state.get("campaign_war_dog_collar_attempted_level", -1))
            == _level(state)
            and (
                self._boot_id is None
                or state.get(_WAR_DOG_COLLAR_ATTEMPT_BOOT_KEY) == self._boot_id
            )
            and int(state.get(_WAR_DOG_COLLAR_COOLDOWN_KEY) or 0) > 0
        )
        has_food = (
            school_exit_required
            or _has_campaign_food(
                state,
                gear_catalog=self._gear_catalog,
            )
        )
        needs_food_funding = bool(
            not school_exit_required
            and state.get(_PROVISION_FUNDING_REQUIRED_KEY)
            and not has_food
        )
        has_flight = (
            state.get("affects") is None
            or any(
                _state_has_active_affect(state.get("affects"), effect)
                for effect in ("fly", "levitation")
            )
        )
        needs_flight_funding = bool(
            not school_exit_required
            and state.get(_FLIGHT_FUNDING_REQUIRED_KEY)
            and not has_flight
        )
        vault_stow_items = _campaign_vault_stow_items(
            state,
            gear_catalog=self._gear_catalog,
        )
        can_retry_rejected_vault = (
            not state.get("vault_storage_rejected")
            or _has_oversized_capacity_stow_item(
                state,
                gear_catalog=self._gear_catalog,
                stow_items=vault_stow_items,
            )
        )
        handoff_policy_id = (
            str(state[_POLICY_HANDOFF_KEY])
            if state.get(_POLICY_HANDOFF_KEY)
            else _campaign_productive_sanctuary_handoff(
                state,
                character_class=self.spec.character.character_class,
            )
        )
        selected = policy_for(
            _level(state),
            self.spec.character.character_class,
            subclass=self.spec.character.subclass,
            has_large_sack=(
                self._historical_large_sack
                or _state_has_item(state.get("inventory"), "large sack")
            ),
            has_sellable_loot=(
                not school_exit_required
                and
                not recovered_own_corpse
                and
                _has_campaign_sellable_loot(
                    state,
                    gear_catalog=self._gear_catalog,
                )
            ),
            has_emergency_provision_sale=bool(
                needs_food_funding
                and _emergency_provision_potion_keyword(
                    state.get("inventory"),
                    self._gear_catalog,
                )
            ),
            needs_coin_deposit=bool(
                not school_exit_required
                and not recovered_own_corpse
                and _state_needs_coin_deposit(state)
            ),
            needs_capacity_relief=bool(
                not school_exit_required
                and
                not recovered_own_corpse
                and
                can_retry_rejected_vault
                and
                vault_stow_items
            ),
            has_food=has_food,
            needs_return_home=bool(
                school_exit_required
                and state.get(_PROVISION_FUNDING_REQUIRED_KEY)
            ),
            needs_provision_funding=bool(
                # A failed or unaffordable flight purchase must not strand a
                # stocked character at an unavailable flight gate. The
                # unresolved flight marker re-enters the same generic,
                # source-ranked money loop used for food funding.
                needs_food_funding or needs_flight_funding
            ),
            has_weapon=bool(
                school_exit_required
                or state.get("campaign_has_weapon", True)
            ),
            needs_piercing_weapon=self._needs_piercing_weapon(state),
            needs_basic_gear=bool(
                not school_exit_required
                and
                (
                    (
                        empty_categories & _BASIC_SHOP_CATEGORIES
                        and not outfit_attempted_this_level
                    )
                    or (
                        state.get(_SACK_VAULT_ITEMS_KEY)
                        and not sack_vault_reclaim_attempted_this_level
                    )
                )
            ),
            needs_body_gear_recovery=(
                not school_exit_required
                and
                "body" in empty_categories
                and outfit_attempted_this_level
                and _has_campaign_free_weight(
                    state,
                    _RECOVER_BASIC_BODY_REQUIRED_FREE_WEIGHT,
                )
                and int(
                    state.get("campaign_body_gear_attempted_level", -1)
                )
                != _level(state)
            ),
            needs_school_wrist_float=bool(
                school_exit_required
                or (
                    empty_categories & {"wrist", "float"}
                    and _has_campaign_free_weight(
                        state,
                        _RECOVER_SCHOOL_WRIST_FLOAT_REQUIRED_FREE_WEIGHT,
                    )
                )
            )
            and (
                school_exit_required
                or not school_wrist_float_attempted_this_level
            ),
            needs_gremlin_waist=(
                "waist" in empty_categories
                and not gremlin_waist_attempted_this_level
                and _has_campaign_free_weight(
                    state,
                    _RECOVER_GREMLIN_WAIST_REQUIRED_FREE_WEIGHT,
                )
            ),
            needs_daycare_ring=(
                "finger" in empty_categories
                and not daycare_ring_attempted_this_level
                and _has_campaign_free_weight(
                    state,
                    _RECOVER_DAYCARE_RING_REQUIRED_FREE_WEIGHT,
                )
            ),
            needs_war_dog_collar=(
                "neck" in empty_categories
                and not war_dog_collar_attempted_this_level
                and _has_campaign_free_weight(
                    state,
                    _RECOVER_WAR_DOG_COLLAR_REQUIRED_FREE_WEIGHT,
                )
            ),
            needs_foundry_set_circlet=(
                int(
                    state.get(_FOUNDRY_SET_CIRCLET_ATTEMPTED_LEVEL_KEY, -1)
                ) != _level(state)
                and _has_campaign_free_weight(
                    state,
                    _RECOVER_FOUNDRY_SET_CIRCLET_REQUIRED_FREE_WEIGHT,
                )
                and _campaign_has_item(state, "pink ice ring")
                and not _campaign_has_item(state, "silver circlet")
            ),
            needs_piercing_weapon_upgrade=_needs_piercing_weapon_upgrade(
                state,
                gear_catalog=self._gear_catalog,
                character_class=self.spec.character.character_class,
                subclass=self.spec.character.subclass,
            ),
            needs_intermediate_piercing_weapon_upgrade=(
                _needs_piercing_weapon_upgrade(
                    state,
                    gear_catalog=self._gear_catalog,
                    character_class=self.spec.character.character_class,
                    subclass=self.spec.character.subclass,
                    target_vnum=_INTERMEDIATE_PIERCING_WEAPON_UPGRADE_VNUM,
                )
            ),
            needs_pounding_weapon=self._needs_pounding_weapon(state),
            intermediate_piercing_weapon_upgrade_attempted=bool(
                int(
                    state.get(
                        _INTERMEDIATE_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY
                    )
                    or 0
                )
                > 0
            ),
            piercing_weapon_upgrade_attempted=bool(
                int(
                    state.get(_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY)
                    or 0
                )
                > 0
            ),
            movement_available=int(state.get("move") or 0),
            movement_capacity=int(state.get("max_move") or 0),
            has_sanctuary_potion=(
                int(
                    dict(state.get("combat_pouch_potions") or {}).get(
                        "purple", 0
                    )
                )
                > 0
                or _state_has_item(state.get("inventory"), "purple potion")
            ),
            has_acquired_sanctuary_potion=(
                self._historical_sanctuary_potion
                or bool(state.get("campaign_acquired_sanctuary_potion"))
            ),
            protection_recovery_required=_protection_recovery_required(state),
            has_flight=has_flight,
            can_attempt_flight_purchase=_state_copper_value(state) >= 90,
            flight_purchase_failed=bool(state.get("magic_shop_purchase_failed")),
            flight_loan_attempted=bool(
                state.get("campaign_flight_loan_attempted")
            ),
            flight_funding_retry_pending=bool(
                state.get(_FLIGHT_FUNDING_RETRY_KEY)
            ),
            boot_kill_counts=self._boot_kill_counts,
            policy_xp_deltas=self._policy_xp_deltas,
            productive_policy_ids=_state_productive_policy_ids(state),
            research_results=_campaign_research_results(state),
            research_absence_cooldowns=dict(
                state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
            ),
            research_crowd_cooldowns=dict(
                state.get(_RESEARCH_CROWD_COOLDOWN_KEY) or {}
            ),
            excluded_policy_ids=_campaign_below_band_policy_ids(
                state,
                level=_level(state),
                boot_id=state.get("world_boot_id"),
            ),
            world_boot_id=state.get("world_boot_id"),
            stalled_segments=int(state.get("campaign_stalled_segments", 0)),
            last_policy_id=(
                str(state["campaign_last_policy"])
                if state.get("campaign_last_policy")
                else None
            ),
            last_fastwalk_abort_reason=(
                str(state["campaign_fastwalk_abort_reason"])
                if state.get("campaign_fastwalk_abort_reason")
                else None
            ),
            handoff_policy_id=handoff_policy_id,
        )
        if (
            handoff_policy_id
            and selected.policy_id == handoff_policy_id
        ):
            return selected
        if _source_ranked_fallback_needed(state, selected):
            candidate = self._select_source_ranked_candidate(state)
            if candidate is not None:
                level = _level(state)
                policy_id = _source_ranked_policy_id(
                    candidate,
                    character_level=level,
                )
                state[_SOURCE_RANKED_CANDIDATE_KEY] = (
                    _source_ranked_candidate_record(
                        candidate,
                        character_level=level,
                    )
                )
                return replace(
                    _SOURCE_RANKED_HUNT_POLICY,
                    policy_id=policy_id,
                    minimum_level=level,
                    maximum_level=level,
                    summary=(
                        f"Run one bounded source-ranked hunt against "
                        f"{_source_ranked_target_identity(candidate)} in "
                        f"{candidate.area_file} room {candidate.room_vnum}."
                    ),
                    evidence=(
                        *_SOURCE_RANKED_HUNT_POLICY.evidence,
                        "Selected candidate: "
                        f"{candidate.area_file} mobile {candidate.mobile_vnum} "
                        f"room {candidate.room_vnum}, source levels "
                        f"{candidate.estimated_level_range[0]}-"
                        f"{candidate.estimated_level_range[1]}.",
                        "Source hazards: "
                        + ("; ".join(candidate.hazards) or "none"),
                    ),
                    practice_skill=selected.practice_skill,
                )
            state.pop(_SOURCE_RANKED_CANDIDATE_KEY, None)
            return replace(
                _SOURCE_RANKED_HUNT_POLICY,
                policy_id=f"{_SOURCE_RANKED_POLICY_PREFIX}unavailable-{_level(state)}",
                minimum_level=_level(state),
                maximum_level=_level(state),
                status="unavailable",
                execution=None,
                summary=(
                    "No source-safe current-band mobile is available after "
                    "the registered progression frontier and current-reboot "
                    "evidence gates were applied."
                ),
                practice_skill=selected.practice_skill,
            )
        return selected

    def _open_campaign(self, storage: RunStorage) -> tuple[int, dict[str, Any]]:
        campaign = None if self.force_new else storage.get_latest_campaign_for_config(
            self.config_path
        )
        if campaign is None:
            campaign_id = storage.create_campaign(
                name=self.spec.name,
                config_path=self.config_path,
                character_profile_path=self.spec.character_profile,
                target_level=self.spec.target_level,
            )
            return campaign_id, storage.get_latest_character_state(
                self.spec.character.name
            ) or {}

        campaign_id = int(campaign["id"])
        if int(campaign["target_level"]) != self.spec.target_level:
            storage.update_campaign_target_level(
                campaign_id,
                self.spec.target_level,
            )
        checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)
        if (
            checkpoint is not None
            and checkpoint["reason"] == "segment_failed"
            and checkpoint["run_id"] is None
        ):
            if _reconcile_failed_segment_progress(
                storage,
                campaign_id,
                checkpoint,
                character_name=self.spec.character.name,
            ):
                checkpoint = storage.get_latest_campaign_checkpoint(campaign_id)
        checkpoint_state = _checkpoint_state(checkpoint)
        live_state = storage.get_latest_character_state(self.spec.character.name)
        state = _newer_progress_state(checkpoint_state, live_state)
        flight_cooldown_state = _ensure_flight_purchase_retry_cooldown(
            storage,
            campaign_id,
            state,
            boot_id=self._boot_id,
        )
        if flight_cooldown_state != state and checkpoint is not None:
            storage.record_campaign_checkpoint(
                campaign_id,
                segment_id=checkpoint["segment_id"],
                run_id=checkpoint["run_id"],
                phase=str(checkpoint["phase"]),
                reason=_CAMPAIGN_METADATA_REPAIRED_REASON,
                state=flight_cooldown_state,
            )
        state = flight_cooldown_state
        state = _repair_reconciled_campaign_metadata(
            storage,
            campaign_id,
            checkpoint,
            state,
        )
        repaired_research_state = _repair_confirmed_research_kills(
            storage,
            campaign_id,
            state,
        )
        if repaired_research_state != state and checkpoint is not None:
            storage.record_campaign_checkpoint(
                campaign_id,
                segment_id=checkpoint["segment_id"],
                run_id=checkpoint["run_id"],
                phase=str(checkpoint["phase"]),
                reason=_CAMPAIGN_METADATA_REPAIRED_REASON,
                state=repaired_research_state,
            )
        state = repaired_research_state
        repaired_funding_state = _repair_provision_funding_history(
            storage,
            campaign_id,
            state,
        )
        if repaired_funding_state != state and checkpoint is not None:
            storage.record_campaign_checkpoint(
                campaign_id,
                segment_id=checkpoint["segment_id"],
                run_id=checkpoint["run_id"],
                phase=str(checkpoint["phase"]),
                reason=_CAMPAIGN_METADATA_REPAIRED_REASON,
                state=repaired_funding_state,
            )
        state = repaired_funding_state
        crowd_repaired_state = _clear_crowd_absence_marker(state)
        if crowd_repaired_state != state and checkpoint is not None:
            storage.record_campaign_checkpoint(
                campaign_id,
                segment_id=checkpoint["segment_id"],
                run_id=checkpoint["run_id"],
                phase=str(checkpoint["phase"]),
                reason=_CAMPAIGN_METADATA_REPAIRED_REASON,
                state=crowd_repaired_state,
            )
        state = crowd_repaired_state
        if (
            checkpoint is not None
            and checkpoint["reason"] == "segment_failed"
        ):
            state = _maintenance_failure_state(
                state,
                execution=str(checkpoint["phase"]),
                boot_id=self._boot_id,
            )
            if (
                checkpoint["phase"] == "restock-provisions"
                and not _has_campaign_food(
                    state,
                    gear_catalog=self._gear_catalog,
                )
            ):
                state = {
                    **state,
                    _PROVISION_FUNDING_REQUIRED_KEY: True,
                }
        if (
            checkpoint is not None
            and checkpoint["phase"] == "provision-funding"
            and not state.get(_PROVISION_FUNDING_REQUIRED_KEY)
        ):
            attempts = state.get(_PROVISION_FUNDING_ATTEMPTS_KEY)
            if (
                isinstance(attempts, list)
                and attempts
                and isinstance(attempts[-1], dict)
                and attempts[-1].get("completed_kill") is False
            ):
                state = {
                    **state,
                    _PROVISION_FUNDING_REQUIRED_KEY: True,
                }
        repaired_flight_state = _repair_exhausted_flight_funding_state(
            _repair_failed_flight_funding_state(
                state,
                checkpoint,
            ),
            has_sellable_loot=(
                _has_campaign_sellable_loot(
                    state,
                    gear_catalog=self._gear_catalog,
                )
                if state.get(_FLIGHT_FUNDING_RETRY_KEY)
                else None
            ),
        )
        if repaired_flight_state != state and checkpoint is not None:
            storage.record_campaign_checkpoint(
                campaign_id,
                segment_id=checkpoint["segment_id"],
                run_id=checkpoint["run_id"],
                phase=str(checkpoint["phase"]),
                reason=_CAMPAIGN_METADATA_REPAIRED_REASON,
                state=repaired_flight_state,
            )
        state = repaired_flight_state
        flight_purchase_failed = _campaign_flight_purchase_failed(
            storage,
            campaign_id,
            current_state=state,
        )
        if flight_purchase_failed is not None:
            state["magic_shop_purchase_failed"] = flight_purchase_failed
        observed_affects = state.get("affects")
        if observed_affects is not None:
            has_active_flight = any(
                _state_has_active_affect(observed_affects, effect)
                for effect in ("fly", "levitation")
            )
            if has_active_flight:
                state.pop(_FLIGHT_FUNDING_REQUIRED_KEY, None)
                state.pop(_FLIGHT_FUNDING_RETRY_KEY, None)
            elif (
                state.get("magic_shop_purchase_failed")
                and state.get("campaign_flight_loan_attempted")
                and not state.get(_FLIGHT_FUNDING_RETRY_KEY)
            ):
                state[_FLIGHT_FUNDING_REQUIRED_KEY] = True
        if checkpoint is not None and "campaign_last_policy" not in state:
            state["campaign_last_policy"] = str(checkpoint["phase"])
        equipment_run_id = (
            int(checkpoint["run_id"])
            if checkpoint is not None and checkpoint["run_id"] is not None
            else None
        )
        latest_character_run = _latest_character_run(
            storage,
            self.spec.character.name,
        )
        if (
            latest_character_run is not None
            and (
                equipment_run_id is None
                or int(latest_character_run["id"]) > equipment_run_id
            )
        ):
            equipment_run_id = int(latest_character_run["id"])
        weapon_loss = False
        if (
            equipment_run_id is not None
            and (weapon_loss := _run_has_unrecovered_weapon_loss(
                storage,
                equipment_run_id,
            ))
        ):
            state["campaign_has_weapon"] = False
        elif equipment_run_id is not None:
            state["campaign_has_weapon"] = True
        primary_weapon_slot: tuple[bool, str | None] | None = None
        if equipment_run_id is not None:
            empty_categories = _run_equipment_empty_categories(
                storage,
                equipment_run_id,
            )
            if empty_categories is not None:
                state["campaign_empty_equipment_categories"] = sorted(
                    empty_categories
                )
            worn_equipment = _run_worn_equipment_descriptions(
                storage,
                equipment_run_id,
            )
            if worn_equipment is not None:
                state["campaign_worn_equipment"] = worn_equipment
                if self._gear_catalog is not None and not weapon_loss:
                    state["campaign_has_weapon"] = any(
                        (
                            (item := self._gear_catalog.match(description))
                            is not None
                            and item_category(item) == "wield"
                        )
                        for description in worn_equipment
                    )
            primary_weapon_slot = _run_primary_weapon_slot(storage, equipment_run_id)
            if primary_weapon_slot is not None:
                state["campaign_primary_weapon"] = primary_weapon_slot[1]
        if (
            checkpoint is not None
            and (
                "campaign_empty_equipment_categories" not in state
                or "campaign_worn_equipment" not in state
                or "campaign_primary_weapon" not in state
            )
        ):
            for segment in reversed(storage.list_campaign_segments(campaign_id)):
                if segment["run_id"] is None:
                    continue
                run_id = int(segment["run_id"])
                if "campaign_empty_equipment_categories" not in state:
                    empty_categories = _run_equipment_empty_categories(
                        storage,
                        run_id,
                    )
                    if empty_categories is not None:
                        state["campaign_empty_equipment_categories"] = sorted(
                            empty_categories
                        )
                if "campaign_worn_equipment" not in state:
                    worn_equipment = _run_worn_equipment_descriptions(
                        storage,
                        run_id,
                    )
                    if worn_equipment is not None:
                        state["campaign_worn_equipment"] = worn_equipment
                if "campaign_primary_weapon" not in state:
                    primary_weapon_slot = _run_primary_weapon_slot(storage, run_id)
                    if primary_weapon_slot is not None:
                        state["campaign_primary_weapon"] = primary_weapon_slot[1]
                if (
                    "campaign_empty_equipment_categories" in state
                    and "campaign_worn_equipment" in state
                    and "campaign_primary_weapon" in state
                ):
                    break
        worn_equipment = state.get("campaign_worn_equipment")
        if (
            self._gear_catalog is not None
            and isinstance(worn_equipment, list)
            and not weapon_loss
        ):
            state["campaign_has_weapon"] = any(
                (
                    (item := self._gear_catalog.match(description)) is not None
                    and item_category(item) == "wield"
                )
                for description in worn_equipment
                if isinstance(description, str)
            )
        if primary_weapon_slot is not None and not weapon_loss:
            # The weapon slot is omitted from the general worn-equipment list.
            state["campaign_has_weapon"] = bool(
                primary_weapon_slot[0] and primary_weapon_slot[1]
            )
        if "wield" in set(state.get("campaign_empty_equipment_categories") or ()):
            # Prefer an explicit empty audit over stale direct wield metadata.
            state["campaign_has_weapon"] = False
        if (
            checkpoint is not None
            and _state_has_item(state.get("inventory"), "large sack")
            and not state.get(_SACK_VAULT_ITEMS_KEY)
        ):
            for segment in reversed(storage.list_campaign_segments(campaign_id)):
                if (
                    segment["phase"] == "midennir-sack-8-10"
                    and segment["run_id"] is not None
                ):
                    lodged_items = _run_successful_vault_lodges(
                        storage,
                        int(segment["run_id"]),
                    )
                    if lodged_items:
                        state[_SACK_VAULT_ITEMS_KEY] = list(lodged_items)
                    break
        if (
            checkpoint is not None
            and checkpoint["phase"] == "midennir-sack-8-10"
            and _state_has_item(state.get("inventory"), "large sack")
            and "finger"
            in set(state.get("campaign_empty_equipment_categories") or ())
        ):
            # Older checkpoints could record a ring attempt after mandatory
            # invisibility preparation aborted. Acquiring the sack proves that
            # preparation is repaired, so permit one fresh equipment pass.
            state.pop("campaign_daycare_ring_attempted_level", None)
            state.pop(_DAYCARE_RING_ATTEMPT_BOOT_KEY, None)
            state.pop(_DAYCARE_RING_COOLDOWN_KEY, None)
        if (
            checkpoint is not None
            and checkpoint["phase"] == "liquidate-loot"
            and checkpoint["reason"] == "segment_complete"
            and _LIQUIDATION_BASELINE_KEY not in state
        ):
            state[_LIQUIDATION_BASELINE_KEY] = list(
                _campaign_liquidation_signature(
                    state,
                    gear_catalog=self._gear_catalog,
                )
            )
        if (
            campaign["status"] == "success"
            and _level(state) >= self.spec.target_level
        ):
            return campaign_id, state
        storage.resume_campaign(campaign_id)
        return campaign_id, state

    async def _run_starter(
        self,
        storage: RunStorage,
        campaign_id: int,
        state: dict[str, Any],
        totals: Any,
        policy: ProgressionPolicy,
    ) -> CampaignResult:
        segment_id = storage.start_campaign_segment(
            campaign_id,
            phase=policy.policy_id,
            start_state=state,
        )
        adjusted_character = replace(
            self.spec.character,
            max_commands=min(
                self.spec.character.max_commands,
                self.spec.max_total_commands - int(totals["command_count"]),
            ),
            max_runtime=min(
                self.spec.character.max_runtime,
                self.spec.max_total_runtime - float(totals["duration_seconds"]),
                self.max_segment_runtime
                if self.max_segment_runtime is not None
                else float("inf"),
            ),
        )
        prior_run_ids = {
            int(run["id"])
            for run in storage.list_runs(limit=1000)
        }
        provision_funding_candidate = None
        source_ranked_hunt_candidate = None
        provision_funding_boot_id = state.get("world_boot_id") or self._boot_id
        if policy.execution == "provision-funding":
            provision_funding_candidate = _select_provision_funding_candidate(
                state,
                character_level=_level(state),
                boot_kill_counts=self._boot_kill_counts,
                boot_id=provision_funding_boot_id,
                source_directory=Path("runs/dd4-source/server/area"),
                gear_catalog=self._gear_catalog,
                prefer_completed_funding_candidate=bool(
                    state.get(_FLIGHT_FUNDING_REQUIRED_KEY)
                ),
            )
        elif policy.execution == "source-ranked-hunt":
            source_ranked_hunt_candidate = _source_ranked_candidate_from_record(
                state.get(_SOURCE_RANKED_CANDIDATE_KEY)
            )
        try:
            if self.segment_runner is not None:
                result = await self.segment_runner(adjusted_character, self.spec.character_profile)
            else:
                rejected_practice_skills = _campaign_rejected_practice_skills(
                    storage,
                    campaign_id,
                    level=_level(state),
                )
                result = await _run_policy_segment(
                    adjusted_character,
                    self.spec.character_profile,
                    policy,
                    practice_types_spent=_campaign_practice_types_spent(
                        storage,
                        campaign_id,
                        level=_level(state),
                    ),
                    rejected_practice_skills=rejected_practice_skills,
                    emergency_provision_sale=bool(
                        state.get(_PROVISION_FUNDING_REQUIRED_KEY)
                    ),
                    pounding_weapon_required=(
                        policy.execution == "rearm-weapon"
                        and self._needs_pounding_weapon(state)
                    ),
                    counterbalance_preparation_required=(
                        _campaign_counterbalance_preparation_required(
                            storage,
                            campaign_id,
                        )
                    ),
                    vault_stow_items=(
                        _campaign_vault_stow_items(
                            state,
                            gear_catalog=self._gear_catalog,
                        )
                        if policy.execution == "vault-spare-gear"
                        else ()
                    ),
                    vault_claim_items=(
                        _prioritize_sack_vault_claims(
                            state.get(_SACK_VAULT_ITEMS_KEY)
                        )
                        if policy.execution == "outfit-basic-gear"
                        else ()
                    ),
                    fastwalk_skip_target_sightings=_campaign_below_band_sightings(
                        state,
                        policy.policy_id,
                        level=_level(state),
                        boot_id=state.get("world_boot_id"),
                    ),
                    provision_funding_candidate=provision_funding_candidate,
                    source_ranked_hunt_candidate=source_ranked_hunt_candidate,
                )
        except Exception as exc:
            if self._is_controlled_runtime_boundary(exc):
                latest_character_state = (
                    storage.get_latest_character_state(self.spec.character.name)
                    or state
                )
                latest_state = {
                    **state,
                    **_campaign_segment_end_state(
                        state,
                        latest_character_state,
                        execution=policy.execution,
                    ),
                }
                if policy.execution == "borrow-flight":
                    latest_state["campaign_flight_loan_attempted"] = True
                latest_run = _latest_new_character_run(
                    storage,
                    self.spec.character.name,
                    prior_run_ids,
                ) or _latest_character_run(storage, self.spec.character.name)
                run_id = int(latest_run["id"]) if latest_run is not None else None
                boundary_objective_kills = (
                    _run_objective_kills(storage, run_id)
                    if run_id is not None
                    else []
                )
                boundary_target_observed = bool(boundary_objective_kills)
                if run_id is not None:
                    empty_categories = _run_equipment_empty_categories(
                        storage,
                        run_id,
                    )
                    if empty_categories is not None:
                        latest_state[
                            "campaign_empty_equipment_categories"
                        ] = sorted(empty_categories)
                    worn_equipment = _run_worn_equipment_descriptions(
                        storage,
                        run_id,
                    )
                    if worn_equipment is not None:
                        latest_state["campaign_worn_equipment"] = worn_equipment
                    primary_weapon = _run_primary_weapon_slot(storage, run_id)
                    if primary_weapon is not None:
                        latest_state["campaign_primary_weapon"] = primary_weapon[1]
                    terminal_state = _run_terminal_state(storage, run_id)
                    if terminal_state is not None:
                        boundary_target_observed = (
                            boundary_target_observed
                            or bool(
                                terminal_state.get("fastwalk_target_absent")
                                or terminal_state.get(
                                    "fastwalk_consider_outcomes"
                                )
                            )
                        )
                        abort_reason = terminal_state.get(
                            "fastwalk_abort_reason"
                        )
                        if isinstance(abort_reason, str) and abort_reason:
                            latest_state["campaign_fastwalk_abort_reason"] = (
                                abort_reason
                            )
                        else:
                            latest_state.pop(
                                "campaign_fastwalk_abort_reason",
                                None,
                            )
                if (
                    policy.execution == "provision-funding"
                    and provision_funding_candidate is not None
                    and boundary_target_observed
                ):
                    latest_state = _record_provision_funding_attempt(
                        latest_state,
                        candidate=provision_funding_candidate,
                        boot_id=provision_funding_boot_id,
                        completed_kill=bool(boundary_objective_kills),
                    )
                latest_state = _apply_flight_funding_state_transition(
                    state,
                    latest_state,
                    execution=policy.execution,
                    funding_completed=bool(
                        policy.execution == "provision-funding"
                        and boundary_objective_kills
                    ),
                )
                storage.finish_campaign_segment(
                    segment_id,
                    status="ready",
                    run_id=run_id,
                    end_state=latest_state,
                    command_count=(
                        storage.count_events(run_id, kind="command")
                        if run_id is not None
                        else None
                    ),
                    duration_seconds=(
                        _run_duration(latest_run) if latest_run is not None else None
                    ),
                    error=str(exc),
                )
                checkpoint_id = self._checkpoint(
                    storage,
                    campaign_id,
                    segment_id,
                    phase=policy.policy_id,
                    reason="segment_runtime_cap",
                    state=latest_state,
                    run_id=run_id,
                )
                message = (
                    f"{policy.policy_id} segment reached the configured "
                    f"{self.max_segment_runtime:g}-second runtime cap and "
                    "checkpointed for resumption."
                )
                storage.finish_campaign(campaign_id, status="ready", error=message)
                return CampaignResult(
                    campaign_id,
                    "ready",
                    checkpoint_id,
                    message,
                    latest_state,
                )
            latest_run = _latest_new_character_run(
                storage,
                self.spec.character.name,
                prior_run_ids,
            )
            run_id = int(latest_run["id"]) if latest_run is not None else None
            objective_kills = (
                _run_objective_kills(storage, run_id)
                if run_id is not None
                else None
            )
            funding_target_observed = bool(objective_kills)
            if policy.execution == "provision-funding" and run_id is not None:
                funding_run_state = _run_latest_state(storage, run_id) or {}
                funding_target_observed = funding_target_observed or bool(
                    funding_run_state.get("campaign_fastwalk_target_absent")
                    or funding_run_state.get("campaign_fastwalk_consider_outcomes")
                )
            if run_id is not None and isinstance(objective_kills, list) and objective_kills:
                run_state = _run_latest_state(storage, run_id)
                latest_state = {
                    **state,
                    **_campaign_segment_end_state(
                        state,
                        run_state or state,
                        execution=policy.execution,
                    ),
                    "campaign_completed_kills": objective_kills,
                    "campaign_objective_kills": objective_kills,
                    "campaign_last_policy": policy.policy_id,
                    "campaign_policy_revision": _CAMPAIGN_POLICY_REVISION,
                }
                if policy.execution == "borrow-flight":
                    latest_state["campaign_flight_loan_attempted"] = True
                if (
                    policy.execution == "provision-funding"
                    and provision_funding_candidate is not None
                ):
                    latest_state = _record_provision_funding_attempt(
                        latest_state,
                        candidate=provision_funding_candidate,
                        boot_id=provision_funding_boot_id,
                        completed_kill=True,
                    )
                latest_state = _apply_flight_funding_state_transition(
                    state,
                    latest_state,
                    execution=policy.execution,
                    funding_completed=bool(objective_kills),
                )
                message = (
                    f"{policy.policy_id} segment failed after recording "
                    f"{len(objective_kills)} objective kill(s); progress "
                    "was reconciled for resumption: "
                    f"{exc}"
                )
                storage.finish_campaign_segment(
                    segment_id,
                    status="ready",
                    run_id=run_id,
                    end_state=latest_state,
                    command_count=storage.count_events(run_id, kind="command"),
                    duration_seconds=_run_duration(latest_run),
                    error=str(exc),
                )
                checkpoint_id = self._checkpoint(
                    storage,
                    campaign_id,
                    segment_id,
                    phase=policy.policy_id,
                    reason="segment_failed_progress_reconciled",
                    state=latest_state,
                    run_id=run_id,
                )
                storage.finish_campaign(campaign_id, status="ready", error=message)
                return CampaignResult(
                    campaign_id,
                    "ready",
                    checkpoint_id,
                    message,
                    latest_state,
                )

            message = f"{policy.policy_id} segment failed: {exc}"
            failed_state = _maintenance_failure_state(
                state,
                execution=policy.execution,
                boot_id=self._boot_id,
                error=str(exc),
            )
            if (
                policy.execution == "provision-funding"
                and provision_funding_candidate is not None
                and funding_target_observed
            ):
                failed_state = _record_provision_funding_attempt(
                    failed_state,
                    candidate=provision_funding_candidate,
                    boot_id=provision_funding_boot_id,
                    completed_kill=False,
                )
            failed_state = _apply_flight_funding_state_transition(
                state,
                failed_state,
                execution=policy.execution,
                funding_completed=False,
            )
            if policy.execution == "borrow-flight":
                failed_state["campaign_flight_loan_attempted"] = True
            if policy.execution == "upgrade-piercing-weapon":
                failed_state[_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY] = (
                    _PIERCING_WEAPON_UPGRADE_COOLDOWN_SEGMENTS
                )
                if self._boot_id is not None:
                    failed_state[_PIERCING_WEAPON_UPGRADE_BOOT_KEY] = (
                        self._boot_id
                    )
                if (
                    policy.policy_id
                    == "thalos-long-dagger-upgrade-10-29"
                ):
                    failed_state[
                        _INTERMEDIATE_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY
                    ] = (
                        _INTERMEDIATE_PIERCING_WEAPON_UPGRADE_COOLDOWN_SEGMENTS
                    )
            storage.finish_campaign_segment(
                segment_id,
                status="failed",
                run_id=None,
                end_state=failed_state,
                command_count=None,
                duration_seconds=None,
                error=message,
            )
            checkpoint_id = self._checkpoint(
                storage,
                campaign_id,
                segment_id,
                phase=policy.policy_id,
                reason="segment_failed",
                state=failed_state,
            )
            storage.finish_campaign(campaign_id, status="failed", error=message)
            return CampaignResult(
                campaign_id,
                "failed",
                checkpoint_id,
                message,
                failed_state,
            )

        command_count = storage.count_events(result.run_id, kind="command")
        duration_seconds = _run_duration(storage.get_run(result.run_id))
        end_state = _campaign_segment_end_state(
            state,
            result.final_state,
            execution=policy.execution,
        )
        if policy.execution == "restock":
            end_state.pop(_PROVISION_FUNDING_REQUIRED_KEY, None)
        if (
            policy.execution == "sell-loot"
            and state.get(_PROVISION_FUNDING_REQUIRED_KEY)
            and storage.list_loot_sales_for_run(result.run_id)
        ):
            # A completed emergency sale has converted protected loot into
            # spendable currency. Let the next campaign selection run the
            # ordinary restock policy; if that purchase is still unaffordable,
            # restock will set the funding marker again.
            end_state.pop(_PROVISION_FUNDING_REQUIRED_KEY, None)
        if policy.execution == "borrow-flight":
            end_state["campaign_flight_loan_attempted"] = True
        empty_categories = _run_equipment_empty_categories(storage, result.run_id)
        if empty_categories is not None:
            end_state["campaign_empty_equipment_categories"] = sorted(
                empty_categories
            )
        elif "campaign_empty_equipment_categories" in state:
            end_state["campaign_empty_equipment_categories"] = state[
                "campaign_empty_equipment_categories"
            ]
        worn_equipment = _run_worn_equipment_descriptions(storage, result.run_id)
        if worn_equipment is not None:
            end_state["campaign_worn_equipment"] = worn_equipment
        elif "campaign_worn_equipment" in state:
            end_state["campaign_worn_equipment"] = state[
                "campaign_worn_equipment"
            ]
        primary_weapon = _run_primary_weapon_slot(storage, result.run_id)
        if primary_weapon is not None:
            end_state["campaign_primary_weapon"] = primary_weapon[1]
            end_state["campaign_has_weapon"] = bool(
                primary_weapon[0] and primary_weapon[1]
            )
        elif "campaign_primary_weapon" in state:
            end_state["campaign_primary_weapon"] = state[
                "campaign_primary_weapon"
            ]
        if "wield" in set(end_state.get("campaign_empty_equipment_categories") or ()):
            # A split or stale wield acknowledgement must not make an empty
            # primary slot look ready for the next progression segment.
            end_state["campaign_has_weapon"] = False
        fastwalk_abort_reason = end_state.get("campaign_fastwalk_abort_reason")
        preparation_aborted = bool(
            isinstance(fastwalk_abort_reason, str)
            and "invisibility at the safe origin" in fastwalk_abort_reason
        )
        # A first live segment can discover the current reboot after the
        # campaign opened. Prefer that evidence when scoping retry cooldowns.
        segment_boot_id = end_state.get("world_boot_id") or self._boot_id
        end_state = _merge_campaign_below_band_policy_exclusions(
            state,
            end_state,
            policy=policy,
            level=_level(end_state),
            boot_id=segment_boot_id,
        )
        if policy.execution == "outfit-basic-gear":
            end_state["campaign_outfit_attempted_level"] = _level(end_state)
            if state.get(_SACK_VAULT_ITEMS_KEY):
                end_state[_SACK_VAULT_RECLAIM_LEVEL_KEY] = _level(end_state)
            claimed_items = {
                str(item).casefold()
                for item in result.final_state.get("vault_claimed_items") or ()
            }
            pending_items = [
                str(item)
                for item in state.get(_SACK_VAULT_ITEMS_KEY) or ()
                if str(item).casefold() not in claimed_items
            ]
            if pending_items:
                end_state[_SACK_VAULT_ITEMS_KEY] = pending_items
            else:
                end_state.pop(_SACK_VAULT_ITEMS_KEY, None)
        if policy.execution == "recover-basic-body":
            end_state["campaign_body_gear_attempted_level"] = _level(end_state)
        if policy.execution == "recover-foundry-set-circlet":
            end_state[_FOUNDRY_SET_CIRCLET_ATTEMPTED_LEVEL_KEY] = _level(
                end_state
            )
        if (
            policy.execution == "recover-school-wrist-float"
            and not (
                set(end_state.get("campaign_empty_equipment_categories") or ())
                & {"wrist", "float"}
            )
        ):
            end_state["campaign_school_wrist_float_attempted_level"] = _level(
                end_state
            )
        if policy.execution == "recover-gremlin-waist":
            end_state["campaign_gremlin_waist_attempted_level"] = _level(end_state)
        if policy.execution == "recover-daycare-ring":
            if "finger" in set(
                end_state.get("campaign_empty_equipment_categories") or ()
            ) and not preparation_aborted:
                end_state["campaign_daycare_ring_attempted_level"] = _level(
                    end_state
                )
                end_state[_DAYCARE_RING_COOLDOWN_KEY] = (
                    _DAYCARE_RING_COOLDOWN_SEGMENTS
                )
                if segment_boot_id is not None:
                    end_state[_DAYCARE_RING_ATTEMPT_BOOT_KEY] = segment_boot_id
            else:
                end_state.pop("campaign_daycare_ring_attempted_level", None)
                end_state.pop(_DAYCARE_RING_ATTEMPT_BOOT_KEY, None)
                end_state.pop(_DAYCARE_RING_COOLDOWN_KEY, None)
        if policy.execution == "recover-war-dog-collar":
            if "neck" in set(
                end_state.get("campaign_empty_equipment_categories") or ()
            ):
                end_state["campaign_war_dog_collar_attempted_level"] = _level(
                    end_state
                )
                end_state[_WAR_DOG_COLLAR_COOLDOWN_KEY] = (
                    _WAR_DOG_COLLAR_COOLDOWN_SEGMENTS
                )
                if segment_boot_id is not None:
                    end_state[_WAR_DOG_COLLAR_ATTEMPT_BOOT_KEY] = segment_boot_id
            else:
                end_state.pop("campaign_war_dog_collar_attempted_level", None)
                end_state.pop(_WAR_DOG_COLLAR_ATTEMPT_BOOT_KEY, None)
                end_state.pop(_WAR_DOG_COLLAR_COOLDOWN_KEY, None)
        if (
            policy.execution == "midennir-sack"
            and _state_has_item(end_state.get("inventory"), "large sack")
        ):
            lodged_items = result.final_state.get("vault_lodged_items") or ()
            if lodged_items:
                end_state[_SACK_VAULT_ITEMS_KEY] = list(
                    dict.fromkeys(str(item) for item in lodged_items)
                )
            if "finger" in set(
                end_state.get("campaign_empty_equipment_categories") or ()
            ):
                end_state.pop("campaign_daycare_ring_attempted_level", None)
                end_state.pop(_DAYCARE_RING_ATTEMPT_BOOT_KEY, None)
                end_state.pop(_DAYCARE_RING_COOLDOWN_KEY, None)
        xp_delta = _xp_delta(state, end_state)
        objective_kills = _run_objective_kills(storage, result.run_id)
        if isinstance(objective_kills, list) and objective_kills:
            # Research promotion must see the authoritative kill record from
            # the run before it evaluates whether a hunt completed.
            end_state["campaign_completed_kills"] = objective_kills
            end_state["campaign_objective_kills"] = objective_kills
            if policy.execution and policy.execution.endswith("-hunt"):
                end_state[_LAST_PRODUCTIVE_POLICY_KEY] = policy.policy_id
                if xp_delta > 0:
                    end_state = _with_productive_policy_history(
                        end_state,
                        policy_ids=(policy.policy_id,),
                        boot_id=segment_boot_id or end_state.get("world_boot_id"),
                    )
        if policy.execution == "provision-funding":
            if provision_funding_candidate is not None:
                end_state = _record_provision_funding_attempt(
                    end_state,
                    candidate=provision_funding_candidate,
                    boot_id=segment_boot_id,
                    completed_kill=bool(objective_kills),
                )
        end_state = _apply_flight_funding_state_transition(
            state,
            end_state,
            execution=policy.execution,
            funding_completed=bool(
                policy.execution == "provision-funding" and objective_kills
            ),
        )
        end_state = _merge_campaign_research_result(
            state,
            end_state,
            policy=policy,
        )
        end_state = _merge_protection_recovery_metadata(
            end_state,
            policy=policy,
            xp_delta=xp_delta,
        )
        if xp_delta > 0:
            end_state = _clear_absent_research_results(
                end_state,
                except_policy_id=policy.policy_id,
            )
        arena_depleted = (
            policy.execution == "arena"
            and xp_delta <= 0
            and not objective_kills
        )
        research_target_absent = bool(
            policy.status == "research"
            and result.final_state.get("campaign_fastwalk_target_absent")
        )
        verified_field_target_absent = bool(
            policy.status == "verified"
            and policy.execution not in _MAINTENANCE_EXECUTIONS
            and policy.execution not in {"starter", "arena"}
            and result.final_state.get("campaign_fastwalk_target_absent")
        )
        if policy.execution == "upgrade-piercing-weapon":
            if _needs_piercing_weapon_upgrade(
                end_state,
                gear_catalog=self._gear_catalog,
                character_class=self.spec.character.character_class,
                subclass=self.spec.character.subclass,
            ):
                end_state[_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY] = (
                    _PIERCING_WEAPON_UPGRADE_COOLDOWN_SEGMENTS
                )
                if segment_boot_id is not None:
                    end_state[_PIERCING_WEAPON_UPGRADE_BOOT_KEY] = segment_boot_id
            else:
                end_state.pop(_PIERCING_WEAPON_UPGRADE_BOOT_KEY, None)
                end_state.pop(_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY, None)
        intermediate_upgrade = (
            policy.policy_id == "thalos-long-dagger-upgrade-10-29"
        )
        if intermediate_upgrade:
            if _needs_piercing_weapon_upgrade(
                end_state,
                gear_catalog=self._gear_catalog,
                character_class=self.spec.character.character_class,
                subclass=self.spec.character.subclass,
                target_vnum=_INTERMEDIATE_PIERCING_WEAPON_UPGRADE_VNUM,
            ):
                end_state[
                    _INTERMEDIATE_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY
                ] = _INTERMEDIATE_PIERCING_WEAPON_UPGRADE_COOLDOWN_SEGMENTS
            else:
                end_state.pop(
                    _INTERMEDIATE_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY,
                    None,
                )
        if policy.execution != "recover-daycare-ring":
            end_state = _advance_daycare_ring_cooldown(
                end_state,
                execution=policy.execution,
                xp_delta=xp_delta,
            )
        if policy.execution != "recover-war-dog-collar":
            end_state = _advance_war_dog_collar_cooldown(
                end_state,
                execution=policy.execution,
                xp_delta=xp_delta,
            )
        if policy.execution != "upgrade-piercing-weapon":
            end_state = _advance_piercing_weapon_upgrade_cooldown(
                end_state,
                execution=policy.execution,
                xp_delta=xp_delta,
            )
        if policy.execution not in {"buy-flight", "buy-flight-potion"}:
            end_state = _advance_flight_purchase_cooldown(
                end_state,
                execution=policy.execution,
                xp_delta=xp_delta,
            )
        if not intermediate_upgrade:
            end_state = _advance_intermediate_piercing_weapon_upgrade_cooldown(
                end_state,
                execution=policy.execution,
                xp_delta=xp_delta,
            )
        self._policy_xp_deltas[policy.policy_id] = xp_delta
        if result.status != "success":
            message = f"starter segment returned status {result.status}"
            storage.finish_campaign_segment(
                segment_id,
                status="failed",
                run_id=result.run_id,
                end_state=end_state,
                command_count=command_count,
                duration_seconds=duration_seconds,
                error=message,
            )
            checkpoint_id = self._checkpoint(
                storage,
                campaign_id,
                segment_id,
                phase=policy.policy_id,
                reason="segment_failed",
                state=end_state,
                run_id=result.run_id,
            )
            storage.finish_campaign(campaign_id, status="failed", error=message)
            return CampaignResult(campaign_id, "failed", checkpoint_id, message, end_state)

        storage.finish_campaign_segment(
            segment_id,
            status=result.status,
            run_id=result.run_id,
            end_state=end_state,
            command_count=command_count,
            duration_seconds=duration_seconds,
        )
        stalled = (
            0
            if (
                policy.execution in _MAINTENANCE_EXECUTIONS
                or policy.status == "research"
                or arena_depleted
            )
            else _stalled_count(
                state,
                end_state,
                storage.get_latest_campaign_checkpoint(campaign_id),
            )
        )
        checkpoint_state = {
            **end_state,
            "campaign_stalled_segments": stalled,
            "campaign_policy_revision": _CAMPAIGN_POLICY_REVISION,
            "campaign_last_policy": (
                state.get("campaign_last_policy")
                if policy.execution in _MAINTENANCE_EXECUTIONS
                else policy.policy_id
            ),
            "campaign_has_weapon": (
                bool(
                    end_state.get(
                        "campaign_has_weapon",
                        state.get("campaign_has_weapon", True),
                    )
                )
            ),
        }
        previous_liquidation_baseline = state.get(_LIQUIDATION_BASELINE_KEY)
        if policy.execution in {"sell-loot", "rearm-weapon"}:
            checkpoint_state[_LIQUIDATION_BASELINE_KEY] = list(
                _campaign_liquidation_signature(
                    end_state,
                    gear_catalog=self._gear_catalog,
                )
            )
        elif previous_liquidation_baseline is not None:
            checkpoint_state[_LIQUIDATION_BASELINE_KEY] = (
                previous_liquidation_baseline
            )
        checkpoint_id = self._checkpoint(
            storage,
            campaign_id,
            segment_id,
            phase=policy.policy_id,
            reason=(
                "segment_preparation_aborted"
                if preparation_aborted
                else "segment_complete"
            ),
            state=checkpoint_state,
            run_id=result.run_id,
        )

        if _level(end_state) >= self.spec.target_level:
            storage.finish_campaign(campaign_id, status="success")
            return CampaignResult(
                campaign_id,
                "success",
                checkpoint_id,
                f"Target level {self.spec.target_level} reached.",
                end_state,
            )

        if preparation_aborted:
            message = (
                f"{policy.policy_id} returned safely before field departure: "
                f"{fastwalk_abort_reason}. Campaign checkpointed to repair "
                "mandatory preparation."
            )
            storage.finish_campaign(campaign_id, status="ready", error=message)
            return CampaignResult(
                campaign_id,
                "ready",
                checkpoint_id,
                message,
                end_state,
            )

        if arena_depleted:
            message = (
                f"{policy.policy_id} arena circuit was empty at level "
                f"{_level(end_state)}. Campaign checkpointed while awaiting "
                "the Mud School area reset."
            )
            storage.finish_campaign(campaign_id, status="ready", error=message)
            return CampaignResult(
                campaign_id,
                "ready",
                checkpoint_id,
                message,
                end_state,
            )

        crowded_field = any(
            str(fastwalk_abort_reason or "").startswith(prefix)
            for prefix in _FIELD_CROWD_ABORT_PREFIXES
        )
        if crowded_field:
            message = (
                f"{policy.policy_id} encountered a crowded field room. "
                "Campaign checkpointed while awaiting the field area reset."
            )
            storage.finish_campaign(campaign_id, status="ready", error=message)
            return CampaignResult(
                campaign_id,
                "ready",
                checkpoint_id,
                message,
                end_state,
            )

        next_policy = self._policy_for_state(end_state)
        research_absence_wait = research_target_absent and (
            (
                _is_research_absence_retry_policy(policy.policy_id)
                and (
                    policy.policy_id
                    != _MORIA_SANCTUARY_THIEF_LEVEL_SEVENTEEN_POLICY_ID
                    or next_policy.policy_id == policy.policy_id
                )
                and (
                    next_policy.policy_id == policy.policy_id
                    or not next_policy.executable
                )
            )
            or not next_policy.executable
        )
        if research_absence_wait or verified_field_target_absent:
            if verified_field_target_absent:
                message = (
                    f"{policy.policy_id} field circuit found no registered "
                    "target. Campaign checkpointed while awaiting the field "
                    "area reset."
                )
            else:
                message = (
                    f"{policy.policy_id} reached its verified destination but the "
                    "reset target was absent. Campaign checkpointed while awaiting "
                    "the field area reset."
                )
            storage.finish_campaign(campaign_id, status="ready", error=message)
            return CampaignResult(
                campaign_id,
                "ready",
                checkpoint_id,
                message,
                end_state,
            )

        if stalled >= self.spec.max_stalled_segments:
            if self.defer_stall_for_reset:
                message = (
                    f"Campaign stalled for {stalled} completed segment(s). "
                    "Campaign checkpointed while awaiting the field area reset."
                )
                status = "ready"
            else:
                message = f"Campaign stalled for {stalled} completed segment(s)."
                status = "blocked"
            storage.finish_campaign(campaign_id, status=status, error=message)
            return CampaignResult(campaign_id, status, checkpoint_id, message, end_state)

        next_policy = self._policy_for_state(checkpoint_state)
        if next_policy.executable:
            message = (
                f"{policy.policy_id} segment completed at level {_level(end_state)}. "
                "Campaign checkpointed for the next verified segment."
            )
        elif _campaign_should_await_research_reset(checkpoint_state) or (
            self.defer_stall_for_reset
            and _next_pending_absent_research_retry_policy(checkpoint_state)
            is not None
        ):
            message = (
                f"{policy.policy_id} completed without an executable current-"
                "band route. Campaign checkpointed while awaiting the field "
                "area reset before retrying the bounded research route."
            )
        else:
            message = next_policy.blocks_message(self.spec.character.character_class)
        storage.finish_campaign(campaign_id, status="ready", error=message)
        return CampaignResult(campaign_id, "ready", checkpoint_id, message, end_state)

    def _is_controlled_runtime_boundary(self, exc: Exception) -> bool:
        return (
            self.max_segment_runtime is not None
            and isinstance(exc, TimeoutError)
            and str(exc)
            == f"Starter bot exceeded {self.max_segment_runtime:g} second runtime"
        )

    def _checkpoint(
        self,
        storage: RunStorage,
        campaign_id: int,
        segment_id: int | None,
        *,
        phase: str,
        reason: str,
        state: dict[str, Any],
        run_id: int | None = None,
    ) -> int:
        return storage.record_campaign_checkpoint(
            campaign_id,
            segment_id=segment_id,
            run_id=run_id,
            phase=phase,
            reason=reason,
            state=state,
        )


async def run_campaign_file(
    path: str | Path,
    *,
    force_new: bool = False,
    segments: int = 1,
    reset_retries: int | None = None,
    reset_wait: float = 300.0,
    max_segment_runtime: float | None = None,
) -> CampaignResult:
    if segments < 1:
        raise ValueError("segments must be positive")
    if reset_retries is None:
        # A bounded live invocation must return after its work unit. Waiting
        # for a reboot-scoped area reset is opt-in in that mode.
        reset_retries = 0 if max_segment_runtime is not None else segments
    if reset_retries < 0:
        raise ValueError("reset_retries cannot be negative")
    if reset_retries and reset_wait <= 0:
        raise ValueError("reset_wait must be positive when reset_retries is set")
    if max_segment_runtime is not None and max_segment_runtime <= 0:
        raise ValueError("max_segment_runtime must be positive")
    config_path = Path(path)
    spec = load_campaign_spec(config_path)
    runner_options: dict[str, float | bool] = {
        "force_new": force_new,
        "defer_stall_for_reset": bool(reset_retries),
    }
    if max_segment_runtime is not None:
        runner_options["max_segment_runtime"] = max_segment_runtime
    result = await CampaignRunner(spec, config_path, **runner_options).run()
    normal_segments = 1
    retries_remaining = reset_retries
    while True:
        if result.awaiting_area_reset:
            if retries_remaining <= 0:
                break
            await asyncio.sleep(reset_wait)
            retries_remaining -= 1
            retry_options: dict[str, float | bool] = {
                "defer_stall_for_reset": True,
                "retry_stalled": True,
            }
            if max_segment_runtime is not None:
                retry_options["max_segment_runtime"] = max_segment_runtime
            result = await CampaignRunner(
                spec,
                config_path,
                **retry_options,
            ).run()
            continue
        if not result.ready_for_next_segment or normal_segments >= segments:
            break
        continuation_options: dict[str, float | bool] = {
            "defer_stall_for_reset": bool(reset_retries),
        }
        if max_segment_runtime is not None:
            continuation_options["max_segment_runtime"] = max_segment_runtime
        result = await CampaignRunner(
            spec,
            config_path,
            **continuation_options,
        ).run()
        normal_segments += 1
    return result


def load_campaign_spec(path: str | Path) -> CampaignSpec:
    config_path = Path(path)
    return CampaignSpec.from_mapping(load_yaml_mapping(config_path), path=config_path)


def _campaign_practice_types_spent(
    storage: RunStorage,
    campaign_id: int,
    *,
    level: int,
) -> frozenset[str]:
    spent: set[str] = set()
    for segment in storage.list_campaign_segments(campaign_id):
        if segment["run_id"] is None:
            continue
        start_state = json.loads(segment["start_state_json"] or "{}")
        if _level(start_state) != level:
            continue
        for event in storage.list_events(int(segment["run_id"])):
            if event["kind"] != "game_event":
                continue
            payload = json.loads(event["payload_json"])
            if payload.get("type") != "training_completed":
                continue
            practice_type = str(payload.get("data", {}).get("practice_type", ""))
            if practice_type in {"physical", "intellectual"}:
                spent.add(practice_type)
    return frozenset(spent)


def _campaign_rejected_practice_skills(
    storage: RunStorage,
    campaign_id: int,
    *,
    level: int,
) -> frozenset[str]:
    rejected: set[str] = set()
    permanent_trainer_reasons = {
        "trainer level requirement",
        "trainer proficiency cap",
    }
    for segment in storage.list_campaign_segments(campaign_id):
        if segment["run_id"] is None:
            continue
        start_state = json.loads(segment["start_state_json"] or "{}")
        if _level(start_state) != level:
            continue
        for event in storage.list_events(int(segment["run_id"])):
            if event["kind"] != "game_event":
                continue
            payload = json.loads(event["payload_json"])
            if payload.get("type") != "training_rejected":
                continue
            data = payload.get("data", {})
            if data.get("reason") not in permanent_trainer_reasons:
                continue
            skill = str(data.get("skill", "")).strip().casefold()
            if skill:
                rejected.add(skill)
    return frozenset(rejected)


def _campaign_counterbalance_preparation_required(
    storage: RunStorage,
    campaign_id: int,
) -> bool:
    required = False
    for segment in storage.list_campaign_segments(campaign_id):
        if segment["run_id"] is None:
            continue
        for event in storage.list_events(int(segment["run_id"])):
            if event["kind"] != "game_event":
                continue
            payload = json.loads(event["payload_json"])
            data = payload.get("data", {})
            if str(data.get("skill", "")).casefold() != "counterbalance":
                continue
            if payload.get("type") == "training_completed":
                required = True
            elif payload.get("type") == "equipment_preparation_completed":
                required = False
    return required


def _campaign_flight_purchase_failed(
    storage: RunStorage,
    campaign_id: int,
    *,
    current_state: dict[str, Any] | None = None,
) -> bool | None:
    """Return whether the latest failed flight purchase still applies."""
    state = _latest_flight_purchase_state(storage, campaign_id)
    if state is None:
        return None
    failed = bool(state.get("magic_shop_purchase_failed"))
    if not failed or current_state is None:
        return failed
    failed_boot = state.get("world_boot_id")
    current_boot = current_state.get("world_boot_id")
    if failed_boot and current_boot and failed_boot != current_boot:
        return False
    if int(current_state.get(_FLIGHT_PURCHASE_COOLDOWN_KEY) or 0) > 0:
        return True
    return _state_copper_value(current_state) <= _state_copper_value(state)


def _latest_flight_purchase_state(
    storage: RunStorage,
    campaign_id: int,
) -> dict[str, Any] | None:
    """Return the latest completed flight-purchase segment state."""
    for segment in reversed(storage.list_campaign_segments(campaign_id)):
        if segment["phase"] != "buy-flight-potion":
            continue
        if segment["status"] != "success" or not segment["end_state_json"]:
            continue
        return json.loads(segment["end_state_json"])
    return None


def _ensure_flight_purchase_retry_cooldown(
    storage: RunStorage,
    campaign_id: int,
    state: dict[str, Any],
    *,
    boot_id: int | None = None,
) -> dict[str, Any]:
    """Migrate a same-reboot legacy purchase failure into bounded retry state."""
    if _FLIGHT_PURCHASE_COOLDOWN_KEY in state:
        return state
    failed_state = _latest_flight_purchase_state(storage, campaign_id)
    if not failed_state or not failed_state.get("magic_shop_purchase_failed"):
        return state
    failed_boot = failed_state.get("world_boot_id")
    current_boot = state.get("world_boot_id") or boot_id
    if failed_boot and current_boot and failed_boot != current_boot:
        return state
    repaired = dict(state)
    repaired[_FLIGHT_PURCHASE_COOLDOWN_KEY] = (
        _FLIGHT_PURCHASE_COOLDOWN_SEGMENTS
    )
    return repaired


async def _run_policy_segment(
    spec: CharacterSpec,
    profile_path: Path,
    policy: ProgressionPolicy,
    *,
    practice_types_spent: frozenset[str] = frozenset(),
    rejected_practice_skills: frozenset[str] = frozenset(),
    pounding_weapon_required: bool = False,
    counterbalance_preparation_required: bool = False,
    vault_stow_items: tuple[str, ...] = (),
    vault_claim_items: tuple[str, ...] = (),
    fastwalk_skip_target_sightings: frozenset[tuple[str, str]] = frozenset(),
    provision_funding_candidate: HuntCandidate | None = None,
    source_ranked_hunt_candidate: HuntCandidate | None = None,
    emergency_provision_sale: bool = False,
) -> RunResult:
    def starter_runner(**kwargs: Any) -> StarterBotRunner:
        if fastwalk_skip_target_sightings:
            kwargs["fastwalk_skip_target_sightings"] = (
                fastwalk_skip_target_sightings
            )
        if pounding_weapon_required:
            kwargs["city_rearm_pounding"] = True
        if counterbalance_preparation_required:
            kwargs["counterbalance_preparation_required"] = True
        return StarterBotRunner(spec, profile_path, **kwargs)

    if policy.execution == "starter":
        return await starter_runner().run()
    if policy.execution == "arena":
        return await starter_runner(
            objective_level=policy.maximum_level or 10,
            arena_kill_limit=policy.segment_kill_limit,
            arena_respawn_wait=False,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "return-home":
        return await starter_runner(
            return_home=True,
            emergency_provision_sale=emergency_provision_sale,
        ).run()
    if policy.execution == "source-ranked-hunt":
        if source_ranked_hunt_candidate is None:
            raise RuntimeError(
                "no checkpointed source-ranked hunt candidate is available"
            )
        candidate = source_ranked_hunt_candidate
        route = Fastwalk(
            name=(
                "source-ranked hunt "
                f"{candidate.target_keyword} {candidate.room_vnum}"
            ),
            minimum_level=1,
            maximum_level=100,
            notation=_funding_route_notation(candidate.route),
            recall_after_loot=True,
        )
        stop = FieldHuntStop(
            (),
            _source_ranked_target_identity(candidate),
            command_keyword=candidate.target_keyword,
            exact_target=True,
            maximum_target_count=1,
            require_isolated=True,
            minimum_health_ratio=0.85,
            maximum_level_offset=1,
        )
        return await starter_runner(
            objective_level=100,
            fastwalk_route=route,
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(stop,),
            fastwalk_kill_limit=policy.segment_kill_limit or 1,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=(
                spec.character_class.casefold() == "mage"
            ),
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "provision-funding":
        if provision_funding_candidate is None:
            raise RuntimeError(
                "no source-safe current-reboot funding target is available"
            )
        candidate = provision_funding_candidate
        route = Fastwalk(
            name=(
                "provision funding "
                f"{candidate.target_keyword} {candidate.room_vnum}"
            ),
            minimum_level=1,
            maximum_level=100,
            notation=_funding_route_notation(candidate.route),
            recall_after_loot=True,
        )
        stop = FieldHuntStop(
            (),
            normalize_item_name(candidate.target),
            command_keyword=candidate.target_keyword,
            exact_target=True,
            required_items=(candidate.loot[0],) if candidate.loot else (),
            allow_below_band_for_required_loot=bool(candidate.loot),
            maximum_target_count=1,
            maximum_level_offset=1,
        minimum_health_ratio=0.27,
            require_isolated=True,
        )
        return await starter_runner(
            objective_level=100,
            fastwalk_route=route,
            fastwalk_hunt_stops=(stop,),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_defer_provision_resupply=True,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=(
                spec.character_class.casefold() == "mage"
            ),
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "foundry-hunt":
        hunt_stops = (
            foundry_level_seven_hunt_stops()
            if policy.minimum_level >= 7
            else foundry_level_six_hunt_stops()
        )
        return await starter_runner(
            objective_level=policy.maximum_level or 7,
            fastwalk_route=route_named("foundry"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=hunt_stops,
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "moria-orc-hunt":
        return await starter_runner(
            objective_level=policy.maximum_level or 8,
            fastwalk_route=route_named("moria"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=moria_level_seven_orc_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "moria-large-orc-hunt":
        hunt_stops = (
            moria_level_eight_large_orc_hunt_stops()
            if policy.minimum_level >= 10
            else (
                moria_level_seven_orc_hunt_stops()
                if policy.minimum_level >= 9
                else moria_level_eight_large_orc_hunt_stops()
            )
        )
        return await starter_runner(
            objective_level=policy.maximum_level or 9,
            fastwalk_route=route_named("moria"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=hunt_stops,
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "daycare-nanny-hunt":
        return await starter_runner(
            objective_level=policy.maximum_level or 8,
            fastwalk_route=daycare_nanny_hunt_route(),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=daycare_nanny_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "daycare-armed-guard-hunt":
        return await starter_runner(
            objective_level=policy.maximum_level or 9,
            fastwalk_route=daycare_armed_guard_hunt_route(),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=daycare_armed_guard_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "cult-fanatic-research":
        return await starter_runner(
            objective_level=policy.maximum_level or 9,
            fastwalk_route=route_named("dragon cult"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=cult_fanatic_research_stops(),
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {"plains-aruncus-research", "plains-aruncus-hunt"}:
        return await starter_runner(
            objective_level=policy.maximum_level or 15,
            fastwalk_route=route_named("plains aruncus"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                plains_aruncus_hunt_stops()
                if policy.execution == "plains-aruncus-hunt"
                else plains_aruncus_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=spec.character_class == "mage",
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "dwarven-workers-research":
        return await starter_runner(
            objective_level=policy.maximum_level or 15,
            fastwalk_route=route_named("dwarven workers"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=dwarven_worker_research_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "mahntor-rock-toad-research",
        "mahntor-rock-toad-hunt",
        "mahntor-rock-toad-circuit",
    }:
        rock_toad_hunt = policy.execution == "mahntor-rock-toad-hunt"
        rock_toad_circuit = policy.execution == "mahntor-rock-toad-circuit"
        return await starter_runner(
            objective_level=policy.maximum_level or 15,
            fastwalk_route=route_named("mahn tor rock toads"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                mahntor_rock_toad_circuit_hunt_stops()
                if rock_toad_circuit
                else (
                    mahntor_rock_toad_hunt_stops()
                    if rock_toad_hunt
                    else mahntor_rock_toad_research_stops()
                )
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "dwarven-nobleman-research",
        "dwarven-nobleman-hunt",
    }:
        return await starter_runner(
            objective_level=policy.maximum_level or 15,
            fastwalk_route=route_named("dwarven nobleman"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                dwarven_nobleman_hunt_stops()
                if policy.execution == "dwarven-nobleman-hunt"
                else dwarven_nobleman_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "dwarven-servant-research",
        "dwarven-servant-hunt",
    }:
        servant_hunt = policy.execution == "dwarven-servant-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 18,
            fastwalk_route=route_named("dwarven servant"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                dwarven_servant_hunt_stops()
                if servant_hunt
                else dwarven_servant_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "ambush-bardoosh-hunt":
        return await starter_runner(
            objective_level=policy.maximum_level or 13,
            fastwalk_route=route_named("ambush"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=ambush_bardoosh_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "mirror-realm-watchman-research",
        "mirror-realm-watchman-hunt",
        "mirror-realm-gardener-research",
        "mirror-realm-gardener-hunt",
        "mirror-realm-guardian-research",
        "mirror-realm-guardian-hunt",
    }:
        watchman_hunt = policy.execution == "mirror-realm-watchman-hunt"
        gardener_probe = policy.execution == "mirror-realm-gardener-research"
        gardener_hunt = policy.execution == "mirror-realm-gardener-hunt"
        guardian_hunt = policy.execution == "mirror-realm-guardian-hunt"
        guardian_probe = policy.execution == "mirror-realm-guardian-research"
        return await starter_runner(
            objective_level=policy.maximum_level or (
                30
                if guardian_probe or guardian_hunt
                else 25
                if gardener_probe or gardener_hunt
                else 20
            ),
            fastwalk_route=route_named(
                "mirror realm guardian"
                if guardian_probe or guardian_hunt
                else "mirror realm gardener"
                if gardener_probe or gardener_hunt
                else "mirror realm watchman"
            ),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                mirror_realm_gardener_hunt_stops()
                if gardener_hunt
                else mirror_realm_gardener_research_stops()
                if gardener_probe
                else mirror_realm_guardian_hunt_stops()
                if guardian_hunt
                else mirror_realm_guardian_research_stops()
                if guardian_probe
                else mirror_realm_watchman_hunt_stops()
                if watchman_hunt
                else mirror_realm_watchman_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "shadow-keep-undead-soldier-research",
        "shadow-keep-undead-soldier-hunt",
    }:
        soldier_hunt = policy.execution == "shadow-keep-undead-soldier-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 20,
            fastwalk_route=route_named("shadow keep soldier"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                shadow_keep_soldier_hunt_stops()
                if soldier_hunt
                else shadow_keep_soldier_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "highland-keeper-research",
        "highland-keeper-hunt",
    }:
        keeper_hunt = policy.execution == "highland-keeper-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 20,
            fastwalk_route=route_named("highland keeper"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                highland_keeper_hunt_stops()
                if keeper_hunt
                else highland_keeper_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=spec.character_class == "mage",
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "crystalmir-white-stag-research",
        "crystalmir-white-stag-hunt",
    }:
        stag_hunt = policy.execution == "crystalmir-white-stag-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 20,
            fastwalk_route=route_named("crystalmir white stag"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_required_move=_PIERCING_WEAPON_UPGRADE_REQUIRED_MOVE,
            fastwalk_hunt_stops=(
                crystalmir_white_stag_hunt_stops()
                if stag_hunt
                else crystalmir_white_stag_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "galaxy-white-dwarf-research",
        "galaxy-white-dwarf-hunt",
    }:
        dwarf_hunt = policy.execution == "galaxy-white-dwarf-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 20,
            fastwalk_route=route_named("galaxy white dwarf"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_required_move=_PIERCING_WEAPON_UPGRADE_REQUIRED_MOVE,
            fastwalk_hunt_stops=(
                galaxy_white_dwarf_hunt_stops()
                if dwarf_hunt
                else galaxy_white_dwarf_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "galaxy-red-supergiant-research",
        "galaxy-red-supergiant-hunt",
    }:
        supergiant_hunt = policy.execution == "galaxy-red-supergiant-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 20,
            fastwalk_route=route_named("galaxy red supergiant"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_required_move=_PIERCING_WEAPON_UPGRADE_REQUIRED_MOVE,
            fastwalk_hunt_stops=(
                galaxy_red_supergiant_hunt_stops()
                if supergiant_hunt
                else galaxy_red_supergiant_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "galaxy-white-dwarf-secondary-research",
        "galaxy-white-dwarf-secondary-hunt",
    }:
        secondary_dwarf_hunt = (
            policy.execution == "galaxy-white-dwarf-secondary-hunt"
        )
        return await starter_runner(
            objective_level=policy.maximum_level or 20,
            fastwalk_route=route_named("galaxy white dwarf"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_required_move=_PIERCING_WEAPON_UPGRADE_REQUIRED_MOVE,
            fastwalk_hunt_stops=(
                galaxy_white_dwarf_secondary_hunt_stops()
                if secondary_dwarf_hunt
                else galaxy_white_dwarf_secondary_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "galaxy-horsehead-nebula-research",
        "galaxy-horsehead-nebula-hunt",
    }:
        horsehead_hunt = policy.execution == "galaxy-horsehead-nebula-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 20,
            fastwalk_route=route_named("galaxy horsehead nebula"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_required_move=_PIERCING_WEAPON_UPGRADE_REQUIRED_MOVE,
            fastwalk_hunt_stops=(
                galaxy_horsehead_nebula_hunt_stops()
                if horsehead_hunt
                else galaxy_horsehead_nebula_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "hightower-jailor-research",
        "hightower-jailor-hunt",
    }:
        jailor_hunt = policy.execution == "hightower-jailor-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 20,
            fastwalk_route=route_named("hightower jailor"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_required_move=_PIERCING_WEAPON_UPGRADE_REQUIRED_MOVE,
            fastwalk_hunt_stops=(
                hightower_jailor_hunt_stops()
                if jailor_hunt
                else hightower_jailor_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "shire-battle-master-research":
        return await starter_runner(
            objective_level=policy.maximum_level or 30,
            fastwalk_route=route_named("shire battle master"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=shire_battle_master_research_stops(),
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "shire-dwarven-prince-research",
        "shire-dwarven-prince-hunt",
    }:
        prince_hunt = policy.execution == "shire-dwarven-prince-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 20,
            fastwalk_route=route_named("shire dwarven prince"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                shire_dwarven_prince_hunt_stops()
                if prince_hunt
                else shire_dwarven_prince_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {"shire-thain-research", "shire-thain-hunt"}:
        thain_hunt = policy.execution == "shire-thain-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 20,
            fastwalk_route=route_named("shire thain"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                shire_thain_hunt_stops()
                if thain_hunt
                else shire_thain_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "argent-bandit-leader-research",
        "argent-bandit-leader-hunt",
    }:
        bandit_leader_hunt = policy.execution == "argent-bandit-leader-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 20,
            fastwalk_route=route_named("argent bandit leader"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                argent_bandit_leader_hunt_stops()
                if bandit_leader_hunt
                else argent_bandit_leader_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "shire-elven-wizard-research",
        "shire-elven-wizard-hunt",
    }:
        wizard_hunt = policy.execution == "shire-elven-wizard-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 20,
            fastwalk_route=route_named("shire elven wizard"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                shire_elven_wizard_hunt_stops()
                if wizard_hunt
                else shire_elven_wizard_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "pyramid-ali-baba-research",
        "pyramid-ali-baba-hunt",
    }:
        ali_baba_hunt = policy.execution == "pyramid-ali-baba-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 20,
            fastwalk_route=route_named("pyramid ali baba"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                pyramid_ali_baba_hunt_stops()
                if ali_baba_hunt
                else pyramid_ali_baba_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "solace-lord-doom-research",
        "solace-lord-doom-hunt",
    }:
        lord_doom_hunt = policy.execution == "solace-lord-doom-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 20,
            fastwalk_route=route_named("solace lord doom"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                solace_lord_doom_hunt_stops()
                if lord_doom_hunt
                else solace_lord_doom_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "solace-magnus-research",
        "solace-magnus-hunt",
    }:
        magnus_hunt = policy.execution == "solace-magnus-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 20,
            fastwalk_route=route_named("solace magnus"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                solace_magnus_hunt_stops()
                if magnus_hunt
                else solace_magnus_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "minotaur-gatekeeper-research",
        "minotaur-gatekeeper-hunt",
    }:
        gatekeeper_hunt = policy.execution == "minotaur-gatekeeper-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 35,
            fastwalk_route=route_named("minotaur gatekeeper"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                minotaur_gatekeeper_hunt_stops()
                if gatekeeper_hunt
                else minotaur_gatekeeper_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "galaxy-cancer-research":
        return await starter_runner(
            objective_level=policy.maximum_level or 35,
            fastwalk_route=route_named("galaxy cancer"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=galaxy_cancer_research_stops(),
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "mirror-realm-jerry-garcia-research":
        return await starter_runner(
            objective_level=policy.maximum_level or 40,
            fastwalk_route=route_named("mirror realm jerry garcia"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=mirror_realm_jerry_garcia_research_stops(),
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "pit-official-research":
        return await starter_runner(
            objective_level=policy.maximum_level or 45,
            fastwalk_route=route_named("pit official"),
            fastwalk_hunt_stops=pit_official_research_stops(),
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "dwarven-home-chess-dwarf-research",
        "dwarven-home-chess-dwarf-hunt",
    }:
        chess_dwarf_hunt = policy.execution == "dwarven-home-chess-dwarf-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 50,
            fastwalk_route=route_named("dwarven home chess dwarf"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                dwarven_home_chess_dwarf_hunt_stops()
                if chess_dwarf_hunt
                else dwarven_home_chess_dwarf_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "mirror-realm-storn-research",
        "mirror-realm-storn-hunt",
    }:
        storn_hunt = policy.execution == "mirror-realm-storn-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 50,
            fastwalk_route=route_named("mirror realm storn"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                mirror_realm_storn_hunt_stops()
                if storn_hunt
                else mirror_realm_storn_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "darkwood-strange-mist-research",
        "darkwood-strange-mist-hunt",
    }:
        strange_mist_hunt = policy.execution == "darkwood-strange-mist-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 55,
            fastwalk_route=route_named("darkwood strange mist"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                darkwood_strange_mist_hunt_stops()
                if strange_mist_hunt
                else darkwood_strange_mist_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "dwarven-home-gambler-research",
        "dwarven-home-gambler-hunt",
    }:
        gambler_hunt = policy.execution == "dwarven-home-gambler-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 55,
            fastwalk_route=route_named("dwarven home gambler"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                dwarven_home_gambler_hunt_stops()
                if gambler_hunt
                else dwarven_home_gambler_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "dwarven-home-master-research",
        "dwarven-home-master-hunt",
    }:
        master_hunt = policy.execution == "dwarven-home-master-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 60,
            fastwalk_route=route_named("dwarven home master"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                dwarven_home_master_hunt_stops()
                if master_hunt
                else dwarven_home_master_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "vampire-hive-wounded-vampire-research",
        "vampire-hive-wounded-vampire-hunt",
    }:
        vampire_hunt = policy.execution == "vampire-hive-wounded-vampire-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 65,
            fastwalk_route=route_named("vampire hive wounded vampire"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                vampire_hive_wounded_vampire_hunt_stops()
                if vampire_hunt
                else vampire_hive_wounded_vampire_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "tabernacle-hulking-beast-research",
        "tabernacle-hulking-beast-hunt",
    }:
        beast_hunt = policy.execution == "tabernacle-hulking-beast-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 70,
            fastwalk_route=route_named("tabernacle hulking beast"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                tabernacle_hulking_beast_hunt_stops()
                if beast_hunt
                else tabernacle_hulking_beast_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "pirates-seas-rastafarians-research",
        "pirates-seas-rastafarians-hunt",
    }:
        rastafarians_hunt = policy.execution == "pirates-seas-rastafarians-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 75,
            fastwalk_route=route_named("pirates seas rastafarians"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                pirates_seas_rastafarians_hunt_stops()
                if rastafarians_hunt
                else pirates_seas_rastafarians_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "ghost-town-crypt-thing-research",
        "ghost-town-crypt-thing-hunt",
    }:
        crypt_hunt = policy.execution == "ghost-town-crypt-thing-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 76,
            fastwalk_route=route_named("ghost town crypt thing"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                ghost_town_crypt_thing_hunt_stops()
                if crypt_hunt
                else ghost_town_crypt_thing_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "ghost-town-retriever-research",
        "ghost-town-retriever-hunt",
    }:
        retriever_hunt = policy.execution == "ghost-town-retriever-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 80,
            fastwalk_route=route_named("ghost town retriever"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                ghost_town_retriever_hunt_stops()
                if retriever_hunt
                else ghost_town_retriever_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "circus-freak-show-hunt":
        return await starter_runner(
            objective_level=policy.maximum_level or 8,
            fastwalk_route=route_named("circus bearded lady"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=circus_freak_show_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_world_cache_items=("ticket",),
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "shire-bull-hunt":
        return await starter_runner(
            objective_level=policy.maximum_level or 8,
            fastwalk_route=shire_bull_hunt_route(),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=shire_bull_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "gnome-hermit-hunt":
        return await starter_runner(
            objective_level=policy.maximum_level or 8,
            fastwalk_route=gnome_hermit_hunt_route(),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=gnome_hermit_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "gnome-guard-hunt":
        return await starter_runner(
            objective_level=policy.maximum_level or 9,
            fastwalk_route=route_named("gnome guard hut"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=gnome_guard_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "gnome-guard-research":
        return await starter_runner(
            objective_level=policy.maximum_level or 11,
            fastwalk_route=route_named("gnome guard hut"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=gnome_guard_research_stops(),
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "gnome-small-troll-hunt":
        return await starter_runner(
            objective_level=policy.maximum_level or 8,
            fastwalk_route=route_named("gnome small troll"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=gnome_small_troll_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=True,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "gnome-treasurer-research":
        return await starter_runner(
            objective_level=policy.maximum_level or 15,
            fastwalk_route=route_named("gnome treasury"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=gnome_treasurer_research_stops(),
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "gnome-treasurer-hunt":
        return await starter_runner(
            objective_level=policy.maximum_level or 15,
            fastwalk_route=route_named("gnome treasury"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=gnome_treasurer_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "sell-loot":
        return await starter_runner(
            liquidate_loot=True,
            emergency_provision_sale=emergency_provision_sale,
        ).run()
    if policy.execution == "vault-spare-gear":
        return await starter_runner(
            vault_stow_items=vault_stow_items,
            vault_required_free_weight=10,
            vault_only=True,
        ).run()
    if policy.execution == "bank-excess-coins":
        return await starter_runner(
            bank_excess_coins=True,
        ).run()
    if policy.execution == "restock":
        return await starter_runner(
            city_restock=True,
        ).run()
    if policy.execution == "rearm-weapon":
        return await starter_runner(
            city_rearm=True,
        ).run()
    if policy.execution == "outfit-basic-gear":
        return await starter_runner(
            city_outfit=True,
            vault_claim_items=vault_claim_items,
            vault_wear_claimed_items=bool(vault_claim_items),
        ).run()
    if policy.execution == "recover-basic-body":
        return await starter_runner(
            objective_level=policy.maximum_level or 100,
            fastwalk_route=route_named("foundry"),
            fastwalk_required_free_weight=_RECOVER_BASIC_BODY_REQUIRED_FREE_WEIGHT,
            fastwalk_hunt_stops=foundry_body_gear_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=False,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
        ).run()
    if policy.execution == "recover-foundry-set-circlet":
        return await starter_runner(
            objective_level=policy.maximum_level or 100,
            fastwalk_route=route_named("foundry"),
            fastwalk_required_free_weight=(
                _RECOVER_FOUNDRY_SET_CIRCLET_REQUIRED_FREE_WEIGHT
            ),
            fastwalk_hunt_stops=foundry_set_circlet_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=False,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
        ).run()
    if policy.execution == "recover-school-wrist-float":
        return await starter_runner(
            objective_level=policy.maximum_level or 100,
            fastwalk_route=school_accessory_hunt_route(),
            fastwalk_required_free_weight=(
                _RECOVER_SCHOOL_WRIST_FLOAT_REQUIRED_FREE_WEIGHT
            ),
            fastwalk_hunt_stops=school_wrist_float_hunt_stops(),
            fastwalk_train_before_departure=False,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
        ).run()
    if policy.execution == "recover-gremlin-waist":
        return await starter_runner(
            objective_level=policy.maximum_level or 100,
            fastwalk_route=gremlin_waist_hunt_route(),
            fastwalk_required_free_weight=_RECOVER_GREMLIN_WAIST_REQUIRED_FREE_WEIGHT,
            fastwalk_hunt_stops=gremlin_waist_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=False,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
        ).run()
    if policy.execution == "recover-daycare-ring":
        return await starter_runner(
            objective_level=policy.maximum_level or 100,
            fastwalk_route=daycare_ring_hunt_route(),
            fastwalk_required_free_weight=_RECOVER_DAYCARE_RING_REQUIRED_FREE_WEIGHT,
            fastwalk_hunt_stops=daycare_ring_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=spec.character_class == "mage",
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "recover-war-dog-collar":
        return await starter_runner(
            objective_level=policy.maximum_level or 100,
            fastwalk_route=route_named("ambush"),
            fastwalk_origin_actions=(
                "wear collar",
                "eq all",
                "get all.pie",
                "eat pie",
                "drink skin",
            ),
            fastwalk_required_free_weight=(
                _RECOVER_WAR_DOG_COLLAR_REQUIRED_FREE_WEIGHT
            ),
            fastwalk_hunt_stops=ambush_war_dog_collar_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "upgrade-piercing-weapon":
        intermediate = (
            policy.policy_id == "thalos-long-dagger-upgrade-10-29"
        )
        return await starter_runner(
            objective_level=policy.maximum_level or 14,
            fastwalk_route=(
                thalos_long_dagger_hunt_route()
                if intermediate
                else forest_bear_claws_hunt_route()
            ),
            fastwalk_required_free_weight=(
                _PIERCING_WEAPON_UPGRADE_REQUIRED_FREE_WEIGHT
            ),
            fastwalk_required_move=(
                0 if intermediate else _PIERCING_WEAPON_UPGRADE_REQUIRED_MOVE
            ),
            fastwalk_hunt_stops=(
                thalos_long_dagger_hunt_stops()
                if intermediate
                else forest_bear_claws_hunt_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            use_sanctuary_potions=False,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "buy-flight":
        return await starter_runner(
            magic_shop_research=True,
            magic_shop_buy_fly=True,
        ).run()
    if policy.execution == "borrow-flight":
        return await starter_runner(
            flight_borrowing=True,
        ).run()
    if policy.execution in {
        "ambush-war-dog-hunt",
        "ambush-hunt",
        "ambush-raider-hunt",
        "ambush-vile-hunt",
    }:
        if policy.execution == "ambush-war-dog-hunt":
            hunt_stops = (
                ambush_caster_level_eight_hunt_stops()
                if policy.policy_id == "ambush-war-dog-looter-8-9"
                else ambush_level_eight_hunt_stops()
            )
        elif policy.execution == "ambush-raider-hunt":
            hunt_stops = ambush_raider_hunt_stops()
        elif policy.execution == "ambush-vile-hunt":
            hunt_stops = ambush_vile_goblin_hunt_stops()
        else:
            hunt_stops = ambush_level_eight_hunt_stops()
        return await starter_runner(
            objective_level=policy.maximum_level or 10,
            fastwalk_route=route_named("ambush"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=hunt_stops,
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=True,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "fleshmonger-guard-research":
        return await starter_runner(
            objective_level=policy.maximum_level or 9,
            fastwalk_route=replace(
                route_named("fleshmonger"),
                recall_after_loot=True,
            ),
            fastwalk_hunt_stops=fleshmonger_guard_research_stops(),
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "fleshmonger-guard-hunt":
        return await starter_runner(
            objective_level=policy.maximum_level or 11,
            fastwalk_route=replace(
                route_named("fleshmonger"),
                recall_after_loot=True,
            ),
            fastwalk_hunt_stops=fleshmonger_guard_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "fleshmonger-mufti-research":
        return await starter_runner(
            objective_level=policy.maximum_level or 11,
            fastwalk_route=replace(
                route_named("fleshmonger"),
                recall_after_loot=True,
            ),
            fastwalk_hunt_stops=fleshmonger_mufti_research_stops(),
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "fleshmonger-cook-research":
        return await starter_runner(
            objective_level=policy.maximum_level or 11,
            fastwalk_route=replace(
                route_named("fleshmonger"),
                recall_after_loot=True,
            ),
            fastwalk_hunt_stops=fleshmonger_cook_research_stops(),
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "fleshmonger-cook-hunt":
        return await starter_runner(
            objective_level=policy.maximum_level or 11,
            fastwalk_route=replace(
                route_named("fleshmonger"),
                recall_after_loot=True,
            ),
            fastwalk_hunt_stops=fleshmonger_cook_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "fleshmonger-thief-rotation-research":
        return await starter_runner(
            objective_level=policy.maximum_level or 11,
            fastwalk_route=replace(
                route_named("fleshmonger"),
                recall_after_loot=True,
            ),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=fleshmonger_thief_rotation_research_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "fleshmonger-servant-research":
        return await starter_runner(
            objective_level=policy.maximum_level or 11,
            fastwalk_route=replace(
                route_named("fleshmonger"),
                recall_after_loot=True,
            ),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=fleshmonger_servant_research_stops(),
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "fleshmonger-servant-hunt":
        return await starter_runner(
            objective_level=policy.maximum_level or 11,
            fastwalk_route=replace(
                route_named("fleshmonger"),
                recall_after_loot=True,
            ),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=fleshmonger_servant_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "fleshmonger-thief-extended-rotation-research":
        return await starter_runner(
            objective_level=policy.maximum_level or 11,
            fastwalk_route=replace(
                route_named("fleshmonger"),
                recall_after_loot=True,
            ),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=fleshmonger_thief_extended_rotation_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_xp_first_capacity_threshold=20,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "ambush-archer-research":
        return await starter_runner(
            objective_level=policy.maximum_level or 11,
            fastwalk_route=replace(
                route_named("ambush"),
                recall_after_loot=True,
            ),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=ambush_archer_research_stops(),
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "ambush-archer-hunt":
        return await starter_runner(
            objective_level=policy.maximum_level or 11,
            fastwalk_route=replace(
                route_named("ambush"),
                recall_after_loot=True,
            ),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=ambush_archer_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "fleshmonger-guard-circuit-research",
        "fleshmonger-guard-circuit",
    }:
        return await starter_runner(
            objective_level=policy.maximum_level or 11,
            fastwalk_route=replace(
                route_named("fleshmonger"),
                recall_after_loot=True,
            ),
            fastwalk_hunt_stops=fleshmonger_guard_circuit_research_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "ambush-martial-hunt":
        return await starter_runner(
            objective_level=policy.maximum_level or 9,
            fastwalk_route=route_named("ambush"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=ambush_martial_level_eight_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "midennir-hunt":
        use_level_eight_loadout = (policy.minimum_level or 0) >= 8
        return await starter_runner(
            objective_level=policy.maximum_level or 10,
            fastwalk_route=route_named("ambush"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=midennir_mountain_goblin_hunt_stops(),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=not use_level_eight_loadout,
            fastwalk_require_invisibility=use_level_eight_loadout,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "midennir-sack":
        return await starter_runner(
            objective_level=policy.maximum_level or 10,
            fastwalk_route=route_named("ambush"),
            fastwalk_origin_actions=("drop all.piping", "drop cap"),
            vault_stow_items=(
                "sleeves",
                "vest",
                "cape",
                "belt",
                "bracer",
                "guards",
            ),
            vault_required_free_weight=60,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=True,
            fastwalk_hunt_stops=(
                FieldHuntStop(
                    (
                        "west",
                        "south",
                        "south",
                        "west",
                        "south",
                        "west",
                        "south",
                        "south",
                        "east",
                        "south",
                        "south",
                        "open east",
                        "east",
                        "east",
                    ),
                    actions=("get sack", "inventory"),
                    required_items=("large sack",),
                ),
            ),
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution == "moria-circuit":
        return await starter_runner(
            objective_level=policy.maximum_level or 10,
            fastwalk_route=route_named("moria"),
            fastwalk_hunt_stops=(
                FieldHuntStop(
                    (
                        "west",
                        "west",
                        "north",
                        "west",
                        "south",
                        "east",
                        "south",
                    ),
                    "hobgoblin",
                ),
                FieldHuntStop(("east",), "centipede"),
                FieldHuntStop((), "hobgoblin"),
                FieldHuntStop(("west", "north", "west"), "large orc"),
                FieldHuntStop((), "orc"),
            ),
        ).run()
    if policy.execution == "moria-sanctuary-hunt":
        return await starter_runner(
            objective_level=policy.maximum_level or 10,
            fastwalk_route=route_named("moria"),
            fastwalk_hunt_stops=moria_sanctuary_potion_hunt_stops(),
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=(
                spec.character_class == "mage"
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    if policy.execution in {
        "moria-deep-sanctuary-research",
        "moria-deep-sanctuary-hunt",
    }:
        deep_hunt = policy.execution == "moria-deep-sanctuary-hunt"
        return await starter_runner(
            objective_level=policy.maximum_level or 20,
            fastwalk_route=route_named("moria"),
            fastwalk_origin_actions=("get all.pie", "eat pie", "drink skin"),
            fastwalk_hunt_stops=(
                moria_deep_sanctuary_potion_hunt_stops()
                if deep_hunt
                else moria_deep_sanctuary_potion_research_stops()
            ),
            fastwalk_kill_limit=policy.segment_kill_limit,
            fastwalk_train_before_departure=True,
            fastwalk_require_invisibility=False,
            require_fastwalk_kill=False,
            allow_safe_fastwalk_abort=True,
            practice_types_spent=practice_types_spent,
            rejected_practice_skills=rejected_practice_skills,
        ).run()
    raise ValueError(f"unsupported executable policy {policy.policy_id}")


def _checkpoint_state(checkpoint: Any) -> dict[str, Any]:
    if checkpoint is None:
        return {}
    return dict(json.loads(checkpoint["state_json"]))


def _run_matches_character(run: Any, character_name: str) -> bool:
    suffixes = (
        f":{character_name}".casefold(),
        f"-{character_name}".casefold(),
    )
    return str(run["scenario_name"]).casefold().endswith(suffixes)


def _run_for_failed_segment(
    storage: RunStorage,
    segment: Any,
    *,
    character_name: str,
) -> Any | None:
    """Find the failed runner created inside one campaign segment window."""
    try:
        segment_started = datetime.fromisoformat(segment["started_at"])
        segment_finished = (
            datetime.fromisoformat(segment["finished_at"])
            if segment["finished_at"]
            else None
        )
    except (TypeError, ValueError):
        return None
    for run in storage.list_runs(limit=1000):
        if not _run_matches_character(run, character_name):
            continue
        if str(run["status"]) != "failed":
            continue
        try:
            run_started = datetime.fromisoformat(run["started_at"])
        except (TypeError, ValueError):
            continue
        if run_started < segment_started:
            continue
        if segment_finished is not None and run_started > segment_finished:
            continue
        return run
    return None


def _reconcile_failed_segment_progress(
    storage: RunStorage,
    campaign_id: int,
    checkpoint: Any,
    *,
    character_name: str,
) -> bool:
    """Repair an old failed segment whose runner recorded an objective kill."""
    segment_id = checkpoint["segment_id"]
    if segment_id is None:
        return False
    segment = next(
        (
            row
            for row in storage.list_campaign_segments(campaign_id)
            if int(row["id"]) == int(segment_id)
        ),
        None,
    )
    if segment is None or segment["status"] != "failed":
        return False
    run = _run_for_failed_segment(
        storage,
        segment,
        character_name=character_name,
    )
    if run is None:
        return False
    objective_kills = _run_objective_kills(storage, int(run["id"]))
    if not isinstance(objective_kills, list) or not objective_kills:
        return False
    start_state = json.loads(segment["start_state_json"] or "{}")
    current_state = _run_latest_state(storage, int(run["id"])) or start_state
    end_state = {
        **_campaign_segment_end_state(
            start_state,
            current_state,
            execution=str(segment["phase"]),
        ),
        "campaign_completed_kills": objective_kills,
        "campaign_objective_kills": objective_kills,
        "campaign_last_policy": str(segment["phase"]),
        "campaign_policy_revision": _CAMPAIGN_POLICY_REVISION,
    }
    run_id = int(run["id"])
    storage.finish_campaign_segment(
        int(segment["id"]),
        status="ready",
        run_id=run_id,
        end_state=end_state,
        command_count=storage.count_events(run_id, kind="command"),
        duration_seconds=_run_duration(run),
        error=segment["error"],
    )
    storage.record_campaign_checkpoint(
        campaign_id,
        segment_id=int(segment["id"]),
        run_id=run_id,
        phase=str(segment["phase"]),
        reason="segment_failed_progress_reconciled",
        state=end_state,
    )
    storage.finish_campaign(
        campaign_id,
        status="ready",
        error=(
            f"{segment['phase']} progress reconciled from failed run "
            f"{run_id} after {len(objective_kills)} objective kill(s)."
        ),
    )
    return True


def _repair_reconciled_campaign_metadata(
    storage: RunStorage,
    campaign_id: int,
    checkpoint: Any,
    state: dict[str, Any],
) -> dict[str, Any]:
    """Restore metadata lost by an older failed-segment reconciliation."""
    if checkpoint is None:
        return state
    reconciled_checkpoints = [
        row
        for row in storage.list_campaign_checkpoints(campaign_id)
        if row["reason"] == "segment_failed_progress_reconciled"
        and row["segment_id"] is not None
    ]
    if not reconciled_checkpoints:
        return state
    segments = sorted(
        storage.list_campaign_segments(campaign_id),
        key=lambda row: int(row["sequence"]),
    )
    reconciled_segments = [
        next(
            (
                segment
                for segment in segments
                if int(segment["id"]) == int(checkpoint["segment_id"])
            ),
            None,
        )
        for checkpoint in reconciled_checkpoints
    ]
    reconciled_segments = [segment for segment in reconciled_segments if segment]
    if not reconciled_segments:
        return state
    reconciled_segment_ids = {
        int(segment["id"]) for segment in reconciled_segments
    }
    first_reconciled = min(
        reconciled_segments,
        key=lambda row: int(row["sequence"]),
    )
    historical_results: dict[str, dict[str, Any]] = {}
    historical_cooldowns: dict[str, int] = {}
    cleared_research_policies = {
        str(policy_id)
        for policy_id in state.get(_CLEARED_RESEARCH_POLICIES_KEY, ())
    }
    inferred_cleared_research_policies: set[str] = set()
    for segment in segments:
        if int(segment["sequence"]) < int(first_reconciled["sequence"]):
            continue
        start_state = json.loads(segment["start_state_json"] or "{}")
        end_state = json.loads(segment["end_state_json"] or "{}")
        if (
            int(segment["id"]) not in reconciled_segment_ids
            and str(segment["status"]) in {"ready", "success"}
        ):
            start_results = _campaign_research_results(start_state)
            end_results = _campaign_research_results(end_state)
            for policy_id, result in start_results.items():
                if result.get("absent") and policy_id not in end_results:
                    inferred_cleared_research_policies.add(policy_id)
            for policy_id, result in end_results.items():
                if (
                    policy_id == str(segment["phase"])
                    or result != start_results.get(policy_id)
                ):
                    inferred_cleared_research_policies.discard(policy_id)
        for historical_state in (start_state, end_state):
            historical_results.update(
                _campaign_research_results(historical_state)
            )
            cooldowns = historical_state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY)
            if isinstance(cooldowns, dict):
                historical_cooldowns.update(
                    {
                        str(policy_id): int(remaining)
                        for policy_id, remaining in cooldowns.items()
                    }
                )
        if str(end_state.get("campaign_fastwalk_abort_reason") or "").startswith(
            "field room contained "
        ):
            historical_results.pop(str(segment["phase"]), None)
            historical_cooldowns.pop(str(segment["phase"]), None)
    cleared_research_policies.update(inferred_cleared_research_policies)
    first_start_state = json.loads(
        first_reconciled["start_state_json"] or "{}"
    )
    repaired = _campaign_segment_end_state(
        first_start_state,
        state,
        execution=str(first_reconciled["phase"]),
    )
    repaired = _clear_crowd_absence_marker(repaired)
    current_results = _campaign_research_results(repaired)
    current_state_results = _campaign_research_results(state)
    current_reboot_crowd_policies = {
        policy_id
        for policy_id, result in current_state_results.items()
        if (
            result.get("crowded") is True
            and result.get("boot_id") == state.get("world_boot_id")
        )
    }
    inferred_cleared_research_policies.difference_update(
        current_reboot_crowd_policies
    )
    cleared_research_policies.difference_update(
        current_reboot_crowd_policies
    )
    cleared_research_policies.difference_update(
        set(current_state_results).difference(
            inferred_cleared_research_policies
        )
    )
    for policy_id in cleared_research_policies:
        historical_results.pop(policy_id, None)
        historical_cooldowns.pop(policy_id, None)
        current_results.pop(policy_id, None)
    historical_results.update(current_results)
    if historical_results:
        repaired["campaign_research_results"] = historical_results
    else:
        repaired.pop("campaign_research_results", None)
    current_cooldowns = repaired.get(_RESEARCH_ABSENCE_COOLDOWN_KEY)
    if historical_cooldowns or isinstance(current_cooldowns, dict):
        merged_cooldowns = dict(historical_cooldowns)
        if isinstance(current_cooldowns, dict):
            merged_cooldowns.update(
                {
                    str(policy_id): int(remaining)
                    for policy_id, remaining in current_cooldowns.items()
                }
            )
        for policy_id in cleared_research_policies:
            merged_cooldowns.pop(policy_id, None)
        if merged_cooldowns:
            repaired[_RESEARCH_ABSENCE_COOLDOWN_KEY] = merged_cooldowns
        else:
            repaired.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
    if cleared_research_policies:
        repaired[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(
            cleared_research_policies
        )
    else:
        repaired.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
    if repaired == state:
        return state
    storage.record_campaign_checkpoint(
        campaign_id,
        segment_id=checkpoint["segment_id"],
        run_id=checkpoint["run_id"],
        phase=str(checkpoint["phase"]),
        reason=_CAMPAIGN_METADATA_REPAIRED_REASON,
        state=repaired,
    )
    return repaired


def _repair_confirmed_research_kills(
    storage: RunStorage,
    campaign_id: int,
    state: dict[str, Any],
) -> dict[str, Any]:
    """Promote old hunt results whose run already records the objective kill."""
    results = _campaign_research_results(state)
    repaired_results = dict(results)
    changed = False
    repaired_cooldowns = dict(
        state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
    )
    repaired_crowd_cooldowns = dict(
        state.get(_RESEARCH_CROWD_COOLDOWN_KEY) or {}
    )
    cleared_research_policies = {
        str(policy_id)
        for policy_id in state.get(_CLEARED_RESEARCH_POLICIES_KEY, ())
    }
    latest_segments: dict[str, Any] = {}
    segments_by_phase: dict[str, list[Any]] = {}
    for segment in storage.list_campaign_segments(campaign_id):
        policy_id = str(segment["phase"])
        latest_segments[policy_id] = segment
        segments_by_phase.setdefault(policy_id, []).append(segment)
    for policy_id, result in results.items():
        segment = latest_segments.get(policy_id)
        if segment is None:
            continue
        if not isinstance(result, dict) or not isinstance(
            result.get("completed_kill"), bool
        ):
            continue
        end_state = json.loads(segment["end_state_json"] or "{}")
        objective_kills = end_state.get("campaign_objective_kills")
        if objective_kills is None:
            objective_kills = end_state.get("campaign_completed_kills")
        if objective_kills is None and segment["run_id"] is not None:
            objective_kills = _run_objective_kills(
                storage,
                int(segment["run_id"]),
            )
        completed_kill = bool(
            isinstance(objective_kills, list) and objective_kills
        )
        if result.get("completed_kill") == completed_kill:
            continue
        repaired_results[policy_id] = {
            **result,
            "observed": bool(result.get("observed")) or completed_kill,
            "viable": completed_kill,
            "completed_kill": completed_kill,
        }
        changed = True

    # A later crowd checkpoint can remove a positive result even though the
    # successful hunt segment and its objective kill remain durable. Recover
    # that evidence across crowd-only retries, but never carry it across a
    # reboot or over a newer absent, hazardous, or failed hunt.
    for policy_id, phase_segments in segments_by_phase.items():
        positive_evidence: dict[str, Any] | None = None
        for segment in sorted(
            phase_segments,
            key=lambda row: int(row["sequence"]),
        ):
            if str(segment["status"]) not in {"ready", "success"}:
                positive_evidence = None
                continue
            try:
                end_state = json.loads(segment["end_state_json"] or "{}")
            except (TypeError, json.JSONDecodeError):
                end_state = {}
            objective_kills = end_state.get("campaign_objective_kills")
            if objective_kills is None:
                objective_kills = end_state.get("campaign_completed_kills")
            if objective_kills is None and segment["run_id"] is not None:
                objective_kills = _run_objective_kills(
                    storage,
                    int(segment["run_id"]),
                )
            if isinstance(objective_kills, list) and objective_kills:
                historical_result = _campaign_research_results(end_state).get(
                    policy_id
                )
                boot_id = (
                    historical_result.get("boot_id")
                    if isinstance(historical_result, dict)
                    else None
                ) or end_state.get("world_boot_id")
                if (
                    isinstance(historical_result, dict)
                    and historical_result.get("viable") is True
                    and (
                        state.get("world_boot_id") is None
                        or boot_id == state.get("world_boot_id")
                    )
                ):
                    positive_evidence = {
                        "result": historical_result,
                        "boot_id": boot_id,
                    }
                    continue
                positive_evidence = None
                continue
            if positive_evidence is not None:
                abort_reason = str(
                    end_state.get("campaign_fastwalk_abort_reason") or ""
                )
                if any(
                    abort_reason.startswith(prefix)
                    for prefix in _FIELD_CROWD_ABORT_PREFIXES
                ):
                    continue
                positive_evidence = None
        if positive_evidence is None:
            continue
        recovered_result = {
            **positive_evidence["result"],
            "observed": True,
            "viable": True,
            "completed_kill": True,
        }
        if repaired_results.get(policy_id) != recovered_result:
            repaired_results[policy_id] = recovered_result
            changed = True
        if policy_id in repaired_cooldowns:
            repaired_cooldowns.pop(policy_id, None)
            changed = True
        if policy_id in repaired_crowd_cooldowns:
            repaired_crowd_cooldowns.pop(policy_id, None)
            changed = True
        if policy_id in cleared_research_policies:
            cleared_research_policies.discard(policy_id)
            changed = True
    # Older campaign checkpoints discarded crowd-only research results. Rebuild
    # a temporary crowd marker from the latest durable segment so a reconnect
    # cannot immediately select the same crowded route again.
    for policy_id, segment in latest_segments.items():
        if str(segment["status"]) not in {"ready", "success"}:
            continue
        try:
            end_state = json.loads(segment["end_state_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            end_state = {}
        abort_reason = str(end_state.get("campaign_fastwalk_abort_reason") or "")
        if not any(
            abort_reason.startswith(prefix)
            for prefix in _FIELD_CROWD_ABORT_PREFIXES
        ):
            continue
        boot_id = end_state.get("world_boot_id")
        if (
            state.get("world_boot_id") is None
            or boot_id != state.get("world_boot_id")
        ):
            continue
        current_result = repaired_results.get(policy_id)
        if (
            isinstance(current_result, dict)
            and current_result.get("crowded") is True
            and current_result.get("boot_id") == boot_id
        ):
            if policy_id not in repaired_crowd_cooldowns:
                repaired_crowd_cooldowns[policy_id] = (
                    _DEFAULT_RESEARCH_CROWD_COOLDOWN
                )
                changed = True
            continue
        if (
            isinstance(current_result, dict)
            and current_result.get("boot_id") == boot_id
            and current_result.get("viable") is True
            and current_result.get("completed_kill") is not False
        ):
            if repaired_crowd_cooldowns.pop(policy_id, None) is not None:
                changed = True
            continue
        crowd_result = {
            "observed": False,
            "viable": False,
            "crowded": True,
            "boot_id": boot_id,
        }
        if repaired_results.get(policy_id) != crowd_result:
            repaired_results[policy_id] = crowd_result
            changed = True
        if repaired_cooldowns.pop(policy_id, None) is not None:
            changed = True
        if repaired_crowd_cooldowns.get(policy_id) != (
            _DEFAULT_RESEARCH_CROWD_COOLDOWN
        ):
            repaired_crowd_cooldowns[policy_id] = (
                _DEFAULT_RESEARCH_CROWD_COOLDOWN
            )
            changed = True
        if policy_id in cleared_research_policies:
            cleared_research_policies.discard(policy_id)
            changed = True
    if not changed:
        return state
    repaired = dict(state)
    repaired["campaign_research_results"] = repaired_results
    if repaired_cooldowns:
        repaired[_RESEARCH_ABSENCE_COOLDOWN_KEY] = repaired_cooldowns
    else:
        repaired.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
    if repaired_crowd_cooldowns:
        repaired[_RESEARCH_CROWD_COOLDOWN_KEY] = repaired_crowd_cooldowns
    else:
        repaired.pop(_RESEARCH_CROWD_COOLDOWN_KEY, None)
    if cleared_research_policies:
        repaired[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(
            cleared_research_policies
        )
    else:
        repaired.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
    return repaired


def _repair_provision_funding_history(
    storage: RunStorage,
    campaign_id: int,
    state: dict[str, Any],
) -> dict[str, Any]:
    """Recover funding attempts that older metadata checkpoints discarded."""
    successful_emergency_sales = False
    for segment in storage.list_campaign_segments(campaign_id):
        if (
            segment["phase"] != "liquidate-loot"
            or segment["status"] != "success"
            or segment["run_id"] is None
        ):
            continue
        try:
            start_state = json.loads(segment["start_state_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            start_state = {}
        if (
            start_state.get(_PROVISION_FUNDING_REQUIRED_KEY)
            and storage.list_loot_sales_for_run(int(segment["run_id"]))
        ):
            successful_emergency_sales = True
            break
    records: list[dict[str, Any]] = []
    invalid_navigation_attempts: set[str] = set()
    for segment in storage.list_campaign_segments(campaign_id):
        if segment["phase"] != "provision-funding":
            continue
        try:
            end_state = json.loads(segment["end_state_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            continue
        raw_attempts = end_state.get(_PROVISION_FUNDING_ATTEMPTS_KEY)
        if isinstance(raw_attempts, list):
            segment_records = [
                dict(record)
                for record in raw_attempts
                if isinstance(record, dict)
            ]
            error = str(segment["error"] or "").casefold()
            if segment["status"] == "failed" and (
                "without observing its endpoint" in error
                or "progress watchdog" in error
            ):
                invalid_navigation_attempts.update(
                    str(record.get("candidate_key"))
                    for record in segment_records
                    if record.get("candidate_key") is not None
                )
            else:
                records.extend(segment_records)
    current_attempts = state.get(_PROVISION_FUNDING_ATTEMPTS_KEY)
    if isinstance(current_attempts, list):
        records.extend(
            dict(record)
            for record in current_attempts
            if (
                isinstance(record, dict)
                and str(record.get("candidate_key"))
                not in invalid_navigation_attempts
            )
        )
    if not records:
        if (
            successful_emergency_sales
            and state.get(_PROVISION_FUNDING_REQUIRED_KEY)
            and _has_campaign_food(state, gear_catalog=None)
        ):
            repaired = dict(state)
            repaired.pop(_PROVISION_FUNDING_REQUIRED_KEY, None)
            return repaired
        return state

    by_candidate: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        key = (
            str(record.get("boot_id")),
            str(record.get("candidate_key")),
        )
        by_candidate[key] = record
    repaired_attempts = list(by_candidate.values())[-12:]
    repaired = dict(state)
    if repaired_attempts != current_attempts:
        repaired[_PROVISION_FUNDING_ATTEMPTS_KEY] = repaired_attempts
    latest = records[-1]
    if latest.get("candidate_key") is not None:
        repaired[_PROVISION_FUNDING_LAST_ATTEMPT_KEY] = {
            "boot_id": latest.get("boot_id"),
            "candidate_key": str(latest.get("candidate_key")),
            "completed_kill": latest.get("completed_kill") is True,
        }
    if latest.get("completed_kill") is False:
        repaired[_PROVISION_FUNDING_REQUIRED_KEY] = True
    elif latest.get("completed_kill") is True:
        repaired.pop(_PROVISION_FUNDING_REQUIRED_KEY, None)
    if successful_emergency_sales and _has_campaign_food(state, gear_catalog=None):
        repaired.pop(_PROVISION_FUNDING_REQUIRED_KEY, None)
    return repaired if repaired != state else state


def _level(state: dict[str, Any]) -> int:
    level = state.get("level")
    return int(level) if isinstance(level, (int, float)) else 0


_FUNDING_ROUTE_DIRECTIONS = {
    "north": "n",
    "east": "e",
    "south": "s",
    "west": "w",
    "up": "u",
    "down": "d",
}


def _funding_route_notation(commands: Collection[str]) -> str:
    """Convert source graph directions into a Fastwalk notation string."""
    return ";".join(
        _FUNDING_ROUTE_DIRECTIONS.get(command, command)
        for command in commands
    )


def _provision_funding_candidate_key(candidate: HuntCandidate) -> str:
    return ":".join(
        (
            candidate.area_file,
            str(candidate.mobile_vnum),
            str(candidate.room_vnum),
        )
    )


def _candidate_has_saleable_funding_drop(
    candidate: HuntCandidate,
    *,
    gear_catalog: GearCatalog | None,
) -> bool:
    if candidate.contained_coins > 0:
        return True
    if gear_catalog is None:
        return bool(candidate.loot)
    return any(
        (
            (item := gear_catalog.match(description)) is not None
            and safe_shop_for_item(
                item.short_description,
                item_type=item.item_type,
            )
            is not None
        )
        for description in candidate.loot
    )


def _funding_candidate_is_below_band(
    state: dict[str, Any],
    candidate: HuntCandidate,
    *,
    character_level: int,
    boot_id: str | int | None,
) -> bool:
    """Honor live below-band evidence before selecting a funding kill."""
    raw = state.get(_BELOW_BAND_POLICY_EXCLUSIONS_KEY)
    if not isinstance(raw, dict):
        return False
    target = normalize_item_name(candidate.target)
    for record in raw.values():
        if (
            not isinstance(record, dict)
            or record.get("level") != character_level
            or record.get("boot_id") != boot_id
        ):
            continue
        targets = record.get("targets")
        if isinstance(targets, (list, tuple, set)) and any(
            normalize_item_name(str(item)) == target for item in targets
        ):
            return True
    return False


def _source_ranked_target_identity(candidate: HuntCandidate) -> str:
    """Convert a source short description into the starter target identity."""
    target = normalize_item_name(candidate.target)
    return re.sub(r"^(?:a|an|the)\s+", "", target)


def _source_ranked_policy_id(
    candidate: HuntCandidate,
    *,
    character_level: int,
) -> str:
    """Return a stable, character-independent identity for one source reset."""
    area = re.sub(
        r"[^a-z0-9]+",
        "-",
        Path(candidate.area_file).stem.casefold(),
    ).strip("-") or "area"
    return (
        f"{_SOURCE_RANKED_POLICY_PREFIX}{area}-"
        f"{candidate.mobile_vnum}-{candidate.room_vnum}-{character_level}"
    )


def _source_ranked_candidate_record(
    candidate: HuntCandidate,
    *,
    character_level: int,
) -> dict[str, Any]:
    """Serialize the selected source candidate into a checkpoint-safe record."""
    return {
        "policy_id": _source_ranked_policy_id(
            candidate,
            character_level=character_level,
        ),
        "status": candidate.status,
        "score": candidate.score,
        "area_file": candidate.area_file,
        "mobile_vnum": candidate.mobile_vnum,
        "target": candidate.target,
        "target_keyword": candidate.target_keyword,
        "level": candidate.level,
        "room_vnum": candidate.room_vnum,
        "room_name": candidate.room_name,
        "route": list(candidate.route),
        "source_spawn_limit": candidate.source_spawn_limit,
        "room_spawn_count": candidate.room_spawn_count,
        "boot_kills": candidate.boot_kills,
        "loot": list(candidate.loot),
        "source_value": candidate.source_value,
        "contained_coins": candidate.contained_coins,
        "hazards": list(candidate.hazards),
        "equipped_weapons": list(candidate.equipped_weapons),
        "estimated_level_range": list(candidate.estimated_level_range),
        "estimated_base_hp_range": list(candidate.estimated_base_hp_range),
        "estimated_peak_round_damage": candidate.estimated_peak_round_damage,
        "autonomy_rejections": list(candidate.autonomy_rejections),
    }


def _source_ranked_candidate_from_record(
    value: object,
) -> HuntCandidate | None:
    """Restore a selected source candidate after a disconnect or process exit."""
    if not isinstance(value, Mapping):
        return None

    def text_tuple(key: str) -> tuple[str, ...]:
        raw = value.get(key)
        if not isinstance(raw, (list, tuple)):
            return ()
        return tuple(str(item) for item in raw)

    def int_pair(key: str) -> tuple[int, int]:
        raw = value.get(key)
        if not isinstance(raw, (list, tuple)) or len(raw) != 2:
            return (0, 0)
        try:
            return int(raw[0]), int(raw[1])
        except (TypeError, ValueError):
            return (0, 0)

    try:
        area_file = str(value.get("area_file") or "")
        target = str(value.get("target") or "")
        target_keyword = str(value.get("target_keyword") or "")
        if not area_file or not target or not target_keyword:
            return None
        return HuntCandidate(
            status=str(value.get("status") or "caution"),
            score=float(value.get("score") or 0),
            area_file=area_file,
            mobile_vnum=int(value.get("mobile_vnum") or 0),
            target=target,
            target_keyword=target_keyword,
            level=int(value.get("level") or 0),
            room_vnum=int(value.get("room_vnum") or 0),
            room_name=str(value.get("room_name") or ""),
            route=text_tuple("route"),
            source_spawn_limit=int(value.get("source_spawn_limit") or 0),
            room_spawn_count=int(value.get("room_spawn_count") or 0),
            boot_kills=int(value.get("boot_kills") or 0),
            loot=text_tuple("loot"),
            source_value=int(value.get("source_value") or 0),
            contained_coins=int(value.get("contained_coins") or 0),
            hazards=text_tuple("hazards"),
            equipped_weapons=text_tuple("equipped_weapons"),
            estimated_level_range=int_pair("estimated_level_range"),
            estimated_base_hp_range=int_pair("estimated_base_hp_range"),
            estimated_peak_round_damage=int(
                value.get("estimated_peak_round_damage") or 0
            ),
            autonomy_rejections=text_tuple("autonomy_rejections"),
        )
    except (TypeError, ValueError):
        return None


def _source_ranked_target_tokens(candidate: HuntCandidate) -> frozenset[str]:
    return frozenset(
        token
        for token in re.findall(
            r"[a-z0-9]+",
            _source_ranked_target_identity(candidate),
        )
        if token not in {"a", "an", "the"}
    )


def _source_ranked_result_status(
    candidate: HuntCandidate,
    state: Mapping[str, Any],
    *,
    character_level: int,
) -> str:
    """Classify a candidate against current-reboot research evidence."""
    boot_id = state.get("world_boot_id")
    results = _campaign_research_results(state)
    cooldowns = state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
    crowd_cooldowns = state.get(_RESEARCH_CROWD_COOLDOWN_KEY) or {}
    candidate_policy_id = _source_ranked_policy_id(
        candidate,
        character_level=character_level,
    )
    matching_results: list[tuple[str, Mapping[str, Any]]] = []
    target_tokens = _source_ranked_target_tokens(candidate)
    for raw_policy_id, raw_result in results.items():
        policy_id = str(raw_policy_id)
        if not isinstance(raw_result, Mapping):
            continue
        if raw_result.get("boot_id") != boot_id:
            continue
        if policy_id == candidate_policy_id:
            matching_results.append((policy_id, raw_result))
            continue
        policy_tokens = frozenset(re.findall(r"[a-z0-9]+", policy_id))
        if target_tokens and target_tokens.issubset(policy_tokens):
            matching_results.append((policy_id, raw_result))

    retryable = False
    cooldown_active = False
    productive = False
    for policy_id, result in matching_results:
        if result.get("viable") is True and result.get("completed_kill") is True:
            productive = True
            continue
        if (
            result.get("route_hazard")
            and not policy_id.startswith(_SOURCE_RANKED_POLICY_PREFIX)
        ):
            cooldown_active = True
            continue
        negative = bool(
            result.get("absent") is True
            or result.get("crowded") is True
            or result.get("route_hazard")
            or result.get("unattackable")
            or result.get("viable") is False
            or result.get("completed_kill") is False
        )
        if not negative:
            continue
        try:
            remaining = max(
                int(cooldowns.get(policy_id) or 0),
                int(crowd_cooldowns.get(policy_id) or 0),
            )
        except (TypeError, ValueError):
            remaining = 0
        if remaining > 0:
            cooldown_active = True
        else:
            retryable = True
    if cooldown_active:
        return "cooldown"
    if retryable:
        return "retryable"
    if productive:
        return "productive"
    return "fresh"


def _select_source_ranked_hunt_candidate(
    candidates: Collection[HuntCandidate],
    state: Mapping[str, Any],
    *,
    character_level: int,
) -> HuntCandidate | None:
    """Choose the safest fresh current-band source target for one segment."""
    if character_level < 13:
        return None
    valid: list[tuple[HuntCandidate, str]] = []
    for candidate in candidates:
        if (
            candidate.status == "reject"
            or not candidate.autonomous_safe
            or candidate.boot_kills >= 3
            or candidate.estimated_level_range[1] <= character_level - 5
            or candidate.estimated_level_range[1] > character_level + 1
            or _funding_candidate_is_below_band(
                dict(state),
                candidate,
                character_level=character_level,
                boot_id=state.get("world_boot_id"),
            )
        ):
            continue
        status = _source_ranked_result_status(
            candidate,
            state,
            character_level=character_level,
        )
        valid.append((candidate, status))
    if not valid:
        return None

    last_policy_id = str(state.get("campaign_last_policy") or "")

    def candidate_policy_id(candidate: HuntCandidate) -> str:
        return _source_ranked_policy_id(
            candidate,
            character_level=character_level,
        )

    persisted = _source_ranked_candidate_from_record(
        state.get(_SOURCE_RANKED_CANDIDATE_KEY)
    )
    if (
        persisted is not None
        and candidate_policy_id(persisted) == last_policy_id
        and _source_ranked_result_status(
            persisted,
            state,
            character_level=character_level,
        )
        == "fresh"
    ):
        return persisted

    def rank(item: tuple[HuntCandidate, str]) -> tuple[float, float, int, int]:
        candidate = item[0]
        return (
            float(candidate.estimated_level_range[1]),
            candidate.score,
            -len(candidate.route),
            candidate.source_value,
        )

    for preferred_status in ("fresh", "retryable", "productive"):
        choices = [
            item
            for item in valid
            if item[1] == preferred_status
            and candidate_policy_id(item[0]) != last_policy_id
        ]
        if choices:
            return max(choices, key=rank)[0]
    choices = [item for item in valid if item[1] != "cooldown"]
    return max(choices, key=rank)[0] if choices else None


def _select_provision_funding_candidate(
    state: dict[str, Any],
    *,
    character_level: int,
    boot_kill_counts: Mapping[str, int] | None,
    boot_id: str | int | None,
    source_directory: Path,
    gear_catalog: GearCatalog | None,
    prefer_completed_funding_candidate: bool = False,
) -> HuntCandidate | None:
    """Choose one source-safe current-reboot target to fund provisions.

    When flight money is the immediate blocker, reuse a same-reboot successful
    funding target before spending another segment on an untried candidate.
    Ordinary food funding keeps the broader fresh-candidate rotation.
    """
    if character_level < 2 or not source_directory.is_dir():
        return None
    world = load_world_source(source_directory, include_all_areas=True)
    candidates = rank_hunt_candidates(
        world,
        character_level=character_level,
        boot_kill_counts=boot_kill_counts,
        include_below_band=True,
        character_max_hp=(
            int(state["max_hp"])
            if isinstance(state.get("max_hp"), (int, float))
            else None
        ),
        include_all_areas=True,
    )
    attempted: set[str] = set()
    attempt_order: list[str] = []
    completed_attempts: set[str] = set()
    failed_attempts: set[str] = set()
    latest_attempt_completed: dict[str, bool] = {}
    last_attempted: str | None = None
    raw_attempts = state.get(_PROVISION_FUNDING_ATTEMPTS_KEY)
    if isinstance(raw_attempts, (list, tuple)):
        for record in raw_attempts:
            if not isinstance(record, dict) or record.get("boot_id") != boot_id:
                continue
            candidate_key = record.get("candidate_key")
            if candidate_key is None:
                continue
            candidate_key = str(candidate_key)
            attempted.add(candidate_key)
            if candidate_key not in attempt_order:
                attempt_order.append(candidate_key)
            last_attempted = candidate_key
            if record.get("completed_kill") is True:
                completed_attempts.add(candidate_key)
            else:
                failed_attempts.add(candidate_key)
            latest_attempt_completed[candidate_key] = (
                record.get("completed_kill") is True
            )
    last_attempt = state.get(_PROVISION_FUNDING_LAST_ATTEMPT_KEY)
    if (
        isinstance(last_attempt, dict)
        and last_attempt.get("boot_id") == boot_id
        and last_attempt.get("candidate_key") is not None
    ):
        last_attempted = str(last_attempt["candidate_key"])

    def funding_eligible_candidate(candidate: HuntCandidate) -> bool:
        candidate_key = _provision_funding_candidate_key(candidate)
        return (
            candidate.status != "reject"
            and candidate.autonomous_safe
            and candidate.estimated_level_range[1] <= character_level
            and (
                candidate.boot_kills < 3
                or (
                    prefer_completed_funding_candidate
                    and candidate_key in completed_attempts
                )
            )
            and _candidate_has_saleable_funding_drop(
                candidate,
                gear_catalog=gear_catalog,
            )
        )

    all_candidates = [
        candidate
        for candidate in candidates
        if funding_eligible_candidate(candidate)
    ]
    all_eligible = [
        candidate
        for candidate in all_candidates
        if _provision_funding_candidate_key(candidate) not in completed_attempts
    ]
    never_attempted = [
        candidate
        for candidate in all_eligible
        if _provision_funding_candidate_key(candidate) not in attempted
    ]
    eligible = never_attempted
    if not eligible:
        # A successful funding kill may have already been sold or spent. Once
        # every other source-safe candidate has had one bounded attempt, reuse
        # that target before cycling failed candidates forever.
        reusable_completed = [
            candidate
            for candidate in all_candidates
            if (
                _provision_funding_candidate_key(candidate) in completed_attempts
                and latest_attempt_completed.get(
                    _provision_funding_candidate_key(candidate)
                )
                is True
            )
        ]
        if reusable_completed:
            eligible = reusable_completed
        else:
            # A missing or failed reset is temporary. Once every source-safe
            # candidate has had one bounded attempt, rotate to another failed
            # candidate instead of declaring the generic money loop exhausted.
            retryable = [
                candidate
                for candidate in all_eligible
                if _provision_funding_candidate_key(candidate) in failed_attempts
            ]
            retryable_by_key = {
                _provision_funding_candidate_key(candidate): candidate
                for candidate in retryable
            }
            if last_attempted in attempt_order:
                start = attempt_order.index(last_attempted) + 1
                rotated_keys = attempt_order[start:] + attempt_order[:start]
                eligible = [
                    retryable_by_key[key]
                    for key in rotated_keys
                    if key in retryable_by_key
                ][:1]
            else:
                eligible = retryable
    reusable_completed = [
        candidate
        for candidate in all_candidates
        if (
            _provision_funding_candidate_key(candidate) in completed_attempts
            and latest_attempt_completed.get(
                _provision_funding_candidate_key(candidate)
            )
            is True
        )
    ]
    if prefer_completed_funding_candidate and reusable_completed:
        eligible = reusable_completed
    preferred = [
        candidate
        for candidate in eligible
        if not _funding_candidate_is_below_band(
            state,
            candidate,
            character_level=character_level,
            boot_id=boot_id,
        )
    ]
    # A money-only segment may use a source-safe, already below-band carrier
    # when every non-excluded saleable target is exhausted. The dispatch layer
    # marks its first saleable drop as required loot so this is never treated
    # as an XP hunt.
    below_band_fallback = not preferred
    eligible = preferred or eligible
    if not eligible:
        return None
    if below_band_fallback:
        return max(
            eligible,
            key=lambda candidate: (
                -len(candidate.route),
                candidate.contained_coins > 0,
                candidate.source_value,
                candidate.score,
                min(candidate.estimated_level_range[1], character_level),
            ),
        )
    return max(
        eligible,
        key=lambda candidate: (
            min(candidate.estimated_level_range[1], character_level),
            candidate.contained_coins > 0,
            candidate.source_value,
            candidate.score,
            -len(candidate.route),
        ),
    )


def _record_provision_funding_attempt(
    state: dict[str, Any],
    *,
    candidate: HuntCandidate,
    boot_id: str | int | None,
    completed_kill: bool,
) -> dict[str, Any]:
    """Persist a funding attempt without losing the need for provisions."""
    recorded = dict(state)
    attempts = [
        dict(record)
        for record in state.get(_PROVISION_FUNDING_ATTEMPTS_KEY, ())
        if isinstance(record, dict)
    ]
    attempts.append(
        {
            "boot_id": boot_id,
            "candidate_key": _provision_funding_candidate_key(candidate),
            "target": candidate.target,
            "room_vnum": candidate.room_vnum,
            "completed_kill": completed_kill,
        }
    )
    recorded[_PROVISION_FUNDING_ATTEMPTS_KEY] = attempts[-12:]
    recorded[_PROVISION_FUNDING_LAST_ATTEMPT_KEY] = {
        "boot_id": boot_id,
        "candidate_key": _provision_funding_candidate_key(candidate),
        "completed_kill": completed_kill,
    }
    if completed_kill:
        recorded.pop(_PROVISION_FUNDING_REQUIRED_KEY, None)
    else:
        recorded[_PROVISION_FUNDING_REQUIRED_KEY] = True
    return recorded


def _has_campaign_food(
    state: dict[str, Any],
    *,
    gear_catalog: GearCatalog | None,
) -> bool:
    if "inventory" not in state:
        return True
    for description in _inventory_descriptions(state.get("inventory")):
        normalized = normalize_item_name(description)
        if "pie" in normalized or "steak" in normalized:
            return True
        item = gear_catalog.match(description) if gear_catalog is not None else None
        if (
            item is not None
            and item.item_type == 19
            and len(item.values) >= 4
            and item.values[3] <= 0
        ):
            return True
    return False


def _needs_piercing_weapon_upgrade(
    state: dict[str, Any],
    *,
    gear_catalog: GearCatalog | None,
    character_class: str,
    subclass: str | None,
    target_vnum: int = _PIERCING_WEAPON_UPGRADE_VNUM,
) -> bool:
    """Compare known carried piercing weapons with the registered source upgrade."""
    if gear_catalog is None:
        return False
    target = gear_catalog.objects.get(target_vnum)
    if (
        target is None
        or not is_piercing_weapon(target)
        or not character_can_use_item(
            target,
            character_class=character_class,
            subclass=subclass,
        )
    ):
        return False
    descriptions = [
        *(
            str(description)
            for description in state.get("campaign_worn_equipment") or ()
        ),
        *_inventory_descriptions(state.get("inventory")),
    ]
    current_score = max(
        (
            weapon_damage_score(item)
            for description in descriptions
            if (item := gear_catalog.match(description)) is not None
            if is_piercing_weapon(item)
            and character_can_use_item(
                item,
                character_class=character_class,
                subclass=subclass,
            )
        ),
        default=0,
    )
    return current_score < weapon_damage_score(target)


def _state_has_source_weapon_role(
    state: dict[str, Any],
    *,
    gear_catalog: GearCatalog | None,
    character_class: str,
    subclass: str | None,
    predicate: Callable[[Any], bool],
    worn_only: bool = False,
) -> bool:
    """Return whether persisted inventory or worn gear proves a weapon role."""
    if gear_catalog is None:
        return False
    if worn_only and (
        state.get("campaign_has_weapon") is False
        or "wield" in set(state.get("campaign_empty_equipment_categories") or ())
    ):
        # A direct ``You wield`` acknowledgement can be left over from an
        # earlier response chunk or segment.  An explicit empty current slot,
        # or a reconciled false weapon flag, is stronger evidence.
        return False
    primary_weapon = state.get("campaign_primary_weapon")
    if worn_only and "campaign_primary_weapon" in state:
        descriptions = [str(primary_weapon)] if primary_weapon else []
    else:
        descriptions = [
            *(
                str(description)
                for description in state.get("campaign_worn_equipment") or ()
            )
        ]
    if not worn_only:
        descriptions.extend(_inventory_descriptions(state.get("inventory")))
    # The persisted worn description is the primary proof of a wielded role;
    # inventory evidence is also useful when a disarm or reconnect has left
    # the item carried.  Source matching already restricts this to usable
    # catalog objects, and the role predicate restricts it to real weapons.
    return any(
        predicate(item)
        for item in gear_catalog.match_many_usable(
            descriptions,
            character_class=character_class,
            subclass=subclass,
        )
    )


def _state_needs_better_piercing_weapon(
    state: dict[str, Any],
    *,
    gear_catalog: GearCatalog | None,
    character_class: str,
    subclass: str | None,
) -> bool:
    """Return whether a carried piercing weapon outranks the worn primary."""
    if gear_catalog is None:
        return False
    current_weapon = None
    primary_description = state.get("campaign_primary_weapon")
    if isinstance(primary_description, str) and primary_description.strip():
        candidate = gear_catalog.match(primary_description)
        if candidate is not None and item_category(candidate) == "wield":
            current_weapon = candidate
    if current_weapon is None:
        for description in state.get("campaign_worn_equipment") or ():
            candidate = gear_catalog.match(str(description))
            if candidate is not None and item_category(candidate) == "wield":
                current_weapon = candidate
                break
    if current_weapon is None or not is_piercing_weapon(current_weapon):
        return True
    current_score = weapon_damage_score(current_weapon)
    return any(
        is_piercing_weapon(item)
        and weapon_damage_score(item) > current_score
        for item in gear_catalog.match_many_usable(
            _inventory_descriptions(state.get("inventory")),
            character_class=character_class,
            subclass=subclass,
        )
        if item_category(item) == "wield"
    )


def _has_own_corpse_recovery(
    state: dict[str, Any],
    character_name: str,
) -> bool:
    needle = f"corpse of {character_name}".casefold()
    acquisitions = state.get("acquired_items")
    if not isinstance(acquisitions, list):
        return False
    return any(
        needle in str(acquisition.get("item", "")).casefold()
        for acquisition in acquisitions
        if isinstance(acquisition, dict)
    )


def _campaign_policy_xp_deltas(
    segments: list[Any],
    *,
    storage: RunStorage | None = None,
) -> dict[str, int]:
    """Return each policy's latest bounded result, discounting unconfirmed hunts."""
    results: dict[str, int] = {}
    for segment in segments:
        if segment["status"] not in {"success", "ready"}:
            continue
        start = json.loads(segment["start_state_json"] or "{}")
        end = json.loads(segment["end_state_json"] or "{}")
        if not end:
            continue
        objective_kills = end.get("campaign_objective_kills")
        if objective_kills is None:
            # Older checkpoints have only the unfiltered combat record.
            objective_kills = end.get("campaign_completed_kills")
        if objective_kills is None and storage is not None and segment["run_id"]:
            objective_kills = _run_objective_kills(storage, int(segment["run_id"]))
        phase = str(segment["phase"])
        if (
            results.get(phase, 0) > 0
            and isinstance(objective_kills, list)
            and not objective_kills
            and any(
                str(end.get("campaign_fastwalk_abort_reason") or "").startswith(
                    prefix
                )
                for prefix in _FIELD_CROWD_ABORT_PREFIXES
            )
        ):
            # A crowded field is transient route-state evidence. Preserve a
            # confirmed productive result for this policy so a later rotation
            # can retry it after the crowd cooldown instead of erasing its
            # only useful progression path.
            continue
        results[phase] = _effective_policy_xp_delta(
            start,
            end,
            completed_kills=objective_kills,
        )
    return results


def _campaign_productive_policy_ids(
    segments: list[Any],
    *,
    storage: RunStorage | None = None,
    boot_id: str | int | None = None,
) -> frozenset[str]:
    """Collect same-reboot hunt policies with a confirmed positive kill."""
    productive: set[str] = set()
    for segment in segments:
        if segment["status"] not in {"success", "ready"}:
            continue
        phase = str(segment["phase"])
        if "-hunt" not in phase:
            continue
        try:
            start = json.loads(segment["start_state_json"] or "{}")
            end = json.loads(segment["end_state_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            continue
        if not end or (boot_id is not None and end.get("world_boot_id") != boot_id):
            continue
        objective_kills = end.get("campaign_objective_kills")
        if objective_kills is None:
            objective_kills = end.get("campaign_completed_kills")
        if objective_kills is None and storage is not None and segment["run_id"]:
            objective_kills = _run_objective_kills(storage, int(segment["run_id"]))
        if (
            isinstance(objective_kills, list)
            and objective_kills
            and _xp_delta(start, end) > 0
        ):
            productive.add(phase)
    return frozenset(productive)


def _state_productive_policy_ids(state: Mapping[str, Any]) -> frozenset[str]:
    """Read productive-policy history only when it matches the current boot."""
    history = state.get(_PRODUCTIVE_POLICY_HISTORY_KEY)
    if not isinstance(history, Mapping):
        return frozenset()
    if history.get("boot_id") != state.get("world_boot_id"):
        return frozenset()
    policy_ids = history.get("policy_ids")
    if not isinstance(policy_ids, (list, tuple, set, frozenset)):
        return frozenset()
    return frozenset(str(policy_id) for policy_id in policy_ids if policy_id)


def _mark_retryable_research_failures(state: dict[str, Any]) -> dict[str, Any]:
    """Keep productive hunts retryable after a safe, incomplete combat pass."""
    boot_id = state.get("world_boot_id")
    if boot_id is None:
        return state
    productive_policy_ids = _state_productive_policy_ids(state)
    if not productive_policy_ids:
        return state
    results = dict(state.get("campaign_research_results") or {})
    absence_cooldowns = dict(
        state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
    )
    cleared_research_policies = {
        str(policy_id)
        for policy_id in state.get(_CLEARED_RESEARCH_POLICIES_KEY, ())
    }
    changed = False
    for policy_id in productive_policy_ids:
        raw_result = results.get(policy_id)
        if not (
            isinstance(raw_result, dict)
            and raw_result.get("boot_id") == boot_id
            and raw_result.get("observed") is True
            and raw_result.get("viable") is False
            and raw_result.get("completed_kill") is False
            and not raw_result.get("absent")
            and not raw_result.get("route_hazard")
            and not raw_result.get("crowded")
            and not raw_result.get("unattackable")
        ):
            continue
        result = dict(raw_result)
        retry_cooldown = _research_absence_retry_cooldown(
            policy_id,
            default=_DEFAULT_RESEARCH_CROWD_COOLDOWN,
        )
        if not result.get("retryable_failure"):
            result["retryable_failure"] = True
            changed = True
        if not result.get("previously_productive"):
            result["previously_productive"] = True
            changed = True
        if results.get(policy_id) != result:
            results[policy_id] = result
            changed = True
        if absence_cooldowns.get(policy_id) != retry_cooldown:
            absence_cooldowns[policy_id] = retry_cooldown
            changed = True
        if policy_id in cleared_research_policies:
            cleared_research_policies.discard(policy_id)
            changed = True
    if not changed:
        return state
    updated = dict(state)
    updated["campaign_research_results"] = results
    updated[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
    if cleared_research_policies:
        updated[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(
            cleared_research_policies
        )
    else:
        updated.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
    return updated


def _with_productive_policy_history(
    state: Mapping[str, Any],
    *,
    policy_ids: Collection[str],
    boot_id: str | int | None,
) -> dict[str, Any]:
    """Merge durable same-reboot productive hunt identities into state."""
    updated = dict(state)
    if boot_id is None:
        return updated
    current_ids = _state_productive_policy_ids(state)
    merged_ids = current_ids | {str(policy_id) for policy_id in policy_ids}
    if merged_ids:
        updated[_PRODUCTIVE_POLICY_HISTORY_KEY] = {
            "boot_id": boot_id,
            "policy_ids": sorted(merged_ids),
        }
    else:
        updated.pop(_PRODUCTIVE_POLICY_HISTORY_KEY, None)
    return updated


def _effective_policy_xp_delta(
    start: dict[str, Any],
    end: dict[str, Any],
    *,
    completed_kills: Any,
) -> int:
    """Ignore incidental XP from a field segment with no confirmed kill."""
    xp_delta = _xp_delta(start, end)
    if xp_delta > 0 and isinstance(completed_kills, list) and not completed_kills:
        return 0
    return xp_delta


def _run_objective_kills(storage: RunStorage, run_id: int) -> list[Any] | None:
    """Read objective kills even when the runner failed after recording them."""
    for event in reversed(storage.list_events(run_id)):
        if event["kind"] != "state":
            continue
        payload = json.loads(event["payload_json"])
        objective_kills = payload.get("objective_kills")
        if isinstance(objective_kills, list):
            return objective_kills
        completed_kills = payload.get("completed_kills")
        if isinstance(completed_kills, list):
            return completed_kills
    return None


def _run_terminal_state(
    storage: RunStorage,
    run_id: int,
) -> dict[str, Any] | None:
    """Return the latest structured runner completion boundary."""
    for event in reversed(storage.list_events(run_id)):
        if event["kind"] != "state":
            continue
        payload = json.loads(event["payload_json"])
        if payload.get("state") not in {"completed", "runtime_cap"}:
            continue
        return payload
    return None


def _advance_retry_cooldown(
    state: dict[str, Any],
    *,
    key: str,
    execution: str,
    xp_delta: int,
) -> dict[str, Any]:
    """Advance an optional-loot retry only after productive field work."""
    if execution in _MAINTENANCE_EXECUTIONS or xp_delta <= 0:
        return state
    remaining = int(state.get(key) or 0)
    if remaining <= 0:
        return state
    updated = dict(state)
    updated[key] = remaining - 1
    return updated


def _advance_daycare_ring_cooldown(
    state: dict[str, Any],
    *,
    execution: str,
    xp_delta: int,
) -> dict[str, Any]:
    """Retry missing Daycare rings after other productive work."""
    return _advance_retry_cooldown(
        state,
        key=_DAYCARE_RING_COOLDOWN_KEY,
        execution=execution,
        xp_delta=xp_delta,
    )


def _advance_war_dog_collar_cooldown(
    state: dict[str, Any],
    *,
    execution: str,
    xp_delta: int,
) -> dict[str, Any]:
    """Retry missing war dog collars after other productive work."""
    return _advance_retry_cooldown(
        state,
        key=_WAR_DOG_COLLAR_COOLDOWN_KEY,
        execution=execution,
        xp_delta=xp_delta,
    )


def _advance_piercing_weapon_upgrade_cooldown(
    state: dict[str, Any],
    *,
    execution: str,
    xp_delta: int,
) -> dict[str, Any]:
    """Retry the Forest weapon after six productive field segments."""
    return _advance_retry_cooldown(
        state,
        key=_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY,
        execution=execution,
        xp_delta=xp_delta,
    )


def _advance_intermediate_piercing_weapon_upgrade_cooldown(
    state: dict[str, Any],
    *,
    execution: str,
    xp_delta: int,
) -> dict[str, Any]:
    """Retry the Thalos weapon after three productive field segments."""
    return _advance_retry_cooldown(
        state,
        key=_INTERMEDIATE_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY,
        execution=execution,
        xp_delta=xp_delta,
    )


def _advance_flight_purchase_cooldown(
    state: dict[str, Any],
    *,
    execution: str,
    xp_delta: int,
) -> dict[str, Any]:
    """Retry an optional flight purchase after productive field work."""
    return _advance_retry_cooldown(
        state,
        key=_FLIGHT_PURCHASE_COOLDOWN_KEY,
        execution=execution,
        xp_delta=xp_delta,
    )


def _xp_delta(before: dict[str, Any], after: dict[str, Any]) -> int:
    """Treat a level gain as progress even when DD4 resets cumulative XP."""
    level_delta = _level(after) - _level(before)
    if level_delta > 0:
        return max(1, level_delta)
    return _numeric_progress(after, "xp") - _numeric_progress(before, "xp")


def _campaign_segment_end_state(
    previous: dict[str, Any],
    current: dict[str, Any],
    *,
    execution: str,
) -> dict[str, Any]:
    """Keep maintenance facts sticky until their owning policy re-evaluates them."""
    merged = dict(current)
    for key in _CAMPAIGN_STICKY_METADATA_KEYS:
        if key not in merged and key in previous:
            merged[key] = previous[key]
    if not current.get("world_boot_id") and previous.get("world_boot_id"):
        merged["world_boot_id"] = previous["world_boot_id"]
    if (
        "combat_pouch_potions" not in current
        and "combat_pouch_potions" in previous
    ):
        merged["combat_pouch_potions"] = previous["combat_pouch_potions"]
    if (
        execution not in {"buy-flight", "buy-flight-potion"}
        and previous.get("magic_shop_purchase_failed")
    ):
        merged["magic_shop_purchase_failed"] = True
    if previous.get("vault_storage_rejected"):
        merged["vault_storage_rejected"] = True
    if _SACK_VAULT_ITEMS_KEY in previous:
        merged[_SACK_VAULT_ITEMS_KEY] = previous[_SACK_VAULT_ITEMS_KEY]
    if _SACK_VAULT_RECLAIM_LEVEL_KEY in previous:
        merged[_SACK_VAULT_RECLAIM_LEVEL_KEY] = previous[
            _SACK_VAULT_RECLAIM_LEVEL_KEY
        ]
    for owner, key in (
        ("outfit-basic-gear", "campaign_outfit_attempted_level"),
        ("recover-basic-body", "campaign_body_gear_attempted_level"),
        (
            "recover-school-wrist-float",
            "campaign_school_wrist_float_attempted_level",
        ),
        ("recover-gremlin-waist", "campaign_gremlin_waist_attempted_level"),
        ("recover-daycare-ring", "campaign_daycare_ring_attempted_level"),
        ("recover-daycare-ring", _DAYCARE_RING_ATTEMPT_BOOT_KEY),
        ("recover-daycare-ring", _DAYCARE_RING_COOLDOWN_KEY),
        ("recover-war-dog-collar", "campaign_war_dog_collar_attempted_level"),
        ("recover-war-dog-collar", _WAR_DOG_COLLAR_ATTEMPT_BOOT_KEY),
        ("recover-war-dog-collar", _WAR_DOG_COLLAR_COOLDOWN_KEY),
        (
            "recover-foundry-set-circlet",
            _FOUNDRY_SET_CIRCLET_ATTEMPTED_LEVEL_KEY,
        ),
        ("upgrade-piercing-weapon", _PIERCING_WEAPON_UPGRADE_BOOT_KEY),
        ("upgrade-piercing-weapon", _PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY),
    ):
        if execution != owner and key in previous:
            merged[key] = previous[key]
    if _INTERMEDIATE_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY in previous:
        merged[_INTERMEDIATE_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY] = previous[
            _INTERMEDIATE_PIERCING_WEAPON_UPGRADE_COOLDOWN_KEY
        ]
    return _apply_flight_funding_state_transition(
        previous,
        merged,
        execution=execution,
        funding_completed=False,
    )


def _apply_flight_funding_state_transition(
    previous: dict[str, Any],
    current: dict[str, Any],
    *,
    execution: str,
    funding_completed: bool,
) -> dict[str, Any]:
    """Advance the bounded flight-funding loop without mixing it with XP."""
    transitioned = dict(current)
    if execution == "provision-funding":
        if previous.get(_FLIGHT_FUNDING_REQUIRED_KEY) and funding_completed:
            transitioned.pop(_FLIGHT_FUNDING_REQUIRED_KEY, None)
            transitioned[_FLIGHT_FUNDING_RETRY_KEY] = True
        return transitioned
    if execution not in {"buy-flight", "buy-flight-potion"}:
        return transitioned

    active_flight = any(
        _state_has_active_affect(transitioned.get("affects"), effect)
        for effect in ("fly", "levitation")
    )
    if active_flight or transitioned.get("magic_shop_purchase_failed") is False:
        transitioned.pop(_FLIGHT_FUNDING_REQUIRED_KEY, None)
        transitioned.pop(_FLIGHT_FUNDING_RETRY_KEY, None)
        transitioned.pop(_FLIGHT_PURCHASE_COOLDOWN_KEY, None)
    elif transitioned.get("magic_shop_purchase_failed") is True:
        transitioned[_FLIGHT_FUNDING_REQUIRED_KEY] = True
        transitioned.pop(_FLIGHT_FUNDING_RETRY_KEY, None)
        transitioned[_FLIGHT_PURCHASE_COOLDOWN_KEY] = (
            _FLIGHT_PURCHASE_COOLDOWN_SEGMENTS
        )
    return transitioned


def _campaign_has_item(state: dict[str, Any], item_name: str) -> bool:
    """Check carried, worn, and newly acquired state for a named item."""
    target = normalize_item_name(item_name)
    descriptions = [
        *_inventory_descriptions(state.get("inventory")),
        *(
            str(description)
            for description in state.get("campaign_worn_equipment") or ()
        ),
        *(
            str(item.get("item", ""))
            for item in state.get("acquired_items") or ()
            if isinstance(item, dict)
        ),
    ]
    return any(
        target in normalize_item_name(description)
        for description in descriptions
    )


def _prioritize_sack_vault_claims(items: Any) -> tuple[str, ...]:
    """Reclaim combat-value gear before heavier fallback armour."""
    if not isinstance(items, (list, tuple)):
        return ()
    priority = {
        keyword: index
        for index, keyword in enumerate(
            ("collar", "bracer", "belt", "sleeves", "vest", "guards", "cape")
        )
    }
    unique = tuple(dict.fromkeys(str(item).casefold() for item in items))
    return tuple(
        sorted(unique, key=lambda item: (priority.get(item, len(priority)), item))
    )


def _campaign_research_results(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_results = state.get("campaign_research_results")
    if not isinstance(raw_results, dict):
        return {}
    return {
        str(policy_id): dict(result)
        for policy_id, result in raw_results.items()
        if isinstance(result, dict)
    }


def _repair_research_absence_cooldowns(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    """Drop absence cooldowns whose reboot-scoped evidence no longer exists."""
    raw_cooldowns = state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY)
    if not isinstance(raw_cooldowns, Mapping):
        return dict(state)
    results = _campaign_research_results(dict(state))
    boot_id = state.get("world_boot_id")
    retained: dict[str, int] = {}
    for raw_policy_id, raw_remaining in raw_cooldowns.items():
        policy_id = str(raw_policy_id)
        try:
            remaining = int(raw_remaining)
        except (TypeError, ValueError):
            continue
        result = results.get(policy_id)
        if (
            remaining <= 0
            or not isinstance(result, dict)
            or result.get("boot_id") != boot_id
            or not (
                result.get("absent") is True
                or result.get("route_hazard")
                == _DYNAMIC_FIELD_ROUTE_HAZARD_ABORT_REASON
                or result.get("retryable_failure") is True
            )
        ):
            continue
        retained[policy_id] = remaining
    original = dict(raw_cooldowns)
    if retained == original:
        return dict(state)
    repaired = dict(state)
    if retained:
        repaired[_RESEARCH_ABSENCE_COOLDOWN_KEY] = retained
    else:
        repaired.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
    return repaired


def _repair_protection_recovery_metadata(
    state: Mapping[str, Any],
    segments: list[Any],
    *,
    storage: RunStorage | None = None,
) -> dict[str, Any]:
    """Recover a current-reboot protection need from recorded hunt evidence."""
    updated = dict(state)
    if _state_has_sanctuary_reserve(updated):
        updated.pop(_PROTECTION_RECOVERY_KEY, None)
        return updated
    boot_id = updated.get("world_boot_id")
    if boot_id is None:
        return updated
    existing = updated.get(_PROTECTION_RECOVERY_KEY)
    if (
        isinstance(existing, Mapping)
        and existing.get("boot_id") == boot_id
    ):
        return updated
    for segment in reversed(segments):
        if segment["status"] not in {"success", "ready"}:
            continue
        phase = str(segment["phase"])
        if "-hunt-" not in phase:
            continue
        try:
            start = json.loads(segment["start_state_json"] or "{}")
            end = json.loads(segment["end_state_json"] or "{}")
        except (TypeError, json.JSONDecodeError):
            continue
        if not end or end.get("world_boot_id") != boot_id:
            continue
        outcomes = end.get("campaign_fastwalk_consider_outcomes")
        if not (
            isinstance(outcomes, Mapping)
            and any(value is True for value in outcomes.values())
        ):
            continue
        objective_kills = end.get("campaign_objective_kills")
        if objective_kills is None:
            objective_kills = end.get("campaign_completed_kills")
        if objective_kills is None and storage is not None and segment["run_id"]:
            objective_kills = _run_objective_kills(storage, int(segment["run_id"]))
        if not isinstance(objective_kills, list) or objective_kills:
            continue
        xp_delta = _xp_delta(start, end)
        if xp_delta >= 0:
            continue
        updated[_PROTECTION_RECOVERY_KEY] = {
            "boot_id": boot_id,
            "level": _level(end),
            "policy_id": phase,
            "xp_delta": xp_delta,
            "reason": "recorded viable hunt withdrew with an XP loss before a kill",
        }
        return updated
    return updated


def _remember_last_productive_policy(
    state: dict[str, Any],
    *,
    policy_xp_deltas: Mapping[str, int],
) -> dict[str, Any]:
    """Keep a current-reboot hunt available after an absent research probe."""
    results = _campaign_research_results(state)
    boot_id = state.get("world_boot_id")

    def is_productive(policy_id: str) -> bool:
        result = results.get(policy_id)
        return bool(
            isinstance(result, dict)
            and result.get("boot_id") == boot_id
            and result.get("observed") is True
            and result.get("viable") is True
            and result.get("completed_kill") is True
            and "-hunt" in str(policy_id)
        )

    existing = state.get(_LAST_PRODUCTIVE_POLICY_KEY)
    if isinstance(existing, str) and is_productive(existing):
        return state
    candidates = [
        str(policy_id)
        for policy_id, delta in policy_xp_deltas.items()
        if int(delta or 0) > 0 and is_productive(str(policy_id))
    ]
    if not candidates:
        return state
    selected = max(
        candidates,
        key=lambda policy_id: (
            int(policy_xp_deltas.get(policy_id, 0) or 0),
            policy_id,
        ),
    )
    if existing == selected:
        return state
    remembered = dict(state)
    remembered[_LAST_PRODUCTIVE_POLICY_KEY] = selected
    return remembered


def _historical_productive_handoff_policy_id(
    state: Mapping[str, Any],
    *,
    current_group: frozenset[str],
) -> str | None:
    """Find a previously productive hunt whose current miss is retryable."""
    history = state.get(_PRODUCTIVE_POLICY_HISTORY_KEY)
    boot_id = state.get("world_boot_id")
    if not isinstance(history, Mapping) or history.get("boot_id") != boot_id:
        return None
    policy_ids = history.get("policy_ids")
    if not isinstance(policy_ids, (list, tuple, set, frozenset)):
        return None
    cooldowns = state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
    results = _campaign_research_results(dict(state))
    candidates: list[str] = []
    for raw_policy_id in policy_ids:
        policy_id = str(raw_policy_id)
        if "-hunt-" not in policy_id or policy_id in current_group:
            continue
        probe_id = policy_id.replace("-hunt-", "-probe-", 1)
        if any(
            int(cooldowns.get(candidate_id) or 0) > 0
            for candidate_id in (policy_id, probe_id)
        ):
            continue
        hunt_result = results.get(policy_id)
        probe_result = results.get(probe_id)
        blocked = False
        for result, is_hunt in (
            (hunt_result, True),
            (probe_result, False),
        ):
            if not isinstance(result, dict) or result.get("boot_id") != boot_id:
                continue
            if result.get("absent") is True or result.get("unobserved") is True:
                continue
            if is_hunt and result.get("completed_kill") is False:
                blocked = True
                break
            if result.get("observed") is True and result.get("viable") is True:
                continue
            blocked = True
            break
        if not blocked:
            candidates.append(policy_id)
    return sorted(candidates)[0] if candidates else None


def _state_has_sanctuary_reserve(state: Mapping[str, Any]) -> bool:
    """Return whether a usable sanctuary potion is carried or pouch-held."""
    if _state_has_item(state.get("inventory"), "purple potion"):
        return True
    try:
        return int(
            dict(state.get("combat_pouch_potions") or {}).get("purple", 0)
            or 0
        ) > 0
    except (TypeError, ValueError):
        return False


def _protection_recovery_required(state: Mapping[str, Any]) -> bool:
    """Return whether a current-reboot hunt needs a protection upgrade."""
    record = state.get(_PROTECTION_RECOVERY_KEY)
    if not isinstance(record, Mapping):
        return False
    if record.get("boot_id") != state.get("world_boot_id"):
        return False
    return not _state_has_sanctuary_reserve(state)


def _campaign_sanctuary_recovery_required(state: dict[str, Any]) -> bool:
    """Return whether a current-reboot protected hunt still needs a reserve."""
    boot_id = state.get("world_boot_id")
    results = _campaign_research_results(state)
    for policy_id in (
        _SHIRE_ELVEN_WIZARD_HUNT_POLICY_ID,
        _HIGHTOWER_JAILOR_HUNT_POLICY_ID,
        _SOLACE_LORD_DOOM_HUNT_POLICY_ID,
        _SOLACE_LORD_DOOM_SANCTUARY_HUNT_POLICY_ID,
    ):
        result = results.get(policy_id)
        if (
            isinstance(result, dict)
            and result.get("boot_id") == boot_id
            and result.get("completed_kill") is False
        ):
            return True
    return False


def _campaign_productive_sanctuary_handoff(
    state: dict[str, Any],
    *,
    character_class: str,
) -> str | None:
    """Keep a productive hunt running while a required Moria pass is crowded."""
    if character_class.casefold() != "thief" or _level(state) < 17:
        return None
    if (
        int(
            dict(state.get("combat_pouch_potions") or {}).get("purple", 0)
            or 0
        )
        > 0
        or _state_has_item(state.get("inventory"), "purple potion")
    ):
        return None
    if not _campaign_sanctuary_recovery_required(state):
        return None
    policy_id = _MORIA_SANCTUARY_THIEF_LEVEL_SEVENTEEN_POLICY_ID
    result = _campaign_research_results(state).get(policy_id)
    cooldowns = state.get(_RESEARCH_CROWD_COOLDOWN_KEY) or {}
    if not (
        isinstance(result, dict)
        and result.get("crowded") is True
        and result.get("boot_id") == state.get("world_boot_id")
        and isinstance(cooldowns, dict)
    ):
        return None
    try:
        if int(cooldowns.get(policy_id) or 0) <= 0:
            return None
    except (TypeError, ValueError):
        return None
    productive_policy_id = state.get(_LAST_PRODUCTIVE_POLICY_KEY)
    productive_result = (
        _campaign_research_results(state).get(productive_policy_id)
        if isinstance(productive_policy_id, str)
        else None
    )
    if not (
        isinstance(productive_policy_id, str)
        and "-hunt" in productive_policy_id
        and isinstance(productive_result, dict)
        and productive_result.get("boot_id") == state.get("world_boot_id")
        and productive_result.get("observed") is True
        and (
            (
                productive_result.get("viable") is True
                and productive_result.get("completed_kill") is not False
            )
            or (
                state.get(_LAST_PRODUCTIVE_POLICY_KEY) == productive_policy_id
                and productive_result.get("completed_kill") is False
            )
        )
    ):
        return None
    if productive_policy_id in {
        _SHIRE_ELVEN_WIZARD_HUNT_POLICY_ID,
        _HIGHTOWER_JAILOR_HUNT_POLICY_ID,
        _SOLACE_LORD_DOOM_HUNT_POLICY_ID,
        _SOLACE_LORD_DOOM_SANCTUARY_HUNT_POLICY_ID,
    }:
        # A crowd checkpoint must never bypass the progression safety gate
        # for a caster hunt that requires a currently carried potion.
        return None
    return productive_policy_id


def _campaign_below_band_policy_ids(
    state: dict[str, Any],
    *,
    level: int,
    boot_id: str | int | None,
) -> frozenset[str]:
    """Return policies rejected by live consider at this level and reboot."""
    raw = state.get(_BELOW_BAND_POLICY_EXCLUSIONS_KEY)
    if not isinstance(raw, dict):
        return frozenset()
    return frozenset(
        str(policy_id)
        for policy_id, record in raw.items()
        if isinstance(record, dict)
        and record.get("level") == level
        and record.get("boot_id") == boot_id
    )


def _below_band_sighting_pairs(value: Any) -> set[tuple[str, str]]:
    if not isinstance(value, (list, tuple, set)):
        return set()
    pairs: set[tuple[str, str]] = set()
    for sighting in value:
        if not isinstance(sighting, dict):
            continue
        room_vnum = sighting.get("room_vnum")
        target = sighting.get("target")
        if room_vnum is None or target is None:
            continue
        room = str(room_vnum).strip()
        target_name = str(target).strip().casefold()
        if room and target_name:
            pairs.add((room, target_name))
    return pairs


def _campaign_below_band_sightings(
    state: dict[str, Any],
    policy_id: str,
    *,
    level: int,
    boot_id: str | int | None,
) -> frozenset[tuple[str, str]]:
    raw = state.get(_BELOW_BAND_SIGHTINGS_KEY)
    if not isinstance(raw, dict):
        return frozenset()
    record = raw.get(policy_id)
    if (
        not isinstance(record, dict)
        or record.get("level") != level
        or record.get("boot_id") != boot_id
    ):
        return frozenset()
    return frozenset(_below_band_sighting_pairs(record.get("sightings")))


def _merge_campaign_below_band_policy_exclusions(
    previous: dict[str, Any],
    current: dict[str, Any],
    *,
    policy: ProgressionPolicy,
    level: int,
    boot_id: str | int | None,
) -> dict[str, Any]:
    """Persist live below-band rejections until level or reboot changes."""
    merged = dict(current)
    raw = previous.get(_BELOW_BAND_POLICY_EXCLUSIONS_KEY)
    exclusions = {
        str(policy_id): dict(record)
        for policy_id, record in (raw.items() if isinstance(raw, dict) else ())
        if isinstance(record, dict)
        and record.get("level") == level
        and record.get("boot_id") == boot_id
    }
    previous_sightings = previous.get(_BELOW_BAND_SIGHTINGS_KEY)
    sightings_by_policy: dict[str, set[tuple[str, str]]] = {}
    if isinstance(previous_sightings, dict):
        for policy_id, record in previous_sightings.items():
            if (
                isinstance(record, dict)
                and record.get("level") == level
                and record.get("boot_id") == boot_id
            ):
                pairs = _below_band_sighting_pairs(record.get("sightings"))
                if pairs:
                    sightings_by_policy[str(policy_id)] = pairs
    current_sightings = _below_band_sighting_pairs(
        current.get("campaign_fastwalk_below_band_sightings")
    )
    if current_sightings:
        sightings_by_policy.setdefault(policy.policy_id, set()).update(
            current_sightings
        )
    targets = current.get("campaign_fastwalk_below_band_targets")
    if policy.allow_partial_below_band:
        outcomes = current.get("campaign_fastwalk_consider_outcomes")
        has_viable_stop = isinstance(outcomes, dict) and any(
            value is True for value in outcomes.values()
        )
        below_band_evidence = (
            list(targets)
            if isinstance(targets, (list, tuple, set)) and targets
            else [target for _, target in current_sightings]
        )
        if below_band_evidence and not has_viable_stop:
            # A multi-stop hunt may tolerate one below-band mobile only when
            # another stop remains inside the useful XP band.
            exclusions[policy.policy_id] = {
                "level": level,
                "boot_id": boot_id,
                "targets": sorted(
                    {str(target).casefold() for target in below_band_evidence}
                ),
            }
        else:
            exclusions.pop(policy.policy_id, None)
    elif isinstance(targets, (list, tuple, set)) and targets:
        exclusions[policy.policy_id] = {
            "level": level,
            "boot_id": boot_id,
            "targets": sorted({str(target).casefold() for target in targets}),
        }
    if exclusions:
        merged[_BELOW_BAND_POLICY_EXCLUSIONS_KEY] = exclusions
    else:
        merged.pop(_BELOW_BAND_POLICY_EXCLUSIONS_KEY, None)
    if sightings_by_policy:
        merged[_BELOW_BAND_SIGHTINGS_KEY] = {
            policy_id: {
                "level": level,
                "boot_id": boot_id,
                "sightings": [
                    {"room_vnum": room_vnum, "target": target}
                    for room_vnum, target in sorted(pairs)
                ],
            }
            for policy_id, pairs in sorted(sightings_by_policy.items())
        }
    else:
        merged.pop(_BELOW_BAND_SIGHTINGS_KEY, None)
    return merged


def _merge_protection_recovery_metadata(
    current: dict[str, Any],
    *,
    policy: ProgressionPolicy,
    xp_delta: int,
) -> dict[str, Any]:
    """Remember a costly failed hunt until a protection reserve is restored."""
    updated = dict(current)
    if _state_has_sanctuary_reserve(updated):
        updated.pop(_PROTECTION_RECOVERY_KEY, None)
        return updated
    execution = str(policy.execution or "")
    outcomes = updated.get("campaign_fastwalk_consider_outcomes")
    viable = isinstance(outcomes, Mapping) and any(
        value is True for value in outcomes.values()
    )
    if (
        policy.status == "research"
        and execution.endswith("-hunt")
        and not updated.get("campaign_objective_kills")
        and viable
        and xp_delta < 0
        and updated.get("world_boot_id") is not None
    ):
        updated[_PROTECTION_RECOVERY_KEY] = {
            "boot_id": updated.get("world_boot_id"),
            "level": _level(updated),
            "policy_id": policy.policy_id,
            "xp_delta": xp_delta,
            "reason": "viable hunt withdrew with an XP loss before a kill",
        }
    return updated


def _merge_campaign_research_result(
    previous: dict[str, Any],
    current: dict[str, Any],
    *,
    policy: ProgressionPolicy,
) -> dict[str, Any]:
    """Persist one reboot-scoped live consideration for research promotion."""
    merged = dict(current)
    results = _campaign_research_results(previous)
    absence_cooldowns = dict(
        previous.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
    )
    crowd_cooldowns = dict(
        previous.get(_RESEARCH_CROWD_COOLDOWN_KEY) or {}
    )
    cleared_research_policies = {
        str(policy_id)
        for policy_id in previous.get(_CLEARED_RESEARCH_POLICIES_KEY, ())
    }
    recorded_current_result = False
    if policy.status == "research":
        outcomes = current.get("campaign_fastwalk_consider_outcomes")
        viable = None
        if isinstance(outcomes, dict):
            boolean_outcomes = [
                value for value in outcomes.values() if isinstance(value, bool)
            ]
            if boolean_outcomes:
                viable = any(boolean_outcomes)
        fastwalk_abort_reason = str(
            current.get("campaign_fastwalk_abort_reason") or ""
        )
        hunt_without_confirmed_kill = bool(
            str(policy.execution or "").endswith("-hunt")
            and not current.get("campaign_objective_kills")
        )
        unobserved_hunt = bool(
            hunt_without_confirmed_kill
            and viable is None
            and not current.get("campaign_fastwalk_consider_outcomes")
            and not current.get("campaign_fastwalk_target_absent")
            and not current.get("campaign_fastwalk_abort_reason")
            and not current.get("campaign_fastwalk_unattackable_target")
        )
        unattackable_target = current.get(
            "campaign_fastwalk_unattackable_target"
        )
        crowded_field = any(
            fastwalk_abort_reason.startswith(prefix)
            for prefix in _FIELD_CROWD_ABORT_PREFIXES
        )
        route_hazard = any(
            fastwalk_abort_reason.startswith(prefix)
            for prefix in _FIELD_ROUTE_HAZARD_ABORT_PREFIXES
        )
        if route_hazard:
            results[policy.policy_id] = {
                "observed": False,
                "viable": False,
                "route_hazard": fastwalk_abort_reason,
                "boot_id": current.get("world_boot_id"),
            }
            recorded_current_result = True
            if fastwalk_abort_reason == _DYNAMIC_FIELD_ROUTE_HAZARD_ABORT_REASON:
                retry_cooldown = _research_absence_retry_cooldown(
                    policy.policy_id
                )
                if retry_cooldown is not None:
                    absence_cooldowns[policy.policy_id] = retry_cooldown
            else:
                absence_cooldowns.pop(policy.policy_id, None)
            crowd_cooldowns.pop(policy.policy_id, None)
        elif crowded_field:
            previous_result = results.get(policy.policy_id)
            preserve_positive_result = (
                isinstance(previous_result, dict)
                and current.get("world_boot_id") is not None
                and previous_result.get("boot_id") == current.get("world_boot_id")
                and previous_result.get("viable") is True
                and previous_result.get("completed_kill") is not False
            )
            if not preserve_positive_result:
                results[policy.policy_id] = {
                    "observed": False,
                    "viable": False,
                    "crowded": True,
                    "boot_id": current.get("world_boot_id"),
                }
                crowd_cooldowns[policy.policy_id] = (
                    _DEFAULT_RESEARCH_CROWD_COOLDOWN
                )
                absence_cooldowns.pop(policy.policy_id, None)
            else:
                absence_cooldowns.pop(policy.policy_id, None)
                crowd_cooldowns.pop(policy.policy_id, None)
            recorded_current_result = True
        elif unattackable_target:
            results[policy.policy_id] = {
                "observed": viable is not None,
                "viable": False,
                "unattackable": str(unattackable_target),
                "boot_id": current.get("world_boot_id"),
            }
            recorded_current_result = True
            absence_cooldowns.pop(policy.policy_id, None)
            crowd_cooldowns.pop(policy.policy_id, None)
        aborted_without_consider = bool(
            current.get("campaign_fastwalk_abort_reason")
            and viable is None
            and not current.get("campaign_fastwalk_target_absent")
        )
        source_ranked_route_abort = bool(
            policy.execution == "source-ranked-hunt"
            and aborted_without_consider
        )
        if route_hazard or crowded_field or unattackable_target:
            pass
        elif source_ranked_route_abort:
            results[policy.policy_id] = {
                "observed": False,
                "viable": False,
                "route_hazard": fastwalk_abort_reason,
                "boot_id": current.get("world_boot_id"),
            }
            recorded_current_result = True
            retry_cooldown = _research_absence_retry_cooldown(
                policy.policy_id,
                default=_DEFAULT_RESEARCH_CROWD_COOLDOWN,
            )
            if retry_cooldown is not None:
                absence_cooldowns[policy.policy_id] = retry_cooldown
            crowd_cooldowns.pop(policy.policy_id, None)
        elif aborted_without_consider:
            pass
        elif current.get("campaign_fastwalk_target_absent") and viable is None:
            results[policy.policy_id] = {
                "observed": False,
                "viable": False,
                "absent": True,
                "boot_id": current.get("world_boot_id"),
            }
            recorded_current_result = True
            retry_cooldown = _research_absence_retry_cooldown(
                policy.policy_id
            )
            if retry_cooldown is not None:
                absence_cooldowns[policy.policy_id] = retry_cooldown
            crowd_cooldowns.pop(policy.policy_id, None)
        elif hunt_without_confirmed_kill:
            # A positive consider proves only that the target was worth
            # probing. A research hunt is not viable until the runner records
            # the deliberate kill, even if the character dealt partial damage
            # before a safe withdrawal.
            result = {
                "observed": viable is not None,
                "viable": False,
                "completed_kill": False,
                "boot_id": current.get("world_boot_id"),
            }
            if unobserved_hunt:
                # A bounded hunt that never produced a live consideration did
                # not find a target to fight. Treat it as temporary absence so
                # the scheduler rotates to another policy instead of replaying
                # an empty, movement-expensive circuit immediately.
                result["absent"] = True
                result["unobserved"] = True
                retry_cooldown = _research_absence_retry_cooldown(
                    policy.policy_id
                )
                if retry_cooldown is not None:
                    absence_cooldowns[policy.policy_id] = retry_cooldown
            else:
                previous_result = results.get(policy.policy_id)
                same_boot = bool(
                    current.get("world_boot_id") is not None
                    and (
                        previous_result is None
                        or (
                            isinstance(previous_result, dict)
                            and previous_result.get("boot_id")
                            == current.get("world_boot_id")
                        )
                    )
                )
                previously_productive = bool(
                    same_boot
                    and (
                        policy.policy_id
                        in _state_productive_policy_ids(previous)
                        or (
                            isinstance(previous_result, dict)
                            and previous_result.get("viable") is True
                            and previous_result.get("completed_kill") is not False
                        )
                    )
                )
                if previously_productive and viable is True:
                    # Preserve positive same-reboot history, but do not replay
                    # a route that just failed to finish its target.
                    result["retryable_failure"] = True
                    result["previously_productive"] = True
                    retry_cooldown = _research_absence_retry_cooldown(
                        policy.policy_id,
                        default=_DEFAULT_RESEARCH_CROWD_COOLDOWN,
                    )
                    absence_cooldowns[policy.policy_id] = retry_cooldown
                else:
                    absence_cooldowns.pop(policy.policy_id, None)
            results[policy.policy_id] = result
            recorded_current_result = True
            crowd_cooldowns.pop(policy.policy_id, None)
        else:
            result = {
                "observed": viable is not None,
                "viable": viable is True,
                "boot_id": current.get("world_boot_id"),
            }
            if (
                policy.policy_id == _MORIA_SANCTUARY_THIEF_LEVEL_SEVENTEEN_POLICY_ID
                and current.get("campaign_objective_kills")
            ):
                result["objective_kill"] = True
            results[policy.policy_id] = result
            recorded_current_result = True
            absence_cooldowns.pop(policy.policy_id, None)
            crowd_cooldowns.pop(policy.policy_id, None)
        if recorded_current_result:
            cleared_research_policies.discard(policy.policy_id)
    if results:
        merged["campaign_research_results"] = results
    if absence_cooldowns:
        merged[_RESEARCH_ABSENCE_COOLDOWN_KEY] = absence_cooldowns
    else:
        merged.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
    if crowd_cooldowns:
        merged[_RESEARCH_CROWD_COOLDOWN_KEY] = crowd_cooldowns
    else:
        merged.pop(_RESEARCH_CROWD_COOLDOWN_KEY, None)
    if cleared_research_policies:
        merged[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(
            cleared_research_policies
        )
    else:
        merged.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
    return merged


def _clear_crowd_absence_marker(state: dict[str, Any]) -> dict[str, Any]:
    """Undo the old crowd-as-absence encoding without touching real absence."""
    reason = str(state.get("campaign_fastwalk_abort_reason") or "")
    if not reason.startswith("field room contained "):
        return state
    policy_id = state.get("campaign_last_policy")
    if not isinstance(policy_id, str) or not policy_id:
        return state
    results = _campaign_research_results(state)
    result = results.get(policy_id)
    if not isinstance(result, dict) or not result.get("absent"):
        return state
    results.pop(policy_id, None)
    repaired = dict(state)
    if results:
        repaired["campaign_research_results"] = results
    else:
        repaired.pop("campaign_research_results", None)
    cooldowns = dict(repaired.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {})
    cooldowns.pop(policy_id, None)
    if cooldowns:
        repaired[_RESEARCH_ABSENCE_COOLDOWN_KEY] = cooldowns
    else:
        repaired.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
    cleared_research_policies = {
        str(policy_id)
        for policy_id in state.get(_CLEARED_RESEARCH_POLICIES_KEY, ())
    }
    cleared_research_policies.add(policy_id)
    repaired[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(
        cleared_research_policies
    )
    repaired["campaign_fastwalk_target_absent"] = False
    return repaired


def _clear_absent_research_results(
    state: dict[str, Any],
    *,
    except_policy_id: str,
) -> dict[str, Any]:
    """Retry missing or crowded reset targets after productive work elsewhere."""
    merged = dict(state)
    results = _campaign_research_results(state)
    cooldowns = dict(state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {})
    crowd_cooldowns = dict(
        state.get(_RESEARCH_CROWD_COOLDOWN_KEY) or {}
    )
    cleared_research_policies = {
        str(policy_id)
        for policy_id in state.get(_CLEARED_RESEARCH_POLICIES_KEY, ())
    }
    retained: dict[str, dict[str, Any]] = {}
    expired_retryable_groups: set[frozenset[str]] = set()
    for policy_id, result in results.items():
        if policy_id == except_policy_id:
            retained[policy_id] = result
            continue
        if result.get("retryable_failure"):
            remaining = int(
                cooldowns.get(
                    policy_id,
                    _research_absence_retry_cooldown(
                        policy_id,
                        default=_DEFAULT_RESEARCH_CROWD_COOLDOWN,
                    ),
                )
                or 0
            )
            if remaining > 1:
                retained[policy_id] = result
                cooldowns[policy_id] = remaining - 1
            else:
                cooldowns.pop(policy_id, None)
                expired_retryable_groups.add(
                    _research_retryable_failure_group(policy_id)
                )
                cleared_research_policies.add(policy_id)
            continue
        if not result.get("absent"):
            retained[policy_id] = result
            continue
        remaining = int(cooldowns.get(policy_id) or 0)
        if remaining > 1:
            retained[policy_id] = result
            cooldowns[policy_id] = remaining - 1
        else:
            cooldowns.pop(policy_id, None)
            cleared_research_policies.add(policy_id)
    for policy_id, result in list(retained.items()):
        if (
            policy_id == except_policy_id
            or not result.get("crowded")
            or result.get("boot_id") != state.get("world_boot_id")
        ):
            continue
        remaining = int(
            crowd_cooldowns.get(policy_id)
            or _DEFAULT_RESEARCH_CROWD_COOLDOWN
        )
        if remaining > 1:
            crowd_cooldowns[policy_id] = remaining - 1
        else:
            crowd_cooldowns.pop(policy_id, None)
            retained.pop(policy_id, None)
            cleared_research_policies.add(policy_id)
    for retryable_group in expired_retryable_groups:
        for policy_id in retryable_group:
            retained.pop(policy_id, None)
            cooldowns.pop(policy_id, None)
            crowd_cooldowns.pop(policy_id, None)
            cleared_research_policies.add(policy_id)
    if retained:
        merged["campaign_research_results"] = retained
    else:
        merged.pop("campaign_research_results", None)
    if cooldowns:
        merged[_RESEARCH_ABSENCE_COOLDOWN_KEY] = cooldowns
    else:
        merged.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
    if crowd_cooldowns:
        merged[_RESEARCH_CROWD_COOLDOWN_KEY] = crowd_cooldowns
    else:
        merged.pop(_RESEARCH_CROWD_COOLDOWN_KEY, None)
    if cleared_research_policies:
        merged[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(
            cleared_research_policies
        )
    else:
        merged.pop(_CLEARED_RESEARCH_POLICIES_KEY, None)
    return merged


def _campaign_should_await_research_reset(state: dict[str, Any]) -> bool:
    """Allow a bounded reset wait for an absent target or dynamic hazard."""
    policy_id = str(state.get("campaign_last_policy") or "")
    if not policy_id:
        return False
    results = _campaign_research_results(state)
    cooldowns = state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
    if not isinstance(cooldowns, dict):
        return False
    group = _research_absence_retry_group(policy_id)
    group_cooldown_active = any(
        int(cooldowns.get(candidate_id) or 0) > 0
        for candidate_id in group
    )
    if not group_cooldown_active:
        return False
    for candidate_id in group:
        result = results.get(candidate_id)
        if not isinstance(result, dict) or result.get("boot_id") != state.get(
            "world_boot_id"
        ):
            continue
        if not (
            result.get("absent") is True
            or result.get("route_hazard")
            == _DYNAMIC_FIELD_ROUTE_HAZARD_ABORT_REASON
            or (
                policy_id.startswith(_SOURCE_RANKED_POLICY_PREFIX)
                and result.get("route_hazard")
            )
        ):
            continue
        return True
    return False


def _campaign_has_pending_dynamic_route_hazard(state: dict[str, Any]) -> bool:
    """Identify a current dynamic route hazard that is waiting for reset."""
    policy_id = str(state.get("campaign_last_policy") or "")
    result = _campaign_research_results(state).get(policy_id)
    if not (
        isinstance(result, dict)
        and (
            result.get("route_hazard")
            == _DYNAMIC_FIELD_ROUTE_HAZARD_ABORT_REASON
            or (
                policy_id.startswith(_SOURCE_RANKED_POLICY_PREFIX)
                and result.get("route_hazard")
            )
        )
        and result.get("boot_id") == state.get("world_boot_id")
    ):
        return False
    cooldowns = state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
    return isinstance(cooldowns, dict) and int(cooldowns.get(policy_id) or 0) > 0


def _maintenance_failure_state(
    state: dict[str, Any],
    *,
    execution: str,
    boot_id: str | int | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    """Prevent a failed optional equipment errand from looping at one level."""
    attempted_level_key = _MAINTENANCE_ATTEMPT_LEVEL_KEYS.get(execution)
    if attempted_level_key is None:
        if execution == "restock" and (
            error is None
            or any(
                marker in (error or "").casefold()
                for marker in (
                    "no pie after purchase",
                    "can't even afford",
                    "not enough money",
                    "unaffordable",
                )
            )
        ):
            failed_state = dict(state)
            failed_state[_PROVISION_FUNDING_REQUIRED_KEY] = True
            return failed_state
        return state
    failed_state = dict(state)
    failed_state[attempted_level_key] = _level(state)
    if execution == "recover-daycare-ring":
        failed_state[_DAYCARE_RING_COOLDOWN_KEY] = _DAYCARE_RING_COOLDOWN_SEGMENTS
        if boot_id is not None:
            failed_state[_DAYCARE_RING_ATTEMPT_BOOT_KEY] = boot_id
    if execution == "recover-war-dog-collar" and boot_id is not None:
        failed_state[_WAR_DOG_COLLAR_ATTEMPT_BOOT_KEY] = boot_id
    if execution == "recover-war-dog-collar":
        failed_state[_WAR_DOG_COLLAR_COOLDOWN_KEY] = (
            _WAR_DOG_COLLAR_COOLDOWN_SEGMENTS
        )
    if execution == "restock" and (
        error is None
        or any(
            marker in error.casefold()
            for marker in (
                "no pie after purchase",
                "can't even afford",
                "not enough money",
                "unaffordable",
            )
        )
    ):
        failed_state[_PROVISION_FUNDING_REQUIRED_KEY] = True
    return failed_state


def _repair_failed_flight_funding_state(
    state: dict[str, Any],
    checkpoint: Any,
) -> dict[str, Any]:
    """Re-arm one pre-withdrawal funding failure after its bank fix."""
    if (
        checkpoint is None
        or checkpoint["reason"] != "segment_failed"
        or checkpoint["phase"] != "borrow-flight-potion"
        or not state.get("campaign_flight_loan_attempted")
        or state.get("campaign_flight_funding_repair_applied")
    ):
        return state
    repaired = dict(state)
    repaired["campaign_flight_loan_attempted"] = False
    repaired["campaign_flight_funding_repair_applied"] = True
    return repaired


def _repair_exhausted_flight_funding_state(
    state: dict[str, Any],
    *,
    has_sellable_loot: bool | None = None,
) -> dict[str, Any]:
    """Re-arm funding after a used flight reserve expires without cash."""
    affects = state.get("affects")
    if (
        affects is None
        or not state.get("campaign_flight_loan_attempted")
        or any(
            _state_has_active_affect(affects, effect)
            for effect in ("fly", "levitation")
        )
    ):
        return state
    if state.get(_FLIGHT_FUNDING_RETRY_KEY):
        if (
            has_sellable_loot is False
            and _state_copper_value(state) < 90
        ):
            if state.get(_FLIGHT_FUNDING_REQUIRED_KEY):
                return state
            repaired = dict(state)
            repaired[_FLIGHT_FUNDING_REQUIRED_KEY] = True
            return repaired
        if not state.get(_FLIGHT_FUNDING_REQUIRED_KEY):
            return state
        repaired = dict(state)
        repaired.pop(_FLIGHT_FUNDING_REQUIRED_KEY, None)
        return repaired
    if (
        state.get(_FLIGHT_FUNDING_REQUIRED_KEY)
        or _state_copper_value(state) >= 90
    ):
        return state
    repaired = dict(state)
    repaired[_FLIGHT_FUNDING_REQUIRED_KEY] = True
    return repaired


def _newer_progress_state(
    checkpoint: dict[str, Any],
    live: dict[str, Any] | None,
) -> dict[str, Any]:
    if not live:
        return checkpoint
    if (
        isinstance(live.get("level"), (int, float))
        and isinstance(live.get("xp"), (int, float))
    ):
        merged = {**checkpoint, **live}
        if (
            merged.get("dead")
            and str(merged.get("area", "")).casefold() != "purgatory"
            and _numeric_progress(merged, "hp") > 0
        ):
            merged["dead"] = False
        return merged
    checkpoint_progress = (_level(checkpoint), _numeric_progress(checkpoint, "xp"))
    live_progress = (_level(live), _numeric_progress(live, "xp"))
    return {**checkpoint, **live} if live_progress >= checkpoint_progress else checkpoint


def _numeric_progress(state: dict[str, Any], key: str) -> int:
    value = state.get(key)
    return int(value) if isinstance(value, (int, float)) else 0


def _run_has_unrecovered_weapon_loss(
    storage: RunStorage,
    run_id: int,
) -> bool:
    """Reconstruct the final weapon state for legacy or interrupted runs."""
    weapon_present: bool | None = None
    awaiting_equipment_response = False
    for event in storage.list_events(run_id):
        payload = json.loads(event["payload_json"])
        if event["kind"] == "command":
            awaiting_equipment_response = str(
                payload.get("command", "")
            ).casefold() in {"equipment", "eq all"}
            continue
        if event["kind"] != "response":
            continue
        response = _ANSI_ESCAPE.sub("", str(payload.get("text", ""))).casefold()
        if awaiting_equipment_response:
            cleaned = _ANSI_ESCAPE.sub("", response)
            if _is_equipment_audit_response(cleaned):
                weapon_present = bool(
                    re.search(r"(?:\[weapon\]|<[^>]*wield[^>]*>)", cleaned)
                )
                awaiting_equipment_response = False
        if (
            "disarms you" in response
            or "your weapon slips from your hand" in response
        ):
            weapon_present = False
        if "you wield " in response:
            weapon_present = True
    return weapon_present is False


def _latest_character_run(
    storage: RunStorage,
    character_name: str,
) -> Any | None:
    """Return the latest conventionally named runner for one character."""
    suffixes = (
        f":{character_name}".casefold(),
        f"-{character_name}".casefold(),
    )
    return next(
        (
            run
            for run in storage.list_runs(limit=1000)
            if str(run["scenario_name"]).casefold().endswith(suffixes)
        ),
        None,
    )


def _latest_new_character_run(
    storage: RunStorage,
    character_name: str,
    prior_run_ids: Collection[int],
) -> Any | None:
    """Return the newest named run created during the current segment."""
    prior = {int(run_id) for run_id in prior_run_ids}
    suffixes = (
        f":{character_name}".casefold(),
        f"-{character_name}".casefold(),
    )
    return next(
        (
            run
            for run in storage.list_runs(limit=1000)
            if int(run["id"]) not in prior
            and str(run["scenario_name"]).casefold().endswith(suffixes)
        ),
        None,
    )


def _run_latest_state(storage: RunStorage, run_id: int) -> dict[str, Any] | None:
    """Return the last character snapshot recorded by one run."""
    snapshot = storage.get_latest_state_snapshot(run_id)
    if snapshot is None:
        return None
    try:
        state = json.loads(snapshot["state_json"])
    except (TypeError, json.JSONDecodeError):
        return None
    return dict(state) if isinstance(state, dict) else None


def _run_successful_vault_lodges(
    storage: RunStorage,
    run_id: int,
) -> tuple[str, ...]:
    """Return command keywords for vault lodges acknowledged by DD4."""
    lodged: list[str] = []
    pending_keyword: str | None = None
    for event in storage.list_events(run_id):
        payload = json.loads(event["payload_json"])
        if event["kind"] == "command":
            command = str(payload.get("command", "")).strip().casefold()
            pending_keyword = (
                command.removeprefix("lodge ")
                if command.startswith("lodge ")
                else None
            )
            continue
        if event["kind"] != "response" or pending_keyword is None:
            continue
        response = _ANSI_ESCAPE.sub(
            "",
            str(payload.get("text", "")),
        ).casefold()
        if "you lodge " in response and " in your vault." in response:
            lodged.append(pending_keyword)
        pending_keyword = None
    return tuple(dict.fromkeys(lodged))


def _run_equipment_empty_categories(
    storage: RunStorage,
    run_id: int,
) -> set[str] | None:
    """Return the newest empty categories, including later weapon acks."""
    result: set[str] | None = None
    awaiting_audit = False
    for event in storage.list_events(run_id):
        payload = json.loads(event["payload_json"])
        if event["kind"] == "command":
            awaiting_audit = (
                str(payload.get("command", "")).strip().casefold() == "eq all"
            )
            continue
        if event["kind"] != "response":
            continue
        response = str(payload.get("text", ""))
        if awaiting_audit and _equipment_audit_present(response):
            result = _equipment_empty_categories(response)
            awaiting_audit = False
        acknowledgement = _direct_weapon_slot_acknowledgement(response)
        if acknowledgement is None or result is None:
            continue
        if acknowledgement[0]:
            result.discard("wield")
        else:
            result.add("wield")
    return result


def _run_worn_equipment_descriptions(
    storage: RunStorage,
    run_id: int,
) -> list[str] | None:
    """Return worn descriptions, applying later direct weapon acknowledgements."""
    result: list[str] | None = None
    weapon_description: str | None = None
    awaiting_audit = False
    for event in storage.list_events(run_id):
        payload = json.loads(event["payload_json"])
        if event["kind"] == "command":
            awaiting_audit = (
                str(payload.get("command", "")).strip().casefold() == "eq all"
            )
            continue
        if event["kind"] != "response":
            continue
        response = str(payload.get("text", ""))
        if awaiting_audit and _equipment_audit_present(response):
            result = [
                _strip_live_selector(description)
                for description in _equipment_audit_descriptions(response)
            ]
            weapon_seen, weapon_description = _equipment_weapon_slot(response)
            if not weapon_seen:
                weapon_description = None
            elif weapon_description is not None:
                weapon_description = _strip_live_selector(weapon_description)
            awaiting_audit = False
        acknowledgement = _direct_weapon_slot_acknowledgement(response)
        if acknowledgement is None or result is None:
            continue
        if acknowledgement[0]:
            if weapon_description is not None:
                result = [
                    description
                    for description in result
                    if description != weapon_description
                ]
            weapon_description = (
                _strip_live_selector(acknowledgement[1])
                if acknowledgement[1] is not None
                else None
            )
            if weapon_description is not None:
                result.append(weapon_description)
        elif weapon_description is not None:
            result = [
                description
                for description in result
                if description != weapon_description
            ]
            weapon_description = None
    return result


def _direct_weapon_slot_acknowledgement(
    response: str,
) -> tuple[bool, str | None] | None:
    """Extract a direct wield or stop-using acknowledgement from game text."""
    wielded = re.search(
        r"(?im)^\s*you wield\s+(?P<item>.+?)(?:[.!]\s*$|\s*$)",
        response,
    )
    if wielded is not None:
        return True, wielded.group("item").strip()
    if re.search(r"(?im)^\s*you stop using\s+", response):
        return False, None
    return None


_LIVE_SELECTOR_PREFIX = re.compile(r"^\s*\[#\d+\]\s*")


def _strip_live_selector(description: str) -> str:
    """Remove a connection-scoped TARGETMODE selector before persistence."""
    return _LIVE_SELECTOR_PREFIX.sub("", description).strip()


def _run_primary_weapon_slot(
    storage: RunStorage,
    run_id: int,
) -> tuple[bool, str | None] | None:
    """Return the newest observed primary weapon state, if one was recorded.

    Equipment output can be split across Telnet response chunks.  Replay both
    explicit ``eq all`` slots and direct ``You wield ...`` acknowledgements so
    a later successful rearm is not hidden by an earlier empty-slot audit.
    """
    awaiting_audit = False
    result: tuple[bool, str | None] | None = None
    for event in storage.list_events(run_id):
        payload = json.loads(event["payload_json"])
        if event["kind"] == "command":
            awaiting_audit = (
                str(payload.get("command", "")).strip().casefold() == "eq all"
            )
            continue
        if event["kind"] != "response":
            continue
        response = str(payload.get("text", ""))
        if awaiting_audit and _equipment_audit_present(response):
            weapon_seen, weapon_description = _equipment_weapon_slot(response)
            result = (
                weapon_seen,
                _strip_live_selector(weapon_description)
                if weapon_description is not None
                else None,
            )
            awaiting_audit = False
        acknowledgement = _direct_weapon_slot_acknowledgement(response)
        if acknowledgement is not None:
            result = (
                acknowledgement[0],
                _strip_live_selector(acknowledgement[1])
                if acknowledgement[1] is not None
                else None,
            )
    return result


def _research_absence_retry_group(policy_id: str) -> frozenset[str]:
    """Return the probe/hunt identities that share one reset target."""
    if policy_id in _MORIA_SANCTUARY_RESEARCH_POLICY_IDS:
        return _MORIA_SANCTUARY_RESEARCH_POLICY_IDS
    if policy_id in {
        _NOBLEMAN_LEVEL_SEVENTEEN_HUNT_POLICY_ID,
        _NOBLEMAN_LEVEL_SEVENTEEN_PROBE_POLICY_ID,
    }:
        return frozenset(
            {
                policy_id,
                _NOBLEMAN_LEVEL_SEVENTEEN_HUNT_POLICY_ID,
                _NOBLEMAN_LEVEL_SEVENTEEN_PROBE_POLICY_ID,
            }
        )
    if policy_id in {_SOLACE_MAGNUS_POLICY_ID, _SOLACE_MAGNUS_HUNT_POLICY_ID}:
        return frozenset({_SOLACE_MAGNUS_POLICY_ID, _SOLACE_MAGNUS_HUNT_POLICY_ID})
    return frozenset({policy_id})


def _research_retryable_failure_group(policy_id: str) -> frozenset[str]:
    """Return paired identities only for previously productive hunt retries."""
    for group in (
        frozenset(
            {
                "mirror-realm-watchman-probe-19-20",
                "mirror-realm-watchman-hunt-19-20",
            }
        ),
        frozenset(
            {
                "crystalmir-white-stag-probe-16-20",
                "crystalmir-white-stag-hunt-16-20",
            }
        ),
        frozenset(
            {
                "shadow-keep-undead-soldier-probe-16-20",
                "shadow-keep-undead-soldier-hunt-16-20",
            }
        ),
        frozenset(
            {
                "galaxy-white-dwarf-probe-17-20",
                "galaxy-white-dwarf-hunt-17-20",
            }
        ),
        frozenset(
            {
                "galaxy-white-dwarf-secondary-probe-17-20",
                "galaxy-white-dwarf-secondary-hunt-17-20",
            }
        ),
        frozenset(
            {
                "galaxy-red-supergiant-probe-17-20",
                "galaxy-red-supergiant-hunt-17-20",
            }
        ),
        frozenset(
            {
                "galaxy-horsehead-nebula-probe-18-20",
                "galaxy-horsehead-nebula-hunt-18-20",
            }
        ),
        frozenset(
            {
                _HIGHTOWER_JAILOR_POLICY_ID,
                _HIGHTOWER_JAILOR_HUNT_POLICY_ID,
            }
        ),
        frozenset(
            {
                _SHIRE_DWARVEN_PRINCE_POLICY_ID,
                _SHIRE_DWARVEN_PRINCE_HUNT_POLICY_ID,
            }
        ),
        frozenset(
            {
                "shire-dwarven-prince-thief-probe-19-20",
                "shire-dwarven-prince-thief-hunt-19-20",
            }
        ),
        frozenset({_SHIRE_THAIN_POLICY_ID, _SHIRE_THAIN_HUNT_POLICY_ID}),
        frozenset(
            {
                _SHIRE_ELVEN_WIZARD_POLICY_ID,
                _SHIRE_ELVEN_WIZARD_HUNT_POLICY_ID,
            }
        ),
        frozenset(
            {
                _PYRAMID_ALI_BABA_POLICY_ID,
                _PYRAMID_ALI_BABA_HUNT_POLICY_ID,
            }
        ),
        frozenset(
            {
                _SOLACE_LORD_DOOM_POLICY_ID,
                _SOLACE_LORD_DOOM_HUNT_POLICY_ID,
            }
        ),
        frozenset(
            {
                _ARGENT_BANDIT_LEADER_POLICY_ID,
                "argent-bandit-leader-hunt-17-20",
            }
        ),
        frozenset(
            {
                _ARGENT_BANDIT_LEADER_LEVEL_NINETEEN_POLICY_ID,
                _ARGENT_BANDIT_LEADER_LEVEL_NINETEEN_HUNT_POLICY_ID,
            }
        ),
        frozenset(
            {
                _HIGHLAND_KEEPER_POLICY_ID,
                _HIGHLAND_KEEPER_HUNT_POLICY_ID,
            }
        ),
    ):
        if policy_id in group:
            return group
    return frozenset({policy_id})


def _next_absent_research_retry_policy(
    state: dict[str, Any],
    *,
    current_group: frozenset[str],
    current_policy_id: str,
    only_expired: bool = True,
) -> str:
    """Rotate to another absent target after retrying the current one.

    A reset wait is a chance to inspect a different registered target as well
    as the one that just expired.  Keeping the cooldown map intact prevents a
    depleted route from being reopened on every campaign invocation.
    """
    results = _campaign_research_results(state)
    boot_id = state.get("world_boot_id")
    cooldowns = state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
    candidates: list[tuple[int, str]] = []
    for policy_id, remaining_value in cooldowns.items():
        candidate_id = str(policy_id)
        if candidate_id in current_group:
            continue
        try:
            remaining = int(remaining_value)
        except (TypeError, ValueError):
            continue
        result = results.get(candidate_id)
        cooldown_ready = remaining <= 0 if only_expired else remaining > 0
        if (
            cooldown_ready
            and isinstance(result, dict)
            and result.get("absent") is True
            and result.get("boot_id") == boot_id
        ):
            candidates.append((remaining, candidate_id))
    if not candidates:
        return current_policy_id
    return min(candidates)[1]


def _next_pending_absent_research_retry_policy(
    state: dict[str, Any],
    *,
    maximum_remaining: int = 1,
) -> str | None:
    """Find a current-reboot absence retry that is one step from reopening."""
    results = _campaign_research_results(state)
    boot_id = state.get("world_boot_id")
    cooldowns = state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
    candidates: list[tuple[int, str]] = []
    for raw_policy_id, raw_remaining in cooldowns.items():
        policy_id = str(raw_policy_id)
        if not _is_research_absence_retry_policy(policy_id):
            continue
        result = results.get(policy_id)
        if not (
            isinstance(result, dict)
            and result.get("boot_id") == boot_id
            and (
                result.get("absent") is True
                or result.get("route_hazard")
                == _DYNAMIC_FIELD_ROUTE_HAZARD_ABORT_REASON
                or (
                    policy_id.startswith(_SOURCE_RANKED_POLICY_PREFIX)
                    and result.get("route_hazard")
                )
            )
        ):
            continue
        try:
            remaining = int(raw_remaining)
        except (TypeError, ValueError):
            continue
        if 0 < remaining <= maximum_remaining:
            candidates.append((remaining, policy_id))
    return min(candidates)[1] if candidates else None


def _retry_current_absent_research_policy(
    state: dict[str, Any],
    *,
    productive_only: bool = False,
) -> dict[str, Any]:
    """Re-open the next target whose bounded reset wait has just expired."""
    policy_id = str(state.get("campaign_last_policy") or "")
    if not _is_research_absence_retry_policy(policy_id):
        return state
    result = _campaign_research_results(state).get(policy_id)
    if not (
        isinstance(result, dict)
        and (
            result.get("absent")
            or (
                policy_id.startswith(_SOURCE_RANKED_POLICY_PREFIX)
                and result.get("route_hazard")
            )
        )
        and result.get("boot_id") == state.get("world_boot_id")
    ):
        return state
    retried = dict(state)
    retried.pop(_POLICY_HANDOFF_KEY, None)
    current_group = _research_absence_retry_group(policy_id)
    results = dict(_campaign_research_results(state))
    productive_policy_id = state.get(_LAST_PRODUCTIVE_POLICY_KEY)
    productive_result = (
        results.get(productive_policy_id)
        if isinstance(productive_policy_id, str)
        else None
    )
    productive_handoff = bool(
        isinstance(productive_policy_id, str)
        and productive_policy_id not in current_group
        and isinstance(productive_result, dict)
        and productive_result.get("boot_id") == state.get("world_boot_id")
        and productive_result.get("observed") is True
        and productive_result.get("viable") is True
        and productive_result.get("completed_kill") is True
    )
    historical_handoff = (
        None
        if productive_handoff
        else _historical_productive_handoff_policy_id(
            state,
            current_group=current_group,
        )
    )
    handoff_policy_id = (
        productive_policy_id
        if productive_handoff
        else historical_handoff
    )
    if productive_only and handoff_policy_id is None:
        return state
    if handoff_policy_id is not None:
        selected_policy_id = handoff_policy_id
        retry_policy_ids = ()
        retried[_POLICY_HANDOFF_KEY] = selected_policy_id
    else:
        cooldowns = state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
        current_cooldown = 0
        for candidate_id in current_group:
            try:
                current_cooldown = max(
                    current_cooldown,
                    int(cooldowns.get(candidate_id) or 0),
                )
            except (TypeError, ValueError):
                continue
        selected_policy_id = _next_absent_research_retry_policy(
            state,
            current_group=current_group,
            current_policy_id=policy_id,
        )
        if (
            selected_policy_id == policy_id
            and current_cooldown > 0
        ):
            return state
        retry_policy_ids = _research_absence_retry_group(selected_policy_id)
    for candidate_id in retry_policy_ids:
        results.pop(candidate_id, None)
    if results:
        retried["campaign_research_results"] = results
    else:
        retried.pop("campaign_research_results", None)
    cooldowns = dict(state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {})
    for candidate_id in retry_policy_ids:
        cooldowns.pop(candidate_id, None)
    if cooldowns:
        retried[_RESEARCH_ABSENCE_COOLDOWN_KEY] = cooldowns
    else:
        retried.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
    if retry_policy_ids:
        cleared_research_policies = {
            str(candidate_id)
            for candidate_id in state.get(_CLEARED_RESEARCH_POLICIES_KEY, ())
        }
        cleared_research_policies.update(retry_policy_ids)
        retried[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(
            cleared_research_policies
        )
    retried["campaign_fastwalk_target_absent"] = False
    retried.pop("campaign_fastwalk_abort_reason", None)
    retried["campaign_last_policy"] = selected_policy_id
    return retried


def _retry_any_pending_absent_research_policy(state: dict[str, Any]) -> dict[str, Any]:
    """Reopen a nearly-expired absence route after the frontier is exhausted."""
    policy_id = _next_pending_absent_research_retry_policy(state)
    if policy_id is None:
        return state
    retry_policy_ids = _research_absence_retry_group(policy_id)
    retried = dict(state)
    results = dict(_campaign_research_results(state))
    for candidate_id in retry_policy_ids:
        results.pop(candidate_id, None)
    if results:
        retried["campaign_research_results"] = results
    else:
        retried.pop("campaign_research_results", None)
    cooldowns = dict(state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {})
    for candidate_id in retry_policy_ids:
        cooldowns.pop(candidate_id, None)
    if cooldowns:
        retried[_RESEARCH_ABSENCE_COOLDOWN_KEY] = cooldowns
    else:
        retried.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
    cleared_research_policies = {
        str(candidate_id)
        for candidate_id in state.get(_CLEARED_RESEARCH_POLICIES_KEY, ())
    }
    cleared_research_policies.update(retry_policy_ids)
    retried[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(
        cleared_research_policies
    )
    retried["campaign_fastwalk_target_absent"] = False
    retried.pop("campaign_fastwalk_abort_reason", None)
    retried["campaign_last_policy"] = policy_id
    return retried


def _retry_required_sanctuary_research_policy(
    state: dict[str, Any],
) -> dict[str, Any]:
    """Reopen an absent sanctuary carrier after the bounded reset wait."""
    policy_id = _MORIA_SANCTUARY_THIEF_LEVEL_SEVENTEEN_POLICY_ID
    moria_policy_ids = _MORIA_SANCTUARY_RESEARCH_POLICY_IDS
    results = _campaign_research_results(state)
    cooldowns = state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
    moria_cooldown_active = isinstance(cooldowns, dict) and any(
        int(cooldowns.get(candidate_id) or 0) > 0
        for candidate_id in moria_policy_ids
    )
    moria_target_absent = any(
        isinstance(results.get(candidate_id), dict)
        and results[candidate_id].get("absent") is True
        and results[candidate_id].get("boot_id") == state.get("world_boot_id")
        for candidate_id in moria_policy_ids
    )
    if not (
        moria_cooldown_active
        and moria_target_absent
        and _campaign_sanctuary_recovery_required(state)
    ):
        return state
    retried = dict(state)
    results = dict(results)
    for candidate_id in moria_policy_ids:
        results.pop(candidate_id, None)
    if results:
        retried["campaign_research_results"] = results
    else:
        retried.pop("campaign_research_results", None)
    remaining_cooldowns = dict(cooldowns)
    for candidate_id in moria_policy_ids:
        remaining_cooldowns.pop(candidate_id, None)
    if remaining_cooldowns:
        retried[_RESEARCH_ABSENCE_COOLDOWN_KEY] = remaining_cooldowns
    else:
        retried.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
    cleared = {
        str(candidate_id)
        for candidate_id in state.get(_CLEARED_RESEARCH_POLICIES_KEY, ())
    }
    cleared.update(moria_policy_ids)
    retried[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(cleared)
    retried["campaign_fastwalk_target_absent"] = False
    retried.pop("campaign_fastwalk_abort_reason", None)
    retried["campaign_last_policy"] = policy_id
    return retried


def _active_crowded_research_policy_id(
    state: dict[str, Any],
) -> str | None:
    """Return the first current-reboot crowd route with an active cooldown."""
    results = _campaign_research_results(state)
    cooldowns = state.get(_RESEARCH_CROWD_COOLDOWN_KEY) or {}
    candidates: list[tuple[int, str]] = []
    for policy_id, result in results.items():
        if (
            not isinstance(result, dict)
            or result.get("crowded") is not True
            or result.get("boot_id") != state.get("world_boot_id")
        ):
            continue
        try:
            remaining = int(cooldowns.get(policy_id) or 0)
        except (TypeError, ValueError):
            continue
        if remaining > 0:
            candidates.append((remaining, policy_id))
    if not candidates:
        return None
    return min(candidates)[1]


def _retry_any_crowded_research_policy(state: dict[str, Any]) -> dict[str, Any]:
    """Reopen one crowded route after its explicit reset wait."""
    policy_id = _active_crowded_research_policy_id(state)
    if policy_id is None:
        return state
    retried = dict(state)
    results = dict(_campaign_research_results(state))
    results.pop(policy_id, None)
    if results:
        retried["campaign_research_results"] = results
    else:
        retried.pop("campaign_research_results", None)
    cooldowns = dict(state.get(_RESEARCH_CROWD_COOLDOWN_KEY) or {})
    cooldowns.pop(policy_id, None)
    if cooldowns:
        retried[_RESEARCH_CROWD_COOLDOWN_KEY] = cooldowns
    else:
        retried.pop(_RESEARCH_CROWD_COOLDOWN_KEY, None)
    cleared_research_policies = {
        str(candidate_id)
        for candidate_id in state.get(_CLEARED_RESEARCH_POLICIES_KEY, ())
    }
    cleared_research_policies.add(policy_id)
    retried[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(
        cleared_research_policies
    )
    retried["campaign_fastwalk_target_absent"] = False
    retried.pop("campaign_fastwalk_abort_reason", None)
    retried["campaign_last_policy"] = policy_id
    return retried


def _retry_current_crowded_research_policy(state: dict[str, Any]) -> dict[str, Any]:
    """Rotate a crowded research checkpoint after its bounded wait."""
    policy_id = str(state.get("campaign_last_policy") or "")
    abort_reason = str(state.get("campaign_fastwalk_abort_reason") or "")
    if abort_reason == _DYNAMIC_FIELD_ROUTE_HAZARD_ABORT_REASON:
        result = _campaign_research_results(state).get(policy_id)
        cooldowns = state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {}
        if not (
            isinstance(result, dict)
            and result.get("route_hazard") == abort_reason
            and result.get("boot_id") == state.get("world_boot_id")
            and isinstance(cooldowns, dict)
            and int(cooldowns.get(policy_id) or 0) > 0
        ):
            return state
        retried = dict(state)
        results = dict(_campaign_research_results(state))
        results.pop(policy_id, None)
        if results:
            retried["campaign_research_results"] = results
        else:
            retried.pop("campaign_research_results", None)
        remaining_cooldowns = dict(cooldowns)
        remaining_cooldowns.pop(policy_id, None)
        if remaining_cooldowns:
            retried[_RESEARCH_ABSENCE_COOLDOWN_KEY] = remaining_cooldowns
        else:
            retried.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
        cleared_research_policies = {
            str(candidate_id)
            for candidate_id in state.get(_CLEARED_RESEARCH_POLICIES_KEY, ())
        }
        cleared_research_policies.add(policy_id)
        retried[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(
            cleared_research_policies
        )
        retried["campaign_fastwalk_target_absent"] = False
        retried.pop("campaign_fastwalk_abort_reason", None)
        retried["campaign_last_policy"] = policy_id
        return retried
    if not policy_id or not any(
        abort_reason.startswith(prefix) for prefix in _FIELD_CROWD_ABORT_PREFIXES
    ):
        return _retry_any_crowded_research_policy(state)
    retry_policy_id = _next_absent_research_retry_policy(
        state,
        current_group=_research_absence_retry_group(policy_id),
        current_policy_id=policy_id,
        only_expired=False,
    )
    if retry_policy_id == policy_id:
        return _retry_any_crowded_research_policy(state)
    retried = dict(state)
    # Crowd rotation selects one executable route.  Paired probe/hunt
    # identities share absence-reset state only in the dedicated reset path;
    # clearing the whole group here can erase an unrelated sanctuary probe.
    retry_policy_ids = (retry_policy_id,)
    results = dict(_campaign_research_results(state))
    for candidate_id in retry_policy_ids:
        results.pop(candidate_id, None)
    if results:
        retried["campaign_research_results"] = results
    else:
        retried.pop("campaign_research_results", None)
    cooldowns = dict(state.get(_RESEARCH_ABSENCE_COOLDOWN_KEY) or {})
    for candidate_id in retry_policy_ids:
        cooldowns.pop(candidate_id, None)
    if cooldowns:
        retried[_RESEARCH_ABSENCE_COOLDOWN_KEY] = cooldowns
    else:
        retried.pop(_RESEARCH_ABSENCE_COOLDOWN_KEY, None)
    cleared_research_policies = {
        str(candidate_id)
        for candidate_id in state.get(_CLEARED_RESEARCH_POLICIES_KEY, ())
    }
    cleared_research_policies.update(retry_policy_ids)
    retried[_CLEARED_RESEARCH_POLICIES_KEY] = sorted(
        cleared_research_policies
    )
    retried["campaign_fastwalk_target_absent"] = False
    retried.pop("campaign_fastwalk_abort_reason", None)
    retried["campaign_last_policy"] = retry_policy_id
    return retried


def _is_equipment_audit_response(response: str) -> bool:
    """Reject stale command pulses while reconstructing an equipment audit."""
    return "you are not using any equipment" in response or bool(
        re.search(r"(?:\[weapon\]|\[held\]|<[^>]*worn[^>]*>)", response)
    )


def _state_has_item(value: Any, item_name: str) -> bool:
    target = item_name.casefold()
    if isinstance(value, str):
        try:
            decoded = json.loads(_ANSI_ESCAPE.sub("", value))
        except json.JSONDecodeError:
            return target in value.casefold()
        return _state_has_item(decoded, item_name)
    if isinstance(value, dict):
        for key in ("short_desc", "name", "item"):
            description = value.get(key)
            if isinstance(description, str) and target in description.casefold():
                return True
        return any(_state_has_item(item, item_name) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_state_has_item(item, item_name) for item in value)
    return False


def _state_item_count(value: Any, item_name: str) -> int:
    target = item_name.casefold()
    if isinstance(value, str):
        try:
            decoded = json.loads(_ANSI_ESCAPE.sub("", value))
        except json.JSONDecodeError:
            return int(target in value.casefold())
        return _state_item_count(decoded, item_name)
    if isinstance(value, dict):
        description = next(
            (
                value[key]
                for key in ("short_desc", "name", "item")
                if isinstance(value.get(key), str)
            ),
            None,
        )
        if description is not None and target in description.casefold():
            quantity = value.get("quan", 1)
            try:
                return max(1, int(quantity))
            except (TypeError, ValueError):
                return 1
        return sum(_state_item_count(item, item_name) for item in value.values())
    if isinstance(value, (list, tuple)):
        return sum(_state_item_count(item, item_name) for item in value)
    return 0


def _state_has_active_affect(value: Any, affect_name: str) -> bool:
    target = affect_name.casefold()
    if isinstance(value, str):
        try:
            decoded = json.loads(_ANSI_ESCAPE.sub("", value))
        except json.JSONDecodeError:
            return target in value.casefold()
        return _state_has_active_affect(decoded, affect_name)
    if isinstance(value, dict):
        name = value.get("name")
        if isinstance(name, str) and target == name.casefold():
            return True
        return any(
            _state_has_active_affect(item, affect_name)
            for item in value.values()
        )
    if isinstance(value, (list, tuple)):
        return any(_state_has_active_affect(item, affect_name) for item in value)
    return False


def _state_copper_value(state: dict[str, Any]) -> int:
    currencies = state.get("currencies")
    source = currencies if isinstance(currencies, dict) else state

    def amount(name: str) -> int:
        value = source.get(name, 0)
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return 0

    return (
        amount("platinum") * 1_000
        + amount("gold") * 100
        + amount("silver") * 10
        + amount("copper")
    )


def _state_needs_coin_deposit(state: dict[str, Any]) -> bool:
    stats = state.get("stats")
    if not isinstance(stats, dict):
        return False
    carry_weight = stats.get("carry_wt")
    maximum_weight = stats.get("maxcarry_wt")
    if not isinstance(carry_weight, (int, float)):
        return False
    if not isinstance(maximum_weight, (int, float)) or maximum_weight <= 0:
        return False
    if maximum_weight - carry_weight >= 10:
        return False

    currencies = state.get("currencies")
    source = currencies if isinstance(currencies, dict) else state
    coin_count = 0
    for denomination in ("platinum", "gold", "silver", "copper"):
        try:
            coin_count += max(0, int(source.get(denomination, 0)))
        except (TypeError, ValueError):
            continue
    return coin_count >= 10


def _has_campaign_sellable_loot(
    state: dict[str, Any],
    *,
    gear_catalog: GearCatalog | None = None,
) -> bool:
    stats = state.get("stats")
    if gear_catalog is not None and isinstance(stats, dict):
        carry_items = stats.get("carry_num")
        maximum_items = stats.get("maxcarry_num")
        if (
            isinstance(carry_items, (int, float))
            and isinstance(maximum_items, (int, float))
            and carry_items >= maximum_items
            and any(
                item is not None and is_disposable_food(item)
                for description in _inventory_descriptions(state.get("inventory"))
                for item in (gear_catalog.match(description),)
            )
        ):
            return True
    keyword = _sellable_inventory_keyword(
        state.get("inventory"),
        gear_catalog,
        worn_descriptions=state.get("campaign_worn_equipment"),
    )
    if keyword is None:
        return False
    if keyword == "collar":
        carried_collars = _state_item_count(
            state.get("inventory"),
            "war dog collar",
        )
        worn_collars = sum(
            "war dog collar" in normalize_item_name(description)
            for description in state.get("campaign_worn_equipment") or ()
        )
        retained_carried_collars = max(0, 2 - worn_collars)
        if carried_collars <= retained_carried_collars:
            return False
        stats = state.get("stats")
        if not isinstance(stats, dict):
            return False
        carry_weight = stats.get("carry_wt")
        maximum_weight = stats.get("maxcarry_wt")
        if not isinstance(carry_weight, (int, float)):
            return False
        if not isinstance(maximum_weight, (int, float)) or maximum_weight <= 0:
            return False
        if carry_weight / maximum_weight < 0.85:
            return False
    if isinstance(stats, dict):
        carry_weight = stats.get("carry_wt")
        maximum_weight = stats.get("maxcarry_wt")
        if (
            isinstance(carry_weight, (int, float))
            and isinstance(maximum_weight, (int, float))
            and maximum_weight > 0
            and maximum_weight - carry_weight <= 10
        ):
            empty_categories = set(
                state.get("campaign_empty_equipment_categories") or ()
            )
            for description in _inventory_descriptions(state.get("inventory")):
                if _sellable_inventory_keyword(
                    [[{"short_desc": description}]],
                    gear_catalog,
                    worn_descriptions=state.get("campaign_worn_equipment"),
                ) is None:
                    continue
                item = gear_catalog.match(description) if gear_catalog else None
                if (
                    item is not None
                    and item_category(item) in empty_categories
                ):
                    continue
                return True
            return False
    # A failed purchase is not new loot. Once a liquidation checkpoint has
    # recorded the retained inventory, repeating the same no-op sale only
    # stalls the pending purchase retry; a changed signature will still
    # schedule one fresh liquidation pass.
    return not _matches_liquidation_baseline(state, gear_catalog=gear_catalog)


def _campaign_vault_stow_items(
    state: dict[str, Any],
    *,
    gear_catalog: GearCatalog | None,
    required_free_weight: int = 10,
) -> tuple[str, ...]:
    if gear_catalog is None:
        return ()
    stats = state.get("stats")
    if not isinstance(stats, dict):
        return ()
    carry_weight = stats.get("carry_wt")
    maximum_weight = stats.get("maxcarry_wt")
    if not isinstance(carry_weight, (int, float)):
        return ()
    if not isinstance(maximum_weight, (int, float)):
        return ()
    if maximum_weight - carry_weight >= required_free_weight:
        return ()

    keywords: list[str] = []
    selected_weight = 0
    capacity_candidates: list[tuple[int, str]] = []
    worn_counts = Counter(
        normalize_item_name(description)
        for description in state.get("campaign_worn_equipment") or ()
    )
    for description in _inventory_descriptions(state.get("inventory")):
        item = gear_catalog.match(description)
        if item is None:
            continue
        normalized_description = normalize_item_name(description)
        if worn_counts[normalized_description] > 0:
            worn_counts[normalized_description] -= 1
            continue
        candidates = gear_catalog.candidates(description)
        ambiguous_weapon = (
            item.item_type == 5
            and len(candidates) > 1
            and all(candidate.item_type == 5 for candidate in candidates)
        )
        plain_armour = item.item_type == 9 and not protects_from_sale(item)
        protected_spare = (
            protects_from_sale(item)
            and not is_capacity_infrastructure(item)
            and item_category(item) not in {"light", "wield"}
        )
        keyword = item_keyword(item)
        normalized_name = normalize_item_name(item.short_description)
        if is_capacity_infrastructure(item):
            if "large sack" in normalized_name:
                keyword = "sack"
            elif "backpack" in normalized_name:
                keyword = "backpack"
            elif "girdle of many pouches" in normalized_name:
                keyword = "girdle"
        if not keyword:
            continue
        if is_capacity_infrastructure(item):
            capacity_candidates.append((item.weight, keyword))
            continue
        if ambiguous_weapon or plain_armour or protected_spare:
            selected_weight += item.weight
        else:
            continue
        if keyword not in keywords:
            keywords.append(keyword)

    free_weight = maximum_weight - carry_weight
    for weight, keyword in sorted(capacity_candidates, reverse=True):
        if free_weight + selected_weight >= required_free_weight:
            break
        if keyword not in keywords:
            keywords.append(keyword)
            selected_weight += weight
    if free_weight + selected_weight < required_free_weight:
        return ()
    return tuple(keywords)


def _has_oversized_capacity_stow_item(
    state: dict[str, Any],
    *,
    gear_catalog: GearCatalog | None,
    stow_items: tuple[str, ...],
) -> bool:
    if gear_catalog is None or not stow_items:
        return False
    stats = state.get("stats")
    maximum_weight = stats.get("maxcarry_wt") if isinstance(stats, dict) else None
    if not isinstance(maximum_weight, (int, float)) or maximum_weight <= 0:
        return False
    stow_keywords = {keyword.casefold() for keyword in stow_items}
    for description in _inventory_descriptions(state.get("inventory")):
        item = gear_catalog.match(description)
        if item is None or not is_capacity_infrastructure(item):
            continue
        if not stow_keywords.intersection(item.keywords.casefold().split()):
            continue
        if item.weight >= max(20, maximum_weight * 0.2):
            return True
    return False


def _has_campaign_free_weight(
    state: dict[str, Any],
    required_free_weight: int,
) -> bool:
    stats = state.get("stats")
    if not isinstance(stats, dict):
        return True
    carry_weight = stats.get("carry_wt")
    maximum_weight = stats.get("maxcarry_wt")
    if not isinstance(carry_weight, (int, float)):
        return True
    if not isinstance(maximum_weight, (int, float)):
        return True
    return maximum_weight - carry_weight >= required_free_weight


def _campaign_liquidation_signature(
    state: dict[str, Any],
    *,
    gear_catalog: GearCatalog | None = None,
) -> tuple[str, ...]:
    descriptions = _inventory_descriptions(state.get("inventory"))
    worn_descriptions = state.get("campaign_worn_equipment")
    protected_seen: Counter[str] = Counter()
    candidates: list[str] = []
    for description in descriptions:
        normalized = normalize_item_name(description)
        item = gear_catalog.match(description) if gear_catalog is not None else None
        if (
            item is not None
            and protects_from_sale(item)
            and not any(
                location == 1 and modifier < 0
                for location, modifier in item.affects
            )
            and _sellable_inventory_keyword(
                [[{"short_desc": description}]],
                gear_catalog,
                worn_descriptions=worn_descriptions,
            ) is None
        ):
            protected_seen[normalized] += 1
            retained_capacity = {
                "finger": 2,
                "neck": 2,
                "wrist": 2,
            }.get(item_category(item) or "", 1)
            if protected_seen[normalized] <= retained_capacity:
                continue
        elif (
            _sellable_inventory_keyword(
                [[{"short_desc": description}]],
                gear_catalog,
                worn_descriptions=worn_descriptions,
            )
            is None
        ):
            continue
        candidates.append(normalized)
    return tuple(sorted(candidates))


def _matches_liquidation_baseline(
    state: dict[str, Any],
    *,
    gear_catalog: GearCatalog | None = None,
) -> bool:
    baseline = state.get(_LIQUIDATION_BASELINE_KEY)
    if not isinstance(baseline, (list, tuple)) or not all(
        isinstance(item, str) for item in baseline
    ):
        return False
    return _campaign_liquidation_signature(
        state,
        gear_catalog=gear_catalog,
    ) == tuple(sorted(normalize_item_name(item) for item in baseline))


def _budget_failure(spec: CampaignSpec, totals: Any) -> str | None:
    if int(totals["segment_count"]) >= spec.max_segments:
        return f"Campaign exceeded its {spec.max_segments} segment budget."
    if int(totals["command_count"]) >= spec.max_total_commands:
        return f"Campaign exceeded its {spec.max_total_commands} command budget."
    if float(totals["duration_seconds"]) >= spec.max_total_runtime:
        return f"Campaign exceeded its {spec.max_total_runtime:g} second runtime budget."
    return None


def _stalled_count(
    before: dict[str, Any],
    after: dict[str, Any],
    checkpoint: Any,
) -> int:
    previous = _checkpoint_state(checkpoint)
    previous_stalled = int(previous.get("campaign_stalled_segments", 0))
    if previous.get("campaign_policy_revision") != before.get(
        "campaign_policy_revision"
    ):
        previous_stalled = 0
    if _level(after) > _level(before):
        return 0
    before_xp = before.get("xp")
    after_xp = after.get("xp")
    if isinstance(before_xp, (int, float)) and isinstance(after_xp, (int, float)):
        if after_xp > before_xp:
            return 0
    if not before and _level(after) > 0:
        return 0
    return previous_stalled + 1


def _run_duration(run: Any) -> float:
    if run is None or not run["finished_at"]:
        return 0.0
    try:
        elapsed = datetime.fromisoformat(run["finished_at"]) - datetime.fromisoformat(
            run["started_at"]
        )
    except ValueError:
        return 0.0
    return max(0.0, elapsed.total_seconds())
