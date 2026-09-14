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
full source map. This report is diagnostic only; it never grants live dispatch
permission.

Refresh the DD4 source periodically, roughly daily during active work. Use a
bounded ordinary pull, preserve source pins and revision evidence, and defer
network failure rather than blocking development. Source area files and C code
are legitimate game knowledge. Never modify the upstream game to make a test pass.
The estimator mirrors the pinned source's inherited and area `MobHPMod` and
`MobDamMod` scalars. `MobDamMod` is applied to each positive NPC attack before
sanctuary or critical arithmetic; an unresolved scalar is a hard rejection for
combat and transit budgets. It also credits `fight.c:do_knife_toss`'s
eye-dependent face-hit double only when parsed target body-form evidence proves
eyes; unknown anatomy remains uncredited.
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
breathers, scripted specials, or an unbounded fight. Run **13256** measured
Green at **576 HP** versus Kestrel's **342-point** conservative output ceiling;
the bot withdrew after gas nausea and DD4 applied a **385 XP** loss. That exact
policy is closed for the current boot. Revision **301** fixes the separate
handoff that previously failed to carry an eligible improved-output retry into
the protected live stop; a live kill and fame change must still be recorded
before any policy is treated as proven.

## Live Sessions

Use indexed latest-state lookups for terminal run outcomes, not full transcript
loads. Completion/runtime-cap and failure lookups have independent precedence;
retain the entire selected payload, explicit empty kill ledgers, and newer
events. Do not cache terminal absence or remove loss history to speed startup.
Measure public startup separately from query benchmarks and distinguish cold
from warm reads. Faster inspection is not XP or combat-readiness evidence.
When a checkpoint contains an observed training listing for the current level
and reboot, use that compact audit as the skill capability source; do not replay
up to 4,096 historical segments. Keep the legacy event backfill for checkpoints
without that evidence, and retain visible preparation boundaries so a shared
SQLite database cannot make a live launch appear hung.
When reconnect reveals a verified same-level XP drop, retain it as a campaign
loss lower bound even without a captured penalty message. Do not add it twice
to explicit loss counters, infer a death or command-level cause, or reopen a
failed hunt while repairing the counter. Use saved per-segment baselines for
idempotent history repair.
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

Check fresh SQLite events and process state to diagnose silence. JSONL size or
stale metadata alone does not prove a hang. A pre-login socket gets a 15-second
banner/creation-prompt bound; an authenticated worker gets the configured
45-second inactivity bound and one bounded reconnect. If it remains silent,
close only that exact worker and preserve interruption evidence. Never kill
unrelated Python or Codex processes. An observation timeout is not proof of
worker exit.

## Gameplay And Evidence

Midgaard recovery and logout belong at healer room 3054, one north of recall,
not the Mage's Laboratory. Wake to eat/drink during sleep when needed; never
change equipment asleep. Never log out in Purgatory: recover the corpse, loot,
restore gear, leave the portal, then hand off once to healer recovery.

Field recall is an asynchronous command: keep it in flight until a real
Temple-of-Midgaard room response or equivalent authoritative room update is
observed. The runner may use the decision-time `CharacterState` room as the
recall origin when the text parser is one event batch behind; a missing
immediate response is not an immediate recall failure. The normal bounded
inactivity and reconnect watchdogs still apply.

Optimize useful kills and net XP per complete journey. Keep attacking viable
targets until a meaningful health, protection, nutrition, movement, or runtime
boundary. Do not kill below-band targets for XP, infer emptiness from one room,
or treat sanctuary expiry alone as a losing fight. An exact source-required
resource or loot target may be admitted below-band only with positive carrier
evidence, a bounded safe route, and an explicit missing-resource objective; its
XP is maintenance evidence, never progression evidence. Retain source risk,
crowd, consider, and observed loss gates. Repeated attempts need changed
evidence.

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
to the route contract. Fixed routes, unregistered VNUMs, crowds, specials,
programs, or useful-band live rolls remain withdrawal conditions.

A world-time probe may recheck a recorded city-shop obstruction once from healer
3054. Only a complete, positive off-route locator from that successful run,
with the same observed reboot, can release route cooldowns. Missing or absent
locations, cached checkpoint evidence, and actual purchase failures cannot do
so. This supersedes kill-only aging for that positive revalidation case, not
the normal shop preflight or any combat-loss gate. No additional wait, segment,
loan, or purchase is authorized by the probe.

The same rule applies to a field-city departure that stopped after its bounded
healer waits. Persist `campaign_field_city_preflight` with its level, reboot,
locations, stop evidence, and exact policy ID. A same-level, same-reboot
continuation selects an unavailable cooldown for that recorded policy; an
alternate source-ranked route receives its own bounded preflight. Checkpoints
without a policy ID remain globally conservative and require fresh world-time
or route evidence. The checkpoint merge keeps a policy-scoped stop through a
safe healer recovery, so maintenance cannot accidentally reopen the same
blocked route. This prevents replaying an unchanged obstruction while keeping
route rotation live.

An exact same-level, same-reboot protection marker with no sanctuary reserve
and no executable independent current-band route is also a reset boundary. A
runner invoked with explicit reset retries returns `ready` with
`awaiting_area_reset` and opens no gameplay segment; the outer runner waits
once for the configured interval, then opens only the maintenance world-time
probe. A capped invocation remains `blocked`. This preserves the protection
requirement and prevents repeated invocations from becoming a terminal
liveness failure or silently buying flight against a higher-priority funding
objective.

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

Use exact source keywords and connection-local target IDs. Mobile, object,
room, and object-set VNUM namespaces are distinct. Never restore pending
commands, companion ownership, or timing rights from saved checkpoints.
Field route greeting checks may use fresh invisibility only for an exact
source mobile whose ordinary GREET program requires `can_see`. Audit detection,
source-level bounds, aggression, specials, scripts, and reset equipment; unknown
or ALL_GREET cases do not qualify. Require current-connection GMCP effects with
at least two observed ticks remaining. An exact invisibility-loss message
revokes the exemption even while an old affect record remains; reapplication
needs both its positive message and fresh GMCP. Preserve pending scan ownership,
unrelated hazard checks, combat/emergency returns, losses, and retry budgets.
Skipped visibility checks are audit evidence, not completed preflight or cached
scan permission; never restore them from checkpoints. Report locator locations
separately from the room where the command was issued.

Revision 243 grants one revalidation only for the exact current-level/reboot
sanctuary failure produced by the obsolete visible-GREET check. Archive that
result under `campaign_sanctuary_visibility_revalidation`, consume the marker
before opening the sanctuary segment, and close it as succeeded or failed from
the fresh result. Do not remove the prior XP loss, protection requirement, or
attempt count. Absence, route failure, interruption, or death does not authorize
another attempt.

Revision 244 grants one further revalidation only when revision 243 positively
located the invisible carrier but the old graph could not reach it. Consume the
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
unknown, pre-combat, and endpoint-combat hazards remain blocked. Both modes
share the original runtime and command limits. Paths must be
open, known, same-area ground routes without random, private, solitary, no-recall,
wall, flight, or unresolved source transit hazards. Ambiguous room names authorize
only the mapped accessible subset, never every room with that name. Preserve
pre-entry scans, exact consideration, crowd/loot checks, and all loss/retry gates.
Retain required familiar staging on the outbound prefix, the original city
preflight, exact target/consider/crowd checks, and the normal reset fallback.
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
Run 13053 is live evidence for the handoff and +168 player XP on Granny
Jenkins; it does not establish sustained progression or HERO proof.
DD4's source-defined pony is charmed and cannot leave its master in the same
room. Its withdrawal command therefore uses the source-recognized `flee Fear`
argument to bypass the NPC random no-op, then requires `The pony sleeps.` as
positive in-place evidence. `Ok.` alone remains only order acceptance.
If the withdrawal budget is exhausted without departure or positive in-place
sleep, abort the stop and enter the normal healer return. A no-command result
from the retry helper is still a failure boundary; it must not fall through to
the player's damage selector in the same decision cycle.

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

Funding completion and objective eligibility are separate ledgers. A source-
identified below-band kill may complete an explicitly selected provision-funding
action and age its retry cooldown, while its XP remains excluded from objective
progression. Prefer the funding segment's durable `completed_kills` event over
an empty `objective_kills` list, and repair its completion marker on resume from
that exact run only. A completed funding action advances cooldown even when its
XP delta is zero. An observed below-quote balance remains actionable despite a
retry cooldown; negative fame must not override that safe funding path. None of
these repairs authorize another target or promote low-value XP.

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
required-loot expedition withdraws after bounded source-absence sightings, keep
that raw terminal evidence and recover it at startup; apply the registered
current-reboot cooldown before retrying the exact route. The sole revision-279
exception permits the exact Moria sanctuary carrier with global capacity two
only when source proves one reset entry in each of its two audited rooms; it
authorizes one bounded maintenance attempt, never ordinary XP hunting. The
generic capacity entitlement armed by a completed automatic area-reset wait
may reopen that same audited carrier once when the older one-shot marker is no
longer present. The entitlement is source-narrowed to mobile **4055**, object
**4050**, rooms **4064** or **4071**, global capacity two, and one room entry;
it is consumed in the persisted segment start before connecting. A live
absence closes the probe without XP credit and cannot be replayed in the same
boot. The
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
Thief route. It is selectable only at level 26 or above when the character
needs a strictly better piercing weapon, has the observed currency ledger and
capacity for the source lockpick plus dagger, and has a sanctuary reserve. The
plan buys lockpick object 38 from shopkeeper mobile 3050 in room 3120, trains
the source prerequisite `thief base` to 30% before `pick lock` to 60%, returns
to healer room 3054, and follows the source-replayed route to room 16619. It
uses `pick west`, `open west`, and the exact endpoint chain to room 16635,
where smuggler mobile 16609 is source-reset with equipped dagger object 16614.
The smuggler's `spec_thief` procedure is economic rather than combat-damaging,
but the plan still caps 20%-of-carried-coin exposure at 250 copper and retains
the sanctuary-backed live HP and damage-window probe. Source cost is a funding
floor, not a promise that a reboot's live shop price is identical; an actual
purchase failure must checkpoint as evidence. Source replay and offline
selection do not prove live purchase, door entry, combat, or loot acquisition.

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

## Documentation

`README.md` is current usage; `ROADMAP.md` is delivery gates. Dated reviews hold
analysis and run evidence. `docs/history/` preserves prior documents without
making their old "latest" sections authoritative. Update current facts once
in the active review rather than copying every run into all three root files.
