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
- Runs 1128-1129 live-validated that revision. Dorrik bought and confirmed
  flight at the current 94-copper price, then completed all three Ambush
  targets in one trip for 747 XP. She continued productively to 129/197 HP,
  stayed above the 40% withdrawal boundary, sacrificed uncarryable remains,
  and recovered safely at healer room 3054. Dorrik now has 32,639 XP and needs
  7,061 to level ten; at 391/400 carried weight, varied-armour liquidation is
  the next required work unit before another hunt.
