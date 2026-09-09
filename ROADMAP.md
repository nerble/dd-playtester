# Autonomous Playtesting Roadmap

## Master Objective

Given only a source-legal race, cosmetic sex, base class, optional subclass,
name/personality, and credentials when resuming, create or resume a character
and autonomously reach the requested level, up to HERO 100. Preserve progress,
explain the experience, and support direct Telnet and visible Mudlet operation.

**Not complete:** no HERO character is proved. Highest actual frontier is 25;
the fresh-creation track is 8. The active goal remains this master objective.
The [September 8 review](docs/APPROACH_REVIEW_2026-09-08.md) is the current work
order; dated run evidence belongs there, not in an expanding policy changelog.

## Delivered Foundations

- Async Telnet negotiation, GMCP capture, transcripts, SQLite, and inspection CLI.
- Deterministic observations, character state, checkpoints, and replay tests.
- Parameterized creation, the starter tutorial, and early character development.
- Run/campaign reports with evidence-grounded commentary and persona metadata.
- Public `hero` entry point, resumable campaigns, credentials, bounds, and recovery.
- Shared source-backed combat, training, equipment, travel, and resource policies.
- Mudlet bridge interface; this is not full VM lifecycle or HERO validation.

These have implementation and varying amounts of live proof. Their existence
does not mean every race/class or level band works end to end.

## Immediate Delivery Gate

1. Advance Aeloria from level 18 to 19 using measured current-band encounters;
   audit prior Arachnos loss evidence before allowing the next guardian route.
2. Advance the fresh character from level 8 to 9 and through the level-10
   trainer transition without adding name-specific behavior.
3. Demonstrate three consecutive bounded public invocations with positive
   combined net XP, repeated useful kills, autonomous maintenance, and a level
   gained. Include travel, recovery, provisions, and failed hunts in the cost.
4. Use existing thief, mage, and warrior campaigns for shared-behavior
   comparisons at their actual frontiers. Fix the largest measured bottleneck.

The latest Kestrel handoff consumed its sanctuary reserve in an interrupted
Circus attempt. Recovery checkpoint 39707 is level 24 at 333,258 XP and full
health at the healer; it did not clear negative fame. Connection-gap accounting
now retains the 385-XP decrease without claiming an observed death or a failed
damage probe. Preserve that evidence while continuing roster-level progression;
do not reopen the same combat merely because its worker was interrupted.

Aeloria checkpoint 39727 remains level 18 at 161,091 XP. Run 12880 now
live-proves that the invisible carrier locator reaches both required-loot
mobiles together. Duplicate-target consideration was the next blocker; its
shared probe handoff is now replay-tested. Require actual second-potion
acquisition and a subsequent useful kill before claiming progression.

Current checkpoint 39657 is Aeloria level 18 at 161,091 XP, with full resources
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
