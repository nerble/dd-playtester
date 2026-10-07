# Quest Route Audit: October 7, 2026

## Live Assignment

Run **16425** requested a quest from Goldmoon and received the retrieve
assignment for the City's ancient scroll (object **79**) in Wastelands room
**25530**, with a 30-minute countdown. The campaign recognized a locked gate
and issued `quest abort` while still at healer room **3054**. It made no field
trip, gained no XP or quest points, and recorded no XP loss. Run **16426** last
observed no active quest and a 13-minute cooldown at the same healer. That
checkpoint was stopped deliberately; reconnect and read fresh quest status.

## Source Chain

The source-only path to room 25530 crosses the locked north gate at **25429**;
it requires key object **25405**. The key is created by the broken statue mobile
**25408** at that gate after it receives badly chipped stone head object
**25404**. The head is reset on octopus mobile **25405** in room **25426**.
Mobile VNUM **25405** and object VNUM **25405** are different source records.
The campaign now validates this exact chain and includes it in the blocked
route explanation. It does not dispatch the analysis-only path.

## Remaining Gates

- The shortest recall-to-octopus path is **53 commands** and crosses aggressive,
  wandering cave beasts (mobile **25402**) in rooms **25412** and **25418**.
  Source resets allow up to two in each room. Source identification does not
  authorize a fight or transit through them.
- Room **25426** is underwater-ground. DD4 gives two air-supply updates; without
  `breathe water`, drowning damage starts on the second. Source lists a
  breathe-water philter (object **3389**) in the Midgaard Magic Shop, reset on
  wizard mobile **3000** in room **3033**. A live stock listing, quoted price,
  successful use, and fresh affect are still required.
- Once the statue has opened the gate, the shortest route to the scroll is
  **63 commands** and still intersects aggressive cave beasts, a wandering
  fire serpent, and molten uzuz with `spec_thief`. The ordinary 60-command
  economic-theft route allowance does not make this longer locked route safe.
  Each exact mobile needs its normal live identity, route, consider, combat,
  and survival checks.

## Progression Value

## Assignment Selection

`quest.c:generate_quest` does not pre-screen route reachability, room hazards,
or dig safety. After a random eligible mobile/location search, it has a 10%
"no quest" outcome and selects hoard, object retrieval, or kill with an even
three-way roll. Hoards choose a random room VNUM from **0-32200**, excluding
Purgatory, the questmaster's current area, and water/air sectors; the code does
not check whether that room is reachable or survivable. Retrieval and kill
assignments inherit the randomly selected mobile's location. Consequently,
the tester cannot choose the next quest type or destination at request time.
The useful control point is a source-and-live preflight of each exact
assignment, followed by a safe abort and another request only after fresh
live cooldown evidence when a hard gate fails.

Dorrik has **18 QP**, clearing the level-30 gate but leaving **182 QP** to the
level-50 requirement. `quest.c` awards 10-40 base points for a completed
retrieve quest; Goldmoon is level 25, and Dorrik's Knight subclass adds 25%,
yielding **12-50 QP** per successful hand-in. A failed or aborted request earns
nothing. Continue requesting at the live cooldown boundary and count only a
confirmed reward. The source route chain is evidence for future implementation,
not a promise that this particular assignment is currently executable.

## Second Live Assignment

Run **16427** requested again after the previous cooldown cleared and received
the tattered codex (object **589**) in room **10786**, White Lotus Temple, with
a 15-minute countdown. Source planning returned no safe route, so Dorrik
aborted at the healer without entering the field. The segment finished
`objective=not_achieved`, `safety=safe`; it gained no QP or XP and recorded no
XP loss.

The shortest route is **76 commands** and crosses room **10005**. Mobile
**10007** (Barracuda) is aggressive and sentinel, level **7**, with up to **16**
reset instances in that room. A same-length route avoiding 10005 still crosses
Market Square room **3014** and Temple Doors room **10706**. Those have
source-reset `spec_guard` mobiles **3060** and **10707** respectively; room
10706 has two reset groups of up to **9** guards. Their source special makes
them hard transit hazards for the current route gate. They are not aggressive,
but `spec_guard` can join Dorrik's fight (his observed alignment is -1000). The
current route admission does not authorize fighting through the barracuda crowd
or crossing these guard rooms. Keep this assignment closed unless a fresh,
source-validated route and its live checks pass.

An exhaustive shortest-path check against the checked-in room graph confirms
that room **10706** is mandatory from recall to room 10786: blocking 10706
yields no path, even when the Barracuda room **10005** and Market Square room
**3014** are also blocked. Blocking 10005 alone gives a 76-command path;
blocking both 10005 and 3014 gives an 83-command path, but both still cross
10706. This rules out a longer ordinary route as a workaround under the current
source-special hazard contract. It is source-graph evidence, not live route
authorization.

Run **16428** reconnected at healer room **3054** after the abort. Its fresh
status showed no active quest and 14 minutes remaining. It stayed connected at
the healer and requested once after a fresh zero-timer observation.

## Third Live Assignment: Ultima Graveyard

Run **16428** received a 12-minute kill quest for the mourner, mobile **2453**,
reported near Graveyard room **2558** in Ultima. The source prototype is level
**33**, unarmed, with no special; its reset is room **2560**, maximum count
**4**. This looked like a reasonable combat target for level-29 Dorrik, but the
source room graph has no unlocked route from recall to either assigned room.
The analysis-only shortest route is **76 commands** and requires nine locked
doors using seven unique moonstone keys (**2408-2414**). The live campaign
aborted at healer **3054** with that exact key list before entering the field.
The run finished `objective=not_achieved`, `safety=safe`, with no XP loss or
QP.

The official [Ultima fastwalk](https://dragons-domain.org/world/fastwalks/)
reaches entrance room **2400** in 14 commands; following it does not bypass the
locked route to the Graveyard. Source reset analysis found this key chain:

| Key | Carrier and reset room | Shortest approach with earlier keys | Source route finding |
| --- | --- | ---: | --- |
| 2408 | Bat 2401, level 4, room 2411 | 22 commands | No static transit hazard found |
| 2409 | Giant spider 2407, level 8, room 2435 | 22 commands | Requires key 2408 |
| 2410 | Snake 2412, level 9, room 2454 | 38 commands | Requires keys 2408-2409 |
| 2411 | Dirty prisoner 2427, level 11, room 2467 | 44 commands | Requires keys 2408-2410 |
| 2412 | Headless 2434, level 19, room 2492 | 50 commands | Orc crowd and aggressive headless |
| 2413 | Squid 2467, level 30, room 2523 | 63 commands | Orc, gazers, squid, mimic, and shark hazards |
| 2414 | Dragon 2444, level 32, room 2548 | 73 commands | Adds sandtrap and dragon hazards |

The static path checks do not authorize combat or prove live carrier presence.
This is a multi-stage dungeon key chain, not a missing single fastwalk. Do not
reopen the quest without an exact live key/door plan and all ordinary movement,
hazard, identity, and combat gates.

Run **16429** requested after a fresh zero timer and received a 29-minute kill
quest for White Mistress (mobile **1808**) in room **1830**, Little Haven. The
source route was rejected before travel: its route/capacity audit found four
aggressive target resets and wandering hazards. Run **16430** restocked at the
healer. Run **16431** then received the retrieve quest for the Coin of Amaros
in room **1425**, the Necromancer's Lair, with a 14-minute deadline. Its
82-command source route crosses randomized Shadow Grove rooms and dangerous
crowds, so the bot aborted at healer **3054** before travel. Neither attempt
earned QP or lost XP.

Run **16432** last observed no active quest and 13 minutes remaining at healer
**3054** (03:49:16Z). The autonomous loop has started another bounded cycle;
there is not yet a newer live assignment to report. Reconnect decisions must
refresh `quest time` rather than trust this saved timer.

## Questmaster Reward And Route Choice

`quest.c:do_quest` finds the questmaster in the character's current room for
each command. Completion checks the live objective, then calculates QP from
that present questmaster's level; it does not compare that mobile with the
original `questgiver` pointer. Suturb (level **20**, **7** commands from recall)
and Goldmoon (level **25**, **48** commands) both give the same base QP tier.
For Dorrik's Knight subclass, either pays **12-50 QP**; choose Suturb for a
turn-in while no audited higher-reward route is available. This shortens each
turn-in trip by **41 commands** without sacrificing the reward tier.

The higher-reward alternatives are not free shortcuts. Reaver Maeril (level
**35**) gives no QP bonus and its 29-command route crosses source-unsafe
specials. The Mercenary Master (level **65**) offers +25%, but its 112-command
route includes a large aggressive crowd, unsafe specials, and a randomized
room. Dahij (level **250**) offers +50%; its 93-command route has no source
aggressor finding at level 29, but requires confirmed flight and live navigation
through four randomized water rooms (**18807, 18814, 18817, 18828**). Keep these
out of selection until their exact route and live checks are registered. Never
fight a questmaster to obtain its reward.

## Verification

The source parser confirmed the key, head, mobiles, resets, and route hazard
sets. It also confirmed the questmaster reward and route comparison above.
Focused tests cover selecting the shorter equal-reward turn-in; the October 7
pytest batch has already been used, so those new tests remain unrun until the
next local calendar day.
