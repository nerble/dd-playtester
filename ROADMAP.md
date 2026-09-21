# Autonomous Playtesting Roadmap

## Master Objective

Given only a source-legal race, cosmetic sex, base class, optional subclass,
name/personality, and credentials when resuming, create or resume a character
and autonomously reach the requested level, up to HERO 100. Preserve progress,
explain the experience, and support direct Telnet and visible Mudlet operation.

**Not complete:** no HERO character is proved. Highest actual frontier is 25;
the fresh-creation track is 9. The active goal remains this master objective.
The [September 8 review](docs/APPROACH_REVIEW_2026-09-08.md) is the current work
order; dated run evidence belongs there, not in an expanding policy changelog.

The ordinary fame gate is now recorded precisely: `fight.c` uses
`victim.level - player.level > 5`, which means at least six levels higher. The
source-famous `ACT_IS_FAMOUS` branch is separate. The +9 value shown by the
readiness report is a diagnostic horizon, not a game ceiling; live fame
selection searches the source range through HERO before applying its safety
gates. Kestrel's latest bounded
Green Dragon attempts (runs **13407-13408**) did not recover fame: one stopped
on the live HP/output gate, and the sanctuary-protected retry encountered gas,
with a recorded **385 XP** loss before safe healer recovery. Run **13409** then
replenished one purple sanctuary reserve through the bounded Moria route; this
added 100 maintenance XP and did not change fame or progression level.

### Funding loss gate: September 21, 2026

Run **13691** took Dorrik (level 25) to the source-ranked Highlander funding
target. The live `consider` was viable and sanctuary was used, but a critical
hit forced a bounded withdrawal at 257/569 HP; DD4 charged **419 XP** and fame
remained **0**. The persisted loss ledger now excludes that candidate for the
current reboot, and the next policy check finds no safe replacement funding
route. This was a provision-funding attempt, not fame recovery: an ordinary
fame target for Dorrik would need to be level **31 or higher**.

### Bounded sale-buyer retry: September 21, 2026

Run **13693** completed the source-backed Moria large-orc funding attempt for
Dorrik, yielding **50 maintenance XP**, one yellow-and-green ring, and one
copper from the sacrificed corpse. The follow-up sale run **13694** recorded
the ring refused by the Leather Shop, then tried the other safe armour buyer
once; the Armoury also refused it, so the ring was donated and the balance
remained **4 silver, 8 copper**. DD4 uses the same uninterested text for several
shop-side causes, so the runner now preserves the refusal, excludes tried
shops, and permits exactly one alternate compatible buyer before donation. This
is funding evidence only; no progression XP or fame is claimed.

### Protection-aware funding rotation: September 21, 2026

The campaign now recognizes a current-reboot absent flight-funding attempt even
when reset repair has exposed an older reusable carrier. From a fed healer
checkpoint with protection recovery still required and the sanctuary budget
terminal, it makes one source-output-gated ordinary current-band selection
instead of repeating either funding target. Existing route, movement,
sanctuary, consider, live-identity, and finite-action gates remain in force;
an empty ordinary frontier becomes a no-socket checkpoint. The regression
models Dorrik's Midget/Moria mismatch and passes with the focused campaign
tests; compilation is clean.

Runs **13699-13701** then produced bounded live evidence: 60 maintenance XP
from the large orc, a clean absent-Midget retry, and a same-reboot `time`
probe. The following policy selection correctly found no admissible ground
progression target and opened no gameplay socket. Dorrik remains level 25 at
**382,940 XP**, with sanctuary reacquisition or a stronger source-safe combat
envelope still required. HERO 100 remains unproved.

Aeloria's run **13703** separately completed the source-ranked Haon food reserve
and returned safely to healer room **3054** at checkpoint **42595**. It added no
XP; the next level-18 lemming-smithy candidate is below-band with a hard route
preflight, so it remains research-only rather than a weak XP expedition.

### Multi-character continuation and key-route audit: September 21, 2026

Aeloria's level-18 mage repair reopened the local trainer and the server
accepted two `evocation magiks` practices, moving 49% to 58% with no Mage's
Laboratory sleep. The subsequent familiar-backed Arachnos guardian attempt
lost the familiar and withdrew after DD4 deducted 232 XP (net checkpoint
change -152); the exact retry is now closed for this reboot. A bounded lemming
smithy probe found the endpoint empty and recorded a three-segment absence
cooldown. Kestrel completed a safe level-24 grain reserve route, but fame
remains -12 and no ordinary +6 target passed admission. Dorrik's tree-sprite
and Abyss routes both returned safely without XP, leaving the level-25
frontier unavailable rather than replaying stale targets.

The source resource audit now distinguishes a locked route from an acquisition
plan. The level-18 sanctuary flask (object 2008) on grand templar 2015 in
room 2025 is reached through key 6502; its source carriers are dwarven guard
6500 and wraith 6502. Raw reset provenance now keeps the key attached only to
the keyed guard reset in rooms 6505 and 6540; adjacent same-mobile guard
resets do not inherit it, and the wraith remains a separate mobile category.
The key route is retained as source evidence, but its carrier
level/capacity/output gates fail for Aeloria, so no live sanctuary permission
is inferred. A route key whose source resets are all beyond the
recall-reachable graph is now labelled as a circular acquisition dependency.

### Reset-boundary funding handoff: September 21, 2026

Run **13702** supplied live counterevidence to the first protection-aware
funding regression: automatic reset repair removed Dorrik's current-boot
absent-Midget marker, and policy selection reopened the same empty carrier.
The repair now preserves that marker only for the exact combination of pending
flight funding, current protection recovery, and terminal sanctuary attempts.
It still clears the transient attempt list and leaves the ordinary
source-output-gated fallback in charge. The new boundary test and the full
campaign suite pass **1,608 tests**. Bounded run **13704** found no new reboot
and therefore did not exercise a live reset wait; the reset handoff remains
unit-proved and awaits fresh area-reset or reboot evidence.

### Automatic frontier liveness probe: September 21, 2026

An unavailable policy at a healthy healer checkpoint now opens one bounded
`world-time-probe` automatically, even in a one-segment invocation. The probe
records DD4's authoritative `time` reboot marker, saves, and quits; it does not
hunt, clear cooldowns, or claim XP. A durable probe checkpoint prevents repeat
connections on the same frontier, while the existing reset-aware retry remains
the only path that can probe again after a real area-reset wait. Live run
**13646** validated this with Aeloria: the current reboot remained
`Fri Sep 4 06:19:51 2026`, checkpoint **42459**, level 18, with no XP change.
This is a liveness improvement, not progression or HERO proof.

### World-time completion liveness repair: September 21, 2026

Live run **13705** found a second liveness edge in the maintenance probe. After
`time` and `save` completed at healer room **3054**, a stale local combat flag
allowed the ordinary healer-recovery branch to alternate `sleep` and `stand`
until the 180-second segment boundary. The starter now gives a completed probe
priority over optional recovery, and clears that local flag only after the
authoritative room state confirms no combat and no mobiles in the source-safe
healer room. City-shop observation remains ahead of logout when explicitly
requested, and actual combat or an occupied room still blocks the shortcut.

The new regression covers the hungry, wounded, runtime-boundary shape and the
full starter suite passes **1,445 tests**. Direct live run **13708** verified the
fix with six commands (`time`, `save`, and `quit` after login), returning Dorrik
to healer room **3054** at full health without a stand/sleep loop. No new reboot,
fame change, or HERO
progression was observed; the next frontier remains sanctuary reacquisition or
a stronger source-safe level-25 combat envelope.

### Aggressive endpoint entry correction: September 21, 2026

Serevian's source-ranked air run exposed a timing hole: the source griffin in
room **1037** was plain `ACT_AGGRESSIVE` and auto-attacked on entry, before the
runner could issue its deliberate attack or use live `consider`; a nearby fairy
dragon then caused the bounded withdrawal and DD4 charged **99 XP**. The route
builder now carries a source-proven plain aggressive endpoint mobile in the
invisibility identity, so an already-selected route must establish fresh
invisibility before crossing the room. Scripted, detecting, special, unknown,
capacity-rejected, HP-over-budget, and live combat hazards remain blocked or
authoritative. The new regression preserves the griffin's separate capacity
rejection and verifies the route identity; the full offline suite passes
**5,903 tests**. No new live XP or HERO proof is claimed.

### TARGETMODE identity boundary: September 21, 2026

Run **13663** safely exercised the source-ranked New Ofcol cow research route.
The source graph shows both wandering mobile **613** and sentinel mobile **614**
can reach Barn room **620**. DD4's live `TARGETMODE` response exposed two cows
as ephemeral process-wide selectors **#372** and **#373**, with identical live
descriptions; those selectors are not source VNUMs. The runner therefore kept
the source-ambiguous stop closed, returned to healer room **3054**, and recorded
no kill, XP change, or loss. This confirms that exact selector presence alone
cannot authorize a source-identified target when same-name instances remain
indistinguishable; a unique live description or source identity is still
required. It is identity-safety evidence, not progression or HERO proof.

### Area door semantics: September 21, 2026

The source parser now follows `runs/dd4-source/server/src/db.c` when reading
area `D` records. Their second field is DD4's lock type: raw `-1` and `0`
produce an ordinary open exit, while type `2` expands to
`EX_ISDOOR | EX_PICKPROOF`. This corrected the source route graph and moved the
Dwarven Catacombs sanctuary plan back to research-only status. Its west door in
room `6505` is closed, locked, and pickproof; `pick lock` cannot bypass it, so
the selector rejects the route for both trained and untrained thieves until a
separate source-proven key acquisition path is implemented. The parser smoke
test and source policy regression preserve this fail-closed boundary. No live
XP or HERO evidence follows from the correction.

## Current Continuation: September 21, 2026

Serevian's bounded funding run acquired the Moria yellow-and-green ring, then
live liquidation showed both the Leather Worker and Armourer refusing it. The
source object is poisoned (`ITEM_POISONED`), so it was never valid sale funding.
The planner now rejects poisoned source loot before dispatch. Funding kills
remain durable audit evidence but contribute zero to policy progress, fame
history, or HERO metrics. Checkpoint **42044** is safe at healer **3054** with
the stale Moria research result removed; the next executable step requires a
fresh funding carrier or another source-safe progression route.

### Forest route liveness correction: September 21, 2026

Kestrel's live Forest required-loot gate observed the source poison-swarm crowd
at room 18027 and withdrew without combat. The resulting current-reboot hazard
was persisted, but the funding-preemption selector could still reopen the same
maintenance route on a later resume. Selection now treats that exact hazard as
a quarantine: ordinary resumes rotate to the available frontier or return a
bounded unavailable result, while only the separately evidenced healer-origin
recheck may reopen the route once. The live regression stopped at checkpoint
**42402** with no duplicate Forest run, no XP change, and no new live socket.
The full offline suite passes **5,883 tests**.

### Readiness admission audit: September 21, 2026

The offline readiness report now separates an offensive HP-ceiling fit from
the campaign's full dispatch admission. Each target records source HP
admission, sanctuary requirement and availability, and final `admission_fit`.
This corrected a misleading level-25 report where Mr Smithy fit the raw damage
ceiling but still failed the survival/output-reserve gate. Dorrik's bounded
resume at checkpoint **42404** therefore opened no gameplay socket and retained
the real blocker: sanctuary reacquisition or a stronger, source-safe combat
envelope is required before the next productive route.

### Level-25 frontier and maze liveness: September 21, 2026

Dorrik's bounded continuation reached checkpoint **42416** at level 25 with
381,533 XP. One finite 60-second area-reset wait completed, but `time`
confirmed the same DD4 reboot and no current-band route reopened. The live
Abyss copepod policy withdrew at its movement reserve without combat or XP;
the tree-sprite policy remained unavailable. The readiness report now makes
the boundary explicit: the three unprotected admission-fit candidates are
source level 18-22 maintenance targets, while current-band targets require a
sanctuary reserve or fail the survival/output gate. They are not progression
targets and must not be counted as XP evidence.

The source audit of the Sahuagin Market purple potion also remains analysis
only. The potion is nested in a locked display case; its glass key is carried
by level-35 shopkeeper Bilani, whose scripted cleric special makes this an
unproved high-risk acquisition rather than a level-25 sanctuary route. The
campaign therefore remains fail-closed until a legitimate reserve or stronger
combat envelope is evidenced. The resource inspection CLI now preserves that
chain explicitly as container 27323, key 27324, and carrier 27234, and marks
the placement with a locked-container autonomy rejection.

The live maze navigator had an unreachable unexpected-room rebase branch. It
now clears stale DFS state once and continues from the observed room within
the existing eight-rebase bound. The starter suite passes **1,440 tests**, the
campaign suite passes **1,581 tests**, and the complete offline suite passes
**5,883 tests** after the repair.

### Abyss safe-fido navigation revalidation: September 21, 2026

Policy revision **307** now treats source-audited `spec_fido` rooms as
non-combat hazards during Abyss randomized-route planning. The offline planner
for Dorrik's copepod reset at room **7548** no longer blocks the fido bridge;
the route remains statically safe and estimates 96 flying movement. A narrow,
source-revision-tagged migration preserved the prior 7544 result and sentinel
cooldown while reopening only the preferred 7548 result for one retry.

The bounded resume did not open a gameplay socket because Dorrik has no
sanctuary reserve and the target's audited HP range is **242-713** against his
**569** HP ceiling. Its protection gate remains authoritative; checkpoint
**42456** is safe at healer **3054**, level 25, with no XP change. The marker
remains pending for a legitimate protection/resource handoff. This is route
evidence only, not progression or HERO proof. The complete offline suite now
passes **5,890 tests**; compilation is clean.

### Familiar-backed Aeloria revalidation: September 21, 2026

Aeloria's level-18 mage checkpoint **42421** has learned `summon familiar`,
and the exact source Guardian policy (`source-ranked-hunt-arachnos-6313-6367-18`)
passes the existing familiar damage, route, mana, isolation, and source
identity gates. The prior hard-health withdrawal had no XP loss, so the
campaign now arms one durable familiar-backed revalidation for that exact
same-boot target. It is consumed at dispatch and closed after one result;
ordinary fame still requires a target at least six levels higher, and this
repair does not widen that rule. Run **13629** live-validated the path: the
familiar was summoned and grouped, the Guardian died for **607 XP**, and
Aeloria recalled and slept in healer room **3054** with no death or XP loss.
Checkpoint **42423** records `completed_kill=true` and a succeeded, single-use
revalidation marker. HERO remains unproved; the next segment must select a new
current-band policy rather than replaying this target.

### Kestrel fame prerequisite boundary: September 21, 2026

Kestrel's bounded resume reached checkpoint **42426** at level 24 with fame
**-12**. One finite area-reset wait reopened the source-ranked Moria sanctuary
reserve, but the carrier route produced no potion; the exact reboot-scoped
recheck budget is now exhausted and the character returned safely to healer
room **3054**. The fame selector remains source-correct: an ordinary recovery
target must have a live level at least **six higher**, so Kestrel needs a
level-30-or-higher target. No fame change or progression XP is claimed.

## Delivered Foundations

- Async Telnet negotiation, GMCP capture, transcripts, SQLite, and inspection CLI.
- Deterministic observations, character state, checkpoints, and replay tests.
- Parameterized creation, the starter tutorial, and early character development.
- Run/campaign reports with evidence-grounded commentary and persona metadata.
- Public `hero` entry point, resumable campaigns, credentials, bounds, and recovery.
- Shared source-backed combat, training, equipment, travel, and resource policies.
- Source resource analysis recognizes DD4 `ITEM_PILL` objects such as Olympus
  nectar, emits exact `eat` activation, and handles live success/failure
  acknowledgements without leaving a reserve pending. This remains source
  evidence until a bounded live acquisition proves the route.
- Bounded campaign startup that reuses a current-level live training audit and
  reserves historical event scans for legacy checkpoints.
- Source-ranked gear acquisition report with separate equipment-reset
  provenance, stance scoring, route evidence, and hazard/rejection fields.
  Executable planners cover direct ground resets and exact source carriers;
  carrier execution still requires a matching hunt candidate and post-kill
  loot/equip action, and live acquisition remains unproved.
- Exact TARGETMODE selectors now bind case-normalized live room descriptions to
  the source mobile prototype before a same-name attack. Protection recovery can
  retain one independent low-fuzz plain fallback after the ordinary ranking
  floor, but same-boot below-band evidence remains a hard exclusion.
- Read-only `show-combat-readiness` report for cross-class output envelopes,
  durable campaign constraints, current-band target fit, and gear blockers.
  It is diagnostic evidence only and cannot authorize live dispatch. Its fame
  view exposes DD4's ordinary +6-or-higher rule separately from the current
  bounded +9 research horizon and
  source-famous branch, so a missing fame route is visible rather than hidden
  by the normal current-band target list.
- Required-loot maintenance withdrawals retain bounded raw terminal absence
  evidence and recover it on startup, with a reset-scoped cooldown before the
  exact route can be reconsidered.
- Current DD4 source parsing resolves inherited and per-mobile `MobHPMod`
  values and applies them after level/rank scaling in hunt, encounter, city,
  and campaign HP budgets. Unresolved source templates fail closed across
  those gates instead of falling back to neutral HP.
- Current DD4 source parsing also resolves inherited and per-mobile `MobDamMod`
  values and applies them per NPC attack before sanctuary/critical bounds.
  Unknown damage modifiers fail closed in hunt, encounter, route, city, and
  companion timing gates; reports and persisted candidates retain the scalar.
- Target-specific source output models DD4's eye-dependent `knife toss`
  face-hit double only when parsed body-form evidence proves the target has
  eyes; unknown anatomy receives no bonus. The target-independent Kestrel
  report therefore remains a 318-point school-dagger envelope.
- Mudlet bridge interface; this is not full VM lifecycle or HERO validation.
- Source-backed familiar withdrawal uses DD4's `flee Fear` override for the
  charmed pony and requires positive in-place sleep evidence; live acceptance
  of the repair remains pending a clear city route.
- `hero --autonomous` now supervises one bounded live worker at a time,
  reusing durable credentials and checkpoints until HERO or a finite reset/
  blocker boundary. Its reset budget counts completed waits, not the periodic
  progress heartbeats emitted during one wait. This improves liveness and
  resumability; it is not progression or HERO proof.
- Field-city obstruction evidence is scoped to the exact source policy that
  encountered it, allowing alternate source routes to receive their own
  bounded preflight while legacy policy-less evidence remains conservative.
- Ordinary source-ranked hunts can opt into one exact source-material bystander
  when both mobiles are unarmed, non-aggressive, non-scripted, non-special,
  freshly considered, and covered by one combined HP, damage, mana, and
  six-action budget. Unknown or hazardous additions still withdraw; live
  acceptance remains open.
- A source-verified displaced sentinel can resume the already-vetted outbound
  step to its registered reset room after a temporary crowd is observed in the
  preceding room. This preserves the crowd combat gate while avoiding a false
  terminal return before the planned endpoint is checked.
- The displaced-sentinel repair has a one-shot campaign revalidation marker.
  When its exact policy is pending, the outer crowd wait may open only that
  segment; segment-start consumption and segment-end closure prevent replay,
  while a new crowd remains a bounded withdrawal.
- Capacity-container recovery reconstructs pending sack, backpack, and girdle
  claims chronologically, suppresses stale legacy restores after later claims,
  and permits one healer-side relief/retry when a live capacity claim is
  rejected for weight. The source-ranked last-policy fallback honors exhausted,
  throughput-limited, and current-reboot crowd evidence.
 - Policy revision 302 admits one sanctuary-protected damage-window probe for a
  passive nominal-current-level target whose DD4 load-time HP fuzz reaches two
  levels above the character. It also mirrors `fight.c`'s `ACT_IS_FAMOUS` fame
  branch and registers the exact Green Dragon 6112 gas-breath candidate for
  Kestrel's negative-fame recovery. The selector, stop builder, HP admission,
  and healer nausea-recovery gates share this contract; live GMCP still decides
   whether the one-shot probe is executable. A no-combat, source-audited ground
   gear reset is now considered before a blocked flight-funding loop, while
   flight-only and carrier routes retain their existing gates. Once sanctuary
   is observed for that exact gas contract, the runner may use the existing
   finite 36-action probe; ordinary and pre-sanctuary estimates remain fixed.
   Revision 301 also carries the improved-output fame retry through the stop
   builder so the live sanctuary opener is reachable when its one-shot evidence
   and reserve gates pass.
 - Revision 302 keeps an already-reconciled level-24 Moria recovery checkpoint
   on the dedicated 11-stop route instead of collapsing it into the generic
   single-room reserve executor. Run 13275 live-validated that route through
   rooms 4064, 4152, 4071, and the remaining bounded locator stops; the carrier
   was absent, so no acquisition or progression is claimed.
 - Policy revision 303 makes healer recovery explicit for active poison at room
   3054. It reopens one exact Forest claw retry despite the
   old protection marker, then consumes that exception at segment start; a live
   poison-swarm crowd at room 18027 still forces withdrawal.
 - Policy revision 306 carries the exact source upper level bound into every
   generated stop for a sanctuary-backed, required-loot gear carrier. This
   closes a route-construction gap when load-time level fuzz reaches the
   source-recorded upper bound, without authorizing unprotected combat or
   changing the ordinary +6 fame rule; live acquisition remains unproved.
 - Runtime preparation now reuses the already-loaded immutable source catalog
   across resource and frontier selector passes and emits level-aware progress
   while no gameplay socket is open. This addresses large-database resume
   liveness without changing combat admission or progression proof.
 - Policy revision 305 makes the exact Shadow Keep fine-dagger maintenance plan
  available at level 24. Its source-identified level-26 smuggler is admitted
  only through the plan's explicit +2 level ceiling, sanctuary protection,
  lower-bound output check, and finite live damage probe. This does not widen
  ordinary fame recovery, whose target window still starts at +6 levels.
- Revision 305 also permits an ordinary fame target with wider source HP fuzz
  when sanctuary is verified and the player output covers the source lower
  bound. The live stop still requires GMCP HP and damage-window confirmation;
  this is an admission improvement, not evidence of a fame kill.
- A separate source-ranked aggressive HP-fuzz probe now covers only a plain,
  unarmed, unscripted aggressive target whose exact source route preflight and
  bounded transit checks pass. Sanctuary, source lower-bound output, and a
  finite live damage window are required; this does not widen ordinary fame
  recovery or authorize generic aggressive targets.
- Admitted caster encounters now have a finite live spell fallback: after two
  weak preferred-spell attempts, the damage probe can measure the next
  practiced source-registered damage spell. The rotation is encounter-local
  and retains all source, mana, incoming-damage, and withdrawal gates; it is
  not evidence of a kill until live XP and return state are recorded.
- The exact source Circus flight reserve is now reputation-aware. Its first
  action is a shopkeeper `buy ticket`, and DD4's `do_buy` rejects every shop
  purchase below zero fame. Live refusal evidence is persisted as a structured
  route result; `--retry-stalled` may reopen a dynamic route hazard only when
  this reputation boundary is absent.

These have implementation and varying amounts of live proof. Their existence
does not mean every race/class or level band works end to end.

## Immediate Delivery Gate

1. Continue Kestrel beyond level 24 with measured current-band encounters and
   positive whole-session net XP; use a source-executable target or gear
   upgrade after recovery and funding gates clear, without reopening closed,
   over-budget targets. The source mirror is `bee610c`, and the current source
   estimator still reports a 318-point target-independent school-dagger
   envelope. Ordinary fame recovery requires a victim at least six levels above
   the player, so level-24 Kestrel needs a source level-30-or-higher target.
   If sanctuary is reacquired, the newly unlocked level-24 Shadow Keep
   fine-dagger plan is the next output-improvement route; it is not fame or XP
   permission and must still pass its live HP and damage-window checks.
   Kestrel is level 24 at **330,969 XP**, safely at healer room **3054**, with
   checkpoint **41526**. Run **13275** exercised the corrected
   11-stop Moria route through the second carrier room **4071**, but the purple
   potion was absent. A new quest request cannot repair fame at **-12** because
   DD4 rejects requests below zero fame; only a completed kill quest would award
   positive fuzzy fame. The next gate is a source-supported fame-positive kill
   or stronger gear/output route, followed by positive whole-session
   progression. No higher-band route is authorized.
2. Advance the fresh character from level 8 to 9 and through the level-10
   trainer transition without adding name-specific behavior.
3. Demonstrate three consecutive bounded public invocations with positive
   combined net XP, repeated useful kills, autonomous maintenance, and a level
   gained. Include travel, recovery, provisions, and failed hunts in the cost.
4. Exercise the autonomous supervisor across a reset boundary, then compare
   the existing thief, mage, and warrior campaigns at their actual frontiers,
   then expand only after the shared loop proves productive.

## Current Status (September 15)

The latest source pull is `bee610c4081a1d2c1d7c8ee80343a337079be024`.
Kestrel's latest durable checkpoint is **41526**, level 24 at **330,969 XP**
in healer room **3054**. Run **13275** opened the corrected deep Moria plan
and checked both source carrier rooms plus the bounded locator chain; the
carrier was absent and no XP, fame, or reserve changed. The latest bounded
policy pass returned without opening a gameplay socket or changing XP. Run
**13289** then returned safely to the healer in six commands without XP
progress. Run **13256**
reached the source-famous Green Dragon under the improved-output
revalidation gate; GMCP reported **576 HP**, Kestrel withdrew after gas nausea,
and DD4 applied a **385 XP** loss without a kill or fame change. Runs **13277**
and **13278** exercised the revision-303 healer recovery and exact Forest
retry: poison was cured at room **3054**, `where kodiak` found the carrier in
the River bed, and the connecting room **18027** contained a live poison-swarm
crowd. The bounded retry withdrew safely without XP loss or claw acquisition.
The campaign policy revision is **306**. Alignment is
**1000**, distinct from fame **-12**. DD4 rejects new quest requests below zero
fame, so the next recovery choice must be a source-proven fame-positive kill or
stronger gear/output route. The full campaign suite passes **5,796 tests** and
clean compilation; sustained progression, the level-10 fresh-character gate,
and HERO 100 remain unproved.

## Current Status (September 13)

The latest source pull is `80cad011b8c17b5ffc8828edae9182271bf7e46e`.
Kestrel remains level 24 at **332,319 XP** in healer room **3054**, checkpoint
**40782**, with **1,046 copper-equivalent**. Runs **13154-13156** repaired the
funding loop through safe sales and a source-backed maintenance kill. Runs
**13157-13158** performed bounded exact-target reset/preflight checks and found
the target absent; run **13159** then completed a source-backed low-band
funding kill for **50 XP** and extracted its coins. Run **13160** donated the
unaccepted purse after the coins were extracted. Run **13161** used the one
post-reset capacity entitlement for the exact Moria carrier, found it absent,
and returned safely without XP or loss. The current-reboot sanctuary route is
still exhausted and the prior Magic Shop refusal remains durable.
The full offline suite passes **5,701 tests**; sustained progression and HERO
remain unproved.

The shared source estimator now carries DD4's `do_knife_toss` face-hit double
only for target records whose parsed body form proves eyes; unknown anatomy is
left uncredited. The target-independent Kestrel envelope remains 318, and
readiness still reports no candidate passing every source, safety, and output
filter; no higher-band route is authorized. The latest bounded autonomous retry
was checkpoint **40782**; it used the repaired post-reset capacity entitlement
exactly once, and the audited carrier was absent with no kill, XP change, or
loss. The supervisor is regression-tested to count one completed reset wait
rather than each progress heartbeat, and the same entitlement is consumed at
the segment boundary so it cannot be replayed.

Astrevo is level 8 at **31,513 XP** at checkpoint **40956**. Runs **13179**
and **13181** added 180 and 118 XP from source-ranked current-band routes;
runs **13180**, **13182**, and **13184** recorded bounded absence or crowd
outcomes, while **13183** and **13185** retained the finite funding boundary.
Run **13185** also captured an exact source sentinel one room before its
registered reset room. The interception now resumes that already-vetted
outbound step after a temporary crowd, preserving the combat rejection while
allowing the planned endpoint to be checked. Run **13186** exercised the
one-shot campaign revalidation and closed it on a fresh two-mobile crowd. Runs
**13190-13192** then proved the capacity-claim relief path, banked maintenance
coins, rotated away from the exhausted Circus route, and recovered an
interrupted worker. Astrevo is safely at healer room **3054** with no new loss;
the level-10 trainer transition and sustained progression gate remain open.

The following reset-aware continuation used its one configured wait exactly
once. Run **13187** completed a bounded funding segment without XP change;
run **13188** then reached a fresh target endpoint, observed a two-mobile
crowd, and withdrew safely. The supervisor ended that earlier sequence at
checkpoint **40901** with no loss and no duplicate worker. The next invocation
rotated from that crowd evidence rather than replaying the closed route.

### Route-Only Loss Revalidation: September 13, 2026

An old Astrevo source-ranked hunt had recorded an XP loss during transit before
the intended target was present. The new bounded repair recognizes this exact
shape only when there was no target combat, no objective kill, full healer
recovery, and one source-labelled below-band transit hazard. It then requires
a fresh same-level source candidate with the normal source, route, movement,
identity, HP, and output gates. The marker is consumed at segment start and is
cleared only by a productive result; a second failure closes it.

Live runs **13168-13170** validated the policy: Astrevo completed the repaired
route, a clean repeat, and a rotated Circus target. Follow-up runs
**13171-13177** recorded bounded city, crowd, and watchdog boundaries; run
**13178** stopped before connection while awaiting an area reset. Checkpoint
**40837** is level **8** at **31,068 XP** in healer room **3054**, with no new
loss. The campaign module passes **1,489 tests**. This is the first
three-segment positive current-band run for the fresh track, but not yet the
level gain, trainer transition, or HERO acceptance gate.

Recent continuation (2026-09-10 through 2026-09-11): runs 12948-12953 advanced the level-24
frontier without inventing progress. The secretary exceeded Kestrel's audited
damage budget, food was replenished, a poisonous live crowd blocked Mr. Smithy,
and the Forest bear-claw route withdrew at room 18027 when its required-loot
gate found a bystander. Run 12959 completed a below-band Midget kill as a
funding action, adding 40 XP and 50 copper before a safe return to healer 3054.
Runs 12960-12962 then cleared the recovered purse, sold the loot, and produced
a viable current-band watchman research result; the balance reached 2,878
copper-equivalent. Runs 12963-12965 safely exhausted the current Moria
sanctuary attempts. Reconnect run 12966 was interrupted; startup repair marked
it failed, left its segment ready, and converged at checkpoint 39961. Runs
12967-12970 completed bounded food maintenance. Run 12971 exercised the
widened nine-endpoint fallback, killed source carrier 4055 for 100 expected
below-band XP, recovered purple potion 4050 into the pouch, sacrificed the
corpse, and returned safely to healer 3054. Runs 12972-12978 completed safe
food, recovery, and target probes. Run 12979 verified that the purple potion
ledger survives a fresh live resume; runs 12980-12982 reached current-band
targets but rejected them on source HP and damage bounds without combat or new
loss. Run 12984 reopened the source-validated Forest upgrade after the fresh
damage gate, then withdrew at room 18027 when source-registered mosquitoes and
wasps formed a crowd. Runs 12985-12986 then refreshed the source-verified
food/revision state and reached the Solace Secretary route through its exact
`where drunk` preflight. The live target's source HP ceiling still exceeded
the fixed knife-toss budget, so the segment withdrew before combat and
checkpoint 40039 preserves the same-reboot loss evidence. Run 13018 then
reached the source Cyclops, where GMCP reported 407 maximum HP against a
318-point audited output budget. Its aggressive entry produced a net 338-XP
loss; the target is now closed at this level and the evidence remains in the
ledger. Kestrel remains level 24 at 332,289 XP in healer room 3054.
Required-loot and funding kills remain separate from objective progression.
This proves safe resource recovery, corrected source location, durable
campaign metadata, and bounded crowd handling, not sustained progression; the
next gate remains a protected productive current-band journey.

The source-ranked chooser now skips a plain target whose source HP ceiling has
no legal live probe path. For a current-band HP-fuzz target, the new narrow
path requires sanctuary, a source-audited lower-bound kill window, and the
bounded `where drunk` contract when that route preflight is present. One live
GMCP damage-window probe must still show that the loaded target fits the fixed
source output budget; sanctuary does not authorize an unlimited fight.

### Cross-Class Continuation (September 11)

Dorrik's bounded warrior runs rotated across two absent but source-valid
routes, preserving a level-25 healer checkpoint. Serevian completed a thief
weapon-repair attempt but did not acquire the source-required bear claws.
Astrevo killed the Circus Bearded Lady for 140 XP at level 8, then safely
deferred a repeat when the city route was obstructed. That run also exposed
and fixed a key-classification bug: ITEM_KEY objects are no longer stance gear,
including when a key was incorrectly worn by an earlier run. The next gate is
repeatable positive net XP across the thief and mage tracks, not a new HERO
claim. Astrevo's following New Ofcol attempt found a source-observed crowd at
Gallow Hill and withdrew safely without combat or loss, preserving the
positive Circus evidence.
The shared source combat registry now includes infernalist `hellfire` and witch
`wither`, including source-derived damage bounds and spell timing checks. These
paths are ready for a bounded live probe once a corresponding character reaches
the subclass; no subclass or HERO proof is claimed.

### Latest Live Continuation: Moria And Protected Specials (September 12)

The refreshed DD4 source is `c8c4ddc`. Source reset analysis confirms that
Moria's large hobgoblin carrier (mobile 4055) has global capacity two, with one
reset in each of rooms 4064 and 4071; this is the only multi-instance exception
currently admitted for a required sanctuary resource. Revision 279 reopened
that exact source contract for one bounded maintenance attempt per remaining
instance. Runs **13093** and **13100** killed the two carriers, acquired purple
potion object 4050 twice, added **180 maintenance XP**, and returned alive to
healer room 3054. This is resource proof, not progression proof.

Runs after the acquisition safely rotated through fame, food, and current-band
research. Run **13097** reached live Chaplain Jerrold (mobile 629), confirmed
his presence and an easy-but-healthier consider result, then withdrew before
combat because no authoritative enemy HP snapshot existed yet. Source audit
shows `spec_guard` adds its special attacks only after combat begins. The
starter now permits an exact, unarmed, nonaggressive, no-program audited
special to consume verified sanctuary before its opener, while retaining the
live GMCP HP and fixed output-budget gates; entry-attacking targets remain
blocked. Run **13099** confirmed the mayor at live 664 HP and rejected it
without combat after recording a 385-XP loss. Run **13102** preserved the
Chaplain route's wandering-drunk hazard after bounded waits and returned to
the healer. The full starter and campaign suites pass **1,395** and **1,460**
tests, respectively, and compilation passes. The next acceptance gate remains
a positive whole-session current-band kill and then three consecutive positive
net-XP invocations; HERO is still unproved.

### Latest Live Gate: Cyclops HP Revalidation (September 11)

Run **13018** reached source mobile **9202** at endpoint room **9204**. The
authoritative GMCP enemy record reported **407/407 HP**, while the thief's
source-audited `backstab` plus `knife toss` budget covered **318 HP**. The
aggressive target engaged on arrival; the run withdrew with a net **-338 XP**,
no death, and no kill, then safely checkpointed **40172** at healer room **3054**.
The source loss ledger now closes this target for level 24. The endpoint gate
was corrected to consume the exact validated GMCP enemy records before sanctuary
or opener dispatch, with a regression test for the over-budget case. This is
useful boundary evidence, not sustained progression or HERO proof.

The funding ledger now prefers durable completed-kill evidence for a funding
segment even when the kill is below the useful XP band. A completed funding
action ages its retry cooldown even when it yields no progression XP, and a
below-quote funding need is not hidden by a cooldown while the observed balance
is insufficient. This prevents stale funding markers from causing startup
deadlocks without turning low-value kills into progression proof.

Offline source work (September 10) now retains objects loaded through `E`
equipment resets when building hunt and campaign loot evidence. The new
`show-gear-sources` command ranks class-usable placements by combat, pre-level,
or recovery stance and exposes reset provenance, route, hazards, source
rejections, and role fit. Thief combat and recovery reports preserve the
source-backed piercing primary required by backstab, so a higher-damage
non-piercing weapon is not misreported as a usable upgrade. It makes gear
planning reusable across the roster, but it does not grant live combat
permission or count as acquisition or progression proof.

Aeloria checkpoint 39739 is level 18 at 161,181 XP. Run 12880 proved that the
invisible carrier locator reaches both required-loot mobiles together. Run
12881 live-proved the duplicate-target handoff and gained 90 XP from the exact
carrier; run 12882 found the White Stag absent with no loss. Require repeated
positive whole-journey XP and the second potion before claiming sustained
progression.

### Earlier comparison (preserved)

Current checkpoint 39657 was Aeloria level 18 at 161,091 XP, with full resources
and one verified purple potion in healer room 3054. Runs 12857-12863 netted
-7 XP over 575.85 connected seconds, plus one 180-second reset wait, with no
level gained. Policy 254 source-proves a narrower alternative to repeatedly
waiting for a second potion: a fixed mage special whose maximum load is below
20 can rely on recallable flee rooms and Midgaard's fixed adept healer for
blindness recovery. Run 12863 live-proved selection and safe routing, but the
hobgoblin king considered below band and was skipped. Rotate to the next
source candidate; require a useful consider, protected combat, player XP, and
safe recovery before calling this a productive progression path. Actual
blindness and healer curing remain separate live gates.

Latest offline corrections: current-field crowd priority, same-reboot reset
handoff, elapsed-time damage sampling, and a deterministic deadline regression.
Travel invisibility now requires practiced authorization; shop obstruction uses
bounded rechecks. Fresh local targets supersede unengaged wandering pursuit.
Reconnect repair now attributes circuit kills to the observed stop rather than
the headline, and the legacy migration no longer rewrites modern terminal data.
Run 12785 exercised the restored selection but found absence/crowding; a later
rotation earned 109 XP from the hermit crab. Next assess the actual three-target
Moria crowd and avoid unproductive early repeats of a just-completed single-target
route. Preserve source assistance, health, and recorded loss constraints.
Repeated same-name instances now share bounded bystander considers. Only
positive below-band evidence discounts them; an XP target needs its own fresh
consider. Source combat retains that chosen instance across room/GMCP updates.
Current Telnet GMCP can repeat the primary opponent instead of identifying
each attacker; duplicate records are not independent identity evidence.
Run 12790 live-validated three exact-instance probes: two possible useful
combatants and one below-band bystander, with no XP. The next capability is a
bounded two-instance encounter, not another identical inspection. The new
source-estimated pair controller now passes timed offline replays for both
kills, exact selectors, practiced-spell cost, and survival/expiry failures.
It shares ordinary action dispatch and retains existing loss history.
The first live acceptance attempt was interrupted in town before reaching the
pair and lost 58 XP. Source guard assistance, not pair execution, is the next
access issue to resolve. Do not repeat the unchanged journey or count its
safe healer return as useful XP proof.
The source-backed field departure now shares the existing bounded city locator
and healer wait, with an independent audit record. Revealed alignment must be
within the real 300-1000 guard-safe range; the low-level GMCP sentinel 50000
cannot authorize ignoring a guard. Run 12794 live-validated two blocked healer
waits followed by positive clearance and normal departure. Runs 12795-12796
added two useful kills, but 12797 repeated an absent target and 12798 paid 68 XP
to retreat from an already-engaged below-band target at full health. Selection
and defensive continuation must remain separate. That continuation now reuses
the bounded active-encounter budget and has offline replay proof, not a new live
kill. Pair execution and sustained levelling remain open acceptance gates;
current verification and measured results are in the active review.

Funding now locates wandering carriers from an earlier source-checked same-area
waypoint. Run 12801 reached the actual carrier with movement remaining, then
returned because the required-loot branch rejected a second ordinary orc before
live consider or a crowd recheck. The repaired path now uses shared exact-instance
consideration and existing crowd waits; the real-source replay also catches the
`orc`/`large orc` keyword collision. Fresh loot acquisition and liquidation remain
the next gate. The reset status contract was already working. Navigation proof
is not income or XP proof. Full offline validation passes 4,765 tests.
The next bounded invocation (12802-12803) never left town because its shared
departure checks remained blocked. Resolve or observe clearance of that common
restriction, then require live carrier acquisition and a sale; repeated safe
town logouts do not validate the new endpoint behavior.
Successful, freshly confirmed no-travel stops now have a separate departure
outcome. They spend the segment without inventing a failed funding target or
rotating through another destination behind the same obstruction. The full
4,789-test suite passes; live confirmation of this handoff remains pending.
Run 12804 cleared town but stopped its ambiguous cave search in a passive
poison-mob room without the carrier. Examine bounded search continuation there,
preserving source/exit/resource checks and excluding new combat admission.
No new funding income or XP was demonstrated.
The passive-room change now reaches the existing absent-target/search path
under exact source identity, current exit and safe path checks. It neither
attacks that crowd nor adds another search. All 4,825 tests pass, including
the run-12804 cave replay. Runs 12805-12806 now prove one carrier acquisition
and sale, adding 133 XP and 14 carried copper including the sacrifice. Only
4 of the 9 sale coins became carried money because of bank debt. The passive
crowd branch was not exercised. Improve retained funding income and useful
kills per whole journey next; one low-value sale does not meet the sustained
progression gate.

The funding checkpoint now distinguishes fresh observations from inherited
field-abort text. A narrowly verified repair removes only restrictions replayed
onto a completed carrier; failed/newer attempts and unrelated hazards remain.
Runs 12807-12808 live-validated startup repair, a 175-XP carrier kill, sale, and
safe return without another reset wait. All 4,865 tests pass. Optional-flight
funding still needs better retained income or a productive ground-hunting
fallback; the fresh track remains level 8, not a sustained levelling success.

Funding carrier rewards now reconcile into exact source-route research without
duplicating XP or changing the segment's purpose. A measured low-yield sale can
prefer an immediately executable ground hunt. Runs 12809-12810 validate the
repaired reward surviving startup, an ordinary 195-XP hunt, and liquidation.
The preliminary protection-blocker diagnosis came from an inspection that
omitted source-world initialization; the live familiar contract was executable.
Three recent invocations have positive combined XP, but no level gained.
Improve one-target travel and preparation cost before claiming sustained progress.

Run 12811 then exposed a familiar opening kill before the player could act:
zero XP and missed corpse loot. The observer now cancels the stale opener and
preserves the zero-XP encounter/loot path under exact ownership and identity
checks. It also distinguishes the target's death from the familiar's death.
That repair passed 4,933 tests and still needs live acceptance. A fresh-consider
solo substitution is now implemented for ordinary, fully funded low loads:
confirm companion sleep, use the existing one-target encounter budget, and
confirm waking before ordinary travel. It preserves class, crowd, damage,
resource and loss gates. Preparation mana is still spent; neither this code
change nor an NPC finishing blow establishes improved progression. Validate
the player kill and complete return through the public runner next.
The follow-up public check opened no connection: its one 180-second reset wait
reduced the prior failed-hunt cooldown from 3 to 2, then funding remained
unavailable at checkpoint 39364. XP stayed 28,868. All 4,988 tests pass, but
the solo handoff has no live acceptance yet; preserve that distinction and
do not treat the cooldown as proof that the area is empty.

The existing thief campaign then completed runs 12813-12814: a pursued target
yielded 183 objective XP, followed by two loot sales and safe healer logout.
The hunt and sale took 166.23 connected seconds with no reset wait or loss.
Serevian is level 11 at checkpoint 39387, 50,894 XP. This route retained its
door-bearing approach, so it is not live proof of the new early locator.

Run 12812 followed two further bounded reset waits and reached Moria, but
spent most movement reaching the reset before `where` located the target
elsewhere. It returned fully recovered with zero XP after 144.72 connected
seconds. Ordinary hunts now share the existing early-locator planner, keeping
mandatory familiar staging and all combat/retry gates. The source replay
reduces the approach from 21 commands to 13 before locating. All 5,003 tests
pass; improved live travel and XP throughput remain separate acceptance gates.

Latest public runs 12815-12816 exposed two decision errors: an unsolicited
prompt falsely failed familiar preparation, and a one-HP shortfall in the
opening-damage threshold caused a healthy solo fight to flee. Both have timed
replay fixes. Early location and confirmed companion sleep/player opening now
have live proof; completed solo kill/wake and improved throughput do not.
Raw GMCP also exposed double subtraction of the flee penalty. The parser fix
passes all **5,080 tests**; the actual comparison is **-53 XP**, not -121, over
171.00 connected seconds plus 1,080 reset-wait seconds. Historical checkpoint
39419 is stale (28,747 versus raw 28,815). Recovery run 12820 and normal public
resume now confirm the correct baseline in 39433, preserving the genuine loss.
Runs 12817-12819 also live-validated flee/refund accounting and added net 253 XP
to the existing thief, including a 297-XP incidental Moria warrior kill. This
took 267.14 connected seconds with no reset waits and no level gained. Keep the
warrior distinct from the selected hobgoblin and retain the real second-griffin
arrival as evidence; duplicated primary-enemy fields do not prove one attacker.
Next validate productive continuation at an executable roster frontier, not
another unchanged deferral.
Two further public hunts (12821-12822) added no XP and exposed an early-target
rejection losing its actual route position. The repaired handoff resumes the
existing unfinished leg from its observed waypoint, retains the rejection,
and requires fresh consideration at the destination. Its 13 new checks pass;
live continuation and useful target acquisition remain to be proved. Across
all five thief segments the measured net +253 XP cost 409.67 connected seconds,
not only the earlier 267.14. Serevian remains level 11 at checkpoint 39441.
Runs 12823-12824 added no XP in 65.80 connected seconds plus a 180-second reset
wait; checkpoint 39452 retains level 11 and 51,147 XP. The seven-connection
comparison is therefore +253 XP over 475.46 connected seconds plus the wait.
The tower planner already included both safe servant reset rooms. Its bystander
check lost the intercepted target handoff, allowing travel before the second
exact instance was considered. The corrected replay considers that instance
first and retains source, timeout, combat, and return gates. Thirteen new tests
pass; neither this handoff nor the earlier waypoint resume has fresh live proof.

## Subsequent Gates

Policy revision 244 consumed one exact revalidation of revision 243's
source-located but unreachable invisible carrier. Runs 12831-12833 proved the
wider Moria graph, potion acquisition, and two source carrier resets, while also
exposing an unwanted potion use during collection. Recovery now derives a
two-copy ceiling from reachable source resets, requests two from an empty pouch,
and disables combat consumption for that errand. Run 12838 killed both carriers,
gained 380 XP, issued two successful `put purple pouch` commands, issued no
`quaff purple`, and checkpointed both reserves at healer 3054.

Source-ranked XP-loss evidence now distinguishes an unprotected first loss from
a route that already consumed sanctuary. One unprotected loss may receive one
protected retry; a protected loss is quarantined immediately. The segment keeps
a sticky sanctuary-use fact even though its per-fight latch resets for another
encounter. Runs 12840 and 12842 live-verified this persistence and safe recovery.

Run 12840 also exposed a zero-damage generic `kill` opener for a mage. A
source-ranked caster now opens with the exact source-planned direct spell only
when class registration, positive live practice, spell availability, and the
15% mana reserve all pass. Run 12842's first hostile command was acknowledged
`burning hands`; its eel still failed the measured damage window and was safely
quarantined. Runs 12831-12842 netted +1,490 XP over 1,265.54 connected seconds,
about 70.6 XP/minute, including maintenance and failed probes. Current checkpoint
39544 retained Aeloria at level 18, 159,658 XP, full resources at healer 3054,
and no sanctuary reserve.

Run 12843 exposed two locator defects: the bounded planner spent room capacity
on duplicate display labels while omitting a distinct reachable label, and a
zero-step relocation rechecked the already-empty current room. Unrelated
sanctuary wear-off output could also complete that pending `look`. Revision 245
reserves bounded coverage for distinct `where` labels, rejects empty relocation
paths, and requires an actual room listing. Silence gets one five-second retry
before safe return. Its revalidation recognizes only that exact same-reboot
failure and is consumed before connection.

Run 12844 live-validated the repair. Aeloria continued beyond empty rooms, found
mobile 4055 in source room 4070, killed it for 100 XP, pouched one purple potion,
and returned fully recovered. Run 12845 then quaffed that reserve against the
already productive giant, opened with `burning hands`, and gained 581 objective
XP with seven acknowledged damage commands and zero timing failures. Runs
12831-12845 netted +2,171 XP over 1,543.20 connected seconds, about 84.4 XP/minute.
Checkpoint 39558 is level 18 at 160,339 XP, 218/218 HP, 571/628 mana, and full
movement at healer 3054. The full suite passes 5,291 tests. Next improve the
reserve-to-productive-kill cycle and mage damage throughput before widening the
frontier; this pair of runs is not yet sustained progression.

Revision 255 passes actual maximum HP into fixed-route program admission. One
exact, weak, low-probability GREET attacker may use the existing source damage
bounds; ambiguous, equipped, special, deterministic, multiple, or inadequately
buffered attackers remain blocked. Run 12872 crossed the repaired Midgaard-to-
Moria route with zero stale `where drunk` checks and returned safely when the
carrier was absent. Nutrition correctly preempted the route until Kestrel had a
fresh source-backed mushroom.

Revision 256 replaced the obsolete hazardous deep-Moria route with the shared
bounded carrier locator. Run 12874 found the target by live `where`, checked the
two then-admitted endpoints, and returned safely when the carrier moved beyond
them. Revision 257 applies DD4's ordinary aggression cutoff to combat-only
transit specials: level 22 still blocks the fuzzed level-8..12 poison snake,
while level 23+ may pass it. Pre-combat and unknown specials remain exclusions.

Run 12875 live-validated the complete corrected loop. Kestrel crossed the
visible snake room without combat, found exact carrier 4055 in room 4072,
killed it for 110 XP, stored purple potion 4050, ate the severed leg, sacrificed
the corpse, and returned full-health to healer 3054. Checkpoint 39701 is level
24 at 333,643 XP. The subsequent fame attempt was interrupted and spent the
reserve; recovery checkpoint 39707 is 333,258 XP. Full verification now passes
5,424 tests, including reconnect loss and duplicate-carrier consideration. The remaining gate
is positive net XP across repeated whole journeys; neither a below-band
resource kill nor a safe recovery establishes sustained progression.

| Gate | Acceptance |
| --- | --- |
| Sustained progression | Repeated productive journeys, training/equipment changes, and interruption recovery without steering |
| First HERO | One fresh creation-to-100 campaign with inspectable runs, losses, checkpoints, and report |
| Class coverage | One fresh HERO per base class across multiple races; source-audited legal subclass behavior |
| Race coverage | Each legal race/base-class pair reaches 10; sex is cosmetic, not another coverage axis |
| Visible operation | Same behavior through Mudlet in a Windows VM, with commentary, artifacts, restart, and failure recovery |
| Personality and analysis | Humanlike feedback grounded in actual events and configured persona |

Extend only the next needed band after lower-band executable proof. AI decision-
making remains deferred until deterministic behavior is replayable; generated
personality does not imply executable action authority.

## Measurement And Architecture

Report net XP, useful objective kills, losses/deaths, and connected time; report
reset, setup, and development time separately. Never present maintenance XP or
static coverage as autonomous progression. A safe checkpoint is recovery proof,
not a successful levelling segment.

Keep one observation/state/action/acknowledgement/outcome path. Consolidate
touched behavior into existing focused modules with timeline regressions.
Avoid wholesale rewrites and competing controllers. A failed experiment needs
a replay and changed input before a bounded retry, not erased history or a
character-name exception.

## Preserved History

The [previous roadmap](docs/history/ROADMAP_2026-09-08.md) retains the original
practical milestones, exit criteria, and subsequent cycles. The
[operating instructions](docs/OPERATIONS.md) retain commentary, fail-fast,
process, source-refresh, and local-only commit requirements.

### Current Frontier: Kestrel (September 10, 2026)

Runs 12948-12986 now supply the current frontier evidence: a secretary
exceeded the dagger damage budget, food was recovered, the Forest bear route
reached a real target before rejecting a crowded room, and the flight shop
refused service at fame -12. Funding, loot sale, and watchman research all
completed safely. Moria sanctuary attempts were exhausted without acquisition;
run 12966 was interrupted and recovered, while runs 12967-12970 supplied food
maintenance. Run 12971 completed the corrected nine-endpoint Moria fallback,
acquired purple potion 4050 from source carrier 4055, and returned safely.
Runs 12972-12978 added safe resource and target probes. Run 12979 confirmed
the potion ledgers survive startup reconciliation; run 12981 replenished food,
while runs 12980 and 12982 reached current-band targets and rejected them on
source-backed damage bounds. Run 12984 reopened the Forest upgrade only after
fresh source damage evidence, reached room 18027, and withdrew from a crowd of
source-registered mosquitoes and wasps. Runs 12985-12986 refreshed the source
revision and food reserve, then reached the Solace Secretary route via the
exact `where drunk` preflight before withdrawing on its source HP budget.
Kestrel is level 24 at 332,692 XP, alive at healer 3054, with 2,979
copper-equivalent and one pouch reserve at checkpoint 40039. Do not widen the
level band or claim sustained progression until the protection marker is
cleared by a positive net-XP journey.

The chooser now filters plain high-HP candidates unless a legal source-backed
or sanctuary-protected live probe is available. The protected path requires
the source lower HP bound to fit Kestrel's audited output and still withdraws
when live GMCP reports a target above the fixed action budget. A source-audited
passive target can now reach that probe through exact `consider`, sanctuary,
and opener sequencing; scripted attackers, special/armed targets, and
uncertain routes remain blocked.

### Current Frontier Correction: Passive HP-Fuzz Probe Liveness (September 11, 2026)

The protected HP-fuzz admission previously rejected every passive target
before the runner could issue the exact `consider` and open combat needed to
obtain authoritative GMCP HP. It now admits only a source-identified,
non-scripted, unarmed, non-special passive target with an exact selector;
scripted, armed, special, ambiguous, and unaudited-route cases remain blocked.
The starter keeps the live HP ceiling and fixed output budget authoritative
after the opener. Compilation is clean, the full offline suite passes **5,560
tests**, and offline selection now identifies the source-validated passive
golem route as the next Kestrel hunt after maintenance. This is liveness and
selection evidence only; no new live kill, sustained XP, or HERO proof is
claimed.

### Alignment Evidence Correction (September 11, 2026)

The upstream `update.c` path sends the real clamped player alignment through
`Char.Worth` from level 10 onward and deliberately sends `50000` below level
10. Run **13036** captured `alignment: 1000` for Kestrel at level 24, ruling
out a GMCP transport defect. The policy bug was local: it compared the NPC
hunt target's alignment to DD4's player-fight assistance rule. The corrected
gate uses the player's revealed alignment. It mirrors the exact
`violence_update` good-vs-good threshold of **350** for a bystander and keeps
the `spec_guard` special's separate **300** threshold distinct. Masked or
invalid values remain unknown, and neutral or unknown bystanders remain
material hazards. Focused alignment, hunt, starter, observation, and campaign
regressions pass; this changes safety admission only and adds no progression or
HERO proof.

### Target-Specific Output Revalidation (September 11, 2026)

The current checkpoint is **40247**, with Kestrel at level 24 and **331,489
XP** in healer room **3054** after run **13039** rearmed the source school
jewel-studded dagger. Recomputing the shared estimator from the live skill,
damroll, swiftness, and weapon state gives a conservative ceiling of **396**
damage. The passive golem evidence from run **13034** remains exact: mobile
**1303**, room **1312**, live **545/545 HP**, and an earlier **318**-point
output budget. It therefore remains closed because the improved loadout still
does not cover the observed target.

The campaign now stores that target identity, observed HP, source revision,
old output budget, and weapon in the current-reboot loss record. A strictly
stronger output can earn one retry only for that same source mobile and room,
at the same level and reboot, after all ordinary route, current-band, funding,
and protection gates pass. The retry marker is consumed at live segment start;
it cannot become a general retry loop after interruption or another loss.
This is tested offline and is not live revalidation or HERO proof. The next
productive gate is a source-verified weapon upgrade such as the bear claws,
followed by one bounded golem revalidation if the live evidence still matches.

### Latest Checkpoint: Sanctuary Reserve Repair (September 11, 2026)

Policy revision 273 repaired the exact markerless state left by the previous
second-reserve handoff. Run **13016** selected the corrected recovery policy,
used source mobile 4055 in Moria as an explicit missing-resource target, and
collected the second purple potion without consuming either reserve. The target
was below-band for XP, so its 110 XP is maintenance evidence only. Kestrel
returned to healer room 3054, slept, saved, and quit safely; segment **12566**
and checkpoint **40159** record level 24 at **332,627 XP**, two verified purple
reserves, and no new loss. Campaign tests pass **1,421** and the full offline
suite passes **5,515**. The next acceptance gate remains a productive
current-band journey with positive whole-session net XP; HERO is unproved.

### Current Frontier Update: Protected Level Ceiling (September 11, 2026)

The source-ranked selector now returns Mr. Smithy (mobile **2413**, room
**2406**) as the next executable Kestrel probe. His nominal level is 25, with
DD4 source fuzz allowing a live level through 27 and an estimated HP range of
**316-945**. The new admission is deliberately narrow: source-safe sentinel,
sanctuary reserve, fitted lower-bound output, and a maximum live level of
character level plus two. The endpoint compares the exact GMCP enemy record to
Kestrel's **318-point** opener-plus-repeat budget before sanctuary or attack;
an over-budget load must withdraw without spending the potion.

Runs **13019-13028** supplied maintenance and boundary evidence rather than
progression: food and sanctuary recovery succeeded, the Forest wandering bear
did not yield its required claws, Circus and Mirror Realm fame targets were too
strong, New Ofcol was absent in bounded search, and the questmaster refused a
new quest while fame was negative. Kestrel is level 24 at **332,469 XP**, alive
at healer room **3054**, checkpoint **40205**. The affected campaign, starter,
and progression suite passes **3,341 tests**; the full **5,523-test** result
predates the two newest regression cases. The next gate is one bounded live
Mr. Smithy probe, followed by positive whole-session XP if the loaded target
fits the live budget.

### Evidence Correction And Ground Gear Audit (September 11, 2026)

The planned Mr. Smithy experiment is complete and closed. Run **13029** found
the passive target at **474/474 HP** against Kestrel's **318-point** audited
output budget; the protected retreat produced a real net **-384 XP** without a
kill or death. Runs **13030-13032** restored sanctuary and food state. Kestrel
is level 24 at **332,185 XP** in healer room 3054, with checkpoint **40225** as
the latest durable state. Run **13033** continued Dorrik safely and recorded
one **150-XP** below-band rolling-rock maintenance kill, not progression.

The source equipment report now applies the shared route-safety audit to direct
ground resets and exact source carriers. Clean reachable placements retain a
`promising` route record; doors, movement requirements, aggressive/program/
special hazards, and crowds are explicit hazards or autonomy rejections.
Unranked, unreachable, and future mob drops remain `source-only` analysis and
cannot authorize a campaign action. Carrier execution additionally requires a
matching source hunt candidate and post-kill loot/equip verification. The full
offline suite passes **5,543 tests** and the affected suite passes **3,637
tests**. The next acceptance gate remains a source-approved, current-band
productive journey; no target is being forced while the saved checkpoints are
blocked by recovery or funding.

### Familiar Opening Handoff Acceptance (September 12, 2026)

Run **13052** exposed a timing loss: the pony was ordered to attack an exact
easy target, the player cast, and the pony's next automatic round finished the
target before the player could act again, producing zero objective XP. The
source-ranked planner now enables a narrow handoff when the audited player
output covers the target HP ceiling. It confirms one familiar probe attack,
orders and confirms the familiar's withdrawal, and only then opens player
combat. Run **13053** live-proved the repair on Granny Jenkins: the pony
withdrew, Astrevo killed personally for **168 objective XP**, and the character
returned safely at checkpoint **40298** (level 8, 29,505 XP). The full offline
suite passes **5,580 tests**. This is a live timing/XP acceptance, not
sustained progression or HERO proof; the next gate is continued positive
whole-session XP with the same bounded controls.

### Failed Familiar Withdrawal Guard (September 12, 2026)

Run **13057** exposed a second timing edge after the successful handoff: the
charmed pony exhausted three flee/sleep withdrawal pairs without positive
departure evidence, but the selector still fell through to a player spell.
Granny Jenkins died for only **28 XP**, despite the run recording the
withdrawal failure. The starter now handles a retry helper that exhausts its
budget in the same decision cycle, marks the stop skipped, and enters healer
recovery before any player opener can be emitted. The focused familiar suite
passes **1,521 tests** and the full offline suite passes **5,581 tests**;
compilation is clean. Run **13058** then stopped safely at the city-route
preflight with no combat command, while live proof of this exact failed-flee
branch remains pending. HERO and sustained progression remain unproved.

### Continued Level-8 Progression (September 12, 2026)

Runs **13059-13061** added **280 XP** through two clean Circus kills (+172
and +108) and one target-absent rejection. A subsequent source-ranked check
stopped at the city-route preflight, and later selection correctly held at
provision funding because no source-safe current-reboot funding target was
available. Astrevo remains alive at healer room **3054** with five pies, water,
full resources, and **30,108 XP** at checkpoint **40329**. The next live gate
is another fresh target or funding observation; sustained progression and HERO
remain open.

The refreshed source was used by Dorrik's bounded run **13064**, which selected
the tree-sprite sentinel, recorded its absence at room 18564, and returned
without XP or loss. A follow-up reached the existing sanctuary-recovery
cooldown at checkpoint **40351** without opening gameplay. This confirms safe
rotation and cooldown behavior only; Dorrik remains level 25 at **379,568 XP**.

### Public HERO API Liveness (September 12, 2026)

The public `run_hero_request` wrapper now defaults to the same 180-second live
segment cap as the CLI and treats a missing cap as bounded. Explicit larger
positive runtime and reset budgets remain available for controlled probes, while
implicit reset waits stay disabled for bounded calls. The full offline suite
passes **5,590 tests**. This closes an API-level hang risk but does not advance
the live level frontier or establish sustained progression.

### Clean Astrevo Continuation (September 12, 2026)

Run **13070** reached the exact source-ranked Bearded Lady instance after a
fresh Midgaard city preflight, considered it at the observed level, and Astrevo
personally killed it for **139 objective XP**. The mage returned to healer room
**3054** without death, loss, or a familiar handoff, reaching checkpoint
**40378** at level 8 and **30,179 XP**. This is fresh positive live evidence, not
sustained progression. The source-backed `flee Fear` repair remains unaccepted
live because this target did not require a familiar; the next gate is an
eligible familiar-required encounter followed by another positive level-band
segment.

### Field-City Cooldown (September 12, 2026)

Run **13071** found the source greeter in three current Midgaard route rooms
after the bounded preflight waits and stopped at healer room **3054** before
any funding or hunting action. The campaign now treats that same-level,
same-reboot `campaign_field_city_preflight` evidence as the explicit
unavailable policy **field-city-route-blocked**. A subsequent invocation opens
no live worker until fresh world-time or route evidence changes the state,
preventing repeated calls from replaying an unchanged obstruction. The follow-up
resume selected that unavailable policy at checkpoint **40384** without opening
a live connection or transcript. This is a liveness and evidence improvement,
not progression or HERO proof.

### Current Kestrel Frontier: Alignment Parity And Reset Retry (September 12, 2026)

Runs **13089-13090** tested the paired food-reserve rule. Run 13089 exposed
premature consumption after the first object-only stop; the starter now retains
all outstanding reserve items until the complete paired route is satisfied.
Run 13090 then returned one verified toadstool without eating it when its
companion was not source-safe under the movement budget. Runs **13091-13092**
used one bounded reset retry: Moria's sanctuary carrier was absent on the live
route, and the follow-up world-time probe completed safely. Kestrel's current
checkpoint is **40553**, level 24 at **331,521 XP**, full health in healer room
**3054**, with GMCP alignment **1000**.

The current source checkout is `c8c4ddc`. Its ordinary thief estimator gives a
**318-point** conservative opener-plus-repeat ceiling. The readiness report
finds 93 autonomous-safe candidates and 1,154 output-fitting candidates, but
zero passing all three filters. Moria's purple-potion placement remains
source-rejected because its reset permits two matching carriers; source-only
gear and below-band maintenance do not authorize progression. The public
inspection commands now read nested GMCP alignment consistently with campaign
gates and show the interpreted value. These fixes improve evidence parity and
liveness, but no new kill, sustained positive whole-session XP, level gain, or
HERO proof is claimed. The full offline suite passes **5,631 tests**, including
**68** CLI tests.

### Bounded Forest Gear Retry (September 12, 2026)

When no source-safe current-band target fits Kestrel's audited output, the
explicit stalled-run path now admits one exact Forest bear-claw upgrade retry.
It is limited to the healer checkpoint, level 10-29 thieves, the source
revision and reboot scope, and the existing food, water, movement, weight,
protection, route, and live combat gates. The marker is written before the
connection and closes after the attempt, including a failed or interrupted
expedition. This removes an unnecessary reboot-local wait from a materially
useful gear objective without turning a source-only placement or below-band
kill into progression permission. Focused campaign coverage passes; the next
live step is one bounded retry and inspection of its durable outcome.

The first live recheck was run 13106. Kestrel reached Forest room 18027 and
the exact source crowd gate, but the return-home handoff was falsely marked
failed because the text parser had not yet advanced its room cursor when the
recall decision was issued. The runner now records the authoritative
decision-time room and waits for the asynchronous recall acknowledgement. Run
13107 live-validated the repair: the response returned Kestrel to the Temple
of Midgaard, healer recovery completed, and checkpoint 40551 was saved at
level 24 with 331,521 XP. The next step is progression selection from that
safe checkpoint, not another recovery retry. The full offline suite passes
**5,631 tests**.

The selector repair now registers a sanctuary-backed protected HP-fuzz probe
as a distinct candidate pool. It selects the source-safe Tree Sprite frontier
for Kestrel, but that route requires flight; live run 13112 correctly stopped
at the Magic Shop's negative-fame refusal and saved checkpoint **40553**.
The readiness report now marks such candidates with `protected_hp_probe`,
keeping the strict full-output and live-GMCP gates visible.

### Current Frontier: Thief Lockpick And Fine Dagger Plan (September 12, 2026)

The source-backed campaign now has its first multi-step upgrade plan. For a
Thief at level 26 or higher, it verifies lockpick object **38** at Dave's shop
(mobile **3050**, room **3120**), requires the source prerequisite chain
`thief base` 30% then `pick lock` 60%, and replays the official Shadow Keep
route to the locked west exit in room **16619**. The exact target is smuggler
mobile **16609** in room **16635**, whose reset equips fine dagger object
**16614**. The route is source-replayed at 266 raw movement and 74 flying
movement. Its `spec_thief` economic special is bounded by the existing
250-copper maximum exposed loss, and the normal sanctuary, live HP, damage
window, exact identity, loot, equip, and healer-return gates remain active.

This is an executable offline plan, not a live claim: the purchase, practice,
door, kill, and dagger-loot path still needs one bounded live acceptance run.
The source checkout is `622d5de`; the full offline suite passes **5,645
tests**. The master acceptance gate remains sustained positive whole-session
progression across arbitrary source-legal identities through HERO 100.

### Current Frontier: Lockpick Funding Exception (September 13, 2026)

When Kestrel reaches the level-26 Shadow Keep plan without enough copper for
lockpick object **38**, policy revision **282** can select the exact Shargugh
carrier (mobile **6115**, room **6100**, iron ring object **6114**) as a
source-required maintenance expedition. The route is source-replayed at 12
commands and 56 movement, with `where drunk` retained before transit. Its
below-band kill is excluded from progression XP and is admitted only when the
source identity, one-spawn reset, HP/output, capacity, inventory, route-hazard,
and safe-sale checks all pass. Offline coverage is complete; live acquisition
and sustained HERO progression remain unproved.

### Moria Locator Recheck: September 13, 2026

Run **13119** showed a live locator race: `where hobgoblin` positively listed
two mobile-4055 carriers in `The maze`, but the subsequent listing at source
room **4063** was empty. DD4's `where` output is visibility-filtered but gives
room names rather than VNUMs, and mobile 4055 is allowed to wander within its
area. The starter now grants one source-mapped same-room `look` recheck after
a positive locator refresh with no route to move, then preserves the existing
exact target and `consider` gates. This improves liveness without converting a
stale or ambiguous locator into an attack permission. No new kill, XP, or HERO
proof resulted; the full offline suite passes **5,646 tests**.

### Moria Southern-Maze Locator Coverage: September 13, 2026

The next live evidence is now explicit: run **13120** found no live Shargugh
for the lockpick funding attempt, while run **13121** found the Moria carrier
in-area but acquired no potion. Source revision `622d5de` maps the safe,
reachable `The maze` destinations to rooms **4063**, **4066**, and **4065**.
The locator excludes the western poisoner/sentinel rooms **4057**, **4058**,
and **4062**, and the aggressive branch at **4067**. The deep search now
retains exact room listing, source identity, visibility, consider, hazard, and
required-loot gates while narrowing to all three reachable rooms. Policy
revision **283** reopened only the prior same-boot, no-loss level-24 terminal
result, preserving its old attempt evidence. Live run **13124** then followed
the widened graph, killed source mobile **4055**, acquired the required purple
potion, and returned Kestrel safely to healer room **3054** for **100 XP**
without a death. Maintenance runs **13122** and **13123** acquired `some grain`
from Crystal rooms **10036** and **10038** without changing XP. Kestrel is
level 24 at **331,279 XP**. Offline coverage passes **5,648 tests**; sustained
progression and HERO remain unproved.

### Lockpick Funding Shortfall Selection: September 13, 2026

The campaign now keeps a selected `provision-funding` handoff actionable when
generic source-frontier fallback would otherwise report no hunt, including
the level-24 Thief's outstanding Shadow Keep lockpick requirement. Candidate
ranking also uses the known copper shortfall: a source-safe carrier whose
audited coins cover the requirement outranks an insufficient 50-coin carrier.
The rule only filters already eligible candidates; it does not bypass route,
multiple-attacker, sanctuary, movement, output, or saleability gates. The
real-source Solace carrier therefore remains closed for Kestrel's current
state.

Run **13125** selected the repaired funding policy and completed a live Midget
kill for **40** below-band maintenance XP and **50** copper, with safe healer
return and no loss. Runs **13126-13127** completed Circus and Mirror Realm
fame-recovery checks without XP change. Run **13128** then completed the second
permitted large-hobgoblin carrier kill, acquired the purple potion, and added
**100** XP with safe healer return. Kestrel is level 24 at **331,419 XP** in
healer room **3054**, checkpoint **40618**. The full offline suite passes
**5,650 tests** and compilation is clean; this remains bounded evidence, not
sustained progression or HERO proof.

### Funding Handoff Repair And Live Guard Attempt: September 13, 2026

The campaign now preserves an active food, flight, or Shadow Keep lockpick
funding objective when an already-excluded city maintenance policy would
otherwise become a generic unavailable frontier. The existing source-safe
candidate selector still applies the full identity, route, movement,
protection, output, and saleability gates; the repair changes policy ordering
only. The focused funding cases pass, and the full offline suite passes
**5,651 tests** with compilation clean.

Run **13132** exercised the repaired handoff against the source-backed
patrolling guard (mobile **9400**, room **9400**). The kill produced **90**
below-band maintenance XP and **1 copper** of realized proceeds, with no death
or XP loss, then returned Kestrel to healer room **3054** at checkpoint
**40633**. The lockpick shortfall is still open; the next policy correctly
prioritizes a second purple sanctuary reserve before another funding or
progression route. This is live maintenance evidence, not sustained
progression or HERO proof.

### Lockpick Shortfall Ahead Of Flight Retry: September 13, 2026

The latest checkpoint exposed a second ordering edge after the prior funding
repair: `policy_for` could select a pending `buy-flight` retry before the
campaign evaluated an active Shadow Keep lockpick shortfall. The campaign now
preserves `provision-funding` for a fed, alive, non-combat character whenever
that concrete shortfall is still below its source cost. The source-ranked
funding selector remains responsible for exact identity, route, movement,
protection, output, saleability, and below-band admission; this is policy
ordering only.

Run **13133** acquired Kestrel's second purple sanctuary reserve and added
**100** maintenance XP with a safe healer return. Runs **13134-13135** reached
the bounded Circus and Mirror Realm fame routes but recorded retryable source
boundaries with no kill or XP change. Kestrel is level 24 at **331,699 XP**,
checkpoint **40642**, with **527 copper** toward the **1,000-copper** lockpick.
The direct live-checkpoint audit now selects `provision-funding`; the full
offline suite passes **5,652 tests** and compilation is clean. Sustained
progression and HERO proof remain open.

### Funding Precedence Live Check: September 13, 2026

Run **13136** exercised the pending-flight precedence and completed the
source-backed on-duty-guard funding route for **110** bounded maintenance XP
and **1 copper**, with no sale, death, or XP loss. Kestrel returned to healer
room **3054** at checkpoint **40645**, level 24 and **331,809 XP**. The ending
ledger has one verified purple sanctuary reserve and **528 copper**; the next
policy correctly returns to Moria sanctuary recovery before another funding or
progression attempt. This remains maintenance evidence, not sustained HERO
progression or HERO proof.

### Moria Reserve Recheck: September 13, 2026

Run **13137** re-entered the source-ranked Moria sanctuary-recovery route at
level 24. The required second purple was not present, so the segment ended
cleanly with no kill, XP change, death, or loss and returned Kestrel to healer
room **3054** at checkpoint **40649**. The ending ledger remains one verified
purple reserve and **528 copper**; the selector now rotates back to the active
lockpick `provision-funding` handoff. This is a bounded source boundary, not
sustained progression or HERO proof.

### Loose Sanctuary Reserve Precedence: September 13, 2026

Run **13142** confirmed the Magic Shop's -12-fame refusal. Run **13143** then
recovered a large hobgoblin's purple potion for **90** maintenance XP and
returned safely to healer room **3054**. Because the potion was loose in
inventory, the selector now prioritizes `audit-combat-pouch` ahead of money
container cleanup and lockpick funding. Run **13144** stowed it in the worn
combat pouch with no XP change, death, or loss. Checkpoint **40674** is level
24 at **332,149 XP** with one verified purple reserve and **532
copper-equivalent**. The full offline suite passes **5,653 tests**; sustained
progression and HERO proof remain open.

### Protection Wait Liveness Repair: September 13, 2026

The reset-aware runner now defers the exact current-level, current-reboot
protection boundary when no sanctuary reserve or executable independent route
is available. The first live attempt stopped at checkpoint **40717** without
opening a gameplay connection, waited the configured **180 seconds**, and
completed maintenance world-time run **13150**. No newer reboot was observed;
the next attempt selected `provision-funding` and stopped without repeating the
refused flight purchase. Kestrel is level 24 at checkpoint **40724** with
**639 copper-equivalent** toward the **1,000-copper** lockpick. The full suite
passes **5,656 tests**. This is liveness and evidence progress, not sustained
progression or HERO proof.

### Route-Scoped City Quarantine And Mage Continuation: September 13, 2026

The field-city cooldown now retains the exact blocked source policy. A later
same-level, same-reboot invocation blocks only that policy; an alternate
source-ranked route performs its own bounded city preflight, while policy-less
legacy evidence remains globally conservative. Run **13162** live-validated
this repair for Astrevo: the exact Circus target yielded **108 objective XP**
and returned safely to healer room **3054** at checkpoint **40787**. No death or
XP loss occurred. The cross-module suite then passed **5,667 tests**; Astrevo
remains level 8 and sustained progression through the level-10 trainer
transition remains open.

### Source Refresh And Special-Contract Audit: September 13, 2026

The source mirror was refreshed to `80cad011b8c17b5ffc8828edae9182271bf7e46e`.
The current DD4 contract now explicitly includes `AFF_MINDLESS` and resolves
mobile procedures through three weighted template slots plus area
`#SPECIALS` `M`, `N`, and `P` overrides. The source parser tracks nested C
initializer braces, preserves explicit probability vectors, and includes
inherited template procedures in route hazard analysis. A full source smoke
parse finds 4,138 mobiles and 1,629 effective special-bearing mobiles; the
offline suite passes **5,692 tests**. Existing live checkpoints remain
evidence from their recorded source revision, and no new live progression or
HERO proof is claimed.

### Capacity Metadata And Route Rotation: September 13, 2026

Campaign startup now rebuilds pending capacity-container metadata from
chronological segment evidence. Later successful claims suppress stale legacy
restore entries, and a carried sack/backpack/girdle is never repeatedly
reintroduced. If an exact live claim is rejected for weight, the starter may
perform one healer-side `eq all`, remove/lodge relief action, and one claim
retry. This remains a bounded maintenance action.

The source-ranked selector no longer uses its last-policy fallback to bypass
retry-exhausted, throughput-limited, or current-reboot crowd evidence. Run
**13190** proved the large-sack claim after lodging an obstructing object; run
**13191** banked maintenance currency; and startup recovered interrupted run
**13192** before selecting Moria. Checkpoint **40956** is level **8** at
**31,513 XP** in healer room **3054**, with a safe city-departure deferral and
no new loss. The full offline suite passes **5,701 tests**; sustained
progression, the level-10 trainer transition, and HERO remain open.

### Deep Moria Resume And Level-24 Frontier: September 14, 2026

Bounded deep Moria sanctuary runs now persist one verified same-boot route
cursor when a runtime cap interrupts a quiet waypoint. A later invocation may
rebuild only the audited bridge from room 4064 to that waypoint and continue
the unfinished leg; combat, route hazards, explicit aborts, malformed cursors,
and reboot changes invalidate the cursor. Unit, campaign, and checkpoint
storage coverage protects this contract, and the full offline suite passes
**5,770 tests** with clean compilation.

Live runs **13263-13264** confirmed the 4064 large-hobgoblin target absent,
including after one bounded reset wait. Run **13265** then completed the deep
Moria circuit, killed the exact large hobgoblin with Kestrel's piercing weapon,
and added **100** maintenance XP without loss or death. Runs **13266-13267**
tested the independent Circus and Mirror Realm fame routes; the former
rejected the ticket clerk at a 1,353 HP ceiling against the 318-point output
budget, while the latter rejected the moose on live `consider`. Kestrel is
level **24** at **331,364 XP**, safe in healer room **3054**, and fame remains
**-12**. The next engineering frontier is accessible damage/gear improvement;
HERO proof remains open.

### Deep Moria Dispatcher Reconciliation: September 15, 2026

Policy revision **302** prevents an already-reconciled level-24 Moria recovery
from falling back to the generic one-room reserve executor. Live run **13275**
opened all **11** source-audited stops, including rooms **4064**, **4152**,
**4071**, and **4074**, then returned safely to healer **3054** without finding
the purple potion or changing XP, fame, or reserve state. The old terminal
result remains nested in the checkpoint for auditability. The full campaign
suite passes **1,539 tests**; sustained progression and HERO proof remain open.

### Text-Only Combat Engagement Guard: September 15, 2026

DD4 area files use aggression descriptions including “grunts as he takes a
swing at you”. The observation parser now maps these source-backed variants
to `combat_started`, preventing the starter from continuing familiar setup
after a target has already engaged during route arrival. The full suite passes
**5,808 tests** with clean compilation.

Live run **13320** captured the original failure and two 50-XP losses; its
incidental kill was excluded. Run **13321** then stopped safely at the Moria
pre-entry crowd, and run **13322** added **232 XP** from Granny Jenkins. The
following three-segment batch added **196 XP** from two gnome-woman kills.
Astrevo is at checkpoint **41669**, level **9**, with **33,387 XP**. The
ordinary fame gate remains six or more levels above the player, and HERO 100
is unproved.

### Level-9 Fame And Sanctuary Frontier: September 16, 2026

The policy graph now preserves DD4's strict ordinary fame threshold: the
victim must be at least six levels above the player. A required-loot sanctuary
carrier one level above the character is included in source ranking, allowing
the level-9 Moria carrier to be considered. When an ordinary current-band
target needs protection, level 9 and other pre-deep-band characters use the
shallow Moria recovery policy; the established level-16/17 blindness-special
and level-19+ deep policies are unchanged.

The full offline suite passes **5,810 tests** with clean compilation. Astrevo
remains safely checkpointed at **41690**, level **9**, with **33,691 XP**;
the current reboot's bounded reset waits are exhausted. The next live attempt
must wait for fresh reboot evidence rather than replaying the closed frontier.

### Fresh Source Target Probability Guard: September 16, 2026

Fresh autonomous ordinary targets now need at least a 50% source-fuzz
probability of landing in the useful XP band before they can consume a field
segment. This keeps the HELP FAME six-level rule effective during source
ranking as well as at live `consider` time. Productive routes and explicit
familiar, invisibility, and revalidation probes retain their own bounded
exceptions. The complete campaign module passes **1,558 tests**; the next
frontier remains a fresh executable route beyond the current level-18 blocker.

### Flight Frontier Preference: September 16, 2026

The no-flight fallback now compares fresh candidates by useful source-fuzz
probability. A ground target no longer displaces a materially stronger
flight-required target merely because it avoids flight preparation; productive
ground routes and equal-band ground choices retain priority. This aligns the
selector with DD4 movement economics and the master XP-per-time objective.

### Mage Output Chain Extension: September 20, 2026

The source-backed mage plan no longer stops at burning hands. The capability
registry, combat timing acknowledgements, and output estimator now cover
shocking grasp, lightning bolt, colour spray, fireball, and acid blast with
their DD4 prerequisites, mana costs, and save/resistance-aware bounds. Training
gate entries carry the dependent skill and only advance when the live teacher
listing exposes that next step, preventing premature practice spending. Shield
and stone-skin prerequisite gates are recorded as well. Focused capability,
timing, training, and output tests pass; the chain remains offline evidence
until a bounded Aeloria run validates a live transition.

The level-18 audit in run **13420** recorded the teacher's learnable list as
`ventriloquate`, `summoning magiks`, `enchantment magiks`, and `mana control
disciplines`. None is a current mage damage or mitigation gateway, so Aeloria
retained two physical and two intellectual practices and returned to healer
room **3054**. The negative listing is now durable campaign evidence and will
be rechecked only when the level or reboot scope changes.

### Live Gear Hazard Quarantine And Thief Rotation: September 20, 2026

Run **13424** exposed a gap in the Thalos long-dagger maintenance contract:
an aggressive wandering lamia entered the route, disarmed Serevian, and caused
**339 XP** of bounded withdrawal loss before healer recovery. The route is now
registered as an isolated, sanctuary-required carrier objective, and all three
progression entry points refuse it without a verified sanctuary reserve. Runs
**13425-13426** proved the repair: Serevian safely rearmed with the Midgaard
dagger, then killed the level-11 Air griffin for **270 eligible XP**. Run
**13427** recorded a clean New Ofcol absence and rotated without replaying the
area. The fame rule remains the HELP FAME six-level threshold, and HERO 100 is
still unproved.

Run **13428** then exposed a liveness defect after a below-band Circus funding
target fled: the follow-up absence response left the resource stop open until
the progress watchdog fired. The starter now closes that stop only when an
engagement has started, the target is absent on the bounded re-check, and the
stop is explicitly source-coin or required-loot work. Offline coverage is
green at **1,432 starter tests**, **537 progression tests**, and clean
compilation. Live run **13430** regressed the repaired funding route: Serevian
killed the source-verified Midget for **40 non-progression XP**, recovered the
purse coins, returned safely to healer **3054**, and checkpointed at level 11
with **51,118 XP**. Follow-up runs **13431-13436** completed cleanup and flight
preparation, added **332** and **248** eligible XP from two further griffin
segments, and recorded two clean New Ofcol rotations. Serevian is now at
checkpoint **41954** with **51,698 XP**. HERO 100 remains unproved.

### Locator Route Re-rooting: September 20, 2026

Run **13436** exposed a source-ranked locator defect: after a positive `where`
result removed intermediate target stops, a later destination could retain a
route VNUM relative to an older origin. The live runner reached room **621**
and then treated room **632** as a direct exit even though the audited source
path returns through rooms **618**, **668**, **611**, **608**, **605**, **602**,
**601**, and **625**.

The starter now re-roots compacted destination-guided segments against the
source graph only when every replacement room is already present in the
registered route evidence. Closed-door and randomized paths remain
fail-closed, and missing source paths still use the ordinary live-exit abort.
The exact disconnected-waypoint replay is covered by the starter suite.

Offline verification is green at **1,433 starter tests** and **1,566 campaign
tests**, with clean source reproduction and compilation. Run **13439** resumed
Serevian safely at checkpoint **41963**, level **11**, with **51,748 XP** in
healer room **3054**; the current reboot's exhausted sanctuary boundary
prevented another gameplay socket. HERO 100 remains unproved, and the next
live frontier is still a fresh executable level-11 route.

### Skipped-Stop Re-root And Live Identity Evidence: September 20, 2026

Run **13445** exercised the next failure shape after locator narrowing. The
citizen circuit reached rooms **637**, **642**, **646**, and **647** after the
live source-identity gate found both citizen VNUMs **617** and **618** reachable
in the same room. The runner correctly skipped the ambiguous target and
re-rooted the following registered stop from the actual live waypoint, so it
never repeated the prior impossible room-**632** to room-**651** transition.

The segment returned safely to healer room **3054** at checkpoint **41975**,
level **11**, with **51,748 XP** and no kill, death, or XP loss. The route repair
is restricted to source-registered rooms and leaves unproven or closed paths
fail-closed. The ordinary HELP FAME rule remains unchanged: ordinary fame
targets begin at player level plus six; source-famous targets are separate.
Fresh practice repair is also bounded behind active provision-funding and
affordable-flight gates so urgent resources retain priority. Verification is
**1,434 starter tests** and **1,566 campaign tests**. HERO 100 remains unproved.

### Runtime-Boundary Cleanup And Funding Evidence: September 20, 2026

Runtime-boundary cleanup now takes precedence over stale consider, equipment,
and route-wait acknowledgements once the live character is commandable and
combat-free. This preserves the bounded recall, room-3001 north step, healer
recovery, save, and quit path instead of misclassifying safe cleanup as a
`no policy decision` watchdog failure. The full starter suite is green at
**1,435 tests**, with clean compilation.

Run **13446** remains the historical failure; run **13447** proves the cleanup
repair. Run **13448** killed source mobile **4408** (the Midget) for required
funding, yielding **30 XP** and coins. Run **13450** acquired Katrina the
Shepherd's required funding drop for **50 XP**. Run **13452** found Katrina
present at room **2415**, rejected her with live `consider` as below-band, and
returned without combat, loss, or XP change at checkpoint **41988**, level
**11**, **51,828 XP**. HERO 100 remains unproved.
### Bounded Last-Chance Frontier Probes: September 20, 2026

The ordinary fame rule is now recorded exactly as DD4's HELP entry and source
logic require: `victim.level - player.level > 5`, making level 31 the first
ordinary fame band for Dorrik at level 25. Fame recovery is not being conflated
with ordinary XP progression or the separate source-famous path.

Campaign selection now keeps measured productive repeats and fresh candidates
with at least 50% useful source-level fuzz probability ahead of weaker probes.
Only after those pools are exhausted, and only with a populated source world,
may one fresh candidate in the 25-50% range be tried. The live level and
`consider` response decide XP; below-band results never receive progression
credit.

Runs **13465-13466** exercised this bounded frontier for Dorrik at level 25.
The tree sprite was absent; the copepod route reached its Abyss movement
reserve before the endpoint. Both segments returned safely to healer room
**3054**, with no death, loss, or XP credit. Checkpoint **42027** is therefore
a durable route/resource boundary, not HERO evidence. The next live work is to
improve protection acquisition and shorten source-audited routes before trying
another current-band progression target.
