# Autonomy Reassessment: 2026-09-06

Current priorities are consolidated in
[the September 7 approach review](APPROACH_REVIEW_2026-09-07.md).
The chronological findings below remain historical evidence.

## Master Goal

The product goal remains a character-independent runner that accepts any
source-legal race, cosmetic sex, base class, optional subclass, name, and
personality, then creates or resumes that character and plays it to HERO 100.
Direct Telnet and GMCP are the canonical execution boundary. Mudlet and a
Windows VM are visibility and lifecycle validation layers, not a second policy
engine. AI commentary remains downstream of deterministic, replayable policy.

## Astra Findings And Changes

- The HERO entry point had a source-consistency gap: `--source` controlled
  identity validation but the campaign and StarterBot reloaded the repository
  default area directory during runtime. New HERO workspaces now persist the
  resolved area directory in `campaign.yaml` and `hero.json`; the campaign
  runner scopes all source-backed loaders to that directory, and resumes keep
  the original pin. The accepted source forms are `const.c`, its `src`
  directory, the server directory, and the area directory itself.

- The live frontier is Dorrik, a dwarf warrior at level 25, not a static
  level-31 template. After the latest bounded segment he is at checkpoint
  38252 with 380,076 XP, full in healer room 3054. Aeloria
  is level 18 Mage, Praelarran level 20 Warrior, and Kestrel level 24 Thief;
  none has subclass or HERO proof.
- The source audit found a missing Smithy combat boundary: DD4's `hurl` is a
  repeatable between-round weapon action, but only for a worn weapon carrying
  `EGO_ITEM_CHAINED`. The registry now exposes `weaponchain` and `hurl` as
  unestimated setup/combat capabilities; the estimator and starter require a
  matching chained weapon VNUM, and campaign checkpoints preserve it. The
  current DD4 GMCP encoder omits the chained ego bit, so bounded `identify`
  text is retained as the live evidence fallback. Learned hurl proficiency
  alone never enables a command or combat budget.
- The field executor's fixed twelve-action source horizon was too rigid after
  live combat data existed. The damage-window probe now derives a larger,
  bounded action budget from observed damage and the current HP reserve. It
  still enforces the target-to-player damage trade, the explicit healer-return
  floor, and the original source horizon when no measured reserve justifies
  extension. This applies to protected and ordinary fights.
- Campaign reserve accounting now distinguishes a durable field reserve from
  DD4's active affect display. Sanctuary duration `0` means "less than an
  hour"; it remains usable by the live starter until GMCP removes it, but it
  cannot authorize a new outbound route without a positive/indefinite affect,
  trained sanctuary, or a verified carried potion.
- The live evidence pass found a second reconciliation edge: DD4 can split a
  flee-loss message and its partial combat XP across adjacent text lines while
  GMCP has already published the authoritative net XP. The observation layer
  now combines those lines before reduction, so the state reducer records one
  net delta instead of subtracting the full flee loss twice.
- The live ledger confirms the change: runs 12372-12373 recorded sanctuary
  acquisition followed by a 419-XP Ki-Rin loss; 12374 safely stopped an
  expiring-reserve route; 12375 recorded a 340-XP Secretary loss; 12376
  reacquired a purple potion for 100 required-loot XP; and 12377 consumed it
  to kill Mr. Smithy for 1,619 XP and return safely. Run 12378 found the
  known Temple Square drunk hazard and deferred flight without entering the
  shop. Run 12379 reacquired the purple reserve through Moria for 100 XP and
  returned safely. Run 12380 then tested an unprotected Secretary route: DD4
  reported 117 partial combat XP alongside a 419-XP flee loss, for an
  authoritative net of -302 XP; the route is quarantined. Run 12381 repaired
  the durable checkpoint from GMCP and reacquired the purple reserve for 100
  XP. Dorrik was then at checkpoint 38034 with 379,277 XP, full in healer room
  3054.

- Runs 12382-12389 continued the level-25 frontier. The Weeping Willow probe
  dealt only 39 damage in four rounds against a live 740-HP instance and
  withdrew with a 380-XP net loss; the route is quarantined. Sanctuary recovery
  restored the purple reserve, the Ki-Rin probe then withdrew for a 271-XP net
  loss and was quarantined, and the Donjonkeeper route correctly stopped before
  combat when no reserve remained. After one bounded reset wait, run 12389
  reacquired the purple potion for 90 XP and returned safely.
- Run 12390 killed the isolated Solace Secretary for 1,370 kill XP plus 662
  damage XP, 2,032 XP total, and returned to healer room 3054. Run 12391 found
  Mr. Smithy present but rejected the stables because two insect swarms and a
  young girl made the room crowded; no combat or XP change followed.
- Run 12392 exposed a Windows `WinError 121` socket read failure during a
  bounded Mirror Realm research probe. The runner stopped after four bounded
  connection attempts with no XP change. Run 12393 selected the required
  return-home policy, but the MUD then stopped accepting TCP connections on
  port 8888; its finite inactivity retry stopped without changing XP. Dorrik's
  latest durable checkpoint at that point was 38064 at 380,838 XP, last known
  in the Mirror Realm watchtower, alive and full. No level-26, subclass, or
  HERO proof is implied.
- Run 12394 live-validated the new recovery handoff: Dorrik returned from the
  Mirror Realm to healer room 3054 with no XP change. Runs 12395-12396 then
  completed bounded provision and quest maintenance, and run 12397 confirmed
  that the single 180-second reset wait had not been followed by a new DD4
  reboot. The durable campaign is now checkpoint 38072 at 380,838 XP, full in
  healer room 3054, awaiting the next area reset before fresh level-25 route
  selection.

- Runs 12398-12405 continued bounded provision, liquidation, and flight work.
  Runs 12406 and 12411 then exposed two distinct level-25 route failures:
  the Fleshmonger senior-guard route lost 419 XP because its level-15
  `greet_prog` companion can initiate `mpkill`, and the Arachnos Donjonkeeper
  route lost 419 XP when the reachable Guardian interrupted transit. Both
  losses are persisted and quarantined. Candidate construction now treats
  attack programs as non-trivial even below the ordinary XP floor, and applies
  the ten-level transit-risk gate to reachable aggressive wanderers as well as
  fixed-reset route mobs. The ordinary Arachnos candidate is therefore closed;
  the only exception is the separately bounded outdoor mage familiar probe.
- Run 12412 tested the next source-ranked Solace Secretary probe. The source
  route was isolated and free of hard transit hazards, but the live target was
  585 HP and the first bounded exchange produced only 95 damage against 80
  received. The starter withdrew safely, DD4 charged a 324-XP escape loss, and
  the exact policy was quarantined. This validates the live damage-window stop,
  but also shows that a low incoming source peak is not enough to authorize a
  post-loss unprotected probe. Policy revision 197 now requires the source
  player-output budget and expected incoming exchange to cover the target before
  that exception can open.
- A read-only source-catalog audit then found no fresh level-25 warrior target
  that passes both the revised exchange budget and the route-hazard gates. The
  only plain unprotected candidate is the exact quarantined Secretary policy;
  all other current-band options require sanctuary or carry a typed transit
  hazard. This is an intentional reboot/resource boundary, not a stalled
  selector.

- The straight-shifter slice closes a planner/executor mismatch.
  `sft.c:do_morph_snake` creates and equips source object VNUM 59 (fangs), but
  the source-ranked output path previously discarded the stale carried weapon
  after morph and then had no source weapon to budget. It now accepts VNUM 59
  when the live form is snake, or projects it from a normal checkpoint only
  when the starter's morph, 20% snake-form, and source mana gates are met. The
  shared capability registry reports `morph` and `snake form` as setup rather
  than direct-damage actions. This is source-backed planning coverage, not live
  shifter progression proof; damage calibration and later form selection remain
  separate gates.
- The route-risk audit found that the emergency no-sanctuary fallback was
  treating every source-aggressive transit mobile as equally dangerous. The
  selector now admits only a source-proven mobile at least ten levels below the
  character, with no attack program and only a typed non-combat special such as
  `spec_fido`; near-band, programmed, unsafe-special, and unknown-source cases
  still fail closed. Focused campaign coverage passes. This is a local safety
  classification repair and has not been live-validated or counted as level-26
  evidence.

- Policy revision 199 makes the probabilistic-program case explicit rather
  than treating it as either harmless or permanently fatal. A single
  far-below-band program attacker is admitted only with source-matched
  `where` metadata from recall, a complete source room map, and the existing
  one-loss protection fallback. The StarterBot checks the locator before
  crossing; a located mobile causes a healer return, and an absent or
  inconclusive response never authorizes crossing. Deterministic, multiple,
  near-band, unsafe-special, and malformed program routes remain blocked. The
focused campaign and candidate tests cover both admission and rejection.

## Post-Reassessment Continuation (2026-09-07)

Before opening Serevian's level-11 frontier, runs 12417-12419 exposed a
campaign liveness defect. The thief had four durable class-priority deficits,
but `Char.Worth.practice` was exactly zero. The starter correctly audited the
balance and exited without spending anything; campaign startup then reopened
the no-op trainer marker and repeated the same city segment. Policy revision
201 now treats an exact zero practice balance as a same-level/reboot deferral,
while retaining the deficit for a later level or positive practice award.
Missing practice data remains unknown, so it does not weaken the existing
trainer-listing evidence rule. The focused regression covers both deferral and
reopening, and the next live segment is Serevian's source-ranked frontier at
checkpoint 38139, not another trainer-only retry.

The first continuation after this review ended safely at Dorrik checkpoint
38118, still level 25 at 380,076 XP in healer room 3054. A bounded Mirror
Realm watchman probe and a sanctuary-recovery pass both recorded no XP change;
the world reboot marker remained `Fri Sep 4 06:19:51 2026`. The source-ranked
level-25 audit currently exposes one autonomous-safe warrior candidate, Mr.
Smithy, but its route includes the low-level probabilistic drunk program and
the source-backed fido special. The other near-band candidates are blocked by
armed targets, special procedures, crowds, or transit hazards. That confirms
the current stop is an evidence-backed frontier boundary rather than a dead
worker.

The named workspace inventory is: Aeloria level 18 Mage, Kestrel level 24
Thief, Praelarran level 20 Warrior, Serevian level 11 Thief, Velnor level 6
Cleric, and Brannor level 3 Warrior. They remain safe durable tracks, but none
has subclass or HERO proof. The next operating change is observable matrix
rotation: `matrix --progress` now prefixes each bounded campaign attempt with
its character id and forwards the underlying attempt/checkpoint messages to
stderr. This keeps the rotation auditable without weakening the per-character
safety gates or treating a checkpoint as progression proof.

## Astra Policy-200 Validation (2026-09-07)

The first Astra policy slice was too narrow for a campaign that had already
recorded two losses on its protection-recovery route: a fresh low-band route
with one source-identified probabilistic attacker could still be safe when its
source damage peak, live HP budget, and route preflight all fit. Revision 200
adds exactly one such independent fallback after a second current-reboot loss.
It requires the exact source VNUM and `where` preflight from recall, a fresh
policy with no prior XP-loss record, the existing 80%-of-maximum-HP peak bound,
and the audited +2 source-fuzz window. Selection persists a one-use marker, so
the exception cannot become a reconnect or multi-segment retry loop. Crowd,
live-consider, damage-window, resource, and healer-return gates remain
authoritative.

Offline verification now passes 3,657 tests. Live validation correctly found
that this particular reboot does not yet satisfy the exception: Mr. Smithy had
two current-reboot crowd findings from the poison swarm, while the Weeping
Willow and Secretary carried separate live damage-window loss evidence. The
selector returned `source-ranked-hunt-unavailable-25` without combat. The
single reset-aware continuation then rechecked Moria (run 12416), found the
sanctuary carrier absent, and returned Dorrik safely to healer room 3054 with
380,076 XP at checkpoint 38131. This is a durable, bounded frontier stop, not
HERO evidence and not a reason to bypass the current crowd or loss ledger.

## Astra Policy-202 Validation (2026-09-07)

Runs 12440-12442 exposed a second liveness gap in the level-11 thief
frontier. Serevian withdrew from Fleshmonger at the health floor with a
negative net XP delta, but the registered research result did not persist the
route loss, so startup could later treat the route as fresh. Policy revision
202 adds a durable current-reboot ledger for negative, pre-objective-kill
results from research or verified routes. Startup reconstructs it from the
complete campaign history, including legacy segments whose checkpoints omitted
the result payload. A later positive objective kill clears the same route's
current-boot loss record, preserving the useful earlier Fleshmonger kill and
avoiding a permanent quarantine after one bad exchange.

The repair reconstructed exactly one current-boot loss for
`fleshmonger-thief-rotation-11-12`, tied to the latest withdrawal, while
retaining the earlier positive kill as productive evidence. Selection now
rotates away from that freshest loss without weakening live consider, crowd,
damage-window, resource, or healer-return gates. Focused campaign tests and
the full offline suite now pass 3,658 tests. This is liveness and evidence
hygiene, not level-12, subclass, or HERO proof.

## Astra Policy-202 Resource Classifier Follow-Up (2026-09-07)

The first live sanctuary retry after Policy 202 exposed a classification bug:
the fixed-route ledger recognized `source-ranked-hunt-*` but not the
source-ranked sanctuary, food, and cure-critical resource policy ids. Run
12448 reached the source-identified Moria orc at room 2785 during sanctuary
recovery, withdrew with a 99-XP loss, and returned safely to healer room 3054.
The repair now classifies those resource routes as source-ranked evidence,
reconstructs their durable attempt state, and removes the stale registered
loss record during startup repair. The current reboot therefore remains on
the existing sanctuary cooldown; it is not retried as a fixed research route.

Focused classifier tests pass 5 tests and the full offline suite passes 3,660
tests. This closes an evidence-accounting blocker, not a progression gate:
Serevian remains level 11 at checkpoint 38237 with 50,711 XP, and Dorrik
remains level 25 at checkpoint 38239 with 380,076 XP. No level-12, level-26,
subclass, or HERO proof is implied.

## Astra Source Refresh (2026-09-07)

The read-only DD4 mirror advanced cleanly to
`900c61592875771c701beaf70e4e83654d029d66` after the prior source audit. The
server now resolves mobile body species and creature archetypes from
`server/src/mob.c`, applying XOR inheritance before the individual area-file
override. The Python source catalog now reads that table and the relevant flag
definitions from `merc.h`, preserves `template_name`, species, area-local
masks, and effective flags on `MobileSource`, and exposes the archetype XP
modifier for later reward estimation. Unknown or malformed templates remain
unresolved instead of being guessed. Three focused template regressions and
the full 3,660-test suite pass; no live progression claim changed.

The same review found that source-revision synchronization previously occurred
only after source-ranked candidate selection. A protection or maintenance stop
could therefore leave a durable checkpoint pointing at an older source commit,
even though the next decision would read the refreshed mirror. Campaign resume
now persists a distinct `source_revision_refreshed` checkpoint before policy
selection and applies the existing source-evidence invalidation at that point;
candidate selection retains its defensive repeat check. The focused campaign
regression covers the no-candidate boundary. This improves auditability and
liveness but is not progression proof.

## Astra Fallback Handoff Repair (2026-09-07)

The policy-202 second-loss exception already admits one fresh,
source-preflighted route in a narrow +2 source-fuzz window. The campaign-level
fallback collector was still applying only the ordinary current-band gate, so
it could discard a valid level-ceiling probe before the nested selector saw it.
The collector now accepts that exact level-ceiling shape through the existing
movement and below-band evidence gates. Crowd exhaustion, live `consider`,
damage-window, resource, and healer-return evidence remain authoritative.

The focused fallback coverage passes, and the full offline suite now passes
3,669 tests. The latest Dorrik continuation is checkpoint 38252: run 12449
reached the Moria sanctuary endpoint, found the carrier absent, and returned
safely without XP change; the next bounded attempt selected
`source-ranked-hunt-unavailable-25` and also made no progression claim. No
level-26, subclass, or HERO proof is implied.

## Matrix Coverage Liveness Repair (2026-09-07)

The Astra reassessment exposed a separate operational stall. `matrix-coverage`
opened the shared 25 GB SQLite ledger once for each entry, loaded every
checkpoint, and then walked every event in every campaign segment to answer two
existence questions. Praelarran's 1,957-segment campaign made that path exceed
the bounded smoke window. Coverage now reuses one `RunStorage` connection per
database, queries only the newest accepted target checkpoint in SQL, and limits
creation evidence to `starter:<name>` runs, the durable naming contract of
`StarterBotRunner`. The five-entry active HERO rotation completes in about two
seconds locally. The strict distinction remains: coverage output inventories
durable evidence and does not claim creation-to-HERO progression.

The matrix regression suite and storage suite pass after this change; the full
offline suite remains the required final verification before the next live
level-25/26 attempt.

## Astra Guardian Route Dispatch (2026-09-07)

The next-band audit found that the level-26 Mirror Realm guardian was still
the first named route whose campaign boundary used a hand-authored target and
room constant. The area source has one guardian reset in room 19041 and two
additional resets in room 19031. Revision 203 now builds both the research
probe and the bounded hunt through `_source_registered_hunt_stops`, retaining
those placements as separate source routes. The probe records presence,
crowd, isolation, and `consider` without initiating combat. The hunt repeats
`consider`, requires 85% health, a +1 source-level ceiling, exact isolation,
and one confirmed kill. Focused guardian dispatch tests and the campaign/CLI
regression pass; the live Dorrik checkpoint remains level 25 at 380,076 XP, so
no level-26, subclass, or HERO proof is claimed.

## Astra City-Route Recovery (2026-09-07)

The first fresh public-HERO creation track, Astrevo (human female mage),
reached level 5 at checkpoint 38315 with 10,069 XP after automatic credential
storage, generated title/personality persistence, Mud School progression, and
healer recovery. Runs 12469-12470 exposed a real interruption boundary: a
wanderer stopped the leather-shop route, flee/recall returned the character to
room 3001, and the old fixed cursor then arrived at Cleric's Bar (3003).

Revision 204 makes the route cursor authoritative-room driven for outfit and
weapon errands, and narrows the campaign's completed healer checkpoint to room
3054. A non-healer Midgaard checkpoint now selects `return-home` before any
new maintenance or field policy. The repaired resume returned from room 3003,
completed daycare maintenance, and continued arena progression to checkpoint
38386 at level 6 and 15,075 XP. Runs 12506-12519 then crossed the level-6
boundary, completed the level-6 outfit and daycare handoff, killed a
source-ranked wild boar for 206 XP, and safely closed the wolf, quest-frontier,
and world-time probes. Runs 12520-12521 added two bounded world-time
checkpoints without a new reboot marker. Focused route/campaign tests pass;
this is resumability and early-band creation evidence, not subclass or HERO
proof.

## Astra Live Continuation (2026-09-07)

The advanced-model reassessment keeps the fresh creation track as the primary
proof path: continue Astrevo from the durable healer checkpoint, let the
source-ranked selector choose level-8 and later targets, and treat reset,
research, and route hazards as evidence rather than manual steering prompts.
The first post-level-6 rotation produced a 206-XP wild-boar kill after the
arena reset, while wolf and quest-frontier probes stopped safely under their
existing gates. Two bounded world-time probes found no new reboot marker, so
the campaign initially stopped at checkpoint 38420 at an explicit area-reset boundary
instead of spinning a retry loop. Runs 12527-12528 then live-validated the
revision-205 route-program preflight: the Bearded Lady endpoint was crowded,
while the Midget route passed an absent drunk lookup but found no target. Both
returned safely without XP change or loss. Runs 12529-12531 rotated to the
Sword Swallower, Ultima bat, and little Bobby; the first was crowded and the
  latter routes stopped when the drunk was at recall. Run 12533 then selected the
  school route, killed two wild boars for 354 XP, and returned safely to healer
  room 3054 at checkpoint 38425 with 15,429 XP. Runs 12534-12551 exercised
  bounded maintenance, reset waiting, and target rotation without unsafe retrying.
  Run 12552 live-validated revision 207 by killing a source-ranked wild boar for
  246 XP and returning safely at checkpoint 38466 with 17,389 XP. Runs 12553-
  12600 then rotated through level-7 Moria, Circus, Ultima, school, equipment,
  and flight policies. A crowded bat withdrawal cost 58 XP and remains
  quarantined; later school rotations added net progress. Run 12600 returned
  safely at checkpoint 38614 with 22,754 XP after another safe level-7
  rotation. The next school rotation crossed level 8, and the outfit handoff
  completed safely at checkpoint 38661 with 25,030 XP. The next executable
  slice is Astrevo level 8 to 9, then the live level-10 trainer and subclass-capability
  gate.
Dorrik's level-25 continuation
remains a parallel higher-band frontier; neither path implies HERO proof.

## Policy 206: bounded transient route rechecks

The revision-205 live evidence exposed a liveness boundary rather than a
combat-safety defect: a source-valid Circus route could be abandoned merely
because the wandering drunk happened to occupy a route room on the first
preflight. Revision 206 retains the exact source-matched locator and all
existing route, consider, crowd, resource, and healer-return gates. For a
source-proven probabilistic route program only, the runner now recalls to healer
room 3054, sleeps for up to three 12-second intervals, and retries the lookup.
A clear lookup restarts the route from recall. Hard hazards, ambiguous output,
and an exhausted retry budget still produce a safe bounded stop. The deadline
is visible to the inactivity watchdog and the retry count is persisted in run
state. This removes a concrete early-band liveness blocker without converting
research or preflight evidence into progression or HERO proof.

## Policy 207: multi-kill reward accounting

The live Astrevo frontier exposed a separate liveness problem after revision
206: the school route earned useful two-kill segments, but a per-kill ceiling
below the configured meaningful-XP floor eventually classified the route as
low reward and left only crowded or absent alternatives. Revision 207 treats a
confirmed segment that clears that floor and has at least two objective kills
as productive repeat evidence. A lone 10-XP kill remains low reward, and all live consider,
crowd, route, damage-window, resource, and healer-return gates remain in force.
The change is selector liveness evidence, not level-8 or HERO proof.

## Next Executable Slice

The zero-practice repair is live-validated on Serevian. Runs 12420-12426
rotated through finite funding, the cult research stop, Circus Ivan for 175
XP, liquidation, and flight maintenance; checkpoint 38157 is level 11 at
50,163 XP in healer room 3054. The next Serevian proof gate is level 12. This
does not replace Dorrik's separate level-25 frontier or imply HERO progress.
Runs 12427-12433 then filled basic gear, recorded an 11-XP net loss at the
Fleshmonger health floor, rejected the hazardous Moria sanctuary endpoint,
and killed Circus Ivan for 240 XP. The current Serevian checkpoint is 38182 at
50,392 XP in healer room 3054. The Fleshmonger loss remains evidence for route
selection and is not silently retried.
Runs 12437-12439 then refreshed equipment and completed a bounded Cult absence
recheck without a kill. Runs 12440-12442 recorded the current Fleshmonger
withdrawal and rebuilt its registered-route loss ledger. Run 12443 completed
the bounded flight-loan handoff. Run 12444 bought the reboot-local 131-copper
light-blue potion, observed flight, and returned safely without XP change.
Run 12445 tested the Gnome small troll, dealt 97 partial XP, paid a 99-XP
flee loss, and quarantined that source route. Runs 12446-12447 rejected
Granny Jenkins and the Circus child-father target via live `consider`. Run
12448 reached the source-identified Moria orc during sanctuary recovery, lost
99 XP, and returned safely. Startup repair removed that resource loss from the
fixed-route ledger. Run 12449 then completed a bounded resume without combat,
leaving Serevian checkpointed at 38237 with 50,711 XP in healer room 3054; the
current reboot has no executable sanctuary route.

Continue level-25 progression from healer room 3054 after the current reboot
or a newly verified sanctuary/resource route. Do not immediately replay the
freshly failed Fleshmonger
companion route, ordinary Arachnos transit, the Secretary damage-window loss,
the Weeping Willow loss, or Mr. Smithy's crowded endpoint. Let the selector
use the policy-200 exception only when its exact fresh route evidence is
present; otherwise wait at the healer through the bounded reset controller.
Use the same bounded segment, cleanup, and evidence reconciliation for every
attempt. The next proof gates are Serevian level 12 and Dorrik level 26,
followed by each class's trainer/subclass path;
no policy selection, research result, or checkpoint implies subclass or HERO
progression.

## Verification

The source mirror remains at `900c61592875771c701beaf70e4e83654d029d66`.
The full offline suite passes 3,698 tests; `compileall` passes and changed
files pass `git diff --check` when the intentionally append-only conversation
log is excluded. The latest live evidence is in campaign 32: run 12686 stopped
safely after bounded route preflights, and run 12687 reproduced the fixed-route
gap before returning Astrevo to healer room 3054 at checkpoint 38861 with
26,671 XP. Campaign 28 remains safely checkpointed after run 12681's 549-XP
Guardian kill and run 12682's crowded Shadow Keep stop. Aeloria remains level
18 at 160,952 XP, while Astrevo remains the primary fresh-creation continuation
at level 8. No level-9, level-19, subclass, or HERO proof is claimed.
Dorrik remains level 25 at 380,076 XP in healer room 3054. Remote pushes remain manual, and the repository's local
commit window is 9 PM with a 60-second timeout.

## Astra Policy-205 Route Preflight Liveness (2026-09-07)

The advanced-model reassessment found a concrete early-band liveness gap. The
source catalog identified Circus routes whose only route-program hazard was a
low-level probabilistic drunk; `StarterBot` already had the exact `where`
preflight and safe recall behavior, but the campaign selector admitted that
shape only during a narrow protection-recovery fallback. At level 6 this made
otherwise safe candidates disappear from ordinary progression.

Policy revision 205 adds a dedicated `route_program_preflight` pool for the
normal source-ranked selector. It requires one source-identified probabilistic
program, an exact source-matched locator from recall, no armed or special
target, no unsafe route special, and a source-fuzzed route level at least two
levels below the character. The live starter continues only after an explicit
absent locator and returns for a located or ambiguous result. Focused campaign
tests pass 1,203 tests after the change, and the full suite passes 3,669. Runs
12527-12528 live-validated the gate without XP change, death, or loss. This is
a liveness repair and not level-up or HERO proof.

## Astra Target Horizon Repair (2026-09-07)

The reassessment found one configuration mismatch with the master objective:
campaign 32's fresh Astrevo workspace was still capped at level 10 even though
the public HERO entry point and its manifest were already HERO-oriented. The
campaign now names the full target explicitly with `target_level: 100`, without
altering the existing credential, character profile, or checkpoint history.
The active HERO rotation includes Astrevo as a sixth resumable workspace, and
the matrix regression locks that roster change in place.

Live continuation then resumed from healer room 3054. The source-ranked gnome
hermit segment completed at checkpoint 38721 with +81 XP, leaving Astrevo at
level 8 and 26,234 XP. The earlier Ambush loss and the bounded stall recovery
remain durable evidence; neither the early-band checkpoint nor the new horizon
is progression proof for level 9, subclass, or HERO.

This is the correct operating shape for the master goal: one declarative
character profile, one durable campaign horizon, source-ranked live selection,
and bounded segments that can stop and resume without silently downgrading the
requested target.

## Astra Policy-208 Route Retry Handoff (2026-09-07)

The first retry implementation stopped one layer too early. The StarterPolicy
already had the bounded healer-side retry for a transient probabilistic route
program, but campaign result classification treated the exact
`field route preflight found source-registered hazard` result as a permanent
cooldown. Policy 208 keeps ordinary absence, crowd, static route hazards, and
malformed or deterministic programs closed, while allowing only an otherwise
source-approved single-program candidate to use the explicit retry path.

Focused regressions and the full 3,672-test suite pass. Runs 12653-12654 then
live-validated the repair: Astrevo reached the Bearded Lady twice, killed her
for 151 XP and 126 XP, acquired the hairy key, and returned safely to healer
room 3054. Runs 12655-12656 recorded safe absent-target rotation for the
Bearded Lady and Midget. The current checkpoint is 38751 at 26,616 XP. This
is fresh level-8 route evidence, not level-9, subclass, or HERO proof.

## Astra Policy-209 Evidence Ordering (2026-09-07)

The advanced-model reassessment found that policy 208 still left one liveness
gap. A later below-band observation for mobile 3713 was hiding exact school
resets even though their own same-level, same-reboot results had already
recorded meaningful confirmed kills. The shared funding-band gate applied the
same exclusion, so safe rotation could fall through to an unavailable
checkpoint.

Policy 209 centralizes the meaningful exact-result check and applies it to both
candidate exclusion and the funding gate. Only the exact source-ranked reset
with current-reboot productive evidence reopens; sibling resets, stale or
low-reward results, losses, crowds, and unproven capacity remain closed. A
productive capacity route also competes before fresh research, while unknown
capacity stays research-only.

The focused regressions and full 3,675-test suite pass. Runs 12660 and 12661
live-validated the repair: room 3736 returned safely with 90 XP, then room
3729 returned safely with 101 XP. Astrevo was then level 8 at 26,807 XP in
healer room 3054, checkpoint 38767. Runs 12662-12665 then recorded fresh
below-band and route-hazard boundaries without XP loss, and the next selector
reached the explicit crowded-route reset boundary at checkpoint 38780. This
is fresh early-band evidence, not level-9, subclass, or HERO proof.

## Astra Policy-210 Route-Program Admission (2026-09-07)

The reassessment found that policy 209 still classified a level-2 probabilistic
drunk as a useful-band rejection for a level-8 character because source fuzzing
raised its upper bound to level 4. That classification prevented the existing
exact `where drunk` preflight from protecting otherwise viable Moria, Circus,
and Ultima routes.

Policy 210 admits a probabilistic, non-aggressive route program when its
source-fuzzed upper level is at least two levels below the character. The exact
source-matched locator remains mandatory before departure, and all live
consider, crowd, health, damage-window, resource, and healer-return gates stay
in force. Deterministic, aggressive, near-band, malformed, armed, and
unsafe-special hazards remain closed. Focused route and campaign regressions
pass. Run 12667 then completed a fresh source-ranked route with a live
below-band `consider`, no XP change, and no loss; the campaign is safely
checkpointed at 38848 with Astrevo at level 8 and 26,807 XP. Run 12683 then
recorded a safe crowded school stop without changing XP. Runs 12668-12670
then cleared the quest safety pair and completed one bounded reset-aware retry;
no reboot was observed and no XP changed. This is a liveness repair and honest
early-band evidence, not level-9, subclass, or HERO proof.

## Astra Policy-211 Bounded Transit Aggression (2026-09-07)

The current Aeloria level-18 checkpoint exposed a real liveness bottleneck:
the source catalog rejected every otherwise useful route because Miden'nir
goblins sit inside the blanket ten-level transit-risk band. Policy 211 makes
that admission evidence-based. It accepts only a below-useful-band, unarmed
aggressor with no attack program or unsafe special whose source peak and
critical damage are at most 40% and 20% of live character HP. Campaign
selection and StarterPolicy share the rule; exact identity, isolation, live
consider, resource, and healer-return gates remain authoritative. Focused
regressions pass, but a new live completion is still required before this is
progression evidence.

The bounded live check then reached Aeloria checkpoint 38808 at level 18 and
159,938 XP, full in healer room 3054, without opening combat or changing XP.
The catalog exposed four candidates after the policy change, while the
campaign-level sanctuary and damage-window gates correctly held because no
executable protection reserve was available. The next executable boundary is
therefore reserve acquisition or a fresh reboot, not a speculative retry of the
same protected route.

## Astra Policy-212 Familiar Transit Guard (2026-09-07)

The first familiar-backed armed-endpoint change exposed an interaction defect:
the endpoint proof was being allowed even when the route itself could carry an
armed aggressive wanderer. The repair requires all source-identified route
aggressors to pass the existing bounded, unarmed transit test before familiar
admission. This preserves the useful Bardoosh-shaped experiment while closing
the Eastern Desert counterexample.

Runs 12674-12678 left Aeloria safely at the healer after a 697-XP Undead
Soldier kill, a safe Bardoosh no-match consider, liquidation, and flight
maintenance. Run 12679 then reached the nomad route, where source mobile 5011
the drider interrupted while armed and caused a 232-XP flee loss. That route is
now quarantined for the reboot. The latest checkpoint is 38827, level 18,
160,403 XP, full in healer room 3054. This is safety evidence, not level-19,
subclass, or HERO proof.

The next live validation confirmed the repair rather than hiding behind the
offline suite: run 12680 safely stopped on a crowded Shadow Keep circuit, run
12681 completed the Arachnos guardian route for 549 XP, and run 12682 safely
stopped on another crowded Shadow Keep circuit. Aeloria is now checkpoint
38841 at level 18 with 160,952 XP, full in healer room 3054. The Eastern Desert
armed-wanderer loss remains quarantined evidence; the familiar transit guard
is live-validated, but no level-19, subclass, or HERO proof is claimed.

## Astra Policy-214 Cross-Area Program Guard (2026-09-07)

Run 12684 rotated Astrevo to the Circus Illusionist and stopped on a live crowd
without losing XP. The following Midget attempt exposed a flaw in the
route-program contract: `where drunk` returned no Midgaard match, but four
moves later the drunk was in Wall Road after the route crossed into Dangerous
Neighborhood. Source inspection confirmed that `do_where` filters by the
caller's current area. The immediate flee cost 68 XP; run 12685 nevertheless
recovered Astrevo fully in healer room 3054 at checkpoint 38856.

Policy 214 retains the exact source-matched origin locator but no longer treats
it as global proof. Every generated route using the probabilistic-program
exception carries the program mobile's complete source-reachable room set.
Before entering a matching adjacent GMCP destination, the executor performs a
directional `scan`; a visible match, blindness, missing destination, or empty
response causes a safe return and bounded cooldown. The parser now accepts
punctuated mobile identities. Focused regressions cover source graph creation,
the outbound scan, safe clear, comma-bearing match, retry reset, and durable
cooldown aging. The complete suite passes 3,686 tests. This closes the observed
safety gap but does not prove level 9, subclass selection, or HERO progression.

## Astra Throughput Reassessment And Policy 215 (2026-09-07)

The campaign ledger shows that the dominant blocker is now work granularity,
not missing future-band declarations. Praelarran used 1,958 segments to reach
level 20; 1,157 produced no XP. Astrevo's source-ranked hunts have yielded
about 95 XP per elapsed minute, versus about 281 XP per minute in the compact
Mud School loop. Maintenance is even more connection-heavy: 314 of
Praelarran's 329 maintenance segments produced no XP. These figures include
travel and recovery and therefore describe the operator-visible system, not
only combat speed.

The revised priority is to raise productive XP per connection at the live
frontier before extending speculative level-31-plus graphs. Policy 215 removes
one false global veto from the existing area-circuit planner. A program mobile
is bounded transit only when the current source proves one low-chance
`greet_prog`, no aggression flag, weapon, unsafe special, fame cost, or combat
prohibition, at most three reset instances, a source-fuzzed level at least four
below the character, a source HP ceiling no greater than character HP, and
strict peak/critical damage ratios. Live identity, isolation, crowd, consider,
health, resource, and return gates still govern the encounter. The resulting
graph can combine up to three source-safe same-area targets in one trip.

Focused tests prove both the classifier's rejection boundaries and a complete
two-target synthetic circuit. The change is a throughput mechanism, not a
claim that any live character advanced a level.

## Astra Fixed-Route Audit And Policy 216 (2026-09-07)

Run 12686 safely exhausted three live preflight checks for the source-ranked
Bearded Lady route without changing XP. Run 12687 then selected the older
fixed Moria sanctuary route, which had none of the generated source-route
metadata. The level-3 drunk attacked on Main Street beside a source-reachable
level-13-to-17 cityguard. Fighting was not safely isolated, so the bot correctly
fled, paid 68 XP, and returned Astrevo full to healer room 3054 at checkpoint
38861 with 26,671 XP.

Policy 216 repairs the abstraction boundary centrally. Before dispatch, every
source-resolvable fixed fastwalk is replayed through the current room graph and
checked for reachable non-objective attack-program mobiles. One exact mobile
inherits the locator, route-room names, and complete adjacent-scan set;
multiple unrepresented mobiles block departure at the route origin. Existing
hand-authored preflights are preserved, while generated routes mark their own
audit complete so policy 215 is not reversed. The actual Moria source map now
derives `where drunk`, four normalized route labels, and all 59 reachable scan
rooms without a route-name or character-name special case.

Compilation and all 3,698 offline tests passed at this boundary. Run 12688 then
completed safely but exposed a separate selector/executor mismatch: the
ordinary protection fallback was selected precisely because no sanctuary
reserve was executable, yet its generated hunt stop required sanctuary again
and aborted before combat. Astrevo returned full at checkpoint 38864 without
an XP change.

## Astra Fallback Alignment And Policy 217 (2026-09-07)

Policy 217 carries the selector's deliberate no-sanctuary decision into hunt-
stop construction. The fallback still requires the source-bounded target, 95%
departure health, exact live isolation and consideration, and a mandatory
damage-window probe. It simply no longer requires the unavailable reserve that
caused this one-probe escape path to exist.

Startup migration re-arms only a revision-216 fallback whose terminal reason
was the pre-combat missing-sanctuary abort. It clears the matching exhausted
marker and stale research annotation, but refuses to reopen a real exchange,
XP loss, death, or objective kill. Run 12689 validated startup continuation: Astrevo
killed the level-6 Bearded Lady for 159 XP, recovered her key, and returned at
full health, mana, and movement to healer room 3054. This was an ordinary hunt,
not live validation of the specific Ivan no-sanctuary fallback. Campaign 32 was
checkpoint 38867 at level 8 with 26,830 XP. Compilation and all 3,700 offline
tests pass; no level-9, subclass, or HERO proof is claimed.

## Astra Fallback Lifetime And Policy 218 (2026-09-07)

The checkpoint audit after run 12689 found a second-order state bug. The
productive Bearded Lady kill correctly cleared the underlying protection
requirement, but the fallback marker still named Ivan because the selected
fallback and eventual successful target differed. Left alone, that orphan
could have disabled Ivan's ordinary sanctuary requirement later.

Policy 218 enforces the relationship at three boundaries: productive merge
clears a same-reboot fallback when it clears protection recovery, startup
migrates an orphaned legacy marker, and field construction refuses to honor a
fallback unless its parent protection marker still matches the reboot and
level. Run 12690 live-validated the result by killing the Bearded Lady for 167
XP and returning full to healer room 3054. Checkpoint 38871 is policy revision
218, Astrevo is level 8 at 26,997 XP, and neither protection marker is present.
Compilation and all 3,703 offline tests pass.
