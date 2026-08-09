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
Scope reboot-local source hunt kill caps by mobile prototype VNUM, not by the
mobile's display name: distinct mobile VNUMs can share a short description
(for example, two different `Secretary` prototypes). Derive source-ranked kill
counts from the selected candidate recorded in campaign segments; retain the
name-based counter only for legacy generic policies.
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
Before selecting a source-ranked target whose route crosses a randomized room
set, preflight source-graph reachability after excluding source-proven
aggressive or special-procedure hazard rooms. Skip a candidate whose only
source-connected path is blocked; do not spend a live connection discovering
that the maze cannot reach its target.
The Shadow Grove (rooms 1300-1309) is a randomized `no_recall` maze. For
return-home and fastwalk recovery, navigate by live GMCP exits to room 1300,
then follow the source-backed reverse route through Haon Dor rooms 6137,
6136, 6135, 6129, 6128, 6126, 6127, 6112, 6111, 6110, 6109, 6108, 6103,
6102, 6101, 6100, 6004, 6003, 6002, 6001, 6000, and Midgaard 3052, 3040,
3012, 3013, 3014, 3005, 3001, 3054. Never rely on `recall` from a Shadow
Grove room. Live run 2623 reached and exited the grove's Galaxy approach
without invalid movement; direct recovery run 2620 also returned Kestrel to
healer room 3054.
Every Abyss room 7500-7559 is an air sector. Source rooms 7505, 7536-7539,
7548, 7551-7552, 7554-7555, and 7557-7558 are no-mob rooms that permit recall;
many surrounding rooms are `no_recall`. Use the source distance-to-recall map
and live GMCP destination VNUMs to move toward the nearest one, then recall.
Enter an Abyss route only with full movement and at least 16 visible flight
ticks, and withdraw at the 36-movement reserve. Never sleep in the Abyss:
recover the six points needed for the next flying step while standing. If
flight is already gone, do not issue impossible air movement; observe forced
falls and recall immediately upon reaching any legal room. Live run 4338
stopped Kestrel at 5 movement in room 7531, one live west step from recallable
7536. Recovery run 4339 let flight expire while sleeping, encountered mobile
7504, died after combat-locked navigation and recall retries, then traversed
Purgatory, looted the corpse in room 427, entered the portal, and reached
healer room 3054. Verification run 4340 restored and audited the equipment,
saved, and quit at full health. Live run 4352 then proved the repaired field
gate: the randomized search reached 35 movement, followed one live-GMCP step
to a source-confirmed recall room, recalled, and recovered at healer room 3054
without sleeping or fighting in the Abyss. Never let generic recall or gear handling
override active combat, Purgatory recovery, or an Abyss no-recall return.
The Purgatory portal emits the Midgaard text room and prompt before the complete
GMCP room update. Clear persisted death state when that prompt first changes the
area from Purgatory to Midgaard; otherwise a fully recovered character remains
falsely dead and the campaign fails after safe healer cleanup. Run 4564 exposed
this ordering after Kestrel looted the corpse, entered the portal, restored gear,
and recovered fully in room 3054.
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
only after live state confirms the character has subclassed. At exactly level
30, use the source short `who_name` keyword with `change` at the Kerofk class
teacher, then wait for live `Char.Base` subclass state before checkpointing or
activating subclass policies; never treat success text alone as confirmation.
Practice order
must account for prerequisite
gateways, current trainer listings and caps, separate physical/intellectual
budgets, direct damage, mitigation, sustain, mobility, and whether the combat
runner can actually use the result. Mark unsupported rotations analysis-only
rather than spending practices on unusable skills.
Persist a trainer's `no immediately useful listed skill` result by practice
type for the current character level so later field segments do not repeat the
same long trainer journey. Re-evaluate both practice types after a level gain.
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
Parse `#OBJECT_SETS` from the area files and score a complete equipment
loadout, not each slot in isolation. Mirror `handler.c`: set progress counts
distinct equipped object prototype VNUMs, duplicate copies count once, and
effects are paired with cumulative bonus thresholds in reverse area-file `A`
order. Include strength-derived hitroll and damroll changes from `str_app` when
choosing combat gear so a nominal hitroll upgrade cannot break a stronger set
bonus.
Live run 4477 validated this with Kestrel: the planner retained object 108 and
both object-6601 rings, replaced only the recovery boots with object 28372, and
finished at 5 damroll and 10 hitroll instead of the old set-breaking 3 damroll
and 11 hitroll field stance.
Treat DD4 `Char.Worn` as the authoritative worn-equipment snapshot. Resolve a
structured object VNUM before matching display text because distinct
prototypes can share a short description (for example, purchased dagger 3020
and unrelated dagger 31015). A textual `eq all` confirmation may establish
profession-visible slots, but it must not overwrite a current structured paper
doll. Mark structured identity stale when issuing a wear, remove, wield, or
hold command and restore it only from the next complete `Char.Worn` snapshot;
fall back to text only when that structured acknowledgement is absent. If a
complete snapshot loses the wield slot
during combat, recover the previously audited source keyword from the room and
re-wield it before recurring attacks resume. Treat `You must wield a weapon to
disarm.` as secondary evidence of the same loss. Equipment stance application
must converge; stop and re-audit exact worn VNUMs instead of repeating opposing
swap signatures.
Live run 4499 exposed the missing weapon recovery after a rolling-rock disarm.
Runs 4501-4502 then showed that display-only confirmation could mistake dagger
3020 for dagger 31015 and alternate forever between the object set and bead
necklaces. The structured worn snapshot and exact-VNUM policy close both
failure modes.
Live run 4505 then proved that below-band transit-attacker branches could
bypass the generic recovery block: a rolling rock removed dagger 3020 and the
runner issued recurring knife attacks before rearming. Route every decision to
continue combat through the shared disarm-recovery state machine, including
consider-only, trivial-attacker, utility, and runtime-boundary paths. Complete
the bounded get and wield sequence before another recurring action. The same
run acquired and equipped long slim dagger 5252, reached 5 damroll and 10
hitroll, and returned safely to healer room 3054.
Spellcasting combat plans must combine source-verified damage spells with
available damage-reduction spells rather than spending all mana on damage.
Apply character titles and descriptions only during initial identity setup;
use persisted command evidence to avoid recreating them on later logins. Store
new command evidence in the compact per-character command ledger at event-write
time; never scan and decode the global event history during live startup. A
persisted level above one is sufficient legacy evidence that creation-only
identity setup must not be replayed.
Live startup must not repeatedly scan full campaign histories or decode large
global event streams. Use bounded runtime tails of at most 1,024 segments and
256 checkpoints or event-bearing segments, cache those reads with write-time
invalidation, and maintain exact campaign totals plus historical command and
item evidence in compact write-time ledgers. A legacy ledger may be backfilled
once and marked complete; never repeat that backfill during later segments.
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
Persist each observed reboot-specific shop price; once the current price is
known, do not treat a generic cash threshold as sufficient. Re-enter the
source-backed money loop until the character can afford that price and its
required travel and food reserve.
Parse `ITEM_MONEY` values as copper, silver, gold, and platinum and convert
them at 1, 10, 100, and 1,000 copper respectively. Include direct `O`/`I`
room coin resets as non-combat funding candidates when their source route has
no useful-band aggressive hazard; collect them by source keyword and verify
the currency delta before clearing the funding requirement. Treat nested
containers and unverified hoards as research-only until their extraction and
lock/key requirements are source-backed.
Include money objects loaded onto mobiles through `G`/`E` resets, including
money nested in source-linked containers, in the ordinary loot-value ranking.
These are combat funding opportunities, not permission to attack: retain the
mobile's level-band, special, crowd, route, and live `consider` gates, and use
the total copper-equivalent value when comparing a carrier with other targets.
Before a live area launch, parse each registered mobile's exact area-file room
description through the target recognizer; use live output to confirm presence
and dynamic reset state, not to discover static mobile display lines.
During outbound official fastwalk travel, inspect each fresh room response for
source-catalogued ground items required by the active hunt. Collect a matching
item before advancing the route index, then resume the same route step; never
use an unverified display noun or pick up a required item while in combat.
If a current-band source candidate is rejected only because one reset permits
two matching mobiles, it may enter research rotation: live TARGETMODE output
must prove exactly one source-matched target before consider or combat. Never
relax this exception for special procedures, aggression, companions, route
hazards, or larger reset capacities.
When a current-reboot hunt withdraws with negative XP before a kill, persist
that policy as protection-recovery evidence and do not immediately reselect the
same source route. Recover or acquire the required protection first, or choose
another current-band route; a later retry is allowed only after the recovery
gate clears.
Treat an explicit hard-health-floor withdrawal as stronger policy-specific
protection evidence even when partial combat produced a net XP gain. Sanctuary
may temporarily satisfy the gate, but retain it until that exact policy records
an objective kill; an unrelated easier kill must not clear it. Live runs 4387
and 4397 reached 19/305 and 26/320 HP against High Tower mobile 1303 while
gaining partial XP, proving that net XP alone does not make the retry safe.
An absent or cooldown-protected Moria carrier must not suppress generic
source ranking. Continue with a different current-band candidate while the
exact XP-losing route remains blocked by its protection marker.
For the Moria sanctuary required-loot hunt, a carrier located by `where` but
outside its source reset room is not an authorization to pursue. Record the
bounded attempt as a retryable failure with the normal three-segment cooldown,
then use the registered Argent, Shire, or deep-Moria alternate frontier before
reopening the carrier route.
Read `special.c` together with `db.c::load_specials` before classifying a
special mobile. DD4 adds +0, +5, +10, +15, or +20 to a mobile's XP modifier;
use that tier as a danger signal, not as permission by itself. The source
implementation makes `spec_fido`, `spec_janitor`, `spec_repairman`,
`spec_cast_adept`, `spec_cast_hooker`, and `spec_cast_orb` non-attacking for a
normal player, so a sole-special candidate may be audited under the ordinary
exact-target, isolated-room, live-`consider`, elevated-health, one-kill, and
healer-return gates. Do not blanket-reject every special, but keep
`spec_celestial_repairman` and crime-conditional `spec_bounty`,
`spec_clan_guard`, and `spec_executioner` research-gated until their movement
or player-status preconditions are proven.
Source `spec_thief` returns before its theft branch while fighting and can take
at most 20% of carried coins while standing. Bound the possible loss to 250
copper-equivalent (so carried currency may be as high as 1,250 copper), with
the normal source level, route, crowd, live `consider`, and HP gates still
enforced. A `spec_thief`-only source-ranked probe may retain the ordinary +1
live-level fuzz allowance because the special does not add combat damage;
keep the separate coin-loss bound and do not extend this allowance to other
special procedures. The weak `spec_poison` and `spec_kungfu_poison` paths may
be audited as debuff-only targets only when the runner recalls and waits for
the healer while poison remains active. Bound weak `spec_guard`,
`spec_sahuagin_guard`, and `spec_bloodsucker` as one additional ordinary hit,
and `spec_cast_judge` as its source `6 * level` high-explosive ceiling. Keep
all other weak, moderate, strong, boss, breath, and caster specials blocked
unless a matching source damage/effect policy and live evidence are added.
Never select a mobile carrying `ACT_LOSE_FAME` for XP or funding. Live run 4564
proved that killing Solace mobile 10255 (Alex) cost 12 fame; DD4 then blocks
both shop service and leveling while fame is negative. Treat a reputation shop
refusal as a bounded, nonfatal return to the healer. When fame is negative,
restore a legal field weapon first, acquire a purple sanctuary reserve, then use
the level-24-26 Mirror Realm buck or moose recovery circuit. Attack exactly one
isolated target only when live `consider` returns the `laughs at you
mercilessly` branch, confirming the six-to-nine-level fame-award band; return
to the healer after each kill and repeat until live fame is nonnegative. A live
nonnegative fame value clears the sticky shop-refusal marker.
Any explicitly audited `spec_cast_mage` hunt must mark sanctuary as required,
quaff its carried purple potion before the opener, and confirm the sanctuary
affect before attacking. Live run 4217 exposed the unsafe gap between merely
carrying a reserve and consuming it: unprotected fireball and colour spray
forced a withdrawal from the Shire dwarven prince.
If a source peak-damage rejection is caused only by the maximum fuzzy mobile
level, allow it only as an explicit reset-retry probe when the minimum source
peak is below current max HP. Require exact live `consider` level (no positive
level offset), at least 95% health, and no other source rejection; record the
probe separately and never treat its conservative maximum as ordinary combat
permission.
When the ordinary current-band frontier is exhausted, a source mobile exactly
one base level above the character may enter a separate ceiling-probe pool only
when its full fuzzy peak-round bound is strictly below current max HP, it has
no source rejection or coin-stash role, and its lower fuzzy range remains
useful. Require live `consider` to return the perfect-match branch, retain the
normal +1 live-level stop ceiling, and never generalize this exception to
special, aggressive, crowded, or route-hazard targets.
Also permit a source mobile whose nominal base level equals the character's
current level when only one additional fuzzy level exceeds the ordinary upper
band, provided it is autonomous-safe, special-free, rejection-free, single-
spawn, and its estimated peak round damage is strictly below max HP. Treat it
as the same bounded live-consider probe; do not relax the +1 live-level combat
ceiling or the normal route and crowd gates.
Live run 3613 validated this gate against the Old Treant in Mahn-Tor: Kestrel
earned 1,644 XP and returned to healer room 3054 at 236/283 HP. Live run 3618
then validated the independent Solace secretary reset for 1,198 XP without
player damage. Preserve both as reusable level-20 source-ranked evidence.
When comparing an exact registered target with a parsed live identity, strip
only leading grammatical articles (`a`, `an`, `the`) on both sides; preserve
the remaining source identity and selector distinctions.
For source-backed discovery, treat fixed `ACT_SENTINEL` mobiles and
`ACT_DIE_IF_MASTER_GONE` mobiles as reset-room-only. For ordinary mobiles,
search every bounded source-reachable room from every reset, blocking
`EX_CLOSED`, `ROOM_NO_MOB`, and stay-area boundaries. An open exit is
mobile-reachable even if its lock flag remains set. `AFF_CONFUSION` is a
separate source movement path that overrides sentinel, stay-area, and no-mob
restrictions, so search its full bounded open-exit graph. If `where` confirms a
target but its room label is unmapped, retain that positive evidence and run
the full bounded source search instead of abandoning the target.
`where` may list several same-named mobiles from unrelated areas; retain every
matching row, prefer source-vetted safe locations, and never let the first row
hide a later mapped location. Treat an excluded location as fatal only when no
safe source-vetted match remains.
Normalize flattened GMCP room descriptions with the same sentence boundaries
used by live room output before applying crowd gates; furniture or other static
room prose must not become a phantom mobile. Ignore companions only when their
source identity is explicitly trivial for the current character level.
Keep source-ranked evidence keyed by area, mobile VNUM, reset-room VNUM, and
character level. Do not let a crowd or absence result from one reset room
suppress an independent reset room for the same mobile; only a legacy,
explicitly multi-room policy may aggregate those locations.
The requested mobile's own reset rooms are valid endpoints even when that
mobile is aggressive; block other aggressive reset rooms as route hazards and
let the live crowd/isolation gate decide. A visible room target or positive
`where` row remains presence evidence even when `consider` rejects it as
below-band or too dangerous; never serialize that case as target absence.
Never attack for XP when `consider` returns a `do_consider` result from the
`diff <= -5` or `diff <= -10` branches; those targets are too low to be useful.
When the best fresh source prototype has less than a 50% chance for its normal
level fuzz to land inside the useful consider band, prefer a same-reboot route
whose latest recorded kill still earned meaningful XP, even after its third
kill. High-confidence fresh targets retain priority, and a repeat stops being
eligible when its latest reward falls below the meaningful-XP threshold.
Bound that discovery preference with durable throughput evidence: after two
consecutive same-level, same-reboot source-ranked segments earn zero XP, choose
a proven meaningful repeat even when the next fresh candidate has at least 50%
useful fuzz odds. Derive the streak from campaign segment history, ignore city
maintenance between hunts, and reset it on XP gain, level change, or reboot.
Runs 4537-4541 produced five consecutive zero-XP probes after run 4535 earned
1,044 XP, proving that unbounded fresh discovery can displace progression.
Use the source level-difference branch as the level-band decision: the separate
hitpoint comparison text is descriptive combat-risk context, not a substitute
for level difference and not an automatic rejection of an otherwise viable
level-band target.
For source-ranked hunts, persist a negative live `consider` separately from a
failed combat attempt; a short retry cooldown must not reopen a target already
reported as materially stronger than the character.
Live runs 4299 and 4325 exposed this exact failure for Hightower mobile 1303:
productive work expired its generic retry marker and reopened the same diamond
golem at level 22 in the same reboot. Preserve `consider_viable: false` as
terminal for that policy and discard its short retry cooldown instead.
Persist that below-band result against the selected policy for the current
character level and reboot. Do not revisit the same surviving mobile until the
level or reboot identity changes.
Every shared probe-to-hunt promotion and fallback must enforce both the
policy's minimum and maximum character level. Live run 4223 proved that an
expired level-18 Rock Toad policy is below-band and wasteful at level 22; a
cooldown or protection-recovery path must not revive it outside its band. Live
run 4408 caught the Moria-absence alternate helper reviving the same fallback
at level 23, so enforce the bounds inside helper-level fallback branches too.
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
Before a Magic Shop trip, use known invisibility when available. Otherwise
issue `where drunk` from healer room 3054 and defer the trip when mobile 3064
is in a source-route room. Its `greet_prog` calls `mpkill`, while
`mprog_greet_trigger` requires the mobile to see the entering player. Treat a
blocked route as a bounded retry after productive work, not as an
unaffordable-purchase result.
For verified hunts, continue until a meaningful discomfort threshold: low
health without vetted local recovery, an uncured disabling affect, unusable
food or water when needed, insufficient movement, encumbrance, or exhausted
local targets. Prefer source-vetted local sleep and multi-target circuits over
recalling after one safe kill. Before an imminent level, issue `train` for the
class profile's current primary stat and wear all legal stat-improving gear.
For generated source-ranked hunts, chain up to three fixed, single-reset,
ordinary targets in one same-area circuit only when every target passes the
normal source and live gates and each short inter-target path excludes
useful-band aggressive or combat-capable special-procedure reachability.
Allow up to 20 source-safe same-area steps between fixed circuit targets; live
level-24 frontier analysis showed that the former 12-step cap rejected an
18-step Solace lieutenant-to-Alex pair and chose an 81-step singleton trip
instead. The larger bound does not relax route hazards, target isolation,
`consider`, health, or exact-selector gates.
Source-proven nonattacking specials may be transit-only hazards; economic
specials additionally require the existing bounded carried-coin exposure, and
the live crowd gate still applies in every target room. Tag every kill with its
source mobile VNUM and generated policy ID. Recovery need, not the first kill,
normally ends a productive circuit. If only one in-band target can be
killed before health, mana, or movement forces recovery while another vetted
target remains, persist that as combat-readiness evidence and audit equipment,
trained damage or mitigation capabilities, and the active rotation. While that
same-level marker remains active, exclude the exact exhausting source policy,
force one fresh class-trainer audit even when the ordinary per-level audit was
already recorded, and prefer the largest viable lower-peak-damage source
circuit before raw XP score. Record the completed training and gear audits on
the marker, but clear it only after at least two objective kills or a level
gain; an audit by itself is not proof that throughput improved.
A failed live `consider` at one generated circuit stop must preserve that
policy-specific evidence and advance to later independently tagged stops. Recall
only when no vetted stop remains or the stop explicitly requires abort after
rejection.
Before any hunt fastwalk from recall, refill the carried water skin in room
3005, drink there, and return north; never rely on a stale in-memory thirst
flag for a long route.
Before any source-ranked, funding, or coin-stash fastwalk departs from healer
room 3054, sleep until its movement threshold is ready; apply this even when
the route has no combat hunt stops.
Deferred funding routes must honor that initial healer movement gate before
starting class-trainer travel; the funding policy may defer normal resupply,
but it must not bypass the first safe recovery checkpoint.
Any live checkpoint outside Midgaard must select `return-home` before restock,
liquidation, banking, training, or other city maintenance, even when current
HP and movement are otherwise sufficient. Exclude death handling and the
explicit Mud School accessory rooms from this location gate. Live run 4238
showed why: restock correctly refused to invent a Midgaard shop route from
Solace room 10295, but return-home needed to own that transition first.
When a bounded segment reaches its runtime limit, force the existing healer
save-and-quit path to become command-ready even if the latest server prompt
has not yet been observed; cleanup must not expire while a character is
sleeping safely at room 3054.
Tune autonomous field play 50% more aggressively than the original baseline:
tolerate recoverable damage, use 360-second bounded fights, continue circuits
at 22.5% health with 7.5% mana and 5% movement, leave the healer at 37.5%
health and 15% mana, ordinarily withdraw at 15% health, and finish a
lower-level half-dead opponent down to 10%. Retain a 67.5% departure floor
for high-risk and aggressive targets. Keep death traps, unknown high-level
enemies, unsafe crowds, disabling affects, and unsupplied hunger or thirst as
hard withdrawal boundaries.
Do not let the generic non-fastwalk 25% emergency-resupply floor override a
field fight's 15% withdrawal or 10% finisher threshold.
For a return-home checkpoint at the healer, use the same 90% movement floor
both when deciding to sleep and when deciding to wake. A lower generic wake
floor creates a no-progress sleep/stand command loop.
For bounded live HERO invocations that can enter progression combat, set
`--max-segment-runtime` to at least 420 seconds so the 360-second combat bound
still has travel and healer-cleanup time. Live run 4211 proved that 240 seconds
can preempt a healthy near-finished fight and force an unnecessary XP-losing
recall.
Do not count source-proven or live-level-confirmed below-band mobiles as an
unsafe crowd. They must not block selection of a useful-band target or trigger
a flee while a planned useful-band fight is still unfinished. Never select them
deliberately for XP, but finish unavoidable trivial combat so it cannot stall the
productive hunt. Once the bounded objective kill budget is complete, this
exception ends: flee immediately from any unplanned attacker, including a
below-band one, because there is no remaining objective worth the exposure.
Live run 4564 killed both Solace circuit targets for 2,923 XP, then stayed against
mobile 10215 because its live level was only 13. Its `spec_guard` headbutt and
kick bursts killed Kestrel and turned the segment into a net XP loss; an early
post-objective flee is now mandatory.
For source-ranked room isolation, include a trivial same-area wanderer only
when its source movement graph can reach the live room. Before ignoring its
normalized short identity, prove that no materially dangerous source mobile
with the same identity can also reach that room; generic names such as
`citizen` must never mask an ambiguous dangerous prototype. Build this
reachability index once for the complete circuit, never once per destination;
the White Stag's 38-stop graph exposed minute-scale CPU stalls from per-room
world scans before the inverted index correction.
Treat duplicate same-prototype targets as a possible assist crowd: `fight.c`
allows an idle mobile sharing the engaged mobile's prototype to join
probabilistically. Skip that stop and continue to later registered circuit
rooms; do not let a matching target in the old room satisfy the next routed
stop before its destination is reached.
Treat an unapproved attacker that joins after combat starts as the same
retryable crowd condition: flee, recover, discard the interrupted research
result, and recheck the source target on the next bounded segment.
When productive work ages an absence or crowd cooldown, reconnect metadata
repair must preserve the remaining count. Historical positive-kill recovery
may restore the policy result, but crowd evidence on that same kill segment or
on a later durable segment still owns its already-decremented cooldown; never
reset it to the default merely because the positive evidence was reconstructed.
Run 4533 both killed the Solace lieutenant and ended crowded at Alex. Run 4544
then reduced that cooldown from three to two at checkpoint 11429, and the fixed
live reconnect preserved two through checkpoints 11430-11433.
Before HERO renaming is available, use source-backed keywords and keep active
gear directly accessible; put spare ambiguous items in containers or the vault.
Never guess object or mobile command keywords when the entity exists in the
public source. Parse and use its source keyword list; display-text noun
inference is only a temporary fallback for genuinely uncatalogued live
entities and must not be promoted into policy without source confirmation.
Choose wear, wield, remove, get, and similar selectors against every carried
source-matched object, including potions and other non-gear. Live run 4403
proved that `wear blue` selected a light blue potion before blue snakeskin
boots; `wear snakeskin` is the unambiguous command. Treat `You can't wear,
wield, or hold that.` as a completed failed gear command so it cannot become an
`eq all`/wear loop.
Enable DD4 `TARGETMODE` before a combat fastwalk. Bind each live `[#number]`
selector only to a mobile whose target-mode line matches its source room
description, and use that exact selector for `consider`, the combat opener, and
targeted combat actions. Never promote an object selector into the mobile map,
persist a live selector across connections or reboots, or replace the reusable
source identity in policy/evidence with an ephemeral selector.
When the complete source mobile catalog is loaded, count only live room lines
that match a catalogued mobile description. Do not run the generic mobile-prose
parser over unmatched lines: TARGETMODE also numbers objects, and ordinary room
prose may contain mobile-shaped verbs. Live run 4533 reached Alex in Solace but
misread `Metal and wooden objects are everywhere.` as a third mobile; the
source-only count retains Alex and the harmless below-band townguard without
inventing that phantom crowd.
When a registered wandering target appears in any source-vetted room while its
circuit is active, stop before the next route step and run the normal crowd,
health, level-ceiling, and `consider` gates against that live selector.
Apply this interception during destination-guided field circuits as well as the
official outbound fastwalk, but only when the current room VNUM belongs to the
active stop's registered route graph. Live runs 4227 and 4235 exposed Old
Thalos lamias walking through those safe transit rooms while endpoint-only
searches missed them; source confirms every mobile-5201 lamia reset equips the
required long slim dagger.
Do not apply the reset-endpoint VNUM restriction to that bounded circuit
interception: the source mobile VNUM identifies the registered prototype, while
an ordinary non-sentinel mobile may have wandered to another room in the same
safe route graph. Still require its exact source display line and fresh
TARGETMODE selector. Live run 4253 saw mobile 5201's lamia twice in Thalos room
5212 and exposed the obsolete endpoint-only guard before the corrected worker
was loaded.
Use the source parser's canonical `strange lamia` identity for this exact
target while retaining `lamia` as the explicit `where_target` and command
keyword. Live run 4273 exposed the combat mismatch: the circuit saw many valid
selectors but a policy targeted only as exact `lamia` rejected all of them.
Live run 4293 then exposed the inverse locator mismatch: `where lamia` reports
rows as `The lamia`, so parsing them as exact `strange lamia` waited until the
watchdog. Live run 4304 proved both identity fixes, then exposed a movement
race: selector `#3416` appeared in room 5239, but the lamia left south in the
same response before `consider` arrived. Remove that stale selector, follow
the observed direction once through the registered route graph, and require a
fresh exact line and selector before considering or attacking. Live run 4307
then found two exact lamias together in room 5239. Treat that duplicate
same-prototype room as a skipped stop and continue to later registered circuit
rooms; do not turn the local assist risk into an immediate circuit-wide
recall. Live run 4309 validated the complete recovery: the circuit found an
isolated lamia at selector `#3398`, disarmed and killed it for the intentionally
below-band 80 XP, looted object 5252, verified the long slim dagger in the
primary weapon slot, and returned at full health to healer room 3054. Apply the same canonical contract to the Forest `kodiak bear` and
Moria `garter snake`; their longer room prose is not the parsed mobile
identity.
When different mobile prototypes share a short description, preserve the
source-distinct identity from the room line and keyword list (for example,
male versus female `a centaur`). Use the generic short name only for the
area-scoped `where` preflight; for source-ranked stops also require the
candidate's exact normalized source room display line before considering or
attacking a live selector.
Persisted GMCP inventory descriptions may still contain an ephemeral
`[#number]` prefix from the connection that recorded them. Strip that prefix
before source-catalog matching, sale planning, equipment comparison, and
liquidation signatures; never treat it as part of an object's identity. Live
run 2047 validated that this recognizes Aruncus's no-drop strange amulet,
triggers `heal curse`, destroys it, and disposes of the remaining unsellable
loot safely.
For source-ranked wandering targets, first follow the source-backed path from
any fastwalk staging room into the target area's source endpoint, then issue a
source-keyword `where` preflight. Require an exact source identity in the
response: related names such as `Farmers guarddog` do not locate `The Farmer`.
A miss from a staging room or another area is not presence evidence and must
not mark the target absent. Once inside the target area, if DD4 returns `You
fail to find anyone by that name.`, or lists no exact target, mark it absent
from the current area and recall rather than enumerating the full area. For a
global wanderer this is current-area evidence, not a reboot-wide absence claim;
rotate to another candidate and retry later. If `where` reports a presence,
retain the bounded source-room search. Treat the reported room as a snapshot,
not a guarantee: check its mapped source-room group first, then continue
through the remaining source-reachable rooms if the wanderer has moved before
arrival. Live run 2048 spent about 290 seconds searching for a globally absent
Kodiak and motivated this gate.
Treat source-program messages that forcibly relocate the character as hard
route hazards. Record the relocation, stop the stale route immediately, and
recall even if GMCP omits the post-transfer room snapshot; never retry doors
or route steps from the pre-transfer location.
If a live field step reports that swimming, flying, a boat, or an accessible
door is required, roll back that waypoint and record the route hazard. Skip
only the blocked registered stop and continue the bounded circuit when a later
source reset remains; if it was the final stop, return immediately. Never wait
for the inactivity watchdog before trying the next safe location or policy.
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
persist the source mobile VNUM for source-ranked exclusions so sibling reset
rooms for the same mobile are excluded too; never return that mobile or policy
until level or reboot changes. Runs 2146 through 2149
exposed both gaps: an unnecessary expanded Toad pass followed by two checks of
the same below-band Moria carrier.
Provision-funding routes may deliberately use a below-band carrier only for a
source-registered coin or saleable-drop requirement, never for XP. A current
level/current-reboot below-band sighting normally excludes that carrier from
funding rotation, but an explicit flight or provision shortfall may use one
source-safe mobile coin carrier after the normal route, crowd, special, and
live-consider gates remain valid. Keep the emergency choice bounded to the
carrier's observed copper-equivalent value and record it as funding-only.
Prefer fresh coin carriers over ordinary gear carriers, then use observed
proceeds, current cash, and rotated completed routes to accumulate the shortfall;
prototype object cost is not realized sale value. Do not route back to a mobile
whose live gate will only produce another skipped segment. Rotate to another
source candidate or surface an explicit funding-unavailable state. When a
flight shortfall remains after fresh carriers have been exhausted, a previously
successful direct ground coin stash may be re-probed once through its source
route; verify the live currency delta and never treat the non-combat collection
as XP progress.
Mandatory maintenance, including funding, food, liquidation, equipment, and
flight recovery, takes precedence over a productive-hunt handoff created by a
temporary research miss. A handoff may resume ordinary field progression only
after those resource and equipment gates are clear.
If emergency loot liquidation meets an unexpected mobile, flee and return to
healer room 3054, preserve the failed run and transcript, and checkpoint the
current liquidation signature as ready. Do not fail the whole campaign or
immediately repeat that unchanged sale pass; resume it only after new loot
changes the signature.
Treat any forced combat during liquidation or other maintenance as transcript
evidence only. It must not become a campaign objective kill, promote a hunt,
consume a source-mobile kill cap, or count as progression XP policy evidence;
the provision-funding exception is explicitly funding-only.
After a failed flight purchase, a stocked character must select source-ranked
no-flight XP work while its retry cooldown remains, even if current cash is
still below the observed same-reboot price. Decrement that cooldown only after
positive-XP field work, then retry or resume funding; do not repeat a funding
route merely to wait.
If the source-ranked frontier has no eligible no-flight target during that
cooldown, return a bounded unavailable checkpoint. Never recursively reselect
the same flight-required candidate; that is a preflight stall, not progress.
If the current reboot-priced flight potion is already affordable and no
no-flight target is reachable, bypass the cooldown and buy it rather than
launching another funding walk solely to wait.
Also buy optional flight before a source-ranked ground route when the source
estimate is at least 100 movement and flight saves at least 60 movement. A
failed optional purchase must cool down and fall back to the safe ground
frontier without creating a funding requirement. Live run 4187 bought the
reboot-priced potion for 90 copper and confirmed a duration-34 `fly` affect;
run 4188 then reached Kerofk mobile 30248 with 260 movement, killed it for
1,168 XP, and had 348/360 movement before recall.
Never quaff a replacement fly potion while `fly` or `levitation` remains
active: source `spell_fly` returns immediately when `AFF_FLYING` is already
set, so the potion is consumed without refreshing duration. Sleep in healer
room 3054 until the old effect expires, then buy and quaff one replacement.
When all current-band source routes are temporarily unavailable because of
reboot-scoped absence, crowd, or route cooldowns, keep the campaign `ready`
and expose the reset wait; never convert that resumable state to `blocked`.
An explicit bounded retry may reopen the route after waiting outside the area.
If a source fastwalk returns without observing its endpoint, quarantine that
candidate as a route hazard, checkpoint `ready`, and rotate to the next source
route. Migrate an already-recorded failed endpoint checkpoint on resume; never
replay the same broken route indefinitely.
If a source fastwalk progress watchdog repeats a movement cycle without state
progress, treat it as a current-reboot route hazard: preserve the failed run
and transcript, quarantine the candidate, checkpoint `ready`, and rotate after
the bounded productive-work cooldown. Do not rerun the same stalled route in
the next invocation.
The same rule applies to optional maintenance fastwalks such as Forest or
Thalos piercing-weapon upgrades: preserve the failed evidence, apply their
existing retry cooldown, checkpoint `ready`, and continue the generic campaign
instead of turning an upgrade-route watchdog into a campaign failure.
Funding routes are waypoint missions: never adopt an unknown or useful-band
aggressive mobile encountered in transit. Preserve any candidate route-hazard
metadata on the generated fastwalk so registered hazards remain active for
funding as well as XP hunts. When an unavoidable transit attacker is
source-proven below the useful band, finish it as incidental combat, then
resume the route; do not count that kill as the funding objective.
Reject funding candidates whose source route crosses a direct or reachable
wandering aggressive reset inside the useful or higher level band. Preserve
below-band route hazards as caution evidence; the runner must finish an
unavoidable source-proven trivial interruption without treating it as an XP
target, so funding cannot dead-end on ordinary Midgaard transit. On a
no-combat funding route, any unexpected useful-band or higher attacker is
terminal for that route: return to healer room 3054 and let campaign rotation
choose the next policy rather than resuming an intermediate waypoint.
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
When consumed sanctuary expires during a generic field fight, do not flee solely
because the affect disappeared. Re-evaluate the live player and opponent HP:
honor the ordinary finish threshold for a target at or below half HP, and
withdraw only at the normal health floor or when the opponent remains materially
healthier than the character; when both sides are low, compare current HP as
well as percentages, while allowing a nearly dead opponent to be finished.
Special-policy `require_sanctuary` fights use the same health-aware matchup gate
after sanctuary loss: continue a favorable one-on-one fight with a usable live
HP snapshot, withdraw when the matchup is unsafe, and fall back to the normal
character health floor while opponent HP is temporarily unavailable; missing
evidence is not an automatic flee trigger.
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
While a live campaign segment is running, its `campaign_segments.run_id` may
remain null until the segment returns. Monitor the newest matching character
run and its event stream before diagnosing a preflight stall or stopping the
worker; a null segment run id is not evidence that no connection opened.
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
Treat the level-16/20 and level-19/20 watchman probe/hunt policies as one
reboot-local reset family: a crowd in either room sets a shared cooldown, so do
not re-enter the other policy name until productive work consumes that wait.
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
Treat the dynamic no-combat interruption used by older named research policies
as temporary route evidence when it aliases a newer source-ranked candidate;
respect its persisted absence cooldown, then allow the generic source route to
reopen after that cooldown expires. Static source hazards, capability blocks,
and live negative `consider` evidence remain hard exclusions.
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
Reset retries are always finite. The CLI and library default to a 30-second
outside-area wait; any longer wait must be passed explicitly with
`--reset-wait`. A retry command must return a checkpoint after its retry budget
is exhausted, and a stale tester process must never be left behind.
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
Persist trainer-level practice rejections only for the current character
level. Persist a trainer-proficiency cap across every level that uses the same
source trainer tier because increasing the character's skill cannot make that
teacher stronger; clear it only when the character graduates to a different
trainer. Do not persist prerequisite rejections because another skill learned
at the same level may unlock them.
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
On Windows, launch detached Python workers with `pythonw.exe` or an explicit
`CREATE_NO_WINDOW` creation flag, and redirect stdout and stderr to `runs/`.
Calling console `python.exe` directly can create a visible `conhost.exe` window
even when the worker is intended to run unattended.
When every fresh current-band source-ranked target is exhausted, the selector
may reuse a same-reboot route only if its evidence records a completed kill
and its policy XP delta is at least 50; this exception does not permit trivial
or crowded routes to loop, and ordinary absent/crowded cooldowns still defer
to the bounded reset controller.
Within that selector, fully source-safe current-band routes have priority over
special-procedure research; among safe routes, productive same-reboot evidence
comes first, then fresh routes, then retryable routes. Research remains
available after the safe progress pool is exhausted.

## Operational Fail-Fast Policy

Treat routine repository, test, live-run, source-refresh, and local process
operations as already authorized by the user. Use direct or previously approved
commands without asking for confirmation. Do not trigger a permission handoff
for an optional status or process audit; if that audit cannot run directly,
skip it and continue productive work. Never leave the task waiting for such an
audit.

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
For routine DD4 source refreshes and Git publication, do not request escalated
execution after an ordinary command times out. The app permission review can
delay command launch outside the command timeout itself; live run evidence on
2026-08-09 showed one such review consuming several hours. Give the ordinary
action one short attempt, defer it on failure, and continue local or live work.
Judge a live tester process by fresh SQLite events via `show-transcript` plus
its process state, never by the JSONL file's observed size alone. A temporarily
stale or zero-length file is not sufficient evidence of a stalled connection.
When launching a bounded foreground segment, give the outer command timeout
more time than the segment's own runtime cap so the runner can recall, save,
and quit cleanly. The StarterBot deadline is a safe-return boundary: request it
once, trust either the local combat flag or a live GMCP enemy list, recall or
flee until combat is gone, recover at healer room 3054, then stand, save, and
quit. Cold source-catalog loading happens before the outer live-session timer;
the StarterBot clock itself starts at the beginning of the run and includes
local setup, and the cleanup phase has a 25-second hard limit. It must produce
a controlled checkpoint rather than leave a socket or process hanging.

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
The streamer configuration must include `USER`; after any logging repair,
confirm the source contains the user record, `streamer.stdout.log` contains
both `Publishing USER record` and a successful delivery with no matching
error, and the checkpoint offset equals the source length with an empty queue.
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
