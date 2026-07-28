from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace

from .archetypes import archetype_registry


_ARCHETYPES = archetype_registry()
_MEANINGFUL_FIELD_SEGMENT_XP = 50
_FOREST_BEAR_CLAWS_MINIMUM_NONFLIGHT_MOVE = 300
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

    @property
    def executable(self) -> bool:
        return self.execution is not None and self.status in {"verified", "research"}

    def blocks_message(self, character_class: str) -> str:
        if self.status == "research":
            return (
                f"Policy {self.policy_id} is research-gated for {character_class}. "
                "Its route is observed, but its combat and XP loop are not yet verified."
            )
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
    needs_capacity_relief: bool = False
    has_food: bool = True
    has_weapon: bool = True
    needs_basic_gear: bool = False
    needs_body_gear_recovery: bool = False
    needs_school_wrist_float: bool = False
    needs_gremlin_waist: bool = False
    needs_daycare_ring: bool = False
    needs_war_dog_collar: bool = False
    needs_piercing_weapon_upgrade: bool = False
    piercing_weapon_upgrade_attempted: bool = False
    movement_available: int = 0
    movement_capacity: int = 0
    has_sanctuary_potion: bool = False
    has_flight: bool = True
    can_attempt_flight_purchase: bool = False
    flight_purchase_failed: bool = False
    boot_kill_counts: Mapping[str, int] | None = None
    policy_xp_deltas: Mapping[str, int] | None = None
    stalled_segments: int = 0
    last_policy_id: str | None = None

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

_LIQUIDATE_LOOT_POLICY = ProgressionPolicy(
    policy_id="liquidate-loot",
    minimum_level=2,
    maximum_level=None,
    status="verified",
    execution="sell-loot",
    summary="Sell expendable equipment at compatible safe Midgaard shops.",
    evidence=(
        "Live run 323 sold Ambush armour, returned to the Mage Guild, saved, and quit safely.",
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
    summary="Buy, wield, and verify a lightweight dagger at the safe Midgaard weapon shop.",
    evidence=(
        "DD4 source resets object 3020, a one-pound dagger, on the weaponsmith in room 3011.",
        "DD4 source prices the dagger at 10 copper before the weaponsmith's reboot-fuzzy markup.",
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
        "The room reset creates two old dolls carrying pink ice rings, so one bounded visit can fill both finger slots.",
        "The same route returns through room 6602, where the old wrinkled nanny carries a linen robe granting wisdom and mana.",
        "The old doll is reached two rooms beyond the verified Dwarven Daycare route; other source resets in the room are low-level non-aggressive dolls and youths.",
        "These are three bounded required-loot kills; below-band targets remain forbidden for XP progression.",
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

_FOREST_BEAR_CLAWS_UPGRADE_POLICY = ProgressionPolicy(
    policy_id="forest-bear-claws-upgrade-10-14",
    minimum_level=10,
    maximum_level=14,
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


def policy_for(
    level: int | float | None,
    character_class: str,
    *,
    subclass: str | None = None,
    has_large_sack: bool = False,
    has_sellable_loot: bool = False,
    needs_capacity_relief: bool = False,
    has_food: bool = True,
    has_weapon: bool = True,
    needs_basic_gear: bool = False,
    needs_body_gear_recovery: bool = False,
    needs_school_wrist_float: bool = False,
    needs_gremlin_waist: bool = False,
    needs_daycare_ring: bool = False,
    needs_war_dog_collar: bool = False,
    needs_piercing_weapon_upgrade: bool = False,
    piercing_weapon_upgrade_attempted: bool = False,
    movement_available: int = 0,
    movement_capacity: int = 0,
    has_sanctuary_potion: bool = False,
    has_flight: bool = True,
    can_attempt_flight_purchase: bool = False,
    flight_purchase_failed: bool = False,
    boot_kill_counts: Mapping[str, int] | None = None,
    policy_xp_deltas: Mapping[str, int] | None = None,
    stalled_segments: int = 0,
    last_policy_id: str | None = None,
) -> ProgressionPolicy:
    return select_policy(
        ProgressionContext.from_values(
            level,
            character_class,
            subclass=subclass,
            has_large_sack=has_large_sack,
            has_sellable_loot=has_sellable_loot,
            needs_capacity_relief=needs_capacity_relief,
            has_food=has_food,
            has_weapon=has_weapon,
            needs_basic_gear=needs_basic_gear,
            needs_body_gear_recovery=needs_body_gear_recovery,
            needs_school_wrist_float=needs_school_wrist_float,
            needs_gremlin_waist=needs_gremlin_waist,
            needs_daycare_ring=needs_daycare_ring,
            needs_war_dog_collar=needs_war_dog_collar,
            needs_piercing_weapon_upgrade=needs_piercing_weapon_upgrade,
            piercing_weapon_upgrade_attempted=piercing_weapon_upgrade_attempted,
            movement_available=movement_available,
            movement_capacity=movement_capacity,
            has_sanctuary_potion=has_sanctuary_potion,
            has_flight=has_flight,
            can_attempt_flight_purchase=can_attempt_flight_purchase,
            flight_purchase_failed=flight_purchase_failed,
            boot_kill_counts=boot_kill_counts,
            policy_xp_deltas=policy_xp_deltas,
            stalled_segments=stalled_segments,
            last_policy_id=last_policy_id,
        )
    )


def select_policy(context: ProgressionContext) -> ProgressionPolicy:
    normalized_level = context.level
    if normalized_level < 2:
        return _STARTER_POLICY
    if context.has_sellable_loot:
        return _LIQUIDATE_LOOT_POLICY
    if context.needs_capacity_relief:
        return _VAULT_SPARE_GEAR_POLICY
    if not context.has_food:
        return _RESTOCK_POLICY
    if not context.has_weapon:
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
    if (
        context.character_class == "thief"
        and 10 <= normalized_level <= 14
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
        return _MORIA_SANCTUARY_LEVEL_TEN_POLICY
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
            recent_xp = completed.get(
                _FLESHMONGER_GUARD_CIRCUIT_POLICY.policy_id
            )
            if recent_xp is None or recent_xp > 0:
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
        if (
            _FLESHMONGER_GUARD_LEVEL_TEN_RESEARCH_POLICY.policy_id
            in (context.policy_xp_deltas or {})
        ):
            return replace(
                _UNAVAILABLE_POLICY,
                minimum_level=11,
                practice_skill=context.practice_skill,
            )
        return replace(
            _FLESHMONGER_GUARD_LEVEL_TEN_RESEARCH_POLICY,
            minimum_level=11,
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
        nanny_is_productive = nanny_recent_xp is None or nanny_recent_xp > 0
        established_circuits_depleted = all(
            recent_xp is not None and recent_xp <= 0
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
            return replace(
                _GNOME_GUARD_CASTER_LEVEL_SEVEN_POLICY,
                practice_skill=context.practice_skill,
            )
        if (
            field_caster
            and not established_circuits_depleted
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
            and context.last_policy_id
            == _DAYCARE_ARMED_GUARD_LEVEL_SEVEN_POLICY.policy_id
        ):
            return replace(
                _GNOME_LEVEL_SEVEN_POLICY,
                practice_skill=context.practice_skill,
            )
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


def _next_productive_policy(
    rotation: tuple[ProgressionPolicy, ...],
    *,
    previous_index: int,
    xp_deltas: Mapping[str, int] | None,
) -> ProgressionPolicy:
    ordered = rotation[previous_index + 1 :] + rotation[: previous_index + 1]
    if not xp_deltas:
        return ordered[0]
    for policy in ordered:
        recent_xp = xp_deltas.get(policy.policy_id)
        if recent_xp is None or recent_xp >= _MEANINGFUL_FIELD_SEGMENT_XP:
            return policy
    return max(ordered, key=lambda policy: xp_deltas.get(policy.policy_id, 0))


def _normalize_mob_name(value: str) -> str:
    words = value.casefold().split()
    while words and words[0] in {"a", "an", "the"}:
        words.pop(0)
    return " ".join(words)


def canonical_class_name(value: str) -> str:
    return _ARCHETYPES.class_profile(value).name
