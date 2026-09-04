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

## Development checks

Run the full offline suite from the repository root after code or policy
changes. Use a focused file or keyword while iterating:

```powershell
python -m pytest -q
python -m pytest -q tests/test_campaign.py -k protection_recovery
python -m dd4tester --help
```

## Current Status

As of 2026-09-04, the full offline suite passes 3,410 tests, including the
terminal sanctuary-recovery, capacity-history, bounded-timeout retry,
protection-aware circuit, delayed-GMCP endpoint, source-safe locator,
armed-target combat-floor, and strict recovery-route repairs. Praelarran is a
level-19 Human Warrior at 197,920 XP, with 5,380 XP to level 20. Checkpoint
37334 is in healer room 3054 after a safe return, with full health and
movement, no active flight, and a current protection-recovery marker.

Runs 12176-12189 preserved the Shadow Grove return repair, a clean Lord Doom
kill, a source-backed sanctuary recovery, a bounded watchman withdrawal, and
rearming after a live disarm. Run 12190 then found a real Moria recovery hazard:
the required-loot search crossed source-reachable aggressive Warrior and Mage
mobiles and lost 768 XP before returning safely. The recovery planner now uses
a strict source no-combat proof for the actual deep route; when that proof is
absent it falls back to the shallow room-4064 check or stops safely, rather
than treating ordinary below-band tolerance as recovery permission. Run 12191
confirmed a 910-XP Secretary kill and run 12193 confirmed a 568-XP Dwarven
giant kill, both with safe healer returns. Run 12192 was a clean no-XP Shire
rotation. No level-20, subclass, or HERO proof is claimed.

Runtime-cap recovery is deliberately narrow: source and live safety gates still
apply, while the checkpoint is built from the current live snapshot and the
runner's terminal event. Objective kills are transient per segment; startup
repair trusts terminal events or durable mob-kill rows over a stale segment
end-state, so partial combat cannot masquerade as a confirmed kill.

Runs 12073 and 12074 reopened the previously quarantined Dwarven giant route
after a later objective kill superseded an older no-kill capacity probe. The
two exact isolated kills added 594 and 714 XP respectively; run 12075 then
completed liquidation and run 12076 added another 754 objective XP, all with
safe healer returns. Run 12072 still records the bounded city-shop hazard
from the source-backed Midgaard drunk. Run 12077 refreshed flight maintenance,
and runs 12078-12080 added 471, 497, and 596 exact objective XP through
Secretary and Dwarven giant routes. Run 12081 reached its bounded cap without a
kill; runs 12082-12083 added 554 and 372 exact Secretary XP. The sanctuary
recovery route remains terminal for the current reboot after its bounded
attempts. The reset retry found no new MUD reboot; the repaired handoff kept
the reset-aged Dwarven capacity entitlement armed through that maintenance
probe for the next field invocation. This is level-18 continuation evidence,
not level-19, subclass, or HERO proof.

Run 12034 live-validated the repaired protection-recovery fallback with a 674
XP Secretary-area result. Runs 12038, 12039, 12041, and 12043 then recorded
four more exact Secretary kills for 445, 602, 576, and 392 XP respectively,
each with a safe healer return; the positive kills cleared the protection hold.
Run 12036 acquired and observed a live flight affect. Runs 12037 and 12042
found the Queen Spider endpoint crowded, while run 12040 recorded the Moria
sanctuary carrier absent. Run 12045 exposed a legacy-checkpoint edge case where
the two-attempt counter survived but its result payload did not; startup repair
now reconstructs the terminal result. Run 12046 validated that repair by
selecting the independent Secretary route and recording a 665-XP kill with a
safe healer return. These are level-18 continuation results, not level-19,
subclass, or HERO proof.

Runs 12010-12012 exercised the current funding frontier: the Dwarven giant was
present and easy by live `consider`, the Midget was absent, and the Dwarven
servant was correctly rejected as non-corporeal after its live attack refusal;
the servant run's 170 XP came from incidental transit kills, not its target.
Runs 12013, 12015, 12018, 12020, and 12022 completed real guard kills for 480
objective XP plus incidental transit XP, with safe healer returns. Runs
12014, 12016, 12019, and 12021 liquidated the patched jerkin drops. The MUD's
bank-loan rule reduced the observed eight-coin sale to four coins received,
so the campaign remains in funding rather than claiming flight acquisition.
These are fresh level-18 continuation and safety results, not level-19,
subclass, or HERO proof.
Runs 11979-11981 then completed a clean rotation: Wyvern returned with no XP
change, Dwarven Home added 80 XP, and flight maintenance completed without a
loss. Runs 11982-11984 added 170 incidental XP from unavoidable transit kills,
1,030 objective XP from the Arachnos guardian, and no liquidation XP change;
the guardian route reached the runtime boundary after its kill. Run 11985
rearmed the primary weapon and added 30 incidental XP from a source-known
drunk, leaving all wear slots populated at checkpoint 36513. Run 11986
reselected the Arachnos route for live repair validation, but an intervening
source-known drunk and the guardian's partial damage caused a bounded
withdrawal at 50/416 HP; it added 51 net XP, no objective kill, and did not
validate the cap-after-kill repair. The intervening liquidation maintenance
completed safely. Run 11988 then killed the lemming smithy (mobile 29953) for
672 objective XP, and checkpoint 36522 preserved that kill in campaign state.
Runs 11989-11991 then added a 628-XP Secretary objective kill, clean Moria
recovery, and a 765-XP repeat Lemmings Smithy objective kill. The runtime-cap
evidence repair is covered by the offline suite but still needs a fresh live
run that both kills and reaches the controlled cap.
Runs 11992-11994 then preserved a blocked liquidation boundary, a Secretary
runtime-cap return without a kill, and a live below-band Lemmings result; all
three returned safely without new XP loss. Checkpoint 36538 is the current
level-18 rotation boundary.
Runs 11995-11997 repeated the known liquidation boundary, completed flight
maintenance, and returned through liquidation without XP change or loss. The
latest durable checkpoint is 36543; the next invocation obtained a fresh
Queen Spider field decision. Run 11998 recorded a live crowded stop at
checkpoint 36547 without XP change or loss, so the next candidate must be
independent of that crowd result.
Run 11999 completed the bounded restock route; hunger 39, thirst 47, movement
319, weapon state, and empty wear-slot checks were all healthy at checkpoint
36549. The next field decision can proceed without a provision or equipment
maintenance blocker.
Run 12000 selected the independent Essabella route but intercepted it below the
95% field-health gate, so the target was not attacked; a below-band goblin
guard supplied 110 incidental XP. The sanctuary recovery gate then remained on
its current-reboot cooldown and checkpoint 36553 stopped safely. Run 12001
exercised the automatic reset retry and exposed a live Moria pre-entry gap: the
scan named source mobile 4056, an aggressive orc one room below room 4064, but
the old allow-list did not classify it before entry. The first recall failed and
the second recall cost 232 XP; Praelarran stayed alive and returned to the
Healer at checkpoint 36556. This is a safety reproduction, not progression
proof. The source-aware scan repair is covered by the offline suite and needs a
fresh live validation before the route is trusted again. Runs 12002-12004
then completed a clean Dwarven giant check, a clean Queen Spider check, and
the expected protection-recovery unavailable checkpoint, all without XP change,
death, or additional loss. The next invocation uses the configured automatic
reset wait to obtain fresh sanctuary evidence.
Runs 11967-11968 completed level-18 training-deficit repair and flight
maintenance. Run 11969 tested the Eastern Desert giant purple sand worm
frontier and added 90 incidental XP; run 11971 tested Bardoosh and added 90
incidental XP; run 11973 completed the source-ranked Wyvern ranger objective
for 440 XP, and run 11974 liquidated successfully. These are fresh level-18
continuation results, not subclass or HERO proof.
Run 11958 live-validated a source-ranked Bird Spider objective kill (mobile
6310, room 6342) for 369 XP and returned to the Healer at the segment boundary
without adding an XP loss. This is level-17 continuation evidence, not
level-18, subclass, or HERO proof for that run.
Runs 11959-11961 live-validated the new multi-segment continuation behavior:
the blocked loot-sale attempt checkpointed, the same invocation selected an
independent Dwarven giant route, then completed the sanctuary-reserve pass.
The Dwarven and sanctuary segments added no XP, but all returned safely and
the wrapper did not stop after the recoverable shop hazard.
Runs 11934 and 11936 added 277 and 554 XP from the same independently
source-ranked Bird Spider policy. Run 11935 completed the repaired Dwarven
route without XP change or loss. Run 11937 live-validated the Moria
pre-entry scan: `scan down` ran from room 4020 before room 4064, the scan
found no warrior 4051, and the route safely acquired the purple potion after
two bounded endpoint kills. The specific hazard-blocking branch remains
research-gated until that warrior appears in a live scan.
Run 11938 added 80 XP from the Shadow Keep route, and run 11939 completed a
clean sanctuary-reserve probe without XP change. Run 11940 exposed a combat
throughput failure against the Shire Thain: sanctuary expired while the
target remained at 80 percent, producing a 73-XP loss; that source policy is
now quarantined. Runs 11941-11942 completed flight and Moria maintenance
without XP, run 11943's protected Wyvern retry added 494 XP, and runs
11945-11946 added 70 XP through source-backed funding. The character remains
alive and fully recovered; the loss history is preserved rather than hidden.
Run 11932 exposed the remaining Moria timing bug: two source-registered
warriors entered room 4064 before the endpoint hazard gate ran, costing 208 XP.
The repair now scans the immediate destination before the final entry and
recalls when that scan finds a known wandering hazard; its focused and full
offline tests pass.
Runs 11924-11925 validated the repaired frontier rotation: a crowded Queen
Spider route withdrew without an objective kill, then the Bird Spider route
completed an objective kill for 566 XP. Run 11926 refreshed flight at the
observed 104-copper price. Run 11927 correctly recorded that no independent
source-safe target remained while protection recovery was pending. Run 11928
rechecked the exact Moria sanctuary carrier after the bounded reset wait; it
was absent, so the character returned to the Healer without claiming a purple
potion or progression proof. The protection marker remains active and the
campaign is ready for the next fresh source or reboot boundary.
Run 11844 live-validated recovery from the final Mud School corpse: the bot
dropped a duplicate bracer to make room, recovered the iron key, unlocked and
opened the northern exit, reached the healer, slept, saved, and quit. This is
safe continuation evidence, not level-18, subclass, or HERO proof.
Runs 11847-11848 live-validated exact object-selector food recovery and added
180 XP. Runs 11849-11851 completed liquidation, restocking, and flight
maintenance safely. Runs 11852-11857 completed sanctuary recovery, Shadow
Keep, Bird Spider, and Queen Spider rotations, adding 1,323 XP without death;
the character ended back at healer room 3054. These are current-band
continuation results, not level-18, subclass, or HERO proof.
The following reset-aware pass waited through the bounded area-reset window,
then completed sanctuary recovery and Shadow Keep safely; a Dwarven Home
check also returned without XP. The current-reboot cooldown was respected and
the character remained at the healer between every segment.
The latest bounded funding rotation correctly distinguished food from flight
funding: one pie and a full water skin were present, but the purse held only
36 copper-equivalent against the current 90-copper flight minimum. The
source-ranked Midget attempt was absent and quarantined for this reboot rather
than replayed.
The next funding kill added 90 XP and produced two saleable drops, but its
liquidation was safely deferred after three bounded checks found the known
Midgaard drunk route hazard. The loot remains carried for a later safe shop
attempt.
The following three money-loop attempts added 190 XP in total and left the
character fully recovered. The purse is now 39 copper-equivalent, leaving a
51-copper shortfall before the current flight purchase can be attempted.
The most recent funding rotation added another 140 XP and left full combat
resources, but hunger is now 5 with one pie remaining; food recovery is the
next survival gate if the character cannot buy provisions before leaving town.
The latest funding segment added 50 XP and produced two gold, two silver, and
ten copper, bringing the purse to 230 copper-equivalent and reopening the
current flight purchase gate. Two pies are now carried.
The latest three-segment pass then added 240 XP through sanctuary recovery and
Shadow Keep, and completed a sanctuary-reserve check without XP. Praelarran
remains alive and fully recovered at healer room 3054 with two pies and 223
copper-equivalent; no flight-required route was forced during that pass.
The following pass entered the buy-flight policy but did not acquire flight:
the live Magic Shop transcript contained no purchase command because the
source-backed Midgaard drunk hazard blocked the route. The Dwarven servant
segment still added 80 XP and the character returned safely to the healer.
The next ground rotation returned safely from Shadow Keep and then reached the
current-reboot funding boundary: no source-safe money target remained, so the
campaign checkpointed instead of replaying exhausted routes. The next retry
will use the bounded area-reset wait to reopen fresh evidence.
After that reset wait, the Midget route reopened as fresh evidence and added
30 XP, bringing the purse to 235 copper-equivalent. The character is fully
recovered, but hunger is 2 with two pies, so food maintenance now takes
precedence over another field segment.
The subsequent bounded pass added 20 XP and recovered cash from a money
container, ending at 282 copper-equivalent with one pie and full resources.
The next invocation can retry the flight purchase without another funding
expedition.
The retry then observed a 104-copper flight price but correctly held the
purchase behind the three-segment blocked-shop cooldown; no source-safe
funding target remained in that reboot. The character stayed at the healer
with one pie and full combat resources while the cooldown awaits productive
ground progress.
The following reset-aware continuation waited through the configured 180-second
area-reset window, completed Moria sanctuary and Shadow Keep checks without
XP, then reopened the source-ranked Midget funding route and added 30 XP. The
latest durable checkpoint is 36124 at 149,380 XP; the purse is 2 gold, 2
silver, and 118 copper, and the blocked-shop flight cooldown has aged to two
steps. This remains continuation evidence, not level-18, subclass, or HERO
proof.
The next ordinary rotation inspected the source money container without XP,
then completed two source-ranked Midget funding kills for another 30 XP. The
latest checkpoint is 36132 at 149,410 XP, with 172 copper plus 2 gold and 2
silver; the blocked-shop cooldown is down to one step. The character remains
safe at the Healer while the flight purchase is re-evaluated.
The subsequent ordinary and reset-aware rotations produced no additional XP:
the source-ranked money container was empty, the remaining funding candidates
were exhausted, and the refreshed Moria, Shadow Keep, and funding checks all
returned safely. The latest checkpoint is 36151; the 104-copper flight price
remains observed, but the shared shop route still has one cooldown step. The
campaign is intentionally paused at the Healer until a reset supplies fresh
funding evidence.
The next reset-aware rotation restocked food, added 20 XP through the Midget
funding route, and then reached the buy-flight policy. The live `where drunk`
preflight found the shared Midgaard shop hazard, so no purchase command was
issued and the character returned safely to the Healer. The latest checkpoint
is 36160 at 149,430 XP; the observed flight price is 104 copper and the route
cooldown has reset to three steps. This is continuation and route-safety
evidence, not flight acquisition or level-18/HERO proof.
The following bounded rotation completed safely at checkpoint 36174. Moria
and funding maintenance added no XP, while the Shadow Keep route recorded a
30-XP incidental kill of the source-scripted drunk before returning to the
Healer; it did not count as an objective kill. Source analysis now records
that program as route risk, hard-rejects deterministic program attackers, and
keeps probabilistic wandering hazards visible without suppressing the entire
level frontier. This is continuation evidence only, not level-18 or HERO
proof. The full offline suite passes 3,362 tests.
Runs 11737-11743 completed the level-16 Mahn-Tor handoff, maintenance, and
Bardoosh frontier, reaching level 17 without death or XP loss. Runs 11744-11749
added 1,152 XP from Bird Spider, Bardoosh, Wyvern ranger, and Mahn-Tor routes.
Runs 11750-11752 added 370 XP from the Wyvern ranger; liquidation completed
once and then deferred after three bounded checks found the source-backed
Midgaard drunk hazard. Run 11753 exposed a delayed wield-result bug in rearm;
run 11754 live-validated the repair. Runs 11755-11757 added 1,071 XP from
Bardoosh and Bird Spider, with flight maintenance and healer returns. Runs
11758-11760 added 820 XP from Mahn-Tor and Bardoosh, with clean liquidation.
Runs 11761-11763 added 880 XP from Bird Spider and Bardoosh, with clean
liquidation. Runs 11764-11766 added 876 XP from Mahn-Tor and Bardoosh, with
clean liquidation. Runs 11767-11769 added 900 XP from Bird Spider and
Bardoosh, with clean flight maintenance and healer returns. The selector is
executing real level-17 combat rather than replaying stale research. Run 11776
correctly quarantined the Shadow Grove no-combat probe after an unexpected
combat interruption and recorded a 1,040 XP loss without death; the startup
repair now reconstructs that current-reboot hazard from segment history. Run
11779 selected the independent Bardoosh route and added 531 XP, checkpointing
cleanly at healer. Run 11780 selected the independent Wyvern ranger route and
added 336 XP; run 11781 deferred liquidation after three bounded checks found
the same source-backed drunk hazard. Run 11790 live-validated duplicate-armour
capacity relief, pie restock, and healer return; run 11792 completed
liquidation, and run 11793 added 589 XP from Bardoosh without loss. Runs
11796-11797 added 843 XP from Bird Spider and Bardoosh, with run 11798
completing liquidation. Runs 11799-11801 added 411 XP from the Shadow Keep
probe and Bardoosh, with clean liquidation. Runs 11802-11804 added 438 XP
from Bird Spider and 328 XP from the Wyvern ranger; the intervening repeat
checks returned safely without XP. Runs 11805-11808 added 904 XP from two
Wyvern ranger kills and the Shadow Keep circuit, with clean liquidation and
healer returns. Runs 11809-11814 added 298 XP from the Wyvern ranger; the
Dwarven Home check returned safely without XP. Runs 11815-11816 safely stopped
at the Bakery after exposing the remaining full-capacity edge. The capacity
releaser now recognizes source-identified equipment illegal for the current
class; run 11817 live-validated dropping and sacrificing the Warrior's long
bow, buying a pie, and returning to healer. Its 30 XP change was incidental
drunk-crossing XP, not progression credit. This remains continuation evidence,
not subclass or HERO proof. Run 11818 completed a clean Dwarven giant check;
run 11819 added 501 XP from the Wyvern ranger. Run 11820 exposed an unsafe
level-17 deep Moria transit after the carrier was absent, recorded 624 XP of
bounded flee/recall loss without death, and returned safely to the healer. The
source graph now gates that deep route and limits lower-level recovery to the
safe reset room. Runs 11821-11823 completed restock, added 440 XP from the
Wyvern ranger, and bought flight without entering the quarantined Moria route.
Runs 11824-11828 then added 494 XP from Bird Spider and 80 XP from the Eastern
Desert nomad commander; a partial Wyvern exchange in run 11825 cost 208 XP,
run 11826 rearmed the dagger, and run 11827 returned safely without XP. The
five-segment pass produced a net 497 XP from the prior anchor. This remains
continuation evidence, not subclass or HERO proof.

Campaign policy revision 189 prevents a stale positive research result from
reopening a source-ranked route after an XP loss: one loss requires a carried
sanctuary reserve, and a second loss quarantines the route for the reboot.
It also prioritizes the class-tagged warrior Mahn-Tor continuation at level 16
before generic research probes, and preserves that handoff after a generic
research miss when the required sanctuary reserve is executable. A sanctuary
resource route is now quarantined after two failed same-reboot attempts, so a
stalled recovery cannot consume the progression loop indefinitely.
Protection-recovery markers are scoped to the character level that incurred
the hard-health withdrawal. A later level retains the marker for audit but may
select a fresh current-level source candidate, preventing an old unavailable
sanctuary route from freezing the next band.
The emergency provision selector now suppresses its city-sale shortcut while
the shared shop hazard is active, keeping a foodless character in the explicit
funding loop so capacity relief and safe return happen before field travel.
The shared city-shop hazard now also blocks optional flight purchases until its
bounded cooldown clears, so flight funding cannot reopen a known unsafe shop
crossing.
No-recall recovery also resynchronizes at a known Midgaard waypoint after a
flee advances the character beyond the command cursor, preventing stale maze
commands from sending a returned character into the Cartography Store loop.
Source candidate construction now records the same aggressive-target gate in
`autonomy_rejections`; legacy capacity-only checkpoints are checked again before
they can be reused.

The read-only DD4 source mirror was refreshed to revision
`4d68421e67295cca1c04923d18273ca48a6476ce`. The source parser now preserves
the new `ACT_UNDEAD` marker in candidate inspection and checkpoints. It is
reported as metadata only because the current source uses it for inspection,
not as an autonomous combat hazard.

## Usage

Run commands from the repository root. In PowerShell, leave the virtual
environment with `deactivate`; without activation, prefix commands with
`.\.venv\Scripts\python.exe`.

Create or resume a character with the source-validated HERO entry point. A
new workspace generates and stores its first password automatically; a named
resume reads `character:<name>` from the Windows Credential Manager unless
`--password` or the matching environment variable is supplied. Select the
canonical workspace explicitly when the same character exists in validation
matrices:

```powershell
python -m dd4tester hero --username Aeloria --workspace runs/heroes/aeloria `
  --target-level 100 --segments 1 --max-segment-runtime 120
python -m dd4tester hero --username Kestrel --workspace runs/heroes/kestrel `
  --target-level 30 --segments 1 --max-segment-runtime 120
python -m dd4tester hero --name Newmage --race human --sex female `
  --class mage --personality "patient, observant, and dryly funny" `
  --prepare-only
```

Use `--password` for a one-process override. Add `--remember-password` only
when that explicit password should be saved to Windows Credential Manager for
later resumes; neither form writes credentials to generated files.

For visible execution through Mudlet, first create the shared-file bridge and
make its directory available to the Windows VM, then select the Mudlet
transport:

```powershell
python -m dd4tester mudlet-bridge --directory runs/mudlet-bridge
python -m dd4tester hero --race human --sex female --class mage `
  --transport mudlet --mudlet-directory runs/mudlet-bridge
```

Import the generated `dd4tester_bridge.lua` into the DD4 Mudlet profile. See
[`docs/mudlet-bridge.md`](docs/mudlet-bridge.md) for the shared-folder and
profile setup boundary.

For a bounded live continuation, cap each segment and disable automatic reset
waiting. Add `--reset-retries 1 --reset-wait 180` when you want one additional
attempt after an empty-area checkpoint:

```powershell
python -m dd4tester hero --username Kestrel --workspace runs/heroes/kestrel `
  --segments 1 --max-segment-runtime 180 --reset-retries 0
python -m dd4tester hero --username Kestrel --workspace runs/heroes/kestrel `
  --segments 1 --max-segment-runtime 180 --reset-retries 1 --reset-wait 180
python -m dd4tester hero --username Praelarran `
  --workspace runs/heroes/human-male-warrior-base `
  --segments 1 --max-segment-runtime 180 --reset-retries 0
```

Add `--progress` to `campaign` or `hero` when a multi-segment run should print
each bounded attempt's start and completion, checkpoint, level, and XP to
stderr while the normal final status remains on stdout.

If the frontier is blocked only by trailing no-progress history, request one
bounded rotation explicitly:

```powershell
python -m dd4tester hero --username Kestrel --workspace runs/heroes/kestrel `
  --segments 1 --max-segment-runtime 180 --retry-stalled
```

`--retry-stalled` does not pretend that an area reset occurred and does not
override live route, crowd, consider, health, resource, or protection gates.
Use `--reset-retries 1 --reset-wait 180` for the separate automatic reset-wait
path after an empty-area checkpoint.

With `--segments 1`, this permits one bounded retry after the selected segment
reports that a reset is required; without that result, the invocation does not
sleep or open a second segment.

An existing campaign target can be extended but never lowered. For example,
resuming a stored HERO campaign with `--target-level 30` leaves its target at
100; use a fresh workspace for a shorter validation run.

Use `--prepare-only` to validate and write a new durable workspace without
connecting. `--new` starts a fresh stored campaign; `--workspace` selects a
specific workspace when a name has more than one stored horizon. Use
`hero-options` to list the currently source-legal races, classes, subclasses,
and cosmetic sexes.

Inspect the deterministic decision surface before a live run:

```powershell
python -m dd4tester show-policies --class thief --level 16
python -m dd4tester show-policy-coverage --class mage --from-level 1 --to-level 30
python -m dd4tester show-prereqs --class warrior --skill disarm
python -m dd4tester skill-analysis --class mage
```

After confirming no campaign worker is still running, use `recover-runs` after
an interrupted local process. It repairs unfinished segments and reopens a
campaign that was left `running` before its next segment was created, without
altering its durable checkpoints:

```powershell
python -m dd4tester recover-runs --reason "orphaned worker reconciled"
```

Recovery respects an active campaign lease, so a live worker is left untouched
even during the brief window before its first segment is recorded.

Then use
`collect-evidence RUN_ID` to export redaction-safe JSON for a report or
external stream. `show-transcript RUN_ID --raw` prints the original JSONL;
without `--raw`, it prints a readable event view. The source-analysis commands
read the checked-in DD4 snapshot unless `--source` or `--snapshot` is supplied.

For repeated campaigns, use `campaign` for one YAML configuration or `matrix`
for round-robin rotation:

```powershell
python -m dd4tester campaign runs/heroes/aeloria/campaign.yaml --segments 1
python -m dd4tester matrix matrices/level-10.yaml --rounds 10 `
  --segments-per-character 1 --max-segment-runtime 180
```

Inspect durable evidence with `show-runs`, `show-transcript`, `show-state`,
`show-campaign`, `report`, and `campaign-report`. For example:

```powershell
python -m dd4tester show-runs --limit 20
python -m dd4tester show-transcript 10917
python -m dd4tester show-state 10917 --history
python -m dd4tester show-campaign 8
python -m dd4tester show-campaign 9
python -m dd4tester show-campaign 19
python -m dd4tester show-campaign 30
python -m dd4tester show-campaign 31
python -m dd4tester report 10917 --format markdown --output reports/run-10917.md
python -m dd4tester campaign-report 30 --format markdown --output reports/campaign-30.md
```

`report` reads one run; `campaign-report` walks every stored segment for that
campaign and can take longer when the shared SQLite ledger is large.

`show-runs` lists the newest durable run ids. Pass a run id to
`show-transcript` for the formatted event view, add `--raw` for the original
JSONL, or pass a transcript path directly. Both inspection commands accept
`--database PATH` when using a non-default SQLite file.

Each bounded live segment has its own StarterBot runtime cap. The launcher also
allows 60 seconds for local source/checkpoint setup and 45 seconds for bounded
healer-return cleanup; an inner transport timeout is kept distinct from that
outer launcher deadline. A controlled cap persists the runner's current combat-
pouch counts, so a resumed campaign cannot restore a potion already consumed in
the interrupted segment.

By default, SQLite is written to `runs/dd4tester.sqlite3`, JSONL transcripts
to `transcripts/`, generated HERO workspaces to `runs/heroes/`, and explicit
reports to the path passed with `--output`. Override the database with
`--database` on inspection commands. Use `show-sales`, `show-fastwalks`,
`show-hunt-candidates`, `show-resource-sources`, `show-prereqs`, and
`skill-analysis` for focused
operational and source-analysis views.

The project connects over asyncio Telnet, records transcripts, captures GMCP,
loads YAML scenarios, and stores run evidence in SQLite. Its observation layer
derives deterministic `game_event` records for rooms, prompts, health, combat,
quests, items, levels, and deaths. A state reducer turns those events into
revisioned character snapshots. The starter bot uses explicit rules only; it
also maintains source-verified subclass protections and can issue bounded
barbarian, vampire, and martial-artist combat actions after the level-30
handoff. Area-wide spells, forms, songs, turrets, runes, and AI decision-making
remain outside the implemented boundary.

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

When the character has a recorded live `recall list`, this command reuses its
source-known remote origins and prints the selected `recall_origin` beside
each route. Add `--all-areas --autonomous-safe-only` to inspect the late-band
frontier without including source-rejected targets:

```powershell
python -m dd4tester show-hunt-candidates --level 25 --character Praelarran `
  --all-areas --autonomous-safe-only
```

The report also includes estimated ground and flying movement costs plus a
`requires_flight` flag, making it clear whether a candidate is blocked by
travel capability or by combat and source-evidence gates.
When the selected character has durable class and skill evidence, the report
also shows `combat_readiness` and `combat_bonus`: these identify source-backed
damage, passive, control, and defensive commands already usable by that
character. The bonus is only a small target-specific ordering hint; it never
overrides live `consider`, crowd, route, health, resource, or damage-window
gates. Older or unprofiled candidates remain `unassessed`.

If a source-ranked route is longer than the current movement pool, the runner
may split it at source-audited `no_mob` rooms. It sleeps and recovers only at
those verified waypoints, then resumes the exact route; randomized rooms and
unsafe staging points remain unavailable. The complete outbound route is kept
for a bounded return, including reversed `open <direction>` commands for
source-registered closed doors.

Inspect source-backed recovery resources before changing a campaign policy:

```powershell
python -m dd4tester show-resource-sources --level 18 --effect sanctuary `
  --character Aeloria --all-areas --limit 40
python -m dd4tester show-resource-sources --level 18 --effect all `
  --all-areas --limit 80
```

The report distinguishes direct ground resets, mob-carried or equipped items,
and shop stock. Each row includes the exact object VNUM, reset room, source
level range, route, and source-derived hazards. `source-only` means the object
is present in the source but has no current-level hunt or stash candidate; it
is research evidence, not proof that the object is live or safely obtainable.
Effects include `sanctuary`, `healing` (including cure and refresh spells),
`flight` (fly or levitation), and non-poisonous direct `food`.

Generated retrieve, hoard, and kill quests use the same recorded recall
origins when their source-safe route is available. The route metadata causes
the runner to select the observed point, travel to the exact source target,
and restore default recall before healer recovery; an unobserved or unsafe
origin remains a bounded research or unavailable result.

The ranking starts at Midgaard recall and reports exact routes, reset-backed
loot, room placements, global mobile limits, route hazards, and kills observed
during the current DD4 reboot. Prices, repeated-kill XP, and spawn or instance
observations are not carried across the `DD was started at ...` boundary.
Low-band provision-funding routes are additionally limited to one source-known
route attacker; routes with several static or wandering attackers are skipped
because a no-progression money trip does not justify repeated combat risk.
Before field selection, the runner banks a carried coin hoard when DD4's
source `spec_thief` could remove more than 250 copper-equivalent, retaining
one gold as a compact working reserve. This is maintenance, not progression
evidence.
After looting, leave the area before recovery or liquidation so its unoccupied
reset timer can advance faster. Automatic campaign retries now wait 180 seconds
by default after returning home, matching DD4's documented roughly three-minute
empty-area reset interval; capped live invocations still disable reset retries
unless explicitly requested.
When flight funding is required but the reboot-local funding pool has no safe
candidate, a fed character now performs one bounded source-ranked ground
fallback when an independently source-safe no-flight target exists. The
flight-funding markers remain recorded so a later reboot can retry the purchase;
the fallback is ordinary progression, not proof that flight was acquired.
When an automatic retry is actually reached, the live runner first opens one
bounded `world-time` maintenance run, issues `time`, records the reboot marker,
and safely returns to the healer before replanning. Direct `--retry-stalled`
invocations do not claim that a reboot occurred or run this probe.
The funding reset ledger records the segment boundary as well. Startup repair
replays only post-reset funding evidence for the current reboot, while older
checkpoints without that marker are repaired by locating the first segment that
carried the reset snapshot.
Audited `spec_cast_cleric` and `spec_cast_mage` routes now share one
class-independent blindness-reserve gate: when sanctuary is the opener, the
character must carry two verified purple potions or have persisted `cure
blindness` capability. This protects warriors, clerics, thieves, and mages
alike; it is not a mage-only exception.
Moria sanctuary recovery is now source-graph gated at execution time. At the
checked-in source revision, the deep route to room 4152 is not source-safe
below level 20, so lower-level recovery inspects only the room-4064 reset and
withdraws if the carrier has wandered; the shallow stop can require one or two
exact purple potions. From level 20 onward, the deep required-loot sweep is
available to every class; mages still use the bounded invisibility readiness
gate, and every class retains the live high-health, exact-carrier, crowd, and
healer-return gates. At the current level-24 frontier, the deep probe checks
room 4064 and then follows a source-audited cross-area detour to the
large-cave-side carrier rooms, avoiding the borderline sentinel in room 4062.
The maze branch remains gated until its
poison and aggression evidence is safe for the character's level. A
current-reboot crowd or absence result defers the sweep until its bounded reset
cooldown is consumed rather than replaying the route immediately. When the
source-identified large hobgoblin is visible beside the exact below-band sickly
brown snake (mobile 4053), the sweep may confirm and fight the carrier first;
an engaged, ambiguous, or higher-band poisoner still forces the normal
recall/flee stop.
The Moria stop construction does not use the generic route-gate exception for
4053: a remote `where` result is not same-room carrier visibility, so a fixed
room-4058 poisoner is a pre-combat withdrawal rather than a target to kill.
At the registered room 4064 endpoint, source-known below-band hostiles without
an observed combat exchange trigger recall before combat when recall is legal;
once an exchange has begun, the existing bounded flee-and-return path remains
authoritative.
For the lower-level Moria required-loot stop, the predecessor room 4020 is
scanned with the exact destination direction before entering room 4064. The
scan resolves one-room mobile reports against source VNUMs, so the explicit
warrior (mobile 4051) and any other source-identified combat-capable bystander
block entry while the exact carrier remains exempt. A clear scan permits the
normal exact carrier, crowd, and combat gates to continue; an empty or delayed
scan is inconclusive and takes the same safe return path. Run 12001 reproduced
the missing-orc case live; the source-aware classification repair is covered
by the 3,380-test offline suite and awaits fresh live validation.

The public HERO command accepts `--retry-stalled` for one bounded source-frontier
rotation when only trailing no-progress history blocks selection. It never
overrides current-reboot absence, crowd, route, consider, protection, resource,
or cooldown evidence. Use `--workspace` when equal-horizon matrix copies make a
named resume intentionally ambiguous.

For a round-robin run across several resumable campaigns, use a matrix with a
bounded segment cap so an absent or crowded route yields to the next character:

```powershell
python -m dd4tester matrix matrices/level-10.yaml --rounds 10000 `
  --segments-per-character 1 --max-segment-runtime 180
```

Omitting `--max-segment-runtime` preserves the matrix's unbounded campaign
behavior. Each campaign still checkpoints independently in SQLite.

Every bounded live segment has a hard field cap and a separate cleanup window.
The starter uses a distinct controlled-cap signal so the campaign records a
ready checkpoint instead of confusing its own safe-return boundary with an
outer process timeout. Recovery and research waits are clipped at the field
deadline, and a runtime-boundary return is not progression evidence unless a
confirmed objective kill was recorded.
Connection cleanup is cancellation-aware and bounded to five seconds, so an
interrupted worker cannot remain stuck awaiting a Telnet close. Interrupted
segments are recovered through the normal run-recovery path before the next
live rotation. Each adapter read has a 200ms adapter budget and an independent
250ms hard outer bound; if an adapter blocks while reading or processing a
Telnet negotiation, the runner records `read_available_timeout`, closes the
connection, and retries at most three times before leaving a durable safe
checkpoint. Liveness measures semantic traffic (text, GMCP, or completed
negotiation), so raw Telnet keepalives cannot hide a stalled recovery wait. After
the bounded inactivity interval the runner sends one harmless `look` probe,
then closes and retries if the socket remains silent. During bounded cleanup, a
safe healer-room logout uses a five-second command-acknowledgement guard and
stops through the controlled-cap path if the socket stays silent.
After any transport close, the policy clears its authenticated/in-world state
and completes the DD4 name/password/entry handshake (or an explicit
reconnecting banner) before selecting recovery, route, or gameplay commands.

When a character has both a protection-recovery marker and negative fame,
level-21-and-higher observation-only research probes may still refresh the
frontier while sanctuary and city-service recovery are blocked; combat and
objective hunts remain protection- and reputation-gated. The runner reports an
unavailable checkpoint when the current reboot has no fresh source-safe probe
left.

See [ROADMAP.md](ROADMAP.md) for the staged path from scripted scenarios to a
level-100 autonomous campaign running visibly through Mudlet in a virtual machine.
The current architecture and evidence audit is in
[docs/PROGRESS_AUDIT_2026-08-13.md](docs/PROGRESS_AUDIT_2026-08-13.md).

## Historical status

**Live continuation (2026-09-02):** Dorrik is a level-25 dwarf warrior at
377,925 XP, safely checkpointed in healer room 3054 at checkpoint 34567. The
bounded transport and `--progress` repairs are live-validated. Run 11440
showed that a level-2 drunk could be killed for 20 incidental XP and a fresh
same-prototype drunk could arrive during the return, causing an avoidable
419-XP flee loss. The starter now permits one bounded, exact-profile,
no-special defensive kill on a recallable return square before recalling; the
focused regression suite passes. Run 11441 live-verified banking Dorrik's
33-platinum hoard. Runs 11442-11449 added four independent level-25 checks,
then exposed the Smithy route's high-health and room-specific swarm hazards;
those gates are now source-aware and offline-tested. Run 11450 safely completed
a bounded Mirror Realm wanderer search but found the gardener outside its
source-approved graph, so it added no XP. Run 11451 then reached the Mirror
Guardian corridor and killed a source-known carnivorous-grass transit attacker
for 150 incidental XP, but the old handler still returned before the Guardian.
The repaired starter now finishes that exact harmless interruption and resumes
the route once; revision 187 reopens only this current-reboot result for a
fresh bounded validation. Runs 11452-11454 found no objective at three
independent endpoints and returned safely without XP loss. Run 11455 completed
the bounded reset wait and confirmed that the MUD had not rebooted. Run 11456
revalidated the Smithy endpoint, found its source-registered poison-capable
swarm crowd, and returned safely without XP. A startup repair bug that restored
aged retry cooldowns to three has been fixed and regression-tested, so future
reset waits will actually advance the frontier. The full offline suite passes
3,317 tests. No character has reached HERO yet; this remains level-25
continuation and safety evidence, not level-100 proof.

The route-resume repair is now live-tested against an absent endpoint. The next
rotation should acquire the second sanctuary reserve or select a fresh
source-safe level-25 target; it must not replay the exhausted Smithy route.

**Live update (2026-09-02):** Vergalcoror (human mage) is safely checkpointed
at level 10 with 44,592 XP in healer room 3054. After the level-10 transition,
bounded reset-enabled and ordinary rotations continued through source-ranked
ground hunts, liquidation, and exact absence probes. The latest 12-segment
rotation added 807 XP without a failed segment, death, or XP loss after one
bounded field-reset wait. A previous
live liquidation (run 11202) exposed
the source-scripted level-2 drunk on the Temple Square crossing; healer-origin
shop routes now preflight that shared hazard with invisibility or a bounded
`where drunk` check. The flight-funding marker remains intact for later
reboots, while safe ground targets continue to earn XP. The full offline suite
passes 3,290 tests after the later protection repair. This is level-10 continuation evidence,
not subclass or HERO proof.

**Kestrel update (2026-09-02):** The closest existing character remains a
level-24 Drow Thief. A bounded fame-recovery rotation left him alive in healer
room 3054 at 334,688 XP after one cumulative 385-XP loss and a later
120-second cap. The protection/fame frontier remains quarantined; this is not
level-25 or HERO evidence.

**Live update (2026-09-01, latest):** Kestrel remains a level-24 Drow Thief at
334,938 XP in healer room 3054 (checkpoint 33309). Run 11074 live-validated
the source-audited long-route recovery: Kestrel slept at no-mob waypoints,
reached the gravedigger room, received a below-band `consider`, and returned
without combat, death, or XP loss. Run 11075 restored the food reserve; run
11076 retried Moria sanctuary recovery, found the carrier absent, and returned
safely. Aeloria remains level 18 and Serevian level 11. The current MUD reboot
marker is still `Fri Aug 14 00:15:48 2026`, so no character advanced to the
next level in this rotation. The source-ranked selector now passes the loaded
source world into movement gates, and the full offline suite passes 3,278
tests. These are continuation and safety results, not HERO proof.

**Latest Aeloria continuation (2026-09-01):** Aeloria remains a level-18
Human Mage at 165,794 XP, 11,856 XP short of level 19, safely checkpointed in
healer room 3054 at checkpoint 33030. Run 10934 added a real 433-XP Shadow Keep
kill; runs
10935-10945 completed bounded liquidation, return-home, flight, source-ranked,
and Moria recovery work without another loss or death. Run 10946 performed the
bounded `time` probe after the reset wait, found no new DD4 reboot marker, and
returned safely to the healer. The required-loot recovery code now permits one
healer restart at the next source-approved carrier location after a pre-combat
below-band interruption; no live run has triggered that exact branch yet. This
is safe research and continuation evidence, not level-19, level-30, subclass,
or HERO proof. The current reboot remains `Fri Aug 14 00:15:48 2026`; the full
offline suite passes 3,268 tests.

**Live update (2026-09-01, latest):** Kestrel remains level 24 at 334,938 XP
with 31,162 XP to level 25, safely in healer room 3054 at checkpoint 33287.
Run 11061 validated the fame damage-window probe against the Mirror Realm
moose: it counted the opening attack, measured only 30 of 949 target HP, and
withdrew safely after the resulting 385-XP loss. Runs 11062-11065 completed
bounded Moria reserve, food, sanctuary, and return-home maintenance; no purple
reserve was recovered. The reserve selector now rejects a carrier whose source
reset can load more than two same-prototype mobiles. Run 11066 selected the
source-legal two-capacity Moria orc carrier, found its cure-critical potion
absent this reboot, and returned without combat, loss, or death. Negative fame,
protection recovery, and reserve boundaries remain active. This is level-24
research evidence, not level-25, subclass, or HERO proof. The campaign suite
passes 1,058 tests, the starter suite passes 1,221, and the full offline suite
passes 3,272 tests. Fame recovery now admits a clean, unarmed, source-ranked
candidate without sanctuary when both its raw peak-round and critical-hit
bounds are below current maximum HP; it still requires exact targeting,
isolation, live consider, and the bounded damage-window probe. The current
Kestrel frontier has no executable candidate under those gates: Sosivia's
ground route costs 456 movement against 380 available, and flight-required
alternatives remain unavailable or source-hazardous. No live progression claim
is made for this new branch.

**Historical Praelarran continuation (2026-09-01):** Praelarran was a level-15
Human Warrior at 106,709 XP, with 8,091 XP to level 16, safely checkpointed in
healer room 3054 at checkpoint 33028. Runs 10947-10949 completed bounded flight
and source-ranked
endpoint checks without progression or death. Run 10950 retried the Moria
sanctuary route after its bounded reset wait; the carrier was absent at room
4064 and source mobile 4056, a wandering orc, engaged before endpoint
confirmation. The bot followed the authoritative post-engagement flee rule,
lost 167 XP, recalled, and recovered safely. This is live safety evidence, not
level-16, subclass, or HERO proof. Campaign 30 is ready for a fresh source
frontier result; the reboot remains `Fri Aug 14 00:15:48 2026`.

**Earlier live update (2026-08-31):** Praelarran is level 15 at 106,876 XP in healer
room 3054 at the latest checkpoint 32926, with 7,924 XP to level 16. Run 10915
rotated to the independent Haon Dor Shargugh route, encountered one
source-known below-band brown bear in transit, earned 80 incidental XP, then
aborted and quarantined the route safely. Run 10916 checked the next
Wyvern-area endpoint and found its exact target absent. Run 10917 checked all
three configured centaur endpoint rooms (1711, 1714, and 1715), found the exact
elder centaur absent at each, and returned without combat. No loss or death
occurred; no current sanctuary reserve is available and the protection marker
remains active. The reset-aware retry then ran 10918, reopened the
source-verified Moria sanctuary route, found its exact carrier absent, and
returned safely without XP change, loss, or death. Run 10919 retried the
source-registered room-4064 circuit, found the carrier absent again, and
recorded one unavoidable below-band warrior for 80 incidental XP before a safe
return. Run 10920 checked one source-ranked centaur endpoint and found it absent;
run 10921 completed the three-room centaur absence sweep without combat or XP
change. Run 10922 then completed the reset-aware Moria retry: the exact
sanctuary carrier was absent at room 4064, so the character recalled and quit
safely with no combat, loss, or death. No objective kill occurred. The full
offline suite passes 3,197 tests. Campaign 30 is ready for the next
reboot-aware retry; this is level-15 continuation and level-16 research-handoff
evidence, not level-16, level-30, subclass, or HERO proof.
The registry now includes research-status
`mahntor-rock-toad-warrior-circuit-16-18` and its level-19-to-20 continuation
`mahntor-rock-toad-warrior-circuit-19-20`. The first is selected only for
warriors with prior class-tagged Mahn-Tor progress; the later policy is selected
only after a positive level-16-to-18 result. Both preserve the source mobile,
peak-damage, live-consider, crowd, and healer-return gates. Run 10906 was level
15 and run 10922 found the required carrier absent, so fresh combat evidence is
still required for both bands.
Earlier level-15 evidence remains recorded below. Runs 10847-10848 safely exercised the repaired
source-ranked timeout rotation. Runs 10849-10850 completed bounded funding
maintenance, but run 10851 exposed a safety failure: the low-band Haon route
admitted several source-reachable wandering attackers and cost 985 XP before
the character returned safely. The selector now rejects low-band funding routes
with multiple reachable route attackers; that branch is offline-verified and
awaits a fresh route-specific live validation. Run 10852 selected Katrina the
Shepherd through the repaired funding selector, recorded 50 XP, and returned
safely to the healer without loss or death. Run 10853 then performed the
bounded Wyvern capacity probe: the source-registered centaur guard was absent,
so the runner returned without combat, XP change, loss, or death. Run 10854 then
retried Moria sanctuary recovery after its bounded reset wait; the carrier was
absent and two source-registered orcs reached room 4064 before target
confirmation. The old path fled and cost 167 XP, but returned safely. The new
source-reset endpoint preflight now recalls before an unstarted exchange; this
repair is offline-verified and awaits a fresh Moria live validation. Run 10855
selected the source-ranked Haon Dor Shargugh endpoint, confirmed its absence
with `where`, and returned safely without combat or further XP loss. Run 10856
then completed a source-ranked centaur route with all three candidate rooms
absent and no combat. Runs 10839-10841
completed the preceding sanctuary-recovery, Magic Shop, and Wyvern checks
without combat. Kestrel is
level 24 at 336,894 XP in healer room 3054 at checkpoint 32748. Runs 10817-10818
acquired and tested the source-backed Moria sanctuary reserve and Mirror Realm
research route without loss. Run 10819 reached the source Beast, which returned
the mixed response "looks like an easy kill" plus "built like a tank"; the old
parser entered combat, withdrew safely, and paid one 385-XP recall loss. The
checkpoint briefly double-counted that textual loss when the same response also
contained the authoritative GMCP Worth packet. The parser now rejects that
unsupported durability warning for source-ranked targets without a source peak
bound, and the state reducer reconciles either packet ordering. Run 10820
re-read the authoritative Worth snapshot and repaired the durable checkpoint;
Kestrel is full at the current checkpoint after that correction. Run 10821
then killed the source large hobgoblin for 110 XP and returned safely with a
purple reserve. Runs 10822-10823 completed cure-critical and venison-reserve
maintenance without combat or XP change. The Moria locator sweep remains
offline-verified and awaits a fresh carrier-bearing live result. Run 10824
then found the exact Mirror Realm target absent and returned safely without XP
change. Run 10825 then reached the Circus ticket clerk, which returned the
source-expected six-to-nine-level response plus the explicit "built like a
tank" durability warning. The new source-ranked consider gate refused combat,
recorded a bounded retryable result, and returned Kestrel safely to the healer
with no XP change. Run 10842 then reached the Mirror Realm moose, rejected its
source-confirmed "built like a tank" response before combat, and returned safely
without XP change. Run 10843 attempted the light-blue flight-potion purchase;
the Magic Shop refused service because of negative fame, and the runner
returned without pretending flight was acquired. Run 10844 performed the
bounded `time` probe and found no new MUD
reboot marker, so the campaign remains safely parked. Serevian then completed
bounded funding rotations: run 10826
inspected the Midget endpoint without a kill, run 10830 killed Uburz for 50 XP,
and runs 10833 and 10836 killed Ushog for 123 and 146 XP after unavoidable
10-XP Olog transit encounters. Runs 10831, 10834, and 10837 liquidated the
resulting gear; the rotations returned safely with no loss or death. Run 10813
recorded one unavoidable, source-known below-band rabbit
transit encounter, quarantined that route, and added 150 incidental XP without
an objective kill. Aeloria is level 18 at 165,361 XP at checkpoint 32481 after
bounded sanctuary recovery (run 10804), and Serevian is level 11 at 49,938 XP
at checkpoint 32571 after the productive funding rotations. Its next funding
candidate is unavailable for the current reboot, so the campaign is parked
safely at the healer. Vergalcoror is level 8 at 30,800 XP in healer room 3054
at checkpoint 32594; runs 10827-10829 completed safe liquidation, return-home,
and a Circus route without loss or death, while run 10845 reached the Daycare
ring and withdrew before the exact target because the old wrinkled nanny was a
source-registered endpoint hazard. The current MUD reboot is still
`Fri Aug 14 00:15:48 2026`; the source mirror is clean at `7996722`, and the
full offline suite passes 3,195 tests. Run 10893's source-backed gas-breath
result is now a research boundary: sanctuary does not neutralize its
poison-backed nausea, so `spec_breath_gas` and random `spec_breath_any` are
excluded from autonomous-safe selection.
The quiet healer-sleep movement check is bounded by a 30-second score probe,
with offline regression coverage. These are continuation and safety results,
not level-30, subclass, or HERO proof. Use `show-runs`, `show-state`, and
`show-transcript` with run `10930` (or another latest id above) to inspect the
durable evidence, including the reset-aware Moria retry.
Campaign 8 is ready at checkpoint 32748; its next policy selection is deferred
to the next bounded invocation. The selector keeps this level-24 thief on the
source-registered fame-recovery rotation while its one verified purple reserve
is available. Run 10842 added independent Mirror Realm evidence by refusing
the tank-like moose before combat; run 10843 confirmed that negative fame still
blocks the Magic Shop and did not acquire flight. Run 10844 found no new reboot marker, so the
reboot-local cure-critical boundary remains authoritative. Runs 10819, 10825,
and 10842 make the durability warning a permanent source-ranked pre-combat
gate unless a policy supplies an explicit source peak-damage bound.
Campaign 9 remains ready at checkpoint 32546 for its next bounded mage segment.
Campaign 19 is the current catalog-smoke workspace for Vergalcoror and is ready
at checkpoint 32594 after the Daycare endpoint hazard in run 10845.
Runs 10863-10898 are the latest durable continuation evidence: the reset-aware
sanctuary retry added 320 XP, the source-ranked ranger added 508 XP, run 10875
added 60 incidental XP while exercising the plain below-band exception, and
the Shargugh, wraith, centaur, flight, return-home, and Moria endpoint checks
returned safely when their exact targets or carrier were absent. Run 10868
recorded a 167-XP Moria withdrawal loss before the repair; run 10869 was
operator-stopped and recovered without replaying its transcript. Campaign 30
is checkpointed at 32809 after the bounded Moria searches and reset-aware
retry.
Run 10877 had no source-verified purple reserve, run 10887 recovered one, and
run 10893 consumed it during the poison withdrawal, so the
protection-recovery marker and route quarantine remain authoritative. Runs
10879-10881 found their exact endpoints or carrier absent and returned safely.
Run 10882 exercised the first bounded low-peak ordinary recovery fallback at Shadow
Keep, found the exact wraith absent, and returned safely without combat or XP
change. Run 10883 used the next distinct fallback probe, killed Sir Durok for
449 objective XP, and was reconciled after the launcher expired during bounded
logout cleanup; run 10884 then liquidated the recovered gear. The protection
marker remains recorded, and the sanctuary route is cooling after its reserve
was consumed; the fallback's
three-probe and failed-exchange limits remain authoritative. Run 10886's
negative `consider` result is reboot-scoped and prevents blind re-entry. The exact plain
below-band exception has live support and 2,213-test starter/campaign
coverage; runs 10885-10886 completed safe healer return and consideration with
no XP change after the recovered kill. Runs 10887-10888 then completed
sanctuary recovery and healer return for 338 XP without loss or death. Runs
10889-10892 rotated through absent endpoints, flight purchase, and one
quarantined incidental transit kill. Run 10893 exposed the gas-breath poison
boundary described above; its 167-XP withdrawal returned safely but consumed
the purple reserve. Its history
also retains run 10851's funding-route loss and run 10854's earlier Moria
withdrawal. This is continuation evidence rather than level-30, subclass, or
HERO proof.

DD4 area prototype costs are not live sale prices for mob loot. `E`/`G` resets
call `create_object`, which derives a positive runtime cost even when the
prototype cost is zero; the source formula has a ten-copper minimum. The
funding selector models that dynamic mob-loot floor while still rejecting
zero-cost ground `O`/`I` resets and ambiguous duplicate-name matches.

The subclass combat adapter selects only source-verified capabilities that are
already known in the live practice listing. It maintains `bark skin`, `mental
barrier`, and `displacement`; repeats direct spells such as `harm`, `wither`,
`flamestrike`, and `agitation`; and uses bounded `berserk`, `suck`, `atemi`,
and `kansetsu` actions where the subclass permits them. Berserk is one-use per
target and targeted actions use the existing between-round cooldown. Area,
corpse/object, form, song, turret, rune, and opener-only abilities remain
separately gated. The subclass adapter remains covered by the full offline
suite.

Source special audits are level-aware. `spec_cast_druid` is eligible only
before its source level-15 fear branch, while `spec_cast_psionicist` is eligible
only before its source level-14 energy-drain branch. The `spec_demon` profile
now mirrors its source spell gates through level 50, including curse, energy
drain, hold, hex, and fire breath; it remains research-only because those
combat and escape effects are not yet executable. Higher-level variants stay
research-only until their recovery and object-loss behavior is executable.
The source audit also keeps `spec_breath_gas` and `spec_breath_any` research-
gated: DD4's gas branch can apply poison-backed `nausea` after combat starts,
and sanctuary does not cure it. `spec_breath_lightning` remains a separate
source-bounded path and still follows the existing sanctuary and health gates.

Bounded funding output names the exact source target result, and current
protection evidence cannot be obscured by an unrelated crowd wait. Verified
combat-pouch sanctuary reserves are now passed into policy selection, so a
fresh recovery run is not repeated unnecessarily. Ordinary field hunts finish
one unavoidable source-known below-band transit fight and then return, even
when several such attackers arrive together; the runner never adopts a second
incidental target. Funding and required-loot policies retain their explicit
acquisition exceptions.

When a distant class-trainer route is interrupted by that bounded transit
hazard, the starter records a `training_deferred` event and does not retrace the
route in the same segment. Campaign state scopes the deferral by level, reboot,
and source revision, so it remains an explicit progression trade-off rather
than silently treating unperformed training as completed forever.

Startup repair also reconstructs accepted training capabilities from a bounded
event-ledger history for legacy checkpoints, then supplies those capabilities
to the resumed StarterPolicy before field decisions, so reconnecting does not
discard skills learned before those fields were persisted.

### Historical continuation detail

Runs 9478-9479 created
Serevian, a fresh human male thief, through live creation and recovery. Runs
9515-9519 completed bounded maintenance without loss or death. Run 9520 then
killed six Mud School opponents for 444 XP. Run 9521 added 216 XP through five
more source-ranked kills, and run 9522 added 336 XP through three more. Runs
9524-9526 added another 679 XP through the same source-ranked arena route;
run 9527 completed return-home maintenance, and run 9528 added 205 XP. Runs
9529, 9531, 9534-9535, and 9537-9538 added 1,230 XP; runs 9530, 9533, 9536,
and 9539 were safe maintenance or reset-boundary checkpoints. Run 9540 added
189 XP and crossed Serevian to level 5. Runs 9541-9543 completed level-5 setup
and handoff maintenance, run 9544 added 265 XP, run 9545 recorded an empty
arena and one bounded reset wait, and run 9546 completed return-home cleanup.
Serevian is safely level 5 at 10,436 XP and checkpoint 28829, with maximum
health 99 and mana 127. Runs 9547-9548 and 9550 added 564 XP; run 9549 was
maintenance, runs 9552-9554 added 525 XP, run 9555 was maintenance, and run
9556 added 157 XP. Run 9557 recorded another empty arena and bounded reset
wait; run 9558 then added 122 XP. Serevian is now level 5 at 11,804 XP and
checkpoint 28848. Subsequent bounded Serevian runs added 2,365 XP, with safe
maintenance and reset-wait checkpoints interleaved. Run 9589 crossed him to
level 6 at 14,169 XP and checkpoint 28896, raising maximum health to 113 and
mana to 134. Runs 9590-9613 then completed bounded level-6 outfit, recovery,
and source-ranked rotations; productive Circus and other routes added 955 XP,
while empty or absent candidates stopped safely. Run 9613 left Serevian at
15,124 XP and checkpoint 28948, full in healer room 3054. Runs 9614 and 9615
then safely tested another Circus route and the Dwarven Daycare route without
forcing combat; the latest Serevian checkpoint is 28948. Praelarran run 9598
added 502 XP through the Fleshmonger route, and runs 9626-9628 added another
450 XP through the current-band pool. His latest pre-repair field checkpoint
was 29331. Runs 9798-9802 then completed bounded sanctuary, secretary,
Shadow Keep, crowd, and Ambush continuations without death or XP loss; run
9799 killed source mobile 3142 for 269 objective XP and run 9802 killed source
mobile 4512 for 338 objective XP. Praelarran is safely level 14 at 94,450 XP
in healer room 3054 at checkpoint 29475, 3,650 XP short of level 15.
Runs 9681-9682 crossed level 14 and completed liquidation. Run 9686 exposed a
text-only `The Temple Square` room header without a GMCP VNUM; the runner
cleared stale identity and aborted safely. `StarterPolicy` now resolves unique
source-backed Midgaard room names when GMCP omits the VNUM. Run 9687 crossed
the repaired transition but paid a 148-XP health-floor withdrawal; run 9689
then completed a clean 288-XP archer route. Runs 9690-9692 then added 665 XP
through Haon, Shadow Keep, and Plains North with no loss or death; the campaign
is ready at the next source-ranked boundary. Runs 9699-9701 then added 80 XP
through Haon, Shadow Keep, and Midgaard without loss or death; the campaign is
ready again at the next source-ranked boundary. Runs 9702-9704 then added 601 XP
through Shire, Shadow Keep, and Fleshmonger without loss or death. Runs 9705-9707 then
completed liquidation, return-home, and sanctuary recovery without changing XP or
recording loss or death. Runs 9708-9710 then added 411 XP through Shire, Haon,
and Shadow Keep without loss or death. Runs 9711-9713 then added 607 XP through
Shire and Shadow Keep and completed provision restock without loss or death.
Runs 9714-9716 then added 271 XP through Fleshmonger and completed safe return
and liquidation. Runs 9717-9719 then added 130 incidental XP without a
source-objective kill and completed safe healer recovery. Runs 9720-9722 then
added 620 XP, including a source-objective Shire kill, without loss or death.
Runs 9723-9725 then added 316 XP through Shire and completed Fleshmonger and
Dwarven Daycare segments without loss or death. Runs 9726-9728 then added 378
XP, including a source-objective Shire kill and safe sanctuary recovery. Runs
9729-9734 then added 496 XP; run 9733 killed source mobile 4512, The vile
goblin, for 346 objective XP, with the remainder incidental transit XP.
Praelarran is alive and loss-free in healer room 3054 with no stalled segment
or orphan worker. Runs 9735-9740 then added 437 XP; run 9736 killed source
mobile 4512 for 50 objective XP, run 9737 killed source mobile 139, Sir Durok
of EAT, for 377 objective XP, and run 9735's 10 XP drunk was incidental. Runs
9741-9746 then added 1,047 XP; run 9741 killed source mobile 4512 for 307
objective XP, run 9743 killed source mobile 139, Sir Durok of EAT, for 396
objective XP, and run 9744 killed the goblin lieutenant incidentally for 80 XP
and source mobile 4512 for 264 objective XP. Runs 9747-9752 then added 1,079
XP; run 9748 killed source mobile 139, Sir Durok of EAT, for 431 objective XP,
run 9750 killed source mobile 4512 for 50 objective XP, and run 9751 killed
source mobile 139 for 488 objective XP, with 110 incidental XP alongside them.
Run 9757 then reproduced a Gremlin Lair recall-recovery hazard: the first
recall reached Temple room 3001, but stale GMCP identity caused the following
inferred text room event to be discarded and a second recall cost 148 XP. No
death or objective kill was recorded. Campaign revision 174 now accepts the
authoritative room transition and persists this exact route as a retryable
current-reboot hazard. Run 9758 converted the failed checkpoint during startup
migration and completed safe return-home. Runs 9759-9788 then added 1,507
objective XP across five source-matched kills, plus bounded incidental combat
and safe maintenance. Run 9787 reached the 120-second field cap and recovered
cleanly; run 9790 then recorded a 148-XP Gizmo-route recall loss without a
death or objective kill, and run 9791 restored full healer state. Runs 9792 and
9795 then recorded separate -148 XP losses on the Fleshmonger and Moria routes;
their one-loss quarantines held, and run 9797 completed flight maintenance.
Runs 9798-9802 then exercised bounded sanctuary recovery and source-ranked
fallback rotation: Moria's carrier was absent, the secretary yielded 269
objective XP, Shadow Keep was absent after 170 incidental wandering-goblin XP,
a crowded secretary repeat was skipped, and the vile goblin yielded 338
objective XP after live consider passed. The selector now prefers a recent
productive route over a fresh low-fuzz candidate; the focused campaign module
passes 932 tests and the full offline suite passes 3,013 tests. Praelarran is
now 3,650 XP short of level 15. This is level-14 continuation and repair evidence, not level-15,
subclass, or HERO proof. The full offline suite passes
3,013 tests. The public HERO credential boundary still permits an untouched
`--prepare-only` workspace to generate its first stored password, while any
workspace with a recorded campaign remains strict about missing credentials.
The longer narrative below retains earlier checkpoints as historical evidence.

The protocol, state, persistence, starter, reporting, and resumable campaign
layers are operational. The representative mage/thief/warrior matrix has
reached level 10 for all three characters, but no character has yet been proven
from fresh creation to HERO. Current anchors are Aeloria human mage level 18 at
165,613 XP (checkpoint 27725 after runs 9109-9111; 12,037 XP to level 19), Dorrik
warrior level 24 at 363,190 XP (checkpoint 27807 after runs 9141-9142),
Kestrel thief level 24 at 336,913 XP (26810), and Praelarran human warrior
level 13 at 74,127 XP (checkpoint 28726; level-13 warrior continuation active
at the source-ranked frontier handoff).
Corararfen remains human cleric level 6 at 17,020 XP (checkpoint 27756), Velnor level 6
at 15,255 XP (checkpoint 27762 after runs 9124-9125; cure light trained), and
Fenanallor human ranger level 4 at 7,771 XP (checkpoint 27767 after runs
9128-9129; shoot trained). All active campaigns are safely checkpointed in
healer room 3054.

Runs 9109-9110 requested a live Suturb retrieve quest and exposed a gap in the
non-kill quest route: the raw shortest path entered Old Marsh room 8310, where
source mobile 8306, an aggressive level-12 huge hairy beast, attacked. Aeloria
fled at 193/218 HP and lost 232 XP, with no death; she recovered in healer room
3054. The quest preflight and executor now share a source-safe route gate for
retrieve, object, and hoard targets. Real source validation rejects room 8310
for level 18, and the full offline suite passes 2,994 tests. Direct live proof
of the repaired quest route awaits the next generated non-kill quest. Run 9041
Runs 9112-9113 completed Dorrik's provision-funding loop without XP change,
death, or loss. Runs 9114-9120 added 1,304 XP to Praelarran through four
source-matched warrior kills, with no loss or death. Runs 9121-9123 completed
Corararfen's outfit, return-home, and
daycare-ring recovery maintenance without a field loss. Runs 9124-9125 added
109 XP to Velnor through a source-matched Sorbus kill and trained cure light;
the later fanatic route was absent. Runs 9128-9129 completed Fenanallor's ranger
starter/Mud School boundary, added 227 XP from two boars and two wolves, and
trained shoot. Run 9130 advanced Praelarran from level 8 to 9 through a 192-XP
Illusionist kill, recovering a shimmering key and 21 maximum HP without loss or
death. Run 9132 then added 835 XP from three source-matched level-9 kills,
recovered a disarmed broadsword and 14 items, and trained enhanced damage plus
unarmed combat knowledge for stun. Run 9137 then added 681 XP from the on-duty
guard and cook, recovered eight items including a rearmed broadsword, and
returned safely without loss or death. Runs 9141-9142 then added 200 XP to Dorrik
from the large hobgoblin and blonde dwarf, recovered a purple sanctuary potion,
and used it on the second route; he returned full without loss or death. Run
9147 then added 494 XP from two more guard/cook kills, recovered ten items and
a disarmed broadsword, and returned full without loss or death. Run 9153 then
added 485 XP from a source-matched on-duty guard and cook after a trivial drunk
contact, recovered seven items, and returned Praelarran full to the healer.
Runs 9154-9155 sold the recovered loot and completed bounded return-home
maintenance without another field attempt. His campaign now displays as
`Praelarran to HERO` in both YAML and SQLite; the resume migration preserved
Campaign 30 and its checkpoint rather than creating a duplicate.
Runs 9156 and 9158-9159 then added 1,367 XP through armed-guard, bull, and
guard/cook kills; run 9157 recorded a safe Moria absence. Runs 9160-9161
completed return-home and Plains North/Sorbus absence maintenance. Runs
9162-9169 added a further 1,023 XP through a Shire bull and three guard/cook
rotations, with no death or XP loss. Run 9187 then crossed Praelarran from
level 9 to 10 with 519 XP and 23 maximum HP. Run 9191 visited the level-10
warrior trainer, read the guildmaster plan, trained enhanced damage to 44%,
and added 640 XP from the patrolling guard and cook's boy after recovering a
disarmed broadsword. Runs 9194-9195 then trained enhanced damage to 49% and
unarmed combat knowledge to 41% toward the source-backed stun prerequisite.
Runs 9198-9218 added 4,456 XP through source-matched warrior kills and safe
Moria, Shire, and Circus rotations; run 9219 sold recovered loot, and runs
9220-9221 recorded clean target absences. Run 9222 then killed the patrolling
guard, on-duty guard, and cook for 828 XP, recovered a disarmed broadsword and
13 items, and returned safely. Run 9225 then killed an armed guard for 176 XP
and recorded body-part food handling; run 9226 killed the patrolling guard,
on-duty guard, and cook for 966 XP and recovered 13 items. Run 9227 sold the
loot, while runs 9228-9229 recorded clean Cult absences. Praelarran is safely
checkpointed at level 10 with 46,870 XP and no loss or death; this is
representative level-10 class/training evidence, not subclass or HERO proof.
Run 9239 then crossed Praelarran from level 10 to 11 with 771 XP from two
source-matched guard kills and 22 maximum HP, returning safely without loss or
death. Runs 9242-9243 continued the warrior trainer route, raising enhanced
damage to 53%; run 9244 added 507 XP and trained unarmed combat knowledge to
47% toward the 60% stun gateway. Runs 9247-9249 included a clean Circus probe,
flight maintenance, and a further 255-XP small-troll kill. Run 9250 then added
582 XP from two source-matched guards and recovered 12 items. Praelarran is
now safely checkpointed at level 11 with 50,804 XP and no loss or death. This
is level-11 continuation and training evidence, not subclass or HERO proof.
Runs 9254, 9259, and 9262 added 536 XP from three small-troll kills; runs
9255 and 9263 added 1,220 XP from four source-matched guards, with safe Moria
and Shire absence probes between them. Praelarran is now safely checkpointed at
level 11 with 52,560 XP and no loss or death. This remains level-11
continuation evidence, not subclass or HERO proof. Run 9267 added 230 XP from
an armed guard. Runs 9268 and 9280 added 864 XP from source-matched patrolling
guards; run 9272 added 202 XP and run 9278 added 186 XP from small trolls.
Run 9274 killed a patrolling guard for 395 XP, withdrew at the 32% health floor,
and paid a 99-XP flee cost for a net 296 XP; the exact source policy is now
bounded by its one-loss protection rule. Run 9277 added 302 XP from an armed
guard, while run 9279 recorded a clean Circus absence. Praelarran is safely
checkpointed at level 11 with 54,650 XP and no death; this remains level-11
continuation evidence, not subclass or HERO proof. Runs 9283-9284 added 468
objective XP from an armed guard and a small troll. Run 9285 recorded a clean
Strongman's Tent no-target result; run 9286 added 401 XP from a patrolling guard;
runs 9287-9288 completed loot sale and return-home maintenance. Run 9289 added
178 XP from an armed guard and used its body part as food; runs 9290-9291
completed flight and return-home maintenance. Run 9292 added 178 XP from a small
troll, run 9293 recorded 10 incidental XP from a drunk while its Circus target
was unavailable, and run 9294 added 342 XP from a patrolling guard after
recovering a weapon dropped by a live disarm. Praelarran is now level 11 at
56,227 XP at checkpoint 28226, with no loss or death in this continuation
batch. This remains level-11 continuation evidence, not subclass or HERO proof.
Runs 9297-9298 added 490 objective XP from an armed guard and a small troll;
run 9299 recorded a clean Strongman's Tent no-target result; and run 9300 added
281 XP from a patrolling guard with six items recovered. Praelarran is now
level 11 at 56,998 XP at checkpoint 28243, with no loss or death in these
follow-up segments. This remains level-11 continuation evidence, not subclass
or HERO proof. Runs 9303-9306 added 789 objective XP and 20 incidental XP
through armed-guard, small-troll, Circus absence, and patrolling-guard routes.
Runs 9307-9308 completed loot sale and return-home maintenance; run 9309 added
202 XP from an armed guard; run 9310 refreshed flight; run 9311 recorded a
10-XP incidental drunk contact while the Cult fanatic was unavailable. Run 9312
then added 442 XP from a patrolling guard and crossed Praelarran from level 11
to 12, raising maximum health from 246 to 270. He is now level 12 at 58,461 XP
at checkpoint 28275 with no loss or death. This is level-12 continuation
evidence, not subclass or HERO proof.
Runs 9313-9316 completed loot sale, healer return, outfit, and return-home
maintenance; a 10-XP transit contact occurred during the sale without an
objective target, loss, or death. Run 9317 then killed the source-matched
on-duty guard for 241 XP, recovered six items, and preserved an enhanced-damage
practice when the trainer's current proficiency cap rejected another attempt.
Praelarran is now level 12 at 58,712 XP at checkpoint 28287, with no loss or
death. This remains level-12 continuation evidence, not subclass or HERO proof.
Runs 9318-9319 completed loot sale and healer return. Run 9320 accepted second
attack at 40% toward its 50% cap; run 9321 refreshed flight. Run 9322 completed
a bounded Moria search with only 20 incidental XP and no objective kill, while
run 9323 raised unarmed combat knowledge to 50% toward the 60% stun gateway.
Run 9324 then killed the patrolling guard and on-duty guard for 583 objective
XP, recovering 11 items. Praelarran is now level 12 at 59,315 XP at checkpoint
28306 with no loss or death. This remains level-12 continuation evidence, not
subclass or HERO proof. Runs 9325-9326 completed loot sale and healer return.
Run 9327 added 192 XP from an armed guard; run 9328 recorded the Dragon Cult
fanatic absent; and run 9329 reached the Shire route and skipped a crowded
circuit target before combat. Run 9330 then killed the patrolling guard and
on-duty guard for 477 objective XP, recovering 11 items. Praelarran is now
level 12 at 59,984 XP at checkpoint 28323 with no loss or death. This remains
level-12 continuation evidence, not subclass or HERO proof.
Run 9340 recorded a clean Circus absence. Run 9341 added 543 XP from a
patrolling guard and on-duty guard; run 9342 recorded a 10-XP incidental drunk
contact during loot sale; and run 9344 added 182 XP from an armed guard. Run
9345 recorded another clean Circus absence, while run 9346 added 269 XP from a
patrolling guard and skipped a crowded second target. Run 9349 added 318 XP
from an on-duty guard; run 9352 added 280 XP from an armed guard; run 9353
recorded a clean Circus absence; and run 9354 added 284 XP from an on-duty
guard. Intervening maintenance returned safely. Praelarran is now level 12 at
63,051 XP at checkpoint 28390 with no loss or death. This remains level-12
continuation evidence, not subclass or HERO proof.
Runs 9355-9356 recorded safe Daycare and Cult absences. Run 9357 added 271 XP
from an on-duty guard; run 9358 added 175 XP from a Shire bull after skipping a
crowded circuit; and runs 9359-9360 completed flight and return-home
maintenance. Runs 9361, 9364, and 9367 recorded clean New Ofcol absences; run
9362 added 228 XP from an on-duty guard; and run 9363 recorded a clean Circus
absence. Run 9368 added 174 XP from an armed guard. Run 9369 then exposed an
unexpected dwarf-forest combat, costing 116 XP on withdrawal without death; the
exact route is now bounded by the current-reboot loss policy. Praelarran is
level 12 at 63,783 XP at checkpoint 28435, safe and with no death. This remains
level-12 continuation evidence, not subclass or HERO proof.
Run 9370 then killed the source-matched Aruncus the Druid for 477 XP, recovered
one item, and returned safely at full health. Praelarran is now level 12 at
64,260 XP at checkpoint 28438. This remains level-12 continuation evidence,
not subclass or HERO proof.
Run 9371 then killed the source-matched armed guard for 207 XP, used a recovered
body part as food, and returned safely at full health. Praelarran is now level
12 at 64,467 XP at checkpoint 28441. This remains level-12 continuation
evidence, not subclass or HERO proof.
Run 9373 then killed the source-matched on-duty guard at VNUM 9401 for 224 XP,
recovered one patched leather jerkin, and returned safely at full health. The
separate VNUM 9406 route remains bounded after its 116-XP loss. Praelarran is
now level 12 at 64,691 XP at checkpoint 28447. This remains level-12
continuation evidence, not subclass or HERO proof.
Run 9374 then killed another source-matched armed guard for 190 XP and returned
safely at full health without loss or death. Praelarran is now level 12 at
64,881 XP at checkpoint 28451. This remains level-12 continuation evidence,
not subclass or HERO proof.
Run 9375 recorded a safe Dragon Cult no-target result with no combat or XP
change, advancing the resumable checkpoint to 28454. This remains level-12
continuation evidence, not subclass or HERO proof.
Run 9376 recorded a safe New Ofcol no-target result with no combat or XP change,
advancing the resumable checkpoint to 28457. This remains level-12 continuation
evidence, not subclass or HERO proof.
Run 9377 then killed the source-matched on-duty guard at VNUM 9401 for 222 XP
and returned safely at full health without loss or death. Praelarran is now
level 12 at 65,103 XP at checkpoint 28460. This remains level-12 continuation
evidence, not subclass or HERO proof.
Run 9378 recorded another safe Circus no-target result with no combat or XP
change, advancing the resumable checkpoint to 28463. This remains level-12
continuation evidence, not subclass or HERO proof.
Run 9379 recorded a safe Daycare no-target result with no combat or XP change,
advancing the resumable checkpoint to 28466. This remains level-12 continuation
evidence, not subclass or HERO proof.
Run 9380 then killed the source-matched on-duty guard for 286 XP, recovered a
notched scimitar after a live disarm, and returned safely at full health without
loss or death. Praelarran is now level 12 at 65,389 XP at checkpoint 28469. This
remains level-12 continuation evidence, not subclass or HERO proof.
Run 9381 recorded a safe Drow no-target result with no combat or XP change,
advancing the resumable checkpoint to 28473. This remains level-12 continuation
evidence, not subclass or HERO proof.
Run 9382 recorded a bounded New Ofcol squire search with no target, combat, or
XP change, advancing the resumable checkpoint to 28476. This remains level-12
continuation evidence, not subclass or HERO proof.
Run 9383 then killed the source-matched on-duty guard for 334 XP and returned
safely at full health without loss or death. Praelarran is now level 12 at
65,723 XP at checkpoint 28479. This remains level-12 continuation evidence,
not subclass or HERO proof.
Run 9384 recorded a safe Dragon Cult no-target result with no combat or XP
change, advancing the resumable checkpoint to 28482. This remains level-12
continuation evidence, not subclass or HERO proof.
Run 9385 recorded a bounded New Ofcol Jack search with no target, combat, or XP
change, advancing the resumable checkpoint to 28485. This remains level-12
continuation evidence, not subclass or HERO proof.
Run 9386 then killed the source-matched on-duty guard for 219 XP and returned
safely at full health without loss or death; its practice audit also retried
cleanly after interleaved room output. Praelarran is now level 12 at 65,942 XP
at checkpoint 28488. This remains level-12 continuation evidence, not subclass
or HERO proof.
Run 9387 recorded a clean Circus no-target result with no combat or XP change,
advancing the resumable checkpoint to 28491. This remains level-12 continuation
evidence, not subclass or HERO proof.
Run 9388 stopped safely before field travel because the character had no carry
capacity for one essential pie after reaching General Supplies. There was no
combat or XP change; checkpoint 28494 preserves the resource-maintenance
boundary for the next invocation. This remains level-12 continuation evidence,
not subclass or HERO proof.
Run 9389 repeated that capacity boundary during a return-home resupply segment,
again without combat or XP change. The return-home handoff now defers the
purchase instead of failing when one pie cannot fit; the full offline suite
passes 2,993 tests, and live revalidation remains the next step. This remains
level-12 continuation evidence, not subclass or HERO proof.
Run 9390 then exposed the asynchronous variant: the server rejected buy-one
pie repeatedly after the quantity backoff, and the progress watchdog stopped
the run without combat or XP change at checkpoint 28499. A decision-time guard
now exits the shop after the final rejection; the full offline suite passes
2,994 tests and live revalidation remains the next step. This remains level-12
continuation evidence, not subclass or HERO proof.
Runs 9333 and 9338 recorded clean Circus and Dragon Cult absences. Run 9334
added 214 XP from an armed guard; run 9335 added 738 XP from a patrolling guard
and on-duty guard after recovering a disarmed broadsword; runs 9336-9337
completed loot sale and healer return. Run 9339 added 229 XP from another armed
guard. Praelarran is now level 12 at 61,165 XP at checkpoint 28347 with no loss
or death. This remains level-12 continuation evidence, not subclass or HERO
proof.
Aeloria's next bounded invocation retained her Shadow Keep crowd gate
without combat. Run 9041
completed a bounded Shadow Keep eel continuation without combat, XP
change, death, or loss, and left Aeloria full in healer room 3054. The live
level-18 frontier is currently dominated by source-confirmed absence and crowd
evidence, so the runner stopped safely rather than repeating depleted routes.
The quest-point implementation now also source-ranks dynamic quests using
the exact target reset, current level/HP, specials, companions, and route
metadata before any live movement. An unsafe active quest, including a
source-proven inaccessible room, is converted to a bounded `quest abort`
return to its registered questmaster, after which DD4's cooldown must expire
before a replacement request. Run 9043 live-validated this behavior against an
object quest in disconnected Gloomy Forest room 285; Dorrik returned safely to
healer room 3054 with the quest cleared. Run 9044 then recorded a clean Shire
absence after one automatic reset wait. Run 9045 completed a bounded
source-ranked hunt without progress; run 9046 safely applied the source-
identity gate, and run 9047 recorded the next funding target absent at its
source room. All three runs had no combat, XP change, death, or loss. Run 9048
then killed the source-matched large orc in Moria for 175 XP and two items;
Praelarran returned safely to healer room 3054 without death or loss. Run 9049
then killed the source-matched Shire Miller for another 115 XP and recovered a
heart, again returning safely.
Runs 9050-9051 then added 125 XP from a source-matched Shire bull and 161 XP
from two source-matched Circus kills, recovering five items in the latter run.
Run 9052 extracted the source-listed purse coins and discarded the empty
container; run 9053 recorded a safe Circus absence; run 9054 then reopened
Moria for another 182-XP large-orc kill and two items. Runs 9055-9057 then
added 68 XP from a Circus bearded lady, 92 XP from Sorbus the Hermit, and 190
XP from a fanatic monk. Run 9058 sold three rings for 23 coins and returned
Praelarran safely to the healer. Run 9067 then killed a source-matched Shire
bull for 170 XP, crossing Praelarran from level 7 to level 8 with 19 additional
maximum hit points and no loss or death. Run 9068 filled the last legal empty
wear slot, hands, with a verified basic item from the Leather Shop. Run 9069
completed healer recovery without XP change; Praelarran remains safely
checkpointed in room 3054. Run 9070 then trained enhanced damage and unarmed
combat knowledge for the source-backed stun prerequisite, killed Ivan and the
Illusionist for 335 XP, and returned without taking damage or losing XP. Run
9071 rejected the live receptionist after `consider`; an aggressive wandering
drunk attacked during transit and was finished defensively for 10 incidental XP.
No objective target was claimed, and the return remained safe. Run 9072 then
recorded the fanatic route absent with no combat, XP change, loss, or death.
Run 9073 rotated to the Circus and confirmed Ivan plus the Illusionist for 320
XP, with full health and a safe healer return. Run 9074 then killed the source-
matched cook for 368 XP, recovered two items, and returned at full health. Run
9075 then recorded the Circus midget route absent with no combat, XP change,
loss, or death. Run 9076 confirmed Ivan plus the Illusionist for 403 XP, with
no loss or death and full healer recovery. Run 9077 recorded the fanatic route
absent with no combat, XP change, loss, or death. Run 9078 then killed the
source-matched cook for 429 XP and two items, returning at full health. Runs
9079-9080 sold four recovered items for 164 coins through the verified Weapon
Shop, Leather Shop, and Armoury, then completed healer recovery without XP
change. Runs 9081-9082 then added 786 XP from an armed guard and Ivan; the
second run skipped an ambiguous target and tried the recovered body part as
food. Both returned safely without XP loss or death. Runs 9083-9084 then
recorded the fanatic route absent and a source-matched cook kill for 275 XP and
two items, again returning at full health. Runs 9085-9086 then added 739 XP
from Ivan and an armed guard, with no loss or death and safe healer returns.
Runs 9087-9088 then recorded a fanatic absence and skipped an ambiguous
strongman target; an aggressive drunk was finished defensively for 20 incidental
XP, with no objective target, loss, or death. Runs 9089-9090 then added 614 XP
from a Bearded Lady, Illusionist, and armed guard; one wandering drunk added 10
incidental XP. Both returned safely without loss or death. Runs 9091-9092 then
covered the Foundry loop, recovering a disarmed broadsword and selling six items
for 103 coins through the Leather and Weapon Shops. Run 9093 completed a safe
return-home checkpoint; run 9094 then added 120 XP from a source-matched Bearded
Lady without loss or death. Run 9095 confirmed the Dragon Cult fanatic absent
and returned safely; run 9096 then killed source mobile 112, Ushog, for 238
objective XP after a 20-XP incidental Olog contact, recovered five items, and
returned full to healer room 3054. Run 9097 sold three items for 26 coins
through the Armoury and Jeweller after an aggressive drunk was finished for 10
incidental XP; run 9098 slept and completed a safe healer return. Runs 9099
and 9100 then reached two Circus source rooms, found the Bearded Lady and
mother targets absent, and returned safely without combat, XP loss, or death.
Runs 9101-9102 then killed the source-matched Illusionist and Ivan for 250
objective XP, recovered two keys, and recorded the Dragon Cult fanatic absent;
both returned safely without loss or death. Run 9103 then added 141 XP in the
Foundry: Olog supplied 10 incidental XP and source mobile 112, Ushog, supplied
131 objective XP; five items were recovered. Run 9104 sold three items for 41
coins through the Leather Shop and Jeweller. Praelarran is now level 8 at
30,114 XP at checkpoint 27707. Run 9105 completed healer recovery; run 9106
then killed source mobile 2405, Katrina the Shepherd, for 269 objective XP and
two items after a safe consider. Praelarran reached a 71.7% HP low point and
returned safely. He is now level 8 at 30,383 XP at checkpoint 27712. Run 9107
recorded the Circus midget absent; run 9108 bought and verified a light blue
flight potion from the Magic Shop without combat or XP change. The current
checkpoint is 27717.
The selector keeps gas-bearing breath forms (`spec_breath_gas` and the random
gas branch of `spec_breath_any`) research-gated even when sanctuary and health
reserves are proven. Lightning breath retains its separate source-bounded
path. The selector and executor share this boundary. The full offline suite
passes 3,189 tests; this remains level-15/24 continuation and
source-safety evidence, not level-19, level-30, subclass-transition, or HERO
proof.
Quest target ceilings now mirror `quest.c` exactly: +4 below level 20, +9
below level 50, +14 below level 80, and +19 thereafter. That wider ceiling is
used only for an active generated quest and still requires source route, HP,
special, companion, crowd, and live-consider gates; ordinary hunts retain
their narrower level policy. Quest-ineligible mobile flags and shopkeepers are
also rejected from dynamic target execution.
When `where` reports a wandering target away from its reset room, the runner
requires the source wander graph to reach that exact room, ranks a temporary
live endpoint, and dispatches the ranked safe route rather than a raw shortest
path.

Runs 9014-9015 completed bounded Aeloria and Praelarran continuations without
death or XP loss: Aeloria reached the source-registered Arachnos route and
withdrew on its poisonous bystander gate, while Praelarran confirmed a Circus
target absent. Run 9016 completed Dorrik's automatic reset retry and safe Magic
Shop flight maintenance; runs 9017-9019 then added 67, 122, and 176 objective
XP to Praelarran from source-matched routes and returned him safely to the
healer after each segment; run 9020 added another 134 objective XP, and runs
9021-9024 recorded two source absences, flight maintenance, and safe return-home
without loss. The campaign repair now re-arms a timed-out source route only
after that automatic reset wait,
consumes the retry when the hunt segment opens, carries legacy attempt counts
forward, and quarantines it after two bounded attempts. Campaign preflight now
also records the exact source teacher mobile, room, keyword, skill, and route
for all 18 legal subclass combinations. The subclass-focused checks pass 78
tests and the full offline suite passes 2,965 tests. The source-ranked campaign
handoff now acquires that second purple or trained cure for every class when an
audited caster special is selected. A bounded Dorrik invocation after the
repair preserved the current-reboot Tentusks crowd gate, so live reserve-branch
revalidation still awaits a fresh executable candidate. This remains
level-7/18/24 continuation and source-preflight evidence, not level-19,
level-30, subclass-transition, or HERO proof.

Runs 8928-8963 extended the earlier level-18 continuation. A direct Gnome Treasury
stash yielded 719 copper and enabled flight; Arikasbab recorded a 139-XP loss,
and a bounded Town Clerk `spec_thief` probe recorded a 166-XP loss and
quarantined that exact policy. The selector now blocks incomplete negative
results before they displace fresh candidates, and source-ranked combat rejects
an unsupported "much healthier" target unless a peak-damage bound exists.
Highland Keeper supplied safe 284- and 556-XP kills; automatic reset waiting
completed once; runs 8953-8955 checked Crystal and Dwarven Home crowd gates;
run 8957 exposed the 319-HP Secretary loss; runs 8958-8959 restored full
healer state without another loss; and run 8962 confirmed another Keeper kill,
acquiring its tower key without an XP delta. The source audit also confirmed
that DD4's `group_gain` awards no XP when a summoned NPC delivers the final
blow, so the mage familiar opener now orders the pony to flee once an exact
target reaches 45% HP or less. Resume from checkpoint 27347 toward level 19,
then level 30 and the subclass transition. This is continuation evidence, not
fresh creation-to-HERO proof.

Campaign state now captures DD4 `Char.Quest` snapshots, including current and
total quest points plus the next level's required points and shortfall. Reports
show those values, and `policy_for` selects bounded quest request, target, and
completion steps when the live shortfall is positive while still allowing
recovery and maintenance first. Suturb is source-registered through level 25;
the source graph now supplies Goldmoon's explicit room-10024 route for levels
26-100. DD4's `update.c` gates advancement from current levels 29, 49, 79, and
99, so the required quest-point milestones are levels 30, 50, 80, and HERO
100; the selector reconstructs those values for older checkpoints that have
total points but no `Char.Quest` requirement fields. Live checkpoint 26804
verified clean continuation with status `available`, zero points, and zero
shortfall. Source-backed hoard preparation now recognizes DD4's ITEM_DIGGER,
form, and digging-weapon paths and acquires exact shovel VNUM 3604 from
Graveyard room 3613 when needed. Dynamic quest preflight now stops before any
Telnet action when the exact source route, room, mobile, or object is absent;
an inaccessible target follows DD4 FAQ 5.4 and uses QUEST ABORT, while a
missing source identity remains a resumable ready/unavailable checkpoint.
Object/hoard completion
and the remote Ota'ar Dar questmaster boundary remain research-gated; no
level-30 or HERO claim is implied.

The latest bounded continuation validated the level-24 source frontier and
startup repair. Run 8866 bought flight; runs 8867 and 8871 added only safe
incidental rabbit XP, while runs 8868-8870 recorded absent source targets. Run
8872 exposed a field-stop watchdog in a randomized Mirror Realm inter-target
leg; it returned safely with no XP loss. Runs 8873-8875 completed safe return
and bounded Mirror probes, including a crowded watchman and a route exit
mismatch, without death or loss. Aeloria's run 8876 safely exposed a delayed
text/GMCP transition boundary during provision funding; run 8877 replayed it
successfully after the parser repair, and runs 8878-8879 completed liquidation
and healer return. The parser now emits a GMCP room refresh only when text has
identified a transition and cleared the prior exit graph, while the reducer
still rejects delayed text that conflicts with a confirmed room. The full
offline suite passes 2,930 tests. These are continuation and repair records,
not fresh creation-to-HERO proof.

Level-30 subclass selection is now source-capability-gated for all 18 legal
base/subclass combinations. The area parser captures mobile teaching entries,
campaign preflight requires both `teacher base` and the exact `<subclass> base`
entry on a reset-backed route, and the starter selects that exact source teacher
instead of falling back to a base-class route. Examples include Jolob (mobile
31002, room 31041) for engineer/runesmith, Stathog (29134, room 29153) for
werewolf/vampire, and Zelda (20603, room 20695) for necromancer/warlock/witch.
The public HERO command also passed a prepare-only human mage/necromancer smoke
test. This is executable source/preflight evidence, not live level-30
transition or HERO proof.

Runs 8759-8809 validated the latest bounded continuation. Run 8759 bought a
135-copper flight potion and confirmed that a text-only return to Main Street
recovers the known room VNUM before safely reaching the healer. Run 8760
recorded the white stag absent and returned without XP change. Run 8761 found
the Arachnos guardian by `where`, but its reported Realm of Hopeless location
was not a reachable combat endpoint before the progress watchdog; it returned
without XP loss. The locator repair now rebases matched source routes from the
live room rather than concatenating unrelated circuit waypoints; it is
offline-verified, while a fresh live guardian target remains pending behind the
current-reboot absence cooldown. Run 8762 then killed the source-matched Fat
Black Cat (mobile 28311, room 28316) for 682 objective XP and returned safely
with no XP loss or death. Run 8758 remains an important negative result:
Aeloria died
after repeatedly fleeing a level-8 dustdigger in the Great Eastern Desert
return maze, completed corpse recovery, and was restored safely. Run 8763 then
killed the source-matched giant, purple sand worm (mobile 5004, room 5028) for
592 objective XP, but lost 1,392 XP to repeated flee penalties from below-band
dustdiggers before returning alive and full to the healer. The delayed-pursuer
assessment repair is offline-verified and awaits a fresh live maze target;
these are level-18 continuation and safety records, not subclass or HERO proof.
Run 8764 then completed the normal Moria sanctuary continuation, killed the
source-matched large hobgoblin for 100 objective XP, and returned full to healer
room 3054 without XP loss or death. Run 8765 found no objective nomad kill;
a source-known below-band drider interruption yielded 80 incidental XP without
XP loss or death, and Aeloria returned safely. Run 8766 then completed a
return-home maintenance segment with no XP change, death, or unsafe state. Run
8767 then completed safe loot liquidation with no XP change, death, or XP loss.
Run 8768 then completed another return-home maintenance segment with no XP
change, death, or XP loss. Run 8769 then completed the source-priced
flight-potion maintenance step without XP change or combat. Run 8770 then used
`where` to confirm the white stag absent, returned safely, and recorded no XP
change, death, or loss. Run 8771 then found three mobiles in the Dwarven Home
room, recorded a source-backed crowd gate, and withdrew without combat, XP
change, death, or loss. Run 8772 then found two mobiles in the Dwarven Home
servant room, recorded the source-backed crowd gate, and withdrew before
combat without XP change, death, or loss. Run 8773 then reached the
source-present Keeper of the Tower, withdrew at the 51% health gate after
missed mage damage, and paid 232 XP without a kill or death; the exact policy
is quarantined rather than blindly retried. Run 8774 reached the Forest
medicine route but hit the 180-second boundary and returned safely without an
objective kill, required item, XP loss, or death. Run 8775 then completed the
safe return-home maintenance boundary with no XP change, loss, or death. Run
8776 then confirmed the gang/hood target absent at room 2148 and returned
safely without combat, XP change, loss, or death. Run 8777 then confirmed the
wyvern/centaur target absent at room 1717 and returned safely without combat,
XP change, loss, or death. Run 8778 found Essabella present at room 4528 but
below the useful-XP floor, skipped her before combat, and returned safely
without XP change, loss, or death. Run 8779 then killed the source-matched
giant, mobile 6506 in room 6508, for 376 objective XP and returned full without
XP loss or death. Run 8780 retried the same source VNUM after a fresh respawn,
found the giant materially healthier, withdrew at 85/218 HP, and paid 232 XP;
the exact policy is quarantined for this reboot rather than replayed. Run 8781
then completed the source-backed provision loop, killing valley elf sentry
mobile 7804 for 60 XP under the registered below-band funding exception and
returning full without XP loss or death. Run 8782 then completed safe loot
liquidation with no XP change, loss, or death. Run 8783 then completed a safe
return-home boundary with no XP change, loss, or death. Run 8784 then killed
the source-matched large hobgoblin for 110 objective XP, recovered a purple
sanctuary potion and a body part, and returned full without XP loss or death.
Run 8785 completed a source-priced flight-potion research step without combat
or XP change; no new stored price was obtained. Run 8786 then killed Lord Doom
for 888 objective XP and returned safely to healer room 3054 without XP loss or
death. Aeloria was at 209/218 HP at the latest checkpoint, so healer recovery
remains the next bounded step. Run 8787 then repeated the source-matched
large-hobgoblin sanctuary kill for 110 objective XP and returned full without
XP loss or death. Run 8788 then confirmed the white stag absent with `where`
and returned safely without combat, XP change, loss, or death. Run 8789 then
killed source mobile 28311, the Fat Black Cat in room 28316, for 972 objective
XP and returned full without XP loss or death. Run 8790 then reached the
source-matched queen spider in room 6134, observed three huge poisonous spiders,
and withdrew at the source-backed crowd gate without combat, XP change, loss,
or death. Run 8791 then found the gang/hood target absent and returned safely
without combat, XP change, loss, or death. Run 8792 found source mobile 28311,
the Fat Black Cat, present and considered viable, but Aeloria's mage damage was
insufficient; she withdrew at 46% health and paid 232 XP. The exact policy is
quarantined for this reboot rather than replayed. Run 8793 then reconfirmed the
white stag absent with `where` and returned safely without combat, XP change,
loss, or death. Run 8794 then completed another source-priced flight-potion
research step without combat or XP change; no new stored price was obtained.
Run 8795 reached source mobile 10302, the foreign trade representative, but
GMCP reported two useful-band or unknown active enemies; the executor aborted
safely and returned home, with a net 205-XP drop and no kill or death. The exact
policy is quarantined for review. Run 8796 then killed source mobile 10249,
the Sergeant at Arms' Secretary in room 10273, for 446 objective XP and
returned full without XP loss or death. Run 8797 killed the required large
hobgoblin for 110 XP and recovered its purple potion, but a source-known
sickly brown snake joined before return; Aeloria fled at 27% health after
paying a 232-XP penalty, leaving a net 122-XP drop and no death. The repair now
classifies ambiguous dynamic live names with any audited poison profile as
hazards before required-loot combat; offline-verified, bounded live validation
is pending. Run 8798 then completed a safe combat-pouch audit without XP
change, loss, or death. Run 8799 reached source mobile 6317, the medium dragon
wormkin, but live `consider` placed it below the useful-XP floor; it was skipped
before combat and Aeloria returned full without XP change, loss, or death. Run
8800 then confirmed the wyvern/centaur target absent at room 1717 and returned
safely without combat, XP change, loss, or death. Run 8801 reached the
source-matched Sergeant at Arms' Secretary again, but Aeloria's mage damage
remained insufficient; she withdrew at 46% health, paid 118 net XP, and
returned alive and full to healer room 3054. The exact combat policy is
quarantined rather than replayed. The next engineering priority is
source-backed mage damage, protection, and training decisions rather than a
lower withdrawal floor. The poison-name repair remains offline-verified and
awaits bounded live Moria revalidation.

Run 8802 confirmed the white stag absent and returned safely without combat,
XP change, loss, or death. Run 8803 then entered the source-matched foreign-
trade representative room, whose arrival text visibly contained three
bodyguards. The pre-patch endpoint did not apply the room-prose crowd gate
while `Char.Enemies` was null; combat began, the bodyguards joined, and Aeloria
lost 282 XP in aggregate before returning safely. The repaired gate now counts
source-indexed room mobiles before GMCP enemy data exists and is covered by the
offline suite. Run 8804 then killed source mobile 28311, the Fat Black Cat in
room 28316, for 791 objective XP and returned full without XP loss or death.
Direct live revalidation of the new room-prose gate remains pending because
the selector rotated to this productive route. Run 8805 then completed the
normal Moria sanctuary-carrier route, killed the source-registered large
hobgoblin for 100 objective XP, recovered another purple potion, sacrificed
the empty corpse, and returned full to healer room 3054 without loss or death.
Aeloria is now at 158,276 XP. Run 8806 then searched the source-allowed Hood
circuit, found the target absent, and returned safely through healer recovery
without XP change, loss, or death. The campaign remains ready for the next
frontier selection. Run 8807 then resumed Praelarran from the explicit
authoritative validation workspace, killed the source-matched Bearded Lady for
92 objective XP, collected its hairy key, sacrificed the empty corpse, and
returned full to healer room 3054 without XP loss or death. This extends generic
warrior continuation evidence but is not level-10, subclass, or HERO proof. Run
8808 then resumed Corararfen from campaign 22, killed the source-matched
Bearded Lady for 68 objective XP with `cause serious`, handled Beastly Fido as a
non-combat joiner, and returned safely without XP loss or death. This extends
cleric continuation evidence but is not level-10, subclass, or HERO proof. Run
8809 then searched Corararfen's independent Circus Bobby route, found the
approved target absent, and returned fully recovered without XP change, loss,
or death. The level-10 cleric campaign remains ready for the next reset-aware
selection.

Runs 8744-8746 closed a live recovery and equipment-loop gap. Run 8744
acquired the source rabbit roast and reached the healer, but exposed an unsafe
fed-return checkpoint at 32/218 HP. Run 8745 was then stopped at the safe
healer room after its recovery gear audit repeated `remove sword`, `wear
2.sword`, and `eq all`; the next invocation reconciled that interrupted row.
Run 8746 completed liquidation in 92.9 seconds and checkpointed Aeloria at
155,695 XP and 218/218 HP without a death. The guard now preserves
state-sensitive gear-loop history across complete `Char.Worn` snapshots, and
the full offline suite covers the repair. This is level-18 continuation and
repair evidence, not subclass or HERO proof.

Runs 8703-8725 continued Aeloria's level-18 frontier and exposed two live
protocol races. Run 8704 showed that mage sanctuary recovery needed the same
class-independent Lord Doom retry used by other classes. Run 8705 exposed
required-loot corpse cleanup being bypassed before an emergency return, and
run 8709 exposed a failed-recall loop that skipped the live Great Eastern
Desert maze. Runs 8711 and 8723 then reproduced liquidation watchdogs when a
city drunk was already fighting but GMCP had not yet published a usable enemy
snapshot. The starter now preserves required-loot cleanup, enters the Pyramid
maze return graph after recall failure, treats live enemy reports as combat
before utility navigation, and preserves a text-derived combat lock across a
stale empty `Char.Enemies` packet. Focused starter coverage is 1,095 tests;
the campaign suite passes 876 tests. Run 8713 live-validated the first city
combat repair by killing the drunk for 10 XP without loss. Runs 8720 and 8722
then added 383 and 100 XP through the mage familiar and source-drider routes;
run 8725 returned safely after a below-band Shire rejection. The second
empty-packet repair is offline-verified and awaits a later loot-bearing
liquidation for direct live revalidation. This remains level-band continuation
evidence, not subclass or HERO proof.

Runs 8726-8730 added 1,150 objective XP through two Arachnos guardian kills,
an Eastern Desert drider kill, and a further source-ranked kill, with safe
healer returns. Run 8731 reached a source-matched level-15 secretary but
withdrew at the calculated 51% reserve after dealing 96 partial XP, paying a
232-XP flee cost for a 136-XP net loss; this is a live combat-balance finding,
not progression proof. Run 8732 completed the Plains North source circuit with
the target absent and no loss, and run 8733 completed a safe liquidation. Aeloria
is now safely checkpointed at 155,625 XP; the stale empty-packet repair remains
offline-verified and still needs a loot-bearing live reproduction.

Run 8734 completed a bounded sanctuary-provisioning route and returned Aeloria
full with a purple reserve. Run 8735 completed another safe liquidation without
triggering the stale packet race. Run 8736 continued Dorrik's level-24 Mirror
Realm probe safely, and run 8737 completed Aeloria's healer return. The new
source-gated one-action finisher is covered by 1,096 starter tests and the full
2,854-test suite; its first independent live target validation remains open.
Run 8738 added a final safe liquidation checkpoint at 26524 with no XP change.

Runs 8699-8702 then continued Aeloria's level-17/18 frontier without a death:
one Eastern Desert route recorded a bounded 10-XP net loss after an incidental
drider, the sanctuary recovery route killed a large hobgoblin for 90 XP, and a
source-matched Highland Keeper kill added 402 objective XP and crossed her to
level 18. She returned safely to healer room 3054 with one verified purple
reserve. This is executable level-band continuation evidence, not subclass or
HERO proof.

The latest scheduler repair persists a registered research route's `where`
locator hazard instead of repeatedly selecting the same probe. It is covered by
the campaign regression suite and the full offline suite; live runs 8658-8669
also completed bounded class rotations safely, including Praelarran's level-7
transition and Corararfen's source-confirmed early-band kills. These are
continuation records, not level-10, subclass, or HERO proof.
Runs 8674-8676 then continued the class rotation without death or XP loss:
Praelarran recorded a 191-XP objective hermit kill and a later Circus crowd,
while Corararfen recorded a bounded source-ranked Gnome absence. These are
early-band continuation records, not level-10 or HERO proof.
Revision 173 also preserves `retryable_failure` for source-ranked runtime,
locator, and watchdog route boundaries, allowing the bounded automatic reset
retry to consume stale cooldown evidence. Run 8673 live-validated that repair
without death or XP loss; it recorded 150 incidental transit XP but no objective
kill before the 180-second route cap. This is scheduler and liveness evidence,
not level-25 or HERO proof.
Runs 8613-8620 continued Praelarran's level-6 HERO campaign safely. Run 8614
killed source mobile 1108 for 182 objective XP; run 8616 directly validated
the source-VNUM alias repair by killing the live `a hermit` identity for 295
objective XP under the canonical hermit-crab stop; runs 8615, 8617, and 8618
recorded bounded absence or maintenance results; run 8619 killed source mobile
1108 for 164 XP; and run 8620 killed source mobile 301 for 102 XP. These runs
recorded zero XP loss, no death, objective evidence where applicable, and safe
returns to healer room 3054. Praelarran is not yet level 7, and this remains
level-6 continuation evidence rather than level-10, subclass, or HERO proof.
Runs 8634-8651 continued Praelarran's bounded Cult, Circus, and daycare
rotation. Direct run 8646 reproduced DD4's selector-only text combat-start
packet ordering, preserved the authoritative source VNUM 1524, killed `a hermit`
for 304 objective XP, and returned safely to healer room 3054. Campaign 11 then
reconciled the live character at checkpoint 26276 and 18,332 XP, with no death
or XP loss. Corararfen's run 8652 and Dorrik's run 8653 also completed bounded
cleric and level-24 rotations safely. This is live source-identity and level-6
continuation evidence, not level-7, level-10, subclass, or HERO proof.
Runs 8621-8625 extended the same source-identity evidence across the cleric
campaigns: Corararfen killed source mobiles 1524 and 301 for 252 and 124 XP,
while Velnor killed source mobiles 1524 and 1108 for 171 and 272 XP. Run 8622
recorded a Shire crowd withdrawal with a net 47-XP gain and no death. These
are cross-class level-6 continuation records, not level-10, subclass, or HERO
proof.
Runs 8626-8628 continued Dorrik's level-24 frontier: run 8626 refreshed
flight at the current price of 135 copper, run 8627 killed source mobile 635
for 803 objective XP, and run 8628 completed the safe return-home boundary.
The kill occurred before the 180-second liveness boundary, with zero XP loss
and no death; the segment then checkpointed Dorrik in healer room 3054. This
is level-24 continuation evidence, not level-25, subclass, or HERO proof.
Runs 8629 and 8631 completed bounded Mirror Realm research probes for Dorrik
without XP change, loss, or death. Kestrel's next invocation honored the
current-reboot fame/service cooldown without opening a duplicate live segment,
and Aeloria's latest invocation preserved her safe state while recording the
Fleshmonger crowd. These are safe frontier and cooldown records, not
progression proof.
Runs 8418-8427 continued the bounded
level-17 frontier: the
runner rejected a live-negative Bardoosh consider, killed the source-matched
Bird Spider for 369 XP, then recorded a zero-XP repeat that is now quarantined
by the selector; Hood and Wyvern were absent and Shadow Keep was crowd-
exhausted. Run 8427 confirmed the Hood gang leader was absent. A reset-aware
continuation then returned safely without combat or XP change. The reset-wait
selector now ignores prior-level source cooldowns, so an old level-15 Ambush
record cannot block or describe Aeloria's level-17 frontier. The current source
revision is `7996722bc43508cc3773c48f8d79e3d07d68e5e4`; checkpoint 25886 is safe
and no worker remains active. Run 8428 then opened the bounded dynamic-wanderer
research fallback, reached source mobile 11518 in Highland room 11536, used the
mage familiar opener, and killed the Keeper of the Tower for 638 objective XP
before returning safely to the healer. Checkpoint 25886 is the latest safe
checkpoint after the subsequent bounded rotations and reset retry.
Run 8429 repeated the same bounded route and killed the Keeper of the Tower for
477 objective XP before returning safely; its reboot-local one-shot
repeatability marker is now consumed. Run 8430 then rotated to the Hood route,
recorded its target absent, and returned safely without XP change at checkpoint
25869. Run 8431 then recorded a crowded Shadow Keep route without combat, and
run 8432 killed source mobile 11512 in Highland room 11530 for 492 objective XP
before returning safely at checkpoint 25877. Run 8433 completed bounded flight
maintenance without XP change; run 8434 found the Wyvern target absent. The
bounded reset retry then found no fresh current-band route and left checkpoint
25886 safe in the healer room. Runs 8437-8448 then completed bounded retry and
rotation work. Run 8444 reproduced a same-policy Mirror Realm gardener research
handoff after startup reconciliation; the selector now requires a research
handoff to differ from `campaign_last_policy` before it is considered fresh.
Run 8445 completed Kestrel's sanctuary recovery. Run 8446 rotated Dorrik to
the source-ranked Shire Keeper route, reached the 180-second liveness boundary,
and returned safely without an endpoint kill, XP loss, or death. No character
died, no campaign worker remains active, and no new objective XP was recorded.
Run 8447 then rotated to the gardener again, rejected a wandering target
outside the source-safe relocation graph, and returned safely. Run 8448
completed a fresh source-ranked Mirror Realm probe and returned to healer room
3054 without an objective kill. The latest checkpoints are Aeloria 25916,
Dorrik 25936, and Kestrel 25925. This is safe frontier, selector-rotation,
and liveness evidence, not level-18, subclass, or HERO proof.
The mage reserve gate is now candidate-specific:
a clean source target can use one purple reserve, while blindness-capable caster
specials still require a second purple or a trained cure. The complete offline
suite passes 2,831 tests. The level-17 fallback admits one bounded research
probe when the only source objection is a reachable aggressive wanderer; the
live probe was safe and productive, but it remains research-status after the
one-shot repeatability probe; that allowance is now consumed for this reboot.
Promotion criteria remain open. This is not level-18,
subclass, or HERO proof.
The level-aware crowd repair ignored Dorrik's stale level-19 Eastern Desert
crowd and exposed the real level-24 Tentusks crowd. One bounded reset retry
rotated that current-band wait to an Arachnos cooldown at checkpoint 25956,
with no XP loss, duplicate segment, death, or worker left behind. The campaign
suite passes 868 tests and the full offline suite passes 2,833 tests. Run 8529
then exposed a silent pre-login socket while resuming Dorrik: DD accepted TCP
but sent no Telnet greeting. The bounded runner stopped safely at checkpoint
26038 and the repaired watchdog no longer sends gameplay recovery before
authentication. This is liveness evidence, not level-25, subclass, or HERO
proof.
Run 8530 then completed Dorrik's mirror-realm gardener probe, returning him
safely at level 24 and 360,901 XP; the 10-XP incidental increase is not
objective progression. Later checks recorded the Tentusks crowd and rotated
to an Arachnos current-reboot cooldown after an explicit reset retry. Velnor
runs 8531-8540 added 1,250 XP without a death. Corararfen and Praelarran both
reached safe level-6 empty-arena boundaries. These are continuation and reset
evidence, not level-25, subclass, or HERO proof.
Velnor's runs 8544-8564 continued the source-backed early cleric rotation
without death or manual steering. He crossed from level 5 to level 6 at
checkpoint 26079 with 14,201 XP and continued through checkpoint 26101 at
14,687 XP after level-6 kills and recovery. Corararfen's run 8567 killed the source-matched Bearded Lady for 64
objective XP and left her safely at checkpoint 26090 with 15,275 XP; the
following cult probe was a bounded zero-XP result at checkpoint 26092. This is
live level-6 continuation evidence, not level-10, subclass, or HERO proof.
Run 8571 then completed Dorrik's reset-aware mirror-realm gardener probe at
checkpoint 26097 without objective XP; the next selector invocation recorded
the Tentusks crowd at checkpoint 26099 and stopped before combat. Velnor's
latest safe return-home is checkpoint 26101 at 14,687 XP. These are current-band
continuation and crowd-gate records, not level-25, subclass, or HERO proof.
Runs 8574-8583 continued Velnor through the level-6 source frontier without
death; the explicit retry-stalled probe honored a below-band source `consider`
result at checkpoint 26119. Runs 8584-8585 recorded Corararfen's Circus crowd
and below-band boundaries at checkpoint 26123. Praelarran's runs 8586-8599
added 526 XP without death, including two source-matched Bearded Lady kills
and a Shire bull kill, leaving him at checkpoint 26148 with 15,604 XP. The
latest bounded higher-band invocations preserved Dorrik's Tentusks crowd,
Kestrel's fame-service cooldown, and Aeloria's Fleshmonger crowd. These are
current-band continuation and safe-stop evidence, not level-25, subclass, or
HERO proof.
Runs 8450-8452 then resumed the canonical human cleric matrix workspace:
Corararfen killed three Mud School mobs for 161 XP, completed a safe return-home
segment, then killed two wild boars and a wolf for 196 XP. Checkpoint 25959 is
alive at level 5 and 11,196 XP in healer room 3054. This is early cleric
continuation evidence, not level-10 or HERO proof.
The following bounded batch completed run 8453 with 573 XP from seven Mud
School kills, run 8454's daycare-ring maintenance, and run 8455 with 224 XP
from four more kills. Checkpoint 25962 is alive at level 5 and 11,769 XP.
Runs 8457-8486 then continued the canonical cleric rotation, adding 2,395 net
XP through source-backed Mud School kills, safe healer returns, and daycare
maintenance. Empty arena circuits were checkpointed for reset rather than
forced. Run 8486 crossed level 6; checkpoint 25993 is alive at 14,164 XP in
healer room 3054. This is live early-cleric progression evidence, not level-10
or HERO proof.
Runs 8491-8494 then added 355 net XP to Corararfen after the level-6
transition; checkpoint 26001 stopped safely when the Mud School arena was
empty. Runs 8495-8500 advanced Velnor through three source-backed Mud School
batches for 708 net XP, crossing him to level 5 at checkpoint 26007 in healer
room 3054. These remain early-cleric progression records, not level-10 or HERO
proof.
Runs 8511-8516 then added 1,074 net XP through four further Mud School
segments, a safe return-home, and daycare-ring maintenance. Velnor is alive at
checkpoint 26023 with 11,863 XP in healer room 3054; this remains early-cleric
progression evidence, not level-10 or HERO proof.
Runs 8517-8519 then added 312 net XP to Velnor across six Mud School kills
before an honest empty-arena checkpoint at 26026. Runs 8520-8525 added 487
net XP to Corararfen through two further Mud School batches, recovery, and
maintenance; she is alive at checkpoint 26032 with 15,006 XP. These remain
early-cleric progression records, not level-10 or HERO proof.
Run 8528 completed Corararfen's daycare-ring recovery and left her full at
checkpoint 26035 with 15,098 XP. This is a safe maintenance boundary for the
next verified level-6 segment, not level-10 or HERO proof.
Runs 8501-8510 then added 579 net XP to Velnor through recovery, daycare-ring
maintenance, and six further Mud School kills. He is safely checkpointed at
26017 with 10,789 XP in healer room 3054; this remains early-cleric
progression evidence, not level-10 or HERO proof.
Praelarran is safely
checkpointed there at full 143/143 HP, with no active worker.
Runs 8396-8406 live-validated bounded absence, reset, crowd, reserve, flight,
and return-home rotation. Run 8399 killed source mobile 6506, the Dwarven
giant, for 514 objective XP and returned safely. Run 8400 confirmed the
Olympus jailer absent; run 8401 reacquired a verified purple sanctuary potion
for 110 recovery XP; runs 8402-8403 confirmed Hood and Wyvern targets absent;
run 8404 restored flight; and run 8406 safely recorded a crowded Dwarven room
without a new kill, XP loss, or death. The
startup migration then exposed a convergence defect: an older no-kill circuit
record could downgrade a newer confirmed source kill, causing alternating
metadata checkpoints and a misleading Fleshmonger wait. The repair preserves
current-reboot confirmed objective results and is covered by a reconnect
regression. Checkpoint 25781 is the latest safe state. This remains level-17
continuation and repair evidence, not a level-18, subclass, or HERO claim.
Run 8360 killed source mobile 6506 for 787 objective XP and returned safely.
Run 8361 acquired the purple sanctuary reserve but exposed a probabilistic
combat-recall defect: the first recall failed for 50 XP and the immediate
second recall cost 208 XP, for a net 168-XP loss without death. The runner now
records that failed recall and takes one bounded flee/recovery path instead of
repeating recall; the full suite covers the parser and decision transition.
Runs 8362-8363 then completed an absent Hood probe and flight maintenance with
no further XP loss. Run 8364 reached the source-matched Fleshmonger, consumed
sanctuary, was blinded by its audited mage special, and triggered the area's
source `greet_prog`, which forced the senior guard into combat; Aeloria
withdrew safely for a net 179-XP loss. The source parser now records mobile
program `mpkill` hazards and hard-gates scripted targets and companions before
combat. Run 8365 rotated to the Crystalmir white-stag probe, found it absent,
and returned safely with no further XP change. The automatic reset retry found
the next Ambush route on its current-reboot cooldown and stopped safely. This
is level-17 continuation and repair evidence, not level-18, subclass, or HERO
proof.
Runs 8366-8367 reproduced the Moria required-loot cleanup hazard and recorded
bounded XP losses after successful carrier kills. The runner now permits one
source-known, below-band poison pursuer when required loot is already secured,
while unmodelled pursuers still block corpse cleanup; focused tests cover both
paths. Run 8372 exposed an ANSI reset before a live target selector and cost
208 XP; the parser now removes presentation bytes before matching TARGETMODE.
Run 8373 then killed the source giant for 533 XP without loss. Run 8374
confirmed the selector repair but exposed an over-broad cleanup response to a
source-known below-band warrior; the final guard refinement tolerates that
bystander while retaining the unmodelled-pursuer stop. Its live revalidation is
waiting on the current restock cooldown. The pre-audit offline suite passed 2,803
tests.
The source audit now models `spec_cast_undead` separately: only a source level
ceiling below 15 can enter the executable frontier, with chill/blindness damage
bounded against character HP and a verified blindness cure required when that
branch is possible. Energy drain, harm, and gate remain research-only. The
post-audit Aeloria invocation preserved the `restock-provisions` crowd safe-stop
without opening a connection or clearing reboot-local evidence. The full
offline suite now passes 2,810 tests.
Runs 8386-8388 then recorded a safe Shadow Keep crowd, an absent centaur
chief, and a live wormkin whose `consider` result was below the useful-XP
floor. Run 8389 found the source-matched giant eel (mobile 16602, room 16610)
present and consider-viable, but exposed a selector/executor mismatch: the
executor still applied a zero-level source-fuzz ceiling. Lightning breath is
now source-audited as a direct HP pulse, the stop and selector share a +2
source-fuzz ceiling under sanctuary and HP bounds, and startup migration
reopens only that stale result. Checkpoints 25630-25641 persisted the repair,
completed one bounded 180-second reset wait, and returned Aeloria safely while
Fleshmonger crowd and Hood absence evidence remained active. No direct eel
combat revalidation is claimed yet. The full offline suite passes 2,813 tests.
Runs 8379-8380 exercised a source-present but crowded Forest medicine-man
route, immediately refreshed `where` to follow the wandering target, and
returned safely without XP change. Run 8381 identified Arachnos mobile 6317,
quaffed sanctuary, survived its gas breath and nausea effect, and killed it
for 708 objective XP before recalling and sleeping at the healer. The trace
showed that DD4 reports this poison as a `nausea` affect with `gives: poison`;
the runner now recognizes both fields, recalls from a recallable field room on
the next prompt, and keeps a poisoned healer checkpoint asleep until the
effect clears. Runs 8382-8383 completed coin banking and poison recovery with
no death or XP loss. Run 8384 then killed the source-matched Moria large
hobgoblin for 110 XP and secured its purple potion, but a separate live warrior
(source VNUM 4050) remained reported before corpse cleanup. The old ordering
recalled without first issuing `consider`, costing 208 XP; Aeloria survived and
returned safely for a net 98-XP loss. The post-objective consider handler now
runs before the generic required-loot cleanup guard, with a regression covering
the exact 4055-carrier plus 4050-warrior pattern. Run 8385 then probed the next
source-ranked gang-leader route, found it absent, and returned safely without
another loss. Direct live re-entry through the repaired Moria branch remains
pending; this is level-17 repair evidence, not level-18, subclass, or HERO
proof.
Run 8377 then executed the source-ranked Wyvern's Tower route for the audited
level-14 centaur chief; the source target was absent, so the campaign returned
safe to healer room 3054 and retired that route for the current reboot without
XP change. Run 8378 completed flight maintenance. The next invocation preserved
the absence without opening a duplicate run. A single purple potion is enough
for a non-sanctuary undead-special blindness cure; caster specials that consume
sanctuary still require two verified purples unless cure blindness is trained.
Run 8375 completed Velnor's next Mud School segment and left the cleric at
level 4, 9,502 XP, full in healer room 3054 with no death. Run 8376 stopped
Brannor before connection because no stored character credential exists; no
live character state changed. These are continuation and credential-boundary
records, not HERO proof.
The progression selector now exposes the first generic source-ranked handoff
at level 11 for tutorial-arena classes after their level-10 scout; explicit
level-12 through level-80 policies remain authoritative, and level 81+ uses
the same research-status frontier. This is executable research coverage, not
verified HERO progression.
When the level-6 to 10 tutorial routes are exhausted, the source-ranked
fallback now opens under the distinct `source-ranked-hunt-6-10` policy while
preserving the live source, route, consider, crowd, health, and healer-return
gates. Run 8295 proved that path with Praelarran's source-matched Bearded Lady
kill for 108 XP; run 8296 then rotated to the independent Cult fanatic route,
found it absent, and returned safely without replaying the blocked target.
Runs 8297-8300 continued the Circus rotation and public hero retry boundary;
runs 8301-8302 added 103 XP from the Bearded Lady and 274 XP from the Shire
bull, both with safe healer returns. The full offline suite passes 2,799 tests.
Run 8307 exposed an endpoint identity hazard and cost 49 XP; run 8308 exposed
the older generic Moria locator chase and cost a further 98 XP, without a
death. The recovery policy now binds to source mobile 4055 in reset room 4064,
and run 8309 live-validated that it records the carrier absent, recalls, sleeps
at the healer, and quits with no XP loss. This is early warrior and safety
evidence, not level-10, subclass, or HERO proof.
Runs 8310-8316 live-validated the mage-specific second-purple reserve gate and
two productive level-17 hunts. The repaired route counts an audited pouch
potion, requires two purple potions and invisibility, and preserves the first
reserve while acquiring the second. Aeloria killed source mobile 8902 for 835
XP and source mobile 6367 for 821 XP, returning safely with no death or XP
loss. Run 8328 then exposed a remaining post-objective escape defect: a useful-
band warrior joined after the Moria carrier kill, and fleeing cost 208 XP. DD4
source confirms that successful flee and combat recall both charge the same
level-scaled loss, so the runner now assesses an unknown attacker with an exact
live selector before paying that cost and directly recalls from audited hazards.
Run 8329 live-validated the repaired ordinary Arachnos route with 566 XP and no
death or XP loss. The post-objective warrior assessment was not triggered in
that run, so this remains level-17 repair and continuation evidence, not level-
18, subclass, or HERO proof.
Runs 8331-8332 then added one clean 568-XP Arachnos guardian kill and one
neutral Crystalmir probe. The interrupted run 8333 was reconciled on resume;
run 8334 exposed a second-order Moria defect where repeated Char.Enemies rows
for the exact source-bound below-band carrier were counted as a crowd, costing
208 XP without a death or objective kill. The repair now permits that duplicate
packet only for exact required-loot carriers and leaves ordinary XP hunts
conservative. Runs 8335-8336 completed flight maintenance and a Hood probe
without XP change. Direct live revalidation of the duplicate-packet repair is
deferred until the current recovery cooldown clears. Aeloria is level 17 at
150,396 XP, safely full in healer room 3054 with no active worker or verified
combat-pouch reserve. This remains level-17 continuation evidence, not level-18,
subclass, or HERO proof.
Runs 8340-8341 and 8348 advanced Velnor through seven verified Mud School
kills for 280, 206, and 101 XP, reaching level 4 at 9,334 XP; run 8349 then
recorded the arena empty without XP loss. Run 8351 advanced Praelarran through
a wild boar and wolf for 110 XP to level 6 at 15,078 XP, while run 8352
recorded an honest empty-arena stop. Run 8353 completed Velnor's safe healer
return. Runs 8354-8355 then exposed and repaired the Moria post-objective
ordering defect: the consider-only recovery guard had been fleeing before the
unknown warrior could be assessed, costing 208 XP after a 110-XP carrier kill;
the regression now gives the exact attacker selector priority. Run 8355 then
reacquired the sanctuary reserve for 100 XP without loss. Run 8356 exposed a
separate protected-peak handoff: the selector admitted the Dwarven servant but
the field executor still used a zero-level ceiling. The repair carries the
verified sanctuary half-damage bound into a +2 source-fuzz ceiling, covered by
845 campaign tests. Runs 8357-8359 rotated safely through Arachnos, sanctuary
recovery, and an absent Shadow Keep Undead Soldier; Aeloria ended level 17 at
150,498 XP, full in healer room 3054 with two verified reserves. Direct live
combat through the protected peak and the post-objective warrior branch remain
unobserved, so this is level-17 continuation and safety evidence, not level-18,
subclass, or HERO proof.
The durable Aeloria, Dorrik, and Kestrel campaigns retain target level 100;
their current levels are safe progression checkpoints rather than completion
claims.
Runs 8022-8048 continued the ordinary level-17 rotation with one bounded XP
loss and no death. Run
8022 recorded a bounded Arachnos health-floor loss; the route was quarantined
for that reboot. Runs 8026-8028 then directly probed and revalidated the
extended Moria carrier circuit, acquiring purple sanctuary potion VNUM 4050
and returning safely. Runs 8029 and 8038 killed source-matched Dwarven
Noblemen for 882 and 791 XP. Runs 8035 and 8043 killed the source-matched
Arachnos guardian for 622 and 705 XP. Run 8045 reproduced the late
post-objective snake hazard and cost 208 XP after a 100-XP carrier kill; the
character survived and returned full, and that route is retained as bounded
loss evidence. Run 8046 then preserved the recovered potion reserve. Direct
run 8047 killed another carrier for 90 XP, while run 8048 found the snake-only
maze with no carrier and recalled without combat. Aeloria's campaign checkpoint
is full in healer room 3054 at 144,241 XP, 10,209 XP short of level 18. Run
8075 reproduced a live post-objective poison hazard after the carrier kill;
the first recall failed, the old return branch fled, and the segment lost 774
XP without a death. The repair retries recall for an audited hazard in a
recallable room, with focused regression coverage. Runs 8076-8078 then
completed a safe Chapel probe, killed the source-matched Arachnos guardian for
439 XP, and completed a Grove probe without another loss. The room-text hazard
gate remains offline-verified but has not yet received a direct live rejection
trigger; clean live route results are not proof that the branch fired. The full
offline suite passes 2,776 tests. Runs 8079-8084 then completed sanctuary
recovery, Arachnos, Crystalmir, and another sanctuary rotation without loss.
Runs 8085-8087 safely recorded Arachnos, Hood, and Shadow Keep absences. Runs
8088-8089 completed an Eastern Desert incidental drider withdrawal and safe
liquidation. Run 8090 withdrew from a Dwarven endpoint after GMCP reported two
useful-band or unknown enemies, costing 208 XP without a death; that exact
policy remains bounded route-risk evidence. Aeloria is now full at 145,360 XP.
Run 8101 recorded Kestrel's actual Circus fame-recovery death: the ticket
clerk's consider response said he was `built like a tank`, but the old policy
still entered combat. Purgatory recovery completed, and live XP fell from
345,681 to 336,616. The new consider gate rejects that warning before combat,
and the failed-flee fallback prefers recall on recallable field routes. Run
8102 live-validated the rejection without combat or death; run 8103 reacquired
Moria sanctuary for 110 XP, and run 8104 completed a safe food-reserve segment.
Runs 8105-8111 then completed flight, forest gear, funding, liquidation, and
safe return-home maintenance; run 8109 added 70 XP from a source-backed John
the Lumberjack funding kill. Kestrel was safely checkpointed in healer room
3054 at 336,796 XP before the later bounded continuation. No level-25 or HERO
claim is made.
Runs 8112-8115 then recorded a bounded fame withdrawal, crowded Moria, a
successful stalled-candidate retry that killed the source-matched large
hobgoblin for 110 XP and recovered purple sanctuary, and an absent gnome-guard
probe. Runs 8116-8126 advanced Velnor's cleric through verified arena kills to
level 3; run 8118 stopped Brannor at the missing credential boundary. Runs
8127-8149 created and advanced Praelarran, a fresh human warrior with a stored
credential, anti-machine title, and backstory, to level 4 using the bounded Mud
School reset wait. Runs 8150-8201 then crossed level 5 and continued through
post-level maintenance and reset-aware arena segments without death. Runs
8214-8223 crossed level 6. Run 8224 exposed a real partial-band bug: wild boar
passed live consideration while wolf failed, but the old merge excluded the
whole arena. Policy revision 170 now preserves viable targets and reopens only
the stale same-reboot exclusion; the full suite passes 2,776 tests. Runs
8226-8228 revalidated the arena and recorded both targets below band. Run 8229
safe-probed the source-ranked Dragon Cult fanatic and found it absent, so
Praelarran is waiting for a fresh reboot or candidate. These records are
continuation evidence, not level-10, subclass, or HERO proof.
Runs 8240-8243 exposed and repaired a bounded provisioning timeout for Kestrel;
the worker now exits at its liveness boundary with a resumable healer checkpoint.
Runs 8244-8249 then exposed a negative-reputation loop: the Magic Shop refused
Kestrel's flight purchase, but the old selector reopened the same shop and
funding path. The selector now treats a failed purchase plus used flight loan as
a hard service boundary and returns `unavailable` when no executable non-shop
frontier remains. Regression coverage passes in the 838-test campaign suite and
the 2,777-test offline suite. Runs 8250-8252 live-validated the repair: Kestrel
used the registered Mirror Realm fame route, withdrew safely from an overmatched
moose for a net 111 XP loss without dying, then reacquired purple sanctuary and
returned to healer room 3054 at level 24 and 336,913 XP. This is safety and
selector evidence, not level-25 or HERO proof.
The latest bounded Aeloria invocation ended safely at level 17 while her
source-ranked current-band route waited on this reboot's reset cooldown. Run
8253 advanced Velnor, a human cleric, to level 4 at 6,839 XP through the
verified Mud School segment and returned him safely to healer room 3054. Runs
8260-8261 added 141 XP in two more bounded segments and exited without an
unnecessary reset wait. Run 8266 then added 267 XP through four Mud School
kills; runs 8267-8269 advanced Velnor to 8,177 XP, 1,873 XP from level 5,
before the reboot-local arena-empty gate. These early-class and safe-stop
records are not level-10, subclass, or HERO proof.
Runs 8262-8263 then gave Kestrel a source cure-critical reserve and safely
rejected the Circus fame target without combat or XP change. Dorrik's next
source-ranked probe found the Eastern Desert crowded and returned him safely;
both remain continuation evidence rather than level-25 or HERO proof.
Runs 8270-8274 continued Velnor to 8,747 XP at level 4 before an honest Mud
School arena-empty stop. Runs 8275-8285 continued Corararfen through safe
healer, daycare-ring, and Mud School segments to 9,991 XP at level 4, leaving
him 59 XP from level 5. The DD4 source mirror was refreshed and remains at
revision 7996722. These early-class checkpoints are not level-10, subclass, or
HERO proof. Runs 8286-8287 then crossed Corararfen to level 5 at 10,225 XP
through another verified Mud School rotation. Runs 8288-8290 completed outfit,
healer, and daycare-ring maintenance, adding 82 incidental XP and leaving him
at 10,307 XP with full HP and mana in healer room 3054; no death occurred.
Run 7900 live-validated the repaired wandering-carrier locator through the
ordinary campaign selector. `where hobgoblin` located carriers in `The maze`
and `The large cave`; the source-approved sweep found the maze carrier at
room 4057, killed it for 90 XP, acquired purple sanctuary potion VNUM 4050,
stored it in the combat pouch, and returned Aeloria safely to healer room
3054. The campaign recorded the required object as acquired and viable, with
no death or XP loss. This is resource-recovery and route-repair evidence, not
level-17 or HERO proof.
Run 7907 repeated the ordinary sanctuary-recovery route and acquired another
source-matched purple potion for 100 XP. Runs 7908-7933 continued through safe
absence, funding, flight, sanctuary, guardian, elite-guard, and Bird Spider
policies. Runs 7937-7945 then live-validated the bounded inactivity probe and
several source-ranked routes, reaching the valid level-16 checkpoint at 132,332
XP without death or XP loss. Run 7946 is explicitly rejected as progression:
an immortal-arrival GMCP snapshot for another character supplied an impossible
level-106 `Char.Worth` payload. Its transcript remains available for audit, but
the run and campaign segment are quarantined and the campaign resumes from the
healer checkpoint. This is continuation evidence, not level-17 or HERO proof.
Run 7948 then exposed a Moria crowd-state defect: repeated carrier records in
`Char.Enemies` were counted as material enemies even though the room's veteran
warrior and orc were source-proven below-band; the safe retreat cost 188 XP.
Run 7949 confirmed a Crystalmir absence without XP change. Run 7950 live-
validated the crowd repair: Aeloria killed the carrier for 100 XP, finished the
incidental orc for 80 XP, acquired and pouched the purple potion, and returned
safely with no retreat loss. Run 7952 then exposed a separate ordering hazard:
source mobile 4053, the sickly brown snake with `spec_poison`, remained after
the carrier kill and the pre-repair poison gate acted too late. The segment
ended without a death but netted only 9 XP. The runner now indexes source
specials by mobile VNUM and recalls before an audited post-objective poison,
direct-damage, cleric, or mage special. Runs 7953-7955 completed flight
maintenance and two source absences safely. Aeloria is now at 132,762 XP.
This is fresh level-16 continuation and repair evidence, not level-17 or HERO
proof; direct live validation of the new poison boundary remains next. Run
7956 then killed source mobile 6310, the Bird Spider, for 548 objective XP and
returned safely without death or XP loss. Run 7957 recorded an absent source
druidess and returned safely. Run 7958 repeated the source-matched Moria
carrier route, killed mobile 4055 for 90 XP, acquired the purple sanctuary
potion, and returned safely. Run 7959 reached the Dwarven Homestead nobleman,
withdrew at the existing health floor, and paid 188 XP without dying. Aeloria
is now 307 XP short of level 17. Run 7960 then killed the source-matched
large hobgoblin for 100 XP and the joining warrior for 80 XP, recovered and
pouched the purple sanctuary potion, sacrificed the emptied corpse, and
returned safely without death or XP loss. Run 7961 then killed source mobile
6310, the Bird Spider, for 484 total XP, including a critical hit and the
level-up to 17. The level-up granted 8 HP, 31 mana, 10 movement, 2 physical
practices, and 4 intellectual practices; Aeloria returned full to healer room
3054 without death or XP loss. She is now level 17 at 133,957 XP. Run 7962 then
reached the Crystalmir Lake endpoint, issued the source-backed `where stag`
search, found no White Stag, and returned safely to healer room 3054 with XP
unchanged. Run 7963 then bought and quaffed a light blue flight potion for 30
reboot-local copper, confirmed the fly affect, and returned full to the healer
with XP unchanged. Run 7965 then killed source mobile 4055 for 100 XP,
recovered and pouched the purple sanctuary potion, sacrificed the corpse, and
returned safely. A nearby source snake and wandering warriors were observed
but not attacked; the post-objective hazard guard was not triggered. Aeloria
is level 17 at 134,057 XP with 20,393 XP to level 18. Run 7967 then
source-located Aruncus the Druid, considered him an easy kill, used the mage
familiar as the opener, and earned 169 total XP including a critical hit.
Aeloria collected the druidic staff and other drops, sacrificed the corpse for
silver, and returned full to healer room 3054. She is now level 17 at 134,178
XP with 20,272 XP to level 18. This is fresh level-17 continuation and
maintenance evidence, not subclass or HERO proof. Run 7968 safely healed and
discarded a cursed amulet, but the live Magic Shop rejected a source scroll;
the source prototype and shop metadata agree, so this remains a runtime-state
sale discrepancy rather than a guessed route. Runs 7969-7970 recorded a
crowded Moria circuit and a below-band secretary, both safely skipped. Run
7971 then showed that a live level-13 ranger can outlast an unprotected mage
despite a useful consider result; Aeloria withdrew at 43/209 HP for a 48 XP net
loss, survived, and returned full to healer room 3054. That exact Wyvern's
Tower policy is quarantined for this reboot. Aeloria is now level 17 at 134,178
XP with 20,272 XP to level 18. This is fresh level-17 combat-boundary evidence,
not subclass or HERO proof. Runs 7972-7975 completed rearm, liquidation, and
provision maintenance safely. Run 7973 killed source mobile 300, Aruncus the
Druid, for 246 objective XP. Run 7976 then killed source mobile 6310, the Bird
Spider, safely but received 0 XP; the merged evidence now records
`low_reward=true`, and the selector excludes it from productive repeats. Run
7977 rotated to source mobile 1131, the Shire receptionist, received a negative
live consider, and skipped safely. Aeloria is now level 17 at 134,444 XP with
20,006 XP to level 18, full in healer room 3054. The full offline suite passes
2,762 tests. This is fresh level-17 continuation evidence, not subclass or
HERO proof; direct live validation of the post-objective poison boundary remains
open. Runs 7978-8002 then rotated through negative considers, source identity
ambiguity, coin-stash funding, flight maintenance, absence, and crowd gates
without unsafe combat. Run 7988 killed Fewmaster Toede for 277 objective XP;
run 7997 killed the source giant for 495 objective XP. Runs 7992-7993 withdrew
from the Arachnos guardian and Dwarven Nobleman after their health floors,
paying bounded 208 XP losses that quarantined those exact policies. Run 8003
exposed a separate giant boundary: the live room contained the target plus two
guards, and Aeloria's melee attempt withdrew at 108/209 HP, losing 208 XP for
114 damage credit. Run 8004 then exposed that an aggressive source poison
target loaded five-plus levels below Aeloria could still auto-aggro on room
entry through the audited-special fallback; it withdrew safely but lost 208 XP.
The selector now blocks aggressive source targets whose minimum fuzz level is
below the useful-XP floor, including special-procedure candidates; the focused
regression and full suite pass 2,763 tests. Aeloria is now level 17 at 134,806
XP with 19,644 XP to level 18, full in healer room 3054. These are fresh
level-17 boundary and repair checkpoints, not subclass or HERO proof. Runs
8005-8011 then exercised blocked-shop funding. Run 8006 found the Haon Dor
Shargugh absent; run 8007 killed John the Lumberjack for 60 XP and acquired
saleable gear, and run 8008 liquidated it safely. Runs 8010-8011 recorded two
more bounded absences without death or XP loss. The funding loop exposed that
productive funding kills did not age the flight retry cooldown; the repair now
counts positive-XP provision funding for that cooldown, and the full offline
suite passes 2,765 tests. Direct live validation of that liveness repair remains
the next field task.
Runs 8012-8017 then completed a source-backed funding, liquidation, flight,
sanctuary, and guardian rotation; Aeloria reached 135,968 XP after an
822-XP guardian kill with no death or XP loss. Run 8018 exposed the remaining
Moria ordering gap: the large hobgoblin was killed and purple sanctuary potion
VNUM 4050 was acquired, but the already-present source snake VNUM 4053 with
`spec_poison` was noticed only after combat began, costing 208 XP on recall.
The new endpoint gate rejects that audited hazardous bystander before a
required-loot fight; focused and full offline coverage now pass 2,766 tests.
Run 8019 then skipped a crowded Dwarven Home endpoint before combat and
returned Aeloria safely to healer room 3054 at level 17 and 135,850 XP. This
is fresh boundary and repair evidence, not level-18, subclass, or HERO proof;
direct live validation of the new pre-combat Moria gate remains open.
Run 7711 provided 814 objective XP from source mobile 4517; runs 7712-7714
completed banking, liquidation, and healer recovery safely. Runs 7715-7716
checked distinct Shadow Keep Wraith prototypes and found both absent without
XP change. Run 7718 added 381 objective XP from source mobile 3142; run 7719
then recorded an absent Haon Dor Shargugh target and a safe healer return.
Run 7721 exposed a post-objective Moria pursuer ordering defect and a 990-XP
loss from repeated flee/recall commands; run 7722 added 787 objective XP from
source mobile 4517. The repaired live-VNUM gate is covered by regression tests
and awaits direct Moria live revalidation. Runs 7723-7725 then completed safe
maintenance and an absent New Ofcol probe without changing XP or death state.
Run 7726 added 286 objective XP from source mobile 3142; runs 7727-7728 then
checked both Shadow Keep Wraith prototypes and returned safely.
Runs 7729-7731 completed additional sanctuary/Midgaard rotation safely without
XP change; the direct Moria repair proof remains pending.
Runs 7732-7735 then completed four bounded Aeloria segments, adding 593 XP
without death and returning safely to the healer. The interrupted third batch
was reconciled as a resumable boundary after an operator monitoring mistake;
runs 7737-7739 then completed safe return-home, Ambush absence, and New Ofcol
absence checks. The live Moria VNUM repair remains pending direct reproduction.
Run 7740 completed bounded provision restock and left Aeloria safe at the
healer. Cleric campaign run 7741 added 508 XP through the generic Mud School
executor and returned Corararfen safely to healer room 3054 at level 3; this is
early cross-class evidence, not level-11 or HERO proof. The full offline suite
now passes 2,761 tests, including all 18 source-legal subclass handoff pairs.
The later bounded continuation resumed an interrupted Mud School boundary,
returned Corararfen safely to the healer at 7,841 XP, and left the campaign
ready for the next invocation. Aeloria likewise completed a source-ranked
level-16 hunt in run 7825, earning 446 objective XP from source mobile 3142 and
quitting full at the healer; neither result is a HERO claim.
Run 7892 exposed a runtime-boundary failure after a Moria snake poisoned
Aeloria: cleanup attempted recall from POS_INCAP after she had fled at 1 HP.
Run 7893 recovered the resulting corpse through Purgatory and returned safely
to healer room 3054, with a 3,799-XP death loss. The starter now recalls as
soon as GMCP reports active poison in a recallable field room, raises the
withdrawal floor for no-recall poison encounters, waits on POS_STUNNED and
below, and refuses unsafe save/quit cleanup. Runs 7894-7898 then completed
safe Shadow Keep, elite-goblin, liquidation, return-home, and Crystalmir
segments without another death or XP loss. The exact poisoned-Moria trigger
still needs a direct live re-entry; ordinary post-field cleanup is validated.
Runs 7833-7843 then exercised the 180-second reset handoff and recorded clean
source absences in Ambush, Shadow Keep, New Ofcol, and Haon Dor. Moria
observation found its two large hobgoblins wandering in The maze and The large
cave. Run 7844 live-validated the mage-only deep recovery path through the
source snake room under bounded invisibility and acquired purple sanctuary
potion VNUM 4050. Run 7845 then consumed that reserve before an audited ranger
fight and earned 445 XP without death or XP loss. Run 7848 safely attempted
replenishment but found the carrier absent; runs 7849-7850 added safe no-progress
observations. The selector now permits a fresh level-16+ fixed non-combat
research probe during sanctuary cooldown without overriding live absence,
crowd, or cleared-policy evidence. Run 7853 selected the source-ranked New
Ofcol jack at room 617, confirmed it absent, and returned Aeloria safely at
full HP and mana without XP change. Aeloria remains level 16 at 125,752 XP in
healer room 3054. This is resource-recovery and continuation evidence, not
level-17 or HERO proof.
Run 7826 also repaired legacy sanctuary-acquisition evidence, reacquired a
source-verified purple potion for Kestrel, and returned her safely to the
healer. Its 100 XP came from the below-band resource carrier and is not a
current-band progression claim.
Shared campaign SQLite storage uses WAL journaling, a bounded busy timeout, and
immediate state-snapshot commits so concurrent character workers do not hold a
write transaction across a live segment. Named HERO resumes also search nested
validation workspaces by stored manifest identity, avoiding duplicate campaigns
when a matrix character is resumed by name. If several matching manifests exist,
the resolver selects the closest stored campaign horizon that satisfies the
requested target and never lowers an existing target; equal-horizon duplicates
remain an explicit error. The fixed resolver was live-checked with Corararfen:
a target-5 request resumed the validation campaign while preserving its target
10 in both YAML and SQLite.
The next automatic reset retry (run 7817) completed sanctuary recovery safely
but acquired no potion and preserved Aeloria's protection marker. Campaign
segment 7391 (run 7822) then reopened the independent source-ranked frontier
during sanctuary cooldown and killed source mobile 3142, the Midgaard
secretary, for 354 objective XP. Aeloria returned to healer room 3054 at
201/201 HP and the protection marker remained intact. This validates the
liveness fallback, not level-17 or HERO completion. Segments 7392-7393 (runs
7823-7824) then recorded a live Haon Dor absence and a bounded Ambush no-kill
result, both returning Aeloria safely to the healer with no XP change.
Earlier evidence recorded 2,718 tests. Fresh
direct `hero` character Velnor has reached level 2 and resumed
without a password argument through multiple safe checkpoints. Aeloria is
checkpointed. Run 7617 proved source-verified amber `cure light` use at low
combat health, then recorded a guardian hard-health-floor death followed by
successful corpse and healer recovery; that exact policy is now protection-
quarantined. Runs 7638, 7653, 7658, and 7665 repeatedly proved the outdoor mage
familiar opener: Aeloria summoned and grouped the source-defined pony, ordered
it onto exact Bardoosh targets, earned 177, 233, 191, and 191 objective XP, and
returned to the healer unharmed each time.
The human psionic validation campaign has reached level 3 through
the same generic early progression path.
The latest continuation also keeps Fenanallor, a human male ranger, at level 4
and 7,565 XP with a primary dagger and ranged bow preserved in separate
structured slots. Praorquilmor, a human female brawler, reached level 3 at
4,149 XP through the shared Mud School arena without a weapon-repair detour.
These are fresh generic early-progression checkpoints, not level-10, subclass,
or HERO proof.
Aeloria run 7495 completed a bounded Grove probe and returned safely without an
objective kill. Kestrel run 7496 completed a bounded Mirror Realm probe and
returned safely without an objective kill; her next invocation remains bounded
by current-reboot fame-recovery evidence. Dorrik remains safely checkpointed at
level 24 while his remaining frontier is blocked by explicit timeout,
protection, or cooldown evidence. The source-ranked no-progress fallback now
remains available during ordinary resumptions after all other safe pools are
exhausted; it still cannot override live absence, crowd, route, consider,
protection, resource, identity, or cooldown evidence.
Aeloria run 7497 then found a source-matched Old Thalos caster target and
returned safely without claiming XP because one purple potion was insufficient
to cover both sanctuary and blindness recovery. The selector now requires a
trained cure blindness capability or a two-potion reserve before opening either
audited caster-special route; this closes the mismatch between source ranking
and the field runner's safe withdrawal rule.
Aeloria run 7498 then skipped that unsafe route, killed the source-matched
Midgaard secretary for 315 objective XP, and returned full to healer room 3054.
The public HERO workspace then reused Aeloria's stored credential and completed
runs 7499-7513 without manual steering. Runs 7515-7574 continued the generic
source-ranked rotation and crossed Aeloria to level 16. Run 7574 recorded the
transition at 114,836 XP. A new faerie-fire training priority then exposed a
stale practice-deferral issue; the revision-aware marker repair forced one
fresh class-trainer audit. Run 7583 trained `faerie fire` at the live mage
trainer, run 7584 cast it once before eight `chill touch` rounds and killed the
Shire receptionist for 405 objective XP, and run 7585 added 483 objective XP
from Aruncus. Aeloria was safely at 116,717 XP at that earlier checkpoint. This
is live level-16 continuation evidence, not subclass or HERO proof.
A pre-repair run 7547 exposed an endpoint race: two live on-duty guards were
reported by `Char.Enemies` while the aggressive arrival branch issued a spell
before crowd and source checks. The shared endpoint gate now waits for
source-identified GMCP, rejects duplicate or below-band targets, and preserves
generic endpoints without source VNUMs. Live run 7549 then killed the
source-matched large hobgoblin for 243 objective XP and returned safely. Runs
7550-7574 continued the generic rotation with safe healer returns and crossed
the level-16 boundary. The suite then passed 2,699 tests before the later
pouch and recovery changes.
Aeloria's level-16 route rotation remains active, with individual
reboot-scoped crowd and safety gates handled by the selector. Kestrel's run 7376 died in a
sanctuary-protected fame fight after the aura expired against a still-dangerous
level-30 moose; run 7377 completed Purgatory recovery, and run 7379 reacquired
a purple sanctuary reserve in Moria and returned full; run 7380 then deferred
the fame route as crowded without another fight. Protection loss now
reevaluates both live health bars before allowing another attack.
Source-sensitive decisions use DD4 revision 7996722.

The latest bounded rotation kept all three active tracks safe in healer room
3054: Aeloria checkpoint 22997 recorded a live druidess relocation outside the
source-safe wander graph without claiming XP, Kestrel checkpoint 23001
preserved the fame-service cooldown, and Dorrik checkpoint 23006 retained the
Eastern Desert crowd retirement. A second immediate Dorrik invocation returned
checkpoint 23006 without creating another metadata-only row. A productive route
with a source-proven non-combat special may receive one sanctuary-backed retry
after a single XP-loss record; combat specials and repeated losses remain
quarantined.
Loss records carry their completed segment identity, so repeated startup repair
cannot manufacture additional losses.

The current continuation added an explicit research-status generic source-ranked
fallback for levels 81-100, after the fixed Ghost Town registry ends at level
80. This keeps the HERO path executable while late-band area policies are still
being researched; it is not a claim that those bands are live-verified. The
latest bounded live rotations are checkpoint 23010 for Aeloria (safe Grove
absence), 23014 for Dorrik (safe Mirror Realm absence), and 23018 for Dorrik's
next Highland crowd rotation. No campaign worker remains after those runs.

All characters share `runs/dd4tester.sqlite3`. `RunStorage` configures a bounded
30-second SQLite busy timeout so overlapping character rotations wait briefly
for a commit instead of failing on transient write contention; a live worker is
still bounded by its segment timeout. Each campaign also claims an OS-backed
lease keyed by its database and config before opening SQLite, so duplicate
launches fail immediately instead of recovering an active segment.

On 2026-08-17, Dorrik's startup-repair path was live-validated against a
crowded Dwarven route. Checkpoint 22805 retained the explicit same-reboot
route retirement; a second reconnect returned the same checkpoint without
creating another metadata-only checkpoint. This proves restart idempotence,
not progression to HERO.

The same continuation then exposed a maintenance-state attribution bug. Runs
7381-7383 safely exercised provision funding and return-home while a missing
GMCP exit and a bounded runtime return were recorded; those maintenance
observations could overwrite the prior field policy's transient metadata. The
campaign now records new maintenance route hazards separately, preserves
source-owned field evidence, and repairs legacy unowned markers on resume.
Kestrel's resume checkpoint 22899 live-confirmed the cleanup. The full offline
suite passes 2,678 tests. This is checkpoint-integrity evidence, not HERO
completion evidence.

Run 7384 then resumed the mage frontier and killed the source-matched Midgaard
secretary (mobile 3142) for 494 objective XP; Aeloria reached 107,709 XP at
level 15 and returned safely. Runs 7385-7388 completed healer return, an absent
Shargugh locator, and liquidation without false XP. Dorrik's bounded retries
22908 and 22910 re-evaluated Highland and stopped on the live crowd gate; no
level-24 XP claim is made for those checkpoints.

Run 7389 live-validated explicit `--retry-stalled` recovery: the generic
selector reopened the fresh Mirror Realm route, confirmed its young-boy target
was absent, returned Dorrik safely to healer room 3054 at 360,891 XP, and
persisted reboot-local absence evidence. A normal invocation remains a safe
stop while the remaining routes are blocked; retry mode rotates to another
fresh source-safe route instead of replaying the absent target.

Run 7390 completed that rotation in SQLite before the outer command wrapper
timed out: the independent Mirror Realm guardian route was live-crowded, made
no XP claim, and returned Dorrik safely to healer room 3054. The persisted
segment is authoritative; a wrapper timeout is not treated as a hung campaign
when the segment has already checkpointed successfully.

Run 7391 kept the mage rotation safe when New Ofcol was absent, returning
Aeloria to the healer at level 15 and 107,709 XP. Kestrel checkpoint 22941
then preserved the fame-recovery cooldown and left her safely in healer room
3054 without another shop or combat attempt.

The 2026-08-17 retry-stalled repair then closed two cooldown bypasses. Current-
reboot absence, crowd, route, and failed-viability evidence now forces source
frontier rotation even when `--retry-stalled` is supplied; an explicit retry
cannot clear active research evidence. Only an automatic retry marked after a
completed area-reset wait may consume that evidence. Live checkpoints 22948
through 22954 retained Dorrik's Eastern Desert crowd result at cooldown 3 and
created no duplicate field segment or XP claim. The campaign-specific suite
passes 818 tests and the complete offline suite passes 2,678 tests. This is a
safe-stop and selector-integrity result, not HERO progression evidence.

Run 7376 is retained as failure evidence rather than hidden progress: Kestrel
died at 220/334 HP while the moose remained at 410/535 HP. The executor now
withdraws from that materially stronger matchup after sanctuary expires, while
still allowing a near-dead opponent to be finished. Runs 7377-7379 completed
Purgatory recovery, healer recovery, and a bounded Moria sanctuary-reserve
continuation; Kestrel is safe at healer room 3054. These are continuation and
repair checkpoints, not a HERO completion claim.

Run 7283 exposed a real live failure: the randomized Great Eastern Desert
walker restarted its depth-first search after every successful backtrack and
cycled between three rooms until the worker was stopped. The walker now
preserves its visited graph and explores the next parent branch. Run 7284
recovered the resulting Aeloria death through Limbo and the protected corpse,
recording a 3,623-XP loss. The Eastern Desert route is quarantined for this
reboot. Live CLI campaigns now default to a 180-second segment cap plus a
60-second local setup budget and 45 seconds of cleanup grace, so an operational
stall is checkpointed instead of waiting indefinitely. Nested transport
timeouts are not treated as launcher expiry.

Runs 7285 and 7286 then resumed generic current-band execution: Aeloria killed
the Miden-nir goblin leader for 294 objective XP and the Shire receptionist for
330 objective XP. The first route also recorded 167 incidental XP loss after an
unapproved attacker joined; the second returned cleanly after acquiring a
usable body part. Net progress across both runs was 457 XP, leaving her 12,460
XP short of level 16.

Run 7291 was a residual selector-regression invocation after the timeout marker
was cleared: it produced only 50 incidental XP from a transit dark dwarf and no
Eastern Desert objective kill. Run 7292 restored the timeout marker from history
and selected liquidation instead, leaving the route quarantined for this reboot.
Aeloria is now 12,013 XP short of level 16.

Run 7294 then killed another source-matched Shire receptionist for 431
objective XP without an XP loss or death. Run 7298 added a further 368-XP
receptionist kill after addressing hunger during recovery. Aeloria is now 11,214
XP short of level 16. Run 7301 added a further 369-XP receptionist kill and
acquired a usable body part; Aeloria is now 10,845 XP short of level 16. Run
7304 added a further 414-XP receptionist kill without an XP loss or death.
Aeloria is now 10,431 XP short of level 16. Run 7310 then added a 272-XP
receptionist kill without an XP loss or death. Aeloria is now 10,159 XP short of
level 16. Run 7313 then added a further 333-XP receptionist kill without an XP
loss or death; Aeloria is now 9,826 XP short of level 16. Run 7321 then added a
further 368-XP receptionist kill without an XP loss or death; Aeloria is now
8,844 XP short of level 16. Run 7324 then withdrew from an incidental fight at
the hard health floor: it recorded 167 XP loss, 58 net incidental XP, and no
objective kill before returning safely. Aeloria is now 8,786 XP short of level
16, and the exact route is quarantined for rotation. Run 7328 then produced five
Eastern Desert kills for 380 XP, including successful dropped-weapon recovery
after a disarm; Aeloria returned safely at 187/193 HP and was 8,406 XP short
of level 16. Run 7332 added only a 50-XP dark-dwarf contact, and run 7338
repeated the 146-room Forest absence without combat. The retry-marker guard in
`dd4tester/campaign.py` now keeps that absent route closed after minimum-value
contact; the full offline suite passes 2,662 tests. Run 7343 then added a clean
358-XP young dragon wormkin kill; Aeloria is now 7,998 XP short of level 16.
Run 7344 then added a clean 233-XP huge python kill; Aeloria is now 7,765 XP
short of level 16.

Runs 7349-7366 then exercised safe absence, provisioning, liquidation, and
bounded no-progress rotation paths without deaths or false XP. Run 7351 killed
a drider for 90 objective XP, and run 7367 killed a goblin leader for another
90 XP; Aeloria is now 7,585 XP short of level 16. The selector now retains the
full bounded same-reboot no-progress history and does not wait on
crowd-exhausted routes; the full offline suite passes 2,664 tests.

Runs 7369-7372 then bounded Kestrel's negative-fame recovery. The Magic Shop
listed a light blue potion at the reboot-local price of 135 copper, but the
wizard explicitly refused service; the next purchase retry was blocked by a
wandering drunk before any duplicate purchase. Run 7371 reached the Circus
ticket clerk, consumed sanctuary, and withdrew at the configured 39% health
floor, losing 319 XP but returning safely. Run 7372 found the Mirror Realm
moose without a sanctuary reserve and recalled before combat. The runner now
treats the refusal as a hard shop boundary, permits a non-shop fame route only
with verified sanctuary, and stops a flight-only fallback instead of retrying
the refused shop. These are safe research probes, not fame-kill proof.

Run 7373 then resumed Kestrel through the generic source-backed food reserve
route. It acquired the exact chunk-of-venison object (VNUM 5219), returned full
to healer room 3054, and logged out without XP change, combat, or another shop
attempt. Aeloria checkpoint 22766 and Dorrik checkpoint 22769 both recorded
crowded current-band rooms and deferred safely for area reset. The live
rotation is therefore continuing from durable checkpoints rather than stacking
workers or forcing an unsafe fame fight.

Runs 7220-7229 exposed and repaired two live ordering failures: ambiguous gear
descriptions could make a stance alternate between two object prototypes, and
a fixed shop route could advance from stale prompt text before GMCP confirmed
the new room. The repaired run sequence validated exact worn-object identity,
completed a Queen Wasp kill for 374 objective XP, then killed the Giant Kodiak
bear for 280 objective XP and crossed Aeloria to level 15. Run 7231 added 528
objective XP from Bardoosh. Runs 7230 and 7232-7235 completed bounded
level-15, maintenance, and no-objective rotations safely. Run 7236 then killed
Aruncus the Druid for 413 objective XP and returned safely to healer room 3054.
Runs 7237-7270 then added 5,354 objective XP from Bardoosh, Bird Spider, and
Queen Wasp kills, offset by two source-policy hard-floor withdrawals totaling
190 XP and 20 incidental XP. Aeloria then reached 105,430 XP before the
quarantined Eastern Desert stall and its recovery loss; she is now 12,917 XP
short of level 16. These are
continuation checkpoints, not a HERO claim. The earlier run ledger is
historical:
Run 6936 exposed a source-
audited gas-breath target above Dorrik's live level ceiling; the selector now
rejects that class of target before launch. Run 6938 recorded a Swamp Wraith
kill but a 385-XP flee penalty from three below-band Mistlings in the Mahn-Tor
return maze, and the return branch now handles that bounded interruption in
combat. Run 6940 then added 170 XP on the Eastern Desert worm route and returned
Dorrik safely. Runs 6941 and 6942 then added 933 and 1,177 XP through the
Kerofk gravedigger and Old Thalos mayor with safe healer returns and no XP loss.
Runs 6948-6950 then completed a bounded generic continuation: run 6949 killed
the source-matched Mirror Realm watchman for 873 XP, while runs 6948 and 6950
correctly withdrew from crowded circuits without forcing combat. All three
returned safely with no death or XP loss. Runs 6951-6960 then added 1,988
aggregate XP, including a 636-XP Mirror Realm watchman and a 1,352-XP Kerofk
route; absent and crowded targets were skipped without XP loss. Run 6963
exposed a timed sleeping-recovery watchdog gap during flight maintenance; the
starter now reopens the prompt gate when the scheduled health check is due.
Run 6964 live-validated the repair by buying and activating flight with no XP
loss. Run 6965 completed a bounded Abyss route with its registered target
absent; run 6966 earned 460 incidental XP from three low-risk Kerofk
interruptions and returned Dorrik full to healer room 3054. Runs 6967 and
6968 exposed the same Abyss return hazard, while run 6971 live-validated the
repaired return graph. Runs 6981 and 6982 recorded bounded 149-XP and 16-XP
net losses; the finisher now permits one source-admitted final action against
a target up to one level higher at 35% health or less when the observed
one-hit reserve is covered. Run 6983 added 450 incidental XP and run 6987
exposed a held earthquake staff on the otherwise noncombat priest of Thalos.
Candidate ranking now rejects source-equipped scrolls, wands, and staves until
their spell behavior is audited. Runs 6994-7004 added productive Moria, Mirror
Realm, and Canyon evidence; run 7004 consumed the sanctuary reserve after a
1,256-XP objective kill. Runs 7008 and 7014 added 886 and 799 objective XP
from source-matched Mirror Realm watchmen. Run 7013 withdrew from Dwarven
Homestead at the explicit 27% health floor after 179 incidental XP, without
death or XP loss. The Moria recovery circuit now uses one reset-room stop plus
eight bounded source-room edges; it is live acquisition verified. Runs 7009-7011
and 7015
completed maintenance and a safe zero-kill probe. Run 7019 then live-validated
the split Moria recovery circuit through rooms 4064 and 4063, acquired the
purple sanctuary potion from the source-matched carrier, placed it in the
combat pouch, and returned full. Run 7022 added 683 objective XP from the
Tentusks treant and consumed the reserve; run 7023 reacquired a purple potion
through Moria with 90 incidental XP. Runs 7024-7026 safely rotated protected
Mirror routes without forcing absent targets. Run 7027 killed the source-matched
Dwarven Home host for 1,938 objective XP and returned full with the sanctuary
reserve intact; run 7029 reacquired the reserve with 90 incidental XP, and run
7030 safely skipped a wandering Mirror Realm gardener outside the source-safe
relocation graph. Run 7031 withdrew from the source-matched Solace Sergeant at
Arms at the shared 30% health floor after sanctuary expired, recording a 385-XP
flee loss; run 7032 restored full healer recovery. Run 7033 reacquired the
sanctuary reserve with 100 objective XP. Run 7034 safely skipped a crowded
Mirror Realm target without combat. Run 7035 then killed the source-matched
Dwarven Home host for 1,520 objective XP without consuming the reserve. Run
7038 exposed a same-name Grove VNUM race between wandering mobiles 8900 and
8901 and caused a 385-XP flee loss before GMCP identity arrived. The runner now
uses source-graph reachability to skip ambiguous same-name targets before
`consider` or `kill`; run 7039 restored the sanctuary reserve with 140 total
XP, and run 7040 added 1,465 objective XP from the Dwarven Home host. Dorrik
is now 15,053 XP short of level 25. Run 7041 recorded a safe zero-kill Mirror
Realm rotation, run 7042 live-validated the pre-combat same-name VNUM guard at
Grove room 8906 without combat or XP loss, and run 7043 added 1,410 objective
XP from the Dwarven Home host. Run 7049 exposed a `spec_cast_cleric` cyclops
that blinded Dorrik after sanctuary expired and caused a 39-XP net loss before
safe healer recovery. Source audit now requires a verified cure-blindness route
before status-casting hunts, retains a second matching potion when sanctuary
would consume the first, and uses the cure before fleeing when blindness is
active. Runs 7050 and 7051 then completed safe recovery and Dwarven Home
rotations without reaching that candidate; the repair is offline-verified and
still awaits a live trigger. Run 7055 then live-tested the source-matched
Weeping Willow at a perfect consider; the shared 35% health floor fired after
the target reduced Dorrik to 137/542 HP, producing a 213-XP net loss after the
flee charge. Runs 7056-7059 recovered and rotated through Dwarven Home, Shire,
flight, and Tentusks without another loss. Run 7060 then reopened the Dwarven
Home host route; Dorrik withdrew at 124/542 HP after earning 602 damage-credit
XP, paying the 385-XP flee cost for a 217-XP net gain without an objective kill.
He returned safely to healer room 3054 at 480/542 HP, full mana and movement,
with hunger 4 and thirst 42. Runs 7063-7066 then exercised the next protected
frontier: run 7063 killed the source-matched New Ofcol teller for 1,119
objective XP with a 20-XP below-band drunk interruption; run 7064 withdrew
from the Drow weapons master at 43/542 HP, losing 385 XP after 23 damage-credit
XP. Run 7065 replayed the Canyon `spec_cast_cleric` cyclops with sanctuary
active, then withdrew at 80/542 HP after its harm spell outlasted the aura for
a 117-XP net loss. Audited special routes that fail after sanctuary are now
quarantined for the reboot. Run 7066 reacquired the purple reserve from the
source-matched large hobgoblin for 100 objective XP, pouch-stowed it, and
returned full to the healer. Runs 7081 and 7092 repeated the Drow weapons
master route under its two-mobile crowd: the first lost 210 XP, and the
sanctuary-protected retry lost 265 XP at the 39% health floor. The exact route
is quarantined for this reboot. Run 7083 hit the 180-second segment boundary
during a deferred Mirror Realm search and run 7084 returned Dorrik safely; the
starter now clears stale crowd and locator waits before its runtime return
boundary. Runs 7085-7091 completed flight, New Ofcol, Moria, and bounded absence
maintenance. Run 7095 then killed the source-matched New Ofcol teller for 934
objective XP and returned full to healer room 3054 at 358,980 XP. The full
offline suite passes 2,648 tests. These are continuation
checkpoints, not a HERO claim. Runs 6784,
6786, 6788, 6790, and 6795 supplied productive source-ranked
kills for 736, 893, 739, 1,040, and 881 XP, respectively, with safe healer
returns. Runs 6785, 6787, 6789, and 6794 recorded bounded Mirror Realm zero-kill
or absence results without forcing combat; run 6793 refreshed flight and run
6796 restored hunger from 2 to 39, and runs 6797-6799 completed liquidation,
safe rejection of a non-corporeal funding target, and restock. The campaign now
persists deferred practice
types so it does not repeat
a fruitless class-trainer trip, while still allowing newly unlocked damage
gateways to reopen. The level-20 shifter trainer has a source-derived Kerofk
locator route with bounded stale-result retries. Live level-20 and level-30
subclass proof remain outstanding. Runs 6800 and 6801 then added 875 and 857
objective XP from the source-matched Kerofk gravedigger and Old Treant. The
next Mirror Realm segment was stopped after an outer watchdog stall and
recovered as ready with explicit interruption evidence; run 6803 returned
Dorrik safely home without XP loss. Run 6804 then added 891 objective XP from
the Kerofk gravedigger, and run 6805 completed liquidation and full healer
recovery at room 3054. Run 6807 added 784 objective XP and run 6812 added 534
objective XP through the generic Old Treant route. Runs 6806, 6809, 6810,
6811, and 6813 recorded bounded no-kill rotations; run 6808 refreshed flight.
Run 6814 withdrew from a Shudde-M'ell interruption after the live level gate,
lost 354 XP, fed the character from 5 to 40 hunger, and quarantined the exact
Plains North policy for three same-reboot segments. Run 6815 then killed the
source-matched Swamp Wraith in the alternate Mahn-Tor circuit for 1,060 XP,
and run 6816 restored full movement at the healer; Dorrik is now at 313,440 XP.
Run 6817 then completed a bounded Mirror Realm zero-kill probe and returned
safely with no XP change. Runs 6818, 6827, and 6824 then added 726, 637, and
884 objective XP through source-ranked Old Treant and Swamp Wraith routes. Run
6824 exposed two 354-XP flee penalties from source-known below-band Mistlings
in the Mahn-Tor no-recall return maze. The shared return policy now fights that
narrow class of safe interruption and resumes the live-GMCP exit graph; 38
focused tests and the full offline suite cover the repair. This exact live
post-repair branch remains to be re-triggered, so these are continuation
checkpoints rather than a HERO claim. Runs 6832 and 6835 added 1,053 and 1,083
XP through the generic gravedigger route; run 6833 added 894 XP from Old Treant,
and run 6834 rejected a crowded Mirror route without XP. Dorrik is now 9,361
XP short of level 24 and is full on HP, mana, and movement in healer room 3054.
Runs 6836 and 6839 were bounded zero-XP maintenance or Mirror rotations; run
6837 added 608 XP from Old Treant, run 6838 withdrew at the health floor with
208 net XP, and run 6840 added 150 XP from the Arachnos guardian. Hunger is
now 2, so provision recovery is the next gate before another field launch.
Run 6841 then restored hunger to 38 while adding 716 XP from Old Treant. Runs
6842-6845 recorded bounded Mirror, Crystal, Sentinel, and Abyss results without
forced targets; run 6846 refreshed flight. Run 6847 retained a repeated
no-policy-decision watchdog failure, and run 6848 reconciled it successfully.
Dorrik is now at 320,558 XP, 6,992 short of level 24, and remains safe at
healer room 3054. Run 6853 recorded an absent Highland candidate without XP;
run 6854 added 646 XP from Old Treant; and run 6855 found Nessy's child but
withdrew when the adult Nessy joined, paying the 354-XP flee cost. The exact
Highland policy was quarantined and Dorrik is now 6,389 XP short of level 24.
Run 6856 then added 1,325 XP from the source-matched Maid; run 6857 sold four
items for 291 coins; and run 6858 recorded another bounded Mirror zero-kill
result. Dorrik was then 5,064 XP short of level 24. Runs 6878-6881 validated
the new one-attempt source-route exclusion: an empty Mirror route rotated to
flight maintenance and Old Treant for 633 objective XP, clearing the marker.
Run 6883 acquired sanctuary from the large hobgoblin, run 6887 added 760 XP
from Old Treant, and run 6895 withdrew from Dwarven Homestead at the health
floor for a 189-XP loss without death. Run 6896 recorded the subsequent
bounded Mirror absence. Dorrik is now level 24 at 331,164 XP, 34,936 short of
level 25, full in healer room 3054. Runs 6897-6925 continued bounded
source-ranked rotation; run 6921 added 802 objective XP from the Old Treant
and run 6923 added 1,367 objective XP from the New Ofcol Dragonhoard teller.
Run 6926 exposed a live endpoint-gate bug when the level-19 Goblin Caves
Sentry was attacked at Dorrik's level-24 useful-XP floor despite being recorded
below-band and non-objective. The starter now withdraws before attacking such
an endpoint target, except for an explicitly source-allowed resource or
required-loot stop. Run 6927 live-validated the repair by avoiding the Sentry;
runs 6928-6935 continued bounded no-objective rotations and safe healer
returns. These are continuation checkpoints, not a HERO completion claim.
Aeloria run 6763 then completed a zero-kill Wyvern/centaur probe and returned
full to the healer, preserving absence evidence without claiming progression.
Earlier continuation detail: run 6747 exposed an optional daycare-ring absence watchdog; the
campaign reconciler now quarantines that route and persists its level/boot
cooldown, with run 6748 live-validating rotation to a safe return-home segment.
Runs 6749 through 6754 then resumed Aeloria and Dorrik without manual target
steering: Dorrik's run 6751 recorded 860 incidental XP, run 6752 slept at the
healer from 133/370 to 370/370 movement, and Aeloria's run 6750 killed the
source-matched goblin leader for 302 objective XP before an unapproved attacker
caused a net checkpoint increase of 154 XP. Runs 6753 and 6754 recorded absent
Shargugh and Wraith targets without forced combat. Run 6594 then
live-validated the generic starvation override:
Dorrik acquired and ate the source-matched rabbit roast, raised hunger from -7
to 17, and returned alive to healer room 3054 with 481/489 HP. The current
read-only DD4 checkout is `7996722`. Run 6598 added 543 objective XP to Aeloria
through the source-ranked Shire receptionist route and returned her fully
recovered to healer room 3054. Runs 6602 and 6603 then added 450 objective XP
to Dorrik and completed full healer recovery in room 3054. Aeloria run 6616
added 221 net XP after a protected Wyvern withdrawal; 6617 then rotated safely
through Shadow Keep. Runs 6620 through 6623 and 6628 through 6635 added
1,780 objective XP to Dorrik and left a five-pie plus rabbit-leg reserve in
his inventory. Aeloria run 6650 added 371 XP through Gremlin Lair and returned
her safely; run 6658 added 330 objective XP through Plains North, and run 6659
completed bounded loot liquidation. Run 6663 recorded a -38 XP Shire withdrawal
and run 6664 selected Shadow Keep without repeating it. Dorrik run 6653 added
280 XP through Solace, run 6656 added 130 XP through Mirror Realm, run 6657
completed full recovery, and run 6661 returned him safely after bounded
liquidation. Run 6665 then added 130 objective XP through Mahn-Tor and left
him full in healer room 3054. Runs 6680 through 6690 then continued the
generic source-ranked rotation: bounded gravedigger research found no target,
the flight and liquidation paths completed safely, and the Shire and Mirror
Realm attempts recorded no objective kill rather than forcing absent or unsafe
targets. Run 6683 exposed a stale posture state after DD4 accepted wake but
omitted a position update from `Char.Vitals`; explicit sleep and wake text now
updates the local state. Dorrik recovered to full resources at 285,451 XP and
352 movement in healer room 3054. The full offline suite now passes 2,614
tests. These are level-22 continuation checkpoints, not a HERO completion
claim. Runs 6691 through 6698 then completed the resumable maintenance and
return phases around three source-ranked probes. Mirror Realm watchman and
Dwarven routes did not prove their objective targets; one Dwarven route recorded
a reboot-local -163 XP loss and was quarantined, while incidental field kills
added 750 XP without being credited as objectives. Recovery returned Dorrik
full to healer room 3054 at 285,878 XP. The next policy phase remains persisted
for later continuation. Runs 6701 through 6706 then completed bounded flight,
Abyss, liquidation, and healer-return work. Run 6707 exposed that generic
high-band sanctuary recovery stopped after the short Moria reset-room probe;
the repaired dispatch now uses the source-room-guided deep circuit. Run 6708
acquired a purple sanctuary potion from the source-matched large hobgoblin,
stored it in Dorrik's verified combat pouch, and returned him to healer room
3054 at 287,128 XP with full HP and mana. The failed-hunt protection marker is
still pending until that hunt is retried under sanctuary. This is continuation
evidence, not a HERO completion claim. Runs 6709 through 6712 then exercised
the protected Ofcol retry, cleanup, healer movement recovery, and flight
refresh. Run 6709 refused a two-mobile crowd. Run 6713 used sanctuary on an
audited cleric-special cyclops route and withdrew safely after blindness made
continuation unsafe; run 6714 found both Moria carriers crowded. Run 6715
added 653 XP through an audited Highland route before an unapproved attacker
joined, and run 6716 restored Dorrik to full resources at 288,592 XP in healer
room 3054. The original protection marker remains pending and its reserve must
be reacquired before the exact failed hunt is retried. Runs 6717 through 6721
then completed Dorrik liquidation, a productive Arikasbab circuit, and safe
returns; run 6718 added 1,628 XP, including a 1,338-XP Maid kill. Aeloria
runs 6722 and 6723 completed bounded Ambush and Plains North probes without
objective XP. Kestrel runs 6724 and 6725 completed the reserve and Mirror
Realm probes without XP and returned him full to the healer. These remain
continuation evidence, not a HERO completion claim.
Runs 6730, 6735, and 6737 exposed stale wandering-target, repeated-room route,
and prompt-before-room event-order defects. The shared repairs now pass the
full offline suite. Run 6738 live-validated the repaired Moria route through
the level-20 trainer and official endpoint, earning 420 incidental XP without
claiming an objective kill. Run 6742 withdrew from a source-matched Dwarven
Home host at the health floor, preserving protection evidence. Run 6743 then
killed the source-matched level-20 gravedigger for 1,072 XP and returned
Dorrik safely to healer room 3054. These are continuation checkpoints, not a
HERO completion claim.
Run 6745 then handled a reboot-local Mirror Realm absence without forcing the
guardian objective: the neighboring reset proved source presence, while four
incidental route kills added 600 XP. Dorrik returned full to the healer at
295,215 XP, still level 23 and 32,335 XP from level 24.
Dorrik crossed level 14 on run 5246 after the level-13 source-ranked frontier, and
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

The live DD4 checkout used for the current audit is
`4d68421e67295cca1c04923d18273ca48a6476ce`. The packaged
prerequisite and training snapshots remain pinned evidence from `f703daa`, and
the fallback character catalog is pinned to `0482387`; source-sensitive policy
changes must record both the live checkout and snapshot revisions.

### Current status (2026-09-03)

The full offline suite passes 3,340 tests. The source-ranked long-route repair
separates the healer departure gate from later movement legs: Kestrel's Kerofk
route needs 73 movement to depart, then recovers at audited no-mob waypoints
before entering the target suffix. A new repair also preserves the official
outbound route cursor after an allowed harmless transit fight, instead of
asking the endpoint planner to reconstruct the route from the interruption
room. Both repairs are covered by focused and full-suite tests.

Dorrik is safely at level 25 with 378,748 XP in `runs/heroes/dorrik`, 29,302 XP
from level 26. Runs 11493, 11495, 11498, 11499, and 11513 supplied durable
XP-loss evidence from weak damage windows; runs 11496, 11497, and 11504 correctly
recorded crowded, absent, or below-band endpoints without claiming progression.
Run 11504 live-validated looting and route resumption after an incidental city
attack. Run 11507 then exposed two source-known below-band transit attackers on
the Kerofk route; the starter now allows up to three sequential, isolated,
special-free transit fights on source-ranked routes, with focused coverage and
the full suite passing. Run 11510 killed the exact Mirror Realm fisherman for
1,718 objective XP and returned safely. Run 11513 reached the exact Ki-Rin
endpoint but withdrew at the 32% health floor after the target proved healthier
than Dorrik, recording a 419-XP loss; the protection hold remained active and
the subsequent Moria recovery probe stopped safely without a target. The
current protection boundary requires sanctuary for a high-peak armed target
when disarm is not known. An unarmed one-level source-ceiling probe also now
requires its source HP ceiling to fit within current maximum HP unless a
protected path is available, based on the Ki-Rin loss evidence.
Kestrel is level 24 at 334,688 XP, Serevian level 11 at 49,938 XP, and
Praelarran is level 15 at 108,488 XP at checkpoint 34856. Praelarran's latest
live segment completed the exact Mahn-Tor circuit for 592 objective XP and
returned safely; the earlier segment supplied the route-resume failure
evidence and added only incidental XP. No character has reached HERO; this
remains executable
level-15-to-30 readiness and evidence work, not level-100 proof.

The `hero` command is a resumable execution boundary, not a claim that HERO is
already solved. It checkpoints and stops when the selected class and level band
has no executable policy. `verified` policies are repeatable evidence-backed
progress; `research` policies are bounded probes; `unavailable` policies are
explicit safe stops. No fresh character has yet completed an uninterrupted
level-0-to-100 run. The active work order is executable level-15-to-30 generic
progression, including training and the level-30 subclass handoff, followed by
the late-band access and combat work needed for levels 31-100. See the detailed
[progress audit](docs/PROGRESS_AUDIT_2026-08-13.md) and the historical
[roadmap](ROADMAP.md).

### Continue and inspect a campaign

Run `hero` again with the same identity and workspace to resume the existing
campaign. A bounded segment returns to a durable checkpoint when its runtime
cap expires; omit the cap for the normal resumable mode:

```powershell
python -m dd4tester hero --username Praelarran `
  --workspace runs/heroes/human-male-warrior-base `
  --segments 1 --max-segment-runtime 120
```

Use the stored campaign, run, and transcript commands to inspect what happened:

```powershell
python -m dd4tester show-campaign 30
python -m dd4tester show-state 10917 --history
python -m dd4tester show-transcript 10917
python -m dd4tester show-runs --limit 20
```

The numeric arguments are durable SQLite ids from the latest Praelarran
continuation. Replace them with the campaign or run you want to inspect. Use
`show-transcript <path> --raw` when
the JSONL records themselves are needed.

For a short live retry after an area-reset checkpoint, opt into one bounded
reset wait explicitly. `--max-segment-runtime` otherwise defaults reset retries
to zero so an inspection command returns promptly:

```powershell
python -m dd4tester hero --username Praelarran `
  --workspace runs/heroes/human-male-warrior-base `
  --segments 1 --max-segment-runtime 120 `
  --reset-retries 1 --reset-wait 180
```

The wait runs only after the character is safely back at the healer. A
`--retry-stalled` invocation rotates one trailing no-progress frontier but
does not erase current-reboot absence, crowd, route, consider, protection, or
cooldown evidence.

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
For a named character without an existing HERO workspace, the runner first
honors --password and DD4_<NAME>_PASSWORD, then performs a bounded lookup of
the stored character:<name> credential. It generates and stores a password
only when no existing credential is available, so wrapping an existing character
cannot silently replace its login password.
`--target-level` accepts levels 2 through 100 and updates a resumed campaign's
durable target without rebuilding its character workspace.

The default `hero` invocation is the resumable to-HERO mode: each StarterBot
segment remains bounded by the profile runtime, while empty-area checkpoints
receive the campaign's automatic reboot-reset retries. Supply
`--max-segment-runtime 180` (or another positive value) when you want a short,
explicitly bounded live probe; that mode intentionally returns at reset
checkpoints instead of waiting through them.

This command uses the existing verified and research-status policy graph. It
will checkpoint and stop safely only when the current policy graph or a safety
gate genuinely prevents continuation; extending verified class-aware coverage
through HERO remains ongoing work.
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

For source-legal coverage across every current race and base class, use the
checked-in `matrices/level-10-all-race-class.yaml`. It declares all 225 pairs
from the current DD4 catalog and alternates cosmetic female/male identities;
declared entries are not live proof until their campaigns checkpoint at level
10:

```powershell
python -m dd4tester matrix matrices/level-10-all-race-class.yaml --rounds 1 --segments-per-character 1
python -m dd4tester configure-matrix-passwords matrices/level-10-all-race-class.yaml
python -m dd4tester matrix-coverage matrices/level-10-all-race-class.yaml
```

Regenerate the matrix after a source-catalog change with
`python -m dd4tester prepare-validation-matrix --output matrices/level-10-all-race-class.yaml`.
The generated profiles and credentials remain local under `runs/`.

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
- `character_commands`: normalized commands observed during campaign runs.
- `character_acquired_items` and `character_item_backfills`: durable item
  identity and repair records used by equipment and loot policies.
- `loot_sales`: observed item/shop payouts scoped to character and DD4 reboot.
- `mob_kills`: observed target kills and XP scoped to character and DD4 reboot.
- `campaigns`, `campaign_segments`, and `campaign_checkpoints`: durable campaign
  status, policy-segment history, and resumable character-state checkpoints.
- `campaign_usage`: aggregate command, runtime, and segment usage accounting.

Inspect stored runs, transcripts, and character state with:

```powershell
python -m dd4tester show-runs
python -m dd4tester show-transcript 1
python -m dd4tester show-transcript transcripts/login-1.jsonl --raw
python -m dd4tester show-state 1
python -m dd4tester show-state 1 --history
python -m dd4tester show-campaign 1
```

Create a deterministic run report from the stored events and state snapshots:

```powershell
python -m dd4tester report 1
python -m dd4tester report 1 --format json --output reports/run-1.json
python -m dd4tester report 1 --output reports/run-1.md
```

Reports cover progression, failures, health and combat signals, structured
decision categories, safety interventions, and concise first-person commentary
derived from recorded evidence. Run context also retains each character's
non-secret title, description, and optional personality so reports preserve the
voice and identity that were configured at creation. They do not make AI
decisions or invent events.
The optional `reports/` directory is local output and is ignored by Git.

When a campaign reaches its target level, the runner also writes a durable
campaign report beside its YAML configuration:

```text
runs/heroes/<workspace>/hero-report.json
runs/heroes/<workspace>/hero-report.md
```

The campaign report aggregates checkpoints, segments, run ids, transcripts,
XP, kills, deaths, safety commentary, and the final location. Inspect or
regenerate one directly with:

```powershell
python -m dd4tester campaign-report 23
python -m dd4tester campaign-report 23 --format json --output reports/campaign-23.json
```

The report is evidence only: a HERO claim is valid when its target is reached
and its underlying runs remain independently source-backed and unsteered.
