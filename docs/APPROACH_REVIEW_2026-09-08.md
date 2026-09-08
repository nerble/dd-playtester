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
| Fresh mage, Astrevo | 12789-12790 | 0 XP; three exact-instance considers; 61.16 connected seconds plus 180-second wait | 39254: level 8, 28,273 XP |
| Mage, Aeloria | 12759-12761 | +281 kill followed by -3,768 death loss; net -3,487 XP | 39130: level 18, 158,168 XP |
| Warrior, Dorrik | 12766-12768 | +100 incidental XP, then -339 failed-hunt XP; net -239 | 39160: level 25, 379,837 XP |

Dorrik's comparison consumed 286.28 connected seconds plus a 180-second reset
wait. All three characters ended safely at healer 3054. Safe logout is a
reliability result, not an XP result. No improved throughput is established.

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
are offline results. A bounded public acceptance invocation is now testing the
change; no live pair kill or XP-throughput improvement is claimed yet.
