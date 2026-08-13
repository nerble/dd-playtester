# Progress Audit: 2026-08-13

## Refined Goal

The active goal remains one character-independent, rule-based engine that
accepts a source-legal race, cosmetic sex, base class, optional subclass,
name, and personality, then creates or resumes the character and plays it
without manual gameplay to HERO level 100. Names and credentials identify
history only. Direct Telnet and GMCP remain the primary adapter; Mudlet and a
Windows virtual machine are later visibility and lifecycle boundaries. AI
decision-making stays deferred until deterministic policy execution is broad,
replayable, and measurable.

The proof order is creation and tutorial, representative level-10 classes,
class-aware level 1-30 progression with a confirmed level-30 subclass change,
executable bands through 31-70 and 71-100, and finally fresh
creation-to-HERO runs. Every band needs source identity, live consider and
route evidence, resource and recovery evidence, and offline regression tests.

## Current Evidence

- Async Telnet, negotiation, GMCP, redacted transcripts, YAML profiles,
  SQLite checkpoints, reports, process recovery, and the Discord conversation
  stream are operational.
- The Discord stream's permanent `--new-only` mode now treats truncation,
  replacement, and in-place rewrites as an EOF reset rather than a byte-zero
  rewind. It also fingerprints speaker/body content independently of the
  timestamp, preventing resumed tasks from reposting the same turn under a new
  timestamp. All 17 focused tests pass; the live process is at exact EOF with
  an empty queue and a seeded recent-content ledger.
- The live mage/thief/warrior matrix reaches level 10. Current long-running
  anchors are Aeloria mage level 13 at 74,825 XP, Dorrik warrior level 16 at
  123,437 XP, and Kestrel thief level 24 at 360,704 XP.
- Runs 5447 through 5459 exposed a level-boundary selector defect: useful
  Shire and Wyvern repeats were allowlisted through source-mobile reward
  evidence but retained `fresh` ordering under regenerated level-15 policy
  IDs, behind a 50-XP current-level repeat. The repaired selector promotes
  those candidates into the productive pool. Run 5460 selected receptionist
  1131, earned 401 objective XP, and returned safely to healer room 3054. Runs
  5467 and 5468 then selected Wyvern ranger 1706 and receptionist 1131 back to
  back, earning another 600 objective XP with two safe healer returns.
- Runs 5470 through 5488 continued that rotation without crediting absent
  Shadow Keep or Haon Dor objectives for incidental travel kills. Run 5493
  then killed ranger 1706 for 380 objective XP and crossed Dorrik to level 16.
  The healer checkpoint records 345 max HP, 300 max movement, three practices,
  subclass `none`, and 115,129 XP.
- Runs 5494 through 5496 completed the first level-16 handoff. The executor
  preserved below-band safety against both Fleshmonger guards, trained `shield
  block` and `defense knowledge`, killed Aruncus mobile 300 for 519 objective
  XP, and returned full to healer room 3054. The live checkpoint now records
  two practices and 115,688 XP.
- Run 5499 live-validated worn-aware required-loot accounting. One worn pink
  ice ring left exactly one ring outstanding, while the worn linen robe closed
  the nanny branch. The runner searched the registered doll room, traversed the
  nanny room without considering or attacking her, and returned safely in 50
  seconds. Runs 5498 and 5500 added 1,107 objective XP from Bardoosh and
  Aruncus; Dorrik is full at healer room 3054 with 117,035 XP. The focused
  starter suite passes 985 tests and the full suite passes 2,524 tests.
- Runs 5502, 5503, 5506, and 5507 then added 1,612 objective XP through
  source-matched Bardoosh, Aruncus, ranger, and Bardoosh kills. The intervening
  ring and flight maintenance remained bounded and returned control to XP
  selection. Dorrik finished full and safely logged out at healer room 3054
  with 118,647 XP, 14,953 short of level 17.
- A tightly bounded source gate now permits one aggressive transit prototype
  whose worst fuzzy roll is exactly the useful-band fringe, provided it has a
  single global source instance, no special, fame, shop, or no-XP flag, and
  both maximum damage bounds remain below current max HP. Live below-band
  evidence permits the defensive kill; a useful-band roll still triggers the
  existing flee path. Fifty hunt-candidate tests, 739 campaign tests, and all
  2,526 offline tests pass.
- Run 5512 live-validated that gate in Ambush. Three unavoidable below-band
  transit kills supplied 160 incidental XP, Haglik mobile 4519 supplied 622
  tagged objective XP, and the prisoner and elite guard were considered but
  skipped as below-band. Dorrik returned full to healer room 3054 with 119,429
  XP, 14,171 short of level 17.
- Run 5515 added 963 objective XP from Dwarven Nobleman mobile 20504. Run 5516
  then showed that an ambiguous positive `where` label could preserve every
  intermediate source room as a full hunt stop and consume the 240-second
  boundary. The repaired locator retains those source paths as transit but
  inspects only matching room labels, reducing the current Aruncus route from
  42 target stops to seven before one fresh all-origin relocation.
- Run 5518 added 930 tagged objective XP from Haglik plus 160 incidental XP.
  Its safe return exposed `The brush is closed`, which the door/grate-only
  recovery parser missed; the runtime watchdog still recalled Dorrik safely.
  Generic named closed exits now open and retry, named locked exits fail
  closed, and all 2,528 offline tests pass. Dorrik is safe at healer room 3054
  with 121,482 XP, 12,118 short of level 17.
- Run 5522 added 619 tagged Bardoosh XP. Runs 5523 through 5525 completed
  bounded ring, flight, and food maintenance. Run 5526 live-validated the
  repaired locator: `where` reported `Path in the plains`, the compacted route
  found Aruncus in room 302 for 501 objective XP, and the segment returned
  without a runtime boundary. Run 5527 then added 655 objective Haglik XP and
  160 incidental transit XP. Dorrik is fully recovered at healer room 3054
  with 123,437 XP, 10,163 short of level 17. The named-exit parser remains
  offline-verified pending a fresh live closed-exit response.
- Run 5436 live-validated exact below-band objective filtering. The selected
  goblin leader loaded at level 8 against level-15 Dorrik; its unavoidable
  80-XP kill was stored with durable non-objective flags and no source-policy
  credit, while the terminal checkpoint retained the exact policy exclusion.
  Run 5437 then selected a useful-band fanatical guard and returned safely.
- Runs 5383, 5385, and 5386 then validated the repaired risk/reward handoff:
  Dorrik killed a source-matched ranger for 389 XP, followed by a Shire
  receptionist for 334 XP, and crossed level 15 safely. The final segment's
  incidental goblin XP remains separate from objective evidence; the durable
  checkpoint is full at healer room 3054.
- Run 5391 validated the next level-15 route: the registered Shadow Keep
  search found wandering Undead Soldier mobile 16601 in room 16618, earned
  956 XP, and returned to healer room 3054 at full health. Dorrik was then at
  99,355 XP; Fleshmonger and Ambush below-band results remain closed.
- Runs 5392 through 5401 exercised the failed-return recovery, maintenance,
  and absent/low-value route branches. Run 5400's lone 10-XP drunk kill exposed
  stale wandering-target promotion: contact had been associated with the
  selected room rather than the tagged source identity. Run 5402 corrected the
  live balance by selecting Bardoosh mobile 4515 in room 4514, earning 671
  objective XP and 851 XP total after three incidental 60-XP goblin kills, then
  returning Dorrik to healer room 3054 at full health and movement.
- The selector now requires an explicit objective kill of at least 50 XP before
  a source-ranked result becomes productive history. Wandering kills use their
  tagged source policy identity. A fresh route can displace a productive repeat
  only when its risk-adjusted reward per travel step is at least 25% stronger;
  an aggressive requested target is scored as a risk-pool option behind the
  normal source, consider, crowd, health, protection, and return gates.
- Run 5403 then selected Aruncus the Druid, mobile 300 in room 323, and earned
  505 objective XP. Dorrik returned to healer room 3054 at full 322/322 HP and
  290/290 movement, leaving 13,493 XP to level 16. This confirms the revised
  throughput preference can choose and complete a materially rewarding route.
- Run 5405 repeated the productive Bardoosh route for 351 objective XP and one
  incidental 70-XP goblin kill. Dorrik returned to healer room 3054 at full HP
  and 264/290 movement, leaving 13,072 XP to level 16.
- Run 5406 repeated Aruncus for 462 objective XP, returning to healer room 3054
  at full HP and 269/290 movement. Dorrik now has 12,610 XP to level 16.
- Run 5407 found the fanatical goblin guard, source mobile 4516, wandering into
  room 4522. Dorrik killed it for 264 XP after absorbing a critical hit and
  returned safely; the fight ended at 228/322 HP before healer recovery. The
  old record did not attach source metadata because the display-name stop and
  live wandering identity differed. The repaired runtime now records exact
  live enemy VNUMs for this attribution path.
- Run 5409 selected Aruncus mobile 300 for 421 XP in 69.8 seconds and returned
  at full HP with 272/290 movement. Run 5410 reopened the cooled Shargugh route
  and confirmed it absent; runs 5411 and 5412 completed flight/provision upkeep
  without being counted as progression.
- Run 5413 reached Bardoosh. Its SQLite event trail records a 60-XP goblin
  lieutenant interruption and a 460-XP Bardoosh kill, but the worker was stopped
  after the transcript remained empty. Run 5414 completed healer recovery at
  103,935 XP. Keep the interrupted segment failed until its kill metadata is
  reconciled; the orphan-run cleanup now closes its unbound run row as well.
- Run 5415 confirmed both Shadow Keep Wraith rooms absent after one incidental
  60-XP goblin interruption. Run 5416 then reopened the fanatical goblin guard,
  confirmed source mobile 4516, earned 257 objective XP, and returned at full
  HP with 281/290 movement. Dorrik is now 10,488 XP from level 16.
- Run 5417 proved write-time durability by exposing its incidental kill in
  SQLite while the run still had status `running`. Interrupted source-ranked
  recovery now reads that run-scoped ledger and requires the exact policy ID,
  so incidental kills cannot masquerade as the objective.
- Run 5418 found Aruncus beside an Ofcol cityguard. Source `spec_guard` is
  non-hostile to Dorrik's +1000 alignment unless aiding a sub-300 combatant; the
  runner now permits that sole profile after one observed non-hostile retry,
  while ambiguous and lower-alignment cases remain blocked.
- Run 5419 then completed the fanatical-guard route for 286 objective XP plus
  70 incidental XP and returned Dorrik fully recovered at 104,728 XP, 10,072
  from level 16. Objective kills now clear stale target-absence metadata.
- Runs 5420 and 5421 found Shargugh and the Wraith circuit unavailable while
  earning only 60-XP and 10-XP incidental transit kills. Those raw deltas had
  incorrectly hidden a two-segment no-progress streak. Progress accounting now
  requires objective-kill evidence in-process and after restart. Run 5425 then
  selected the measured fanatical-guard repeat, earned 303 objective XP, and
  returned full at 105,161 XP, 9,639 from level 16.
- Run 5408 then accepted the measured Bardoosh repeat: mobile 4515 yielded 460
  objective XP and a wandering goblin added 70 incidental XP. Dorrik returned
  without death or flee at full 322/322 HP and 279/290 movement, reaching
  102,994 XP. This confirms that the revised policy can tolerate meaningful
  field risk for throughput without treating safe return as the only success
  criterion.
- Runs 5231 through 5245 continued Dorrik's generic source-ranked level-13
  frontier without steering. Run 5246 crossed him to level 14; the live
  checkpoint recorded 295/295 HP, 280/280 movement, two practices, and
  subclass `none`. Run 5247 completed post-level recovery at healer room 3054.
  No segment stalled, died, or required corpse recovery in this transition.
- Runs 5249 and 5251 then completed useful level-14 Ambush kills from two
  distinct source reset rooms for 911 and 514 XP. Runs 5250 and 5252 handled
  liquidation; each field segment returned Dorrik safely to healer room 3054.
- Run 5258 added a productive 551-XP Ambush repeat. Run 5261 observed a live
  Ambush identity whose consider result was non-viable and correctly skipped it;
  run 5262 refreshed flight. Dorrik remained full and safe at healer room 3054,
  with no stalled segment, death, or corpse recovery.
- The MUD rebooted during this work. Runs 5269 and 5271 re-established the
  Dwarven Nobleman route under boot `Wed Aug 12 17:44:43 2026`; the bounded
  kill attempt reached the 15% withdrawal floor without a kill, and run 5272
  restored full health in healer room 3054. The result remains negative
  research evidence for this level and boot, not a software failure.
- Runs 5274, 5280, 5284, and 5295 then produced useful current-band XP from
  Plains North, Fleshmonger, and both Ambush reset identities. Run 5302
  completed a successful Shire continuation at 91,544 XP. Run 5307 then
  selected source-ranked Ambush Bardoosh: live consider was viable, but an
  armed critical stab killed Dorrik after two incidental low-XP goblin
  interruptions. Purgatory corpse recovery, equipment restoration, healer
  recovery, save, and quit all completed; the death penalty left the durable
  checkpoint at 87,820 XP in room 3054. The exact mobile VNUM, reset room,
  level, and reboot are now fatal evidence for that policy, while the selector
  remains free to choose other productive current-band targets.
- Bounded post-repair runs 5308 through 5310 then selected a current-band duty
  target, refreshed flight, completed the ranger circuit, recovered a long bow,
  and returned Dorrik to healer room 3054 at full resources and 88,279 XP.
- Runs 5311 through 5316 then sold loot, returned home, completed maintenance
  and Moria transitions, and killed a Shadow Wraith for 296 XP after two
  trivial transit interruptions. Dorrik returned at full resources with 89,572
  XP; no death or stalled segment occurred.
- Runs 5317 through 5319 then completed daycare and flight maintenance and
  killed the source-matched ranger for 624 XP, returning at full HP and mana.
  The ranger transcript records a nonfatal carry-capacity rejection while
  collecting a long bow; loot collection did not obscure the objective kill.
  Dorrik is now at 90,196 XP with 7,904 XP to level 15.
- Runs 5320 through 5325 then handled sanctuary, Moria, and daycare
  prerequisites, killed a Shire receptionist for 569 XP, and recorded both
  registered Shadow Wraith rooms absent. One unavoidable transit goblin remains
  separate from objective XP. Dorrik returned safely at 90,835 XP with 7,265
  XP to level 15.
- Runs 5326 through 5328 then followed the source-backed Moria and Wraith
  circuits; both Wraith rooms remained absent, so no objective kill was forced.
  The field produced only incidental kills, and Dorrik returned safely to
  healer 3054 at full HP and mana with 91,025 XP.
- Runs 5329 through 5334 then added a 449-XP ranger kill and a 349-XP Shire
  receptionist kill, with safe healer returns. The following Wraith route was
  absent again on both registered rooms, so the runner recorded absence and
  did not force combat; Dorrik reached 91,903 XP without death or a stalled
  segment.
- Runs 5335 through 5337 then completed a source-ranked Aruncus kill for 743
  XP and safe daycare/Moria maintenance. Runs 5338 and 5339 completed two
  Wraith probes safely; the incidental goblin XP remained outside objective
  attribution. Dorrik reached 92,836 XP without death or a stalled segment.
- Run 5343 restocked provisions. Run 5344 then completed a source-matched
  Aruncus kill for 919 XP in 166.6 seconds with full health before and after.
  Runs 5345 and 5346 found the two Wraith rooms absent and recorded only
  incidental goblin XP outside objective attribution. Dorrik reached 94,264 XP
  without death or a stalled segment.
- Source-ranked stops now carry a DD4-derived one-hit critical reserve. The
  ordinary aggressive 15% withdrawal and 10% finish thresholds remain in
  force, but a source-verified critical that can kill raises only that target's
  floor. Objective-kill attribution also requires exact target/source identity,
  preventing route interruptions from inflating XP evidence. The source-ranked
  selector also compares safe multi-target circuits by risk-adjusted source
  reward per travel step, so a wandering high-score singleton cannot suppress
  a productive fixed-reset circuit. The offline suite now passes 2,526 tests.
  No remote push or local commit was attempted under
  the local publication policy.
- The source graph has no practical level-14 bypass around Miden'nir to the
  Dwarven Home route. The fastwalk now distinguishes its source-level-seven
  goblin lieutenant as a below-band transit interruption from level fourteen
  onward, while retaining the higher-damage dark horseman and wyvern as hard
  hazards. Run 5353 reached the Dwarven Homestead, resolved the abbreviated
  live goblin identity through mobile VNUM 3501 after delayed GMCP, and
  recorded a positive nobleman consider without combat. Runs 5354 through
  5358 reconciled the standalone probe, restocked, and rotated past crowded or
  absent candidates. Run 5359 then completed a source-ranked current-band
  ranger kill for 413 XP in 141.8 seconds and returned full; run 5360 completed
  maintenance. Dorrik is now at 95,303 XP in healer room 3054. The lieutenant
  remains incidental evidence and cannot become an XP objective merely because
  it interrupts travel.
- The VNUM-first and delayed-GMCP identity fix is covered by focused tests,
  and remains covered in the full 2,526-test offline suite. The no-combat route waits
  one bounded prompt for `Char.Enemies`, then uses the live `isnpc` VNUM before
  abbreviated text names; unresolved attackers still abort conservatively.

## Architecture Findings

The system has a sound layered boundary: protocol and observations produce
typed events; the reducer produces revisioned state; source catalogs and class
analysis feed a progression context; the campaign selector chooses a policy;
the deterministic executor performs navigation, training, combat, provisions,
recovery, death handling, and checkpointing; reports and commentary derive
from stored evidence.

The key policy insight is a two-stage lifecycle. Registered policies describe
bounded research probes and remain `research` until their own promotion gates
are satisfied. After a current-reboot result, runtime may hand off to the
generic source-ranked executor. This is why a static coverage report can still
show a research row while a live campaign is making safe, productive progress
in that same level band. Campaign segments and objective-kill records are the
authoritative live ledger.

The risk/reward boundary is explicit. Source-ranked selection still prefers
productive current-band routes and retains bounded research/probe pools for
high-payoff candidates; it does not blanket-ban armed mobiles. During combat,
the runner retains the aggressive field thresholds unless source evidence for
the active mobile supplies a critical burst that can kill at the current HP.
That reserve becomes the withdrawal floor, and a death without an objective
kill permanently blocks the exact policy for the current level and reboot.
The selector audit found one throughput-specific failure mode: after the
fresh-pool kill cap removed a measured ranger or receptionist repeat, an
expired Shadow Keep absence could be treated as a fresh or retryable target and
win a long field segment. The selector now compares status and measured XP
evidence explicitly. A retryable absence cannot hide a meaningful same-reboot
repeat, and a no-flight fallback cannot displace a productive route merely to
avoid a flight purchase. This preserves the source and live safety gates while
raising expected XP per travel step.

Reward continuity must also survive generated policy-ID changes at a level
boundary. A prior-level objective kill is carried by source mobile VNUM; when
that evidence explicitly allowlists the current candidate, selection treats it
as productive for ordering. The result itself is not rewritten, and the live
executor still decides whether the target is currently legal and worthwhile.
Run 5460 is the live proof of that distinction.

Source provenance is similarly explicit. The live read-only DD4 checkout is
`f2491fd`; the prerequisite and training snapshots are pinned to `f703daa`,
and the fallback character catalog to `0482387`. A relevant source change
requires either regenerating the snapshot or recording both revisions and
re-auditing the affected policy.

## Remaining Gaps

No fresh character has completed level 0 to HERO. Generic class and subclass
coverage is not yet proven through level 30, the higher-band routes remain
mostly research, and level 81-100 still has no complete executable evidence.
The subclass transition, broader race/class proof, Mudlet/VirtualBox visible
execution, and humanlike commentary acceptance run are also outstanding.

## Resumed Work Order

The active goal is now the level-14-to-30 frontier. Continue bounded,
no-steering segments, retain objective XP and safe-return evidence by source
mobile VNUM, and add a focused regression whenever a new failure appears. At
each level boundary, verify training, stat, equipment, subclass, and resource
state from the live checkpoint before the next hunt. Then rotate the same
generic executor through Aeloria and Kestrel to expose shared-policy gaps.
Only after the level-1-30 path and level-30 subclass handoff are executable
should the project spend effort on the high-band routes and visible Mudlet/VM
layer.

## Definition Of Done

The goal is complete only when one command can create or resume any legal
request, progress autonomously to level 100, survive normal restart, reboot,
death, and disconnect paths, preserve transcripts and checkpoints, produce a
final HERO report with commentary, and pass fresh proof for every base class
plus legal race/class pairings at level 10. Configuration or policy-count
output alone is never sufficient.
