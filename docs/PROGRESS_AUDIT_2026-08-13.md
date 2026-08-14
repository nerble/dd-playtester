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
  rewind. Append position and the monotonic timestamp fence define live
  records, so repeated speaker/body text is delivered when it is genuinely
  appended; exact-record fingerprints only prevent duplicate queueing. Network
  and HTTP 5xx failures are dropped as uncertain, while HTTP 429 is retried.
  A 30-second delivery-age fence now drops delayed queued records instead of
  replaying them, and the state records the exact cutover byte and timestamp.
  The first record at the cutover second is rejected, while subsequent
  same-second appends are accepted after the byte cursor crosses the boundary.
  All 26 focused tests pass. The 5:11 AM clean restart started exactly one
  worker at the current EOF, published the fresh restart commentary once, and
  emitted no historical record. Existing duplicate Discord messages are not
  deleted by the webhook worker. Subsequent live commentary and user records
  were each published once; the live checkpoint remains at source EOF with
  an empty queue and no in-flight record.
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
- The next level-17 batch exposed and repaired a route-cursor interruption.
  When combat consumes a field movement command before DD4 emits a new-room
  GMCP snapshot, the executor now rewinds the pending destination for both
  official outbound and hunt routes. Regression coverage exercises the same-room
  combat path, and the relevant offline suite passes 2,188 tests. Unsteered runs
  5636 through 5638 then completed an Ambush Bardoosh kill for 378 objective XP,
  followed by loot liquidation and a safe return to healer room 3054, without a
  route abort or death. Dorrik is level 17 at 140,788 XP. This is live recovery
  evidence, not proof of level-30 or HERO completion.
- A maintenance-ledger regression then caught a second generic boundary bug:
  an incidental wandering-mobile kill during `liquidate-loot` could survive in
  the runner's transient objective fields and contaminate the next campaign
  checkpoint. Non-objective maintenance end states now clear both objective and
  completed-kill metadata while retaining the raw transcript evidence. The
  focused regression and full relevant suite pass 2,189 tests. Unsteered runs
  5643 and 5646-5647 added safe Eastern Desert evidence; runs 5643 and 5647
  killed source mobile 5007, the nomad commander, for 560 and 440 objective XP,
  respectively, while incidental transit kills remained separate. Dorrik is
  level 17 at 142,645 XP in healer room 3054. This remains below-band proof,
  not a level-30 or HERO completion claim.
- Policy revision 166 adds live-state movement-capability filtering to generic
  source-ranked circuits. Source routes entering water or air are omitted when
  the character has no verified fly, levitation, swim, native-water race, or
  boat capability; the real Shadow Keep graph now produces land-only stops for
  Dorrik instead of scheduling the moat reset. The focused regression and full
  relevant suite pass 2,190 tests. Run 5656 is retained as pre-repair evidence:
  it reached the moat, refused the impossible swim, and recalled safely. The
  corrected unsteered runs 5657-5662 completed New Ofcol, Plains North, return
  home, Crystal, and Dwarven routes without a movement abort; run 5662 killed
  source mobile 6506 for 721 objective XP and returned Dorrik full to healer
  room 3054 at 144,509 XP. Later unsteered selections 5665, 5672, and 5683
  re-entered Shadow Keep under revision 166 without issuing the impossible swim
  step; active flight allowed the water-side branch to remain reachable while
  land-safe stops were absent. That is live evidence for the corrected selector,
  while the no-capability branch remains covered by the focused regression.
- Runs 5663-5689 then continued the generic level-17 rotation without steering.
  Objective kills included Eastern Desert mobile 5006 for 605 and 797 XP,
  mobile 5007 for 499 and 462 XP, plus a 412-XP objective kill with 260 XP
  from below-band transit attackers, and Aruncus mobile 300 for 385, 628,
  and 485 XP. Bardoosh and Shadow Keep were observed and skipped under live
  gates; loot liquidation, healer recovery, and safe logout completed without
  death or route abort. Dorrik is now level 17 at 150,042 XP, 4,408 short of
  level 18. This is executable level-17 evidence, not a HERO completion claim.
- Runs 5690-5698 added another clean flight purchase, an Arachnos kill for 370
  XP, an Aruncus kill for 632 XP, an Eastern Desert commander kill for 378 XP,
  and a bounded Crystal probe. The Crystal route reached its target area but
  withdrew after the incidental Fewmaster Toede encounter consumed the field
  reserve; its 394 incidental XP remained separate from objective progress and
  the exact route hazard was persisted. Dorrik returned full to healer room
  3054 at 151,816 XP, 2,632 short of level 18, with no death or movement abort.
- Runs 5699-5706 then completed the level-18 boundary without steering. The
  Arachnos bird spider supplied 733 total XP, including a 404-XP target kill,
  and the live response raised Dorrik to level 18. The transition granted 25
  hitpoints, 7 mana, 10 movement, 3 physical practices, and 1 intellectual
  practice; the durable healer checkpoint records 393 max HP, 208 max mana,
  320 max movement, and 3 remaining practices. The subsequent daycare-ring
  maintenance completed safely. Dorrik is full in room 3054 at 154,657 XP,
  with no death or route abort. This proves the generic level-17-to-18 handoff,
  not the later subclass or HERO bands.
- Run 5707 then exercised the first level-18 source-ranked policy in Mirror
  Realm. Dorrik killed watchman mobile 19009 for 1,182 objective XP, then the
  adjacent second watchman drove health below the configured 27% field floor;
  the executor withdrew and returned safely rather than risking a death. The
  segment persisted both the productive kill and the one-kill recovery signal;
  Dorrik finished full at healer room 3054 with 155,694 XP. This is useful
  level-18 safety/throughput evidence, not a claim that the band is solved.
- Runs 5708-5710 then rotated through Dwarven Home and Solace without manual
  steering. Dwarven Home rejected the live non-corporeal servant and recorded
  10 incidental XP; Solace produced 525 objective XP before its configured 15%
  health floor caused a safe withdrawal. Loot liquidation completed, and Dorrik
  is recovering at healer room 3054 with 156,229 XP, no death, and no route
  abort. These routes remain useful but recovery-limited level-18 evidence.
- Runs 5711-5713 then completed daycare and reboot-priced flight maintenance
  before selecting Moria. The registered warrior target was unavailable; the
  route nevertheless returned safely after one below-band snake interruption
  worth 210 incidental XP, with the source maze and transit hazard persisted.
  Dorrik finished full at healer room 3054 with 156,469 XP and no death or maze
  failure.
- Runs 5714-5716 then completed a clean Shadow Keep no-swim route, an Ambush
  Haglik kill for 588 objective XP, and bounded loot liquidation. The brush
  closed during return and was handled by the generic named-exit recovery;
  Dorrik finished full at healer room 3054 with 157,057 XP, no death, and no
  runtime boundary. This is another executable level-18 rotation, not a claim
  that the band is solved.
- Runs 5717-5719 then completed healer return, a bounded New Ofcol jack probe,
  and a Crystal white-stag probe. The jack was below-band and skipped; Crystal
  confirmed the registered white stag absent after one incidental 110-XP
  Fewmaster Toede kill. Dorrik returned full to healer room 3054 at 157,167 XP
  with no death or runtime boundary. Incidental XP remains outside objective
  progression evidence.
- Runs 5720-5725 then completed liquidation, healer and flight maintenance,
  and a Solace representative attempt. The representative yielded 517
  objective XP, but three source-room bodyguards killed Dorrik afterward;
  Purgatory recovery, corpse recovery, equipment restoration, and healer return
  all succeeded. The death penalty made the net segment negative, reducing the
  durable total to 156,122 XP before the next maintenance checkpoint. The
  policy now records the observed kill as forensic evidence while marking the
  exact route fatal for this level and reboot; Dorrik is alive and recovered.
  This is a risk-boundary correction, not productive level-18 proof.
- Runs 5726-5728 then rotated through the Eastern Desert and Ambush without
  manual steering. The desert nomad was not confirmed; four incidental drider
  and dervish kills supplied 350 XP and their loot was liquidated safely.
  Ambush then supplied 428 objective Haglik XP plus one incidental 100-XP
  guard interruption. Dorrik returned full to healer room 3054 at 157,020 XP,
  with no further death or runtime boundary.
- Runs 5729-5733 then completed liquidation, healer and flight maintenance,
  a 1,095-XP Eastern Desert worm kill, and a bounded Shadow Keep absence probe.
  The worm route withdrew after an incidental kill left an insufficient reserve,
  returned safely, and the Shadow Keep target was absent without forced combat.
  Dorrik reached the healer at 158,115 XP, full health, and no death.
- Run 5734 exposed a generic equipment convergence defect rather than a live
  route or network failure. Three carried long swords had distinct live
  selectors (#24390, #24364, and #24362), but display-keyword matching kept
  removing and re-wearing the same instance until the 500-command budget
  stopped the segment. The checkpoint remained safe at 158,115 XP. The repair
  now preserves exact inventory selectors, resolves their source VNUMs from
  `Char.Worn`, and aborts repeated equipment states after two repeats. The
  offline core suite passes 2,195 tests; the live campaign is ready for a
  bounded retry after this repair.
- Runs 5735-5738 then completed healer return, loot liquidation, and flight
  maintenance without incident. Run 5739 live-validated the repair in the
  same Eastern Desert route: the source nomad was present but below-band and
  was not attacked; three incidental drider kills supplied 290 XP. The hunt
  completed in 166 commands, used exact selectors `#24397`, `#24399`, and
  `#24401` for its identical long swords, and returned safely. Run 5740
  liquidated the loot in 43 commands. Dorrik finished full at healer room
  3054 with 158,655 XP and no gear-loop abort. This validates finite equipment
  handling, not productive objective progress for the nomad policy.

- Runs 5741-5746 then exercised the repaired generic rotation without manual
   steering. The Eastern Desert worm probe withdrew at the configured health
   floor; Ambush Haglik supplied 383 objective XP; the next desert rotation
   was correctly abandoned without objective credit; Plains North Aruncus
   supplied 458 objective XP; and liquidation returned Dorrik full to healer
   room 3054. The six-segment batch completed with no death, runtime boundary,
   or equipment-loop abort. Dorrik is safely logged out at 159,907 XP. These
   runs add current-band throughput evidence, but level 18 is not solved and
   level 19 remains the next executable frontier.

- Runs 5748-5752 then continued the same no-steering rotation. Shadow Keep
  found both registered Undead Soldier reset rooms empty and recorded the
  bounded absence; flight maintenance completed; Ambush Haglik supplied 372
  objective XP; liquidation and healer return completed safely. Dorrik is
  full in healer room 3054 at 160,389 XP, with no death, runtime boundary, or
  equipment-loop abort. This is additional level-18 execution evidence while
  the campaign advances toward the level-19 boundary.
- Runs 5753-5760 then added Aruncus for 344 objective XP and Haglik for 498
  objective XP. The intervening Shadow Keep absence was recorded, and the
  generic executor completed liquidation, movement recovery, flight refresh,
  and safe healer logout. Dorrik finished full at healer room 3054 with
  161,341 XP, 16,309 short of level 19; no death, watchdog boundary, or
  equipment-loop abort occurred. This remains live level-18 throughput
  evidence, not proof that the band or the level-19 handoff is solved.
- Runs 5761-5771 then continued the same generic level-18 rotation. The pass
  recorded a 662-XP Haglik objective kill plus 110 incidental XP, later a
  530-XP Haglik objective kill plus 90 incidental XP, and safe liquidation
  and healer return; the other registered frontier candidates produced no
  objective kill on this pass. Dorrik finished alive at healer position with
  162,733 XP. A follow-up `return-home` segment corrected a zero-hunger
  checkpoint to hunger 40 and thirst 40 without combat. This is productive
  current-band evidence and a provisions-recovery validation, not a level-19
  or HERO completion claim.
- Runs 5772-5779 then added 409 objective XP from the Dwarven giant and 405
  objective XP from Haglik. Shadow Keep and the Crystal/Stag probes recorded
  no objective kill; flight refresh, liquidation, and healer return completed
  safely, with 90 incidental guard XP and 10 incidental drunk XP kept outside
  objective accounting. Dorrik finished alive in Midgaard at 163,647 XP with
  hunger 11 and thirst 43. This is additional level-18 throughput evidence,
  not proof of the level-19 handoff.
- Run 5780 then completed the next Crystal-family probe without an objective
  kill or runtime boundary. Dorrik remained alive at 163,647 XP in Midgaard;
  hunger declined to 6 and the next segment must therefore exercise the
  generic provisions branch before further field throughput. This is a safe
  maintenance checkpoint, not a progression claim.
- Run 5781 then completed another source-ranked Ambush circuit and killed
  Haglik for 623 objective XP without a death or runtime boundary. Dorrik
  returned alive to healer position at 164,270 XP; hunger reached zero while
  thirst remained 43. The next resume must use direct food maintenance before
  another field hunt. This is productive level-18 evidence, not a level-19 or
  HERO completion claim.
- Run 5782 then live-validated the repaired carried-provision boundary. The
  character logged in at healer room 3054 with hunger 0, issued `eat potpie`
  before leaving, rose to hunger 40, completed safe loot liquidation, and
  logged out alive at healer room 3054 with hunger 38 and thirst 41. No combat
  or XP was added; the run proves starvation recovery and safe logout ordering,
  not level-19 progression.
 - Run 5784 then reached the source-ranked Mirror Realm route and observed the
   live young-man target in room 19049. An unexpected field fight reached the
   shared 27% health floor, so the executor fled, recalled, restored recovery
   gear, healed, and logged out safely; no objective kill occurred and 78 XP was
   retained as incidental. This is route-safety evidence, not useful-band
   progression, and the policy must remain subject to the shared return gate.
- Runs 5785 through 5787 then validated the next level-18 rotation. Run 5785
  bought the current reboot's flight support at the live price and returned
  safely. Run 5786 reached source mobile 6305 in Arachnos; live GMCP identified
  the Queen Wasp at level 12 and its 100 XP kill was recorded as incidental
  below-band evidence, with the exact mobile exclusion persisted. The next
  unsteered invocation skipped that mobile and selected Haglik 4519, whose
  objective kill yielded 559 XP and returned Dorrik full to healer room 3054.
  Dorrik is now level 18 at 165,107 XP. This proves source-ranked below-band
  rotation, not level-19 completion.
- Run 5789 then selected Solace mobile 10244 and found Lord Doom present. The
  live consider result was viable, but combat reached the shared 26% hard health
  floor before a kill. The executor recalled, healed, restored combat gear, and
  logged out safely; no mob kill or objective XP was persisted. The checkpoint
  retained the exact current-reboot protection marker for this policy, with a
  14-XP partial delta, so this is protection-recovery and return evidence rather
  than a progression claim.
- Run 5790 then proved that the protection marker does not stall generic
  progression. The selector rotated to Sergeant mobile 10273 in the same Solace
  frontier, completed the objective kill for 779 XP, and returned Dorrik full to
  healer room 3054. Dorrik is now level 18 at 165,900 XP, while the Lord Doom
  marker remains preserved until that exact policy records a successful kill.
- Run 5791 then completed the next Shadow Keep rotation without a worker error or
  death. The route produced no mob kill or objective XP and returned Dorrik alive
  to healer room 3054; the Lord Doom protection marker remained unchanged. This
  is bounded route or absence evidence, not a level-19 progression claim.
- Run 5792 then completed a bounded Crystal-family probe without a worker error,
  death, mob kill, or objective XP. Dorrik returned alive to healer room 3054 and
  the exact Lord Doom hard-health-floor marker remained intact. This is route or
  absence evidence, not a level-19 progression claim.
- Run 5793 then restored productive throughput through the generic Ambush route:
  Haglik mobile 4519 yielded 488 objective XP, while an incidental fanatical
  goblin guard contributed 100 XP outside objective accounting. Dorrik returned
  full to healer room 3054 at 166,488 XP; the Lord Doom protection marker remains
  active until its exact policy records a successful kill.
- Run 5798 exposed a persistence gap in the generic level-18 frontier: the
  Goblin Caves route withdrew after a live GMCP level-band abort, lost 218 net
  XP without an objective kill, and left no consider outcome to drive the old
  protection marker. Policy revision 167 now records that exact source policy,
  reboot, level, and XP delta as durable route-loss evidence and excludes only
  that policy on the same reboot; unrelated current-band routes remain eligible.
- Run 5800 then selected the Forest route instead of replaying Goblin Caves,
  completed 108 commands, and returned Dorrik full to healer room 3054 at
  level 18 and 166,280 XP. This is live proof of exact route exclusion and safe
  rotation, not a level-19 progression claim.
- Runs 5801 through 5805 then completed liquidation, return-home, and a fresh
  Ambush rotation without worker failure or death. The Ambush run recorded one
  below-band transit guard for 100 incidental XP but no objective target kill;
  Dorrik returned full to healer room 3054 at 166,380 XP. This is safe
  non-objective progress, not level-19 evidence.
- Runs 5806 through 5810 then completed Shire, liquidation, return-home, Shadow
  Keep, and Crystal rotation without a worker error or death. Crystal run 5810
  killed Fewmaster Toede for 110 objective XP and returned Dorrik full to
  healer room 3054 at 167,108 XP. Dorrik remains level 18, 10,542 XP short of
  level 19; this is productive current-band evidence, not a level-boundary
  claim.
- Runs 5811 through 5815 then refreshed flight, completed Hood, liquidation,
  return-home, and Midgaard routing without error or death. The Midgaard route
  ended without a target kill or XP change; Dorrik returned safely to healer
  room 3054 at 167,228 XP, 10,422 short of level 19. This is bounded absence or
  no-progress evidence, not a level-boundary claim.
- Runs 5816 through 5820 then completed Ambush, liquidation, return-home,
  Dwarven route, and flight maintenance without error or death. Dwarven run
  5819 killed the giant for 417 objective XP and returned Dorrik full to healer
  room 3054; the campaign then refreshed flight and checkpointed at 167,745 XP,
  9,905 short of level 19.
- Runs 5821 through 5825 then completed Solace, Crystal, Arachnos, Shadow Keep,
  and Crystal rotation without a worker error or death. Arachnos run 5823
  killed The guardian for 1,095 objective XP; the other routes returned safely
  without objective progress. Dorrik finished full at healer room 3054 with
  169,454 XP, 8,196 short of level 19.
- Runs 5826 through 5830 then completed Solace, liquidation, Arachnos, flight
  maintenance, and a measured Arachnos repeat without error or death. Solace
  run 5826 supplied 569 XP from two confirmed kills; run 5828 added 454 XP
  from the Bird Spider, and run 5830 added 658 XP from The guardian. Dorrik
  returned full to healer room 3054 at 171,135 XP, 6,515 short of level 19.
- Runs 5831 through 5835 then completed Solace, Shadow Keep, Crystal, Arachnos,
  and Solace rotation without error or death. Solace run 5831 supplied 406 XP;
  Arachnos run 5834 supplied 894 XP, including 874 XP from The guardian; and
  run 5835 supplied 485 XP from a Secretary. Dorrik finished full at healer
  room 3054 with 172,920 XP, 4,730 short of level 19.
- Runs 5836 through 5840 then completed Shire, Arachnos, Shadow Keep, flight,
  and Crystal rotation without error or death. Shire and Crystal routes
  returned safely without objective progress; Arachnos run 5837 supplied 990
  XP, including 900 XP from The guardian. Dorrik finished full at healer room
  3054 with 173,910 XP, 3,740 short of level 19.
- Runs 5841 through 5845 then completed Forest, Dwarven, Mirror Realm, Shire,
  and Dwarven rotation without error or death. Mirror Realm run 5843 supplied
  971 XP from a watchman, and Dwarven run 5845 supplied 365 XP from a giant.
  Dorrik finished full at healer room 3054 with 175,711 XP, 1,939 short of
  level 19.
- Run 5849 live-validated the new source-ranked XP-loss ledger a second time.
  Arachnos route 6313/6367 encountered unexpected combat during its bounded
  fastwalk, withdrew safely, and lost 115 net XP without an objective kill.
  The campaign persisted the exact policy, reboot, level, and delta, then
  rotated to Solace rather than replaying Arachnos. This is route-quarantine
  evidence, not a death or level-progression claim.
- Run 5850 then completed the rotated Solace route with a 437-XP Secretary kill
  and a safe healer return. Dorrik finished full at healer room 3054 with
  176,033 XP, 1,617 short of level 19; the quarantined Arachnos policy was not
  replayed.
- Runs 5856-5858 then exercised the new exact source-ranked XP-loss ledger:
  Old Thalos withdrew at the configured health floor with -133 XP and no
  objective kill, Solace supplied 462 XP from a Secretary, and Shire returned
  safely with no target. Run 5859 crossed Dorrik to level 19 with a 733-XP
  cityguard kill; the post-level checkpoint recorded 418 max HP, 213 max mana,
  330 max movement, 3 practices, 15 damroll, and 20 hitroll at healer room
  3054. Runs 5862-5865 then recovered from one transient Windows network
  disconnect without duplicating a worker; Dwarven Home was safely empty and
  provisioning resumed on the next invocation.
- Runs 5866-5871 admitted and rotated Mirror Realm, Dwarven Home, and Plains
  North level-19 routes without manual target steering. Run 5867 killed a
  Mirror Realm watchman for 1,360 XP and returned safely. Run 5872 then
  demonstrated the current throughput boundary: the Eastern Desert worm paid
  838 objective XP, but a hidden dustdigger caused three 256-XP flee losses;
  the route returned alive with +160 net XP and its single-kill recovery gate
  sent selection to a different route. Runs 5874-5878 then continued through
  Mirror Realm and Shadow Keep; the Undead Soldier supplied 721 XP. Runs
  5880-5883 completed an Ambush guard kill for 90 objective XP, liquidated,
  returned home, and refreshed flight. Dorrik is level 19 at 180,636 XP and
  full at healer room 3054; these are live progression checkpoints, not a
  HERO completion claim.
- Runs 5884-5888 continued the level-19 rotation through Shadow Keep and
  Mirror Realm. Run 5888 withdrew at 91/418 HP after partial combat with no
  objective kill; its +201 net XP was correctly treated as non-productive and
  the hard-health recovery marker sent selection to sanctuary recovery. Run
  5889 then killed the large hobgoblin for 100 XP and returned full. Run 5890
  re-tested the Eastern Desert worm route successfully: the worm supplied 699
  objective XP, incidental driders and a drunk were kept separate, and the
  route returned at 394/418 HP after one 256-XP flee cost. Runs 5894-5898
  safely exercised the empty Shadow Keep route, an empty alternate desert
  route, liquidation, return-home, and flight refresh. Dorrik is at 182,530
  XP and the level-19 frontier remains live and unsteered.
- Runs 5899-5918 then widened the level-19 rotation without manual target
  steering. Goblin Caves returned safely with no objective kill; Mirror Realm,
  Crystal Mirror, and Shadow Keep produced bounded empty or incidental-only
  results. Solace run 5902 completed a long 386.8-second route and killed the
  Foreign Trade Representative for 692 objective XP, with +436 net XP after
  incidental costs. Dwarven run 5904 killed the giant for 996 objective XP;
  Mahntor and New Ofcol were safely empty; sanctuary recovery run 5907 killed
  the large hobgoblin for 90 XP. Dorrik finished the batch full at healer room
  3054 with 184,290 XP. The wider source audit now exposes the next candidates
  rather than treating the recent empty tail as a solved band.
- Runs 5919-5933 then validated separate current-reboot route identities and
  higher-throughput options. Eastern Desert policy 5004/5028 withdrew for
  -256 XP in run 5920 and was quarantined; the alternate 5006/5061 route then
  returned safely without an objective target. Solace run 5923 recorded only
  incidental Fewmaster Toede XP, while Arachnos runs 5924 and 5930 supplied
  130 and 877 objective XP from The Bird Spider and The guardian. Solace runs
  5926 and 5933 each completed two-Secretary sweeps for 1,752 and 1,616 XP.
  Dorrik finished full at healer room 3054 with 189,549 XP, 12,751 short of
  level 20; these are live level-19 throughput results, not a HERO claim.
- Runs 5934-5973 then extended the generic level-19 rotation through Arachnos,
  Solace, Haon Dor, Hood, Forest, Shadow Keep, Shire, and Arikasbab. Productive
  examples included the 1,555-XP Solace sweep in run 5936, the 1,072-XP Haon
  Dor kill in run 5953, a 1,329-XP Solace sweep in run 5960, a 1,285-XP
  two-Secretary sweep in run 5963, and a 722-XP Forest kill in run 5971.
  Arachnos run 5962 withdrew for -256 XP and Arikasbab run 5964 withdrew for
  -66 XP after incidental troglodyte kills; both exact source policies were
  deferred for the reboot while the selector continued with unrelated routes.
  Empty and incidental-only candidates remained safe bounded probes. Dorrik
  finished full at healer room 3054 with 197,009 XP and 6,291 XP to level 20;
  this remains live level-19 progress, not a HERO completion claim.
- Runs 5974-5996 then closed the level-19 frontier. Solace run 5974 supplied
  1,145 XP, run 5977 supplied two Secretaries for 1,374 objective XP plus an
  incidental drunk, and Old Thalos run 5978 supplied an 856-XP cityguard kill.
  Shire, Shadow Keep, Mirror Realm, and Forest also produced bounded empty or
  incidental-only results. Mirror run 5993 withdrew for -119 XP without an
  objective kill and was deferred by the exact policy ledger. Dwarven run 5994
  then crossed Dorrik to level 20 with a 437-XP giant kill. The post-level
  checkpoint is full at healer room 3054 with 203,423 XP, 444 max HP, 218 max
  mana, 340 max movement, three practices, and subclass `none`; the first
  level-20 Shadow Keep route is now live. This is an executable level-20
  checkpoint, not a HERO completion claim.
- Runs 6018-6021 then validated the next live recovery boundary. Run 6018
  stopped a Great Eastern Desert hunt at room 5029 with only 8 movement;
  run 6019 reproduced the pre-fix no-recall stall. The repaired runner waited
  through DD4's movement pulse, and run 6020 reached the legal room-5006
  tunnel boundary without dying. Run 6021 then recalled from room 5006 without
  flight, reached healer room 3054, recovered to 444/444 HP, 218/218 mana,
  and 340/340 movement, and saved and quit successfully. This proves generic
  no-recall recovery at the level-20 checkpoint; it is not a HERO completion
  claim.
- Runs 6022-6025 then resumed level-20 execution. Loot liquidation and flight
  maintenance completed safely, and run 6025 reached Solace room 10295 with
  a live perfect-match consider for the source-matched level-19 Secretary.
  Dorrik killed her for 888 objective XP, recalled at 176/444 HP, recovered
  fully in healer room 3054, and logged out at 211,328 XP. This is productive
  level-20 evidence, not a HERO completion claim.
- Runs 6026-6027 then kept the generic selector moving without forcing a bad
  target. The Solace sergeant route found a live below-band Secretary and
  skipped it with no XP change. The Great Eastern Desert route then killed the
  level-17 giant purple sand worm for 665 objective XP, returned safely from
  403/444 HP, recovered fully in healer room 3054, and logged out at 211,993
  XP. This is productive level-20 evidence, not a HERO completion claim.
- Runs 6028-6030 then completed maintenance and repeated the Solace lieutenant
  route. Run 6030 accepted the live target and supplied another 718 objective
  XP, raising Dorrik to 212,711 XP; he returned safely, recovered to 444/444
  HP, and logged out in healer room 3054. This remains executable level-20
  evidence, not a HERO completion claim.
- Runs 6031-6032 then exercised the Shadow Keep absence gate and a live
  Mirror Realm watchman engagement. The watchman reached 26 HP, but two
  critical pound attacks and bleeding reduced Dorrik to 50/444 HP; he fled,
  retained 463 damage-credit XP after the 270 XP flee loss, and recovered
  safely. Run 6033 then killed the level-17 giant purple sand worm for 616
  objective XP. Runs 6034-6035 completed loot and return-home maintenance.
  Run 6036 then killed the source-matched level-19 Secretary on the Solace
  lieutenant route for 622 objective XP. Dorrik is now at 214,142 XP, full
  and safely logged out in healer room 3054. These are productive level-20
  evidence, not a HERO completion claim.
- Runs 6037-6040 then maintained flight and funding while continuing the
  generic rotation. Run 6037 recorded the live Magic Shop stock and bought a
  light blue potion for 30 copper, confirming flight before a safe healer
  logout. Run 6038 killed the Great Eastern Desert nomad leader for 738
  objective XP; run 6039 sold its long curved sabre for 68 coins. Run 6040
  then killed the level-17 giant purple sand worm for 653 objective XP and
  returned safely. Dorrik is now at 215,533 XP, full and based in healer room
  3054. These remain productive level-20 evidence, not a HERO completion
  claim.
 - Runs 6041-6045 then completed worm loot and return-home maintenance, checked
   the absent nomad circuit without forcing a target, and left Dorrik at
   216,331 XP. Run 6046 live-validated the new source-ranked XP-loss guard:
  the worm route withdrew and cost 270 XP without an objective kill, so its
  exact level-20 policy was deferred for the reboot while unrelated routes
  remained eligible. Run 6047 exhausted the Shadow Keep undead circuit with
  no target and no XP. Run 6048 then selected the eligible Solace Secretary
   route and supplied 733 objective XP. Dorrik is now at 216,794 XP, full and
   safely logged out in healer room 3054. These remain productive level-20
   evidence, not a HERO completion claim.
 - Run 6049 then live-validated the dangerous-combat boundary on the sluggish
   Dragonhoard teller route. Dorrik reached 41/444 HP, issued the 17-percent
   flee decision, took one already queued round to 6/444 after a failed flee,
   then escaped with 289 damage XP offset by the 270-XP flee loss. He recalled,
  recovered at the healer, saved, and quit safely at 216,813 XP. The repaired
  executor now tracks target-scoped observed damage and adds one such round to
  the source critical reserve before withdrawing. This is live timing evidence,
  not a HERO completion claim.
- Runs 6050-6051 then recovered the interrupted flight-maintenance segment and
  completed a safe no-target route. Runs 6053-6054 exercised two live Mirror
  Realm circuits: one exposed a missing destination-guided GMCP exit, while
  the other reached a viable young boy that departed after repeated kick
  attacks; Dorrik lost only 16 HP and returned safely. Run 6055 reached Moria,
  separated two below-band transit kills and 360 incidental XP from the
  below-band troll objective, and returned full. Runs 6056-6059 collected
  source-backed coins, bought pies and water, repaired the food recognition
  edge case, sold a quoted scroll safely, and restored the healer checkpoint.
  Run 6060 recorded a clean Crystal target absence; run 6061 rejected a
  five-mobile Dwarven Home crowd. Run 6062 then completed two source-matched
  level-20 woman kills for 1,800 objective XP, bringing Dorrik to 218,973 XP
  at full healer recovery. These are productive level-20 evidence, not a HERO
  completion claim.

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
After the first authoritative HP loss, the executor also reserves one observed
combat round because DD4's flee command can consume a violence pulse before it
reports success. This target-scoped reserve becomes the withdrawal floor and
resets on target or combat end. Any death during a source-ranked attempt still
permanently blocks the exact policy for the current level and reboot, even when
an objective kill was recorded before the death and the net attempt lost XP.
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

Equipment identity is now treated the same way as target identity. A display
name is a useful source-catalog lookup, but it is not an object identity when
multiple live instances share that name. Exact `Char.Items` selectors, the
structured worn instance-to-VNUM acknowledgement, and a repeated-state guard
make stance maintenance finite and observable even when a field hunt returns
several identical pieces of loot.

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
