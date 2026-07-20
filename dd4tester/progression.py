from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace

from .character import CLASSES


CLASS_PRACTICE_SKILLS = {
    "mage": "magic missile",
    "cleric": "cure light",
    "thief": "backstab",
    "warrior": "kick",
    "psionic": "mind thrust",
    "shifter": "shapeshift",
    "brawler": "kick",
    "ranger": "kick",
    "smithy": "repair",
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
        return self.execution is not None and self.status == "verified"

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

_MORIA_SNAKE_POLICY = ProgressionPolicy(
    policy_id="moria-circuit-7-10",
    minimum_level=7,
    maximum_level=10,
    status="research",
    execution=None,
    summary=(
        "Mage field progression through three live-considered Moria targets, "
        "with one recall after the bounded circuit."
    ),
    evidence=(
        "DD4 source: the official Moria fastwalk reaches room 4014; two north moves reach room 4025.",
        "DD4 source: room 4025 has one level-7 garter-snake reset and no other mobile reset.",
        "Live run 252: level-7 mage Ararisa considered the snake a perfect match, killed it for 373 XP, and returned to room 3019 at full health and mana.",
        "DD4 source: the circuit links a level-6 hobgoblin in room 4059, a level-5 centipede in room 4060, and a level-7 large orc in room 4022; same-room hobgoblin and orc fallbacks cover wandering mobiles.",
        "Area-file mobile levels are approximate; every field target is checked with live consider output before combat.",
        "Live run 264: a wandering veteran warrior intercepted the static route, forced repeated combat extraction, and produced a net XP loss; the circuit is not safe for unattended execution.",
    ),
    practice_skill="magic missile",
    segment_kill_limit=1,
)

_MIDENNIR_LEVEL_SEVEN_POLICY = ProgressionPolicy(
    policy_id="midennir-goblin-7-8",
    minimum_level=7,
    maximum_level=8,
    status="verified",
    execution="midennir-hunt",
    summary=(
        "One bounded, live-considered Miden'nir goblin hunt with conservative "
        "multi-attacker withdrawal, recall, and healer recovery."
    ),
    evidence=(
        "Live runs 268, 270, 272, and 275 killed Miden'nir goblins for 361, 210, 244, and 216 XP.",
        "Live runs 270 and 274 safely withdrew from a wandering level-9 horseman and two simultaneous level-7 goblins.",
        "Live run 275 returned to the Mage Guild at full health and mana after one bounded kill.",
        "DD4 source resets a mountain goblin in room 3506, exactly one east of the official fastwalk endpoint.",
        "Empty or crowded spawn windows are retryable campaign checkpoints, not reasons to force combat.",
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
        "Live run 326 killed a reboot-fuzzed level-7 war dog for 249 XP and returned safely to the Midgaard healer.",
        "Live run 327 lost 44 XP after three magic-missile attempts failed to finish the higher-HP wounded goblin.",
        "The route excludes the level-8 raider, level-10 guard, and the cave complex.",
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
        "The route between the Mage Laboratory and Weapon Shop uses only safe Midgaard rooms.",
    ),
    practice_skill=None,
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
        "The workflow checks current stock and affordability instead of assuming a fixed reboot price.",
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
    has_large_sack: bool = False,
    has_sellable_loot: bool = False,
    has_food: bool = True,
    has_weapon: bool = True,
    has_sanctuary_potion: bool = False,
    has_flight: bool = True,
    can_attempt_flight_purchase: bool = False,
    flight_purchase_failed: bool = False,
    boot_kill_counts: Mapping[str, int] | None = None,
    stalled_segments: int = 0,
) -> ProgressionPolicy:
    normalized_level = int(level or 0)
    canonical_class = canonical_class_name(character_class)
    if normalized_level < 2:
        return _STARTER_POLICY
    if has_sellable_loot:
        return _LIQUIDATE_LOOT_POLICY
    if not has_food:
        return _RESTOCK_POLICY
    if not has_weapon:
        return _REARM_WEAPON_POLICY
    if normalized_level < 6:
        return replace(
            _MUD_SCHOOL_ARENA_POLICY,
            practice_skill=CLASS_PRACTICE_SKILLS[canonical_class],
        )
    if canonical_class == "mage" and normalized_level == 7:
        return _MIDENNIR_LEVEL_SEVEN_POLICY
    if canonical_class == "mage" and 8 <= normalized_level < 10:
        if not has_large_sack:
            return _MIDENNIR_SACK_POLICY
        if normalized_level == 8:
            war_dog_kills = _boot_kill_count(boot_kill_counts, "war dog")
            goblin_kills = _boot_kill_count(boot_kill_counts, "goblin")
            if (
                stalled_segments % 2 == 0
                and war_dog_kills >= 5
                and goblin_kills < war_dog_kills
            ):
                return _MIDENNIR_LEVEL_EIGHT_POLICY
            return _AMBUSH_LEVEL_EIGHT_POLICY
        if (
            not has_flight
            and can_attempt_flight_purchase
            and not flight_purchase_failed
        ):
            return _BUY_FLIGHT_POLICY
        if has_sanctuary_potion:
            return _AMBUSH_VILE_LEVEL_NINE_POLICY
        large_hobgoblin_kills = _boot_kill_count(
            boot_kill_counts, "large hobgoblin"
        )
        vile_goblin_kills = _boot_kill_count(boot_kill_counts, "vile goblin")
        exterior_kills = (
            _boot_kill_count(boot_kill_counts, "war dog")
            + _boot_kill_count(boot_kill_counts, "wounded goblin")
        )
        if (
            boot_kill_counts
            and stalled_segments == 0
            and (
                vile_goblin_kills >= large_hobgoblin_kills > 0
                or exterior_kills >= 4
            )
        ):
            if (
                not has_flight
                and can_attempt_flight_purchase
                and not flight_purchase_failed
            ):
                return _BUY_FLIGHT_POLICY
            return _MORIA_SANCTUARY_LEVEL_NINE_POLICY
        return _AMBUSH_LEVEL_NINE_POLICY
    if canonical_class == "mage" and normalized_level == 10:
        if (
            not has_flight
            and can_attempt_flight_purchase
            and not flight_purchase_failed
        ):
            return _BUY_FLIGHT_POLICY
        if has_sanctuary_potion:
            return _AMBUSH_VILE_LEVEL_TEN_POLICY
        return _MORIA_SANCTUARY_LEVEL_TEN_POLICY
    if normalized_level < 10:
        return replace(
            _MUD_SCHOOL_RESEARCH_POLICY,
            practice_skill=CLASS_PRACTICE_SKILLS[canonical_class],
        )
    return replace(
        _UNAVAILABLE_POLICY,
        minimum_level=normalized_level,
        practice_skill=CLASS_PRACTICE_SKILLS[canonical_class],
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


def _normalize_mob_name(value: str) -> str:
    words = value.casefold().split()
    while words and words[0] in {"a", "an", "the"}:
        words.pop(0)
    return " ".join(words)


def canonical_class_name(value: str) -> str:
    normalized = " ".join(value.strip().casefold().replace("-", " ").split())
    try:
        return CLASSES[normalized]
    except KeyError as exc:
        available = ", ".join(sorted(CLASSES))
        raise ValueError(f"unknown class {value!r}; choose one of: {available}") from exc
