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
