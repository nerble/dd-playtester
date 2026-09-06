# Autonomous Playtesting Roadmap

The target is an autonomous character that can progress from character creation
to HERO level 100, explain its experience in humanlike language, and run either
headlessly or through a visible Mudlet client in a Windows virtual machine.

## Delivery Principles

- Use direct Telnet and GMCP runs to develop and repeat game behavior quickly.
- Keep observations, state, decisions, commands, and commentary as separate layers.
- Preserve every raw input beside derived data so a failed decision can be replayed.
- Make campaign runs resumable; a level-100 test must survive process and VM restarts.
- Keep AI optional until deterministic behavior and safety boundaries are measurable.

## Latest Continuation

**Runtime reassessment (2026-09-06):** See
`docs/REASSESSMENT_2026-09-06.md` for the measured costs, revised health
budget, and proof boundaries. The latest live frontier is Dorrik, a level-25
Dwarf Warrior at 380,076 XP and checkpoint 38105, safely full in healer room
3054 with flight active. Runs 12398-12405 covered bounded funding,
liquidation, and flight maintenance. Run 12406 found a Fleshmonger senior-guard
companion with a level-15 `greet_prog` that can initiate `mpkill`, costing 419
XP; run 12411 found a reachable Arachnos Guardian interrupting transit, also
costing 419 XP. Run 12412 then reached an isolated Solace Secretary whose live
585-HP instance produced only 95 damage against 80 received during the bounded
probe, costing 324 XP on withdrawal. All three exact policies are now
quarantined before ordinary selection. Revision 197 requires a source-backed
damage budget and incoming-exchange proof before another post-loss unprotected
HP-fuzz probe. The next live step is fresh level-25 progression or a bounded
sanctuary/resource handoff; no level-26, subclass, or HERO proof is implied.

Revision 198 narrows one remaining false positive in the emergency no-sanctuary
fallback. Source-ranked route aggressors are no longer rejected solely because
they carry `ACT_AGGRESSIVE`: a source-proven mobile at least ten levels below
the character, with no attack program and only a typed non-combat special such
as `spec_fido`, may be treated as incidental transit noise. Near-band mobiles,
program attackers, unsafe specials, and missing or malformed source metadata
remain fail-closed. This improves frontier availability without weakening the
live consider, crowd, damage-window, health, resource, or healer-return gates;
it is not live progression proof.

The connection-loss recovery patch now persists an explicit homeward marker
and clears stale field target/crowd observations before the next policy
selection. The full offline suite passes 3,647 tests.

The Astra implementation slice now treats DD4 sanctuary duration `0` as live
for the current fight but not as durable protection for a new outbound route.
Once a field exchange has measured both damage streams, the damage-window
probe may extend the conservative twelve-action source horizon from the
character's actual HP reserve, while retaining the damage-trade, HP-floor, and
healer-return gates. The full offline suite passes 3,647 tests. The next
executable slice is fresh level-25 progression toward level 26, followed by
class trainer and subclass validation; no level-26, subclass, or HERO proof is
implied.

Static template coverage is not executable or live progression proof. Continue
current class frontiers, measure net XP including maintenance and losses, and
validate trainer/subclass handoffs before adding distant level bands.

The latest Kestrel continuation is the active engineering anchor: checkpoint
37990, level 24, 333,533 XP, safely in healer room 3054 after a bounded resume
following run 12363. Runs
12355 and 12359 acquired source food at the live Haon endpoint; run 12356 rejected a
below-band Old Treant without combat; run 12358 reached the Solace Secretary,
which passed live `consider` but outlasted the thief's audited action budget
and cost 385 XP. The selector now closes unprotected HP-fuzz probes after any
current-level reboot loss, and the live controller rejects a fuzzy target whose
GMCP HP exceeds its source action budget. The runner now opens a dynamic
source-ranked frontier at level 21 and above after the registered band is
exhausted, without bypassing its safety gates. Run 12360 live-validated that
handoff through a bounded Kerofk gravedigger route; it returned from Ambush at
the field boundary with no XP change or objective kill. Runs 12361-12362 then
refreshed Kestrel's source-verified food reserve and movement without changing
level or XP. The latest resume stopped at the existing sanctuary-recovery
cooldown without opening combat. These repairs still
need fresh post-reboot target validation and do not constitute level-25 or HERO proof.

Policy revision 193 now makes the executable source-ranked frontier lead
ordinary fresh research from level 10 onward. A named research probe remains
the fallback when no safe current-band candidate is available, while resource,
training, quest, subclass, equipment, funding, flight, and recovery transitions
remain mandatory. This is the reusable progression path for arbitrary
race/class campaigns; selection evidence is not progression proof.

Revision 193 separates fixed-reset transit risk from the ordinary five-level
XP cutoff. An aggressive source mobile within the ten-level transit-risk band
blocks a route even when it is too low-level to farm, and long class-trainer
routes are preflighted from healer room 3054 before departure. A blocked route
defers training with its exact source hazard instead of discovering it after a
flee loss.

Revision 195 extends the same ten-level gate to source-reachable aggressive
wanderers and refuses below-band room companions with attack programs. It also
keeps retryable liquidation ahead of generic funding selection, so fresh loot
is sold before another field hunt. The only transit-risk exception is the
explicitly bounded outdoor Mage/Witch familiar probe; ordinary source-ranked
warrior and thief routes remain blocked.

Revision 196 closes the post-loss plain-target escape unless the source-ranked
combat model proves that the player's audited damage budget covers the target
HP ceiling and expected incoming exchange. This retains the aggressive
single-probe behavior for fresh evidence while preventing a low incoming peak
from reopening an unprotected route after a same-level XP loss.

A read-only level-25 source audit found no fresh warrior candidate that passes
that budget and the route-hazard gates. The remaining plain unprotected
Secretary is the exact policy quarantined by run 12412; every other
current-band option requires sanctuary or carries a source-identified transit
hazard. The campaign must wait for a new reboot or acquire a verified
sanctuary reserve before the next live combat attempt.

The Astra reassessment also fixed source consistency at the HERO boundary.
New HERO workspaces now persist the resolved area directory alongside the
manifest and campaign configuration; the campaign runner scopes every gear,
teacher, route, resource, and candidate loader to that directory. Resumes keep
the original source pin, so a later upstream pull cannot silently mix source
revisions into an existing evidence trail.

The Astra selector repair also blocks an ordinary source-ranked candidate when
its audited HP ceiling or combat path requires sanctuary but the checkpoint has
no executable sanctuary reserve. The runner no longer spends a bounded segment
travelling to a target that the field executor is guaranteed to reject before
combat. Explicit bounded-peak retries, sanctuary-resource specials, and
audited protection fallbacks remain available through their separate gates.
Revision 194 applies the same boundary to an unprotected HP-fuzz durability
probe during active protection recovery, so a small source peak cannot reopen
a fuzzy target outside the plain-target fallback.

The familiar-backed mage slice closes the matching planner/executor gap. When
live practice shows `summon familiar`, a plain unarmed target is source-ranked
as outdoors and non-underwater, and the combined player-plus-pony damage
budget fits the source HP ceiling and mana reserve, the field stop persists
`require_familiar`. The starter summons, groups, and orders the pony before
combat, withdraws it near 45% target health to preserve player XP, and flees
if the familiar is lost early. Run 12365 live-validated this route for 633 XP;
the result is continuation evidence, not HERO proof.

**Shared combat contract (2026-09-06):** Direct combat action ordering now
lives in `dd4tester/combat_capabilities.py` and is consumed by both source
damage estimation and live `StarterPolicy` dispatch. Base psionic `agitation`
is source-formula-backed, positively-observed at runtime, and marked automated
in training priorities. Subclass actions whose lifecycle or formula is still
incomplete remain explicitly readiness-visible but estimate-ineligible. The
next implementation slices should extend this contract one audited action at
a time, with source, training, runtime, and focused tests landing together.
The first follow-on slice now covers brawler `second punch`: DD4 emits it as
an automatic side effect of `punch`, so the estimator weights its source damage
only from positive live proficiency while the controller continues issuing one
ordinary `punch` command.
The shared registry now also exposes the already-implemented control-only
`disarm` path for thief, warrior, ranger, and vampire identities. It remains
estimate-ineligible, but its source reference and automated training status now
match the live controller and the class prerequisite catalog.

The source parser now retains each mobile prototype's DD4 rank and applies the
`mob.c` rank-table HP multiplier to candidate estimates. Candidate inspection
also reports the rank, making elite, boss, and world targets visibly distinct
from ordinary source mobiles before a live route is admitted.

The next physical slice now covers source-backed `headbutt` for warrior,
brawler, and barbarian identities. The estimator mirrors DD4's level-scaled
first and optional second hit, includes the automatic weapon cycle, and admits
the action only when parsed body-form flags prove a non-huge target has a head.
The starter repeats the exact no-argument `headbutt` command only for one fresh
source target in live combat, with positive observed proficiency and no head
trauma. Unknown or legacy anatomy remains unassessed; this is capability
evidence, not live progression or HERO proof.

Thief opening estimates now also include DD4's automatic `double backstab`
branch after a successful backstab, using only positive observed proficiency
and preserving the one-shot opening boundary. The thief training priorities
now schedule that automatic branch after its source prerequisites.

The next thief slice registers source-defined `trip` and `dirt kick` as
control-only capabilities. Each action is dispatched at most once per exact
source target after live body-form, sector, fighting-position, and GMCP enemy
gates pass. Because DD4's target-state and sector rules are not yet represented
in the damage estimator, these actions remain estimate-ineligible; this is
executable control coverage, not live progression proof.

The vampire combat slice now covers `suck` and the bounded `lunge` opener. The
estimator mirrors `skill.c:do_suck`, `fight.c:do_lunge`, and
`fight.c:one_hit`, including weapon or unarmed fallback, the half-damage and
rage branches, observed skill success, and `double lunge` probability. The
live bridge issues lunge only for an exact source target whose fresh enemy
snapshot is unique, full-health, and not already fighting; a rejection falls
back once to ordinary combat. This remains bounded combat-planning evidence:
live organic-target admission, vampire forms, and light/blood lifecycle still
need their own source and controller coverage.

The warrior physical slice now gives source-audited `stun` a bounded opener
controller. It requires positive live proficiency, an exact source VNUM,
one fresh full-health enemy record, and a blunt weapon; after the attempt it
switches back to the source-selected primary weapon and starts ordinary
combat. Rejections, missing heads, oversized targets, and absent targets are
handled once without a retry loop. The shared registry now rejects subclass
actions when their declared base class does not match the character identity,
closing a stale-checkpoint path to source-illegal dispatch.

The martial-artist slice adds the corresponding `kansetsu` gate. DD4 uses it
to break an armed opponent's weapon arm, so the starter requires a positive
live proficiency, level-30 martial-artist identity, exact source VNUM, fresh
single-target room evidence, and source-armed target metadata. It consumes one
attempt per fight and accepts the server's rejection or disarm message without
retrying. Its damage remains estimate-ineligible until target weapon state and
the source outcome are represented in the planner.

The body-form provenance slice closes the missing source contract behind these
physical gates. Raw DD4 body bits now survive area parsing and candidate,
checkpoint, and field-stop serialization. Kansetsu requires known usable arms;
thug `smash` requires a known non-huge target and a worn shield. A missing body
line in legacy or synthetic data is preserved as unknown and cannot authorize
either anatomy-dependent action.

The same evidence rule now covers smithy `counterbalance`. A confirmed anvil
command records the exact prepared weapon VNUM in campaign metadata, and the
source estimator adds DD4's `APPLY_BALANCE` extra-attack chance only when that
VNUM matches the currently wielded source object. Skill knowledge alone cannot
inflate a weapon estimate; a replacement or mismatched weapon falls back to
ordinary output. This is reusable planning coverage, not live progression
proof.

Smithy `hurl` now has the corresponding chained-weapon boundary. The source
estimator and between-round starter command are enabled only for the matching
currently wielded weapon after `EGO_ITEM_CHAINED` has been observed in GMCP or
`identify` output. The VNUM survives campaign checkpoints; a learned hurl
percentage, stale marker, or mismatched weapon cannot authorize the action.
Steel/material acquisition, weaponchain preparation, and shieldchain remain
future live-safe automation work.

The current-reboot protection fallback was also recalibrated to the same 80%
source-peak bound used by the unprotected HP-fuzz probe. It now requires the
source lower HP bound to fit the character, while retaining one-loss scope,
95% departure health, distinct-route rotation, live isolation, consider,
damage-window, and second-loss quarantine. This is intended to prevent a
recovery cooldown from freezing an otherwise executable level frontier.
It now also requires the route's typed source hazard metadata to be clear of
aggressive, attack-program, and special mobiles. The live gravedigger attempt
showed why: the rolling rock had no special procedure, but ordinary `fight.c`
combat still disarmed Kestrel. A no-sanctuary recovery allowance cannot treat
that route as a plain target.

**Astra strategy reassessment (2026-09-06):** The full offline suite passes
3,629 tests. Dorrik was level 25 at 379,277 XP and checkpoint 38034 after
runs 12372-12381, safely full in healer room 3054. The sequence recorded two
source-ranked losses, safe expiry handling, a 100-XP sanctuary acquisition,
a 1,619-XP protected Mr. Smithy kill, a safe shop-hazard deferral, and a
second 100-XP reserve acquisition, the corrected -302-XP net result for run
12380, and the repaired checkpoint resume in run 12381. The live damage-window
probe now extends
the conservative twelve-action source horizon only when measured damage and
current HP reserve support the projected exchange; unsafe trades still flee.
Campaign selection treats sanctuary duration 0 as active for the current fight
but not as a durable outbound reserve. Aeloria remains level 18, Praelarran
level 20, and Kestrel level 24; none has subclass or HERO proof.
The next frontier is fresh level-25 progression toward level 26, followed by
class trainer and subclass validation. See
`docs/REASSESSMENT_2026-09-06.md` for the full live ledger and proof rules.

The post-reassessment continuation reached a clean 2,032-XP Secretary kill in
run 12390 and safely rejected a crowded Mr. Smithy room in run 12391. Runs
12392-12393 then bounded a Windows socket failure and a return-home retry while
the MUD stopped accepting port 8888 connections. Run 12394 validated the
return-home repair; runs 12395-12396 completed bounded maintenance, and run
12397 confirmed no new reboot after the single reset wait. The campaign is now
checkpointed at 38072 with Dorrik alive at level 25 and 380,838 XP, full in
healer room 3054. The next executable action is fresh progression after the
area reset; no level-26, subclass, or HERO proof is claimed.

Runs 12398-12405 then covered bounded funding, liquidation, and flight
maintenance. Run 12406 exposed a level-15 `greet_prog` companion in the
Fleshmonger senior-guard room; its `mpkill` path cost 419 XP and is now
quarantined. Run 12411 exposed a separate Arachnos transit loss when the
source-reachable Guardian interrupted the Donjonkeeper route, also costing 419
XP. Run 12412 reached an isolated Solace Secretary, measured only 95 damage
against 80 received on a 585-HP live instance, and cost 324 XP on withdrawal.
Checkpoint 38105 is safe at 380,076 XP. Candidate construction now rejects all
three exact policies before ordinary selection, while the single familiar-backed
Mage/Witch exception remains explicitly bounded and covered by the full 3,647
test suite. Revision 196 also requires source-backed player-output and
incoming-exchange proof before a post-loss unprotected HP-fuzz probe. No
level-26, subclass, or HERO proof is implied.

The direct resource planner now treats source `greet_prog` attackers with a
bounded distinction: deterministic programs reject a route, while one
probabilistic low-band program is checked with `where` at recall and mapped to
the rooms crossed by the source path. The runner fails closed on an absent
locator response and records the result in the segment state. This unblocks
Kestrel's Crystal grain route without weakening live combat or healer-return
gates.

The caster frontier now has a reusable source-output gate. It mirrors audited
single-target spell formulas from `magic.c`, applies an explicit conservative
action budget, source-derived expected incoming rounds, and mana reserve, and
carries the result into field stops. It may open only a bounded live probe; it
never converts source estimates into a kill claim. Aeloria's Secretary probe
is now retained as measured quarantine evidence, while the high-HP worm remains
sanctuary-gated.

The new `autonomy-audit` report validates a requested source-legal
identity, renders its static policy bands, and reports the first unverified
level separately from registered research. Every bundled base class and all 18
subclasses have a static template path; none should be described
as fully proven until a fresh live campaign validates its route, combat, XP,
training, recovery, and (where requested) level-30 subclass handoff. Generic
source-ranked route preparation now reads invisibility from the identity
capability model rather than from a mage-name branch.

The audit now exposes `combat_automation_status` and combines declared base and
subclass automation gaps. `--all-classes` produces the nine-base-class view,
which is useful for choosing the next replay matrix. A practice listing at
`0%` is recorded as known training information but is not treated as an
executable combat capability; opener, mitigation, between-round, and subclass
action dispatch all use the same rule.

The caster admission model carries source-verified direct spells: base psionic
`agitation`, plus necromancer `harm`, druid `wither`, knight `flamestrike`, and
monk `agitation` after subclass transition. A spell is eligible only when the
requested identity owns it; source formulas improve bounded planning but never
replace live evidence.

The output model now also covers existing deterministic physical controllers:
brawler `punch`, martial artist `atemi`, werewolf `wolfbite`/`ravage`, ranger
`shoot` as a one-shot bow opener, warrior/ranger `kick`, learned thief `knife
toss`, learned thief `circle` with a source-identified piercing primary weapon,
and ordinary weapon strikes. A trained
thief's source-matched `backstab` is budgeted once as an opener, never as a
recurring action. The weapon branch requires an observed primary wielded source object
and applies DD4's source
`one_hit`/`multi_hit` formula to its damage dice, live damroll, observed
enhancement percentages, and source-gated follow-up attacks. Learned-percent
actions are weighted by their observed proficiency. Hit chance and temporary
combat state remain live-calibrated; a missing or ambiguous weapon never
becomes a guessed capability. Between-round kick, knife toss, and circle
budgets include the automatic weapon cycle that continues alongside them. The
source-identified ranger bow is resolved from DD4's separate `ranged_weapon`
slot; `shoot`, `second shot`, and `third shot` contribute only to one bounded
opening volley. That intermediate ranger pass passed 3,548 tests; the current
full offline suite passes 3,587 tests. Observed skills that arrive before the
static registry remain checkpoint and audit evidence, but are not dispatched
until a source-audited registry entry exists. The latest lifecycle slice adds
straight-shifter form entry and healer-side restoration. Source-ranked
admission now recognizes DD4's source-created snake fangs (object VNUM 59): a
live snake form is accepted directly, while a normal form checkpoint may
project the fangs only when the same morph, 20% form-skill, and source mana
gates used by the starter are satisfied. The shared readiness report labels
`morph` and `snake form` as setup capabilities rather than direct damage. Later
form selection, live damage calibration, and travel behavior remain open.
Vampire light/blood state and follower or constructed-platform subclasses are
also still pending.

The controller/source contract is now exact for thieves: repeatable knife-toss
actions issue `knife toss <target>`, matching DD4's registered command instead
of the previously incorrect shortened form. `circle` and `backstab` also
require the source-identified primary weapon, matching DD4's `WEAR_WIELD`
lookup. The focused and full suites cover the corrected dispatch path.

The control plane now notices when another stored run has observed a newer
reboot than a character's checkpoint. It schedules one maintenance-only
`world-time-probe` immediately, even for a bounded invocation, so each
character refreshes its own live reboot marker before cooldowns and route
evidence are evaluated. The shared SQLite marker is only a prompt; the live
`time` response remains authoritative.

**XP reconciliation and source-special route hardening (2026-09-05):** The
full offline suite passes 3,427 tests. Praelarran is level 20 at 219,584 XP and
checkpoint 37791, safely in healer room 3054 with 473/464 effective health,
full mana, 333/340 movement, nine silver and fifteen copper, and all observed
wear slots populated. Run
12282 exposed the Sentinel Gap tree-sprite route: an incidental Fewmaster
Toede kill added 110 XP, then the rock crab's `spec_breath_gas` poisoned the
character and a bounded recall cost 270 XP, for a net loss of 160 XP. The
policy is quarantined. The selector now rejects source-identified non-safe
special mobiles as hard route hazards only when their source procedure can
initiate transit combat, steal currency, or is unknown. The source audit now
covers all 62 special names: combat-only procedures can be crossed while no
fight is underway, aggressive carriers remain hazardous, and conditional
guards are safe for an ordinary unflagged character. Target-room combat gates
remain separate. After one bounded area-reset wait, run 12283 retried sanctuary
recovery but found source mobile 4056 blocking the Moria required-loot endpoint;
it returned safely without a potion or progression. Run 12284 selected the
newly unblocked Eastern Desert worm route, completed one objective kill for 585
XP, and returned safely to healer room 3054 without death, flee, or XP loss.
Run 12285 then completed a bounded provision-funding sweep that recorded the
Midget as absent without claiming XP. Run 12286 moved to Katrina the Shepherd,
added 60 XP, and returned safely to the healer. Run 12287 then liquidated the
resulting loot and returned safely with XP unchanged. Run 12288 completed a
source-backed patrolling-guard funding kill for 100 XP, run 12289 liquidated
safely, and run 12290 killed the source-ranked Dwarven giant for 499 XP with a
full healer return. Runs 12291 and 12292 then killed a Dwarven thief for 982 XP
and a Dwarven giant for 535 XP, both with safe healer returns. Run 12293 then
recorded a 320-XP Dwarven Home withdrawal and quarantined that policy; runs
12294 and 12295 recovered 472 and 558 XP from fresh Dwarven giant kills. Run
12296 added 539 objective XP and 30 incidental XP before a safe return; run
12297 completed without an objective kill, and run 12298 completed sanctuary
recovery with 100 XP. Run 12299 quarantined the Goblin Caves Sentry after DD4
reported a 270-XP flee loss and 69 partial combat XP. The GMCP worth packet
recorded the authoritative net result of 219,584 XP, while the old segment
snapshot at 219,314 had subtracted the full loss twice. The observation and
state layers now preserve partial XP explicitly, covered by the full suite.
Run 12300 found the Moria sanctuary endpoint absent and returned safely
without a potion or objective XP. Runs 12301-12305 continued safe funding and
maintenance, adding 100, 60, and 90 XP from source-ranked guard targets; the
intervening sale route remained bounded by the shared shop hazard. Runs
12307-12308 then killed Dwarven giants for 495 and 472 XP. Runs 12309-12311
completed liquidation, flight maintenance, and another safe sanctuary check;
run 12312 rejected the crowded White Stag route without XP. Runs 12313-12314
then added 693 XP from the Arachnos guardian and 609 XP from the Eastern
Desert worm, and run 12316 added another 580 XP from the guardian. Run 12317
rechecked Moria safely but still found the source orc blocking the sanctuary
endpoint. Praelarran is now checkpointed at 37854 with 222,683 XP. This is
current level-20 continuation and safety evidence, not level-21, subclass, or
HERO proof.

The preceding funding rotation remains recorded below: runs 12267, 12269,
12270, and 12271 added 50, 70, 60, and 40 XP while acquiring replacement gear;
the Midget absence was recorded and not replayed. The funding selector keeps
the latest sale amount separate from cumulative proceeds, prefers source-known
coin carriers when flight money is short, and ages a temporary city-shop route
cooldown after productive kills.

The earlier entries below remain historical live evidence; they are retained
to keep the route and policy decisions auditable.

**Consumable-aware gear audit (2026-09-05):** The full offline suite now
passes 3,414 tests. Praelarran is level 20 at 213,579 XP, checkpoint 37554,
safely in healer room 3054 with full health and 323/340 movement, no active
flight, and a current protection-recovery marker. Runs 12185-12189 recovered a
sanctuary potion, restocked, tested an independent Mirror Realm watchman, and rearmed the
warrior's dagger. Run 12190 exposed a real Moria failure boundary: the deep
required-loot search crossed source-reachable aggressive Warrior and Mage
mobiles and lost 768 XP before a safe healer return. The runner now validates
the exact deep route with a strict source no-combat gate; without that proof it
uses only the shallow room-4064 check or returns a bounded safe result. Runs
12191 and 12193 added confirmed Secretary and Dwarven giant kills for 910 and
568 XP; run 12192 rotated safely through Shire without XP. Run 12194 bought
flight at the observed reboot-local price, run 12195 killed the Eastern Desert
worm for 841 objective XP but lost 256 XP to a drider during no-recall return,
and run 12196 liquidated the loot and returned safely. Run 12197 reached the
Solace administration corridor three rooms short of its endpoint at the
deliberately bounded 120-second cap without making a progression claim. Run
12198 then killed the Eastern Desert worm for 767 objective XP and live-validated
the new recovery state: it distinguished the no-recall refusal from a failed
combat recall, exited to room 5007, and recalled without a pursuer, flee, XP
loss, or death. Run 12202 repeated that route, added 20 incidental XP from a
city drunk and 875 objective XP from the worm, and again returned safely. This
does not claim level-20, subclass, or HERO progression. Run 12204 then added
90 incidental XP from a drider, rejected the unsuitable nomad leader after
live `consider`, and returned safely through the repaired route. The next
executable work is another current-band hunt followed by level-20 and subclass
validation. Run 12205 sold the drider dagger, and run 12206 restored flight
with the live 131-copper light-blue potion price before returning to the healer.
Run 12207 then killed The guardian in Arachnos for 1,091 objective XP and
returned safely through the repaired no-recall route. The next executable work
is to close the remaining 811 XP to level 20, then validate the subclass
handoff. Run 12210 retried the worm, earned 426 partial XP, withdrew at 75/440
HP, and paid a 256-XP flee loss before returning safely. The selector must
rotate away from that exhausted route rather than replay it blindly. Run 12211
then killed The guardian for 715 objective XP and returned safely, leaving only
96 XP to level 20. Run 12212 crossed level 20 with a 665-XP Secretary kill;
DD4 awarded 24 hitpoints, 7 mana, 10 movement, 2 physical practices, and 1
intellectual practice. Run 12213 trained strength at the Kerofk Captain, raised
enhanced damage to 61% and unarmed combat knowledge to 59%, and returned with
587 objective XP plus 480 incidental XP from below-band transit mobs. The next
executable work is the level-20 trainer and subclass handoff, followed by an
executable class-aware level-20-to-30 route. Run 12214 killed the Old Treant
for 1,167 objective XP, sacrificed its arm and corpse, and returned safely. The
next executable work is another level-20 field segment using the current
class-aware skill state. Run 12215 restored the light-blue flight reserve, run
12216 completed a bounded Mirror Realm probe without XP, and run 12217 killed
two live Secretaries for 1,841 objective XP before returning safely. The next
executable work is continued level-20 field progression toward level 21. Run
12220 then killed another Old Treant for 1,198 objective XP and returned safely.
Runs 12221 and 12222 completed bounded Mirror Realm and Solace no-kill
rotations without unsafe combat. Run 12223 killed the level-20 giant purple
sand worm for 534 objective XP, recovered a pink potion, and live-validated the
no-recall exit-and-recall path again without flee, death, or XP loss. The next
executable work is continued level-20 progression toward level 21, followed by
fresh trainer and subclass validation; no level-21 or HERO proof is claimed.
Run 12224 completed bounded flight maintenance with no XP change and left the
character safely checkpointed for the next target selection. Run 12225 reached
the Mahn-Tor Old Treant route but encountered an unexpected dark ethereal
knight at the bloody intersection. The bot withdrew at 75/464 HP, received 293
partial XP, paid a 270-XP flee loss, and returned safely; the resulting net gain
was 23 XP. This route is now concrete hazard evidence, not an objective kill.
Run 12226 completed the bounded Moria sanctuary-recovery segment with no XP
change and left a safe healer checkpoint for the next independent target. Run
12227 killed an incidental city drunk for 10 XP and the level-20 giant purple
sand worm for 630 objective XP, recovered a pink potion, and returned safely
through the no-recall boundary without XP loss or death.
Run 12228 completed safely but found the Shadow Keep Undead Soldier route
crowded, including a multi-mobile underwater room, so it did not execute the
exact isolated target stop or claim XP. Run 12229 safely rejected the Crystal
White Stag route after reaching an Ambush clearing with a wounded goblin and
the Forest foothills without finding an isolated target; it claimed no XP. Run
12230 then killed the giant purple sand worm for 589 objective XP and returned
safely through the no-recall boundary without flee, death, or XP loss. Its
potion, wand, and bow drops hit the carrying limit, so the next maintenance
pass must liquidate or discard loot safely. Run 12231 completed a bounded
Mirror Realm young-boy attempt safely without converting the research target
into an isolated kill or claiming XP. Run 12232 killed the giant purple sand
worm for 778 objective XP, then reached the runtime boundary while checking the
healer checkpoint; the kill was reconciled, but the segment failed after
connection-inactivity retries. The safe-healer cleanup predicate now trusts the
live room and enemy state even when the policy combat flag is stale, covered by
the full offline suite. Run 12233 then recovered the character to healer room
3054 at full health but hit a separate silent equipment-audit acknowledgement
boundary; it changed no XP and remains a startup-recovery failure, not a
progression claim. Runs 12234-12235 completed bounded flight-purchase and
healer-recovery attempts; run 12235 confirmed live `where drunk` hazards at
Main Street and Eastern End of Poor Alley, so the shared shop route remains
blocked. Run 12236 safely completed the Mirror Realm watchman research probe,
and run 12237 restocked provisions. Run 12238 killed a source-verified
dwarven thief for 1,043 objective XP; run 12239's Moria sanctuary-recovery
route recorded 90 XP from a large hobgoblin while restoring resources. Run
12240 then encountered the Shadow Keep watchman with sanctuary active, was
disarmed, recovered its sword, and withdrew at 22% health after a bounded
fight, losing 128 XP; that policy is quarantined. Run 12241 safely probed the
Shadow Keep undead-soldier route, and run 12242 completed Moria
sanctuary-recovery with 100 XP, ending at full health and movement in healer
room 3054. Runs 12243-12245 then completed a bounded Moria recovery, selected
the source-ranked Goblin Caves Sentry, and withdrew after sanctuary expired at
34% health following two live disarms; the route lost 270 XP but dealt 287
partial damage XP and is now quarantined. The follow-up rearm bought and
wielded a source-backed dagger and saved in healer room 3054. The current
checkpoint is safe at level 20; no level-21 or HERO progression is claimed.
Runs 12246-12248 then completed a bounded Thain rotation, exposed a funding
route that attacked an armed Mirror Realm young man and lost 270 XP while
earning 214 partial XP, and safely skipped the below-band Circus Midget. The
source audit confirmed that Mirror Realm mobile 19005 carries a knife and
3,280 copper; funding selection now honors the ordinary armed-target sanctuary
gate, with a regression covered by the full suite. The next live funding
candidate is the lower-peak Miden-nir guard; this maintenance route is not
progression evidence.

**Runtime-cap evidence and sanctuary recovery (2026-09-04):** The full
offline suite passes 3,408 tests. Run 12176 exposed a route-return bug in which
a dynamic Shadow Grove hazard caused five repeated flee/recall attempts and a
1,280-XP loss. The starter now recognizes the grove as a randomized no-recall
maze during emergency return and follows live GMCP exits to its stable entrance
instead of issuing doomed recalls. Run 12177 live-validated that return path
without loss or death. Run 12178 completed a safe Solace research probe, and
run 12179 completed one source-matched Solace Lord Doom kill for 1,273 XP
without loss. Run 12180 exposed an armed-target runtime-cap failure: Lord Doom
disarmed the warrior twice and the bounded withdrawal cost 256 XP. The runner
now requires sanctuary for that static hunt, builds cap checkpoints from the
fresh live snapshot, and keeps objective kills scoped to the current segment.
Startup repair also prefers terminal events or durable mob-kill rows over a
stale segment end-state. Run 12181 safely deferred a no-flight worm route, run
12182 stopped at the source-backed shop hazard, and run 12183 recovered a
purple sanctuary potion from the Moria large hobgoblin for 100 XP. Run 12184
found Lord Doom, then safely returned after sanctuary expired; its old 27%
combat floor still cost 256 XP, so armed Lord Doom hunts now use an explicit
40% combat floor while preserving a bounded near-death finishing action.
Praelarran is level 19 at 196,904 XP, checkpoint 37304, safely in healer room
3054 with 260/440 health, 294/330 movement, no active flight, and a current
protection-recovery marker. No level-20, subclass, or HERO proof is implied.

**Capacity-history, bounded-timeout, and endpoint repair (2026-09-04):** A
clean isolated source-ranked target
that reaches a bounded runtime cap with negative XP but remains above 90%
health now receives one exact, source-damage-bounded retry. Startup reconstructs
that entitlement from SQLite, and an older pre-combat sanctuary-abort is
re-armed only when the segment proves that no attack was issued. Run 12157/
segment 11709 exposed a live cursor race against the giant purple sand worm;
run 12158 rotated safely to an independent Solace route. Run 12159 then
exposed an unnecessary 38-room sweep after `where` found a target only in a
source-known room without a safe relocation route; the runner now stops at that
source boundary. Run 12160 safely skipped Haglik after live `consider`, run
12161 completed liquidation, and run 12162 exposed a second endpoint race:
Arachnos Guardian arrived in a source-registered adjacent stop before the
fastwalk cursor advanced, causing a 306-XP escape loss. Run 12163 selected
Dwarven Home, returned safely, and added 90 XP, moving the checkpoint to 37234
without validating Arachnos. Run 12164 found the Lemmings Smithy below the
useful band at its live source stop and returned safely without XP change. It
also observed the new MUD boot `Fri Sep 4 06:19:51 2026`, resetting reboot-local
candidate and item-limit history; checkpoint 37238 is ready. The starter now adopts
an exact live source VNUM in any registered stop, including a field-circuit
future stop, while retaining consider, crowd, damage, resource, and
healer-return gates. Run 12165 then practised enhanced damage with the class
trainer and returned safely. Run 12166 reached the mirror-realm watchman
endpoint, considered live mobile 9983, declined the field gates, and returned
safely without XP change. Run 12167 completed the Crystalmir white-stag probe
with the same safe no-XP outcome. Praelarran is level 19 at 195,116 XP,
checkpoint 37249, in healer room 3054 with full health and move and active
flight. Run 12168 then stopped at the source-backed `where drunk` preflight
instead of crossing Temple Square for a flight purchase; no purchase was
claimed, and checkpoint 37252 is safely recovered. The
repair is offline-validated. Run 12169 marked Haglik below-band after live
`consider` and returned safely; checkpoint 37256 is current. The next work is
a bounded live Arachnos validation. Run 12170 then reached the bounded Solace
Secretary field cap, returned safely without loss, and added 110 incidental XP
without an accepted objective kill. Praelarran is level 19 at 195,226 XP,
checkpoint 37260, in healer room 3054 with full health and move and active
flight. Run 12171 then considered the Dwarven nobleman, classified it
below-band, and returned safely at the runtime boundary without XP change;
checkpoint 37264 is ready. Run 12172 then completed two source-matched Dwarven
giant objective kills for 897 and 832 XP, adding 1,729 XP without loss. Praelarran
is level 19 at 196,955 XP, checkpoint 37268, in healer room 3054 with full
health, 163/330 movement, and no active flight. No level-20, subclass, or HERO
proof is implied. Run 12173 completed the Moria sanctuary-reserve attempt
safely without acquiring the potion; a below-band drunk supplied 10 incidental
XP, not an objective kill, and checkpoint 37271 is ready.
Run 12174 sold the four giant drops through the Leather Shop, leaving 38 silver
and 45 copper and 131/600 carry weight; checkpoint 37274 is safe.
Run 12175 bought flight at the observed 131-copper price; flight is active, the
balance is 29 silver and 4 copper, and checkpoint 37277 is safe.

Earlier in this cycle, the capacity-history repair reopened the Dwarven giant
route after a later objective kill superseded an older no-kill capacity probe;
the reset-aged entitlement was preserved through the maintenance-only
`world-time` probe. The current-reboot sanctuary route remains terminal after
its bounded attempts, so future selection must continue to honor independent
source, live-consider, crowd, route, health, and healer-return gates.

**Protection-loss accounting and Dorrik continuation (2026-09-02):** The
Telnet adapter and StarterBot now hard-bound connection, read, negotiation,
command-write, and close awaits without waiting on cancellation-resistant
tasks. A final `quit` send timeout closes the already-saved session locally
instead of reopening authentication or holding the process. The `--progress`
option reports bounded campaign attempts while durable SQLite evidence remains
authoritative. Run 11364 exposed that partial combat XP could mask a 419-XP
loss with a net-positive segment; the campaign now compares the durable XP-loss
counter as well as net XP and repairs historical segments on startup. Run
11365 then selected sanctuary recovery instead of replaying Highlander, leaving
Dorrik level 25 at 374,233 XP in healer room 3054 at checkpoint 34135. No
character has reached HERO, and no level-25-to-100 progression claim is
implied. The full offline suite now passes 3,290 tests.

**Latest field-risk result (2026-09-02):** Highlander is now quarantined with
`loss_count=2` and a hard-health protection marker. The next bounded invocation
replayed the existing database evidence, refused that route, completed the
sanctuary recovery boundary, and returned without a new loss or death. This is
a confirmed liveness and safety repair, not level-26 or HERO progression proof.

**Healer-origin liquidation hazard repair (2026-09-02):** Live run 11202
exposed a source-scripted level-2 Midgaard drunk (mobile 3064) on Temple
Square: a generic loot sale crossed the room, triggered its `greet_prog`, and
caused an 88-XP flee loss before the campaign safely checkpointed
`segment_utility_abort`. The starter now applies one source-backed preflight to
all healer-origin city-shop liquidations: capable characters cast invisibility
and remain hidden until the shop; other classes locate the drunk with a bounded
`where` check and stop safely if the hazard cannot be classified. Subsequent
reset-enabled and ordinary rotations completed cleanly and advanced Vergalcoror
from 39,832 to 44,592 XP, including a latest reset-enabled batch that added
807 XP after one bounded field-reset wait.
This repairs a liveness and safety blocker, but the character remains level 10
and no subclass or HERO progression proof is claimed.
The full offline suite passes 3,290 tests after the repair and the CLI now
reports each bounded attempt when invoked with `--progress`.

**Kestrel fame boundary (2026-09-02):** A bounded level-24 rotation recorded
100 incidental XP, then preserved a cumulative 385-XP fame-recovery loss and a
later 120-second segment cap while returning Kestrel safely to healer room
3054. The route remains quarantined pending fresh protection/fame evidence;
this is not level-25 or HERO proof.

**Flight-funding ground fallback (2026-09-02):** When a stocked character is
blocked because the current reboot has exhausted safe funding targets for an
affordable flight purchase, the campaign now preflights the independent
source-ranked no-flight frontier and hands it to the normal selector for
persistence and dispatch. Funding markers remain intact for a later reboot,
while the fallback can earn ordinary XP immediately. The campaign and starter
suites pass 2,287 tests, and the full offline suite now passes 3,279. Two
bounded live rotations plus a third continuation completed 36 segments cleanly,
moving Vergalcoror from 36,046 to 39,832 XP and crossing the level-10 threshold
with no death or XP-loss event. This is level-10 continuation evidence, not
subclass or HERO proof.

**Source-ranked movement gate repair (2026-09-01):** The source-ranked
candidate selector now receives the loaded `WorldSource` when applying its
movement gate. A route longer than the current movement pool is admitted only
when the source route planner proves an audited `no_mob` waypoint split; the
field runner then sleeps and resumes each leg under the existing health,
consider, crowd, and healer-return rules. The focused selector tests and full
offline suite pass 3,278 tests. Live run 11074 exercised the split route to the
Kerofk gravedigger, reached the exact endpoint, and correctly rejected its
below-band live `consider` without combat or XP loss. The route repair is live
validated, but it is not level-25 or HERO progression proof.

**Live rotation status (2026-09-01):** Kestrel is safely checkpointed at level
24 and 334,938 XP after runs 11074-11076; the gravedigger route was below-band,
the food reserve was replenished, and the Moria sanctuary carrier was absent.
Aeloria is level 18 and Serevian level 11. All three workers closed cleanly;
the next executable work is to rotate after a new reboot or independent
source-safe target, while preserving the current cooldown and protection
evidence. No character has reached HERO yet.

**Reconnect authentication gate (2026-09-01):** A live bounded run exposed a
race where a quiet recovery check could be sent into DD4's login prompt after
the socket reconnected. The starter now clears authenticated/in-world state on
every close and waits for the expected name/password/entry handshake or an
explicit reconnect banner before resuming healer return or field policy. The
regression and full offline suite pass. Run 11074 also completed a fresh
reconnect-capable field segment without an authentication race; the next
bounded run must still exercise a reconnect during actual combat or recovery.

**Negative-fame frontier and probe repair (2026-09-01):** Kestrel remains level
24 at 334,938 XP and fame -12 in healer room 3054. Run 11061 live-validated the
damage-window accounting against the Mirror Realm moose: the opener was
included, but the target lost only 30 of 949 HP, so the bot withdrew safely
after a 385-XP loss. Runs 11062-11065 completed bounded Moria reserve, food,
sanctuary, and return-home maintenance without recovering another purple
reserve. The cure-critical selector now rejects a carrier whose source reset
can load more than two same-prototype mobiles; run 11066 selected the remaining
two-capacity Moria orc carrier, found its potion absent this reboot, and returned
safely without combat, loss, or death. The selector still keeps unsuitable
targets quarantined and does not fall back to ordinary below-band XP during
negative fame recovery. Campaign tests pass 1,058, the starter suite passes
1,221, and the full offline suite passes 3,272. No level-25, subclass, or HERO
proof is claimed; a genuinely executable fame target is still required.

**Reserve-carrier capacity gate (2026-09-01):** Source-backed cure-critical
and other recovery carriers may use only a one- or two-capacity reset and at
most two reset entries at the endpoint. A source reset with capacity three or
more is excluded even when its live room appears empty, because DD4 can load
same-prototype assistants before the client can establish isolation. The rule
is covered offline and live-validated by run 11066 through the rotated
two-capacity endpoint; the potion's current-reboot absence remains research
evidence rather than a progression claim.

**Bounded unprotected fame recovery (2026-09-01):** Source-ranked fame
recovery now permits a clean, unarmed, one-capacity target without sanctuary
when the source raw peak-round and critical-hit bounds are both strictly below
the character's maximum HP. The exact-target, isolated, live-consider, and
three-sample/12-second damage-window gates remain in force; candidates with
specials, armed targets, route hazards, or any other autonomy rejection remain
excluded, while source-peak-only candidates still require sanctuary. Offline
coverage passes 3,272 tests. Kestrel's current reboot has no executable target
for this branch because the only clean fame candidate, Sosivia, costs 456
ground movement against 380 available; this is reusable policy support, not
live progression evidence.

**Source-audited transit recovery (2026-09-01):** Long source-ranked routes
can now be divided at audited `no_mob` rooms when the full path exceeds the
character's movement pool. The runner recovers before each long leg, preserves
the exact target suffix, and retains the complete outbound path for bounded
return if recall fails. Closed-door commands are reversed on return. This is
covered by offline route-planning and runner regressions; no new live
progression claim is made until Kestrel completes a fresh fame attempt.

**Damage-window baseline repair (2026-09-01):** A fame fight can produce its
first `Char.Enemies` HP snapshot only after the opening backstab or attack. The
starter now starts the bounded probe before that opener and, only when no
pre-opener enemy snapshot existed, uses the first exact target's source/live
`maxhp` as its initial baseline. This preserves the three-sample/12-second and
10-percent gates, includes opening damage in the measurement, and never infers
a full-health baseline from a multiple-enemy snapshot. The regression suite
reproduces the live moose sequence; run 11058 confirmed the resulting failure
was genuine low damage rather than omitted opener damage.

**Source-ranked combat readiness (2026-09-01):** The source candidate ranker
now consumes the durable class and trained-skill state restored by campaign
checkpoints. It records the active starter combat capabilities and applies a
small target-specific tie-breaker for near-band damage actions, armed-target
disarm control, and defensive reserves. This does not change promising,
caution, or reject status, and it cannot bypass live consider, crowd, route,
health, resource, or damage-window gates. The `show-hunt-candidates` report
now exposes the readiness label and bonus. No live progression claim is made by
this ranking change.

**Moria rotated-stop reentry (2026-09-01):** Live run 10952 reached the
official Moria endpoint, then exposed that the bounded healer rotation
advanced to a source VNUM stop without replaying the source route from the
endpoint. The starter now carries that preceding route as a one-use reentry
leg before checking live GMCP exits. Focused Moria coverage passes, while a
fresh live segment is still required before this route is treated as verified
progression. Run 10954 exercised the prefix replay and reached room 4064, then
exposed the missing 4064-to-4063-to-4058 waypoint bridge; run 10955 selected a
food-reserve maintenance segment instead. Run 10958 completed a bounded reset
wait and `time` probe without finding a new DD4 reboot marker. Startup then
corrected six legacy source-hunt loss records from an inflated count of 16 to
one loss per exact policy, based on durable segment history, without overriding
the current sanctuary cooldown or other safety gates. Run 10960 then completed
the repaired Moria reentry bridge, reached the large hobgoblin carrier,
recovered the purple sanctuary potion and head, and returned safely after the
required source-known below-band kill for 100 XP. This validates the route and
recovery boundary, not level-25 progression. Run 10961 then verified the source
cure-critical reserve route and returned safely without level progress. The
waypoint repair is now live-validated.

**Latest Aeloria continuation (2026-09-01):** Aeloria remains a level-18
Human Mage at 165,794 XP, 11,856 XP short of level 19, safely checkpointed in
healer room 3054 at checkpoint 33030. Run 10934 produced a real 433-XP Shadow
Keep kill; runs 10935-10945 completed bounded maintenance and Moria recovery
without another loss or death. Run 10946 performed the bounded `time` probe
after the reset wait, found no new DD4 reboot marker, and returned safely to the
healer. The required-loot recovery code allows one bounded healer restart at
the next source-approved carrier location after a pre-combat below-band
interruption; no live run has triggered that exact branch. Offline coverage is
clean at 3,233 tests. Aeloria is still level 18, so no level-19, subclass, or
HERO proof is claimed.

**Sanctuary quaff confirmation (2026-09-01):** DD4's `do_quaff` extracts a
potion even when `spell_sanctuary` reports that the character is already
affected. The starter now records the reserve debit before issuing the command,
tracks the target-level attempt, and will not spend a second sanctuary potion
while a stale Char.Affect snapshot still lacks sanctuary. Explicit
non-consuming quaff refusals restore the ledgers. Focused and full offline
coverage pass, while a live potion-required fight is still needed to validate
the timing branch.

**Moria poison-gate repair (2026-09-01):** Live run 11014 showed that a
locator-confirmed carrier in a remote Moria room could incorrectly authorize
the fixed room-4058 `spec_poison` snake as a route gate. Kestrel failed the
route-gate consider for 50 XP, killed the level-10-fuzzed snake, was poisoned,
and paid a further 385-XP combat-recall loss before reaching the carrier. The
active Moria stop construction no longer configures that generic route gate.
The exact 4053 exception remains only for
a carrier visible in the same room; otherwise the pre-combat source hazard
causes a bounded recall or reset wait. Run 11016 then live-validated the repair:
source-known warrior crowds caused safe pre-combat withdrawal before target
confirmation, with no poison, loss, or death. The focused Moria tests and full
confirmation, with no poison, loss, or death. The required-loot endpoint now
uses complete source aggression/program/special maps to ignore only mobiles
that cannot initiate or join at the current level; run 11021 confirmed that
4051 is ignorable at level 24 while sentinel 4050 remains blocked. The deep
sanctuary probe now has a source-audited large-cave detour around room 4062;
the maze branch remains research-gated. The focused Moria tests and full
offline suite pass.

**Current live update (2026-09-01, latest):** Kestrel remains level 24 at
335,293 XP with 30,807 XP to level 25, safely in healer room 3054 at
checkpoint 33274. Run 11057 found the source cure-critical gnome target absent.
Run 11058 validated the repaired Circus damage-window probe, counted the
opening attack, measured 36 damage against 1,093 target HP, and lost 385 XP on
withdrawal. Run 11059 rotated to Mirror Realm and withdrew before combat when
the last purple reserve was unavailable. Run 11060 completed the Moria
sanctuary-reserve circuit, recovered one purple potion from the
source-registered large hobgoblin, and returned safely to healer room 3054. The
current reboot remains `Fri Aug 14 00:15:48 2026`; negative fame, protection
recovery, and reserve boundaries remain active. The campaign suite passes 1,057,
the starter suite passes 1,221, and the full offline suite passes 3,270 tests.
This is level-24 route and recovery evidence, not level-25, subclass, or HERO
proof.

The resource catalog and executor now share reset provenance: mobile-carried
objects and mobile-equipped objects are both eligible required-resource
placements, while direct carried loot remains the saleable subset. A generic
sanctuary reserve route carries the exact source mobile and object VNUM into
the live required-loot stop and falls back to the proven Moria route when no
other source-safe potion carrier is reachable. The Dwarven Catacombs flask
VNUM 2008 is correctly `source-only` because its route is key-locked; this is
source evidence, not live acquisition proof. Castable scrolls, wands, and
staves now expose source-derived activation semantics in each resource
placement (`quaff`, held `recite`, held `brandish`, or held `zap self`). Once
one is acquired and acknowledged live, the checkpoint persists its exact
activation contract and remaining charges; the next segment can hold and use
it without guessing. Source-only placement rows remain outside executable
proof until that acquisition boundary is crossed.

Training policy note: live `practice` output is authoritative for current
skill percentages. Historical accepted or rejected events are migration
evidence only. A same-level, same-reboot regression schedules one
progression-route trainer refresh that clears stale practice, deferred-type,
and trainer-cap filters; the refresh is consumed once, preserves live route
hazards, and is never replayed after it has been attempted. A trainer-only
no-op may be reopened once, and one rejection-only follow-up may receive one
alternate-skill refresh. The durable deficit snapshot is refreshed from the
latest live skill levels when the segment closes.

**Latest Praelarran continuation (2026-09-01):** Praelarran remains a level-15
Human Warrior at 106,709 XP, with 8,091 XP to level 16, safely checkpointed in
healer room 3054 at checkpoint 33028. Runs 10947-10949 completed bounded
flight and source-ranked endpoint checks without progression or death. Run
10950 retried the source-verified Moria sanctuary route after its bounded reset
wait; the carrier was absent at room 4064 and source mobile 4056, a wandering
orc, engaged before endpoint confirmation. The bot followed the authoritative
post-engagement flee rule, lost 167 XP, recalled, and recovered safely. The
ordinary low-peak fallback remains closed; fresh level-16 combat evidence is
outstanding. This is live safety and continuation evidence, not level-16,
level-30, subclass, or HERO proof.

The same continuation exposed a liveness bookkeeping gap: a worker can leave a
campaign marked `running` after opening it but before creating its next segment.
`recover-runs` now reopens only such campaigns without a running segment, after
the operator confirms no worker remains, while preserving checkpoints. It also
respects the existing OS-backed campaign lease, leaving a live worker untouched
during the brief window before its first segment is recorded. Focused and full
offline coverage validates the repair.

The source audit now exposes a reusable `rank_resource_sources` report and the
`show-resource-sources` CLI. It maps sanctuary, healing, flight, and
non-poisonous food objects to exact reset rooms, distinguishes shop stock from
mob carriers and ground resets, and carries the existing route and hazard
annotations into the inspection output. This is source research and planning
evidence only; it does not claim that a reset is currently live. Starter
checkpoints also retain observed skill names and percentages across maintenance
segments, allowing a trained protective or cure spell to satisfy an executable
reserve gate without inventing a capability. Startup repair reconstructs those
accepted capabilities from a bounded event-ledger history for older checkpoints,
then supplies them to the resumed StarterPolicy before field decisions, so
reconnecting does not discard skills learned before the fields existed.

**Earlier current live update (2026-08-31):** Praelarran is level 15 at 106,876 XP in
healer room 3054 at the latest checkpoint 32926, with 7,924 XP to level 16. Run
10915 rotated to the independent Haon Dor Shargugh route, encountered one
source-known below-band brown bear in transit, earned 80 incidental XP, then
aborted and quarantined the route safely. Run 10916 checked the next
Wyvern-area endpoint and found its exact target absent. Run 10917 checked all
three configured centaur endpoint rooms (1711, 1714, and 1715), found the exact
elder centaur absent at each, and returned without combat. No loss or death
occurred; no current sanctuary reserve is available and the protection marker
remains active. The reset-aware retry then ran 10918, reopened the
source-verified Moria sanctuary route, found its exact carrier absent, and
returned safely without XP change, loss, or death. Run 10919 retried the
source-registered room-4064 circuit, found the carrier absent again, and
recorded one unavoidable below-band warrior for 80 incidental XP before a safe
return. Run 10920 checked one source-ranked centaur endpoint and found it absent;
run 10921 completed the three-room centaur absence sweep without combat or XP
change. Run 10922 then completed the reset-aware Moria retry: the exact
sanctuary carrier was absent at room 4064, so the character recalled and quit
safely with no combat, loss, or death. No objective kill occurred. The full
offline suite passes 3,197 tests. Campaign 30 is ready for the next
reboot-aware retry; this is level-15 continuation and level-16 research-handoff
evidence, not level-16, level-30, subclass, or HERO proof. The registry now
includes the research-status `mahntor-rock-toad-warrior-circuit-16-18`
continuation and its level-19-to-20 continuation
`mahntor-rock-toad-warrior-circuit-19-20`. The first is selected only for
warriors with prior class-tagged Mahn-Tor progress; the later policy is selected
only after a positive level-16-to-18 result. Both retain the source mobile,
peak-damage, live-consider, crowd, and healer-return gates. Run 10906 was level
15 and run 10922 found the required carrier absent, so fresh level-16
confirmation remains outstanding. Earlier
level-15 evidence follows. Runs
10847-10848 safely exercised the
repaired source-ranked timeout rotation. Runs 10849-10850 completed bounded
funding maintenance; run 10851 exposed a 985-XP loss on a low-band Haon route
with several source-reachable attackers. The funding selector now rejects
low-band routes with multiple static or wandering attackers. Run 10852 then
selected Katrina the Shepherd through the repaired selector, added 50 XP, and
returned safely to healer room 3054 with no loss or death. The multi-attacker
branch is offline-verified and awaits a fresh route-specific live validation.
Run 10853 performed the bounded Wyvern capacity probe; its source-registered
centaur guard was absent, so it returned without combat, XP change, loss, or
death. Run 10854 retried Moria sanctuary recovery after its bounded reset wait;
the carrier was absent and two source-registered orcs reached room 4064 before
target confirmation. The old path fled and cost 167 XP, but returned safely.
The source-reset endpoint preflight now recalls before an unstarted exchange;
this repair is offline-verified and awaits a fresh Moria live validation. Run
10855 selected the source-ranked Haon Dor Shargugh endpoint, confirmed its
absence with `where`, and returned safely without combat or further XP loss.
Run 10856 then completed a source-ranked centaur route with all three candidate
rooms absent and no combat. Run 10857 then checked the next bounded
provision-funding endpoint; the source-selected Circus Midget was absent, so it
returned safely without combat, XP change, loss, or death. Run 10858 followed
the next source-selected Ambush funding route; the fanatical goblin guard was
absent, but two source-known below-band goblin lieutenants were unavoidable
transit attackers and yielded 120 incidental XP before the runner returned
safely. No XP loss or death occurred. Praelarran is now checkpointed at 32636.
Runs 10839-10841 completed a bounded sanctuary-recovery
pass, a Magic Shop boundary check, and a source Wyvern route probe without
combat, loss, or death. Run 10770 completed one source-matched
Bird Spider kill for 506 objective XP through the repaired bounded timeout
revalidation handoff, and run 10772 added 245 incidental XP before the
source-known below-band drider transit gate quarantined the Eastern Desert
route. Runs 10773-10779 then rotated through absent Wyvern, Moria sanctuary,
Haon, and Wyvern targets without death or XP loss. Run 10779 reached its
bounded field cap and returned safely; DD4 supplied the healer room arrival
without a prompt, and the runner now accepts that authoritative safe-room
transition as the acknowledgement. Praelarran remains safely in healer room
3054. The current level-15 protection marker remains the Eastern Desert
hard-health-floor result, so sanctuary recovery is still cooldown-gated;
independent source-safe routes can make progress when their live target and
route gates pass. The earlier run 10762 exposed the pre-repair orc-engagement
loss; its flee-first repair is offline-verified but still awaits fresh live
validation.
Kestrel is level 24 at 336,894 XP at checkpoint 32584, safely in healer room
3054. Runs 10788-10790 restored food and cure-critical reserves and tested
bounded fame routes. Run 10791 exposed that a mixed bravery-plus-durability
`consider` response could authorize an unwinnable moose fight; Kestrel
withdrew after a 479-XP loss and survived. The fame policy now rejects that
mixed response, and normal resumes did not replay the lossy route. Runs
10792-10801 completed recovery, liquidation, source probes, and food
maintenance without another loss or death; run 10801 left the exact venison
reserve in healer room 3054 with full health, mana, and movement. Run 10803
then completed the fresh `mirror-realm-watchman-probe-21-25` observation-only
segment and checkpointed Kestrel at 32478 without loss, death, or XP change.
Runs 10809-10813 completed bounded return-home, food, Moria, reset-wait,
cure-critical, and Shire maintenance; run 10813 live-validated the ordinary
one-below-band-transit-fight quarantine, adding 150 incidental XP with no
objective kill, loss, or death. Run 10815 found the Moria carrier beside
source aggressive warrior 4051 and returned safely; the locator-backed
required-loot sweep now advances to the next source-approved carrier room only
when the exact target is visible and no combat is active. Run 10816 acquired
the source-required venison reserve without combat or XP change. The repair is
offline-verified and awaits a fresh carrier-bearing live result.
Run 10819 also exposed that DD4 can combine "looks like an easy kill" with
"built like a tank". The source-ranked parser now rejects that unsupported
durability warning without a source peak-damage bound, and the state reducer
handles GMCP-before-text XP-loss ordering without double subtraction. Run
10820 repaired the durable checkpoint from the authoritative Worth snapshot.
Run 10821 then killed the source large hobgoblin for 110 XP and returned safely
with a purple reserve; runs 10822-10823 completed cure-critical and venison-
reserve maintenance without combat or XP change. The latest checkpoint is
full in healer room 3054, with the historical Beast loss quarantined. Run 10824
then found the exact Mirror Realm target absent and returned safely without XP
change. Run 10825 reached the source-registered Circus ticket clerk, observed
the six-to-nine-level response paired with `built like a tank`, and correctly
refused combat under the source-ranked durability gate before returning
without XP loss. Run 10842 then reached the Mirror Realm moose, rejected the
same durability warning before combat, and returned safely; run 10843 attempted
a flight purchase in a bounded segment, but the Magic Shop refused service
because of negative fame, so no flight capability was recorded. Run 10844
performed the bounded `time` probe and found no new MUD reboot marker; the next
invocation remains behind the reboot-local cure-critical/fame recovery boundary.
Serevian then completed
bounded funding rotations: run 10826
inspected the Midget endpoint without a kill, run 10830 killed Uburz for 50 XP,
and runs 10833 and 10836 killed Ushog for 123 and 146 XP after unavoidable
10-XP Olog transit encounters. Runs 10831, 10834, and 10837 liquidated the
resulting gear; run 10838 completed safe return-home with no loss or death.
Aeloria is level 18 at 165,361 XP at checkpoint 32481 after
run 10780 requested a Suturb kill quest and run 10781 boundedly aborted its
source-unsafe Highlands target; Serevian is level 11 at 49,938 XP at checkpoint
32571 after the productive funding rotations; its next source-safe funding
candidate is unavailable for the current reboot. The current catalog-smoke
Vergalcoror campaign (19) is level 8 at 30,800 XP in healer room 3054 at
checkpoint 32594; runs 10827-10829 completed safe liquidation, return-home, and
a Circus route without loss or death. Run 10845 reached the Daycare ring and
withdrew before the exact target because the old wrinkled nanny was a
source-registered endpoint hazard. The older validation campaign (9) remains
at checkpoint 32546. The current MUD reboot is `Fri Aug 14 00:15:48 2026`;
the source mirror is clean at `7996722`, and the full offline suite passes 3,195
tests. Run 10893 established that sanctuary does not neutralize
gas-breath's poison-backed nausea; `spec_breath_gas` and random
`spec_breath_any` are now research-gated. Policy revision 184 still preserves a
level-21-or-higher observation-only
probe when both negative fame and protection recovery are active, allowing the
source frontier to refresh without authorizing combat; fame, sanctuary, and
flight gates still control every hunt. The quiet healer-sleep movement check is bounded by a 30-second score
probe with offline regression coverage. These are continuation and safety
results, not level-30, subclass, or HERO proof. The starter now has a small
source-backed subclass combat slice after the level-30 handoff: druid bark skin
and monk defensive spells are maintained, while barbarian berserk, vampire
suck, and martial-artist strikes are bounded by live-known skills and combat
cooldown state. Area-wide spells, forms, songs, turrets, and runes remain
research-only. The next practical work is continued bounded source progress
while sanctuary recovery remains separately gated, then the level-30 subclass
transition boundary. Campaign 8 is ready at checkpoint 32584; its current
catalog-aware result is `source-ranked-hunt-unavailable-24` because negative
fame blocks the Magic Shop, the remaining frontier requires flight, and no
verified sanctuary reserve is available for fame recovery.

The deep Moria required-loot policy now has one explicit source-backed
target-first exception: when the exact below-band carrier is visible beside
source mobile 4053, the poison snake may remain unengaged until after the
carrier. Active, ambiguous, or higher-band poisoners still force withdrawal;
the exception is not general progression evidence. At registered room 4064,
source-known below-band hostiles without an observed combat exchange trigger a
legal recall before combat; an already-engaged exchange retains the bounded
flee-and-return path.

The source sweep also makes the late-band debt measurable: the current parser
finds 15 safe candidates at level 70, 9 at level 80, and 3 at level 90, but no
safe candidate at level 95 or 99. The level-95 frontier is currently limited to
the psionicist, demon, and two-instance assassin research cases; level 99 is
limited to a fame-gated unicorn and shopkeepers. The new source-special audit
opens only the low-risk spell thresholds, so the next late-band work must model
energy drain, disintegrate, demon spell damage, fame, and exact quest access
before promoting any of those routes.
Verified combat-pouch sanctuary reserves reach policy selection as usable
protection, while funding and required-loot routes retain their explicit
below-band acquisition exceptions.

The trainer deferral is deliberately bounded. A `training_deferred` event and
the route hazard are persisted in SQLite; the marker is valid only for the
recorded level, reboot, and source revision, so unperformed training is retried
when the environment changes rather than becoming a permanent character rule.

### Historical continuation detail

Runs 9478-9479 created Serevian, a
fresh human male thief, through live creation and recovery. Runs 9515-9519
completed bounded maintenance without loss or death. Run 9520 killed six Mud
School opponents for 444 XP, run 9521 added 216 XP through five more
source-ranked kills, and run 9522 added 336 XP through three more. Runs
9524-9526 added 679 XP, run 9527 completed return-home maintenance, and run
9528 added 205 XP. Runs 9529, 9531, 9534-9535, and 9537-9538 added 1,230 XP;
the intervening checkpoints were safe maintenance or reset boundaries. Run
9540 crossed Serevian to level 5; runs 9541-9543 completed level-5 setup and
handoff maintenance, run 9544 added 265 XP, run 9545 recorded an empty arena
with one bounded reset wait, and run 9546 completed return-home cleanup. He is
now safely level 5 at 10,436 XP and checkpoint 28829, with maximum health 99
and mana 127. Runs 9547-9548 and 9550 added 564 XP, runs 9552-9554 added 525
XP, run 9556 added 157 XP, and run 9558 added 122 XP; the other checkpoints
were safe maintenance or bounded reset waits. Subsequent bounded Serevian runs
added 2,365 XP with safe maintenance and reset-wait checkpoints interleaved. Run
9589 crossed him to level 6 at 14,169 XP and checkpoint 28896, raising maximum
health to 113 and mana to 134. Runs 9590-9613 then completed bounded level-6
outfit, recovery, and source-ranked rotations; productive routes added 955 XP,
while empty or absent candidates stopped safely. Run 9613 left Serevian at
15,124 XP and checkpoint 28948, full in healer room 3054. Runs 9614 and 9615
then safely tested another Circus route and the Dwarven Daycare route without
forcing combat; the latest Serevian checkpoint is 28948. Praelarran run 9598
added 502 XP through Fleshmonger, and runs 9626-9628 added another 450 XP
through the current-band pool. His latest pre-repair field checkpoint was
29331. Runs 9798-9802 then completed bounded sanctuary, secretary, Shadow
Keep, crowd, and Ambush continuations without death or XP loss; run 9799 killed
source mobile 3142 for 269 objective XP and run 9802 killed source mobile 4512
for 338 objective XP. Praelarran is safely level 14 at 94,450 XP in healer room
3054 at checkpoint 29475, 3,650 XP short of level 15. Runs
9681-9682 crossed level 14 and completed liquidation. Run 9686 exposed a
text-only `The Temple Square` room header without a GMCP VNUM; the runner
cleared stale identity and aborted safely. The fastwalk decision now resolves
unique source-backed Midgaard room names when GMCP omits the VNUM. Run 9687
crossed the repaired handoff but paid a 148-XP health-floor withdrawal; run
9689 then completed a clean 288-XP archer route. Runs 9690-9692 then added 665
XP through Haon, Shadow Keep, and Plains North with no loss or death; the
campaign is ready at the next source-ranked boundary. Runs 9699-9701 then added
80 XP through Haon, Shadow Keep, and Midgaard without loss or death; the campaign
is ready again at the next source-ranked boundary. Runs 9702-9704 then added 601 XP
through Shire, Shadow Keep, and Fleshmonger without loss or death. Runs 9705-9707 then
completed liquidation, return-home, and sanctuary recovery without changing XP or
recording loss or death. Runs 9708-9710 then added 411 XP through Shire, Haon,
and Shadow Keep without loss or death. Runs 9711-9713 then added 607 XP through
Shire and Shadow Keep and completed provision restock without loss or death.
Runs 9714-9716 then added 271 XP through Fleshmonger and completed safe return and
liquidation. Runs 9717-9719 then added 130 incidental XP without a
source-objective kill and completed safe healer recovery. Runs 9720-9722 then
added 620 XP, including a source-objective Shire kill, without loss or death.
Runs 9723-9725 then added 316 XP through Shire and completed Fleshmonger and
Dwarven Daycare segments without loss or death. Runs 9726-9728 then added 378
XP, including a source-objective Shire kill and safe sanctuary recovery. Runs
9729-9734 then added 496 XP; run 9733 killed source mobile 4512, The vile
goblin, for 346 objective XP, with the remainder incidental transit XP. Runs
9735-9740 then added 437 XP; run 9736 killed source mobile 4512 for 50
objective XP, run 9737 killed source mobile 139, Sir Durok of EAT, for 377
objective XP, and run 9735's 10 XP drunk was incidental. Runs 9741-9746 then
added 1,047 XP; run 9741 killed source mobile 4512 for 307 objective XP, run
9743 killed source mobile 139, Sir Durok of EAT, for 396 objective XP, and run
9744 killed the goblin lieutenant incidentally for 80 XP and source mobile 4512
for 264 objective XP. Runs 9747-9752 then added 1,079 XP; run 9748 killed
source mobile 139, Sir Durok of EAT, for 431 objective XP, run 9750 killed
source mobile 4512 for 50 objective XP, and run 9751 killed source mobile 139
for 488 objective XP, with 110 incidental XP alongside them. Run 9757 then
reproduced a Gremlin Lair recall-recovery hazard: the first recall reached
Temple room 3001, but stale GMCP identity caused the following inferred text
room event to be discarded and a second recall cost 148 XP. No death or
objective kill was recorded. Campaign revision 174 now accepts the authoritative
room transition and persists this exact route as a retryable current-reboot
hazard. Run 9758 converted the failed checkpoint during startup migration and
completed safe return-home. Runs 9759-9788 then added 1,507 objective XP across
five source-matched kills, plus bounded incidental combat and maintenance. Run
9787 reached the 120-second field cap and recovered cleanly; run 9790 recorded
a 148-XP Gizmo-route recall loss without a death or objective kill, and run
9791 restored full healer state. Runs 9792 and 9795 then recorded separate
-148 XP losses on the Fleshmonger and Moria routes; their one-loss quarantines
held, and run 9797 completed flight maintenance. Runs 9798-9802 then exercised
bounded sanctuary recovery and source-ranked fallback rotation: Moria's carrier
was absent, run 9799 yielded 269 objective XP, run 9800 safely recorded an
absent Shadow Keep target with incidental wandering combat, run 9801 skipped a
crowded secretary repeat, and run 9802 yielded 338 objective XP from a
live-considered vile goblin. The selector now prefers recent productive routes
over low-fuzz fresh candidates; the full offline suite passes 3,013 tests.
Praelarran is now 3,650 XP short of level 15. This is level-14 continuation and repair evidence, not level-15, subclass, or
HERO proof. The runner now processes GMCP
`Room.Info` before same-read textual room output, and startup reconciliation
preserves newer maintenance-attempt markers. The public HERO credential boundary permits an untouched prepared
workspace to generate its first stored password while remaining strict for a
campaign that has already recorded work. No subclass or HERO completion is
claimed.

### Historical detail

The live continuation remains Aeloria, a human mage at level 18 with 165,613 XP
at checkpoint 27725 after runs 9109-9111. Dorrik is level 24 at 363,190 XP at
checkpoint 27807 after runs 9141-9142; his Moria and sanctuary-protected
funding kills completed
without a field loss. The earlier live quest-abort validation, clean Shire absence, and
three bounded source-safety continuations;
Kestrel is level 24
at 336,913 XP at checkpoint 26810, where fame recovery remains on a
current-reboot service cooldown. Praelarran is a human warrior at level 13 with
71,295 XP at checkpoint 28694; the level-13 warrior continuation is active at
the source-ranked frontier handoff.
Corararfen remains a human cleric at level 6 with 17,020 XP at checkpoint 27756;
Velnor is level 6 at 15,255 XP at checkpoint 27762 after runs 9124-9125;
Fenanallor remains a human ranger at level 4 with 7,771 XP at checkpoint
27767 after runs 9128-9129. All active campaigns are safely checkpointed in healer
room 3054. Runs 9109-9110 requested a live Suturb retrieve quest and exposed a
raw shortest-path route into Old Marsh room 8310, where source mobile 8306, an
aggressive level-12 huge hairy beast, attacked. Aeloria fled at 193/218 HP and
lost 232 XP without dying, then recovered at the healer. The quest preflight
and executor now share a source-safe route gate for retrieve, object, and hoard
targets; real source validation rejects room 8310 for level 18, and the full
offline suite passes 2,994 tests. Direct live proof of the repaired quest route
awaits the next generated non-kill quest. Runs 9114-9120 added 1,304 XP to
Praelarran through four source-matched warrior kills, with no loss or death.
Runs 9121-9123 completed Corararfen's outfit, return-home, and daycare-ring
recovery maintenance without a field loss. Runs 9124-9125 added 109 XP to
Velnor through a source-matched Sorbus kill and trained cure light; the later
fanatic route was absent. Runs 9128-9129 completed Fenanallor's ranger
starter/Mud School boundary, added 227 XP from two boars and two wolves, and
trained shoot. Run 9130 advanced Praelarran from level 8 to 9 through a 192-XP
Illusionist kill, recovering a shimmering key and 21 maximum HP without loss or
death. Run 9132 then added 835 XP from three source-matched level-9 kills,
recovered a disarmed broadsword and 14 items, and trained enhanced damage plus
unarmed combat knowledge for stun. Run 9137 then added 681 XP from the on-duty
guard and cook, recovered eight items including a rearmed broadsword, and
returned safely without loss or death. Runs 9141-9142 then added 200 XP to Dorrik
from the large hobgoblin and blonde dwarf, recovered a purple sanctuary potion,
and used it on the second route; he returned full without loss or death. Run
9147 then added 494 XP from two more guard/cook kills, recovered ten items and
a disarmed broadsword, and returned full without loss or death. Run 9153 then
added 485 XP from the source-matched on-duty guard and cook after a trivial
drunk contact, recovered seven items, and returned full. Runs 9154-9155 sold
the loot and completed return-home maintenance. The campaign resume migration
also synchronized Praelarran's stale SQLite display label to `Praelarran to HERO`
without changing Campaign 30 or its checkpoints. Runs 9156 and 9158-9159 added
1,367 XP through armed-guard, bull, and guard/cook kills; run 9157 recorded a
safe Moria absence. Runs 9160-9161 completed return-home and Plains North/
Sorbus absence maintenance. Runs 9162-9169 added a further 1,023 XP through a
Shire bull and three guard/cook rotations without death or XP loss. Run 9187
then crossed Praelarran from level 9 to 10 with 519 XP and 23 maximum HP. Run
9191 visited the level-10 warrior trainer, read the guildmaster plan, trained
enhanced damage to 44%, and added 640 XP from the patrolling guard and cook's
boy after recovering a disarmed broadsword. Runs 9194-9195 trained enhanced
damage to 49% and unarmed combat knowledge to 41% toward the source-backed stun
prerequisite. Runs 9198-9218 added 4,456 XP through source-matched warrior
kills and safe Moria, Shire, and Circus rotations; run 9219 sold recovered
loot, runs 9220-9221 recorded clean absences, and run 9222 added 828 XP from
three source-matched kills. Run 9225 then killed an armed guard for 176 XP and
recorded body-part food handling; run 9226 killed the patrolling guard, on-duty
guard, and cook for 966 XP and recovered 13 items. Run 9227 sold the loot,
while runs 9228-9229 recorded clean Cult absences. Praelarran is safely
checkpointed at level 10 with 46,870 XP and no loss or death. This is
representative level-10 class/training evidence, not subclass or HERO proof.
Run 9239 then crossed Praelarran from level 10 to 11 with 771 XP from two
source-matched guard kills and 22 maximum HP, returning safely without loss or
death. Runs 9242-9243 continued the warrior trainer route, raising enhanced
damage to 53%; run 9244 added 507 XP and trained unarmed combat knowledge to
47% toward the 60% stun gateway. Runs 9247-9249 included a clean Circus probe,
flight maintenance, and a further 255-XP small-troll kill. Run 9250 then added
582 XP from two source-matched guards and recovered 12 items. Praelarran is
now safely checkpointed at level 11 with 50,804 XP and no loss or death. This
is level-11 continuation and training evidence, not subclass or HERO proof.
Runs 9254, 9259, and 9262 added 536 XP from three small-troll kills; runs
9255 and 9263 added 1,220 XP from four source-matched guards, with safe Moria
and Shire absence probes between them. Praelarran is now safely checkpointed at
level 11 with 52,560 XP and no loss or death. This remains level-11
continuation evidence, not subclass or HERO proof. Run 9267 added 230 XP from
an armed guard. Runs 9268 and 9280 added 864 XP from source-matched patrolling
guards; run 9272 added 202 XP and run 9278 added 186 XP from small trolls.
Run 9274 killed a patrolling guard for 395 XP, withdrew at the 32% health floor,
and paid a 99-XP flee cost for a net 296 XP; the exact source policy is now
bounded by its one-loss protection rule. Run 9277 added 302 XP from an armed
guard, while run 9279 recorded a clean Circus absence. Praelarran is safely
checkpointed at level 11 with 54,650 XP and no death; this remains level-11
continuation evidence, not subclass or HERO proof. Runs 9283-9284 added 468
objective XP from an armed guard and a small troll. Run 9285 recorded a clean
Strongman's Tent no-target result; run 9286 added 401 XP from a patrolling guard;
runs 9287-9288 completed loot sale and return-home maintenance. Run 9289 added
178 XP from an armed guard and used its body part as food; runs 9290-9291
completed flight and return-home maintenance. Run 9292 added 178 XP from a small
troll, run 9293 recorded 10 incidental XP from a drunk while its Circus target
was unavailable, and run 9294 added 342 XP from a patrolling guard after
recovering a weapon dropped by a live disarm. Praelarran is now level 11 at
56,227 XP at checkpoint 28226, with no loss or death in this continuation
batch. This remains level-11 continuation evidence, not subclass or HERO proof.
Runs 9297-9298 added 490 objective XP from an armed guard and a small troll;
run 9299 recorded a clean Strongman's Tent no-target result; and run 9300 added
281 XP from a patrolling guard with six items recovered. Praelarran is now
level 11 at 56,998 XP at checkpoint 28243, with no loss or death in these
follow-up segments. This remains level-11 continuation evidence, not subclass
or HERO proof. Runs 9303-9306 added 789 objective XP and 20 incidental XP
through armed-guard, small-troll, Circus absence, and patrolling-guard routes.
Runs 9307-9308 completed loot sale and return-home maintenance; run 9309 added
202 XP from an armed guard; run 9310 refreshed flight; run 9311 recorded a
10-XP incidental drunk contact while the Cult fanatic was unavailable. Run 9312
then added 442 XP from a patrolling guard and crossed Praelarran from level 11
to 12, raising maximum health from 246 to 270. He is now level 12 at 58,461 XP
at checkpoint 28275 with no loss or death. This is level-12 continuation
evidence, not subclass or HERO proof.
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
Runs 9355-9356 recorded safe Daycare and Cult absences. Run 9357 added 271 XP
from an on-duty guard; run 9358 added 175 XP from a Shire bull after skipping a
crowded circuit; and runs 9359-9360 completed flight and return-home
maintenance. Runs 9361, 9364, and 9367 recorded clean New Ofcol absences; run
9362 added 228 XP from an on-duty guard; and run 9363 recorded a clean Circus
absence. Run 9368 added 174 XP from an armed guard. Run 9369 then exposed an
unexpected dwarf-forest combat, costing 116 XP on withdrawal without death; the
exact route is now bounded by the current-reboot loss policy. Praelarran is
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
Runs 9333 and 9338 recorded clean Circus and Dragon Cult absences. Run 9334
added 214 XP from an armed guard; run 9335 added 738 XP from a patrolling guard
and on-duty guard after recovering a disarmed broadsword; runs 9336-9337
completed loot sale and healer return. Run 9339 added 229 XP from another armed
guard. Praelarran is now level 12 at 61,165 XP at checkpoint 28347 with no loss
or death. This remains level-12 continuation evidence, not subclass or HERO
proof.
Aeloria's next bounded invocation retained her Shadow Keep crowd gate
without combat. Runs 9014-9015 completed bounded
continuations without death or XP
loss: Aeloria reached a source-registered Arachnos route and withdrew on its
poisonous-bystander gate, while Praelarran confirmed a Circus target absent.
Run 9016 completed Dorrik's automatic reset retry and safe Magic Shop flight
maintenance; runs 9017-9019 then added 67, 122, and 176 objective XP for
Praelarran from source-matched routes and returned him safely to the healer
after each segment; run 9020 added another 134 objective XP, and runs 9021-9024
recorded two source absences, flight maintenance, and safe return-home without
loss. The campaign
repair now re-arms a timed-out source route only
after an automatic reset wait, consumes the retry when the hunt segment opens,
carries legacy attempt counts forward, and quarantines the route after two
bounded attempts. Campaign preflight now records the exact source teacher
mobile, room, keyword, skill, and route for all 18 legal subclass combinations.
The subclass-focused checks pass 78 tests and the full offline suite passes
2,965 tests. The source-ranked handoff now requires a second verified purple
potion or persisted `cure blindness` for audited caster specials across every
class, while preserving the negative-fame protected-frontier ordering. A
bounded Dorrik invocation after the repair remained safely behind the
current-reboot Tentusks crowd gate; direct live reserve-branch proof is still
pending. These are continuation and source-preflight anchors, not level-19,
level-30, subclass-transition, or HERO proof.

Run 9041 then completed a bounded Shadow Keep eel continuation without combat,
XP change, death, or loss, leaving Aeloria full in healer room 3054. Run 9042
requested a live retrieve quest for Dorrik; source preflight identified its
Gloomy Forest room 285 as disconnected from Midgaard. Run 9043 followed DD4
FAQ 5.4 and returned to Suturb to issue `QUEST ABORT`, clearing the quest
without combat, XP change, death, or loss. Run 9044 then completed one
automatic reset retry and recorded a clean Shire target absence, returning
Dorrik full to the healer. Run 9045 completed a bounded source-ranked hunt
without progress; run 9046 applied the source-identity gate; and run 9047
recorded the next funding target absent at its source room. All three had no
combat, XP change, death, or loss. Run 9048 then killed the source-matched
large orc in Moria for 175 XP and two items, returning Praelarran safely to
healer room 3054. Run 9049 then killed the source-matched Shire Miller for
another 115 XP and recovered a heart, again returning safely. Runs 9050-9051
then added 125 XP from a Shire bull and 161 XP from two Circus kills, with five
items recovered in the latter run. Praelarran remains safely checkpointed at
the healer. Run 9052 extracted purse coins and discarded the empty container;
run 9053 recorded a safe Circus absence; run 9054 then reopened Moria for
another 182-XP large-orc kill and two items. Runs 9055-9057 then added 68 XP
from a Circus bearded lady, 92 XP from Sorbus the Hermit, and 190 XP from a
fanatic monk. Run 9058 sold three rings for 23 coins and returned Praelarran
safely to the healer. Run 9067 then killed a source-matched Shire bull for 170 XP,
crossing him from level 7 to level 8 with 19 additional maximum hit points and no
loss or death. Run 9068 filled the last legal empty wear slot, hands, with a
verified basic Leather Shop item; run 9069 completed healer recovery without XP
change. Praelarran is safely checkpointed in room 3054. Run 9070 then trained
enhanced damage and unarmed combat knowledge for the source-backed stun
prerequisite, killed Ivan and the Illusionist for 335 XP, and returned without
taking damage or losing XP. Run 9071 rejected the live receptionist after
`consider`; an aggressive wandering drunk attacked during transit and was
finished defensively for 10 incidental XP, with no objective target claimed.
The return remained safe. Run 9072 then recorded the fanatic route absent with no
combat, XP change, loss, or death. Run 9073 rotated to the Circus and confirmed
Ivan plus the Illusionist for 320 XP, with full health and a safe healer return.
Run 9074 then killed the source-matched cook for 368 XP, recovered two items,
and returned at full health. Run 9075 then recorded the Circus midget route
absent with no combat, XP change, loss, or death. Run 9076 confirmed Ivan plus
the Illusionist for 403 XP, with no loss or death and full healer recovery. Run
9077 recorded the fanatic route absent with no combat, XP change, loss, or
death. Run 9078 then killed the source-matched cook for 429 XP and two items,
returning at full health. Runs 9079-9080 then sold four recovered items for 164
coins through the verified Weapon Shop, Leather Shop, and Armoury, followed by
safe healer recovery without XP change. Runs 9081-9082 then added 786 XP from an
armed guard and Ivan; the second run skipped an ambiguous target and tried the
recovered body part as food. Both returned safely without XP loss or death. Runs
9083-9084 then recorded the fanatic route absent and a source-matched cook kill
for 275 XP and two items, again returning at full health. Runs 9085-9086 then
added 739 XP from Ivan and an armed guard, with no loss or death and safe healer
returns. Runs 9087-9088 then recorded a fanatic absence and skipped an ambiguous
strongman target; an aggressive drunk was finished defensively for 20 incidental
XP, with no objective target, loss, or death. Runs 9089-9090 then added 614 XP
from a Bearded Lady, Illusionist, and armed guard; one wandering drunk added 10
incidental XP. Both returned safely without loss or death. Runs 9091-9092 then
covered the Foundry loop, recovering a disarmed broadsword and selling six items
for 103 coins through the Leather and Weapon Shops. Run 9093 completed a safe
return-home checkpoint; run 9094 then added 120 XP from a source-matched Bearded
Lady without loss or death. Run 9095 confirmed the Dragon Cult fanatic absent
and returned safely; run 9096 then killed source mobile 112, Ushog, for 238
objective XP after a 20-XP incidental Olog contact, recovered five items, and
returned full to healer room 3054. Run 9097 sold three items for 26 coins
through the Armoury and Jeweller after an aggressive drunk was finished for 10
incidental XP; run 9098 slept and completed a safe healer return. Runs 9099
and 9100 then reached two Circus source rooms, found the Bearded Lady and
mother targets absent, and returned safely without combat, XP loss, or death.
Runs 9101-9102 then killed the source-matched Illusionist and Ivan for 250
objective XP, recovered two keys, and recorded the Dragon Cult fanatic absent;
both returned safely without loss or death. Run 9103 then added 141 XP in the
Foundry: Olog supplied 10 incidental XP and source mobile 112, Ushog, supplied
131 objective XP; five items were recovered. Run 9104 sold three items for 41
coins through the Leather Shop and Jeweller. Praelarran is now level 8 at
30,114 XP at checkpoint 27707. Run 9105 completed healer recovery; run 9106
then killed source mobile 2405, Katrina the Shepherd, for 269 objective XP and
two items after a safe consider. Praelarran reached a 71.7% HP low point and
returned safely. He is now level 8 at 30,383 XP at checkpoint 27712. Run 9107
recorded the Circus midget absent; run 9108 bought and verified a light blue
flight potion from the Magic Shop without combat or XP change. The current
checkpoint is 27717. The
current level-18 frontier is presently governed by
source-confirmed absence and crowd evidence. Dynamic quest planning now
reuses ordinary source ranking with the exact target reset room, current
level/HP, special, companion, and route gates before any live movement. An
unsafe active quest or source-proven inaccessible quest room is converted to a
bounded `quest abort` return to its registered questmaster, then waits for
DD4's cooldown before replacement. The generic selector and executor now
keep gas-bearing breath forms research-gated even when damage, sanctuary, and
health reserves are proven; lightning breath retains its separate
source-bounded path and lower nominal targets retain the ordinary ceiling. The
offline suite passes 3,189 tests; quest completion and the later level bands remain
research work.
Quest target selection now mirrors `quest.c`'s strict nominal level bands:
maximum offsets are +4, +9, +14, and +19 across the four level ranges. This
expanded ceiling is opt-in for generated quests only; ordinary hunts keep the
existing ceiling, and the dynamic path still rejects source-ineligible mobiles
and any failed route, HP, special, companion, crowd, or live-consider gate.
Wandering quest targets are accepted only when the source movement graph reaches
their reported live room; that room is ranked as a temporary endpoint and the
resulting safe route is used for dispatch.

Runs 8964-8978 extended the level-18 frontier after the earlier Queen Spider
crowd result. Shadow Keep recorded a crowd, Wyvern and Hood were absent, Moria
and Crystal were absent, and Dwarven Home failed its live useful-XP gate; flight
maintenance completed safely. The repaired Giant Eel route then observed source
mobile 16602 in room 16610, passed `consider`, and completed the kill without
death or XP loss. The next work unit resumes from checkpoint 27347 toward level
19, then level 30 and the subclass transition.

Runs 8928-8963 extended the level-18 frontier. The Gnome Treasury stash yielded
719 copper and enabled flight; Arikasbab recorded a 139-XP loss, and a bounded
Town Clerk `spec_thief` probe recorded a 166-XP loss and quarantined that exact
policy. The selector now defers incomplete negative results before they
displace fresh routes. The source-aware bystander map covers non-aggressive,
unspecialized mobiles only when every same-name source prototype in the room is
safe, and source-ranked combat now rejects an unsupported "much healthier"
consider result without a peak-damage bound. Run 8957 exposed the 319-HP
Secretary loss, run 8958 recovered safely, and run 8959 found a Wyvern target
absent and returned full. Run 8962 confirmed the source-ranked Keeper kill and
returned full without XP change. DD4 source `fight.c:group_gain` gives no XP for
a summoned NPC's final blow; the mage field policy now orders the familiar to
flee below 45% target HP and is covered by the full offline suite. The earlier
work unit began at checkpoint 27235; the next resumes at checkpoint 27295
toward level 19, then level 30
and the subclass transition.

Quest progression is now visible and bounded: the parser persists DD4
`Char.Quest` points, totals, next-level requirements, and shortfalls, campaign
reports render them, and a positive shortfall selects bounded request, target,
or completion work after required recovery and maintenance. Suturb is
source-registered through level 25, and the source graph now supplies
Goldmoon's explicit room-10024 route for levels 26-100. The source gate is at
current levels 29, 49, 79, and 99, requiring total quest points before levels
30, 50, 80, and HERO 100; missing fields can now be reconstructed from the
source rule. Checkpoint 26804 live-validated clean continuation with status
`available`, zero points, and zero shortfall. The source audit now recognizes
DD4's ITEM_DIGGER, form, and digging-weapon capabilities and adds a bounded
exact shovel VNUM 3604 acquisition from Graveyard room 3613 before a hoard
target. Dynamic quest preflight returns a durable ready/unavailable checkpoint
for missing source identity, while an inaccessible target is converted to the
source-labeled `QUEST ABORT` policy before any target movement. Exact
object/hoard completion and the remote
Ota'ar Dar route remain research-gated; this is not level-30, subclass, or HERO
proof.

The latest bounded continuation validated the level-24 source frontier and
startup repair. Run 8866 bought flight; runs 8867 and 8871 added only safe
incidental rabbit XP, while runs 8868-8870 recorded absent source targets. Run
8872 exposed a randomized Mirror Realm inter-target watchdog and returned
safely with no XP loss. Runs 8873-8875 completed safe return and bounded Mirror
probes without death or loss. Aeloria's run 8876 safely exposed a delayed
text/GMCP transition boundary during provision funding; run 8877 replayed it
successfully after the parser repair, and runs 8878-8879 completed liquidation
and healer return. The parser now emits a GMCP room refresh only when text has
identified a transition and cleared the prior exit graph; delayed text that
conflicts with a confirmed room remains rejected. The full offline suite passes
2,930 tests. These are continuation, liveness, and repair records, not fresh
creation-to-HERO proof.

The next generic handoff is now source-capability-gated at level 30 for all 18
legal base/subclass combinations. Mobile teaching entries are parsed from the
read-only DD4 area files; a subclass teacher must have both `teacher base` and
the exact `<subclass> base` entry, plus a source reset and route from recall.
The starter now follows that exact source teacher for every supported subclass;
examples include Jolob mobile 31002 (room 31041) for engineer/runesmith,
Stathog 29134 (room 29153) for werewolf/vampire, and Zelda 20603 (room 20695)
for necromancer/warlock/witch. A prepare-only public HERO smoke test for a
human mage/necromancer request also passed. This is offline/source evidence and
still needs a live level-30 transition proof.

Runs 8759-8809 validated the latest bounded continuation. Run 8759 bought a
135-copper flight potion and live-validated recovery of a known room VNUM after
a text-only return to Main Street, then reached healer room 3054 safely. Run
8760 found the white stag absent and returned without XP change. Run 8761 found
the Arachnos guardian through `where`, but its Realm of Hopeless location could
not be converted into a reachable combat endpoint before the progress watchdog
returned Aeloria safely. The locator repair now rebases matched source routes
from the live room instead of concatenating unrelated circuit waypoints; it is
offline-verified, while a fresh live guardian target remains pending behind the
current-reboot absence cooldown. Run 8762 then killed the source-matched Fat
Black Cat (mobile 28311, room 28316) for 682 objective XP and returned safely
with no XP loss or death. Run 8758 recorded a real negative safety result:
repeated fleeing from a level-8 dustdigger in the Great Eastern Desert return
maze led to death, followed by successful corpse and Purgatory recovery. Run
8763 then killed the source-matched giant, purple sand worm (mobile 5004, room
5028) for 592 objective XP, but lost 1,392 XP to repeated flee penalties from
below-band dustdiggers before returning alive and full to the healer. The
delayed-pursuer assessment repair is now offline-verified and awaits a fresh
live maze target; none of these runs is HERO proof. Run 8764 then completed the
normal Moria sanctuary continuation, killed the source-matched large hobgoblin
for 100 objective XP, and returned full to healer room 3054 without XP loss or
death. Run 8765 found no objective nomad kill; a source-known below-band
drider interruption yielded 80 incidental XP without XP loss or death, and
Aeloria returned safely. Run 8766 then completed a return-home maintenance
segment with no XP change, death, or unsafe state. Run 8767 then completed safe
loot liquidation with no XP change, death, or XP loss. Run 8768 then completed
another return-home maintenance segment with no XP change, death, or XP loss.
Run 8769 then completed the source-priced flight-potion maintenance step
without XP change or combat. Run 8770 then used `where` to confirm the white
stag absent, returned safely, and recorded no XP change, death, or loss. Run
8771 then found three mobiles in the Dwarven Home room, recorded a source-backed
crowd gate, and withdrew without combat, XP change, death, or loss. Run 8772
then found two mobiles in the Dwarven Home servant room, recorded the same
source-backed crowd gate, and withdrew before combat without XP change, death,
or loss. Run 8773 then reached the source-present Keeper of the Tower, withdrew
at the 51% health gate after missed mage damage, and paid 232 XP without a kill
or death; the exact policy is quarantined rather than blindly retried. Run
8774 reached the Forest medicine route but hit the 180-second boundary and
returned safely without an objective kill, required item, XP loss, or death. Run
8775 then completed the safe return-home maintenance boundary with no XP change,
loss, or death. Run 8776 then confirmed the gang/hood target absent at room
2148 and returned safely without combat, XP change, loss, or death. Run 8777
then confirmed the wyvern/centaur target absent at room 1717 and returned
safely without combat, XP change, loss, or death. Run 8778 found Essabella
present at room 4528 but below the useful-XP floor, skipped her before combat,
and returned safely without XP change, loss, or death. Run 8779 then killed the
source-matched giant, mobile 6506 in room 6508, for 376 objective XP and
returned full without XP loss or death. Run 8780 retried the same source VNUM
after a fresh respawn, found the giant materially healthier, withdrew at
85/218 HP, and paid 232 XP; the exact policy is quarantined for this reboot
rather than replayed. Run 8781 then completed the source-backed provision loop,
killing valley elf sentry mobile 7804 for 60 XP under the registered below-band
funding exception and returning full without XP loss or death. Run 8782 then
completed safe loot liquidation with no XP change, loss, or death. Run 8783
then completed a safe return-home boundary with no XP change, loss, or death.
Run 8784 then killed the source-matched large hobgoblin for 110 objective XP,
recovered a purple sanctuary potion and a body part, and returned full without
XP loss or death. Run 8785 completed a source-priced flight-potion research
step without combat or XP change; no new stored price was obtained. Run 8786
then killed Lord Doom for 888 objective XP and returned safely to healer room
3054 without XP loss or death. The next bounded step should allow healer
recovery before another field policy. Run 8787 then repeated the source-matched
large-hobgoblin sanctuary kill for 110 objective XP and returned full without
XP loss or death. Run 8788 then confirmed the white stag absent with `where`
and returned safely without combat, XP change, loss, or death. Run 8789 then
killed source mobile 28311, the Fat Black Cat in room 28316, for 972 objective
XP and returned full without XP loss or death. Run 8790 then reached the
source-matched queen spider in room 6134, observed three huge poisonous spiders,
and withdrew at the source-backed crowd gate without combat, XP change, loss,
or death. Run 8791 then found the gang/hood target absent and returned safely
without combat, XP change, loss, or death. Run 8792 found source mobile 28311,
the Fat Black Cat, present and considered viable, but Aeloria's mage damage was
insufficient; she withdrew at 46% health and paid 232 XP. The exact policy is
quarantined for this reboot rather than replayed. Run 8793 then reconfirmed the
white stag absent with `where` and returned safely without combat, XP change,
loss, or death. Run 8794 then completed another source-priced flight-potion
research step without combat or XP change; no new stored price was obtained.
Run 8795 reached source mobile 10302, the foreign trade representative, but
GMCP reported two useful-band or unknown active enemies; the executor aborted
safely and returned home, with a net 205-XP drop and no kill or death. The exact
policy is quarantined for review. Run 8796 then killed source mobile 10249,
the Sergeant at Arms' Secretary in room 10273, for 446 objective XP and
returned full without XP loss or death. Run 8797 killed the required large
hobgoblin for 110 XP and recovered its purple potion, but a source-known
sickly brown snake joined before return; Aeloria fled at 27% health after
paying a 232-XP penalty, leaving a net 122-XP drop and no death. The repair now
classifies ambiguous dynamic live names with any audited poison profile as
hazards before required-loot combat; offline-verified, bounded live validation
is pending. Run 8798 then completed a safe combat-pouch audit without XP
change, loss, or death. Run 8799 reached source mobile 6317, the medium dragon
wormkin, but live `consider` placed it below the useful-XP floor; it was skipped
before combat and Aeloria returned full without XP change, loss, or death. Run
8800 then confirmed the wyvern/centaur target absent at room 1717 and returned
safely without combat, XP change, loss, or death. Run 8801 reached the
source-matched Sergeant at Arms' Secretary again, but Aeloria's mage damage
remained insufficient; she withdrew at 46% health, paid 118 net XP, and
returned alive and full to healer room 3054. The exact combat policy is
quarantined rather than replayed. This makes source-backed mage damage,
protection, and training decisions the next blocker to address, not a lower
withdrawal floor. The poison-name repair remains offline-verified and awaits
bounded live Moria revalidation.

Run 8802 confirmed the white stag absent and returned safely without combat,
XP change, loss, or death. Run 8803 then entered the source-matched foreign-
trade representative room, whose arrival text visibly contained three
bodyguards. The pre-patch endpoint did not apply the room-prose crowd gate
while `Char.Enemies` was null; combat began, the bodyguards joined, and Aeloria
lost 282 XP in aggregate before returning safely. The repaired gate now counts
source-indexed room mobiles before GMCP enemy data exists and is covered by the
offline suite. Run 8804 then killed source mobile 28311, the Fat Black Cat in
room 28316, for 791 objective XP and returned full without XP loss or death.
Direct live revalidation of the new room-prose gate remains pending because
the selector rotated to this productive route. Run 8805 then completed the
normal Moria sanctuary-carrier route, killed the source-registered large
hobgoblin for 100 objective XP, recovered another purple potion, sacrificed
the empty corpse, and returned full to healer room 3054 without loss or death.
Aeloria is now at 158,276 XP. Run 8806 then searched the source-allowed Hood
circuit, found the target absent, and returned safely through healer recovery
without XP change, loss, or death. The campaign remains ready for the next
frontier selection. Run 8807 then resumed Praelarran from the explicit
authoritative validation workspace, killed the source-matched Bearded Lady for
92 objective XP, collected its hairy key, sacrificed the empty corpse, and
returned full to healer room 3054 without XP loss or death. This extends generic
warrior continuation evidence but is not level-10, subclass, or HERO proof. Run
8808 then resumed Corararfen from campaign 22, killed the source-matched
Bearded Lady for 68 objective XP with `cause serious`, handled Beastly Fido as a
non-combat joiner, and returned safely without XP loss or death. This extends
cleric continuation evidence but is not level-10, subclass, or HERO proof. Run
8809 then searched Corararfen's independent Circus Bobby route, found the
approved target absent, and returned fully recovered without XP change, loss,
or death. The level-10 cleric campaign remains ready for the next reset-aware
selection.

Runs 8744-8746 closed a live recovery and equipment-loop gap. Run 8744
acquired source food but reached the healer at 32/218 HP before quitting. Run
8745 was stopped at that safe room when the recovery stance repeated
`remove sword`, `wear 2.sword`, and `eq all`; startup reconciliation closed it
as an interrupted boundary. Run 8746 then completed liquidation in 92.9 seconds
and checkpointed Aeloria at 155,695 XP and 218/218 HP. Complete `Char.Worn`
snapshots no longer clear the state-sensitive gear-loop guard. This is
level-18 continuation and repair evidence, not subclass or HERO proof.

Runs 8703-8725 advanced the level-18 research frontier while preserving safe
returns. The sequence repaired mage access to the class-independent Lord Doom
sanctuary retry, required-loot corpse cleanup before emergency return, and
Pyramid maze navigation after failed recall. It also exposed two liquidation
watchdog races: live city combat can arrive before a usable `Char.Enemies`
snapshot, and a stale empty enemy packet can erase the text-derived combat
state. The starter now handles both boundaries with regression coverage.
Run 8713 live-validated the first repair by killing the Temple Square drunk
for 10 XP without an XP loss. Run 8720 killed the Arachnos guardian for 383
XP using the source-backed mage familiar opener, and run 8722 killed a drider
for 100 XP; both returned safely. Run 8723 remains the reproducing liquidation
loss, while run 8725 safely rejected a below-band Shire receptionist. The
second empty-packet repair is offline-verified and awaits a later loot-bearing
liquidation for direct live revalidation. This is level-18 continuation and
runtime evidence, not subclass or HERO proof.

Runs 8726-8730 added 1,150 objective XP through source-ranked Arachnos and
Eastern Desert kills, all with safe healer returns. Run 8731 reached the
source-matched level-15 secretary, dealt 96 partial XP, then withdrew at the
51% calculated combat reserve and paid a 232-XP flee cost. That 136-XP net loss
is now a concrete combat-balance input for the level-18 frontier. Run 8732
completed the Plains North source circuit with no target and no XP loss, while
run 8733 completed safe loot liquidation. Aeloria is checkpointed at 155,625
XP; the stale empty-packet repair remains offline-verified and still lacks a
loot-bearing live reproduction. These are continuation records, not subclass
or HERO proof.

Run 8734 completed bounded sanctuary provisioning for Aeloria and restored a
purple reserve without combat loss. Run 8735 completed safe liquidation; run
8736 continued Dorrik's level-24 Mirror Realm probe; and run 8737 completed
Aeloria's healer return. The source-gated one-action finisher added focused
starter coverage and passes the full offline suite, but its first independent
live target validation remains open. These are runtime and continuation
records, not subclass or HERO proof.
Run 8738 added a final safe liquidation checkpoint at 26524 without XP change.

The current engineering blocker was a registered research route that lost its
`where` locator hazard during campaign reconciliation and could be selected
again indefinitely. The merge now preserves that hazard for registered probes,
with regression coverage for both registered and source-ranked routes. Live
runs 8658-8669 then completed bounded warrior and cleric rotations safely;
Praelarran crossed level 7, while Corararfen recorded additional source-backed
early-band kills. Aeloria and Dorrik both honored current-band crowd gates. The
next executable proof boundary remains level 10.
Revision 173 also restores the missing `retryable_failure` marker for
source-ranked runtime, locator, and watchdog route boundaries so automatic
reset recovery can clear their cooldowns. Live run 8673 validated that repair
safely, recording 150 incidental transit XP but no objective kill before the
route cap. This is scheduler and liveness evidence, not level-25 or HERO proof.
Live runs 8674-8676 then continued the early class rotation without death or
XP loss: Praelarran added a 191-XP objective hermit kill and later honored a
Circus crowd, while Corararfen completed a bounded source-ranked Gnome absence
probe. These are early-band continuation records, not level-10 or HERO proof.
Runs 8677-8690 then continued the same rotation with no death: Praelarran
confirmed two Circus kills for 200 objective XP and completed safe ring and
flight maintenance; Corararfen confirmed an 89-XP Circus huckster kill and
recorded a separate cult absence; Aeloria confirmed a 100-XP Moria hobgoblin
kill and a 70-XP funding orc kill, while safely recording centaur and Shadow
Keep crowd/absence outcomes. Run 8678 reached the old cleanup boundary; the
new controlled-cap path then completed runs 8679-8685 normally. These remain
continuation evidence, not level-10, subclass, or HERO proof.
Runs 8691-8696 then continued without death: Praelarran recorded a cult
absence and a crowded Circus endpoint, while Corararfen recorded a separate
Circus absence. Aeloria added another 90-XP Moria hobgoblin kill and completed
flight maintenance safely, then rejected a below-band nomad commander after a
90-XP incidental drider transit kill. These remain early-band continuation
evidence.
Runs 8699-8702 then continued Aeloria without a death: the Eastern Desert
route recorded a bounded 10-XP net loss after an incidental drider, sanctuary
recovery killed a large hobgoblin for 90 XP, and a source-matched Highland
Keeper kill added 402 objective XP and crossed her to level 18. She returned
safely to healer room 3054 with one verified purple reserve. This is executable
level-band continuation evidence, not subclass or HERO proof.

Runs 8634-8651 continued Praelarran's bounded Cult, Circus, daycare, and source-
ranked rotations without death or XP loss. Direct run 8646 reproduced DD4's
selector-only text combat-start packet ordering, preserved the authoritative
source VNUM 1524, killed `a hermit` for 304 objective XP, and returned safely.
The campaign reconciled that live state through checkpoint 26276. Corararfen's
run 8652 and Dorrik's run 8653 also completed bounded rotations safely. This is live
source-identity and level-6 continuation evidence, not level-7, level-10,
subclass, or HERO proof. Runs 8621-8625 and 8641 also retain cross-class cleric
continuation evidence, while Dorrik's latest bounded frontier remains safe
level-24 evidence rather than level-25, subclass, or HERO proof.
The level-aware crowd repair ignored Dorrik's stale level-19 Eastern Desert
crowd and exposed the real level-24 Tentusks crowd. One bounded reset retry
rotated that current-band wait to an Arachnos cooldown at checkpoint 25956,
with no XP loss, duplicate segment, death, or worker left behind. Run 8529 then
exposed a silent pre-login socket while resuming Dorrik: DD accepted TCP but
sent no Telnet greeting. The bounded runner stopped safely at checkpoint 26038
and the repaired watchdog no longer sends gameplay recovery before
authentication. The current frontier is safe liveness evidence, not level-25,
subclass, or HERO proof.
Run 8530 then completed Dorrik's mirror-realm gardener probe, returning him
safely at level 24 and 360,901 XP; the 10-XP incidental increase is not
objective progression. Later checks recorded the Tentusks crowd and rotated
to an Arachnos current-reboot cooldown after an explicit reset retry. Velnor
runs 8531-8540 added 1,250 XP without a death. Corararfen and Praelarran both
reached safe level-6 empty-arena boundaries. These are continuation and reset
evidence, not level-25, subclass, or HERO proof.
Velnor's runs 8544-8564 continued the source-backed early cleric rotation
without death or manual steering. He crossed from level 5 to level 6 at
checkpoint 26079 with 14,201 XP and continued through checkpoint 26101 at
14,687 XP after level-6 kills and recovery. Corararfen's run 8567 killed the source-matched Bearded Lady for 64
objective XP and left her safely at checkpoint 26090 with 15,275 XP; the
following cult probe was a bounded zero-XP result at checkpoint 26092. This is
live level-6 continuation evidence, not level-10, subclass, or HERO proof.
Run 8571 then completed Dorrik's reset-aware mirror-realm gardener probe at
checkpoint 26097 without objective XP; the next selector invocation recorded
the Tentusks crowd at checkpoint 26099 and stopped before combat. Velnor's
latest safe return-home is checkpoint 26101 at 14,687 XP. These are current-band
continuation and crowd-gate records, not level-25, subclass, or HERO proof.
Runs 8574-8583 continued Velnor through the level-6 source frontier without
death and honored a below-band `consider` result at checkpoint 26119. Runs
8584-8585 recorded Corararfen's Circus crowd and below-band boundaries at
checkpoint 26123. Praelarran's runs 8586-8599 added 526 XP without death,
including two source-matched Bearded Lady kills and a Shire bull kill; he is
alive at checkpoint 26148 with 15,604 XP. The latest bounded higher-band
invocations preserved Dorrik's Tentusks crowd, Kestrel's fame-service cooldown,
and Aeloria's Fleshmonger crowd. These are current-band continuation and
safe-stop records, not level-25, subclass, or HERO proof.
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
transition and left checkpoint 26001 safely awaiting an arena reset. Runs
8495-8500 advanced Velnor through three source-backed Mud School batches for
708 net XP, crossing him to level 5 at checkpoint 26007 in healer room 3054.
These are early-cleric progression records, not level-10 or HERO proof.
Runs 8501-8510 then added 579 net XP to Velnor through recovery, daycare-ring
maintenance, and six further Mud School kills. Checkpoint 26017 leaves him
alive in healer room 3054 at 10,789 XP; this remains early-cleric progression
evidence, not level-10 or HERO proof.
Runs 8517-8519 then added 312 net XP to Velnor across six Mud School kills
before checkpoint 26026 recorded an empty arena. Runs 8520-8525 added 487 net
XP to Corararfen through two further Mud School batches, recovery, and
maintenance; checkpoint 26032 leaves her alive at 15,006 XP. These remain
early-cleric progression records, not level-10 or HERO proof.
Run 8528 completed Corararfen's daycare-ring recovery and left her full at
checkpoint 26035 with 15,098 XP. This is a safe maintenance boundary for the
next verified level-6 segment, not level-10 or HERO proof.
Runs 8511-8516 then added 1,074 net XP through four further Mud School
segments, a safe return-home, and daycare-ring maintenance. Checkpoint 26023
leaves Velnor alive in healer room 3054 at 11,863 XP; this remains early-cleric
progression evidence, not level-10 or HERO proof.

Runs 8437-8448 then continued the bounded rotation. Run 8444 reproduced a
same-policy Mirror Realm gardener research handoff after startup reconciliation;
the selector now requires the next research policy to differ from
`campaign_last_policy`. Run 8445 completed Kestrel's sanctuary recovery. Run
8446 rotated Dorrik to the source-ranked Shire Keeper route, reached the
180-second liveness boundary, and returned safely without an endpoint kill, XP
loss, or death. Run 8447 then rejected a wandering target outside the
source-safe relocation graph and returned safely. Run 8448 completed a fresh
source-ranked Mirror Realm probe and returned to healer room 3054 without an
objective kill. All returns were safe, no objective XP was added, and no
campaign worker remains active. The level-17 frontier is currently waiting on
fresh source evidence; this is not level-18, subclass, or HERO proof.

Runs 8418-8427 continued the level-17 source frontier. The selector probed
Bardoosh and honored its live-negative `consider`, then killed source mobile
6310, the Bird Spider, for 369 objective XP. A following zero-XP Bird Spider
result exposed a repeatability defect; current low-reward results now block
older source-history carryover, while a separate best-reward index still allows
a new level-specific policy one bounded live probe. Hood and Wyvern were
absent, and Shadow Keep was crowd-exhausted; all returns were safe. The
pre-probe checkpoint 25861 was authoritative, the source revision is
`7996722bc43508cc3773c48f8d79e3d07d68e5e4`, and no worker remains active. The
full offline suite passes 2,831 tests after this repair. The mage reserve gate
is now candidate-specific: clean source targets can use the existing purple
reserve, while blindness-capable caster specials still require a second purple
or a trained cure. This repair is offline-verified and awaits a fresh live
target after the current reboot cooldowns. Reset-aware run 8425 found source
undead soldiers present in Shadow Keep but crowded; run 8426 confirmed the
Wyvern centaur-chief target absent; and run 8427 confirmed the Hood gang leader
target absent. A further reset-aware continuation returned safely without
combat or XP change. The reset-wait selector now ignores prior-level source
cooldowns, so an old level-15 Ambush record cannot block the current level-17
frontier. Run 8428 then opened the bounded dynamic-wanderer research fallback,
reached source mobile 11518 in Highland room 11536, used the mage familiar
opener, and killed the Keeper of the Tower for 638 objective XP before returning
safely to the healer at checkpoint 25863. Run 8429 then repeated the same
bounded route, killed the Keeper of the Tower for 477 objective XP, and returned
safely at checkpoint 25866. Run 8430 then rotated to the Hood route, recorded
the gang-leader target absent, and returned safely at checkpoint 25869. Run 8431
then recorded a crowded Shadow Keep route without combat, and run 8432 killed
source mobile 11512 in Highland room 11530 for 492 objective XP before
returning safely at checkpoint 25877. Run 8433 completed flight maintenance
without XP change; run 8434 found the Wyvern target absent, and the bounded
reset retry then left no fresh current-band route available at checkpoint
25886. This is level-17 continuation and selector evidence
with two live productive research probes, not level-18, subclass, or HERO
progression proof.

The level-17 frontier now has a bounded research fallback for a source-clean
Keeper route whose only rejection is a reachable aggressive wanderer. It is
allowed only after the ordinary no-progress threshold, with a source peak
below current HP and no special procedure. The fastwalk still requires one
exact isolated target and records a crowd withdrawal if the wanderer appears;
the first repeatability result was also safe and productive; its one-shot
same-reboot allowance is now consumed, while promotion still requires the
remaining research criteria.

Runs 8396-8406 live-validated bounded absence, reset, crowd, reserve, flight,
and return-home rotation. Run 8399 killed source mobile 6506, the Dwarven
giant, for 514 objective XP and returned safely. Run 8400 confirmed the
Olympus jailer absent; run 8401 reacquired a verified purple sanctuary potion
for 110 recovery XP; runs 8402-8403 confirmed Hood and Wyvern targets absent;
run 8404 restored flight; and run 8406 safely recorded a crowded Dwarven room
without a new kill, XP loss, or death. The
startup migration then exposed a convergence defect: an older no-kill circuit
record could downgrade a newer confirmed source kill, causing alternating
metadata checkpoints and a misleading Fleshmonger wait. The repair preserves
current-reboot confirmed objective results and is covered by a reconnect
regression. Checkpoint 25781 is the latest safe state. This is level-17
continuation and repair evidence, not a level-18,
subclass, or HERO claim.

Run 8394 exposed a cleanup edge after the source-matched Moria large
hobgoblin kill: a stale enemy prevented the normal required-loot cleanup from
stowing the recovered purple potion, leaving the reserve loose in inventory.
The new verified `audit-combat-pouch` maintenance policy completed in run 8395,
returned Aeloria safely through recall to healer room 3054, and confirmed both
the combat-pouch and verified-reserve counters without another connection to a
field target. Checkpoints 25693 and 25698 then preserved a crowded frontier and
one automatic reset wait; no source-safe current-band route was available under
the current reboot cooldowns. This is level-17 continuation and repair
evidence, not level-18, subclass, or HERO proof.

Runs 8386-8388 recorded a Shadow Keep crowd, an absent centaur chief, and a
below-band wormkin. Run 8389 found the source giant eel present and
consider-viable, then exposed that the field executor still used a zero-level
source-fuzz ceiling. The audited lightning-breath path now has a shared +2
ceiling under sanctuary and direct-HP bounds; startup migration reopens only
the stale eel result and persists a policy-specific marker until a fresh field
segment starts. Checkpoints 25630-25641 verified the migration and one bounded
180-second reset wait, but subsequent Fleshmonger crowd and Hood absence
evidence prevented direct eel combat revalidation. This is level-17 repair and
continuation evidence, not level-18, subclass, or HERO proof.

Runs 8379-8380 exercised the source-ranked Forest route: a live medicine man
was found wandering outside the reset room, the runner immediately refreshed
`where` after the crowd result, and it returned safely without XP change. Run
8381 then identified Arachnos mobile 6317, quaffed sanctuary, survived its gas
breath and nausea effect, and killed it for 708 objective XP before recalling
and sleeping at the healer. The trace showed that DD4 reports this poison as a
`nausea` affect with `gives: poison`; the runner now recognizes both fields,
recalls from a recallable field room on the next prompt, and remains asleep at
the healer until the poison clears. Runs 8382-8383 completed coin banking and
poison recovery with no death or XP loss. This is level-17 safety and source
evidence, not level-18, subclass, or HERO proof.

Run 8384 then killed the source-matched Moria large hobgoblin for 110 XP and
secured its purple potion, but a separate live warrior with source VNUM 4050
remained reported before corpse cleanup. The old guard recalled without first
issuing `consider`, costing 208 XP; the character survived and returned safely
for a net 98-XP loss. The post-objective consider handler now precedes that
generic guard, and a regression models the exact 4055-carrier plus 4050-warrior
pattern. Run 8385 selected the next source-ranked gang-leader route, found it
absent, and returned safely without another loss. Direct live re-entry through
the repaired Moria branch remains pending, so this is repair and continuation
evidence rather than level-18 or HERO proof.

The source audit now models `spec_cast_undead` as a level-aware combat-only
special. It may enter the executable frontier only when the source ceiling is
below level 15, its chill/blindness damage remains below the character's HP
reserve, and a blindness-capable branch has a verified cure reserve. Energy
drain, harm, and gate branches remain research-only. The post-audit bounded
Aeloria invocation preserved the existing `restock-provisions` crowd safe-stop
in seven seconds without opening a connection or clearing reboot evidence.
Run 8377 then executed the source-ranked Wyvern's Tower route for the level-14
centaur chief, recorded a source-verified absence, and returned Aeloria safely
to healer room 3054 without XP change. Run 8378 completed flight maintenance;
the following normal invocation preserved the absence without creating a
duplicate run. The selector now requires one verified purple for a
non-sanctuary undead-special blindness cure, while caster specials that spend
sanctuary retain the two-purple boundary. This is live level-17 continuation
and selector evidence, not level-18, subclass, or HERO proof.

Run 8364 live-tested the newly admitted sanctuary-aware Fleshmonger route. The
source special blinded Aeloria and the area's `greet_prog` forced its senior
guard to attack; the runner withdrew safely after a net 179-XP loss and
consumed both purple reserves. Source parsing now records mobile-program
`mpkill` hazards and rejects scripted targets or companions before combat. Run
8365 then rotated to the registered Crystalmir white-stag probe, confirmed the
source target absent, and returned Aeloria full to healer room 3054 with no
further XP change. This is level-17 selector and safety evidence, not a clean
level-18, subclass, or HERO progression claim.

Runs 8366-8367 reproduced the Moria required-loot cleanup hazard: the carrier
was killed, but a source-poison snake or an unmodelled pursuer was treated as a
reason to flee before corpse cleanup, costing XP. The bounded poison-pursuer
exception and authoritative post-kill cleanup state are now covered by focused
tests. Run 8368 recorded a safe Shadow Keep absence; run 8369 completed
provision maintenance; runs 8370-8371 recorded a safe jailer absence and a
non-corporeal Dwarven servant rejection. Run 8372 exposed an ANSI reset before
the MUD's target selector, causing a live Moria target to be missed and costing
208 XP; the parser now strips presentation bytes before matching selectors.
Run 8373 then killed the source giant for 533 XP without loss. Run 8374
confirmed the selector repair but exposed the cleanup guard's over-broad
response to a source-known below-band warrior; the guard now tolerates such
bystanders while retaining the unmodelled-pursuer stop. Direct live validation
of that final cleanup refinement is waiting on the current restock cooldown.
This is level-17 continuation and repair evidence, not level-18, subclass, or
HERO proof.

Run 8375 completed Velnor's next Mud School segment and left the cleric at
level 4, 9,502 XP, full in healer room 3054 with no death. Run 8376 stopped
Brannor before connection because no stored character credential exists; no
live character state changed. These are useful class-continuation and
credential-boundary records, not HERO proof.

Runs 8360-8363 then killed source giant mobile 6506 for 787 objective XP,
exposed a failed combat recall followed by an immediate duplicate recall
(-168 net XP, no death), and completed safe Hood-absence and flight-maintenance
segments. The recall state machine now records the failed attempt and chooses
one bounded flee/recovery path instead of repeating recall. The automatic reset
retry then stopped honestly on current-reboot cooldown evidence, leaving the
campaign safe at level 17; this is continuation and repair evidence, not
level-18, subclass, or HERO proof.

Runs 8340-8341 and 8348 supplied Velnor with 587 verified Mud School XP before
run 8349 recorded the arena empty and waited for reset. Run 8351 supplied
Praelarran with 110 verified XP from a wild boar and wolf; run 8352 confirmed
the same empty-arena boundary, and run 8353 completed Velnor's safe healer
return. Runs 8354-8355 reproduced the Moria post-objective warrior loss and
then restored the sanctuary reserve. The fixed branch now considers an exact
live selector before fleeing even when the route is a consider-only recovery
probe. Run 8356 exposed the related protected-peak executor ceiling: the
selector admitted Dwarven servant mobile 20505, but the field stop still
rejected its source range 15-19 at level 17. Protected peak stops now carry a
verified +2 source-fuzz ceiling only when sanctuary reserve and half-damage
proof are present. Runs 8357-8359 rotated safely through Arachnos, reserve
recovery, and an absent Shadow Keep Undead Soldier; Aeloria ended at 150,498 XP
with two reserves and no death. The live combat triggers for both repairs remain
pending, so these are level-17 continuation and safety records, not level-18,
subclass, or HERO proof.

Runs 8310-8316 exposed and repaired a level-16-plus mage reserve defect. The
second-purple reserve gate now counts an audited pouch potion, requires two
purple potions, requires invisibility for the Moria acquisition route, and
preserves the first potion while acquiring the second. Run 8312 restored two
reserves; run 8313 killed Grove druid mobile 8902 for 835 XP; run 8315 restored
two reserves again; and run 8316 killed Arachnos guardian mobile 6367 for 821
XP. Aeloria ended safely with one purple reserve and no death or XP loss. This
is level-17 continuation and protection evidence, not level-18, subclass, or
HERO progression proof. Run 8328 exposed a remaining post-objective escape
defect: a useful-band warrior joined after a Moria carrier kill, and fleeing
cost 208 XP. DD4 source confirms that successful flee and combat recall both
charge the same level-scaled loss. The runner now uses an exact live selector
to consider an unknown attacker before paying that cost, and directly recalls
from audited hazards. Run 8329 live-validated the repaired ordinary Arachnos
route with 566 XP and no death or XP loss; the post-objective warrior branch
was not triggered, so its direct live validation remains pending.
Runs 8331-8332 then added one clean 568-XP Arachnos guardian kill and one
neutral Crystalmir probe. Run 8333 was reconciled after an operator stop; run
8334 exposed a second-order Moria defect where repeated Char.Enemies rows for
the exact source-bound below-band carrier were counted as a crowd, costing 208
XP without a death or objective kill. The repair permits that duplicate packet
only for exact required-loot carriers and remains conservative for ordinary XP
hunts. Runs 8335-8336 completed flight maintenance and a Hood probe without XP
change. Direct live revalidation is deferred until the current recovery
cooldown clears, so Aeloria's current checkpoint is level 17 at 150,396 XP,
full in healer room 3054 with no active worker or verified combat-pouch reserve.

Runs 8240-8243 repaired a bounded Kestrel provisioning timeout. Runs 8244-8249
exposed a negative-reputation Magic Shop refusal loop; the selector now records
the refusal and stops with a level-scoped `unavailable` result when the remaining
frontier is flight-only, rather than retrying the shop or funding route. Runs
8250-8252 live-validated that boundary: Kestrel took the non-shop Mirror Realm
fame route, withdrew safely from an overmatched moose for a net 111 XP loss,
then reacquired purple sanctuary and returned to healer room 3054 at level 24
and 336,913 XP. The campaign remains resumable, but this is safety and selector
evidence rather than level-25 or HERO progression proof.

The latest bounded Aeloria invocation ended safely while the current-band route
waited on its reboot-local reset cooldown. Run 8253 advanced Velnor, a human
cleric, to level 4 at 6,839 XP through the verified Mud School segment and
returned him safely to healer room 3054. Runs 8260-8261 added 141 XP in two
more bounded segments and exited without an unnecessary reset wait. Run 8266
then added 267 XP through four Mud School kills. Runs 8267-8269 advanced Velnor
to 8,177 XP before the reboot-local arena-empty gate. The next useful work
remains a fresh source candidate for Aeloria or Praelarran, plus continued class
rotation.
Runs 8262-8263 gave Kestrel a source cure-critical reserve and safely rejected
the Circus fame target without combat or XP change. Dorrik's next source-ranked
probe found the Eastern Desert crowded and returned him safely. These are
continuation and safety records, not level-25 or HERO proof.
Runs 8270-8274 continued Velnor to 8,747 XP before the reboot-local Mud School
arena-empty gate. Runs 8275-8285 continued Corararfen through safe maintenance
and Mud School rotations to 9,991 XP, leaving only 59 XP to level 5. The source
mirror was refreshed and remained at revision 7996722. No campaign worker was
left running after the bounded invocations. Runs 8286-8287 then crossed
Corararfen to level 5 at 10,225 XP through another verified Mud School rotation.
Runs 8288-8290 completed outfit, healer, and daycare-ring maintenance, adding
82 incidental XP and leaving him at 10,307 XP with full HP and mana in healer
room 3054; no death occurred.

Runs 8291-8294 continued Corararfen through bounded Mud School and daycare
maintenance, adding 532 XP in total and leaving her at level 5 with 10,839 XP,
full HP and mana, and a healer-room checkpoint. Runs 8295-8296 then live-
validated the new level-6 source-ranked fallback for Praelarran: run 8295
killed the source-matched Bearded Lady (mobile 4406) for 108 objective XP and
returned safely; run 8296 rotated to the Cult fanatic route, recorded its exact
target absent, and returned without combat or XP loss. The campaign suite now
passes 842 tests; the full offline suite passes 2,782 tests. This removes the
early fallback blocker but is not level-10, subclass, or HERO proof.

Runs 8297-8299 continued Praelarran's source-ranked Circus rotation without a
death, and run 8300 exercised the public HERO `--retry-stalled` option through
the explicit canonical workspace. Runs 8301-8302 then added 103 XP from the
Bearded Lady and 274 XP from the Shire bull, leaving Praelarran safely at
level 6 and 14,885 XP. The early fallback now has its own
`source-ranked-hunt-6-10` evidence identity. The Aeloria reset retry and
retry-stalled invocation both preserved the active reboot-local Ambush
cooldown. This confirms bounded public and early-band behavior, but does not
claim level-10, subclass, or HERO progression.

Runs 8026-8048 and 8075-8090 continue Aeloria's source-ranked level-17 work,
including Moria sanctuary recovery, Arachnos and Dwarven kills, bounded route
withdrawals, and the repaired post-objective poison escape. Run 8101 exposed
an actual Kestrel death: the Circus ticket clerk's `built like a tank` consider
warning was not rejected, and XP fell from 345,681 to 336,616 before Purgatory
recovery. The new hard consider gate and failed-flee recall fallback are
covered by regressions. Run 8102 live-validated the tank-warning rejection
without combat or death; run 8103 reacquired Moria sanctuary for 110 XP, and
run 8104 completed a safe food-reserve segment. Runs 8105-8111 then completed
flight, forest gear, funding, liquidation, and safe return-home maintenance;
run 8109 added 70 XP from a source-backed John the Lumberjack funding kill. The
next progression target is level 18, followed by executable class-aware
level-1-30 proof and the level-30 subclass transition. These checkpoints are
continuation evidence, not HERO or subclass proof.

Runs 8112-8115 recorded Kestrel's bounded fame withdrawal, crowded Moria
checkpoint, successful stalled-candidate retry for a 110-XP large hobgoblin
kill and purple sanctuary recovery, and absent gnome-guard probe. Runs
8116-8126 advanced Velnor's cleric through verified arena kills to level 3;
run 8118 correctly stopped the unrelated Brannor scaffold at its missing
credential boundary. Runs 8127-8149 created and advanced Praelarran, a fresh
human warrior with generated credentials, an anti-machine title, and a stored
backstory, to level 4 using the bounded Mud School reset wait. Runs 8150-8201
then crossed level 5 and continued through reset-aware arena and maintenance
segments without death. Runs 8214-8223 crossed level 6. Run 8224 exposed the
mixed live-consider arena bug; policy revision 170 now keeps a viable target
when a bystander is below-band, with a migration and regressions. Runs
8226-8228 revalidated the arena and recorded both targets below-band; run 8229
then completed a safe absent Dragon Cult fanatic probe. None of these records
is level-10, subclass, or HERO proof.

## Current Assessment (2026-08-21)

The first five practical milestones are complete as foundations. Async Telnet,
GMCP, transcripts, SQLite state, YAML profiles, deterministic starter behavior,
reports, checkpoints, bounded segments, and death/recovery handling are in use.
The round-robin matrix now accepts `--max-segment-runtime`, carrying the same
finite live-session boundary into multi-character rotation so a reboot-scoped
absence or crowd wait cannot monopolize the worker.
Campaign inspection now uses summary-only segment queries, keeping durable
monitoring responsive as long-running HERO histories grow.
Negative-reputation service refusals are now terminal for the current flight-only
frontier: a failed Magic Shop purchase and consumed flight loan cannot reopen a
shop or funding loop. A separate bounded non-shop route may still run when it is
source-verified and executable; otherwise the campaign waits for new reboot or
fame evidence.
Reset-aware continuation now uses the source-backed empty-area interval: after a
safe healer return, an automatic retry waits 180 seconds before consuming
reboot-local absence or crowd evidence. Bounded live invocations remain
non-blocking unless reset retries are explicitly enabled.
The level-16 protection blocker is now class-aware: mages may enter the
source-backed Moria deep carrier probe only after the existing bounded
invisibility readiness gate, while thieves and other non-invisible classes
retain the reset-room-only boundary until level 19. Runs 7833-7843 exercised
the reset handoff and recorded safe Ambush, Shadow Keep, New Ofcol, Haon Dor,
and Moria observations. Run 7844 live-validated the mage path through the
source snake room and acquired purple sanctuary potion VNUM 4050. Run 7845
then spent that reserve on an audited ranger fight for 445 XP without death or
XP loss; run 7848 safely attempted replenishment but found the carrier absent.
Runs 7849-7850 added safe no-progress observations. The selector now permits a
fresh level-16+ fixed non-combat research probe while sanctuary recovery is on
cooldown, without overriding live absence, crowd, or cleared-policy evidence.
Run 7853 selected the source-ranked New Ofcol jack at room 617, confirmed it
absent, and returned Aeloria safely at full HP and mana without XP change. The
level-17 frontier and repeatable reserve lifecycle remain evidence-gated.
Runs 7892-7893 then exposed a real runtime-boundary safety defect: a Moria
snake poisoned Aeloria, she fled at 1 HP, and cleanup attempted recall after
DD4 had moved her to POS_INCAP. The bot waited through the resulting death,
recovered the corpse through Purgatory, and returned to healer room 3054 at a
cost of 3,799 XP. The repair now recalls immediately on active poison while
recallable, raises the no-recall poison withdrawal floor, and refuses commands
or logout while stunned or worse. Offline regression coverage is complete;
Runs 7894-7898 then exercised the repaired return machinery through a safe
Shadow Keep absence probe, an elite-goblin kill, loot liquidation, return-home,
and a Crystalmir probe. All five segments completed without another death or
XP loss and left Aeloria full in healer room 3054. The exact poisoned-Moria
trigger did not recur, so the repair is live-validated for ordinary post-field
cleanup but remains explicitly pending direct re-entry through that poison
encounter.
Run 7900 then exercised the repaired wandering-carrier locator through the
ordinary campaign selector. The live `where hobgoblin` response named `The
maze` and `The large cave`; the source-approved waypoint sweep found the maze
carrier at room 4057, killed it for 90 XP, acquired purple sanctuary potion
VNUM 4050, stored it in the combat pouch, and returned safely to healer room
3054. The one-time policy revision migration reopened only the old retryable
sanctuary result. This is fresh level-16 resource and route evidence, not
level-17, subclass, or HERO proof.
Run 7907 then repeated the ordinary sanctuary route and acquired the same
source-matched potion for 100 XP. Runs 7908-7910 completed safe absence,
funding, and flight maintenance. Runs 7911-7913 added a safe guardian pass,
another 90-XP sanctuary acquisition, and a 559-XP elite-guard kill, all without
death or XP loss. Runs 7914-7933 and 7937-7945 continued bounded source-ranked
level-16 rotations, including sanctuary recovery, maintenance, and productive
current-band kills. The valid checkpoint is now level 16 at 133,310 XP in
healer room 3054. Run 7946 is quarantined: an interleaved immortal-arrival
GMCP snapshot for another character supplied an impossible level-106 payload
and falsely triggered the wrapper's completion message. Identity-bound GMCP
parsing and impossible-progress validation now reject that evidence, and the
campaign resumes from the valid checkpoint. The next work item remains the
evidence-gated level-17 transition. Run 7948 exposed a crowd-state defect and
cost 188 XP; run 7949 confirmed a Crystalmir absence. Run 7950 then live-
validated the source-aware repair by killing the carrier for 100 XP and the
incidental orc for 80 XP, acquiring the purple potion, and returning safely
without another retreat loss. Run 7952 then exposed a separate pre-repair
ordering hazard: source mobile 4053, the sickly brown snake with
`spec_poison`, remained after the carrier kill and the poison gate acted too
late. The runner now indexes specials by mobile VNUM and recalls before an
audited post-objective poison, direct-damage, cleric, or mage special. Runs
7953-7955 then completed flight maintenance and two source absences safely.
Direct live validation of the new poison boundary remains the next field task.
Run 7956 then killed source mobile 6310, the Bird Spider, for 548 objective XP
and returned safely without death or XP loss. Run 7957 recorded an absent source
druidess and returned safely. Run 7958 repeated the source-matched Moria
carrier route, killed mobile 4055 for 90 XP, acquired the purple sanctuary
potion, and returned safely. Run 7959 reached the Dwarven Homestead nobleman,
withdrew at the existing health floor, and paid 188 XP without dying. Aeloria
is now level 16 at 133,293 XP, 307 XP short of level 17. Run 7960 then killed
the source-matched large hobgoblin for 100 XP and the joining warrior for 80
XP, recovered and pouched the purple sanctuary potion, sacrificed the emptied
corpse, and returned safely without death or XP loss. Aeloria is now level 16
at 133,473 XP, 127 XP short of level 17. Run 7961 then killed source mobile
6310, the Bird Spider, for 484 total XP, including a critical hit and the
level-up to 17. The level-up granted 8 HP, 31 mana, 10 movement, 2 physical
practices, and 4 intellectual practices; Aeloria returned full to healer room
3054 without death or XP loss. She is now level 17 at 133,957 XP. Run 7962 then
reached the Crystalmir Lake endpoint, issued the source-backed `where stag`
search, found no White Stag, and returned safely to healer room 3054 with XP
unchanged. Run 7963 then bought and quaffed a light blue flight potion for 30
reboot-local copper, confirmed the fly affect, and returned full to the healer
with XP unchanged. Run 7965 then killed source mobile 4055 for 100 XP,
recovered and pouched the purple sanctuary potion, sacrificed the corpse, and
returned safely. A nearby source snake and wandering warriors were observed
but not attacked; the post-objective hazard guard was not triggered. Aeloria
is level 17 at 134,057 XP with 20,393 XP to level 18. Run 7967 then
source-located Aruncus the Druid, considered him an easy kill, used the mage
familiar as the opener, and earned 169 total XP including a critical hit.
Aeloria collected the druidic staff and other drops, sacrificed the corpse for
silver, and returned full to healer room 3054. She is now level 17 at 134,178
XP with 20,272 XP to level 18. This is fresh level-17 continuation and
maintenance evidence, not subclass or HERO proof. Run 7968 safely handled a
cursed amulet but the live Magic Shop rejected a source scroll despite matching
source metadata; this is a runtime-state sale discrepancy, not a reason to
guess a new shop route. Runs 7969-7970 safely recorded a crowded Moria circuit
and a below-band secretary. Run 7971 showed that a live level-13 ranger can
outlast an unprotected mage despite a useful consider result; Aeloria withdrew
at 43/209 HP for a 48 XP net loss and returned full to healer room 3054. The
exact Wyvern's Tower policy is quarantined for this reboot. Aeloria is now
level 17 at 134,178 XP with 20,272 XP to level 18. This is fresh level-17
combat-boundary evidence, not subclass or HERO proof. Runs 7972-7975 completed
rearm, liquidation, and provision maintenance safely. Run 7973 killed source
mobile 300, Aruncus the Druid, for 246 objective XP. Run 7976 killed source
mobile 6310, the Bird Spider, safely but received 0 XP; the evidence now records
`low_reward=true`, and the selector excludes that route from productive repeats.
Run 7977 rotated to source mobile 1131, the Shire receptionist, received a
negative live consider, and skipped safely. Runs 7978-8002 then rotated through
negative considers, source identity ambiguity, coin-stash funding, flight
maintenance, absence, and crowd gates without unsafe combat. Run 7988 killed
Fewmaster Toede for 277 objective XP; run 7997 killed the source giant for 495
objective XP. Runs 7992-7993 withdrew from the Arachnos guardian and Dwarven
Nobleman after their health floors, paying bounded 208 XP losses that
quarantined those exact policies. Run 8003 exposed a giant-room boundary with
two live guards and withdrew at 108/209 HP for 208 XP after 114 damage credit.
Run 8004 exposed an aggressive source poison target loaded at live level 10
being admitted through the audited-special fallback at level 17; it withdrew
safely but lost 208 XP. The selector now blocks aggressive source targets whose
minimum fuzz level is below the useful-XP floor, including special procedures.
Aeloria is now level 17 at 134,806 XP with 19,644 XP to level 18, full in
healer room 3054. The full offline suite passes 2,763 tests. This is fresh
level-17 boundary and repair evidence, not subclass or HERO proof; direct live
validation of the post-objective poison guard remains open. Runs 8005-8011 then
exercised the blocked-shop funding path: Shargugh, Jack, and the Eastern Desert
dervish were absent, while John the Lumberjack yielded 60 XP and 80 copper-
value of saleable gear before safe liquidation. The campaign stayed at level
17 with no death or XP loss. That live sequence exposed a liveness defect in
which productive funding kills could not age the flight retry cooldown because
funding is classified as maintenance. The repair now counts positive-XP funding
as productive for that cooldown; the full suite passes 2,765 tests. Direct live
revalidation is still required before this is progression proof.
Runs 8012-8017 then completed source-backed funding, liquidation, flight,
sanctuary, and guardian rotation; run 8017 added 822 XP without death or XP
loss. Run 8018 exposed a remaining Moria ordering gap: the required-loot
carrier died and yielded purple sanctuary potion VNUM 4050, but source mobile
4053, the `spec_poison` snake, was already present and was detected only after
combat began, costing 208 XP on recall. The endpoint gate now resolves audited
special bystanders before required-loot combat and recalls before combat when
such a hazard is present; the full offline suite passes 2,766 tests. Run 8019
then skipped a crowded Dwarven Home endpoint before combat and returned Aeloria
safely to healer room 3054 at level 17 and 135,850 XP. Direct live validation
of the new pre-combat Moria gate remains open; this is repair evidence, not a
level-18, subclass, or HERO claim.
The live level-10 matrix is complete for mage, thief, and warrior. The checked-in
`matrices/level-10-all-race-class.yaml` now declares all 225 source-legal
race/class pairs for the next validation phase; declarations remain distinct
from live level-10 proof. The current
representative campaigns are Aeloria mage level 17 at 135,850 XP, Dorrik warrior
level 24 at 360,891 XP, Kestrel thief level 24 at 345,798 XP, and Corararfen
cleric level 4 at 7,841 XP. The durable Aeloria, Dorrik, and Kestrel campaign
horizons are restored to target level 100; their current levels are progress
checkpoints, not completion claims. Aeloria's latest live checkpoint is healer
room 3054 at 209/209 HP, 593/593 mana, and 298/310 movement. The full offline
suite passes 2,766 tests.
The
progression selector now exposes a
research-status generic source-ranked handoff at level 11 for tutorial-arena
classes after their level-10 scout; explicit level-12 through level-80 bands
remain authoritative, and level 81+ uses the same frontier. Corararfen is the
human cleric validation campaign at level 4; its later bounded continuation
returned safely to healer room 3054 at 7,841 XP after recovering an interrupted
Mud School boundary. This is early class coverage, not level-11 or HERO proof.
The latest automatic reset retry for Aeloria (run 7817) returned safely from
sanctuary recovery without XP or a level gain, preserving the explicit
protection marker. Campaign segment 7391 (run 7822) then selected the
independent Midgaard secretary route while sanctuary recovery was on cooldown,
earned 354 objective XP from source mobile 3142, and returned safely to healer
room 3054. The level-17 frontier is still an evidence-gated work item, not a
completed band; this run proves liveness of the fallback rather than HERO
progression. Segments 7392-7393 (runs 7823-7824) then recorded a live Haon Dor
absence and a bounded Ambush no-kill result, both returning Aeloria safely with
no XP change. The level-17 frontier is still an evidence-gated work item.
Shared campaign storage now
uses WAL plus immediate state-snapshot commits; a two-worker live overlap
completed without a database-lock failure. Named HERO resumes also search
nested validation workspaces by stored manifest identity. Fresh direct HERO entry-point
character Velnor is
checkpointed safely at level 2 after passwordless resume and early arena
continuations. The human psionic matrix character has also reached level 3;
the ranger and brawler rotations now add live level-4 and level-3 early-path
evidence while preserving their distinct primary/ranged and weaponless combat
rules. Aeloria's level-16 continuation now includes a revision-aware mage
trainer audit: run 7583 learned `faerie fire`, run 7584 cast it once before
repeated `chill touch` and earned 405 objective XP, and run 7585 added 483
objective XP from Aruncus. Run 7617 proved source-verified amber `cure light`
use at low combat health, then recorded a guardian hard-health-floor death
followed by successful corpse and healer recovery; that exact policy is now
protection-quarantined. Runs 7628-7669 continued with bounded current-band
rotation, maintenance, and recovery evidence. Run 7638 then proved the
source-backed outdoor mage familiar opener: Aeloria cast `summon familiar`,
grouped and ordered the level-15 pony onto an exact Bardoosh instance, earned
246 objective XP, and returned to healer room 3054 at full resources. Runs
7653, 7658, and 7665 repeated the same familiar-backed Bardoosh kill for 177,
233, and 191 objective XP with safe returns. Dorrik is
full at 542/542 HP with full mana and movement in healer room 3054, 5,209 XP
short of level 25; Aeloria is also full in healer room 3054 with 16,257 XP to
level 17. Runs 7495 and 7496 then completed bounded Aeloria and Kestrel
probes, returning both safely to healer room 3054 without objective XP. Dorrik
remains safe at level 24 while explicit timeout, protection, and cooldown
evidence blocks his remaining current-reboot routes. The source-ranked
no-progress fallback now remains available during ordinary resumptions after
all other safe pools are exhausted, without bypassing hard live evidence. On
2026-08-18, Aeloria run 7497 exposed and closed a generic caster-special
preflight mismatch: a blindness-capable target is now selected only when a
trained cure blindness capability or a two-purple reserve remains after the
sanctuary opener. The field runner's safe withdrawal and the source selector
now share the same executable recovery boundary. Run 7498 then selected a
source-matched Midgaard secretary for 315 objective XP and returned Aeloria
full to healer room 3054. The public HERO workspace then reused Aeloria's
stored credential and completed
runs 7499-7513 without manual steering. It safely rejected the Dwarven
Nobleman, Fleshmonger, and Mahntor routes when their live safety or route gates
failed, then completed Bardoosh mobile 4515 for 414 objective XP and Rock Toad
mobile 2303 for 756 objective XP and Aruncus mobile 300 for 519 objective XP.
Aeloria returned at 110,063 XP; this is
current-band entry-point evidence, not level-16, subclass, or HERO proof. Follow-up
runs 7515-7533 continued the same generic source-ranked rotation without
manual steering and left Aeloria full at 111,811 XP in healer room 3054. The
2026-08-17 Dorrik reconnect then settled checkpoint
22805 while retaining an explicit same-reboot crowded-route retirement; the
next reconnect created no new metadata checkpoint. The later live repair
converged Dorrik at checkpoint 23006, and its immediate repeat created no new
metadata row. Startup reconciliation is now idempotent, removing a restart
blocker. Shared SQLite writes use a bounded 30-second busy timeout so the
three-character rotation can overlap without transient lock failures. Each
campaign also claims an OS-backed lease before opening SQLite, so a duplicate
invocation fails immediately instead of recovering an active segment. The fixed
research registry now hands levels 81-100 to a research-status generic
source-ranked frontier, keeping the HERO path executable while later area
policies are researched; this is not verified HERO coverage. Kestrel run 7376
exposed a real
sanctuary-expiry death against a level-30 moose at 220/334 HP versus 410/535
HP; runs 7377-7379 completed corpse recovery, healer recovery, and a bounded
Moria sanctuary-reserve continuation. Run 7380 then deferred the fame route
as crowded without another fight. The shared protection-loss branch now uses
live player and opponent health before another attack. Runs 7381-7383 then
exposed a maintenance-state attribution bug: provision-funding and return-home
could overwrite the preceding field policy's transient fastwalk metadata. The
repair keeps new maintenance route hazards in a dedicated ledger, preserves
source-owned field evidence, and removes legacy unowned markers on resume;
Kestrel checkpoint 22899 live-confirmed the cleanup. This is checkpoint-
integrity evidence, not a HERO claim. Run 7384 then killed the source-matched
Midgaard secretary (mobile 3142) for 494 objective XP, moving Aeloria to
107,709 XP at level 15 before safe healer return. Runs 7385-7388 completed
healer return, an absent Shargugh locator, and liquidation without false XP.
Dorrik checkpoints 22908 and 22910 re-evaluated Highland and stopped on the
live crowd gate without XP. Run 7389 live-validated explicit `--retry-stalled`
recovery: the selector reopened the fresh Mirror Realm route, confirmed its
young-boy target absent through live GMCP, returned Dorrik safely to healer room
3054 at 360,891 XP, and persisted reboot-local absence evidence. A normal
invocation remains a safe stop while the remaining routes are blocked; retry
mode rotates to another fresh source-safe route. Run 7390 then completed that
rotation in SQLite before the outer wrapper timed out: the independent mirror
guardian route was live-crowded, made no XP claim, and returned safely. Dorrik
run 7391 then recorded Aeloria's New Ofcol target absent and returned her safely
at level 15 and 107,709 XP; Kestrel checkpoint 22941 preserved the fame-service
cooldown in healer room 3054. The retry-stalled boundary is now explicit:
current-reboot absence, crowd, route, and failed-viability evidence cannot be
cleared by an operator retry; only a retry marked after an observed area-reset
wait may consume it. Live checkpoints 22948-22954 retained Dorrik's Eastern
Desert crowd result at cooldown 3 and created no duplicate field segment or XP
claim. The campaign suite passes 818 tests and the full offline suite passes
2,678 tests. The next bounded rotation kept all three active characters safe
in healer room 3054: Dorrik checkpoint 22973 retained the Eastern Desert crowd
boundary at level 24 after a bounded reconnect without XP change, Aeloria
checkpoint 22979 completed buy-flight-potion maintenance at level 15, and
Kestrel checkpoint 22985 completed the follow-up return-home recovery at full
HP and mana. Productive routes with source-proven
non-combat specials may use one sanctuary-backed retry after one XP-loss
record; combat specials and repeated losses remain quarantined. Dorrik run
7104 added 1,852
objective XP before his current-reboot frontier exhausted. Aeloria run 7112
added 475 objective XP in Gremlin Lair, and run 7121 added 600 objective XP
from a source-matched Bird Spider. Run 7123 exposed a liquidation fight with a
city drunk and a net 138-XP loss; the utility dispatcher now flees before
below-band transit combat, with regression coverage. Run 7126 then recorded
108 incidental XP before a shared health-floor withdrawal and safe healer
return; no objective kill was confirmed. Kestrel run 7128 then added 90 XP from
the large hobgoblin, recovered purple sanctuary, and returned full after a
recovery-gear stance. Run 7130 then exposed an on-duty guard interruption on
the Fleshmonger route, costing 117 XP before a health-floor withdrawal; no
death or objective kill occurred, and the exact policy is now quarantined.
Run 7133 then recorded an 83-XP loss and a 23% health-floor withdrawal on the
Gizmo route; no death or objective kill occurred. Run 7136 then killed the
source-matched huge python for 375 verified XP and returned full after
chill-touch combat. Run 7137 then killed Bardoosh for 743 verified XP,
recovered a dagger after disarm, and returned full with four drops recorded.
Run 7141 then killed the large hobgoblin for 321 verified XP, recovered purple
sanctuary, and returned full. Run 7142 then used sanctuary, killed the
below-band Midget for 30 non-objective XP, and recovered its purse and coins
before a full healer return. Run 7145 then added 283 verified XP from the large
hobgoblin, recovered purple sanctuary, and returned at full health. Run 7149
then killed Bardoosh for 490 verified XP, maintained source-verified armor
protection, and returned full with three drops. Run 7155 then withdrew from
Bardoosh at 56% health and cost 40 XP without a kill; it was the exact policy's
second loss and is now quarantined. Run 7156 exposed that the Forest 80-stop
circuit could exceed the 250-command profile cap; the runner now derives a
finite 613-command allowance for it and reconciles the old failed checkpoint.
Runs 7157-7162 completed safe return, absence, funding, and flight-maintenance
segments. Runs 7163, 7166, and 7169 added 574, 280, and 371 objective XP from
Queen Wasp kills; the other bounded runs through 7172 returned safely without
false progress. Source-sensitive decisions use DD4 revision 7996722.
Runs 7220-7229 exposed and repaired exact gear identity and stale-room ordering
in the live rearm route. The validated continuation completed a Queen Wasp
kill for 374 objective XP, a Giant Kodiak bear kill for 280 XP, and crossed
Aeloria to level 15. Run 7231 added 528 objective XP from Bardoosh; runs 7230
and 7232-7235 then completed bounded level-15, maintenance, and no-objective
rotations safely. Run 7236 killed Aruncus the Druid for 413 objective XP and
returned safely to healer room 3054. Runs 7237-7270 then added 5,354 objective
XP from Bardoosh, Bird Spider, and Queen Wasp kills, offset by two source-policy
hard-floor withdrawals totaling 190 XP and 20 incidental XP; no death occurred.
Aeloria is now 12,917 XP short of level 16. Run 7283 exposed a randomized Great
Eastern Desert DFS cycle; run 7284 recovered Aeloria through Limbo and the
protected corpse after a death that cost 3,623 XP. The repaired walker preserves
its visited graph, the Eastern Desert route is quarantined for this reboot, and
these are continuation checkpoints, not a HERO claim. Runs 7285 and 7286 then
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
suite passes 2,664 tests. Run 7343 then added a clean 358-XP young dragon
wormkin kill; Aeloria is now 7,998 XP short of level 16. Run 7344 then added a
clean 233-XP huge python kill; Aeloria is now 7,765 XP short of level 16. Runs
7349-7366 then exercised safe absence, provisioning, liquidation, and bounded
no-progress rotation paths. Run 7351 killed a drider for 90 objective XP and
run 7367 killed a goblin leader for another 90 XP; Aeloria is now 7,585 XP
short of level 16. The selector now retains the full bounded same-reboot
no-progress history and skips crowd-exhausted waits. Runs 7369-7372 then
bounded Kestrel's negative-fame recovery: the Magic Shop refused a priced
flight potion, a retry was blocked by a wandering drunk, Circus recovery
withdrew at the 39% health floor after consuming sanctuary, and Mirror Realm
recalled before combat when no sanctuary reserve was available. The runner now
records explicit shop refusal as a hard boundary, permits fame recovery only
with verified sanctuary, and blocks a flight-only fallback from reopening the
refused shop. Live CLI campaigns now
default to a 180-second segment cap plus a 60-second local setup budget and 45
seconds of cleanup grace. The
Kestrel validation then used source food reserve route 5217, acquired exact
object VNUM 5219, and returned full without XP change, combat, or another shop
attempt. Aeloria checkpoint 22766 and Dorrik checkpoint 22769 both recorded
crowded current-band rooms and deferred safely for area reset. The live
rotation is continuing from durable checkpoints rather than stacking workers
or forcing an unsafe fame fight. The
selector now counts repeated exact-policy XP losses, quarantines after the
second loss, and waits for a reset when protection recovery has no independent
route. This is current continuation evidence, not a HERO claim. The earlier
run ledger is historical:
Runs 6994-7015 then added productive Mirror Realm, Moria, and Canyon
evidence, including source-matched watchman kills of 886 and 799 XP. Run 7013
withdrew from Dwarven Homestead at the explicit 27% health floor after 179
incidental XP and preserved the protection marker without death or XP loss. The
Moria sanctuary circuit is now split into one reset-room stop plus eight
bounded source-room edges; tests pass. Run 7019 then live-validated the
split circuit through rooms 4064 and 4063, acquired the purple sanctuary
potion, and placed it in the combat pouch before returning full. Run 7022
added 683 objective XP from the Tentusks treant and consumed the reserve; run
7023 reacquired a purple potion through Moria with 90 incidental XP. Runs
7024-7026 safely rotated protected Mirror routes without forcing absent targets.
Run 7027 then killed the source-matched Dwarven Home host for 1,938 objective
XP and returned full with the sanctuary reserve intact. Run 7029 reacquired the
reserve with 90 incidental XP; run 7030 safely skipped a wandering Mirror Realm
gardener outside the source-safe relocation graph. Run 7031 withdrew from the
source-matched Solace Sergeant at Arms at the shared 30% health floor after
sanctuary expired, recording a 385-XP flee loss; run 7032 restored full healer
recovery. Run 7033 reacquired the sanctuary reserve with 100 objective XP; run
7034 safely skipped a crowded Mirror Realm target without combat. Run 7035 then
killed the source-matched Dwarven Home host for 1,520 objective XP without
consuming the reserve. Run 7038 exposed a same-name Grove race between
wandering mobile VNUMs 8900 and 8901 and caused a 385-XP flee loss before GMCP
identity arrived. The runner now uses source-graph reachability to skip
ambiguous same-name targets before `consider` or `kill`; run 7039 restored the
sanctuary reserve with 140 total XP, and run 7040 added 1,465 objective XP from
the Dwarven Home host. Runs 7041 and 7042 then recorded a safe Mirror rotation
and live-validated the pre-combat same-name VNUM guard at Grove room 8906
without combat or XP loss; run 7043 added 1,410 objective XP from the Dwarven
Home host. Run 7049 exposed a source-casting status gap: mobile 9202, a
`spec_cast_cleric` cyclops, blinded Dorrik after sanctuary expired and caused a
39-XP net loss before safe healer recovery. The source-backed repair requires a
verified cure-blindness route before combat, retains two matching potions when
sanctuary and cure blindness share an item, and uses the cure before fleeing
when blindness is active. Runs 7050 and 7051 completed safe recovery and
Dwarven Home rotations without reaching the cyclops, so the repair is
offline-verified but still needs a live trigger. Dorrik is now 14,116 XP short
of level 25. Run 7055 then live-tested the source-matched Weeping Willow at a
perfect consider; the shared 35% health floor fired after it reduced Dorrik to
137/542 HP, producing a 213-XP net loss after the flee charge. Runs 7056-7059
recovered and rotated through Dwarven Home, Shire, flight, and Tentusks without
another loss. Run 7060 then reopened the Dwarven Home host route; Dorrik
withdrew at 124/542 HP after earning 602 damage-credit XP, paying the 385-XP
flee cost for a 217-XP net gain without an objective kill. He returned safely
to healer room 3054 at 480/542 HP, full mana and movement, with hunger 4 and
thirst 42. Runs 7063-7066 then exercised the next protected frontier: run 7063
killed the source-matched New Ofcol teller for 1,119 objective XP with a 20-XP
below-band drunk interruption; run 7064 withdrew from the Drow weapons master
at 43/542 HP, losing 385 XP after 23 damage-credit XP. Run 7065 consumed
sanctuary before engaging the Canyon `spec_cast_cleric` cyclops, but its harm
spell outlasted the aura and forced a flee at 80/542 HP, for a 117-XP net loss.
Special routes that fail after sanctuary are now quarantined for the reboot.
Run 7066 reacquired the purple reserve from the source-matched large hobgoblin
for 100 objective XP, pouch-stowed it, and returned full. Runs 7081 and 7092
repeated the Drow weapons master route under its two-mobile crowd: the first
lost 210 XP, and the sanctuary-protected retry lost 265 XP at the 39% health
floor. The exact route is quarantined for this reboot. Run 7083 hit the
180-second segment boundary during a deferred Mirror Realm search and run 7084
returned Dorrik safely; the starter now clears stale crowd and locator waits
before its runtime return boundary. Runs 7085-7091 completed flight, New Ofcol,
Moria, and bounded absence maintenance. Run 7095 then killed the source-matched
New Ofcol teller for 934 objective XP and returned full to healer room 3054 at
358,980 XP. The full offline suite passes `2,648` tests.
Runs 6921 and 6923 then added 802
and 1,367 objective XP. Run 6926 exposed an endpoint-gate
failure against the level-19 Goblin Caves Sentry at Dorrik's level-24 floor;
the starter now withdraws before attacking a below-band endpoint target, with
resource and required-loot exceptions retained. Run 6927 live-validated the
repair by avoiding that target, and runs 6928-6935 completed bounded rotations
with safe healer returns. Run 6936 exposed a source-audited gas-breath target
above the live level ceiling and caused a 385-XP flee; combat-special admission
now rejects that class before launch. Run 6938 killed a Swamp Wraith for 587 XP
but encountered three below-band Mistlings on the Mahn-Tor return; the repaired
return branch keeps that source-known interruption in bounded combat. Run 6940
then added 170 XP on the Eastern Desert worm route and returned safely. Runs
6941 and 6942 then added 933 and 1,177 XP through the Kerofk gravedigger and
Old Thalos mayor with safe healer returns and no XP loss. Runs 6948-6950 then
completed a bounded generic continuation: run 6949 killed the source-matched
Mirror Realm watchman for 873 XP, while runs 6948 and 6950 correctly withdrew
from crowded circuits without forcing combat. All three returned safely with
no death or XP loss. Runs 6951-6960 then added 1,988 aggregate XP, including
a 636-XP Mirror Realm watchman and a 1,352-XP Kerofk route; absent and crowded
targets were skipped without XP loss. Run 6963 exposed a timed sleeping-
recovery watchdog gap during flight maintenance; the starter now reopens the
prompt gate when the scheduled health check is due. Run 6964 live-validated
the repair by buying and activating flight with no XP loss. Run 6965 completed
a bounded Abyss route with its registered target absent; run 6966 earned 460
incidental XP from three low-risk Kerofk interruptions and returned Dorrik full
to healer room 3054. Runs 6967 and 6968 exposed the same Abyss return hazard,
and run 6971 live-validated the repaired return graph. Runs 6981 and 6982
recorded bounded 149-XP and 16-XP net losses; the finisher now permits one
source-admitted final action against a target up to one level higher at 35%
health or less when the observed one-hit reserve is covered. Run 6987 exposed
a held earthquake staff on the otherwise noncombat priest of Thalos, so source
ranking now rejects unevaluated spell-bearing scrolls, wands, and staves. The
full suite passes 2,636 tests; Dorrik is full at 343,424 XP. Run 6747 exposed an
optional daycare
absence watchdog; run 6748 live-validated its reconciliation and rotation.
Runs 6749 through 6754 then resumed the character matrix without manual target
steering: Dorrik's run 6752 slept from 133/370 to 370/370 movement at the
healer, run 6751 recorded 860 incidental XP, Aeloria run 6750 killed the
source-matched goblin leader for 302 objective XP before an unapproved attacker
left a 154-XP net checkpoint increase, and runs 6753-6754 recorded absent
targets without forcing combat. Runs 6758, 6760, and 6762 then exercised the
updated source-ranked selector safely; run 6766 completed the next bounded
no-steering regression with two incidental kills, a net 185 XP after a 354-XP
loss event, a 35% health-floor withdrawal, and a full healer return. Run 6770
then killed the source-matched Kerofk gravedigger for 1,063 objective XP and
returned Dorrik full. Run 6771 exercised the repaired deferred-practice handoff
on a Mirror Realm continuation: no unnecessary trainer trip, no forced absent
target, and a safe healer return with no XP change. A narrow near-death finish
window is covered by regression tests but has not yet been claimed as live-
specific evidence. The level-20 shifter trainer now has a source-derived
Kerofk locator across 62 reachable rooms with bounded stale-result recovery.
Live level-20 and level-30 subclass proof remain outstanding. Runs 6784, 6786,
6788, 6790, and 6795 then supplied 736, 893, 739, 1,040, and 881 objective XP
through the generic source-ranked rotation, while runs 6785, 6787, 6789, and
6794 safely recorded bounded Mirror Realm zero-kill or absence results. Run
6793 refreshed flight and 6796 restored hunger from 2 to 39 before another
field launch; runs 6797-6799 then completed liquidation, safely rejected a
non-corporeal funding target, and restocked. Runs 6800 and 6801 then added 875
and 857 objective XP from the source-matched Kerofk gravedigger and Old Treant.
The following Mirror Realm batch was stopped after an outer watchdog stall;
segment 6371 recovered as ready with explicit interruption evidence, and run
6803 returned Dorrik safely home without XP loss. Runs 6807 and 6812 then
added 784 and 534 objective XP through the generic Old Treant route; runs 6806,
6809, 6810, 6811, and 6813 recorded bounded zero-kill rotations, and run 6808
refreshed flight. Run 6814 withdrew from a Shudde-M'ell interruption after the
live level gate, lost 354 XP, fed hunger from 5 to 40, and quarantined the
exact Plains North policy for three same-reboot segments. Run 6815 then killed
the source-matched Swamp Wraith in the alternate Mahn-Tor circuit for 1,060
objective XP, and run 6816 restored full movement at healer room 3054. The
next run, 6817, completed a bounded Mirror Realm zero-kill probe without XP
change. The campaign persists a
practice-type
deferral when a trainer has no immediately useful listed skill, while
preserving re-entry for newly unlocked damage gateways.
This remains level-23 continuation evidence, not a HERO completion claim. Runs
6566 and 6570 added 484 and 287 objective XP to Aeloria
through generic Plains North and Fleshmonger routes; run 6572 added 570 XP to
Dorrik through source-ranked provision funding before automatic return and
liquidation. Run 6594 live-validated the starvation override by acquiring and
eating a source-matched rabbit roast, raising Dorrik's hunger from -7 to 17,
and returning alive to healer room 3054. Runs 6596 and 6597 then added 560 XP,
completed healer recovery, and left Dorrik full at 280,734 XP. Run 6598 added
543 XP to Aeloria from a source-ranked Shire receptionist kill and returned her
fully recovered to healer room 3054. Runs 6602 and 6603 then added 450 XP and
completed full healer recovery, leaving Dorrik at 281,724 XP. Aeloria run 6616
added 221 net XP after a protected Wyvern withdrawal, and run 6617 safely
rotated the Shadow Keep variant without another loss. Runs 6620 through 6623
added 750 XP and completed full recovery; runs 6628 and 6633 added 1,030 XP,
and run 6635 built a five-pie plus rabbit-leg food reserve. Aeloria run 6650
added 371 XP from Gremlin Lair and recovered safely; run 6658 added 330 XP from
Plains North and run 6659 completed loot liquidation. Run 6663 recorded a -38
XP Shire withdrawal and run 6664 selected Shadow Keep without repeating it.
Dorrik run 6653 added 280 XP from Solace, run 6656 added 130 XP from Mirror
Realm, run 6657 completed full recovery, and run 6661 returned safely after
bounded liquidation. Run 6665 then added 130 objective XP through Mahn-Tor and
left Dorrik full in healer room 3054 at 284,324 XP. Runs 6680 through 6690
continued the generic source-ranked rotation: bounded gravedigger research
found no target, flight and liquidation completed safely, and Shire and Mirror
Realm attempts recorded no objective kill rather than forcing absent or unsafe
targets. Run 6683 exposed stale posture after DD4 accepted wake without a
position field in `Char.Vitals`; explicit sleep and wake text now updates local
state. Dorrik recovered to full resources at 285,451 XP and 352 movement in
healer room 3054. The full offline suite now passes 2,614 tests. This remains
level-22 continuation evidence, not a HERO completion claim. Runs 6691 through
6698 then completed resumable maintenance and return phases around three
source-ranked probes. Mirror Realm watchman and Dwarven routes did not prove
their objective targets; one Dwarven route recorded a reboot-local -163 XP loss
and was quarantined, while incidental field kills added 750 XP outside
objective evidence. Recovery returned Dorrik full to healer room 3054 at
285,878 XP. The next policy phase remains persisted for later continuation.
Runs 6701 through 6706 then completed bounded flight, Abyss, liquidation, and
healer-return work. Run 6707 exposed that generic high-band sanctuary recovery
stopped after the short Moria reset-room probe. The repaired dispatch now uses
the source-room-guided deep circuit; run 6708 acquired a purple sanctuary
potion from the source-matched large hobgoblin and returned Dorrik safely to
healer room 3054 at 287,128 XP with full HP and mana. The protection marker for
the original failed hunt remains pending until that hunt is retried under the
new reserve. This is continuation evidence, not a HERO completion claim. Runs
6709 through 6712 then exercised the protected Ofcol retry, cleanup, healer
movement recovery, and flight refresh. Run 6709 refused a two-mobile crowd;
run 6713 used sanctuary on an audited cleric-special cyclops route and
withdrew safely after blindness made continuation unsafe; run 6714 found both
Moria carriers crowded. Run 6715 added 653 XP through an audited Highland
route before an unapproved attacker joined, and run 6716 restored Dorrik to
full resources at 288,592 XP in healer room 3054. The original protection
marker remains pending and its reserve must be reacquired before the exact
failed hunt is retried. Runs 6717 through 6721 then completed Dorrik
liquidation, a productive Arikasbab circuit, and safe healer returns; run 6718
added 1,628 XP, including a 1,338-XP Maid kill. Aeloria runs 6722 and 6723
completed bounded Ambush and Plains North probes without objective XP. Kestrel
runs 6724 and 6725 completed safe reserve and Mirror Realm probes without XP.
These are continuation checkpoints, not a HERO completion claim. Runs 6730,
6735, and 6737 exposed and then guided repairs for stale wandering targets,
repeated-room route context, and prompt-before-room event ordering. Run 6738
live-validated the repaired Moria route and trainer handoff, reaching the
official endpoint and returning safely after 420 incidental XP. Run 6742
recorded a health-floor withdrawal from the Dwarven Home host; run 6743 then
added 1,072 XP from the level-20 gravedigger and returned Dorrik full to the
healer. The next work unit is another bounded, no-steering level-23 rotation;
the protection marker remains evidence, not permission to repeat the risky
host route unchanged.
Run 6745 then preserved the Mirror Realm split-locator result: the selected
room was absent, a neighboring reset proved the guardian existed elsewhere,
and four incidental kills added 600 XP before a full healer return. Dorrik is
now level 23 at 295,215 XP, 32,335 XP short of level 24.
Dorrik's live return-home run 6752 then slept at healer room 3054 until the
full 370/370 movement reserve was restored. This closes the runtime-boundary
recovery defect exposed by run 6751; the next work unit remains a bounded,
no-steering level-23 rotation toward the level-30 subclass transition.
Dorrik's
level-15 transition is now live evidence:
run 5246 crossed the boundary, and runs 5231 through 5306 executed
source-ranked field circuits with no manual target steering before returning
to healer room 3054. Runs 5249 and 5251 then validated both registered Ambush
reset rooms at level 14, while run 5261 correctly skipped a non-viable live
candidate and run 5262 refreshed flight. Runs 5274, 5280, 5284, and 5295 then
proved productive current-band alternatives after the reboot-scoped Dwarven
Nobleman probe withdrew at the 15% floor without a kill. Run 5297 checkpointed
Dorrik at 91,474 XP; run 5302 then completed another successful Shire segment.
Run 5307 exposed an armed Ambush Bardoosh critical-hit burst that killed him
after two incidental low-XP goblin interruptions. Purgatory corpse recovery,
equipment restoration, and healer recovery completed correctly; the death
penalty left the durable checkpoint at 87,820 XP. The transition checkpoint preserved
two practices and the live subclass value `none`; the requested knight
subclass is not being assumed before the level-30 change point. Aeloria and
Kestrel remain correctly waiting on their reboot-scoped protection and
cure-critical dependencies rather than false crowd results.
- Bounded post-repair runs 5308 through 5310 then selected a productive duty
  target, refreshed flight, completed the ranger circuit, recovered a long bow,
  and returned Dorrik to healer room 3054 at full resources and 88,279 XP.
- Runs 5311 through 5316 then completed maintenance, returned through Moria,
  and killed a Shadow Wraith for 296 XP after two trivial transit interruptions;
  Dorrik returned safely at 89,572 XP.
- Runs 5317 through 5319 then completed daycare and flight maintenance and
  killed the source-matched ranger for 624 XP. The long-bow collection hit the
  carry-count limit without affecting the successful kill or healer return.
  Dorrik is now at 90,196 XP.
- Runs 5320 through 5325 then handled sanctuary/Moria prerequisites, killed a
  Shire receptionist for 569 XP, and recorded both Wraith rooms absent before
  returning safely. Dorrik is now at 90,835 XP.
- Runs 5326 through 5328 followed the source-backed Moria and Wraith circuits;
  both Wraith rooms remained absent, so no objective kill was forced. Dorrik
  returned safely at 91,025 XP after incidental field kills.
- Runs 5329 through 5334 then added a 449-XP ranger kill and a 349-XP Shire
  receptionist kill; the later Wraith absence was recorded without forcing a
  low-value fight. Dorrik is now at 91,903 XP.
- Runs 5335 through 5337 then completed a source-ranked Aruncus kill for 743
  XP and safe daycare/Moria maintenance. Runs 5338 and 5339 completed two
  Wraith probes safely; their incidental goblin XP was kept separate from
  objective evidence. Runs 5344 then completed an Aruncus kill for 919 XP in
  166.6 seconds with full health before and after. Runs 5345 and 5346 found
  both Wraith targets absent and kept their incidental goblin XP outside
  objective evidence. Dorrik is now at 94,264 XP. The selector's new circuit
  rule compares safe multi-target routes by risk-adjusted source score per
travel step, preventing a wandering high-score target from hiding a better
fixed-reset circuit. Run 5353 then re-proved the Dwarven Homestead route with
a delayed-GMCP, VNUM-resolved below-band bridge goblin and a positive nobleman
consider without combat. Runs 5354 through 5358 rotated past maintenance,
crowding, and absence; run 5359 completed a 413-XP current-band ranger kill in
141.8 seconds and run 5360 completed safe maintenance.

Runs 5392 through 5401 then exercised failed-return recovery, maintenance, and
low-value or absent route evidence without leaving a campaign worker behind.
Run 5402 selected source-matched Bardoosh mobile 4515 in room 4514 and earned
671 objective XP, plus 180 incidental XP from three goblin interruptions, for
851 XP total before returning to healer room 3054 at full health and movement.
This is the intended risk/reward balance: the runner remains willing to enter
a scored aggressive-target risk pool when the source, live `consider`, crowd,
health, protection, and return gates pass, but it does not promote an explicit
objective kill below 50 XP as productive history. Wandering kills are keyed by
tagged source identity, and a fresh route can displace a productive repeat only
when its risk-adjusted reward per travel step is at least 25% stronger.

This is not yet a HERO proof. A level-100 campaign can resume and checkpoint,
but it must still stop at a missing or research-gated band. Treat policy status
as a contract: `verified` means executable evidence is reusable, `research`
means a bounded probe with explicit limits, and `unavailable` means the runner
must stop safely. A checkpoint, a source catalog entry, or a policy-count report
does not by itself prove progression.

## Refined Goal And Work Order

Given a source-legal race, cosmetic sex, base class, optional subclass, name,
and personality, one command must create or resume the character and play it
without manual gameplay to level 100. Character names identify credentials and
history only. Direct Telnet/GMCP is the primary behavior adapter; Mudlet and a
Windows virtual machine are later visual and lifecycle validation boundaries.

The proof sequence is creation/tutorial, representative level-10 classes,
class-aware level 1-30 coverage with the level-30 subclass transition, then
executable bands through 31-70 and 71-100, followed by fresh creation-to-HERO
runs. Each band must have source identity, live consider and route evidence,
combat/resource/return evidence, and offline regression coverage. AI-assisted
decisions remain intentionally deferred.

The immediate work package is now the level-14-to-30 frontier: preserve the
newly proven level-boundary behavior, make class-aware training and equipment
decisions observable at every level, and promote one generic band at a time
until the level-30 subclass handoff is executable. The source-derived shifter
trainer locator is now implemented and offline-covered; live level-20 and
level-30 evidence are still required before promotion. See
[`docs/PROGRESS_AUDIT_2026-08-13.md`](docs/PROGRESS_AUDIT_2026-08-13.md) for the
current architecture assessment and definition of done; the 2026-08-12 audit
remains the historical record.

The reporting foundation now preserves the configured persona across the full
path from HERO request to profile, run context, and campaign report. Title,
backstory, and optional personality are non-secret durable metadata; they do
not alter deterministic decisions or count as progression evidence. The next
progression blocker remains fresh, executable evidence beyond the current
level-13 boundary.

## Character-Independent Autonomy Cycle 34 - 2026-08-16

- The next generic blocker was the level-20 shifter trainer. Source revision
  `7996722` places mobile 30257 in inaccessible MobChute room 30250 and lets it
  wander across 62 reachable Kerofk rooms. The class-aware trainer route now
  starts from the Kerofk staging room, uses bounded `where shifter` queries,
  follows live GMCP exits to the reported room, and retries stale locations
  without assuming that the teacher is stationary.
- Focused shifter and subclass tests, the full starter suite, and the full
  offline suite pass (`2,623` tests). The route is implemented evidence, not a
  live promotion: no character has yet supplied level-20 shifter or level-30
  subclass confirmation.
- Run 6766 completed the bounded no-steering Dorrik regression after this
  repair. It recorded two incidental kills, a net 185 XP after a 354-XP loss
  event, withdrew at the 35% health floor, and returned full to healer room
  3054. The active HERO goal remains open; the next work is live progression
  to the level-30 handoff and then generic higher-band coverage.

## Character-Independent Autonomy Cycle 35 - 2026-08-16

- Source revision `7996722` remains current. Run 6770 advanced Dorrik through
  the generic level-23 frontier: the source-matched Kerofk gravedigger yielded
  1,063 objective XP and the character returned full to healer room 3054.
- Run 6771 exercised the repaired deferred-practice handoff on a Mirror Realm
  continuation. The runner did not revisit the level-20 trainer, did not force
  an absent target, and returned safely with no XP change. This is executable
  safety evidence, not a progression claim.
- The full offline suite passes `2,624` tests. The immediate live target is
  continued character-independent level-23-to-24 progress, followed by the
  level-30 trainer and subclass transition. The HERO goal remains open.

## Character-Independent Autonomy Cycle 36 - 2026-08-16

- Runs 6772, 6776, 6778, and 6780 extended Dorrik's generic level-23
  continuation by 887, 605, 599, and 868 objective XP. Each run used an exact
  source-matched target, returned full to healer room 3054, and remained free
  of death or runtime failure. Dorrik is now at 302,885 XP, 24,665 short of
  level 24.
- Runs 6774 and 6779 exercised route watchdog and absence handling. The engine
  quarantined a repeated Mirror Realm movement cycle and separately recorded
  an absent split-locator target without forcing combat; both returned safely.
- The deferred-practice marker is live-validated across subsequent segments:
  Dorrik no longer revisits the fruitless trainer at the same level, while the
  existing skill-gateway reopen behavior remains covered offline. The full
  suite remains green at `2,624` tests. The level-30 trainer/subclass handoff
  and the HERO goal remain open.

## Character-Independent Autonomy Cycle 37 - 2026-08-16

- Run 6784 killed the source-matched Old Treant (mobile 2301) for 736 objective
  XP, and run 6786 killed the Mirror watchman (mobile 19010) for 893 objective
  XP. Run 6788 then killed another source-matched Old Treant for 739 XP. Each
  segment returned Dorrik full to healer room 3054 without death, flee, or a
  runtime boundary. He is now level 23 at 305,822 XP, 21,728 short of level 24.
- Runs 6785 and 6787 exercised two Mirror Realm routes that produced no
  objective kill. The executor persisted those zero-kill or absent-target
  results and rotated without forcing combat, preserving honest evidence for
  future source-ranked selection.
- The full offline suite remains green at `2,624` tests. The next work is the
  same generic level-23-to-24 rotation, followed by live level-20 trainer and
  level-30 subclass confirmation; the HERO goal remains open.

## Character-Independent Autonomy Cycle 38 - 2026-08-16

- Run 6790 selected the generic source-ranked Kerofk route and killed the
  source-matched gravedigger (mobile 30248) for 1,040 objective XP. Runs 6791
  and 6792 then liquidated and returned home, leaving Dorrik full in healer room
  3054 at level 23 with 307,312 XP, 20,238 short of level 24.
- The three-segment batch ended at its requested checkpoint boundary with no
  death, flee, runtime failure, or orphan process. Run 6789 immediately before
  the batch recorded another clean Mirror watchman no-kill result, so the
  executor continues to preserve both productive and unproductive live evidence.
- The full offline suite remains green at `2,624` tests. The next work is the
  same generic level-23-to-24 rotation, followed by live level-20 trainer and
  level-30 subclass confirmation; the HERO goal remains open.

## Character-Independent Autonomy Cycle 39 - 2026-08-16

- The second three-segment batch completed without a stall: run 6793 refreshed
  flight, run 6794 recorded a bounded Mirror Realm zero-kill result, and run
  6795 killed the source-matched Old Treant (mobile 2301) for 881 objective XP.
  Dorrik is now level 23 at 308,193 XP, 19,357 short of level 24, full in
  healer room 3054.
- The checkpoint also persisted hunger at 2/48, making the next generic action
  a provision priority before another extended hunt. No death, flee, runtime
  failure, or process residue was observed; the streamer remained healthy.
- The full offline suite remains green at `2,624` tests. The next work is the
  provision-aware level-23-to-24 rotation, followed by live level-20 trainer
  and level-30 subclass confirmation; the HERO goal remains open.

## Character-Independent Autonomy Cycle 40 - 2026-08-16

- Run 6796 exercised the provision gate after Dorrik's hunger reached 2/48.
  The executor restored hunger to 39/48, retained the safe healer checkpoint,
  and recorded the Mirror kid as absent without forcing combat or claiming XP.
- The latest durable state remains level 23 at 308,193 XP with full HP and mana
  in healer room 3054. The provision branch is now live evidence alongside the
  productive Old Treant and gravedigger routes; the HERO goal remains open.

## Character-Independent Autonomy Cycle 41 - 2026-08-16

- Runs 6797-6799 completed the provision follow-up: liquidation freed capacity,
  the funding route encountered a source-observed non-corporeal dwarven servant
  and correctly refused combat, and restock restored thirst to 48 with hunger
  at 36. Dorrik remained level 23 at 308,193 XP, full in healer room 3054.
- This batch added no XP, but it strengthened the generic safety contract:
  funding and provision work can rotate through a rejected target without
  forcing a low-value or impossible attack. The level-23-to-24 hunt remains
  active and the HERO goal remains open.

## Character-Independent Autonomy Cycle 42 - 2026-08-16

- Runs 6800 and 6801 extended the generic level-23 rotation with a
  source-matched Kerofk gravedigger kill for 875 objective XP and an Old Treant
  kill for 857 objective XP. Dorrik advanced to 310,065 XP, 17,485 short of
  level 24, and remained full in healer room 3054.
- The next three-segment launch stopped after its outer watchdog saw no
  progress. The campaign recovery path marked Mirror Realm segment 6371 ready
  with explicit interruption evidence, then run 6803 completed a bounded
  return-home segment. No death, XP loss, or orphan worker remained; the
  streamer was left running normally. The HERO goal remains open, and the
  next work is another single-segment level-23 rotation before the live
  level-20 trainer and level-30 subclass handoff.
- The full offline suite remains green at `2,624` tests.

## Character-Independent Autonomy Cycle 43 - 2026-08-16

- Run 6804 completed the next generic Kerofk segment and killed the
  source-matched gravedigger for 891 objective XP. Dorrik reached 311,416 XP,
  16,134 short of level 24, and remained alive at healer room 3054.
- Run 6805 completed the normal liquidation and recovery handoff. Checkpoint
  20293 records full 516/516 HP, 234/234 mana, and 338/370 movement in healer
  room 3054, with no active combat or death state. The single-segment watchdog
  completed normally; the HERO goal remains open.

## Character-Independent Autonomy Cycle 44 - 2026-08-16

- Runs 6806, 6809, 6810, 6811, and 6813 completed bounded source-ranked
  probes without objective kills; run 6807 killed the source-matched Old
  Treant for 784 XP, run 6808 refreshed flight, and run 6812 killed another
  Old Treant for 534 XP. Dorrik reached 312,734 XP before the next safety
  event, then remained alive and fully recovered in healer room 3054.
- Run 6814 exercised the low-hunger branch on Plains North. Shudde-M'ell
  entered during the official route, the live GMCP level gate forced a flee,
  and DD4 charged the 354-XP flee penalty. The character returned safely,
  consumed a pie, and rose from 5 to 40 hunger; the campaign quarantined the
  exact source policy for three same-reboot segments. The durable checkpoint
  is level 23 at 312,380 XP, 15,170 short of level 24, with full HP, mana, and
  movement. The HERO goal remains open.
- The full offline suite remains green at `2,624` tests. This is live safety
  and continuation evidence, not a level-24, subclass, or HERO claim.

## Character-Independent Autonomy Cycle 45 - 2026-08-16

- Run 6815 validated post-quarantine rotation to the alternate Mahn-Tor
  circuit. The source-matched Swamp Wraith (mobile 2306) yielded 1,060
  objective XP, raising Dorrik to 313,440 XP, 14,110 short of level 24.
- Run 6816 completed the bounded healer return. Checkpoint 20335 records room
  3054 with full 516/516 HP, 234/234 mana, and 370/370 movement; Dorrik is
  alive and out of combat. This removes the immediate recovery blocker while
  keeping the level-20 trainer and level-30 subclass handoff outstanding.
- The full offline suite remains green at `2,624` tests. The HERO goal remains
  open.

## Character-Independent Autonomy Cycle 46 - 2026-08-16

- Run 6817 completed the post-test Mirror Realm route in 143 seconds with no
  objective kill or XP change. The selector preserved the bounded zero-kill
  evidence, returned Dorrik safely to healer room 3054, and left him alive and
  out of combat at hunger 29/48.
- The full offline suite passed `2,624` tests immediately before this live
  continuation. The next work remains generic level-23-to-24 progression,
  followed by live level-20 trainer and level-30 subclass confirmation; the
  HERO goal remains open.

## Character-Independent Autonomy Cycle 47 - 2026-08-16

- Runs 6818, 6827, and 6824 added 726, 637, and 884 objective XP through the
  generic Old Treant and Swamp Wraith routes. Run 6824 also exposed two
  avoidable 354-XP flee penalties when source-known below-band Mistlings
  interrupted the Mahn-Tor no-recall return maze; the character still returned
  safely, but the evidence showed that fleeing was poorer than completing a
  safe lower-band combat interruption.
- The return-maze policy now fights only when every live enemy is source-known
  below the useful band, the character has adequate health and provisions, and
  the room is one of Mahn-Tor's registered no-recall return rooms. It then
  resumes the live-GMCP exit graph. Ordinary interrupted routes still use the
  existing flee and return path. The focused policy set passes 38 tests and
  the full offline suite passes `2,626` tests.
- Runs 6819, 6820, 6821, 6822, 6823, 6825, 6826, 6828-6831 completed bounded
  flight, absence, watchdog recovery, liquidation, and healer-return work.
  Run 6822 stopped at the runtime boundary and run 6823 recovered it without
  death; the remaining routes recorded no forced low-value target. Dorrik was
  level 23 at 315,159 XP before the subsequent continuation runs below.
  The new live policy is offline-verified but has not yet been re-triggered by
  a post-repair Swamp Wraith return. Runs 6832 and 6835 then added 1,053 and
  1,083 XP through the generic gravedigger route; run 6833 added 894 XP from
  Old Treant, and run 6834 rejected a crowded Mirror route with no XP change.
  At that point Dorrik was level 23 at 318,189 XP, 9,361 short of level 24,
  full on HP, mana, and movement in healer room 3054. The level-20 trainer and
  level-30 subclass handoff remain the next generic progression gates; the HERO
  goal remains open. Runs 6836 and 6839 were bounded zero-XP maintenance or Mirror
  rotations. Run 6837 added 608 XP from Old Treant, run 6838 withdrew at the
  health floor with 208 net XP, and run 6840 added 150 XP from the Arachnos
  guardian. Runs 6841 and 6848 added 716 XP and completed flight maintenance;
  runs 6842-6845 recorded bounded zero-XP or safe absence routes. Run 6847
  exposed a repeated no-policy-decision watchdog on flight maintenance, and
  the next invocation reconciled it cleanly. Before run 6851, Dorrik was at
  319,871 XP with hunger 24, so the generic rotation could continue. Run 6851
  then added 687 XP
  from Old Treant, and run 6852 recorded another bounded Mirror zero-kill
  result. Dorrik is now at 320,558 XP, 6,992 short of level 24. Run 6853
  recorded an absent Highland candidate without XP; run 6854 added 646 XP from
  Old Treant; and run 6855 found Nessy's child but withdrew when the adult
  Nessy joined, paying the 354-XP flee cost. Dorrik returned full and the exact
  Highland policy was quarantined for rotation. He is now at 321,161 XP, 6,389
  short of level 24. Run 6856 then added 1,325 XP from the source-matched Maid;
  run 6857 sold four items for 291 coins; and run 6858 recorded a bounded
  Mirror zero-kill result. Runs 6878-6881 then validated the one-attempt
  source-route exclusion: an empty Mirror route rotated to flight maintenance
  and Old Treant for 633 objective XP, clearing the marker. Run 6883 acquired
  sanctuary from the large hobgoblin and run 6887 added 760 XP from Old Treant.
  Run 6895 withdrew from Dwarven Homestead at the health floor for a 189-XP
  loss without death; run 6896 recorded the subsequent bounded Mirror absence.
  Dorrik is now level 23 at 326,057 XP, 1,493 short of level 24, full in healer
  room 3054. These are continuation checkpoints, not a HERO completion claim.

## Character-Independent Autonomy Cycle 48 - 2026-08-16

- The normal source-ranked checkpoint path now persists a one-attempt
  exclusion after an empty, crowded, unreachable, or otherwise safely
  unsuccessful route. The exact policy and reboot identity are retained, the
  candidate is cleared, and the next selection rotates or waits for reset;
  productive objective XP clears the marker. This closes the repeated empty
  Mirror retry observed in runs 6873-6877. The focused regression passes, and
  the rule is live-validated by runs 6878-6881.
- Runs 6881 and 6887 added 633 and 760 objective XP from Old Treant; run 6883
  collected the source-matched sanctuary potion from the large hobgoblin. Run
  6895 accepted a measured risk, withdrew at the Dwarven Homestead health
  floor, lost 189 XP, and survived; the exact route remains quarantined for
  later protection-aware rotation. Run 6896 recorded a bounded Mirror
  absence after rotation. Dorrik is level 23 at 326,057 XP, 1,493 short of
  level 24, and safely full in healer room 3054. The level-20 trainer and
  level-30 subclass handoff remain live gates; HERO remains unproven.

## Character-Independent Autonomy Cycle 27 - 2026-08-13

- Run 5353 re-proved the Dwarven Nobleman route through the Miden'nir bridge.
  A level-6 mountain goblin arrived in abbreviated live text before GMCP; the
  executor waited for `Char.Enemies`, resolved mobile VNUM 3501, and handled it
  as incidental below-band combat. The route reached the homestead, recorded a
  positive consider for mobile 10734, and returned without attacking the
  research target.
- Runs 5354 through 5358 reconciled the standalone probe's XP penalty,
  restocked, and rotated past a crowded Shire room and an absent Aruncus
  reset. Run 5359 then selected a current-band source-ranked route and killed
  the source-matched ranger for 413 XP in 141.8 seconds, returning at full
  resources; run 5360 completed safe maintenance. Dorrik is now level 14 at
  95,303 XP in healer room 3054.
- The VNUM-first and delayed-GMCP identity behavior has focused regression
  coverage, and the full offline suite passes 2,496 tests. The active goal
  remains level-14-to-30 progression; no remote publication or local commit
  was attempted under the 24-hour publication policy.

## Character-Independent Autonomy Cycle 29 - 2026-08-13

- Runs 5392 through 5401 exercised return recovery, maintenance, and absent or
  low-value route evidence. Run 5400's lone 10-XP drunk kill exposed stale
  wandering-target promotion: the selector had been treating contact as
  productive because it was keyed to the selected room rather than the tagged
  source mobile. The repaired ledger now uses source policy identity and
  requires an explicit objective kill of at least 50 XP for productive history.
- Run 5402 selected Bardoosh mobile 4515 in room 4514 and earned 671 objective
  XP plus three incidental 60-XP goblin kills, for 851 XP total. Dorrik reached
  100,802 XP at level 15 and returned to healer room 3054 at full health and
  movement without dying. A fresh source route may now outrank a productive
  repeat only when its risk-adjusted reward per travel step is at least 25%
  stronger; aggressive requested targets remain soft risk-pool candidates
  behind the normal source, consider, crowd, health, protection, and return
  gates.
- Run 5403 then selected Aruncus the Druid, mobile 300 in room 323, and earned
  505 objective XP. Dorrik returned to healer room 3054 at full 322/322 HP and
  290/290 movement, now 13,493 XP short of level 16.
- Run 5405 repeated the productive Bardoosh route for 351 objective XP and one
  incidental 70-XP goblin kill. Dorrik returned at full HP and 264/290 movement;
  13,072 XP remain to level 16.
- Run 5406 repeated Aruncus for 462 objective XP, returning at full HP and
  269/290 movement. Dorrik is now 12,610 XP short of level 16.
- Run 5407 reached the fanatical goblin guard, source mobile 4516, after it
  wandered into room 4522. Dorrik killed it for 264 XP, took a critical hit,
  and returned safely after finishing at 228/322 HP. The old run record lacked
  source attribution because the display-name stop differed from the live
  wandering identity; the repaired ledger now keys this evidence by VNUM.
- Run 5408 then accepted the measured Bardoosh repeat: mobile 4515 yielded 460
  objective XP and a wandering goblin added 70 incidental XP. Dorrik returned
  without death or flee at full 322/322 HP and 279/290 movement, reaching
  102,994 XP. This is productive risk/reward evidence, not a safe-return-only
  result.
- Run 5409 selected Aruncus for 421 XP in 69.8 seconds and returned at full HP
  with 272/290 movement. Run 5410 reopened the cooled Shargugh route and
  confirmed it absent; runs 5411 and 5412 completed flight and provision
  maintenance without misreporting them as XP progress.
- Run 5413 reached Bardoosh and SQLite events show a 60-XP goblin-lieutenant
  interruption followed by a 460-XP Bardoosh kill, but the worker was stopped
  after its transcript produced no bytes. Run 5414 recovered at healer room
  3054 with 103,935 XP. The interrupted segment remains failed evidence until
  its kill metadata is reconciled; orphan cleanup now closes its run row too.
- Run 5415 confirmed both Shadow Keep Wraith rooms absent after one incidental
  60-XP goblin interruption. Run 5416 then deliberately reopened the fanatical
  goblin guard, earned 257 objective XP from mobile 4516, and returned at full
  HP with 281/290 movement. Dorrik is now 10,488 XP short of level 16.
- Run 5417 live-validated write-time kill persistence: its incidental goblin
  row was committed while the run still had status `running`. Run 5418 found
  Aruncus with a non-hostile Ofcol cityguard, waited through the generic crowd
  budget, and lost the wandering target. The source-special crowd gate now
  ignores proven noncombat bystanders immediately and permits `spec_guard` only
  after one non-hostile interval for alignment 300 or higher. Ambiguous
  profiles and lower-alignment characters remain blocked.
- Run 5419 selected the fanatical guard again and earned 286 objective XP plus
  70 incidental XP, with all three kill rows durable before final cleanup. It
  returned Dorrik fully recovered at 104,728 XP, 10,072 from level 16. A
  confirmed objective kill now clears stale target-absence metadata.
- The full offline suite passes 2,523 tests. This is local work only; no commit
  or remote publication is due
  under the 24-hour publication policy. The active goal remains generic
  level-15-to-30 progression toward the level-30 subclass handoff.
- The Discord streamer replayed August 2 records after the append-only source
  became shorter at 11:51 AM. Permanent `--new-only` mode now fingerprints the
  source identity and preceding 4 KiB at every checkpoint; truncation,
  replacement, or in-place rewrite discards queued and partial history and
  resumes at the new end. A second guard now preserves a monotonic record-time
  watermark and refuses queued records more than 120 seconds old. A third guard
  fingerprints speaker/body content independently of timestamps and seeds its
  bounded ledger from the complete source history, preventing a resumed task
  from reposting any old turn that was appended again with a new timestamp. All
  18 streamer tests pass; the live process restarted with 13,840 protected
  content identities, an empty queue, a current watermark, and an exact EOF
  checkpoint. The conversation writer also rejects nested timestamped headers.
- Runs 5420 and 5421 found their source objectives absent but earned 60 and 10
  incidental transit XP. Raw XP had incorrectly reset the no-progress streak,
  allowing empty probes to keep displacing measured repeats. Source-ranked
  progress now uses exact objective-kill evidence during live execution and
  restart reconstruction. Run 5425 validated the repair: it selected mobile
  4516, earned 303 objective XP, and returned Dorrik full at 105,161 XP.
- Run 5426 then earned 470 aggregate XP while clearing forced Miden'nir
  aggression, but its selected goblin leader loaded at level 8 against
  level-15 Dorrik and paid only 80 XP. Live `Char.Enemies` below-band evidence
  now makes such an unavoidable kill incidental and persists the exact source
  policy exclusion; required-loot hunts retain their explicit exception. Run
  5428 supplied the productive contrast by earning 536 objective XP from the
  nomad commander and returning Dorrik safely at 106,561 XP, 8,239 from level
  16.
- Run 5436 then supplied the clean end-to-end proof. Mobile 3507 loaded at
  level 8, the unavoidable 80-XP leader kill was durably marked below-band and
  non-objective in SQLite, and the campaign checkpoint persisted the exact
  level-15 source-policy exclusion before returning safely to healer room
  3054. Run 5437 moved on to a live level-11 fanatical guard, earned 113 direct
  objective XP, and returned Dorrik safely at 108,315 XP, 6,485 from level 16.
  The full suite passes 2,523 tests.
- Run 5442 exposed a separate liveness bug when DD4 sent the `where nomad`
  prompt before the locator rows. The grace wait suppressed that prompt, but
  its expiry check was itself behind `prompt_ready`, so only the 45-second
  inactivity watchdog recalled. Locator and magic-shop preflight deadlines now
  wake before the prompt gate, and their bounded buffers preserve a line break
  before a late response header without breaking a row split mid-identity.
  Run 5444 live-validated the complete repair: the leader was mapped to Fungus
  Temple, the next command was issued immediately, no inactivity watchdog ran,
  and Dorrik saved and quit at healer room 3054 with 109,271 XP. Focused tests
  and the full 2,523-test suite pass.

## Character-Independent Autonomy Cycle 33 - 2026-08-13

- Run 5515 killed Dwarven Nobleman mobile 20504 for 963 objective XP and
  returned safely. Run 5516 then positively located Aruncus in `Grassy plains`
  but spent its 240-second budget inspecting every differently named source
  room on the way through the ambiguous room-name group.
- A mapped wandering locator now combines nonmatching source rooms into safe
  transit legs, inspects only the reported room-name group, and refreshes once
  from the actual current room through an all-origin relocation graph. The
  real Aruncus graph narrows from 42 target checks to seven while retaining
  every source-backed movement step.
- Run 5518 earned 930 objective XP from Haglik and 160 incidental transit XP.
  It returned safely through the runtime watchdog after DD4 reported `The
  brush is closed`, exposing a noun-specific exit parser. Any source-named
  closed exit now triggers `open <direction>` and a bounded retry; named locked
  exits fail closed. Dorrik is safe at healer room 3054 with 121,482 XP,
  12,118 short of level 17. The complete 2,528-test suite passes.
- Run 5522 added 619 objective Bardoosh XP. After bounded maintenance, run 5526
  live-validated locator compaction by following `Path in the plains`, finding
  Aruncus in room 302, earning 501 objective XP, and returning without the
  runtime watchdog. Run 5527 then added 655 objective Haglik XP and 160
  incidental transit XP. Dorrik finished full at healer room 3054 with
  123,437 XP, 10,163 short of level 17. The named-exit branch remains
  regression-verified but has not yet received a post-repair live trigger.

## Character-Independent Autonomy Cycle 32 - 2026-08-13

- Source ranking could permanently hide a deeper safe circuit when its only
  path crossed one aggressive mobile whose normal fuzz straddled the forbidden
  below-band boundary. The runner already distinguishes live below-band
  transit attackers from useful-band targets, but the source filter never let
  that evidence reach it.
- A generic bounded-borderline gate now admits only one global source instance
  with no special, fame, shop, or no-XP flag, a maximum fuzzy level exactly at
  `character level - 4`, and peak-round and critical-hit bounds below current
  max HP. Live below-band rolls may be defeated; useful-band rolls retain the
  existing flee-and-return behavior. Fifty hunt-candidate tests, 739 campaign
  tests, and the complete 2,526-test suite pass.
- Run 5512 live-validated the Ambush circuit. Three unavoidable below-band
  transit attackers yielded 160 incidental XP, Haglik mobile 4519 yielded 622
  tagged objective XP, and the prisoner and elite guard were considered and
  skipped as below-band. Dorrik returned full to healer room 3054 at 119,429
  XP, 14,171 short of level 17.

## Character-Independent Autonomy Cycle 31 - 2026-08-13

- Repeated Dwarven Daycare maintenance exposed a carried-only required-loot
  count: a worn pink ice ring and worn linen robe were invisible to the
  acquisition planner, so it could overstate duplicate quantities and revisit
  a carrier whose item was already equipped.
- Required field-item accounting now combines inventory with the authoritative
  worn paper doll. Worn copies satisfy duplicate quantities individually; a
  worn item also closes its single-item carrier branch. The focused starter
  suite passes 985 tests and the full offline suite passes 2,524 tests.
- Run 5499 live-validated the repair. The runner searched the registered old
  doll room for the one remaining ring, traversed the nanny room without a
  consider or attack, and returned safely to healer room 3054 in 50 seconds.
  Runs 5498 and 5500 added 580 and 527 objective XP from Bardoosh and Aruncus.
  Dorrik is level 16 at 117,035 XP, full, and safely logged out at the healer.
- Runs 5502, 5503, 5506, and 5507 then added another 1,612 objective XP from
  Bardoosh, Aruncus, ranger, and Bardoosh. Ring and flight maintenance remained
  bounded between those kills. Dorrik finished full at healer room 3054 with
  118,647 XP, 14,953 short of level 17.

## Character-Independent Autonomy Cycle 30 - 2026-08-13

- Runs 5447 through 5459 showed that a useful cross-level repeat could be
  allowlisted by source mobile VNUM yet remain classified as `fresh` under its
  regenerated level-15 policy ID. That let a measured 50-XP Ambush goblin
  repeat outrank prior-level Shire and Wyvern kills worth 334 and 389 XP.
- The selector now promotes an allowlisted cross-level candidate into the
  productive pool for the current decision. The durable result ledger and all
  live consider, crowd, route, health, and below-band gates remain unchanged.
- Run 5460 live-validated the repair by selecting Shire receptionist mobile
  1131 in room 1157, earning 401 objective XP, and returning Dorrik safely to
  healer room 3054.
- Runs 5467 and 5468 then selected the two strongest cross-level repeats back
  to back: Wyvern ranger 1706 yielded 283 objective XP and Shire receptionist
  1131 yielded 317. Both runs returned safely to healer room 3054. The third
  slot found its lower-value Ambush fallback absent rather than forcing a kill.
  Dorrik is level 15 at 111,291 XP, 3,509 short of level 16. The full offline
  suite passes 2,523 tests.
- Runs 5470 through 5488 continued the measured Wyvern/Shire rotation while
  retaining separate absence and incidental-XP evidence for Shadow Keep and
  Haon Dor. Run 5493 killed Wyvern ranger 1706 for 380 objective XP and crossed
  Dorrik to level 16 at 115,129 XP. The live checkpoint records 345 max HP,
  300 max movement, three practices, subclass `none`, and a safe return to
  healer room 3054.
- Runs 5494 through 5496 proved the post-level handoff. The generic executor
  completed equipment maintenance, refused both Fleshmonger guards on the
  prohibited below-band consider branch, trained `shield block` and `defense
  knowledge`, and killed Aruncus mobile 300 for 519 objective XP. Dorrik
  returned full to healer room 3054 at 115,688 XP with two practices.

## Character-Independent Autonomy Cycle 28 - 2026-08-13

- Runs 5373, 5376, 5378, and 5383 added 332, 337, 533, and 389 XP from
  source-matched Shire and Wyvern targets. Dorrik then crossed to level 15 at
  98,229 XP during the bounded 5385-5386 rotation and returned with full
  resources to healer room 3054.
- Run 5391 then found a wandering source-matched Undead Soldier in room 16618
  and earned 956 XP, returning at full health. Fleshmonger and Ambush routes
  were closed by live below-band evidence instead of being repeated for noise.
- Selector audit found that a fresh or expired Shadow Keep absence probe could
  hide a measured same-reboot repeat after the fresh pool's kill cap removed
  the productive route. The generic selector now compares retry status with
  measured reward evidence and keeps a productive flight route from being
  displaced by a low-value ground retry.
- Focused campaign coverage passes 729 tests and the full offline suite passes
  2,497 tests. This is a local change only; no commit or remote publication is
  due under the 24-hour publication policy.

## Character-Independent Autonomy Cycle 26 - 2026-08-13

- Run 5307 tested the generic source-ranked Ambush Bardoosh reset after two
  incidental goblin interruptions. Live consider was viable and the target
  was source-matched, but DD4's armed NPC critical stab killed Dorrik at
  46/295 HP while Bardoosh was nearly dead. This is durable fatal evidence for
  that exact mobile VNUM, reset room, level, and reboot; it is not permission to
  retreat to low-XP routes or to retry the same fight blindly.
- The executor recovered the corpse through Purgatory, restored equipment,
  reached healer room 3054, and saved and quit. The death penalty reduced XP
  from 92,389 to 87,820. Objective-kill attribution was tightened so route
  interruptions cannot be promoted as the deliberate source target.
- Source-ranked stops now carry a source-derived one-hit critical reserve. The
  ordinary 15%/10% aggressive field thresholds remain in force for normal
  fights, but a source-verified critical that can kill overrides the finish
  floor. High-payoff candidates remain selectable through the existing bounded
  probe/research pools, preserving risk/reward throughput rather than applying
  a blanket armed-target ban. The offline suite passes 2,496 tests.
- The active goal remains generic level-14-to-30 progression. Resume Dorrik
  from the recovered checkpoint, rotate to productive alternatives, and use
  the new reserve evidence to improve subsequent class and equipment policy.
  The Dwarven Nobleman route now permits only the source-level-seven goblin
  lieutenant as a below-band incidental interruption from level fourteen
  onward; the horseman and wyvern remain hard hazards. A bounded live retry
  re-proved that the route reaches the target without accepting low-XP
  interruptions as objectives; the next work is productive level-14 rotation.
  No remote publication or local commit was attempted.

## Character-Independent Autonomy Cycle 25 - 2026-08-13

- Runs 5231 through 5242 continued Dorrik's level-13 source-ranked frontier
  through Shire, Fleshmonger, Grove, provisioning, liquidation, and healer
  return segments without manual target steering.
- Run 5246 crossed Dorrik from level 13 to level 14 at 83,427 XP. The live
  checkpoint recorded 295/295 HP, 280/280 movement, two practices, and
  subclass `none`; run 5247 then completed the post-level daycare recovery at
  healer room 3054. No segment stalled and no death or corpse recovery occurred.
- Runs 5249 and 5251 then killed useful source-matched Ambush targets from two
  distinct reset rooms for 911 and 514 XP, with liquidation and healer return
  after each. Dorrik reached 84,852 XP at level 14 without manual steering.
- Run 5258 added another 551 XP from a productive Ambush repeat; run 5261
  recorded a live but non-viable Ambush identity and skipped it without combat.
  Run 5262 refreshed flight. Runs 5274, 5280, 5284, and 5295 then added
  productive Plains North, Fleshmonger, and Ambush kills. Run 5297 left Dorrik
  at 91,474 XP; run 5302 then left him at 91,544 XP in healer room 3054, with
  the active goal still level-14-to-30 progression.
- The MUD rebooted during this cycle. Runs 5269 and 5271 re-established the
  Dwarven Nobleman route under the new boot; the kill probe reached the hard
  15% withdrawal floor without an objective kill, returned as run 5272, and
  remained negative research evidence rather than a promoted policy. The
  selector rotated away instead of stalling, and later productive alternatives
  carried Dorrik to 91,544 XP in healer room 3054; run 5302 then completed a
  successful Shire continuation and left the campaign ready for resumption.
- The active goal is updated operationally to the next concrete frontier:
  execute generic level-14-to-30 progression, confirm class-aware training and
  the level-30 subclass transition, then expand the same evidence contract to
  the higher bands. No remote publication or local commit was attempted.

## Character-Independent Autonomy Cycle 24 - 2026-08-13

- Dorrik crossed from level 12 to level 13 on run 5142 and completed the
  level-13 maintenance and research sequence without manual intervention.
- Run 5146 completed the registered Mahn-Tor Rock Toad probe safely. The
  campaign then opened the generic source-ranked executor, which continued to
  kill source-matched Fleshmonger and Shire targets through run 5174, returning
  to healer room 3054 after each bounded circuit. Dorrik reached 74,115 XP.
- This validates the two-stage policy lifecycle: a registered `research` row
  acquires evidence, then the runtime selector may choose a safe generic
  source-ranked candidate. Static coverage output must not be mistaken for
  live proof; campaign segments and objective-kill evidence remain the source
  of truth.
- The current read-only DD4 checkout is `7996722`; packaged prerequisite and
  training data retain their pinned `f703daa` evidence revision. No remote
  publication or local commit was attempted.

## Character-Independent Autonomy Cycle 23 - 2026-08-13

- An outbound fastwalk interception now snapshots the pre-intercept hunt
  context. A rejected source-ranked target can no longer advance the relative
  circuit to a later waypoint and then ask the live exit graph for a non-
  adjacent VNUM. The context is restored, the official endpoint is marked
  complete, and the source circuit resumes from there.
- Run 5102 exposed the bug in the Moria large-orc route: the target was seen
  below-band in room 4011, the character reached room 4022 safely, and the
  stale relative segment requested room 4010 before recalling. Runs 5103 and
  5106 then completed clean Fleshmonger kills for 279 XP and 252 XP, returning
  Dorrik to healer room 3054 at level 12 and 65,469 XP.
- The focused route checks and full offline suite pass 2,490 tests. No remote
  publication or local commit was attempted; the active HERO goal resumes at
  Dorrik's level-13 frontier with 9,135 XP remaining to level 14.

## Character-Independent Autonomy Cycle 22 - 2026-08-12

- Added `source_reset_room_vnum` to field stops so a static required-loot
  carrier is evaluated only at its source reset room. Direct-command routes may
  cross a waypoint where the same mobile has wandered, but neither interception
  nor ordinary target evaluation may consume that waypoint as source evidence.
- Applied the boundary to the Day Care ring and linen-robe carriers. The new
  regression proves the nanny is ignored in room 6603 and considered in room
  6602; this is generic endpoint behavior, not a character-specific rule.
- Full offline verification now passes 2,489 tests. Dorrik runs 5094 and 5095
  added 533 live XP and returned him to healer room 3054 at level 12 and 64,515
  XP. The HERO goal remains active: the next concrete frontier is level 13 and
  then executable policy coverage beyond the current level-12 band.
- No remote publication was attempted. The local worktree remains the durable
  source of truth under the recorded 24-hour commit policy.

## Practical Milestones

1. **Structured observations — complete.** Convert text and GMCP into typed events
   such as room entry, prompts, health changes, combat, quests, items, levels, and death.
2. **Character state — complete.** Build current state from events and persist
   timestamped snapshots.
3. **Rule-based starter bot - complete.** Automate login, character
   creation/selection, the tutorial, basic movement, recovery, and safe failure
   handling.
4. **Reports - complete.** Produce Markdown and JSON summaries with progress, failures,
   balance signals, and representative run-time commentary.
5. **Campaign execution foundation - complete.** Add checkpoints, resume support,
   budgets, stuck detection, and controlled long-running progression.
6. **Mudlet bridge.** Create a small Lua integration that exchanges commands, output,
   GMCP, and commentary while leaving the normal client visible.
7. **VirtualBox orchestration.** Start and monitor a Windows VM, launch the Mudlet
   profile, collect artifacts, and recover from client or VM failure.
8. **Humanlike commentary.** Turn important events and decisions into concise progress
   notes, observations, frustrations, and game-experience feedback.
9. **AI-assisted policy.** Introduce constrained model decisions for unfamiliar
   situations only after deterministic replay, limits, and evaluation are in place.

## Milestone 1 Exit Criteria

- Text and GMCP parsers are deterministic and independently tested.
- Structured events are written to both JSONL transcripts and SQLite.
- Raw responses and GMCP messages remain unchanged and auditable.
- New DD4-specific examples can be added as fixtures without changing the runner.

Milestone 1 was validated against a bounded live DD4 capture. Sanitized fixtures
cover the server's actual room/prompt format and `Char.Base`, `Char.Vitals`,
`Char.Stats`, `Char.Worth`, `Char.Affect`, `Char.Items`, and `Room.Info` GMCP.

## Milestone 2 Exit Criteria

- The same ordered game events always reconstruct the same character state.
- State covers identity, level and XP, resources, room, exits, stats, currency,
  inventory, affects, quests, combat, and death.
- Every meaningful state change creates a revisioned transcript event and a
  timestamped SQLite snapshot linked to its source event.
- Repeated GMCP does not create duplicate state revisions.
- `show-state` exposes the latest state and complete revision history.

Milestone 2 was validated with deterministic fixture replay and a bounded live
DD4 capture, including text-room enrichment from the later `Room.Info` GMCP.

## Milestone 3 Exit Criteria

- A YAML profile selects name, race, gender, base class, and optional level-30
  subclass target without storing a password.
- Character creation and reconnection are deterministic and transcripted.
- The bot completes the prelude, obstacle course, all required training fights,
  final gladiator/key sequence, and Victory portal.
- It recovers below 25% health, provisions food and water, equips tutorial
  rewards, practices an available class ability, reaches level 2, saves, and
  quits.
- Runtime, command, reconnect, and repeated-command limits stop stuck runs.

Milestone 3 was validated live with a newly created Human female Mage targeting
Warlock. The bot reached level 2 during advanced training, completed the final
combat and provisioning steps, practiced `magic missile`, saved, and quit.

## Milestone 4 Exit Criteria

- `report` renders the same stored run as either concise Markdown or structured JSON.
- Reports show level, XP, health, room, combat, item, and quest progress when observed.
- Failed runs and detected character deaths are called out directly.
- Balance signals report observed progression, combat, and low-health pressure without
  claiming conclusions beyond the recorded evidence.
- First-person commentary is deterministic, traceable to stored decisions and game
  events, and never includes redacted commands or secrets.

## Milestone 5 Exit Criteria

- A campaign YAML binds a character profile to a target level and aggregate limits.
- Campaign, segment, and checkpoint rows survive process restarts in SQLite.
- The campaign resumes its last checkpoint by default and can explicitly start fresh.
- Segment, command, runtime, and stalled-progress limits stop unsafe repetition.
- The verified starter policy is executed as the first campaign segment; unimplemented
  post-tutorial territory blocks with an explicit checkpoint instead of guessing.

This completes the campaign execution foundation, not a claim that every class
already has a verified level-2-to-HERO policy. The next progression work must
collect live evidence for safe XP routes, class abilities, recovery, equipment,
and failure handling before registering each new level-band policy.

## Character-Independent Autonomy Cycle 21 - 2026-08-12

- The campaign now reports a reboot-scoped cure-critical reserve wait before
  unrelated crowd handling when negative fame blocks city service.
- Day Care route evidence was reconciled with `db.c::reset_area`: room 6605's
  old-doll reset supplies one pink ice ring per area reset. The route no longer
  attacks room-6603 wanderers for that loot and performs one exact carrier
  attempt before the existing reset cooldown can seek the second ring.
- Dorrik's live level-12 continuation reached 63,548 XP. Run 5088 earned 241
  XP from the source-matched Fleshmonger guard; run 5091 earned 200 XP from the
  cook and recorded one incidental 20-XP drunk interruption separately. Runs
  5089 and 5090 demonstrated clean bounded return boundaries with no stale
  worker left behind.
- The full offline suite is green at 2,488 tests. The Discord source log and
  streamer were verified together: Codex and USER records both delivered, with
  no duplicate in-flight queue remaining. Remote publishing remains manual.

## Progression Evidence Cycle 1

- Registered the level-2-to-10 Mud School band as research-gated for every base
  class, with class-specific practice candidates.
- Preserved the live evidence: the entrance links to the Loremaster and arena;
  the Loremaster advertises training through level 10; and observed arena rooms
  contain low-tier opponents with safe exits.
- Kept the policy non-executable until a bounded live run proves the combat, XP,
  recovery, and exit sequence. Campaigns now identify this precise gate instead
  of reporting only a generic missing policy.

## Progression Evidence Cycle 2

- Added `arena-research`, a separate level-2 probe that defaults to a level-3
  objective while retaining the existing arena target discovery, 25% health
  retreat, recovery route, safe exit, save, and quit behavior.
- The command is intentionally outside the campaign registry. Its first live
  transcript must show an engagement, XP change, recovery-or-safe-health proof,
  exit, and final level before the level-2-to-10 policy can become executable.

## Progression Evidence Cycle 3

- Added source-backed candidate scoring for exact recall routes, reset placements,
  loot, mobile spawn limits, alignment, aggressive hazards, and current-reboot
  kill history.

## Progression Evidence Cycle 4

- Added source-backed equipment parsing and three explicit loadouts: combat
  prioritizes damroll, pre-level prioritizes positive stats during the final 10%
  of a level, and recovery prioritizes maximum hitpoints and mana before sleep.
- Equipment is audited before changes and confirmed afterward. Waking returns to
  combat or pre-level gear, while newly acquired inventory triggers a fresh plan.
- Bonus gear, large sacks, backpacks, and the girdle of many pouches are protected
  from liquidation. Early progression should acquire a safe sack or backpack;
  the Mahntor girdle remains a later-band objective.
- Live run 200 verified the text equipment fallback, equipped Ararisa's carried
  weapon, preserved her stat-boosting diploma and snowy stone, saved, and quit
  safely without consuming XP or supplies.
- Live run 201 gained 110 XP from two arena boars in 43.6 seconds and exited at
  full health with 218/268 mana. This showed checkpoint overhead, not combat
  pressure, was limiting progress, so the verified level-6 arena batch was
  increased from two to ten kills while retaining all recovery and exit guards.

## Progression Evidence Cycle 5

- Added `money-loop`, which selects source-backed Foundry targets, performs
  bounded hunt and recall trips, liquidates only identified expendable gear at
  compatible safe shops, fills the water skin, and buys the affordable pie
  reserve.
- Corrected mobile reset `maximum_count` evidence to a concurrent spawn limit.
  It is not an object instance limit and does not make a mobile unavailable
  after that many kills; reboot kill history remains useful for XP weighting.
- Live runs 206, 207, and 208 killed Uburz and two Ologs for 196 XP without
  damage. Run 212 identified loot with the Human racial spell, protected and
  equipped Uburz's +1 Intelligence silver circlet, and sold four expendable
  items for 56 coins.
- Live run 213 filled and drank from the buffalo skin, observed a 46-copper pie
  price, and bought one pie with 21 copper-equivalent left. Field hunts now
  continue toward their requested target after safe incidental kills so later
  trips can collect varied drops instead of recalling after every Olog.
- Verified the Circus midget route in run 146 and one bounded kill in run 148:
  43 XP, 94/96 minimum health, purse loot, immediate recall, full recovery, and
  safe return to the Mage Guild.
- Verified the complete money loop in runs 150-151: 51 copper extracted from
  the purse and 8 copper from selling the empty container at the safe General
  Store. Hunt areas are vacated after loot so their reset timers advance faster.

## Progression Evidence Cycle 6

- Grouped compatible sales by shop and made city restocking return to the Mage
  Guild. Run 223 verified the full fountain, Bakery, return, save, and safe quit
  path with two pies carried.
- Money loops now preserve successful hunt evidence and continue to liquidation
  and restocking when a later requested mobile is absent. Runs 224-228 verified
  this with Uburz, an incidental Olog, absent Ushog and Golgog targets, 295 XP,
  29 copper of accepted loot sales, and a safe two-pie finish.
- Run 225 exposed a higher-than-expected Foundry wandering risk: a level-2 Olog
  reduced the lightly armoured level-6 mage to 24/96 health before dying. The
  bot recalled immediately, recovered fully beside the healer, and consumed a
  pie when hunger interrupted recovery.
- Human identify evidence showed Uburz's silver circlet belongs to the Dwarven
  and Goblin Alliance set; pairing it with the dwarven children's pinkish ring
  grants +2 Strength. Repeated metal piping sales decayed until the weaponsmith
  refused the item, so refused duplicates must not be counted as cash reserve.
- Run 229 used four bounded arena kills for 369 XP and advanced Ararisa from
  level 6 to level 7 with 105 maximum health. Run 230 then verified the safe
  return to the Mage Guild with two pies intact. Future liquidation retains the
  best carried combat item for each otherwise-empty wear slot before selling
  expendable gear.

## Progression Evidence Cycle 7

- Run 233 proved the outside-area arena reset loop: ten kills, 698 XP, two
  resets while Ararisa waited at Midgaard's healer, and a safe exit through
  Mud School Safety. Campaign resume now reconciles stale checkpoints against
  the latest persisted character state.
- Run 235 exposed two field-combat faults against Uburz: withdrawal at 25% was
  too late, and a missed opening magic missile suppressed later casts. Run 236
  recovered Ararisa from 36/105 health to full safety. Field fights now flee and
  recall at 60% health, hunger, or thirst, and retry magic missile after either
  a hit or miss result.
- Loot liquidation now audits worn equipment, expands stacked inventory
  quantities, preserves the best combat, recovery, and pre-level loadouts, and
  sells redundant stat gear by actual DD4 item type. Live runs 240 and 242 sold
  duplicate boots, jerkin, cap, circlet, and boots for 139 coins total. Run 243
  converted the reserve into four pies and a filled water skin.
- Pre-level equipment priorities are profile-configurable and source-backed:
  intellectual practices use `2*WIS + INT`, physical practices use
  `WIS + STR + DEX`, mana uses `2*INT + WIS`, hit points use CON, and movement
  uses `CON + DEX`. Ararisa prioritizes intellectual practices, mana, hit
  points, movement, then physical practices.
- Run 244 validated repeated field casting against Olog: three magic-missile
  commands, 97 XP, no health loss, confirmed loot, recall, and safe return to
  the Mage Guild with four pies intact.

## Progression Evidence Cycle 8

- Live `consider` output is authoritative for field combat because area-file
  mobile levels can vary slightly at runtime. Run 247 proved that low-value
  arena targets can be skipped; the same gate now protects fastwalk hunts.
- Runs 250-252 turned the official Moria fastwalk into a verified level-7 mage
  segment. Room 4015 was rejected because its snake can be joined by an orc or
  hobgoblin. DD4 source shows room 4025, two north from the endpoint, has one
  level-7 garter snake and no other mobile reset.
- Run 252 considered that isolated snake a perfect match, killed it for 373 XP,
  recalled, recovered, saved, and logged out in room 3019 at full health and
  mana. The campaign now selects this one-kill field segment for level 7-9
  mages while retaining the arena policy for other classes.
- The command watchdog now resets when room, vitals, movement, XP, level,
  combat, death, or position changes. This permits long real fights while
  retaining a bounded escape for commands the server genuinely ignores.
- DD4 source confirms the level-10 large hobgoblins in Moria rooms 4064 and
  4071 carry purple sanctuary potions. These are future defensive farm targets.
  `HELP VAULT` also permits town vault storage for objects up to five levels
  above the character; future inventory policy should bank valuable usable-soon
  gear instead of selling it.

## Progression Evidence Cycle 9

- DD4 source and the official Ambush fastwalk establish the Miden'nir sack
  route: `6s` from recall, then
  `w,s,s,w,s,w,s,s,e,s,s,open east,e,e` to room 4518. The guaranteed large
  sack reset weighs 50 pounds and holds 400 pounds, so the expedition now
  discards low-value piping and a cap before departure while preserving food.
- Runs 268, 270, and 272 killed a mountain goblin, goblin lieutenant, and
  mountain goblin for 361, 210, and 244 XP. The first run reached room 4518 but
  could not carry the sack; the later load plan leaves sufficient capacity.
- Miden'nir is productive but spawn-sensitive. A level-9 dark horseman joined
  run 270, and two level-7 mountain goblins occupied the entry in run 274.
  Conservative flee, recall, healer recovery, and safe logout paths worked in
  both cases. Room 3570 is a source-proven route choke point, so no alternate
  path can bypass a dangerous occupant.
- Required expedition items are now verified from inventory before a run can
  succeed. Run 272's early reserve withdrawal was retrospectively corrected
  from success to failure because it did not acquire the sack.
- Leaving an arena area for 90 seconds successfully reset it in run 267, but
  the resulting targets were below the efficient XP band. Ararisa is safe at
  level 7. Run 275 found one reset goblin, killed it for 216 XP, and returned
  safely at full health and mana with 23,491 XP. Run 277's Moria snake survived
  to the withdrawal threshold; flee damage credit offset the penalty for a net
  31 XP, confirming that Moria remains research-only.
- DD4 practice formulas establish a two-level mage unlock plan. At level 8,
  three intellectual practices train `illusion magiks`, `invis`, and `invis`;
  the Miden'nir runner then verifies invisibility at Temple origin before
  entering the choke point. At level 9, practices train `evocation magiks`,
  `chill touch`, and `chill touch`. Level-9 combat prefers chill touch's
  source-backed 19-29 damage range and falls back to magic missile if the
  server rejects it.

## Progression Evidence Cycle 10

- The HERO campaign now selects Miden'nir progression from both level and
  persisted inventory. Level 7 uses one bounded live-considered goblin hunt;
  level 8 selects the invisible sack expedition until `a large sack` appears,
  then levels 8-9 resume bounded goblin segments.
- Empty, moved, or crowded goblin spawn windows are safe retry checkpoints.
  Campaign hunts do not require a kill to complete a segment, while XP gain
  still resets the stalled-segment counter. Ararisa's campaign permits ten
  consecutive no-progress segments so ordinary area reset timing does not
  prematurely block the run.
- Source inspection after run 278 showed that the fastwalk endpoint has no
  goblin reset; successful endpoint kills were wandering mobiles. Campaign
  hunts now inspect the endpoint and room 3506, one east, where DD4 directly
  resets a mountain goblin. The probe remains bounded to that single room.
- Field runners with new level-8 or level-9 practices detour from the Mage
  Guild to the Mud School Loremaster before departure. Training remains active
  while GMCP decrements the practice balance, preventing a partially completed
  practice plan from accidentally starting the fastwalk.
- Campaign sack attempts require a verified GMCP invisibility affect and treat
  a safely completed no-sack attempt as retryable. Manual `midennir-research`
  remains strict and reports a missing sack as failure.

## Progression Evidence Cycle 11

- Live runs 279 and 280 gained 210 and 369 XP from Miden'nir goblins. Run 280
  completed two sequential fights and returned safely to the Mage Guild at full
  health and mana, leaving Ararisa 749 XP from level 8.
- Run 281 found neither a wandering goblin at the fastwalk endpoint nor the
  room-3506 reset. It returned safely with no XP change in 48.7 seconds,
  confirming that an empty area remains a cheap, bounded retry rather than a
  reason to force a deeper hunt.
- Source-backed hunt discovery now indexes Ambush, Moria, and Thalos and offers
  an explicit `--include-xp-only` mode. The default remains loot-oriented, while
  progression research can also inspect targets without saleable drops.
- At level 10, source ranking identifies Ambush's level-8 to level-10 goblins
  as the strongest reachable loot-and-XP candidates. Thalos is rejected while
  its level-11 mimic can wander, and useful Moria targets remain behind mixed
  level-10 to level-13 opposition. Ambush is therefore the next level-band
  research candidate, not yet an executable policy.
- Live run 284 confirmed that level-7 Ararisa considers the remaining Mud
  School boars and wolves "no match" and correctly refuses their poor XP.
  Arena patrols now distinguish under-level occupants from an empty arena:
  the former save and exit immediately, while only the latter trigger an
  outside-area reset wait.

## Progression Evidence Cycle 12

- Miden'nir runs 282 and 285 gained 208 and 209 XP. Run 291 then killed a
  level-7 goblin lieutenant and advanced Ararisa to level 8 with 24,850 XP,
  115 maximum hit points, 316 maximum mana, and 220 maximum movement. She
  withdrew at the safety threshold and recovered in the Mage Guild.
- Foundry run 287 gained 118 XP from Uburz, while run 288 gained only 33 XP
  from an incidental Olog before the intended target was found absent. These
  results reinforce Miden'nir as the better current progression loop.
- A level-2 drunk interrupted the run-290 shop route. Delayed GMCP enemy data
  made the utility runner issue a second flee after the first had succeeded,
  causing an avoidable second XP penalty. A latched flee-success state now
  recalls immediately despite one stale enemy update, with regression coverage.
- A run that reaches its objective level before withdrawing safely now counts
  as successful. This preserves run-291-style level advancement without
  weakening safety failures below the requested objective.
- DD4 source defines one area pulse as 30-90 seconds. Empty areas reset at age
  8 and receive a randomized post-reset age of 0-3; occupied areas can be
  delayed beyond age 14. Progression waits should therefore leave the area and
  use bounded multi-minute retries instead of waiting beside missing spawns.
- The next executable stage is the level-8 practice plan followed by a verified
  invisibility-assisted expedition to room 4518 for the large sack. Food and
  water are restocked before departure, and low-value piping and cap weight are
  discarded at the safe origin.

## Progression Evidence Cycle 13

- Run 292 restocked Ararisa to seven pies and a filled buffalo water skin.
  Run 293 exposed stale enemy data after fleeing, and runs 294-295 exposed two
  practice-audit timing gaps without placing the character outside safe rooms.
- Practice balances are now parsed from both Loremaster and `score` output,
  retained across movement commands, and audited explicitly before level-8 or
  level-9 field departure. Invisibility retries use the policy's complete
  eight-attempt budget before a safe abort.
- The level-8 sack policy now uses the Dragonhoard Bank vault. Run 296 lodged
  low-value sleeves, vest, cape, belt, bracer, and leg guards, reducing field
  carry weight to 67/140 while preserving stat gear, weapon, diploma, light,
  provisions, and water.
- Run 296 practiced `illusion magiks` once and `invis` twice, established a
  verified 10-tick invisibility affect, traversed the source-backed Ambush route
  without combat, and acquired the guaranteed large sack in room 4518.
- Ararisa recalled, recovered to 115/115 health, 316/316 mana, and 220/220
  movement, then saved and logged out in the Mage Guild. Her persistent
  inventory now contains the large sack, six pies, and buffalo water skin.
  The campaign can advance to its level-8 Miden'nir goblin hunt policy.

## Progression Evidence Cycle 14

- Run 297 revealed that two identical mountain-goblin room lines represented
  two attackers. Field policies now preserve mobile multiplicity, reject any
  inspected room containing more than one mobile, and flee immediately when
  GMCP reports multiple active enemies.
- The large sack is now durable campaign evidence and is lodged in the town
  vault between expeditions. Runs 298-301 reclaimed Ararisa's armour and left
  43-48 pounds free for loot; run 298 then killed a solitary level-7 goblin
  for 260 XP while losing only 15 hit points.
- The northern Miden'nir policy now inspects a nine-room source-backed circuit.
  At level 8 it establishes invisibility before departure and restores it after
  each kill, allowing every room to be inspected before combat. Run 300
  traversed the complete circuit at full health and gained 117 XP.
- Dark horsemen are now eligible when solitary. They are level 8, have no
  current-reboot kill penalty, and their resets carry one gold coin. Mixed
  goblin/horseman rooms remain forbidden. Recall-room pies are collected before
  departure to extend the food runway.
- Ararisa ended run 301 safely in the Mage Guild at level 8 with 25,474 XP,
  full resources, six pies, and a filled water skin. The suite contains 328
  passing tests.

## Progression Evidence Cycle 15

- Run 303 proved that reboot fuzz can load a source-level-8 dark horseman at
  level 9. Although `consider` called it a perfect match, Ararisa could not
  damage it quickly enough to finish above the 70% health threshold. Horsemen
  are therefore excluded from the level-8 policy, superseding Cycle 14.
- Routine hunts no longer revisit the vault or repeat the level-8 training
  audit. The sack is already vaulted, combat armour is already worn, and
  repeated preparation introduced response-order and safe-detour failures
  without improving a field run.
- Runs 306-310 completed as five consecutive successful campaign segments
  without manual intervention. Runs 308 and 309 killed three goblins for
  415 total XP; hunger in run 309 consumed exactly one pie. Ararisa ended at
  26,025 XP with full resources and four pies.
- Source resets place ordinary goblins in rooms 3506, 3509, 3512, and 3513,
  but the mobs wander. The circuit now adds a western sweep through rooms
  3516, 3515, 3518, 3522, 3511, and 3508 while avoiding the poison wyverns in
  3521 and the mixed opposition in the goblin headquarters.
- Field circuits now recall below 25% movement. All 331 tests pass.

## Progression Evidence Cycle 16

- Runs 311-320 sustained the expanded Miden'nir circuit through ten successful
  autonomous campaign segments. Ararisa reached 27,904 XP at level 8 before
  Ambush research began.
- Run 321 rejected the source-level-8 raider after a safe flee and net 9-XP
  loss. Run 322 killed the wounded goblin and war dog for 521 XP, returned at
  full resources, and supplied saleable armour; run 323 sold that loot safely.
- Campaign runs 324-326 proved automatic Ambush hunting and liquidation. They
  gained 372 XP from a reboot-fuzzed level-7 wounded goblin and 249 XP from the
  war dog, then returned to the Midgaard healer. Interrupted-run recovery now
  closes orphaned runs, campaign segments, and campaign status records before
  a resume.
- Run 327 exposed a poor level-8 matchup: three magic-missile attempts left the
  higher-HP wounded goblin unfinished, producing a net 44-XP loss after the
  safety flee. The level-8 campaign now goes directly to the lower-HP war dog
  and defers the wounded goblin until level 9's `chill touch` training.
- Run 328 validated the revised route with a 294-XP war-dog kill, only 22 hit
  points lost, full recovery, safe logout, and a successful campaign
  checkpoint. DD4 source confirms the retained collar grants +1 damroll. All
  338 tests pass.
- The read-only DD4 mirror was fast-forwarded from `9bdd510` to upstream
  `0482387` on 2026-07-20 before planning the next level band. Consequential
  source-backed research now begins with a once-per-working-day refresh.

## Progression Evidence Cycle 17

- A live raider probe showed that favorable `consider` text is not sufficient
  protection from weapon burst. Run 363 died after a failed flee; the bot then
  found room 427 in Purgatory, looted the corpse, entered the portal, and
  recovered beside the Midgaard healer. Purgatory recovery now keys on area and
  room identity as well as the transient death flag.
- Source-backed equipment keywords now avoid ambiguous abbreviations, and light
  objects have an explicit equipment slot. Run 367 verified the recovered
  illumination banner in the light slot, killed a war dog and goblin looter for
  733 XP, recalled, recovered fully, and logged out safely at 27,980 XP.
- Ambush departures now eat and drink at the safe origin. Routine healer
  recovery no longer polls the hard-coded `heal` menu before sleeping.
- Containers reduce item count and isolate duplicate keywords, but DD4 includes
  their contents in carried weight. Use the 50-pound large sack for organization
  only when capacity permits; use the vault for actual weight relief, and keep
  the active light, provisions, water, and selected loadout directly accessible.
- Runs 368-370 verified the campaign maintenance cycle: sell looter armour,
  refill the skin, and buy a reboot-priced food reserve. Known inventories with
  no pie now select restocking before combat, including GMCP inventories stored
  as serialized JSON.
- Run 371 showed that a reboot-fuzzed looter can force a safe flee after the dog.
  Optional hunt stops now carry their own health reserve; run 372 verified that
  the 95% looter gate recalled after a 175-XP dog kill instead of forcing the
  second fight. Ararisa ended safely at 28,356 XP.
- Runs 379-380 proved that even a full-health level-8 mage can suffer extreme
  looter weapon burst despite a favorable `consider`; run 380 escaped at 2 HP.
  The level-8 policy is therefore dog-only. Critical recall recovery now moves
  north from room 3001 to the healer before sleeping.
- Campaign collar liquidation now requires more than the two active collars as
  well as carry pressure, so expiry of a temporary Strength effect cannot cause
  a pointless sale trip.

## Progression Evidence Cycle 18

- Reboot-scoped dog/goblin rotation and one-kill Miden'nir segments moved
  Ararisa through level 8 without repeating the lethal raider experiment. Run
  398 reached level 9 at 31,795 XP with 126 hit points and returned safely.
- Source parsing now ranks candidates using both reset-equipped weapons and
  DD4's fuzzed mobile level, hit-point, and peak-round damage formulas. The
  armed fanatical guard, raider, and archer are rejected at Ararisa's current
  health; the unarmed vile goblin remains consider-only evidence.
- Run 401 verified carry-aware restocking after reconnecting in the Bakery:
  four pies were purchased, the skin was filled, and Ararisa returned to the
  Mage's Laboratory. Invisible shop rejection now uses `vis` and retries.
- Run 402 trained evocation and `chill touch`, killed the wounded goblin and
  war dog for 494 XP, and recovered beside the healer. Run 403 repeated the
  bounded pair for 422 XP. Ararisa is level 9 at 32,711 XP with 6,989 XP to
  level 10.
- Field cleanup now loots before sacrificing the corpse for its source-backed
  level-difference coin. When already hungry, the bot may collect and eat an
  edible severed body part. Overflow handling preserves stance, stat, food,
  water, and capacity gear before selling, vaulting, or donating redundant
  unsellable objects.

## Progression Evidence Cycle 19

- Run 404 verified corpse sacrifice for one silver and safely recalled when the
  wounded-goblin fight left only 85 of 126 hit points before the optional dog.
  Ararisa ended at 32,905 XP, 6,795 XP from level 10.
- Serialized GMCP inventory now strips ANSI colour before quantity parsing.
  This correctly recognized three collars, and run 405 sold only the redundant
  third collar while preserving both worn +damroll collars.
- Missing primary weapons block combat. A dedicated safe Midgaard maintenance
  policy buys source object 3020, a one-pound dagger, verifies DD4's `[weapon]`
  equipment slot, and returns to the Mage's Laboratory. Run 406 exposed the
  display-label mismatch; run 407 recognized the already-wielded dagger,
  returned home, saved, and checkpointed successfully.
- DD4 source confirms a worn pouch is the only place a player can draw a potion
  from while fighting. Field departures now audit pouch contents at recall,
  stow only identified purple sanctuary and black cure-critical potions, use
  healing at or below 55% health, and use sanctuary at or below 80% when the
  effect is absent. Unknown potions are never consumed automatically.
- Run 408 live-validated the empty-pouch audit and armed field path. Ararisa
  killed a war dog for 158 XP, stayed above 92 of 126 hit points, gained one
  silver from corpse sacrifice, recovered fully, and ended at 33,063 XP.
- Run 409 exposed that generic overflow donation could discard the only water
  skin. Food and water containers are now protected from sale and donation,
  and the unsafe Mud School fallback that removed worn armour was deleted.
- Runs 410-411 stopped safely after exposing a silent connection and an
  exhausted equipment-maintenance loop. Reads now have a 45-second inactivity
  timeout with bounded reconnects, exhausted characters sleep before
  maintenance, and non-movement stalls in safe rooms fail in place instead of
  repeatedly recalling and consuming movement.
- Run 412 verified emergency provisioning from an otherwise unaffordable
  state. The bot took one bounded 300-copper Dragonhoard loan, bought and ate a
  pie, bought a buffalo water skin, drank, saved, and quit safely at General
  Supplies with five pies, the skin, full health and mana, and 206 movement.
- Run 413 killed a wounded goblin for 180 XP but exposed an equipment loop:
  DD4 classed the looted wooden spear as a lance that Ararisa could not use.
  Explicit wear rejections now blacklist that item for the run, discard the
  stale stance plan, and force a fresh paper-doll audit.
- Run 414 live-validated that recovery. The bot rejected the spear once,
  re-wielded and verified the retained dagger, recalled, changed into recovery
  gear, slept, restored combat gear, and saved safely in the Mage's Laboratory.
  Ararisa is level 9 at 33,243 XP, 6,457 XP from level 10.
- Runs 415-416 showed that duplicate source prototypes named `a wooden spear`
  caused the sale planner to retain the unusable lance. Object parsing now
  preserves DD4 extra flags, applies the Knight-only lance and Ranger-only bow
  rules, and rejects ambiguous display names if any matching prototype is
  class-incompatible.
- Run 417 produced the correct weaponsmith sale route, but a wandering city
  drunk initiated combat before the shop. The utility policy fled and recalled
  safely at an 80-XP retreat cost; no sale was attempted. Return-home recovery
  now moves north from recall to the healer before sleeping.
- Run 418 safely restored Ararisa to the Mage's Laboratory with full health and
  mana and 143 movement. She remains level 9 at 33,163 XP, 6,537 XP from level
  10, with the 12-pound spear retained pending a lower-risk disposal route.
- Run 419 verified the risk/value disposal rule: under at least 90% carry
  pressure, identified class-incompatible loot worth at most 100 copper is
  donated in the guild instead of risking a shop journey. The spear was removed
  safely and carry weight fell from 136/140 to 124/140.
- Run 420 completed a two-kill Ambush segment without disturbing the equipped
  dagger. The wounded goblin and war dog yielded 271 XP; the bot looted and
  sacrificed both corpses, recalled, recovered beside the healer, and created
  checkpoint 125 at 33,434 XP with full health and mana.
- Run 421 safely donated the next wooden lance under the same policy, retained
  both combat collars and four pies, and reduced carry weight to 119/140.

## Progression Evidence Cycle 20

- Runs 422-423 searched the source-backed Miden'nir horseman reset room and
  all four connected trail rooms under invisibility. Both horsemen had
  wandered elsewhere, so the bot recalled without combat.
- Runs 424-426 exposed two false crowd signals in the vile-goblin room.
  Occupancy now uses only the latest room response, and object source parsing
  retains room descriptions so `A piece of leather armor is here` is not
  mistaken for a mobile. The fixed prisoner is the only explicitly permitted
  noncombat bystander; unknown or duplicate mobiles still abort the hunt.
- Run 427 live-considered the unarmed level-9 vile goblin an easy kill and
  returned without attacking. Run 428 repeated the check, killed it at full
  126/126 health for 322 XP, looted and sacrificed the corpse, recalled, and
  recovered safely. Run 430 repeated the kill for 382 XP and returned with
  99/126 health.
- Field recovery now latches an approved reserve while walking between the
  healer and recall. A route no longer reverses for a redundant second sleep
  merely because normal city movement drops the character just below 90%.
- Run 432 disproved unattended safety for the vile goblin: poor combat rolls
  were followed by repeated flee failures and death, costing 1,219 XP. The
  target is demoted to research and cannot be selected by the campaign until
  potion-backed survival is live-validated.
- Run 433 traversed Purgatory, recovered every corpse item, entered the portal,
  slept beside the healer, and saved in the Mage's Laboratory at 126/126
  health. Death now clears stale combat and flee state immediately, and a
  completed recovery clears its diagnostic failure.
- Emergency-potion tracking now retains quantities. Loot cleanup puts all
  exact-known purple sanctuary or black cure-critical potions into the worn
  pouch. Sanctuary is used before avoidable combat damage; healing remains
  reserved for health at or below 55%.
- Run 434 live-validated the invisible route from the Moria fastwalk endpoint
  to the first sanctuary-potion reset in room 4064. The large hobgoblin had
  wandered, so the consider-only policy recalled, recovered, and saved without
  combat.
- Run 436 exposed a false-positive fly-potion purchase while invisible. The
  Magic Shop workflow now becomes visible, repeats the listing, verifies the
  potion in inventory, and only then quaffs it. Run 437 bought the reboot-priced
  potion for 94 copper and confirmed 34 ticks of flight.
- Runs 438-440 used flight to verify both potion resets and DD4's `where`
  locator. Source flags confirm the large hobgoblins are scavengers that stay
  in Moria but are not sentinels, and live output showed both wandering between
  generic tunnel and cave rooms.
- Run 441 safely considered one large hobgoblin in room 4071: DD4 reported
  `The perfect match!` and that Ararisa was slightly healthier. Consider-only
  probes may assess a target around bystanders, but attack-capable policies
  retain the strict isolated-target gate. The bounded search now checks rooms
  4064, 4069, 4071, and 4072 before recalling.
- Run 442 exposed a zero-duration invisibility affect that was being treated as
  active. An aggressive orc initiated combat, but the policy recalled safely,
  recovered at the healer, and saved. Affect checks now require a positive
  duration when DD4 supplies one.
- Run 443 exposed ambiguous `hobgoblin` command targeting: a small hobgoblin was
  considered and attacked when the large carrier was absent. The policy fled
  at high health and recovered safely. Moria potion stops now require the exact
  large-hobgoblin room description and reject any second mob sharing the
  `hobgoblin` command keyword. No sanctuary potion has been recovered yet.
- Run 445 live-validated the corrected targeting policy. It ignored a small
  hobgoblin and unrelated mobiles throughout the four-stop circuit, issued no
  combat command, and returned at full health. Run 446 then found no fresh
  source-ranked Foundry target, and run 447 confirmed the two carried war-dog
  collars were not accepted by the current sale plan. Money acquisition remains
  the next blocker before further potion provisioning.

## Progression Evidence Cycle 21

- Run 448 exposed two city-safety faults: a wandering drunk attacked during an
  unprotected healer route, and recalling from recall left the policy waiting
  for a room change that could never occur. Mage field and supply routes now
  cast invisibility before crossing Midgaard, and recall no longer creates a
  pending travel origin.
- Runs 449-451 live-validated safe invisible travel and bounded missing-target
  handling. Uburz and Ushog were absent from the Foundry, so the policies
  returned without combat instead of waiting inside the area and delaying its
  reset.
- Run 452 recorded the level-9 Mage guild state: chill touch, invisibility,
  evocation, and illusion are practised to 36; alteration is 24, with one
  physical and no intellectual practices. Source prerequisites require
  alteration 30 for fly, so the spell cannot yet replace potions.
- Run 453 showed that the original Moria circuit reached the potion carrier
  with too little movement when flight was absent. The bounded search now
  covers the connected maze, cave, and tunnel rooms while preserving a recall
  reserve.
- Run 454 used one bounded 300-copper bank loan, safely becoming visible only
  at the bank and shops, then bought six pies and refilled the water skin. Run
  455 bought a light blue potion at the current reboot price of 94 copper and
  verified 33 ticks of flight.
- Run 456 found an isolated source mob 4055 in the expanded maze circuit,
  confirmed `The perfect match!`, and killed it from full health for 505 XP.
  The policy looted its purple sanctuary potion, put it in the worn pouch,
  recalled, recovered fully beside the healer, and saved at 33,175 XP with
  6,525 XP remaining to level 10.
- Run 457 found no second eligible potion carrier. It ignored unrelated veteran
  warriors, preserved the pouch-held potion, recalled at full health, recovered
  movement beside the healer, and saved safely.
- Run 458 live-validated the protected progression loop. Ararisa drew the
  purple potion from her worn pouch during combat, confirmed sanctuary, and
  killed the level-9 vile goblin for 465 XP while losing only 14 hit points.
  She recovered fully and saved at 33,640 XP, 6,060 XP from level 10.
- Level-9 Mage campaign selection now checkpoints exact emergency-potion
  quantities. It may choose the vile goblin only when a purple potion is
  confirmed in the pouch; otherwise it rotates through the verified Moria
  acquisition circuit and falls back to safer exterior kills when the carrier
  is absent.

## Progression Evidence Cycle 22

- Runs 459-461 exercised the autonomous selector end to end. Ararisa gained
  336 XP from safe exterior targets, killed a large hobgoblin for 432 XP and
  stowed its purple potion in her pouch, then quaffed it after engaging the
  vile goblin and killed that target for 309 XP. She finished fully recovered
  at 34,717 XP.
- Run 462 found both potion carriers absent, but a level-1 drunk attacked on
  the Midgaard route. The bot fled and paid DD4's level-scaled 80-XP escape
  penalty. A lone forced attacker at or below the character's level is now
  finished regardless of its poor voluntary-hunt XP; higher-level or multiple
  attackers retain the emergency-flee policy.
- Runs 463-464 recovered the loss with a 237-XP wounded goblin and a 310-XP
  large hobgoblin. Ararisa ended fully recovered at 35,184 XP with another
  purple sanctuary potion stored in her worn pouch and 4,516 XP remaining to
  level 10.
- Runs 465-467 completed the protected loop twice more: two potion-backed vile
  goblin kills and one Moria carrier kill produced 940 XP, ending at 36,124 XP.
- Runs 468-470 showed two limitations in the unprotected fallback. A no-flight
  Moria circuit could not search beyond the first carrier room while preserving
  a recall reserve, and unlucky wounded-goblin fights forced XP-costly escapes.
  Level-nine fallback now hunts only the proven lower-burst war dog. When the
  campaign has at least 90 copper-equivalent and either Moria is selected or
  progress has stalled twice, it first checks the reboot-fuzzy Magic Shop price,
  buys one light blue potion, and verifies flight before field work.
- Combat preparation retains identified purple sanctuary and black
  cure-critical potions in the worn pouch. Sanctuary is used before avoidable
  combat damage; healing potions remain reserved for 55% health or lower.

## Progression Evidence Cycle 23

- Run 471 bought the reboot-priced light blue potion for 94 copper and verified
  33 ticks of flight. Run 472 then found a carrier, but a wandering warrior
  joined on the opening pulse; conservative multi-attacker withdrawal prevented
  a dangerous unprotected fight.
- Run 473's war-dog fallback gained 206 XP without taking damage. Runs 474-475
  discarded only reboot-exhausted duplicate gear, preserved the two worn
  +damroll collars, bought two pies, and refilled the water skin.
- Run 476 used flight to find an isolated carrier, gained 405 XP, and stowed its
  sanctuary potion. Run 477 spent it against the vile goblin for 221 XP while
  taking only 10 damage. Run 478 gained another 368 XP and a purple potion.
- Run 478 exposed command-response reordering: corpse cleanup advanced before
  the delayed loot response made the potion visible, leaving it loose in the
  backpack. Loot cleanup now issues an explicit inventory synchronization
  before potion stow. Campaign selection also recognizes a confirmed loose
  purple potion, and every fastwalk departure moves it into the worn pouch
  before field combat.

## Progression Evidence Cycle 24

- Runs 479-480 live-validated the synchronization repair end to end: the loose
  purple potion was moved into the worn pouch at departure, quaffed before the
  vile-goblin fight, and produced a protected 269-XP kill.
- Runs 482-486 rotated between conservative Moria searches and verified
  exterior targets. Run 486 killed an isolated large hobgoblin for 288 XP,
  then explicitly synchronized inventory and stowed the newly looted sanctuary
  potion in the pouch.
- Run 487 drew that potion from the pouch, confirmed sanctuary, and killed the
  vile goblin for 333 XP. Ararisa recovered fully at 38,143 XP, 1,557 short of
  level 10, and run 488 replenished food.
- Run 486 also exposed that recent XP progress could suppress flight
  maintenance and permit an unflown Moria departure. An affordable light blue
  potion is now routine level-nine travel preparation rather than a
  stall-triggered fallback; a reboot-price purchase failure still disables
  repeated attempts for that campaign state.
- Run 492 exposed an emergency-provision loop after the invisible bot's
  Quartermaster purchase was refused. The supply path now becomes visible,
  clears the pending order, and retries instead of walking repeatedly between
  General Supplies and the Mud School entrance.
- Run 493 live-validated that recovery: Ararisa became visible, used the
  existing bounded bank advance, bought five pies at the current reboot price,
  and returned safely.
- Run 494 stopped the Miden'nir horseman probe at the observed South Bridge
  wander room. Both coin-carrying horsemen were together there, so the crowd
  guard skipped consideration and combat before completing the circuit safely.
  The horseman loop remains research-only until an isolated target is observed
  and assessed.

## Progression Evidence Cycle 25

- Level-10 Mage progression is now registered through two bounded policies:
  acquire a sanctuary potion from an isolated source-level-10 large
  hobgoblin, then spend it against the source-level-9 vile goblin. Both
  policies target level 11 and retain live consider, crowd withdrawal, health
  retreat, healer recovery, potion-pouch handling, and a one-kill limit.
- Run 495 found two large hobgoblins elsewhere in Moria but completed the
  circuit without an eligible encounter. It recalled with 24 movement, slept
  in the healing room, and returned safely without forcing combat.
- Run 496 rotated to the proven Ambush exterior, killed one war dog for 204 XP
  while taking 17 damage, looted a collar and one silver coin, then recovered
  fully. Ararisa reached 38,467 XP, 1,233 short of level 10.
- Run 497 identified the new collar as another 20-pound +1 damroll item,
  preserved the two useful existing collars, donated only the redundant copy,
  saved, and quit safely.

## Progression Evidence Cycle 26

- Runs 498 and 501 confirmed from live `where` output that both Moria potion
  carriers continue to wander through the registered maze and large-cave
  circuit. Run 498 completed without an encounter; run 501 intercepted one.
- During run 501 an orc joined after the initial room audit. Ararisa killed the
  nearly finished carrier for 250 XP, immediately switched to multi-attacker
  withdrawal, fled the remaining orc, and accepted an 80-XP escape penalty.
  She recalled at 32/126 health, recovered fully at the healer, and saved at
  38,739 XP, 961 short of level 10. The disrupted corpse cleanup yielded no
  sanctuary potion, so this is safety evidence rather than a clean acquisition.
- Run 499's exterior fallback killed another war dog safely, but reboot
  repetition reduced the reward to 102 XP. Its coin raised Ararisa's reserve to
  65 copper; flight remains unaffordable at the current 94-copper price.
- Field departures no longer eat a pie or drink the water skin unconditionally.
  The origin queue now consumes only after a live hunger or thirst signal,
  while the existing missing-provision and preflight checks remain active.
  This preserves scarce food during short repeated hunt segments.

## Progression Evidence Cycle 27

- Runs 502-503 live-validated conservative target selection and provision
  preservation. Moria's carrier shared a room with a brown snake and was
  skipped; the Ambush fallback then killed a war dog for 152 XP without
  consuming any of the three carried pies.
- Runs 506-507 repeated the bounded rotation. The empty Moria circuit caused
  no loss, and a war dog produced another 135 XP for only 11 damage. Ararisa
  retained all food and recovered fully.
- Run 509 killed a wandering large hobgoblin for 290 XP, but an orc arrived
  before corpse looting completed and a snake attacked after the first escape.
  Fleeing and recalling from the two combats cost 80 XP each, leaving a net
  gain of 130 XP and no potion.
- Run 510 intercepted another isolated carrier, gained 339 XP, looted and
  pouched its purple sanctuary potion, sacrificed the corpse for one silver,
  and recovered safely. Ararisa saved at 39,495 XP, only 205 short of level
  10, with 95 copper-equivalent and three pies.
- DD4 source confirms `check_autoloot()` runs synchronously inside the kill
  immediately after corpse creation. Combat fastwalks now issue the idempotent
  `config +autoloot` at the safe recall origin, securing potions, equipment,
  and coins before a wandering mobile can interrupt post-kill commands.

## Progression Evidence Cycle 28

- Run 511 spent 94 copper on flight, leaving one copper and three pies. Runs
  512-513 then completed the Moria carrier loop: the second carrier yielded
  296 XP, autoloot secured its purple potion synchronously, and Ararisa reached
  level 10 with 136 HP, 373 mana, and 240 movement.
- Runs 514, 516, and 517 cleanly exercised the level-10 protected rotation.
  Two vile goblins yielded 205 and 240 XP, while an isolated large hobgoblin
  yielded 290 XP and another sanctuary potion. Corpse sacrifices raised the
  reserve to four silver without consuming the remaining field food.
- Runs 515 and 518 demonstrate why gross kill rewards cannot drive policy
  selection. Run 515 withdrew after a warrior joined the carrier fight and
  lost 52 net XP. Run 518 killed an orc for 224 XP, but three forced escapes
  and two failed recalls produced a 37-XP net loss before safe recovery.
- Run 519 returned to an isolated carrier, gained 286 XP, autolooted its
  potion, and reached six silver. Run 520 found no eligible Ambush target and
  returned without forcing combat. Ararisa saved at 40,801 XP, 7,699 short of
  level 11, with full health and mana, two pies, and the water skin.
- Source inspection identifies the level-8 goblin raider in Ambush room 4506
  as an untried reboot-fresh candidate carrying six saleable items, but its
  fuzzed level range reaches 10 and its weapon peak is 125 damage. The new
  `ambush-research --raider-probe` command follows the exterior route under
  invisibility and issues `consider` only; combat remains disabled pending
  live evidence.

## Progression Evidence Cycle 29

- Run 521 reached the exact goblin raider in Ambush room 4506 under
  invisibility. Live `consider` reported an easy kill with Ararisa healthier,
  and the probe returned without starting combat.
- Run 522 repeated the gated route at full health, quaffed a confirmed purple
  sanctuary potion after engaging, and killed the level-8 raider for 368 XP
  without losing a hit point. Autoloot secured its hard leather helmet, the
  corpse yielded one silver, and Ararisa returned to heal, save, and quit at
  41,169 XP, 7,331 short of level 11.
- Run 523 identified the 30-pound helmet as level-7 armour and sold it safely
  for 54 copper. The bank diverted half toward Ararisa's loan, leaving 98
  copper-equivalent in hand and reducing carried weight from 139/140 to
  110/140 while preserving food, water, and stat gear.
- The level-10 policy now treats the raider as a protected target only: exact
  isolated target, favorable live consider, full health, sanctuary, and one
  kill per segment. Reboot-local kill counts rotate sanctuary expenditure
  between the raider and vile goblin so repeated kills do not crowd out the
  fresher productive target.

## Character-Independent Autonomy Cycle 1

- The master objective is now arbitrary valid race, gender, base-class, and
  subclass-target progression from creation to HERO, with evidence-derived
  feedback, analysis, and human-readable commentary. Character names may
  identify credentials and history but must never choose behavior.
- `dd4tester/data/archetypes.json` is the single source for base-class aliases,
  subclass relationships and availability, primary stats, initial practice
  skills, level-gain priorities, capabilities, and progression tracks.
  `CharacterSpec` and `ProgressionContext` consume the same registry.
- Existing mage field evidence now enters policy selection through the
  `verified-field-caster` data track instead of a direct mage branch. Shared
  creation, tutorial, arena, maintenance, safety, and reporting behavior remains
  available to every registered class.
- Every new starter run records its full non-secret character/objective context.
  Decisions add stable categories and a safety-critical flag; deterministic
  reports summarize those fields alongside progress, balance signals, and
  first-person commentary.
- `matrices/level-10.yaml` defines the first representative live proof: female
  human warlock-target mage Aeloria, male drow ninja-target thief Kestrel, and
  neuter dwarf knight-target warrior Dorrik. The `matrix` CLI advances their
  durable campaigns round-robin and succeeds only when all three reach level
  10. Unit coverage validates orchestration, but live runs remain required.

## Character-Independent Autonomy Cycle 2

- The first live matrix round created all three configured characters with
  generated passwords stored only in Windows Credential Manager. Run 524
  created female human mage Aeloria, completed every tutorial stage, reached
  level 2, practiced magic missile, provisioned food and water, saved, and
  quit at full health and mana.
- Run 525 created male drow thief Kestrel correctly, but Aeloria had just
  depleted the shared tutorial mobiles. Kestrel reached the empty final room
  at level 1, where an unchecked empty target list caused `list index out of
  range`. The matrix isolated the failure and continued instead of hiding it.
- Run 526 created neuter dwarf warrior Dorrik after the area reset, completed
  the same tutorial without character-specific rules, reached level 2, saved,
  and quit successfully. Mage and warrior now have live creation-to-level-2
  matrix proof; thief remains pending a reset-aware retry.
- DD4 `area_update()` documents that Mud School resets every three minutes
  while occupied and on the next eligible update once no player remains. The
  matrix now waits 75 seconds between characters, including after a failed
  entry. An absent final gladiator now produces `look`, `save`, and `quit` with
  an explicit reset-retry reason instead of indexing an empty target list.
- Decision classification now gives explicit commands precedence: movement is
  navigation, `look` is research, and spell casts are combat even when their
  free-form reasons mention another domain. Starter practice selection also
  comes directly from the archetype registry rather than a duplicate class map.

## Character-Independent Autonomy Cycle 3

- Run 527 resumed Kestrel after the shared Mud School reset. The thief defeated
  the restored final gladiator, completed the tutorial, provisioned, practiced,
  and then used bounded arena patrols with recovery at the Temple healer.
- Kestrel saved and quit safely at level 1 with 2,182 XP, only 118 XP short of
  level 2. The run succeeded as a completed policy segment while campaign 4
  correctly remained blocked and checkpointed for continued progression.
- Live `consider` rejected a reboot-fuzzed wolf whose difficulty was outside
  the safe combat band. Decision text now says "outside the safe live-consider
  band" rather than incorrectly assuming every rejection is an under-level
  mobile, and safe segment exits no longer claim that the campaign objective is
  complete.
- Run 528 advanced Aeloria from level 2 to level 3 before exposing a command
  race: a second boar attacked after the first kill but before a queued `sleep`
  reached DD4. The rejected sleep left stale recovery state, so the operator
  interrupted the run safely and recorded it as failed. Rejected sleep now
  clears the unconfirmed posture and recovery locks and resumes combat handling.
- Run 529 validated that repair across repeated sleep, wake, live-consider, and
  combat cycles, gaining 1,244 XP before a safe operator stop at the Temple
  healer. It also showed that the level-2-to-6 policy could cycle arena resets
  until its runtime expired. That policy now checkpoints after at most ten
  kills, matching the established bounded level-6-to-10 arena policy.

## Character-Independent Autonomy Cycle 4

- Run 530 exercised the new ten-kill bound with Aeloria. The mage gained 1,334
  XP, reached level 4, recovered between spellcasting fights, then saved and
  quit from Safety immediately after the tenth confirmed kill.
- Run 531 reconciled Kestrel's live state by replaying the tutorial fights that
  were not retained from the earlier retry. The drow thief applied pre-level
  gear, reached level 2, provisioned, practiced `hide`, saved, and quit at full
  health and mana. This completes live creation-to-level-2 proof for all three
  representative classes.
- Run 532 advanced Dorrik through ten bounded arena kills. The dwarf warrior
  gained 1,385 XP, reached level 3, and checkpointed from Safety at full health.
- All three successful reports contain the configured non-secret character
  identity, decision-category counts, confirmed-kill evidence, progress deltas,
  checkpoint reasons, and deterministic first-person commentary. The matrix
  remains correctly incomplete at mage 4, thief 2, and warrior 3.

## Character-Independent Autonomy Cycle 5

- The second bounded round completed without intervention. Run 533 gained 930
  XP for Aeloria, run 534 gained 1,231 XP for Kestrel, and run 535 gained 1,353
  XP for Dorrik. Each run stopped after exactly ten confirmed arena kills,
  saved, and quit from Safety.
- Aeloria safely handled a second wolf engaging just as the kill cap triggered:
  DD4 rejected the attempted exit, the existing combat-reentry rule finished
  the attacker, and checkpointing waited until combat and recovery completed.
- Kestrel's report records a reboot-fuzzed boar outside the safe live-consider
  band and a suitable wolf selected instead. Repeated same-reboot arena kills
  produced visibly declining progress, providing balance and policy-rotation
  evidence without compromising safety.
- The matrix remains incomplete at mage level 4 with 7,684 XP, thief level 2
  with 3,577 XP, and warrior level 3 with 5,753 XP. Every campaign has a durable
  next-segment checkpoint and no live process remains after the round.

## Character-Independent Autonomy Cycle 6

- Run 536 advanced Aeloria by another 961 XP through ten bounded kills. The
  mage saved and quit from Safety at level 4 with 8,645 XP, 1,405 short of
  level 5. The matrix launcher was stopped during its inter-character delay,
  with no active connection or unfinished run, to add resource-preserving
  body-part cleanup.
- DD4 source defines organic severed heads, hearts, arms, and legs as takeable
  food. `do_eat` rejects food above the fullness threshold, while inorganic
  mobiles convert their body parts to trash. `do_sacrifice` accepts either type
  from the room, but does not search carried inventory.
- Shared post-combat cleanup now tries `get` and `eat` for every observed
  severed part without waiting for hunger. A fullness or inedibility rejection
  triggers `drop` followed by `sacrifice`, preserving pies when possible and
  still clearing unusable objects. Active combat, sleep, death, and health below
  50 percent prevent opportunistic cleanup from outranking safety.
- Run 537 live-validated the consumption path immediately: Kestrel severed a
  boar leg, collected it, and ate it without a hunger signal before ordinary
  corpse cleanup. The thief preserved carried food, gained 1,204 XP across ten
  kills, reached level 3, and saved and quit from Safety at full resources.
- Run 538 supplied the no-op comparison: no severed part appeared, so Dorrik
  performed only ordinary corpse cleanup. The warrior gained 1,176 XP, reached
  level 4 with 103 HP, and saved and quit from Safety after ten kills.

## Character-Independent Autonomy Cycle 7

- Run 539 advanced Aeloria to 9,837 XP, only 213 short of level 5, through
  another bounded arena segment, then saved and quit safely before the matrix
  handoff. The launcher was stopped during its inter-character delay so
  training policy could be audited without interrupting a live character.
- DD4 source revision `0482387` confirms that the Mud School Loremaster teaches
  from level 1 and has 60-percent knowledge in broad combat, defense, stealth,
  magic, psionic, morphing, ranger, and smithing groups. The server's live
  `practice` listing filters skills through the character's satisfied
  prerequisites before the bot sees them.
- Training is now ranked for every supported base class, with separate physical
  and intellectual budgets. Immediate damage, damage gateways, mitigation, and
  sustain outrank non-combat utility; each command records the skill's current
  and target proficiency and its combat rationale.
- The planner uses both already-known and newly learnable skills, never invents
  a skill absent from the current trainer listing, and validates every ranked
  skill against the bundled source prerequisite snapshot. This corrects
  live-observed waste such as choosing `detect invis` over a weak
  `magic missile`, or an unarmed gateway before a warrior's low
  `second attack`.
- Source inspection refined the policy further: spell proficiency changes cast
  success but not damage, second attack fires at `45 + proficiency / 2`,
  enhanced damage adds `proficiency / 2` percent weapon damage, and dodge,
  parry, and shield block use half proficiency as their base chance. At low
  levels, chill touch's `10-20 + level` damage substantially exceeds magic
  missile's `2-5` damage per missile, so evocation now outranks reinforcing the
  starter spell.
- Practices are not ordinary accumulating currency. On level-up, unspent
  physical practices add maximum hit points, unspent intellectual practices add
  maximum mana, and both pools are then replaced by the new level's allotment.
  The planner therefore buys at most one high-value skill of each type per
  level and explicitly reports why it preserves the rest.
- Skills that need unsupported commands or equipment preparation are recorded
  but marked ineligible for autonomous spending. The shared combat controller
  now uses the strongest known damage spell for mages, clerics, and psionics;
  shifter forms, ranged attacks, and smithing preparations remain gated until
  their execution policies are implemented and tested.
- Run 540 live-validated conservation with an exhausted intellectual pool. The
  planner spent nothing, preserved two physical practices, and Aeloria's next
  level raised maximum HP from 81 to 90 before issuing a fresh practice pool.
  She reached level 5, gained 852 XP across ten kills, and checkpointed safely.
- Run 541 presented 2 physical and 3 intellectual practices. The planner bought
  exactly one `evocation magiks` lesson at 24 percent, the Loremaster accepted
  it, and the report explained both the `chill touch` damage unlock and the four
  points preserved for future HP or mana. Aeloria gained another 690 XP over ten
  kills and saved at full health in Safety with no detected failure.
- Run 542 live-validated the thief branch. Kestrel spent one of two intellectual
  practices on `armed combat knowledge`, preserved both physical points and the
  remaining intellectual point, gained another bounded ten kills, and saved
  safely at level 3. An explicit-command precedence fix ensures the report
  classifies `practice armed combat knowledge` as training rather than combat.
- Run 543 validated both intended warrior purchases before exposing stale state:
  Dorrik trained `second attack` and `armed combat knowledge`, preserved one
  physical point, and completed six safe kills. After a wolf died, GMCP reported
  no enemies while a stale text-derived combat target remained; periodic affect
  updates kept the generic watchdog alive. The session was terminated at full
  health in a safe room and recovered as interrupted rather than left hanging.
- Empty GMCP enemy snapshots now authoritatively clear combat state. Source and
  `HELP KICK` confirm that kick is a fighting-position action with an 8-pulse
  wait, learned-percent success, and `level / 2 + random(1, level)` player
  damage. Warriors now use it between automatic rounds, and its prerequisite
  and first lesson become eligible after the higher-value automatic damage
  passives.
- Run 544 live-validated the stale-combat repair: Dorrik completed ten kills,
  gained 894 XP, left the depleted arena, slept through the bounded reset
  window beside the healer, resumed hunting, and checkpointed safely. An empty
  GMCP enemy snapshot ended combat immediately after each kill.
- Source revision `0482387` and `HELP BACKSTAB` show that backstab requires
  `sneak` at 40 percent, `stealth techniques` at 60 percent, thief base at 30
  percent, and a wielded weapon whose damage type is pierce or stab. The generic
  thief plan now trains hide before sneak for races without racial sneak, uses
  the exact prerequisite thresholds, and opens only fresh fights with a
  catalog-verified piercing weapon. A rejected opener falls back to `kill` once.
- Runs 545 and 546 advanced Kestrel from level 3 to level 4 and then to 8,022
  XP. Across twenty safe kills he trained armed combat from 23 through the
  40-percent gateway and second attack from 0 through the 35-percent target,
  while preserving unused practices and checkpointing at full health.
- Run 547 live-validated the repaired thief branch. The listing showed armed
  combat at 41 percent, second attack at 35 percent, racial sneak at 99 percent,
  and stealth techniques at 0 percent. The planner spent its sole intellectual
  point on stealth toward the exact 60-percent backstab prerequisite, preserved
  its physical point, gained 841 XP over ten kills, and checkpointed safely.

## Character-Independent Autonomy Cycle 8

- Practice commands are now outcome-driven. A skill is added to the active
  capability set only after DD4's `I hope my knowledge helps you` response.
  Every source-defined rejection records a structured `training_rejected`
  event, preserves the point, and advances the bounded plan. A prompt without a
  recognized response is treated as unconfirmed instead of leaving the bot
  waiting indefinitely.
- Run reports now list accepted and rejected lessons and turn both outcomes
  into first-person commentary. Run 548 live-validated `training_completed`
  when Aeloria learned `chill touch`; she then gained 653 XP from eight kills
  without falling below 93 percent health.
- Run 548 also exposed a source-map routing bug after arena depletion: room
  3732 is the center and has no upward exit, while every wall section exits up
  to Safety. Arena completion and reset routes now move north from the center
  before climbing, rather than alternating an invalid `up` with `look` until
  the command budget expires.
- Run 549 validated the repaired exit over a complete thief segment. Kestrel
  gained 1,050 XP from ten kills in 130 commands, remained above 91 percent
  health, and checkpointed safely. The trainer showed one physical and zero
  intellectual practices, so the bot preserved the point while waiting for the
  intellectual lesson needed to raise stealth toward backstab's prerequisite.
- Run 550 supplied the warrior comparison: Dorrik gained 949 XP from ten kills
  in 120 commands, remained above 98 percent health, and checkpointed safely.
  Kick was visible but both practice pools were zero, so it was neither falsely
  credited nor issued in combat.

## Character-Independent Autonomy Cycle 9

- Run 551 live-validated the arena-center repair after the failed run 548. The
  mage completed ten kills in 119 commands, gained 566 XP, vacated Mud School
  for the reset window, recovered beside the healer, and moved north from room
  3732 before climbing and checkpointing safely.
- Resumed segments previously began arena combat with an empty in-memory skill
  set. DD4's no-argument `practice` command calls `prac_slist` before trainer or
  posture checks, so the bot now uses it once per authenticated arena session
  to refresh actual known capabilities. A returned prompt closes an incomplete
  audit rather than leaving the session waiting.
- Run 552 proved the refresh order. Aeloria's authoritative listing was parsed
  before the Imp or target decisions, and the first and subsequent combat casts
  used known `chill touch` instead of the weaker fallback `magic missile`. She
  gained 790 XP from ten kills and checkpointed safely with full health.

## Character-Independent Autonomy Cycle 10

- Runs 553 and 554 advanced the contrasting thief and warrior from level 4 to
  level 5. Kestrel gained 720 XP and 13 maximum HP; Dorrik gained 762 XP and 18
  maximum HP. Both completed ten kills, used the pre-level equipment stance,
  and checkpointed safely at full health without inventing unavailable skills.
- Runs 555 and 556 carried Aeloria across the next boundary. The first ten-kill
  segment gained 670 XP and stopped 92 XP short; the bounded follow-up reached
  level 6 after two kills, raised maximum HP from 90 to 100 and maximum mana
  from 245 to 267, and immediately left the arena after satisfying its level
  objective.
- Run 557 live-validated the actual `mud-school-6-10` handoff. Aeloria refreshed
  her known skills before fighting, used `chill touch`, gained 787 XP from ten
  confirmed kills, and finished at 100/100 HP in Safety with no detected
  failure. This is evidence that the level-band selector does more than merely
  advertise the next policy.
- DD4 source revision `0482387`, `HELP KICK`, the skill table, and `do_kick`
  agree that kick is an in-battle attack: it is rejected unless the character
  is already fighting, consumes an 8-pulse skill wait, and on success deals
  `level / 2 + random(1, level)` damage for a player. The bot therefore issues
  it only from the between-round combat decision path, after an automatic
  round has returned a prompt, and only after the live skill listing confirms
  it is known.
- The warrior prerequisite source requires either 20 percent unarmed-combat
  knowledge or 30 percent warrior-base knowledge before kick. Those exact
  gateways remain in the data-driven training plan; kick competes for precious
  practice points only after higher-value passive damage and defense choices.
- Run 558 applied the class-specific thief plan at level 5. Kestrel's live
  listing showed stealth techniques at 23 percent and two practices of each
  type; the Loremaster confirmed one intellectual lesson to 35 percent while
  the bot preserved three points. He gained 856 XP from ten kills, ate severed
  body parts opportunistically, and checkpointed at 99/99 HP. Backstab remained
  gated by its exact 60-percent stealth prerequisite and was never attempted.
- Run 559 applied the contrasting warrior plan. Kick became learnable after
  unarmed-combat knowledge reached 21 percent, but the planner first bought
  confirmed armed-combat and second-attack lessons because they improve passive
  weapon damage more frequently than an 8-pulse active kick. Dorrik preserved
  one physical practice, issued no unlearned `kick` command, gained 954 XP from
  ten kills, and checkpointed at 121/121 HP.

## Character-Independent Autonomy Cycle 11

- Runs 560 through 562 advanced Kestrel another 2,402 XP through three safe,
  bounded arena segments. One confirmed stealth-techniques lesson raised the
  prerequisite group from 35 to 41 percent; later segments observed the
  exhausted intellectual pool and made no unsupported backstab attempt.
- Run 563 crossed the thief boundary after five kills and stopped immediately
  at the level objective. Kestrel reached level 6, maximum HP rose from 99 to
  111, maximum mana from 130 to 138, and maximum movement from 190 to 200; the
  bot recovered, left the arena, saved, and quit from Safety.
- That progression exposed a cross-process conservation defect: the in-memory
  one-lesson-per-type limit reset at every bounded campaign segment. A character
  could therefore spend another practice of the same type before levelling,
  reducing the points converted into maximum HP or mana.
- Campaign execution now reconstructs accepted practice types from successful
  run evidence whose segment began at the current level. Those types are passed
  into the next deterministic training plan and excluded until the level
  changes. This works for existing campaign history without schema migration
  and naturally gives the new level a fresh allowance.
- Run 564 live-validated the repair against the warrior case. Dorrik's listing
  showed one physical practice and learnable kick, but campaign history showed
  that both practice types had already been spent at level 5. The bot issued
  only read-only practice listings, preserved the point, gained 763 XP from ten
  kills, and checkpointed at 121/121 HP with no failure.

## Character-Independent Autonomy Cycle 12

- Runs 565 and 566 added another 1,690 XP across twenty safe warrior kills.
  Both bounded processes reconstructed the prior level-5 physical lesson and
  preserved Dorrik's remaining practice instead of spending it on kick.
- Run 567 crossed the warrior boundary after three kills. Dorrik reached level
  6, maximum HP rose from 121 to 138, maximum mana from 122 to 127, maximum
  movement from 190 to 200, and strength from 22 to 23. The preserved practice
  therefore contributed to the intended level-gain resource pool.
- Run 568 live-validated the shared level-6 policy for the thief. Kestrel raised
  stealth techniques from 41 percent toward backstab's exact 60-percent gate,
  preserved three practices, gained 735 XP from ten kills, and used the temple
  healer during arena reset waits and before the final checkpoint.
- Run 569 supplied the warrior comparison. Dorrik raised armed combat knowledge
  through the 40-percent enhanced-damage and third-attack gateway, raised
  second attack toward 50 percent, and preserved one practice. He gained 720 XP
  from ten kills at full final health, then followed `enter portal`, `down`, and
  `north` from arena Safety to healer room 3054 before saving and quitting.
- Arena completion now outranks ordinary safe-room recovery, so reaching a kill
  or level boundary cannot make the bot sleep inside the arena. Post-tutorial
  recovery also treats Safety as merely safe rather than equivalent to room
  3054: with adequate movement it takes the portal and temple route to the real
  healing room. Level-2 tutorial sequencing and low-movement emergency sleep
  remain unchanged.
- Run 570 completed the level-6 comparison for the mage. Campaign evidence
  prevented duplicate level-6 lessons, Aeloria used confirmed `chill touch`
  only after combat began, and healer-room reset waits restored the mana spent
  on each patrol. Ten kills added 890 XP; she checkpointed in room 3054 at
  100/100 HP, 219/267 mana, and 186/200 movement, with 3,130 XP left to level 7.
- Run 571 preserved Kestrel's three remaining practices and gained 603 XP from
  eight safe kills. It stopped when the live consider sweep found no remaining
  viable target, providing direct evidence that Mud School spawn availability,
  rather than combat risk, is now limiting level-6 throughput.
- Source scoring rejected the denser Miden'nir goblins for level-6 autonomy
  because a source-level-7 lieutenant can fuzz higher and wander through the
  area. Foundry's Uburz ranked as the best non-rejected alternative: source
  level 4, fuzzed range 2-6, estimated 75 peak round damage, and three distinct
  sellable drops.
- Runs 572-574 live-validated that alternative with Dorrik. He killed Uburz for
  106 XP without losing health, replaced a plain cloak with the source-backed
  silver circlet (`APPLY_STR +1`), sold the displaced cloak, piping, and leg
  guards for 57 copper, and finished with nine pies and a filled water skin.
  The complete 162-second hunt-sale-restock cycle is an economic and equipment
  loop; it does not yet outperform arena XP enough to replace that policy.

## Character-Independent Autonomy Cycle 13

- Level 6 now starts with a generic two-target Foundry circuit. The existing
  recall-origin fastwalk reaches room 109; source-backed relative routes visit
  Uburz in room 120 and Ushog in room 112 while avoiding the poison-bearing
  room 122. Every target still passes live presence, crowd, `consider`, and
  health gates, and the circuit recalls safely after two kills or exhaustion.
- Run 575 live-validated the combined route. Uburz was absent, a roaming Olog
  engaged on the connecting path, and Ushog was present. Dorrik killed both for
  208 XP, recovered five equipment drops, recalled, slept at healer room 3054,
  and checkpointed at 138/138 HP in 146 seconds.
- Runs 576 and 577 applied the same policy to Kestrel and Aeloria. The Foundry
  was depleted, so both made clean no-kill returns and finished at full health
  in 76 and 65 seconds. After an empty level-6 field segment, policy selection
  now alternates to the verified ten-kill arena batch instead of immediately
  revisiting the same depleted rooms.
- Run 578 live-validated that adaptive fallback. Aeloria killed ten wild boars
  for 781 XP in 547 seconds, finished at 100/100 HP with 225/267 mana, and
  checkpointed beside the temple healer with 2,349 XP left to level 7.
- DD4's no-argument `practice` command calls `prac_slist` before any trainer or
  posture requirement. Every authenticated field-hunt process now uses that
  read-only listing before travel, restoring learned combat capabilities after
  reconnect so source-correct between-round attacks such as `kick` are never
  forgotten or invented.
- Runs 581 and 582 exposed two escape-cost regressions. The official Foundry
  fastwalk ends in room 109, so the Uburz leg required a second `south`; an
  aggressive endpoint mobile could also arrive after the text prompt but
  before its GMCP enemy record. The bot paid 98 XP in run 581 by fleeing and
  then recalling, and 19 net XP in run 582 after fleeing when a disarm left
  the in-memory weapon keyword unknown.
- Field combat now waits for delayed GMCP assessment before deciding whether a
  lone attacker is safe to finish. If a combat disarm has no remembered weapon
  keyword, the bot uses `get all`, identifies a source-backed wieldable item
  from the refreshed inventory, and rearms it instead of paying an avoidable
  escape penalty. Multiple or out-of-band enemies retain the immediate safety
  withdrawal.
- Runs 583 and 585 validated the corrected room graph and incoming-combat text
  detection. Aeloria reached rooms 120 and 112, used confirmed `chill touch`,
  and gained 413 net XP across four kills. Run 583 exposed a recall race after
  the previously unrecognized source damage verb `injures`; the recognizer now
  covers DD4's complete damage-message ladder before navigation decisions.
- Run 585's remaining flee was an intentional 70-percent-health withdrawal:
  Aeloria entered Ushog at only 80 percent health and the target still had 82
  percent health when the threshold fired. Ushog is now a full-health-only
  second stop, so a damaging first encounter ends the circuit before entering
  his aggressive room.

## Character-Independent Autonomy Cycle 14

- Run 587 live-validated the full-health gate. Aeloria killed an Olog, Uburz,
  and Ushog for 514 XP with no flee or escape penalty, recovered eight items,
  and returned at full health. Runs 590 and 593 added another 493 XP from five
  Foundry kills without a safety withdrawal; she is now 929 XP from level 7.
- Runs 589 and 596 advanced Dorrik by 1,003 XP through ten arena kills and one
  Ushog kill. His live listing still showed one physical practice and learnable
  kick, but the bot preserved it because campaign history had already spent the
  level-6 physical lesson. It issued no unlearned active attack and finished at
  138/138 HP with 2,896 XP left to level 7.
- Runs 592 and 595 advanced Kestrel by 907 XP through ten arena kills and two
  Foundry kills. Backstab remained unavailable behind its exact stealth and
  sneak prerequisites; no unsupported opener was attempted. He finished at
  111/111 HP with 1,901 XP left to level 7.
- Source revision `0482387` confirms the action economics used by the warrior
  plan. `second attack` is automatic each combat round at `45 + proficiency/2`
  percent. `kick` requires an existing fight, consumes its 8-pulse wait, tests
  learned proficiency, and deals `level/2 + random(1, level)` player damage.
  Armed knowledge toward enhanced damage therefore remains ahead of kick, while
  known kick is issued only by the between-round combat decision path.
- Run 597 sold Kestrel's Foundry armour but a level-2 drunk attacked the drow on
  safe-flagged Main Street. The bot recovered at full health and saved safely,
  yet correctly exposed the interruption as a failed utility segment. Safe room
  flags do not guarantee race-neutral travel.
- Noncombat utility runs now wait for GMCP enemy assessment and may defend only
  against one attacker at least three levels lower, in a flagged safe room,
  while at 90 percent health or better and neither hungry nor thirsty. Every
  unknown, multiple, peer-level, unsafe-room, or low-health encounter retains
  flee, recall, healer recovery, save, and quit behavior.
- Run 598 live-validated the repaired Kestrel route. It completed in 44 seconds
  with no combat event or utility abort, retained his sole usable metal-piping
  weapon plus food and water, and saved and quit from room 3019 at 111/111 HP.

## Character-Independent Autonomy Cycle 15

- Run 600 advanced Dorrik by 273 XP through one defensive city kill plus Olog
  and Uburz, with no escape penalty and full final health. Run 599 had already
  sold his prior Foundry drops, leaving eight pies, water, and `3g 13s 34c`.
- Run 601 killed Ushog for 126 XP, but delayed corpse-cleanup output arrived
  after Aeloria sent `recall`. The policy treated that stale same-room prompt as
  the recall result and closed in room 112. Dedicated run 602 immediately
  recovered her to room 3019 at full health and mana.
- Recall commands now remain pending until GMCP reports a room transition.
  Source-defined rejection messages clear the pending state and retain the
  clean failure path. Run 604 live-validated extraction after two Foundry kills:
  Aeloria recalled, recovered, saved, and quit at full health without error.
- Run 604 gained only 85 XP in 133 seconds because repeated reboot-local
  Foundry kills had heavily reduced Aeloria's rewards. Level-6 policy selection
  now totals Olog, Uburz, and Ushog kills for the current character and reboot;
  at eight kills it rotates to the verified arena fallback. Fresh Foundry loops
  remain available after reboots and to other characters below that threshold.
- Run 606 proved the rotation and advanced Aeloria to level 7. Ten arena kills
  added 838 XP; maximum HP rose from 100 to 110, mana from 267 to 293, and
  movement from 200 to 210. She checkpointed by the healer at full health.
- Run 607 advanced Kestrel by 369 XP through Olog, Uburz, and Ushog, with full
  final health and no error. Run 609 added another 266 XP from the same circuit,
  but a level-1 drunk attacked on the Midgaard return after the final hunt-stop
  index had been exhausted. Defensive-kill bookkeeping indexed beyond the stop
  tuple and failed the process; run 610 recovered Kestrel safely to room 3019.
- Post-circuit attackers are now recorded only after a hunt-stop bounds check.
  A focused regression reproduces the completed-circuit city attack, preserves
  its XP record, and leaves the final field-stop state unchanged.

## Character-Independent Autonomy Cycle 16

- Runs 607 and 609 advanced Kestrel by 635 XP through two three-kill Foundry
  circuits. A harmless level-1 city attacker exposed the completed-stop index
  defect in run 609; run 610 recovered him at full health, and the source-safe
  bounds repair was published before progression resumed.
- Kestrel's reboot-local Foundry count then selected the arena automatically.
  An externally short five-minute wrapper interrupted run 611 while he was
  safely asleep beside the healer after gaining 416 XP; the child process was
  terminated explicitly, orphaned records were repaired, and run 612 saved the
  character home. Arena runs now retain their established 15-minute ceiling.
- Runs 613 and 614 added another 1,315 XP across nineteen kills. Run 614 advanced
  Kestrel to level 7, raising maximum HP from 111 to 123, mana from 138 to 145,
  and movement from 200 to 210. He checkpointed beside the healer at full HP.
- Repeated Foundry sales reduced Dorrik's guards and four piping copies below
  every compatible shop's minimum offer. Runs 617-619 showed two maintenance
  loops: an uninterested item remained classified as sellable, and repeated
  duplicate `value piping` commands triggered the progress watchdog.
- An uninterested response from the best compatible shop now collapses every
  remaining plan entry with that keyword and schedules one home donation per
  carried copy. Run 621 live-validated four pipe donations plus one guards
  donation, then saved at full health with only food and water in inventory.
- Dorrik's reboot-local Foundry count, including the earlier run 572 Uburz kill,
  reached the eight-kill rotation threshold. Runs 622 and 623 completed twenty
  safe arena kills for 1,529 XP while preserving his unspent physical practice.
  Run 624 found no eligible respawn and made a clean zero-kill healer checkpoint
  with 918 XP remaining to level 7.
- After a full outside-area reset interval, run 625 gained 849 XP from ten kills
  and left Dorrik 69 XP short. Run 626 completed the boundary after seven kills,
  raising maximum HP from 138 to 157, mana from 127 to 133, and movement from
  200 to 210. He retained two practices and checkpointed beside the healer at
  157/157 HP with no error.
- Aeloria, Kestrel, and Dorrik have therefore all reached level 7 through the
  same data-driven level-band selector, while preserving class-specific skill,
  equipment, practice, commentary, transcript, and safety behavior. No policy
  branch contains a matrix character name.

## Character-Independent Autonomy Cycle 17

- Run 627 exposed an unsafe mismatch in the level-7 Miden'nir policy. The
  broad `goblin` keyword and a long roaming circuit reached a goblin lieutenant;
  two flee penalties and one failed recall cost 163 XP against a 332-XP kill.
- The policy now visits only room 3506, one east of the official Ambush
  fastwalk endpoint, and requires the exact observed `mountain goblin` name
  backed by the area reset. A failed or interrupted recall keeps evacuation
  state sticky and cannot promote a pursuer into the requested hunt target.
- Run 628 live-validated the correction. With no mountain goblin loaded, Aeloria
  returned without combat or XP loss, recovered in the temple healing room,
  and saved and quit from room 3019 at full health and mana.
- DD4's `HELP KICK`, `do_kick`, and warrior prerequisite table agree that kick
  is a practiced in-combat action, not an opener. It consumes the configured
  between-round wait and deals `level/2 + random(1, level)` on success. Passive
  second attack remains the warrior's first damage investment; kick follows
  after its unarmed-knowledge prerequisite and is repeated only during combat.
- Run 629 found no level-7 arena opponent in the viable consider band and
  returned Kestrel without combat or XP loss. Run 630 then disproved a generic
  Miden'nir fallback: the reboot-fuzzed level-8 mountain goblin auto-attacked
  the level-7 thief before consideration, forcing a safe flee at a 58-XP cost.
- A stalled level-7 non-caster now falls back to the already proven Uburz and
  Ushog Foundry circuit with a level-8 objective boundary. Run 631 validated it
  for Kestrel with Olog, Uburz, and Ushog kills worth 307 XP total. His passive
  second attacks fired, two disarms were recovered in combat, and he finished
  at full health with sellable drops.
- Run 632 raised Dorrik's armed knowledge from 39% to 40%, unlocking enhanced
  damage, and raised passive second attack from 43% to 44%. His remaining
  physical practice was preserved by the one-lesson-per-type-per-level rule.
  Run 633 safely found the Foundry depleted after Kestrel's pass and left the
  area at full health so its faster unoccupied reset could begin.
- DD4's `HELP PRACTICE`, `do_practice`, and `advance_level` confirm the practice
  tradeoff. The Loremaster teaches the starter knowledge groups to 60%; lesson
  gain depends on teacher knowledge, current proficiency, and character
  penalties. Unspent physical and intellectual practices do not accumulate:
  they convert 1:1 into hit points and mana respectively at the next level.
- Run 634 returned after the unoccupied reset and let Dorrik kill Uburz for 155
  XP. At 145/157 HP he declined the full-health Ushog stop, recalled, and
  recovered to full health. Runs 635-636 then sold fresh armour and jewellery,
  retained the best worn pieces and usable weapons, and removed rejected
  duplicates without progress loops.
- Run 636 exposed movement recovery sleeping in safe Mage's Bar instead of the
  temple healing room. Ordinary level-above-two and maintenance recovery now
  follows the known Midgaard route to room 3054 whenever at least 10% movement
  remains; field routes retain their separate invisibility-aware handling.
- Runs 637 and 639 rechecked the arena after a long unoccupied interval for
  Kestrel and Dorrik. Both found only below-band opponents and exited without
  XP or damage. The repeated cross-character evidence promotes the level-7
  Foundry circuit to the primary thief/warrior policy; a stalled mage also uses
  it instead of retrying this reboot's aggressive level-8 mountain goblin.
- Run 638 added another 107 XP for Kestrel through Olog and Uburz. Reboot-local
  repetition reduced Olog to 10 XP, while Uburz remained worth 97. At 111/123
  HP Kestrel declined the full-health Ushog stop, recalled, and recovered at
  the healer. Room 3726 is now also on the standard healer route, preventing
  future movement sleeps at the Loremaster.
- Run 640 live-validated the stalled level-7 mage fallback. Aeloria killed
  Olog, Uburz, and Ushog for 303 XP, collected six loot items, recovered from
  70/110 to full health at the temple healer, saved, and quit safely. Run 641
  then exposed recovery interrupting the final step of an otherwise safe shop
  return: the cached direction resumed from the healer instead of Mage's Bar.
  Healthy liquidation routes now complete without a mid-route healer detour;
  critical-health recovery still takes precedence.
- Run 642 recovered Aeloria from Donation Temple, rebuilt the liquidation plan
  from current inventory, completed both safe shop routes, and checkpointed at
  the Mage Laboratory with full health. The two sales completed before run
  641's route failure remained recorded instead of being replayed.
- Run 643 live-validated the promoted Foundry policy for Dorrik with Olog,
  Uburz, and Ushog kills worth 365 XP and eight loot items. His current skill
  listing showed passive second attack at 44% while kick remained learnable at
  0%; the bot never issued the unpractised action and finished at full health.
- Run 644 live-validated uninterrupted safe-shop routing after the recovery
  fix. Dorrik sold three item types through three compatible shops, returned
  to the Mage Laboratory, and finished at full health.
- Run 647 proved the old level-7 circuit was still too narrow. Kestrel killed
  Olog and Oshu, but a level-1 Golgog auto-attacked before consideration; the
  bot incorrectly treated the low level as unsafe, fled for a 58-XP penalty,
  and kept only 38 net XP. A lone attacker below the useful XP band is no
  longer classified as dangerous: once combat has begun, only an over-level
  or crowded encounter triggers that safety evacuation.
- The level-7 Foundry policy now follows source exits through Oshu, Golgog,
  Shargook, Lobuk, Uburz, and Ushog, with exact names, live consideration,
  crowd checks, reserve gates, and a five-kill bound. It never enters room 122,
  whose pit beast has the poison special. The level-6 two-target circuit is
  unchanged.
- Run 648 live-validated every expanded waypoint for Dorrik. Olog, Oshu, and
  Uburz produced 295 XP and seven items; absent Golgog, Shargook, and Lobuk
  were skipped. At 147/157 HP the full-health Ushog gate recalled instead of
  taking the final fight, and Dorrik recovered, saved, and quit at full health.
- Run 650 gained 20 XP but exposed an equipment-state loop after Golgog dropped
  a metal buckler: the drow thief repeatedly tried to wear it even though DD4
  reported that his profession prohibited that wear location. The process was
  terminated with Kestrel alive at full health and the orphaned run and
  campaign records were recovered immediately.
- Profession-rejected wear commands now use the existing generic unusable-item
  path: blacklist the pending keyword, discard the queued stance, and re-audit
  without that item. Run 651 live-validated a single rejected `wear buckler`
  with no retry, then gained 194 XP from Olog, Uburz, and Ushog, recovered and
  rewielded a disarmed weapon, and finished safely at 123/123 HP.

## Character-Independent Autonomy Cycle 18

- Run 652 found the intended level-8 mountain goblin and a wandering level-7
  goblin lieutenant on Aeloria's exact Miden'nir route. She escaped both and
  recovered at the healer, but the two flee penalties cost 116 XP. The stalled
  checkpoint correctly selected the lower-risk Foundry fallback next.
- Run 653 gained Aeloria 188 XP from Olog, Oshu, and Uburz, collected seven
  items, and returned her to the Mage Laboratory at full health and mana.
- DD4 help and `fight.c` now anchor the matrix skill choices: kick is an active
  8-beat between-round attack; second attack is an automatic `45 + skill/2`
  chance; enhanced damage adds `skill/200` of weapon damage; dodge and parry
  use half proficiency, with parry requiring a weapon; and backstab is a
  piercing-weapon opener with triple damage below level 15.
- Field-run training had an accidental mage-only, level-8-to-9 gate. It now
  considers every class's automated combat priorities and both practice types,
  while respecting the campaign ledger's one physical and one intellectual
  lesson per level. This lets thieves progress toward backstab and warriors
  toward enhanced damage without inventing skills absent from the trainer.
- Run 654 confirmed that Dorrik's level-7 lesson ledger remained intact: run
  632 had already raised second attack to 44% and armed knowledge to 40%, so
  the remaining physical point was preserved for level-up HP instead of being
  double-spent. He then gained 307 XP from four Foundry targets, collected 11
  items, and finished at 157/157 HP.
- Run 655 was interrupted on the Midgaard shop route by a wandering level-2
  drunk. Aeloria fled, recalled, recovered, saved, and quit at full health, but
  the 48-XP flee cost correctly failed the noncombat segment. Run 656 rebuilt
  the plan from live inventory, sold the sole worthwhile jerkin, and returned
  safely without replaying stale state.
- Run 657 live-proved the generalized level-7 training gate for Kestrel. The
  Loremaster had no immediately useful physical lesson after his intellectual
  lesson was already spent, so the bot preserved both physical points, then
  gained 179 XP in the Foundry and recovered safely.
- An empty trainer plan now emits a structured `training_deferred` event for
  each useful, unspent practice type. The campaign treats that type as handled
  for the current level, preventing repeated Loremaster detours while retaining
  the point's next-level HP or mana conversion and reconsidering it after the
  level changes.
- Source mobile 3064 is a level-2 Midgaard drunk whose greet program explicitly
  attacks passing players and whose attack is only `1d6`. Run 655 showed that
  merely waiting for automatic rounds let him reduce Aeloria from 108 to 75 HP
  before evacuation. A lone, sufficiently lower-level safe-room attacker now
  receives the class's strongest known combat action while every existing
  health, crowd, food, thirst, room, and level safety gate remains enforced.
- Run 658 exposed maintenance resetting Aeloria's transient stall state and
  selecting Miden'nir again. The exact mountain-goblin stop was empty, so she
  returned safely but spent a full segment for no progress. Level-7 selection
  now uses the expanded Foundry circuit for every class; Miden'nir remains
  recorded evidence rather than the default caster route.
- Run 659 live-validated that cross-class selection for Aeloria. She killed
  Oshu, Golgog, and Uburz for 200 XP, collected six items, honored the Ushog
  health gate, and returned at full health.
- Run 659 also showed a delayed `Skills known:` response arriving after a stale
  prompt had cleared the capability-audit pending flag. The listing contained
  chill touch at 36%, but the bot had ignored it and used magic missile. Skill
  listings are now parsed whenever observed, so asynchronous prompt ordering
  cannot discard known combat capabilities.
- Run 661 exposed the same asynchronous ordering risk in the predeparture
  practice audit: a healer spell and prompt arrived before the requested
  `score`, causing a safe but unnecessary segment failure. Practice-balance
  audits now make at most three bounded attempts when unrelated room output is
  interleaved, rather than failing after the first missing response.
- Run 662 live-validated the bounded retry path. Kestrel parsed the practice
  balance, recorded a structured deferred physical lesson when the Loremaster
  offered no useful option, then gained 300 XP in the Foundry and returned at
  full health.
- A fresh audit of `HELP KICK`, the skill table, `do_kick`, `comm.c`,
  `update.c`, and the pulse macros clarified its exact action economy. Kick is
  legal only while fighting, uses an 8-pulse command wait, and deals
  `level/2 + 1..level`; automatic combat still runs independently every 12
  pulses. The policy therefore treats kick as additive between-round damage,
  never as an opener or a replacement for automatic weapon attacks. Future
  skill automation must record equivalent help and implementation evidence.
- Run 664 live-validated delayed capability capture and the cross-class
  Foundry policy together. Aeloria used confirmed `chill touch` throughout,
  killed Olog, Oshu, Golgog, and Uburz for 339 XP, collected seven items, then
  recalled and recovered to full health before checkpointing safely.
- The run-664 report exposed a summary mismatch: decision analysis classified
  19 combat actions correctly, while the progress counter looked only for the
  word `fight` and reported zero. Combat totals now honor the stored category
  and fall back to the shared decision classifier, covering casts, kicks,
  backstabs, and other combat commands. The regenerated report records all 19.
- Run 665 sold Aeloria's source-classified loot through the compatible safe
  shops, reduced carried weight from 140 to 101, and returned to the Mage
  Laboratory without combat or route failures.
- Run 666 safely liquidated Kestrel's previously recognized Foundry overflow.
  Run 667 then killed Olog, Oshu, Uburz, and Ushog for 377 XP, recovered and
  rewielded a disarmed weapon during the final fight, and returned at full
  health with 186 movement.
- Run 668 exposed a campaign-layer blind spot: Kestrel carried 113/115 pounds
  of source-known `piping`, `jerkin`, `cap`, `circlet`, and `buckler`, but the
  quick selector recognized only a small generic noun list and spent an empty
  Foundry circuit instead of liquidating. Campaign selection now loads the
  same source gear catalog as execution and uses source-backed item keywords
  for unfamiliar, unprotected equipment.
- Run 669 live-validated the repaired handoff by selecting `sell-loot` and
  valuing `piping`. A level-2 drunk interrupted the return; after GMCP reported
  two byte-identical drunk records, the transcript showed a vagabond joining
  the fight. The records represented two real attackers even though the server
  duplicated the current target's details. The crowd gate therefore fled and
  recalled correctly. Kestrel finished unharmed at the Mage Laboratory, but
  the flee and partial-damage awards produced a net 49-XP loss. Enemy records
  must retain multiplicity; identical entries are not safe to deduplicate.
- The matrix training audit now pairs each automated mage, thief, and warrior
  choice with current help, prerequisite, trainer, and implementation source
  references. It records the Loremaster's 60% group ceiling and
  attribute-penalized practice formula, and corrects thief armed-combat
  training from an unnecessary 40% target to the exact 20% second-attack
  prerequisite. Completed training events retain the evidence references that
  justified spending the practice point.
- Run 670 retried Kestrel's liquidation without weakening crowd safety. It
  sold the circlet, confirmed that the compatible keepers were uninterested in
  the piping, jerkin, and cap, donated those redundant pieces, and returned to
  the Mage's Laboratory at full health. Carry weight fell from 113/115 to
  85/115 with no combat or XP loss.
- Run 969 live-validated campaign-level capacity relief. Source-backed
  classification selected only Aeloria's plain carried buckler and velvet
  cape for the Midgaard vault, reducing carry weight from 110/115 to 100/115
  while preserving provisions and protected gear. The run exposed standalone
  vault maintenance falling through to the starter completion path; the
  dedicated mode now always saves and quits at healer room 3054.
- Runs 971-976 advanced Aeloria by 268 XP through two Circus kills while
  safely rotating through empty Circus, gnome, and guard circuits. Automatic
  junk cleanup sacrificed transient keys before they could consume the newly
  recovered carrying capacity.
- Runs 977-982 advanced Kestrel by 233 XP through one Circus kill. Runs
  983-990 found every registered level-eight Circus, Moria, and gnome segment
  empty for Dorrik, establishing spawn availability as the immediate
  throughput limit rather than class-specific combat safety.
- Run 990 showed that Dwarven Day Care's mini-maze shuffles direction labels
  relative to the static area-file exits. Field stops can now follow GMCP exit
  destinations by source VNUM, preserving deterministic goals while adapting
  to the live maze.
- Run 991 followed the shuffled route `east, north, west, south`, found exactly
  one source-level-8 armed guard in room 6624, and recorded a perfect-match
  consider result without combat. Run 992 then killed that unarmed,
  special-free guard for 728 XP and returned Dorrik to healer room 3054 at
  full health and movement. The one-kill Day Care guard fallback is now part
  of the level-eight martial rotation.
- Run 993 independently followed Kestrel's different live maze sequence
  `east, west, south, south` and returned safely when the guard had not yet
  reset. DD4 `area_update` increments area age on randomized 30-90 second
  pulses and resets unoccupied areas once their age reaches eight, so the
  controller must rotate elsewhere rather than assume a fixed five-minute
  respawn.
- Run 994 found a reset guard with level-seven mage Aeloria and recorded a
  perfect-match consider result while she was slightly healthier at 110/110
  HP. Run 995 then killed the same source-vetted guard for 410 XP with four
  chill touches; Aeloria never fell below 104 HP and recovered to full health,
  mana, and movement at healer room 3054. The fallback is therefore verified
  for both field-caster and field-martial level bands.
- Run 996 completed the cross-class proof after the next unoccupied area
  reset. Level-eight thief Kestrel killed the guard for 492 XP, never fell
  below 110/135 HP, and recovered to full health, mana, and movement at the
  healer. Mage, thief, and warrior now share the same data-driven route,
  consideration, combat, and recovery policy without character-name branches.
- Runs 997-1004 rotated Aeloria and Kestrel through fully searched but depleted
  field circuits without unsafe target substitution. Run 1005 then found the
  reset Day Care guard, gained Kestrel 475 structured XP, and returned him to
  healer room 3054 at full resources.
- Run 1006 exposed a two-room resupply cycle after a duplicate queued
  `eat pie` left stale food-unavailable state even though Kestrel successfully
  bought two replacement pies. The process was terminated, the orphaned run
  was marked failed, and run 1007 returned Kestrel safely to the healer. A
  shop-local consumption rule now trusts a newly visible pie or water skin,
  and a bounded route-cycle watchdog forces a direct healer return if
  alternating navigation repeats.
- Run 1008 moved spare Kestrel equipment to the vault. Runs 1009 and 1014
  reached Dragon Cult reception room 9850 safely, but the non-sentinel fanatic
  had wandered away both times; run 1014 instead found a wandering Beastly
  Fido beside the receptionist. The Cult research route is therefore retired
  from autonomous progression rather than wasting repeated segments on an
  unreliable target.
- Runs 1010-1013 resumed productive level-eight rotation. Kestrel gained 78 XP
  from a live-considered Circus Illusionist and 314 XP from the reset Day Care
  guard, never fell below 118/135 HP, and finished at healer room 3054 with
  full health, mana, and movement. He now has 28,339 XP and needs 3,361 for
  level nine.
- Runs 1015-1018 safely searched Aeloria's depleted Gnome, guard, and Day Care
  fallbacks but produced no XP. They exposed an unreachable selector branch:
  after all established circuits recorded zero XP, Day Care returned to Gnome
  instead of rechecking Circus after the elapsed reset window. The depleted
  caster fallback now rotates from Day Care to Circus while retaining the
  ordinary Day Care-to-Gnome transition when established circuits remain
  productive.
- Runs 1019-1022 live-validated recovery from the campaign's ten-segment stall
  guard. Checkpoints now carry an explicit autonomy-policy revision, which
  resets stale consecutive-stall history once when the policy graph changes
  but preserves the guard for unchanged code. Aeloria refreshed flight in run
  1021 and run 1022 selected Circus directly after the depleted Day Care
  fallback, proving the previously unreachable transition; the searched
  Circus targets were absent, so no unsafe substitute was attacked.
- Runs 1023-1026 rotated Dorrik through depleted Circus, Moria, and Gnome
  circuits before the reset Day Care guard appeared. He killed it for 395 XP,
  remained above 163/177 HP, and recovered to full resources at healer room
  3054. Dorrik now has 27,370 XP and needs 4,330 for level nine.
- Run 1027 safely rejected reversing the official Fleshmonger route because it
  contains `open east`; the research dispatcher now explicitly recalls from
  the foyer. Run 1028 verified that route and exposed the missing mobile verb
  `greets`, which is now parsed with regression coverage. Run 1029 then
  considered the lone patrolling guard and received the source `diff 2-5`
  “Do you feel lucky, punk?” result while Dorrik was only slightly healthier.
  The armed, armored target is retired from level-eight automation and retained
  as level-nine research evidence.
- Runs 1030-1031 rotated Aeloria from an empty Gnome guard check to a reset
  Day Care guard. The source-level-eight guard fuzzed below Aeloria's useful
  level-seven XP band, so the live-consider gate rejected combat and returned
  her safely to healer room 3054.
- Run 1032 found the reset Circus Bearded Lady as a perfect match. Aeloria
  killed her for 185 XP while remaining above 100/110 HP, sacrificed the
  corpse for one silver, and finished with 23,098 XP and 1,752 to level eight.
  Delayed loot responses caused duplicate invisibility casts before the next
  stop; the policy now waits for a pending cast result and retries only after
  a confirmed recitation failure.
- Run 1033 used invisibility to reach the aggressive, isolated Gnome small
  troll without forced combat. Aeloria recorded a perfect-match consider
  result at full resources, recalled untouched, and established the target as
  a viable caster-only fallback.
- Run 1034 exposed a route-cycle watchdog that incorrectly counted five
  legitimate combat spells as stalled navigation. Aeloria fled safely,
  retained a net 12 XP from damage, recovered fully at healer room 3054, and
  quit. Route-cycle detection is now restricted to movement commands.
- Run 1035 killed the small troll for 524 XP while Aeloria remained above
  89/110 HP. She collected the severed leg, recalled, recovered fully at the
  healer, and finished with 23,634 XP and 1,216 to level eight. The verified
  `gnome-small-troll-caster-7-8` campaign policy requires invisibility, full
  health, an isolated exact target, live consideration, and one kill.
- Runs 1036-1040 rotated Aeloria through the Circus, Day Care, and Gnome
  fallbacks. Two productive Circus trips killed the Bearded Lady and
  Illusionist for 530 combined XP; the other routes safely rejected a
  below-band guard or recorded absent targets.
- Runs 1041-1044 validated registered-policy dispatch and corrected the Circus
  circuit. The Ivan route now reaches room 4413 by west, west, south; his full
  visible name is parsed, and only source-vetted level-zero Beastly Fido is an
  allowed bystander. An animal keeper or Bobby's mother still blocks combat.
  Three Circus kills advanced Aeloria another 580 XP.
- Runs 1045-1048 searched depleted Day Care, Gnome, Moria, and Dragon Cult
  resets without unsafe substitution. The Cult fanatic remained absent,
  reinforcing that route's retirement from normal autonomous progression.
- Run 1049 used invisibility and the exact crowd and consider gates to isolate
  the Ambush war dog. Aeloria killed it with chill touch for 267 total XP,
  reached level eight at 102/120 HP, equipped its damroll collar for combat,
  recalled, switched to recovery gear, and finished fully restored at healer
  room 3054. The verified `ambush-war-dog-caster-7-8` fallback is now part of
  policy revision 7 after the established level-seven caster circuits and
  small-troll fallback are depleted.
- Runs 1050-1053 resumed Kestrel's checkpointed level-eight rotation. A short
  `Ivan` combat name was initially mistaken for an extra attacker; the safe
  flee cost a net 60 XP, and a proper-name prefix regression now preserves
  the full `Ivan the Strongman` room identity. Moria and Gnome were depleted,
  then the reset Day Care guard yielded 438 XP. Kestrel finished with 28,839
  XP and 2,861 to level nine.
- Runs 1054-1055 exposed and fixed the related flee alias. Ivan fled east, but
  case-folding prevented the short name from matching the full room target,
  so the watchdog safely recalled Dorrik after repeated attack attempts. The
  parser now preserves case for proper-name matching; the retry killed the
  Illusionist for 87 XP and returned safely after Ivan had wandered away.
- Runs 1056-1059 continued the independent martial rotations. Moria and Gnome
  remained depleted, while Dorrik solved a different live Day Care maze and
  killed its guard for 342 XP. Dorrik now has 27,961 XP and needs 3,739 for
  level nine. Kestrel's later Circus recheck retained both crowd gates and
  returned safely when Ivan was absent.
- Run 1060 found a reset Bearded Lady and advanced Dorrik another 124 XP;
  the Illusionist was crowded and Ivan was absent, so the remaining stops were
  skipped without forcing combat.
- Runs 1061-1064 expanded the level-eight martial rotation beyond the
  reset-limited Moria, Gnome, Day Care, and Circus circuits. Moria was empty,
  the Gnome hut and mess hall were empty, and four gateway guards were rejected
  as crowded. Dorrik then killed the isolated Day Care guard for 338 XP before
  entering the newly verified three-target Ambush exterior circuit.
- Run 1064 passed perfect-match checks and killed the wounded goblin and war
  dog for 538 combined XP. Dorrik never fell below 152/177 HP, saw but did not
  engage the wandering dark horseman, collected varied saleable armour and a
  damroll collar, and recovered fully at healer room 3054. The final visible
  looter uses the text `A goblin is here, looting the dead`; that transcript
  now has a parser alias and regression coverage so the exact `goblin looter`
  gate can assess it on the next pass. Dorrik has 28,961 XP and needs 2,739
  for level nine.
- Runs 1065-1068 applied the expanded rotation independently to thief Kestrel.
  Moria was empty and Gnome's only present target was the rejected four-guard
  gateway group. Kestrel solved another shuffled Day Care maze and killed its
  guard for 316 XP, then reached Ambush and killed the perfect-match wounded
  goblin for 266 XP without losing health. He recovered and rearmed after two
  disarms, then recalled because his low Drow carry-weight margin could not
  safely accept another target's drops. Kestrel has 29,421 XP and needs 2,279
  for level nine.
- Run 1068 also exposed a boundedness gap: passive thief combat could continue
  for 106 seconds while neither side posed immediate danger. Field fights now
  have a 150-second hard cap; elapsed fights flee, audit the post-flee room,
  recall, and recover at healer room 3054 instead of remaining indefinitely in
  a low-damage matchup.
- Runs 1069-1072 exercised recovery from the Ambush loot pass. Dorrik sold
  four different hard-leather armour pieces for 127 copper-equivalent coins,
  preserving the varied-item money-loop strategy, then killed a reset Bearded
  Lady for 167 XP. Kestrel's Circus and Moria checks found no isolated target.
- Runs 1073-1076 completed another Dorrik rotation. Moria remained empty and
  Gnome retained four crowded gateway guards, while Day Care reset and yielded
  a 253 XP guard kill at a cost of only four hit points. On the Ambush approach,
  a mountain goblin attacked beside the inn while a dark horseman was present.
  The lone-attacker GMCP gate accepted it; Dorrik killed it for 185 XP without
  taking damage, ate its severed leg to clear hunger, sacrificed the corpse,
  and returned safely when the horseman did not join. Dorrik has 29,566 XP and
  needs 2,134 for level nine.
- Run 1079 completed the full three-target Ambush sweep for thief Kestrel:
  wounded goblin, war dog, and goblin looter yielded 882 XP while he remained
  above 119/135 HP and recovered every disarm. The looter's activity-text alias
  worked live, proving the policy is independent of GMCP display wording.
- Runs 1081-1084 rotated through depleted Circus, Moria, and Gnome circuits.
  Day Care combat then proved the hard field-duration withdrawal and safe
  healer recovery path. The source catalog also exposed four prototypes named
  `a wooden spear`; run 1085 safely lodged Kestrel's ambiguous heavy spear in
  the Midgaard vault, reducing carried weight from 90/90 to 78/90.
- Runs 1086-1091 showed why offensive throughput belongs in policy evidence.
  Kestrel could not outpace the wounded goblin's regeneration, while a blessed
  Day Care attempt reduced its guard to 1/105 HP before the old 120-second cap
  and still netted 100 damage XP after fleeing. The cap is now 150 seconds.
  A repeated combat line from one adopted wandering attacker could also race
  GMCP adoption and look like a second attacker; same-target identity is now
  retained while genuinely different joiners still force immediate withdrawal.
- Runs 1092-1095 advanced Kestrel by 534 XP through an Illusionist and a
  reboot-fuzzed Day Care guard. The 150-second cap completed the latter kill
  after the old ceiling had repeatedly withdrawn with the guard nearly dead.
- Run 1096 exposed two related event-order races. A lone safe-band attacker
  could block a movement command before the route failure check reached the
  existing adoption gate, and post-flee recall could beat delayed enemy GMCP
  by a fraction of a second. Confirmed combat now takes precedence over the
  unchanged-room check, and the post-flee `look` holds a 0.75-second GMCP grace
  window before recall.
- Runs 1100-1101 live-validated both the longer cap and movement interception
  behavior. Kestrel killed a reboot-fuzzed 144-HP Day Care guard for 453 XP at
  132/135 HP, then adopted a level-eight mountain goblin that blocked Ambush
  travel, killed it for 296 XP without damage, and continued the remaining
  circuit before recalling. He finished safely at healer room 3054 with 263 XP
  remaining to level nine.
- Runs 1102-1105 finished Kestrel's level-eight campaign. The Circus yielded
  214 XP from the Bearded Lady and Illusionist, Moria and Gnome were empty,
  and the isolated Day Care guard yielded the final 307 XP. Kestrel reached
  level nine with 9 additional HP, 8 mana, 10 movement, two physical
  practices, and two intellectual practices, then recovered safely at healer
  room 3054.
- Level-nine martial selection now has objective-level-ten Circus, Moria,
  Gnome, Day Care, and Ambush policy identities instead of falling through to
  the prohibited Mud School fallback. Run 1107 live-validated the handoff:
  Kestrel rejected a crowded Circus stop, skipped the Illusionist after the
  `no match for you` consider result, found Ivan absent, and returned to healer
  room 3054 at 144/144 HP, 159/159 mana, and 230/230 movement.
- Runs 1108-1112 advanced Dorrik through the same character-independent
  martial rotation. Circus yielded 85 XP, Moria and Gnome were depleted, Day
  Care yielded 409 XP, and two consecutive useful-band Ambush goblins yielded
  507 XP. Dorrik accepted the second wandering attacker instead of ending the
  trip after one kill, stayed at or above 160/177 HP, and recovered safely.
- Run 1113 bought and verified a light blue flight potion for the reboot-local
  price of 534 copper. Runs 1114-1118 then produced 159 XP at Circus, 333 XP
  at Day Care, and 335 XP from an Ambush goblin lieutenant while skipping
  depleted or unsuitable stops. Flight or levitation now lowers a field
  circuit's healer departure reserve from 90% to 40%; the non-flying reserve
  remains unchanged.
- Runs 1119-1122 completed Dorrik's level-eight campaign. Empty Circus, Moria,
  and Gnome stops rotated without unsafe substitution; the next perfect-match
  Day Care guard yielded 328 XP. Dorrik reached level nine with 20 additional
  HP, 4 mana, 10 movement, two physical practices, and one intellectual
  practice, then finished fully restored at healer room 3054.
- Runs 1123-1127 began Dorrik's objective-level-ten rotation. The trainer plan
  spent one physical practice on Enhanced Damage and one intellectual practice
  on Defense Knowledge toward Dodge's exact 40% prerequisite. Day Care then
  yielded 192 XP at level nine while depleted Circus, Moria, and Gnome stops
  rotated without substitution.
- Run 1123 also exposed a text/GMCP ordering race at the Ambush bridge: the
  visible goblin lieutenant attacked before named enemy GMCP arrived, causing
  an unnecessarily cautious flee. A newly named field attacker now receives
  one decision cycle for structured level assessment; useful-band GMCP adopts
  it, while a second cycle without assessment still withdraws.
- Autonomous field thresholds are now tuned approximately 30% more
  aggressively. Bounded combat lasts 195 seconds, ordinary withdrawal occurs
  at 40% health, a lower-level half-dead opponent can be finished down to 30%,
  circuits continue at 55% health with 20% mana and 15% movement, and
  source-vetted high-risk openings require 85% rather than perfect health.
  Unknown high-level enemies, unsafe crowds, disabling affects, death traps,
  and unsupplied hunger or thirst remain hard stops.
- The 2026-07-26 live progression pass increased aggression by another 25%.
  Bounded combat now lasts 240 seconds, ordinary withdrawal occurs at 30%
  health, a lower-level half-dead opponent can be finished down to 20%,
  circuits continue at 45% health with 15% mana and 10% movement, and
  field-ready or high-risk openings require 75% health and 30% mana.
- Runs 1128-1129 live-validated that revision. Dorrik bought and confirmed
  flight at the current 94-copper price, then completed all three Ambush
  targets in one trip for 747 XP. She continued productively to 129/197 HP,
  stayed above the 40% withdrawal boundary, sacrificed uncarryable remains,
  and recovered safely at healer room 3054. Dorrik now has 32,639 XP and needs
  7,061 to level ten; at 391/400 carried weight, varied-armour liquidation is
  the next required work unit before another hunt.
- Runs 1188-1189 replaced narrow "empty area" probes with full four-stop
  Circus and Moria circuits. Circus found four performers or their crowded
  rooms and pursued a fleeing Ivan once; Moria gained 412 XP and returned
  Dorrik safely with 965 XP remaining. Source-proven or GMCP-confirmed
  below-band bystanders now do not block an appropriate target, and below-band
  combat joiners no longer force a flee. Unknown and useful-band joiners retain
  the normal crowd gate, and trivial mobs are never deliberately selected for
  XP.
- Run 1200 supplied the first concrete false-crowd regression: source-level-zero
  Beastly Fido was the Illusionist's only bystander, but the older name-only
  crowd gate skipped the performer. Fido is now registered as a trivial
  bystander for that stop, so the useful target receives live `consider`
  without weakening the gate for a vagabond or unknown mobile.
- The ticketed Big Top extension treats its ticket as a reusable key rather
  than consumable travel cost. Circus runs claim it from the Midgaard vault,
  buy it only when the claim leaves inventory without one, and lodge it again
  after healer recovery but before logout, preventing DD4's logout key cleanup
  from destroying it.
- Run 1206 bought the reboot-priced ticket, unlocked the Big Top, ignored only
  the source-level-one audience around the Ringmaster, and killed the
  useful-band target for 510 XP. Dorrik reached level ten with constitution
  trained and gained 20 HP, 14 mana, and 10 movement. A post-return routing
  loop prevented automatic lodging, so run 1207 immediately used the proven
  standalone vault path to preserve the ticket, fully recover, save, and quit
  at healer room 3054. The post-return vault now owns its route once started.
- `HELP TEACHER CLUE` marks level ten as the transition from Mud School to
  Midgaard class masters. Source revision `0482387` locates all nine base-class
  trainers: mage 3019, cleric 3002, thief 3029, warrior 3023, psionic 3150,
  brawler 3218, shifter 3221, ranger 3048, and smithy 3050. Campaign policy
  revision 15 registers each outbound route, trainer keyword, and reverse
  healer route so level-ten training is no longer a thief-only exception.
- Live run 1212 captured the full `TEACHER CLUES` response, followed the new
  warrior route to room 3023, confirmed Dorrik's guildmaster, and recorded two
  physical and one intellectual practices remaining. Dorrik then walked back
  to healer room 3054 and saved and quit at full health and mana.
- Runs 1213-1216 resumed Kestrel's level-nine campaign under revision 15.
  Two Ambush trips produced 403 XP and 462 XP, and the Day Care armed guard
  produced 219 XP, leaving 6,127 XP to level ten. The fourth segment sold the
  recovered bloody spear for 26 reboot-local copper, reduced carried weight
  from 84/90 to 72/90, and saved and quit safely in healer room 3054.
- Runs 1217-1225 exposed and repaired a false rearm success. The old parser
  treated the empty `eq all` line `[weapon] -` as an occupied weapon merely
  because the slot label was present, so two bounded fights ran barehanded.
  Policy revision 16 parses the occupied value, overrides stale persisted
  weapon state, and requires a verified item in the slot. Run 1225 also
  live-validated the generic insufficient-funds recovery: Kestrel borrowed 300
  copper from Dragonhoard Bank, bought the reboot-priced 156-copper dagger,
  wielded it, verified `[weapon] a dagger`, and saved and quit safely at healer
  room 3054 with 4,871 XP remaining to level ten.
- Run 1226 then killed a level-eight war dog for 295 XP with the verified
  dagger and collected its 20-pound collar. The collar displaced a protected
  silver circlet into inventory, leaving only two pounds free; run 1227 showed
  that food restocking could not buy even one pie. Policy revision 17 now
  treats protected carried stat gear as vaultable capacity relief, preserving
  it for later stance use while making room before essential restocking.

## Character-Independent Autonomy Cycle 19 - 2026-08-12

- The project audit separated the product goal from the evidence ledger. The
  level-10 mage/thief/warrior matrix remains proven, while the level-100 hero
  command is correctly described as resumable and safe-stopping rather than
  complete. A full audit is recorded in
  `docs/PROGRESS_AUDIT_2026-08-12.md`.
- A legacy source-ranked kill ledger was missing source mobile VNUMs for older
  segments. Latest XP now inherits the selected candidate VNUM only when the
  segment has an unambiguous selected source candidate, allowing meaningful
  rewards to carry across a character level boundary.
- The selector now evaluates productive same-reboot repeats when its first
  choice is research-only. A regression test prevents a capacity or other
  research probe from hiding a safe repeat route.
- Kestrel's live campaign validated the repair at level 24: the Dwarven Home
  host (mobile 20507, room 20510) yielded 1,006 XP and returned to healer room
  3054 at full HP and mana. The campaign checkpoint is 13571.
- The Discord streamer was audited after a missing user message report. Its
  configuration already included `USER`; the source log was missing the user
  record. Appending the record with `tools/conversation_log.py` produced both
  `Publishing USER record` and `Delivered USER record`, with an empty queue and
  current source offset. Future turns must append user steering as strictly as
  Codex commentary and final responses.
- The route-aware Nobleman probe was live-tested with Dorrik (run 5054):
  source mobile 3506, the wandering goblin lieutenant, interrupted the
  Miden'nir approach and caused a safe withdrawal with a 116-XP loss. The
  route now performs an early `where goblin lieutenant` check and names the
  goblin lieutenant, dark horseman, and wyvern as hard hazards. The reboot-
  scoped result remains deferred rather than retried blindly.
- Source-ranked routing now excludes source-proven noncombat specials such as
  `spec_fido` from hard route-crowd rejection. The full suite is 2,485 tests;
  Dorrik subsequently earned 584 XP from the Shire receptionist and 519 XP
  from two Fleshmonger targets, returning safely after both segments.

## Character-Independent Autonomy Cycle 20 - 2026-08-12

- Reconnect repair is now event-specific. Only an explicit
  `research_policy_retried` checkpoint can restore a cleared research-policy
  marker; metadata-repair, policy-rotation, and segment-complete snapshots are
  derived state and cannot resurrect stale clear decisions. A regression test
  covers the former reconnect oscillation.
- When a character still requires sanctuary recovery but that policy is on a
  reboot-scoped cooldown, the campaign now reports the protection wait before
  generic crowd handling. Aeloria's level-13 campaign therefore checkpoints as
  ready at healer room 3054 instead of looping on a false Midgaard crowd.
- Fresh bounded continuation kept the frontier productive without manual target
  steering. Dorrik reached 62,672 XP at level 12 after a Shire receptionist
  kill and two Fleshmonger guard circuits; Kestrel reached 359,301 XP at level
  24 after an Old Treant kill and two Dwarven Home host kills. Both returned to
  healer room 3054 with recovery complete.
- The offline suite now passes 2,487 tests. The source checkout was refreshed
  and was already at the current upstream revision. The HERO objective remains
  active: the next work is executable, class-aware policy coverage through the
  level-30 subclass transition and then the higher level bands, followed by a
  fresh uninterrupted creation-to-HERO acceptance run.
taking damage or losing XP. Run 9071 rejected the live receptionist after
`consider`; an aggressive wandering drunk attacked during transit and was
finished defensively for 10 incidental XP, with no objective target claimed.
The return remained safe. The current level-18 frontier is presently governed by
