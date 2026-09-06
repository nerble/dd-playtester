# Autonomy Reassessment: 2026-09-06

## Master Goal

The product goal remains a character-independent runner that accepts any
source-legal race, cosmetic sex, base class, optional subclass, name, and
personality, then creates or resumes that character and plays it to HERO 100.
Direct Telnet and GMCP are the canonical execution boundary. Mudlet and a
Windows VM are visibility and lifecycle validation layers, not a second policy
engine. AI commentary remains downstream of deterministic, replayable policy.

## Astra Findings And Changes

- The HERO entry point had a source-consistency gap: `--source` controlled
  identity validation but the campaign and StarterBot reloaded the repository
  default area directory during runtime. New HERO workspaces now persist the
  resolved area directory in `campaign.yaml` and `hero.json`; the campaign
  runner scopes all source-backed loaders to that directory, and resumes keep
  the original pin. The accepted source forms are `const.c`, its `src`
  directory, the server directory, and the area directory itself.

- The live frontier is Dorrik, a dwarf warrior at level 25, not a static
  level-31 template. After the latest bounded segment he is at checkpoint
  38105 with 380,076 XP, full in healer room 3054, with flight active. Aeloria
  is level 18 Mage, Praelarran level 20 Warrior, and Kestrel level 24 Thief;
  none has subclass or HERO proof.
- The source audit found a missing Smithy combat boundary: DD4's `hurl` is a
  repeatable between-round weapon action, but only for a worn weapon carrying
  `EGO_ITEM_CHAINED`. The registry now exposes `weaponchain` and `hurl` as
  unestimated setup/combat capabilities; the estimator and starter require a
  matching chained weapon VNUM, and campaign checkpoints preserve it. The
  current DD4 GMCP encoder omits the chained ego bit, so bounded `identify`
  text is retained as the live evidence fallback. Learned hurl proficiency
  alone never enables a command or combat budget.
- The field executor's fixed twelve-action source horizon was too rigid after
  live combat data existed. The damage-window probe now derives a larger,
  bounded action budget from observed damage and the current HP reserve. It
  still enforces the target-to-player damage trade, the explicit healer-return
  floor, and the original source horizon when no measured reserve justifies
  extension. This applies to protected and ordinary fights.
- Campaign reserve accounting now distinguishes a durable field reserve from
  DD4's active affect display. Sanctuary duration `0` means "less than an
  hour"; it remains usable by the live starter until GMCP removes it, but it
  cannot authorize a new outbound route without a positive/indefinite affect,
  trained sanctuary, or a verified carried potion.
- The live evidence pass found a second reconciliation edge: DD4 can split a
  flee-loss message and its partial combat XP across adjacent text lines while
  GMCP has already published the authoritative net XP. The observation layer
  now combines those lines before reduction, so the state reducer records one
  net delta instead of subtracting the full flee loss twice.
- The live ledger confirms the change: runs 12372-12373 recorded sanctuary
  acquisition followed by a 419-XP Ki-Rin loss; 12374 safely stopped an
  expiring-reserve route; 12375 recorded a 340-XP Secretary loss; 12376
  reacquired a purple potion for 100 required-loot XP; and 12377 consumed it
  to kill Mr. Smithy for 1,619 XP and return safely. Run 12378 found the
  known Temple Square drunk hazard and deferred flight without entering the
  shop. Run 12379 reacquired the purple reserve through Moria for 100 XP and
  returned safely. Run 12380 then tested an unprotected Secretary route: DD4
  reported 117 partial combat XP alongside a 419-XP flee loss, for an
  authoritative net of -302 XP; the route is quarantined. Run 12381 repaired
  the durable checkpoint from GMCP and reacquired the purple reserve for 100
  XP. Dorrik was then at checkpoint 38034 with 379,277 XP, full in healer room
  3054.

- Runs 12382-12389 continued the level-25 frontier. The Weeping Willow probe
  dealt only 39 damage in four rounds against a live 740-HP instance and
  withdrew with a 380-XP net loss; the route is quarantined. Sanctuary recovery
  restored the purple reserve, the Ki-Rin probe then withdrew for a 271-XP net
  loss and was quarantined, and the Donjonkeeper route correctly stopped before
  combat when no reserve remained. After one bounded reset wait, run 12389
  reacquired the purple potion for 90 XP and returned safely.
- Run 12390 killed the isolated Solace Secretary for 1,370 kill XP plus 662
  damage XP, 2,032 XP total, and returned to healer room 3054. Run 12391 found
  Mr. Smithy present but rejected the stables because two insect swarms and a
  young girl made the room crowded; no combat or XP change followed.
- Run 12392 exposed a Windows `WinError 121` socket read failure during a
  bounded Mirror Realm research probe. The runner stopped after four bounded
  connection attempts with no XP change. Run 12393 selected the required
  return-home policy, but the MUD then stopped accepting TCP connections on
  port 8888; its finite inactivity retry stopped without changing XP. Dorrik's
  latest durable checkpoint at that point was 38064 at 380,838 XP, last known
  in the Mirror Realm watchtower, alive and full. No level-26, subclass, or
  HERO proof is implied.
- Run 12394 live-validated the new recovery handoff: Dorrik returned from the
  Mirror Realm to healer room 3054 with no XP change. Runs 12395-12396 then
  completed bounded provision and quest maintenance, and run 12397 confirmed
  that the single 180-second reset wait had not been followed by a new DD4
  reboot. The durable campaign is now checkpoint 38072 at 380,838 XP, full in
  healer room 3054, awaiting the next area reset before fresh level-25 route
  selection.

- Runs 12398-12405 continued bounded provision, liquidation, and flight work.
  Runs 12406 and 12411 then exposed two distinct level-25 route failures:
  the Fleshmonger senior-guard route lost 419 XP because its level-15
  `greet_prog` companion can initiate `mpkill`, and the Arachnos Donjonkeeper
  route lost 419 XP when the reachable Guardian interrupted transit. Both
  losses are persisted and quarantined. Candidate construction now treats
  attack programs as non-trivial even below the ordinary XP floor, and applies
  the ten-level transit-risk gate to reachable aggressive wanderers as well as
  fixed-reset route mobs. The ordinary Arachnos candidate is therefore closed;
  the only exception is the separately bounded outdoor mage familiar probe.
- Run 12412 tested the next source-ranked Solace Secretary probe. The source
  route was isolated and free of hard transit hazards, but the live target was
  585 HP and the first bounded exchange produced only 95 damage against 80
  received. The starter withdrew safely, DD4 charged a 324-XP escape loss, and
  the exact policy was quarantined. This validates the live damage-window stop,
  but also shows that a low incoming source peak is not enough to authorize a
  post-loss unprotected probe. Policy revision 197 now requires the source
  player-output budget and expected incoming exchange to cover the target before
  that exception can open.
- A read-only source-catalog audit then found no fresh level-25 warrior target
  that passes both the revised exchange budget and the route-hazard gates. The
  only plain unprotected candidate is the exact quarantined Secretary policy;
  all other current-band options require sanctuary or carry a typed transit
  hazard. This is an intentional reboot/resource boundary, not a stalled
  selector.

- The straight-shifter slice closes a planner/executor mismatch.
  `sft.c:do_morph_snake` creates and equips source object VNUM 59 (fangs), but
  the source-ranked output path previously discarded the stale carried weapon
  after morph and then had no source weapon to budget. It now accepts VNUM 59
  when the live form is snake, or projects it from a normal checkpoint only
  when the starter's morph, 20% snake-form, and source mana gates are met. The
  shared capability registry reports `morph` and `snake form` as setup rather
  than direct-damage actions. This is source-backed planning coverage, not live
  shifter progression proof; damage calibration and later form selection remain
  separate gates.
- The route-risk audit found that the emergency no-sanctuary fallback was
  treating every source-aggressive transit mobile as equally dangerous. The
  selector now admits only a source-proven mobile at least ten levels below the
  character, with no attack program and only a typed non-combat special such as
  `spec_fido`; near-band, programmed, unsafe-special, and unknown-source cases
  still fail closed. Focused campaign coverage passes. This is a local safety
  classification repair and has not been live-validated or counted as level-26
  evidence.

## Next Executable Slice

Continue level-25 progression from healer room 3054 after the three route
quarantines. Do not replay the Fleshmonger companion route, ordinary Arachnos
transit, or the Solace Secretary post-loss probe. Let the source-ranked selector
rotate to a fresh candidate that passes the audited damage budget, or to a
bounded sanctuary/resource handoff. Use the same bounded segment, cleanup, and
evidence reconciliation for every attempt. The next proof gate is level 26 and
the class/trainer/subclass path; no policy selection, research result, or
checkpoint implies subclass or HERO progression.

## Verification

The source mirror remains at `6b6624fab18a8367aaaa4f4883e12f749704e7f6`.
The full offline suite passes 3,647 tests; `compileall` passes and changed
files pass `git diff --check` (excluding the intentionally append-only
conversation log). Remote pushes remain manual, and the repository's local
commit window is 9 PM with a 60-second timeout.
