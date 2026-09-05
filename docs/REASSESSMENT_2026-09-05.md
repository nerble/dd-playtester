# Autonomy Reassessment: 2026-09-05

## Objective

Keep the master goal: one parameterized command creates or resumes a legal
character and autonomously reaches the requested level, ultimately HERO 100.
Names select credentials and history only. Sex is cosmetic. Reuse the same
decision engine behind direct Telnet and Mudlet; VM visibility is a separate
integration test. No character has yet proved creation-to-HERO.

## Evidence

### Latest Live Finding

The Astra re-audit continued Kestrel's level-24 Drow Thief campaign. Run
12355 acquired source-verified food at the live Haon endpoint. Run 12356
reached the source-identified Old Treant but live `consider` classified it as
below the useful XP band, so it stopped without combat. Run 12358 reached the
Solace Secretary: live `consider` accepted the target, but the target's GMCP
maximum was 523 HP while the thief's audited recurring action budget was 300
damage. The bounded run recalled at a 385-XP loss before a kill and left
checkpoint 37973 at 333,918 XP in healer room 3054. This is failure evidence,
not level-25, subclass, or HERO proof.

The repair closes the unprotected HP-fuzz exception after any current-level
reboot loss and adds a live budget gate that withdraws when a fuzzy target's
GMCP maximum HP exceeds its audited source action budget. The selector still
uses the source nominal level only to avoid a false static below-band deadlock;
live `consider` remains authoritative on the loaded mobile. Fresh post-reboot
live validation is required before treating either repair as progression
evidence.

The latest saved states are Praelarran, warrior, level 20, Aeloria, mage,
level 18, and Kestrel, thief, level 24. Serevian remains a stored thief
campaign at level 11. Work should follow these actual frontiers rather than
the static HERO template count.

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
rejections. The full offline suite passes 3,531 tests.

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
The current Aeloria checkpoint is 37924 at 159,305 XP, full in healer room
3054. Run 12338 exposed a further general gap: an unarmed same-band target
whose source HP ceiling exceeds the player's current maximum can outlast the
damage window even when its nominal round bound looks acceptable. The worm
route lost 298 net XP and is quarantined. Run 12339 completed a clean
sanctuary-recovery pass with no XP change. Run 12341 selected Solace Secretary
as a bounded caster calibration. The live target loaded at 321 HP; two
burning-hands exchanges dealt 77 while Aeloria took 60, and the probe withdrew
at 117/218 HP. She returned safely, but the route netted a 125-XP loss and is
quarantined. The complete offline suite passes 3,531 tests.

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

The model now includes the legal level-30 subclass direct-damage family:
necromancer `harm`, druid `wither`, knight `flamestrike`, and monk `agitation`.
The estimator receives both base class and live subclass, so a skill from one
subclass cannot make another subclass's route appear executable. Each formula
remains a planning bound and is still subordinate to live `consider`, health,
mana, crowd, route, and damage-window gates.

The same source-output contract now covers the existing action controllers for
brawler `punch`, martial artist `atemi`, werewolf `wolfbite`/`ravage`, learned
warrior/ranger `kick`, learned thief `knife toss`, learned thief `circle` with
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

The next lifecycle slice adds straight-shifter form handling. With live-known
`morph` and `snake form` at the source's 20% minimum, the starter can enter
snake form between weapon rounds using the exact form mana formula. At the
Midgaard healer it wakes, waits for the fixed 10-mana normal-form cost, and
restores normal form before gear or sale maintenance. This does not yet claim
that the generated natural weapon beats carried gear, so form output remains
outside source-ranked damage admission.

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
   Validate the new HP-fuzz budget gate live before resuming progression, and
   keep independent field routes available after a failed matchup.
2. Rotate Aeloria to an independent source-ranked candidate after the Secretary
   quarantine, using only the tightened whole-fight caster gate. Improve
   sustainable damage and protection before adding distant routes; retain the
   measured 77-damage/60-incoming exchange as calibration rather than retrying
   the failed route.
   The mage plan now adds the evocation 45% / burning hands 30% path at
   level 10+, gated by observed teacher availability and practice budgets; the
   live listing now confirms the trained spell percentage. Measure its actual
   damage and mana use, and obtain or prove a protection reserve before taking
   an armed target. Saves and resistance affect value.
3. Reduce maintenance overhead through useful loot variety, capacity-aware
   selling, funded supplies, and multiple suitable kills per journey. Evaluate
   net XP per total elapsed time, objective kills, losses, deaths, and time
   spent recovering or provisioning together. Do not optimize kill count alone.
4. Use the all-class audit to turn the largest declared combat gaps into replay
   cases, beginning with the level-10 trainer transition and the thief, mage,
   and warrior surfaces. Advance the current frontiers, validate level-20
   trainers and the level-30 subclass transition, then extend bands in step
   with live characters. Follow with fresh race/class coverage and
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
