# Repository Guidelines

## Project Structure

The `dd4tester/` package contains the asyncio Telnet client, GMCP parser,
scenario runner, persistence layer, state model, and CLI. YAML scenarios live
in `scenarios/`; keep reusable scenarios small and non-destructive. Tests are
under `tests/`, with sanitized protocol samples in `tests/fixtures/`. Generated
SQLite databases and JSONL transcripts belong in `runs/` and `transcripts/`;
both directories are intentionally ignored by Git. Generated declarative HERO
requests, profiles, and campaign files belong under `runs/heroes/`.

## Master Goal And Proof Discipline

The master objective is a character-independent engine that accepts any
source-legal race, cosmetic sex, base class, optional subclass, name, and
personality, creates or resumes the character, and plays it autonomously to
HERO level 100. Names and credentials identify stored history only; never add
name-specific behavior to make a live run succeed. Direct Telnet/GMCP is the
primary behavior adapter. Mudlet and Windows VM automation are separate
visibility and lifecycle validation boundaries. AI decision-making remains out
of scope until deterministic behavior is replayable.

Keep proof layered and honest: creation/tutorial, representative level-10
classes, executable class-aware level 1-30 coverage with confirmed subclass
transition, then bands 31-70 and 71-100, followed by fresh creation-to-HERO
runs. A checkpoint, policy-count report, source catalog entry, or research
probe is not proof of progression. Use `verified` for reusable executable
evidence, `research` for bounded probes with explicit limits, and
`unavailable` for an explicit safe stop. Every engineering work unit must
remove a concrete blocker to the next executable level band.

Live continuation anchor for 2026-08-15: Aeloria is level 14 at 84,126 XP,
full in healer room 3054 after the first level-14 rotations. Runs 6533-6542
supplied the level-14 transition, training/provision handoff, Miden'nir and
Ambush evidence, and a source-policy-specific -34 XP protection marker without
a death or manual target selection. The offline suite passes 2,609 tests.
This is level-14 continuation evidence, not a HERO completion claim.

Audit anchor for 2026-08-13: the live level-10 mage/thief/warrior matrix is
complete; Aeloria is level 13 at 74,825 XP, Dorrik level 16 at 123,437 XP, and
Kestrel level 24 at 360,704 XP. Run 5246 proves Dorrik's level-14 transition;
runs 5231 through 5306 prove the surrounding generic source-ranked execution
without steering, including safe healer return and preserved subclass state.
Runs 5274, 5280, 5284, and 5295 add productive current-band alternatives after
the reboot-scoped Dwarven Nobleman probe withdrew at the 15% floor without a
kill. Run 5302 then completed a successful Shire continuation. Run 5307 exposed
an armed Ambush Bardoosh critical-hit death after two incidental low-XP goblin
interruptions; Purgatory recovery, equipment restoration, and healer recovery
succeeded, leaving the durable checkpoint at 87,820 XP. Runs 5308 through
5310 then resumed with productive duty and ranger alternatives, refreshed
flight, recovered a long bow, and returned Dorrik to healer room 3054 at
88,279 XP. Runs 5311 through 5316 then completed maintenance and killed a
Shadow Wraith for 296 XP after trivial transit interruptions, returning safely
at 89,572 XP. Runs 5317 through 5319 then completed daycare and flight
maintenance and killed a source-matched ranger for 624 XP, returning safely;
the long-bow collection hit the carry-count limit without invalidating the
objective kill. Runs 5320 through 5325 then handled sanctuary and Moria
prerequisites, killed a Shire receptionist for 569 XP, and recorded both Wraith
rooms absent before returning safely. Runs 5326 through 5328 repeated the
source-backed Moria/Wraith circuit without forcing an absent objective target;
Dorrik returned safely at 91,025 XP after incidental field kills. Runs 5329
through 5334 then added ranger and Shire receptionist objective kills and
recorded the later Wraith absence without forcing combat. Runs 5335 through
5337 then completed a 743-XP Aruncus kill and safe maintenance; runs 5338 and
5339 completed two safe Wraith probes with incidental goblin XP kept separate
from objective evidence. Run 5344 then completed an Aruncus kill for 919 XP in
166.6 seconds with full health before and after; runs 5345 and 5346 found the
Wraith targets absent and retained incidental goblin XP outside objective
evidence. Run 5353 then reached the Dwarven Homestead through the Miden'nir
bridge, resolved the level-6 mountain goblin by live mobile VNUM 3501, and
recorded a positive consider result for the nobleman without attacking him.
Runs 5354 through 5358 reconciled the standalone probe's XP loss, restocked,
and rotated past crowded or absent candidates. Run 5359 then completed a
source-ranked current-band kill for 413 XP in 141.8 seconds and returned full
to healer room 3054; runs 5373, 5376, 5378, and 5383 added productive
source-matched kills, and the bounded 5385-5386 rotation crossed level 15.
Run 5391 then killed the level-15 Undead Soldier for 956 XP and returned full.
Runs 5392 through 5425 then exercised maintenance, absence, interruption,
source-special crowd, and assertive repeat branches. Run 5419 earned 286
objective XP plus 70 incidental XP and returned full. Runs 5420 and 5421 then
produced only incidental 60-XP and 10-XP transit kills while their objectives
were absent. After objective-aware progress accounting, run 5425 selected a
measured repeat and earned 303 objective XP. Runs 5426-5428 then added 1,400
aggregate XP; the productive nomad commander supplied 536 objective XP, while
the level-8 goblin leader exposed and motivated exact live below-band objective
filtering. Run 5436 then live-validated that repair: mobile 3507 loaded at
level 8, its 80-XP kill was persisted as below-band and non-objective, the
campaign recorded the exact source-policy exclusion, and Dorrik returned to
healer room 3054. Run 5437 moved on to a useful-band fanatical guard and
returned safely at 108,315 XP. Runs 5438-5443 then exercised bounded absence,
repeat, split-locator, and safe-return paths. Run 5444 live-validated immediate
split-locator resumption and safe healer logout; Dorrik is at 109,271 XP. The
following rotation exposed a cross-level status bug: measured Shire and Wyvern
repeats were allowlisted by mobile VNUM but still sorted as `fresh`, behind a
50-XP current-level repeat. Run 5460 live-validated the repair by selecting
Shire receptionist 1131, earning 401 objective XP, and returning Dorrik safely
to healer room 3054. Runs 5467 and 5468 then selected the two strongest
cross-level repeats back to back, earning 283 XP from Wyvern ranger 1706 and
317 XP from Shire receptionist 1131 before safe healer returns. Dorrik is at
111,291 XP. Runs 5470 through 5488 continued the same generic rotation while
keeping absent objectives and incidental XP separate. Run 5493 then killed
Wyvern ranger 1706 for 380 objective XP and crossed Dorrik to level 16 at
115,129 XP; the live checkpoint recorded 345 max HP, 300 max movement, three
practices, subclass `none`, and a safe healer return. Runs 5494-5496 then
proved the level-16 handoff: the
equipment audit returned safely, both Fleshmonger guards were rejected on the
prohibited below-band consider branch, the Warrior trainer accepted `shield
block` and `defense knowledge`, and Aruncus 300 yielded 519 objective XP.
Dorrik finished full at healer room 3054 with two practices and 115,688 XP.
Run 5499 then proved that required-loot accounting includes worn gear: one
worn pink ice ring left one ring outstanding, while the worn linen robe
suppressed the nanny carrier entirely. Runs 5498 and 5500 added 1,107 objective
XP from Bardoosh and Aruncus around that maintenance proof. Dorrik is now full
and safely logged out at healer room 3054 with 117,035 XP; the full offline
suite passes 2,524 tests.
Runs 5502, 5503, 5506, and 5507 then added 1,612 objective XP through
source-matched Bardoosh, Aruncus, ranger, and Bardoosh kills. Runs 5504 and
5505 interleaved bounded ring and flight maintenance without suppressing that
progress. Dorrik finished full and safely logged out at healer room 3054 with
118,647 XP, 14,953 short of level 17.
Campaign revision 164 admits a single source-proven borderline route aggressor
only when its maximum fuzzy level is exactly the useful-band fringe, it has one
global source instance, no special, fame, shop, or no-XP flag, and both its
peak-round and critical-hit bounds are below current max HP. Live GMCP remains
authoritative: defeat it only on a below-band roll; a useful-band roll follows
the existing flee-and-return path. The full offline suite passes 2,528 tests.
Run 5512 proved this gate in Ambush: three unavoidable below-band transit kills
contributed 160 incidental XP, Haglik 4519 supplied 622 objective XP, and the
below-band prisoner and elite guard were considered but not attacked. Dorrik
finished full at healer room 3054 with 119,429 XP, 14,171 short of level 17.
Run 5515 then killed Dwarven Nobleman 20504 for 963 objective XP. Run 5518
added 930 objective XP from Haglik and 160 incidental XP before returning
safely through the runtime watchdog. Dorrik is at healer room 3054 with
121,482 XP, 12,118 short of level 17.
Run 5526 live-validated mapped-room compaction: `where` reported `Path in the
plains`, the runner found Aruncus in room 302 for 501 objective XP, and returned
without a runtime boundary. Run 5527 added 655 objective Haglik XP and 160
incidental transit XP. Dorrik finished full at healer room 3054 with 123,437
XP, 10,163 short of level 17. The named-exit branch remains regression-verified
but not yet post-repair live-validated.
These are
representative checkpoints, not a HERO completion claim. Since that anchor,
runs 5856-5883 crossed Dorrik to level 19 and added a source-ranked XP-loss
ledger, safe level-19 Mirror Realm and Shadow Keep kills, an Ambush guard kill,
and a measured Eastern Desert hidden-attacker throughput result. Runs
5884-5898 then added hard-health withdrawal and sanctuary-recovery evidence,
plus a second successful worm route; Dorrik is now at 182,530 XP and safely
full in healer room 3054. Runs 5899-5918 then widened the source-ranked
level-19 rotation, including a 996-XP Dwarven giant kill, a 692-XP Solace
Foreign Trade Representative kill, and bounded empty or incident-only routes;
Dorrik is now at 184,290 XP and safely full in healer room 3054. Runs
5919-5933 then added exact Eastern Desert route quarantine, separate alternate
desert handling, two productive Arachnos routes, and two productive Solace
Secretary sweeps; Dorrik is now at 189,549 XP and safely full in healer room
3054. Runs 5934-5973 then extended the generic level-19 rotation through
Arachnos, Solace, Haon Dor, Hood, Forest, Shadow Keep, Shire, and Arikasbab.
The exact Arachnos and Arikasbab source policies that lost XP without objective
kills were deferred for this reboot, while unrelated routes continued; Dorrik
is now at 197,009 XP and safely full in healer room 3054. Runs 5974-5996 then
closed the level-19 frontier, deferred a -119-XP Mirror route, and crossed
Dorrik to level 20 through a Dwarven giant kill. He is now at 203,423 XP with
444 max HP, 218 max mana, 340 max movement, three practices, and subclass
`none`, safely in healer room 3054; the first level-20 route is active. The
Runs 6018-6021 then validated movement-starved Great Eastern Desert recovery:
the repaired runner waited through a real movement pulse, recalled from legal
room 5006 without flight, and recovered Dorrik to 444/444 HP, 218/218 mana,
and 340/340 movement before saving and quitting in healer room 3054. The
Runs 6022-6025 then resumed the level-20 rotation: after loot liquidation and
flight maintenance, run 6025 reached Solace room 10295, received a live
perfect-match consider, killed the source-matched level-19 Secretary for 888
XP, and returned safely from 176 HP to full healer recovery. Dorrik is now at
211,328 XP, safely logged out in healer room 3054. The
Runs 6026-6027 then kept the same generic rotation honest: the Solace
sergeant locator returned a live below-band no-match and was skipped, while
the Great Eastern Desert route killed the level-17 giant purple sand worm for
665 XP. Dorrik is now at 211,993 XP after another full healer recovery and
safe logout.
Runs 6028-6030 then liquidated loot, refreshed the safe healer checkpoint, and
repeated the Solace lieutenant route successfully for another 718 XP. Dorrik
is now at 212,711 XP after full healer recovery and clean logout.
Runs 6031-6032 then exercised the Shadow Keep absence gate and a live level-18
Mirror Realm watchman engagement. The watchman reached 26 HP, but critical
pound attacks and bleeding forced a flee at 50/444 HP; the net result was a
safe 193-XP gain after damage credit and the flee loss. Run 6033 killed the
level-17 giant purple sand worm for 616 objective XP; runs 6034-6035 completed
loot and return-home maintenance; run 6036 killed the source-matched level-19
Secretary on the Solace lieutenant route for 622 objective XP. Dorrik is now
at 214,142 XP, full and safely logged out in healer room 3054. These remain
representative level-20 checkpoints, not a HERO completion claim.
Runs 6037-6040 then maintained flight and funding while continuing the generic
rotation. Run 6037 recorded the live Magic Shop stock, bought a light blue
potion for 30 copper, confirmed flight, and returned to the healer. Run 6038
killed the Great Eastern Desert nomad leader for 738 objective XP; run 6039
sold its long curved sabre for 68 coins; run 6040 killed the level-17 giant
purple sand worm for 653 objective XP. Dorrik is now at 215,533 XP, full and
based in healer room 3054. These remain representative level-20 checkpoints,
not a HERO completion claim.
Runs 6041-6045 then completed worm loot and return-home maintenance and
exhausted the absent nomad circuit without forcing a target. Run 6046
live-validated the source-ranked XP-loss guard: the worm route withdrew for a
270-XP loss without an objective kill, and the exact level-20 policy was
deferred for this reboot. Run 6047 then exhausted the Shadow Keep undead
circuit with no target, while run 6048 selected an unrelated eligible Solace
Secretary and supplied 733 objective XP. Dorrik is now at 216,794 XP, full and
safely logged out in healer room 3054. These remain representative level-20
checkpoints, not a HERO completion claim.
Run 6049 then exposed a live flee-latency hazard: Dorrik reached 41/444 HP,
issued the shared 17-percent withdrawal decision, and took one already queued
combat round to 6/444 before escaping after several DD4 flee failures. He
survived, recovered at the healer, and finished at 216,813 XP. The executor now
tracks the largest target-scoped HP loss between authoritative combat snapshots
and adds one observed round to the greater of that loss or the source critical
reserve before selecting flee. This is a timing reserve, not a blanket risk
ban; reset it when the target or combat ends and validate it against live
transcripts.
Runs 6050-6051 then recovered the interrupted flight-maintenance segment and
validated a safe no-target route completion. Runs 6053-6054 exercised two live
Mirror Realm circuits: one exposed a missing destination-guided GMCP exit and
the other reached a viable young boy that departed after repeated kick attacks,
with only 16 HP lost. Run 6055 reached Moria, correctly separated two
below-band transit kills and 360 incidental XP from the below-band troll
objective, and returned full. Runs 6056-6059 then collected source-backed
coins, bought pies and water, repaired food recognition, liquidated a quoted
scroll safely, and restored the healer checkpoint. Run 6060 recorded a clean
Crystal target absence; run 6061 rejected a five-mobile Dwarven Home crowd;
run 6062 then completed two source-matched level-20 woman kills for 1,800
objective XP, bringing Dorrik to 218,973 XP at full healer recovery. These are
productive level-20 checkpoints, not a HERO completion claim.
current detailed assessment and definition of done live in
`docs/PROGRESS_AUDIT_2026-08-13.md`; the prior audit is historical.

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
When plain combat text arrives before `Char.Enemies`, wait one bounded prompt
for the authoritative GMCP enemy record. Resolve a live enemy's source level
by its `isnpc` mobile VNUM before matching its abbreviated display name; only
then may a source-proven below-band transit attacker pass the incidental
combat gate. An unresolved attacker remains a hard route interruption.
Refresh `runs/dd4-source` with `git pull --ff-only` before source-sensitive
research and record the revision used for the decision. The live checkout used
by the 2026-08-13 audit is `f2491fd`. The bundled prerequisite and training
snapshots are pinned evidence from `f703daa`, while the fallback character
catalog is pinned to `0482387`; do not silently present a pinned snapshot as
the current checkout. If a relevant source file changes, either regenerate the
snapshot or record both revisions and re-audit the affected policy.

The registered policy table is a declarative research graph, not a live proof
ledger. After a bounded registered probe has a reboot-scoped result, the
campaign may select the generic source-ranked executor when its candidate
passes source, route, crowd, consider, health, resource, and return gates.
Use campaign segments, objective-kill records, and checkpoints to claim live
progression; `show-policy-coverage` alone never proves that a band is solved.
Treat explicit DD4 flee or death XP-loss text as authoritative negative
progress. Persist the loss evidence and accept the following GMCP progress
snapshot as authoritative; only an unexplained same-level GMCP regression
after a text score is stale. Never restore an older higher same-level XP total
merely because the regression did not include a death; the campaign must
optimize real XP per hour, including the cost of failed engagements.
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
The Great Eastern Desert pyramid maze also needs a live movement reserve:
when a no-combat return or outbound search has fewer than 12 movement points,
sleep until one live step is affordable before issuing another maze move. DD4
regenerates movement on a randomized 3.75-to-11.25 second character-update
window, so the decision must carry a 12-second asynchronous wait after the
specific recovery sleep; repeated sleep commands while already asleep are
intentional until GMCP reports enough movement. Room 5006 is the legal
underground-lake return boundary; if flight or levitation is inactive, both
generic return-home and fastwalk recovery must recall there before any fixed
route can issue the impossible west step. Never let a movement-starved maze
branch spin on repeated navigation.
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
The Mahn-Tor swamp (rooms 2332-2338) is another randomized `no_recall` maze.
On a return-home or runtime-watchdog boundary, follow live GMCP exits to the
stable source entrance 2331, then use the source-backed reverse route through
room 2300 to Midgaard recall room 3001 before taking the ordinary north healer
route. A fixed return-route list ending at a normal Midgaard waypoint must hand
off to the ordinary healer routes rather than report a failed maze escape.
Never retry `recall` in these rooms after DD4 answers `God has forsaken you`;
use the bounded live maze state machine and fail explicitly if its registered
exit graph is exhausted.
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
For base Thief, include the source third-attack chain in the early damage plan:
`second attack` and `armed combat knowledge` must each reach 60 before `third
attack` unlocks. Buy a functional third attack after backstab and knife toss,
then improve second attack before third attack because `multi_hit` attempts the
third hit only after the second hit succeeds. Do not let a prior same-level
physical-practice marker suppress an entirely missing automatic attack skill.
Run class-aware training before every protected fame-recovery fight; a bounded
high-level kill must not bypass newly available damage or mitigation training.
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
must converge. Preserve `Char.Items` target selectors and `Char.Worn`
`instance_id` to source-VNUM mappings for carried objects whose display names
are ambiguous; issue `wear #<instance_id>` for those objects and accept the
source VNUM only after the complete worn snapshot confirms it. Never collapse
distinct live instances back to one display keyword during a stance swap. Keep
a bounded repeated `(stance, worn VNUMs, inventory selectors, command)` guard;
if the same equipment state repeats twice, stop the swap, retain the current
legal gear, record the loop reason, and let the campaign continue rather than
consuming the 500-command run budget.
For multi-command shop maintenance, a generic prompt or unrelated room message
does not acknowledge the pending command. Wait independently for a completed
`list` response, an explicit purchase result, a wield acknowledgement or fresh
`Char.Worn`, and the requested equipment audit before advancing. Buy from an
ambiguous listing with its live `#target` selector, then verify the cloned
purchased object's source VNUM through the post-wield structured snapshot.
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
Persist GMCP hunger and thirst values in character and campaign state. When
negative fame blocks food service and hunger is zero or below, wake the
character immediately and launch the shortest source-safe direct-food policy
that provides enough fullness to end starvation. Never wait for healer HP
recovery while starving: live run 4629 showed starvation damage can exceed the
healer pulses. If the character is fed but lacks a reserve, collect the food
without eating it. Track exact object VNUM acquisition as success even when
urgent food is immediately eaten, then recall and resume fed healer recovery.
Live run 4633 proved the room-331 rabbit route and exact ground acquisition;
run 4634 consumed the roast and cleared hunger from -10 to 14; run 4635 then
recovered Kestrel to full HP, mana, and movement in healer room 3054. Live
run 4636 validated the fed reserve branch: it retained the roast, returned at
full resources, and persisted hunger 9 and thirst 46 in campaign state. Run
4637 then completed a full cure-critical reserve probe with the target absent,
returned to healer room 3054 at full resources, retained the roast, and
persisted hunger 6; an absent prerequisite carrier must not consume the food
reserve or strand the character in the field.
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
For a fixed capacity-two prototype with separate source reset rooms, tag each
stop with its own reset-room policy identity and permit at most two total kills
across the circuit. Retain the exact-one live TARGETMODE gate in every room;
skip a duplicate room and never infer per-room safety from the global reset
maximum.
For a wandering capacity-two prototype, do not collapse its bounded room
search to one kill merely because every stop shares one policy identity. Keep
the global two-kill source cap and the exact-one gate in each live room. Run
4758 followed two `where squire` locations, killed both New Ofcol squires for
422 XP total, and returned safely to healer room 3054.
When a current-reboot hunt withdraws with negative XP before a kill, persist
that policy as protection-recovery evidence and do not immediately reselect the
same source route. Recover or acquire the required protection first, or choose
another current-band route; a later retry is allowed only after the recovery
gate clears.
For source-ranked hunts, a negative net XP delta before an objective kill is
also durable evidence when consider outcomes are empty (for example, a live
GMCP level-band abort). Persist the exact policy, reboot identity, level, and
delta; exclude only that exact policy on the same reboot, and clear it only
after that policy records its own objective kill. Do not reject unrelated
current-band routes.
During active combat, track the largest HP loss for the current target between
authoritative snapshots. DD4's `do_flee` waits a violence pulse before reporting
failure or success, so use one additional observed round plus the greater of
the source critical-hit reserve and that observed loss as the withdrawal floor.
Reset the reserve when the target or combat ends; this absorbs command latency
without turning normal current-band combat into an automatic retreat.
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
When source route scoring finds one of those proven noncombat specials in a
large below-band transit crowd, retain the hazard in evidence but do not turn
it into an autonomy rejection. Ordinary aggressive crowds and all unclassified
specials remain route-gated.
For a live target-room crowd, resolve every matching source mobile profile and
retain ambiguous identities, including profiles with no special. Ignore a
bystander immediately only when every matching profile is nonempty and every
special is source-proven non-attacking or combat-only in transit. A sole
`spec_guard` profile may stop inflating the crowd only when the controlled
character's alignment is at least 300 and one complete crowd retry has passed
without hostility; lower alignment and ambiguous profiles stay blocked. Run
5418 proved the good-alignment Ofcol cityguard remained non-hostile throughout
the bounded wait, though Aruncus wandered away before consider.
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
Classify source-proven combat-only specials separately from target safety.
`spec_cast_undead` scans only for a victim already fighting its mobile and
returns otherwise, so a non-aggressive mobile with that special is safe to
cross without engagement. This transit exception does not permit selecting or
fighting the special mobile and must not be generalized without reading the
specific source implementation.
Never select a mobile carrying `ACT_LOSE_FAME` for XP or funding. Live run 4564
proved that killing Solace mobile 10255 (Alex) cost 12 fame; DD4 then blocks
both shop service and leveling while fame is negative. Treat a reputation shop
refusal as a bounded, nonfatal return to the healer. When fame is negative,
restore a legal field weapon first and acquire a purple sanctuary reserve.
Try the level-31 Circus ticket clerk (mobile 4400, room 4402) before the
level-30 Mirror Realm buck or moose circuit. All three are single,
non-aggressive, special-free source resets. Attack exactly one isolated target
only when live `consider` returns the `laughs at you mercilessly` branch,
confirming the six-to-nine-level fame-award band; return to the healer after
each kill and repeat until live fame is nonnegative. DD4 ignores legacy mobile
hit and damage dice when `create_mobile` derives ordinary combat values from
live level. Shop `G` stock receives `ITEM_INVENTORY` and is extracted from a
dead shopkeeper, so never expect the clerk's ticket to drop. A live nonnegative
fame value clears the sticky shop-refusal marker.
In Circus room 4402, source-proven level-3 Bobby's mother and wandering
Midgaard Beastly Fido are trivial bystanders for the clerk probe. The latter is
`spec_fido` and cannot attack a normal player. Ignore those exact identities
there, but retain the crowd gate for every other mobile.
The fame routes require at least 95% health before the opener, but that is not
their combat withdrawal floor. Once sanctuary is confirmed and combat begins,
use the normal 15% field floor and live matchup logic; never flee merely because
health drops below the departure threshold.
Before another bounded fame-recovery fight, carry one source-verified
`cure critical` potion in the worn pouch as well as sanctuary. Select its
carrier by parsed potion effect, safe source route, mobile risk, and exact live
target count rather than by a fixed character or route. A reset capacity of two
is admissible only when TARGETMODE proves exactly one matching carrier in the
room. Use the healing reserve at or below 55% combat health without consuming
sanctuary during the below-band acquisition fight.
Potion display names are not provenance. Moria object 4150 and Thalos object
5210 are both `a black potion`; the first casts `cure critical`, while the
second casts `blindness` and `giant strength`. Retain parsed object value
strings, bind an ambiguous potion to the exact source reset that produced it,
persist that verified count across pouch audits, and decrement it when quaffed.
Never classify, stow, or quaff an ambiguous black potion from name alone.
Select any source-safe potion that provides the required spell, then persist
and use its actual source-unambiguous command keyword; do not pin cure-critical
acquisition to a black potion or one route. DD4's multi-object `put all.<name>`
path can place non-potions in a worn pouch, so stow one exact collision-free
selector at a time and remove any audited pouch contaminant before combat.
If sanctuary expires before a protected opener and no reserve remains, record
the target as live and viable with a sanctuary dependency. Do not assign an
absence or generic failed-hunt cooldown; acquire a new reserve first, then
return to the same gated target.
After an absent or rejected fame target, require three productive field
segments before retrying that exact circuit. Preserve the sanctuary potion
until a source-matched target passes its live consider gate; ordinary
source-ranked alternatives must not consume it. A living low-roll Mirror
Realm mobile retains its live level until it dies or the world reboots, so a
cooldown alone cannot reroll it.
The flight-assisted Lotus Temple chamber attendant (mobile 10736, room 10837)
is an independent fame-recovery research route only while carrying both a
light blue flight potion and a purple sanctuary potion. Live run 4581 reached
the level-31 attendant and exposed a post-opener guard that incorrectly
reapplied the ordinary +1 level ceiling after the six-to-nine-level consider
gate. Twenty-two failed flee attempts ended in death; the Purgatory controller
recovered the corpse and returned Kestrel fully equipped to healer room 3054.
The active-combat GMCP guard must honor the current stop's explicit maximum
level offset. Any research-hunt death is nevertheless durable fatal evidence,
including a death after the nominal target kill when the whole attempt loses
XP: preserve the objective-kill observation for audit, but do not mark the
route viable or reopen that exact policy at the same character level and
reboot, even after ordinary retry cooldowns expire.
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
player damage. Preserve both as reusable level-20 source-ranked evidence. Live
run 4638 killed the level-band Old Treant for 971 XP while losing only 9 HP;
that margin requires continuation to another vetted target when a safe circuit
is available instead of an unconditional single-kill recall.
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
DD4 may send a prompt before the rows of a `where` response. A bounded locator
grace timer must be evaluated before the ordinary `prompt_ready` gate so its
expiry can wake the policy without another server prompt. Apply the same rule
to the magic-shop drunk preflight. Preserve a synthetic line boundary when a
new locator header begins in a later socket read, but do not split a target row
that genuinely continues across reads. Run 5442 exposed both defects by
waiting for the inactivity watchdog after `where nomad`. Run 5444 then parsed
the delayed leader row in Fungus Temple, issued its next command in the same
timestamped read, completed the bounded search without a watchdog event, and
saved and quit at healer room 3054.
Normalize flattened GMCP room descriptions with the same sentence boundaries
used by live room output before applying crowd gates; furniture or other static
room prose must not become a phantom mobile. Ignore companions only when their
source identity is explicitly trivial for the current character level.
When the source mobile catalog is available, subtract static GMCP room prose
only through exact normalized source display-line matches. Never subtract a
live source-matched mobile by a generic noun parsed from differently worded
room prose. Run 4773 incorrectly removed the visible Fleshmonger cook because
the room said `a cook is bent` while the mobile said `the cook bends`; run 4779
then retained selector 23775, killed the cook for 322 XP, recovered its dropped
weapon after a disarm, and returned safely to healer room 3054.
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
Apply the same floor when authoritative `Char.Enemies` identifies the exact
source target at five or more levels below the character after aggression has
already forced combat. Finish a harmless unavoidable fight when appropriate,
but record the kill as incidental, persist the exact source-policy below-band
sighting, and do not let its XP satisfy the objective or reset no-progress
selection. Explicit required-loot carriers retain their separate audited
exception. Run 5426 exposed this when level-15 Dorrik's selected goblin leader
loaded at level 8 and paid only 80 XP among forced Miden'nir attackers. Run
5436 proved the repaired path end to end: the SQLite kill ledger stores
`below_useful_band=1` and `objective_eligible=0`, omits source-policy credit,
and restart reconciliation filters the row from objective progress.
Treat an explicit objective kill below 50 XP as contact evidence only, not as
productive source history or permission to repeat a route. Use the tagged
`source_policy_id`/mobile VNUM for wandering kills; never attribute the reward
to the selected room or a display-name anchor. Fall back to the segment XP
delta only for legacy kill records that lack explicit objective XP metadata.
When the best fresh source prototype has less than a 50% chance for its normal
level fuzz to land inside the useful consider band, prefer a same-reboot route
whose latest recorded kill still earned meaningful XP, even after its third
kill. High-confidence fresh targets retain priority, and a repeat stops being
eligible when its latest reward falls below the meaningful-XP threshold.
Apply the 50% fresh threshold across the complete research pool ordering, not
only within one candidate category. A low-probability capacity probe must not
hide a high-confidence level-ceiling probe merely because capacity research is
visited first. At level 11, revision 162 replaced the 20%-useful Circus father
with the 60%-useful Shire receptionist; live run 4771 earned 743 XP and returned
safely to healer room 3054.
Carry that reward evidence across a character level boundary by source mobile
VNUM, not by the generated policy ID's level suffix. Use the tagged objective
kill's `xp_gained`, because a level transition can make the aggregate XP delta
look negligible. Campaign revision 156 threads those proven repeats through
same-area circuit construction, so capped but still-productive mobiles can
form a multi-kill route while live consider, crowd, health, and below-band
gates remain mandatory.
When a cross-level repeat is allowlisted by that evidence, classify it as
`productive` for candidate ordering even if its new level-suffixed policy ID
has no direct result yet. Do not let a weak current-level repeat outrank it
merely because the regenerated ID is marked `fresh`. Run 5460 proved this
handoff by replacing a 50-XP Ambush goblin route with the Shire receptionist
and earning 401 objective XP. Runs 5467-5468 then proved repeat rotation after
cooldown by earning another 600 objective XP from the Wyvern and Shire routes.
Run 5493 proved that the same source-mobile reward continuity survives through
the next level transition: ranger 1706 earned 380 objective XP, crossed Dorrik
to level 16, and returned him safely to healer room 3054.
If the fresh selector initially returns a research-only candidate, still
evaluate the current-band productive repeat pool before stopping or exposing
the research route. Research must never mask executable progress. For legacy
source-ranked segments that lack a mobile VNUM, carry forward XP only from the
unambiguous selected candidate record; never guess an identity from a display
name or assign the reward to a different prototype.
Live run 4727 validated the level-11 Gnome circuit after seven same-reboot
kills per prototype: Aeloria killed treasurer 1521 for 368 XP, continued to
cook 1526 for 191 XP, ate the cook's severed leg, then returned to healer room
3054 at full health and movement. Preserve the tagged reward per mobile VNUM
and the two-kill route as reusable evidence until a later reward falls below
the meaningful-XP threshold or a live gate rejects either stop.
Do not poll a just-killed source prototype before its area can plausibly reset.
Campaign revision 158 blocks each tagged mobile VNUM until two later completed
source-ranked hunt segments have run; city maintenance does not count. Live
run 4731 killed the Gnome pair for 448 XP, run 4732 supplied only one
intervening Daycare hunt, and premature run 4733 then found both Gnomes absent.
The two-segment cooldown would have blocked exactly that wasted revisit while
leaving other areas available for productive work.
Live run 4734 validated the selector boundary: it withheld the recent Gnome
and Daycare VNUMs, killed Moria large orc 4005 for 166 XP instead, and returned
to healer room 3054 at full health, mana, and movement.
Live run 5047 exposed a route-throughput hazard in the Gnome kitchen approach:
the source-safe cook route crossed barracks resets permitting up to 15-20
below-band aggressive soldiers, producing a long chain of incidental 20-40 XP
kills before the useful endpoint. Reject a route that crosses an aggressive
below-band reset with capacity greater than four, while retaining lone
source-proven below-band interruptions as finishable transit hazards. A
source-backed required-loot reserve may retain that route only when its exact
carrier also passes the one-live-target, isolation, health, and item-provenance
gates; this exception does not reopen the route for ordinary XP hunting.
Bound that discovery preference with durable throughput evidence: after two
consecutive same-level, same-reboot source-ranked segments earn zero XP, choose
a proven meaningful repeat even when the next fresh candidate has at least 50%
useful fuzz odds. Derive the streak from campaign segment history, ignore city
maintenance between hunts, and reset it on XP gain, level change, or reboot.
Runs 4537-4541 produced five consecutive zero-XP probes after run 4535 earned
1,044 XP, proving that unbounded fresh discovery can displace progression.
An explicit `--retry-stalled` rotation may reopen a current-reboot
retry-exhausted policy only when that exact policy is also a meaningful,
productive repeat. Keep the marker binding during normal selection and never
use the switch to open unrelated absence, crowd, protection, or route-hazard
cooldowns.
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
For the optional `recover-daycare-ring` equipment probe, a live below-band
source target is terminal for the current level and reboot: persist
`campaign_daycare_ring_blocked_level` and
`campaign_daycare_ring_blocked_boot_id`, clear the temporary countdown, and
reopen only after either identity changes. Do not spend productive field
segments retrying that same ring route.
Attach a below-band source-mobile key only when the active execution is the
matching source-ranked policy. Bespoke equipment or maintenance hunts may
inherit a stale candidate record at their checkpoint boundary; never let that
record exclude an unrelated source mobile. Sanitize mismatched and non-source
keys during policy revision repair.
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
with a trivial forced fight. Cast it before stepping south for the fountain
water preflight, then confirm the affect before moving. Live run 4702 reached
the fountain before casting and was forced to kill the wandering drunk for 10
XP; the ordering fix prevents that avoidable transit combat.
Before a Magic Shop trip, use known invisibility when available. Otherwise
issue `where drunk` from healer room 3054 and defer the trip when mobile 3064
is in a source-route room. Its `greet_prog` calls `mpkill`, while
`mprog_greet_trigger` requires the mobile to see the entering player. Treat a
blocked route as a bounded retry after productive work, not as an
unaffordable-purchase result.
Live runs 4668-4669 exposed an immediate next-connection retry despite the
three-segment marker: run 4668 correctly stayed at the healer while the drunk
blocked the route, but run 4669 immediately crossed the now-clear route and
bought flight. Campaign policy revision 148 therefore persists the route block
against the reboot identity, suppresses another affordable purchase until
three productive field segments advance the cooldown, and clears the block
only when that cooldown completes, active flight is confirmed, or the reboot
identity changes.
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
A generated circuit applies the full departure-health gate only before its
first target. After an objective kill, ordinary later stops use the 22.5%
field-continuation floor; stops with specials, sanctuary requirements, or
bounded peak-damage exceptions retain the 67.5% high-risk floor. Live run 4683
validated this at level 10: Aeloria killed Gnome treasurer 1521 for 276 XP,
continued at 129/145 HP, killed cook 1526 for 248 XP, and returned to healer
room 3054 at full health. The two-kill circuit earned 524 XP in 114 seconds.
After loot, use the same 7.5% mana and 5% movement continuation floors; never
fall back to the old 30% mana recovery gate while a kill-budget-eligible target
remains. Scan past targetless locator or transit stops to the next actual
combat stop before deciding that the circuit is over. Live run 4692 exposed
the stale mana gate by recalling at 87/382 mana after one kill; campaign policy
revision 153 clears throughput markers produced by that obsolete boundary.
When the kill budget is already exhausted, return normally and do not report a
fictional next-target recovery failure.
A failed live `consider` at one generated circuit stop must preserve that
policy-specific evidence and advance to later independently tagged stops. Recall
only when no vetted stop remains or the stop explicitly requires abort after
rejection.
Key generated-circuit `consider` and below-band evidence by the active stop's
source policy ID, mobile VNUM, and reset room. Never assign a supplementary
stop result to the primary route merely because both ran in one segment. For
legacy transcripts without stop IDs, match only an exact normalized source
identity after stripping a leading article. Campaign revision 151 repaired
the Fleshmonger level-10 history so cook 9403 remains productive while the
independent cook's boy 9404 remains terminally below-band.
Key absence evidence by the same exact source policy. Presence or a live
`consider` at one supplementary stop must not hide an absent primary reset or
cool down the whole circuit. Live runs 4717 and 4719 exposed the old aggregate
failure at mage level 11: absent Ivan 4409 was retried because the visible,
below-band Bearded Lady and Illusionist made the circuit look present. Campaign
revision 154 began recording each searched reset miss independently. A later
live sighting, `consider`, or kill for that exact policy must clear and dominate
all waypoint misses; run 4721 found and fought the wandering Shire Miller
before it fled through a crowded room, proving that an empty later waypoint is
not target absence. Campaign revision 155 preserves the positive presence and
applies absence cooldowns only to policies never seen during the circuit.
Before any hunt fastwalk from recall, refill the carried water skin in room
3005, drink there, and return north; never rely on a stale in-memory thirst
flag for a long route.
When negative fame makes a shopkeeper refuse food, never bounce between that
shop and the healer. Rank source-direct ground food resets, exclude every food
prototype with a nonzero poison value, bind acquisition to the exact object
VNUM and source keyword, and carry the reserve home before consuming it. Treat
an empty reset as a bounded, reset-specific absence and rotate to another safe
food route.
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
For every source-ranked combat stop, also carry the source-derived maximum
critical damage of one NPC hit. DD4 criticals double one ordinary hit; when
that verified burst can kill at current HP, raise only the active stop's live
withdrawal floor to the burst ratio. Otherwise retain the aggressive 15%/10%
thresholds. Do not blanket-reject armed, high-XP targets: preserve explicit
bounded peak probes and research pools, and let source, live consider, gear,
protection, and reward evidence balance risk against XP per trip. When a safe
fixed-reset area offers multiple isolated targets, rank the whole circuit by
risk-adjusted source reward per outbound and inter-target travel step. A
wandering high-score candidate must not suppress that circuit merely because
it ranked first as a singleton. A death during a source-ranked attempt is
fatal evidence for the exact mobile VNUM, reset room, character level, and
reboot, including when an objective kill was recorded before the death and the
net attempt lost XP. Preserve that kill as forensic evidence, but block blind
retries. Tag objective kills by exact source identity so incidental transit
kills cannot inflate progress or promotion evidence.
Balance risk against throughput rather than minimizing death probability alone.
An expired absence or retryable probe is not progress evidence: when a
same-reboot source route has a meaningful measured XP return, let that
productive repeat outrank the retry unless the fresh route has materially
stronger risk-adjusted reward evidence. A no-flight fallback must not displace
a productive route solely because it avoids buying flight; preserve the normal
source, live-consider, crowd, health, protection, and return gates while
optimizing expected XP per travel step.
Quantify the fresh-route exception: a fresh candidate may displace a
productive repeat only when its risk-adjusted source score per travel step is
at least 25% higher. The score is a route reward proxy with a soft peak-damage
penalty, not a replacement for live gates. Keep the requested mobile's own
aggressive reset in the risk pool when its route is otherwise source-reachable;
score the aggression as caution and enforce the normal consider, isolation,
health, protection, equipment, and return checks instead of rejecting it solely
for being aggressive. Other aggressive route or companion hazards remain hard
blocks.
Live run 5402 validated this balance for Dorrik: Bardoosh mobile 4515 in room
4514 produced 671 objective XP and 851 XP total after three incidental 60-XP
goblin kills, then returned safely to healer room 3054 at full health and
movement. Runs 5392 through 5401 remain recovery, maintenance, or low-value
contact evidence and must not be misreported as equivalent progression.
Run 5403 then selected Aruncus the Druid, mobile VNUM 300 in reset room 323,
for 505 objective XP and a full healer return. Dorrik reached 101,307 XP;
this is productive level-15 evidence, not merely a safe recovery.
Run 5405 repeated Bardoosh mobile VNUM 4515 for 351 objective XP plus one
incidental 70-XP goblin kill, returning at full HP and 264/290 movement. Keep
the repeat eligible while its tagged reward remains meaningful and its live
gates continue to pass.
Run 5406 repeated Aruncus mobile VNUM 300 for 462 objective XP and returned
at full HP and 269/290 movement. Continue this productive repeat while its
measured reward remains meaningful; do not let an empty unrelated route or a
generic safety preference displace it.
Run 5407 found fanatical goblin guard mobile VNUM 4516 wandering into room
4522; Dorrik killed it for 264 XP after absorbing a critical hit and returned
safely for healer recovery. The transcript proved the exact live VNUM even
though the registered reset-room stop used a different display name, so retain
wandering kill attribution by source identity rather than by room label alone.
Run 5408 accepted the measured Bardoosh repeat: mobile VNUM 4515 yielded 460
objective XP and a wandering goblin added 70 incidental XP. Dorrik returned
without death or flee at full 322/322 HP and 279/290 movement. Treat this as
productive risk/reward evidence and keep the repeat eligible while its tagged
reward remains meaningful; do not optimize for zero damage or zero incidental
encounters when the live withdrawal and return gates still pass. Run 5409 then
selected Aruncus for 421 XP in 69.8 seconds and returned at full HP; run 5410
reopened the cooled Shargugh route and confirmed it absent. Runs 5411 and 5412
were required flight/provision maintenance and must not be counted as XP work.
Run 5413 reached Bardoosh and SQLite events recorded a 60-XP goblin-lieutenant
interruption plus a 460-XP Bardoosh kill, but the worker was stopped after its
transcript stayed empty; run 5414 recovered safely at 103,935 XP. Keep the
interrupted segment failed until its kill metadata is reconciled, and close both
the segment and its unbound run record during process recovery. Persist each
recognized mob kill and loot sale immediately while the run is active, not only
during normal runner cleanup. Recover an interrupted source-ranked objective
from the run-scoped kill ledger only when its exact `source_policy_id` matches;
never promote an incidental kill. Run 5417 proved that a kill row was externally
visible while its run still had status `running`. Run 5415
confirmed both Shadow Keep Wraith rooms absent after one incidental 60-XP goblin
interruption; do not promote that result. Run 5416 then reopened fanatical
goblin guard mobile VNUM 4516, earned 257 objective XP, and returned at full HP
with 281/290 movement. This is an approved higher-risk repeat because the
reward remained meaningful and the live withdrawal/return gates passed.
Run 5419 then killed the same source-matched guard for 286 objective XP plus 70
incidental XP and returned full at 104,728 XP. A confirmed objective kill must
force target-presence evidence and clear stale target-absence state before the
segment and campaign snapshots are serialized.
For source-ranked throughput, count progress only from objective-kill evidence,
not the character's aggregate XP delta. Incidental transit kills must not reset
the no-progress streak, clear unrelated absence evidence, or become the current
policy's productive XP result. Apply the same calculation during a live
multi-segment process and when reconstructing after restart. Runs 5420 and 5421
earned 60 and 10 incidental XP with empty objective-kill lists; the repaired
two-segment streak forced a measured productive repeat, and run 5425 killed
mobile 4516 for 303 objective XP before returning safely at 105,161 XP.
Do not let the generic non-fastwalk 25% emergency-resupply floor override a
field fight's 15% withdrawal or 10% finisher threshold.
For a return-home checkpoint at the healer, use the same 90% movement floor
both when deciding to sleep and when deciding to wake. A lower generic wake
floor creates a no-progress sleep/stand command loop.
After a completed field hunt reaches healer room 3054, recover to the same 90%
movement floor before save and quit. The lower field-ready reserve may carry a
return through Midgaard, but must not force the next campaign segment to spend
a separate connection on healer recovery.
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
For static required-loot circuits, derive trivial bystanders per destination
room from the source movement graph and the current character level. Do not use
a world-wide display-name level range when source reachability can distinguish
the local low-level prototype from a dangerous namesake. Live run 4654 used
this gate to ignore the level-1 teddy and level-3 toy soldier, kill an old doll
and the nanny for 151 XP, and return Dorrik safely at full health.
For source-ranked room isolation, include a trivial same-area wanderer only
when its source movement graph can reach the live room. Before ignoring its
normalized short identity, prove that no materially dangerous source mobile
with the same identity can also reach that room; generic names such as
`citizen` must never mask an ambiguous dangerous prototype. Build this
reachability index once for the complete circuit, never once per destination;
the White Stag's 38-stop graph exposed minute-scale CPU stalls from per-room
world scans before the inverted index correction.
When the bot opens a source-closed door, live movement can place an ordinary
wanderer outside that static graph. In that case, permit an area-scoped
fallback only when every same-area reset prototype with the normalized live
identity is source-proven trivial at the current level. Campaign revision 157
adds this boundary after run 4730 found Granny Jenkins with a harmless level-5
New Ofcol citizen in room 600; a dangerous same-name prototype still preserves
the crowd rejection. Live run 4744 validated the repair: the citizen no longer
made Granny Jenkins appear crowded, while her below-band live `consider` still
prevented combat independently.
Apply the same reverse-reachability proof to global wanderers whose source
movement can cross area boundaries. Ignore only an exact trivial identity that
can reach the destination, and retain it as a crowd when any dangerous
same-named prototype can also reach that room. Live run 4678 exposed wandering
Midgaard Fidos and a vagabond inside the Circus; campaign revision 150 reopened
the resulting false crowd result for the Bearded Lady and Illusionist circuit.
Treat duplicate same-prototype targets as a possible assist crowd: `fight.c`
allows an idle mobile sharing the engaged mobile's prototype to join
probabilistically. Skip that stop and continue to later registered circuit
rooms; do not let a matching target in the old room satisfy the next routed
stop before its destination is reached.
For a source-ranked mobile proven by `MobileSource.wanders` to move, do not
discard a full circuit merely because the target enters a crowded room. Remain
standing and re-run `look` at 12-second intervals, deriving three to eight
attempts from the number of source-reachable exits. This mirrors the four-second
`mobile_update` and 1-in-32 chance per usable direction, targeting about a 50%
chance that the mobile leaves while keeping the live segment bounded. Retain
every normal source, identity, isolation, health, and live-`consider` gate, and
cancel the wait immediately if combat starts.
Live run 4601 validated the timer against Mirror Realm mobile 19022 in the
one-exit Travellers Shop: three 12-second looks remained safe but did not move
the gardener. Source `update.c` then justified the exit-weighted three-to-eight
look budget. The same rotation continued productively in run 4603, where
Kestrel killed Mahn-Tor mobile 2301 for 1,137 XP and returned to healer room
3054 at 274/334 HP without consuming the reserved sanctuary potion.
For Mirror Realm fame recovery only, treat an unrelated wandering mobile in
the buck or moose room as potentially transient. Remain standing, re-run
`look` up to three times at 12-second intervals, and apply the full source
identity, isolation, health, sanctuary, and live-`consider` gates after every
refresh. Any combat interruption cancels the wait immediately. If the room is
still crowded after the third refresh, preserve the normal retryable crowd
result and return to the healer without consuming the sanctuary potion.
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
Historical clear-marker recovery is event-specific: only an explicit
`research_policy_retried` checkpoint may restore `campaign_cleared_research_policies`.
`campaign_metadata_repaired`, `source_policy_rotated`, and segment-complete
snapshots are derived state and must not be replayed as new clear decisions. If
protection recovery is required while its sanctuary policy is on cooldown,
report that protection wait before applying unrelated crowd or reset handling.
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
DD4 mobile arrival notices do not include a TARGETMODE selector. When an exact
active source target produces `<target> has arrived.` in a source-vetted route
room, pause navigation for one `look`; only the resulting source-matched room
line and fresh selector may enter the ordinary interception gates. Do not treat
the arrival notice itself as combat authorization. Live run 4616 saw the large
hobgoblin enter Moria room 4063, but the pre-fix circuit continued navigating
and returned without its sanctuary potion.
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
Apply the same bounded pursuit when an engaged target flees: live run 4673
reduced Circus mobile 4409, Ivan, from 106 to 57 HP before he fled east, but a
cleared live-enemy identity prevented the old detector from following him and
six stale `kill #2923` commands triggered the watchdog. Campaign policy
revision 149 recognizes an observed departure after combat has started even
when GMCP has already cleared the active identity, removes the stale room
selector, and follows the legal adjacent exit for a fresh room safety check.
Treat a seen or considered target as positive evidence even when it survives:
never propagate whole-circuit absence to supplementary resets. Revision 149
repairs the primary as a retryable present attempt and reopens any unvisited
supplementary targets; run 4675 confirmed the repaired checkpoint before a
productive two-kill, 495-XP Fleshmonger repeat and safe healer return.
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
DD4 can also emit malformed `Char.Items` JSON when a scroll description contains
unescaped quotation marks. Keep the structured parser as the first path, but
fall back to a bounded item-entry recovery that preserves quantities and
`[#number]` selectors; otherwise a newly purchased pie can disappear from the
food reserve detector and cause a needless funding loop. Cover this fallback
with a fixture derived from a redacted live payload.
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
not a guarantee. Collapse differently named intermediate rooms into
movement-only legs, inspect every safe room in the mapped name group, then
refresh `where` once from the actual current room using source routes generated
for every safe origin. Do not blind-sweep the remaining differently named
rooms first. Preserve the complete waypoint sweep only for legacy locators
without a safe relocation graph. Run 5516 spent its 240-second boundary on 42
Aruncus destinations; the repaired `Grassy plains` group requires seven target
checks. Live run 2048 spent about 290 seconds searching for a globally absent
Kodiak and motivated the original gate.
Treat source-program messages that forcibly relocate the character as hard
route hazards. Record the relocation, stop the stale route immediately, and
recall even if GMCP omits the post-transfer room snapshot; never retry doors
or route steps from the pre-transfer location.
If a live field step reports that swimming, flying, a boat, or an accessible
door is required, roll back that waypoint and record the route hazard. Skip
only the blocked registered stop and continue the bounded circuit when a later
source reset remains; if it was the final stop, return immediately. Never wait
for the inactivity watchdog before trying the next safe location or policy.
Treat any pending movement response of the form `The <source name> is closed.`
as a dynamic exit, not only `door` or `grate`: roll back the exact route index,
issue `open <direction>`, and retry. If the named exit reports locked after the
open attempt, stop the stale route and recall. Run 5518 exposed this with `The
brush is closed`; its watchdog returned Dorrik safely before the generic parser
was repaired.
Do not let one borderline aggressive transit reset permanently hide a deeper
source-safe circuit. It may be crossed only when its maximum source-fuzz level
is exactly `character level - 4`, the prototype has one global reset instance,
no special, fame, shopkeeper, or no-XP flag, and its maximum peak round and
critical hit are each below current max HP. Require live GMCP level evidence:
finish it only below-band, and flee from a useful-band roll. Run 5512 validated
this with Ambush mobile 4516 before a 622-XP Haglik kill and a safe healer
return.
Treat profession-visible empty `eq all` slots as equipment debt. Prefer usable
mob drops, then inexpensive class-legal Midgaard basics; after major gear loss,
revisit Mud School first and repeat its course to recover free starter drops.
Count required replacement gear across both carried inventory and the
authoritative worn paper doll. A worn item satisfies its share of a duplicate
quantity requirement; never attack a carrier for an item already worn. Run
5499 proved that one worn pink ice ring leaves only one ring missing and a worn
linen robe removes the nanny branch.
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
Old dolls from the room-6604 reset can wander north into room 6603, but that
reset has no `E 1 6601` ring load. Observe or bypass those wanderers; do not
use them as a pink-ring required-loot exception. The room-6605 reset loads two
mobile-VNUM-6605 dolls and applies its single `E 1 6601` ring load to the last
created doll. Enter room 6605, use the last exact TARGETMODE selector, and
perform one carrier attempt per area reset. Keep the second finger objective
for the existing reboot-local retry cooldown rather than killing the other
10-XP doll without a possible ring. The room-6602 nanny's separate `E 1 6621`
reset remains valid for the linen robe. Source evidence comes from
`daycare.are` at DD4 revision `f2491fd`; do not infer a second ring from the
mobile reset capacity.
When a static required-loot `FieldHuntStop` has a known source reset room,
record it as `source_reset_room_vnum`. The route may pass through a waypoint
where the same mobile has wandered, but field interception and ordinary target
evaluation must wait until that registered room. This endpoint gate is generic
and must not be replaced with character-specific target handling.
An absent or crowded ring carrier is a temporary area-state miss, not a
reboot-scoped failure. Rotate through three productive field segments before
retrying the Daycare ring recovery during the same reboot; a reboot permits an
immediate retry. Policy-revision migration must preserve an in-progress retry
countdown, and below-band evidence from a required-loot nanny or doll must not
exclude `recover-daycare-ring` itself. Runs 4738 and 4760 respectively proved
the countdown decrement and the repaired exclusion-free live retry.
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
Keep optional-maintenance fastwalk results out of generic research metadata.
Preserve their dedicated retry cooldown, but clear transient crowd, absence,
consider, and abort fields before checkpointing so the retained last XP policy
cannot inherit a maintenance-room outcome. Runs 4653-4654 exposed and verified
this separation for Dwarven Day Care ring recovery at policy revision 145.
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
For the Dwarven Nobleman fastwalk, the source-level-seven goblin lieutenant is
an allowed below-band transit interruption from level fourteen onward: finish
it only under the ordinary live combat, health, and crowd gates, record it as
incidental, and resume the route. Keep the source-level-eight dark horseman
and wyvern as hard hazards because their damage or procedures can overwhelm a
nominally below-band character.
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
return to healer room 3054. If item-count capacity is full, liquidate or
donate safe carried drops before entering the weapon shop; weight capacity
alone does not prove that a purchase can be carried. Live run 5048 exposed
this with two source-matched large clubs hidden behind a retained war-dog
collar; the selector must preserve the collar and free a slot with the clubs.
Runs 5049-5051 validated the repair: the clubs were cleared at healer room
3054, the return-home checkpoint completed, and the subsequent Daycare-ring
maintenance finished safely with Dorrik still wielding his broadsword.

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
For a new `hero` request, generate a random alphanumeric character password and
persist it under the profile credential name before the first connection; keep
it out of profiles, manifests, transcripts, and status output. Bound the
credential write to five seconds on a daemon worker so a keyring prompt cannot
stall the campaign. `--prepare-only` stays secret-free, and resumed work uses
the existing keyring or environment override rather than generating a new
password.
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
From level 10 onward, open the generic source-ranked frontier only after the
registered class-aware routes are unavailable or excluded by current evidence;
never let generic ranking displace an executable registered route.
Live run 4661 validated this fallback for a level-10 mage: Aeloria killed the
Gnome Village treasurer and cook for 529 total XP, then returned to healer room
3054 at full health, mana, and movement.
When a generated multi-target circuit completes with no observed target, mark
every exact primary and supplementary policy saved in that circuit absent; do
not suppress unrelated reset rooms. If that generated absence is on cooldown
and the registered fallback most recently earned less than 50 XP, continue to
an independent generated candidate instead of alternating the two depleted
routes. Runs 4662-4664 exposed this Moria/Gnome oscillation at mage level 10.
Run 4665 validated the repaired rotation by selecting the independent
Fleshmonger kitchen circuit: Aeloria recovered her disarmed weapon, consumed a
verified cure-critical reserve at low health, killed both cooks for 715 XP,
and returned to healer room 3054 safely after the second kill.
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

When an outbound official fastwalk sees a source-ranked target at an
intermediate waypoint, an opportunistic `consider` may collect evidence but
must not replace the official route with that later relative circuit stop. If
the target is below-band, crowded, or otherwise rejected, restore the
pre-intercept stop context, mark the outbound route complete at its actual
endpoint, and only then resume source-ranked stops. Keep this invariant
character-independent; the Moria run 5102 failure and the outbound-intercept
regression capture its need.

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
The streamer cannot infer a user message from the Codex interface. When a user
turn arrives, append that exact turn as `USER` before or with the response;
diagnosing Discord without checking the source file only hides the logging
failure.
Use `python tools/conversation_log.py append --speaker "CODEX COMMENTARY"
--body "..."` or `--body-file <UTF-8 text file>` for new entries whenever possible;
the helper emits the exact header and appends UTF-8 bytes without rewriting
legacy mixed-encoding history. It must reject a body containing another
timestamped speaker header; nested headers split one update into misleading
records. Before restarting or diagnosing the Discord
streamer, run `python tools/conversation_log.py validate`. A malformed
headerish line is a format failure to investigate, not a reason to change the
required header contract. Before every visible progress update, perform this
checklist: create the timestamped header, append the matching log entry, then
send the same header and commentary to the user.
Run the Discord streamer in permanent `--new-only` mode. This is a runtime
no-rewind guarantee, not merely a startup preference: if the conversation file
is truncated, replaced, or rewritten, discard queued and partial records and
checkpoint its new end. Never restart from byte zero or publish historical
records unless the user explicitly requests a one-off replay.
The streamer must keep `allow_historical_replay` set to `false` in its live
configuration, and `run_from_start_once.bat` must remain disabled. Even after
an explicit user request, historical replay requires both temporarily setting
that configuration value to literal `true` and supplying the separate
`--allow-historical-replay` command-line confirmation. Validate that a denied
`--reset-state --from-start` attempt leaves the existing checkpoint unchanged.
Maintain a monotonic local-record timestamp watermark in that mode, set to the
later of the source tail and the actual restart time. Reject the first record
at or before that cutover before queueing; after one live append crosses the
byte cursor, allow additional same-second records because they are still fresh
appends. Also reject a queued record older than the configured 30-second
live-feed age before sending it. These are independent backstops: cursor or
source-checkpoint damage must never become a historical Discord posting burst.
In `--new-only` mode, append position plus the monotonic local-record timestamp
watermark define newness. Seed a separate cutover content set from the source
tail and reject a copied pre-cutover speaker/body pair even when it is
restamped with a fresh timestamp. Apply this content fence only to `CODEX
COMMENTARY` and `CODEX FINAL`; never content-dedupe `USER` turns, because
repeated steering is a legitimate new turn. Include already-delivered Codex
content in the live fence as well, so a previously published assistant body
copied later cannot become a second Discord post. Keep exact-record
fingerprints to prevent the same append from being queued twice or replayed
after a checkpoint. Retry Discord HTTP 429 responses after their rate-limit delay, but
do not retry network failures or HTTP 5xx responses because Discord may have
accepted the request; mark that delivery uncertain and drop it to prefer
at-most-once posting over duplicate commentary. The 2026-08-14 repair verified
29 focused streamer tests, one live worker, an empty queue, and an EOF-matching
checkpoint after cutover. Launch the production worker directly with the
configured `python.exe` in `run_streamer.bat`; do not restore a `py.exe`
launcher/child pair, which makes cleanup and duplicate-worker detection
ambiguous. After any restart, inspect the fresh startup log for `Initial mode:
new records only` and no historical `Publishing` lines before accepting new
traffic.

## Commits And Pull Requests

Use concise imperative commit subjects, for example `Persist character state
snapshots`. Include verification details and behavioral impact in pull
requests. Follow the local commit schedule above and leave remote publishing to
the user. Never stage generated run data, transcripts, secrets, or unrelated
user changes.
