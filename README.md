# dd-playtester

An experimental autonomous Dragons Domain IV playtester using asyncio Telnet,
GMCP, source-backed deterministic policies, and durable run evidence.

## Current Status: October 2

Dorrik remains the sole progression character. Checkpoint **48437** records
level **29**, **576,805 XP**, and **37,095 XP** to level 30, with **666/666 HP**
at healer room **3054**. Level 30 also requires his first quest point. HERO is
unproved; keep progression focused on this character.

Runs **15903-15908** earned **3,609 net XP**, including a **381 XP net loss**
on the Secretary hunt, **1,606 XP** from Sosivia, and **2,384 XP** from the
dwarven circuit. The whole six-run interval took **13.77 minutes**, about
**262 net XP/minute**, including quest, flight purchase, and a city-route
deferral. An unavailable quest cooldown now returns to current-band hunt
selection instead of repeating a no-progress wait.

Through run **15938**, the evening continuation gained **10,334 net XP**. Trainer travel
now works live: the inventory parser no longer mistakes DD4's carrying-total
footer for an item. Run **15920** consumed the purchased invisibility potion,
reached the teacher, gained enhanced damage **66->67%**, defense knowledge
**62->63%**, and parry **57->62%**, then recovered at the healer. The following
sailor hunt gained **1,321 XP**. The first completed quest remains a level-30
blocker.

The latest seven runs (**15932-15938**) gained **1,218 net XP** in **13.91 elapsed
minutes**, including food, sales, an absent-target trip, an abandoned quest, and
gear acquisition. Dorrik now wields the source-selected grey branch **6104**;
its combat benefit is not yet measured. The failed-stun timing repair removes
an extra wait after DD4's exact already-fighting `kill` refusal. It compiles,
but that reply has not yet occurred in a new live fight. Normal action and
survival limits remain unchanged.

Quest requests remain automatic. DD4 labels both buried hoards and loose quest
objects as `retrieve` in GMCP. The bot now binds the exact questmaster narrative
to the requested quest's giver, room, and object, preserving raw wire data.
Known hoards are explicitly deferred until trap-aware acquisition is implemented;
the old blind twelve-dig sequence has been removed. Ordinary retrieval and kill
quests retain their existing route and combat checks. These new cases compile
but remain unrun under today's one-regression-batch limit; hoard recognition
is not yet live-proved.

Source parsing now recognizes DD4's actual area-section headers instead of
mistaking hash-prefixed ASCII maps for headers. This restores **492 Underdark
rooms** and their route hazards. A route appearing in the corrected map does
not authorize travel or combat; the normal source and live checks still apply.

Continue the existing character through the normal bounded autonomous command:

```powershell
python -m dd4tester hero --name Dorrik --autonomous --segments 3 --max-reset-waits 0 --max-segment-runtime 300 --progress
```

The segment count bounds this invocation; rerunning resumes its saved checkpoint.
The default segment allowance is now 300 seconds, including preparation and
travel. An explicit `--max-segment-runtime` overrides it; combat-action limits
and bounded return/cleanup still apply. The old 180-second default caused a
forced combat withdrawal in run 15929 only 16 seconds after its opener.
See the [approach review](docs/APPROACH_REVIEW_2026-09-08.md) for dated evidence.

## Discord Conversation Relay

The separate streamer in `E:\dd4-discord-streamer` tails
`DEVELOPMENT_CONVERSATION.txt`; it cannot read the Codex chat directly. At the
start of each assistant turn, record the newest user message as `USER` before
commentary or tool work. Record each outgoing commentary/final before showing
it. Use `--body-stdin` with a PowerShell here-string so punctuation is passed
without shell reinterpretation:

```powershell
$body = @'
Exact message text
'@
$body | python tools/conversation_log.py append --speaker USER --body-stdin
```

Use `CODEX COMMENTARY` or `CODEX FINAL` for assistant messages. The standing
capture rule is in `AGENTS.md`. Verify the file with
`python tools/conversation_log.py validate`, then check the streamer's delivery
log for `Delivered USER` and an empty queue at the source-file end. Keep the
worker in `--new-only` mode; do not rewind history or start a duplicate. On
October 1, a user message was missing because it had not been appended to the
source file. Adding the exact `USER` record made the existing worker deliver it;
the relay itself was healthy, so it was not restarted and history was not
replayed. The stdin-based logger decodes the pipe as UTF-8, independent of the
Windows Python console encoding; historical records are not rewritten.

## Historical: September 29 Transport Follow-up

Aeloria's one permitted post-reset sanctuary check (run **15536**, checkpoint
**47468**) reached a silent login socket. It issued no game commands and earned
no XP, so it did not provide route evidence. The check now remains pending for
a later explicit invocation; the current run stops without waiting for another
area reset or retrying automatically. This change has a focused test saved but
unrun: September 29's single test batch was already used. Only a syntax check
has verified this edit; live retry behavior remains unproved.
The all-area level-18 scan currently returns no autonomous-safe XP stop for
Aeloria; the visible source candidates still have route, crowd, protection, or
combat-output blockers, so none is being promoted from analysis to permission.

Run **15326** also exposed a route-index mismatch: the safe Midgaard detour
lengthened Dorrik's path, but the saved Shadow Grove maze markers still pointed
to their original positions. The detour now shifts both later markers by the
exact command-count change. The matching same-boot, pre-combat failure can now
receive one exact revalidation when the current source path proves the room and
maze destination; the marker is spent before dispatch and does not bypass live
gates. Focused tests are saved but today's regression batch has already run, so
this change is syntax-checked only and still needs its next permitted test batch
and a fresh live route to prove it.

## Historical: September 29 Progress

Dorrik is level **26**, **450,253 XP**, with **3,347 XP** to level 27.
Checkpoint **47413** confirms **594/594 HP** at healer **3054**. Secretary
**15505** earned **1,113 XP**; **15506** withdrew from the same target at a
cost of **455 XP**, leaving **658 net XP**. His next quest departure was
blocked, and the bounded time probe confirmed the same reboot; work rotated
to another character instead of repeating failed routes.
Fenanallor is level **8**, **29,054 XP**, **2,646 XP** to level 9, fully healed
at **3054** (**47400**). Orc and illusionist kills earned **331 XP** across
three hunts; a strongman withdrawal lost **42 net XP**, leaving **289 net XP**.
Ararisa is level **11**, **49,524 XP**, fully recovered at healer **3054**
(**47429**), after **191 net XP** from Moria **15519**. Trips **15520** and
**15525-15526** added none; the latter found an orc and hobgoblin but both live
considers rejected them as below-band.
Kestrel replenished food in **15501**, then had a city-blocked hunt; he remains
level **24**, **329,125 XP**, at the healer (**47348**).
These totals include losses; safe returns and successful command status alone
are not counted as progression. No character levelled, and HERO remains unproved.
Across **15519-15526**, **191 net XP** in **716.00 connected seconds** is
**16.0 net XP/minute**. Across **15478-15526**, including unsuccessful hunts,
city waits, provisions, shopping, sales, and recovery, **6,134 net XP** in
**4,660.48 connected seconds** is **79.0 net XP/minute**. These are connected-time
rates, not whole-session rates: the latest block also spent **180 seconds**
waiting offline for an area reset, plus planning and startup time. Training
**15517** and funding **15518** added no XP; the latter returned when the Circus
approach remained blocked. All workers finished; the final process check found
no project Python worker still running.

`hero --autonomous` can now select one source-audited vendor purchase to prepare
blocked level-20-to-29 training. It checks the actual shop price, item level and
TARGETMODE selector, keeps 100 copper, buys once, and verifies inventory growth.
Dorrik **15522** purchased invisibility elixir **9231** from vendor **9238** in
room **9203** for **188 copper**, returning with **645 copper** and full healer
HP. The preceding quote **15521** exposed an overly small spending cap; its
one-time correction is consumed. Inspect the sequence with
`python -m dd4tester show-transcript 15522`; the checkpoint also stores
`campaign_source_purchases` and `campaign_training_travel_supply`.
Potion acquisition is live-proved. Potion-assisted advanced training is now
implemented as one separate noncombat visit per level/reboot, but **not yet
live-proved**. Ordinary `hero --autonomous` selects it after checking useful
lessons, the purchased item, and movement. It verifies consumption, live
invisibility and every route step, then uses the usual training and healer
return. Inspect `campaign_consumable_training_travel` for admission and
`campaign_training_travel_result` for the actual outcome. This does not open
ordinary equipped-hazard routes. Saved checks are unrun under the daily limit.

Attempts **15523/15524** stopped at the healer before consuming the potion.
The first lacked targeting setup; the second exposed delayed replies and
zero-ID objects loaded from character saves. The implementation now confirms
configuration and request-local replies, and allows one exact source-unique
keyword when no numeric item selector exists. That fix is not yet live-proved;
the spent journey is not reopened this reboot. Ararisa's next selection lacked
funding, and Kestrel's lacked protection supplies; neither connected. This
implementation batch earned **zero XP**, and no regression batch ran.

Funding no longer blocks the next registered activity merely because an unused
ground-hunt allowance remains when that search finds no target. Its ground
handoff also preserves the hunt selector's existing bounded capacity admission.
Normal `hero --autonomous` uses both changes automatically; live identity,
crowd, consider, and combat checks remain mandatory. New checks are saved but
unrun under the one-batch-per-day limit.
Runs **15525-15526** proved this handoff reaches live hunts and keeps the
below-band rejection intact, not improved XP. Both finished at the healer,
earning **zero XP** in **189.67 connected seconds**. Rotate the next work away
from these two unchanged targets. No additional regression batch ran.

Normal `hero` hunts can now identify an unambiguous primary weapon at the
Midgaard healer when the character has positively practiced `identify` and
enough mana. The bot confirms removal, reads actual damage, re-equips, and checks
the weapon slot. Each reply is bounded; failed rearming stops departure.
The result is connection-local and saved as `campaign_weapon_damage_audit`.
It informs live encounter budgets, while pre-login planning uses conservative
load-level damage. Prototype numbers are no longer used as ordinary live damage.

Runs **15478-15479** completed this automatically: Ararisa's dagger **3-8**,
Fenanallor's **5-9**. Their subsequent hunts earned no XP because the target was
below-band or the route was blocked. Inspect the actual sequence with:

```powershell
python -m dd4tester show-transcript 15478
python -m dd4tester hero --name Dorrik --autonomous --segments 1 --max-reset-waits 0 --max-segment-runtime 180 --progress
```

The September 29 focused batch passed **38 tests in 2.22 seconds**. No full suite
was run; the daily allowance is spent. HERO remains unproved.

The one-batch-per-Auckland-day limit is permanent in `AGENTS.md`; most work
belongs to implementation and actual progression. Route-hazard retries now
finish healer recovery before departing and discard the completed emergency
return, preventing an immediate trip back without a fresh check. Combat, loss,
and logout boundaries still cancel retries. Saved checks for this repair have
not run; its exact live sequence remains unproved.

Ordinary single-target hunts now plan when to put on levelling gear from the
source reward and possible damage XP, rather than always sacrificing combat
bonuses for the last ten percent of a level. Complex or unknown fights retain
the original rule; recovery gear and stat training are unchanged. The terminal
run record includes `pre_level_gear_windows` for inspection; **15504** recorded
**4,374 XP** for its target. This records live use, not proof of improved gear
timing or XP throughput. Its saved checks remain unrun.

A local training trip blocked before any lesson can now reopen once after a
later productive hunt reports the wandering obstruction away from the entire
teacher route, or after a later automatic world check confirms the same reboot
at least five minutes after the blocked visit. Both share one retry allowance.
The bot still rechecks before leaving and requires useful,
affordable lessons at the same teacher. This runs through ordinary `hero
--autonomous`; it does not clear combat failures. Its saved checks remain unrun.
Run **15517** proved the timed retry and bounded history lookup reached a fresh
trainer-route check. The drunk was still on Main Street, so Dorrik returned
without a lesson; the retry stayed consumed and combat-loss records remained.
That local fallback did not produce a lesson. The later consumable-assisted
teacher visit succeeded in run **15920**, as recorded above; improved sustained
combat throughput remains unproved.

Ordinary multi-spawn wandering hunts can now refresh `where` after a useful
kill instead of returning solely because the first mapped stop is complete.
The original kill and search limits remain; every next target needs fresh
identity, isolation, and consider checks. Resource routes and protected probes
are excluded. This is automatic in `hero --autonomous`, with no new option.
Inspect `campaign_fastwalk_where_decisions` for `after_objective_kills` on an
executed continuation. The change is implemented; its focused checks are saved
but unrun, and a live multi-kill improvement is not yet proved.
Moria **15515** retained an earlier poisonous-bystander warning and therefore
did not use the new continuation. Circus **15516** ended at the healer after
its route remained blocked; it earned no XP.

Run **15482** exposed a navigation error: an optional Mirror Guardian encounter
at room **19031** was rejected as crowded, then discarded the original,
unvisited destination **19041**. The handoff now restores that earlier stop and
finishes the approved outbound route, without permitting the armed pair or
clearing an abort. Run **15490** demonstrated that continuation live, but the
legacy directions then looped inside the shuffled mirror maze. Guardian campaign
routes now preserve the approach to **19031** and use the existing source-backed
live-exit navigator to reach **19041**. That maze repair and its new checks remain
unverified; navigation success alone will not prove a useful kill.

Pouch checks now preserve an unfinished preceding prompt across the command
boundary. This addresses **15487**, where a real empty listing was incorrectly
treated as unanswered. Only the partial prompt is retained, never old inventory
text; the complete-listing requirement and five-second timeout remain. New
checks are saved but unrun under the daily regression limit.
Absence recording now also requires an observed room and, for a destination-
guided stop, arrival at that endpoint. Wrong-room navigation failures cannot
consume its search. Existing historical loss and absence records were preserved.

## September 28 Progress

Dorrik is level **26**, at **444,599 XP**, **9,001 XP** short of level 27
(checkpoint **47256**, healer **3054**). Run **15457** successfully used the
city detour but lost **342 net XP** after withdrawing from the Weeping Willow.
That fight remains closed; a successful route is not a successful hunt.

Local fallback training now permits up to three accepted useful lessons per
visit instead of leaving solely because one practice type was already used.
Additional lessons need fresh live eligibility and a positive source-teacher
gain; listed unlearned skills are included. Legacy single-lesson visits get
one narrowly scoped retry. Saved checks await the next permitted test batch;
run **15461** selected this repair but stopped at a city hazard without spending
practices. Live training improvement is not yet proved. HERO remains unproved.

Pouch checks now retain split replies through the complete contents listing,
including departure and healer logout. An unanswered check ends after five
seconds and returns to healer logout without erasing the previous verified
contents or authorizing a hunt. Confirmed empty listings still clear the ledger.
The shared fix and new replay cases await the next permitted regression batch;
the earlier repacking-only fix was observed working in run **15386**.
Run **15414** confirmed the shared check accepts a real empty-pouch response.
It then returned to the healer because of a wandering route hazard; food
restocking run **15415** also completed. Neither run earned XP.

Development prioritizes useful implementation and live progression. Regression
tests run **at most once per Pacific/Auckland calendar day**, using either
focused tests or the full suite, never both. This is a ceiling, not a daily quota.

Fenanallor earned **200 target/net XP** in **15472**, reaching **28,765 XP** at
level **8**, **2,935 XP** from level 9 (checkpoint **47296**). The following
ring-recovery attempt earned no XP and obtained no rings. Together the two
segments used **219.90 connected seconds**; both ended at healer **3054**.

Weapon upgrade ranking now uses conservative DD4 load-level damage estimates,
not the incorrect assumption that area-file values are damage dice. Live
identification in **15475** confirmed Ararisa's level-5 dagger does **3-8** base
damage, while its prototype contains **2,4**. The September 29 continuation
above adds bounded automatic identification and live encounter-budget use;
it does not widen route, target-identity, health, or action-count gates.

Locator redirects now retain registered safe recovery stops along their exact
route. This fixes a sanctuary search that discarded its movement-recovery
waypoint and returned empty-handed. The live safety checks and segment limits
are unchanged; the new cases are saved but unrun, and successful acquisition
through the repaired redirect remains unproved.
The following roster rotation earned **220 target/net XP** in **15470-15471**;
Ararisa is level **11**, **49,333 XP**, fully recovered at healer **3054**
(checkpoint **47291**). No new regression batch was run.

The autonomous command now tries the existing bounded quest option when flight
funding, ground hunts, and registered alternatives are exhausted. It shares the
usual one-request-per-level/reboot limit. Run **15464** exercised that handoff:
Astrevo reached Suturb, received a retrieval quest, then aborted when the route
needed Circus admission. No reward or XP was earned.
Noncombat Circus quest planning now includes the source-checked ticket purchase
and door unlock, reusing the existing field-action runner. That admission change
and its saved failure cases are not yet live-proved or regression-tested.

Equipment acquisition now compares an upgrade against the weakest selected
slot, accounting for two rings, necklaces, or wrist items and any carried spares.
Inspection commands count each worn item once and preserve inventory quantities.
The current source report now recognizes a second war-dog collar as a combat
upgrade for Kestrel; route and protection gates still control acquisition.
This ranking improvement is source-inspected, not yet live-acquired; its focused
cases are saved for the next permitted regression batch.

The evening roster pass (runs **15416-15422**) earned **661 net XP** from four
confirmed kills: Ararisa +234, Astrevo +106, Serevian +209, and Velnor +112.
No character levelled or recorded an XP loss; all seven live sessions finished
fully healed at room **3054**. Total connected time was **617.76 seconds**,
including preparation, travel, and recovery. Three blocked campaigns did not
connect. See the approach review for the next combat-throughput issue.

Run **15423** exposed a wait after a fleeing target: DD4's `They're not here.`
reply was missing from the ordinary target-check acknowledgement matcher.
That reply now releases the wait through the bounded refresh path. A fresh
source encounter identity also resolves differing room and combat names for
departure tracking. These changes and their saved cases await further proof;
no extra regression batch was run. Runs **15423-15424** earned no net XP.
Ordinary target checks now buffer split replies and expire after five seconds
without an answer. A timeout returns through the existing recovery and healer
logout controls, rather than waiting out the whole hunting segment or recording
false target-level evidence. Silent and split-response cases remain unproved
live; their focused tests are written but deferred.
Ararisa's follow-up runs **15425-15426** also earned none: both targets were
below-band on live consideration. Both characters ended fully recovered at
healer **3054**, without recorded XP loss; that is not advancement evidence.

Run **15429** completed a Circus target kill for **188 XP**, leaving Serevian
at level **11**, **54,376 XP**, with **4,074 XP** to level 12 and full recovery
at healer **3054**. The preceding equipment search earned **145 incidental XP**
but obtained no upgrade; neither that XP nor the empty funding trip counts as
target-progression proof. The ordinary target reply worked live; the new
split-response, silence, and flee-name cases remain deferred and unproved live.

Completed money hunts now prioritize selling new loot while a funding retry is
pending, even if carried coins exceed the provisional flight-price estimate.
Shop-route checks and retained-gear protections remain in place; a completed
kill is not counted as money earned until a sale is observed. This closes the
handoff exposed after run **15431**; focused cases are saved but not yet run.
The flight-purchase preference also leaves a selected sale in place. Live run
**15434** selected liquidation, but three blocked city-route checks prevented
the sale. Serevian is safely saved at checkpoint **47186**, **54,416 XP**,
**4,034 XP** to level 12. No sale income or flight purchase is proved; the
additional **40 XP** from Katrina is funding maintenance, not progression XP.

Closed exits no longer break familiar room confirmation. A listing such as
`[Exits: north east south west [up]]` now preserves the closed marker, and a
pending familiar check cannot fall through to route completion. Run **15436**
exposed that premature return; the fix and its saved cases remain unproved live
and unrun under the daily test cap. Failed-route checkpoints now retain the
matching familiar audit without restoring ownership on reconnect.

Fenanallor's runs **15437-15438** earned **452 target XP** from three kills,
including two in one Circus outing, without recorded loss. He is level **8**,
**28,565 XP**, **3,135 XP** from level 9, saved at healer **3054** (checkpoint
**47203**, after two later city-obstructed departures added no XP). Astrevo's
intervening food and failed familiar trips also earned no XP. Including all six
connections, the block earned about **53.6 target XP per connected minute**.

Familiar-backed hunts now check escape safety during selection using the same
rule as combat, including wandering hazards and the actual encounter room.
Run **15441** exposed a wasted trip when those checks disagreed; it summoned
and grouped the familiar but earned no XP. The repair is saved, with its new
regression cases deferred; useful replacement-hunt progress remains unproved.
The following six connections (**15441-15446**) gained no XP: Aeloria's potion
searches missed moving carriers, and Dorrik's departures were city-obstructed.
Both ended at healer **3054**; latest checkpoints are **47210** (Aeloria) and
**47216** (Dorrik). These completed attempts are not progression proof.

Field locators now wait for the complete location listing before narrowing a
search, and preserve their choices in `campaign_fastwalk_where_decisions`.
An incomplete reply ends the hunt through the bounded return, without recording
false absence. Astrevo's runs **15447-15450** earned **242 target XP**, including
maintenance time, and ended fully recovered at level **9**, **35,712 XP**,
**3,988** to level 10 (checkpoint **47227**). The normal complete-listing path
worked live; split-response and timeout cases remain saved but unrun today.
The subsequent crowded-target trip added no XP; checkpoint **47234** preserves
that total and full recovery. Across the five connections, including maintenance
and the failed trip, the block earned **37.8 net XP per connected minute**.
An additional locator handoff repair allows only an already-approved forward
route suffix from the actual room, and stops repeated queries after navigation
is exhausted. Run **15453** exposed this waste; the repair and saved cases
await live suffix evidence and the next permitted regression batch.
Velnor's existing Circus circuit earned **367 target XP** from two kills in
**15454**. He remains level **7**, **19,845 XP**, **5,005** to level 8, fully
recovered at healer **3054** (checkpoint **47240**); the following flight-shop
trip was blocked and bought no potion. No loss or level gain was recorded.

## September 26 Roster Snapshot

HERO 100 remains unproved. The latest saved roster checkpoints are:

| Character | Level | XP | Checkpoint |
| --- | ---: | ---: | ---: |
| Aeloria | 18 | 162,145 | 45166 |
| Ararisa | 10 | 47,544 | 45168 |
| Astrevo | 9 | 35,282 | 45171 |
| Corararfen | 8 | 26,528 | 45172 |
| Dorrik | 25 | 404,981 | 45174 |
| Fenanallor | 7 | 20,733 | 45177 |
| Kestrel | 24 | 329,349 | 45179 |
| Praelarran | 21 | 233,527 | 45180 |
| Serevian | 11 | 53,834 | 45182 |

The September 26 rotation produced no level gains. Aeloria, Dorrik, Kestrel,
and Serevian remain at exhausted sanctuary rechecks; Ararisa and Astrevo have
no safe funding target; Corararfen has no current executable frontier;
Fenanallor's field departure was blocked by the wandering drunk; and
Praelarran's quest request earned no XP. These are per-character blockers, not
a reason to pause all progression until a MUD reboot.

Morjornelmor's separate level-6 campaign ended at **14,489 XP** (checkpoint
**45189**), only **11 net XP** above its starting point. The Cult room held a
receptionist who joined the fight, so the character fled; there was no
confirmed kill, and **49 XP** was lost against **60 partial XP** earned. The
following recovery and same-boot time check earned no XP, and no safe current-
band route remained. HERO 100 remains unproved.

The one regression batch allowed for September 26 was already used on earlier
work. This cleric-priority change received only JSON and Python syntax checks;
its focused tests are deferred to the next daily batch.

Campaign policy revision **334** now schedules the cleric protection path after
its damage and healing priorities: protective magiks 45%, protection 40%, then
sanctuary 40%, only when the live teacher offers each skill. Existing mana and
buff checks remain in force; the new path has not yet been live-verified.

Historical Ararisa work added **460 net XP**, from **43,842** to
**44,302**: run **14501** (+48), run **14504** (+240), and run **14506**
(+172). Run **14500** earned no XP when the familiar finished the bard; the
stunned-bard hunt was not repeated. Run **14502** exposed an empty-route bug
before combat, and recovery run **14503** returned her safely to healer room
**3054**. The fix passed its focused test and live run **14504**: after `where`
found no fanatic monk in Dragon Cult, Ararisa followed the source-mapped
Midgaard route through rooms **3024, 3025, 3026, 3045, 3046, and 3219**, reached
the guild, killed the monk for **240 XP**, and returned to the healer. Run
**14505** handled loot without XP. At that historical checkpoint, Ararisa was
level 10 at checkpoint **44687**, with **4,198 XP** to level 11. No one levelled
in those runs; the full suite remains deferred while progression work continues.

An earlier bounded roster pass produced confirmed XP without losses: Ararisa gained
**83 XP** in run **14491**, Corararfen gained **223 XP** in Moria in run
**14492**, and Fenanallor gained **256 XP** in run **14493**. All three saved
at healer room **3054**; none levelled. Corararfen's runs **14488-14490** also
confirmed that the wandering drunk can block several Midgaard outbound routes;
those routes were safely abandoned, then the campaign selected Moria and made
progress. Aeloria, Dorrik, Kestrel, and Serevian were deferred before login at
their exhausted protection gates; Praelarran had no executable frontier, and
Astrevo had no safe funding target. No HERO result is proved.

The no-XP familiar handoff now checks the exact live target after the familiar
opens. When a non-crediting familiar has brought it to 65% health or lower, the
bot must confirm the charmed pony's flee-and-sleep handoff before the player's
first attack. `tests/test_companion_withdrawal.py` passes **30 tests**, and the
edited Python files compile. This fix is not yet live-proven; the full suite is
deferred while progression continues.

Earlier Fenanallor runs 14300-14312 earned **1,925 XP**: 1,715 from boar
hunts and 210 from a daycare gear route. The latest two school-boar attempts
found no target at their reset-room anchors. DD4 source marks the boar as a
stay-area wanderer, and the route builder already provides up to eight nearby
source-vetted rooms. The locator now continues that bounded sweep after a
`where` miss; a positive locator still uses the full source map, and live room,
identity, and hazard checks remain required. Three focused tests pass. This
Fenanallor change is not live-proven: the school route is on a same-reboot reset
cooldown.

The full suite remains deferred until a larger implementation batch or release
checkpoint; the bounded roster run is campaign evidence, not a regression run.

## Run the saved roster

Run one bounded turn for each campaign in the active roster:

```powershell
python -m dd4tester hero-rotation --config matrices/active-hero-rotation.yaml --rounds 1 --progress
```

Each turn runs at most one campaign segment, with a 180-second live cap and no
area-reset wait. A completed character is skipped; a blocked or failed
character is reported and deferred for the rest of that invocation, so the
remaining roster still gets a turn. Use `--rounds N` to continue only campaigns
that returned a durable next-segment checkpoint. This does not override any
character's safety gates or claim progress when no XP was earned.

The September 24 live roster pass gave all six then-configured characters one
turn and completed in about a minute. No level or XP changed. Aeloria, Dorrik,
Kestrel, and Serevian stopped at their already-spent sanctuary recheck;
Praelarran was on a protection-recovery cooldown, and Astrevo had no safe
funding target. These are character-specific route and resource limits, not a
global pause until the MUD reboots. The saved rotation now includes nine
unfinished campaigns, adding the existing Ararisa, Corararfen, and Fenanallor
tracks.

Corararfen then resumed his level-6 cleric campaign. Run **14186** completed
the Mud School segment and saved **302 XP** through GMCP, reaching **17,348 XP**
with **1,702 XP** to level 7. He returned to healer room **3054**. This is
productive route evidence, not HERO proof.

### Progress persistence update: September 24, 2026

Fenanallor's first reconnect exposed unsaved progress, so the starter now saves
after first observing progress and after each later XP or level change. Live
runs 14079-14094 confirmed the fix: he resumed at level 4, reached level 5,
and retained his gains across bounded sessions. That batch saved him at
level 5, 12,292 XP, healer room 3054, full health and mana. The latest hunt
added 250 XP in six kills. A reconnect confirmed that an unusual in-session XP
reading had not changed his saved total. He is continuing between MUD reboots;
a reboot can change some kill and spawn bonuses, but is not a prerequisite for
XP. HERO 100 remains unproved.

The preceding full repository suite passed 6,038 tests; the starter and
campaign suites also passed after the save-on-progress change. Compilation and
conversation-log validation are clean. Inspect the current evidence with
`python -m dd4tester show-campaign 27 --limit 12` and
`python -m dd4tester show-state 14094`.

The first-miss location refresh is covered by the full starter suite: **1,483
tests passed**. The related campaign and progression checks passed **4,145
tests** before that small follow-up. Compilation is clean. Praelarran's latest
bounded run also completed its area-reset check without XP; Kestrel's fame
readiness audit found no current target within his damage limits.

## Historical State: September 22, 2026

Dorrik is the current highest live character: level 25, 388,606 XP, checkpoint
42991, safely saved in healer room 3054. Runs 13848-13850 performed the
maintenance-only world-time probe after the bounded reset wait; DD4 still reports
the same reboot, `Fri Sep 4 06:19:51 2026`, so no XP or level changed. The
latest probe opened a short authenticated connection, issued `time`, `save`, and
`quit`, and then closed normally. The source-ranked runner now permits
one bounded last-chance fresh probe when the only remaining candidate has a
25-50% chance of landing in the useful XP band; productive routes and stronger
fresh candidates always win first, and live `consider` remains authoritative.
The September 21 continuation tested that frontier safely: the tree sprite was
absent, the Abyss copepod route withdrew at its movement reserve, and a later
Crystal grain reserve run completed safely without XP. Run 13691 then tested
the source-ranked Highlander funding route, withdrew after an unexpected
critical-hit damage spike, and recorded a 419 XP flee loss; the current-reboot
loss ledger now closes that target. Run 13693 then completed the source-backed
Moria large-orc funding attempt, adding 50 maintenance XP, one ring, and one
sacrificial copper without claiming progression XP. Direct sale run 13694 tried
the Leather Shop and one alternate Armoury buyer; both refused the ring and it
was donated, leaving 4 silver and 8 copper.
Serevian's New Ofcol research route exposed an exact source identity ambiguity;
the source audit proved VNUMs 617 and 618 are equivalent ordinary citizens, and
revision 311 now reopens that result once with the live TARGETMODE alias recorded.
His next bounded segment still has to clear flight funding first. The local DD4
source mirror is now revision `7faf3f9`; the synchronization run found the
same DD4 reboot identity and opened no gameplay socket.
HERO 100 remains unproved.

When a source-ranked frontier is unavailable, the checkpoint retains a
compact offline diagnosis under
`campaign_source_ranked_frontier_diagnosis`. The readiness report is a source
shortlist, not a promise that the campaign will dispatch a fight: it now
separates source-gate fit from useful-XP probability and shows known live
below-band or invisibility blockers. The final selector still applies route,
cooldown, combat, and fresh live-consider checks. Inspect the durable boundary with
`python -m dd4tester show-campaign 7 --limit 12`, then use
`show-combat-readiness --level 25 --class warrior --character Dorrik
--all-areas --json` for the source candidate details. This diagnosis is
observational only and never authorizes a live route.

The September 22 continuation also fixed a live endpoint-combat parsing gap:
DD4 can announce an attack as "grunts as he takes a swing at you," and the
starter now recognizes that line, preserves the planned target, and runs the
normal consider and source-identity gates instead of treating the attacker as
unknown. A successful recall without an explicit combat-end message is now
also treated as combat-free before healer recovery. The fixes are covered by
the full 1,460-test starter suite, 1,642 campaign tests, and 5,973 repository
tests, with clean compilation.

Revision 319 reopened the exact stale Gnome Village result once. Run 13798
proved the corrected swing parser but exposed the missing recall cleanup; run
13799 then processed the live small troll identity and stopped at the
independent familiar-loss gate, losing 80 XP before returning safely to healer
room 3054. Astrevo is level 9 at 33,932 XP, checkpoint 42837; the Gnome route
is quarantined for this reboot with that familiar-loss evidence. No fame or
HERO claim is made from these results.

The follow-up policy repair now rejects an aggressive or scripted endpoint
unless the source proves an outdoor no-mob waypoint where the familiar can be
summoned and identified before entry. This prevents entry combat from
starting before the familiar can be prepared. Run 13802 then selected the
staged New Ofcol route, killed Granny Jenkins for 118 XP, and returned to
healer room 3054; Astrevo is level 9 at 34,050 XP, checkpoint 42844. The full
campaign suite passes at 1,642 tests; HERO 100 remains unproved.

Run 13803 then captured a useful transport boundary: Granny Jenkins was
present in the live room response, but the ANSI reset and prompt arrived in
different Telnet chunks. The parser now retains an incomplete ANSI escape
between chunks, so the next prompt is parsed with the correct area and room
instead of being mistaken for a malformed response. The bounded worker still
returned safely at its runtime limit with no XP claim. Targeted observation and
starter coverage is 1,503 tests; run 13804 confirmed the current reboot is
unchanged and correctly selected the finite field-reset wait.

Run 13805 then reached the source-ranked Moria endpoint and found the large orc
in room 4019. DD4 also reported a second mobile in that room, so the live
crowd gate stopped the fight before combat and the worker returned safely to
healer room 3054. Astrevo remains level 9 at 34,050 XP, checkpoint 42851. This
is positive target-location evidence, not progression credit, and the next
invocation must rotate rather than replaying the unchanged crowd.

Run 13806 rotated to the Circus and reached the Midget's Tent, but the Midget
was absent while other circus mobiles were visible along the route. The worker
returned safely and recorded a bounded target absence at checkpoint 42854;
the area was not treated as globally empty and no XP was claimed.

Run 13807 rechecked Moria and found the large orc in room 4025, but two
source-registered garter snakes with `spec_poison` were present as well. The
runner rejected that exact room before combat and returned safely. The target
is live and locatable; this route instance is closed by its hazardous
bystanders, not by an assumption that Moria is empty.

Run 13808 stopped before opening a socket because the funding ledger is now
explicit: Astrevo has 27 copper-equivalent, while the current observed fly
price is 131 copper. The all-area source audit found only two direct coin
stashes at level 9, both rejected by route or level hazards; the remaining
local funding targets require fresh area evidence. One finite reset wait is
the next action, not an unbounded funding retry.

Runs 13809-13812 then collected four bounded Moria funding results after the
area reset: the large orc supplied maintenance-only XP of **142**, **152**, and
**148** on productive attempts, while one locator pass found it absent. Astrevo
returned safely to healer room **3054** after every run, with no death or XP
loss, and reached checkpoint **42880** at **34,492 XP**. The resulting rings are
not a money loop: source object 4000 is poisoned, so both the Leather Shop and
Armoury offered zero despite its nominal value. Run **13813** recorded that
evidence, donated five copies, and left one for the next bounded cleanup pass.
The selector now liquidates carried saleable loot when a quarantined
`bank-excess-coins` route would otherwise send the character back to the field,
and it never reserves a known -2 strength ring merely because a finger slot is
empty. The current checkpoint is safe in healer room 3054 with **57
copper-equivalent**; HERO 100 remains unproved.

The full repository regression after this repair is **5,977 tests passed** in
455 seconds; `python -m compileall -q dd4tester tests` also passes. No gameplay
worker remains active; the long-running Python process is the intentional
Discord streamer.

Runs **13814-13817** then kept the continuation bounded. Run 13814 found the
Circus Midget absent; run 13815 revalidated the Moria large orc and earned
**101** maintenance XP, returning safely to healer room **3054** at checkpoint
**42889**. Run 13816 removed the last poisoned ring after both compatible shops
again offered zero; its incidental **10 XP** drunk kill is explicitly marked
below-useful-band and does not count as progression. One finite post-reset wait
then rechecked the Midget in run 13817 and found it absent again. Astrevo is
safe at healer checkpoint **42897**, level **9**, **34,603 XP**, with no carried
loot and no current source-safe funding target. The level-9 all-area catalog
currently admits only the Moria large orc, Circus Midget, and Katrina; Foundry
Uburz remains closed by prior live pre-consider aggression evidence. HERO 100
remains unproved.

### Source-Audited Invisible Funding: September 22, 2026

Policy revision **320** carries source-proven route invisibility through the
provision-funding selector and `Fastwalk` dispatch. It admits one exact,
unarmed dynamic saleable drop, such as the source-safe war-dog collar route,
only when practiced invisibility, every transit mobile identity, current-band,
movement, HP/protection, saleability, and live target gates pass. The segment is
recorded as `funding_only`, so any incidental XP cannot advance progression.
Armed ambush endpoints and the previously quarantined Foundry Uburz remain
closed; Astrevo's current HP ceiling still requires the ordinary protection
gate, so this is offline executable coverage rather than new live permission.
The full repository suite now passes **5,979 tests** in 448.62 seconds, with
clean compilation. HERO 100 remains unproved.

### Source Keyword Identity Repair: September 22, 2026

Run **13818** safely reached the New Ofcol route but earned no XP because the
visible `citizen` name could refer to source mobiles **617** or **618**. The
source catalog confirms their distinct keywords are `man` and `woman`, while
their room text is identical. Revision **321** now chooses a keyword that is
unique among same-display prototypes and lets that exact keyword resolve a
live room only when it is unique among the source identities reachable there;
the shared generic keyword remains fail-closed. Legacy checkpoint candidates
are refreshed before route construction. The full repository suite passes
**5,982 tests**, compilation is clean, and Serevian remains level **11** at
checkpoint **42900** with no new progression or HERO evidence. Run **13819**
then reached the Circus Midget's Tent after the bounded reset wait, found the
source target absent while unrelated mobiles wandered in, and returned safely
at checkpoint **42906** with no XP change. The keyword repair is therefore
offline identity evidence; no live target was promoted from it.

### Bounded Funding and Protection Handoff: September 22, 2026

Policy revision **322** closes a selector stall exposed by the level-11
Serevian continuation. If a current-boot flight-funding carrier is absent while
the protection-recovery sanctuary budget is not exhausted, the runner may make
one source-validated sanctuary acquisition attempt before reopening that empty
carrier. The branch requires the normal healer, food, no-combat, unarmed,
movement, capacity, and source gates; if no safe sanctuary carrier exists, the
funding marker remains and the finite reset-wait path is used. It never grants
ordinary XP permission. The focused regression passes, and live runs
**13828-13833** continued source-backed funding kills without death; run
**13834** rejected an ambiguous New Ofcol cow identity and returned safely.
Serevian is level **11** at checkpoint **42955** with **53,384 XP**; HERO 100
remains unproved. The full repository suite now passes **5,983 tests** in
612.47 seconds, with clean compilation.

### Endpoint Invisibility Admission: September 22, 2026

Policy revision **323** closes a source-ranked selector gap exposed by
Serevian's level-11 route. A route whose aggressive endpoint is source-proven
to be safe only while invisible cannot be selected for capacity or level-
ceiling research unless the character has practiced `invis` and has enough
current mana to cast it. The gate applies before any live connection or
preparation, so an unprepared character is not sent to a route that will
inevitably abort at the safe origin. The independently audited familiar-probe
contract remains available, and ordinary route metadata or sanctuary routes do
not inherit the restriction. HERO 100 remains unproved.

Run 13702 exposed a reset-boundary defect: automatic funding repair cleared the
current-boot absent-Midget marker before policy selection, so the same empty
carrier was reopened. Reset repair now preserves that marker only when flight
funding, protection recovery, and the terminal sanctuary budget all match;
the existing source-ranked fallback then remains responsible for the next
bounded decision. The focused regression and the full campaign suite pass, but
the live reset-wait path still needs a future reboot or area-reset observation.

The HELP FAME rule is explicit in the source mirror: ordinary fame kills need
`victim.level - player.level > 5`, so a level-25 character needs a level-31 or
higher ordinary target. This fame gate is separate from ordinary XP-band
selection and from the source-famous exception. The readiness report retains a
bounded +9 research horizon for readable diagnostics, but the live fame
selector now searches the complete source range through HERO; all existing
route, output, sanctuary, isolation, and finite-action gates still apply.
For the shallow Moria sanctuary endpoint, an adjacent scan that sees the
source-registered warrior now receives one short, bounded re-scan before the
route is abandoned. A repeated hazard still returns safely without combat or
XP credit.

The September 22 multi-character continuation kept the same boundaries
visible. Aeloria's run **13780** reached lemming-smithy room **29966**, found
the source target absent, and returned safely to healer room **3054** at
checkpoint **42770** with no XP change. The one permitted reset wait then
completed without a DD4 reboot; runs **13781-13782** confirmed the same boot
marker and stopped at checkpoint **42773**. Dorrik remains level 25 and
Kestrel remains level 24 with fame -12. No below-band kill, stale target
replay, or unbounded retry was introduced.

The latest multi-character evidence keeps the blockers concrete. Aeloria's
trainer repair issued two accepted `evocation magiks` practices (49% -> 58%),
then a bounded familiar-backed guardian attempt lost the familiar and 232 XP;
that retry is closed. Her lemming-smithy probe then found the source room empty
and recorded a reset-scoped absence. Aeloria's live run **13703** then
completed the Haon food reserve, acquired a toadstool and mushroom, and
returned to healer room **3054** at checkpoint **42595** without XP change or
loss. The later run **13780** reached the lemming-smithy endpoint and confirmed
the target was absent; the one bounded reset wait in **13781-13782** found no
new boot, so that frontier remains closed until fresh reset evidence. Kestrel completed a safe grain reserve
route at level 24 but remains fame -12. Dorrik's tree-sprite and Abyss probes
returned safely without XP. Dorrik's latest reserve run acquired grain and
returned to healer room 3054 without XP or loss. Source analysis also finds a level-18 sanctuary
flask on the grand templar in Dwarven Catacombs. At level 25+, the selector now
proves key 6502 on the exact dwarven guard resets in rooms 6505 and 6540 and
registers a bounded live same-source key gate to exact TARGETMODE guard
selectors, one at a time, before the holy-water route. Its source route checks
the original doorway room, makes one `east east west west` detour to the
alternate carrier room, and returns to the locked door. It stops once the key is carried;
unknown or extra mobiles remain rejected. The route is now available at level
25 with one source-specific transit exception for zombie mage 2011 at the
strict ten-level aggression cutoff; GMCP identity, source damage bounds, good
player alignment, and the non-XP maintenance boundary remain mandatory.
Revision 312 reopens the previous same-boot crowd-abort evidence for this
changed gate implementation. This is executable policy evidence, not live
acquisition or progression proof yet. Revision 313 reopens only the matching
same-boot transit-identity artifact, and revision 314 reopens the matching
health-floor artifact after a gate-maintenance kill. Revision 315 recovers the
exact same-boot key acquisition from the old selector-persistence crash, and
revision 316 reopens only the same-boot reconnect loss without restoring the
non-persistent key. Revision 317 records the alternate carrier-room route.
Revision 318 records that DD4's same-prototype guards automatically join one
another in combat, so the key gate first requires a verified sanctuary reserve;
without one, the planner selects bounded Moria reserve recovery and stops after
its finite attempt budget rather than entering the aggregate guard fight.
None of these migrations relaxes the live selector, source, or bounded-attempt
rules.

**HERO 100 is not yet demonstrated.** Creation, tutorial play, reporting, and
resumable campaigns work. The highest roster level is 25; active fresh-creation
tracks include Serevian at 11 and Astrevo at 9. See the [current review](docs/APPROACH_REVIEW_2026-09-08.md) for
measured results and the [roadmap](ROADMAP.md) for remaining acceptance gates.

The current continuation focus is the level-25 progression and funding frontier,
with Serevian (level 11), Astrevo (level 9), and the other roster characters
retained as alternate tracks. Kestrel remains level 24 with fame -12 and Aeloria
level 18. The sale policy now preserves a generic shop refusal, tries one other
source-compatible safe buyer, and donates only after that bounded retry also
fails. Sustained progression and HERO proof remain open. Ordinary fame recovery
for Kestrel still requires a level-30-or-higher target, plus a live sanctuary
and output envelope. The focused offline suites pass **1,457 starter tests**
and **1,633 campaign tests**. Live dispatch remains gated by source-safe route
evidence.

Serevian's run **13783** supplied a useful safety correction: two level-5
hobgoblin soldiers shared Gnome Village room **1583**, but the old transit
exception fought one before fleeing the second and losing 99 XP. Same-room
source-known below-band crowds are now rejected before combat; only an isolated
bounded interrupter can use the finite transit-fight path. The route remains
closed for this reboot.

Run **13784** then exercised the next New Ofcol policy after that repair. The
live `where` result reached room **655**, where the ordinary `citizen` identity
was source-ambiguous between mobile VNUMs **617** and **618**. The runner
withdrew to healer room **3054** at checkpoint **42782** with no combat, kill,
XP change, or loss, and marked that exact policy unavailable for this reboot.
This is useful identity evidence, not progression proof.

Runs **13699-13702** continued Dorrik's level-25 funding frontier. Run 13699
added 60 maintenance XP from the large orc; the bounded reset retry in run
13700 found the Midget absent and returned safely without XP change. World-time
run **13701** confirmed the same DD4 reboot; run **13702** exposed a reset-repair
marker loss and reopened the absent Midget. The repair is now covered by a
reset-boundary regression. The bounded follow-up world-time run **13704**
found the same DD4 reboot and opened no
gameplay socket because Mr Smithy and the other current-band targets require
sanctuary or fail the survival/output-reserve admission; the remaining
unprotected targets are below-band maintenance candidates. `show-combat-readiness`
now reports
`source_hp_admission`, `requires_sanctuary`, `sanctuary_available`, and
`admission_fit` separately from its older offensive `output_fit` field.

Run **13705** exposed a liveness defect in that maintenance path: after `time`
and `save`, a stale local combat flag reopened the healer sleep loop until the
180-second segment boundary. The completion gate now trusts only the safe,
no-mob healer room's authoritative state, clears that stale local flag, and
prioritizes save/quit over optional healing. Direct live run **13708** verified
the repair with six commands (`time`, `save`, and `quit` after login), returning
at healer room **3054** at full health without a stand/sleep loop. The full starter suite passes
**1,445 tests** and the campaign suite passes **1,608 tests**.

The live Abyss navigator also received a bounded rebase fix: if a changed
maze edge delivers an unexpected room, stale DFS state is cleared once and the
search continues within its eight-rebase limit. The Sahuagin Market purple
potion remains source-only because it is locked in a display case and its key
is carried by level-35 shopkeeper Bilani; it is not treated as level-25
sanctuary permission. The inspection report now also prints the nested
container, required key, and source key-carrier VNUMs.

Kestrel's current-boot Forest crowd hazard is now quarantined at policy
selection: an ordinary resume cannot reopen the same required-loot route after
the live gate observed another mobile. The exact persisted healer-origin
recheck remains bounded and evidence-gated. The live regression stopped at
checkpoint **42402** with no duplicate Forest run, no new XP, and the existing
sanctuary cooldown preserved.

For ordinary fame recovery, `HELP FAME` and `fight.c` require the victim to be
at least six levels above the player (`victim.level - player.level > 5`), so Kestrel's
level-24 ordinary target window starts at source level 30. The source-famous
`ACT_IS_FAMOUS` branch is a separate exception and is not evidence that a
level-25 Green Dragon satisfies the ordinary window. The current source audit
finds no executable ordinary target in the +6 window: his school-dagger
envelope is 318 points, and the available candidates remain above the bounded
output or route gates.
The latest bounded resume returned safely without opening a gameplay socket or
gaining XP; the current reboot's sanctuary protection cooldown remains the
live boundary. Oversized-database startup now uses bounded history repair instead
of an unbounded phase scan. Source policy selection reuses the immutable source
catalog loaded for the attempt and reports each preparation stage, so repeated
selector passes do not silently reparse the world or appear stalled.
Interrupted-segment recovery also reuses that newest bounded tail instead of
scanning the wide campaign table for `status = 'running'`. On the shared large
database, the tail is capped at eight newest segments to keep cold resume
responsive while retaining the latest interruption and retry evidence.

When a required sanctuary carrier route exhausts its two current-reboot probes,
the campaign may arm exactly one additional recheck after a bounded area-reset
wait, provided the character is alive and safely checkpointed in healer room
3054. The prior attempts remain in the audit ledger; a failed post-reset cycle
is terminal until a reboot, level change, new source evidence, or a narrowly
matched code-revision migration.

The exact level-20 generic sanctuary-recovery fallback now has a bounded
eight-location locator sweep with source-identified below-band route gates in
Moria. Gate kills are maintenance-only and never progression XP; live
validation is deferred until the next MUD area reset or reboot.

The parser now mirrors the refreshed DD4 source's three weighted mobile-special
slots, area `#SPECIALS` `M`/`N`/`P` overrides, and explicit `AFF_MINDLESS` flag.
Existing live checkpoints retain their recorded source revision until resumed.

The source-area parser also mirrors `db.c`'s `D`-record lock-type mapping:
the second field is a lock type, not an exit-flag bitmask. This reopens ordinary
`-1` exits and correctly marks type-2 doors as `EX_PICKPROOF`. The Dwarven
Catacombs sanctuary reserve therefore uses key 6502 rather than `pick lock`:
the room-6505 guard is an isolated, live-considered maintenance gate, and the
key plus flask VNUMs remain bound to the required-loot audit.

Source resource analysis now recognizes DD4 `ITEM_PILL` objects such as Olympus
nectar, reports their exact `eat` activation, and clears the reserve only after
the live acknowledgement. This is source and parser evidence; it does not
claim live pill acquisition or progression.

Maintenance-route hazards are now checked before Forest gear preemption and
frontier retry selection. Current-reboot crowd evidence therefore closes the
implicit retry path instead of consuming another zero-progress segment.

The current campaign policy revision is 317. It preserves the source and live
GMCP gates while allowing a nominally current-level passive target whose DD4
load-time HP fuzz reaches two levels above the character to receive one
sanctuary-protected damage-window probe. This is a measured admission path,
not a general level or safety override. It also lets reachable direct ground
gear resets improve combat output before the campaign attempts flight funding
or a carrier fight. For the exact source-famous Green Dragon gas contract,
sanctuary plus healer nausea recovery can extend the live probe to the existing
finite 36-action horizon after sanctuary is observed; the ordinary source
estimate remains twelve actions and is unchanged before that point.

Revision 311 also closes the New Ofcol identity gap exposed by run 13714.
When multiple source VNUMs share one room and display name, the runner may use
the exact live TARGETMODE selector only when every reachable prototype is
source-identical, ordinary, unarmed, unspecialized, and has no loot or probe
contract. The observed alias VNUM is persisted in the run and campaign state;
materially different prototypes remain a hard rejection.

Casters now retain a bounded fallback inside an admitted fight: after two weak
uses of the preferred practiced damage spell, the live damage probe may measure
the next practiced source-registered spell. The rotation is finite per target
and does not bypass source admission, mana reserves, incoming-damage checks, or
withdrawal. It is intended to handle live resistance differences without
pretending that offline spell estimates prove a kill.

Live run **15277** showed that DD4 can append the target's wound description
and prompt after a valid spell-hit line; an end-of-line-only match then timed
out and blocked later combat commands. The matcher now recognizes the exact
target within that bundled reply while retaining quoted-speech and target
checks. `test_combat_timing.py` includes a saved-format regression case; it
awaits the next daily test batch, and the same-boot Fleshmonger target remains
closed to live retry.

The mage training graph now continues past burning hands. When the current
teacher listing exposes each dependent skill, the planner can advance through
the source prerequisites for shocking grasp, lightning bolt, colour spray,
fireball, and acid blast, and can build the exact shield and stone-skin gates.
The output estimator and combat acknowledgement registry mirror those spells'
source formulas and mana costs. Live trainer audits now persist both known and
learnable skills: Aeloria's level-18 listing exposed only ventriloquate,
summoning magiks, enchantment magiks, and mana control disciplines, so the new
combat chain was correctly deferred without spending practices. This is still
offline capability coverage; no new live kill or HERO evidence is claimed until
a bounded run validates the path.

Live run **13424** exposed a real maintenance hazard: an aggressive wandering
Thalos lamia disarmed Serevian and caused **339 XP** of bounded withdrawal loss
before healer recovery. The Thalos long-dagger route now requires a single
isolated carrier and a sanctuary reserve in both progression selection and the
field stop; without that reserve, the campaign safely chose the Midgaard rearm
route instead (run **13425**). Run **13426** then killed the source griffin for
**270 eligible XP**. Run **13427** recorded a clean New Ofcol absence with no
XP change. These are live safety and rotation evidence, not HERO proof.

The exact Shadow Keep fine-dagger maintenance plan is now selectable at level
24 when a Thief needs the upgrade and has sanctuary, capacity, funding, and
the source-prerequisite evidence. This does not change fame admission: the
ordinary fame target still starts six source levels above the player. The
level-plus-two exception is limited to the source-identified smuggler's
economic `spec_thief` route, its protected HP/output probe, and its exact
lockpick-and-loot actions; live acquisition remains unproved.

Run **13428** exposed a liveness defect after a below-band funding target fled:
the subsequent absence response left the field stop open until the progress
watchdog intervened. The policy now closes only that explicit coin/required-loot
stop after a started engagement and bounded absent re-check, preserving the
no-progression evidence and returning safely. Run **13430** live-regressed the
funding path successfully: Serevian killed the source-verified Circus Midget
for **40 non-progression XP**, recovered the purse coins, and returned to healer
room **3054** at checkpoint **41942**. Follow-up runs **13431-13436** completed
the purse cleanup, bought flight, added **332** and **248** eligible XP from
two more griffin segments, and recorded two clean New Ofcol rotations; Serevian
is now safely checkpointed at **41963** with **51,748 XP**.

Run **13436** exposed a route-state defect in source-ranked locator narrowing:
after a positive `where` result, a compacted stop could retain a destination
VNUM without the audited waypoints from its actual live room. The starter now
re-roots such segments only through rooms already present in the registered
source route, and remains fail-closed for missing, closed, or randomized paths.
The exact 621-to-632 New Ofcol replay now restores the audited route through
618, 668, 611, 608, 605, 602, 601, and 625. Run **13439** verified that the
campaign resumes cleanly at the current sanctuary cooldown without opening a
socket. Starter coverage is **1,433 tests** and campaign coverage is **1,566
tests**; this is route-safety evidence, not HERO proof.

Run **13445** validated the follow-up repair for skipped wandering-target
stops. Serevian's source-ranked citizen circuit advanced through rooms **637**,
**642**, **646**, and **647** after the live identity gate rejected the
source-ambiguous citizen VNUMs **617/618**; it no longer asked room **632** for
an impossible direct exit to **651**. The segment returned to healer room
**3054** at checkpoint **41975**, level **11**, with **51,748 XP**, no kill,
death, or XP loss. This is successful navigation and fail-closed identity
evidence, not progression proof. The ordinary fame gate remains the HELP FAME
rule: a plain target must be at least six levels higher; source-famous targets
are a separate contract.

The level-up repair now trains fresh practices before optional loot liquidation
when no active provision-funding obligation exists; funding and affordable
flight remain ahead of training. Verification is **1,434 starter tests** and
**1,566 campaign tests**.

Revision 305 applies the same bounded reasoning to ordinary fame recovery: a
plain target in DD4's +6-or-higher fame window may be admitted when its
source HP lower bound fits the current player output, even if its load-time
upper bound exceeds player HP. Sanctuary must be verified, the live stop must
measure GMCP HP and damage output, and a target above the measured action
budget is still abandoned before a losing fight.

Revision 306 carries the exact source upper level bound into every generated
stop for a sanctuary-backed, required-loot gear carrier. This closes a route
construction gap when load-time level fuzz reaches the source-recorded upper
bound; it does not authorize unprotected combat or change the ordinary +6
fame rule. Kestrel has not yet live-validated this acquisition.

Revision 303 makes healer recovery explicit when a checkpoint at room 3054
still carries active poison. It permits the one reopened Forest
gear route to proceed after recovery despite the old level-24 protection
marker, but only for the exact source-identified claw objective and only once.
Live run **13277** cleared Kestrel's poison at the healer. Run **13278** found
the Kodiak in the River bed, met a live poison-swarm crowd at gate room
**18027**, withdrew, retried once after healer sleep, and withdrew again without
XP loss or claw acquisition. The route is now closed for this reboot; this is
safety and liveness evidence, not progression.

`show-combat-readiness` reports alignment and fame separately, along with the
current quest status, questmaster route, quest-point level gate, and the
source-backed fame outcome. Only a completed kill quest awards positive fuzzy
fame; object, retrieve, and hoard quests award quest points or gold but no
fame. A negative-fame character therefore needs a proven gear/output route or
an eligible fame-awarding kill, not a guessed quest request.

The fame-recovery policy mirrors the `ACT_IS_FAMOUS` fame branch in `fight.c`. For
Kestrel's negative-fame recovery, the offline selector now identifies Green
Dragon mobile 6112 as a one-shot candidate only with sanctuary, the exact
source route and HP budget, and healer mobile 3012's source-proven
`spec_cast_adept` recovery for gas-breath nausea. This is an offline policy
authorization for a bounded live probe; no Green Dragon kill, fame recovery,
or HERO progress is claimed yet.

The `--autonomous` supervisor now counts one completed reset wait rather than
each progress heartbeat and preserves every bounded result in SQLite.
His source-verified long slim dagger (vnum 5252) gives a
318-point conservative opener-plus-repeat ceiling. The current local DD4
checkout is `4cffee6` (full revision
`4cffee6551bda62b0c7accc439dfb5069712e2c0`). Earlier run notes below retain
the source revisions they were collected against. Readiness finds
317 source-band candidates, 93 autonomous-safe candidates, 1,154
output-fitting candidates, and protected HP probes under the revision-302
nominal-current-level admission. The newly selected Shudde-M'ell route still
requires live GMCP confirmation and may withdraw without combat. Runs 13093 and
13100 proved both permitted
Moria carrier instances and acquired two purple sanctuary potions for 180
maintenance XP without dying. Run 13117 reached Chaplain Jerrold at 416 HP and
withdrew before a losing exchange against the 318-point ceiling. Astrevo's
latest checkpoint is 40956; runs 13179 and 13181 added 180 and 118 XP from
source-ranked current-band routes. Runs 13180, 13182, and 13184 recorded
bounded target-absence or crowd outcomes, while runs 13183 and 13185 kept the
finite provision-funding boundary explicit. Run 13185 also recorded an exact
source sentinel one room before its registered reset room; the interception
now resumes that already-vetted outbound step after a temporary crowd instead
of recalling before the reset endpoint is checked. Run 13186 exercised that
one-shot campaign revalidation live: the endpoint was checked, a new
two-mobile crowd closed the marker, and Astrevo returned safely to healer room
3054 without XP change. Runs 13190-13192 then exercised overweight sack
recovery, coin banking, route rotation, and interrupted-worker recovery; the
latest boundary remains safe at healer room 3054 with no new loss. Run 13125
added 40 below-band maintenance XP and a 50-copper
Midget coin drop; runs 13126-13127 completed Circus and Mirror Realm fame
recovery checks with no XP change. Run 13132 completed a patrolling-guard
funding attempt for 90 below-band maintenance XP and 1 copper. Run 13133
acquired the second purple reserve for 100 maintenance XP; runs 13134-13135
recorded bounded fame-route boundaries without XP change. Run 13136 added 110
maintenance XP and 1 copper against the on-duty guard, after which the selector
correctly reopened Moria sanctuary recovery. No sustained HERO progression or
HERO proof is claimed.

Run 12985 refreshed source-verified food and the DD4 source revision. Run
12986 used the exact source-ranked `where drunk` locator to reach the Solace
Secretary route, then withdrew before combat because the loaded target's
source HP ceiling exceeded Kestrel's fixed knife-toss budget. Checkpoint 40039
preserves that evidence and the one same-reboot loss record, so the chooser
will not repeat the probe until a fresh legal route is available.

Campaign startup reuses a current-level, current-reboot live training audit
when one is present, avoiding a large historical event scan in the shared
SQLite database. Legacy checkpoints still receive historical skill backfill;
the public runner reports each preparation boundary and stops within its
bounded setup allowance.
Score-confirmed maxed stats are saved with campaign progress and restored on
the next session, so pre-level stat choices can move on to the next useful
stat instead of repeating a capped one.

## Setup

Run from the repository root with Python 3.12:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
python -m dd4tester --help
```

Leave the environment with `deactivate`. Without activation, replace `python`
with `.\.venv\Scripts\python.exe` in these examples.

## Create Or Resume

```powershell
python -m dd4tester hero-options
python -m dd4tester hero --race human --sex female --class mage --prepare-only
python -m dd4tester hero --race human --sex female --class mage --progress
python -m dd4tester hero --race human --sex female --class mage `
  --autonomous --progress
python -m dd4tester hero --username Astrevo --workspace runs/heroes/astrevo `
  --segments 3 --max-segment-runtime 180 --reset-retries 1 --reset-wait 180 --progress
python -m dd4tester hero --username Ararisa --progress
```

`hero-options` lists source-legal identities. Requests accept race, cosmetic sex,
base class, optional level-30 subclass target, name, and personality. Omitting
the name generates a stable name. `--prepare-only` writes configuration without
connecting; repeat the same request/workspace to resume. Names select history,
never special gameplay behavior. If duplicate folders match a name, resume may
select the sole checkpointed campaign only when the other matching folders are
confirmed to have no campaign record. Conflicting identities, multiple tracked
campaigns, or unreadable history remain an error rather than a guess.

When no HERO workspace matches `--username` and race/class are omitted, the CLI
also checks `runs/dd4tester.sqlite3` for that character's latest saved campaign
checkpoint. It reuses the recorded profile and campaign file, so resuming an
older campaign does not create a duplicate character workspace.

```powershell
python -m dd4tester hero --name Newmage --race human --class mage `
  --personality "patient, observant, and dryly funny" --prepare-only
python -m dd4tester hero --username Existingthief --race drow --class thief `
  --subclass ninja --password PLACEHOLDER --target-level 30 --prepare-only
```

Remove `--prepare-only` to execute. `--username` aliases `--name`.
`--target-level` accepts 2-100, default 100. A resumed target can be extended,
not lowered; use a separate workspace for a shorter validation horizon.
`--new` starts a new stored campaign, not a second identity in the MUD.

For a bounded, source-audited sanctuary-resource check on an existing
character, use the ordinary Moria probe or hunt. Characters at the level-24+
frontier can use the deep route, which follows the registered room-VNUM
detour and still requires the live carrier, consider, crowd, and required-loot
gates:

```powershell
python -m dd4tester moria-research runs/heroes/dorrik/character.yaml `
  --sanctuary-deep-hunt
```

This command is maintenance evidence, not ordinary XP or fame progression;
the autonomous `hero --autonomous` campaign remains the production path.

`hero` is a bounded invocation. Add `--autonomous` to keep opening one
bounded worker at a time until the target is reached or the campaign reports a
durable blocker. In this mode `--segments` is the cycle budget and
`--max-reset-waits` (default 3) is the total area-reset wait budget. The
supervisor preserves the same SQLite checkpoints and credentials between
cycles, counts one completed wait rather than each progress heartbeat, returns
on a real failure or blocked policy, and never spins on an unchanged world. A
returned `ready` result is safe to resume later.
An exhausted, already-dispatched sanctuary recheck remains blocked across
process restarts; it does not authorize another identical area-reset wait.

### Credentials

New executed HERO requests generate and store their password in Windows
Credential Manager. Named resumes reuse `character:<name>`. `--password` or
the matching environment variable overrides it; `--remember-password`
explicitly saves that override for later resumes.

Plaintext arguments can appear in shell history and process listings. Prefer
stored credentials for unattended runs. Passwords are redacted from transcripts
and never written into generated profiles, requests, reports, or SQLite.

```powershell
python -m dd4tester configure-login
python -m dd4tester configure-character-password profiles/your-character.yaml
```

The first configures scenario login; the second configures a profile credential.
`DD4_USERNAME`, `DD4_PASSWORD`, and profile password environment variables remain
supported.

### Bounds And Recovery

`--segments` limits checkpoint segments. The public `hero` command defaults to
`--max-segment-runtime 300`, so every live worker has a bounded field and
healer-return window while the process continues through durable checkpoints.
The Python `run_hero_request` entry point uses the same 300-second default and
normalizes a missing cap to it, so library callers receive the same liveness
contract.
An explicit `--max-segment-runtime 180` on `campaign` requests a shorter
continuation and defaults reset retries to zero. Add
`--reset-retries 1 --reset-wait 180` for one wait outside a depleted area.
For either command, omitting the runtime override retains the command's
default; longer values are explicit bounded probes, not an unbounded mode.
Live cleanup has its own allowance.
On shared databases larger than 1 GB, startup skips the campaign-phase index
migration and uses bounded loss-history repair so a long-lived SQLite file
cannot block a hero resume. Build that index during a separate maintenance
window if full historical phase repair is required.

If a worker is stopped after its deadline, recover only its campaign on a large
shared database so maintenance stays bounded:

```powershell
python -m dd4tester recover-runs --campaign-id 28 --character Aeloria
```

The scoped command uses the campaign segment index and does not scan every
historical run. It also closes a run row left marked `running` after its
campaign segment has already failed. The no-argument form remains available
for small databases.

For unattended progression, use `hero --autonomous --progress`. Its worker
and reset budgets are finite by design; increase them explicitly only when
the surrounding run supervisor can observe and stop the process.
Ctrl+C exits 130 after preserving the durable checkpoint, so the same command
can be resumed without treating an operator stop as a silent hang or a fresh
character run.

Use at least two segments when a reset wait may need a world-time probe before
field selection. The probe consumes a segment. A fresh response confirming the
same reboot after the completed wait permits reselection; an area reset does
not require a reboot. Missing observations and ordinary loss, route, resource,
and protection gates still block execution. `--retry-stalled` permits one bounded
frontier rotation, not a safety override. For a level-10-through-29 thief whose
current-band output-fitting frontier is empty, it may also open one exact
source-audited Forest bear-claw maintenance attempt. That exception requires
the healer checkpoint, food, water, movement, weight, protection, route, and
live gates; it records boot, level, and source revision before connecting and
closes after the attempt. It is not an XP or below-band permission.

The normal attempt limit still ends the invocation even when reset retries
remain. A funding-exhausted `ready` result can represent an area-reset wait;
read its message as well as its status. A new bounded invocation can use its
own explicit retry budget; do not run duplicate workers.

When a character is already safe in healer room 3054 and policy selection has
no executable frontier, the runner performs one automatic maintenance-only
world-time probe before returning the unavailable result. It issues `time`,
saves, and quits within the normal bounded worker. A same-boot response is
persisted as an area-reset wait; a failed or completed probe is not repeated
until the reset-aware path supplies fresh evidence.

Resume also reconciles losses first observed after a disconnect. A verified
same-level XP decrease sets a lower bound on `campaign_xp_loss_total`, even
without a captured penalty message. This does not invent a death or identify
the command that caused the loss. Replaying saved history cannot charge the
same decrease twice; explicit larger loss counters remain authoritative.

For wandering hunt targets and funding carriers, the runner can stop the approach at a verified
waypoint in the same area and locate the target before visiting its reset
room. Fresh results choose a source-checked route; uncertain approaches keep
the original plan. This saves travel without adding searches or retry budgets.
Ordinary hunts retain any required familiar staging waypoint before locating
the target. Specialised transit-recovery plans, closed or random approaches,
and routes whose required preflight would be omitted keep the original route.
If a below-band wanderer is intercepted before the planned destination, the
runner retains its exact route position and continues the unvisited path.
It does not jump to the following leg as though it had reached the endpoint.
Later targets still need fresh consideration; no search or retry budget grows.
An intercepted room check retains control after a bystander response. The
remaining exact target must receive its own consider before travel or attack;
an inconclusive check cannot silently resume the outbound route. This handoff
is replay-tested, with fresh live acceptance still pending.
A uniquely source-identified sentinel seen beside its planned reset room can
also be considered on approach. This requires a fresh exact instance and
matching source/live room exits; normal crowd, combat, and loss gates remain.
Run 13186 live-validated the navigation handoff once. A pending marker can
open only that exact source-ranked segment through the outer crowd wait; the
segment consumes the marker and a new crowd closes it without granting combat
permission or XP credit.
Restricted protection-carrier trips can query the exact source identity before
their final approach, then search accessible source-mapped rooms. The bounded
plan retains excluded locations as sightings rather than reporting area absence;
it does not grant access to hazardous deep routes or bypass combat checks.
The deep-reserve fallback can use this same search from level 16 when
invisibility is source-authorized and positively practiced. A fresh live effect
is still required. Lower-level or unqualified characters retain the restricted
reset-room plan; the change does not grant a new retry or reduce required loot.
When an exactly identified carrier shares its room with one ordinary bystander,
the runner uses its existing bystander consideration and bounded crowd waits.
Only fresh evidence can discount that bystander; the carrier still requires
its own normal combat checks. Dangerous or unidentified crowds remain blocked.
An absent carrier in a fully source-identified passive room can use the normal
search continuation to the next already-planned endpoint. This is not combat
permission, and it adds neither locator queries nor route alternatives.
On resume, checkpoint cleanup does not treat an inherited field-abort message
as a fresh funding failure. A completed, safely returned carrier run can repair
that exact replayed restriction; newer failures and other route hazards remain.

Positive, source-tagged funding kills also update their exact hunting-route
reward evidence. Their runs remain funding segments, and XP is not counted
twice. A fed character may prefer an executable ground hunt when the latest
same-reboot carrier sale cannot cover the observed flight-price shortfall.
Food, protection, loss, and retry requirements still apply; this preference
does not authorize another loan or an extra trip for missing protection.
Below-band kills selected specifically for provision funding are retained in
`completed_kills` even when they are absent from `objective_kills`; successful
funding advances its retry cooldown without becoming progression proof.

If an identified familiar finishes the pending target before the player can
attack, the runner records a zero-XP encounter, cancels that player opener,
and preserves corpse looting. Source-ranked low-load targets whose audited
player damage budget already covers their HP ceiling now withdraw the familiar
after its opening probe so the player receives the kill credit. This remains
maintenance evidence until player XP is observed in the transcript; ordinary
progression must still be earned from the live player kill. The opening-death
fix is replay-verified.

Familiar preparation waits for its own summon, room-listing, and grouping
acknowledgements within one 30-second deadline. Unrelated world messages do not
trigger a duplicate cast or immediate recall. Temporary confirmation failures
retain the normal bounded retry; explicit refusals and identity failures do not.

A freshly considered easy-kill load may instead use a source-budgeted solo
fight. The runner first confirms that its owned companion is asleep, then
uses the existing timed encounter and measured-damage checks without companion
damage credit. It confirms the companion is awake before ordinary onward
travel. Each acknowledgement is capped at five seconds; an uncertain handoff
returns to recovery. Stronger or underfunded targets keep the normal familiar
path. No new CLI option is required. This does not yet avoid summoning costs.
Solo continuation uses the opponent's remaining health, current spell costs,
observed damage rate, and the original time/command limits. A single missed
spell or narrowly missed opening-damage threshold is not itself a retreat.
The live sleep/opening sequence is confirmed; a complete solo kill/wake cycle
with this continuation correction still needs live acceptance.

For a source-ranked target whose audited player output already covers the
target HP ceiling, the familiar may make one bounded probe attack, then the
runner confirms its withdrawal before opening player combat. For DD4's charmed
pony this uses the source-recognized `order <familiar> flee Fear` override and
requires the positive in-place sleep message; ordinary familiars require the
actual departure message. This
prevents a familiar's next round from taking the finishing blow. Run 13053
live-proved the sequence against Granny Jenkins: Astrevo personally received
168 objective XP and returned safely.
If the familiar cannot be positively withdrawn within its bounded attempts, the
runner abandons the stop and returns through the healer path; it must never
fall through to a player opener after that failure.

Fixed fame routes use the same source-backed player output envelope as the
dynamic frontier. Their live damage-window probe compares measured target and
player HP against the current action budget; a target that cannot be completed
inside that budget is abandoned before protection expires. GMCP target level
and HP remain authoritative, while source estimates only admit or bound the
probe.

A roaming city obstruction can trigger up to three 12-second healer waits
within a shop segment, each followed by a fresh location check. Persistent
obstruction normally stops travel. Invisibility requires source authorization,
positive observed practice, sufficient mana, and an awake noncombat state;
class and level alone do not authorize a cast.

For source-audited field routes, fresh active invisibility can also suppress
an ordinary sight-dependent greeting hazard and a source-proven plain
aggressive endpoint target's entry auto-attack. This does not bypass detecting
mobiles, all-greeting programs, unrelated hazards, capacity/consider checks,
or combat checks. Expiry,
an explicit invisibility-loss message, or reconnection revokes the exemption;
saved effects alone never grant it. Route messages distinguish the observation
room from the reported mobile location. No additional CLI option is needed.

Required-loot carrier searches can use the same source-proven visibility rule
for ordinary aggressive transit mobiles. The character must have an audited
class path, positive observed `invis` practice, and a live effect that the
runner maintains while moving. Detect-invisibility, scripts, equipped reset
objects, pre-combat specials, and unknown behavior remain hard exclusions.
This may inspect up to 12 rooms within the existing 24-step circuit; target,
consider, crowd, resource, and return-home gates are unchanged.
Because `where` reports display labels rather than room VNUMs, a bounded plan
preserves coverage for distinct labels before adding duplicate names. A field
`look` completes only after an actual room listing. Unrelated status output is
ignored; silence receives one five-second retry and then a safe abort. An empty
locator path never rechecks a room already proved empty.

An ordinary aggressive transit mobile with a combat-only special follows the
same source aggression cutoff as its normal attack. The route remains blocked
when the highest fuzzed mobile level is within ten levels of the character;
only a strictly larger gap makes that special inert before combat. Pre-combat,
economic, scripted, equipped, unknown, engaged, and endpoint hazards remain
blocked. This rule can widen an existing bounded locator circuit, but it adds no
room, step, query, retry, combat, or resource permission.

When a city obstruction is recorded, the existing world-time probe also makes
one observation-only `where drunk` check at the healer. A fresh off-route
location may release that route cooldown, but not an actual purchase failure.
The next shop trip still performs its own preflight. No extra wait or segment
is added, and the probe never buys, borrows, or travels to a shop.

Flight shopping may instead admit the existing source-bounded city greeter risk
when the character is ready. This allows one isolated, exactly identified weak
interruption, with a 70% health floor and 60-second combat deadline. Extra or
unidentified enemies, changed source bounds, or the segment deadline force
withdrawal. A failed attempt remains excluded at the same level/reboot; missing
reboot evidence never grants a retry. Purchase failures and loan limits remain.
The audit is stored as `campaign_city_shop_transit`; timers are connection-local.

Source-backed field departures also check the actual Midgaard route and fountain
when guard assistance cannot be ruled out by revealed alignment. This shares
the bounded city locator/wait behavior; it adds no retries to the campaign.
`campaign_field_city_preflight` records the result separately from shopping.
DD4 sends the actual alignment through `Char.Worth` at level 10 and above,
clamped by the server to -1000..1000. Below level 10 it intentionally sends
50000 as a concealment sentinel. The parser retains the wire value in state and
transcripts; policy derives only a level-aware, in-range value. `spec_guard`
uses 300 as its own assistance cutoff, while `violence_update` separately
requires both a good bystander and a good player at the exact 350 threshold to
suppress its generic assist. A target NPC's alignment is not a substitute for
the player's value. Raw packets remain unchanged in transcripts.
A confirmed healer-origin departure deferral stops the current invocation after
its existing short waits. It consumes the segment but not a funding-target or
hunting-endpoint attempt. The checkpoint reason is
`field_city_departure_blocked`. A later invocation with the same level and
reboot blocks the recorded policy when its exact policy ID is present; a
different source-ranked route gets its own bounded preflight. Legacy
checkpoints without a policy ID remain conservative and require fresh
`time`/route evidence, so repeated calls cannot burn identical city checks.

A below-band target is still skipped for XP. If it has already attacked at its
registered endpoint, one exactly identified ordinary enemy may use the existing
30-second combat-finishing budget instead of an automatic XP-losing retreat.
Source hazards, fresh health/mana, nutrition, extra attackers, and command
acknowledgements still govern continuation. Its kill is incidental, never a
repeatable XP objective. Inspect `campaign_fastwalk_encounter_budgets` for the
`below-band-endpoint-defense` audit; no new CLI option is required.

Source-ranked routes also carry an explicit source VNUM for at most one
borderline transit aggressor when source damage bounds prove the reset safe.
The live runner may finish that exact mobile once if GMCP confirms an isolated
below-band instance and the ordinary health, nutrition, consider, and combat
gates pass. The result is recorded as maintenance and cannot become an XP
target; unregistered attackers and useful-band rolls still cause withdrawal.

Run only one gameplay worker at a time. After an interrupted worker has stopped:

```powershell
python -m dd4tester return-home profiles/your-character.yaml
python -m dd4tester resupply profiles/your-character.yaml
python -m dd4tester restock profiles/your-character.yaml
```

Recovery belongs at Midgaard healer room 3054. Never quit in Purgatory.
See [operating instructions](docs/OPERATIONS.md) for timeout and process rules.

## Inspect Progress

Replace these examples with IDs printed by your run:

```powershell
python -m dd4tester show-runs --limit 20
python -m dd4tester show-transcript 12767
python -m dd4tester show-state 12767 --history
python -m dd4tester show-campaign 7
python -m dd4tester report 12767
python -m dd4tester campaign-report 7
python -m dd4tester report 12767 --format json --output reports/run-12767.json
python -m dd4tester show-combat-readiness --level 24 --class thief `
  --character Kestrel --all-areas
```

Reports distinguish XP, kills, losses, deaths, decisions, and recovery. Non-secret
title, description, and personality remain in run context. Commentary derives
from stored events; a report does not itself prove autonomous HERO progression.
The parser now reconciles DD4's LF-CR flee/refund lines with GMCP without
subtracting the same loss twice. Historical records are not rewritten:
run 12816's raw GMCP confirms 28,815 XP (net -53), while checkpoint 39419
incorrectly retains 28,747. Fresh recovery run 12820 confirmed 28,815 and the
normal public resume saved it in checkpoint 39433. This correction is not
earned XP; the genuine loss and original audit records remain relevant.
For multi-stop source hunts, the circuit name is not the killed target's
identity. Reconnect reconstruction uses each kill's source policy ID and keeps
later stop-specific failures distinct from that earlier success.

Crowded field rooms can receive up to three exact-instance consider probes per
visit. Only positively identified below-band bystanders are discounted; a
remaining XP target still needs its own ordinary consider and combat checks.
Follow-up attacks retain the selected instance rather than switching to a
same-name bystander. These probes are recorded under
`campaign_fastwalk_bystander_consider_outcomes`, not restored as permissions.

An ordinary source-ranked hunt may also admit one exact, distinct room
bystander when its stop explicitly opts in. The primary target and bystander
must be source-identified, unarmed, ordinary, non-aggressive, non-scripted,
non-special mobiles with fresh exact selectors and easy-kill considers. A
source-estimated two-mobile HP, incoming-damage, mana, and six-action budget
must fit at near-full health. Any extra, unknown, armed, scripted, special, or
scope-changed mobile withdraws the fight. The result is audited in
`campaign_fastwalk_encounter_budgets`; it is regression-tested, but live
acceptance and any XP claim still require a fresh DD4 run.

## Data Locations

Defaults when running from `E:\dd-playtester`:

| Artifact | Location |
| --- | --- |
| SQLite | `E:\dd-playtester\runs\dd4tester.sqlite3` |
| JSONL transcripts | `E:\dd-playtester\transcripts\<scenario-name>-<run-id>.jsonl` |
| HERO request/profile/campaign | `E:\dd-playtester\runs\heroes\<workspace>\` |
| Target-completion reports | `runs/heroes/<workspace>/hero-report.json` and `hero-report.md` |
| Development conversation | `E:\dd-playtester\DEVELOPMENT_CONVERSATION.txt` |

Relative locations resolve from the working directory; profiles/scenarios can
configure other destinations. Run records retain the actual transcript path.

SQLite tables: `runs`, `events`, `state_snapshots`, `character_commands`,
`character_acquired_items`, `character_item_backfills`, `loot_sales`, `mob_kills`,
`campaigns`, `campaign_segments`, `campaign_checkpoints`, and `campaign_usage`.
`mob_kills.route_gate` marks an incidental source route-gate kill; it is not
progression evidence even when the kill produced experience.

`loot_sales.sold_coins` and campaign funding `proceeds` are gross shop prices,
not necessarily carried income. Shops divert part of a sale toward outstanding
bank debt; use the live currency snapshots and loan notice to reconcile cash.

```powershell
python -m dd4tester show-transcript transcripts/login-1.jsonl --raw
python -m dd4tester campaign-report 7 --format json --output reports/campaign-7.json
```

## Scenarios And Source Analysis

```powershell
python -m dd4tester run scenarios/login.yaml
python -m dd4tester run scenarios/capture.yaml
python -m dd4tester starter profiles/starter.example.yaml
python -m dd4tester campaign campaigns/hero.example.yaml
python -m dd4tester show-policies --class mage --level 8
python -m dd4tester skill-analysis --class warrior
python -m dd4tester show-prereqs --class mage --skill fireball
python -m dd4tester show-gear-sources --level 24 --class thief `
  --stance combat --all-areas
python -m dd4tester show-combat-readiness --level 24 --class thief `
  --character Kestrel --all-areas
python -m dd4tester autonomy-audit --race human --sex female --all-classes --target-level 100
```

The capture scenario connects to `dragons-domain.org:8888`, observes room and
character output, and quits. Configure credentials first. Static audits describe
registered templates, not live executable coverage. Observed skill names require
source authorization and positive practice before execution.

`hero --source` accepts the DD4 source/area directory or `const.c`. Workspaces
retain the resolved directory and source evidence. Keep the local DD4 checkout
fresh and review changes before live use. Race/class validation is declared in
`matrices/level-10-all-race-class.yaml`; the existing roster is in
`matrices/active-hero-rotation.yaml`. Run serially and use `matrix-coverage` to
distinguish declared entries from actual proof.

`show-gear-sources` ranks source-reset equipment for a requested class and
stance (`combat`, `pre_level`, or `recovery`). It includes equipped and carried
mobile drops, shop stock, ground resets, source level ranges, route origins,
exact source keywords, hazards, autonomy rejections, and a `weapon_role`
column. Thieves automatically receive the source-backed `piercing` primary
preference used by the backstab planner; stronger non-piercing weapons are
shown as mismatches rather than upgrades. Use `--database` and `--character`
to compare the latest stored loadout. This is acquisition evidence only: a
promising row does not authorize combat or claim live availability. Campaign
execution additionally requires an exact source-ranked carrier hunt when the
item is mob-carried or mob-equipped, including one source spawn, clean route
and hazard gates, a fitting live HP budget, and an exact post-kill loot/equip
step. Source class-slot coverage and live carrier acquisition remain active
proof gaps.

`show-resource-sources` lists healing, food, sanctuary, protection, and flight
resources while keeping executable routes separate from source-only
analysis. When a placement is behind a locked door, its
`source_analysis_route`, `route_key_objects`, and `route_key_sources` columns
show the paper route and source key provenance; those rows remain diagnostic
evidence and are never dispatched automatically. On shared databases larger
than 2 GiB, inspection checks only each campaign's latest indexed checkpoint;
it does not scan the full checkpoint history, and it retains campaign safety
and same-boot target evidence.
The source parser also retains each area header's display range and its
separate movement-enforced range from `db.c:load_area`. Candidate endpoints and
resource routes behind an enforced gate, or inside a `-4 -4` safety area, are
rejected before live planning; a display range alone is never treated as an
access permission.

`show-combat-readiness` is a read-only checkpoint and source audit. It reports
the learned repeatable action, conservative damage ceiling, durable campaign
constraints, separate player alignment and fame, ranked current-band targets,
and stronger gear placements with their source rejection reasons. Use `--json`
for automation. Its output is
analysis only and never authorizes a live connection; a target still needs
the campaign's fresh consider, protection, resource, route, and loss gates.
The report also evaluates DD4's ordinary +6-or-higher fame rule separately
from the usable `ACT_IS_FAMOUS` branch. Its current +9 ceiling is a bounded
research horizon, not a game rule, so fame candidates and their blockers remain
visible without misrepresenting the source behavior.
The source report also exposes each target's resolved `MobDamMod`; this is the
per-attack NPC damage scalar from the pinned DD4 source, applied before
sanctuary and critical-hit bounds. An unknown scalar rejects the target rather
than silently treating it as neutral.

## Mudlet Visibility

```powershell
python -m dd4tester mudlet-bridge --directory runs/mudlet-bridge
python -m dd4tester hero --race human --sex female --class mage `
  --transport mudlet --mudlet-directory runs/mudlet-bridge
```

Import the bridge into the DD4 Mudlet profile and share its directory with the
Windows VM. See [the bridge guide](docs/mudlet-bridge.md). Telnet remains primary;
automated VM lifecycle and full visible HERO proof are unfinished gates.

## Development

Some source-integration tests require the public DD4 checkout. Once per clone:

```powershell
git clone https://github.com/fromage-fraser/dd4.git runs/dd4-source
```

Keep an existing checkout fresh with `git -C runs/dd4-source pull --ff-only`.

```powershell
python -m pytest -q
python -m pytest -q tests/test_damage_window_timing.py
python -m compileall -q dd4tester tests
```

Latest full offline verification: **5,756 tests pass**. The dedicated CLI
regression suite passes **69 tests**. Reconnect accounting
preserves verified XP decreases first observed after disconnection, without
double-counting or inventing their cause. Campaign startup now preserves
campaign-owned potion and source-resource ledgers when a raw live snapshot
omits those fields. Fresh source combat-budget evidence can reopen a previously
cleared Forest upgrade without erasing its crowd quarantine. Run 12984 recorded
that retry and withdrew at room 18027; the earlier checkpoint 40031 recorded
Kestrel at level 24 and 332,692 XP in healer room 3054. The latest focused Moria and locator
regressions also pass; the nine-endpoint fallback remains within the shared
24-step movement bound.

Run 13106 reached the source-validated Forest crowd gate and exposed a runner
acknowledgement bug: recall was sent from room 18027, but a lagging text-room
cursor made the policy report failure before the server response arrived. The
state-aware acknowledgement fix passed the full suite and live run 13107;
Kestrel received the Temple Of Midgaard response, recovered at healer 3054,
saved, and quit cleanly. The latest checkpoint is 40551 at level 24 and
331,521 XP; no progression XP is claimed by this recovery segment.

Run 12880 live-validated Aeloria's invisible carrier-search handoff, reaching
both carriers together, but duplicate-target handling prevented consideration.
Run 12881 then exercised the fix live: exact-instance consideration selected a
large hobgoblin, Aeloria gained 90 XP, ate its severed head, and returned full
to healer 3054. Run 12882 found the White Stag absent and returned safely with
no loss. Aeloria is now level 18 at 161,181 XP. This is the first positive
post-fix kill, not yet sustained progression or HERO. The
[contributor guide](AGENTS.md) defines coding, evidence, and local-only commit
rules. The [preserved README](docs/history/README_2026-09-08.md) retains earlier
details and run history; superseded defaults there are not the current
operating contract.

### Current Frontier: Kestrel (September 10, 2026)

Runs 12948-12953 followed the level-24 source frontier. The secretary target
exceeded the dagger damage budget, the Forest bear-claw route reached room
18027 and correctly withdrew from a live crowd, and the flight shop refused
service because fame is -12. Run 12959 then completed a below-band Midget
funding kill for 40 XP and 50 copper. Run 12960 cleared the recovered purse,
12961 sold its loot for a 2,878 copper-equivalent balance, and 12962 found the
watchman research route viable. Runs 12963-12965 safely exhausted the current
Moria sanctuary attempts. Reconnect run 12966 was interrupted and repaired;
runs 12967-12970 completed bounded food and recovery maintenance. Run 12971
used the widened nine-endpoint Moria fallback, killed source carrier 4055 for
100 below-band XP, and stored purple potion 4050 in the pouch. Runs 12972-12978
continued food and target probes safely. Run 12979 proved the pouch ledger is
preserved across a new live connection; run 12981 replenished food, while runs
12980 and 12982 reached current frontier targets and rejected them on source
damage bounds. Run 12984 reopened the Forest upgrade only after fresh source
damage evidence, reached room 18027, and withdrew when source-registered
mosquito and wasp instances formed a crowd. Run 12985 refreshed source-verified
food and the current DD4 source revision. Run 12986 reached the Solace
Secretary route through the exact `where drunk` locator, then withdrew before
combat because the loaded target's source HP ceiling exceeded the fixed
knife-toss budget. Run 13016 then completed the corrected sanctuary-reserve
handoff. Run 13018 reached the source Cyclops in Elemental Canyon. GMCP
reported 407 maximum HP, above the 318-point source combat budget, but the old
endpoint path still opened after sanctuary and withdrew only after the
aggressive target and an unapproved attacker were active; the net loss was
338 XP. The loss and live target evidence are retained, and the fixed endpoint
now passes the exact validated enemy records into the budget gate. Kestrel is
level 24 at 332,289 XP at checkpoint 40172, safely in healer room 3054. HERO
remains unproved.

The source-ranked chooser now requires a legal live HP probe whenever a plain
target's source HP range crosses the character ceiling. A current-band target
may use one sanctuary-protected GMCP damage-window probe only when its lower
HP bound fits the audited player output and its route passes the established
source locator contract. For a source-identified passive target, the live
runner may issue exact `consider`, consume sanctuary, and open combat before
the first `Char.Enemies` HP record exists; scripted, special, armed, and
uncertain targets remain excluded. The live ceiling still has to fit the fixed
source damage budget; no source estimate grants an unlimited fight.

When a same-level source target has one recorded HP-budget loss, a strictly
stronger audited loadout may reopen that exact mobile and room once. The retry
requires matching reboot, source revision, policy identity, observed GMCP HP,
and current-band route gates; the marker is consumed when the live segment
starts. A changed weapon cannot reopen a different target or turn an
over-budget target into general permission.

Use the source checkout refresh command above before source-sensitive planning;
do not treat a live observation or static source estimate as proof of a kill.
The current source mirror is up to date at `622d5de`, the affected campaign
suite passes **1,464 tests**, and offline selection still finds no Kestrel
target that passes all three filters at level 24. Live progression remains
unproved.

### Alignment Evidence Correction: September 11, 2026

The upstream source confirms that `Char.Worth.alignment` is accurate at level
10 and above; level 1-9 uses the deliberate wire mask `50000`. Live run
13036 captured alignment `1000` for Kestrel at level 24, so the transport was
not corrupt. The policy gate had instead applied the NPC target's alignment to
DD4's player-fight assistance rule. It now uses the player's revealed value:
`violence_update` blocks a good bystander only when both sides meet the exact
350 `IS_GOOD` threshold, while `spec_guard`'s separate assistance path uses
the 300 threshold. The raw GMCP value remains preserved for evidence, and
masked or invalid values fail closed.

### Cross-Class Continuation: September 11, 2026

The warrior Dorrik completed bounded flight preparation, then rotated through
the Sentinel and Abyss routes; both source-valid targets were absent and he
returned safely to healer room 3054. Serevian's thief weapon-repair route
completed without acquiring the missing bear claws after an unrelated field
combat caused a safe return. Astrevo's mage then killed the Circus Bearded
Lady for **140 XP**, survived, and checkpointed at level 8. That live run
exposed a classification error in which the source-defined hairy key was
treated as combat gear. Keys are now excluded from stance selection and are
removed if already worn; pouches remain supported. The next live gate is a
productive repeat for Astrevo or Serevian, followed by a level transition.
Astrevo's next New Ofcol attempt found a source-observed crowd at Gallow Hill
and withdrew without combat or loss, preserving the earlier XP gain.
Offline source work now exposes the legal infernalist `hellfire` and witch
`wither` damage paths through the shared estimator and timed spell contract;
this is executable coverage, not live subclass or HERO proof.

### Latest Live Evidence: Sanctuary Reserve Repair (September 11, 2026)

Policy revision 273 repaired a markerless checkpoint left by the previous
second-reserve handoff. Live run **13016** selected the corrected
`source-ranked-sanctuary-recovery-2-100` policy, reached source mobile 4055 in
Moria, and used the exact live target ID after a below-band `consider` result.
The kill was admitted only because one sanctuary reserve was missing: it
provided 110 XP and the second purple potion, which was placed in the pouch.
The character did not quaff either reserve, returned to healer room 3054,
slept, saved, and quit safely. Segment **12566** and checkpoint **40159** record
level 24, **332,627 XP**, two verified purple reserves, and no new death or XP
loss. This is recovery and source-required-loot evidence, not sustained
progression. The campaign tests pass **1,421**, the affected cross-module tests
pass **1,766**, and the full offline suite passes **5,515**; HERO remains
unproved.

### Latest Live Evidence: GMCP HP Budget Gate (September 11, 2026)

Run **13018** selected the exact source-ranked Cyclops revalidation at level 24.
GMCP identified mobile **9202** at **407/407 HP**, while the source-audited
thief output budget was **318 HP**. The run withdrew after the aggressive target
engaged and produced a net **-338 XP** result, with no death or kill; checkpoint
**40172** is safely at healer room **3054** with **332,289 XP**. The loss remains
in the current-reboot ledger and the target is closed for this level. The
endpoint implementation now passes its already-validated live enemy records
directly to the HP-budget check, and regression coverage protects that ordering.
The endpoint regression remains covered; the latest affected campaign,
starter, and progression suite passes **3,341 tests**. The full offline result
above predates the two newest regression cases.

### Latest Frontier Selection: Protected Level Ceiling (September 11, 2026)

The source-ranked selector now exposes Mr. Smithy (mobile **2413**, Stables
room **2406**) for Kestrel as a narrow level-ceiling probe. His nominal source
level is 25, but DD4 can load him through level 27; the source HP range is
**316-945**. The ordinary HP-fuzz helper still rejects this wider range. The
new path requires a source-safe sentinel, sanctuary, a fitted lower-bound
damage window, and a maximum live level of character level plus two. Before
sanctuary or the opener, the endpoint will compare the exact GMCP HP ceiling
with Kestrel's audited **318-point** budget and withdraw if it is too high.

Runs **13019-13028** preserved safe recovery and research evidence: food and
sanctuary maintenance succeeded, the Forest wandering bear route did not find
its required claws, Circus and Mirror Realm fame routes were too strong, New
Ofcol was absent during bounded search, and the live questmaster refused a new
quest while fame was negative. Kestrel remains level 24 in healer room 3054;
the next live step is now a new source-approved route, because the Mr. Smithy
probe is closed by its measured HP. The current carrier implementation and
verification counts are recorded in the frontier section below.

### Current Evidence Correction: Ground And Carrier Gear Routes (September 11, 2026)

Run **13029** is recorded as a failed protected probe, not a pending
experiment: passive Mr. Smithy loaded at **474/474 HP**, above Kestrel's
**318-point** thief output budget, and the retreat produced a real net
**-384 XP**. The loss is preserved in SQLite and the transcript; no kill or
death occurred. Runs **13030-13032** restored sanctuary and food state, and
Kestrel's current durable checkpoint is **40225** at **332,185 XP**. Dorrik's
run **13033** returned safely after one source-known below-band rolling-rock
maintenance kill for **150 XP**, with no objective kill.

The source equipment report now sends direct ground-reset objects through the
same route-safety audit used by food and resource stashes, and the campaign
can pair a source-carrier placement with an exact one-kill hunt candidate.
A reachable clean route is marked `promising`; closed doors, movement
requirements, aggressive or scripted mobiles, specials, and crowds remain in
hazards or autonomy rejections. Future, unreachable, or unranked mob drops
remain `source-only` and are never campaign permission. Carrier execution also
requires a fitting live HP budget and post-kill loot/equip verification. An
unresolved source template is unknown and is rejected by the target, transit,
city, and encounter gates rather than treated as neutral HP. The full offline
suite passes **5,543 tests**; the affected equipment, hunt, campaign, starter,
progression, and CLI suite passes **3,637 tests**. No live carrier hunt is
launched while the saved checkpoints remain blocked by recovery or funding.

### Latest Liveness Hardening: Public HERO API (September 12, 2026)

Historical evidence; the shared default was raised to 300 seconds on October 2.
At this checkpoint, the `hero` CLI and Python `run_hero_request` shared a
180-second live-segment default. A missing runtime cap is normalized to that
bounded value, and implicit reset waits remain disabled for bounded invocations;
larger runtime or reset budgets must be explicit. This makes library launchers
resumable and observable under the same contract as the CLI. The full offline
suite passes **5,590 tests**; this is a liveness improvement, not new live
progression or HERO proof.

### GMCP Alignment And Fame Inspection: September 14, 2026

The public `show-hunt-candidates` and `show-combat-readiness` commands now read
alignment from the nested GMCP `progress` snapshot used by `CharacterState`,
rather than looking only for a top-level field. They apply the same level-aware
rule as campaign admission: `50000` below level 10 is concealed, while a
level-10-or-higher value in DD4's `-1000..1000` range is authoritative. Kestrel's
real report now displays alignment **1000** and passes it into source candidate
ranking. The same reports now expose `character_fame` separately from
alignment, reading fame from nested GMCP `Char.Stats`; Kestrel's live value is
**-12**. This prevents the two independent DD4 reputation fields being treated
as one. Run **13255** confirmed the distinction during the Green Dragon probe:
the wire alignment remained **1000**, fame remained **-12**, and the target's
**576 HP** exceeded the **342-point** conservative output ceiling, so the bot
withdrew and lost **385 XP** without a kill. The exact policy is closed for this
boot; this evidence does not claim sustained progression or HERO proof.

### Protected HP Probe Admission: September 12, 2026

The source-ranked selector now surfaces a sanctuary-backed HP-fuzz probe when
the source lower bound fits the audited combat output, even if the loaded
upper bound does not. The readiness report exposes this as
`protected_hp_probe`; it does not relax the live GMCP HP gate. Run 13112
attempted the Tree Sprite frontier, but Magic Shop flight service refused
Kestrel's -12 fame. That remains useful funding evidence, not progression.
Runs 13113-13117 then completed bounded food and target checks; run 13117
reached Chaplain Jerrold at 416 HP and withdrew against the 318-point ceiling.
The campaign is now safely checkpointed at **40575** in healer room **3054**;
the latest resume opened no gameplay connection.

### Live Fallback Output Gate: September 12, 2026

The source-ranked selector now applies the fixed combat-output ceiling even
when protection recovery is using its tightly bounded no-reserve fallback.
This closes a live-state edge case where a known-disarm character could select
an armed target whose source HP ceiling exceeded the audited kill window.
Source-less policy fixtures retain their compatibility behavior; live states
must provide the source world and character class before this gate can be
applied. The campaign suite passes **1,464 tests** after the regression.

### Source-Backed Thief Upgrade Route: September 12, 2026

Source revision `622d5de` now registers a multi-step Thief equipment plan for
the next useful frontier. At level 26 or above, with a better piercing weapon
still needed, the campaign can source-audit buying lockpick object **38** from
Dave (mobile **3050**, room **3120**), practice `thief base` to 30% and `pick
lock` to 60%, then use the official Shadow Keep approach to unlock room
**16619** and target the exact smuggler mobile **16609** in room **16635**.
That mobile's equipped fine dagger is object **16614**. The source route costs
266 raw movement, or 74 while flying; `spec_thief` is admitted only with a
bounded exposed-coin loss and the existing sanctuary, HP, output, identity,
and healer-return gates. The complete route and practice chain are covered
offline, but live lockpick purchase, door entry, kill, and dagger acquisition
remain unproved. The full offline suite passes **5,645 tests**.

### Lockpick Funding Exception: September 13, 2026

At level 24 or above, a Thief who still needs the Shadow Keep lockpick can use
one source-audited maintenance route to fund it: Shargugh, mobile **6115**, in
room **6100**, carries iron ring object **6114** with a source value of 5,000
copper. The route is limited to 12 commands and 56 movement, retains the
`where drunk` preflight for its source `spec_drunk` hazard, and requires the
exact source mobile, room, object, HP, output, inventory, and safe-sale gates.
This below-band kill is a bounded funding objective, not progression XP; the
live reboot's sale price must still be verified before purchase.

### Moria Locator Recheck: September 13, 2026

Live run **13119** confirmed that DD4's `where` command reports visible target
names with room labels, but not room VNUMs. Moria's mobile **4055** wanders,
and several rooms share the label `The maze`; the runner therefore reached
source room **4063** after a positive locator result but found its room listing
empty. The locator now performs one bounded same-room `look` recheck when a
positive refresh has no movement path, then returns to normal exact-target and
`consider` gates. The run remains absence/recovery evidence with no kill, XP,
or HERO claim. The full offline suite passes **5,646 tests**.

### Moria Southern-Maze Locator Coverage: September 13, 2026

Run **13120** recorded Shargugh absent while funding Kestrel's future Shadow
Keep lockpick, and run **13121** positively located the Moria carrier but did
not acquire a purple potion. Source revision `622d5de` confirms that mobile
**4055** may wander through the reachable rooms **4063**, **4066**, and
**4065**, which all display as `The maze`; the western rooms **4057**, **4058**,
and **4062**, plus the aggressive branch at **4067**, remain excluded. The
deep locator now narrows to those three source rooms and preserves exact
visibility, identity, consider, hazard, and required-loot gates. Policy
revision **283** reopened only the prior same-boot, no-loss level-24 terminal
result, preserving its old attempt evidence. Live run **13124** then followed
the widened graph, killed source mobile **4055**, acquired the required purple
potion, and returned Kestrel safely to healer room **3054** for **100 XP**
without a death. Maintenance runs **13122** and **13123** acquired `some grain`
from Crystal rooms **10036** and **10038** without changing XP. Kestrel is
level 24 at **331,279 XP**. The full offline suite passes **5,648 tests**; HERO
proof remains outstanding.

### Lockpick Funding Shortfall Selection: September 13, 2026

The funding policy now remains executable when the progression layer selects a
lockpick shortfall but a generic source-frontier fallback would otherwise
replace it with an unavailable policy. Among candidates that already pass the
source, route, protection, movement, and saleability gates, a known currency
shortfall now prefers a carrier whose audited coins cover that shortfall over a
50-coin fallback. This is a ranking rule, not a safety override: the real
3,400-coin Solace carrier remains excluded because its route has multiple
attackers and no sanctuary reserve was available.

Live run **13125** exercised the repaired policy and killed the source Midget
for **40** below-band maintenance XP plus **50** copper, returning safely to
healer room **3054**. Runs **13126-13127** completed the next Circus and Mirror
Realm fame-recovery checks without XP change. Run **13128** then killed the
second permitted large-hobgoblin carrier, acquired the required purple potion,
and added **100** XP with a safe healer return. Kestrel is level 24 at
**331,419 XP**, checkpoint **40618**. Offline coverage passes **5,650 tests**
and compilation is clean; sustained progression and HERO proof remain open.

### Funding Handoff Repair And Live Guard Attempt: September 13, 2026

An excluded city-maintenance policy can no longer erase an active food, flight,
or Shadow Keep lockpick shortfall by falling through to a generic unavailable
frontier. The repair is limited to a fed, alive, non-combat checkpoint; the
source-safe funding selector still enforces identity, route, movement,
protection, output, saleability, and below-band rules. The full offline suite
passes **5,651 tests**, including the new checkpoint regression, and compilation
is clean.

Run **13132** completed the repaired handoff against patrolling guard mobile
**9400** in room **9400**, producing **90** below-band maintenance XP and **1
copper** of realized proceeds with no death or XP loss. Kestrel returned to
healer room **3054** at checkpoint **40633**, level 24 and **331,599 XP**. The
next policy correctly prioritizes a second purple sanctuary reserve before the
lockpick funding loop reopens. This is bounded maintenance evidence, not
sustained progression or HERO proof.

### Lockpick Shortfall Ahead Of Flight Retry: September 13, 2026

The campaign now gives an active Shadow Keep lockpick shortfall precedence over
a pending flight-purchase retry when the generic policy layer selects a flight
service handoff first. This keeps provision-funding executable while retaining
the existing healer, death, combat, route, protection, output, and source
candidate gates. The full offline suite passes **5,652 tests** and compilation
is clean.

Run **13133** completed the second permitted Moria carrier route, acquired the
second purple sanctuary reserve, and added **100** bounded maintenance XP with
a safe healer return. Runs **13134-13135** tested Circus and Mirror Realm fame
recovery; both ended as retryable source boundaries with no kill or XP change.
Kestrel is level 24 at **331,699 XP**, checkpoint **40642**, with **527 copper**
toward the **1,000-copper** lockpick. The current next policy is
`provision-funding`; sustained progression and HERO proof remain outstanding.

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

Run **13142** confirmed that the Magic Shop still refuses Kestrel at fame
**-12**, leaving the flight retry as a bounded service boundary. Run **13143**
then recovered a large hobgoblin's purple potion for **90** maintenance XP and
returned safely to healer room **3054**. The potion initially remained loose
in inventory, so the campaign selector now gives `audit-combat-pouch`
precedence over money-container cleanup and lockpick funding. Run **13144**
placed the potion in the worn pouch with no XP change, death, or loss;
checkpoint **40674** is level 24 at **332,149 XP** with one verified reserve
and **532 copper-equivalent**. The full offline suite passes **5,653 tests**;
sustained progression and HERO proof remain outstanding.

### Funding Fallback And Provenance Repair: September 13, 2026

Runs **13145** and **13147** recorded bounded no-change funding scans. Runs
**13146** and **13148** completed source-ranked Midget maintenance kills for
**40 XP** each. Run 13146 exposed missing source identity on an exact
below-band stop; the runner now retains the mobile VNUM and policy while
keeping the kill non-objective. The follow-up dispatch repair also prevents an
empty funding scan from falling through to a flight purchase while the
1,000-copper Shadow Keep lockpick shortfall is active. Kestrel is at checkpoint
**40724**, level 24, **332,229 XP**, healer room **3054**, no verified purple
reserve, and **639 copper-equivalent**. The full suite passes **5,656 tests**;
sustained progression and HERO proof remain outstanding.

### Protection Wait Liveness Repair: September 13, 2026

The reset-aware runner now defers the exact current-level, current-reboot
protection boundary when no sanctuary reserve or executable independent route
is available. A capped invocation remains blocked; a run with explicit reset
retries returns `awaiting_area_reset` without opening a gameplay segment, then
performs only the bounded world-time probe after its single configured wait.
The live proof waited 180 seconds, completed world-time run **13150** without
discovering a newer reboot, and returned to `provision-funding` without a
second flight attempt. Kestrel remains level 24 at checkpoint **40724** with
**639 copper-equivalent** toward the **1,000-copper** lockpick. The full suite
passes **5,656 tests**; this is liveness and evidence progress, not HERO proof.

### Liquidation Execution And Funding Follow-up: September 13, 2026

The campaign now derives emergency-provision sale mode from actual inventory:
a stale funding marker no longer creates a resupply detour when food is already
carried. Focused regressions and the full offline suite pass **5,659 tests**;
compilation is clean.

Live run **13154** sold 16 carried items through four safe Midgaard shops for
**305 copper**. Run **13155** completed a source-backed maintenance funding
kill for **40 XP** and **52 copper**, and run **13156** sold the residual purse
for **2 copper**. Kestrel is safely at checkpoint **40755**, level 24 with
**332,269 XP**, healer room **3054**, and **998 copper-equivalent**. The final
2-copper lockpick shortfall has no eligible current-reboot funding target, so
the campaign is waiting for fresh area-reset or source evidence. Run **13157**
performed the exact source preflight after one bounded reset wait; the carrier
was still absent, with no kill, loss, or XP change. No sustained HERO
progression or HERO proof is claimed.

### Route-Scoped City Quarantine And Mage Continuation: September 13, 2026

Field-city departure evidence now retains the exact policy that encountered the
bounded obstruction. A same-level, same-reboot retry blocks that policy, while
another source-ranked route receives its own route preflight; legacy evidence
without a policy ID remains globally conservative. Live run **13162** validated
the repair with Astrevo: the Circus route completed the exact Bearded Lady kill
for **108 objective XP** and returned to healer room **3054** at checkpoint
**40787**, with no death or XP loss. The earlier cross-module suite passed
**5,667 tests** at that earlier checkpoint; Astrevo remains level 8 and HERO
remains unproved.

### Route-Only Loss Revalidation: September 13, 2026

The campaign now distinguishes a pre-combat transit loss from a failed target
fight. When one exact same-level, same-reboot source hunt ended before target
engagement, with full recovery and only a source-labelled below-band transit
hazard, the selector may arm one fresh route-only revalidation. The candidate
must still pass source identity, current-band, output, movement, route-program,
and ordinary live gates. The marker is consumed before connection, cleared by
a productive target result, and closed by another failure; it never authorizes
general retries or counts incidental maintenance kills as progression.

Live runs **13168-13170** validated the repair for Astrevo. The first exact
route produced a current-band kill, the next segment repeated it for **226 XP**,
and the selector then rotated to another Circus target for a further positive
result. Follow-up runs **13171-13177** recorded bounded city, crowd, and
watchdog boundaries, and run **13178** stopped before connection while awaiting
an area reset. Checkpoint **40837** records level **8**, **31,068 XP**, a safe
return to healer room **3054**, no new loss, and no pending route marker. The campaign
suite passes **1,489 tests**; the level-10 trainer transition, sustained level
gain, and HERO proof remain open.

### Source Refresh And Special-Contract Audit: September 13, 2026

The source mirror was pulled to `80cad011b8c17b5ffc8828edae9182271bf7e46e`.
The refresh adds an explicit `AFF_MINDLESS` trait and confirms that mobile
specials are resolved from three weighted slots, including body/archetype
defaults and area `#SPECIALS` `M`, `N`, and `P` overrides. The source parser now
tracks nested C initializer braces, so weighted vectors no longer hide the
archetype XP field, and inherited template procedures are included in hazard
analysis. The refreshed source parses 4,138 mobiles and 1,629 effective
special-bearing mobiles; the full offline suite passes **5,692 tests**.
This is parser and evidence freshness work only; no new live progression or
HERO proof is claimed.

### Capacity Metadata And Route Rotation: September 13, 2026

Campaign startup now rebuilds pending sack, backpack, and girdle metadata from
chronological successful or ready segment results. A later explicit vault claim
removes that item from legacy recovery, so a claimed container is not restored
on every resume. An overweight capacity claim can receive one healer-side
equipment relief pass before one retry; the pass preserves recovery and does
not authorize unrelated loot.

The source-ranked selector also honors retry-exhausted, throughput-limited, and
current-reboot crowd evidence when considering its last-policy fallback. Run
**13190** live-proved the large-sack claim after lodging an obstructing object;
run **13191** banked the remaining coins; and startup recovered interrupted run
**13192** before selecting Moria. The latest boundary is safe at healer room
**3054**, level **8**, **31,513 XP**, checkpoint **40956**. Focused persistence
and selector coverage is included in the full offline result: **5,701 tests
pass**.

### Deep Moria Resume Cursor: September 14, 2026

The bounded runner now records a `campaign_fastwalk_resume_checkpoint` only
when a deep Moria route reaches a verified quiet waypoint. A same-boot retry
may rebuild the audited bridge to that waypoint and continue the unfinished
leg; stale boots, route hazards, combat, malformed cursors, and explicit
aborts force normal source-gated selection. The full offline suite passes
**5,770 tests** and compilation is clean.

Live run **13263** exercised the current sanctuary-reserve policy, found its
large hobgoblin absent at the audited 4064 endpoint, and returned Kestrel to
healer room **3054** without XP change, loss, or a reserve acquisition. This is
fresh absence evidence, not progression or HERO proof.

### Deep Moria Dispatcher Reconciliation: September 15, 2026

Policy revision **302** prevents an already-reconciled level-24 Moria recovery
from falling back to the generic one-room reserve executor. Live run **13275**
opened all **11** source-audited stops, including rooms **4064**, **4152**,
**4071**, and **4074**, then returned safely to healer **3054** without finding
the purple potion or changing XP, fame, or reserve state. The old terminal
result remains nested in the checkpoint for auditability.

### Text-Only Combat Engagement Guard: September 15, 2026

The observation parser now recognizes DD4 source aggression messages such as
“grunts as he takes a swing at you”, “grunts and swings at you”, and “takes a
swing at you as you enter” as combat-start evidence. This closes a live
ordering gap where a target could engage during the final route step before
GMCP `Char.Enemies` arrived; the runner could then incorrectly continue
familiar preparation. The full offline suite passes **5,808 tests** and
compilation is clean.

Live run **13320** exposed the gap against the level-10 small troll and
recorded two 50-XP losses; the kill was correctly excluded from progression.
After the parser repair, run **13321** stopped before a source-registered
Moria crowd with no combat or loss, and run **13322** killed Granny Jenkins
for **232 XP**. A bounded three-segment batch then added **196 XP** from two
gnome-woman kills. Astrevo is safely at checkpoint **41669**, level **9**,
with **33,387 XP**; HERO remains unproved.

### Six-Level Fame Rule And Level-9 Recovery Handoff: September 16, 2026

The source `HELP FAME` contract is now recorded explicitly: an ordinary fame
kill must be at least six levels above the player (`victim_level -
player_level > 5`). Famous mobiles and quests remain separate source-defined
routes. The source consumable selector also keeps a level-10 Moria sanctuary
carrier visible to a level-9 character, and the ordinary protection handoff
now selects the verified shallow Moria route below level 19; existing
level-16/17 blindness-special and level-19+ deep-route policies remain intact.

The full offline suite passes **5,810 tests** with clean compilation. Astrevo's
current bounded live checkpoint is **41690**, level **9**, at **33,691 XP** in
healer room **3054**; the current reboot exhausted its reset-wait budget, so
no new live segment is being replayed until a fresh reset boundary exists.
HERO remains unproved.

### Fresh Source Target Probability Guard: September 16, 2026

The generic ordinary-hunt selector now refuses a fresh autonomous target when
its source level fuzz has less than a 50% chance of landing in the useful XP
band. This prevents known lower-band candidates from consuming a full live
segment merely to be rejected by `consider`. Existing productive routes and
explicit familiar, invisibility, and revalidation probes retain their
narrower evidence gates. The complete campaign module passes **1,558 tests**;
the repository-wide HERO proof remains open.

### Flight Frontier Preference: September 16, 2026

When no flight affect is active, a fresh ground candidate may replace a fresh
flight candidate only when it has equal or better useful-band probability.
Productive ground evidence still wins immediately. This keeps long, useful
flight routes available for source-ranked progression instead of letting a
shorter but weaker target consume the segment.

### Runtime-Boundary Cleanup And Funding Evidence: September 20, 2026

The starter now gives a commandable, combat-free runtime-boundary return
priority over stale consider, equipment, and route-wait acknowledgements. This
keeps a bounded worker moving from a field room through recall and room 3001
to healer room **3054**, instead of turning safe cleanup into a false
`no policy decision` watchdog failure. The added regression is covered by the
full **1,435-test starter suite** and clean compilation.

Run **13446** preserved the original failure as historical evidence; run
**13447** proved the bounded return-home repair. Run **13448** then killed the
source-identified Midget for a required funding drop, yielding **30 XP** and
coins before saving at the healer. Run **13450** acquired Katrina the
Shepherd's source-required funding drop for **50 XP**. A later ordinary hunt
found Katrina present in room **2415**, but live `consider` rejected her as
below the useful band; run **13452** correctly recorded no attack, no loss, and
safe healer recovery at checkpoint **41988**, level **11**, with **51,828 XP**.
HERO 100 remains unproved.

### Familiar-Backed Hard-Health Revalidation: September 21, 2026

The source-ranked campaign now recognizes one narrow change in combat
capability: when a learned familiar is available, the exact same-boot target
that reached a hard health floor without an XP loss may receive one strict
familiar-backed revalidation. The existing source, route, output, target
identity, and live-consider gates still apply. The marker is consumed at
dispatch and closed after the segment, so an interruption or no-kill result
cannot create a retry loop. The full offline suite passes **5,878 tests**;
this is an executable liveness repair, not live HERO proof. Run **13629**
live-validated the path: the familiar was summoned and grouped, the Guardian
died for **607 XP**, and the character recalled and slept in healer room
**3054** with no death or XP loss. Checkpoint **42423** records
`completed_kill=true` and a succeeded, single-use revalidation marker. HERO
remains unproved.
