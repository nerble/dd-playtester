# Quest Hoard Execution Audit

Source: DD4 revision `6941814a72c464dd90c8127ad6b0573c69cf03d9`, inspected
October 3. This is implementation evidence, **not live execution permission**.
The hoard executor remains disabled. Dorrik still needs his first quest point.

## Acquisition Sequence

`quest.c:generate_quest` creates object **584**, type `ITEM_HOARD`, at the
player's level. Its prototype values are `(400, 1, 200, 200)`: initial digging
depth is **200**. The quest token is owned by the requesting player and put
inside the hoard. The server adds a disturbed-ground hint. GMCP still reports
`retrieve`; retain the existing request-local narrative binding.

`act_obj.c:do_dig` uses the first carried digger, then a worn digger, then an
eligible form, then a wielded/dual digging weapon. Ordinary weapons do not
qualify. It rejects mounted characters, arm trauma, and water/air sectors.
The selected digger must not exceed the character's level.

Each command spends movement and applies wait state before searching for the
first hoard in the room. It reduces depth. At zero, it marks the hoard unearthed
and calls `checkopen` **before** releasing contents. A triggered trap returns
early. The next dig can trigger another charge, even though depth is already
zero. Successful excavation releases all contents onto the ground and destroys
the hoard. `get <token> hoard` is not the extraction mechanism.

Use the exact success message and exact quest-object confirmation; neither a
room hint nor reaching a fixed dig count proves acquisition. Another hoard in
the room can be selected first. Futility text may be absent despite no hoard.

## Digging Budget

The existing tool route names shovel **3604** in room **3613**. Prototype values
are `(25, 16, 39, 83)`: wait pulses, minimum digging damage, maximum damage,
movement cost. `db.c:create_object` fuzzes wait and movement by one at loading;
`do_dig` fuzzes each again. Account for **both** rolls. Dig damage is not fuzzed
at loading for this tool.

`const.c:digmod_terrain_list` applies terrain percentages. `modify_dig_damage`
adds STR/3 after terrain and gives dwarf/duergar a 1.25 multiplier. Movement
subtracts CON/2 after terrain, floors to one, and multiplies by 0.75 for those
races. The final conversion rounds using `(int)(value + 0.5f)`.

For the observed STR 30, CON 25 dwarf using that shovel, conservative examples
are **5 digs / 115 movement** in a field, **8 / 688** inside, and **9 / 918** in
a city. These exclude travel and recovery reserves. His maximum movement is
482. Therefore some otherwise reachable hoards need a separately audited
in-place recovery plan; a blind twelve-command loop is not sufficient.
Wait also depends on DEX, swiftness, race, haste/quicken/bonus attack, blindness,
and slow. Do not use a single fixed command delay or assume room regeneration.
`update.c` sends `GET_SWIFT` as `Char.Stats.swift`, already including the DEX
bonus and learned enhanced-swiftness contribution. Digging uses base swiftness
plus DEX only: subtract the source integer-divided learned bonus from the wire
value, and do not add DEX again. Require the live learned percentage for this
conversion. `Char.Stats.ac` is already `GET_AC`, suitable for trap arithmetic.

## Traps And Escape

`merc.h` defaults `HOARD_TRAP_CHANCE` to **5%**, subject to build overrides.
`quest.c:maybe_arm_hoard_trap` assigns **1-3 charges** and may set room-wide
effects. The generated types are elemental damage, poison, snare, physical
damage, curse, hex, or spirit guardian. Generic sleep and teleport traps exist
in `trap.c`, but this generator does not select them.

- Elemental ceilings: fire 4L, cold 5L, acid 6L, energy 3L.
- Single-target physical ceiling: 10L + AC/4, with C integer division.
  The room-wide branch instead recalculates 10L + AC for each victim. Use
  the larger of these and the elemental ceilings, especially with positive AC.
  Sanctuary halves ordinary trap damage. Fresh HP must leave an escape reserve
  after one hit. This does not bound the separately spawned guardian's attacks.
- Poison applies STR -4 and its normal ongoing effect. Snare applies HOLD for
  six ticks and hitroll -10. Noncombat recall does not reject HOLD by itself;
  combat recall has an additional failure chance while held.
- Curse and hex apply `AFF_CURSE`, preventing recall. Hex lasts L ticks and
  reduces stats, hitroll, and damroll. Source-audited physical return is needed,
  including post-hex carrying capacity; do not plan to wait it out on site.
- A spirit guardian is mobile **83**, created from its level-64 prototype,
  then assigned player level, HP `10L + 20..100`, hitroll/damroll L/2, and evil
  alignment. It immediately attacks. Prototype-derived armor and other fields
  are **not all regenerated** by this override. Its source flags include detect
  invisible/hidden, flying, and pass door. It is not an ordinary level-L reset.

`trapdamage` announces a strange noise before the specific effect. It removes
invisibility, so a return route relying on invisibility is insufficient even
after a resisted curse. A room-wide trap can affect bystanders. Do not admit
an occupied endpoint without separately supporting those consequences.

## Implemented Controller, Not Yet Dispatched

`dd4tester/excavation.py` calculates source tool budgets from terrain, current
stats, race, both fuzzy rolls, and spell-dependent lag. It requires revealed
stats and either an observed tool level or a conservative source-backed shop
level bound; forms and digging weapons are not yet covered. The new
`shop_digger_level_bounds` helper does not prove that a carried item came from
the matching stock, and it does not authorize excavation.
The depth estimate now reserves up to three additional dig commands: on an
armed hoard, each remaining charge makes `do_dig` return before spilling the
contents, and one final dig is needed after the charges are spent. The movement
budget includes that worst case plus the return reserve.

`HoardDigSession` issues one dig, waits for the complete response, prompt, fresh
observation and lag, and pauses on a trap as `trap_recovery_required`. It now
identifies one exact effect from the source response markers for the generated
fire, cold, acid, energy, blunt, pierce, slash, poison, snare, curse, hex, and
spirit traps. Multiple or unrecognized effects are recorded as unknown and
stop the session; this classification is evidence, not recovery permission.
The response markers were checked against DD4 source revision
`2f3b56890ed965d3f6b21c3fb68a8364d276b1a5`. The controller can resume only
through an explicit recovery confirmation tied to a newer state with the same
quest, room, and tool, no combat or occupants, standing posture, the HP floor,
and preserved return movement. The outer caller must independently verify the
live effect state, guardian clearance, route safety, and a refreshed tool
budget before setting that confirmation. The controller still does not fight,
heal, issue sleep/wake, prove endpoint recovery is safe, or authorize that
confirmation in live dispatch. Its compact audit retains trap and recovery
observation sequence numbers for linking to ordered run events. Refusals, futile
digging, changed identity, timeouts, overflow, and exhausted bounds still stop.
Movement recovery remains a separate `recovery_required` handoff. Unearthing
never claims that the exact quest object was acquired.

`HoardDigSession.checkpoint()` now serializes its exact quest/tool identity,
source budget, command count, and ordered trap/recovery evidence.
`from_checkpoint()` requires a newer observation before continuing a safe
boundary. A checkpoint taken while awaiting a dig response restores as stopped;
the caller must reconcile ordered events before any further dig, so a restart
cannot replay an uncertain command. This persistence primitive is not yet
attached to live dig dispatch. `QuestSessionController` carries the checkpoint
through campaign state only when the current quest has the same
narrative-verified giver, room, and object identity; a changed assignment is
cleared. The Telnet reader now forwards response chunks to that controller
only while the exact assignment remains active, dropping it if identity changes.
The controller also exposes identity-gated dig-poll and trap-recovery methods,
but `StarterBotRunner` does not call them yet. This adapter boundary does not
construct or dispatch a live excavation.

The observation parser now stores a compact room-render snapshot after the
exits, visible listing, and prompt arrive, and clears it on a room transition.
DD4's `act_info.c` prefixes both objects and mobiles with the same runtime
`target_id`; the saved lines are raw selector evidence, not mobile VNUMs or
proof that no hidden entity is present. The snapshot is not yet consumed by a
live safety gate. Focused parser and state tests were added October 5 but not
run because that day's regression batch was already used.

The module and saved success/failure replay cases were not run under October
3's daily regression limit. On October 4, a focused staged-movement recovery
case was added but not run because that day's regression batch was already used.
On October 5, coverage was added for the three-charge bound, explicit trap
recovery handoff, typed source responses for the current quest trap table,
unknown-effect rejection, restart checkpoints, exact-assignment text forwarding,
flight-aware route movement, and quest-session-owned poll/recovery identity
gates. Flying movement plans require a fresh active flight check before each
route and escape check; dig costs are unchanged. These tests were not run
because the daily regression batch had already been used.
The campaign still does not construct or dispatch the excavation controller;
the explicit hoard blocker remains. This is observation and planning support,
not live safety permission or completed-quest evidence.

## Physical Return Planner

`excavation_routes.py` adds the separate source return contract. It budgets
walking to an explicitly registered, source-flagged healer without recall or
invisibility. An optional `flying=True` plan applies DD4's source-verified
one-third travel movement cost, but leaves digging-tool movement unchanged and
requires a fresh flight-affect check before each route leg and escape check.
Do not assume flight survives the digging interval; callers must refresh or
verify it before outbound and return movement. Walking remains the default.
Every source-open endpoint exit needs a bounded
return; a branch may re-enter the hoard room only when its route records a
fresh guardian-absence check. The reserve includes the random flee step and
the most expensive branch; slow triples the walking cost. Routing uses the
existing source hazard exclusions to find a bounded safe detour instead of
treating an obstructed shortest path as the only possible route. Ordinary
unlocked doors produce explicit `open` commands. An endpoint door needed for
return must be opened before excavation and included in the complete fresh live
exit check. Locked/secret doors, walls, private rooms, randomized exits,
flight/water sectors, and unknown route resets remain unsupported. No source
room name establishes a recovery location.

The optional exact-live-locator mode validates the current Midgaard cityguard
and drunk prototypes/reset profiles before excluding only those reset rows from
static route ranking. It records VNUMs **3060** and **3064** for `where` checks:
all flee/return branches must be clear before excavation, and the complete
remaining route must be checked again before each movement leg. A return that
re-enters the hoard room also requires guardian VNUM **83** to be absent from
that remaining route. This conditional planner does not enable the live
executor or override combat and recovery checks.

Saved cases cover all-exit admission, changed live exits, doors, source access,
hazards, conditional guardian-room re-entry, live locator completeness,
movement, flight-gated movement estimates, and finite command bounds. The new
flight cases are **unrun** under the October 5 test limit. Against the actual
source, the prior room-25410 assignment has a
40-command physical path with one unlocked door; strict return audit finds
cityguards and the wandering drunk. The exact-locator option now builds a
conditional Forest route, but that is diagnostic evidence, not a reopened
quest or permission to cross them. Run **16011** later received
another hoard in Fortress of Goblins room **20339** and aborted it; the new
planner was not used to authorize or execute that quest.

The planner remains separate from live dispatch. It does not execute escape
or prove that trap recovery succeeds. The separate calculations below are
inputs to that future admission, not permission by themselves.

## Guardian And Hex Calculations

`hoard_guardian_damage` now checks the exact source guardian profile and applies
the runtime overrides in `trap.c`: player level clamped to 1-99, maximum HP
`10 * level + 100`, and damroll `level / 2`. It includes that extra damroll before
`MobDamMod`, sanctuary, and critical arithmetic. At level 29, the current source
gives **64** raw ordinary damage or **128** critical damage per strike, up to
six strikes. The **384/768** ordinary/all-critical round bounds assume strikes
land and no damage-increasing victim effects. They are not expected damage,
final incoming damage, or proof of survival through dig lag and escape. Account
for victim posture/resistance/mitigation and the immediate trap `multi_hit` plus
later rounds before live admission. Changed or unresolved profiles stay closed.

This audit also found and corrected the ordinary NPC estimator's level bonus:
`one_hit` adds level/4 below 30, level/2 at 30-64, and 3*level/4 thereafter, before
the weapon multiplier. The old estimator always added level/4. Shared peak,
expected, critical, and sanctuary estimates now use the correct bands.

`hoard_hex_inventory` computes minimum effective STR/DEX after the level/4
penalty and source floor of three, then the carrying and wielding limits from
`const.c` and `handler.c`. With effective STR 30 / DEX 16 at level 29, the lower
bounds are **23 / 9**, carry weight **800**, item count **31**, and wield weight
**50**. Crucially, encumbrance does **not** itself prevent walking: capacity is a
pickup constraint, not permission to discard belongings after a trap.
`affect_modify` can drop an over-heavy primary weapon, checking the dual weapon
only when no primary exists. Fresh instance weights and explicit slot absence
are required; an unknown weight is not retention proof.

The new boundary, modifier, changed-profile, and hex cases compile but remain
**unrun** under the October 3 regression limit. Neither calculation is wired
into live digging yet.

## Remaining Integration

Build a source-backed excavation plan with tool identity, worst-case dig count,
movement/lag budget, the source physical return contract, and guardian damage
over the complete dig/escape timing window. Add live route preflight where static source hazards need
fresh location evidence; never erase a hazard merely to obtain a return plan.
Wire the response-driven controller to current observations and persisted run
events only after the route and recovery admission is complete.
An initial release can complete untrapped hoards and abandon trapped ones after
verified recovery; it need not deliberately trigger all three charges.
Integrate the exact-object pickup and quest turn-in into the existing connected
quest phases. Validate timed success/trap/timeout/return replays before enabling
live dispatch. Do not grant permission merely because traps are uncommon.

## October 3 Assignment: Forest Room 18022

Run **16070** accepted the coin of Serenos (quest object **585**) as a
retrieve-type hoard in room **18022**, Forest. DD4 generates the hoard object
and its contents at request time; `forest.are` has no static object reset in
that room. This establishes source placement, not pickup permission. The run
aborted safely under the disabled hoard gate, earned no QP, and left a
15-minute cooldown.

The source graph connects Dwarven Home room **20500** west to Forest room
**18021**, then north to **18022**. The west exit is a door; check its live
state. Forest mobile **18008** (level **6**) resets in room **18023**; it is
area-bound but not sentinel, aggressive, or assigned a source special. It may
wander within Forest, so do not assume it remains at reset or treat the source
profile as live absence evidence.

On October 4, run **16162** purchased a spade from the Midgaard Grocer (mobile
**3002**, room **3010**) for the live-quoted **70 copper**. The exact source stock
is object **3393**; the transcript confirmed the purchase and Dorrik's inventory
showed `a spade` on return to healer room **3054**. The displayed selector is not
an object prototype VNUM, and the quoted price is only evidence for that boot;
always use a fresh shop listing. The source gear catalog recognizes the item as
`ITEM_DIGGER`, which satisfies DD4's digging-tool capability check. Its lower
damage and higher movement cost affect the excavation budget, not whether it
can dig. This still does not mean the live hoard flow is integrated. There is
no active quest; the latest observed timer was clear, so a fresh eligible
selection may request again. The old level/boot request marker is audit history,
not a limit. Trap handling and route admission remain unimplemented in live
dispatch; the route stays disabled until those gates and timed replay cases pass.

### October 5 shop-level provenance

`midgaard.are` defines spade **3393** at prototype level **1** and resets it
into the Grocer's inventory. It lacks `ITEM_DONOT_RANDOMISE`, so `db.c` applies
`number_fuzzy(1)` to shop stock; its live level is bounded to **1-2**. `do_buy`
clones the stock item's current level, preserving that bound. Run **16162**
records the exact source purchase, and run **16189** still shows one carried
`a spade`; at level **29**, the source-bounded tool level is usable. The
excavation budget now accepts this conservative bound, but that helper does
not establish item provenance on its own and does not authorize digging.

GMCP `Char.Items.Inv` sends only quantity and short description, not object
level. `do_identify` requires an `ACT_IDENTIFY` mobile in the room; the healer
mobile **3012** in room **3054** lacks that flag, so identifying the spade
there is not an available shortcut. Run **16189** also confirms the current
healer checkpoint has no active quest, zero quest points toward the one-point
level-30 requirement, and a clear MUD cooldown. The persisted campaign request
marker does not restrict another request after a fresh live status check.

### October 4 tool and route check

The bought spade is the basic Midgaard prototype, not the stronger Graveyard
shovel. Its source digging values are `(36, 3, 9, 160)` (wait, minimum damage,
maximum damage, movement). Forest room **18022** is source sector **1**. Using
Dorrik's latest observed modified STR/CON/DEX/swiftness of **30/25/16/5**, and
assuming no enhanced-swiftness contribution, the current budget calculator
estimates **14** minimum damage, **15** earth-removal digs, up to **203 movement**
and **32 pulses** per dig. Including three extra commands for a fully charged
trap gives a conservative **18 commands / 3,654 movement** total before any
return reserve. This is a planning estimate, not measured live digging. The
controller checks one dig plus return reserve at a time and pauses for recovery
rather than requiring all movement up front. An in-place recovery cycle still
needs separate source and live safety evidence; the pause itself does not
authorize sleeping at the endpoint.

The Graveyard shovel reset in room **3613** has values `(25, 16, 39, 83)`.
Under the same assumptions its Forest estimate is **23** minimum damage,
**9** digs, up to **102 movement** and **22 pulses** per dig (**918 movement**
total). It is a useful efficiency option, but still does not fit Dorrik's
**430** maximum movement without recovery. The exact tool identity and a
usable observed or source-bounded tool level, plus the trained swiftness
percentage, are required before estimating a dig.

### October 5 throughput comparison

For Forest room **18022**, the spade requires **15** digs. With freshly
confirmed flight on every travel leg, the 430-movement circuit plan still
allows only one spade dig per healer visit: **15 circuits / 1,215 route-and-dig
commands**. Without flight, even one outbound, dig, and return reserve does not
fit. The Graveyard shovel reduces this to **9** digs at 102 movement each; with
flight, the source plan fits two digs on most visits (**5 circuits / 409
commands**). These are offline throughput estimates, not permission or proof
that the quest timer and runtime will admit the full route.

The healer-to-shovel route is **20 commands** and crosses a cityguard source
room and the wandering-drunk risk. Any acquisition still requires fresh exact
`where cityguard` and `where drunk` results, live exits, current flight, and
the ordinary endpoint checks. Dorrik has no active quest and his live timer
allows another request, but the optional equipment trip remains unjustified by
the hoard executor gap.

The default source planner still finds no unconditional,
hazard-accepted route from room **18022** to the healer. With the narrow
live-locator option, the exact source graph yields a 40-command outbound path
from the healer (estimated **221 movement**) and return path (also **221**);
the worst return/flee branch reserves **231 movement**. Every random flee
branch is bounded; the north branch returns through room 18022 and therefore
needs a fresh `where` result showing guardian VNUM **83** off the remaining
route. The exact live selectors are `cityguard` and `drunk`; both must be absent
from every outbound, flee, and return path, with new `where` evidence before
each movement leg. This does not prove the executor can yet perform those
checks or recover safely. Run
**16167** confirms Dorrik is at healer
**3054**, level **29**, with **3,248 XP** to level 30, no active quest, and a
zero live quest cooldown. No assignment is currently active; campaign request
history is not a limit, but the live hoard executor remains incomplete.

### October 5 execution-plan slice

`build_source_hoard_execution_plan` now composes an exact narrative-verified
assignment, source-resolved carried digger, shop-stock load-level fuzz bounds,
worst-case dig count, physical healer return and flee branches, movement
circuits, direct trap damage, and the dynamic guardian's worst dig-lag damage
window. The plan remains offline evidence; current inventory, exits, locator
results, flight, and recovery must still be observed live. It deliberately
does not lift the campaign blocker. The first executor should finish an
untrapped assignment and stop digging on any trap until a verified recovery
and physical-return path is wired. Exact-object pickup and quest turn-in remain
required for objective success.

### October 5 carried-object evidence

DD4's `Char.Items` entries contain `quan` and `short_desc`, not the room's
runtime target selector. The standalone controller now takes the selector from
a complete, fresh room listing, checks that its exact description maps to only
the assigned quest-object VNUM, and records the current quantity in the nested
`Char.Items` snapshot before returning one `get #selector` command. It confirms
possession only when a later complete inventory snapshot shows exactly one
additional copy. An unchanged or missing snapshot leaves the saved pickup
intent pending without repeating the command. Checkpoint schema 3 preserves
that intent; older `object_acquired` checkpoints are downgraded because they
cannot prove a quantity delta. This repairs the evidence controller, not the
live execution gap: `StarterBotRunner` still does not issue hoard pickups or
prove physical return, trap recovery, or quest turn-in, and the campaign's
hoard blocker remains in place. These controller cases were updated but not
run because the October 5 regression allowance was already used.

### October 5 live request: Demondium room 21784

Run **16191** observed no active quest, `nextquest=0`, and nonnegative fame,
then successfully requested from Goldmoon. DD4 assigned a narrative-verified
retrieve hoard for the book of Fretya (object **78**) in room **21784**, `1000
Stairs`, Demondium. Dorrik still carried the spade (object **3393**), but the
campaign hoard blocker stopped the target phase before any route or `dig`
command. It then issued `quest abort`; no XP or QP was gained, and DD4 set
`nextquest=15`.

The source mirror places the room in an area with nominal level range **60-90**
and has no route from default recall **3001** to room 21784. The route was not
attempted live, so this is source-map evidence rather than proof that every
in-world access method is absent. Do not retry this assignment without a
separately verified route. Request again as soon as a fresh live quest status
reports the timer at zero; the old request marker is history, not a quota.

### October 5 live request: Yitrite Mines room 24005

Run **16212** requested from Goldmoon immediately after the live timer cleared.
Goldmoon assigned a narrative-verified hoard for the book of Fretya (object
**78**) in The secret meeting room, room **24005**, The Yitrite Mines. Dorrik
carried the Midgaard spade (**3393**). The connected campaign recognized the
assignment but applied the still-active trap-aware hoard blocker and issued
`quest abort` at healer room **3054**. It did not enter Yitrite Mines or issue
`dig`; no XP or QP was gained, and the abort set a fresh 15-minute timer.

The source area is rated **50-75**. Its target-room reset is Olaf (mobile
**24010**, level **55**); the area also resets level-**60** dwarven guards
(mobile **24005**) with `spec_guard` across mine rooms. Dorrik was level **29**.
This source profile reinforces the rejection: possession of a spade alone does
not make this route safe, and the live dig/trap/recovery executor remains
unwired. The source room graph and live hazard checks must be audited before
reconsidering this assignment at a more suitable level.

### October 5 live request: Elemental Canyon room 9247

Run **16214** observed DD4's exact `You may now quest again` message at
8:59:55 PM NZDT. Dorrik followed the registered 48-command route from the
healer to Goldmoon and issued `quest request` at 9:01:38 PM. Goldmoon assigned
the coin of Serenos (object **585**) in The Electric Playground, room **9247**,
Elemental Canyon. The live status carried narrative-verified hoard evidence.
Dorrik had the Midgaard spade (**3393**), but the current live runner still
has no integrated excavation/recovery cycle; it issued `quest abort` at healer
room **3054** before entering the area or digging. No XP or QP was gained.

The source rates Elemental Canyon for levels **5-30** and defines room 9247 as
hills terrain. Its room reset is a small spark (mobile **9218**, level **4**,
sentinel). The source spade has base dig damage **3-9** and movement cost
**160**; the hills, Dorrik's strength and constitution, and dwarf modifiers
make this a bounded multi-dig task rather than an unbounded guess. The hoard
still has a **5%** trap chance and may carry **1-3** charges, including curse,
hex, or a dynamically spawned spirit guardian. Keep the execution blocker
until those outcomes, the exact token pickup, physical recovery, turn-in, and
restart boundaries are handled by the live runner.

### October 5 live request: Zyklor's Tower room 14612

Run **16216** requested again after the connected `QUEST TIME` cooldown reached
zero. Goldmoon assigned a narrative-verified hoard for the bowl of Ambros
(object **587**) in The Pens, room **14612**, Zyklor's Tower. Dorrik carried the
spade (**3393**), but the source hoard planner found no bounded route from the
registered healer, and the official map index rates Zyklor's Tower for levels
**60-100** while Dorrik is level **29**. No route or dig was attempted.

The assignment expired while the separate, source-approved Gnome treasury
funding run **16218** was completed safely. Live quest status then showed no
active assignment and `nextquest=14`. The campaign resumed the connected timer
wait and must request again at the next observed zero; request-history markers
remain uncapped by level or reboot. This hoard is not evidence that the
spade-only execution path is safe or integrated.

### October 5 live request: Dragon Tower room 2208

Run **16220** dispatched `quest request` at the first observed zero-timer
opportunity. Goldmoon assigned a retrieve quest for the amulet of Aevros
(object **586**) in Guardian's Room, room **2208**, Dragon Tower, with 21
minutes. The source route to that room has no executable path from recall;
the analysis-only path requires key **2231**. The only area reset found for
that key gives it to mobile **2200** in room **2241**, while the analysis path
to 2241 itself requires keys **2231** and **2232**. The campaign therefore
aborted from Midgaard before entering the area; no XP or QP was gained, and
DD4 set `nextquest=15`. Do not treat this as an ordinary retry or an excuse to
probe Dragon Tower at level 29. The next request remains eligible at the next
live zero timer.

### October 5 live request: Vampire Catacombs room 9504

Run **16223** requested again at the first observed zero-timer opportunity.
Goldmoon assigned the bowl of Ambros (object **587**) in A Dark Corridor,
room **9504**, Vampire Catacombs. The campaign aborted at healer room **3054**
before entering because the source route requires hive master key **25609**.
No XP or QP was gained, and DD4 restarted the 15-minute request timer.

The source mirror has no ground reset for key 25609. Its carrier resets are all
in the Hive: spies level **65-85** in areas with an enforced minimum level of
**40**. The target Catacombs area is rated **25-40**, but the key cannot be
acquired safely by level-29 Dorrik. This is a source-backed access rejection,
not a general ban on requesting again; request again at the next live zero.

### October 5 live request: Galaxy kill quest, Leo

Run **16224** requested again after the live timer cleared. Goldmoon assigned a
kill quest for Leo (mobile **9320**) in Within the Deep Jungle, room **9346**,
Galaxy. Source lists Leo at level **30** with `spec_cast_cleric`; the campaign
aborted from healer room **3054** before travel because the target special is
combat-capable. No XP or QP was gained, and DD4 restarted the 15-minute timer.

The special's source code chooses a victim fighting the mobile and casts a
level-eligible hostile cleric spell: blindness, earthquake, flamestrike, harm,
dispel magic, or others. The source area is otherwise level-appropriate
(**20-45**), but that alone does not bound the caster's incoming damage or
disable effects. Leo's prototype also carries `AFF_SANCTUARY`; DD4's damage
path halves damage to a sanctuaried target. Verify the live affect before any
future combat decision. This is an evidence-based special rejection, not a ban
on future quest requests or all special-bearing mobs.

### October 5 live request: White Lotus Temple room 10843

Run **16225** sent `quest request` at the first observed zero-timer opportunity.
Goldmoon assigned retrieval of the coin of Amaros (object **75**) from the 6th
Chamber of the White Lotus, room **10843**, with 16 minutes. DD4's `quest.c`
creates this token in the selected room; it is not reset onto a mobile. The
campaign aborted at healer room **3054** before travel, so no XP or QP was
gained and the abort restarted the live request timer.

The source area has six consecutive east doors into rooms **10838-10843**;
they require keys **10725, 10726, 10727, 10728, 10730, 10732** respectively.
The keys are held by one sentinel in each preceding chamber (mobiles
**10736-10741**, levels **32-36**). The source shortest route from Midgaard
recall is **88 commands even when all six keys are assumed available**; it
crosses source hazards including the city guard, temple guard, and a large
below-band barracuda crowd. No registered route currently supports this staged
key acquisition, so this rejection is specific to the assignment's access and
combat requirements, not a request-frequency cap. The area-file `1d1+30000`
hit-dice text is not the runtime HP: `db.c` regenerates mobile HP from level
and rank. Reassess only with a route that preserves the ordinary live hazard,
consider, damage-output, and survival gates.

### October 6 live request: Pirate Isles kill quest

Run **16226** observed DD4's `You may now quest again` message and followed the
registered route to Goldmoon. It issued `quest request` at the first available
opportunity, about 50 seconds after the live zero while traveling to the
questmaster. Goldmoon assigned a 28-minute kill quest for the dock guard
(mobile **17022**, room **17211**) in The Isles of the Pirate Lords. The
quest-phase planner rejected the route and sent `quest abort` at the Healer
before entering the area; no XP or QP was gained. The follow-up connection
confirmed DD4 had restarted `nextquest` at **15**.

The target is a level-**27** sentinel with one source reset in the assigned
room and a cutlass; the area is rated **20-45**. The registered source route
search found no safe path from Dorrik's observed Midgaard recall. Its shortest
96-command route crosses the aggressive pirate-raider group (room **17033**,
mobile **17001**, seven resets), the aggressive barracuda crowd (room **10005**,
mobile **10007**, sixteen resets), the aggressive level-**25** kracken (room
**17194**, mobile **17021**), and the roaming raging typhoon
(mobile **17010**, `spec_breath_lightning`). No travel or combat was attempted.
This is a route-specific rejection, not a request cap; the connected timer
worker remains responsible for the next request at zero.

### October 6 live request: TenTusks scroll

Run **16227** requested again after the live cooldown reached zero. Goldmoon
assigned the City's ancient scroll (object **79**) in Impenetrable Fog, room
**25471**, TenTusks. Source route analysis required locked-door keys **25405**;
the campaign sent `quest abort` before travel. No XP or QP was gained, and the
request timer restarted. Keep this assignment closed until the exact key route
is registered and passes the ordinary source and live gates.

### October 6 live request: Rats' Lair hoard

Run **16229** requested again when the connected quest cooldown reached zero.
Goldmoon assigned a narrative-verified hoard for the bowl of Zackera (object
**77**) in A Bedroom, room **3821**, The Rats' Lair, with an 18-minute quest
timer. Dorrik's saved live inventory confirms he already carried the Midgaard
spade (**3393**), five big pot pies, and a buffalo water skin; buying another
spade was unnecessary. The campaign aborted at healer room **3054** before
entering the area or digging, so no XP or QP was gained and `nextquest` reset
to **15**.

The checked-in area rates The Rats' Lair at levels **2-10**. Source planning
for Dorrik at level **29**, using the carried shop spade and observed stats,
estimates up to **15** digs at **173** movement each. With **482** maximum
movement, the plan needs eight healer round trips and about **263** route/dig
commands, exceeding the current **240** command bound even before fresh live
hazard checks. A source-ground shovel (**3604**) is reset once in Graveyard
room **3613**; the recall-origin path is **19** commands and the source hazard
audit is empty at level **29**. Offline planning with that shovel estimates
**8** digs at **87** movement each, two healer circuits, and about **70**
route/dig commands. From the healer, the source route needs the additional
step to recall. This is a tool-upgrade lead only: item presence, live route,
hazards, exact pickup, and physical return still need fresh checks. `quest.c`
gives each generated hoard a **5%** trap chance and allows **1-3** charges;
`trap.c` can deal damage, poison or snare, curse, hex, or spawn a player-level
spirit guardian. The standalone dig controller can pause for verified
recovery, but live routing, trap recovery, safe return, exact pickup, and
turn-in are not integrated. Keep the live blocker in place; neither tool alone
makes this route safe. Continue requesting at the next live zero timer without
a reboot or request-history cap.

### October 6 live request: Sentinel Pass hoard

Run **16230** requested again as the connected live timer reached its zero
window. Goldmoon assigned the amulet of Thagg (object **76**) in Dank Tunnel,
room **18567**, Sentinel Pass, with a 10-minute quest timer. The campaign
aborted at healer room **3054** before travel or digging because trap-aware
hoard acquisition is not integrated. Independently, source route planning
found no bounded healer route to room **18567** with either Dorrik's carried
spade (**3393**) or the candidate Graveyard shovel (**3604**): the source
room's only exit leads west to room **18524**, which resets a troglodyte. No
XP or QP was gained; the request restarted the timer. This is a route-specific
failure, not a reason to delay the next request.

### October 6 live request: White Lotus Temple coin of Serenos

Run **16231** observed the timer reach zero and issued the next quest request
on that connected cycle. Goldmoon assigned the coin of Serenos (object
**585**) in Training Room of the Centipede, room **10775**, with an 11-minute
quest deadline. Source route checks rejected the path from the healer because
it crosses special-bearing mobiles Ma Tang (room **10773**) and Tang Seung
Qwe (room **10775**), plus the large aggressive Barracuda crowd in room
**10005**. Dorrik aborted at healer room **3054** before travel; no XP or QP
was lost. DD4 restarted `nextquest` at **15**, and the following connected
check observed **12** minutes remaining. This closes this assignment's route,
not future requests: issue another when the fresh live timer is zero.

### October 6 live request: Vampire Catacombs tome of Orinth

Run **16233** observed the next zero-timer message and requested again on the
same connected quest cycle. Goldmoon assigned the tome of Orinth (object
**588**) in The Galleria, room **9588**, Vampire Catacombs, with 23 minutes.
The source route gate found locked access requiring keys **9672** and **9662**;
there is no registered safe key-acquisition route. Dorrik aborted at healer
room **3054** before travel, with no XP or QP loss. DD4 then confirmed
`nextquest=15`; retain the route rejection for this assignment only and
request again when a fresh live timer reaches zero.

### October 6 live request: Mahn-Tor Keep tome of Orinth

Run **16234** sent another request after the connected timer reached zero.
Goldmoon assigned the tome of Orinth (object **588**) in Nasturn's Humble
Abode, room **2394**, Mahn-Tor Keep, with a 24-minute deadline. Source route
checks found that locked access requires keys **2350** and **2357**, with no
registered safe key-acquisition route. Dorrik aborted at healer room **3054**
before entering the area; no XP or QP was lost. DD4 confirmed the next timer
at **15**. Close this assignment's route only, and continue requesting when
the fresh live timer next reaches zero.

### October 6 live request: Mirror Realm bowl of Zackera

Run **16235** observed the next live zero and requested again on that
connected cycle. Goldmoon assigned the bowl of Zackera (object **77**) in The
Pond, room **19058**, Mirror Realm, with a 25-minute deadline. The source route
gate rejected room **19058** for level **29** because the gardener can reach
the route as a non-safe special mobile. Dorrik aborted at healer room **3054**
before travel; no XP or QP was lost, and DD4 restarted `nextquest` at **15**.
This is an assignment-specific route rejection, not a request-frequency cap.

### October 6 live request: Goldmoon temporarily has no quest

Run **16236** reached live `nextquest=0` and requested immediately along the
registered route. Goldmoon had no assignment available and replied, “Try again
later”; GMCP set a short `nextquest=3`. Dorrik returned to healer room **3054**
without XP or QP loss. The next request remained eligible when this new live
timer reached zero; an empty questmaster response is not a campaign request cap.

### October 6 live request: Underdark coin of Serenos

Run **16238** requested at live `nextquest=0`. Goldmoon assigned the coin of
Serenos (object **585**) in the Dining Area, room **16351**, Underdark, with a
15-minute deadline. Source preflight rejected the route before travel: the
shortest path crosses the wandering footpad in room **16088** and the large
aggressive Barracuda crowd in room **10005**, while Shillikif's `spec_thief`
can reach the destination. A route avoiding the footpad and Barracudas still
crosses the rooms resetting aggressive `spec_breath_gas` rock crabs. Dorrik
aborted safely at the Healer with no XP or QP loss. This closes only this
assignment's route; continue requesting at the next live zero.

### October 6 live request: Goldmoon temporarily has no quest (again)

Run **16239** waited for the new connected cooldown to reach zero, then
requested again. Goldmoon again had no assignment; GMCP set `nextquest=3`.
The request was not blocked by level, reboot, or campaign history. Dorrik
returned safely to healer room **3054** with no XP or QP loss; retry after this
short live timer reaches zero.

### October 6 live request: Githyanki Knight

Run **16241** requested after the connected timer reached zero. Goldmoon
assigned a 12-minute kill quest for a Githyanki Knight (mobile **1908**) in
Exploring the Astral Plane, room **1908**. Source preflight rejected it before
travel: the target has multiple reset placements, a below-band wandering
aggressor is not an XP target, and non-safe special and aggressive-wanderer
hazards can reach the route. Dorrik aborted at the Healer without XP or QP
loss; DD4 restarted `nextquest` at **15**. Keep this target assignment closed,
not future quest requests.

### October 6 live request: Shadow Keep ancient scroll

Run **16242** requested again after the connected timer reached zero.
Goldmoon assigned the City's ancient scroll (object **79**) in Throne Room,
room **16674**, Shadow Keep, with a 23-minute deadline. Source route analysis
found locked access requiring keys **16603**, **16617**, and **16620**; no
registered safe key-acquisition route is available. Dorrik aborted safely at
the Healer before travel, with no XP or QP loss, and DD4 restarted
`nextquest=15`. Keep this assignment closed, not future requests.

### October 6 live request: Great Pyramid book of Fretya hoard

Run **16243** waited for the live timer to reach zero and requested from
Goldmoon. She assigned the book of Fretya (object **78**) as a buried hoard in
The Apex of the Great Pyramid, room **2606**, with a 13-minute deadline.
Dorrik already carried the source-identified spade (**3393**), but the current
campaign still applies its explicit trap-aware execution blocker and aborted
before travel or digging. DD4 reset `nextquest` to **15**; run **16244** then
confirmed the inactive status and 15-minute timer at healer room **3054**.
This was not a missing-tool problem. The live excavation and recovery path is
still unimplemented, so the hoard remains unproved.

### October 6 live request: Alindra of Dunkeldorf

Run **16245** continued waiting until the live timer reached zero and
requested again. Goldmoon assigned a 14-minute kill quest for Alindra of
Dunkeldorf (mobile **17048**) in the Private Quarters of the Pirate Lord, room
**17270**, The Isles of the Pirate Lords. Source route analysis found locked
access requiring keys **25609** and **17041**, with no registered safe
acquisition route. Dorrik abandoned the assignment before entering the area;
no XP or QP was gained, and DD4 restarted the timer at **15**. Run **16246**
reconnected at the Healer and observed **14** minutes remaining. Keep the
assignment-specific route rejection; request again when the live timer next
reaches zero.

### October 6 live request: TenTusks cave beast

Run **16247** observed DD4's zero-timer availability and requested again on
the connected cycle. Goldmoon assigned an 18-minute kill quest for a cave
beast (mobile **25402**) in Musty Chamber, room **25412**, TenTusks. The
source gate rejected this target because it is aggressive and has multiple
reset placements. Dorrik abandoned it before travel, with no XP or QP gain;
DD4 restarted `nextquest` at **15**. Run **16248** confirmed the fresh timer
and inactive quest status at healer room **3054**. This is another
assignment-specific rejection; keep requesting at each later live zero.

### October 6 live request: Yggdrasil planetar

Run **16250** waited for the live timer to reach zero and requested on the
connected cycle. Goldmoon assigned a 15-minute kill quest for a planetar
(mobile **9901**) in An Upper Branch of Yggdrasil, room **9922**. Source
preflight rejected the target's `spec_cast_mage` and a non-safe special mobile
on the route. Dorrik abandoned the assignment without entering Yggdrasil or
losing XP or QP, then returned to healer room **3054**. DD4 restarted
`nextquest` at **15**. Keep this assignment closed, not future requests.

### October 6 live requests: repeated timer-expiry checks

Runs **16251-16256** each observed DD4's live quest timer reach zero and sent a
new `quest request` at the same level and reboot. This confirms there is no
campaign quota per level or reboot; active-assignment state and live
`nextquest` control eligibility.

Goldmoon assigned the secretary (mobile **29839**) in Prince's Fortress on
run **16251**. Source checks rejected the route for below-band transit
aggressors, an unsafe special, and an aggressive wanderer in the transit-risk
band. Run **16252** received a retrieve quest for the tome of Orinth (object
**588**) in The Gazebo, room **19067**, Mirror Realm; the gardener's unsafe
special can reach the route. Both assignments were abandoned before entering
their areas, without XP or QP gain.

Run **16253** received a buried-hoard quest at The Ballroom in Dwarven
Homestead. Dorrik had the source-identified spade, but the explicit
trap-aware excavation blocker rejected the attempt before travel. Run
**16254** received a kill quest for the Minotaur Warrior (mobile **2317**),
room **2376**, Mahn-Tor Keep; multiple target resets, an unsafe special,
aggressive transit threats, and target aggression failed its source gates.
Run **16255** received a retrieve quest for the book of Fretya (object **78**)
in the Training Room of the Snake, room **10766**, White Lotus Temple; the
route crossed the large aggressive Barracuda crowd in room **10005**. These
assignments were abandoned before entering their areas, with no XP or QP gain.

Run **16256** received a kill quest for Joan (mobile **9506**) in Showers,
room **9517**, Vampire Catacombs. The route requires hive master key **25609**;
the source mirror has no ground reset for it, and its carriers are level
**65-85** in the higher-level Hive. Dorrik abandoned the assignment at Midgaard
without entering the area. Each rejected quest restarted DD4's 15-minute
timer; request again when the next live timer expires.

Run **16257** requested again at live `nextquest=0`. Goldmoon assigned a
29-minute buried-hoard quest near A Corridor in Zyklor's Tower. Dorrik had the
spade, but the trap-aware excavation blocker again rejected it before travel:
the live dig and recovery flow for curse, hex, and spirit guardians is not
integrated. No XP or QP was gained; DD4 restarted `nextquest` at **15**. This
is another repeated request at timer expiry, not a request quota.

Run **16259** also requested at live `nextquest=0`. Goldmoon assigned the
book of Fretya (object **78**) in the Inn Room, room **16451**, Underdark.
Source checks found Orak in room **16444**, the footpad in room **16088**, and
the large aggressive Barracuda crowd in room **10005** on or able to reach the
route. Dorrik abandoned the assignment at Midgaard before entering the area;
no XP or QP was gained, and DD4 restarted `nextquest` at **15**. Try again at
the next live zero.

Run **16260** requested again at live `nextquest=0`. Goldmoon assigned the
tome of Orinth (object **588**) near Along the Seashore, room **9345**, Galaxy.
The source route crossed the large aggressive shadow guardians in rooms
**1306** and **1308**, and the poor mudder's unsafe special could reach it.
Dorrik abandoned the quest before entering Galaxy and returned to healer room
**3054** with no XP or QP gain; DD4 restarted `nextquest` at **15**.

Runs **16261** and **16262** both requested at live `nextquest=0`. Goldmoon had
no assignment either time, but DD4 restarted the timer at **3** minutes. This
is not a level or reboot cap: wait for that fresh timer and request again at
zero. The saved campaign wait marker initially stopped before reconnecting;
the fix now treats a dispatched request followed by a positive post-request
timer as a new cooldown cycle and keeps the healer wait selectable.

Run **16263** confirmed the fix live. It refreshed the remaining timer at the
healer, waited for DD4's zero message, and immediately requested again.
Goldmoon assigned a 15-minute kill quest for a pair of disembodied eyes
(mobile **1313**) in the Guardians chamber, room **1335**, Tower of Sorcery.
Source checks rejected the target because its reset capacity exceeds one, it
is aggressive, and it has `spec_cast_undead`; Dorrik issued `quest abort`
without fighting, returned to healer room **3054**, and gained no XP or QP.
DD4 restarted `nextquest` at **15** after the abort.

### October 6 live request: Vale of the Vampyre hoard

Run **16293** continued the connected healer wait from five minutes remaining,
observed DD4's explicit `You may now quest again` message, and requested from
Goldmoon in the same bounded segment. Goldmoon assigned a 19-minute hoard
quest for the Bowl of Ambros (object **587**) near Undergrowth, room **20667**,
Vale of the Vampyre. Dorrik carried the source-identified Midgaard spade
(**3393**). The current campaign applied `QUEST_HOARD_EXECUTION_BLOCKER` and
aborted at the Healer before entering the area or digging. No XP, QP, or loss
was recorded; DD4 restarted `nextquest` at **15**.

An offline `build_source_hoard_execution_plan` check for this exact narrative-
verified assignment also failed: the current source graph has no bounded safe
route from the registered healer to room **20667**. The spade is not the sole
blocker, and wiring the dig controller alone would not make this assignment
executable. Preserve route admission, trap recovery, physical return, exact
pickup, and turn-in gates. Run **16293** confirms a request is eligible as
soon as DD4 reports the timer clear; it does not establish quest completion.

Run **16316** continued at the next live zero after the preceding quest abort.
Goldmoon assigned a buried-hoard quest for the Bowl of Zackera (object **77**)
in Corridor in the Hive, room **25740**, The Vampyre Hive. Dorrik carried the
Midgaard spade (**3393**), but the area file enforces levels **50-80** and
Dorrik was level **29**. The exact source hoard planner rejected the endpoint
as inaccessible before any travel or digging; the still-unwired trap-aware
executor also issued its explicit abort at healer room **3054**. No XP, QP, or
loss was recorded, and DD4 reset `nextquest` to **15**. This is a real area-
access blocker, not a missing-spade problem. Keep requesting at each fresh
zero; do not treat one randomly assigned high-band hoard as a level/reboot
quota or as evidence that every hoard is inaccessible. The generic hoard
execution gate still needs trap recovery, physical return, exact pickup, and
turn-in integration before a source-accessible assignment can be dispatched.

Run **16319** continued after the previous abort cooldown reached zero and
requested again from Goldmoon at **5:33:50 PM NZST**. Goldmoon assigned the
amulet of Thagg (object **76**) as a buried-hoard quest near Ota'ar Dar Arena,
Beast Cage, room **27577**, with 21 minutes remaining. The campaign did not
travel or dig: its trap-aware execution blocker explicitly issued `quest
abort` at **5:35:41 PM NZST**. No XP, QP, or loss was recorded, and the next
live status showed `active=0`, `nextquest=15`. This confirms the cooldown is
the ordinary abort timer; there is no level- or reboot-scoped request quota.
Request again at the next observed zero, while keeping hoard route and
execution safety gates separate from request eligibility.

Run **16321** then continued the connected wait through its fresh abort timer.
GMCP showed `active=0`, `nextquest=0` at **5:50:56 PM NZST**; after the
registered route and live hazard checks, the campaign dispatched `quest
request` at **5:51:53 PM NZST**. Goldmoon assigned the tome of Orinth (object
**588**) in A living area, room **9532**, Vampire Catacombs, with 21 minutes
remaining. Source route admission rejected the assignment because the
analysis-only path requires key object **9672**, a black gem on a chain with
source load-level bounds **46-50**, above Dorrik's level **29**; no registered
acquisition route exists. Dorrik aborted at the healer before travel; no XP,
QP, or loss was recorded. The fresh timer again reflects an explicit abort,
not a level/reboot request cap.

Run **16322** continued from that timer, observed `active=0`, `nextquest=0`
at **6:07:33 PM NZST**, and dispatched the next request at **6:08:23 PM**.
Goldmoon assigned the City's ancient scroll (object **79**) as a buried hoard
in Asverna's Lair, room **19200**, DragonQuest, with 18 minutes remaining.
Source marks DragonQuest for levels **80-100**; Dorrik was level **29**.
The current trap-aware executor blocker aborted before travel or digging. No
XP, QP, or loss was recorded, and DD4 started another 15-minute abort timer.

Run **16323** observed `active=0`, `nextquest=0` at **6:23:46 PM NZST** and
dispatched the next request at **6:24:37 PM**. Goldmoon assigned a 20-minute
kill quest for cave beast mobile **25402** in Small Chamber, room **25414**,
TenTusks. Source checks rejected the target: reset capacity exceeds one, the
room has a dangerous reset companion and a source-capable assisting companion,
the route crosses an aggressive reset in the useful XP band, and the target
itself is aggressive. Dorrik aborted at **6:25:47 PM** without fighting; no
XP, QP, or loss was recorded. This is the fourth directly observed request
within about a minute of timer zero, with no level/reboot throttle.

### October 6 live quest request sequence

Run **16325** observed the timer clear at **6:39:28 PM NZST** and requested
from Goldmoon at **6:40:17 PM** after the registered route. No assignment was
available; DD4 restarted `nextquest` at **3**. Run **16326** observed the next
zero at **6:43:18 PM** and requested at **6:44:08 PM**. Goldmoon assigned the
tattered codex (object **589**) in Wintergern's Room, room **29903**, Prince's
Fortress. Source route checks rejected the route because it crosses the huge
hairy beast and marsh wolves in rooms **8304/8308/8309**, plus the Marsh Hag's
unsafe special in room **8309**. Dorrik aborted at **6:45:21 PM** without
entering the area; no XP, QP, or loss was recorded, and the timer restarted at
**15**.

Run **16327** observed another live zero at **6:58:54 PM** and requested at
**6:59:44 PM**. Goldmoon assigned the buried-hoard narrative for the Bowl of
Ambros (object **587**) in Atop A Dark Tower, room **23608**, City of Thieves,
with 26 minutes remaining. Dorrik already carried the source-identified spade
(**3393**). The active campaign applied `QUEST_HOARD_EXECUTION_BLOCKER` and
aborted at the healer before travel or digging. An independent source-plan
check also rejected the endpoint: there is no bounded route from the
registered healer. In `city_thieves.are`, room **23608** has no exits and has
three deathhawk resets (mobile **23538**). DD4's `quest.c` hoard generator
selects a random room while excluding purgatory, water/air sectors, and the
requester's current area, but does not test reachability or exits. This
assignment cannot be solved by
buying a spade or bypassing the route gate. No XP, QP, or loss was recorded;
DD4 restarted `nextquest` at **15**. Run **16328** is continuing the connected
healer wait for the next live zero. These runs confirm requests remain
available at each observed timer expiry; the target's route and execution
checks remain separate from request eligibility.

Run **16328** observed the timer clear at **7:14:34 PM NZST** and requested
from Goldmoon at **7:15:24 PM**. Goldmoon assigned another buried-hoard
narrative for the tattered codex (object **589**) at Entrance to Watermill,
room **1123**, The Shire, with 10 minutes remaining. Dorrik still carried
spade **3393**. The source plan found no bounded safe return route from the
registered healer. The 15-step shortest route crosses cityguards, the drunk,
and source-reachable Shire hazards including shiriffs and the Thain; no
hazard-free route was found. The campaign kept the trap-aware hoard blocker and
aborted at the healer at **7:16:26 PM** without travel or digging. No XP, QP,
or loss was recorded; DD4 restarted `nextquest` at **15**. Run **16329** is
continuing the connected healer wait and observed **13** minutes remaining at
**7:18:19 PM**. This assignment is not cleared by owning a spade; route and
return admission still fail independently of excavation.

Run **16329** observed the abort timer reach zero at **7:29:30 PM NZST** and
requested from Goldmoon at **7:30:20 PM**. The tattered codex (object **589**)
was assigned to A Bend in the Hall, room **9941**, Kaladim, with 20 minutes.
The source route crossed the higher-level aggressive large knife reset in
room **9933**. The campaign aborted before entering Kaladim or fighting; no
XP, QP, or loss was recorded, and DD4 restarted `nextquest` at **15**.

Run **16331** observed its fresh zero at **7:46:29 PM NZST**, then requested
from Goldmoon at **7:47:18 PM** after refilling and drinking at the healer's
fountain. Goldmoon assigned a buried-hoard retrieve for the Bowl of Ambros
(object **587**) in the Crypt, room **26766**, Thoran, with 28 minutes (27 on
the subsequent GMCP update). Dorrik carried the source spade (**3393**), but
an offline `build_source_hoard_execution_plan` check found no bounded route
from healer room **3054**. `thoran.are` marks the area level range **35-90**,
and room **26766** resets a level-80 vampire (mobile **26745**); Dorrik was
level **29**. The live campaign applied `QUEST_HOARD_EXECUTION_BLOCKER` and
aborted at **7:48:06 PM** before travelling or digging. No XP, QP, or loss was
recorded; DD4 restarted `nextquest` at **15**, and connected run **16332** was
still reducing that timer. This assignment was ineligible for both route and
level reasons, independently of the remaining trap-recovery work. Requests
remain available at each observed timer zero; these failed targets do not
create a level- or reboot-based request cap.

Run **16332** observed DD4 clear the timer at **8:03:59 PM NZST** and
requested from Goldmoon at **8:04:49 PM**. Goldmoon assigned a hoard retrieve
for the amulet of Aevros (object **586**) on Path along Lake, room **11544**,
The Highlands, with 29 minutes. Dorrik carried spade **3393**, but the source
planner found no bounded route from healer room **3054**. `highland.are`
enforces levels **15-25**; DD4's `act_move.c` rejects movement outside that
band, and Dorrik was level **29**. The campaign aborted at **8:05:47 PM**
before travel or digging. No XP, QP, or loss was recorded; DD4 restarted
`nextquest` at **15**. This assignment was inaccessible regardless of spade
ownership, and the general trap-aware execution gate remains a separate
blocker for otherwise accessible hoards.

Run **16333** observed the abort timer reach zero at **8:22:22 PM NZST** and
requested from Goldmoon at **8:23:12 PM**. Goldmoon assigned a kill quest for
criosphinx mobile **2614** in A Shining Vault, room **2652**, The Great Pyramid.
The source gate rejected it because the target had multiple resets and
`spec_cast_cleric`, while a non-safe special mobile crossed and could reach the
route. Dorrik aborted at **8:24:26 PM** before travelling or fighting; no XP,
QP, or loss was recorded, and DD4 restarted `nextquest` at **15**.

Run **16334** observed the next live zero at **8:40:05 PM** and requested at
**8:40:55 PM**. Goldmoon assigned mad Prisoner mobile **16622** in The Pit,
room **16697**, Shadow Keep. `shadow_keep.are` defines the target's
`spec_poison` special, and the source route crosses a non-safe special mobile.
Dorrik aborted at **8:42:25 PM** without entering the area or fighting; no XP,
QP, or loss was recorded, and DD4 restarted `nextquest` at **15**. Run **16335**
then observed the fresh timer counting down online from **14** at **8:43:44 PM**.
Both requests were dispatched on the first arrival at Goldmoon after DD4
announced eligibility. The normal timer is the only repeat-request cadence;
unsafe assignments trigger their own new server cooldown and do not create a
level- or reboot-based cap.

Run **16335** observed the next zero at **8:57:54 PM NZST** and requested at
**8:58:44 PM**. Goldmoon assigned a hoard retrieve for the amulet of Aevros
(object **586**) in The Yellow Room, room **19082**, Mirror Realm, with 10
minutes. Dorrik carried spade **3393**. The live runner applied the existing
trap-aware execution blocker and aborted at **8:59:49 PM** before travel or
digging; no XP, QP, or loss was recorded, and DD4 restarted `nextquest` at
**15**. An independent source-only `build_source_hoard_execution_plan` call
for this exact narrative identity, tool, and level failed with
`hoard has no bounded source route from the registered healer`. This target is
unreachable on the current audited graph independently of the still-missing
live trap-recovery integration. Run **16336** observed the fresh timer online
at **7** minutes at **9:06:10 PM**.

Run **16336** observed DD4 clear `nextquest` at **9:12:51 PM NZST** and
dispatched the next request at **9:13:41 PM**. Goldmoon assigned a retrieve
quest for the City's ancient scroll (object **79**) in Tyrgoth's Inner Sanctum,
room **2374**, Mahn-Tor Keep, with 22 minutes. The source route check found
that access requires keys **2350** and **2353**, with no registered safe key
route; Dorrik aborted at **9:14:59 PM** before entering the area. No XP, QP, or
loss was recorded, and DD4 restarted `nextquest` at **15**. Run **16337**
observed **14** minutes remaining at **9:16:19 PM**. The completed request
confirms the timer is the only request cadence gate; this assignment is blocked
by the locked route, not by request frequency.

Run **16337** dispatched the next request at **9:30:44 PM NZST**, after DD4
announced eligibility. Goldmoon assigned another retrieve quest for the City's
ancient scroll (object **79**), this time in The Foothills of Mount Doom, room
**15727**, with 17 minutes. GMCP marked the retrieval method as `hoard`; the
campaign therefore applied the existing trap-aware hoard blocker and aborted
at **9:32:20 PM** before travel or digging. No XP, QP, or loss was recorded,
and DD4 restarted `nextquest` at **15**. This is a per-assignment execution
gate, not a request-frequency limit; the next request remains available at the
next live timer zero.

Run **16344** observed the next timer clear at **9:46:25 PM NZST** and
dispatched a request at **9:47:09 PM**. Goldmoon assigned a kill quest for
mobile **16003**, The Prisoner, in Prison Cell, room **16343**, Underdark, with
21 minutes. The source gate rejected the target because its reset capacity
exceeds one and non-safe, combat-joining specials can reach the route. Dorrik
aborted at **9:48:20 PM** before travelling to the target or fighting; no XP,
QP, or loss was recorded, and DD4 restarted `nextquest` at **15**. This is a
target-specific safety rejection; the live timer still permits the next
request at zero.

Run **16345** observed `nextquest` reach zero at **10:04:11 PM NZST** and
dispatched another request at **10:05:47 PM**. Goldmoon assigned a kill quest
for mobile **16129**, The Eye Killer, in Wyrm Street, room **16003**,
Underdark, with 25 minutes. The source gate rejected the target because its
reset capacity exceeds one, a source-capable companion can assist, another
dangerous reset companion is present, and a non-safe special mobile crosses
the route. Dorrik aborted at **10:06:57 PM** before travelling or fighting;
no XP, QP, or loss was recorded, and DD4 restarted `nextquest` at **15**. Run
**16346** observed the new cooldown counting down online at **13** minutes by
**10:08:46 PM**. The repeated request was allowed at timer zero; the current
wait is DD4's fresh post-abort timer, not a campaign request quota.

Run **16346** observed `nextquest` clear at **10:24:10 PM NZST** and dispatched
the next request at **10:25:48 PM** after the fresh Midgaard greeter check
cleared. Goldmoon assigned the hoard retrieve for the Tome of Orinth (object
**588**) in the Great Ice Cavern, room **17296**, Isles of the Pirate Lords,
with 29 minutes. Dorrik carried the source-identified spade **3393** and
completed the registered 48-step route to Goldmoon. On return to healer room
3054, a stale `the wandering Midgaard greeter entered the route after the
healer check` marker made the quest phase abort at **10:26:54 PM**, before
source-route preflight or any digging. No XP, QP, or loss was recorded; DD4
restarted `nextquest` at **15**. A fresh clear final route check now clears
only this exact temporary marker; the live route and hoard safety gates remain.

Run **16347** observed `nextquest` clear at **10:40:21 PM NZST** and requested
again at **10:41:11 PM**. Goldmoon assigned the Coin of Serenos (object **585**)
in the Tower of Sorcery antechamber, room **1453**, with 30 minutes. The source
route audit found no safe route from recall at level 29: the 95-step shortest
path crosses multiple reset crowds (shadow guardians, disembodied hands and
eyes, golems, and the golem maker), while the source-safe path search found no
alternative. Dorrik aborted at **10:42:12 PM** before travel or combat; no XP,
QP, or loss was recorded, and DD4 restarted `nextquest` at **15**. This
assignment is route-blocked, not request-limited.

Run **16349** observed the next live timer reach zero at **10:59 PM NZST** and
dispatched another request at **10:59:29 PM**. Goldmoon assigned a retrieve
hoard for the Book of Fretya (object **78**) in the Cleric Academy, room
**5116**, Drow City, with 22 minutes. Dorrik carried spade **3393**. The
campaign's existing trap-aware hoard gate explicitly aborted at **11:00:58 PM**
before travelling or digging; no XP, QP, or loss was recorded. Run **16350**
observed the resulting ordinary `nextquest` cooldown at **13** minutes by
**11:03:09 PM**. This confirms requests are not capped by level or reboot;
the separate blocker is safe execution of this hoard assignment.

Run **16350** observed the next live timer clear at **11:15:10 PM NZST** and
dispatched a request at **11:15:59 PM**. Goldmoon assigned a kill quest for
mobile **9533**, the nude sculpture, in room **9532**, Vampire Catacombs, with
24 minutes. The source route requires locked-door key **9672**, with no
registered safe key-access route. The campaign explicitly aborted at
**11:17:05 PM** before travel or combat; no XP, QP, or loss was recorded, and
DD4 restarted `nextquest` at **15**. Run **16351** confirmed the new connected
cooldown at **14** minutes by **11:17:54 PM**. Request timing remains
uncapped; this target was blocked by its locked route.

Run **16351** stayed connected at healer room **3054** until DD4 reported the
quest timer clear, then travelled the registered 48-step route and requested
again from Goldmoon at **11:32:39 PM NZST**. Goldmoon assigned a 27-minute kill
quest for mobile **10721**, the small red scorpion, in room **10773**, Training
Room of the Scorpion, White Lotus Temple. The source area file contains five
reset entries for this level-21 `spec_poison` target in that room, plus Ma Tang
(mobile **10722**), a level-35 aggressive `spec_kungfu_poison` companion.
The source specials are combat-triggered: `spec_poison` bites a player already
fighting the scorpion on a one-in-four proc check; Ma Tang's aggressive flag
and `spec_kungfu_poison` can produce a poison-palm attack on three of four
combat invocations.
At **11:34:15 PM**, the campaign aborted at the healer before travelling to
the target or fighting. No XP, QP, or loss was recorded; DD4 restarted
`nextquest` at **15**. This confirms another request was made as soon as the
timer cleared; the assignment itself failed the source-backed safety gates.

Run **16353** stayed connected through the new cooldown and dispatched the
next Goldmoon request at **11:48:42 PM NZST**, after the live timer cleared.
Goldmoon assigned an 11-minute retrieve quest for the Coin of Amaros (object
**75**) in room **10775**, Training Room of the Centipede, White Lotus Temple.
DD4's `quest.c` creates this ordinary quest object in its assigned room; it is
not a reset or buried-hoard item. The source route audit found Ma Tang in room
**10773**, Tang Seung Qwe in target room **10775**, and a large aggressive
Barracuda crowd on the route in room **10005**. Dorrik aborted at the Healer at
**11:50:25 PM**, before travelling to the target or fighting. No XP, QP, or
loss was recorded; DD4 restarted `nextquest` at **15**. The request occurred
at timer zero as expected; this assignment was blocked by its source-audited
route hazards.

Run **16354** remained connected until the live cooldown expired, then
requested from Goldmoon at **12:06:14 AM NZST**. Goldmoon assigned a 29-minute
kill quest for the cyclops (mobile **9202**) in room **9204**, A Blind Curve on
the Mountain Path, Elemental Canyon. The source area registers
`spec_cast_cleric`; the campaign's source safety gate also identifies the
endpoint as aggressive. Dorrik issued `quest abort` at **12:07:45 AM**, before
travelling or fighting. No XP, QP, or loss was recorded; DD4 restarted
`nextquest` at **15**. Run **16355** confirmed the new connected cooldown at
**13** minutes by **12:09:34 AM** and **12** minutes by **12:10:04 AM**. This is
another successful timer-zero request followed by a separate, source-backed
assignment rejection, not a request-frequency limit.

Run **16355** remained connected through the cooldown and requested from
Goldmoon at **12:24:36 AM NZST**, shortly after DD4 reported the timer clear at
**12:23:46 AM**. Goldmoon assigned a 17-minute buried-hoard retrieve quest for
the tattered codex (object **589**) in room **16296**, Audience Chamber,
Underdark. Dorrik carried spade **3393**, so the blocker was not missing
equipment: hoard execution is still disabled until the trap-aware recovery,
guardian escape, and return-route contracts are integrated. He returned to the
Healer and issued `quest abort` at **12:26:23 AM**, before travelling to or
digging at the target. The source area resets one level-50 sentinel iron golem
(mobile **16034**, wielding object **16024**) in room **16296**; this is source
placement evidence only, not a live sighting from this run. No XP, QP, or loss
was recorded, and DD4 restarted `nextquest` at **15**. This run confirms that
having a spade alone does not make an unresolved hoard safe to execute.

Run **16356** observed DD4 clear the live timer at **12:41:02 AM NZST** and
immediately began the registered trip to Goldmoon. Dorrik reached her and
issued `quest request` at **12:41:51 AM**. Goldmoon replied that no quests
were available, and GMCP set `nextquest` to **3**; no quest was assigned.
Dorrik recalled and returned to healer room **3054**. No XP, QP, or loss was
recorded. Run **16357** confirmed the new connected server timer at **2** by
**12:43:25 AM**. The first request followed the original timer expiry without
an added campaign quota; the three-minute wait is DD4's response to having no
quest available at that request.

Run **16357** observed the new timer clear at **12:44:44 AM NZST** and
requested from Goldmoon at **12:45:47 AM**. Goldmoon assigned a 10-minute
buried-hoard retrieve quest for the tattered codex (object **589**) in room
**16297**, Audience Chamber, Underdark. Dorrik carried spade **3393**, then
recalled and returned to healer room **3054**. The campaign issued `quest
abort` at **12:47:17 AM**, before travelling to or digging at the target,
because trap-aware hoard execution is not yet integrated. The source reset
loads up to four level-49 stone golems (mobile **16035**) into room **16297**
and equips them with maces (object **16025**); this is source placement
evidence, not a live sighting. An offline `hoard_return_plan` for endpoint
**16297**, healer **3054**, and level **29** also returned
`hoard has no bounded source route from the registered healer`; no live route
was attempted. No XP, QP, or loss was recorded, and DD4 restarted `nextquest`
at **15**.

Run **16358** observed the connected timer clear at **1:01:38 AM NZST** and
requested from Goldmoon at **1:02:28 AM**. Goldmoon assigned a 14-minute
buried-hoard retrieve quest for the Bowl of Ambros (object **587**) in room
**14646**, Temple of Zyklor, Zyklor's Tower. Dorrik carried spade **3393**.
The campaign recalled him to the Healer and issued `quest abort` at
**1:04:04 AM**, before travelling to or digging at the target. The source
planner found no bounded route from healer **3054** at level **29**; the target
area is **60-100** and resets a level-83 black dragon statue (mobile **14547**)
with `spec_breath_acid`. This is source evidence only, not a live sighting. No
XP, QP, or loss was recorded, and DD4 restarted `nextquest` at **15**.

## October 7 Live Evidence

DD4 source advanced from `7e163cd` to `48cb5a6` on October 7. The refreshed
all-area parser loaded **13,052 rooms, 4,125 mobiles, and 6,138 objects** before
the following source-route conclusions were recorded.

Run **16359** requested again when DD4 reported `nextquest=0` at **1:18:21 AM
NZST**. Goldmoon assigned a 20-minute kill quest for the Prisoner (mobile
**1309**) in room **1327**, Tower of Sorcery. The cell door requires key
**1323**, which the source resets on the level-17 Jailor (mobile **1310**) in
room **1328**; that Jailor has `spec_cast_mage`. The bounded source-route check
found no safe route from default recall: its shortest path crosses aggressive
shadow-guardian crowds in rooms **1302** and **1308**. The campaign aborted at
the Healer before travel or combat at **1:19:56 AM**. No XP, QP, or loss was
recorded; DD4 restarted `nextquest` at **15**.

Run **16360** requested again at timer zero, at **1:34:13 AM NZST**. Goldmoon
assigned a 27-minute buried-hoard retrieve quest for the tattered codex
(object **589**) in room **28756**, Central Omu, with spade **3393** carried.
The campaign aborted at **1:35:44 AM**, before travel or digging, because the
trap-aware recovery and return executor is not integrated. Independently, the
source area `omu_central.are` enforces a level-40 minimum; Dorrik was level 29,
and `hoard_return_plan` rejected the endpoint as unsupported access. No XP, QP,
or loss was recorded; DD4 restarted `nextquest` at **15**. This assignment is
not evidence that the spade failed or that Dorrik entered Omu. After a bounded
provision restock, run **16362** resumed the same campaign at the Healer and
was connected with 11 minutes remaining on the live timer as of **1:39 AM**.
