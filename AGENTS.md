# Repository Guidelines

## Project Structure

The `dd4tester/` package contains the asyncio Telnet client, GMCP parser,
scenario runner, persistence layer, state model, and CLI. YAML scenarios live
in `scenarios/`; keep reusable scenarios small and non-destructive. Tests are
under `tests/`, with sanitized protocol samples in `tests/fixtures/`. Generated
SQLite databases and JSONL transcripts belong in `runs/` and `transcripts/`;
both directories are intentionally ignored by Git. Generated declarative HERO
requests, profiles, and campaign files belong under `runs/heroes/`.

The master product boundary is one character-independent autonomy engine that
can create any source-legal race/class/subclass request and progress it to level
100 without manual gameplay. Sex is cosmetic in DD4: accept and preserve it for
identity, but do not multiply progression coverage across sex choices. Never
add character-name-specific behavior to satisfy a live run.

Never modify the Dragons Domain IV core repository from this project.
Treat its public source and area files as valid read-only evidence for routes,
resets, mob flags and levels, drops, shops, prerequisites, and mechanics.
Treat VNUMs as separate namespaces: room, mobile, object, and object-set VNUMs
are unique within their category, but the same number may appear across them.
Do not treat an object prototype's trailing numeric level as the live level of
ordinary field loot. Follow `db.c` reset order: `G`, `E`, and ordinary `O`
loads derive from the active preceding mobile reset with mobile and object
fuzz; `P` inherits the loaded container level, `I` uses its explicit level, and
low-level Mud School mobile loot is forced to level one. Keep the prototype
value and reset-derived load range separately, and confirm consequential wear
or sale decisions with live `identify` evidence when available.
For randomized mazes, use live GMCP exit destination room VNUMs to follow a
source-backed room path; never assume the area-file direction labels remain
stable after reset.
The Shadow Grove (rooms 1300-1309) is a randomized `no_recall` maze. For
return-home and fastwalk recovery, navigate by live GMCP exits to room 1300,
then follow the source-backed reverse route through Haon Dor rooms 6137,
6136, 6135, 6129, 6128, 6126, 6127, 6112, 6111, 6110, 6109, 6108, 6103,
6102, 6101, 6100, 6004, 6003, 6002, 6001, 6000, and Midgaard 3052, 3040,
3012, 3013, 3014, 3005, 3001, 3054. Never rely on `recall` from a Shadow
Grove room. Live run 2623 reached and exited the grove's Galaxy approach
without invalid movement; direct recovery run 2620 also returned Kestrel to
healer room 3054.
Before training or automating a skill, read both its current in-game help and
its source implementation. Record whether it is active or passive, its legal
position and target, pulse/mana cost, effect formula, prerequisites, and any
equipment or status constraints; never infer behavior from the skill name.
Mirror source `do_stun` exactly for classes whose prerequisite graph exposes
it, currently base Warrior and Bounty Hunter: stun is a pre-combat action that
requires a pounding, blasting, or crushing weapon and cannot be issued after
combat begins. When a character knows both `stun` and `backstab`, retain the
best legal weapon for each action, wield the pounding weapon for the stun
attempt, then switch to the piercing weapon before backstab. Do not assume
`stun` is available to classes whose prerequisite graph does not expose it.
For a thief, the primary wield slot must hold a source-matched piercing weapon
whenever backstab is available; preserve it through sale, vault, and capacity
maintenance, recovery stance, and pre-level stance, and persist the audited
`[weapon]` slot separately from the full worn-equipment list. For a Warrior or
active Bounty Hunter, acquire and retain a separate source-matched blunt weapon
before training or relying on stun. The
opener is
`wield <pounding>`, `stun <exact target>`, `wield <piercing>`, then
`backstab <exact target>`; restore the piercing weapon before ordinary combat
or logout.
For classes whose source graph exposes `disarm`, build its exact prerequisites
after the profile's earlier damage gates. Value `grip` as passive resistance
where available. Once learned and wielding a weapon, attempt `disarm` early
against each exact opponent, alternate failed retries with recurring damage
actions, and stop after success or live confirmation that the target is
unarmed.
Maintain a source-backed leveling-value analysis for every base class and
level-30 subclass, not only active test characters. Apply subclass priorities
only after live state confirms the character has subclassed. Practice order
must account for prerequisite
gateways, current trainer listings and caps, separate physical/intellectual
budgets, direct damage, mitigation, sustain, mobility, and whether the combat
runner can actually use the result. Mark unsupported rotations analysis-only
rather than spending practices on unusable skills.
Keep representative characters from different base classes in active rotation.
Use their live evidence to improve shared class-aware policy, and never let
progress on one character become a name-specific substitute for generic
race/class support.
Use explicit equipment stances. Combat gear ranks positive damroll first, then
hitroll, swiftness, and critical chance. Recovery gear favors hit points for
martial classes and mana for spellcasters; derive hybrid priorities from the
class profile. For weapons, rank estimated per-hit damage from source dice plus
damroll so a minor modifier cannot outrank a materially stronger weapon; retain
the damroll, hitroll, swiftness, then critical order for non-weapon slots.
Spellcasting combat plans must combine source-verified damage spells with
available damage-reduction spells rather than spending all mana on damage.
Apply character titles and descriptions only during initial identity setup;
use persisted command evidence to avoid recreating them on later logins.
For characters below level 20, treat an affect's name as observable but do not
base decisions on GMCP duration or modifier details hidden by `do_affects`.
An affect remains active while listed; duration zero means less than one hour.
Treat each skill table `msg_off` string as a human-visible expiry signal, then
confirm the removal from the next affect snapshot before dependent travel.
Before source-backed research, and at least once per active working day,
fast-forward `runs/dd4-source` from upstream with `git pull --ff-only`; record
the revision used for consequential policy decisions.
Confirm dynamic behavior such as wandering, prices, and combat risk with live,
redacted transcripts before promoting it into an autonomous policy. Scope
prices, kill repetition, applicable object instance limits, and observed spawn
counts to the `DD was started at ...` reboot identity; never carry them across
reboots. Instance limiting applies only to the few objects whose source
definitions use it, not to mobiles.
Before a live area launch, parse each registered mobile's exact area-file room
description through the target recognizer; use live output to confirm presence
and dynamic reset state, not to discover static mobile display lines.
Never attack for XP when `consider` returns a `do_consider` result from the
`diff <= -5` or `diff <= -10` branches; those targets are too low to be useful.
Use the source level-difference branch as the level-band decision: the separate
hitpoint comparison text is descriptive combat-risk context, not a substitute
for level difference and not an automatic rejection of an otherwise viable
level-band target.
Persist that below-band result against the selected policy for the current
character level and reboot. Do not revisit the same surviving mobile until the
level or reboot identity changes.
The next registered high-level extension is the 46-50 Dwarven Home chess-room
dwarf (mobile 20514, room 20530), followed by the Mirror Realm Storn fallback
(mobile 19034, room 19114), both source-registered from revision `bf745c3` as
sentinel/stay-area, no-special probes. Their combat policies remain research-
gated until live exact-target, crowd, and level-difference evidence promotes
them; HP thresholds govern combat withdrawal only.
The next registered extension is the 51-55 Darkwood strange mist (mobile 11200,
room 11211) followed by the Dwarven Home gambler (mobile 20515, room 20531),
also source-registered from `bf745c3` as sentinel/stay-area, no-special probes.
Bind their live lines to `strange mist` and `dwarf`; the level-difference branch
of `consider` decides XP-band eligibility, while hitpoint text only informs
combat-risk gates.
The 56-60 extension is the Dwarven Home master of the house (mobile 20517,
room 20537), source-registered from `bf745c3` as a single sentinel/stay-area,
no-special target with a source-equipped dwarven dagger. Bind its live line to
`master of the house`; require the same exact-target, single-reset,
level-difference, health, and healer-return gates before promoting a hunt.
The 61-65 extension is the Vamp Hive wounded vampire (mobile 25652, room
25641), source-registered from `bf745c3` as a single non-aggressive,
stay-area, no-special mobile with source-equipped sharp fangs, black cloth
trousers, and an elegant black cane. Use `where vampire` before the bounded
reset-room search; bind the source line to `wounded vampire` and do not expand
the wandering search space without fresh live room evidence.
The 66-70 extension is the Tabernacle hulking beast (mobile 39013, room
39016), source-registered from `bf745c3` as a single sentinel/non-aggressive,
no-special target with no source equipment or room companion. Bind its source
line to `hulking beast` and keep the exact-room, level-difference, health, and
healer-return gates before promoting combat.
Live run 2640 reached the Shire research circuit at level 18 and safely returned
to healer room 3054 with full health, but the MUD connection dropped during a
field `look`. Reconnecting placed Kestrel in Midgaard while the local cursor
still expected room 1123; `StarterPolicy.on_connection_closed()` therefore
marks any in-world field route for healer recovery, clears pending travel state,
and lets the campaign retry the segment instead of treating stale navigation as
current-room evidence.
Rerun 2642 used SQLite event freshness rather than JSONL file size as its live
watchdog: the level-18 Shire probe completed without combat, found the target
absent, returned Kestrel to healer room 3054 at full health, and checkpointed
the campaign for a later reset retry.
Treat `hide` as a stationary ambush or avoidance skill because ordinary
movement removes it; do not use it as travel concealment.
Before a mage field fastwalk, establish known invisibility at recall so
wandering Midgaard greet-program mobiles cannot replace a productive target
with a trivial forced fight.
For verified hunts, continue until a meaningful discomfort threshold: low
health without vetted local recovery, an uncured disabling affect, unusable
food or water when needed, insufficient movement, encumbrance, or exhausted
local targets. Prefer source-vetted local sleep and multi-target circuits over
recalling after one safe kill. Before an imminent level, issue `train` for the
class profile's current primary stat and wear all legal stat-improving gear.
Before any hunt fastwalk from recall, refill the carried water skin in room
3005, drink there, and return north; never rely on a stale in-memory thirst
flag for a long route.
Tune autonomous field play 50% more aggressively than the original baseline:
tolerate recoverable damage, use 360-second bounded fights, continue circuits
at 22.5% health with 7.5% mana and 5% movement, leave the healer at 37.5%
health and 15% mana, ordinarily withdraw at 15% health, and finish a
lower-level half-dead opponent down to 10%. Retain a 67.5% departure floor
for high-risk and aggressive targets. Keep death traps, unknown high-level
enemies, unsafe crowds, disabling affects, and unsupplied hunger or thirst as
hard withdrawal boundaries.
Do not count source-proven or live-level-confirmed below-band mobiles as an
unsafe crowd. They must not block selection of a useful-band target or trigger
a flee when they join its combat. Never select them deliberately for XP, but
finish unavoidable trivial combat so it cannot stall the productive hunt.
Treat duplicate same-prototype targets as a possible assist crowd: `fight.c`
allows an idle mobile sharing the engaged mobile's prototype to join
probabilistically. Skip that stop and continue to later registered circuit
rooms; do not let a matching target in the old room satisfy the next routed
stop before its destination is reached.
Treat an unapproved attacker that joins after combat starts as the same
retryable crowd condition: flee, recover, discard the interrupted research
result, and recheck the source target on the next bounded segment.
Before HERO renaming is available, use source-backed keywords and keep active
gear directly accessible; put spare ambiguous items in containers or the vault.
Never guess object or mobile command keywords when the entity exists in the
public source. Parse and use its source keyword list; display-text noun
inference is only a temporary fallback for genuinely uncatalogued live
entities and must not be promoted into policy without source confirmation.
Enable DD4 `TARGETMODE` before a combat fastwalk. Bind each live `[#number]`
selector only to a mobile whose target-mode line matches its source room
description, and use that exact selector for `consider`, the combat opener, and
targeted combat actions. Never promote an object selector into the mobile map,
persist a live selector across connections or reboots, or replace the reusable
source identity in policy/evidence with an ephemeral selector.
When a registered wandering target appears in any source-vetted room while its
circuit is active, stop before the next route step and run the normal crowd,
health, level-ceiling, and `consider` gates against that live selector.
Persisted GMCP inventory descriptions may still contain an ephemeral
`[#number]` prefix from the connection that recorded them. Strip that prefix
before source-catalog matching, sale planning, equipment comparison, and
liquidation signatures; never treat it as part of an object's identity. Live
run 2047 validated that this recognizes Aruncus's no-drop strange amulet,
triggers `heal curse`, destroys it, and disposes of the remaining unsellable
loot safely.
For exact stay-area wanderers, issue a source-keyword `where` preflight at the
area endpoint. If DD4 returns `You fail to find anyone by that name.`, mark the
target absent and recall rather than enumerating the full area; if `where`
reports a presence, retain the bounded source-room search. Live run 2048 spent
about 290 seconds searching for a globally absent Kodiak and motivated this
gate.
Treat profession-visible empty `eq all` slots as equipment debt. Prefer usable
mob drops, then inexpensive class-legal Midgaard basics; after major gear loss,
revisit Mud School first and repeat its course to recover free starter drops.
Never wear a finger item that applies a strength penalty. For low-level
characters with two legal finger slots, prefer two pink ice rings; each gives
+1 strength and +6 hit points. Only the old-doll reset in Dwarven Daycare room
6605 equips object 6601. A same-vnum doll loads without a ring in room 6604 and
may wander into 6605, so verify the corpse drop and use the bounded
three-productive-segment retry after killing a non-carrier. An empty oversized
container may be lodged temporarily to make room for required drops only after
`look in` proves it is empty.
A thief whose best accessible piercing weapon is still materially weaker than
Forest object 18000 must retain the bounded kodiak upgrade through level 29.
The claws are source type 5 weaponry, not a body-part object: they deal 6d12
piercing damage and add +3 hit roll. Keep the three-productive-segment cooldown
after an absent bear and stop retrying as soon as carried or worn gear matches
or exceeds that source damage score. A `where kodiak` result of `River bed`
does not authorize pursuit: those rooms hold the excluded aggressive mosquito
and wasp resets.
When that Forest attempt is cooling down and a thief still uses a weaker
piercing weapon, use the Old Thalos intermediate tier. Object 5252 is a 2d5
long slim dagger with +1 hitroll and +1 damroll, carried by source-level-9
lamias. Issue `where lamia` at the official route endpoint, then search only
the registered lamia-only reset rooms. Keep this tier's retry cooldown
independent from the Forest cooldown. Live run 2128 acquired and equipped the
dagger after recovering from a combat disarm, raising damroll from 3 to 4
without taking damage. During `rearm-primary-weapon`, inspect the wield slot
after `eq all`; for a thief, directly wield a carried source-matched piercing
weapon before considering a shop trip, and never accept an arbitrary wielded
weapon as the primary when backstab gear is available. Live run 2338 verified
the persisted long slim dagger, exact-selector backstab, a 484-XP nobleman
kill, and safe healer recovery after this maintenance gate.
The old dolls can wander north into room 6603. Check up to two exact old-doll
selectors there before moving south, then keep two independent room-6605
checks. Live run 2042 saw both dolls in 6603 and proved that walking through
that room to the empty reset room loses the recovery opportunity.
An absent or crowded ring carrier is a temporary area-state miss, not a
reboot-scoped failure. Rotate through three productive field segments before
retrying the Daycare ring recovery during the same reboot; a reboot permits an
immediate retry.
A registered one-off gear recovery may attack a source-proven low-level carrier
after a below-band `consider`, but must record that the kill is solely for a
required missing item and never treat it as an XP policy. Do not consume a
sanctuary potion for that deliberately below-band required-loot kill; preserve
protection consumables for progression combat.
For mages, treat `summon familiar` as a source-backed risk-control candidate:
cast it outdoors, group the follower, and order it to open combat only after a
live bounded probe. Account for the spell's 100-mana cost and the familiar's
level-weighted group XP dilution; do not use it for trivial required-loot kills.
Leave a depleted hunt area before waiting because occupied areas reset more
slowly.
Use the recorded per-policy XP delta to rotate away from zero-XP field
segments; in particular, an empty Circus segment at level seven must not send
the next run back to an already empty Moria circuit.
Before an imminent level, select a source-backed training stat and skip any
stat whose parenthesized permanent score is followed by `+`. Prefer
constitution for low-level martial characters because it directly increases
hitpoint gains.
Do not fall back to Mud School after live `consider` evidence shows its entire
opponent set is below the useful XP band. Level-eight thief and warrior
campaigns rotate the registered three-target Circus policy with the isolated
Moria large-orc probe and the three-stop Gnome guard circuit. Engage a Gnome
guard only when it is the room's sole mobile and passes live `consider`; reject
duplicate guards or a guard accompanied by any wanderer. Keep
the Miden'nir Ambush exterior research-gated because a wandering dark horseman
can join otherwise suitable combat.
Level-seven Gnome campaigns continue from the hermit to the isolated miner
resets in rooms 1563 and 1565; each stop retains independent crowd, live
`consider`, health, mana, movement, and encumbrance gates.
At thief level 13, rotate an empty Aruncus sweep through Fleshmonger, then
return to Aruncus. Do not repeat Bardoosh after a completed no-kill combat
probe until backstab becomes trainable or materially stronger gear changes the
matchup. At thief level 16, one empty Rock Toad circuit may trigger one bounded
Bardoosh retry only after the generic progression path has prioritized
backstab and a stronger piercing weapon. Preserve the exact-target, live
consider, 90% health, +1 live-level, sole-target, disarm recovery, and healer
return gates; never immediately repeat this fallback. Live run 2209 proved the
new capability boundary: repeated knife attacks and automatic long slim dagger
recovery killed level-12 Bardoosh for 535 XP without Kestrel taking damage,
returned three saleable drops, and finished at healer room 3054 with full
health and movement. This positive kill promotes a reusable level-16-only
hunt. Select it after a Rock Toad segment has given Ambush time to reset
outside the area, including a non-actionable Toad pass when Bardoosh's latest
verified result remains productive, then rotate back to Mahn-Tor after every
Bardoosh pass. A zero-XP verified Bardoosh result blocks another Bardoosh
retry.
Maintenance such as flight purchase, optional weapon recovery, and loot sale
must preserve this last-progression-policy cadence. Live run 2217 proved the
preserved transition across two maintenance passes, killed Bardoosh for 474 XP
without player damage, and returned three drops to healer room 3054. Run 2219
then proved the required reverse transition through loot-sale maintenance,
killing a level-13 Rock Toad for 303 XP and returning safely. Runs 2224 and
2225 correctly rejected three crowded Toads but exposed an immediate zero-XP
repeat; run 2226 proved the corrected rotation by killing Bardoosh for 517 XP
and returning safely at full health.
If a specialized opener such as `backstab` or `shoot` is rejected while the
exact target remains present, immediately retry once with normal `kill` using
the same TARGETMODE selector. During recurring combat actions, treat a changed
GMCP enemy HP snapshot as watchdog progress; unchanged enemy and character
state must still retain the bounded repeated-command watchdog. Live run 2215
proved both behaviors by finishing a suspicious level-13 Rock Toad for 395 XP
without a false watchdog withdrawal.
An Aruncus sweep starts in reset room 323, then immediately checks room 330 and
opens the west door into Hermit's Hut room 331 before traversing the outdoor
circuit. Live run 2037 proved that `where aruncus` can report the hut while an
outdoor-first search consumes the entire movement reserve. Sorbus is a
source-level-four non-aggressive bystander there and must not block the exact
Aruncus selector. Live run 2041 validated both door directions, a viable
room-318 fight, one bounded flee pursuit, a 541-XP kill, and safe healer
return. Live run 2044 validated the exact hut-present case: the route entered
room 331 immediately, accepted Sorbus as harmless, killed Aruncus for 538 XP,
and safely saved and quit in healer room 3054. Live run 2045 proved that
immediately repeating this single-reset hunt wastes 320 commands on an empty
circuit. After a successful kill, rotate to a current-reboot viable outside
area such as the Gnome treasurer before retrying Aruncus. At level 14, Kestrel has no
recurring thief attack because the trainer
caps Stealth Techniques at 56%, below backstab's 60% prerequisite; do not
misdiagnose normal-only combat as a runner fault until that cap clears.
On the Bardoosh circuit, treat the Miden'nir wyvern as an allowed non-attacking
bystander: source revision `d7cb330` defines it at level 8 without
`ACT_AGGRESSIVE`. It has `spec_poison`, so do not select it, but its presence
must not trigger a flee from a lone forced goblin or goblin lieutenant fight.
The Ambush route reaches the sentinel goblin archer in room 4515, then goes
`west` to Bardoosh's reset room 4514; do not infer this final step from the
duplicate mobile/room VNUM values or the rooms' shared display name.
When a source mobile has an explicit proper short name but a generic room line,
bind the TARGETMODE selector to the proper source identity. In particular,
`A goblin is here sleeping.` in room 4514 is Bardoosh, mobile 4515.
At level 13, Bardoosh is evidence-valid but inefficient until backstab becomes
trainable: live run 1902 gained 257 partial-combat XP, paid 132 XP to flee, and
completed no kill. Record runtime-capped no-kill segments as zero effective
policy XP and rotate back to Aruncus rather than forgetting or immediately
repeating the attempt.
Keep the level-14 Dwarven Kingdom worker route passive. Live run 2022 found
perfect-match workers, but run 2023 proved that the source-level-16 giant can
wander from an adjacent room and assist an apparently isolated fight. Worker
combat is retired; do not promote it without an adjacent-room threat gate and
new bounded evidence.
The level-14 Gnome treasury loop may traverse the crowded hobgoblin-soldier
approach but must not attack there. In room 1570, collect both source-keyed
`coins` piles, then attack at most one exact, isolated treasurer only after a
fresh viable `consider`. Scope pile values to the current reboot. Live run 2038
earned 282 XP without taking damage and returned safely after one kill.
At thief levels 14 and 15, the verified Mahn-Tor Rock Toad circuit checks rooms
2311, 2313, 2312, and 2319 independently. With a sanctuary potion, kill at most
one viable target. Without a potion, a second isolated target is allowed only
when the first kill leaves the existing continuation gates satisfied.
Each target keeps exact-selector, single-mobile, live `consider`, and +1
live-level gates. One purple potion protects only the first fight, so return
after that kill instead of entering another toad fight unprotected. The level-10
thief guildmaster caps second attack at 65% for Kestrel at level 14; persist the
live trainer-cap rejection until he levels. After a toad segment nets at most
250 XP and no sanctuary reserve remains, run the verified Moria large-hobgoblin
acquisition pass. Inspect only source reset room 4064, reached directly by
descending from no-mob room 4020. If the carrier has wandered, return and defer;
do not continue west into the aggressive maze circuit. Admit only a live
carrier above the prohibited diff <= -5 branch, stow its purple potion in the
worn pouch, and require the next toad combat to quaff it and confirm sanctuary
before ordinary damage. Never classify self-inflicted affect damage such as
`Your poisoned blood ... you` as a joining mobile attacker.
Live runs 2129 and 2130 killed Rock Toads with the Thalos long slim dagger in
69.9 and 73.8 seconds, finishing at 212/217 and 194/217 hit points; the
preceding three plain-dagger kills took 104.1, 92.1, and 90.0 seconds. Treat
those two upgraded samples as encouraging evidence rather than a stable speedup
claim.
Live run 2134 proved the campaign reset retry waits outside Moria and can
recover its source-room potion carrier after 60 seconds; the kill yielded 332
XP without damage. Live run 2135 then acquired Kestrel's second pink ice ring,
raising maximum hit points from 217 to 224, modified strength to 17, damroll
from 4 to 5, and carry capacity from 250 to 300. Live run 2137 repeated the
source-excluded `River bed` Kodiak result and returned safely instead of
pursuing into the poison branch.
Live runs 2153 and 2157 repeated that safe River-bed rejection. Run 2163
received only the ambiguous `Forest` locator label, spent about three minutes
searching every vetted room, and returned with zero XP. Retry this wandering
weapon carrier only after six productive field segments; maintenance and
zero-XP segments do not reduce the cooldown.
After a productive Rock Toad segment, rotate to a previously productive
Aruncus hunt or same-reboot viable Gnome treasurer before revisiting Mahn-Tor.
After the single-reset Aruncus hunt, rotate onward to the treasurer or Rock
Toads. Do not erase reboot-scoped evidence of productive Rock Toad kills only
because the latest Toad segment was empty; useful work outside Mahn-Tor gives
its resets time to repopulate. Live runs 2138 through 2140 exposed the waste
from immediately repeating
the cleared Toad circuit and then checking the recently cleared Moria carrier.
Apply the same rotation after a productive one-kill Toad policy whenever the
expanded circuit already has live evidence. A current level-and-reboot
below-band policy exclusion is terminal for selection, not merely advisory;
never return that policy until level or reboot changes. Runs 2146 through 2149
exposed both gaps: an unnecessary expanded Toad pass followed by two checks of
the same below-band Moria carrier.
At thief level 15, use the Olive Grove bandit leader after the level-10
guildmaster cap blocks further progression. The leader wanders among source
rooms 25202 through 25205, so the reset room alone is not presence evidence:
scan the connected rooms and stop when the live TARGETMODE line matches the
source mobile. After an accepted prerequisite gateway, refresh `practice` in
the same room before leaving so newly unlocked skills can be learned. Recall
from this distant trainer and recover at healer room 3054 instead of spending
the field movement reserve on the return walk. Live runs 2098 and 2099 unlocked
and practised backstab; run 2101 then opened a viable level-13 Rock Toad fight
with `backstab`, earned 473 XP, and returned safely. After an empty Aruncus
sweep, run 2104 selected this productive fallback, opened a level-14 Rock Toad
with the exact selector, earned 514 XP, and recovered fully in healer room
3054 before logout.
Sanctuary is opportunistic rather than a prerequisite for the four-room Rock
Toad circuit. Runs 2025, 2026, 2101, and 2104 returned safely
without it. Runs 2110, 2113, and 2114 then ended unprotected kills at 166/217,
206/217, and 150/217 hit points. With no sanctuary reserve, allow at most two
isolated targets while independently enforcing the 40.5% continuation and 27%
withdrawal gates. With a carried sanctuary potion, retain the one-kill cap so
one consumable never authorizes a second fight. If a circuit earns at most 250
XP without sanctuary, attempt one bounded Moria
supply pass; whether or not the wandering carrier is found, retry the circuit
next instead of letting consumable acquisition block productive XP. Run 2105
proved the absent-carrier return path from room 4064. Run 2106 then retained
65 partial XP against a level-15 Rock Toad and withdrew safely, exposing
repeatable damage rather than sanctuary as the immediate throughput blocker.
For thieves, learn a functional backstab opener, then take the shortest
source-backed recurring-damage path: raise thievery skills to 40% and practise
knife toss toward 45%. `do_knife_toss` is legal while fighting, waits eight
beats, deals level-scaled damage, can double on a face hit, and does not consume
an inventory knife. Issue `knife <exact-selector>` between automatic rounds;
continue the longer disarm and circle chains afterward.
Treat a live segment runtime limit as a soft return boundary, never permission
to close a socket during field combat. Request recall immediately, retry until
combat ends, recover at healer room 3054, and only then save, quit, and finish
the segment. Persist the boundary request and objective-kill evidence.
The Mirror Realm watchman route enters room 19005 after two north steps from
room 19003, opens the reset-closed north door, moves north three times to room
19008, then west into isolated watchtower room 19009. The gardener route
shares that `2n;open north;3n` prefix before turning east. Because the
watchman fastwalk already ends in room 19009, its field stop has no additional
`route_vnums`; never ask the room navigator to find an exit to its current room.
Distinct level-19 mobile 19010 resets alone in the eastern watchtower room
19010 with the same sentinel, stay-area, non-aggressive, and no-special
properties. After probing room 19009, return east to hub room 19008 and move
east into room 19010. Aggregate repeated canonical-target considerations with
logical OR so either independently fuzzed watchman can promote the bounded
one-kill hunt; do not let a later rejection erase an earlier viable result.
The source target parser canonicalizes `The watchman stands here, eyeing you
carefully.` as `watchman`; use that exact identity rather than the prototype
short description `a watchman`. Live run 2188 proved the complete probe and
received the `diff <= 5` consider branch with at least a 100-hit-point
disadvantage for room 19009. Do not attack that instance; probe room 19010
before rejecting the expanded policy for the current reboot. Live run 2200
proved the expanded route and both exact selectors; both watchmen returned the
same `Do you feel lucky, punk?` and `much healthier than you` rejection. The
run entered no combat, lost no HP or XP, and safely checkpointed at healer room
3054, so preserve the expanded policy's nonviable result for this reboot.
After a nonviable watchman result, probe the Crystalmir White Stag before
Shadow Keep. Source mobile 10012 is level 17 with 15-19 fuzz, evil, unarmed,
non-aggressive, stay-area, and has no special. Require flight for the long
approach. Reach reset room 10016 around the north shore without entering
aggressive Barracuda room 10005, then use the registered GMCP room circuit to
search all 34 low-risk rooms the Stag can occupy. Exclude Fewmaster Toede reset
room 10030 and guard-dog room 10039 as well as room 10005. The first pass is
consider-only; a viable current-reboot result may promote one exact-target
fight with 85% health and a maximum +1 live level offset. Unexpected aggression
from a wandering Fewmaster aborts to healer recovery.
Live run 2203 proved the complete route to room 10016 without combat or damage;
`where stag` confirmed the mobile absent from the current area, so the runner
skipped the long circuit and safely checkpointed at healer room 3054. Treat
this as temporary absence, but account for the route's cost: complete three
productive field segments outside Crystalmir before a bounded retry rather
than rejecting the policy for the whole reboot. Live run 2205 confirmed that
one productive Toad segment was too short a retry interval. Live run 2206
earned 440 XP from one isolated level-14 Toad, skipped a triple-Toad assist
crowd, and reduced the Stag cooldown from three to two without revisiting
Crystalmir. After three productive outside-area segments, live run 2211
performed the authorized retry; `where stag` still reported absence, so it
returned without combat and reset the cooldown to three.
The first level-16 fallback is the non-aggressive Shadow Keep Undead Soldier
in room 16615. Its source level is 15 with 13-17 fuzz and it wields a Rusty
Sword, so require a fresh exact-target `consider`, at least 85% health, a
maximum +1 live level offset, and one confirmed kill. A route abort before
`consider` is not target-viability evidence. Live run 2229 proved that an old
aborted-probe rejection no longer suppresses the policy, reached room 16615
safely, and again found the Soldier absent. Require three productive field
segments outside Shadow Keep before another absence retry. The same source
route passes non-aggressive, no-special Shadow Wraith resets in rooms 16603
and 16600. Live run 2237 proved those two rooms after finding room 16615
empty; all three resets were absent. The full exterior circuit also checks the
solitary Soldier resets in rooms 16607 and 16618. From room 16615, follow
west-north-north-west-up, down-east-south-west-west, east-east-east, then
east-south-east. At thief level 16 only a live-level-12 Wraith remains inside
the useful XP band. Promote at most one exact-target kill after a viable
result. On reboot `Sat Aug 1 03:23:54 2026`, run 2252 skipped a duplicate
Soldier pair and promoted the isolated drawbridge Soldier; run 2253 killed it
for 844 XP, recovered from two disarms, and returned safely at 145/233 HP. Run
2255 then traversed the full remaining circuit, skipped the duplicate pair,
and rotated away after finding no other target.
At level 17, after the watchman, White Stag, and Shadow Keep probes are
unavailable, probe Galaxy mobile 9306 in its isolated reset room. Reach stable
Shadow Grove room 1300 by fixed route, then follow live GMCP destination VNUMs
through randomized rooms 1308, 1305, and 1306 and the fixed 9301-9306 chain.
Live run 2291 proved that route without combat or damage but found the reset
absent. A `where white` result in room 9345 is unsafe for this band because that
source room also resets level-31 Cancer; never pursue the white dwarf there.
After an unavailable Galaxy probe, level-17 and level-18 thieves may re-probe
the isolated Dwarven Homestead nobleman under a new band-specific evidence ID.
Source mobile 20504 is level 13 with normal fuzz, non-aggressive, sentinel,
stay-area, unarmed, and has no special. Live runs 1926 and 1931 found a
level-15 instance that was unsafe for level-13 Kestrel but is useful-band for
level 17. Require exact `consider`, at least 90% health, no unsafe bystander,
and a maximum +1 live-level offset. The source-known non-aggressive maid in the
endpoint room is an allowed bystander; a wandering house guest is not. Recall
immediately after a failed consider and
promote at most one kill from the single reset before rotating onward. Live run
2292 got `looks like an easy kill` with only a slight HP disadvantage, but a
level-20 house guest shared room 20506. The no-combat result remains valid;
the hunt must reconsider and enforce its one-mobile ceiling. Do not allow the
guest as a bystander: `fight.c` can make a different-prototype mobile assist
probabilistically even when it is not aggressive.
If a research route reaches its verified destination and the reset target is
absent, do not treat it as a reboot-long viability rejection. Leave the area
and select another executable policy; clear the temporary absence after
productive work elsewhere, using a policy-specific cooldown when the route is
expensive or the mobile wanders widely. Wait outside through the bounded reset
controller only when no alternate policy is available.
For thieves at levels 16-18, fall back to the proven Mahn-Tor Rock Toad
two-kill circuit after both level-16 probes reject. Its source range is 12-16;
retain exact live `consider` at each stop, require the 40.5% continuation floor
for the second target, reject every `diff <= -5` result, and never generalize
the thief combat evidence to another class. Live runs 2257 and 2259 each
completed two isolated kills, earning 1,286 and 877 XP respectively while
returning safely; intervening run 2258 rejected a below-band Bardoosh and
rotated directly back to this productive circuit. Run 2261 exposed an
aura-prefixed TARGETMODE line falling back to a generic keyword; normalize
leading status labels after ANSI removal. Run 2263 then proved exact selectors
for both targets and every knife command. Run 2272 caught the reset after two
empty bounded passes and raised Kestrel to level 17 with two exact-target kills
before returning safely.
At thief levels 17-18, rotate every completed Rock Toad pass through the
verified Aruncus hunt before returning to Mahn-Tor. His source-backed 11-15
live range must still pass exact `consider`; leave weaker `diff <= -5` fuzzed
instances alone. Disable autoloot and manually collect only staff, scroll, and
ivy so object 307, the no-drop strange amulet, remains in the corpse. Live run
2281 killed a viable Aruncus for 612 XP without player damage, restored
autoloot, and saved and quit in healer room 3054.
At critical field-departure encumbrance, sacrifice only registered expendable
loot such as spent Circus keys; preserve food, water, potions, containers,
weapons, and gear unless a separate source-backed replacement policy applies.
When protected spare stat gear prevents an essential food or weapon purchase,
store it in the Midgaard vault before restocking; do not sell it merely to
free capacity. Re-equip the best legal copy from carried gear afterward.
Treat the first vault weight or item-count rejection as terminal for that
storage pass; never remove another item after it. Prefer selling expendable
loot at a compatible shop, then donate or sacrifice registered expendable
objects when they cannot be carried, sold, or lodged. Preserve food, water,
potions, containers, weapons, and best-in-slot gear.
When fewer than ten carry-weight units remain and at least ten individual coins
are carried, bank the coins before considering vault relief. DD4 charges one
weight unit per ten coins, so this may free the required capacity without
lodging protected equipment. Live run 2053 exposed the ordering defect by
lodging a silver circlet at 161/170 weight while carrying 240 coins.
Treat `You can't let go of it.` during sale, donation, or removal as cursed-item
evidence. Prefer a known and usable `remove curse` spell or an identified
remove-curse wand/stave; otherwise return to healer room 3054 and buy
`heal curse`. The spell may toss `NOREMOVE` or `NODROP` objects into the room.
Destroy expendable tossed objects after source or identify evidence confirms
they are not useful; never loop the rejected command. If the healer fee is
unaffordable, take one bounded 500-copper Dragonhoard Bank loan, return to the
healer, and retry once. Live run 2018 verified this flow against Aruncus's
no-drop strange amulet. A room mobile may pick up the tossed item before the
destroy command, so confirm it has left inventory instead of looping.
When source evidence identifies a cursed or no-drop object on a known target,
disable autoloot before combat and collect only approved corpse drops by exact
source keyword. Restore normal autoloot at healer room 3054 after leaving the
cursed object in the corpse. For Aruncus, leave object 307, the strange amulet;
manually collect `staff`, `scroll`, and `ivy`. Live run 2150 proved this exact
flow against live-level-14 Aruncus: the kill awarded 568 XP, only the three
approved drops entered inventory, 15 gold remained unchanged, normal autoloot
was restored at the healer, and the character saved and quit safely. Live run
2154 repeated the behavior against a wandering Aruncus in source room 318,
earned 325 XP, and safely checkpointed without the amulet.
Liquidate the approved Aruncus drops before they create item-count pressure.
Current `midgaard.are` shop data makes the Wizard in safe room 3033 a buyer
for item-type-two scrolls and the grocer in safe room 3010 a buyer for
item-type-19 food. Sell the scroll and poison ivy through those source-backed
buyers; object 308 is item-type-12 furniture despite its `staff` name, so
donate it when no compatible safe buyer exists. Live run 2159 sold three of
each sellable drop, donated three staffs, reduced inventory from 37 to 28
items and 153 to 138 weight, then saved and quit safely at the healer.
DD4's `fwrite_obj` omits `ITEM_KEY` objects from both character and vault save
files, so lodging a key preserves it only until the next save/logout. When a
key is costly or difficult to replace, cache it loose in a source-vetted
`ROOM_NO_MOB` room whose reset residents are neither scavengers nor
`spec_janitor`, and scope that cache to the current reboot identity. Midgaard
bank room 3007 is the registered Circus-ticket cache; try to retrieve the
ticket there before buying and drop it there before logout. A missing cache
must fall back to reacquisition because another player or a reboot may remove
it.
At level 10, stop using the Mud School Loremaster and route each base class to
its source-backed Midgaard trainer, as directed by `HELP TEACHER CLUE`. The
registered trainer rooms are mage 3019, cleric 3002, thief 3029, warrior 3023,
psionic 3150, brawler 3218, shifter 3221, ranger 3048, and smithy 3050. Their
source-defined teacher bases reject lower-level characters. For field-caster
mages, once the shared level-10/11 Fleshmonger guard probe is recorded, use the
protected Moria level-11 hunt as the next progression policy; a zero-XP result
is terminal for that level/reboot until the live evidence is reviewed. At level
10, a zero-XP Moria acquisition rotates once to the mage-specific Fleshmonger
guard-hunt research policy; do not repeat either route without fresh evidence.
If that guard result is nonviable, use the two-stop Moria large-orc research
policy; promote it only after a positive live mage kill, and keep the poison
snake and deeper Moria circuit out of this fallback.
When that research target is absent, persist the reboot-scoped absence and let
the campaign's bounded outside-area reset controller sleep and retry; a new
process invocation must resume that controller rather than launch immediately.
When the bounded wait expires, reopen that current research policy before
selecting any reboot-scoped below-band exclusion; an expired absence must never
turn into a hard campaign block or an unrelated target selection.
For thieves, raise Stealth Techniques to its 60% prerequisite, then prioritize
backstab while a piercing weapon is equipped.
At level 15, route thieves to the stronger bandit leader in Argentium Olive
Grove. His source reset is room 25205, but he can wander across rooms 25202
through 25205. Match his source-backed live room line and practise wherever he
is found; if `look leader` fails, defer training without issuing a blind
practice command. His teacher base is 15 and his Thievery, Armed Combat, and
Stealth group caps are 75%, allowing progression beyond the Midgaard
guildmaster's effective cap.
Persist trainer-cap and trainer-level practice rejections for the current
character level so later segments choose another eligible priority. Clear that
exclusion after levelling; do not persist prerequisite rejections because
another skill learned at the same level may unlock them.
Treat an `eq all` line containing `[weapon] -` as an empty slot, never as proof
of a wielded weapon. A dedicated rearm run must buy, wield, and verify an
occupied weapon line before succeeding. If the source-backed dagger is
unaffordable, use the existing Dragonhoard Bank credit route, then retry and
return to healer room 3054.

## Development Commands

Use Python 3.12 in the local virtual environment:

```powershell
python -m pip install -e .[dev]
python -m pytest
python -m compileall -q dd4tester tests
python -m dd4tester run scenarios/login.yaml
```

The first command installs the package and test tools. Run the full pytest and
compile checks before publishing a significant change.

## Style And Naming

Use four-space indentation, type hints, dataclasses for explicit data models,
and `snake_case` for modules, functions, variables, and event names. Use
`PascalCase` for classes. Keep protocol parsing, state reduction, storage, and
decision logic in independently testable modules. Prefer deterministic parsing
and structured JSON data over ad hoc text manipulation.

## Testing

Use pytest. Name files `test_<module>.py` and tests `test_<behavior>`. Add
sanitized fixtures for real DD4 output and never include account credentials.
Every bug fix should have a focused regression test. Network access must not be
required by the normal test suite.

## Data And Security

Record commands, responses, GMCP, derived events, state changes, and timestamps.
Use `configure-login` and `configure-character-password` for local credentials;
they use Windows Credential Manager through `keyring`. `DD4_USERNAME`,
`DD4_PASSWORD`, and a profile's password environment variable remain supported
overrides. Transcript and database records must redact credentials. Use direct
Telnet/GMCP for primary testing and reserve Mudlet-in-VM automation for
client-specific validation.
For live progression, prefer one bounded multi-segment campaign process over
repeated one-shot connections. Before launching, verify no tester process is
already active. Omitted campaign `--reset-retries` now uses the `--segments`
budget so dynamic area depletion waits outside the area and retries instead of
silently converting an autonomous run into a blocked campaign; pass
`--reset-retries 0` only when an operator explicitly wants no reset wait.

## Operational Fail-Fast Policy

Never wait, poll, or suspend useful work for an invisible permission review.
If an external action reports an approval timeout, retry that exact action once
immediately. If the retry also times out or fails, abandon the action for the
current pass, report it briefly, and continue with the best local or offline
work available. Retry the deferred action only after completing another useful
work unit or when the user explicitly requests it. Do not repeatedly poll for
approval, leave a required shell call hanging, or describe the task as blocked
while local implementation, testing, evidence analysis, or documentation can
still progress. A failed push or live connection must never prevent local
commits and verification.
Judge a live tester process by fresh SQLite events via `show-transcript` plus
its process state, never by the JSONL file's observed size alone. A temporarily
stale or zero-length file is not sufficient evidence of a stalled connection.
When launching a bounded foreground segment, give the outer command timeout
more time than the segment's own runtime cap so the runner can recall, save,
and quit cleanly.

For levels 71-75, the registered source-backed fallback is the Pirates Seas
Rastafarians probe/hunt. Source revision `bf745c3` identifies mobile 17099 in
room 17141 at source level 70, with no aggressive, sentinel, stay-area, or
special flag. Use `where rastafarians`, search only the registered reset room,
and require a fresh live `consider`: level difference determines XP-band
eligibility; HP wording remains a separate combat-risk signal.
For level 76, use the Ghost Town crypt thing probe/hunt; for levels 77-80,
use the Ghost Town retriever probe/hunt. Source revision `1b759f5` identifies
mobiles 8809 and 8829 as sentinel, stay-area, non-aggressive, and special-free
resets in rooms 8850 and 8843. Keep their closed-door routes and the adjacent
water-weird hazard behind the normal abort gates, and promote combat only
after a fresh exact `consider` proves the live level difference useful.

## Local Commit And Commentary Policy

Keep all changes local. Do not push, open pull requests, merge remote branches,
or otherwise publish to GitHub; the user handles remote publishing manually.
Attempt at most one local commit in each 24-hour period, scheduled for 9:00 PM
Pacific/Auckland time. Set a 60-second command timeout for that commit. If it
fails or times out, do not retry for 24 hours. Prefix every progress update to
the user with the current Pacific/Auckland local time so stalled work is
visible.
Beginning 2026-07-26, append every user steering message and every Codex
commentary or final response verbatim to `DEVELOPMENT_CONVERSATION.txt` in the
repository root. Stamp every entry using exactly
`[YYYY-MM-DD h:mm:ss AM/PM NZST] USER`,
`[YYYY-MM-DD h:mm:ss AM/PM NZST] CODEX COMMENTARY`, or
`[YYYY-MM-DD h:mm:ss AM/PM NZST] CODEX FINAL`. Do not substitute a speaker-first
header, UTC offset, ISO timestamp, or other format.
The `AM` or `PM` token is literal uppercase. In PowerShell, generate it with
`$stamp = (Get-Date -Format 'yyyy-MM-dd h:mm:ss tt').ToUpperInvariant()`;
do not use the locale's lowercase `am` or `pm` output. The Discord streamer
parses these append-only headers, so timestamp casing is a delivery contract.
Treat the file as append-only development history; do not rewrite or remove
earlier entries. Write an entry before or as the corresponding response is
sent so a stalled task cannot leave the visible discussion unrecorded.
Use `python tools/conversation_log.py append --speaker "CODEX COMMENTARY"
--body "..."` or `--body-file <UTF-8 text file>` for new entries whenever possible;
the helper emits the exact header and appends UTF-8 bytes without rewriting
legacy mixed-encoding history. Before restarting or diagnosing the Discord+streamer, run `python tools/conversation_log.py validate`. A malformed
headerish line is a format failure to investigate, not a reason to change the
required header contract. Before every visible progress update, perform this
checklist: create the timestamped header, append the matching log entry, then
send the same header and commentary to the user.

## Commits And Pull Requests

Use concise imperative commit subjects, for example `Persist character state
snapshots`. Include verification details and behavioral impact in pull
requests. Follow the local commit schedule above and leave remote publishing to
the user. Never stage generated run data, transcripts, secrets, or unrelated
user changes.
