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
