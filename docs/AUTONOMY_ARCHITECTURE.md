# Character-Independent Autonomy

DD4Tester targets any valid race, gender, base-class, and subclass combination.
Character names identify credentials and stored history only; they must never
select behavior.

## Current Boundary

The deterministic Telnet/GMCP path is the product boundary under active
development. Mudlet consumes the same command and observation contract, but
Mudlet profile automation and Windows VM lifecycle control are validation work,
not alternate decision engines. AI decisions are intentionally absent until
the deterministic path can be replayed and measured.

The public hero entry point is also safe for an existing named character:
explicit and environment credentials take precedence, then a bounded
character:name credential lookup reuses a stored password before any new
password is generated. An untouched `--prepare-only` workspace may generate
and store its first password; once SQLite records a campaign for that
workspace, a missing credential is a strict resume error and never authorizes
replacement.
The `hero` command also exposes the campaign runner's bounded
`--retry-stalled` rotation. It may reopen only a candidate blocked by trailing
no-progress history; current-reboot absence, crowd, route, consider, resource,
protection, and cooldown evidence remain hard stops. Equal-horizon matrix
workspace matches remain explicit errors and can be disambiguated with
`--workspace`.

Research handoffs have an explicit liveness guard. Startup reconciliation may
remove stale result payloads, but that does not make the same selected policy
fresh. `_policy_for_state` requires a research handoff to differ from
`campaign_last_policy`; otherwise the source-ranked fallback rotates to an
independent candidate or stops safely. Run 8444 reproduced the old loop and
run 8446 live-validated rotation to the Shire Keeper route, which returned at
the 180-second segment boundary without an endpoint kill or XP loss.

## Live Safety Boundary

DD4 gas breath is represented as an affect named `nausea` whose metadata says
`gives: poison`; it is not necessarily named `poison`. The starter therefore
recognizes both fields. A poison-like affect in a recallable field room causes
one immediate recall decision, while a poisoned checkpoint in healer room 3054
stays asleep until the healer or the finite affect duration clears it. Runs
8379-8383 live-validated the surrounding behavior: the runner followed a
wandering Forest target, killed Arachnos mobile 6317 for 708 XP under
sanctuary, secured and sacrificed the empty corpse, returned to the healer,
and recovered without death or XP loss. This is level-17 safety evidence, not
HERO progression proof.

The required-loot cleanup path now assesses a live post-objective attacker
before its generic combat-recall guard. Run 8384 exposed the ordering defect:
the Moria carrier (source VNUM 4055) yielded 110 XP and its purple potion, then
source VNUM 4050 joined and the old path paid 208 XP before cleanup. The repair
is covered by a regression with the exact live selector pattern. Run 8385
completed a bounded source-ranked absence probe safely, but did not re-enter
Moria, so direct live validation of the repaired branch remains open.

The same boundary now covers a GMCP-only ordering variant. If `Char.Enemies`
replaces a just-defeated carrier with a different mobile before any attack text
arrives, `StarterPolicy` records that mobile as an unapproved post-objective
attacker and sends the exact `consider` before loot cleanup, another spell, or
escape. The regression is included in the 2,966-test offline suite. Run 9033
re-entered Moria safely and killed the large hobgoblin, but no pursuer remained
after the kill, so direct live trigger validation of this event-only branch is
still pending.

## Data Flow

1. A character YAML profile supplies identity and local safety limits.
2. `data/archetypes.json` resolves class aliases, subclass relationships,
   capabilities, training defaults, stat priorities, and progression tracks.
3. Live GMCP, text observations, inventory, effects, reboot identity, and
   campaign history form a `ProgressionContext`.
4. The progression selector chooses an evidence-backed policy from that
   context. It may use capabilities or a configured track, but not a character
   name.
5. The deterministic executor applies shared navigation, provisioning,
   recovery, combat, death, inventory, and checkpoint safeguards.
6. Every command records its stage, reason, category, and safety-critical flag.
   Reports derive progress, decision analysis, feedback signals, and first-
   person commentary from those records.

Event batches are applied in order: each parsed event updates the reducer and
is then observed by policy before the next event is processed. GMCP room VNUMs
and arrival metadata are authoritative for repeated-room routes. A room change
also acknowledges a pending move when the prompt was emitted before the room
update, preventing valid routes from being mistaken for inactivity.

The durable SQLite database is shared by character rotations. `RunStorage`
opens it with a 30-second busy timeout, so concurrent campaign workers wait for
one bounded commit rather than treating transient write contention as a failed
character run. Segment runtime limits remain the outer liveness boundary, and
the database checkpoint is authoritative when a wrapper exits after a segment
has already committed.
Before opening that shared store, each campaign claims an OS-backed lease keyed
by its database and config path. A duplicate invocation fails immediately
instead of marking an active segment orphaned; a genuinely dead process
releases the lease at the OS level so the existing restart recovery can run.

Named HERO resume is identity-based rather than directory-based. If matrix
workspaces contain duplicate manifests for one stored character, the resolver
chooses the closest campaign horizon that satisfies the requested target and
rejects equal-horizon ambiguity. Resuming can extend a campaign target but
never lowers it, preventing a short validation invocation from weakening the
matrix or HERO contract shared by YAML and SQLite.

Human inspection uses bounded projections too. `show-campaign` reads only
segment summary columns for its table and decodes the latest checkpoint once;
full state JSON remains available to the campaign engine and detailed reports,
but is not loaded for every historical row just to monitor progress. When a
campaign reaches its target, the runner writes `hero-report.json` and
`hero-report.md` beside the campaign YAML; `campaign-report` can regenerate or
inspect that aggregate without changing campaign state.

## Policy Lifecycle

The selector must distinguish three states. `verified` is reusable executable
evidence. `research` is a bounded live probe with explicit route, combat,
resource, and return limits. `unavailable` is a durable safe stop explaining
what evidence or implementation is missing. A checkpoint, source catalog
entry, policy count, or research result is not a progression proof by itself.

Quest-point gates are source rules, not inferred level bands. DD4's
`questpoints_required_for_advance()` checks current levels 29, 49, 79, and 99,
so the corresponding advancement milestones are 30, 50, 80, and HERO 100.
Live `Char.Quest` fields remain authoritative; when a legacy checkpoint has
total quest points but no requirement or shortfall fields, the selector derives
the missing values from this checked-in source rule before choosing ordinary
progression.

Dynamic kill quests now pass through the ordinary source-ranked candidate
builder before movement. The exact quest mobile and room must match a source
reset (or a source-reachable wandering target), and the candidate carries the
current level/HP bound, route hazards, companions, equipment, and special
procedures into the field stop. A target absent from that safe set becomes a
durable preflight stop instead of an unbounded name-based attack. The source
advancement function is authoritative over the older level-69 reminder in
`act_info.c`.
When the rejection is an active target safety failure, the campaign returns to
the registered questmaster with `quest abort`, then preserves DD4's bounded
abort cooldown before requesting a replacement. Missing source metadata still
produces an unavailable checkpoint rather than an unsupported live action.
The generated-quest ranker mirrors `quest.c`'s strict nominal target bands:
the maximum mobile level offset is +4 below character level 20, +9 below 50,
+14 below 80, and +19 thereafter. This allowance is passed only to the quest
candidate and its field stop; ordinary hunt selection retains its narrower
ceiling. Source-ineligible mobile flags and shopkeepers are rejected before
movement, and the normal HP, route, special, companion, crowd, and live
consider gates remain authoritative.
For wandering targets, the reported live room must be source-reachable from the
mobile's reset graph. The campaign adds that room as a temporary ranking
endpoint and dispatches the resulting source-safe route, preserving exact live
room identity without trusting a raw shortest path.
Retrieve, object, and hoard quest targets use the same source-safe route gate
even though they do not have a kill candidate. The gate blocks fixed-reset
aggressors, reachable aggressive wanderers, program-triggered attackers, and
large useful-band crowds on the route or at the destination; a source-unsafe
quest becomes a bounded preflight stop rather than an unreviewed fastwalk.

The fixed research registry has an intentional level-11 handoff for
tutorial-arena classes after their level-10 scout. At that first uncovered
level, `policy_for` returns the generic source-ranked hunt in research status
with a level-local policy bound. Explicit level-12 through level-80 routes
remain authoritative; at level 81 and above the same generic frontier applies.
The campaign then selects a source-identity-specific candidate and applies the
same live route, consider, health, resource, and healer-return gates. This
keeps the path to HERO executable without presenting an unresearched route as
verified.

The level-30 subclass handoff is separately source-capability-gated. The area
parser records mobile teaching entries; preflight requires a reset-backed route
from recall to a mobile that teaches both `teacher base` and the exact
`<subclass> base` skill. For the source-supported smithy subclasses, engineer
and runesmith resolve to Anon mobile 31002 (Jolob, room 31041), while Kerofk's
Gorn is not a valid teacher. This establishes executable route selection and
offline regression coverage, but not a live subclass transition.

Source identity is part of the policy key: area, mobile VNUM, reset room,
character level, and reboot identity are retained separately. Same-reboot
productive XP may carry a safe repeat across a level boundary when the source
identity is unambiguous and the normal live presence, consider, crowd, health,
equipment, and recovery gates still pass. Research candidates must not hide
such a repeat. Promotion requires objective XP, bounded damage and resource
evidence, loot or funding evidence where relevant, and a safe healer return.
The carryover ledger keeps both the latest source reward and the best confirmed
reward: the latest result remains authoritative for current failures, while the
best result can open one new level-specific live probe. A current low-reward
result cannot be resurrected by older success history, preventing a 0- or
10-XP loop.

Finite source-ranked hunt circuits derive their effective command allowance from
the registered outbound route, each hunt stop, and a fixed reserve for combat,
loot, return, and healer cleanup. The extension is recorded in the run and is
still finite; exhausting it becomes a retryable route hazard. This keeps a
large but valid source circuit from being cut off by a small profile default
without allowing an unbounded navigation loop.

The source-ranked selector normally stops when the current reboot has no
fresh, safe candidate. After ordinary safe pools are exhausted, a normal
resumable invocation or an explicit `retry_stalled` request may reopen one
fresh candidate blocked only by trailing no-progress history. It cannot
override live absence, crowd, route, consider, protection, resource,
source-identity, or cooldown evidence; the live result is persisted and the
next retry rotates rather than replaying the same blocked policy.

An operator retry is not proof of an area reset. Only the automatic retry
marked `reset_wait_completed=True` may consume reboot-local absence or crowd
evidence; otherwise the runner must preserve the cooldown and return an
explicit safe-stop state when no alternative is executable.

Protection recovery distinguishes source-proven non-combat specials from
combat-capable procedures. A productive candidate with only a safe special
such as `spec_fido` may use one existing sanctuary reserve after a single
XP-loss record; a candidate with another autonomy rejection, a combat special,
or a second loss remains quarantined. This preserves the risk boundary while
allowing the source evidence to improve XP/min when the special itself cannot
attack.

Audited caster specials are a shared selector/executor contract. Because
`spec_cast_cleric` and `spec_cast_mage` can blind before or during combat, a
route that must consume sanctuary is eligible only with persisted `cure
blindness` training or two verified purple potions. The runner records that
training capability at segment completion, and the selector otherwise keeps
the target out of the live rotation instead of discovering the mismatch after
travel.

This reserve rule is candidate-specific. A mage with one verified purple may
continue to a clean source-ranked target in the same level band; only the
selected blindness-capable caster special triggers the second-potion or trained
cure requirement. This keeps protection recovery proportional to the actual
combat hazard instead of stalling every safe frontier.

`spec_cast_undead` is audited separately from its transit-safe behavior. The
source procedure acts only after combat begins and selects spells by mobile
level. The selector admits only source ceilings below 15, bounds chill touch
and blindness damage, and requires one verified purple cure reserve when
blindness is possible without sanctuary; energy drain, harm, and gate remain
blocked. Caster specials that consume sanctuary retain the two-purple reserve
boundary unless cure blindness is trained. The starter uses the same
conservative source-level ceiling when deciding whether a live status effect
has a recovery path. Run 8377 live-exercised this route and recorded the source
target absent without XP change; run 8378 completed the resulting flight
maintenance handoff.

Each source-ranked XP-loss record carries the completed campaign segment that
created it. Reconstructing state or repairing an interrupted segment replays
that identity idempotently, so repeated startup metadata checkpoints cannot
manufacture additional losses; a distinct completed segment still increments
the reboot-local count.

Current-reboot explicit retry ownership is also durable. Circuit-consider
repair may restore missing per-stop evidence from historical segment starts,
but it cannot clear a policy recorded in the current explicit retry marker.
This prevents reconnects from oscillating a crowd retirement and producing
metadata-only checkpoints indefinitely.

Risk is evaluated per interruption, not as a blanket fear of death. On the
Dwarven Nobleman fastwalk, the source-level-seven goblin lieutenant may be
handled as incidental below-band transit combat from level fourteen onward
when the ordinary live combat, health, and crowd gates pass; the higher-damage
dark horseman and wyvern remain hard route hazards. If plain combat text
precedes GMCP, the executor waits one bounded prompt and resolves the enemy by
live mobile VNUM before accepting a below-band classification; an unresolved
identity remains a hard interruption. Before a source-ranked attack, the
executor also consults a source-graph index of same-name mobile VNUMs that can
reach the current room. If the expected source VNUM is absent or another
same-name VNUM is reachable, it records presence and skips the stop before
`consider` or `kill`; post-combat GMCP is never used as the first identity
check.

The aggressive endpoint path uses the same identity boundary. When arrival
text starts combat before the ordinary hunt prompt, a source-VNUM stop must
wait for `Char.Enemies`, match the expected mobile VNUM, and see exactly one
useful-band target with no material bystander. Duplicate or below-band live
targets are rejected before recurring combat; generic routes without source
identity keep their legacy text-only behavior. Run 7547 exposed the duplicate
guard case, the repair passed the full 2,699-test suite, and run 7549
confirmed a valid source endpoint still killed and returned safely.

Training graph revisions are persisted separately from general campaign
revisions. When a new class-aware priority is registered, source-ranked
segments clear stale practice-type deferrals for one fresh trainer audit and
record the new training revision only after the audit completes. Runs 7583-7584
live-validated this with mage `faerie fire`: the trainer taught it at level 16,
and the combat opener cast it once before repeated `chill touch`.

Source-verified self-healing potions are part of the shared combat-resource
contract. Once a keyword is tied to an exact source object, a fresh pouch audit
trusts the current observed quantity even if an older run recorded only one
acknowledgement for `put all`; unverified colors and same-keyword non-potions
remain excluded. The executor uses verified `cure critical`, `cure serious`,
`cure light`, and `heal` potions before the health-floor withdrawal. Run 7617
proved the amber `cure light` branch, then exposed a guardian death and
successful Purgatory/corpse/healer recovery. Its hard-health-floor protection
marker now quarantines that exact policy until a stronger reserve is available.

Protection loss is a shared combat decision, not an automatic flee. When a
consumed sanctuary affect disappears, the executor uses authoritative GMCP
player and enemy health plus live enemy level: a materially healthier or more
than one level higher opponent is withdrawn from below 75% player health, while
an opponent in the near-death finisher band may still be completed. This rule
is replay-tested against Kestrel's real 7376 death transcript and is applied
before another recurring combat action.

Maintenance fastwalks share the navigation executor but not the field-policy
ledger. A new maintenance route abort is recorded under
`campaign_maintenance_route_hazards`; transient target, crowd, absence, and
consider fields are restored from the preceding field policy before the
checkpoint is written. Resume migration removes legacy unowned maintenance
markers while retaining source-backed field hazards. This prevents safe
funding or healer returns from changing which progression route is retried.

## Current Proof And Debt

**Current live update (2026-08-24):** Praelarran is level 13 at 78,152 XP at
checkpoint 28988; Dorrik is level 24 at 363,330 XP at checkpoint 28574; Aeloria
is level 18 at 165,613 XP; Kestrel is level 24 at 336,913 XP; and Velnor is
level 6 at 15,471 XP at checkpoint 28565. Runs 9478-9479 created Serevian, a
fresh human male thief, through live creation and recovery. Runs 9515-9519
completed bounded maintenance without loss or death. Run 9520 killed six Mud
School opponents for 444 XP, run 9521 added 216 XP through five more
source-ranked kills, and run 9522 added 336 XP through three more. Runs
9524-9526 added 679 XP, run 9527 completed return-home maintenance, and run
9528 added 205 XP. Runs 9529, 9531, 9534-9535, and 9537-9538 added 1,230 XP;
the intervening checkpoints were safe maintenance or reset boundaries. Run
9540 crossed him to level 5; runs 9541-9543 completed level-5 setup and handoff
maintenance, run 9544 added 265 XP, run 9545 recorded an empty arena with one
bounded reset wait, and run 9546 completed return-home cleanup. He is safely
level 5 at 10,436 XP and checkpoint 28829, with maximum health 99 and mana 127.
Runs 9547-9548 and 9550 added 564 XP, runs 9552-9554 added 525 XP, run 9556
added 157 XP, and run 9558 added 122 XP; the other checkpoints were safe
maintenance or bounded reset waits. Subsequent bounded Serevian runs added
2,365 XP with safe maintenance and reset-wait checkpoints interleaved. Run 9589
crossed him to level 6 at 14,169 XP and checkpoint 28896, raising maximum health
to 113 and mana to 134. Runs 9590-9613 then completed bounded level-6 outfit,
recovery, and source-ranked rotations; productive routes added 955 XP while
empty or absent candidates stopped safely. Run 9613 left Serevian at 15,124 XP
and checkpoint 28948, full in healer room 3054. Runs 9614 and 9615 then safely
tested another Circus route and the Dwarven Daycare route without forcing
combat; the latest Serevian checkpoint is 28948. Praelarran run 9598 added 502
XP through Fleshmonger, and runs 9626-9628 added another 450 XP through the
current-band pool. His latest checkpoint is 28988; he is level 13 at 78,152 XP,
full HP and 155/176 mana in healer room 3054. This is tutorial
continuation evidence, not HERO proof. The read path now reduces GMCP
`Room.Info` before same-read text, and startup reconciliation preserves newer
maintenance-attempt markers. The full offline suite passes 3,008 tests. Run
9482 added 437 Shire XP; run 9483 found sanctuary recovery absent; run 9484
rejected a crowded secretary route; run 9485 withdrew at the hard health floor
with 34 incidental XP and no loss; and run 9486 added 452 objective XP from
the Shire receptionist. Runs 9487-9488 safely recorded Circus and Moria
no-target probes. Praelarran is 8,200 XP below level 14. The public HERO
credential boundary now generates a first password only for an untouched
prepared workspace and remains strict after campaign activity. The full
offline suite passes 3,006 tests. These are continuation and training proofs,
not subclass or HERO completion evidence.

### Historical detail

The latest bounded live continuation completed safe Dorrik, Kestrel, Aeloria,
and low-level rotations without an orphaned campaign worker. Aeloria is level
18 at 165,613 XP at checkpoint 27725 after a bounded retrieve-route loss;
Dorrik is level 24 at 363,190 XP at 27807; Kestrel is level 24 at 336,913 XP
at 26810; Praelarran is level 12 at 65,942 XP at checkpoint 28499, with the
level-12 warrior continuation active; and
Corararfen is level 6 at 17,020 XP at checkpoint 27756. Velnor is level 6 at
15,255 XP at checkpoint 27762, and Fenanallor is level 4 at 7,771 XP at
checkpoint 27767. Runs
9109-9110 requested a live Suturb retrieve quest, then exposed that
the non-kill quest executor followed a raw shortest path into Old Marsh room
8310. Source mobile 8306, an aggressive level-12 huge hairy beast, attacked;
Aeloria fled at 193/218 HP, lost 232 XP, and recovered without dying. The
repaired preflight and executor now apply the source-safe route gate to
retrieve, object, and hoard targets. Real source validation rejects room 8310
for level 18, and the full offline suite passes 2,994 tests; direct live proof
of the repaired quest route awaits the next generated non-kill quest.
Runs 9112-9113 completed Dorrik's provision-funding loop without XP change,
death, or loss. Runs 9114-9120 added 1,304 XP to Praelarran through four
source-matched warrior kills, with no loss or death. Runs 9121-9123 completed
Corararfen's outfit, return-home, and daycare-ring recovery maintenance without
a field loss. Runs 9124-9125 added 109 XP to Velnor through a source-matched
Sorbus kill and trained cure light; the later fanatic route was absent.
Aeloria's next bounded invocation retained her Shadow Keep crowd gate without
combat. Runs 9128-9129 completed Fenanallor's ranger starter/Mud School
boundary, added 227 XP from two boars and two wolves, and trained shoot. Run
9130 advanced Praelarran from level 8 to 9 through a 192-XP Illusionist kill,
recovering a shimmering key and 21 maximum HP without loss or death. Run 9132
then added 835 XP from three source-matched level-9 kills, recovered a
disarmed broadsword and 14 items, and trained enhanced damage plus unarmed
combat knowledge for stun. Run 9137 then added 681 XP from the on-duty guard
and cook, recovered eight items including a rearmed broadsword, and returned
safely without loss or death. Runs 9141-9142 then added 200 XP to Dorrik from
the large hobgoblin and blonde dwarf, recovered a purple sanctuary potion, and
used it on the second route; he returned full without loss or death. Run 9147
then added 494 XP from two more guard/cook kills, recovered ten items and a
disarmed broadsword, and returned full without loss or death. Run 9153 then
added 485 XP from the source-matched on-duty guard and cook after a trivial
drunk contact, recovered seven items, and returned full; runs 9154-9155
completed loot sale and return-home maintenance. Resume migration synchronized
Praelarran's stale SQLite `to level 10` label to `Praelarran to HERO` without
creating a new campaign or checkpoint.
Runs 9156 and 9158-9159 added 1,367 XP through armed-guard, bull, and
guard/cook kills; run 9157 recorded a safe Moria absence. Runs 9160-9161
completed return-home and Plains North/Sorbus absence maintenance. Runs
9162-9169 added a further 1,023 XP through a Shire bull and three guard/cook
rotations without death or XP loss. Run 9187 then crossed Praelarran from
level 9 to 10 with 519 XP and 23 maximum HP. Run 9191 visited the level-10
warrior trainer, read the guildmaster plan, trained enhanced damage to 44%, and
added 640 XP from the patrolling guard and cook's boy after recovering a
disarmed broadsword. Runs 9194-9195 trained Praelarran's enhanced damage to
49% and unarmed combat knowledge to 41% toward the source-backed stun
prerequisite. Runs 9198-9218 added 4,456 XP through source-matched warrior
kills and safe Moria, Shire, and Circus rotations; run 9219 sold recovered
loot, runs 9220-9221 recorded clean absences, and run 9222 added 828 XP from
three source-matched kills. Praelarran is safely checkpointed at level 10 with
45,728 XP and no loss or death. Runs 9225-9226 then added 1,142 XP through an
armed-guard kill and three source-matched Fleshmonger kills; run 9227 sold the
loot, and runs 9228-9229 recorded clean Cult absences. Praelarran is now safely
checkpointed at level 10 with 46,870 XP and no loss or death. This is
representative level-10 class/training evidence, not subclass or HERO proof.
Run 9239 then crossed Praelarran from level 10 to 11 with 771 XP from two
source-matched guard kills and 22 maximum HP, returning safely without loss or
death. Runs 9242-9243 continued the warrior trainer route, raising enhanced
damage to 53%; run 9244 added 507 XP and trained unarmed combat knowledge to
47% toward the 60% stun gateway. Runs 9247-9249 included a clean Circus probe,
flight maintenance, and a further 255-XP small-troll kill. Run 9250 then added
582 XP from two source-matched guards and recovered 12 items. Praelarran is
safely checkpointed at level 11 with 50,804 XP and no loss or death. This is
level-11 continuation and training evidence, not subclass or HERO proof. Runs
9254, 9259, and 9262 added 536 XP from three small-troll kills; runs 9255 and
9263 added 1,220 XP from four source-matched guards, with safe Moria and Shire
absence probes between them. Praelarran is now safely checkpointed at level 11
with 52,560 XP and no loss or death. This remains level-11 continuation
evidence, not subclass or HERO proof. Run 9267 added 230 XP from an armed
guard. Runs 9268 and 9280 added 864 XP from source-matched patrolling guards;
run 9272 added 202 XP and run 9278 added 186 XP from small trolls. Run 9274
killed a patrolling guard for 395 XP, withdrew at the 32% health floor, and paid
a 99-XP flee cost for a net 296 XP; the exact source policy is now bounded by
its one-loss protection rule. Run 9277 added 302 XP from an armed guard, while
run 9279 recorded a clean Circus absence. Praelarran is safely checkpointed at
level 11 with 54,650 XP and no death. This remains level-11 continuation
evidence, not subclass or HERO proof. Runs 9283-9284 added 468 objective XP from
an armed guard and a small troll. Run 9285 recorded a clean Strongman's Tent
no-target result; run 9286 added 401 XP from a patrolling guard; runs 9287-9288
completed loot sale and return-home maintenance. Run 9289 added 178 XP from an
armed guard and used its body part as food; runs 9290-9291 completed flight and
return-home maintenance. Run 9292 added 178 XP from a small troll, run 9293
recorded 10 incidental XP from a drunk while its Circus target was unavailable,
and run 9294 added 342 XP from a patrolling guard after recovering a weapon
dropped by a live disarm. Praelarran is now level 11 at 56,227 XP at checkpoint
28226, with no loss or death in this continuation batch. This remains level-11
continuation evidence, not subclass or HERO proof.
Runs 9355-9356 recorded safe Daycare and Cult absences. Run 9357 added 271 XP
from an on-duty guard; run 9358 added 175 XP from a Shire bull after skipping a
crowded circuit; and runs 9359-9360 completed flight and return-home
maintenance. Runs 9361, 9364, and 9367 recorded clean New Ofcol absences; run
9362 added 228 XP from an on-duty guard; and run 9363 recorded a clean Circus
absence. Run 9368 added 174 XP from an armed guard. Run 9369 then exposed an
unexpected dwarf-forest combat, costing 116 XP on withdrawal without death; the
exact route is now bounded by the current-reboot loss policy. Praelarran is now
level 12 at 63,783 XP at checkpoint 28435, safe and with no death. This remains
level-12 continuation evidence, not subclass or HERO proof.
Run 9370 then killed the source-matched Aruncus the Druid for 477 XP, recovered
one item, and returned safely at full health. Praelarran is now level 12 at
64,260 XP at checkpoint 28438. This remains level-12 continuation evidence,
not subclass or HERO proof.
Run 9371 then killed the source-matched armed guard for 207 XP, used a recovered
body part as food, and returned safely at full health. Praelarran is now level
12 at 64,467 XP at checkpoint 28441. This remains level-12 continuation
evidence, not subclass or HERO proof.
Run 9373 then killed the source-matched on-duty guard at VNUM 9401 for 224 XP,
recovered one patched leather jerkin, and returned safely at full health. The
separate VNUM 9406 route remains bounded after its 116-XP loss. Praelarran is
now level 12 at 64,691 XP at checkpoint 28447. This remains level-12
continuation evidence, not subclass or HERO proof.
Run 9374 then killed another source-matched armed guard for 190 XP and returned
safely at full health without loss or death. Praelarran is now level 12 at
64,881 XP at checkpoint 28451. This remains level-12 continuation evidence,
not subclass or HERO proof.
Run 9375 recorded a safe Dragon Cult no-target result with no combat or XP
change, advancing the resumable checkpoint to 28454. This remains level-12
continuation evidence, not subclass or HERO proof.
Run 9376 recorded a safe New Ofcol no-target result with no combat or XP change,
advancing the resumable checkpoint to 28457. This remains level-12 continuation
evidence, not subclass or HERO proof.
Run 9377 then killed the source-matched on-duty guard at VNUM 9401 for 222 XP
and returned safely at full health without loss or death. Praelarran is now
level 12 at 65,103 XP at checkpoint 28460. This remains level-12 continuation
evidence, not subclass or HERO proof.
Run 9378 recorded another safe Circus no-target result with no combat or XP
change, advancing the resumable checkpoint to 28463. This remains level-12
continuation evidence, not subclass or HERO proof.
Run 9379 recorded a safe Daycare no-target result with no combat or XP change,
advancing the resumable checkpoint to 28466. This remains level-12 continuation
evidence, not subclass or HERO proof.
Run 9380 then killed the source-matched on-duty guard for 286 XP, recovered a
notched scimitar after a live disarm, and returned safely at full health without
loss or death. Praelarran is now level 12 at 65,389 XP at checkpoint 28469. This
remains level-12 continuation evidence, not subclass or HERO proof.
Run 9381 recorded a safe Drow no-target result with no combat or XP change,
advancing the resumable checkpoint to 28473. This remains level-12 continuation
evidence, not subclass or HERO proof.
Run 9382 recorded a bounded New Ofcol squire search with no target, combat, or
XP change, advancing the resumable checkpoint to 28476. This remains level-12
continuation evidence, not subclass or HERO proof.
Run 9383 then killed the source-matched on-duty guard for 334 XP and returned
safely at full health without loss or death. Praelarran is now level 12 at
65,723 XP at checkpoint 28479. This remains level-12 continuation evidence,
not subclass or HERO proof.
Run 9384 recorded a safe Dragon Cult no-target result with no combat or XP
change, advancing the resumable checkpoint to 28482. This remains level-12
continuation evidence, not subclass or HERO proof.
Run 9385 recorded a bounded New Ofcol Jack search with no target, combat, or XP
change, advancing the resumable checkpoint to 28485. This remains level-12
continuation evidence, not subclass or HERO proof.
Run 9386 then killed the source-matched on-duty guard for 219 XP and returned
safely at full health without loss or death; its practice audit also retried
cleanly after interleaved room output. Praelarran is now level 12 at 65,942 XP
at checkpoint 28488. This remains level-12 continuation evidence, not subclass
or HERO proof.
Run 9387 recorded a clean Circus no-target result with no combat or XP change,
advancing the resumable checkpoint to 28491. This remains level-12 continuation
evidence, not subclass or HERO proof.
Run 9388 stopped safely before field travel because the character had no carry
capacity for one essential pie after reaching General Supplies. There was no
combat or XP change; checkpoint 28494 preserves the resource-maintenance
boundary for the next invocation. This remains level-12 continuation evidence,
not subclass or HERO proof.
Run 9389 repeated that capacity boundary during a return-home resupply segment,
again without combat or XP change. The return-home handoff now defers the
purchase instead of failing when one pie cannot fit; the full offline suite
passes 2,993 tests, and live revalidation remains the next step. This remains
level-12 continuation evidence, not subclass or HERO proof.
Run 9390 then exposed the asynchronous variant: the server rejected buy-one
pie repeatedly after the quantity backoff, and the progress watchdog stopped
the run without combat or XP change at checkpoint 28499. A decision-time guard
now exits the shop after the final rejection; the full offline suite passes
2,994 tests and live revalidation remains the next step. This remains level-12
continuation evidence, not subclass or HERO proof.
Runs 9297-9298 added 490 objective XP from an armed guard and a small troll;
run 9299 recorded a clean Strongman's Tent no-target result; and run 9300 added
281 XP from a patrolling guard with six items recovered. Praelarran is now
level 11 at 56,998 XP at checkpoint 28243, with no loss or death in these
follow-up segments. This remains level-11 continuation evidence, not subclass
or HERO proof.
Runs 9303-9306 added 789 objective XP and 20 incidental XP through armed-guard,
small-troll, Circus absence, and patrolling-guard routes. Runs 9307-9308
completed loot sale and return-home maintenance; run 9309 added 202 XP from an
armed guard; run 9310 refreshed flight; run 9311 recorded a 10-XP incidental
drunk contact while the Cult fanatic was unavailable. Run 9312 then added 442
XP from a patrolling guard and crossed Praelarran from level 11 to 12, raising
maximum health from 246 to 270. Praelarran is now level 12 at 58,461 XP at
checkpoint 28275 with no loss or death. This is level-12 continuation evidence,
not subclass or HERO proof.
Runs 9313-9316 completed loot sale, healer return, outfit, and return-home
maintenance; a 10-XP transit contact occurred during the sale without an
objective target, loss, or death. Run 9317 then killed the source-matched
on-duty guard for 241 XP, recovered six items, and preserved an enhanced-damage
practice when the trainer's current proficiency cap rejected another attempt.
Praelarran is now level 12 at 58,712 XP at checkpoint 28287, with no loss or
death. This remains level-12 continuation evidence, not subclass or HERO proof.
Runs 9318-9319 completed loot sale and healer return. Run 9320 accepted second
attack at 40% toward its 50% cap; run 9321 refreshed flight. Run 9322 completed
a bounded Moria search with only 20 incidental XP and no objective kill, while
run 9323 raised unarmed combat knowledge to 50% toward the 60% stun gateway.
Run 9324 then killed the patrolling guard and on-duty guard for 583 objective
XP, recovering 11 items. Praelarran is now level 12 at 59,315 XP at checkpoint
28306 with no loss or death. This remains level-12 continuation evidence, not
subclass or HERO proof. Runs 9325-9326 completed loot sale and healer return.
Run 9327 added 192 XP from an armed guard; run 9328 recorded the Dragon Cult
fanatic absent; and run 9329 reached the Shire route and skipped a crowded
circuit target before combat. Run 9330 then killed the patrolling guard and
on-duty guard for 477 objective XP, recovering 11 items. Praelarran is now
level 12 at 59,984 XP at checkpoint 28323 with no loss or death. This remains
level-12 continuation evidence, not subclass or HERO proof.
Run 9340 recorded a clean Circus absence. Run 9341 added 543 XP from a
patrolling guard and on-duty guard; run 9342 recorded a 10-XP incidental drunk
contact during loot sale; and run 9344 added 182 XP from an armed guard. Run
9345 recorded another clean Circus absence, while run 9346 added 269 XP from a
patrolling guard and skipped a crowded second target. Run 9349 added 318 XP
from an on-duty guard; run 9352 added 280 XP from an armed guard; run 9353
recorded a clean Circus absence; and run 9354 added 284 XP from an on-duty
guard. Intervening maintenance returned safely. Praelarran is now level 12 at
63,051 XP at checkpoint 28390 with no loss or death. This remains level-12
continuation evidence, not subclass or HERO proof.
Runs 9333 and 9338 recorded clean Circus and Dragon Cult absences. Run 9334
added 214 XP from an armed guard; run 9335 added 738 XP from a patrolling guard
and on-duty guard after recovering a disarmed broadsword; runs 9336-9337
completed loot sale and healer return. Run 9339 added 229 XP from another armed
guard. Praelarran is now level 12 at 61,165 XP at checkpoint 28347 with no loss
or death. This remains level-12 continuation evidence, not subclass or HERO
proof.
Praelarran's latest progression pair recorded the Dragon Cult fanatic
absent, then killed source mobile 112 for 238 objective XP after a 20-XP
incidental Olog contact, recovering five items and returning safely. The next
rotation killed the source-matched Illusionist and Ivan for 250 objective XP,
recovered two keys, and safely recorded an absent fanatic route. The next
Foundry loop added 141 XP, recovered five items, and sold three for 41 coins.
The subsequent Ultima route then killed source mobile 2405 for 269 objective
XP and two items after a safe consider, reached a 71.7% HP low point, and
returned through healer recovery. A subsequent Circus absence and Magic Shop
maintenance bought and verified a light blue flight potion without XP change.
Follow-up
maintenance sold three items for 26 coins and completed healer sleep; no
objective kill was forced when the next segment was maintenance-only.
Dorrik remains behind a current-reboot crowd
gate, Kestrel behind a fame-service cooldown, and Aeloria behind the quest
cooldown created by the bounded retrieve probe. The full offline suite passes
2,992 tests. These are
continuation and liveness records, not level-25, subclass, or HERO progression
proof. Campaign preflight now records the exact source teacher identity for all
18 legal subclass combinations. The source-ranked handoff for audited caster
specials is now class-independent: sanctuary as the opener requires two
verified purple potions or persisted `cure blindness`, including for warriors,
clerics, and thieves. A bounded Dorrik invocation preserved the current-reboot
Tentusks crowd gate, so live reserve-branch proof remains pending.
Run 8859 exposed a stale below-band ordering loop in the Mirror Realm
watchman route; runs 8860-8863 completed safe healer return and maintenance,
and run 8864 live-validated immediate recall after the watchman's below-band
`consider`. Run 8865 recorded the paired gardener target absent. The watchman
route is now on its current-reboot crowd cooldown, and the bounded reconnect
produced no metadata-only checkpoint churn after startup repair. This is
repair and liveness evidence, not level-25, subclass, or HERO progression
proof.
The initialized source selector correctly leaves Aeloria unavailable
when current-reboot absence, crowd, and trailing no-progress evidence exhaust
the safe pool; explicit `--retry-stalled` does not override those live gates.
These are liveness and frontier-wait records, not level-18, level-25, subclass, or HERO
progression proof. The source quest audit now also selects a bounded exact
shovel acquisition from Graveyard room 3613 when a buried-hoard quest lacks
an ITEM_DIGGER, while retaining the live object/hoard completion gate. Dynamic
quest source preflight now records a ready/unavailable checkpoint before any
Telnet action when the exact source route or VNUM is absent. Runs
8444-8448 are selector-rotation and liveness evidence,
not level-18, subclass, or HERO progression proof.

Runs 8450-8452 then resumed the canonical human cleric matrix workspace:
Corararfen killed three Mud School mobs for 161 XP, completed a safe return-home
segment, then killed two wild boars and a wolf for 196 XP. Checkpoint 25959 is
alive at level 5 and 11,196 XP in healer room 3054. This is early cleric
continuation evidence, not level-10 or HERO proof.
The following bounded batch completed run 8453 with 573 XP from seven Mud
School kills, run 8454's daycare-ring maintenance, and run 8455 with 224 XP
from four more kills. Checkpoint 25962 is alive at level 5 and 11,769 XP.
Runs 8457-8486 then continued the canonical cleric rotation, adding 2,395 net
XP through source-backed Mud School kills, safe healer returns, and daycare
maintenance. Empty arena circuits were checkpointed for reset rather than
forced. Run 8486 crossed level 6; checkpoint 25993 is alive at 14,164 XP in
healer room 3054. This is live early-cleric progression evidence, not level-10
or HERO proof.
Runs 8491-8494 then added 355 net XP to Corararfen after the level-6
transition and checkpointed an empty Mud School arena safely at 26001. Runs
8495-8500 advanced Velnor through three source-backed Mud School batches for
708 net XP, crossing him to level 5 at checkpoint 26007. Both campaigns remain
alive in healer room 3054; this is early-cleric progression evidence, not
level-10 or HERO proof.
Runs 8501-8510 then added 579 net XP to Velnor through recovery, daycare-ring
maintenance, and six further Mud School kills. He remains alive in healer room
3054 at checkpoint 26017; this is still early-cleric progression evidence, not
level-10 or HERO proof.

The latest live continuation leaves Aeloria at level 17 and 153,607 XP, Dorrik
at level 24 and 360,891 XP, Kestrel at level 24 and 336,913 XP, Corararfen at
level 6 and 15,098 XP, Velnor at level 5 and 12,175 XP, Praelarran at level 6
and 15,078 XP, and Fenanallor at level 4 and 7,565 XP. Aeloria is safely
checkpointed in healer room 3054 at 209/209 HP, 593/593 mana, and 310/310
movement, with one verified purple reserve in the combat pouch and no active
campaign worker. Runs 8418-8427 continued the bounded level-17 source
frontier: Bardoosh was live-consider rejected, Bird Spider mobile 6310 yielded
369 objective XP, a later zero-XP Bird Spider result exposed a repeatability
bug, and Hood, Shadow Keep, and Wyvern produced absence or crowd evidence.
The selector now carries a separate best source reward across a new
level-specific policy only when that policy has no current negative result,
and refuses to reopen a current low-reward result. The source revision is
`7996722bc43508cc3773c48f8d79e3d07d68e5e4`, checkpoint 25861 was the pre-probe
safe state, and the full offline suite passes 2,830 tests. Runs 8428-8434 then
completed two productive research probes plus bounded absence, crowd, flight,
and reset-wait rotations; checkpoint 25886 is the current safe state. Run 8428
then opened the
bounded dynamic-wanderer research fallback, reached source mobile 11518 in
Highland room 11536, used the mage familiar opener, and killed the Keeper of
the Tower for 638 objective XP before returning safely to healer room 3054 at
checkpoint 25863. Run 8429 repeated the same route, killed the Keeper of the
Tower for 477 objective XP, and returned safely at checkpoint 25866. Runs
8425-8427 found
source undead soldiers present in Shadow Keep but crowded, then found the
Wyvern centaur-chief and Hood gang-leader targets absent; all returned safely
with no XP change or death. A reset-aware continuation also stopped safely.
Reset-wait selection now ignores source-hunt cooldowns whose level suffix is
older than the character's current level, so historical level-15 evidence
cannot block or describe Aeloria's level-17 frontier. This is bounded level-17
continuation and selector evidence with two live productive research probes, not
level-18, subclass, or HERO proof. The one-shot repeatability allowance is
consumed; promotion still requires the remaining research criteria. Run 8430
then recorded the Hood gang-leader target absent and returned safely at
checkpoint 25869. Run 8431 then recorded a crowded Shadow Keep route without
combat or XP change, and run 8432 killed source mobile 11512 in Highland room
11530 for 492 objective XP before returning safely at checkpoint 25877. Run
8433 completed flight maintenance without XP change; run 8434 found the Wyvern
target absent. The bounded reset retry then found no fresh current-band route
and left checkpoint 25886 safe in the healer room.
When clean current-band candidates are exhausted, the selector may now expose
one source-bounded dynamic-wanderer research probe after the no-progress
threshold. It has no combat special, stays within the current level/HP bound,
and keeps the exact isolated endpoint gate; a live wanderer remains a crowd
safe-stop. The first repeatability result was also safe and productive; the
one-shot same-reboot allowance is consumed, and the route remains research-status
until its promotion criteria are met.
Runs 8394-8395 record the
Moria post-objective cleanup loss, its ordering repair, and a safe source-ranked
absence rotation; no death occurred. Runs 8386-8389 then added Shadow Keep
crowd, absence, below-band consider, and live giant-eel evidence. Run 8389
exposed a selector/executor source-fuzz mismatch; the audited lightning-breath
path now shares a +2 ceiling and direct-HP/sanctuary bound, and a policy-specific
startup migration repairs the stale result even after historical segment
reconciliation restores transient evidence. The full offline suite passes
2,817 tests. Checkpoints 25630-25641 verified the repair and a bounded reset
wait; direct eel combat revalidation remains open because subsequent live
selection was crowd/absence gated. Runs
7732-7739 added 593 XP, completed safe absence and return-home checkpoints, and
reconciled one operator-terminated segment without false progress. Campaign
segment 7391 (run 7822) then reopened the independent source-ranked frontier
during sanctuary cooldown, killed source mobile 3142 for 354 objective XP, and
returned safely without clearing the existing protection marker. Segments
7392-7393 (runs 7823-7824) then recorded a live Haon Dor absence and a bounded
Ambush no-kill result, both with safe healer returns and no XP change. Runs 7495
and 7496 completed bounded Aeloria and Kestrel probes and returned both safely
to healer room 3054 without objective XP. Run 7498 then selected the
source-matched Midgaard secretary for 315 objective XP and returned Aeloria
safely. Run 7825 then classified source-audited noncombat target specials as
safe progression candidates, killed source mobile 3142 for 446 objective XP,
and returned Aeloria full to healer room 3054. Dorrik remains safe while
timeout, protection, and current-reboot cooldown evidence blocks his remaining
routes. Run 7826 repaired a legacy false failure for Kestrel's successful
sanctuary acquisition, reacquired and pouch-verified potion VNUM 4050, and
returned her safely to healer room 3054 with 100 incidental carrier XP. The
full offline suite passes 2,746 tests. Runs 7515-7574 continued
Aeloria's generic level-15 rotation and
crossed the level-16 boundary. Runs 7583-7585 then proved the revision-aware
mage training audit and added 888 objective XP with safe healer returns. Run
7617 added the potion and death-recovery evidence described above. Runs
7628-7669 continued bounded current-band rotation, maintenance, and recovery
evidence. Runs 7638, 7653, 7658, and 7665 repeatedly live-validated the
source-backed outdoor mage familiar opener: Aeloria summoned and grouped the
level-15 pony, ordered it to exact Bardoosh instances, earned 177, 233, 191,
and 191 objective XP, and returned safely each time. On
2026-08-17, the bounded
rotation's Dorrik checkpoint 22973 retained the Eastern Desert crowd boundary
after a bounded reconnect without XP change; Aeloria checkpoint 22979 completed
buy-flight-potion maintenance and Kestrel checkpoint 22985 completed the
follow-up return-home recovery at full HP and mana. All three remained safe in
healer room 3054. The earlier full offline suite passed 2,678 tests, including the
source-proven non-combat-special protection distinction described above. These
are continuation checkpoints, not level-25, subclass, or HERO proof.
route reconnect settled checkpoint 22805 and retained the explicit same-reboot
route retirement; a second reconnect returned the same checkpoint without
another metadata-only repair. Startup repair now preserves explicit retry
intent and authoritative current objective evidence across reconnects. The
full offline suite passes 2,678 tests. Kestrel run 7376 then exposed a real
sanctuary-expiry death at 220/334 HP against a level-30 moose at 410/535 HP;
7377 completed Purgatory recovery and 7379 reacquired the Moria sanctuary
reserve, returning full to healer room 3054. Run 7380 then deferred the fame
route as crowded without another fight. The protection-loss repair now
uses the live health matchup before another attack. Run 7384 then killed the
source-matched Midgaard secretary for 494 objective XP and returned Aeloria
safely; runs 7385-7388 completed bounded absence and maintenance work without
false XP. Runs 7389-7390 then validated explicit retry-stalled rotation: the
young-boy route recorded live absence, the independent mirror guardian route
recorded a live crowd, and both returned Dorrik safely without XP change. Runs
The follow-up safety check closed the remaining retry bypass. Checkpoints
22948-22954 retained Dorrik's Eastern Desert crowd result at cooldown 3 and
created no duplicate field segment or XP claim; the campaign suite passes 818
tests and the complete offline suite passes 2,678 tests. This is selector-
integrity evidence, not progression or HERO completion evidence.
7351 and 7367 added 90 objective XP
each through the generic
source-ranked executor. The runner now retains the full bounded same-reboot
no-progress history and skips crowd-exhausted reset waits. Runs 7369-7372
bounded Kestrel's negative-fame recovery: the priced flight potion was refused
by the Magic Shop, a retry met a wandering-drunk route block, Circus withdrew
at the 39% health floor after using sanctuary, and Mirror Realm recalled before
combat without a sanctuary reserve. Explicit service refusal is now a hard shop
boundary; fame routes require a verified sanctuary reserve, and a flight-only
fallback cannot reopen the refused shop. Run
7373 then resumed Kestrel through the source food reserve route, acquired exact
object VNUM 5219, and returned full without XP change, combat, or another shop
attempt. Aeloria checkpoint 22766 and Dorrik checkpoint 22769 both recorded
crowded current-band rooms and deferred safely for area reset. This is bounded
continuation evidence, not a HERO completion claim.
7104 added 1,852 objective XP for Dorrik before his reboot-local source frontier
exhausted. Aeloria run 7112 added 475 objective XP in Gremlin Lair and run 7121
added 600 objective XP from a source-matched Bird Spider. Run 7123 exposed a
liquidation interruption that fought a city drunk and caused a net 138-XP loss;
the utility dispatcher now flees before below-band transit combat, with
regression coverage. Run 7126 then recorded 108 incidental XP before a shared
health-floor withdrawal and safe healer return; no objective kill was
confirmed. Kestrel run 7128 then added 90 verified XP from the large hobgoblin,
recovered purple sanctuary, and returned full after applying recovery gear. The
full offline suite passes 2,656 tests. Run 7133 then recorded an 83-XP loss
and a 23% health-floor withdrawal on the Gizmo route; no death or objective
kill occurred, and the exact policy is now quarantined. Run 7136 then added
375 verified XP from the source-matched huge python and returned Aeloria full
after chill-touch combat. Run 7137 then added 743 verified XP from Bardoosh,
recovered a dagger after disarm, and returned full with four drops recorded.
Run 7141 then added 321 verified XP from the large hobgoblin, recovered purple
sanctuary, and returned full. Run 7142 then used sanctuary, killed the
below-band Midget for 30 non-objective XP, and recovered its purse and coins
before a full healer return. Run 7145 then added 283 verified XP from the large
hobgoblin, recovered purple sanctuary, and returned at full health. Run 7149
then added 490 verified XP from Bardoosh, maintained source-verified armor
protection, and returned full with three drops. Run 7155 then withdrew from
Bardoosh at 56% health and cost 40 XP without a kill; it was the exact policy's
second loss and is now quarantined. Run 7156 exposed that the Forest's
80-stop source circuit could exceed the profile's 250-command cap; the runner
now derives a finite 613-command allowance and keeps a hard boundary. The old
failed checkpoint reconciled to ready. Runs 7157-7162 completed safe return,
absence, funding, and flight maintenance. Runs 7163, 7166, and 7169 added
574, 280, and 371 objective XP from Queen Wasp kills; runs through 7172
otherwise returned safely without false progress. Runs 7220-7229 then exposed
and repaired ambiguous selector-less gear identity and stale-room ordering in
the fixed rearm route. The repaired sequence validated a Queen Wasp kill for
374 objective XP, a Giant Kodiak bear kill for 280 XP, and Aeloria's level-15
transition. Run 7231 added 528 objective XP from Bardoosh; runs 7230 and
7232-7235 completed bounded level-15 and maintenance rotations safely. Run 7236
then killed Aruncus the Druid for 413 objective XP and returned safely to healer
room 3054. Runs 7237-7270 then added 5,354 objective XP from Bardoosh, Bird
Spider, and Queen Wasp kills, offset by two source-policy hard-floor withdrawals
totaling 190 XP and 20 incidental XP. Run 7283 exposed a randomized Great
Eastern Desert DFS cycle; run 7284 recovered Aeloria through Limbo and the
protected corpse after a death that cost 3,623 XP. The repaired walker now
preserves its visited graph, the Eastern Desert route is quarantined for this
reboot, and Aeloria is 12,917 XP short of level 16. Runs 7285 and 7286 then
added 624 objective XP from the Miden-nir goblin leader and Shire receptionist;
the first also recorded 167 incidental XP loss after an unapproved attacker
joined. Aeloria is now 12,460 XP short of level 16. Run 7289 then killed a
second source-matched Shire receptionist for 397 objective XP without an XP loss
or death. Aeloria is now 12,063 XP short of level 16. Run 7291 was a residual
selector-regression invocation after the timeout marker was cleared; it produced
only 50 incidental XP from a transit dark dwarf and no Eastern Desert objective
kill. Run 7292 restored the marker from history and selected liquidation instead,
leaving that route quarantined for this reboot. Aeloria is now 12,013 XP short
of level 16. Run 7294 then killed another source-matched Shire receptionist for
431 objective XP without an XP loss or death. Run 7298 added a further 368-XP
receptionist kill after addressing hunger during recovery. Aeloria is now 11,214
XP short of level 16. Run 7301 added a further 369-XP receptionist kill and
acquired a usable body part. Aeloria is now 10,845 XP short of level 16. Run
7304 added a further 414-XP receptionist kill without an XP loss or death.
Aeloria is now 10,431 XP short of level 16. Run 7310 then added a 272-XP
receptionist kill without an XP loss or death. Aeloria is now 10,159 XP short of
level 16. Run 7313 then added a further 333-XP receptionist kill without an XP
loss or death; Aeloria is now 9,826 XP short of level 16. Run 7321 then added a
further 368-XP receptionist kill without an XP loss or death; Aeloria is now
8,844 XP short of level 16. Run 7324 then withdrew from an incidental fight at
the hard health floor, recording 167 XP loss, 58 net incidental XP, and no
objective kill before a safe healer return. Aeloria is now 8,786 XP short of
level 16, and the exact route is quarantined for rotation. Run 7328 then
produced five Eastern Desert kills for 380 XP, including successful dropped-weapon
recovery after a disarm; Aeloria returned safely at 187/193 HP and was 8,406
XP short of level 16. Run 7332 added only a 50-XP dark-dwarf contact, and run
7338 repeated the 146-room Forest absence without combat. The retry-marker guard
now keeps that absent route closed after minimum-value contact; the full offline
suite passes 2,662 tests. Run 7343 then added a clean 358-XP young dragon
wormkin kill; Aeloria is now 7,998 XP short of level 16. Run 7344 then added a
clean 233-XP huge python kill; Aeloria is now 7,765 XP short of level 16. Live
CLI campaigns now
default to a 180-second segment cap plus 45 seconds of cleanup grace. Current
live source decisions use revision `7996722`. The selector
now counts exact-policy XP losses, quarantines after the second loss, and waits
for an area reset when protection recovery has no independent route. The older
continuation details below are historical:
Runs 6994-7004 added productive
Moria, Mirror Realm, and Canyon evidence; run 7004 supplied 1,256 objective XP
before consuming the purple sanctuary reserve. Runs 7008 and 7014 then added
886 and 799 objective XP from source-matched Mirror Realm watchmen. Run 7013
withdrew from Dwarven Homestead at the explicit 27% health floor after 179
incidental XP and installed a newer protection marker without death or XP loss.
Runs 7009, 7010, 7011, and 7015 completed liquidation, healer movement
recovery, flight maintenance, and a safe zero-kill probe. The Moria recovery
circuit now uses one reset-room stop plus eight bounded source-room edges; this
is regression-verified. Run 7019 live-validated the circuit through rooms 4064
and 4063, acquired the purple sanctuary potion, and placed it in the combat
pouch before returning full. Run 7022 added 683 objective XP from the Tentusks
treant and consumed the reserve; run 7023 reacquired a purple potion through
Moria with 90 incidental XP. Runs 7024-7026 safely rotated protected Mirror
routes without forcing absent targets. Run 7027 then killed the source-matched
Dwarven Home host for 1,938 objective XP and returned full with the sanctuary
reserve intact. Run 7029 reacquired the reserve with 90 incidental XP; run 7030
skipped a wandering Mirror Realm gardener outside the source-safe relocation
graph without forcing combat. Run 7031 withdrew from the source-matched Solace
Sergeant at Arms at the shared 30% health floor after sanctuary expired,
recording a 385-XP flee loss; run 7032 restored full healer recovery. Run 7033
reacquired the sanctuary reserve with 100 objective XP. Run 7034 safely skipped
a crowded Mirror Realm target without combat. Run 7035 then killed the
source-matched Dwarven Home host for 1,520 objective XP without consuming the
reserve. Run 7038 exposed a same-name Grove race between wandering mobile VNUMs
8900 and 8901 and caused a 385-XP flee loss before GMCP identity arrived. The
pre-combat source-graph ambiguity guard now skips such a stop before `consider`
or `kill`; run 7039 restored the sanctuary reserve with 140 total XP, and run
7040 added 1,465 objective XP from the Dwarven Home host. Runs 7041 and 7042
then recorded a safe Mirror rotation and live-validated the pre-combat
same-name VNUM guard at Grove room 8906 without combat or XP loss; run 7043
added 1,410 objective XP from the Dwarven Home host. Run 7049 then exposed a
source-casting status gap: mobile 9202 (`spec_cast_cleric`) blinded Dorrik after
sanctuary expired and caused a 39-XP net loss before a safe healer return. The
runner now requires a verified cure-blindness route before such a hunt, retains
two matching potions when sanctuary and cure blindness share an item, and uses
the cure before fleeing when blindness is active. Runs 7050 and 7051 completed
safe sanctuary and Dwarven Home rotations without reaching the target, so this
repair is offline-verified but not yet live-triggered. Run 7055 then live-tested
the source-matched Weeping Willow at a perfect consider; the shared 35% health
floor fired after it reduced Dorrik to 137/542 HP, producing a 213-XP net loss
after the flee charge. Runs 7056-7059 recovered and rotated through Dwarven Home,
Shire, flight, and Tentusks without another loss. Run 7060 then reopened the
Dwarven Home host route; Dorrik withdrew at 124/542 HP after earning 602
damage-credit XP, paying the 385-XP flee cost for a 217-XP net gain without an
objective kill. He returned safely to healer room 3054 at 480/542 HP, full mana
and movement, with hunger 4 and thirst 42. Runs 7063-7066 then exercised the
protected frontier: run 7063 killed the source-matched New Ofcol teller for
1,119 objective XP with a 20-XP below-band interruption; run 7064 withdrew from
the Drow weapons master at 43/542 HP and lost 385 XP after 23 damage-credit XP.
Run 7065 consumed sanctuary before the Canyon `spec_cast_cleric` cyclops, but
its harm spell outlasted the aura and forced a flee at 80/542 HP for a 117-XP
net loss. Audited special routes that fail after sanctuary are now quarantined
for the reboot. Run 7066 reacquired and pouch-stowed the purple reserve from
the source-matched large hobgoblin for 100 objective XP and returned full to
the healer. Runs 7081 and 7092 repeated the Drow weapons master route under
its two-mobile crowd: the first lost 210 XP, and the sanctuary-protected retry
lost 265 XP at the 39% health floor. The exact route is quarantined for this
reboot. Run 7083 hit the 180-second segment boundary during a deferred Mirror
Realm search and run 7084 returned Dorrik safely; the starter now clears stale
crowd and locator waits before its runtime return boundary. Runs 7085-7091
completed flight, New Ofcol, Moria, and bounded absence maintenance. Run 7095
then killed the source-matched New Ofcol teller for 934 objective XP and
returned full to healer room 3054 at 358,980 XP. The full offline suite passes
2,648 tests. Run
6987 exposed a
held earthquake staff on the otherwise noncombat priest of Thalos, so source
ranking now rejects unevaluated spell-bearing scrolls, wands, and staves. Runs
6948-6950 then completed a
bounded generic continuation: run 6949 killed the source-matched Mirror Realm
watchman for 873 XP, while runs 6948 and 6950 correctly withdrew from crowded
circuits without forcing combat. All three returned safely with no death or XP
loss. Runs 6951-6960 then added 1,988 aggregate XP, including a 636-XP
Mirror Realm watchman and a 1,352-XP Kerofk route with 742 objective XP plus
610 incidental XP; absent and crowded targets were skipped without XP loss.
Run 6963 exposed a timed sleeping-recovery watchdog gap during flight
maintenance: after one health score, the policy suppressed its prompt gate
while waiting for the affect to expire. The starter now reopens that gate when
the scheduled health check is due; the full offline suite passes 2,636 tests,
and run 6964 live-validated the repair by buying and activating flight with no
XP loss. Runs 6967 and 6968 then exposed the same Abyss return hazard twice,
while run 6971 live-validated the repaired return graph. Runs 6981 and 6982
recorded bounded 149-XP and 16-XP net losses; the finisher now permits one
source-admitted final action against a target up to one level higher at 35%
health or less when the observed one-hit reserve is covered. Run 6987 exposed
a held earthquake staff on the otherwise noncombat priest of Thalos, and
source ranking now rejects unevaluated spell-bearing scrolls, wands, and staves.
The full offline suite passes 2,636 tests. Runs 6965 and 6966 completed a
bounded Abyss absence and 460 incidental XP from three low-risk Kerofk
interruptions, returning full to healer room 3054. Objective and incidental
XP remain separate. Runs 6921 and 6923 supplied
802 and 1,367 objective XP. Run 6926 exposed a live endpoint-gate bug when a
level-19 Goblin Caves Sentry was attacked at the level-24 useful-XP floor
despite being recorded below-band and non-objective. The starter now withdraws
before such an endpoint attack, retaining explicit resource and required-loot
exceptions; run 6927 live-validated the repair. Run 6936 exposed a second
admission gap: a source-audited gas-breath special above the live level ceiling
caused a 385-XP flee from the level-25 Green Dragon. Combat-special admission
now applies that ceiling before launch. Run 6938 then killed the level-19 Swamp
Wraith for 587 XP but paid a 385-XP flee penalty when three source-known
level-16 Mistlings joined the Mahn-Tor no-recall return; the repaired return
branch keeps that bounded below-band interruption in combat. Run 6940 added
170 XP on the Eastern Desert worm route and returned safely. Runs 6941 and 6942
then added 933 and 1,177 XP through the Kerofk gravedigger and Old Thalos
mayor, respectively, with safe healer returns and no XP loss. The full offline
suite passes 2,632 tests. The earlier level-23 evidence follows.

The preceding level-23 continuation left Dorrik at level 23 and 326,057 XP and
Aeloria at level 14 and 88,949 XP, both full in healer room 3054. Runs 6784,
6786, 6788, 6790, 6795, 6800, and 6801 supplied productive source-ranked
kills; runs 6800 and 6801 added 875 and 857 objective XP through the Kerofk
gravedigger and Old Treant routes. Runs 6785, 6787, 6789, and 6794 recorded
bounded Mirror Realm zero-kill or absence results without forced combat; run
6793 refreshed flight, run 6796 restored hunger from 2 to 39, and runs 6797-6799
completed liquidation, safe rejection of a non-corporeal funding target, and
restock. The next Mirror Realm segment was stopped after an outer watchdog
stall and recovered as ready with explicit interruption evidence; run 6803
returned Dorrik safely home without XP loss. Run 6804 then added 891 objective
XP from the same Kerofk gravedigger route, and run 6805 completed liquidation
and full healer recovery in room 3054. Runs 6807 and 6812 then added 784 and
534 objective XP through the generic Old Treant route, while runs 6806, 6809,
6810, 6811, and 6813 recorded bounded zero-kill rotations and run 6808 refreshed
flight. Run 6814 withdrew from a Shudde-M'ell interruption after the live level
gate, lost 354 XP, fed hunger from 5 to 40, and quarantined the exact Plains
North policy for three same-reboot segments. Run 6815 then killed the
source-matched Swamp Wraith in the alternate Mahn-Tor circuit for 1,060
objective XP, and run 6816 restored full movement at healer room 3054. Run
6817 then completed another bounded Mirror Realm zero-kill probe without XP
change. Runs 6818 and 6827 added 726 and 637 objective XP through the generic
Old Treant route. Run 6824 then killed the source-matched Swamp Wraith for 884
objective XP, but exposed two avoidable 354-XP flee penalties from source-known
below-band Mistlings in the Mahn-Tor no-recall return maze. The return policy
now permits a safe lower-band combat interruption only in the registered
Mahn-Tor return rooms when all enemies are source-known below-band and health
and provision gates pass; it then resumes the live-GMCP exit graph. The
focused policy tests pass 38 and the full offline suite passes 2,629 tests.
The exact post-repair live branch remains untriggered, so this closes a
regression while preserving the evidence boundary. Runs 6832 and 6835 then
added 1,053 and 1,083 XP through the generic gravedigger route; run 6833 added
894 XP from Old Treant, and run 6834 rejected a crowded Mirror route without
XP. Dorrik is now 9,361 XP short of level 24 and full on HP, mana, and movement
in healer room 3054. Runs 6836 and 6839 were bounded zero-XP maintenance or
Mirror rotations; run 6837 added 608 XP from Old Treant, run 6838 withdrew at
the health floor with 208 net XP, and run 6840 added 150 XP from the Arachnos
guardian. Hunger is now 2, so provision recovery is the next gate before
another field launch. Run 6841 then restored hunger to 38 while adding 716 XP
from Old Treant. Runs 6842-6845 recorded bounded Mirror, Crystal, Sentinel, and
Abyss results without forced targets; run 6846 refreshed flight. Run 6847
retained a repeated no-policy-decision watchdog failure, and run 6848
reconciled it successfully. Before run 6851, Dorrik was at 319,871 XP with
hunger 24. Run 6851 then added 687 XP from Old Treant, and run 6852 recorded another
bounded Mirror zero-kill result. Dorrik was 6,992 XP short of level 24 before
run 6854 added 646 XP from Old Treant. Run 6855 found Nessy's child but
withdrew when the adult Nessy joined, paying the 354-XP flee cost; the exact
Highland policy was quarantined and the healer return completed safely. Dorrik
is now 6,389 XP short of level 24. Run 6856 then added 1,325 XP from the
source-matched Maid; run 6857 sold four items for 291 coins; and run 6858
recorded another bounded Mirror zero-kill result. Dorrik was then at 322,486
XP, 5,064 short of level 24. Runs 6878-6881 then validated the source-route
scheduler repair: one empty Mirror attempt was excluded from the next
selection, flight maintenance ran, and Old Treant supplied 633 objective XP
before the marker cleared. Run 6883 collected the source-matched sanctuary
potion from the large hobgoblin; run 6887 added 760 objective XP from Old
Treant. Run 6895 withdrew from Dwarven Homestead at the health floor, losing
189 XP without dying and quarantining that exact route; run 6896 recorded a
bounded Mirror absence after rotation. Dorrik is now level 23 at 326,057 XP,
1,493 short of level 24, full in healer room 3054. The campaign now carries a
one-attempt source-route exclusion after a normal no-progress segment;
productive XP clears it, and it is scheduling evidence rather than
progression proof. The
campaign now carries a persisted
deferred-practice marker for a practice type whose current trainer has no
immediately useful listed skill; legitimate newly unlocked damage gateways can
still reopen that type. The combat reserve now has a narrow
finish window for one last action against a nearly defeated lower/equal-level
opponent when the character is healthier than the opponent and above one known
incoming-hit reserve. Explicit stop floors still win, and that branch remains
without live-specific proof. The level-20 shifter trainer now uses a bounded
source-derived Kerofk locator across 62 reachable rooms, with stale-result
recovery covered offline. Live level-20 and level-30 subclass evidence remain
the next generic frontier; none of this proves HERO.

The live mage/thief/warrior matrix proves level 10. Representative long-running
campaigns currently anchor Aeloria at level 14 and 88,949 XP, Dorrik at level
23 and 297,605 XP, and Kestrel at level 24 and 363,995 XP. Run 6708 acquired
a purple sanctuary potion through the generic high-band Moria recovery circuit
and returned Dorrik to healer room 3054 at full HP and mana; the protection
marker for the original failed hunt remains pending for a protected retry.
Runs 6709 through 6716 then recorded a crowded teller withdrawal, a bounded
audited-special withdrawal, an additional 653-XP Highland attempt interrupted
by an unapproved attacker, and safe healer recovery. The next executable
frontier must reacquire sanctuary before retrying the exact failed hunt. Runs
6717 through 6721 then added a productive Arikasbab circuit worth 1,628 XP,
including a 1,338-XP Maid kill, and completed safe Dorrik returns. The next
sanctuary selection remained on a reboot-local cooldown after one bounded
retry. Aeloria runs 6722 and 6723 completed safe no-objective Ambush and Plains
North probes; Kestrel runs 6724 and 6725 completed safe reserve and Mirror
Realm probes without XP. The next frontier remains class-aware continuation,
not a HERO completion claim.
Dorrik's run 5246
crossed level 14 after runs 5231 through 5245 executed generic source-ranked
circuits without manual target steering; run 5247 completed the post-level
recovery at healer room 3054; runs 5249 and 5251 then validated both Ambush
reset rooms at level 14. Run 5261 also recorded a live non-viable target and
skipped it without combat, while run 5262 refreshed flight. Runs 5269 and
5271 re-established the Dwarven Nobleman route after the reboot, and the
bounded kill probe withdrew at the 15% floor without a kill. Runs 5274, 5280,
5284, and 5295 then proved productive Plains North, Fleshmonger, and Ambush
alternatives, with run 5302 completing a successful Shire continuation and
leaving the campaign at 91,544 XP in healer room 3054. Run 5307 then exposed
an armed Bardoosh critical-hit death after two incidental low-XP goblin
interruptions. Purgatory recovery and healer restoration succeeded, but the
death penalty left the current checkpoint at 87,820 XP. Runs 5308 through 5310
then resumed with productive duty and ranger alternatives, refreshed flight,
recovered a long bow, and returned Dorrik to healer room 3054 at 88,279 XP.
Runs 5335 through 5337 then completed a 743-XP Aruncus kill and safe daycare/
Moria maintenance; runs 5338 and 5339 completed two safe Wraith probes and
left Dorrik at 94,264 XP after run 5344 added a 919-XP Aruncus kill; runs 5345
and 5346 found Wraith targets absent and retained incidental goblin XP outside
objective attribution. Run 5353 then reached the Dwarven Homestead through the
Miden'nir bridge and recorded a positive nobleman consider without attacking;
the level-6 bridge goblin was resolved by live VNUM 3501 after delayed GMCP.
Runs 5354 through 5358 reconciled the standalone probe and rotated past
crowded or absent candidates. Run 5359 added a 413-XP ranger kill in 141.8
seconds; runs 5373, 5376, 5378, and 5383 then added 332, 337, 533, and 389
XP. Run 5360 completed maintenance, and the bounded 5385-5386 rotation added
334 XP and crossed Dorrik to level 15; run 5391 then added 956 XP from a
wandering Undead Soldier. The live checkpoint
preserved two practices and
subclass `none`, so the requested knight subclass is not treated as active
before the level-30 handoff. Aeloria is waiting on an explicit reboot-scoped sanctuary recovery
cooldown, while Kestrel's negative-fame campaign is waiting on its source-ranked
cure-critical reserve; both waits are distinguished from unrelated crowd
evidence. The missing proof is a fresh uninterrupted creation-to-HERO run,
generic class/subclass executable coverage after level 30, and the Mudlet/VM
visible-client boundary. Source-ranked combat now carries a source-derived
one-hit critical reserve: ordinary aggressive thresholds remain active, but a
critical capable of killing the character raises only that target's withdrawal
floor. This preserves productive high-XP candidates and bounded probe paths
without treating death as acceptable routine throughput. Safe multi-target
circuits are now ranked by risk-adjusted source reward per travel step, so a
wandering singleton cannot hide a productive fixed-reset circuit. A selector
retry audit also prevents an expired absence probe or low-value ground fallback
from hiding a measured same-reboot route. Explicit objective kills below 50 XP
remain contact evidence only, and wandering kills are keyed by tagged source
identity rather than the selected room. A fresh candidate may displace a
productive repeat only when its risk-adjusted reward per travel step is at
least 25% stronger. An aggressive requested target remains a scored risk-pool
option behind the normal source, live-consider, crowd, health, protection, and
return gates. Run 5403 then validated the selected throughput route: Aruncus
the Druid (mobile 300, room 323) yielded 505 objective XP and returned Dorrik
to healer room 3054 at full health and movement. Run 5405 repeated Bardoosh
for 351 objective XP plus one incidental 70-XP goblin kill, returning at full
HP and 264/290 movement. Run 5406 repeated Aruncus for 462 objective XP and
returned at full HP and 269/290 movement. Run 5407 then followed the fanatical
goblin guard by live source VNUM 4516 after it wandered into room 4522; Dorrik
earned 264 XP, absorbed a critical hit, and returned safely at 228/322 HP
before healer recovery. The runtime now records this kind of wandering kill by
exact source identity even when the registered room stop has a different display
name. Run 5408 then accepted the measured Bardoosh repeat: mobile 4515 yielded
460 objective XP and a wandering goblin added 70 incidental XP. Dorrik returned
without death or flee at full 322/322 HP and 279/290 movement, reaching 102,994
XP. This is productive risk/reward evidence rather than a safe-return-only
result. Runs 5409 through 5412 then demonstrated the measured rotation and
maintenance boundary: Aruncus yielded 421 XP, Shargugh was absent after its
cooldown, and flight/provision upkeep completed without being counted as XP.
Run 5413 reached Bardoosh and its SQLite event trail records a 60-XP goblin
interruption plus a 460-XP Bardoosh kill, but the worker was stopped after its
transcript stayed empty; run 5414 recovered at healer room 3054. Keep the
interrupted segment failed until kill metadata is reconciled, and close both
its segment and unbound run row during recovery. Run 5415 confirmed both Wraith
rooms absent after one incidental 60-XP goblin interruption. Run 5416 then
reopened the fanatical guard by source VNUM 4516, earned 257 objective XP, and
returned at full HP and 281/290 movement. Run 5417 proved that completed kill
rows now commit during live reads rather than waiting for graceful cleanup.
Run 5418 exposed a throughput loss when a source `spec_guard` bystander kept a
good-aligned character waiting until Aruncus wandered away. Source-special
profiles now reach the runtime crowd gate: noncombat and combat-only bystanders
cannot inflate the crowd, while `spec_guard` requires alignment 300 or higher
and one non-hostile retry. Run 5419 then earned 286 objective and 70 incidental
XP, persisted all three kill rows before cleanup, and returned Dorrik fully
recovered at 104,728 XP. Confirmed objective kills suppress stale absence
metadata. Runs 5420 and 5421 then exposed a separate accounting boundary: their
objectives were absent, but incidental transit kills added 60 and 10 aggregate
XP. The source-ranked no-progress streak and live policy reward cache now use
objective-kill evidence instead of raw XP, matching restart reconstruction.
Run 5425 selected the measured mobile-4516 repeat, earned 303 objective XP, and
returned fully recovered at 105,161 XP. The immediate
executable work is the level-14-to-30
frontier and the class-aware training/equipment gates it exposes; only after the
level-30 subclass handoff is executable should the project spend effort on the
higher-band routes and visible Mudlet/VM layer.

The policy lifecycle is deliberately two-stage. A registered `research` policy
is the bounded knowledge-acquisition step. Once it records a current-reboot
outcome, the campaign can hand off to the generic source-ranked executor; that
executor selects a source mobile and reset room at runtime and records its own
policy ID, consider result, objective kill, XP, and safe return. Therefore
`show-policy-coverage` describes registered policy readiness, while campaign
segments and objective-kill records describe actual live execution. Neither
view may be used alone to claim HERO coverage.

The source provenance is also layered. The current read-only DD4 checkout is
`7996722`. The bundled prerequisite and training snapshots remain pinned to
`f703daa`, and the fallback character catalog to `0482387`; a source-sensitive
change must record both the live checkout revision and the snapshot revision
used by the decision.

The conversation streamer is part of the audit path, not a decision engine.
`DEVELOPMENT_CONVERSATION.txt` is configured for both `USER` and Codex records;
live delivery has confirmed the source offset reaches the file end with no
duplicate queued record. Required-loot policy must likewise remain source
specific: the Day Care room-6605 reset loads one ring onto its last old doll,
while room 6603 is only a wandering observation point. Static carrier stops
declare their source reset room and suppress both interception and normal target
evaluation at route waypoints.

Outbound source interceptions have a separate route invariant. A rejected
target seen on an official fastwalk may contribute below-band or crowd
evidence, but it must restore the pre-intercept stop context before the
relative source circuit continues. The official route endpoint is authoritative
for the next stop; otherwise a later VNUM can be mistaken for a directly
adjacent live exit. Run 5102 exposed this with Moria rooms 4011, 4022, and
4010, and the starter regression now covers the repaired state transition.

## Policy Boundaries

- **Shared safety:** hunger, thirst, health, mana, movement, disarmament,
  encumbrance, death recovery, escape, saving, and quitting.
- **World knowledge:** routes, rooms, mobs, drops, shops, resets, and observed
  reboot-scoped facts.
- **Archetype policy:** usable abilities, practice prerequisites, combat
  resources, stat priorities, and equipment restrictions.
- **Level-band policy:** suitable targets, protection requirements, kill limits,
  recovery points, and fallback actions.
- **Execution adapter:** direct Telnet/GMCP is primary. The Mudlet shared-file
  bridge consumes the same decisions and emits the same GMCP/text observations;
  VM and profile lifecycle automation remains a separate validation boundary.

## Representative Proof

`matrices/level-10.yaml` defines the first proof matrix: mage, thief, and
warrior characters with different races, genders, and subclass targets. The
matrix runner advances them round-robin, persists each campaign independently,
continues after an isolated failure, and succeeds only when all three reach
level 10. Live evidence, not configuration or unit tests alone, is required to
claim that proof complete.

Use `python -m dd4tester matrix-coverage <matrix.yaml>` to inspect both
declared source-legal pair coverage and persisted target-level evidence. The
two counts are intentionally separate: a generated entry is not validation
until its campaign checkpoint records the matrix target level.

`matrices/level-10-all-race-class.yaml` is the checked-in source-legal
validation boundary. It currently declares all 225 race/class pairs and uses
two cosmetic sexes without multiplying progression requirements. The smaller
`matrices/level-10.yaml` remains the quick three-character representative loop;
neither matrix is live proof until its campaigns reach the declared target.
