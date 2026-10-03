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

`dd4tester/excavation.py` now calculates source tool budgets from terrain,
current stats, race, both fuzzy rolls, and spell-dependent lag. It requires an
observed tool level and revealed stats; forms and digging weapons are not yet
covered. `HoardDigSession` issues one dig, waits for the complete response,
prompt, fresh observation and lag, and stops on the first trap, refusal, futile
dig, changed quest/tool/room, occupied endpoint, low HP, insufficient return
movement, changed live-stat/buff budget, timeout, buffer overflow, or exhausted
source budget. The adapter must rebuild that budget from fresh inputs, not
copy the old plan into each observation. It emits an
audit and never claims that unearthing means the quest object was acquired.

The module and saved success/failure replay cases compile. They have **not been
run** under October 3's daily regression limit. It is not imported by live quest
dispatch; the explicit hoard blocker remains. This is a controller implementation,
not live safety permission or completed-quest evidence.

## Physical Return Planner

`excavation_routes.py` adds the separate source return contract. It budgets
walking to an explicitly registered, source-flagged healer without recall,
flight, or invisibility. Every source-open endpoint exit needs its own return
that does not cross the guardian room again. The reserve includes the random
flee step and the most expensive branch; slow triples the walking cost. Routing
uses the existing source hazard exclusions to find a bounded safe detour
instead of treating an obstructed shortest path as the only possible route.
Ordinary unlocked doors produce explicit `open` commands. An endpoint door
needed for return must be opened before excavation and included in the complete
fresh live exit check. Locked/secret doors, walls, private rooms, randomized
exits, flight/water sectors, unknown route resets, and source hazards remain
unsupported. No source room name establishes a recovery location.

Saved cases cover all-exit admission, changed live exits, doors, source access,
hazards, guardian-room exclusion, movement, and finite command bounds. They
compile but are **unrun**. Against the actual source, the prior room-25410
assignment has a 40-command physical path with one unlocked door; strict return
audit finds cityguards in 3014/3040 and the wandering drunk. Excluding source
hazards also yields no bounded supported return. This is diagnostic evidence,
not a reopened quest or permission to cross them. Run **16011** later received
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
profile as live absence evidence. Dorrik's final room-3054 observation has no
shovel and no active affects. Tool acquisition, complete route admission,
hoard/trap handling, and an audited physical return are all still required;
the route stays disabled until those gates and timed replay cases pass.
