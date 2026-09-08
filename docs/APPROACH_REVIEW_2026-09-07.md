# Approach Review: 2026-09-07

## Verdict

The transport, credentials, persistence, recovery, source analysis, and public
HERO entry point are substantial working foundations. They are not yet a
successful autonomous levelling product. No character has reached HERO; the
highest recorded frontier is Dorrik at level 25. Astrevo is the fresh-creation
proof track, currently level 8. More policy declarations cannot close that gap.

## Measured Bottleneck

The SQLite segment ledger shows excessive unproductive execution:

| Campaign | Recorded segments | Zero-XP segments | Net XP/minute |
| --- | ---: | ---: | ---: |
| 7, Dorrik | 2,297 | 1,423 | 102.2 |
| 28, Aeloria | 973 | 655 | 16.5 |
| 30, Praelarran | 1,958 | 1,157 | 86.5 |
| 31, Serevian | 741 | 410 | 57.8 |

These descriptive totals use numeric segment start/end XP and recorded
duration, including travel and maintenance but excluding development downtime.
They are not comparable class benchmarks: levels, equipment, legacy failures,
and starting states differ. Astrevo's source hunts averaged about 95 XP/minute
versus 281 in the compact school loop before this review. Travel amortization
and productive encounter selection are immediate opportunities.

## Refined Execution Strategy

1. Advance Astrevo through levels 9 and 10 using the public resumable entry
   point. Prove trainer handoff, then sustain progression without steering.
2. Use the existing thief, mage, and warrior campaigns to test shared changes
   at their actual frontiers. Do not open hypothetical level-31-plus work while
   executable lower-level blockers remain.
3. Optimize net XP per total session time, objective kills per journey, and
   loss/death rates together. A checkpoint with zero XP is diagnostic evidence,
   not delivery. Report maintenance separately; do not hide it in combat XP/min.
4. When damage or protection is the bottleneck, improve source-backed training,
   equipment, and executable reserves before broadening target risk. When
   travel dominates, combine nearby useful targets. Retain bounded finishing
   attacks and live health/damage judgement rather than globally raising fear.
5. Stop repeating a failed experiment without a changed input. State the
   hypothesized blocker, add a replay, change the software, and compare fresh
   runs. A passing suite alone does not prove the hypothesis in the MUD.

## September 8 Acceptance Result

### Reset Scheduling And Solo Comparison

The next public invocation exposed a scheduling defect: when the current
hunting pool was unavailable, an old `liquidate-loot` crowd won the reset
choice through alphabetic ordering. Current-level source-ranked field crowds
now precede unrelated maintenance crowds, with the same ordering for the
reported wait and explicit bounded retry. Six regressions preserve the
cooldown, old-level, exhausted-route, reboot, and loss-evidence boundaries.
All 4,473 tests pass. This changes retry selection, not combat admission.

The already-running reset invocation completed world-time probe 12762 without
a reboot change. A fresh public continuation then selected Moria. Run 12763
earned 205 XP from two solo centipede kills, acknowledged all five damage
commands without timing out, and returned safely. Run 12764 found Granny
Jenkins alongside another mobile and returned without combat. Run 12765 found
its first Moria target absent and returned on low walking movement, also
without XP. Astrevo checkpoint 39147 is level 8, 27,952 XP, with full resources
at healer 3054 and 3,748 XP to level 9.

These four runs total 338.28 connected seconds for 205 XP: 36.4 XP/minute.
Including the separate 180-second reset wait gives 23.7 XP/minute before local
setup and development delays. Neither figure demonstrates a throughput gain.
The concrete remaining inefficiency is unproductive travel after a productive
trip. Keep measuring complete journeys; do not turn a source-only candidate,
a wait, or a safe checkpoint into progression proof. The critical-spell and
post-death repairs remain separately pending live acceptance. Aeloria stays
at healer checkpoint 39130 with her death-related protection gate intact.
The subsequent Dorrik invocation also stopped before connecting: checkpoint
39149, level 25, 380,076 XP, protection recovery unavailable. This makes the
shared recovery dependency another concrete current-frontier bottleneck,
not a reason to work on hypothetical higher-level policies or clear losses.

### Cross-Character Repeatability Failure

The next public comparison tested Aeloria at her level-18 frontier. Run 12759
found the smithy absent. Run 12760 killed the guardian for 281 XP. Repeat
12761 received a successful burning-hands critical reply ending in
`*CRITICAL HIT*`, which the timing recognizer did not accept. Although the
malformed enemy packet after companion departure was correctly rejected,
the unresolved command suspended additional spells. The fight deteriorated,
escape attempts failed, and Aeloria died, losing 3,768 XP. The three-run
comparison lost 3,487 net XP; no sustained-throughput success is claimed.

The source critical suffix is now recognized and tested for all registered
direct spells. Automatic corpse retrieval and equipment restoration succeeded,
but recovery then alternated sleep and stand because the corpse-recovery
branch kept running after its handoff. It now delegates once to ordinary
healer recovery, which owns the resource wait and eventual wake-up. These
two repairs have focused replay coverage and await fresh live validation.

Aeloria checkpoint 39128 is safe at healer 3054, level 18, 158,168 XP,
218/218 HP, 343/628 mana, and 320/320 movement. Astrevo checkpoint 39116
is safe at the same healer, level 8, 27,747 XP, full resources. Preserve the
death and route quarantine. Next validate critical-reply continuation and
recovery through normal execution, without promoting the failed repeat or
removing its history. The master creation-to-HERO objective remains incomplete.
Final verification passes all 4,467 tests in 151.82 seconds, including the
99-check focused regression selection. No live critical-reply or corrected
post-death handoff acceptance is claimed from these offline results.

### Malformed Input Is Not An Empty Fight

Run 12756 observed actual companion departure followed by malformed GMCP
`Char.Enemies [  ] ]`. The decoder retained the invalid body as a string, but
the policy interpreted its lack of enemy records as an empty fight. It erased
the active target, re-entered the companion admission requirement, and recalled
from combat at full health, losing 68 XP. This was a protocol/semantic-boundary
failure, not evidence that the character lacked the ability to finish.

Enemy snapshots now receive structural validation before caching or dispatch.
Rejected packets produce durable `gmcp_snapshot_rejected` diagnostics while
the raw transcript and last valid fight remain intact. Character-state and
policy replay apply the same guard for legacy events. Valid empty arrays still
end combat. The run-12756 replay now chooses the finishing spell, not recall.

Run 12758 live-validated the exact repair: the same malformed packet followed
the pony's departure, was rejected, and Astrevo cast chill touch to complete the
Granny Jenkins kill for 231 XP. The character returned to healer 3054 with full
HP, mana, and movement. All 4,451 tests pass. This proves departure handoff and
malformed-packet recovery, not the sleep branch or sustained levelling. Keep
measuring the whole journey, including maintenance and healer recovery.

### Final Comparison And Next Gate

Runs 12747-12754 consumed 525.13 connected seconds and lost 28 net XP.
The final run, 12754, acknowledged both player damage commands without a timing
timeout, issued three withdrawal attempts promptly, and correctly recorded the
NPC finishing blow as zero-XP and non-objective. It still failed the progression
acceptance gate. Astrevo checkpoint 39101 is safely in healer room 3054, level
8, 27,584 XP, full 113 HP and 324 mana. Highest roster level remains 25.

The source audit uncovered an additional missing contract: the pony's source
AFF_CHARM flag and `move_char` master-presence guard can prevent departure.
`do_flee` may clear combat before movement fails; `do_sleep` refuses while
fighting and emits a visible sleep message only on success. The controller now
uses that in-place handoff for source-charmed familiars, accepting departure
or sleep, with three acknowledged flee/sleep pairs and a ten-second limit.
The previous guardian trace 12743 contains a real departure, so the static
source flag cannot be treated as a complete explanation of every live failure.
Preserve that discrepancy. The new handoff has source and replay tests but no
fresh live success yet; do not reopen unlimited experiments or claim delivery.

Next: validate positive player XP after the confirmed handoff, then sustain
fresh-track progression to 9 and 10. Compare total connected time, maintenance,
and loss rates against compact solo routes. Companions are an optional combat
tool, not a goal: if preparation/control costs dominate, prefer executable solo
progression. Do not spend further work on hypothetical higher-level policy
coverage while these actual execution contracts remain unresolved.

Final offline validation passes all 4,435 tests in 152 seconds; the focused
timing/companion/pursuit selection passes 158 tests. All live comparison workers
exited and the character is saved safely. This is implementation and regression
evidence, not a successful live sleep handoff or creation-to-HERO proof.

### Confirm Outcomes, Not Requests

Run 12749 resolved duplicate spell injection and issued withdrawal early at
38/60 target HP. The source NPC flee random-failure branch then fired: the
owner saw `Ok.`, but no departure. The familiar remained in combat and killed
the target; character XP stayed unchanged. Run 12750 completed liquidation,
ending safely at checkpoint 39084, Astrevo level 8, 27,584 XP.

The architectural correction is outcome-driven action state. A dedicated
`FamiliarWithdrawal` binds the owned instance, distinguishes acknowledgement
from departure, and retries only acknowledged unsuccessful orders. It permits
three attempts in ten seconds. An
unanswered order never repeats. Pending withdrawal blocks ordinary queued
casts, but not normal survival, automatic combat, or the segment deadline.
Counters and outcomes are durable; identity and pending orders are not resumed.
The recorded failure has replay coverage. Positive player XP is the live gate.

Run 12751 exposed an output-driven scheduling error in the first retry:
a 100-ms grace interval meant no retry occurred before the next NPC attack.
Source `do_order` invokes the follower synchronously, then emits `Ok.` without
a player wait state. Successful departure therefore precedes the acknowledgement
on the same stream. The retry now occurs on that acknowledgement, without
depending on another output tick. Explicit companion damage/death pairs are
recorded as zero-XP, non-objective encounters instead of progression proof.

### Command Execution Is Not A Prompt

Policy 242 addresses the next causal error in run 12745. `comm.c` continues
reading network input during a wait but does not interpret commands until the
wait expires. `do_kill` and the registered direct damage spells impose twelve
pulses at four pulses per second. Background violence output is independent
of that command queue. The old generic prompt acknowledgement unlocked another
cast before the first spell's result, delaying the later withdrawal behind it.

`CombatCommandWindow` now recognizes the actual source damage noun and target
or an explicit refusal, waits through the source lag and next input pulse, and
allows at most one unacknowledged damage command. Ten seconds without an
acknowledgement suspends damage-command injection while automatic rounds,
normal survival decisions, and the segment deadline remain active. A matching
late reply may resume actions after its wait. Survival actions retain priority.
Companion withdrawal runs ahead of attack cooldowns, and a source-budgeted
two-round finishing reserve can withdraw earlier on a fragile target when the
player has sufficient HP, mana, and practiced damage to finish it. Its raw peak
bound is separate from the intentionally absent solo-admission ceiling.

Tests cover the run-12745 timing sequence, all registered direct-spell source
nouns/mana/wait values, missing and misleading replies, the bounded timeout,
urgent withdrawal, and the actual source-generated Katrina stop. Counters are
durable audit evidence; pending commands and clocks remain session-local.
Fresh useful XP through the public HERO command remains the acceptance gate.

The first live attempt, run 12747, exposed an identity-binding regression:
the controller used the room alias `small centipede` while combat output used
the source short description `the centipede`. The initial timeout branch fled
at 109/113 HP, forfeiting 68 XP while receiving 40 partial-damage XP (net -28).
Recognition now uses the source combat name, and uncertainty suspends extra
commands rather than forcing a healthy fight to flee. This follows the central
risk/reward requirement: a parser problem is not evidence of a losing fight.
Run 12748 completed liquidation and returned safely to checkpoint 39076,
Astrevo level 8, 27,584 XP. The loss remains durable regression evidence.

### One Confirmed Companion Lifecycle

Policy 241 closes the second execution path exposed by run 12741. Outdoor
endpoint preparation no longer blindly advances from casting to `group pony`.
It shares `FamiliarPreparation` with staged indoor trips, verifies the actual
source-defined summon line, uniquely identifies the companion, confirms exact
group membership, and waits for the order acknowledgement before player combat.
The mage/witch class authorization and positive practiced value are shared
between campaign selection and execution.

Source `do_cast` fails when the roll exceeds `65 + learned / 3`; failure uses
the recitation wording and consumes half the source mana cost. The spell costs
100 mana. At most three explicitly failed casts may be attempted within 30
seconds, checking remaining mana each time. Missing success without an explicit
failure never triggers another summon, since the source permits duplicates.
The identity remains session-local, attempts are durable audit evidence, and
normal crowd, target, damage, travel, and player-finishing gates remain intact.
The recorded failed-summon sequence now passes replay. The full suite passes
4,365 tests, including 67 companion and 21 pursuit checks.

**Live acceptance:** the public two-segment HERO invocation selected sanctuary
maintenance first (12742, 79.78 seconds, zero XP), then the guardian hunt
(12743, 91.71 seconds). The second run confirmed one summon, exact-instance
group/order acknowledgements, companion withdrawal before the finish, and a
603-XP objective kill of mobile 6313. This is 603 XP over 171.48 recorded
connected seconds, including maintenance, but excluding source preparation
and process startup. No death or XP loss. Checkpoint 39056 is Aeloria level 18,
161,655 XP, healer room 3054, full 218 HP, 543/628 mana, and 288/320 movement.
This proves the positive outdoor companion path and a useful kill; it does
not prove live retry-after-fizzle, a pursuit kill, or sustained throughput.
The next acceptance work applies shared behavior to the fresh level-8 track.

**Fresh-track counterexamples:** run 12744 live-verified a recitation failure,
one retry, successful summon, and exact grouping at level 8. It gained no XP:
`move_char` printed the target room before the owned follower arrived, so the
cached TARGETMODE listing omitted its ID. The runtime now permits one fresh
`look` per room before declaring a confirmed companion absent. Arrival text
alone never proves identity, a changed ID is rejected, and the refresh returns
through ordinary target validation. This repair has replay coverage.

Run 12745 confirmed companion preparation and combat against Katrina, but the
NPC delivered the killing blow before the queued withdrawal executed. The
character received zero XP; do not promote the corpse or collected equipment
to progression proof. Its trace also shows a second chill-touch command sent
before the first cast's reply. The next combat-control work must model command
acknowledgement and source wait-state latency together with remaining companion
damage, instead of relying only on a fixed target-HP withdrawal percentage.
Both runs returned safely; checkpoint 39064 is Astrevo level 8, 27,612 XP,
full HP/mana/movement, healer 3054. Total recorded duration was 184.31 seconds.

The final regression suite passes 4,368 tests (70 companion, 21 pursuit).
Follow-up 12746 found Granny Jenkins with an Ofcol cityguard and rejected the
crowded fight, returning safely after 60.29 seconds with no XP. It did not
exercise the new follower-presence refresh. Current fresh-track checkpoint
39068 is level 8, 27,612 XP, full 113 HP, 320/324 mana, observed 246/220
movement, healer 3054. Keep the source wait-state/command-acknowledgement
repair as the next executable work, not another unmodified combat experiment.

### Execute Learned Flight Before Funding It

Policy 240 implements the concrete gap exposed by runs 12738-12739. It keeps
the existing source selector and applies one explicit learned-flight handoff
after selection. Only flight-related funding/purchase decisions or an eligible
source-ranked journey can use it; foodless, under-recovered, off-site, and
unknown-affect states keep their original decisions. The source-authorized
spell registry covers mage/cleric fly and psionic/monk levitation, including
legal inherited subclass capabilities, and requires a positive practiced value.

The independent `flight.py` state machine uses `handler.c:mana_cost`, requires
standing, bounds preparation to 30 seconds/three concentration attempts/one
affect probe, and accepts only fresh GMCP confirmation after casting. The
campaign records a pending attempt before opening a connection and retains a
ten-minute same-level/proficiency/reboot failure cooldown across subsequent
maintenance. Success clears only superseded flight-funding flags, never food
needs, city hazards, or combat losses. Existing active-flight expiry/refresh
gates remain separate. No character-specific behavior or checkpoint editing is
introduced. The same public HERO command drives the new step.

Fifty-five focused tests pass, including public runner dispatch and simulated
preconnection interruption. A read-only selection from actual checkpoint 39044
now yields `prepare-learned-flight` instead of funding. This is offline evidence
only; the next acceptance test must show the live spell, unchanged currency,
and useful follow-on combat. A short preparation checkpoint is not the final
performance objective. The completed policy-240 suite passed 4,333 tests.

**Live result:** run 12740 confirmed `cast 'fly' self` on the first attempt,
costing 10 mana and no currency (91 copper-equivalent before and after). The
21-tick effect was observed in GMCP, funding flags cleared, and the character
quit safely at the healer after 10.70 seconds. Run 12741 then selected the
Arachnos guardian rather than more funding. It earned no XP in 105.26 seconds:
the outdoor familiar spell returned `You fail to correctly recite the spell!`,
but the legacy path issued `group pony` anyway and later withdrew. No HP/XP
loss; checkpoint 39051 is level 18, 161,052 XP, full resources, healer 3054,
with 17 observed flight ticks remaining. Flight preparation is proven for fly,
not yet levitation; improved useful XP per total session time is still unproven.

The live trace also tightened two boundaries: bind a short runner's missing
reboot stamp to the known campaign reboot when merging the flight attempt, and
recognize the actual DD4 recitation-failure wording for bounded retries. The
dedicated preparation segment is capped at 60 seconds plus normal cleanup,
alongside the 30-second confirmation deadline. Flight casts are classified as
navigation, not combat. The next concrete work is positive confirmation and
bounded retry for outdoor familiar preparation, reusing the staged identity
contract rather than advancing after an unconfirmed summon.

### Make Trained Companions Executable

The next observed capability gap affects both active mages: summon familiar is
trained, but the planner required every target destination to be outdoors.
Source `magic.c:5316` restricts summoning, while `act_move.c:733` separately
moves standing followers after the owner, including into ordinary indoor rooms.
Policy 239 now finds an outdoor no-mob waypoint on the actual source route and
permits the existing familiar-backed probe only if the remaining route and
wandering search rooms support ordinary ground following. It does not authorize
water, air, wall, random-exit, or unclassified hazard traversal.

The new `companions.py` module separates pure staging selection from bounded
positive acknowledgement handling. The field runner must observe a summon,
uniquely identify the pony, confirm exact-instance group ownership, verify its
presence at the target, and receive the attack-order acknowledgement. Own
companion identity is not a blanket same-name crowd exemption. Instance IDs and
ownership are never restored from a prior connection. Target consider, incoming
damage, resource, loss-history, and player-finishing-XP gates still apply.

The initial 4,257-test suite includes 35 new companion tests and real-source
selector-to-field contracts at levels 8 and 18. Source inspection admits three
new staged level-8 targets and the indoor lemming smithy at level 18. The
separate level-25-and-above familiar tiers remain unaudited and are not silently
treated as the level-15 pony.

Run 12736 then proved outdoor summoning, exact group membership, follower
travel, indoor attack orders, and combat while the companion took damage
instead of the player. It produced zero XP in 100.61 seconds. The smithy fled
west from room 29966 to 29964; its same instance was found but rejected because
the source marks it sentinel. This is a concrete abstraction error: the graph
of ordinary wandering is not the graph of forced combat movement.

The fix preserves only a unique GMCP-confirmed VNUM and live instance, then
binds it to the observed flee and bounded known exit. Its 30-second, same-stop,
level/reboot scope cannot survive reconnection. The field runner still applies
consider, crowd, route/resource limits, and confirms a new companion order.
Twenty-one pursuit cases cover the actual sequence and refusal boundaries;
fresh live chase-and-kill proof remains the next test. Run 12737 separately
earned 50 funding XP in 63.57 seconds. Combined, these two sessions delivered
only 18.3 net XP/minute, including funding: this remains inadequate throughput,
not a completed levelling improvement. Aeloria is safely at healer checkpoint
39039, level 18, 161,002 XP, full HP. Preserve this failed acceptance result
rather than crediting preparation as a successful kill.
Final offline verification passes 4,278 tests in 151.98 seconds. The focused
companion/pursuit set passes all 56 cases; older minimal runner adapters retain
optional-reporting compatibility on both normal and exceptional termination.

The public follow-up did not dispatch the repaired hunt. Runs 12738-12739
selected liquidation and provision funding, with 50 XP over 199.20 seconds
(15.1 net XP/minute), no loss, and safe healer checkpoint 39044. Aeloria remains
level 18, 161,052 XP, with full HP/mana/movement. Do not call this live pursuit
validation or improved progression.

This trial identifies the next capability mismatch. The durable practice
listing contains `fly` at 48%, but the runner has no pre-travel learned-flight
cast. Existing potion-funding flags continue to divert the selector, although
the new movement-evidence repair declines to create such flags for learned
flight. Source `magic.c:3440`, `const.c:2949`, and
`pre_reqs/pre_req-common.c:29` establish the spell, standing-position/minimum
mana requirements, and alteration prerequisite. The next implementation should
add a source-authorized, bounded healer-origin cast with positive live affect
confirmation and resource/failure handling; then clear only the superseded
funding requirement. Do not equate a learned spell name with active flight,
mutate checkpoints to force the hunt, or let failed concentration create an
unlimited casting loop. This is current-level readiness work, ahead of another
speculative target expansion.

### Movement-Limited Progression Experiment

Policy 238 connects run 12730's observed movement exhaustion to optional-flight
funding. Its useful kill, healthy field snapshot at eight movement, source costs
of 130 walking versus 37 flying, and later safe healer snapshot constitute a
specific hypothesis: travel limits this circuit before combat health does.
The repair reads bounded durable history and remembers the exact evidence
pointer so clearing funding does not replay the same request indefinitely.

The review also found a planner inconsistency: provision-funding selection used
only the armed-target protection check. It now uses the ordinary source-target
contract, including the trained-familiar indoor limitation. An unreachable
branch of that contract is restored. The existing one-time bank fallback must
pass the same city-route preflight as shops and now returns directly by recall
after confirmed funding instead of making a redundant magic-shop detour.

Do not treat a loan or potion as proof of better levelling. The acceptance
comparison is objective kills per trip and net XP per total connected time,
including maintenance. Run 12731's unsuitable retrieval request/abort added no
XP. Runs 12732-12733 then live-validated policy 238's public funding handoff:
a 300-coin loan, a 131-coin flight potion purchase/quaff, and safe healer returns
in 16.52 and 17.83 seconds respectively. Total in-game debt is 791 coins, with
238 carried. The evidence pointer survived, funding flags cleared, and flight
is confirmed active. All 4,222 tests pass in 150.55 seconds. The first post-flight
selection still encountered the temporary crowd gate before connecting, so no
improved hunting-throughput result is claimed. Checkpoint 39024 is level 8,
27,612 XP, full HP/mana and 170/220 movement at healer room 3054.
After one 180-second area wait and world-time check (12734), run 12735 executed
the fresh Moria orc route. The target was found, but its room contained two
source-level-7 garter snakes with `spec_poison`, later joined briefly by a
kobold. These were not harmless below-band occupants: `fight.c:296` allows
other prototypes to assist within this level interval. The runner completed
its bounded search and returned with movement remaining, with no combat, XP
gain, or loss. Final checkpoint 39031 is fully recovered at healer room 3054,
level 8, 27,612 XP, with flight active. The session lasted 149.07 seconds.

**Interpretation:** the new funding handoff works and walking exhaustion no
longer ended this trip. It did not establish improved XP throughput. The
comparison also uses different live targets and occupancy, so it is not a
controlled before/after rate estimate. The next experiment must improve useful
encounter density or executable combat readiness at this actual level; avoid
repeating the consumed funding observation or simply relaxing an unclassified
multi-enemy fight. Preserve the crowded-room evidence as such, not absence.

Keep the existing roster as class-regression tracks
while Astrevo remains the fresh-creation proof track.

### Prior Verified Results

Policy 237 subsequently exposed and repaired a stale consequence of the
database interruption: its observed centipede target carried both a timeout
quarantine and a generic failure/absence cooldown. A successful later live
healer recovery, unchanged level/reboot, healthy interrupted snapshot, and no
observed XP loss now authorize one bounded unarmed population revalidation.
The original failure stays recorded, while actual absence/crowd/consider and
combat rejections remain blocking evidence. The existing dispatch counter
prevents another reset-wait retry. Forty-one focused cases cover this boundary.

Run 12730 proved the public handoff, a 95-XP objective kill, safe healer logout,
and normal removal of the obsolete timeout after the kill. Checkpoint 39012
is Astrevo at level 8, 27,612 XP, full health/mana, 219/220 movement, room 3054.
The full suite passes 4,184 tests in 159.74 seconds. The hunt still yielded only
about 35 net XP/minute over 161 seconds: movement exhaustion after the first
kill ended the remaining search. Flight access and travel amortization are
now measured next steps, not grounds to claim a satisfactory levelling loop.

Run 12727 now proves one complete live retrieval quest through the public HERO
entry point, without gameplay steering. Aeloria requested the tome of Orinth,
recovered it from Dwarven Homestead room 20516, and returned it to Suturb on
the same connection. The server awarded 22 quest points and 20 gold to her
bank. The 198-second session contains one request, one completion, one final
quit, no abort, and no combat. Checkpoint 39004 is safely at healer room 3054,
level 18, unchanged 160,952 XP, with full health/mana.

This is a real lifecycle and reward result, not XP throughput or HERO proof.
The initial observed cooldown was zero; run 12724's separate 5-to-4 wait cannot
be presented as one uninterrupted wait-to-reward run. Kill/dig variants and
concurrent live stability still need validation. The review has removed this
reproduced quest blocker; further work now returns to damage/training and
multi-kill progression at actual character levels. Banked rewards must be
withdrawn before treating them as money available for provisions or equipment.

## Architecture Adjustment

### Keep Database Transactions Out Of Live Waits

Policy 236 follows an actual failed experiment, not a speculative refactor.
The first concurrent cooldown/hunt trial let Aeloria's partial event batch
retain SQLite's writer lock during a 30-second wait. Astrevo's combat then
failed with `database is locked` (12723). The runner now flushes before async
waits and after command/lifecycle evidence. A second SQLite connection with a
10-ms timeout writes successfully at every scripted connect/read/send/close
boundary. The full suite passes 4,143 tests in 147.16 seconds. Resume serial
live campaigns first; this replay does not prove concurrent live stability.

The same trial exposed a derived-state defect: checkpoint merging omitted the
cooldown-attempt markers, silently discarding the no-progress retry guard.
Those markers now survive merges. A cleared cooldown also needs at least 180
seconds left before requesting a quest. A short remainder defers the request
without creating another avoidable abort/cooldown cycle.

Run 12724 verified a live 5-to-4 counter decrease, hunger recovery from 2 to 42,
and safe healer logout. Run 12726 recovered Astrevo after the failed hunt:
checkpoint 39000, level 8, 27,517 XP, full health in room 3054. The 162-XP change
has no confirmed objective-kill ledger and is not claimed as a successful hunt.
Run 12727 subsequently passed the same-connection retrieval reward gate above.
Measured productive progression remains next. More waiting infrastructure is
not the goal.

### Respect The Server's Online Cooldown

Policy 235 addresses the online-only cooldown identified during policy 234
validation. The fallback is subordinate to productive field options, except
when a quest-point advancement gate makes questing mandatory. One connected
healer wait checks the live counter and provisions, then enters the existing
quest session. It is not a client-side countdown simulation or an offline
retry loop. The starting counter is consumed on dispatch; a capped frontier
attempt must show a decrease before it can repeat. The original total runtime
and command bounds apply to waiting and subsequent quest phases together.
Source `PULSE_AREA` is 60 seconds with 0.5-1.5 interval jitter, which explains
why a displayed 14-minute cooldown may exceed a short segment budget.

Keep one deterministic behavior engine behind Telnet/GMCP and future Mudlet
visibility. Separate source facts, durable character capabilities, combat-loss
evidence, and temporary occupancy observations. They have different lifetimes.
Use immutable run evidence as the authority and checkpoints as a derived cache.
Extract narrow pure decisions when touching the large campaign module; avoid a
rewrite that stops collecting executable proof.

### Quest Sessions Cannot End Between Phases

**September 8 implementation:** policy 234 replaces this logout boundary with
an explicit, bounded session handoff. Each completed route checkpoints at the
healer, and a fresh route policy inherits only authenticated capabilities and
verified resources. The connection, lease, recorder, original deadline, and
command counter remain owned by one runner. Request/tool/target/turn-in are
limited to four distinct phases. A transport loss closes the continuation;
cached quest identity cannot authorize another target trip. Unfinished quests
use the source-supported local abort command before logout.

Fifty-one focused tests cover the lifecycle, reward state, kill aggregation,
failure records, reconnects, missing live status, source population gates,
runtime cutoff, and duplicate-phase rejection. The original kobold population
is six, outside the existing four-instance research bound; the analysis does
not justify relaxing that bound solely to accept that assignment. A fresh live
quest reward is still required. This fixes a lifecycle contract, not the wider
XP-throughput problem or the missing creation-to-HERO proof.
The final full suite passes 4,119 tests in 152.56 seconds, 25 more cases than
the pre-session implementation.

The first bounded public trial checkpointed without connecting because the
school target was still marked crowded. One explicit reset retry then ran the
world-time probe (12722), returning safely at checkpoint 38988 with no XP
change, no reboot, and quest cooldown still 14. Source `quest_update()`
(`quest.c:1139-1155`) decrements that counter only for live character-list
entries. Consequently offline waiting cannot make this character quest-ready.
The next useful change is connected progression while cooldown runs, or one
bounded connected wait when no productive field option exists. Repeating short
login/logout probes is neither progress nor a valid cooldown experiment.

Runs 12720-12721 expose an architectural mismatch, not another target-specific
route exception. The request run had a live kobold quest with eight minutes
remaining before it quit. The next run logged in with no active target and a
15-minute cooldown before sending any quest-abort command. Current DD4
`save.c:309-312` writes `QuestNext = QUEST_ABORT_DELAY` for an active countdown;
the quest target is not serialized. A campaign checkpoint taken before quit
therefore retains a quest that the subsequent login cannot resume.

The next work must preserve the connection across request, target, and turn-in.
Retain bounded phase budgets, durable checkpoints, ownership leases, safe
cancellation, and emergency cleanup, but separate checkpointing from logout.
On reconnect, live quest status is authoritative. Prove a single authentication
and no intermediate quit in replay, then an actual live completion and reward.
Do not keep requesting quests through the known losing lifecycle.

The kobold's independent source rejection was exactly `target reset capacity
exceeds one`, not an observed dangerous special or stronger opponent. Review
that older quest admission against the bounded population logic already used
by ordinary research, retaining exact live targeting and the remaining gates.

The current mage checkpoint is 38983, level 8 and 27,355 XP, fully recovered at
healer room 3054. The recent large-orc search exhausted movement before a kill;
Granny Jenkins supplied 142 objective XP in run 12719. The other 80 XP came from
a below-band city interruption. These results validate restored scheduling and
one useful kill, not adequate XP throughput or level-9/HERO completion.
Final verification passes 4,094 tests in 148.76 seconds, including 27 added
regressions for the training-ceiling and completed-recovery contracts.

### Rejected Priority Ceiling, September 8

The remaining-practice question from run 12710 is now reproduced, not merely
attributed to conservative spending. Its final live listing showed headbutt
28%, enhanced damage 66%, and two physical practices. The fallback damage
chooser returned enhanced damage despite the same visit's teacher-cap
rejection. The lesson planner excluded that skill but stopped at its priority
index, hiding headbutt and producing an empty plan.

Policy 232 applies rejected/equipment exclusions and minimum levels to that
fallback ceiling. The source teacher still predicts headbutt 28 -> 42 -> 49
with the remaining two practices. Replay confirms a fresh listing between
commands and a stop at zero balance. A source-capable same-teacher retry is
available only for the consumed policy-231 failure whose actual event history
contains the rejected ceiling and terminal deferral; its run ID is durable and
the later attempt cannot reopen. This is a repaired scheduling bug, not blanket
permission to spend saved practices or bypass combat-loss restrictions.

Run 12711 confirmed the two additional lessons (headbutt 42%, then 49%), zero
remaining practices, and safe healer logout. Checkpoint 38957 keeps Dorrik at
level 25 and 380,076 XP with full health and 426/442 movement. The complete
policy-232 suite passed 4,079 tests in 146.35 seconds. His next source decision
still reports unavailable protection, so repeating that unchanged hunt would
not be useful validation of the improved skill.

### Completed Recovery Must Advance, September 8

Rotation to Astrevo exposed another unproductive control loop. Runs 12712 and
12713 successfully confirmed healer room 3054 and quit, but maintenance
reconciliation restored the old field connection-loss abort from its research
result. That checkpoint requested return-home again indefinitely.

Policy 233 consumes only the transport handoff after a successful return-home
result independently supplies a living, non-fighting healer snapshot and no new
abort. It runs after maintenance reconciliation. Merged old vitals, missing
enemy/position observations, another maintenance execution, and failed returns
cannot confirm completion. The failed-run ledger, field hazards, and XP losses
remain untouched. The next acceptance check is a public invocation that moves
from recovery to a field decision; safe recovery alone is not XP progress.

Runs 12714-12715 caught an invalid fixture assumption in the first guard: the
actual model serializes `enemies`, not `enemy`. The test and guard incorrectly
agreed on the invented singular name, so every real recovery was rejected.
The regression now constructs `CharacterState.to_dict()` and uses the existing
empty-enemy parser, including nested empty lists. Read-only replay of the actual
checkpoint confirms that only the transport handoff is removed.

Run 12716 then completed recovery, and the same public two-segment invocation
selected the Circus Midget hunt as run 12717. The target was absent. A
below-band drunk interruption yielded 80 incidental XP, leaving Astrevo safely
at level 8, 27,213 XP, checkpoint 38970. This proves the scheduling handoff,
not useful-target progression; the next invocation rotates to a Moria large orc.

### Useful Local Training, September 8

The level-25 warrior's saved state exposed an actionable alternative to another
unavailable hunt: three physical practices remained while dodge was only 28%.
Its fixed advanced-teacher route crossed source-known aggressive mobiles, so
the old behavior deferred the entire training opportunity. The current source
does not impose a maximum player level on the nearer teacher; `teacher base`
is a minimum. That teacher's 70% group capacity remains useful for dodge.

Policy 230 reads GSN-to-name and skill-group membership from `const.c` and
mirrors `act_info.c:do_practice`, `has_groups`, and the stat penalties in
`handler.c`. With modified STR/DEX/INT 30/17/12, the physical penalty is 13.
The first local dodge practice predicts `(28 - 13 + 70) / 2 = 42` after integer
truncation. Enhanced damage 66% cannot improve there and cannot improve at
the 80-capacity teacher without changing the relevant stats. Target percentages
in the training priorities are goals, not a teacher's actual ceiling.

The new fallback chooses the registered class guild, requires available points
and an observed positive skill with a useful expected gain, checks source route
hazards, and retains the route through the visit and healer return. A matching
durable practice audit can reopen one local attempt after a distant deferral.
The exact teacher, expected gains, and pending/consumed record are saved before
dispatch. This does not remove existing combat-loss or protection requirements.
Focused tests cover the source/formula boundary, three classes,
missing data, exhausted lessons, route hazards, and actual pre-worker persistence.
Improved combat throughput remains a separate acceptance gate.

Run 12709 then demonstrated why the public acceptance test matters. The
campaign selected the fallback, but the worker checked its distant route before
reading the live practice balance. Its initial `(None, None)` could not support
the local forecast, so it deferred, changed equipment, and logged out at the
healer. No practice or movement command occurred; XP remained 380,076. Its
successful segment label means safe completion, not a useful training outcome.

Policy 231 reuses the three-attempt score audit before that fallback decision
and retains source preflight across the response. The startup repair may reopen
the exact policy-230 no-audit/no-visit event pattern once, recording its run ID;
it rejects actual audits, movements, lessons, and later-version attempts.
The selector regression also retains source-revision invalidation: a changed
source may clear a stale deferral, whereas an unchanged source can select the
pending lesson before an unavailable-protection stop. No combat restriction is
removed by this maintenance priority.

Run 12710 validated the correction through the public HERO command. It read
score before choosing the fallback, reached guildmaster 3023 in room 3023,
received an enhanced-damage teacher-cap refusal, and learned headbutt to 28%.
That new damage skill took precedence in the live class priority list; the
forecast dodge increase did not occur. The character returned to healer room
3054, slept, and logged out at checkpoint 38954 with 569/569 HP and 442/442
movement. The run lasted 57.17 seconds and left XP unchanged at 380,076.
Two physical practices remain. This is live evidence for the trainer handoff,
not optimal practice spending or improved XP/minute. Review that remaining
practice decision and collect a useful current-band combat comparison next.
The final offline suite passes 4,067 tests in 146.34 seconds, including 47 new
training-source, formula, route, selection, live-order, and retry-ledger cases.

### Resume Cost And Diagnostic Discipline, September 8

The older roster must remain part of development. Dorrik's level-25 resume
spent roughly 159 seconds preparing before selecting an unavailable-protection
boundary; it opened no gameplay connection and ended at checkpoint 38946,
380,076 XP. A process sample identified historical kill reconstruction. Its
helper loaded each complete event list, then walked backward for the latest
state record containing a kill list. Repeating this across historical segments
turns transcript volume into startup cost.

Policy 229 queries that latest qualifying state event directly using the existing
run/event index. Empty lists still override inherited positive kills, later
legacy completed-kill events retain precedence, and missing event ledgers use
the same objective-eligible kill-table fallback. There is no persistent cache
that could hide a newer failure. Fourteen tests exercise those contracts and
forbid the full-event loader on the new path. Across 64 actual Dorrik runs,
the old path materialized 43,228 rows in 0.8024 seconds; the new path returned
the same 64 event IDs in 0.0026 seconds. This warm-order microbenchmark is not
an end-to-end startup claim; preparation still includes other history repair
and source selection work.
Repeating the entire confirmed-research-kill repair against the saved campaign
returned identical repaired state in 0.7545 instead of 3.5614 seconds. The second
comparison cleared the Python history caches before each path; filesystem and
SQLite pages could still be warm. All 4,020 offline tests pass in 142.03 seconds,
including 29 new cases for policies 228 and 229 in this continuation.

A separate Astrevo attempt, run 12708, disproved the first diagnosis of a
policy stall after moving south. Complete event inspection showed immediate
`look in pouch`, a response about 40 seconds later, `config +autoloot`, then a
45-second acknowledgement probe and another 45-second reconnect boundary.
The socket was semantically quiet during these delays. Client, network, and
server causes remain unresolved; neither a prompt parser failure nor a stuck
policy flag is established. The character returned to healer checkpoint 38944,
level 8, 27,133 XP, without combat. Run 12707 was maintenance with no XP change.

Do not spend another work unit repeating the unchanged acceptance failure.
Distinguish preparation, transport acknowledgement, intentional game waits,
target search, and combat throughput in diagnosis. Complete per-run decisions
and watchdog events take precedence over a truncated query or an old summary.
The next executable milestone remains useful multikill progression on the
fresh track, alongside a resolved protection/training gate for the stored
level-18-to-25 roster, not another catalog or checkpoint count.

### Population Audit, September 8

#### Route/Endpoint Follow-Up

Checkpoint 38939's final locator placed the drunk at the bank entrance and
bakery, off the registered Moria path; the runtime cap prevented departure.
The next source replay found a planner/executor mismatch: the low-level greeter
passed its own damage/HP bound, but `_source_ranked_route_program_candidate_allowed`
rejected the endpoint's capacity-only research marker. That meant a population
of three unrelated orcs changed the handling of the same city greeter.

Policy 228 adds an execution-only opt-in for the existing bounded capacity
research class. Default route-program candidate admission remains unchanged;
all other endpoint and route exclusions remain. The greeter's exact source,
probabilistic program, HP/damage bounds, and live isolation/resource checks
are still required. City-shop liquidation does not use this opt-in. Fifteen
new cases cover class independence, exclusion preservation, and missing/low
health reserves. This is an executable current-frontier correction; live
access and multiple useful kills are separate acceptance checks.

Run 12695 spent 130.87 seconds on one 163-XP objective kill, about 74.7 net
XP/minute including travel/recovery. It recalled at 113/113 HP and 270/324 mana
because of its one-kill cap. That proves an avoidable field boundary, not a
need to loosen the health threshold. Cross-prototype circuits exclude wanderers
because their existing connecting paths assume fixed reset rooms; locator
narrowing also replaces the remaining stop list. Removing only that guard
would be an incomplete planner/executor change.

The narrower executable opportunity is already-supported same-prototype
wandering hunts. Moria's ordinary orc (4004) has a global limit of three and two
M entries at room 4028. Policy 225 rejected it because capacity research allowed
only two global instances and multiplied that count by the reset entries.
DD4 `db.c:reset_area` checks `pMobIndex->count >= pReset->arg2` globally; these
entries do not each authorize another independent population of three.

Policy 226 keeps a four-global-instance research ceiling and two-local-entry
limit without multiplication. Exact live isolation, useful-band consider,
source hazards, health/resources, prior losses, and bounded search remain
authoritative. Population evidence is not simultaneous-enemy permission or
availability proof. The existing plan supplies a three-kill limit for this
population. Thirty-four new tests cover admission, source exclusions, malformed
counts, retained loss evidence, all three representative classes, and generated
locator/target gates. A fresh public run must establish actual improvement.

Run 12702 then selected mobile 4004 automatically, intercepted exact instance
#2761 in room 4010, killed it for 89 XP, and returned to the healer. Its
61.647-second duration includes travel and recovery (86.6 XP/minute). One run
is not a comparative throughput benchmark. At the return decision it still had
109/113 HP, 287/324 mana, and no recorded one-kill resource limit. The actual
cause was an unconditional post-intercept return flag, separate from the kill
budget. Policy 227 moves that decision after kill accounting and returns only
when the objective budget completes; existing pending returns and ordinary
post-loot resource gates remain. Nine additional replay cases bring this unit
to 43 focused tests. Fresh multi-kill continuation remains to be demonstrated.

Run 12703 lost 48 XP while withdrawing from Circus transit, leaving Astrevo
safe at checkpoint 38930, level 8, 27,133 XP. It emitted identical drunk rows
with matching changing HP. The read-only source audit found that Telnet
`update.c` iterates room combatants but serializes the primary `enemy` for each
match. Those repeated rows may represent other participants, not distinct
copies of the identified opponent. Do not deduplicate them into isolation or
interpret their copied HP/identity as a combined damage budget. This is a
perception limitation to resolve with independent live evidence, not a reason
to erase the actual loss or loosen ambiguity checks.

The population audit also found 111 source prototypes with differing limits
between M resets. The catalog now takes their global maximum across all rooms,
including other areas. For example, sewer mobile 7002 has limits 3, 5, and 7;
its first reset cannot establish a three-instance population. Generated source
capacity warnings and `source_spawn_limit` use the same maximum. Three extra
cross-room tests bring the focused unit to 46 cases. Runs 12704-12705 ended at
safe checkpoint 38936 without XP change after shop and route-program waits;
they did not exercise the post-intercept repair. Preserve that failed acceptance
check rather than claiming a replay as live improvement.

Final verification: 3,991 tests passed in 143.77 seconds; compilation and scoped
whitespace checks passed. Run 12706 selected the corrected Moria population but
experienced delayed command responses followed by route-program waits. It
saved and quit at its controlled cap without combat: checkpoint 38939, level 8,
27,133 XP, 113/113 HP, 320/324 mana, 186/220 movement, healer 3054. A ten-second
process sample found 992/999 main-thread samples in the event-loop poll, not
source preparation. It cannot distinguish transport delay, server behavior,
or response scheduling; keep those hypotheses separate. The five live segments
in this work unit earned 89 objective XP and lost 48 XP, for 41 net XP. This
is inadequate progression throughput, not a successful multikill benchmark.
The next work must prove the repaired continuation with actual useful kills
and resolve any fresh execution blocker shown by that attempt.

Policy 219 introduces `temporal_evidence.py`. An exact, successful, zero-XP,
pre-combat room-crowd observation at the same level/reboot becomes eligible for
reinspection after 5, 10, 20, then 30 minutes. The clock and backoff come from
completed segments, so reconnection cannot renew them. Only a current-source
ordinary, fixed, single-reset candidate may use this permission. Actual losses,
failed considers, protection requirements, and source hazards remain separate
gates. The original observations and reinspection provenance stay auditable.

The review also repairs the recent-kill/circuit handoff: primary-target rotation
must not remove a useful recent target from an otherwise executable nearby
circuit. The circuit planner still rechecks repeatability and all field gates.

## Validation Boundary

All 3,736 offline tests passed at policy 219 (249.03 seconds), including
timestamp boundaries, increasing backoff, malformed/newer history, source and
combat exclusions, and the recent-kill/circuit handoff. Compilation and scoped
Git whitespace checks passed at that boundary.

Run 12691 reopened the expired Illusionist observation and returned safely at
checkpoint 38874, level 8, 26,997 XP. The room still contained the Illusionist,
the displaced Midget, and a harmless Fido. The bot declined combat. This proves
bounded reinspection, not improved throughput; the next inspection now waits
20 minutes from that observation. The live trace also exposed the recent-kill
filter defect repaired above. A multi-objective live journey remains required
before claiming a throughput improvement.

Run 12692 replenished food. Run 12693 then encountered the level-2, 20-HP
drunk beside the Bearded Lady, fled without attacking, and lost 68 XP. The
checkpoint was 38881: level 8, 26,929 XP, full at healer room 3054. This
loss remains quarantined and is not erased by crowd expiry. Source
`fight.c:violence_update` permits the nearby Lady to join a fight against a
level-8 player, so blindly ignoring all bystanders would be unsound. The next
concrete execution improvement is a shared planner/executor budget for an
unavoidable weak attacker plus identified potential joiners, or source-aware
avoidance of that occupied endpoint. Current bounded-greeter admission was
tested in isolation and did not establish that combined encounter contract.

Run 12689 demonstrated repaired startup and an ordinary Bearded Lady kill,
not the specific no-sanctuary Ivan fallback execution. Preserve that distinction
when referring to policy 217. HERO, subclass transition, and arbitrary-class
completion remain unproven.

## Packet-Order Finding And Policy 220

Deeper replay corrected the initial explanation of run 12693. DD4 sent
`Char.Enemies` before `Room.Info` in the same read. The observation handler
used the final reduced character state to bind that enemy to room 4409, then
marked it stale when processing the arrival into 4409. The ordinary defensive
decision therefore never saw the fresh enemy records; a later fallback
declined the room's bystanders. Raising aggression would not repair this
perception failure.

The handler now retains only a destination association created in the current
batch. A previous visit cannot refresh an old enemy, and a batch crossing
multiple distinct rooms cannot assign an early enemy to its final destination.
The existing defensive, health, and joining-attacker gates remain unchanged.
The full suite passes 3,746 tests (263.08 seconds); the new packet-order cases
explicitly instantiate mage, thief, and warrior identities.

Run 12694 found the Illusionist still crowded. Run 12695 then killed the large
orc for 163 objective XP and recovered at the healer. Checkpoint 38889 is level
8, 27,092 XP, 113/113 HP, 324/324 mana, 213/220 movement. The next selector
stopped on the remaining crowded frontier. This is fresh progression, not live
reproduction of the exact packet-order interruption and not a level-9 claim.

Next, resolve eligible borderline bystanders with exact, read-only `consider`
checks. The source assistance window starts three levels below the player;
live `consider` evidence at five or more levels below may rule out assistance
where the source fuzz range alone cannot. Preserve source identity, aggression,
program, and special checks, and never apply one instance's result to another.
This can reopen a useful room without claiming its visible occupants are absent.

## Policy 221: Test The Actual Execution Path

Runner integration replay found an important shortcoming in policy 220's proof:
the policy tests submitted complete batches, but the real runner reduced and
delivered one event at a time. The enemy-first case still belonged to the old
room. Policy 221 preserves sequential reduction, then reconciles fresh enemies
with the batch's sole explicit GMCP destination. Tests exercise `_record_read`
across mage, thief, and warrior, including old visits and ambiguous arrivals.
This strengthens the review's rule: test the actual adapter-to-decision path,
not only a convenient internal method boundary.

Borderline-bystander inspection is now implemented. It requires an exact
TARGETMODE instance and globally unique full source room description, then a
live no-match or naked-and-weaponless result. Source `fight.c:violence_update`
excludes ordinary assistance more than three levels below the chosen victim;
`act_info.c:do_consider` gives a five-level upper bound for these messages.
Programmed, special, aggressive, non-corporeal, shop, and ambiguous mobiles are
excluded, as are encounters with an active familiar: assistance can select a
different group member. The Midget displaced into the Illusionist's room is the
concrete motivating case, not a character-specific exception.

Use at most three inspections per room visit with five-second response bounds.
Results expire after 30 seconds before combat. A result observed fresh during
the admitted fight may remain attached to that same target and kill sequence;
expiry alone must not force an otherwise unnecessary retreat mid-fight. Room,
reboot, level, instance, reconnect, and familiar changes invalidate authorization.
Audit copies are persisted separately from intended-target consider evidence
and are never loaded as permissions for a later run.

All 3,793 tests pass (262.08 seconds), including the 47 new focused tests.
Compilation and scoped whitespace checks pass. Test adapters were updated for
the new terminal audit field; the final complete suite includes those changes.

Run 12696 issued `consider #2916` to the source-identified Midget and received
"The Midget looks like an easy kill." This leaves his ability to assist
unresolved. The runtime retained the crowd gate, persisted the negative result,
and returned fully recovered. Checkpoint 38895 is level 8, 27,092 XP, 113/113 HP,
324/324 mana, and 220/220 movement in healer room 3054. This proves inspection,
negative-result handling, persistence, and recovery, not the permissive branch,
the exact arrival interruption, a throughput increase, or another level.

## Next Executable Gate

Stop repeating the unresolved Illusionist inspection without a changed input.
Build the missing contract for a fight plus its identified potential joiners:
combine source/live HP and incoming-damage bounds, positively trained damage
actions, executable protection, mana cost, and bounded finishing behavior.
Compare that encounter with independent current-level targets by total expected
journey cost. Unknown identities remain explicit uncertainty, not invisible
occupants or unconditional global crowd permission.

Acceptance is fresh unattended evidence through the public HERO entry point:
multiple useful objective kills in a journey, measured net XP over total run
time, no manual combat commands, and correct recovery/checkpoint accounting.
Then advance Astrevo to level 10 and prove trainer handoff; use the stored thief,
mage, and warrior frontiers for shared-behavior regressions. A larger policy
inventory or another unchanged safe stop cannot satisfy that gate.

## Policy 222: Active Encounter Controller

The first executable part of the combined-encounter contract is now in
`encounters.py`. Previously the runner fled immediately on more than one
useful-band active enemy, regardless of their remaining HP. A short ordinary
encounter can now continue when all live/source identities, HP, levels, reset
equipment, trained output, and current resources support it. It budgets every
active mobile, including below-band attackers, in the worst possible defeat
order, adds two utility/acknowledgement rounds, and retains health and mana
reserves. No opening attack or protective affect is credited speculatively.

Runtime permission belongs only to this fight and its remaining actors, not a
character name or durable checkpoint. The existing survival and timeout checks
preempt it; a live damage-progress probe detects a failed output estimate. The
controller expires after 30 seconds and cannot reopen itself while that fight
remains active. Unknown/programmed/special/armed enemies are still handled by
their existing policies. Pre-combat crowded-room admission is deliberately not
inferred from an ongoing-fight budget.

The concrete replay uses two live level-5 ordinary enemies with 10 HP each.
A level-8 mage can cover them with two estimated damage actions and a 46-HP
reserve; weaker thief/warrior loadouts need four actions and more current HP.
Tests cover both the admitted and rejected cases through `next_decision`, not
only the pure calculator. There are 43 additional tests. Full-suite results and
fresh live outcomes are recorded at the next validation boundary below.

### Validation And Next Blocker

All 3,836 tests pass (236.96 seconds); compilation and scoped whitespace checks
also pass. Bounded public-entry resumes selected unavailable policies before
opening a gameplay connection: Astrevo checkpoint 38896 (level 8, 27,092 XP),
Aeloria 38898 (level 18, 160,952 XP), and Kestrel 38900 (level 24, 333,533 XP).
These are selector/recovery evidence, not live validation of the new combat
branch. The active-combat controller is replay-verified only.

Kestrel's attempt spent approximately 160 seconds in local campaign startup.
The process was observed alive, with no DD4 socket, and exited normally at its
protection-recovery boundary. The expected 30-second heartbeat did not run:
`_run_runner_with_outer_timeout` schedules `runner.run()` on the same event loop
as its monitor, but campaign preparation executes synchronous history/source
work before yielding. The asyncio deadline is therefore not a hard wall-clock
bound on that work. A late stack-sampling attempt found the process already
exited, so the exact expensive preparation function is not yet identified.

Next, profile and bound the startup path without leaving a background worker
or changing live recovery ownership. Preserve the ordinary-loss and protection
evidence; do not erase it merely to force an available policy. Then complete
pre-combat encounter admission and demonstrate useful kills through the same
public command. Neither more zero-XP retries nor a passing suite substitutes
for that progression proof.

## Startup Profile And Repair

The hypothesis that the 25-GB SQLite store dominated startup was not supported
by the profile. Eight `rank_hunt_candidates` calls consumed 66.19 seconds of a
92.59-second profiled Kestrel resume. The main loop repeatedly classified every
wandering hazard for every target, including unreachable areas. Fastwalk
expansion also repeated roughly 170,000 times. This is avoidable planning cost,
not an approval wait, disconnected character, or source-download stall.

Source ranking now indexes wanderers by reachable room once per call, separately
for transit threats and endpoint-only assistance. Candidate processing retains
original reset order and all existing hazard checks. Mutable world data is not
cached across calls. Pure fastwalk expansion has a bounded 1,024-entry cache.
Regression tests cover endpoint scope, source-door changes, hazard ordering,
and classification counts independent of unrelated targets.

The complete 317-candidate level-24 serialization and order have the same SHA256
before and after: `5b1ed8995c918b19e2033f2c1972e88816e3b653fbb3fc3e40d78f280fb6fabf`.
That comparison used the current source mirror, level 24, thief, 334 maximum HP,
all areas, XP-only targets enabled, and the one-level source ceiling enabled.
Unprofiled single-pass ranking fell from 2.308 to 0.614 seconds. Matched full
profiling fell to 39.83 seconds, with ranking down to 12.92 seconds. These are
observed timings, not a universal performance guarantee. A subsequent public
resume without the profiler took 27.15 seconds while the offline suite was
running, and returned the same checkpoint 38900 and protection cooldown.

Preparation now has named source/history, repair, selection, execution-check,
and segment-construction boundaries. They yield to the event loop and check the
task-scoped outer deadline before advancing. Tests inject a blocking history
or selector phase and verify no gameplay segment opens after expiry, the lease
is released, and the deadline does not leak into another task. No gameplay
ownership moves to a detached thread or process.
The final dispatcher checks the same deadline before and after live-runner
construction as well, so synchronous argument/source preparation cannot
silently consume the remaining budget and then open a connection.

This does not make synchronous Python preemptible. A single call can still
overrun until the next boundary, and cold catalog setup remains outside the
live budget. Do not claim a hard wall-clock guarantee. If further profiles
show long indivisible work, bound or isolate that specific phase with explicit
ownership and termination tests, rather than masking it with a heartbeat.

The next progression gate is unchanged: executable pre-combat encounter
planning and fresh useful multikill evidence, then the fresh character's
level-10 trainer handoff. Do not spend another work unit repeatedly launching
the same protection/crowd stop without changing its evidence or implementation.

Final verification: 3,848 tests pass in 138.55 seconds, including 12 additional
reachability, cache, preparation deadline, dispatch, and cancellation cases.
Compilation and scoped whitespace checks pass. No profiling process remains;
the independent Discord streamer was left running. No local commit or remote
push was attempted in this work unit.

## Policy 223: Concealed Combat Statistics

The next pre-combat encounter audit uncovered a more immediate input defect.
The captured `dd4_gmcp.txt` fixture and Astrevo's live checkpoint contain
`damroll: 50000`, `swift: 50000`, and `ac: 50000`. Source `update.c:3987-4040`
deliberately sends this sentinel for statistics below their disclosure level.
Damroll, hitroll, critical, and swiftness become visible at level 15; armor
class and save-vs at level 20. This is not an exceptionally powerful character.

Both campaign readiness and the policy-222 active controller passed these
values to `source_combat_output_estimate`. A reproduced level-8 warrior plan
therefore estimated 100,014 damage per action instead of 8, and admitted an
otherwise unaffordable two-enemy fight. The shared estimator now decodes the
sentinel before calculating physical damage or automatic extra attacks. Raw
state is left intact; real positive and negative bonuses are still applied.
Missing, concealed, malformed, and non-finite values supply no bonus credit.

Six initial tests reproduced the failure before the repair. Broader coverage
uses the captured protocol fixture through observation parsing, state reduction,
live policy decisions, and legacy campaign output reconstruction. New group
admission must wait for this input contract, rather than inherit a false
damage budget. No combat threshold has been globally relaxed in this repair.

The source review also confirmed that pre-combat `consider` exposes a current-HP
interval (`act_info.c:do_consider`), while armor affects ordinary hit probability
(`fight.c:one_hit`). Armor is concealed at the fresh character's level, so an
armor-based group estimate cannot simply read `stats.ac`. Future admission needs
audited visible/derived inputs and a runtime controller with the same resource
budget; the existing short finishing calculation alone is not such permission.
All 3,870 offline tests pass (137.58 seconds), with 22 additional tests for this
repair. Compilation and scoped whitespace checks also pass. The captured
low-level fixture is now exercised beyond parsing, through both consumers of
the damage estimate; the unmodified raw sentinel remains in audit state.

### Live Search Counterexample

The public Serevian resume selected source mobile 9808, a fanatic monk, and
opened run 12697. At Dragon Cult room 9850, `where fanatic` returned no match.
The bot recalled and recovered at healer room 3054. The next bounded attempt
stopped at the existing sanctuary cooldown. Checkpoint 38906 is policy 223,
level 11, 50,711 XP, 186/186 HP, 172/172 mana, and 250/250 movement. There was
no kill or XP change; this is not live combat validation of the new estimator.

Source `cult.are` gives the monk no sentinel or stay-area flag. Its reset room
has an open southern exit to Midgaard room 3024. Of the source parser's first
32 reachable rooms, one is in Dragon Cult and 31 are in Midgaard. However,
`_source_ranked_hunt_stops` enables `abort_if_where_target_unlisted` for this
global wanderer, and the runtime recalls before checking another area. Its
abort record correctly says current-area only, but the control flow discards
the cross-area search and its decision text calls the locator global.

This is the next concrete progression repair, ahead of speculative group
admission: continue one bounded source-vetted neighboring-area check after a
local miss, retaining exact target identity, current route/resource checks,
and explicit search scope. Do not loosen real loss/protection evidence or
search an unbounded world graph. The monk's presence elsewhere is unobserved;
source reachability is a search hypothesis, not live availability. The sanitized
reproduction is `tests/fixtures/dd4_cross_area_locator_miss.json`.

## Policy 224: Search Scope Is Not World Absence

The planner now offers one neighboring-area locator waypoint for an
unrestricted, non-confused wanderer. It uses the existing bounded source graph,
an open ground path of at most six moves, and excludes random exits, private,
solitary, no-recall, and initiating-hazard rooms. The runtime consumes that
extension before moving, clears the old response, and asks the same exact
locator question in the new area. It never retries an unlimited list of areas.
Low live health/movement or an unavailable live exit still stops the route.

Source room 3024 is reachable by one southern move from the reproduced Cult
query. A cityguard may reach that endpoint, but its special joins existing
combat rather than attacking a walking character. The shared route auditor now
has an explicit noncombat-endpoint mode used only for locator transit; default
combat callers retain the original joining-risk checks. Programmed and
aggressive transit attackers are not exempted.

A second miss ends the attempt. A positive second-area label is rebased from
the actual query room using the existing source relocation graph, retaining
exact identity, live consider, crowd, and damage-window requirements. Unknown
labels do not replay an old-origin route. Run and checkpoint audit lists record
the source area, query room, target VNUM, and scoped result; they cannot be
rehydrated as live authorization. The first miss remains visible even when
the second query succeeds.

This continues the revised method: repair a captured execution failure, test
the actual command/reply sequencing, then seek fresh public-entry evidence.
It is not grounds to erase unrelated loss or protection cooldowns. Neither
the monk's current presence nor improved XP throughput is established by replay.

Verification: all 3,894 tests pass in 147.97 seconds. The 24 new cases cover the
captured negative response, exact second-area mapping, unavailable/unsafe paths,
resource limits, delayed responses, the two-area bound, and persistence during
a runtime cap. Compilation and scoped whitespace checks pass.

### Live Boundary And Next Work

The bounded public resume made three server-time checks, runs 12698-12700,
with no XP change. The same reboot remained active. The configured reset waits
expired the monk's area-local absence and retained the original observation in
history. A subsequent ordinary public resume nevertheless selected unavailable
protection recovery without opening gameplay. Checkpoint 38918 is level 11,
50,711 XP, 186/186 HP at healer room 3054. The new locator branch is not yet
live-validated, and these maintenance runs do not count as progression.

Read-only selection reproduction gives the monk `fresh` status, no below-band
exclusion, and no sanctuary requirement. However, the protection-recovery
fallback predicate returns false, including when ordinary selection is called
with that fallback enabled. The next work must trace this exact gate and its
attempt ledger, distinguishing expired search occupancy from actual combat
failure. Do not clear all safety history or repeat another unchanged command.
This is a concrete current-level blocker; speculative higher bands remain lower
priority. No test/profiling worker remains and no commit or push was attempted.

## Policy 225: Revalidate Changed Search Scope

The protection-fallback ledger consumed the monk's distinct-policy slot before
run 12697. Expiring its area-local absence did not release that independent
exclusion. The last-target and exhausted-search rotation also blocked the same
candidate after the fallback check was repaired. These were separate gates;
testing only the fallback predicate would have missed the second defect.

One expanded search may now be registered from the latest successful,
same-level/reboot segment after ordinary absence expiry. Audit at most 512
events from each of at most three relevant runs. Require matching recorded
command/decision counts, a single exact locator in the reset room, an observed
negative response, no unknown/offensive commands or combat events, unchanged
XP and health, and safe healer completion. The current actual hunt plan must
offer the new neighboring-area continuation. Source reachability alone is not
sufficient to reopen a failed fight.

The old attempt and retry markers remain in history. A separate
`campaign_source_locator_revalidations` record carries the source run, query
room, source revision, new route, and one-use status. `_run_starter` consumes it
before opening the worker and records that state in the segment ledger. Newer
attempts invalidate a stale pending checkpoint, while old history cannot revive
a consumed record. Actual loss, timeout, throughput, failed-fallback, and
three-distinct-probe limits remain effective. Class/name-specific behavior was
not introduced.

Read-only replay of checkpoint 38918 now selects the real monk candidate with
all those gates. An integration test also verifies the worker and durable
segment start both see `consumed`, not merely a conveniently tested helper.
Live execution, actual presence, useful kills, and XP throughput remain unproven
until observed in the public resumable run.

### Live Validation: Run 12701

The ordinary public resume selected the monk without a manual gameplay command
or checkpoint edit. The worker queried in Cult room 9850, walked south via the
live exit to Midgaard 3024, and queried again. Both responses were unlisted;
it recalled, went north to healer 3054, recovered, saved, and quit. The following
selection retained the existing protection boundary. Checkpoint 38923 is level
11, 50,711 XP, 186/186 HP at the healer. There was no XP gain or loss.

Both `campaign_fastwalk_where_area_checks` entries and the consumed
`campaign_source_locator_revalidations` record survived into the checkpoint.
This is live proof of the negative two-area branch, source-based selection,
one-use consumption, and recovery. It does not prove that a positive second-area
location can produce a kill, and it does not establish improved XP throughput.
Do not run the same now-consumed search again without changed evidence.

All 3,945 tests pass in 143.17 seconds, including 51 additional cases. No
gameplay, test, or diagnostic Python process remains; the independent Discord
streamer is still running. No commit or push was attempted. During observation,
an open transcript's file metadata lagged actual gameplay; future activity
checks must read content/events, not infer inactivity from size/mtime alone.

Next, return to the active roster's actual combat and training bottlenecks.
Prioritize useful encounter execution and fresh progression at current levels,
including the fresh mage track, rather than another unchanged search or
speculative distant-band policies. Preserve the repaired search behavior as a
shared capability; no character-name-specific exception was introduced.
