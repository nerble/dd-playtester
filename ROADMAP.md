# Autonomous Playtesting Roadmap

## Master Objective

Given only a source-legal race, cosmetic sex, base class, optional subclass,
name/personality, and credentials when resuming, create or resume a character
and autonomously reach the requested level, up to HERO 100. Preserve progress,
explain the experience, and support direct Telnet and visible Mudlet operation.

**Not complete:** no HERO character is proved. The highest actual frontier is
30 (Dorrik). Per the current focus instruction, breadth is deferred until one
character reaches HERO; Dorrik is the sole active progression track.
The [September 8 review](docs/APPROACH_REVIEW_2026-09-08.md) is the current work
order; dated run evidence belongs there, not in an expanding policy changelog.

### Current campaign status: October 7, 2026

Latest XP-first checkpoint: **49271**, healer **3054**, level **30**,
**614,804 XP**, **54,246 XP** to level 31, and **18 QP**. Optional quests are
shelved until a source-defined next-level shortfall becomes positive (the next
threshold is level 50). Runs **16440** and **16442** killed the exact Ki-Rin for
**1,147** and **1,409 net XP**, with no loss and safe healer returns. Their
whole-session rates were about **383** and **627 net XP/minute**. The unchanged
route received one recheck from fresh off-route city-locator evidence, then
its verified productive result survived a new process and ordinary selection.
The old city-closure ledger remains intact. Run **16441** did not acquire a
second pink ice ring; run **16443** found the Ki-Rin absent and returned safely.
The autonomous runner now admits the first bounded respawn wait for a newly
depleted, recently productive plain hunt even when the separate sanctuary
retry is spent. The existing finite wait budget and all live hunting gates
remain in force; failed fights and sanctuary attempts are not reopened.
Run **16444** revealed a separate capacity-selection bypass and repeated the
empty Moria supply visit without combat or XP change. That extra failed
attempt remains recorded; both capacity selection and exact Moria admission
now reject a spent sanctuary recheck. Checkpoint **49249** retained the
independent Ki-Rin wait with its cooldown reduced to two.
The already-running old supervisor also dispatched **16445**, which acquired
a purple potion and 90 resource XP. Do not discard those extra attempts.
Runs **16446/16447** returned without combat because loose-potion selection
stopped at an already-attempted healing keyword after making pouch space.
Selection now skips attempted and deliberately evicted keywords. **16448**
confirmed the subsequent purple-potion placement, collected both audited
treasury piles for **1,186 copper-equivalent**, and returned fully recovered;
the campaign funding objective is achieved, while the run's unrelated kill
objective correctly remains not achieved. No progression XP is claimed for
that maintenance visit. New packing replay cases are saved but unrun.

Run **16454** live-verified the **29-to-30 transition**: **1,017 net XP**, no
loss, observed sanctuary before the opener, and a fully recovered healer
checkpoint (**702/702 HP**). A fresh process loaded level 30 and selected
training with the new practices. **16455** accepted defense knowledge
(**64% to 65%**), recorded enhanced damage's rejection, and returned safely at
unchanged XP. The productive-history rebuild now uses the
already-loaded compact objective-kill ledger, so maintenance cannot erase
earlier source hunts outside the eight-row tail. A repaired missing sanctuary
prerequisite may restore a proven route's repeat admission and remove only its
soft rotation block; actual losses and live gates remain intact. Supply-carrier
XP no longer advances the ring cooldown. Run **16453**'s unsupported passive
armed-cleric probe is now excluded before travel, without weakening the runner.
The quest-reward/level-30/restart acceptance gate is proved. Next: complete
useful training and build sustained level-30 progression, not optional quests.

Runs **16436-16439** gained no XP and lost none.
Run **16436** attempted audited Gnome treasury funding but returned after a
scan incorrectly treated the drunk three rooms south as adjacent; the parser
now uses the reported distance, without clearing that route's saved failure.
Run **16437** withdrew 300 copper-equivalent from Dorrik's bank and bought six
pies, **16438** recovered at the healer, and **16439** bought and quaffed a
141-copper flight potion, positively confirming `fly`. The bank had ample
funds; carried coins alone did not describe his wealth. The selector now keeps
that affordable purchase ahead of protection rewrites and can retain already
audited, funding-only ground resources when the ordinary XP frontier is empty.
The new source-only passive-defense estimate does not reopen lost fights.
The phase index permits one exact old route record to be read without scanning
historical checkpoint JSON. Compilation and whitespace checks passed; new
focused cases remain unrun because October 7's daily test batch was already
used. HERO remains unproved; continue the productive current-band
path, not optional quest exploration.

#### Earlier October 7 Evidence

Dorrik remains at level **29**, **611,051 XP**, **2,849 XP** from level 30,
and **18 quest points**. Run **16423** finished safely without objective
completion after Goldmoon assigned a kill quest for Yellow Lord (mobile
**19018**). Source review found its only reset at room **19047**, but the
32-command route is blocked by the wandering `spec_thief` gardener (mobile
**19036**) and its reset-loaded clippers. Run **16424** received a 20-minute
buried-hoard quest for the Bowl of Zackera (object **77**) in room **1449**, The
Landing, Tower of Sorcery, then aborted safely at healer room **3054**. Its
source route crosses randomized Shadow Grove rooms and multiple aggressive
resets, so no field travel or digging was attempted. Run **16425** is connected
to Goldmoon and received the retrieve quest for the City's ancient scroll
(object **79**) in room **25530**, with a 30-minute countdown. The route is
blocked by the locked north gate at room **25429**; source requires key object
**25405**. The bot aborted at the healer before field travel and earned no XP or
QP. Run **16426** is the last saved checkpoint: healer room **3054**, no active
quest, and a live cooldown of **13 minutes** at the last observation. Its
worker was stopped deliberately for this route audit; reconnect and recheck the
timer before making any new decision. The exact source chain and its separate
underwater/combat blockers are documented in
`docs/QUEST_ROUTE_AUDIT_2026-10-07.md`. After the cooldown expired, run
**16427** received a different retrieve quest: the tattered codex (object
**589**) in room **10786**, White Lotus Temple, with a 15-minute countdown. Its
76-command shortest route crosses room **10005**, where the source allows a
crowd of up to 16 aggressive level-7 barracudas. A same-length detour avoids
them but crosses Temple Doors room **10706**, with two reset groups of level-30
`spec_guard` guards. An exhaustive source-graph check found no route avoiding
10706, even when also avoiding 10005 and Market Square 3014, so the assignment
remains closed under current hazard rules. Dorrik aborted at the healer, with
no field travel, XP loss, or QP. Run **16428** waited at healer **3054** for
the live cooldown, then requested once after a fresh zero. Goldmoon assigned a
12-minute kill quest for the level-33 mourner (mobile **2453**) in Ultima's
Graveyard, room **2558**. Although the target is unarmed and has no special,
the source route needs seven distinct moonstone keys across nine locked doors;
the exact source chain adds aggressive transit hazards. The bot aborted safely
at healer, no field travel, no XP loss, and no QP. The full route/key audit is
in `docs/QUEST_ROUTE_AUDIT_2026-10-07.md`. Run **16429** received a 29-minute
kill quest for White Mistress (mobile **1808**) in room **1830**, Little Haven,
and aborted at the healer after the source capacity/route audit rejected four
aggressive resets and wandering hazards. Run **16430** restocked. Run **16431**
received the Coin of Amaros retrieve quest in room **1425**, the Necromancer's
Lair, with 14 minutes; its 82-command route crosses randomized Shadow Grove
rooms and dangerous crowds, so it was safely aborted before travel. Both runs
gained no QP and lost no XP. Run **16432** most recently observed no active
quest and 13 minutes remaining at healer **3054** (03:49:16Z). The bounded
autonomous cycle had moved on to a fresh frontier check; that was the state at
the time of this checkpoint.

Current steering and frontier update (October 7, 2026, 5:47 PM NZST): runs
**16432** and **16433** each received a buried-hoard assignment (Bowl of Ambros,
object **587**, then the City's ancient scroll, object **79**). Both safely
aborted at the healer because trap-aware hoard execution is not connected to the
campaign; neither earned XP or QP. Run **16434** completed another optional
cooldown wait, and **16435** was recovered as interrupted at healer **3054**;
no new quest was requested. Dorrik remains level **29**, at **611,051 XP**, with
**18 QP** and source-derived next-level shortfall **0**. Per user direction,
optional requests and cooldown waits are now closed until a positive QP
shortfall blocks progression; the required-QP path remains available.
The XP-first selector found **3** current-band candidates, all requiring a
sanctuary reserve, and no unprotected candidate. The one post-area-reset Moria
sanctuary recheck is already spent on this boot. Campaign **7** is safely
checkpointed as blocked at level 29 pending a newly executable current-band
target or a source-valid way to restore protection and flight. Next work stays
on that progression gate, not quest exploration.
Run **16419**
completed the first fully evidenced quest round trip: after the prior cooldown
expired, Goldmoon assigned the retrieve quest for the tome of Orinth (object
**588**) in room **9904**, Yggdrasil. The source-checked 38-command route
avoided two special-bearing rooms. Dorrik picked up the exact tome, returned to
healer **3054** to recover movement, then reached Goldmoon (mobile **10001**) in
room **10024** and issued `quest complete`. The response confirms the hand-in
and awards **18 quest points and 45 gold**; GMCP confirms the quest is inactive,
`total_points=18`, and level-30 shortfall **0**. Run **16419** is recorded as
`objective=achieved`, `safety=safe`. Dorrik still needs the 2,849 XP; quest
completion did not itself advance him. Keep him as the sole pilot and resume
questing only when the next-level QP shortfall becomes positive. HERO remains
unproved.

The next request (run **16420**) assigned a buried-hoard quest for the City's
ancient scroll (object **79**) in room **935**, Olympus. It was not a loose
floor object: `quest.c` puts the exact quest token inside a buried
`ITEM_HOARD`. The runner stopped at its disabled hoard-execution gate and
aborted at healer room **3054** before going to the target. Offline source
review found the only room reset is Samuel the Armourer (VNUM **918**), a
level-30 aggressive sentinel with no special or program, source HP range
**420-1,280**, and **360** raw peak-round damage. The source physical approach
and return both cross his room, so this is not a route to force. Run **16420**
is `objective=not_achieved`, `safety=safe`, with no XP loss. The server set a
**15-minute** cooldown after the abort. Run
**16421** successfully restocked six pies and water. At cooldown expiry, run
**16422** requested again and Goldmoon assigned the buried-hoard quest for the
amulet of Thagg (object **76**) in room **27377**. Dorrik's source-valid spade
was already in inventory. Source inspection found the endpoint is a water
sector in the level-35-to-40 Sahuagin Residential area; the shortest route
crosses numerous combat hazards, and the hoard return planner rejects this
endpoint's water access. The bot recovered at healer room **3054**, issued
`quest abort` before field travel, and finished `objective=not_achieved`,
`safety=safe`, with XP **611,051** and no loss. The autonomous loop immediately
started run **16423**. This is a genuine route and hoard-execution gap, not a
missing spade; do not force this assignment. Do not classify run 16420's fixed
Samuel sentinel as a wandering miss or bypass its combat gate without a fresh,
bounded plan.

Quest points are a recurring progression gate, not a one-time level-30 hurdle:
the source-defined totals are **1** before level 30, **200** before 50, **500**
before 80, and **1,000** before HERO. Dorrik's 18 points clear the current gate
but leave a **182-point** shortfall before level 50. Shelve quests while the
next-level shortfall is zero; request on fresh timer-zero evidence when the
next actual QP gate blocks progression, and count only live-confirmed rewards.

Questmaster reward is part of the throughput calculation. `quest.c` adds 25%
to base quest points for questmasters above level 40, 50% above level 70, and a
further 25% for a Knight. Goldmoon (level 25) is the registered post-25 route;
the level-65 Mercenary Master route crosses a large aggressive crowd, while
Dahij (level 250) requires a route through randomized sea rooms. Do not switch
to a higher theoretical reward until its complete outbound, assignment, and
return routes pass the normal live gates.
For Dorrik's Knight bonus, Goldmoon yields 12-50 QP (mean **30.9**): about six
successful quests cover the level-50 shortfall, and about 32 successful
hand-ins at the same rate cover the remaining 982 QP to HERO. These counts
exclude failed or unavailable assignments and are not time estimates.

Turn-ins need not use the original giver: `quest.c` pays according to the
questmaster in the room when `quest complete` runs. Suturb (level 20) and
Goldmoon (level 25) are in the same reward tier, so current completion planning
uses Suturb's 7-command route rather than retracing Goldmoon's 48-command path.
The 25%/50% bonus routes remain unavailable until their hazards, flight needs,
randomized rooms, and complete return plans pass the normal gates. Questing at
an active QP blocker is an explicit throughput track: request on fresh timer-zero evidence, pursue
each source/live-executable assignment, and count only confirmed QP rewards.

Dorrik has no active quest and **18 total QP**. The source generator divides
requests among hoard, loose-object, and kill assignments, so the two consecutive
hoards are an unlucky draw; when QP blocks progression, keep requesting rather
than treating either abort as a permanent quest restriction. The live timer, not level or
boot, controls request frequency; campaign request history does not cap
requests. He already owns
the source-identified spade (VNUM **3393**, run **16162**), confirmed in live
inventory. That
spade is mechanically valid but slower than the optional Graveyard shovel
(VNUM **3604**); buying that upgrade is not a prerequisite. The campaign still
rejects hoard dispatch, so the software gap is trap handling and the connected
dig/return/pickup flow, not tool acquisition. The standalone excavator accounts
for three possible trap-charge commands and exposes a fresh recovery handoff,
but it is not connected to live digging, physical return, exact-object pickup,
or quest turn-in. Do not claim hoard capability until that bounded flow is
integrated and verified. On October 5, the shared quest-session owner gained
exact-assignment-gated dig-session start, poll, and trap-recovery methods; the
live runner does not call them yet. Their new cases are unrun under today's
regression limit.

DD4's `fight.c` completes a kill quest on the assigned mobile prototype VNUM,
not its narrative room hint. The quest planner now considers other source
resets for that same VNUM only when the existing source-safety admission
passes. Its focused regression is added but awaits the October 8 test window.
This does not change the earlier Book of Fretya route rejection or enable
hoard digging; those remain separate route and recovery gaps.

The DD4 source mirror advanced from `7e163cd` to `48cb5a6` on October 7. The
refreshed all-area parser loaded 13,052 rooms, 4,125 mobiles, and 6,138 objects.
The October 7 focused cooldown batch passed 3 tests. The older October 5 batch
reported 298 passed and 5 failures; follow-up fixes, including alternate-reset
kill-quest coverage and hoard-charge recovery, remain unverified. The live
retrieve round trip proves one quest path only; live kill and hoard completions
remain unproved. Defer another regression batch until October 8 local time.
HERO remains unproved.

The storage, state-ownership, outcome, incremental-summary, and experiment
foundations from the architecture review remain in the current worktree; keep
the work focused on Dorrik's current-band gates and durable resume evidence.

Run **16147** failed before issuing game commands because optional rearm
reporting dereferenced an absent policy adapter; that crash is fixed. Run
**16148** recovered its exact rearm marker from bounded checkpoint history,
but also exposed that two sanctuary-route attempts had vanished during an
unrelated merge and the Moria route reopened. The local fix carries these
frontier limits across unrelated segments and restores matching
same-level/same-boot records at startup, with separate handling for reset
rechecks and successful acquisitions. The restored counter was observed at
checkpoint **48823**; the new migration tests remain unrun. A fresh training
audit now bypasses historical practice-event reads, and healer recovery now
hands carried provisions ahead of movement-rest equipment work; the latter
has a focused test but awaits the next daily regression window. Continue with
a different executable current-band policy rather than repeating Sosivia or
waiting for a reboot.

#### Earlier October 4 evidence

Campaign checkpoint **48807** recorded the safe run **16140** return-home save.
Run **16139** failed the exact Dave-the-Dealer mace rearm because no source-safe
sweep was available within its 22-command limit, so Dorrik returned to healer
**3054** without fighting or gaining/losing XP. The segment was
`execution=failed`, `objective=unknown`, `safety=safe`. At that earlier point,
run **16140** was the latest verified save; run **16145** is current. A bounded same-frontier
marker now suppresses only this failed optional rearm route and expires when
level, boot, source revision, or primary weapon changes. Missing-primary and
thief-piercing gates remain mandatory. Continue with another eligible current-
band policy. The earlier instruction not to repeat a request absent reset
evidence reflected a mistaken campaign-side quota; DD4's live timer is the
request-frequency gate.
Dorrik remains the sole progression pilot until the first HERO. At that earlier
checkpoint, the DD4 source mirror was
`fbc5a5761af2f8a0734ca48df7993a4feffe55d2`; parser smoke covered 13,052 rooms,
4,125 mobiles, 6,138 objects, 1,622 special profiles, and 399 skill groups.
Runs **16108** and **16111** added no XP or QP. Goldmoon assigned a retrieve
hoard for amulet **586** in room **4521**, then bowl **587** in room **6355**.
Both routes were safely aborted because live digging still lacks trap recovery,
exact pickup, and verified physical return. Run **16111** ended at healer
**3054** with `execution=success`, `objective=not_achieved`, `safety=safe` and
no XP loss. Dorrik had no active quest. At that earlier checkpoint the recent
level-29 source-ranked search found no other candidate passing current gates.
No gameplay worker is active now.

Run **16116** completed a bounded trainer audit and returned safely to room
**3054**, but the teacher twice rejected enhanced-damage practice; no skill or
XP gain was observed. Its pre-change stored objective is `unknown`. Reports now
give future trainer runs an explicit skill-gain objective, so safe execution
cannot imply that a lesson succeeded.

Run **16117** returned safely to the healer after a bounded funding hunt. Its
run outcomes remain `interrupted` / `not_achieved` / `safe`; campaign segment
**3166** separately records the exact funding objective as achieved from source
mobile **10245** in room **10302** and **3,111 copper-equivalent** proceeds.
Recovery reconciled the unlinked run once and preserved its last observed finish
time. The run added **290 raw XP**, but neither kill receives progression credit.

An October 4 bounded resume incorrectly selected a required-QP cooldown wait
with **15 minutes** left. Orphan segment **3161** had no run ID or commands;
recovery closed it without changing checkpoint **48772**. A later selection
also chose `quest-request`; run **16114** recorded 53 commands but no quest
request in its transcript. Segment **3164** safely returned Dorrik to the
healer; checkpoint **48776** follows trainer segment **3165**. Campaign code
then incorrectly treated a previous request marker as a level/boot quota. That
restriction was removed October 5; DD4's fresh live timer and assignment state
now decide when another request is eligible. Updated focused cases await the
next permitted regression batch.

Run **16113** safely returned from a Moria sanctuary-supply preflight after 14
commands; it added no XP and incurred no loss. The route repeated the same
purple-potion requirement at 13 alternate reset rooms, and the capacity
preflight treated those alternatives as 13 required copies despite five free
slots. It attempted to drop and sacrifice a talisman, but the final inventory
still listed one; do not treat that slot relief as verified. The local fix now
uses the maximum explicit item quantity across route alternatives, preserving
per-stop quantity checks. A focused test was added but remains unrun.

The active milestone is one verified quest point, level 30, then a fresh-process
resume that re-observes both. While an active quest or positive live timer
closes requesting, keep advancing through eligible level-29 XP rather than
waiting idle. Once `nextquest` reaches zero, the next eligible selection may
request again. The latest Dwarven Home probe ended
safely at the live below-band check, while the next selector found no
executable policy under the current protection-recovery gate. Runs **16149-16150** add explicit evidence
that a safe return can still be an objective failure and an XP loss. Runs **16108**, **16111**, and **16113** confirm
that safe aborts do not count as objective completion; the same blocked route
must not be requested again without a new executable assignment. Experiment
**1** preserves checkpoint **48726**
and source audit `655fb82`; later `fbc5a57` runs are not a version-matched arm
for that record. Comparisons now pin tester/DD4 versions, test mode, source
revision, and objective. Continue current-band XP; do not repeat the consumed
quest request. The Yggdrasil assignment, blocked city-food street,
and hoard-digging paths remain closed under their source/live gates.

The default campaign report now aggregates compact kill rows in SQLite rather
than materializing the 1,593-row chronology. Campaign **7** reports **229**
target groups and has current-format summaries for **74/3,194** linked runs.
Overall coverage is **77/16,151** completed runs (**0.5%**).
Backfill that campaign with
`python -m dd4tester summarize-runs --campaign-id 7 --limit 25`, continuing
from the printed `--after-run-id` when older activity and outcome detail is
needed.
`show-campaign` now prints segment status, execution result, objective result,
and safety result separately.

Routine item acquisition and XP changes now remain in ordered events plus the
compact current-state row; full snapshots are reserved for initial state,
level transitions, identity/safety/quest boundaries, and run completion. Resume
reads prefer a newer current state than a stale checkpoint. The Oct 4 focused
test batch had **119 passed, 1 failed**; source confirmed the corrected
guardian damage expectation, which remains unrerun under the one-batch-per-day
rule. The new duplicate-route capacity regression is also pending that next
test window.

#### Earlier October 3 campaign evidence

The exact Dwarven Home bard policy is closed after a failed
damage-window probe cost **325 net XP**. He needs one QP before advancing. Runs
**16055-16057** safely rejected the crowded Secretary stop, then killed Sosivia
(**+1,867 XP**) and the Ki-Rin (**+1,137 XP**) for **3,004 useful XP**. Run
**16058** made a valid ordinary new-cycle request after observing inactive
quest status and zero cooldown; Goldmoon assigned the coin of Serenos (object
**585**, room **30263**). The bot safely aborted before digging because
trap-aware acquisition and return are not enabled. It recorded
`execution=success`, `objective=not_achieved`, `safety=safe`, with no XP or
quest points and a 15-minute cooldown. Run **16059** purchased and verified a light-blue potion at
the live shop price, then confirmed its fly effect. Run **16060** killed the
bard for **1,655 XP**, ate a severed leg, sacrificed the empty corpse, and
returned to the healer without XP loss. Run **16061** found the Captain's
Waiting Room crowded and safely withdrew without combat or XP. Run **16062**
found a fresh bard respawn at the same registered Dwarven Home stop; `consider`
said “The perfect match,” the stun opener landed, and the kill yielded **1,398
XP** plus an I.Q. Vine. Dorrik returned to the healer without XP loss. The old
campaign incorrectly treated frontier requests as limited per level and reboot;
that rule was removed October 5. Continue current-band XP while the live
cooldown is positive. Dorrik is alive
and checkpointed; no gameplay worker is running.

Run **16063** killed Sosivia for **1,595 XP** and recovered a talisman of hope.
The fight reached a **99/666 HP** trough before Dorrik recalled; he healed to
full at the Midgaard healer and incurred no XP loss. The old campaign request
quota was removed October 5; the live timer remains the cooldown gate. Continue
current-band XP while it is positive. Run **16064** killed a fresh
Dwarven Home bard for **1,456 XP** after a live easy-kill consider and successful
stun. Dorrik returned to healer room **3054**, recovered to full vitals, and
incurred no XP loss. Its cached run summary measures **207.78 seconds** whole
session: **32.99** productive combat, **40.01** travel, **87.73** maintenance,
and **47.05** waiting, about **420 net XP/minute**. Run **16065** accepted
Goldmoon's retrieve assignment for amulet **586** in room **9564**. Source
inspection found that the route requires the level-15+ bouncer transfer at
**9571**, then spiked key **9565** from Joan (mobile **9506**, level **35**) in
**9517**, with additional locked doors and hazards. That route is not registered
or executable; the assignment expired without XP or quest points. The quest
cooldown is now **12 minutes**. Run **16066** acquired the exact food-reserve
items (rabbit roast and timian herbs), returned to healer **3054**, and earned
no XP. Its corrected version-4 summary is `execution=success`,
`objective=achieved`, `safety=safe`. Run **16067** bought a light-blue potion
and confirmed flight. Run **16068** killed the Dwarven Home bard for **1,506
XP**, reached a **177/666 HP** low point, then recalled and slept at the healer;
it ended at **592 HP** without XP loss. Its 325.59-second session comprised
39.93 seconds combat, 39.49 travel, 208.20 maintenance, and 37.96 waiting
(about **278 net XP/minute**). The run summary records
`execution=ready`, `objective=achieved`, `safety=safe`; its 325.59-second
session wrote 13 full state snapshots. The 300-second cap note remains, but the
next resume linked run **16068** and recovered its outcomes at checkpoint
**48703**. Run **16069** verified safe return at full HP. Run **16070** accepted
the coin of Serenos (object **585**) in Forest room **18022**, then safely
aborted because the hoard route is disabled; it earned no QP and left a
15-minute quest cooldown. Source shows the target is runtime-generated, has no
static room reset, and sits west then north of Dwarven Home room **20500**;
Dorrik has no shovel and no active protection. Tool acquisition, exact live
approach, hoard/trap handling, and return are still unimplemented or unproved,
so keep the quest gate closed. Dorrik is level **29**, zero quest points, and
**2,971 XP** from level 30. Continue current-band XP during cooldown.

Run **16071** completed the bounded food-reserve route with
`execution=success`, `objective=achieved`, and `safety=safe`; the required grain
was present in inventory at completion. It made no XP or QP change and recorded
**10** full state snapshots over **101** commands. Treat its `success` as
completion of the food objective only, not campaign progression. The quest
timer fell **15 -> 12**. The final `Room.Info` was VNUM **3054** with the
healing flag; its display name “By the Temple Altar” had initially been
misread as recall. Dorrik was already at the healer, so no extra return was
needed. The first quest reward, level-30 transition, and restart/resume
continuity check remain open.

Follow-up run **16072** began from that same healer checkpoint, bought and
quaffed a light-blue potion, and returned to healer room **3054** before saving
and quitting. Its outcome is `execution=success`, `objective=unknown`,
`safety=safe`; it gained no XP. The route used **26 commands** and **6** full
state snapshots. Flight and the healer location are now live-observed; keep the
next campaign step bounded and focused on current-band progress.

Run **16073** completed the registered blackberries reserve at room **6023**.
The required exact object was acquired and returned to healer VNUM **3054**;
`execution=success`, `objective=achieved`, and `safety=safe`. It added no XP or
QP and recorded **8** full snapshots across **69** commands. The timer moved
from **12 to 11**. This protects supplies but does not advance the level-30
gate; resume current-band XP selection from this healed checkpoint.

Run **16074** was the last combat segment. It selected the Dwarven Home bard
(mobile 20509, room 20514); identity and consider passed, but the bounded damage
probe fell short and the encounter cost 325 net XP. Dorrik returned alive to
healer room 3054 at full HP. The outcomes are `execution=success`,
`objective=not_achieved`, `safety=loss`; the exact policy remains closed. The
190.62-second session measured 18.19 seconds combat, 53.12 travel, 73.73
maintenance, and 45.59 waiting, with 11 full checkpoints across 125 commands.
Checkpoint 48711 retains level 29, 610,604 XP, 3,296 XP to level 30, zero QP,
and quest cooldown 8.

Runs **16075-16077** are the newer noncombat outcomes. Run **16075** safely
reached the registered Solace Secretary endpoint and found no target. Run
**16076** restored full movement by sleeping at healer room **3054**. Run
**16077** did not leave the healer: the required live `where drunk` check found
wandering hazards on Main Street, inside the west gate, and in the weapon shop.
It saved checkpoint **48718** with full vitals and no loss. The exact hunt did
not start, so retain the obstruction as current navigation evidence and do not
replay the same route until a fresh locator changes it. The first QP reward,
level-30 transition, and restart/resume proof remain open.

Run **16078** was the last completed combat segment. The selector chose a young
sailor in Sea of Deception. A fresh consider said easy kill but healthier; the
bounded live probe observed **145/870** target damage and **69** received before
the player fled. DD4 recorded the 576-point flee penalty and 178 partial XP;
the session's net XP was **-398**. Dorrik was not killed and reached healer
**3054** at **666/666 HP**, with **3,694 XP** left to level 30 and the saved
quest timer at **1**. Close this exact target and retain the failed output
evidence. No quest reward or level transition occurred.

Runs **16079-16080** exercised the persisted quest path across two fresh
processes. Run **16079** observed the cooldown reach zero at the healer but
deferred the request with **170.3 seconds** remaining, below the controller's
180-second minimum for a quest route. It saved checkpoint **48722**; run
**16080** resumed and selected `quest-request` directly. Goldmoon assigned a
kill quest for yagnodemon **9906** in room **9913**. The source preflight found
multiple target resets, dangerous and assisting companions, an unsafe transit
special, and target special `spec_demon`; the bot aborted before combat and
returned to healer **3054**. Run 16080 ended `execution=success`,
`objective=not_achieved`, `safety=safe`, with no XP or QP change. Checkpoint
**48724** is healthy with cooldown **15**. The assigned target remains closed;
the verified QP reward and level-30 transition are still open.

Run **16031** also now reports `objective=not_achieved`: its terminal policy
state explicitly recorded that the required blackberries were not acquired.
The report includes that reason; the historical transcript and snapshots are
unchanged.

### Architecture Audit: October 4, 2026

The implementation is in the local checkout. The completed-run timeout
reconciliation compiled and was confirmed by Dorrik's live resume; its saved
integration test awaits a future regression batch.
The October 4 focused regression batch returned **119 passed, 1 failed**. DD4
source confirmed the corrected guardian damage expectation (**46/92**); the
assertion was fixed without rerunning. No further test batch or compile sweep
is allowed today. The architecture implementation now covers:

- Keep each ordered observation once in `events`; compact event indexes hold
  searchable fields and join back to canonical payloads. Old duplicate index
  rows remain readable; no 33-GB rewrite is attempted automatically.
- Use a bounded background SQLite writer, a compact current-state projection,
  and sparse evidence/recovery checkpoints. The writer coalesces state updates
  to one write per batch or barrier; queue and barrier waits time out. Run
  **16068**, **16071**, **16072**, **16073**, and **16074** logged 112, 101, 26,
  69, and 125 commands with 13, ten, six, eight, and 11 full state snapshots,
  not one full snapshot per observation.
- Keep item acquisitions in ordered events and a compact first-seen index rather
  than checkpointing the growing acquisition history. Routine XP changes update
  the current-state row; snapshots occur for initial state, level transitions,
  identity/safety/quest boundaries, and run completion. Resume/report reads use
  the current state when it is newer than the last checkpoint.
- Cache one completed report summary per run. Campaign reports aggregate those
  summaries and read only boundary states by default; historical segment detail
  is omitted. Pass `--full-history` to `campaign-report` to include it. Reports
  read compact campaign/run links and fetch cached summaries, avoiding a
  campaign-wide grouping query. `backfill-campaign-runs` materializes legacy
  links in resumable pages of at most 256 segments; `summarize-runs` separately
  backfills completed run summaries. Campaign 7's historical links were
  backfilled in 12 pages. The trigger-maintained table now contains 3,126 run
  links through segment sequence 3,129; its standard 3,126-run/1,588-kill JSON
  report rendered in 9.01 seconds with segment detail left out. No historical
  event or snapshot payloads were rewritten.
- Persist execution, objective, and safety outcomes separately, and estimate
  combat, travel, maintenance, and waiting across each whole session.
  Objective completion must come from the recorded contract and positive
  evidence, never from a successful/safe stop or a stale stored claim. Required
  items need distinct acquired entries; quest reward and level-transition gates
  are independently testable. Explicit terminal missing-item evidence forces
  `not_achieved` and is shown in reports, correcting run 16031. Summary version
  6 rebuilds older run summaries. Previous versions retain cached metrics,
  but an unverified positive objective becomes `unknown` until refreshed.
- A campaign segment linked to a current run summary inherits its execution,
  objective, and safety outcomes by default. A distinct campaign objective may
  override only the objective field when its named evidence contract is
  satisfied; run execution and safety remain inherited. Level or quest-point
  changes alone cannot turn an unrelated or failed item objective into an
  achievement.
- Outer-timeout handling distinguishes a genuinely running/interrupted worker
  from a run already finished as `ready` or `success`. A completed run keeps
  its status and cap diagnostic, links its cached summary to the segment, and
  restores a resumable campaign checkpoint only when its observed end state is
  neither dead nor in Purgatory.
- Keep `LiveSessionState` as the shared snapshot owner. Typed combat, travel,
  recovery, and quest controllers own their active mutable state; the policy's
  existing field interface delegates selected combat flags, route cursors, and
  recovery actions to them. New quest phases get fresh route-local controllers;
  `QuestHandoffState` transfers only validated character/progression continuity.
  Historical repair stays in `campaign_migrations.py`; continue focused
  extraction instead of a broad `StarterPolicy` rewrite.
- Record controlled experiment arms with tester/DD4/source versions, a complete
  start snapshot plus boot ID, objective, linked run/campaign, shared metrics,
  and separate bot-error/game-defect attribution for source-informed and
  ordinary-player modes. A comparison key pins DD4 version and objective;
  variants retain their own starting state and completed arms are immutable.
  `experiment start --checkpoint-id N` captures an exact saved boundary,
  infers its campaign, and records checkpoint provenance without manual export.
  `experiment compare --comparison KEY` now summarizes per-variant full-session
  metrics and bot/game attribution, while flagging mismatched conditions,
  objectives, or world baselines and printing each arm's character/build start
  profile instead of implying a controlled result.
- When a required next-level QP is missing by one point and the recovered,
  supplied healer has exactly one live cooldown tick remaining, retain the
  bounded connected quest wait instead of opening another source-ranked probe.
  A stale/no-progress wait still falls through to normal source selection. Runs
  **16079-16080** verified this wait, saved zero-cooldown checkpoint, and fresh
  process resume into the request phase.
- The prior checkpoint **48779** followed runs **16108**, **16111**, **16113**,
  **16114**, **16115**, **16116**, and **16117**. The first six earned no XP or
  QP. Run **16117** added 290 raw XP and 3,111 copper-equivalent in a
  funding-only hunt; neither kill received progression credit. Its run outcome
  is `interrupted` / `not_achieved` / `safe`, while segment **3166** records the
  exact funding objective as achieved. The two Goldmoon retrieve assignments were buried
  hoards (objects **586** and **587**) and were safely aborted because trap
  recovery, exact pickup, and physical return are not live-authorized. Run
  **16113** safely returned from Moria's sanctuary-supply preflight after the
  duplicate-reset capacity bug; its fix and focused test await regression.
  Trainer segment **3165** safely returned from Kerofk but could not teach
  enhanced damage; no skill gain occurred. Future training runs compare
  observed skill listings so execution success cannot imply lesson success.
  Dorrik then completed run **16124** for **1,198 XP**, banked excess coins in
  **16125**, and ended run **16126** at Road Crossing **3120** after the old
  watchdog stall. Runs **16127-16129** returned him to the healer, liquidated
  some loot, and confirmed the new finite shopkeeper-absence exit. Checkpoint
  **48797** is alive at healer **3054**, **2,669 XP** from level 30. Campaign 7
  remains failed because the mace purchase was not achieved. Dorrik has zero
  QP, one point short. The persisted request marker is historical only. At that
  checkpoint, the source parser was at revision
  `fbc5a5761af2f8a0734ca48df7993a4feffe55d2`.

Next progression gate: earn one verified quest point, cross level **30**, then
restart and resume once to verify evidence continuity. Scripted criteria cover
the positive quest-point delta, level 30, and persistence across a storage
reopen; live completion remains unproved. The level-29 assignments in runs
**16058**, **16065**, and **16080** remain closed under their route/safety
gates. Runs **16108** and **16111** add two more safely rejected hoards, not
rewards. Do not mistake a request or safe abort for completion, or reopen a
rejected route from offline source evidence alone. The current checkpoint is
**48797**, level **29**, **611,231 XP**, **2,669** to level 30, at healer **3054**,
zero QP, with quest cooldown **0**; another request is eligible after fresh
status and ordinary fame/readiness checks. Campaign request history is not a
limiter.
Experiment
**1** deliberately retains checkpoint **48726** as its exact starting state;
the later actions remain part of the same campaign but not its baseline.
It requires a verified positive QP delta, level 30, and a later process
observing both after resume. Continue current-band XP during cooldown; request a
quest only through the normal live gates. Request history does not impose a
per-level or per-reboot cap.

#### Recent Verified Progression Interval

Runs **16003-16011** gained **5,948 net XP** from five kills over **24.07 minutes**
(about **247 XP/minute**), including all intervening maintenance, recovery,
development gaps, and two quest requests. There was no XP loss. The replacement
Smithy was positively below-band and left alone. Goldmoon had no assignment
on the first request; the second hoard in room **20339** was recognised and
aborted. The latest checkpoint has **470/482 movement**, **1,069 copper-equivalent**,
quest cooldown **15**, the branch equipped, and zero QP.

The swiftness double-count is corrected and documented. Excavation now has a
source walking-return planner with door preparation, safe detours, all-exit
escape branches, and a finite worst-branch movement reserve. It is not yet a
live capability. Next implementation must join the dig controller to guardian
damage/carrying-capacity admission and verified recovery/pickup, then validate
replays in the next daily test batch. Keep current-band hunts moving meanwhile.

Runs **15990-15998** gained **3,653 net XP / 20.72 minutes**, about **176 XP/minute**
including maintenance. The last three hunts delivered that XP without loss in
**9.55 minutes** (about **382 XP/minute**). The branch remained equipped through
combat, recovery and reconnect. Food and **1,240 copper-equivalent** were
collected, flight cost **141 copper**, and the sanctuary carrier was unavailable.
That earlier checkpoint had **1,150 copper-equivalent**, **444/482 movement**,
quest cooldown **3**, and still no QP.

The hoard budget and response-driven dig controller are implemented and compile,
but remain outside live dispatch. Finish visible physical-return/guardian escape
admission, exact tool observations, recovery and pickup integration, and saved
replay verification before enabling them. Keep ordinary XP/quest work moving;
do not wait solely for this feature or count an aborted hoard as quest progress.

Runs **15982-15986** earned **757 net XP** in **13.39 elapsed minutes** after
one **1,711-XP** Sosivia kill and **954 XP** in two withdrawals. No QP was
earned; Gorak's locked route needs unsupported keys. The low-level guard
bystander defect has a saved correction and replay, compiled but unrun and
not live-proved. Existing loss exclusions remain closed.

Run **15989** restored branch **6104**, verified by the server, and logged out
at the healer. Recovery weapon retention is now live-proved by the later hunts;
the separate same-session removed-item identity path remains unexercised live.
The comparison parser and failed-audit persistence are repaired; the old exact
three-command failure was recovered from bounded evidence, not discarded.
Run **15988** nevertheless lost **466 XP** while still using the club; preserve
that closure. Runs **15982-15989** netted just **291 XP / 54.65 minutes** including
development, about **5 XP/minute**. Maintenance success is not progression.

Next: sustain current-band kills and earn the first quest point.
Branch **6104** earned a bard kill in **15981**, but recovery in **15985**
replaced it with club **1521** and the next hunt retained the club. Latest
health is **660/666** and movement is **444/482**. Pursue current-band XP and the first
executable quest. Do not substitute more
wait-only loops or higher-band research. Hoard source auditing is saved in
`docs/QUEST_HOARD_AUDIT_2026-10-03.md`; trap-aware dispatch is still absent.

The October 3 focused batch had **148 passes and 27 failures**. Corrected the
comparison fixture (25 failures) and required an observed positive quest active
flag for new-cycle evidence (two failures). These corrections are not rerun
today. Small-purse pickpocket transit passed its offline cases; its actual-source
Yggdrasil route is analyzed, but live retrieval and reward proof remain outstanding.
The city-repeat recheck cases are saved and compiled, not run after that batch.
Source **6941814** parsed successfully after the latest fast-forward pull;
new Bard/Cleric/Knight abilities do not expand Dorrik's authorized actions.

#### Earlier October 2 Evidence

Runs **15954-15958** added **1,051 net XP** from Mr. Smithy, about **53 net
XP/minute** across the full **19.78-minute** interval including development,
maintenance, reset waiting, and unsuccessful trips. **15958** confirmed a new
quest wait progressed **12 -> 11** and returned a full-health, full-movement
checkpoint. The first QP is still missing. The bounded theft-exposure change
is now implemented, but does not globally whitelist the special or resume the
abandoned Yggdrasil assignment. Preserve the new
same-connection equipment identity fix; its live handoff proof is still pending,
and the old club was equipped at that checkpoint.

Through run **15938**, the evening continuation gained **10,334 net XP**. The exact
inventory-footer repair is now live-proved: run **15920** consumed the potion,
completed the 80-step trainer route, gained three lessons, and recovered at
the healer. Enhanced damage is **67%**, defense knowledge **63%**, and parry
**62%**. Continue current-band XP and complete an eligible quest; do not confuse
one successful teacher visit with proof of sustained progression or HERO.

Runs **15932-15938** added **1,218 net XP** without loss, about **88 XP/minute**
over the whole 13.91-minute interval. Food, sales, an absent target, quest
rejection, and ground-gear acquisition are included. That interval equipped
level-15 grey branch **6104**, whose combat benefit remains unmeasured.
The shared live-segment default is 300 seconds after the old 180-second cap
forced an early withdrawal. A source-backed already-fighting `kill` reply now
clears only its unnecessary command wait. Saved regression cases remain unrun;
live proof of that exact refusal path is still pending.

Runs **15939-15945** produced no XP. Exact structured weapon identity now ends
the false missing-stun-weapon loop and informs upgrade ranking. However, the
intervening ground pickup equipped a weaker level-3 club **1521**. Run **15946**
has now restored branch **6104** through a fresh server comparison, wield, and
exact equipment audit at the healer. This adds no XP or combat proof. Next:
measure current-band combat and command timing while pursuing the first quest
point. Shared item names alone must never identify a carried weapon.
The next two funding runs (**15947-15948**) yielded no XP or money: city
obstruction first, then an absent Circus carrier. Checkpoint **48451** retains
the restored weapon, full health/movement, and two quest-cooldown ticks. Keep
that absence evidence and pursue another executable current-band objective.

**Supplies/quest handoff repair:** run **15950** bought and activated flight
for 141 copper; **15952** bought six pies for 174. These remove real maintenance
selection loops without clearing combat history. **15951** completed a
connected cooldown and requested a quest, but its trapped-hoard assignment was
aborted, with no QP. Mandatory next-level QP waits now survive an already-used
optional request and preserve completed-cycle evidence through maintenance.
The next proof remains a completed quest and productive current-band XP, not
another maintenance success. Tests are saved, compiled, and unrun today.
Run **15953** advanced the live quest cooldown from **6 to 4**, then ended
normally at its 300-second cap. Dorrik remains fully recovered at the healer
with five pies, no additional XP, and no QP. The saved primary is now club
**1521**; reconcile that current equipment evidence before claiming branch
**6104** remains equipped. Do not count connected waiting as progression.

Keep pursuing an executable quest. Run **15937**'s TenTusks retrieval
was aborted at the source gate requiring key **25405**; the source produces and
destroys that key in a stone-head gift program, so there is no ordinary key
purchase to automate. Do not retry the abandoned quest or dispatch an
analysis-only route. Quest access remains a concrete level-30 blocker.

Runs **15903-15908** gained **3,609 net XP** over **13.77 wall-clock minutes**,
including maintenance and one failed hunt. Continue useful hunts through quest
cooldowns, pursue an executable assigned quest, and validate the level-30
training/subclass transition when reached.

Run **15903** exposed an object-quest distinction missing from the wire protocol:
hoards and loose retrievals both use `type=retrieve`. Request-scoped narrative
binding now records the distinction without replacing GMCP identity. Source
`quest.c` and `trap.c` show up to three trap charges, curses, hexes, and spirit
guardians; the former blind dig loop is removed. Implement and verify a bounded
trap-aware hoard executor before enabling that quest subtype. Loose retrievals
and eligible kill quests remain the immediate quest-point path.

New quest cases are saved and compilation passes; no second October 2 pytest
batch was run. HERO and autonomous hoard acquisition remain unproved.

#### Earlier September 30 run notes

Dorrik is at checkpoint **47958**, level **27**, with **479,215 XP** and
**23,735 XP** to level 28. He is safely at healer **3054** with **617/617 HP**
and **461/462 movement**. He remains the only active progression character;
HERO is unproved. Since checkpoint **47903** he completed seventeen productive
hunts for **20,781 XP**, without another XP loss. The latest productive runs
were **15694** (+993, Mr. Smithy), **15698** (+1,668, Ki-Rin), **15699**
(+1,240, Mr. Smithy), **15700** (+1,226, Ki-Rin), **15702** (+908, Mr. Smithy),
and **15703** (+2,452, young sailor). Run **15692** found the Dwarven Home host
below-band on live consider and earned no XP; that exact reset was closed for
this boot. Run **15697** also earned no XP, while its later fresh attempt reached
a productive sailor stop. Ki-Rin fights used ochre healing potions; Dorrik ate a
severed head, and later loot was stowed in his pouch. On **15684** a Goblin
Sentry's Sword zapped him and fell; the transcript confirms he rearmed with his
hammer before leaving the area.

Funding route **15705** live-proved the exact Gnome treasury trip: Dorrik took
two coin piles and returned safely to the healer with no XP loss. The live
breakdown was **6 gold, 40 silver, 55 copper**, plus **4 silver and 100 copper**;
that is **1,195 copper-equivalent**, below the source's nominal 1,240. DD4's
`db.c` fuzzes each denomination above ten independently by +/-10% unless
`ITEM_DONOT_RANDOMISE` is set. The funding admission now compares against the
source-derived 1,175 guaranteed floor. Run **15706** then bought and quaffed a
light-blue potion, with the flight affect confirmed live. Funding and purchase
are maintenance proof, not progression XP.

Food trip **15681** reached the Hermit's hut despite the city drunks, acquired a
rabbit roast and black gyvel, and returned safely. The previously failing pouch
audit is now bounded by the complete server prompt when its layout is not
recognized; **15681** confirmed the listed contents and stowed an ochre potion.
The Wabbit trip earned no XP. Loot sale **15683** remains blocked after three
checks found the wandering drunk, so the horseshoes are still unsold. Flight
purchase **15685** was maintenance only.

Run **15670** still records the earlier **493 XP** loss against Shudde-M'ell:
its aggressive mobile loaded at level 22, exactly the unsafe useful-XP floor.
Candidate construction and legacy admission now require an aggressive target's
minimum fuzzed level to be strictly above that floor. The focused cutoff tests
are saved but remain unrun; September 30's one regression batch was already
used, and a fresh live check of that exact target remains pending. The Discord
relay's missing user post was a missing `USER` record in its file source. That
turn and new assistant comments are now being delivered once; the single
`--new-only` worker remains alive with an empty queue and its cursor at the file
end. The latest user message and current commentary were confirmed in its
delivery log. HERO remains unproved.

### Prior roster status: September 29, 2026

Dorrik is at checkpoint **47486**, level **26**, with **451,577 XP** and
**2,023 XP** to level 27, safely recovered at healer room **3054**. Run **15541**
killed Mr. Smithy for **1,244 XP** without loss. Mirror Realm run **15540**
confirmed the shared guardian population in room **19031**, not the later reset
room **19041**. Runs **15543-15544** exposed a moving-drunk race between the
healer and recall: a fresh second location set blocked the route after the
first detour. One bounded changed-input correction is implemented and syntax
checked; its focused test is saved but not run, and live proof is pending. The
sanctuary recheck is now spent for this boot, so Dorrik has no executable hunt.

Fenanallor is at checkpoint **47509**, level **8**, with **29,306 XP** and
**2,394 XP** to level 9. Run **15551** earned **141 XP** from the level-8
Illusionist. The huckster failed live consider; Moria orc run **15552** found
only wandering locations outside the source-safe relocation graph. Aeloria is
at **47493**, level **18**, **162,145 XP**; the watchman failed live consider,
and her Moria reserve search found no carrier. Kestrel remains level **24**,
**329,125 XP**, fame **-12**, with the sanctuary recheck spent. Ararisa is level
**11**, **49,524 XP**; run **15553** stopped before room 3014 on the source-known
drunk. Serevian's level-11 frontier is empty for this boot. Astrevo's Moria orc
run **15554** confirmed the same unsafe relocation problem and earned no XP.
No progress is credited for blocked routes, research, or empty funding checks.
Today's regression allowance had already been used; only compilation and
whitespace checks ran after that, with no additional pytest batch.

An earlier live event was Aeloria's post-reset sanctuary attempt **15536**:
the server accepted the connection but sent no login greeting within the
bounded retries. It issued zero game commands and earned no XP. The latest
checkpoint is **47468**, level **18**, at healer **3054**. A no-greeting,
zero-command failure now leaves this one-shot check pending for a later explicit
invocation, without another area-reset wait. Implementation and a focused test
are saved; only a syntax check has run because today's single test batch is
spent. The new behavior is not yet test-suite or live verified.
The all-area level-18 source scan also returned no autonomous-safe XP stop for
Aeloria; the remaining candidates still carry source route, crowd, protection,
or combat-output blockers.

At the earlier roster checkpoint **47413**, Dorrik was level **26**, **450,253 XP**, **3,347** to 27,
**594/594 HP**, healer **3054**. Secretary **15505** earned **1,113 XP**;
**15506** failed two flees and recalled at a cost of **455 XP**, leaving
**658 net XP**. The quest departure and same-boot time probe added no XP.
Preserve that combat loss, the singer loss, and the failed Willow probe.
Kestrel's food reserve was replenished in **15501**;
his following hunt was city-blocked, leaving **24**, **329,125 XP** (**47348**).
Ararisa is **11**, **49,524 XP** (**47429**); Fenanallor is **8**,
**29,054 XP**, **2,646** to level 9, full healer HP (**47400**). His three
productive hunts earned **331 XP**, offset by **42 net XP** lost against the
strongman; flight attempts and the absent funding target added no XP.
No character levelled.
The earlier **15519-15526** block gained **191 net XP** in **716.00 connected
seconds**, **16.0 net XP/minute**. Across **15478-15526**, **6,134 net XP** in
**4,660.48 connected seconds** gives **79.0 net XP/minute**, including all
unsuccessful and maintenance trips. These exclude off-game costs, including
the latest **180-second** area-reset wait, and are not whole-session rates.
The final training and Circus funding trips added no XP. Funding **15518**
encountered a wandering route hazard; checkpoint **47400** preserves its block.
The subsequent supply route **15522** acquired invisibility elixir **9231** for
**188 copper** and returned Dorrik fully healed with **645 copper**. Ordinary
campaign selection, source-safe travel, live quoting, exact purchase, inventory
confirmation, and durable one-attempt accounting are live-observed. The prior
**15521** cap refusal is retained; its one-time budget repair is spent.
The separately registered potion activation and advanced teacher journey is
implemented with fresh effects, exact exits, remaining movement, expiration
recovery, and useful source-capable lessons. Next proof: complete that visit
through ordinary campaign selection, then measure better current-band combat.
Only this noncombat executor has equipment-aware invisibility permission.
Do not repeat the purchase or count maintenance as XP. Saved checks are unrun.
Teacher attempts **15523/15524** stopped before consumption; targeting setup,
request-local replies, and source-unique keyword selection for saved zero-ID
objects are now implemented, still unproved live. The same-boot retry is spent.
The funding handoff now preserves bounded source-capacity admission and may
select another registered activity after a fresh empty ground search without
first spending unused ground attempts. Keep the same counters, source hazards,
live crowd/consider gates, and shared quest-request budget. Saved checks remain
unrun under the daily limit; measure useful XP after this selection repair.
Runs **15525-15526** reached live Moria hunts, found the wandering targets,
and rejected their below-band considers. They gained **zero XP** in **189.67
connected seconds** and returned fully recovered. Selection is unblocked;
throughput is not improved. Next work rotates to a distinct route or character,
preserving these observations. No additional regression batch ran.
Ararisa and Kestrel then stopped at funding/protection selection without a
connection. This work unit earned no XP. Continue removing these current-roster
supply/training blockers, not extending coverage above actual character levels.
All workers finished; no project Python worker remained in the process audit.
No additional regression batch was run. Continue current-band progression,
retain the failed fight, and prove the new maze/prompt handling without clearing
existing cooldowns. Do not count ready statuses or safe returns as XP progress.
The route-program retry now finishes healer recovery and clears only its
completed emergency return before a fresh lookup; its new checks remain unrun.
Saved run **15326** revealed that the one-time city detour lengthened Dorrik's
route without shifting the later Shadow Grove navigation indexes, so maze
navigation began in Haon Dor and returned safely. The detour now rebases both
indexes by its exact command-count change. The focused case is saved but awaits
the next daily test allowance. Its exact same-boot, no-contact failure can now
be reopened once when source route evidence confirms the old index mismatch;
that revalidation is syntax-checked only and the route and useful XP remain
unproved.
Run **15538** exposed a separate city-greeter handoff: the first location set
had no source-safe detour, and that failed calculation consumed the one-shot
flag before the wandering drunk moved. A later fresh set had a safe detour and
ample movement, but the route was abandoned before departure. The recheck now
keeps its allowance until a detour is actually applied, within the existing
three healer waits. The focused check is saved but unrun under today's test
limit; live route and XP remain unproved.
The gear audit confirmed that Dorrik's pre-level swaps sacrifice four damroll.
A source-backed one-kill planning window now keeps combat equipment longer for
plain single-target hunts, with the original rule retained for unknown or
complex fights. **15504** recorded a **4,374-XP** window, but improved gear timing
and throughput remain unproved. Saved checks are unrun. Continue useful current-
band hunts and address weak accuracy and the saved training-route obstruction;
do not replay failed fights unchanged or start another regression batch today.
One bounded local-teacher recheck is now implemented for a proven unspent visit
followed by a productive hunt with changed, clear city-locator evidence. Its
marker is consumed before launch, and a fresh live check remains mandatory.
Next proof is an accepted useful lesson, not merely another healer return.
Saved negative cases remain unrun under the daily regression limit.
The recheck can also follow a later automatic world-time probe after a five-
minute cooldown, sharing the same once-only allowance. A targeted metadata
lookup retrieves the blocked visit when it is older than the eight-row runtime
tail. **15517** live-proved that handoff, but its fresh Main Street hazard check
still blocked departure. No lesson or XP gain is claimed; the retry is spent.
The one-kill Moria return in **15509** exposed a disabled post-kill locator.
Ordinary, plain wandering targets can now continue within the already registered
kill/search limits using fresh locations and isolated encounters. Resource and
protected probes remain excluded. Next proof: more useful kills in one normal
trip, measured through recovery; saved checks remain unrun.
Moria **15515** still returned after one kill because its earlier poisonous
bystander warning remained active. Preserve it; the new continuation must not
erase a route abort merely to obtain another kill.

Automatic healer-side weapon identification is implemented and live-observed
in **15478-15479**, with complete removal, identification, rearming, and slot
confirmation. Live encounter budgets can use the connection-local reading;
ordinary pre-login output uses generated lower bounds from the actual worn
level when available. Saved zero-ID readings never authorize a later connection.
The scoped **38-test** batch passed in **2.22 seconds**, consuming September 29's
single allowance. Broader regression is deferred; continue useful campaigns.

Ararisa remains **49,333 XP**, level **11** (**47303**), after a below-band live
target. Fenanallor remains **28,765 XP**, level **8** (**47305**), after the bounded
route-hazard wait. Both finished fully recovered at healer **3054**. Dorrik
successfully replenished flight in **15480**, then killed the Dwarven Home host
in **15481** for **759 target/net XP**. He is level **26**, **445,358 XP**,
**8,242 XP** from 27, fully recovered at healer **3054** (**47308**). The whole
four-run block earned **149.3 net XP per connected minute**, including the
unproductive attempts and shopping. Continue that executable progression;
broader sustained throughput and HERO remain unproved.

Run **15482** earned no XP because a crowded optional stop interrupted the
outbound route before its original destination. The shared handoff now retains
that unvisited endpoint even when the optional stop is last in the circuit.
Crowd and hard-abort evidence remain intact; checks are saved but unrun under
the daily test limit. **15490** proved continuation past the rejected pair, but
found that the remaining fixed north commands looped in randomized rooms.
The Guardian dispatcher now uses the existing bounded live navigator from
**19031** to **19041**, with source checks for the entrance and safe maze path.
That new handoff remains unproved live. The pouch false timeout in **15487** is
also addressed by retaining only the unfinished preceding prompt, with new
checks saved and unrun. Neither repair widens combat permission.

Fenanallor is level **8**, **28,765 XP**, **2,935 XP** from level 9, at healer
**3054** (checkpoint **47296**). Runs **15472-15473** earned **200 target/net XP**
in **219.90 connected seconds**; the ring attempt did not acquire its objective.
Serevian's next public selection stopped before login at the saved funding
blocker. Neither result justifies replaying an unchanged unavailable route.

Source weapon ranking no longer treats prototype values as damage dice.
DD4 generates minimum/maximum damage at object creation; live run **15475**
identified a **3-8** dagger whose prototype says **2,4**. The September 29
implementation now binds a reading through one confirmed removal/rearm sequence.
Cross-connection reuse and any claimed sustained XP/minute improvement remain
unproved; do not promote legacy instance ID zero into durable weapon identity.

Kestrel remains level **24**, **329,125 XP**, fully recovered with food at healer
**3054** (checkpoint **47283**). His latest sanctuary searches exposed a locator
redirect that lost the registered movement-recovery stop. The redirect now
preserves that exact boundary; saved checks and live acquisition proof remain
pending. Rotate to productive roster hunts rather than clearing those failures.
That rotation earned Ararisa **220 target/net XP** in **15470-15471**. She remains
level **11**, at **49,333 XP**, with **9,117 XP** to level 12 and full healer
recovery (checkpoint **47291**). The second target failed its live admission;
no XP loss was recorded.

The funding dead end now hands off to the existing bounded quest request after
registered alternatives are exhausted. Astrevo exercised it in **15464**, but
the assigned Circus retrieval required a ticket and was safely aborted. The
new noncombat ticket-access planner is saved; the next relevant quest must
prove purchase, entry, retrieval, and reward together. Do not replay the aborted
quest or reset its allowance. Ararisa killed the kindly traveller for **164 XP**
in **15462**, reaching **49,113 XP** at level **11**; the next target was rejected.

The latest Dorrik checkpoint is **47256**: level **26**, **444,599 XP**,
**9,001 XP** to 27. The city detour worked in **15457**, but the target fight
lost **342 net XP**. Preserve that loss and improve readiness rather than
repeating the target. Local-teacher continuation now admits distinct useful
lessons, including live-listed unlearned skills, within a three-lesson visit.
Next proof: an actual accepted lesson and better current-band combat, not
another coverage report or extra regression batch. The first repair attempt,
**15461**, stopped at the city-route check without spending practices.

Dorrik reached level 26. Run **15413** last observed **444,941 XP** and
**8,659 XP** to level 27, back at the Midgaard healer; its worker interruption
was recovered before resuming. Pouch accounting now waits for a complete
reply across transport chunks, with a five-second healer-return boundary.
Run **15414** has exercised the normal empty-pouch response; split-response and
timeout cases are written but await the next permitted regression batch.
Continue current-band XP and remove recurring preparation overhead. Regression
work is limited to one batch per local day and is not a daily requirement.

The evening roster pass added **661 net XP** over seven live segments with no
level gains or recorded losses. Paired-slot acquisition ranking now recognizes
upgrades to the weaker second item and correctly counts existing gear. Next,
address lost combat opportunities: run **15423** stalled after Ivan fled because
the target-check reply was not acknowledged. That reply now releases the wait;
fresh source identity also supports differing combat and room names. The saved
failure cases remain unrun, and improved live pursuit is not yet proved.
Serevian's healthy one-kill return in **15421** had no second currently eligible
Moria target; raising the kill limit alone would not improve it. Preserve the
separate one-shot resource and probe contracts.

Run **15429** subsequently killed displaced Ivan for **188 target XP** and
returned fully recovered to healer **3054**. Serevian remains level **11**, at
**54,376 XP** with **4,074 XP** remaining to level 12. The preceding funding
and equipment attempts did not meet their objectives; **145 incidental XP**
is accounted separately. Keep improving useful kills per whole session rather
than treating completed maintenance or safe logout as advancement.

The funding-to-sale handoff now prioritizes new saleable drops from a completed
money hunt, preserving shop-route and retained-gear checks. A pending flight
purchase no longer replaces a selected sale. Live run **15434** selected that
sale but stopped at the bounded city-route hazard; proceeds remain unproved.
Serevian's latest checkpoint is **47186**, **54,416 XP** at level **11**. Rotate
the next progression block to another character rather than replaying his
blocked shop trip. New regression cases remain deferred under the daily cap.

The next concrete repair addresses Astrevo's premature familiar return in
**15436**: closed-exit headers now parse correctly, and pending identification
cannot be treated as a completed route. Failure checkpoints preserve the
matching familiar audit; identity and combat permissions remain connection-local.
The change is not yet live-proved, and its new cases remain deferred. Meanwhile
Fenanallor earned **452 objective XP** from three kills in **15437-15438**,
including a two-target Circus circuit, and reached **28,565 XP** at level **8**.
Two subsequent city-obstructed departures (**15439-15440**) added no XP;
checkpoint **47203** retains that total with full resources at the healer.
Rotate to an eligible distinct route or character rather than replaying those
obstructions. Obtain a fresh eligible familiar sequence without clearing its
earlier failure evidence solely to force a retry.

Run **15441** found a second familiar bottleneck: planning admitted Haglik while
combat rejected the familiar's random escape destinations. Both stages now use
one source audit, and the final check uses the live encounter room. The next
proof is an executable alternative and useful XP, not merely avoiding that
failed trip. Regression cases remain deferred under the daily cap.
The follow-up **15441-15446** block gained no XP over **439.90 connected
seconds** plus one **180-second** reset wait. Aeloria missed located, moving
potion carriers; Dorrik never cleared the city obstruction. Retain those
results and investigate the approved locator graph before repeating resource
trips. Their latest safe checkpoints are **47210** and **47216**, respectively.

Locator selection now waits for the complete reply and records reported
locations, mapped rooms, and chosen endpoints. The next Astrevo block earned
**242 target XP** over **313.53 connected seconds**, including maintenance,
ending at **35,712 XP**, level **9**, healer **3054** (checkpoint **47227**).
The normal live listing retained all ten locations; split and timeout cases
remain deferred. Continue productive current-band campaigns without reopening
the daily regression allowance or treating this as sustained HERO proof.
The following hunt encountered a crowd and added no XP; funding then had no
eligible target. Checkpoint **47234** retains the same total and full healer
recovery. Rotate to a distinct executable route or character for the next pass.
Corararfen's **15453** then exposed repeated locator queries after reaching a
room outside the initial route origins. Execution now supports an exact forward
suffix of an approved path and closes exhausted searches promptly. Obtain live
handoff evidence without clearing prior route failures merely to retry; keep
cross-prototype wandering circuits closed until their separate routing and
locator-scope requirements are implemented.
The existing Circus circuit remains productive: Velnor earned **367 target XP**
from two kills in **15454**, then saved after blocked flight shopping at level
**7**, **19,845 XP** (checkpoint **47240**). Continue these executable current-
band hunts alongside the navigation repair; do not count maintenance XP or a
safe return as equivalent to advancement.

### September 27 snapshot

No HERO result is proved; the highest actual frontier is level 25. Ararisa is
level 11 at **48,577 XP**, saved at the Midgaard Healer in room **3054**,
checkpoint **45761**. The active roster frontiers are Aeloria 18, Ararisa 11,
Astrevo 9, Corararfen 8, Dorrik 25, Fenanallor 8, Kestrel 24, Praelarran 21,
and Serevian 11.

Ararisa's run **14871** secured the two-item food reserve but earned no XP.
Run **14872** stopped at `bank-excess-coins` before login, with zero game
commands and no XP change. The MUD accepted TCP but sent no login greeting on
the bounded retries or the later five-second probe; no character action
occurred. The login-only timeout is now five seconds, with the existing bounded
retry, while the in-game timeout remains unchanged. Its focused test was
updated but not rerun.

The strongest plausible level-11 source candidate is the Gnome-area small
troll (#1507, room **1524**): source level 8, one reset, aggressive, unarmed,
and without a special. It remains caution-only. A live `consider` must reject
any response equivalent to five or more levels below; the route also requires
a fresh `where` check for the Drunk and the ordinary output, health, and action
limits. No live combat is authorized by the source estimate alone. When the
MUD sends its greeting again, resume the saved Ararisa campaign and return to
current-band XP work after any required maintenance step.

An earlier Ararisa campaign batch added **507 net XP**, from **44,302** to
**44,809**: run **14511** (+151) against the fanatic monk and run **14514**
(+356) against the Gnome cook. Run **14512** was loot liquidation. Run
**14513** killed the Miden'nir bard but awarded no XP because the familiar kept
attacking after the bot ordered it to flee. Its transcript exposed a parser
edge: DD4 appends a health comparison after the exact source-matched "easy
kill" sentence, while the solo-consider recognizer required the entire line to
match. The recognizer now accepts trailing text after that exact sentence; its
focused regression is covered by **69 passing tests** in
`tests/test_considered_solo.py`. Live run **14514** confirmed the companion
left before the player's spell delivered the kill and full XP. This validates
the withdrawal and XP-credit path; the exact bard wording has offline test
coverage, not a repeated live attempt. The earlier run **14504** confirmed
that an area-local `where` miss in Dragon Cult can use one source-audited
crossing and follow the exact Midgaard route through rooms **3024, 3025, 3026,
3045, 3046, and 3219** to the guild. Ararisa remains level 10 at checkpoint
**44715**, **3,691 XP** from level 11. The full suite remains deferred during
this progression batch; no HERO result is proved.

Subsequent bounded work added **169 XP** in run **14515**, moving Ararisa to
**44,978 XP**. Run **14516** exposed a split bank-response bug: a 500-coin loan
was confirmed, but the following prompt replaced its confirmation before the
policy checked it. A short response buffer now preserves that bank exchange;
the two focused loan tests pass. The loan raised her purse from 1 gold, 2 silver
to 6 gold, 2 silver, while the bank reported **3,985 coins owed** and a 50%
share of future shop sales until repayment.

Runs **14519-14520** earned no XP: live `consider` rejected the war dog as no
match, and the Gnome cook attempt stopped when the familiar could not be
confirmed safely in place. Run **14521** then started a Cult fight inside the
Midgaard transit corridor before its city-interruption gate rejected the
target. Ararisa fled, losing 88 XP and receiving 27 for damage, a **61 XP net
loss** to **44,917**. The policy now blocks proactive field and familiar
openers inside that corridor; its focused city-transit tests pass **35/35**.
Run **14522** completed the Moria sanctuary route without XP. Run **14523** was
interrupted at Temple Square before combat; run **14524** recovered and saved
Ararisa at healer room **3054**, level 10, **44,917 XP**, full health. The full
suite remains deferred; the HERO objective is still unproved.

The prior bounded roster pass had three net XP gains: Ararisa reached level 10
at **43,306 XP**, checkpoint **44644** (run **14491**, +83); Corararfen was
level 8 at **26,664 XP**, checkpoint **44650** (run **14492**, +223 in Moria);
Fenanallor was level 7 at **20,733 XP**, checkpoint **44654** (run **14493**,
+256 in New Ofcol). All three saved at healer room **3054**; none levelled.

Corararfen's runs **14488-14490** repeatedly found the wandering drunk blocking
the selected Circus/New Ofcol routes and returned safely; the route checks
quarantined those exact paths. The next roster segment took the distinct Moria
route and earned XP. The one-pass rotation deferred Aeloria, Dorrik, Kestrel,
and Serevian before login at their exhausted protection gates, and deferred
Astrevo and Praelarran at their funding/frontier blockers. This confirms that
the roster can keep progressing where a route is executable without repeatedly
opening blocked high-level sessions. The full suite remains deferred.

The source-mapped Midgaard detour has movement, exact-location, and route-hazard
gates, followed by a fresh live `where` check; 50 focused tests pass. Run
**14420** found the drunk at the bank entrance, Levee, and Main Street, so the
level-7 source-bounded transit gate correctly refused the detour. The same route
qualifies offline at level 8 if live locations still match (129 movement on
foot or 45 flying), but it is not live-proved. A one-round roster pass screened
all nine characters; only Fenanallor connected, ended safely without XP, and
checkpointed at **44447**. The others were deferred before login at their
recorded route, sanctuary, funding, or protection blockers. The full suite
remains deferred.

Ordinary wanderer searches now default to eight nearby safe target rooms even
when a caller omits the limit; the complete source map remains available for
hazards and exact live `where` results. Five focused locator tests pass. This is
offline implementation evidence, not new live XP; the full suite stays deferred.

The gear planner also no longer treats an empty finger slot as making a
negative-stat ring an upgrade. In the current DD4 source, Moria ring **4000**
has **-2 strength** and now ranks below an empty slot, so it is excluded from
executable carrier upgrades. Four focused equipment tests pass; this is gear
selection evidence only, not new XP or live loot proof.

Recent live work produced confirmed XP on four characters without losses.
Ararisa is level 10 at **42,828 XP**, checkpoint **44370**, 5,672 XP from level
11. This batch started at 41,882 XP/checkpoint **44342** and added **946 XP**:
Ambush traveller runs **14381**, **14385**, and **14390** earned 137, 240, and
177 XP; Gremlin Lord run **14387** earned 392 XP. Later Gremlin Lord runs
**14392-14393** yielded no recorded XP, so do not repeat without fresh target
or reward evidence. Run **14384** killed the Miden'nir bard but recorded no XP;
the Cult hunts in **14383** and **14391** recorded no XP (**14383**'s target
was absent). Live `consider` correctly rejected Granny Jenkins as no match in
**14386**. These no-gain checks do not establish a code defect. The earlier
funding trip recovered Katrina's sword and Lum, but liquidation raised cash
only from 1 silver and 1 copper to 2 silver and 10 copper; it is not yet a
useful flight funding loop.

Corararfen's latest confirmed live total is level 8 at **25,388 XP**: run
**14363** added 92 XP in the Mud School arena and run **14376** added 113 XP in
the Circus. Run **14364** found Mud School empty. Run 14376 used the separate
level-10 `validation-all` track; the level-100 `validation` campaign remains at
checkpoint **44280**, blocked by the same-boot Moria crowd. Do not mistake the
test-track checkpoint **44331** for the HERO campaign checkpoint.

Fenanallor's earlier checkpoint was level 6 at **18,935 XP**, checkpoint
**44334**. Circus runs **14365-14366** earned 45 and 124 XP; the daycare ring,
Sword Swallower, and repeat Bobby attempts then earned none. Leave those
same-boot targets closed.
Praelarran remains level 21 at **233,527 XP**, checkpoint **44075**; Aeloria,
Dorrik, Kestrel, and Serevian likewise had no current safe route and were
deferred before login. Astrevo had no safe funding target. These individual
blockers do not justify waiting globally for a reboot. The focused rotation
configuration test passes; the full regression suite remains deferred while
we continue with changed routes and live evidence.

### Current blockers and combat work: September 24, 2026

Dorrik is level 25 at 405,281 XP (checkpoint 44076), Kestrel level 24 at
329,349 XP (checkpoint 44066, fame -12), and Aeloria level 18 at 162,145 XP
(checkpoint 44077). HERO 100 remains unproved. Run 14152's diamond-golem probe
measured 86 damage dealt against 132 received; Dorrik withdrew and ended 168 XP
lower. Run 14153 stopped before its Solace target because the source-registered
drunk was at Temple Square, with no XP change. The parsed room-exit graph has
no open or unlocked path to that target avoiding that room. Do not repeat
without changed route evidence.

All four affected campaigns record an already-dispatched sanctuary recheck with
no reserve. Actual resumes now return a durable blocked checkpoint without
another reset wait or gameplay connection. This prevents a repeated wait, but
does not solve the missing sanctuary resource or create XP permission. The next
campaign priority is a genuinely new, source-safe reserve route or an executable
current-band target supported by live route, identity, consider, and output
evidence.

The exact Moria ring flight-funding route now admits its two source-verified
wimpy transit mobiles only with the live character damage bound, the `where
drunk` preflight, and existing crowd and finite-fight checks. The relevant
source-population tests pass (**63 passed**) and the focused Moria funding test
passes. This is not live proof: Corararfen's latest bounded resume stopped
before connecting at level 8, checkpoint **44081**, **24,953 XP**, because no
source-safe current-band hunt was available. HERO and Moria ring acquisition
remain unproved; the full suite is deferred.

Praelarran's live funding route did make concrete progress: run **14266**
collected two Gnome treasury piles totaling **6 gold, 49 silver, and 151
copper** (1,241 copper-equivalent), and run **14267** bought flight. His next
source-ranked Queen Spider route found the target but also three huge poisonous
spiders in its room; the safety gate withdrew without XP or loss. The following
selection found sanctuary recovery on cooldown and stopped before reconnecting.
This proves a funding loop and hazard response, not sustained leveling.

The combat loop now rotates through available, source-registered between-round
attacks, so a practiced kick is no longer starved by headbutt. Four focused
campaign checks and six starter checks pass, and changed modules compile; this
rotation is not yet live-proven. The full suite remains deferred until a larger
coherent batch is ready. No regression result or offline shortlist is HERO
proof.

The source-ranked fallback now opens from level 1 after a registered route is
unavailable; levels 1-5 use a distinct band label and the normal exact-target,
route, live-consider, useful-XP, output, and health gates. A registered arena
route can hand off only when same-level, same-boot below-band evidence has
closed it. Ten focused tests passed; the full suite remains deferred.
Fenanallor advanced from level 5 at 12,292 XP (checkpoint **44082**) to level
6 at 14,809 XP (checkpoint **44116**), gaining **2,517 XP** without waiting
for a reboot. Level-5 source-ranked hunts added **1,932 XP**; the level-6 Mud
School and cult-fanatic routes added **323** and **262 XP**. His later quest
request and one-time world-time check added no XP; no new reboot marker appeared,
and the latest checkpoint has no autonomous-safe current-band route. Two empty
wear slots remain after a basic-outfit attempt. This proves low-band progression
through level 6, not progress beyond it or HERO.

The new `hero-rotation` command gives each saved campaign one bounded segment
per pass, then defers blocked or failed entries so another character still gets
a turn. A live pass on September 24 completed in about a minute with no XP or
level changes: four campaigns hit an already-spent sanctuary recheck, Praelarran
was on a protection-recovery cooldown, and Astrevo had no safe funding target.
The roster now contains nine unfinished tracks, including the previously
omitted Ararisa, Corararfen, and Fenanallor campaigns. These per-character
route and resource blockers do not mean XP work should stop until a global MUD
reboot.

Corararfen's cleric campaign is now level **8**, saved at **24,953 XP** in
checkpoint **44081**. An earlier hunting batch added **291 GMCP-confirmed XP**
from two distinct Mud School boar resets; lizard, daycare, wolf, and return-home
segments added none. A field-city preflight had also been falsely blocked by a
drunk in Temple Square, which one Mud School route does not cross. The route
now lists only rooms it actually traverses, and the 65 focused departure tests
pass. The full suite remains deferred until a larger coherent batch. This is
early-band progress, not proof beyond level 8.

### Progress persistence and combat-readiness: September 24, 2026

Reconnect recovery corrected Fenanallor's actual saved state. Run 14075 reached
level 11 (52,153 XP), but the live connection failed before that segment could
save. Runs 14073-14074 had last saved level 4 (9,076 XP); reconnect run 14078
therefore loaded level 4 and safely saved it at healer room 3054. Treat the
level-11 result as transient live evidence, not current character progress.
The starter now requests a save on first verified progress after login and on
each later XP/level change, including during combat; DD4 source confirms `save`
is available at any position and writes the character file. Three focused
regression tests cover initial save, changed-vs-duplicate progress, and the
level-1 save restriction. Live runs 14079-14094 confirmed that earned XP
survived bounded session endings: Fenanallor reached level 5 and was saved
at 12,292 XP in healer room 3054, with full health and mana. The latest hunt
added 250 XP in six kills; a reconnect verified his saved total. Reboot-sensitive
bonuses may affect efficiency for particular mobs, but progression must continue
on other eligible targets rather than pausing globally.

Dorrik remains level 25 at 392,314 XP, fame 0, checkpoint 43669. In run 14099,
`where dolphin` placed the mobile in The Ocean Deep, but the next room check
found no exact target; Dorrik never attacked. The starter now uses its one
allowed location refresh after the first mapped-room miss, instead of waiting
for the full search. The full starter suite passes with this change (**1,483
tests**); the related campaign and progression tests had passed (**4,145**) just
before it. Runs 14102-14104 completed three food-reserve routes safely with no
XP. Run 14105 followed one area-reset wait and confirmed the same DD4 boot, so
this exact frontier remains closed by its safety evidence. The MUD login has
recovered; a reboot is not a general requirement for progression.

Praelarran remains level 21 at 233,527 XP. His offline report showed three
source candidates, but the live campaign correctly admitted none; run 14106
confirmed the same boot after one bounded area wait. Kestrel remains level 24
at fame -12, and his current fame audit found no target that fits his damage
limit. These checks identify separate character-specific blockers, not a reason
to stop all character work.

Offline review also fixed two readiness-report gaps: the combat report had
omitted source objects outside its starter-area object set, and the source
damage estimate for a ranger's `shoot` opening omitted DD4's two-times bow-hit
bonus and practiced `accuracy` bonus. The report now loads all objects without
widening its hunt areas; the estimator follows `fight.c` and counts accuracy
only when observed. The affected campaign, CLI, and source-candidate modules
passed 1,978 tests before the new persistence change; the four persistence and
healer-checkpoint tests then passed separately. This is offline evidence, not
live bow acquisition or new XP. The source-listed Ambush bow (4540) remains
caution-only because goblin traffic makes its route unsafe under current gates.

### Same-boot progression: September 23, 2026

Fenanallor advanced from level 4 (7,937 XP) to level 11 (52,153 XP), a net
44,216 XP, without a MUD reboot. Astrevo also gained 474 XP on the same boot.
This confirms that a recent reboot is not a general requirement for XP. A
cooldown or missing target belongs to that character's exact route; when one
frontier closes, check another eligible character or policy without bypassing
its safety gates. Fenanallor's last saved state is alive, standing, not in
combat, and at full health in the Mud School arena. Run 14076 could not observe
a login banner during homeward recovery, so recovery remains the next action.

### Reboot-scoped frontier diagnosis: September 22, 2026

Dorrik's latest checkpoint is **42991**, level **25**, at **388,606 XP** in
healer room **3054**. The latest maintenance-only probe was run **13850**;
`time` confirmed the existing DD4 reboot (`Fri Sep 4 06:19:51 2026`), so it
correctly claimed no progression XP. This short connection was intentional:
the worker authenticated, queried `time`, saved, and quit, then returned to the
durable healer checkpoint.

The source selector now persists `campaign_source_ranked_frontier_diagnosis`
when it finds no executable target. It records candidate counts, current-band
and autonomous-safe counts, sanctuary requirements, and exact same-boot
below-band exclusions. This makes a blocked frontier inspectable without
opening another gameplay connection. Dorrik's current offline audit reports
191 considered candidates, 17 current-band candidates, 8 autonomous-safe
candidates, 4 sanctuary-required candidates, and one below-band exclusion.
The remaining no-sanctuary options do not satisfy the live progression gates;
the next productive opportunity is a fresh reboot or new source-backed
evidence, not an unsafe sanctuary bypass. HERO 100 remains unproved.

### Endpoint invisibility admission: September 22, 2026

The Serevian checkpoint exposed a selector bug: the level-11 griffin route
could be classified as capacity research even though the thief had no learned
`invis` skill or practices. Policy revision **323** now rejects a source-proven
aggressive endpoint that requires invisibility unless the current state has
both the learned class/subclass path and enough mana. The gate runs before
route preparation and preserves the separate audited familiar-probe path.
This is a safety and evidence-quality repair; it creates no new live XP claim.

The September 21 identity repair is now in policy revision 311. New Ofcol
citizen VNUMs 617 and 618 have identical ordinary source profiles, so the
runner can preserve an exact live TARGETMODE instance selector and record the
observed alias instead of rejecting a safe target solely on cosmetic sex. This
exception does not apply to armed, special, protected, resource, bystander, or
probe stops, and it does not claim new XP until a live segment completes.

The ordinary fame gate is now recorded precisely: `HELP FAME` and `fight.c` use
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

### Endpoint swing parsing and Astrevo continuation: September 22, 2026

Live run 13794 exposed a transport-to-starter parsing gap at the level-9
Moria-adjacent endpoint: DD4 announced the mobile with
"grunts as he takes a swing at you," while the starter only recognized direct
damage verbs. The starter now recognizes all four source-format swing variants
already supported by the observation parser, binds the planned endpoint target,
and preserves the normal consider and source-identity gates. The focused
regression, full starter suite (1,459 tests), compilation, and full repository
suite (5,966 tests) pass.

The live continuation then completed Astrevo's Moria large-orc route in run
13792, adding 117 XP and returning safely to healer room 3054. Run 13794
remains negative route evidence because the swing parser fix was made
afterward; the campaign recorded the endpoint attacker as unidentified and
withdrew without XP loss. The next bounded rotation selected Katrina, but run
13795 failed before its endpoint and was quarantined. Run 13796 then repeated
the already productive Moria route for another 89 XP; Astrevo is now level 9
at 34,012 XP in healer room 3054, checkpoint 42826. These are progression and
route evidence only; they do not prove a sustained run or HERO 100.

Revision **319** reopened that exact stale Gnome result once. Run **13798**
confirmed the swing parser live, but exposed a second defect: DD4's successful
combat recall returned to Midgaard without a combat-end line, leaving local
combat state active and causing repeated recall commands. The starter now
clears that local state on the canonical recall-room header. Run **13799**
then reached the same troll, recognized its live source identity, and withdrew
once the required familiar reserve was found missing; DD4 charged **80 XP**.
The character returned safely to healer room **3054** at checkpoint **42837**,
level **9**, with **33,932 XP**. The route is now quarantined for the reboot by
its exact familiar-loss hazard. Verification is **1,460 starter tests**,
**1,642 campaign tests**, **5,973 repository tests**, and clean compilation.

The follow-up policy repair now rejects an aggressive or scripted endpoint
unless the source proves an outdoor no-mob waypoint where the familiar can be
summoned and identified before entry. This is a selection gate, not a combat
permission bypass. Run **13802** exercised the staged New Ofcol route, killed
Granny Jenkins for **118 XP**, and returned to healer room **3054**; Astrevo
is now level **9** with **34,050 XP** at checkpoint **42844**. The complete
campaign suite passes at **1,642 tests**. HERO proof remains open.

Run **13803** supplied a transport regression fixture: Granny Jenkins was
announced in the live room response, while the ANSI reset and prompt arrived
in separate Telnet chunks. The observation and starter parsers now retain an
incomplete escape across chunks and reassemble the prompt before extracting
the area. The worker returned safely at its bounded runtime limit without
claiming XP. The focused observation/starter suites pass **1,503 tests**.
Run **13804** confirmed the current reboot was unchanged and selected the
finite field-reset wait rather than replaying a stale hunt.

Run **13805** reached the source-ranked Moria endpoint and found the large orc
in room **4019**, but DD4 reported a second mobile in the room. The live crowd
gate therefore stopped before combat and the worker returned safely to healer
room **3054** with no XP change. Astrevo remains level **9** at **34,050 XP**,
checkpoint **42851**. This is positive locator evidence only; the unchanged
crowd route is closed for the next rotation.

Run **13806** rotated to the Circus and reached the Midget's Tent. The Midget
was absent, although other circus mobiles were visible on the approach. The
worker returned safely and recorded a bounded absence at checkpoint **42854**;
this is not evidence that the whole area is empty and no XP was claimed.

Run **13807** rechecked Moria and found the large orc in room **4025**, with
two source-registered garter snakes carrying `spec_poison`. The runner rejected
the exact room before combat and returned safely. The target is live and
locatable; the route instance is closed by its hazardous bystanders, not by an
empty-area assumption.

Run **13808** stopped before opening a socket because the funding ledger is
now explicit: Astrevo has **27 copper-equivalent** and the current observed
fly price is **131 copper**. The all-area source audit found only two direct
coin stashes at level 9, both rejected by route or level hazards; the remaining
local funding targets require fresh area evidence. One finite reset wait is
the next action, not an unbounded funding retry.

Runs **13809-13812** collected four bounded post-reset Moria funding results.
The large orc supplied maintenance-only XP of **142**, **152**, and **148** on
productive attempts; one locator pass found it absent. Every run returned to
healer room **3054** without death or XP loss, leaving Astrevo at level **9**,
**34,492 XP**, checkpoint **42880**. Source object 4000 is poisoned, so its
nominal value is not spendable: both the Leather Shop and Armoury offered zero.
Run **13813** preserved that no-sale evidence, donated five copies, and left
one for the next bounded cleanup pass. The selector repair now sends carried
saleable loot through liquidation when a quarantined `bank-excess-coins` route
would otherwise repeat field funding, and does not preserve a known -2 strength
ring just to fill an empty finger slot. The current state is safe at healer
room 3054 with **57 copper-equivalent**; this is maintenance evidence, not
progression XP or HERO proof.

The post-repair full repository regression is **5,977 passed** in 455 seconds,
with clean compilation. No gameplay worker remains active; the Discord
streamer is the only intentional long-running Python process.

Runs **13814-13817** kept the next step bounded. The Circus Midget was absent
in runs 13814 and 13817, including after one finite area-reset wait. Run 13815
revalidated the Moria large orc for **101** maintenance XP and returned safely
to healer room **3054** at checkpoint **42889**. Run 13816 removed the final
poisoned ring after both shops offered zero; its incidental **10 XP** drunk kill
was recorded below the useful band and excluded from progression. Astrevo is
now safe at checkpoint **42897**, level **9**, **34,603 XP**, with no carried
loot and no current source-safe funding target. The all-area level-9 catalog
admits only the Moria large orc, Circus Midget, and Katrina; Foundry Uburz
remains closed by prior live pre-consider aggression evidence. HERO 100 remains
unproved.

### Source-audited invisible funding boundary: September 22, 2026

Policy revision **320** now carries exact route-invisibility identities into
provision-funding dispatch. One unarmed, source-safe dynamic saleable drop may
be selected only after practiced invisibility, source route/program checks,
current-band, movement, HP/protection, saleability, and live identity gates;
the segment is persisted as `funding_only` and its XP is excluded from
progression. Armed ambush endpoints, scripted or unknown transit hazards, and
the quarantined Foundry Uburz remain closed. Astrevo's current HP/protection
state does not yet create live permission for this route. The repository suite
passes **5,979 tests** in 448.62 seconds, with clean compilation. HERO remains
unproved.

### Source keyword identity repair: September 22, 2026

Run **13818** safely reached the New Ofcol route but earned no XP because the
visible `citizen` name could refer to source mobiles **617** or **618**. Their
room text is identical, but the source keywords `man` and `woman` distinguish
the prototypes. Revision **321** now prefers those distinguishing keywords
and admits one only when it is unique among the source identities reachable in
the exact room. A shared generic keyword remains fail-closed, and legacy
checkpoint candidates are refreshed before route construction. Serevian is
level **11** at checkpoint **42900**; the full repository suite passes
**5,982 tests** with clean compilation. No new progression or HERO proof is
claimed. Run **13819** then reached the Circus Midget's Tent after the bounded
reset wait, found the source target absent among unrelated wandering mobiles,
and returned safely at checkpoint **42906** with no XP change. The selector
repair remains offline identity evidence until a uniquely targetable live
prototype is present.

### Bounded funding/protection handoff: September 22, 2026

Revision **322** prevents an absent current-boot flight-funding carrier from
being reopened ahead of an unfinished sanctuary recovery budget. It permits one
existing source-validated sanctuary attempt, with the normal healer, food,
unarmed carrier, movement, capacity, and source gates; an empty sanctuary
frontier remains a finite reset wait, not a safety bypass. Live runs **13828-
13833** added source-backed maintenance XP without death, while **13834**
rejected an ambiguous cow target. Serevian remains level **11** at checkpoint
**42955** with **53,384 XP**. HERO and level-12 transition proof remain open.
The full repository suite now passes **5,983 tests** in 612.47 seconds, with
clean compilation.

### Deep Moria runtime-cursor repair: September 22, 2026

Run **13773** reached the source-audited quiet waypoint at room **4152** after
`where hobgoblin` located both large hobgoblins in `The maze`. The bounded worker
returned safely at its 180-second limit before reaching the endpoint, so this is
route evidence, not sanctuary acquisition or progression XP. The normal success
return path now promotes the starter cursor into campaign state, and resume
reanchors a compacted locator stop only when one audited transit stop, endpoint,
or route leg matches the saved room. HERO proof remains open; the live reboot and
sanctuary-attempt boundaries remain authoritative.

The repair is covered by **1,457 starter tests** and **1,633 campaign tests**,
plus compilation and conversation-log validation.

The next autonomous continuation completed two bounded policy cycles and wrote
checkpoints **42765-42766** without opening a gameplay socket. The DD4 reboot
marker did not change, and the remaining level-25 source-safe candidates either
need sanctuary or are excluded by current-reboot below-band evidence. This is
a durable wait boundary, not HERO or progression proof; the next live attempt
must resume from the healer checkpoint after fresh reset evidence.

### Aeloria reset-boundary confirmation: September 22, 2026

Run **13780** reached lemming-smithy room **29966** and recorded the source
target absent, returning to healer room **3054** at level 18 with no XP change.
The supervisor then used exactly one 180-second reset wait. Runs
**13781-13782** confirmed that DD4 still reports boot `Fri Sep 4 06:19:51
2026`, so the absent-target and sanctuary cooldown evidence remain current and
the campaign stopped at checkpoint **42773**. This is a clean deferred boundary,
not a reason to relax protection recovery, below-band, or fame gates.

### Serevian crowd-loss repair: September 22, 2026

Run **13783** exposed a starter bug on the level-11 thief track. The Gnome
Village endpoint route entered room **1583**, where two source mobile **1517**
hobgoblin soldiers were simultaneously present. The old transit exception
treated that crowd as one bounded below-band interrupter, killed one for 50
maintenance XP, then fled the remaining soldier and lost 99 XP. The starter
now rejects any same-room crowd of source-known below-band transit mobiles
before combat; the existing single-isolated-interrupter and bounded special
contracts remain unchanged. The replay is covered by the full **1,457-test**
starter suite and **1,633-test** campaign suite. Run 13783 remains loss
evidence, not progression proof, and the unchanged route will not be retried
on the current reboot.

Run **13784** exercised the next New Ofcol policy after the crowd repair. The
live `where` result reached room **655**, where the ordinary `citizen` identity
was source-ambiguous between mobile VNUMs **617** and **618**. The runner
returned to healer room **3054** at checkpoint **42782** without combat, a kill,
XP change, or loss, and marked that exact policy unavailable for this reboot.
This is identity evidence and a clean deferred boundary, not progression proof.

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
**382,950 XP**, with sanctuary reacquisition or a stronger source-safe combat
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
The key route is now source-proven for the level-25 frontier: the executable
plan binds key 6502 to the exact guard resets in rooms 6505 and 6540, requires
a fresh exact TARGETMODE selector for each same-source guard, and uses one
bounded `east east west west` detour to inspect the alternate carrier room
before returning to the locked door. It carries both key 6502 and flask 2008
through the required-loot audit; each maintenance kill still requires a
consider result.
At the exact level-25 aggression cutoff, only source mobile 2011 (the level-15
zombie mage with `spec_cast_mage`) may interrupt transit, under a fresh GMCP
identity and source damage bound. This remains maintenance-only; live key
acquisition and progression benefit are not yet proven. Revision 312 reopens
the earlier same-boot crowd-abort result only for this selector-preserving
implementation; revision 313 repairs the matching transit-identity checkpoint,
revision 314 repairs the matching post-maintenance health-floor checkpoint,
revision 315 recovers the exact same-boot key acquisition from the prior
selector-persistence crash, revision 316 reopens only the matching
quit/reconnect loss, revision 317 records the alternate carrier-room route,
and revision 318 requires a verified sanctuary reserve before dispatching the
gate because DD4's same-prototype guards automatically join the fight. Without
that reserve, the planner selects bounded Moria recovery and then records an
unavailable boundary when its reboot-scoped attempts are exhausted.
Other stale fatal evidence remains authoritative.

The shallow Moria endpoint now has one explicit source-configured pre-entry
re-scan for the adjacent wandering warrior. This addresses a transient room
timing miss without relaxing the hazard gate: a second sighting still closes
the segment, and the retry cannot earn combat or progression XP. The next live
check remains Serevian's bounded protection-recovery frontier.

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
Dwarven Catacombs sanctuary plan back to its research/maintenance track. Its
west door in room `6505` is closed, locked, and pickproof; `pick lock` cannot
bypass it. The selector now requires the separately audited key reset on
dwarven guard 6500, then uses the bounded route-gate machinery to consider and
isolate that guard before issuing `unlock west`. The parser smoke test and
source policy regression preserve the fail-closed boundary. No live XP or HERO
evidence follows from the correction.

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

The offline readiness report separates an offensive HP-ceiling fit from its
source-gate fit, including source HP admission and sanctuary availability.
That source-gate result is not the campaign's final dispatch decision: live
target history and route checks can still reject a candidate. This corrected a
misleading level-25 report where Mr Smithy fit the raw damage ceiling but still
failed the survival/output-reserve gate. Dorrik's bounded
resume at checkpoint **42404** therefore opened no gameplay socket and retained
the real blocker: sanctuary reacquisition or a stronger, source-safe combat
envelope is required before the next productive route.

### Level-25 frontier and maze liveness: September 21, 2026

Dorrik's bounded continuation reached checkpoint **42416** at level 25 with
381,533 XP. One finite 60-second area-reset wait completed, but `time`
confirmed the same DD4 reboot and no current-band route reopened. The live
Abyss copepod policy withdrew at its movement reserve without combat or XP;
the tree-sprite policy remained unavailable. The readiness report now makes
the boundary explicit: the three unprotected source-gate candidates are
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

### Retry Cooldown And Roster Check: September 24, 2026

Runs **14161** and **14163** repeated the level-9 Ambush goblin route while its
same-boot failure cooldown was active. Both runs summoned the pony but found it
was not present in the target pit, so they withdrew without a kill or XP. The
generic cooldown override now reopens genuinely absent resets only; an observed
retryable failure stays closed unless its exact one-use revalidation is active.
Campaign policy revision **326** records the change. Six focused campaign tests
passed, including absent-reset rotation and the bounded timeout recheck; the
full suite is deferred until a larger batch.

Astrevo remains level **9** at **35,282 XP**. Checkpoint **43841** stopped at
the real flight-funding shortage, so no identical hunt was opened. Dorrik
remains level **25** at **405,281 XP**. Run **14164** confirmed the same
September 4 reboot; the all-areas readiness audit found three post-loss target
candidates, all already excluded by live below-band evidence. Other promising
level-25 targets still require sanctuary, and the single post-reset Moria
recheck is spent. No XP or HERO proof is claimed for these checks.

### Bounded Level-Seven Progress And Healer Recovery: September 25, 2026

Fenanallor is level **7** at **19,459 XP**, safely checkpointed at **44467**.
Runs **14424**, **14425**, and **14427** killed source-ranked Moria orcs and
Granny Jenkins for **309 total XP**. The Moria route checked its next mapped
room after run **14427**'s orc kill, found no target, then returned to the
healer; no death or XP-loss message was recorded. Run **14426** attempted the
Daycare ring route but withdrew when its source-registered teddy-bear hazard
blocked confirmation of the doll. It gained no XP or ring and is not an
immediate retry.

Run **14423** had found the Daycare nanny and received an easy live `consider`,
but a broad cleric-special estimate stopped the fight for lack of a carried
cure. The source nanny is level **5** (load range **3-7**); the current gate
charged it for spells unavailable at that level. Healer-backed blindness
recovery is now limited to source-verified, non-scripted clerics below the
curse threshold, with a recall-safe area and level-accurate damage bounds.
Run **14421** also exposed a missing route from an intermediate Moria waypoint
to a positive exact `where` result; that locator now follows safe, unique-room
routes while retaining the eight-room blind-search cap.

Twelve focused campaign, starter, and locator tests pass, including the
no-recall and curse boundaries. The full suite remains deferred until a larger
implementation batch. The Daycare recovery change still needs a fresh bounded
live confirmation. HERO 100 remains unproved.

### Level-Ten Combat Acknowledgement And Progress: September 26, 2026

Run **14528** exposed a live-name mismatch: the campaign addressed `human boy`,
while DD4 reported the exact enemy as `The stunned boy`. The spell acknowledgement
timed out, the between-round spell loop did not engage, and the character withdrew
at the existing health gate after a small **22 XP** gain. Combat acknowledgement
now prefers the current GMCP name when exactly one enemy is present; crowded rooms
keep the narrower source-name match. A focused replay of the exact DD4 response
passes, alongside the existing spell-rotation tests.

Run **14529** met `The small boy`; live `consider` said he was no match, so the
campaign correctly skipped combat and awarded no XP. Run **14530** then killed
Granny Jenkins for **145 XP**. The live combat tracker acknowledged all three
actions with zero timeouts. Ararisa is level **10** at **45,218 XP**, alive and
fully recovered at healer room **3054**. This is evidence of level-ten progress,
not HERO completion. The full suite remains deferred until a larger coherent
implementation batch.

Run **14531** bought and quaffed a light-blue flight potion for the observed
price of **131 copper**, then returned to healer room **3054** at full health.
This was preparation only and earned no XP; the price is reboot-sensitive and
must not be treated as fixed.

Run **14532** recorded no sale proceeds, so the empty liquidation route should
not be repeated without new saleable loot. Run **14533** stopped the exact
Daycare ring errand at its source-registered toy-soldier and stuffed-bear
hazards before confirming the old doll. No ring or XP was gained; Ararisa
returned safely to healer room **3054**. Do not retry this route until fresh
boot, route, or hazard evidence changes.

After the safe skip of the no-match small boy and the unmeasured-HP bard, run
**14535** repeated Granny Jenkins for **130 XP**. The combat tracker acknowledged
both actions with zero timeouts, and Ararisa returned at full health to healer
room **3054**. Her current level-ten total is **45,348 XP**. This confirms a
useful current-band repeat, but does not justify an unlimited single-target
loop; continue comparing live XP per completed segment.

Run **14536** found Katrina's route unable to reach its registered endpoint;
the campaign quarantined that route and safely returned without combat. Run
**14537** then killed Granny Jenkins for **205 XP**. Four combat actions were
acknowledged with no timeouts, and Ararisa returned at full health to healer
room **3054**. She is now level **10** at **45,553 XP**, a net gain of **636 XP**
from the start of this work block. Level 11 and HERO 100 remain unproved.

### Roster Rotation And Frontier Closures: September 26, 2026

One configured rotation pass checked all nine character campaigns. Aeloria,
Dorrik, Kestrel, and Serevian opened no live session because their level-band
policy frontier or sanctuary reserve was unavailable; Astrevo had no safe
funding target. Praelarran was held at the current-reboot sanctuary cooldown.
Corararfen's Circus route stopped at the Midgaard drunk preflight without
combat. Ararisa's outfit check made no XP change.

After two new Jenkins kills, run **14545** found fresh liquidation inventory:
a pair of leather leg guards sold for **24 copper**. XP did not change, and
Ararisa returned safely to healer room **3054**. This is distinct from the
earlier empty sale attempt **14532**; do not repeat liquidation again without
new loot evidence.

Fenanallor's saved state was already **20,733 XP** in earlier run **14493**;
the rotation did not add **1,274 XP**. Run **14544** lost its field connection
before combat and safely returned to healer room **3054** with the same XP.
Run **14538** likewise stopped before Moria entry at a source-registered
warrior; **14539** found Granny Jenkins absent; **14540** skipped the easy-
consider hobgoblin cook because live HP was unavailable; and **14541** refused
the Ambush route because invisibility had no fresh duration. None of these
opened combat or earned XP. Keep the full suite deferred while addressing the
highest-value executable frontier; no reboot-wide pause is justified.

The single route-only revalidation for Katrina then repeated the same endpoint
failure. Run **14546** reached New Magincia's moongate and summoned the pony,
but recalled before the registered final route steps; it never reached Katrina
or opened combat. Ararisa returned alive at full health to healer room **3054**
with unchanged **45,553 XP**. Close this route for the current boot; do not
dispatch another retry without changed route evidence.

Runs **14547-14548** show why segment time must match route length. The
150-second cap returned Ararisa just before acting at King Boo's room. The
single longer attempt reached room **160**, confirmed King Boo absent, and
returned safely to healer room **3054** at unchanged **45,553 XP**. Close this
target for the current boot and let the campaign select another eligible
current-level policy; do not repeat this empty endpoint.

Runs **14549-14550** found Boos the Gremlin in room **153** and Booz the
Gremlin in room **156**, but live `consider` classified both below band. The
bot correctly skipped both fights, recorded no XP, and returned safely to the
healer with full health and movement. Close these exact targets for Ararisa's
current level and boot; other eligible targets remain available.

Runs **14551-14552** exposed a campaign-history bug: stale provision-funding
kill metadata for Katrina could erase a newer same-boot route-failure result
with the same policy ID, making the route appear fresh and causing it to be
selected twice. Funding cleanup now preserves current-boot negative evidence
and its cooldown while still removing stale positive funding proof. Four
focused funding-repair tests pass. A local policy preview now retains the
Katrina quarantine and selects the Moria hobgoblin route; no full suite was
run.

Run **14553** confirmed the selected Moria target, the small beat-up hobgoblin,
was present but below band by live `consider`. No combat or XP was recorded;
Ararisa returned to healer room **3054** at full HP with **92/240 movement**.
Keep this exact target closed at the current level and recover movement before
the next field segment.

Run **14554** reached the distinct Moria orc in room **4028**, but live
`consider` again placed it below band. The planned continuation then lacked a
GMCP exit to room **4019**. No combat or XP was recorded; Ararisa returned to
healer room **3054** at full health and movement. The all-area readiness report
shows the large orc in room **4022** at 80% useful-XP probability, but it
requires sanctuary; keep that gate closed until a reserve is available.

### Progress Focus And Bounded Passive Probe: September 27, 2026

The daily regression limit is a ceiling, not a task: spend nearly all work on
implementation and executable character progress. Today's one focused pytest
batch had already run before this work, so no additional regression tests were
started.

The bounded roster rotation advanced Corararfen from **29,293** to **29,373
XP** (+80) after a Circus kill. Fenanallor's interrupted route was recovered
back to the Midgaard healer and safely saved at **27,070 XP**. The other
rotation entries were blocked, maintenance-only, or ended without XP; Kestrel
and Dorrik remain at levels **24** and **25** without an executable frontier.

Ararisa's level-11 Gnome cook attempt (run **14926**) reached the exact passive
target; live `consider` called it an easy kill, but the runner withdrew before
combat because it did not have the required large current-health lead. Source
HP was **46-153** against **145** player HP, and audited spell output was **348**.
The existing protection-recovery admission had already passed source, route,
damage, and same-boot gates, so the final opener check was stricter than its
bounded fallback. A single opener is now allowed only for that exact fixed,
passive, unarmed, program-free, special-free source endpoint when its full HP
ceiling fits audited output. GMCP damage evidence and the existing finite
withdrawal rules still decide whether the fight continues. Focused tests were
added but not run under today's test cap; HERO 100 remains unproved.

Run **14927** did not exercise that new opener; policy rotation selected a
different Ambush target. The familiar opened first, but withdrawal was not
positively confirmed. The bot then tried combat `recall`, which failed, and
followed with `flee`; Ararisa returned to healer room **3054** and saved at
**48,443 XP**, down **171 XP** from the prior checkpoint. DD4 source confirms
that a failed combat recall costs **50 XP** and a successful flee costs the
level-based amount. Do not repeat the unchanged Ambush target. The passive
probe still needs an eligible live confirmation, and the withdrawal sequence
is a separate improvement opportunity.

### Progress Focus And Current-Band Evidence: September 30, 2026

One focused city-departure regression batch was run today after the route
improvement; do not run another batch today. Keep the once-per-local-day test
ceiling, and spend the available effort on executable current-band progression.

Corararfen's level-9 Cleric moved from **34,032** to **34,228 XP** (**+196
net**) across runs **15606-15613**. Circus runs **15608** and **15609** earned
118 XP from the child's father and 140 XP from the Illusionist. The large-orc
attempt **15611** lost 62 XP; run **15612** completed the Moria recovery task,
and run **15613** returned safely without further XP. Keep the large orc
closed for this level and reboot unless new evidence changes its risk. The
Moria hobgoblin and orc checks **15606-15607** and daycare-ring maintenance
**15610** did not add XP.

Ararisa remained level 11 at **50,014 XP** after six cycles ending at
checkpoint **47706**; the Gnome hunt added no XP and subsequent steps were
maintenance. Astrevo remained level 9 at **37,244 XP** and checkpoint **47727**;
no live session opened because no safe same-boot funding target was available.
Kestrel remained level 24 at **329,125 XP** and checkpoint **47386**; the
sanctuary-recovery route is on a same-boot cooldown, so the campaign checkpointed
without reconnecting. These are character-specific blockers, not reasons to
pause the roster or wait for a reboot when another route is executable.

Source-ranked run output still reports `circuit_targets=0`. Existing circuit
planning therefore needs a focused throughput investigation, while preserving
the registered live identity, route, consider, output, and recovery gates.
No level gain occurred in this checkpoint; HERO 100 remains unproved.

### Roster Rotation And Route Evidence: September 30, 2026

The bounded ten-character rotation completed without adding XP. Characters
checkpointed on unavailable
current-band targets, funding routes, or sanctuary reserves; several decisions
closed before a new connection. Do not replay those unchanged selectors merely
because the rotation finished.

Dorrik's recorded Mirror Realm route reached the castle entrance and saw two
level-23 guardians, then failed to resolve the shuffled maze's live exit to
room **19036**. There was no consider or combat. Source confirms each guardian
can carry a sword, the room permits two, and the approach has a level-25 special
and an aggressive city wanderer. The earlier viable guardian probe is research
evidence, not hunt authorization; this hunt remains unproved and must not be
opened by weakening the existing crowd, equipment, or route gates.
The exact missing-exit result is now persisted as a same-boot route blocker,
without discarding the earlier probe evidence; the selector can rotate to the
Shire battle-master probe instead. Dorrik's following bounded sanctuary-recovery
segment (run **15664**) safely returned to the healer with no XP gain; he remains
level **27** at **454,973 XP**. The Shire route has not yet been live-verified.

Elariven's live considers rejected the Circus huckster and Mud School boars as
below-band; wandering drunks separately blocked city departures. Corararfen's
Circus attempt also stopped at the healer on that city obstruction. Serevian
and Ararisa had no safe current-boot funding target, while Velnor's sanctuary
carrier was absent. These are bounded, character-specific blockers, not a
reason to wait for a whole-world reboot. HERO 100 remains unproved.

Corararfen's latest city preflight (run **15631**) recorded a changing-location
case: the first mapped detour avoided Practice Yard and Main Street, then a
fresh locator found a drunk in Market Square on that revised route. The runner
correctly stopped before departure. A single changed-input correction is now
available at the healer as well as at recall, using the same source-map, hazard,
health, and movement checks; it must recheck live locations and cannot be used a
third time. Source replay found a 144-movement route around the new locations
against Corararfen's saved 230 movement. A one-use same-boot revalidation is now
implemented for this exact saved shape, but only if ordinary selection finds no
other executable current-band candidate. It must reconstruct the first detour
from source and obtain fresh live locator evidence; this path is not yet proved
live and does not relax any combat gate. Current source ranking rejects that
exact target because its room can reset two matching mobiles alongside several
other occupants, so the saved city evidence alone does not make it executable.

Today's one focused run of `tests/test_field_city_departure.py` reported 54
passed and one failure in the separate bounded-city-transit admission case.
The changed-route correction passed. The new persisted-marker and runner-handoff
tests were added afterward and remain unrun because today's regression allowance
is spent. Compilation passed; do not run another regression batch today.

One additional bounded `hero-rotation --rounds 1` pass checked all ten saved
characters; none opened a gameplay connection or gained XP. Funding still blocks
Ararisa, Astrevo, Fenanallor, and Serevian; sanctuary recovery or its exhausted
recheck blocks Aeloria, Dorrik, Kestrel, and Praelarran; Velnor's carrier is
absent. Corararfen's exact city route remains unavailable because its current
source target fails
the reset-capacity and room-occupant checks. Do not repeat this unchanged
rotation; the next useful work is a new safe funding or protection option, or a
source-valid current-band target.

### Dorrik-Only Level-27 Progress And Gear Selector Repair: September 30, 2026

Until one character reaches HERO, Dorrik is the only progression pilot. Do not
create characters, rotate the roster, or spend live effort on matrix breadth.
Keep selecting executable current-band work; a reboot is not a prerequisite
unless the chosen objective itself depends on a reset.

Dorrik advanced from checkpoint **47958** at **479,215 XP** to checkpoint
**47975** at **482,045 XP**, a net gain of **2,830 XP**. He is level **27**,
**20,905 XP** from level 28, and ended safely at healer **3054** with **617/617
HP**, **445/462 movement**, no combat, and no new loss. Runs **15708**, **15710**,
and **15711** killed Mr. Smithy for **1,094**, **869**, and **1,051 XP**. Ki-Rin
run **15707** withdrew with a **493 XP** loss and a **184 XP net decrease**. The
Sea Deception run **15709** had no exact safe room for the live `where` result
“Out to sea”; run **15712** found no fresh Smithy. Both policies are persisted
on current-boot cooldowns and must not be replayed unchanged.

The bounded source-gear step in run **15713** acquired weapon object **6104**
from room **6125**, but its generated `wield 4.branch` selector counted matching
prototypes across the entire source catalog. DD4 rejected the command even
though the item was carried; subsequent cleanup donated it. The source executor
now uses the item's own keyword for gear and lockpick commands. A duplicate-
prototype case was added to `tests/test_campaign.py`, and `docs/OPERATIONS.md`
records the selector rule. `py_compile` and scoped `git diff --check` passed;
the focused test and a live corrected re-acquisition remain unverified. Today's
regression allowance was already used, so do not run pytest again today.

DD4 source was fetched from `origin` and is current at commit **0788349** dated
September 29; the mirror was clean and needed no merge. Continue Dorrik's level-
27 route selection and verify every kill and net XP from saved evidence. HERO
100 remains unproved.
