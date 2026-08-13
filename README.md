# dd-playtester
Automated play-testing and balance-analysis system for Dragons Domain IV.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
python -m dd4tester configure-login
python -m dd4tester run scenarios/login.yaml
```

`configure-login` asks once, without echoing the password, and stores the DD4
login in Windows Credential Manager. `run` then retrieves it automatically.
For a character profile, store its password once as well:

```powershell
python -m dd4tester configure-character-password profiles/your-character.yaml
```

The `starter`, `arena-research`, and `campaign` commands automatically use that
profile's `credential_name`. Environment variables still take precedence for
automation. Credentials are never written to YAML, SQLite, or transcripts.

Use the bounded resupply command to return an existing character from Limbo or
the Mud School arena, consume food and water, save, and log out safely:

```powershell
python -m dd4tester resupply profiles/your-character.yaml
```

To refill at the Midgaard Temple Square fountain and buy six pies from the
Bakery, use the separate bounded restock command:

```powershell
python -m dd4tester restock profiles/your-character.yaml
```

The project connects over asyncio Telnet, records transcripts, captures GMCP,
loads YAML scenarios, and stores run evidence in SQLite. Its observation layer
derives deterministic `game_event` records for rooms, prompts, health, combat,
quests, items, levels, and deaths. A state reducer turns those events into
revisioned character snapshots. The starter bot uses explicit rules only; AI
decision-making is intentionally not implemented yet.

The official recall-origin fastwalks are included as parsed, inspectable route
data. They are planning aids only until live runs verify an arrival and safe
return for a specific character:

```powershell
python -m dd4tester show-fastwalks --level 6
```

Rank low-level hunt targets from DD4's public area files before a live probe:

```powershell
python -m dd4tester show-hunt-candidates --level 6 --character Ararisa
```

The ranking starts at Midgaard recall and reports exact routes, reset-backed
loot, room placements, global mobile limits, route hazards, and kills observed
during the current DD4 reboot. Prices, repeated-kill XP, and spawn or instance
observations are not carried across the `DD was started at ...` boundary.
After looting, leave the area before recovery or liquidation so its unoccupied
reset timer can advance faster.

See [ROADMAP.md](ROADMAP.md) for the staged path from scripted scenarios to a
level-100 autonomous campaign running visibly through Mudlet in a virtual machine.
The current architecture and evidence audit is in
[docs/PROGRESS_AUDIT_2026-08-13.md](docs/PROGRESS_AUDIT_2026-08-13.md).

## Current status

The protocol, state, persistence, starter, reporting, and resumable campaign
layers are operational. The live mage/thief/warrior matrix has reached level 10
for all three representatives. Current long-running anchors are Aeloria mage
level 13 at 74,825 XP, Dorrik warrior level 16 at 123,437 XP, and Kestrel thief
level 24 at 360,704 XP. The offline suite currently passes 2,528 tests. Dorrik
crossed level 14 on run 5246 after the level-13 source-ranked frontier, and
runs 5231 through 5306 continued the generic executor without steering,
returning safely to healer room 3054 after every bounded circuit. Run 5307
then exposed an under-modeled risk: an armed Ambush Bardoosh reset passed the
ordinary peak estimate, but a critical stab killed Dorrik after two incidental
low-XP goblin interruptions. Corpse recovery through Purgatory, equipment
restoration, and healer recovery all completed correctly; the death penalty
left the durable checkpoint at 87,820 XP. Bounded post-repair runs 5308 through
5310 then selected a productive duty target, refreshed flight, completed the
ranger circuit, recovered a long bow, and returned Dorrik to healer room 3054
at 88,279 XP. Runs 5311 through 5316 then sold loot, returned home, completed
maintenance and Moria transitions, and killed a Shadow Wraith for 296 XP after
two trivial transit interruptions, returning safely at 89,572 XP. Runs 5317
through 5319 then added a 624-XP source-matched ranger kill and safe healer
return; the ranger transcript records a nonfatal carry-capacity rejection while
collecting a long bow. Runs 5320 through 5325 then handled sanctuary and Moria
prerequisites, killed a Shire receptionist for 569 XP, and recorded both Wraith
rooms absent across the following circuit. Dorrik returned safely at 91,025 XP
after incidental field kills. Runs 5329 through 5334 then added a 449-XP ranger
kill and a 349-XP receptionist kill; later Wraith absence was recorded without
forcing combat. Runs 5335 through 5337 then completed an Aruncus kill for 743
XP and safe daycare/Moria maintenance. Runs 5338 and 5339 completed two Wraith
probes safely; incidental goblins added 190 XP but were not credited as
objective kills. Runs 5344 then completed an Aruncus kill for 919 XP in 166.6
seconds with full health before and after. Runs 5345 and 5346 found the Wraith
targets absent and recorded only incidental goblins. Run 5353 then reached the
Dwarven Homestead through the Miden'nir bridge and recorded a positive nobleman
consider without attacking the target; the level-6 bridge goblin was resolved
by live mobile VNUM. Runs 5354 through 5358 reconciled the standalone probe,
restocked, and rotated past crowded or absent candidates. Run 5359 then
completed a current-band source-ranked kill for 413 XP in 141.8 seconds, with
a full healer return; run 5360 completed safe equipment maintenance. Dorrik is
was at 99,355 XP before the latest level-15 rotation. Runs 5373, 5376, 5378, and 5383 added productive current-band
kills, and run 5391 added 956 XP from a wandering Undead Soldier after the
level-15 boundary. Runs 5373, 5376, and 5378 added 332, 337, and 533 XP from
source-matched current-band targets; the selector then fixed a throughput bug
that could prefer an expired Shadow Keep absence retry over a measured
same-reboot repeat. The generic policy now models the
DD4 critical-hit reserve and withdraws before a source-verified one-hit burst
can kill, while preserving deliberate high-payoff probe paths. The
source-ranked circuit selector also compares safe multi-target circuits by
risk-adjusted source score per travel step, so a wandering high-score mobile
cannot suppress a productive fixed-reset circuit. The retry/reward rule is
covered by regression tests and the full suite passes 2,523 tests. Runs 5392
through 5401 handled a failed return, maintenance, and low-value/absent route
evidence without leaving a worker behind. Run 5402 then selected the
source-matched Bardoosh mobile (4515) in room 4514, earned 671 objective XP
and 851 XP total including three incidental 60-XP goblin interruptions, and
returned Dorrik to healer room 3054 at full health and movement. The selector
now treats explicit objective kills below 50 XP as contact evidence rather
than productive history, keys wandering kills by their tagged source identity,
and lets a fresh route displace a productive repeat only when its risk-adjusted
reward per travel step is at least 25% stronger. An aggressive requested target
is a scored risk-pool option subject to the normal source, consider, crowd,
health, protection, and return gates; it is no longer rejected solely for being
aggressive. Run 5403 then selected Aruncus the Druid (mobile 300, room 323)
and earned 505 objective XP, returning to healer room 3054 at full 322/322 HP
and 290/290 movement. Dorrik is now 13,493 XP from level 16.
Run 5405 then repeated the productive Bardoosh route for 351 objective XP and
one incidental 70-XP goblin kill, returning at full HP and 264/290 movement.
The next level-16 boundary is 13,072 XP away.
Run 5406 then repeated Aruncus for 462 objective XP, returning at full HP and
269/290 movement; Dorrik is now 12,346 XP from level 16. Run 5407 then found
the fanatical goblin guard (mobile 4516) wandering into room 4522, killed it
for 264 XP, absorbed a critical hit, and returned safely at 228/322 HP before
healer recovery. The transcript proved the exact source VNUM; the new ledger
now records such wandering kills by VNUM even when the display name differs
from the registered reset-room stop. Run 5408 then accepted the measured Bardoosh
repeat: the source target yielded 460 objective XP and a wandering goblin added
70 incidental XP. Dorrik took no death or flee, returned at full 322/322 HP and
279/290 movement, and reached 102,994 XP. The live reward supports the throughput
preference without treating survival as the only success criterion. Run 5409
then selected Aruncus for 421 XP in 69.8 seconds and returned at full HP;
run 5410 reopened the cooled Shargugh route and confirmed it was still absent.
Runs 5411 and 5412 completed required flight and provision maintenance. Run
5413 reached the live Bardoosh fight but was stopped after a zero-transcript
startup stall; SQLite events still show the 60-XP lieutenant interruption and
460-XP Bardoosh kill, and run 5414 completed healer recovery at 103,935 XP.
The interrupted run remains failed evidence until its kill metadata is
reconciled, while the new orphan-run cleanup closes both segment and run rows.
Run 5415 then confirmed both Shadow Keep Wraith rooms absent after one incidental
60-XP goblin interruption. Run 5416 deliberately reopened the fanatical guard
and earned 257 objective XP from source mobile 4516, returning at full HP and
281/290 movement. Run 5417 then live-validated write-time kill persistence: its
incidental 60-XP goblin row was visible in SQLite before the run finished. Run
5418 found Aruncus beside a non-hostile Ofcol cityguard, but watched the target
wander away while waiting on the generic crowd gate. The runner now loads
source special profiles and, after one non-hostile interval, permits a
`spec_guard` bystander only for a controlled character at alignment 300 or
higher; ambiguous profiles and lower alignment remain blocked. Run 5419 then
earned 286 objective XP from fanatical guard mobile 4516 plus 70 incidental XP,
persisted all three kills during the live run, and returned fully recovered.
Dorrik is now 10,072 XP from level 16. Confirmed objective kills also override
stale absence metadata in future segment snapshots. The policy table intentionally
keeps the registered probe marked `research`; `show-campaign` and its stored
segments are the authority for live progression evidence. An
objective-only throughput repair then excluded the 60-XP and 10-XP incidental
transit kills from runs 5420 and 5421 from resetting the no-progress streak.
Run 5425 validated the repair by selecting the measured fanatical-guard repeat,
earning 303 objective XP, and returning fully recovered at 105,161 XP. An
outbound-intercept regression now keeps a rejected source target from
corrupting the relative route segments that follow the official fastwalk. Day
Care required-loot routes keep source carriers at their registered reset room.
Kestrel remains correctly parked behind the reboot-scoped cure-critical reserve
required by his negative fame. The conversation streamer delivers both Codex
and USER records from `DEVELOPMENT_CONVERSATION.txt`; new-only operation now
blocks both repeated queue entries and old content from anywhere in the full
history re-appended under a fresh timestamp. The current reboot's Dwarven Nobleman probe was re-established,
then withdrew at the 15% combat floor without a kill; its negative result is
stored as research evidence. The route now distinguishes the source-level-seven
goblin lieutenant as a bounded below-band transit interruption from level
fourteen onward, while retaining the higher-damage horseman and wyvern as hard
hazards. Runs 5274, 5280, 5284, and 5295 added current-band XP before the
failed Bardoosh attempt; the latest campaign checkpoint is safely ready in
healer room 3054 after recovery, with the exact fatal hunt quarantined for
this level and reboot.

Runs 5447 through 5459 exposed a level-boundary throughput bug: prior-level
Shire and Wyvern rewards were correctly allowlisted by source mobile VNUM but
their regenerated level-15 policy IDs still sorted as `fresh`, behind a weak
50-XP current-level repeat. The selector now promotes those allowlisted
cross-level candidates into the productive pool. Run 5460 selected Shire
receptionist 1131, earned 401 objective XP, and returned Dorrik safely to
healer room 3054. Runs 5467 and 5468 then selected Wyvern ranger 1706 and the
receptionist back to back, earning another 283 and 317 objective XP before safe
healer returns. Dorrik is at 111,291 XP, 3,509 short of level 16.
Runs 5470 through 5488 continued the same measured Shire/Wyvern rotation while
keeping absent Shadow Keep and Haon Dor objectives separate from incidental
travel XP. Run 5493 then killed ranger 1706 for 380 objective XP and crossed
Dorrik to level 16. The safe healer checkpoint records 345 max HP, 300 max
movement, three practices, and subclass `none` at 115,129 XP.
Runs 5494 through 5496 then completed the post-level handoff. The runner kept
both below-band Fleshmonger guards out of combat, trained `shield block` and
`defense knowledge` at the Warrior guildmaster, killed Aruncus mobile 300 for
519 objective XP, and returned full to healer room 3054. Dorrik now has two
physical practices and 115,688 XP.
Run 5499 then live-validated worn-aware required-loot accounting: the worn
linen robe prevented another nanny kill, while one worn pink ice ring left
exactly one ring outstanding. The bounded maintenance run returned safely in
50 seconds without considering or attacking the nanny. Runs 5498 and 5500
added 1,107 objective XP from Bardoosh and Aruncus, leaving Dorrik full and
safely logged out at healer room 3054 with 117,035 XP.
Runs 5502, 5503, 5506, and 5507 then added 1,612 objective XP from
source-matched Bardoosh, Aruncus, ranger, and Bardoosh kills. Bounded ring and
flight maintenance ran between those field segments without suppressing XP
selection. Dorrik is now full at healer room 3054 with 118,647 XP, 14,953 from
level 17.
The source frontier now permits one tightly bounded borderline route aggressor
when its worst fuzzy level is only the useful-band fringe and both source
damage bounds remain below current max HP. Run 5512 live-validated the rule:
three below-band transit kills produced 160 incidental XP, Haglik mobile 4519
produced 622 objective XP, and the below-band prisoner and elite guard were
skipped. Dorrik returned full to healer room 3054 at 119,429 XP, 14,171 from
level 17.
Run 5515 then killed Dwarven Nobleman mobile 20504 for 963 objective XP and
returned safely. Run 5516 exposed a throughput defect after `where aruncus`
reported `Grassy plains`: the route inspected every differently named transit
room and reached its 240-second boundary. Locator narrowing now compacts those
rooms into movement-only legs, checks the seven matching rooms instead of all
42 source destinations, and can refresh from every safe origin. Run 5518 added
930 objective XP from Haglik plus 160 incidental transit XP. It also exposed
the named closed-exit response `The brush is closed`; generic named exits now
open and retry like doors and grates. The watchdog returned Dorrik safely to
healer room 3054 at 121,482 XP, 12,118 from level 17.
Run 5522 then added 619 tagged Bardoosh XP. Runs 5523 through 5525 completed
ring, flight, and food maintenance; the ring carrier supplied 20 XP. Run 5526
live-validated the locator repair: `where` reported `Path in the plains`, the
compacted route found Aruncus in room 302, earned 501 objective XP, and
returned without a runtime boundary. Run 5527 added 655 objective Haglik XP
and 160 incidental transit XP. Dorrik finished fully recovered at healer room
3054 with 123,437 XP, 10,163 from level 17.

The live DD4 checkout used for the current audit is `f2491fd`. The packaged
prerequisite and training snapshots remain pinned evidence from `f703daa`, and
the fallback character catalog is pinned to `0482387`; source-sensitive policy
changes must record both the live checkout and snapshot revisions.

The `hero` command is a resumable execution boundary, not a claim that HERO is
already solved. It checkpoints and stops when the selected class and level band
has no executable policy. `verified` policies are repeatable evidence-backed
progress; `research` policies are bounded probes; `unavailable` policies are
explicit safe stops. No fresh character has yet completed an uninterrupted
level-0-to-100 run. The active work order is now level-14-to-30 generic
progression, including training and the level-30 subclass handoff. See the
detailed [progress audit](docs/PROGRESS_AUDIT_2026-08-13.md) and the historical
[roadmap](ROADMAP.md).

## Real DD4 capture

`scenarios/capture.yaml` performs a bounded, read-only observation run against
`dragons-domain.org:8888`. It logs in, captures the room and character state,
runs `look`, `score`, `inventory`, and `equipment`, then quits:

```powershell
$env:DD4_USERNAME = "your-test-character"
$env:DD4_PASSWORD = "your-test-password"
python -m dd4tester run scenarios/capture.yaml
```

Environment-backed commands are sent to DD4 but stored as `[REDACTED]` in both
the transcript and SQLite. Sanitized real-protocol fixtures live under
`tests/fixtures/`.

## Rule-based starter bot

Create a YAML profile based on `profiles/starter.example.yaml`, then set the
profile's password environment variable and run:

```powershell
$env:DD4_CHARACTER_PASSWORD = "your-test-password"
python -m dd4tester starter profiles/starter.example.yaml
```

The profile accepts `name`, `race`, `gender`, `class`, and optional `subclass`.
Subclasses are level-30 targets in DD4; specifying only `subclass: warlock`
automatically selects its required `mage` base class at creation. Runtime,
command, attribute-roll, database, and transcript limits are also configurable.

The deterministic policy creates or resumes the character, completes both
tutorial courses and required fights, recovers with safe-room healers, loots
and equips rewards, buys food and water, practices a real class ability, reaches
level 2, saves, and quits. Every choice is stored as a `decision` event with its
stage and reason. Passwords remain redacted.

## HERO autonomy entry point

Prepare and run a durable level-100 campaign directly from a character request:

```powershell
python -m dd4tester hero-options
python -m dd4tester hero --race human --sex female --class mage
python -m dd4tester hero --name Valora --race elf --class thief --subclass ninja
python -m dd4tester hero --username Kestrel --password SECRET --race drow --class thief --subclass ninja --target-level 30
```

The command reads races, classes, and base/subclass relationships from the
current DD4 `const.c`, falling back to a packaged snapshot of a recorded source
revision. When `--name` is omitted, it generates a stable name. The request,
generated profile, and campaign configuration are stored under `runs/heroes/`
and reused on the next identical invocation. Use `--prepare-only` to validate
and inspect configuration without connecting. Sex is retained as a cosmetic
identity choice but is not a progression coverage dimension.

`--username` is an alias for `--name`. `--password` overrides the generated
profile's password environment variable for that process only and is never
written to the HERO manifest, profile, database, or transcript. Because command
arguments can remain visible in shell history and process listings, prefer the
profile's password environment variable for routine unattended runs.
`--target-level` accepts levels 2 through 100 and updates a resumed campaign's
durable target without rebuilding its character workspace.

This command uses the existing verified policy graph. It will checkpoint and
stop safely at the first level band that still lacks an executable policy;
extending verified class-aware coverage through HERO remains ongoing work.
The command is intentionally character-independent: names and credentials
identify a stored profile, while race, class, subclass, live state, and
source-backed evidence determine behavior.

## Campaign execution

`campaigns/hero.example.yaml` turns a character profile into a durable
level-100 campaign. It records a checkpoint after every verified policy segment,
resumes the same configuration by default, and applies aggregate runtime,
command, segment, and stalled-progress limits:

```powershell
python -m dd4tester campaign campaigns/hero.example.yaml
python -m dd4tester show-campaign 1
python -m dd4tester campaign campaigns/hero.example.yaml --new
```

Campaign policy selection uses a structured progression context containing the
character's data-driven archetype, capabilities, live resources, inventory,
effects, and reboot-local kill history. Character names are never behavior
selectors. See `docs/AUTONOMY_ARCHITECTURE.md` for the architectural boundary.

## Representative matrix

The first character-independent proof uses mage, thief, and warrior campaigns
with contrasting races, genders, and subclass targets:

```powershell
python -m dd4tester matrix matrices/level-10.yaml --rounds 1 --segments-per-character 1
```

The command runs campaigns round-robin, prints every character's level and
status, waits for the shared Mud School area to reset between characters, and
continues the other entries if one needs more evidence. Each
profile uses its own Windows Credential Manager key; configure the three local
passwords before a live first run without displaying them:

```powershell
python -m dd4tester configure-matrix-passwords matrices/level-10.yaml
```

## Progression Evidence

Inspect the currently registered policy for a class and level before launching a
campaign segment:

```powershell
python -m dd4tester show-policies --level 2 --class mage
```

The registry distinguishes `verified`, `research`, and `unavailable` policies.
Creation and the complete tutorial are verified. Later bands use bounded,
source-backed field policies; for example, run 1411 verifies the level-10
warrior Fleshmonger guard loop. A research route can attack only when its
policy explicitly permits bounded combat, and it is promoted only after live
XP, damage, loot, and safe-return evidence is recorded.

Combat fastwalks enable DD4's `TARGETMODE`. The runner binds the resulting
`[#number]` to a source-recognized mobile line and uses that exact live instance
for `consider`, the opener, and targeted combat spells. Selectors are ephemeral:
policies and persisted evidence continue to identify targets by reusable source
identity, and IDs are never reused across connections or reboot boundaries.

Export a compact evidence record from a bounded research run for review:

```powershell
python -m dd4tester collect-evidence 56
python -m dd4tester collect-evidence 56 --output evidence/run-56.json
```

The local `evidence/` output directory is ignored by Git. Exports omit commands,
credentials, and raw response text.

## Skill Prerequisites

The package includes a versioned snapshot of DD4's server-side prerequisite
definitions. Inspect a class skill before selecting practice targets:

```powershell
python -m dd4tester show-prereqs --class mage --skill fireball
python -m dd4tester show-prereqs --class warlock --skill dragon-shield
```

Inspect the ordered leveling analysis for any base class or level-30 subclass:

```powershell
python -m dd4tester skill-analysis --class psionic
python -m dd4tester skill-analysis --class warrior
python -m dd4tester skill-analysis --class ninja
python -m dd4tester skill-analysis --class "bounty hunter"
```

The analysis reports the class strategy, practice policy, highest-value
leveling skills, known automation gaps, target percentages, and source
prerequisites. The live planner intersects the ordered priorities with the
current trainer's `practice` listing, available physical and intellectual
practices, known percentages, prior rejections, and per-level spending limits.
It spends at most one practice of each type per level because unused physical
and intellectual practices feed the next level's hit-point and mana gains.
All automated choices for the nine base classes and all 18 subclass analyses
carry DD4 source references. Before level 30 the planner uses only base-class
priorities. Once the live state confirms a subclass, its priorities take
precedence while inherited base-class priorities remain available.

When a level-2 profile and its password environment variable are available, run
one bounded arena probe before enabling any automated level-2-to-10 policy:

```powershell
python -m dd4tester arena-research profiles/your-level-2-character.yaml
python -m dd4tester collect-evidence <run-id> --output evidence/arena-level-3.json
```

The probe targets level 3 by default, keeps the existing health retreat and
safe-exit rules, then saves and quits. It is deliberately not registered as a
campaign policy until that live evidence proves its combat, recovery, and XP
behavior.

## Run data

With the default `scenarios/login.yaml` values, running from this repository root writes:

- SQLite database: `runs/dd4tester.sqlite3`
- JSONL transcripts: `transcripts/<scenario-name>-<run-id>.jsonl`, for example `transcripts/login-1.jsonl`

The SQLite schema includes run and campaign tables:

- `runs`: one row per scenario run, including status, start/end times, scenario path, transcript path, and error text.
- `events`: one row per command, response, GMCP message, runner state, or derived
  `game_event`. Structured event payloads contain `type`, `source`, and `data`.
- `state_snapshots`: timestamped character-state revisions linked to the
  `game_event` that caused each change.
- `loot_sales`: observed item/shop payouts scoped to character and DD4 reboot.
- `mob_kills`: observed target kills and XP scoped to character and DD4 reboot.
- `campaigns`, `campaign_segments`, and `campaign_checkpoints`: durable campaign
  status, policy-segment history, and resumable character-state checkpoints.

Inspect stored runs, transcripts, and character state with:

```powershell
python -m dd4tester show-runs
python -m dd4tester show-transcript 1
python -m dd4tester show-transcript transcripts/login-1.jsonl --raw
python -m dd4tester show-state 1
python -m dd4tester show-state 1 --history
```

Create a deterministic run report from the stored events and state snapshots:

```powershell
python -m dd4tester report 1
python -m dd4tester report 1 --format json --output reports/run-1.json
python -m dd4tester report 1 --output reports/run-1.md
```

Reports cover progression, failures, health and combat signals, structured
decision categories, safety interventions, and concise first-person commentary
derived from recorded evidence. They do not make AI decisions or invent events.
The optional `reports/` directory is local output and is ignored by Git.
