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

## Policy Lifecycle

The selector must distinguish three states. `verified` is reusable executable
evidence. `research` is a bounded live probe with explicit route, combat,
resource, and return limits. `unavailable` is a durable safe stop explaining
what evidence or implementation is missing. A checkpoint, source catalog
entry, policy count, or research result is not a progression proof by itself.

Source identity is part of the policy key: area, mobile VNUM, reset room,
character level, and reboot identity are retained separately. Same-reboot
productive XP may carry a safe repeat across a level boundary when the source
identity is unambiguous and the normal live presence, consider, crowd, health,
equipment, and recovery gates still pass. Research candidates must not hide
such a repeat. Promotion requires objective XP, bounded damage and resource
evidence, loot or funding evidence where relevant, and a safe healer return.

Risk is evaluated per interruption, not as a blanket fear of death. On the
Dwarven Nobleman fastwalk, the source-level-seven goblin lieutenant may be
handled as incidental below-band transit combat from level fourteen onward
when the ordinary live combat, health, and crowd gates pass; the higher-damage
dark horseman and wyvern remain hard route hazards. If plain combat text
precedes GMCP, the executor waits one bounded prompt and resolves the enemy by
live mobile VNUM before accepting a below-band classification; an unresolved
identity remains a hard interruption.

## Current Proof And Debt

The live mage/thief/warrior matrix proves level 10. Representative long-running
campaigns currently anchor Aeloria at level 13 and 74,825 XP, Dorrik at level
15 and 105,161 XP, and Kestrel at level 24 and 360,704 XP. Dorrik's run 5246
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
`f2491fd`. The bundled prerequisite and training snapshots remain pinned to
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
