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

Event batches are applied in order: each parsed event updates the reducer and
is then observed by policy before the next event is processed. GMCP room VNUMs
and arrival metadata are authoritative for repeated-room routes. A room change
also acknowledges a pending move when the prompt was emitted before the room
update, preventing valid routes from being mistaken for inactivity.

The durable SQLite database is shared by character rotations. `RunStorage`
opens it with a 30-second busy timeout, so concurrent campaign workers wait for
one bounded commit rather than treating transient write contention as a failed
character run. Segment runtime limits remain the outer liveness boundary, and
the database checkpoint is authoritative when a wrapper exits after a segment
has already committed.

## Policy Lifecycle

The selector must distinguish three states. `verified` is reusable executable
evidence. `research` is a bounded live probe with explicit route, combat,
resource, and return limits. `unavailable` is a durable safe stop explaining
what evidence or implementation is missing. A checkpoint, source catalog
entry, policy count, or research result is not a progression proof by itself.

The fixed research registry currently covers explicit routes through level 80.
At level 81 and above, `policy_for` returns the generic source-ranked hunt in
research status with a level-local policy bound. The campaign then selects a
source-identity-specific candidate and applies the same live route, consider,
health, resource, and healer-return gates. This keeps the path to HERO
executable without presenting an unresearched late-band route as verified.

Source identity is part of the policy key: area, mobile VNUM, reset room,
character level, and reboot identity are retained separately. Same-reboot
productive XP may carry a safe repeat across a level boundary when the source
identity is unambiguous and the normal live presence, consider, crowd, health,
equipment, and recovery gates still pass. Research candidates must not hide
such a repeat. Promotion requires objective XP, bounded damage and resource
evidence, loot or funding evidence where relevant, and a safe healer return.

Finite source-ranked hunt circuits derive their effective command allowance from
the registered outbound route, each hunt stop, and a fixed reserve for combat,
loot, return, and healer cleanup. The extension is recorded in the run and is
still finite; exhausting it becomes a retryable route hazard. This keeps a
large but valid source circuit from being cut off by a small profile default
without allowing an unbounded navigation loop.

The source-ranked selector normally stops when the current reboot has no
fresh, safe candidate. An explicit `retry_stalled` request may reopen one
fresh candidate blocked only by trailing no-progress history. It cannot
override live absence, crowd, route, consider, protection, resource,
source-identity, or cooldown evidence; the live result is persisted and the
next retry rotates rather than replaying the same blocked policy.

An operator retry is not proof of an area reset. Only the automatic retry
marked `reset_wait_completed=True` may consume reboot-local absence or crowd
evidence; otherwise the runner must preserve the cooldown and return an
explicit safe-stop state when no alternative is executable.

Protection recovery distinguishes source-proven non-combat specials from
combat-capable procedures. A productive candidate with only a safe special
such as `spec_fido` may use one existing sanctuary reserve after a single
XP-loss record; a candidate with another autonomy rejection, a combat special,
or a second loss remains quarantined. This preserves the risk boundary while
allowing the source evidence to improve XP/min when the special itself cannot
attack.

Each source-ranked XP-loss record carries the completed campaign segment that
created it. Reconstructing state or repairing an interrupted segment replays
that identity idempotently, so repeated startup metadata checkpoints cannot
manufacture additional losses; a distinct completed segment still increments
the reboot-local count.

Current-reboot explicit retry ownership is also durable. Circuit-consider
repair may restore missing per-stop evidence from historical segment starts,
but it cannot clear a policy recorded in the current explicit retry marker.
This prevents reconnects from oscillating a crowd retirement and producing
metadata-only checkpoints indefinitely.

Risk is evaluated per interruption, not as a blanket fear of death. On the
Dwarven Nobleman fastwalk, the source-level-seven goblin lieutenant may be
handled as incidental below-band transit combat from level fourteen onward
when the ordinary live combat, health, and crowd gates pass; the higher-damage
dark horseman and wyvern remain hard route hazards. If plain combat text
precedes GMCP, the executor waits one bounded prompt and resolves the enemy by
live mobile VNUM before accepting a below-band classification; an unresolved
identity remains a hard interruption. Before a source-ranked attack, the
executor also consults a source-graph index of same-name mobile VNUMs that can
reach the current room. If the expected source VNUM is absent or another
same-name VNUM is reachable, it records presence and skips the stop before
`consider` or `kill`; post-combat GMCP is never used as the first identity
check.

Protection loss is a shared combat decision, not an automatic flee. When a
consumed sanctuary affect disappears, the executor uses authoritative GMCP
player and enemy health plus live enemy level: a materially healthier or more
than one level higher opponent is withdrawn from below 75% player health, while
an opponent in the near-death finisher band may still be completed. This rule
is replay-tested against Kestrel's real 7376 death transcript and is applied
before another recurring combat action.

Maintenance fastwalks share the navigation executor but not the field-policy
ledger. A new maintenance route abort is recorded under
`campaign_maintenance_route_hazards`; transient target, crowd, absence, and
consider fields are restored from the preceding field policy before the
checkpoint is written. Resume migration removes legacy unowned maintenance
markers while retaining source-backed field hazards. This prevents safe
funding or healer returns from changing which progression route is retried.

## Current Proof And Debt

The latest live continuation leaves Aeloria at level 15 and 107,709 XP, Dorrik
at level 24 and 360,891 XP, and Kestrel at level 24 and 345,698 XP. Aeloria's
latest checkpoint is in healer room 3054 at 193/193 HP, 533/533 mana, and
290/290 movement after the latest safe return. On 2026-08-17, the bounded
rotation's Dorrik checkpoint 22973 retained the Eastern Desert crowd boundary
after a bounded reconnect without XP change; Aeloria checkpoint 22979 completed
buy-flight-potion maintenance and Kestrel checkpoint 22985 completed the
follow-up return-home recovery at full HP and mana. All three remained safe in
healer room 3054. The full offline suite passes 2,678 tests, including the
source-proven non-combat-special protection distinction described above. These
are continuation checkpoints, not level-25, subclass, or HERO proof.
route reconnect settled checkpoint 22805 and retained the explicit same-reboot
route retirement; a second reconnect returned the same checkpoint without
another metadata-only repair. Startup repair now preserves explicit retry
intent and authoritative current objective evidence across reconnects. The
full offline suite passes 2,678 tests. Kestrel run 7376 then exposed a real
sanctuary-expiry death at 220/334 HP against a level-30 moose at 410/535 HP;
7377 completed Purgatory recovery and 7379 reacquired the Moria sanctuary
reserve, returning full to healer room 3054. Run 7380 then deferred the fame
route as crowded without another fight. The protection-loss repair now
uses the live health matchup before another attack. Run 7384 then killed the
source-matched Midgaard secretary for 494 objective XP and returned Aeloria
safely; runs 7385-7388 completed bounded absence and maintenance work without
false XP. Runs 7389-7390 then validated explicit retry-stalled rotation: the
young-boy route recorded live absence, the independent mirror guardian route
recorded a live crowd, and both returned Dorrik safely without XP change. Runs
The follow-up safety check closed the remaining retry bypass. Checkpoints
22948-22954 retained Dorrik's Eastern Desert crowd result at cooldown 3 and
created no duplicate field segment or XP claim; the campaign suite passes 818
tests and the complete offline suite passes 2,678 tests. This is selector-
integrity evidence, not progression or HERO completion evidence.
7351 and 7367 added 90 objective XP
each through the generic
source-ranked executor. The runner now retains the full bounded same-reboot
no-progress history and skips crowd-exhausted reset waits. Runs 7369-7372
bounded Kestrel's negative-fame recovery: the priced flight potion was refused
by the Magic Shop, a retry met a wandering-drunk route block, Circus withdrew
at the 39% health floor after using sanctuary, and Mirror Realm recalled before
combat without a sanctuary reserve. Explicit service refusal is now a hard shop
boundary; fame routes require a verified sanctuary reserve, and a flight-only
fallback cannot reopen the refused shop. Run
7373 then resumed Kestrel through the source food reserve route, acquired exact
object VNUM 5219, and returned full without XP change, combat, or another shop
attempt. Aeloria checkpoint 22766 and Dorrik checkpoint 22769 both recorded
crowded current-band rooms and deferred safely for area reset. This is bounded
continuation evidence, not a HERO completion claim.
7104 added 1,852 objective XP for Dorrik before his reboot-local source frontier
exhausted. Aeloria run 7112 added 475 objective XP in Gremlin Lair and run 7121
added 600 objective XP from a source-matched Bird Spider. Run 7123 exposed a
liquidation interruption that fought a city drunk and caused a net 138-XP loss;
the utility dispatcher now flees before below-band transit combat, with
regression coverage. Run 7126 then recorded 108 incidental XP before a shared
health-floor withdrawal and safe healer return; no objective kill was
confirmed. Kestrel run 7128 then added 90 verified XP from the large hobgoblin,
recovered purple sanctuary, and returned full after applying recovery gear. The
full offline suite passes 2,656 tests. Run 7133 then recorded an 83-XP loss
and a 23% health-floor withdrawal on the Gizmo route; no death or objective
kill occurred, and the exact policy is now quarantined. Run 7136 then added
375 verified XP from the source-matched huge python and returned Aeloria full
after chill-touch combat. Run 7137 then added 743 verified XP from Bardoosh,
recovered a dagger after disarm, and returned full with four drops recorded.
Run 7141 then added 321 verified XP from the large hobgoblin, recovered purple
sanctuary, and returned full. Run 7142 then used sanctuary, killed the
below-band Midget for 30 non-objective XP, and recovered its purse and coins
before a full healer return. Run 7145 then added 283 verified XP from the large
hobgoblin, recovered purple sanctuary, and returned at full health. Run 7149
then added 490 verified XP from Bardoosh, maintained source-verified armor
protection, and returned full with three drops. Run 7155 then withdrew from
Bardoosh at 56% health and cost 40 XP without a kill; it was the exact policy's
second loss and is now quarantined. Run 7156 exposed that the Forest's
80-stop source circuit could exceed the profile's 250-command cap; the runner
now derives a finite 613-command allowance and keeps a hard boundary. The old
failed checkpoint reconciled to ready. Runs 7157-7162 completed safe return,
absence, funding, and flight maintenance. Runs 7163, 7166, and 7169 added
574, 280, and 371 objective XP from Queen Wasp kills; runs through 7172
otherwise returned safely without false progress. Runs 7220-7229 then exposed
and repaired ambiguous selector-less gear identity and stale-room ordering in
the fixed rearm route. The repaired sequence validated a Queen Wasp kill for
374 objective XP, a Giant Kodiak bear kill for 280 XP, and Aeloria's level-15
transition. Run 7231 added 528 objective XP from Bardoosh; runs 7230 and
7232-7235 completed bounded level-15 and maintenance rotations safely. Run 7236
then killed Aruncus the Druid for 413 objective XP and returned safely to healer
room 3054. Runs 7237-7270 then added 5,354 objective XP from Bardoosh, Bird
Spider, and Queen Wasp kills, offset by two source-policy hard-floor withdrawals
totaling 190 XP and 20 incidental XP. Run 7283 exposed a randomized Great
Eastern Desert DFS cycle; run 7284 recovered Aeloria through Limbo and the
protected corpse after a death that cost 3,623 XP. The repaired walker now
preserves its visited graph, the Eastern Desert route is quarantined for this
reboot, and Aeloria is 12,917 XP short of level 16. Runs 7285 and 7286 then
added 624 objective XP from the Miden-nir goblin leader and Shire receptionist;
the first also recorded 167 incidental XP loss after an unapproved attacker
joined. Aeloria is now 12,460 XP short of level 16. Run 7289 then killed a
second source-matched Shire receptionist for 397 objective XP without an XP loss
or death. Aeloria is now 12,063 XP short of level 16. Run 7291 was a residual
selector-regression invocation after the timeout marker was cleared; it produced
only 50 incidental XP from a transit dark dwarf and no Eastern Desert objective
kill. Run 7292 restored the marker from history and selected liquidation instead,
leaving that route quarantined for this reboot. Aeloria is now 12,013 XP short
of level 16. Run 7294 then killed another source-matched Shire receptionist for
431 objective XP without an XP loss or death. Run 7298 added a further 368-XP
receptionist kill after addressing hunger during recovery. Aeloria is now 11,214
XP short of level 16. Run 7301 added a further 369-XP receptionist kill and
acquired a usable body part. Aeloria is now 10,845 XP short of level 16. Run
7304 added a further 414-XP receptionist kill without an XP loss or death.
Aeloria is now 10,431 XP short of level 16. Run 7310 then added a 272-XP
receptionist kill without an XP loss or death. Aeloria is now 10,159 XP short of
level 16. Run 7313 then added a further 333-XP receptionist kill without an XP
loss or death; Aeloria is now 9,826 XP short of level 16. Run 7321 then added a
further 368-XP receptionist kill without an XP loss or death; Aeloria is now
8,844 XP short of level 16. Run 7324 then withdrew from an incidental fight at
the hard health floor, recording 167 XP loss, 58 net incidental XP, and no
objective kill before a safe healer return. Aeloria is now 8,786 XP short of
level 16, and the exact route is quarantined for rotation. Run 7328 then
produced five Eastern Desert kills for 380 XP, including successful dropped-weapon
recovery after a disarm; Aeloria returned safely at 187/193 HP and was 8,406
XP short of level 16. Run 7332 added only a 50-XP dark-dwarf contact, and run
7338 repeated the 146-room Forest absence without combat. The retry-marker guard
now keeps that absent route closed after minimum-value contact; the full offline
suite passes 2,662 tests. Run 7343 then added a clean 358-XP young dragon
wormkin kill; Aeloria is now 7,998 XP short of level 16. Run 7344 then added a
clean 233-XP huge python kill; Aeloria is now 7,765 XP short of level 16. Live
CLI campaigns now
default to a 180-second segment cap plus 45 seconds of cleanup grace. Current
live source decisions use revision `7996722`. The selector
now counts exact-policy XP losses, quarantines after the second loss, and waits
for an area reset when protection recovery has no independent route. The older
continuation details below are historical:
Runs 6994-7004 added productive
Moria, Mirror Realm, and Canyon evidence; run 7004 supplied 1,256 objective XP
before consuming the purple sanctuary reserve. Runs 7008 and 7014 then added
886 and 799 objective XP from source-matched Mirror Realm watchmen. Run 7013
withdrew from Dwarven Homestead at the explicit 27% health floor after 179
incidental XP and installed a newer protection marker without death or XP loss.
Runs 7009, 7010, 7011, and 7015 completed liquidation, healer movement
recovery, flight maintenance, and a safe zero-kill probe. The Moria recovery
circuit now uses one reset-room stop plus eight bounded source-room edges; this
is regression-verified. Run 7019 live-validated the circuit through rooms 4064
and 4063, acquired the purple sanctuary potion, and placed it in the combat
pouch before returning full. Run 7022 added 683 objective XP from the Tentusks
treant and consumed the reserve; run 7023 reacquired a purple potion through
Moria with 90 incidental XP. Runs 7024-7026 safely rotated protected Mirror
routes without forcing absent targets. Run 7027 then killed the source-matched
Dwarven Home host for 1,938 objective XP and returned full with the sanctuary
reserve intact. Run 7029 reacquired the reserve with 90 incidental XP; run 7030
skipped a wandering Mirror Realm gardener outside the source-safe relocation
graph without forcing combat. Run 7031 withdrew from the source-matched Solace
Sergeant at Arms at the shared 30% health floor after sanctuary expired,
recording a 385-XP flee loss; run 7032 restored full healer recovery. Run 7033
reacquired the sanctuary reserve with 100 objective XP. Run 7034 safely skipped
a crowded Mirror Realm target without combat. Run 7035 then killed the
source-matched Dwarven Home host for 1,520 objective XP without consuming the
reserve. Run 7038 exposed a same-name Grove race between wandering mobile VNUMs
8900 and 8901 and caused a 385-XP flee loss before GMCP identity arrived. The
pre-combat source-graph ambiguity guard now skips such a stop before `consider`
or `kill`; run 7039 restored the sanctuary reserve with 140 total XP, and run
7040 added 1,465 objective XP from the Dwarven Home host. Runs 7041 and 7042
then recorded a safe Mirror rotation and live-validated the pre-combat
same-name VNUM guard at Grove room 8906 without combat or XP loss; run 7043
added 1,410 objective XP from the Dwarven Home host. Run 7049 then exposed a
source-casting status gap: mobile 9202 (`spec_cast_cleric`) blinded Dorrik after
sanctuary expired and caused a 39-XP net loss before a safe healer return. The
runner now requires a verified cure-blindness route before such a hunt, retains
two matching potions when sanctuary and cure blindness share an item, and uses
the cure before fleeing when blindness is active. Runs 7050 and 7051 completed
safe sanctuary and Dwarven Home rotations without reaching the target, so this
repair is offline-verified but not yet live-triggered. Run 7055 then live-tested
the source-matched Weeping Willow at a perfect consider; the shared 35% health
floor fired after it reduced Dorrik to 137/542 HP, producing a 213-XP net loss
after the flee charge. Runs 7056-7059 recovered and rotated through Dwarven Home,
Shire, flight, and Tentusks without another loss. Run 7060 then reopened the
Dwarven Home host route; Dorrik withdrew at 124/542 HP after earning 602
damage-credit XP, paying the 385-XP flee cost for a 217-XP net gain without an
objective kill. He returned safely to healer room 3054 at 480/542 HP, full mana
and movement, with hunger 4 and thirst 42. Runs 7063-7066 then exercised the
protected frontier: run 7063 killed the source-matched New Ofcol teller for
1,119 objective XP with a 20-XP below-band interruption; run 7064 withdrew from
the Drow weapons master at 43/542 HP and lost 385 XP after 23 damage-credit XP.
Run 7065 consumed sanctuary before the Canyon `spec_cast_cleric` cyclops, but
its harm spell outlasted the aura and forced a flee at 80/542 HP for a 117-XP
net loss. Audited special routes that fail after sanctuary are now quarantined
for the reboot. Run 7066 reacquired and pouch-stowed the purple reserve from
the source-matched large hobgoblin for 100 objective XP and returned full to
the healer. Runs 7081 and 7092 repeated the Drow weapons master route under
its two-mobile crowd: the first lost 210 XP, and the sanctuary-protected retry
lost 265 XP at the 39% health floor. The exact route is quarantined for this
reboot. Run 7083 hit the 180-second segment boundary during a deferred Mirror
Realm search and run 7084 returned Dorrik safely; the starter now clears stale
crowd and locator waits before its runtime return boundary. Runs 7085-7091
completed flight, New Ofcol, Moria, and bounded absence maintenance. Run 7095
then killed the source-matched New Ofcol teller for 934 objective XP and
returned full to healer room 3054 at 358,980 XP. The full offline suite passes
2,648 tests. Run
6987 exposed a
held earthquake staff on the otherwise noncombat priest of Thalos, so source
ranking now rejects unevaluated spell-bearing scrolls, wands, and staves. Runs
6948-6950 then completed a
bounded generic continuation: run 6949 killed the source-matched Mirror Realm
watchman for 873 XP, while runs 6948 and 6950 correctly withdrew from crowded
circuits without forcing combat. All three returned safely with no death or XP
loss. Runs 6951-6960 then added 1,988 aggregate XP, including a 636-XP
Mirror Realm watchman and a 1,352-XP Kerofk route with 742 objective XP plus
610 incidental XP; absent and crowded targets were skipped without XP loss.
Run 6963 exposed a timed sleeping-recovery watchdog gap during flight
maintenance: after one health score, the policy suppressed its prompt gate
while waiting for the affect to expire. The starter now reopens that gate when
the scheduled health check is due; the full offline suite passes 2,636 tests,
and run 6964 live-validated the repair by buying and activating flight with no
XP loss. Runs 6967 and 6968 then exposed the same Abyss return hazard twice,
while run 6971 live-validated the repaired return graph. Runs 6981 and 6982
recorded bounded 149-XP and 16-XP net losses; the finisher now permits one
source-admitted final action against a target up to one level higher at 35%
health or less when the observed one-hit reserve is covered. Run 6987 exposed
a held earthquake staff on the otherwise noncombat priest of Thalos, and
source ranking now rejects unevaluated spell-bearing scrolls, wands, and staves.
The full offline suite passes 2,636 tests. Runs 6965 and 6966 completed a
bounded Abyss absence and 460 incidental XP from three low-risk Kerofk
interruptions, returning full to healer room 3054. Objective and incidental
XP remain separate. Runs 6921 and 6923 supplied
802 and 1,367 objective XP. Run 6926 exposed a live endpoint-gate bug when a
level-19 Goblin Caves Sentry was attacked at the level-24 useful-XP floor
despite being recorded below-band and non-objective. The starter now withdraws
before such an endpoint attack, retaining explicit resource and required-loot
exceptions; run 6927 live-validated the repair. Run 6936 exposed a second
admission gap: a source-audited gas-breath special above the live level ceiling
caused a 385-XP flee from the level-25 Green Dragon. Combat-special admission
now applies that ceiling before launch. Run 6938 then killed the level-19 Swamp
Wraith for 587 XP but paid a 385-XP flee penalty when three source-known
level-16 Mistlings joined the Mahn-Tor no-recall return; the repaired return
branch keeps that bounded below-band interruption in combat. Run 6940 added
170 XP on the Eastern Desert worm route and returned safely. Runs 6941 and 6942
then added 933 and 1,177 XP through the Kerofk gravedigger and Old Thalos
mayor, respectively, with safe healer returns and no XP loss. The full offline
suite passes 2,632 tests. The earlier level-23 evidence follows.

The preceding level-23 continuation left Dorrik at level 23 and 326,057 XP and
Aeloria at level 14 and 88,949 XP, both full in healer room 3054. Runs 6784,
6786, 6788, 6790, 6795, 6800, and 6801 supplied productive source-ranked
kills; runs 6800 and 6801 added 875 and 857 objective XP through the Kerofk
gravedigger and Old Treant routes. Runs 6785, 6787, 6789, and 6794 recorded
bounded Mirror Realm zero-kill or absence results without forced combat; run
6793 refreshed flight, run 6796 restored hunger from 2 to 39, and runs 6797-6799
completed liquidation, safe rejection of a non-corporeal funding target, and
restock. The next Mirror Realm segment was stopped after an outer watchdog
stall and recovered as ready with explicit interruption evidence; run 6803
returned Dorrik safely home without XP loss. Run 6804 then added 891 objective
XP from the same Kerofk gravedigger route, and run 6805 completed liquidation
and full healer recovery in room 3054. Runs 6807 and 6812 then added 784 and
534 objective XP through the generic Old Treant route, while runs 6806, 6809,
6810, 6811, and 6813 recorded bounded zero-kill rotations and run 6808 refreshed
flight. Run 6814 withdrew from a Shudde-M'ell interruption after the live level
gate, lost 354 XP, fed hunger from 5 to 40, and quarantined the exact Plains
North policy for three same-reboot segments. Run 6815 then killed the
source-matched Swamp Wraith in the alternate Mahn-Tor circuit for 1,060
objective XP, and run 6816 restored full movement at healer room 3054. Run
6817 then completed another bounded Mirror Realm zero-kill probe without XP
change. Runs 6818 and 6827 added 726 and 637 objective XP through the generic
Old Treant route. Run 6824 then killed the source-matched Swamp Wraith for 884
objective XP, but exposed two avoidable 354-XP flee penalties from source-known
below-band Mistlings in the Mahn-Tor no-recall return maze. The return policy
now permits a safe lower-band combat interruption only in the registered
Mahn-Tor return rooms when all enemies are source-known below-band and health
and provision gates pass; it then resumes the live-GMCP exit graph. The
focused policy tests pass 38 and the full offline suite passes 2,629 tests.
The exact post-repair live branch remains untriggered, so this closes a
regression while preserving the evidence boundary. Runs 6832 and 6835 then
added 1,053 and 1,083 XP through the generic gravedigger route; run 6833 added
894 XP from Old Treant, and run 6834 rejected a crowded Mirror route without
XP. Dorrik is now 9,361 XP short of level 24 and full on HP, mana, and movement
in healer room 3054. Runs 6836 and 6839 were bounded zero-XP maintenance or
Mirror rotations; run 6837 added 608 XP from Old Treant, run 6838 withdrew at
the health floor with 208 net XP, and run 6840 added 150 XP from the Arachnos
guardian. Hunger is now 2, so provision recovery is the next gate before
another field launch. Run 6841 then restored hunger to 38 while adding 716 XP
from Old Treant. Runs 6842-6845 recorded bounded Mirror, Crystal, Sentinel, and
Abyss results without forced targets; run 6846 refreshed flight. Run 6847
retained a repeated no-policy-decision watchdog failure, and run 6848
reconciled it successfully. Before run 6851, Dorrik was at 319,871 XP with
hunger 24. Run 6851 then added 687 XP from Old Treant, and run 6852 recorded another
bounded Mirror zero-kill result. Dorrik was 6,992 XP short of level 24 before
run 6854 added 646 XP from Old Treant. Run 6855 found Nessy's child but
withdrew when the adult Nessy joined, paying the 354-XP flee cost; the exact
Highland policy was quarantined and the healer return completed safely. Dorrik
is now 6,389 XP short of level 24. Run 6856 then added 1,325 XP from the
source-matched Maid; run 6857 sold four items for 291 coins; and run 6858
recorded another bounded Mirror zero-kill result. Dorrik was then at 322,486
XP, 5,064 short of level 24. Runs 6878-6881 then validated the source-route
scheduler repair: one empty Mirror attempt was excluded from the next
selection, flight maintenance ran, and Old Treant supplied 633 objective XP
before the marker cleared. Run 6883 collected the source-matched sanctuary
potion from the large hobgoblin; run 6887 added 760 objective XP from Old
Treant. Run 6895 withdrew from Dwarven Homestead at the health floor, losing
189 XP without dying and quarantining that exact route; run 6896 recorded a
bounded Mirror absence after rotation. Dorrik is now level 23 at 326,057 XP,
1,493 short of level 24, full in healer room 3054. The campaign now carries a
one-attempt source-route exclusion after a normal no-progress segment;
productive XP clears it, and it is scheduling evidence rather than
progression proof. The
campaign now carries a persisted
deferred-practice marker for a practice type whose current trainer has no
immediately useful listed skill; legitimate newly unlocked damage gateways can
still reopen that type. The combat reserve now has a narrow
finish window for one last action against a nearly defeated lower/equal-level
opponent when the character is healthier than the opponent and above one known
incoming-hit reserve. Explicit stop floors still win, and that branch remains
without live-specific proof. The level-20 shifter trainer now uses a bounded
source-derived Kerofk locator across 62 reachable rooms, with stale-result
recovery covered offline. Live level-20 and level-30 subclass evidence remain
the next generic frontier; none of this proves HERO.

The live mage/thief/warrior matrix proves level 10. Representative long-running
campaigns currently anchor Aeloria at level 14 and 88,949 XP, Dorrik at level
23 and 297,605 XP, and Kestrel at level 24 and 363,995 XP. Run 6708 acquired
a purple sanctuary potion through the generic high-band Moria recovery circuit
and returned Dorrik to healer room 3054 at full HP and mana; the protection
marker for the original failed hunt remains pending for a protected retry.
Runs 6709 through 6716 then recorded a crowded teller withdrawal, a bounded
audited-special withdrawal, an additional 653-XP Highland attempt interrupted
by an unapproved attacker, and safe healer recovery. The next executable
frontier must reacquire sanctuary before retrying the exact failed hunt. Runs
6717 through 6721 then added a productive Arikasbab circuit worth 1,628 XP,
including a 1,338-XP Maid kill, and completed safe Dorrik returns. The next
sanctuary selection remained on a reboot-local cooldown after one bounded
retry. Aeloria runs 6722 and 6723 completed safe no-objective Ambush and Plains
North probes; Kestrel runs 6724 and 6725 completed safe reserve and Mirror
Realm probes without XP. The next frontier remains class-aware continuation,
not a HERO completion claim.
Dorrik's run 5246
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
`7996722`. The bundled prerequisite and training snapshots remain pinned to
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
