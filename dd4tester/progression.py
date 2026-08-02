from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace

from .archetypes import archetype_registry


_ARCHETYPES = archetype_registry()
_MEANINGFUL_FIELD_SEGMENT_XP = 50
_MEANINGFUL_LEVEL_SEVEN_SEGMENT_XP = 200
_FOREST_BEAR_CLAWS_MINIMUM_NONFLIGHT_MOVE = 300
_FIELD_RESOURCE_ABORT_PREFIX = (
    "field expedition withdrew before target evaluation because "
)
_FIELD_CROWD_ABORT_PREFIX = (
    "field combat aborted after unapproved attacker "
)
_NOBLEMAN_APPROACH_INTERRUPT_ABORT = (
    "unexpected combat interrupted fastwalk 'dwarven nobleman' before its objective"
)
_RETIRED_MORIA_SANCTUARY_LEVEL_TWELVE_RESEARCH_POLICY_ID = (
    "moria-sanctuary-probe-12-13"
)
CLASS_PRACTICE_SKILLS = {
    name: profile.practice_skill
    for name, profile in _ARCHETYPES.classes.items()
}


@dataclass(frozen=True)
class ProgressionPolicy:
    policy_id: str
    minimum_level: int
    maximum_level: int | None
    status: str
    execution: str | None
    summary: str
    evidence: tuple[str, ...]
    practice_skill: str | None
    segment_kill_limit: int | None = None
    allow_partial_below_band: bool = False

    @property
    def executable(self) -> bool:
        return self.execution is not None and self.status in {"verified", "research"}

    def blocks_message(self, character_class: str) -> str:
        if self.status == "research":
            return (
                f"Policy {self.policy_id} is research-gated for {character_class}. "
                "Its route is observed, but its combat and XP loop are not yet verified."
            )
        if self.status == "unavailable" and self.summary:
            return self.summary
        return (
            f"No policy is registered for level {self.minimum_level}+ "
            f"{character_class} progression."
        )


@dataclass(frozen=True)
class ProgressionContext:
    level: int
    character_class: str
    subclass: str | None
    progression_track: str
    practice_skill: str
    capabilities: frozenset[str]
    has_large_sack: bool = False
    has_sellable_loot: bool = False
    needs_coin_deposit: bool = False
    needs_capacity_relief: bool = False
    has_food: bool = True
    has_weapon: bool = True
    needs_basic_gear: bool = False
    needs_body_gear_recovery: bool = False
    needs_school_wrist_float: bool = False
    needs_gremlin_waist: bool = False
    needs_daycare_ring: bool = False
    needs_war_dog_collar: bool = False
    needs_foundry_set_circlet: bool = False
    needs_intermediate_piercing_weapon_upgrade: bool = False
    intermediate_piercing_weapon_upgrade_attempted: bool = False
    needs_piercing_weapon_upgrade: bool = False
    piercing_weapon_upgrade_attempted: bool = False
    needs_piercing_weapon: bool = False
    needs_pounding_weapon: bool = False
    movement_available: int = 0
    movement_capacity: int = 0
    has_sanctuary_potion: bool = False
    has_flight: bool = True
    can_attempt_flight_purchase: bool = False
    flight_purchase_failed: bool = False
    boot_kill_counts: Mapping[str, int] | None = None
    policy_xp_deltas: Mapping[str, int] | None = None
    research_results: Mapping[str, Mapping[str, object]] | None = None
    excluded_policy_ids: frozenset[str] = frozenset()
    world_boot_id: str | int | None = None
    stalled_segments: int = 0
    last_policy_id: str | None = None
    last_fastwalk_abort_reason: str | None = None

    @classmethod
    def from_values(
        cls,
        level: int | float | None,
        character_class: str,
        *,
        subclass: str | None = None,
        **state: object,
    ) -> "ProgressionContext":
        class_profile = _ARCHETYPES.class_profile(character_class)
        capabilities = set(class_profile.capabilities)
        canonical_subclass = None
        if subclass is not None:
            subclass_profile = _ARCHETYPES.subclass_profile(subclass)
            if subclass_profile.base_class != class_profile.name:
                raise ValueError(
                    f"subclass {subclass_profile.name!r} requires base class "
                    f"{subclass_profile.base_class!r}"
                )
            canonical_subclass = subclass_profile.name
            capabilities.update(subclass_profile.capabilities)
        return cls(
            level=int(level or 0),
            character_class=class_profile.name,
            subclass=canonical_subclass,
            progression_track=class_profile.progression_track,
            practice_skill=class_profile.practice_skill,
            capabilities=frozenset(capabilities),
            **state,
        )


_STARTER_POLICY = ProgressionPolicy(
    policy_id="starter-0-2",
    minimum_level=0,
    maximum_level=2,
    status="verified",
    execution="starter",
    summary="Character creation and the complete Mud School tutorial through level 2.",
    evidence=(
        "Live starter run reached level 2, saved, and quit (run 60).",
        "Policy is generic over the supported race, gender, and base-class choices.",
        "Live run 1751 created the prepared human male cleric from scratch, practised Healing Magiks, used Cause Light in tutorial combat, reached level 2, and exited safely.",
    ),
    practice_skill=None,
)

_MUD_SCHOOL_ARENA_POLICY = ProgressionPolicy(
    policy_id="mud-school-2-6",
    minimum_level=2,
    maximum_level=6,
    status="verified",
    execution="arena",
    summary=(
        "Mud School orientation, the Loremaster, and the small arena observed for "
        "the level-2 to level-10 band."
    ),
    evidence=(
        "Live run 56: Mud School entrance vnum 3725 links to Loremaster vnum 3726 and arena vnum 3728.",
        "Live run 56: room text says the Loremaster trains recruits until level 10.",
        "Live run 57: arena rooms 3728-3732 contained a giant lizard and wild boar, with safe up exits.",
        "Live run 56: level-2 character had 325 XP to the next level and available practice points.",
        "Live mage runs 65, 69, and 76 reached levels 3, 4, and 5 respectively; run 76 saved after a wolf level-up.",
        "Live run 76: the level-4-to-5 arena segment used Safety recovery, a Midgaard food-and-water restock, and returned to Mud School safely.",
        "Live run 82: the paced arena policy reached level 6, saved, and quit after a giant-lizard level-up.",
    ),
    practice_skill=None,
    segment_kill_limit=10,
)

_MUD_SCHOOL_RESEARCH_POLICY = replace(
    _MUD_SCHOOL_ARENA_POLICY,
    policy_id="mud-school-6-10",
    minimum_level=6,
    maximum_level=10,
    status="verified",
    execution="arena",
    summary=(
        "Mud School arena progression from level 6 through level 10 in "
        "ten-kill batches with safe recovery and save-and-exit checkpoints."
    ),
    segment_kill_limit=10,
    evidence=(
        *_MUD_SCHOOL_ARENA_POLICY.evidence,
        "DD4 source: the Loremaster directs level-10 characters to their Guildmaster; the Magic Users Guildmaster spawns in Midgaard room 3019.",
        "Live run 88: the mage route reached Midgaard room 3019, confirmed the Magic Users Guildmaster, and recorded Ararisa's available mage skills.",
        "Live run 91: a no-combat round trip from the Mage Guild reached Moria entry room 3900 (West trail around Midgaard) and returned safely to room 3019.",
        "Live run 92: the depth-one Moria scout verified room 3901 as another empty north/south West Trail segment, then returned safely to room 3019.",
        "Live run 93: the depth-two scout reached Moria room 3902 (Northwest corner of dusty trail), with east exit 3903 and a safe south return to 3901 and room 3019.",
        "Live run 94: the depth-three scout reached Moria room 3903 (Dusty trail along north wall), with east exit 3904 and a safe west return through room 3902 to room 3019.",
        "Live run 96: Midgaard Magic Shop listed a level-5 light blue potion for 123 at that time; quaffing it applied the fly effect. Shop prices must be checked each run.",
        "Live run 97: the fly effect persisted through reconnect and the depth-four Moria round trip reached room 3904 (the long dusty trail following the north wall), with exits east 3905, north 300, and west 3903.",
        "Live run 99: the clean depth-five Moria scout reached room 3905 (Dusty trail along north wall), with east exit 3906 and a safe west return to room 3019; fly remained active after the trip.",
        "Live run 103: the official recall-origin Moria fastwalk (2s6e8n) reached room 4014 (The tunnel), with exits east 4015, north 4018, south 4011, and west 4013; return recall reached the Mage Guild safely.",
        "Live run 104: one northward no-combat probe from room 4014 reached room 4018 (The cave), which contained an ugly kobold, an orc, and a large orc; return recall reached the Mage Guild safely.",
        "Live run 105: the explicit kobold probe found the target absent when its attack command arrived, potentially because it wandered; it received no combat or XP signal and returned safely without engaging either orc.",
        "Live run 106: the kobold had wandered from room 4018 to the fastwalk endpoint at room 4014 while the cave was empty; with Fly active, ordinary route movement cost 34 move, while return recall halved movement from 88 to 44.",
        "Live run 146: the source-derived Circus route reached midget tent room 4411 without combat or damage, then recalled, recovered, and returned safely to room 3019.",
        "Live run 148: Ararisa killed the level-3 midget for 43 XP, remained above 97% health, looted its purse, recalled immediately, recovered fully, and returned safely to room 3019.",
        "Live runs 150-151: the midget purse contained 51 copper this reboot and the safe General Store in room 3010 bought the empty purse for 8 copper.",
        "Live run 165: a two-kill bounded arena segment confirmed wild boar (+38 XP) and giant lizard (+20 XP), then saved safely.",
        "Live run 167: the corrected two-kill segment confirmed two wild boars (+109 XP total) and exited to Mud School Safety at full health.",
        "Live run 201: another two-kill checkpoint gained 110 XP in 43.6 seconds and exited at full health with 218/268 mana; route and audit overhead, rather than combat pressure, justified increasing the bounded batch to ten kills.",
        "The published Midgaard map verifies the Common Square-to-Mage-Guild route as 3025 north, 3014 west, 3013 west, 3012 south, 3017 south, and 3018 east to room 3019.",
        "DD4 source map metadata lists Moria for levels 5-15 and Old Thalos for levels 10-25.",
        "DD4 source help: reaching level 100 also requires at least 1,000 total quest points.",
    ),
)

_FOUNDRY_LEVEL_SIX_POLICY = ProgressionPolicy(
    policy_id="foundry-circuit-6-7",
    minimum_level=6,
    maximum_level=7,
    status="retired",
    execution="foundry-hunt",
    summary=(
        "Retired: source and live evidence show that the Foundry's apparent "
        "level-six targets are aggressive and can force an XP-losing flee."
    ),
    evidence=(
        "DD4 source: the existing Foundry fastwalk ends in room 109; rooms 108, 107, 117, 118, 119, and 120 lead to Uburz without entering the captain's quarters.",
        "DD4 source: Uburz loads near level 4; live consider remains authoritative because mobile levels are fuzzed and can wander.",
        "Live run 572: level-6 Dorrik killed Uburz for 106 XP without losing health and recovered three sellable equipment drops.",
        "Live runs 576-577: depleted circuits for thief and mage returned safely at full health, establishing the need for an arena fallback after an empty pass.",
        "The route avoids the poison-bearing pit beast in room 122 and permits a safe no-kill recall when a target is absent or unsuitable.",
        "Live run 841: an aggressive Foundry target forced an XP-losing flee before it could be considered, so this route is not autonomous-safe.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)

_FOUNDRY_LEVEL_SEVEN_POLICY = ProgressionPolicy(
    policy_id="foundry-circuit-7-8",
    minimum_level=7,
    maximum_level=8,
    status="retired",
    execution="foundry-hunt",
    summary=(
        "Retired: the apparent level-seven Foundry sweep contains aggressive "
        "targets that can force an XP-losing flee before consideration."
    ),
    evidence=(
        *_FOUNDRY_LEVEL_SIX_POLICY.evidence,
        "Live run 629: the level-7 arena population had no viable opponents and returned safely with zero XP.",
        "Live run 630: a reboot-fuzzed level-8 mountain goblin auto-attacked the level-7 thief before consideration, so the caster field route is not a generic melee fallback.",
        "Earlier empty passes suggested a lower-risk level-seven sweep, but target presence must be tested separately from route traversal.",
        "DD4 source: from Foundry room 107, Golgog, Shargook, Lobuk, and Uburz form a connected sweep that avoids Oshu's aggressive pit room 110, Ushog's aggressive quarters 112, and the poison-bearing pit beast room 122.",
        "Live runs 828 and 830: entering Oshu's pit room triggered an unapproved attack and an XP-losing flee, so Oshu is excluded from the autonomous route.",
        "Live run 835: entering Ushog's quarters triggered an auto-attack and an XP-losing flee before consider, so Ushog is excluded from the autonomous route.",
        "Live runs 653, 654, and 657 proved empty or target-absent passes for mage, warrior, and thief respectively; they did not establish combat-safe target engagement.",
        "Live runs 652 and 658 showed the level-7 Miden'nir route can impose flee penalties or consume an empty segment, so it is no longer the default caster route.",
        "Live run 841: Lobuk's aggressive flag forced an XP-losing flee before consider; source confirms the other sweep targets also carry ACT_AGGRESSIVE.",
    ),
    practice_skill=None,
    segment_kill_limit=5,
)

_MORIA_LEVEL_SEVEN_ORC_POLICY = ProgressionPolicy(
    policy_id="moria-orc-circuit-7-8",
    minimum_level=7,
    maximum_level=8,
    status="verified",
    execution="moria-orc-hunt",
    summary=(
        "A bounded, live-considered first-level Moria circuit: two poison-free "
        "orcs, then an optional snake immediately before healer recovery."
    ),
    evidence=(
        "DD4 source: the official Moria fastwalk reaches room 4014; poison-free source-level-7 and source-level-5 orcs reset in rooms 4022 and 4015.",
        "DD4 source: the large orc carries a yellow and green ring, while the level-7 garter snake has spec_poison.",
        "Area-file mobile levels are approximate; every field target is checked with live consider output before combat.",
        "Live run 264: a deeper multi-target Moria circuit encountered a wandering veteran warrior and is deliberately excluded from this isolated policy.",
        "DD4 source revision 0482387: the circuit remains on Moria level 1 and does not enter the level-2 graph containing aggressive veteran warriors.",
        "Live run 693: level-7 thief Kestrel considered the snake a perfect match, killed it for 334 XP, and returned to healer room 3054; repeated poison made his heavy weapon slip, so the campaign must checkpoint and rearm before another hunt.",
        "Live run 697: a repeated snake kill yielded only 11 XP while poisoning Kestrel, disqualifying it as a primary repeatable progression target.",
        "The snake is sequenced last and requires full health so recall and healer cure-poison recovery follow immediately.",
        "Live run 701 considered a reboot-fuzzed level-6 orc a perfect match; an exact duplicate GMCP enemy row caused a conservative flee and motivated protocol-level deduplication before revalidation.",
        "Live run 702 completed the flight-enabled last-stop snake kill for 392 XP, then recovered from 99/123 to full health at healer room 3054 with no remaining poison affect or weapon loss.",
        "Live runs 920-924 proved the large orc wanders between reset room 4022 and its north exit 4023, so both rooms are isolated and checked before the rest of the circuit.",
    ),
    practice_skill=None,
    segment_kill_limit=3,
)

_DAYCARE_LEVEL_SEVEN_POLICY = ProgressionPolicy(
    policy_id="daycare-nanny-circuit-7-8",
    minimum_level=7,
    maximum_level=8,
    status="verified",
    execution="daycare-nanny-hunt",
    summary=(
        "A source-backed, live-considered two-nanny circuit in Dwarven Day "
        "Care, with explicit bystander and crowd gates."
    ),
    evidence=(
        "DD4 source revision 0482387: the recall route to rooms 6602 and 6604 has no reachable above-level aggressive reset.",
        "DD4 source: the nannies are non-aggressive source-level-5 cleric specials whose reboot-fuzzed levels can reach 7.",
        "DD4 source: the room-6602 nanny carries a linen robe; the other reset companions are explicitly excluded as targets.",
        "DD4 source: nanny mobile 6606 uses spec_cast_cleric, whose level-zero spell case can cast blindness; healer.c confirms the Midgaard healer can cast cure blindness.",
        "Every nanny must pass the existing exact-description, room-crowd, full state, and live-consider gates before combat.",
        "Live runs 706 and 707 traversed both reset rooms and returned safely to healer room 3054; both nannies were absent in that reboot window, so the campaign rotates areas instead of repeating indefinitely.",
        "Live run 712 considered a reboot-fuzzed level-4 nanny in room 6604, killed her for 149 XP, collected her robe, potion, and food drop, and recovered at healer room 3054; blindness was not selected in that fight.",
        "Live run 790: level-7 dwarf warrior Dorrik considered and killed a nanny for 192 XP. Its cleric blindness triggered recall and healer recovery; the completed save-and-quit was recorded as a successful campaign segment.",
        "Live run 798: level-7 drow thief Kestrel killed a nanny for 69 XP, recovered an amber potion, woke to address hunger and thirst during healer recovery, and returned safely to room 3054.",
    ),
    practice_skill=None,
    segment_kill_limit=2,
)

_CIRCUS_ILLUSIONIST_LEVEL_SEVEN_POLICY = ProgressionPolicy(
    policy_id="circus-illusionist-7-8",
    minimum_level=7,
    maximum_level=8,
    status="verified",
    execution="circus-freak-show-hunt",
    summary=(
        "A bounded three-performer Circus sweep that considers each "
        "non-aggressive target and recovers locally when the room is vetted."
    ),
    evidence=(
        "DD4 source revision 0482387: mobile 4407 is a single, non-aggressive, unarmed level-five reset in Circus room 4410.",
        "DD4 source: Bobby's mother is a non-aggressive level-three wanderer; live combat shows she can assist, so her presence blocks engagement like every other bystander.",
        "Live run 859 considered the Illusionist an easy kill and returned to healer room 3054 without combat.",
        "Live run 861 killed exactly one Illusionist for 190 XP, looted its key, recalled, and recovered fully at healer room 3054.",
        "Live run 862 considered the level-five Bearded Lady a perfect match; source confirms she is non-aggressive, has no special, and carries no weapon.",
        "Live run 913: a fuzzed animal keeper joined combat against level-seven Dorrik, so Circus performers are engaged only when no bystander is present.",
        "DD4 source revision 0482387: Ivan is a non-aggressive level-seven sentinel with no special; every attempted engagement remains live-consider gated.",
        "DD4 source room graph: Ivan resets in Strongman's room 4413, reached from the Illusionist by west, west, south.",
        "DD4 source: level-zero Beastly Fido has only the corpse-scavenging spec_fido special; his wimpy flag suppresses ordinary aggression against an awake character and fight.c's level-gap gate prevents him assisting against level-seven or level-eight characters.",
        "GMCP room-description targets are removed before crowd checks so the tent's illusory Dragon prose is not treated as a mobile.",
        "Live runs 959 and 961: a wandering level-one Midgaard drunk intercepted visible Aeloria for 10 XP on the approach; after capability-driven invisibility was enabled, she crossed uninterrupted and killed the Bearded Lady for 192 XP.",
        "Live run 1043 reached Ivan's corrected room and confirmed the wandering Beastly Fido bystander before returning safely to healer room 3054.",
        "Live run 1044 preserved the crowd gate when an animal keeper and Bobby's mother wandered into Ivan's tent; neither is an approved bystander.",
    ),
    practice_skill=None,
    segment_kill_limit=3,
)

_CIRCUS_FREAK_SHOW_LEVEL_EIGHT_POLICY = ProgressionPolicy(
    policy_id="circus-freak-show-8-9",
    minimum_level=8,
    maximum_level=9,
    status="verified",
    execution="circus-freak-show-hunt",
    summary=(
        "Repeat the three-performer Circus sweep for martial characters after "
        "Mud School opponents stop providing worthwhile experience."
    ),
    evidence=(
        *_CIRCUS_ILLUSIONIST_LEVEL_SEVEN_POLICY.evidence,
        "Live run 879: level-seven thief Kestrel completed the three-stop sweep, reached level eight, and returned safely to healer room 3054.",
        "Live runs 881-882: every Mud School opponent considered below the useful level band for level-eight Kestrel, establishing the need for field progression.",
        "Each performer remains independently live-consider gated, so reboot-level fuzz cannot force an unsuitable engagement.",
        "Live run 913 overrides static level assumptions: wandering Circus mobiles are treated as unsafe bystanders because load-level fuzz can place them inside fight.c's assist band.",
        "Beastly Fido is the only approved Ivan-room bystander; every other wandering mobile still blocks engagement.",
        "Live run 946: level-eight Kestrel remembered the Loremaster's Stealth Techniques cap, trained Defense Knowledge instead, then killed the Bearded Lady for 231 XP and recovered at full health.",
        "Live runs 1050 and 1054 exposed distinct short-name aliases: GMCP and combat use Ivan while room prose uses Ivan the Strongman, and flee text reports Ivan leaves. Proper-name prefix matching now covers both combat and pursuit without weakening the unrelated-attacker gate.",
        "Live run 1055 safely retried the corrected sweep, killed the Illusionist, and returned to healer room 3054 after Ivan had wandered away.",
    ),
    practice_skill=None,
    segment_kill_limit=3,
)

_DAYCARE_ARMED_GUARD_LEVEL_EIGHT_POLICY = ProgressionPolicy(
    policy_id="daycare-armed-guard-8-9",
    minimum_level=8,
    maximum_level=9,
    status="verified",
    execution="daycare-armed-guard-hunt",
    summary=(
        "Navigate the live Day Care mini-maze and hunt its isolated armed "
        "guard after an exact-target and live-consider gate."
    ),
    evidence=(
        "DD4 source revision 0482387 places one source-level-8 armed guard in room 6624.",
        "The guard has no weapon, special procedure, aggressive flag, or reset companion.",
        "The source-derived route from recall contains no reachable above-level aggressive reset.",
        "Live run 991 followed GMCP destination VNUMs through the shuffled maze, found exactly one guard, received the perfect-match consider result at full health, and returned safely to healer room 3054 without combat.",
        "Live run 992 killed the isolated guard for 728 XP at level 8, then recalled and recovered to full health and movement at healer room 3054.",
        "Live run 996 killed the guard for 492 XP with level-eight thief Kestrel; health remained at or above 110/135 before full healer recovery.",
        "Live run 1100 killed a reboot-fuzzed 144-HP guard for 453 XP inside the 150-second combat cap; Kestrel finished at 132/135 HP and returned safely to healer room 3054.",
        "Live runs 1111 and 1117 killed two reboot-fuzzed guards for 409 and 333 XP with level-eight warrior Dorrik; neither fight reduced her below 160/177 HP.",
        "Live run 1122 killed a perfect-match guard for 328 XP, raising Dorrik to level nine with 20 HP, 4 mana, 10 movement, 2 physical practices, and 1 intellectual practice before safe healer recovery.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)

_CULT_FANATIC_LEVEL_EIGHT_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="cult-fanatic-research-8-9",
    minimum_level=8,
    maximum_level=9,
    status="retired",
    execution="cult-fanatic-research",
    summary=(
        "Retired research route for the wandering Dragon Cult fanatic; do not "
        "spend autonomous progression segments searching for it."
    ),
    evidence=(
        "DD4 source revision 0482387 places one non-aggressive, unarmed source-level-6 fanatic monk in room 9850.",
        "The fanatic lacks the sentinel flag and can wander away from its reset room.",
        "The reset companion is a non-aggressive source-level-4 receptionist; both mobiles have no special procedure.",
        "The official level-5-25 Dragon Cult fastwalk reaches room 9850 directly from Midgaard recall.",
        "Live runs 1009 and 1014 reached room 9850 safely but found no fanatic; run 1014 instead found a wandering Beastly Fido in the reception.",
        "The mobile's unreliable availability makes this route inferior to the verified level-eight rotation.",
    ),
    practice_skill=None,
)

_FLESHMONGER_GUARD_LEVEL_EIGHT_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="fleshmonger-guard-research-8-9",
    minimum_level=8,
    maximum_level=9,
    status="retired",
    execution="fleshmonger-guard-research",
    summary=(
        "Retired level-eight research route: reconsider the armored foyer guard "
        "at level nine before enabling combat."
    ),
    evidence=(
        "DD4 source revision 0482387 places one source-level-10 patrolling guard alone in foyer room 9400.",
        "The guard is non-aggressive, sentinel, stay-area, and has no special procedure.",
        "Its greet program only speaks, and its reset equips four armour pieces plus a notched scimitar.",
        "The official level-5-12 Fleshmonger fastwalk reaches room 9400 without an aggressive reset on the route.",
        "Live run 1029 found Dorrik slightly healthier but returned the do_consider diff 2-5 'Do you feel lucky, punk?' branch.",
        "The armed, armored above-level target is not approved for level-eight combat without sanctuary evidence.",
    ),
    practice_skill=None,
)

_FLESHMONGER_GUARD_LEVEL_TEN_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="fleshmonger-guard-probe-10-12",
    minimum_level=10,
    maximum_level=12,
    status="research",
    execution="fleshmonger-guard-research",
    summary=(
        "Collect one bounded live consideration of the isolated Fleshmonger "
        "foyer guard without initiating combat."
    ),
    evidence=(
        "DD4 source revision 0482387 places one source-level-10 patrolling guard alone in foyer room 9400.",
        "The guard is non-aggressive, sentinel, stay-area, and has no special procedure.",
        "Its greet program only speaks; its reset equips four armour pieces and a notched scimitar.",
        "The official level-5-12 Fleshmonger fastwalk reaches room 9400 without an aggressive reset on the route.",
        "Live run 1028 verified the no-combat round trip from healer room 3054 to the foyer and back.",
        "Live run 1029 rejected combat at level eight after the guard returned the do_consider diff 2-5 branch.",
        "This research policy only records the current level, reboot, crowd, and consider result; it cannot attack.",
    ),
    practice_skill=None,
)

_FLESHMONGER_GUARD_LEVEL_TEN_KILL_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="fleshmonger-guard-kill-research-10-11",
    minimum_level=10,
    maximum_level=11,
    status="research",
    execution="fleshmonger-guard-hunt",
    summary=(
        "Attempt one live-considered Fleshmonger foyer guard with the level-ten "
        "warrior profile, then return to the Midgaard healer."
    ),
    evidence=(
        "DD4 source revision 0482387 places one source-level-10 patrolling guard alone in foyer room 9400.",
        "The guard is non-aggressive, sentinel, stay-area, and has no special procedure.",
        "Its greet program only speaks; its reset equips four armour pieces and a notched scimitar.",
        "Live run 1408 reached the foyer safely after training enhanced damage and defense knowledge.",
        "Live run 1408 returned the exact-level do_consider 'The perfect match!' branch and reported Dorrik healthier than the guard.",
        "This research policy permits exactly one kill and retains live crowd, consider, health, withdrawal, and safe-return gates.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)

_FLESHMONGER_MAGE_GUARD_LEVEL_TEN_RESEARCH_POLICY = replace(
    _FLESHMONGER_GUARD_LEVEL_TEN_KILL_RESEARCH_POLICY,
    policy_id="fleshmonger-mage-guard-kill-research-10-11",
    summary=(
        "Attempt one bounded live-considered Fleshmonger foyer guard hunt with "
        "the field-caster combat runner after an empty Moria acquisition pass."
    ),
    evidence=(
        *_FLESHMONGER_GUARD_LEVEL_TEN_KILL_RESEARCH_POLICY.evidence,
        "The mage-specific route remains research until a live caster result "
        "confirms its damage, recovery, and XP behavior.",
    ),
)

_FLESHMONGER_THIEF_GUARD_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="fleshmonger-thief-guard-research-10-11",
    minimum_level=10,
    maximum_level=11,
    status="research",
    execution="fleshmonger-guard-circuit-research",
    summary=(
        "Assess both isolated Fleshmonger guards with the level-ten thief "
        "profile, attack only an in-band spawn, and return to the healer."
    ),
    evidence=(
        "DD4 source revision 0482387 places isolated non-aggressive source-level-10 guards in rooms 9400 and 9401.",
        "Both guards are sentinel, stay-area, lack special procedures, and carry the same five-piece equipment set.",
        "Live run 1415 verified Kestrel's thief route, class-guild training, full-health departure, and safe return.",
        "Run 1415 rejected the foyer guard's above-band do_consider result without initiating combat.",
        "The second stop independently repeats the crowd, consider, health, and withdrawal gates before permitting one fight.",
        "The class-aware combat opener uses backstab only when it is known and a piercing weapon is visibly equipped.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)

_FLESHMONGER_THIEF_GUARD_POLICY = ProgressionPolicy(
    policy_id="fleshmonger-thief-guard-10-11",
    minimum_level=10,
    maximum_level=11,
    status="verified",
    execution="fleshmonger-guard-circuit",
    summary=(
        "Assess both isolated Fleshmonger guards, kill the first in-band spawn "
        "with the thief combat profile, and return to the healer."
    ),
    evidence=(
        "DD4 source revision 0482387 places isolated non-aggressive source-level-10 guards in rooms 9400 and 9401.",
        "Live run 1419 skipped the above-band foyer guard and independently found the north guard to be a perfect match.",
        "Kestrel killed the north guard for 423 XP, ending the field fight at 112/154 hit points.",
        "Run 1419 recovered from the guard's disarm by rearming the carried piercing dagger, looted all five reset items, and returned safely to healer room 3054.",
        "The policy retains a one-kill ceiling, per-stop crowd and consider gates, a 60% second-stop health floor, and healer recovery.",
        "The opener will switch to source-verified backstab after Stealth Techniques 60% unlocks it and a piercing weapon is equipped.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)

_FLESHMONGER_MUFTI_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="fleshmonger-mufti-probe-10-11",
    minimum_level=10,
    maximum_level=11,
    status="research",
    execution="fleshmonger-mufti-research",
    summary=(
        "Count and consider the Fleshmonger barracks guards without attacking, "
        "then return to the healer."
    ),
    evidence=(
        "DD4 source revision 0482387 places up to four source-level-10 mufti guards in room 9402.",
        "The mufti guards are non-aggressive, sentinel, stay-area, and have no special procedure.",
        "Room 9402 is directly south of the verified foyer behind a closed but unlocked door.",
        "The probe cannot attack; it records the live count and consider band so a later policy can require one isolated viable guard.",
    ),
    practice_skill=None,
)

_FLESHMONGER_COOK_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="fleshmonger-cook-probe-v2-10-11",
    minimum_level=10,
    maximum_level=11,
    status="research",
    execution="fleshmonger-cook-research",
    summary=(
        "Consider the Fleshmonger kitchen cook without attacking while "
        "recording its low-level helper as a bystander."
    ),
    evidence=(
        "DD4 source revision 0482387 places one source-level-8 cook and one source-level-6 cook's boy in room 9403.",
        "Neither mobile is aggressive or has a special procedure; both are sentinel and stay-area.",
        "The kitchen is directly east of the verified foyer behind a closed but unlocked door.",
        "The cook carries whites and a wooden spoon, while the boy carries a vest and leggings for later sale.",
        "Live run 1423 showed that the shared `cook` keyword selects the boy first.",
        "The corrected probe uses source-backed ordinal keyword `2.cook`; it cannot attack and records the adult cook's live consider band.",
    ),
    practice_skill=None,
)

_FLESHMONGER_COOK_IDENTITY_RESEARCH_POLICY = replace(
    _FLESHMONGER_COOK_RESEARCH_POLICY,
    policy_id="fleshmonger-cook-identity-probe-v3-10-11",
    summary=(
        "Try both live kitchen ordinals without combat, rejecting any consider "
        "response that resolves to the cook's boy."
    ),
    evidence=(
        *_FLESHMONGER_COOK_RESEARCH_POLICY.evidence,
        "Live run 1436 proved that `2.cook` can resolve to the cook's boy after a reset, so ordinal position is not a stable identity.",
        "The v3 probe tries `cook` and `2.cook` as separate candidates and rejects either candidate when the consider response explicitly names the boy.",
    ),
)

_FLESHMONGER_COOK_POLICY = ProgressionPolicy(
    policy_id="fleshmonger-cook-10-11",
    minimum_level=10,
    maximum_level=11,
    status="verified",
    execution="fleshmonger-cook-hunt",
    summary=(
        "Attack the ordinal-selected adult Fleshmonger cook after a live "
        "consider check, then return to the healer."
    ),
    evidence=(
        "DD4 source revision 0482387 places one non-aggressive source-level-8 cook without a special procedure in room 9403.",
        "The source-level-6 cook's boy is the only reset bystander and is treated as trivial rather than a reason to abandon a viable target.",
        "Live run 1424 used `consider 2.cook`, received the exact-level perfect-match branch, and found Kestrel slightly healthier.",
        "Live run 1425 killed the adult cook for 696 XP; the boy did not join, and Kestrel recalled at 75/154 hit points.",
        "Run 1425 recovered to full health and movement, saved, and quit in healer room 3054.",
        "The cook carries whites and a wooden spoon; the one-kill policy retains full-health departure, crowd, consider, withdrawal, and healer-return gates.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)

_FLESHMONGER_COOK_IDENTITY_POLICY = replace(
    _FLESHMONGER_COOK_POLICY,
    policy_id="fleshmonger-cook-identity-10-11",
    summary=(
        "Kill the adult cook only after the live ordinal candidate resolves "
        "without naming the cook's boy."
    ),
    evidence=(
        *_FLESHMONGER_COOK_POLICY.evidence,
        "Live run 1443 reached the kitchen without combat, where `consider cook` returned the perfect-match branch and `consider 2.cook` returned `They're not here`.",
        "The live room therefore contained one unambiguous cook match; the two-candidate policy still rejects any future response that explicitly names the boy.",
        "Live run 1444 used `consider cook` and `kill cook`, killed the adult for 504 XP without taking damage, looted its whites and spoon, and returned safely.",
    ),
)

_AMBUSH_ARCHER_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="ambush-archer-probe-10-11",
    minimum_level=10,
    maximum_level=11,
    status="research",
    execution="ambush-archer-research",
    summary=(
        "Follow the source-backed exterior trail to the isolated goblin archer, "
        "consider it without attacking, and return to the healer."
    ),
    evidence=(
        "DD4 source revision 0482387 places one non-aggressive source-level-9 goblin archer in room 4515.",
        "The archer has no special procedure and is reached by an unlocked brush door from the established Ambush exterior route.",
        "Its reset equips a bow, quiver, helmet, leggings, and boots; the bow raises the source risk estimate.",
        "The probe cannot attack and retains route, crowd, consider, unexpected-combat, withdrawal, and healer-return gates.",
    ),
    practice_skill=None,
)

_AMBUSH_ARCHER_KILL_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="ambush-archer-kill-research-10-11",
    minimum_level=10,
    maximum_level=11,
    status="research",
    execution="ambush-archer-hunt",
    summary=(
        "Attack one isolated goblin archer after a live perfect-match result, "
        "then return to the healer."
    ),
    evidence=(
        "DD4 source revision 0482387 places one non-aggressive source-level-9 goblin archer without a special procedure in room 4515.",
        "The archer equips a bow and armour, so the policy permits exactly one fight from at least 85% health.",
        "Live run 1428 reached the archer alone, received the perfect-match consider branch, and returned safely.",
        "Live run 1429 attacked from 154/154 hit points, was disarmed, earned only 3 XP without a kill, and recalled at 38/154.",
        "Run 1429 recovered safely at the healer, but the poor damage efficiency retires this target for level-10 thief progression.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)

_GNOME_GUARD_LEVEL_TEN_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="gnome-guard-hut-probe-10-11",
    minimum_level=10,
    maximum_level=11,
    status="research",
    execution="gnome-guard-research",
    summary=(
        "Revalidate the unarmed Gnome hut guard at level ten without attacking, "
        "then return to the healer."
    ),
    evidence=(
        "DD4 source revision 0482387 places one non-aggressive source-level-8 gnome guard without a special procedure in room 1519.",
        "The room-1519 reset gives this guard a potion and bloody cloak but no weapon; later circuit guards are excluded from this probe.",
        "Live runs 949 and 957 established the route and productive combat at level eight, but level ten needs a fresh consider result because reset fuzz can load the guard from level 6 through 10.",
        "The probe cannot attack and retains exact-target, sole-mobile, live-consider, unexpected-combat, withdrawal, and healer-return gates.",
    ),
    practice_skill=None,
)

_FLESHMONGER_THIEF_ROTATION_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="fleshmonger-thief-rotation-research-v8-10-11",
    minimum_level=10,
    maximum_level=11,
    status="research",
    execution="fleshmonger-thief-rotation-research",
    summary=(
        "Sweep the two isolated Fleshmonger guards and adult cook, taking at "
        "most two independently gated fights before returning to the healer."
    ),
    evidence=(
        "DD4 source revision 0482387 places isolated source-level-10 guards in rooms 9400 and 9401, and the source-level-8 adult cook with one trivial helper in room 9403.",
        "Live run 1419 killed the north guard for 423 XP and returned with 112/154 hit points after recovering from a disarm.",
        "Live run 1425 killed the adult cook for 696 XP; its source-level-6 helper did not join, and Kestrel recalled at 75/154 hit points.",
        "Live runs 1421 and 1427 found individual targets absent, showing why one route should inspect all three rather than pay recall travel for a single reset.",
        "Live run 1432 was interrupted in Midgaard by source-level-2 mobile 3064 before reaching the area; v2 uses the source-backed trivial-interruption policy instead of paying repeated flee penalties.",
        "Live run 1433 skipped the above-band foyer guard and killed the perfect-match north guard for 476 XP, repeatedly rearming its dagger after disarms.",
        "Run 1433 recalled safely after the first loot because the generic one-way route threshold required 80% health.",
        "The v3 launch failed before connection because the locked-door route is not safely reversible; v4 keeps recall-only return while allowing post-loot continuation when the next stop's explicit health floor is met.",
        "Live run 1436 killed the north guard for 420 XP and continued at 132/154 HP, proving the dynamic continuation threshold.",
        "Run 1436 also proved that room-list ordering can make `2.cook` resolve to the boy; v5 rejects any consider response naming the boy and tries both ordinal forms until one resolves to the adult.",
        "Live run 1438 skipped a crowded foyer, killed the perfect-match north guard for 472 XP, recalled at 58/154 hit points, and recovered fully at the healer.",
        "Live run 1454 admitted a reset-level-11, 169-HP north guard through the generic perfect-match consider branch, then withdrew at 41/154 HP for only 69 net XP after flee cost; v6 limits both guard stops to live targets no higher than the character.",
        "Live run 1455 proved DD4 exposes the exact target level only after combat starts; v7 enforces the same ceiling on the first Char.Enemies combat snapshot and withdraws immediately when that reveals an over-ceiling target.",
        "Live run 1456 confirmed first-snapshot withdrawal prevented injury but still cost 74 net XP; v8 uses the source-defined do_consider health comparison to skip healthier guards before combat while retaining the live-level fallback.",
        "Each stop retains exact-target, crowd, live-consider, health, disarm, withdrawal, and healer-return handling; the research circuit stops after two kills.",
    ),
    practice_skill=None,
    segment_kill_limit=2,
)

_FLESHMONGER_THIEF_ROTATION_POLICY = replace(
    _FLESHMONGER_THIEF_ROTATION_RESEARCH_POLICY,
    policy_id="fleshmonger-thief-rotation-10-11",
    status="verified",
    summary=(
        "Repeat the evidenced Fleshmonger guard-and-kitchen rotation while "
        "its latest segment remains productive."
    ),
    evidence=(
        *_FLESHMONGER_THIEF_ROTATION_RESEARCH_POLICY.evidence,
        "Live runs 1433, 1436, and 1438 produced 476, 420, and 472 XP respectively from independently gated north-guard fights.",
        "The latest run's low post-kill health correctly prevented a second fight, demonstrating that the more aggressive continuation policy remains bounded.",
        "Live run 1446 completed the first verified two-target sweep: the north guard yielded 294 XP, Kestrel continued at 121/154 HP, and the adult cook yielded 439 XP for 733 XP total before safe healer recovery.",
        "Live run 1448 repeated the full sweep after the area reset, yielding 414 XP from the guard and 397 XP from the cook for 811 XP total; Kestrel ate a severed body part, respected the weight limit, and returned safely at 114/154 HP.",
        "Live run 1452 encountered a high-roll 178-HP guard, won for 526 XP at 56/154 HP, skipped the cook, recalled, and recovered safely; mob identity alone must not bypass live health and continuation gates.",
        "Live run 1457 validated v8 against the unchanged high-roll reset: it skipped the healthier guard before combat, killed the adult cook for 265 XP without taking damage, looted both items, and returned safely.",
    ),
)

_FLESHMONGER_SERVANT_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="fleshmonger-servant-probe-v1-10-11",
    minimum_level=10,
    maximum_level=11,
    status="research",
    execution="fleshmonger-servant-research",
    summary=(
        "Pass through the non-aggressive Library and consider the isolated "
        "Study servant without opening the Laboratory trapdoor."
    ),
    evidence=(
        "DD4 source revision f703daa places one source-level-8 hobgoblin servant in Study room 9418.",
        "Mobile 9411 is non-aggressive, stay-area, wimpy, and has no special procedure; its reset equips pants and a shirt.",
        "The source route is up from foyer room 9400 through Library room 9417, then up to the Study.",
        "Two non-aggressive servants reset in the intervening Library, so the endpoint still requires exactly one target and no bystander.",
        "The closed upward trapdoor in room 9418 isolates the probe from the source-level-12 senior guard and source-level-15 Fleshmonger in room 9419.",
        "The probe cannot attack and records live target count, consider band, room state, and safe healer return before any kill policy is registered.",
    ),
    practice_skill=None,
)

_FLESHMONGER_SERVANT_KILL_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="fleshmonger-servant-kill-research-v1-10-11",
    minimum_level=10,
    maximum_level=11,
    status="research",
    execution="fleshmonger-servant-hunt",
    summary=(
        "Attack one isolated Study servant after live consideration, then "
        "recall to the Midgaard healer."
    ),
    evidence=(
        *_FLESHMONGER_SERVANT_RESEARCH_POLICY.evidence,
        "Live run 1461 traversed Library room 9417 without incident despite its two passive servants.",
        "Run 1461 found exactly one hobgoblin servant in Study room 9418 while the Laboratory trapdoor remained visibly closed.",
        "The live consider result said the servant looked like an easy kill and that Kestrel was slightly healthier.",
        "Run 1461 recalled without combat, recovered to full health and movement at healer room 3054, saved, and quit safely.",
        "The kill probe requires at least 85% health, one exact target, no bystander, a non-healthier consider result, and no target above the character's live level.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)

_FLESHMONGER_THIEF_EXTENDED_ROTATION_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="fleshmonger-thief-extended-rotation-research-v1-10-11",
    minimum_level=10,
    maximum_level=11,
    status="research",
    execution="fleshmonger-thief-extended-rotation-research",
    summary=(
        "Sweep the independently evidenced guards, adult cook, and Study "
        "servant, stopping after two gated kills."
    ),
    evidence=(
        *_FLESHMONGER_THIEF_ROTATION_POLICY.evidence,
        *_FLESHMONGER_SERVANT_KILL_RESEARCH_POLICY.evidence,
        "Live run 1462 killed the level-8 Study servant for 372 XP, looted both source-predicted garments, and recalled at 131/154 hit points.",
        "The extension moves west from the kitchen to foyer room 9400, then up through the passive Library to Study room 9418.",
        "A two-kill cap preserves the established bounded rotation: the servant replaces an absent or rejected earlier target rather than adding a third fight.",
        "The servant stop requires at least 60% health after earlier fights and retains exact-target, sole-mobile, non-healthier-consider, and live-level gates.",
    ),
    practice_skill=None,
    segment_kill_limit=2,
)

_FLESHMONGER_THIEF_EXTENDED_ROTATION_POLICY = replace(
    _FLESHMONGER_THIEF_EXTENDED_ROTATION_RESEARCH_POLICY,
    policy_id="fleshmonger-thief-extended-rotation-10-11",
    status="verified",
    summary=(
        "Repeat the guarded Fleshmonger sweep through the Study while the "
        "composed route remains productive."
    ),
    evidence=(
        *_FLESHMONGER_THIEF_EXTENDED_ROTATION_RESEARCH_POLICY.evidence,
        "Live run 1464 rejected the healthier north guard, killed the level-10 cook for 394 XP, and continued from 117/154 hit points.",
        "Run 1464 traversed kitchen, foyer, passive Library, and Study in one segment; the previously killed servant was absent, so the empty stop caused a safe recall rather than forced combat.",
        "Run 1464 recovered at healer room 3054 and checkpointed with 1,782 XP remaining to level 11.",
        "A populated same-segment cook-plus-servant pair remains useful additional evidence, but run 1462 independently verifies the exact servant fight and run 1464 verifies the composed continuation path.",
        "Live run 1468 found two same-vnum level-10 guards in basement room 9406, fled their automatic assistance at 35/154 HP, and safely recovered; that room is excluded because its source reset maximum_count is 2 even though it uses one reset command.",
    ),
)

_FLESHMONGER_THIEF_LEVEL_ELEVEN_POLICY = replace(
    _FLESHMONGER_THIEF_EXTENDED_ROTATION_POLICY,
    policy_id="fleshmonger-thief-rotation-11-12",
    minimum_level=11,
    maximum_level=12,
    summary=(
        "Progress from level 11 by sweeping the independently gated "
        "Fleshmonger guards, adult cook, and Study servant."
    ),
    evidence=(
        *_FLESHMONGER_THIEF_EXTENDED_ROTATION_POLICY.evidence,
        "Live run 1504: level-11 Kestrel skipped a crowded foyer, rejected a "
        "perfect-match guard because the guard was healthier, and selected "
        "the adult cook only after an easy-kill live consider result.",
        "Run 1504 killed the reboot-fuzzed level-8 cook for 274 XP, never fell "
        "below 137/165 hit points, looted both source-predicted items, and "
        "saved and quit in healer room 3054.",
        "Live run 1507 repeated the level-11 cook fight for 251 XP, recovered "
        "and rewielded its dagger after five disarms, looted and sacrificed "
        "the corpse, and returned safely to healer room 3054 at 114/165 HP.",
        "The level-11 route retains the verified Study servant as a fallback "
        "for absent or rejected earlier targets and remains capped at two kills.",
    ),
)

_FLESHMONGER_THIEF_LEVEL_TWELVE_RESEARCH_POLICY = replace(
    _FLESHMONGER_THIEF_LEVEL_ELEVEN_POLICY,
    policy_id="fleshmonger-thief-rotation-research-12-13",
    minimum_level=12,
    maximum_level=13,
    status="research",
    summary=(
        "Revalidate the live-gated Fleshmonger thief rotation at level 12 "
        "before promoting a level-12 field policy."
    ),
    evidence=(
        "DD4 source revision d7cb330 places the isolated source-level-10 "
        "guards in rooms 9400 and 9401, the adult cook in room 9403, and "
        "the Study servant in room 9418.",
        "The established route retains exact-target, crowd, consider, live "
        "level, combat-health, disarm, withdrawal, and healer-return gates.",
        "Level-11 runs 1563, 1565, 1568, 1572, and 1574 produced 508, 273, "
        "428, 432, and 214 XP from independently selected guards, cooks, "
        "and servants while recovering safely at healer room 3054.",
        "This research policy is deliberately bounded to two kills and must "
        "record a level-12 result before a verified level-12 policy exists.",
    ),
)

_FLESHMONGER_THIEF_LEVEL_TWELVE_POLICY = replace(
    _FLESHMONGER_THIEF_LEVEL_TWELVE_RESEARCH_POLICY,
    policy_id="fleshmonger-thief-rotation-12-13",
    status="verified",
    summary=(
        "Use the live-gated Fleshmonger thief rotation at level 12 after "
        "liquidating loot and preparing a source-backed combat kit."
    ),
    evidence=(
        *_FLESHMONGER_THIEF_LEVEL_TWELVE_RESEARCH_POLICY.evidence,
        "Live run 1578: level-12 Kestrel rejected no safety gate, killed the "
        "isolated patrolling guard for 354 XP, and recalled safely at 145/182 "
        "hit points.",
        "The guard's five-item drop filled Kestrel's 140-weight capacity, so "
        "the runner recalled instead of risking a second drop; the campaign "
        "must liquidate compatible loot before the next circuit.",
        "Run 1578 confirmed a dagger, two +1 damroll war dog collars, two "
        "bracers, and one pink ice ring before departure; the registered Forest "
        "bear-claw upgrade remains higher priority while its live gates hold.",
    ),
)

_FLESHMONGER_TWO_GUARD_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="fleshmonger-two-guard-research-v2-10-11",
    minimum_level=10,
    maximum_level=11,
    status="research",
    execution="fleshmonger-guard-circuit-research",
    summary=(
        "Extend the verified foyer kill to the second isolated guard immediately "
        "north, then recall after at most two kills."
    ),
    evidence=(
        "DD4 source revision 0482387 places a second source-level-10 on-duty guard alone in room 9401.",
        "The room-9401 guard is non-aggressive, sentinel, stay-area, and has no special procedure.",
        "It carries the same jerkin, pothelm, bindings, and scimitar reset as the verified foyer guard.",
        "The only extra route is opening the north foyer door and moving north; the door is closed but not locked.",
        "Live run 1411 verifies the first guard, exact-level consider branch, loot set, recall, and healer return.",
        "The second fight requires at least 60% health; the deeper aggressive room-9406 guard is excluded.",
    ),
    practice_skill=None,
    segment_kill_limit=2,
)

_FLESHMONGER_GUARD_CIRCUIT_POLICY = ProgressionPolicy(
    policy_id="fleshmonger-guard-circuit-10-11",
    minimum_level=10,
    maximum_level=11,
    status="verified",
    execution="fleshmonger-guard-circuit",
    summary=(
        "Assess the isolated foyer and north guards independently, kill each "
        "viable spawn, loot it, and recover at the Midgaard healer."
    ),
    evidence=(
        "DD4 source revision 0482387 places isolated non-aggressive source-level-10 guards in rooms 9400 and 9401.",
        "Both guards are sentinel, stay-area, lack special procedures, and carry the same five-piece equipment set.",
        "Live run 1414 departed at full health and rejected the foyer guard's above-band consider result.",
        "Run 1414 independently considered the north guard, resolved it at live level 9, and killed it for 505 XP.",
        "Dorrik finished combat at 164/217 hit points, looted all five pieces, recalled, and recovered to 217/217 hit points and 240/240 movement in healer room 3054.",
        "Live run 1873 resolved the foyer guard at level 11 and received the perfect-match consider branch while level-10 Dorrik was slightly healthier.",
        "The policy excludes the aggressive basement guard and retains per-stop crowd, consider, health, withdrawal, two-kill, and safe-return gates.",
    ),
    practice_skill=None,
    segment_kill_limit=2,
)

_MORIA_LARGE_ORC_LEVEL_EIGHT_POLICY = ProgressionPolicy(
    policy_id="moria-large-orc-8-9",
    minimum_level=8,
    maximum_level=9,
    status="verified",
    execution="moria-large-orc-hunt",
    summary=(
        "Alternate the Circus with a two-room probe for one live-considered "
        "large orc on Moria level one, rejecting any room with a bystander."
    ),
    evidence=(
        "DD4 source revision 0482387: one source-level-seven large orc resets in Moria room 4022 and carries a yellow and green ring.",
        "The source-derived route remains on Moria level one and excludes the poison snake, deeper warriors, and every target after room 4022.",
        "Live run 736: level-seven Dorrik killed the large orc for 539 XP without losing health, looted its ring, recalled, and recovered at healer room 3054.",
        "Live run 736 also found a wandering kobold in the room; the promoted policy requires the target to be alone before consider or combat.",
        "Live runs 920 and 922 observed the orc wandering north into room 4023, so the bounded route checks both that room and reset room 4022.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)

_GNOME_GUARD_LEVEL_EIGHT_POLICY = ProgressionPolicy(
    policy_id="gnome-guard-circuit-8-9",
    minimum_level=8,
    maximum_level=9,
    status="verified",
    execution="gnome-guard-hunt",
    summary=(
        "Rotate through three source-level-eight Gnome guard resets, engaging "
        "only an isolated guard that passes live consideration."
    ),
    evidence=(
        "DD4 source revision 0482387: non-aggressive gnome guards reset in rooms 1519, 1527, and 1534 without special procedures.",
        "DD4 source: the room-1519 guard is unarmed and carries a bloody cloak; the later guards can carry gnome swords and therefore retain the stricter existing health and live-consider gates.",
        "The source-derived route from recall reaches room 1519 without a dangerous reset, then traverses ordinary non-aggressive village roads to the two later stops.",
        "Every room rejects duplicate guards or any bystander before consideration; wandering can still join after combat starts, so the live combat monitor must retain its unexpected-enemy and withdrawal gates.",
        "Live run 949: level-eight Dorrik killed the isolated hut guard for 543 XP, looted its cloak, potion, and key, skipped duplicate guards and a guard-plus-rat room, then recovered at the Midgaard healer.",
        "Live run 951: level-eight Kestrel traversed the same route safely after the hut guard was absent, rejecting three guards plus two rats at the gateway and one guard plus two giant rats in the Mess Hall.",
        "Live run 957: level-eight Kestrel killed an isolated guard for 582 XP; a wandering giant rat joined late and poisoned her, but she finished it for another 262 XP, recalled at 52/135 HP, and recovered fully beside the Midgaard healer.",
    ),
    practice_skill=None,
    segment_kill_limit=3,
)

_GNOME_GUARD_CASTER_LEVEL_SEVEN_POLICY = ProgressionPolicy(
    policy_id="gnome-guard-caster-7-8",
    minimum_level=7,
    maximum_level=8,
    status="verified",
    execution="gnome-guard-hunt",
    summary=(
        "Use one live-considered Gnome guard as a caster fallback after the "
        "established level-seven circuits stop producing experience."
    ),
    evidence=(
        "DD4 source revision 0482387: non-aggressive source-level-eight gnome guards reset without special procedures in rooms 1519, 1527, and 1534.",
        "The room-1519 guard is unarmed; all three stops reject bystanders and duplicate guards before consideration.",
        "The generic field gate rejects consideration branches outside the useful band, and live GMCP aborts combat if a fuzzed guard loads above character level plus one.",
        "Live runs 949 and 957 proved the route and isolated-guard combat at level eight; this level-seven caster policy is limited to one kill and retains full-health, mana, crowd, consider, and withdrawal gates.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)

_GNOME_SMALL_TROLL_CASTER_LEVEL_SEVEN_POLICY = ProgressionPolicy(
    policy_id="gnome-small-troll-caster-7-8",
    minimum_level=7,
    maximum_level=8,
    status="verified",
    execution="gnome-small-troll-hunt",
    summary=(
        "Approach the isolated aggressive Gnome small troll under invisibility, "
        "then engage only after a perfect-match live consideration."
    ),
    evidence=(
        "DD4 source revision 0482387: one unarmed, special-free, source-level-eight small troll resets alone in dead-end room 1524.",
        "The source-derived route reaches room 1524 without a dangerous reset; invisibility prevents the aggressive troll from forcing combat before consideration.",
        "Live run 1033 reached the troll at full resources under invisibility, recorded a perfect-match result, and returned untouched to healer room 3054.",
        "Live run 1035 killed the same target for 524 XP; Aeloria remained above 89/110 HP and recovered fully at healer room 3054.",
        "The policy requires the invisibility capability, full health, an exact isolated target, live consideration, and one kill at most.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)

_DAYCARE_ARMED_GUARD_LEVEL_SEVEN_POLICY = ProgressionPolicy(
    policy_id="daycare-armed-guard-7-8",
    minimum_level=7,
    maximum_level=8,
    status="verified",
    execution="daycare-armed-guard-hunt",
    summary=(
        "Navigate the live Day Care mini-maze and hunt its isolated armed "
        "guard after full-resource, exact-target, and live-consider gates."
    ),
    evidence=(
        "DD4 source revision 0482387 places one unarmed, non-aggressive, special-free source-level-8 guard alone in room 6624.",
        "Live runs 991 and 993 proved GMCP destination-VNUM navigation through two differently shuffled maze layouts.",
        "Live run 992 killed the guard safely with a level-eight martial character.",
        "Live run 994 found Aeloria slightly healthier than the perfect-match guard at full health and mana, then returned without combat.",
        "Live run 995 killed the guard for 410 XP with level-seven mage Aeloria; her health never fell below 104/110 before full healer recovery.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)

_AMBUSH_MARTIAL_LEVEL_EIGHT_POLICY = ProgressionPolicy(
    policy_id="ambush-martial-exterior-8-9",
    minimum_level=8,
    maximum_level=9,
    status="verified",
    execution="ambush-martial-hunt",
    summary=(
        "Sweep three live-considered Ambush exterior targets while retaining "
        "immediate withdrawal if the wandering dark horseman joins."
    ),
    evidence=(
        "DD4 source revision 0482387: the three targets are non-aggressive level-six or level-seven exterior resets with no player-trapping route segment.",
        "DD4 source: each target carries distinct armour, weapon, shield, or damroll-collar loot that Midgaard shops can buy.",
        "The existing source-derived exterior route reaches all three targets and returns through recall without entering the higher-level cave complex.",
        "Live run 326 killed a reboot-fuzzed level-seven war dog for 249 XP and returned safely to healer room 3054.",
        "Live run 327 established the wounded goblin as the highest-burst target in this set, so it is attempted first at full health and remains live-consider gated.",
        "The armed level-eight raider is deliberately excluded until sanctuary or stronger martial evidence is available.",
        "Live run 886: Kestrel killed a wandering goblin for 292 XP, but a dark horseman joined; the safety policy fled and recalled at 63/135 HP, losing 68 XP.",
        "Live run 1064: level-eight warrior Dorrik passed perfect-match checks and killed the wounded goblin and war dog for 538 combined XP, never fell below 152/177 HP, and returned safely after seeing but not engaging the wandering dark horseman.",
        "Live run 1068: level-eight thief Kestrel killed the wounded goblin for 266 XP at full health, recovered and rearmed after two disarms, then recalled when another drop would exceed his remaining carry capacity.",
        "Live run 1076: a mountain goblin attacked level-eight Dorrik on the approach while a dark horseman was present; the lone-attacker GMCP gate accepted it, Dorrik killed it for 185 XP without damage, and the horseman did not join.",
        "Live run 1079: level-eight thief Kestrel completed the wounded goblin, war dog, and goblin looter sweep for 882 XP, never fell below 119/135 HP, and recovered every disarm.",
        "Live run 1101: a level-eight mountain goblin blocked Kestrel's route movement; the lone-attacker gate adopted and killed it for 296 XP at full health, then continued the remaining circuit before recalling.",
        "Live run 1112: level-eight Dorrik accepted two consecutive useful-band wandering goblins for 507 combined XP and remained at or above 160/177 HP before healer recovery.",
        "Live run 1118: Dorrik killed a useful-band goblin lieutenant for 335 XP, ate its severed body part, sacrificed the corpse, and returned safely to healer room 3054.",
    ),
    practice_skill=None,
    segment_kill_limit=3,
)

_CIRCUS_FREAK_SHOW_LEVEL_NINE_POLICY = replace(
    _CIRCUS_FREAK_SHOW_LEVEL_EIGHT_POLICY,
    policy_id="circus-freak-show-9-10",
    minimum_level=9,
    maximum_level=10,
    summary=(
        "Sweep the Circus performers and ticketed Big Top at level nine, "
        "engaging only targets inside the useful live-consider band."
    ),
    evidence=(
        *_CIRCUS_FREAK_SHOW_LEVEL_EIGHT_POLICY.evidence,
        "The level-nine continuation preserves exact-target, crowd, and live-consider gates; targets that have fallen into a do_consider <= -5 branch are skipped.",
        "Live run 1107: level-nine Kestrel rejected a crowded first stop, skipped the Illusionist after the 'no match for you' consider result, found Ivan absent, and recovered fully at healer room 3054.",
        "Source revision 0482387 adds the adjacent non-aggressive Midget as a fourth live-considered stop; its fuzzed load is engaged only when it remains above the do_consider <= -5 branches.",
        "Source revision 0482387 places the ticket on the room-4402 clerk and uses it to unlock the Big Top entrance; its live purchase price remains reboot-local. The source-level-ten Ringmaster resets in room 4419 with only source-level-one audience members.",
        "Live run 1204 proved source-level-zero Beastly Fido no longer blocks consideration of the Illusionist; useful-band and unknown bystanders retain the crowd gate.",
        "Live run 1206 bought and retained the ticket, opened the Big Top, discounted only the level-one audience, killed the Ringmaster for 510 XP, and advanced Dorrik to level ten.",
    ),
    segment_kill_limit=5,
)

_MORIA_LARGE_ORC_LEVEL_NINE_POLICY = replace(
    _MORIA_LARGE_ORC_LEVEL_EIGHT_POLICY,
    policy_id="moria-large-orc-9-10",
    minimum_level=9,
    maximum_level=10,
    summary=(
        "Sweep the source-backed level-one Moria orc circuit at level nine, "
        "leaving the poison snake until last."
    ),
    evidence=(
        *_MORIA_LARGE_ORC_LEVEL_EIGHT_POLICY.evidence,
        "The source-level-seven target remains potentially useful at level nine, subject to reboot fuzz and the mandatory live-consider gate.",
        "The broader established circuit adds a second large-orc location, an orc-plus-snake room, and the snake last; every stop retains exact-target, crowd, health, and live-consider gates.",
    ),
    segment_kill_limit=3,
)

_MORIA_LARGE_ORC_MAGE_LEVEL_TEN_RESEARCH_POLICY = replace(
    _MORIA_LARGE_ORC_LEVEL_NINE_POLICY,
    policy_id="moria-large-orc-mage-research-10-11",
    minimum_level=10,
    maximum_level=11,
    status="research",
    summary=(
        "Probe the two isolated Moria large-orc stops with the mage combat "
        "runner after the level-10 sanctuary and guard options are exhausted."
    ),
    evidence=(
        *_MORIA_LARGE_ORC_LEVEL_NINE_POLICY.evidence,
        "The source candidate remains autonomous-safe at level 10-11 only "
        "with the two-stop route, exact target, crowd, and live-consider gates.",
        "Live run 2351 reached the source-matched Moria guard and received the "
        "healthier-than-you consider rejection without initiating combat.",
        "Live runs 2352-2354 completed the two-stop Moria route, found the "
        "large-orc target absent, and returned safely to healer room 3054; the "
        "later passes used bounded outside-area reset waits.",
    ),
    segment_kill_limit=1,
)

_MORIA_LARGE_ORC_MAGE_LEVEL_TEN_POLICY = replace(
    _MORIA_LARGE_ORC_MAGE_LEVEL_TEN_RESEARCH_POLICY,
    policy_id="moria-large-orc-mage-10-11",
    status="verified",
    summary=(
        "Hunt one isolated Moria large orc at a time with the mage combat "
        "runner, retaining the exact-target and live-consider gates."
    ),
)

_GNOME_GUARD_LEVEL_NINE_POLICY = replace(
    _GNOME_GUARD_LEVEL_EIGHT_POLICY,
    policy_id="gnome-guard-circuit-9-10",
    minimum_level=9,
    maximum_level=10,
    summary=(
        "Revalidate the three-stop Gnome guard circuit at level nine, retaining "
        "the exact-target, crowd, poison, and live-consider safety gates."
    ),
    evidence=(
        *_GNOME_GUARD_LEVEL_EIGHT_POLICY.evidence,
        "Source-level-eight guards remain potentially productive at level nine; each reboot-fuzzed load must still pass live consideration.",
    ),
)

_DAYCARE_ARMED_GUARD_LEVEL_NINE_POLICY = replace(
    _DAYCARE_ARMED_GUARD_LEVEL_EIGHT_POLICY,
    policy_id="daycare-armed-guard-9-10",
    minimum_level=9,
    maximum_level=10,
    summary=(
        "Revalidate the isolated Day Care armed guard at level nine after "
        "source-derived maze navigation and live consideration."
    ),
    evidence=(
        *_DAYCARE_ARMED_GUARD_LEVEL_EIGHT_POLICY.evidence,
        "Run 1105 raised Kestrel to level nine after the reboot-fuzzed guard yielded 307 XP; the same isolated reset remains live-consider gated.",
        "Live run 1127: level-nine Dorrik killed the perfect-match guard for 192 XP, remained above 183/197 HP, and recovered safely at healer room 3054.",
    ),
)

_AMBUSH_MARTIAL_LEVEL_NINE_POLICY = replace(
    _AMBUSH_MARTIAL_LEVEL_EIGHT_POLICY,
    policy_id="ambush-martial-exterior-9-10",
    minimum_level=9,
    maximum_level=10,
    summary=(
        "Revalidate the Ambush exterior sweep at level nine while retaining "
        "immediate withdrawal for unsafe joins or disabling conditions."
    ),
    evidence=(
        *_AMBUSH_MARTIAL_LEVEL_EIGHT_POLICY.evidence,
        "The source-level-six and level-seven exterior targets remain potentially useful at level nine, subject to reboot fuzz and live consideration.",
        "Live run 1123 exposed attack text arriving one event before named enemy GMCP; source-approved attackers now receive one structured-assessment cycle before withdrawal, while a second unassessed cycle still flees.",
        "Live run 1129: level-nine Dorrik completed the wounded goblin, war dog, and goblin looter sweep for 747 XP under the aggressive thresholds, finishing at 129/197 HP before safe healer recovery.",
    ),
)

_SHIRE_LEVEL_SEVEN_POLICY = ProgressionPolicy(
    policy_id="shire-bull-7-8",
    minimum_level=7,
    maximum_level=8,
    status="research",
    execution=None,
    summary=(
        "A source-backed single-target Shire circuit used to rotate away "
        "from depleted Daycare and Moria resets."
    ),
    evidence=(
        "DD4 source revision 0482387: mobile 1108 is an aggressive source-level-6 bull with no special procedure or equipped weapon.",
        "DD4 source: exactly one bull resets alone in room 1138, and the source-derived route reaches no above-level aggressive reset before that endpoint.",
        "Live run 709 killed the aggressive bull for 207 XP, looted and sacrificed its corpse, then recalled and checkpointed at healer room 3054 with full health and no adverse affect.",
        "Live run 730: the Thain wandered into the bull fight and joined combat; Kestrel fled at 20/123 health and recovered, so this route is research-only until multi-attacker isolation can be proven.",
        "Live run 787: Dorrik withdrew on the approach when an unapproved attacker joined field combat, losing 43 XP despite full health and flight. The route remains research-only for every archetype.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)

_GNOME_LEVEL_SEVEN_POLICY = ProgressionPolicy(
    policy_id="gnome-hermit-7-8",
    minimum_level=7,
    maximum_level=8,
    status="verified",
    execution="gnome-hermit-hunt",
    summary=(
        "A source-backed three-target Gnome mine circuit that rotates away "
        "from recently depleted Moria, Shire, and Daycare resets."
    ),
    evidence=(
        "DD4 source revision 0482387: mobile 1524 is an aggressive source-level-5 hermit crab with no special procedure or equipped weapon.",
        "DD4 source: exactly one hermit resets in room 1589, and the source-derived route reaches no above-level aggressive reset before that endpoint.",
        "DD4 source revision 0482387: separate non-aggressive source-level-5 hobgoblin miners reset in rooms 1563 and 1565, reached from the hermit by south-south-south then east-east without doors or special procedures.",
        "The target must pass exact identity and GMCP enemy-level gates; full starting health and the generic field withdrawal threshold bound the aggressive encounter.",
        "Live run 720 killed the hermit for 143 XP, looted and sacrificed its corpse, then recalled and checkpointed at healer room 3054 with 150/157 health and no adverse affect.",
        "Live run 788: level-7 drow thief Kestrel killed the hermit for 91 XP, used an observed body-part food drop before consuming carried provisions, and returned at full health to healer room 3054.",
        "Live runs 814 and 817: level-7 drow thief Kestrel killed the hermit for 131 then 83 XP and returned safely; after the ninth same-reboot hermit kill, run 819 found no confirmed target or XP. Day Care and Moria probes remain fallback routes rather than a reason to repeat a depleted hermit circuit.",
        "Live run 936: level-7 mage Aeloria killed the hermit for 107 XP without losing health; the two-miner extension retains independent crowd and consider gates.",
        "Live run 942: Aeloria killed the hermit for 90 XP and traversed both miner stops safely; two miners occupied each room, so the crowd gate skipped both and recalled at full health.",
        "Live runs 958 and 960: visible Aeloria was intercepted by the wandering Midgaard drunk before one attempt, while the next reached and killed the hermit for 90 XP; mage field runners now establish known invisibility before crossing the city.",
    ),
    practice_skill=None,
    segment_kill_limit=3,
)

_MIDENNIR_LEVEL_SEVEN_POLICY = ProgressionPolicy(
    policy_id="midennir-goblin-7-8",
    minimum_level=7,
    maximum_level=8,
    status="research",
    execution=None,
    summary=(
        "Source-backed Miden'nir goblin route awaiting a safe approach policy "
        "for wandering aggressive targets."
    ),
    evidence=(
        "Live runs 268, 270, 272, and 275 killed Miden'nir goblins for 361, 210, 244, and 216 XP.",
        "Live runs 270 and 274 safely withdrew from a wandering level-9 horseman and two simultaneous level-7 goblins.",
        "Live run 275 returned to the Mage Guild at full health and mana after one bounded kill.",
        "DD4 source resets a mountain goblin in room 3506, exactly one east of the official fastwalk endpoint.",
        "Empty or crowded spawn windows are retryable campaign checkpoints, not reasons to force combat.",
        "Live run 777: a level-7 mountain goblin wandered to the arrival room and auto-attacked before the planned stop; the generic field safety policy fled, lost 58 XP, and recovered safely. The route must not be selected for level 7 until an approach can retain live-consider safety.",
    ),
    practice_skill="magic missile",
    segment_kill_limit=1,
)

_MIDENNIR_SACK_POLICY = ProgressionPolicy(
    policy_id="midennir-sack-8-10",
    minimum_level=8,
    maximum_level=10,
    status="verified",
    execution="midennir-sack",
    summary=(
        "Train and verify invisibility, collect the source-backed large sack "
        "from room 4518, then recall and recover."
    ),
    evidence=(
        "DD4 source guarantees the 50-pound, 400-capacity large sack reset in room 4518.",
        "DD4 source and live routing establish the exact Ambush fastwalk and room-4518 path.",
        "The level-8 mage practice plan raises illusion magiks above the invis prerequisite and spends the remaining practices on invis.",
        "The runner verifies the invis affect before leaving safe Temple origin and aborts safely if it cannot establish the spell.",
    ),
    practice_skill="invis",
)

_MIDENNIR_LEVEL_EIGHT_POLICY = ProgressionPolicy(
    policy_id="midennir-goblin-8-10",
    minimum_level=8,
    maximum_level=10,
    status="verified",
    execution="midennir-hunt",
    summary=(
        "Repeat the bounded Miden'nir goblin segment after capacity "
        "infrastructure has been acquired."
    ),
    evidence=_MIDENNIR_LEVEL_SEVEN_POLICY.evidence,
    practice_skill="chill touch",
    segment_kill_limit=1,
)

_AMBUSH_LEVEL_EIGHT_POLICY = ProgressionPolicy(
    policy_id="ambush-war-dog-8-9",
    minimum_level=8,
    maximum_level=9,
    status="verified",
    execution="ambush-war-dog-hunt",
    summary=(
        "Hunt the lower-HP war dog on the Ambush exterior, then recall for "
        "healer recovery."
    ),
    evidence=(
        "DD4 source places the level-6 war dog in room 4505 and gives its collar +1 damroll.",
        "DD4 source places the level-7 goblin looter two rooms farther south on the same exterior circuit.",
        "Live run 326 killed a reboot-fuzzed level-7 war dog for 249 XP and returned safely to the Midgaard healer.",
        "Live run 327 lost 44 XP after three magic-missile attempts failed to finish the higher-HP wounded goblin.",
        "Live run 1079 proved the war-dog-to-looter route while the exact-target, crowd, consider, and withdrawal gates remained active.",
        "Live run 1297: level-eight Aeloria killed the war dog for 308 XP and remained at 78/120 HP, above the field continuation threshold.",
        "Live run 1305 showed the unprotected looter can outlast a failed flee and kill a 120-HP mage; the ordinary policy therefore stops after the dog.",
        "The route excludes the level-8 raider, level-10 guard, and the cave complex.",
    ),
    practice_skill="chill touch",
    segment_kill_limit=1,
)

_AMBUSH_PROTECTED_LEVEL_EIGHT_POLICY = ProgressionPolicy(
    policy_id="ambush-war-dog-looter-8-9",
    minimum_level=8,
    maximum_level=9,
    status="verified",
    execution="ambush-war-dog-hunt",
    summary=(
        "Sweep the war dog and goblin looter only while a source-identified "
        "sanctuary potion is available in the combat pouch."
    ),
    evidence=(
        *_AMBUSH_LEVEL_EIGHT_POLICY.evidence,
        "DD4 source gives the looter a spear, while sanctuary halves incoming damage.",
        "Live run 1301 completed the two-target circuit for 446 XP; the protected policy retains independent consider, crowd, and health gates.",
    ),
    practice_skill="chill touch",
    segment_kill_limit=2,
)

_AMBUSH_CASTER_LEVEL_SEVEN_POLICY = ProgressionPolicy(
    policy_id="ambush-war-dog-caster-7-8",
    minimum_level=7,
    maximum_level=8,
    status="verified",
    execution="ambush-war-dog-hunt",
    summary=(
        "Use invisibility and live consideration for one isolated Ambush war "
        "dog after the established level-seven caster circuits are depleted."
    ),
    evidence=(
        *_AMBUSH_LEVEL_EIGHT_POLICY.evidence,
        "Live run 1049: level-seven mage Aeloria reached the isolated war dog under invisibility, killed it with chill touch for 267 total XP, reached level eight at 102/120 HP, and recovered fully at healer room 3054.",
        "The exact crowd gate and generic field withdrawal policy remain mandatory because a wandering dark horseman can enter the exterior route.",
    ),
    practice_skill="chill touch",
    segment_kill_limit=1,
)

_AMBUSH_LEVEL_NINE_POLICY = ProgressionPolicy(
    policy_id="ambush-exterior-9-10",
    minimum_level=9,
    maximum_level=10,
    status="verified",
    execution="ambush-hunt",
    summary=(
        "Use trained chill touch against the proven lower-burst war dog on "
        "the Ambush exterior while no protection potion is available."
    ),
    evidence=(
        "DD4 source places the level-6 war dog on the Ambush exterior.",
        "Live runs 326 and 459 killed the reboot-fuzzed war dog safely.",
        "Live runs 469-470 showed that the reboot-fuzzed wounded goblin can force costly emergency withdrawal at level 9 when Ararisa lacks sanctuary.",
        "DD4 source gives trained chill touch a stronger damage range than the level-8 magic-missile loop.",
        "The route excludes the level-8 raider, level-10 guard, and the cave complex.",
    ),
    practice_skill="chill touch",
    segment_kill_limit=1,
)

_AMBUSH_VILE_LEVEL_NINE_POLICY = ProgressionPolicy(
    policy_id="ambush-vile-goblin-9-10",
    minimum_level=9,
    maximum_level=10,
    status="verified",
    execution="ambush-vile-hunt",
    summary=(
        "Revalidate the level-nine vile goblin only with sanctuary or healing "
        "potions reserved in the worn pouch."
    ),
    evidence=(
        "DD4 source places one unarmed level-9 vile goblin with a noncombat prisoner in room 4519.",
        "Live run 427 considered the reboot-fuzzed vile goblin an easy kill and returned without combat.",
        "Live run 428 killed it at full health for 322 XP, looted and sacrificed the corpse, and recalled safely.",
        "Live run 432 suffered repeated flee failures and died; one easy kill is not sufficient unattended-safety evidence.",
        "Live run 458 consumed a pouch-held purple potion in combat, confirmed sanctuary, killed the vile goblin for 465 XP, and returned with 112/126 health.",
    ),
    practice_skill="chill touch",
    segment_kill_limit=1,
)

_MORIA_SANCTUARY_LEVEL_NINE_POLICY = ProgressionPolicy(
    policy_id="moria-sanctuary-9-10",
    minimum_level=9,
    maximum_level=10,
    status="verified",
    execution="moria-sanctuary-hunt",
    summary=(
        "Hunt one isolated large hobgoblin for a purple sanctuary potion, "
        "then keep it in the worn pouch for the next protected fight."
    ),
    evidence=(
        "DD4 source places two level-10 large hobgoblins carrying purple sanctuary potions in Moria.",
        "Live run 456 found an isolated reboot-fuzzed level-9 carrier in the expanded circuit, killed it for 505 XP, and stowed the potion in the worn pouch.",
        "Live run 457 completed the same bounded circuit without combat when no eligible carrier was present.",
    ),
    practice_skill="chill touch",
    segment_kill_limit=1,
)

_AMBUSH_VILE_LEVEL_TEN_POLICY = ProgressionPolicy(
    policy_id="ambush-vile-goblin-10-11",
    minimum_level=10,
    maximum_level=11,
    status="verified",
    execution="ambush-vile-hunt",
    summary=(
        "Spend one confirmed pouch-held sanctuary potion on the isolated vile "
        "goblin while progressing from level 10."
    ),
    evidence=(
        "DD4 source places one unarmed source-level-9 vile goblin with a noncombat prisoner in room 4519.",
        "The source level remains inside the productive range at character level 10, subject to the existing live consider gate.",
        "Live runs 458, 477, 480, and 487 verified the sanctuary-protected one-kill loop at level 9.",
        "The level-10 policy preserves the same crowd withdrawal, health retreat, healer recovery, and one-kill limit.",
    ),
    practice_skill="chill touch",
    segment_kill_limit=1,
)

_AMBUSH_RAIDER_LEVEL_TEN_POLICY = ProgressionPolicy(
    policy_id="ambush-goblin-raider-10-11",
    minimum_level=10,
    maximum_level=11,
    status="verified",
    execution="ambush-raider-hunt",
    summary=(
        "Spend one confirmed pouch-held sanctuary potion on the isolated "
        "goblin raider while its reboot-local kill count remains fresh."
    ),
    evidence=(
        "DD4 source places one armed source-level-8 goblin raider with six saleable equipment drops in Ambush room 4506.",
        "Live run 521 found the reboot-fuzzed raider an easy kill while Ararisa was healthier, without initiating combat.",
        "Live run 522 killed the level-8 raider for 368 XP under sanctuary with no hit-point loss, then autolooted and sold its helmet safely.",
        "The route requires full health, an exact isolated target, favorable live consider text, sanctuary, and a one-kill limit because historical unprotected combat was lethal.",
    ),
    practice_skill="chill touch",
    segment_kill_limit=1,
)

_MORIA_SANCTUARY_LEVEL_TEN_POLICY = ProgressionPolicy(
    policy_id="moria-sanctuary-10-11",
    minimum_level=10,
    maximum_level=11,
    status="verified",
    execution="moria-sanctuary-hunt",
    summary=(
        "Acquire one sanctuary potion from an isolated source-level-10 large "
        "hobgoblin before the next protected level-10 fight."
    ),
    evidence=(
        "DD4 source places two source-level-10 large hobgoblins carrying purple sanctuary potions in Moria, an official level 5-15 area.",
        "Live runs 456, 476, 478, and 486 verified the bounded carrier circuit and safe empty-circuit return at level 9.",
        "The target remains level-appropriate at character level 10 and every candidate still passes live consider and crowd gates.",
        "The policy keeps the one-kill limit and explicit inventory synchronization before potion stow.",
    ),
    practice_skill="chill touch",
    segment_kill_limit=1,
)

_MORIA_SANCTUARY_LEVEL_ELEVEN_POLICY = replace(
    _MORIA_SANCTUARY_LEVEL_TEN_POLICY,
    policy_id="moria-sanctuary-11-12",
    minimum_level=11,
    maximum_level=12,
    summary=(
        "Progress from level 11 by hunting one isolated large hobgoblin while "
        "replenishing the protected-combat potion reserve."
    ),
    evidence=(
        *_MORIA_SANCTUARY_LEVEL_TEN_POLICY.evidence,
        "Live run 1503: level-11 Kestrel handled a harmless source-known "
        "level-5 wandering warrior, then admitted only the live-considered "
        "level-9 large hobgoblin.",
        "Run 1503 killed the hobgoblin for 313 XP, acquired and pouched its "
        "purple sanctuary potion, finished at 156/165 hit points, and "
        "recovered fully in healer room 3054 before saving and quitting.",
        "Live run 1506 accepted one source-known equal-level wandering warrior "
        "at full health, withdrew immediately when a second mobile joined, "
        "and recovered fully in healer room 3054 without death or disconnect.",
    ),
)

_MORIA_SANCTUARY_LEVEL_FOURTEEN_THIEF_POLICY = replace(
    _MORIA_SANCTUARY_LEVEL_TEN_POLICY,
    policy_id="moria-sanctuary-thief-14-15",
    minimum_level=14,
    maximum_level=15,
    summary=(
        "Acquire one purple sanctuary potion after an unprotected Rock Toad "
        "fight withdraws or produces only a small net XP gain."
    ),
    evidence=(
        *_MORIA_SANCTUARY_LEVEL_ELEVEN_POLICY.evidence,
        "At thief level 14, source-fuzzed level-10 and level-11 large "
        "hobgoblins remain above the prohibited diff <= -5 consider branches; "
        "a live level-9 carrier is rejected as too low.",
        "Live run 2027 withdrew safely from a level-15 Rock Toad at 46/205 hit "
        "points and netted only 115 XP. Sanctuary halves incoming damage and "
        "the combat runner already quaffs a pouch-held purple potion before "
        "taking avoidable combat damage.",
        "Live run 2028 killed an isolated level-10 large hobgoblin without "
        "losing hit points, gained 354 XP, stowed its purple potion in the worn "
        "pouch, and checkpointed at healer room 3054 with full health and "
        "movement.",
        "Live run 2033 found the room-4064 reset empty, then entered room 4063 "
        "and was attacked by wandering warrior, orc, and poisonous snake "
        "mobiles. The escape and forced trivial kill cost 212 XP before safe "
        "healer recovery. Acquisition now checks only reset room 4064 from "
        "no-mob room 4020 and defers when the carrier has wandered.",
        "Live run 2134 waited 60 seconds outside Moria after area depletion, "
        "then found the source-room carrier respawned in room 4064, killed it "
        "for 332 XP without taking damage, and stowed its purple sanctuary "
        "potion before returning safely to healer room 3054.",
    ),
    practice_skill="backstab",
)

_MORIA_SANCTUARY_THIEF_LEVEL_SEVENTEEN_POLICY = replace(
    _MORIA_SANCTUARY_LEVEL_FOURTEEN_THIEF_POLICY,
    policy_id="moria-sanctuary-thief-17-20",
    minimum_level=17,
    maximum_level=20,
    status="research",
    summary=(
        "Acquire one source-verified purple sanctuary potion as a required "
        "combat-safety reserve after a caster hunt withdraws; this is a "
        "replacement-item pass, not an XP target."
    ),
    evidence=(
        *_MORIA_SANCTUARY_LEVEL_FOURTEEN_THIEF_POLICY.evidence,
        "The High Tower Jailor source mobile is level 17 and the live first "
        "hunt delivered a critical hit and fireball damage before a safe "
        "withdrawal at 11/242 hit points without a sanctuary potion.",
        "The source Moria reset gives purple potion 4050 to large hobgoblin "
        "4055 in room 4064; the carrier is admitted below the XP band only "
        "when the required purple potion is missing.",
    ),
)

_LIQUIDATE_LOOT_POLICY = ProgressionPolicy(
    policy_id="liquidate-loot",
    minimum_level=2,
    maximum_level=None,
    status="verified",
    execution="sell-loot",
    summary="Sell expendable equipment at compatible safe Midgaard shops.",
    evidence=(
        "Live run 323 sold Ambush armour, returned to the Mage Guild, saved, and quit safely.",
        "Current midgaard.are #SHOPS makes the Wizard in safe room 3033 a "
        "buyer for scrolls, wands, staves, and potions, and the grocer in "
        "safe room 3010 a buyer for food. Use those source item types rather "
        "than inferring compatibility from an object's display name.",
        "Live run 2159 sold three Aruncus poison-ivy drops to the General "
        "Store, sold three jhyfrdow scrolls to the Magic Shop, and donated "
        "three unsellable furniture-typed druidic staffs. It reduced carried "
        "items from 37 to 28 and weight from 153 to 138, then saved and quit "
        "safely in healer room 3054.",
    ),
    practice_skill=None,
)

_VAULT_SPARE_GEAR_POLICY = ProgressionPolicy(
    policy_id="vault-spare-gear",
    minimum_level=2,
    maximum_level=None,
    status="verified",
    execution="vault-spare-gear",
    summary="Lodge carried plain armour in the safe Midgaard vault to free hunt capacity.",
    evidence=(
        "The existing source-backed vault workflow uses only safe Midgaard rooms between healer room 3054 and vault room 3007.",
        "Only carried armour without protected stat, combat, recovery, light, or capacity effects is eligible.",
    ),
    practice_skill=None,
)

_BANK_EXCESS_COIN_POLICY = ProgressionPolicy(
    policy_id="bank-excess-coins",
    minimum_level=2,
    maximum_level=None,
    status="verified",
    execution="bank-excess-coins",
    summary=(
        "Deposit a critically encumbering coin hoard and retain one gold coin "
        "as a compact working reserve."
    ),
    evidence=(
        "DD4 source revision d7cb330: calc_coin_weight charges one carry unit per ten individual coins, regardless of denomination.",
        "DD4 source do_deposit accepts `deposit all`, clears carried denominations, and immediately recalculates coin weight.",
        "DD4 source do_withdraw accepts `withdraw 1 gold`; the safe Midgaard bank is room 3007, one east of Market Square.",
        "Live run 2053 started at 161/170 carry weight with 240 individual "
        "coins and incorrectly lodged a silver circlet before banking. Coin "
        "deposit now takes priority whenever fewer than ten weight units remain, "
        "matching the vault-relief threshold and preserving protected gear.",
    ),
    practice_skill=None,
)

_RESTOCK_POLICY = ProgressionPolicy(
    policy_id="restock-provisions",
    minimum_level=2,
    maximum_level=None,
    status="verified",
    execution="restock",
    summary="Fill the water skin and buy a safe food reserve in Midgaard.",
    evidence=(
        "Live run 223 verified the fountain, Bakery, Mage Guild return, save, and safe quit route.",
    ),
    practice_skill=None,
)

_REARM_WEAPON_POLICY = ProgressionPolicy(
    policy_id="rearm-primary-weapon",
    minimum_level=2,
    maximum_level=None,
    status="verified",
    execution="rearm-weapon",
    summary=(
        "Buy, wield, and verify the source-appropriate primary or pounding "
        "weapon at a safe Midgaard shop."
    ),
    evidence=(
        "DD4 source resets object 3020, a one-pound dagger, on the weaponsmith in room 3011.",
        "DD4 source prices the dagger at 10 copper before the weaponsmith's reboot-fuzzy markup.",
        "DD4 source resets object 3352, a standard mace, at Dave the Dealer in room 3120; source-supported stun users retain it separately from their normal primary.",
        "The route between healer room 3054 and Weapon Shop room 3011 uses only safe Midgaard rooms.",
    ),
    practice_skill=None,
)

_OUTFIT_BASIC_GEAR_POLICY = ProgressionPolicy(
    policy_id="outfit-basic-gear",
    minimum_level=2,
    maximum_level=None,
    status="verified",
    execution="outfit-basic-gear",
    summary="Fill empty legal armour slots with inexpensive Midgaard basics.",
    evidence=(
        "DD4 source resets leather body, head, arm, hand, leg, foot, and pouch basics on the leather worker in room 3035.",
        "The route between healer room 3054 and Leather Shop room 3035 uses only safe Midgaard rooms.",
        "The workflow audits eq all and buys only basics for profession-visible empty slots.",
    ),
    practice_skill=None,
)

_RECOVER_BASIC_BODY_POLICY = ProgressionPolicy(
    policy_id="recover-basic-body-gear",
    minimum_level=2,
    maximum_level=None,
    status="verified",
    execution="recover-basic-body",
    summary="Recover a lightweight body basic from a registered low-risk carrier.",
    evidence=(
        "DD4 source equips level-3 sentinel Oshu in Foundry room 110 with object 104, a seven-pound leather jerkin.",
        "Oshu is one east from the official Foundry fastwalk endpoint in room 109.",
        "This is a one-kill required-loot action; below-band targets remain forbidden for XP progression.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)

_RECOVER_SCHOOL_WRIST_FLOAT_POLICY = ProgressionPolicy(
    policy_id="recover-school-wrist-float",
    minimum_level=2,
    maximum_level=None,
    status="verified",
    execution="recover-school-wrist-float",
    summary="Fill empty wrist and floating slots from low-risk Mud School carriers.",
    evidence=(
        "DD4 school.are equips the level-2 lizardman in room 3720 with object 3713, a copper bracer.",
        "DD4 school.are equips the level-1 gladiator in room 3722 with another copper bracer and object 3721, a wisdom-boosting snowy white floating stone.",
        "The route begins at Midgaard recall, passes only tutorial rooms, and recalls after the two bounded required-loot kills.",
    ),
    practice_skill=None,
    segment_kill_limit=2,
)

_RECOVER_GREMLIN_WAIST_POLICY = ProgressionPolicy(
    policy_id="recover-gremlin-waist",
    minimum_level=2,
    maximum_level=None,
    status="verified",
    execution="recover-gremlin-waist",
    summary="Fill an empty waist slot from a low-risk baby gremlin.",
    evidence=(
        "DD4 gremlinlair.are gives the level-2 baby gremlin in room 134 object 135, a waist-slot diaper.",
        "The source-backed route reaches room 134 directly from Midgaard recall and permits immediate recall after looting.",
        "This is a one-kill required-loot action; below-band targets remain forbidden for XP progression.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)

_RECOVER_DAYCARE_RING_POLICY = ProgressionPolicy(
    policy_id="recover-daycare-ring",
    minimum_level=2,
    maximum_level=None,
    status="verified",
    execution="recover-daycare-ring",
    summary="Fill both finger slots and restore nearby stat-bearing bodywear.",
    evidence=(
        "DD4 daycare.are equips the level-1 old doll in room 6605 with object 6601, a pink ice ring granting +1 strength and +6 hit points.",
        "Only the room-6605 old-doll reset equips the ring. A same-vnum doll "
        "loads without a ring in room 6604 and can wander into 6605, so an "
        "empty corpse is a bounded failed drop rather than evidence that the "
        "ring prototype or recovery route is wrong.",
        "Live run 2107 killed the non-carrier after it wandered into room 6605, "
        "found an empty corpse, and safely activated the three-productive-segment "
        "retry cooldown.",
        "The same route returns through room 6602, where the old wrinkled nanny carries a linen robe granting wisdom and mana.",
        "The old doll is reached two rooms beyond the verified Dwarven Daycare route; other source resets in the room are low-level non-aggressive dolls and youths.",
        "These are three bounded required-loot kills; below-band targets remain forbidden for XP progression.",
        "Live run 1730: a room-6602 nanny cast blindness during a ring-recovery pass; the runner fled, recalled, and waited at the Midgaard healer without dying. Treat blindness as a terminal recovery condition for the remaining pass.",
        "Live run 1739: one old doll and the live-considered nanny yielded four recovery items, 444 XP, and a safe level-6 transition; the following generic segment liquidated compatible loot in Midgaard.",
        "Live run 2042 found both old dolls wandering through transit room 6603 "
        "while reset room 6605 was empty. Inspect each doll independently in "
        "6603 before continuing south, then retain two independent 6605 checks.",
        "Live run 2121 found no eligible ring carrier, killed only the "
        "source-registered nanny, and returned safely. The generic stance "
        "planner equipped her linen robe, raising modified wisdom from 16 to "
        "17 and maximum mana from 215 to 220 without changing damroll.",
        "Live run 2135 killed the room-6605 carrier and equipped Kestrel's "
        "second pink ice ring. Maximum hit points rose from 217 to 224, "
        "modified strength rose to 17, damroll rose from 4 to 5, and the "
        "carry limit rose from 250 to 300.",
    ),
    practice_skill=None,
    segment_kill_limit=3,
)

_RECOVER_WAR_DOG_COLLAR_POLICY = ProgressionPolicy(
    policy_id="recover-war-dog-collar",
    minimum_level=6,
    maximum_level=None,
    status="verified",
    execution="recover-war-dog-collar",
    summary="Fill one empty neck slot with a low-risk +1 damroll collar.",
    evidence=(
        "DD4 ambush.are resets mobile 4504, the source-level-6 war dog, in room 4505 with object 4538, a war dog collar.",
        "Object 4538 is neck-slot gear with apply 19 (+1 damroll); DD4 merc.h defines apply 19 as damroll.",
        "The registered Ambush fastwalk reaches the isolated carrier through the verified exterior route and recalls after one required-loot kill.",
        "This is a bounded required-loot action; below-band targets remain forbidden for XP progression.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)

_RECOVER_FOUNDRY_SET_CIRCLET_POLICY = ProgressionPolicy(
    policy_id="recover-foundry-set-circlet",
    minimum_level=6,
    maximum_level=None,
    status="verified",
    execution="recover-foundry-set-circlet",
    summary=(
        "Pair a carried pink ice ring with the Foundry silver circlet for a "
        "+2 strength set bonus."
    ),
    evidence=(
        "DD4 sets.are pairs object 108, the Foundry silver circlet, with object "
        "6601, the Dwarven Daycare pink ice ring, and applies +2 strength.",
        "Live run 2016 equipped the pair and raised Kestrel's current strength "
        "from 14 to 16 and carry capacity from 170 to 250.",
        "The same live evidence showed no intelligence increase, so this item "
        "must not be used as a trainer-penalty workaround.",
        "The existing Foundry fastwalk reaches room 109; the registered search "
        "covers every open main-corridor room while excluding the captain, "
        "Oshu, Hoobuk's closed pen, and the poison-bearing pit beast.",
        "This is one bounded required-loot kill. The carrier is deliberately "
        "below-band and is never treated as an XP target.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)

_FOREST_BEAR_CLAWS_UPGRADE_POLICY = ProgressionPolicy(
    policy_id="forest-bear-claws-upgrade-10-29",
    minimum_level=10,
    maximum_level=29,
    status="research",
    execution="upgrade-piercing-weapon",
    summary=(
        "Acquire the Forest kodiak's piercing bear claws when the character's "
        "current backstab-capable weapon is materially weaker."
    ),
    evidence=(
        "DD4 forest.are resets mobile 18001, a level-10 Giant Kodiak bear, in room 18026.",
        "The same reset equips object 18000, a 6d12 piercing weapon with +3 hit roll.",
        "The source-derived route from Midgaard recall reaches room 18026 through Ambush and the Forest without a required combat stop.",
        "DD4 act_move.c and the route room sectors total 236 movement without flight; the policy requires 246 available movement to retain a one-step emergency margin.",
        "The bear is aggressive, wandering, and reset-fuzzy, so live consider, crowd rejection, a live-level ceiling, sufficient movement or flight, and safe-abort handling remain mandatory.",
        "Live run 1521 traversed the full route under flight with 168/250 movement remaining, but found the bear absent from reset room 18026.",
        "DD4 source revision f703daa confirms the bear is stay-area but not sentinel; the bounded search extends through reversible adjacent rooms 18025, 18023, 18024, and 18022.",
        "The one-way eastern slope from room 18027 is excluded because it leads toward aggressive mosquito and wasp resets.",
        "Live run 2014 traversed all 50 source-vetted Forest rooms while excluding "
        "the poison-swarm branch, medicine man's lair, and adjacent-area exits. "
        "The wandering bear was absent throughout, and Kestrel returned safely "
        "to healer room 3054 after 319 bounded commands.",
        "Live run 2048 repeated the safe exhaustive search but spent about 290 "
        "seconds on another globally absent bear. The route now issues `where "
        "kodiak` at the reset room and recalls immediately only when the source "
        "`do_where` absence response confirms no matching mobile in the area.",
        "Live run 2110 showed level-15 Kestrel still using a source-matched "
        "plain dagger with materially lower damage while a Rock Toad required "
        "a long scratch-and-graze fight. The source-legal upgrade remains useful "
        "through the pre-subclass band, so bounded retries continue through "
        "level 29 rather than stopping at level 14.",
        "Live run 2112 proved the extended policy is selected at level 15. "
        "`where kodiak` found the bear in a River bed room on the excluded "
        "mosquito-and-wasp branch, so Kestrel declined the unsafe pursuit, "
        "recalled, and recovered fully with flight still active.",
        "Live run 2137 repeated the exact River bed result after flight "
        "restocking. Kestrel again declined the excluded branch, recalled, "
        "checkpointed at level 15, and exited cleanly.",
        "Live runs 2153 and 2157 again located the bear in the excluded River "
        "bed and returned safely. Run 2163 received only the ambiguous area "
        "label `Forest`, searched all vetted rooms for about three minutes, "
        "and returned with zero XP. Delay another attempt until six productive "
        "field segments complete; maintenance segments do not count.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)

_THALOS_LONG_DAGGER_UPGRADE_POLICY = ProgressionPolicy(
    policy_id="thalos-long-dagger-upgrade-10-29",
    minimum_level=10,
    maximum_level=29,
    status="research",
    execution="upgrade-piercing-weapon",
    summary=(
        "Acquire a reliable intermediate piercing weapon from an isolated "
        "Old Thalos lamia before continuing the rarer Forest upgrade."
    ),
    evidence=(
        "DD4 source revision d7cb330 defines object 5252 as a 2d5 piercing "
        "long slim dagger with +1 hitroll and +1 damroll.",
        "Twenty source-level-9 lamia resets carry object 5252 in Old Thalos; "
        "the nearest carrier resets alone in room 5203.",
        "The official Thalos fastwalk reaches room 5200. Rooms 5201 and 5202 "
        "are empty transit rooms, followed by three reversible westward moves "
        "to the isolated carrier.",
        "Lamia mobile 5201 is aggressive and stay-area but has no special "
        "procedure. The required-loot action remains exact-target, live-"
        "consider gated, crowd gated, and capped at one kill.",
        "The intermediate tier has an independent three-productive-segment "
        "retry cooldown, so it can run while the rarer Forest tier is cooling "
        "down without becoming an immediate retry loop of its own.",
        "Live run 2127 verified the official route and the first three source "
        "room transitions, but all three carriers had wandered. The corrected "
        "route issues `where lamia` and searches fourteen lamia-only reset rooms "
        "without crossing any room containing a different static mobile.",
        "Live run 2128 found a wandering lamia at the fifth registered stop, "
        "survived one disarm by recovering the dropped weapon, killed the "
        "carrier without taking damage, looted object 5252, and replaced the "
        "plain dagger. Live damroll rose from 3 to 4; hitroll gained the "
        "dagger's +1 in addition to the healer's active bless.",
        "In live runs 2129 and 2130, the upgraded Kestrel killed level-15 Rock "
        "Toads in 69.9 and 73.8 seconds, finishing at 212/217 and 194/217 hit "
        "points. The preceding three plain-dagger kills took 104.1, 92.1, and "
        "90.0 seconds; treat these two upgraded samples as encouraging "
        "throughput evidence, not a stable causal speedup.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)

_BUY_FLIGHT_POLICY = ProgressionPolicy(
    policy_id="buy-flight-potion",
    minimum_level=5,
    maximum_level=None,
    status="verified",
    execution="buy-flight",
    summary=(
        "Check the current Magic Shop price, buy one light blue potion, and "
        "verify flight before a movement-heavy field route."
    ),
    evidence=(
        "Live run 96 bought the reboot-priced light blue potion for 123 copper and confirmed flight.",
        "Live run 437 bought the same potion for 94 copper after becoming visible and verifying the purchase.",
        "Live run 1113 bought the potion for 534 copper on reboot Mon Jul 20 06:53:03 2026 and confirmed the fly affect before Dorrik's martial field rotation.",
        "Live run 1128 rechecked the shop, bought the currently listed 94-copper potion, and confirmed the fly affect before the level-nine Ambush sweep.",
        "The workflow checks current stock and affordability instead of assuming a fixed reboot price.",
        "DD4 fight.c suppresses NPC trip attempts against flying, fly-affected, or levitating targets.",
    ),
    practice_skill=None,
)

_UNAVAILABLE_POLICY = ProgressionPolicy(
    policy_id="unregistered-10-100",
    minimum_level=10,
    maximum_level=None,
    status="unavailable",
    execution=None,
    summary="No evidence-backed route, combat loop, or recovery plan has been registered.",
    evidence=(),
    practice_skill=None,
)


_PLAINS_ARUNCUS_LEVEL_TWELVE_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="plains-aruncus-probe-12-13",
    minimum_level=12,
    maximum_level=13,
    status="research",
    execution="plains-aruncus-research",
    summary=(
        "After an empty level-12 Fleshmonger segment, consider the non-aggressive "
        "Plains druid Aruncus without initiating combat."
    ),
    evidence=(
        "DD4 source revision d7cb330: mobile 300, Aruncus the Druid, resets once "
        "in Plains of the North room 323.",
        "His source level is 13 with normal mobile-level fuzz; his act flags are "
        "stay-area and wimpy, not aggressive or sentinel, and he has no special procedure.",
        "The source-derived route reaches room 323 from healer room 3054 and returns "
        "by recall; its exact-keyword probe tolerates a wandering or absent target.",
        "This probe replaces the retired Moria sanctuary-carrier research route: live "
        "run 1606 proved that the carrier room can begin automatic combat before "
        "consideration, costing a safe flee 101 net XP.",
        "Live run 1607 reached the route endpoint at level 12, found Aruncus absent, "
        "and returned to healer room 3054 without combat, damage, or XP loss.",
    ),
    practice_skill=None,
)


_AMBUSH_BARDOOSH_LEVEL_TWELVE_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="ambush-bardoosh-probe-12-13",
    minimum_level=12,
    maximum_level=13,
    status="retired",
    execution=None,
    summary=(
        "Retired: the apparent Bardoosh probe cannot guarantee a no-combat Ambush "
        "approach because incidental mobile combat can occur en route."
    ),
    evidence=(
        "DD4 source revision d7cb330: mobile 4515, Bardoosh, resets once in Ambush "
        "room 4514 after the isolated goblin archer room.",
        "Bardoosh has source level 12, sentinel rather than aggressive act flags, "
        "the sleep affect, and no special procedure.",
        "The exact source keyword is bardoosh; the reset equips armour, shield, "
        "spear, gauntlets, sleeves, girdle, and a ring, so any later kill policy "
        "must retain strict capacity and sale handling.",
        "Live run 1612 encountered and killed an incidental goblin lieutenant and "
        "goblin for 120 XP before safe healer recovery, so the route is not valid "
        "for a no-combat research policy.",
    ),
    practice_skill=None,
)


_AMBUSH_BARDOOSH_THIEF_KILL_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="ambush-bardoosh-thief-kill-research-13",
    minimum_level=13,
    maximum_level=13,
    status="research",
    execution="ambush-bardoosh-hunt",
    summary=(
        "Live-consider and attack isolated Bardoosh after repeated Aruncus "
        "kills have reduced the current-reboot XP return."
    ),
    evidence=(
        "DD4 source revision d7cb330: mobile 4515, Bardoosh, is a source-level-12 "
        "sentinel reset alone in Ambush room 4514 with no special procedure.",
        "Bardoosh begins under the sleep affect and carries a complete hard-leather "
        "set, shield, spear, girdle, gauntlets, and ring; strict capacity and "
        "post-fight liquidation remain required.",
        "Live run 1612 traversed the same route and safely finished incidental "
        "level-6/7 goblins. At level 13 those source-backed wanderers are below "
        "the useful XP band and cannot invalidate an isolated Bardoosh decision.",
        "Live run 1899 finished a level-6 mountain goblin, then fled a lone "
        "level-7 goblin lieutenant because a non-aggressive level-8 wyvern was "
        "visible. Source revision d7cb330 proves the wyvern has no aggressive "
        "flag, so revision 77 allows it as a bystander.",
        "Live run 1900 proved the old final `south` command stopped in archer "
        "room 4515. Source reset and exit evidence place Bardoosh in adjacent "
        "room 4514 via `west`; revision 78 corrects and retries that route once.",
        "Live run 1901 reached room 4514 and saw Bardoosh's generic live line "
        "`A goblin is here sleeping.` at selector #3095. Revision 79 binds that "
        "line to the source mobile's proper short name for exact targeting.",
        "Live run 1902 considered Bardoosh a perfect match and attacked the exact "
        "selector. Kestrel withdrew safely at 40/194 HP after three successful "
        "automatic dagger recoveries; partial-combat XP 257 less the 132-XP flee "
        "cost yielded 125 net XP but no kill, so the policy remains research-only "
        "and rotates back to Aruncus.",
        "This first combat pass retains exact TARGETMODE identity, live consider, "
        "a 90% departure-health gate, a +1 live-level ceiling, normal crowd "
        "checks, and bounded field withdrawal.",
    ),
    practice_skill="backstab",
    segment_kill_limit=1,
)


_AMBUSH_BARDOOSH_LEVEL_FOURTEEN_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="ambush-bardoosh-thief-kill-research-14",
    minimum_level=14,
    maximum_level=14,
    status="retired",
    execution=None,
    summary=(
        "Retired: Kestrel's level-14 dagger rotation could not overcome "
        "Bardoosh's defense and repeated disarms."
    ),
    evidence=(
        *_AMBUSH_BARDOOSH_THIEF_KILL_RESEARCH_POLICY.evidence,
        "The level-13 bounded attempt reached exact Bardoosh combat and withdrew "
        "safely without a kill. A level-14 retry retains the same source-backed "
        "identity, live consider, crowd, target-level, capacity, and withdrawal "
        "gates while testing the stronger character state.",
        "Live run 2006 found Bardoosh at level 12 with 220 hit points and received "
        "the easy-kill consider branch. Six disarms and a 60-second damage plateau "
        "left him at 191 hit points; the safe withdrawal produced 73 partial XP "
        "against a 148-XP flee cost, for a net loss of 75 XP.",
        "The failure was damage throughput rather than reboot-specific target "
        "availability, so the policy remains retired until a materially stronger "
        "weapon and combat rotation are verified.",
    ),
    practice_skill="backstab",
    segment_kill_limit=1,
)


_AMBUSH_BARDOOSH_THIEF_LEVEL_SIXTEEN_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="ambush-bardoosh-thief-kill-research-16",
    minimum_level=16,
    maximum_level=16,
    status="research",
    execution="ambush-bardoosh-hunt",
    summary=(
        "Use the source-vetted Bardoosh route for one bounded backstab-enabled "
        "fight after the level-16 Rock Toad circuit is empty."
    ),
    evidence=(
        *_AMBUSH_BARDOOSH_LEVEL_FOURTEEN_RESEARCH_POLICY.evidence,
        "The earlier retirement explicitly required backstab or materially stronger equipment before another attempt. The generic thief path now prioritizes backstab at the level-10 trainer and the piercing-weapon maintenance path upgrades the starter dagger.",
        "This level-16 retry runs only after an empty Rock Toad segment, retains exact TARGETMODE identity, live consider, sole-target, 90% health, +1 live-level, recurring damage-action, disarm recovery, and healer-return gates, and is attempted at most once before returning to the Toad reset controller.",
        "Live run 2209 killed live-level-12 Bardoosh for 535 XP with repeated knife attacks and automatic long slim dagger recovery. Kestrel took no damage, returned with three saleable drops, slept to full health and movement in healer room 3054, then saved and quit.",
    ),
    practice_skill="backstab",
    segment_kill_limit=1,
)


_AMBUSH_BARDOOSH_THIEF_LEVEL_SIXTEEN_HUNT_POLICY = ProgressionPolicy(
    policy_id="ambush-bardoosh-thief-hunt-16",
    minimum_level=16,
    maximum_level=16,
    status="verified",
    execution="ambush-bardoosh-hunt",
    summary=(
        "Alternate one source-vetted Bardoosh kill after productive Rock Toad "
        "work has allowed the Ambush reset time outside the area."
    ),
    evidence=(
        *_AMBUSH_BARDOOSH_THIEF_LEVEL_SIXTEEN_RESEARCH_POLICY.evidence,
        "Run 2209 satisfies the reusable promotion gates: a confirmed exact-target kill, positive 535-XP return, no player damage, automatic recovery from every disarm, source-approved loot, and a full healer-room checkpoint.",
        "The verified hunt is selected only after a productive Rock Toad segment and always rotates back to Mahn-Tor after its own pass. This gives the sentinel reset time outside Ambush and prevents immediate Bardoosh retries.",
        "Live run 2217 proved autonomous promotion from the productive 395-XP Toad run 2215, across intervening flight and weapon-upgrade maintenance. The planner selected this verified hunt, killed live-level-12 Bardoosh for 474 XP without player damage, recovered three source-approved drops, and returned safely to healer room 3054.",
        "Live runs 2224 and 2225 found three Rock Toads crowded together and correctly declined combat, but exposed an immediate zero-XP circuit repeat. The selector now rotates such a non-actionable Toad pass to this hunt only while its latest verified result remains productive.",
        "Live run 2226 proved that corrected transition: Kestrel killed Bardoosh for 517 XP, recovered the three registered drops, and returned to healer room 3054 at full health. A zero-XP verified Bardoosh result still blocks another Bardoosh retry.",
    ),
    practice_skill="backstab",
    segment_kill_limit=1,
)


_AMBUSH_BARDOOSH_THIEF_LEVEL_SEVENTEEN_RESEARCH_POLICY = replace(
    _AMBUSH_BARDOOSH_THIEF_LEVEL_SIXTEEN_RESEARCH_POLICY,
    policy_id="ambush-bardoosh-thief-kill-research-17-18",
    minimum_level=17,
    maximum_level=18,
    summary=(
        "Reconsider the source-vetted Bardoosh route at thief levels 17-18 "
        "when the higher-band probes and the Toad fallback are unproductive."
    ),
    evidence=(
        *_AMBUSH_BARDOOSH_THIEF_LEVEL_SIXTEEN_RESEARCH_POLICY.evidence,
        "The source-level-12 Bardoosh has a normal live range of levels 10-14. "
        "At thief level 18 its highest possible roll is four levels below the "
        "player, so it remains above DD4's prohibited `diff <= -5` XP branch; "
        "every live attempt still rejects the forbidden consider responses.",
        "This separate policy ID forces a fresh same-reboot consider result "
        "after the level-16 evidence rather than carrying a stale target roll "
        "into the level-17/18 band.",
    ),
)


_AMBUSH_BARDOOSH_THIEF_LEVEL_SEVENTEEN_HUNT_POLICY = replace(
    _AMBUSH_BARDOOSH_THIEF_LEVEL_SIXTEEN_HUNT_POLICY,
    policy_id="ambush-bardoosh-thief-hunt-17-18",
    minimum_level=17,
    maximum_level=18,
    summary=(
        "Use one fresh, exact Bardoosh kill to bridge a depleted level-18 "
        "thief campaign toward the level-19 watchman band."
    ),
    evidence=(
        *_AMBUSH_BARDOOSH_THIEF_LEVEL_SIXTEEN_HUNT_POLICY.evidence,
        "The hunt remains a one-kill transition policy. After either a "
        "successful or zero-XP pass it rotates back to the Toad policy so "
        "the Ambush reset can repopulate and the route cannot loop blindly.",
    ),
)


_PLAINS_ARUNCUS_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="plains-aruncus-probe-13-15",
    minimum_level=13,
    maximum_level=15,
    status="research",
    execution="plains-aruncus-research",
    summary=(
        "Consider the Plains of the North druid Aruncus without initiating "
        "combat, then return to the Midgaard healer."
    ),
    evidence=(
        "DD4 source revision d7cb330: mobile 300, Aruncus the Druid, resets once in Plains of the North room 323.",
        "His source level is 13 with normal mobile-level fuzz; his act flags are stay-area and wimpy, not aggressive or sentinel.",
        "Aruncus has no special procedure, but can wander within the area, so the exact-keyword live probe must tolerate an absent target and cannot promote a combat policy.",
        "The source room graph permits a non-hostile 323 -> 324 -> 322 -> 330 foothill loop; the probe issues `where aruncus` before checking each room.",
        "Live runs 1637, 1641, and 1643 found Aruncus wandering through the source-named Dark smelly tunnels, Stones of G'harne, and room 337 on the preceding ancient path. The extension inspects every source-verified room from 322 through 343, travels through rooms carrying at most rabbits, and stops before room 344, whose level-24 giant worm reset is unsafe for this band.",
        "Live run 1881 located Aruncus in a `Grassy plains` room while the older "
        "route missed that source-connected branch. The expanded GMCP-guided "
        "search covers rooms 300-327 and 330-343 while excluding one-way room "
        "345, the pool branch, external-area exits, and dangerous room 344.",
        "Live run 1883 validated the expanded source route but a single linear "
        "pass still missed Aruncus while `where` continued to report Grassy "
        "plains. The bounded route now makes three short grassy-room circuits "
        "and refreshes `where` at room 323 between them before searching the "
        "remaining safe branch.",
        "The source-derived route reaches room 323 from healer room 3054 and returns by recall; this policy records the live reboot, crowd, target presence, and do_consider result only.",
        "Live run 1607 verified the level-12 route endpoint and safe healer return while Aruncus was absent in this reboot window.",
    ),
    practice_skill=None,
)


_PLAINS_ARUNCUS_THIEF_KILL_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="plains-aruncus-thief-kill-research-13-15",
    minimum_level=13,
    maximum_level=15,
    status="retired",
    execution=None,
    summary=(
        "Retired exact-level Aruncus probe: it could only discover normal "
        "source fuzz after paying an avoidable flee penalty."
    ),
    evidence=(
        *_PLAINS_ARUNCUS_RESEARCH_POLICY.evidence,
        "Live run 1645 found Aruncus in room 333, used exact selector #147, and received `The perfect match! However, you are a teensy bit healthier than he.`",
        "DD4 act_info.c maps `The perfect match!` to level difference <= 1; with both live character and source mobile level 13, this is the exact-level branch rather than a below-band branch.",
        "Live run 1647 found the same source mobile at live level 14 after `consider` said perfect match. The live ceiling gate fled immediately unharmed but cost 132 XP, proving that no pre-combat source or consider signal can safely enforce the exact-level restriction.",
        "DD4 db.c fuzzes the loaded prototype level and fuzzes it again in create_mobile. This target remains evidence-only until the range-aware v2 probe has gathered a live bounded result.",
    ),
    practice_skill="backstab",
    segment_kill_limit=1,
)


_PLAINS_ARUNCUS_THIEF_KILL_RESEARCH_V2_POLICY = ProgressionPolicy(
    policy_id="plains-aruncus-thief-kill-research-v2-13-15",
    minimum_level=13,
    maximum_level=15,
    status="retired",
    execution=None,
    summary=(
        "Retired source-fuzz probe: the initial exact-target range lookup still "
        "merged generic source keywords and therefore skipped safe combat."
    ),
    evidence=(
        *_PLAINS_ARUNCUS_THIEF_KILL_RESEARCH_POLICY.evidence,
        "Run 1648 found Aruncus in room 337 and received the perfect-match consider branch, but its source lookup merged the unrelated generic `druid` key and conservatively skipped combat as range 8-53.",
        "The parser correction requires exact source identities for exact-target stops. The v3 result must remain distinct from the v2 safe no-combat result.",
    ),
    practice_skill="backstab",
    segment_kill_limit=1,
)


_PLAINS_ARUNCUS_THIEF_KILL_RESEARCH_V3_POLICY = ProgressionPolicy(
    policy_id="plains-aruncus-thief-kill-research-v3-13-15",
    minimum_level=13,
    maximum_level=15,
    status="retired",
    execution=None,
    summary=(
        "Retired one-kill probe: Aruncus's source wimpy behavior made the "
        "evidenced fight an unsafe, zero-XP chase rather than a field circuit."
    ),
    evidence=(
        *_PLAINS_ARUNCUS_THIEF_KILL_RESEARCH_V2_POLICY.evidence,
        "The exact-target source-range gate now resolves only `Aruncus the Druid` to its 11-15 range, rather than merging generic source `druid` entries.",
        "Live run 1649 found Aruncus in room 337, considered and attacked from 194/194 HP, then reduced him to a fleeing state at 128/194 HP. The bot did not pursue into the next room and returned to healer room 3054 at full recovery with no XP gain.",
        "The source act flags mark Aruncus wimpy. Do not promote a mobile that must be chased after a long fight into a repeatable level-13 XP loop; use the verified Fleshmonger rotation instead.",
    ),
    practice_skill="backstab",
    segment_kill_limit=1,
)


_PLAINS_ARUNCUS_THIEF_PURSUIT_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="plains-aruncus-thief-pursuit-research-13-15",
    minimum_level=13,
    maximum_level=15,
    status="research",
    execution="plains-aruncus-hunt",
    summary=(
        "Re-test the viable Aruncus fight with bounded pursuit restricted to "
        "source-vetted foothill, ancient-path, and tunnel rooms."
    ),
    evidence=(
        *_PLAINS_ARUNCUS_THIEF_KILL_RESEARCH_V3_POLICY.evidence,
        "The current field runner can follow the requested target for at most three "
        "observed flee steps, re-checking the destination room before re-engaging.",
        "The pursuit allowlist covers source rooms 309-312, 322-326, 330, and "
        "332-343, including empty dead-end room 341, but excludes room 344 and "
        "its source-level-24 Shudde-M'ell reset.",
        "Any flee direction whose live GMCP destination is absent from that "
        "allowlist aborts the chase and recalls to healer room 3054.",
    ),
    practice_skill="backstab",
    segment_kill_limit=1,
)


_PLAINS_ARUNCUS_THIEF_HUNT_POLICY = ProgressionPolicy(
    policy_id="plains-aruncus-thief-hunt-13-15",
    minimum_level=13,
    maximum_level=15,
    status="verified",
    execution="plains-aruncus-hunt",
    summary=(
        "Find, consider, and kill Aruncus with bounded source-room pursuit, then "
        "loot and recover at the Midgaard healer."
    ),
    evidence=(
        *_PLAINS_ARUNCUS_THIEF_PURSUIT_RESEARCH_POLICY.evidence,
        "Live run 1879 found Aruncus as exact selector #147, received the "
        "perfect-match consider branch, and killed him from full 194 HP.",
        "The kill awarded 866 XP, including 598 kill XP and 268 damage XP; "
        "Kestrel finished at 133/194 HP without a disabling affect.",
        "Run 1879 looted the corpse, recalled, and checkpointed safely in healer "
        "room 3054 with full mana and movement and no manual gameplay command.",
        "Live run 2037 repeatedly confirmed `where aruncus` as `Hermit's hut` "
        "while the older outdoor-first circuit exhausted its movement reserve. "
        "Source room 323 leads south to 330, whose unlocked west door enters "
        "safe room 331; check that hut immediately after the reset room.",
        "Live run 2041 opened and traversed the hut door successfully, then "
        "live-considered a wandering Aruncus in room 318, pursued one safe "
        "southward flee, and killed him for 541 XP.",
        "Kestrel finished at 187/205 HP, looted the source reset items, "
        "recalled, and checkpointed in healer room 3054. No recurring active "
        "attack was available because level-14 trainer evidence caps Stealth "
        "Techniques at 56%, below backstab's 60% prerequisite.",
        "Live run 2044 exercised the exact hut-present case: `where aruncus` "
        "reported Hermit's Hut, the route checked room 331 immediately, and "
        "Sorbus did not block the exact Aruncus selector. Kestrel killed "
        "Aruncus for 538 XP and safely saved and quit in healer room 3054.",
        "Live run 2045 immediately repeated that successful single-reset hunt, "
        "spent 320 commands searching an empty circuit, and returned safely "
        "with zero XP. After a successful Aruncus kill, rotate to a viable "
        "outside-area policy before retrying him.",
        "Live run 2047 proved persisted GMCP inventory descriptions can retain "
        "ephemeral `[#number]` object selectors. Stripping that prefix restored "
        "source recognition of Aruncus's no-drop amulet, triggered liquidation, "
        "used healer remove-curse, destroyed the amulet, and safely disposed of "
        "the scroll and staff before quitting in room 3054.",
        "Live runs 2062, 2068, and 2072 killed Aruncus for 469, 629, and 438 "
        "XP respectively and returned safely to healer room 3054. Run 2062 "
        "also showed that a wandering target can be visible in a vetted "
        "circuit room before its configured destination step.",
        "Live run 2150 disabled autoloot before combat, killed live-level-14 "
        "Aruncus for 568 XP, and manually collected only object 308 `staff`, "
        "object 312 `scroll`, and object 302 `ivy`. Object 307, the no-drop "
        "strange amulet, remained in the corpse; Kestrel's 15 gold was "
        "unchanged because no curse healing was needed. The run sacrificed "
        "the corpse, restored autoloot in healer room 3054, saved, and quit.",
        "Live run 2154 repeated the policy against a wandering Aruncus in "
        "source room 318, earned 325 XP, collected the same three approved "
        "drops, restored autoloot, and checkpointed safely. The repeat proves "
        "the behavior is reusable rather than tied to one selector or room.",
    ),
    practice_skill="backstab",
    segment_kill_limit=1,
)


_PLAINS_ARUNCUS_THIEF_LEVEL_SEVENTEEN_FALLBACK_POLICY = replace(
    _PLAINS_ARUNCUS_THIEF_HUNT_POLICY,
    policy_id="plains-aruncus-thief-fallback-17-18",
    minimum_level=17,
    maximum_level=18,
    summary=(
        "Rotate from Mahn-Tor to the verified Aruncus hunt so the Rock Toad "
        "resets can repopulate without spending consecutive segments in one "
        "depleted area."
    ),
    evidence=(
        *_PLAINS_ARUNCUS_THIEF_HUNT_POLICY.evidence,
        "Aruncus's source-backed 11-15 live range overlaps the useful XP band "
        "at thief levels 17 and 18. The existing exact-selector consider gate "
        "rejects every fuzzed instance that reaches the prohibited `diff <= "
        "-5` or `diff <= -10` branches.",
        "This alternate retains the verified selective-loot workflow: disable "
        "autoloot, collect only the source-approved staff, scroll, and ivy, "
        "and leave object 307, the no-drop strange amulet, in the corpse.",
        "Live run 2281 proved the level-17 alternate end to end. Kestrel "
        "accepted an exact live Aruncus after `consider`, pursued one northward "
        "flee, killed him for 612 XP without taking damage, collected only the "
        "three approved drops, left the cursed amulet behind, restored "
        "autoloot, and saved and quit in healer room 3054. The productive "
        "outside-area segment reset the campaign stall counter and advanced "
        "the higher-band absence cooldowns.",
    ),
)


_DWARVEN_WORKERS_THIEF_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="dwarven-workers-thief-probe-13-15",
    minimum_level=13,
    maximum_level=15,
    status="research",
    execution="dwarven-workers-research",
    summary=(
        "Consider the three non-aggressive dwarven worker resets along the "
        "short mountain approach without initiating combat."
    ),
    evidence=(
        "DD4 dwarven.are resets one source-level-12 worker in each of rooms "
        "6501, 6502, and 6503; the workers have no special procedure but do "
        "have the accelerated-regeneration act flag.",
        "The source route from recall is 2s6edn and reaches the first worker "
        "room without a locked door or required combat.",
        "Each worker carries a mining pick. A three-stop circuit can provide "
        "both useful-band XP and weapon-shop loot if live consideration is viable.",
        "The first pass considers exact source identities only and rejects a "
        "room containing duplicate workers or any unknown bystander.",
        "Source reachability limits wandering workers to twelve rooms. The "
        "survey covers all eleven safely reversible rooms and excludes 6505, "
        "whose locked reverse exit could strand the character.",
        "Live run 2022 found two exact workers and received the perfect-match "
        "consider branch for both. One was isolated in room 6522; the other "
        "shared room 6509 with two source-level-20 guards.",
    ),
    practice_skill="backstab",
)


_DWARVEN_WORKERS_THIEF_HUNT_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="dwarven-workers-thief-kill-research-13-15",
    minimum_level=13,
    maximum_level=15,
    status="retired",
    execution=None,
    summary=(
        "Retired: a wandering source-level-16 giant can join an apparently "
        "isolated worker fight from an adjacent room."
    ),
    evidence=(
        *_DWARVEN_WORKERS_THIEF_RESEARCH_POLICY.evidence,
        "Combat requires a same-reboot viable probe, exact target-mode identity, "
        "a +1 live-level ceiling, one worker in the room, and normal health, "
        "capacity, hunger, thirst, and disabling-affect withdrawal gates.",
        "Live run 2023 attacked an isolated perfect-match worker from full health, "
        "but a giant entered and assisted after several rounds. The safe flee "
        "recovered 118 partial XP against a 148-XP flee cost, for a net 30-XP loss.",
    ),
    practice_skill="backstab",
    segment_kill_limit=1,
)


_MAHNTOR_ROCK_TOAD_THIEF_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="mahntor-rock-toad-thief-probe-14-15",
    minimum_level=14,
    maximum_level=15,
    status="research",
    execution="mahntor-rock-toad-research",
    summary=(
        "Consider the four non-aggressive Mahn-Tor Rock Toad resets without "
        "initiating combat."
    ),
    evidence=(
        "DD4 source revision d7cb330: mobile 2303, the Rock Toad, is source "
        "level 14, sentinel, evil-aligned, and has no special procedure.",
        "Mahn-Tor rooms 2311, 2312, 2313, and 2319 each contain one reset line "
        "under the mobile's global maximum of four.",
        "The source route crosses only level-0 Fido and source-level-7 Drow "
        "scouts; their fuzzed maxima are below the useful XP band at level 14.",
        "The four target rooms have no reset companions and are connected by "
        "ordinary open exits. Live duplicate and unknown-bystander checks still "
        "apply because reset order can concentrate a global mobile count after "
        "partial depletion.",
        "This first pass records exact TARGETMODE identity, room count, live "
        "consider output, and reboot identity only; it cannot initiate combat.",
    ),
    practice_skill="backstab",
)


_MAHNTOR_ROCK_TOAD_THIEF_HUNT_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="mahntor-rock-toad-thief-kill-research-14-15",
    minimum_level=14,
    maximum_level=15,
    status="research",
    execution="mahntor-rock-toad-hunt",
    summary=(
        "Attack one isolated, live-considered Mahn-Tor Rock Toad to measure "
        "damage throughput before enabling the four-room circuit."
    ),
    evidence=(
        *_MAHNTOR_ROCK_TOAD_THIEF_RESEARCH_POLICY.evidence,
        "Live run 2024 found exactly one source-matched Rock Toad in each of "
        "rooms 2311, 2313, 2312, and 2319; all four returned the perfect-match "
        "consider branch without a bystander or route interruption.",
        "Run 2024 returned from room 2319 to healer room 3054 at full health. "
        "The first combat pass retains a 90% departure-health floor, exact "
        "selector, fresh consider, +1 live-level ceiling, crowd rejection, and "
        "one-kill segment limit.",
        "Live run 2101 found a fuzzed level-13 Rock Toad in room 2311 at thief "
        "level 15, passed live consider, and opened with the newly trained "
        "backstab while wielding a piercing dagger. The first backstab missed, "
        "but combat completed without an assist for 473 XP; Kestrel sacrificed "
        "the empty corpse, recalled, recovered fully, and quit in healer room "
        "3054.",
        "Live run 2104 revisited room 2311 after an empty Aruncus sweep, found "
        "a source-matched level-14 Rock Toad, and used the exact selector for "
        "another backstab opener. The miss still initiated an unassisted fight "
        "worth 514 XP; Kestrel finished at 91/217 health, sacrificed the empty "
        "corpse for one silver, recalled, and slept to full health and movement "
        "in healer room 3054 before saving and quitting.",
    ),
    practice_skill="backstab",
    segment_kill_limit=1,
)


_MAHNTOR_ROCK_TOAD_THIEF_CIRCUIT_POLICY = ProgressionPolicy(
    policy_id="mahntor-rock-toad-thief-circuit-14-15",
    minimum_level=14,
    maximum_level=15,
    status="verified",
    execution="mahntor-rock-toad-circuit",
    summary=(
        "Hunt one isolated Rock Toad across its four Mahn-Tor reset rooms, then "
        "return to the Midgaard healer before protection or health is exhausted."
    ),
    evidence=(
        *_MAHNTOR_ROCK_TOAD_THIEF_HUNT_RESEARCH_POLICY.evidence,
        "Live run 2025 resolved the room-2311 Rock Toad at level 14 with 288 "
        "hit points and killed it without an assist or special attack.",
        "Kestrel earned 1,001 XP, finished at 132/205 hit points, ate a severed "
        "leg, sacrificed the corpse for one silver, and recovered safely at "
        "healer room 3054.",
        "Live run 2026 killed a fuzzed level-15 Rock Toad for 991 XP. Kestrel "
        "finished at 64/205 hit points, so the 40.5% continuation floor ended "
        "the circuit before a second fight and returned him safely to room 3054.",
        "Run 2026 also confirmed the level-10 thief guildmaster caps second "
        "attack at Kestrel's current 65%; the campaign persisted that rejection "
        "for level 14 instead of repeating the practice attempt.",
        "Live run 2031 quaffed the Moria purple potion before ordinary damage, "
        "confirmed sanctuary through GMCP, killed a level-15 Rock Toad for 842 "
        "XP, and finished that kill at 160/205 hit points.",
        "The old three-kill cap then allowed an unprotected second fight. "
        "Kestrel retained 137 partial XP, withdrew at the 27% health boundary, "
        "and recovered safely in healer room 3054; the cap is now one kill.",
        "The circuit retains independent exact-selector, crowd, consider, and "
        "+1 live-level gates at every stop. A carried sanctuary potion keeps a "
        "one-kill cap so one consumable cannot authorize an unprotected second "
        "fight.",
        "Live run 2105 found both large hobgoblin potion carriers wandering "
        "outside source-vetted room 4064 and returned safely without entering "
        "Moria's aggressive maze. Because unprotected runs 2025, 2026, 2101, "
        "and 2104 all returned safely after one Toad, sanctuary is an "
        "opportunistic advantage rather than a prerequisite for this one-kill "
        "circuit. A weak or partial circuit still triggers one bounded supply "
        "pass before the next attempt.",
        "Live run 2106 proved the scheduler immediately returns from an absent "
        "Moria carrier to the Mahn-Tor circuit. Kestrel retained 65 partial XP "
        "against a level-15 Rock Toad, withdrew at the health boundary, and "
        "recovered fully in healer room 3054. The safe but low-throughput fight "
        "motivated the source-backed thievery-40 and knife-toss combat path.",
        "Unprotected live runs 2110, 2113, and 2114 earned 648, 483, and 617 XP "
        "and ended their kills at 166/217, 206/217, and 150/217 hit points. "
        "Without a sanctuary reserve, the circuit may therefore attempt a "
        "second isolated target only when the existing 40.5% continuation gate "
        "passes; the 27% withdrawal boundary and all per-stop gates remain.",
        "Live runs 2129 and 2130 used the Thalos long slim dagger, killed Rock "
        "Toads for 575 and 514 XP in 69.9 and 73.8 seconds, finished at 212/217 "
        "and 194/217 hit points, and returned safely to healer room 3054. The "
        "preceding three plain-dagger kills took 104.1, 92.1, and 90.0 seconds.",
    ),
    practice_skill="backstab",
    segment_kill_limit=1,
    allow_partial_below_band=True,
)


_MAHNTOR_ROCK_TOAD_THIEF_LEVEL_SIXTEEN_POLICY = replace(
    _MAHNTOR_ROCK_TOAD_THIEF_CIRCUIT_POLICY,
    policy_id="mahntor-rock-toad-thief-circuit-16-18",
    minimum_level=16,
    maximum_level=18,
    summary=(
        "Use the proven Mahn-Tor Rock Toad circuit as a two-kill thief fallback "
        "after the level-16 watchman and Undead Soldier probes reject."
    ),
    evidence=(
        *_MAHNTOR_ROCK_TOAD_THIEF_CIRCUIT_POLICY.evidence,
        "The source-level-14 Toad has a normal 12-16 live range. Through thief level 18, every attempt retains exact-target live consider and rejects the `diff <= -5` and `diff <= -10` branches before combat.",
        "Same-reboot live runs 2176, 2181, and 2184 earned 488, 382, and 444 XP from single bounded Toad kills; run 2184 reached level 16 and returned safely to healer room 3054.",
        "Live run 2192 proved the extended policy at thief level 16: Kestrel killed an exact level-14 Toad for 472 XP, finished at 213/233 HP with full mana, ate the severed leg, sacrificed the corpse, and recovered fully at healer room 3054.",
        "Because run 2192 retained 91% health after the kill, the cap is two independently gated targets; the second stop still requires the established 40.5% health floor and a fresh exact live consider.",
        "Live run 2194 killed another level-14 Toad for 540 XP without taking damage. Two same-prototype Toads had concentrated in room 2312; DD4 `fight.c` permits a same-prototype idle mobile to assist probabilistically, so the circuit must skip that room and continue to the later reset rather than attack the pair.",
        "Live run 2199 proved that continuation: after a 419-XP first kill, the runner skipped the two-Toad room 2312, followed the registered route through room 2315 to room 2319, and killed the isolated Toad there for 466 XP. The 885-XP segment ended at 215/233 HP and recovered safely at healer room 3054.",
        "Live run 2215 finished a previously injured level-13 Toad for 395 XP after its suspicious response rejected backstab. The runner immediately opened normal combat with the same exact selector, repeated knife while GMCP enemy HP fell, avoided a false progress-watchdog withdrawal, and returned undamaged to healer room 3054.",
        "Live run 2219 proved the mandatory return from the reusable Bardoosh hunt and its loot-sale maintenance: the planner selected Mahn-Tor, killed an exact level-13 Toad for 303 XP, and recovered safely at healer room 3054.",
        "Live runs 2257 and 2259 each completed two isolated kills for 1,286 and 877 XP. Run 2258 rejected a reboot-fuzzed below-band Bardoosh between them and rotated directly back to this circuit.",
        "Live run 2261 earned 896 XP but exposed that a `(White Aura)` status prefix prevented selector binding for its second Toad. Source-line normalization now strips leading status labels after ANSI removal; run 2263 then used exact selectors for both targets and every recurring knife command while earning 731 XP without taking damage.",
        "Live run 2272 caught the area reset after two empty bounded passes, killed two exact-selector Toads for 330 and 404 XP, and raised Kestrel to level 17 with 9 hit points, 7 mana, 10 movement, and two practices of each type before returning safely.",
        "This extended fallback does not promote its combat evidence to mage, warrior, or other class rotations.",
    ),
    segment_kill_limit=2,
)


def _configured_mahntor_rock_toad_circuit(
    context: ProgressionContext,
) -> ProgressionPolicy:
    """Apply the evidence-backed kill cap for the current protection state."""
    return replace(
        _MAHNTOR_ROCK_TOAD_THIEF_CIRCUIT_POLICY,
        practice_skill=context.practice_skill,
        segment_kill_limit=1 if context.has_sanctuary_potion else 2,
    )


_DWARVEN_NOBLEMAN_THIEF_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="dwarven-nobleman-thief-probe-13-15",
    minimum_level=13,
    maximum_level=15,
    status="research",
    execution="dwarven-nobleman-research",
    summary=(
        "Consider the isolated neutral dwarven nobleman as a varied-loot "
        "alternative after repeated Aruncus kills."
    ),
    evidence=(
        "DD4 source revision d7cb330: mobile 20504, the dwarven nobleman, "
        "resets once in Dwarven Homestead room 20506.",
        "The source prototype is level 13 with normal mobile-level fuzz, "
        "neutral alignment, sentinel and stay-area act flags, and no special "
        "procedure.",
        "The reset equips a cane, pants, and tuxedo, giving a future verified "
        "kill varied sellable loot instead of Aruncus's no-remove amulet.",
        "The source-derived route reaches room 20506 through two reset-closed "
        "doors. The only potentially relevant approach wanderer is a "
        "source-level-10 Kodiak bear, so this first pass records live route, "
        "crowd, target, and consider evidence without initiating combat. The "
        "source-level-45 maid in the endpoint room is non-aggressive and is an "
        "explicitly allowed bystander; wandering house guests remain unsafe.",
    ),
    practice_skill="backstab",
)


_DWARVEN_NOBLEMAN_THIEF_HUNT_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="dwarven-nobleman-thief-kill-research-13-15",
    minimum_level=13,
    maximum_level=15,
    status="research",
    execution="dwarven-nobleman-hunt",
    summary=(
        "Attack one isolated, live-considered dwarven nobleman as a "
        "varied-loot alternative to the depleted Aruncus loop."
    ),
    evidence=(
        *_DWARVEN_NOBLEMAN_THIEF_RESEARCH_POLICY.evidence,
        "Live run 1919 traversed the complete source route without incidental "
        "combat, but a redundant destination hop prevented consideration.",
        "Live run 1922 traversed the corrected route, arrived in room 20506 at "
        "full health, and returned safely to healer room 3054 after finding the "
        "sentinel reset absent.",
        "Combat remains gated on a same-reboot viable consider result, one exact "
        "source-matched target, a 90% departure-health floor, a +1 live-level "
        "ceiling, no unsafe bystanders, and one bounded kill. The source-known "
        "maid is the only permitted endpoint bystander.",
    ),
    practice_skill="backstab",
    segment_kill_limit=1,
)


_DWARVEN_NOBLEMAN_THIEF_LEVEL_SEVENTEEN_RESEARCH_POLICY = replace(
    _DWARVEN_NOBLEMAN_THIEF_RESEARCH_POLICY,
    policy_id="dwarven-nobleman-thief-probe-17-18",
    minimum_level=17,
    maximum_level=18,
    summary=(
        "Reconsider the isolated Dwarven Homestead nobleman as a fresh "
        "level-17 progression target after the longer probes are unavailable."
    ),
    evidence=(
        *_DWARVEN_NOBLEMAN_THIEF_RESEARCH_POLICY.evidence,
        "Live runs 1926 and 1931 found a level-15 nobleman and correctly "
        "rejected it for level-13 Kestrel. At level 17 that upper source-fuzz "
        "roll is inside the useful XP band and no longer exceeds the player, "
        "so a new policy ID must collect a fresh exact consider result.",
        "The unique sentinel target returns immediately after a failed consider "
        "gate; it never expands an already decisive rejection into an area "
        "search.",
        "Live run 2292 reached exact selector #10736 at full health and received "
        "`looks like an easy kill` with only a slight target-health advantage. "
        "The no-combat probe remained valid while a level-20 house guest shared "
        "the room; combat promotion must reconsider the nobleman and require it "
        "to be the room's sole mobile because `fight.c` permits probabilistic "
        "different-prototype assistance.",
        "DD4 source revision cd138ae: Miden'nir mobile 3501, the mountain goblin, "
        "is source level 6 and mobile 3506, the goblin lieutenant, is source "
        "level 7. At thief level 17 these approach interruptions are below the "
        "useful XP band; the mountain goblin is therefore a registered trivial "
        "bystander while any unknown or useful-band joiner remains a hard abort.",
    ),
)


_DWARVEN_NOBLEMAN_THIEF_LEVEL_SEVENTEEN_HUNT_POLICY = replace(
    _DWARVEN_NOBLEMAN_THIEF_HUNT_RESEARCH_POLICY,
    policy_id="dwarven-nobleman-thief-hunt-17-18",
    minimum_level=17,
    maximum_level=18,
    summary=(
        "Use fresh level-17 evidence for one exact nobleman fight, collect its "
        "varied equipment, and return to the Midgaard healer."
    ),
    evidence=(
        *_DWARVEN_NOBLEMAN_THIEF_LEVEL_SEVENTEEN_RESEARCH_POLICY.evidence,
        "Promotion permits one kill per reboot-scoped probe. After that single "
        "reset is consumed, selection rotates onward rather than immediately "
        "repeating the long route.",
        "A wandering house guest is not an allowed bystander. The hunt's explicit "
        "one-mobile ceiling must skip the stop before combat unless the guest has "
        "left room 20506.",
    ),
)


_DWARVEN_SERVANT_THIEF_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="dwarven-servant-thief-probe-17-18",
    minimum_level=17,
    maximum_level=18,
    status="research",
    execution="dwarven-servant-research",
    summary=(
        "Consider the isolated Dwarven Home servant as a fresh level-17 "
        "progression target without initiating combat."
    ),
    evidence=(
        "DD4 source revision cd138ae: mobile 20505, the dwarven servant, "
        "resets once in Kitchen room 20508 at source level 17 with a normal "
        "15-19 live range.",
        "The servant is non-aggressive, stays in its area, has no special "
        "procedure, and has no reset companion in room 20508.",
        "The reset equips a serving tray and a servant's uniform, providing "
        "varied source-keyed loot for the existing sale loop.",
        "The source-derived Dwarven Home route reuses the proven two-door "
        "approach and adds the final north-north-west suffix from room 20506 "
        "through rooms 20507 and 20508.",
        "The servant is positively aligned, so the probe records live "
        "consider output and room state before any combat promotion; no kill "
        "is authorized without a fresh useful-band result and a sole target.",
    ),
    practice_skill="backstab",
)


_DWARVEN_SERVANT_THIEF_HUNT_POLICY = ProgressionPolicy(
    policy_id="dwarven-servant-thief-hunt-17-18",
    minimum_level=17,
    maximum_level=18,
    status="research",
    execution="dwarven-servant-hunt",
    summary=(
        "Use fresh Dwarven Home servant evidence for one bounded thief fight, "
        "then return to the Midgaard healer."
    ),
    evidence=(
        *_DWARVEN_SERVANT_THIEF_RESEARCH_POLICY.evidence,
        "The hunt repeats consider immediately before combat, requires at "
        "least 90% health, accepts at most one live level above the thief, "
        "and permits only one exact-target kill.",
    ),
    practice_skill="backstab",
    segment_kill_limit=1,
)


_SHIRE_DWARVEN_PRINCE_THIEF_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="shire-dwarven-prince-thief-probe-17-20",
    minimum_level=17,
    maximum_level=20,
    status="research",
    execution="shire-dwarven-prince-research",
    summary=(
        "Reach the Shire's Bag End bedroom and consider the dwarven prince "
        "without initiating combat."
    ),
    evidence=(
        "DD4 source revision d7cb330: mobile 1117, the dwarven prince, "
        "resets once in Shire room 1136 at source level 17 with normal "
        "15-19 live fuzz.",
        "The source reset also loads one elven warrior in room 1136, so the "
        "probe requires a single exact target and rejects the companion as a "
        "combat crowd.",
        "The prince is sentinel and non-aggressive but has spec_cast_mage, "
        "positive alignment, and a mithril axe; this policy records route, "
        "presence, crowd, and consider evidence before any hunt promotion.",
        "The source-derived recall route is 2s5w4n2w5nw and ends at room 1136 "
        "without entering the Thain's guard office.",
    ),
    practice_skill="backstab",
)


_SHIRE_DWARVEN_PRINCE_THIEF_HUNT_POLICY = replace(
    _SHIRE_DWARVEN_PRINCE_THIEF_RESEARCH_POLICY,
    policy_id="shire-dwarven-prince-thief-hunt-17-20",
    execution="shire-dwarven-prince-hunt",
    summary=(
        "Use one same-reboot viable, sole-target prince probe for a bounded "
        "thief hunt after the source special and live consider gates pass."
    ),
    evidence=(
        *_SHIRE_DWARVEN_PRINCE_THIEF_RESEARCH_POLICY.evidence,
        "Combat remains limited to one exact target, a 95% departure-health "
        "floor, a maximum +1 live-level offset, and no elven-warrior or other "
        "unapproved bystander.",
    ),
    segment_kill_limit=1,
)


_SHIRE_THAIN_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="shire-thain-probe-17-20",
    minimum_level=17,
    maximum_level=20,
    status="research",
    execution="shire-thain-research",
    summary=(
        "Reach the Shire's Thain's Office and consider the isolated Thain "
        "without initiating combat."
    ),
    evidence=(
        "DD4 source revision eaaad93: mobile 1112, the Thain, resets once in "
        "Shire room 1111 at source level 14 with normal 12-16 live fuzz.",
        "The Thain is stay-area and non-aggressive, has no reset companion in "
        "room 1111, and uses spec_guard; the first pass therefore uses a "
        "where preflight plus a bounded source-room sweep before recording "
        "isolation and live consider output without attacking.",
        "The source reset loads a bardiche, leather vest, and thain girth. "
        "The route from recall is the short source-backed `2s5w4n5e` path "
        "to room 1111, with no closed door.",
        "A useful-band result is required before combat; the existing do_consider "
        "policy rejects both diff <= -5 branches and any healthier target.",
        "Live run 2578 reached room 1111 safely but found the Thain absent from "
        "the reset room. The source stay-area flag makes that a temporary "
        "wandering-state result rather than permanent route evidence; the next "
        "pass uses `where thain` and the registered Shire room sweep.",
    ),
    practice_skill="backstab",
)


_SHIRE_THAIN_HUNT_POLICY = replace(
    _SHIRE_THAIN_RESEARCH_POLICY,
    policy_id="shire-thain-hunt-17-20",
    execution="shire-thain-hunt",
    summary=(
        "Use one same-reboot viable, isolated Thain probe for a bounded thief "
        "hunt, then return to the Midgaard healer."
    ),
    evidence=(
        *_SHIRE_THAIN_RESEARCH_POLICY.evidence,
        "Combat repeats consider immediately before the opener, requires at "
        "least 90% health, a target no more than the thief's live level, no "
        "unapproved bystander, and one confirmed kill.",
        "The Thain's spec_guard is a source-verified risk boundary: the runner "
        "must not turn a special response into permission to continue after an "
        "unexpected guard or assist event.",
    ),
    segment_kill_limit=1,
)


_SHIRE_ELVEN_WIZARD_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="shire-elven-wizard-probe-17-20",
    minimum_level=17,
    maximum_level=20,
    status="research",
    execution="shire-elven-wizard-research",
    summary=(
        "Reach the Shire's grassy field and consider the isolated Elven Wizard "
        "without initiating combat."
    ),
    evidence=(
        "DD4 source revision eaaad93: mobile 1100, the Elven Wizard, resets "
        "once in Shire room 1128 at source level 18 with normal 16-20 live "
        "fuzz.",
        "The Wizard is sentinel and stay-area, has spec_cast_mage, and is "
        "positive aligned. The same room reset loads one source-level-6 "
        "halfling beauty, which is registered as a trivial bystander at this "
        "level; the first pass records presence and live consider output only.",
        "The source-backed recall route is `2s5w4n5w` and ends in room 1128 "
        "without a redundant destination hop or closed door.",
        "No combat policy is promoted from this probe until source spell risk, "
        "live consideration, and the permitted bystander behavior are all "
        "reviewed together.",
    ),
    practice_skill=None,
)


_SHIRE_ELVEN_WIZARD_HUNT_POLICY = replace(
    _SHIRE_ELVEN_WIZARD_RESEARCH_POLICY,
    policy_id="shire-elven-wizard-hunt-17-20",
    execution="shire-elven-wizard-hunt",
    summary=(
        "Use one same-reboot viable, isolated Wizard probe for a bounded thief "
        "hunt only after a sanctuary reserve is available."
    ),
    evidence=(
        *_SHIRE_ELVEN_WIZARD_RESEARCH_POLICY.evidence,
        "The source special can cast blindness, chill touch, weaken, lightning "
        "bolt, fireball, colour spray, dispel magic, acid blast, or energy "
        "drain; the live hunt therefore requires a full-health departure, a "
        "pouch-held sanctuary potion, one exact target, and one kill limit.",
        "Combat returns to the Midgaard healer after the first target or any "
        "disabling-affect, health, movement, or combat-progress boundary.",
    ),
    practice_skill="backstab",
    segment_kill_limit=1,
)


_PYRAMID_ALI_BABA_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="pyramid-ali-baba-probe-18-20",
    minimum_level=18,
    maximum_level=20,
    status="research",
    execution="pyramid-ali-baba-research",
    summary=(
        "Reach the Great Pyramid's isolated Ali Baba reset and record live "
        "consideration before authorizing combat."
    ),
    evidence=(
        "DD4 source revision eaaad93: mobile 2605, Ali Baba, resets once in "
        "Pyramid room 2643 at source level 18 with normal 16-20 live fuzz.",
        "The reset has no companion and the mobile is sentinel/stay-area, "
        "with no aggressive flag; its source special is spec_thief, which "
        "steals a small percentage of carried coins rather than dealing combat "
        "damage.",
        "The reset equips a cloth turban and wields an obsidian dirk. The "
        "official prefix crosses the low-level desert and enters the pyramid "
        "at room 2600. The desert maze is randomized, so the runner follows "
        "live GMCP destination VNUMs; from room 2600 the verified continuation "
        "is `e;u;n;e;u;open down;2d;4e;n` to room 2643.",
        "This first pass is consider-only. Combat promotion requires an exact "
        "target, a sole mobile, a useful-band live consider, and a bounded "
        "return path; no special-procedure assumption authorizes a kill by "
        "itself.",
        "Live run 2599 crossed the randomized desert safely to room 2600 and "
        "returned after the first post-maze route mismatch was detected.",
        "Live run 2600 reached room 2643 and `where ali baba` found Ali Baba "
        "in an `A Tunnel` room rather than at the reset. The probe therefore "
        "searches source-connected rooms 2642, 2641, 2640, and 2639 before "
        "returning through the branch to check 2636, 2635, and 2634. Live "
        "run 2604 then visibly placed Ali Baba in source room 2639, proving "
        "that the omitted tunnel rooms must be checked individually.",
        "Live run 2605 found the exact Ali Baba selector in room 2639; the "
        "perfect-match consider still reported him much healthier than the "
        "thief, so the research policy correctly authorized no combat and "
        "returned safely to the healer.",
        "Live run 2606 repaired a stale long-sword checkpoint by wielding the "
        "carried long slim dagger, confirming the source-backed primary after "
        "the recovery stance and saving in healer room 3054.",
    ),
    practice_skill="backstab",
)


_PYRAMID_ALI_BABA_HUNT_POLICY = replace(
    _PYRAMID_ALI_BABA_RESEARCH_POLICY,
    policy_id="pyramid-ali-baba-hunt-18-20",
    execution="pyramid-ali-baba-hunt",
    summary=(
        "Use one same-reboot viable Ali Baba probe for a full-health, "
        "single-target thief hunt and return safely to the healer."
    ),
    evidence=(
        *_PYRAMID_ALI_BABA_RESEARCH_POLICY.evidence,
        "The hunt retains exact-target, sole-mobile, maximum-live-level, "
        "90-percent departure-health, and one-kill limits. A coin-stealing "
        "special is recorded as an economic risk, not silently treated as "
        "an attack-safe guarantee.",
    ),
    segment_kill_limit=1,
)


_GNOME_TREASURER_THIEF_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="gnome-treasurer-thief-probe-13-15",
    minimum_level=13,
    maximum_level=15,
    status="research",
    execution="gnome-treasurer-research",
    summary=(
        "Collect source-keyed loose coin piles and consider the isolated Gnome "
        "treasurer without initiating combat."
    ),
    evidence=(
        "DD4 source revision d7cb330: mobile 1521, the treasurer, resets once "
        "in Gnome Village room 1570 with source level 10 and normal load fuzz.",
        "The treasurer is unarmed, has no special procedure, and is isolated "
        "from the aggressive soldier resets in adjacent room 1571.",
        "Objects 1516 and 1517 reset loose in room 1570 as piles with the "
        "source keyword `coins`; collecting them is a non-combat money action.",
        "The source-derived route reaches room 1570 from recall. Any approach "
        "combat may continue only while every GMCP enemy is confirmed below "
        "the useful XP band; unknown or useful-band attackers still force an "
        "immediate withdrawal.",
    ),
    practice_skill="backstab",
)


_GNOME_TREASURER_THIEF_HUNT_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="gnome-treasurer-thief-kill-research-13-15",
    minimum_level=13,
    maximum_level=15,
    status="research",
    execution="gnome-treasurer-hunt",
    summary=(
        "Attack one isolated, live-considered Gnome treasurer after collecting "
        "any loose source-keyed coin piles."
    ),
    evidence=(
        *_GNOME_TREASURER_THIEF_RESEARCH_POLICY.evidence,
        "Combat requires a same-reboot viable probe, 90% departure health, "
        "one exact source-matched target, a +1 live-level ceiling, no "
        "bystanders, and one bounded kill.",
        "Live run 2038 collected both loose piles for 6 gold, 45 silver, and "
        "143 copper under reboot Mon Jul 27 09:12:49 2026, then killed the "
        "live-considered treasurer for 282 XP without losing hit points.",
        "The crowded hobgoblin-soldier approach remained traversal-only; the "
        "treasurer room itself contained no combat bystander. Kestrel recalled, "
        "recovered, saved, and quit in healer room 3054.",
        "Live runs 2067 and 2071 encountered the same selector #24994 at level "
        "14 and both received the below-band `is no match for you` result. "
        "Persist that rejection for this character level and reboot instead "
        "of repeating the non-XP trip.",
    ),
    practice_skill="backstab",
    segment_kill_limit=1,
)


_MIRROR_REALM_WATCHMAN_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="mirror-realm-watchman-probe-16-20",
    minimum_level=16,
    maximum_level=20,
    status="research",
    execution="mirror-realm-watchman-research",
    summary=(
        "Reach and consider two source-isolated Mirror Realm watchmen without "
        "initiating combat, then return to the Midgaard healer."
    ),
    evidence=(
        "DD4 source revision d7cb330: mobile 19009 resets once in Mirror Realm room 19009; it is sentinel and stay-area, but not aggressive.",
        "Distinct mobile 19010 has the same level and safe flags and resets alone in room 19010; from room 19009 the route returns east to hub room 19008 and enters the eastern watchtower.",
        "The source route reaches room 19009 from recall through only ordinary open exits and one reset-open north door. Its only static aggressor is level-0 Fido; update.c skips aggression when the player is more than ten levels higher.",
        "The source prototype level is 19 with normal mobile-level fuzz, carries a staff, and has no special procedure. This policy only records presence, crowd state, and do_consider output.",
        "Any unexpected combat aborts the probe with flee and healer recovery; no combat policy may be promoted until a bounded live probe confirms the route and target behavior.",
        "Live run 2185 reached room 19005 undamaged but exposed an off-by-two route that attempted north before opening the reset-closed door. The watchdog recalled, saved, and quit at healer room 3054; source room exits corrected the suffix to `2n;open north;3nw`.",
        "Live run 2186 proved the corrected door sequence through rooms 19005-19008 and entered watchtower room 19009 with its watchman. The run then exposed and safely recovered from a redundant stop-level request to navigate to the room it had already reached.",
        "Live run 2187 entered room 19009 and returned safely in 29 seconds, but exposed that exact matching must use the source parser's canonical generic identity `watchman`, not the short description `a watchman`.",
        "Live run 2188 bound exact selector #9987 to the room-19009 watchman and received the `diff <= 5` consider branch plus a 100-or-more hit-point disadvantage. It did not attack and returned to healer room 3054 at full health and movement; this reboot-scoped roll is not viable.",
        "Live run 2200 proved the expanded two-stop probe: it reconsidered room-19009 selector #9987, followed live GMCP exits east through room 19008 into room 19010, and considered selector #9991. Both watchmen returned the dangerous `Do you feel lucky, punk?` level branch, so neither was attacked; their separate HP wording did not determine the level gate.",
        "Live run 2248 repeated both exact watchman checks after reboot Sat Aug 1 03:23:54 2026; the bot declined the dangerous level-difference result and returned safely.",
        "Live run 2607 repeated both exact watchman selectors after the Aug 2 reboot; both returned `The perfect match!` and therefore passed the level-difference gate, despite separate much-healthier/slightly-healthier HP addenda. No combat was initiated during this consider-only probe; this evidence may promote the bounded hunt policy.",
    ),
    practice_skill=None,
)


_MIRROR_REALM_WATCHMAN_HUNT_POLICY = ProgressionPolicy(
    policy_id="mirror-realm-watchman-hunt-16-20",
    minimum_level=16,
    maximum_level=20,
    status="research",
    execution="mirror-realm-watchman-hunt",
    summary=(
        "Use a fresh viable watchman consideration to run one bounded field "
        "fight, then re-consider before any further engagement."
    ),
    evidence=(
        *_MIRROR_REALM_WATCHMAN_RESEARCH_POLICY.evidence,
        "The watchman has no source special procedure and is non-aggressive, unlike later registered probes with caster, thief, guard, or breath specials.",
        "The hunt repeats DD4 consider immediately before combat, requires 85% health, one exact source-matched target, no crowd, and a single confirmed kill.",
        "A missing, unsuitable, or zero-XP hunt returns to the probe gate rather than retrying combat blindly.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)


_MIRROR_REALM_WATCHMAN_LEVEL_NINETEEN_RESEARCH_POLICY = replace(
    _MIRROR_REALM_WATCHMAN_RESEARCH_POLICY,
    policy_id="mirror-realm-watchman-probe-19-20",
    minimum_level=19,
    maximum_level=20,
    summary=(
        "Reconsider the source-isolated Mirror Realm watchman after reaching "
        "the level-19 band; earlier lower-level rejection is not reusable."
    ),
    evidence=(
        *_MIRROR_REALM_WATCHMAN_RESEARCH_POLICY.evidence,
        "The level-16-20 result key is deliberately not reused here: a target "
        "that was much healthier at level 17 must be reconsidered after the "
        "character reaches level 19, because the source mobile rolls within "
        "its normal level fuzz and the live level gap has changed.",
    ),
)


_MIRROR_REALM_WATCHMAN_LEVEL_NINETEEN_HUNT_POLICY = replace(
    _MIRROR_REALM_WATCHMAN_HUNT_POLICY,
    policy_id="mirror-realm-watchman-hunt-19-20",
    minimum_level=19,
    maximum_level=20,
    summary=(
        "Use a fresh level-19/20 watchman consideration for one bounded "
        "exact-target fight, then return to the Midgaard healer."
    ),
    evidence=(
        *_MIRROR_REALM_WATCHMAN_LEVEL_NINETEEN_RESEARCH_POLICY.evidence,
        "The level-19/20 hunt repeats consider immediately before combat, "
        "requires 85% health, one exact source-matched target, no crowd, and "
        "a single confirmed kill.",
    ),
)


_CRYSTALMIR_WHITE_STAG_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="crystalmir-white-stag-probe-16-20",
    minimum_level=16,
    maximum_level=20,
    status="research",
    execution="crystalmir-white-stag-research",
    summary=(
        "Search the source-safe Crystalmir circuit and consider the wandering "
        "White Stag without initiating combat."
    ),
    evidence=(
        "DD4 source revision d7cb330: mobile 10012, the White Stag, is level 17 with normal 15-19 live fuzz, evil aligned, unarmed, stay-area, non-aggressive, and has no special procedure.",
        "The Stag resets alone in room 10016 but can wander through 37 connected Crystal rooms. The GMCP-guided circuit covers all 34 low-risk reachable rooms while excluding aggressive reset rooms 10005, 10030, and 10039.",
        "The recall route uses the proven Ambush and Forest approach, enters Crystal at room 10001, and reaches room 10016 around the north shore without crossing the aggressive Barracuda reset.",
        "A wandering Fewmaster Toede can still reach the circuit. Any unexpected aggression aborts the no-combat probe with flee, recall, and healer recovery.",
        "Live run 2203 proved the complete 51-command route to room 10016 without damage. `where stag` confirmed the target absent from the area, so the bot skipped the search circuit, recalled, recovered to full movement, and saved and quit in healer room 3054 without losing HP or XP.",
        "Live run 2205 repeated the absence after only one productive Rock Toad segment. The temporary absence now requires three productive field segments outside Crystalmir before another bounded probe.",
        "Live run 2206 earned 440 XP from one isolated level-14 Rock Toad, skipped a triple-Toad assist crowd, and reduced the Stag absence cooldown from three to two without revisiting Crystalmir.",
        "After three productive outside-area segments, live run 2211 performed the authorized retry. `where stag` still reported absence in room 10016, so the bot returned without combat or XP loss and reset the cooldown to three.",
        "Live run 2251 repeated the source-room `where stag` preflight after reboot Sat Aug 1 03:23:54 2026, found the Stag globally absent, skipped the expensive search circuit, and returned safely.",
    ),
    practice_skill=None,
)


_CRYSTALMIR_WHITE_STAG_HUNT_POLICY = ProgressionPolicy(
    policy_id="crystalmir-white-stag-hunt-16-20",
    minimum_level=16,
    maximum_level=20,
    status="research",
    execution="crystalmir-white-stag-hunt",
    summary=(
        "Use fresh viable White Stag evidence for one reconsidered field fight."
    ),
    evidence=(
        *_CRYSTALMIR_WHITE_STAG_RESEARCH_POLICY.evidence,
        "The hunt requires 85% health, a live consider no more than one level above the character, one exact source-matched target, no unsafe crowd, and one confirmed kill.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)


_SHADOW_KEEP_SOLDIER_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="shadow-keep-undead-soldier-probe-16-20",
    minimum_level=16,
    maximum_level=20,
    status="research",
    execution="shadow-keep-undead-soldier-research",
    summary=(
        "Consider the isolated Shadow Keep Undead Soldier and two "
        "non-aggressive Shadow Wraith resets without initiating combat, then "
        "return to the Midgaard healer."
    ),
    evidence=(
        "DD4 source revision d7cb330: mobile 16601, an Undead Soldier, resets once in Shadow Keep Burial Mound room 16615.",
        "The source prototype is level 15 with normal mobile-level fuzz (observed range 13-17), is sentinel and non-aggressive, and has no special procedure.",
        "The route from Midgaard healer room 3054 reaches room 16615 through ordinary exits. The source parser canonicalizes the room line to `undead soldier`, which is bound to a fresh TARGETMODE selector.",
        "The soldier wields a Rusty Sword, so source combat estimates account for the armed-mobile damage multiplier. This policy records live presence, crowd state, and do_consider output without attacking.",
        "Any unexpected combat aborts the probe with flee and healer recovery; combat remains limited to one freshly reconsidered target after a viable reboot-scoped result.",
        "Live runs 2189-2193 reached room 16615 safely but found the reset absent. Run 2198 was interrupted by below-band route goblins before reaching Shadow Keep; no-consider route aborts no longer persist as target nonviability.",
        "Live run 2229 proved the repaired persistence path by selecting and completing the probe again without route combat. The Soldier remained absent, so retries now require three productive field segments outside Shadow Keep.",
        "The source route also passes mobile 16600, a sentinel, non-aggressive Shadow Wraith with no special procedure, resetting once in room 16600 and once in room 16603. Its source level 10 fuzzes to 8-12; only a live level-12 result remains inside the level-16 useful XP band.",
        "Live run 2237 proved the first expanded path through rooms 16603 and 16600 without combat, but the Soldier and both Wraith resets were absent.",
        "Source resets place one additional Soldier in room 16607 and one in room 16618. From room 16615, the full circuit uses west-north-north-west-up to 16607, down-east-south-west-west to 16618, east-east-east to Wraith room 16603, then east-south-east to Wraith room 16600. Each exact target receives its own live consider gate without combat.",
        "Live run 2252 skipped a duplicate-Soldier assist risk, found an isolated drawbridge Soldier that was a perfect match and slightly less healthy than Kestrel, and promoted it without attacking.",
    ),
    practice_skill=None,
)


_SHADOW_KEEP_SOLDIER_HUNT_POLICY = ProgressionPolicy(
    policy_id="shadow-keep-undead-soldier-hunt-16-20",
    minimum_level=16,
    maximum_level=20,
    status="research",
    execution="shadow-keep-undead-soldier-hunt",
    summary=(
        "Use a fresh viable Shadow Keep exterior consideration for one bounded "
        "Soldier or Wraith fight, then return to the Midgaard healer."
    ),
    evidence=(
        *_SHADOW_KEEP_SOLDIER_RESEARCH_POLICY.evidence,
        "The hunt repeats DD4 consider immediately before combat, requires 85% health, rejects targets more than one level above the character, and permits only one confirmed kill.",
        "A missing, unsuitable, crowded, or zero-XP result retires this fallback for the current reboot rather than retrying blindly.",
        "Live run 2253 killed the promoted Soldier for 844 XP, recovered and rearmed through two disarms, looted its helm and sword, and returned safely at 145/233 hit points. Run 2255 then skipped the remaining duplicate pair, completed every other Soldier and Wraith stop, and rotated away after the empty pass.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)


_GALAXY_WHITE_DWARF_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="galaxy-white-dwarf-probe-17-20",
    minimum_level=17,
    maximum_level=20,
    status="research",
    execution="galaxy-white-dwarf-research",
    summary=(
        "Follow the source-derived Galaxy route and consider the room-9306 "
        "white dwarf without initiating combat."
    ),
    evidence=(
        "DD4 source revision cd138ae: Galaxy mobile 9306 is source level 15 "
        "with a 13-17 live range, is non-aggressive, unarmed, stay-area, and "
        "has no special procedure.",
        "The first mobile-9306 reset is alone in room 9306. Later same-vnum "
        "reset commands are constrained by the one-mobile source limit, so "
        "the reset room is the bounded first probe rather than permission to "
        "search the area's higher-level branches.",
        "The source graph reaches stable Shadow Grove entrance room 1300 from "
        "recall through low-level transit rooms and no closed door. The Grove "
        "randomizes direction labels, so the runner follows live GMCP exit "
        "destinations through rooms 1308, 1305, and 1306 before traversing the "
        "fixed 9301-9306 Galaxy chain.",
        "The live source line canonicalizes to `tiny white dwarf`. The first "
        "pass is exact-target and consider-only, rejects a healthier target, "
        "and returns immediately after any failed consider gate.",
        "Live run 2289 proved the fixed directions only as far as room 1300, "
        "then safely aborted when a randomized Grove exit returned to the "
        "entrance. That failure is route evidence, not target viability; the "
        "policy now delegates the maze to destination-vnum navigation.",
        "Live run 2291 proved that GMCP destination navigation reaches room "
        "9306 without combat or damage. The reset target was absent there, and "
        "`where white` located a white dwarf in room 9345, whose source reset "
        "also contains level-31 Cancer; the level-17 policy correctly refused "
        "to pursue that unsafe locator result and returned to healer room 3054.",
    ),
    practice_skill=None,
)


_GALAXY_WHITE_DWARF_HUNT_POLICY = ProgressionPolicy(
    policy_id="galaxy-white-dwarf-hunt-17-20",
    minimum_level=17,
    maximum_level=20,
    status="research",
    execution="galaxy-white-dwarf-hunt",
    summary=(
        "Use fresh viable room-9306 evidence for one reconsidered white-dwarf "
        "fight, then return to the Midgaard healer."
    ),
    evidence=(
        *_GALAXY_WHITE_DWARF_RESEARCH_POLICY.evidence,
        "The hunt requires at least 85% health, a fresh exact consider no more "
        "than one level above the character, no unsafe bystander, and one "
        "confirmed kill.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)


_GALAXY_RED_SUPERGIANT_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="galaxy-red-supergiant-probe-17-20",
    minimum_level=17,
    maximum_level=20,
    status="research",
    execution="galaxy-red-supergiant-research",
    summary=(
        "Follow the source-derived Galaxy route and consider one red "
        "supergiant without initiating combat."
    ),
    evidence=(
        "DD4 source revision cd138ae: Galaxy mobile 9305 is source level 15 "
        "with a 13-17 live range, is sentinel, non-aggressive, stay-area, "
        "and has no special procedure.",
        "The source resets one red supergiant in each of rooms 9304, 9308, "
        "9309, and 9313. Each reset is registered as a separate destination "
        "stop so live GMCP room VNUMs govern navigation after the stable "
        "Shadow Grove route.",
        "The source line canonicalizes to `red supergiant`. The first pass "
        "uses `where red` only as an area-presence preflight, then performs "
        "an exact-target, sole-target, fresh-consider probe in each registered "
        "room without attacking. A perfect-match result that is only teensy "
        "healthier remains inside this source-safe policy's aggressive band.",
        "The reset-room traversal avoids the 9305 comet corridor by moving "
        "from room 9308 through 9312 and 9313 before checking 9309; unrelated "
        "wandering attackers remain a hard abort rather than a target.",
        "The route records no source-listed equipment drop; this policy is a "
        "bounded level-band XP probe and does not replace the thief's retained "
        "piercing weapon or future stun-weapon maintenance.",
    ),
    practice_skill=None,
)


_GALAXY_RED_SUPERGIANT_HUNT_POLICY = ProgressionPolicy(
    policy_id="galaxy-red-supergiant-hunt-17-20",
    minimum_level=17,
    maximum_level=20,
    status="research",
    execution="galaxy-red-supergiant-hunt",
    summary=(
        "Use fresh viable red-supergiant consideration for one bounded fight, "
        "then return to the Midgaard healer."
    ),
    evidence=(
        *_GALAXY_RED_SUPERGIANT_RESEARCH_POLICY.evidence,
        "The hunt requires at least 85% health, a fresh exact consider no more "
        "than one level above the character, no unsafe bystander, and one "
        "confirmed kill.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)


_HIGHTOWER_JAILOR_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="hightower-jailor-probe-17-20",
    minimum_level=17,
    maximum_level=20,
    status="research",
    execution="hightower-jailor-research",
    summary=(
        "Reach the High Tower through the randomized Shadow Grove and "
        "consider the Jailor without initiating combat."
    ),
    evidence=(
        "DD4 source revision cd138ae: mobile 1310, the Jailor, resets once "
        "in High Tower room 1328 at source level 17 with a normal 15-19 "
        "live range.",
        "The Jailor is positively aligned, stays in the area, has no reset "
        "companion in room 1328, and carries no source-listed equipment drop.",
        "The source mobile assigns spec_cast_mage. Its source implementation "
        "can cast blindness, chill touch, weaken, lightning bolt, fireball, "
        "colour spray, dispel magic, acid blast, or energy drain according to "
        "the Jailor's level; no combat is authorized by the first probe.",
        "The recall route reaches stable Shadow Grove entrance room 1300 via "
        "2s13ws2w2sws3wnwn. The Grove randomizes direction labels, so the "
        "runner follows live GMCP destination VNUMs through 1308, 1305, and "
        "1302 before using the source-backed 1311-1317 approach.",
        "The final source-backed route opens the trapdoor at room 1317, goes "
        "down twice, then east twice to Jailor office room 1328. The research "
        "stop is exact-target, sole-mobile, fresh-consider, and consider-only.",
    ),
    practice_skill=None,
)


_HIGHTOWER_JAILOR_HUNT_POLICY = ProgressionPolicy(
    policy_id="hightower-jailor-hunt-17-20",
    minimum_level=17,
    maximum_level=20,
    status="research",
    execution="hightower-jailor-hunt",
    summary=(
        "Use fresh viable Jailor evidence for one bounded fight only after "
        "the source-caster risk gates pass."
    ),
    evidence=(
        *_HIGHTOWER_JAILOR_RESEARCH_POLICY.evidence,
        "Combat promotion requires a same-reboot viable exact consider, at "
        "least 90% health, a target no more than one live level above the "
        "character, no bystanders, and one confirmed kill.",
        "The first live hunt must retain the normal blindness, poison, mana, "
        "movement, combat-progress, and healer-return withdrawal boundaries; "
        "a source special is not evidence that the target is safe for every "
        "class.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)


_MIRROR_REALM_WATCHMAN_LEVEL_TWENTY_ONE_RESEARCH_POLICY = replace(
    _MIRROR_REALM_WATCHMAN_RESEARCH_POLICY,
    policy_id="mirror-realm-watchman-probe-21-25",
    minimum_level=21,
    maximum_level=25,
    summary=(
        "Revalidate the isolated Mirror Realm watchman through level 25 before "
        "engaging its source-fuzzed, now borderline level range."
    ),
)


_MIRROR_REALM_WATCHMAN_LEVEL_TWENTY_ONE_HUNT_POLICY = replace(
    _MIRROR_REALM_WATCHMAN_HUNT_POLICY,
    policy_id="mirror-realm-watchman-hunt-21-25",
    minimum_level=21,
    maximum_level=25,
    summary=(
        "Use a fresh viable Watchman consideration as a bounded level-21 to "
        "25 hunt, while rejecting every below-band result before combat."
    ),
)


_MIRROR_REALM_GARDENER_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="mirror-realm-gardener-probe-21-25",
    minimum_level=21,
    maximum_level=25,
    status="research",
    execution="mirror-realm-gardener-research",
    summary=(
        "Reach and consider the Mirror Realm gardener without initiating combat, "
        "then return to the Midgaard healer."
    ),
    evidence=(
        "DD4 source revision cd138ae: mobile 19036, the gardener, resets once in Mirror Realm room 19091.",
        "The source prototype is level 25 with normal mobile-level fuzz. Its act flags are stay-area rather than aggressive; it carries clippers and has spec_thief, so the route remains no-combat research only.",
        "The executable route tail is east from room 19108 to 19089, then north through 19090 to 19091; taking east again enters 19120 and cannot reach the target. Its only static aggressor is level-0 Fido; update.c skips aggression when the player is more than ten levels higher.",
        "Live run 2366 reached source room 19091, found the gardener absent, and returned through the healer without combat; this is temporary reboot-scoped absence, not a permanent route rejection.",
        "Any unexpected combat aborts the probe with flee and healer recovery; live presence, crowd state, and do_consider evidence are required before registering combat behavior.",
    ),
    practice_skill=None,
)


_MIRROR_REALM_GARDENER_HUNT_POLICY = ProgressionPolicy(
    policy_id="mirror-realm-gardener-hunt-21-25",
    minimum_level=21,
    maximum_level=25,
    status="research",
    execution="mirror-realm-gardener-hunt",
    summary=(
        "Use a fresh viable Mirror Realm gardener consideration for one bounded "
        "fight, then return to the Midgaard healer."
    ),
    evidence=(
        *_MIRROR_REALM_GARDENER_RESEARCH_POLICY.evidence,
        "Source special.c: spec_thief skips NPC victims, so it does not steal from the autonomous bot while the gardener is fought as a mobile.",
        "The hunt repeats consider immediately before combat, requires 85% health, no more than one live level above the character, one exact target, no crowd, and one confirmed kill.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)


_SHIRE_BATTLE_MASTER_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="shire-battle-master-probe-26-30",
    minimum_level=26,
    maximum_level=30,
    status="research",
    execution="shire-battle-master-research",
    summary=(
        "Reach and consider the Shire battle master without initiating combat, "
        "then return to the Midgaard healer."
    ),
    evidence=(
        "DD4 source revision d7cb330: mobile 1121, the battle master, resets once in Shire room 1117 with up to three level-5 trainees.",
        "The source prototype is level 25 with normal mobile-level fuzz; source level 23-27 remains within five levels of the registered 26-30 band.",
        "The battle master is sentinel, not aggressive, carries a bardiche, and has spec_guard. The recall-origin route crosses only level-0 Fido, which update.c cannot aggro against a level-26-or-higher character.",
        "This policy permits only live presence, crowd, and do_consider evidence. Any unexpected guard combat aborts the probe with flee and healer recovery.",
    ),
    practice_skill=None,
)


_MIRROR_REALM_GUARDIAN_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="mirror-realm-guardian-probe-26-30",
    minimum_level=26,
    maximum_level=30,
    status="research",
    execution="mirror-realm-guardian-research",
    summary=(
        "Reach and consider the isolated Mirror Realm guardian before enabling "
        "a bounded level-26 to 30 hunt."
    ),
    evidence=(
        "DD4 source revision d7cb330: mobile 19001, the mirror guardian, resets once in Mirror Realm room 19041.",
        "The source prototype is level 23 with normal mobile-level fuzz. Its act flags are sentinel and stay-area, not aggressive, and it has no special procedure.",
        "The source-derived route reaches room 19041 through ordinary exits and two reset-open north doors. Its only static aggressor is level-0 Fido, which cannot aggro a character above level ten.",
        "The target is exact, single-reset, and source-isolated. The probe records live crowd and consider evidence before combat is allowed.",
    ),
    practice_skill=None,
)


_MIRROR_REALM_GUARDIAN_HUNT_POLICY = ProgressionPolicy(
    policy_id="mirror-realm-guardian-hunt-26-30",
    minimum_level=26,
    maximum_level=30,
    status="research",
    execution="mirror-realm-guardian-hunt",
    summary=(
        "Run a one-kill Mirror Guardian hunt only after a fresh viable live "
        "consider result."
    ),
    evidence=(
        *_MIRROR_REALM_GUARDIAN_RESEARCH_POLICY.evidence,
        "The hunt repeats consider immediately before combat, requires 85% health, one exact source-matched target, no crowd, and a single confirmed kill.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)


_GALAXY_CANCER_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="galaxy-cancer-probe-31-35",
    minimum_level=31,
    maximum_level=35,
    status="research",
    execution="galaxy-cancer-research",
    summary=(
        "Reach and consider Cancer in the Galaxy area without initiating combat, "
        "then return to the Midgaard healer."
    ),
    evidence=(
        "DD4 source revision d7cb330: mobile 9319, Cancer, resets once in Galaxy room 9345 and is level 31, sentinel, and not aggressive.",
        "Cancer has spec_cast_cleric and carries the Titanic Shell of Cancer, so this remains a no-combat probe despite its non-aggressive flag.",
        "The source route has aggressive static or reachable mobiles only at levels 0-10. update.c skips their aggression when a character is more than ten levels higher; this gate holds throughout levels 31-35.",
        "This policy records only live route completion, presence, crowd, and do_consider evidence. Any unexpected combat aborts with flee and healer recovery before a combat policy can be considered.",
    ),
    practice_skill=None,
)


_MINOTAUR_GATEKEEPER_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="minotaur-gatekeeper-probe-31-35",
    minimum_level=31,
    maximum_level=35,
    status="research",
    execution="minotaur-gatekeeper-research",
    summary=(
        "Reach and consider the isolated Mahn-Tor Gatekeeper before enabling "
        "a bounded level-31 to 35 hunt."
    ),
    evidence=(
        "DD4 source revision d7cb330: mobile 2318, the Minotaur Gatekeeper, resets once in Mahn-Tor room 2377.",
        "The source prototype is level 25 with normal mobile-level fuzz. Its act flags are sentinel, scavenger, and stay-area, not aggressive, and it has no special procedure.",
        "The source-derived route contains only aggressors whose fuzzed maximum is at least five levels below a level-31 character; one reset-closed, unlocked south door is opened explicitly.",
        "The exact source keyword is gatekeeper. The probe records live presence, crowd, and consider evidence before combat is allowed.",
    ),
    practice_skill=None,
)


_MINOTAUR_GATEKEEPER_HUNT_POLICY = ProgressionPolicy(
    policy_id="minotaur-gatekeeper-hunt-31-35",
    minimum_level=31,
    maximum_level=35,
    status="research",
    execution="minotaur-gatekeeper-hunt",
    summary=(
        "Run a one-kill Minotaur Gatekeeper hunt only after a fresh viable "
        "live consider result."
    ),
    evidence=(
        *_MINOTAUR_GATEKEEPER_RESEARCH_POLICY.evidence,
        "The hunt repeats consider immediately before combat, requires 85% health, one exact source-matched target, no crowd, and a single confirmed kill.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)


_MIRROR_REALM_JERRY_GARCIA_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="mirror-realm-jerry-garcia-probe-36-40",
    minimum_level=36,
    maximum_level=40,
    status="research",
    execution="mirror-realm-jerry-garcia-research",
    summary=(
        "Reach and consider Mirror Realm's Jerry Garcia without initiating "
        "combat, then return to the Midgaard healer."
    ),
    evidence=(
        "DD4 source revision d7cb330: mobile 19068, Jerry Garcia, resets once in Mirror Realm room 19170 and is level 35, sentinel, and not aggressive.",
        "Jerry Garcia has spec_cast_adept and is a stationary healer, so the route remains no-combat research only.",
        "The source path has only level-0 Fido as an aggressive static or reachable mobile. update.c skips aggression when a character is more than ten levels higher; this holds throughout levels 36-40.",
        "This policy records only live route completion, presence, crowd, and do_consider evidence. Any unexpected combat aborts with flee and healer recovery before a combat policy can be considered.",
    ),
    practice_skill=None,
)


_PIT_OFFICIAL_RESEARCH_POLICY = ProgressionPolicy(
    "pit-official-probe-41-45", 41, 45, "research", "pit-official-research",
    "Reach and consider the Pit Official without initiating combat, then return to the Midgaard healer.",
    (
        "DD4 source revision d7cb330: mobile 13700 resets in safe Pit spectator room 13703; it is level 39, sentinel, and not aggressive.",
        "The four-move recall route and its room companions are source-vetted; spec_breath_acid keeps this as no-combat research only.",
        "Any unexpected combat aborts with flee and healer recovery.",
    ), None,
)


_DWARVEN_HOME_CHESS_DWARF_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="dwarven-home-chess-dwarf-probe-46-50",
    minimum_level=46,
    maximum_level=50,
    status="research",
    execution="dwarven-home-chess-dwarf-research",
    summary=(
        "Reach and consider the isolated Dwarven Home chess-room dwarf before "
        "enabling a bounded level-46 to 50 hunt."
    ),
    evidence=(
        "DD4 source revision bf745c3: mobile 20514, the dwarf, resets once "
        "in Dwarven Home room 20530 at source level 46.",
        "The source flags are sentinel and stay-area, with no special "
        "procedure and no source-listed equipment or object drop.",
        "The source-derived route reaches room 20530 through two reset-open "
        "doors; its reachable aggressive mobiles are all at least ten levels "
        "below a level-46 character and cannot replace the registered target.",
        "This first pass records live presence, exact target identity, crowd "
        "state, and do_consider level-difference evidence without initiating "
        "combat.",
    ),
    practice_skill=None,
)


_DWARVEN_HOME_CHESS_DWARF_HUNT_POLICY = ProgressionPolicy(
    policy_id="dwarven-home-chess-dwarf-hunt-46-50",
    minimum_level=46,
    maximum_level=50,
    status="research",
    execution="dwarven-home-chess-dwarf-hunt",
    summary=(
        "Run one bounded chess-room dwarf hunt after a fresh viable "
        "level-difference consider result."
    ),
    evidence=(
        *_DWARVEN_HOME_CHESS_DWARF_RESEARCH_POLICY.evidence,
        "Combat promotion requires a fresh exact consider in the useful "
        "level band, at least 85% health, no more than one live level above "
        "the character, one exact target, and one confirmed kill.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)


_MIRROR_REALM_STORN_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="mirror-realm-storn-probe-46-50",
    minimum_level=46,
    maximum_level=50,
    status="research",
    execution="mirror-realm-storn-research",
    summary=(
        "Use the isolated Mirror Realm assassin as a second level-46 to 50 "
        "probe after the Dwarven Home candidate is unavailable."
    ),
    evidence=(
        "DD4 source revision bf745c3: mobile 19034, Storn the assassin, "
        "resets once in Mirror Realm room 19114 at source level 45.",
        "Storn is sentinel and stay-area, has no source special procedure, "
        "and equips a blood-red dagger; the route has only trivial low-level "
        "reachable aggressors before the isolated target room.",
        "The probe remains no-combat until live presence, exact identity, "
        "crowd state, and do_consider level-difference evidence are recorded.",
    ),
    practice_skill=None,
)


_MIRROR_REALM_STORN_HUNT_POLICY = ProgressionPolicy(
    policy_id="mirror-realm-storn-hunt-46-50",
    minimum_level=46,
    maximum_level=50,
    status="research",
    execution="mirror-realm-storn-hunt",
    summary=(
        "Run one bounded Storn hunt after a fresh viable level-difference "
        "consider result."
    ),
    evidence=(
        *_MIRROR_REALM_STORN_RESEARCH_POLICY.evidence,
        "Combat promotion requires a fresh exact consider in the useful "
        "level band, at least 85% health, no more than one live level above "
        "the character, one exact target, and one confirmed kill.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)


_DARKWOOD_STRANGE_MIST_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="darkwood-strange-mist-probe-51-55",
    minimum_level=51,
    maximum_level=55,
    status="research",
    execution="darkwood-strange-mist-research",
    summary=(
        "Reach and consider the isolated Darkwood strange mist before "
        "enabling a bounded level-51 to 55 hunt."
    ),
    evidence=(
        "DD4 source revision bf745c3: mobile 11200, the strange mist, "
        "resets once in Darkwood room 11211 at source level 50.",
        "The source flags are sentinel and stay-area, with no special "
        "procedure and no source-listed equipment or object drop.",
        "The source-derived route reaches room 11211 through the Darkwood "
        "approach; its only reachable aggressive mobiles are level-0 Fido and "
        "level-7 drow scouts, below the level-difference danger band here.",
        "The source room line canonicalizes to `strange mist`; the probe "
        "records exact TARGETMODE identity, crowd state, and do_consider "
        "level-difference evidence without initiating combat.",
    ),
    practice_skill=None,
)


_DARKWOOD_STRANGE_MIST_HUNT_POLICY = ProgressionPolicy(
    policy_id="darkwood-strange-mist-hunt-51-55",
    minimum_level=51,
    maximum_level=55,
    status="research",
    execution="darkwood-strange-mist-hunt",
    summary=(
        "Run one bounded strange mist hunt after a fresh viable "
        "level-difference consider result."
    ),
    evidence=(
        *_DARKWOOD_STRANGE_MIST_RESEARCH_POLICY.evidence,
        "Combat promotion requires a fresh exact consider in the useful "
        "level band, at least 85% health, no more than one live level above "
        "the character, one exact target, and one confirmed kill.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)


_DWARVEN_HOME_GAMBLER_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="dwarven-home-gambler-probe-51-55",
    minimum_level=51,
    maximum_level=55,
    status="research",
    execution="dwarven-home-gambler-research",
    summary=(
        "Use the isolated Dwarven Home gambler as a second level-51 to 55 "
        "probe after the Darkwood candidate is unavailable."
    ),
    evidence=(
        "DD4 source revision bf745c3: mobile 20515, the dwarven gambler, "
        "resets once in Dwarven Home room 20531 at source level 49.",
        "The source flags are sentinel and stay-area, with no special "
        "procedure and no source-listed equipment or object drop.",
        "The source-derived route reaches room 20531 through two reset-open "
        "doors and a source-isolated room; reachable aggressive mobiles are "
        "below the level-difference danger band for this policy.",
        "The live source room line canonicalizes the target to `dwarf`; the "
        "probe records exact TARGETMODE identity, crowd state, and consider "
        "level-difference evidence without initiating combat.",
    ),
    practice_skill=None,
)


_DWARVEN_HOME_GAMBLER_HUNT_POLICY = ProgressionPolicy(
    policy_id="dwarven-home-gambler-hunt-51-55",
    minimum_level=51,
    maximum_level=55,
    status="research",
    execution="dwarven-home-gambler-hunt",
    summary=(
        "Run one bounded Dwarven Home gambler hunt after a fresh viable "
        "level-difference consider result."
    ),
    evidence=(
        *_DWARVEN_HOME_GAMBLER_RESEARCH_POLICY.evidence,
        "Combat promotion requires a fresh exact consider in the useful "
        "level band, at least 85% health, no more than one live level above "
        "the character, one exact target, and one confirmed kill.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)


_DWARVEN_HOME_MASTER_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="dwarven-home-master-probe-56-60",
    minimum_level=56,
    maximum_level=60,
    status="research",
    execution="dwarven-home-master-research",
    summary=(
        "Reach and consider the isolated Dwarven Home master of the house "
        "before enabling a bounded level-56 to 60 hunt."
    ),
    evidence=(
        "DD4 source revision bf745c3: mobile 20517, the master of the house, "
        "resets once in Dwarven Home room 20537 at source level 55.",
        "The source flags are sentinel and stay-area, with neutral alignment, "
        "no special procedure, no room companion, and a source-equipped "
        "dwarven dagger.",
        "The source-derived route reaches room 20537 through two reset-open "
        "doors; its reachable aggressive mobiles are below the useful "
        "level-difference band for levels 56 through 60.",
        "The source room line canonicalizes to `master of the house`; the "
        "probe records exact TARGETMODE identity, crowd state, and the "
        "do_consider level-difference result without initiating combat.",
    ),
    practice_skill=None,
)


_DWARVEN_HOME_MASTER_HUNT_POLICY = ProgressionPolicy(
    policy_id="dwarven-home-master-hunt-56-60",
    minimum_level=56,
    maximum_level=60,
    status="research",
    execution="dwarven-home-master-hunt",
    summary=(
        "Run one bounded Dwarven Home master hunt after a fresh viable "
        "level-difference consider result."
    ),
    evidence=(
        *_DWARVEN_HOME_MASTER_RESEARCH_POLICY.evidence,
        "Combat promotion requires a fresh exact consider in the useful "
        "level band, at least 85% health, no more than one live level above "
        "the character, one exact target, and one confirmed kill.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)


_VAMPIRE_HIVE_WOUNDED_VAMPIRE_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="vampire-hive-wounded-vampire-probe-61-65",
    minimum_level=61,
    maximum_level=65,
    status="research",
    execution="vampire-hive-wounded-vampire-research",
    summary=(
        "Reach the Vamp Hive wounded vampire reset and consider the exact "
        "target before enabling a bounded level-61 to 65 hunt."
    ),
    evidence=(
        "DD4 source revision bf745c3: mobile 25652, the wounded vampire, "
        "resets once in Vamp Hive room 25641 at source level 59.",
        "The source mobile is stay-area, non-aggressive, has no special "
        "procedure, and has no source room companion; its source reset equips "
        "sharp fangs, black cloth trousers, and an elegant black cane, and "
        "loads a scrap of parchment.",
        "The source-derived route reaches room 25641 through three reset-open "
        "doors; source ranking finds only lower-band route hazards. Because "
        "the mobile wanders, the probe issues `where vampire` before the "
        "bounded reset-room search.",
        "The source room line canonicalizes to `wounded vampire`; the probe "
        "records exact TARGETMODE identity, crowd state, and the do_consider "
        "level-difference result without initiating combat.",
    ),
    practice_skill=None,
)


_VAMPIRE_HIVE_WOUNDED_VAMPIRE_HUNT_POLICY = ProgressionPolicy(
    policy_id="vampire-hive-wounded-vampire-hunt-61-65",
    minimum_level=61,
    maximum_level=65,
    status="research",
    execution="vampire-hive-wounded-vampire-hunt",
    summary=(
        "Run one bounded wounded vampire hunt after a fresh viable "
        "level-difference consider result."
    ),
    evidence=(
        *_VAMPIRE_HIVE_WOUNDED_VAMPIRE_RESEARCH_POLICY.evidence,
        "Combat promotion requires a fresh exact consider in the useful "
        "level band, at least 85% health, no more than one live level above "
        "the character, one exact target, and one confirmed kill.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)


_TABERNACLE_HULKING_BEAST_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="tabernacle-hulking-beast-probe-66-70",
    minimum_level=66,
    maximum_level=70,
    status="research",
    execution="tabernacle-hulking-beast-research",
    summary=(
        "Reach and consider the isolated Tabernacle hulking beast before "
        "enabling a bounded level-66 to 70 hunt."
    ),
    evidence=(
        "DD4 source revision bf745c3: mobile 39013, a hulking beast, resets "
        "once in Tabernacle room 39016 at source level 65.",
        "The source mobile is sentinel and non-aggressive, has neutral "
        "alignment, no special procedure, no source equipment, and no room "
        "companion.",
        "The source-derived route reaches room 39016 through one reset-open "
        "door; source ranking finds only lower-band route hazards for levels "
        "66 through 70.",
        "The source room line canonicalizes to `hulking beast`; the probe "
        "records exact TARGETMODE identity, crowd state, and the do_consider "
        "level-difference result without initiating combat.",
    ),
    practice_skill=None,
)


_TABERNACLE_HULKING_BEAST_HUNT_POLICY = ProgressionPolicy(
    policy_id="tabernacle-hulking-beast-hunt-66-70",
    minimum_level=66,
    maximum_level=70,
    status="research",
    execution="tabernacle-hulking-beast-hunt",
    summary=(
        "Run one bounded hulking beast hunt after a fresh viable "
        "level-difference consider result."
    ),
    evidence=(
        *_TABERNACLE_HULKING_BEAST_RESEARCH_POLICY.evidence,
        "Combat promotion requires a fresh exact consider in the useful "
        "level band, at least 85% health, no more than one live level above "
        "the character, one exact target, and one confirmed kill.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)


_PIRATES_SEAS_RASTAFARIANS_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="pirates-seas-rastafarians-probe-71-75",
    minimum_level=71,
    maximum_level=75,
    status="research",
    execution="pirates-seas-rastafarians-research",
    summary=(
        "Reach the Pirates Seas reset and consider the exact wandering "
        "Rastafarians target before enabling a bounded level-71 to 75 hunt."
    ),
    evidence=(
        "DD4 source revision bf745c3: mobile 17099, the Rastafarians, "
        "resets once in Pirates Seas room 17141 at source level 70 with a "
        "conservative 68-72 live range.",
        "The source mobile has no aggressive, sentinel, or stay-area flag, "
        "no special procedure, and no source room companion. Its reset loads "
        "the source-listed dreddlocks and drink-related objects; the policy "
        "is registered primarily as an XP-band probe rather than a loot loop.",
        "The source-derived recall route reaches room 17141 through two "
        "reset-open doors and includes lower-band route hazards plus wandering "
        "mobiles. Those hazards remain hard abort conditions; they are not "
        "deliberate XP targets.",
        "Because the target can wander, the probe issues `where rastafarians` "
        "and searches only the registered reset room. The all-area source "
        "index binds its TARGETMODE short line to canonical identity "
        "`rastafarians`.",
        "The first pass records exact identity, isolation, and the live "
        "do_consider level-difference result without initiating combat. The "
        "level difference, not the target-versus-character HP wording, decides "
        "whether the target is inside the useful XP band.",
    ),
    practice_skill=None,
)


_PIRATES_SEAS_RASTAFARIANS_HUNT_POLICY = ProgressionPolicy(
    policy_id="pirates-seas-rastafarians-hunt-71-75",
    minimum_level=71,
    maximum_level=75,
    status="research",
    execution="pirates-seas-rastafarians-hunt",
    summary=(
        "Run one bounded Rastafarians hunt after a fresh viable "
        "level-difference consider result."
    ),
    evidence=(
        *_PIRATES_SEAS_RASTAFARIANS_RESEARCH_POLICY.evidence,
        "Combat promotion requires a fresh exact consider in the useful "
        "level band, at least 85% health, no more than one live level above "
        "the character, one exact isolated target, and one confirmed kill.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)


_GHOST_TOWN_CRYPT_THING_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="ghost-town-crypt-thing-probe-76",
    minimum_level=76,
    maximum_level=76,
    status="research",
    execution="ghost-town-crypt-thing-research",
    summary=(
        "Reach the Ghost Town crypt thing reset and consider the exact "
        "target before enabling a bounded level-76 hunt."
    ),
    evidence=(
        "DD4 source revision 1b759f5: mobile 8809, a crypt thing, resets "
        "once in Ghost Town room 8850 at source level 73 with a conservative "
        "71-75 live range.",
        "The source mobile is sentinel, stay-area, and non-aggressive, with "
        "no special procedure and no source room companion. The reset carries "
        "a source-listed circlet; the first policy is an XP-band probe, not a "
        "loot-dependent route.",
        "The source-derived route reaches room 8850 through four reset-open "
        "doors. Its lower-band route hazards, including the Ghost Town water "
        "weird branch, remain hard abort conditions rather than deliberate XP "
        "targets.",
        "The source index binds both the room sentence and TARGETMODE short "
        "line to canonical identity `crypt thing`. The probe records exact "
        "identity, isolation, and the live do_consider level-difference result "
        "without initiating combat.",
        "Level difference determines useful XP eligibility; the separate HP "
        "wording in consider is not used as the XP-band decision.",
    ),
    practice_skill=None,
)


_GHOST_TOWN_CRYPT_THING_HUNT_POLICY = ProgressionPolicy(
    policy_id="ghost-town-crypt-thing-hunt-76",
    minimum_level=76,
    maximum_level=76,
    status="research",
    execution="ghost-town-crypt-thing-hunt",
    summary=(
        "Run one bounded crypt thing hunt after a fresh viable "
        "level-difference consider result."
    ),
    evidence=(
        *_GHOST_TOWN_CRYPT_THING_RESEARCH_POLICY.evidence,
        "Combat promotion requires a fresh exact consider in the useful "
        "level band, at least 85% health, no more than one live level above "
        "the character, one exact isolated target, and one confirmed kill.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)


_GHOST_TOWN_RETRIEVER_RESEARCH_POLICY = ProgressionPolicy(
    policy_id="ghost-town-retriever-probe-77-80",
    minimum_level=77,
    maximum_level=80,
    status="research",
    execution="ghost-town-retriever-research",
    summary=(
        "Reach the Ghost Town retriever reset and consider the exact target "
        "before enabling a bounded level-77 to 80 hunt."
    ),
    evidence=(
        "DD4 source revision 1b759f5: mobile 8829, a retriever, resets once "
        "in Ghost Town room 8843 at source level 77 with a conservative 75-79 "
        "live range.",
        "The source mobile is sentinel, stay-area, and non-aggressive, with "
        "no special procedure, no source room companion, and no source-listed "
        "equipment drop.",
        "The source-derived route reaches room 8843 through two reset-open "
        "doors. Lower-band route hazards and the adjacent Ghost Town water "
        "weird branch remain hard abort conditions; the retriever itself is "
        "not selected until its exact room is isolated.",
        "The source index binds the room sentence and TARGETMODE short line to "
        "canonical identity `retriever`. The probe records a live "
        "do_consider level-difference result without initiating combat.",
        "Level difference determines useful XP eligibility; the separate HP "
        "wording in consider is not used as the XP-band decision.",
    ),
    practice_skill=None,
)


_GHOST_TOWN_RETRIEVER_HUNT_POLICY = ProgressionPolicy(
    policy_id="ghost-town-retriever-hunt-77-80",
    minimum_level=77,
    maximum_level=80,
    status="research",
    execution="ghost-town-retriever-hunt",
    summary=(
        "Run one bounded retriever hunt after a fresh viable level-difference "
        "consider result."
    ),
    evidence=(
        *_GHOST_TOWN_RETRIEVER_RESEARCH_POLICY.evidence,
        "Combat promotion requires a fresh exact consider in the useful "
        "level band, at least 85% health, no more than one live level above "
        "the character, one exact isolated target, and one confirmed kill.",
    ),
    practice_skill=None,
    segment_kill_limit=1,
)


def policy_for(
    level: int | float | None,
    character_class: str,
    *,
    subclass: str | None = None,
    has_large_sack: bool = False,
    has_sellable_loot: bool = False,
    needs_coin_deposit: bool = False,
    needs_capacity_relief: bool = False,
    has_food: bool = True,
    has_weapon: bool = True,
    needs_basic_gear: bool = False,
    needs_body_gear_recovery: bool = False,
    needs_school_wrist_float: bool = False,
    needs_gremlin_waist: bool = False,
    needs_daycare_ring: bool = False,
    needs_war_dog_collar: bool = False,
    needs_foundry_set_circlet: bool = False,
    needs_intermediate_piercing_weapon_upgrade: bool = False,
    intermediate_piercing_weapon_upgrade_attempted: bool = False,
    needs_piercing_weapon_upgrade: bool = False,
    piercing_weapon_upgrade_attempted: bool = False,
    needs_piercing_weapon: bool = False,
    needs_pounding_weapon: bool = False,
    movement_available: int = 0,
    movement_capacity: int = 0,
    has_sanctuary_potion: bool = False,
    has_flight: bool = True,
    can_attempt_flight_purchase: bool = False,
    flight_purchase_failed: bool = False,
    boot_kill_counts: Mapping[str, int] | None = None,
    policy_xp_deltas: Mapping[str, int] | None = None,
    research_results: Mapping[str, Mapping[str, object]] | None = None,
    excluded_policy_ids: frozenset[str] = frozenset(),
    world_boot_id: str | int | None = None,
    stalled_segments: int = 0,
    last_policy_id: str | None = None,
    last_fastwalk_abort_reason: str | None = None,
) -> ProgressionPolicy:
    context = ProgressionContext.from_values(
        level,
        character_class,
        subclass=subclass,
        has_large_sack=has_large_sack,
        has_sellable_loot=has_sellable_loot,
        needs_coin_deposit=needs_coin_deposit,
        needs_capacity_relief=needs_capacity_relief,
        has_food=has_food,
        has_weapon=has_weapon,
        needs_basic_gear=needs_basic_gear,
        needs_body_gear_recovery=needs_body_gear_recovery,
        needs_school_wrist_float=needs_school_wrist_float,
        needs_gremlin_waist=needs_gremlin_waist,
        needs_daycare_ring=needs_daycare_ring,
        needs_war_dog_collar=needs_war_dog_collar,
        needs_foundry_set_circlet=needs_foundry_set_circlet,
        needs_intermediate_piercing_weapon_upgrade=(
            needs_intermediate_piercing_weapon_upgrade
        ),
        intermediate_piercing_weapon_upgrade_attempted=(
            intermediate_piercing_weapon_upgrade_attempted
        ),
        needs_piercing_weapon_upgrade=needs_piercing_weapon_upgrade,
        piercing_weapon_upgrade_attempted=piercing_weapon_upgrade_attempted,
        needs_piercing_weapon=needs_piercing_weapon,
        needs_pounding_weapon=needs_pounding_weapon,
        movement_available=movement_available,
        movement_capacity=movement_capacity,
        has_sanctuary_potion=has_sanctuary_potion,
        has_flight=has_flight,
        can_attempt_flight_purchase=can_attempt_flight_purchase,
        flight_purchase_failed=flight_purchase_failed,
        boot_kill_counts=boot_kill_counts,
        policy_xp_deltas=policy_xp_deltas,
        research_results=research_results,
        excluded_policy_ids=excluded_policy_ids,
        world_boot_id=world_boot_id,
        stalled_segments=stalled_segments,
        last_policy_id=last_policy_id,
        last_fastwalk_abort_reason=last_fastwalk_abort_reason,
    )
    selected = select_policy(context)
    if selected.policy_id not in context.excluded_policy_ids:
        return selected
    return replace(
        _UNAVAILABLE_POLICY,
        minimum_level=context.level,
        maximum_level=context.level,
        summary=(
            f"{selected.policy_id} is excluded by live consider evidence for "
            "this character level and reboot; wait for a level or reboot "
            "change, or register another verified policy."
        ),
    )


def select_policy(context: ProgressionContext) -> ProgressionPolicy:
    normalized_level = context.level
    if normalized_level < 2:
        return _STARTER_POLICY
    if context.has_sellable_loot:
        return _LIQUIDATE_LOOT_POLICY
    if context.needs_coin_deposit:
        return _BANK_EXCESS_COIN_POLICY
    if context.needs_capacity_relief:
        return _VAULT_SPARE_GEAR_POLICY
    if not context.has_food:
        return _RESTOCK_POLICY
    if not context.has_weapon:
        return _REARM_WEAPON_POLICY
    if context.needs_piercing_weapon:
        return _REARM_WEAPON_POLICY
    if context.needs_pounding_weapon:
        return _REARM_WEAPON_POLICY
    if context.needs_basic_gear:
        return _OUTFIT_BASIC_GEAR_POLICY
    if context.needs_body_gear_recovery:
        return _RECOVER_BASIC_BODY_POLICY
    if context.needs_school_wrist_float:
        return _RECOVER_SCHOOL_WRIST_FLOAT_POLICY
    if context.needs_gremlin_waist:
        return _RECOVER_GREMLIN_WAIST_POLICY
    if context.needs_daycare_ring:
        return _RECOVER_DAYCARE_RING_POLICY
    if (
        normalized_level >= 6
        and context.progression_track == "verified-field-martial"
        and context.needs_foundry_set_circlet
    ):
        return _RECOVER_FOUNDRY_SET_CIRCLET_POLICY
    if context.needs_war_dog_collar:
        return _RECOVER_WAR_DOG_COLLAR_POLICY
    if normalized_level < 6:
        return replace(
            _MUD_SCHOOL_ARENA_POLICY,
            practice_skill=context.practice_skill,
        )
    if normalized_level == 6:
        return replace(
            _MUD_SCHOOL_RESEARCH_POLICY,
            practice_skill=context.practice_skill,
        )
    field_caster = context.progression_track == "verified-field-caster"
    field_martial = context.progression_track == "verified-field-martial"
    thief_weapon_upgrade_band = (
        context.character_class == "thief"
        and 10 <= normalized_level <= 29
    )
    if (
        thief_weapon_upgrade_band
        and context.needs_intermediate_piercing_weapon_upgrade
        and not context.intermediate_piercing_weapon_upgrade_attempted
    ):
        return replace(
            _THALOS_LONG_DAGGER_UPGRADE_POLICY,
            practice_skill=context.practice_skill,
        )
    if (
        thief_weapon_upgrade_band
        and context.needs_piercing_weapon_upgrade
        and not context.piercing_weapon_upgrade_attempted
    ):
        if (
            not context.has_flight
            and max(
                context.movement_available,
                context.movement_capacity,
            )
            < _FOREST_BEAR_CLAWS_MINIMUM_NONFLIGHT_MOVE
        ):
            if (
                context.can_attempt_flight_purchase
                and not context.flight_purchase_failed
            ):
                return _BUY_FLIGHT_POLICY
        else:
            return replace(
                _FOREST_BEAR_CLAWS_UPGRADE_POLICY,
                practice_skill=context.practice_skill,
            )
    if field_martial and normalized_level == 8:
        if (
            not context.has_flight
            and context.can_attempt_flight_purchase
            and not context.flight_purchase_failed
        ):
            return _BUY_FLIGHT_POLICY
        if (
            context.last_policy_id
            == _GNOME_GUARD_LEVEL_EIGHT_POLICY.policy_id
        ):
            return replace(
                _DAYCARE_ARMED_GUARD_LEVEL_EIGHT_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _DAYCARE_ARMED_GUARD_LEVEL_EIGHT_POLICY.policy_id
        ):
            return replace(
                _AMBUSH_MARTIAL_LEVEL_EIGHT_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _AMBUSH_MARTIAL_LEVEL_EIGHT_POLICY.policy_id
        ):
            return replace(
                _CIRCUS_FREAK_SHOW_LEVEL_EIGHT_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _FLESHMONGER_GUARD_LEVEL_EIGHT_RESEARCH_POLICY.policy_id
        ):
            return replace(
                _CIRCUS_FREAK_SHOW_LEVEL_EIGHT_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _CULT_FANATIC_LEVEL_EIGHT_RESEARCH_POLICY.policy_id
        ):
            return replace(
                _CIRCUS_FREAK_SHOW_LEVEL_EIGHT_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _CIRCUS_FREAK_SHOW_LEVEL_EIGHT_POLICY.policy_id
        ):
            return replace(
                _MORIA_LARGE_ORC_LEVEL_EIGHT_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _MORIA_LARGE_ORC_LEVEL_EIGHT_POLICY.policy_id
        ):
            return replace(
                _GNOME_GUARD_LEVEL_EIGHT_POLICY,
                practice_skill=context.practice_skill,
            )
        return replace(
            _CIRCUS_FREAK_SHOW_LEVEL_EIGHT_POLICY,
            practice_skill=context.practice_skill,
        )
    if field_martial and normalized_level == 9:
        if (
            not context.has_flight
            and context.can_attempt_flight_purchase
            and not context.flight_purchase_failed
        ):
            return _BUY_FLIGHT_POLICY
        rotation = (
            _AMBUSH_MARTIAL_LEVEL_NINE_POLICY,
            _CIRCUS_FREAK_SHOW_LEVEL_NINE_POLICY,
            _MORIA_LARGE_ORC_LEVEL_NINE_POLICY,
            _GNOME_GUARD_LEVEL_NINE_POLICY,
            _DAYCARE_ARMED_GUARD_LEVEL_NINE_POLICY,
        )
        previous_indexes = {
            _AMBUSH_MARTIAL_LEVEL_EIGHT_POLICY.policy_id: 0,
            _AMBUSH_MARTIAL_LEVEL_NINE_POLICY.policy_id: 0,
            _CIRCUS_FREAK_SHOW_LEVEL_EIGHT_POLICY.policy_id: 1,
            _CIRCUS_FREAK_SHOW_LEVEL_NINE_POLICY.policy_id: 1,
            _MORIA_LARGE_ORC_LEVEL_EIGHT_POLICY.policy_id: 2,
            _MORIA_LARGE_ORC_LEVEL_NINE_POLICY.policy_id: 2,
            _GNOME_GUARD_LEVEL_EIGHT_POLICY.policy_id: 3,
            _GNOME_GUARD_LEVEL_NINE_POLICY.policy_id: 3,
            _DAYCARE_ARMED_GUARD_LEVEL_EIGHT_POLICY.policy_id: 4,
            _DAYCARE_ARMED_GUARD_LEVEL_NINE_POLICY.policy_id: 4,
        }
        previous_index = previous_indexes.get(context.last_policy_id)
        if previous_index is not None:
            policy = _next_productive_policy(
                rotation,
                previous_index=previous_index,
                xp_deltas=context.policy_xp_deltas,
            )
            return replace(policy, practice_skill=context.practice_skill)
        return replace(
            _CIRCUS_FREAK_SHOW_LEVEL_NINE_POLICY,
            practice_skill=context.practice_skill,
        )
    if field_caster and 8 <= normalized_level < 10:
        if not context.has_large_sack:
            return _MIDENNIR_SACK_POLICY
        if normalized_level == 8:
            if context.has_sanctuary_potion:
                return _AMBUSH_PROTECTED_LEVEL_EIGHT_POLICY
            rotation = (
                _AMBUSH_LEVEL_EIGHT_POLICY,
                _MIDENNIR_LEVEL_EIGHT_POLICY,
                _MORIA_LARGE_ORC_LEVEL_EIGHT_POLICY,
                _CIRCUS_FREAK_SHOW_LEVEL_EIGHT_POLICY,
                _GNOME_GUARD_LEVEL_EIGHT_POLICY,
                _DAYCARE_ARMED_GUARD_LEVEL_EIGHT_POLICY,
            )
            previous_indexes = {
                policy.policy_id: index
                for index, policy in enumerate(rotation)
            }
            previous_index = previous_indexes.get(context.last_policy_id)
            recent_xp = (context.policy_xp_deltas or {}).get(
                context.last_policy_id or ""
            )
            if (
                previous_index is not None
                and recent_xp is not None
                and recent_xp < _MEANINGFUL_FIELD_SEGMENT_XP
            ):
                policy = _next_productive_policy(
                    rotation,
                    previous_index=previous_index,
                    xp_deltas=context.policy_xp_deltas,
                )
                return replace(policy, practice_skill=context.practice_skill)
            if (
                previous_index is not None
                and previous_index >= 2
                and recent_xp is not None
            ):
                return replace(
                    rotation[previous_index],
                    practice_skill=context.practice_skill,
                )
            war_dog_kills = _boot_kill_count(
                context.boot_kill_counts, "war dog"
            )
            goblin_kills = _boot_kill_count(context.boot_kill_counts, "goblin")
            if (
                context.stalled_segments > 0
                and context.last_policy_id == _AMBUSH_LEVEL_EIGHT_POLICY.policy_id
            ):
                return _MIDENNIR_LEVEL_EIGHT_POLICY
            if (
                context.stalled_segments > 0
                and context.last_policy_id == _MIDENNIR_LEVEL_EIGHT_POLICY.policy_id
            ):
                return _AMBUSH_LEVEL_EIGHT_POLICY
            if (
                context.stalled_segments % 2 == 0
                and war_dog_kills >= 5
                and goblin_kills < war_dog_kills
            ):
                return _MIDENNIR_LEVEL_EIGHT_POLICY
            return _AMBUSH_LEVEL_EIGHT_POLICY
        if (
            not context.has_flight
            and context.can_attempt_flight_purchase
            and not context.flight_purchase_failed
        ):
            return _BUY_FLIGHT_POLICY
        if context.has_sanctuary_potion:
            protected_recent_xp = (context.policy_xp_deltas or {}).get(
                _AMBUSH_VILE_LEVEL_NINE_POLICY.policy_id
            )
            if (
                context.last_policy_id
                == _AMBUSH_VILE_LEVEL_NINE_POLICY.policy_id
                and protected_recent_xp is not None
                and protected_recent_xp < _MEANINGFUL_FIELD_SEGMENT_XP
            ):
                return replace(
                    _CIRCUS_FREAK_SHOW_LEVEL_NINE_POLICY,
                    practice_skill=context.practice_skill,
                )
            return _AMBUSH_VILE_LEVEL_NINE_POLICY
        large_hobgoblin_kills = _boot_kill_count(
            context.boot_kill_counts, "large hobgoblin"
        )
        vile_goblin_kills = _boot_kill_count(
            context.boot_kill_counts, "vile goblin"
        )
        exterior_kills = (
            _boot_kill_count(context.boot_kill_counts, "war dog")
            + _boot_kill_count(context.boot_kill_counts, "wounded goblin")
        )
        if (
            context.boot_kill_counts
            and context.stalled_segments == 0
            and (
                vile_goblin_kills >= large_hobgoblin_kills > 0
                or exterior_kills >= 4
            )
            ):
            if (
                not context.has_flight
                and context.can_attempt_flight_purchase
                and not context.flight_purchase_failed
            ):
                return _BUY_FLIGHT_POLICY
            return _MORIA_SANCTUARY_LEVEL_NINE_POLICY
        fallback_rotation = (
            _AMBUSH_LEVEL_NINE_POLICY,
            _CIRCUS_FREAK_SHOW_LEVEL_NINE_POLICY,
            _MORIA_LARGE_ORC_LEVEL_NINE_POLICY,
            _GNOME_GUARD_LEVEL_NINE_POLICY,
            _DAYCARE_ARMED_GUARD_LEVEL_NINE_POLICY,
        )
        previous_indexes = {
            policy.policy_id: index
            for index, policy in enumerate(fallback_rotation)
        }
        previous_index = previous_indexes.get(context.last_policy_id)
        recent_xp = (context.policy_xp_deltas or {}).get(
            context.last_policy_id or ""
        )
        if (
            previous_index is not None
            and recent_xp is not None
            and recent_xp < _MEANINGFUL_FIELD_SEGMENT_XP
        ):
            policy = _next_productive_policy(
                fallback_rotation,
                previous_index=previous_index,
                xp_deltas=context.policy_xp_deltas,
            )
            return replace(policy, practice_skill=context.practice_skill)
        return _AMBUSH_LEVEL_NINE_POLICY
    if field_caster and normalized_level == 10:
        if (
            not context.has_flight
            and context.can_attempt_flight_purchase
            and not context.flight_purchase_failed
        ):
            return _BUY_FLIGHT_POLICY
        completed = context.policy_xp_deltas or {}
        if _FLESHMONGER_GUARD_LEVEL_TEN_RESEARCH_POLICY.policy_id not in completed:
            return replace(
                _FLESHMONGER_GUARD_LEVEL_TEN_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
        if context.has_sanctuary_potion:
            raider_kills = _boot_kill_count(
                context.boot_kill_counts, "goblin raider"
            )
            vile_goblin_kills = _boot_kill_count(
                context.boot_kill_counts, "vile goblin"
            )
            if raider_kills <= vile_goblin_kills:
                return _AMBUSH_RAIDER_LEVEL_TEN_POLICY
            return _AMBUSH_VILE_LEVEL_TEN_POLICY
        if (
            context.last_policy_id == _MORIA_SANCTUARY_LEVEL_TEN_POLICY.policy_id
            and completed.get(_MORIA_SANCTUARY_LEVEL_TEN_POLICY.policy_id) == 0
        ):
            mage_guard_id = _FLESHMONGER_MAGE_GUARD_LEVEL_TEN_RESEARCH_POLICY.policy_id
            if mage_guard_id not in completed:
                return replace(
                    _FLESHMONGER_MAGE_GUARD_LEVEL_TEN_RESEARCH_POLICY,
                    practice_skill=context.practice_skill,
                )
            mage_guard_xp = completed.get(mage_guard_id)
            orc_research_id = _MORIA_LARGE_ORC_MAGE_LEVEL_TEN_RESEARCH_POLICY.policy_id
            orc_research_xp = completed.get(orc_research_id)
            if mage_guard_xp is not None and mage_guard_xp > 0:
                if orc_research_xp is None:
                    return replace(
                        _MORIA_LARGE_ORC_MAGE_LEVEL_TEN_RESEARCH_POLICY,
                        practice_skill=context.practice_skill,
                    )
                if orc_research_xp > 0:
                    return replace(
                        _MORIA_LARGE_ORC_MAGE_LEVEL_TEN_POLICY,
                        practice_skill=context.practice_skill,
                    )
            elif orc_research_xp is None:
                return replace(
                    _MORIA_LARGE_ORC_MAGE_LEVEL_TEN_RESEARCH_POLICY,
                    practice_skill=context.practice_skill,
                )
            elif orc_research_xp > 0:
                return replace(
                    _MORIA_LARGE_ORC_MAGE_LEVEL_TEN_POLICY,
                    practice_skill=context.practice_skill,
                )
            return replace(
                _UNAVAILABLE_POLICY,
                minimum_level=10,
                maximum_level=11,
                summary=(
                    "The level-10 mage has exhausted the current Moria and "
                    "Fleshmonger research options without new XP; review the "
                    "live evidence before repeating either route."
                ),
                evidence=(
                    *_FLESHMONGER_MAGE_GUARD_LEVEL_TEN_RESEARCH_POLICY.evidence,
                    "Both level-10 field-caster routes require fresh live "
                    "evidence before another attempt.",
                ),
                practice_skill=context.practice_skill,
            )
        mage_guard_id = _FLESHMONGER_MAGE_GUARD_LEVEL_TEN_RESEARCH_POLICY.policy_id
        if (
            context.last_policy_id == mage_guard_id
            and completed.get(mage_guard_id) == 0
        ):
            orc_research_id = _MORIA_LARGE_ORC_MAGE_LEVEL_TEN_RESEARCH_POLICY.policy_id
            orc_research_xp = completed.get(orc_research_id)
            if orc_research_xp is None:
                return replace(
                    _MORIA_LARGE_ORC_MAGE_LEVEL_TEN_RESEARCH_POLICY,
                    practice_skill=context.practice_skill,
                )
            if orc_research_xp > 0:
                return replace(
                    _MORIA_LARGE_ORC_MAGE_LEVEL_TEN_POLICY,
                    practice_skill=context.practice_skill,
                )
            return replace(
                _UNAVAILABLE_POLICY,
                minimum_level=10,
                maximum_level=11,
                summary=(
                    "The level-10 mage guard research result was nonviable and "
                    "the Moria acquisition was already empty; review live "
                    "evidence before another attempt."
                ),
                evidence=_FLESHMONGER_MAGE_GUARD_LEVEL_TEN_RESEARCH_POLICY.evidence,
                practice_skill=context.practice_skill,
            )
        orc_research_id = _MORIA_LARGE_ORC_MAGE_LEVEL_TEN_RESEARCH_POLICY.policy_id
        if context.last_policy_id == orc_research_id:
            if completed.get(orc_research_id, 0) > 0:
                return replace(
                    _MORIA_LARGE_ORC_MAGE_LEVEL_TEN_POLICY,
                    practice_skill=context.practice_skill,
                )
            absent_result = (context.research_results or {}).get(orc_research_id)
            if (
                isinstance(absent_result, Mapping)
                and absent_result.get("absent") is True
                and absent_result.get("boot_id") == context.world_boot_id
            ):
                return replace(
                    _MORIA_LARGE_ORC_MAGE_LEVEL_TEN_RESEARCH_POLICY,
                    practice_skill=context.practice_skill,
                )
            return replace(
                _UNAVAILABLE_POLICY,
                minimum_level=10,
                maximum_level=11,
                summary=(
                    "The level-10 mage Moria large-orc probe produced no XP; "
                    "wait for a new area state or collect fresh evidence before "
                    "repeating it."
                ),
                evidence=_MORIA_LARGE_ORC_MAGE_LEVEL_TEN_RESEARCH_POLICY.evidence,
                practice_skill=context.practice_skill,
            )
        return _MORIA_SANCTUARY_LEVEL_TEN_POLICY
    if normalized_level == 10 and context.character_class in {
        "cleric",
        "psionic",
        "shifter",
        "brawler",
        "ranger",
        "smithy",
    }:
        completed = context.policy_xp_deltas or {}
        if _FLESHMONGER_GUARD_LEVEL_TEN_RESEARCH_POLICY.policy_id not in completed:
            return replace(
                _FLESHMONGER_GUARD_LEVEL_TEN_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
    if (
        field_martial
        and context.character_class == "thief"
        and normalized_level == 11
    ):
        rotation = (
            _FLESHMONGER_THIEF_LEVEL_ELEVEN_POLICY,
            _MORIA_SANCTUARY_LEVEL_ELEVEN_POLICY,
        )
        previous_indexes = {
            _FLESHMONGER_THIEF_LEVEL_ELEVEN_POLICY.policy_id: 0,
            _FLESHMONGER_THIEF_ROTATION_POLICY.policy_id: 0,
            _MORIA_SANCTUARY_LEVEL_ELEVEN_POLICY.policy_id: 1,
            _MORIA_SANCTUARY_LEVEL_TEN_POLICY.policy_id: 1,
        }
        previous_index = previous_indexes.get(context.last_policy_id)
        if previous_index is not None:
            policy = _next_productive_policy(
                rotation,
                previous_index=previous_index,
                xp_deltas=context.policy_xp_deltas,
            )
            return replace(policy, practice_skill=context.practice_skill)
        return replace(
            _FLESHMONGER_THIEF_LEVEL_ELEVEN_POLICY,
            practice_skill=context.practice_skill,
        )
    if (
        field_martial
        and context.character_class == "thief"
        and normalized_level == 12
    ):
        completed = context.policy_xp_deltas or {}
        research_xp = completed.get(
            _FLESHMONGER_THIEF_LEVEL_TWELVE_RESEARCH_POLICY.policy_id
        )
        if research_xp is None:
            return replace(
                _FLESHMONGER_THIEF_LEVEL_TWELVE_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
        if research_xp > 0:
            if context.last_policy_id in {
                _RETIRED_MORIA_SANCTUARY_LEVEL_TWELVE_RESEARCH_POLICY_ID,
                _FLESHMONGER_THIEF_LEVEL_TWELVE_POLICY.policy_id,
            } and (
                context.last_policy_id
                == _RETIRED_MORIA_SANCTUARY_LEVEL_TWELVE_RESEARCH_POLICY_ID
                or completed.get(_FLESHMONGER_THIEF_LEVEL_TWELVE_POLICY.policy_id)
                == 0
            ):
                return replace(
                    _PLAINS_ARUNCUS_LEVEL_TWELVE_RESEARCH_POLICY,
                    practice_skill=context.practice_skill,
                )
            return replace(
                _FLESHMONGER_THIEF_LEVEL_TWELVE_POLICY,
                practice_skill=context.practice_skill,
            )
        return replace(
            _UNAVAILABLE_POLICY,
            minimum_level=12,
            practice_skill=context.practice_skill,
        )
    if field_martial and 10 <= normalized_level <= 11:
        completed = context.policy_xp_deltas or {}
        if _FLESHMONGER_GUARD_LEVEL_TEN_RESEARCH_POLICY.policy_id not in completed:
            return replace(
                _FLESHMONGER_GUARD_LEVEL_TEN_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            context.character_class == "warrior"
            and _FLESHMONGER_GUARD_LEVEL_TEN_KILL_RESEARCH_POLICY.policy_id
            not in completed
        ):
            return replace(
                _FLESHMONGER_GUARD_LEVEL_TEN_KILL_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            context.character_class == "thief"
            and _FLESHMONGER_THIEF_GUARD_RESEARCH_POLICY.policy_id
            not in completed
        ):
            return replace(
                _FLESHMONGER_THIEF_GUARD_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
        if context.character_class == "thief":
            research_xp = completed.get(
                _FLESHMONGER_THIEF_GUARD_RESEARCH_POLICY.policy_id
            )
            recent_xp = completed.get(_FLESHMONGER_THIEF_GUARD_POLICY.policy_id)
            if (
                research_xp is not None
                and research_xp > 0
                and (recent_xp is None or recent_xp > 0)
            ):
                return replace(
                    _FLESHMONGER_THIEF_GUARD_POLICY,
                    practice_skill=context.practice_skill,
                )
            if (
                recent_xp is not None
                and recent_xp <= 0
                and _FLESHMONGER_MUFTI_RESEARCH_POLICY.policy_id
                not in completed
            ):
                return replace(
                    _FLESHMONGER_MUFTI_RESEARCH_POLICY,
                    practice_skill=context.practice_skill,
                )
            if (
                _FLESHMONGER_MUFTI_RESEARCH_POLICY.policy_id in completed
                and _FLESHMONGER_COOK_RESEARCH_POLICY.policy_id not in completed
            ):
                return replace(
                    _FLESHMONGER_COOK_RESEARCH_POLICY,
                    practice_skill=context.practice_skill,
                )
            if (
                _FLESHMONGER_COOK_RESEARCH_POLICY.policy_id in completed
            ):
                recent_xp = completed.get(_FLESHMONGER_COOK_POLICY.policy_id)
                if recent_xp is None or recent_xp > 0:
                    return replace(
                        _FLESHMONGER_COOK_POLICY,
                        practice_skill=context.practice_skill,
                    )
                if _AMBUSH_ARCHER_RESEARCH_POLICY.policy_id not in completed:
                    return replace(
                        _AMBUSH_ARCHER_RESEARCH_POLICY,
                        practice_skill=context.practice_skill,
                    )
                if (
                    _AMBUSH_ARCHER_KILL_RESEARCH_POLICY.policy_id
                    not in completed
                ):
                    return replace(
                        _AMBUSH_ARCHER_KILL_RESEARCH_POLICY,
                        practice_skill=context.practice_skill,
                    )
                if (
                    _GNOME_GUARD_LEVEL_TEN_RESEARCH_POLICY.policy_id
                    not in completed
                ):
                    return replace(
                        _GNOME_GUARD_LEVEL_TEN_RESEARCH_POLICY,
                        practice_skill=context.practice_skill,
                    )
                if (
                    _FLESHMONGER_THIEF_ROTATION_RESEARCH_POLICY.policy_id
                    not in completed
                ):
                    return replace(
                        _FLESHMONGER_THIEF_ROTATION_RESEARCH_POLICY,
                        practice_skill=context.practice_skill,
                    )
                rotation_research_xp = completed.get(
                    _FLESHMONGER_THIEF_ROTATION_RESEARCH_POLICY.policy_id
                )
                rotation_recent_xp = completed.get(
                    _FLESHMONGER_THIEF_ROTATION_POLICY.policy_id
                )
                if (
                    rotation_recent_xp is not None
                    and rotation_recent_xp > 0
                    and _FLESHMONGER_COOK_IDENTITY_RESEARCH_POLICY.policy_id
                    not in completed
                ):
                    return replace(
                        _FLESHMONGER_COOK_IDENTITY_RESEARCH_POLICY,
                        practice_skill=context.practice_skill,
                    )
                if (
                    _FLESHMONGER_COOK_IDENTITY_RESEARCH_POLICY.policy_id
                    in completed
                    and _FLESHMONGER_COOK_IDENTITY_POLICY.policy_id
                    not in completed
                ):
                    return replace(
                        _FLESHMONGER_COOK_IDENTITY_POLICY,
                        practice_skill=context.practice_skill,
                    )
                if (
                    rotation_research_xp is not None
                    and rotation_research_xp > 0
                    and (
                        rotation_recent_xp is None
                        or rotation_recent_xp > 0
                    )
                ):
                    if (
                        _FLESHMONGER_COOK_IDENTITY_POLICY.policy_id
                        in completed
                    ):
                        if (
                            _FLESHMONGER_SERVANT_RESEARCH_POLICY.policy_id
                            not in completed
                        ):
                            return replace(
                                _FLESHMONGER_SERVANT_RESEARCH_POLICY,
                                practice_skill=context.practice_skill,
                            )
                        if (
                            _FLESHMONGER_SERVANT_KILL_RESEARCH_POLICY.policy_id
                            not in completed
                        ):
                            return replace(
                                _FLESHMONGER_SERVANT_KILL_RESEARCH_POLICY,
                                practice_skill=context.practice_skill,
                            )
                        if (
                            (
                                servant_kill_xp := completed.get(
                                    _FLESHMONGER_SERVANT_KILL_RESEARCH_POLICY.policy_id
                                )
                            )
                            is not None
                            and servant_kill_xp > 0
                            and _FLESHMONGER_THIEF_EXTENDED_ROTATION_RESEARCH_POLICY.policy_id
                            not in completed
                        ):
                            return replace(
                                _FLESHMONGER_THIEF_EXTENDED_ROTATION_RESEARCH_POLICY,
                                practice_skill=context.practice_skill,
                            )
                        extended_research_xp = completed.get(
                            _FLESHMONGER_THIEF_EXTENDED_ROTATION_RESEARCH_POLICY.policy_id
                        )
                        extended_recent_xp = completed.get(
                            _FLESHMONGER_THIEF_EXTENDED_ROTATION_POLICY.policy_id
                        )
                        if (
                            extended_research_xp is not None
                            and extended_research_xp > 0
                            and (
                                extended_recent_xp is None
                                or extended_recent_xp > 0
                            )
                        ):
                            return replace(
                                _FLESHMONGER_THIEF_EXTENDED_ROTATION_POLICY,
                                practice_skill=context.practice_skill,
                            )
                        if (
                            extended_recent_xp is not None
                            and extended_recent_xp <= 0
                            and not context.has_sanctuary_potion
                            and context.last_policy_id
                            != _MORIA_SANCTUARY_LEVEL_TEN_POLICY.policy_id
                        ):
                            return replace(
                                _MORIA_SANCTUARY_LEVEL_TEN_POLICY,
                                practice_skill=context.practice_skill,
                            )
                    return replace(
                        _FLESHMONGER_THIEF_ROTATION_POLICY,
                        practice_skill=context.practice_skill,
                    )
        if context.character_class == "warrior":
            if (
                _FLESHMONGER_TWO_GUARD_RESEARCH_POLICY.policy_id
                not in completed
            ):
                return replace(
                    _FLESHMONGER_TWO_GUARD_RESEARCH_POLICY,
                    practice_skill=context.practice_skill,
                )
            return replace(
                _FLESHMONGER_GUARD_CIRCUIT_POLICY,
                practice_skill=context.practice_skill,
            )
        return replace(
            _UNAVAILABLE_POLICY,
            minimum_level=10,
            practice_skill=context.practice_skill,
        )
    if field_caster and normalized_level == 11:
        completed = context.policy_xp_deltas or {}
        if (
            _FLESHMONGER_GUARD_LEVEL_TEN_RESEARCH_POLICY.policy_id
            not in completed
        ):
            return replace(
                _FLESHMONGER_GUARD_LEVEL_TEN_RESEARCH_POLICY,
                minimum_level=11,
                practice_skill=context.practice_skill,
            )
        moria_xp = completed.get(_MORIA_SANCTUARY_LEVEL_ELEVEN_POLICY.policy_id)
        if moria_xp is None or moria_xp > 0:
            return replace(
                _MORIA_SANCTUARY_LEVEL_ELEVEN_POLICY,
                practice_skill=context.practice_skill,
            )
        return replace(
            _UNAVAILABLE_POLICY,
            minimum_level=11,
            maximum_level=12,
            summary=(
                "The level-11 protected Moria hunt produced no XP; "
                "review its live result before repeating it."
            ),
            evidence=_MORIA_SANCTUARY_LEVEL_ELEVEN_POLICY.evidence,
            practice_skill=context.practice_skill,
        )
    if normalized_level == 7:
        if (
            not context.has_flight
            and context.can_attempt_flight_purchase
            and not context.flight_purchase_failed
        ):
            return _BUY_FLIGHT_POLICY
        nanny_kills = _boot_kill_count(context.boot_kill_counts, "nanny")
        hermit_kills = _boot_kill_count(context.boot_kill_counts, "hermit")
        nanny_recent_xp = (
            context.policy_xp_deltas.get(
                _DAYCARE_LEVEL_SEVEN_POLICY.policy_id
            )
            if context.policy_xp_deltas is not None
            else None
        )
        circus_recent_xp = (
            context.policy_xp_deltas.get(
                _CIRCUS_ILLUSIONIST_LEVEL_SEVEN_POLICY.policy_id
            )
            if context.policy_xp_deltas is not None
            else None
        )
        moria_recent_xp = (
            context.policy_xp_deltas.get(
                _MORIA_LEVEL_SEVEN_ORC_POLICY.policy_id
            )
            if context.policy_xp_deltas is not None
            else None
        )
        gnome_recent_xp = (
            context.policy_xp_deltas.get(
                _GNOME_LEVEL_SEVEN_POLICY.policy_id
            )
            if context.policy_xp_deltas is not None
            else None
        )
        nanny_is_productive = (
            nanny_recent_xp is None
            or nanny_recent_xp >= _MEANINGFUL_LEVEL_SEVEN_SEGMENT_XP
        )
        established_circuits_depleted = all(
            recent_xp is not None
            and recent_xp < _MEANINGFUL_LEVEL_SEVEN_SEGMENT_XP
            for recent_xp in (
                circus_recent_xp,
                moria_recent_xp,
                gnome_recent_xp,
            )
        )
        if (
            field_caster
            and established_circuits_depleted
            and context.last_policy_id
            in {
                _CIRCUS_ILLUSIONIST_LEVEL_SEVEN_POLICY.policy_id,
                _MORIA_LEVEL_SEVEN_ORC_POLICY.policy_id,
                _GNOME_LEVEL_SEVEN_POLICY.policy_id,
            }
        ):
            completed = context.policy_xp_deltas or {}
            if _GNOME_GUARD_CASTER_LEVEL_SEVEN_POLICY.policy_id not in completed:
                return replace(
                    _GNOME_GUARD_CASTER_LEVEL_SEVEN_POLICY,
                    practice_skill=context.practice_skill,
                )
            for policy in (
                _GNOME_SMALL_TROLL_CASTER_LEVEL_SEVEN_POLICY,
                _AMBUSH_CASTER_LEVEL_SEVEN_POLICY,
            ):
                recent_xp = completed.get(policy.policy_id)
                if (
                    recent_xp is None
                    or recent_xp >= _MEANINGFUL_LEVEL_SEVEN_SEGMENT_XP
                ):
                    return replace(
                        policy,
                        practice_skill=context.practice_skill,
                    )
            return replace(
                _GNOME_SMALL_TROLL_CASTER_LEVEL_SEVEN_POLICY,
                practice_skill=context.practice_skill,
            )
        caster_rotation = (
            _CIRCUS_ILLUSIONIST_LEVEL_SEVEN_POLICY,
            _DAYCARE_ARMED_GUARD_LEVEL_SEVEN_POLICY,
            _GNOME_LEVEL_SEVEN_POLICY,
            _MORIA_LEVEL_SEVEN_ORC_POLICY,
        )
        caster_previous_indexes = {
            policy.policy_id: index for index, policy in enumerate(caster_rotation)
        }
        caster_previous_index = caster_previous_indexes.get(context.last_policy_id)
        caster_recent_xp = (
            (context.policy_xp_deltas or {}).get(context.last_policy_id or "")
        )
        if (
            field_caster
            and not established_circuits_depleted
            and caster_recent_xp is None
            and context.last_policy_id
            == _CIRCUS_ILLUSIONIST_LEVEL_SEVEN_POLICY.policy_id
        ):
            return replace(
                _DAYCARE_ARMED_GUARD_LEVEL_SEVEN_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            field_caster
            and not established_circuits_depleted
            and caster_recent_xp is None
            and context.last_policy_id
            == _DAYCARE_ARMED_GUARD_LEVEL_SEVEN_POLICY.policy_id
        ):
            return replace(
                _GNOME_LEVEL_SEVEN_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            field_caster
            and not established_circuits_depleted
            and caster_previous_index is not None
            and context.policy_xp_deltas is not None
            and context.last_policy_id in context.policy_xp_deltas
        ):
            policy = _next_productive_policy(
                caster_rotation,
                previous_index=caster_previous_index,
                xp_deltas=context.policy_xp_deltas,
                minimum_xp=_MEANINGFUL_LEVEL_SEVEN_SEGMENT_XP,
            )
            return replace(policy, practice_skill=context.practice_skill)
        if (
            context.last_policy_id
            == _GNOME_GUARD_CASTER_LEVEL_SEVEN_POLICY.policy_id
        ):
            if (
                established_circuits_depleted
                and "invisibility" in context.capabilities
            ):
                return replace(
                    _GNOME_SMALL_TROLL_CASTER_LEVEL_SEVEN_POLICY,
                    practice_skill=context.practice_skill,
                )
            return replace(
                _DAYCARE_ARMED_GUARD_LEVEL_SEVEN_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _GNOME_SMALL_TROLL_CASTER_LEVEL_SEVEN_POLICY.policy_id
        ):
            if (
                established_circuits_depleted
                and "invisibility" in context.capabilities
            ):
                return replace(
                    _AMBUSH_CASTER_LEVEL_SEVEN_POLICY,
                    practice_skill=context.practice_skill,
                )
            return replace(
                _DAYCARE_ARMED_GUARD_LEVEL_SEVEN_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _AMBUSH_CASTER_LEVEL_SEVEN_POLICY.policy_id
        ):
            return replace(
                _DAYCARE_ARMED_GUARD_LEVEL_SEVEN_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            field_caster
            and established_circuits_depleted
            and context.last_policy_id
            == _DAYCARE_ARMED_GUARD_LEVEL_SEVEN_POLICY.policy_id
        ):
            completed = context.policy_xp_deltas or {}
            if _GNOME_GUARD_CASTER_LEVEL_SEVEN_POLICY.policy_id not in completed:
                return replace(
                    _GNOME_GUARD_CASTER_LEVEL_SEVEN_POLICY,
                    practice_skill=context.practice_skill,
                )
            expanded_rotation = (
                _GNOME_SMALL_TROLL_CASTER_LEVEL_SEVEN_POLICY,
                _AMBUSH_CASTER_LEVEL_SEVEN_POLICY,
            )
            for policy in expanded_rotation:
                recent_xp = completed.get(policy.policy_id)
                if (
                    recent_xp is None
                    or recent_xp >= _MEANINGFUL_LEVEL_SEVEN_SEGMENT_XP
                ):
                    return replace(
                        policy,
                        practice_skill=context.practice_skill,
                    )
            return replace(
                _GNOME_SMALL_TROLL_CASTER_LEVEL_SEVEN_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _DAYCARE_ARMED_GUARD_LEVEL_SEVEN_POLICY.policy_id
        ):
            return replace(
                _CIRCUS_ILLUSIONIST_LEVEL_SEVEN_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _CIRCUS_ILLUSIONIST_LEVEL_SEVEN_POLICY.policy_id
            and circus_recent_xp is not None
            and circus_recent_xp <= 0
            and gnome_recent_xp is not None
            and gnome_recent_xp <= 0
            and moria_recent_xp is not None
            and moria_recent_xp <= 0
        ):
            return replace(
                _MORIA_LEVEL_SEVEN_ORC_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            circus_recent_xp is not None
            and circus_recent_xp <= 0
            and context.last_policy_id
            in {
                _CIRCUS_ILLUSIONIST_LEVEL_SEVEN_POLICY.policy_id,
                _MORIA_LEVEL_SEVEN_ORC_POLICY.policy_id,
            }
        ):
            return replace(
                _GNOME_LEVEL_SEVEN_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            not nanny_is_productive
            and context.last_policy_id
            in {
                _GNOME_LEVEL_SEVEN_POLICY.policy_id,
                _MORIA_LEVEL_SEVEN_ORC_POLICY.policy_id,
            }
        ):
            return replace(
                _CIRCUS_ILLUSIONIST_LEVEL_SEVEN_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _CIRCUS_ILLUSIONIST_LEVEL_SEVEN_POLICY.policy_id
        ):
            if moria_recent_xp is not None and moria_recent_xp <= 0:
                return replace(
                    _GNOME_LEVEL_SEVEN_POLICY,
                    practice_skill=context.practice_skill,
                )
            return replace(
                _MORIA_LEVEL_SEVEN_ORC_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            context.character_class == "thief"
            and hermit_kills < 9
            and context.last_policy_id
            in {
                _DAYCARE_LEVEL_SEVEN_POLICY.policy_id,
                _MORIA_LEVEL_SEVEN_ORC_POLICY.policy_id,
            }
        ):
            return replace(
                _GNOME_LEVEL_SEVEN_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            context.character_class == "thief"
            and hermit_kills >= 9
            and context.last_policy_id == _MORIA_LEVEL_SEVEN_ORC_POLICY.policy_id
        ):
            return replace(
                _DAYCARE_LEVEL_SEVEN_POLICY,
                practice_skill=context.practice_skill,
            )
        if context.last_policy_id in {
            _DAYCARE_LEVEL_SEVEN_POLICY.policy_id,
            _SHIRE_LEVEL_SEVEN_POLICY.policy_id,
            # This policy was briefly executable before live evidence re-gated
            # it. Preserve the safe post-Shire rotation for old checkpoints.
            "shire-bull-warrior-7-8",
        }:
            return replace(
                _MORIA_LEVEL_SEVEN_ORC_POLICY,
                practice_skill=context.practice_skill,
            )
        if context.last_policy_id == _MORIA_LEVEL_SEVEN_ORC_POLICY.policy_id:
            return replace(
                _GNOME_LEVEL_SEVEN_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id == _GNOME_LEVEL_SEVEN_POLICY.policy_id
            and nanny_is_productive
        ):
            return replace(
                _DAYCARE_LEVEL_SEVEN_POLICY,
                practice_skill=context.practice_skill,
            )
        if nanny_kills < 2 and nanny_is_productive:
            return replace(
                _DAYCARE_LEVEL_SEVEN_POLICY,
                practice_skill=context.practice_skill,
            )
        return replace(
            _MORIA_LEVEL_SEVEN_ORC_POLICY,
            practice_skill=context.practice_skill,
        )
    if normalized_level < 10:
        return replace(
            _MUD_SCHOOL_RESEARCH_POLICY,
            practice_skill=context.practice_skill,
        )
    if (
        field_martial
        and context.character_class == "thief"
        and 13 <= normalized_level <= 15
    ):
        completed = context.policy_xp_deltas or {}
        aruncus_xp = completed.get(_PLAINS_ARUNCUS_RESEARCH_POLICY.policy_id)
        aruncus_pursuit_xp = completed.get(
            _PLAINS_ARUNCUS_THIEF_PURSUIT_RESEARCH_POLICY.policy_id
        )
        aruncus_hunt_xp = completed.get(
            _PLAINS_ARUNCUS_THIEF_HUNT_POLICY.policy_id
        )
        worker_hunt_xp = completed.get(
            _DWARVEN_WORKERS_THIEF_HUNT_RESEARCH_POLICY.policy_id
        )
        fleshmonger_xp = completed.get(
            _FLESHMONGER_THIEF_LEVEL_TWELVE_POLICY.policy_id
        )
        bardoosh_xp = completed.get(
            _AMBUSH_BARDOOSH_THIEF_KILL_RESEARCH_POLICY.policy_id
        )
        nobleman_xp = completed.get(
            _DWARVEN_NOBLEMAN_THIEF_RESEARCH_POLICY.policy_id
        )
        nobleman_hunt_xp = completed.get(
            _DWARVEN_NOBLEMAN_THIEF_HUNT_RESEARCH_POLICY.policy_id
        )
        treasurer_hunt_xp = completed.get(
            _GNOME_TREASURER_THIEF_HUNT_RESEARCH_POLICY.policy_id
        )
        treasurer_excluded = (
            _GNOME_TREASURER_THIEF_HUNT_RESEARCH_POLICY.policy_id
            in context.excluded_policy_ids
        )
        moria_sanctuary_excluded = (
            _MORIA_SANCTUARY_LEVEL_FOURTEEN_THIEF_POLICY.policy_id
            in context.excluded_policy_ids
        )
        rock_toad_hunt_xp = completed.get(
            _MAHNTOR_ROCK_TOAD_THIEF_HUNT_RESEARCH_POLICY.policy_id
        )
        rock_toad_circuit_xp = completed.get(
            _MAHNTOR_ROCK_TOAD_THIEF_CIRCUIT_POLICY.policy_id
        )
        treasurer_kills = _boot_kill_count(
            context.boot_kill_counts,
            "the treasurer",
        )
        aruncus_kills = _boot_kill_count(
            context.boot_kill_counts,
            "Aruncus the Druid",
        )
        rock_toad_kills = _boot_kill_count(
            context.boot_kill_counts,
            "the Rock Toad",
        )
        if context.last_fastwalk_abort_reason in {
            "policy revision removed the redundant nobleman destination hop",
            "policy revision aligned the nobleman stop with its source identity",
        }:
            return replace(
                _DWARVEN_NOBLEMAN_THIEF_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
        if context.last_fastwalk_abort_reason == (
            "policy revision bound the worker survey to its exact source room "
            "line"
        ):
            return replace(
                _DWARVEN_WORKERS_THIEF_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _DWARVEN_WORKERS_THIEF_HUNT_RESEARCH_POLICY.policy_id
            and not _research_result_recorded(
                context,
                _MAHNTOR_ROCK_TOAD_THIEF_RESEARCH_POLICY.policy_id,
            )
        ):
            return replace(
                _MAHNTOR_ROCK_TOAD_THIEF_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            normalized_level > 13
            and context.last_policy_id
            == _PLAINS_ARUNCUS_THIEF_HUNT_POLICY.policy_id
            and (aruncus_hunt_xp is None or aruncus_hunt_xp > 0)
            and not _research_result_recorded(
                context,
                _DWARVEN_WORKERS_THIEF_RESEARCH_POLICY.policy_id,
            )
        ):
            return replace(
                _DWARVEN_WORKERS_THIEF_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _DWARVEN_NOBLEMAN_THIEF_RESEARCH_POLICY.policy_id
            and _research_result_is_viable(
                context,
                _DWARVEN_NOBLEMAN_THIEF_RESEARCH_POLICY.policy_id,
            )
            and nobleman_hunt_xp is None
        ):
            return replace(
                _DWARVEN_NOBLEMAN_THIEF_HUNT_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _MAHNTOR_ROCK_TOAD_THIEF_RESEARCH_POLICY.policy_id
            and _research_result_is_viable(
                context,
                _MAHNTOR_ROCK_TOAD_THIEF_RESEARCH_POLICY.policy_id,
            )
            and rock_toad_hunt_xp is None
        ):
            return replace(
                _MAHNTOR_ROCK_TOAD_THIEF_HUNT_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _MAHNTOR_ROCK_TOAD_THIEF_HUNT_RESEARCH_POLICY.policy_id
            and rock_toad_hunt_xp is not None
            and rock_toad_hunt_xp > 0
            and rock_toad_circuit_xp is not None
            and aruncus_pursuit_xp is not None
            and aruncus_pursuit_xp > 0
        ):
            return replace(
                _PLAINS_ARUNCUS_THIEF_HUNT_POLICY,
                summary=(
                    "Rotate from the proven one-kill Rock Toad policy to the "
                    "previously productive Aruncus hunt so Mahn-Tor can reset."
                ),
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _MAHNTOR_ROCK_TOAD_THIEF_HUNT_RESEARCH_POLICY.policy_id
            and rock_toad_hunt_xp is not None
            and rock_toad_hunt_xp > 0
            and rock_toad_circuit_xp is not None
            and not treasurer_excluded
            and treasurer_kills > 0
            and _research_result_is_viable(
                context,
                _GNOME_TREASURER_THIEF_RESEARCH_POLICY.policy_id,
            )
        ):
            return replace(
                _GNOME_TREASURER_THIEF_HUNT_RESEARCH_POLICY,
                summary=(
                    "Rotate from the proven one-kill Rock Toad policy to the "
                    "same-reboot viable Gnome treasurer so Mahn-Tor can reset."
                ),
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _MAHNTOR_ROCK_TOAD_THIEF_HUNT_RESEARCH_POLICY.policy_id
            and rock_toad_hunt_xp is not None
            and rock_toad_hunt_xp > 0
        ):
            return _configured_mahntor_rock_toad_circuit(context)
        if (
            context.last_policy_id
            == _MAHNTOR_ROCK_TOAD_THIEF_CIRCUIT_POLICY.policy_id
            and rock_toad_circuit_xp is not None
            and rock_toad_circuit_xp <= 250
            and not context.has_sanctuary_potion
            and moria_sanctuary_excluded
            and aruncus_pursuit_xp is not None
            and aruncus_pursuit_xp > 0
        ):
            return replace(
                _PLAINS_ARUNCUS_THIEF_HUNT_POLICY,
                summary=(
                    "Rotate from a depleted Rock Toad circuit to Aruncus "
                    "because the Moria potion carrier is below-band for this "
                    "level and reboot."
                ),
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _MAHNTOR_ROCK_TOAD_THIEF_CIRCUIT_POLICY.policy_id
            and rock_toad_circuit_xp is not None
            and rock_toad_circuit_xp <= 250
            and not context.has_sanctuary_potion
        ):
            return replace(
                _MORIA_SANCTUARY_LEVEL_FOURTEEN_THIEF_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _MORIA_SANCTUARY_LEVEL_FOURTEEN_THIEF_POLICY.policy_id
            and moria_sanctuary_excluded
            and aruncus_pursuit_xp is not None
            and aruncus_pursuit_xp > 0
        ):
            return replace(
                _PLAINS_ARUNCUS_THIEF_HUNT_POLICY,
                summary=(
                    "Leave the below-band Moria carrier for a previously "
                    "productive Aruncus hunt."
                ),
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _MORIA_SANCTUARY_LEVEL_FOURTEEN_THIEF_POLICY.policy_id
            and rock_toad_hunt_xp is not None
            and rock_toad_hunt_xp > 0
        ):
            return _configured_mahntor_rock_toad_circuit(context)
        if (
            context.last_policy_id
            == _MAHNTOR_ROCK_TOAD_THIEF_CIRCUIT_POLICY.policy_id
            and rock_toad_circuit_xp is not None
            and rock_toad_circuit_xp > 0
            and aruncus_pursuit_xp is not None
            and aruncus_pursuit_xp > 0
        ):
            return replace(
                _PLAINS_ARUNCUS_THIEF_HUNT_POLICY,
                summary=(
                    "Rotate from a productive Rock Toad circuit to the "
                    "previously productive Aruncus hunt so the Mahn-Tor "
                    "resets can repopulate."
                ),
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _MAHNTOR_ROCK_TOAD_THIEF_CIRCUIT_POLICY.policy_id
            and rock_toad_circuit_xp is not None
            and rock_toad_circuit_xp > 0
            and not treasurer_excluded
            and treasurer_kills > 0
            and _research_result_is_viable(
                context,
                _GNOME_TREASURER_THIEF_RESEARCH_POLICY.policy_id,
            )
        ):
            return replace(
                _GNOME_TREASURER_THIEF_HUNT_RESEARCH_POLICY,
                summary=(
                    "Rotate from a productive Rock Toad circuit to the "
                    "same-reboot viable Gnome treasurer so the Mahn-Tor "
                    "resets can repopulate."
                ),
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _MAHNTOR_ROCK_TOAD_THIEF_CIRCUIT_POLICY.policy_id
            and rock_toad_circuit_xp is not None
            and (
                rock_toad_circuit_xp > 250
                or context.has_sanctuary_potion
            )
        ):
            return _configured_mahntor_rock_toad_circuit(context)
        if (
            context.last_policy_id
            == _DWARVEN_WORKERS_THIEF_RESEARCH_POLICY.policy_id
            and not _research_result_recorded(
                context,
                _MAHNTOR_ROCK_TOAD_THIEF_RESEARCH_POLICY.policy_id,
            )
        ):
            return replace(
                _MAHNTOR_ROCK_TOAD_THIEF_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            not treasurer_excluded
            and context.last_policy_id
            == _GNOME_TREASURER_THIEF_RESEARCH_POLICY.policy_id
            and _research_result_is_viable(
                context,
                _GNOME_TREASURER_THIEF_RESEARCH_POLICY.policy_id,
            )
            and treasurer_hunt_xp is None
        ):
            return replace(
                _GNOME_TREASURER_THIEF_HUNT_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            normalized_level == 13
            and context.last_policy_id
            == _GNOME_TREASURER_THIEF_HUNT_RESEARCH_POLICY.policy_id
            and treasurer_hunt_xp is not None
            and treasurer_hunt_xp <= 0
            and treasurer_kills > 0
            and _research_result_is_viable(
                context,
                _GNOME_TREASURER_THIEF_RESEARCH_POLICY.policy_id,
            )
        ):
            return replace(
                _FLESHMONGER_THIEF_LEVEL_TWELVE_POLICY,
                summary=(
                    "Leave the empty treasury for one verified outside-area "
                    "segment before retrying its source-backed reset."
                ),
                practice_skill=context.practice_skill,
            )
        if (
            normalized_level == 13
            and not treasurer_excluded
            and context.last_policy_id
            in {
                _FLESHMONGER_THIEF_LEVEL_TWELVE_POLICY.policy_id,
                _GNOME_TREASURER_THIEF_HUNT_RESEARCH_POLICY.policy_id,
            }
            and fleshmonger_xp is not None
            and fleshmonger_xp <= 0
            and treasurer_hunt_xp is not None
            and (
                treasurer_hunt_xp > 0
                or (
                    context.last_policy_id
                    == _FLESHMONGER_THIEF_LEVEL_TWELVE_POLICY.policy_id
                    and treasurer_kills > 0
                    and _research_result_is_viable(
                        context,
                        _GNOME_TREASURER_THIEF_RESEARCH_POLICY.policy_id,
                    )
                )
            )
        ):
            return replace(
                _GNOME_TREASURER_THIEF_HUNT_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            normalized_level == 13
            and context.last_policy_id
            == _FLESHMONGER_THIEF_LEVEL_TWELVE_POLICY.policy_id
            and (aruncus_hunt_xp is None or aruncus_hunt_xp <= 0)
            and (fleshmonger_xp is None or fleshmonger_xp <= 0)
            and _research_result_was_observed(
                context,
                _DWARVEN_NOBLEMAN_THIEF_RESEARCH_POLICY.policy_id,
            )
            and not _research_result_is_viable(
                context,
                _DWARVEN_NOBLEMAN_THIEF_RESEARCH_POLICY.policy_id,
            )
            and not _research_result_recorded(
                context,
                _GNOME_TREASURER_THIEF_RESEARCH_POLICY.policy_id,
            )
        ):
            return replace(
                _GNOME_TREASURER_THIEF_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            normalized_level == 13
            and context.last_policy_id
            == _FLESHMONGER_THIEF_LEVEL_TWELVE_POLICY.policy_id
            and (aruncus_hunt_xp is None or aruncus_hunt_xp <= 0)
            and (fleshmonger_xp is None or fleshmonger_xp <= 0)
            and (
                _research_result_is_stale(
                    context,
                    _DWARVEN_NOBLEMAN_THIEF_RESEARCH_POLICY.policy_id,
                )
                or (
                    _research_result_recorded(
                        context,
                        _DWARVEN_NOBLEMAN_THIEF_RESEARCH_POLICY.policy_id,
                    )
                    and not _research_result_was_observed(
                        context,
                        _DWARVEN_NOBLEMAN_THIEF_RESEARCH_POLICY.policy_id,
                    )
                )
            )
        ):
            stale_result = _research_result_is_stale(
                context,
                _DWARVEN_NOBLEMAN_THIEF_RESEARCH_POLICY.policy_id,
            )
            return replace(
                _DWARVEN_NOBLEMAN_THIEF_RESEARCH_POLICY,
                summary=(
                    "Recheck the source-proven nobleman after the MUD reboot "
                    "provided a newly rolled mobile."
                    if stale_result
                    else "Recheck the source-proven nobleman room after two "
                    "outside-area segments allowed an absent reset to advance."
                ),
                practice_skill=context.practice_skill,
            )
        if (
            normalized_level == 13
            and aruncus_kills >= 5
            and bardoosh_xp is not None
            and nobleman_xp is None
            and context.last_policy_id
            == _PLAINS_ARUNCUS_THIEF_HUNT_POLICY.policy_id
        ):
            return replace(
                _DWARVEN_NOBLEMAN_THIEF_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            normalized_level == 13
            and aruncus_kills >= 3
            and bardoosh_xp is None
        ):
            return replace(
                _AMBUSH_BARDOOSH_THIEF_KILL_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            normalized_level == 13
            and context.last_policy_id
            == _AMBUSH_BARDOOSH_THIEF_KILL_RESEARCH_POLICY.policy_id
            and context.last_fastwalk_abort_reason
            in {
                "unexpected combat interrupted fastwalk 'ambush' before its objective",
                "policy revision corrected the Bardoosh final route from south to west",
                "policy revision bound Bardoosh's generic live line to his source identity",
            }
        ):
            return replace(
                _AMBUSH_BARDOOSH_THIEF_KILL_RESEARCH_POLICY,
                summary=(
                    "Retry isolated Bardoosh once after a source-vetted trivial "
                    "bystander interrupted the previous route."
                ),
                practice_skill=context.practice_skill,
            )
        if (
            normalized_level == 13
            and context.last_policy_id
            == _AMBUSH_BARDOOSH_THIEF_KILL_RESEARCH_POLICY.policy_id
        ):
            return replace(
                (
                    _PLAINS_ARUNCUS_THIEF_HUNT_POLICY
                    if aruncus_pursuit_xp is not None
                    and aruncus_pursuit_xp > 0
                    else _PLAINS_ARUNCUS_THIEF_PURSUIT_RESEARCH_POLICY
                ),
                practice_skill=context.practice_skill,
            )
        if (
            normalized_level > 13
            and context.last_policy_id
            == _PLAINS_ARUNCUS_THIEF_HUNT_POLICY.policy_id
            and aruncus_hunt_xp is not None
            and treasurer_kills > 0
            and (
                not treasurer_excluded
            )
            and _research_result_is_viable(
                context,
                _GNOME_TREASURER_THIEF_RESEARCH_POLICY.policy_id,
            )
        ):
            return replace(
                _GNOME_TREASURER_THIEF_HUNT_RESEARCH_POLICY,
                summary=(
                    "Rotate to the same-reboot viable Gnome treasurer after "
                    + (
                        "an empty or escaped Aruncus segment."
                        if aruncus_hunt_xp <= 0
                        else "a successful Aruncus kill so his single reset "
                        "has time to repopulate."
                    )
                ),
                practice_skill=context.practice_skill,
            )
        if (
            normalized_level > 13
            and context.last_policy_id
            == _PLAINS_ARUNCUS_THIEF_HUNT_POLICY.policy_id
            and aruncus_hunt_xp is not None
            and treasurer_excluded
            and rock_toad_hunt_xp is not None
            and (
                rock_toad_hunt_xp > 0
                or rock_toad_kills > 0
            )
        ):
            return replace(
                _MAHNTOR_ROCK_TOAD_THIEF_HUNT_RESEARCH_POLICY,
                summary=(
                    (
                        "Rotate from an empty or escaped Aruncus pursuit to "
                        if aruncus_hunt_xp <= 0
                        else "Rotate from a completed single-reset Aruncus hunt to "
                    )
                    + "the reboot-proven bounded rock-toad hunt while the "
                    "Gnome treasurer is excluded. A latest empty Toad segment "
                    "does not erase earlier same-reboot kills after productive "
                    "work elsewhere has given Mahn-Tor time to reset."
                ),
                practice_skill=context.practice_skill,
            )
        if aruncus_pursuit_xp is not None and aruncus_pursuit_xp > 0:
            if (
                normalized_level > 13
                or aruncus_hunt_xp is None
                or aruncus_hunt_xp > 0
                or (
                    fleshmonger_xp is not None
                    and fleshmonger_xp <= 0
                    and context.last_policy_id
                    == _FLESHMONGER_THIEF_LEVEL_TWELVE_POLICY.policy_id
                )
            ):
                return replace(
                    _PLAINS_ARUNCUS_THIEF_HUNT_POLICY,
                    practice_skill=context.practice_skill,
                )
        if aruncus_xp is not None and (
            aruncus_pursuit_xp is None
        ):
            return replace(
                _PLAINS_ARUNCUS_THIEF_PURSUIT_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            aruncus_pursuit_xp is not None
            and aruncus_pursuit_xp <= 0
            and fleshmonger_xp is not None
            and fleshmonger_xp <= 0
            and context.last_policy_id
            == _FLESHMONGER_THIEF_LEVEL_TWELVE_POLICY.policy_id
        ):
            return replace(
                _PLAINS_ARUNCUS_THIEF_PURSUIT_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
        if normalized_level > 13 and aruncus_xp is not None:
            return replace(
                _PLAINS_ARUNCUS_THIEF_PURSUIT_RESEARCH_POLICY,
                summary=(
                    "Retry the source-vetted Aruncus pursuit under the campaign "
                    "stall and outside-area reset controller."
                ),
                practice_skill=context.practice_skill,
            )
        if aruncus_xp is not None and (
            fleshmonger_xp is None or fleshmonger_xp > 0
        ):
            return replace(
                _FLESHMONGER_THIEF_LEVEL_TWELVE_POLICY,
                practice_skill=context.practice_skill,
            )
        if aruncus_xp is not None and fleshmonger_xp <= 0:
            return replace(
                _FLESHMONGER_THIEF_LEVEL_TWELVE_POLICY,
                summary=(
                    "Retry the verified level-13 Fleshmonger rotation under the "
                    "campaign stall and outside-area reset controller."
                ),
                evidence=(
                    *_FLESHMONGER_THIEF_LEVEL_TWELVE_POLICY.evidence,
                    "A zero-XP Fleshmonger pass after the retired Aruncus "
                    "evidence loop is temporary area depletion, not proof that "
                    "the source-backed route has become invalid.",
                    "The campaign stall controller bounds immediate retries, "
                    "logs out at the healer, waits outside the area, and then "
                    "retries after an area-reset window.",
                ),
                practice_skill=context.practice_skill,
            )
        if (
            context.last_policy_id
            == _FLESHMONGER_THIEF_LEVEL_TWELVE_POLICY.policy_id
            and fleshmonger_xp is not None
            and fleshmonger_xp > 0
        ):
            return replace(
                _FLESHMONGER_THIEF_LEVEL_TWELVE_POLICY,
                practice_skill=context.practice_skill,
            )
    if normalized_level == 12:
        return replace(
            _PLAINS_ARUNCUS_LEVEL_TWELVE_RESEARCH_POLICY,
            practice_skill=context.practice_skill,
        )
    if 13 <= normalized_level <= 15:
        return replace(
            _PLAINS_ARUNCUS_RESEARCH_POLICY,
            practice_skill=context.practice_skill,
        )
    if 16 <= normalized_level <= 20:
        if (
            not context.has_flight
            and context.can_attempt_flight_purchase
            and not context.flight_purchase_failed
        ):
            return _BUY_FLIGHT_POLICY
        if normalized_level >= 17 and context.character_class == "thief":
            if (
                context.last_policy_id
                == _MORIA_SANCTUARY_THIEF_LEVEL_SEVENTEEN_POLICY.policy_id
                and context.has_sanctuary_potion
                and _research_result_is_viable(
                    context,
                    _SHIRE_ELVEN_WIZARD_RESEARCH_POLICY.policy_id,
                )
            ):
                return replace(
                    _SHIRE_ELVEN_WIZARD_HUNT_POLICY,
                    practice_skill=context.practice_skill,
                )
            if (
                context.last_policy_id
                == _MORIA_SANCTUARY_THIEF_LEVEL_SEVENTEEN_POLICY.policy_id
                and context.has_sanctuary_potion
            ):
                return replace(
                    _HIGHTOWER_JAILOR_HUNT_POLICY,
                    summary=(
                        "Retry the source-verified Jailor only after the "
                        "Moria carrier supplied a sanctuary reserve."
                    ),
                    practice_skill=context.practice_skill,
                )
            if (
                context.last_policy_id == _HIGHTOWER_JAILOR_HUNT_POLICY.policy_id
                and not context.has_sanctuary_potion
                and str(context.last_fastwalk_abort_reason or "").startswith(
                    "field combat aborted"
                )
            ):
                return replace(
                    _MORIA_SANCTUARY_THIEF_LEVEL_SEVENTEEN_POLICY,
                    practice_skill=context.practice_skill,
                )
        if 19 <= normalized_level <= 20:
            late_watchman_policy = _research_hunt_policy(
                context,
                probe=_MIRROR_REALM_WATCHMAN_LEVEL_NINETEEN_RESEARCH_POLICY,
                hunt=_MIRROR_REALM_WATCHMAN_LEVEL_NINETEEN_HUNT_POLICY,
            )
            if late_watchman_policy is not None:
                return replace(
                    late_watchman_policy,
                    practice_skill=context.practice_skill,
                )
        watchman_policy = _research_hunt_policy(
            context,
            probe=_MIRROR_REALM_WATCHMAN_RESEARCH_POLICY,
            hunt=_MIRROR_REALM_WATCHMAN_HUNT_POLICY,
        )
        if watchman_policy is not None:
            return replace(watchman_policy, practice_skill=context.practice_skill)
        stag_policy = _research_hunt_policy(
            context,
            probe=_CRYSTALMIR_WHITE_STAG_RESEARCH_POLICY,
            hunt=_CRYSTALMIR_WHITE_STAG_HUNT_POLICY,
        )
        if stag_policy is not None:
            return replace(stag_policy, practice_skill=context.practice_skill)
        soldier_policy = _research_hunt_policy(
            context,
            probe=_SHADOW_KEEP_SOLDIER_RESEARCH_POLICY,
            hunt=_SHADOW_KEEP_SOLDIER_HUNT_POLICY,
        )
        if soldier_policy is not None:
            return replace(soldier_policy, practice_skill=context.practice_skill)
        if normalized_level >= 17:
            white_dwarf_policy = _research_hunt_policy(
                context,
                probe=_GALAXY_WHITE_DWARF_RESEARCH_POLICY,
                hunt=_GALAXY_WHITE_DWARF_HUNT_POLICY,
            )
            if white_dwarf_policy is not None:
                return replace(
                    white_dwarf_policy,
                    practice_skill=context.practice_skill,
                )
            red_supergiant_policy = _research_hunt_policy(
                context,
                probe=_GALAXY_RED_SUPERGIANT_RESEARCH_POLICY,
                hunt=_GALAXY_RED_SUPERGIANT_HUNT_POLICY,
            )
            if red_supergiant_policy is not None:
                return replace(
                    red_supergiant_policy,
                    practice_skill=context.practice_skill,
                )
            if context.character_class == "thief" and normalized_level <= 18:
                nobleman_policy = _research_hunt_policy(
                    context,
                    probe=_DWARVEN_NOBLEMAN_THIEF_LEVEL_SEVENTEEN_RESEARCH_POLICY,
                    hunt=_DWARVEN_NOBLEMAN_THIEF_LEVEL_SEVENTEEN_HUNT_POLICY,
                )
                if (
                    nobleman_policy is None
                    and context.last_policy_id
                    == _DWARVEN_NOBLEMAN_THIEF_LEVEL_SEVENTEEN_HUNT_POLICY.policy_id
                    and context.last_fastwalk_abort_reason
                    == _NOBLEMAN_APPROACH_INTERRUPT_ABORT
                    and _research_result_is_viable(
                        context,
                        _DWARVEN_NOBLEMAN_THIEF_LEVEL_SEVENTEEN_HUNT_POLICY.policy_id,
                    )
                ):
                    nobleman_policy = (
                        _DWARVEN_NOBLEMAN_THIEF_LEVEL_SEVENTEEN_HUNT_POLICY
                    )
                if (
                    nobleman_policy is None
                    and context.last_policy_id
                    == _MORIA_SANCTUARY_THIEF_LEVEL_SEVENTEEN_POLICY.policy_id
                    and _research_result_is_viable(
                        context,
                        _DWARVEN_NOBLEMAN_THIEF_LEVEL_SEVENTEEN_HUNT_POLICY.policy_id,
                    )
                    and _MAHNTOR_ROCK_TOAD_THIEF_LEVEL_SIXTEEN_POLICY.policy_id
                    in context.excluded_policy_ids
                    and _PLAINS_ARUNCUS_THIEF_LEVEL_SEVENTEEN_FALLBACK_POLICY.policy_id
                    in context.excluded_policy_ids
                ):
                    nobleman_policy = _DWARVEN_NOBLEMAN_THIEF_LEVEL_SEVENTEEN_HUNT_POLICY
                if (
                    nobleman_policy is not None
                    and (
                        context.last_policy_id
                        != _DWARVEN_NOBLEMAN_THIEF_LEVEL_SEVENTEEN_HUNT_POLICY.policy_id
                        or str(context.last_fastwalk_abort_reason or "").startswith(
                            "field room contained "
                        )
                        or str(context.last_fastwalk_abort_reason or "").startswith(
                            _FIELD_RESOURCE_ABORT_PREFIX
                        )
                        or str(context.last_fastwalk_abort_reason or "").startswith(
                            _FIELD_CROWD_ABORT_PREFIX
                        )
                        or context.last_fastwalk_abort_reason
                        == _NOBLEMAN_APPROACH_INTERRUPT_ABORT
                    )
                ):
                    return replace(
                        nobleman_policy,
                        practice_skill=context.practice_skill,
                    )
                if (
                    nobleman_policy is not None
                    and context.last_policy_id
                    == _DWARVEN_NOBLEMAN_THIEF_LEVEL_SEVENTEEN_HUNT_POLICY.policy_id
                    and _MAHNTOR_ROCK_TOAD_THIEF_LEVEL_SIXTEEN_POLICY.policy_id
                    in context.excluded_policy_ids
                    and _PLAINS_ARUNCUS_THIEF_LEVEL_SEVENTEEN_FALLBACK_POLICY.policy_id
                    in context.excluded_policy_ids
                ):
                    return replace(
                        nobleman_policy,
                        practice_skill=context.practice_skill,
                    )
                servant_policy = _research_hunt_policy(
                    context,
                    probe=_DWARVEN_SERVANT_THIEF_RESEARCH_POLICY,
                    hunt=_DWARVEN_SERVANT_THIEF_HUNT_POLICY,
                )
                if servant_policy is not None:
                    return replace(
                        servant_policy,
                        practice_skill=context.practice_skill,
                    )
        jailor_policy_allowed = (
            normalized_level >= 17
            and (
                context.character_class != "thief"
                or normalized_level > 18
                or (
                    context.last_policy_id
                    == _DWARVEN_SERVANT_THIEF_HUNT_POLICY.policy_id
                    and _research_result_recorded(
                        context,
                        _DWARVEN_NOBLEMAN_THIEF_LEVEL_SEVENTEEN_RESEARCH_POLICY.policy_id,
                    )
                    and _research_result_recorded(
                        context,
                        _DWARVEN_SERVANT_THIEF_RESEARCH_POLICY.policy_id,
                    )
                )
                or context.last_policy_id
                in {
                    _HIGHTOWER_JAILOR_RESEARCH_POLICY.policy_id,
                    _HIGHTOWER_JAILOR_HUNT_POLICY.policy_id,
                }
            )
        )
        if jailor_policy_allowed:
            jailor_policy = _research_hunt_policy(
                context,
                probe=_HIGHTOWER_JAILOR_RESEARCH_POLICY,
                hunt=_HIGHTOWER_JAILOR_HUNT_POLICY,
            )
            if jailor_policy is not None:
                return replace(
                    jailor_policy,
                    practice_skill=context.practice_skill,
                )
        productive_late_hunt = _next_productive_research_hunt(
            context,
            (
                _MIRROR_REALM_WATCHMAN_HUNT_POLICY,
                _CRYSTALMIR_WHITE_STAG_HUNT_POLICY,
                _SHADOW_KEEP_SOLDIER_HUNT_POLICY,
                _GALAXY_WHITE_DWARF_HUNT_POLICY,
                _GALAXY_RED_SUPERGIANT_HUNT_POLICY,
                _HIGHTOWER_JAILOR_HUNT_POLICY,
                _SHIRE_DWARVEN_PRINCE_THIEF_HUNT_POLICY,
                _SHIRE_THAIN_HUNT_POLICY,
                _PYRAMID_ALI_BABA_HUNT_POLICY,
            ),
        )
        if productive_late_hunt is not None:
            return replace(
                productive_late_hunt,
                practice_skill=context.practice_skill,
            )
        if context.character_class == "thief" and normalized_level <= 18:
            completed = context.policy_xp_deltas or {}
            prince_policy = _research_hunt_policy(
                context,
                probe=_SHIRE_DWARVEN_PRINCE_THIEF_RESEARCH_POLICY,
                hunt=_SHIRE_DWARVEN_PRINCE_THIEF_HUNT_POLICY,
            )
            if (
                normalized_level >= 17
                and context.last_policy_id
                in {
                    _SHIRE_DWARVEN_PRINCE_THIEF_RESEARCH_POLICY.policy_id,
                    _SHIRE_DWARVEN_PRINCE_THIEF_HUNT_POLICY.policy_id,
                }
                and prince_policy is not None
            ):
                return replace(
                    prince_policy,
                    practice_skill=context.practice_skill,
                )
            thain_policy = _research_hunt_policy(
                context,
                probe=_SHIRE_THAIN_RESEARCH_POLICY,
                hunt=_SHIRE_THAIN_HUNT_POLICY,
            )
            thain_transition = (
                context.last_policy_id
                in {
                    _SHIRE_DWARVEN_PRINCE_THIEF_RESEARCH_POLICY.policy_id,
                    _SHIRE_DWARVEN_PRINCE_THIEF_HUNT_POLICY.policy_id,
                }
                and prince_policy is None
            ) or context.last_policy_id in {
                _SHIRE_THAIN_RESEARCH_POLICY.policy_id,
                _SHIRE_THAIN_HUNT_POLICY.policy_id,
            } or (
                context.last_policy_id
                in {
                    _MAHNTOR_ROCK_TOAD_THIEF_LEVEL_SIXTEEN_POLICY.policy_id,
                    _PLAINS_ARUNCUS_THIEF_LEVEL_SEVENTEEN_FALLBACK_POLICY.policy_id,
                }
                and _MAHNTOR_ROCK_TOAD_THIEF_LEVEL_SIXTEEN_POLICY.policy_id
                in context.excluded_policy_ids
                and _PLAINS_ARUNCUS_THIEF_LEVEL_SEVENTEEN_FALLBACK_POLICY.policy_id
                in context.excluded_policy_ids
                and context.stalled_segments > 0
            )
            if normalized_level >= 17 and thain_transition and thain_policy is not None:
                return replace(
                    thain_policy,
                    practice_skill=context.practice_skill,
                )
            if (
                normalized_level >= 17
                and context.last_policy_id
                in {
                    _SHIRE_THAIN_RESEARCH_POLICY.policy_id,
                    _SHIRE_THAIN_HUNT_POLICY.policy_id,
                }
                and not _research_result_recorded(
                    context,
                    _SHIRE_ELVEN_WIZARD_RESEARCH_POLICY.policy_id,
                )
            ):
                return replace(
                    _SHIRE_ELVEN_WIZARD_RESEARCH_POLICY,
                    practice_skill=context.practice_skill,
                )
            if context.last_policy_id in {
                _SHIRE_ELVEN_WIZARD_RESEARCH_POLICY.policy_id,
                _SHIRE_ELVEN_WIZARD_HUNT_POLICY.policy_id,
                _MORIA_SANCTUARY_THIEF_LEVEL_SEVENTEEN_POLICY.policy_id,
            }:
                if (
                    context.last_policy_id
                    == _MORIA_SANCTUARY_THIEF_LEVEL_SEVENTEEN_POLICY.policy_id
                    and not context.has_sanctuary_potion
                    and not _research_result_recorded(
                        context,
                        _MORIA_SANCTUARY_THIEF_LEVEL_SEVENTEEN_POLICY.policy_id,
                    )
                ):
                    return replace(
                        _MORIA_SANCTUARY_THIEF_LEVEL_SEVENTEEN_POLICY,
                        practice_skill=context.practice_skill,
                    )
                wizard_policy = _research_hunt_policy(
                    context,
                    probe=_SHIRE_ELVEN_WIZARD_RESEARCH_POLICY,
                    hunt=_SHIRE_ELVEN_WIZARD_HUNT_POLICY,
                )
                if wizard_policy is not None:
                    if (
                        wizard_policy.policy_id
                        == _SHIRE_ELVEN_WIZARD_HUNT_POLICY.policy_id
                        and not context.has_sanctuary_potion
                    ):
                        if (
                            context.last_policy_id
                            != _MORIA_SANCTUARY_THIEF_LEVEL_SEVENTEEN_POLICY.policy_id
                        ):
                            return replace(
                                _MORIA_SANCTUARY_THIEF_LEVEL_SEVENTEEN_POLICY,
                                summary=(
                                    "Acquire one purple sanctuary potion in Moria "
                                    "before the source-verified Shire Wizard fight."
                                ),
                                practice_skill=context.practice_skill,
                            )
                        ali_baba_policy = _research_hunt_policy(
                            context,
                            probe=_PYRAMID_ALI_BABA_RESEARCH_POLICY,
                            hunt=_PYRAMID_ALI_BABA_HUNT_POLICY,
                        )
                        if ali_baba_policy is not None:
                            return replace(
                                ali_baba_policy,
                                practice_skill=context.practice_skill,
                            )
                        return replace(
                            _UNAVAILABLE_POLICY,
                            minimum_level=17,
                            maximum_level=20,
                            summary=(
                                "The viable Shire Wizard probe is retained, but its "
                                "caster risk requires a sanctuary reserve before "
                                "combat can be attempted."
                            ),
                            evidence=_SHIRE_ELVEN_WIZARD_HUNT_POLICY.evidence,
                            practice_skill=context.practice_skill,
                        )
                    return replace(
                        wizard_policy,
                        practice_skill=context.practice_skill,
                    )
            if normalized_level >= 18 and context.last_policy_id in {
                _PYRAMID_ALI_BABA_RESEARCH_POLICY.policy_id,
                _PYRAMID_ALI_BABA_HUNT_POLICY.policy_id,
            }:
                ali_baba_policy = _research_hunt_policy(
                    context,
                    probe=_PYRAMID_ALI_BABA_RESEARCH_POLICY,
                    hunt=_PYRAMID_ALI_BABA_HUNT_POLICY,
                )
                if ali_baba_policy is not None:
                    return replace(
                        ali_baba_policy,
                        practice_skill=context.practice_skill,
                    )
            toad_xp = completed.get(
                _MAHNTOR_ROCK_TOAD_THIEF_LEVEL_SIXTEEN_POLICY.policy_id
            )
            bardoosh_xp = completed.get(
                _AMBUSH_BARDOOSH_THIEF_LEVEL_SIXTEEN_RESEARCH_POLICY.policy_id
            )
            verified_bardoosh_xp = completed.get(
                _AMBUSH_BARDOOSH_THIEF_LEVEL_SIXTEEN_HUNT_POLICY.policy_id
            )
            aruncus_fallback_excluded = (
                _PLAINS_ARUNCUS_THIEF_LEVEL_SEVENTEEN_FALLBACK_POLICY.policy_id
                in context.excluded_policy_ids
            )
            if (
                normalized_level >= 17
                and context.last_policy_id
                == _AMBUSH_BARDOOSH_THIEF_LEVEL_SEVENTEEN_RESEARCH_POLICY.policy_id
            ):
                if _research_result_is_viable(
                    context,
                    _AMBUSH_BARDOOSH_THIEF_LEVEL_SEVENTEEN_RESEARCH_POLICY.policy_id,
                ):
                    return replace(
                        _AMBUSH_BARDOOSH_THIEF_LEVEL_SEVENTEEN_HUNT_POLICY,
                        practice_skill=context.practice_skill,
                    )
                return replace(
                    _MAHNTOR_ROCK_TOAD_THIEF_LEVEL_SIXTEEN_POLICY,
                    practice_skill=context.practice_skill,
                )
            if (
                normalized_level >= 17
                and context.last_policy_id
                == _AMBUSH_BARDOOSH_THIEF_LEVEL_SEVENTEEN_HUNT_POLICY.policy_id
            ):
                return replace(
                    _MAHNTOR_ROCK_TOAD_THIEF_LEVEL_SIXTEEN_POLICY,
                    practice_skill=context.practice_skill,
                )
            if (
                normalized_level >= 17
                and context.last_policy_id
                == _MAHNTOR_ROCK_TOAD_THIEF_LEVEL_SIXTEEN_POLICY.policy_id
                and toad_xp is not None
                and toad_xp <= 0
                and aruncus_fallback_excluded
            ):
                late_bardoosh_policy = _research_hunt_policy(
                    context,
                    probe=_AMBUSH_BARDOOSH_THIEF_LEVEL_SEVENTEEN_RESEARCH_POLICY,
                    hunt=_AMBUSH_BARDOOSH_THIEF_LEVEL_SEVENTEEN_HUNT_POLICY,
                )
                if late_bardoosh_policy is not None:
                    return replace(
                        late_bardoosh_policy,
                        practice_skill=context.practice_skill,
                    )
            if (
                normalized_level >= 17
                and context.last_policy_id
                == _MAHNTOR_ROCK_TOAD_THIEF_LEVEL_SIXTEEN_POLICY.policy_id
                and toad_xp is not None
                and toad_xp <= 0
                and aruncus_fallback_excluded
                and context.stalled_segments > 0
                and prince_policy is not None
            ):
                return replace(
                    prince_policy,
                    practice_skill=context.practice_skill,
                )
            if (
                normalized_level >= 17
                and context.last_policy_id
                == _MAHNTOR_ROCK_TOAD_THIEF_LEVEL_SIXTEEN_POLICY.policy_id
            ):
                if (
                    _PLAINS_ARUNCUS_THIEF_LEVEL_SEVENTEEN_FALLBACK_POLICY.policy_id
                    not in context.excluded_policy_ids
                ):
                    return replace(
                        _PLAINS_ARUNCUS_THIEF_LEVEL_SEVENTEEN_FALLBACK_POLICY,
                        practice_skill=context.practice_skill,
                    )
                # A room-specific or whole-policy Aruncus exclusion must not
                # turn the reusable Toad fallback into an unavailable policy.
                # Keep the source-backed Toad circuit executable so the
                # campaign can use its bounded stall/reset controller.
                if (
                    _MAHNTOR_ROCK_TOAD_THIEF_LEVEL_SIXTEEN_POLICY.policy_id
                    not in context.excluded_policy_ids
                ):
                    return replace(
                        _MAHNTOR_ROCK_TOAD_THIEF_LEVEL_SIXTEEN_POLICY,
                        practice_skill=context.practice_skill,
                    )
            if (
                normalized_level >= 17
                and context.last_policy_id
                == _PLAINS_ARUNCUS_THIEF_LEVEL_SEVENTEEN_FALLBACK_POLICY.policy_id
            ):
                return replace(
                    _MAHNTOR_ROCK_TOAD_THIEF_LEVEL_SIXTEEN_POLICY,
                    practice_skill=context.practice_skill,
                )
            if (
                normalized_level == 16
                and bardoosh_xp is not None
                and bardoosh_xp > 0
                and context.last_policy_id
                == _MAHNTOR_ROCK_TOAD_THIEF_LEVEL_SIXTEEN_POLICY.policy_id
                and (
                    verified_bardoosh_xp is None
                    or verified_bardoosh_xp > 0
                )
            ):
                return replace(
                    _AMBUSH_BARDOOSH_THIEF_LEVEL_SIXTEEN_HUNT_POLICY,
                    practice_skill=context.practice_skill,
                )
            if (
                normalized_level == 16
                and toad_xp is not None
                and toad_xp <= 0
                and bardoosh_xp is None
            ):
                return replace(
                    _AMBUSH_BARDOOSH_THIEF_LEVEL_SIXTEEN_RESEARCH_POLICY,
                    practice_skill=context.practice_skill,
                )
            return replace(
                _MAHNTOR_ROCK_TOAD_THIEF_LEVEL_SIXTEEN_POLICY,
                practice_skill=context.practice_skill,
            )
        return replace(
            _UNAVAILABLE_POLICY,
            minimum_level=16,
            maximum_level=20,
            summary=(
                "The Mirror Realm watchmen, Crystalmir White Stag, and Shadow "
                "Keep Undead Soldier produced no viable progress on this "
                "reboot; wait for a new reboot before repeating these probes."
            ),
            evidence=(
                *_MIRROR_REALM_WATCHMAN_RESEARCH_POLICY.evidence,
                *_CRYSTALMIR_WHITE_STAG_RESEARCH_POLICY.evidence,
                *_SHADOW_KEEP_SOLDIER_RESEARCH_POLICY.evidence,
            ),
            practice_skill=context.practice_skill,
        )
    if 21 <= normalized_level <= 25:
        watchman_policy = _research_hunt_policy(
            context,
            probe=_MIRROR_REALM_WATCHMAN_LEVEL_TWENTY_ONE_RESEARCH_POLICY,
            hunt=_MIRROR_REALM_WATCHMAN_LEVEL_TWENTY_ONE_HUNT_POLICY,
        )
        if watchman_policy is not None:
            return replace(watchman_policy, practice_skill=context.practice_skill)
        gardener_policy = _research_hunt_policy(
            context,
            probe=_MIRROR_REALM_GARDENER_RESEARCH_POLICY,
            hunt=_MIRROR_REALM_GARDENER_HUNT_POLICY,
        )
        if gardener_policy is not None:
            return replace(gardener_policy, practice_skill=context.practice_skill)
        return replace(
            _UNAVAILABLE_POLICY,
            minimum_level=21,
            maximum_level=25,
            summary=(
                "The Mirror Realm gardener probe is recorded for this reboot; "
                "do not authorize combat until its route and consider evidence "
                "are reviewed."
            ),
            evidence=_MIRROR_REALM_GARDENER_RESEARCH_POLICY.evidence,
            practice_skill=context.practice_skill,
        )
    if 26 <= normalized_level <= 30:
        guardian_policy = _research_hunt_policy(
            context,
            probe=_MIRROR_REALM_GUARDIAN_RESEARCH_POLICY,
            hunt=_MIRROR_REALM_GUARDIAN_HUNT_POLICY,
        )
        if guardian_policy is not None:
            return replace(guardian_policy, practice_skill=context.practice_skill)
        if not _research_result_recorded(
            context,
            _SHIRE_BATTLE_MASTER_RESEARCH_POLICY.policy_id,
        ):
            return replace(
                _SHIRE_BATTLE_MASTER_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
        return replace(
            _UNAVAILABLE_POLICY,
            minimum_level=26,
            maximum_level=30,
            summary=(
                "The Shire battle-master probe is recorded for this reboot; "
                "do not authorize combat until its route and consider evidence "
                "are reviewed."
            ),
            evidence=_SHIRE_BATTLE_MASTER_RESEARCH_POLICY.evidence,
            practice_skill=context.practice_skill,
        )
    if 31 <= normalized_level <= 35:
        gatekeeper_policy = _research_hunt_policy(
            context,
            probe=_MINOTAUR_GATEKEEPER_RESEARCH_POLICY,
            hunt=_MINOTAUR_GATEKEEPER_HUNT_POLICY,
        )
        if gatekeeper_policy is not None:
            return replace(gatekeeper_policy, practice_skill=context.practice_skill)
        if not _research_result_recorded(
            context,
            _GALAXY_CANCER_RESEARCH_POLICY.policy_id,
        ):
            return replace(
                _GALAXY_CANCER_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
        return replace(
            _UNAVAILABLE_POLICY,
            minimum_level=31,
            maximum_level=35,
            summary=(
                "The Galaxy Cancer probe is recorded for this reboot; do not "
                "authorize combat until its route and consider evidence are "
                "reviewed."
            ),
            evidence=_GALAXY_CANCER_RESEARCH_POLICY.evidence,
            practice_skill=context.practice_skill,
        )
    if 36 <= normalized_level <= 40:
        completed = context.policy_xp_deltas or {}
        if _MIRROR_REALM_JERRY_GARCIA_RESEARCH_POLICY.policy_id not in completed:
            return replace(
                _MIRROR_REALM_JERRY_GARCIA_RESEARCH_POLICY,
                practice_skill=context.practice_skill,
            )
        return replace(
            _UNAVAILABLE_POLICY,
            minimum_level=36,
            maximum_level=40,
            summary=(
                "The Mirror Realm Jerry Garcia probe is recorded for this reboot; "
                "do not authorize combat until its route and consider evidence are "
                "reviewed."
            ),
            evidence=_MIRROR_REALM_JERRY_GARCIA_RESEARCH_POLICY.evidence,
            practice_skill=context.practice_skill,
        )
    if 41 <= normalized_level <= 45:
        if _PIT_OFFICIAL_RESEARCH_POLICY.policy_id not in (context.policy_xp_deltas or {}):
            return replace(_PIT_OFFICIAL_RESEARCH_POLICY, practice_skill=context.practice_skill)
        return replace(
            _UNAVAILABLE_POLICY, minimum_level=41, maximum_level=45,
            summary="The Pit Official probe is recorded; do not authorize combat until its evidence is reviewed.",
            evidence=_PIT_OFFICIAL_RESEARCH_POLICY.evidence,
            practice_skill=context.practice_skill,
        )
    if 46 <= normalized_level <= 50:
        chess_dwarf_policy = _research_hunt_policy(
            context,
            probe=_DWARVEN_HOME_CHESS_DWARF_RESEARCH_POLICY,
            hunt=_DWARVEN_HOME_CHESS_DWARF_HUNT_POLICY,
        )
        if chess_dwarf_policy is not None:
            return replace(chess_dwarf_policy, practice_skill=context.practice_skill)
        storn_policy = _research_hunt_policy(
            context,
            probe=_MIRROR_REALM_STORN_RESEARCH_POLICY,
            hunt=_MIRROR_REALM_STORN_HUNT_POLICY,
        )
        if storn_policy is not None:
            return replace(storn_policy, practice_skill=context.practice_skill)
        return replace(
            _UNAVAILABLE_POLICY,
            minimum_level=46,
            maximum_level=50,
            summary=(
                "The registered level-46 to 50 Dwarven Home and Mirror Realm "
                "probes are recorded for this reboot; do not authorize another "
                "route until new evidence is registered."
            ),
            evidence=(
                *_DWARVEN_HOME_CHESS_DWARF_RESEARCH_POLICY.evidence,
                *_MIRROR_REALM_STORN_RESEARCH_POLICY.evidence,
            ),
            practice_skill=context.practice_skill,
        )
    if 51 <= normalized_level <= 55:
        strange_mist_policy = _research_hunt_policy(
            context,
            probe=_DARKWOOD_STRANGE_MIST_RESEARCH_POLICY,
            hunt=_DARKWOOD_STRANGE_MIST_HUNT_POLICY,
        )
        if strange_mist_policy is not None:
            return replace(strange_mist_policy, practice_skill=context.practice_skill)
        gambler_policy = _research_hunt_policy(
            context,
            probe=_DWARVEN_HOME_GAMBLER_RESEARCH_POLICY,
            hunt=_DWARVEN_HOME_GAMBLER_HUNT_POLICY,
        )
        if gambler_policy is not None:
            return replace(gambler_policy, practice_skill=context.practice_skill)
        return replace(
            _UNAVAILABLE_POLICY,
            minimum_level=51,
            maximum_level=55,
            summary=(
                "The registered level-51 to 55 Darkwood and Dwarven Home "
                "probes are recorded for this reboot; do not authorize another "
                "route until new evidence is registered."
            ),
            evidence=(
                *_DARKWOOD_STRANGE_MIST_RESEARCH_POLICY.evidence,
                *_DWARVEN_HOME_GAMBLER_RESEARCH_POLICY.evidence,
            ),
            practice_skill=context.practice_skill,
        )
    if 56 <= normalized_level <= 60:
        master_policy = _research_hunt_policy(
            context,
            probe=_DWARVEN_HOME_MASTER_RESEARCH_POLICY,
            hunt=_DWARVEN_HOME_MASTER_HUNT_POLICY,
        )
        if master_policy is not None:
            return replace(master_policy, practice_skill=context.practice_skill)
        return replace(
            _UNAVAILABLE_POLICY,
            minimum_level=56,
            maximum_level=60,
            summary=(
                "The registered level-56 to 60 Dwarven Home master probe is "
                "recorded for this reboot; do not authorize another route "
                "until new evidence is registered."
            ),
            evidence=_DWARVEN_HOME_MASTER_RESEARCH_POLICY.evidence,
            practice_skill=context.practice_skill,
        )
    if 61 <= normalized_level <= 65:
        vampire_policy = _research_hunt_policy(
            context,
            probe=_VAMPIRE_HIVE_WOUNDED_VAMPIRE_RESEARCH_POLICY,
            hunt=_VAMPIRE_HIVE_WOUNDED_VAMPIRE_HUNT_POLICY,
        )
        if vampire_policy is not None:
            return replace(vampire_policy, practice_skill=context.practice_skill)
        return replace(
            _UNAVAILABLE_POLICY,
            minimum_level=61,
            maximum_level=65,
            summary=(
                "The registered level-61 to 65 wounded vampire probe is "
                "recorded for this reboot; do not authorize another route "
                "until new evidence is registered."
            ),
            evidence=_VAMPIRE_HIVE_WOUNDED_VAMPIRE_RESEARCH_POLICY.evidence,
            practice_skill=context.practice_skill,
        )
    if 66 <= normalized_level <= 70:
        beast_policy = _research_hunt_policy(
            context,
            probe=_TABERNACLE_HULKING_BEAST_RESEARCH_POLICY,
            hunt=_TABERNACLE_HULKING_BEAST_HUNT_POLICY,
        )
        if beast_policy is not None:
            return replace(beast_policy, practice_skill=context.practice_skill)
        return replace(
            _UNAVAILABLE_POLICY,
            minimum_level=66,
            maximum_level=70,
            summary=(
                "The registered level-66 to 70 Tabernacle hulking beast probe "
                "is recorded for this reboot; do not authorize another route "
                "until new evidence is registered."
            ),
            evidence=_TABERNACLE_HULKING_BEAST_RESEARCH_POLICY.evidence,
            practice_skill=context.practice_skill,
        )
    if 71 <= normalized_level <= 75:
        rastafarians_policy = _research_hunt_policy(
            context,
            probe=_PIRATES_SEAS_RASTAFARIANS_RESEARCH_POLICY,
            hunt=_PIRATES_SEAS_RASTAFARIANS_HUNT_POLICY,
        )
        if rastafarians_policy is not None:
            return replace(
                rastafarians_policy,
                practice_skill=context.practice_skill,
            )
        return replace(
            _UNAVAILABLE_POLICY,
            minimum_level=71,
            maximum_level=75,
            summary=(
                "The registered level-71 to 75 Pirates Seas Rastafarians "
                "probe is recorded for this reboot; do not authorize another "
                "route until new evidence is registered."
            ),
            evidence=_PIRATES_SEAS_RASTAFARIANS_RESEARCH_POLICY.evidence,
            practice_skill=context.practice_skill,
        )
    if normalized_level == 76:
        crypt_policy = _research_hunt_policy(
            context,
            probe=_GHOST_TOWN_CRYPT_THING_RESEARCH_POLICY,
            hunt=_GHOST_TOWN_CRYPT_THING_HUNT_POLICY,
        )
        if crypt_policy is not None:
            return replace(crypt_policy, practice_skill=context.practice_skill)
        return replace(
            _UNAVAILABLE_POLICY,
            minimum_level=76,
            maximum_level=76,
            summary=(
                "The registered level-76 Ghost Town crypt thing probe is "
                "recorded for this reboot; do not authorize another route "
                "until new evidence is registered."
            ),
            evidence=_GHOST_TOWN_CRYPT_THING_RESEARCH_POLICY.evidence,
            practice_skill=context.practice_skill,
        )
    if 77 <= normalized_level <= 80:
        retriever_policy = _research_hunt_policy(
            context,
            probe=_GHOST_TOWN_RETRIEVER_RESEARCH_POLICY,
            hunt=_GHOST_TOWN_RETRIEVER_HUNT_POLICY,
        )
        if retriever_policy is not None:
            return replace(
                retriever_policy,
                practice_skill=context.practice_skill,
            )
        return replace(
            _UNAVAILABLE_POLICY,
            minimum_level=77,
            maximum_level=80,
            summary=(
                "The registered level-77 to 80 Ghost Town retriever probe is "
                "recorded for this reboot; do not authorize another route "
                "until new evidence is registered."
            ),
            evidence=_GHOST_TOWN_RETRIEVER_RESEARCH_POLICY.evidence,
            practice_skill=context.practice_skill,
        )
    return replace(
        _UNAVAILABLE_POLICY,
        minimum_level=normalized_level,
        practice_skill=context.practice_skill,
    )


def _boot_kill_count(
    counts: Mapping[str, int] | None,
    target: str,
) -> int:
    expected = _normalize_mob_name(target)
    return sum(
        int(count)
        for name, count in (counts or {}).items()
        if _normalize_mob_name(name) == expected
    )


def _research_result_recorded(context: ProgressionContext, policy_id: str) -> bool:
    result = (context.research_results or {}).get(policy_id)
    if not isinstance(result, Mapping):
        return False
    return (
        result.get("boot_id") == context.world_boot_id
        and isinstance(result.get("observed"), bool)
    )


def _research_result_was_observed(
    context: ProgressionContext,
    policy_id: str,
) -> bool:
    result = (context.research_results or {}).get(policy_id)
    return bool(
        isinstance(result, Mapping)
        and result.get("boot_id") == context.world_boot_id
        and result.get("observed") is True
    )


def _research_result_is_stale(
    context: ProgressionContext,
    policy_id: str,
) -> bool:
    result = (context.research_results or {}).get(policy_id)
    boot_id = result.get("boot_id") if isinstance(result, Mapping) else None
    return bool(
        context.world_boot_id
        and isinstance(boot_id, str)
        and boot_id
        and boot_id != context.world_boot_id
    )


def _research_result_is_viable(context: ProgressionContext, policy_id: str) -> bool:
    result = (context.research_results or {}).get(policy_id)
    return bool(
        isinstance(result, Mapping)
        and result.get("boot_id") == context.world_boot_id
        and result.get("observed") is True
        and result.get("viable") is True
    )


def _research_hunt_policy(
    context: ProgressionContext,
    *,
    probe: ProgressionPolicy,
    hunt: ProgressionPolicy,
) -> ProgressionPolicy | None:
    """Promote a reboot-scoped viable probe into a bounded live hunt."""
    if context.last_policy_id == hunt.policy_id:
        if (
            (context.policy_xp_deltas or {}).get(hunt.policy_id, 0) > 0
            and _research_result_is_viable(context, hunt.policy_id)
        ):
            return hunt
        if _research_result_recorded(context, hunt.policy_id):
            return None
        if any(
            str(context.last_fastwalk_abort_reason or "").startswith(prefix)
            for prefix in (
                _FIELD_RESOURCE_ABORT_PREFIX,
                _FIELD_CROWD_ABORT_PREFIX,
            )
        ):
            return hunt
        return probe
    if context.last_policy_id == probe.policy_id:
        if str(context.last_fastwalk_abort_reason or "").startswith(
            ("field room contained ", _FIELD_CROWD_ABORT_PREFIX)
        ):
            # A crowd checkpoint is route-state evidence, not a new target
            # result. Move to another policy before retrying this probe.
            return None
        if _research_result_is_viable(context, probe.policy_id):
            return hunt
        if _research_result_recorded(context, probe.policy_id):
            return None
    if (
        _research_result_is_viable(context, probe.policy_id)
        and not _research_result_recorded(context, hunt.policy_id)
    ):
        return hunt
    if (
        _research_result_recorded(context, probe.policy_id)
        or _research_result_recorded(context, hunt.policy_id)
    ):
        return None
    return probe


def _next_productive_research_hunt(
    context: ProgressionContext,
    policies: tuple[ProgressionPolicy, ...],
) -> ProgressionPolicy | None:
    """Rotate to a positive same-reboot hunt after probes consume themselves."""
    productive = tuple(
        policy
        for policy in policies
        if policy.policy_id not in context.excluded_policy_ids
        and (context.policy_xp_deltas or {}).get(policy.policy_id, 0) > 0
        and _research_result_is_viable(context, policy.policy_id)
    )
    if not productive:
        return None
    previous_index = next(
        (
            index
            for index, policy in enumerate(productive)
            if policy.policy_id == context.last_policy_id
        ),
        -1,
    )
    return productive[(previous_index + 1) % len(productive)]


def _next_productive_policy(
    rotation: tuple[ProgressionPolicy, ...],
    *,
    previous_index: int,
    xp_deltas: Mapping[str, int] | None,
    minimum_xp: int = _MEANINGFUL_FIELD_SEGMENT_XP,
) -> ProgressionPolicy:
    ordered = rotation[previous_index + 1 :] + rotation[: previous_index + 1]
    if not xp_deltas:
        return ordered[0]
    for policy in ordered:
        recent_xp = xp_deltas.get(policy.policy_id)
        if recent_xp is None or recent_xp >= minimum_xp:
            return policy
    return max(ordered, key=lambda policy: xp_deltas.get(policy.policy_id, 0))


def _normalize_mob_name(value: str) -> str:
    words = value.casefold().split()
    while words and words[0] in {"a", "an", "the"}:
        words.pop(0)
    return " ".join(words)


def canonical_class_name(value: str) -> str:
    return _ARCHETYPES.class_profile(value).name
