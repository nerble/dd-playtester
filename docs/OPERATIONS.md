# Operating Instructions

## Current Target-Selection Policy

For ordinary source-ranked XP hunts, consider every source-supported target
through the active character's `+5` level band. The live `consider` response,
exact source identity, route, crowd state, and source hazards decide admission.
Target hitpoints, weapon output, Sanctuary, damage-window estimates, and
equipment projections are observation/report evidence only; they must not make
a plain target ineligible or trigger an automatic flee. Preserve source
specials and aggression hazards, identity and isolation checks, provisioning,
movement and recovery checks, and the character's own health withdrawal floor.
Historical rejection records remain evidence for their exact target and boot;
they are not permission to reject an otherwise valid current target merely
because an old predicted output estimate was unfavorable.

## Commentary And Discord

At the start of every assistant turn, before commentary or other tool work,
append the newest visible user message verbatim to `DEVELOPMENT_CONVERSATION.txt`.
Repeat this after interruptions and context compaction; do not assume the newest
visible message is already recorded.
Append every visible assistant update and final response before displaying it.
Do not append internal goal continuations or injected environment context as
user speech. Never rewrite this append-only file or replay historical entries
to Discord.

Append the exact message through standard input. The helper reads the pipe's
UTF-8 bytes directly, avoiding Windows Python's default console encoding:

```powershell
$body = @'
Exact update text
'@
$body | python tools/conversation_log.py append --speaker "CODEX COMMENTARY" --body-stdin
```

Publish the exact returned header and the same body. Use `USER` for user turns
and `CODEX FINAL` for the final response. Headers must be exactly:

```text
[YYYY-MM-DD h:mm:ss AM/PM NZST] CODEX COMMENTARY
[YYYY-MM-DD h:mm:ss AM/PM NZST] USER
[YYYY-MM-DD h:mm:ss AM/PM NZST] CODEX FINAL
```

Use current Pacific/Auckland time, literal uppercase AM/PM, and the helper's
timezone label. Never nest another timestamped speaker header inside a body.
Provide informative progress updates about every 30 seconds during long work.
Validate format with `python tools/conversation_log.py validate`.

Keep the separate streamer in `--new-only` mode with historical replay disabled.
Do not kill it during gameplay-worker cleanup. Never reset its offset to zero.
After a logging repair, verify the new USER record exists locally, the streamer
logged successful USER delivery, and its queue is empty at the source EOF.
An absent local USER record cannot be repaired by restarting Discord delivery.
The preserved instruction archive contains the full no-rewind, timestamp,
content-deduplication, and at-most-once delivery contract; consult it before
editing the streamer. Launch background helpers hidden, without console windows.
Read live results before drafting numerical claims. Do not combine an unread
result query and a guessed commentary reward in one tool call. Timestamped
updates describe evidence already returned; correct mistakes append-only.

## Authorization And Fail-Fast Behavior

### Combat State Ownership

DD4 source `merc.h` defines `POS_FIGHTING` as 6, and `update.c` reports that
position through `Char.Vitals`. Fresh valid positions 0-7 update the root
character state's combat flag; only 6 marks fighting. Valid nonempty
`Char.Enemies` also marks combat, while a valid empty snapshot clears combat
and the target. Explicit nonfighting positions clear the target too.
Do not derive target identity from posture or an ambiguous enemy list.
Missing/malformed position or enemy data does not prove a transition;
partial vitals must not revive combat from a retained position 6.

Runs **16850/16852** exposed position 6 and nonempty enemies persisting with
`in_combat=False`; neither observation previously set the flag. This live-state
correction leaves the 20% plain-target trigger, controller admissions and loss
ledgers unchanged. Historical evidence is not rewritten. Focused cases compile
and await October 11's regression batch; fresh live proof is tracked separately.
Run **16862** observed position 6 and `in_combat=True` at **762/767 HP**, then
position 4 and `False` at the healer after a **1,628-XP** kill. Its objective,
safety and farewell confirmation were independently positive. This verifies
the live flag transition; it does not replace the pending negative-case tests.

Run **17229** reached **153/831 HP (18.4%)** with the target at 121 HP. The
near-dead finisher calculation lowered its temporary withdrawal floor below
20%, despite a 138-HP source critical estimate; the next hit dropped Dorrik to
27 HP, where the ordinary reserve restored the 20% trigger. For source-proven
unarmed targets without specials, the 20% floor is now applied before finisher
grace. A focused case reproduces those exact values; compilation passes, and
the case awaits the next daily regression batch. Do not retry this target
without the verified regression and fresh policy admission.

### Food Supply And Failed-Fight Baselines

At a noncombat healer checkpoint, a needed current-band food reserve may prefer
the existing Bakery executor when fame is known and nonnegative, the current
source pie is plain nonpoisonous food, and the selection budget includes two
source-cost pies plus the current flight allowance. Preserve city-shop blocks,
cooldowns and the no-consecutive-restock rule. This is a purchase preference,
not a price guarantee: live stock/quote, capacity and route checks still decide
the order. Unaffordable or blocked characters keep the existing source-food path.

Before an exact-source withdrawal, retain a compact output estimate from the
currently worn combat gear. Commit it only on the matching explicit XP-loss
event. Target-HP evidence keeps the old planned ceiling separately and uses the
higher baseline for improved-output revalidation. This is source-estimated
output with observed equipment, not measured damage. Legacy same-weapon health
or damage-window failures lacking it cannot reopen merely because a later
checkpoint wears combat instead of recovery gear. Keep consumed markers and
all old losses; do not rewrite historical rows or alter combat permission.

### Inventory And Combat Text

DD4's source `update.c` builds Telnet inventory strings using colour-converted
descriptions. Raw ANSI escapes can make the captured JSON nonstandard. Stored
item-objective parsing removes complete ANSI sequences before standard JSON
decoding, preserving quantities and distinct entries. Incomplete escapes and
malformed structured JSON are not item evidence; raw `[#ID]` descriptions remain
single entries. Numeric zero is not the default quantity one. An exact affected
completed summary may be repaired with `refresh-run-summary RUN_ID`; never
rewrite transcripts or refresh the whole database automatically.

Direct attack lines may contain a possessive mobile name, such as
`Teacher's last student misses you.` This is not an attack by `Teacher`.
Disambiguation requires the complete current source name; ordinary possessive
weapon/spell attack messages and genuinely additional attackers stay in force.
Parsing does not authorize a fight, identify an instance, erase XP loss, or
reopen a failed policy. New cases await the next available regression allowance.

### Bounded Logout Confirmation

Normal starter workers must read after a dispatched `quit`, for at most five
seconds, and capture the exact complete source reply
`You bid farewell to the Dragons Domain.` in `logout_confirmation`. The
session owner retains a compact receipt; canonical events retain final text
and GMCP. Split text, ANSI and complete DD4 prompts are handled incrementally.
Chatter does not extend the deadline. A refusal, bare EOF, partial farewell,
send/read failure or timeout is visibly unconfirmed; never reconnect, repeat
`quit`, or issue a probe to repair it. A confirmed farewell proves logout only,
not objective completion or a safe hunt. Death and XP-loss outcomes still win.
Cached historical summaries without this receipt remain unknown; do not
rewrite history or invalidate every summary to populate the new field.
The exact failed-underwater cleanup remains separately source-gated; neither
confirmation path permits a new field endpoint or logout in Purgatory.

Run 16744 exposed a duplicate-login filter fault, not incorrect DD4 carrying
data: flight expiry refreshed identical room metadata except exit costs while
retaining `arrival.kind=login`. The raw packets correctly reported 38/38 and
five loose vines after a drop, but quarantine suppressed them. Admit only a
complete, prior-matched same-room snapshot with valid nonnegative integer
cost-only changes; retain destination, door/state, identity and all malformed/
foreign guards. An existing quarantine is never cleared by this allowance.
The room baseline is connection-local and copied, not shared with event data.
16745 verified acknowledged 38/38 to 37/38 cleanup and flight renewal, not the
exact expiry boundary; its focused cases await October 11.

The ready, registered Midgaard fountain preflight at room 3005, water steps
1-3 and outbound index zero, may retain applied combat gear through movement-
only checks. Require the source recall origin 3001, readiness, existing health/
mana gates and no return lifecycle. No new travel or combat permission follows.
A return at healer 3054 retains already-applied recovery gear after waking;
ordinary recovery readiness still gates completion. 16747 verified fountain
fill/drink without swaps and a single healer sleep, then stand/save/quit.
The original near-full-movement fountain boundary remains unproved live.

An explicitly registered required-loot stop may inspect one reset-ambiguous
carrier instead of demanding a second mob that may not be present. Require an
exact live instance, the existing source identity check, a unique source object
name, and an audited worn reset sufficient for the missing quantity. The
five-second `look #<instance>` reply must finish at a prompt and show the exact
source description, target health, and the required item in equipment; neither
description mentions nor peeked inventory count. Bind the receipt to room,
instance, mobile, visit, missing quantity, level and boot; expire it after
twenty seconds and invalidate it on movement. Keep the real mobile count and
every crowd, consider, health, combat, loot and retry gate. At most eight
inspections run per session, with no same-instance/visit retry. Only the daycare
ring stop opts in. October 10 cases compile but await the next daily batch.
Required-loot cleanup fixes its session budget from the initial observed item
deficit, including any existing overload, with at most eight disposals. Keep
the source-identified redundant-item selector and drop/sacrifice/inventory
acknowledgements. A missing capacity change never expands that fixed budget;
departure still requires fresh sufficient capacity. Run 16700 exposed the
old one-item budget stopping at 38/38 after repairing a one-item overload.
Each cleanup phase now accumulates its own bounded reply rather than using the
latest Telnet chunk. Require complete drop/sacrifice lines and inventory's
header/count footer; healer chatter is not an acknowledgement. A pending phase
keeps the route open and times out visibly after five seconds. Run 16706 exposed
the old premature logout; run 16710 subsequently confirmed a delayed flask drop,
sacrifice and inventory audit before actual departure.

`HealerPouchStorage`, owned by the recovery controller, may first audit an exact
structured worn pouch at room 3054. Only an observed empty pouch admits one
source-candidate potion group, at most four individual placements, bounded by
the worst candidate weight and source container capacity. Require each exact
put reply and a fresh text/GMCP count reduced by the acknowledged quantity.
Every reply has a five-second deadline. A nonempty pouch or ordinary release/fit
refusal ends this optional storage attempt without claiming a slot. Record
`storage_only`: ambiguous potion effects remain unknown and quaffing is not
authorized. Do not nest containers or alter the combat reserve ledger from
storage alone. Run 16710 confirmed two clear potions stored and 39/38 to 37/38
capacity before one redundant flask was sacrificed; the water skin and gear
remained. Ordinary source-unique drink-vessel cleanup requires another carried
vessel whose every source variant is plain refillable water. Retain the last
water vessel of each prototype; an ordinary nonwater vessel needs no reserve,
including its last copy. Poison, ambiguous prototypes, protected gear and
keyword collisions remain excluded. Contents are not inferred safe to drink
from prototype values; only disposal is admitted. A colliding default word may
use another actual source keyword only with complete source-known inventory
and no matching peer prefix. Unknown descriptions close this selector. Run
16849 live-confirmed `drop shot`, sacrifice and 38/38 to 37/38 carrying relief,
then purchase/use of flight for 141 copper, without changing the audit budget.

`HealerCarryingCapacity` now owns the shared required-loot and flight-shop
preflight. A flight purchase normally reserves one free item slot before
leaving room 3054; existing overload counts against the fixed eight-disposal
maximum. If no ordinary safe relief item exists, one exact source-identified
worn Mud School diploma (#3715) may be recorded as a destination relief plan
only when dropping it covers the measured deficit. At the Magic Shop, require
DD4's exact capacity refusal before removing and caching the diploma, retry the
purchase only after the acknowledged drop, and restore it before departure.
Preserve the last carried food reserve; only surplus food or urgently needed
food may be consumed for capacity. The plan is not a free slot until the live
shop rejection and recovery flow confirms it.
After an aborted preparation starts healer logout, the logout controller owns
recovery instead of alternating with generic departure recovery. Ordinary field
returns retain the 90% movement reserve, runtime-boundary returns retain their
separate 40% reserve, and health/mana requirements remain unchanged. Sleeping
waits continue reading live output; a preparation correction does not reopen
the failed route or authorize a new departure.
Drop/sacrifice/inventory replies and five-second state confirmation remain
mandatory. Record the compact cleanup receipt and separate purchase failure
causes. Capacity is not insufficient money. For a legacy purchase outside the
eight-segment tail, inspect one exact latest purchase among at most 256 segment
rows and fewer than 256 complete canonical events. Require actual `buy light`
carrying replies and reject funds/reputation evidence; preserve run/segment
provenance and all cooldowns. Failed historical rows remain unchanged. These
new cases compile but await October 11's regression batch.

Runs 16720-16723 exposed four empty liquidation visits after the successful
sale in 16719. The retained signature was unchanged, but subtracting the worn
I.Q. Vine namesake from its baseline made carried duplicates appear new.
Compare the exact signature first; apply the legacy inventory-to-worn
adjustment only when it differs. A later changed signature may reopen sale
planning, never a blind sale of an ambiguous instance. Fresh selection after
this correction left liquidation and resumed gear/XP work; the focused cases
compile but remain unrun until October 11.

Newly retained duplicates then exposed a separate completion fault in
16728-16729: no-sale plans kept the previous signature. Record
`campaign_liquidation_completion`, bound to the exact run, only after finished
planning at healer 3054 with no pending/rejected action, failure or runtime
interruption. Its completed retention may update the baseline without profit
or an achieved objective. Legacy no-op repair must preserve this explicit
receipt. Run 16730 verified the new baseline and fresh 16731 resumed XP work.

Runs 16750/16752 exposed repeated vine-shop trips: the refusal pattern excluded
internal full stops and missed `an I.Q. Vine`. Share the pattern in `shops.py`
between live policy, bounded historical recovery and reports. Accept refusals
after value or sell, requiring a complete line from the recovery controller's
2,048-character command-local buffer; clear it on the next shop command and
after a recorded refusal. Preserve existing alternate-buyer, donation and
retention checks. Standalone 16763 sold one vine for one copper, recognized the
next refusal, and immediately returned instead of retrying that buyer. Its
alternate route failed after three city waits: failed/unknown/safe, not completed
cleanup. It saved at healer 3054 with no combat or XP change. Split-packet and
negative cases compile but await October 11; no historical summaries were rewritten.

Run 16702 falsely called the intended buck an extra attacker because the
dispatched keyword was `deer` but combat text said `The buck`. Ordered GMCP
recorded only source mobile 19039 in room 19132; flee lost 592 XP, offset by
97 damage XP. Keep execution success, objective not-achieved, safety loss and
the closed policy. The combat controller may reconcile that flag only for an
already-opened, unfinished fight with one raw current-room enemy, matching
source VNUM, canonical name and room description, the exact registered reset
room, and one selected instance without a conflicting selector. Preserve real
crowds and every combat limit. Record at most eight aliases per session. This
repair compiles but has no fresh live proof; focused cases await October 11.

For source-ranked circuits, record the exact source policy, mobile VNUM,
registered room and current live opponent in the combat controller before a
flee/recall clears identity. Commit that record only after an explicit positive
XP-loss event. Successful earlier kills must not clear the failed stop, even
when partial damage XP makes the trip profitable. Across connections, compare
`campaign_xp_loss_total`; identical per-run penalties are separate losses.
Missing legacy identities may be reconstructed only from linked runs in the
existing eight-segment tail, at most four loss events and 128 preceding events
each. Require exact GMCP enemy, actual room/arrival and dispatched withdrawal;
shared names, absent targets and safe aborts never prove a failed fight. Keep
secondary-stop counts when phase indexes omit their parent circuit. This repair
closes losses; it creates no new retry permission. October 10 replay cases are
written and compile, but remain unrun until the next daily batch.

Departure `where`/adjacent scans retain `fastwalk_recovery_ready` until the
first actual outbound command. At the exact verified safe route origin,
already-applied combat gear may remain during movement-only checks when health,
mana and other readiness gates pass. A blocked scan still aborts normally;
this is neither a field sleep location nor relaxed combat/travel admission.

Automatic source absence/no-progress fallback is not a route-program retry.
Do not derive `allow_route_program_retry` from a cooldown-rotation flag; doing
so offered an obstructed productive route only for the final dynamic-hazard
guard to stop it before connection. Preserve the saved route result and useful
kill history, select other candidates normally, and retain the final guard.
Only an existing exact revalidation or explicit `--retry-stalled` can reopen
that source-validated preflight. New focused cases await October 11.

For a recently productive plain hunt, a completed clear city observation may
arm one exact-policy/level/boot clearance even when a different policy spent
the legacy global receipt. Require a current-version linked summary-confirmed
objective kill in the existing eight-segment tail, unchanged source and total
losses, current XP matching that recovered hunt's end, and a later successful
no-travel three-wait block followed by a changed clear locator. Preserve the
old receipt under `superseded_clearance`, retain the blocked-policy ledger,
and persist `campaign_productive_city_clearances` before opening the worker.
Admission still checks route, provisions, source output, useful XP, flight,
health, crowd and loss; repeat fresh locator, exact instance and consider live.
The receipt binds the prior result and XP/loss to its pending ledger entry and
is consumed before dispatch. This cannot reset a spent same-policy clearance,
combat loss, failed target check or changed source. Cases are saved for October
11, not an additional October 10 regression batch.

Live run 16671 consumed that productive receipt before connecting and crossed
the formerly blocked city route. Its source-12041 citizen had 915 HP versus
624 on the previous successful instance. The fight withdrew at the 20%
trigger, reached 18.98% HP during flee, lost 551 XP before damage XP reduced
the net loss to 188, and returned recovered to the healer. Record safety=loss;
the combat failure and same-policy clearance remain closed. Run 16672 acquired
no sanctuary; 16673 renewed flight for 141 copper. Checkpoint 49712 is level
30 with 662,990 XP and 6,060 remaining to 31. No level transition is proved.

`combat_actions.preferred_timed_damage_skill` compares already-admitted kick
and headbutt using positive observed proficiency and DD4's strict percent roll.
Both have blunt/nonmagic resistance flags; successful headbutt waits six
seconds, failure three, and kick two. NPC ordinary attacks are not suspended
by this wait. Include second headbutt only from its observed proficiency.
Planner and live dispatch share the choice; unknown inputs keep prior ordering.
`CombatCommandWindow` recognizes only the exact target's damage acknowledgement,
splits complete prompt prefixes, and retains those waits plus one input pulse.
The failed-headbutt short wait requires its exact miss without a preceding
success message. This never reopens losses or changes encounter admission.
At checkpoint 49713 the next launch stopped before login because the source
frontier remained unavailable and the sanctuary recheck was spent; there was
no new run or XP change. Timing/ranking cases compile but await October 11;
the new rotation is not live-proved yet.

### Verified Level-31 Transition

Checkpoint **49727**, last run **16680**, records Dorrik at level **31 Knight**,
**670,744 XP**, **57,556 XP** to 32, **18 QP**, alive/noncombat at healer 3054.
Runs **16674/16675/16678/16679** killed the Catacombs sentinel and Mirror Realm
buck for **2,074/2,231/1,591/1,858 XP**, respectively. All four record
success/achieved/safe with no flee or XP loss. Including maintenance visits
**16676/16677/16680**, the seven-run total is **7,754 XP** in **727.90 connected
seconds**, approximately **639 XP/minute**; development/planning is excluded.
Selling and banking have unknown objective outcomes; the ring objective was
not achieved. Do not relabel these maintenance runs as successful item goals.

`greeting_echo_programs_only` admits only greeting triggers, numeric percent
conditions, at most four programs/32 commands/four nested random branches,
balanced control flow, and non-CHAT local echoes. Unknown commands, casts,
attack/transfer actions and malformed scripts remain closed. It is a source
behavior proof, not route or combat permission. The sentinel retains the exact
existing bouncer route and fresh source/loadout/identity/isolation/consider gates.
Its independent contract was never part of the failed three-target parent.
`completed_single_target_hunt` accepts only the exact current-version safe,
achieved linked summary with one useful source-tagged kill, matching boot and
recorded start/end source revisions, terminal level, and unchanged encounter
loss totals. An opted-in one-level
transition also requires its exact summary levels and observed gain, preserving
the original source-policy tag. Later unrelated losses cannot erase that
success; current/prior exact target quarantines remain authoritative and loss
totals cannot rewind. A completed productive independent hunt may repeat beyond
the initial three-kill discovery cap, retaining its one-kill visit limit and
every fresh source/live check. Absence, crowd, loss, or failed objective cannot
qualify. Historical rows and parent failure ledgers are not rewritten.

`hunt_efficiency.py` compares at most eight linked completed visits using their
actual net XP and full run duration, including safe zero-progress visits to the
same route. It deduplicates runs and rejects old summaries, malformed timing,
unlinked outcomes and token rewards. These are route-selection observations,
not a controlled class-balance experiment or combat permission. A proven
registered current-band hunt may compete before the generic frontier is empty;
an unmeasured generic choice does not automatically suppress the proven route.
An already-selected multi-kill circuit keeps control: single-target receipts
cannot establish its comparable rate or justify replacing it.
Persist the selected comparison's run IDs and rates in its segment start.
Fresh complete source route/loadout audit may admit historical success recorded
under an older revision; its own start/end revisions must still match, and no
historical revision or loss ledger is rewritten. Food, recovery, flight,
QP/fame, current source and every live targeting/consider/output gate remain.

Run **16679** live-confirmed the level gain, 26 HP, 17 mana, 10 movement and
3 physical/2 intellectual practices. Repeated kicks were dispatched in these
fights; this does not establish comparative balance or prove every timing edge.
No sanctuary, optional quest, reboot wait or roster rotation was needed.
Compilation passes; new script/selection/timing cases await October 11, not
a second October 10 regression batch. Next: fresh level-31 training and useful
XP toward 32. HERO and full class/race coverage remain unproved.

### Area-Local Recall Recovery

DD4 `do_recall` uses the current area's `#RECALL` when recall index zero is
selected. `recall set 0` does not force Midgaard, and word of recall uses the
same rule. The Ota'ar Dar market's destination is room 27347. Run 16462
confirmed Dorrik's Knight identity but ended there after the old return routine
incorrectly expected Midgaard. It gained no XP and incurred no loss.

The maintenance-only `AreaRecallEscape` owns one bounded return attempt. From
27347 it may visit shop 27331 via 27341/27336/27337/27332 and purchase exactly
source object 27292 (goblin shark pie) using a live quote, exact selector, level,
inventory confirmation, and 100-copper reserve. Its spell level is 40; the
object's usable level is 30. Source mobile 27246 is a separately audited
economic risk on this shop route: non-aggressive, unprogrammed, `spec_thief`
only, with the exact ordinary loincloth/dagger resets. No combat is authorized.
Any other diagnosed shop-route hazard closes the exception.

Require independently verified water breathing or an explicit `update.c`
survival exemption, fresh flight, at least 95% HP, 30 movement, observed infravision (or
clairvoyance), and observed sanctuary before the escape. Follow the exact
source/live exits 27347 up 27647 up 27132 up 27071, scanning before each dark
destination. Reject every one-room sighting, unknown/incomplete scan reply,
closed exit, hidden/invisible source attacker, changed attacker set, changed
reset or special, and source/live route mismatch. Distant sightings do not
occupy the immediate destination. Only at source-recallable Undersea room
27071 may the routine recall to 3001 and continue north to healer 3054. Cap
the routine at thirty commands and every response at five seconds. Store
`campaign_area_recall_escape` evidence. This is recovery, never hunt admission;
live success remains unproved until an observed healer return.

### Ota'ar Dar Favour Gate

The Ota'ar Dar gladiators hold a character in the arena until all five distinct
favours have been collected. Treat this as a hard live gate, not a normal
arena completion condition: retain arena control through the remaining
gladiator sequence, verify each current-reboot favour receipt, and do not
issue the exit route, generic recall, logout, or maintenance detour while any
favour is missing. A saved receipt from an earlier DD4 reboot is not valid.

Trainer visits record `subclass_selection` independently from execution and
safety. A requested subclass in the profile is not proof: require the final
observed character identity to match. New recovery and reporting cases are
queued for October 8; do not exceed October 7's spent regression allowance.

Run 16463 reconnected in Purgatory before using this new escape controller.
It retrieved the corpse, exited the portal, restored and audited gear, and
returned to the healer at 696/702 HP. The gap from the previous checkpoint was
-226 XP. `update.c` drains air and applies drowning damage in sectors 8/12
regardless of flight; that is a likely cause, not directly observed death text.
Do not label the old foreign-room disconnect a safe recovered return.
On a live failed noncombat room-27347 session, only the exact source/no-mob
logout gate may send `quit` once before closing, with five seconds each for
send and farewell confirmation. Record `failed_local_recall_logout`; retain
the original failed execution. `do_quit` saves the character. Missing source,
combat, enemy evidence, an uncommandable character, or Purgatory forbids this
cleanup. It is not generic permission to quit from arbitrary field rooms.

Before calling an autonomous attempt pre-connection or retrying its policy,
check the process list, `show-campaign`, `show-runs --limit 4`, and the exact
transcript/current state. A campaign segment with no `run_id` or zero recorded
commands does not prove that the run issued none. If the worker has stopped,
recover while its segment is still running with
`recover-runs --campaign-id N --character NAME`; this binds a unique matching
run and preserves its measured execution, objective, and safety outcomes. Do
not repeat a target after a live output-budget flee without new source or live
evidence clearing that gate. Failed-segment source-loss repair must merge the
exact starting campaign metadata with the terminal state, and requires a linked
run, nonzero command count, and explicit XP-loss evidence. An orphan or safe
abort cannot create a target quarantine.

Run reports reconcile `completed_kills` from ordered events with the compact
`mob_kills` index. If a recovered or interrupted run has a kill in that index
but not its cached summary, use `refresh-run-summary RUN_ID` to rebuild exactly
that run's summary and reconcile its indexed outcomes; ordinary `report` stays
read-only. Execution, objective, and safety outcomes remain independent.
Campaign segments inherit refreshed run outcomes unless they explicitly own a
campaign-specific objective. Only objective-eligible kills count toward a kill
objective; route-gate and below-band kills remain visible evidence but never
satisfy progression.
Health minima must include ordered `vitals_changed` and `prompt_seen` pairs,
not just full-state checkpoint boundaries. Require each observation's own
valid HP and maximum; do not pair a partial update with a guessed maximum.
This keeps compact storage without hiding damage healed before the end.
Exact run summaries may be refreshed; do not force a full-history rebuild.

Keep the DD4 source checkout at `runs/dd4-source` current with `origin/master`.
Update it only after every live worker has finished and `git status` is clean.
Use a fast-forward update, then parse the full world and verify representative
pilot-route rooms and prototypes before relying on its new revision. The
October 7 refresh moved from **48cb5a6** to **bbd55b1**; parser smoke found
13,052 rooms, 4,125 mobiles, and 6,138 objects. No regression suite was run.
On October 8, with no live worker and a clean source checkout, the source mirror
fast-forwarded from **bbd55b1** to **7953a00**. Full parsing returned the same
world counts. The refreshed source confirms club **1521** has one ground reset
in room **1573**, and the recall-to-reset route is 18 steps / 71 ground
movement, with no flight requirement. Its low-level program hazard is mobile
**3064** (`greet_prog`, `mpkill`); the direct-loot placement now retains the
registered live `where` preflight and route-room list. Live pickup is unproved.
The new source commits also changed stun/fall and undead-aggression handling;
the live server's deployed revision is unknown, so do not count those changes
as live evidence.

On October 10, after confirming no live worker and a clean source checkout, the
source mirror fast-forwarded from **6d77df8** to **971d8e7**. The full parser
again returned **13,052 rooms, 4,125 mobiles, and 6,138 objects**. The refresh
did not change `const.c` or `pre_reqs`; it updates the working source baseline,
not live-server behavior. Those skill-tree files also match the bundled
analysis baseline at **7953a006**, so the class-priority report remains current
through this refresh.

On October 11, with no live worker and a clean source checkout, the mirror
fast-forwarded from **4c039fa** to **26749cd**. Full parsing verified **13,052
rooms, 4,125 mobiles, 6,138 objects, 7,749 mobile resets, and 1,430 object
resets**; the three representative Midgaard, Kerofk, and 36 Chambers rooms
loaded. This commit adds `turn undead` to the Divine Magiks trainer group and
increments `MAX_SPELL_GROUP`; the prerequisite files did not change. The
bundled prerequisite snapshot remains valid for its unchanged data, but teacher
availability must still come from the live learnable listing. Source changes do
not prove the running MUD has deployed them.

Startup productive-history repair uses the already-loaded normalized,
same-boot kill ledger alongside the eight-segment JSON tail. Require an exact
source-policy tag, objective eligibility, useful-band membership, no route-gate
flag, and a meaningful latest recorded kill reward. Maintenance visits cannot
erase older proven hunt identities merely by pushing them outside that tail.
Do not expand historical event or checkpoint reads. Normal loss, current
low-reward, crowd, route, cooldown, and live checks remain authoritative.
After a previously productive route returned before its opener solely for a
missing sanctuary reserve, fresh supply may restore ordinary kill-cap repeat
admission only with an observed viable same-boot result, no target-loss record,
and no absence, crowd, route, mismatch, unattackable, or below-band evidence.
This repairs a prerequisite, not a failed fight or a consumed route marker.
Only that exact repaired prerequisite is removed from the soft no-progress
rotation list; ordinary source and live admission still decide dispatch.
Run 16454 live-proved the repair with a protected Ki-Rin kill, +1,017 net XP,
level 29 to 30, and safe full healer recovery. Run 16455 resumed that checkpoint
in a new process and gained one defense-knowledge percent, without quests.

At healer room **3054**, a live food or drink need with the matching supply
already carried takes priority over movement-rest sleep. Wake, eat or drink,
then resume recovery. A repeated stand/sleep cycle while supplies are usable is
a controller failure, not productive waiting.

October 11 runs **17274/17275** exposed a reconnect gap: GMCP reported hunger **2** at healer room 3054 with six pies carried, but the policy only armed its food need at zero and left on a loot route. `StarterPolicy` now treats hunger or thirst at **8 or below** as a recovery need only at a safe, noncombat healer; at that low threshold it may consume the last carried food. Run **17276** live-verified waking, eating two pies to DD4's “You are full” response, and drinking from the water skin before leaving for the warehouse hunt, which finished safely for **2,305 XP**. `test_low_positive_nutrition_at_healer_preempts_loot_travel` covers the food and drink wake/consume path. The touched Python files compile; pytest is deferred because today's regression batch has already been used.

Combat swiftness estimates consume the revealed GMCP `Char.Stats.swift` total.
DD4's `GET_SWIFT` already includes the DEX and enhanced-swiftness bonuses;
adding either again overstates automatic attacks. `number_percent()` rolls
1..100 and the attack check is strictly less than the score. Use the clamped
score-minus-one probability; hidden/sentinel data grants no inferred bonus.
Digging differs: subtract the practiced enhanced-swiftness contribution, but
do not remove or add the DEX contribution a second time.

NPC normal-hit estimates mirror `fight.c:one_hit`'s level bands: add level/4
below 30, level/2 below 65, otherwise 3*level/4, before the weapon multiplier.
Peak, expected, critical, and sanctuary calculations share that base; preserve
per-hit damage-modifier scaling and sanctuary-before-critical rounding.
For an exact, source-confirmed single unarmed target with no special, ordinary
combat withdraws at 20% health rather than stacking two observed-hit reserves.
This accepts more risk only for that plain-target case; poison, multiple
enemies, explicit stop and route floors, and all live identity, consider, and
damage/output gates remain in force.
`mobile_loadouts.single_weapon_loadout` may extend the independently prepared
single-weapon defense probe to passive singleton wanderers and ordinary reset
armor/instruments. Require one global reset/capacity, exact wield identity, no
aggression, scripts, scavenging or specials, and a complete ordinary loadout.
For common-rank gear, `db.c` uses prototype level minus two: under 40 (or with
the weak flag), `random_qnd` keeps existing affects within 25 percent. Round
positive damage and HP ceilings upward; fixed gear keeps exact affects.
Reject strong/fickle randomisation, unknown/critical/swiftness affects, poison,
spell items and additional weapons. Add damage after the NPC wield multiplier
and before its damage modifier; preserve corrected raw peak/critical and HP
ceilings in the live hunt stops. Fresh training, equipped defenses, full health,
finite damage output, isolated identity/consider, route and loss gates still
apply. Target sanctuary halves ordinary/opening source output before finite
action planning; unmodelled target protection, battle aura and globe close
this new admission. Wandering permission does not widen the eight-room blind search or
reset a saved failure. New regression cases await October 11; this expansion
has no live combat proof. Run 16657 found the Highlander and rejected its
below-band consider, returning to the healer without combat or loss. That
negative evidence stays closed; the later sanctuary correction grants no retry.
`populations.plain_bounded_population` supplies a source proof for the existing
capacity-research isolation check: two to four passive sentinel/stay-area resets,
one per distinct same-area room, with the same global maximum of two to four.
Reject scripts, specials, fear/confusion/noncorporeality, randomized reset
rooms, unknown equipment/objects, weapons, and spell items. The capacity-only
rejection remains recorded. Post-loss no-reserve admission must independently
pass the existing incoming peak, observed defense, output, route, and exact
policy-loss checks. Audited route-program admission receives the bounded
capacity-endpoint flag only from this source proof; it retains its own route
hazard preflight. The live executor still requires one exact isolated useful-XP
target before combat, with the ordinary finite search and action budgets.
That source-proved plain population may retain a nominally current-level
candidate whose source load fuzz reaches plus two only when the existing
post-loss no-reserve peak/defense/output proof passes. It does not raise the
live plus-one ceiling or bypass observed below-band, movement, kills, routes,
or saved failures. Source-less and all other capacity research keep plus one.
`plain_bounded_mobile_population` shares the complete prototype/reset audit
with candidate admission. For its wandering, ordinary XP targets only,
`_below_band_population_locator_allowed` may finish the current registered
search after a weak individual is rejected. Require exact source/policy/room,
awake noncombat state, known sufficient vitals, food/water, an isolated target
contract, and unchanged finite locator/kill limits. Exclude required-item,
quest, sanctuary/familiar, armed and special probes; ordinary harmless drops
are not required-item objectives. Preserve the negative consider and sightings,
and skip same-mobile rooms already queried in this visit. Each new target still
needs its own live audit; exhausted routes close without a same-room recheck.
An empty stop following the weak member retains this search context only when
its inspection is complete, it is explicitly skipped as absent, and the visit
contains an exact source/policy weak-member receipt. Seeded historical skip
names alone do not qualify. Keep crowd, mismatch, unattackable, loss, vitals,
and locator-limit stops authoritative. Run 16656 exposed this premature return;
its corrected handoff is not yet live-proved and grants no new campaign retry.
Reconstructing run 16648's observations with current source selected the
remaining registered 16471-to-16479 route on refresh eight. This is offline
evidence only; no historical result, saved exclusion, or live kill was changed.
New cases compile and await October 11.

For the same source-proved plain population, a useful objective kill may start
the first post-kill `where` query after an outbound interception skipped the
initial locator. Ordinary harmless reset drops do not turn XP hunting into a
required-item objective. Existing damage-window/unprotected-HP-fuzz checks
remain attached to every fresh isolated target; lookup grants no attack
permission. Require exact policy/mobile kill identities, reward above the
current-level-times-ten below-band floor, latest positive consider, known
awake vitals, provisions, and no combat, loss, hard abort, or runtime return.
Continuation health uses the source upper-load peak round, one extra critical
hit, and the 20% withdrawal reserve, with the ordinary continuation minimum.
Carry that entry requirement to the relocated stop without changing its
separate combat withdrawal floor. Retain weak-instance receipts only when
each has an exact-policy source sighting; skip those rooms and all same-visit
checked destinations. A query needs no old positive locator, but its reply
must positively identify a registered, unsearched safe destination before
movement. Preserve the finite locator, population, and kill budgets. Required
loot, sanctuary/familiar objectives, protected/special probes, and historical
cooldown changes remain excluded. New replay cases compile but are unrun.

Ordinary XP routes have a separate economic-only admission in
`economic_hunts.py`. Require a passive, unarmed singleton sentinel target, an
otherwise eligible source route, and a known whole purse no larger than 1,250
copper-equivalent. Every economic actor must have exactly one global singleton
reset, only `spec_thief`, no aggression or programs, and an audited ordinary
loadout without spells, poison, positive damage bonuses or unsafe randomisers.
Its upper source level cannot exceed the player. DD4 steals 1-20% per attempt;
250 is the maximum single attempt at this purse ceiling, not an aggregate loss
cap. Retain the original economic rejection and actor identities in the saved
candidate. Recheck source and current money before outbound actions; failure
returns home. This authorizes no combat with the thief, crowd exception, saved
failure retry or quest waiver. Existing live isolation, route, consider,
training, health/output, finite-action and return checks still apply. Mirror
Realm buck/moose source candidates pass this narrower admission. Run 16658
proved the buck kill for 2,084 XP without sanctuary, a 50.6% lowest observed HP,
and safe healer return. The moose failed live consider, so the full two-target
objective remains not-achieved. The next visit's finite city waits failed to
clear the route; retain that block. New regression cases await October 11.

The economic-only allowance may also accompany an independently source-proved
plain population of two to four distinct, same-area resets. Remove only the
economic rejection; retain `status=reject` and the capacity-only rejection so
the existing isolation research, damage, output, loss and finite-search gates
remain authoritative. Audit every target reset's objects. The bounded route-
program preflight may accept only the explicitly audited economic actors, and
noncombat locator paths receive their exact VNUMs through the existing source
economic-transit audit. Unknown, armed or changed locator actors remain closed.
The live purse cap still applies before outbound actions, including after gold
loot. Quake's four level-30 Westreen citizen resets pass source preparation
without sanctuary. Run 16664 followed positive sightings, but source identity
remained ambiguous: 12041 and 12042 have the same room description and reachable
rooms, with different source levels. It returned without combat, XP or loss;
success/not-achieved/safe. Preserve that failure, not an absence claim. Do not
infer a prototype from its instance selector or reuse an identical-profile
alias for differently leveled mobiles. New cases compile and await October 11.

`target_inspection.py` resolves a distinct contract: DD4's `look #<instance>`
prints the source mobile's full description before its health line. The parser
now retains that description. A passive, isolated ambiguous target may receive
one exact-instance look with a five-second deadline, at most eight per run.
Require all reachable prototypes to be known, passive, unprogrammed and without
specials, plus a unique complete expected description. Match the description
and named health acknowledgement, not gender guesses or substring keywords.
Keep the receipt under the travel controller, bound to instance, room, stop,
level, boot and source descriptions. It expires after twenty seconds; movement
invalidates it. A known different prototype skips the stop without attacking.
Unknown, partial, expired or changed output cannot authorize combat. Continue
with fresh consider, isolation, equipment, health/output and finite-action gates;
GMCP's post-opener VNUM must still match the intended prototype.

The exact old ambiguity-only visit may receive one
`campaign_target_inspection_revalidation`: require its linked completed run
summary with no combat/kills, unchanged level/boot/source/XP/loss and healthy
healer boundaries, the same candidate/route, and a currently distinguishable
description set covering the recorded source identities. Keep the old result
inside the receipt and in the research ledger. Consume before dispatch; the
new failure remains closed. This never clears crowd, negative consider, loss
or another route failure. Saved replay cases compile but await October 11.
The exact first-generation article-prefix mismatch may receive one revision-2
parser check only from its own completed no-combat segment and bounded
512-event tail. Require the attempted revision-1 receipt, unchanged boundaries,
one dispatched exact-instance look, and a complete source-matching reply within
five seconds before the next command. Preserve `prompt_repair_of` and the
matched response event ID. The matcher now uses the full source short name,
not an article-stripped target alias. Recheck the current instance, source,
consider and all combat gates; revision-2 failures remain closed. Run 16665
proved the actual woman description but incorrectly rejected that reply; it
returned without combat, XP or loss. Its objective remains not-achieved.

Run 16666 freshly identified citizen instance #6752 using the corrected
description matcher, then passed consider and confirmed source VNUM 12041
through combat GMCP. It killed the live level-31 citizen for 2,641 XP without
sanctuary, flee or XP loss, reached a lowest observed 32.3% HP, and returned
fully recovered to healer 3054. Preserve the attempted revision-2 receipt;
this kill does not grant more parser retries or waive another policy's route
gate. Its independent level-100 objective remains not-achieved. Run 16668's
subsequent city-preflight stop was no target attempt and gained no XP.

An admitted temporary-crowd reset must not discard a source policy's confirmed
useful-kill result while leaving its weak-instance exclusions authoritative.
`productive_crowd_reset_result` retains positive evidence only for known same-
boot, positive-consider kills above the below-band reward floor, without fatal,
exhausted, retryable, route, absence or identity failures. Source loss policy
gates remain authoritative. Historical repair lives separately in
`campaign_migrations.restore_productive_population_after_crowd_reset`: require
an already-completed, unconsumed capacity wait, that exact cleared policy, a
source-proved plain population, current full healer state, the latest linked
success/success/safe visit in the existing tail, exact objective kills matching
the already-loaded normalized ledger, unchanged source/level/boot/XP/loss, and
a later successful same-state healer `time` visit. Preserve original outcomes,
weak-instance receipts and the two run IDs. Existing results, new losses or
failures, changed revisions, exhausted waits, and unknown evidence never reopen.
Checkpoint 49664 restored 16652 via time run 16653; ordinary selection admitted
the route. Run 16654's fresh city failure remains closed. New cases compile but
await October 11; no multi-kill live proof is claimed.

When ordinary current-band selection finds nothing, the separate
`campaign_population_search_revalidations` receipt may offer one exact saved
premature population return. Read only the already-loaded eight-segment tail
and its linked compact run summary. Require success/not-achieved/safe, no
combat/kills, unchanged level/boot/source/route/XP/loss, recovered healer
boundaries, one below-band individual, an unspent original eight-refresh
budget, and a live-reported, originally planned, current-source registered
room that was not checked. Keep the old negative ledger and locator evidence.
This is a retryable search, never fabricated productive history. Repeat the
ordinary source, route, output, survival and target-loss checks, then persist
the attempted receipt and segment ID before connecting. Any recorded receipt
closes another repair; fresh live identity, isolation and consider remain
required at every destination. This is not a general cooldown reset.

Equipment valuation uses `GearCatalog.observed_equipment_item` for exact
structured worn identities. Require matching integer VNUM, name, item type,
class compatibility, and an integer observed load level from 0 through 100.
Keep missing-slot/weapon-loss evidence authoritative. Substitute that level
only in a copied source item; bonuses remain source estimates. An ambiguous
carried description cannot borrow this worn identity. `show-gear-sources` and
campaign weapon-upgrade selection share the valuation; a lower-level placement
of the already-worn sword is not an upgrade.

Source hunt-stop preparation checks its own 60-second deadline before candidate
work and throughout destination/relocation loops. Expiry fails visibly before
connecting; it does not grant a target retry. `SourceRouteHazardIndex` belongs
to one unchanged `WorldSource` within that plan. Reuse reset groups, full-world
wanderer ranges, and level-specific special classifications, not route verdicts
or live observations. Discard it after the plan or any source mutation/refresh.
Stay-area navigation may search only the target area, while hazard checks still
use the full source graph and all source-known wanderers. Skipping an empty
combat-only hazard destination changes no permission. Keep the outer deadline
and every route, isolation, consider, output, loss, and live response gate.

`AdjacentRecallEscape`, owned by `RecoverySessionController`, handles one
source-known no-recall room with an open, unlocked, ordinary exit to a safe,
nonrandom land room. Audit source hazards/access and that area's default recall
to 3001. Reject Purgatory, water/air destinations, missing source, combat,
unknown posture, less than 50% HP, or less than ten movement. Verify the live
exit, then dispatch only scan, one movement, and recall. Each reply has a
five-second deadline and exact expected room; a complete immediate-occupancy
or closed-door scan stops the attempt. Distant sightings do not become adjacent
ones. Store `campaign_adjacent_recall_escape` on success and failure, and follow
the ordinary healer return afterward. This authorizes no combat or field logout.
Run 16640 proved the 16459 north 16465 recall 3001 escape after run 16639's
failed return. Its scan showed a clan member three rooms north, not adjacent.
The earlier failed run remains failed/not-achieved/safe despite its useful kill.

`campaign_recall_route_revalidation` binds one useful failed-return hunt to its
immediately following successful `return-home` segment. Load only the exact
policy's latest segment within 256 rows, its sequence neighbour, its compact
kill ledger, and its last eight events. Require unchanged level/boot/source,
an exact recall-only error, original source route, fresh positive consider,
useful objective-eligible kill, no original or recovery loss, and the recorded
three-command source-safe escape followed by healer recovery. Read the hunt's
own terminal state event: inherited campaign abort/consider flags are not that
run's evidence. A pending receipt changes selection only, never historical
execution/objective outcomes; consume it before opening the live segment.
Current crowd, below-band, source, output, movement, and target-loss gates still
apply. A later visit replaces the latest-policy evidence and cannot resurrect
the older receipt. The helper matches saved runs 16639/16640; automatic live
admission remains unproved. Cases in `test_recall_route_revalidation.py` are
compiled but unrun under October 10's spent regression allowance.

The Catacombs fallback stores Martin, Charles, Amanda, Sally, and Paul as separate
mobile objectives. Amanda (9512, reset 9510) and Sally (9514, reset 9514) are
source-confirmed level-30, unarmed, unprogrammed, same-area wanderers without
specials. Adding them does not expand the original three-target parent contract.
A parent-route cooldown from one linked, completed health-floor withdrawal may
leave an untried sibling eligible only when exact source-consider and presence
evidence identifies the failed mobile, with unchanged level, boot, source, and
accumulated losses and no death or route hazard. Preserve the parent result and
loss ledger. Each sibling keeps its own cooldown/loss record, exact source
route, fresh live identity/consider/output checks, and initial one-kill limit.
After another target fails, use that exact linked failure if it matches the
current accumulated-loss total; an older parent failure must not override it.
The exact extra-attacker/duplicated-GMCP abort may also scope its linked loss to
one source target. Require success/not-achieved/loss outcomes, a real combat
and XP-loss event, one useful consider/presence identity, no death or route
hazard, recovered full-health healer boundaries, and the exact current loss
total and segment-linked loss record. A historical positive research result
cannot override that newer loss. This negative scope survives a source refresh
only when the failed run's own start/end revision agrees; alternatives need
fresh current-source admission. Keep every same-level/boot child abort closed
across refreshes unless its separate recorded repair contract admits it.
Paul (9517, reset 9509) is level 30, unarmed, and has no special. Its one
`rand_prog` immediately breaks while fighting and otherwise executes one
`mpecho`. `mobile_programs.py` accepts only that exact five-line control flow,
a numeric chance from 0 through 100, and non-CHAT echo output. Other triggers,
actions, branches, or extra commands remain excluded. Source admission is not
live kill evidence and retains every ordinary hunt gate.
The proven idle-script shape retains ordinary three-step source-safe pursuit
even when a live health probe or protection check is required; those combat
checks remain unchanged. The non-aggressive unarmed no-reserve output gate may
use the same script proof; every source damage, output, reset, loss and live
check still applies. Aggressive or other scripted targets remain excluded.
After ordinary sibling selection finds nothing, one exact safe no-combat
one-step pursuit failure may receive `campaign_idle_pursuit_revalidations`.
Require a linked completed run, positive live locator and target presence,
unchanged level/boot/source/XP/loss, full-health healer start/end/current state,
no consider or combat evidence, and a newly proven three-step safe-room map.
Persist an attempted receipt with the prior run/segment before connecting.
Never clear the old route result, combat loss, or source policy ledger; any
failure or previously recorded receipt closes this one-use repair.
Receipts are sticky campaign metadata. If a terminal checkpoint lacks one,
restore only its exact consumed receipt from the already-loaded eight-segment
tail, with matching policy, level, boot and source. This recovery closes the
repair; it never copies gameplay state or creates new retry permission.
Cooldown ageing retains loss-bearing route results. If a legacy result is
missing, target scope may use that exact linked completed segment's terminal
result only for its recorded loss outcome and matching current loss ledger;
all level, boot, source, identity, and hazard checks still apply. A conflicting
current result takes precedence; never substitute history for it.
An expired parent cooldown never clears its recorded XP-loss fight. A child's
same-level/boot/source failed search remains closed from its exact bounded
segment evidence, including legacy attempts without a research-result entry.
Before-consider Catacombs aborts now record their own route failure and cooldown;
positive `where` presence is not proof of a reached target or a useful kill.
Relocation tables include safe positive-locator destinations beyond the eight
blind stops as origins. Every new origin retains path, hazard, access, and live
identity checks; blind stops and live relocation limits remain eight. This
repairs a missing map origin, not a consumed failed search or combat permission.
After one source-mapped room is rechecked and still lacks a source-ranked
wanderer, the locator may broaden to another non-empty source-mapped label only
when the locator explicitly permits continuation and the target/source VNUMs
match. The alternate leg is still source-routed and bounded by the same
eight-refresh limit; this never authorizes combat without fresh identity,
isolation, consider, output and recovery checks.
After ordinary sibling selection finds nothing, an already-productive exact
registered source identity may receive one `campaign_registered_locator_revalidations`
route check. Require its linked completed success/not-achieved/safe run,
zero combat and unchanged XP/loss within that run, full-health healer boundaries,
same level/boot/source, and the exact missing-origin abort. The final positive
locator must lack a registered origin, and the current audited map must provide
routes from that origin to every endpoint under its old reported labels.
Keep its prior locator decision and result in the receipt; do not clear either
the research result or target loss ledger. Later unrelated XP/loss remains
current and cannot substitute for evidence from this failed search. A recorded
loss for the exact registered or source target closes this allowance.
Selection saves a pending receipt; the segment start consumes and checkpoints
it before opening the connection. Fresh identity, isolated targeting, consider,
health, protection/output gates and the eight-search/refresh limits still apply.
Sticky attempted receipts forbid another automatic check after any outcome.
Run 16634 completed its fresh Martin objective for 1,923 net XP and retained
the attempted receipt at checkpoint 49605. Its ordinary repeat 16638 lost
189 net XP after Caroline joined. The old positive research result is historical
kill evidence, not permission to override the new registered loss. The consumed
locator repair never reopens that combat failure; checkpoint 49610 is recovered.
The higher-band Vampire Catacombs fallback audits each reset separately.
Anton (mobile 9501, level 35, room 9506) is a source candidate, but his current
combat stop requires Sanctuary, so source level and the short entrance route do
not make him an executable no-reserve target. His reset has no special or
program, wields the source-identified chef's knife (object 9506), and carries
the paintbrush wand (9504) loose; `fight.c` only zaps a wand held in
`WEAR_HOLD`, and the source audit rejects a loadout change that holds it.

The exact XP-loss receipt for Grok (9510) scopes that failure to Grok only.
The parent Catacombs failure and cumulative loss ledger remain intact. If a
source refresh makes that historical target scope unusable, the parent remains
closed rather than retrying an unknown mobile, but the independent missing-key
route remains eligible. At levels 38-39 the separate Joan key hunt (mobile
9506, room 9517) passes its source audit for the spiked key (object 9565), with
a 95-percent starting-health requirement and Peter retained as a checked
trivial bystander. The key opens the east door from room 9523; the bats, art
critic, and gallery visitors then pass their individual source audits. This is
candidate evidence only: confirmed key inventory, reachable live exits, exact
identity, consider, isolation, output, health, provisions, and return checks
still govern each attempt.

Joan's required-loot policy may fight an otherwise below-XP-band Joan when the
key is absent; that evidence must not close the key route as it would an
ordinary XP hunt. After a successful key hunt, the starter now enters the
reboot-scoped cache route from the healer before logout and verifies the key is
dropped in room 3007. The world-cache receipt is valid for the current MUD boot;
a later source-mirror refresh does not invalidate the physical cache, although
the recorded source revision remains useful provenance. The key is then
expected to remain available until the next MUD reboot; a missing cache receipt
still means the key was not preserved. Floor receipts remain source-checked.

The target-scoped loss and fallback behavior passed its focused campaign tests,
and all 120 `test_hunt_outcomes.py` tests passed on October 17. The full
regression suite was already run today and was not repeated for this change.

The default Midgaard recall shortlist is not the whole level-38 frontier.
From the registered Mirror Realm route's Suite (19170), source revision
9205f316 admits three close, plain level-39/40 opponents: the barkeeper
(19026, room 19071), the waiter (19027, room 19072), and Mr. Teece (19069,
room 19166). Each is a single-reset sentinel with no aggression, attack
program, combat special, or combat weapon reset; their exact source paths are
registered as one bounded three-kill visit. Each stop keeps the 20% health
floor, unprotected HP-fuzz probe, and live damage-window, identity, isolation,
and consider gates. No sanctuary is required if those gates pass. This is
source-approved opportunity, not live proof of presence or a kill. Positive
alignment on Teece may shift Dorrik's alignment further negative under
`xp_compute`; fame and XP remain separately observed.

An eligible target route may first use an existing affordable optional flight
purchase. Preserve current food/recovery, nonnegative fame, shop-route and
purchase cooldowns, purchase-failure evidence, fresh price/stock, and live
affect verification. An unaffordable or failed purchase never grants departure.
At healer 3054 before departure or after the registered field return, retain an already-applied combat loadout when
only movement is low and HP is at least 95% and mana at least 50%. Swapping
movement gear can change the maximum and otherwise oscillate loadouts. Keep
the ordinary movement ratio, absolute route budget, and recovery checks; this
does not lower departure readiness or replace HP/mana recovery gear.
The return case includes a movement-only pending recovery flag, but keeps the
registered healer return and ordinary sleep/readiness requirements. Damaged
or mana-depleted characters still use recovery gear.
October 10's single focused regression batch passed 26 tests. The later
cooldown-expiry, locator-origin, expanded-target, and optional-flight changes
and their extra cases are compiled but not pytest-verified;
do not run another regression batch before October 11 local time.
Run 16628 live-triggered the new 20% threshold against Sally. Flee took another
violence pulse and HP reached 48/702; the character returned to healer 3054 and
finished fully healed. Record execution success, objective not achieved, and
safety loss independently: 551 flee XP lost, 846 damage XP gained, +295 net.
The prior successful Sally kill never clears this new failed fight.
Hoard guardians are dynamic spawns: their player-derived level, HP, and extra
level/2 damroll replace the ordinary reset assumptions. The standalone guardian
calculation reports raw attack bounds, not complete damage after victim-specific
effects and not a proof that the dig lag and escape can be survived.

For passive-defense probes, `combat_defenses.py` mirrors `fight.c`'s sequential
shield-block, parry/pre-empt, and dodge rolls. Require
observed positive proficiency from the current level/boot training audit,
matching current skills, normal form, structured equipment/affects, and an
awake, unimpeded character. Ordinary probes remain limited to plain targets.
One prepared armed-target probe is permitted only for a fixed sentinel with
exactly one source-identified, reset-loaded ordinary weapon; reject specials,
programs, aggression, fear aura, extra resets, bows, and other combat gear.
Require at least 95% player HP, enough HP to survive one raw peak while
retaining the 22.5% reserve, a raw peak within 67% of maximum HP, a combined
normal-hit probability of at most 1/2, and source output covering the target's
maximum loaded HP plus expected incoming damage. Use the target's maximum
loaded level and strict percent-roll boundary; ignore armor misses, dual parry,
and other unproved mitigation. The probability reduces expected normal-hit
damage only; never discount the raw peak. Preserve the fixed action budget,
route preflight, live isolation/consider/damage window, and exact target-loss
closures. All other high-peak armed targets still require sanctuary or learned
disarm. Save `campaign_source_ranked_passive_defense_estimate` as source-only
evidence, not a retry marker or live authorization. This never reopens a
recorded loss or any below-band/route exclusion. Focused tests were added for
the October 8 change and await the next daily regression window.
Save `campaign_source_ranked_passive_defense_estimate` as source-only evidence,
not a retry marker or a successful combat observation. This never reopens the
bard's recorded loss or any below-band/route exclusion. October 7 compilation
passed; the new focused cases await the October 8 daily test window.

An improved-output revalidation may retain one exact low-level route-program
hazard only when `_source_ranked_route_program_candidate_allowed` validates the
candidate's registered `where` preflight. This is not a route-hazard bypass:
issue the locator fresh before crossing and return if it finds the mobile. The
existing one-shot loss marker and all post-loss output, health, identity, and
consider gates remain in force.

For a source-ranked route that crosses a plain wandering aggressor, a positive
`where` result anywhere in the current area closes the no-combat transit proof,
even when the reported room is not on the planned path. The mobile may move
between the origin locator and an adjacent scan; generated routes therefore
recall on any positive location and retain their bounded scan checks for a
negative result. This protects route identity without reopening the failed
target or authorizing combat with the wandering mobile.

For the exact policy with the prior damage-window loss, admit the post-loss
plain-target variant only when that one-shot revalidation proves a strictly
higher source output ceiling covers the observed target HP. Its independent
incoming-damage bounds still apply; this does not reopen a second attempt.

Persist consumption on the exact loss record and loss event, not only in the
single active marker: selecting a different target must not make the earlier
attempt available again. Startup may repair a legacy record only from a
matching source-ranked segment whose marker, policy, target identity, observed
HP, output ceiling, and loss event agree. After selection consumes the marker,
the active stop builder may carry that exact proof through only when the same
policy, level, boot, target, source revision, and current output signature
still match. This preserves the selected probe's no-sanctuary admission; it
does not reopen selection, grant a retry after interruption, or relax any live
consider, isolation, health, route, damage-window, or return gate. A verified
objective kill clears that policy's loss record, allowing future evidence to
be evaluated afresh.

Prefer current-band fights with the best expected net XP per whole-session
time when the observed gear, trained skills, and source-backed output support
the existing finite combat budget. Do not require sanctuary just to avoid
ordinary damage when the exact plain-target no-reserve rules pass. Keep live
`consider`, target identity, useful-XP, incoming-damage, and survival checks as
hard gates; increased aggression means using proven capability, not weakening
those checks.

After a same-level XP loss, the plain-target HP-fuzz probe may use a combined
source exposure ceiling of 65% of maximum HP: the worst source round plus the
extra damage from one critical hit (half the doubled critical total). This is
30% above the former 50% post-loss ceiling, but remains below the ordinary
80% unprotected-probe ceiling. Require an exact fixed sentinel with one reset,
no aggression, fear aura, program, special, or wielded weapon; retain the
source-output lower-bound and HP-uncertainty checks, route-program `where`
preflight, and all live isolation, `consider`, damage-window, and return gates.
The 50% limits for route-loss and partial-timeout retries are unchanged.

For a passive post-loss target whose source-loaded level range straddles the
five-level useful-XP floor, use the range's upper bound for bounded-probe
admission; the nominal source level alone must not close it. This is only
permission to run the exact route preflight and fresh live `consider`. The live
result remains authoritative: a result at -5 or lower closes that reset before
combat and cannot earn progression XP.

The passive contract above remains unchanged. A separate aggressive post-loss
probe may be armed once per level and reboot only for one exact, fixed,
unarmed sentinel with one reset, no special, program, fear aura, or confusion.
Require the source-loaded minimum level to be strictly greater than
`character_level - 5`, the maximum no more than `character_level + 2`, the same
65% peak-plus-critical ceiling, and source output covering the lower HP bound
and uncertainty gap. Persist the exact target marker and consume it before the
segment opens. Start at 95% health; fresh route checks, isolated live identity,
useful `consider`, observed damage window, and bounded withdrawal remain
mandatory. A second aggressive probe at that level and reboot is closed even
after interruption.

Live result from run **16569**: Dorrik's exact source-ranked Olympus policy for
Samuel the Armourer (mobile 918, room 935) reached the live fight, then withdrew
at the hard-health floor before an objective kill. The source output ceiling was
1,392 against 792 observed target HP, yet the segment recorded 551 XP lost
(level 30, boot `Sun Sep 27 23:55:43 2026`). The checkpoint stores this exact
policy in the current-boot XP-loss ledger; do not retry Samuel or infer that the
source output estimate proves the exchange survivable. Select a distinct
current-band policy and retain all ordinary live damage and withdrawal gates.

Reject a passive armed combat-special HP-fuzz probe during source selection
when the runner cannot open it without enemy GMCP HP. DD4 `update.c` sends that
HP only during combat; `consider` does not supply it. Preserve the existing
source-audited economic-special exception and every ordinary opener gate.
Run 16453 demonstrated this unsupported armed cleric shape at Solace's
Lieutenant Commander: exact consider succeeded, but no opener or potion was
dispatched. Do not make pre-combat enemy data appear by weakening the runner.

Keep a selected affordable flight purchase ahead of protection-frontier
rewrites only at a provisioned, recovered healer checkpoint with observed
nonnegative fame, zero next-level QP shortfall, and no active shop-route or
purchase cooldown. The ordinary runner must still verify its source route,
current quote, stock, purchase, and resulting flight affect. An empty XP
frontier may select already-audited ground-stash or coin-carrier funding under
their existing admission and retry contracts; record it as maintenance, not XP.
Treat a fresh fly/levitation affect as sufficient only when its known duration
meets the selected route's source-derived reserve; a generic flight objective
requires positive duration. If an active affect is too short, stay at the
healer, handle observed food or thirst needs, and sleep on the same connected
session until it expires before buying and verifying one replacement. Duration
zero is not route-ready flight, and repeated save/quit shop probes do not age it
productively.

`scan` describes each sighting's distance. The pre-entry check concerns the
immediate destination, so only an exact target **one** room away in the chosen
direction blocks that step. A sighting three rooms down the same direction is
not evidence that the adjacent room is occupied. Preserve the whole-route
`where` preflight and fresh checks before later registered destinations. This
parser correction does not reopen historical failures or spend new retries.

Hex inventory planning uses current effective STR/DEX minus level/4, floored
at three. Hidden over-cap stat surplus can only improve that lower bound.
Capacity changes affect pickup; `move_char` and `get_move_ws` do not forbid
walking solely because weight or item count exceeds the new capacity. Preserve
already-carried belongings. Separately check `affect_modify`'s primary-else-dual
weapon drop against the new STR wield limit. Use the existing exact required-
loot capacity relief for pickup, not an invented post-hex disposal loop.

Equipment removal text arrives before `Char.Worn`. Capture a removed item's
unique already-observed source identity before clearing its slot; otherwise
the later diff cannot recover it. Keep hints session-local and require current
inventory presence. A known nonweapon removal is not primary-weapon loss;
unknown removals remain conservative. A single role-compatible primary stays
equipped during recovery unless the full proposed loadout improves the existing
HP/mana/stat priorities, including set bonuses. A hitroll-only change is not a
reason to replace it while sleeping. Combat/pre-level ranking remains unchanged.

Recovery identity revision 2 permits one fresh comparison after an exactly
matching legacy five-command verified restoration. Both saved plans must match
the current source/inventory plan, level, and reboot. Persist consumption and
the old result in `recovery_identity_repair_of`; never reuse an old comparison
reply as current item identity. Repaired or changed results stay closed.
One separate response-parser revision-2 check may follow only the exact legacy
three-command `weapon comparison timed out during compare` failure. Preserve
that failure in `prompt_repair_of` and preserve an already-consumed restoration
marker. Split complete prompts before matching period-terminated reply lines;
asynchronous healer chatter can precede a valid reply without a newline. Five-
second deadlines, fresh equipment/inventory, exact comparison, and post-wield
verification still apply. Neither repair clears any combat loss or hunt closure.
Persist comparison audits on failed runner exits as well as successful ones.
A legacy dispatched-only record may recover the missing failure audit from its
matching failed comparison in the existing segment tail: unchanged level/boot,
identical start/end request, healer endpoints, unchanged visit XP/loss, the exact
compare-timeout terminal error, and only the three read-only comparison decisions.
Require the entire visit to fit below 128 stored events. Preserve its run ID and
all current loss evidence; missing, modern, changed, or post-wield records remain
closed. This recovers a result, not a comparison reply or permission to hunt.

Before any opener, a source-resolved guard bystander must pass the target-aware
alignment/non-hostility check even below the ordinary assistance-level window.
Keep it in the room-hazard set until then, ahead of trivial-bystander and cached
non-assisting shortcuts. Run 15984 lost 576 XP after a level-15 townguard joined
the level-29 player's fight. Preserve that loss and its closed policy; this fix
does not authorize a retry. Telnet `update.c` serializes the primary enemy for
each participating room combatant, including possible allies; duplicated rows
prove neither identical prototypes nor a harmless duplicate. Do not deduplicate
them or substitute the repeated primary level for another attacker's level.

Startup equipment reconstruction uses the ordered live primary-slot replay.
Do not set `campaign_has_weapon` from absence of a loss message or by looking
up shared worn names. A failed connection that issued zero commands and matches
the pre-login transport classifier can be skipped using only the loaded segment
tail. Stop at the next real run, including a disarm, an empty slot, or a partial
post-login failure. This repairs transport-only checkpoints without reviving
equipment after actual loss or broadening history scans. Report connection
establishment failures separately from failures to reach a usable login.

A healthy pending lesson at the exact source-registered distant class teacher
does not need the later XP route's movement pool. This applies only after the
training trip has started, with no return/abort/runtime boundary, no combat,
known positive vitals, at least 95% HP, 50% mana, eight movement, no active food
or water need, and no poison or blindness. Preserve source teacher identity and
all existing practice checks. The separately registered consumable-invisibility
journey keeps its own rules. Once training completes, ordinary healer return,
movement recovery, and combat readiness apply again. Never apply this lesson
exception to a route waypoint, merely similar room name, or hunt target.

The one-shot long city-route revalidation uses the same productive-repeat
admission as ordinary source selection. Its fresh-candidate three-kill cap
must not discard a route independently admitted by same-boot meaningful XP
evidence. Compute that admission over all ranked candidates, including those
with the exact city-only block, and record `repeat_after_kill_cap`. Retain the
unchanged no-travel blocked segment, later run-matched unblocked locator,
source/level/boot identity, 22-extra-command ceiling, and consumed retry marker.
Every ordinary selection, source and live combat gate still applies; this is
not a second attempt after an already-consumed route revalidation.
Run 15974 live-proved selection after that repair, then stopped on fresh Poor
Alley hazard sightings. Its clear city-prefix record is not contradictory:
the separate full-route check covers later city rooms after the sewer section.
The consumed marker stays closed; do not reinterpret that result as a stale
abort or use the partial prefix to authorize the remainder of the path.

Connected quest waits must continue reading the socket between thirty-second
`quest time` queries. Do not sleep the reader for that interval: queued healer
chatter can strand fresher GMCP and create a false no-progress result. Treat the
exact `quest time` cooldown replies and DD4's `You may now quest again.` message
as live quest-status updates even while duplicate-login filtering suppresses
later `Char.Quest` snapshots. Keep resource maintenance, the 180-second
no-progress stop, and the finite segment deadline. DD4 calls `quest_update` on
the randomized area pulse (30-90 seconds), not on an exact one-minute schedule.
One legacy sleep-before-read stall may reopen only from its exact single
cooldown phase at the recovered healer, unchanged level/reboot/XP/timer,
nonnegative fame, and a required next-level QP shortfall. Persist reader
revision 3 and the old marker before dispatch; a repaired-reader failure cannot
reopen this legacy exception. When a fresh status reports no active quest and a
zero timer, request again immediately on the connected quest phase; do not
impose a level, reboot, or campaign-history quota.

A loose-item quest may cross source-audited `spec_thief` mobiles with a known
whole ordinary purse of at most 250 copper-equivalent. Audit every reachable
pickpocket as passive, unarmed by reset, unprogrammed, without fear aura, and
with no other special. Retain all other route hazards, source access, program,
movement, and live safety gates. Limit the recall-origin path to 60 commands
and exclude randomized exits. Persist the exact giver/room/object identity and
mobile VNUMs on the route; recheck the active loose retrieval, purse, and source
profile during outbound travel. No combat target is authorized. The cap covers
the entire purse, not just one 20-percent theft; DD4 only steals copper, silver,
gold, and platinum through `total_coins_char`. Source analysis of the rejected
run-15955 Yggdrasil assignment passes a 36-command route to object 76 with
pickpocket 9911; that abandoned quest is not live completion evidence.

Source-required next-level quest points and optional frontier requests are
different objectives. First try executable current-band XP during a positive
quest timer. If none remains, a recovered, fed healer checkpoint with observed
nonnegative fame and a source-defined QP shortfall may select `quest-cooldown`.
Reuse the existing connected wait, finite runtime, food/water maintenance,
fresh assignment and source route checks. DD4 advances `nextquest` only while
the character is connected. If the worker cap arrives first, finish safely at
the healer and resume the same campaign promptly; do not wait offline or treat
the positive timer as a failed request. Keep each worker bounded and preserve
the live timer as the only request cadence gate. An unchanged timer closes the
next wait. A same-level/boot dispatched request plus ordered live phases
showing cooldown zero and then a positive active quest identity proves that a
later cooldown is new, not stalled. Remove that phase evidence when the next
wait is persisted, and persist completion as an explicit null wait marker so
ordinary maintenance cannot restore the older timer. Legacy checkpoints may
recover this fact from the latest quest wait in the existing bounded segment
tail only: require success, a run ID, identical saved wait marker, matching
level/reboot, and the ordered positive assignment evidence. A later quest
segment or changed marker closes this repair; never expand the history scan.
Never infer a new cycle from selection alone or an unacknowledged request.
There is no campaign request limit by character level or reboot. Require a
complete observed quest status with valid `active` and `nextquest` fields; a
missing or malformed status is unknown, never an expired timer. The active
assignment and timer are the cadence gates: request only when inactive and the
timer is zero, and allow another request after DD4's timer expires. Campaign
request markers are audit history, not eligibility gates. A
source-required quest request for a remaining next-level QP shortfall remains
available after executable current-band hunts are exhausted and the healer,
food, water, fame, and live-quest gates pass. A selected cooldown may dispatch
after the observed timer reaches zero; do not require an unused campaign marker.
Do not defer that dispatch solely because less than 180 seconds remain in the
bounded session; the inactive status and zero timer are the cadence gates.
A direct `quest-request` can establish the same new-cycle fact when its saved
start explicitly has inactive quest status and zero cooldown at the same level
and reboot, followed by a dispatched request and positive live assignment.
Legacy repair may read that start alongside the end in the existing bounded
tail, but its first recorded quest phase must match the segment. Missing
availability, a changed reboot/level, or an unaccepted request cannot clear a
wait marker. Run 15955 exposed this direct-request case. Checkpoint 48490
confirmed the legacy marker repair, and run 15958 selected the connected wait;
this is maintenance evidence, not a completed quest.
New-cycle evidence requires an explicitly positive observed `active` flag.
The legacy snapshot parser's inferred activity from object/mobile fields is
not enough: stale identities must not override inactive or missing status.

Quest handoffs share a socket, so preserve the preceding policy's current
structured worn items, primary identity, instance mappings, ranged/chain facts,
and removed-item hints. Copy containers rather than aliasing them. Keep weapon
loss/refusal evidence independently, including when structured gear is stale.
Do not copy pending commands, completed gear audits, or route cursors. The next
text audit remains mandatory but must not overwrite a current structured identity.
DD4 `update.c:4415` only sends changed `Char.Worn` data: requesting `eq all`
cannot be relied on to resend it. Run 15951 lost that identity at the cooldown
handoff and replaced branch 6104 with club 1521. The handoff fix compiles; its
new positive/stale/loss regression cases await the next daily test batch.

Old research-rotation exclusions must not turn an already-affordable flight
purchase into another funding hunt. The narrow maintenance admission requires
food, affordability, no flight, no current purchase failure, and no observed
reputation refusal. The caller's route cooldown still applies, and the live
shop listing must confirm price and availability before buying. Run 15950
proved the repair: 345 copper-equivalent covered the freshly quoted 141-copper
potion, leaving 204 and a positive fly affect. It earned no XP.
When food is missing and city restocking is affordable, choose it before an
emergency equipment sale, including while already flying. Normal sellable-loot
liquidation keeps its independent priority and item-protection checks.
Run 15952 proved this combined ordering: six pies purchased for 174 copper
while already flying, with 30 copper-equivalent left. No emergency gear sale
was required. All new focused regression cases remain unrun on October 2.

The source contains three `a long, grey branch` prototypes: light 6103, weapon
6104, and trash 6105. Names alone cannot prove their weapon role. Resolve a
current structured primary through exact VNUM, item type, source description,
and class compatibility, retaining reconciled weapon-loss and empty-slot
evidence. Use that same identity in ground/carrier upgrade ranking, not the
lowest-VNUM same-name object. Contradictory structured identity must not fall
back to its worn name. Legacy unique names and separately carried role weapons
retain their existing checks; this does not identify an ambiguous carried item.
Runs 15941/15942 repeatedly saved and quit because campaign role matching chose
the light while the live executor correctly saw the weapon. The corrected
selection moved on in 15943. Run 15946 then proved the carried-branch recovery:
checkpoint 48447 has weapon 6104 equipped instead of club 1521, with full health
and unchanged XP.

`compare-carried-weapon` is noncombat healer maintenance, once per level and
reboot, recorded in `campaign_carried_weapon_comparison` before dispatch.
Refresh `eq all` and inventory; require one equipped weapon, one carried
candidate, exact text/GMCP inventory counts, and source mappings for every
carried item. The shared name must contain exactly one usable, releasable weapon
prototype, with a command keyword shared by its variants but by no other
carried prototype. `compare <keyword>` omits the second argument deliberately:
DD4 searches worn gear only when that argument is absent. Only the exact
better-than reply against the known primary permits `wield`; fresh `eq all`
must then confirm the expected VNUM, type, and name. Each reply has a five-second
deadline. An unclear, worse, incompatible, or changed result closes the attempt,
not a retry loop. This type-resolution contract grants no combat permission.

If an earlier successful comparison's exact reference weapon becomes primary
again, one healer-side restoration check may repeat the full comparison at
the same level and reboot. Require the earlier five-command verified result
without failure and the same current source plan (candidate, reference, names,
and unique keyword). Preserve it in `restoration_of` before dispatch; that
field closes any second restoration, even if the new attempt fails. Fresh
equipment and inventory, a new exact better-than reply, and post-wield VNUM
verification are still required. Never infer that a same-named carried item
is the same instance across reconnects. This repairs an observed equipment
reversal without clearing hunt failures or granting combat permission.
If the same source-resolved carried candidate remains available but the worn
primary VNUM has changed since a verified comparison, allow one further check
at the same level and reboot. Require the exact prior five-command success and
unchanged candidate VNUM, name, and unique keyword; save the prior primary
identity as `primary_change_revalidation_of` before dispatch. This allowance
is consumed once even if the primary changes again. Repeat every fresh
equipment, inventory, comparison, and post-wield check; a failed or ambiguous
result does not reopen it, and it grants no combat permission.

Run 15968 live-proved the restoration, and checkpoint 48510 after two further
wait segments still records weapon 6104 equipped. The October 3 focused batch
exposed incorrect wear flags in the synthetic comparison fixture; they are
corrected, but the correction has not been rerun under the daily test limit.

For pounding-weapon rearm, an absent `list mace` at Dave the Dealer allows one
live `where dave` check. Parse the complete source short description before the
room label, then map that exact label to at most four source-reachable Midgaard
rooms. Prevalidate one source-safe circuit through those rooms and back to
healer 3054, capped at 22 commands total, with enough observed movement for
the remaining circuit at every stop. Reject private or solitary route rooms.
Dispatch each leg only from its recorded origin; if that origin changes,
return to the healer and close the attempt. Issue one fresh `list mace` at each
candidate room, buying only after a live listing proves the shop is present.
After one circuit, return to the healer; never repeat `where`, guess a room, or
turn locator navigation into combat permission.
If that exact route ends safely at the healer with unchanged level, boot, source
revision, XP, loss totals, and wielded primary, persist the failed optional
rearm attempt and continue with another eligible current-band policy. An empty
single live locator check is also a completed optional attempt, not permission
to repeat the shop journey. Require a linked run and nonzero commands. Retain
the proof XP/loss totals in the marker; later XP gains do not reopen this route.
The marker expires when level, boot, source revision, or primary weapon changes.
It never overrides a missing-primary or required-piercing-weapon gate, and it
does not authorize using `stun` without a confirmed pounding weapon.
One route-code correction may reopen only the exact safe marker whose linked
failed segment records Dave's room label as having no bounded
source-reachable room set. Require the same level, boot, source revision,
primary weapon, healer checkpoint, and the linked segment's unchanged XP/loss
and safe-return evidence. Consume the correction in the original marker and
checkpoint it before opening the segment; it cannot be repeated. During the
registered outbound route, a complete current room listing may instead identify
Dave at an exact source-reachable room VNUM on that route. Stop there only when
the source shopkeeper identity matches, the registered route prefix and its
reverse still match open source exits, private/solitary rooms are absent, and
observed movement covers the return. This uses exact live room identity, never
the ambiguous `where` label, and grants no combat permission.
For a Thief/Bounty Hunter stun opener, only the positive collapse message
authorizes the follow-up backstab. A missed attempt can start combat through
DD4's zero-damage path, and `do_backstab` rejects an already-fighting target;
restore the primary weapon and use ordinary combat instead. Keep the existing
source, target, and survival gates unchanged.

Source `do_kill` adds no `WAIT_STATE` when it replies exactly `You do the best
you can!` to an already-fighting player. Release that command window without
adding another combat-round delay, including when a preceding automatic parry
acknowledged it first. Keep the reply request-local and bounded; quoted speech,
other commands, and normal damage replies do not inherit this exception.
Between-round action cooldowns, damage probes, and survival gates remain active.
For current ordinary progression runs, allow 300 seconds per segment: the older
180-second cap forced run 15929 out of combat after only 16 seconds. This is a
finite whole-segment allowance, not permission to extend any combat action limit.

DD4 `gmcp_update_quest` labels both loose objects and buried hoards `retrieve`.
Preserve that wire type. Only a real dispatched `quest request` opens the
five-second, 4,096-character narrative window. Match the exact questmaster's
hoard announcement to GMCP giver, room name, and area, then bind its annotation
to positive giver/room/object VNUMs. Retain it for that active identity only;
reconnect, a new request, inactive status, or changed identity clears it.
Unsolicited text and item names cannot authorize digging. The hoard generator
has a 5% chance to arm a trap with up to three charges, including curse, hex,
and a spirit guardian. Each triggered charge makes `do_dig` return before
contents spill; exhausting the charges can require up to three more digs than
the depth estimate. Known hoards currently abort with an explicit trap-handling
blocker; the former fixed twelve-dig sequence is removed. The standalone
controller now budgets those extra commands and pauses for an explicit, freshly
verified trap recovery before another dig, but live dispatch does not provide
that recovery verification or the physical return yet. Do not treat the
controller change as permission to dig. Ordinary loose retrievals keep the
existing source route and exact-object checks.
On October 4, Dorrik purchased the source-identified Midgaard Grocer spade
VNUM 3393 for a live quote of 70 copper (run 16162) and returned to healer room
3054. This is a valid `ITEM_DIGGER`, and the campaign recognizes it as
satisfying the tool capability check; its lower throughput means more digs and
tighter movement planning, not a requirement to buy a better shovel. The quote
is boot-specific, so list the item before buying. His quest request is already
used and no hoard is active; do not repeat the request. For former Forest room
18022, the spade's source values `(36, 3, 9, 160)` estimate 15 minimum-damage
digs plus up to three trap-charge digs: 18 commands and up to 3,654 movement
before return in the conservative total budget. The controller budgets one dig
at a time and can pause for movement recovery, but live trap handling and
physical return remain unintegrated. Its checkpoint API resumes only from a
safe boundary with a newer observation; an interrupted dig awaiting its reply
stops until ordered events are reconciled. Matching checkpoints now pass
through the quest-session owner and campaign state, but no live dig is attached
to dispatch. The parser also keeps a compact room-render snapshot after the
exits, visible listing, and prompt arrive, and clears it on a room transition.
DD4 `act_info.c` uses the same runtime `target_id` prefix for objects and
mobiles; these raw lines are not prototype VNUMs or proof that the room has no
hidden occupants. They are not yet consumed by a live digging gate.
The strict source
return check admits no unconditional path from that room to a healing-flag
room. `hoard_return_plan(...,
allow_exact_live_where_hazards=True)` now recognizes only the audited cityguard
and drunk profiles, records their VNUMs as mandatory live `where` checks, and
builds conditional outbound and return routes. The exact `where` selectors are
`cityguard` and `drunk`. `live_escape_issue` must clear the outbound path and
every random flee/return branch before digging; `live_route_issue` must be
repeated with fresh complete locations before each route leg. The planner now
also accepts an explicit `flying=True` estimate: DD4 divides eligible travel
movement by three while flying, but this does not reduce tool movement for
`dig`. A flying route plan is rejected by its live route/escape checks unless
the flight affect is freshly observed for that leg. Refresh or verify flight
before each leg; never assume it will last through excavation. Walking remains
the default and worst-case estimate. The unflown Forest route is 40 commands
each way; it estimates 221 movement outbound and reserves 231 movement for
return and flee. Its north flee branch re-enters the hoard room and requires a
fresh check that guardian VNUM 83 is absent from the remaining route. This is
planner evidence only, not live dispatch or permission to ignore an occupied
route. `build_source_hoard_execution_plan` passes its configured route limit
(no more than 240 commands) into the outbound/return planner; movement circuits
still enforce the total command budget. This does not admit randomized exits
or source-hazard rooms. `HoardDigSession` now pauses for movement recovery,
preserves its return reserve, and records a uniquely identified trap effect
from DD4's response; unknown or mixed effects stop the session. It still does
not resolve trap effects, fight guardians, issue sleep/wake, or prove recovery
safe. Keep live digging disabled until an integrated,
source/live-gated recovery cycle and physical return are implemented and
replay-verified. See
`docs/QUEST_HOARD_AUDIT_2026-10-03.md` for the assumptions and run evidence.
Questmaster routes are registered from recall room 3001. When a live checkpoint
starts at the healer in room 3054, prepend the source-verified `south` step and
set 3054 as the route origin; keep 3001 unchanged and reject other origins
instead of replaying recall directions from the wrong room.
DD4 kill quests retain an exact mobile prototype VNUM. `fight.c` marks the
quest kill complete on that VNUM without checking the hinted room, so the
campaign may choose another source-listed reset for the same prototype only
when the normal source admission succeeds. The assignment room remains search
evidence; alternate resets do not relax route, live identity, isolation,
consider, output, or recovery gates. Do not apply this rule to object quests.
The October 3 source audit is in `docs/QUEST_HOARD_AUDIT_2026-10-03.md`, including
double-fuzzed tool costs, terrain/stat modifiers, first-trap abort, invisibility
loss, cursed physical return, and the guardian's partially overridden prototype.
The standalone `excavation.py` controller and tool budget are implemented but
not enabled. `QuestSessionController` can restore and persist a checkpoint
only for the same narrative-verified active hoard assignment; a malformed or
changed-identity checkpoint is recorded and cleared. The Telnet reader now
forwards response chunks to an already active session only while its exact
assignment still matches; changing or clearing the quest drops that controller.
The owner can start a dig controller only after that exact assignment is
observed on the current connection; repeated setup cannot reset an active
controller. Polling, trap-recovery confirmation, and pickup use the same
identity gate. This connects observation and construction only, not permission
to dig. `StarterBotRunner` does not call those adapter methods yet, and the live
campaign still does not construct or dispatch a dig session. Before dispatch,
integrate exact tool/quest observations, the full visible physical return route,
post-hex carrying capacity, guardian escape, trap recovery, persisted audits,
and exact-object pickup/turn-in. The pickup controller now saves a unique
selector from the fresh room listing and the matching object's baseline
quantity from DD4's nested `Char.Items` payload, then returns exactly one
`get #selector` command. It confirms possession only after a newer complete
inventory snapshot increases that source-unique description by exactly one;
the selector is not expected in inventory. Checkpoint schema 3 persists the
pending pickup intent so a restart never blindly issues it again. Older
`object_acquired` checkpoints are downgraded because they lack quantity-delta
proof. This proves carriage only; it does not prove quest turn-in or
completion, and it is not yet called by the live runner.
`build_source_hoard_execution_plan` now composes the narrative-verified quest,
carried source tool, source-fuzzed shop level, dig budget, return route,
movement circuits, and direct-trap/guardian damage windows. It is source
planning only: it does not authorize a route or issue `dig`. The first live
version may complete an untrapped hoard and must stop on a trap until recovery
and physical return are verified; do not remove the campaign blocker before
exact-object pickup, turn-in, and timed restart/recovery cases are integrated.
Room-wide physical trap damage uses full AC, not the single-target AC/4
formula. Saved controller tests are unrun; compilation alone does not release
the existing hoard blocker.

`training-travel-supply-20-29` may acquire one pure-invisibility potion for an
observed, affordable advanced-teacher lesson blocked by source route hazards.
Require matching level/reboot training evidence, a recovered healer checkpoint,
nonnegative fame, food, carrying space, and a source-safe ground vendor route.
The vendor must have one stationary reset, no aggression or program, and only
audited noncombat or combat-only specials. Keep private, solitary, no-recall,
randomized, and flight-dependent routes closed. Ordinary city program checks
and source-validated detours still apply.

Use a fresh complete shop listing, one exact TARGETMODE selector and unique
source description, a usable live level, and a price below the current balance
minus 100 copper. Buy once; require acknowledgement and increased inventory.
Replies have a five-second deadline. Record quotes, outcomes and selectors in
`campaign_source_purchases`; persist `campaign_training_travel_supply` at segment
start. Its first, legacy 100-copper cap may reopen once only for the exact saved
unbought quote failure with a larger available budget. Revision 2 consumes that
repair; successful, attempted-buy, identity, transport and other failures do not
reopen it. Acquisition grants no XP or trainer-travel permission.

`consumable-training-travel-20-29` independently registers one noncombat teacher
visit after that completed purchase. Require the same level/reboot lesson audit,
a unique carried source potion, a stationary class teacher with useful gains,
and an exact, recallable ground route of at most 90 source steps. Keep a
20-movement reserve above the remaining source cost, using actual current
movement rather than assuming the character's maximum. Persist
`campaign_consumable_training_travel` before dispatch; never repeat it on
reconnect. Revision 1's exact missing-selector setup failure may reopen once
only when its saved result has no selected potion, route index zero, and the
same still-carried item and teacher. Persist setup revision 2 before that
repair; any other failure stays closed. Empty shop activity must not overwrite
prior purchase evidence. A confirmed purchase remains provenance after a reboot
or level change, but a new journey still needs a current matching training audit
and fresh inventory. Enable TARGETMODE and confirm the live reboot and practice
balance before consuming. Check the city greeter before drinking at the healer.
Require a fresh inventory selector, quaff acknowledgement, inventory reduction, and a
new GMCP invisibility affect of at least four ticks; all replies have five-second
deadlines. Duplicate GMCP inventory suppression is not evidence of absence:
the request-local text listing must match the carried selector. DD4 `save.c`
loads carried objects with target ID zero, so after login a single source-unique
keyword may replace the numeric selector. Its prefix must match no other source
object keyword, and exactly one current carried description must agree with
the complete live inventory listing. Alternatively, one single keyword may be
unique among carried items: require identical complete text/GMCP inventory
counts, one source-unique target description, source mappings for every carried
description, and no matching keyword on any other possible carried prototype.
Unknown or renamed descriptions, duplicates, conflicting aliases, and listing
mismatches reject this fallback. Quoted multiword names do not work here:
`do_quaff` reaches `get_obj_carry`, which uses single-prefix `is_name`.
Setup revision 3 may reopen revision 2's exact unselected, unconsumed, route-index
zero failure once when the current source and carried inventory prove this
keyword method. Require matching item and teacher evidence, consume the marker
before dispatch, and retain all route, practice, inventory and affect checks.
Never reuse a saved numeric selector.
Carry `campaign_training_travel_result` into later checkpoints. If a legacy
checkpoint lost it, load only the latest matching trainer segment through the
256-row metadata lookup. Restore only a completed healer result whose full
attempt marker, level, boot, item, teacher, and setup revision match the current
marker. Preserve explicit later results, including nulls; restoration records
its run ID and is evidence recovery, not retry authorization.
Only the prompt after the expected reply header completes that request; an
earlier configuration or room prompt cannot acknowledge inventory or quaffing.

Only this noncombat teacher executor may use equipment-aware invisibility to
pass source-known, non-detecting equipped aggressors. Programs, detecting gear,
unknown objects, unsafe specials, private/solitary/no-recall rooms, randomized
exits and flight-dependent paths remain closed. At every step require the exact
live exit, at least two invisibility ticks, health, and remaining movement.
The exact route's reserve replaces the ordinary half-full movement floor, not
health recovery. Any change ends the visit and returns to healer 3054. Buy at
most three useful source-capable lessons using fresh practice listings, then
recall and recover. Save `campaign_training_travel_result`; accepted lessons
and useful later XP remain separate proof gates. Runs 15523/15524 and 15916
proved bounded pre-consumption rejection only. Run 15920 subsequently proved
the zero-ID keyword path: `quaff elixir`, confirmed invisibility, the complete
80-step teacher route, three accepted lessons, and full healer recovery at
checkpoint 48408. Its live listing confirmed enhanced damage 67%, defense
knowledge 63%, and parry 62%. Preserve both the failed and successful evidence.
Saved regression cases remain unrun under the October 2 daily limit.

DD4's `do_inventory` appends `You are carrying N/M items.` after its listing;
that total includes worn gear. Ignore only this exact terminal footer when
matching inventory counts, not unknown lines or extra items. Setup revision 4
may repair revision 3's unselected, unconsumed, route-index-zero failure only
when the same completed healer segment's bounded 64-event tail proves an actual
inventory request, a complete matching text/GMCP listing with that footer, and
no quaff before the request ends. Match the entire attempt marker and saved
result; persist its run ID as `inventory_footer_repair`. Current source keyword
uniqueness, fresh live inventory agreement, and every existing route gate still
apply. Consuming revision 4 closes this repair; it is not a general retry.

Local fallback training retains the registered class-teacher route and its
hazard checks. After the normal lesson selection is exhausted, the same visit
may buy another distinct registered priority only when the fresh listing,
remaining practice balance, current stats, and exact source teacher predict a
positive gain. Stop at three accepted lessons, refreshing `practice` after
each acknowledgement; never invent the resulting percentage. A live listed
zero-percent skill can justify a lesson, unlike an absent or inferred skill.
Persist `lesson_policy_revision` in local-fallback evidence. A consumed legacy
visit without that marker gets one fresh attempt only for a newly learnable,
source-capable skill at the same teacher, level, and reboot. Consume it before
dispatch; neither failure nor reconnect reopens it or clears combat losses.

Before leaving the healer for a distant class trainer above level 10, require a
fresh observed skill listing and practice balance, complete live stat modifiers,
and the exact registered source teacher's capacity. Apply DD4's practice-gain
formula to the eligible automated priorities. Skip the distant trip only when
all of that evidence proves no lesson can gain a percent; incomplete evidence
retains the existing route. This check does not suppress explicitly required
practice or separately gated maintenance.

A consumed local teacher fallback can receive one separate route-clear recheck
per level and reboot only when its actual run confirms the exact teacher,
pre-departure city hazard, and no attempted or rejected lesson. The latest
successful source hunt must have gained net XP and recorded its own completed
city locator, with positive source-known locations outside every teacher-route
room. Inherited checkpoint sightings do not count. Require a recovered healer
checkpoint and a fresh source plan with useful, affordable lessons; preserve
all combat-loss evidence. Save blocked/observation run IDs and route rooms in
`campaign_training_deficit_repair.local_teacher_fallback.route_clear_recheck`;
consume its pending status at segment start. The normal live trainer preflight
still decides whether to leave, and another block ends this recheck.
The same retry may instead use a later successful automatic `world-time-probe`:
require its actual `time` command and connection-local matching boot response,
unchanged level, no net XP loss, and timezone-aware segment timestamps showing
at least 300 seconds between the blocked visit ending and that probe starting.
This breaks the dependency on a productive hunt before improving readiness.
It does not claim the route is clear; the ordinary trainer locator must still
prove departure. Record `reason: bounded-route-cooldown` and `cooldown_seconds`
in the shared retry marker. A spent clear-sighting or timed retry excludes the
other. Missing time or boot evidence cannot reopen it.
When the blocked visit is no longer in the recent eight-segment tail, use
`get_latest_campaign_segment_for_phase`: scan at most 256 narrow metadata rows
under that campaign, then load only the chosen row. It needs no new phase index
and never expands the runtime history payload window.

Ordinary `consider` replies have a request-local 2,000-character buffer and a
five-second response limit. DD4's absence reply, `They're not here.`, completes
the pending request and enters the existing bounded target-refresh path, even
when split across reads. Retain that absence until a new request; later room
chatter must not erase it. An unanswered check ends the hunt through normal
combat/death recovery and healer logout, without inventing absent or below-band
evidence. When a combat name differs from a room description, a flee
may match the source short name only through a fresh, same-room, same-level,
same-boot encounter identity for the registered prototype; pursuit bounds and
destination checks remain unchanged.

Field `where` replies retain the request-local 8,000-character buffer until
the prompt after the listing header arrives. A first matching row cannot
complete the reply or discard later matching locations. An explicit absence
reply still completes immediately. If the existing 1.5-second grace expires
without a complete field listing, use the bounded watchdog return; record
neither absence nor below-band evidence. Preserve up to sixteen locator
decisions in `campaign_fastwalk_where_decisions`: reported locations, their
registered room mappings, remaining endpoints, and any chosen relocation.
These records explain navigation only and cannot authorize combat or enlarge
the registered safe search graph.
After a positive locator takes the player beyond the initial search origins,
an exact matching source prototype may continue along a forward suffix of an
already-audited relocation path containing the actual room. Preserve waypoint
mode, reported destination labels, empty-room evidence, and the existing retry
cap. Never reverse a path or join fragments to invent a connection. Record the
original route origin with the selected suffix. When no usable relocation
remains, or the one same-room recheck is spent, close that locator until its
scope changes; do not spend its remaining budget repeating an unchanged query.
Treat a positive-location rebase as a detour, not a replacement circuit:
insert its inspection immediately after the current stop and preserve the
original unvisited stop suffix. If the destination is empty, continue that
registered suffix instead of jumping to the end of the itinerary. Before
continuing, re-root only the first unvisited VNUM leg from the exact detour
endpoint to that same registered endpoint, using a bounded source-safe bridge
and live GMCP exits; keep later stops unchanged. Never replay its old
origin-relative VNUM sequence or widen the allowed room graph. If no safe
bridge exists, return with the route evidence intact.
If that selected path crosses an already registered recovery endpoint, split
the relocation at the exact endpoint and retain its targetless transit stop.
Do not copy recovery permission to the origin, an off-path room, or an
unresolved command-based route. The normal live empty/no-mob, health, movement,
and timeout checks still govern sleep and continuation. Record retained
`recovery_waypoints` with the locator decision; never replace the entire path
with a combat stop that silently loses the recovery boundary.
Campaign revision 338 may reopen one exact source-ranked wanderer result when
its saved segment ended safely at the healer after `where` positively located
the target but the old relocation graph had no endpoint left. This repair
requires the same level, boot, and DD4 source revision; positive mapped locator
evidence; full healer recovery; and no kill, death, combat, or policy-specific
XP loss. It preserves the superseded result and locator decision, consumes its
marker before dispatch, and retries navigation only. The corrected direct
rebase and all current source, live-exit, hazard, identity, isolation, consider,
output, and action-budget gates still apply. A second miss closes the route.
Closed markers for a different exact policy, level, boot, or source revision
must not suppress a new eligible result; retain them in bounded revalidation
history. A pending or attempted marker in the same level and boot remains the
only active locator recheck. Evaluate this repair on every campaign resume,
after loss evidence reconstruction, rather than only during a policy-version
migration.
After a useful ordinary source-ranked kill, an unarmed, non-aggressive wanderer
with no special, program, or loot contract may receive another fresh locator
query within the original segment kill cap and source spawn capacity. Require
positive exact-prototype XP evidence, only accepted considers, and the ordinary
health, mana, movement, provision, and no-loss boundaries. Protected, familiar,
resource, and damage-window probes are excluded. Reuse only registered paths
and the existing locator budget; the next encounter must be isolated and receive
a new live selector and consider. Record `after_objective_kills` on the selected
relocation. No further mapped destination ends a productive search normally,
without marking the target unavailable or revisiting the just-cleared room.
An optional outbound interception must retain the original unvisited stop even
when the intercepted stop is last in the circuit. After a pre-combat crowd
rejection, restore that earlier stop and continue only the remaining official
outbound commands. Preserve crowd evidence and the completed-interception marker;
do not retry the crowd, authorize combat, clear a route abort, or resume a
completed, failed, or already-returning journey.
Registered Mirror Guardian hunts and research retain the fixed approach only
through room 19031. Source `R` resets shuffle rooms 19032-19040: derive the
existing bounded live-navigation graph from current source, reject source
hazards, and finish at exact room 19041 using observed GMCP exits. Both navigation
indexes refer to the end of that preserved approach. Never execute the old
fixed north commands inside the maze or record an absence from another room
as if the target endpoint had been reached. The route grants no combat override.
When continuing from room 19041 to the second registered reset in room 19031,
derive reverse live-navigation preferences from that same route metadata and
follow observed exits back through rooms 19040-19032; never treat the
source-static waypoint list as proof of randomized exits.
Source absence records require an observed room, never a fallback to the planned
destination. For a purely destination-guided stop, that room must be its actual
endpoint; an unfinished or misdirected route cannot spend the endpoint search.
If the level-26-to-30 Guardian hunt safely aborts because live GMCP has no exit
to room 19036, persist that exact route failure for the current boot only when
the segment began and ended at the same level and boot with no kill, death, or
XP loss. Preserve any earlier probe evidence, but do not let it reopen this
route; rotate to the Shire battle-master probe. A new boot may probe the route
again under the ordinary live navigation and combat gates.
After a bounded route-program wait, finish ordinary healer recovery before
leaving. Consume the pending wait at departure and clear the completed emergency
return, so the next step performs a fresh route check. Recovery alone cannot
consume another hazard attempt. Combat, loss, death, explicit logout, and runtime
boundaries cancel the retry without clearing their return evidence. Preserve
the existing retry limit and all subsequent live hazard checks.

Room-listing headers retain balanced closed-exit markers such as `[up]` inside
`[Exits: ...]`. Familiar identification still requires the completed listing,
one exact source-matched selector, and a positive group acknowledgement. While
that preparation is pending, suppress the ordinary route-complete fallback;
only its existing confirmation deadline or an actual safety boundary may end
the wait. A quiet decision is not a completed route.
For a failed route that has safely returned, retain its matching terminal
familiar-preparation, withdrawal, and combat-timing evidence in the campaign
checkpoint. Older preparation records must not replace the failed run's audit;
the saved selector and group state remain diagnostic only on reconnect.
Familiar-backed route selection and combat share the random-withdrawal audit:
each possible encounter room needs an NPC-usable exit, and every usable exit
must exclude source aggressors, attack programs, unsafe specials, and possible
fight joiners. Include full source wandering reach, not the short target-search
budget. Recheck the actual live encounter room before ordering the familiar;
a safe reset room does not authorize a displaced encounter.

Combat-pouch audits at departure, repacking, and logout share a bounded reply
buffer. Require the complete contents listing before replacing either potion
ledger; unrelated room or healer text is not an empty-pouch observation. After
five seconds without confirmation, preserve the previous ledger and return to
healer logout without hunting or retrying the audit. A confirmed empty listing
does clear old quantities. Newly discovered potion keywords still require the
existing source-safety checks; ambiguous potions require retained provenance.
Treat a completed DD4 prompt as a line boundary before matching the pouch
header: unsolicited healer output can place that prompt immediately before
the actual reply without a newline. Preserve the complete-listing requirement.
If the check starts partway through that preceding prompt, retain only its
recognized unfinished prompt prefix from the bounded current-line tail. Never
seed a new audit with old listing contents, a complete prompt, or unrelated
text. Clear the tail on disconnect; an incomplete new listing still cannot
replace either inventory ledger.

When choosing a loose combat potion, skip keywords already attempted in that
preparation and potions deliberately evicted to free a sanctuary slot. Continue
to the next source-safe carried potion instead of letting the first skipped
healing potion end preparation. Require the existing eviction acknowledgement
before stowing; missing replies retain the bounded abort, and only acknowledged
placement adds a pouch reserve. Run 16448 live-confirmed `get ochre beltpouch`
followed by `put all.purple pouch`, correcting runs 16446/16447's wasted travel.
This changes packing only, not sanctuary admission or combat authorization.

One later source-ranked retry may be armed for the exact five-second pouch
timeout only when the same-boot, same-level result has no target, consider,
absence, crowd, or XP-loss evidence and exactly one current-band autonomous-safe
candidate matches. Keep that marker through healer and other maintenance
segments and unrelated source-ranked hunts; consume it only when that exact
policy is dispatched, and close it after the attempt whether or not it kills.
This does not retry a pouch audit inside the failed run or relax any route or
combat gate. When the exact policy is present only in the same-boot
city-route-attempt ledger, this one retry may pass that attempted marker; any
city-blocked or caller-excluded policy remains closed, and the new segment
must perform its live route preflight again. The split-color prefix repair has
captured-transcript and offline-test coverage; a live retry remains unproved.

Gear acquisition uses the same per-category capacities as stance selection.
Compare a candidate with the weakest selected slot, or an empty slot, after
including carried alternatives. Preserve actual duplicate-item quantities, but
never add the structured equipment snapshot to its duplicate textual summary.
An improved rank is not permission to bypass source route or combat gates.
Never derive a live `n.keyword` selector by numbering every prototype in the
world source catalog. DD4 resolves that ordinal against the current carried
items or shop listing; use the exact item's source keyword, then require the
fresh `eq all` result to confirm a wielded or worn upgrade.

Weapon prototype values are not live damage dice. DD4 `create_object` generates
minimum/maximum damage from the loaded level, with two fuzzy rolls per endpoint;
`one_hit` draws uniformly between those live values. Source gear ranking uses
the conservative generated floor, never the prototype's apparent dice product.
Keep that estimate separate from an identified instance, especially constructed
or body-part weapons. Telnet `Char.Worn` does not supply damage endpoints, and
legacy `instance_id` zero does not uniquely identify an item. Human `identify`
requires an inventory object: remove the exact worn weapon while awake at the
healer, identify it, and re-wield it with confirmation before leaving. A generic
scenario's completed status alone does not confirm `quit`; require the farewell
or use the existing bounded return-home worker to finish recovery and logout.
For ordinary field preparation, the registered `identify` action requires a
positive observed proficiency, healer room 3054, standing, no combat, sufficient
mana plus reserve, one source-known removable weapon, and an unambiguous command
keyword. Permit one inspection per connection, with five seconds per reply.
Read the complete name, level, and min/max damage; confirm `wield` and a fresh
`eq all` listing before using that reading. On identification timeout, make
one rearm attempt; a failed rearm ends the hunt at the healer. Armour changes
do not invalidate weapon identity, but weapon removal, disarm, a changed worn
record, or reconnect do. Persist `campaign_weapon_damage_audit` for inspection
only; it never authorizes damage on another connection, including positive IDs.
The pre-login estimator uses generated floors, with the existing independently
audited natural-form damage contract kept separate. Live encounter budgets may
use the confirmed reading without changing route, HP, or finite-action gates.

Pre-level equipment may narrow the existing ten-percent-of-level window only
for source-known, plain, unequipped single targets without a familiar, gate
fight, or admitted bystander. Include the area and inherited mobile XP
modifiers, source level fuzz, best ordinary popularity/random reward, full HP
damage credit, regeneration over the bounded worker lifetime, and final-hit
allowance. Unknown source syntax, rank, specials, or output retains the original
window. Keep each level/target window monotonic during the connection so a gear
swap cannot oscillate its own threshold; save `pre_level_gear_windows` as
diagnostic evidence only. Reevaluate before each encounter, retain recovery
precedence and ordinary stat-training preparation, and never swap while asleep
or fighting. This is reward planning, not a promise about every possible XP
source and not permission to change combat or route gates.

While the project is active, run exactly one regression batch each local
calendar day. Use focused tests for routine changes or the full suite at a
coherent milestone, never both on the same day.
Record it before starting in ignored `runs/regression_test_batches.json`, using
the Pacific/Auckland calendar date, and record the outcome afterward. A failed
batch consumes the day's allowance; do not rerun tests or start another
regression batch that day.

When flight funding is unavailable, a fresh ground search with no eligible
target may hand over to the next registered current-level policy even if the
three-attempt ground budget is not spent. Preserve its count and the funding
marker; never consume empty attempts to unlock an alternative. A pending exact
locator retry remains first. Quest fallback and cooldown waits are available
only when a source-derived next-level QP shortfall blocks progression; with no
shortfall, skip optional questing and keep selecting current-band XP. Once a
QP gate is active, retain the live assignment and `nextquest` cadence gates.
Ground funding fallbacks and their rotation must retain the main selector's
bounded capacity-only admission, including its independently audited route
program allowance. Recheck the current band, movement, kill count, protection,
and below-band evidence. Other source rejections and live crowd, identity,
consider, and combat limits remain unchanged.

An otherwise selected hunt that needs sanctuary may reach the bounded quest
request only when a source-derived QP shortfall blocks the next level and its
reserve/recovery attempts are exhausted. Require a recovered healer checkpoint,
carried food, observed quest status, nonnegative fame, no active quest, and a
zero live timer. Preserve sanctuary counts and protection evidence. Any assignment still needs its own source
route and combat approval; rejection returns safely, and DD4's cooldown
controls when another request becomes eligible. Run 15527 exercised the
handoff but abandoned its unsafe assignment, earning no XP. New checks are
saved, unrun.

Selection alone does not spend the quest request. Record dispatch only when
the command is actually sent; after an ambiguous interruption, obtain fresh
quest status before deciding whether to request again. An active assignment or
positive `nextquest` closes the request gate. A later zero timer reopens it,
regardless of earlier campaign request markers. If a request made at zero has
no assignment but DD4 starts a new positive timer, that is a fresh cooldown
cycle, not a per-level or per-reboot cap. Clear the prior wait marker, stay at
the safe healer while the new timer runs, and request again as soon as it
reaches zero. A stale earlier countdown must not prevent a live timer refresh.
This grants no movement or combat permission.

A completed current-boot funding kill with a pending purchase/funding marker
must liquidate new saleable loot before waiting for an ordinary loot batch,
even when carried coins exceed a provisional purchase-price estimate. Keep
the retained-inventory baseline and shared city-shop route checks ahead of
this priority; neither unchanged gear nor a blocked crossing grants a retry.
Only observed sales count as funding proceeds. A selected sale also precedes
the pending flight-purchase preference: converting loot cannot spend the
coins reserved for that purchase, and an estimated price is not a live quote.

Routine repository, source refresh, tests, live runs, and exact process audits
are already authorized. Use ordinary available tools; do not ask again or
manufacture an escalation. If an external permission review times out, retry
once promptly, then defer that operation and continue useful local work. Never
wait indefinitely for an invisible review or repeatedly poll unchanged failure.

At the 9:00 PM Pacific/Auckland checkpoint, make at most one local commit
attempt per day: commit a coherent, reviewed change set only. The user handles
all remote pushes and merges; never change a remote unless explicitly asked.
Bound the local attempt to 60 seconds. A failure consumes the day's attempt;
record it and do not retry for 24 hours. Do not commit unrelated or unreviewed
worktree changes. Record the attempt and next eligible timestamp in ignored
`runs/local_commit_attempt.json`, including success or failure when no commit
was created. Use native filesystem operations and verify absolute targets
before any recursive move or delete.

Read-only campaign selection probes must load the same source world, gear
catalog, and relevant history as public startup. A missing inspection dependency
is not a live capability defect. Inspect returned tool results before composing
the commentary that reports them; do not combine dependent evidence queries
and prewritten conclusions in one tool batch.

Use `python -m dd4tester show-combat-readiness --level N --class CLASS`
for a bounded, offline view of the current output envelope, durable campaign
constraints, source-band targets, gear blockers, and quest readiness. The report
keeps GMCP alignment and fame separate and shows the questmaster route, quest
point level gate, and whether a fresh request is source-eligible. Add
`--character NAME` and `--all-areas` when comparing a saved campaign across the
full source map. It also exposes DD4's ordinary +6-or-higher fame rule and the
current bounded research horizon, alongside
the separate `ACT_IS_FAMOUS` usable band, with source candidates and their
output or safety blockers. This report is diagnostic only; it never grants live
dispatch permission.

The report's `output_fit` field is only the offensive source HP-ceiling check.
`source_gate_fit` combines source safety, source-level band, HP admission, and
sanctuary availability. It is not the campaign's final dispatch decision: it
does not include every live route check, same-boot consider record, target
cooldown, or current useful-XP probability. The report shows useful-XP
probability and known below-band or invisibility blockers where available, but
these fields remain inspection evidence and never authorize a live route.

Refresh the DD4 source periodically, roughly daily during active work. Use a
bounded ordinary pull, preserve source pins and revision evidence, and defer
network failure rather than blocking development. Source area files and C code
are legitimate game knowledge. Never modify the upstream game to make a test pass.
Area section boundaries use `boot_db`'s actual header vocabulary, including
ambient/sound and object-set sections. Hash-prefixed ASCII maps inside room or
mobile descriptions are not headers. Preserve the complete room graph, exits,
flags, resets, and special procedures; newly parsed rooms grant no exception
to route or combat checks. The October 2 correction restored 492 Underdark
rooms. Its formerly missing quest route remains blocked by real companion and
special-procedure hazards, not a missing source graph.
When an unavailable quest room has an analysis-only path through locked doors,
report its required source key VNUMs separately from a disconnected map. Never
dispatch that analysis path or treat a key listing as possession or acquisition.
For the October 7 TenTusks scroll assignment (quest room **25530**), source
proves a narrow key chain: object **25404** is carried by octopus mobile
**25405** in underwater-ground room **25426**; giving it to statue **25408**
in room **25429** creates key object **25405** and unlocks north. Mobile and
object VNUMs are separate namespaces. This explanation is not an executable
quest route. The recall-to-carrier source path is 53 commands and crosses
aggressive cave beasts **25402** in rooms **25412** and **25418**. The carrier
room is underwater-ground: `update.c` initializes air supply to two and begins
drowning damage on the second underwater update without `breathe water`. Source
lists a breathe-water philter (**3389**) in Midgaard's Magic Shop, but stock,
price, and a fresh live breathing effect must be verified before entry. Even
with the key, the 63-command shortest route to room 25530 has further source
hazards, including the fire serpent and molten uzuz; each needs its own live
route and safety admission. Never convert this chain into a blanket exception
for aggressive transit, specials, water, or locked doors. See
`docs/QUEST_ROUTE_AUDIT_2026-10-07.md` for the run-specific evidence.
Source refreshes clear source-derived routes and cooldowns, but preserve exact
XP-loss records and observed absent-target results from the current MUD boot,
along with the matching absence cooldowns. A local source update must not erase
live evidence and silently reopen a failed fight or an expensive empty route;
evidence from an older boot is discarded. Preserve a same-boot loss as a block
on that exact hunt, while dropping old target-HP and route-only retry evidence;
stale source estimates never authorize a retry.
The estimator mirrors the pinned source's inherited and area `MobHPMod` and
`MobDamMod` scalars. `MobDamMod` is applied to each positive NPC attack before
sanctuary or critical arithmetic; an unresolved scalar is a hard rejection for
combat and transit budgets. It also credits `fight.c:do_knife_toss`'s
eye-dependent face-hit double only when parsed target body-form evidence proves
eyes; unknown anatomy remains uncredited.
Area headers are parsed with the same distinction as `db.c:load_area`: the
first two values describe the display band, while the third and fourth values
are the movement-enforced low/high gate used by `act_move.c`. Candidate
endpoints and resource routes are rejected when the character cannot enter a
room at the enforced level, and `-4 -4` safety areas remain inaccessible to
ordinary player characters. A display band is evidence for ranking, never
permission to dispatch a route.
The source Circus flight reserve begins with `buy ticket`. DD4's `do_buy`
rejects all shop purchases while fame is below zero, so a live ticket refusal is
recorded as `reputation_blocked` and cannot be reopened by `--retry-stalled`.
For negative-fame recovery, the only current gas-special exception is the
source-famous Green Dragon mobile **6112**. Its admission requires the exact
`spec_breath_gas` procedure, sanctuary, a source-validated route and HP budget,
and healer mobile **3012**'s `spec_cast_adept` recovery, which can cure the
resulting nausea through `cure poison`. This permits one bounded GMCP damage
probe; after sanctuary is observed, that exact contract may use the existing
finite **36-action** live horizon. The ordinary twelve-action estimate still
governs admission before sanctuary. This does not authorize generic gas
breathers, scripted specials, or an unbounded fight. Run **13407** measured
Green at **576 HP** versus Kestrel's **342-point** conservative output ceiling;
the bot withdrew before a losing exchange. Run **13408** repeated this
bounded branch after the reboot-local preparation: the first stopped at that
live HP/output gate, while the second quaffed sanctuary, observed the expected
gas special, withdrew, and recorded a **385 XP** loss before healer recovery.
Neither run produced a kill or fame change. Revision **302** fixes the separate
handoff that previously failed to carry an eligible improved-output retry into
the protected live stop; a live kill and fame change must still be recorded
before any policy is treated as proven.
The current ordinary fame search uses a bounded +9 research horizon, but DD4's
actual rule is `victim.level - player.level > 5`, or at least six levels higher,
with no game-enforced upper limit. Revision **305** additionally permits a
plain candidate whose source HP range crosses the player's maximum HP when
sanctuary is verified and the audited player output covers only the source
lower bound. The resulting stop is sanctuary-backed and always requires a
live GMCP HP/damage-window probe. A plain, unarmed current-band target may
also receive one unprotected version of that probe when its source HP range
fits the audited output: if the whole range is below the player's HP ceiling,
the upper bound must fit; if it crosses that ceiling, both the lower bound and
the uncertainty above the player's HP ceiling must fit one output window. A
passive endpoint does not waive this check. Any transit program must be one
exact low-level mobile that can be located with `where`. A nominally same-level
target may retain one additional level of source load-time fuzz only when its
audited range reaches character level minus two, and its maximum remains
within character level plus two. This does not open armed, special, unknown, or
unresolved hazards. The live target HP ceiling must still fit the finite action
budget before combat continues. A plain, unprotected probe may finish a live
target that falls just short of the warning fraction only when the target's
remaining HP and projected incoming damage fit that same bounded action budget
and health reserve. The exception ends the probe; it does not create a general
combat retry or override a special, armed, crowded, or unresolved target.
For this exact unprotected HP-fuzz probe, the initial live ceiling check may
allow the target through to the existing damage-window measurement even when
its observed maximum is slightly above the total output budget, but never above
the source-audited target HP ceiling. This is only the pre-probe handoff: the
measured remaining HP and incoming damage must still fit the bounded budget
and health reserve before combat continues.
If the first three live samples land at least 70% of the warning threshold but
fall just short, an exact unarmed target may receive one extra two-update
window when the measured exchange is at least as favorable as the ordinary
1.1:1 damage-trade floor. This also applies when incoming damage is zero. The
source action budget must cover both updates, current health must be at least
70% of maximum, and their projected damage must leave the usual field reserve.
This is only more evidence for the same admitted target; the normal output,
health, and live identity checks still decide whether the fight continues.
DD4's `do_consider` health wording compares current hit points. In the general
case, only `you are currently much healthier than` (a lead greater than 100
current HP) can authorize the passive pre-combat fallback when live enemy HP
is unavailable. `currently healthier`, `slightly healthier`, and `teensy bit`
alone do not authorize it. A source-vetted protection-recovery fallback has one
narrow exception: the exact endpoint must be a fixed, passive, unarmed mobile
with no source program or special, and its full source HP ceiling must fit the
audited player damage budget. The candidate must already pass the ordinary
source HP-range, incoming-damage, route, and same-boot attempt gates. This
allows one bounded opener to obtain live GMCP and damage-window evidence; it
does not authorize continuing combat. Run **14041** remains the reason not to
generalize from small health leads: a teensy-bit result preceded zero observed
damage and a **419 XP** loss against the diamond golem. The normal live damage
window and withdrawal path remain authoritative after any permitted opener.
This exact fallback may use a route requiring flight only when the checkpoint
proves active `fly` or `levitation` with enough remaining duration for the
route. That satisfies movement only; it does not relax the endpoint, locator,
consider, health, or damage-window gates.

Revision **324** adds one narrow Mage fallback: a practiced familiar may open
an otherwise sanctuary-gated endpoint when fresh source evidence proves that
invisibility blocks every transit aggressor. The endpoint must be a stationary,
non-aggressive, unscripted source mobile no more than five source levels below
the player, with at most one weapon and an audited staging room. This is a
bounded familiar probe, not a lower-band XP exception; the live target,
damage, output, and route gates still decide whether the fight proceeds.
After an unrelated current-level loss, one plain unarmed target may use the
same bounded probe when the audited output covers its lower HP bound and the
uncertainty above the player's HP ceiling, while the target's source peak stays
below the tighter half-HP limit. The route must be the exact source-locatable
program exception; known transit specials are allowed only when source verifies
noncombat behavior and confirms the mobile has no program or reset-loaded gear.
Unknown or combat-capable specials remain blocked. GMCP HP and the damage
window still decide whether combat continues.

Revision **325** repairs an empty-ground-frontier flight handoff. From a fed,
healthy healer checkpoint with an open Magic Shop route, the campaign may run
the ordinary source selector against a disposable ten-tick flight snapshot.
That snapshot only detects whether a source-ranked current-band flight route
exists; it is never persisted, dispatched, or treated as active flight. If the
selector finds one, the existing bounded flight workflow is chosen. It first
refreshes inventory and may quaff a carried potion only when the source spells,
source-unique keyword or current positive item selector, inventory reduction,
and resulting live flight affect all verify. Otherwise it follows the existing
fresh-price purchase path. The campaign reranks from real live state afterward,
so normal route, target, consider, output, and survival gates still control
combat. Offline coverage was added on 2026-09-30; it was not rerun because the
daily regression batch was already used. Dorrik's live handoff and carried-potion
activation remain unproved.

Run that same bounded snapshot before closing a frontier when its best ground
candidate is removed by an exhausted sanctuary gate. For this handoff, require
the hypothetical-flight selector to find a separate current-band candidate
that does not require sanctuary; otherwise continue to the existing bounded
quest or unavailable path. Preserve the exhausted sanctuary marker and every
ordinary live route, identity, consider, output, and survival check.
Campaign policy revision **336** records this selection change. Focused positive
and negative regression cases were added on 2026-10-01; they remain unrun because
the daily regression allowance was already used. `show-campaign` now includes
each listed no-sanctuary option's same-boot result and explicit retry blockers;
these remain diagnostics, never authorization to dispatch.

Revision **306** carries the source-recorded upper level bound into every
generated stop for an exact sanctuary-backed required-loot gear carrier. This
is route construction only: it does not authorize unprotected combat, broaden
ordinary progression, or alter the strict +6 fame threshold. Live acquisition
remains unproved until a run records the item and return state.
Runs **13259-13260** made two bounded Moria sanctuary-resource attempts and
returned safely without a carrier. Live run **13261** exercised the permitted
post-reset recheck and again returned safely without a carrier; run **13262**
completed a food-reserve segment without XP change. The all-area source audit
finds no other executable level-24 sanctuary reserve; later source placements
begin at level 27 or require routes that are not audited safe for this
character. Treat checkpoint **41449** as a durable resource frontier, not
permission to replay the exhausted route. Run **13275** is the current live
proof that the reconciled policy opens the full 11-stop Moria route through
rooms 4064, 4152, 4071, and 4074; the carrier was absent, so the route remains
unproved for resource acquisition.
Run **18252** exposed a locator stop after a confirmed below-band route-gate
kill in Maze room **4058**: the generic post-fight guard closed the required-
loot search. The exact room-4064 purple-potion hunt may resume its locator after
only confirmed kills from its audited route-gate VNUMs, while in a source-mapped
Maze room and within the existing eight-query limit. This resumes searching;
each fight retains its original live identity, consider, route, output, and
survival gates.

Policy revision **303** makes healer recovery explicit when a checkpoint in
room **3054** still has active poison. The exact reopened Forest
gear retry may proceed after that recovery despite the old level-24 protection
marker, but only once and only for the source-identified claw objective. Run
**13277** cleared Kestrel's poison at the healer. Run **13278** found the
Kodiak in the River bed, encountered a live poison-swarm crowd at gate room
**18027**, withdrew, retried once after healer sleep, and withdrew again without
XP loss or claw acquisition. The marker is closed for this reboot.

## Live Sessions

Use indexed latest-state lookups for terminal run outcomes, not full transcript
loads. Completion/runtime-cap and failure lookups have independent precedence;
retain the entire selected payload, explicit empty kill ledgers, and newer
events. Do not cache terminal absence or remove loss history to speed startup.
Measure public startup separately from query benchmarks and distinguish cold
from warm reads. Faster inspection is not XP or combat-readiness evidence.
On databases larger than 1 GB, startup deliberately skips building the
campaign-phase index and uses the bounded durable segment tail for loss
repair; schedule that index migration separately rather than blocking a live
resume on multi-gigabyte SQLite maintenance.
When a checkpoint contains an observed training listing for the current level
and reboot, use that compact audit as the skill capability source; do not replay
up to 4,096 historical segments. Keep the legacy event backfill for checkpoints
without that evidence, and retain visible preparation boundaries so a shared
SQLite database cannot make a live launch appear hung.
Source policy selection must reuse the immutable world catalog loaded during
campaign setup; do not reparse all area files for each selector fallback. Emit
level-aware preparation progress before expensive frontier passes, and keep
those passes bounded by the campaign outer deadline before opening gameplay.
After a source-audited crossing into one neighboring area, retain only locator
routes rooted at the new room and already vetted within that area. Allow at most
one further locator refresh and clear the neighbor-crossing fields; exact
in-area routes remain usable, but a second area crossing is never implied. Run
**14504** live-validated this path: a Dragon Cult miss routed through Midgaard
rooms **3024, 3025, 3026, 3045, 3046, and 3219** to the guild, where Ararisa
earned **240 XP** and returned safely. The focused neighbor-locator test covers
both populated and empty source-mapped routes.
When startup already has the newest campaign-segment tail, pass it to
interruption and timeout cleanup; status-only scans over the full JSON-heavy
segment table are not an acceptable live-resume path. On the shared large
database, the runtime tail is capped at eight newest segments so cold startup
does not materialize hundreds of large JSON states before a live socket opens.
When reconnect reveals a verified same-level XP drop, retain it as a campaign
loss lower bound even without a captured penalty message. Do not add it twice
to explicit loss counters, infer a death or command-level cause, or reopen a
failed hunt while repairing the counter. Use saved per-segment baselines for
idempotent history repair.
Damage-window trade checks compare target damage after observed target healing
against player damage net of observed in-window HP recovery. Future health
reserve projections still use gross player damage, so a single recovery tick
does not make the bot assume healing will continue.
Starter combat identity parsing must treat DD4's source-format swing messages
("grunts as ... takes a swing at you", "grunts and swings at you", "takes a
swing at you", and "stops swinging ... and swings at you instead") as incoming
combat. Preserve the planned endpoint target and continue through the normal
live consider, source VNUM, isolation, and damage gates; this is recognition
evidence, not permission to bypass them.
For a pending `kill` opener, a matching target's "dodges your attack" or
"parries your attack" line also confirms that the opener resolved. Keep the
normal combat wait before dispatching a between-round skill. This does not
acknowledge spells, unrelated mobiles, or incoming NPC attacks; all target,
output, and survival gates remain in force.
For a source-ranked spell action in a room with exactly one current GMCP enemy,
use that live enemy's displayed name when matching the action response. The
campaign keyword and DD4's combat display can differ (for example, `human boy`
versus `The stunned boy`). In a crowded room, retain the exact source/target
identity; never accept a generic damage line as acknowledgement.
The streaming text path must also retain an incomplete ANSI escape when a
Telnet response splits between chunks. Reassemble that escape before prompt
and area extraction; otherwise a valid endpoint room can be recorded with a
corrupted area name and the worker can reach its runtime boundary while
waiting for an acknowledgement that was already on the wire. This is a
transport/parser repair only and does not grant target or combat permission.
When a successful combat recall returns the character to the Temple of
Midgaard without an explicit combat-end line, clear the local combat target
and combat-active flags before issuing the healer-room recovery step. A stale
local target must not cause repeated recall commands or a watchdog failure;
the live room and enemy state remain authoritative.
For a familiar-backed source probe, an aggressive or scripted endpoint must
also have a source-audited outdoor no-mob staging waypoint on the outbound
route. If no such waypoint exists, reject the policy before travel; do not
enter the endpoint and hope to summon after an automatic entry attack.
Also reject a private destination with a source-reset mobile: DD4 checks room
occupancy when the follower enters, so the target and player can prevent the
pony from following even though the player entered successfully.
For an ordinary source-ranked candidate whose endpoint aggression is blocked
only by invisibility, require the learned class/subclass `invis` path and
enough current mana before selecting the candidate, including for capacity or
level-ceiling research. Reject it before opening a socket when that preparation
is absent. The separately audited familiar-probe contract is an explicit
alternative; unrelated route aggression and sanctuary recovery do not imply
invisibility permission.
Sanctuary attempt reconstruction must be idempotent. Rebuild the supplied
segment history separately from the current saved counter, seeding an omitted
prefix from the first segment's start. Retain a matching saved count as a floor
unless positive acquisition resets it. Replaying the same or overlapping window
must not add attempts; a world-time probe is not a resource hunt. Preserve
existing failure/loss evidence and do not silently lower legacy inflated counts
or reopen a terminal route while fixing replay. Such correction or revalidation
requires its own authoritative evidence.

Run gameplay serially until concurrent validation proves the shared-database
boundary. Before launch, check for an existing gameplay worker. A tool returning
a session handle means it is still running: inspect or resume that exact handle,
not a duplicate connection. Finish required workers before ending the turn.

Use the bounded public `hero` command, not manual gameplay to manufacture proof.
Normal live segments have a 300-second cap, plus separate 60-second setup and
45-second cleanup allowances. Leave the outer timeout long enough for safe
cleanup. Reset retries and segment counts are separate explicit budgets.
The Python `run_hero_request` API applies the same cap by default and treats a
missing runtime value as the default; longer runs must be explicit positive
bounded overrides. This keeps non-CLI launchers from creating an unbounded
worker accidentally.
For a self-driving multi-segment run, use `hero --autonomous`. Its supervisor
opens one bounded worker per cycle, carries the same credential and SQLite
checkpoint across cycles, and stops on success, failure, a blocked policy, or
the finite `--max-reset-waits` budget (default three). It never converts an
unchanged reboot or absent source target into an unbounded retry loop. A
`ready` result remains an intentional resume boundary, not proof of progress.
The reset budget counts completed waits; periodic progress messages inside one
wait do not consume additional wait slots.
Ctrl+C is a bounded operator stop: the command exits 130 after the worker's
durable checkpoint is preserved, and the next invocation resumes that
checkpoint. Do not start a second worker while the interrupted process is
still present; inspect the exact process and recover its campaign if required.
Scoped recovery also closes a run row left marked `running` after its linked
campaign segment has already failed, without scanning unrelated run history.

When a deep Moria sanctuary segment reaches its runtime cap at a verified quiet
waypoint, the worker records `campaign_fastwalk_resume_checkpoint` with the
route, boot, room, and stop cursor. The next same-boot invocation may rebuild
only the audited bridge from room 4064 to that waypoint and continue the exact
unfinished leg. Stale boots, malformed cursors, combat, route hazards, and
explicit aborts invalidate the cursor and force the normal source-gated route
selection. If locator narrowing has compacted the live stop list, room 4152 may
be recovered only from the completed source-verified transit stop, with a
positive live large-hobgoblin locator result, a quiet live room, and source
proof that the room is no-mob and has no mobile reset. No other waypoint gets
this fallback. The normal success-return path promotes the starter cursor only
when its explicit `runtime_boundary_requested` flag is true; older saved runs
may use the prior runtime-boundary reason text. Deep-route resume may re-anchor
only on one unambiguous audited transit stop, endpoint, or route leg; ambiguous
room matches remain closed.

Check fresh SQLite events and process state to diagnose silence. JSONL size or
stale metadata alone does not prove a hang. A pre-login socket gets a five-second
banner/creation-prompt bound; an authenticated worker gets the configured
45-second inactivity bound and one bounded reconnect. If it remains silent,
close only that exact worker and preserve interruption evidence. Never kill
unrelated Python or Codex processes. An observation timeout is not proof of
worker exit. If the bounded failure occurred before any command was sent,
checkpoint the segment as `ready` with transport-unavailable evidence; do not
mark a route hazardous, alter XP, or wait for a reboot. If commands were sent,
checkpoint the exact live state as `ready`, add the connection-loss homeward
handoff, and require the next invocation to recover at healer room 3054 before
selecting another route. These resumable transport boundaries stop the current
invocation and never authorize an autonomous retry spin.

## Gameplay And Evidence

### Skill Tree Progression

Review the active pilot's class/subclass skill tree at each level, new practice
balance, observed prerequisite unlock, subclass transition, or relevant source
change. Use a current live listing, source prerequisites and skill code, and
the actual trainer's limits.
Choose useful damage, extra attacks, between-round attacks, disarm, defenses,
and protective/damaging spells; practice their prerequisite chains deliberately.
Set an effective proficiency target, improve high-value abilities toward
mastery where worthwhile, and verify the gain and subsequent unlocks after
each lesson. Preserve physical/intellectual practice budgets, leveling's
unused-practice conversion, stat-training decisions, route safety, and action
registration. An unchanged zero balance or capped teacher is not a reason to
repeat a trainer trip; record the blocker and keep earning current-band XP.

October 13's level-38 audit, before the later Captain visit, had these verified
proficiencies:
enhanced damage **68%**, second attack **64%**, third attack **63%**, armed
combat knowledge **64%**, stun **67%**, and defense knowledge **65%**. The
healer checkpoint then had three physical practices and no intellectual
practices.
The local Midgaard Warrior teacher cannot improve the priority physical skills
under Dorrik's current practice penalty. Source data identifies Cluh'g Mani
(mobile **27205**, room **27616**) as a level-30 teacher with a higher cap; the
current planner predicts useful gains to enhanced damage (**68% to 71%**),
second attack (**64% to 69%**), and third attack (**63% to 68%**). Do not make
that 29-step trip yet: it crosses underwater rooms and needs both flight and
independent water breathing, while source hazard checks still identify the
aggressive rolling calf and Old Higue. Flight alone does not prevent drowning.
Run **17687** then completed a separate source-preflighted route to the live
Warrior Captain in room **30272**. The refreshed practice listing led to one
stun lesson (**67% to 68%**) and two shield-block lessons (**66% to 68%**); all
three physical practices were spent. He returned to healer room **3054** at
full HP with no XP loss. This is the current verified skill state; keep the
Cluh'g Mani route closed until its underwater and hazard gates can be met.
Knight protection-vs-evil/undead remains the next intellectual chain when
Dorrik earns intellectual practices.

Run **17664** tested Celia at level 38. Dorrik fled at **177/893 HP** after
his magical armor wore off and Celia was still alive. The flee cost **941 XP**;
damage earned **1,064 XP**, for only **+123 net XP**. He returned to the healer
alive, but the run records a safety loss and no completed kill. Do not
immediately replay this unchanged policy. Keep the priority skill plan active
and prefer another current-band target until a material training, gear, or
protection improvement changes the fight's expected value.

On October 13, the clean DD4 source mirror fast-forwarded from **26749cd** to
**9205f31** and the all-area level-38 candidate scan completed. It ranked the
level-37 Astral Guardian highest, but marked it caution: the source model gives
a **690 damage peak round**, the mobile wields a massive slate-grey sledgehammer,
and the route analysis reports a reachable griffin and Drunk. Treat this as the
next lead to validate, not combat authorization; require fresh exact identity,
route, live consider, protection, and output checks. The same refreshed scan
leaves Celia in caution, consistent with run **17664**'s poor net-XP result.
The upstream changes did not alter `server/src/pre_reqs`, so the recorded
Warrior/Knight practice order remains current. The refreshed `update.c` now
enforces quest points at level gain; Dorrik's **18 QP** do not block level 39,
but he will need **200 QP** before level 50.
Follow-up run **17665** safely closed the Dwarven Catacombs sanctuary route when
the west door remained locked after the source-identified open step; do not
repeat it unchanged. Run **17666** rechecked the Dwarven Ballroom after its
earlier crowd result, found the dancer alone, and earned **2,023 XP** without
loss before returning to the healer. Liquidation run **17667** sold another
dancer's suit for **4 coins** after the prior suit sold for **10**; the amulet
of protection again brought no offer. None of these runs changed Dorrik's
three physical practices or his priority-skill audit.
Run **17668** confirms the low-consider gate: Teacher's last student returned
"no match for you" and was recorded below-band without an attack. The route
then admitted the separate level-34 Yeun Sun Ho on a positive live consider;
Dorrik killed him for **2,190 XP** with no loss. Run **17669** killed the
Dwarven dancer for **2,316 XP** without loss. At the final healer checkpoint,
run **17670**, Dorrik was full, level 38, and **43,563 XP** from level 39, with
all three physical practices intact. Sale pricing is seller-specific: the
Leather Shop paid **4 coins** for a repeat dancer's suit, while the Armourer
paid **42** for another; do not assume one shop's margin applies to another.
Run **17673** confirmed the level gate independently: the chamber attendant's
live consider was "no match for you," so the below-band target was skipped.
Dorrik returned to the healer full with no XP or safety loss. Keep this
level/boot result closed and continue to a different executable policy; his
priority skills and three physical practices remain unchanged.
Run **17674** safely restocked food and water when provisions became a real
shortfall. Run **17675** killed the Dwarven dancer for **1,716 XP** with only
**38 HP** lost, then recovered at the healer. Run **17676** sold the next
dancer's suit for **2 coins** at the Leather Shop; its successive offers were
**10**, **4**, and **2** coins, while the Armourer paid **42** for another.
Dorrik remains level 38 at **1,234,603 XP**, **41,847** from level 39, with
three physical practices.
Run **17677** reached the Freeport warehouse overseer, but live consider said
"no match"; the target was skipped with no XP or safety loss despite the
source estimate. Run **17678** killed the Dwarven dancer for **1,515 XP**;
Dorrik ate the severed arm and sacrificed the corpse for one silver coin before
returning to the healer. Run **17679** sold its suit for **1 coin** at the
Leather Shop. Dorrik finished full at **1,236,118 XP**, **40,332** from level
39; the three physical practices and priority proficiencies remain unchanged.
Run **17680** killed Yeun Sun Ho for **1,713 XP** without loss. Run **17681**
killed the Dwarven dancer for **2,223 XP**, also without loss, bringing Dorrik
to **1,240,054 XP**, **36,396** from level 39. Run **17682** safely sold loot
and returned him to the healer. The next bounded campaign attempt, run **17683**,
quoted **141 copper** for a light-blue travel potion, bought and quaffed it,
verified its flight objective, and received the healer's farewell on logout.
That supply segment added no XP or loss; it provides fresh evidence that this
reboot's shop quote was affordable, not a fixed price guarantee. The campaign
was then checkpointed at the healer, level 38, with three physical practices.
Run **17684** reached the Lotus Temple but the live `consider` for Yeun Sun Ho
said “no match,” so Dorrik skipped that instance, recalled, and finished safely
without XP change. This contrasts with the earlier positive Yeun kill: judge
each live instance rather than allowing a source/name match to authorize it.
Run **17685** passed its own live gates and killed the Dwarven dancer for
**2,207 XP**; Dorrik recalled at **490/893 HP**, above the configured 20% floor,
and recovered at the healer without XP loss. Run **17686** safely sold loot.
Run **17687** used the three available physical practices at the live Captain
trainer as recorded above, then saved and quit safely at the healer. Run
**17688** safely confirmed the healer checkpoint. Run **17689** followed eight
bounded live `where citizen` relocations through the mapped Isle of Quake
rooms, but never observed a citizen at a reached endpoint; it returned safely
with `objective=not_achieved`, no kill, and no XP loss. The locator ledger
records eight attempts, not a proven target absence; do not blindly repeat the
same circuit without changed live location evidence. Run **17690** then
received a positive live consider on the Dwarven dancer, landed stun at **68%**,
and killed her for **1,531 XP** without loss. Its fresh campaign training audit
confirmed stun **68%**, shield block **68%**, and zero physical/intellectual
practices. The current campaign checkpoint **51866** is level 38 at
**1,243,792 XP**, **32,658** from level 39; other priority proficiencies remain
at their previous verified values.
Run **17691** safely sold loot. Run **17692** reached the Shrine Attendant's
registered endpoint but found no target, then returned safely without XP
change. Run **17693** passed fresh live identity and consider checks, landed
stun at **68%**, and killed the Dwarven dancer for **1,802 XP**. Dorrik finished
safely at healer room **3054**, with no XP loss. The latest checkpoint **51873**
is level 38 at **1,245,594 XP**, **30,856** from level 39. Its training audit
still shows zero practices, stun **68%**, and shield block **68%**; keep using
the trained stun in admitted fights and resume skill-tree review promptly when
a level, practice gain, or unlock changes lesson eligibility.
The next bounded campaign pass safely liquidated loot (run **17694**), bought
and verified flight from a fresh affordable shop quote (run **17695**), then
completed another source-ranked Dwarven dancer kill for **1,790 XP** (run
**17696**). Its transcript confirms the exact target passed live consider and
logout was confirmed. Checkpoint **51878** is level 38 at **1,247,384 XP**,
**29,066** from level 39. The fresh training listing remains unchanged with
zero practices, so continue using stun and do not make an empty-balance trainer
trip.
Runs **17697–17699** added no XP. The Quake candidate in room **12194** was
not reached: at Midgaard, three fresh `where drunk` checks still showed the
greeter at **Alley at Levee** and **the Pet Shop**, so departure stopped safely
before travel. Keep that exact route closed until fresh locator evidence
changes. The later Dwarven Ballroom check saw the dancer with a maid in the
room; the isolation gate marked it crowded and skipped combat. Do not retry
either unchanged condition. Checkpoint **51885** remains level 38 at
**1,247,384 XP**, **29,066** from level 39; the fresh skill audit still shows
zero practices, stun **68%**, and shield block **68%**.
A fresh all-area candidate scan ranks the level-**37** Astral Guardian in room
**1906** as the next lead: its short registered route requires flight, and the
source model estimates a **690-damage peak round** because it wields a
massive slate-grey sledgehammer. A reachable griffin and the Drunk are route
hazards. Keep this as a caution candidate, not an automatic rejection; require
fresh live route and target identity, positive consider, flight, and the normal
20% survival/output gates before deciding whether to fight.
Run **17700** checked the source-ranked sanctuary-reserve Alchemist at room
**927**, but live evidence confirmed the target absent; no sanctuary objective
or XP was achieved. Run **17701** likewise found the Shrine Attendant absent at
room **10822** and returned safely. Run **17702** then found the Dwarven dancer
alone, passed live consider, opened with stun at **68%**, and killed her for
**2,397 XP** using six Flamestrikes at **48%**. No combat loss was recorded;
the post-fight healer score was **724/911 HP**. Checkpoint **51890** is level 38
at **1,249,781 XP**, **26,669** from level 39. The fresh training listing still
shows zero practices, stun **68%**, Flamestrike **48%**, and kick **68%**.
The transcript showed kick was not used because the source-spell branch always
preempted repeatable actions. The combat loop now alternates the admitted
source-planned spell with an eligible repeatable attack, while preserving
capability and target gates; a focused sequence test is added. Syntax checking
passed; the daily regression-test allowance was already used, so the new test
has not yet been run.
Run **17703** could not liquidate loot: three bounded `where drunk` checks
still blocked the Midgaard shop route, so it stopped safely before sale. Run
**17704** then live-verified the new skill rhythm: stun, Flamestrike, kick,
Flamestrike, kick, Flamestrike. The dancer died for **2,259 XP**; Dorrik slept
at the Healer and recovered from **665/911 HP** to full without XP loss. Run
**17705** found the dancer absent at room **20516** and returned safely without
combat. Checkpoint **51897** is level 38 at **1,252,040 XP**, **24,410** from
level 39. The fresh audit remains at zero practices, with kick **68%** and
Flamestrike **48%**. Do not repeat the absent target without changed evidence.
Runs **17706** and **17708** each deferred loot liquidation safely after three
bounded checks found the source-backed Drunk blocking the city shop route. In
run **17708**, `where drunk` first returned Weapon Shop, Poor Alley, and Practice
Yard, then Main Street, Poor Alley, and Practice Yard; the route remained
blocked. Do not retry that sale route until fresh evidence makes a registered
route clear. Between them, run **17707** bought a light-blue flight potion for
the fresh quoted price of **141 copper**; `affect` confirmed `fly` for **34 MUD
hours**. The purchase succeeded but added no XP. Checkpoint **51900** remains
level 38 at **1,252,040 XP**, **24,410** from level 39, with no practices
available and no XP loss.

The October 12 level-37 audit (run **17560**) found Dorrik had no physical or
intellectual practices to spend. His useful combat skills included enhanced
damage **68%**, second attack **64%**, third attack **63%**, stun **67%**, kick
**68%**, Flamestrike **48%**, and healing magiks **52%**. Keep earning current-
band XP until practices or unlocks change; do not make an empty-balance trainer
trip. The next source-backed Warrior skill-tree target is disarm: its
prerequisites are Warrior **30%**, grip **85%**, and defense group **85%**.
Dorrik already has grip **99%** and defense knowledge **65%**; at the next
physical practice balance, refresh the live learnable list and teacher limits,
then test whether raising the defense-group path toward **85%** unlocks
disarm. Verify every lesson and unlock live. Keep comparing that path with
enhanced damage, attack-chain gains, and the Knight protection/spell chain;
source value alone never proves current trainer access.

On October 13 NZST, run **17720** refreshed Dorrik's level-38 skill listing at
healer room **3054**: enhanced damage **68%**, second attack **64%**, third
attack **63%**, stun **68%**, defense knowledge **65%**, grip **99%**, dodge
**66%**, and no physical or intellectual practices. The learnable entries
(conjuration magiks, inner force, rescue, riding techniques, and swim) were all
at **0%**. No lesson was actionable, so continue current-band XP rather than
making an empty-balance trainer trip. Recheck at the next level, practice gain,
unlock, or relevant source change; keep disarm's defense prerequisite on the
priority list once a useful practice becomes available.

October 10 runs **16891**, **16920**, and **16921** confirmed Dorrik's level-32
live `practice` listing:
enhanced damage **67%**, kick **67%**, stun **62%**, second and third attack
**63%**; `flamestrike` and `healing magiks` appeared as learnable at **0%**.
Physical and intellectual practice balances were both **zero**, so no lesson
could be taken. Run **16921** showed no proficiency change. A planner-only
check against that exact live listing, with one hypothetical practice per
type, selects `flamestrike` **0% to 45%** (intellectual) and `enhanced damage`
**67% to 100%** (physical). This does not prove teacher capacity or authorize a
lesson; recheck the actual teacher's positive gain before dispatch. Third attack
already meets its analysis target of **60%**.
Source analysis prioritizes Knight protection wards, flamestrike, and the healing
chain, but the wards were absent from this live learnable list; do not infer
trainer access or practice a lesson until fresh eligibility and capacity checks
pass. Reuse this audit until level, practice balance, unlock, subclass, or source
changes.

October 11 run **17073** refreshed Dorrik's level-33 listing at healer room
3054, then verified the nearby Cleric guildmaster accepted two practices:
`flamestrike` rose from **0%** to **27%**, then **41%**. The final listing
showed **zero** physical and intellectual practices and `healing magiks` still
learnable at **0%**. The next useful target remains `flamestrike` **45%**;
the current blocker is no intellectual practice, not trainer access. Recheck
the tree when a new practice is earned, continue that chain if still eligible,
and then reassess the healing/protection unlocks before spending further.

Run **17079** used the one-use source-output revalidation for the dwarven
musician but ended `objective=not_achieved`, `safety=loss`; Dorrik withdrew at
the 20% floor and returned to the healer. The trace shows the source budget
credited Flamestrike while the live action selector issued stun, kill, then 17
kicks and no Flamestrike. The controller now gives an exact, practised,
affordable source-planned spell priority over other repeatable attacks after
disarm, subclass setup, and control actions. The planned spell keeps the normal
mana reserve check. Its focused command-selection test is deferred because
today's regression allowance has already been used; this is not yet live proof,
and run 17079's target remains closed after its recorded loss.

October 11 runs **17130** and **17131** refreshed Dorrik's level-34 live skill
audit. Current proficiencies include enhanced damage **67%**, second attack
**64%**, third attack **63%**, kick **67%**, stun **66%**, armed combat
knowledge **64%**, defense knowledge **65%**, grip **99%**, and Flamestrike
**48%**. The observed learnable listing showed conjuration magiks, inner force,
rescue, riding techniques, and swim at **0%**; both physical and intellectual
practice balances were **zero**. Source analysis keeps enhanced damage on the
path toward **100%** and prioritizes attack-chain improvements and the
prerequisites for disarm as they become available. No lesson is currently
actionable; the immediate blocker is practice availability, and the exact
teacher's positive gain must still be verified before any training trip. Recheck
at the next level, practice gain, unlock, subclass, or source change; keep
current-band XP moving while the balance is empty.

October 11 runs **17143**, **17146**, and **17148** verified the Knight combat
sequence in live fights: consider, stun with the hammer, switch back to the
long sword, then use practiced Flamestrike between rounds. Those targets were
killed for **1,146**, **1,610**, and **1,792 XP** without an XP loss. Run
**17150** reconfirmed the level-34 skill listing and zero physical and
intellectual practices; its separate Quake target produced **1,870 XP** with
Flamestrike in the rotation. There is still no lesson to take. Continue current-
band hunts, then recheck the tree immediately on a level or practice change and
advance enhanced damage toward mastery alongside newly unlocked class skills.

October 11 run **17229** observed Dorrik at level 35 with enhanced damage
**67%**, armed combat knowledge **64%**, third attack **63%**, Flamestrike
**48%**, healing magiks **49%**, **3 physical** practices and **0
intellectual** practices. The latest saved run is **17230**, checkpoint
**50877**, at healer room **3054**. The current DD4 source revision is
`4c039fa6b0f84d51ae7d40e516977fbb8ebc6ad3`.

The Knight source requires `protect vs evil` **60%** to unlock `protect vs
undead`; the former training target incorrectly stopped at **50%**. Its target
is now **60%**, tied to the current prerequisite snapshot and covered by a
focused test. The changed training-policy fingerprint will force a fresh
campaign training audit. Neither ward appeared in the observed live learnable
listing, so live teacher support remains unproved.

Source teacher checks found no safe nearby trainer that can currently raise
enhanced damage: the level-20 Warrior teacher caps the skill at **80%**, which
cannot improve Dorrik's **67%** with his observed practice penalty. Level-25,
-30, and -35 teachers have more capacity, but their routes fail current source
hazard checks; the level-35 teacher at room **31077** would raise it to **75%**
on the next practice, but its 115-step route crosses the Barracuda reset in room
**10005** and a `spec_thief`. Strict safe-route search found no alternate.
Preserve the unused practices, do not repeat an unchanged teacher audit, and
continue executable level-35 XP policies until practice, stats, or route
evidence changes.

Run **17231** superseded that unused-practice snapshot: the live level-35
listing showed three physical practices, stun **66%**, and shield block
**62%**. At the Captain in Kerofk, one accepted lesson raised stun to **67%**;
two raised shield block to **65%** and then **66%**. The final practice count
was zero. These are verified improvements, not mastery: on the next earned
practice, refresh the full class tree and teacher limits, then favor the
highest-value reachable leveling skill rather than repeating these lessons by
habit. Run **17276** later confirmed Dorrik remains level 35 with **986,559 XP**
and no practices; keep the skill plan current while continuing XP progression.

Run **17310** advanced Dorrik to level 36 at **1,011,355 XP** and awarded
three practices. The immediate post-level run **17311** refreshed his skill
listing at the Cleric's Inner Sanctum: **3 physical, 2 intellectual**. The
guildmaster accepted two intellectual lessons, raising healing magiks from
**49% to 52%** and learning cure light at **28%**; the final balance was **3
physical, 0 intellectual**. On the next selection, use a fresh class-tree and
teacher-capacity audit to find a source-safe instructor for the physical
points. Enhanced damage remains **67%** and a high-value priority toward
mastery; also weigh the attack chain, stun, and disarm prerequisites against
the exact teacher's proven gains. Do not spend physical practices merely to
empty the balance.

Run **17313** performed that fresh level-36 audit at the Captain in Kerofk.
The reachable teacher used Dorrik's three physical practices on dodge, raising
it from **60% to 66%**; enhanced damage remained **67%**, and no practices
remain. This is a verified defensive improvement, not a reason to repeat the
same trainer visit. Continue level-36 XP progression and refresh the skill
tree at the next level, practice gain, unlock, or relevant source change; keep
enhanced damage and the attack chain ahead of lower-value options whenever a
safe teacher can actually improve them. The same run killed the dwarven dancer
for **3,242 XP**, recovered a dancer's suit, and returned safely to healer room
**3054** without XP loss. Dorrik ended at **1,014,597 XP**, **79,253 XP** from
level 37.

Run **17314** then verified the level-36 Lotus Temple route live: Dorrik
stunned Yeun Sun Ho, used Flamestrike between attacks, and killed him for
**2,742 XP**. He recalled and recovered at the healer with
`objective=achieved` and `safety=safe`; the refreshed skill audit still shows
enhanced damage **67%**, dodge **66%**, and zero practices. Continue XP
progression, then reassess the class tree immediately when new practices or
unlocks appear. Run **17318** repeated the source-ranked dancer hunt and
produced another **3,120 XP**, ending at **1,020,459 XP** with
`objective=achieved` and `safety=safe`. The same training blocker remains: no
practices are available, so continue XP progression rather than repeating the
unchanged trainer visit.
Run **17320** repeated the Lotus Temple kill and earned **2,905 XP**, ending
at **1,023,364 XP** with `objective=achieved` and `safety=safe`. The fresh
audit remains at enhanced damage **67%**, dodge **66%**, and zero practices;
continue current-band XP and recheck training on the next unlock or practice
gain. Run **17322** completed another safe dancer kill for **2,417 XP**, taking
Dorrik to **1,025,781 XP**. No new practice points or skill unlocks appeared;
the training priorities remain unchanged until the next level or practice
change. Run **17324** added **3,101 XP** from another clean Yeun Sun Ho kill,
bringing the total to **1,028,882 XP** with no XP loss. Enhanced damage remains
**67%**, dodge **66%**, and the practice balances are still empty.
Runs **17316**, **17321**, **17326**, and **17331** each found Celia (mobile
**30244**) at room **30291**, but the live crowd check counted two observed
mobiles and declined combat. All four were safe, not achieved, and produced no
XP. Keep this exact stop closed until fresh live evidence changes the room
count or target location; do not force another unchanged trip. Run **17327** then
completed a two-kill Dwarven Home circuit: the dancer paid **2,382 XP** and a
route musician paid **1,855 XP**, for **4,237 XP** total. Both were looted and
Dorrik returned safely at **1,033,119 XP**. The skill audit remains unchanged
with no practices available. Run **17332** selected Teacher's last student,
which failed live consideration; the route continued to Yeun Sun Ho and earned
**2,302 XP**. Record `safety=safe` separately from
`objective=not_achieved`, since the selected target was not killed. Dorrik ended
at **1,035,421 XP**, still level 36 with no practices.
Run **17334** demonstrates the cost of extending the circuit after its first
kill. Dorrik earned **2,136 XP** from the dwarven musician, then attacked a
1,449-HP dancer after consider said “perfect match” but “built like a tank.”
At **87/844 HP** he fled; DD4 charged **830 XP** and awarded **733** damage XP
for the escape, leaving net progress **+2,039 XP** at **1,037,460 XP**. The run
is `objective=not_achieved`, `safety=loss`; Dorrik survived and reached the
healer. Keep the exact failed dancer encounter closed unless fresh source or
live evidence changes its output/survival case. The skill audit remains
enhanced damage **67%**, dodge **66%**, and zero practices.

Run **17337** started after the source mirror advanced from **4c039fa** to
**26749cd**. Startup cleared Celia's same-boot crowd result and cooldown, so
selection sent Dorrik back toward that policy. Before departure, `where drunk`
reported the Drunk at Temple Square and the Practice Yard; three bounded waits
did not clear the route. Dorrik saved and quit safely at healer room **3054**,
with no target contact, combat, XP change, or loss. This exposed two persistence
gaps: a source refresh must retain exact same-boot crowd evidence, and a later
no-travel city block cannot supersede a crowd observation at the target room.
Both repairs and focused tests are now in the worktree; the October 11 test
allowance was already spent, so the new cases await the next daily batch.

Run **17338** confirmed both source-registered Kerofk Bartender locations were
below-band at level 36: live `consider` returned “The Bartender is no match for
you” in rooms **30246** and **30265**. No attack was issued. Dorrik returned to
healer room **3054** at **1,037,460 XP**, with full HP and movement and no loss.
Both exact policy/room sightings are saved as same-boot below-band evidence;
select a different current-band candidate rather than repeating either room.

Run **17339** tested the Freeport source-ranked circuit. Live `consider`
returned “The harbormaster is no match for you” in room **29116**, so Dorrik
did not attack him; the route's warehouse overseer in room **29129** passed
the fresh combat gates and was killed for **2,286 XP**. The segment reached its
runtime boundary, returned Dorrik to healer room **3054**, and completed a safe
save/logout with no XP loss. Final state: level **36**, **1,039,746 XP**,
**54,104 XP** to level 37, **854/862 HP**, and **441/596 movement**. The skill
audit still shows enhanced damage **67%**, dodge **66%**, and zero practices.

Run **17340** was a bounded healer setup, not progression: Dorrik restored
movement, changed from recovery gear to combat gear, checked his potion pouch,
saved, and received a confirmed farewell. Run **17341** then attempted loot
sales, but three fresh `where drunk` checks after bounded healer sleeps kept
reporting the wandering Drunk at Temple Square and Alley at Levee. No sale or
XP change occurred; the saved character remained alive at healer room **3054**
with full HP and movement. The liquidation route is closed on this evidence;
do not repeat its waits without a changed locator result. Its transcript has no
explicit `quit` acknowledgement, so verify connection status on the next
bounded login rather than assuming the logout was confirmed.

Run **17342** completed the bounded Magic Shop support purchase safely. The
live quote was **141 copper-equivalent**; Dorrik bought and quaffed one light
blue potion, and `affects` confirmed flight. He returned to healer room **3054**
and received a confirmed farewell. XP remained **1,039,746**. On the next login,
recheck `affects` rather than assuming the potion's flight duration survived
logout; keep using live prices instead of a fixed reboot-independent cost.
Run **17343** rechecked the liquidation route after a fresh locator and used the
Jeweller in room **3034**. The live `value notebook` offer was zero; Dorrik
donated the redundant notebook rather than treating the route as a funding
success. He saved and received a confirmed farewell at the healer, with no
currency or XP gain. The exact notebook/Jeweller zero-offer pair is recorded;
do not repeat it unless the item or shop evidence changes.
Run **17344** selected the source-ranked Kaladim hunt for “a large knife,” but
the audited route required live invisibility to cross its source-known
aggression. Dorrik has no learned, usable invisibility spell or verified
substitute; the safe-origin preflight therefore returned him to healer room
**3054** before field departure. He saved and logged out safely with no combat,
XP change, or loss. The same live `practice` audit confirmed zero physical and
intellectual practices. Keep this route closed until its invisibility gate can
actually be met; do not spend another cycle rediscovering the same blocker.
Run **17345** returned to the Lotus Temple route after the source audit
confirmed its level-18 small green lizard cannot join the level-36 fight.
Fresh live evidence found Yeun Sun Ho, `consider` admitted him, and the bot
recorded a confirmed kill for **1,836 XP**. Dorrik finished without loss,
recovered and logged out safely at healer room **3054**: **1,041,582 XP**,
**52,268 XP** to level 37, and **862/862 HP**. The skill audit remained
enhanced damage **67%**, dodge **66%**, with zero practices; refresh it after
the next practice gain or level transition.
The currency snapshot rose from **1** to **2 silver** across run **17345** with
no shop sale in that segment, a likely coin source from the encounter; keep it
as a live observation, not a general drop guarantee. Run **17346** found no
eligible sale candidate and completed a short save/logout at the healer with
no further XP or currency change. Do not repeat that empty liquidation check.
Run **17347** spent **177.6 seconds** reaching the Lotus Temple chamber
attendant; exact live `consider` returned “Chamber attendant is no match for
you.” No attack was issued. Dorrik returned and logged out safely at healer
room **3054**, full on HP, mana, and movement, with no XP change or loss. Keep
the exact room/target closed as same-boot below-band evidence and prefer a
different current-band policy over repeating this long route.
Run **17348** then found Yeun Sun Ho again on a fresh live route and passed a
new `consider`. The hammer stun landed (“causing him to buckle and collapse”);
Dorrik switched back to his primary and confirmed the kill for **1,390 XP**.
The **184.7-second** run finished without loss or combat timeout and logged out
safely at healer room **3054**. Currency rose by one silver (**2** to **3**)
without a shop sale, a second encounter-level coin observation. Final progress
is **1,042,972 XP**, **50,878 XP** to level 37. The skill audit remains
enhanced damage **67%**, dodge **66%**, with zero practices.

Run **17187** reached Yeun Sun Ho in room 10771 but ended without considering
the level-34 target: the crowd gate treated its level-18 small green lizard
companion's `spec_poison` as an active threat. `special.c:2530-2547` shows
`spec_poison` only bites a character already fighting that lizard, and the
source level window proves this lizard cannot join Dorrik's fight. The room
hazard check now consults the existing source-backed non-assisting proof before
blocking combat-only specials, while retaining guard and joinable-poisoner
hazards. A focused regression case covers below-band versus joinable poisoners;
it has not been run because today's regression batch was already used, and this
route still needs live proof before being treated as productive.

Run **17188** is a live calibration: Dorrik considered the source-ranked
Gambler at two Kerofk rooms and DD4 returned “The Gambler is no match for you”
both times. `act_info.c` computes `diff = victim->level - ch->level`; this
message is the `diff <= -5` branch, so no attack was issued and the exact
candidate is now below-band evidence for this level and boot. Its source level
is 28, but the live load landed at least five levels below Dorrik. Preserve the
negative result rather than reopening the same target without changed evidence.

Keep three run outcomes separate: execution says whether the bounded worker
finished its procedure, objective says whether the stated goal is proved, and
safety records deaths or losses. A safe abort may be `execution=success` and
`safety=safe` while the objective is `not_achieved`. Do not infer success from
a default level value for maintenance work or reuse a stored positive objective
claim when current evidence is unknown. Quest reward requires an observed
positive quest-point delta; level transition is a separate explicit condition.
Required-item objectives must be recorded in run context and matched to
distinct acquired or carried entries. Older campaign summaries may supply
cached time/progress metrics, but their positive objective claims remain
`unknown` until a bounded summary refresh verifies them.

Midgaard recovery and logout belong at healer room 3054, one north of recall,
not the Mage's Laboratory. Wake to eat/drink during sleep when needed; never
change equipment asleep. Never log out in Purgatory: recover the corpse, loot,
restore gear, leave the portal, then hand off once to healer recovery.

For urgent source-food routes, wake from healer sleep only to use carried food
or water, or when the registered route's movement threshold is met. If starving
without supplies and still below that threshold, keep sleeping until the route
is affordable; do not alternate stand/sleep at unchanged movement or depart
below the registered budget. This avoids waiting for HP recovery while
starving without stranding the character in a no-progress loop.

On DD4, an invisibility affect at duration 0 can still be active until the next
30-second affect update, and `spell_invis` rejects a recast while that affect
remains. For a source-registered visibility route starting at recall, do not
cast or travel on a duration below 2: go north to room 3054, sleep, and check
at most twice at 30-second intervals. Once GMCP removes the affect, wake, return
south to recall, and cast again. If it remains after the bounded checks, stop
at the healer; never enter the route without fresh observed invisibility.

Optional loot-sale trips must use a fresh live `where drunk` check, even when
the source-bounded city-transit exception is otherwise available. A shop visit
does not justify accepting a greet attack: the cityguard may join the drunk's
fight, turning a small kill into a costly withdrawal. A source estimate or an
older route clearance is not a substitute for the live check.

Field recall is an asynchronous command: keep it in flight until a real
Temple-of-Midgaard room response or equivalent authoritative room update is
observed. The runner may use the decision-time `CharacterState` room as the
recall origin when the text parser is one event batch behind; a missing
immediate response is not an immediate recall failure. The normal bounded
inactivity and reconnect watchdogs still apply.

If a flee fails during a recallable emergency, try fleeing once more when the
character is still at least half healthy and an enemy is still present. This
single retry avoids paying an unnecessary recall penalty while combat is still
active. Poison, low health, no-recall rooms, and a second failed flee use the
existing direct-return path instead; never spin on repeated escape attempts.

Optimize useful kills and net XP per complete journey. Keep attacking viable
targets until a meaningful health, protection, nutrition, movement, or runtime
boundary. Do not kill below-band targets for XP, infer emptiness from one room,
or treat sanctuary expiry alone as a losing fight. An exact source-required
resource or loot target may be admitted below-band only with positive carrier
evidence, a bounded safe route, and an explicit missing-resource objective; its
XP is maintenance evidence, never progression evidence. Retain source risk,
crowd, consider, and observed loss gates. Repeated attempts need changed
evidence.

Continue pursuing eligible current-band XP regardless of how recently the MUD
rebooted. A reboot can improve a particular target's XP or refresh a reset-based
resource, but it is never a general reason to pause hunting. Wait only for a
specific reset-dependent objective; if that route is cooling down or exhausted,
choose another worthwhile policy that passes the same live safety gates.

When an urgent source-ranked food run starts with no carried food, the planner
may chain a distinct, same-area source food reset when the complete route still
fits the movement budget and both legs pass the normal source and live-navigation
gates. Keep every required food item in the pending-reserve check, including
earlier stops after the field cursor advances. Do not consume the first item
while a later stop is outstanding; after one item is eaten, retain any remaining
source-verified food for the next recovery window.

Source-ranked routes may carry one source-validated borderline transit
aggressor whose maximum fuzzy level is exactly four below the character. The
route must register that mobile's exact source VNUM, and the live encounter
must still be one isolated GMCP identity at or below the useful-XP floor with
normal health, nutrition, consideration, and combat gates satisfied. Finish
that single defensive interruption through the existing bounded transit-fight
state machine, record it as maintenance, and then resume or return according
to the route contract. A same-room crowd of source-known below-band mobiles is
rejected before combat; do not fight one member and flee the rest. Fixed routes,
unregistered VNUMs, crowds, specials, programs, or useful-band live rolls remain
withdrawal conditions.

A world-time probe may recheck a recorded city-shop obstruction once from healer
3054. Only a complete, positive off-route locator from that successful run,
with the same observed reboot, can release route cooldowns. Missing or absent
locations, cached checkpoint evidence, and actual purchase failures cannot do
so. This supersedes kill-only aging for that positive revalidation case, not
the normal shop preflight or any combat-loss gate. No additional wait, segment,
loan, or purchase is authorized by the probe.

During loot liquidation, if the locator blocks one planned buyer but another
already-planned compatible buyer has a route that avoids every observed hazard
room, defer only the blocked entries and complete the safe sales. The hazard
and its cooldown remain evidence for later retry; this does not authorize a
new shop route, clear a live obstruction, or turn unsold equipment into XP.

If a compatible shop returns DD4's generic uninterested response, preserve the
refusal and try at most one other source-compatible safe buyer, excluding every
shop already attempted for that item. This distinguishes a shop-specific
refusal from a zero-value or otherwise unsellable object without creating a
shop loop. If the alternate also refuses, record no proceeds and donate or
sacrifice the item according to the normal release rules.

The same rule applies to a field-city departure that stopped after its bounded
healer waits. Persist `campaign_field_city_preflight` with its level, reboot,
locations, stop evidence, and exact policy ID. A same-level, same-reboot
continuation cools down that exact route while another source-ranked route may
run its own bounded preflight. Legacy checkpoints without a policy ID do not
close the whole source frontier: the selected candidate may make one normal
preflight, and its policy ID is saved before the live segment so an interrupted
attempt cannot blindly reconnect to that route. Confirmed blocks accumulate in
a level- and reboot-scoped policy ledger, surviving healer recovery without
reopening earlier failed routes. A level change or reboot expires that ledger.
The route check still grants no permission to cross a live hazard or engage a
target; all existing movement, health, transit, and combat gates remain active.

If a live `where drunk` result blocks only the Midgaard prefix of a
healer-origin hunt route, the runner may try one source-mapped detour to the
same first outside-city waypoint. This applies both when the healer departure
check finds the Drunk and when a fresh route-level locator at room 3001 finds
it, even if no separate healer-side preflight ran. Every reported room name must
map to the Midgaard source map; the detour must avoid those rooms, add no more
than 16 commands, pass source hazard checks except for the exact bounded drunk,
and leave enough movement for the revised route plus its 15-point reserve. The
player must be at least 95% healthy. Unknown locations, a matching location
later on the target route, custom return commands, or any other hazard refuse
the detour. The runner then repeats `where drunk` on the revised route before
moving; a continued obstruction uses the ordinary bounded waits and cooldown.
If the revised healer-side route is newly blocked by a changed location set, or
a fresh `where drunk` at safe recall room 3001 reports a different Midgaard
location set on the route prefix, allow one separate corrective detour from the
new live evidence. Preserve both location sets and detour records, require the
same source mapping, hazard, health, and movement gates, and repeat the locator
before departure. No third detour is allowed; a still-blocked route returns
safely and is checkpointed unavailable.
If the exact source-ranked policy is otherwise the only executable current-band
candidate, one persisted revalidation may reopen it once. Arm only from the
same-level, same-boot, same-source-revision successful no-travel segment when
the saved evidence contains the first mapped detour, a changed later locator,
unchanged XP and movement, no loss, and no attempted correction. Consume the
marker before starting a new segment, reconstruct the first detour from the
current source map, and require its evidence to match exactly before passing it
to the runner. The runner must query live locations again and use the existing
health, movement, source-hazard, and correction checks. A reconstruction
mismatch, other live hazard, or second attempt stays closed; this does not
clear other cooldowns or grant combat permission.
There is one separate full-route case for an exact source-ranked policy whose
healer departure was blocked before any outbound movement. It may be reopened
once only after ordinary current-band selection finds no executable target, at
a living healer checkpoint at least 95% healthy, and only when a later
same-level, same-boot, same-source-revision locator is complete, unblocked,
and reports a changed location set. Prove that observation from a bounded
successful segment whose start/end locator sets differ and whose level, boot,
source revision, XP, loss, and kill evidence remain unchanged. The locator's
run ID must match its segment row; legacy records without one need changed
start/end location sets. The earlier successful segment
must show three bounded waits, `outbound_index=0`, unchanged XP and loss totals,
and no completed or objective kills. Map every earlier location name to Midgaard
source rooms, require the original shortest route to cross one, and register
only an alternate source route that avoids all of them and adds 21 or 22
commands. Keep the old city-blocked policy ledger intact and persist a separate
one-use marker. Re-rank only that exact policy; consume the marker before its
segment and require a fresh live locator plus all normal route, health,
movement, source-output, protection, consider, and combat gates. Any mismatch,
new obstruction, unavailable route, or second attempt closes the exception;
it never clears cooldowns or grants combat permission.
If a source refresh intervenes, allow one distinct refresh revalidation only
when the earlier blocked segment and later changed, unblocked locator were
both recorded under the same prior revision, and the current-source candidate
still has the exact policy, mobile VNUM, room, and route. If the blocked
segment fell outside the normal eight-row tail, fetch only that policy's
latest segment with the bounded 256-row lookup; never expand checkpoint
history. Persist this separately as
`campaign_field_city_source_refresh_revalidation`; retain the old route marker
and blocked-policy ledger unchanged. Match the locator to its exact successful
segment/run in the bounded recent history. The fresh live locator and every
normal gate still apply.
The same source-refresh marker may carry `route_clear_recheck` when the old
blocked and later clear locator segments share their prior source revision and
the current-source candidate retains the identical route. Map every old and new
city label to rooms; require the old blocker on that route and all later
locations outside it. This reopens only the exact route for one fresh live
preflight; preserve the earlier clear-route marker and blocked-policy ledger.
Release that closure only after a linked positive-XP kill and safe healer return.
A city-blocked policy must not short-circuit offline source selection: keep
that exact policy excluded unless its one-use marker is pending or its exact
route-clear recheck has verified productive completion, but allow
other current-band candidates to pass their normal source and route gates.

There is one distinct unchanged-route recheck when a wandering city blocker
has moved completely off the route. After ordinary current-band selection and
the existing detour rechecks find nothing executable, require a recovered
healer checkpoint, one plain unarmed candidate passing every independent
current-band, useful-XP, output, protection, flight, and target-loss gate, and
a later successful run-linked locator with complete changed location evidence.
The campaign can obtain that observation itself: after ordinary selection
closes, a linked successful safe no-travel city stop with three waits may
receive one `campaign_field_city_observation`. Require the same current
source, level, boot, XP, loss, and recovered healer boundaries. Persist it
before dispatch, use the ordinary world-time worker with the exact saved city
route labels, keep reading through at most three 12-second waits, and save/quit
at healer 3054. No outbound command or attack is permitted. A complete clear
locator is a next-segment handoff, not an area-reset wait or XP progress.
Failure or continued obstruction consumes the observation and stops.
The existing clear-route marker may cover a source-proved small plain
population. Require its full reset audit and ordinary no-reserve output proof,
plus independently measured same-boot useful-kill history after the fresh-search
cap. A no-travel city stop must not erase that historical reward, while weak
individual receipts remain recorded and every new target still gets fresh
isolation/consider. Only the exact pending marker may pass the old route-derived
capacity, cooldown, and incomplete-visit filters; every real target loss,
crowd, absence, changed route, and explicit exclusion remains authoritative.
Map every duplicate city room label and prove all current locations lie
outside the entire unchanged source route. The earlier exact-policy segment
must have stopped before departure after three waits, returned to healer,
and changed neither XP, loss, level, boot, nor its own source revision. It
must contain no kill, detour, or correction; its saved mobile, endpoint, and
commands must match the current source candidate exactly. Different source
revisions do not authorize a changed path.

A separate dynamic preflight retry may reopen one exact plain current-band
source hunt after its `where drunk` check at room 3001 finds the source Drunk
(mobile 3064) on Temple Square and exhausts three bounded checks. Arm it only
after ordinary current-band selection and city-detour rechecks find nothing
executable. The linked successful prior segment must retain the exact source
revision, policy, mobile, room, and route; unchanged level, boot, XP, and loss;
three route-preflight retries; no target, consider, kill, or combat evidence;
and a full-health return to healer 3054. The current checkpoint and exact
retryable route-hazard result must still match that evidence. Persist one
marker and consume it before connecting. It may reopen only that route's
cooldown for a fresh healer and room-3001 locator; every normal route, live
identity, consider, output, protection, and combat gate remains in force. Any
new hazard, mismatch, interruption, or failed attempt closes it permanently
for that level/boot. It does not clear other cooldowns or route exclusions.
If the target is past the three-kill fresh-search cap, the ordinary productive
repeat selector must independently admit that exact policy using all ranked
candidates and the normalized XP ledger. The route marker itself is never
productivity evidence; record `repeat_after_kill_cap` when this gate passes.
The general dynamic-hazard reset guard yields only while this exact marker is
pending and still matches the selected candidate and saved result.
Repair one legacy closed marker only when it lacks that field, records the
exact offline source/current-band gate closure, remains unattempted, and still
matches the same run, route, boot, level, and source revision. Consume that
repair on re-arming; never reopen a marker after dispatch or another failure.

Persist `campaign_field_city_clear_route_revalidation` separately, preserve the
old closure ledger, and consume it before dispatch. One marker per level/boot
is the limit. When the exact old segment is beyond the eight-row tail and
256-row metadata window, `get_indexed_campaign_phase_segment_id` may obtain
one ID from `idx_campaign_segments_campaign_phase`, then hydrate only that
segment. Missing indexes or invalid rows fail closed; never expand checkpoint
history or create an index in the observation reader. This index was prepared
once for the active historical database on October 7.

At restart, promote the consumed marker only from a linked successful segment
with the exact source mobile's positive objective kill, positive net XP, no
loss, unchanged level/boot/source, a complete run-linked unblocked route, and
safe healer return. Save the verified run/segment IDs and gain as `succeeded`.
Ordinary selection may then use that exact route with fresh checks, while the
historical blocked-policy ledger remains intact. A new live city block closes
it again. Absence, failure, interrupted return, changed route, or mere safe
execution does not promote it and cannot reopen a combat loss. Runs 16440 and
16442 verified successive useful Ki-Rin kills after this route correction;
new negative/legacy-index cases are saved but unrun until the next daily window.

Because the detour replaces route commands before the area boundary, shift any
later live-maze start and resume indexes by the exact command-count difference.
The live maze must begin at its registered entry room; stale source-path indexes
must never be applied to the longer detour.
After that correction, one prior same-boot result may be revalidated only when
it records the exact pre-combat "live maze navigation reached unregistered
room" failure, the room is on the current source route before its registered
maze entry, and the recorded maze destination matches the source route. Require
no target or consider observation, kill, XP change, crowd, or cooldown. Persist
the exact policy marker and consume it before dispatch; a second failure stays
closed. This repairs route evidence only and does not relax any live gate.
A recent level-8 Circus attempt found the Drunk at Lusty Ogres
Tavern, Main Street, and the Mage's Guild entrance, then returned safely
without engaging a target. The exact mapped bypass is admitted only when the
fresh route-level locator is clear of its rooms; that check does not depend on
an earlier healer-side flag. Existing XP, health, movement, and route gates
remain authoritative. The detour reached an actual target in run 15457; the
subsequent fight lost XP, so route execution is proved, not improved throughput
or HERO progression.

Field-city obstruction checks must use only the rooms traversed by the selected
route, not a fixed list of nearby rooms. The Mud School path from healer room
3054 goes through Temple room 3001 and then north; it does not cross Temple
Square room 3005, so a drunk there must not block that route. Routes that do
cross room 3005 still require the registered live `where drunk` check.
The source-bounded city-transit shortcut does not replace this preflight for
field XP routes; check the selected route from the healer and again at recall
before crossing any reported room. DD4's Drunk greet program attacks visible
entrants regardless of alignment, so a revealed good alignment is not a bypass;
only a fresh, practiced invisibility affect can suppress that greet trigger.

An automatic world-time probe must not preempt progression once the checkpoint
already has an authoritative reboot identity and a same-boot source policy
result. In that state, the next invocation must rotate to another executable
current-band route or report the actual protection/output/route blocker. The
single legacy probe remains available only when boot or policy evidence is
missing, or when an explicit reset-wait/shared-boot revalidation requires it.

This is not a blanket reboot requirement for XP. DD4 assigns a mobile's fuzzy
level when the area data loads, so a same-reboot live below-band observation
keeps that exact reset policy closed. A separate reset room for the same mobile
may load a different level, but it must pass its own fresh live `where` and
`consider` before combat. A later reboot matters only when all remaining
source-ranked targets are closed by their exact-reset evidence or by an
exhausted protection reserve; otherwise the selector continues with any
independent current-band route immediately.

A source-ranked hunt recorded as a same-boot retryable failure with a positive
cooldown is not an ordinary retry. Keep it out of normal ranking until its
cooldown ages or new evidence changes the route. The generic cooldown switch may
reopen a genuinely absent reset; retryable route or combat failures require
their matching one-use timeout, protection, familiar, route-loss, or other
source-audited revalidation. If a summoned companion does not reach the target
room, rotate to another route instead of repeating the same approach unchanged.

One reset-aware revalidation may reopen an exact source-ranked policy after a
pre-target runtime-boundary timeout. If that policy has already reached the
ordinary three-kill cap this reboot, require its latest eligible kill from the
same policy and reboot to have earned meaningful XP. This only admits the
bounded route check: current-band, source, movement, hazard, live identity,
`where`, consider, protection, and combat gates remain in force.

When a source-ranked route-program preflight finds its registered hazard in a
specific live room, the next same-boot selection may arm one narrow detour if
the room label maps to exactly one source room in the route origin's area and
the alternate path stays within the existing detour bound. The route still
runs its normal `where` preflight and all identity, crowd, consider, movement,
and combat gates. An off-route wandering result is evidence only and does not
block travel; an absent endpoint earns no XP but does not create a reboot-wide
pause. Ambiguous labels, missing paths, or a second changed hazard remain
closed.

When no high-confidence fresh route remains, a source-safe current-band target
with a material useful-XP fuzz probability may outrank capacity research. The
ordinary below-band floor still applies, and research or resource probes never
count as progression XP.

An exact same-level, same-reboot protection marker with no sanctuary reserve
and no executable independent current-band route is also a reset boundary. A
runner invoked with explicit reset retries returns `ready` with
`awaiting_area_reset` and opens no gameplay segment; the outer runner waits
once for the configured interval, then opens the maintenance world-time probe
only if no independent executable current-band route remains. Any such route
still takes priority and earns XP immediately. A capped invocation remains
`blocked`. This preserves the protection requirement and prevents repeated
invocations from becoming a terminal liveness failure or silently buying
flight against a higher-priority funding objective.

Once a world-time probe has observed `time` and is back in healer room 3054,
save and quit take precedence over optional health, mana, hunger, or movement
recovery. The starter may clear only a stale local combat flag when the live
room is authoritative, safe, no-mob, and not in combat; actual combat or
unknown room occupancy remains a hard stop. An explicit city-route observation
still runs before logout. This prevents a completed maintenance probe from
reopening the generic sleep/stand loop at the runtime boundary.

Before declaring the frontier unavailable, a living character already at the
safe healer with food must complete the normal bounded recovery if health,
movement, or mana is below the campaign readiness threshold. Re-select the
source frontier after waking. Low movement by itself is not a reason to spend
the one-shot reboot probe or wait for a reset.

When source ranking finds no executable target, persist
`campaign_source_ranked_frontier_diagnosis` in the checkpoint. This is an
offline explanation only: it records the reboot, level, candidate counts,
current-band and autonomous-safe counts, sanctuary requirements, and exact
same-boot below-band exclusions. Inspect it with `show-campaign` or the
campaign state report before deciding whether a reset wait or source refresh
is justified. Never use the diagnosis to bypass a sanctuary, route, identity,
or live-consider gate.

When the two bounded current-reboot sanctuary carrier attempts are exhausted,
arm `campaign_sanctuary_area_reset_recheck` only from a living, quiet healer
checkpoint. Without a current protection-loss marker, do not let this
maintenance route preempt an executable current-band hunt; arm it only after
the selector reports no safe hunt. The outer runner may wait once for the
configured area-reset interval, then clear the exhausted result and reset the
active attempt count to zero while retaining `prior_count`, `area_reset_cycle`,
and the reset boundary. Startup repair ignores pre-boundary sanctuary segments.
The marker becomes `attempted` before the fresh route opens. If the connection
never reaches the login prompt and zero game commands were issued, restore its
dispatch marker to pending and checkpoint transport unavailability. A later
explicit invocation may use that same one-shot recheck without another reset
wait; the current invocation must stop. Once any game command is issued, a
second route failure cannot reopen it during that reboot. Acquisition or a new
reboot remains the other reopening event. A source checkout refresh must
preserve spent-marker and attempt evidence: it may invalidate source-derived
route results, but must not let generic protection fallback or an automatic
capacity probe silently re-dispatch an exhausted Moria route. The autonomous
outer runner must honor this persisted boundary across process restarts; a
spent recheck is a durable blocker, not permission to start another area-reset
wait.

That sanctuary boundary must not suppress an independent progression retry.
From the same quiet healer checkpoint, one bounded area-reset wait may reopen
only an exact, same-boot, current-level `source-ranked-hunt-*` whose live result
is absent, whose remaining absence cooldown is at most two, and which is not
city-blocked or already attempted from the city. Persist the exact hunt that
justifies waiting. The ordinary reset handler then ages reboot-local absence
evidence and reruns current-level source ranking; the saved target does not
authorize a route or combat. Every selected route still needs the ordinary
identity, route, consider, output, protection, and action gates. Do not change
the spent sanctuary marker or attempt count, and do not wait again for the same
unchanged absence result.

The initial cooldown of three may enter that existing wait flow only when the
bounded eight-segment tail proves the latest exact hunt reached its registered
endpoint, found it absent, and returned safely without XP, kills, or loss,
after a recent useful kill of the same source mobile and policy. Both visits
must retain the current level, boot, and source revision; the plain, unarmed
candidate must not require sanctuary. A source/route change, loss, missing
endpoint sighting, city block, or intervening failed visit rejects this first
wait. Save the exact policy in `awaiting_independent_absence_reset`; the normal
completed-wait handler ages the cooldown, and the supervisor's finite budget
remains authoritative. This changes wait admission only, not target permission,
sanctuary markers, or combat-loss closures. New cases await the next daily
test window.

An automatic source-capacity entitlement does not reopen general sanctuary
recovery after its retry is terminal. One exception is the exact Moria
capacity probe: a fresh, unconsumed automatic-reset entitlement may admit the
source-audited mobile **4055**, object **4050** route even when the general
sanctuary retry is exhausted. The selector must still prove the two-room,
one-entry-per-room source capacity and all required-loot route gates. Consume
that entitlement at persisted segment start; it grants no ordinary XP hunt or
general protection fallback, and a live absence closes it for this boot.
Without an unconsumed reset entitlement, the terminal sanctuary boundary
remains closed. Run 16444's extra failed attempt remains recorded and is not
replayed.

Flight funding must not strand a healthy, fed character after its safe carrier,
one ground probe, bounded current-band XP rotation, alternate funding targets,
and available bank loan are exhausted. From a fully recovered healer
checkpoint, the campaign may then re-run normal selection without the funding
override and take an executable registered policy for the current level.
Preserve the funding marker; this handoff grants no combat permission and does
not bypass the selected policy's route, identity, consider, output, or health
gates. Do not wait for a reboot solely because flight remains unfunded.
If no registered alternative is executable either, the existing
`quest-frontier-request` is available only when a source-derived QP shortfall
blocks the next level, with fresh observed quest state and nonnegative fame.
Campaign markers remain audit history only; they do not cap requests by level
or reboot. An active quest or positive live `nextquest` closes this handoff;
once the timer reaches zero, another request is eligible under the ordinary
fame, healer, and preparation checks. This does not authorize the randomly
assigned target.

An observed positive quest cooldown never pauses current-level XP. With no
active quest, let the source-ranked candidate selector check the current band;
choose a connected cooldown wait only when a positive QP shortfall blocks the
next level. Keep
active quest steps and every ordinary route, identity, consider, output, health,
and combat gate unchanged. A cooldown wait is only the bounded fallback when no
other current-band route is executable. If an earlier wait made no counter
progress and left an unavailable cooldown checkpoint, rerun the source-ranked
selector rather than repeating that wait. Active quests and an expired timer
remain ineligible for this fallback.

For the required next-level QP gate only, preserve the connected healer wait
when exactly one live cooldown minute remains and the normal fed, recovered,
safe-healer, fame, and no-stall checks allow it. Let that bounded wait request
the quest when DD4 clears the timer before opening another hunt. This narrow
priority does not apply to optional frontier requests or reopen a stalled wait.

For noncombat Circus quest objects, `quest_access.py` audits the existing
admission purchase as a prerequisite instead of treating the locked Big Top
as unreachable. Require the exact ticket object 4400, shopkeeper mobile 4400
and its independent room-4402 reset stock, and the locked south door from
4415 to 4416. The approach and continuation must pass source hazard checks,
stay within forty commands, and use no other key. The first stop buys and
requires `a ticket`; the second unlocks, opens, and follows the checked route
to the exact quest object. A different ticket does not suppress the purchase.
Changed source identities, unsafe paths, unaffordable/failed purchases, and
missing admission stop the attempt normally. Keys are not assumed to survive
logout. Kill quests retain their independent combat admission.

Flight-shopping transit can use the existing source-bounded greeter assessment
with fresh departure readiness. Permit only one isolated, exact source-VNUM
interruption in the registered city route, with source-level/HP limits, a 70%
character-health floor, nutrition, and a 60-second deadline. Normal segment
cleanup still takes precedence. Persist `campaign_city_shop_transit` outcomes,
not a resumable combat timer. A failed transit denies the same-level/reboot
allowance; missing reboot evidence cannot reopen it. Bind a short run's missing
stamp to the campaign's known reboot when merging fresh evidence. Do not erase
field losses, reopen real purchase failures, add loans, or count these weak
defensive kills as objective XP.

The bounded city-transit allowance does not reopen routine loot sales during
an active shop-route cooldown. Defer those until productive work ages the
cooldown. Only an explicit food, flight, or lockpick funding shortfall may
force liquidation through the audited transit allowance; count only observed
sale proceeds.
Do not start a proactive field fight or familiar attack while still inside this
city corridor. Only a cityguard that attacks first may enter the exact live
source-VNUM combat check above; resume ordinary hunting after leaving the route.

If the Magic Shop purchase policy reaches the healer while `fly` or
`levitation` is still active, the worker must sleep until the existing affect
expires because DD4's spell handlers do not refresh an active flight effect.
DD4 decrements positive affects every 30-second `PULSE_TICK`; the campaign
therefore caps this maintenance worker from the observed duration plus a
fixed shop/cleanup allowance. A short expiry wait may checkpoint and resume,
but it may not consume a replacement potion or spend a full stale segment.

Use exact source keywords and connection-local target IDs. Mobile, object,
room, and object-set VNUM namespaces are distinct. Never restore pending
commands, companion ownership, or timing rights from saved checkpoints.
When several source prototypes share one visible target name, an exact command
keyword may resolve the expected prototype only when it appears on that source
prototype and on no other prototype reachable in the exact room. A shared
generic keyword remains source-ambiguous; refresh persisted candidate keywords
from the current source catalog before constructing a live route.
Every route containing a registered GREET or other source program must complete
its exact `where` preflight and adjacent-room scans, even while the character is
invisible. Leave if the named attacker is found on the planned route; invisibility
does not waive detection, scripts, or unknown hazards. Fresh invisibility is
limited to separately audited ordinary aggression with no relevant programs.
Record locator results separately from the room where the command was issued,
and never treat a skipped scan or old visibility note as completed preflight.

Revision 243 grants one revalidation only for the exact current-level/reboot
sanctuary failure produced by the obsolete visible-GREET check. Archive that
result under `campaign_sanctuary_visibility_revalidation`, consume the marker
before opening the sanctuary segment, and close it as succeeded or failed from
the fresh result. Do not remove the prior XP loss, protection requirement, or
attempt count. Absence, route failure, interruption, or death does not authorize
another attempt.

Revision 246 grants one further revalidation only when revision 243 positively
located the carrier and a fresh, completed route `where` preflight found no
planned-route hazard. Old invisibility notes alone do not qualify. Consume the
marker before connection and preserve every earlier failure. A practiced,
source-authorized invisibility route may request two sanctuary potions only when
two reachable carrier resets prove that capacity. During this recovery errand,
do not consume either potion; require two positive pickups, two successful pouch
stows, and the ordinary healer return before recording two verified reserves.

Revision 245 grants one revalidation only for revision 244's exact live shape:
the carrier was positively located, one empty relocation was attempted, no
object or objective kill was recorded, and the character returned safely with
no new loss. Persist `campaign_sanctuary_locator_label_revalidation` and consume
it before connection. `where` display labels require distinct bounded coverage;
an empty relocation path cannot revisit the current room. A pending field
`look` completes only on an actual room listing, not a prompt or status message.
Retry silence once after five seconds, then return safely. Acquisition or failure
closes the marker and never authorizes another retry.

Revision 273 repairs a markerless persistence edge for the second sanctuary
reserve. It may reopen only the exact same-boot, same-level failed handoff
whose source carrier and reachable object reset are already evidenced. Preserve
the nested failed result, loss and attempt ledgers, and protection marker; the
corrected errand requests two total pouch reserves, consumes neither, and
closes after the healer return. This narrow repair does not generalize to
below-band XP hunting.

Persist sanctuary use across the whole segment for XP-loss reconstruction while
resetting the combat latch between stops so a later fight may use its own
reserve. An unprotected first loss may receive one protected retry. A loss from
a segment that spent sanctuary is already the protected attempt and must not
authorize another potion-backed retry. For source-ranked caster combat, replace
the generic `kill` opener only with the exact source-planned direct spell after
class registration, positive observed proficiency, availability, exact target,
and a post-cast 15% mana reserve all pass. Track and acknowledge that opening
cast through the normal combat command window; otherwise retain `kill`.

During the same bounded encounter, a caster may rotate to the next practiced,
source-registered damage spell after two weak attempts if the measured target
damage is below 25% of the live target HP. Each rotation resets only the finite
damage probe, is limited to the remaining known spell list, and preserves the
existing target identity, resource, incoming-damage, and withdrawal gates. A
rotation is combat adaptation, not new source admission or proof of a kill.

For an exact sanctuary-backed, passive, unarmed HP-fuzz target, a three-sample
high-health probe that is within 10% of its required damage fraction may receive
one additional two-update window. The measured exchange must remain favourable,
the target must match the exact live VNUM, and its projected finish may exceed
the audited action budget by at most one action. This is a finite observation
extension, not a retry or permission to fight an unknown special. Damage-window
withdrawals retain gross damage, regeneration, net damage, incoming damage,
target VNUM, and room as loss evidence for later output or gear decisions.

A displaced sentinel beside the planned reset endpoint may be identified from
one fresh complete room listing only when its full source description is
globally unique, its single reset has capacity one, and source plus live exits
agree on the adjacent same-area ground route. Reject random, no-mob, locked,
wall, aggressive, or scripted cases. This is explicitly source-description
inference, not a GMCP VNUM observation. Bind the exact instance to room, stop,
level, reboot, and a 30-second lifetime; discard on movement or disconnect.
Require ordinary consider, crowd, companion, resources, and combat admission.
Persist `campaign_fastwalk_displaced_target_outcomes` for audit only, never
restore identity or reopen source-route/loss exclusions from that record.
Ordinary hunts and funding trips share the early same-area locator planner.
Reset-only required-loot hunts may reuse the same locator controller with
source-bounded carrier paths. Require a known same-area, nonconfused wanderer,
the unchanged admitted carrier/loot contract, and a verified original approach.
Query before the final approach, map exact source short names, and retain
excluded labels as sightings with no executable route, not area absence.
Search at most eight source-reachable rooms within a 24-move fallback sweep;
allow at most one existing locator refresh with a separately bounded 24-move
relocation. A carrier route that requires source-authorized practiced
invisibility may inspect at most 12 rooms under the same 24-move cap. Admit an
ordinary aggressive transit mobile only when DD4 `can_see` proves it lacks
detect-invisibility, all source programs are absent, no reset equipment can
alter detection, and every special is noncombat or combat-only. The runtime
must require and maintain the live invisibility effect. Detecting, scripted,
unknown, pre-combat, and endpoint-combat hazards remain blocked. For a
source-ranked hunt that has already passed selection, a plain endpoint
``ACT_AGGRESSIVE`` target may be included in the same route invisibility
identity when the source proves it cannot detect invisibility and has no
special or program. This only prevents an entry auto-attack; capacity,
consider, HP/output, combat, and return gates remain authoritative. Both modes
share the original runtime and command limits. Paths must be
open, known, same-area ground routes without random, private, solitary, no-recall,
wall, flight, or unresolved source transit hazards. Ambiguous room names authorize
only the mapped accessible subset, never every room with that name. Preserve
pre-entry scans, exact consideration, crowd/loot checks, and all loss/retry gates.
Retain required familiar staging on the outbound prefix, the original city
preflight, exact target/consider/crowd checks, and the normal reset fallback.
For provision-funding, the same visibility contract may admit one exact
unarmed carrier of a dynamic saleable drop, including a source-safe noncombat
special such as `spec_fido`, only after the source current-band, movement,
HP/protection, saleability, and live-identity gates pass. Carry every audited
transit mobile VNUM into the `Fastwalk`, mark the segment `funding_only`, and
exclude its XP from progression. Armed ambush endpoints, rejected targets,
scripted or unknown transit hazards, and same-boot repeats remain closed.
Do not shorten specialised transit-recovery plans a second time. An early
locator changes travel order, not candidate eligibility, movement admission,
search limits, retries, or loss history.
An early field interception must retain its connection-local route position.
After a below-band rejection, only a matching observed waypoint on an unfinished
destination-guided leg may resume that leg. Keep the rejected sighting and
require fresh consideration at later rooms. Do not mark an unvisited endpoint
consumed or start the next leg from a fictional origin. Explicit aborts, crowd
and route hazards, changed rooms, and ambiguous command-only routes do not
receive this continuation. No new candidate, search, or retry is authorized.
An intercepted evaluation owns ordinary outbound travel until resolved. A
completed bystander audit clears primary consider state, not that ownership;
resume the shared target evaluator and require the remaining exact instance's
own result. Pending checks retain their existing deadlines and attempt limits.
Never turn a no-command evaluation into movement. Combat, emergency return,
and the segment cleanup boundary retain precedence.
Register and test skills before dispatch; positive practice, equipment,
resources, target state, and safety gates remain mandatory. Honor existing
gear-mode, provision, corpse, trainer, and prerequisite contracts in the archive.

Campaign policy revision **334** enables the cleric protection chain after its
existing damage and healing priorities: protective magiks 45%, protection 40%,
then sanctuary 40%, each only when a fresh live teacher listing offers it.
Protection reduces damage only against sufficiently opposed alignments;
sanctuary halves damage while active but costs 75 mana. Existing buff upkeep,
proficiency, and mana-reserve checks remain authoritative. The revision makes
older trainer audits stale so the next eligible segment can inspect the teacher
again; it does not grant practice or spell-use permission by itself.

DD4 source revision **7953a00** adds Knight access to `protection vs evil` and
`protection vs undead`. The prerequisite identifiers are `protect vs evil` and
`protect vs undead`; keep those distinct from the castable skill names in
training data. Maintain either ward only when the current live skill listing
proves it is known and the ordinary mana reserve passes. The undead ward can
deter fresh uncommanded undead attacks or joins, but cannot end an existing
fight. `turn undead` remains analysis-only until the controller can verify all
eligible room targets, crowd risk, damage credit, and safe withdrawal. These
new source capabilities are not live proof while the server revision and
teacher listing remain unverified.

Training-audit freshness is tracked by a fingerprint of executable base-class
and subclass priorities, separately from the campaign code revision. A changed
training graph reopens at most one same-level, same-boot trainer repair; that
visit clears old practice deferrals and records the fingerprint only after a
live practice listing is observed.

A familiar may kill during the synchronous opening order, before a player
attack or enemy snapshot exists. Adopt that completed encounter only from a
pending order in the same room, exact unique source target/selector, positive
unique companion ownership/presence, and the named damage/death pair. Cancel
the player opener, retain zero XP with `objective_eligible=False`, and preserve
normal corpse looting. Never restore this pending order across connections.
Familiar damage plus another target's death in one packet is not familiar
death. A positive familiar-loss line cancels its opening without declaring the
player's still-active opponent dead. Keep these outcome repairs separate from
proof that the player can secure the next finishing blow.

World ticks and unsolicited prompts do not acknowledge summon, look, or group.
Retain one 30-second deadline across familiar preparation; silence neither
retries nor immediately fails it. Require the fresh complete room listing after
look and exact positive summon/group replies. Explicit source refusals stop
preparation. Late replies cannot restore expired ownership. Hold ordinary
travel and attack during preparation, never emergency recovery or runtime caps.
Temporary confirmation, recitation-exhaustion, and observed-mana failures use
the existing bounded route retry, not a permanent reboot-wide exclusion.
Preserve the failed record and countdown; identity/refusal, fatal, negative
consider, and loss evidence are not cleared by this classification.

A reassembled exact-target easy-kill response must reach both the solo budget
and the ordinary consider handler. Retain the request's room, target selector,
source mobile, stop, level, reboot and freshness scope. Explicit stop rejections
still take precedence. Do not assume fixtures with a pre-existing positive
consider prove that a fresh fragmented reply completes the real decision.

A fresh exact-instance easy-kill consider can narrow an ordinary source load
to character levels -4 through -2. A solo substitution requires the current
room/stop/level/reboot binding, unique target and owned companion, audited
spell capability and positive practice, full source HP/weapon/rank/special
checks, and actual proficiency-adjusted mana costs. Use the existing encounter
controller with one target; never grant companion damage credit. Confirm the
owned companion sleeps before the player attacks, and wakes before ordinary
onward travel. Each exchange permits one exact-instance order and five seconds
for a positive outcome; `Ok.` alone and late acknowledgements do not suffice.
Emergency recovery and runtime caps remain prior authorities. Persist only
`considered-solo` budget/outcome audit records, never pending orders, timers,
ownership or consider permission across connections. This does not eliminate
outdoor preparation or its mana cost, and adds no route retries or loss reset.

When the audited player output alone covers a source-ranked target's HP
ceiling, use the bounded familiar opening handoff: issue one exact familiar
attack, require its positive acknowledgement, then issue and confirm its
withdrawal before the player's opener. This is a timing guard against the
familiar taking the next automatic round, not extra combat authority. Keep
the normal familiar requirement for stronger or underfunded targets, and
retain exact ownership, selector, room, source, and live outcome checks.
Before issuing the familiar's attack, audit every open exit it could randomly
choose when fleeing. Each destination must admit NPCs and have no source-known
aggressor, combat program, unsafe special, or mobile that can join the fight;
one safe exit does not make the others safe. DD4 rejects no-mob destinations
before stopping the familiar's fight. If the handoff is optional, proceed solo
only under the registered player-output proof; otherwise reject the stop before
the attack.
Run 13053 is live evidence for the handoff and +168 player XP on Granny
Jenkins; it does not establish sustained progression or HERO proof.
Although `mounts.are` sets the pony prototype's `AFF_CHARM` bit, `db.c` removes
that bit while loading every mobile prototype. `spell_summon_familiar` only
adds the created mount as a follower, so the live pony can leave its master.
Use `order <exact selector> flee Fear` to bypass the NPC random no-op, and
require the exact `The pony has fled!` departure before the player's opener.
`Ok.` alone is only order acceptance; do not issue a sleep order after the
pony has left. Allow five seconds for confirmation. If withdrawal is
unconfirmed, abort the stop and make one direct recall attempt when legal. If
flee is unavoidable, issue it once; after it succeeds, continue the bounded
return instead of fleeing again because a snapshot or pursuer remains. A
no-command result from the retry helper is still a failure boundary; it must
not fall through to the player's damage selector or resume automatic combat
actions. In-place sleep is valid only for a separately verified charmed
companion that remains in the room.

DD4's `fight.c` awards a familiar's finishing blow to its owner only for the
witch, infernalist, necromancer, knight, and werewolf subclasses, or an
unsubclassed shifter. For other class/subclass combinations, start the ordinary
familiar withdrawal at 65% target HP instead of 45%, giving the player more
room to secure the XP. This changes only the handoff timing; target admission,
combat budgets, and emergency recovery remain unchanged.

Treat source aggression text such as `grunts as he takes a swing at you`,
`grunts and swings at you`, and `takes a swing at you as you enter` as
immediate `combat_started` evidence, even when `Char.Enemies` has not arrived.
This closes the pre-combat familiar and route-preparation workflow on the same
read; it does not grant combat permission or replace the authoritative GMCP
identity and damage gates.

For an admitted solo encounter, reprice continuation from remaining enemy HP,
current mana, observed outgoing/incoming damage, and the original command/time
budget. Do not apply the generic opening-damage fraction as an additional solo
veto. Retain source identity, companion standby, health reserves, no-progress
deadline, spell acknowledgements, and emergency withdrawal. An offline repair
does not clear the failed route's actual loss history.

Record raw input beside derived observations, reject malformed enemy snapshots
without erasing combat, and retain real loss/death history. Flush SQLite event
batches before asynchronous waits. Use indexed, bounded read-only queries for
inspection; do not scan entire transcripts or giant checkpoint histories.
Normalize CR-LF and LF-CR pairs once, including pairs split across packets,
without removing real blank lines. Reconcile each flee penalty and partial-XP
refund with its authoritative GMCP change; a prior loss in the same connection
must not disable deduplication. Compare raw progress with derived checkpoints
when totals disagree. Record corrections explicitly, preserve historical raw
events and real losses, and do not report an accounting correction as earned XP.

Separate gross shop prices, carried currency, and bank debt when reporting
funding. Current sale/proceeds records store gross values. A loan notice means
source `do_sell` credits integer half the price to carried money and half to
debt; odd-price rounding can lose a coin. Reconcile against fresh currency
snapshots and distinguish sacrifices, loot, purchases, and sales. Do not infer
spendable income or a sustainable money loop from a sale acknowledgement alone.

Reconstruct source circuits by observed stop identity, not only segment phase.
Use the authoritative run kill ledger, including explicit empty results. A
secondary kill must not promote the headline or inherit another stop's crowd.
Preserve newer negative results, whole-run death/failure, and actual segment
reboot scope. Do not let inherited result metadata override that scope.
Revision-242-and-newer terminal records already contain per-stop results; the
legacy consider migration must not rebuild them and resurrect old failures.

Funding remains objective-bearing when its authoritative ledger contains
positive, eligible XP tagged with the exact source policy and carrier VNUM.
Project only that carrier onto hunting research, retaining the funding phase,
raw ledger, and existing kill counts. Failed, fatal, XP-losing, unknown-XP,
wrong-identity, superseded, or other-reboot runs cannot promote route proof.
An explicit reset clear is superseded only by a successful attempt whose
timezone-aware start is demonstrably later than the latest matching reset
checkpoint. Unknown ordering keeps the clear. Do not resurrect older proof.
Compare an exact same-reboot latest gross sale with a known current flight
shortfall only as an income upper bound. A low-yield funding preference may
yield to an already executable ground hunt, never skip food or protection,
add a loan, or manufacture another reset allowance.
When a live funding candidate has no audited coin balance or measured
same-reboot proceeds covering the shortfall, a failed funding route, including a
completed kill whose liquidation produces no sale proceeds, may hand back to an
executable source-ranked current-band ground hunt without flight for at most
three attempts at that level and reboot. Persist its policy identity before
dispatch, then return to the funding handoff; do not turn the exception into a
ground-hunt loop or wait for reboot while safe current-band XP remains
available.
There is one more exact funding route for the current flight shortfall: the
Gnome treasury in room 1570 contains source money objects 1516 and 1517 worth
1,240 coins nominally. `db.c` independently fuzzes each denomination above ten
by ten percent in either direction unless `ITEM_DONOT_RANDOMISE` is set, so the
guaranteed total for these objects is 1,175 copper-equivalent. Compare the
current shortfall against that minimum, not the nominal total. The route crosses
eight reset entries for level-3 hobgoblin guards, but DD4's `update.c` skips
aggression when the player is more than ten levels above the mobile. Admit this
stash only when the source rooms, object VNUMs, crowd limits, route-program
audit, movement budget, and minimum payout all match. Record it as
`funding_only`; it is never ordinary XP permission, and a changed crowd or
source identity closes it.

Funding completion and objective eligibility are separate ledgers. A source-
identified below-band kill may complete an explicitly selected provision-funding
action and age its retry cooldown, while its XP remains excluded from objective
progression. Prefer the funding segment's durable `completed_kills` event over
an empty `objective_kills` list, and repair its completion marker on resume from
that exact run only. A completed funding action advances cooldown even when its
XP delta is zero. An observed below-quote balance remains actionable despite a
retry cooldown; negative fame must not override that safe funding path. None of
these repairs authorize another target or promote low-value XP.

Treat source objects flagged `ITEM_POISONED`, `ITEM_CURSED`, `ITEM_NODROP`, or
`ITEM_NOREMOVE` as non-tradeable until live shop evidence proves otherwise.
Their area-file value is not funding evidence. If a compatible shop returns
zero, retain the refusal and use the bounded donation/sacrifice cleanup path;
do not repeat the same shop route as a money loop. Likewise, an equipment
object with a known negative stat modifier, especially a ring with `-2 str`,
must not be retained solely to fill an empty wear slot. A quarantined
`bank-excess-coins` handoff may fall back to liquidation when saleable surplus
is present, but the resulting proceeds must still be observed before flight or
food service is retried.

Crowd assessment shares the existing three-probe, five-second-response budget
across single and repeated mobile identities. Require complete, unique live
selectors and source-identified ordinary mobiles. Only an exact source consider
response at or below the -5 band discounts that instance; unknown, refused,
expired or changed instances remain material. Another target's consider is
never attack authorization. Preserve level/reboot/room scope and all combat-loss
gates. Pin an ongoing source fight to its considered instance across GMCP name
changes and room refreshes; never redirect it to a same-name replacement.
Telnet GMCP currently repeats
the primary enemy record for some other combat participants, so duplicated
records do not provide authoritative identities or levels for those attackers.

An ordinary unarmed pair may use the source-estimated encounter envelope only
after two exact, fresh easy-kill considers and the normal route/target gates.
Require near-full health, source HP/peak bounds, executable class damage, and
mana priced by observed practice, not the spell's minimum alone. Retain the
source estimate as an estimate: compare combined incoming damage with measured
output while preserving emergency, unknown-attacker, and runtime exits. Both
kills share one 45-second/action budget and the original exact selectors.
If the second target has not joined, refresh and consider it normally. Movement,
disconnect, level/reboot change, or expiry discards the allowance. Persist only
audit outcomes under `campaign_fastwalk_encounter_budgets`, never reusable IDs
or combat permission. Do not erase crowd/loss evidence to force live admission.

An ordinary source-ranked stop may opt into one source-material bystander when
the room contains exactly one exact primary target and one distinct, uniquely
selected bystander. Require fresh easy-kill considers, source identity for both,
ordinary non-aggressive/non-scripted/non-special prototypes, no reset weapons,
known HP and damage modifiers, bounded reset population, near-full player
health, and one combined source budget that fits the six-action finishing
window, health reserve, and practiced resource cost. This path is never valid
for required loot, source coins, sanctuary or other protected probes, familiar
routes, or an ordinary unresolved route hazard. A single route-program
attacker is an exception only when the generated source audit proves the exact
program, mobile, level band, route, and bounded damage; the normal city/transit
gate and every other safety check still apply. It is enabled only by the
generated source-ranked stop flag; do not infer it from a name or from a generic
crowd count.

After the primary opener, the live GMCP enemy set may contain only the two
admitted source VNUMs, with the primary still present until it is defeated.
An extra, unknown, armed, special, scripted, malformed, out-of-band, stale, or
scope-changed enemy clears the admission and withdraws. Movement, reconnect,
level/reboot change, expiry, or a failed budget reprice also clears it. Record
admission, live budget, and cleanup outcomes under
`campaign_fastwalk_encounter_budgets`; these records are evidence, never
reusable combat permission. Current tests cover the path; no live acceptance
or progression claim follows until a fresh DD4 run completes it.

The server currently masks GMCP alignment as 50000 below level 10 and sends
the clamped -1000..1000 player value from level 10 onward. Preserve the raw
wire value, but never use the mask as real alignment. A revealed value at or
above 300 is necessary for the `spec_guard` special's own assistance path;
`violence_update` is a separate gate and suppresses a good bystander only
when both the bystander and player meet the exact 350 `IS_GOOD` threshold.
Use the player's alignment for player fights, not the NPC target's alignment.
A source-ranked target carrying exactly `spec_guard` is admitted past the
target-special gate only when the target and revealed player both meet that
350 threshold. Its source headbutt/smash/kick peak is included in the ordinary
damage budget; unknown alignment, mixed target specials, and every other target
special remain rejected. A guard elsewhere in the room has an independent
special: `spec_guard` and `spec_sahuagin_guard` examine the room occupant's
alignment below 300 while that occupant fights an NPC. For our fight, that is
the player, not the NPC target. There is no level cutoff in that path. This
corrects the earlier target-alignment interpretation after reviewing run 15984
and `special.c:spec_guard`/`spec_sahuagin_guard`. The 350 ordinary-assistance
gate and live non-hostility requirement remain separate and mandatory.
The GMCP and MSDP server paths differ; this is not evidence of corrupted
transport. Field city preflight shares the existing three 12-second healer
waits and locator parser, scoped to the actual source route plus fountain. A
completed absence or off-route observation permits normal departure; silence
does not. Keep its `campaign_field_city_preflight` audit separate from
shop-funding flags and retain ordinary combat/loss gates.
If a reported wandering-greeter location set has no safe detour, keep the
detour allowance available for a later fresh location set during those same
three waits. Apply at most one healer-side detour plus one changed-input
correction, either at the healer or at room 3001; do not extend the wait budget
or permit another correction after its fresh hazard check.

A successful field run that positively reports `stopped_before_departure`,
zero outbound movement, current level/reboot, a living noncombat healer state,
unchanged known XP and no kills is a departure deferral, not a target attempt.
Use only fresh runner evidence, never a merged old preflight marker. Checkpoint
the run and spent segment, retain prior funding and loss history, and stop the
invocation before target-outcome reconciliation or destination rotation. Failed
or interrupted runs keep normal recovery handling. Old historical outcomes
are not silently reclassified from incomplete markers.

Checkpoint cleanup is not a new maintenance observation. Pass
`fresh_observation=False` when reconciling an already-merged checkpoint; do not
assign an inherited field abort to the last funding candidate. Repair an already
replayed hazard only from the latest successful connected funding segment:
matching level/reboot/candidate, a newly completed acquisition, identical
inherited abort at start/end, no owning funding hazard in either segment state,
and a living noncombat healer return with known XP and no loss. Retain other
candidate hazards, source results, losses, and reset history. A later failed or
interrupted funding segment prevents clearance. Run this check after legacy
candidate inference so that inference cannot restore the cleared candidate.

Do not confuse declining a low-XP target with escaping an already-started fight.
An isolated, source-matched below-band endpoint attacker may reuse the existing
30-second active-encounter budget, including practiced spell costs and measured
damage checks. Require its fresh exact selector, registered endpoint, at least
70% health, nutrition, and no pending return, familiar, or runtime boundary.
Unknown, armed, scripted, special, extra, or out-of-source-band attackers retain
their rejection gates. Preserve the below-band sighting and incidental kill;
never promote it to objective XP or deliberately start another such encounter.
Discard the identity on departure/disconnect, and reject changed level/reboot,
selector, stop, or an expired timer. Checkpoint audits are not permissions.

Funding locators may run before reaching a wandering carrier's reset room.
Shorten only a fully known existing approach, retain its city/preflight origin,
and require an ordinary traversable same-area observation point. Random exits,
unresolved doors, missing source links, and hard route hazards retain the old
approach. Build source paths rooted at the actual locator origin; preserve the
reset-first fallback, exact source short-name matching, unknown/absent-location
handling, one relocation limit, and live target/consider/crowd/resource gates.
Do not change the candidate's source identity or reopen funding/loss history
merely because its observation point moved.

Required-loot endpoints may hand one exactly identified ordinary bystander
to the shared pre-combat consider/crowd evaluator only while a single carrier
is visibly identified and no combat has begun. Preserve the existing probe
and wait budgets. A fresh exact below-assistance result can discount that
instance through the existing encounter scope; it does not authorize the
carrier or survive reconnect, movement, expiry, or changed identity. Use the
registered target's exact matching rules: `orc` is not `large orc`.
Aggressive, scripted, special, ambiguous, or already-engaged cases retain
the required-loot safety path.

When the carrier is absent, do not confuse passive-room transit with combat
admission. The existing absence/search path may continue only with exact known
room instances, no aggressive mobile or program, and specials from the existing
noncombat/combat-only registry. Require the next already-planned same-carrier
endpoint, a current live exit, known open source links, and the normal locator
path restrictions; unknown, random, private, no-recall or flight-dependent paths
do not qualify. Ordinary resource and runtime returns retain priority. Preserve
the absence and existing area-presence evidence separately. Do not attack the
passive crowd, fabricate carrier presence, add a search or restore a pending move.

For a source-ranked target whose source HP range crosses the character's live
HP ceiling, pass the exact GMCP `Char.Enemies` records already validated by the
endpoint gate into the source damage-budget check. The budget is the audited
opening conservative damage plus the bounded repeat-action output; a live
maximum HP above it must stop opener and potion dispatch and close that target
for the current level/reboot scope. A plain, source-identified passive target
may instead pass exact `consider`, consume sanctuary, and open combat before
the first `Char.Enemies` HP snapshot; this is allowed only for the protected
HP-fuzz probe, with an audited exact selector, no script attacker, no special,
and no weapon. An aggressive target may already have engaged while its arrival
snapshot is processed; a resulting flee penalty is real evidence to retain,
not a reason to retry the same target. Never erase the loss ledger or
reclassify this boundary as a successful hunt.
The exact unprotected plain-target HP-fuzz exception above is narrower: after
its source lower-bound and uncertainty-gap checks, its first exact live maximum
may reach the bounded damage-window probe only when it does not exceed the
source-audited target ceiling. It is not permission to continue above the
measured output or health budget; targets outside that exact contract still
withdraw at the live ceiling check.
Before dispatch, reject an aggressive XP endpoint when its minimum
source-fuzzed level is at or below `character_level - 5`. Equality is unsafe:
the live mobile can load at that exact floor and attack before `consider`.

One separate source-ranked exception covers a plain, unarmed, unscripted
aggressive target only when its route carries the exact audited `where`
preflight and every transit aggressor is independently bounded. The runner may
consume sanctuary before the exact opener and obtain one live HP/damage-window
probe; the lower source HP bound must fit the fixed output budget, and any live
GMCP ceiling above that budget still forces withdrawal for this protected
opener. The separately admitted unprotected HP-fuzz probe follows the narrower
pre-probe handoff above and still requires its source ceiling and measured
damage window. This does not authorize special, armed, scripted, or otherwise
uncertain aggressive targets.

When sanctuary recovery is cooling, the runner may also try at most eight
distinct plain, unarmed, source-safe current-band targets without sanctuary.
For an HP range above the character ceiling, both the lower bound and the
uncertainty gap must fit the audited attack budget. The live endpoint then
checks the target's actual GMCP HP before the exchange can continue; a target
above that budget causes an immediate withdrawal and closes the fallback for
the reboot. This is a bounded attempt to keep XP moving, not permission to
repeat a losing route or ignore protection evidence.

A meaningful, same-boot productive kill for the exact source mobile and reset
may clear only the indoor familiar HP-fuzz gate for a repeat when no XP-loss
record exists. It does not clear current absence, crowd, route, consider, or
source combat-output evidence, and it does not authorize an unproven target.

For the same narrow HP-fuzz hurdle, two independent solo kills at exactly the
previous character level may support the matching plain, unarmed reset one
level later. Rebuild the receipt from the same-boot objective-eligible kill
ledger, safe completed run summaries, and bounded transcripts with observed
GMCP affects and no Sanctuary use; require the prior fights to stay above the
20% floor and current HP to be at least 95%. Match character, class/subclass,
mobile, reset room, and source policy exactly. The prior GMCP target max HP
must fit the current conservative source output budget. This is not an XP or
combat permission: the endpoint must still match the live identity and max HP,
pass `consider`, and pass the damage-window, output, and abort checks; any XP
loss closes the exception.

After that kind of productive kill, the exact route may also re-enter the
recent-kill rotation before its three-kill cap when the fresh frontier is
exhausted. This is a bounded fallback, not a repeat loop: current presence,
crowd, consider, route, health, and output gates still decide the next segment.

An audited special procedure may use the same pre-opener sanctuary handoff only
when its source stop is exact, unarmed, nonaggressive, and free of attack
programs, with a source-audited route and a fixed lower-bound output window.
Consume the verified sanctuary reserve before the opener, then require the
authoritative live HP ceiling and damage-window result; entry-attacking or
uncertain specials remain blocked.

A protected plain target may cross the ordinary source HP-fuzz level ceiling
only when its nominal source level is exactly character level plus one and the
existing level-ceiling admission, sanctuary, route, and lower-bound output
checks all pass. Carry that explicit probe flag into the stop so the endpoint
allows character level plus two, checks exact live level and HP, and consumes
no potion when the live budget fails. This is a single bounded measurement,
not permission to widen the level band generally.

DD4's `quest.c` rejects every new quest request while `pcdata->fame` is below
zero, before generating a target. Treat that refusal as durable eligibility
evidence and do not retry new requests until fame is nonnegative and freshly
observed; missing fame is also a hard block. Only a completed kill quest adds
positive fuzzy fame. Object, retrieve, and hoard completions award other
rewards but no fame. An already active quest may continue through normal
completion; the negative-fame gate applies to requesting a new quest, not to
abandoning or resolving an existing one.

For a normal fame-positive kill, DD4 requires a victim at least six levels
above the player (`victim.level - player.level > 5`). A famous or infamous
source mobile follows the separate `ACT_IS_FAMOUS` branch; never treat the
ordinary six-level rule as permission to attack that exception.

The campaign orders that recovery deliberately: first admit any reachable,
source-audited direct ground gear reset that improves the combat envelope and
does not require combat; then reconsider an eligible fame-awarding kill. A
pending flight-funding marker must not hide that no-combat upgrade pass, but it
continues to block flight-only and carrier actions until their own gates clear.

October 12 NZST run **17552** refreshed Dorrik's level-37 tree at healer room
**3054**: enhanced damage **68%**, second attack **64%**, third attack **63%**,
stun **67%**, kick **68%**, Flamestrike **48%**, and **zero** physical or
intellectual practices. The live learnable list includes rescue, conjuration
magiks, riding techniques, inner force, and swim. Source shows Warrior Inner
Force can lead to Fast Healing (**40%** group prerequisite), which improves
natural HP recovery; Bash is door-only, while Warcry adds hitroll/damroll but
requires at least **16 Intelligence** (Dorrik currently has **12**). Do not
spend or detour with an empty balance. At the next real practice gain, recheck
the current class tree and exact teacher; prioritize useful damage, attacks,
control, protection, and recovery skills by measured combat value, not by a new
learnable label alone. Run **17552** killed the warehouse overseer for **1,707
XP**, ending safely at **1,148,396 XP**, **33,954** from level 38. Run **17553**
confirmed the same target absent without a loss, but the same-level, same-boot
field-city route-attempt marker still includes this policy, so the retry selector
excludes it from the independent reset wait. Preserve that marker; do not retry
or wait on this route until its registered route-clear evidence changes. Run
**17554** returned safely to room **3054** at full health; it added no XP or
practices.

Run **17560** refreshed the level-37 skill listing: enhanced damage **68%**,
second attack **64%**, third attack **63%**, stun **67%**, kick **68%**,
Flamestrike **48%**, and healing magiks **52%**. Physical and intellectual
practice balances were both **zero**; learnable entries included conjuration
magiks, inner force, rescue, riding techniques, and swim at **0%**. No lesson
was actionable, so keep current-band XP progressing and recheck the full class
tree as soon as practices, an unlock, or level changes.

On October 12, run **17571** safely returned Dorrik to healer room **3054** and
logged out without XP change. He remains level **37**, at **1,148,426 XP** with
**33,924 XP** to level 38, **18 QP** and no next-level shortfall, and zero
physical or intellectual practices. Autonomous preflights saved checkpoints
**51616** and **51617**, both before any game connection. Keep the active skill
plan focused: disarm needs Warrior **30%**, grip **85%**, and defense group
**85%**; grip is **99%**, defense knowledge **65%**. Recheck and train the
defense prerequisite as soon as a physical practice is earned, subject to the
live listing and teacher cap.

The adjacent-level unprotected-kill evidence now accepts candidates whose
source route requires a live locator preflight; it does not waive that route
check. Offline validation found two safe level-36 Yeun Sun Ho kills (runs
**17449** and **17452**) with observed target maxima of **782** and **925 HP**,
within Dorrik's current **2,784** source-output envelope. The level-37 Yeun
policy remains explicitly city-blocked, however. The one level-37 city-clear
marker was already consumed for a different Lotus Temple mobile (**10736**),
so do not transfer or retry it; its status is still `attempted`. The Dwarven
Dancer policy retains explicit level-36 and level-37 XP-loss evidence, while
the warehouse policy has extensive same-boot kill history and a retry cooldown.
Do not clear those records or wait for a reboot. Continue source-ranked current-
band selection for another eligible policy; no live hunt has yet passed these
gates since checkpoint **51617**.

### Source-Ranked Random-Exit Relocation

When a fresh positive `where` label has no registered route from the character's
current safe room, one bounded fallback may stitch only edges already present
in that source-ranked locator's safe relocation paths. It applies only to an
exact ordinary wandering target: source-known, unarmed, unprogrammed, without
specials, and outside protected, probe, resource, or crowd exceptions. The
reported label must map to an unsearched room in the same source area and
mobile search graph. Require a current live exit for the first step, the normal
movement capability and route-hazard checks, and cap the stitched route at 24
steps or three times the locator retry limit, whichever is lower. Navigate
inside only those stitched room VNUMs using each room's current GMCP exits;
preserve registered recovery rooms as separate stops. At the destination,
normal live room identity, selector, consider, and combat gates still apply.
This repairs navigation evidence only; it never widens target or attack
permission. If any source, movement, hazard, or live-exit check fails, keep the
existing bounded return behavior.

### Moria Locator Recheck

DD4's `where` command uses normal visibility rules but returns room labels,
not VNUMs. When a source-audited wandering carrier is positively located in a
label that maps to the current source room, and a locator refresh has no
movement path left, the runner may issue one additional `look`. This is a
look-only recheck for the live timing race between locator output and room
arrival; it never selects a target by locator text alone. The ordinary exact
room listing, source identity, consider, crowd, HP, and combat gates still
authorize any attack. Unknown labels, ambiguous source routes, stale absence,
and exhausted rechecks retain the existing bounded return behavior.

The shallow Moria sanctuary carrier has one additional source-configured
endpoint re-scan when room 4064's adjacent scan sees the registered warrior
4051. The runner waits briefly, rechecks the same room, and still recalls if
the hazard remains. This is a navigation timing repair only: it never permits
fighting the warrior, does not count XP, and does not widen the Moria route.

For the deep Moria sanctuary route, the source mapping currently includes
rooms **4063**, **4066**, and **4065** for the repeated `The maze` label. The
reachable path to those rooms must not cross the source-registered poisoner or
sentinel branch (**4057**, **4058**, **4062**) or the aggressive branch at
**4067**. The locator may narrow the existing exact inspection stops to this
set, or use one bounded source relocation; it must not infer a VNUM from the
wire label, search every same-named room, or treat run **13121**'s positive
area sighting as potion-acquisition evidence. A successful live listing,
consider, required-item, and healer-return sequence remains necessary. Policy
revision **283** may reopen one exact same-boot, no-loss level-24 exhaustion
result after a source-mapped locator graph change; it preserves the old attempt
and does not authorize a second unbounded retry.
At room **4064**, a positive `The maze` result may detour to one exact safe
mapped room first, but an empty inspection must return to the still-unvisited
registered stops (including **4020**, **4152**, and the later carrier rooms).
That locator detour cannot replace or complete the rest of the route.

The source-ranked deep sanctuary recovery route is flight-required from level
19, and from level 16 for a mage. DD4 reduces ordinary non-underwater movement
cost to one third while `AFF_FLYING` is active. Select flight through the
existing bounded purchase workflow before dispatch. A missing `affects`
snapshot is unknown: request one live `affects` refresh, then return safely if
`fly` or `levitation` is still unconfirmed. Targetless transit stops do not
require the purple potion before the route reaches an exact carrier inspection;
the required-item objective applies at carrier stops and at run completion.
Offline coverage was added
2026-09-30 but not run because that day's regression batch was already used.
Dorrik's latest checkpoint has an active flight affect, but a deep Moria trip
with flight and sanctuary acquisition remain live-unproved. His original
same-boot general sanctuary recheck is spent; do not repeat its reset wait or
ordinary retry. The one distinct route-suffix correction for safe run **17547** /
segment **17037** was consumed by run **17560** / segment **17050**. The positive
maze locator reached room **4063**, found no carrier, and safely returned after
the original 4020 route (which began at 4012) could not be replayed from 4063.
No further general Moria attempt is authorized on this boot; preserve the
original evidence and spent marker. The general suffix repair now re-roots only
the first unvisited VNUM leg through a bounded source-safe bridge and fresh live
exits, then preserves later stops. It grants no reset wait or combat permission. A
separate, unconsumed automatic-reset capacity entitlement may dispatch only
the exact mobile-4055/object-4050 maintenance probe below. It does not reopen
general sanctuary recovery or authorize XP combat.

Run **18250** / segment **17684** later used the exact room-4064 entitlement and
ended safely at the healer: its sole fixed-room target was absent, with no kill,
XP change, or cumulative-loss change. Because mobile **4055** wanders through
source-mapped Moria rooms, that precise miss permits one locator-only
revalidation while boot, level, source revision, XP, and cumulative losses stay
unchanged. Consume its receipt before dispatch; require a recovered healer,
current flight reserve, the eight-relocation bound, exact source route gates
(4053/4056/4050 in rooms 4058/4057/4062), and all normal live identity, item,
consider, hazard, and return checks. A miss or abort ends Moria retries for this
boot. Run **18252** / segment **17686** consumed this exception, found no potion,
and returned safely to the healer; it recorded 80 incidental XP from one
source-authorized route-gate kill. Do not repeat it. This does not clear a combat
loss, authorize fighting a route-gate mob outside that exact route, or grant
progression-XP permission against the carrier. A source refresh cannot reset
this consumed same-boot, same-level receipt; the exact attempt history remains
closed even when its original route revision is older than the current source.

The 2026-10-09 all-area source inventory found no second executable sanctuary
reserve for Dorrik at level 30. The level-27-to-33 ettin's blood (#17029) is in
a chest behind the keyed west door at room 17220; its key (#17021) is carried
by Redbeard in room 17218, but the 99-command route crosses audited aggressive
and special hazards. The sanctuary scroll (#13345) is nested in chests in the
disconnected Catacombs, while the reachable ground pill (#20645) has minimum
load level 31 and a source hazard on its route. Checkpoint 49500 has no pending
capacity-reset entitlement, and the one post-reset recheck is already marked
attempted. Do not retry Moria or wait again on this evidence alone.

For the exact level-20 generic protection-recovery transition, a source-backed
fallback may use up to eight bounded locator relocations after positive carrier
evidence. It admits only source mobiles **4053**, **4056**, and **4050** in
rooms **4058**, **4057**, and **4062** as below-band required-loot route gates,
with exact live identity and `consider` checks. Any gate kill is incidental and
cannot earn progression XP. This does not widen the deep route, waive special
or unknown hazards, or change the ordinary +6 fame rule; live validation waits
for the next MUD area reset or reboot.

For ordinary unarmed source-ranked targets, a same-room prototype ambiguity may
be resolved only when all reachable source prototypes have identical audited
combat, special, equipment, and reset-object profiles. TARGETMODE's exact live
instance selector is then recorded with the observed alias VNUM. Resource,
special, protected, bystander, and probe stops remain strict prototype-VNUM
matches.

### Equipment Placement Admission

Source gear reports are planning evidence, not permission to walk or fight. A
direct ground reset must carry the shared route audit used for resource stashes,
including closed doors, movement capabilities, aggressive or scripted mobiles,
special procedures, crowds, and destination hazards. `promising` and `caution`
rows still require the campaign's live identity, consider, resource, combat,
and healer-return gates. `reject` rows are blocked. `source-only` rows have no
current executable candidate and must never be dispatched as a fallback. Mob
carried/equipped placements likewise retain their complete hunt candidate
hazards; a shortest source path alone is insufficient. The executable carrier
path requires an exact source mobile, room, and object match, one source spawn
for both mobile and room, a clean bounded route, a fitting live HP budget, and
the normal movement, sanctuary, protection, provision, and funding gates. It
dispatches one bounded kill, then verifies the required object before issuing
the exact loot and equip actions. A successful offline ranking or replay does
not prove that the carrier is live or that the upgrade has been acquired. If a
direct, no-combat ground reset is available, the campaign may select it before
waiting for a sanctuary recovery route or attempting a carrier upgrade. The
sanctuary gate still applies to every placement that requires entering combat.
A ground-reset pickup must wait until the live room equals its registered reset
room. A matching name or description earlier on the route is not proof of the
source prototype: DD4 can place different same-named objects in different rooms,
and live object selectors are not prototype VNUMs.
When a Warrior or Bounty Hunter still lacks its required stun weapon after the
bounded shop-rearm attempt has been spent, a direct ground reset may supply a
source-verified blunt weapon. Keep the best primary wielded and retain the blunt
weapon in inventory for the existing pre-combat stun opener. The item must be a
registered ground reset, and the ordinary live route, exact-room, capacity,
return, and identity checks still apply; this does not admit a carrier fight or
authorize combat on the acquisition route.
If source-gear setup itself fails before a run is created, reopen that exact
object/reset once only from a persisted marker tied to the failed segment,
checkpoint, level, boot, and source revision. Require `run_id` absent, zero
commands, and unchanged character state; consume the marker before dispatch.
Any connected run, command, movement, target sighting, loss, or XP change closes
this setup-only revalidation.
A protection-recovery fallback may retain one independent, source-audited plain
target even when its fresh useful-XP probability is below the ordinary ranking
floor, but its source HP range must satisfy the same audited output-window rule
even when a passive endpoint can reveal live HP before the opener. It must also
pass the live route, movement, consider, and healer-return gates. Same-boot
below-band evidence for that exact source mobile remains a hard exclusion; the
fallback never converts a known low-XP target into progression credit.

### Daycare Ring Recovery

The optional ring objective is source-specific: only the room-6605 old-doll
reset (mobile 6605) equips pink ice ring object 6601. Confirm the exact live
carrier selectors before one bounded attempt: both reset-load dolls must be
present, and the last exact selector identifies the ring-loaded instance. If
fewer than two selectors are present, return without a kill. Verify the ring
before loot or equip commands. A below-band consider is expected for this
required-loot task: it grants no progression XP and must not permanently close this policy.
After a miss or crowd abort, retain a three-segment cooldown across reboot,
decremented only by positive-XP, non-maintenance work at the same level.
Sanctuary,
healing, food, and flight reserve hunts are resource maintenance even when a
required carrier grants incidental XP. Exclude those executions from both
normal countdown and bounded-history reconstruction; do not let supply kills
trigger another optional ring search. Recheck live
route hazards and crowd on retry; the exception never relaxes combat, identity,
health, or healer-return gates.
If this errand was already the eligible policy before current-band fallback,
it may run once that search and the exhausted sanctuary route have no safe
option left, but only from the healer with no active quest and an observed
zero QP shortfall. It remains maintenance, not progression XP.

If a
required-loot expedition withdraws after bounded source-absence sightings, keep
that raw terminal evidence and recover it at startup; apply the registered
current-reboot cooldown before retrying the exact route. The sole revision-279
exception permits the exact Moria sanctuary carrier with global capacity two
only when source proves one reset entry in each of its two audited rooms; it
authorizes one bounded maintenance attempt, never ordinary XP hunting. A fresh
generic capacity entitlement armed by a completed automatic area-reset wait
may reopen that same audited carrier once, even if the general sanctuary
attempt counter is exhausted; it never resets that counter or reopens the
ordinary sanctuary route. The entitlement is source-narrowed to mobile
**4055**, object **4050**, rooms **4064** or **4071**, global capacity two, and
one room entry; it is consumed in the persisted segment start before
connecting. A live absence closes the probe without XP credit and cannot be
replayed in the same boot. The
level-11 Mage frontier then has one distinct continuation: after a zero-XP
Moria result, try the existing one-kill Fleshmonger guard policy once. It
still requires fresh live target identity, consider, route, output, and health
checks; a zero-XP result closes that policy and returns selection to the
source-ranked frontier.
explicit `--retry-stalled` path has a separate, equally narrow Forest
bear-claw exception for a level-10-through-29 thief who still needs the
source-validated piercing upgrade. It can open only from the healer after the
current-band output-fitting frontier is empty, food and water are present, and
the normal route, movement, weight, protection, and live combat gates pass.
Record the boot, level, source revision, and policy before connecting; close
the marker after that one attempt, whether the claws are acquired or not. This
is gear maintenance evidence, not permission to repeat a failed route, ignore
a below-band target, or claim progression XP.

The source-verified Shadow Keep fine-dagger plan is a separate multi-step
Thief route. It is selectable at level 24 or above when the character
needs a strictly better piercing weapon, has the observed currency ledger and
capacity for the source lockpick plus dagger, and has a sanctuary reserve. The
plan buys lockpick object 38 from shopkeeper mobile 3050 in room 3120, trains
the source prerequisite `thief base` to 30% before `pick lock` to 60%, returns
to healer room 3054, and follows the source-replayed route to room 16619. It
uses `pick west`, `open west`, and the exact endpoint chain to room 16635,
where smuggler mobile 16609 is source-reset with equipped dagger object 16614.
The smuggler's `spec_thief` procedure is economic rather than combat-damaging,
but the plan still caps 20%-of-carried-coin exposure at 250 copper and retains
but the plan still uses an explicit level-plus-two ceiling, caps 20%-of-carried-
coin exposure at 250 copper, and retains the sanctuary-backed live HP and
damage-window probe. This +2 allowance is limited to this source-identified
economic-special gear plan; it does not change the ordinary +6 fame rule.
Source cost is a funding
floor, not a promise that a reboot's live shop price is identical; an actual
purchase failure must checkpoint as evidence. Source replay and offline
selection do not prove live purchase, door entry, combat, or loot acquisition.

`show-resource-sources` exposes protection resources and may also expose a
`source_analysis_route` for a source-only placement that is hidden behind a
locked door. Its
`route_key_objects` and `route_key_sources` columns identify the source key
and mobile resets that could satisfy the paper route. This is provenance for
future research only: the route is not executable, and the campaign must not
infer a safe key-acquisition expedition from it. The source mirror preserves
the raw `M`/`G` reset association when auditing a key, so an adjacent reset
for the same mobile and room cannot falsely inherit the key. A live plan still
needs an exact carrier, class-specific HP/output proof, and a bounded item-
confirmed segment before it can be dispatched.

DD4 area `D` records use their second field as a lock type, not as a raw exit
flag bitmask. The source mirror follows `db.c`: type `2` includes
`EX_PICKPROOF`, while `-1` and `0` leave the exit open/default. A source route
through a type-2 door must remain rejected even when the character has positive
`pick lock` practice. The Dwarven Catacombs sanctuary plan now uses the
separately source-proven key 6502 on guard 6500 in rooms 6505 and 6540; its
live maintenance gate still requires exact source identity, isolation,
consider, and corpse-confirmed key extraction before `unlock west`. Each room
has two raw M resets for source mobile 6500 and each reset has a maximum-count
of four. The source route checks 6505, makes one `east east west west` detour
to 6540, and returns to 6505 before unlocking. It still requires passive
source profiles, known selectors, a source-derived joiner defense, and no
extra or unknown mobile. Revisions 313 and 314 reopen their exact same-boot artifacts;
315 recovers the old selector-persistence acquisition, 316 reopens only the
matching reconnect loss, and 317 records the alternate-room route. Revision
318 conservatively required sanctuary because same-prototype guards can join
a fight. DD4 `fight.c` limits assistance to mobiles within three levels below
through six levels above the player, and also prevents good-aligned mobs from
joining a fight against a good-aligned player. Mobile 6500 loads at level 20
with at most two levels of fuzz and has good alignment. The campaign uses
DD4's level and alignment assist checks to choose the needed defense: a guard
that could join requires sanctuary, while a known-good player who prevents the
join must still be confirmed good at the live gate. Missing source identity
fails closed. At level 30 the source level ceiling alone rules out assistance,
so neither sanctuary nor good alignment blocks Dorrik's key route.
Exact live selector, isolation, consider, the 90% route-gate health floor,
corpse-confirmed key extraction, and all other route checks remain mandatory.
The source proof also requires the key on the first same-room guard reset. When
the duplicate guards are otherwise indistinguishable, the route prefers the
lowest runtime target ID first; this is only a search order, never proof that a
guard carries the key. Inventory/corpse confirmation remains authoritative.
This gate grants no progression XP permission. At the exact level-25 frontier, source mobile 2011 is the only admitted transit special: its
level-15 upper bound is exactly ten levels below the player, its
`spec_cast_mage` acts only after combat begins, and its source damage bounds
fit the player ceiling. The live route must confirm that VNUM through GMCP;
the interruption is bounded maintenance combat and never progression XP.

October 12 NZST live run **17571** reached Dwarven Kingdom room **6505** and
used the area-scoped `where dwarf guard`. It listed six guards at **Door to
Kingdom** (room **6509**) and none at the key-route rooms 6505 or 6540. The
source `M 0 6500 6 6509` reset groups equip gear but do not load key 6502; the
key-bearing resets are the separate groups at 6505 and 6540. This snapshot does
not satisfy the route's key-carrier gate, and the level-20 guards at 6509 are
below-band for Dorrik 37. Do not fight them for XP or reopen the failed route
from this evidence. The probe recalled, returned north to healer room 3054, and
logged out cleanly without combat.

If the Dwarven route reaches room 6505 and west remains locked after the
registered open-door recovery, record a same-level, same-boot key-gate failure
and do not dispatch that route again without new evidence. A later live
inventory containing the deep green key reopens the route; a level or reboot
change also invalidates the old blocker. Startup repair may recover this
blocker only from the matching linked, successful, safe segment with the exact
locked-exit evidence and no objective kill.

Revision 340 is a narrow implementation revalidation, not a general retry:
only the exact revision-339 fatal result and its linked successful, safe,
no-objective-kill segment qualify, with unchanged boot, level, source revision,
XP, XP-loss totals, no carried key, and full-health healer start/end checkpoints.
The route must have stopped on the exact closed-then-locked west-door hazards.
The migration preserves the old result and marker, loss quarantines, and
sanctuary/reset counters, while clearing only this route quarantine and old
selector ordering. Consume the one-shot marker before dispatch. A route failure
or interruption after that point does not authorize another attempt; fresh
live identity, room-wide isolation, consider, health, sanctuary, and route
gates remain mandatory.

The same area also resets object **6502** on mobile **6502**, the wraith in
room **6527**. Do not treat this as an independent key source: the source
route to room 6527 crosses the locked west exit from room 6505, which itself
requires object 6502. The Grand Templar carrying sanctuary flask 2008 in room
2025 is behind that same key dependency. This is source-map evidence, not a
live acquisition result; the level-aware guarded key gate remains
authoritative.

TARGETMODE selectors identify live mobile instances, not durable characters.
Keep attempted gate selectors within the connected encounter; campaign history
may retain them for audit but must not seed a later run. DD4's name-only
`Char.Enemies` update must preserve the exact active gate selector only while
that selector remains in the current room listing. If it is absent, fail closed
instead of switching to another same-name mobile.

Revision **282** adds one narrow funding exception for this plan. If a level-24+
Thief still needs the 1,000-copper source lockpick, the selector may choose
only Shargugh (mobile **6115**, room **6100**) and its source-reset iron ring
object **6114**. The route is bounded at 12 commands and 56 movement and must
issue the source `where drunk` preflight; exact mobile, room, object, one-spawn,
HP, output, capacity, inventory, route-hazard, and safe-sale checks remain
mandatory. The ring expedition is a maintenance/funding objective, so its XP
must not enter progression evidence. Source value is only a floor: verify the
actual post-reboot sale price before buying the lockpick, and checkpoint any
purchase failure as live evidence.

If that lockpick marker is active after the exact Shargugh attempt is absent,
the campaign must retain the `provision-funding` handoff while it evaluates
other candidates; a generic exhausted source frontier must not silently replace
an actionable maintenance policy with an unavailable hunt. When a known copper
shortfall is present, rank only candidates that already pass the ordinary
funding gates and prefer audited coin carriers whose contained currency covers
the shortfall. This preference never bypasses route attackers, sanctuary,
movement, output, identity, saleability, or below-band admission rules. An
insufficient carrier can remain a bounded fallback only when no sufficient
source-safe candidate is eligible, and its XP remains maintenance evidence.

When an active food, flight, or lockpick shortfall reaches the selector, an
excluded `empty-money-container`, `sell-loot`, or other city-maintenance result
must not erase it by becoming a generic unavailable source frontier. The
campaign may preserve `provision-funding` only from a fed, alive, non-combat
checkpoint; candidate selection still runs before connection and retains all
source identity, route, movement, protection, output, saleability, and
below-band rules. If no eligible carrier exists, checkpoint the bounded
unavailable result and wait for new source or reboot evidence rather than
repeating the connection.

If a current-reboot flight-funding attempt has just reported its target absent,
the character is at the healer, is fed and healthy, protection recovery is
required, and the sanctuary recovery budget is terminal for that reboot, rotate
to the existing source-output-gated ordinary current-band selector instead of
reopening the empty target or an older reusable funding carrier. This is a
single bounded frontier decision: sanctuary-required, route-hazard, output,
consider, and live-identity gates remain authoritative. If no ordinary target
passes them, checkpoint without opening gameplay; do not convert a below-band
funding kill into progression XP.

When no source-safe funding carrier remains and the exact same-boot ground
probe (including its one pending expanded locator search) is recorded absent,
the campaign may use the existing three-attempt current-band XP budget to
select another no-flight ground target. A pending exact locator retry takes
priority; each alternate still passes the ordinary level, output, protection,
route, consider, and live-identity gates. Persist and spend the budget per
segment, then return to funding selection. Do not repeat the absent target or
wait for a reboot while another eligible ground target remains.

Revision **322** adds the preceding bounded branch for the nonterminal case:
when a current-boot flight-funding carrier is absent and protection recovery
still has a remaining sanctuary attempt, select one source-validated sanctuary
carrier before reopening the empty funding route. The branch requires the
healer checkpoint, food, no combat, no sanctuary reserve, and the ordinary
source, movement, capacity, and unarmed-carrier gates. If the source selector
finds no safe carrier, keep the funding marker and use the existing finite
reset-wait path; do not manufacture a route or grant XP permission.

Reset repair must not erase that absent-target evidence before the next policy
selection. For the exact protection-starved, sanctuary-exhausted flight
funding state, retain the current-boot absent marker while clearing the
transient attempt list. This prevents the same empty carrier from being
reopened immediately after an area-reset wait; it does not authorize a
different carrier or bypass the ordinary source-ranked output, route,
movement, consider, and identity gates. Other funding states keep the normal
reset behavior and may become selectable again only through their recorded
reset evidence.

If the active lockpick marker remains below its recorded source cost while a
pending flight retry causes the generic policy layer to select `buy-flight` or
`buy-optional-flight`, preserve `provision-funding` before entering fame or
generic source fallback. This is a priority rule only: the character must still
be fed, alive, out of combat, and at the healer checkpoint, and the existing
funding selector must reapply every source identity, route, movement,
protection, output, saleability, and below-band gate. Do not claim progress from
the resulting funding kill; if no eligible carrier remains, checkpoint the
bounded maintenance boundary instead of retrying the refused service.

The starter runner must set `emergency_provision_sale` from the observed food
ledger, not from the existence of a stale funding marker alone. A fed checkpoint
must not enter `needs_food` or create a resupply detour; a foodless funding
marker still preserves emergency sale mode until provisions are obtained.

When a source-verified sanctuary potion is loose in inventory and a current
protection marker is active, select `audit-combat-pouch` before money-container
cleanup or field funding. Require the live pouch placement acknowledgement and
verify the worn-pouch ledger before reopening combat. Loose inventory evidence
may explain the reserve, but it does not substitute for a verified pouch
reserve at a field-fight admission gate.

When an exact source hunt stop completes below the useful-XP band, retain its
source mobile VNUM and source policy ID in the kill evidence even though
`objective_eligible` is false. Provenance makes maintenance evidence auditable;
it does not authorize another low-value fight, reopen a closed route, or promote
the XP to progression. Unknown or intercepted below-band kills keep their
existing incidental-evidence rules.

### Target-Specific Combat Output Revalidation

When a same-level source-ranked target produces one exact live HP-budget loss,
persist the target name, mobile VNUM, endpoint room, reboot, source revision,
observed GMCP maximum HP, prior audited output ceiling, and primary weapon.
Only a strictly stronger audited output that covers that exact observed HP may
reopen the same plain, autonomous-safe, current-band target. The ordinary
route, movement, funding, protection, and live identity gates still apply;
special, armed, scripted, equipped, hard-hazard, coin, and food targets remain
closed. Consume a dedicated marker at source-hunt segment start, after all
preparation has selected the target. An interrupted or failed retry is closed
for the current reboot and level, and source revision synchronization clears
the evidence. This contract is a bounded live measurement, not permission for
general target expansion or an unlimited fight.

### Route-Only Loss Revalidation

An exact same-level, same-reboot source-ranked loss may be reopened once when
the saved segment proves the loss occurred before target combat: the target was
not present, no consider or objective-kill evidence exists, the character ended
at least 90% healed, and the sole route hazard is a source-labelled below-band
transit interruption. The exact policy and source revision must match a fresh
current-band candidate that remains autonomous-safe and passes the ordinary
source, identity, HP, output, movement, route-program, and crowd gates.

Repair legacy segment evidence before arming the marker. Persist the marker and
consume it at segment start, after preparation has selected the target. A
productive target result clears the route-only marker and its exact loss record;
another failed or interrupted attempt closes the marker for that boot and
level. Never use this exception for a combat loss, absent-target search, hard
route hazard, below-band progression, or a generic retry loop.

### City-Greeter Route Revalidation

The level-25 Solace Secretary fallback may receive one fresh city-route check
only when its recorded prior segment ended at healer room 3054 at full health,
with unchanged XP, no combat or kills, and the exact source-registered Drunk
preflight at Temple Square. Match the same source mobile, reset room, boot, and
level; retain the ordinary no-sanctuary output and route gates. From recall,
issue a fresh `where drunk` and reject any selected route that crosses a
reported location. Consume the marker at dispatch. This reopens navigation
only: live identity, consider, and damage gates still control combat, and any
combat loss closes the policy for that boot.

## Capacity And Worker Recovery

Reconstruct pending capacity-container metadata chronologically from successful
or ready segment end states. A later explicit vault claim must suppress stale
legacy restore evidence, while a carried sack, backpack, or girdle is removed
from the pending list. If a live claim is rejected for weight, allow one
healer-side equipment-relief pass and one retry; retain the normal recovery,
funding, and bounded-retry gates.

When a bounded worker is interrupted, preserve its evidence and let the next
startup recover the prior run before opening new live work. Stop only the
abandoned DD4 worker or diagnostic process after its deadline; leave the healthy
Discord streamer and unrelated services untouched.
On the shared multi-character database, use the indexed scoped recovery command
(`recover-runs --campaign-id ID --character NAME`) after verifying the worker is
gone; the global no-argument recovery scan is reserved for small databases.

## Healer-Side Deity Prayer

DD4's `deity.c` allows `pray protection` only when the level-15-or-higher
character's patron offers it; peaceful and lawful patrons include that prayer,
but the patron's stature determines which effects it grants. Never infer
sanctuary from the command or patron name. When a selected current-band hunt
needs sanctuary and no durable reserve exists, the campaign may try one prayer
from healer room 3054 per DD4 boot. Require a live, safe, provisioned healer
checkpoint; wake at most once, issue exactly one `pray protection`, then save
and quit. Consume the marker before dispatch. A recorded command spends the
attempt even if the patron refuses or the favor/timer prevents a grant; a
bounded pre-login failure with no prayer command does not. Only a fresh
sanctuary affect in the saved GMCP state can help selection, and every ordinary
route, identity, consider, output, and survival gate still applies. Live
success remains unproved until the affect is observed after the prayer.

If the ordinary source selector rejects a current-band target solely because
the missing reserve blocks its output admission, it may expose that exact
source-ranked candidate only to choose the healer prayer policy. The candidate
is removed before dispatch; this exception authorizes no route or combat. After
the prayer, selection starts fresh and every ordinary source and live gate is
applied again.

If the MUD reports that the character has no patron, the command still spends
the boot's one-shot attempt. Do not automatically follow it with `pray
patronage`: DD4 warns that patronage may be difficult to leave, requires
multiple confirmations, and may not grant the required protection. First
verify the exact patron's prayer list and character-specific favour from
source/live evidence. Dorrik's October 9 attempt (run 16571) returned “You have
no patron,” granted no Sanctuary, and left him safely at healer room 3054.

## Mirror Realm Route Recheck

Run **17554** reached Mirror Realm room **19056**, Foot of the Rock Ladder. The
live exits were a closed west door and up, but the registered Jerry Garcia
route issued another `down`, received `Alas, you cannot go that way.`, and
recalled without combat. The first route correction was short by one descent:
run **17555** reached room **19044**, Below the Watchtower, then tried west
although its exits were up and down. The source graph and run 17554's room
sequence show the path needs two downs after entering the watchtower, reaching
room **19045** before opening west. Preserve both failed segments and use the
distinct `mirror-realm-jerry-garcia-route-recheck-v2-36-40` policy for one
final no-combat route check. Run **17565** consumed that policy but did not
leave healer room **3054**: its three bounded `where drunk` checks ended with
the field-city preflight blocked, without movement, XP change, or loss. Run
**17566** was a separate eight-command world-time/locator check at the healer;
it observed three city locations instead of none. Both runs used source
revision `2533108641f46f7a6998d3ac4ec54c0f47194e8d`, while the current parsed
source is `9205f31648e713953edb77f844325fa47b6fd9bf`. The level-37 city-clear
revalidation was already consumed for the exact Lotus Temple policy
`source-ranked-hunt-lotus-temple-10736-10837-37`; do not transfer it to Mirror
Realm. These records do not prove the Mirror route clear or authorize a route
or combat retry. Any distinct source-refresh revalidation must satisfy its
exact registered policy and all ordinary live gates.

Source audit correction: Mirror Realm mobile **19004** is Caerlin, level **35**.
His reset in room **19068** equips the **Staff of the Bard** (**19173**) in
the hold slot and also loads a silver harp (**19011**); object 19173 is a
10-charge staff whose source spell is `sanctuary`. This makes Caerlin a valid
Sanctuary-resource target, not a safe or plain XP target. His
`spec_cast_cleric` special only selects someone already fighting him, then
casts offensive spells including blindness, curse, flamestrike, harm, and
dispel evil. Require exact live identity and consider, a source-bounded combat
plan, and verified acquisition/brandish before counting Sanctuary as a reserve.
Do not confuse it with the separate Royal Staff (**19010**) equipped by the
withered knight (**19012**) in room **19043**; that staff casts `heal`.

Run **18010** followed the official recall route through room **19008** and
received two live `where Caerlin` replies naming “Beside the Watchtowers”; the
mobile had moved before the later room inspections. The reset-room endpoint
**19068** has no source-safe reverse route to **19008**, so the generic local
locator cannot recover that sighting. The bounded recall-origin prefix
`mirror realm caerlin watchtowers` ends at **19008** and is for exact live
consideration only. It does not lower Caerlin's special, output, isolation,
recovery, or combat gates.

The current carrier executor starts at the exact reset room with a live `where
caerlin` locator. If Caerlin wanders into an already-checked room or outside the
audited relocation graph, one safe, no-loss retry may be consumed after the
positive locator evidence is checkpointed. A second miss closes this recovery
attempt until the normal source/reboot evidence changes; it never authorizes a
generic chase or combat outside the registered route.

Run **18490** added a distinct live observation: Caerlin was visible in room
**19002**, “The Path,” while Dorrik was still following the official outbound
route to room 19068. The generic locator must continue to reject that ambiguous
label, but the exact source VNUM and route prove this one waypoint. The carrier
stop now permits one outbound interception at VNUM 19002 only; it still requires
the live source identity, isolation, consider, output, required staff receipt,
and healer-return checks. The current boot's retry is already closed, so this
evidence will be used on the next eligible recovery attempt rather than looped.

The next source-ranked Sanctuary fallback is recorded as
`source-ranked-sanctuary-alternate-2-100`. Its first eligible carrier is the
level-39 Alchemist (mobile **916**, room **927**), whose source reset can load
the ivory staff (**905**) and nectar (**926**) and has no listed special. The
selector binds the effect, reset, route, isolation, and output evidence rather
than assuming a mobile name. The ordinary Alchemist hunt already recorded an
absence on the current boot, so this fallback remains closed until a reboot or
source revision changes that evidence; it is required-loot maintenance, not XP
permission. A legacy absence without a complete boot boundary is also kept
closed, because it cannot prove either current-reboot absence or post-reboot
availability.

October 13 NZST run **17722** reached Jerry Garcia's registered endpoint and
refreshed `where` once; the live result located him only at “Below the
Watchtower.” The current source map identifies that label as room **19044**,
but it is outside the route's registered source-safe relocation graph. The
probe returned to healer room **3054** and logged out safely without combat or
XP. Preserve the locator evidence, but do not follow or fight there until an
audited safe approach is registered.

Dorrik's level-37 skill audit is historical; the current level-38 proficiency,
practice, and trainer audit is recorded above. Keep the same Warrior/Knight
source priorities, but re-evaluate their useful targets and actual lesson access
against the current live balance and exact teacher before travelling. Recheck
on the next level, practice gain, new unlock, or relevant source change; do not
repeat an unchanged trainer visit.
At a fresh trainer listing, compare the current proficiency, useful target,
remaining practice balance, teacher cap, and level-up HP/mana value. Refresh the
listing after an accepted lesson and continue high-value training when another
source-supported gain is worthwhile; do not mistake an initial unlock for a
finished skill. Preserve practices when no useful teacher-supported lesson
remains.

## Documentation

`README.md` is current usage; `ROADMAP.md` is delivery gates. Dated reviews hold
analysis and run evidence. `docs/history/` preserves prior documents without
making their old "latest" sections authoritative. Update current facts once
in the active review rather than copying every run into all three root files.

## Level-Based Engagement (October 15)

Choose mobs by relative level and live `consider`. Target hitpoints are
diagnostic evidence, including the health comparison in `consider`; they do
not veto a target, require sanctuary or HP gear, or trigger an escape based on
predicted damage or kill duration. The character's own health and actual
encounter hazards still govern withdrawal. Preserve exact previous loss
records; changing this strategy does not automatically retry failed targets.
