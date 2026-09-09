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

Refresh the DD4 source periodically, roughly daily during active work. Use a
bounded ordinary pull, preserve source pins and revision evidence, and defer
network failure rather than blocking development. Source area files and C code
are legitimate game knowledge. Never modify the upstream game to make a test pass.

## Live Sessions

Use indexed latest-state lookups for terminal run outcomes, not full transcript
loads. Completion/runtime-cap and failure lookups have independent precedence;
retain the entire selected payload, explicit empty kill ledgers, and newer
events. Do not cache terminal absence or remove loss history to speed startup.
Measure public startup separately from query benchmarks and distinguish cold
from warm reads. Faster inspection is not XP or combat-readiness evidence.
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

Check fresh SQLite events and process state to diagnose silence. JSONL size or
stale metadata alone does not prove a hang. If a connected worker emits no
progress for 45 seconds, allow one bounded reconnect; if still silent, close
only that exact worker and preserve interruption evidence. Never kill unrelated
Python or Codex processes. An observation timeout is not proof of worker exit.

## Gameplay And Evidence

Midgaard recovery and logout belong at healer room 3054, one north of recall,
not the Mage's Laboratory. Wake to eat/drink during sleep when needed; never
change equipment asleep. Never log out in Purgatory: recover the corpse, loot,
restore gear, leave the portal, then hand off once to healer recovery.

Optimize useful kills and net XP per complete journey. Keep attacking viable
targets until a meaningful health, protection, nutrition, movement, or runtime
boundary. Do not kill below-band targets for XP, infer emptiness from one room,
or treat sanctuary expiry alone as a losing fight. Retain source risk, crowd,
consider, and observed loss gates. Repeated attempts need changed evidence.

A world-time probe may recheck a recorded city-shop obstruction once from healer
3054. Only a complete, positive off-route locator from that successful run,
with the same observed reboot, can release route cooldowns. Missing or absent
locations, cached checkpoint evidence, and actual purchase failures cannot do
so. This supersedes kill-only aging for that positive revalidation case, not
the normal shop preflight or any combat-loss gate. No additional wait, segment,
loan, or purchase is authorized by the probe.

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

The server currently masks GMCP alignment as 50000 below level 10. Preserve
that raw observation but do not use it as a real alignment or evidence that
`spec_guard` will not assist. The GMCP and MSDP server paths differ; this is
not evidence of corrupted transport. Field city preflight shares the existing
three 12-second healer waits and locator parser, scoped to the actual source
route plus fountain. A completed absence or off-route observation permits
normal departure; silence does not. Keep its `campaign_field_city_preflight`
audit separate from shop-funding flags and retain ordinary combat/loss gates.

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

## Documentation

`README.md` is current usage; `ROADMAP.md` is delivery gates. Dated reviews hold
analysis and run evidence. `docs/history/` preserves prior documents without
making their old "latest" sections authoritative. Update current facts once
in the active review rather than copying every run into all three root files.
