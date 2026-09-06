# Autonomy Reassessment: 2026-09-06

## Objective

Keep the master goal: one parameterized command creates or resumes a legal
character and autonomously reaches the requested level, ultimately HERO 100.
Names select credentials and history only. Sex is cosmetic. Reuse the same
decision engine behind direct Telnet and Mudlet; VM visibility is a separate
integration test. No character has yet proved creation-to-HERO.

## Evidence

### Latest Live Finding

The Astra re-audit continued Kestrel's level-24 Drow Thief campaign. Run 12360
then exercised the newly wired dynamic frontier: it selected the source-ranked
Kerofk gravedigger route, reached Ambush, and returned safely at the controlled
120-second field boundary with no XP change or objective kill. Runs
12355 and 12359 acquired source-verified food at the live Haon endpoint. Run 12356
reached the source-identified Old Treant but live `consider` classified it as
below the useful XP band, so it stopped without combat. Run 12358 reached the
Solace Secretary: live `consider` accepted the target, but the target's GMCP
maximum was 523 HP while the thief's audited recurring action budget was 300
damage. The bounded run recalled at a 385-XP loss before a kill; run 12359 then
returned Kestrel to checkpoint 37978 at 333,918 XP in healer room 3054. Run
12361 and 12362 subsequently refreshed Kestrel's source-verified food reserve
and movement, returning him to checkpoint 37982 with unchanged level and XP.
Run 12363 then admitted the gravedigger fallback, but the route crossed source
mobile 18401, the aggressive rolling rock. Its ordinary DD4 combat loop
disarmed Kestrel before he recalled, costing 385 XP without an objective kill.
Kestrel is safely back in healer room 3054 at checkpoint 37990 and 333,533 XP
after a bounded resume selected the unavailable level-24 frontier; the fallback
marker is terminal for this reboot. These are failure and
maintenance evidence, not level-25, subclass, or HERO proof.

Aeloria's run 12364 completed the bounded sanctuary-recovery segment without
XP change after two failed current-reboot resource attempts. The following
resume performed startup repair, recognized the terminal cooldown, and
persisted checkpoint 37989 in healer room 3054 without opening another field
segment. Run 12365 then selected the newly admitted source-ranked Arachnos
guardian route: Aeloria cast `summon familiar`, grouped the level-15 pony,
ordered it onto The guardian, withdrew it near target finish so the player
retained XP credit, and earned 633 XP. The segment reached its controlled
120-second cap during post-kill cleanup and reconciled safely at checkpoint
37994, level 18, 159,938 XP, in healer room 3054. This is fresh continuation
evidence, not level-19, subclass, or HERO proof.

The repair closes the unprotected HP-fuzz exception after any current-level
reboot loss and adds a live budget gate that withdraws when a fuzzy target's
GMCP maximum HP exceeds its audited source action budget. The selector still
uses the source nominal level only to avoid a false static below-band deadlock;
live `consider` remains authoritative on the loaded mobile. Fresh post-reboot
live validation is required before treating either repair as progression
evidence. The live fallback failure adds a route-safety lesson: source
`ACT_AGGRESSIVE` is dangerous even when a mobile has no `spec_*` procedure,
because ordinary `fight.c` combat can still disarm a player.

The source-ranked selector now also closes a planning/execution mismatch: an
ordinary candidate whose source HP ceiling or audited combat path requires
sanctuary is not dispatched when the checkpoint has no executable sanctuary
reserve. This prevents spending a bounded segment travelling to a target that
the field executor must reject before combat. Explicit bounded-peak retries,
sanctuary-resource specials, and separately audited protection fallbacks remain
eligible through their own gates. The regression is covered by the complete
offline suite; this is a decision-quality repair, not progression proof.

The Astra familiar slice closes the mage planner/executor mismatch for a narrow
source-backed case. A Mage or Witch may use `summon familiar` only when live
practice observed the spell, the target is plain and unarmed, every reachable
target room is outdoors and non-underwater, and the combined player-plus-pony
damage budget fits the source HP ceiling and mana reserve. The field stop
persists `require_familiar`; the starter summons, groups, and orders the pony,
withdraws it near 45% target health to preserve player XP, and flees if the
familiar is lost early. Run 12365 is the first fresh live validation of this
new admission and remains bounded continuation evidence.

The latest saved states are Praelarran, warrior, level 20, Aeloria, mage,
level 18, and Kestrel, thief, level 24. Serevian remains a stored thief
campaign at level 11. Work should follow these actual frontiers rather than
the static HERO template count.

Policy revision 192 changes the selection order at the first post-tutorial
frontier. From level 10 onward, an ordinary fresh named research probe is a
fallback behind an executable generic source-ranked candidate. If source
ranking finds no safe current-band target, the named probe still runs, so
research coverage is retained. Dedicated resource, class/shared evidence,
quest, trainer, subclass, equipment, funding, flight, and recovery transitions
remain ahead of both choices. The existing level-21 handoff still covers later
unregistered bands. Every generic candidate continues to require exact source
identity, live `consider`, crowd and route checks, damage-window admission,
resources, and healer return.

The read-only DD4 source mirror is refreshed to revision
`6b6624fab18a8367aaaa4f4883e12f749704e7f6`. The current source applies
resistance categories to ordinary weapon attacks and suppresses immunity-
blocked trip/disarm attempts. The planner records this as source context, but
still requires live target evidence before relying on resistance in a fight.

The Astra pass also corrected a static safety gap: `create_mobile` multiplies
the area-file HP roll by the prototype rank from `mob.c`. Area parsing now
retains that rank, candidate HP bounds apply the source multiplier, checkpoint
records preserve it, and `show-hunt-candidates` reports it. This changes source
fidelity only; it does not turn a rank or catalog entry into live progression
proof.

Run 12342 completed a bounded Praelarran sanctuary-recovery segment without
XP change. The following bounded hero resume checkpointed at 37939 after the
selector found the same current-reboot recovery cooldown, so the campaign is
waiting for the field-area reset rather than replaying an exhausted route.

Earlier bounded resumes exercised Kestrel's stored level-24 Drow Thief
campaign and returned at checkpoint 37955 without XP change. Run 12346
confirmed that negative fame still blocks the Bakery; run 12347 returned
safely to healer room 3054. The live `time` response still reports the older
Kestrel boot marker, while other stored runs have observed Fri Sep 4. This is
safe continuation evidence, not level-25 or HERO proof.

The source food audit then identified Crystal room 10036 and its grain reset
as a viable current route. The wandering Midgaard drunk had been treated as a
permanent rejection even though its `greet_prog 10` is probabilistic. Direct
food and coin ranking now carries that source hazard as a bounded `where drunk`
preflight: an observed drunk on a crossed room or an inconclusive locator
still forces a safe return, while an observed off-route drunk permits the
resource run. Safe `spec_fido` mobiles are also excluded from route-crowd
rejections. The full offline suite passes 3,618 tests.

### Physical combat follow-on: headbutt

The Astra pass now adds source-backed `headbutt` to the shared combat
contract for warrior, brawler, and barbarian identities. `fight.c:do_headbutt`
requires a fighting actor, a target with a head, and a target that is not huge;
its source wait and level-scaled first hit are followed by an optional
`second headbutt` hit when that proficiency is observed. The estimator carries
both branches and the automatic weapon cycle, while the starter emits the
exact no-argument command only for one fresh source-matched live target and
rejects unknown anatomy, head trauma, and stale or non-fighting state. Focused
and full offline tests pass, but this remains capability evidence rather than
live progression or HERO proof.

The same source audit corrected the thief opening budget: `multi_hit` makes a
second `one_hit` attempt after backstab when `double backstab` succeeds. The
planner now carries that optional second hit using the observed proficiency,
and the thief training data schedules the skill after its source prerequisites.
The live controller still issues only the normal `backstab` command; this is a
planning correction, not a new live progression claim.

The thief follow-on now registers source-defined `trip` and `dirt kick` as
control-only actions. The starter makes at most one attempt per exact source
target, after source anatomy, fighting position, compatible sector, and fresh
GMCP enemy gates pass. The player-facing `dirt kick` row records the source
internal `dirt` symbol through `source_skill`; target-state and sector-specific
damage remain estimate-ineligible until those transient inputs are modeled.

The shared combat follow-on now includes vampire `suck` and the bounded
`lunge` opener. Source inspection confirmed that `do_suck` is a fighting-only,
organic-target command that calls one non-dual `one_hit`, while `do_lunge`
requires a standing vampire and an unwounded, non-fighting target before its
source half-damage and rage-adjusted `multi_hit`; `double lunge` may invoke a
second bounded opening. The estimator uses the observed primary weapon or
DD4's unarmed 1d4 range and weights both success probabilities from live skill
percentages. The controller requires a fresh, unique full-health source target
and falls back once after a source rejection. No live vampire progression claim
is made; live organic-target admission and vampire light/blood lifecycle remain
unimplemented, while source body-form classification is now available.

The next physical controller slice is now source-backed warrior `stun`.
`fight.c:do_stun` requires a standing player, a blunt wielded or dual weapon,
and a live non-fighting target with a head that is not huge or already
stunned. The starter therefore admits it only for a warrior with positive
observed proficiency and one exact source VNUM target at full health. It
switches to the strongest source-matched blunt weapon, makes one bounded
attempt, then restores the strongest primary weapon before `kill`; a source
rejection falls back once and an absent target is discarded. This is a
controller improvement, not live progression proof. The shared capability
registry also now validates subclass/base-class compatibility before exposing
subclass actions to the estimator or starter.

The next focused controller slice is martial-artist `kansetsu`. Source review
shows a fighting-only, one-target arm-lock command that can drop an armed
opponent's weapon and deal variable damage. The starter now issues it once only
when level-30 martial-artist identity, positive live proficiency, exact source
VNUM, fresh unique room evidence, and source-armed target metadata all agree.
Server rejection or a successful disarm consumes the attempt, preventing stale
between-round retries. Because the live enemy snapshot does not yet expose
weapon state and the source damage depends on the target's current arms, the
action remains research-only for damage estimation and progression admission.

This reassessment also closed the body-form provenance gap behind those rules.
The area parser now retains DD4's raw body bits, and ranked candidates,
checkpoints, and field stops carry them forward. Kansetsu requires source
evidence of usable arms; the new thug `smash` controller requires a known
non-huge target, a worn shield, and a live fighting target. Missing legacy body
data stays unknown, so the controller cannot silently turn absent evidence into
an anatomy assumption. The slice is covered offline and is not live progression
or HERO proof.

The shared registry audit then exposed a smaller but real drift: the live
controller already handled `disarm` for thief, warrior, ranger, and vampire,
but readiness and training reports did not. Those four source-legal surfaces
now register it as control-only and estimate-ineligible, preserving the live
weapon and response gates instead of treating disarm as recurring damage.

The source candidate record now persists exact VNUM sets for route mobiles,
aggressive route mobiles, attack-program route mobiles, and special route
mobiles. Emergency no-sanctuary recovery accepts only a typed-hazard-free
route, in addition to its source HP, health, isolation, consider,
damage-window, and healer-return gates. The current Kestrel selector therefore
returns an unavailable checkpoint rather than reopening the gravedigger route
or another stale fallback during the same reboot.

The matrix coverage audit found that its durable view could read a newer
character snapshot from an unrelated run and treat any high level as
validation. The ledger now uses only the entry's matching campaign checkpoints.
It reports target-level checkpoint evidence separately from strict
`creation-to-target` proof, which additionally requires a recorded creation
decision in that campaign's segment history. A resumed checkpoint may therefore
be useful live state without being mistaken for fresh creation evidence.

Against the current shared database, `matrix-coverage matrices/level-10.yaml`
reports all three declared entries with target-level checkpoint evidence, but
only two with creation-to-target proof. Kestrel is intentionally the remaining
`target-reached` entry because his stored campaign history predates the creation
decision events; this is a proof-ledger gap, not a reason to fabricate a fresh
creation claim.

The controller audit also found a live command-contract defect: DD4 registers
the repeatable skill as `knife toss`, while the between-round path sent only
`knife`. The controller now emits the exact source command and the full suite
confirms that the repair does not disturb runtime boundaries. The same audit
closed a primary-slot mismatch for `circle`, `backstab`, and `disarm`: a
secondary worn weapon can no longer authorize a command that DD4 will reject
because its `WEAR_WIELD` slot is empty or holds another weapon.

Praelarran's last 12 segments through run 12326 consumed 973.1 recorded
execution seconds: eight maintenance segments took 494.0 seconds and added
200 XP; four field segments took 479.2 seconds and added 1,750 XP. Combined
net throughput was about 120 XP/minute, excluding setup and time between
invocations. This is a small sample, not a general performance benchmark.

Run 12327 exposed a shared runtime failure. Aeloria encountered a drider and
worm; Telnet GMCP repeated the drider while combat text named both attackers.
The source `update.c` room loop serializes the primary `enemy` repeatedly.
The below-band transit branch bypassed the later survival checks. After death,
stale field recovery outranked Purgatory navigation. The outer timeout then
reported the old healthy checkpoint. Run 12328 recovered the corpse,
restored equipment, and returned to healer room 3054. The 5,672-XP reduction
remains failure evidence.

Run 12335 exposed a second shared safety flaw. `where shadow guardian` found
six Shadow Guardians in Shadow Grove, but the old below-band waiver allowed the
route because the source level was low. Their source special can still deal
`9d9+90` damage; the live route caused two stale-snapshot flee losses totalling
464 XP. The route is now quarantined. Runs 12336-12337 validated the immediate
repair boundary: Lord Doom research returned safely with 232 net XP and no
objective kill, while the real hunt stopped before combat without sanctuary.
The pre-retry Aeloria checkpoint was 37924 at 159,305 XP, full in healer room
3054. Run 12338 exposed a further general gap: an unarmed same-band target
whose source HP ceiling exceeds the player's current maximum can outlast the
damage window even when its nominal round bound looks acceptable. The worm
route lost 298 net XP and is quarantined. Run 12339 completed a clean
sanctuary-recovery pass with no XP change. Run 12341 selected Solace Secretary
as a bounded caster calibration. The live target loaded at 321 HP; two
burning-hands exchanges dealt 77 while Aeloria took 60, and the probe withdrew
at 117/218 HP. She returned safely, but the route netted a 125-XP loss and is
quarantined. The complete offline suite passes 3,533 tests.

The training repair is also live-confirmed. An accepted lesson now forces one
bounded post-lesson practice listing, and Aeloria's durable capability state
records `burning hands` at 31% rather than assuming the acknowledgement is the
new percentage.

Earlier repaired autonomous resumes 12329-12330 refreshed the full skill listing
and added 70 funding XP, returning to the Healer at checkpoint 37903,
160,192 XP, full health and mana. They precede the later route losses. The
spell-upgrade branch now has live calibration, but no positive combat or
progression proof.

## Architecture Changes

Emergency precedence is a shared contract: authenticated corpse recovery,
incapacitation, route hazards, combat survival, then ordinary actions. Existing
health reserves, healing options, and bounded finishing attacks still apply.
Route-specific combat cannot bypass them. Duplicate enemy records alone do
not force withdrawal; explicit contradictory combat text supplies the missing
attacker evidence. A source-audited hard route preflight hazard is never waived
by a low nominal level. After a successful flee, stale enemy state is discarded
and the runner enters safe return rather than paying a second flee penalty.
Enemy snapshots are also invalidated whenever the observed room changes,
preventing a previous-room attacker from contaminating healer or recall
decisions; combat flags and fresh current-room snapshots still preserve real
interruptions. Source-ranked unprotected fights now require the audited upper
base-HP bound to fit the player's maximum HP, including same-band targets. The
narrow HP-fuzz exception is limited to one empirical opportunity before any
current-level reboot loss. When a fuzzy target reaches combat, the live
controller compares GMCP maximum HP with the audited source action budget and
withdraws immediately if the target cannot fit inside that budget. Timeouts
retain failed status while checkpointing the latest snapshot and clearing
inherited objective kills.

Source-ranked direct resource routes use the same evidence discipline as hunts.
Deterministic program attackers remain hard source rejections. A single
probabilistic program attacker can instead be attached to the route origin as
a live locator preflight, mapped against normalized room names from the source
path, and treated as a hard stop if the response is absent or places the mobile
on the path. This keeps source inspection useful without converting a static
wander graph into a false guarantee of safety.

The source-resource audit also fixed a provenance blind spot: a mobile reset's
equipment placements are now matched alongside its carried object list. That
makes the Dwarven Catacombs holy-water flask VNUM 2008 visible as a
`mob-equipped` sanctuary source while preserving its `source-only` status,
because the source path is key-locked and no safe key route is currently
proven. The generic sanctuary executor now accepts a different source-safe
potion carrier when one is reachable, carries its exact VNUM into the live
required-loot stop, and retains the established Moria route as fallback.
Castable scrolls, wands, and staves now carry source-derived activation
semantics in the resource report (`quaff`, held `recite`, held `brandish`, or
held `zap self`). The campaign selector now admits those typed objects when
their source carrier passes the same class and route gates as other required
resources. After live acquisition, the starter persists the exact object,
command, target, and remaining charges in `campaign_source_resource_reserves`,
then holds and activates it on a later segment. Source-only rows remain
research evidence until that live boundary is crossed.

The combat path now has one shared capability contract in
`dd4tester/combat_capabilities.py`. Source ranking and live action dispatch use
the same ordered, source-labelled direct-action registry, while formulas and
live safety gates remain separate. This removed a real drift path: base
psionic `agitation` was already source-formula-audited but was absent from the
live spell order and training automation. It is now wired end to end. Registry
entries marked `estimated: false` are intentionally visible for readiness and
future work without creating unverified kill budgets.

The same source pass closes the next small brawler gap. `second punch` is not
a separate command in DD4: `do_punch` emits its extra damage roll when the
positive proficiency and no-arm-trauma conditions pass. The source estimator
now includes that bounded contribution in the existing `punch` budget, and
training can pursue it as automated damage without inventing an extra action.

The next pass closes the equivalent ranger accounting gap. DD4's `do_shoot`
temporarily uses the equipped bow, performs a source-gated first hit plus the
observed `second shot` and `third shot` branches, then restores the prior melee
loadout. The planner now resolves the bow from the structured
`ranged_weapon` slot and carries that volley as one opening budget beside the
normal melee or kick action. It does not admit shoot without a source bow or
turn the pre-combat volley into recurring damage. That intermediate ranger
pass passed 3,548 tests; the current complete suite passes 3,615 tests.
The starter preserves live-observed skills that are not yet in the registry
after the registered order, while unknown names remain filtered by
action-specific dispatch gates.

Smithy `counterbalance` now follows the same evidence contract. A confirmed
anvil command records the exact prepared weapon VNUM in campaign metadata, and
the source estimator adds DD4's `APPLY_BALANCE` extra-attack chance only when
that VNUM matches the currently wielded source object. A learned skill without
matching object evidence remains ordinary weapon output, so a replacement
weapon cannot inherit an unverified passive attack estimate.

The source catalog remains advisory. `autonomy-audit` inventories registered
templates and their declared status; it cannot certify that an arbitrary
character can execute them successfully. Capability confidence must distinguish
source legality, trained skills, and current usable resources.

The Astra implementation pass makes that distinction executable. The audit can
compare all nine base classes with `--all-classes`, reports a separate combat
automation status, and combines subclass gaps with base-class gaps. A live
practice entry at `0%` is training information only: opener, mitigation,
between-round, and subclass-action dispatch now require a positive observed
percentage, while legacy checkpoints with no percentage map keep their
backward-compatible known-skill behavior. This removes a silent no-progress
failure mode without claiming that static templates are live proof.

The follow-up implementation adds a bounded source-output model for audited
single-target caster spells. It carries the action, damage bounds, mana cost,
conservative action budget, source-derived expected incoming rounds, and
`magic.c` reference into each generated field stop. That model can relax the raw
source-HP sanctuary requirement only when the incoming peak, projected whole-
fight health reserve, and mana reserve also fit; it still requires a current
live enemy HP snapshot and the damage-window probe. Aeloria's first Secretary
probe falsified the looser admission with a 125-XP loss, so the route is now
quarantined and the tightened selector requires sanctuary for that 146-425 HP
matchup. This is calibration evidence, not a progression claim.

The model now includes base psionic `agitation` and the legal level-30
subclass direct-damage family: necromancer `harm`, druid `wither`, knight
`flamestrike`, and monk `agitation`. The estimator receives both base class and
live subclass, so a skill from one subclass cannot make another subclass's
route appear executable. Each formula remains a planning bound and is still
subordinate to live `consider`, health, mana, crowd, route, and damage-window
gates.

The same source-output contract now covers the existing action controllers for
brawler `punch`, martial artist `atemi`, werewolf `wolfbite`/`ravage`, the
ranger `shoot` bow opener, warrior/ranger `kick`, learned thief `knife toss`,
learned thief `circle` with
a source-identified piercing weapon, and ordinary weapon strikes. A trained
thief's source-matched `backstab` is carried once as an opener and never as a
recurring action. Learned percent actions are weighted by their observed
proficiency. A weapon
projection is admitted only when structured GMCP or an unambiguous legacy
checkpoint identifies the wielded source object; it applies the `fight.c`
damage dice, live damroll, observed enhancement percentages, and conditional
`multi_hit` follow-up chances. Hit chance, temporary affects, armor, and
resistances remain live-calibration concerns. The campaign gate can compare
this conservative output with a target's source HP ceiling without turning an
unknown or ambiguous weapon into a capability. The live action cooldown and
damage-window checks remain authoritative. When a between-round kick, knife
toss, or circle is available, its budget includes the automatic weapon cycle
that continues alongside the command. A backstab opener remains a one-shot
addition only.

The ranger path now resolves a source-identified bow from DD4's separate
`ranged_weapon` slot. Observed `shoot`, `second shot`, and `third shot`
proficiencies contribute to one bounded opening volley beside the normal melee
or kick action; the bow is never treated as recurring damage.

The next lifecycle slice adds straight-shifter form handling. With live-known
`morph` and `snake form` at the source's 20% minimum, the starter can enter
snake form between weapon rounds using the exact form mana formula. At the
Midgaard healer it wakes, waits for the fixed 10-mana normal-form cost, and
restores normal form before gear or sale maintenance. This does not yet claim
that the generated natural weapon beats carried gear, so form output remains
outside source-ranked damage admission.

The progression control has now been narrowed to two explicit paths: mandatory
state transitions first, then an executable generic frontier before ordinary
research. This makes the level-10-to-HERO path character-independent without
discarding named research when no safe target is available. The distinction is
important for reports: a selected candidate is an execution plan, while only a
confirmed kill and checkpoint can advance progression evidence.

Avoid a wholesale rewrite of the large starter and campaign modules. Extract
shared decisions when a replay exposes conflicting priorities, retain existing
adapter and storage contracts, and verify each extraction across representative
classes. Every failure should produce a reusable regression.

The reassessment also found a control-plane synchronization gap: bounded
resumes previously honored an old character reboot marker until an explicit
reset wait was requested, even when another character had already recorded a
newer reboot in the shared ledger. Startup now schedules one maintenance-only
world-time probe when that mismatch is visible. The shared marker is a trigger,
not proof; the live character's `time` response must refresh and confirm its
own reboot identity before reboot-scoped evidence is reused.

## Next Work

1. Reconcile Kestrel's current level-24 losses and resource state, then wait
   for the reboot boundary or acquire sanctuary before another field fight.
   Do not retry the gravedigger route during this reboot: its source route
   includes aggressive transit mobiles, and the fallback allowance is now
   correctly closed. After the boundary, validate a route with fresh live
   isolation and consider evidence before resuming progression.
2. Continue Aeloria from checkpoint 37994 toward level 19 using independent
   source-ranked familiar-compatible targets and the same live consider,
   isolation, damage-window, resource, and healer-return gates. Keep the
   measured Secretary exchange as quarantine evidence, preserve the familiar
   withdrawal rule, and obtain or prove a protection reserve before taking an
   armed target. Validate the level-19 frontier before attempting the level-20
   trainer and subclass gate.
3. Reduce maintenance overhead through useful loot variety, capacity-aware
   selling, funded supplies, and multiple suitable kills per journey. Evaluate
   net XP per total elapsed time, objective kills, losses, deaths, and time
   spent recovering or provisioning together. Do not optimize kill count alone.
4. Use the all-class audit to turn the largest declared combat gaps into replay
   cases, beginning with the level-10 trainer transition and the thief, mage,
   and warrior surfaces. The source-first level-10 handoff now supplies the
   reusable progression path; named probes remain fallback evidence when the
   selector has no safe target. Advance the current frontiers, validate
   level-20 trainers and the level-30 subclass transition, then extend bands in
   step with live characters. Follow with fresh race/class coverage and
   uninterrupted HERO proof runs.
5. Keep extending the source-action matrix only when a command has both a
   source-audited formula and a deterministic controller. The next live pass
   should calibrate the new physical actions against a fresh, lower-risk target
   at the actual warrior/thief frontiers, then use that evidence to choose
   multiple-kill routes. The next high-value lifecycle work is source-ranked
   selection among later straight-shifter
   forms, vampire light/blood handling, and follower or constructed-platform
   control for the remaining subclasses; each must earn replay coverage before
   it changes admission. The weapon branch now makes the current warrior and
   thief frontiers measurable; the next live step is to calibrate that output
   against a fresh, lower-risk target rather than reopen quarantined routes.

Humanlike reports must describe observed events and uncertainty. Preserve
timestamped operator steering and commentary, bounded execution, and manual
remote publishing throughout.
