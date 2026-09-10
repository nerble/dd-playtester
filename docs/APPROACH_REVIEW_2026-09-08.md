# Approach Review: 2026-09-08

## Assessment

The master goal is unchanged: a generic request for a legal race/class/subclass
must create or resume a character and reach HERO 100 autonomously. Cosmetic sex
is preserved, not a separate coverage dimension. No character has reached HERO.
The highest frontier is Dorrik at 25; the fresh-creation track, Astrevo, is at 8.

Telnet/GMCP, credentials, checkpoints, source inspection, training, equipment,
recovery, and the public `hero` command are useful foundations. The missing
product is a reliably productive closed loop. Thousands of tests and policies
have not demonstrated that loop. Recent losses also disprove the assumption
that more defensive decisions necessarily reduce total progression risk.

## Measured Evidence

| Track | Latest comparison | Outcome | Current checkpoint |
| --- | --- | --- | --- |
| Fresh mage, Astrevo | 12815-12816, refresh 12820 | Hunt net -53 XP; fresh recovery confirms corrected baseline without reopening the hunt | 39433: level 8, 28,815 XP; historical 39419 is incorrect |
| Thief, Serevian | 12817-12819, 12821-12824 | Flight purchase, -44 flee loss, +297 incidental warrior kill, then zero-XP searches/probe; net +253 XP in 475.46 connected seconds plus 180-second reset wait | 39452: level 11, 51,147 XP |
| Mage, Aeloria | 12825-12829 | Missed displaced smithy, one-coin sale, absent protection carrier, city departure deferral, then world-time probe; 0 XP in 333.09 connected seconds plus 540 seconds of reset waits; prior guardian loss remains | 39488: level 18, 158,168 XP |
| Warrior, Dorrik | 12766-12768 | +100 incidental XP, then -339 failed-hunt XP; net -239 | 39160: level 25, 379,837 XP |

Dorrik's comparison consumed 286.28 connected seconds plus a 180-second reset
wait. These characters ended safely at healer 3054. Safe logout is a
reliability result, not an XP result. No improved throughput is established.

## Current Continuation: 2026-09-10

Kestrel is the active frontier at level 24 with 332,552 XP and fame -12. Run
12912 reached the Circus Ticket Clerk and captured GMCP level 31, maximum HP
1,033, and the matching high-risk consider text. This is not an alignment
defect: GMCP supplied the target data accurately. Run 12932 then exposed that
the level-22 Canyon cyclops is an aggressive `spec_cast_cleric` sentinel that
attacked on room entry, before `consider`; the resulting flee cost 81 XP.

Runs 12939-12941 exercised the next resource and equipment frontier. Run
12939 stopped the blackberries route at the source-registered level-2 drunk
after three bounded preflight checks. Run 12940 acquired one dead squid and
returned safely. Run 12941 reached Forest room 18027 and found the Kodiak, but
the room also held multiple source-aggressive mosquito and wasp instances; the
crowd gate fled before combat with no loss. Revision 269 now requires a
matching live `where` location before a narrow route branch is entered, so a
broad `Forest` result cannot select the River bed poison-swarm route. The
campaign was later checkpointed at **39920**, alive and fully recovered at
healer 3054, after startup repair restored the damage-gate marker. The full
offline suite now passes **5,471 tests**, and compilation passes; this remains
regression evidence rather than HERO proof.

## Root Causes

1. **Incorrect observation units.** The willow probe counted an opening hit
   and two automatic-round HP decreases as three actions. It fled at 518/569
   HP after four seconds, before a between-round attack. Its kick-labelled
   forecast contained no executed kick. Tests that fed instantaneous snapshots
   hid this timing error.
2. **Broken scheduling handoffs.** A completed area-reset wait followed by an
   unchanged server reboot could stop the public invocation before reselection.
   An area reset does not require a reboot. Old shop crowds could also outrank
   current hunting crowds; the preceding repair addresses that ordering.
3. **High setup cost, weak amortization.** Travel, potion acquisition, recovery,
   and failed searches consume entire segments. Productive multi-kill sessions
   must be evaluated with these costs included, not by combat-only XP/minute.
4. **Excessive intertwined state.** `starter.py` and `campaign.py` each exceed
   35,000 nonblank lines. Core instructions, README, and roadmap also contain
   thousands of historical lines and conflicting "latest" anchors. This makes
   ordering bugs and stale assumptions harder to detect. Another policy number
   is not an architectural solution.
5. **Stale intent outranking observation.** Run 12774 followed a departing orc
   even after a fresh look showed another local instance. It entered a python's
   room and lost 50 XP on failed recall plus 68 on flee. Run 12771 also guessed
   that a level-8 mage could cast invisibility, despite no observed practice.
   These are decision errors, not reasons to raise arbitrary risk thresholds.

## Changes In This Work Unit

- Reset probes use fresh result evidence, not merged old state. An observed
  unchanged reboot after a completed wait permits ordinary reselection within
  the existing segment budget. Missing observations still wait; exhausted,
  loss, resource, and protection gates remain intact.
- Damage-probe completion now requires three samples **and 6.5 elapsed seconds**,
  or the existing 12-second deadline. This permits an opening wait and a
  follow-up opportunity; it does not guarantee a command executed. Normal
  emergency, source-ceiling, crowd, and runtime checks retain precedence.
- The recorded willow sequence has a decision-path replay: kick replaces the
  premature flee. Counterfactual follow-up damage is explicitly synthetic,
  not represented as a live win. The failed route remains quarantined.
- Learned travel invisibility now requires an audited class/subclass path,
  positive practice, source-formula mana, standing, and no combat. A cast alone
  is not an active affect or permission to ignore a city hazard.
- Magic Shop travel shares liquidation's existing bounded healer wait: at most
  three 12-second pauses, each followed by a fresh locator response. Persistent
  obstruction still stops travel; the runtime boundary interrupts the wait.
  No campaign cooldown, loan limit, or source hazard is erased.
- A fresh source-matched local instance cancels unengaged wandering pursuit
  and requires its own consider. Genuine combat pursuit and ordinary crowd,
  target, resource, and loss gates are preserved. The run-12774 replay changes
  `north` to `consider #23632`; the latter is not a claimed live kill.
- Fixed fame routes now receive the same state-specific source combat envelope
  as source-ranked routes. This closes the gap exposed by run 12912 without
  weakening GMCP authority or turning the source estimate into a claimed kill.
- Revision 264 fills missing fixed-stop HP ceilings from the source mobile's
  rank and level range. The pre-combat gate now fails closed even without a
  live enemy HP snapshot; live verification rejected the 660-HP Secretary
  against a 318-point budget with no additional XP loss.
- Revision 265 closes the aggressive-special ordering gap. A source target
  that can auto-attack on entry must have a source-backed player output
  envelope covering its source HP ceiling before selection; persisted candidate
  records cannot hide a special newly present in the source mirror. The change
  has focused, full-suite, and compilation verification; no live retry has yet
  been claimed.
- Revision 269 binds source route branches to their locator labels. The Forest
  River bed legs now require `where` to report `River bed`; a broad `Forest`
  result proceeds through the safe Forest search instead of entering the
  source-aggressive poison-swarm branch. Six focused forest cases and the full
  5,456-test suite pass. Live run 12941 remains valid crowd-withdrawal
  evidence, not a kill or progression result.

## Revised Work Order

1. Validate these shared handoffs through bounded public runs at actual roster
   levels. No manual attack sequences, credential shortcuts, or name branches.
2. Advance the fresh track to 9 and through the level-10 trainer transition.
   Retain thief and warrior comparisons when a shared capability can be tested.
3. Establish sustained progress: three consecutive bounded public invocations
   with positive combined net XP, repeated useful kills, autonomous maintenance,
   and a level gained. Publish connected time and reset/setup time separately.
   This is the next acceptance gate, not HERO completion.
4. Fix the largest measured blocker to that gate. A failed experiment needs a
   changed input and replay before retry; preserve losses and limit retries.
5. Expand only the next needed level band after executable proof. Broaden
   race/class coverage and Mudlet/VM lifecycle validation after this loop works.

## Architecture Direction

Keep one observation-to-action path: validated input, typed character/encounter
state, capability-authorized action selection, command acknowledgement, and
durable outcome. New control logic belongs in focused existing modules such as
`combat_timing`, `companions`, `flight`, and `sessions`; avoid new parallel
controllers. Extract touched behavior with timeline replays before deleting its
old implementation. Do not attempt a wholesale rewrite during live operation.

Use current status sections for decisions; keep dated reviews and run IDs as
history. The root documentation is now consolidated: the 6,729-nonblank-line
instruction file became a 382-word contributor guide, with explicit operations
in `docs/OPERATIONS.md`. README and roadmap are current usage and delivery gates.
Complete previous documents remain in `docs/history/`; detailed game contracts
remain searchable and applicable, while old checkpoints are historical.
The conversation log was not rewritten. AI personality generation remains separate
from executable combat authorization. Mudlet is a visibility adapter, not a
second game-playing implementation.

## Proof Boundary

The earlier full suite passed 4,566 tests in 181.22 seconds. Eleven damage-window checks
cover the actual four-second sequence, emergency withdrawal, source HP ceiling,
minimum elapsed time, the no-hit deadline, and rearming the clock. Eighteen
focused scheduling checks cover fresh versus cached reboot evidence, segment
budgets, and deterministic preparation deadlines. Compilation also passes.
Travel authorization and city waiting have 36 focused checks. Eight additional
precombat-pursuit cases pass, including source identity, fresh observations,
nontransferable consider, crowd, low health, and retained combat pursuit.
The final full run includes that last repair.
Twenty-two city revalidation checks cover fresh locator evidence, timeout,
missing/blocked locations, article normalization, stale checkpoints, purchase
failure, and adapter opt-in. Compilation and whitespace validation pass.

Public runs 12769-12771 live-validate the reset continuation. One 180-second
wait led to world-time probe 12769, which observed the unchanged September 4
reboot. The same invocation then selected Moria and killed source orc 4004 for
86 objective XP in run 12770. It checked further circuit rooms, found those
targets absent, and returned on movement limits. Run 12771 selected flight
maintenance but stopped at the city hazard preflight before reaching the shop;
no potion purchase or active flight is claimed.

That earlier checkpoint 39173 was level 8, 28,038 XP, fully recovered at healer
3054. Those three runs took 161.23 connected seconds:
32.0 XP/minute, or 15.1 including the reset wait before other setup/development
costs. This is positive XP and a live handoff, not improved throughput, a level
gain, or sustained progression.

The next invocation, runs 12772-12774, found Granny Jenkins crowded, waited once,
then selected Moria after a same-reboot probe. The pursuit error above produced
no kills and a 118-XP loss in 219.12 connected seconds, plus 180 seconds waiting.
Checkpoint 39186 was Astrevo level 8, 27,920 XP, full 113 HP, 324 mana,
220 movement, at healer 3054. Magic Shop
maintenance was not selected, so its new wait and flight purchase remain without
fresh live proof. Across both invocations the net result is -32 XP, not sustained
progression. Do not repeat the lost pursuit as an unchanged experiment.

The timed damage probe still needs fresh live acceptance. Earlier malformed-
enemy rejection has live proof; critical-spell continuation and post-death
handoff still need separate positive cases. Do not combine these claims into
"autonomy works."

## City Obstruction Revalidation

Runs 12775-12776 added 20 incidental XP in 156.89 connected seconds, with no
useful objective kill. Granny remained crowded; the Circus target was absent.
Checkpoint 39196 is level 8, 27,940 XP, fully recovered at healer 3054. The
flight price is affordable, but the old city obstruction still has two
productive-segment cooldown steps. Requiring kills to refresh a wandering
mobile's location can leave travel efficiency blocked by unproductive hunts.

The existing world-time probe now optionally checks that location once, using
the shared bounded locator parser at the healer. It does not cast, buy, borrow,
or travel to a shop. Only a fresh successful same-reboot off-route observation
releases the old route cooldowns; unknown locations, cached evidence, real
purchase failures, funding requirements, loan limits, and combat losses remain.
The next buying trip still runs its own preflight. Source `merc.h:PULSE_MOBILE`
and `update.c:mobile_update` confirm that wandering is independent of player
kills; elapsed time alone nevertheless grants no crossing permission.

Run 12777 live-validates one bounded healer locator after the existing reset
wait. It observed two drunks, on The Main Street and in The Leather Shop, so
the route block and purchase cooldown remained. One `time`, one `where drunk`,
save, quit; 13.77 connected seconds, no movement, cast, purchase, or XP change.
The fresh result is stored as `campaign_city_shop_route_probe`, with run ID
12777. This is live blocked-observation proof; positive clearance is not proved.
The checkpoint validator now uses the shared article-normalizing room parser,
with the exact two-location response as a negative regression.

Run 12778 searched Moria for a centipede but exhausted movement without a kill;
it returned safely in 90.65 seconds. Checkpoint 39205 is level 8, 27,940 XP,
full 113 HP, 324 mana, 220 movement, healer 3054. No gameplay worker remains.
The two runs plus the 180-second reset wait added no XP. Including 12775-12776,
the work unit added only 20 incidental XP, not useful-target progression.

The next source-backed gap is city transit admission. Mobile 3064 is level 2,
unarmed, without combat specials; its source-fuzz bounds are levels 1-4, HP
8-48, peak round damage 35 and critical hit 14, with a 10% greet attack and a
three-instance global reset. The existing
`source_mobile_route_program_attacker_is_bounded` accepts it at level 8 and
113 maximum HP. Apply that existing contract consistently to city shopping,
with fresh exact enemy identity, isolation, health and time bounds. Do not
equate a source-admitted transit risk with a guaranteed harmless encounter,
erase field losses, or count these below-band interruptions as objective XP.

Upstream refreshed successfully at 6:55 PM NZST from `900c615` to
`5fffa4d3f36d2bd6b35dd3e222dc163bcba58efb`. Its new individual/live NPC resistance
overrides change resistance resolution, not the city attacker's HP/damage or
wandering rules. No current area uses `MobResists`, `MobVulnerabilities`, or
`MobImmunes`; support for those optional masks is not claimed by the playtester.
All 354 focused source, population, companion, and city checks pass on the new
revision in 14.90 seconds. The 4,566-test full run above preceded this refresh.

## Bounded City Transit

`city_travel.py` now reuses the existing source admission and owns one
session-local defensive interruption for flight shopping. Departure requires
95% health, standing and nutrition. Live combat requires exactly mobile 3064,
source-fuzz level and HP bounds, a registered city room, at least 70% character
health, and no second attacker. Sixty seconds or the segment boundary ends
the allowance. Finished combat does not itself claim a kill. No timer or
pending action is restored from checkpoints.

An aborted `campaign_city_shop_transit` denies another bounded admission at
the same level/reboot. Missing reboot information cannot reopen it. Fresh short
segments inherit only a missing audit stamp from the campaign's known reboot;
an explicitly observed different reboot remains authoritative. Source admission
can bypass route-only shop cooldowns, not actual purchase failures or losses.
Selection previews do not mutate the old evidence.

Run 12779 killed source mobile 1524 for 113 objective XP in 108.03 seconds.
Its combat name is `a hermit`, while the room description identifies the hermit
crab; live GMCP confirms VNUM 1524, level 5 and 63 maximum HP. Run 12780 found
that target absent and returned in 77.51 seconds. Run 12781 then bought and
quaffed one 131-coin light blue potion, confirmed 34 flight ticks, and returned
to healer 3054 in 16.00 seconds. No new loan, death or XP loss occurred. The
transit audit is `admitted`, not `fighting`: this validates shopping admission,
purchase and active flight, not the defensive-combat branch.

Checkpoint 39215 is level 8, 28,053 XP, 113/113 HP, 324/324 mana and 175/220
movement at healer 3054. The three runs total 201.55 connected seconds, about
33.6 net XP/minute before setup/development time. That is not sustained
progression or a demonstrated throughput improvement. A follow-up selection
stopped at checkpoint 39216 without connecting because field cooldowns remain.
The next explicit bounded reset/reselection will test productive flight use.

The first full integration run exposed an audit-export compatibility bug:
13 minimal-adapter tests failed because the exporter required city state.
The shared optional snapshot boundary now preserves legacy adapters and the
original interrupted-run error. Three reproduced adapter cases pass, as do
84 city/learned-flight checks including five missing-reboot regressions. Final
full verification now passes **4,600 tests in 172.31 seconds** on source
`5fffa4d3f36d2bd6b35dd3e222dc163bcba58efb`. Compilation and whitespace checks
also pass. The failed integration run remains historical counterevidence,
not the final result.

The explicit 180-second reset wait then led to world-time run 12782 (10.29
seconds), Moria run 12783 (94.91 seconds), and restocking run 12784 (15.46
seconds). Run 12783 killed one centipede for 111 objective XP, checked a further
circuit room, and returned after finding that room crowded. It did not return
because of exhausted movement. Food maintenance followed in the same public
invocation: after the baker's affordability response, it bought three pies
instead of six and confirmed them in inventory. Checkpoint 39225 is level 8,
28,164 XP, full 113 HP and 324 mana, 190/220 movement, and 30 flight ticks at
healer 3054.

Together, 12779-12784 produced 224 objective XP from two kills in 322.21
connected seconds, plus the 180-second reset wait. This is 41.7 connected
XP/minute or 26.8 including that wait, before other setup/development costs.
There was no level gain, no multi-kill journey, and no city-combat interruption
to validate the new defensive branch. Keep the sustained-progression gate open.
All test and gameplay workers exited; only the intentional Discord streamer
remains. The conversation file has no malformed headers, and the streamer
was at its current EOF with no queued updates.

## Reconnect Kill Attribution

Run 12783 produced the correct terminal checkpoint 39222: 111 objective XP
belonged to source stop `moria-4002-4017-8`, not the circuit's primary stop
`moria-4002-4020-8`. Startup checkpoints 39223-39224 then reversed that outcome:
the primary gained false kill credit and the successful secondary stop regained
an older connection-loss hazard. Checkpoint 39226 consequently selected no
executable route. This was a reconstruction defect, not a new combat failure.

`_research_segment_views` now projects each circuit onto actually observed
stops, using the authoritative per-run kill ledger. Tagged kills cannot migrate
to the circuit headline; untagged legacy kills retain their original phase.
Secondary views do not inherit a different stop's crowd. Later exact negative
evidence, failed runs, death, and unknown/different reboot stamps remain gates.
An inherited result's reboot cannot override the segment's actual reboot.
The old consider migration no longer reconstructs audited revision-242-and-newer
terminal results; their observed identities instead protect against older
history. Older formats retain their migration path. No historical row is edited,
and this does not clear independent loss or protection evidence.

The repaired public runner selected the previously lost stop in run 12785.
It found rooms 4017 and 4020 absent and a later circuit room crowded, then
returned safely in 96.10 seconds with no XP change. Checkpoint 39231 is level 8,
28,164 XP, full health/mana/movement, healer 3054, and 27 flight ticks.
This proves the positive-history-to-selection handoff, not repeat-kill progress.
Keep the new availability evidence; do not resurrect the old connection error
or count the earlier kill a second time.

Focused verification passes 149 history, circuit, repair and ledger checks.
The new cases cover fresh and already-corrupted checkpoints, repeated replay,
later absence/negative considers, failed runs with and without a kill, death,
empty terminal ledgers, legacy untagged kills and contradictory reboot stamps.
The full suite passes **4,612 tests in 154.35 seconds**; compilation and whitespace
checks pass. Twelve added cases accompany the shared history changes. The first
full run's older-total regression was repaired before this final validation.

The next explicit 180-second wait led to a normal route rotation, not another
connection-failure handoff. Run 12786 killed the hermit crab for 109 objective XP
in 74.71 seconds. Run 12787's wolf attempt added none in 40.30 seconds. Run 12788
revisited the just-killed crab and found it absent, taking another 53.39 seconds.
Together with 12785, this unit added 109 XP in 264.50 connected seconds, plus
180 seconds waiting: 24.7 connected XP/minute or 14.7 including the wait, before
setup/development costs. It is not a throughput improvement or a level gain.
Checkpoint 39244 is Astrevo level 8, 28,273 XP, full 113 HP, 324 mana and 220
movement, at healer 3054 with 20 flight ticks. All workers exited normally.

The next concrete encounter is not hypothetical: run 12785's room-4023 listing
showed three exact centipede instances and no other mobile. Source
`fight.c:violence_update` skips its cross-prototype assistance random gate for
identical prototypes, but still applies the player/helper level-difference
bounds. Source mobile 4002 has no combat special. Assess that group using exact
live identities, source-fuzz limits and measured incoming damage; do not label
it empty, assume it harmless, or erase the prior room-4023 loss. Separately,
12788 is evidence of an unproductive early repeat after consuming a solitary
target. These are the next throughput questions. Source `db.c:area_update`
requires age eight even without PCs and resets age to zero through three;
leaving an area helps but a three-minute wait does not itself prove a reset.

## Crowd Knowledge And Target Identity

The source audit of run 12785 changed the proposed group-fight approach.
`moria.are` mobile 4002 has ACT_SENTINEL, no special, and three resets sharing
a global capacity of three. Reset room 4023 is listed first, so replacements
can accumulate there without ordinary wandering. This is a population/selection
problem, not evidence that the area is empty. In run 12783 the solo level-5,
55-HP centipede died after two chill touches while the character retained all
113 HP. That is a useful solo observation, not a three-enemy damage forecast.

`update.c:4224-4275` loops over combat participants but serializes the primary
`enemy` repeatedly. Its duplicate records cannot identify or level each add.
The existing active-encounter budget must not treat them as independent known
targets. Source `violence_update` still permits same-prototype assistance inside
its level band; attacking all three blindly is not the repaired behavior.

Instead, existing bystander consideration now supports up to three distinct
instances of one identity. Each requires a full matching source description,
a unique live selector, no dangerous behavior, and its own bounded response.
Only exact <=-5 consider evidence discounts a bystander. If one material target
remains, ordinary target consideration resumes with that exact instance. Two
or more material/unknown copies remain crowded; all-below-band copies still
produce an ordinary negative XP-target consideration. No new probe budget or
restored checkpoint permission is introduced.

The same review found a prerequisite targeting defect: GMCP combat names or
room refreshes could lose the considered selector, and subsequent actions could
use a shared keyword or the latest same-name instance. Source-backed combat now
retains its original considered selector until the existing encounter lifecycle
releases it. A stale exact selector may be refused; it cannot silently redirect
an attack to another mobile. Before combat, a changed selector invalidates the
previous consider and requires a fresh one.

The first focused pass exposed two fixture expectations, not live failures:
one omitted the opening damage acknowledgement/source wait; the other expected
an extra probe after ordinary consideration had already rejected the last weak
copy. Their time-ordered corrections pass with the complete focused set of
140 bystander and command-timing checks. Broad regression and fresh public-run
acceptance remain pending at this point. This is not yet group-fight or improved
XP-throughput proof.

The first broad run exposed three regressions in replacement detection. Missing
room selectors are not a positively observed replacement, and an explicit
not-here reply must retain the existing bounded refresh path. The second broad
run exposed 19 pursuit failures after exact-instance cleanup reached an old
mutable-list assumption. Cleanup now replaces the collection, accepts list or
tuple input, removes only the defeated/departed exact instance, and cannot erase
a different same-name replacement. These were integration defects, not evidence
of test-order dependence. All 172 focused pursuit/crowd/timing checks pass.
Final full verification passes **4,633 tests in 154.46 seconds**, including
21 added cases for this work. Compilation and whitespace checks also pass.

The bounded public continuation used one 180-second reset wait, world-time
run 12789 (9.79 seconds), and Moria run 12790 (51.37 seconds). It found the same
three centipedes in room 4023. The bot considered #23772 and #23724 as easy kills
and positively classified #23653 as no match. Their source-fuzz intersection
puts the two material instances at level 4 or 5, not exact observed level 5.
One discounted bystander therefore left two possible combatants, and the
unchanged crowd rule declined combat. All three probes and their individual
outcomes were persisted. This live-validates inspection and negative/positive
bystander discrimination, not a crowd-to-kill handoff or exact-ID spell dispatch.

No XP changed. The 61.16 connected seconds plus reset wait are not a throughput
improvement. Checkpoint 39254 is level 8, 28,273 XP, 3,427 XP to next level,
113/113 HP, 324/324 mana, 213/220 movement, healer 3054, and 18 flight ticks.
All gameplay/test workers exited; only the intended Discord streamer remains.
Its queue was empty at the conversation EOF, and header validation found zero
malformed entries. Current local time remained before the 9 PM commit window;
no commit, push, or remote merge was attempted.

The next concrete work is bounded two-instance encounter admission/control,
using this exact room evidence and existing source/health/damage-window tools.
Do not simply raise `maximum_target_count`: current GMCP duplicates lack distinct
attacker HP/level/IDs, and the existing finishing budget assumes independently
observed targets. Any source-estimated encounter envelope must remain explicitly
an estimate, preserve unexpected-attacker and survival exits, retain the prior
losses, and use the exact selected instance for attacks. Initial progress must
be measured through actual player kills and whole-journey XP, not another round
of repeated crowd inspection. Also evaluate needless reset waits after long
offline development intervals and early repeats of already-consumed solitary
targets; neither should be solved by erasing negative history or adding retries.

## Source-Estimated Pair Execution

The room-4023 replay now admits the two individually considered easy instances
through `encounters.source_pair_budget`, without raising the general crowd
limit. Source ceilings are 65 HP per target, 80 combined peak round damage,
and a 46-HP withdrawal reserve for the observed 113-HP character. The 28-damage
initial allowance covers only a two-round measurement probe, not a guaranteed
whole-fight prediction. Measured combined incoming damage and remaining source
HP ceilings govern continuation; duplicated GMCP remains ambiguous evidence.

Source `handler.c:mana_cost` prices an offensive spell as the greater of its
minimum and `60 - learned percentage`. Chill touch at 35% therefore costs 25,
not the generic forecast's minimum of 10. Pair admission reserves 250 mana for
eight source-estimated damage casts and two failures, plus 15% maximum mana.
This correction is local to the pair admission; other legacy estimates have
not been globally changed or claimed correct.

The session-local pair retains two exact selectors through the first death,
continues the second fight, and does not mark the circuit stop complete early.
A quiet second mobile still requires a fresh look/consider. Both share the
original 45-second deadline and command allowance; no pending rights persist.
Existing class authorization, source/route/loss gates, emergency withdrawal,
unexpected-attacker checks, command acknowledgements, and healer cleanup remain.

All **4,670 tests pass in 158.74 seconds**, including 37 added source-budget,
practice-cost, identity, second-kill, time, health, and resource cases. These
are offline results. Compilation and whitespace checks also pass.

The bounded public acceptance invocation used one 180-second reset wait, then
runs 12791-12793. The 12.90-second world-time probe confirmed the same reboot.
Run 12792 selected Moria but never reached it: mobile 3064 attacked at Temple
Square, then a cityguard joined. The exact combat-text guard detected this
additional attacker despite duplicated GMCP and withdrew. The drunk died for
10 incidental XP before the 68-XP flee cost, producing net -58 XP. Character
HP stayed 113. No pair admission occurred; its audit list is empty. Do not
misdiagnose this as a pair-controller failure or promote it as pair proof.

The same invocation rotated to the Circus in run 12793, found the selected
Midget absent, and recovered at the healer. The three connections total
122.38 seconds, plus the reset wait, with no objective XP. Checkpoint 39265 is
level 8, 28,215 XP, full 113 HP, 324 mana and 220 movement, healer 3054, with
14 flight ticks and armor active. There was no death. All gameplay and test
workers exited; only the intended Discord streamer remains. Its queue was
empty at the conversation EOF, with zero malformed new-format headers.

Source `special.c:spec_guard` selects a combatant below alignment 300 who is
fighting an NPC; it does not ask who initiated that fight. This explains why
an otherwise weak greeter interruption can escalate in town. The next access
repair must use that source relationship and current room evidence, rather
than assume a defensive fight is isolated or repeatedly force the same trip.
Keep the pair acceptance gate open and the 58-XP loss in whole-session results.

The single scheduled local commit succeeded at 9:00:16 PM NZST as `c1c3fc2`.
Nothing was pushed or merged remotely. This final live-outcome documentation
and later conversation entries remain saved locally after that commit; the
next commit attempt must not occur before September 9 at 9:00:16 PM NZST.

## Field Departure And Alignment Investigation

The run-12792 replay now checks the shared city locator at healer 3054 before
field departure. Its room scope follows the actual source route within Midgaard,
plus the fountain preflight; unrelated shop rooms are not added. Source greeter
and guard behavior must exist. A revealed alignment of 300-1000 does not require
this additional guard-interaction check. Otherwise it shares the existing three
12-second healer waits, with fresh rechecks, ordinary invisibility authorization,
and the original segment deadline. An explicit absence or off-route result can
continue the same route. Missing output remains inconclusive. The separate
`campaign_field_city_preflight` audit does not turn into shop-funding flags.
No historical loss, crowd record, or retry allowance is cleared.

The user questioned whether GMCP really conceals alignment. Investigation
distinguishes the sender, transport, and consumer:

- At source revision `5fffa4d3f36d2bd6b35dd3e222dc163bcba58efb`,
  `update.c:4079-4086` explicitly sends real GMCP alignment at level >=10 and
  50000 otherwise. Nearby combat-stat fields use the same concealment pattern.
- `protocol.c:3307` maps GMCP_ALIGNMENT to Char.Worth/alignment.
  `UpdateGMCPNumber` at line 4368 stores the supplied numeric value unchanged.
- Run 12792 raw event 8009246 contains Char.Worth alignment "50000", level "8".
  Parsed event 8009257 retains that value; the client did not invent it.
  Runs 12791 and 12793 independently show the same low-level value.
- Run 12760 at level 18 and run 12766 at level 25 report alignment "1000".
  These are recorded comparisons, not new live connections.
- MSDP is different: `update.c:3589` sends actual alignment unconditionally.

The earlier wording "GMCP alignment bug" was imprecise. The observed behavior
matches an explicit server masking rule, not corrupted GMCP or a parser mapping
error. The bot defect was interpreting 50000 as actual high alignment in its
guard-bystander rule. That consumer now requires a real numeric 300-1000 value;
it does not prohibit legitimate values below character level 10 if the server
later supplies them. Raw state and transcripts remain intact. No upstream MUD
source was modified. Always-accurate GMCP would require changing the server's
level gate, which was not part of the requested investigation.

All **4,701 tests pass in 200.53 seconds**, including 31 new field-city scope,
three-class departure, bounded wait, absence, timeout, hidden-alignment, and
boundary cases. The 118 focused city checks also pass. The first focused run
exposed two test-construction errors (wrong source room and helper name), fixed
before final validation. Fresh live field-departure and pair-kill acceptance
remained pending at that boundary; no gameplay worker was launched during the
alignment investigation itself. Subsequent acceptance is recorded below.

## Live Departure And Defensive Endpoint Continuation

The next public invocation, runs 12794-12796, took 248.00 connected seconds
and added 218 objective XP without a death or loss. Run 12794 observed a city
obstruction, slept twice for 12 seconds at the healer, then observed clearance
and continued normally. This is live blocked-to-clear field-departure proof.
The Illusionist endpoint contained both its target and the Midget, not an empty
room. That mixed-prototype pair remains outside the new same-prototype allowance.
Run 12795 killed the Bearded Lady for 97 XP; 12796 killed the hermit crab for
121 XP. Both recovered fully at the healer. The Moria circuit already receives
a three-kill budget; the singleton route's one-kill limit was not its blocker.

The following invocation, runs 12797-12799, took 302.37 connected seconds and
lost 68 XP. The recently killed Bearded Lady was absent. The crab had actually
respawned: run 12798 observed instance #23779, source mobile 1524, live level 3,
29 maximum HP, attacking Astrevo. Source level 5 allows that fuzzed load. With
113/113 HP and 324/324 mana, the bot fled solely because the target was below
the useful XP floor. Flee failed; combat recall charged 68 XP. The enemy was
already at 11 HP before recall executed. This is an avoidable decision loss,
not evidence that the crab was too strong. Preserve the original loss record.

Run 12799's funding search found no kill before movement recovery; the next
selection stopped before connection because no currently eligible funding
target remained. Flight had expired. Final checkpoint 39287 is at healer 3054,
level 8, 28,365 XP, full 113 HP, 324 mana, and 220 movement. Across the six
connections the net gain is 150 XP in 550.37 seconds, about 16.35 connected
XP/minute before setup/development. No reset wait was used in these invocations.
There was no level gain or sustained-throughput proof.

The repaired decision shares `_active_encounter_decision`, not a second combat
controller. Only an already-engaged, single exact source endpoint attacker may
use its 30-second finishing window while remaining excluded from useful XP.
Fresh live level/HP, source hazards, equipment, 70% character health, nutrition,
spell practices/resources, damage measurement, and normal emergency/segment
boundaries remain authoritative. Another attacker or changed identity ends the
allowance. Its session-local selector/level/reboot/stop binding cannot resume
from checkpoint data. The existing audit distinguishes this as
`below-band-endpoint-defense`; completed kills retain `objective_eligible=False`.

Practice-based mana pricing now also applies to this shared finishing estimator,
not only source-pair admission. For the observed chill-touch practice of 35%,
the two-action finish reserves 100 mana including utility/failure allowance,
plus the existing 15% maximum-mana reserve. Other legacy forecasts have not
been globally corrected. The captured-GMCP replay exposed a second ordering
gap: enemy refresh can clear the selector before the endpoint is rebound.
Exact source/room matching now refreshes that binding before defense assessment;
it does not switch an ongoing considered attack to a replacement.

The 214 focused checks pass, including 33 added endpoint-defense cases across
mage, thief, and warrior, negative boundaries, scope expiry, acknowledgement,
incidental accounting, and disconnect cleanup. A read-only replay against the
current source also selects chill touch and estimates 12 incoming damage with
a 46-HP reserve. This is offline counterfactual evidence, not a live kill.
Final full verification passes **4,734 tests in 163.38 seconds**. Compilation,
whitespace checks, and conversation validation pass; there are zero malformed
new-format conversation headers. The final review also added a one-use guard:
a valid empty enemy update clears encounter identity but cannot authorize a
second defensive endpoint fight in that session. No repeat, reset, loan, or
historical loss gate was reopened by this fix.

No further live connection was launched during that work unit. The initial
diagnosis of a funding/reset status mismatch was incorrect: the
`CampaignResult.awaiting_area_reset` property recognizes `ready` plus the
existing waiting message. The fourth attempt stopped because all four normal
attempts had been used; the outer loop correctly checks that limit first.
Preserve that budget, rather than changing a working status contract.
`_reopen_provision_funding_after_reset_wait` already owns bounded revalidation
and preserves prior attempts in history. The next action is a new public
invocation with an explicit reset retry, not a fabricated scheduling fix or
manual removal of funding attempts. Fresh outcome evidence will determine the
next actual blocker.

## Early Funding Location

The new public invocation did use its explicit 180-second reset wait and then
ran funding segment 12800. Four existing reset/history tests pass. The city
departure waited twice, observed clearance, and continued. At the carrier's
reset room 4022, `where orc` positively located **the large orc** in **The valley**.
The exact short-name parser correctly excluded other orc prototypes; this was
not a keyword or absence failure. The bot ran out of movement en route and
returned without a kill or proceeds. It woke to eat during healer recovery.
The connection lasted 91.79 seconds, plus the 180-second offline wait, with
unchanged 28,365 XP. Checkpoint 39295 was level 8, full 113 HP and 324 mana,
206/220 movement, healer 3054. No death or XP loss occurred.

The source route explains the repeated failure. The original approach to 4022
costs an estimated 140 movement; the subsequent eleven-step route to the
reported valley costs 107. Total 247 exceeds the character's 220 maximum even
before fighting. Asking at safe same-area entry room 4000 instead costs 45
movement on approach and 102 to the valley: total 147. The complete route is
22 rather than 32 movement commands. An earlier commentary estimated eleven
commands saved; the exact comparison is ten, and 100 estimated movement saved.
These are source estimates, not observed post-change savings.

The funding execution builder now uses `_source_ranked_early_locator_route`
and the existing source locator/relocation planner. It shortens only a fully
known movement-only approach whose preflight is retained and whose first
same-area observation point and reset fallback are source-safe. Random exits,
closed/locked doors, missing links, later preflights, and hard route hazards
retain the old route. Sentinel, stash, and confused-mobile handling is unchanged.
New-origin relocation paths must be source-safe; the normal exact target,
consider, crowd, equipment, provision and loss checks still authorize combat.
No target identity, candidate admission, loan, retry, or historical record is
changed to make this plan run. An ordinary legacy staging call still moves its
locator to the target area as before.

All **4,751 tests pass in 158.79 seconds**, including 17 new planner/runtime
replays and 109 existing funding/source-route checks. The real-source replay
consumes the captured locator rows and goes from 4000 directly toward 4031,
without first visiting 4022. Its final test name and explicit old/new route
length assertions were corrected and the 17 focused tests passed again.
Fresh live carrier acquisition and useful progression remain separate gates.

Run 12801 live-validates the earlier observation point. After its explicitly
budgeted 180-second reset wait, it located the large orc from room 4000. The
mobile had moved again, now to the grassy foothills room 4034. The existing
source-name parser ignored other orc rows and the runner followed the correctly
rooted path to the actual source-matched carrier, instance #23698. It arrived
with 113/113 HP and 61 movement, without visiting the old reset room first.
This is live navigation proof, not the hypothetical valley cost comparison.

Source mobile 4004, instance #23632, was also present. The required-loot branch
immediately recalled because of that source-capable bystander, before any
consider or bounded crowd recheck. Source 4004 is a level-5 ordinary unarmed
wandering orc with no special or program; its live load was not considered.
Do not assume its exact level, harmlessness, or willingness to assist. Assess
the existing bystander-consider/crowd-retry integration before widening combat
admission or adding more routes. Both exact room selectors were visible.

Run 12801 took 85.21 connected seconds, with no combat, XP change, or proceeds.
Checkpoint 39303 is level 8, 28,365 XP, full 113 HP, 324 mana and 220 movement
at healer 3054. Both gameplay invocations and the full test worker have exited.
Across 12800-12801, 177.00 connected seconds plus 360 seconds of explicit reset
waits yielded no income or XP. The shorter approach removed the demonstrated
movement blocker but has not established a productive money loop or sustained
levelling. Preserve this distinction and the original failed approach.

### Required-Loot Bystander Assessment

The run-12801 replay reproduces two independent premature-stop causes. The
required-loot pre-combat gate rejected an ordinary source-identified bystander
before the shared assessment could run. That shared assessment also used broad
keyword matching, mistaking `orc` for the registered exact target `large orc`.
It now uses the stop's existing exact identity rules. A single positively
identified carrier and one probe-eligible ordinary bystander can reach the
existing consider/crowd evaluator without changing combat admission. A fresh
exact below-assistance result is respected by the loot gate as well; other
hazards, attack interruptions, absent carriers and uncertain identities retain
the previous return behavior. The existing three probes per visit, five-second
acknowledgement window, ephemeral evidence and configured crowd waits remain.

The real-source replay now issues `consider #23632` in room 4034 with 61
movement instead of recalling. Fourteen added cases and 147 existing focused
cases pass. Full verification passed **4,765 tests in 159.59 seconds**, with
compilation and whitespace checks also clean.

The public four-attempt invocation used its one explicit 180-second reset
wait, then opened two live runs. Funding run 12802 used three existing healer
waits and ended with the town hazard reported on Main Street; the unrelated
bakery location was also retained. Circus run 12803 likewise completed three
waits and ended with the hazard at Temple Square. Both routes include those
locations. The first and fourth campaign attempts stopped before connecting
with funding unavailable. No wait, retry, loss, or attempt record was erased.

Runs 12802 and 12803 took 55.69 and 51.77 connected seconds: **107.46 seconds
plus the 180-second reset wait, zero kills, zero XP change, zero proceeds**.
Both saved and quit safely at healer 3054. Checkpoint 39315 retains level 8,
28,365 XP, 113/113 HP, 324/324 mana and 220/220 movement. All workers exited.
This does not exercise the new endpoint assessment live or demonstrate a
productive funding loop. Keep that acceptance gate open and do not label the
town obstruction as an absent carrier or empty hunting area. Assess the shared
departure restriction against fresh source/live evidence before spending more
whole journeys on unchanged town waits; retain the real guard-attack evidence.

### Departure Is Not A Target Attempt

The source and complete run-12803 locator rows confirm a real city obstruction,
not an alignment or room-parser bug. The drunk has a 10% greet attack, and the
cityguard prototypes include wandering level-15 guards and sentinel gate guards.
`mprog_greet_trigger` requires visibility; learned invisibility already provides
an audited bypass. The fresh mage's score is neutral, with no intellectual
practices left. The final positions in 12802-12803 were on their required paths.

The scheduler nevertheless appended a failed `moria.are:4005:4022` funding
attempt after run 12802 never left healer 3054. It then selected a Circus hunt
behind the same city obstruction. The new early completion branch separates
that decision from target-outcome reconciliation. A fresh, successful run must
explicitly report a stop before departure, zero outbound index, matching level
and reboot, a living noncombat healer state, unchanged known XP and no kills.
It records `field_city_departure_blocked` and the run/policy audit, spends the
segment, preserves existing funding/loss history, and stops the public invocation
without a new automatic wait or another destination. Other failures keep their
normal handling. A cached marker cannot authorize this classification.

The 24 new cases cover the independent evidence boundary, funding and source-hunt
checkpoint persistence, failed-run exclusions, and the public four-segment loop.
Existing city tests also prove the marker is set only at the actual bounded stop.
Historical run 12802 remains preserved, not retroactively edited. Full verification
passes **4,789 tests in 158.86 seconds**; fresh live validation is pending.

Run 12804 then observed the drunk in Eastern End of Poor Alley, outside the
actual city route. It departed normally with `stopped_before_departure=False`
and finished with outbound index 11, so it was correctly not classified as a
no-travel deferral. The carrier locator reported `The large orc / The cave`.
Several Moria rooms share that label. The bounded search passed room 4010 and
reached 4025 through 4018; 4025 contained two source-4001 garter snakes but no
carrier. The existing required-loot hazard branch recalled at full HP/mana and
118 movement. No bystander consider, attack, loot or sale occurred.

Source 4001 is sentinel, nonaggressive, and has no mobile programs.
`special.c:1211-1231` applies its poison special only to a character already
fighting that snake. This does not authorize attacking the crowd. It does
justify examining the existing bounded search continuation through a passive
room when the sought carrier is absent. Preserve exact identity, no-combat,
known exit, movement, and segment bounds; do not add a blanket special exemption.

The run took **98.02 connected seconds plus the 180-second explicit reset wait**,
with zero XP or income and no loss. Checkpoint 39323 is level 8, 28,365 XP,
113/113 HP, 324/324 mana, 220/220 movement at healer 3054. The invocation ended
after its next preconnection funding-unavailable result. The new successful
no-travel classification still has offline proof only. The earlier ordinary
bystander repair also remains unexercised live. Kestrel and Aeloria were inspected
read-only: both retain their earlier protection-recovery requirements; no new
roster combat proof is claimed.

### Passive-Room Search Continuation

The premature required-loot gate in run 12804 prevented the existing absent-target
logic from inspecting the next mapped cave. `_required_loot_search_can_leave_passive_room`
now recognizes only a source-identified passive room with no carrier and no
combat. It lets the normal hunt planner record absence and advance its existing
stop list. It does not add a parallel search controller, open combat on a poison
crowd, manufacture target presence, or increase a locator/route/retry allowance.
The current live first-hop exit and full known source path must remain open,
nonrandom, nonprivate, recallable and independent of flight; source transit
hazards remain authoritative. Normal health, mana, movement and nutrition gates
still decide whether to continue. Runtime and emergency returns cannot reopen.

All 36 new checks pass, including a real-source replay of the exact run-12804
plan. It retains the locator's area-level presence evidence, records absence
in room 4025, and moves south toward the next pre-existing stop at 4018, without
attacking either snake or adding stops. Full verification passes **4,825 tests
in 162.38 seconds**, with compilation and whitespace checks clean. The old run
remains preserved as the counterexample.

Runs 12805-12806 subsequently completed acquisition and liquidation through the
public bounded command. The early locator reported the carrier in `The tunnel`;
the existing search inspected several matching rooms and found its exact live
instance in room 4027. Two acknowledged chill-touch casts helped kill the
level-5 source-4005 carrier for **133 objective XP**. Combat timing recorded
three acknowledgements including the opener, with zero timeouts. The character
looted the ring, sacrificed the corpse, recalled, and recovered at healer 3054.
No passive snake crowd appeared, so this does **not** live-validate the new
passive-room branch or the earlier ordinary-bystander assessment.

The next segment sold the yellow and green ring at the Leather Shop for **9
gross copper-equivalent**. Its explicit loan notice and GMCP currency change
show only **4 carried copper** from that sale. Source `act_obj.c:5771-5781`
credits integer `cost / 2` to both the character and bank debt; at this odd
price, one copper is lost to rounding. The sacrifice separately paid one silver
coin, or 10 copper. Carried currency therefore rose **50 -> 60 -> 64**, not by
the gross sale total. Existing `loot_sales.sold_coins` and funding `proceeds`
record gross prices, not spendable income; do not describe them as cash gains.
The source-backed debt treatment needs to inform future funding forecasts.

The two runs took **121.36 + 33.28 = 154.64 connected seconds**, plus the one
explicit **180-second reset wait**: 51.6 XP/minute connected, or 23.8 including
that wait, excluding development time. There was no death or XP loss. Final
checkpoint 39335 is level 8, 28,498 XP, **113/113 HP, 324/324 mana, 172/220
movement**, at healer 3054; 3,202 XP remains to level 9. The public invocation
then stopped before another connection with funding unavailable. This proves
one carrier-to-sale cycle, not sustainable funding, sustained progression, or
a level gain. Next compare accessible coin/loot candidates by real retained
income and whole-journey cost; repeating a 4-copper sale is not the master goal.

### Funding Hazard Ownership (September 9)

Checkpoint 39329 correctly ended run 12805 without a funding-route hazard.
Startup checkpoint 39330 then restored the old city-departure obstruction.
The read-only startup replay identifies `_open_campaign`'s call to
`_reconcile_maintenance_fastwalk_state(state, state)` as the cause: the completed
carrier had no owning hazard, so the fallback attached an inherited field abort
as though it were a fresh funding observation. The reset history and original
successful run were intact; this was a reconciliation error, not a new hazard.

Startup now explicitly disables fresh-observation recording during checkpoint
cleanup. A narrow history repair handles already-replayed restrictions after
legacy candidate inference. It requires the latest connected funding run to be
successful at the same level/reboot, a newly completed matching carrier,
unchanged inherited abort text, no owning start/end funding hazard, and a living
noncombat healer return with known nondecreasing XP and no recorded loss. It
removes only that candidate from the replayed hazard; all other hazards and
historical loss/research/reset records remain. A newer failure prevents repair.

The actual checkpoint-39335 read-only replay changes only
`campaign_maintenance_route_hazards` and is idempotent. With the actual reboot
kill counts, selection changes from unavailable to source carrier 4005. This
fix restores a valid option; it does not make that option economically strong
or claim that the next encounter will be present or safe. Forty added tests
cover clean and corrupted full startup, repeated reconciliation, legacy
inference, and positive/negative ownership and survival boundaries.

Full verification passes **4,865 tests in 163.87 seconds**; compilation and
whitespace checks also pass. The public two-segment invocation then repaired
the actual checkpoint, cleared the stale hazard durably, and selected funding
without another reset wait. Run 12807 found the carrier in room 4024, issued
three acknowledged chill-touch casts, and earned **175 objective XP**. The
terminal counter records four acknowledgements including the opener and zero
timeouts. It looted the ring, sacrificed the corpse for 10 copper-equivalent,
and recovered at healer 3054. Run 12808 reopened the campaign without restoring
the old hazard, then sold the ring at the Armoury for **8 gross coins**, of
which **4 became carried money** and 4 repaid bank debt.

The runs took **140.31 + 19.29 = 159.60 connected seconds**, with no reset wait,
no death, and no XP loss: 65.8 net XP/minute connected, excluding development
and process setup. Carried currency rose **64 -> 74 -> 78**. Checkpoint 39341
retains no funding-route hazard and ends at healer 3054 with **113/113 HP,
312/324 mana, 188/220 movement**, level 8, 28,673 XP, and 3,027 XP to level 9.
Both gameplay segments and the full-suite worker have exited. This is fresh
live proof of the startup repair and another acquisition/sale cycle, not
sustained levelling or a sustainable funding yield. The latest two invocations
combined added 308 XP over 314.24 connected seconds plus 180 seconds waiting;
their combined rate including that wait is only 37.4 XP/minute.

Next address the economic scheduler at the actual frontier: optional-flight
funding currently takes priority even with carried food, while this loot source
retains only 4 sale coins per trip. Compare accessible net-income alternatives
and a bounded productive ground-hunting fallback before spending more cycles
on one weak carrier. Do not erase food funding, protection/loss gates, existing
attempts, or source route constraints to make an alternative selectable.

### Funding Reward Handoff (September 9)

At checkpoint 39341, the mobile ledger already contains the 133- and 175-XP
source-4005 kills. Its exact route result still reports zero XP from the earlier
NPC-finished encounter. Funding is already objective-bearing; the defect is
missing per-route reconciliation, not missing XP or a reason to increment the
kill counters again. Fresh completion and bounded history repair now project
eligible positive kills onto the exact source policy/VNUM, while preserving
the funding phase and original run ledgers. Later failures, death, loss,
unknown XP, changed identity, and reboot scope retain their exclusion gates.

The replay also finds an explicit reset clear older than the new funding kills.
Only a successful attempt with a timezone-aware start later than the latest
matching retry checkpoint may supersede that clear. Unknown or newer reset
ordering remains closed. The actual read-only repair changes only the source
research result and its cleared-policy entry, returning the same state on a
second pass. The reward becomes 175 XP, without changing mobile kill counts.

The existing ground fallback can now consider a measured low-yield flight
funding source as well as an exhausted funding pool. It requires carried food,
a same-reboot observed flight quote and exact latest sale, and an ordinary
ground candidate with no additional missing protection. Gross sale value is
only an upper bound on spendable income, not a debt-adjusted forecast. No
extra loan, reset, action, or segment budget is introduced.

An isolated selector probe incorrectly suggested sanctuary preparation was
the remaining blocker. That probe omitted `_ensure_gear_catalog()`, leaving
the source world unavailable to familiar admission. With the full source world
and selected checkpoint candidate, familiar admission is true and sanctuary
is not required. The public startup confirms the ordinary source-ranked hunt.
This corrects the preliminary protection-mismatch diagnosis: an incomplete
inspection context is not evidence that the live runner lacks the capability.
Funding does build its stops without character-aware input, but that difference
did not block this ordinary hunt. Preserve its existing risk and familiar gates.
Read-only selector comparisons must initialize the same source/history context
as the public runner before drawing conclusions about missing capabilities.

The new checks cover historical ownership, reset ordering, idempotence, full
runner completion, failures, missing live XP despite merged old XP, and
ground-preference boundaries. All **4,916 tests pass in 164.48 seconds**, including
51 new funding-reward cases; compilation and whitespace checks pass.

Public runs 12809-12810 live-validate startup reward repair and its handoff to
ordinary hunting. The earlier 175-XP record is retained in checkpoint 39345.
Run 12809 summoned and grouped the familiar after two failed recitations, then
confirmed the bounded sleep withdrawal and killed the exact source-4005 target
for **195 objective XP**. Three damage commands, including the opener, were
acknowledged without timeouts. It used free body-part food, looted the ring,
sacrificed the corpse, and returned to full resources at healer 3054.

Run 12810 sold the ring at the Leather Shop for 8 gross coins, retaining 4
after debt repayment. Including the 10-coin sacrifice, carried currency rose
**78 -> 92**. Connected time was **147.76 + 21.95 = 169.70 seconds**, with no
reset wait or XP loss: 68.9 XP/minute connected, excluding development/setup.
Checkpoint 39350 is level 8, 28,868 XP, **113/113 HP, 312/324 mana, 172/220
movement**, at healer 3054, with the source reward updated to 195 across the
reconnect. There are 2,832 XP left to level 9. Fresh funding-completion merging
remains offline-only proof because this live kill was an ordinary hunt.

The last three invocations added **503 XP** in 483.95 connected seconds plus
180 reset-wait seconds: 45.5 XP/minute including that wait. No level was gained,
so the sustained-progression gate is still open. One-target journeys and
familiar preparation cost remain the measured throughput work.

### Familiar Opening Death (September 9)

Run 12811 found another exact carrier in room 4024. Its fresh consider was
`looks like an easy kill`. At event 8017886 the bot ordered familiar #23800 to
attack target #23798. The response at 8017888 contains three familiar hits,
the target's death, and `Ok.` together. No player XP was awarded. The next
decision incorrectly issued `kill #23798`; the target was already gone. The
bot collected and ate the severed leg but failed to record or loot the corpse.
It returned safely without XP or currency change in **151.29 seconds**. The
next selection stopped before connecting because funding was unavailable.

The terminal record has empty completed/objective kill ledgers; preserve this
raw counterexample. Checkpoint 39357 is level 8, **28,868 XP, full 113 HP,
324 mana, 220 movement**, healer 3054, and 92 carried copper-equivalent. The
latest work-unit total is +195 XP in 320.99 connected seconds, or **36.5 XP/min**,
with no reset wait, death, or XP loss. This is not sustained progression.

The observer now adopts a completed opening encounter only from the pending
order's exact unique source target, unchanged room, positively owned/present
unique familiar, and the source damage/death pair without player XP. It cancels
the player opener, records zero XP with `objective_eligible=False`, and enters
the existing corpse-looting path. It does not add attack authority or rewrite
historical runs. Fragmented replies use the bounded preparation buffer; a later
acknowledgement cannot duplicate the encounter. Source identity, ownership,
room changes, another attacker, and ambiguous same-name instances are tested.

The same response also exposed an overly broad familiar-loss check: `pony`
anywhere in a chunk plus `is dead` anywhere else retired the companion even
when its target died. Loss now requires the familiar's own exact named line.
A real familiar death cancels its pending opener, but does not finish the
player's still-active fight. A quoted familiar death does not revoke ownership.
These are offline replay repairs; fresh live acceptance is still pending.

Next investigate a source-bounded solo opening for sufficiently weak loaded
targets, avoiding unnecessary familiar mana and NPC finishing blows. Source
`act_info.c` calculates `diff = victim->level - ch->level`; the easy-kill band
is -4 through -2. For the source-level-7 carrier's 5-9 load range and a level-8
player, this narrows the current target to levels 5-6, not the whole source
upper range. Existing source formulas bound a common level-6 target at 84 HP
and an unarmed peak round at 50. This is a lead, not implemented authorization:
require fresh exact-instance consider, full source/rank/weapon/special checks,
class damage and resource budgets, and ordinary survival/loss gates before
removing any familiar requirement. No broad death-text parser rewrite is claimed.

Final validation passes **4,933 tests in 165.38 seconds**, including 17 new
opening-death cases and 97 focused companion/timing checks. No fresh live
acceptance of the opening-death repair is claimed. Both bounded invocations
and all validation workers have exited; the master goal remains active.

### Considered Solo Substitution (September 9)

The next capability uses the run-12811 easy-kill observation without assuming
the source's whole 5-9 load range applies to this particular target. Only an
exact-instance, source-named easy-kill reply to the current consider command
can establish the -4 through -2 band. Keep its room, stop, character level,
reboot and 20-second freshness scope connection-local. Normal selection,
crowd, protection, route-loss and retry gates still apply.

`encounters.source_solo_budget` applies full source HP/rank ceilings and the
existing short-encounter cost calculation. It excludes unreviewed specials,
programs, armed loads, excessive reset populations and other nonordinary
targets. In the level-8 replay, the highest possible easy load is level 6:
84 HP, 50 peak round damage, five conservative chill-touch actions, 175 mana
including two utility actions, and a 46-HP reserve. Actual 35% practice makes
each spell cost 25 mana, not its nominal minimum of 10. With a 324 maximum,
224 current mana passes the 15% reserve and 223 does not.

That is a **funded counterfactual**, not the actual resource state from the
failed opening. Run 12811 snapshot 8017877 had 182 mana before consider
8017878 and order 8017886; it must retain the familiar path. Run 12809 had
only 124 mana at snapshot 8016883 before its opening order. A regression now
uses the real 12811 balance. These observations make pre-target preparation
cost the next optimisation, not a reason to lower the solo mana reserve or
claim the existing run would have passed the new mode.

Outdoor familiar preparation is unchanged. Once the solo budget passes,
`FamiliarStandby` issues one exact owned-instance sleep order and requires
`The pony sleeps.` within five seconds before the player can attack. `Ok.`
alone, quotations and late replies are not confirmation. The one-target
`SourcePairEncounter` then owns the existing measured-damage checks, live
enemy bounds, spell acknowledgements, 45-second window and command cap.
There is no companion damage credit. On completion, confirm one exact stand
order before ordinary onward travel; emergency recovery and runtime cleanup
can interrupt the handoff. Only audit outcomes persist.

This prevents unnecessary NPC participation in a funded low-load fight; it
does **not** eliminate summoning mana or prove cheaper preparation. Stronger
or underfunded loads retain their normal familiar contract. A positive exact
player kill before its first enemy snapshot can close the one-target budget;
it cannot claim another target, an NPC finishing award, or a new attack.

Offline verification passes **4,988 tests in 165.64 seconds**, including 55
new solo/standby cases. Compilation and whitespace checks pass. The separate
opening-death repair remains replay-only until exercised live. A bounded
public invocation is now checking the new mode; no fresh live solo proof is
claimed by this implementation entry.

The public check has now completed: two selections stopped before connecting,
at checkpoints **39361 and 39364**, both `provision_funding_unavailable`.
One explicit 180-second reset wait reduced the existing source-4005 retry
cooldown from 3 to 2. It did not clear the prior incomplete-fight result or
establish that the target was absent. The normal ground fallback remained
unavailable; `--retry-stalled` does not override that cooldown. No extra retry
was launched and no historical evidence was erased to force a solo test.

There were **zero connected seconds, zero new runs and zero XP** in this
invocation. Latest saved checkpoint 39364 retains Astrevo's last live state:
level 8, 28,868 XP, full 113 HP/324 mana/220 movement, healer 3054 and 92
carried copper-equivalent. These are retained values, not fresh observations.
Live solo opening/kill/wake acceptance and sustained progression remain open.
The next execution must respect the remaining retry budget or use another
genuinely executable roster frontier; do not describe this preconnection stop
as a transport hang or another empty-area observation. Test and gameplay
workers are terminal; only the intended Discord streamer remains active.

### Earlier Ordinary-Hunt Location (September 9)

The remaining retry countdown was inspected without mutation: two authorized
reset waits expire the counter and its old result together. No countdown repair
or extra retry permission was needed. Run 12812 then reached Moria's original
reset before issuing `where orc`. The reply positively located the exact large
orc in The cave, but the subsequent search exhausted movement. This is not an
empty-area observation. It added no XP in 144.72 connected seconds, plus 360
seconds of reset waits. Checkpoint 39379 is Astrevo level 8, 28,868 XP, full
113 HP/324 mana/220 movement, healer 3054, and 92 carried copper-equivalent.

Ordinary source-ranked hunts now share funding's early same-area locator.
Required familiar staging must remain on the outbound prefix. Keep the full
original route's validation and admission, city preflight, exact instance and
consider checks, bounded search, and original reset fallback. Special transit
recovery is not shortened again. Sentinel, closed/random, hard-hazard, or
late-preflight approaches retain their existing route.

The real-source 12812 replay shortens the initial approach from 21 to 13
commands while retaining outdoor staging at 4002. Only the exact large-orc
locator row is used; ordinary orc rows do not match. This is offline navigation
evidence, not live movement savings. Fourteen new integration/planner cases and
the actual-resource solo regression bring the full suite to **5,003 passing
tests in 173.87 seconds**. Compilation and whitespace checks pass.

The next public invocation rotated to the existing thief campaign. Run 12813
followed a departing exact hobgoblin-servant instance into the adjacent room,
rechecked both occupants, rejected the below-band alternative, and finished the
original opponent for **183 objective XP**. Both attack commands were matched,
with no acknowledgement timeout. Run 12814 sold its shirt and pants for gross
59 and 63 coins; bank deductions leave 29 and 31 spendable coins respectively.
Do not report the gross 122 as carried income. The hunt also sacrificed the
corpse for one silver coin and ate its severed leg.

Those runs took **126.65 + 39.58 = 166.23 connected seconds**, no reset wait,
death or XP loss: 66.1 XP/minute excluding startup/development. Checkpoint
39387 is Serevian level 11, **50,894 XP, 186/186 HP, 150/172 mana, 224/250
movement**, healer 3054. The route includes a door command, so it correctly
retained the old approach and did not validate early location. One kill and
sale are useful roster evidence, not sustained progression or a level gained.
Fresh live early-location and considered-solo acceptance remain pending.

### Preparation Acknowledgement Ownership (September 9)

Run 12815 reached the shortened approach's retained staging room 4002, after
two town-obstruction waits, but never reached its early locator. Event 8019852
sent summon at 14:46:08.463 UTC. At 08.711 the server sent sunset text and a
prompt. The controller immediately treated the missing spell reply as failure
and sent recall at 08.715. The actual positive summon arrived at 09.571, only
1.108 seconds after dispatch. This was a controller acknowledgement error,
not failed recitation, an empty hunting area, or exhausted combat resources.

The run added **zero XP in 94.46 connected seconds**, preceded by three
explicit 180-second reset waits. Checkpoint 39404 retained level 8, 28,868 XP,
113/113 HP, 320/324 mana, 220/220 movement, healer 3054. Preserve the failed
preparation and late success in the raw transcript. No live early-location
or solo acceptance was collected.

`FamiliarPreparation` now waits through unrelated output and partial replies.
The original 30-second overall deadline covers summon, fresh complete look,
and group. Known source refusals stop promptly; only explicit recitation
failure permits the existing three-attempt retry. An unsolicited prompt before
the look cannot complete its listing, and a prompt without a newline cannot
hide the subsequent spell/group line. Long room descriptions retain listing
evidence while the stored buffer stays bounded. Expiry reopens decision
processing without waiting for another prompt; late success cannot revive it.
Ordinary travel/attack waits, while emergency and runtime authorities remain.

The old missing-acknowledgement result was also a permanent route exclusion.
Current startup now applies the existing dynamic-failure classification without
requiring a policy-version bump. Temporary preparation failures acquire the
existing bounded retry handling, retaining their original reason. Exact
refusals, ambiguous identity, fatal and negative-consider results are excluded.
The actual 39404 read-only replay adds only `retryable_failure=True`; it does
not clear the failed run, fabricate a target observation, or create a retry.

A separate fresh-state replay exposed split-consider inconsistency: the exact
source observer recognized the easy-kill reply, but ordinary consideration
remained unknown and pending when the phrase crossed chunks. Both now consume
the same scoped reassembly, preserving explicit rejection rules. Twelve new
cases exercise fragmentation, room/level/reboot/stop/selector/time changes,
and stop rejection. This is offline protocol proof, not an observed kill.

### Solo Continuation And XP Accounting (September 9)

The next public invocation completed run **12816** after one explicit
180-second reset wait. It validated successful familiar preparation, the
13-command prefix to room 4002, early `where orc`, and two moves to the target
in room 4011. It considered exact instance 23803, positively confirmed owned
instance 23819 sleeping, then attacked without companion damage credit. This
is live early-location and solo-opening evidence, not a completed solo kill.
No interleaved world tick occurred in this preparation; that specific repair
still has replay proof only.

At 7.32 seconds the player had 107/113 HP and 212 mana; the opponent had
64/79 HP. One chill-touch missed. The old probe demanded 16 damage and had
observed 15, so it fled despite affordable remaining damage and time. Solo
continuation now uses remaining HP, source-formula spell costs, observed damage
rate and incoming loss within the original 45-second/command budget. It waits
for the existing cast cooldown before the next spell. Low resources, inadequate
time/commands, missing standby, and no progress still cause withdrawal. Ten
replays cover these boundaries; the fixed continuation needs fresh live proof.

The initial report of **-121 XP was incorrect**. Raw `Char.Worth` event
**8020332** reports **28,815 XP**, following a 68-XP flee penalty and 15-XP
partial reward: **net -53** from 28,868. The text parser expanded DD4's LF-CR
endings into blank lines, separating the refund from its penalty. Derived
event 8020344 then subtracted another 68 XP, producing 28,747. Checkpoint
39419 and the stored loss magnitude inherit that error. They remain preserved
as historical evidence, not the authoritative current XP total. Do not count
the correction as earned XP or erase the genuine loss/protection requirement.
A fresh server observation was still needed at this stage; run 12820 below
subsequently confirmed the correction without rewriting this history.

Incremental newline normalization now handles LF, CR, CR-LF and LF-CR, including
split pairs, while preserving real blank lines. Repeated losses in one
connection still reconcile GMCP against their textual evidence. Thirty tests
cover the actual numbers, ordering, fragmentation, repeated losses and reset.
This does not claim that every quiet-flush/partial-refund timing is proved.

Run 12816 took **76.54 connected seconds**, with zero objective kills and no
death, ending at healer 3054 with 113/113 HP, 316/324 mana and 220/220 movement.
Its invocation spent three 180-second reset waits in total, including two
subsequent preconnection deferrals. Together runs 12815-12816 cost **171.00
connected seconds plus 1,080 reset-wait seconds**, excluding development and
startup, for **net -53 XP**. This is not improved throughput. Public retry
handling reopened preparation after one wait; the direct helper's three-step
countdown must not be described as the only public scheduling path.

Final offline verification passes **5,080 tests in 172.35 seconds**. The next
acceptance is a useful player finishing blow and completed solo wake/return,
followed by repeated kills and a level gained through the public runner.
Preserve the failed-route history; do not reopen it merely to exercise a test.

### Live Accounting Acceptance And Roster Rotation (September 9)

Runs **12817-12819** used one three-segment public thief invocation. The first
spent 131 coins on a light blue potion, confirmed flight and returned to the
healer in 18.10 seconds. The air hunt then met an aggressive griffin, source
1001 at live level 8 in room 1008. It reduced that opponent from 101 to 46 HP
before a second griffin visibly arrived and attacked. At 172/186 character HP,
the existing multiple-enemy boundary withdrew. Do not deduplicate away the
second attacker merely because Telnet GMCP repeats the primary enemy fields:
`update.c` builds those fields from `enemy` for each qualifying room character.
The arrival and damage text independently confirm this particular second foe.

The flee cost 99 XP and refunded 55. Raw GMCP event **8021171** and derived
state agree at **50,850 XP**, exactly **-44**, without double subtraction.
This is fresh live acceptance of the LF-CR accounting repair, not a successful
hunt or proof of every possible fragmented/quiet-flush ordering. A sanitized
fixture preserves the loss/refund and worth data, with six ordering/chunk tests.

The third segment searched for source hobgoblin 4052 but encountered aggressive
warrior **4051**, live level 8, 112 HP, in room 4053. Automatic combat killed
the warrior for **297 XP**; the character finished combat at 107/186 HP, looted
and sacrificed the empty corpse, ate its heart, then recovered at healer 3054.
The terminal objective list correctly remains empty: this is an incidental
kill, not evidence that the requested hobgoblin was found or killed. Observed
skills contain no executable between-round damage action; do not invent one.

Durations were **18.10 + 92.85 + 156.19 = 267.14 connected seconds**, no reset
waits, net **+253 XP**, no death: 56.8 net XP/minute excluding startup and
development. Checkpoint 39430 is level 11, 51,147 XP, full 186 HP/172 mana/250
movement at healer 3054. A positive invocation is useful, but it gained no
level and produced no planned objective kill. Target acquisition and travel
amortization remain unresolved, not a reason to claim sustained progression.

The existing recovery CLI then opened **run 12820** for the mage, confirmed
**28,815 XP**, and saved/quit at the healer in **10.68 seconds**. Normal public
startup merged this fresh character snapshot into **checkpoint 39433**, without
a new gameplay connection or hunt. Current HP/mana/movement are 113/316/220.
The funding stop and loss/protection metadata remain. Its historical -121
loss-magnitude record is still an accounting artifact; the real run delta is
-53. No old event/checkpoint was rewritten, and the 68-point baseline correction
must not be added to earned XP. Safe-source stash inspection found no currently
admissible level-8 route; it did not launch an unchanged funding retry.

### Resume The Actual Interception Waypoint (September 9)

The next two-segment public invocation completed **12821-12822**, both with
zero XP. The tower visit found servants, not an empty area: it considered one
approach bystander and the destination instance, both below-band. Another
same-name approach instance was not considered. The source identifies these
servants as sentinel mobile 9411 with several reset rooms and fuzzy live levels;
one weak instance does not prove that every instance is weak. The initial
endpoint-restriction explanation was incomplete: the follow-up below identifies
a lost bystander-to-target handoff even though both safe rooms were planned.

Run 12822 exposed a separate reproducible route bug. Early `where orc` selected
a cave search. In room **4010**, the runner considered instance **2763** and
correctly rejected its `no match` response. Interception had overwritten the
current leg's move index with its endpoint index. On rejection the controller
advanced to a leg beginning with **4015**, although live exits from 4010 are
only **4011** and **4002**. It recalled with `field route could not find GMCP
exit to room 4015`. This was not a changed map or missing server exit.

The controller now retains its pre-interception context for field travel as
well as outbound travel. A below-band rejection can restore only a matching
observed waypoint with an unfinished destination-guided leg, no explicit abort,
no crowd/route hazard, and the original unconsumed stop. The existing route
continues north to 4011 rather than jumping to 4015. The rejected sighting is
retained; a later endpoint requires a new exact-instance consider. Command-only
routes and changed/missing contexts do not receive this continuation. Existing
health, transit, runtime, source, loss and search limits remain unchanged.

Thirteen new checks reproduce both the old recall and corrected next movement,
test an unvisited final stop, fresh endpoint consideration, and nine negative
boundaries. Together with the existing starter and locator cases, **1,393
focused tests pass**. Fresh live waypoint-resume and subsequent useful kill
acceptance remain pending; no route quarantine was cleared to force them.

The follow-ups cost **82.79 + 59.74 = 142.53 connected seconds**, no reset waits.
All five thief segments total **409.67 connected seconds for net +253 XP**,
about **37.1 XP/minute**, excluding startup/development. Checkpoint **39441**
retains level 11, 51,147 XP and full resources at healer 3054. Including the
separate 10.68-second mage baseline audit gives **420.35 connected seconds**
for this work unit, still only 253 earned XP. No level or planned objective
kill was gained. Do not omit the two unsuccessful trips from throughput.

Final verification after the interception repair passes **5,099 tests in
173.96 seconds**. Compilation and whitespace checks pass. The commentary
streamer was at the conversation EOF with an empty queue; gameplay workers
were terminal. The master goal remains active and unproved. Next validate the
waypoint handoff through normal public selection, then improve acquisition of
useful exact instances at the actual roster levels without speculative bands.

### Preserve Bystander-To-Target Ownership (September 9)

The next public invocation completed **12823** (59.70 seconds) and a world-time
probe **12824** (6.10 seconds), separated by one authorized **180-second reset
wait**. The hunt considered three separate gnome-woman instances, each below
the useful XP band; it produced no kill, XP, or death. The final selection
stopped before connection with protection recovery still unavailable. Current
checkpoint **39452** retains Serevian at level 11, **51,147 XP**, full resources
at healer 3054. Across the seven thief connections the net remains **+253 XP**
over **475.46 connected seconds**, plus that wait. This is not improved
throughput or live proof of the route-position correction.

Further source/planner inspection found that the tower plan already contained
both safe servant reset rooms, **9417** and **9418**. Mobile **9411** is sentinel
with multiple resets; the separate dangerous 9419 room was not authorized.
Run **12821** reached 9417 with exact instances **23815** and **4903**. Event
**8022876** considered the first as a bystander; **8022884** confirmed it was
below-band. That audit cleared the main consider fields. The interception's
follow-up did not re-enter target evaluation, and **8022887** moved upstairs,
leaving the second instance unchecked. No extra reset-room planner is needed
to repair this specific miss.

The replay reproduced that exact erroneous `up`. The controller now resumes
the shared target evaluator when its primary check is unset, and an unresolved
interception holds outbound travel even when no command is ready. The replay
instead issues **`consider #4903`**, then waits for that target's own response.
A synthetic positive reply opens only that instance; two negative replies end
the evaluation without attack. Thirteen new cases cover the live ordering,
pending/silent checks, source-level rejection, combat interruption, emergency
return, and the runtime boundary. Existing searches, retry limits, prototype
exclusions, source admission, and historical losses are unchanged. Fresh live
acceptance and sustained useful kills remain pending.

The full offline suite passes **5,112 tests in 174.93 seconds** after the
handoff repair. Compilation and whitespace checks pass. No additional live
retry was launched against the unchanged unavailable protection decision.

### Terminal Lookup And Displaced Smithy Evidence (September 9)

Kestrel's ordinary public continuation spent minutes reconstructing history,
then stopped before connecting with protection recovery unavailable. Checkpoint
**39454** retains level 24, **333,533 XP**, and the original combat loss. The
synchronous history phase suppressed the usual asynchronous progress heartbeat;
this was local work, not a permission prompt or live MUD stall.

Completion and failure reconstruction called `list_events` for every run, then
selected just the last matching state. The new `get_latest_run_state_event`
uses the existing run-ID index and descending event ID, returning one full
payload. Completion/runtime-cap and failure retain independent precedence;
later writes are observed without a cache. Replay stores without the targeted
method retain their original event-list interface. No schema migration,
historical deletion, loss-gate change, or new gameplay retry is involved.

A read-only comparison of Kestrel's latest 64 run IDs returned identical event
IDs and payloads: **40,198 rows / 77,452,452 payload characters** versus **62
matching rows**. The first old-path read took 16.906 seconds, versus a direct
read below that timer's resolution. Two high-resolution warm comparisons
returned identical results in **0.162923/0.153756 seconds** for full reads and
**0.006090/0.006621 seconds** for targeted reads. These are query benchmarks,
not full-startup speed ratios. A subsequent public invocation completed in
**20.64 seconds**, retaining the exact same checkpoint and unavailable decision,
without connecting. Filesystem caching and the already-repaired checkpoint
also differ from the first invocation; do not attribute the entire reduction
solely to this code change.

Aeloria's public runs **12825-12826** took **142.38 + 24.51 = 166.89 connected
seconds**, no reset waits, no XP or death. The second sold one yellow-and-green
ring for one coin. Current checkpoint **39462** is level 18, **158,168 XP**,
218/218 HP, 628/628 mana, 272/320 movement, healer 3054, and 112 carried copper
equivalent. The older guardian death and protection marker remain.

The hunt supplied a concrete acquisition counterexample, not an empty area.
Source mobile **29953**, the lemming smithy, is sentinel with one reset at
**29966**. Raw response **8024559** positively lists exact instance **18435**
in adjacent room **29964**, alongside a lemming miner. Fresh Room.Info agrees
with 29964 and its exit to 29966. The runner opened the east door, walked past
him, and recorded absence in the workshop before recalling. Earlier source
and live evidence already demonstrate combat displacement of this sentinel.
The present source-reset/endpoint admission does not recognize a newly seen
displaced instance on approach; the current-session pursuit exception cannot
be restored across connections. Next repair this exact acquisition boundary
with fresh source-unique identity, bounded source/room/exit evidence, and normal
consider/crowd/combat gates, not a guessed VNUM or reused old instance ID.

Fourteen terminal-lookup regressions and **47 focused storage/evidence tests**
pass. The full suite passes **5,126 tests in 175.74 seconds**; compilation and
whitespace checks pass. At this checkpoint the displaced-sentinel repair was
not implemented or live-validated. The bystander handoff and field waypoint-resume fixes still
need fresh live acceptance. No useful target kill or new level was gained in
this work unit; the master objective remains active.

### Fresh Displaced-Target Acquisition (September 9)

The run-12825 replay now considers the smithy's freshly listed exact instance
in room 29964 instead of opening the door and walking past it. Identity is
inferred from the globally unique full source room description, not represented
as an observed GMCP VNUM. The single sentinel reset has capacity one; its room
and the current room share a reciprocal, unlocked ground link confirmed by
the planned route and live exit. Random, no-mob, wall, cross-area, aggressive,
scripted, ambiguous-description, and multiple-reset cases do not qualify.

This connection-local binding expires after 30 seconds and cannot transfer
between rooms, stops, levels, reboots, selectors, or connections. It permits
normal target evaluation, not an attack without consideration. The actual
source-catalog replay includes the low-level miner and positively owned pony:
it requires the smithy's own consider, exact companion order, and positive
order acknowledgement before the player opener. A duplicate room listing in
the initial fixture falsely counted the smithy twice; refreshing through the
normal command boundary corrected that fixture without changing crowd gates.

All **33 focused cases pass**, including the old walk-past counterexample,
negative considerations, low health, dangerous bystanders, and stale identity.
Audit outcomes are stored separately from confirmed GMCP pursuit evidence;
no instance, pending action, or combat permission is restored from them. Normal
loss history, target admission, retry limits, and recovery remain unchanged.
Full verification passes **5,159 tests in 175.53 seconds**, with compilation
and whitespace checks clean. Fresh live acceptance remains a separate gate.

The following public invocation used one **180-second reset wait** and opened
only **run 12827**, a normal sanctuary-recovery selection, not the smithy hunt.
It inspected Moria room **4064** for mobile **4055**; raw responses **8025564,
8025575, and 8025579** show no mobile there. It returned, recovered at healer
3054, and quit safely in **89.08 connected seconds**, with no combat, item
acquisition, XP, or death. The next normal selection stopped without connecting.
Checkpoint **39472** is level 18, **158,168 XP**, 218/218 HP, 628/628 mana,
300/320 movement, and 112 carried copper equivalent. No historical loss or
protection marker was cleared. Runs 12825-12827 therefore total **255.97
connected seconds**, plus the reset wait, for zero XP; do not omit the failed
protection search or call it progression.

The current low-level `safe_reset_only` sanctuary plan intentionally visits
one room and omits the normal carrier locator to avoid the deep maze. This
explains the limited search; it does not establish that Moria or the carrier's
entire reachable range was empty. Next assess a source-bounded locator/search
within the already-accessible corridor, retaining excluded deep-room hazards
and ordinary combat checks, or find another executable protection source.
Do not repeat the same empty-room trip without changed evidence. The new
displaced-sentinel path and earlier bystander/waypoint repairs still need
fresh live acceptance; no new level or sustained progression is claimed.

### Bounded Protection-Carrier Search (September 9)

Run 12827's reset-only plan omitted the existing locator controller. Source
mobile **4055** is a stay-area wanderer with two resets, both capacity two.
The current route checker admits **4064** and adjacent **4063** at level 18;
deeper paths cross separately registered transit hazards. A single empty reset
room is therefore insufficient search evidence, but removing all deep-route
restrictions would also be unsupported.

`locator_paths.py` now builds a bounded same-area ground graph using the shared
route hazard assessment. It avoids closed/wall edges and random, private,
solitary, no-recall, and water rooms. An eight-room fallback sweep has a total
24-move budget; the existing controller can make one locator refresh with a
separate maximum-24-move relocation. These remain inside the original runtime
and command limits. Source labels outside the executable graph have empty
routes, preserving positive sightings without claiming absence. A shared label
such as "the maze" authorizes only its accessible mapped subset.

The reset-only required-loot handoff retains the existing carrier, potion,
pre-entry scan, health, consider, and kill-limit contracts. It asks `where
hobgoblin` at the original fastwalk endpoint **4014**, before the six-move final
approach. The real-source replay of a maze sighting reaches **4063** and issues
an exact-instance consider. A sighting only in the large cave returns before
that approach, with `target_absent=False`. No source exclusion, campaign retry,
loss record, or permission is reset to make this plan executable.

The full offline suite passes **5,183 tests in 206.84 seconds**. The new module's
**24 checks** also pass after extending its real-source replay through endpoint
consideration. Two previous campaign assertions were updated from a one-stop
plan to the locator plus endpoints 4064/4063, retaining explicit deep-room
exclusion and the original one-kill limit. Compilation passes. The current
source planner takes approximately 8.8 seconds in a separate cold-process
measurement; this is preparation cost, not XP throughput. Live protection
acquisition and subsequent sustained XP remain unproved at this checkpoint.

The next public invocation used one **180-second reset wait**, then selected
sanctuary recovery and opened **run 12828**. It spent **67.22 connected seconds**
on city departure checks and the three existing short healer rechecks, without
reaching Moria. The final locator response **8025968** lists two "The drunk"
entries at **Main Street** and **The Main Street**. The abort text says the
hazard was "in room 3001", but that is the observation origin, not a reported
target location. Do not use that message as proof of the mobile's room or
prototype. The source/live identity and room-label handling of this departure
restriction require inspection before another unchanged attempt.

There were no kills, acquired potions, XP, deaths, or carrier locator actions.
The terminal's `fastwalk_target_absent` is false. The new carrier plan and its
exact-consider handoff therefore remain offline-verified only. Current
checkpoint **39480** is level 18, **158,168 XP**, full 218 HP and 628 mana,
312/320 movement, healer 3054, and unchanged 112 carried copper equivalent.
The following normal selection stopped before another connection. All gameplay
workers are terminal. Across 12825-12828 the net remains zero XP over **323.18
connected seconds plus 360 seconds of reset waits**; safe returns are not
sustained progression.

### Visibility-Aware Field Departure (September 9)

Run **12828** was not evidence that GMCP alignment was wrong: its raw
`Char.Worth` event **8025743** reports alignment **1000**, also retained in
`state.progress`. Raw `Char.Affect` events **8025756/8025895** instead show
active invisibility with **18/17 ticks** remaining during the failed departure.
The fixed-route greeting preflight ignored that effect.

At source pin `5fffa4d3f36d2bd6b35dd3e222dc163bcba58efb`,
`mob_prog.c:mprog_greet_trigger` requires `can_see` for ordinary GREET, unlike
ALL_GREET. Mobile **3064** has no detection flag, special, reset equipment, or
script that grants detection. `handler.c:can_see` therefore rejects an invisible
player. The new source predicate checks those properties, exact source identity,
and level bounds; it is not a general invisibility-based route override.

The shared field preflight and program pre-entry scan now use a fresh
connection-local GMCP affect with at least two ticks remaining. Neither marks
the underlying check completed. Expiry, disconnect, explicit loss, other
hazards, combat, and emergency return retain their ordinary checks. Source
dispel can announce loss before a lingering affect record disappears, so the
exact loss line revokes the exemption even when fragmented. A positive fade
message requires a new GMCP confirmation before restoring it. Pending scans
retain ownership and unrelated required-loot scans are unchanged. Persisted
audit records do not restore authorization.

The misleading abort now reports the observed street labels separately from
observation origin 3001, retaining the established historical classification
prefix. Historical raw messages and loss records remain unchanged. All **32
focused cases pass**, and the full suite passes **5,215 tests in 202.50 seconds**.
At this checkpoint the repair is offline-verified; a bounded public continuation
is in progress, not yet proof of departure or a useful kill.

The public invocation subsequently used one **180-second reset wait** and only
**run 12829**, a **9.91-second** world-time probe. Its ordinary reselection
stopped before another connection with sanctuary recovery unavailable. It did
not exercise invisible departure or the new carrier search. Checkpoint **39488**
retains level 18, **158,168 XP**, 218/218 HP, 628/628 mana, 312/320 movement,
and healer room 3054. The whole 12825-12829 comparison is zero XP over **333.09
connected seconds plus 540 seconds waiting**. No extra unchanged live retry was
launched to force acceptance.

### Idempotent Sanctuary Attempt History (September 9)

Inspecting that unavailable decision found another concrete defect:
`_repair_sanctuary_resource_acquisition_history` initialized a reconstruction
from the latest saved count, then added the same historical failures again on
every startup. Around run 12829, the counter rose **22 -> 24 -> 26 -> 28**, even
though no sanctuary hunt connected. A minimal replay turned one recorded
failure into counts two and three merely by running reconstruction twice.

The repair now builds the supplied history independently, using the first
segment's starting counter for any omitted prefix. A matching saved counter is
a floor, not an additive seed. Positive acquisition retains its existing reset
semantics. A later actual failure counts once; overlapping or repeated reads
cannot manufacture another. The old checkpoint count of 28 is not represented
as 28 actual hunts and is not silently rewritten. Actual earlier failures, the
terminal route result, and the guardian's **-3,768 XP** protection marker remain.
Correcting legacy totals or granting a changed-condition retry is separate work.

Twelve new cases cover repeated and partial windows, the actual count shape,
prefix evidence, acquisition, level/reboot boundaries, absent/dead outcomes,
and input immutability. Together with four existing acquisition/terminal cases,
**16 focused tests pass**. Read-only replays against the latest 64 segments for
each of Aeloria, Astrevo, Serevian, Kestrel, and Dorrik produce identical
checkpoints on both passes, with no changed keys. Full verification passes
**5,227 tests in 208.45 seconds**; compilation and whitespace checks pass.
No live hunt or new level is claimed by this
accounting correction; executable protection acquisition and sustained useful
combat remain the progression gates.

### Revision 243 Revalidation And Run 12830 (September 9)

Revision 243 permits one revalidation only when the saved result is the exact
run-12828 drunk-GREET failure, the level and reboot still match, protection is
still required, and practiced invisibility is source-authorized. The migration
archives that result, preserves the historical attempt count and guardian loss,
and consumes its marker before connection. A fresh terminal result closes the
marker; it cannot create a second retry.

Run **12830** live-validated the corrected city boundary. Aeloria crossed all
six registered GREET checks with fresh invisibility, with no route hazard, then
reached Moria. `where hobgoblin` reported targets in **The maze** and **The large
cave**. The then-current safe graph inspected room **4063**, found no carrier,
rechecked once, recalled, recovered at healer 3054, saved, and quit. There was
no potion, kill, XP change, death, or loss. The second requested segment stopped
before connection. Checkpoint **39495** remains level 18 at **158,168 XP**;
12825-12830 total zero XP over **412.86 connected seconds plus 540 reset-wait
seconds**. This proves departure and safe return, not protection acquisition.

### Invisibility-Aware Carrier Paths (September 9)

The next source audit found that DD4 ordinary aggression checks `can_see` in
`update.c`, while `handler.c` makes a mobile without `AFF_DETECT_INVIS` unable
to see an invisible player. `special.c:spec_poison` acts only after combat has
already started. The short Moria corridor's snake, orcs, and warriors have no
detect-invisibility affect or source program. The prior locator therefore
discarded reachable rooms that the required live invisibility already protects.

The source route predicate now permits that narrow case only for noncombat
travel. It rejects detecting or above-HERO mobiles, any source program, reset
equipment, unknown or pre-combat specials, and deliberate combat endpoints.
Campaign dispatch broadens the plan only when the class/subclass registry and
positive observed `invis` practice authorize the spell; the live runner still
requires and restores the effect before movement. Ordinary characters retain
the previous planner. The invisibility-only search may inspect 12 rooms but
keeps the original 24-step, runtime, command, locator-refresh, target, consider,
crowd, resource, and return limits.

The generated level-18 Moria plan maps the reset tunnel, seven maze rooms, and
four large-cave rooms; its complete fallback circuit costs 18 steps. The 33-case
carrier suite and a 141-case combined visibility/sanctuary/hazard suite pass.
Full verification passes **5,250 tests in 248.61 seconds**; compilation passes.
The expanded corridor has no fresh live proof and the revision-243 attempt is
spent. Validate it only after a new policy-authorized condition, while using
another roster track for immediate progression work.

### Revision 244, Two Reserves, And Caster Openers (September 9)

Revision 244 opened one exact revalidation after run 12830 had positively
located the Moria carrier but the prior safe graph could not reach it. Runs
12831-12833 proved the invisibility-aware corridor, live potion acquisition,
and two reachable source carrier resets. They also exposed that the generic
combat-potion path consumed one newly acquired reserve against the second
carrier. Recovery now derives its requested count from those source resets and
disables sanctuary consumption during a two-copy acquisition.

Run **12838** started with an empty pouch, killed two large hobgoblins for 100
and 110 objective XP, and received 170 incidental XP. It issued two confirmed
`put purple pouch` commands, no `quaff purple`, and checkpointed two verified
reserves at healer 3054. This is live proof of the complete empty-to-two
recovery path, not sustained levelling. Run 12839 then sold incidental loot for
3 copper without consuming either reserve.

Loss policy now records a sticky segment-wide sanctuary-use fact while keeping
the existing per-fight latch reset. A first unprotected source-route loss may
receive one sanctuary-backed retry; a loss after sanctuary was spent is already
that protected attempt and is quarantined. Run **12840** consumed one reserve
against the chief gnome, lost 232 XP, earned 16 partial XP, and returned fully
recovered. Its checkpoint records a protected net loss of 216 XP and preserves
the second potion.

Run 12840 also showed that a generic `kill` opener could allow a complete enemy
round before a mage's first active spell. The runner now uses the exact
source-planned direct spell as the opener only with class/subclass registration,
positive observed proficiency, availability, an exact target, and enough mana
to retain 15%. Run **12842** live-validated an acknowledged opening
`burning hands` cast, then faerie fire and another timed cast. The 398-HP eel
still failed the live exchange projection: 88 damage dealt versus 65 received,
with about 239 further incoming damage forecast. Aeloria withdrew for a net
127-XP loss, returned fully recovered, and the protected route was quarantined.

Runs **12831-12842** netted **+1,490 XP over 1,265.54 connected seconds**,
approximately **70.6 XP/minute**, including maintenance and failed research.
Checkpoint **39544** is Aeloria level 18 at **159,658 XP**, full 218 HP, 628
mana, and 320 movement in healer room 3054, with no purple potion. Full offline
verification passes **5,280 tests in 272.95 seconds**; compilation and whitespace
checks pass. Next recover the bounded reserve, prefer demonstrated productive
current-band routes over additional costly probes, and raise mage damage
throughput through source-audited training and equipment before widening the
frontier.

### Revision 245 Locator Completion And Productive Handoff (September 9)

Run **12843** positively located two Moria carriers but acquired neither. The
bounded source plan favored nearby duplicate room labels and omitted the unique
reachable `The hole` label. At room 4064, the live locator then selected a
zero-length relocation for `The tunnel`, re-inspecting a room already proved
empty. Its delayed `look` was additionally vulnerable to an unrelated sanctuary
wear-off message and prompt being treated as a completed listing. The run added
no XP or potion and returned safely to healer 3054 in **60.53 seconds**.

The planner now ranks an unrepresented normalized room label ahead of duplicate
labels while retaining the 12-room and 24-step ceilings. Locator relocation
requires a nonempty path. A field `look` remains pending until output includes an
actual `[Exits: ...]` room-listing line; unrelated output cannot advance the
circuit. Silence triggers one retry after five seconds and then a bounded safe
return. Revision **245** opens exactly one same-level/reboot revalidation for
run 12843's evidence shape, checkpoints it as attempted before connection, and
closes it from the fresh acquisition result. Loss, crowd, route, resource, and
protection gates remain unchanged.

Run **12844** live-validated that repair. Aeloria traversed the corrected circuit,
continued after confirmed empty rooms, found source mobile **4055** in room
**4070**, and killed it for **100 XP** despite its below-band consider solely to
recover required protection. She looted object **4050**, put the purple potion
in her pouch, recalled, and recovered fully at healer 3054. The revision marker
is `succeeded`; no retry remains.

Run **12845** immediately validated the useful handoff. The current source-ranked
planner selected the previously productive Dwarven Homestead giant. Aeloria cast
armor, quaffed the reserve, opened with acknowledged `burning hands`, and killed
the giant for **581 objective XP**. Seven damage commands were acknowledged with
zero timing failures. She recalled at 128/218 HP and ended safely at healer 3054
with 218/218 HP, 571/628 mana, and full movement. Runs **12831-12845** total
**+2,171 XP over 1,543.20 connected seconds**, approximately **84.4 XP/minute**.
Checkpoint **39558** is level 18 at **160,339 XP**. Full verification passes
**5,291 tests in 271.94 seconds**; compilation and whitespace checks pass. This
proves locator-to-protected-kill capability, not sustained autonomous progression
or HERO.

### Revisions 250-251: Invisible Transit And Closed Exits (September 9)

The generated Ambush route to mobile **4519** was previously rejected because
it crosses ordinary aggressive source mobiles. Revision 250 admits only the
source-proven visibility case: every transit attacker must lack intrinsic or
equipped detect-invisibility, source programs, dangerous pre-combat specials,
and an above-HERO fuzz ceiling. Dispatch additionally requires an audited
class/subclass path, positive observed `invis` practice, enough mana, and a
fresh connection-local affect with at least two ticks. The runner rechecks that
evidence before every outbound move; expiry, explicit wear-off, combat, or
reconnection fails closed. No target, consider, crowd, damage, loss, or return
gate is bypassed.

Run **12855** crossed the 23-step route to Ambush room **4525**, including the
fixed fanatical-guard room, under fresh invisibility with no forced combat or
visibility lapse. The room then appeared three times with the exit line
`[Exits: north east [south] [west]]` and exact mobile instance **#3144**, but
the listing recognizer stopped at the first inner closing bracket. It exhausted
its one five-second retry and returned safely without considering or attacking.
Checkpoint **39613** retained level 18 and **161,098 XP**. This proves the
visibility route, not endpoint or progression behavior.

Revision 251 accepts the complete one-line exit boundary while retaining the
existing mobile/object parser. The run-12855 replay recognizes Haglik's source
room description, ignores object instances #3111 and #3110, preserves the
unconscious prisoner as a separate bystander, and chooses `consider #3144`.
The campaign migration reopens only the exact same-reboot parser abort after a
safe healer return with no combat, death, enemy record, combat target, or XP
loss. It preserves the original run and checkpoint and consumes one corrected
revalidation at source-hunt dispatch.

Run **12856** live-validated the complete repair. The listing cleared
immediately and the exact consider returned `Haglik is no match for you`.
Source `do_consider` maps that line to a level difference from -5 through -9,
so the bot correctly marked the live load below band, declined combat, recalled,
and recovered at healer 3054. Checkpoint **39617** remains level 18 at
**161,098 XP**. Runs **12846-12856** netted **+759 XP over 969.27 connected
seconds**, about **47.0 XP/minute**, with no level gained. Full offline
verification passes **5,331 tests in 281.53 seconds**; compilation and whitespace
checks pass. The next planner view rotates to an Arachnos guardian candidate;
audit its prior loss evidence before another live connection.

### Revisions 252-253: Wanderer Transit And Double Reserve (September 9)

Revision 252 recognizes both source route-rejection forms covered by DD4's
visibility check: a fixed aggressive transit attacker and an aggressive
wanderer that can reach the route. Admission still requires positive practiced
`invis`, sufficient mana, exact source mobile identities, no hard route hazard,
and proof that every listed aggressor lacks detect-invisibility. It does not
relax endpoint, crowd, consider, damage, loss, or healer-return gates.

Run **12857** live-validated the 51-step Crystal route with six source-checked
aggressors and a fresh invisibility affect. The White Stag was absent, so the
bot returned safely without combat. Run **12858** reached an exact Wyvern
ranger and correctly rejected `no match for you` as below band. Run **12859**
reached the Solace Secretary, measured 61 outgoing damage against 47 incoming,
and withdrew when the projected kill crossed the 50-HP reserve. The flee cost
**117 XP**. Run **12860** then killed Moria mobile **4055** for **110 XP**,
looted object **4050**, stored the purple potion, and recovered fully.

That first-potion result exposed a generic double-reserve deadlock. The selector
suppressed further sanctuary recovery after any same-reboot acquisition, while
its hypothetical second-potion check updated the observed pouch count but not
the authoritative verified ledger. Revision 253 permits a top-up only when one
sanctuary reserve exists and the source-audited caster frontier still lacks a
blindness recovery reserve; the simulation now advances both ledgers to two.
Run **12862** selected the repaired handoff, found the Moria carrier absent, and
returned with the original potion intact. It proves selection and safe absence
handling, not the second acquisition or caster combat.

Checkpoint **39652** is Aeloria level 18 at **161,091 XP**, 218/218 HP,
628/628 mana, and 320/320 movement in healer room 3054. Runs **12857-12862**
netted **-7 XP over 491.97 connected seconds**, plus one 180-second reset wait.
Full verification passes **5,334 tests in 288.77 seconds**. Recheck the carrier
after a later reset, then validate the selected caster-special route and useful
XP before claiming policy 253 live progression.

### Revision 254: Healer-Backed Mage-Special Recovery (September 9)

The second-potion handoff was safe but shared one reboot-scoped Moria carrier
across the roster. Source `special.c` shows a stricter alternative below mobile
level 20: `spec_cast_mage` can blind and weaken but cannot curse, dispel, or
energy-drain. `do_recall` does not reject blindness, and Midgaard mobile 3012
is fixed in room 3054 with `spec_cast_adept`, which automatically casts cure
blindness.

Revision 254 admits that alternative only for a fixed mage special whose
candidate level fuzz matches current source and stays below 20. Every reset
room and direct flee destination must exist and permit recall, one exit must be
traversable, the character must begin at healer 3054 without curse/no-recall,
and the source healer reset must still match. Cleric specials, wandering
casters, stale records, random rooms, missing exits, and missing healer evidence
fail closed. The generated field stop rechecks the special and level boundary;
all ordinary sanctuary, consider, crowd, damage, resource, and runtime gates
remain active.

Run **12863** live-selected the king of the hobgoblins through this gate. The
exact mobile was present in room 1569 with five source-proven trivial
bodyguards, but `consider #1062` returned `no match for you`. The bot did not
spend sanctuary or attack. It recalled, slept at healer 3054, and logged out
fully recovered at checkpoint **39657**, level 18 and **161,091 XP**. This
proves real campaign selection, route execution, exact targeting, and below-band
rejection. It does not prove caster combat, blindness, healer curing, useful XP,
or improved throughput. Full verification passes **5,345 tests in 289.52
seconds**. Rotate to the next source candidate rather than repeating this
below-band mobile.

### Runs 12864-12867: Unproductive Aeloria Rotation (September 9)

Four bounded Aeloria segments added no XP in **313.27 connected seconds**. Run
**12864** found the lemming in black robes but rejected its live consider as
below band. Run **12865** spent 10 mana refreshing learned flight. Run **12866**
confirmed the White Stag absent from Crystal, and run **12867** found the Olympus
jailer absent. Every segment returned safely to healer room 3054. This rotation
is negative throughput evidence, not frontier progress, and motivates following
an executable roster blocker instead of repeatedly inspecting unavailable mage
targets.

### Revision 255: Bounded Fixed-Route GREET Admission (September 9)

Kestrel's run **12868** spent **107.10 seconds** without reaching Moria because
three exact `where drunk` checks found mobile 3064 on the watched Midgaard route.
Source identifies one unarmed level-2 mobile with no special and a 10% GREET
attack program. The existing bounded program-attacker evaluator already proved
that interruption safe for much weaker characters, but the fixed-fastwalk guard
had no character HP and could not call it.

Revision 255 supplies current maximum HP to that guard. It admits only one exact
GREET attacker that passes the established source level, probability, equipment,
population, normal-damage, critical-damage, and HP bounds. Unknown HP, multiple
attackers, deterministic programs, specials, weapons, or inadequate reserves
remain blocked. Its migration recognizes only run 12868's exact three-check,
no-loss, healer-safe result, archives the superseded result, and preserves the
existing **-385 XP** protection marker.

Runs **12869-12871** handled nutrition before combat: two source-backed mushroom
acquisitions bracketed one absent placement. Run **12872** then issued zero
`where drunk` commands, traversed the repaired fixed route, found the carrier
absent from reset room 4064, ate the carried mushroom when hungry, and returned
safely. XP remained **333,533**. This validates the route handoff, not potion
acquisition or progression. The revision-255 suite passed **5,354 tests**.

### Revision 256: Safe Carrier Locator (September 9)

The old deep-Moria fallback was no longer source-safe: one branch crosses a
guardian snake in room 4103 and another a Mage in room 4114. Revision 256 instead
applies the shared bounded wanderer locator to level-24 non-invisible recovery,
initially admitting only reset room 4064 and adjacent room 4063. Level-17
characters retain the strict single-reset plan. A one-use migration requires
run 12872's exact no-loss absence and keeps all earlier route and protection
evidence.

Run **12873** first acquired another Haon Dor mushroom because food maintenance
correctly preempted the pending retry. Run **12874** then used `where hobgoblin`
from room 4014. That room was the observation point, not the target location.
The reported labels first led to empty room 4064; a refresh then reported `The
hole` and `End of tunnel`, outside the two-room graph. Kestrel recalled safely
at 334/334 HP, 356/380 movement, and unchanged XP. This proves the locator and
safe return, not acquisition. Full verification passed **5,366 tests**.

### Revision 257: Source Aggression Cutoff And Live Acquisition (September 9)

The only barrier to the deeper bounded locator was Moria snake 4053 in room
4058: aggressive, sentinel, `spec_poison`, and fuzzed from source level 10 to a
live range of **8-12**. `update.c` suppresses ordinary aggression only when the
player is strictly more than ten levels above the mobile. `special.c` makes
`spec_poison` select only someone already fighting that snake. Therefore level
22 remains blocked at the equality boundary, while level 23+ cannot have combat
initiated by this mobile.

Revision 257 applies that cutoff only to aggressive combat-only specials.
Pre-combat, economic, scripted, equipped, unknown, already-engaged, and endpoint
hazards remain unchanged. Kestrel's level-24 visible circuit maps eight source
rooms within the existing 24-step cap. The one-use migration requires run
12874's exact locator outcome, retains its two failed attempts and protection
history, and consumes the changed-condition retry before connection.

Run **12875** live-validated the correction in **92.34 seconds** and 80 commands.
Kestrel walked through room 4058 while the snake was visibly present and was not
attacked. The bounded sweep found exact carrier **4055** in room **4072**.
`consider #23913` classified it below band, but the required-loot rule correctly
allowed the resource kill; Kestrel opened with `backstab`, used disarm and knife
toss, and gained **110 XP**. He looted purple potion **4050**, stored it in his
pouch, ate the severed leg, sacrificed the corpse, recalled, and finished at
healer 3054 with 334/334 HP, 289/283 mana, and 347/380 movement. There was no
death, loss, crowd, route hazard, timeout, or abort.

Checkpoint **39701** is Kestrel level 24 at **333,643 XP** with the sanctuary
reserve. Runs **12864-12875** total only **+110 XP over 931.60 connected
seconds**, plus one 180-second reset wait, about **7.1 connected XP/minute**.
This is resource-route acceptance, not a throughput improvement, level gain, or
HERO proof. Full verification passes **5,381 tests in 358.23 seconds** and
compilation passes. Next require the reserve-to-useful-kill handoff and repeated
positive whole-journey XP at the actual level-24 frontier.

### Interrupted Fame Attempt And Connection-Gap Accounting (September 9)

Run **12876** acquired a replacement mushroom in **55.95 seconds**, without
changing XP. Run **12877** then selected the registered Circus fame policy.
The exact clerk considered in the required fame-awarding band; Kestrel quaffed
the sanctuary reserve and opened with backstab, which missed. Only one combat
round is captured before the worker ended: player **316/334 HP**, clerk level
**31**, **1,025/1,033 HP**. This is insufficient evidence to judge the existing
timed damage probe, and it proves neither a kill nor a death.

Public recovery **12878** reconnected at recall with **333,258 XP**, already
**385 below** the interrupted checkpoint. It moved north and safely logged out
at healer 3054 with full HP. The pouch was empty. The loss occurred in the
unobserved interval; its command-level cause is not recorded. Runs 12875-12878
therefore net **-275 XP**, not progression or a successful fame handoff.
Source `fight.c:1907` attempts recall for disconnected combatants, and
`act_move.c:2606` charges XP for a successful combat recall. This is consistent
with the observed reconnect location and loss, but is not a captured command.

Checkpoint **39707** preserved the lower XP but exposed an accounting defect:
`campaign_xp_loss_total` remained **1,640** because no connected penalty event
had been captured. The shared segment merge now uses a valid, same-level,
GMCP/text XP decrease as a loss floor, taking the maximum with explicit losses
instead of adding the two. History repair compares each saved segment's own
endpoints and starting counter, so duplicate/overlapping replays do not charge
the loss again. The read-only replay raises this checkpoint's loss floor to
**2,025** and changes no other key. Invalid or untrusted progress, different
characters, and level changes cannot supply this inference. No retry, route,
combat-admission, or loss-history exclusion is reopened by this repair.

Verification: **22 new reconnect-accounting cases**, **24 focused cases**
including existing counter regressions, and **5,403 full-suite tests in 321.49
seconds** pass. Compilation and conversation-header validation pass.

### Invisible Carrier Dispatch Handoff (September 9)

Aeloria's initial public continuation stopped before connecting on existing
current-band cooldowns. A second invocation used one explicit **180-second
reset wait**. Run **12879** then selected the reserve policy, checked the
carrier's fixed reset room, and returned with **no potion and no XP** after
**76.69 connected seconds**, 54 commands. Checkpoint **39717** remains level 18,
161,091 XP, 218/218 HP, 628/628 mana at healer 3054.

The shared locator already source-audits a level-18 invisible corridor, and
the recovery execution already uses it. The deep-reserve fallback, however,
called that same helper only at level 24+. It therefore silently skipped the
existing capability despite Aeloria's positively observed `invis` proficiency
of 42. Dispatch now also admits that helper at level 16+ when class capability
registration and positive practice authorize invisibility. The runner still
requires the fresh affect; the locator retains its 12-room, 24-move, one-refresh
limits, exact carrier identity, pre-entry checks, and source hazard exclusions.
Unqualified lower-level characters retain the strict reset-room fallback.

The existing two-potion requirement and no-consumption rule are unchanged.
No historical failure is cleared and no changed-condition retry is invented.
Fresh live acceptance of this dispatch path remains pending.

The dispatcher passed **91 focused tests**. A full run exposed one existing
assertion that treated the new locator-only stop as a loot stop. Its correction
separately verifies the locator and the unchanged two-potion requirement at all
combat stops. The subsequent clean full run passed **5,409 tests in 395.17
seconds**. One acceptance launcher was stopped during its disconnected reset
wait while that assertion was investigated; no live character was interrupted.

Run **12880** then live-validated the dispatch: `where hobgoblin` reported two
carriers in `The large cave`, and the bounded invisible route found exact
instances **#23896** and **#23920** together. Both appeared in the arrival and
explicit `look` responses. The bot nevertheless refreshed the locator and
returned without consideration, loot, or XP. It spent **79.61 connected seconds**
and 74 commands. Checkpoint **39727** remains 161,091 XP, full HP and mana at
healer 3054, with the original single purple potion retained. This proves
navigation to the carriers, not acquisition or sustained progression.

### Duplicate Required-Loot Targets (September 9)

Run 12880's saved abort says `field room contained 0 observed mobiles while
evaluating 'large hobgoblin'`. This is not a parser failure: the source-below-band
filter removes the two carriers from the material-bystander count, while their
matching-target count remains two. The shared consider probe then skips them
because source data already proves they cannot assist. The unchanged single-
target gate therefore rejects the pair without assessing either instance.

The probe now retains duplicate matching targets even when source-non-assisting.
It still requires exact distinct selectors, globally unambiguous source room
descriptions, safe ordinary mobiles, no active combat or familiar, and the
existing three-probe limit. One below-band response excludes that instance as
an assistant, then the chosen target gets its own fresh consider. This adds no
multi-opponent combat permission and cannot authorize below-band XP kills.

Fifteen focused cases cover mage/thief/warrior, identity and hazard failures,
probe limits, ordinary XP rejection, and the actual recorded two-carrier room
text. That replay uses a fixture-room alias and a synthetic consider reply;
no live consider or kill is claimed. Next live acceptance must acquire and
verify the second potion, then obtain useful XP without clearing past losses.

Final verification passes **5,424 tests in 427.19 seconds**, including the
15 duplicate-carrier cases. Compilation, whitespace checks, and conversation
header validation pass. No gameplay worker remains; the separate Discord
streamer is left running. All changes remain local. The master goal is active
and HERO remains unproved.

### Live Duplicate-Carrier Acceptance (September 9)

Run **12881** is the first live acceptance after the duplicate-target fix. The
level-18 mage reached Moria invisibly, queried `where hobgoblin`, and received
two large-hobgoblin instances in `The large cave`. The controller issued exact
instance consideration rather than treating the pair as an unresolvable crowd,
selected the source carrier **4055**, killed it for **90 XP**, ate the severed
head, and returned safely to healer 3054. The segment took **153.71 seconds**
and 94 commands; final state was 218/218 HP, 628/628 mana, and 258/320 move.
The second purple reserve was not lost: the run still shows one purple potion
in Aeloria's pouch after this required-loot segment.

Run **12882** immediately exercised the ordinary current-band continuation at
the same level. The White Stag route reached room 10016, found no exact target
after its bounded locator check, recalled, recovered at healer 3054, and ended
with unchanged **161,181 XP** and no loss. It took **75.03 seconds** and 83
commands. Runs 12880-12882 therefore prove the repaired search and one useful
kill, but not a level gain, second-potion acquisition, or sustained positive
XP/minute across repeated journeys.

### Dynamic Fame Damage Preflight (September 10)

Run **12899** exercised the newly admitted source-ranked fame fallback after
the route-greeter audit. The source selector chose mobile **20510**, the
Dwarven musician, at Kestrel level 24. Live `consider` correctly accepted its
level band, and the route reached room 20515. The damage-window probe then
measured **84 outgoing versus 101 incoming damage** and projected about **40
actions** for the observed **1,187-HP** target, above the audited 12-action
budget. Kestrel recalled safely; the segment recorded a **301-XP loss** and no
objective kill. This is a failed combat experiment, not progression.

The existing source-backed player-output estimator is now an admission gate
for high-health fame candidates. It accounts for the character's practiced
repeatable action, bounded opener, target HP ceiling, resource reserve, and
incoming damage; sanctuary uses the protected source incoming bound. Route
program preflight remains independently bounded, so a safe transit greeter
does not imply a killable endpoint. The same live candidate now fails offline
selection, preventing a repeat loss. Read-only verification confirms Kestrel
at checkpoint **39782**, level 24, **332,847 XP**, fame -12, healer 3054, with
no purple reserve and an active protection-recovery marker.

The focused fame/output regressions pass, the full campaign suite passes
**1,374 tests**, and compilation passes. The next evidence requirement is a
sanctuary recovery or verified combat-output improvement followed by a fresh
positive whole-journey result. No sustained progression, level 25, subclass,
or HERO proof is claimed.

### Durable Damage-Gate Handoff (September 10)

Runs **12948-12951** separated three safe non-progress outcomes from a policy
deadlock. Run 12948 found a level-24 Solace secretary whose source HP ceiling
was 660, above Kestrel's 318-point knife-toss budget. That rejection correctly
avoided combat, but its transient abort text disappeared after run 12949's
successful food reserve. Run 12950 then found Mr. Smithy with a live poisonous
insect beside it and withdrew before combat.

The campaign now records a source damage-gate marker with reboot, level, source
revision, weapon, policy, and reason. It carries across recovery and food
segments, is invalidated by a reboot, level, source, or weapon change, and is
consumed by the next Forest upgrade attempt. Startup repair also reconstructs
the newest unconsumed marker from the bounded segment history, so an interposed
maintenance segment cannot hide it or cause an immediate retry loop.

Run **12951** live-validated the repaired selection: the Forest bear-claw
route was selected once, reached room 18027, and withdrew when another live
mobile accompanied the required-loot route. Kestrel recalled and slept at
healer 3054; checkpoint **39914** remains level 24 at **332,552 XP**, with no
death or XP loss. The full suite passes **5,460 tests**. This is selection and
one-shot hazard handling proof, not bear-claw acquisition, positive XP/minute,
level 25, or HERO proof. The next delivery gate is still a productive
current-band kill and repeated positive whole-journey XP.

### GMCP Alignment Source Contract (September 10)

The additional source audit confirms that the alignment value is not being
corrupted by the Telnet or JSON layers. In `update.c:4079-4086`, DD4 sends
`d->character->alignment` through `Char.Worth` at level 10 and above, and sends
the deliberate value **50000** below level 10. `protocol.c:3307` maps that
field to `alignment`; the parser retains the value exactly in the progress
event and raw transcript. A live level-24 Kestrel packet recorded alignment
**1000**, matching the source contract.

The consumer rule is now level-aware. Player alignment is clamped to
**-1000..1000** in `fight.c:3518`, while `special.c:spec_guard` uses
`max_evil = 300` and assists only a character below that strict threshold.
Route admission therefore requires known level **10 or higher** and a numeric
alignment in **300..1000**. A hidden sentinel, an unknown level, an out-of-range
value, or a pre-reveal value cannot waive the source guard check. This updates
the older historical note that did not yet apply the level gate; it does not
rewrite any raw packet or historical run.

The focused parser, state, and city-departure checks pass **90 tests**, and the
full suite passes **5,468 tests**. Runs 12952-12953 and startup attempt 1306
added no new gameplay loss; the current checkpoint remains level 24 at
**332,552 XP** in healer room 3054. HERO and sustained progression remain
unproved.

### Source Equipment Placement Report (September 10)

The source equipment audit now treats `MobReset.equipment` as loot provenance
alongside ordinary carried-object resets. Hunt candidates and campaign stops
therefore retain equipped weapons and armour instead of silently dropping them
from required-loot evidence. A regression covers both the parsed candidate and
the source-ranked campaign stop path.

`rank_gear_sources` and `show-gear-sources` provide a reusable acquisition view
for a requested class, optional subclass, level, and loadout stance. Each row
preserves the object VNUM, reset kind, source mobile or ground room, source
level range, exact source keywords, route origin, route, hazard text, autonomy
rejections, weapon role, and whether the role-aware stance score improves the
stored loadout. Thief reports automatically mark piercing wieldables as
preferred, matching the campaign planner's backstab requirement; a stronger
non-piercing weapon is retained as a visible mismatch rather than a usable
upgrade.
`source-only` rows keep future or otherwise unranked placements visible. The
report is evidence for gear planning, not a combat authorization or
live-availability claim; class-slot
coverage and live acquisition remain open master-goal work.

The focused equipment, hunt-candidate, campaign, and CLI checks pass, and the
full offline suite passes **5,471 tests**. No live connection was launched for
this report because Kestrel's current damage and
crowd gates are unchanged. The next acceptance gate remains a productive
current-band journey with positive whole-session XP.

### Bounded Startup Skill Backfill (September 10)

The first frontier rerun exposed a startup cost rather than a gameplay
failure: Kestrel's shared 25.9 GB database spent more than a minute in the
legacy training-event repair before policy selection. The latest checkpoint
already contains an observed practice listing for level 24 and the current
reboot. The repair now treats that live audit as authoritative and skips the
historical scan; only checkpoints without a matching audit replay training
events. A regression test covers the skip and preserves the legacy merge path.

The public rerun reached all preparation boundaries in seconds, selected the
same unavailable source-ranked frontier, and exited cleanly without opening a
connection. This is startup reliability evidence only; Kestrel remains level
24 at **332,552 XP** in healer room 3054, and HERO plus sustained progression
remain unproved.

### Funding Completion Ledger And Retry Liveness (September 10)

Run **12959** exercised the next Kestrel funding continuation after the startup
repair. The exact source-ranked Midget at Circus room **4411** was below the
useful XP band, so its kill was not objective progression, but it completed the
explicit provision-funding action. The live state recorded **40 XP**, **50
copper**, the completed kill, and a safe return to healer room **3054**. There
was no death, loss, or invented target result.

The first resume checkpoint retained an empty `objective_kills` list and a
false funding marker because the two ledgers were being read interchangeably.
The repair now reads the exact segment's durable `completed_kills` event and
created checkpoint **39933** with `completed_kill: true`. Funding actions also
advance their retry cooldown when their XP delta is zero, while an observed
below-quote balance remains eligible for safe funding even during a retry
cooldown. These changes prevent a stale marker or an unaffordable quote from
stalling the campaign without promoting low-value XP into progression proof.

The focused ledger regressions pass **64 tests** and the full offline suite now
passes **5,475 tests**; compilation and log validation pass. Kestrel remains
level **24** at **332,592 XP**, with **157** carried copper-equivalent, a
**131-copper** flight quote, and two funding cooldown steps. The next acceptance
gate is a productive current-band journey and repeated positive whole-session
XP. HERO remains unproved.

### Current-Band Rotation And Bounded Liveness Recovery (September 10)

Runs **12960-12962** completed the immediate maintenance sequence: the
recovered Midget purse was cleared, its loot was sold, and Kestrel reached
**2,878 copper-equivalent**. The watchman research probe produced a fresh
viable result for the level-24 frontier. Runs **12963-12965** then used the
official Moria route and returned safely to healer 3054 without acquiring
sanctuary or adding XP. Run 12965 completed before the liveness stop; it was
not interrupted.

Reconnect run **12966** emitted no fresh transcript event across its bounded
liveness window. The exact gameplay worker tree was stopped after the single
allowed reconnect, without touching the Discord streamer or unrelated Python
processes. Startup recovery marked the run failed with interruption evidence,
left segment 12515 ready, and converged through checkpoints **39960-39961**.
There was no death, XP loss, or fabricated kill result. Kestrel is currently
level **24** at **332,592 XP**, alive in healer room 3054. The next gate is a
productive current-band kill and repeated positive whole-session XP; the HERO
claim remains unproved.

The focused ledger regressions pass **64 tests**, the full offline suite passes
**5,475 tests**, compilation passes, and the conversation log remains valid.

### Moria Carrier Locator Expansion (September 10)

The first corrected Moria retry exposed a bounded-plan omission rather than a
source safety failure. Mobile 4055 can reach 15 source rooms, and the live
`where hobgoblin` response named `the large cave`; the eight-endpoint fallback
did not inspect every safe room with that label. The shared locator already
admitted room 4068 within its 24-step safety budget, so the required-loot
campaign handoff now requests nine non-invisibility endpoints. All existing
source hazard, exact-target, below-band, and healer-return gates remain in
force.

Runs **12967-12970** recorded the bounded reconnect and food-reserve
maintenance needed before another protected field trip. Run **12971** then
used the new plan live: Kestrel considered and killed source carrier 4055 in
Moria's large cave, gained the source-consistent **100 XP**, looted object 4050
(`purple potion`), placed it in the combat pouch, sacrificed the corpse, and
returned to healer room 3054. The run ended at checkpoint **39975**, level 24
with **332,692 XP**, no new loss, and one verified purple reserve. This is
required-loot recovery evidence, not sustained progression; the existing
protection marker still requires a protected productive hunt.

The focused locator and campaign checks pass, and the generated fallback uses
22 of 24 movement steps while including room 4068. The next live gate is the
protected current-band hunt, followed by repeated positive whole-session XP;
HERO remains unproved.

### Durable Resource Ledgers And Level-24 Rotation (September 10)

The first post-Moria resume exposed a state-reconciliation defect. A raw live
character snapshot correctly supplies current room, inventory, vitals, and
affects, but it does not carry campaign-owned combat-pouch counts or verified
source-resource contracts. Because those keys were absent from the startup
sticky-metadata allowlist, the next segment temporarily forgot the purple
sanctuary reserve and unnecessarily reopened the Moria recovery policy.

The campaign now preserves `combat_pouch_potions`,
`verified_combat_pouch_potions`, and `campaign_source_resource_reserves` from
the durable checkpoint while still accepting live inventory and resource
consumption outcomes. A regression reproduces the omission and verifies that
live inventory remains authoritative. The full offline suite passes **5,477
tests**.

Runs **12972-12978** completed bounded food and target maintenance. Run
**12979** began with both purple ledgers intact and selected the ordinary
Solace frontier, proving the startup fix against the live campaign database.
Run **12981** replenished food at Haon. Runs **12980** and **12982** reached
Ultima and Mahntor targets; each returned safely without a kill because source
HP ceilings exceeded Kestrel's measured knife damage budget. The latest
checkpoint is **40014**, level 24 at **332,692 XP**, alive in healer room 3054
with one purple reserve and no new loss. The
protection-recovery marker remains open, so the next gate is still a protected
productive current-band journey and repeated positive whole-session XP.

### Forest Retry And Crowd Evidence (September 10)

The fresh source combat-budget marker now reopens a previously cleared Forest
bear-claw upgrade only when the current level, reboot, source revision, weapon,
and damage-gate reason still match. This restores a valid retry without erasing
the prior crowd quarantine or permitting a bypass of target, consider, route,
or healer-return checks. A regression covers the policy-selection boundary.

Run **12984** selected that repaired Forest policy and reached the source-mapped
River bed approach. The exact `where kodiak` result placed the Giant Kodiak bear
in room **18026**; room **18027** then exposed source-registered mosquito and
wasp instances alongside the route. The required-loot crowd gate withdrew
before combat, recalled, recovered at healer **3054**, and quit cleanly. There
was no death, loss, kill, or XP change. Kestrel's latest checkpoint is **40031**
at level **24** and **332,692 XP**, with one purple reserve; the upgrade cooldown
is six bounded segments. The full offline suite passes **5,477 tests**, and
compilation is clean. This is concrete route-safety evidence, not sustained
progression; the next acceptance gate remains a protected productive
current-band journey with positive whole-session XP.
