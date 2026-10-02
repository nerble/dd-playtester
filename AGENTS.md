# Repository Guidelines

## Objective And Evidence

Build for every source-legal race, cosmetic
sex, base class, optional subclass, name, and personality, capable of creating
or resuming characters to HERO 100. HERO remains unproved. Follow
`docs/APPROACH_REVIEW_2026-09-08.md` and `ROADMAP.md`: fix roster-level
blockers, measure whole-session net XP, and avoid higher bands.
Until one character reaches HERO 100, keep one existing primary pilot in
progression focus and stay with him through each verified level and band
transition. Do not create characters, rotate the roster, or run matrix breadth.
If he reaches a durable blocker, focus source research and implementation on
clearing his current-band gates; do not switch characters unless the user
explicitly redirects the pilot. Resume breadth only after the first HERO100.
Keep pursuing the best executable current-band XP whether or not the MUD has
rebooted recently. Reboots may improve particular XP or loot opportunities, but
never pause progression; wait for a reset only when the selected objective
actually depends on one, and otherwise move to the next eligible policy.
For ordinary source-ranked XP hunts against wanderers, keep blind room checks
to the eight nearest safe rooms. Preserve the full source map for hazard checks
and follow a positive live `where` result to any exact safe room outside that
short search. Keep named research and resource routes on their own bounds.
If a same-level, same-boot source-ranked wanderer hunt ends at the healer after
a positive `where` result exhausts its registered relocation graph, a corrected
direct rebase may receive one persisted route-only revalidation. Preserve the
old locator evidence, consume the marker before dispatch, and require the new
source route plus fresh live identity, isolated targeting, and consider checks;
this never grants combat permission or repeats after another miss.
Ordinary productive wanderer hunts may refresh `where` after a kill within the
original kill, source-capacity, and locator limits. Follow the exact eligibility
contract in `docs/OPERATIONS.md`; require fresh isolated targeting and consider,
and never extend protected probes or resource work into multi-kill permission.
Locator refreshes must preserve registered recovery endpoints on the selected
path. Reuse only their exact targetless transit stops, require the existing
live safety checks, and never infer a new place to sleep from a room label.
An optional crowded outbound interception must not consume the earlier,
unvisited destination merely because the intercepted stop is last in the circuit.
Restore the saved stop and finish the approved outbound route; never clear a
hard abort, retry the crowd, or treat navigation permission as combat permission.
Source `R` resets require bounded live-exit navigation through the audited room
graph. A registered fixed approach must end before its shuffled section, and
target absence is meaningful only at an actually reached registered endpoint.
When a registered progression route is unavailable at the current level, allow
the bounded source-ranked fallback from level 1, including its distinct
level-1-to-5 policy. This opens candidate selection only: exact target, route,
live consider, useful-XP, health/output, and finite-action gates still apply.
An arena route stays in control unless same-level, same-boot below-band
evidence closes its target set; then the campaign may try the independent
source-ranked fallback instead of replaying that arena or waiting for a reboot.
Names and credentials identify history, never behavior. Distinguish source
estimates, offline replays, live observations, and sustained progression.
For plain, single-target source hunts, time pre-level equipment against the
source-backed one-kill planning window, retaining the existing ten-percent
window when reward, equipment, group, or source details are uncertain. Include
damage XP, regeneration, and the best ordinary reward roll; keep the window
monotonic within the encounter. This changes gear timing only, never combat
permission or stat-training priorities. Recovery gear retains precedence.

## Structure

`dd4tester/` contains transport, observation/state, deterministic decisions,
campaign orchestration, storage, and CLI modules. Reuse behavior
modules; keep configuration in YAML. Tests and sanitized
protocol fixtures live in `tests/`. SQLite, transcripts, and HERO
workspaces belong in ignored `runs/`, `transcripts/`, and `runs/heroes/`.

## Development Commands

Use Python 3.12 from `.venv`. From the repository root:

```powershell
python -m pip install -e .[dev]
python -m pytest -q
python -m compileall -q dd4tester tests
python -m dd4tester run scenarios/login.yaml
```

These install dependencies, run offline tests, check compilation, and execute
a scenario. Follow `README.md` for bounded live runs and inspection commands.

## Style And Tests

Use four-space indentation, type hints, `snake_case`, and `PascalCase` classes.
Prefer structured parsers and helpers. Keep changes scoped; preserve
unrelated worktree changes. Name pytest cases `test_<behavior>` in
`test_<module>.py`. Reproduce live failures with sanitized, timed event replays,
including negative and survival cases. Build a meaningful, coherent
implementation slice before stopping for regression work. Run at most one
regression-test batch per local calendar day (Pacific/Auckland): choose focused
tests for routine changes, or use the full suite instead at a coherent milestone
or release checkpoint. Do not run both on the same day. Fix issues that block
the next step; record unrelated failures and keep moving until they become
relevant.

## Runtime Contracts

Read `docs/OPERATIONS.md` before live work or user commentary. Source-audited
command timing must distinguish actual lag from an already-fighting `kill`
refusal: DD4's exact `You do the best you can!` reply returns before `WAIT_STATE`.
Do not add a new round delay for it or relax any action or survival limits.
Source-audited
capability registration plus positive practice and action-specific gates are
required for dispatch; observed skill names alone authorize nothing. Preserve
loss evidence, exact live targeting, bounded retries, and healer recovery. Use
`hero --autonomous` for multi-segment progression; it keeps each worker
bounded and stops after its finite reset-wait budget or a durable blocker. For
an accepted connection that sends no login prompt, use the five-second
pre-login timeout and its bounded retry, then checkpoint transport
unavailability; do not convert silence into route evidence or a reboot wait.
The in-game inactivity timeout remains separate. If this happens during the
one-shot sanctuary area-reset recheck and zero game commands were issued, leave
that recheck pending for a later explicit invocation; do not spend it, wait
again, or retry automatically in the same invocation. Once game commands have
started, the normal one-shot boundary applies.
DD4's summoned familiar is an uncharmed follower at runtime: `db.c` strips
`AFF_CHARM` from mobile prototypes, and `spell_summon_familiar` only adds a
follower. Use `order <selector> flee Fear` and require the exact companion
`has fled!` message before the player's opener; `Ok.` alone is not withdrawal.
Do not follow it with a sleep order after it leaves. Allow five seconds for
confirmation; if it fails, abort the hunt and make one direct recall attempt
when legal. Never resume combat on an unconfirmed withdrawal. Require in-place
sleep only for a separately verified charmed companion that remains in-room.
Before ordering a familiar to attack, audit every open exit it could randomly
choose when fleeing. Each destination must admit NPCs and have no source-known
aggressor, combat program, unsafe special, or mobile that can join the fight;
one safe exit does not make the others safe. Skip an optional familiar opener
only when the registered stop already proves solo output is sufficient;
otherwise reject the stop before ordering the familiar. If withdrawal fails in
combat, make one direct recall attempt when legal. If a flee is unavoidable,
issue it once; after it succeeds, continue the bounded return instead of
repeating flee because an enemy snapshot is stale or a pursuer remains.
If a field-city preflight has already stopped at the healer for the same level
and reboot, select the recorded unavailable cooldown for that exact policy.
Allow another source-ranked policy to perform its own bounded route preflight;
legacy checkpoints without a policy ID remain conservative until fresh
`time`/route evidence changes that state.
When a source-validated city detour replaces a route prefix, shift later live-
maze start and resume indexes by the exact command-count change; the maze
handoff must remain aligned with its registered entry room.
An unsafe or unavailable detour calculation for one fresh wandering-greeter
report does not consume the detour. Re-evaluate each fresh report within the
existing three healer waits. Apply at most one healer-side detour; if a fresh
room-3001 locator reports a changed location set on its Midgaard prefix, allow
one separately bounded corrective detour. Keep both evidence sets, repeat the
hazard check, and reject any obstruction after that correction.
When no other current-band source candidate is executable, one exact saved
source-ranked policy may be reopened once if its completed no-travel segment
records that first detour, a changed fresh locator set, unchanged level, boot,
source revision, XP, and movement, and no loss or attempted correction. Consume
the marker before dispatch, reconstruct and match the prior detour from the
current source map, then run a fresh live locator. This is not a route-wide
cooldown reset; a mismatch, new hazard, or second attempt stays closed.
Keep long-route revalidation separate: only after ordinary current-band
selection finds nothing executable may one exact policy be reopened from a
same-level/boot/source-revision no-travel segment blocked at outbound index 0
after its three waits, with unchanged XP/loss totals and no kills. Require a
later complete, unblocked locator with changed locations, proven by a bounded
successful segment whose start/end locator sets differ and whose level, boot,
source revision, XP, loss, and kill evidence remain unchanged. The locator's
run ID must match its segment row; legacy records without that ID need changed
start/end location sets. Map every old label to Midgaard rooms,
prove the original shortest route crosses one, and allow only a source route
avoiding them that adds at most 22 commands. Preserve the old blocked-policy
ledger, persist and consume a separate one-use marker before dispatch, then run
a fresh locator and all ordinary route, movement, health, output, protection,
consider, and combat checks. Any mismatch, new obstruction, or failed attempt
closes it; it grants no cooldown bypass or combat permission.
If a source refresh intervenes, allow one distinct refresh revalidation only
when the earlier blocked segment and later changed, unblocked locator were
both recorded under the same prior revision, and the current-source candidate
still has the exact policy, mobile VNUM, room, and route. If the blocked
segment fell outside the normal eight-row tail, fetch only that policy's
latest segment with the bounded 256-row lookup; never expand checkpoint
history. The fresh live locator and every ordinary gate still apply.
A city-blocked policy must not short-circuit offline source selection: keep
that exact policy excluded unless its one-use marker is pending, but allow
other current-band candidates to pass their normal source and route gates.
One saved source-ranked result may be reopened once when it records the exact
pre-combat live-maze index mismatch, the encountered room lies on that
candidate's source route before its registered maze entry, and the reported
maze destination matches the current source route. Require unchanged boot and
level, no target/consider/kill or XP-loss evidence, and no crowd or cooldown.
Persist and consume this exact marker before dispatch; any other route failure
or a second attempt stays closed.
When a healthy character is already at healer room 3054 and the selected
frontier is unavailable, allow exactly one automatic maintenance-only
`world-time-probe`. It may issue `time`, save, and quit, but it cannot hunt,
clear reboot-scoped cooldowns, or claim XP. Persist its checkpoint phase so a
same-frontier failure or same-boot result is not reconnected blindly; only the
existing reset-aware wait may authorize another probe.
At a safe healer checkpoint, if health, movement, or mana is below the campaign
readiness threshold and food is available, use the bounded healer recovery
policy before declaring the frontier unavailable. Re-select the source route
after waking; low movement alone is not evidence that every route is closed.
If the latest checkpoint has an observed, same-level, same-boot training audit,
reuse its live skill listing instead of scanning thousands of historical event
rows. Only legacy checkpoints without that audit should use historical skill
backfill, and public preparation stages must remain visible and bounded.
Before leaving the healer for a distant class trainer above level 10, use the
fresh observed listing and practice balances, complete live stats, and exact
registered source teacher to predict whether any eligible automated priority
can gain a percent. Skip the trip only when this complete source calculation
proves there is no lesson; missing or uncertain evidence keeps the existing
route. Required practices and separately gated maintenance journeys retain
their own admission rules.
At a source-validated local fallback teacher, refresh the live practice listing
after each accepted lesson and allow at most three accepted lessons per visit.
An additional fallback lesson must be a distinct registered priority with positive
source-predicted gain and a live practice balance. An explicitly learnable
zero-percent skill is eligible; an inferred or merely historical name is not.
Legacy single-lesson visits may reopen once only for such an unlearned skill
at the same teacher, level, and reboot. Persist consumption before dispatch
and preserve all combat losses and route gates.
A local teacher visit blocked before any lesson may receive one same-level,
same-boot route recheck after a later productive source hunt. Require actual
run-local preflight evidence that every reported wandering hazard location is
source-known and outside the entire teacher path, a recovered healer checkpoint,
and still-useful lessons at that exact registered teacher. Persist
`local_teacher_fallback.route_clear_recheck` and consume it before dispatch.
Alternatively, a later successful automatic `world-time-probe` that actually
issued `time` and observed the same reboot can arm that same single recheck
when its start is at least five minutes after the blocked visit ended. This
authorizes only a fresh trainer preflight, not crossing the old hazard or
clearing combat failures. Both paths share one retry marker. If the blocked
visit is outside the normal eight-row history tail, read one matching segment
through the bounded 256-row metadata lookup; never expand all checkpoint JSON.
Recheck the live route normally; inherited sightings, an attempted lesson,
another failure, or a reconnect cannot reopen it.
Use `docs/history/AGENTS_2026-09-08.md` for gameplay contracts; search
the affected topic before changing its behavior. Preserve distinct labels,
nested closed exits, and synchronized observed and verified resource ledgers.
Below-band targets are allowed only for an exact source-required resource or
loot objective with positive carrier evidence and a bounded safe route; never
count them as progression XP. For XP policies, a below-band live check closes
only that exact reset for the current level and reboot. A different reset room
for the same mobile may get a fresh live `where` and `consider`; neither its
source estimate nor another room's result authorizes combat. A visibility-dependent route requires positive practiced
authorization plus a fresh affect; it cannot bypass detecting, scripted, or
unknown mobiles. Combat-only specials follow source aggression cutoffs during
transit; pre-combat, scripted, equipped, unknown, and engaged hazards remain
blocked. A source `ACT_FEAR_AURA` target is also a combat hazard: DD4 can make
a visible player flee before the first attack, even though it is not a special
procedure. Before routing to an aggressive XP endpoint, require its minimum
source-fuzzed level to be strictly greater than `character_level - 5`; equality
can roll at the below-useful-XP floor and force an XP-losing flee before
`consider`. A same-room crowd of source-known below-band transit mobiles is
also a pre-combat hard rejection; only one isolated, source-validated bounded
interrupter may enter the existing finite transit-fight path. A source HP range
that crosses the character ceiling may use one bounded GMCP
damage-window probe only when its lower bound and uncertainty gap fit the
audited player output
and the exact route preflight is source-validated. A plain, unarmed
current-band target may instead use one unprotected probe when the same
HP/output gates pass and any transit program is one exact, source-locatable
low-level mobile checked with `where`; a nominally same-level target may retain
one additional level of source load-time fuzz only when the audited range also
reaches character level minus two, and its maximum remains within character
level plus two. Unknown, armed, special, and unresolved
transit hazards remain blocked. The live target ceiling must still fit the
fixed ordinary action budget before the fight continues. A plain unprotected
probe may finish a live target that falls just short of the warning fraction
only when its remaining HP and projected incoming damage fit that same bounded
budget and health reserve; this ends the probe and never opens a general retry.
The source-vetted protection-recovery fallback may open once without a large
consider health lead only against an exact fixed, passive, unarmed endpoint
with no source program or special, and only when its full source HP ceiling
fits the audited output budget; live damage evidence still decides whether to
continue.
The exact
source-famous `spec_breath_gas` contract may use the existing finite 36-action
probe only after sanctuary and healer nausea recovery are observed; this never
extends pre-sanctuary admission or creates an unbounded fight. Protection-
recovery fallback cannot bypass that output gate in a live source-backed state
with a known character class; source-less fixtures are not live authorization.
AI personality generation does not authorize AI gameplay.
Provision-funding may use one exact source-audited dynamic saleable drop
behind practiced route invisibility only when the endpoint is unarmed, its
specials are in the source noncombat allowlist, every transit aggressor is
source-known and invisibility-blocked, and the ordinary current-band,
movement, HP/protection, saleability, and live identity gates pass. Carry the
route mobile VNUMs into `Fastwalk`, record the segment as `funding_only`, and
exclude its XP from progression. Armed ambush targets, scripted or unknown
transit hazards, rejected endpoints such as the live-quarantined Foundry
Uburz, and repeat attempts remain closed.
If a same-boot hard-health marker records a no-loss withdrawal and the exact
source target now passes the strict familiar probe, a learned familiar may arm
one exact revalidation. Consume it at source-hunt dispatch and close it after
the segment; it never bypasses fame, target identity, route, output, or live
consider gates and never becomes an ordinary retry loop.
A Mage with a practiced familiar and fresh source-backed invisibility may use
one additional bounded probe when the route aggressors are all proven blocked
by invisibility. The endpoint must still be no more than five source levels
below the player, stationary, non-aggressive, unscripted, single-weapon at
most, and have a source-audited staging room. This fallback replaces the
ordinary sanctuary requirement only for that exact probe; it never makes a
lower-band target progression XP or bypasses target, output, or live-consider
gates. Reject familiar destinations marked private when a source mobile reset
occupies the room: DD4's follower entry check would leave the pony behind.
A source-audited greet-program attacker at least five levels below the player is
never a transit XP target. XP routes must run its registered `where` preflight
before crossing the route and leave if it is present; only an exact, source-required
resource or loot route may retain its separately audited bounded exception.
The source estimator must mirror DD4's current level/rank roll, inherited or
individual `MobHPMod` scalar, and inherited or individual `MobDamMod` scalar
before any combat, transit, or city gate. Apply `MobDamMod` per positive NPC
attack before sanctuary or critical-hit arithmetic; missing or unparsed source
modifiers must fail closed rather than lower a target estimate.
A post-loss plain-target probe may use the same lower-bound and uncertainty-gap
output test as the protection-recovery fallback, but only with a plain,
unarmed, source-locatable route and the tighter incoming-damage limits recorded
in `docs/OPERATIONS.md`; live GMCP HP and damage remain decisive. A route
special is permitted only when source verifies it as noncombat and its mobile
has no program or reset-loaded gear. Unknown or combat-capable specials remain
blocked; the exact low-level greet-program exception still requires its own
registered `where` preflight.
Area-section parsing must use DD4's actual `boot_db` header vocabulary, not
arbitrary hash-prefixed lines: ASCII maps occur inside tilde descriptions.
Restoring missing rooms also restores their hazards; it grants no route,
cooldown, or combat exception.
When the source mirror changes, rerun parser smoke checks before updating
revision markers. Current DD4 resolves three weighted mobile-special slots,
body/archetype inheritance, area `#SPECIALS` `M`/`N`/`P` overrides, and the
explicit `AFF_MINDLESS` trait. An unparsed special must remain a rejection,
not an empty slot that authorizes a route.
When multiple source prototypes can reach the same room under one ordinary
target name, a live TARGETMODE selector may stand in for the missing
prototype VNUM only when every reachable prototype has the same audited
profile, is unarmed, has no special or loot contract, and the stop is not a
probe, protected, bystander, or resource action. Record the actual live VNUM
as alias evidence; any material difference remains a hard ambiguity.
Before that equivalent-alias fallback, an exact source command keyword may
resolve the expected prototype only when it is present on that prototype and
absent from every other source prototype reachable in the exact room. Repair
legacy candidate records from the current source keywords; a shared generic
keyword such as `citizen` remains ambiguous.
When a current-boot flight-funding carrier is absent while protection recovery
still has a nonterminal sanctuary attempt, select exactly one source-validated
sanctuary acquisition before reopening that empty funding route. If no safe
sanctuary carrier exists, preserve the funding marker and wait through the
normal bounded reset path; never turn this handoff into an unbounded retry or
ordinary progression permission.
For object quests, preserve GMCP's raw `retrieve` type: it covers both loose
tokens and buried hoards. Only a dispatched request may bind the exact hoard
narrative to the live giver/room/object identity, within five seconds and 4,096
characters. Clear that annotation on reconnect, a new request, inactive status,
or changed identity. Do not infer burial from a token name. Known hoards require
a trap-aware executor; the former fixed twelve-dig loop is not authorized.
Continue ordinary eligible quests and XP hunts while that capability is pending.

For the bounded trainer-potion journey, one source keyword may replace a zero
instance ID when the complete fresh text/GMCP inventories agree in item counts,
every carried description maps to source, and no possible other carried
prototype matches that prefix. Require a single source-unique target description;
unknown items and aliases with conflicting keywords remain rejections. `quaff`
does not support multiword keyword matching. Setup revision 3 grants one repair
only to revision 2's matching, unselected, unconsumed, route-index-zero failure,
with the same item/teacher and a currently provable carried keyword. Consume it
before dispatch; all training and travel gates still apply.
Retain the trainer journey result across checkpoints. A missing legacy result
may be restored only from one completed, exactly matching healer segment found
through the bounded 256-row lookup. Never replace an explicit later result or
infer permission from the restoration alone.
Exclude only DD4's exact terminal `You are carrying N/M items.` footer from
inventory items. Revision 4 may repair the same revision-3 setup failure only
after its bounded 64-event run tail proves a requested, otherwise matching
inventory with that footer and no quaff. Preserve the old result and its run ID
as `inventory_footer_repair`; consume revision 4 before dispatch and require
fresh complete inventories, current source keywords, and all ordinary gates.

GMCP `Char.Worth.alignment` is authoritative wire data: DD4 sends 50000 below
level 10 and the actual server-clamped -1000..1000 value at level 10 and above.
Never treat the sentinel as good alignment. A revealed value at or above 300
is necessary for the `spec_guard` special's own assistance path, while
`violence_update` separately suppresses a good bystander only when both that
mobile and the player meet DD4's exact 350 `IS_GOOD` threshold. Use the
player's alignment for player fights; a target NPC's alignment is not a proxy.
A source-ranked target carrying exactly `spec_guard` is a narrow exception to
the blanket target-special rejection only when the target and the revealed
player both meet that 350 threshold; its source headbutt/smash/kick peak must
fit the ordinary damage budget. Unknown player alignment, mixed target
specials, and every other target special remain rejected.
Treat a bystander carrying `spec_guard` separately: its own special attacks a
player who is fighting any NPC with alignment below 300, even when the player
is good. Do not apply the ordinary good-versus-good bystander shortcut to that
case; neutral targets below 300 trigger it too.
For fame recovery, an ordinary kill target must be at least six levels above
the player (`victim.level - player.level > 5`); a source-famous target is a
separate exception and must use its own `ACT_IS_FAMOUS` contract.
The readiness report's +9 research horizon is diagnostic only; live fame
selection may inspect the complete source range through HERO before applying
the existing route, output, protection, and finite-action gates.
An ordinary source-ranked stop may opt into one exact source-material bystander
only after fresh selectors, easy-kill considers, ordinary unarmed source
identities, and one combined HP, damage, resource, and six-action budget pass.
Extra, unknown, armed, scripted, special, protected, or scope-changed mobiles
remain hard rejections; this path is not a generic crowd override.
A source-verified displaced sentinel may resume the already-vetted outbound
step to its registered reset room after a temporary crowd in the preceding
room; this is navigation evidence only and never combat permission.
That exact changed-input shape may arm one persisted, same-boot revalidation;
the outer crowd wait can open only its matching segment, which consumes the
marker at start and closes it at the boundary. A fresh crowd, loss, hazard, or
absent endpoint remains authoritative and cannot be bypassed.
For a required-loot endpoint with an explicit source pre-entry scan, one
configured short re-scan may wait for an adjacent wandering hazard to move;
the second hazard remains a hard return, and this retry grants no combat or XP
permission.
Source gear planning must retain route audits for direct ground resets and
carrier drops. A reachable, no-combat ground reset may be selected before a
pending flight-funding loop; executable carrier candidates must match the source mobile,
room, and object, have one source spawn, pass level, HP, movement, protection,
and funding gates, and use exact post-kill loot/equip actions. A `source-only`
or offline placement is analysis evidence, never campaign permission; live
carrier acquisition remains unproved. The sanctuary revision-279 exception is
limited to the exact Moria carrier: source must prove global capacity two with
one reset entry in each of the two audited rooms, and the result is one bounded
required-loot maintenance attempt, never ordinary XP permission. A completed
automatic area-reset wait may reopen one source-narrowed capacity probe for
this exact carrier, consumed at persisted segment start; live absence closes
 it for that boot without XP credit.
For `recover-daycare-ring`, only the room-6605 old-doll reset (mobile 6605,
object 6601) carries the pink ice ring. Require both reset-load selectors in
that room and choose the last exact selector; with fewer than two, return
without a kill. Its below-band consider is expected required-loot evidence,
never progression XP or a permanent same-level/boot exclusion. After a miss
or crowd abort, preserve the three-positive-XP-segment cooldown; count only
same-level, same-boot, non-maintenance segments, then recheck the live route
and crowd before the next bounded attempt.
When flight funding is short and a candidate has no audited coin balance or
measured same-boot proceeds covering the shortfall, a failed funding route, a
completed kill whose liquidation produces no sale proceeds, or a ground-probe
target and its one expanded locator retry recorded absent may hand back to
source-ranked current-band ground XP for at most three same-level, same-boot
attempts. A pending exact locator retry takes precedence. Persist the marker
and return to funding afterward; this is a bounded throughput exception, never
a reboot-wide XP pause or an unbounded retry.
The funding handoff must retain the selector's existing bounded capacity-only
admission, including its independent route-program audit. This does not permit
an unresolved live crowd, extra source rejection, or below-band target.
If funding is unavailable and either the bounded ground-XP budget is exhausted
or a fresh ground search has no eligible target, a fully recovered healer
checkpoint may select the next executable
registered policy for the current level. Preserve the funding marker, retain
the policy's ordinary route and combat gates, and do not wait for a reboot
solely because flight remains unfunded.
If that selection also has no executable policy, it may use the existing
one-per-level/reboot frontier quest request, with live quest availability and
nonnegative fame. Share the same request marker; funding exhaustion grants no
extra requests, cooldown bypass, or target permission.
Policy selection alone is not a dispatched request. Reopen it once only when
the exact saved request segment returned to healer room 3054 after the pouch
listing timeout, with unchanged level, boot, XP, and loss total and no
`quest_request_attempt` event; consume that retry at policy selection.
The same shared quest request may follow a selected hunt whose required
sanctuary supply is exhausted, from a recovered, provisioned healer checkpoint
with observed quest status. Preserve sanctuary attempts and protection gates;
this authorizes a request, never the generated quest's route or combat.
Noncombat Circus quests may use the source-audited admission sequence: an
independently reachable shopkeeper mobile 4400 in room 4402 stocks key object
4400, which unlocks room 4415 south to 4416. Confirm the ticket before proceeding;
retain the full route audit, finite budget, and exact quest-object requirement.
Other locked routes and kill quests do not inherit this admission exception.
The exact Moria flight-funding ring route may tolerate only the two source
transit mobiles 3062 and 3066 when both remain wandering, `ACT_WIMPY`,
`spec_fido`-only, unprogrammed, unarmed, and within the live character's
damage bound. Keep the exact `where drunk` preflight mandatory, preserve the
live same-room crowd rejection and finite transit-fight cap, and require the
ring's positive live sighting plus a real flight shortfall. Record all such
segments as `funding_only`; they are not progression XP. This is source- and
offline-test-backed only; live acquisition remains unproved.
The source-defined Gnome treasury stash in room 1570 is one additional,
funding-only exception: verify money objects 1516/1517, the exact route, and
eight level-3 guard resets (maximum five after source fuzz). Their nominal sum
is 1,240 copper-equivalent, but `db.c` fuzzes each denomination above ten by
ten percent in either direction unless `ITEM_DONOT_RANDOMISE` is set. Require
the minimum independently fuzzed payout (1,175 copper-equivalent for these
objects) to cover the current flight shortfall, not the nominal sum. It is
allowed only when the player is more than ten levels above those guards and the
route-program audit passes. The guards are transit evidence, never XP
targets; changed crowd size, objects, rooms, or route closes the exception.
For the Dwarven Catacombs sanctuary reserve, room 6505 is pickproof and
`pick lock` is never a bypass. The only current source-backed route uses key
6502 from the raw room-6505 dwarven-guard reset (mobile 6500). Its live
maintenance gate must resolve the exact source identity in room 6505 and use
one live TARGETMODE selector at a time. The source-audited two-reset shape
allows at most four same-prototype, passive, non-special guards in sequence;
each requires its own below-band `consider`, exact selector, and corpse loot
step. Stop as soon as key 6502 is carried, then issue the audited `unlock
west`; gate kills are never progression XP. A missing selector, unknown or
extra mobile, non-good alignment, or more than four guards remains a hard
rejection.
The exact Dwarven Catacombs required-loot route has one additional level-25
transit exception: source mobile 2011, the wandering level-15 zombie with
`spec_cast_mage`, may be tolerated only when the route registers that VNUM,
the live GMCP enemy record confirms it, and the source HP/damage bounds still
fit. It is one bounded transit interruption, never an endpoint target or XP
kill; any extra, unidentified, or changed special remains a hard rejection.
DD4's `violence_update` makes same-prototype guards join a player's fight, so
the Dwarven key gate also requires a verified sanctuary reserve before dispatch.
If the reserve is absent, select the bounded Moria reserve route first; after
its reboot-scoped attempts are exhausted, checkpoint as unavailable rather
than entering the aggregate guard fight. Revision 318 records this boundary.
Nested resource reports must preserve every container VNUM, required key VNUM,
and source key-carrier VNUM. Closed or locked containers are never treated as
loose ground loot; a locked placement receives an explicit key-acquisition
rejection unless a named, source-audited executor proves the exact extraction
sequence. The inspection CLI must expose this provenance so source-only
evidence cannot be mistaken for campaign permission.
Route-analysis keys require the same distinction: a source path that names a
key is diagnostic only until an independently reachable, source-safe key
carrier or ground reset is proven. If every key reset lies beyond the locked
route, record a circular-acquisition rejection and never dispatch the resource
route. Do not widen level, capacity, output, or protection gates merely to
obtain a recovery object.
When a source-backed sanctuary carrier has exhausted its two current-reboot
attempts, arm at most one `campaign_sanctuary_area_reset_recheck` from a live,
safe healer checkpoint. Without a current protection-loss marker, do not let
this maintenance route preempt an executable current-band hunt; arm it only
after the selector reports no safe hunt. Wait only through the normal bounded
reset path, retain the old attempt count and segment boundary for audit, and
mark the recheck spent before dispatch. A second failure is terminal for that
reboot; do not turn reset handling into an unbounded sanctuary loop.
An exact same-level, same-boot source-ranked loss that ended before target
combat may receive one route-only revalidation only when the saved evidence
proves no target engagement, one source-labelled below-band transit hazard,
full recovery, and a fresh source-safe candidate with the normal output,
movement, route, and identity gates. Consume the marker at segment start;
clear it only after a productive target result, and close it after another
failure. This is a bounded evidence repair, never a general retry or a way to
promote incidental kills to progression.
Capacity-container metadata must be reconstructed chronologically from
successful or ready segment end states. Later explicit claims suppress stale
legacy restore evidence; carried capacity items are never left pending. If a
live capacity claim is rejected for weight, allow one healer-side `eq all`,
remove/lodge relief action, and one retry, while preserving the ordinary
recovery and bounded-retry gates. After any worker interruption, the next
startup must recover the prior run before opening new live work; diagnostic
processes must be stopped once their bounded inspection is complete.

Source weapon ranking must use DD4's load-level minimum/maximum generation,
not a dice interpretation of prototype values. Keep source estimates separate
from actual identified damage; Telnet worn-equipment records omit damage, and
legacy instance ID zero cannot bind persisted values to one unique weapon.
Identification requires the weapon in inventory. Confirm re-equipping before
travel and acknowledged logout before treating an inspection as complete.
Automatic identification is one healer-side, positive-practice, unambiguous-item
attempt per connection, with five-second replies and one rearm on timeout.
Its saved audit is diagnostic only across reconnects; confirmed live readings
may inform encounter output without weakening route, identity, or action gates.

Advanced-training supply acquisition is bounded maintenance, not permission to
travel to the teacher. It requires a fresh useful-lesson audit, a source-safe
vendor route, one exact live item quote and selector, a 100-copper reserve, and
confirmed inventory growth. Persist the attempt before dispatch; never repeat
it on reconnect. Follow `docs/OPERATIONS.md` for the single legacy spending-cap
repair. The separate consumable teacher journey requires a completed purchase,
fresh carried selector, acknowledged consumption, fresh GMCP invisibility,
positive source lesson gains, and enough movement for the exact route plus its
reserve. Check the city obstruction before consuming the potion; persist one
journey attempt per level and boot before dispatch. This noncombat journey alone
may use the equipment-aware invisibility audit; ordinary routes retain their
equipped-hazard rejection. A changed exit, effect, health, or movement budget
ends the trip through healer return. See `docs/OPERATIONS.md` for proof status.

## Communication

Use natural, conversational language in every update and explanation. Sound
like a helpful person, not a technical lecture: explain the practical point
first, keep it brief, and avoid unnecessary jargon, acronyms, and play-by-play
implementation details. Say "the login greeting did not arrive" rather than
leading with a protocol diagnosis. Add technical detail only when it helps
explain a decision or the user asks for it.

Keep `DEVELOPMENT_CONVERSATION.txt` as the Discord relay's source of truth.
At the start of every assistant turn, before commentary or other tool work,
append the newest visible user message verbatim with `--speaker USER`. Append
each outgoing commentary or final with its exact speaker and body before
displaying it. This applies after interruptions and context compaction too;
never assume the newest visible user message was already captured. Use the
helper's `--body-stdin` option with a PowerShell
here-string; the helper decodes piped bytes as UTF-8 even when the Windows
Python console encoding is Windows-1252. The relay cannot read Codex chat
directly. If a post is missing, check the source record and streamer delivery
log first; do not replay history or launch a second streamer when the existing
worker is healthy.

## Work Rhythm

Spend nearly all work time advancing the HERO100 objective through useful
implementation and campaign progress; regression work is secondary. Do not run
regression tests more than once per local calendar day
(Pacific/Auckland); build useful implementation and campaign progress before
that one batch. This is a maximum, not a daily quota: skip tests when they do
not justify the time. Choose focused tests for routine changes, or the full suite for
a coherent milestone or release checkpoint, never both on the same day. If a
run exposes an unrelated existing failure, record it and keep moving; fix it
when it blocks the active work or creates material risk, not as an automatic
detour.
Record each daily test batch and outcome in `runs/regression_test_batches.json`
before any later test invocation; failures also consume that day's allowance.
After two full-length attempts on one character yield no net XP, inspect the
saved blocker and switch to a distinct registered route or another character;
do not repeat an unchanged same-boot route. Keep unrelated regression cleanup
behind the next substantive implementation or campaign batch.
For ordinary live hunts, keep the standard 180-second segment bound unless a
named short probe has a specific reason to use less. Do not shorten hunts for
rotation speed; verify kills and XP rather than treating a ready status as
progress.

## Security And Changes

Use Windows Credential Manager; never place secrets in YAML, logs, or tests.
Preserve non-secret persona metadata in run context. Keep changes local: no
pushes, remote merges, or PRs. At most one local commit per 24 hours, at 9:00 PM
Pacific/Auckland, with a 60-second timeout and no retry for 24 hours. Use concise
imperative commit subjects. Update usage and proof status when behavior changes;
keep historical run narration out of these operating instructions. If the
current platform usage quota is exhausted and the user-authorized reset is
available, consume that reset automatically rather than asking or stopping.
