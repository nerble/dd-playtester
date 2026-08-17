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
for all three representatives. Current anchors are Aeloria mage level 15 at
107,709 XP, Dorrik warrior level 24 at 360,891 XP, and Kestrel thief level 24 at
345,698 XP. The full offline suite passes 2,682 tests. Aeloria is checkpointed
alive in healer room 3054 at 193/193 HP, 533/533 mana, and 290/290 movement;
Dorrik and Kestrel are also safely checkpointed in that healer room. Aeloria's
level-15 frontier is temporarily crowd-gated. Kestrel's run 7376 died in a
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
still bounded by its segment timeout.

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
reboot. Live CLI campaigns now default to a 180-second segment cap plus 45
seconds of cleanup grace, so an operational stall is checkpointed instead of
waiting indefinitely.

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
`7996722bc43508cc3773c48f8d79e3d07d68e5e4`. The packaged
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
