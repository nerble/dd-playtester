# Operating Instructions

## Commentary And Discord

Append every new user steering message and every visible assistant update or
final response verbatim to `DEVELOPMENT_CONVERSATION.txt`. Do not append internal
goal continuations or injected environment context as user speech. Never rewrite
this append-only file or replay historical entries to Discord.

Before publishing commentary, run:

```powershell
python tools/conversation_log.py append --speaker "CODEX COMMENTARY" --body "Exact update text"
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

## Authorization And Fail-Fast Behavior

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

Combat-pouch audits at departure, repacking, and logout share a bounded reply
buffer. Require the complete contents listing before replacing either potion
ledger; unrelated room or healer text is not an empty-pouch observation. After
five seconds without confirmation, preserve the previous ledger and return to
healer logout without hunting or retrying the audit. A confirmed empty listing
does clear old quantities. Newly discovered potion keywords still require the
existing source-safety checks; ambiguous potions require retained provenance.

Gear acquisition uses the same per-category capacities as stance selection.
Compare a candidate with the weakest selected slot, or an empty slot, after
including carried alternatives. Preserve actual duplicate-item quantities, but
never add the structured equipment snapshot to its duplicate textual summary.
An improved rank is not permission to bypass source route or combat gates.

Routine repository, source refresh, tests, live runs, and exact process audits
are already authorized. Use ordinary available tools; do not ask again or
manufacture an escalation. If an external permission review times out, retry
once promptly, then defer that operation and continue useful local work. Never
wait indefinitely for an invisible review or repeatedly poll unchanged failure.

Keep all Git changes local. No pushes, PRs, or remote merges unless a new
explicit one-off instruction overrides this policy. Attempt one local commit
at most per 24 hours, at 9:00 PM Pacific/Auckland. Bound it to 60 seconds; a
failure consumes that day's attempt. Use the current shell's native filesystem
operations and verify absolute targets before any recursive move or delete.

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
Source refreshes clear source-derived routes and cooldowns, but preserve exact
XP-loss records and observed absent-target results from the current MUD boot,
along with the matching absence cooldowns. A local source update must not erase
live evidence and silently reopen a failed fight or an expensive empty route;
evidence from an older boot is discarded, and stale source estimates still
cannot authorize a retry.
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
Normal live segments have a 180-second cap, plus separate 60-second setup and
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
selection.
The normal success-return path must promote the starter's `fastwalk_resume_checkpoint`
into those campaign keys before policy selection. Deep-route locator narrowing can compact
the runtime stop tuple, so resume may re-anchor only on one unambiguous audited transit
stop, endpoint, or route leg; ambiguous room matches remain closed.

Check fresh SQLite events and process state to diagnose silence. JSONL size or
stale metadata alone does not prove a hang. A pre-login socket gets a 15-second
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

Midgaard recovery and logout belong at healer room 3054, one north of recall,
not the Mage's Laboratory. Wake to eat/drink during sleep when needed; never
change equipment asleep. Never log out in Purgatory: recover the corpse, loot,
restore gear, leave the portal, then hand off once to healer recovery.

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
A recent level-8 Circus attempt found the Drunk at Lusty Ogres
Tavern, Main Street, and the Mage's Guild entrance, then returned safely
without engaging a target. The exact mapped bypass is admitted only when the
fresh route-level locator is clear of its rooms; that check does not depend on
an earlier healer-side flag. Existing XP, health, movement, and route gates
remain authoritative. No successful live detour or HERO proof is claimed.

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
checkpoint. The outer runner may wait once for the configured area-reset
interval, then clear the exhausted result and reset the active attempt count
to zero while retaining `prior_count`, `area_reset_cycle`, and the reset
boundary. Startup repair ignores pre-boundary sanctuary segments. The marker
becomes `attempted` before the fresh route opens, so a second failure cannot
reopen the route again during that reboot; acquisition or a new reboot remains
the only other reopening event. A source checkout refresh must preserve this
spent marker and attempt evidence: it may invalidate source-derived route
results, but it must not let generic protection fallback or an automatic
capacity probe silently re-dispatch the exhausted Moria route. The autonomous
outer runner must honor that persisted boundary across process restarts; a
spent recheck is a durable blocker, not permission to start another area-reset
wait.

Flight funding must not strand a healthy, fed character after its safe carrier,
one ground probe, bounded current-band XP rotation, alternate funding targets,
and available bank loan are exhausted. From a fully recovered healer
checkpoint, the campaign may then re-run normal selection without the funding
override and take an executable registered policy for the current level.
Preserve the funding marker; this handoff grants no combat permission and does
not bypass the selected policy's route, identity, consider, output, or health
gates. Do not wait for a reboot solely because flight remains unfunded.

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
1,240 coins. The route crosses eight reset entries for level-3 hobgoblin
guards, but DD4's `update.c` skips aggression when the player is more than ten
levels above the mobile. Admit this stash only when the source rooms, object
VNUMs, crowd limits, route-program audit, movement budget, and shortfall all
match. Record it as `funding_only`; it is never ordinary XP permission, and a
changed crowd or source identity closes it.

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
special remain rejected. A guard elsewhere in the room is different: its
`spec_guard` code can attack a player fighting an NPC whose alignment is below
300, including a good player fighting a neutral target. Keep that bystander
route closed rather than treating the `violence_update` good-alignment rule as
protection from the guard's separate special.
The GMCP and MSDP server paths differ; this is not evidence of corrupted
transport. Field city preflight shares the existing three 12-second healer
waits and locator parser, scoped to the actual source route plus fountain. A
completed absence or off-route observation permits normal departure; silence
does not. Keep its `campaign_field_city_preflight` audit separate from
shop-funding flags and retain ordinary combat/loss gates.

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

One separate source-ranked exception covers a plain, unarmed, unscripted
aggressive target only when its route carries the exact audited `where`
preflight and every transit aggressor is independently bounded. The runner may
consume sanctuary before the exact opener and obtain one live HP/damage-window
probe; the lower source HP bound must fit the fixed output budget, and any live
GMCP ceiling above that budget still forces withdrawal. This does not authorize
special, armed, scripted, or otherwise uncertain aggressive targets.

When sanctuary recovery is cooling, the runner may also try at most three
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
A protection-recovery fallback may retain one independent, source-audited plain
target even when its fresh useful-XP probability is below the ordinary ranking
floor, but its source HP range must satisfy the same audited output-window rule
even when a passive endpoint can reveal live HP before the opener. It must also
pass the live route, movement, consider, and healer-return gates. Same-boot
below-band evidence for that exact source mobile remains a hard exclusion; the
fallback never converts a known low-XP target into progression credit.
If a
required-loot expedition withdraws after bounded source-absence sightings, keep
that raw terminal evidence and recover it at startup; apply the registered
current-reboot cooldown before retrying the exact route. The sole revision-279
exception permits the exact Moria sanctuary carrier with global capacity two
only when source proves one reset entry in each of its two audited rooms; it
authorizes one bounded maintenance attempt, never ordinary XP hunting. The
generic capacity entitlement armed by a completed automatic area-reset wait
may reopen that same audited carrier once only while the sanctuary attempt
counter remains available; it is never an alternate retry after the bounded
sanctuary route is exhausted. The entitlement is source-narrowed to mobile
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
source profiles, known selectors, good player alignment, and no extra or
unknown mobile. Revisions 313 and 314 reopen their exact same-boot artifacts;
315 recovers the old selector-persistence acquisition, 316 reopens only the
matching reconnect loss, and 317 records the alternate-room route. Revision
318 additionally requires a verified sanctuary reserve before this gate is
dispatchable, because DD4's same-prototype guards automatically join the
fight. Without that reserve, select bounded Moria recovery first and stop as
unavailable after its finite reboot-scoped attempts. These revisions do not
broaden the live gate. At the exact level-25 frontier, source mobile 2011 is the only admitted transit special: its
level-15 upper bound is exactly ten levels below the player, its
`spec_cast_mage` acts only after combat begins, and its source damage bounds
fit the player ceiling. The live route must confirm that VNUM through GMCP;
the interruption is bounded maintenance combat and never progression XP.

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

## Documentation

`README.md` is current usage; `ROADMAP.md` is delivery gates. Dated reviews hold
analysis and run evidence. `docs/history/` preserves prior documents without
making their old "latest" sections authoritative. Update current facts once
in the active review rather than copying every run into all three root files.
